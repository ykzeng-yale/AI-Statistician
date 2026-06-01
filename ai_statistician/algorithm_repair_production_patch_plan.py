from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .research_lab import RESEARCH_ALGORITHM_REGISTRY, audit_research_algorithm_registry


ALGORITHM_REPAIR_PRODUCTION_PATCH_PLAN_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AlgorithmRepairProductionPatchPlan:
    plan_id: str
    example_id: str
    patch_eval_id: str
    algorithm_id: str
    target_procedure: str
    source_file: str
    target_symbol: str
    patch_kind: str
    patch_summary: str
    predicted_decision: str
    comparison_status: str
    gold_score: float
    unsafe_score: float
    review_required: bool
    production_patch_applied: bool
    promotion_ready: bool
    required_source_edits: tuple[str, ...]
    release_gates: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


def export_algorithm_repair_production_patch_plan(
    policy_model_dir: Path,
    out_dir: Path,
) -> dict[str, object]:
    """Export reviewed production patch plans from safe patch-policy predictions.

    This is the bridge after the learned safety policy and before source
    mutation.  It creates concrete reviewed-change plans with target files,
    method symbols, required edits, and release gates, but it deliberately does
    not edit production code.
    """

    errors: list[str] = []
    manifest_path = policy_model_dir / "algorithm_repair_patch_policy_model_manifest.json"
    manifest = _load_json(manifest_path, errors)
    train_examples = _load_jsonl(Path(str(manifest.get("train_jsonl", ""))), errors)
    validation_examples = _load_jsonl(Path(str(manifest.get("validation_jsonl", ""))), errors)
    example_index = {
        str(row.get("example_id", "")): row
        for row in [*train_examples, *validation_examples]
        if isinstance(row, dict) and row.get("example_id")
    }
    train_predictions = _load_jsonl(Path(str(manifest.get("train_predictions_jsonl", ""))), errors)
    validation_predictions = _load_jsonl(Path(str(manifest.get("validation_predictions_jsonl", ""))), errors)
    predictions = _dedupe_predictions([*train_predictions, *validation_predictions])
    registry_audit = audit_research_algorithm_registry()
    plans = [
        _plan_for_prediction(row, example_index, registry_audit_ok=bool(registry_audit.get("all_ok")))
        for row in predictions
        if isinstance(row, dict) and _prediction_is_safe(row)
    ]
    by_kind = Counter(row.patch_kind for row in plans)
    by_decision = Counter(row.predicted_decision for row in plans)
    out_dir.mkdir(parents=True, exist_ok=True)
    plans_path = out_dir / "algorithm_repair_production_patch_plans.jsonl"
    _write_jsonl(plans_path, [asdict(row) for row in plans])
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_REPAIR_PRODUCTION_PATCH_PLAN_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy_model_dir": str(policy_model_dir),
        "policy_manifest": str(manifest_path),
        "algorithm_audit_all_ok": bool(registry_audit.get("all_ok")),
        "algorithm_registry_fingerprint": str(registry_audit.get("registry_fingerprint", "")),
        "n_predictions": len(predictions),
        "n_safe_predictions": sum(1 for row in predictions if _prediction_is_safe(row)),
        "n_plans": len(plans),
        "n_ok": sum(1 for row in plans if row.ok),
        "n_review_required": sum(1 for row in plans if row.review_required),
        "n_production_patches_applied": sum(1 for row in plans if row.production_patch_applied),
        "n_promotion_ready": sum(1 for row in plans if row.promotion_ready),
        "by_patch_kind": dict(sorted(by_kind.items())),
        "by_predicted_decision": dict(sorted(by_decision.items())),
        "plans_jsonl": str(plans_path),
        "dataset_fingerprint": stable_hash([asdict(row) for row in plans]),
        "all_ok": (
            not errors
            and bool(manifest.get("all_ok"))
            and all(row.ok for row in plans)
            and all(row.review_required for row in plans)
            and not any(row.production_patch_applied for row in plans)
            and not any(row.promotion_ready for row in plans)
        ),
        "errors": errors,
        "limitations": [
            "exports reviewed source-change plans only; no production files are edited",
            "plan quality depends on the upstream isolated patch-eval and policy-model evidence",
            "promotion still requires implementing the reviewed source edit, rerunning algorithm audit, and rerunning finite simulation before/after checks",
        ],
    }
    (out_dir / "algorithm_repair_production_patch_plan_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "algorithm_repair_production_patch_plan.md").write_text(
        _markdown_report(payload, plans),
        encoding="utf-8",
    )
    return payload


