from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LEGACY_FORMAL_REALIZATION_FIELD_ALIASES,
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    OPTIMIZATION_OBJECTIVES,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
    PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS,
    TARGET_PROVER_FAMILY,
    evaluation_protocol,
    interactive_route_synthesis_contract,
    normalize_target_prover_family,
    planner_contract,
    portable_gap_plan_row_json_schema,
    route_alignment_edge_json_schema,
    validate_portable_gap_plan_row,
    validate_route_alignment_edge,
    validate_portable_gap_plan_payload,
    write_portable_gap_plan_schema,
    write_portable_gap_plan_row_schema,
    write_route_alignment_edge_schema,
)
from .formalization_gap_planner_route_adoption_blockers import (
    ROUTE_ADOPTION_BLOCKER_VALUES as LLM_ROUTE_PLANNER_ROUTE_ADOPTION_BLOCKER_VALUES,
)
from .goal_conditioned_minimal_formalization_plan import (
    GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION,
    _graph_count,
    _markdown_report,
    _plan_row,
)


FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION = 1
FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-standalone-input:1"
)
FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-seed-route-selection:1"
)
FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_KIND = (
    "formalization_gap_planner_llm_route_planner_seed_route_selection"
)
FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
)
FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_ROUTE_OPTION_SELECTION_BRIEF_KIND = (
    "formalization_gap_planner_llm_route_planner_route_option_selection_brief"
)
LLM_ROUTE_PLANNER_READY_FOR_STANDALONE_REPLAY = "READY_FOR_STANDALONE_REPLAY"
LLM_ROUTE_PLANNER_ACCEPTED_SELECTION_STATUS = "accepted_llm_routes_ranked"
LLM_ROUTE_PLANNER_FALLBACK_SELECTION_STATUS = "fallback_routes_ranked"
FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT = (
    "formalization_gap_planner_standalone_input"
)
QUALITY_CONTROL_FIELDS = (
    "resource_contract_ids",
    "required_quality_signals",
    "quality_gates",
    "response_validation_signals",
    "stop_conditions",
)
FORMALIZATION_DELTA_OBJECTIVE = (
    "Given a target theorem T and a current formal library snapshot L, find a "
    "small additional formalization Delta of existing reuse, wrappers, bridge "
    "lemmas, source ports, or new primitives such that L + Delta is a plausible "
    "route to a kernel-checked proof of T."
)


def export_formalization_gap_planner_standalone_plan(
    input_json: Path,
    out_dir: Path | None = None,
    *,
    max_routes: int = 20,
) -> dict[str, object]:
    """Build a portable gap-plan manifest from standalone theorem-route JSON.

    This is the prover-agnostic entry point for users who do not have the full
    AI Statistician research audit pipeline. The input supplies target theorem
    routes, primitive coverage labels, and candidate declarations; the output is
    the same portable planner manifest consumed by evaluation, refinement,
    prover-adapter, and publication-bundle tools.
    """

    errors: list[str] = []
    input_payload = _read_json(input_json, errors)
    input_errors = validate_standalone_input_payload(input_payload)
    errors.extend(input_errors)

    library_snapshot_ref = str(input_payload.get("library_snapshot_ref", "")).strip()
    target_prover_family = _target_prover_family(input_payload)
    route_specs = _route_specs(
        input_payload,
        errors,
        target_prover_family=target_prover_family,
    )
    routes = [route for route, _queue_row in route_specs]
    queue_by_route = {
        str(route.get("route_id", "")): queue_row
        for route, queue_row in route_specs
        if str(route.get("route_id", ""))
    }
    all_primitives = _all_primitives(input_payload, routes)
    raw_rows = [
        _plan_row(
            route,
            queue_by_route.get(str(route.get("route_id", "")), {}),
            all_primitives,
            library_snapshot_ref=library_snapshot_ref,
            source_target_prover_family=target_prover_family,
        )
        for route in routes
    ]
    rows = sorted(
        raw_rows,
        key=lambda row: (
            row.goal_conditioned_cost,
            -row.route_efficiency_score,
            row.display_name,
            row.goal_plan_id,
        ),
    )[: max(0, max_routes)]
    by_route_class = Counter(row.route_class for row in rows)
    by_target_prover_family = Counter(
        normalize_target_prover_family(row.target_prover_family) or "missing"
        for row in rows
    )
    route_alignment_edge_schema = route_alignment_edge_json_schema()
    route_alignment_edge_schema_errors = [
        validate_route_alignment_edge(edge, route_alignment_edge_schema)
        for row in rows
        for edge in row.route_alignment_edges
    ]
    n_route_alignment_edge_schema_valid = sum(
        1 for edge_errors in route_alignment_edge_schema_errors if not edge_errors
    )
    n_route_alignment_edge_schema_invalid = (
        len(route_alignment_edge_schema_errors) - n_route_alignment_edge_schema_valid
    )
    row_dicts = [
        _portable_row_with_formal_aliases(
            asdict(row),
            target_prover_family=str(row.target_prover_family or target_prover_family),
        )
        for row in rows
    ]
    goal_plan_row_schema = portable_gap_plan_row_json_schema()
    goal_plan_row_schema_errors = [
        validate_portable_gap_plan_row(
            row_dict,
            goal_plan_row_schema,
            library_snapshot_ref=library_snapshot_ref,
        )
        for row_dict in row_dicts
    ]
    n_goal_plan_row_schema_valid = sum(
        1 for row_errors in goal_plan_row_schema_errors if not row_errors
    )
    n_goal_plan_row_schema_invalid = (
        len(goal_plan_row_schema_errors) - n_goal_plan_row_schema_valid
    )
    by_llm_model_tier = Counter(
        str(row.standalone_input_trace.get("llm_route_planner_model_tier", ""))
        or "missing"
        for row in rows
        if row.standalone_input_trace.get("llm_route_planner_row_id")
        or row.standalone_input_trace.get("llm_route_planner_model_tier")
    )
    by_llm_route_adoption_status = Counter(
        str(
            row.standalone_input_trace.get(
                "llm_route_planner_route_adoption_status",
                "",
            )
        )
        or "missing"
        for row in rows
        if row.standalone_input_trace.get("llm_route_planner_row_id")
        or row.standalone_input_trace.get(
            "llm_route_planner_route_adoption_status"
        )
    )
    by_llm_seed_selection_rank = Counter(
        str(row.standalone_input_trace.get("llm_route_planner_seed_selection_rank", ""))
        or "missing"
        for row in rows
        if row.standalone_input_trace.get("llm_route_planner_seed_selection_rank")
    )
    manifest_target_prover_family = _manifest_target_prover_family(
        rows,
        fallback_target_prover_family=target_prover_family,
    )
    payload: dict[str, object] = {
        "schema_version": GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION,
        "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "portable_schema_version": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
        "component_name": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        "target_prover_family": manifest_target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "formalization_delta_objective": FORMALIZATION_DELTA_OBJECTIVE,
        "optimization_objectives": list(OPTIMIZATION_OBJECTIVES),
        "planner_contract": planner_contract(library_snapshot_ref),
        "interactive_route_synthesis_contract": interactive_route_synthesis_contract(),
        "evaluation_protocol": evaluation_protocol(),
        "legacy_formal_realization_field_aliases": dict(
            LEGACY_FORMAL_REALIZATION_FIELD_ALIASES
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "standalone_input_schema_id": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
        "standalone_input_path": str(input_json),
        "standalone_input_component": str(input_payload.get("component_name", "")),
        "n_theorem_routes": len(routes),
        "n_goal_plans": len(rows),
        "n_target_prover_families": sum(
            1 for target in by_target_prover_family if target != "missing"
        ),
        "by_target_prover_family": dict(sorted(by_target_prover_family.items())),
        "n_ready": sum(1 for row in rows if row.ok),
        "n_low_cost_goal_plans": sum(1 for row in rows if row.goal_conditioned_cost <= 7),
        "n_reuse_or_composition": by_route_class.get("reuse_or_composition", 0),
        "n_bridge_or_wrapper": by_route_class.get("bridge_or_wrapper", 0),
        "n_requires_new_theory": by_route_class.get("requires_new_theory", 0),
        "n_existing_reuse_nodes": sum(len(row.existing_reuse_nodes) for row in rows),
        "n_wrapper_nodes": sum(len(row.wrapper_nodes) for row in rows),
        "n_bridge_nodes": sum(len(row.bridge_nodes) for row in rows),
        "n_source_discovery_nodes": sum(len(row.source_discovery_nodes) for row in rows),
        "n_first_principles_nodes": sum(len(row.first_principles_nodes) for row in rows),
        "n_minimal_additional_formalization_nodes": sum(
            len(row.minimal_additional_formalization_nodes) for row in rows
        ),
        "n_goal_plans_with_minimal_cut": sum(1 for row in rows if row.minimal_cut_summary),
        "n_route_cost_breakdown_terms": sum(len(row.route_cost_breakdown) for row in rows),
        "n_and_or_plan_nodes": sum(_graph_count(row.and_or_plan, "nodes") for row in rows),
        "n_and_or_plan_edges": sum(_graph_count(row.and_or_plan, "edges") for row in rows),
        "n_informal_knowledge_dag_nodes": sum(
            _graph_count(row.informal_knowledge_dag, "nodes") for row in rows
        ),
        "n_informal_knowledge_dag_edges": sum(
            _graph_count(row.informal_knowledge_dag, "edges") for row in rows
        ),
        "n_lean_realization_dag_nodes": sum(
            len(_dict_list(row.get("lean_realization_dag_nodes", [])))
            for row in row_dicts
        ),
        "n_lean_realization_dag_edges": sum(
            len(_dict_list(row.get("lean_realization_dag_edges", [])))
            for row in row_dicts
        ),
        "n_formal_realization_dag_nodes": sum(
            len(_dict_list(row.get("formal_realization_dag_nodes", [])))
            for row in row_dicts
        ),
        "n_formal_realization_dag_edges": sum(
            len(_dict_list(row.get("formal_realization_dag_edges", [])))
            for row in row_dicts
        ),
        "n_route_alignment_edges": sum(len(row.route_alignment_edges) for row in rows),
        "n_standalone_input_traces": sum(
            1 for row in rows if row.standalone_input_trace
        ),
        "n_standalone_input_traces_with_replan_metadata": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("has_replan_metadata")
        ),
        "n_standalone_input_traces_with_target_theorem_context_packet": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("has_target_theorem_context_packet")
        ),
        "n_standalone_input_traces_with_llm_target_theorem_context_packet": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "has_llm_route_planner_target_theorem_context_packet"
            )
        ),
        "n_standalone_input_traces_with_llm_target_context_summary": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "has_llm_route_planner_target_context_summary"
            )
        ),
        "n_standalone_input_traces_with_llm_route_planning_brief": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "has_llm_route_planner_route_planning_brief"
            )
        ),
        "n_standalone_input_traces_with_llm_route_option_selection_brief": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "has_llm_route_planner_route_option_selection_brief"
            )
        ),
        "n_standalone_input_traces_with_llm_route_option_selected_route_option": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_route_option_selected_route_option_id"
            )
        ),
        "n_standalone_input_traces_with_llm_primitive_evidence_matrix_witness": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "has_llm_route_planner_primitive_evidence_matrix_witness"
            )
        ),
        "n_standalone_input_traces_with_complete_llm_primitive_evidence_matrix_accounting": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_primitive_evidence_matrix_accounting_complete"
            )
        ),
        "n_standalone_input_trace_llm_primitive_evidence_matrix_repair_obligations": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_planner_primitive_evidence_matrix_repair_obligation_count",
                    0,
                )
                or 0
            )
            for row in rows
        ),
        "n_standalone_input_trace_llm_primitive_evidence_matrix_unaccounted_primitives": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_planner_primitive_evidence_matrix_unaccounted_primitive_count",
                    0,
                )
                or 0
            )
            for row in rows
        ),
        "n_standalone_input_trace_llm_primitive_evidence_matrix_selected_without_matrix_rows": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_planner_primitive_evidence_matrix_selected_without_matrix_row_count",
                    0,
                )
                or 0
            )
            for row in rows
        ),
        "n_standalone_input_trace_llm_primitive_evidence_matrix_source_backed_missing_response_source_snippets": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippet_count",
                    0,
                )
                or 0
            )
            for row in rows
        ),
        "n_standalone_input_trace_llm_primitive_evidence_matrix_formal_supported_missing_reuse": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse_count",
                    0,
                )
                or 0
            )
            for row in rows
        ),
        "n_standalone_input_trace_llm_primitive_evidence_matrix_delta_needed_missing_accounting": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting_count",
                    0,
                )
                or 0
            )
            for row in rows
        ),
        "n_standalone_input_traces_with_llm_route_adoption_preconditions": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "has_llm_route_planner_route_adoption_preconditions"
            )
        ),
        "n_standalone_input_trace_llm_route_adoption_precondition_blockers": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_adoption_precondition_blocker_count",
                    0,
                )
            )
            for row in rows
        ),
        "n_standalone_input_trace_llm_route_adoption_precondition_required_response_fields": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_adoption_precondition_required_response_field_count",
                    0,
                )
            )
            for row in rows
        ),
        "n_standalone_input_trace_llm_route_adoption_precondition_target_primitives": sum(
            int(
                row.standalone_input_trace.get(
                    "llm_route_adoption_precondition_target_primitive_count",
                    0,
                )
            )
            for row in rows
        ),
        "n_standalone_input_trace_target_theorem_context_target_mismatches": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "target_theorem_context_packet_target_mismatch"
            )
        ),
        "n_standalone_input_trace_target_theorem_context_route_statement_differs": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "target_theorem_context_route_statement_differs"
            )
        ),
        "n_standalone_input_traces_with_llm_route_planner_metadata": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("llm_route_planner_row_id")
        ),
        "n_standalone_input_traces_with_llm_model_tier": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("llm_route_planner_model_tier")
        ),
        "standalone_input_trace_by_llm_model_tier": dict(
            sorted(by_llm_model_tier.items())
        ),
        "n_standalone_input_traces_with_llm_generator_metadata": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_has_generator_metadata"
            )
        ),
        "n_standalone_input_traces_with_llm_request_contract_blocked": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_request_contract_blocked"
            )
        ),
        "n_standalone_input_traces_with_llm_route_planner_errors": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("llm_route_planner_errors")
        ),
        "n_standalone_input_trace_llm_route_planner_errors": sum(
            len(row.standalone_input_trace.get("llm_route_planner_errors", []))
            for row in rows
        ),
        "n_standalone_input_trace_llm_generation_errors": sum(
            len(row.standalone_input_trace.get("llm_route_planner_generation_errors", []))
            for row in rows
        ),
        "n_standalone_input_traces_with_llm_route_planner_hook_traces": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "applied_llm_route_planner_hook_traces"
            )
        ),
        "n_standalone_input_trace_llm_route_planner_hook_traces": sum(
            len(
                row.standalone_input_trace.get(
                    "applied_llm_route_planner_hook_traces",
                    [],
                )
            )
            for row in rows
        ),
        "n_standalone_input_traces_with_residual_goal_contexts": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("residual_goal_contexts")
        ),
        "n_standalone_input_trace_residual_goal_contexts": sum(
            len(row.standalone_input_trace.get("residual_goal_contexts", []))
            for row in rows
        ),
        "standalone_input_trace_by_llm_route_adoption_status": dict(
            sorted(by_llm_route_adoption_status.items())
        ),
        "n_standalone_input_traces_with_llm_route_adoption_status": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_route_adoption_status"
            )
        ),
        "n_standalone_input_traces_ready_for_route_adoption": (
            by_llm_route_adoption_status.get("READY_FOR_STANDALONE_REPLAY", 0)
        ),
        "n_standalone_input_traces_pending_refinement_before_route_adoption": (
            by_llm_route_adoption_status.get(
                "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION",
                0,
            )
        ),
        "n_standalone_input_trace_route_adoption_blockers": sum(
            len(
                row.standalone_input_trace.get(
                    "llm_route_planner_route_adoption_blockers",
                    [],
                )
            )
            for row in rows
        ),
        "n_standalone_input_traces_with_llm_seed_selection": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_seed_selection_rank"
            )
        ),
        "n_standalone_input_traces_llm_seed_selected": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("llm_route_planner_seed_selected")
        ),
        "n_standalone_input_traces_llm_seed_adoptable_for_standalone_replay": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_seed_adoptable_for_standalone_replay"
            )
        ),
        "n_standalone_input_traces_llm_seed_selected_not_adoptable": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("llm_route_planner_seed_selected")
            and not row.standalone_input_trace.get(
                "llm_route_planner_seed_adoptable_for_standalone_replay"
            )
        ),
        "standalone_input_trace_by_llm_seed_selection_rank": dict(
            sorted(by_llm_seed_selection_rank.items())
        ),
        "n_standalone_input_traces_with_llm_seed_minimal_delta_route_cost": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_seed_minimal_delta_route_cost"
            )
            is not None
        ),
        "n_standalone_input_traces_with_llm_seed_minimal_delta_selected_route_option": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "llm_route_planner_seed_minimal_delta_selected_route_option_id"
            )
        ),
        "n_standalone_input_traces_with_source_snippets": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("has_source_snippets")
        ),
        "n_standalone_input_trace_source_snippets": sum(
            len(row.standalone_input_trace.get("source_snippets", []))
            for row in rows
        ),
        "n_standalone_input_trace_primitive_source_refs": sum(
            len(row.standalone_input_trace.get("primitive_source_refs", []))
            for row in rows
        ),
        "n_standalone_input_traces_with_quality_controls": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("has_quality_controls")
        ),
        "n_standalone_input_trace_quality_control_fields": sum(
            len(row.standalone_input_trace.get("quality_controls", {}))
            for row in rows
        ),
        "n_primitive_source_snippets": sum(
            len(action.get("source_snippets", []))
            for route in routes
            for action in route.get("actions", [])
            if isinstance(action, dict)
        ),
        "n_standalone_input_traces_with_minimal_delta_cost_graph": sum(
            1
            for row in rows
            if row.standalone_input_trace.get(
                "has_minimal_delta_and_or_cost_graph"
            )
        ),
        "n_standalone_input_traces_with_realization_coverage_witness": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("has_realization_coverage_witness")
        ),
        "n_standalone_input_traces_with_complete_realization_coverage": sum(
            1
            for row in rows
            if row.standalone_input_trace.get("realization_coverage_complete")
        ),
        "n_standalone_input_trace_selected_primitives_missing_formal_realization": sum(
            len(
                row.standalone_input_trace.get(
                    "realization_selected_primitives_missing_formal_realization",
                    [],
                )
            )
            for row in rows
        ),
        "n_standalone_input_trace_delta_primitives_missing_route_alignment": sum(
            len(
                row.standalone_input_trace.get(
                    "realization_delta_primitives_missing_route_alignment",
                    [],
                )
            )
            for row in rows
        ),
        "n_standalone_input_trace_route_options": sum(
            int(row.standalone_input_trace.get("minimal_delta_route_option_count", 0) or 0)
            for row in rows
        ),
        "n_route_alignment_edge_schema_valid": n_route_alignment_edge_schema_valid,
        "n_route_alignment_edge_schema_invalid": n_route_alignment_edge_schema_invalid,
        "n_goal_plan_row_schema_valid": n_goal_plan_row_schema_valid,
        "n_goal_plan_row_schema_invalid": n_goal_plan_row_schema_invalid,
        "n_route_revision_triggers": sum(len(row.route_revision_triggers) for row in rows),
        "n_portable_work_packets": sum(len(row.portable_work_packets) for row in rows),
        "n_do_not_formalize_hints": sum(len(row.do_not_formalize_now) for row in rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": False,
        "errors": errors,
        "by_route_class": dict(sorted(by_route_class.items())),
        "rows": row_dicts,
        "goal_plan_row_schema": goal_plan_row_schema,
        "goal_plan_row_schema_errors": goal_plan_row_schema_errors,
        "route_alignment_edge_schema": route_alignment_edge_schema,
        "plan_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "standalone inputs are source and coverage planning records, not theorem proof evidence",
            "coverage labels should be replaced by live library/prover adapter evidence when available",
            "kernel proof status still requires target-prover replay with no placeholders",
        ],
    }
    contract_errors = validate_portable_gap_plan_payload(payload)
    if contract_errors:
        payload["errors"] = [*errors, *contract_errors]
    if n_route_alignment_edge_schema_invalid:
        payload["errors"] = [
            *[str(error) for error in payload.get("errors", [])],
            "route alignment edge schema validation failed",
        ]
    if n_goal_plan_row_schema_invalid:
        payload["errors"] = [
            *[str(error) for error in payload.get("errors", [])],
            "goal plan row schema validation failed",
        ]
    payload["all_ok"] = (
        not payload["errors"]
        and bool(rows)
        and all(row.ok for row in rows)
        and n_route_alignment_edge_schema_invalid == 0
        and n_goal_plan_row_schema_invalid == 0
    )
    if out_dir is not None:
        _write_standalone_plan_outputs(out_dir, input_payload, payload)
    return payload


