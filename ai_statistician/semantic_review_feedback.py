from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


PRESCRIPTIVE_REPAIR_FIELDS = frozenset(
    {
        "candidate_reroute_options",
        "core_lean_diagnostic_helper_shape",
        "next_action",
        "preferred_tool_order",
        "proof_search_result_use",
        "proof_state_workflow",
        "recommended_action",
        "recommended_actions",
        "recommended_capability_eval_command",
        "recommended_command",
        "recommended_commands",
        "recommended_formalizer_target_mode",
        "recommended_next_action",
        "recommended_repair",
        "recommended_repair_scope",
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
        "required_next_checks",
        "required_repair",
        "required_resolution",
        "required_revision",
        "route_revision_recommended",
        "semantic_reviewer_recommended_repair_scope",
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


CODING_AGENT_ROUTING_FIELDS = frozenset(
    {
        "active_pending_repair_scopes",
        "available_observation_types",
        "candidate_live_proof_state_request",
        "candidate_lean_lsp_mcp_ready_request",
        "candidate_proof_state_requested_tools",
        "expected_transcript_events",
        "fallback_adapter",
        "mcp_tool_calls",
        "n_candidate_live_proof_state_requests",
        "model_requested_repair_instructions",
        "model_requested_repair_scope",
        "model_requested_repair_scopes",
        "pending_repair_plan",
        "pending_repair_plan_id",
        "provider_preferences",
        "proofengineer_repair_loop_contract",
        "retrieval_query_seeds",
        "repair_instructions",
        "repair_owner",
        "repair_owner_agent",
        "repair_plan",
        "repair_scope",
        "repair_scopes",
        "repair_target_subsystem",
        "runtime_queue_status",
        "runtime_carried_pending_repair",
        "semantic_reviewer_repair_instructions",
        "semantic_reviewer_repair_scope",
        "semantic_reviewer_repair_scopes",
        "source_repair_contract",
    }
)


ARCHITECT_RUNTIME_ROUTING_FIELDS = frozenset(
    {
        "active_pending_repair_scopes",
        "candidate_reroute_options",
        "model_requested_repair_scope",
        "model_requested_repair_scopes",
        "pending_repair_plan",
        "pending_repair_plan_id",
        "repair_owner",
        "repair_owner_agent",
        "repair_plan",
        "repair_scope",
        "repair_scopes",
        "repair_target_subsystem",
        "semantic_reviewer_repair_scope",
        "semantic_reviewer_repair_scopes",
    }
)


def _project_runtime_fields(
    value: Any,
    *,
    excluded_fields: frozenset[str],
    preserve_exact_keys: Sequence[str] = ("rejected_candidate",),
) -> Any:
    """Remove known envelope fields, never infer ownership from a key suffix."""

    preserved = frozenset(str(key) for key in preserve_exact_keys)

    def project(child: Any, *, parent_key: str = "") -> Any:
        if parent_key in preserved:
            return deepcopy(child)
        if isinstance(child, Mapping):
            return {
                str(key): project(item, parent_key=str(key))
                for key, item in child.items()
                if str(key) not in excluded_fields
            }
        if isinstance(child, list):
            return [project(item) for item in child]
        if isinstance(child, tuple):
            return [project(item) for item in child]
        return deepcopy(child)

    return project(value)


def model_observations_without_repair_recipes(
    value: Any,
    *,
    preserve_exact_keys: Sequence[str] = ("rejected_candidate",),
) -> Any:
    """Remove explicit runtime directives while preserving candidate observations."""

    return _project_runtime_fields(
        value,
        excluded_fields=PRESCRIPTIVE_REPAIR_FIELDS,
        preserve_exact_keys=preserve_exact_keys,
    )


def coding_agent_observations_only(
    value: Any,
    *,
    preserve_exact_keys: Sequence[str] = ("rejected_candidate",),
) -> Any:
    """Expose evidence to a coding model without runtime-authored fix routing."""

    return _project_runtime_fields(
        value,
        excluded_fields=PRESCRIPTIVE_REPAIR_FIELDS | CODING_AGENT_ROUTING_FIELDS,
        preserve_exact_keys=preserve_exact_keys,
    )


def architect_observations_without_runtime_routing(value: Any) -> Any:
    """Give the Architect evidence without a runtime or reviewer-authored route."""

    return _project_runtime_fields(
        value,
        excluded_fields=PRESCRIPTIVE_REPAIR_FIELDS | ARCHITECT_RUNTIME_ROUTING_FIELDS,
    )
