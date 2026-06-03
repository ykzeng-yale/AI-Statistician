from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_SCHEMA_VERSION = 1
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
    route_class: str
    recommended_action: str
    best_route_cost: int
    goal_conditioned_cost: int
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
        _plan_row(route, queue_by_route.get(str(route.get("route_id", "")), {}), all_primitives)
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
    goal_conditioned_cost = max(
        0,
        best_route_cost
        + min(8, import_cone_size // 12)
        + min(6, dependency_depth)
        + 2 * blocker_count
        - trust_credit,
    )
    route_efficiency_score = max(0, 100 - goal_conditioned_cost + 2 * len(existing_reuse))
    do_not_formalize = tuple(
        primitive
        for primitive in all_primitives
        if primitive not in set(selected_primitives)
    )[:8]
    next_packets = _next_packets(minimal_nodes or existing_reuse)
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
        route_class=str(route.get("route_class", "")),
        recommended_action=str(queue_row.get("recommended_action", "")),
        best_route_cost=best_route_cost,
        goal_conditioned_cost=goal_conditioned_cost,
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
        lines.append(f"  summary: {row.get('route_summary')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    return "\n".join(lines) + "\n"
