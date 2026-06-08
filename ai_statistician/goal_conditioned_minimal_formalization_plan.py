from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    portable_gap_plan_row_json_schema,
    route_alignment_edge_json_schema,
    validate_portable_gap_plan_row,
    validate_route_alignment_edge,
    write_portable_gap_plan_schema,
    write_portable_gap_plan_row_schema,
    write_route_alignment_edge_schema,
)


GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION = 3
PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION = 1
PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID = (
    "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1"
)
LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME = "library_aware_formalization_gap_planner"
TARGET_PROVER_FAMILY = "lean4_adapter_with_portable_gap_schema"
FORMALIZATION_DELTA_OBJECTIVE = (
    "Given a target theorem T and a current formal library snapshot L, find a "
    "small additional formalization Delta of existing reuse, wrappers, bridge "
    "lemmas, source ports, or new primitives such that L + Delta is a plausible "
    "route to a kernel-checked proof of T."
)
OPTIMIZATION_OBJECTIVES = (
    "minimize_new_declarations",
    "minimize_import_cone",
    "minimize_dependency_depth",
    "minimize_typeclass_and_statement_shape_risk",
    "maximize_existing_verified_library_reuse",
    "avoid_field_wide_formalization_not_needed_for_this_goal",
)
PROOF_EVIDENCE_STATUS = "GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Goal-conditioned minimal formalization plans are route-selection and "
    "cost-planning artifacts, not theorem proof evidence. They identify a small "
    "additional formalization cut for a target theorem, but only target-prover "
    "kernel verification can prove the target."
)


