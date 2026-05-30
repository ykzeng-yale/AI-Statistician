from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


ALGORITHM_REPAIR_PROMOTION_SCHEMA_VERSION = 1
ALGORITHM_REPAIR_TASK_TYPE = "algorithm_repair_from_numerical_failure"
FORBIDDEN_EXECUTABLE_FIELDS = {
    "code",
    "code_patch",
    "generated_code",
    "python_code",
    "exec",
    "eval",
}


@dataclass(frozen=True)
class AlgorithmRepairPromotionCandidate:
    candidate_id: str
    artifact_id: str
    question_id: str
    source_action_id: str
    target_procedure: str
    algorithm_id: str
    implementation_hash: str
    numerical_repair_kind: str
    sandbox_status: str
    required_gate: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_algorithm_repair_promotion_queue(
    loop_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Promote algorithm live-repair artifacts into sandbox patch candidates.

    This is deliberately not a code executor. It extracts contract-valid
    AlgorithmEngineer artifacts, validates that they contain patch intent and
    rerun gates, rejects embedded executable code, and writes a queue for a
    future sandboxed patch/apply/evaluate worker.
    """

    errors: list[str] = []
    manifest_path = loop_dir / "research_loop_manifest.json"
    manifest = _load_json(manifest_path, errors)
    artifact_path = Path(
        str(manifest.get("live_repair_artifacts_jsonl", loop_dir / "research_loop_live_repair_artifacts.jsonl"))
    )
    if not artifact_path.is_absolute() and not artifact_path.exists():
        artifact_path = loop_dir / artifact_path
    artifacts = _load_jsonl(artifact_path, errors)
    algorithm_artifacts = [
        row for row in artifacts if row.get("task_type") == ALGORITHM_REPAIR_TASK_TYPE
    ]
    candidates = [_candidate_for_artifact(row) for row in algorithm_artifacts]
    by_kind = Counter(row.numerical_repair_kind for row in candidates)
    by_status = Counter(row.sandbox_status for row in candidates)
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_REPAIR_PROMOTION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "loop_dir": str(loop_dir),
        "manifest": str(manifest_path),
        "live_repair_artifacts_jsonl": str(artifact_path),
        "n_live_repair_artifacts": len(artifacts),
        "n_algorithm_repair_artifacts": len(algorithm_artifacts),
        "n_candidates": len(candidates),
        "n_ok": sum(1 for row in candidates if row.ok),
        "all_ok": not errors and all(row.ok for row in candidates),
        "errors": errors,
        "by_repair_kind": dict(sorted(by_kind.items())),
        "by_sandbox_status": dict(sorted(by_status.items())),
        "candidates": [asdict(row) for row in candidates],
        "dataset_fingerprint": stable_hash([asdict(row) for row in candidates]),
        "limitations": [
            "promotion candidates are patch work orders, not applied code changes",
            "no executable code from repair artifacts is run or trusted by this audit",
            "a future sandbox worker must create a patch, run algorithm audit, and rerun finite simulations before promotion",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        queue_path = out_dir / "algorithm_repair_promotion_queue.jsonl"
        _write_jsonl(queue_path, [asdict(row) for row in candidates])
        payload["queue_jsonl"] = str(queue_path)
        (out_dir / "algorithm_repair_promotion_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "algorithm_repair_promotion.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _candidate_for_artifact(row: dict[str, Any]) -> AlgorithmRepairPromotionCandidate:
    artifact = row.get("repair_artifact") if isinstance(row.get("repair_artifact"), dict) else {}
    errors: list[str] = []
    artifact_id = str(row.get("artifact_id", ""))
    question_id = str(row.get("question_id", ""))
    source_action_id = str(row.get("source_action_id", ""))
    target_procedure = str(artifact.get("target_procedure", ""))
    algorithm_id = str(artifact.get("algorithm_id", ""))
    implementation_hash = str(artifact.get("implementation_hash", ""))
    numerical_repair_kind = str(artifact.get("numerical_repair_kind", ""))
    required_gate = "sandboxed algorithm patch + algorithm audit + finite simulation rerun"

    if row.get("repair_contract_ok") is not True:
        errors.append("repair_contract_ok must be true")
    if row.get("repair_contract_errors"):
        errors.append("repair_contract_errors must be empty")
    if not target_procedure:
        errors.append("target_procedure missing")
    if not algorithm_id:
        errors.append("algorithm_id missing")
    if not _looks_like_sha256(implementation_hash):
        errors.append("implementation_hash must be a SHA-256 hex digest")
    if not str(artifact.get("patch_summary", "")):
        errors.append("patch_summary missing")
    reproduction_test = artifact.get("reproduction_test")
    if not isinstance(reproduction_test, dict) or not reproduction_test.get("procedure_id"):
        errors.append("reproduction_test.procedure_id missing")
    rerun_metrics = artifact.get("rerun_metrics")
    if not isinstance(rerun_metrics, dict):
        errors.append("rerun_metrics missing")
    else:
        for key in ("n_failed_target", "finite_metric_required", "max_failed_fraction"):
            value = rerun_metrics.get(key)
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                errors.append(f"rerun_metrics.{key} must be finite")
    if str(artifact.get("algorithm_registry_status", "")) != "vetted":
        errors.append("algorithm_registry_status must be vetted")
    forbidden = sorted(FORBIDDEN_EXECUTABLE_FIELDS & set(artifact))
    if forbidden:
        errors.append("repair artifact must not embed executable code fields: " + ", ".join(forbidden))

    sandbox_status = "READY_FOR_SANDBOX_PATCH" if not errors else "BLOCKED_INVALID_REPAIR_ARTIFACT"
    return AlgorithmRepairPromotionCandidate(
        candidate_id="algorithm_repair_candidate:" f"{stable_hash([artifact_id, artifact])[:16]}",
        artifact_id=artifact_id,
        question_id=question_id,
        source_action_id=source_action_id,
        target_procedure=target_procedure,
        algorithm_id=algorithm_id,
        implementation_hash=implementation_hash,
        numerical_repair_kind=numerical_repair_kind,
        sandbox_status=sandbox_status,
        required_gate=required_gate,
        ok=not errors,
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


def _looks_like_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Algorithm Repair Promotion Queue",
        "",
        f"- Loop dir: `{payload.get('loop_dir')}`",
        f"- Algorithm repair artifacts: {payload.get('n_algorithm_repair_artifacts')}",
        f"- Promotion candidates: {payload.get('n_ok')}/{payload.get('n_candidates')} valid",
        "",
        "## Sandbox Status",
        "",
    ]
    by_status = payload.get("by_sandbox_status", {})
    if isinstance(by_status, dict) and by_status:
        for status, count in sorted(by_status.items()):
            lines.append(f"- `{status}`: {count}")
    else:
        lines.append("- none")
    if payload.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in payload.get("errors", []):
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)
