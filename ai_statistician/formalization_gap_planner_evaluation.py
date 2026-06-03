from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
)


FORMALIZATION_GAP_PLANNER_EVALUATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalizationGapPlannerEvaluationRow:
    schema_version: int
    evaluation_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    matched_ground_truth: bool
    match_key: str
    predicted_route_primitives: tuple[str, ...]
    ground_truth_route_primitives: tuple[str, ...]
    route_true_positive_primitives: tuple[str, ...]
    route_missing_primitives: tuple[str, ...]
    route_extra_primitives: tuple[str, ...]
    route_recall: float
    route_precision: float
    predicted_delta_primitives: tuple[str, ...]
    ground_truth_delta_primitives: tuple[str, ...]
    delta_true_positive_primitives: tuple[str, ...]
    delta_unnecessary_primitives: tuple[str, ...]
    delta_missing_primitives: tuple[str, ...]
    delta_precision: float
    delta_recall: float
    predicted_existing_reuse_primitives: tuple[str, ...]
    ground_truth_existing_reuse_primitives: tuple[str, ...]
    existing_reuse_precision: float
    existing_reuse_recall: float
    coverage_classification_accuracy: float
    n_coverage_classification_checked: int
    coverage_classification_confusions: tuple[dict[str, object], ...]
    two_dag_contract_ok: bool
    feedback_loop_ready: bool
    portable_schema_id: str
    proof_evidence_boundary_ok: bool
    kernel_verified_ground_truth: bool
    ok: bool
    errors: tuple[str, ...] = ()


