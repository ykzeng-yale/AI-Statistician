from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


PRESCRIPTIVE_REPAIR_FIELDS = frozenset(
    {
        "candidate_reroute_options",
        "next_action",
        "preferred_tool_order",
        "proof_state_workflow",
        "recommended_action",
        "recommended_actions",
        "recommended_capability_eval_command",
        "recommended_command",
        "recommended_commands",
        "recommended_next_action",
        "recommended_repair",
        "recommended_repairs",
        "recommended_repair_tasks",
        "recommended_tools",
        "repair_instructions",
        "repair_policy",
        "repair_strategy",
        "required_action",
        "required_architect_behavior",
        "required_behavior",
        "required_change",
        "required_repair",
        "required_resolution",
        "required_revision",
        "semantic_reviewer_required_change",
        "source_repair_strategy",
        "suggested_fix",
        "target_behavior",
        "target_drift_repair_contract",
        "target_shape_contract",
        "unknown_identifier_grounding_requests",
        "validation_issue_repair_actions",
    }
)


def model_observations_without_repair_recipes(
    value: Any,
    *,
    preserve_exact_keys: Sequence[str] = ("rejected_candidate",),
) -> Any:
    """Remove prescriptive edits while preserving raw candidate observations."""

    preserved = frozenset(str(key) for key in preserve_exact_keys)

    def project(child: Any, *, parent_key: str = "") -> Any:
        if parent_key in preserved:
            return deepcopy(child)
        if isinstance(child, Mapping):
            return {
                str(key): project(item, parent_key=str(key))
                for key, item in child.items()
                if str(key) not in PRESCRIPTIVE_REPAIR_FIELDS
                and not str(key).endswith(("_repair_rule", "_recipe"))
            }
        if isinstance(child, list):
            return [project(item) for item in child]
        if isinstance(child, tuple):
            return [project(item) for item in child]
        return deepcopy(child)

    return project(value)


def compact_semantic_review_feedback(
    feedback: Mapping[str, Any] | None,
    *,
    expected_feedback_type: str,
    max_rows: int = 8,
    max_text_chars: int = 2400,
) -> dict[str, Any]:
    """Keep bounded independent-review findings intact for the revising agent."""

    if not isinstance(feedback, Mapping):
        return {}
    feedback_type = str(feedback.get("feedback_type", "") or "").strip()
    if feedback_type != expected_feedback_type:
        return {}

    dimension_reviews = _compact_mapping_rows(
        feedback.get("dimension_reviews", []),
        keys=("dimension", "status", "rationale", "evidence_refs"),
        max_rows=max_rows,
        max_text_chars=max_text_chars,
    )
    findings = _compact_mapping_rows(
        feedback.get("findings", []),
        keys=(
            "severity",
            "category",
            "summary",
            "repair_scope",
            "evidence_refs",
        ),
        max_rows=max_rows,
        max_text_chars=max_text_chars,
    )
    payload = {
        "feedback_type": feedback_type,
        "feedback_source": _bounded_text(
            feedback.get("feedback_source", ""), max_text_chars
        ),
        "source_subsystem": _bounded_text(
            feedback.get("source_subsystem", ""), max_text_chars
        ),
        "semantic_review_execution_id": _bounded_text(
            feedback.get("semantic_review_execution_id", ""), max_text_chars
        ),
        "semantic_review_packet_id": _bounded_text(
            feedback.get("semantic_review_packet_id", ""), max_text_chars
        ),
        "semantic_review_packet_hash": _bounded_text(
            feedback.get("semantic_review_packet_hash", ""), max_text_chars
        ),
        "candidate_materialization_id": _bounded_text(
            feedback.get("candidate_materialization_id", ""), max_text_chars
        ),
        "candidate_id": _bounded_text(
            feedback.get("candidate_id", ""), max_text_chars
        ),
        "candidate_source_hash": _bounded_text(
            feedback.get("candidate_source_hash", ""), max_text_chars
        ),
        "target_theorem_statement_hash": _bounded_text(
            feedback.get("target_theorem_statement_hash", ""), max_text_chars
        ),
        "target_theorem_statement_hash_algorithm": _bounded_text(
            feedback.get("target_theorem_statement_hash_algorithm", ""),
            max_text_chars,
        ),
        "overall_verdict": _bounded_text(
            feedback.get("overall_verdict", ""), max_text_chars
        ),
        "repair_owner_agent": _bounded_text(
            feedback.get("repair_owner_agent", ""), max_text_chars
        ),
        "repair_target_subsystem": _bounded_text(
            feedback.get("repair_target_subsystem", ""), max_text_chars
        ),
        "dimension_reviews": dimension_reviews,
        "findings": findings,
        "reviewed_source_artifacts": _compact_reviewed_source_artifacts(
            feedback.get("reviewed_source_artifacts", []),
            max_rows=max_rows,
            max_source_chars=40000,
            max_text_chars=max_text_chars,
        ),
        "source_repair_contract": _compact_source_repair_contract(
            feedback.get("source_repair_contract", {}),
            max_text_chars=max_text_chars,
        ),
        "blocking_reason": _bounded_text(
            feedback.get("blocking_reason", ""), max_text_chars
        ),
        "proof_evidence_status": _bounded_text(
            feedback.get("proof_evidence_status", ""), max_text_chars
        ),
        "evidence_boundary": _bounded_text(
            feedback.get("evidence_boundary", ""), max_text_chars
        ),
    }
    return {
        key: value
        for key, value in payload.items()
        if value not in (None, "", [], {})
    }