@dataclass(frozen=True)
class GoalConditionedMinimalFormalizationPlanRow:
    schema_version: int
    goal_plan_id: str
    route_id: str
    formal_verifier_queue_item_id: str
    task_id: str
    question_id: str
    problem_class: str
    theorem_goal_id: str
    display_name: str
    theorem_skeleton: str
    theorem_statement: str
    planner_component: str
    target_prover_family: str
    library_snapshot_ref: str
    formalization_delta_objective: str
    route_class: str
    pareto_profile: str
    optimization_objectives: tuple[str, ...]
    recommended_action: str
    best_route_cost: int
    goal_conditioned_cost: int
    route_cost_breakdown: dict[str, object]
    route_efficiency_score: int
    dependency_graph_depth: int
    import_cone_size: int
    selected_primitives: tuple[str, ...]
    existing_reuse_nodes: tuple[dict[str, object], ...]
    wrapper_nodes: tuple[dict[str, object], ...]
    bridge_nodes: tuple[dict[str, object], ...]
    source_discovery_nodes: tuple[dict[str, object], ...]
    first_principles_nodes: tuple[dict[str, object], ...]
    minimal_additional_formalization_nodes: tuple[dict[str, object], ...]
    minimal_cut_summary: dict[str, object]
    route_dag_contract: dict[str, object]
    and_or_plan: dict[str, object]
    and_or_plan_nodes: tuple[dict[str, object], ...]
    and_or_plan_edges: tuple[dict[str, object], ...]
    informal_knowledge_dag: dict[str, object]
    informal_knowledge_dag_nodes: tuple[dict[str, object], ...]
    informal_knowledge_dag_edges: tuple[dict[str, object], ...]
    lean_realization_dag: dict[str, object]
    lean_realization_dag_nodes: tuple[dict[str, object], ...]
    lean_realization_dag_edges: tuple[dict[str, object], ...]
    formal_realization_dag_nodes: tuple[dict[str, object], ...]
    formal_realization_dag_edges: tuple[dict[str, object], ...]
    route_alignment_edges: tuple[dict[str, object], ...]
    standalone_input_trace: dict[str, object]
    route_revision_triggers: tuple[dict[str, object], ...]
    interactive_refinement_hooks: tuple[dict[str, object], ...]
    portable_work_packets: tuple[dict[str, object], ...]
    minimal_delta_summary: dict[str, object]
    portable_work_packet_contract: dict[str, object]
    do_not_formalize_now: tuple[str, ...]
    blocked_only_by: tuple[str, ...]
    next_work_packets: tuple[dict[str, object], ...]
    route_summary: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_goal_conditioned_minimal_formalization_plan(
    formalization_delta_plan_dir: Path,
    formal_verifier_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    max_routes: int = 20,
) -> dict[str, object]:
    """Choose low-cost theorem-specific formalization routes.

    This planner answers a narrow efficiency question: for each theorem route,
    which exact wrappers, bridge lemmas, source-discovery items, or new
    primitive obligations should be added now, and which unrelated primitives
    should not be formalized for this target.
    """

    errors: list[str] = []
    delta_manifest_path = formalization_delta_plan_dir / "formalization_delta_plan_manifest.json"
    queue_manifest_path = formal_verifier_queue_dir / "formal_verifier_queue_manifest.json"
    delta_payload = _read_json(delta_manifest_path, errors)
    queue_payload = _read_json(queue_manifest_path, errors)
    routes = [
        row
        for row in delta_payload.get("theorem_formalization_routes", [])
        if isinstance(row, dict)
    ]
    queue_rows = [
        row for row in queue_payload.get("rows", []) if isinstance(row, dict)
    ]
    queue_by_route = {
        str(row.get("route_id", "")): row for row in queue_rows if row.get("route_id")
    }
    source_target_prover_family = _source_target_prover_family(
        delta_payload,
        queue_payload,
    )
    all_primitives = tuple(
        sorted(
            {
                str(row.get("primitive", ""))
                for row in delta_payload.get("rows", [])
                if isinstance(row, dict) and str(row.get("primitive", ""))
            }
        )
    )
    raw_rows = [
        _plan_row(
            route,
            queue_by_route.get(str(route.get("route_id", "")), {}),
            all_primitives,
            library_snapshot_ref=_library_snapshot_ref(
                formalization_delta_plan_dir,
                formal_verifier_queue_dir,
            ),
            source_target_prover_family=source_target_prover_family,
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
    by_target = Counter(
        str(row.target_prover_family or "").strip() or "missing" for row in rows
    )
    target_prover_family = _manifest_target_prover_family(
        rows,
        source_target_prover_family=source_target_prover_family,
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
    row_dicts = [asdict(row) for row in rows]
    goal_plan_row_schema = portable_gap_plan_row_json_schema()
    goal_plan_row_schema_errors = [
        validate_portable_gap_plan_row(
            row_dict,
            goal_plan_row_schema,
            library_snapshot_ref=_library_snapshot_ref(
                formalization_delta_plan_dir,
                formal_verifier_queue_dir,
            ),
        )
        for row_dict in row_dicts
    ]
    n_goal_plan_row_schema_valid = sum(
        1 for row_errors in goal_plan_row_schema_errors if not row_errors
    )
    n_goal_plan_row_schema_invalid = (
        len(goal_plan_row_schema_errors) - n_goal_plan_row_schema_valid
    )
    payload: dict[str, object] = {
        "schema_version": GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION,
        "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "portable_schema_version": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
        "component_name": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        "target_prover_family": target_prover_family,
        "n_target_prover_families": sum(
            1 for target in by_target if target != "missing"
        ),
        "by_target_prover_family": dict(sorted(by_target.items())),
        "library_snapshot_ref": _library_snapshot_ref(
            formalization_delta_plan_dir,
            formal_verifier_queue_dir,
        ),
        "formalization_delta_objective": FORMALIZATION_DELTA_OBJECTIVE,
        "optimization_objectives": list(OPTIMIZATION_OBJECTIVES),
        "planner_contract": _planner_contract(
            _library_snapshot_ref(formalization_delta_plan_dir, formal_verifier_queue_dir)
        ),
        "interactive_route_synthesis_contract": _interactive_route_synthesis_contract(),
        "evaluation_protocol": _evaluation_protocol(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formalization_delta_plan_dir": str(formalization_delta_plan_dir),
        "formalization_delta_plan_manifest": str(delta_manifest_path),
        "formal_verifier_queue_dir": str(formal_verifier_queue_dir),
        "formal_verifier_queue_manifest": str(queue_manifest_path),
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
            len(row.lean_realization_dag_nodes) for row in rows
        ),
        "n_lean_realization_dag_edges": sum(
            len(row.lean_realization_dag_edges) for row in rows
        ),
        "n_formal_realization_dag_nodes": sum(
            len(row.formal_realization_dag_nodes) for row in rows
        ),
        "n_formal_realization_dag_edges": sum(
            len(row.formal_realization_dag_edges) for row in rows
        ),
        "n_route_alignment_edges": sum(len(row.route_alignment_edges) for row in rows),
        "n_route_alignment_edge_schema_valid": n_route_alignment_edge_schema_valid,
        "n_route_alignment_edge_schema_invalid": n_route_alignment_edge_schema_invalid,
        "n_goal_plan_row_schema_valid": n_goal_plan_row_schema_valid,
        "n_goal_plan_row_schema_invalid": n_goal_plan_row_schema_invalid,
        "n_route_revision_triggers": sum(len(row.route_revision_triggers) for row in rows),
        "n_portable_work_packets": sum(len(row.portable_work_packets) for row in rows),
        "n_do_not_formalize_hints": sum(len(row.do_not_formalize_now) for row in rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
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
            "minimal route cost is heuristic and goal-conditioned; it is not proof evidence",
            "do_not_formalize_now is a prioritization hint, not a semantic impossibility claim",
            "target-prover kernel verification remains the only proof gate",
        ],
    }
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
        bool(payload["all_ok"])
        and n_route_alignment_edge_schema_invalid == 0
        and n_goal_plan_row_schema_invalid == 0
    )
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "goal_conditioned_minimal_formalization_plan.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
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
    return payload


def _plan_row(
    route: dict[str, Any],
    queue_row: dict[str, Any],
    all_primitives: tuple[str, ...],
    *,
    library_snapshot_ref: str,
    source_target_prover_family: str,
) -> GoalConditionedMinimalFormalizationPlanRow:
    errors: list[str] = []
    route_id = str(route.get("route_id", ""))
    task_id = str(route.get("task_id", ""))
    target_prover_family = _target_prover_family(
        route,
        queue_row,
        source_target_prover_family=source_target_prover_family,
    )
    actions = [
        action for action in route.get("actions", []) if isinstance(action, dict)
    ]
    selected_primitives = tuple(
        sorted({str(action.get("primitive", "")) for action in actions if action.get("primitive")})
    )
    if not route_id:
        errors.append("route_id missing")
    if not task_id:
        errors.append("task_id missing")
    if not actions:
        errors.append("route actions missing")
    if not selected_primitives:
        errors.append("selected_primitives missing")

    existing_reuse = _nodes_for_actions(
        actions,
        {
            "reuse_exact_proof_bank_obligation",
            "compose_existing_bridge_chain",
        },
    )
    wrappers = _nodes_for_actions(actions, {"add_minimal_wrapper"})
    bridges = _nodes_for_actions(
        actions,
        {"design_bridge_lemma", "formalize_assumption_interface"},
    )
    source_discovery = _nodes_for_actions(actions, {"port_external_source"})
    first_principles = _nodes_for_actions(actions, {"design_from_first_principles"})
    pareto_profile = _pareto_profile(
        existing_reuse=existing_reuse,
        wrappers=wrappers,
        bridges=bridges,
        source_discovery=source_discovery,
        first_principles=first_principles,
    )
    minimal_nodes = tuple(
        sorted(
            (
                *wrappers,
                *bridges,
                *source_discovery,
                *first_principles,
            ),
            key=lambda node: (
                int(node.get("cost", 0) or 0),
                str(node.get("primitive", "")),
            ),
        )
    )
    blockers = tuple(
        sorted(
            {
                str(reason)
                for action in actions
                for reason in action.get("blocked_reasons", []) or []
                if str(reason)
            }
        )
    )
    best_route_cost = int(route.get("total_estimated_cost", 0) or 0)
    import_cone_size = int(queue_row.get("import_cone_size", 0) or 0)
    dependency_depth = int(queue_row.get("dependency_graph_depth", 0) or 0)
    blocker_count = int(queue_row.get("blocker_count", len(blockers)) or 0)
    source_trust = str(queue_row.get("source_trust_level", ""))
    trust_credit = 3 if source_trust in {
        "proof_bank_and_local_candidates",
        "proof_bank_bridge_candidates",
        "local_candidate_declarations",
    } else 0
    import_cone_penalty = min(8, import_cone_size // 12)
    dependency_depth_penalty = min(6, dependency_depth)
    blocker_penalty = 2 * blocker_count
    goal_conditioned_cost = max(
        0,
        best_route_cost
        + import_cone_penalty
        + dependency_depth_penalty
        + blocker_penalty
        - trust_credit,
    )
    route_cost_breakdown: dict[str, object] = {
        "base_route_cost": best_route_cost,
        "import_cone_penalty": import_cone_penalty,
        "dependency_depth_penalty": dependency_depth_penalty,
        "blocker_penalty": blocker_penalty,
        "source_trust_credit": trust_credit,
        "final_goal_conditioned_cost": goal_conditioned_cost,
        "source_trust_level": source_trust,
        "cost_model_boundary": (
            "heuristic route-selection cost; not a target-prover proof or proof-risk certificate"
        ),
    }
    route_efficiency_score = max(0, 100 - goal_conditioned_cost + 2 * len(existing_reuse))
    do_not_formalize = tuple(
        primitive
        for primitive in all_primitives
        if primitive not in set(selected_primitives)
    )[:8]
    minimal_cut_summary = _minimal_cut_summary(
        display_name=str(route.get("display_name", "")),
        best_route_cost=best_route_cost,
        goal_conditioned_cost=goal_conditioned_cost,
        existing_reuse=existing_reuse,
        wrappers=wrappers,
        bridges=bridges,
        source_discovery=source_discovery,
        first_principles=first_principles,
        do_not_formalize=do_not_formalize,
        blockers=blockers,
    )
    route_dag_contract = _route_dag_contract(
        existing_reuse=existing_reuse,
        wrappers=wrappers,
        bridges=bridges,
        source_discovery=source_discovery,
        first_principles=first_principles,
        blockers=blockers,
    )
    next_packets = _next_packets(
        minimal_nodes or existing_reuse,
        target_prover_family=target_prover_family,
    )
    route_revision_triggers = _merge_dict_rows(
        _route_revision_triggers(
            existing_reuse=existing_reuse,
            wrappers=wrappers,
            bridges=bridges,
            source_discovery=source_discovery,
            first_principles=first_principles,
            blockers=blockers,
        ),
        _dict_tuple(route.get("route_revision_triggers", [])),
        key_fields=("trigger_kind", "condition", "next_action"),
    )
    portable_work_packets = _portable_work_packets(
        next_packets,
        target_prover_family=target_prover_family,
    )
    and_or_plan = _and_or_plan(
        route_id=route_id,
        display_name=str(route.get("display_name", "")),
        existing_reuse=existing_reuse,
        minimal_nodes=minimal_nodes,
        blockers=blockers,
    )
    informal_knowledge_dag = _informal_knowledge_dag(
        route_id=route_id,
        display_name=str(route.get("display_name", "")),
        selected_primitives=selected_primitives,
        route_source_refs=_str_tuple(route.get("source_refs", [])),
        informal_proof_steps=_str_tuple(route.get("informal_proof_steps", [])),
        source_refs_by_primitive=_source_refs_by_primitive(
            (*existing_reuse, *minimal_nodes)
        ),
        blockers=blockers,
    )
    formal_realization_dag = _lean_realization_dag(
        route_id=route_id,
        display_name=str(route.get("display_name", "")),
        existing_reuse=existing_reuse,
        minimal_nodes=minimal_nodes,
    )
    route_alignment_edges = _route_alignment_edges(
        informal_knowledge_dag=informal_knowledge_dag,
        lean_realization_dag=formal_realization_dag,
    )
    formal_realization_dag_nodes = tuple(formal_realization_dag.get("nodes", []))
    formal_realization_dag_edges = tuple(formal_realization_dag.get("edges", []))
    if _is_lean_target_prover(target_prover_family):
        lean_realization_dag = formal_realization_dag
        lean_realization_dag_nodes = formal_realization_dag_nodes
        lean_realization_dag_edges = formal_realization_dag_edges
    else:
        lean_realization_dag = {
            "nodes": [],
            "edges": [],
            "boundary": (
                "Lean realization DAG is a legacy alias omitted for non-Lean "
                "target prover families; use formal_realization_dag_nodes and "
                "formal_realization_dag_edges."
            ),
        }
        lean_realization_dag_nodes = tuple()
        lean_realization_dag_edges = tuple()
    interactive_refinement_hooks = _merge_dict_rows(
        _interactive_refinement_hooks(
            display_name=str(route.get("display_name", "")),
            theorem_skeleton=str(route.get("theorem_skeleton", "")),
            theorem_statement=str(route.get("theorem_statement", "")),
            selected_primitives=selected_primitives,
            source_discovery=source_discovery,
            first_principles=first_principles,
            blockers=blockers,
            route_revision_triggers=route_revision_triggers,
            target_prover_family=target_prover_family,
        ),
        _dict_tuple(route.get("interactive_refinement_hooks", [])),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )
    minimal_delta_summary = {
        **minimal_cut_summary,
        "pareto_profile": pareto_profile,
        "optimization_objectives": list(OPTIMIZATION_OBJECTIVES),
    }
    route_summary = _route_summary(
        display_name=str(route.get("display_name", "")),
        best_route_cost=best_route_cost,
        existing_reuse=existing_reuse,
        wrappers=wrappers,
        bridges=bridges,
        source_discovery=source_discovery,
        first_principles=first_principles,
        blockers=blockers,
    )
    return GoalConditionedMinimalFormalizationPlanRow(
        schema_version=GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION,
        goal_plan_id="goal_conditioned_minimal_formalization_plan:" + stable_hash(
            [route_id, task_id, selected_primitives, goal_conditioned_cost]
        )[:16],
        route_id=route_id,
        formal_verifier_queue_item_id=str(queue_row.get("item_id", "")),
        task_id=task_id,
        question_id=str(route.get("question_id", "")),
        problem_class=str(route.get("problem_class", "")),
        theorem_goal_id=str(route.get("theorem_goal_id", "")),
        display_name=str(route.get("display_name", "")),
        theorem_skeleton=str(route.get("theorem_skeleton", "")),
        theorem_statement=str(route.get("theorem_statement", "")),
        planner_component=LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        target_prover_family=target_prover_family,
        library_snapshot_ref=library_snapshot_ref,
        formalization_delta_objective=FORMALIZATION_DELTA_OBJECTIVE,
        route_class=str(route.get("route_class", "")),
        pareto_profile=pareto_profile,
        optimization_objectives=OPTIMIZATION_OBJECTIVES,
        recommended_action=str(queue_row.get("recommended_action", "")),
        best_route_cost=best_route_cost,
        goal_conditioned_cost=goal_conditioned_cost,
        route_cost_breakdown=route_cost_breakdown,
        route_efficiency_score=route_efficiency_score,
        dependency_graph_depth=dependency_depth,
        import_cone_size=import_cone_size,
        selected_primitives=selected_primitives,
        existing_reuse_nodes=existing_reuse,
        wrapper_nodes=wrappers,
        bridge_nodes=bridges,
        source_discovery_nodes=source_discovery,
        first_principles_nodes=first_principles,
        minimal_additional_formalization_nodes=minimal_nodes,
        minimal_cut_summary=minimal_cut_summary,
        route_dag_contract=route_dag_contract,
        and_or_plan=and_or_plan,
        and_or_plan_nodes=tuple(and_or_plan.get("nodes", [])),
        and_or_plan_edges=tuple(and_or_plan.get("edges", [])),
        informal_knowledge_dag=informal_knowledge_dag,
        informal_knowledge_dag_nodes=tuple(informal_knowledge_dag.get("nodes", [])),
        informal_knowledge_dag_edges=tuple(informal_knowledge_dag.get("edges", [])),
        lean_realization_dag=lean_realization_dag,
        lean_realization_dag_nodes=lean_realization_dag_nodes,
        lean_realization_dag_edges=lean_realization_dag_edges,
        formal_realization_dag_nodes=formal_realization_dag_nodes,
        formal_realization_dag_edges=formal_realization_dag_edges,
        route_alignment_edges=route_alignment_edges,
        standalone_input_trace=dict(route.get("standalone_input_trace", {})),
        route_revision_triggers=route_revision_triggers,
        interactive_refinement_hooks=interactive_refinement_hooks,
        portable_work_packets=portable_work_packets,
        minimal_delta_summary=minimal_delta_summary,
        portable_work_packet_contract=_portable_work_packet_contract(),
        do_not_formalize_now=do_not_formalize,
        blocked_only_by=blockers,
        next_work_packets=next_packets,
        route_summary=route_summary,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _nodes_for_actions(
    actions: list[dict[str, Any]],
    action_classes: set[str],
) -> tuple[dict[str, object], ...]:
    nodes: list[dict[str, object]] = []
    for action in actions:
        if str(action.get("action_class", "")) not in action_classes:
            continue
        candidate_declaration_rows = _candidate_declaration_rows_for_action(action)
        candidate_declarations = _candidate_declarations_for_action(
            action,
            candidate_declaration_rows=candidate_declaration_rows,
        )
        nodes.append(
            {
                "primitive": str(action.get("primitive", "")),
                "action_id": str(action.get("action_id", "")),
                "action_class": str(action.get("action_class", "")),
                "cost": int(action.get("total_cost", 0) or 0),
                "expected_premises": [
                    str(item) for item in action.get("expected_premises", []) or [] if str(item)
                ][:6],
                "bridge_candidate_obligations": [
                    str(item)
                    for item in action.get("bridge_candidate_obligations", []) or []
                    if str(item)
                ][:6],
                "candidate_declarations": list(candidate_declarations[:6]),
                "candidate_declaration_rows": list(candidate_declaration_rows[:6]),
                "source_refs": _source_refs_for_action(action),
                "source_snippets": _source_snippets_for_action(action),
                "next_step": str(action.get("next_step", "")),
            }
        )
    return tuple(nodes)


def _primitive_names(nodes: tuple[dict[str, object], ...]) -> list[str]:
    return [
        str(node.get("primitive", ""))
        for node in nodes
        if str(node.get("primitive", ""))
    ]


def _source_refs_for_action(action: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for field_name in ("source_refs", "source_gap_ids", "source_task_ids"):
        for item in action.get(field_name, []) or []:
            if str(item):
                refs.append(str(item))
    return list(dict.fromkeys(refs))[:8]


def _source_snippets_for_action(action: dict[str, Any]) -> list[dict[str, object]]:
    snippets: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in action.get("source_snippets", []) or []:
        if not isinstance(item, dict):
            continue
        key = stable_hash(item)
        if key in seen:
            continue
        seen.add(key)
        snippets.append(dict(item))
    return snippets[:8]


def _candidate_declaration_rows_for_action(
    action: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for item in action.get("candidate_declaration_rows", []) or []:
        if not isinstance(item, dict):
            continue
        declaration = str(
            item.get("declaration")
            or item.get("declaration_name")
            or item.get("candidate_declaration")
            or item.get("lean_declaration")
            or item.get("name")
            or item.get("full_name")
            or ""
        ).strip()
        if not declaration:
            continue
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": str(
                    item.get("target_prover_family", "")
                    or item.get("target_prover", "")
                ).strip(),
                "source_field": str(
                    item.get("source_field", "") or "candidate_declaration_rows"
                ).strip(),
            }
        )
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        target = str(row.get("target_prover_family", "")).strip()
        key = (declaration.casefold(), target.casefold())
        if not declaration or key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "declaration": declaration,
                "target_prover_family": target,
                "source_field": str(row.get("source_field", "")).strip()
                or "candidate_declaration_rows",
            }
        )
    return tuple(compact)


def _candidate_declarations_for_action(
    action: dict[str, Any],
    *,
    candidate_declaration_rows: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            [
                *_str_tuple(action.get("candidate_declarations", [])),
                *[
                    str(row.get("declaration", "")).strip()
                    for row in candidate_declaration_rows
                    if str(row.get("declaration", "")).strip()
                ],
            ]
        )
    )