def _plan_for_prediction(
    prediction: dict[str, Any],
    example_index: dict[str, dict[str, Any]],
    *,
    registry_audit_ok: bool,
) -> AlgorithmRepairProductionPatchPlan:
    errors: list[str] = []
    example_id = str(prediction.get("example_id", ""))
    example = example_index.get(example_id, {})
    algorithm_id = str(prediction.get("algorithm_id", "") or example.get("algorithm_id", ""))
    target_procedure = str(prediction.get("target_procedure", "") or example.get("target_procedure", ""))
    record = RESEARCH_ALGORITHM_REGISTRY.get(algorithm_id)
    if record is None:
        errors.append(f"unknown research algorithm: {algorithm_id}")
        target_symbol = ""
    else:
        target_symbol = f"ResearchSimulator.{record.get('method', '')}"
    if not registry_audit_ok:
        errors.append("current algorithm registry audit is not OK")
    predicted_decision = str(prediction.get("predicted_decision", ""))
    if predicted_decision != "hold_for_reviewed_production_commit":
        errors.append(f"unsafe predicted decision for production patch planning: {predicted_decision}")
    if prediction.get("predicted_production_patch_applied") is True:
        errors.append("prediction claims a production patch was already applied")
    if prediction.get("predicted_promotion_ready") is True:
        errors.append("prediction claims the patch is already promotion-ready")
    patch_eval_id = str(prediction.get("patch_eval_id", "") or example.get("patch_eval_id", ""))
    comparison_status = str(example.get("comparison_status", ""))
    patch_kind = _patch_kind(example)
    required_source_edits = _required_source_edits(patch_kind, target_symbol)
    release_gates = (
        "implement the reviewed source edit in ai_statistician/research_lab.py",
        "rerun research algorithm registry audit and verify implementation hash change is intentional",
        "rerun isolated before/after simulation comparison on the affected procedure",
        "rerun full research-system audit before promotion",
    )
    return AlgorithmRepairProductionPatchPlan(
        plan_id="algorithm_repair_production_patch_plan:"
        f"{stable_hash([example_id, patch_eval_id, algorithm_id, target_procedure])[:16]}",
        example_id=example_id,
        patch_eval_id=patch_eval_id,
        algorithm_id=algorithm_id,
        target_procedure=target_procedure,
        source_file="ai_statistician/research_lab.py",
        target_symbol=target_symbol,
        patch_kind=patch_kind,
        patch_summary=_patch_summary(patch_kind, target_symbol),
        predicted_decision=predicted_decision,
        comparison_status=comparison_status,
        gold_score=float(prediction.get("gold_score", 0.0) or 0.0),
        unsafe_score=float(prediction.get("unsafe_score", 0.0) or 0.0),
        review_required=True,
        production_patch_applied=False,
        promotion_ready=False,
        required_source_edits=required_source_edits,
        release_gates=release_gates,
        ok=not errors,
        errors=tuple(errors),
    )


def _prediction_is_safe(row: dict[str, Any]) -> bool:
    return (
        row.get("chose_gold") is True
        and row.get("rejected_unsafe") is True
        and row.get("predicted_valid_json") is True
        and str(row.get("predicted_decision", "")) == "hold_for_reviewed_production_commit"
        and row.get("predicted_production_patch_applied") is not True
        and row.get("predicted_promotion_ready") is not True
    )


def _patch_kind(example: dict[str, Any]) -> str:
    prompt = str(example.get("prompt", "")).lower()
    if "nonfinite" in prompt or "finite_guard" in prompt or "finite-metric" in prompt:
        return "finite_metric_guard"
    return "reviewed_algorithm_repair"


def _patch_summary(patch_kind: str, target_symbol: str) -> str:
    if patch_kind == "finite_metric_guard":
        return f"Port the isolated finite-metric guard into {target_symbol} or a shared simulator metric guard helper."
    return f"Apply a reviewed bounded algorithm repair around {target_symbol}."


def _required_source_edits(patch_kind: str, target_symbol: str) -> tuple[str, ...]:
    if patch_kind == "finite_metric_guard":
        return (
            f"Add finite-value metric validation around outputs produced by {target_symbol}.",
            "Record the number and names of repaired non-finite metrics in simulation diagnostics.",
            "Preserve estimand, theorem goals, and algorithm registry status unless separately reviewed.",
        )
    return (
        f"Make the minimal reviewed source edit affecting {target_symbol}.",
        "Preserve estimator target and theorem statements unless a theory revision is separately approved.",
    )


def _dedupe_predictions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("example_id", ""))
        if key and key not in deduped:
            deduped[key] = row
    return [deduped[key] for key in sorted(deduped)]


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
    if not str(path):
        return []
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


def _markdown_report(payload: dict[str, object], plans: list[AlgorithmRepairProductionPatchPlan]) -> str:
    lines = [
        "# Algorithm Repair Production Patch Plans",
        "",
        f"- Policy model dir: `{payload.get('policy_model_dir')}`",
        f"- Plans: {payload.get('n_ok')}/{payload.get('n_plans')}",
        f"- Review required: {payload.get('n_review_required')}",
        f"- Production patches applied: {payload.get('n_production_patches_applied')}",
        f"- Promotion ready: {payload.get('n_promotion_ready')}",
        "",
        "## Plans",
        "",
    ]
    if plans:
        for plan in plans:
            lines.append(f"- `{plan.plan_id}` -> `{plan.target_symbol}` ({plan.patch_kind})")
    else:
        lines.append("- none")
    if payload.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in payload.get("errors", []):
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)