def validate_standalone_input_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["standalone input must be a JSON object"]
    errors.extend(_kernel_proof_claim_errors(payload, location="standalone_input"))
    component = str(payload.get("component_name", ""))
    if component and component != FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT:
        errors.append("component_name is not formalization_gap_planner_standalone_input")
    if int(payload.get("schema_version", 0) or 0) not in {
        0,
        FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
    }:
        errors.append("schema_version is not supported")
    if not str(payload.get("library_snapshot_ref", "")).strip():
        errors.append("library_snapshot_ref missing")
    routes = _raw_routes(payload)
    if not routes:
        errors.append("routes missing")
    seed_selection = payload.get("llm_route_planner_seed_route_selection")
    if seed_selection is not None:
        errors.extend(
            "llm_route_planner_seed_route_selection." + error
            for error in validate_llm_route_planner_seed_route_selection_payload(
                seed_selection
            )
        )
    payload_target = str(payload.get("target_prover_family", "")).strip()
    mixed_payload_target_keys = _mixed_target_prover_keys(payload_target)
    payload_target_key = (
        "" if mixed_payload_target_keys else _target_prover_key(payload_target)
    )
    route_target_keys: set[str] = set()
    for route in routes:
        metadata = _dict_value(route.get("replan_metadata", {}))
        for target in (
            route.get("target_prover_family", ""),
            route.get("target_prover", ""),
            metadata.get("target_prover_family", ""),
            metadata.get("target_prover", ""),
        ):
            target_key = _target_prover_key(target)
            if target_key:
                route_target_keys.add(target_key)
    if not payload_target_key and not mixed_payload_target_keys and not route_target_keys:
        errors.append("target_prover_family missing")
    for idx, route in enumerate(routes):
        display_name = _display_name(route)
        if not display_name:
            errors.append(f"routes[{idx}].display_name or target_theorem_id missing")
        route_target = str(route.get("target_prover_family", "")).strip()
        metadata = route.get("replan_metadata", {})
        metadata = metadata if isinstance(metadata, dict) else {}
        metadata_target = str(metadata.get("target_prover_family", "")).strip()
        route_target_key = _target_prover_key(route_target)
        metadata_target_key = _target_prover_key(metadata_target)
        if (
            not payload_target_key
            and not route_target_key
            and not metadata_target_key
            and (len(route_target_keys) > 1 or bool(mixed_payload_target_keys))
        ):
            errors.append(f"routes[{idx}].target_prover_family missing")
        for location, target, target_key in (
            (f"routes[{idx}].target_prover_family", route_target, route_target_key),
            (
                f"routes[{idx}].replan_metadata.target_prover_family",
                metadata_target,
                metadata_target_key,
            ),
        ):
            if payload_target_key and target_key and target_key != payload_target_key:
                errors.append(
                    f"{location} {target} does not match target_prover_family "
                    f"{payload_target}"
                )
            if (
                mixed_payload_target_keys
                and target_key
                and target_key not in mixed_payload_target_keys
            ):
                errors.append(
                    f"{location} {target} is not listed in mixed "
                    f"target_prover_family {payload_target}"
                )
        if route_target_key and metadata_target_key and route_target_key != metadata_target_key:
            errors.append(
                f"routes[{idx}].replan_metadata.target_prover_family "
                f"{metadata_target} does not match routes[{idx}].target_prover_family "
                f"{route_target}"
            )
        errors.extend(
            _llm_seed_route_selection_trace_errors(route, location=f"routes[{idx}]")
        )
        errors.extend(
            _llm_route_adoption_blocker_trace_errors(
                route,
                location=f"routes[{idx}]",
            )
        )
        errors.extend(
            _llm_seed_route_selection_trace_errors(
                metadata,
                location=f"routes[{idx}].replan_metadata",
            )
        )
        errors.extend(
            _llm_route_adoption_blocker_trace_errors(
                metadata,
                location=f"routes[{idx}].replan_metadata",
            )
        )
        effective_target = route_target or metadata_target or payload_target
        effective_target_key = (
            route_target_key or metadata_target_key or payload_target_key
        )
        errors.extend(
            _target_theorem_context_packet_input_errors(
                route.get("target_theorem_context_packet", {}),
                location=f"routes[{idx}].target_theorem_context_packet",
                target_prover_family=effective_target,
            )
        )
        metadata_target_context = metadata.get(
            "target_theorem_context_packet",
            metadata.get("llm_route_planner_target_theorem_context_packet", {}),
        )
        errors.extend(
            _target_theorem_context_packet_input_errors(
                metadata_target_context,
                location=f"routes[{idx}].replan_metadata.target_theorem_context_packet",
                target_prover_family=effective_target,
            )
        )
        route_target_context = _dict_value(
            route.get("target_theorem_context_packet", {})
        )
        metadata_target_context_dict = _dict_value(metadata_target_context)
        if (
            route_target_context
            and metadata_target_context_dict
            and route_target_context != metadata_target_context_dict
        ):
            errors.append(
                f"routes[{idx}].target_theorem_context_packet must match "
                f"routes[{idx}].replan_metadata.target_theorem_context_packet"
            )
        route_target_context_summary = _dict_value(
            route.get("llm_route_planner_target_context_summary", {})
        )
        metadata_target_context_summary = _dict_value(
            metadata.get("llm_route_planner_target_context_summary", {})
        )
        if (
            route_target_context_summary
            and metadata_target_context_summary
            and _canonical_target_context_summary(route_target_context_summary)
            != _canonical_target_context_summary(metadata_target_context_summary)
        ):
            errors.append(
                f"routes[{idx}].llm_route_planner_target_context_summary must match "
                f"routes[{idx}].replan_metadata.llm_route_planner_target_context_summary"
            )
        effective_target_context = (
            route_target_context or metadata_target_context_dict
        )
        errors.extend(
            _target_context_summary_input_errors(
                route_target_context_summary,
                target_context_packet=effective_target_context,
                location=(
                    f"routes[{idx}].llm_route_planner_target_context_summary"
                ),
            )
        )
        errors.extend(
            _target_context_summary_input_errors(
                metadata_target_context_summary,
                target_context_packet=effective_target_context,
                location=(
                    f"routes[{idx}].replan_metadata."
                    "llm_route_planner_target_context_summary"
                ),
            )
        )
        route_option_selection_brief = _dict_value(
            route.get("llm_route_planner_route_option_selection_brief", {})
        )
        metadata_route_option_selection_brief = _dict_value(
            metadata.get("llm_route_planner_route_option_selection_brief", {})
        )
        if (
            route_option_selection_brief
            and metadata_route_option_selection_brief
            and route_option_selection_brief != metadata_route_option_selection_brief
        ):
            errors.append(
                f"routes[{idx}].llm_route_planner_route_option_selection_brief must match "
                f"routes[{idx}].replan_metadata.llm_route_planner_route_option_selection_brief"
            )
        effective_library_snapshot_ref = str(
            route.get(
                "library_snapshot_ref",
                metadata.get(
                    "library_snapshot_ref",
                    payload.get("library_snapshot_ref", ""),
                ),
            )
            or ""
        ).strip()
        errors.extend(
            _route_option_selection_brief_input_errors(
                route_option_selection_brief,
                location=(
                    f"routes[{idx}]."
                    "llm_route_planner_route_option_selection_brief"
                ),
                route_id=str(route.get("route_id", "")).strip(),
                target_prover_family=effective_target,
                library_snapshot_ref=effective_library_snapshot_ref,
            )
        )
        errors.extend(
            _route_option_selection_brief_input_errors(
                metadata_route_option_selection_brief,
                location=(
                    f"routes[{idx}].replan_metadata."
                    "llm_route_planner_route_option_selection_brief"
                ),
                route_id=str(route.get("route_id", "")).strip(),
                target_prover_family=effective_target,
                library_snapshot_ref=effective_library_snapshot_ref,
            )
        )
        errors.extend(
            _route_option_selected_route_option_id_input_errors(
                route,
                metadata,
                route_option_selection_brief=route_option_selection_brief,
                metadata_route_option_selection_brief=(
                    metadata_route_option_selection_brief
                ),
                location=f"routes[{idx}]",
            )
        )
        route_adoption_preconditions = _dict_value(
            route.get("llm_route_planner_route_adoption_preconditions", {})
        )
        metadata_route_adoption_preconditions = _dict_value(
            metadata.get("llm_route_planner_route_adoption_preconditions", {})
        )
        if (
            route_adoption_preconditions
            and metadata_route_adoption_preconditions
            and route_adoption_preconditions != metadata_route_adoption_preconditions
        ):
            errors.append(
                f"routes[{idx}].llm_route_planner_route_adoption_preconditions "
                f"must match routes[{idx}].replan_metadata."
                "llm_route_planner_route_adoption_preconditions"
            )
        errors.extend(
            _legacy_lean_declaration_hit_input_errors(
                route,
                location=f"routes[{idx}]",
                target_prover_family=effective_target,
                target_prover_key=effective_target_key,
            )
        )
        errors.extend(
            _legacy_lean_realization_node_input_errors(
                route,
                location=f"routes[{idx}]",
                target_prover_family=effective_target,
                target_prover_key=effective_target_key,
            )
        )
        errors.extend(
            _legacy_lean_declaration_hit_input_errors(
                metadata,
                location=f"routes[{idx}].replan_metadata",
                target_prover_family=effective_target,
                target_prover_key=effective_target_key,
            )
        )
        errors.extend(
            _legacy_lean_realization_node_input_errors(
                metadata,
                location=f"routes[{idx}].replan_metadata",
                target_prover_family=effective_target,
                target_prover_key=effective_target_key,
            )
        )
        errors.extend(
            _candidate_declaration_row_input_errors(
                route.get("candidate_declaration_rows", []),
                location=f"routes[{idx}].candidate_declaration_rows",
                expected_target=effective_target,
                expected_target_key=effective_target_key,
            )
        )
        primitives = _raw_primitives(route)
        if not primitives:
            errors.append(f"routes[{idx}].primitives missing")
        for primitive_idx, primitive in enumerate(primitives):
            if not str(primitive.get("primitive", "")).strip():
                errors.append(f"routes[{idx}].primitives[{primitive_idx}].primitive missing")
            errors.extend(
                _legacy_lean_declaration_hit_input_errors(
                    primitive,
                    location=f"routes[{idx}].primitives[{primitive_idx}]",
                    target_prover_family=effective_target,
                    target_prover_key=effective_target_key,
                )
            )
            errors.extend(
                _candidate_declaration_row_input_errors(
                    primitive.get("candidate_declaration_rows", []),
                    location=(
                        f"routes[{idx}].primitives[{primitive_idx}]"
                        ".candidate_declaration_rows"
                    ),
                    expected_target=effective_target,
                    expected_target_key=effective_target_key,
                )
            )
    return errors