def _declaration_sources_for_node(node: dict[str, Any]) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *_str_tuple(node.get("expected_premises", [])),
                *_str_tuple(node.get("bridge_candidate_obligations", [])),
                *_str_tuple(node.get("candidate_declarations", [])),
                *[
                    str(row.get("declaration", "")).strip()
                    for row in _dict_tuple(node.get("candidate_declaration_rows", []))
                    if str(row.get("declaration", "")).strip()
                ],
            ]
        )
    )[:8]


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else ()


def _dict_tuple(value: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(value, (list, tuple, set)):
        return ()
    return tuple(dict(item) for item in value if isinstance(item, dict))


def _merge_dict_rows(
    primary: tuple[dict[str, object], ...],
    secondary: tuple[dict[str, object], ...],
    *,
    key_fields: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    merged: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in (*primary, *secondary):
        key = stable_hash(
            [
                str(row.get(field_name, ""))
                for field_name in key_fields
            ]
            or [row]
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(dict(row))
    return tuple(merged)


def _minimal_cut_summary(
    *,
    display_name: str,
    best_route_cost: int,
    goal_conditioned_cost: int,
    existing_reuse: tuple[dict[str, object], ...],
    wrappers: tuple[dict[str, object], ...],
    bridges: tuple[dict[str, object], ...],
    source_discovery: tuple[dict[str, object], ...],
    first_principles: tuple[dict[str, object], ...],
    do_not_formalize: tuple[str, ...],
    blockers: tuple[str, ...],
) -> dict[str, object]:
    return {
        "target_theorem": display_name,
        "best_route_cost": best_route_cost,
        "goal_conditioned_cost": goal_conditioned_cost,
        "use_existing": _primitive_names(existing_reuse),
        "add_wrappers": _primitive_names(wrappers),
        "add_bridge_lemmas": _primitive_names(bridges),
        "add_source_discovery": _primitive_names(source_discovery),
        "add_first_principles": _primitive_names(first_principles),
        "do_not_formalize": list(do_not_formalize),
        "blocked_only_by": list(blockers),
        "planner_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _route_dag_contract(
    *,
    existing_reuse: tuple[dict[str, object], ...],
    wrappers: tuple[dict[str, object], ...],
    bridges: tuple[dict[str, object], ...],
    source_discovery: tuple[dict[str, object], ...],
    first_principles: tuple[dict[str, object], ...],
    blockers: tuple[str, ...],
) -> dict[str, object]:
    return {
        "planner_kind": "goal_conditioned_backward_delta_planner",
        "node_groups": {
            "existing_reuse": len(existing_reuse),
            "wrappers": len(wrappers),
            "bridge_lemmas": len(bridges),
            "source_discovery": len(source_discovery),
            "first_principles": len(first_principles),
        },
        "and_or_route_boundary": (
            "This route is a heuristic AND/OR cut derived from "
            "formalization_delta_plan actions and formal_verifier_queue costs; "
            "it is not a complete proof-route DAG until target-prover attempts "
            "materialize each missing node."
        ),
        "alignment_edge_contract": (
            "Each selected informal semantic atom should align to an existing "
            "reuse node or a selected delta candidate in the formal realization "
            "DAG before downstream prover adapters consume the route."
        ),
        "blocking_status": "blocked" if blockers else "unblocked",
    }


def _graph_count(graph: dict[str, object], key: str) -> int:
    values = graph.get(key, [])
    return len(values) if isinstance(values, list) else 0


def _node_id(prefix: str, value: str) -> str:
    return f"{prefix}:{stable_hash(value)[:12]}"


def _library_snapshot_ref(
    formalization_delta_plan_dir: Path,
    formal_verifier_queue_dir: Path,
) -> str:
    return stable_hash(
        [
            str(formalization_delta_plan_dir),
            str(formal_verifier_queue_dir),
        ]
    )[:24]


def _source_target_prover_family(
    delta_payload: dict[str, Any],
    queue_payload: dict[str, Any],
) -> str:
    for payload in (delta_payload, queue_payload):
        value = str(
            payload.get("target_prover_family")
            or payload.get("target_prover")
            or ""
        ).strip()
        if value:
            return value
    return TARGET_PROVER_FAMILY


def _target_prover_family(
    route: dict[str, Any],
    queue_row: dict[str, Any],
    *,
    source_target_prover_family: str,
) -> str:
    return str(
        route.get("target_prover_family")
        or queue_row.get("target_prover_family")
        or source_target_prover_family
        or TARGET_PROVER_FAMILY
    ).strip()


def _manifest_target_prover_family(
    rows: list[GoalConditionedMinimalFormalizationPlanRow],
    *,
    source_target_prover_family: str,
) -> str:
    targets = sorted(
        {
            str(row.target_prover_family or "").strip()
            for row in rows
            if str(row.target_prover_family or "").strip()
        }
    )
    if len(targets) == 1:
        return targets[0]
    if len(targets) > 1:
        return "mixed:" + ",".join(targets)
    return source_target_prover_family or TARGET_PROVER_FAMILY


def _prover_family_key(target_prover_family: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        str(target_prover_family).strip().lower(),
    ).strip("_")


def _is_lean_target_prover(target_prover_family: str) -> bool:
    key = _prover_family_key(target_prover_family)
    return key in {"lean", "lean4", "lean_4"} or key.startswith(
        ("lean4_", "lean_4_", "lean_")
    )


def _proof_state_tools_for_target_prover(target_prover_family: str) -> tuple[str, ...]:
    target = _prover_family_key(target_prover_family)
    if target in {"lean", "lean4", "lean4_adapter_with_portable_gap_schema"}:
        return (
            "lean-lsp-mcp",
            "Lean LSP",
            "lake build",
        )
    if target in {"rocq", "coq"}:
        return (
            "Rocq/coq-lsp proof-state adapter",
            "SerAPI/sertop",
            "rocq/coq build command",
        )
    if target in {"isabelle", "isabelle_hol", "hol"}:
        return (
            "Isabelle server proof-state adapter",
            "find_theorems/Sledgehammer",
            "isabelle build",
        )
    if target == "agda":
        return (
            "Agda interaction-mode proof-state adapter",
            "agda --interaction-json",
            "agda type-check command",
        )
    return (
        "target-prover proof-state adapter",
        "target-prover LSP/kernel diagnostics",
        "target-prover build/check command",
    )


def _planner_contract(library_snapshot_ref: str) -> dict[str, object]:
    return {
        "component": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        "schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "schema_version": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
        "library_snapshot_ref": library_snapshot_ref,
        "output_contract": {
            "existing_reuse_nodes": "already available declarations or verified obligations",
            "minimal_additional_formalization_nodes": "wrappers, bridge lemmas, ports, or new primitives selected for this theorem",
            "and_or_plan": "AND requirements and OR alternatives excluded from the current minimal cut",
            "work_packets": "bounded theorem-prover tasks with source and kernel-verification gates",
        },
        "proof_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _interactive_route_synthesis_contract() -> dict[str, object]:
    return {
        "loop": [
            "target_intake",
            "literature_evidence_search",
            "informal_route_dag",
            "formal_library_coverage_mapping",
            "minimal_delta_planning",
            "leaf_prover_attempts",
            "residual_feedback_revision",
        ],
        "bounded_expansion_policy": [
            "expand literature only until the proof route stabilizes",
            "search the target prover library for every informal route node before proposing new formalization",
            "let target-prover diagnostics trigger focused route revision instead of field-wide formalization",
        ],
        "proof_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _evaluation_protocol() -> dict[str, object]:
    return {
        "primary_metrics": [
            "route_recall",
            "delta_precision",
            "target_prover_effort_new_declarations",
            "coverage_classification_accuracy",
            "downstream_kernel_verified_success",
        ],
        "minimality_proxy": (
            "remove each proposed delta node and check whether the route still "
            "has a lower-cost or kernel-verified alternative"
        ),
    }


def _portable_work_packet_contract() -> dict[str, object]:
    return {
        "required_fields": [
            "primitive",
            "action_class",
            "expected_cost",
            "worker_packet_kind",
            "required_gate",
            "target_prover_family",
        ],
        "acceptance_gate": (
            "kernel verification in the target prover plus no placeholder axioms/sorries"
        ),
    }


def _pareto_profile(
    *,
    existing_reuse: tuple[dict[str, object], ...],
    wrappers: tuple[dict[str, object], ...],
    bridges: tuple[dict[str, object], ...],
    source_discovery: tuple[dict[str, object], ...],
    first_principles: tuple[dict[str, object], ...],
) -> str:
    if source_discovery:
        return "source_grounded_port"
    if first_principles:
        return "least_first_principles_exposure"
    if wrappers and not bridges:
        return "wrapper_only_delta"
    if bridges:
        return "minimal_bridge_cut"
    if existing_reuse:
        return "reuse_existing_library"
    return "manual_review_delta"


def _and_or_plan(
    *,
    route_id: str,
    display_name: str,
    existing_reuse: tuple[dict[str, object], ...],
    minimal_nodes: tuple[dict[str, object], ...],
    blockers: tuple[str, ...],
) -> dict[str, object]:
    target_id = _node_id("target", route_id or display_name)
    nodes: list[dict[str, object]] = [
        {
            "node_id": target_id,
            "kind": "target_theorem",
            "node_type": "target_theorem",
            "label": display_name,
            "status": "target",
            "availability": "target",
        }
    ]
    edges: list[dict[str, object]] = []
    for node in existing_reuse:
        primitive = str(node.get("primitive", ""))
        node_id = _node_id("existing", primitive)
        nodes.append(
            {
                "node_id": node_id,
                "kind": "existing_reuse",
                "node_type": "existing_reuse",
                "label": primitive,
                "status": "existing_in_library",
                "availability": "already_available",
                "action_class": node.get("action_class", ""),
            }
        )
        edges.append(
            {
                "source": node_id,
                "target": target_id,
                "kind": "AND_requires",
                "edge_type": "or_route_reuses_existing_node",
            }
        )
    for node in minimal_nodes:
        primitive = str(node.get("primitive", ""))
        node_id = _node_id("missing", primitive + str(node.get("action_class", "")))
        nodes.append(
            {
                "node_id": node_id,
                "kind": "minimal_additional_formalization",
                "node_type": "minimal_additional_formalization",
                "label": primitive,
                "status": "selected_for_delta",
                "availability": "must_add_for_selected_route",
                "action_class": node.get("action_class", ""),
                "cost": node.get("cost", 0),
            }
        )
        edges.append(
            {
                "source": node_id,
                "target": target_id,
                "kind": "AND_requires",
                "edge_type": "and_route_requires_missing_node",
            }
        )
    for blocker in blockers:
        node_id = _node_id("blocker", blocker)
        nodes.append(
            {
                "node_id": node_id,
                "kind": "route_blocker",
                "node_type": "route_blocker",
                "label": blocker,
                "status": "selected_for_delta",
                "availability": "blocks_or_penalizes_route",
            }
        )
        edges.append(
            {
                "source": node_id,
                "target": target_id,
                "kind": "AND_requires",
                "edge_type": "route_revision_trigger",
            }
        )
    return {
        "nodes": nodes,
        "edges": edges,
        "boundary": (
            "Heuristic AND/OR route cut for planning. It is not a complete target-prover "
            "proof dependency graph until each missing node is materialized and "
            "kernel checked."
        ),
    }


def _informal_knowledge_dag(
    *,
    route_id: str,
    display_name: str,
    selected_primitives: tuple[str, ...],
    route_source_refs: tuple[str, ...],
    informal_proof_steps: tuple[str, ...],
    source_refs_by_primitive: dict[str, tuple[str, ...]],
    blockers: tuple[str, ...],
) -> dict[str, object]:
    target_id = _node_id("informal_target", route_id or display_name)
    nodes: list[dict[str, object]] = [
        {
            "node_id": target_id,
            "kind": "informal_target",
            "node_type": "informal_target",
            "label": display_name,
            "evidence_status": PROOF_EVIDENCE_STATUS,
            "source_refs": list(route_source_refs),
            "informal_proof_steps": list(informal_proof_steps),
        }
    ]
    edges: list[dict[str, object]] = []
    for primitive in selected_primitives:
        node_id = _node_id("semantic_atom", primitive)
        nodes.append(
            {
                "node_id": node_id,
                "kind": "semantic_atom",
                "node_type": "semantic_atom",
                "label": primitive,
                "evidence_status": PROOF_EVIDENCE_STATUS,
                "source_refs": list(source_refs_by_primitive.get(primitive, ())),
            }
        )
        edges.append(
            {
                "source": node_id,
                "target": target_id,
                "kind": "supports_target_route",
                "edge_type": "supports_target_route",
            }
        )
    for blocker in blockers:
        node_id = _node_id("hidden_assumption_or_gap", blocker)
        nodes.append(
            {
                "node_id": node_id,
                "kind": "hidden_assumption_or_gap",
                "node_type": "hidden_assumption_or_gap",
                "label": blocker,
                "evidence_status": PROOF_EVIDENCE_STATUS,
                "source_refs": list(route_source_refs),
            }
        )
        edges.append(
            {
                "source": node_id,
                "target": target_id,
                "kind": "must_resolve_or_accept_boundary",
                "edge_type": "must_resolve_or_accept_boundary",
            }
        )
    return {
        "nodes": nodes,
        "edges": edges,
        "boundary": (
            "Informal semantic atoms and blockers are planning hints; they are "
            "not source-grounded proof evidence by themselves."
        ),
    }


def _source_refs_by_primitive(
    nodes: tuple[dict[str, object], ...],
) -> dict[str, tuple[str, ...]]:
    refs: dict[str, tuple[str, ...]] = {}
    for node in nodes:
        primitive = str(node.get("primitive", ""))
        if not primitive:
            continue
        refs[primitive] = tuple(
            dict.fromkeys(
                str(item)
                for item in node.get("source_refs", []) or []
                if str(item)
            )
        )
    return refs


def _lean_realization_dag(
    *,
    route_id: str,
    display_name: str,
    existing_reuse: tuple[dict[str, object], ...],
    minimal_nodes: tuple[dict[str, object], ...],
) -> dict[str, object]:
    target_id = _node_id("formal_target", route_id or display_name)
    nodes: list[dict[str, object]] = [
        {
            "node_id": target_id,
            "kind": "formal_target_skeleton",
            "node_type": "formal_target_skeleton",
            "label": display_name,
            "evidence_status": PROOF_EVIDENCE_STATUS,
        }
    ]
    edges: list[dict[str, object]] = []
    for node in (*existing_reuse, *minimal_nodes):
        primitive = str(node.get("primitive", ""))
        action_class = str(node.get("action_class", ""))
        declaration_sources = _declaration_sources_for_node(node)
        node_id = _node_id("formal_realization", primitive + action_class)
        nodes.append(
            {
                "node_id": node_id,
                "kind": "formal_realization_candidate",
                "node_type": "formal_realization_candidate",
                "label": primitive,
                "evidence_status": PROOF_EVIDENCE_STATUS,
                "action_class": action_class,
                "declaration_sources": declaration_sources,
                "candidate_declarations": list(
                    _str_tuple(node.get("candidate_declarations", []))[:8]
                ),
                "candidate_declaration_rows": list(
                    _dict_tuple(node.get("candidate_declaration_rows", []))[:8]
                ),
            }
        )
        edges.append(
            {
                "source": node_id,
                "target": target_id,
                "kind": "candidate_realizes_route_node",
                "edge_type": "candidate_realizes_route_node",
            }
        )
    return {
        "nodes": nodes,
        "edges": edges,
        "boundary": (
            "Formal realization candidates require target-prover replay and "
            "kernel verification before they count as proof evidence."
        ),
    }


def _route_alignment_edges(
    *,
    informal_knowledge_dag: dict[str, object],
    lean_realization_dag: dict[str, object],
) -> tuple[dict[str, object], ...]:
    informal_by_label = {
        str(node.get("label", "")): node
        for node in informal_knowledge_dag.get("nodes", [])
        if isinstance(node, dict)
        and str(node.get("node_type", node.get("kind", ""))) == "semantic_atom"
        and str(node.get("label", ""))
    }
    edges: list[dict[str, object]] = []
    for lean_node in lean_realization_dag.get("nodes", []):
        if not isinstance(lean_node, dict):
            continue
        if str(lean_node.get("node_type", lean_node.get("kind", ""))) not in {
            "formal_realization_candidate",
            "lean_realization_candidate",
        }:
            continue
        primitive = str(lean_node.get("label", ""))
        informal_node = informal_by_label.get(primitive)
        if not informal_node:
            continue
        action_class = str(lean_node.get("action_class", ""))
        edges.append(
            {
                "source": str(informal_node.get("node_id", "")),
                "target": str(lean_node.get("node_id", "")),
                "kind": "aligned_to_formal_realization_candidate",
                "edge_type": "informal_to_formal_alignment",
                "primitive": primitive,
                "action_class": action_class,
                "alignment_status": _alignment_status(action_class),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return tuple(
        sorted(
            edges,
            key=lambda edge: (
                str(edge.get("primitive", "")),
                str(edge.get("action_class", "")),
                str(edge.get("target", "")),
            ),
        )
    )


def _alignment_status(action_class: str) -> str:
    return {
        "reuse_exact_proof_bank_obligation": "exact_existing_reuse",
        "compose_existing_bridge_chain": "composition_candidate",
        "add_minimal_wrapper": "wrapper_delta",
        "design_bridge_lemma": "bridge_delta",
        "formalize_assumption_interface": "assumption_interface_delta",
        "port_external_source": "source_port_delta",
        "design_from_first_principles": "new_theory_delta",
    }.get(action_class, "selected_delta_candidate")


def _route_revision_triggers(
    *,
    existing_reuse: tuple[dict[str, object], ...],
    wrappers: tuple[dict[str, object], ...],
    bridges: tuple[dict[str, object], ...],
    source_discovery: tuple[dict[str, object], ...],
    first_principles: tuple[dict[str, object], ...],
    blockers: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    triggers: list[dict[str, object]] = []
    if not existing_reuse:
        triggers.append(
            {
                "trigger_kind": "formal_leaf_attempt_required",
                "condition": "no existing reuse node found for the selected route",
                "next_action": "search formal-library candidates before adding new formalization",
            }
        )
    if wrappers or bridges:
        triggers.append(
            {
                "trigger_kind": "formal_leaf_attempt_required",
                "condition": "selected route contains wrappers or bridge lemmas",
                "next_action": "probe the leaf goals with target-prover feedback before route promotion",
            }
        )
    if source_discovery:
        triggers.append(
            {
                "trigger_kind": "source_port_or_external_declaration_needed",
                "condition": "selected route needs an external source or source port",
                "next_action": "collect source-grounded theorem statements and candidate declarations",
            }
        )
    if first_principles:
        triggers.append(
            {
                "trigger_kind": "new_theory_risk_review",
                "condition": "selected route contains first-principles formalization",
                "next_action": "look for a narrower existing route or lower-cost bridge before expanding theory",
            }
        )
    for blocker in blockers[:6]:
        triggers.append(
            {
                "trigger_kind": "blocked_by_formal_side_condition",
                "condition": blocker,
                "next_action": "revise the route or create a focused side-condition work packet",
            }
        )
    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    for trigger in triggers:
        key = stable_hash([trigger.get("trigger_kind", ""), trigger.get("condition", "")])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(trigger)
    return tuple(deduped)


def _portable_work_packets(
    next_packets: tuple[dict[str, object], ...],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    packets: list[dict[str, object]] = []
    for packet in next_packets:
        packets.append(
            {
                **packet,
                "target_prover_family": target_prover_family,
                "portable_contract": (
                    "Self-contained theorem-development packet. It may be "
                    "sent to a worker or another planning thread, but promotion "
                    "requires local replay and kernel verification."
                ),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            }
        )
    return tuple(packets)


def _interactive_refinement_hooks(
    *,
    display_name: str,
    theorem_skeleton: str,
    theorem_statement: str,
    selected_primitives: tuple[str, ...],
    source_discovery: tuple[dict[str, object], ...],
    first_principles: tuple[dict[str, object], ...],
    blockers: tuple[str, ...],
    route_revision_triggers: tuple[dict[str, object], ...],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    primitive_query = " ".join(selected_primitives[:8])
    hooks: list[dict[str, object]] = [
        {
            "hook_kind": "formal_library_grounding",
            "recommended_tools": [
                "local formal-source index",
                "target prover library search",
                "LeanSearch/Loogle/LeanExplore for Lean targets",
                "Rocq/coq-lsp/SerAPI for Rocq targets",
                "Isabelle find_theorems/Sledgehammer for Isabelle targets",
            ],
            "queries": [item for item in selected_primitives[:8] if item],
            "acceptance_record": (
                "record exact, stronger, weaker, or bridgeable formal declarations "
                "before adding new formalization"
            ),
        },
        {
            "hook_kind": "proof_state_feedback",
            "recommended_tools": list(
                _proof_state_tools_for_target_prover(target_prover_family)
            ),
            "queries": [
                item
                for item in (
                    theorem_statement,
                    theorem_skeleton,
                    primitive_query,
                    display_name,
                )
                if item
            ],
            "acceptance_record": (
                "record exact target-prover goal state, diagnostics, and failed tactic signatures"
            ),
        },
    ]
    if source_discovery or first_principles or blockers:
        hooks.append(
            {
                "hook_kind": "literature_discovery",
                "recommended_tools": [
                    "Paperclip MCP/CLI",
                    "PaperQA2",
                    "Semantic Scholar API",
                    "OpenAlex Works API",
                    "arXiv",
                ],
                "queries": [
                    item
                    for item in (
                        f"{display_name} theorem assumptions proof route",
                        primitive_query,
                        f"{display_name} measurability integrability side conditions",
                    )
                    if item
                ],
                "acceptance_record": (
                    "record source-backed theorem variants and hidden assumptions "
                    "before expanding the formalization delta"
                ),
            }
        )
    if route_revision_triggers:
        hooks.append(
            {
                "hook_kind": "route_revision",
                "recommended_tools": [
                    "literature_discovery",
                    "formal_library_grounding",
                    "proof_state_feedback",
                ],
                "queries": [
                    item
                    for item in (display_name, primitive_query, theorem_skeleton)
                    if item
                ],
                "acceptance_record": (
                    "revise the informal knowledge DAG, formal realization DAG, and "
                    "selected delta before the next replay attempt"
                ),
            }
        )
    return tuple(hooks)


def _next_packets(
    nodes: tuple[dict[str, object], ...],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    packets: list[dict[str, object]] = []
    for node in nodes[:8]:
        packets.append(
            {
                "primitive": node.get("primitive", ""),
                "action_class": node.get("action_class", ""),
                "target_prover_family": target_prover_family,
                "expected_cost": node.get("cost", 0),
                "worker_packet_kind": _worker_packet_kind(str(node.get("action_class", ""))),
                "required_gate": (
                    "emit a target-prover statement/proof candidate only after "
                    "source support and local kernel checks are attached"
                ),
            }
        )
    return tuple(packets)


def _worker_packet_kind(action_class: str) -> str:
    if action_class in {"reuse_exact_proof_bank_obligation", "compose_existing_bridge_chain"}:
        return "reuse_existing_verified_source"
    if action_class == "add_minimal_wrapper":
        return "minimal_wrapper"
    if action_class in {"design_bridge_lemma", "formalize_assumption_interface"}:
        return "bridge_lemma"
    if action_class == "port_external_source":
        return "source_discovery"
    return "new_primitive"


def _route_summary(
    *,
    display_name: str,
    best_route_cost: int,
    existing_reuse: tuple[dict[str, object], ...],
    wrappers: tuple[dict[str, object], ...],
    bridges: tuple[dict[str, object], ...],
    source_discovery: tuple[dict[str, object], ...],
    first_principles: tuple[dict[str, object], ...],
    blockers: tuple[str, ...],
) -> str:
    pieces = [
        f"Target `{display_name}` best route cost={best_route_cost}.",
        f"Use existing={len(existing_reuse)}.",
        f"Add wrappers={len(wrappers)}.",
        f"Add bridge/source nodes={len(bridges) + len(source_discovery)}.",
        f"First-principles nodes={len(first_principles)}.",
    ]
    if blockers:
        pieces.append("Blocked only by: " + ", ".join(blockers[:4]) + ".")
    return " ".join(pieces)


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
        "# Goal-Conditioned Minimal Formalization Plan",
        "",
        f"- Goal plans: {payload.get('n_goal_plans')}",
        f"- Low-cost plans: {payload.get('n_low_cost_goal_plans')}",
        f"- Reuse nodes: {payload.get('n_existing_reuse_nodes')}",
        f"- Wrapper nodes: {payload.get('n_wrapper_nodes')}",
        f"- Bridge nodes: {payload.get('n_bridge_nodes')}",
        f"- Source-discovery nodes: {payload.get('n_source_discovery_nodes')}",
        f"- First-principles nodes: {payload.get('n_first_principles_nodes')}",
        f"- Minimal additional nodes: {payload.get('n_minimal_additional_formalization_nodes')}",
        f"- Minimal cuts: {payload.get('n_goal_plans_with_minimal_cut')}",
        f"- Cost-breakdown terms: {payload.get('n_route_cost_breakdown_terms')}",
        f"- Target prover family: {payload.get('target_prover_family')}",
        f"- AND/OR plan graph: {payload.get('n_and_or_plan_nodes')} nodes / {payload.get('n_and_or_plan_edges')} edges",
        f"- Informal knowledge DAG: {payload.get('n_informal_knowledge_dag_nodes')} nodes / {payload.get('n_informal_knowledge_dag_edges')} edges",
        f"- Formal realization DAG: {payload.get('n_formal_realization_dag_nodes')} nodes / {payload.get('n_formal_realization_dag_edges')} edges",
        (
            f"- Route-alignment edge schema valid: "
            f"{payload.get('n_route_alignment_edge_schema_valid')}/"
            f"{payload.get('n_route_alignment_edges')}"
        ),
        f"- Route revision triggers: {payload.get('n_route_revision_triggers')}",
        f"- Portable work packets: {payload.get('n_portable_work_packets')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary")),
        "",
        "## Goal Plans",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` cost={row.get('goal_conditioned_cost')} "
            f"efficiency={row.get('route_efficiency_score')} class={row.get('route_class')}"
        )
        lines.append(f"  selected primitives: {', '.join(row.get('selected_primitives', []))}")
        nodes = row.get("minimal_additional_formalization_nodes", [])
        if nodes:
            lines.append(
                "  add: "
                + ", ".join(
                    f"`{node.get('primitive')}`/{node.get('action_class')}"
                    for node in nodes[:6]
                    if isinstance(node, dict)
                )
            )
        if row.get("do_not_formalize_now"):
            lines.append(
                "  do not formalize now: "
                + ", ".join(f"`{item}`" for item in row.get("do_not_formalize_now", [])[:6])
            )
        cut = row.get("minimal_cut_summary", {})
        if isinstance(cut, dict):
            lines.append(
                "  minimal cut: "
                f"use_existing={len(cut.get('use_existing', []))} "
                f"wrappers={len(cut.get('add_wrappers', []))} "
                f"bridges={len(cut.get('add_bridge_lemmas', []))} "
                f"source={len(cut.get('add_source_discovery', []))} "
                f"first_principles={len(cut.get('add_first_principles', []))}"
            )
        cost = row.get("route_cost_breakdown", {})
        if isinstance(cost, dict):
            lines.append(
                "  cost terms: "
                f"base={cost.get('base_route_cost')} "
                f"import={cost.get('import_cone_penalty')} "
                f"depth={cost.get('dependency_depth_penalty')} "
                f"blockers={cost.get('blocker_penalty')} "
                f"trust_credit={cost.get('source_trust_credit')}"
            )
        lines.append(f"  summary: {row.get('route_summary')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    return "\n".join(lines) + "\n"
