from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_APPLICATION_VALIDATION_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "SCAFFOLD_ONLY_NOT_PROOF_EVIDENCE"


@dataclass(frozen=True)
class FormalVerifierReplayRepairApplicationValidationRow:
    schema_version: int
    validation_id: str
    application_id: str
    packet_id: str
    replay_id: str
    route_id: str
    display_name: str
    repair_class: str
    application_mode: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    artifact_path: str
    artifact_exists: bool
    artifact_readable: bool
    local_lean_checked: bool
    local_lean_compiled: bool
    local_lean_errors: tuple[str, ...]
    placeholder_free: bool
    contains_scaffold_boundary: bool
    contains_non_evidence_boundary: bool
    contains_target_statement: bool
    contains_candidate_bridge_name: bool
    static_checks_ok: bool
    proof_evidence_status: str
    validation_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_application_validation(
    formal_verifier_replay_repair_application_dir: Path,
    out_dir: Path | None = None,
    *,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
) -> dict[str, object]:
    """Validate generated repair-application Lean scaffolds as source artifacts.

    This validation is deliberately narrower than proof verification. A scaffold
    can be artifact-clean, and can optionally compile as a Lean source file,
    while still not proving the replay target theorem. Proof evidence is only a
    repaired replay attempt that passes AXLE/local Lean and calibrates as
    full_route_kernel_verified.
    """

    errors: list[str] = []
    application_manifest_path = (
        formal_verifier_replay_repair_application_dir
        / "formal_verifier_replay_repair_application_manifest.json"
    )
    application_payload = _read_json(application_manifest_path, errors)
    tasks = [
        row
        for row in application_payload.get("tasks", [])
        if isinstance(row, dict)
    ]
    lean_project_path = Path(lean_project) if lean_project else None
    rows = [
        _validation_row(
            task,
            application_dir=formal_verifier_replay_repair_application_dir,
            lean_project=lean_project_path,
            lean_timeout=lean_timeout,
        )
        for task in tasks
    ]
    by_validation_status = Counter(row.validation_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_APPLICATION_VALIDATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_application_dir": str(
            formal_verifier_replay_repair_application_dir
        ),
        "formal_verifier_replay_repair_application_manifest": str(application_manifest_path),
        "n_application_tasks": len(tasks),
        "n_validation_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_static_ok": sum(1 for row in rows if row.static_checks_ok),
        "n_artifact_exists": sum(1 for row in rows if row.artifact_exists),
        "n_artifact_readable": sum(1 for row in rows if row.artifact_readable),
        "n_placeholder_free": sum(1 for row in rows if row.placeholder_free),
        "n_with_scaffold_boundary": sum(1 for row in rows if row.contains_scaffold_boundary),
        "n_with_non_evidence_boundary": sum(
            1 for row in rows if row.contains_non_evidence_boundary
        ),
        "n_with_target_statement": sum(1 for row in rows if row.contains_target_statement),
        "n_with_candidate_bridge_name": sum(
            1 for row in rows if row.contains_candidate_bridge_name
        ),
        "local_lean_enabled": lean_project_path is not None,
        "local_lean_project": str(lean_project or ""),
        "local_lean_timeout": lean_timeout,
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "all_local_lean_compiled": (
            bool(lean_project_path)
            and bool(rows)
            and all(row.local_lean_checked and row.local_lean_compiled for row in rows)
        ),
        "by_validation_status": dict(sorted(by_validation_status.items())),
        "n_failed": sum(1 for row in rows if not row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "rows": [asdict(row) for row in rows],
        "validation_fingerprint": stable_hash([asdict(row) for row in rows]),
        "errors": errors,
        "limitations": [
            "repair scaffold validation is source-artifact integrity evidence, not theorem proof evidence",
            "a scaffold that compiles under Lean only confirms imports/comments/source syntax",
            "candidate bridge lemma names are repair targets, not declarations known to exist",
            "proof evidence requires a repaired full-route replay attempt to pass AXLE/local Lean and recalibrate as full_route_kernel_verified",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_replay_repair_application_validation_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_application_validation.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_application_validation.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _validation_row(
    task: dict[str, Any],
    *,
    application_dir: Path,
    lean_project: Path | None,
    lean_timeout: int,
) -> FormalVerifierReplayRepairApplicationValidationRow:
    errors: list[str] = []
    application_id = str(task.get("application_id", ""))
    packet_id = str(task.get("packet_id", ""))
    replay_id = str(task.get("replay_id", ""))
    route_id = str(task.get("route_id", ""))
    display_name = str(task.get("display_name", ""))
    repair_class = str(task.get("repair_class", ""))
    application_mode = str(task.get("application_mode", ""))
    target_theorem_name = str(task.get("target_theorem_name", ""))
    candidate_bridge_lemma_name = str(task.get("candidate_bridge_lemma_name", ""))
    source_formal_statement = str(task.get("source_formal_statement", ""))
    proof_evidence_boundary = str(task.get("proof_evidence_boundary", ""))
    artifact_path = _resolve_artifact_path(str(task.get("artifact_path", "")), application_dir)
    artifact_exists = bool(artifact_path.exists())
    artifact_readable = False
    content = ""
    if not str(task.get("artifact_path", "")):
        errors.append("artifact_path missing")
    elif not artifact_exists:
        errors.append(f"artifact_path does not exist: {artifact_path}")
    else:
        try:
            content = artifact_path.read_text(encoding="utf-8")
            artifact_readable = True
        except Exception as exc:
            errors.append(f"failed to read artifact_path: {type(exc).__name__}: {exc}")

    placeholder_free = "h_frontier_missing" not in content
    contains_scaffold_boundary = "FORMAL VERIFIER REPLAY REPAIR APPLICATION TASK" in content
    contains_non_evidence_boundary = (
        "not Lean proof evidence" in content
        or "not proof evidence" in content
    )
    contains_target_statement = bool(target_theorem_name and target_theorem_name in content) or bool(
        source_formal_statement and source_formal_statement.strip() in content
    )
    contains_candidate_bridge_name = bool(
        candidate_bridge_lemma_name and candidate_bridge_lemma_name in content
    )
    if not placeholder_free:
        errors.append("repair scaffold still references h_frontier_missing")
    if not contains_scaffold_boundary:
        errors.append("repair scaffold boundary marker missing")
    if not contains_non_evidence_boundary:
        errors.append("repair scaffold non-evidence boundary missing")
    if not contains_target_statement:
        errors.append("repair scaffold target statement/name missing")
    if not contains_candidate_bridge_name:
        errors.append("repair scaffold candidate bridge lemma name missing")
    if "not proof evidence" not in proof_evidence_boundary:
        errors.append("task proof_evidence_boundary does not state non-evidence status")
    static_checks_ok = not errors

    local_lean_checked = False
    local_lean_compiled = False
    local_lean_errors: tuple[str, ...] = ()
    if lean_project is not None and artifact_readable:
        local_lean_checked = True
        local_lean_compiled, local_lean_errors = _run_local_lean(
            artifact_path,
            lean_project,
            lean_timeout,
        )
        if not local_lean_compiled:
            errors.append("local Lean scaffold compile failed")

    if lean_project is not None:
        validation_status = (
            "scaffold_compiles_not_proof"
            if static_checks_ok and local_lean_compiled
            else "scaffold_compile_failed"
        )
    else:
        validation_status = (
            "scaffold_static_ok_not_checked"
            if static_checks_ok
            else "scaffold_static_failed"
        )
    validation_id = (
        "formal_verifier_replay_repair_application_validation:"
        f"{stable_hash([application_id, packet_id, replay_id, artifact_path])[:16]}"
    )
    return FormalVerifierReplayRepairApplicationValidationRow(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_APPLICATION_VALIDATION_SCHEMA_VERSION,
        validation_id=validation_id,
        application_id=application_id,
        packet_id=packet_id,
        replay_id=replay_id,
        route_id=route_id,
        display_name=display_name,
        repair_class=repair_class,
        application_mode=application_mode,
        target_theorem_name=target_theorem_name,
        candidate_bridge_lemma_name=candidate_bridge_lemma_name,
        artifact_path=str(artifact_path),
        artifact_exists=artifact_exists,
        artifact_readable=artifact_readable,
        local_lean_checked=local_lean_checked,
        local_lean_compiled=local_lean_compiled,
        local_lean_errors=local_lean_errors,
        placeholder_free=placeholder_free,
        contains_scaffold_boundary=contains_scaffold_boundary,
        contains_non_evidence_boundary=contains_non_evidence_boundary,
        contains_target_statement=contains_target_statement,
        contains_candidate_bridge_name=contains_candidate_bridge_name,
        static_checks_ok=static_checks_ok,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        validation_status=validation_status,
        proof_evidence_boundary=(
            "This validation checks repair scaffold source integrity only. It is not proof "
            "evidence for the target theorem; proof evidence starts only after a repaired "
            "full-route replay attempt passes AXLE/local Lean and calibration reports "
            "full_route_kernel_verified."
        ),
        ok=static_checks_ok and (lean_project is None or local_lean_compiled),
        errors=tuple(errors),
    )


def _resolve_artifact_path(raw: str, application_dir: Path) -> Path:
    if not raw:
        return Path("__missing__")
    path = Path(raw)
    if path.is_absolute() or path.exists():
        return path
    return application_dir / path


def _run_local_lean(lean_file: Path, lean_project: Path, timeout_s: int) -> tuple[bool, tuple[str, ...]]:
    if shutil.which("lake") is None:
        return False, ("lake executable not found",)
    if not lean_project.exists():
        return False, (f"lean project does not exist: {lean_project}",)
    try:
        result = subprocess.run(
            ["lake", "env", "lean", str(lean_file.resolve())],
            cwd=str(lean_project),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return False, (f"local Lean timed out after {timeout_s}s",)
    except Exception as exc:
        return False, (f"{type(exc).__name__}: {exc}",)
    errors: list[str] = []
    if result.stdout.strip():
        errors.append(result.stdout.strip())
    if result.stderr.strip():
        errors.append(result.stderr.strip())
    return result.returncode == 0, tuple(errors)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Repair Application Validation",
        "",
        f"- Application manifest: `{payload.get('formal_verifier_replay_repair_application_manifest')}`",
        f"- Validation rows: {payload.get('n_ok')}/{payload.get('n_validation_rows')} audit-clean",
        f"- Static checks OK: {payload.get('n_static_ok')}",
        f"- Local Lean checked: {payload.get('n_local_lean_checked')}",
        f"- Local Lean compiled: {payload.get('n_local_lean_compiled')}",
        f"- Local Lean project: `{payload.get('local_lean_project')}`",
        f"- Fingerprint: `{payload.get('validation_fingerprint')}`",
        "",
        "These rows validate repair scaffold source integrity only; they are not theorem proof evidence.",
        "",
        "## Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No repair application scaffolds were exported for validation.")
    else:
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}` ({row.get('validation_status')}): "
                f"{row.get('candidate_bridge_lemma_name')}"
            )
            lines.append(f"  artifact: `{row.get('artifact_path')}`")
            lines.append(f"  local Lean compiled: {row.get('local_lean_compiled')}")
            lines.append(f"  proof status: {row.get('proof_evidence_status')}")
            lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
