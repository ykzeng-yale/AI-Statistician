from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMALIZATION_DELTA_PLAN_SCHEMA_VERSION = 2


ACTION_COSTS = {
    "reuse_exact_proof_bank_obligation": 1,
    "compose_existing_bridge_chain": 2,
    "formalize_assumption_interface": 2,
    "add_minimal_wrapper": 3,
    "design_bridge_lemma": 5,
    "port_external_source": 6,
    "design_from_first_principles": 8,
}


@dataclass(frozen=True)
class FormalizationDeltaPlanRow:
    schema_version: int
    primitive: str
    action_id: str
    action_class: str
    plan_stage: str
    delta_kind: str
    coverage_classification: str
    owner_agent: str
    base_cost: int
    risk_penalty: int
    reuse_credit: int
    total_cost: int
    priority: str
    expected_premises: tuple[str, ...]
    bridge_candidate_obligations: tuple[str, ...]
    candidate_declarations: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    problem_classes: tuple[str, ...]
    theorem_goals: tuple[str, ...]
    n_gaps: int
    source_gap_ids: tuple[str, ...]
    source_task_ids: tuple[str, ...]
    next_step: str
    evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalizationDeltaGraphNode:
    node_id: str
    kind: str
    label: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class FormalizationDeltaGraphEdge:
    source: str
    target: str
    kind: str
    metadata: dict[str, object]


