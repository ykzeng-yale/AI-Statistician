from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .research_lab import audit_research_algorithm_registry


ALGORITHM_REPAIR_SANDBOX_APPLY_SCHEMA_VERSION = 1
READY_STATUS = "SANDBOX_PATCH_PLAN_READY"


@dataclass(frozen=True)
class AlgorithmRepairSandboxApplyResult:
    application_id: str
    candidate_id: str
    algorithm_id: str
    target_procedure: str
    patch_application_mode: str
    patch_applied_to_production: bool
    sandbox_artifact_created: bool
    registry_audit_ok: bool
    rerun_evidence_kind: str
    allowed_patch_scope: tuple[str, ...]
    required_next_gate: str
    ok: bool
    errors: tuple[str, ...] = ()


def apply_algorithm_repair_sandbox_results(
    sandbox_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Create non-mutating sandbox application records for algorithm repairs.

    This is a deliberately bounded bridge between "candidate is sandbox-ready"
    and "production patch is allowed". It does not execute generated code and it
    does not modify the algorithm registry. Instead it records a reviewed guard
    plan as an applied sandbox artifact, reruns the deterministic algorithm
    registry audit, and emits the next gate required before release promotion.
    """

    errors: list[str] = []
    manifest_path = sandbox_dir / "algorithm_repair_sandbox_manifest.json"
    manifest = _load_json(manifest_path, errors)
    results_path = Path(str(manifest.get("results_jsonl", sandbox_dir / "algorithm_repair_sandbox_results.jsonl")))
    if not results_path.is_absolute() and not results_path.exists():
        results_path = sandbox_dir / results_path
    sandbox_results = _load_jsonl(results_path, errors)
    registry_audit = audit_research_algorithm_registry()
    registry_audit_ok = bool(registry_audit.get("all_ok"))
    results = [
        _apply_sandbox_result(row, registry_audit_ok)
        for row in sandbox_results
        if isinstance(row, dict)
    ]
    by_mode = Counter(row.patch_application_mode for row in results)
    by_status = Counter("OK" if row.ok else "BLOCKED" for row in results)
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_REPAIR_SANDBOX_APPLY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sandbox_dir": str(sandbox_dir),
        "sandbox_manifest": str(manifest_path),
        "sandbox_results_jsonl": str(results_path),
        "algorithm_audit_all_ok": registry_audit_ok,
        "algorithm_registry_fingerprint": str(registry_audit.get("registry_fingerprint", "")),
        "n_candidates": len(results),
        "n_ok": sum(1 for row in results if row.ok),
        "all_ok": not errors and all(row.ok for row in results),
        "errors": errors,
        "by_application_mode": dict(sorted(by_mode.items())),
        "by_application_status": dict(sorted(by_status.items())),
        "results": [asdict(row) for row in results],
        "dataset_fingerprint": stable_hash([asdict(row) for row in results]),
        "limitations": [
            "sandbox apply creates an auditable non-mutating artifact, not a production code patch",
            "no generated code is executed",
            "release promotion still requires an isolated code patch, algorithm audit, and finite simulation rerun",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        result_path = out_dir / "algorithm_repair_sandbox_apply_results.jsonl"
        _write_jsonl(result_path, [asdict(row) for row in results])
        payload["results_jsonl"] = str(result_path)
        (out_dir / "algorithm_repair_sandbox_apply_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "algorithm_repair_sandbox_apply.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _apply_sandbox_result(
    row: dict[str, Any],
    registry_audit_ok: bool,
) -> AlgorithmRepairSandboxApplyResult:
    errors: list[str] = []
    candidate_id = str(row.get("candidate_id", ""))
    algorithm_id = str(row.get("algorithm_id", ""))
    target_procedure = str(row.get("target_procedure", ""))
    allowed_patch_scope = tuple(str(item) for item in row.get("allowed_patch_scope", ()) if str(item))

    if row.get("ok") is not True:
        errors.append("sandbox result ok flag is false")
    if str(row.get("sandbox_status", "")) != READY_STATUS:
        errors.append("sandbox result is not patch-plan ready")
    if row.get("hash_matches_current_registry") is not True:
        errors.append("sandbox result does not target current registry hash")
    if row.get("algorithm_audit_ok") is not True:
        errors.append("candidate algorithm audit was not OK during sandbox evaluation")
    if row.get("patch_applied_to_production") is not False:
        errors.append("sandbox result must not have mutated production code")
    if not registry_audit_ok:
        errors.append("current registry audit is not OK")
    if not allowed_patch_scope:
        errors.append("allowed_patch_scope missing")

    required_next_gate = str(
        row.get(
            "required_next_gate",
            "apply bounded patch in isolated workspace, rerun algorithm audit, then rerun finite simulation diagnostics",
        )
    )
    application_id = "algorithm_repair_sandbox_apply:" f"{stable_hash([candidate_id, algorithm_id, allowed_patch_scope])[:16]}"
    ok = not errors
    return AlgorithmRepairSandboxApplyResult(
        application_id=application_id,
        candidate_id=candidate_id,
        algorithm_id=algorithm_id,
        target_procedure=target_procedure,
        patch_application_mode="non_mutating_guard_plan",
        patch_applied_to_production=False,
        sandbox_artifact_created=ok,
        registry_audit_ok=registry_audit_ok,
        rerun_evidence_kind="registry_audit_plus_guard_gate",
        allowed_patch_scope=allowed_patch_scope,
        required_next_gate=required_next_gate,
        ok=ok,
        errors=tuple(errors),
    )


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse JSON {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse JSONL {path}:{idx}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{idx}")
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Algorithm Repair Sandbox Apply Evaluation",
        "",
        f"- Sandbox dir: `{payload.get('sandbox_dir')}`",
        f"- Applied sandbox artifacts: {payload.get('n_ok')}/{payload.get('n_candidates')}",
        f"- Algorithm audit OK: {payload.get('algorithm_audit_all_ok')}",
        "",
        "## Application Modes",
        "",
    ]
    by_mode = payload.get("by_application_mode", {})
    if isinstance(by_mode, dict) and by_mode:
        for mode, count in sorted(by_mode.items()):
            lines.append(f"- `{mode}`: {count}")
    else:
        lines.append("- none")
    if payload.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in payload.get("errors", []):
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)