def _kernel_proof_claim_errors(value: Any, *, location: str) -> list[str]:
    errors: list[str] = []
    for path, key, item in _kernel_proof_claim_paths(value, location=location):
        errors.append(
            f"{path}.{key} cannot claim kernel/proved theorem evidence: {item}"
        )
    return errors


def _kernel_proof_claim_paths(
    value: Any,
    *,
    location: str,
) -> tuple[tuple[str, str, object], ...]:
    claims: list[tuple[str, str, object]] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            key_normalized = key_text.lower()
            child_location = f"{location}.{key_text}"
            if (
                key_normalized
                in {
                    "kernel_verified",
                    "full_frontier_theorem_proved",
                    "theorem_proved",
                }
                and item is True
            ):
                claims.append((location, key_text, item))
            if key_normalized in {"proof_evidence_status", "claim_status"}:
                item_upper = str(item).upper()
                if (
                    ("KERNEL_VERIFIED" in item_upper or "PROVED" in item_upper)
                    and "NOT_PROOF_EVIDENCE" not in item_upper
                ):
                    claims.append((location, key_text, item))
            claims.extend(_kernel_proof_claim_paths(item, location=child_location))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            claims.extend(
                _kernel_proof_claim_paths(item, location=f"{location}[{index}]")
            )
    return tuple(claims)