def build_formalization_delta_plan(
    proof_bank_actions_dir: Path,
    out_dir: Path | None = None,
    *,
    primitive_source_coverage_dir: Path | None = None,
    formal_gap_tasks_dir: Path | None = None,
) -> dict[str, object]:
    """Plan the smallest useful Lean-formalization delta from action rows.

    This is a planning/ranking artifact, not proof evidence. It estimates which
    new definitions, wrappers, bridge lemmas, or theorem compositions are needed
    before the target frontier theorem can become provable from the current Lean
    environment. AXLE/local Lean still decides whether any row is actually
    verified.
    """

    errors: list[str] = []
    action_manifest_path = proof_bank_actions_dir / "proof_bank_action_manifest.json"
    action_manifest = _read_json(action_manifest_path, errors)
    coverage_manifest_path = (
        primitive_source_coverage_dir / "primitive_source_coverage_manifest.json"
        if primitive_source_coverage_dir is not None
        else None
    )
    coverage_manifest = (
        _read_json(coverage_manifest_path, errors, missing_ok=True)
        if coverage_manifest_path is not None
        else {}
    )
    task_manifest_path = (
        formal_gap_tasks_dir / "formal_gap_lean_task_manifest.json"
        if formal_gap_tasks_dir is not None
        else None
    )
    task_manifest = (
        _read_json(task_manifest_path, errors, missing_ok=True)
        if task_manifest_path is not None
        else {}
    )
    coverage_by_primitive = {
        str(row.get("primitive", "")): row
        for row in coverage_manifest.get("rows", [])
        if isinstance(row, dict) and row.get("primitive")
    }
    task_by_id = {
        str(row.get("task_id", "")): row
        for row in task_manifest.get("tasks", [])
        if isinstance(row, dict) and row.get("task_id")
    }
    rows = [
        _row_from_action(row, coverage_by_primitive)
        for row in action_manifest.get("actions", [])
        if isinstance(row, dict)
    ]
    rows = sorted(rows, key=lambda row: (row.total_cost, row.priority, row.primitive, row.action_id))
    by_stage = Counter(row.plan_stage for row in rows)
    by_delta_kind = Counter(row.delta_kind for row in rows)
    by_action_class = Counter(row.action_class for row in rows)
    graph = _build_dependency_graph(rows, task_by_id)
    theorem_routes = _build_theorem_routes(rows, task_by_id)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_DELTA_PLAN_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_bank_actions_dir": str(proof_bank_actions_dir),
        "proof_bank_action_manifest": str(action_manifest_path),
        "primitive_source_coverage_dir": str(primitive_source_coverage_dir or ""),
        "primitive_source_coverage_manifest": str(coverage_manifest_path or ""),
        "formal_gap_tasks_dir": str(formal_gap_tasks_dir or ""),
        "formal_gap_task_manifest": str(task_manifest_path or ""),
        "n_plan_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(action_manifest.get("all_ok", False)) and all(row.ok for row in rows),
        "total_estimated_cost": sum(row.total_cost for row in rows),
        "mean_estimated_cost": (sum(row.total_cost for row in rows) / len(rows) if rows else 0.0),
        "n_low_cost_existing_reuse": sum(1 for row in rows if row.total_cost <= 2),
        "n_medium_cost_bridge_or_wrapper": sum(1 for row in rows if 3 <= row.total_cost <= 5),
        "n_high_cost_new_theory": sum(1 for row in rows if row.total_cost >= 6),
        "by_plan_stage": dict(sorted(by_stage.items())),
        "by_delta_kind": dict(sorted(by_delta_kind.items())),
        "by_action_class": dict(sorted(by_action_class.items())),
        "dependency_graph": graph,
        "dependency_graph_nodes": graph["n_nodes"],
        "dependency_graph_edges": graph["n_edges"],
        "dependency_graph_by_node_kind": graph["by_node_kind"],
        "dependency_graph_by_edge_kind": graph["by_edge_kind"],
        "dependency_graph_problem_class_nodes": graph["by_node_kind"].get("problem_class", 0),
        "dependency_graph_theorem_goal_nodes": graph["by_node_kind"].get("theorem_goal", 0),
        "dependency_graph_theorem_skeleton_nodes": graph["by_node_kind"].get("lean_theorem_skeleton", 0),
        "dependency_graph_import_nodes": graph["by_node_kind"].get("lean_import", 0),
        "dependency_graph_informal_proof_step_nodes": graph["by_node_kind"].get(
            "informal_proof_step", 0
        ),
        "dependency_graph_goal_to_primitive_edges": graph["by_edge_kind"].get("needs_primitive", 0),
        "dependency_graph_goal_to_skeleton_edges": graph["by_edge_kind"].get("has_lean_skeleton", 0),
        "dependency_graph_skeleton_to_proof_step_edges": graph["by_edge_kind"].get(
            "has_informal_proof_step", 0
        ),
        "n_theorem_formalization_routes": len(theorem_routes),
        "n_theorem_routes_with_informal_steps": sum(
            1 for route in theorem_routes if route.get("informal_proof_steps")
        ),
        "n_theorem_routes_with_reuse_candidates": sum(
            1
            for route in theorem_routes
            if int(route.get("source_support_count", 0) or 0) > 0
        ),
        "n_theorem_routes_requiring_new_theory": sum(
            1 for route in theorem_routes if route.get("route_class") == "requires_new_theory"
        ),
        "theorem_formalization_routes": theorem_routes,
        "top_theorem_routes_by_cost": sorted(
            theorem_routes,
            key=lambda route: (
                -int(route.get("total_estimated_cost", 0) or 0),
                str(route.get("task_id", "")),
            ),
        )[:10],
        "top_low_cost_rows": [asdict(row) for row in rows[:10]],
        "top_high_cost_rows": [asdict(row) for row in sorted(rows, key=lambda row: -row.total_cost)[:10]],
        "rows": [asdict(row) for row in rows],
        "plan_fingerprint": stable_hash([asdict(row) for row in rows]),
        "graph_fingerprint": graph["graph_fingerprint"],
        "errors": errors,
        "limitations": [
            "formalization delta rows are planning evidence, not proof evidence",
            "cost is a heuristic over action class, reuse, blockers, and source coverage",
            "minimality is approximate; AXLE/local Lean verification and semantic review remain required",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_delta_plan_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_delta_plan.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_delta_graph.json").write_text(
            json.dumps(graph, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_delta_plan.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _row_from_action(
    action: dict[str, Any],
    coverage_by_primitive: dict[str, dict[str, Any]],
) -> FormalizationDeltaPlanRow:
    primitive = str(action.get("primitive", ""))
    action_class = str(action.get("action_class", ""))
    coverage = coverage_by_primitive.get(primitive, {})
    expected_premises = tuple(str(item) for item in action.get("expected_premises", []) or [] if str(item))
    bridge_candidates = tuple(
        str(item) for item in action.get("bridge_candidate_obligations", []) or [] if str(item)
    )
    candidate_declarations = tuple(
        str(item) for item in action.get("candidate_declarations", []) or [] if str(item)
    )
    blocked_reasons = tuple(str(item) for item in action.get("blocked_reasons", []) or [] if str(item))
    problem_classes = tuple(str(item) for item in coverage.get("problem_classes", []) or [] if str(item))
    theorem_goals = tuple(str(item) for item in coverage.get("theorem_goals", []) or [] if str(item))
    base_cost = ACTION_COSTS.get(action_class, 9)
    risk_penalty = _risk_penalty(action_class, blocked_reasons, coverage)
    reuse_credit = _reuse_credit(action_class, bridge_candidates, candidate_declarations, coverage)
    total_cost = max(1, base_cost + risk_penalty - reuse_credit)
    errors: list[str] = []
    if not primitive:
        errors.append("missing primitive")
    if not action_class:
        errors.append("missing action_class")
    if action_class not in ACTION_COSTS:
        errors.append(f"unknown action_class={action_class}")
    return FormalizationDeltaPlanRow(
        schema_version=FORMALIZATION_DELTA_PLAN_SCHEMA_VERSION,
        primitive=primitive,
        action_id=str(action.get("action_id", "")),
        action_class=action_class,
        plan_stage=_plan_stage(action_class),
        delta_kind=_delta_kind(action_class),
        coverage_classification=str(coverage.get("classification", "")),
        owner_agent=str(action.get("owner_agent", "formal_verifier")),
        base_cost=base_cost,
        risk_penalty=risk_penalty,
        reuse_credit=reuse_credit,
        total_cost=total_cost,
        priority=str(action.get("priority", "")),
        expected_premises=expected_premises,
        bridge_candidate_obligations=bridge_candidates,
        candidate_declarations=candidate_declarations,
        blocked_reasons=blocked_reasons,
        problem_classes=problem_classes,
        theorem_goals=theorem_goals,
        n_gaps=int(coverage.get("n_gaps", 0) or 0),
        source_gap_ids=tuple(str(item) for item in action.get("source_gap_ids", []) or [] if str(item)),
        source_task_ids=tuple(str(item) for item in action.get("source_task_ids", []) or [] if str(item)),
        next_step=_next_step(action_class, primitive, total_cost),
        evidence_boundary=(
            "This row estimates a minimal formalization delta. It is not proof evidence until "
            "the referenced Lean statements/proofs are accepted by AXLE or the local Lean kernel."
        ),
        ok=not errors and bool(action.get("ok", False)),
        errors=tuple(errors),
    )


def _build_theorem_routes(
    rows: list[FormalizationDeltaPlanRow],
    task_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, object]]:
    rows_by_task: dict[str, list[FormalizationDeltaPlanRow]] = {}
    for row in rows:
        for task_id in row.source_task_ids:
            if task_id:
                rows_by_task.setdefault(task_id, []).append(row)

    routes: list[dict[str, object]] = []
    for task_id, task_rows in sorted(rows_by_task.items()):
        task = task_by_id.get(task_id, {})
        if not task:
            continue
        declaration = _task_declaration(str(task.get("statement", "")))
        if not declaration:
            continue
        ordered_rows = sorted(
            {row.action_id: row for row in task_rows}.values(),
            key=lambda row: (row.total_cost, row.primitive, row.action_id),
        )
        proof_steps = _proof_strategy_steps(str(task.get("proof_strategy", "")))
        required_primitives = tuple(sorted({row.primitive for row in ordered_rows if row.primitive}))
        action_classes = Counter(row.action_class for row in ordered_rows)
        plan_stages = Counter(row.plan_stage for row in ordered_rows)
        total_cost = sum(row.total_cost for row in ordered_rows)
        support_count = sum(
            len(row.expected_premises)
            + len(row.bridge_candidate_obligations)
            + len(row.candidate_declarations)
            for row in ordered_rows
        )
        actions = [
            {
                "primitive": row.primitive,
                "action_id": row.action_id,
                "action_class": row.action_class,
                "plan_stage": row.plan_stage,
                "delta_kind": row.delta_kind,
                "total_cost": row.total_cost,
                "priority": row.priority,
                "expected_premises": list(row.expected_premises),
                "bridge_candidate_obligations": list(row.bridge_candidate_obligations),
                "candidate_declarations": list(row.candidate_declarations),
                "blocked_reasons": list(row.blocked_reasons),
                "next_step": row.next_step,
            }
            for row in ordered_rows
        ]
        routes.append(
            {
                "schema_version": FORMALIZATION_DELTA_PLAN_SCHEMA_VERSION,
                "route_id": f"theorem_route:{task_id}:{stable_hash(str(task.get('statement', '')))[:12]}",
                "task_id": task_id,
                "question_id": str(task.get("question_id", "")),
                "problem_class": str(task.get("problem_class", "")),
                "theorem_goal_id": str(task.get("theorem_goal_id", "")),
                "theorem_skeleton": declaration,
                "display_name": _task_display_name(task_id, task, declaration),
                "namespace": str(task.get("namespace", "")),
                "statement_hash": stable_hash(str(task.get("statement", "")))[:16],
                "imports": [str(item) for item in task.get("imports", []) or [] if str(item)],
                "allowed_sorry": task.get("allowed_sorry", None),
                "informal_proof_steps": list(proof_steps),
                "n_informal_proof_steps": len(proof_steps),
                "required_primitives": list(required_primitives),
                "n_required_primitives": len(required_primitives),
                "total_estimated_cost": total_cost,
                "max_primitive_cost": max((row.total_cost for row in ordered_rows), default=0),
                "low_cost_action_count": sum(1 for row in ordered_rows if row.total_cost <= 2),
                "medium_cost_action_count": sum(1 for row in ordered_rows if 3 <= row.total_cost <= 5),
                "high_cost_action_count": sum(1 for row in ordered_rows if row.total_cost >= 6),
                "route_class": _route_class(ordered_rows),
                "by_action_class": dict(sorted(action_classes.items())),
                "by_plan_stage": dict(sorted(plan_stages.items())),
                "source_support_count": support_count,
                "actions": actions,
                "first_next_actions": actions[:5],
                "evidence_boundary": (
                    "This route summarizes minimal formalization work for a theorem skeleton. "
                    "It is not proof evidence until the referenced Lean work is verified by "
                    "AXLE or the local Lean kernel."
                ),
            }
        )
    return sorted(
        routes,
        key=lambda route: (
            int(route.get("total_estimated_cost", 0) or 0),
            str(route.get("theorem_skeleton", "")),
            str(route.get("task_id", "")),
        ),
    )


def _route_class(rows: list[FormalizationDeltaPlanRow]) -> str:
    if any(row.total_cost >= 6 for row in rows):
        return "requires_new_theory"
    if any(3 <= row.total_cost <= 5 for row in rows):
        return "bridge_or_wrapper"
    return "reuse_or_composition"


def _build_dependency_graph(
    rows: list[FormalizationDeltaPlanRow],
    task_by_id: dict[str, dict[str, Any]],
) -> dict[str, object]:
    nodes: dict[str, FormalizationDeltaGraphNode] = {}
    edges: dict[tuple[str, str, str], FormalizationDeltaGraphEdge] = {}

    def add_node(node_id: str, kind: str, label: str, **metadata: object) -> None:
        if node_id not in nodes:
            nodes[node_id] = FormalizationDeltaGraphNode(
                node_id=node_id,
                kind=kind,
                label=label,
                metadata={key: value for key, value in metadata.items() if value not in (None, "", (), [])},
            )

    def add_edge(source: str, target: str, kind: str, **metadata: object) -> None:
        key = (source, target, kind)
        if key not in edges:
            edges[key] = FormalizationDeltaGraphEdge(
                source=source,
                target=target,
                kind=kind,
                metadata={key: value for key, value in metadata.items() if value not in (None, "", (), [])},
            )

    for row in rows:
        primitive_id = f"primitive:{row.primitive}"
        action_id = f"action:{row.action_id}"
        stage_id = f"stage:{row.plan_stage}"
        delta_kind_id = f"delta_kind:{row.delta_kind}"
        add_node(
            primitive_id,
            "primitive",
            row.primitive,
            coverage_classification=row.coverage_classification,
            total_cost=row.total_cost,
        )
        add_node(
            action_id,
            "action",
            row.action_id,
            action_class=row.action_class,
            priority=row.priority,
            total_cost=row.total_cost,
            owner_agent=row.owner_agent,
        )
        add_node(stage_id, "plan_stage", row.plan_stage)
        add_node(delta_kind_id, "delta_kind", row.delta_kind)
        add_edge(primitive_id, action_id, "planned_by", total_cost=row.total_cost)
        add_edge(action_id, stage_id, "assigned_stage")
        add_edge(action_id, delta_kind_id, "produces_delta_kind")

        goal_node_ids: list[str] = []
        for problem_class in row.problem_classes:
            node_id = f"problem_class:{problem_class}"
            add_node(node_id, "problem_class", problem_class)
            add_edge(node_id, primitive_id, "has_missing_primitive", n_gaps=row.n_gaps)
            for theorem_goal in row.theorem_goals:
                goal_id = f"theorem_goal:{problem_class}:{theorem_goal}"
                goal_node_ids.append(goal_id)
                add_node(goal_id, "theorem_goal", theorem_goal, problem_class=problem_class)
                add_edge(node_id, goal_id, "targets_goal")
                add_edge(goal_id, primitive_id, "needs_primitive", n_gaps=row.n_gaps)
                add_edge(goal_id, action_id, "handled_by_delta_action", total_cost=row.total_cost)
        if not row.problem_classes:
            for theorem_goal in row.theorem_goals:
                goal_id = f"theorem_goal:{theorem_goal}"
                goal_node_ids.append(goal_id)
                add_node(goal_id, "theorem_goal", theorem_goal)
                add_edge(goal_id, primitive_id, "needs_primitive", n_gaps=row.n_gaps)
                add_edge(goal_id, action_id, "handled_by_delta_action", total_cost=row.total_cost)

        for gap_id in row.source_gap_ids:
            node_id = f"gap:{gap_id}"
            add_node(node_id, "formal_gap", gap_id)
            add_edge(node_id, primitive_id, "requires_primitive")
        for task_id in row.source_task_ids:
            node_id = f"task:{task_id}"
            task = task_by_id.get(task_id, {})
            declaration = _task_declaration(str(task.get("statement", "")))
            statement_hash = stable_hash(str(task.get("statement", "")))[:16] if task else ""
            add_node(
                node_id,
                "formal_gap_task",
                task_id,
                question_id=str(task.get("question_id", "")),
                problem_class=str(task.get("problem_class", "")),
                theorem_goal_id=str(task.get("theorem_goal_id", "")),
                priority_hint=str(task.get("priority_hint", "")),
                allowed_sorry=task.get("allowed_sorry", None) if task else None,
                declaration=declaration,
                statement_hash=statement_hash,
            )
            add_edge(node_id, primitive_id, "mentions_primitive")
            if declaration:
                skeleton_id = f"theorem_skeleton:{task_id}:{statement_hash}"
                add_node(
                    skeleton_id,
                    "lean_theorem_skeleton",
                    _task_display_name(task_id, task, declaration),
                    declaration=declaration,
                    namespace=str(task.get("namespace", "")),
                    statement_hash=statement_hash,
                    allowed_sorry=task.get("allowed_sorry", None),
                    problem_class=str(task.get("problem_class", "")),
                    theorem_goal_id=str(task.get("theorem_goal_id", "")),
                )
                add_edge(node_id, skeleton_id, "exports_skeleton")
                add_edge(skeleton_id, primitive_id, "requires_primitive")
                add_edge(skeleton_id, action_id, "handled_by_delta_action", total_cost=row.total_cost)
                for goal_id in goal_node_ids:
                    add_edge(goal_id, skeleton_id, "has_lean_skeleton")
                for index, proof_step in enumerate(
                    _proof_strategy_steps(str(task.get("proof_strategy", ""))),
                    start=1,
                ):
                    step_id = f"proof_step:{task_id}:{index}:{stable_hash(proof_step)[:8]}"
                    add_node(
                        step_id,
                        "informal_proof_step",
                        proof_step,
                        task_id=task_id,
                        step_index=index,
                        theorem_skeleton=declaration,
                    )
                    add_edge(skeleton_id, step_id, "has_informal_proof_step", step_index=index)
                    add_edge(step_id, primitive_id, "motivates_primitive")
                    add_edge(step_id, action_id, "handled_by_delta_action", total_cost=row.total_cost)
                    for goal_id in goal_node_ids:
                        add_edge(goal_id, step_id, "has_informal_proof_step", step_index=index)
                for import_name in task.get("imports", []) or []:
                    import_text = str(import_name)
                    if not import_text:
                        continue
                    import_id = f"import:{import_text}"
                    add_node(import_id, "lean_import", import_text)
                    add_edge(skeleton_id, import_id, "imports")
        for obligation in row.bridge_candidate_obligations:
            node_id = f"proof_bank_obligation:{obligation}"
            add_node(node_id, "proof_bank_obligation", obligation)
            add_edge(action_id, node_id, "uses_verified_bridge_candidate")
        for premise in row.expected_premises:
            node_id = f"expected_premise:{premise}"
            add_node(node_id, "expected_premise", premise)
            add_edge(action_id, node_id, "expects_premise")
        for declaration in row.candidate_declarations:
            node_id = f"lean_declaration:{declaration}"
            add_node(node_id, "lean_declaration", declaration)
            add_edge(action_id, node_id, "uses_candidate_declaration")
        for blocker in row.blocked_reasons:
            node_id = f"blocker:{stable_hash([row.primitive, blocker])[:12]}"
            add_node(node_id, "blocker", blocker)
            add_edge(action_id, node_id, "blocked_by")

    node_rows = sorted((asdict(node) for node in nodes.values()), key=lambda row: (row["kind"], row["node_id"]))
    edge_rows = sorted((asdict(edge) for edge in edges.values()), key=lambda row: (row["kind"], row["source"], row["target"]))
    by_node_kind = Counter(str(row["kind"]) for row in node_rows)
    by_edge_kind = Counter(str(row["kind"]) for row in edge_rows)
    return {
        "schema_version": FORMALIZATION_DELTA_PLAN_SCHEMA_VERSION,
        "n_nodes": len(node_rows),
        "n_edges": len(edge_rows),
        "by_node_kind": dict(sorted(by_node_kind.items())),
        "by_edge_kind": dict(sorted(by_edge_kind.items())),
        "nodes": node_rows,
        "edges": edge_rows,
        "graph_fingerprint": stable_hash([node_rows, edge_rows]),
        "limitations": [
            "graph edges are formalization-planning dependencies, not Lean proof dependencies",
            "proof-bank obligation nodes are proof evidence only if separately kernel verified",
            "Lean declaration nodes are retrieval/source evidence only until imported and verified in a proof",
        ],
    }


def _risk_penalty(action_class: str, blocked_reasons: tuple[str, ...], coverage: dict[str, Any]) -> int:
    penalty = min(len(blocked_reasons), 3)
    if action_class == "design_from_first_principles":
        penalty += 2
    if action_class == "design_bridge_lemma":
        penalty += 1
    if coverage and coverage.get("classification") == "no_source_found":
        penalty += 2
    if coverage and coverage.get("classification") == "source_only_not_importable":
        penalty += 1
    return penalty


def _reuse_credit(
    action_class: str,
    bridge_candidates: tuple[str, ...],
    candidate_declarations: tuple[str, ...],
    coverage: dict[str, Any],
) -> int:
    credit = 0
    if bridge_candidates:
        credit += 1
    if candidate_declarations:
        credit += 1
    if coverage.get("proof_bank_exact_match_available"):
        credit += 2
    if action_class == "reuse_exact_proof_bank_obligation":
        credit += 1
    return min(credit, 3)


def _plan_stage(action_class: str) -> str:
    return {
        "reuse_exact_proof_bank_obligation": "reuse_existing_verified_obligation",
        "compose_existing_bridge_chain": "compose_verified_bridge_chain",
        "formalize_assumption_interface": "define_assumption_interface",
        "add_minimal_wrapper": "add_minimal_wrapper",
        "design_bridge_lemma": "prove_new_bridge_lemma",
        "port_external_source": "port_external_lean_source",
        "design_from_first_principles": "design_new_foundational_primitive",
    }.get(action_class, "unknown")


def _delta_kind(action_class: str) -> str:
    return {
        "reuse_exact_proof_bank_obligation": "no_new_declaration",
        "compose_existing_bridge_chain": "theorem_composition",
        "formalize_assumption_interface": "assumption_interface",
        "add_minimal_wrapper": "minimal_wrapper",
        "design_bridge_lemma": "bridge_lemma",
        "port_external_source": "external_port",
        "design_from_first_principles": "new_definition_or_theorem_family",
    }.get(action_class, "unknown")


def _next_step(action_class: str, primitive: str, total_cost: int) -> str:
    if action_class == "reuse_exact_proof_bank_obligation":
        return f"Reuse the existing verified obligation for `{primitive}`; spend effort on the enclosing theorem."
    if action_class == "compose_existing_bridge_chain":
        return f"Compose the verified bridge chain for `{primitive}` into a non-placeholder theorem skeleton."
    if action_class == "formalize_assumption_interface":
        return f"Keep `{primitive}` as an assumption interface; compile the predicate and require downstream theorem use."
    if action_class == "add_minimal_wrapper":
        return f"Add the smallest wrapper theorem for `{primitive}` and verify it with AXLE/local Lean."
    if action_class == "design_bridge_lemma":
        return f"Design one reusable bridge lemma for `{primitive}`; target cost class {total_cost} before full theorem work."
    return f"Start a new primitive-definition plan for `{primitive}`; expect source search plus semantic review before proving."


def _task_declaration(statement: str) -> str:
    match = re.search(r"\btheorem\s+([A-Za-z_][A-Za-z0-9_'.]*)\b", statement)
    return match.group(1) if match else ""


def _task_display_name(task_id: str, task: dict[str, Any], declaration: str) -> str:
    question_id = str(task.get("question_id", ""))
    theorem_goal_id = str(task.get("theorem_goal_id", ""))
    parts = [item for item in (question_id, theorem_goal_id, declaration) if item]
    return ":".join(parts) if parts else task_id


def _proof_strategy_steps(proof_strategy: str) -> tuple[str, ...]:
    pieces = re.split(r"[.;]\s+|\n+", proof_strategy.strip())
    return tuple(piece.strip() for piece in pieces if piece.strip())


def _read_json(path: Path | None, errors: list[str], *, missing_ok: bool = False) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if not missing_ok:
            errors.append(f"missing {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Delta Plan",
        "",
        f"- Proof-bank actions: `{payload.get('proof_bank_actions_dir')}`",
        f"- Primitive-source coverage: `{payload.get('primitive_source_coverage_dir')}`",
        f"- Plan rows: {payload.get('n_ok')}/{payload.get('n_plan_rows')}",
        f"- Total estimated cost: {payload.get('total_estimated_cost')}",
        f"- Low-cost existing reuse: {payload.get('n_low_cost_existing_reuse')}",
        f"- Medium-cost bridge/wrapper: {payload.get('n_medium_cost_bridge_or_wrapper')}",
        f"- High-cost new theory: {payload.get('n_high_cost_new_theory')}",
        f"- Fingerprint: `{payload.get('plan_fingerprint')}`",
        "",
        "This is a library-aware planning artifact. It is not proof evidence.",
        "",
        "## Plan Stages",
        "",
    ]
    for stage, count in (payload.get("by_plan_stage") or {}).items():
        lines.append(f"- `{stage}`: {count}")
    lines.extend(["", "## Theorem Formalization Routes", ""])
    for route in payload.get("theorem_formalization_routes", []):
        if not isinstance(route, dict):
            continue
        lines.append(
            f"- `{route.get('display_name')}`: {route.get('route_class')} "
            f"(cost={route.get('total_estimated_cost')}, "
            f"steps={route.get('n_informal_proof_steps')}, "
            f"primitives={route.get('n_required_primitives')})"
        )
    lines.extend(["", "## Top Low-Cost Rows", ""])
    for row in payload.get("top_low_cost_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('primitive')}`: {row.get('plan_stage')} "
            f"(cost={row.get('total_cost')}, action={row.get('action_class')})"
        )
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
