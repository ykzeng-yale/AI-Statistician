from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    OPTIMIZATION_OBJECTIVES,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
    PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS,
    evaluation_protocol,
    interactive_route_synthesis_contract,
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
from .goal_conditioned_minimal_formalization_plan import (
    GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION,
    TARGET_PROVER_FAMILY,
    _graph_count,
    _markdown_report,
    _plan_row,
)


FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION = 1
FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-standalone-input:1"
)
FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT = (
    "formalization_gap_planner_standalone_input"
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
        "created_at": datetime.now(timezone.utc).isoformat(),
        "standalone_input_schema_id": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
        "standalone_input_path": str(input_json),
        "standalone_input_component": str(input_payload.get("component_name", "")),
        "n_theorem_routes": len(routes),
        "n_goal_plans": len(rows),
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
    payload_target = str(payload.get("target_prover_family", "")).strip()
    payload_target_key = _target_prover_key(payload_target)
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
    if not payload_target_key and not route_target_keys:
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
            and len(route_target_keys) > 1
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
        if route_target_key and metadata_target_key and route_target_key != metadata_target_key:
            errors.append(
                f"routes[{idx}].replan_metadata.target_prover_family "
                f"{metadata_target} does not match routes[{idx}].target_prover_family "
                f"{route_target}"
            )
        effective_target = route_target or metadata_target or payload_target
        effective_target_key = (
            route_target_key or metadata_target_key or payload_target_key
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


def standalone_input_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    candidate_declaration_rows = {
        "type": "array",
        "items": {"$ref": "#/$defs/candidate_declaration_row"},
    }
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
                    "route_class": {"type": "string"},
                    "recommended_action": {"type": "string"},
                    "source_refs": string_array,
                    "source_snippets": object_array,
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
                    "resource_response_awaiting_request_ids": string_array,
                    "resource_response_rejected_request_ids": string_array,
                    "applied_prover_attempt_statuses": string_array,
                    "applied_prover_diagnostic_signatures": string_array,
                    "route_revision_reasons": string_array,
                    "route_revision_summaries": string_array,
                    "residual_goals": string_array,
                    "source_refs": string_array,
                    "source_snippets": object_array,
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
        route_target_prover_family = str(
            raw_route.get("target_prover_family", "")
            or raw_route.get("target_prover", "")
            or metadata.get("target_prover_family", "")
            or metadata.get("target_prover", "")
            or target_prover_family
        ).strip()
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
        selected_primitives = [
            str(action.get("primitive", "")) for action in actions if action.get("primitive")
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
    primitive_candidate_declaration_rows = [
        {
            "primitive": str(primitive.get("primitive", "")),
            "candidate_declaration_rows": list(
                _candidate_declaration_rows_for_primitive(
                    primitive,
                    target_prover_family=str(
                        raw_route.get("target_prover_family", "")
                        or metadata.get("target_prover_family", "")
                        or target_prover_family
                    ),
                )
            ),
        }
        for primitive in _raw_primitives(raw_route)
        if _candidate_declaration_rows_for_primitive(
            primitive,
            target_prover_family=str(
                raw_route.get("target_prover_family", "")
                or metadata.get("target_prover_family", "")
                or target_prover_family
            ),
        )
    ]
    cost_graph = _minimal_delta_and_or_cost_graph(raw_route)
    selected_cost_graph_option = _selected_cost_graph_option(cost_graph)
    realization_witness = _realization_coverage_witness(raw_route)
    llm_generator_metadata = _dict_value(
        metadata.get("llm_route_planner_generator_metadata", {})
    )
    return {
        "trace_kind": "standalone_input_route_trace",
        "source_route_id": route_id,
        "route_index": route_index,
        "target_prover_family": str(
            raw_route.get("target_prover_family", "")
            or metadata.get("target_prover_family", "")
            or target_prover_family
        ).strip(),
        "has_replan_metadata": bool(metadata),
        "replan_metadata": dict(metadata),
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
        "llm_route_planner_acceptance_status": str(
            metadata.get("llm_route_planner_acceptance_status", "")
        ),
        "llm_route_planner_route_adoption_status": str(
            metadata.get("llm_route_planner_route_adoption_status", "")
        ),
        "llm_route_planner_route_adoption_blockers": _str_list(
            metadata.get("llm_route_planner_route_adoption_blockers", [])
        ),
        "llm_route_planner_generator_metadata": llm_generator_metadata,
        "llm_route_planner_generator_metadata_keys": _str_list(
            metadata.get("llm_route_planner_generator_metadata_keys", [])
        ),
        "llm_route_planner_has_generator_metadata": bool(llm_generator_metadata),
        "applied_proposal_ids": _str_list(metadata.get("applied_proposal_ids", [])),
        "applied_refinement_evidence_ids": _str_list(
            metadata.get("applied_refinement_evidence_ids", [])
        ),
        "applied_hook_kinds": _str_list(metadata.get("applied_hook_kinds", [])),
        "applied_resource_response_traces": _dict_list(
            metadata.get("applied_resource_response_traces", [])
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
        "primitive_source_refs": primitive_source_refs,
        "primitive_source_snippets": primitive_source_snippets,
        "primitive_candidate_declaration_rows": primitive_candidate_declaration_rows,
        "has_source_snippets": bool(source_snippets or primitive_source_snippets),
        "formal_declaration_hits": _dict_list(
            metadata.get(
                "formal_declaration_hits",
                metadata.get("lean_declaration_hits", []),
            )
        ),
        "lean_declaration_hits": _dict_list(
            metadata.get(
                "lean_declaration_hits",
                metadata.get("formal_declaration_hits", []),
            )
        ),
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


def _target_prover_family(payload: dict[str, Any]) -> str:
    value = str(payload.get("target_prover_family", "")).strip()
    if value:
        return value
    route_targets = _route_declared_target_prover_families(payload)
    if len({_target_prover_key(target) for target in route_targets}) == 1:
        return route_targets[0]
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
            str(getattr(row, "target_prover_family", "")).strip()
            for row in rows
            if str(getattr(row, "target_prover_family", "")).strip()
        }
    )
    if len(targets) == 1:
        return targets[0]
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
        rows.append(
            {
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
        )
    if not rows:
        rows.extend(
            {
                "declaration": declaration,
                "target_prover_family": target_prover_family,
                "source_field": "candidate_declarations",
            }
            for declaration in _str_tuple(primitive.get("candidate_declarations", []))
        )
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        target = str(row.get("target_prover_family", "")).strip()
        key = (_normalize_primitive_key(declaration), _normalize_primitive_key(target))
        if not declaration or key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "declaration": declaration,
                "target_prover_family": target,
                "source_field": str(row.get("source_field", "")).strip()
                or "candidate_declarations",
            }
        )
    return tuple(compact)


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
