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
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY as PLANNER_PROOF_EVIDENCE_BOUNDARY,
)


FORMALIZATION_GAP_PLANNER_ROUTE_STABILITY_AUDIT_SCHEMA_VERSION = 1
ROUTE_STABILITY_AUDIT_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-route-stability-audit-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_ROUTE_STABILITY_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner route-stability audit rows make bounded "
    "evidence-expansion decisions over literature, library-grounding, "
    "proof-state, and route-revision artifacts. They are planning evidence, "
    "not theorem proof evidence."
)
HOOK_KINDS = (
    "literature_discovery",
    "formal_library_grounding",
    "lean_library_grounding",
    "proof_state_feedback",
    "route_revision",
    "resource_response_ledger",
)


@dataclass(frozen=True)
class FormalizationGapPlannerRouteStabilityAuditRow:
    schema_version: int
    route_stability_audit_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    stability_decision: str
    stable_under_current_evidence_bound: bool
    needs_more_literature: bool
    needs_more_formal_grounding: bool
    needs_more_lean_grounding: bool
    needs_more_proof_state_feedback: bool
    needs_route_replanning: bool
    response_summary_by_hook: dict[str, dict[str, int]]
    awaiting_hook_kinds: tuple[str, ...]
    rejected_hook_kinds: tuple[str, ...]
    responded_hook_kinds: tuple[str, ...]
    resource_response_awaiting_request_ids: tuple[str, ...]
    resource_response_rejected_request_ids: tuple[str, ...]
    revision_status: str
    original_selected_primitives: tuple[str, ...]
    revised_selected_primitives: tuple[str, ...]
    added_primitives: tuple[str, ...]
    removed_primitives: tuple[str, ...]
    original_delta_primitives: tuple[str, ...]
    revised_delta_primitives: tuple[str, ...]
    added_delta_primitives: tuple[str, ...]
    new_primitives_since_plan: tuple[str, ...]
    source_refs: tuple[str, ...]
    formal_declaration_hits: tuple[dict[str, object], ...]
    lean_declaration_hits: tuple[dict[str, object], ...]
    residual_goals: tuple[str, ...]
    prover_attempt_statuses: tuple[str, ...]
    prover_attempt_classes: tuple[str, ...]
    target_prover_families: tuple[str, ...]
    route_revision_reasons: tuple[str, ...]
    stopping_rule_evidence: tuple[str, ...]
    next_actions: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_route_stability(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    formalization_gap_planner_refinement_evidence_dir: Path,
    formalization_gap_planner_route_revision_overlay_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Audit whether each route should stop expanding or request more evidence."""

    errors: list[str] = []
    plan_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    evidence_path = (
        formalization_gap_planner_refinement_evidence_dir
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    )
    overlay_path = (
        formalization_gap_planner_route_revision_overlay_dir
        / "formalization_gap_planner_route_revision_overlay_manifest.json"
    )
    plan_payload = _read_json(plan_path, errors)
    evidence_payload = _read_json(evidence_path, errors)
    overlay_payload = _read_json(overlay_path, errors)
    if plan_payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("input manifest is not the library-aware formalization gap planner")
    if plan_payload.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("input manifest portable schema id mismatch")

    plan_rows = [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
    evidence_rows = [
        row for row in evidence_payload.get("rows", []) if isinstance(row, dict)
    ]
    overlay_rows = [
        row for row in overlay_payload.get("rows", []) if isinstance(row, dict)
    ]
    evidence_index = _row_index(evidence_rows)
    overlay_index = _row_index(overlay_rows)
    rows = [
        _audit_row(
            plan_row,
            _unique_rows(
                evidence_row
                for key in _row_keys(plan_row)
                for evidence_row in evidence_index.get(key, [])
            ),
            _first(
                _unique_rows(
                    overlay_row
                    for key in _row_keys(plan_row)
                    for overlay_row in overlay_index.get(key, [])
                )
            ),
        )
        for plan_row in plan_rows
    ]
    orphan_overlays = [
        row
        for row in overlay_rows
        if str(row.get("revision_status", "")) == "ORPHAN_ROUTE_REVISION_PROPOSAL"
    ]
    for overlay_row in orphan_overlays:
        rows.append(_orphan_audit_row(overlay_row))

    by_decision = Counter(row.stability_decision for row in rows)
    by_prover_attempt_class = Counter(
        attempt_class
        for row in rows
        for attempt_class in row.prover_attempt_classes
    )
    row_dicts = [asdict(row) for row in rows]
    stability_row_schema = route_stability_audit_row_json_schema()
    row_schema_errors = [
        validate_route_stability_audit_row(row, stability_row_schema)
        for row in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_ROUTE_STABILITY_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_route_stability_audit",
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_path),
        "formalization_gap_planner_refinement_evidence_dir": str(
            formalization_gap_planner_refinement_evidence_dir
        ),
        "formalization_gap_planner_refinement_evidence_manifest": str(evidence_path),
        "formalization_gap_planner_route_revision_overlay_dir": str(
            formalization_gap_planner_route_revision_overlay_dir
        ),
        "formalization_gap_planner_route_revision_overlay_manifest": str(overlay_path),
        "n_plan_rows": len(plan_rows),
        "n_evidence_rows": len(evidence_rows),
        "n_overlay_rows": len(overlay_rows),
        "n_stability_rows": len(rows),
        "n_stable": by_decision.get("ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND", 0),
        "n_needs_expansion": sum(1 for row in rows if not row.stable_under_current_evidence_bound),
        "n_awaiting_responses": by_decision.get("AWAITING_REFINEMENT_RESPONSES", 0),
        "n_repair_response_contract": by_decision.get(
            "REPAIR_REFINEMENT_RESPONSE_CONTRACT", 0
        ),
        "n_apply_route_revision": by_decision.get(
            "APPLY_ROUTE_REVISION_AND_REPLAN", 0
        ),
        "n_expand_literature": by_decision.get("EXPAND_LITERATURE_EVIDENCE", 0),
        "n_expand_formal_grounding": by_decision.get(
            "EXPAND_FORMAL_LIBRARY_GROUNDING", 0
        )
        + by_decision.get("EXPAND_LEAN_LIBRARY_GROUNDING", 0),
        "n_expand_lean_grounding": by_decision.get("EXPAND_LEAN_LIBRARY_GROUNDING", 0),
        "n_expand_proof_state": by_decision.get("EXPAND_PROOF_STATE_FEEDBACK", 0),
        "n_orphan_overlays": len(orphan_overlays),
        "n_new_primitives_since_plan": sum(len(row.new_primitives_since_plan) for row in rows),
        "n_routes_with_residual_goals": sum(1 for row in rows if row.residual_goals),
        "n_routes_with_prover_attempt_class": sum(
            1 for row in rows if row.prover_attempt_classes
        ),
        "target_prover_families": _str_tuple(
            family for row in rows for family in row.target_prover_families
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": len(row_schema_errors) - n_row_schema_valid,
        "row_schema_errors": row_schema_errors,
        "route_stability_audit_row_schema": stability_row_schema,
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and len(row_schema_errors) == n_row_schema_valid
        ),
        "errors": errors,
        "by_stability_decision": dict(sorted(by_decision.items())),
        "by_prover_attempt_class": dict(sorted(by_prover_attempt_class.items())),
        "rows": row_dicts,
        "route_stability_audit_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "bounded_expansion_policy": [
            "stop expanding a route only when queued evidence is present and contract-valid",
            "do not stop if accepted evidence adds route or delta primitives",
            "do not stop if proof-state feedback leaves residual goals",
            "route-stability decisions trigger focused literature, formal-library, proof-state, or replanning work",
        ],
        "limitations": [
            "stability means no new gap-planning information under the current evidence bound",
            "a stable route still requires target-prover replay and kernel verification",
            "missing or weak external tool evidence should be represented as awaiting or expansion decisions",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_route_stability_audit_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_route_stability_audit_row.schema.json"
        ).write_text(json.dumps(stability_row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_route_stability_audit.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_route_stability_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def route_stability_audit_row_json_schema() -> dict[str, object]:
    required = [
        "schema_version",
        "route_stability_audit_id",
        "goal_plan_id",
        "route_id",
        "display_name",
        "stability_decision",
        "stable_under_current_evidence_bound",
        "needs_more_literature",
        "needs_more_formal_grounding",
        "needs_more_lean_grounding",
        "needs_more_proof_state_feedback",
        "needs_route_replanning",
        "response_summary_by_hook",
        "awaiting_hook_kinds",
        "rejected_hook_kinds",
        "responded_hook_kinds",
        "resource_response_awaiting_request_ids",
        "resource_response_rejected_request_ids",
        "revision_status",
        "original_selected_primitives",
        "revised_selected_primitives",
        "added_primitives",
        "removed_primitives",
        "original_delta_primitives",
        "revised_delta_primitives",
        "added_delta_primitives",
        "new_primitives_since_plan",
        "source_refs",
        "formal_declaration_hits",
        "lean_declaration_hits",
        "residual_goals",
        "prover_attempt_statuses",
        "prover_attempt_classes",
        "target_prover_families",
        "route_revision_reasons",
        "stopping_rule_evidence",
        "next_actions",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
        "errors",
    ]
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ROUTE_STABILITY_AUDIT_ROW_SCHEMA_ID,
        "title": "Formalization gap planner route-stability audit row",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_ROUTE_STABILITY_AUDIT_SCHEMA_VERSION,
            },
            "route_stability_audit_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "stability_decision": {
                "type": "string",
                "enum": [
                    "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND",
                    "AWAITING_REFINEMENT_RESPONSES",
                    "REPAIR_REFINEMENT_RESPONSE_CONTRACT",
                    "APPLY_ROUTE_REVISION_AND_REPLAN",
                    "EXPAND_LITERATURE_EVIDENCE",
                    "EXPAND_FORMAL_LIBRARY_GROUNDING",
                    "EXPAND_LEAN_LIBRARY_GROUNDING",
                    "EXPAND_PROOF_STATE_FEEDBACK",
                    "BLOCKED_ROUTE_STABILITY_INPUT",
                ],
            },
            "stable_under_current_evidence_bound": {"type": "boolean"},
            "needs_more_literature": {"type": "boolean"},
            "needs_more_formal_grounding": {"type": "boolean"},
            "needs_more_lean_grounding": {"type": "boolean"},
            "needs_more_proof_state_feedback": {"type": "boolean"},
            "needs_route_replanning": {"type": "boolean"},
            "response_summary_by_hook": {"type": "object"},
            "awaiting_hook_kinds": string_array,
            "rejected_hook_kinds": string_array,
            "responded_hook_kinds": string_array,
            "resource_response_awaiting_request_ids": string_array,
            "resource_response_rejected_request_ids": string_array,
            "revision_status": {"type": "string"},
            "original_selected_primitives": string_array,
            "revised_selected_primitives": string_array,
            "added_primitives": string_array,
            "removed_primitives": string_array,
            "original_delta_primitives": string_array,
            "revised_delta_primitives": string_array,
            "added_delta_primitives": string_array,
            "new_primitives_since_plan": string_array,
            "source_refs": string_array,
            "formal_declaration_hits": object_array,
            "lean_declaration_hits": object_array,
            "residual_goals": string_array,
            "prover_attempt_statuses": string_array,
            "prover_attempt_classes": string_array,
            "target_prover_families": string_array,
            "route_revision_reasons": string_array,
            "stopping_rule_evidence": string_array,
            "next_actions": string_array,
            "proof_evidence_status": {
                "type": "string",
                "const": PROOF_EVIDENCE_STATUS,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_route_stability_audit_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    row_schema = schema or route_stability_audit_row_json_schema()
    required = tuple(row_schema.get("required", ()))
    errors: list[str] = []
    for field_name in required:
        if field_name not in row:
            errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if field_name in row and isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(
                        field_name,
                        row[field_name],
                        field_schema,
                    )
                )
    allowed = set(required)
    for field_name in row:
        if field_name not in allowed:
            errors.append(f"{field_name} unexpected")
    errors.extend(_declaration_hit_scope_errors(row))
    return errors


def _audit_row(
    plan_row: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    overlay_row: dict[str, Any] | None,
) -> FormalizationGapPlannerRouteStabilityAuditRow:
    errors: list[str] = []
    goal_plan_id = str(plan_row.get("goal_plan_id", ""))
    route_id = str(plan_row.get("route_id", ""))
    display_name = str(plan_row.get("display_name", ""))
    for field_name, value in (
        ("goal_plan_id", goal_plan_id),
        ("route_id", route_id),
        ("display_name", display_name),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if overlay_row is None:
        overlay_row = {}
        errors.append("route revision overlay row missing")

    resource_response_summary = _resource_response_summary_from_overlay(overlay_row)
    summary = _merge_resource_response_summary(
        _response_summary_by_hook(evidence_rows),
        resource_response_summary,
    )
    resource_response_awaiting = _str_tuple(
        overlay_row.get("resource_response_awaiting_request_ids", [])
    )
    resource_response_rejected = _str_tuple(
        overlay_row.get("resource_response_rejected_request_ids", [])
    )
    awaiting = _str_tuple(
        [
            *_hook_tuple(
                row
                for row in evidence_rows
                if str(row.get("acceptance_status", ""))
                == "AWAITING_REFINEMENT_TOOL_RESPONSE"
            ),
            "resource_response_ledger" if resource_response_awaiting else "",
        ]
    )
    rejected = _str_tuple(
        [
            *_hook_tuple(
                row
                for row in evidence_rows
                if str(row.get("acceptance_status", "")).startswith("REJECTED_")
            ),
            "resource_response_ledger" if resource_response_rejected else "",
        ]
    )
    responded = _str_tuple(
        [
            *_hook_tuple(row for row in evidence_rows if bool(row.get("response_present"))),
            (
                "resource_response_ledger"
                if resource_response_summary.get("responded", 0)
                else ""
            ),
        ]
    )
    route_revision_recommended = any(
        bool(row.get("route_revision_recommended", False)) for row in evidence_rows
    ) or bool(resource_response_summary.get("route_revision_recommended", 0))
    source_refs = _str_tuple(
        [
            *(
                source
                for row in evidence_rows
                for source in row.get("source_refs", [])
            ),
            *overlay_row.get("source_refs", []),
        ]
    )
    target_prover_families = _target_prover_families_for_audit(
        plan_row,
        evidence_rows,
        overlay_row,
    )
    route_target_prover_family = _primary_target_prover_family(target_prover_families)
    errors.extend(
        _input_declaration_hit_scope_errors(
            [*evidence_rows, overlay_row],
            route_target_prover_family,
        )
    )
    formal_hits = _merge_dicts(
        *(
            _formal_declaration_hits_for_target(row, route_target_prover_family)
            for row in evidence_rows
        ),
        _formal_declaration_hits_for_target(overlay_row, route_target_prover_family),
    )
    lean_hits = _merge_dicts(
        *(
            _lean_declaration_hits_for_target(row, route_target_prover_family)
            for row in evidence_rows
        ),
        _lean_declaration_hits_for_target(overlay_row, route_target_prover_family),
    )
    residual_goals = _str_tuple(
        [
            *(
                residual
                for row in evidence_rows
                for residual in row.get("residual_goals", [])
            ),
            *overlay_row.get("residual_goals", []),
        ]
    )
    prover_statuses = _str_tuple(
        [
            *(row.get("prover_attempt_status", "") for row in evidence_rows),
            *overlay_row.get("applied_prover_attempt_statuses", []),
        ]
    )
    prover_classes = _str_tuple(
        [
            *(
                row.get(
                    "prover_attempt_class",
                    _prover_attempt_class(str(row.get("prover_attempt_status", ""))),
                )
                for row in evidence_rows
            ),
            *overlay_row.get(
                "applied_prover_attempt_classes",
                [
                    _prover_attempt_class(status)
                    for status in overlay_row.get(
                        "applied_prover_attempt_statuses", []
                    )
                ],
            ),
        ]
    )
    revision_status = str(overlay_row.get("revision_status", ""))
    original_selected = _str_tuple(
        overlay_row.get("original_selected_primitives", plan_row.get("selected_primitives", []))
    )
    revised_selected = _str_tuple(
        overlay_row.get("revised_selected_primitives", original_selected)
    )
    added = _str_tuple(overlay_row.get("added_primitives", []))
    removed = _str_tuple(overlay_row.get("removed_primitives", []))
    original_delta = _str_tuple(
        overlay_row.get(
            "original_delta_primitives",
            _node_primitives(plan_row.get("minimal_additional_formalization_nodes", [])),
        )
    )
    revised_delta = _str_tuple(
        overlay_row.get("revised_delta_primitives", original_delta)
    )
    added_delta = _str_tuple(overlay_row.get("added_delta_primitives", []))
    revision_reasons = _str_tuple(
        [
            *overlay_row.get("route_revision_reasons", []),
            *(
                reason
                for evidence_row in evidence_rows
                for reason in evidence_row.get("route_revision_reasons", [])
            ),
        ]
    )
    new_primitives = _str_tuple([*added, *added_delta])
    decision = _stability_decision(
        errors=errors,
        evidence_available=bool(evidence_rows)
        or bool(resource_response_summary.get("queued", 0)),
        awaiting=awaiting,
        rejected=rejected,
        has_literature_hook=_has_hook(evidence_rows, "literature_discovery"),
        has_lean_grounding_hook=_has_any_hook(
            evidence_rows,
            ("formal_library_grounding", "lean_library_grounding"),
        ),
        route_revision_recommended=route_revision_recommended,
        added_primitives=new_primitives,
        residual_goals=residual_goals,
        prover_statuses=prover_statuses,
        prover_classes=prover_classes,
        source_refs=source_refs,
        formal_hits=formal_hits,
    )
    return FormalizationGapPlannerRouteStabilityAuditRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_STABILITY_AUDIT_SCHEMA_VERSION,
        route_stability_audit_id="formalization_gap_planner_route_stability_audit:"
        + stable_hash([goal_plan_id, route_id, display_name, decision, new_primitives])[:16],
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        stability_decision=decision,
        stable_under_current_evidence_bound=decision
        == "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND",
        needs_more_literature=decision == "EXPAND_LITERATURE_EVIDENCE",
        needs_more_formal_grounding=decision
        in {"EXPAND_FORMAL_LIBRARY_GROUNDING", "EXPAND_LEAN_LIBRARY_GROUNDING"},
        needs_more_lean_grounding=decision == "EXPAND_LEAN_LIBRARY_GROUNDING",
        needs_more_proof_state_feedback=decision == "EXPAND_PROOF_STATE_FEEDBACK",
        needs_route_replanning=decision == "APPLY_ROUTE_REVISION_AND_REPLAN",
        response_summary_by_hook=summary,
        awaiting_hook_kinds=awaiting,
        rejected_hook_kinds=rejected,
        responded_hook_kinds=responded,
        resource_response_awaiting_request_ids=resource_response_awaiting,
        resource_response_rejected_request_ids=resource_response_rejected,
        revision_status=revision_status,
        original_selected_primitives=original_selected,
        revised_selected_primitives=revised_selected,
        added_primitives=added,
        removed_primitives=removed,
        original_delta_primitives=original_delta,
        revised_delta_primitives=revised_delta,
        added_delta_primitives=added_delta,
        new_primitives_since_plan=new_primitives,
        source_refs=source_refs,
        formal_declaration_hits=formal_hits,
        lean_declaration_hits=lean_hits,
        residual_goals=residual_goals,
        prover_attempt_statuses=prover_statuses,
        prover_attempt_classes=prover_classes,
        target_prover_families=target_prover_families,
        route_revision_reasons=revision_reasons,
        stopping_rule_evidence=_stopping_rule_evidence(decision, summary, new_primitives, residual_goals),
        next_actions=_next_actions(decision),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _orphan_audit_row(
    overlay_row: dict[str, Any],
) -> FormalizationGapPlannerRouteStabilityAuditRow:
    goal_plan_id = str(overlay_row.get("goal_plan_id", ""))
    route_id = str(overlay_row.get("route_id", ""))
    display_name = str(overlay_row.get("display_name", ""))
    errors = ("orphan route-revision overlay must be matched before stability replay",)
    target_prover_families = _str_tuple(overlay_row.get("target_prover_families", []))
    target_prover_family = _primary_target_prover_family(target_prover_families)
    return FormalizationGapPlannerRouteStabilityAuditRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_STABILITY_AUDIT_SCHEMA_VERSION,
        route_stability_audit_id="formalization_gap_planner_route_stability_audit:"
        + stable_hash([goal_plan_id, route_id, display_name, "orphan"])[:16],
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        stability_decision="BLOCKED_ROUTE_STABILITY_INPUT",
        stable_under_current_evidence_bound=False,
        needs_more_literature=False,
        needs_more_formal_grounding=False,
        needs_more_lean_grounding=False,
        needs_more_proof_state_feedback=False,
        needs_route_replanning=True,
        response_summary_by_hook={hook: _empty_summary() for hook in HOOK_KINDS},
        awaiting_hook_kinds=(),
        rejected_hook_kinds=(),
        responded_hook_kinds=(),
        resource_response_awaiting_request_ids=(),
        resource_response_rejected_request_ids=(),
        revision_status=str(overlay_row.get("revision_status", "")),
        original_selected_primitives=(),
        revised_selected_primitives=_str_tuple(
            overlay_row.get("revised_selected_primitives", [])
        ),
        added_primitives=_str_tuple(overlay_row.get("added_primitives", [])),
        removed_primitives=(),
        original_delta_primitives=(),
        revised_delta_primitives=_str_tuple(
            overlay_row.get("revised_delta_primitives", [])
        ),
        added_delta_primitives=_str_tuple(
            overlay_row.get("added_delta_primitives", [])
        ),
        new_primitives_since_plan=_str_tuple(
            [
                *overlay_row.get("added_primitives", []),
                *overlay_row.get("added_delta_primitives", []),
            ]
        ),
        source_refs=_str_tuple(overlay_row.get("source_refs", [])),
        formal_declaration_hits=_formal_declaration_hits_for_target(
            overlay_row,
            target_prover_family,
        ),
        lean_declaration_hits=_lean_declaration_hits_for_target(
            overlay_row,
            target_prover_family,
        ),
        residual_goals=_str_tuple(overlay_row.get("residual_goals", [])),
        prover_attempt_statuses=_str_tuple(
            overlay_row.get("applied_prover_attempt_statuses", [])
        ),
        prover_attempt_classes=_str_tuple(
            overlay_row.get(
                "applied_prover_attempt_classes",
                [
                    _prover_attempt_class(status)
                    for status in overlay_row.get(
                        "applied_prover_attempt_statuses", []
                    )
                ],
            )
        ),
        target_prover_families=target_prover_families,
        route_revision_reasons=_str_tuple(overlay_row.get("route_revision_reasons", [])),
        stopping_rule_evidence=("orphan route revision cannot be accepted as stable",),
        next_actions=("match the orphan proposal to an active route before replanning",),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=False,
        errors=errors,
    )


def _target_prover_families_for_audit(
    plan_row: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    overlay_row: dict[str, Any],
) -> tuple[str, ...]:
    values: list[object] = [
        plan_row.get("target_prover_family", ""),
        overlay_row.get("target_prover_family", ""),
        *overlay_row.get("target_prover_families", []),
    ]
    for container_name in ("standalone_input_trace", "replan_metadata", "route_summary"):
        container = plan_row.get(container_name, {})
        if isinstance(container, dict):
            values.append(container.get("target_prover_family", ""))
    for row in evidence_rows:
        values.append(row.get("target_prover_family", ""))
        values.extend(_target_prover_family_values_from_declaration_hits(row))
    values.extend(_target_prover_family_values_from_declaration_hits(overlay_row))
    if not any(str(value or "").strip() for value in values):
        if any(
            _dict_tuple(row.get("lean_declaration_hits", []))
            for row in [*evidence_rows, overlay_row]
        ):
            values.append("lean4")
    return _str_tuple(values)


def _target_prover_family_values_from_declaration_hits(
    row: dict[str, Any],
) -> tuple[object, ...]:
    values: list[object] = []
    for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
        values.extend(
            hit.get("target_prover_family", "")
            for hit in _dict_tuple(row.get(field_name, []))
        )
    return tuple(values)


def _primary_target_prover_family(target_prover_families: tuple[str, ...]) -> str:
    for family in target_prover_families:
        text = str(family or "").strip()
        if text:
            return text
    return ""


def _formal_declaration_hits_for_target(
    row: dict[str, Any],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    if "formal_declaration_hits" in row:
        return _dict_tuple(row.get("formal_declaration_hits", []))
    if _is_lean_target_prover(target_prover_family):
        return _dict_tuple(row.get("lean_declaration_hits", []))
    return tuple()


def _lean_declaration_hits_for_target(
    row: dict[str, Any],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    if not _is_lean_target_prover(target_prover_family):
        return tuple()
    if "lean_declaration_hits" in row:
        return _dict_tuple(row.get("lean_declaration_hits", []))
    return _dict_tuple(row.get("formal_declaration_hits", []))


def _declaration_hit_scope_errors(row: dict[str, object]) -> list[str]:
    errors: list[str] = []
    target_families = _str_tuple(row.get("target_prover_families", []))
    target_family = _primary_target_prover_family(target_families)
    target_key = _target_prover_key(target_family)
    if (
        target_key
        and not _is_lean_target_prover(target_family)
        and _dict_tuple(row.get("lean_declaration_hits", []))
    ):
        errors.append(
            "lean_declaration_hits is a Lean-only legacy alias; non-Lean "
            "route stability audit rows must use formal_declaration_hits only"
        )
    errors.extend(
        _declaration_hit_target_mismatch_errors(
            row,
            target_key=target_key,
            target_label="row target_prover_families",
        )
    )
    return errors


def _input_declaration_hit_scope_errors(
    rows: list[dict[str, Any]],
    route_target_prover_family: str,
) -> list[str]:
    errors: list[str] = []
    target_key = _target_prover_key(route_target_prover_family)
    for index, row in enumerate(rows):
        if not row:
            continue
        if (
            target_key
            and not _is_lean_target_prover(route_target_prover_family)
            and _dict_tuple(row.get("lean_declaration_hits", []))
        ):
            errors.append(
                f"input row {index} uses lean_declaration_hits for non-Lean "
                "route stability target"
            )
        errors.extend(
            f"input row {index} {error}"
            for error in _declaration_hit_target_mismatch_errors(
                row,
                target_key=target_key,
                target_label="route target_prover_family",
            )
        )
    return errors


def _declaration_hit_target_mismatch_errors(
    row: dict[str, object],
    *,
    target_key: str,
    target_label: str,
) -> list[str]:
    if not target_key:
        return []
    errors: list[str] = []
    for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
        for index, hit in enumerate(_dict_tuple(row.get(field_name, []))):
            hit_family = str(hit.get("target_prover_family", "") or "").strip()
            if hit_family and _target_prover_key(hit_family) != target_key:
                errors.append(
                    f"{field_name}[{index}].target_prover_family must match "
                    f"{target_label}"
                )
            source_type_family = _declaration_hit_source_type_target_key(hit)
            if (
                not hit_family
                and source_type_family
                and source_type_family != target_key
            ):
                errors.append(
                    f"{field_name}[{index}].source_type implies "
                    f"{source_type_family} but {target_label} is {target_key}"
                )
    return errors


def _merge_dicts(
    *groups: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return _dict_tuple(item for group in groups for item in group)


def _is_lean_target_prover(target_prover_family: str) -> bool:
    key = _target_prover_key(target_prover_family)
    return key in {"lean", "lean4", "lean_4"} or key.startswith(
        ("lean4_", "lean_4_", "lean_")
    )


def _target_prover_key(target_prover_family: object) -> str:
    key = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(target_prover_family).strip().lower(),
    ).strip("_")
    aliases = {
        "coq": "rocq",
        "coq8": "rocq",
        "lean": "lean4",
        "lean_4": "lean4",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(key, key)


def _declaration_hit_source_type_target_key(row: dict[str, object]) -> str:
    source_type = (
        row.get("source_type")
        or row.get("source_kind")
        or row.get("library_family")
        or row.get("source_prover_family")
        or row.get("prover_family")
        or ""
    )
    return _source_type_target_prover_key(source_type)


def _source_type_target_prover_key(value: object) -> str:
    key = _target_prover_key(value)
    if not key:
        return ""
    tokens = {token for token in re.split(r"[^a-z0-9]+", key) if token}
    if key in {"mathlib", "lean4_library"} or {"lean", "lean4", "mathlib"} & tokens:
        return "lean4"
    if key in {"coq", "coq8", "coq_library", "rocq_library"} or {
        "coq",
        "coq8",
        "rocq",
    } & tokens:
        return "rocq"
    if key in {"isabelle_hol", "isabelle_library"} or "isabelle" in tokens:
        return "isabelle"
    if key in {"agda_library"} or "agda" in tokens:
        return "agda"
    return ""


def _stability_decision(
    *,
    errors: list[str],
    evidence_available: bool,
    awaiting: tuple[str, ...],
    rejected: tuple[str, ...],
    has_literature_hook: bool,
    has_lean_grounding_hook: bool,
    route_revision_recommended: bool,
    added_primitives: tuple[str, ...],
    residual_goals: tuple[str, ...],
    prover_statuses: tuple[str, ...],
    prover_classes: tuple[str, ...],
    source_refs: tuple[str, ...],
    formal_hits: tuple[dict[str, object], ...],
) -> str:
    if errors:
        return "BLOCKED_ROUTE_STABILITY_INPUT"
    if not evidence_available or awaiting:
        return "AWAITING_REFINEMENT_RESPONSES"
    if rejected:
        return "REPAIR_REFINEMENT_RESPONSE_CONTRACT"
    if added_primitives or route_revision_recommended:
        return "APPLY_ROUTE_REVISION_AND_REPLAN"
    if (
        residual_goals
        or _failed_prover_statuses(prover_statuses)
        or _failed_prover_classes(prover_classes)
    ):
        return "EXPAND_PROOF_STATE_FEEDBACK"
    if has_literature_hook and not source_refs:
        return "EXPAND_LITERATURE_EVIDENCE"
    if has_lean_grounding_hook and not formal_hits:
        return "EXPAND_FORMAL_LIBRARY_GROUNDING"
    return "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND"


def _failed_prover_statuses(statuses: tuple[str, ...]) -> bool:
    return any(
        status
        for status in statuses
        if status
        not in {
            "local_lean_scaffold_accepted",
            "awaiting_full_route_attempt",
            "no_calibration_signal",
        }
    )


def _failed_prover_classes(classes: tuple[str, ...]) -> bool:
    return any(
        attempt_class
        for attempt_class in classes
        if attempt_class
        not in {
            "target_prover_scaffold_accepted",
            "awaiting_full_route_attempt",
            "no_calibration_signal",
        }
    )


def _prover_attempt_class(attempt_status: str) -> str:
    return {
        "local_lean_scaffold_accepted": "target_prover_scaffold_accepted",
        "local_lean_failed": "target_prover_failed",
        "local_lean_unavailable": "target_prover_unavailable",
        "non_lean_skeleton": "non_target_prover_skeleton",
        "failed_with_residual_goals": "target_prover_failed",
        "placeholder_blocked": "placeholder_blocked",
        "formal_gap_scaffold_blocked": "formal_gap_scaffold_blocked",
        "missing_theorem_skeleton": "missing_theorem_skeleton",
    }.get(attempt_status, attempt_status)


def _response_summary_by_hook(
    evidence_rows: list[dict[str, Any]]
) -> dict[str, dict[str, int]]:
    summary = {hook: _empty_summary() for hook in HOOK_KINDS}
    for row in evidence_rows:
        hook = str(row.get("hook_kind", ""))
        if hook not in summary:
            summary[hook] = _empty_summary()
        summary[hook]["queued"] += 1
        if bool(row.get("response_present", False)):
            summary[hook]["responded"] += 1
        if bool(row.get("response_contract_ok", False)):
            summary[hook]["contract_ok"] += 1
        if str(row.get("acceptance_status", "")) == "AWAITING_REFINEMENT_TOOL_RESPONSE":
            summary[hook]["awaiting"] += 1
        if str(row.get("acceptance_status", "")).startswith("REJECTED_"):
            summary[hook]["rejected"] += 1
    return summary


def _resource_response_summary_from_overlay(
    overlay_row: dict[str, Any],
) -> dict[str, int]:
    raw_summary = overlay_row.get("resource_response_summary", {})
    if not isinstance(raw_summary, dict):
        return _empty_summary()
    summary = _empty_summary()
    for key in ("queued", "responded", "contract_ok", "awaiting", "rejected"):
        value = raw_summary.get(key, 0)
        if isinstance(value, int) and not isinstance(value, bool):
            summary[key] = value
    revision_value = raw_summary.get("route_revision_recommended", 0)
    summary["route_revision_recommended"] = (
        revision_value
        if isinstance(revision_value, int) and not isinstance(revision_value, bool)
        else 0
    )
    return summary


def _merge_resource_response_summary(
    summary: dict[str, dict[str, int]],
    resource_response_summary: dict[str, int],
) -> dict[str, dict[str, int]]:
    merged = {hook: dict(bucket) for hook, bucket in summary.items()}
    bucket = dict(merged.get("resource_response_ledger", _empty_summary()))
    for key in ("queued", "responded", "contract_ok", "awaiting", "rejected"):
        bucket[key] = bucket.get(key, 0) + int(resource_response_summary.get(key, 0))
    merged["resource_response_ledger"] = bucket
    return merged


def _empty_summary() -> dict[str, int]:
    return {"queued": 0, "responded": 0, "contract_ok": 0, "awaiting": 0, "rejected": 0}


def _stopping_rule_evidence(
    decision: str,
    summary: dict[str, dict[str, int]],
    new_primitives: tuple[str, ...],
    residual_goals: tuple[str, ...],
) -> tuple[str, ...]:
    if decision != "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND":
        return (
            f"route did not satisfy stop rule: {decision}",
            f"new_primitives_since_plan={len(new_primitives)}",
            f"residual_goals={len(residual_goals)}",
        )
    responded = sum(bucket["responded"] for bucket in summary.values())
    contract_ok = sum(bucket["contract_ok"] for bucket in summary.values())
    return (
        f"all recorded refinement responses are contract valid: {contract_ok}/{responded}",
        "no accepted refinement evidence added selected or delta primitives",
        "no proof-state residual goals remain in the current evidence round",
    )


def _next_actions(decision: str) -> tuple[str, ...]:
    return {
        "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND": (
            "freeze current route for minimal-delta replay",
            "run target-prover adapter mapping and kernel replay before proof claims",
        ),
        "AWAITING_REFINEMENT_RESPONSES": (
            "run missing refinement or resource-response adapters for queued literature, formal-library, proof-state, or frontier-resource work",
            "rerun refinement evidence and route-stability audit",
        ),
        "REPAIR_REFINEMENT_RESPONSE_CONTRACT": (
            "repair rejected tool or resource responses to the requested response contract",
            "rerun route revision overlay after response repair",
        ),
        "APPLY_ROUTE_REVISION_AND_REPLAN": (
            "accept route-revision overlay as planning state",
            "rerun goal-conditioned minimal formalization planning on the revised route",
        ),
        "EXPAND_LITERATURE_EVIDENCE": (
            "query Paperclip/PaperQA/OpenAlex/Semantic Scholar for source-backed assumptions and lemmas",
            "record source_refs and route_evidence_nodes before revising the DAG",
        ),
        "EXPAND_FORMAL_LIBRARY_GROUNDING": (
            "query local formal-source index and target-prover library search adapters",
            "record declaration hits and coverage_updates before adding new formalization work",
        ),
        "EXPAND_LEAN_LIBRARY_GROUNDING": (
            "query local formal-source index, Lean RAG, LeanSearch, LeanExplore, or Loogle for legacy Lean-only rows",
            "record declaration hits and coverage_updates before adding new formalization work",
        ),
        "EXPAND_PROOF_STATE_FEEDBACK": (
            "materialize non-placeholder Lean theorem skeletons and run proof-state feedback",
            "feed residual goals back into the route revision overlay",
        ),
        "BLOCKED_ROUTE_STABILITY_INPUT": (
            "repair missing route ids, overlay rows, or orphan proposals",
        ),
    }.get(decision, ("review route-stability decision",))


def _row_index(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        for key in _row_keys(row):
            index.setdefault(key, []).append(row)
    return index


def _row_keys(row: dict[str, Any]) -> tuple[str, ...]:
    keys = []
    for field_name in ("route_id", "goal_plan_id", "display_name"):
        value = str(row.get(field_name, ""))
        if value:
            keys.append(f"{field_name}:{value}")
    return tuple(keys)


def _unique_rows(rows: Any) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = stable_hash(row)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def _first(rows: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if not rows:
        return None
    return rows[0]


def _hook_tuple(rows: Any) -> tuple[str, ...]:
    return _str_tuple(row.get("hook_kind", "") for row in rows if isinstance(row, dict))


def _has_hook(rows: list[dict[str, Any]], hook_kind: str) -> bool:
    return any(str(row.get("hook_kind", "")) == hook_kind for row in rows)


def _has_any_hook(rows: list[dict[str, Any]], hook_kinds: tuple[str, ...]) -> bool:
    expected = set(hook_kinds)
    return any(str(row.get("hook_kind", "")) in expected for row in rows)


def _node_primitives(nodes: Any) -> tuple[str, ...]:
    values = []
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            primitive = str(node.get("primitive", "") or node.get("label", ""))
            if primitive:
                values.append(primitive)
    return _str_tuple(values)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return {}


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple, set)):
        try:
            values = tuple(values)
        except TypeError:
            return tuple()
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
    return tuple(rows)


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        try:
            values = tuple(values)
        except TypeError:
            return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


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
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
            return errors
        item_schema = schema.get("items", {})
        if isinstance(item_schema, dict):
            item_type = item_schema.get("type")
            if item_type == "string":
                for index, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(f"{field_name}[{index}] must be string")
            if item_type == "object":
                for index, item in enumerate(value):
                    if not isinstance(item, dict):
                        errors.append(f"{field_name}[{index}] must be object")
    return errors


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Route-Stability Audit",
        "",
        f"- Rows: {payload.get('n_stability_rows')}",
        f"- Stable: {payload.get('n_stable')}",
        f"- Needs expansion: {payload.get('n_needs_expansion')}",
        f"- Apply route revision: {payload.get('n_apply_route_revision')}",
        f"- Expand literature: {payload.get('n_expand_literature')}",
        f"- Expand formal grounding: {payload.get('n_expand_formal_grounding')}",
        f"- Expand Lean grounding (legacy): {payload.get('n_expand_lean_grounding')}",
        f"- Expand proof state: {payload.get('n_expand_proof_state')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Decisions",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` decision={row.get('stability_decision')} "
            f"new={len(row.get('new_primitives_since_plan', []))} "
            f"residual={len(row.get('residual_goals', []))}"
        )
        actions = row.get("next_actions", [])
        if actions:
            lines.append("  next: " + "; ".join(str(item) for item in actions[:2]))
    return "\n".join(lines) + "\n"
