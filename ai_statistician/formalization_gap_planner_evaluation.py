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
EVALUATION_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-evaluation-row:1"
)
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_EVALUATION_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner evaluation rows score route predictions against "
    "route-truth labels. They are evaluation diagnostics, not theorem proof "
    "evidence."
)


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
    predicted_residual_primitives: tuple[str, ...]
    ground_truth_residual_primitives: tuple[str, ...]
    residual_true_positive_primitives: tuple[str, ...]
    residual_missing_primitives: tuple[str, ...]
    residual_extra_primitives: tuple[str, ...]
    residual_precision: float
    residual_recall: float
    predicted_residual_goals: tuple[str, ...]
    ground_truth_residual_goals: tuple[str, ...]
    predicted_existing_reuse_primitives: tuple[str, ...]
    ground_truth_existing_reuse_primitives: tuple[str, ...]
    existing_reuse_precision: float
    existing_reuse_recall: float
    coverage_classification_accuracy: float
    n_coverage_classification_checked: int
    coverage_classification_confusions: tuple[dict[str, object], ...]
    two_dag_contract_ok: bool
    alignment_contract_ok: bool
    alignment_coverage: float
    aligned_primitives: tuple[str, ...]
    unaligned_primitives: tuple[str, ...]
    feedback_loop_ready: bool
    minimal_delta_cost_graph_present: bool
    minimal_delta_route_option_count: int
    minimal_delta_selected_route_option_id: str
    minimal_delta_selected_route_cost: float
    realization_coverage_witness_present: bool
    realization_coverage_complete: bool
    realization_missing_selected_formal_primitives: tuple[str, ...]
    realization_missing_delta_alignment_primitives: tuple[str, ...]
    llm_route_planner_trace_present: bool
    llm_route_planner_row_id: str
    llm_route_planner_provider: str
    llm_route_planner_model: str
    llm_route_planner_model_tier: str
    llm_route_planner_acceptance_status: str
    llm_route_planner_model_selection_rationale: str
    llm_route_planner_has_generator_metadata: bool
    llm_route_planner_generator_metadata_keys: tuple[str, ...]
    portable_schema_id: str
    proof_evidence_boundary_ok: bool
    kernel_verified_ground_truth: bool
    proof_evidence_status: str
    proof_evidence_boundary: str
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
    `actual_existing_reuse_primitives`, `coverage_by_primitive`,
    `expected_residual_primitives`, and `expected_residual_goals`.
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
    evaluation_row_dicts = [asdict(row) for row in evaluation_rows]
    evaluation_row_schema = evaluation_row_json_schema()
    evaluation_row_schema_errors = [
        validate_evaluation_row(row, evaluation_row_schema)
        for row in evaluation_row_dicts
    ]
    n_evaluation_row_schema_valid = sum(
        1 for row_errors in evaluation_row_schema_errors if not row_errors
    )
    matched_rows = [row for row in evaluation_rows if row.matched_ground_truth]
    matched_truth_keys = {
        row.match_key for row in matched_rows if row.match_key
    }
    truth_coverage_ok = not truth_rows or len(matched_truth_keys) >= len(truth_rows)
    by_ok = {True: 0, False: 0}
    for row in evaluation_rows:
        by_ok[row.ok] = by_ok.get(row.ok, 0) + 1
    by_llm_model_tier = _llm_model_tier_summary(evaluation_rows)
    realization_missing_selected = _unique_row_attr_strings(
        evaluation_rows,
        "realization_missing_selected_formal_primitives",
    )
    realization_missing_delta = _unique_row_attr_strings(
        evaluation_rows,
        "realization_missing_delta_alignment_primitives",
    )
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
        "bundled_ground_truth_filename": "formalization_gap_planner_evaluation_ground_truth.json",
        "n_plan_rows": len(plan_rows),
        "n_ground_truth_rows": len(truth_rows),
        "n_evaluation_rows": len(evaluation_rows),
        "n_evaluation_row_schema_valid": n_evaluation_row_schema_valid,
        "n_evaluation_row_schema_invalid": len(evaluation_row_schema_errors)
        - n_evaluation_row_schema_valid,
        "n_matched_ground_truth": sum(1 for row in evaluation_rows if row.matched_ground_truth),
        "n_missing_ground_truth": sum(1 for row in evaluation_rows if not row.matched_ground_truth),
        "n_unlabeled_plan_rows": sum(1 for row in evaluation_rows if not row.matched_ground_truth),
        "n_matched_ground_truth_ok": sum(row.ok for row in matched_rows),
        "n_ground_truth_rows_matched_by_plan": len(matched_truth_keys),
        "ground_truth_coverage_ok": truth_coverage_ok,
        "n_ok": sum(1 for row in evaluation_rows if row.ok),
        "n_two_dag_contract_ok": sum(1 for row in evaluation_rows if row.two_dag_contract_ok),
        "n_alignment_contract_ok": sum(
            1 for row in evaluation_rows if row.alignment_contract_ok
        ),
        "n_feedback_loop_ready": sum(1 for row in evaluation_rows if row.feedback_loop_ready),
        "n_rows_with_minimal_delta_cost_graph": sum(
            1 for row in evaluation_rows if row.minimal_delta_cost_graph_present
        ),
        "n_rows_with_realization_coverage_witness": sum(
            1 for row in evaluation_rows if row.realization_coverage_witness_present
        ),
        "n_rows_with_complete_realization_coverage": sum(
            1 for row in evaluation_rows if row.realization_coverage_complete
        ),
        "n_rows_with_llm_route_planner_trace": sum(
            1 for row in evaluation_rows if row.llm_route_planner_trace_present
        ),
        "n_rows_with_llm_route_planner_model_tier": sum(
            1 for row in evaluation_rows if row.llm_route_planner_model_tier
        ),
        "n_rows_with_llm_route_planner_generator_metadata": sum(
            1
            for row in evaluation_rows
            if row.llm_route_planner_has_generator_metadata
        ),
        "evaluation_by_llm_model_tier": by_llm_model_tier,
        "n_realization_missing_selected_formal_primitives": sum(
            len(row.realization_missing_selected_formal_primitives)
            for row in evaluation_rows
        ),
        "realization_missing_selected_formal_primitives": realization_missing_selected,
        "n_realization_missing_delta_alignment_primitives": sum(
            len(row.realization_missing_delta_alignment_primitives)
            for row in evaluation_rows
        ),
        "realization_missing_delta_alignment_primitives": realization_missing_delta,
        "realization_missing_primitives_by_route": (
            _realization_missing_primitives_by_route(evaluation_rows)
        ),
        "n_minimal_delta_route_options": sum(
            row.minimal_delta_route_option_count for row in evaluation_rows
        ),
        "mean_minimal_delta_selected_route_cost": _mean(
            row.minimal_delta_selected_route_cost
            for row in evaluation_rows
            if row.minimal_delta_cost_graph_present
        ),
        "n_unaligned_primitives": sum(
            len(row.unaligned_primitives) for row in evaluation_rows
        ),
        "n_kernel_verified_ground_truth": sum(
            1 for row in evaluation_rows if row.kernel_verified_ground_truth
        ),
        "mean_route_recall": _mean(row.route_recall for row in matched_rows),
        "mean_route_precision": _mean(row.route_precision for row in matched_rows),
        "mean_delta_precision": _mean(row.delta_precision for row in matched_rows),
        "mean_delta_recall": _mean(row.delta_recall for row in matched_rows),
        "n_ground_truth_residual_rows": sum(
            1 for row in matched_rows if row.ground_truth_residual_primitives
        ),
        "n_predicted_residual_primitives": sum(
            len(row.predicted_residual_primitives) for row in matched_rows
        ),
        "n_ground_truth_residual_primitives": sum(
            len(row.ground_truth_residual_primitives) for row in matched_rows
        ),
        "mean_residual_precision": _mean(
            row.residual_precision
            for row in matched_rows
            if row.ground_truth_residual_primitives
            or row.predicted_residual_primitives
        ),
        "mean_residual_recall": _mean(
            row.residual_recall
            for row in matched_rows
            if row.ground_truth_residual_primitives
        ),
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
        "mean_alignment_coverage": _mean(
            row.alignment_coverage for row in evaluation_rows
        ),
        "all_ok": (
            not errors
            and bool(evaluation_rows)
            and all(row.ok for row in evaluation_rows)
            and truth_coverage_ok
            and len(evaluation_row_schema_errors) == n_evaluation_row_schema_valid
        ),
        "errors": errors,
        "evaluation_row_schema": evaluation_row_schema,
        "rows": evaluation_row_dicts,
        "evaluation_fingerprint": stable_hash(evaluation_row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
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
            "\n".join(json.dumps(row, sort_keys=True) for row in evaluation_row_dicts)
            + ("\n" if evaluation_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_evaluation_row.schema.json").write_text(
            json.dumps(evaluation_row_schema, indent=2),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_evaluation_ground_truth.json"
        ).write_text(
            json.dumps(truth_payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_evaluation.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def evaluation_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": EVALUATION_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Evaluation Row",
        "description": (
            "Per-route evaluation diagnostics comparing planner route and "
            "minimal-delta predictions against route-truth labels. Rows are not "
            "theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "evaluation_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "matched_ground_truth",
            "match_key",
            "predicted_route_primitives",
            "ground_truth_route_primitives",
            "route_true_positive_primitives",
            "route_missing_primitives",
            "route_extra_primitives",
            "route_recall",
            "route_precision",
            "predicted_delta_primitives",
            "ground_truth_delta_primitives",
            "delta_true_positive_primitives",
            "delta_unnecessary_primitives",
            "delta_missing_primitives",
            "delta_precision",
            "delta_recall",
            "predicted_residual_primitives",
            "ground_truth_residual_primitives",
            "residual_true_positive_primitives",
            "residual_missing_primitives",
            "residual_extra_primitives",
            "residual_precision",
            "residual_recall",
            "predicted_residual_goals",
            "ground_truth_residual_goals",
            "predicted_existing_reuse_primitives",
            "ground_truth_existing_reuse_primitives",
            "existing_reuse_precision",
            "existing_reuse_recall",
            "coverage_classification_accuracy",
            "n_coverage_classification_checked",
            "coverage_classification_confusions",
            "two_dag_contract_ok",
            "alignment_contract_ok",
            "alignment_coverage",
            "aligned_primitives",
            "unaligned_primitives",
            "feedback_loop_ready",
            "minimal_delta_cost_graph_present",
            "minimal_delta_route_option_count",
            "minimal_delta_selected_route_option_id",
            "minimal_delta_selected_route_cost",
            "realization_coverage_witness_present",
            "realization_coverage_complete",
            "realization_missing_selected_formal_primitives",
            "realization_missing_delta_alignment_primitives",
            "llm_route_planner_trace_present",
            "llm_route_planner_row_id",
            "llm_route_planner_provider",
            "llm_route_planner_model",
            "llm_route_planner_model_tier",
            "llm_route_planner_acceptance_status",
            "llm_route_planner_model_selection_rationale",
            "llm_route_planner_has_generator_metadata",
            "llm_route_planner_generator_metadata_keys",
            "portable_schema_id",
            "proof_evidence_boundary_ok",
            "kernel_verified_ground_truth",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_EVALUATION_SCHEMA_VERSION,
            },
            "evaluation_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "matched_ground_truth": {"type": "boolean"},
            "match_key": {"type": "string"},
            "predicted_route_primitives": string_array,
            "ground_truth_route_primitives": string_array,
            "route_true_positive_primitives": string_array,
            "route_missing_primitives": string_array,
            "route_extra_primitives": string_array,
            "route_recall": {"type": "number"},
            "route_precision": {"type": "number"},
            "predicted_delta_primitives": string_array,
            "ground_truth_delta_primitives": string_array,
            "delta_true_positive_primitives": string_array,
            "delta_unnecessary_primitives": string_array,
            "delta_missing_primitives": string_array,
            "delta_precision": {"type": "number"},
            "delta_recall": {"type": "number"},
            "predicted_residual_primitives": string_array,
            "ground_truth_residual_primitives": string_array,
            "residual_true_positive_primitives": string_array,
            "residual_missing_primitives": string_array,
            "residual_extra_primitives": string_array,
            "residual_precision": {"type": "number"},
            "residual_recall": {"type": "number"},
            "predicted_residual_goals": string_array,
            "ground_truth_residual_goals": string_array,
            "predicted_existing_reuse_primitives": string_array,
            "ground_truth_existing_reuse_primitives": string_array,
            "existing_reuse_precision": {"type": "number"},
            "existing_reuse_recall": {"type": "number"},
            "coverage_classification_accuracy": {"type": "number"},
            "n_coverage_classification_checked": {"type": "integer"},
            "coverage_classification_confusions": object_array,
            "two_dag_contract_ok": {"type": "boolean"},
            "alignment_contract_ok": {"type": "boolean"},
            "alignment_coverage": {"type": "number"},
            "aligned_primitives": string_array,
            "unaligned_primitives": string_array,
            "feedback_loop_ready": {"type": "boolean"},
            "minimal_delta_cost_graph_present": {"type": "boolean"},
            "minimal_delta_route_option_count": {"type": "integer", "minimum": 0},
            "minimal_delta_selected_route_option_id": {"type": "string"},
            "minimal_delta_selected_route_cost": {"type": "number", "minimum": 0},
            "realization_coverage_witness_present": {"type": "boolean"},
            "realization_coverage_complete": {"type": "boolean"},
            "realization_missing_selected_formal_primitives": string_array,
            "realization_missing_delta_alignment_primitives": string_array,
            "llm_route_planner_trace_present": {"type": "boolean"},
            "llm_route_planner_row_id": {"type": "string"},
            "llm_route_planner_provider": {"type": "string"},
            "llm_route_planner_model": {"type": "string"},
            "llm_route_planner_model_tier": {"type": "string"},
            "llm_route_planner_acceptance_status": {"type": "string"},
            "llm_route_planner_model_selection_rationale": {"type": "string"},
            "llm_route_planner_has_generator_metadata": {"type": "boolean"},
            "llm_route_planner_generator_metadata_keys": string_array,
            "portable_schema_id": {"type": "string", "minLength": 1},
            "proof_evidence_boundary_ok": {"type": "boolean"},
            "kernel_verified_ground_truth": {"type": "boolean"},
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_evaluation_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    row_schema = schema or evaluation_row_json_schema()
    if not isinstance(row, dict):
        return ("evaluation row must be object",)
    errors: list[str] = []
    required = row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(_schema_property_errors(field_name, row[field_name], field_schema))
    return tuple(errors)


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

    predicted_residual_goals = _predicted_residual_goals(row)
    truth_residual_goals = _truth_residual_goals(truth)
    predicted_residual = _predicted_residual_primitives(
        row,
        predicted_route,
        predicted_residual_goals,
    )
    truth_residual = _truth_residual_primitives(truth)
    residual_tp = tuple(sorted(set(predicted_residual) & set(truth_residual)))
    residual_missing = tuple(sorted(set(truth_residual) - set(predicted_residual)))
    residual_extra = tuple(sorted(set(predicted_residual) - set(truth_residual)))

    predicted_existing = _node_primitives(row.get("existing_reuse_nodes", []))
    truth_existing = _str_tuple(truth.get("actual_existing_reuse_primitives", []))
    existing_tp = set(predicted_existing) & set(truth_existing)

    coverage_accuracy, coverage_checked, coverage_confusions = _coverage_accuracy(row, truth)
    two_dag_ok = bool(row.get("informal_knowledge_dag_nodes")) and bool(
        _formal_realization_nodes(row)
    )
    alignment_ok, alignment_coverage, aligned, unaligned = _alignment_contract(row)
    feedback_ready = _feedback_loop_ready(row)
    cost_graph_trace = _minimal_delta_cost_graph_trace(row)
    realization_trace = _realization_coverage_witness_trace(row)
    llm_trace = _llm_route_planner_trace(row)
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
    if not alignment_ok:
        errors.append("route alignment contract is incomplete")
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
        predicted_residual_primitives=predicted_residual,
        ground_truth_residual_primitives=truth_residual,
        residual_true_positive_primitives=residual_tp,
        residual_missing_primitives=residual_missing,
        residual_extra_primitives=residual_extra,
        residual_precision=_ratio(
            len(residual_tp),
            len(predicted_residual),
            empty_value=1.0,
        ),
        residual_recall=_ratio(
            len(residual_tp),
            len(truth_residual),
            empty_value=1.0,
        ),
        predicted_residual_goals=predicted_residual_goals,
        ground_truth_residual_goals=truth_residual_goals,
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
        alignment_contract_ok=alignment_ok,
        alignment_coverage=alignment_coverage,
        aligned_primitives=aligned,
        unaligned_primitives=unaligned,
        feedback_loop_ready=feedback_ready,
        minimal_delta_cost_graph_present=bool(cost_graph_trace["present"]),
        minimal_delta_route_option_count=int(cost_graph_trace["route_option_count"]),
        minimal_delta_selected_route_option_id=str(
            cost_graph_trace["selected_route_option_id"]
        ),
        minimal_delta_selected_route_cost=float(
            cost_graph_trace["selected_route_cost"]
        ),
        realization_coverage_witness_present=bool(realization_trace["present"]),
        realization_coverage_complete=bool(realization_trace["complete"]),
        realization_missing_selected_formal_primitives=_str_tuple(
            realization_trace["missing_selected_formal_primitives"]
        ),
        realization_missing_delta_alignment_primitives=_str_tuple(
            realization_trace["missing_delta_alignment_primitives"]
        ),
        llm_route_planner_trace_present=bool(llm_trace["trace_present"]),
        llm_route_planner_row_id=str(llm_trace["row_id"]),
        llm_route_planner_provider=str(llm_trace["provider"]),
        llm_route_planner_model=str(llm_trace["model"]),
        llm_route_planner_model_tier=str(llm_trace["model_tier"]),
        llm_route_planner_acceptance_status=str(llm_trace["acceptance_status"]),
        llm_route_planner_model_selection_rationale=str(
            llm_trace["model_selection_rationale"]
        ),
        llm_route_planner_has_generator_metadata=bool(
            llm_trace["has_generator_metadata"]
        ),
        llm_route_planner_generator_metadata_keys=_str_tuple(
            llm_trace["generator_metadata_keys"]
        ),
        portable_schema_id=portable_schema_id,
        proof_evidence_boundary_ok=proof_boundary_ok,
        kernel_verified_ground_truth=bool(truth.get("kernel_verified", False)),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
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


def _truth_residual_primitives(truth: dict[str, Any]) -> tuple[str, ...]:
    for field_name in (
        "expected_residual_primitives",
        "actual_residual_primitives",
        "residual_primitives",
        "expected_side_condition_primitives",
    ):
        values = _str_tuple(truth.get(field_name, []))
        if values:
            return values
    return tuple()


def _truth_residual_goals(truth: dict[str, Any]) -> tuple[str, ...]:
    for field_name in (
        "expected_residual_goals",
        "actual_residual_goals",
        "residual_goals",
        "expected_side_conditions",
    ):
        values = _str_tuple(truth.get(field_name, []))
        if values:
            return values
    return tuple()


def _predicted_residual_primitives(
    row: dict[str, Any],
    predicted_route: tuple[str, ...],
    predicted_residual_goals: tuple[str, ...],
) -> tuple[str, ...]:
    explicit = _str_tuple(
        [
            *_str_tuple(row.get("predicted_residual_primitives", [])),
            *_str_tuple(row.get("residual_primitives", [])),
        ]
    )
    from_goals = _residual_primitives_from_texts(
        predicted_residual_goals,
        predicted_route,
    )
    return _str_tuple([*explicit, *from_goals])


def _predicted_residual_goals(row: dict[str, Any]) -> tuple[str, ...]:
    goals: list[str] = []
    goals.extend(_str_tuple(row.get("residual_goals", [])))
    goals.extend(_str_tuple(row.get("blocked_only_by", [])))
    trace = row.get("standalone_input_trace", {})
    if isinstance(trace, dict):
        goals.extend(_str_tuple(trace.get("residual_goals", [])))
        metadata = trace.get("replan_metadata", {})
        if isinstance(metadata, dict):
            goals.extend(_str_tuple(metadata.get("residual_goals", [])))
    for trigger in row.get("route_revision_triggers", []):
        if not isinstance(trigger, dict):
            continue
        if str(trigger.get("trigger_kind", "")) in {
            "blocked_by_formal_side_condition",
            "prover_feedback_residual",
            "proof_state_residual",
        }:
            goals.extend(
                _str_tuple(
                    [
                        trigger.get("condition", ""),
                        trigger.get("residual_goal", ""),
                    ]
                )
            )
    for node in _all_node_dicts(row):
        goals.extend(_str_tuple(node.get("side_conditions", [])))
        goals.extend(_str_tuple(node.get("blocked_reasons", [])))
    for packet in row.get("portable_work_packets", []):
        if not isinstance(packet, dict):
            continue
        goals.extend(_str_tuple(packet.get("residual_goals", [])))
        goals.extend(_str_tuple(packet.get("side_conditions", [])))
    return _str_tuple(goals)


def _residual_primitives_from_texts(
    texts: tuple[str, ...],
    candidate_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    candidates = tuple(sorted(set(candidate_primitives), key=len, reverse=True))
    primitives: list[str] = []
    for text in texts:
        normalized = str(text)
        prefix = normalized.split(":", 1)[0].strip()
        if prefix and " " not in prefix and prefix in candidate_primitives:
            primitives.append(prefix)
        for primitive in candidates:
            if primitive and primitive in normalized:
                primitives.append(primitive)
    return _str_tuple(primitives)


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


def _all_node_dicts(row: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    nodes: list[dict[str, Any]] = []
    for field_name in (
        "existing_reuse_nodes",
        "wrapper_nodes",
        "bridge_nodes",
        "source_discovery_nodes",
        "first_principles_nodes",
        "minimal_additional_formalization_nodes",
        "informal_knowledge_dag_nodes",
        "formal_realization_dag_nodes",
        "lean_realization_dag_nodes",
    ):
        for node in row.get(field_name, []):
            if isinstance(node, dict):
                nodes.append(node)
    return tuple(nodes)


def _feedback_loop_ready(row: dict[str, Any]) -> bool:
    triggers = row.get("route_revision_triggers", [])
    hooks = row.get("interactive_refinement_hooks", [])
    hook_kinds = {
        str(item.get("hook_kind", ""))
        for item in hooks
        if isinstance(item, dict)
    }
    has_formal_grounding = bool(
        {"formal_library_grounding", "lean_library_grounding"} & hook_kinds
    )
    return (
        bool(triggers)
        and "literature_discovery" in hook_kinds
        and has_formal_grounding
        and "proof_state_feedback" in hook_kinds
    )


def _minimal_delta_cost_graph_trace(row: dict[str, Any]) -> dict[str, object]:
    trace = row.get("standalone_input_trace", {})
    trace = trace if isinstance(trace, dict) else {}
    graph = trace.get("minimal_delta_and_or_cost_graph", {})
    graph = graph if isinstance(graph, dict) else {}
    options = [
        option
        for option in graph.get("route_options", [])
        if isinstance(option, dict)
    ]
    selected_id = str(trace.get("minimal_delta_selected_route_option_id", "")).strip()
    selected_cost = trace.get("minimal_delta_selected_route_cost", 0.0)
    if not selected_id or not isinstance(selected_cost, (int, float)) or isinstance(selected_cost, bool):
        selected = {}
        graph_selected_id = str(graph.get("selected_route_option_id", "")).strip()
        for option in options:
            if bool(option.get("selected", False)):
                selected = option
                break
        if not selected and graph_selected_id:
            for option in options:
                if str(option.get("route_option_id", "")).strip() == graph_selected_id:
                    selected = option
                    break
        if selected:
            selected_id = str(selected.get("route_option_id", selected_id)).strip()
            selected_cost = selected.get("route_cost", selected_cost)
    if not isinstance(selected_cost, (int, float)) or isinstance(selected_cost, bool):
        selected_cost = 0.0
    count = trace.get("minimal_delta_route_option_count", len(options))
    if not isinstance(count, int) or isinstance(count, bool):
        count = len(options)
    return {
        "present": bool(
            trace.get("has_minimal_delta_and_or_cost_graph", False) or graph
        ),
        "route_option_count": max(0, count),
        "selected_route_option_id": selected_id,
        "selected_route_cost": max(0.0, float(selected_cost)),
    }


def _realization_coverage_witness_trace(row: dict[str, Any]) -> dict[str, object]:
    trace = row.get("standalone_input_trace", {})
    trace = trace if isinstance(trace, dict) else {}
    witness = trace.get("realization_coverage_witness", {})
    witness = witness if isinstance(witness, dict) else {}
    missing_selected = _str_tuple(
        trace.get(
            "realization_selected_primitives_missing_formal_realization",
            witness.get("selected_primitives_missing_formal_realization_node", []),
        )
    )
    missing_delta = _str_tuple(
        trace.get(
            "realization_delta_primitives_missing_route_alignment",
            witness.get("delta_primitives_missing_route_alignment_edge", []),
        )
    )
    return {
        "present": bool(
            trace.get("has_realization_coverage_witness", False) or witness
        ),
        "complete": bool(
            trace.get(
                "realization_coverage_complete",
                witness.get("realization_coverage_complete", False),
            )
        ),
        "missing_selected_formal_primitives": missing_selected,
        "missing_delta_alignment_primitives": missing_delta,
    }


def _llm_route_planner_trace(row: dict[str, Any]) -> dict[str, object]:
    trace = row.get("standalone_input_trace", {})
    trace = trace if isinstance(trace, dict) else {}
    generator_metadata = trace.get("llm_route_planner_generator_metadata", {})
    generator_metadata = generator_metadata if isinstance(generator_metadata, dict) else {}
    generator_keys = _str_tuple(
        trace.get("llm_route_planner_generator_metadata_keys", [])
    )
    if not generator_keys:
        generator_keys = tuple(sorted(str(key) for key in generator_metadata))
    row_id = str(trace.get("llm_route_planner_row_id", "")).strip()
    provider = str(trace.get("llm_route_planner_provider", "")).strip()
    model = str(trace.get("llm_route_planner_model", "")).strip()
    model_tier = str(trace.get("llm_route_planner_model_tier", "")).strip()
    return {
        "trace_present": bool(row_id or provider or model or model_tier),
        "row_id": row_id,
        "provider": provider,
        "model": model,
        "model_tier": model_tier,
        "acceptance_status": str(
            trace.get("llm_route_planner_acceptance_status", "")
        ).strip(),
        "model_selection_rationale": str(
            trace.get("llm_route_planner_model_selection_rationale", "")
        ).strip(),
        "has_generator_metadata": bool(
            trace.get("llm_route_planner_has_generator_metadata", False)
            or generator_metadata
        ),
        "generator_metadata_keys": generator_keys,
    }


def _llm_model_tier_summary(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> dict[str, dict[str, object]]:
    tiers = sorted(
        {
            row.llm_route_planner_model_tier
            for row in rows
            if row.llm_route_planner_model_tier
        }
    )
    return {
        tier: {
            "n_rows": len(tier_rows),
            "n_ok": sum(1 for row in tier_rows if row.ok),
            "n_matched_ground_truth": sum(
                1 for row in tier_rows if row.matched_ground_truth
            ),
            "mean_route_recall": _mean(
                row.route_recall for row in tier_rows if row.matched_ground_truth
            ),
            "mean_delta_precision": _mean(
                row.delta_precision for row in tier_rows if row.matched_ground_truth
            ),
            "mean_alignment_coverage": _mean(
                row.alignment_coverage for row in tier_rows
            ),
            "n_rows_with_generator_metadata": sum(
                1 for row in tier_rows if row.llm_route_planner_has_generator_metadata
            ),
        }
        for tier in tiers
        for tier_rows in [
            [row for row in rows if row.llm_route_planner_model_tier == tier]
        ]
    }


def _unique_row_attr_strings(
    rows: list[FormalizationGapPlannerEvaluationRow],
    attr_name: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(item)
                for row in rows
                for item in getattr(row, attr_name)
                if str(item)
            }
        )
    )


def _realization_missing_primitives_by_route(
    rows: list[FormalizationGapPlannerEvaluationRow],
) -> tuple[dict[str, object], ...]:
    diagnostics: list[dict[str, object]] = []
    for row in rows:
        missing_selected = _str_tuple(
            row.realization_missing_selected_formal_primitives
        )
        missing_delta = _str_tuple(row.realization_missing_delta_alignment_primitives)
        if not missing_selected and not missing_delta:
            continue
        diagnostics.append(
            {
                "route_id": row.route_id,
                "display_name": row.display_name,
                "goal_plan_id": row.goal_plan_id,
                "missing_selected_formal_primitives": missing_selected,
                "missing_delta_alignment_primitives": missing_delta,
                "llm_route_planner_row_id": row.llm_route_planner_row_id,
                "llm_route_planner_model_tier": row.llm_route_planner_model_tier,
            }
        )
    return tuple(diagnostics)


def _alignment_contract(row: dict[str, Any]) -> tuple[bool, float, tuple[str, ...], tuple[str, ...]]:
    selected = set(_str_tuple(row.get("selected_primitives", [])))
    edges = row.get("route_alignment_edges", [])
    if not selected:
        return False, 0.0, tuple(), tuple()
    if not isinstance(edges, (list, tuple)):
        return False, 0.0, tuple(), tuple(sorted(selected))
    informal_node_ids = {
        str(node.get("node_id", ""))
        for node in row.get("informal_knowledge_dag_nodes", [])
        if isinstance(node, dict)
    }
    formal_node_ids = {
        str(node.get("node_id", ""))
        for node in _formal_realization_nodes(row)
        if isinstance(node, dict)
    }
    aligned: set[str] = set()
    malformed = False
    for edge in edges:
        if not isinstance(edge, dict):
            malformed = True
            continue
        if str(edge.get("kind", "")) != "aligned_to_formal_realization_candidate":
            malformed = True
            continue
        primitive = str(edge.get("primitive", ""))
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if not primitive or source not in informal_node_ids or target not in formal_node_ids:
            malformed = True
            continue
        aligned.add(primitive)
    unaligned = tuple(sorted(item for item in selected - aligned if item))
    aligned_tuple = tuple(sorted(item for item in selected & aligned if item))
    coverage = _ratio(len(aligned_tuple), len(selected), empty_value=0.0)
    return not malformed and not unaligned, coverage, aligned_tuple, unaligned


def _formal_realization_nodes(row: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    nodes = row.get("formal_realization_dag_nodes", [])
    if not isinstance(nodes, (list, tuple)) or not nodes:
        nodes = row.get("lean_realization_dag_nodes", [])
    if not isinstance(nodes, (list, tuple)):
        return tuple()
    return tuple(node for node in nodes if isinstance(node, dict))


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


def _schema_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{field_name} must be number")
    elif expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
        elif field_schema.get("minLength") and len(value) < int(field_schema["minLength"]):
            errors.append(f"{field_name} must be non-empty")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
        else:
            item_schema = field_schema.get("items", {})
            if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                bad = [idx for idx, item in enumerate(value) if not isinstance(item, str)]
                if bad:
                    errors.append(
                        f"{field_name} items must be string at indexes "
                        + ",".join(str(idx) for idx in bad)
                    )
            if isinstance(item_schema, dict) and item_schema.get("type") == "object":
                bad = [idx for idx, item in enumerate(value) if not isinstance(item, dict)]
                if bad:
                    errors.append(
                        f"{field_name} items must be object at indexes "
                        + ",".join(str(idx) for idx in bad)
                    )
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    pattern = field_schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str) and pattern not in value:
        errors.append(f"{field_name} must contain {pattern!r}")
    return tuple(errors)


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
        f"- Evaluation row schema valid: {payload.get('n_evaluation_row_schema_valid')}/{payload.get('n_evaluation_rows')}",
        f"- Matched ground truth: {payload.get('n_matched_ground_truth')}",
        f"- Ground-truth rows matched by plan: {payload.get('n_ground_truth_rows_matched_by_plan')}",
        f"- Unlabeled plan rows: {payload.get('n_unlabeled_plan_rows')}",
        f"- Mean route recall: {payload.get('mean_route_recall')}",
        f"- Mean route precision: {payload.get('mean_route_precision')}",
        f"- Mean delta precision: {payload.get('mean_delta_precision')}",
        f"- Mean delta recall: {payload.get('mean_delta_recall')}",
        f"- Mean residual precision: {payload.get('mean_residual_precision')}",
        f"- Mean residual recall: {payload.get('mean_residual_recall')}",
        f"- Mean coverage classification accuracy: {payload.get('mean_coverage_classification_accuracy')}",
        f"- Two-DAG ready: {payload.get('n_two_dag_contract_ok')}",
        f"- Alignment ready: {payload.get('n_alignment_contract_ok')}",
        f"- Mean alignment coverage: {payload.get('mean_alignment_coverage')}",
        f"- Feedback-loop ready: {payload.get('n_feedback_loop_ready')}",
        f"- Rows with minimal-delta cost graph: {payload.get('n_rows_with_minimal_delta_cost_graph')}",
        f"- Rows with realization coverage witness: {payload.get('n_rows_with_realization_coverage_witness')}",
        f"- Rows with complete realization coverage: {payload.get('n_rows_with_complete_realization_coverage')}",
        f"- Missing selected formal primitives: {payload.get('realization_missing_selected_formal_primitives')}",
        f"- Missing delta alignment primitives: {payload.get('realization_missing_delta_alignment_primitives')}",
        f"- Rows with LLM route-planner trace: {payload.get('n_rows_with_llm_route_planner_trace')}",
        f"- Evaluation by LLM model tier: {payload.get('evaluation_by_llm_model_tier')}",
        f"- Mean selected route-option cost: {payload.get('mean_minimal_delta_selected_route_cost')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
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
            f"delta_recall={row.get('delta_recall')} "
            f"llm_tier={row.get('llm_route_planner_model_tier')} ok={row.get('ok')}"
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
        if row.get("unaligned_primitives"):
            lines.append(
                "  unaligned primitives: "
                + ", ".join(str(item) for item in row.get("unaligned_primitives", [])[:8])
            )
    return "\n".join(lines) + "\n"
