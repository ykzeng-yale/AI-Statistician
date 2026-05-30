from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .research_lab import audit_research_algorithm_registry, get_research_algorithm_spec


ALGORITHM_REPAIR_SANDBOX_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AlgorithmRepairSandboxResult:
    candidate_id: str
    algorithm_id: str
    target_procedure: str
    original_implementation_hash: str
    current_implementation_hash: str
    hash_matches_current_registry: bool
    algorithm_audit_ok: bool
    sandbox_status: str
    patch_applied_to_production: bool
    allowed_patch_scope: tuple[str, ...]
    required_next_gate: str
    ok: bool
    errors: tuple[str, ...] = ()


def evaluate_algorithm_repair_sandbox(
    promotion_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Evaluate algorithm repair promotion candidates in a bounded sandbox lane.

    This worker still does not mutate production code. It verifies that a
    promotion candidate targets the current vetted implementation hash, runs the
    algorithm registry audit, and emits a patch-plan readiness record for the
    future patch/apply/rerun worker.
    """

    errors: list[str] = []
    manifest_path = promotion_dir / "algorithm_repair_promotion_manifest.json"
    manifest = _load_json(manifest_path, errors)
    queue_path = Path(str(manifest.get("queue_jsonl", promotion_dir / "algorithm_repair_promotion_queue.jsonl")))
    if not queue_path.is_absolute() and not queue_path.exists():
        queue_path = promotion_dir / queue_path
    candidates = _load_jsonl(queue_path, errors)
    algorithm_audit = audit_research_algorithm_registry()
    audit_ok_by_algorithm = {
        str(row["algorithm_id"]): bool(row["ok"])
        for row in algorithm_audit.get("algorithms", [])
        if isinstance(row, dict)
    }
    results = [
        _evaluate_candidate(candidate, audit_ok_by_algorithm)
        for candidate in candidates
        if isinstance(candidate, dict)
    ]
    by_status = Counter(row.sandbox_status for row in results)
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_REPAIR_SANDBOX_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "promotion_dir": str(promotion_dir),
        "promotion_manifest": str(manifest_path),
        "promotion_queue_jsonl": str(queue_path),
        "algorithm_audit_all_ok": bool(algorithm_audit.get("all_ok")),
        "algorithm_registry_fingerprint": str(algorithm_audit.get("registry_fingerprint", "")),
        "n_candidates": len(results),
        "n_ok": sum(1 for row in results if row.ok),
        "all_ok": not errors and all(row.ok for row in results),
        "errors": errors,
        "by_sandbox_status": dict(sorted(by_status.items())),
        "results": [asdict(row) for row in results],
        "dataset_fingerprint": stable_hash([asdict(row) for row in results]),
        "limitations": [
            "sandbox evaluation checks patch-plan readiness, not production mutation",
            "no generated code is executed",
            "a future worker must apply a bounded patch and rerun simulations before release promotion",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        result_path = out_dir / "algorithm_repair_sandbox_results.jsonl"
        _write_jsonl(result_path, [asdict(row) for row in results])
        payload["results_jsonl"] = str(result_path)
        (out_dir / "algorithm_repair_sandbox_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "algorithm_repair_sandbox.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _evaluate_candidate(
    candidate: dict[str, Any],
    audit_ok_by_algorithm: dict[str, bool],
) -> AlgorithmRepairSandboxResult:
    errors: list[str] = []
    candidate_id = str(candidate.get("candidate_id", ""))
    algorithm_id = str(candidate.get("algorithm_id", ""))
    target_procedure = str(candidate.get("target_procedure", ""))
    original_hash = str(candidate.get("implementation_hash", ""))
    current_hash = ""
    try:
        current_hash = get_research_algorithm_spec(algorithm_id).implementation_hash
    except Exception as exc:
        errors.append(f"algorithm registry lookup failed: {type(exc).__name__}: {exc}")
    hash_matches = bool(original_hash and current_hash and original_hash == current_hash)
    if not candidate.get("ok", False):
        errors.append("promotion candidate ok flag is false")
    if not hash_matches:
        errors.append("candidate implementation_hash does not match current registry")
    algorithm_audit_ok = audit_ok_by_algorithm.get(algorithm_id, False)
    if not algorithm_audit_ok:
        errors.append("algorithm audit is not OK for candidate algorithm")
    if str(candidate.get("sandbox_status", "")) != "READY_FOR_SANDBOX_PATCH":
        errors.append("promotion candidate is not ready for sandbox patch")
    allowed_patch_scope = _allowed_patch_scope(str(candidate.get("numerical_repair_kind", "")))
    if not allowed_patch_scope:
        errors.append("unknown numerical_repair_kind")
    status = "SANDBOX_PATCH_PLAN_READY" if not errors else "SANDBOX_PATCH_PLAN_BLOCKED"
    return AlgorithmRepairSandboxResult(
        candidate_id=candidate_id,
        algorithm_id=algorithm_id,
        target_procedure=target_procedure,
        original_implementation_hash=original_hash,
        current_implementation_hash=current_hash,
        hash_matches_current_registry=hash_matches,
        algorithm_audit_ok=algorithm_audit_ok,
        sandbox_status=status,
        patch_applied_to_production=False,
        allowed_patch_scope=allowed_patch_scope,
        required_next_gate=(
            "apply bounded patch in isolated workspace, rerun algorithm audit, "
            "then rerun finite simulation diagnostics before promotion"
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _allowed_patch_scope(repair_kind: str) -> tuple[str, ...]:
    if repair_kind == "finite_metric_guard":
        return (
            "add finite-value metric guards",
            "record non-finite replicate diagnostics",
            "do not change estimand or theorem statement",
        )
    if repair_kind == "replicate_failure_rate_reduction":
        return (
            "reduce failed replicate rate with deterministic numerical guards",
            "preserve current statistical estimand",
            "rerun finite simulation diagnostics",
        )
    if repair_kind == "numerical_stability_guard":
        return (
            "add bounded-denominator or clipping guard",
            "preserve current estimator formula unless TheoryDeveloper revises it",
            "rerun algorithm audit",
        )
    return ()


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
        "# Algorithm Repair Sandbox Evaluation",
        "",
        f"- Promotion dir: `{payload.get('promotion_dir')}`",
        f"- Candidates: {payload.get('n_ok')}/{payload.get('n_candidates')} sandbox-ready",
        f"- Algorithm audit OK: {payload.get('algorithm_audit_all_ok')}",
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
