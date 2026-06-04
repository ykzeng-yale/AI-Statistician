from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION = 2
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner refinement evidence records literature search, "
    "Lean-library grounding, prover diagnostics, and route-revision proposals. "
    "These rows may revise the route plan, but they are not theorem proof "
    "evidence. Only target-prover kernel verification can prove a theorem or "
    "bridge lemma."
)


@dataclass(frozen=True)
class FormalizationGapPlannerRefinementEvidenceRow:
    schema_version: int
    refinement_evidence_id: str
    refinement_item_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    hook_kind: str
    refinement_stage: str
    owner_agent: str
    response_present: bool
    response_contract_ok: bool
    evidence_kind: str
    tool_name: str
    source_refs: tuple[str, ...]
    route_evidence_nodes: tuple[dict[str, object], ...]
    lean_declaration_hits: tuple[dict[str, object], ...]
    coverage_updates: dict[str, str]
    prover_diagnostics: tuple[str, ...]
    residual_goals: tuple[str, ...]
    prover_attempt_status: str
    prover_diagnostic_signature: str
    route_revision_summary: str
    revised_selected_primitives: tuple[str, ...]
    revised_delta_primitives: tuple[str, ...]
    revised_informal_knowledge_dag_nodes: tuple[dict[str, object], ...]
    revised_lean_realization_dag_nodes: tuple[dict[str, object], ...]
    route_revision_recommended: bool
    route_revision_reasons: tuple[str, ...]
    acceptance_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_refinement_evidence(
    formalization_gap_planner_refinement_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    response_jsonl: Path | None = None,
) -> dict[str, object]:
    """Validate tool responses to formalization-gap refinement queue rows."""

    errors: list[str] = []
    queue_manifest_path = (
        formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    queue_rows = [row for row in queue_payload.get("rows", []) if isinstance(row, dict)]
    response_jsonl_path = (
        response_jsonl
        if response_jsonl is not None
        else formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    responses, response_file_exists = _read_response_jsonl(response_jsonl_path, errors)
    response_by_item = _match_responses_to_queue_rows(responses, queue_rows, errors)
    rows = [
        _evidence_row(
            queue_row,
            response=response_by_item.get(str(queue_row.get("refinement_item_id", ""))),
        )
        for queue_row in queue_rows
    ]
    by_hook_kind = Counter(row.hook_kind for row in rows)
    by_acceptance_status = Counter(row.acceptance_status for row in rows)
    by_prover_attempt_status = Counter(
        row.prover_attempt_status for row in rows if row.prover_attempt_status
    )
    route_revision_proposals = [
        _route_revision_proposal(row)
        for row in rows
        if row.route_revision_recommended or row.hook_kind == "route_revision"
    ]
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_refinement_evidence",
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir
        ),
        "formalization_gap_planner_refinement_queue_manifest": str(queue_manifest_path),
        "response_jsonl": str(response_jsonl_path),
        "response_jsonl_exists": response_file_exists,
        "n_refinement_items": len(queue_rows),
        "n_responses": len(responses),
        "n_evidence_rows": len(rows),
        "n_response_present": sum(1 for row in rows if row.response_present),
        "n_awaiting_tool_response": sum(
            1 for row in rows if row.acceptance_status == "AWAITING_REFINEMENT_TOOL_RESPONSE"
        ),
        "n_contract_ok": sum(1 for row in rows if row.response_contract_ok),
        "n_literature_evidence": by_hook_kind.get("literature_discovery", 0),
        "n_lean_grounding_evidence": by_hook_kind.get("lean_library_grounding", 0),
        "n_prover_feedback_evidence": by_hook_kind.get("proof_state_feedback", 0),
        "n_route_revision_evidence": by_hook_kind.get("route_revision", 0),
        "n_route_revision_recommended": sum(
            1 for row in rows if row.route_revision_recommended
        ),
        "n_route_revision_proposals": len(route_revision_proposals),
        "n_rejected": sum(1 for row in rows if row.acceptance_status.startswith("REJECTED_")),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_hook_kind": dict(sorted(by_hook_kind.items())),
        "by_acceptance_status": dict(sorted(by_acceptance_status.items())),
        "by_prover_attempt_status": dict(sorted(by_prover_attempt_status.items())),
        "n_prover_attempt_status_records": sum(
            1 for row in rows if row.prover_attempt_status
        ),
        "n_distinct_prover_diagnostic_signatures": len(
            {row.prover_diagnostic_signature for row in rows if row.prover_diagnostic_signature}
        ),
        "rows": [asdict(row) for row in rows],
        "route_revision_proposals": route_revision_proposals,
        "evidence_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "refinement evidence rows are tool-output records, not theorem proof evidence",
            "literature evidence must be attached to informal route DAG nodes before it can justify a route revision",
            "Lean declaration hits and coverage updates are library-grounding evidence, not proof evidence",
            "prover diagnostics are feedback for route repair unless a separate kernel verifier closes the target",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_refinement_evidence.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_route_revision_proposals.jsonl"
        ).write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in route_revision_proposals)
            + ("\n" if route_revision_proposals else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_refinement_evidence.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _evidence_row(
    queue_row: dict[str, Any],
    *,
    response: dict[str, Any] | None,
) -> FormalizationGapPlannerRefinementEvidenceRow:
    refinement_item_id = str(queue_row.get("refinement_item_id", ""))
    goal_plan_id = str(queue_row.get("goal_plan_id", ""))
    route_id = str(queue_row.get("route_id", ""))
    display_name = str(queue_row.get("display_name", ""))
    hook_kind = str(queue_row.get("hook_kind", ""))
    refinement_stage = str(queue_row.get("refinement_stage", ""))
    owner_agent = str(queue_row.get("owner_agent", ""))
    if response is None:
        return FormalizationGapPlannerRefinementEvidenceRow(
            schema_version=FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION,
            refinement_evidence_id=_evidence_id(refinement_item_id, None),
            refinement_item_id=refinement_item_id,
            goal_plan_id=goal_plan_id,
            route_id=route_id,
            display_name=display_name,
            hook_kind=hook_kind,
            refinement_stage=refinement_stage,
            owner_agent=owner_agent,
            response_present=False,
            response_contract_ok=False,
            evidence_kind="",
            tool_name="",
            source_refs=(),
            route_evidence_nodes=(),
            lean_declaration_hits=(),
            coverage_updates={},
            prover_diagnostics=(),
            residual_goals=(),
            prover_attempt_status="",
            prover_diagnostic_signature="",
            route_revision_summary="",
            revised_selected_primitives=(),
            revised_delta_primitives=(),
            revised_informal_knowledge_dag_nodes=(),
            revised_lean_realization_dag_nodes=(),
            route_revision_recommended=False,
            route_revision_reasons=(),
            acceptance_status="AWAITING_REFINEMENT_TOOL_RESPONSE",
            proof_evidence_status="AWAITING_RESPONSE_NOT_PROOF_EVIDENCE",
            proof_evidence_boundary=(
                "No refinement tool response has been recorded. This awaiting "
                "state is not theorem proof evidence."
            ),
            ok=True,
            errors=(),
        )

    errors: list[str] = []
    _require_matching_field(response, queue_row, "refinement_item_id", errors)
    _require_matching_field(response, queue_row, "route_id", errors, required=False)
    _require_matching_field(response, queue_row, "display_name", errors, required=False)
    evidence_kind = str(response.get("evidence_kind", ""))
    tool_name = str(response.get("tool_name", ""))
    if not evidence_kind:
        errors.append("evidence_kind missing")
    if not tool_name:
        errors.append("tool_name missing")
    expected_kind = _expected_evidence_kind(hook_kind)
    if evidence_kind and expected_kind and evidence_kind != expected_kind:
        errors.append(f"evidence_kind {evidence_kind} does not match hook {hook_kind}")

    source_refs = _str_tuple(response.get("source_refs", []))
    route_evidence_nodes = _dict_tuple(response.get("route_evidence_nodes", []))
    lean_declaration_hits = _dict_tuple(response.get("lean_declaration_hits", []))
    coverage_updates = _coverage_updates(response.get("coverage_updates", {}), errors)
    prover_diagnostics = _str_tuple(response.get("prover_diagnostics", []))
    residual_goals = _str_tuple(response.get("residual_goals", []))
    prover_attempt_status = str(response.get("attempt_status", ""))
    route_revision_summary = str(response.get("route_revision_summary", ""))
    revised_selected_primitives = _str_tuple(
        response.get("revised_selected_primitives", [])
    )
    revised_delta_primitives = _str_tuple(response.get("revised_delta_primitives", []))
    revised_informal_nodes = _dict_tuple(
        response.get("revised_informal_knowledge_dag_nodes", [])
    )
    revised_lean_nodes = _dict_tuple(response.get("revised_lean_realization_dag_nodes", []))
    route_revision_recommended = bool(response.get("route_revision_recommended", False))
    route_revision_reasons = _str_tuple(response.get("route_revision_reasons", []))
    prover_diagnostic_signature = _prover_diagnostic_signature(
        prover_attempt_status,
        prover_diagnostics,
        residual_goals,
        route_revision_reasons,
    )
    if "route_revision_recommended" in response and not isinstance(
        response.get("route_revision_recommended"),
        bool,
    ):
        errors.append("route_revision_recommended must be boolean")

    if hook_kind == "literature_discovery":
        if not source_refs:
            errors.append("source_refs missing for literature_discovery")
        if not route_evidence_nodes:
            errors.append("route_evidence_nodes missing for literature_discovery")
    elif hook_kind == "lean_library_grounding":
        if not lean_declaration_hits:
            errors.append("lean_declaration_hits missing for lean_library_grounding")
        if not coverage_updates:
            errors.append("coverage_updates missing for lean_library_grounding")
    elif hook_kind == "proof_state_feedback":
        if not prover_diagnostics and not residual_goals:
            errors.append(
                "prover_diagnostics or residual_goals required for proof_state_feedback"
            )
    elif hook_kind == "route_revision":
        if not route_revision_summary:
            errors.append("route_revision_summary missing for route_revision")
        if not revised_selected_primitives and not revised_delta_primitives:
            errors.append(
                "revised_selected_primitives or revised_delta_primitives required for route_revision"
            )
        route_revision_recommended = True
    else:
        errors.append(f"unsupported hook_kind: {hook_kind}")

    if route_revision_recommended and not route_revision_reasons:
        errors.append("route_revision_reasons missing when route_revision_recommended")
    acceptance_status = (
        "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE"
        if not errors
        else "REJECTED_REFINEMENT_EVIDENCE_CONTRACT"
    )
    return FormalizationGapPlannerRefinementEvidenceRow(
        schema_version=FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_SCHEMA_VERSION,
        refinement_evidence_id=_evidence_id(refinement_item_id, response),
        refinement_item_id=refinement_item_id,
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        hook_kind=hook_kind,
        refinement_stage=refinement_stage,
        owner_agent=owner_agent,
        response_present=True,
        response_contract_ok=not errors,
        evidence_kind=evidence_kind,
        tool_name=tool_name,
        source_refs=source_refs,
        route_evidence_nodes=route_evidence_nodes,
        lean_declaration_hits=lean_declaration_hits,
        coverage_updates=coverage_updates,
        prover_diagnostics=prover_diagnostics,
        residual_goals=residual_goals,
        prover_attempt_status=prover_attempt_status,
        prover_diagnostic_signature=prover_diagnostic_signature,
        route_revision_summary=route_revision_summary,
        revised_selected_primitives=revised_selected_primitives,
        revised_delta_primitives=revised_delta_primitives,
        revised_informal_knowledge_dag_nodes=revised_informal_nodes,
        revised_lean_realization_dag_nodes=revised_lean_nodes,
        route_revision_recommended=route_revision_recommended,
        route_revision_reasons=route_revision_reasons,
        acceptance_status=acceptance_status,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _route_revision_proposal(
    row: FormalizationGapPlannerRefinementEvidenceRow,
) -> dict[str, object]:
    return {
        "proposal_id": "formalization_gap_planner_route_revision:"
        + stable_hash([row.refinement_evidence_id, row.route_revision_reasons])[:16],
        "refinement_evidence_id": row.refinement_evidence_id,
        "refinement_item_id": row.refinement_item_id,
        "goal_plan_id": row.goal_plan_id,
        "route_id": row.route_id,
        "display_name": row.display_name,
        "hook_kind": row.hook_kind,
        "route_revision_summary": row.route_revision_summary,
        "route_revision_reasons": row.route_revision_reasons,
        "revised_selected_primitives": row.revised_selected_primitives,
        "revised_delta_primitives": row.revised_delta_primitives,
        "revised_informal_knowledge_dag_nodes": row.revised_informal_knowledge_dag_nodes,
        "revised_lean_realization_dag_nodes": row.revised_lean_realization_dag_nodes,
        "source_refs": row.source_refs,
        "lean_declaration_hits": row.lean_declaration_hits,
        "residual_goals": row.residual_goals,
        "prover_attempt_status": row.prover_attempt_status,
        "prover_diagnostic_signature": row.prover_diagnostic_signature,
        "required_gate": (
            "rerun goal-conditioned minimal formalization planning and replay "
            "before treating this revision as proof-relevant"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _expected_evidence_kind(hook_kind: str) -> str:
    return {
        "literature_discovery": "literature_route_evidence",
        "lean_library_grounding": "lean_library_grounding",
        "proof_state_feedback": "prover_feedback",
        "route_revision": "route_revision_proposal",
    }.get(hook_kind, "")


def _match_responses_to_queue_rows(
    responses: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    known_ids = {
        str(row.get("refinement_item_id", ""))
        for row in queue_rows
        if str(row.get("refinement_item_id", ""))
    }
    matched: dict[str, dict[str, Any]] = {}
    for response in responses:
        response_id = str(response.get("refinement_item_id", ""))
        if not response_id:
            errors.append("response missing refinement_item_id")
            continue
        if response_id not in known_ids:
            errors.append(f"response references unknown refinement_item_id: {response_id}")
            continue
        if response_id in matched:
            errors.append(f"duplicate response for refinement_item_id: {response_id}")
            continue
        matched[response_id] = response
    return matched


def _require_matching_field(
    response: dict[str, Any],
    queue_row: dict[str, Any],
    field_name: str,
    errors: list[str],
    *,
    required: bool = True,
) -> None:
    response_value = str(response.get(field_name, ""))
    queue_value = str(queue_row.get(field_name, ""))
    if required and not response_value:
        errors.append(f"{field_name} missing")
    if response_value and queue_value and response_value != queue_value:
        errors.append(
            f"{field_name} mismatch: response={response_value} queue={queue_value}"
        )


def _coverage_updates(values: Any, errors: list[str]) -> dict[str, str]:
    if not isinstance(values, dict):
        if values:
            errors.append("coverage_updates must be an object")
        return {}
    return {str(key): str(value) for key, value in values.items() if str(key) and str(value)}


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(item for item in values if isinstance(item, dict))


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
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


def _read_response_jsonl(path: Path, errors: list[str]) -> tuple[list[dict[str, Any]], bool]:
    if not path.exists():
        return [], False
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse response line {line_no}: {type(exc).__name__}: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"response line {line_no} is not an object")
            continue
        rows.append(payload)
    return rows, True


def _evidence_id(refinement_item_id: str, response: dict[str, Any] | None) -> str:
    return "formalization_gap_planner_refinement_evidence:" + stable_hash(
        [refinement_item_id, response or {}]
    )[:16]


def _prover_diagnostic_signature(
    attempt_status: str,
    diagnostics: tuple[str, ...],
    residual_goals: tuple[str, ...],
    route_revision_reasons: tuple[str, ...],
) -> str:
    if not attempt_status and not diagnostics and not residual_goals:
        return ""
    return "prover_diagnostic_signature:" + stable_hash(
        [
            attempt_status,
            tuple(item[:200] for item in diagnostics[:8]),
            tuple(item[:200] for item in residual_goals[:8]),
            tuple(item[:200] for item in route_revision_reasons[:8]),
        ]
    )[:16]


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Refinement Evidence",
        "",
        f"- Refinement items: {payload.get('n_refinement_items')}",
        f"- Responses: {payload.get('n_responses')}",
        f"- Contract OK: {payload.get('n_contract_ok')}",
        f"- Awaiting tool response: {payload.get('n_awaiting_tool_response')}",
        f"- Route revision recommended: {payload.get('n_route_revision_recommended')}",
        f"- Route revision proposals: {payload.get('n_route_revision_proposals')}",
        f"- Prover attempt statuses: {payload.get('by_prover_attempt_status')}",
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
            f"- `{row.get('display_name')}` {row.get('hook_kind')} "
            f"status={row.get('acceptance_status')} "
            f"attempt={row.get('prover_attempt_status') or 'n/a'} "
            f"revision={row.get('route_revision_recommended')}"
        )
        if row.get("route_revision_reasons"):
            lines.append(
                "  revision reasons: "
                + ", ".join(str(item) for item in row.get("route_revision_reasons", [])[:6])
            )
    return "\n".join(lines) + "\n"
