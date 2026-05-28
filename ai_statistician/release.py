from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .capability_audit import build_capability_audit, write_capability_audit
from .doctor import build_doctor_report, write_doctor_manifest
from .fingerprint import stable_hash
from .schema import StatisticalQuestion
from .system_audit import SystemAuditConfig, run_system_audit


@dataclass(frozen=True)
class ReleaseBundleConfig:
    n_runs: int = 300
    seeds: tuple[int, ...] = (20260528, 20260529)
    use_axle: bool = False
    include_eval: bool = True
    max_manifests: int = 12


async def build_release_bundle(
    out_dir: Path,
    *,
    root: Path | None = None,
    env_file: Path | None = None,
    questions: list[StatisticalQuestion] | None = None,
    config: ReleaseBundleConfig = ReleaseBundleConfig(),
) -> dict[str, object]:
    """Create a top-level release artifact from existing production audits."""

    project_root = (root or Path.cwd()).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    doctor = build_doctor_report(
        root=project_root,
        env_file=env_file or project_root / ".env",
        max_manifests=config.max_manifests,
    )
    doctor_path = write_doctor_manifest(doctor, out_dir / "doctor")

    capability = build_capability_audit(root=project_root, max_manifests=config.max_manifests)
    capability_path = write_capability_audit(capability, out_dir / "capability_audit")

    system = await run_system_audit(
        out_dir / "system_audit",
        questions=questions,
        config=SystemAuditConfig(
            n_runs=config.n_runs,
            seeds=config.seeds,
            use_axle=config.use_axle,
            include_eval=config.include_eval,
        ),
    )
    system_path = out_dir / "system_audit" / "system_audit_manifest.json"

    gates = {
        "doctor_required": bool(doctor["summary"]["required_ok"]),
        "capabilities_present": bool(capability["all_required_capabilities_present"]),
        "system_audit": bool(system["all_gates_passed"]),
    }
    if config.use_axle:
        gates["real_lean_ready"] = bool(doctor["summary"]["real_lean_ready"])

    release_basis = {
        "config": {
            "n_runs": config.n_runs,
            "seeds": list(config.seeds),
            "use_axle": config.use_axle,
            "include_eval": config.include_eval,
        },
        "gates": gates,
        "provenance": system["provenance"],
        "counts": system["counts"],
    }
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "release_id": stable_hash(release_basis),
        "root": str(project_root),
        "all_release_gates_passed": all(gates.values()),
        "gates": gates,
        "config": release_basis["config"],
        "provenance": release_basis["provenance"],
        "counts": release_basis["counts"],
        "artifacts": {
            "doctor": str(doctor_path),
            "capability_audit": str(capability_path),
            "system_audit": str(system_path),
            "intake_audit": system["artifacts"]["intake_audit"],
            "algorithm_audit": system["artifacts"]["algorithm_audit"],
            "retrieval_audit": system["artifacts"]["retrieval_audit"],
            "proof_audit": system["artifacts"]["proof_audit"],
            "question_runs": system["artifacts"]["question_runs"],
            "trace_audit": system["artifacts"]["trace_audit"],
            "evaluation": system["artifacts"]["evaluation"],
        },
        "summary": {
            "doctor_required_ok": doctor["summary"]["required_ok"],
            "capability_ready": capability["n_ready"],
            "capability_partial": capability["n_partial"],
            "capability_missing": capability["n_missing"],
            "system_all_gates_passed": system["all_gates_passed"],
        },
    }
    (out_dir / "release_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    return payload
