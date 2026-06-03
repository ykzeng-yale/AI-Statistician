from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION = 2
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
    "additional formalization cut for a target theorem, but only AXLE/local Lean "
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
    payload: dict[str, object] = {
        "schema_version": GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION,
        "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "portable_schema_version": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
        "component_name": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        "target_prover_family": TARGET_PROVER_FAMILY,
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
            _graph_count(row.lean_realization_dag, "nodes") for row in rows
        ),
        "n_lean_realization_dag_edges": sum(
            _graph_count(row.lean_realization_dag, "edges") for row in rows
        ),
        "n_route_revision_triggers": sum(len(row.route_revision_triggers) for row in rows),
        "n_portable_work_packets": sum(len(row.portable_work_packets) for row in rows),
        "n_do_not_formalize_hints": sum(len(row.do_not_formalize_now) for row in rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "by_route_class": dict(sorted(by_route_class.items())),
        "rows": [asdict(row) for row in rows],
        "plan_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "minimal route cost is heuristic and goal-conditioned; it is not proof evidence",
            "do_not_formalize_now is a prioritization hint, not a semantic impossibility claim",
            "AXLE/local Lean verification remains the only proof gate",
        ],
    }
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
    return payload


def _plan_row(
    route: dict[str, Any],
    queue_row: dict[str, Any],
    all_primitives: tuple[str, ...],
    *,
    library_snapshot_ref: str,
) -> GoalConditionedMinimalFormalizationPlanRow:
    errors: list[str] = []
    route_id = str(route.get("route_id", ""))
    task_id = str(route.get("task_id", ""))
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
            "heuristic route-selection cost; not a Lean proof or proof-risk certificate"
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
    next_packets = _next_packets(minimal_nodes or existing_reuse)
    route_revision_triggers = _route_revision_triggers(
        existing_reuse=existing_reuse,
        wrappers=wrappers,
        bridges=bridges,
        source_discovery=source_discovery,
        first_principles=first_principles,
        blockers=blockers,
    )
    portable_work_packets = _portable_work_packets(next_packets)
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
        blockers=blockers,
    )
    lean_realization_dag = _lean_realization_dag(
        route_id=route_id,
        display_name=str(route.get("display_name", "")),
        existing_reuse=existing_reuse,
        minimal_nodes=minimal_nodes,
    )
    interactive_refinement_hooks = _interactive_refinement_hooks(
        display_name=str(route.get("display_name", "")),
        theorem_skeleton=str(route.get("theorem_skeleton", "")),
        selected_primitives=selected_primitives,
        source_discovery=source_discovery,
        first_principles=first_principles,
        blockers=blockers,
        route_revision_triggers=route_revision_triggers,
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
        planner_component=LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        target_prover_family=TARGET_PROVER_FAMILY,
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
        lean_realization_dag_nodes=tuple(lean_realization_dag.get("nodes", [])),
        lean_realization_dag_edges=tuple(lean_realization_dag.get("edges", [])),
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
                "candidate_declarations": [
                    str(item)
                    for item in action.get("candidate_declarations", []) or []
                    if str(item)
                ][:6],
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
            "it is not a complete proof-route DAG until Lean proof attempts "
            "materialize each missing node."
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
            "lean_coverage_mapping",
            "minimal_delta_planning",
            "leaf_prover_attempts",
            "residual_feedback_revision",
        ],
        "bounded_expansion_policy": [
            "expand literature only until the proof route stabilizes",
            "search Lean for every informal route node before proposing new formalization",
            "let Lean diagnostics trigger focused route revision instead of field-wide formalization",
        ],
        "proof_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _evaluation_protocol() -> dict[str, object]:
    return {
        "primary_metrics": [
            "route_recall",
            "delta_precision",
            "lean_effort_new_declarations",
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
            "Heuristic AND/OR route cut for planning. It is not a complete Lean "
            "proof dependency graph until each missing node is materialized and "
            "kernel checked."
        ),
    }


