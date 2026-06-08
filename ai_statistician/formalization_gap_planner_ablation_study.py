from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY as PLANNER_PROOF_EVIDENCE_BOUNDARY,
)


FORMALIZATION_GAP_PLANNER_ABLATION_STUDY_SCHEMA_VERSION = 1
FORMALIZATION_GAP_PLANNER_ABLATION_STUDY_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-ablation-study-row:1"
)
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_ABLATION_STUDY_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner ablation rows compare route-planning metrics "
    "under counterfactual removal of literature, formal-library grounding, "
    "proof-state, or route-planner signals. They are evaluation diagnostics, "
    "not theorem proof evidence."
)


ABLATION_VARIANTS = (
    "full_planner_observed",
    "no_literature_evidence",
    "no_formal_grounding",
    "no_proof_state_feedback",
    "no_route_planner",
)


@dataclass(frozen=True)
class FormalizationGapPlannerAblationStudyRow:
    schema_version: int
    ablation_id: str
    ablation_variant: str
    ablated_signals: tuple[str, ...]
    n_routes: int
    n_matched_routes: int
    n_impacted_routes: int
    n_impacted_primitives: int
    impacted_primitives: tuple[str, ...]
    mean_route_recall: float
    mean_route_precision: float
    mean_delta_precision: float
    mean_delta_recall: float
    mean_residual_precision: float
    mean_residual_recall: float
    mean_existing_reuse_precision: float
    mean_existing_reuse_recall: float
    mean_coverage_accuracy: float
    feedback_loop_readiness: float
    next_action_replan_rate: float
    next_action_replay_rate: float
    route_adoption_ready_rate: float
    route_adoption_pending_refinement_rate: float
    mean_route_adoption_blockers: float
    relative_route_recall_drop: float
    relative_delta_recall_drop: float
    relative_residual_recall_drop: float
    relative_route_adoption_ready_drop: float
    interpretation: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_ablation_study(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    formalization_gap_planner_evaluation_dir: Path,
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_interactive_session_dir: Path | None = None,
) -> dict[str, object]:
    """Export conservative route-planner ablations for publication diagnostics."""

    errors: list[str] = []
    plan_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    evaluation_path = (
        formalization_gap_planner_evaluation_dir
        / "formalization_gap_planner_evaluation_manifest.json"
    )
    session_path = (
        formalization_gap_planner_interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
        if formalization_gap_planner_interactive_session_dir is not None
        else None
    )
    plan_payload = _read_json(plan_path, errors)
    evaluation_payload = _read_json(evaluation_path, errors)
    session_payload = _read_json(session_path, errors) if session_path else {}
    if plan_payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("input manifest is not the library-aware formalization gap planner")
    if plan_payload.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("input manifest portable schema id mismatch")
    if evaluation_payload.get("component_name") != "formalization_gap_planner_evaluation":
        errors.append("evaluation manifest component mismatch")

    plan_rows = [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
    evaluation_rows = [
        row for row in evaluation_payload.get("rows", []) if isinstance(row, dict)
    ]
    session_rows = [
        row for row in session_payload.get("rows", []) if isinstance(row, dict)
    ]
    plan_index = _row_index(plan_rows)
    session_index = _row_index(session_rows)
    rows = [
        _ablation_row(
            variant,
            evaluation_rows,
            plan_index,
            session_index,
        )
        for variant in ABLATION_VARIANTS
    ]
    full = rows[0]
    rows = [
        _row_with_relative_drops(row, full)
        if row.ablation_variant != "full_planner_observed"
        else row
        for row in rows
    ]
    ablated_rows = [row for row in rows if row.ablation_variant != "full_planner_observed"]
    row_dicts = [asdict(row) for row in rows]
    ablation_row_schema = ablation_study_row_json_schema()
    row_schema_errors = [
        validate_ablation_study_row(row, ablation_row_schema)
        for row in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_ABLATION_STUDY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_ablation_study",
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_path),
        "formalization_gap_planner_evaluation_dir": str(
            formalization_gap_planner_evaluation_dir
        ),
        "formalization_gap_planner_evaluation_manifest": str(evaluation_path),
        "formalization_gap_planner_interactive_session_dir": str(
            formalization_gap_planner_interactive_session_dir or ""
        ),
        "formalization_gap_planner_interactive_session_manifest": str(
            session_path or ""
        ),
        "n_plan_rows": len(plan_rows),
        "n_evaluation_rows": len(evaluation_rows),
        "n_session_rows": len(session_rows),
        "n_ablation_variants": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": len(row_schema_errors) - n_row_schema_valid,
        "row_schema_errors": row_schema_errors,
        "ablation_study_row_schema": ablation_row_schema,
        "all_ok": (
            not errors
            and bool(evaluation_rows)
            and all(row.ok for row in rows)
            and len(row_schema_errors) == n_row_schema_valid
        ),
        "errors": errors,
        "rows": row_dicts,
        "best_variant_by_route_recall": max(
            rows,
            key=lambda row: (row.mean_route_recall, row.mean_delta_recall),
        ).ablation_variant
        if rows
        else "",
        "largest_route_recall_drop_variant": max(
            ablated_rows or rows,
            key=lambda row: row.relative_route_recall_drop,
        ).ablation_variant
        if rows
        else "",
        "largest_delta_recall_drop_variant": max(
            ablated_rows or rows,
            key=lambda row: row.relative_delta_recall_drop,
        ).ablation_variant
        if rows
        else "",
        "largest_residual_recall_drop_variant": max(
            ablated_rows or rows,
            key=lambda row: row.relative_residual_recall_drop,
        ).ablation_variant
        if rows
        else "",
        "largest_route_adoption_ready_drop_variant": max(
            ablated_rows or rows,
            key=lambda row: row.relative_route_adoption_ready_drop,
        ).ablation_variant
        if rows
        else "",
        "ablation_study_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "ablations are deterministic counterfactual diagnostics over recorded planner artifacts",
            "no_literature and no_lean ablations remove recorded primitives rather than rerunning live tools",
            "no_proof_state_feedback measures feedback-loop and replan-signal loss, not proof success",
            "kernel proof status still requires target-prover replay/calibration",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_gap_planner_ablation_study_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_ablation_study_row.schema.json").write_text(
            json.dumps(ablation_row_schema, indent=2),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_ablation_study.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_ablation_study.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def ablation_study_row_json_schema() -> dict[str, object]:
    required = [
        "schema_version",
        "ablation_id",
        "ablation_variant",
        "ablated_signals",
        "n_routes",
        "n_matched_routes",
        "n_impacted_routes",
        "n_impacted_primitives",
        "impacted_primitives",
        "mean_route_recall",
        "mean_route_precision",
        "mean_delta_precision",
        "mean_delta_recall",
        "mean_residual_precision",
        "mean_residual_recall",
        "mean_existing_reuse_precision",
        "mean_existing_reuse_recall",
        "mean_coverage_accuracy",
        "feedback_loop_readiness",
        "next_action_replan_rate",
        "next_action_replay_rate",
        "route_adoption_ready_rate",
        "route_adoption_pending_refinement_rate",
        "mean_route_adoption_blockers",
        "relative_route_recall_drop",
        "relative_delta_recall_drop",
        "relative_residual_recall_drop",
        "relative_route_adoption_ready_drop",
        "interpretation",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
        "errors",
    ]
    string_array = {"type": "array", "items": {"type": "string"}}
    rate = {"type": "number", "minimum": 0.0, "maximum": 1.0}
    nonnegative_number = {"type": "number", "minimum": 0.0}
    nonnegative_int = {"type": "integer", "minimum": 0}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": FORMALIZATION_GAP_PLANNER_ABLATION_STUDY_ROW_SCHEMA_ID,
        "title": "Formalization gap planner ablation study row",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_ABLATION_STUDY_SCHEMA_VERSION,
            },
            "ablation_id": {"type": "string", "minLength": 1},
            "ablation_variant": {"type": "string", "enum": list(ABLATION_VARIANTS)},
            "ablated_signals": string_array,
            "n_routes": nonnegative_int,
            "n_matched_routes": nonnegative_int,
            "n_impacted_routes": nonnegative_int,
            "n_impacted_primitives": nonnegative_int,
            "impacted_primitives": string_array,
            "mean_route_recall": rate,
            "mean_route_precision": rate,
            "mean_delta_precision": rate,
            "mean_delta_recall": rate,
            "mean_residual_precision": rate,
            "mean_residual_recall": rate,
            "mean_existing_reuse_precision": rate,
            "mean_existing_reuse_recall": rate,
            "mean_coverage_accuracy": rate,
            "feedback_loop_readiness": rate,
            "next_action_replan_rate": rate,
            "next_action_replay_rate": rate,
            "route_adoption_ready_rate": rate,
            "route_adoption_pending_refinement_rate": rate,
            "mean_route_adoption_blockers": nonnegative_number,
            "relative_route_recall_drop": nonnegative_number,
            "relative_delta_recall_drop": nonnegative_number,
            "relative_residual_recall_drop": nonnegative_number,
            "relative_route_adoption_ready_drop": nonnegative_number,
            "interpretation": {"type": "string", "minLength": 1},
            "proof_evidence_status": {"type": "string", "const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_ablation_study_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    row_schema = schema or ablation_study_row_json_schema()
    required = tuple(row_schema.get("required", ()))
    errors: list[str] = []
    for field_name in required:
        if field_name not in row:
            errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if field_name in row and isinstance(field_schema, dict):
                errors.extend(_schema_property_errors(field_name, row[field_name], field_schema))
    allowed = set(required)
    for field_name in row:
        if field_name not in allowed:
            errors.append(f"{field_name} unexpected")
    if (
        isinstance(row.get("n_impacted_primitives"), int)
        and isinstance(row.get("impacted_primitives"), (list, tuple))
        and row["n_impacted_primitives"] != len(row["impacted_primitives"])
    ):
        errors.append("n_impacted_primitives must match impacted_primitives length")
    return errors


def _ablation_row(
    variant: str,
    evaluation_rows: list[dict[str, Any]],
    plan_index: dict[tuple[str, str], dict[str, Any]],
    session_index: dict[tuple[str, str], dict[str, Any]],
) -> FormalizationGapPlannerAblationStudyRow:
    errors: list[str] = []
    metrics: list[dict[str, float]] = []
    impacted_routes = 0
    impacted_primitives: set[str] = set()
    matched_routes = 0
    for row in evaluation_rows:
        if not bool(row.get("matched_ground_truth", False)):
            continue
        matched_routes += 1
        key = (str(row.get("goal_plan_id", "")), str(row.get("route_id", "")))
        plan_row = plan_index.get(key, {})
        session_row = session_index.get(key, {})
        route_pred = _str_tuple(row.get("predicted_route_primitives", []))
        delta_pred = _str_tuple(row.get("predicted_delta_primitives", []))
        existing_pred = _str_tuple(row.get("predicted_existing_reuse_primitives", []))
        residual_pred = _str_tuple(row.get("predicted_residual_primitives", []))
        route_truth = _str_tuple(row.get("ground_truth_route_primitives", []))
        delta_truth = _str_tuple(row.get("ground_truth_delta_primitives", []))
        existing_truth = _str_tuple(row.get("ground_truth_existing_reuse_primitives", []))
        residual_truth = _str_tuple(row.get("ground_truth_residual_primitives", []))
        coverage = _float(row.get("coverage_classification_accuracy", 0.0))
        removed: set[str] = set()
        if variant == "no_literature_evidence":
            removed = set(_literature_primitives(plan_row))
            route_pred = _without(route_pred, removed)
            delta_pred = _without(delta_pred, removed)
        elif variant == "no_formal_grounding":
            removed = set(_formal_grounding_primitives(plan_row)) | set(existing_pred)
            route_pred = _without(route_pred, removed)
            existing_pred = _without(existing_pred, removed)
            coverage = 0.0 if removed else coverage
        elif variant == "no_proof_state_feedback":
            removed = set(_proof_feedback_primitives(session_row)) | set(residual_pred)
            residual_pred = ()
        elif variant == "no_route_planner":
            removed = set(route_pred) | set(delta_pred) | set(existing_pred) | set(residual_pred)
            route_pred = ()
            delta_pred = ()
            existing_pred = ()
            residual_pred = ()
            coverage = 0.0
        adoption_ready, adoption_pending, adoption_blockers = (
            _route_adoption_metrics(variant, row, removed)
        )
        if removed:
            impacted_routes += 1
            impacted_primitives.update(removed)
        metrics.append(
            {
                "route_recall": _set_recall(route_pred, route_truth),
                "route_precision": _set_precision(route_pred, route_truth),
                "delta_precision": _set_precision(delta_pred, delta_truth),
                "delta_recall": _set_recall(delta_pred, delta_truth),
                "residual_precision": _set_precision(residual_pred, residual_truth),
                "residual_recall": _set_recall(residual_pred, residual_truth),
                "existing_reuse_precision": _set_precision(existing_pred, existing_truth),
                "existing_reuse_recall": _set_recall(existing_pred, existing_truth),
                "coverage_accuracy": coverage,
                "feedback_ready": _feedback_ready(variant, row, session_row),
                "replan": _next_action_rate(variant, session_row, "route_replan"),
                "replay": _next_action_rate(variant, session_row, "target_prover_replay"),
                "route_adoption_ready": adoption_ready,
                "route_adoption_pending": adoption_pending,
                "route_adoption_blockers": adoption_blockers,
            }
        )
    if not evaluation_rows:
        errors.append("evaluation rows missing")
    if not matched_routes:
        errors.append("matched route rows missing")
    return FormalizationGapPlannerAblationStudyRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ABLATION_STUDY_SCHEMA_VERSION,
        ablation_id="formalization_gap_planner_ablation_study:"
        + stable_hash([variant, matched_routes, sorted(impacted_primitives)])[:16],
        ablation_variant=variant,
        ablated_signals=_ablated_signals(variant),
        n_routes=len(evaluation_rows),
        n_matched_routes=matched_routes,
        n_impacted_routes=impacted_routes,
        n_impacted_primitives=len(impacted_primitives),
        impacted_primitives=tuple(sorted(impacted_primitives)),
        mean_route_recall=_mean(metric["route_recall"] for metric in metrics),
        mean_route_precision=_mean(metric["route_precision"] for metric in metrics),
        mean_delta_precision=_mean(metric["delta_precision"] for metric in metrics),
        mean_delta_recall=_mean(metric["delta_recall"] for metric in metrics),
        mean_residual_precision=_mean(
            metric["residual_precision"] for metric in metrics
        ),
        mean_residual_recall=_mean(
            metric["residual_recall"] for metric in metrics
        ),
        mean_existing_reuse_precision=_mean(
            metric["existing_reuse_precision"] for metric in metrics
        ),
        mean_existing_reuse_recall=_mean(
            metric["existing_reuse_recall"] for metric in metrics
        ),
        mean_coverage_accuracy=_mean(metric["coverage_accuracy"] for metric in metrics),
        feedback_loop_readiness=_mean(metric["feedback_ready"] for metric in metrics),
        next_action_replan_rate=_mean(metric["replan"] for metric in metrics),
        next_action_replay_rate=_mean(metric["replay"] for metric in metrics),
        route_adoption_ready_rate=_mean(
            metric["route_adoption_ready"] for metric in metrics
        ),
        route_adoption_pending_refinement_rate=_mean(
            metric["route_adoption_pending"] for metric in metrics
        ),
        mean_route_adoption_blockers=_mean(
            metric["route_adoption_blockers"] for metric in metrics
        ),
        relative_route_recall_drop=0.0,
        relative_delta_recall_drop=0.0,
        relative_residual_recall_drop=0.0,
        relative_route_adoption_ready_drop=0.0,
        interpretation=_interpretation(variant),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _row_with_relative_drops(
    row: FormalizationGapPlannerAblationStudyRow,
    full: FormalizationGapPlannerAblationStudyRow,
) -> FormalizationGapPlannerAblationStudyRow:
    data = asdict(row)
    data["relative_route_recall_drop"] = max(
        0.0,
        full.mean_route_recall - row.mean_route_recall,
    )
    data["relative_delta_recall_drop"] = max(
        0.0,
        full.mean_delta_recall - row.mean_delta_recall,
    )
    data["relative_residual_recall_drop"] = max(
        0.0,
        full.mean_residual_recall - row.mean_residual_recall,
    )
    data["relative_route_adoption_ready_drop"] = max(
        0.0,
        full.route_adoption_ready_rate - row.route_adoption_ready_rate,
    )
    return FormalizationGapPlannerAblationStudyRow(**data)


def _literature_primitives(plan_row: dict[str, Any]) -> tuple[str, ...]:
    primitives: list[str] = []
    for node in _all_node_dicts(plan_row):
        status = str(node.get("coverage_status", "") or node.get("action_class", ""))
        if status in {"source_port_needed", "source_discovery_needed"}:
            primitives.append(str(node.get("primitive", "")))
        elif node.get("source_refs"):
            primitives.append(str(node.get("primitive", "")))
    return _str_tuple(primitives)


def _formal_grounding_primitives(plan_row: dict[str, Any]) -> tuple[str, ...]:
    primitives: list[str] = []
    for node in _all_node_dicts(plan_row):
        status = str(node.get("coverage_status", "") or node.get("action_class", ""))
        if status == "exact_exists" or node.get("candidate_declarations"):
            primitives.append(str(node.get("primitive", "")))
    return _str_tuple(primitives)


def _proof_feedback_primitives(session_row: dict[str, Any]) -> tuple[str, ...]:
    primitives: list[str] = []
    for field in ("residual_goals", "route_revision_reasons"):
        for value in session_row.get(field, []):
            text = str(value)
            if ":" in text:
                primitives.append(text.split(":", 1)[0])
            else:
                primitives.append(text)
    return _str_tuple(primitives)


def _all_node_dicts(plan_row: dict[str, Any]) -> list[dict[str, Any]]:
    fields = (
        "existing_reuse_nodes",
        "wrapper_nodes",
        "bridge_nodes",
        "source_discovery_nodes",
        "first_principles_nodes",
        "minimal_additional_formalization_nodes",
        "formal_realization_dag_nodes",
        "lean_realization_dag_nodes",
    )
    nodes: list[dict[str, Any]] = []
    for field in fields:
        nodes.extend(
            node for node in plan_row.get(field, []) if isinstance(node, dict)
        )
    return nodes


def _feedback_ready(
    variant: str,
    evaluation_row: dict[str, Any],
    session_row: dict[str, Any],
) -> float:
    if variant in {"no_proof_state_feedback", "no_route_planner"}:
        return 0.0
    if bool(evaluation_row.get("feedback_loop_ready", False)):
        return 1.0
    if session_row:
        return 1.0
    return 0.0


def _route_adoption_metrics(
    variant: str,
    evaluation_row: dict[str, Any],
    removed: set[str],
) -> tuple[float, float, float]:
    blockers = _str_tuple(
        evaluation_row.get("llm_route_planner_route_adoption_blockers", [])
    )
    if variant != "full_planner_observed" and removed:
        return (0.0, 1.0, float(max(1, len(blockers))))
    status = str(
        evaluation_row.get("llm_route_planner_route_adoption_status", "")
    ).strip()
    if status == "READY_FOR_STANDALONE_REPLAY":
        return (1.0, 0.0, 0.0)
    if status == "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION":
        return (0.0, 1.0, float(max(1, len(blockers))))
    if status in {
        "AWAITING_LLM_ROUTE_PLANNER_RESPONSE",
        "REJECTED_LLM_ROUTE_PLAN",
    }:
        return (0.0, 1.0, float(max(1, len(blockers))))
    return (0.0, 0.0, float(len(blockers)))


def _next_action_rate(
    variant: str,
    session_row: dict[str, Any],
    action: str,
) -> float:
    if variant in {"no_proof_state_feedback", "no_route_planner"}:
        return 0.0
    return 1.0 if session_row.get("next_interaction_kind") == action else 0.0


def _ablated_signals(variant: str) -> tuple[str, ...]:
    return {
        "full_planner_observed": (),
        "no_literature_evidence": (
            "source_refs",
            "source_port_needed",
            "source_discovery_needed",
            "literature_discovery",
        ),
        "no_formal_grounding": (
            "exact_exists",
            "candidate_declarations",
            "formal_library_grounding",
            "library_declaration_search",
            "lean_library_grounding",
            "local_lean_rag",
        ),
        "no_proof_state_feedback": (
            "proof_state_feedback",
            "residual_goals",
            "route_replan_trigger",
        ),
        "no_route_planner": (
            "informal_route_dag",
            "formal_realization_dag",
            "minimal_delta_cut",
            "interactive_hooks",
        ),
    }.get(variant, ())


def _interpretation(variant: str) -> str:
    return {
        "full_planner_observed": "Observed planner metrics with all recorded route-planning signals present.",
        "no_literature_evidence": "Counterfactual metric after removing source-backed route nodes and literature-only primitives.",
        "no_formal_grounding": "Counterfactual metric after removing exact-reuse and formal-library-grounding primitives.",
        "no_proof_state_feedback": "Counterfactual feedback-loop metric after ignoring proof-state residual and replan signals.",
        "no_route_planner": "Null baseline with no predicted route, formalization delta, existing reuse, or feedback loop.",
    }.get(variant, "Unknown ablation variant.")


def _read_json(path: Path | None, errors: list[str]) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid json: {path}: {exc}")
    return {}


def _row_index(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("goal_plan_id", "")), str(row.get("route_id", "")))
        if all(key):
            index[key] = row
    return index


