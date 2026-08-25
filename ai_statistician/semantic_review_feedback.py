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


def model_observations_without_repair_recipes(
    value: Any,
    *,
    preserve_exact_keys: Sequence[str] = ("rejected_candidate",),
) -> Any:
    """Remove prescriptive edits while preserving raw candidate observations."""

    preserved = frozenset(str(key) for key in preserve_exact_keys)

    def is_prescriptive_key(key: Any) -> bool:
        key_text = str(key)
        return bool(
            key_text in PRESCRIPTIVE_REPAIR_FIELDS
            or key_text == "required_next_checks"
            or key_text.endswith(
                (
                    "_cli",
                    "_repair_contract",
                    "_repair_directive",
                    "_repair_directives",
                    "_repair_diagnostics",
                    "_repair_manifest_paths",
                    "_repair_memory",
                    "_repair_required",
                    "_repair_rule",
                    "_repair_sequence",
                    "_repair_sequences",
                    "_recipe",
                    "_requires_repair",
                    "_strategy",
                    "_structural_reformulation_required",
                )
            )
        )

    def project(child: Any, *, parent_key: str = "") -> Any:
        if parent_key in preserved:
            return deepcopy(child)
        if isinstance(child, Mapping):
            return {
                str(key): project(item, parent_key=str(key))
                for key, item in child.items()
                if not is_prescriptive_key(key)
            }
        if isinstance(child, list):
            return [project(item) for item in child]
        if isinstance(child, tuple):
            return [project(item) for item in child]
        return deepcopy(child)

    return project(value)


def coding_agent_observations_only(
    value: Any,
    *,
    preserve_exact_keys: Sequence[str] = ("rejected_candidate",),
) -> Any:
    """Expose evidence to a coding model without runtime-authored fix routing."""

    projected = model_observations_without_repair_recipes(
        value,
        preserve_exact_keys=preserve_exact_keys,
    )
    preserved = frozenset(str(key) for key in preserve_exact_keys)

    def strip_routing(child: Any, *, parent_key: str = "") -> Any:
        if parent_key in preserved:
            return deepcopy(child)
        if isinstance(child, Mapping):
            return {
                str(key): strip_routing(item, parent_key=str(key))
                for key, item in child.items()
                if str(key) not in CODING_AGENT_ROUTING_FIELDS
            }
        if isinstance(child, list):
            return [strip_routing(item) for item in child]
        if isinstance(child, tuple):
            return [strip_routing(item) for item in child]
        return deepcopy(child)

    return strip_routing(projected)


def architect_observations_without_runtime_routing(value: Any) -> Any:
    """Give the Architect evidence without a runtime or reviewer-authored route."""

    projected = model_observations_without_repair_recipes(value)

    def strip_owner_plan(child: Any) -> Any:
        if isinstance(child, Mapping):
            return {
                str(key): strip_owner_plan(item)
                for key, item in child.items()
                if str(key) not in ARCHITECT_RUNTIME_ROUTING_FIELDS
            }
        if isinstance(child, list):
            return [strip_owner_plan(item) for item in child]
        if isinstance(child, tuple):
            return [strip_owner_plan(item) for item in child]
        return deepcopy(child)

    return strip_owner_plan(projected)