def validate_llm_route_planner_seed_route_selection_payload(
    payload: Any,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    required_fields = (
        "selection_kind",
        "selection_status",
        "selection_policy",
        "selected_route_id",
        "selected_route_adoptable_for_standalone_replay",
        "n_route_candidates",
        "n_adoptable_route_candidates",
        "n_selected_route_candidates_not_adoptable",
        "selection_rows",
        "proof_evidence_status",
        "proof_evidence_boundary",
    )
    for field_name in required_fields:
        if field_name not in payload:
            errors.append(f"{field_name} missing")
    if (
        str(payload.get("selection_kind", ""))
        != FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_KIND
    ):
        errors.append("selection_kind mismatch")
    selection_status = str(payload.get("selection_status", ""))
    if selection_status not in {
        LLM_ROUTE_PLANNER_ACCEPTED_SELECTION_STATUS,
        LLM_ROUTE_PLANNER_FALLBACK_SELECTION_STATUS,
    }:
        errors.append("selection_status unsupported")
    if not str(payload.get("selection_policy", "")).strip():
        errors.append("selection_policy missing")
    if not isinstance(
        payload.get("selected_route_adoptable_for_standalone_replay"),
        bool,
    ):
        errors.append(
            "selected_route_adoptable_for_standalone_replay must be boolean"
        )
    if (
        payload.get("proof_evidence_status")
        != FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_PROOF_EVIDENCE_STATUS
    ):
        errors.append("proof_evidence_status mismatch")
    if not str(payload.get("proof_evidence_boundary", "")).strip():
        errors.append("proof_evidence_boundary missing")

    raw_rows = payload.get("selection_rows", [])
    if not isinstance(raw_rows, list):
        errors.append("selection_rows must be array")
        selection_rows: list[dict[str, Any]] = []
    else:
        selection_rows = [row for row in raw_rows if isinstance(row, dict)]
        if len(selection_rows) != len(raw_rows):
            errors.append("selection_rows items must be objects")

    candidate_count = _int_or_none(payload.get("n_route_candidates"))
    if candidate_count is None or candidate_count < 0:
        errors.append("n_route_candidates must be nonnegative integer")
    elif candidate_count != len(selection_rows):
        errors.append("n_route_candidates must match selection_rows length")
    ready_count = _int_or_none(payload.get("n_ready_route_candidates", 0))
    if ready_count is None or ready_count < 0:
        errors.append("n_ready_route_candidates must be nonnegative integer")
    else:
        computed_ready_count = sum(
            1
            for row in selection_rows
            if str(row.get("route_adoption_status", ""))
            == LLM_ROUTE_PLANNER_READY_FOR_STANDALONE_REPLAY
        )
        if ready_count != computed_ready_count:
            errors.append("n_ready_route_candidates must match selection_rows")
    contract_valid_count = _int_or_none(
        payload.get("n_contract_valid_route_candidates", 0)
    )
    if contract_valid_count is None or contract_valid_count < 0:
        errors.append(
            "n_contract_valid_route_candidates must be nonnegative integer"
        )
    else:
        computed_contract_valid_count = sum(
            1 for row in selection_rows if row.get("response_contract_ok") is True
        )
        if contract_valid_count != computed_contract_valid_count:
            errors.append(
                "n_contract_valid_route_candidates must match selection_rows"
            )
    adoptable_count = _int_or_none(
        payload.get("n_adoptable_route_candidates", 0)
    )
    if adoptable_count is None or adoptable_count < 0:
        errors.append("n_adoptable_route_candidates must be nonnegative integer")
    else:
        computed_adoptable_count = sum(
            1
            for row in selection_rows
            if row.get("adoptable_for_standalone_replay") is True
        )
        if adoptable_count != computed_adoptable_count:
            errors.append("n_adoptable_route_candidates must match selection_rows")
    selected_not_adoptable_count = _int_or_none(
        payload.get("n_selected_route_candidates_not_adoptable", 0)
    )
    if selected_not_adoptable_count is None or selected_not_adoptable_count < 0:
        errors.append(
            "n_selected_route_candidates_not_adoptable must be nonnegative integer"
        )
    else:
        computed_selected_not_adoptable_count = sum(
            1
            for row in selection_rows
            if row.get("selected") is True
            and row.get("adoptable_for_standalone_replay") is not True
        )
        if selected_not_adoptable_count != computed_selected_not_adoptable_count:
            errors.append(
                "n_selected_route_candidates_not_adoptable must match selection_rows"
            )

    ranks: list[int] = []
    selected_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(selection_rows):
        row_errors = _llm_seed_route_selection_row_errors(row)
        errors.extend(f"selection_rows[{idx}].{error}" for error in row_errors)
        rank = _int_or_none(row.get("selection_rank"))
        if rank is not None:
            ranks.append(rank)
        if row.get("selected") is True:
            selected_rows.append(row)
    if ranks and sorted(ranks) != list(range(1, len(selection_rows) + 1)):
        errors.append("selection_rows ranks must be consecutive from 1")
    if selection_rows and len(selected_rows) != 1:
        errors.append(
            f"selection_rows must mark exactly one selected route, found {len(selected_rows)}"
        )
    if selected_rows:
        selected = selected_rows[0]
        if _int_or_none(selected.get("selection_rank")) != 1:
            errors.append("selected selection_row must have rank 1")
        expected_summary_fields = (
            ("selected_route_id", "route_id"),
            ("selected_seed_route_id", "seed_route_id"),
            ("selected_llm_route_planner_row_id", "llm_route_planner_row_id"),
            ("selected_request_id", "request_id"),
            ("selected_route_adoption_status", "route_adoption_status"),
        )
        for summary_field, row_field in expected_summary_fields:
            if str(payload.get(summary_field, "")) != str(selected.get(row_field, "")):
                errors.append(f"{summary_field} must match selected selection_row")
        if payload.get("selected_route_adoptable_for_standalone_replay") != selected.get(
            "adoptable_for_standalone_replay"
        ):
            errors.append(
                "selected_route_adoptable_for_standalone_replay must match selected selection_row"
            )
        selected_cost = _float_or_none(selected.get("minimal_delta_route_cost"))
        summary_cost = _float_or_none(payload.get("selected_minimal_delta_route_cost"))
        if payload.get("selected_minimal_delta_route_cost") is not None and (
            summary_cost is None or summary_cost < 0
        ):
            errors.append(
                "selected_minimal_delta_route_cost must be nonnegative number or null"
            )
        if selected_cost != summary_cost:
            errors.append(
                "selected_minimal_delta_route_cost must match selected selection_row"
            )
        selected_option_id = str(
            selected.get("minimal_delta_selected_route_option_id", "")
        )
        summary_option_id = str(
            payload.get("selected_minimal_delta_selected_route_option_id", "")
        )
        if summary_option_id != selected_option_id:
            errors.append(
                "selected_minimal_delta_selected_route_option_id must match selected selection_row"
            )
    if selection_status == LLM_ROUTE_PLANNER_FALLBACK_SELECTION_STATUS:
        if payload.get("selected_route_adoptable_for_standalone_replay") is True:
            errors.append(
                "fallback_routes_ranked selected_route_adoptable_for_standalone_replay must be false"
            )
        if any(
            row.get("adoptable_for_standalone_replay") is True
            for row in selection_rows
        ):
            errors.append(
                "fallback_routes_ranked selection_rows must not be adoptable_for_standalone_replay"
            )
        if any(
            row.get("llm_route_planner_fallback_route") is not True
            for row in selection_rows
        ):
            errors.append(
                "fallback_routes_ranked selection_rows must carry llm_route_planner_fallback_route true"
            )
    elif selection_status == LLM_ROUTE_PLANNER_ACCEPTED_SELECTION_STATUS:
        if any(
            row.get("llm_route_planner_fallback_route") is True
            for row in selection_rows
        ):
            errors.append(
                "accepted_llm_routes_ranked selection_rows must not carry llm_route_planner_fallback_route true"
            )
    return errors


def _llm_seed_route_selection_row_errors(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = (
        "selection_rank",
        "selected",
        "adoptable_for_standalone_replay",
        "selection_reason",
        "source_order",
        "route_id",
        "seed_route_id",
        "route_adoption_status",
        "route_adoption_status_rank",
        "route_adoption_blocker_count",
        "route_adoption_blockers",
        "acceptance_status",
        "minimal_delta_route_cost",
        "response_contract_ok",
        "proof_evidence_status",
        "proof_evidence_boundary",
    )
    for field_name in required_fields:
        if field_name not in row:
            errors.append(f"{field_name} missing")
    rank = _int_or_none(row.get("selection_rank"))
    if rank is None or rank < 1:
        errors.append("selection_rank must be positive integer")
    if not isinstance(row.get("selected"), bool):
        errors.append("selected must be boolean")
    if not isinstance(row.get("adoptable_for_standalone_replay"), bool):
        errors.append("adoptable_for_standalone_replay must be boolean")
    if not str(row.get("selection_reason", "")).strip():
        errors.append("selection_reason missing")
    source_order = _int_or_none(row.get("source_order"))
    if source_order is None or source_order < 0:
        errors.append("source_order must be nonnegative integer")
    status_rank = _int_or_none(row.get("route_adoption_status_rank"))
    if status_rank is None or status_rank < 0:
        errors.append("route_adoption_status_rank must be nonnegative integer")
    blocker_count = _int_or_none(row.get("route_adoption_blocker_count"))
    blockers = row.get("route_adoption_blockers", [])
    if blocker_count is None or blocker_count < 0:
        errors.append("route_adoption_blocker_count must be nonnegative integer")
    if not isinstance(blockers, list) or any(
        not isinstance(blocker, str) for blocker in blockers
    ):
        errors.append("route_adoption_blockers must be string array")
    else:
        errors.extend(
            _route_adoption_blocker_value_errors(
                blockers,
                field_name="route_adoption_blockers",
            )
        )
        if blocker_count != len(blockers):
            errors.append(
                "route_adoption_blocker_count must match route_adoption_blockers"
            )
    route_cost = _float_or_none(row.get("minimal_delta_route_cost"))
    if row.get("minimal_delta_route_cost") is not None and (
        route_cost is None or route_cost < 0
    ):
        errors.append("minimal_delta_route_cost must be nonnegative number or null")
    if not isinstance(row.get("response_contract_ok"), bool):
        errors.append("response_contract_ok must be boolean")
    if (
        row.get("proof_evidence_status")
        != FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_PROOF_EVIDENCE_STATUS
    ):
        errors.append("proof_evidence_status mismatch")
    if not str(row.get("proof_evidence_boundary", "")).strip():
        errors.append("proof_evidence_boundary missing")
    return errors


def _llm_route_adoption_blocker_trace_errors(
    payload: Any,
    *,
    location: str,
) -> list[str]:
    if not isinstance(payload, dict):
        return []
    if "llm_route_planner_route_adoption_blockers" not in payload:
        return []
    blockers = payload.get("llm_route_planner_route_adoption_blockers", [])
    if not isinstance(blockers, list) or any(
        not isinstance(blocker, str) for blocker in blockers
    ):
        return [
            f"{location}.llm_route_planner_route_adoption_blockers must be string array"
        ]
    return _route_adoption_blocker_value_errors(
        blockers,
        field_name=f"{location}.llm_route_planner_route_adoption_blockers",
    )


def _route_adoption_blocker_value_errors(
    blockers: list[str],
    *,
    field_name: str,
) -> list[str]:
    unsupported = sorted(
        dict.fromkeys(
            blocker
            for blocker in blockers
            if blocker not in LLM_ROUTE_PLANNER_ROUTE_ADOPTION_BLOCKER_VALUES
        )
    )
    if not unsupported:
        return []
    return [
        f"{field_name} contains unsupported route-adoption blocker values: "
        + ", ".join(unsupported[:8])
    ]


def _llm_seed_route_selection_trace_errors(
    payload: Any,
    *,
    location: str,
) -> list[str]:
    if not isinstance(payload, dict):
        return []
    trace_fields = {
        "llm_route_planner_seed_selected",
        "llm_route_planner_seed_adoptable_for_standalone_replay",
        "llm_route_planner_seed_selection_rank",
        "llm_route_planner_seed_selection_reason",
        "llm_route_planner_seed_minimal_delta_route_cost",
        "llm_route_planner_seed_minimal_delta_selected_route_option_id",
    }
    if not trace_fields.intersection(payload):
        return []
    errors: list[str] = []
    if "llm_route_planner_seed_selected" in payload and not isinstance(
        payload.get("llm_route_planner_seed_selected"),
        bool,
    ):
        errors.append(f"{location}.llm_route_planner_seed_selected must be boolean")
    if (
        "llm_route_planner_seed_adoptable_for_standalone_replay" in payload
        and not isinstance(
            payload.get("llm_route_planner_seed_adoptable_for_standalone_replay"),
            bool,
        )
    ):
        errors.append(
            f"{location}.llm_route_planner_seed_adoptable_for_standalone_replay must be boolean"
        )
    rank = _int_or_none(payload.get("llm_route_planner_seed_selection_rank"))
    if rank is None or rank < 1:
        errors.append(
            f"{location}.llm_route_planner_seed_selection_rank must be positive integer"
        )
    if not str(payload.get("llm_route_planner_seed_selection_reason", "")).strip():
        errors.append(f"{location}.llm_route_planner_seed_selection_reason missing")
    cost = payload.get("llm_route_planner_seed_minimal_delta_route_cost")
    parsed_cost = _float_or_none(cost)
    if cost is not None and (parsed_cost is None or parsed_cost < 0):
        errors.append(
            f"{location}.llm_route_planner_seed_minimal_delta_route_cost must be nonnegative number or null"
        )
    if (
        "llm_route_planner_seed_minimal_delta_selected_route_option_id" in payload
        and not isinstance(
            payload.get(
                "llm_route_planner_seed_minimal_delta_selected_route_option_id"
            ),
            str,
        )
    ):
        errors.append(
            f"{location}.llm_route_planner_seed_minimal_delta_selected_route_option_id must be string"
        )
    return errors


def _target_theorem_context_packet_input_errors(
    packet: Any,
    *,
    location: str,
    target_prover_family: str,
) -> list[str]:
    packet_dict = _dict_value(packet)
    if not packet_dict:
        return []
    errors: list[str] = []
    packet_target = str(packet_dict.get("target_prover_family", "")).strip()
    if (
        packet_target
        and target_prover_family
        and _target_prover_key(packet_target)
        != _target_prover_key(target_prover_family)
    ):
        errors.append(
            f"{location}.target_prover_family {packet_target} does not match "
            f"target_prover_family {target_prover_family}"
        )
    return errors


def _route_option_selection_brief_input_errors(
    brief: Any,
    *,
    location: str,
    route_id: str,
    target_prover_family: str,
    library_snapshot_ref: str,
) -> list[str]:
    brief_dict = _dict_value(brief)
    if not brief_dict:
        return []
    _ = route_id
    errors: list[str] = []
    if (
        brief_dict.get("brief_kind")
        != FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_ROUTE_OPTION_SELECTION_BRIEF_KIND
    ):
        errors.append(
            f"{location}.brief_kind must equal "
            + FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_ROUTE_OPTION_SELECTION_BRIEF_KIND
        )
    target_key = _target_prover_key(target_prover_family)
    brief_target = str(brief_dict.get("target_prover_family", "") or "").strip()
    brief_target_key = _target_prover_key(brief_target)
    if target_key and brief_target_key and target_key != brief_target_key:
        errors.append(
            f"{location}.target_prover_family {brief_target} does not match "
            f"target_prover_family {target_prover_family}"
        )
    brief_library_snapshot_ref = str(
        brief_dict.get("library_snapshot_ref", "") or ""
    ).strip()
    if (
        library_snapshot_ref
        and brief_library_snapshot_ref
        and brief_library_snapshot_ref != library_snapshot_ref
    ):
        errors.append(
            f"{location}.library_snapshot_ref {brief_library_snapshot_ref} "
            f"does not match library_snapshot_ref {library_snapshot_ref}"
        )

    candidate_options = _dict_list(brief_dict.get("candidate_route_options", []))
    reported_candidate_count = _int_or_none(
        brief_dict.get("n_candidate_route_options")
    )
    if (
        reported_candidate_count is None
        or reported_candidate_count != len(candidate_options)
    ):
        errors.append(
            f"{location}.n_candidate_route_options must match "
            "candidate_route_options"
        )

    candidate_primitive_total = 0
    for option_index, option in enumerate(candidate_options):
        selected_primitives = _str_tuple(option.get("selected_primitives", []))
        candidate_primitive_total += len(selected_primitives)
        reported_option_primitives = _int_or_none(
            option.get("n_selected_primitives")
        )
        if (
            reported_option_primitives is None
            or reported_option_primitives != len(selected_primitives)
        ):
            errors.append(
                f"{location}.candidate_route_options[{option_index}]."
                "n_selected_primitives must match selected_primitives"
            )

    reported_primitive_total = _int_or_none(
        brief_dict.get("n_candidate_route_option_primitives")
    )
    if (
        reported_primitive_total is None
        or reported_primitive_total != candidate_primitive_total
    ):
        errors.append(
            f"{location}.n_candidate_route_option_primitives must match "
            "candidate_route_options selected_primitives"
        )

    candidate_ids = {
        str(option.get("route_option_id", "") or "").strip()
        for option in candidate_options
        if str(option.get("route_option_id", "") or "").strip()
    }
    lower_bound_id = str(
        brief_dict.get("lower_bound_selected_route_option_id", "") or ""
    ).strip()
    if lower_bound_id and lower_bound_id not in candidate_ids:
        errors.append(
            f"{location}.lower_bound_selected_route_option_id must name a "
            "candidate_route_options route_option_id"
        )
    selected_by_policy_options = [
        option
        for option in candidate_options
        if bool(option.get("selected_by_lower_bound_policy", False))
    ]
    if candidate_options and len(selected_by_policy_options) != 1:
        errors.append(
            f"{location}.candidate_route_options must mark exactly one "
            "selected_by_lower_bound_policy option"
        )
    if selected_by_policy_options and lower_bound_id:
        selected_option_id = str(
            selected_by_policy_options[0].get("route_option_id", "") or ""
        ).strip()
        if selected_option_id and selected_option_id != lower_bound_id:
            errors.append(
                f"{location}.lower_bound_selected_route_option_id must match "
                "the selected_by_lower_bound_policy option"
            )

    reported_tied_count = _int_or_none(
        brief_dict.get("n_lower_bound_tied_route_options")
    )
    if reported_tied_count is not None:
        observed_tied_count = sum(
            1
            for option in candidate_options
            if bool(option.get("lower_bound_tied_for_best", False))
        )
        if reported_tied_count != observed_tied_count:
            errors.append(
                f"{location}.n_lower_bound_tied_route_options must match "
                "candidate_route_options"
            )

    selected_option = next(
        (
            option
            for option in candidate_options
            if str(option.get("route_option_id", "") or "").strip()
            == lower_bound_id
        ),
        {},
    )
    reported_selected_cost = _float_or_none(
        brief_dict.get("lower_bound_selected_route_cost")
    )
    observed_selected_cost = _float_or_none(
        selected_option.get("minimum_route_base_cost")
    )
    if (
        lower_bound_id
        and reported_selected_cost is not None
        and observed_selected_cost is not None
        and abs(reported_selected_cost - observed_selected_cost) > 1e-9
    ):
        errors.append(
            f"{location}.lower_bound_selected_route_cost must match selected "
            "candidate_route_options minimum_route_base_cost"
        )
    return errors


def _route_option_selected_route_option_id_input_errors(
    route: Mapping[str, Any],
    metadata: Mapping[str, Any],
    *,
    route_option_selection_brief: Mapping[str, Any],
    metadata_route_option_selection_brief: Mapping[str, Any],
    location: str,
) -> list[str]:
    route_selected_id = str(
        route.get("llm_route_planner_route_option_selected_route_option_id", "")
        or ""
    ).strip()
    metadata_selected_id = str(
        metadata.get("llm_route_planner_route_option_selected_route_option_id", "")
        or ""
    ).strip()
    route_expected_id = _selected_route_option_id_from_route_option_brief(
        route_option_selection_brief
    )
    metadata_expected_id = _selected_route_option_id_from_route_option_brief(
        metadata_route_option_selection_brief
    )
    errors: list[str] = []
    route_field = (
        f"{location}.llm_route_planner_route_option_selected_route_option_id"
    )
    metadata_field = (
        f"{location}.replan_metadata."
        "llm_route_planner_route_option_selected_route_option_id"
    )
    if route_expected_id:
        if not route_selected_id:
            errors.append(
                f"{route_field} missing for "
                f"{location}.llm_route_planner_route_option_selection_brief"
            )
        elif route_selected_id != route_expected_id:
            errors.append(
                f"{route_field} must match "
                f"{location}.llm_route_planner_route_option_selection_brief "
                "selected route option"
            )
    if metadata_expected_id:
        if not metadata_selected_id:
            errors.append(
                f"{metadata_field} missing for "
                f"{location}.replan_metadata."
                "llm_route_planner_route_option_selection_brief"
            )
        elif metadata_selected_id != metadata_expected_id:
            errors.append(
                f"{metadata_field} must match "
                f"{location}.replan_metadata."
                "llm_route_planner_route_option_selection_brief selected "
                "route option"
            )
    if route_selected_id and metadata_selected_id and (
        route_selected_id != metadata_selected_id
    ):
        errors.append(
            f"{route_field} must match {metadata_field}"
        )
    return errors


def _selected_route_option_id_from_route_option_brief(
    brief: Mapping[str, Any],
) -> str:
    brief_dict = _dict_value(brief)
    selected = str(
        brief_dict.get("lower_bound_selected_route_option_id", "") or ""
    ).strip()
    if selected:
        return selected
    for option in _dict_list(brief_dict.get("candidate_route_options", [])):
        if option.get("selected_by_lower_bound_policy") is True or option.get(
            "selected"
        ) is True:
            option_id = str(option.get("route_option_id", "") or "").strip()
            if option_id:
                return option_id
    for binding in _dict_list(brief_dict.get("required_response_bindings", [])):
        field = str(binding.get("field", "") or "").strip()
        if field.endswith("selected_route_option_id"):
            value = str(binding.get("required_value", "") or "").strip()
            if value:
                return value
    return ""


_TARGET_CONTEXT_SUMMARY_FIELD_ALIASES = {
    "normalized_procedures": (
        "normalized_procedures",
        "normalized_statistical_procedures",
    ),
    "desired_conclusions": (
        "desired_conclusions",
        "normalized_desired_conclusions",
    ),
    "desired_theorem_shapes": (
        "desired_theorem_shapes",
        "normalized_theorem_shapes",
    ),
}


_TARGET_CONTEXT_SUMMARY_PACKET_FIELDS = (
    "normalized_objects",
    "normalized_assumptions",
    "normalized_procedures",
    "desired_conclusions",
    "desired_theorem_shapes",
    "target_intake_ids",
    "proof_source_refs",
)


def _target_context_summary_input_errors(
    summary: Any,
    *,
    target_context_packet: dict[str, object],
    location: str,
) -> list[str]:
    summary_dict = _canonical_target_context_summary(_dict_value(summary))
    if not summary_dict or not target_context_packet:
        return []
    errors: list[str] = []
    for field_name in _TARGET_CONTEXT_SUMMARY_PACKET_FIELDS:
        expected_values = _target_context_packet_values(
            target_context_packet,
            field_name,
        )
        if not expected_values:
            continue
        actual_values = _str_tuple(summary_dict.get(field_name, []))
        missing = _missing_target_context_summary_values(
            expected_values,
            actual_values,
        )
        if missing:
            errors.append(
                f"{location}.{field_name} must preserve "
                "target_theorem_context_packet values; missing: "
                + "; ".join(missing[:8])
            )
    return errors


def _target_context_packet_values(
    packet: dict[str, object],
    field_name: str,
) -> tuple[str, ...]:
    aliases = _TARGET_CONTEXT_SUMMARY_FIELD_ALIASES.get(
        field_name,
        (field_name,),
    )
    values: list[str] = []
    seen: set[str] = set()
    for alias in aliases:
        for value in _str_tuple(packet.get(alias, [])):
            key = _target_context_summary_value_key(value)
            if key in seen:
                continue
            seen.add(key)
            values.append(value)
    return tuple(values)


def _canonical_target_context_summary(
    summary: dict[str, object],
) -> dict[str, object]:
    if not summary:
        return {}
    legacy_aliases = {
        alias
        for aliases in _TARGET_CONTEXT_SUMMARY_FIELD_ALIASES.values()
        for alias in aliases
    } - set(_TARGET_CONTEXT_SUMMARY_FIELD_ALIASES)
    normalized: dict[str, object] = {
        str(key): value
        for key, value in summary.items()
        if str(key) not in legacy_aliases
    }
    for canonical_field, aliases in _TARGET_CONTEXT_SUMMARY_FIELD_ALIASES.items():
        values: list[str] = []
        seen: set[str] = set()
        for alias in aliases:
            for value in _str_tuple(summary.get(alias, [])):
                key = _target_context_summary_value_key(value)
                if key in seen:
                    continue
                seen.add(key)
                values.append(value)
        if values:
            normalized[canonical_field] = values
    return normalized


def _missing_target_context_summary_values(
    expected_values: tuple[str, ...],
    actual_values: tuple[str, ...],
) -> tuple[str, ...]:
    actual_keys = {
        _target_context_summary_value_key(value) for value in actual_values
    }
    return tuple(
        value
        for value in expected_values
        if _target_context_summary_value_key(value) not in actual_keys
    )


def _target_context_summary_value_key(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def standalone_input_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    route_adoption_blocker_array = {
        "type": "array",
        "items": {"enum": list(LLM_ROUTE_PLANNER_ROUTE_ADOPTION_BLOCKER_VALUES)},
    }
    object_array = {"type": "array", "items": {"type": "object"}}
    candidate_declaration_rows = {
        "type": "array",
        "items": {"$ref": "#/$defs/candidate_declaration_row"},
    }
    seed_route_selection_def = _llm_seed_route_selection_schema_def()
    seed_route_selection_trace_properties = (
        _llm_seed_route_selection_trace_properties()
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
        "title": "Formalization Gap Planner Standalone Input",
        "description": (
            "Portable theorem-route input for building a library-aware "
            "formalization gap plan without the full AI Statistician pipeline."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": ["library_snapshot_ref", "routes"],
        "properties": {
            "schema_version": {
                "const": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION
            },
            "component_name": {
                "const": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT
            },
            "target_prover_family": {"type": "string"},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "background_primitives": string_array,
            "llm_route_planner_seed_route_selection": {
                "$ref": "#/$defs/llm_route_planner_seed_route_selection"
            },
            "routes": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/route"},
            },
        },
        "$defs": {
            "route": {
                "type": "object",
                "additionalProperties": True,
                "required": ["display_name", "primitives"],
                "properties": {
                    "route_id": {"type": "string"},
                    "display_name": {"type": "string", "minLength": 1},
                    "target_prover_family": {"type": "string"},
                    "theorem_statement": {"type": "string"},
                    "theorem_skeleton": {"type": "string"},
                    "target_theorem_context_packet": {"type": "object"},
                    "llm_route_planner_target_context_summary": {"type": "object"},
                    "llm_route_planner_route_planning_brief": {"type": "object"},
                    "llm_route_planner_route_option_selection_brief": {
                        "type": "object"
                    },
                    "llm_route_planner_route_option_selected_route_option_id": {
                        "type": "string"
                    },
                    "llm_route_planner_primitive_evidence_matrix_witness": {
                        "type": "object"
                    },
                    "llm_route_planner_route_adoption_preconditions": {
                        "type": "object"
                    },
                    "llm_route_planner_route_adoption_blockers": (
                        route_adoption_blocker_array
                    ),
                    "route_class": {"type": "string"},
                    "recommended_action": {"type": "string"},
                    "source_refs": string_array,
                    "source_snippets": object_array,
                    "quality_controls": {"$ref": "#/$defs/quality_controls"},
                    "informal_proof_steps": string_array,
                    "candidate_declaration_rows": candidate_declaration_rows,
                    "import_cone_size": {"type": "integer", "minimum": 0},
                    "dependency_graph_depth": {"type": "integer", "minimum": 0},
                    "blocker_count": {"type": "integer", "minimum": 0},
                    "source_trust_level": {"type": "string"},
                    "revised_informal_knowledge_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/dag_node"},
                    },
                    "revised_formal_realization_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/dag_node"},
                    },
                    "revised_lean_realization_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/dag_node"},
                    },
                    "revised_route_alignment_edges": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_alignment_edge"},
                    },
                    "minimal_delta_and_or_cost_graph": {
                        "$ref": "#/$defs/minimal_delta_and_or_cost_graph"
                    },
                    "realization_coverage_witness": {
                        "$ref": "#/$defs/realization_coverage_witness"
                    },
                    "replan_metadata": {"$ref": "#/$defs/replan_metadata"},
                    **seed_route_selection_trace_properties,
                    "primitives": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/$defs/primitive"},
                    },
                },
            },
            "primitive": {
                "type": "object",
                "additionalProperties": True,
                "required": ["primitive"],
                "properties": {
                    "primitive": {"type": "string", "minLength": 1},
                    "coverage_status": {"type": "string"},
                    "candidate_declarations": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "candidate_declaration_rows": candidate_declaration_rows,
                    "expected_premises": string_array,
                    "bridge_candidate_obligations": string_array,
                    "source_refs": string_array,
                    "source_snippets": object_array,
                    "cost": {"type": "integer", "minimum": 0},
                    "side_conditions": string_array,
                    "next_step": {"type": "string"},
                },
            },
            "dag_node": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "node_id": {"type": "string"},
                    "label": {"type": "string"},
                    "primitive": {"type": "string"},
                    "source_ref": {"type": "string"},
                    "coverage_status": {"type": "string"},
                },
            },
            "route_alignment_edge": {
                "type": "object",
                "additionalProperties": True,
                "required": ["source", "target", "primitive"],
                "properties": {
                    "source": {"type": "string", "minLength": 1},
                    "target": {"type": "string", "minLength": 1},
                    "kind": {"type": "string"},
                    "edge_type": {"type": "string"},
                    "primitive": {"type": "string", "minLength": 1},
                    "alignment_status": {"type": "string"},
                    "proof_evidence_status": {"type": "string"},
                    "proof_evidence_boundary": {"type": "string"},
                },
            },
            "lean_declaration_hit": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "primitive": {"type": "string"},
                    "declaration": {"type": "string"},
                    "declaration_name": {"type": "string"},
                    "coverage_status": {"type": "string"},
                    "source_ref": {"type": "string"},
                },
            },
            "formal_declaration_hit": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "primitive": {"type": "string"},
                    "declaration": {"type": "string"},
                    "declaration_name": {"type": "string"},
                    "coverage_status": {"type": "string"},
                    "source_ref": {"type": "string"},
                    "target_prover_family": {"type": "string"},
                },
            },
            "candidate_declaration_row": {
                "type": "object",
                "additionalProperties": True,
                "anyOf": [
                    {"required": ["declaration"]},
                    {"required": ["declaration_name"]},
                    {"required": ["candidate_declaration"]},
                    {"required": ["name"]},
                    {"required": ["full_name"]},
                ],
                "properties": {
                    "declaration": {"type": "string", "minLength": 1},
                    "declaration_name": {"type": "string"},
                    "candidate_declaration": {"type": "string"},
                    "name": {"type": "string"},
                    "full_name": {"type": "string"},
                    "target_prover_family": {"type": "string"},
                    "target_prover": {"type": "string"},
                    "source_field": {"type": "string"},
                    "source_fields": string_array,
                    "target_primitives": string_array,
                    "supported_target_primitives": string_array,
                    "unsupported_target_primitives": string_array,
                    "source_refs": string_array,
                    "matched_terms": string_array,
                },
            },
            "replan_metadata": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "source_route_id": {"type": "string"},
                    "source_goal_plan_id": {"type": "string"},
                    "target_prover_family": {"type": "string"},
                    "route_revision_overlay_id": {"type": "string"},
                    "revision_status": {"type": "string"},
                    "stability_decision": {"type": "string"},
                    "requires_replan": {"type": "boolean"},
                    "applied_proposal_ids": string_array,
                    "applied_refinement_evidence_ids": string_array,
                    "applied_hook_kinds": string_array,
                    "applied_resource_response_traces": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "applied_llm_route_planner_hook_traces": object_array,
                    "resource_response_awaiting_request_ids": string_array,
                    "resource_response_rejected_request_ids": string_array,
                    "applied_prover_attempt_statuses": string_array,
                    "applied_prover_diagnostic_signatures": string_array,
                    "route_revision_reasons": string_array,
                    "route_revision_summaries": string_array,
                    "residual_goals": string_array,
                    "source_refs": string_array,
                    "source_snippets": object_array,
                    "quality_controls": {"$ref": "#/$defs/quality_controls"},
                    "formal_declaration_hits": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/formal_declaration_hit"},
                    },
                    "lean_declaration_hits": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/lean_declaration_hit"},
                    },
                    "revised_informal_knowledge_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/dag_node"},
                    },
                    "revised_formal_realization_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/dag_node"},
                    },
                    "revised_lean_realization_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/dag_node"},
                    },
                    "revised_route_alignment_edges": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_alignment_edge"},
                    },
                    "minimal_delta_and_or_cost_graph": {
                        "$ref": "#/$defs/minimal_delta_and_or_cost_graph"
                    },
                    "llm_route_planner_realization_coverage_witness": {
                        "$ref": "#/$defs/realization_coverage_witness"
                    },
                    "target_theorem_context_packet": {"type": "object"},
                    "llm_route_planner_target_theorem_context_packet": {
                        "type": "object"
                    },
                    "llm_route_planner_target_context_summary": {"type": "object"},
                    "llm_route_planner_route_planning_brief": {"type": "object"},
                    "llm_route_planner_route_option_selection_brief": {
                        "type": "object"
                    },
                    "llm_route_planner_route_option_selected_route_option_id": {
                        "type": "string"
                    },
                    "llm_route_planner_primitive_evidence_matrix_witness": {
                        "type": "object"
                    },
                    "llm_route_planner_route_adoption_preconditions": {
                        "type": "object"
                    },
                    **seed_route_selection_trace_properties,
                    "alignment_edge_primitives": string_array,
                    "proof_evidence_status": {"type": "string"},
                },
            },
            "realization_coverage_witness": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "selected_primitives": string_array,
                    "delta_primitives": string_array,
                    "introduced_primitives": string_array,
                    "aligned_primitives": string_array,
                    "selected_primitives_missing_formal_realization_node": string_array,
                    "delta_primitives_missing_route_alignment_edge": string_array,
                    "introduced_primitives_missing_route_alignment_edge": string_array,
                    "realization_coverage_complete": {"type": "boolean"},
                },
            },
            "quality_controls": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    field_name: string_array
                    for field_name in QUALITY_CONTROL_FIELDS
                },
            },
            "minimal_delta_and_or_cost_graph": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "graph_kind": {"type": "string"},
                    "selected_route_option_id": {"type": "string"},
                    "route_options": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_option_cost"},
                    },
                    "or_nodes": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "and_edges": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                },
            },
            "route_option_cost": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "route_option_id": {"type": "string"},
                    "selected": {"type": "boolean"},
                    "selected_primitives": string_array,
                    "route_cost": {"type": "number", "minimum": 0},
                    "cost_rationale": {"type": "string"},
                },
            },
            "llm_route_planner_seed_route_selection": seed_route_selection_def,
        },
    }


