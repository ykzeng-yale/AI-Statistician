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


FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_FEEDBACK_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_FEEDBACK_ADAPTER_NOT_PROOF_EVIDENCE"
)
ADAPTER_TOOL_NAME = "target_prover_adapter_feedback_adapter"
CONTRACT_RESPONSE_VALIDATION_JSONL = (
    "formalization_gap_planner_prover_adapter_response_validation.jsonl"
)
CROSS_PROVER_RESPONSE_VALIDATION_JSONL = (
    "formalization_gap_planner_cross_prover_response_validation.jsonl"
)


def export_formalization_gap_planner_prover_adapter_feedback_responses(
    formalization_gap_planner_refinement_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_prover_adapter_contract_dir: Path | None = None,
    formalization_gap_planner_cross_prover_matrix_audit_dir: Path | None = None,
    base_response_jsonl: Path | None = None,
    target_prover_family: str = "",
    max_items: int = 0,
) -> dict[str, object]:
    """Convert target-prover adapter validation rows into refinement responses."""

    errors: list[str] = []
    queue_manifest_path = (
        formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    queue_rows = [
        row for row in queue_payload.get("rows", []) if isinstance(row, dict)
    ]
    if max_items > 0:
        queue_rows = queue_rows[:max_items]
    proof_rows = [
        row for row in queue_rows if str(row.get("hook_kind", "")) == "proof_state_feedback"
    ]
    base_responses = _read_jsonl(base_response_jsonl, errors) if base_response_jsonl else []
    validation_sources = _validation_source_paths(
        formalization_gap_planner_prover_adapter_contract_dir,
        formalization_gap_planner_cross_prover_matrix_audit_dir,
    )
    if not validation_sources:
        errors.append(
            "at least one prover-adapter contract or cross-prover matrix audit "
            "directory is required"
        )
    validation_rows = [
        row
        for path in validation_sources
        for row in _read_jsonl(path, errors)
        if _target_filter_allows(row, target_prover_family)
    ]
    generated_responses = [
        _feedback_response(row, matches)
        for row in proof_rows
        for matches in [_matching_validation_rows(row, validation_rows)]
        if matches
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
    by_mapping_status = Counter(str(row.get("mapping_status", "")) for row in validation_rows)
    by_acceptance_status = Counter(
        str(row.get("acceptance_status", "")) for row in validation_rows
    )
    by_target = Counter(str(row.get("target_prover_family", "")) for row in validation_rows)
    by_attempt_status = Counter(
        str(row.get("attempt_status", "")) for row in generated_responses
    )
    by_attempt_class = Counter(
        str(row.get("prover_attempt_class", "")) for row in generated_responses
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_FEEDBACK_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_prover_adapter_feedback_adapter",
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir
        ),
        "formalization_gap_planner_refinement_queue_manifest": str(queue_manifest_path),
        "formalization_gap_planner_prover_adapter_contract_dir": str(
            formalization_gap_planner_prover_adapter_contract_dir or ""
        ),
        "formalization_gap_planner_cross_prover_matrix_audit_dir": str(
            formalization_gap_planner_cross_prover_matrix_audit_dir or ""
        ),
        "validation_source_jsonl": tuple(str(path) for path in validation_sources),
        "base_response_jsonl": str(base_response_jsonl or ""),
        "target_prover_family_filter": _normalize_target(target_prover_family),
        "max_items": max_items,
        "n_queue_rows": len(queue_rows),
        "n_proof_state_feedback_rows": len(proof_rows),
        "n_validation_sources": len(validation_sources),
        "n_validation_rows": len(validation_rows),
        "n_validation_rows_with_response": sum(
            1 for row in validation_rows if bool(row.get("response_present", False))
        ),
        "n_validation_rows_contract_ok": sum(
            1 for row in validation_rows if bool(row.get("response_contract_ok", False))
        ),
        "n_base_responses": len(base_responses),
        "n_generated_feedback_responses": len(generated_responses),
        "n_merged_responses": len(merged_responses),
        "n_matched_proof_state_feedback_rows": len(matched_item_ids),
        "n_unmatched_proof_state_feedback_rows": max(
            0,
            len(proof_rows) - len(matched_item_ids),
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
        "by_mapping_status": dict(sorted(by_mapping_status.items())),
        "by_acceptance_status": dict(sorted(by_acceptance_status.items())),
        "by_target_prover_family": dict(sorted(by_target.items())),
        "by_attempt_status": dict(sorted(by_attempt_status.items())),
        "by_prover_attempt_class": dict(sorted(by_attempt_class.items())),
        "all_ok": not errors
        and bool(generated_responses)
        and n_generated_schema_valid == len(generated_responses)
        and n_merged_schema_valid == len(merged_responses),
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
            "target-prover adapter feedback is route-repair evidence, not theorem proof evidence",
            "ready_for_kernel_attempt means a target adapter produced a replay candidate; only the target prover kernel can certify it",
            "translation gaps and unsupported primitives revise the route unless a later source-backed repair resolves them",
            "cross-prover feedback may intentionally target a prover family different from the source queue row",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = (
            out_dir
            / "formalization_gap_planner_prover_adapter_feedback_adapter_manifest.json"
        )
        responses_path = (
            out_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        )
        generated_responses_path = (
            out_dir
            / "formalization_gap_planner_prover_adapter_feedback_responses.jsonl"
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
            / "formalization_gap_planner_prover_adapter_feedback_adapter.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _feedback_response(
    queue_row: dict[str, Any],
    validation_rows: list[dict[str, Any]],
) -> dict[str, object]:
    summary = _attempt_summary(validation_rows)
    target_primitives = _str_tuple(queue_row.get("target_primitives", []))
    revision_recommended = bool(summary["route_revision_recommended"])
    return {
        "refinement_item_id": str(queue_row.get("refinement_item_id", "")),
        "route_id": str(queue_row.get("route_id", "")),
        "display_name": str(queue_row.get("display_name", "")),
        "evidence_kind": "prover_feedback",
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
        "target_prover_family": summary["target_prover_family"],
        "prover_adapter_id": ADAPTER_TOOL_NAME,
        "attempt_status": summary["attempt_status"],
        "prover_attempt_class": summary["prover_attempt_class"],
        "prover_diagnostics": tuple(summary["diagnostics"]),
        "residual_goals": tuple(summary["residual_goals"]),
        "route_revision_recommended": revision_recommended,
        "route_revision_reasons": tuple(summary["route_revision_reasons"]),
        "route_revision_summary": summary["route_revision_summary"],
        "revised_delta_primitives": target_primitives if revision_recommended else tuple(),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _attempt_summary(validation_rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {str(row.get("mapping_status", "")) for row in validation_rows}
    targets = {
        str(row.get("target_prover_family", "")).strip()
        for row in validation_rows
        if str(row.get("target_prover_family", "")).strip()
    }
    primitives = {
        str(row.get("primitive", "")).strip()
        for row in validation_rows
        if str(row.get("primitive", "")).strip()
    }
    diagnostics = _diagnostics(validation_rows)
    residual_goals = _residual_goals(validation_rows)
    reasons = _route_revision_reasons(validation_rows)
    rejected = any(
        bool(row.get("response_present", False))
        and (
            str(row.get("acceptance_status", "")).startswith("REJECTED_")
            or not bool(row.get("response_contract_ok", False))
        )
        for row in validation_rows
    )
    awaiting = any(
        not bool(row.get("response_present", False))
        or str(row.get("acceptance_status", "")) == "AWAITING_PROVER_ADAPTER_MAPPING"
        for row in validation_rows
    )
    if rejected:
        attempt_status = "prover_adapter_mapping_rejected"
        prover_attempt_class = "target_prover_mapping_contract_rejected"
        route_revision_recommended = True
    elif any(status == "unsupported_in_target_prover" for status in statuses):
        attempt_status = "prover_adapter_unsupported_in_target_prover"
        prover_attempt_class = "target_prover_unsupported"
        route_revision_recommended = True
    elif any(status == "needs_statement_translation" for status in statuses):
        attempt_status = "prover_adapter_needs_statement_translation"
        prover_attempt_class = "target_prover_mapping_gap"
        route_revision_recommended = True
    elif any(status == "needs_library_grounding" for status in statuses):
        attempt_status = "prover_adapter_needs_library_grounding"
        prover_attempt_class = "target_prover_mapping_gap"
        route_revision_recommended = True
    elif any(status == "needs_human_review" for status in statuses):
        attempt_status = "prover_adapter_needs_human_review"
        prover_attempt_class = "target_prover_mapping_gap"
        route_revision_recommended = True
    elif all(
        bool(row.get("response_contract_ok", False))
        and str(row.get("mapping_status", "")) == "ready_for_kernel_attempt"
        for row in validation_rows
    ):
        attempt_status = "prover_adapter_ready_for_kernel_attempt"
        prover_attempt_class = "target_prover_mapping_ready"
        route_revision_recommended = False
    elif awaiting:
        attempt_status = "awaiting_prover_adapter_mapping"
        prover_attempt_class = "target_prover_mapping_awaiting"
        route_revision_recommended = bool(reasons)
    else:
        attempt_status = "awaiting_prover_adapter_mapping"
        prover_attempt_class = "target_prover_mapping_awaiting"
        route_revision_recommended = bool(residual_goals or reasons)
    if not diagnostics:
        diagnostics = ["target-prover adapter validation row matched queue item"]
    if route_revision_recommended and not reasons:
        reasons = ["target-prover adapter feedback requires route repair"]
    return {
        "target_prover_family": next(iter(targets)) if len(targets) == 1 else "multi_target",
        "attempt_status": attempt_status,
        "prover_attempt_class": prover_attempt_class,
        "diagnostics": tuple(sorted(dict.fromkeys(diagnostics))),
        "residual_goals": tuple(sorted(dict.fromkeys(residual_goals))),
        "route_revision_recommended": route_revision_recommended,
        "route_revision_reasons": tuple(sorted(dict.fromkeys(reasons))),
        "route_revision_summary": _route_revision_summary(
            attempt_status,
            targets,
            primitives,
        ),
    }


def _diagnostics(validation_rows: list[dict[str, Any]]) -> list[str]:
    diagnostics: list[str] = []
    for row in validation_rows:
        target = str(row.get("target_prover_family", "")).strip() or "target"
        primitive = str(row.get("primitive", "")).strip() or "primitive"
        mapping_status = str(row.get("mapping_status", "")).strip()
        acceptance_status = str(row.get("acceptance_status", "")).strip()
        diagnostics.append(
            f"{target}:{primitive} mapping_status={mapping_status} "
            f"acceptance_status={acceptance_status}"
        )
        notes = str(row.get("semantic_alignment_notes", "")).strip()
        if notes:
            diagnostics.append(f"{target}:{primitive} semantic_alignment_notes={notes[:500]}")
        statement = str(row.get("translated_statement", "")).strip()
        if statement:
            diagnostics.append(f"{target}:{primitive} translated_statement={statement[:500]}")
        verifier = str(row.get("verifier_command", "")).strip()
        if verifier:
            diagnostics.append(f"{target}:{primitive} verifier_command={verifier}")
        for error in _str_tuple(row.get("errors", [])):
            diagnostics.append(f"{target}:{primitive} validation_error={error[:500]}")
    return diagnostics


def _residual_goals(validation_rows: list[dict[str, Any]]) -> list[str]:
    residuals: list[str] = []
    for row in validation_rows:
        target = str(row.get("target_prover_family", "")).strip() or "target"
        primitive = str(row.get("primitive", "")).strip() or "primitive"
        gaps = _str_tuple(row.get("residual_translation_gaps", []))
        for gap in gaps:
            residuals.append(f"{target}:{primitive}: {gap}")
        if not bool(row.get("response_present", False)):
            residuals.append(f"{target}:{primitive}: awaiting prover adapter mapping")
        if str(row.get("acceptance_status", "")).startswith("REJECTED_"):
            residuals.append(
                f"{target}:{primitive}: prover adapter mapping contract rejected"
            )
        if bool(row.get("response_present", False)) and not bool(
            row.get("response_contract_ok", False)
        ):
            residuals.append(f"{target}:{primitive}: response contract not satisfied")
    return residuals


def _route_revision_reasons(validation_rows: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for row in validation_rows:
        target = str(row.get("target_prover_family", "")).strip() or "target"
        primitive = str(row.get("primitive", "")).strip() or "primitive"
        mapping_status = str(row.get("mapping_status", "")).strip()
        if mapping_status == "needs_statement_translation":
            reasons.append(
                "target prover adapter needs statement translation for "
                f"{primitive} in {target}"
            )
        elif mapping_status == "needs_library_grounding":
            reasons.append(
                f"target prover adapter needs library grounding for {primitive} in {target}"
            )
        elif mapping_status == "unsupported_in_target_prover":
            reasons.append(
                f"target prover adapter reports unsupported primitive {primitive} in {target}"
            )
        elif mapping_status == "needs_human_review":
            reasons.append(
                f"target prover adapter needs human review for {primitive} in {target}"
            )
        if str(row.get("acceptance_status", "")).startswith("REJECTED_") or (
            bool(row.get("response_present", False))
            and not bool(row.get("response_contract_ok", False))
        ):
            reasons.append(
                f"target prover adapter mapping contract rejected for {primitive} in {target}"
            )
        if _str_tuple(row.get("residual_translation_gaps", [])):
            reasons.append(
                f"target prover adapter residual translation gaps for {primitive} in {target}"
            )
    return reasons


def _route_revision_summary(
    attempt_status: str,
    targets: set[str],
    primitives: set[str],
) -> str:
    target_text = ", ".join(sorted(targets)) if targets else "target prover"
    primitive_text = ", ".join(sorted(primitives)) if primitives else "queued primitive"
    return (
        f"Target-prover adapter feedback for {primitive_text} in {target_text}: "
        f"{attempt_status}."
    )


def _matching_validation_rows(
    queue_row: dict[str, Any],
    validation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matches = [
        row for row in validation_rows if _validation_matches_queue_row(row, queue_row)
    ]
    return sorted(
        matches,
        key=lambda row: (
            str(row.get("target_prover_family", "")),
            str(row.get("route_id", "")),
            str(row.get("goal_plan_id", "")),
            str(row.get("primitive", "")),
            str(row.get("response_validation_id", "")),
        ),
    )


def _validation_matches_queue_row(
    validation_row: dict[str, Any],
    queue_row: dict[str, Any],
) -> bool:
    queue_route = str(queue_row.get("route_id", "")).strip()
    validation_route = str(validation_row.get("route_id", "")).strip()
    queue_goal = str(queue_row.get("goal_plan_id", "")).strip()
    validation_goal = str(validation_row.get("goal_plan_id", "")).strip()
    primitive = _normalize_primitive(str(validation_row.get("primitive", "")))
    queue_primitives = {
        _normalize_primitive(item) for item in _str_tuple(queue_row.get("target_primitives", []))
    }
    if queue_route and validation_route and queue_route != validation_route:
        return False
    if queue_goal and validation_goal and queue_goal != validation_goal:
        return False
    if queue_primitives and primitive and primitive not in queue_primitives:
        return False
    has_route_anchor = bool(queue_route and validation_route and queue_route == validation_route)
    has_goal_anchor = bool(queue_goal and validation_goal and queue_goal == validation_goal)
    has_primitive_anchor = bool(queue_primitives and primitive in queue_primitives)
    return has_route_anchor or has_goal_anchor or has_primitive_anchor


def _validation_source_paths(
    contract_dir: Path | None,
    cross_prover_matrix_audit_dir: Path | None,
) -> tuple[Path, ...]:
    paths: list[Path] = []
    if contract_dir is not None:
        paths.append(contract_dir / CONTRACT_RESPONSE_VALIDATION_JSONL)
    if cross_prover_matrix_audit_dir is not None:
        paths.append(cross_prover_matrix_audit_dir / CROSS_PROVER_RESPONSE_VALIDATION_JSONL)
    return tuple(paths)


def _target_filter_allows(
    row: dict[str, Any],
    target_prover_family: str,
) -> bool:
    target_filter = _normalize_target(target_prover_family)
    if not target_filter:
        return True
    return _normalize_target(str(row.get("target_prover_family", ""))) == target_filter


def _normalize_target(raw_target: str) -> str:
    normalized = str(raw_target).strip().lower()
    aliases = {
        "lean": "lean4",
        "lean4": "lean4",
        "coq": "rocq",
        "rocq": "rocq",
        "isabelle/hol": "isabelle",
        "isabelle": "isabelle",
        "agda": "agda",
        "other": "other",
    }
    return aliases.get(normalized, normalized)


def _normalize_primitive(raw: str) -> str:
    return str(raw).strip().lower().replace("-", "_").replace(" ", "_")


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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Prover-Adapter Feedback Adapter",
        "",
        f"- Queue rows: {payload.get('n_queue_rows')}",
        f"- Proof-state feedback rows: {payload.get('n_proof_state_feedback_rows')}",
        f"- Validation rows: {payload.get('n_validation_rows')}",
        f"- Generated responses: {payload.get('n_generated_feedback_responses')}",
        f"- Merged responses: {payload.get('n_merged_responses')}",
        f"- Response schema valid: {payload.get('n_response_schema_valid')}/{payload.get('n_generated_feedback_responses')}",
        f"- Route revisions recommended: {payload.get('n_route_revision_recommended')}",
        f"- Mapping statuses: {payload.get('by_mapping_status')}",
        f"- Attempt statuses: {payload.get('by_attempt_status')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Generated Responses",
        "",
    ]
    for row in payload.get("responses", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` target={row.get('target_prover_family')} "
            f"attempt={row.get('attempt_status')} "
            f"revision={row.get('route_revision_recommended')}"
        )
    return "\n".join(lines) + "\n"