def _compact_reviewed_source_artifacts(
    value: Any,
    *,
    max_rows: int,
    max_source_chars: int,
    max_text_chars: int,
) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    rows: list[dict[str, Any]] = []
    for raw_row in value:
        if not isinstance(raw_row, Mapping):
            continue
        source_code = str(raw_row.get("exact_source_code", "") or "")
        source_complete = bool(
            raw_row.get("exact_source_code_complete", False)
            and len(source_code) <= max_source_chars
        )
        exact_result = raw_row.get("exact_result", {})
        compact_result = (
            {
                str(key): child
                if isinstance(child, bool | int | float) or child is None
                else _bounded_text(child, max_text_chars)
                for key, child in list(exact_result.items())[:24]
            }
            if isinstance(exact_result, Mapping)
            else {}
        )
        rows.append(
            {
                "artifact_id": _bounded_text(
                    raw_row.get("artifact_id", ""),
                    max_text_chars,
                ),
                "exact_source_hash": _bounded_text(
                    raw_row.get("exact_source_hash", ""),
                    max_text_chars,
                ),
                "exact_source_code": source_code[:max_source_chars],
                "exact_source_code_complete": source_complete,
                "exact_result": compact_result,
                "exact_result_hash": _bounded_text(
                    raw_row.get("exact_result_hash", ""),
                    max_text_chars,
                ),
                "actual_runtime_arguments": (
                    dict(raw_row.get("actual_runtime_arguments", {}))
                    if isinstance(
                        raw_row.get("actual_runtime_arguments", {}),
                        Mapping,
                    )
                    else {}
                ),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _compact_source_repair_contract(
    value: Any,
    *,
    max_text_chars: int,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    fields = (
        "parent_source_manifest_id",
        "parent_source_manifest_hash",
        "repair_target_subsystem",
        "rejected_descendant_source_manifest_id",
        "rejected_descendant_source_manifest_hash",
        "theory_packet_id",
        "theory_packet_hash",
        "proposal_packet_id",
        "proposal_packet_hash",
        "architect_evidence_contract_fingerprint",
        "current_consumer_source_may_not_modify_dependency",
        "embedded_source_is_untrusted_data",
        "proof_evidence_status",
    )
    return {
        field: (
            value.get(field)
            if isinstance(value.get(field), bool)
            else _bounded_text(value.get(field, ""), max_text_chars)
        )
        for field in fields
        if value.get(field) not in (None, "")
    }


def _compact_mapping_rows(
    value: Any,
    *,
    keys: Sequence[str],
    max_rows: int,
    max_text_chars: int,
) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    rows: list[dict[str, Any]] = []
    for raw_row in value:
        if not isinstance(raw_row, Mapping):
            continue
        row: dict[str, Any] = {}
        for key in keys:
            raw_value = raw_row.get(key)
            if isinstance(raw_value, list | tuple):
                compact_value: Any = _compact_text_rows(
                    raw_value,
                    max_rows=max_rows,
                    max_text_chars=max_text_chars,
                )
            elif isinstance(raw_value, Mapping):
                compact_value = {
                    str(child_key): _bounded_text(child_value, max_text_chars)
                    for child_key, child_value in list(raw_value.items())[:max_rows]
                }
            else:
                compact_value = _bounded_text(raw_value, max_text_chars)
            if compact_value not in (None, "", [], {}):
                row[key] = compact_value
        if row:
            rows.append(row)
        if len(rows) >= max_rows:
            break
    return rows


def _compact_text_rows(
    value: Any,
    *,
    max_rows: int,
    max_text_chars: int,
) -> list[str]:
    candidates = value if isinstance(value, list | tuple) else [value]
    rows = [
        _bounded_text(row, max_text_chars)
        for row in candidates
        if str(row or "").strip()
    ]
    return rows[:max_rows]


def _bounded_text(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    head_chars = max(1, max_chars // 2)
    tail_chars = max(0, max_chars - head_chars - 5)
    return text[:head_chars].rstrip() + " ... " + text[-tail_chars:].lstrip()