def evaluate_formalization_gap_planner(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    ground_truth_path: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Evaluate a portable formalization-gap plan against held-out route truth.

    The ground truth file is intentionally lightweight and prover-agnostic. It
    may contain `routes`, `rows`, or `ground_truth_routes`; each item should be
    keyed by `route_id`, `display_name`, or `goal_plan_id`, and may provide:
    `required_primitives`, `actual_dependencies`, `actual_delta_primitives`,
    `actual_existing_reuse_primitives`, and `coverage_by_primitive`.
    """

    errors: list[str] = []
    plan_manifest_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    plan_payload = _read_json(plan_manifest_path, errors)
    truth_payload = _read_json(ground_truth_path, errors)
    plan_rows = [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
    truth_rows = _truth_rows(truth_payload)
    truth_index = _truth_index(truth_rows)
    evaluation_rows = [
        _evaluate_row(row, truth_index, plan_payload)
        for row in plan_rows
    ]
    matched_rows = [row for row in evaluation_rows if row.matched_ground_truth]
    matched_truth_keys = {
        row.match_key for row in matched_rows if row.match_key
    }
    truth_coverage_ok = not truth_rows or len(matched_truth_keys) >= len(truth_rows)
    by_ok = {True: 0, False: 0}
    for row in evaluation_rows:
        by_ok[row.ok] = by_ok.get(row.ok, 0) + 1
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_EVALUATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_evaluation",
        "evaluated_component": plan_payload.get("component_name", ""),
        "portable_schema_id": plan_payload.get("portable_schema_id", ""),
        "expected_portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_manifest_path),
        "ground_truth_path": str(ground_truth_path),
        "n_plan_rows": len(plan_rows),
        "n_ground_truth_rows": len(truth_rows),
        "n_evaluation_rows": len(evaluation_rows),
        "n_matched_ground_truth": sum(1 for row in evaluation_rows if row.matched_ground_truth),
        "n_missing_ground_truth": sum(1 for row in evaluation_rows if not row.matched_ground_truth),
        "n_unlabeled_plan_rows": sum(1 for row in evaluation_rows if not row.matched_ground_truth),
        "n_matched_ground_truth_ok": sum(row.ok for row in matched_rows),
        "n_ground_truth_rows_matched_by_plan": len(matched_truth_keys),
        "ground_truth_coverage_ok": truth_coverage_ok,
        "n_ok": sum(1 for row in evaluation_rows if row.ok),
        "n_two_dag_contract_ok": sum(1 for row in evaluation_rows if row.two_dag_contract_ok),
        "n_feedback_loop_ready": sum(1 for row in evaluation_rows if row.feedback_loop_ready),
        "n_kernel_verified_ground_truth": sum(
            1 for row in evaluation_rows if row.kernel_verified_ground_truth
        ),
        "mean_route_recall": _mean(row.route_recall for row in matched_rows),
        "mean_route_precision": _mean(row.route_precision for row in matched_rows),
        "mean_delta_precision": _mean(row.delta_precision for row in matched_rows),
        "mean_delta_recall": _mean(row.delta_recall for row in matched_rows),
        "mean_existing_reuse_precision": _mean(
            row.existing_reuse_precision for row in matched_rows
        ),
        "mean_existing_reuse_recall": _mean(
            row.existing_reuse_recall for row in matched_rows
        ),
        "mean_coverage_classification_accuracy": _mean(
            row.coverage_classification_accuracy
            for row in matched_rows
            if row.n_coverage_classification_checked > 0
        ),
        "all_ok": (
            not errors
            and bool(evaluation_rows)
            and all(row.ok for row in evaluation_rows)
            and truth_coverage_ok
        ),
        "errors": errors,
        "rows": [asdict(row) for row in evaluation_rows],
        "evaluation_fingerprint": stable_hash([asdict(row) for row in evaluation_rows]),
        "limitations": [
            "evaluation scores planner predictions against supplied route truth; it is not proof evidence",
            "route recall and delta precision depend on the quality and granularity of the ground truth file",
            "minimality proxy is structural; final proof status still requires target-prover kernel verification",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_gap_planner_evaluation_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_evaluation.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in evaluation_rows)
            + ("\n" if evaluation_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_evaluation.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _evaluate_row(
    row: dict[str, Any],
    truth_index: dict[str, dict[str, Any]],
    plan_payload: dict[str, Any],
) -> FormalizationGapPlannerEvaluationRow:
    errors: list[str] = []
    goal_plan_id = str(row.get("goal_plan_id", ""))
    route_id = str(row.get("route_id", ""))
    display_name = str(row.get("display_name", ""))
    truth, match_key = _match_truth(goal_plan_id, route_id, display_name, truth_index)

    predicted_route = _predicted_route_primitives(row)
    truth_route = _truth_route_primitives(truth)
    route_tp = tuple(sorted(set(predicted_route) & set(truth_route)))
    route_missing = tuple(sorted(set(truth_route) - set(predicted_route)))
    route_extra = tuple(sorted(set(predicted_route) - set(truth_route)))

    predicted_delta = _node_primitives(row.get("minimal_additional_formalization_nodes", []))
    truth_delta = _truth_delta_primitives(truth)
    delta_tp = tuple(sorted(set(predicted_delta) & set(truth_delta)))
    delta_unnecessary = tuple(sorted(set(predicted_delta) - set(truth_delta)))
    delta_missing = tuple(sorted(set(truth_delta) - set(predicted_delta)))

    predicted_existing = _node_primitives(row.get("existing_reuse_nodes", []))
    truth_existing = _str_tuple(truth.get("actual_existing_reuse_primitives", []))
    existing_tp = set(predicted_existing) & set(truth_existing)

    coverage_accuracy, coverage_checked, coverage_confusions = _coverage_accuracy(row, truth)
    two_dag_ok = bool(row.get("informal_knowledge_dag_nodes")) and bool(
        row.get("lean_realization_dag_nodes")
    )
    feedback_ready = _feedback_loop_ready(row)
    portable_schema_id = str(plan_payload.get("portable_schema_id", ""))
    proof_boundary_ok = "not theorem proof evidence" in str(
        row.get("proof_evidence_boundary", "")
    )
    if plan_payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("evaluated manifest is not the library-aware planner component")
    if portable_schema_id != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("portable schema id mismatch")
    if not two_dag_ok:
        errors.append("two-DAG contract is incomplete")
    if not feedback_ready:
        errors.append("feedback-loop hooks are incomplete")
    if not proof_boundary_ok:
        errors.append("proof evidence boundary is missing")

    return FormalizationGapPlannerEvaluationRow(
        schema_version=FORMALIZATION_GAP_PLANNER_EVALUATION_SCHEMA_VERSION,
        evaluation_id="formalization_gap_planner_evaluation:"
        + stable_hash([goal_plan_id, route_id, match_key])[:16],
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        matched_ground_truth=bool(truth),
        match_key=match_key,
        predicted_route_primitives=predicted_route,
        ground_truth_route_primitives=truth_route,
        route_true_positive_primitives=route_tp,
        route_missing_primitives=route_missing,
        route_extra_primitives=route_extra,
        route_recall=_ratio(len(route_tp), len(truth_route), empty_value=1.0),
        route_precision=_ratio(len(route_tp), len(predicted_route), empty_value=1.0),
        predicted_delta_primitives=predicted_delta,
        ground_truth_delta_primitives=truth_delta,
        delta_true_positive_primitives=delta_tp,
        delta_unnecessary_primitives=delta_unnecessary,
        delta_missing_primitives=delta_missing,
        delta_precision=_ratio(len(delta_tp), len(predicted_delta), empty_value=1.0),
        delta_recall=_ratio(len(delta_tp), len(truth_delta), empty_value=1.0),
        predicted_existing_reuse_primitives=predicted_existing,
        ground_truth_existing_reuse_primitives=truth_existing,
        existing_reuse_precision=_ratio(
            len(existing_tp),
            len(predicted_existing),
            empty_value=1.0,
        ),
        existing_reuse_recall=_ratio(
            len(existing_tp),
            len(truth_existing),
            empty_value=1.0,
        ),
        coverage_classification_accuracy=coverage_accuracy,
        n_coverage_classification_checked=coverage_checked,
        coverage_classification_confusions=coverage_confusions,
        two_dag_contract_ok=two_dag_ok,
        feedback_loop_ready=feedback_ready,
        portable_schema_id=portable_schema_id,
        proof_evidence_boundary_ok=proof_boundary_ok,
        kernel_verified_ground_truth=bool(truth.get("kernel_verified", False)),
        ok=not errors,
        errors=tuple(errors),
    )


def _predicted_route_primitives(row: dict[str, Any]) -> tuple[str, ...]:
    primitives = set(_str_tuple(row.get("selected_primitives", [])))
    primitives.update(_node_primitives(row.get("existing_reuse_nodes", [])))
    primitives.update(_node_primitives(row.get("minimal_additional_formalization_nodes", [])))
    return tuple(sorted(item for item in primitives if item))


def _truth_route_primitives(truth: dict[str, Any]) -> tuple[str, ...]:
    for field_name in ("required_primitives", "actual_dependencies", "route_primitives"):
        values = _str_tuple(truth.get(field_name, []))
        if values:
            return values
    return tuple()


def _truth_delta_primitives(truth: dict[str, Any]) -> tuple[str, ...]:
    explicit = _str_tuple(truth.get("actual_delta_primitives", []))
    if explicit:
        return explicit
    route = set(_truth_route_primitives(truth))
    existing = set(_str_tuple(truth.get("actual_existing_reuse_primitives", [])))
    return tuple(sorted(route - existing))


def _coverage_accuracy(
    row: dict[str, Any],
    truth: dict[str, Any],
) -> tuple[float, int, tuple[dict[str, object], ...]]:
    truth_coverage = truth.get("coverage_by_primitive", {})
    if not isinstance(truth_coverage, dict):
        return 1.0, 0, tuple()
    predicted = _predicted_coverage_by_primitive(row)
    checked = 0
    correct = 0
    confusions: list[dict[str, object]] = []
    for primitive, expected_status_raw in truth_coverage.items():
        expected_status = _normalize_coverage_status(str(expected_status_raw))
        predicted_status = _normalize_coverage_status(predicted.get(str(primitive), ""))
        if not predicted_status:
            continue
        checked += 1
        if predicted_status == expected_status:
            correct += 1
        else:
            confusions.append(
                {
                    "primitive": str(primitive),
                    "expected": expected_status,
                    "predicted": predicted_status,
                }
            )
    return _ratio(correct, checked, empty_value=1.0), checked, tuple(confusions)


def _predicted_coverage_by_primitive(row: dict[str, Any]) -> dict[str, str]:
    coverage: dict[str, str] = {}
    for primitive in _node_primitives(row.get("existing_reuse_nodes", [])):
        coverage[primitive] = "exact_exists"
    for primitive in _node_primitives(row.get("wrapper_nodes", [])):
        coverage[primitive] = "wrapper_needed"
    for primitive in _node_primitives(row.get("bridge_nodes", [])):
        coverage[primitive] = "bridge_needed"
    for primitive in _node_primitives(row.get("source_discovery_nodes", [])):
        coverage[primitive] = "definition_missing"
    for primitive in _node_primitives(row.get("first_principles_nodes", [])):
        coverage[primitive] = "theory_missing"
    return coverage


def _feedback_loop_ready(row: dict[str, Any]) -> bool:
    triggers = row.get("route_revision_triggers", [])
    hooks = row.get("interactive_refinement_hooks", [])
    hook_kinds = {
        str(item.get("hook_kind", ""))
        for item in hooks
        if isinstance(item, dict)
    }
    return bool(triggers) and {
        "literature_discovery",
        "lean_library_grounding",
        "proof_state_feedback",
    }.issubset(hook_kinds)


def _truth_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for field_name in ("routes", "rows", "ground_truth_routes"):
        rows = payload.get(field_name, [])
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _truth_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        for field_name in ("goal_plan_id", "route_id", "display_name"):
            value = str(row.get(field_name, ""))
            if value:
                index[f"{field_name}:{value}"] = row
    return index


def _match_truth(
    goal_plan_id: str,
    route_id: str,
    display_name: str,
    truth_index: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    for field_name, value in (
        ("route_id", route_id),
        ("goal_plan_id", goal_plan_id),
        ("display_name", display_name),
    ):
        key = f"{field_name}:{value}"
        if value and key in truth_index:
            return truth_index[key], key
    return {}, ""


def _node_primitives(nodes: Any) -> tuple[str, ...]:
    primitives: list[str] = []
    if not isinstance(nodes, (list, tuple)):
        return tuple()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        primitive = str(node.get("primitive", "") or node.get("label", ""))
        if primitive:
            primitives.append(primitive)
    return tuple(sorted(dict.fromkeys(primitives)))


def _normalize_coverage_status(value: str) -> str:
    aliases = {
        "already_exists": "exact_exists",
        "existing_in_library": "exact_exists",
        "exact_proof_bank_obligation_available": "exact_exists",
        "reuse_exact_proof_bank_obligation": "exact_exists",
        "near_match": "near_exists",
        "near_exists": "near_exists",
        "wrapper_needed": "wrapper_needed",
        "add_minimal_wrapper": "wrapper_needed",
        "bridge_needed": "bridge_needed",
        "design_bridge_lemma": "bridge_needed",
        "source_discovery_needed": "definition_missing",
        "source_port_needed": "definition_missing",
        "port_external_source": "definition_missing",
        "definition_missing": "definition_missing",
        "new_definition_or_theory_needed": "theory_missing",
        "design_from_first_principles": "theory_missing",
        "theory_missing": "theory_missing",
    }
    return aliases.get(value, value)


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(sorted(dict.fromkeys(str(item) for item in values if str(item))))


def _ratio(numerator: int, denominator: int, *, empty_value: float) -> float:
    if denominator == 0:
        return empty_value
    return numerator / denominator


def _mean(values: Any) -> float:
    items = [float(value) for value in values]
    if not items:
        return 0.0
    return sum(items) / len(items)


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
        "# Formalization Gap Planner Evaluation",
        "",
        f"- Evaluation rows: {payload.get('n_evaluation_rows')}",
        f"- Matched ground truth: {payload.get('n_matched_ground_truth')}",
        f"- Ground-truth rows matched by plan: {payload.get('n_ground_truth_rows_matched_by_plan')}",
        f"- Unlabeled plan rows: {payload.get('n_unlabeled_plan_rows')}",
        f"- Mean route recall: {payload.get('mean_route_recall')}",
        f"- Mean route precision: {payload.get('mean_route_precision')}",
        f"- Mean delta precision: {payload.get('mean_delta_precision')}",
        f"- Mean delta recall: {payload.get('mean_delta_recall')}",
        f"- Mean coverage classification accuracy: {payload.get('mean_coverage_classification_accuracy')}",
        f"- Two-DAG ready: {payload.get('n_two_dag_contract_ok')}",
        f"- Feedback-loop ready: {payload.get('n_feedback_loop_ready')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        "This evaluation is benchmark evidence for route planning quality, not theorem proof evidence.",
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` recall={row.get('route_recall')} "
            f"precision={row.get('route_precision')} delta_precision={row.get('delta_precision')} "
            f"delta_recall={row.get('delta_recall')} ok={row.get('ok')}"
        )
        if row.get("route_missing_primitives"):
            lines.append(
                "  missing route primitives: "
                + ", ".join(str(item) for item in row.get("route_missing_primitives", [])[:8])
            )
        if row.get("delta_unnecessary_primitives"):
            lines.append(
                "  unnecessary delta primitives: "
                + ", ".join(str(item) for item in row.get("delta_unnecessary_primitives", [])[:8])
            )
    return "\n".join(lines) + "\n"