def _without(values: tuple[str, ...], removed: set[str]) -> tuple[str, ...]:
    return tuple(value for value in values if value not in removed)


def _str_tuple(values: Iterable[object] | object) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        iterable: Iterable[object] = [values]
    elif isinstance(values, dict):
        iterable = values.values()
    else:
        try:
            iterable = iter(values)  # type: ignore[arg-type]
        except TypeError:
            iterable = [values]
    result: list[str] = []
    seen: set[str] = set()
    for value in iterable:
        item = str(value).strip()
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return tuple(result)


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _set_recall(predicted: tuple[str, ...], truth: tuple[str, ...]) -> float:
    if not truth:
        return 1.0
    return len(set(predicted) & set(truth)) / len(set(truth))


def _set_precision(predicted: tuple[str, ...], truth: tuple[str, ...]) -> float:
    if not predicted:
        return 1.0 if not truth else 0.0
    return len(set(predicted) & set(truth)) / len(set(predicted))


def _mean(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return 0.0
    return round(sum(vals) / len(vals), 6)


def _schema_property_errors(
    field_name: str,
    value: object,
    schema: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
            return errors
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{field_name} must be non-empty")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            errors.append(f"{field_name} must match {pattern}")
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            errors.append(f"{field_name} must be one of {enum}")
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
            return errors
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{field_name} must be >= {minimum}")
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{field_name} must be number")
            return errors
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{field_name} must be >= {minimum}")
        maximum = schema.get("maximum")
        if isinstance(maximum, (int, float)) and value > maximum:
            errors.append(f"{field_name} must be <= {maximum}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
            return errors
        item_schema = schema.get("items", {})
        if isinstance(item_schema, dict) and item_schema.get("type") == "string":
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"{field_name}[{index}] must be string")
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
    return errors


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Ablation Study",
        "",
        f"- Component: {payload.get('component_name')}",
        f"- Variants: {payload.get('n_ok')}/{payload.get('n_ablation_variants')}",
        f"- Row schema valid: {payload.get('n_row_schema_valid')}/{payload.get('n_ablation_variants')}",
        f"- Best route recall: `{payload.get('best_variant_by_route_recall')}`",
        f"- Largest route-recall drop: `{payload.get('largest_route_recall_drop_variant')}`",
        f"- Largest residual-recall drop: `{payload.get('largest_residual_recall_drop_variant')}`",
        f"- Largest route-adoption-ready drop: `{payload.get('largest_route_adoption_ready_drop_variant')}`",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Proof Boundary",
        "",
        str(payload.get("proof_evidence_boundary", "")),
        "",
        "## Variants",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### {row.get('ablation_variant')}",
                "",
                f"- Route recall: {row.get('mean_route_recall')}",
                f"- Delta recall: {row.get('mean_delta_recall')}",
                f"- Residual recall: {row.get('mean_residual_recall')}",
                f"- Existing reuse recall: {row.get('mean_existing_reuse_recall')}",
                f"- Route-adoption ready/pending/blockers: {row.get('route_adoption_ready_rate')}/{row.get('route_adoption_pending_refinement_rate')}/{row.get('mean_route_adoption_blockers')}",
                f"- Impacted routes: {row.get('n_impacted_routes')}",
                f"- Interpretation: {row.get('interpretation')}",
                "",
            ]
        )
    return "\n".join(lines)
