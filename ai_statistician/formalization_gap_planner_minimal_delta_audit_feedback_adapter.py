from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_refinement_evidence import (
    PROOF_EVIDENCE_BOUNDARY,
    refinement_tool_response_json_schema,
    validate_refinement_tool_response_row,
)


FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_FEEDBACK_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_FEEDBACK_ADAPTER_NOT_PROOF_EVIDENCE"
)
ADAPTER_TOOL_NAME = "minimal_delta_audit_feedback_adapter"


def export_formalization_gap_planner_minimal_delta_audit_feedback_responses(
    formalization_gap_planner_refinement_queue_dir: Path,
    formalization_gap_planner_minimal_delta_audit_dir: Path,
    out_dir: Path | None = None,
    *,
    base_response_jsonl: Path | None = None,
    max_items: int = 0,
) -> dict[str, object]:
    """Convert failed minimal-delta audit decisions into route-revision responses."""

    errors: list[str] = []
    queue_manifest_path = (
        formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_queue_manifest.json"
    )
    audit_manifest_path = (
        formalization_gap_planner_minimal_delta_audit_dir
        / "formalization_gap_planner_minimal_delta_audit_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    audit_payload = _read_json(audit_manifest_path, errors)
    queue_rows = [
        row for row in queue_payload.get("rows", []) if isinstance(row, dict)
    ]
    if max_items > 0:
        queue_rows = queue_rows[:max_items]
    route_revision_rows = [
        row for row in queue_rows if str(row.get("hook_kind", "")) == "route_revision"
    ]
    decision_rows = [
        row
        for row in audit_payload.get("minimal_delta_decision_rows", [])
        if isinstance(row, dict)
    ]
    failed_decision_rows = [
        row for row in decision_rows if _decision_requires_route_revision(row)
    ]
    base_responses = _read_jsonl(base_response_jsonl, errors) if base_response_jsonl else []
    generated_responses = [
        _feedback_response(queue_row, decision_row)
        for queue_row in route_revision_rows
        for decision_row in failed_decision_rows
        if _decision_matches_queue_row(decision_row, queue_row)
    ]
    base_by_item = {
        str(row.get("refinement_item_id", "")): row
        for row in base_responses
        if str(row.get("refinement_item_id", ""))
    }
    merged_by_item = dict(base_by_item)
    for response in generated_responses:
        merged_by_item[str(response.get("refinement_item_id", ""))] = response
    merged_responses = sorted(
        merged_by_item.values(),
        key=lambda row: (
            str(row.get("display_name", "")),
            str(row.get("evidence_kind", "")),
            str(row.get("refinement_item_id", "")),
        ),
    )
    response_schema = refinement_tool_response_json_schema()
    generated_schema_errors = [
        validate_refinement_tool_response_row(response, response_schema)
        for response in generated_responses
    ]
    merged_schema_errors = [
        validate_refinement_tool_response_row(response, response_schema)
        for response in merged_responses
    ]
    n_generated_schema_valid = sum(
        1 for row_errors in generated_schema_errors if not row_errors
    )
    n_merged_schema_valid = sum(
        1 for row_errors in merged_schema_errors if not row_errors
    )
    matched_item_ids = {
        str(response.get("refinement_item_id", ""))
        for response in generated_responses
        if str(response.get("refinement_item_id", ""))
    }
    by_dominance_status = Counter(
        str(row.get("dominance_status", "")) for row in failed_decision_rows
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_FEEDBACK_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": (
            "formalization_gap_planner_minimal_delta_audit_feedback_adapter"
        ),
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir
        ),
        "formalization_gap_planner_refinement_queue_manifest": str(
            queue_manifest_path
        ),
        "formalization_gap_planner_minimal_delta_audit_dir": str(
            formalization_gap_planner_minimal_delta_audit_dir
        ),
        "formalization_gap_planner_minimal_delta_audit_manifest": str(
            audit_manifest_path
        ),
        "base_response_jsonl": str(base_response_jsonl or ""),
        "max_items": max_items,
        "n_queue_rows": len(queue_rows),
        "n_route_revision_rows": len(route_revision_rows),
        "n_minimal_delta_decision_rows": len(decision_rows),
        "n_failed_minimal_delta_decision_rows": len(failed_decision_rows),
        "n_base_responses": len(base_responses),
        "n_generated_feedback_responses": len(generated_responses),
        "n_merged_responses": len(merged_responses),
        "n_matched_route_revision_rows": len(matched_item_ids),
        "n_unmatched_route_revision_rows": max(
            0,
            len(route_revision_rows) - len(matched_item_ids),
        ),
        "n_route_revision_recommended": sum(
            1
            for response in generated_responses
            if bool(response.get("route_revision_recommended", False))
        ),
        "n_response_schema_valid": n_generated_schema_valid,
        "n_response_schema_invalid": len(generated_schema_errors)
        - n_generated_schema_valid,
        "n_merged_response_schema_valid": n_merged_schema_valid,
        "n_merged_response_schema_invalid": len(merged_schema_errors)
        - n_merged_schema_valid,
        "response_schema_errors": generated_schema_errors,
        "merged_response_schema_errors": merged_schema_errors,
        "by_dominance_status": dict(sorted(by_dominance_status.items())),
        "all_ok": (
            not errors
            and n_generated_schema_valid == len(generated_responses)
            and n_merged_schema_valid == len(merged_responses)
        ),
        "errors": errors,
        "responses": generated_responses,
        "merged_response_ids": [
            str(row.get("refinement_item_id", "")) for row in merged_responses
        ],
        "refinement_tool_response_schema": response_schema,
        "responses_fingerprint": stable_hash(generated_responses),
        "merged_responses_fingerprint": stable_hash(merged_responses),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "minimal-delta audit feedback is structural route-repair evidence, not theorem proof evidence",
            "a cheaper route option is a planning candidate until source grounding and target-prover replay accept it",
            "this adapter only emits responses for queued route_revision hooks",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = (
            out_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter_manifest.json"
        )
        responses_path = (
            out_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        )
        generated_responses_path = (
            out_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_responses.jsonl"
        )
        response_schema_path = (
            out_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
        )
        payload["manifest_path"] = str(manifest_path)
        payload["responses_jsonl"] = str(responses_path)
        payload["generated_responses_jsonl"] = str(generated_responses_path)
        payload["response_schema_path"] = str(response_schema_path)
        manifest_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        response_schema_path.write_text(
            json.dumps(response_schema, indent=2),
            encoding="utf-8",
        )
        responses_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in merged_responses)
            + ("\n" if merged_responses else ""),
            encoding="utf-8",
        )
        generated_responses_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in generated_responses)
            + ("\n" if generated_responses else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _feedback_response(
    queue_row: dict[str, Any],
    decision_row: dict[str, Any],
) -> dict[str, object]:
    proposed_primitives = _proposed_primitives(decision_row)
    if not proposed_primitives:
        proposed_primitives = _str_tuple(decision_row.get("selected_primitives", []))
    target_primitives = _str_tuple(queue_row.get("target_primitives", []))
    revised_delta = tuple(
        primitive
        for primitive in proposed_primitives
        if primitive not in set(_str_tuple(decision_row.get("existing_reuse_primitives", [])))
    )
    if not revised_delta:
        revised_delta = target_primitives or proposed_primitives
    route_option_id = str(decision_row.get("minimal_delta_selected_route_option_id", ""))
    replacement_option = _replacement_route_option(decision_row)
    replacement_option_id = str(replacement_option.get("route_option_id", ""))
    summary = (
        "Minimal-delta audit requires route replanning"
        + (f": replace selected option {route_option_id}" if route_option_id else "")
        + (f" with lower-cost option {replacement_option_id}" if replacement_option_id else "")
        + "."
    )
    reasons = _route_revision_reasons(decision_row)
    return {
        "refinement_item_id": str(queue_row.get("refinement_item_id", "")),
        "route_id": str(queue_row.get("route_id", "")),
        "display_name": str(queue_row.get("display_name", "")),
        "evidence_kind": "route_revision_proposal",
        "tool_name": ADAPTER_TOOL_NAME,
        "resource_request_ids": _str_tuple(queue_row.get("resource_request_ids", [])),
        "resource_ids": _str_tuple(queue_row.get("resource_ids", [])),
        "resource_request_bindings": _dict_tuple(
            queue_row.get("resource_request_bindings", [])
        ),
        "llm_route_planner_hook_trace": _dict_value(
            queue_row,
            "llm_route_planner_hook_trace",
        ),
        "target_prover_family": str(
            queue_row.get(
                "target_prover_family",
                decision_row.get("target_prover_family", ""),
            )
        ),
        "minimal_delta_decision_id": str(
            decision_row.get("minimal_delta_decision_id", "")
        ),
        "route_revision_recommended": True,
        "route_revision_reasons": reasons,
        "route_revision_summary": summary,
        "revised_selected_primitives": proposed_primitives,
        "revised_delta_primitives": revised_delta,
        "revised_informal_knowledge_dag_nodes": _informal_nodes(
            proposed_primitives,
            decision_row,
        ),
        "revised_formal_realization_dag_nodes": _formal_nodes(
            proposed_primitives,
            decision_row,
        ),
        "revised_lean_realization_dag_nodes": _formal_nodes(
            proposed_primitives,
            decision_row,
        ),
        "residual_goals": _residual_goals(decision_row),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _decision_requires_route_revision(row: dict[str, Any]) -> bool:
    if not bool(row.get("ok", True)):
        return True
    if str(row.get("dominance_status", "")).startswith("DOMINATED_"):
        return True
    if bool(row.get("has_minimal_delta_and_or_cost_graph", False)) and not bool(
        row.get("cost_graph_selection_ok", True)
    ):
        return True
    return False


def _decision_matches_queue_row(
    decision_row: dict[str, Any],
    queue_row: dict[str, Any],
) -> bool:
    queue_route = str(queue_row.get("route_id", "")).strip()
    decision_route = str(decision_row.get("route_id", "")).strip()
    queue_goal = str(queue_row.get("goal_plan_id", "")).strip()
    decision_goal = str(decision_row.get("goal_plan_id", "")).strip()
    queue_display = str(queue_row.get("display_name", "")).strip()
    decision_display = str(decision_row.get("display_name", "")).strip()
    if queue_route and decision_route and queue_route != decision_route:
        return False
    if queue_route and decision_route and queue_route == decision_route:
        return True
    if queue_goal and decision_goal and queue_goal != decision_goal:
        return False
    return bool(
        (queue_route and decision_route and queue_route == decision_route)
        or (queue_goal and decision_goal and queue_goal == decision_goal)
        or (queue_display and decision_display and queue_display == decision_display)
    )


def _proposed_primitives(decision_row: dict[str, Any]) -> tuple[str, ...]:
    replacement = _replacement_route_option(decision_row)
    primitives = _str_tuple(replacement.get("selected_primitives", []))
    if primitives:
        return primitives
    return _str_tuple(decision_row.get("selected_primitives", []))


def _replacement_route_option(decision_row: dict[str, Any]) -> dict[str, object]:
    rejected = _dict_tuple(decision_row.get("minimal_delta_rejected_route_options", []))
    selected_cost = _number(decision_row.get("minimal_delta_selected_route_cost"))
    cheaper = [
        row
        for row in rejected
        if _number(row.get("route_cost")) is not None
        and selected_cost is not None
        and float(row.get("route_cost", 0)) + 1e-9 < selected_cost
        and _str_tuple(row.get("selected_primitives", []))
    ]
    if cheaper:
        return sorted(
            cheaper,
            key=lambda row: (
                float(row.get("route_cost", 0)),
                str(row.get("route_option_id", "")),
            ),
        )[0]
    return {}


def _route_revision_reasons(decision_row: dict[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    if not bool(decision_row.get("cost_formula_ok", True)):
        reasons.append("minimal-delta audit rejected route cost formula accounting")
    if not bool(decision_row.get("node_cost_accounting_ok", True)):
        reasons.append("minimal-delta audit rejected primitive node cost accounting")
    if not bool(decision_row.get("work_packet_cut_ok", True)):
        reasons.append("minimal-delta audit rejected work-packet selected cut")
    if not bool(decision_row.get("delta_nodes_connected", True)):
        reasons.append("minimal-delta audit found disconnected delta nodes")
    if bool(decision_row.get("has_minimal_delta_and_or_cost_graph", False)) and not bool(
        decision_row.get("cost_graph_selection_ok", True)
    ):
        reasons.append("minimal-delta audit found a lower-cost route option")
    dominated_by = _str_tuple(decision_row.get("dominated_by_goal_plan_ids", []))
    if dominated_by:
        reasons.append(
            "minimal-delta audit found same-target dominated route: "
            + ", ".join(dominated_by)
        )
    for error in _str_tuple(decision_row.get("errors", [])):
        reasons.append(f"minimal-delta decision error: {error}")
    if not reasons:
        reasons.append("minimal-delta audit requires route revision")
    return tuple(dict.fromkeys(reasons))


def _residual_goals(decision_row: dict[str, Any]) -> tuple[str, ...]:
    residuals: list[str] = []
    selected = str(decision_row.get("minimal_delta_selected_route_option_id", ""))
    replacement = _replacement_route_option(decision_row)
    replacement_id = str(replacement.get("route_option_id", ""))
    if replacement_id:
        residuals.append(
            f"minimal-delta selected option {selected or '<none>'} is cost-dominated by {replacement_id}"
        )
    for reason in _route_revision_reasons(decision_row):
        residuals.append(reason)
    return tuple(dict.fromkeys(residuals))


def _informal_nodes(
    primitives: tuple[str, ...],
    decision_row: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "node_id": "minimal_delta_audit_informal:"
            + stable_hash([decision_row.get("minimal_delta_decision_id", ""), primitive])[
                :16
            ],
            "kind": "minimal_delta_audit_route_choice",
            "semantic_role": "route_revision_candidate",
            "label": primitive,
            "primitive": primitive,
            "claim": (
                f"{primitive} is a structural route-replanning candidate selected "
                "from the current minimal-delta cost graph."
            ),
            "source_refs": [],
            "source_search_status": "FORMAL_GAP_BOUNDARY",
            "formal_gap_boundary": (
                "This node is justified by a structural minimal-delta audit, "
                "not by source-backed mathematical evidence."
            ),
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        }
        for primitive in primitives
    )


def _formal_nodes(
    primitives: tuple[str, ...],
    decision_row: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "node_id": "minimal_delta_audit_formal:"
            + stable_hash([decision_row.get("minimal_delta_decision_id", ""), primitive])[
                :16
            ],
            "kind": "minimal_delta_audit_formalization_candidate",
            "label": primitive,
            "primitive": primitive,
            "coverage_status": "minimal_delta_route_revision_candidate",
            "formalization_action": "replan_candidate",
            "alignment_status": "route_revision_candidate",
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        }
        for primitive in primitives
    )


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


def _read_jsonl(path: Path | None, errors: list[str]) -> list[dict[str, Any]]:
    if path is None:
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return []
    except Exception as exc:
        errors.append(f"failed to read {path}: {type(exc).__name__}: {exc}")
        return []
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse {path}:{line_no}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"{path}:{line_no} is not an object")
    return rows


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(item for item in values if isinstance(item, dict))


def _dict_value(row: dict[str, Any], field_name: str) -> dict[str, object]:
    value = row.get(field_name, {})
    return dict(value) if isinstance(value, dict) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Minimal-Delta Audit Feedback Adapter",
        "",
        f"- Queue rows: {payload.get('n_queue_rows')}",
        f"- Route-revision rows: {payload.get('n_route_revision_rows')}",
        f"- Minimal-delta decisions: {payload.get('n_minimal_delta_decision_rows')}",
        f"- Failed decisions: {payload.get('n_failed_minimal_delta_decision_rows')}",
        f"- Generated responses: {payload.get('n_generated_feedback_responses')}",
        f"- Merged responses: {payload.get('n_merged_responses')}",
        f"- Response schema valid: {payload.get('n_response_schema_valid')}/{payload.get('n_generated_feedback_responses')}",
        f"- Route revisions recommended: {payload.get('n_route_revision_recommended')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
    ]
    return "\n".join(lines) + "\n"
