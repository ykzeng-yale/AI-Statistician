from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner route-revision overlays apply refinement "
    "evidence back to route plans as planning state. They are not theorem proof "
    "evidence. Only target-prover kernel verification can prove a theorem or "
    "bridge lemma."
)


@dataclass(frozen=True)
class FormalizationGapPlannerRouteRevisionOverlayRow:
    schema_version: int
    route_revision_overlay_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    revision_status: str
    original_selected_primitives: tuple[str, ...]
    revised_selected_primitives: tuple[str, ...]
    added_primitives: tuple[str, ...]
    removed_primitives: tuple[str, ...]
    original_delta_primitives: tuple[str, ...]
    revised_delta_primitives: tuple[str, ...]
    added_delta_primitives: tuple[str, ...]
    applied_proposal_ids: tuple[str, ...]
    applied_refinement_evidence_ids: tuple[str, ...]
    applied_hook_kinds: tuple[str, ...]
    route_revision_reasons: tuple[str, ...]
    route_revision_summaries: tuple[str, ...]
    source_refs: tuple[str, ...]
    lean_declaration_hits: tuple[dict[str, object], ...]
    residual_goals: tuple[str, ...]
    revised_informal_knowledge_dag_nodes: tuple[dict[str, object], ...]
    revised_lean_realization_dag_nodes: tuple[dict[str, object], ...]
    next_required_gate: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_route_revision_overlay(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    formalization_gap_planner_refinement_evidence_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Apply accepted refinement evidence as a route-plan overlay."""

    errors: list[str] = []
    plan_manifest_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    evidence_manifest_path = (
        formalization_gap_planner_refinement_evidence_dir
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    )
    plan_payload = _read_json(plan_manifest_path, errors)
    evidence_payload = _read_json(evidence_manifest_path, errors)
    plan_rows = [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
    proposals = [
        row
        for row in evidence_payload.get("route_revision_proposals", [])
        if isinstance(row, dict)
    ]
    proposal_index = _proposal_index(proposals)
    matched_proposal_ids: set[str] = set()
    rows: list[FormalizationGapPlannerRouteRevisionOverlayRow] = []
    for plan_row in plan_rows:
        matched = _match_proposals(plan_row, proposal_index)
        matched_proposal_ids.update(str(row.get("proposal_id", "")) for row in matched)
        rows.append(_overlay_row(plan_row, matched))

    orphan_proposals = [
        proposal
        for proposal in proposals
        if str(proposal.get("proposal_id", "")) not in matched_proposal_ids
    ]
    for proposal in orphan_proposals:
        rows.append(_orphan_overlay_row(proposal))

    by_revision_status = Counter(row.revision_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_route_revision_overlay",
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_manifest_path),
        "formalization_gap_planner_refinement_evidence_dir": str(
            formalization_gap_planner_refinement_evidence_dir
        ),
        "formalization_gap_planner_refinement_evidence_manifest": str(
            evidence_manifest_path
        ),
        "n_plan_rows": len(plan_rows),
        "n_route_revision_proposals": len(proposals),
        "n_orphan_route_revision_proposals": len(orphan_proposals),
        "n_overlay_rows": len(rows),
        "n_routes_with_revision": by_revision_status.get("ROUTE_REVISION_APPLIED", 0),
        "n_routes_without_revision": by_revision_status.get("NO_ROUTE_REVISION_PROPOSAL", 0),
        "n_orphan_rows": by_revision_status.get("ORPHAN_ROUTE_REVISION_PROPOSAL", 0),
        "n_added_primitives": sum(len(row.added_primitives) for row in rows),
        "n_added_delta_primitives": sum(len(row.added_delta_primitives) for row in rows),
        "n_informal_dag_nodes": sum(
            len(row.revised_informal_knowledge_dag_nodes) for row in rows
        ),
        "n_lean_realization_dag_nodes": sum(
            len(row.revised_lean_realization_dag_nodes) for row in rows
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "by_revision_status": dict(sorted(by_revision_status.items())),
        "rows": [asdict(row) for row in rows],
        "route_revision_overlay_fingerprint": stable_hash([asdict(row) for row in rows]),
        "next_required_gate": (
            "rerun goal-conditioned minimal formalization planning, refinement "
            "queue generation, and verifier replay before any proof claim"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "route-revision overlays are planning state, not proof evidence",
            "proposal application is conservative and does not mutate the original planner manifest",
            "kernel proof status still requires target-prover replay and calibration after the revised route is selected",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_route_revision_overlay_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_route_revision_overlay.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_route_revision_overlay.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _overlay_row(
    plan_row: dict[str, Any],
    proposals: list[dict[str, Any]],
) -> FormalizationGapPlannerRouteRevisionOverlayRow:
    original_selected = _str_tuple(plan_row.get("selected_primitives", []))
    original_delta = _str_tuple(
        node.get("primitive", "")
        for node in plan_row.get("minimal_additional_formalization_nodes", [])
        if isinstance(node, dict)
    )
    if not proposals:
        return FormalizationGapPlannerRouteRevisionOverlayRow(
            schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
            route_revision_overlay_id=_overlay_id(plan_row, proposals),
            goal_plan_id=str(plan_row.get("goal_plan_id", "")),
            route_id=str(plan_row.get("route_id", "")),
            display_name=str(plan_row.get("display_name", "")),
            revision_status="NO_ROUTE_REVISION_PROPOSAL",
            original_selected_primitives=original_selected,
            revised_selected_primitives=original_selected,
            added_primitives=(),
            removed_primitives=(),
            original_delta_primitives=original_delta,
            revised_delta_primitives=original_delta,
            added_delta_primitives=(),
            applied_proposal_ids=(),
            applied_refinement_evidence_ids=(),
            applied_hook_kinds=(),
            route_revision_reasons=(),
            route_revision_summaries=(),
            source_refs=(),
            lean_declaration_hits=(),
            residual_goals=(),
            revised_informal_knowledge_dag_nodes=_existing_graph_nodes(
                plan_row.get("informal_knowledge_dag", {})
            ),
            revised_lean_realization_dag_nodes=_existing_graph_nodes(
                plan_row.get("lean_realization_dag", {})
            ),
            next_required_gate="no route revision proposal recorded",
            proof_evidence_status=PROOF_EVIDENCE_STATUS,
            proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
            ok=True,
            errors=(),
        )

    selected_candidates = _nonempty_tuples(
        proposal.get("revised_selected_primitives", []) for proposal in proposals
    )
    delta_candidates = _nonempty_tuples(
        proposal.get("revised_delta_primitives", []) for proposal in proposals
    )
    revised_selected = _prefer_largest_tuple(selected_candidates) or original_selected
    revised_delta = _prefer_largest_tuple(delta_candidates) or original_delta
    informal_nodes = _merge_nodes(
        _existing_graph_nodes(plan_row.get("informal_knowledge_dag", {})),
        *(
            _dict_tuple(proposal.get("revised_informal_knowledge_dag_nodes", []))
            for proposal in proposals
        ),
    )
    lean_nodes = _merge_nodes(
        _existing_graph_nodes(plan_row.get("lean_realization_dag", {})),
        *(
            _dict_tuple(proposal.get("revised_lean_realization_dag_nodes", []))
            for proposal in proposals
        ),
    )
    return FormalizationGapPlannerRouteRevisionOverlayRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
        route_revision_overlay_id=_overlay_id(plan_row, proposals),
        goal_plan_id=str(plan_row.get("goal_plan_id", "")),
        route_id=str(plan_row.get("route_id", "")),
        display_name=str(plan_row.get("display_name", "")),
        revision_status="ROUTE_REVISION_APPLIED",
        original_selected_primitives=original_selected,
        revised_selected_primitives=revised_selected,
        added_primitives=_tuple_diff(revised_selected, original_selected),
        removed_primitives=_tuple_diff(original_selected, revised_selected),
        original_delta_primitives=original_delta,
        revised_delta_primitives=revised_delta,
        added_delta_primitives=_tuple_diff(revised_delta, original_delta),
        applied_proposal_ids=_str_tuple(
            proposal.get("proposal_id", "") for proposal in proposals
        ),
        applied_refinement_evidence_ids=_str_tuple(
            proposal.get("refinement_evidence_id", "") for proposal in proposals
        ),
        applied_hook_kinds=_str_tuple(proposal.get("hook_kind", "") for proposal in proposals),
        route_revision_reasons=_str_tuple(
            reason
            for proposal in proposals
            for reason in proposal.get("route_revision_reasons", [])
        ),
        route_revision_summaries=_str_tuple(
            proposal.get("route_revision_summary", "") for proposal in proposals
        ),
        source_refs=_str_tuple(
            source_ref
            for proposal in proposals
            for source_ref in proposal.get("source_refs", [])
        ),
        lean_declaration_hits=_merge_nodes(
            *(_dict_tuple(proposal.get("lean_declaration_hits", [])) for proposal in proposals)
        ),
        residual_goals=_str_tuple(
            residual
            for proposal in proposals
            for residual in proposal.get("residual_goals", [])
        ),
        revised_informal_knowledge_dag_nodes=informal_nodes,
        revised_lean_realization_dag_nodes=lean_nodes,
        next_required_gate=(
            "rerun goal-conditioned minimal formalization planning and verifier "
            "replay on the revised route overlay"
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=True,
        errors=(),
    )


def _orphan_overlay_row(
    proposal: dict[str, Any],
) -> FormalizationGapPlannerRouteRevisionOverlayRow:
    errors = ("route revision proposal did not match any current plan row",)
    return FormalizationGapPlannerRouteRevisionOverlayRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_SCHEMA_VERSION,
        route_revision_overlay_id="formalization_gap_planner_route_revision_overlay:"
        + stable_hash([proposal])[:16],
        goal_plan_id=str(proposal.get("goal_plan_id", "")),
        route_id=str(proposal.get("route_id", "")),
        display_name=str(proposal.get("display_name", "")),
        revision_status="ORPHAN_ROUTE_REVISION_PROPOSAL",
        original_selected_primitives=(),
        revised_selected_primitives=_str_tuple(proposal.get("revised_selected_primitives", [])),
        added_primitives=_str_tuple(proposal.get("revised_selected_primitives", [])),
        removed_primitives=(),
        original_delta_primitives=(),
        revised_delta_primitives=_str_tuple(proposal.get("revised_delta_primitives", [])),
        added_delta_primitives=_str_tuple(proposal.get("revised_delta_primitives", [])),
        applied_proposal_ids=_str_tuple([proposal.get("proposal_id", "")]),
        applied_refinement_evidence_ids=_str_tuple(
            [proposal.get("refinement_evidence_id", "")]
        ),
        applied_hook_kinds=_str_tuple([proposal.get("hook_kind", "")]),
        route_revision_reasons=_str_tuple(proposal.get("route_revision_reasons", [])),
        route_revision_summaries=_str_tuple([proposal.get("route_revision_summary", "")]),
        source_refs=_str_tuple(proposal.get("source_refs", [])),
        lean_declaration_hits=_dict_tuple(proposal.get("lean_declaration_hits", [])),
        residual_goals=_str_tuple(proposal.get("residual_goals", [])),
        revised_informal_knowledge_dag_nodes=_dict_tuple(
            proposal.get("revised_informal_knowledge_dag_nodes", [])
        ),
        revised_lean_realization_dag_nodes=_dict_tuple(
            proposal.get("revised_lean_realization_dag_nodes", [])
        ),
        next_required_gate="match proposal to an active route plan before replay",
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=False,
        errors=errors,
    )


def _proposal_index(proposals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for proposal in proposals:
        for key in _proposal_keys(proposal):
            index.setdefault(key, []).append(proposal)
    return index


def _match_proposals(
    plan_row: dict[str, Any],
    proposal_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    matched: list[dict[str, Any]] = []
    for key in _plan_keys(plan_row):
        for proposal in proposal_index.get(key, []):
            proposal_id = str(proposal.get("proposal_id", ""))
            if proposal_id in seen:
                continue
            seen.add(proposal_id)
            matched.append(proposal)
    return sorted(
        matched,
        key=lambda proposal: (
            str(proposal.get("hook_kind", "")) != "route_revision",
            -len(_str_tuple(proposal.get("revised_selected_primitives", []))),
            str(proposal.get("proposal_id", "")),
        ),
    )


def _plan_keys(row: dict[str, Any]) -> tuple[str, ...]:
    return _prefixed_keys(
        (
            ("goal_plan_id", row.get("goal_plan_id", "")),
            ("route_id", row.get("route_id", "")),
            ("display_name", row.get("display_name", "")),
        )
    )


def _proposal_keys(row: dict[str, Any]) -> tuple[str, ...]:
    return _prefixed_keys(
        (
            ("goal_plan_id", row.get("goal_plan_id", "")),
            ("route_id", row.get("route_id", "")),
            ("display_name", row.get("display_name", "")),
        )
    )


def _prefixed_keys(values: tuple[tuple[str, Any], ...]) -> tuple[str, ...]:
    return tuple(
        f"{prefix}:{value}"
        for prefix, raw_value in values
        for value in (str(raw_value),)
        if value
    )


def _overlay_id(plan_row: dict[str, Any], proposals: list[dict[str, Any]]) -> str:
    return "formalization_gap_planner_route_revision_overlay:" + stable_hash(
        [
            plan_row.get("goal_plan_id", ""),
            plan_row.get("route_id", ""),
            plan_row.get("display_name", ""),
            [proposal.get("proposal_id", "") for proposal in proposals],
        ]
    )[:16]


def _existing_graph_nodes(graph: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(graph, dict):
        return tuple()
    return _dict_tuple(graph.get("nodes", []))


def _merge_nodes(*node_groups: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    merged: dict[str, dict[str, object]] = {}
    fallback_index = 0
    for nodes in node_groups:
        for node in nodes:
            key = str(node.get("node_id", "")) or str(node.get("declaration", ""))
            if not key:
                key = "node:" + stable_hash([fallback_index, node])[:12]
                fallback_index += 1
            merged[key] = dict(node)
    return tuple(merged[key] for key in sorted(merged))


def _nonempty_tuples(values: Any) -> tuple[tuple[str, ...], ...]:
    return tuple(item for item in (_str_tuple(value) for value in values) if item)


def _prefer_largest_tuple(values: tuple[tuple[str, ...], ...]) -> tuple[str, ...]:
    if not values:
        return tuple()
    return sorted(values, key=lambda item: (-len(item), item))[0]


def _tuple_diff(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    right_set = set(right)
    return tuple(item for item in left if item not in right_set)


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(item for item in values if isinstance(item, dict))


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        try:
            values = tuple(values)
        except TypeError:
            return tuple()
    return tuple(sorted(dict.fromkeys(str(item) for item in values if str(item))))


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
        "# Formalization Gap Planner Route Revision Overlay",
        "",
        f"- Plan rows: {payload.get('n_plan_rows')}",
        f"- Proposals: {payload.get('n_route_revision_proposals')}",
        f"- Routes revised: {payload.get('n_routes_with_revision')}",
        f"- Routes without revision: {payload.get('n_routes_without_revision')}",
        f"- Orphan proposals: {payload.get('n_orphan_route_revision_proposals')}",
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
            f"- `{row.get('display_name')}` status={row.get('revision_status')} "
            f"added={len(row.get('added_primitives', []))} "
            f"proposals={len(row.get('applied_proposal_ids', []))}"
        )
    return "\n".join(lines) + "\n"