def _informal_knowledge_dag(
    *,
    route_id: str,
    display_name: str,
    selected_primitives: tuple[str, ...],
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


def _lean_realization_dag(
    *,
    route_id: str,
    display_name: str,
    existing_reuse: tuple[dict[str, object], ...],
    minimal_nodes: tuple[dict[str, object], ...],
) -> dict[str, object]:
    target_id = _node_id("lean_target", route_id or display_name)
    nodes: list[dict[str, object]] = [
        {
            "node_id": target_id,
            "kind": "lean_target_skeleton",
            "node_type": "lean_target_skeleton",
            "label": display_name,
            "evidence_status": PROOF_EVIDENCE_STATUS,
        }
    ]
    edges: list[dict[str, object]] = []
    for node in (*existing_reuse, *minimal_nodes):
        primitive = str(node.get("primitive", ""))
        action_class = str(node.get("action_class", ""))
        declaration_sources = [
            *[
                str(item)
                for item in node.get("expected_premises", []) or []
                if str(item)
            ],
            *[
                str(item)
                for item in node.get("bridge_candidate_obligations", []) or []
                if str(item)
            ],
            *[
                str(item)
                for item in node.get("candidate_declarations", []) or []
                if str(item)
            ],
        ][:8]
        node_id = _node_id("lean_realization", primitive + action_class)
        nodes.append(
            {
                "node_id": node_id,
                "kind": "lean_realization_candidate",
                "node_type": "lean_realization_candidate",
                "label": primitive,
                "evidence_status": PROOF_EVIDENCE_STATUS,
                "action_class": action_class,
                "declaration_sources": declaration_sources,
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
            "Lean realization candidates require replay or AXLE/local Lean "
            "kernel verification before they count as proof evidence."
        ),
    }


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
                "trigger_kind": "lean_leaf_attempt_required",
                "condition": "no existing reuse node found for the selected route",
                "next_action": "search Lean/library candidates before adding new formalization",
            }
        )
    if wrappers or bridges:
        triggers.append(
            {
                "trigger_kind": "lean_leaf_attempt_required",
                "condition": "selected route contains wrappers or bridge lemmas",
                "next_action": "probe the leaf goals with Lean LSP or local Lean before route promotion",
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
) -> tuple[dict[str, object], ...]:
    packets: list[dict[str, object]] = []
    for packet in next_packets:
        packets.append(
            {
                **packet,
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
    selected_primitives: tuple[str, ...],
    source_discovery: tuple[dict[str, object], ...],
    first_principles: tuple[dict[str, object], ...],
    blockers: tuple[str, ...],
    route_revision_triggers: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    primitive_query = " ".join(selected_primitives[:8])
    hooks: list[dict[str, object]] = [
        {
            "hook_kind": "lean_library_grounding",
            "recommended_tools": [
                "local Lean RAG DB",
                "LeanSearch",
                "LeanExplore",
                "Loogle",
            ],
            "queries": [item for item in selected_primitives[:8] if item],
            "acceptance_record": (
                "record exact, stronger, weaker, or bridgeable Lean declarations "
                "before adding new formalization"
            ),
        },
        {
            "hook_kind": "proof_state_feedback",
            "recommended_tools": ["lean-lsp-mcp", "Lean LSP", "lake build"],
            "queries": [
                item
                for item in (theorem_skeleton, primitive_query, display_name)
                if item
            ],
            "acceptance_record": (
                "record exact Lean goal state, diagnostics, and failed tactic signatures"
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
                    "before expanding the Lean delta"
                ),
            }
        )
    if route_revision_triggers:
        hooks.append(
            {
                "hook_kind": "route_revision",
                "recommended_tools": [
                    "literature_discovery",
                    "lean_library_grounding",
                    "proof_state_feedback",
                ],
                "queries": [
                    item
                    for item in (display_name, primitive_query, theorem_skeleton)
                    if item
                ],
                "acceptance_record": (
                    "revise the informal knowledge DAG, Lean realization DAG, and "
                    "selected delta before the next replay attempt"
                ),
            }
        )
    return tuple(hooks)


def _next_packets(nodes: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    packets: list[dict[str, object]] = []
    for node in nodes[:8]:
        packets.append(
            {
                "primitive": node.get("primitive", ""),
                "action_class": node.get("action_class", ""),
                "expected_cost": node.get("cost", 0),
                "worker_packet_kind": _worker_packet_kind(str(node.get("action_class", ""))),
                "required_gate": (
                    "emit a Lean statement/proof candidate only after source "
                    "support and local kernel checks are attached"
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
        f"- AND/OR plan graph: {payload.get('n_and_or_plan_nodes')} nodes / {payload.get('n_and_or_plan_edges')} edges",
        f"- Informal knowledge DAG: {payload.get('n_informal_knowledge_dag_nodes')} nodes / {payload.get('n_informal_knowledge_dag_edges')} edges",
        f"- Lean realization DAG: {payload.get('n_lean_realization_dag_nodes')} nodes / {payload.get('n_lean_realization_dag_edges')} edges",
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