def llm_route_planner_seed_route_selection_json_schema() -> dict[str, object]:
    """Schema for how accepted LLM routes are ranked into a standalone seed.

    This is intentionally packaged separately from the full standalone input
    schema so downstream prover adapters can validate the selection decision
    trace without consuming the entire AI Statistician planner bundle.
    """

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
        "title": "Formalization Gap Planner LLM Route Planner Seed Route Selection",
        "description": (
            "Reusable contract for the ranked route-selection summary emitted "
            "when LLM route-planner responses are turned into a standalone "
            "formalization-gap-planner seed."
        ),
        **_llm_seed_route_selection_schema_def(),
    }


def _llm_seed_route_selection_trace_properties() -> dict[str, object]:
    return {
        "llm_route_planner_seed_selected": {"type": "boolean"},
        "llm_route_planner_seed_adoptable_for_standalone_replay": {
            "type": "boolean"
        },
        "llm_route_planner_seed_selection_rank": {
            "type": "integer",
            "minimum": 1,
        },
        "llm_route_planner_seed_selection_reason": {
            "type": "string",
            "minLength": 1,
        },
        "llm_route_planner_seed_minimal_delta_route_cost": {
            "anyOf": [
                {"type": "number", "minimum": 0},
                {"type": "null"},
            ]
        },
        "llm_route_planner_seed_minimal_delta_selected_route_option_id": {
            "type": "string"
        },
        "llm_route_planner_route_adoption_blockers": {
            "type": "array",
            "items": {
                "enum": list(LLM_ROUTE_PLANNER_ROUTE_ADOPTION_BLOCKER_VALUES)
            },
        },
    }


def _llm_seed_route_selection_schema_def() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    nullable_nonnegative_number = {
        "anyOf": [
            {"type": "number", "minimum": 0},
            {"type": "null"},
        ]
    }
    selection_row_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "selection_rank",
            "selected",
            "adoptable_for_standalone_replay",
            "selection_reason",
            "source_order",
            "route_id",
            "seed_route_id",
            "route_adoption_status",
            "route_adoption_status_rank",
            "route_adoption_blocker_count",
            "route_adoption_blockers",
            "acceptance_status",
            "minimal_delta_route_cost",
            "response_contract_ok",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "selection_rank": {"type": "integer", "minimum": 1},
            "selected": {"type": "boolean"},
            "adoptable_for_standalone_replay": {"type": "boolean"},
            "selection_reason": {"type": "string", "minLength": 1},
            "source_order": {"type": "integer", "minimum": 0},
            "route_id": {"type": "string"},
            "seed_route_id": {"type": "string"},
            "llm_route_planner_row_id": {"type": "string"},
            "request_id": {"type": "string"},
            "route_adoption_status": {"type": "string"},
            "route_adoption_status_rank": {
                "type": "integer",
                "minimum": 0,
            },
            "route_adoption_blocker_count": {
                "type": "integer",
                "minimum": 0,
            },
            "route_adoption_blockers": {
                "type": "array",
                "items": {
                    "enum": list(LLM_ROUTE_PLANNER_ROUTE_ADOPTION_BLOCKER_VALUES)
                },
            },
            "acceptance_status": {"type": "string"},
            "minimal_delta_route_cost": nullable_nonnegative_number,
            "minimal_delta_selected_route_option_id": {"type": "string"},
            "response_contract_ok": {"type": "boolean"},
            "proof_evidence_status": {
                "const": (
                    FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_PROOF_EVIDENCE_STATUS
                )
            },
            "proof_evidence_boundary": {
                "type": "string",
                "minLength": 1,
            },
        },
    }
    return {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "selection_kind",
            "selection_status",
            "selection_policy",
            "selected_route_id",
            "selected_route_adoptable_for_standalone_replay",
            "n_route_candidates",
            "n_adoptable_route_candidates",
            "n_selected_route_candidates_not_adoptable",
            "selection_rows",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "selection_kind": {
                "const": (
                    FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_KIND
                )
            },
            "selection_status": {
                "enum": [
                    "accepted_llm_routes_ranked",
                    "fallback_routes_ranked",
                ]
            },
            "selection_policy": {"type": "string", "minLength": 1},
            "selected_route_id": {"type": "string"},
            "selected_seed_route_id": {"type": "string"},
            "selected_llm_route_planner_row_id": {"type": "string"},
            "selected_request_id": {"type": "string"},
            "selected_route_adoption_status": {"type": "string"},
            "selected_route_adoptable_for_standalone_replay": {
                "type": "boolean"
            },
            "selected_minimal_delta_route_cost": nullable_nonnegative_number,
            "selected_minimal_delta_selected_route_option_id": {"type": "string"},
            "n_route_candidates": {"type": "integer", "minimum": 0},
            "n_ready_route_candidates": {"type": "integer", "minimum": 0},
            "n_adoptable_route_candidates": {"type": "integer", "minimum": 0},
            "n_selected_route_candidates_not_adoptable": {
                "type": "integer",
                "minimum": 0,
            },
            "n_contract_valid_route_candidates": {
                "type": "integer",
                "minimum": 0,
            },
            "selection_rows": {
                "type": "array",
                "items": selection_row_schema,
            },
            "proof_evidence_status": {
                "const": (
                    FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_PROOF_EVIDENCE_STATUS
                )
            },
            "proof_evidence_boundary": {"type": "string", "minLength": 1},
        },
    }


def _write_standalone_plan_outputs(
    out_dir: Path,
    input_payload: dict[str, Any],
    payload: dict[str, object],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    (out_dir / "goal_conditioned_minimal_formalization_plan.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )
    (out_dir / "goal_conditioned_minimal_formalization_plan.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )
    write_portable_gap_plan_schema(out_dir)
    write_portable_gap_plan_row_schema(out_dir)
    write_route_alignment_edge_schema(out_dir)
    (out_dir / "formalization_gap_planner_standalone_input.schema.json").write_text(
        json.dumps(standalone_input_json_schema(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_standalone_input.normalized.json").write_text(
        json.dumps(input_payload, indent=2, default=str),
        encoding="utf-8",
    )


def _route_specs(
    payload: dict[str, Any],
    errors: list[str],
    *,
    target_prover_family: str,
) -> list[tuple[dict[str, object], dict[str, object]]]:
    specs: list[tuple[dict[str, object], dict[str, object]]] = []
    for idx, raw_route in enumerate(_raw_routes(payload)):
        route_id = str(raw_route.get("route_id", "")).strip() or (
            "standalone_route:" + stable_hash([_display_name(raw_route), idx])[:16]
        )
        graph_route_cost = _selected_cost_graph_route_cost(raw_route)
        primitive_costs = _minimal_delta_primitive_costs(raw_route)
        metadata = raw_route.get("replan_metadata", {})
        metadata = metadata if isinstance(metadata, dict) else {}
        raw_route_target_prover_family = str(
            raw_route.get("target_prover_family", "")
            or raw_route.get("target_prover", "")
            or metadata.get("target_prover_family", "")
            or metadata.get("target_prover", "")
            or target_prover_family
        ).strip()
        route_target_prover_family = (
            normalize_target_prover_family(raw_route_target_prover_family)
            or raw_route_target_prover_family
        )
        actions = [
            _action_for_primitive(
                route_id,
                primitive,
                primitive_idx,
                primitive_costs=primitive_costs,
                target_prover_family=route_target_prover_family,
            )
            for primitive_idx, primitive in enumerate(_raw_primitives(raw_route))
        ]
        selected_primitives = _str_list(raw_route.get("selected_primitives", []))
        if not selected_primitives:
            selected_primitives = _str_list(
                metadata.get("revised_selected_primitives", [])
            )
        if not selected_primitives:
            selected_primitives = [
                str(action.get("primitive", ""))
                for action in actions
                if action.get("primitive")
            ]
        if not selected_primitives:
            errors.append(f"routes[{idx}] has no selected primitives")
        route_class = str(raw_route.get("route_class", "")).strip() or _route_class(actions)
        total_estimated_cost = raw_route.get("total_estimated_cost", None)
        if total_estimated_cost is None:
            total_estimated_cost = graph_route_cost
        if total_estimated_cost is None:
            total_estimated_cost = sum(int(action.get("total_cost", 0) or 0) for action in actions)
        route: dict[str, object] = {
            "route_id": route_id,
            "task_id": str(raw_route.get("task_id", "")).strip() or route_id,
            "question_id": str(raw_route.get("question_id", "standalone_input")),
            "problem_class": str(raw_route.get("problem_class", "standalone_theorem")),
            "theorem_goal_id": str(raw_route.get("theorem_goal_id", "")) or _display_name(raw_route),
            "display_name": _display_name(raw_route),
            "target_prover_family": route_target_prover_family,
            "theorem_skeleton": str(raw_route.get("theorem_skeleton", "")),
            "theorem_statement": str(raw_route.get("theorem_statement", "")),
            "source_refs": _str_tuple(raw_route.get("source_refs", [])),
            "source_snippets": _dict_list(
                raw_route.get("source_snippets", metadata.get("source_snippets", []))
            ),
            "informal_proof_steps": _str_tuple(raw_route.get("informal_proof_steps", [])),
            "route_class": route_class,
            "total_estimated_cost": int(total_estimated_cost or 0),
            "selected_primitives": selected_primitives,
            "standalone_input_trace": _standalone_input_trace(
                raw_route,
                route_id=route_id,
                route_index=idx,
                target_prover_family=route_target_prover_family,
            ),
            "route_revision_triggers": _route_or_metadata_rows(
                raw_route,
                metadata,
                "route_revision_triggers",
                "llm_route_planner_route_revision_triggers",
            ),
            "interactive_refinement_hooks": _route_or_metadata_rows(
                raw_route,
                metadata,
                "interactive_refinement_hooks",
                "llm_route_planner_interactive_refinement_hooks",
            ),
            "actions": actions,
        }
        queue_row: dict[str, object] = {
            "route_id": route_id,
            "item_id": "standalone_queue_item:" + stable_hash(route_id)[:16],
            "recommended_action": str(
                raw_route.get("recommended_action", _recommended_action(route_class))
            ),
            "import_cone_size": int(raw_route.get("import_cone_size", 0) or 0),
            "dependency_graph_depth": int(raw_route.get("dependency_graph_depth", 0) or 0),
            "blocker_count": int(raw_route.get("blocker_count", _blocker_count(actions)) or 0),
            "source_trust_level": str(
                raw_route.get("source_trust_level", _source_trust_level(actions))
            ),
        }
        specs.append((route, queue_row))
    return specs


def _action_for_primitive(
    route_id: str,
    primitive: dict[str, Any],
    primitive_idx: int,
    *,
    primitive_costs: dict[str, int] | None = None,
    target_prover_family: str,
) -> dict[str, object]:
    primitive_name = str(primitive.get("primitive", "")).strip()
    coverage_status = str(primitive.get("coverage_status", "unknown"))
    action_class = _action_class_for_coverage(coverage_status)
    primitive_costs = primitive_costs or {}
    candidate_declaration_rows = _candidate_declaration_rows_for_primitive(
        primitive,
        target_prover_family=target_prover_family,
    )
    candidate_declarations = _candidate_declarations_for_primitive(
        primitive,
        candidate_declaration_rows=candidate_declaration_rows,
    )
    total_cost = int(
        primitive.get(
            "cost",
            primitive_costs.get(
                _normalize_primitive_key(primitive_name),
                _default_cost(action_class, coverage_status),
            ),
        )
        or 0
    )
    blockers = [
        str(item)
        for item in primitive.get("side_conditions", []) or []
        if str(item)
    ]
    if _coverage_unknown(coverage_status):
        blockers.append(f"coverage_unknown:{primitive_name}")
    return {
        "action_id": "standalone_action:"
        + stable_hash([route_id, primitive_name, primitive_idx, action_class])[:16],
        "primitive": primitive_name,
        "action_class": action_class,
        "total_cost": total_cost,
        "expected_premises": _str_tuple(primitive.get("expected_premises", [])),
        "bridge_candidate_obligations": _str_tuple(
            primitive.get("bridge_candidate_obligations", [])
        ),
        "candidate_declarations": candidate_declarations,
        "candidate_declaration_rows": candidate_declaration_rows,
        "next_step": str(
            primitive.get("next_step", _next_step_for_action(action_class, primitive_name))
        ),
        "blocked_reasons": tuple(blockers),
        "source_refs": _str_tuple(primitive.get("source_refs", [])),
        "source_snippets": _dict_list(primitive.get("source_snippets", [])),
        "coverage_status": coverage_status,
    }


def _standalone_input_trace(
    raw_route: dict[str, Any],
    *,
    route_id: str,
    route_index: int,
    target_prover_family: str,
) -> dict[str, object]:
    metadata = raw_route.get("replan_metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    revised_informal_nodes = _dict_list(
        raw_route.get(
            "revised_informal_knowledge_dag_nodes",
            metadata.get("revised_informal_knowledge_dag_nodes", []),
        )
    )
    revised_formal_nodes = _dict_list(
        raw_route.get(
            "revised_formal_realization_dag_nodes",
            metadata.get(
                "revised_formal_realization_dag_nodes",
                raw_route.get(
                    "revised_lean_realization_dag_nodes",
                    metadata.get("revised_lean_realization_dag_nodes", []),
                ),
            ),
        )
    )
    revised_lean_nodes = _dict_list(
        raw_route.get(
            "revised_lean_realization_dag_nodes",
            metadata.get(
                "revised_lean_realization_dag_nodes",
                revised_formal_nodes
                if _is_lean_target_prover(target_prover_family)
                else [],
            ),
        )
    )
    revised_alignment_edges = _dict_list(
        raw_route.get(
            "revised_route_alignment_edges",
            metadata.get("revised_route_alignment_edges", []),
        )
    )
    source_snippets = _dict_list(
        metadata.get("source_snippets", raw_route.get("source_snippets", []))
    )
    primitive_source_snippets = [
        {
            "primitive": str(primitive.get("primitive", "")),
            "source_snippets": _dict_list(primitive.get("source_snippets", [])),
        }
        for primitive in _raw_primitives(raw_route)
        if _dict_list(primitive.get("source_snippets", []))
    ]
    primitive_source_refs = [
        {
            "primitive": str(primitive.get("primitive", "")),
            "source_refs": _str_list(primitive.get("source_refs", [])),
        }
        for primitive in _raw_primitives(raw_route)
        if _str_list(primitive.get("source_refs", []))
    ]
    raw_candidate_target_prover_family = str(
        raw_route.get("target_prover_family", "")
        or metadata.get("target_prover_family", "")
        or target_prover_family
    ).strip()
    candidate_target_prover_family = (
        normalize_target_prover_family(raw_candidate_target_prover_family)
        or raw_candidate_target_prover_family
    )
    primitive_candidate_declaration_rows = [
        {
            "primitive": str(primitive.get("primitive", "")),
            "candidate_declaration_rows": list(
                _candidate_declaration_rows_for_primitive(
                    primitive,
                    target_prover_family=candidate_target_prover_family,
                )
            ),
        }
        for primitive in _raw_primitives(raw_route)
        if _candidate_declaration_rows_for_primitive(
            primitive,
            target_prover_family=candidate_target_prover_family,
        )
    ]
    cost_graph = _minimal_delta_and_or_cost_graph(raw_route)
    selected_cost_graph_option = _selected_cost_graph_option(cost_graph)
    realization_witness = _realization_coverage_witness(raw_route)
    quality_controls = _quality_controls_for_trace(raw_route, metadata)
    formal_declaration_hits, lean_declaration_hits = (
        _declaration_hits_for_standalone_trace(
            metadata,
            target_prover_family=target_prover_family,
        )
    )
    llm_generator_metadata = _dict_value(
        metadata.get("llm_route_planner_generator_metadata", {})
    )
    llm_model_tier_decision_evidence = _dict_value(
        metadata.get("llm_route_planner_model_tier_decision_evidence", {})
    )
    if not llm_model_tier_decision_evidence:
        llm_model_tier_decision_evidence = _dict_value(
            metadata.get("model_tier_decision_evidence", {})
        )
    llm_model_tier_route_signal_counts = _dict_value(
        llm_model_tier_decision_evidence.get("route_signal_counts", {})
    )
    llm_source_feedback_counts = _dict_value(
        llm_model_tier_decision_evidence.get("source_theorem_feedback_counts", {})
    )
    llm_sonnet_triggers = _str_list(
        llm_model_tier_decision_evidence.get("sonnet_triggers", [])
    )
    llm_seed_selection_rank = _int_value(
        metadata.get(
            "llm_route_planner_seed_selection_rank",
            raw_route.get("llm_route_planner_seed_selection_rank", 0),
        )
    )
    llm_seed_minimal_delta_route_cost = _float_or_none(
        metadata.get(
            "llm_route_planner_seed_minimal_delta_route_cost",
            raw_route.get("llm_route_planner_seed_minimal_delta_route_cost", None),
        )
    )
    llm_seed_minimal_delta_selected_route_option_id = str(
        metadata.get(
            "llm_route_planner_seed_minimal_delta_selected_route_option_id",
            raw_route.get(
                "llm_route_planner_seed_minimal_delta_selected_route_option_id",
                "",
            ),
        )
    )
    target_context_packet = _target_theorem_context_packet_for_trace(
        raw_route,
        metadata,
    )
    llm_target_context_packet = _dict_value(
        metadata.get("llm_route_planner_target_theorem_context_packet", {})
    )
    llm_target_context_summary = _dict_value(
        metadata.get(
            "llm_route_planner_target_context_summary",
            raw_route.get("llm_route_planner_target_context_summary", {}),
        )
    )
    llm_route_planning_brief = _dict_value(
        metadata.get(
            "llm_route_planner_route_planning_brief",
            raw_route.get("llm_route_planner_route_planning_brief", {}),
        )
    )
    llm_route_option_selection_brief = _dict_value(
        metadata.get(
            "llm_route_planner_route_option_selection_brief",
            raw_route.get("llm_route_planner_route_option_selection_brief", {}),
        )
    )
    llm_route_option_selected_route_option_id = str(
        metadata.get(
            "llm_route_planner_route_option_selected_route_option_id",
            raw_route.get(
                "llm_route_planner_route_option_selected_route_option_id",
                llm_route_option_selection_brief.get(
                    "lower_bound_selected_route_option_id",
                    "",
                ),
            ),
        )
    )
    llm_primitive_evidence_matrix_witness = _dict_value(
        metadata.get(
            "llm_route_planner_primitive_evidence_matrix_witness",
            raw_route.get(
                "llm_route_planner_primitive_evidence_matrix_witness",
                {},
            ),
        )
    )
    llm_matrix_unaccounted_primitives = _str_list(
        llm_primitive_evidence_matrix_witness.get("matrix_unaccounted_primitives", [])
    )
    llm_matrix_selected_without_row = _str_list(
        llm_primitive_evidence_matrix_witness.get(
            "selected_primitives_without_matrix_row",
            [],
        )
    )
    llm_matrix_source_backed_missing = _str_list(
        llm_primitive_evidence_matrix_witness.get(
            "source_backed_matrix_primitives_missing_response_source_snippet",
            [],
        )
    )
    llm_matrix_formal_missing_reuse = _str_list(
        llm_primitive_evidence_matrix_witness.get(
            "formal_supported_matrix_primitives_missing_reuse",
            [],
        )
    )
    llm_matrix_delta_missing_accounting = _str_list(
        llm_primitive_evidence_matrix_witness.get(
            "delta_needed_matrix_primitives_missing_accounting",
            [],
        )
    )
    llm_matrix_repair_obligation_count = (
        len(llm_matrix_unaccounted_primitives)
        + len(llm_matrix_selected_without_row)
        + len(llm_matrix_source_backed_missing)
        + len(llm_matrix_formal_missing_reuse)
        + len(llm_matrix_delta_missing_accounting)
    )
    llm_route_adoption_preconditions = _dict_value(
        metadata.get(
            "llm_route_planner_route_adoption_preconditions",
            raw_route.get("llm_route_planner_route_adoption_preconditions", {}),
        )
    )
    raw_trace_target_prover_family = str(
        raw_route.get("target_prover_family", "")
        or metadata.get("target_prover_family", "")
        or target_prover_family
    ).strip()
    trace_target_prover_family = (
        normalize_target_prover_family(raw_trace_target_prover_family)
        or raw_trace_target_prover_family
    )
    target_context_target = str(
        target_context_packet.get("target_prover_family", "")
    ).strip()
    target_context_statement = str(
        target_context_packet.get("theorem_statement", "")
    ).strip()
    route_theorem_statement = str(raw_route.get("theorem_statement", "")).strip()
    return {
        "trace_kind": "standalone_input_route_trace",
        "source_route_id": route_id,
        "route_index": route_index,
        "target_prover_family": trace_target_prover_family,
        "has_replan_metadata": bool(metadata),
        "replan_metadata": dict(metadata),
        "target_theorem_context_packet": dict(target_context_packet),
        "has_target_theorem_context_packet": bool(target_context_packet),
        "has_llm_route_planner_target_theorem_context_packet": bool(
            llm_target_context_packet
        ),
        "llm_route_planner_target_context_summary": dict(
            llm_target_context_summary
        ),
        "has_llm_route_planner_target_context_summary": bool(
            llm_target_context_summary
        ),
        "llm_route_planner_route_planning_brief": dict(llm_route_planning_brief),
        "has_llm_route_planner_route_planning_brief": bool(
            llm_route_planning_brief
        ),
        "llm_route_planner_route_option_selection_brief": dict(
            llm_route_option_selection_brief
        ),
        "has_llm_route_planner_route_option_selection_brief": bool(
            llm_route_option_selection_brief
        ),
        "llm_route_planner_primitive_evidence_matrix_witness": dict(
            llm_primitive_evidence_matrix_witness
        ),
        "has_llm_route_planner_primitive_evidence_matrix_witness": bool(
            llm_primitive_evidence_matrix_witness
        ),
        "llm_route_planner_primitive_evidence_matrix_accounting_complete": bool(
            llm_primitive_evidence_matrix_witness.get(
                "matrix_accounting_complete",
                False,
            )
        ),
        "llm_route_planner_primitive_evidence_matrix_repair_obligation_count": (
            llm_matrix_repair_obligation_count
        ),
        "llm_route_planner_primitive_evidence_matrix_unaccounted_primitive_count": (
            len(llm_matrix_unaccounted_primitives)
        ),
        "llm_route_planner_primitive_evidence_matrix_selected_without_matrix_row_count": (
            len(llm_matrix_selected_without_row)
        ),
        "llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippet_count": (
            len(llm_matrix_source_backed_missing)
        ),
        "llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse_count": (
            len(llm_matrix_formal_missing_reuse)
        ),
        "llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting_count": (
            len(llm_matrix_delta_missing_accounting)
        ),
        "llm_route_planner_route_adoption_preconditions": dict(
            llm_route_adoption_preconditions
        ),
        "has_llm_route_planner_route_adoption_preconditions": bool(
            llm_route_adoption_preconditions
        ),
        "llm_route_adoption_precondition_blocker_count": len(
            _str_tuple(
                llm_route_adoption_preconditions.get(
                    "known_pre_response_blockers",
                    [],
                )
            )
        ),
        "llm_route_adoption_precondition_required_response_field_count": len(
            _str_tuple(
                llm_route_adoption_preconditions.get(
                    "response_required_fields",
                    [],
                )
            )
        ),
        "llm_route_adoption_precondition_target_primitive_count": len(
            _str_tuple(
                llm_route_adoption_preconditions.get(
                    "target_primitives",
                    [],
                )
            )
        ),
        "llm_route_planning_brief_focus_count": len(
            _dict_list(llm_route_planning_brief.get("planner_focus", []))
        ),
        "llm_route_planning_brief_evidence_gap_count": len(
            _dict_list(llm_route_planning_brief.get("evidence_gaps", []))
        ),
        "llm_route_option_selection_brief_candidate_count": int(
            llm_route_option_selection_brief.get(
                "n_candidate_route_options",
                0,
            )
            or 0
        ),
        "llm_route_option_selection_brief_lower_bound_selected_route_option_id": str(
            llm_route_option_selection_brief.get(
                "lower_bound_selected_route_option_id",
                "",
            )
        ),
        "llm_route_planner_route_option_selected_route_option_id": (
            llm_route_option_selected_route_option_id
        ),
        "target_theorem_context_packet_kind": str(
            target_context_packet.get("context_packet_kind", "")
        ),
        "target_theorem_context_route_id": str(
            target_context_packet.get("route_id", "")
        ),
        "target_theorem_context_target_prover_family": target_context_target,
        "target_theorem_context_theorem_statement": target_context_statement,
        "target_theorem_context_packet_target_mismatch": bool(
            target_context_target
            and trace_target_prover_family
            and _target_prover_key(target_context_target)
            != _target_prover_key(trace_target_prover_family)
        ),
        "target_theorem_context_route_statement_differs": bool(
            target_context_statement
            and route_theorem_statement
            and target_context_statement != route_theorem_statement
        ),
        "llm_route_planner_row_id": str(
            metadata.get("llm_route_planner_row_id", "")
        ),
        "llm_route_planner_request_id": str(
            metadata.get("llm_route_planner_request_id", "")
        ),
        "llm_route_planner_provider": str(
            metadata.get("llm_route_planner_provider", "")
        ),
        "llm_route_planner_model": str(metadata.get("llm_route_planner_model", "")),
        "llm_route_planner_model_tier": str(
            metadata.get("llm_route_planner_model_tier", "")
        ),
        "llm_route_planner_model_selection_rationale": str(
            metadata.get("llm_route_planner_model_selection_rationale", "")
        ),
        "llm_route_planner_model_tier_decision_evidence": (
            llm_model_tier_decision_evidence
        ),
        "llm_route_planner_model_tier_decision_basis": str(
            llm_model_tier_decision_evidence.get("decision_basis", "")
        ),
        "llm_route_planner_model_tier_decision_selection_mode": str(
            llm_model_tier_decision_evidence.get("selection_mode", "")
        ),
        "llm_route_planner_model_tier_decision_sonnet_triggers": (
            llm_sonnet_triggers
        ),
        "llm_route_planner_model_tier_decision_sonnet_trigger_count": len(
            llm_sonnet_triggers
        ),
        "llm_route_planner_source_feedback_row_count": _int_value(
            llm_source_feedback_counts.get(
                "total_count",
                llm_model_tier_route_signal_counts.get(
                    "source_theorem_feedback_row_count",
                    0,
                ),
            )
        ),
        "llm_route_planner_source_feedback_unverified_semantic_primitive_row_count": (
            _int_value(
                llm_source_feedback_counts.get(
                    "unverified_semantic_primitive_row_count",
                    llm_model_tier_route_signal_counts.get(
                        "source_theorem_unverified_semantic_primitive_row_count",
                        0,
                    ),
                )
            )
        ),
        "llm_route_planner_source_feedback_proof_body_execution_failure_count": (
            _int_value(
                llm_source_feedback_counts.get(
                    "proof_body_execution_failure_count",
                    llm_model_tier_route_signal_counts.get(
                        "source_theorem_proof_body_execution_failure_count",
                        0,
                    ),
                )
            )
        ),
        "llm_route_planner_source_feedback_formal_environment_blocker_count": (
            _int_value(
                llm_source_feedback_counts.get(
                    "formal_environment_blocker_count",
                    llm_model_tier_route_signal_counts.get(
                        "source_theorem_formal_environment_blocker_count",
                        0,
                    ),
                )
            )
        ),
        "llm_route_planner_interactive_formal_attempt_queue_row_count": (
            _int_value(
                llm_model_tier_route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_row_count",
                    0,
                )
            )
        ),
        "llm_route_planner_interactive_formal_attempt_queue_item_count": (
            _int_value(
                llm_model_tier_route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_item_count",
                    0,
                )
            )
        ),
        "llm_route_planner_interactive_formal_attempt_queue_ready_item_count": (
            _int_value(
                llm_model_tier_route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_ready_item_count",
                    0,
                )
            )
        ),
        "llm_route_planner_interactive_formal_attempt_queue_blocked_item_count": (
            _int_value(
                llm_model_tier_route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_blocked_item_count",
                    0,
                )
            )
        ),
        "llm_route_planner_interactive_formal_attempt_queue_execution_command_count": (
            _int_value(
                llm_model_tier_route_signal_counts.get(
                    "interactive_session_formal_attempt_queue_execution_command_count",
                    0,
                )
            )
        ),
        "llm_route_planner_acceptance_status": str(
            metadata.get("llm_route_planner_acceptance_status", "")
        ),
        "llm_route_planner_route_adoption_status": str(
            metadata.get("llm_route_planner_route_adoption_status", "")
        ),
        "llm_route_planner_route_adoption_blockers": _str_list(
            metadata.get("llm_route_planner_route_adoption_blockers", [])
        ),
        "llm_route_planner_seed_selected": _bool_value(
            metadata.get(
                "llm_route_planner_seed_selected",
                raw_route.get("llm_route_planner_seed_selected", False),
            )
        ),
        "llm_route_planner_seed_adoptable_for_standalone_replay": _bool_value(
            metadata.get(
                "llm_route_planner_seed_adoptable_for_standalone_replay",
                raw_route.get(
                    "llm_route_planner_seed_adoptable_for_standalone_replay",
                    False,
                ),
            )
        ),
        "llm_route_planner_seed_selection_rank": llm_seed_selection_rank,
        "llm_route_planner_seed_selection_reason": str(
            metadata.get(
                "llm_route_planner_seed_selection_reason",
                raw_route.get("llm_route_planner_seed_selection_reason", ""),
            )
        ),
        "llm_route_planner_seed_minimal_delta_route_cost": (
            llm_seed_minimal_delta_route_cost
        ),
        "llm_route_planner_seed_minimal_delta_selected_route_option_id": (
            llm_seed_minimal_delta_selected_route_option_id
        ),
        "llm_route_planner_generator_metadata": llm_generator_metadata,
        "llm_route_planner_generator_metadata_keys": _str_list(
            metadata.get("llm_route_planner_generator_metadata_keys", [])
        ),
        "llm_route_planner_has_generator_metadata": bool(llm_generator_metadata),
        "llm_route_planner_errors": _str_list(
            metadata.get("llm_route_planner_errors", [])
        ),
        "llm_route_planner_generation_errors": _str_list(
            metadata.get("llm_route_planner_generation_errors", [])
        ),
        "llm_route_planner_request_contract_blocked": bool(
            metadata.get("llm_route_planner_request_contract_blocked", False)
        ),
        "applied_proposal_ids": _str_list(metadata.get("applied_proposal_ids", [])),
        "applied_refinement_evidence_ids": _str_list(
            metadata.get("applied_refinement_evidence_ids", [])
        ),
        "applied_hook_kinds": _str_list(metadata.get("applied_hook_kinds", [])),
        "applied_resource_response_traces": _dict_list(
            metadata.get("applied_resource_response_traces", [])
        ),
        "applied_llm_route_planner_hook_traces": _dict_list(
            metadata.get("applied_llm_route_planner_hook_traces", [])
        ),
        "residual_goal_contexts": _dict_list(
            metadata.get(
                "residual_goal_contexts",
                raw_route.get("residual_goal_contexts", []),
            )
        ),
        "has_residual_goal_contexts": bool(
            _dict_list(
                metadata.get(
                    "residual_goal_contexts",
                    raw_route.get("residual_goal_contexts", []),
                )
            )
        ),
        "resource_response_awaiting_request_ids": _str_list(
            metadata.get("resource_response_awaiting_request_ids", [])
        ),
        "resource_response_rejected_request_ids": _str_list(
            metadata.get("resource_response_rejected_request_ids", [])
        ),
        "applied_prover_attempt_statuses": _str_list(
            metadata.get("applied_prover_attempt_statuses", [])
        ),
        "applied_prover_diagnostic_signatures": _str_list(
            metadata.get("applied_prover_diagnostic_signatures", [])
        ),
        "route_revision_reasons": _str_list(
            metadata.get("route_revision_reasons", [])
        ),
        "route_revision_summaries": _str_list(
            metadata.get("route_revision_summaries", [])
        ),
        "residual_goals": _str_list(metadata.get("residual_goals", [])),
        "source_refs": _str_list(
            metadata.get("source_refs", raw_route.get("source_refs", []))
        ),
        "source_snippets": source_snippets,
        "quality_controls": quality_controls,
        "has_quality_controls": bool(quality_controls),
        "quality_control_fields": sorted(quality_controls),
        "primitive_source_refs": primitive_source_refs,
        "primitive_source_snippets": primitive_source_snippets,
        "primitive_candidate_declaration_rows": primitive_candidate_declaration_rows,
        "has_source_snippets": bool(source_snippets or primitive_source_snippets),
        "formal_declaration_hits": formal_declaration_hits,
        "lean_declaration_hits": lean_declaration_hits,
        "revised_informal_knowledge_dag_nodes": revised_informal_nodes,
        "revised_formal_realization_dag_nodes": revised_formal_nodes,
        "revised_lean_realization_dag_nodes": revised_lean_nodes,
        "revised_route_alignment_edges": revised_alignment_edges,
        "minimal_delta_and_or_cost_graph": dict(cost_graph),
        "has_minimal_delta_and_or_cost_graph": bool(cost_graph),
        "minimal_delta_route_option_count": len(
            _dict_list(cost_graph.get("route_options", []))
        ),
        "minimal_delta_selected_route_option_id": str(
            selected_cost_graph_option.get("route_option_id", "")
        ),
        "minimal_delta_selected_route_cost": selected_cost_graph_option.get(
            "route_cost",
            None,
        ),
        "realization_coverage_witness": dict(realization_witness),
        "has_realization_coverage_witness": bool(realization_witness),
        "realization_coverage_complete": bool(
            realization_witness.get("realization_coverage_complete", False)
        ),
        "realization_selected_primitives_missing_formal_realization": _str_list(
            realization_witness.get(
                "selected_primitives_missing_formal_realization_node",
                [],
            )
        ),
        "realization_delta_primitives_missing_route_alignment": _str_list(
            realization_witness.get(
                "delta_primitives_missing_route_alignment_edge",
                [],
            )
        ),
        "alignment_edge_primitives": _str_list(
            metadata.get(
                "alignment_edge_primitives",
                [
                    edge.get("primitive", "")
                    for edge in revised_alignment_edges
                    if isinstance(edge, dict)
                ],
            )
        ),
        "proof_evidence_status": str(
            metadata.get(
                "proof_evidence_status",
                raw_route.get("proof_evidence_status", ""),
            )
        ),
    }


def _target_theorem_context_packet_for_trace(
    raw_route: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, object]:
    for source in (
        raw_route.get("target_theorem_context_packet", {}),
        metadata.get("target_theorem_context_packet", {}),
        metadata.get("llm_route_planner_target_theorem_context_packet", {}),
    ):
        packet = _dict_value(source)
        if packet:
            return dict(packet)
    return {}


def _quality_controls_for_trace(
    raw_route: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for source in (
        raw_route.get("quality_controls", {}),
        metadata.get("quality_controls", {}),
    ):
        if not isinstance(source, dict):
            continue
        for field_name in QUALITY_CONTROL_FIELDS:
            values = _str_list(source.get(field_name, []))
            if values:
                merged.setdefault(field_name, []).extend(values)
    return {
        field_name: _str_list(values)
        for field_name, values in merged.items()
        if _str_list(values)
    }


def _route_or_metadata_rows(
    raw_route: dict[str, Any],
    metadata: dict[str, Any],
    route_field_name: str,
    metadata_field_name: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(_dict_list(raw_route.get(route_field_name, [])))
    rows.extend(_dict_list(metadata.get(metadata_field_name, [])))
    return _dict_list(rows)


def _action_class_for_coverage(coverage_status: str) -> str:
    normalized = _normalize_status(coverage_status)
    if normalized in {"exact_exists", "already_exists", "existing_in_library"}:
        return "reuse_exact_proof_bank_obligation"
    if normalized in {"near_match_exists", "composition_exists", "compose_existing"}:
        return "compose_existing_bridge_chain"
    if normalized in {"wrapper_needed", "needs_wrapper", "different_formulation"}:
        return "add_minimal_wrapper"
    if normalized in {"assumption_interface_needed", "needs_assumption_interface"}:
        return "formalize_assumption_interface"
    if normalized in {"bridge_needed", "needs_bridge_lemma", "bridgeable"}:
        return "design_bridge_lemma"
    if normalized in {
        "source_port_needed",
        "definition_missing",
        "needs_literature",
        "paper_port_needed",
        "source_needed",
    }:
        return "port_external_source"
    if normalized in {
        "new_theory_needed",
        "theory_missing",
        "first_principles_needed",
        "not_in_library",
    }:
        return "design_from_first_principles"
    return "design_bridge_lemma"


def _default_cost(action_class: str, coverage_status: str) -> int:
    if action_class == "reuse_exact_proof_bank_obligation":
        return 1
    if action_class == "compose_existing_bridge_chain":
        return 2
    if action_class == "add_minimal_wrapper":
        return 3
    if action_class in {"design_bridge_lemma", "formalize_assumption_interface"}:
        return 5
    if action_class == "port_external_source":
        return 8
    if action_class == "design_from_first_principles":
        return 13
    return 7 if _coverage_unknown(coverage_status) else 5


def _minimal_delta_and_or_cost_graph(raw_route: dict[str, Any]) -> dict[str, Any]:
    metadata = raw_route.get("replan_metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    graph = raw_route.get(
        "minimal_delta_and_or_cost_graph",
        metadata.get("minimal_delta_and_or_cost_graph", {}),
    )
    if isinstance(graph, dict) and graph:
        return dict(graph)
    minimal_delta = metadata.get(
        "llm_route_planner_minimal_delta_plan",
        raw_route.get("minimal_delta_plan", {}),
    )
    if isinstance(minimal_delta, dict):
        graph = minimal_delta.get("and_or_cost_graph", {})
    return dict(graph) if isinstance(graph, dict) else {}


def _realization_coverage_witness(raw_route: dict[str, Any]) -> dict[str, Any]:
    metadata = raw_route.get("replan_metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    witness = raw_route.get(
        "realization_coverage_witness",
        metadata.get(
            "llm_route_planner_realization_coverage_witness",
            metadata.get("realization_coverage_witness", {}),
        ),
    )
    return dict(witness) if isinstance(witness, dict) else {}


def _selected_cost_graph_route_cost(raw_route: dict[str, Any]) -> int | None:
    selected = _selected_cost_graph_option(_minimal_delta_and_or_cost_graph(raw_route))
    cost = selected.get("route_cost", None)
    return int(cost) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None


def _selected_cost_graph_option(graph: dict[str, Any]) -> dict[str, object]:
    if not graph:
        return {}
    selected_id = str(graph.get("selected_route_option_id", "")).strip()
    options = _dict_list(graph.get("route_options", []))
    for option in options:
        if bool(option.get("selected", False)):
            return option
    for option in options:
        if selected_id and str(option.get("route_option_id", "")).strip() == selected_id:
            return option
    return {}


def _minimal_delta_primitive_costs(raw_route: dict[str, Any]) -> dict[str, int]:
    metadata = raw_route.get("replan_metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    minimal_delta = metadata.get(
        "llm_route_planner_minimal_delta_plan",
        raw_route.get("minimal_delta_plan", {}),
    )
    if not isinstance(minimal_delta, dict):
        return {}
    costs: dict[str, int] = {}
    for row in _dict_list(minimal_delta.get("primitive_costs", [])):
        primitive = _normalize_primitive_key(row.get("primitive", ""))
        total_cost = row.get("total_cost", None)
        if primitive and isinstance(total_cost, (int, float)) and not isinstance(total_cost, bool):
            costs[primitive] = int(total_cost)
    return costs


def _route_class(actions: list[dict[str, object]]) -> str:
    action_classes = {str(action.get("action_class", "")) for action in actions}
    if action_classes & {"port_external_source", "design_from_first_principles"}:
        return "requires_new_theory"
    if action_classes & {
        "add_minimal_wrapper",
        "design_bridge_lemma",
        "formalize_assumption_interface",
    }:
        return "bridge_or_wrapper"
    return "reuse_or_composition"


def _recommended_action(route_class: str) -> str:
    if route_class == "reuse_or_composition":
        return "try existing declarations and proof-bank composition first"
    if route_class == "bridge_or_wrapper":
        return "attempt wrappers and bridge lemmas bottom-up"
    return "collect source evidence and minimize new theory before proving"


def _source_trust_level(actions: list[dict[str, object]]) -> str:
    if any(action.get("candidate_declarations") for action in actions):
        return "local_candidate_declarations"
    if any(action.get("source_refs") for action in actions):
        return "source_backed_route"
    return "standalone_user_supplied"


def _blocker_count(actions: list[dict[str, object]]) -> int:
    return sum(len(action.get("blocked_reasons", []) or []) for action in actions)


def _next_step_for_action(action_class: str, primitive: str) -> str:
    if action_class == "reuse_exact_proof_bank_obligation":
        return f"reuse existing declaration or verified obligation for {primitive}"
    if action_class == "compose_existing_bridge_chain":
        return f"compose existing declarations to realize {primitive}"
    if action_class == "add_minimal_wrapper":
        return f"write a small wrapper statement for {primitive}"
    if action_class in {"design_bridge_lemma", "formalize_assumption_interface"}:
        return f"prove a focused bridge lemma or assumption interface for {primitive}"
    if action_class == "port_external_source":
        return f"attach source-backed statement and candidate port for {primitive}"
    return f"design the smallest new primitive needed for {primitive}"


def _all_primitives(
    payload: dict[str, Any],
    routes: list[dict[str, object]],
) -> tuple[str, ...]:
    primitives = set(_str_tuple(payload.get("background_primitives", [])))
    primitives.update(_str_tuple(payload.get("candidate_primitives", [])))
    primitives.update(_str_tuple(payload.get("excluded_primitives", [])))
    for route in routes:
        for action in route.get("actions", []):
            if isinstance(action, dict) and str(action.get("primitive", "")):
                primitives.add(str(action.get("primitive", "")))
    return tuple(sorted(primitives))


def _raw_routes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for field_name in ("routes", "targets", "theorem_routes"):
        rows = payload.get(field_name, [])
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _raw_primitives(route: dict[str, Any]) -> list[dict[str, Any]]:
    for field_name in ("primitives", "route_primitives", "required_primitives"):
        values = route.get(field_name, [])
        if isinstance(values, list):
            rows: list[dict[str, Any]] = []
            for value in values:
                if isinstance(value, dict):
                    rows.append(value)
                elif str(value):
                    rows.append({"primitive": str(value), "coverage_status": "unknown"})
            return rows
    return []


def _display_name(route: dict[str, Any]) -> str:
    for field_name in ("display_name", "target_theorem_id", "theorem_name", "name"):
        value = str(route.get(field_name, "")).strip()
        if value:
            return value
    return ""


def _legacy_lean_declaration_hit_input_errors(
    row: Mapping[str, Any],
    *,
    location: str,
    target_prover_family: str,
    target_prover_key: str,
) -> list[str]:
    if not target_prover_key or _is_lean_target_prover(target_prover_family):
        return []
    if not _nonempty_legacy_field_value(row.get("lean_declaration_hits")):
        return []
    return [
        (
            f"{location}.lean_declaration_hits is a Lean-only legacy alias; "
            "non-Lean standalone targets must use formal_declaration_hits "
            f"for target_prover_family {target_prover_family}"
        )
    ]


def _nonempty_legacy_field_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return any(_nonempty_legacy_field_value(item) for item in value)
    return bool(value)


def _legacy_lean_realization_node_input_errors(
    row: Mapping[str, Any],
    *,
    location: str,
    target_prover_family: str,
    target_prover_key: str,
) -> list[str]:
    if not target_prover_key or _is_lean_target_prover(target_prover_family):
        return []
    if not _nonempty_legacy_field_value(
        row.get("revised_lean_realization_dag_nodes")
    ):
        return []
    return [
        (
            f"{location}.revised_lean_realization_dag_nodes is a Lean-only "
            "legacy alias; non-Lean standalone targets must use "
            "revised_formal_realization_dag_nodes for target_prover_family "
            f"{target_prover_family}"
        )
    ]


def _declaration_hits_for_standalone_trace(
    metadata: Mapping[str, Any],
    *,
    target_prover_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    formal_hits = _dict_list(metadata.get("formal_declaration_hits", []))
    lean_hits = _dict_list(metadata.get("lean_declaration_hits", []))
    if _is_lean_target_prover(target_prover_family):
        return formal_hits or lean_hits, lean_hits or formal_hits
    return formal_hits, []


def _target_prover_family(payload: dict[str, Any]) -> str:
    value = str(payload.get("target_prover_family", "")).strip()
    if value:
        return normalize_target_prover_family(value) or value
    route_targets = _route_declared_target_prover_families(payload)
    if len({_target_prover_key(target) for target in route_targets}) == 1:
        return normalize_target_prover_family(route_targets[0]) or route_targets[0]
    return TARGET_PROVER_FAMILY


def _route_declared_target_prover_families(payload: dict[str, Any]) -> tuple[str, ...]:
    targets: list[str] = []
    for route in _raw_routes(payload):
        metadata = _dict_value(route.get("replan_metadata", {}))
        for value in (
            route.get("target_prover_family", ""),
            route.get("target_prover", ""),
            metadata.get("target_prover_family", ""),
            metadata.get("target_prover", ""),
        ):
            target = str(value or "").strip()
            if target:
                targets.append(target)
    compact: list[str] = []
    seen: set[str] = set()
    for target in targets:
        key = _target_prover_key(target)
        if not key or key in seen:
            continue
        seen.add(key)
        compact.append(target)
    return tuple(compact)


def _manifest_target_prover_family(
    rows: list[Any],
    *,
    fallback_target_prover_family: str,
) -> str:
    targets = sorted(
        {
            normalize_target_prover_family(
                getattr(row, "target_prover_family", "")
            )
            for row in rows
            if normalize_target_prover_family(
                getattr(row, "target_prover_family", "")
            )
        }
    )
    if len(targets) == 1:
        return targets[0]
    if len(targets) > 1:
        return "mixed:" + ",".join(targets)
    return fallback_target_prover_family or TARGET_PROVER_FAMILY


def _portable_row_with_formal_aliases(
    row: dict[str, Any],
    *,
    target_prover_family: str,
) -> dict[str, Any]:
    legacy_nodes = _dict_list(row.get("lean_realization_dag_nodes", []))
    formal_nodes = row.get("formal_realization_dag_nodes")
    row["formal_realization_dag_nodes"] = (
        _dict_list(formal_nodes)
        if isinstance(formal_nodes, (list, tuple))
        else legacy_nodes
    )
    legacy_edges = _dict_list(row.get("lean_realization_dag_edges", []))
    formal_edges = row.get("formal_realization_dag_edges")
    row["formal_realization_dag_edges"] = (
        _dict_list(formal_edges)
        if isinstance(formal_edges, (list, tuple))
        else legacy_edges
    )
    if _is_lean_target_prover(target_prover_family):
        row["lean_realization_dag_nodes"] = legacy_nodes or list(
            row["formal_realization_dag_nodes"]
        )
        row["lean_realization_dag_edges"] = legacy_edges or list(
            row["formal_realization_dag_edges"]
        )
    else:
        row["lean_realization_dag_nodes"] = []
        row["lean_realization_dag_edges"] = []
    return row


def _is_lean_target_prover(target_prover_family: str) -> bool:
    key = _normalize_status(target_prover_family)
    return key in {"lean", "lean4", "lean_4"} or key.startswith(
        ("lean4_", "lean_4_", "lean_")
    )


def _target_prover_key(value: object) -> str:
    key = normalize_target_prover_family(value)
    if key:
        return key
    key = _normalize_status(str(value or ""))
    aliases = {
        "coq": "rocq",
        "coq8": "rocq",
        "rocq_coq": "rocq",
        "coq_rocq": "rocq",
        "lean": "lean4",
        "lean_4": "lean4",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(key, key)


def _mixed_target_prover_keys(value: object) -> set[str]:
    target = str(value or "").strip()
    if not target.lower().startswith("mixed:"):
        return set()
    return {
        key
        for key in (
            _target_prover_key(part)
            for part in target.split(":", 1)[1].split(",")
        )
        if key
    }


def _candidate_declaration_row_input_errors(
    value: Any,
    *,
    location: str,
    expected_target: str,
    expected_target_key: str,
) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        return [f"{location} must be an array of objects"]
    errors: list[str] = []
    for row_index, item in enumerate(value):
        row_location = f"{location}[{row_index}]"
        if not isinstance(item, dict):
            errors.append(f"{row_location} must be an object")
            continue
        declaration = _candidate_declaration_row_declaration(item)
        if not declaration:
            errors.append(f"{row_location}.declaration missing")
        row_target = str(
            item.get("target_prover_family", "") or item.get("target_prover", "")
        ).strip()
        row_target_key = _target_prover_key(row_target)
        if expected_target_key and row_target_key and row_target_key != expected_target_key:
            errors.append(
                f"{row_location}.target_prover_family {row_target} does not match "
                f"target_prover_family {expected_target}"
            )
    return errors


def _normalize_status(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_primitive_key(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _coverage_unknown(value: str) -> bool:
    return _normalize_status(value) in {"", "unknown", "unclear", "needs_search"}


def _candidate_declaration_rows_for_primitive(
    primitive: dict[str, Any],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for item in _dict_list(primitive.get("candidate_declaration_rows", [])):
        declaration = _candidate_declaration_row_declaration(item)
        if not declaration:
            continue
        row: dict[str, object] = {
            "declaration": declaration,
            "target_prover_family": str(
                item.get("target_prover_family", "")
                or item.get("target_prover", "")
                or target_prover_family
            ).strip(),
            "source_field": str(
                item.get("source_field", "") or "candidate_declaration_rows"
            ).strip(),
        }
        for field_name in (
            "source_fields",
            "target_primitives",
            "supported_target_primitives",
            "unsupported_target_primitives",
            "source_refs",
            "matched_terms",
        ):
            values = _candidate_declaration_row_list_field_values(
                field_name,
                item.get(field_name, []),
            )
            if values:
                row[field_name] = list(values)
        rows.append(row)
    if not rows:
        rows.extend(
            {
                "declaration": declaration,
                "target_prover_family": target_prover_family,
                "source_field": "candidate_declarations",
            }
            for declaration in _str_tuple(primitive.get("candidate_declarations", []))
        )
    compact_by_key: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        target = str(row.get("target_prover_family", "")).strip()
        source_field = str(row.get("source_field", "")).strip() or "candidate_declarations"
        key = (
            _normalize_primitive_key(declaration),
            _normalize_primitive_key(target),
            _normalize_primitive_key(source_field),
        )
        if not declaration:
            continue
        if key not in compact_by_key:
            compact_by_key[key] = {
                **dict(row),
                "declaration": declaration,
                "target_prover_family": target,
                "source_field": source_field,
            }
            continue
        existing = compact_by_key[key]
        for field_name in (
            "source_fields",
            "target_primitives",
            "supported_target_primitives",
            "unsupported_target_primitives",
            "source_refs",
            "matched_terms",
        ):
            merged = tuple(
                dict.fromkeys(
                    [
                        *_str_tuple(existing.get(field_name, [])),
                        *_str_tuple(row.get(field_name, [])),
                    ]
                )
            )
            if merged:
                existing[field_name] = list(merged)
    return tuple(compact_by_key.values())


def _candidate_declaration_row_list_field_values(
    field_name: str,
    value: Any,
) -> tuple[str, ...]:
    if field_name in {
        "target_primitives",
        "supported_target_primitives",
        "unsupported_target_primitives",
    }:
        return tuple(
            dict.fromkeys(
                primitive
                for primitive in (
                    _normalize_primitive_key(item) for item in _str_tuple(value)
                )
                if primitive
            )
        )
    return _str_tuple(value)


def _candidate_declaration_row_declaration(item: dict[str, object]) -> str:
    return str(
        item.get("declaration")
        or item.get("declaration_name")
        or item.get("candidate_declaration")
        or item.get("lean_declaration")
        or item.get("name")
        or item.get("full_name")
        or ""
    ).strip()


def _candidate_declarations_for_primitive(
    primitive: dict[str, Any],
    *,
    candidate_declaration_rows: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            [
                *_str_tuple(primitive.get("candidate_declarations", [])),
                *[
                    str(row.get("declaration", "")).strip()
                    for row in candidate_declaration_rows
                    if str(row.get("declaration", "")).strip()
                ],
            ]
        )
    )


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(str(value) for value in values if str(value))


def _str_list(values: Any) -> list[str]:
    return list(_str_tuple(values))


def _dict_list(values: Any) -> list[dict[str, object]]:
    if not isinstance(values, (list, tuple, set)):
        return []
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            continue
        key = stable_hash(value)
        if key in seen:
            continue
        seen.add(key)
        rows.append(dict(value))
    return rows


def _dict_value(value: Any) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
