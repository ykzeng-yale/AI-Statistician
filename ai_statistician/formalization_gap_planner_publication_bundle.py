from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .formalization_gap_planner_adapter_registry import (
    adapter_registry_row_json_schema,
    export_formalization_gap_planner_adapter_registry,
)
from .formalization_gap_planner_benchmark import (
    benchmark_route_row_json_schema,
    default_formalization_gap_planner_ground_truth_path,
    export_formalization_gap_planner_benchmark,
)
from .formalization_gap_planner_benchmark_audit import (
    audit_formalization_gap_planner_benchmark,
)
from .formalization_gap_planner_ablation_study import (
    ablation_study_row_json_schema,
)
from .formalization_gap_planner_component_resource_registry import (
    PORTABLE_REUSE_TARGETS,
    component_resource_contract_row_json_schema,
    component_resource_registry_component_row_json_schema,
    component_resource_registry_resource_row_json_schema,
    component_resource_execution_plan_json_schema,
    export_formalization_gap_planner_component_resource_registry,
)
from .formalization_gap_planner_cross_prover_matrix_audit import (
    CROSS_PROVER_MATRIX_AUDIT_ROW_SCHEMA_ID,
    CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
    cross_prover_matrix_audit_row_json_schema,
    cross_prover_target_summary_json_schema,
)
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS,
    evaluation_protocol,
    interactive_route_synthesis_contract,
    planner_contract,
    portable_gap_plan_json_schema,
    portable_gap_plan_row_json_schema,
    portable_work_packet_contract,
    route_alignment_edge_json_schema,
)
from .formalization_gap_planner_interactive_session import (
    interactive_decision_policy_row_json_schema,
    interactive_session_row_json_schema,
)
from .formalization_gap_planner_library_coverage_map import (
    library_coverage_map_row_json_schema,
)
from .formalization_gap_planner_llm_route_planner import (
    LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID,
    LLM_ROUTE_PLANNER_PROVIDER_USAGE_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID,
    PROVIDER_EXECUTION_MODES,
    llm_route_planner_library_alignment_summary_json_schema,
    llm_route_planner_manifest_json_schema,
    llm_route_planner_model_tier_decision_ledger_json_schema,
    llm_route_planner_provider_usage_row_json_schema,
    llm_route_planner_request_json_schema,
    llm_route_planner_response_payload_validation_manifest_json_schema,
    llm_route_planner_response_payload_validation_row_json_schema,
    llm_route_planner_route_planning_brief_json_schema,
    llm_route_planner_target_theorem_context_packet_json_schema,
    llm_route_planner_response_payload_schema,
    llm_route_planner_response_json_schema,
    llm_route_planner_row_json_schema,
)
from .formalization_gap_planner_route_adoption_blockers import (
    ROUTE_ADOPTION_AWAITING_STATUS,
    ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE,
    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES,
    ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID,
    ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
    ROUTE_ADOPTION_BLOCKER_VALUES,
    ROUTE_ADOPTION_PENDING_STATUS,
    ROUTE_ADOPTION_READY_STATUS,
    ROUTE_ADOPTION_REJECTED_STATUS,
    route_adoption_blocker_taxonomy_manifest_json_schema,
    route_adoption_blocker_taxonomy_json_schema,
    route_adoption_blocker_taxonomy_payload,
    validate_route_adoption_blocker_taxonomy_payload,
)
from .formalization_gap_planner_primitive_action_queue import (
    primitive_action_queue_row_json_schema,
)
from .formalization_gap_planner_action_resource_plan import (
    action_resource_plan_row_json_schema,
)
from .formalization_gap_planner_resource_request_queue import (
    RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
    resource_request_queue_row_json_schema,
)
from .formalization_gap_planner_resource_response_ledger import (
    RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
    resource_response_json_schema,
    resource_response_ledger_row_json_schema,
)
from .formalization_gap_planner_evaluation import evaluation_row_json_schema
from .formalization_gap_planner_minimal_delta_audit import (
    minimal_delta_decision_row_json_schema,
)
from .formalization_gap_planner_portable_plan_audit import (
    portable_plan_audit_row_json_schema,
)
from .formalization_gap_planner_proof_state_triage import (
    proof_state_triage_row_json_schema,
)
from .formalization_gap_planner_prover_adapter_contract import (
    PROVER_ADAPTER_PACKET_SCHEMA_ID,
    PROVER_ADAPTER_RESPONSE_SCHEMA_ID,
    PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID,
    prover_adapter_packet_json_schema,
    prover_adapter_response_json_schema,
    prover_adapter_response_validation_row_json_schema,
)
from .formalization_gap_planner_refinement_evidence import (
    refinement_evidence_row_json_schema,
    refinement_tool_response_json_schema,
)
from .formalization_gap_planner_refinement_queue import refinement_work_item_json_schema
from .formalization_gap_planner_route_replan_handoff import (
    route_replan_handoff_row_json_schema,
)
from .formalization_gap_planner_route_replan_handoff_audit import (
    route_replan_handoff_audit_row_json_schema,
)
from .formalization_gap_planner_runtime_handoff_audit import (
    runtime_handoff_audit_row_json_schema,
)
from .formalization_gap_planner_route_stability_audit import (
    route_stability_audit_row_json_schema,
)
from .formalization_gap_planner_route_revision_overlay import (
    route_revision_overlay_row_json_schema,
)
from .formalization_gap_planner_source_grounding_audit import (
    source_grounding_row_json_schema,
)
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
    llm_route_planner_seed_route_selection_json_schema,
    standalone_input_json_schema,
)
from .formalization_gap_planner_target_intake import (
    target_intake_json_schema,
    target_intake_row_json_schema,
)
from .model_backend import (
    ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
    ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
    ANTHROPIC_MODEL_SOURCE_EVIDENCE,
    CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS,
    DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER,
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL,
    DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL,
    DEFAULT_LIVE_GENERATOR_PROVIDER,
    PROHIBITED_AGENT_GENERATOR_PROVIDERS,
    SUPPORTED_LIVE_GENERATOR_PROVIDERS,
)


FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_SCHEMA_VERSION = 1
PUBLICATION_BUNDLE_COMPONENT_NAME = "formalization_gap_planner_publication_bundle"
SCHEMA_CATALOG_COMPONENT_NAME = "formalization_gap_planner_schema_catalog"
LLM_MODEL_POLICY_COMPONENT_NAME = "ai_statistician_llm_model_policy"
FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-schema-catalog:1"
)
FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-publication-bundle-manifest:1"
)
LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-response-payload-lean-legacy:1"
)
LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-response-payload-target-prover:1"
)
PORTABLE_TARGET_PROVER_RESPONSE_PAYLOAD_FAMILIES = tuple(
    target for target in PORTABLE_REUSE_TARGETS if target != "lean4"
)
PORTABLE_TARGET_PROVER_FAMILY_HINT = (
    "<" + "|".join((*PORTABLE_REUSE_TARGETS, "other")) + ">"
)
OPTIONAL_ARTIFACT_FILES = {
    "formalization_gap_planner_target_intake": (
        "formalization_gap_planner_target_intake_manifest.json",
        "formalization_gap_planner_target_intake.jsonl",
        "formalization_gap_planner_target_intake_standalone_seed.json",
        "formalization_gap_planner_target_intake.md",
        "formalization_gap_planner_target_intake.schema.json",
        "formalization_gap_planner_target_intake_row.schema.json",
    ),
    "formalization_gap_planner_llm_route_planner": (
        "formalization_gap_planner_llm_route_planner_manifest.json",
        "formalization_gap_planner_llm_route_planner_manifest.schema.json",
        "formalization_gap_planner_llm_route_planner_requests.jsonl",
        "formalization_gap_planner_llm_route_planner_prompt_token_budget.jsonl",
        "formalization_gap_planner_llm_route_planner_library_alignment_summaries.jsonl",
        "formalization_gap_planner_llm_route_planner_target_theorem_context_packets.jsonl",
        "formalization_gap_planner_llm_route_planner_route_planning_briefs.jsonl",
        "formalization_gap_planner_llm_route_planner.jsonl",
        "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.jsonl",
        "formalization_gap_planner_llm_route_planner_provider_usage.jsonl",
        "formalization_gap_planner_llm_route_planner_request.schema.json",
        "formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json",
        "formalization_gap_planner_llm_route_planner_target_theorem_context_packet.schema.json",
        "formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json",
        "formalization_gap_planner_llm_route_planner_response.schema.json",
        "formalization_gap_planner_llm_route_planner_response_payload.schema.json",
        "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json",
        "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json",
        "formalization_gap_planner_llm_route_planner_row.schema.json",
        "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.schema.json",
        "formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json",
        "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        "formalization_gap_planner_llm_route_planner_standalone_seed.schema.json",
        "formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json",
        "formalization_gap_planner_llm_route_planner.md",
    ),
    "formalization_gap_planner_feedback_llm_route_planner": (
        "formalization_gap_planner_llm_route_planner_manifest.json",
        "formalization_gap_planner_llm_route_planner_manifest.schema.json",
        "formalization_gap_planner_llm_route_planner_requests.jsonl",
        "formalization_gap_planner_llm_route_planner_prompt_token_budget.jsonl",
        "formalization_gap_planner_llm_route_planner_library_alignment_summaries.jsonl",
        "formalization_gap_planner_llm_route_planner_target_theorem_context_packets.jsonl",
        "formalization_gap_planner_llm_route_planner_route_planning_briefs.jsonl",
        "formalization_gap_planner_llm_route_planner.jsonl",
        "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.jsonl",
        "formalization_gap_planner_llm_route_planner_provider_usage.jsonl",
        "formalization_gap_planner_llm_route_planner_request.schema.json",
        "formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json",
        "formalization_gap_planner_llm_route_planner_target_theorem_context_packet.schema.json",
        "formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json",
        "formalization_gap_planner_llm_route_planner_response.schema.json",
        "formalization_gap_planner_llm_route_planner_response_payload.schema.json",
        "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json",
        "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json",
        "formalization_gap_planner_llm_route_planner_row.schema.json",
        "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.schema.json",
        "formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json",
        "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        "formalization_gap_planner_llm_route_planner_standalone_seed.schema.json",
        "formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json",
        "formalization_gap_planner_llm_route_planner.md",
    ),
    "formalization_gap_planner_llm_route_planner_response_payload_validation": (
        "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json",
        "formalization_gap_planner_llm_route_planner_response_payload_validation.jsonl",
        "formalization_gap_planner_llm_route_planner_response_payload.schema.json",
        "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json",
        "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json",
    ),
    "goal_conditioned_minimal_formalization_plan": (
        "goal_conditioned_minimal_formalization_plan_manifest.json",
        "goal_conditioned_minimal_formalization_plan.jsonl",
        "goal_conditioned_minimal_formalization_plan.md",
        "library_aware_formalization_gap_plan.schema.json",
        "library_aware_formalization_gap_plan_row.schema.json",
        "formalization_gap_planner_route_alignment_edge.schema.json",
    ),
    "formalization_gap_planner_evaluation": (
        "formalization_gap_planner_evaluation_manifest.json",
        "formalization_gap_planner_evaluation.jsonl",
        "formalization_gap_planner_evaluation_row.schema.json",
        "formalization_gap_planner_evaluation_ground_truth.json",
        "formalization_gap_planner_evaluation.md",
    ),
    "formalization_gap_planner_ablation_study": (
        "formalization_gap_planner_ablation_study_manifest.json",
        "formalization_gap_planner_ablation_study.jsonl",
        "formalization_gap_planner_ablation_study_row.schema.json",
        "formalization_gap_planner_ablation_study.md",
    ),
    "formalization_gap_planner_portable_plan_audit": (
        "formalization_gap_planner_portable_plan_audit_manifest.json",
        "formalization_gap_planner_portable_plan_audit.jsonl",
        "formalization_gap_planner_portable_plan_audit_row.schema.json",
        "formalization_gap_planner_portable_plan_audit.md",
    ),
    "formalization_gap_planner_library_coverage_map": (
        "formalization_gap_planner_library_coverage_map_manifest.json",
        "formalization_gap_planner_library_coverage_map.jsonl",
        "formalization_gap_planner_library_coverage_map_row.schema.json",
        "formalization_gap_planner_library_coverage_map.md",
    ),
    "formalization_gap_planner_primitive_action_queue": (
        "formalization_gap_planner_primitive_action_queue_manifest.json",
        "formalization_gap_planner_primitive_action_queue.jsonl",
        "formalization_gap_planner_primitive_action_queue_row.schema.json",
        "formalization_gap_planner_primitive_action_queue.md",
    ),
    "formalization_gap_planner_action_resource_plan": (
        "formalization_gap_planner_action_resource_plan_manifest.json",
        "formalization_gap_planner_action_resource_plan.jsonl",
        "formalization_gap_planner_action_resource_plan_row.schema.json",
        "formalization_gap_planner_action_resource_plan.md",
    ),
    "formalization_gap_planner_resource_request_queue": (
        "formalization_gap_planner_resource_request_queue_manifest.json",
        "formalization_gap_planner_resource_request_queue.jsonl",
        "formalization_gap_planner_resource_request_queue_row.schema.json",
        "formalization_gap_planner_resource_request_queue.md",
    ),
    "formalization_gap_planner_resource_response_ledger": (
        "formalization_gap_planner_resource_response_ledger_manifest.json",
        "formalization_gap_planner_resource_response_ledger.jsonl",
        "formalization_gap_planner_resource_response.schema.json",
        "formalization_gap_planner_resource_response_ledger_row.schema.json",
        "formalization_gap_planner_resource_response_ledger.md",
    ),
    "formalization_gap_planner_minimal_delta_audit": (
        "formalization_gap_planner_minimal_delta_audit_manifest.json",
        "formalization_gap_planner_minimal_delta_audit.jsonl",
        "formalization_gap_planner_minimal_delta_decisions.jsonl",
        "formalization_gap_planner_minimal_delta_decision_row.schema.json",
        "formalization_gap_planner_minimal_delta_audit.md",
    ),
    "formalization_gap_planner_minimal_delta_audit_feedback_adapter": (
        "formalization_gap_planner_minimal_delta_audit_feedback_adapter_manifest.json",
        "formalization_gap_planner_refinement_evidence_responses.jsonl",
        "formalization_gap_planner_minimal_delta_audit_feedback_responses.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_minimal_delta_audit_feedback_adapter.md",
    ),
    "formalization_gap_planner_source_grounding_audit": (
        "formalization_gap_planner_source_grounding_audit_manifest.json",
        "formalization_gap_planner_source_grounding_audit.jsonl",
        "formalization_gap_planner_source_grounding_row.schema.json",
        "formalization_gap_planner_source_grounding_audit.md",
    ),
    "formalization_gap_planner_refinement_queue": (
        "formalization_gap_planner_refinement_queue_manifest.json",
        "formalization_gap_planner_refinement_queue.jsonl",
        "formalization_gap_planner_refinement_work_item.schema.json",
        "formalization_gap_planner_refinement_queue.md",
    ),
    "formalization_gap_planner_refinement_adapter": (
        "formalization_gap_planner_refinement_adapter_manifest.json",
        "formalization_gap_planner_refinement_evidence_responses.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_refinement_adapter.md",
    ),
    "formalization_gap_planner_local_literature_adapter": (
        "formalization_gap_planner_local_literature_adapter_manifest.json",
        "formalization_gap_planner_refinement_evidence_responses.jsonl",
        "formalization_gap_planner_local_literature_adapter_responses.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_local_literature_adapter.md",
    ),
    "formalization_gap_planner_local_formal_source_adapter": (
        "formalization_gap_planner_local_formal_source_adapter_manifest.json",
        "formalization_gap_planner_refinement_evidence_responses.jsonl",
        "formalization_gap_planner_local_formal_source_adapter_responses.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_local_formal_source_adapter.md",
    ),
    "formalization_gap_planner_local_proof_state_adapter": (
        "formalization_gap_planner_local_proof_state_adapter_manifest.json",
        "formalization_gap_planner_refinement_evidence_responses.jsonl",
        "formalization_gap_planner_local_proof_state_adapter_responses.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_local_proof_state_adapter.md",
    ),
    "formalization_gap_planner_prover_adapter_feedback_adapter": (
        "formalization_gap_planner_prover_adapter_feedback_adapter_manifest.json",
        "formalization_gap_planner_refinement_evidence_responses.jsonl",
        "formalization_gap_planner_prover_adapter_feedback_responses.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_prover_adapter_feedback_adapter.md",
    ),
    "formalization_gap_planner_refinement_evidence": (
        "formalization_gap_planner_refinement_evidence_manifest.json",
        "formalization_gap_planner_refinement_evidence.jsonl",
        "formalization_gap_planner_route_revision_proposals.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_refinement_evidence_row.schema.json",
        "formalization_gap_planner_refinement_evidence.md",
    ),
    "formalization_gap_planner_route_revision_overlay": (
        "formalization_gap_planner_route_revision_overlay_manifest.json",
        "formalization_gap_planner_route_revision_overlay.jsonl",
        "formalization_gap_planner_route_revision_overlay_row.schema.json",
        "formalization_gap_planner_route_revision_overlay.md",
    ),
    "formalization_gap_planner_route_stability_audit": (
        "formalization_gap_planner_route_stability_audit_manifest.json",
        "formalization_gap_planner_route_stability_audit.jsonl",
        "formalization_gap_planner_route_stability_audit_row.schema.json",
        "formalization_gap_planner_route_stability_audit.md",
    ),
    "formalization_gap_planner_route_replan_handoff": (
        "formalization_gap_planner_route_replan_handoff_manifest.json",
        "formalization_gap_planner_route_replan_handoff.jsonl",
        "formalization_gap_planner_route_replan_handoff_row.schema.json",
        "formalization_gap_planner_route_replan_standalone_seed.json",
        "formalization_gap_planner_route_replan_standalone_seed.schema.json",
        "formalization_gap_planner_route_replan_handoff.md",
    ),
    "formalization_gap_planner_route_replan_handoff_audit": (
        "formalization_gap_planner_route_replan_handoff_audit_manifest.json",
        "formalization_gap_planner_route_replan_handoff_audit.jsonl",
        "formalization_gap_planner_route_replan_handoff_audit_row.schema.json",
        "formalization_gap_planner_route_replan_handoff_audit.md",
    ),
    "formalization_gap_planner_runtime_handoff_audit": (
        "formalization_gap_planner_runtime_handoff_audit_manifest.json",
        "formalization_gap_planner_runtime_handoff_audit.jsonl",
        "formalization_gap_planner_runtime_handoff_audit_row.schema.json",
        "formalization_gap_planner_runtime_handoff_audit.md",
    ),
    "formalization_gap_planner_proof_state_triage": (
        "formalization_gap_planner_proof_state_triage_manifest.json",
        "formalization_gap_planner_proof_state_triage.jsonl",
        "formalization_gap_planner_proof_state_triage_row.schema.json",
        "formalization_gap_planner_proof_state_triage.md",
    ),
    "formalization_gap_planner_interactive_session": (
        "formalization_gap_planner_interactive_session_manifest.json",
        "formalization_gap_planner_interactive_session.jsonl",
        "formalization_gap_planner_interactive_session_row.schema.json",
        "formalization_gap_planner_interactive_decision_policy.jsonl",
        "formalization_gap_planner_interactive_decision_policy_row.schema.json",
        "formalization_gap_planner_interactive_session.md",
    ),
    "formalization_gap_planner_prover_adapter_contract": (
        "formalization_gap_planner_prover_adapter_contract_manifest.json",
        "formalization_gap_planner_prover_adapter_packets.jsonl",
        "formalization_gap_planner_prover_adapter_packet.schema.json",
        "formalization_gap_planner_prover_adapter_response_validation.jsonl",
        "formalization_gap_planner_prover_adapter_response_validation_row.schema.json",
        "formalization_gap_planner_prover_adapter_response.schema.json",
        "formalization_gap_planner_prover_adapter_contract.md",
    ),
    "formalization_gap_planner_cross_prover_matrix_audit": (
        "formalization_gap_planner_cross_prover_matrix_audit_manifest.json",
        "formalization_gap_planner_cross_prover_matrix_audit.jsonl",
        "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json",
        "formalization_gap_planner_cross_prover_target_summary.json",
        "formalization_gap_planner_cross_prover_target_summary.schema.json",
        "formalization_gap_planner_cross_prover_packets.jsonl",
        "formalization_gap_planner_prover_adapter_packet.schema.json",
        "formalization_gap_planner_cross_prover_response_validation.jsonl",
        "formalization_gap_planner_prover_adapter_response_validation_row.schema.json",
        "formalization_gap_planner_cross_prover_matrix_audit.md",
    ),
    "formalization_gap_planner_adapter_registry_audit": (
        "formalization_gap_planner_adapter_registry_audit_manifest.json",
        "formalization_gap_planner_adapter_registry_audit.jsonl",
        "formalization_gap_planner_adapter_registry_audit.md",
    ),
    "formalization_gap_planner_component_resource_registry_audit": (
        "formalization_gap_planner_component_resource_registry_audit_manifest.json",
        "formalization_gap_planner_component_resource_registry_audit.jsonl",
        "formalization_gap_planner_component_resource_registry_audit.md",
    ),
}


def export_formalization_gap_planner_publication_bundle(
    out_dir: Path,
    *,
    ground_truth_path: Path | None = None,
    lean_rag_db_path: Path | None = None,
    paper_library_dir: Path | None = None,
    formalization_gap_planner_target_intake_dir: Path | None = None,
    formalization_gap_planner_llm_route_planner_dir: Path | None = None,
    formalization_gap_planner_feedback_llm_route_planner_dir: Path | None = None,
    formalization_gap_planner_llm_route_planner_response_payload_validation_dir: Path
    | None = None,
    goal_conditioned_minimal_formalization_plan_dir: Path | None = None,
    formalization_gap_planner_evaluation_dir: Path | None = None,
    formalization_gap_planner_ablation_study_dir: Path | None = None,
    formalization_gap_planner_portable_plan_audit_dir: Path | None = None,
    formalization_gap_planner_library_coverage_map_dir: Path | None = None,
    formalization_gap_planner_primitive_action_queue_dir: Path | None = None,
    formalization_gap_planner_action_resource_plan_dir: Path | None = None,
    formalization_gap_planner_resource_request_queue_dir: Path | None = None,
    formalization_gap_planner_resource_response_ledger_dir: Path | None = None,
    formalization_gap_planner_minimal_delta_audit_dir: Path | None = None,
    formalization_gap_planner_minimal_delta_audit_feedback_adapter_dir: Path
    | None = None,
    formalization_gap_planner_source_grounding_audit_dir: Path | None = None,
    formalization_gap_planner_refinement_queue_dir: Path | None = None,
    formalization_gap_planner_refinement_adapter_dir: Path | None = None,
    formalization_gap_planner_local_literature_adapter_dir: Path | None = None,
    formalization_gap_planner_local_formal_source_adapter_dir: Path | None = None,
    formalization_gap_planner_local_proof_state_adapter_dir: Path | None = None,
    formalization_gap_planner_prover_adapter_feedback_adapter_dir: Path | None = None,
    formalization_gap_planner_refinement_evidence_dir: Path | None = None,
    formalization_gap_planner_route_revision_overlay_dir: Path | None = None,
    formalization_gap_planner_route_stability_audit_dir: Path | None = None,
    formalization_gap_planner_route_replan_handoff_dir: Path | None = None,
    formalization_gap_planner_route_replan_handoff_audit_dir: Path | None = None,
    formalization_gap_planner_runtime_handoff_audit_dir: Path | None = None,
    formalization_gap_planner_proof_state_triage_dir: Path | None = None,
    formalization_gap_planner_interactive_session_dir: Path | None = None,
    formalization_gap_planner_prover_adapter_contract_dir: Path | None = None,
    formalization_gap_planner_cross_prover_matrix_audit_dir: Path | None = None,
    formalization_gap_planner_adapter_registry_audit_dir: Path | None = None,
    formalization_gap_planner_component_resource_registry_audit_dir: Path | None = None,
    library_snapshot_ref: str = "portable_publication_bundle",
) -> dict[str, object]:
    """Write a self-contained publication/reuse bundle for the gap planner."""

    errors: list[str] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    contract_dir = out_dir / "contract"
    docs_dir = out_dir / "docs"
    artifacts_dir = out_dir / "artifacts"
    reproduce_dir = out_dir / "reproduce"
    examples_dir = out_dir / "examples"
    contract_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    reproduce_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)

    schema_payload = portable_gap_plan_json_schema()
    prover_adapter_packet_schema = prover_adapter_packet_json_schema()
    prover_adapter_response_schema = prover_adapter_response_json_schema()
    prover_adapter_response_validation_row_schema = (
        prover_adapter_response_validation_row_json_schema()
    )
    refinement_work_item_schema = refinement_work_item_json_schema()
    refinement_tool_response_schema = refinement_tool_response_json_schema()
    refinement_evidence_row_schema = refinement_evidence_row_json_schema()
    interactive_session_row_schema = interactive_session_row_json_schema()
    interactive_decision_policy_row_schema = (
        interactive_decision_policy_row_json_schema()
    )
    minimal_delta_decision_row_schema = minimal_delta_decision_row_json_schema()
    portable_plan_audit_row_schema = portable_plan_audit_row_json_schema()
    library_coverage_map_row_schema = library_coverage_map_row_json_schema()
    llm_route_planner_request_schema = llm_route_planner_request_json_schema()
    llm_route_planner_library_alignment_summary_schema = (
        llm_route_planner_library_alignment_summary_json_schema()
    )
    llm_route_planner_target_theorem_context_packet_schema = (
        llm_route_planner_target_theorem_context_packet_json_schema()
    )
    llm_route_planner_route_planning_brief_schema = (
        llm_route_planner_route_planning_brief_json_schema()
    )
    llm_route_planner_response_schema = llm_route_planner_response_json_schema()
    llm_route_planner_response_payload_schema_payload = (
        llm_route_planner_response_payload_schema()
    )
    llm_route_planner_response_payload_lean_legacy_schema = (
        _scoped_llm_response_payload_schema(
            target_prover_family="lean4",
            schema_id=LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID,
            title=(
                "Formalization Gap Planner LLM Route Planner Response Payload "
                "(Lean Legacy Compatible)"
            ),
            target_prover_families=("lean4",),
        )
    )
    llm_route_planner_response_payload_target_prover_schema = (
        _scoped_llm_response_payload_schema(
            target_prover_family="rocq",
            schema_id=LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID,
            title=(
                "Formalization Gap Planner LLM Route Planner Response Payload "
                "(Target-Prover Portable)"
            ),
            target_prover_families=PORTABLE_TARGET_PROVER_RESPONSE_PAYLOAD_FAMILIES,
        )
    )
    llm_route_planner_response_payload_validation_manifest_schema = (
        llm_route_planner_response_payload_validation_manifest_json_schema()
    )
    llm_route_planner_response_payload_validation_row_schema = (
        llm_route_planner_response_payload_validation_row_json_schema()
    )
    llm_route_planner_manifest_schema = llm_route_planner_manifest_json_schema()
    llm_route_planner_row_schema = llm_route_planner_row_json_schema()
    llm_route_planner_model_tier_decision_ledger_schema = (
        llm_route_planner_model_tier_decision_ledger_json_schema()
    )
    llm_route_planner_provider_usage_row_schema = (
        llm_route_planner_provider_usage_row_json_schema()
    )
    llm_route_planner_seed_route_selection_schema = (
        llm_route_planner_seed_route_selection_json_schema()
    )
    primitive_action_queue_row_schema = primitive_action_queue_row_json_schema()
    action_resource_plan_row_schema = action_resource_plan_row_json_schema()
    resource_request_queue_row_schema = resource_request_queue_row_json_schema()
    resource_response_schema = resource_response_json_schema()
    resource_response_ledger_row_schema = resource_response_ledger_row_json_schema()
    source_grounding_row_schema = source_grounding_row_json_schema()
    route_revision_overlay_row_schema = route_revision_overlay_row_json_schema()
    route_stability_audit_row_schema = route_stability_audit_row_json_schema()
    route_replan_handoff_row_schema = route_replan_handoff_row_json_schema()
    route_replan_handoff_audit_row_schema = (
        route_replan_handoff_audit_row_json_schema()
    )
    runtime_handoff_audit_row_schema = runtime_handoff_audit_row_json_schema()
    proof_state_triage_row_schema = proof_state_triage_row_json_schema()
    ablation_study_row_schema = ablation_study_row_json_schema()
    route_alignment_edge_schema = route_alignment_edge_json_schema()
    benchmark_route_schema = benchmark_route_row_json_schema()
    evaluation_row_schema = evaluation_row_json_schema()
    adapter_registry_row_schema = adapter_registry_row_json_schema()
    cross_prover_matrix_audit_row_schema = (
        cross_prover_matrix_audit_row_json_schema()
    )
    cross_prover_target_summary_schema = cross_prover_target_summary_json_schema()
    component_resource_resource_row_schema = (
        component_resource_registry_resource_row_json_schema()
    )
    component_resource_component_row_schema = (
        component_resource_registry_component_row_json_schema()
    )
    component_execution_plan_schema = component_resource_execution_plan_json_schema()
    component_resource_contract_row_schema = (
        component_resource_contract_row_json_schema()
    )
    contract_payload = _contract_payload(library_snapshot_ref)
    llm_model_policy_payload = _llm_model_policy_payload()
    route_adoption_blocker_taxonomy_schema = (
        route_adoption_blocker_taxonomy_json_schema()
    )
    route_adoption_blocker_taxonomy_manifest_schema = (
        route_adoption_blocker_taxonomy_manifest_json_schema()
    )
    route_adoption_blocker_taxonomy_contract = (
        route_adoption_blocker_taxonomy_payload()
    )
    schema_path = contract_dir / "library_aware_formalization_gap_plan.schema.json"
    prover_adapter_schema_path = (
        contract_dir / "formalization_gap_planner_prover_adapter_response.schema.json"
    )
    prover_adapter_packet_schema_path = (
        contract_dir / "formalization_gap_planner_prover_adapter_packet.schema.json"
    )
    prover_adapter_response_validation_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    )
    refinement_tool_response_schema_path = (
        contract_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    )
    refinement_work_item_schema_path = (
        contract_dir / "formalization_gap_planner_refinement_work_item.schema.json"
    )
    refinement_evidence_row_schema_path = (
        contract_dir / "formalization_gap_planner_refinement_evidence_row.schema.json"
    )
    interactive_session_row_schema_path = (
        contract_dir / "formalization_gap_planner_interactive_session_row.schema.json"
    )
    interactive_decision_policy_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_interactive_decision_policy_row.schema.json"
    )
    minimal_delta_decision_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
    )
    portable_plan_audit_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_portable_plan_audit_row.schema.json"
    )
    library_coverage_map_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_library_coverage_map_row.schema.json"
    )
    llm_route_planner_request_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_request.schema.json"
    )
    llm_route_planner_library_alignment_summary_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json"
    )
    llm_route_planner_target_theorem_context_packet_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_target_theorem_context_packet.schema.json"
    )
    llm_route_planner_route_planning_brief_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json"
    )
    llm_route_planner_response_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_response.schema.json"
    )
    llm_route_planner_response_payload_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
    )
    llm_route_planner_response_payload_lean_legacy_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_lean_legacy.schema.json"
    )
    llm_route_planner_response_payload_target_prover_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_target_prover.schema.json"
    )
    llm_route_planner_response_payload_validation_manifest_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json"
    )
    llm_route_planner_response_payload_validation_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
    )
    llm_route_planner_manifest_schema_path = (
        contract_dir / "formalization_gap_planner_llm_route_planner_manifest.schema.json"
    )
    llm_route_planner_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_row.schema.json"
    )
    llm_route_planner_model_tier_decision_ledger_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.schema.json"
    )
    llm_route_planner_provider_usage_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json"
    )
    route_adoption_blocker_taxonomy_schema_path = (
        contract_dir
        / "formalization_gap_planner_route_adoption_blocker_taxonomy.schema.json"
    )
    route_adoption_blocker_taxonomy_manifest_schema_path = (
        contract_dir
        / "formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.schema.json"
    )
    route_adoption_blocker_taxonomy_path = (
        contract_dir
        / "formalization_gap_planner_route_adoption_blocker_taxonomy.json"
    )
    primitive_action_queue_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_primitive_action_queue_row.schema.json"
    )
    action_resource_plan_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_action_resource_plan_row.schema.json"
    )
    resource_request_queue_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_resource_request_queue_row.schema.json"
    )
    resource_response_schema_path = (
        contract_dir / "formalization_gap_planner_resource_response.schema.json"
    )
    resource_response_ledger_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_resource_response_ledger_row.schema.json"
    )
    source_grounding_row_schema_path = (
        contract_dir / "formalization_gap_planner_source_grounding_row.schema.json"
    )
    route_revision_overlay_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_route_revision_overlay_row.schema.json"
    )
    route_stability_audit_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_route_stability_audit_row.schema.json"
    )
    route_replan_handoff_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_route_replan_handoff_row.schema.json"
    )
    route_replan_handoff_audit_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
    )
    runtime_handoff_audit_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_runtime_handoff_audit_row.schema.json"
    )
    proof_state_triage_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_proof_state_triage_row.schema.json"
    )
    ablation_study_row_schema_path = (
        contract_dir / "formalization_gap_planner_ablation_study_row.schema.json"
    )
    route_alignment_edge_schema_path = (
        contract_dir
        / "formalization_gap_planner_route_alignment_edge.schema.json"
    )
    portable_plan_row_schema_path = (
        contract_dir / "library_aware_formalization_gap_plan_row.schema.json"
    )
    schema_catalog_path = (
        contract_dir / "formalization_gap_planner_schema_catalog.json"
    )
    schema_catalog_schema_path = (
        contract_dir / "formalization_gap_planner_schema_catalog.schema.json"
    )
    publication_bundle_manifest_schema_path = (
        contract_dir
        / "formalization_gap_planner_publication_bundle_manifest.schema.json"
    )
    contract_path = contract_dir / "formalization_gap_planner_portable_contract.json"
    llm_model_policy_path = contract_dir / "ai_statistician_llm_model_policy.json"
    llm_model_policy_report_path = contract_dir / "ai_statistician_llm_model_policy.md"
    standalone_schema_path = (
        contract_dir / "formalization_gap_planner_standalone_input.schema.json"
    )
    llm_route_planner_seed_route_selection_schema_path = (
        contract_dir
        / "formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json"
    )
    target_intake_schema_path = (
        contract_dir / "formalization_gap_planner_target_intake.schema.json"
    )
    target_intake_row_schema_path = (
        contract_dir / "formalization_gap_planner_target_intake_row.schema.json"
    )
    component_execution_plan_schema_path = (
        contract_dir
        / "formalization_gap_planner_component_resource_execution_plan.schema.json"
    )
    benchmark_route_schema_path = (
        contract_dir / "formalization_gap_planner_benchmark_route.schema.json"
    )
    evaluation_row_schema_path = (
        contract_dir / "formalization_gap_planner_evaluation_row.schema.json"
    )
    adapter_registry_row_schema_path = (
        contract_dir / "formalization_gap_planner_adapter_registry_row.schema.json"
    )
    cross_prover_matrix_audit_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
    )
    cross_prover_target_summary_schema_path = (
        contract_dir
        / "formalization_gap_planner_cross_prover_target_summary.schema.json"
    )
    component_resource_resource_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_component_resource_resource_row.schema.json"
    )
    component_resource_component_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_component_resource_component_row.schema.json"
    )
    component_resource_contract_row_schema_path = (
        contract_dir
        / "formalization_gap_planner_component_resource_contract_row.schema.json"
    )
    schema_path.write_text(json.dumps(schema_payload, indent=2), encoding="utf-8")
    prover_adapter_packet_schema_path.write_text(
        json.dumps(prover_adapter_packet_schema, indent=2),
        encoding="utf-8",
    )
    prover_adapter_response_validation_row_schema_path.write_text(
        json.dumps(prover_adapter_response_validation_row_schema, indent=2),
        encoding="utf-8",
    )
    refinement_tool_response_schema_path.write_text(
        json.dumps(refinement_tool_response_schema, indent=2),
        encoding="utf-8",
    )
    refinement_work_item_schema_path.write_text(
        json.dumps(refinement_work_item_schema, indent=2),
        encoding="utf-8",
    )
    refinement_evidence_row_schema_path.write_text(
        json.dumps(refinement_evidence_row_schema, indent=2),
        encoding="utf-8",
    )
    interactive_session_row_schema_path.write_text(
        json.dumps(interactive_session_row_schema, indent=2),
        encoding="utf-8",
    )
    interactive_decision_policy_row_schema_path.write_text(
        json.dumps(interactive_decision_policy_row_schema, indent=2),
        encoding="utf-8",
    )
    minimal_delta_decision_row_schema_path.write_text(
        json.dumps(minimal_delta_decision_row_schema, indent=2),
        encoding="utf-8",
    )
    portable_plan_audit_row_schema_path.write_text(
        json.dumps(portable_plan_audit_row_schema, indent=2),
        encoding="utf-8",
    )
    library_coverage_map_row_schema_path.write_text(
        json.dumps(library_coverage_map_row_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_request_schema_path.write_text(
        json.dumps(llm_route_planner_request_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_library_alignment_summary_schema_path.write_text(
        json.dumps(llm_route_planner_library_alignment_summary_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_target_theorem_context_packet_schema_path.write_text(
        json.dumps(
            llm_route_planner_target_theorem_context_packet_schema,
            indent=2,
        ),
        encoding="utf-8",
    )
    llm_route_planner_route_planning_brief_schema_path.write_text(
        json.dumps(llm_route_planner_route_planning_brief_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_response_schema_path.write_text(
        json.dumps(llm_route_planner_response_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_response_payload_schema_path.write_text(
        json.dumps(llm_route_planner_response_payload_schema_payload, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_response_payload_lean_legacy_schema_path.write_text(
        json.dumps(llm_route_planner_response_payload_lean_legacy_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_response_payload_target_prover_schema_path.write_text(
        json.dumps(llm_route_planner_response_payload_target_prover_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_response_payload_validation_manifest_schema_path.write_text(
        json.dumps(
            llm_route_planner_response_payload_validation_manifest_schema,
            indent=2,
        ),
        encoding="utf-8",
    )
    llm_route_planner_response_payload_validation_row_schema_path.write_text(
        json.dumps(
            llm_route_planner_response_payload_validation_row_schema,
            indent=2,
        ),
        encoding="utf-8",
    )
    llm_route_planner_manifest_schema_path.write_text(
        json.dumps(llm_route_planner_manifest_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_row_schema_path.write_text(
        json.dumps(llm_route_planner_row_schema, indent=2),
        encoding="utf-8",
    )
    llm_route_planner_model_tier_decision_ledger_schema_path.write_text(
        json.dumps(
            llm_route_planner_model_tier_decision_ledger_schema,
            indent=2,
        ),
        encoding="utf-8",
    )
    llm_route_planner_provider_usage_row_schema_path.write_text(
        json.dumps(
            llm_route_planner_provider_usage_row_schema,
            indent=2,
        ),
        encoding="utf-8",
    )
    route_adoption_blocker_taxonomy_schema_path.write_text(
        json.dumps(route_adoption_blocker_taxonomy_schema, indent=2),
        encoding="utf-8",
    )
    route_adoption_blocker_taxonomy_manifest_schema_path.write_text(
        json.dumps(route_adoption_blocker_taxonomy_manifest_schema, indent=2),
        encoding="utf-8",
    )
    route_adoption_blocker_taxonomy_path.write_text(
        json.dumps(route_adoption_blocker_taxonomy_contract, indent=2),
        encoding="utf-8",
    )
    primitive_action_queue_row_schema_path.write_text(
        json.dumps(primitive_action_queue_row_schema, indent=2),
        encoding="utf-8",
    )
    action_resource_plan_row_schema_path.write_text(
        json.dumps(action_resource_plan_row_schema, indent=2),
        encoding="utf-8",
    )
    resource_request_queue_row_schema_path.write_text(
        json.dumps(resource_request_queue_row_schema, indent=2),
        encoding="utf-8",
    )
    resource_response_schema_path.write_text(
        json.dumps(resource_response_schema, indent=2),
        encoding="utf-8",
    )
    resource_response_ledger_row_schema_path.write_text(
        json.dumps(resource_response_ledger_row_schema, indent=2),
        encoding="utf-8",
    )
    source_grounding_row_schema_path.write_text(
        json.dumps(source_grounding_row_schema, indent=2),
        encoding="utf-8",
    )
    route_revision_overlay_row_schema_path.write_text(
        json.dumps(route_revision_overlay_row_schema, indent=2),
        encoding="utf-8",
    )
    route_stability_audit_row_schema_path.write_text(
        json.dumps(route_stability_audit_row_schema, indent=2),
        encoding="utf-8",
    )
    route_replan_handoff_row_schema_path.write_text(
        json.dumps(route_replan_handoff_row_schema, indent=2),
        encoding="utf-8",
    )
    route_replan_handoff_audit_row_schema_path.write_text(
        json.dumps(route_replan_handoff_audit_row_schema, indent=2),
        encoding="utf-8",
    )
    runtime_handoff_audit_row_schema_path.write_text(
        json.dumps(runtime_handoff_audit_row_schema, indent=2),
        encoding="utf-8",
    )
    proof_state_triage_row_schema_path.write_text(
        json.dumps(proof_state_triage_row_schema, indent=2),
        encoding="utf-8",
    )
    ablation_study_row_schema_path.write_text(
        json.dumps(ablation_study_row_schema, indent=2),
        encoding="utf-8",
    )
    route_alignment_edge_schema_path.write_text(
        json.dumps(route_alignment_edge_schema, indent=2),
        encoding="utf-8",
    )
    portable_plan_row_schema_path.write_text(
        json.dumps(portable_gap_plan_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    schema_catalog_schema_path.write_text(
        json.dumps(schema_catalog_json_schema(), indent=2),
        encoding="utf-8",
    )
    publication_bundle_manifest_schema_path.write_text(
        json.dumps(publication_bundle_manifest_json_schema(), indent=2),
        encoding="utf-8",
    )
    prover_adapter_schema_path.write_text(
        json.dumps(prover_adapter_response_schema, indent=2),
        encoding="utf-8",
    )
    standalone_schema_path.write_text(
        json.dumps(standalone_input_json_schema(), indent=2),
        encoding="utf-8",
    )
    llm_route_planner_seed_route_selection_schema_path.write_text(
        json.dumps(llm_route_planner_seed_route_selection_schema, indent=2),
        encoding="utf-8",
    )
    target_intake_schema_path.write_text(
        json.dumps(target_intake_json_schema(), indent=2),
        encoding="utf-8",
    )
    target_intake_row_schema_path.write_text(
        json.dumps(target_intake_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    component_execution_plan_schema_path.write_text(
        json.dumps(component_execution_plan_schema, indent=2),
        encoding="utf-8",
    )
    component_resource_resource_row_schema_path.write_text(
        json.dumps(component_resource_resource_row_schema, indent=2),
        encoding="utf-8",
    )
    component_resource_component_row_schema_path.write_text(
        json.dumps(component_resource_component_row_schema, indent=2),
        encoding="utf-8",
    )
    component_resource_contract_row_schema_path.write_text(
        json.dumps(component_resource_contract_row_schema, indent=2),
        encoding="utf-8",
    )
    benchmark_route_schema_path.write_text(
        json.dumps(benchmark_route_schema, indent=2),
        encoding="utf-8",
    )
    evaluation_row_schema_path.write_text(
        json.dumps(evaluation_row_schema, indent=2),
        encoding="utf-8",
    )
    adapter_registry_row_schema_path.write_text(
        json.dumps(adapter_registry_row_schema, indent=2),
        encoding="utf-8",
    )
    cross_prover_matrix_audit_row_schema_path.write_text(
        json.dumps(cross_prover_matrix_audit_row_schema, indent=2),
        encoding="utf-8",
    )
    cross_prover_target_summary_schema_path.write_text(
        json.dumps(cross_prover_target_summary_schema, indent=2),
        encoding="utf-8",
    )
    llm_model_policy_path.write_text(
        json.dumps(llm_model_policy_payload, indent=2, default=str),
        encoding="utf-8",
    )
    llm_model_policy_report_path.write_text(
        _llm_model_policy_markdown(llm_model_policy_payload),
        encoding="utf-8",
    )
    contract_path.write_text(json.dumps(contract_payload, indent=2), encoding="utf-8")

    benchmark_payload = export_formalization_gap_planner_benchmark(
        out_dir / "benchmark",
        ground_truth_path=ground_truth_path,
    )
    benchmark_audit_payload = audit_formalization_gap_planner_benchmark(
        out_dir / "benchmark",
        out_dir / "benchmark_audit",
    )
    adapter_registry_payload = export_formalization_gap_planner_adapter_registry(
        out_dir / "adapter_registry",
        lean_rag_db_path=lean_rag_db_path,
        paper_library_dir=paper_library_dir,
    )
    component_resource_registry_payload = (
        export_formalization_gap_planner_component_resource_registry(
            out_dir / "component_resource_registry",
            formalization_gap_planner_adapter_registry_dir=out_dir / "adapter_registry",
        )
    )

    copied_docs = _copy_docs(docs_dir, errors)
    copied_examples = _copy_example_inputs(examples_dir, errors)
    optional_artifacts = []
    optional_specs = (
        (
            "formalization_gap_planner_target_intake",
            formalization_gap_planner_target_intake_dir,
        ),
        (
            "formalization_gap_planner_llm_route_planner",
            formalization_gap_planner_llm_route_planner_dir,
        ),
        (
            "formalization_gap_planner_feedback_llm_route_planner",
            formalization_gap_planner_feedback_llm_route_planner_dir,
        ),
        (
            "formalization_gap_planner_llm_route_planner_response_payload_validation",
            formalization_gap_planner_llm_route_planner_response_payload_validation_dir,
        ),
        (
            "goal_conditioned_minimal_formalization_plan",
            goal_conditioned_minimal_formalization_plan_dir,
        ),
        (
            "formalization_gap_planner_evaluation",
            formalization_gap_planner_evaluation_dir,
        ),
        (
            "formalization_gap_planner_ablation_study",
            formalization_gap_planner_ablation_study_dir,
        ),
        (
            "formalization_gap_planner_portable_plan_audit",
            formalization_gap_planner_portable_plan_audit_dir,
        ),
        (
            "formalization_gap_planner_library_coverage_map",
            formalization_gap_planner_library_coverage_map_dir,
        ),
        (
            "formalization_gap_planner_primitive_action_queue",
            formalization_gap_planner_primitive_action_queue_dir,
        ),
        (
            "formalization_gap_planner_action_resource_plan",
            formalization_gap_planner_action_resource_plan_dir,
        ),
        (
            "formalization_gap_planner_resource_request_queue",
            formalization_gap_planner_resource_request_queue_dir,
        ),
        (
            "formalization_gap_planner_resource_response_ledger",
            formalization_gap_planner_resource_response_ledger_dir,
        ),
        (
            "formalization_gap_planner_minimal_delta_audit",
            formalization_gap_planner_minimal_delta_audit_dir,
        ),
        (
            "formalization_gap_planner_minimal_delta_audit_feedback_adapter",
            formalization_gap_planner_minimal_delta_audit_feedback_adapter_dir,
        ),
        (
            "formalization_gap_planner_source_grounding_audit",
            formalization_gap_planner_source_grounding_audit_dir,
        ),
        (
            "formalization_gap_planner_refinement_queue",
            formalization_gap_planner_refinement_queue_dir,
        ),
        (
            "formalization_gap_planner_refinement_adapter",
            formalization_gap_planner_refinement_adapter_dir,
        ),
        (
            "formalization_gap_planner_local_literature_adapter",
            formalization_gap_planner_local_literature_adapter_dir,
        ),
        (
            "formalization_gap_planner_local_formal_source_adapter",
            formalization_gap_planner_local_formal_source_adapter_dir,
        ),
        (
            "formalization_gap_planner_local_proof_state_adapter",
            formalization_gap_planner_local_proof_state_adapter_dir,
        ),
        (
            "formalization_gap_planner_prover_adapter_feedback_adapter",
            formalization_gap_planner_prover_adapter_feedback_adapter_dir,
        ),
        (
            "formalization_gap_planner_refinement_evidence",
            formalization_gap_planner_refinement_evidence_dir,
        ),
        (
            "formalization_gap_planner_route_revision_overlay",
            formalization_gap_planner_route_revision_overlay_dir,
        ),
        (
            "formalization_gap_planner_route_stability_audit",
            formalization_gap_planner_route_stability_audit_dir,
        ),
        (
            "formalization_gap_planner_route_replan_handoff",
            formalization_gap_planner_route_replan_handoff_dir,
        ),
        (
            "formalization_gap_planner_route_replan_handoff_audit",
            formalization_gap_planner_route_replan_handoff_audit_dir,
        ),
        (
            "formalization_gap_planner_runtime_handoff_audit",
            formalization_gap_planner_runtime_handoff_audit_dir,
        ),
        (
            "formalization_gap_planner_proof_state_triage",
            formalization_gap_planner_proof_state_triage_dir,
        ),
        (
            "formalization_gap_planner_interactive_session",
            formalization_gap_planner_interactive_session_dir,
        ),
        (
            "formalization_gap_planner_prover_adapter_contract",
            formalization_gap_planner_prover_adapter_contract_dir,
        ),
        (
            "formalization_gap_planner_cross_prover_matrix_audit",
            formalization_gap_planner_cross_prover_matrix_audit_dir,
        ),
        (
            "formalization_gap_planner_adapter_registry_audit",
            formalization_gap_planner_adapter_registry_audit_dir,
        ),
        (
            "formalization_gap_planner_component_resource_registry_audit",
            formalization_gap_planner_component_resource_registry_audit_dir,
        ),
    )
    for artifact_name, source_dir in optional_specs:
        optional_artifacts.append(
            _copy_optional_artifact(
                artifact_name,
                source_dir,
                artifacts_dir / artifact_name,
                errors,
            )
        )
    optional_artifact_ok = {
        str(row.get("artifact_name", "")): bool(row.get("requested", False))
        and bool(row.get("ok", False))
        for row in optional_artifacts
        if isinstance(row, dict)
    }
    bundle_id = "formalization_gap_planner_publication_bundle:" + stable_hash(
        [
            PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
            benchmark_payload.get("benchmark_fingerprint", ""),
            benchmark_audit_payload.get("benchmark_audit_fingerprint", ""),
            adapter_registry_payload.get("adapter_registry_fingerprint", ""),
            component_resource_registry_payload.get(
                "component_resource_registry_fingerprint", ""
            ),
            optional_artifacts,
        ]
    )[:20]
    reproduction_payload = _reproduction_payload(
        bundle_id,
        library_snapshot_ref=library_snapshot_ref,
        has_optional_plan=optional_artifact_ok.get(
            "goal_conditioned_minimal_formalization_plan",
            False,
        ),
        has_optional_llm_route_planner=optional_artifact_ok.get(
            "formalization_gap_planner_llm_route_planner",
            False,
        ),
        has_optional_feedback_llm_route_planner=optional_artifact_ok.get(
            "formalization_gap_planner_feedback_llm_route_planner",
            False,
        ),
        has_optional_evaluation=optional_artifact_ok.get(
            "formalization_gap_planner_evaluation",
            False,
        ),
        has_optional_interactive_session=optional_artifact_ok.get(
            "formalization_gap_planner_interactive_session",
            False,
        ),
        has_optional_runtime_handoff_audit=optional_artifact_ok.get(
            "formalization_gap_planner_runtime_handoff_audit",
            False,
        ),
    )
    reproduction_manifest_path = (
        reproduce_dir / "formalization_gap_planner_reproduction_manifest.json"
    )
    reproduction_report_path = (
        reproduce_dir / "formalization_gap_planner_reproduction.md"
    )
    reproduction_manifest_path.write_text(
        json.dumps(reproduction_payload, indent=2, default=str),
        encoding="utf-8",
    )
    reproduction_report_path.write_text(
        _reproduction_markdown(reproduction_payload),
        encoding="utf-8",
    )

    core_artifacts = (
        {
            "artifact_name": "portable_contract",
            "path": str(contract_path),
            "required": True,
            "ok": contract_payload["schema_id"] == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_model_policy",
            "path": str(llm_model_policy_path),
            "required": True,
            "ok": bool(llm_model_policy_payload.get("all_ok")),
        },
        {
            "artifact_name": "llm_model_policy_report",
            "path": str(llm_model_policy_report_path),
            "required": True,
            "ok": llm_model_policy_report_path.exists()
            and "Claude Haiku" in llm_model_policy_report_path.read_text(
                encoding="utf-8"
            ),
        },
        {
            "artifact_name": "portable_schema",
            "path": str(schema_path),
            "required": True,
            "ok": schema_payload.get("$id") == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        },
        {
            "artifact_name": "schema_catalog_schema",
            "path": str(schema_catalog_schema_path),
            "required": True,
            "ok": schema_catalog_json_schema().get("$id")
            == FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID,
        },
        {
            "artifact_name": "publication_bundle_manifest_schema",
            "path": str(publication_bundle_manifest_schema_path),
            "required": True,
            "ok": publication_bundle_manifest_json_schema().get("$id")
            == FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID,
        },
        {
            "artifact_name": "prover_adapter_packet_schema",
            "path": str(prover_adapter_packet_schema_path),
            "required": True,
            "ok": prover_adapter_packet_schema.get("$id")
            == PROVER_ADAPTER_PACKET_SCHEMA_ID,
        },
        {
            "artifact_name": "prover_adapter_response_schema",
            "path": str(prover_adapter_schema_path),
            "required": True,
            "ok": prover_adapter_response_schema.get("$id")
            == PROVER_ADAPTER_RESPONSE_SCHEMA_ID,
        },
        {
            "artifact_name": "prover_adapter_response_validation_row_schema",
            "path": str(prover_adapter_response_validation_row_schema_path),
            "required": True,
            "ok": prover_adapter_response_validation_row_schema.get("$id")
            == PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID,
        },
        {
            "artifact_name": "refinement_tool_response_schema",
            "path": str(refinement_tool_response_schema_path),
            "required": True,
            "ok": refinement_tool_response_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
        },
        {
            "artifact_name": "refinement_evidence_row_schema",
            "path": str(refinement_evidence_row_schema_path),
            "required": True,
            "ok": refinement_evidence_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-evidence-row:1",
        },
        {
            "artifact_name": "refinement_work_item_schema",
            "path": str(refinement_work_item_schema_path),
            "required": True,
            "ok": refinement_work_item_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-work-item:1",
        },
        {
            "artifact_name": "proof_state_triage_row_schema",
            "path": str(proof_state_triage_row_schema_path),
            "required": True,
            "ok": proof_state_triage_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-proof-state-triage-row:1",
        },
        {
            "artifact_name": "interactive_session_row_schema",
            "path": str(interactive_session_row_schema_path),
            "required": True,
            "ok": interactive_session_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-interactive-session-row:1",
        },
        {
            "artifact_name": "interactive_decision_policy_row_schema",
            "path": str(interactive_decision_policy_row_schema_path),
            "required": True,
            "ok": interactive_decision_policy_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-interactive-decision-policy-row:1",
        },
        {
            "artifact_name": "minimal_delta_decision_row_schema",
            "path": str(minimal_delta_decision_row_schema_path),
            "required": True,
            "ok": minimal_delta_decision_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-minimal-delta-decision-row:1",
        },
        {
            "artifact_name": "portable_plan_audit_row_schema",
            "path": str(portable_plan_audit_row_schema_path),
            "required": True,
            "ok": portable_plan_audit_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-portable-plan-audit-row:1",
        },
        {
            "artifact_name": "library_coverage_map_row_schema",
            "path": str(library_coverage_map_row_schema_path),
            "required": True,
            "ok": library_coverage_map_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-library-coverage-map-row:1",
        },
        {
            "artifact_name": "llm_route_planner_request_schema",
            "path": str(llm_route_planner_request_schema_path),
            "required": True,
            "ok": llm_route_planner_request_schema.get("$id")
            == LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_library_alignment_summary_schema",
            "path": str(llm_route_planner_library_alignment_summary_schema_path),
            "required": True,
            "ok": llm_route_planner_library_alignment_summary_schema.get("$id")
            == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_target_theorem_context_packet_schema",
            "path": str(llm_route_planner_target_theorem_context_packet_schema_path),
            "required": True,
            "ok": llm_route_planner_target_theorem_context_packet_schema.get("$id")
            == LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_route_planning_brief_schema",
            "path": str(llm_route_planner_route_planning_brief_schema_path),
            "required": True,
            "ok": llm_route_planner_route_planning_brief_schema.get("$id")
            == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_response_schema",
            "path": str(llm_route_planner_response_schema_path),
            "required": True,
            "ok": llm_route_planner_response_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_response_payload_schema",
            "path": str(llm_route_planner_response_payload_schema_path),
            "required": True,
            "ok": llm_route_planner_response_payload_schema_payload.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_response_payload_lean_legacy_schema",
            "path": str(llm_route_planner_response_payload_lean_legacy_schema_path),
            "required": True,
            "ok": llm_route_planner_response_payload_lean_legacy_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_response_payload_target_prover_schema",
            "path": str(llm_route_planner_response_payload_target_prover_schema_path),
            "required": True,
            "ok": llm_route_planner_response_payload_target_prover_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID,
        },
        {
            "artifact_name": (
                "llm_route_planner_response_payload_validation_manifest_schema"
            ),
            "path": str(
                llm_route_planner_response_payload_validation_manifest_schema_path
            ),
            "required": True,
            "ok": llm_route_planner_response_payload_validation_manifest_schema.get(
                "$id"
            )
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_response_payload_validation_row_schema",
            "path": str(llm_route_planner_response_payload_validation_row_schema_path),
            "required": True,
            "ok": llm_route_planner_response_payload_validation_row_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_manifest_schema",
            "path": str(llm_route_planner_manifest_schema_path),
            "required": True,
            "ok": llm_route_planner_manifest_schema.get("$id")
            == LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_row_schema",
            "path": str(llm_route_planner_row_schema_path),
            "required": True,
            "ok": llm_route_planner_row_schema.get("$id")
            == LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_model_tier_decision_ledger_schema",
            "path": str(llm_route_planner_model_tier_decision_ledger_schema_path),
            "required": True,
            "ok": llm_route_planner_model_tier_decision_ledger_schema.get("$id")
            == LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID,
        },
        {
            "artifact_name": "llm_route_planner_provider_usage_row_schema",
            "path": str(llm_route_planner_provider_usage_row_schema_path),
            "required": True,
            "ok": llm_route_planner_provider_usage_row_schema.get("$id")
            == LLM_ROUTE_PLANNER_PROVIDER_USAGE_ROW_SCHEMA_ID,
        },
        {
            "artifact_name": "route_adoption_blocker_taxonomy_schema",
            "path": str(route_adoption_blocker_taxonomy_schema_path),
            "required": True,
            "ok": route_adoption_blocker_taxonomy_schema.get("$id")
            == ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
        },
        {
            "artifact_name": "route_adoption_blocker_taxonomy_manifest_schema",
            "path": str(route_adoption_blocker_taxonomy_manifest_schema_path),
            "required": True,
            "ok": route_adoption_blocker_taxonomy_manifest_schema.get("$id")
            == ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID,
        },
        {
            "artifact_name": "route_adoption_blocker_taxonomy_contract",
            "path": str(route_adoption_blocker_taxonomy_path),
            "required": True,
            "ok": not validate_route_adoption_blocker_taxonomy_payload(
                route_adoption_blocker_taxonomy_contract
            ),
        },
        {
            "artifact_name": "primitive_action_queue_row_schema",
            "path": str(primitive_action_queue_row_schema_path),
            "required": True,
            "ok": primitive_action_queue_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-primitive-action-queue-row:1",
        },
        {
            "artifact_name": "action_resource_plan_row_schema",
            "path": str(action_resource_plan_row_schema_path),
            "required": True,
            "ok": action_resource_plan_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-action-resource-plan-row:1",
        },
        {
            "artifact_name": "resource_request_queue_row_schema",
            "path": str(resource_request_queue_row_schema_path),
            "required": True,
            "ok": resource_request_queue_row_schema.get("$id")
            == RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
        },
        {
            "artifact_name": "resource_response_schema",
            "path": str(resource_response_schema_path),
            "required": True,
            "ok": resource_response_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-resource-response:1",
        },
        {
            "artifact_name": "resource_response_ledger_row_schema",
            "path": str(resource_response_ledger_row_schema_path),
            "required": True,
            "ok": resource_response_ledger_row_schema.get("$id")
            == RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
        },
        {
            "artifact_name": "source_grounding_row_schema",
            "path": str(source_grounding_row_schema_path),
            "required": True,
            "ok": source_grounding_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-source-grounding-row:1",
        },
        {
            "artifact_name": "route_stability_audit_row_schema",
            "path": str(route_stability_audit_row_schema_path),
            "required": True,
            "ok": route_stability_audit_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-stability-audit-row:1",
        },
        {
            "artifact_name": "route_revision_overlay_row_schema",
            "path": str(route_revision_overlay_row_schema_path),
            "required": True,
            "ok": route_revision_overlay_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-revision-overlay-row:1",
        },
        {
            "artifact_name": "route_replan_handoff_row_schema",
            "path": str(route_replan_handoff_row_schema_path),
            "required": True,
            "ok": route_replan_handoff_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-row:1",
        },
        {
            "artifact_name": "route_replan_handoff_audit_row_schema",
            "path": str(route_replan_handoff_audit_row_schema_path),
            "required": True,
            "ok": route_replan_handoff_audit_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-audit-row:1",
        },
        {
            "artifact_name": "runtime_handoff_audit_row_schema",
            "path": str(runtime_handoff_audit_row_schema_path),
            "required": True,
            "ok": runtime_handoff_audit_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-runtime-handoff-audit-row:1",
        },
        {
            "artifact_name": "ablation_study_row_schema",
            "path": str(ablation_study_row_schema_path),
            "required": True,
            "ok": ablation_study_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-ablation-study-row:1",
        },
        {
            "artifact_name": "route_alignment_edge_schema",
            "path": str(route_alignment_edge_schema_path),
            "required": True,
            "ok": route_alignment_edge_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-alignment-edge:1",
        },
        {
            "artifact_name": "portable_plan_row_schema",
            "path": str(portable_plan_row_schema_path),
            "required": True,
            "ok": portable_gap_plan_row_json_schema().get("$id")
            == "urn:ai-statistician:schemas:library-aware-formalization-gap-plan-row:1",
        },
        {
            "artifact_name": "standalone_input_schema",
            "path": str(standalone_schema_path),
            "required": True,
            "ok": bool(standalone_input_json_schema().get("required")),
        },
        {
            "artifact_name": "llm_route_planner_seed_route_selection_schema",
            "path": str(llm_route_planner_seed_route_selection_schema_path),
            "required": True,
            "ok": llm_route_planner_seed_route_selection_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
        },
        {
            "artifact_name": "target_intake_schema",
            "path": str(target_intake_schema_path),
            "required": True,
            "ok": target_intake_json_schema().get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-target-intake:1",
        },
        {
            "artifact_name": "target_intake_row_schema",
            "path": str(target_intake_row_schema_path),
            "required": True,
            "ok": target_intake_row_json_schema().get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-target-intake-row:1",
        },
        {
            "artifact_name": "component_execution_plan_schema",
            "path": str(component_execution_plan_schema_path),
            "required": True,
            "ok": component_execution_plan_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-component-execution-plan:1",
        },
        {
            "artifact_name": "component_resource_resource_row_schema",
            "path": str(component_resource_resource_row_schema_path),
            "required": True,
            "ok": component_resource_resource_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-registry-resource-row:1",
        },
        {
            "artifact_name": "component_resource_component_row_schema",
            "path": str(component_resource_component_row_schema_path),
            "required": True,
            "ok": component_resource_component_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-registry-component-row:1",
        },
        {
            "artifact_name": "component_resource_contract_row_schema",
            "path": str(component_resource_contract_row_schema_path),
            "required": True,
            "ok": component_resource_contract_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-contract-row:1",
        },
        {
            "artifact_name": "benchmark_route_schema",
            "path": str(benchmark_route_schema_path),
            "required": True,
            "ok": benchmark_route_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-benchmark-route-row:1",
        },
        {
            "artifact_name": "evaluation_row_schema",
            "path": str(evaluation_row_schema_path),
            "required": True,
            "ok": evaluation_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-evaluation-row:1",
        },
        {
            "artifact_name": "adapter_registry_row_schema",
            "path": str(adapter_registry_row_schema_path),
            "required": True,
            "ok": adapter_registry_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-adapter-registry-row:1",
        },
        {
            "artifact_name": "cross_prover_matrix_audit_row_schema",
            "path": str(cross_prover_matrix_audit_row_schema_path),
            "required": True,
            "ok": cross_prover_matrix_audit_row_schema.get("$id")
            == CROSS_PROVER_MATRIX_AUDIT_ROW_SCHEMA_ID,
        },
        {
            "artifact_name": "cross_prover_target_summary_schema",
            "path": str(cross_prover_target_summary_schema_path),
            "required": True,
            "ok": cross_prover_target_summary_schema.get("$id")
            == CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
        },
        {
            "artifact_name": "benchmark",
            "path": str(out_dir / "benchmark" / "formalization_gap_planner_benchmark_manifest.json"),
            "required": True,
            "ok": bool(benchmark_payload.get("all_ok")),
        },
        {
            "artifact_name": "benchmark_audit",
            "path": str(
                out_dir
                / "benchmark_audit"
                / "formalization_gap_planner_benchmark_audit_manifest.json"
            ),
            "required": True,
            "ok": bool(benchmark_audit_payload.get("all_ok")),
        },
        {
            "artifact_name": "adapter_registry",
            "path": str(
                out_dir
                / "adapter_registry"
                / "formalization_gap_planner_adapter_registry_manifest.json"
            ),
            "required": True,
            "ok": bool(adapter_registry_payload.get("all_ok")),
        },
        {
            "artifact_name": "component_resource_registry",
            "path": str(
                out_dir
                / "component_resource_registry"
                / "formalization_gap_planner_component_resource_registry_manifest.json"
            ),
            "required": True,
            "ok": bool(component_resource_registry_payload.get("all_ok")),
        },
        {
            "artifact_name": "reproduction_manifest",
            "path": str(reproduction_manifest_path),
            "required": True,
            "ok": bool(reproduction_payload.get("all_ok"))
            and reproduction_manifest_path.exists()
            and reproduction_report_path.exists(),
        },
        {
            "artifact_name": "example_inputs",
            "path": str(examples_dir),
            "required": True,
            "ok": len(copied_examples) >= 2
            and all(Path(str(row.get("path", ""))).exists() for row in copied_examples),
        },
    )
    schema_catalog_payload = _schema_catalog_payload(
        bundle_id=bundle_id,
        bundle_dir=out_dir,
        library_snapshot_ref=library_snapshot_ref,
        core_artifacts=core_artifacts,
    )
    schema_catalog_contract_errors = validate_schema_catalog_payload(
        schema_catalog_payload,
        bundle_dir=out_dir,
    )
    schema_catalog_path.write_text(
        json.dumps(schema_catalog_payload, indent=2, default=str),
        encoding="utf-8",
    )
    core_artifacts = (
        *core_artifacts,
        {
            "artifact_name": "schema_catalog",
            "path": str(schema_catalog_path),
            "required": True,
            "ok": bool(schema_catalog_payload.get("all_ok", False))
            and not schema_catalog_contract_errors,
        },
    )
    example_target_prover_families = _example_target_prover_families(copied_examples)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": PUBLICATION_BUNDLE_COMPONENT_NAME,
        "packaged_component": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "bundle_id": bundle_id,
        "out_dir": str(out_dir),
        "ground_truth_path": str(
            ground_truth_path or default_formalization_gap_planner_ground_truth_path()
        ),
        "lean_rag_db_path": str(lean_rag_db_path or ""),
        "paper_library_dir": str(paper_library_dir or ""),
        "library_snapshot_ref": library_snapshot_ref,
        "n_core_artifacts": len(core_artifacts),
        "n_core_artifacts_ok": sum(1 for artifact in core_artifacts if artifact["ok"]),
        "n_optional_artifacts_requested": sum(
            1 for artifact in optional_artifacts if artifact["requested"]
        ),
        "n_optional_artifact_files_copied": sum(
            int(artifact["n_files_copied"]) for artifact in optional_artifacts
        ),
        "n_docs_copied": len(copied_docs),
        "n_example_inputs_copied": len(copied_examples),
        "example_target_prover_families": example_target_prover_families,
        "n_example_target_prover_families": len(example_target_prover_families),
        "has_non_lean_example_input": any(
            family != "lean4" for family in example_target_prover_families
        ),
        "core_artifacts": core_artifacts,
        "optional_artifacts": optional_artifacts,
        "copied_docs": copied_docs,
        "copied_examples": copied_examples,
        "reproduction_manifest": str(reproduction_manifest_path),
        "reproduction_report": str(reproduction_report_path),
        "reproduction_summary": {
            "n_entrypoints": reproduction_payload.get("n_entrypoints", 0),
            "n_commands": reproduction_payload.get("n_commands", 0),
            "n_bundle_relative_artifacts": reproduction_payload.get(
                "n_bundle_relative_artifacts",
                0,
            ),
        },
        "schema_catalog_summary": {
            "schema_id": schema_catalog_payload.get("schema_id", ""),
            "n_schema_entries": schema_catalog_payload.get("n_schema_entries", 0),
            "n_missing_schema_ids": schema_catalog_payload.get(
                "n_missing_schema_ids",
                0,
            ),
            "n_missing_schema_files": schema_catalog_payload.get(
                "n_missing_schema_files",
                0,
            ),
            "n_schema_catalog_contract_errors": len(schema_catalog_contract_errors),
            "all_ok": bool(schema_catalog_payload.get("all_ok", False))
            and not schema_catalog_contract_errors,
        },
        "benchmark_summary": {
            "n_routes": benchmark_payload.get("n_routes", 0),
            "n_route_row_schema_valid": benchmark_payload.get(
                "n_route_row_schema_valid", 0
            ),
            "n_route_row_schema_invalid": benchmark_payload.get(
                "n_route_row_schema_invalid", 0
            ),
            "n_required_primitives": benchmark_payload.get("n_required_primitives", 0),
            "n_kernel_verified_routes": benchmark_payload.get("n_kernel_verified_routes", 0),
            "n_kernel_verification_witnesses": benchmark_payload.get(
                "n_kernel_verification_witnesses",
                0,
            ),
            "n_kernel_verified_routes_with_witnesses": benchmark_payload.get(
                "n_kernel_verified_routes_with_witnesses",
                0,
            ),
            "n_kernel_verified_routes_missing_witnesses": benchmark_payload.get(
                "n_kernel_verified_routes_missing_witnesses",
                0,
            ),
            "benchmark_fingerprint": benchmark_payload.get("benchmark_fingerprint", ""),
        },
        "benchmark_audit_summary": {
            "n_checks": benchmark_audit_payload.get("n_checks", 0),
            "n_failed": benchmark_audit_payload.get("n_failed", 0),
            "n_evaluation_splits": benchmark_audit_payload.get("n_evaluation_splits", 0),
            "n_routes_with_source_refs": benchmark_audit_payload.get(
                "n_routes_with_source_refs", 0
            ),
            "benchmark_audit_fingerprint": benchmark_audit_payload.get(
                "benchmark_audit_fingerprint", ""
            ),
        },
        "evaluation_summary": _evaluation_manifest_summary(
            formalization_gap_planner_evaluation_dir
        ),
        "llm_route_planner_summary": _llm_route_planner_manifest_summary(
            formalization_gap_planner_llm_route_planner_dir
        ),
        "feedback_llm_route_planner_summary": _llm_route_planner_manifest_summary(
            formalization_gap_planner_feedback_llm_route_planner_dir
        ),
        "llm_route_planner_response_payload_validation_summary": (
            _llm_route_planner_response_payload_validation_summary(
                formalization_gap_planner_llm_route_planner_response_payload_validation_dir
            )
        ),
        "library_coverage_map_summary": _library_coverage_map_summary(
            formalization_gap_planner_library_coverage_map_dir
        ),
        "adapter_registry_summary": {
            "n_adapters": adapter_registry_payload.get("n_adapters", 0),
            "n_adapter_row_schema_valid": adapter_registry_payload.get(
                "n_adapter_row_schema_valid", 0
            ),
            "n_adapter_row_schema_invalid": adapter_registry_payload.get(
                "n_adapter_row_schema_invalid", 0
            ),
            "n_ready_local_or_configured": adapter_registry_payload.get(
                "n_ready_local_or_configured", 0
            ),
            "n_contract_only": adapter_registry_payload.get("n_contract_only", 0),
            "adapter_registry_fingerprint": adapter_registry_payload.get(
                "adapter_registry_fingerprint", ""
            ),
        },
        "component_resource_registry_summary": {
            "n_component_rows": component_resource_registry_payload.get(
                "n_component_rows", 0
            ),
            "n_component_row_schema_valid": component_resource_registry_payload.get(
                "n_component_row_schema_valid", 0
            ),
            "n_component_row_schema_invalid": component_resource_registry_payload.get(
                "n_component_row_schema_invalid", 0
            ),
            "n_execution_plan_rows": component_resource_registry_payload.get(
                "n_execution_plan_rows", 0
            ),
            "n_execution_plan_rows_ok": component_resource_registry_payload.get(
                "n_execution_plan_rows_ok", 0
            ),
            "n_execution_plan_row_schema_valid": component_resource_registry_payload.get(
                "n_execution_plan_row_schema_valid", 0
            ),
            "n_execution_plan_row_schema_invalid": component_resource_registry_payload.get(
                "n_execution_plan_row_schema_invalid", 0
            ),
            "n_resources": component_resource_registry_payload.get("n_resources", 0),
            "n_resource_row_schema_valid": component_resource_registry_payload.get(
                "n_resource_row_schema_valid", 0
            ),
            "n_resource_row_schema_invalid": component_resource_registry_payload.get(
                "n_resource_row_schema_invalid", 0
            ),
            "n_resource_contract_rows": component_resource_registry_payload.get(
                "n_resource_contract_rows", 0
            ),
            "n_resource_contract_row_schema_valid": component_resource_registry_payload.get(
                "n_resource_contract_row_schema_valid", 0
            ),
            "n_resource_contract_row_schema_invalid": component_resource_registry_payload.get(
                "n_resource_contract_row_schema_invalid", 0
            ),
            "n_frontier_resources": component_resource_registry_payload.get(
                "n_frontier_resources", 0
            ),
            "n_mcp_or_cli_resources": component_resource_registry_payload.get(
                "n_mcp_or_cli_resources", 0
            ),
            "component_resource_registry_fingerprint": component_resource_registry_payload.get(
                "component_resource_registry_fingerprint", ""
            ),
        },
        "action_resource_plan_summary": _manifest_summary(
            formalization_gap_planner_action_resource_plan_dir,
            "formalization_gap_planner_action_resource_plan_manifest.json",
            (
                "n_resource_plan_rows",
                "n_ok",
                "n_failed",
                "n_with_local_first_resources",
                "n_with_frontier_escalation_resources",
                "n_with_resource_contracts",
                "n_row_schema_valid",
                "n_row_schema_invalid",
                "all_ok",
            ),
        ),
        "resource_request_queue_summary": _manifest_summary(
            formalization_gap_planner_resource_request_queue_dir,
            "formalization_gap_planner_resource_request_queue_manifest.json",
            (
                "n_resource_request_rows",
                "n_ok",
                "n_failed",
                "n_local_first_requests",
                "n_frontier_escalation_requests",
                "n_distinct_resources",
                "n_llm_route_planner_rows",
                "n_llm_route_planner_request_packets",
                "n_llm_route_planner_request_route_planning_briefs",
                "n_llm_route_planner_route_planning_brief_evidence_gaps",
                "n_llm_route_planner_rows_with_route_adoption_preconditions",
                "n_llm_route_planner_route_adoption_precondition_known_blockers",
                "n_llm_route_planner_route_adoption_precondition_required_response_fields",
                "n_llm_route_planner_route_adoption_precondition_target_primitives",
                "n_llm_route_planner_resource_request_rows",
                "n_llm_route_planner_route_planning_brief_resource_request_rows",
                "n_llm_route_planner_total_resource_request_rows",
                "n_llm_route_planner_resource_request_rows_with_explicit_resource_binding",
                "n_llm_route_planner_resource_request_rows_matching_explicit_resource_binding",
                "n_llm_route_planner_resource_request_rows_from_hook_default_fanout",
                "n_llm_route_planner_route_planning_brief_evidence_gap_rows",
                "n_llm_route_planner_resource_request_rows_with_query_intents",
                "n_llm_route_planner_resource_request_query_intents",
                "n_llm_route_planning_brief_evidence_gap_query_intents",
                "n_llm_route_planner_resource_request_rows_with_route_adoption_preconditions",
                "n_llm_route_planner_resource_request_route_adoption_precondition_target_primitives",
                "n_row_schema_valid",
                "n_row_schema_invalid",
                "all_ok",
            ),
        ),
        "resource_response_ledger_summary": _manifest_summary(
            formalization_gap_planner_resource_response_ledger_dir,
            "formalization_gap_planner_resource_response_ledger_manifest.json",
            (
                "n_ledger_rows",
                "n_ok",
                "n_response_present",
                "n_awaiting_response",
                "n_response_contract_ok",
                "n_llm_route_planner_traced_requests",
                "n_llm_route_planner_traced_responses",
                "n_llm_route_planner_traced_route_planning_brief_evidence_gap_rows",
                "n_llm_route_planner_traced_route_planning_brief_evidence_gap_responses",
                "n_llm_route_planner_traced_route_planning_brief_evidence_gap_grounded_responses",
                "n_route_revision_recommended",
                "n_rejected",
                "n_ledger_row_schema_valid",
                "n_ledger_row_schema_invalid",
                "all_ok",
            ),
        ),
        "cross_prover_matrix_summary": _manifest_summary(
            formalization_gap_planner_cross_prover_matrix_audit_dir,
            "formalization_gap_planner_cross_prover_matrix_audit_manifest.json",
            (
                "n_targets",
                "n_targets_ok",
                "n_matrix_row_schema_valid",
                "n_matrix_row_schema_invalid",
                "n_total_packets",
                "n_total_packet_ok",
                "n_total_packet_schema_valid",
                "n_total_packets_schema_invalid",
                "n_packet_row_schema_valid",
                "n_packet_row_schema_invalid",
                "n_response_validation_row_schema_valid",
                "n_response_validation_row_schema_invalid",
                "n_response_minimal_delta_action_witnesses_required",
                "n_response_minimal_delta_action_witnesses_acknowledged",
                "n_response_minimal_delta_action_witnesses_unacknowledged",
                "n_response_addressed_minimal_delta_action_witnesses",
                "n_total_packets_with_alignment",
                "n_total_packets_missing_alignment",
                "packet_count_consistent",
                "alignment_packet_count_consistent",
                "all_ok",
            ),
        ),
        "cross_prover_formal_attempt_dependency_summary": (
            _cross_prover_formal_attempt_dependency_summary(
                formalization_gap_planner_cross_prover_matrix_audit_dir
            )
        ),
        "route_replan_handoff_summary": _manifest_summary(
            formalization_gap_planner_route_replan_handoff_dir,
            "formalization_gap_planner_route_replan_handoff_manifest.json",
            (
                "n_handoff_rows",
                "n_routes_requiring_replan",
                "n_standalone_seed_routes",
                "n_route_alignment_edges",
                "n_unaligned_primitives",
                "all_ok",
            ),
        ),
        "route_replan_handoff_audit_summary": _manifest_summary(
            formalization_gap_planner_route_replan_handoff_audit_dir,
            "formalization_gap_planner_route_replan_handoff_audit_manifest.json",
            (
                "n_checks",
                "n_failed",
                "n_handoff_rows",
                "n_seed_routes",
                "n_roundtrip_goal_plans",
                "n_roundtrip_route_alignment_edges",
                "n_row_schema_valid",
                "n_row_schema_invalid",
                "roundtrip_all_ok",
                "all_ok",
            ),
        ),
        "runtime_handoff_audit_summary": _manifest_summary(
            formalization_gap_planner_runtime_handoff_audit_dir,
            "formalization_gap_planner_runtime_handoff_audit_manifest.json",
            (
                "n_handoffs",
                "n_checks",
                "n_failed",
                "n_cost_control_ok",
                "n_live_explicit_ok",
                "n_standalone_smoke_ok",
                "n_llm_prompt_smoke_ok",
                "n_llm_prompt_packets",
                "n_llm_prompt_model_tier_mismatches",
                "n_llm_prompt_model_tier_haiku",
                "n_llm_prompt_model_tier_sonnet",
                "n_llm_prompt_model_tier_opus",
                "n_row_schema_valid",
                "n_row_schema_invalid",
                "all_ok",
            ),
        ),
        "portable_reuse_targets": PORTABLE_REUSE_TARGETS,
        "all_ok": (
            not errors
            and all(bool(artifact["ok"]) for artifact in core_artifacts)
            and all(bool(artifact["ok"]) for artifact in optional_artifacts)
        ),
        "errors": errors,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "publication bundle artifacts are planner contracts, benchmarks, and route evidence, not theorem proof evidence",
            "optional run artifacts are included only when their source directories are provided",
            "cross-prover reuse requires a prover adapter that maps portable work packets to that prover's library and kernel",
        ],
    }
    readme_path = out_dir / "formalization_gap_planner_publication_bundle.md"
    manifest_path = out_dir / "formalization_gap_planner_publication_bundle_manifest.json"
    payload["manifest_path"] = str(manifest_path)
    payload["readme_path"] = str(readme_path)
    readme_path.write_text(_markdown_report(payload), encoding="utf-8")
    manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def schema_catalog_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID,
        "title": "Formalization Gap Planner Schema Catalog",
        "description": (
            "Machine-readable index of reusable schemas and contract files "
            "packaged in a formalization gap planner publication bundle."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "schema_id",
            "component_name",
            "bundle_id",
            "library_snapshot_ref",
            "schema_entries",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "all_ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_SCHEMA_VERSION,
            },
            "schema_id": {"const": FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID},
            "component_name": {"const": SCHEMA_CATALOG_COMPONENT_NAME},
            "bundle_id": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "n_schema_entries": {"type": "integer", "minimum": 0},
            "n_missing_schema_ids": {"type": "integer", "minimum": 0},
            "n_missing_schema_files": {"type": "integer", "minimum": 0},
            "schema_entries": {
                "type": "array",
                "items": {"$ref": "#/$defs/schema_entry"},
            },
            "schema_catalog_fingerprint": {"type": "string"},
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {"type": "string", "minLength": 1},
            "all_ok": {"type": "boolean"},
            "errors": string_array,
        },
        "$defs": {
            "schema_entry": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "artifact_name",
                    "relative_path",
                    "schema_id",
                    "artifact_kind",
                    "required",
                    "ok",
                ],
                "properties": {
                    "artifact_name": {"type": "string", "minLength": 1},
                    "relative_path": {"type": "string", "minLength": 1},
                    "schema_id": {"type": "string", "minLength": 1},
                    "title": {"type": "string"},
                    "target_prover_families": string_array,
                    "artifact_kind": {
                        "enum": ["json_schema", "contract_manifest", "contract_json"]
                    },
                    "required": {"type": "boolean"},
                    "ok": {"type": "boolean"},
                    "errors": string_array,
                },
            }
        },
    }


def publication_bundle_manifest_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    route_adoption_blocker_array = {
        "type": "array",
        "items": {
            "type": "string",
            "enum": list(ROUTE_ADOPTION_BLOCKER_VALUES),
        },
    }
    nonnegative_integer = {"type": "integer", "minimum": 0}
    core_artifact_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": ["artifact_name", "path", "ok"],
        "properties": {
            "artifact_name": {"type": "string", "minLength": 1},
            "path": {"type": "string"},
            "ok": {"type": "boolean"},
        },
    }
    optional_artifact_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": ["artifact_name", "requested", "ok"],
        "properties": {
            "artifact_name": {"type": "string", "minLength": 1},
            "requested": {"type": "boolean"},
            "source_dir": {"type": "string"},
            "dest_dir": {"type": "string"},
            "n_files_copied": nonnegative_integer,
            "copied_files": string_array,
            "missing_files": string_array,
            "ok": {"type": "boolean"},
        },
    }
    evaluation_summary_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "requested",
            "n_evaluation_rows",
            "n_evaluation_row_schema_valid",
            "n_evaluation_row_schema_invalid",
            "n_realization_missing_selected_formal_primitives",
            "n_realization_missing_delta_alignment_primitives",
            "n_rows_with_incomplete_cost_hint_baseline_coverage",
            "n_realization_cost_hint_baseline_primitives",
            "n_realization_omitted_cost_hint_primitives",
            "realization_cost_hint_baseline_primitives",
            "realization_omitted_cost_hint_primitives",
            "n_minimal_delta_route_options",
            "mean_minimal_delta_selected_route_cost",
            "n_kernel_verified_ground_truth",
            "n_kernel_verification_witnesses",
            "n_kernel_verified_ground_truth_with_witnesses",
            "mean_alignment_coverage",
            "n_rows_with_llm_route_planner_residual_goal_contexts",
            "n_llm_route_planner_residual_goal_contexts",
            "n_llm_route_planner_residual_goal_context_source_refs",
            "n_llm_route_planner_residual_goal_context_provenance_values",
            "n_llm_route_planner_residual_goals_with_context",
            "n_llm_route_planner_residual_goals_without_context",
            "n_rows_with_llm_route_planner_route_option_selection_brief",
            "n_llm_route_planner_route_option_selection_candidate_options",
            "n_llm_route_planner_route_option_selection_candidate_primitives",
            "n_llm_route_planner_route_option_selection_candidates_with_residual_goals",
            "n_llm_route_planner_route_option_selection_candidate_residual_goals",
            "n_llm_route_planner_route_option_selection_lower_bound_residual_goals",
            "n_rows_with_llm_route_planner_route_option_selected_route_option",
            "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals",
            "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta",
            "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta",
            "n_llm_route_planner_route_option_selected_matches_lower_bound",
            "n_llm_route_planner_route_option_selected_mismatches_lower_bound",
            "n_llm_route_planner_route_option_selected_matches_minimal_delta",
            "n_llm_route_planner_route_option_selected_mismatches_minimal_delta",
            "n_rows_with_llm_route_planner_route_adoption_status",
            "n_rows_ready_for_route_adoption",
            "n_rows_pending_refinement_before_route_adoption",
            "n_llm_route_adoption_blockers",
            "n_llm_route_adoption_pending_quality_control_blockers",
            "n_llm_route_adoption_pending_source_grounding_blockers",
            "n_llm_route_adoption_pending_formal_attempt_queue_blockers",
            "n_rows_with_llm_route_planner_route_adoption_preconditions",
            "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions",
            "n_llm_route_planner_route_adoption_precondition_known_blockers",
            "n_llm_route_planner_route_adoption_precondition_required_response_fields",
            "n_llm_route_planner_route_adoption_precondition_target_primitives",
            "llm_route_planner_route_adoption_precondition_known_blockers",
            "llm_route_planner_route_adoption_precondition_required_response_fields",
            "llm_route_planner_route_adoption_precondition_target_primitives",
            "llm_route_adoption_blockers",
            "llm_route_adoption_blocker_counts",
            "llm_route_adoption_status_counts",
            "evaluation_by_llm_route_adoption_blocker",
            "llm_route_planner_provider_usage_summary",
            "n_rows_with_llm_route_planner_provider_usage",
            "total_llm_route_planner_provider_input_tokens",
            "total_llm_route_planner_provider_output_tokens",
            "total_llm_route_planner_provider_cache_creation_input_tokens",
            "total_llm_route_planner_provider_cache_read_input_tokens",
            "total_llm_route_planner_provider_total_tokens",
            "n_rows_with_quality_controls",
            "n_quality_control_fields",
            "quality_control_fields",
            "quality_control_resource_contract_ids",
            "quality_control_response_validation_signals",
            "quality_control_stop_conditions",
            "all_ok",
        ],
        "properties": {
            "requested": {"type": "boolean"},
            "manifest_path": {"type": "string"},
            "n_evaluation_rows": nonnegative_integer,
            "n_evaluation_row_schema_valid": nonnegative_integer,
            "n_evaluation_row_schema_invalid": nonnegative_integer,
            "n_matched_ground_truth": nonnegative_integer,
            "n_missing_ground_truth": nonnegative_integer,
            "n_alignment_contract_ok": nonnegative_integer,
            "n_feedback_loop_ready": nonnegative_integer,
            "n_unaligned_primitives": nonnegative_integer,
            "n_minimal_delta_route_options": nonnegative_integer,
            "mean_minimal_delta_selected_route_cost": {"type": "number"},
            "n_kernel_verified_ground_truth": nonnegative_integer,
            "n_kernel_verification_witnesses": nonnegative_integer,
            "n_kernel_verified_ground_truth_with_witnesses": nonnegative_integer,
            "mean_alignment_coverage": {"type": "number"},
            "n_rows_with_llm_route_planner_residual_goal_contexts": (
                nonnegative_integer
            ),
            "n_llm_route_planner_residual_goal_contexts": nonnegative_integer,
            "n_llm_route_planner_residual_goal_context_source_refs": (
                nonnegative_integer
            ),
            "n_llm_route_planner_residual_goal_context_provenance_values": (
                nonnegative_integer
            ),
            "n_llm_route_planner_residual_goals_with_context": (
                nonnegative_integer
            ),
            "n_llm_route_planner_residual_goals_without_context": (
                nonnegative_integer
            ),
            "n_rows_with_llm_route_planner_route_option_selection_brief": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selection_candidate_options": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selection_candidate_primitives": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selection_candidates_with_residual_goals": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selection_candidate_residual_goals": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selection_lower_bound_residual_goals": (
                nonnegative_integer
            ),
            "n_rows_with_llm_route_planner_route_option_selected_route_option": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selected_matches_lower_bound": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selected_mismatches_lower_bound": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selected_matches_minimal_delta": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_option_selected_mismatches_minimal_delta": (
                nonnegative_integer
            ),
            "n_realization_missing_selected_formal_primitives": nonnegative_integer,
            "n_realization_missing_delta_alignment_primitives": nonnegative_integer,
            "n_rows_with_incomplete_cost_hint_baseline_coverage": nonnegative_integer,
            "n_realization_cost_hint_baseline_primitives": nonnegative_integer,
            "n_realization_omitted_cost_hint_primitives": nonnegative_integer,
            "realization_missing_selected_formal_primitives": string_array,
            "realization_missing_delta_alignment_primitives": string_array,
            "realization_cost_hint_baseline_primitives": string_array,
            "realization_omitted_cost_hint_primitives": string_array,
            "n_rows_with_llm_route_planner_route_adoption_status": nonnegative_integer,
            "n_rows_ready_for_route_adoption": nonnegative_integer,
            "n_rows_pending_refinement_before_route_adoption": nonnegative_integer,
            "n_rows_awaiting_llm_route_planner_response": nonnegative_integer,
            "n_rows_rejected_llm_route_plan": nonnegative_integer,
            "n_llm_route_adoption_blockers": nonnegative_integer,
            "n_llm_route_adoption_pending_quality_control_blockers": (
                nonnegative_integer
            ),
            "n_llm_route_adoption_pending_source_grounding_blockers": (
                nonnegative_integer
            ),
            "n_llm_route_adoption_pending_formal_attempt_queue_blockers": (
                nonnegative_integer
            ),
            "n_rows_with_llm_route_planner_route_adoption_preconditions": (
                nonnegative_integer
            ),
            "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_adoption_precondition_known_blockers": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_adoption_precondition_required_response_fields": (
                nonnegative_integer
            ),
            "n_llm_route_planner_route_adoption_precondition_target_primitives": (
                nonnegative_integer
            ),
            "llm_route_planner_route_adoption_precondition_known_blockers": (
                route_adoption_blocker_array
            ),
            "llm_route_planner_route_adoption_precondition_required_response_fields": (
                string_array
            ),
            "llm_route_planner_route_adoption_precondition_target_primitives": (
                string_array
            ),
            "llm_route_adoption_blockers": route_adoption_blocker_array,
            "llm_route_adoption_blocker_counts": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "llm_route_adoption_status_counts": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "evaluation_by_llm_route_adoption_blocker": {
                "type": "object",
                "additionalProperties": {"type": "object"},
            },
            "llm_route_planner_provider_usage_summary": {
                "type": "object",
                "additionalProperties": True,
            },
            "n_rows_with_llm_route_planner_provider_usage": nonnegative_integer,
            "total_llm_route_planner_provider_input_tokens": nonnegative_integer,
            "total_llm_route_planner_provider_output_tokens": nonnegative_integer,
            "total_llm_route_planner_provider_cache_creation_input_tokens": (
                nonnegative_integer
            ),
            "total_llm_route_planner_provider_cache_read_input_tokens": (
                nonnegative_integer
            ),
            "total_llm_route_planner_provider_total_tokens": nonnegative_integer,
            "n_rows_with_quality_controls": nonnegative_integer,
            "n_quality_control_fields": nonnegative_integer,
            "quality_control_fields": string_array,
            "quality_control_resource_contract_ids": string_array,
            "quality_control_response_validation_signals": string_array,
            "quality_control_stop_conditions": string_array,
            "all_ok": {"type": "boolean"},
        },
    }
    llm_route_planner_summary_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "requested",
            "provider_execution_mode",
            "invoke_provider",
            "response_json_supplied",
            "static_response_json_supplied",
            "generator_backend_supplied",
            "live_provider_backend_requested",
            "static_generator_backend_requested",
            "provider_generation_requested",
            "n_request_packets",
            "n_target_theorem_context_packets",
            "n_requests_with_context_packet_inventory",
            "n_request_context_inventory_total_rows",
            "n_rows_with_context_packet_inventory",
            "n_requests_with_available_source_snippets",
            "n_request_available_source_snippets",
            "n_requests_with_target_intake_rows",
            "n_request_target_intake_rows",
            "n_requests_with_current_goal_plan_rows",
            "n_request_current_goal_plan_rows",
            "n_requests_with_route_adoption_preconditions",
            "n_request_route_adoption_precondition_known_blockers",
            "n_request_route_adoption_precondition_required_response_fields",
            "n_request_route_adoption_precondition_target_primitives",
            "n_requests_with_quality_control_obligation_inventory",
            "n_requests_with_pending_quality_control_obligation_inventory",
            "n_request_quality_control_obligation_fields",
            "n_request_quality_control_obligation_values",
            "n_request_pending_quality_control_fields",
            "n_request_pending_quality_control_values",
            "n_request_discharged_quality_control_fields",
            "n_request_discharged_quality_control_values",
            "n_requests_with_source_grounding_rows",
            "n_request_source_grounding_rows",
            "n_requests_with_source_grounding_obligation_inventory",
            "n_requests_with_pending_source_grounding_obligation_inventory",
            "n_request_source_grounding_unresolved_rows",
            "n_request_residual_source_grounding_unresolved_rows",
            "n_request_residual_goals",
            "n_requests_with_residual_goal_contexts",
            "n_request_residual_goal_contexts",
            "n_request_context_residual_goal_contexts",
            "n_request_inventory_residual_goal_contexts",
            "n_requests_with_resource_feedback_readiness_summary",
            "n_request_resource_feedback_readiness_rows",
            "n_request_resource_feedback_reuse_ready_rows",
            "n_requests_with_formal_source_retrieval_summary",
            "n_request_formal_source_retrieval_metadata_rows",
            "n_request_formal_source_semantic_rerank_rows",
            "n_requests_with_formal_attempt_feedback_summary",
            "n_request_formal_attempt_feedback_contexts",
            "n_request_formal_attempt_feedback_residual_goals",
            "n_request_formal_attempt_feedback_failed_statuses",
            "n_feedback_loop_summary_prior_llm_route_planner_hook_traces",
            "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces",
            "n_feedback_loop_summary_interactive_resource_requests",
            "n_feedback_loop_summary_interactive_resource_request_dispatch_summaries",
            "n_feedback_loop_summary_interactive_resource_request_execution_commands",
            "n_requests_with_component_resource_registry_context",
            "n_component_resource_registry_resources_in_prompt",
            "n_component_resource_registry_contracts_in_prompt",
            "n_requests_with_source_theorem_semantic_primitive_bridge_context",
            "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt",
            "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt",
            "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context",
            "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt",
            "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt",
            "n_requests_with_source_theorem_formal_environment_bridge_context",
            "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt",
            "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt",
            "n_requests_with_exact_source_theorem_proof_body_executor_context",
            "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt",
            "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt",
            "n_requests_with_agentic_proof_execution_materializer_rows",
            "n_request_agentic_proof_execution_materializer_rows",
            "n_requests_with_agentic_proof_execution_artifact_verifier_rows",
            "n_request_agentic_proof_execution_artifact_verifier_rows",
            "n_requests_with_agentic_proof_source_theorem_promotion_rows",
            "n_request_agentic_proof_source_theorem_promotion_rows",
            "n_requests_with_proof_execution_feedback_summary",
            "n_request_proof_execution_feedback_rows",
            "n_request_proof_execution_unsupported_target_prover_rows",
            "n_requests_with_patch_rerun_residual_obligation_summary",
            "n_request_patch_rerun_residual_obligation_rows",
            "n_request_patch_rerun_residual_obligation_source_discovery_needed",
            "n_requests_with_patch_rerun_residual_followup_queue_summary",
            "n_request_patch_rerun_residual_followup_queue_rows",
            "n_request_patch_rerun_residual_followup_queue_ready",
            "n_request_patch_rerun_residual_followup_queue_source_discovery",
            "n_requests_with_agentic_proof_strategy_plan_summary",
            "n_request_agentic_proof_strategy_plan_rows",
            "n_request_agentic_proof_strategy_plan_ready",
            "n_request_agentic_proof_strategy_plan_source_discovery_cache_items",
            "n_rows",
            "n_response_present",
            "n_response_contract_ok",
            "prompt_token_budget_summary",
            "n_prompt_token_budget_rows",
            "max_estimated_prompt_input_tokens",
            "prompt_token_budget_preflight_errors",
            "n_prompt_token_budget_preflight_blocked",
            "estimated_prompt_input_tokens",
            "estimated_prompt_max_output_tokens",
            "estimated_prompt_total_token_budget",
            "provider_usage_summary",
            "n_rows_with_provider_usage",
            "total_provider_input_tokens",
            "total_provider_output_tokens",
            "total_provider_cache_creation_input_tokens",
            "total_provider_cache_read_input_tokens",
            "total_provider_total_tokens",
            "n_generated_responses_model_tier_escalated",
            "n_generated_responses_haiku_to_sonnet_escalated",
            "n_repair_attempt_ledger_model_tier_escalations",
            "n_model_tier_decision_ledger_rows",
            "n_model_tier_decision_ledger_rows_with_escalation",
            "n_model_tier_decision_ledger_provider_failure_rows",
            "n_rows_with_model_tier_escalation",
            "n_requests_with_model_tier_decision_evidence",
            "n_request_target_prover_families",
            "by_request_target_prover_family",
            "n_request_model_tier_haiku",
            "n_request_model_tier_sonnet",
            "n_request_model_tier_opus",
            "by_request_model_tier",
            "n_request_model_tier_decision_auto_haiku_bounded",
            "n_request_model_tier_decision_auto_sonnet_triggered",
            "n_request_model_tier_decision_operator_override",
            "n_request_model_tier_decision_sonnet_triggers",
            "n_request_model_tier_decision_route_planning_evidence_gaps",
            "n_request_model_tier_decision_route_planning_evidence_gap_sonnet_triggers",
            "n_request_model_tier_decision_resource_feedback_readiness_rows",
            "n_request_model_tier_decision_resource_feedback_reuse_ready_rows",
            "n_request_model_tier_decision_resource_feedback_sonnet_triggers",
            "n_request_model_tier_decision_formal_attempt_feedback_contexts",
            "n_request_model_tier_decision_formal_attempt_feedback_residual_goals",
            "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses",
            "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers",
            "n_request_model_tier_decision_evidence_invalid",
            "by_request_model_tier_decision_basis",
            "n_requests_with_library_alignment_summary",
            "n_request_library_alignment_primitives",
            "n_request_library_alignment_reuse_ready_primitives",
            "n_request_library_alignment_wrapper_primitives",
            "n_request_library_alignment_bridge_primitives",
            "n_request_library_alignment_source_port_primitives",
            "n_request_library_alignment_new_definition_primitives",
            "n_request_library_alignment_new_theory_primitives",
            "n_request_library_alignment_unknown_primitives",
            "n_request_library_alignment_bridge_or_harder_primitives",
            "n_request_library_alignment_target_compatible_reuse_declarations",
            "n_request_library_alignment_route_options",
            "n_request_library_alignment_route_option_primitives",
            "n_request_library_alignment_route_option_bridge_or_harder_primitives",
            "n_request_library_alignment_route_option_target_compatible_reuse_declarations",
            "total_request_library_alignment_route_option_minimum_base_cost",
            "by_request_library_alignment_delta_class",
            "by_request_library_alignment_minimum_coverage_bucket",
            "n_requests_with_route_option_selection_brief",
            "n_request_route_option_selection_candidate_options",
            "n_request_route_option_selection_candidate_primitives",
            "n_request_route_option_selection_candidates_with_residual_goals",
            "n_request_route_option_selection_candidate_residual_goals",
            "n_request_route_option_selection_lower_bound_options",
            "n_request_route_option_selection_lower_bound_residual_goals",
            "n_informal_knowledge_dag_nodes",
            "n_formal_realization_dag_nodes",
            "legacy_response_field_aliases",
            "n_lean_realization_dag_nodes",
            "n_route_alignment_edges",
            "n_search_requests",
            "n_planner_next_actions",
            "n_rows_with_planner_next_actions",
            "n_rows_with_residual_goal_contexts",
            "n_row_residual_goal_contexts",
            "n_uncertainty_flags",
            "n_residual_interpretations",
            "n_source_snippets",
            "n_rows_with_source_snippets",
            "n_formal_attempt_queue_items",
            "n_rows_with_formal_attempt_queue",
            "n_delta_action_witness_required_primitives",
            "n_delta_action_witness_missing_primitives",
            "n_rows_with_delta_action_witness_obligations",
            "n_rows_with_complete_delta_action_witness",
            "n_rows_with_route_adoption_preconditions",
            "n_row_route_adoption_precondition_known_blockers",
            "n_row_route_adoption_precondition_target_primitives",
            "n_accepted_route_plans",
            "n_accepted_with_formal_attempt_queue",
            "n_route_adoption_ready",
            "n_route_adoption_pending_refinement",
            "n_route_adoption_awaiting_llm_response",
            "n_route_adoption_rejected",
            "n_route_adoption_pending_formal_gap_boundary_blockers",
            "n_route_adoption_pending_formal_attempt_queue_blockers",
            "n_route_adoption_blockers",
            "route_adoption_blockers",
            "route_adoption_blocker_counts",
            "by_route_adoption_status",
            "by_route_adoption_blocker",
            "standalone_replay_gate",
            "standalone_replay_gate_ok",
            "n_standalone_replay_route_candidates",
            "n_standalone_replay_adoptable_route_candidates",
            "n_standalone_replay_blocked_route_candidates",
            "standalone_replay_gate_blockers",
            "n_row_schema_valid",
            "n_row_schema_invalid",
            "all_ok",
        ],
        "properties": {
            "requested": {"type": "boolean"},
            "manifest_path": {"type": "string"},
            "jsonl_path": {"type": "string"},
            "provider_execution_mode": {
                "type": "string",
                "enum": ["", *PROVIDER_EXECUTION_MODES],
            },
            "invoke_provider": {"type": "boolean"},
            "response_json_supplied": {"type": "boolean"},
            "static_response_json_supplied": {"type": "boolean"},
            "generator_backend_supplied": {"type": "boolean"},
            "live_provider_backend_requested": {"type": "boolean"},
            "static_generator_backend_requested": {"type": "boolean"},
            "provider_generation_requested": {"type": "boolean"},
            "n_request_packets": nonnegative_integer,
            "n_target_theorem_context_packets": nonnegative_integer,
            "n_requests_with_context_packet_inventory": nonnegative_integer,
            "n_request_context_inventory_total_rows": nonnegative_integer,
            "n_rows_with_context_packet_inventory": nonnegative_integer,
            "n_requests_with_available_source_snippets": nonnegative_integer,
            "n_request_available_source_snippets": nonnegative_integer,
            "n_requests_with_target_intake_rows": nonnegative_integer,
            "n_request_target_intake_rows": nonnegative_integer,
            "n_requests_with_current_goal_plan_rows": nonnegative_integer,
            "n_request_current_goal_plan_rows": nonnegative_integer,
            "n_requests_with_route_adoption_preconditions": nonnegative_integer,
            "n_request_route_adoption_precondition_known_blockers": (
                nonnegative_integer
            ),
            "n_request_route_adoption_precondition_required_response_fields": (
                nonnegative_integer
            ),
            "n_request_route_adoption_precondition_target_primitives": (
                nonnegative_integer
            ),
            "n_requests_with_quality_control_obligation_inventory": (
                nonnegative_integer
            ),
            "n_requests_with_pending_quality_control_obligation_inventory": (
                nonnegative_integer
            ),
            "n_request_quality_control_obligation_fields": nonnegative_integer,
            "n_request_quality_control_obligation_values": nonnegative_integer,
            "n_request_pending_quality_control_fields": nonnegative_integer,
            "n_request_pending_quality_control_values": nonnegative_integer,
            "n_request_discharged_quality_control_fields": nonnegative_integer,
            "n_request_discharged_quality_control_values": nonnegative_integer,
            "n_requests_with_source_grounding_rows": nonnegative_integer,
            "n_request_source_grounding_rows": nonnegative_integer,
            "n_requests_with_source_grounding_obligation_inventory": (
                nonnegative_integer
            ),
            "n_requests_with_pending_source_grounding_obligation_inventory": (
                nonnegative_integer
            ),
            "n_request_source_grounding_unresolved_rows": nonnegative_integer,
            "n_request_residual_source_grounding_unresolved_rows": (
                nonnegative_integer
            ),
            "n_request_residual_goals": nonnegative_integer,
            "n_requests_with_residual_goal_contexts": nonnegative_integer,
            "n_request_residual_goal_contexts": nonnegative_integer,
            "n_request_context_residual_goal_contexts": nonnegative_integer,
            "n_request_inventory_residual_goal_contexts": nonnegative_integer,
            "n_requests_with_resource_feedback_readiness_summary": (
                nonnegative_integer
            ),
            "n_request_resource_feedback_readiness_rows": nonnegative_integer,
            "n_request_resource_feedback_reuse_ready_rows": nonnegative_integer,
            "n_requests_with_formal_source_retrieval_summary": (
                nonnegative_integer
            ),
            "n_request_formal_source_retrieval_metadata_rows": nonnegative_integer,
            "n_request_formal_source_semantic_rerank_rows": nonnegative_integer,
            "n_requests_with_formal_attempt_feedback_summary": nonnegative_integer,
            "n_request_formal_attempt_feedback_contexts": nonnegative_integer,
            "n_request_formal_attempt_feedback_residual_goals": nonnegative_integer,
            "n_request_formal_attempt_feedback_failed_statuses": nonnegative_integer,
            "n_feedback_loop_summary_prior_llm_route_planner_hook_traces": (
                nonnegative_integer
            ),
            "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces": (
                nonnegative_integer
            ),
            "n_feedback_loop_summary_interactive_resource_requests": (
                nonnegative_integer
            ),
            "n_feedback_loop_summary_interactive_resource_request_dispatch_summaries": (
                nonnegative_integer
            ),
            "n_feedback_loop_summary_interactive_resource_request_execution_commands": (
                nonnegative_integer
            ),
            "n_requests_with_component_resource_registry_context": (
                nonnegative_integer
            ),
            "n_component_resource_registry_resources_in_prompt": (
                nonnegative_integer
            ),
            "n_component_resource_registry_contracts_in_prompt": (
                nonnegative_integer
            ),
            "n_requests_with_source_theorem_semantic_primitive_bridge_context": (
                nonnegative_integer
            ),
            "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt": (
                nonnegative_integer
            ),
            "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt": (
                nonnegative_integer
            ),
            "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context": (
                nonnegative_integer
            ),
            "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt": (
                nonnegative_integer
            ),
            "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt": (
                nonnegative_integer
            ),
            "n_requests_with_source_theorem_formal_environment_bridge_context": (
                nonnegative_integer
            ),
            "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt": (
                nonnegative_integer
            ),
            "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt": (
                nonnegative_integer
            ),
            "n_requests_with_exact_source_theorem_proof_body_executor_context": (
                nonnegative_integer
            ),
            "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt": (
                nonnegative_integer
            ),
            "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt": (
                nonnegative_integer
            ),
            "n_requests_with_source_theorem_semantic_primitive_rows": (
                nonnegative_integer
            ),
            "n_request_source_theorem_semantic_primitive_rows": (
                nonnegative_integer
            ),
            "n_requests_with_proof_body_semantic_primitive_work_order_rows": (
                nonnegative_integer
            ),
            "n_request_proof_body_semantic_primitive_work_order_rows": (
                nonnegative_integer
            ),
            "n_requests_with_source_theorem_formal_environment_rows": (
                nonnegative_integer
            ),
            "n_request_source_theorem_formal_environment_rows": (
                nonnegative_integer
            ),
            "n_requests_with_source_theorem_proof_body_execution_result_rows": (
                nonnegative_integer
            ),
            "n_request_source_theorem_proof_body_execution_result_rows": (
                nonnegative_integer
            ),
            "n_requests_with_agentic_proof_execution_materializer_rows": (
                nonnegative_integer
            ),
            "n_request_agentic_proof_execution_materializer_rows": (
                nonnegative_integer
            ),
            "n_requests_with_agentic_proof_execution_artifact_verifier_rows": (
                nonnegative_integer
            ),
            "n_request_agentic_proof_execution_artifact_verifier_rows": (
                nonnegative_integer
            ),
            "n_requests_with_agentic_proof_source_theorem_promotion_rows": (
                nonnegative_integer
            ),
            "n_request_agentic_proof_source_theorem_promotion_rows": (
                nonnegative_integer
            ),
            "n_requests_with_proof_execution_feedback_summary": (
                nonnegative_integer
            ),
            "n_request_proof_execution_feedback_rows": nonnegative_integer,
            "n_request_proof_execution_unsupported_target_prover_rows": (
                nonnegative_integer
            ),
            "n_requests_with_patch_rerun_residual_obligation_summary": (
                nonnegative_integer
            ),
            "n_request_patch_rerun_residual_obligation_rows": nonnegative_integer,
            "n_request_patch_rerun_residual_obligation_source_discovery_needed": (
                nonnegative_integer
            ),
            "n_requests_with_patch_rerun_residual_followup_queue_summary": (
                nonnegative_integer
            ),
            "n_request_patch_rerun_residual_followup_queue_rows": (
                nonnegative_integer
            ),
            "n_request_patch_rerun_residual_followup_queue_ready": (
                nonnegative_integer
            ),
            "n_request_patch_rerun_residual_followup_queue_source_discovery": (
                nonnegative_integer
            ),
            "n_requests_with_agentic_proof_strategy_plan_summary": (
                nonnegative_integer
            ),
            "n_request_agentic_proof_strategy_plan_rows": nonnegative_integer,
            "n_request_agentic_proof_strategy_plan_ready": nonnegative_integer,
            "n_request_agentic_proof_strategy_plan_source_discovery_cache_items": (
                nonnegative_integer
            ),
            "n_rows": nonnegative_integer,
            "n_response_present": nonnegative_integer,
            "n_response_contract_ok": nonnegative_integer,
            "n_provider_failures": nonnegative_integer,
            "prompt_token_budget_summary": {"type": "object"},
            "n_prompt_token_budget_rows": nonnegative_integer,
            "max_estimated_prompt_input_tokens": nonnegative_integer,
            "prompt_token_budget_preflight_errors": object_array,
            "n_prompt_token_budget_preflight_blocked": nonnegative_integer,
            "estimated_prompt_input_tokens": nonnegative_integer,
            "estimated_prompt_max_output_tokens": nonnegative_integer,
            "estimated_prompt_total_token_budget": nonnegative_integer,
            "provider_usage_summary": {"type": "object"},
            "n_rows_with_provider_usage": nonnegative_integer,
            "total_provider_input_tokens": nonnegative_integer,
            "total_provider_output_tokens": nonnegative_integer,
            "total_provider_cache_creation_input_tokens": nonnegative_integer,
            "total_provider_cache_read_input_tokens": nonnegative_integer,
            "total_provider_total_tokens": nonnegative_integer,
            "n_generated_responses_model_tier_escalated": nonnegative_integer,
            "n_generated_responses_haiku_to_sonnet_escalated": (
                nonnegative_integer
            ),
            "n_repair_attempt_ledger_model_tier_escalations": (
                nonnegative_integer
            ),
            "n_model_tier_decision_ledger_rows": nonnegative_integer,
            "n_model_tier_decision_ledger_rows_with_escalation": (
                nonnegative_integer
            ),
            "n_model_tier_decision_ledger_provider_failure_rows": (
                nonnegative_integer
            ),
            "n_rows_with_model_tier_escalation": nonnegative_integer,
            "n_requests_with_model_tier_decision_evidence": nonnegative_integer,
            "n_request_target_prover_families": nonnegative_integer,
            "by_request_target_prover_family": {"type": "object"},
            "n_request_model_tier_haiku": nonnegative_integer,
            "n_request_model_tier_sonnet": nonnegative_integer,
            "n_request_model_tier_opus": nonnegative_integer,
            "by_request_model_tier": {"type": "object"},
            "n_request_model_tier_decision_auto_haiku_bounded": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_auto_sonnet_triggered": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_operator_override": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_sonnet_triggers": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_route_planning_evidence_gaps": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_route_planning_evidence_gap_sonnet_triggers": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_resource_feedback_readiness_rows": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_resource_feedback_reuse_ready_rows": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_resource_feedback_sonnet_triggers": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_formal_attempt_feedback_contexts": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_formal_attempt_feedback_residual_goals": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers": (
                nonnegative_integer
            ),
            "n_request_model_tier_decision_evidence_invalid": (
                nonnegative_integer
            ),
            "by_request_model_tier_decision_basis": {"type": "object"},
            "n_requests_with_library_alignment_summary": nonnegative_integer,
            "n_request_library_alignment_primitives": nonnegative_integer,
            "n_request_library_alignment_reuse_ready_primitives": nonnegative_integer,
            "n_request_library_alignment_wrapper_primitives": nonnegative_integer,
            "n_request_library_alignment_bridge_primitives": nonnegative_integer,
            "n_request_library_alignment_source_port_primitives": nonnegative_integer,
            "n_request_library_alignment_new_definition_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_new_theory_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_unknown_primitives": nonnegative_integer,
            "n_request_library_alignment_bridge_or_harder_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_target_compatible_reuse_declarations": (
                nonnegative_integer
            ),
            "n_request_library_alignment_route_options": nonnegative_integer,
            "n_request_library_alignment_route_option_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_route_option_bridge_or_harder_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_route_option_target_compatible_reuse_declarations": (
                nonnegative_integer
            ),
            "total_request_library_alignment_route_option_minimum_base_cost": {
                "type": "number",
                "minimum": 0,
            },
            "by_request_library_alignment_delta_class": {"type": "object"},
            "by_request_library_alignment_minimum_coverage_bucket": {
                "type": "object"
            },
            "n_requests_with_route_option_selection_brief": nonnegative_integer,
            "n_request_route_option_selection_candidate_options": (
                nonnegative_integer
            ),
            "n_request_route_option_selection_candidate_primitives": (
                nonnegative_integer
            ),
            "n_request_route_option_selection_candidates_with_residual_goals": (
                nonnegative_integer
            ),
            "n_request_route_option_selection_candidate_residual_goals": (
                nonnegative_integer
            ),
            "n_request_route_option_selection_lower_bound_options": (
                nonnegative_integer
            ),
            "n_request_route_option_selection_lower_bound_residual_goals": (
                nonnegative_integer
            ),
            "n_informal_knowledge_dag_nodes": nonnegative_integer,
            "n_formal_realization_dag_nodes": nonnegative_integer,
            "legacy_response_field_aliases": {"type": "object"},
            "n_lean_realization_dag_nodes": nonnegative_integer,
            "n_route_alignment_edges": nonnegative_integer,
            "n_search_requests": nonnegative_integer,
            "n_planner_next_actions": nonnegative_integer,
            "n_rows_with_planner_next_actions": nonnegative_integer,
            "n_rows_with_residual_goal_contexts": nonnegative_integer,
            "n_row_residual_goal_contexts": nonnegative_integer,
            "n_uncertainty_flags": nonnegative_integer,
            "n_residual_interpretations": nonnegative_integer,
            "n_source_snippets": nonnegative_integer,
            "n_rows_with_source_snippets": nonnegative_integer,
            "n_formal_attempt_queue_items": nonnegative_integer,
            "n_rows_with_formal_attempt_queue": nonnegative_integer,
            "n_delta_action_witness_required_primitives": nonnegative_integer,
            "n_delta_action_witness_missing_primitives": nonnegative_integer,
            "n_rows_with_delta_action_witness_obligations": nonnegative_integer,
            "n_rows_with_complete_delta_action_witness": nonnegative_integer,
            "n_rows_with_route_adoption_preconditions": nonnegative_integer,
            "n_row_route_adoption_precondition_known_blockers": (
                nonnegative_integer
            ),
            "n_row_route_adoption_precondition_target_primitives": (
                nonnegative_integer
            ),
            "n_accepted_route_plans": nonnegative_integer,
            "n_accepted_with_formal_attempt_queue": nonnegative_integer,
            "n_route_adoption_ready": nonnegative_integer,
            "n_route_adoption_pending_refinement": nonnegative_integer,
            "n_route_adoption_awaiting_llm_response": nonnegative_integer,
            "n_route_adoption_rejected": nonnegative_integer,
            "n_route_adoption_pending_formal_gap_boundary_blockers": (
                nonnegative_integer
            ),
            "n_route_adoption_pending_formal_attempt_queue_blockers": (
                nonnegative_integer
            ),
            "n_route_adoption_blockers": nonnegative_integer,
            "route_adoption_blockers": route_adoption_blocker_array,
            "route_adoption_blocker_counts": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "by_route_adoption_status": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "by_route_adoption_blocker": {
                "type": "object",
                "additionalProperties": {"type": "object"},
            },
            "standalone_replay_gate": {"type": "object"},
            "standalone_replay_gate_ok": {"type": "boolean"},
            "n_standalone_replay_route_candidates": nonnegative_integer,
            "n_standalone_replay_adoptable_route_candidates": nonnegative_integer,
            "n_standalone_replay_blocked_route_candidates": nonnegative_integer,
            "standalone_replay_gate_blockers": string_array,
            "n_row_schema_valid": nonnegative_integer,
            "n_row_schema_invalid": nonnegative_integer,
            "all_ok": {"type": "boolean"},
        },
    }
    response_payload_validation_summary_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "requested",
            "n_payloads",
            "n_valid_payloads",
            "n_invalid_payloads",
            "n_request_context_packets",
            "n_request_contexts_with_context_packet_inventory",
            "n_request_context_inventory_total_rows",
            "n_request_bound_payloads",
            "n_request_bound_payloads_with_route_adoption_status",
            "n_request_bound_payloads_route_adoption_ready",
            "n_request_bound_payloads_route_adoption_pending_refinement",
            "n_request_bound_payloads_route_adoption_rejected",
            "n_request_bound_payloads_adoptable_for_standalone_replay",
            "by_request_bound_payload_route_adoption_status",
            "request_bound_payload_route_adoption_blocker_counts",
            "n_request_bound_payloads_with_context_packet_inventory",
            "n_request_bound_payload_context_inventory_total_rows",
            "n_request_bound_payloads_with_route_adoption_preconditions",
            "n_request_bound_payloads_with_blocking_route_adoption_preconditions",
            "n_request_bound_payload_route_adoption_precondition_known_blockers",
            "n_request_bound_payload_route_adoption_precondition_required_response_fields",
            "n_request_bound_payload_route_adoption_precondition_target_primitives",
            "n_request_bound_payloads_with_agentic_proof_strategy_plan",
            "n_request_bound_payload_agentic_proof_strategy_plan_rows",
            "n_request_bound_payload_agentic_proof_strategy_plan_ready",
            "n_payloads_with_formal_attempt_queue",
            "n_payload_formal_attempt_queue_items",
            "n_payloads_with_formal_attempt_queue_errors",
            "n_formal_attempt_queue_errors",
            "n_payloads_with_agentic_proof_strategy_plan_obligation_errors",
            "n_agentic_proof_strategy_plan_obligation_errors",
            "n_payloads_with_declared_target_prover_family",
            "n_request_bound_payloads_with_target_prover_family_mismatch",
            "by_payload_target_prover_family",
            "by_request_context_target_prover_family",
            "n_schema_errors",
            "n_request_context_errors",
            "all_ok",
        ],
        "properties": {
            "requested": {"type": "boolean"},
            "manifest_path": {"type": "string"},
            "jsonl_path": {"type": "string"},
            "n_payloads": nonnegative_integer,
            "n_valid_payloads": nonnegative_integer,
            "n_invalid_payloads": nonnegative_integer,
            "n_request_context_packets": nonnegative_integer,
            "n_request_contexts_with_context_packet_inventory": nonnegative_integer,
            "n_request_context_inventory_total_rows": nonnegative_integer,
            "n_request_bound_payloads": nonnegative_integer,
            "n_request_bound_payloads_with_route_adoption_status": (
                nonnegative_integer
            ),
            "n_request_bound_payloads_route_adoption_ready": nonnegative_integer,
            "n_request_bound_payloads_route_adoption_pending_refinement": (
                nonnegative_integer
            ),
            "n_request_bound_payloads_route_adoption_rejected": nonnegative_integer,
            "n_request_bound_payloads_adoptable_for_standalone_replay": (
                nonnegative_integer
            ),
            "by_request_bound_payload_route_adoption_status": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "request_bound_payload_route_adoption_blocker_counts": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "n_request_bound_payloads_with_context_packet_inventory": (
                nonnegative_integer
            ),
            "n_request_bound_payload_context_inventory_total_rows": (
                nonnegative_integer
            ),
            "n_request_bound_payloads_with_route_adoption_preconditions": (
                nonnegative_integer
            ),
            "n_request_bound_payloads_with_blocking_route_adoption_preconditions": (
                nonnegative_integer
            ),
            "n_request_bound_payload_route_adoption_precondition_known_blockers": (
                nonnegative_integer
            ),
            "n_request_bound_payload_route_adoption_precondition_required_response_fields": (
                nonnegative_integer
            ),
            "n_request_bound_payload_route_adoption_precondition_target_primitives": (
                nonnegative_integer
            ),
            "n_request_bound_payloads_with_agentic_proof_strategy_plan": (
                nonnegative_integer
            ),
            "n_request_bound_payload_agentic_proof_strategy_plan_rows": (
                nonnegative_integer
            ),
            "n_request_bound_payload_agentic_proof_strategy_plan_ready": (
                nonnegative_integer
            ),
            "n_payloads_with_formal_attempt_queue": nonnegative_integer,
            "n_payload_formal_attempt_queue_items": nonnegative_integer,
            "n_payloads_with_formal_attempt_queue_errors": nonnegative_integer,
            "n_formal_attempt_queue_errors": nonnegative_integer,
            "n_payloads_with_agentic_proof_strategy_plan_obligation_errors": (
                nonnegative_integer
            ),
            "n_agentic_proof_strategy_plan_obligation_errors": nonnegative_integer,
            "n_payloads_with_declared_target_prover_family": nonnegative_integer,
            "n_request_bound_payloads_with_target_prover_family_mismatch": (
                nonnegative_integer
            ),
            "by_payload_target_prover_family": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "by_request_context_target_prover_family": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "n_schema_errors": nonnegative_integer,
            "n_request_context_errors": nonnegative_integer,
            "all_ok": {"type": "boolean"},
        },
    }
    cross_prover_formal_attempt_dependency_summary_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "requested",
            "manifest_path",
            "target_summary_path",
            "n_total_packets",
            "n_total_packets_with_formal_attempt_dependency",
            "n_total_packets_formal_attempt_initial_ready",
            "n_total_packets_formal_attempt_waiting",
            "n_total_packets_formal_attempt_missing_prerequisites",
            "by_total_packet_formal_attempt_dependency_status",
            "n_total_response_minimal_delta_action_witnesses_required",
            "n_total_response_minimal_delta_action_witnesses_acknowledged",
            "n_total_response_minimal_delta_action_witnesses_unacknowledged",
            "n_total_response_addressed_minimal_delta_action_witnesses",
            "target_summary_consistent",
        ],
        "properties": {
            "requested": {"type": "boolean"},
            "manifest_path": {"type": "string"},
            "target_summary_path": {"type": "string"},
            "n_total_packets": nonnegative_integer,
            "n_total_packets_with_formal_attempt_dependency": nonnegative_integer,
            "n_total_packets_formal_attempt_initial_ready": nonnegative_integer,
            "n_total_packets_formal_attempt_waiting": nonnegative_integer,
            "n_total_packets_formal_attempt_missing_prerequisites": (
                nonnegative_integer
            ),
            "by_total_packet_formal_attempt_dependency_status": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "n_total_response_minimal_delta_action_witnesses_required": (
                nonnegative_integer
            ),
            "n_total_response_minimal_delta_action_witnesses_acknowledged": (
                nonnegative_integer
            ),
            "n_total_response_minimal_delta_action_witnesses_unacknowledged": (
                nonnegative_integer
            ),
            "n_total_response_addressed_minimal_delta_action_witnesses": (
                nonnegative_integer
            ),
            "target_summary_consistent": {"type": "boolean"},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID,
        "title": "Formalization Gap Planner Publication Bundle Manifest",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "component_name",
            "packaged_component",
            "portable_schema_id",
            "bundle_id",
            "core_artifacts",
            "optional_artifacts",
            "evaluation_summary",
            "llm_route_planner_summary",
            "feedback_llm_route_planner_summary",
            "llm_route_planner_response_payload_validation_summary",
            "library_coverage_map_summary",
            "cross_prover_formal_attempt_dependency_summary",
            "schema_catalog_summary",
            "all_ok",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_SCHEMA_VERSION,
            },
            "component_name": {"const": PUBLICATION_BUNDLE_COMPONENT_NAME},
            "packaged_component": {
                "const": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME
            },
            "portable_schema_id": {"const": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID},
            "bundle_id": {"type": "string", "minLength": 1},
            "core_artifacts": {"type": "array", "items": core_artifact_schema},
            "optional_artifacts": {
                "type": "array",
                "items": optional_artifact_schema,
            },
            "evaluation_summary": evaluation_summary_schema,
            "llm_route_planner_summary": llm_route_planner_summary_schema,
            "feedback_llm_route_planner_summary": llm_route_planner_summary_schema,
            "llm_route_planner_response_payload_validation_summary": (
                response_payload_validation_summary_schema
            ),
            "library_coverage_map_summary": {"type": "object"},
            "cross_prover_formal_attempt_dependency_summary": (
                cross_prover_formal_attempt_dependency_summary_schema
            ),
            "schema_catalog_summary": {"type": "object"},
            "portable_reuse_targets": string_array,
            "all_ok": {"type": "boolean"},
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {"type": "string", "minLength": 1},
        },
    }


def validate_schema_catalog_payload(
    payload: dict[str, Any],
    schema: dict[str, object] | None = None,
    *,
    bundle_dir: Path | None = None,
) -> tuple[str, ...]:
    """Validate a publication-bundle schema catalog.

    When ``bundle_dir`` is supplied, relative paths are also checked to ensure
    they resolve inside the bundle and point at existing files.
    """

    catalog_schema = schema or schema_catalog_json_schema()
    errors: list[str] = []
    required = catalog_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in payload:
                errors.append(f"{field_name} required")
    properties = catalog_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if (
                isinstance(field_name, str)
                and isinstance(field_schema, dict)
                and field_name in payload
            ):
                errors.extend(
                    _schema_catalog_property_errors(
                        field_name,
                        payload[field_name],
                        field_schema,
                    )
                )
    raw_entries = payload.get("schema_entries", [])
    if not isinstance(raw_entries, list):
        errors.append("schema_entries must be array")
        entries: list[dict[str, Any]] = []
    else:
        entries = [
            entry for entry in raw_entries if isinstance(entry, dict)
        ]
        if len(entries) != len(raw_entries):
            errors.append("schema_entries items must be objects")
    if not entries:
        errors.append("schema_entries must not be empty")

    entry_schema = (
        catalog_schema.get("$defs", {})
        if isinstance(catalog_schema.get("$defs", {}), dict)
        else {}
    ).get("schema_entry", {})
    entry_required = (
        entry_schema.get("required", []) if isinstance(entry_schema, dict) else []
    )
    entry_properties = (
        entry_schema.get("properties", {}) if isinstance(entry_schema, dict) else {}
    )
    for idx, entry in enumerate(entries):
        if isinstance(entry_required, list):
            for field_name in entry_required:
                if isinstance(field_name, str) and field_name not in entry:
                    errors.append(f"schema_entries[{idx}].{field_name} required")
        if isinstance(entry_properties, dict):
            for field_name, field_schema in entry_properties.items():
                if (
                    isinstance(field_name, str)
                    and isinstance(field_schema, dict)
                    and field_name in entry
                ):
                    errors.extend(
                        _schema_catalog_property_errors(
                            f"schema_entries[{idx}].{field_name}",
                            entry[field_name],
                            field_schema,
                        )
                    )
        entry_errors = entry.get("errors", [])
        if entry.get("ok") is True and entry_errors not in ([], (), None):
            errors.append(f"schema_entries[{idx}] ok entries must not carry errors")
        if entry.get("required") is True and entry.get("ok") is not True:
            errors.append(f"schema_entries[{idx}] required entry must be ok")

    if "n_schema_entries" in payload and payload.get("n_schema_entries") != len(entries):
        errors.append(
            "n_schema_entries must equal number of schema_entries object rows"
        )
    computed_missing_schema_ids = sum(
        1 for entry in entries if not str(entry.get("schema_id", "")).strip()
    )
    if (
        "n_missing_schema_ids" in payload
        and payload.get("n_missing_schema_ids") != computed_missing_schema_ids
    ):
        errors.append("n_missing_schema_ids must match schema_entries")
    computed_missing_files = sum(
        1
        for entry in entries
        if "schema file missing"
        in {str(error) for error in entry.get("errors", []) if isinstance(error, str)}
    )
    if (
        "n_missing_schema_files" in payload
        and payload.get("n_missing_schema_files") != computed_missing_files
    ):
        errors.append("n_missing_schema_files must match schema_entries")
    if "not theorem proof evidence" not in str(
        payload.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    if payload.get("all_ok") is True and payload.get("errors") not in ([], (), None):
        errors.append("all_ok catalog payload must not carry errors")
    if bundle_dir is not None:
        errors.extend(_schema_catalog_bundle_path_errors(bundle_dir, entries))
    return tuple(errors)


def _schema_catalog_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
    elif expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
        elif field_schema.get("minLength") and len(value) < int(
            field_schema["minLength"]
        ):
            errors.append(f"{field_name} must be non-empty")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "array":
        if not isinstance(value, list):
            errors.append(f"{field_name} must be array")
        else:
            item_schema = field_schema.get("items", {})
            if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                bad_indexes = [
                    idx for idx, item in enumerate(value) if not isinstance(item, str)
                ]
                if bad_indexes:
                    errors.append(
                        f"{field_name} items must be string at indexes "
                        + ",".join(str(idx) for idx in bad_indexes)
                    )
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    enum_values = field_schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{field_name} must be one of {','.join(map(str, enum_values))}")
    return tuple(errors)


def _schema_catalog_bundle_path_errors(
    bundle_dir: Path,
    entries: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        bundle_root = bundle_dir.resolve()
    except Exception as exc:
        return (f"bundle_dir cannot be resolved: {type(exc).__name__}: {exc}",)
    for idx, entry in enumerate(entries):
        relative_path = str(entry.get("relative_path", ""))
        if not relative_path:
            errors.append(f"schema_entries[{idx}].relative_path must be non-empty")
            continue
        entry_path = Path(relative_path)
        if entry_path.is_absolute():
            errors.append(f"schema_entries[{idx}].relative_path must be relative")
            continue
        candidate = (bundle_dir / entry_path).resolve()
        try:
            candidate.relative_to(bundle_root)
        except ValueError:
            errors.append(f"schema_entries[{idx}].relative_path escapes bundle")
            continue
        if not candidate.exists():
            errors.append(f"schema_entries[{idx}].relative_path file missing")
    return tuple(errors)


def _schema_catalog_target_prover_families(raw_schema: dict[str, object]) -> list[str]:
    values = raw_schema.get("x-target-prover-families", [])
    if not isinstance(values, list):
        return []
    return list(
        dict.fromkeys(
            str(value).strip()
            for value in values
            if str(value).strip()
        )
    )


def _schema_catalog_payload(
    *,
    bundle_id: str,
    bundle_dir: Path,
    library_snapshot_ref: str,
    core_artifacts: tuple[dict[str, object], ...],
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for artifact in core_artifacts:
        artifact_name = str(artifact.get("artifact_name", ""))
        if not _is_schema_catalog_entry(artifact_name):
            continue
        path = Path(str(artifact.get("path", "")))
        entry_errors: list[str] = []
        raw: dict[str, object] = {}
        if not path.exists():
            entry_errors.append("schema file missing")
        elif not path.is_file():
            entry_errors.append("schema path is not a file")
        else:
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                entry_errors.append("schema file is not JSON")
            else:
                if isinstance(loaded, dict):
                    raw = loaded
                else:
                    entry_errors.append("schema file JSON is not an object")
        schema_id = str(raw.get("$id") or raw.get("schema_id") or "")
        if not schema_id:
            entry_errors.append("schema_id missing")
        title = str(raw.get("title") or raw.get("component") or artifact_name)
        target_prover_families = _schema_catalog_target_prover_families(raw)
        entry = {
            "artifact_name": artifact_name,
            "relative_path": _relative_bundle_path(path, bundle_dir),
            "schema_id": schema_id,
            "title": title,
            "artifact_kind": _schema_artifact_kind(path, artifact_name, raw),
            "required": bool(artifact.get("required", False)),
            "ok": bool(artifact.get("ok", False)) and not entry_errors,
            "errors": entry_errors,
        }
        if target_prover_families:
            entry["target_prover_families"] = target_prover_families
        entries.append(entry)
    errors = [
        f"{entry['artifact_name']}: " + "; ".join(str(error) for error in entry["errors"])
        for entry in entries
        if entry.get("errors")
    ]
    return {
        "schema_version": FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_SCHEMA_VERSION,
        "schema_id": FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID,
        "component_name": SCHEMA_CATALOG_COMPONENT_NAME,
        "bundle_id": bundle_id,
        "library_snapshot_ref": library_snapshot_ref,
        "n_schema_entries": len(entries),
        "n_missing_schema_ids": sum(1 for entry in entries if not entry["schema_id"]),
        "n_missing_schema_files": sum(
            1
            for entry in entries
            if "schema file missing" in set(str(error) for error in entry["errors"])
        ),
        "schema_entries": entries,
        "schema_catalog_fingerprint": stable_hash(entries),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "Formalization gap planner schema catalogs index reusable planner "
            "contracts and schemas. They are not theorem proof evidence."
        ),
        "all_ok": bool(entries) and not errors and all(bool(entry["ok"]) for entry in entries),
        "errors": errors,
    }


def _is_schema_catalog_entry(artifact_name: str) -> bool:
    return (
        artifact_name == "portable_contract"
        or artifact_name.endswith("_schema")
        or artifact_name.endswith("_contract")
        or "_schema" in artifact_name
    )


def _relative_bundle_path(path: Path, bundle_dir: Path) -> str:
    try:
        return str(path.relative_to(bundle_dir))
    except ValueError:
        return str(path)


def _schema_artifact_kind(
    path: Path,
    artifact_name: str,
    raw: dict[str, object],
) -> str:
    if path.name.endswith(".schema.json") or "$schema" in raw:
        return "json_schema"
    if artifact_name == "portable_contract":
        return "contract_manifest"
    return "contract_json"


def _llm_model_policy_payload() -> dict[str, object]:
    models_by_tier = dict(
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY.get("models_by_tier", {})
    )
    outside_cost_tier_models = dict(CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS)
    supported_providers = tuple(SUPPORTED_LIVE_GENERATOR_PROVIDERS)
    prohibited_providers = tuple(PROHIBITED_AGENT_GENERATOR_PROVIDERS)
    all_ok = (
        DEFAULT_LIVE_GENERATOR_PROVIDER == "anthropic"
        and models_by_tier
        == {
            "haiku": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            "sonnet": DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL,
            "opus": DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL,
        }
        and outside_cost_tier_models
        and not set(prohibited_providers).intersection(supported_providers)
    )
    return {
        "schema_version": FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_SCHEMA_VERSION,
        "component_name": LLM_MODEL_POLICY_COMPONENT_NAME,
        "policy_kind": "cost_aware_generator_only_llm_policy",
        "source_checked_date": ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
        "source_evidence": ANTHROPIC_MODEL_SOURCE_EVIDENCE,
        "default_live_generator_provider": DEFAULT_LIVE_GENERATOR_PROVIDER,
        "supported_live_generator_providers": supported_providers,
        "prohibited_generator_providers": prohibited_providers,
        "claude_model_selection": ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
        "latest_claude_models_by_tier": models_by_tier,
        "latest_claude_api_aliases_by_tier": dict(
            DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
        ),
        "runtime_model_id_policy": (
            "Runtime calls use latest_claude_models_by_tier API IDs. Claude API "
            "aliases are documented for operator reference only, and Haiku stays "
            "pinned to the dated API ID instead of the shorter alias."
        ),
        "latest_claude_family_models_outside_cost_tiers": outside_cost_tier_models,
        "outside_cost_tier_policy": (
            "Claude family models outside Opus/Sonnet/Haiku are tracked for "
            "operator awareness but are not automatic AI Statistician cost "
            "tiers. Haiku/Sonnet/Opus requests must resolve to their matching "
            "Claude tier families."
        ),
        "request_time_model_resolution_policy": {
            "empty_model_resolution": (
                "LLM worker configs may leave model empty; the concrete provider "
                "model is resolved from provider_name and model_tier when each "
                "request is built, not when modules are imported."
            ),
            "tier_specific_env_overrides": (
                "Tier-specific Claude environment variables override only their "
                "matching Haiku, Sonnet, or Opus tier and must not collapse "
                "cost-aware routing across tiers."
            ),
            "explicit_model_override_policy": (
                "An explicit model remains an explicit operator override; "
                "recognized Anthropic cross-tier model IDs are recorded as "
                "model-tier mismatches by runtime and route-planner audits."
            ),
            "worker_default_tiers": {
                "TheoryIntake": "haiku",
                "SimulationEngineer": "haiku",
                "AlgorithmEngineer": "haiku",
                "CriticEvaluator": "haiku",
                "ArchitectCoordinator": "sonnet",
                "TheoryDeveloper": "sonnet",
                "FormalizerProofEngineer": "sonnet",
                "formalization_gap_planner_route_synthesis": "auto",
            },
        },
        "cost_aware_runtime_tiers": {
            "sonnet": (
                "ArchitectCoordinator",
                "TheoryDeveloper",
                "FormalizerProofEngineer",
                "formalization_gap_planner_route_synthesis",
            ),
            "haiku": (
                "theory_intake",
                "SimulationEngineer",
                "AlgorithmEngineer",
                "CriticEvaluator",
                "bounded_route_triage",
            ),
            "opus": ("operator_explicit_only",),
        },
        "generator_boundary": (
            "Claude/OpenAI/static providers are generator-only backends. "
            "Agent loops, retrieval, tool calls, filesystem writes, tests, "
            "Lean/prover execution, validation, and route repair remain owned "
            "by AI Statistician runtime components."
        ),
        "codex_policy": (
            "Codex, Codex exec, Claude Code, Cursor, Gemini CLI, and other "
            "agent-style CLI providers are not accepted as normal live LLM "
            "providers because they cannot be made a stable pure-generator API "
            "boundary in this system."
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "LLM model policy artifacts document generator routing only. They "
            "are not theorem proof evidence."
        ),
        "all_ok": all_ok,
        "errors": ()
        if all_ok
        else ("Claude generator model policy constants are inconsistent",),
    }


def _llm_model_policy_markdown(payload: dict[str, object]) -> str:
    policy = dict(payload.get("claude_model_selection", {}) or {})
    source_evidence = dict(payload.get("source_evidence", {}) or {})
    models = dict(payload.get("latest_claude_models_by_tier", {}) or {})
    outside_models = dict(
        payload.get("latest_claude_family_models_outside_cost_tiers", {}) or {}
    )
    resolution_policy = dict(
        payload.get("request_time_model_resolution_policy", {}) or {}
    )
    lines = [
        "# AI Statistician LLM Model Policy",
        "",
        f"- Default live provider: `{payload.get('default_live_generator_provider')}`",
        f"- Source checked date: `{payload.get('source_checked_date')}`",
        f"- Supported live providers: {', '.join(str(item) for item in payload.get('supported_live_generator_providers', []))}",
        f"- Prohibited generator providers: {', '.join(str(item) for item in payload.get('prohibited_generator_providers', []))}",
        "",
        "## Claude Tiers",
        "",
        f"- Claude Haiku: `{models.get('haiku', '')}`",
        f"- Claude Sonnet: `{models.get('sonnet', '')}`",
        f"- Claude Opus: `{models.get('opus', '')}`",
        "- Claude API aliases: "
        + ", ".join(
            f"{key}=`{value}`"
            for key, value in sorted(
                dict(
                    payload.get("latest_claude_api_aliases_by_tier", {}) or {}
                ).items()
            )
        ),
        f"- Runtime ID policy: {payload.get('runtime_model_id_policy', '')}",
        "- Outside Opus/Sonnet/Haiku cost tiers: "
        + ", ".join(f"{key}=`{value}`" for key, value in sorted(outside_models.items())),
        "",
        "## Request-Time Resolution",
        "",
        f"- Empty model configs: {resolution_policy.get('empty_model_resolution', '')}",
        f"- Tier-specific overrides: {resolution_policy.get('tier_specific_env_overrides', '')}",
        f"- Explicit overrides: {resolution_policy.get('explicit_model_override_policy', '')}",
        "",
        "## Source",
        "",
        f"- Source evidence: {source_evidence.get('source', '')}",
        f"- Models overview: {policy.get('models_overview_url', '')}",
        f"- Model IDs and versioning: {policy.get('model_ids_and_versioning_url', '')}",
        "- Verified claims: "
        + "; ".join(str(item) for item in source_evidence.get("claims", ())),
        "",
        "## Boundary",
        "",
        str(payload.get("generator_boundary", "")),
        "",
        str(payload.get("proof_evidence_boundary", "")),
    ]
    return "\n".join(lines) + "\n"


def _scoped_llm_response_payload_schema(
    *,
    target_prover_family: str,
    schema_id: str,
    title: str,
    target_prover_families: tuple[str, ...],
) -> dict[str, object]:
    schema = json.loads(
        json.dumps(
            llm_route_planner_response_payload_schema(
                target_prover_family=target_prover_family
            ),
            default=str,
        )
    )
    schema["$id"] = schema_id
    schema["title"] = title
    schema["x-target-prover-families"] = list(target_prover_families)
    schema["description"] = (
        "Target-scoped LLM route-planner response payload schema for the "
        "library-aware formalization gap planner publication bundle."
    )
    return schema


def _contract_payload(library_snapshot_ref: str) -> dict[str, object]:
    return {
        "component": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        "schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "schema_version": 1,
        "library_snapshot_ref": library_snapshot_ref,
        "planner_contract": planner_contract(library_snapshot_ref),
        "schema_catalog_contract": schema_catalog_json_schema(),
        "llm_model_policy_contract": _llm_model_policy_payload(),
        "portable_work_packet_contract": portable_work_packet_contract(),
        "prover_adapter_packet_contract": prover_adapter_packet_json_schema(),
        "prover_adapter_response_contract": prover_adapter_response_json_schema(),
        "prover_adapter_response_validation_row_contract": (
            prover_adapter_response_validation_row_json_schema()
        ),
        "refinement_work_item_contract": refinement_work_item_json_schema(),
        "refinement_tool_response_contract": refinement_tool_response_json_schema(),
        "refinement_evidence_row_contract": refinement_evidence_row_json_schema(),
        "interactive_session_row_contract": interactive_session_row_json_schema(),
        "interactive_decision_policy_row_contract": (
            interactive_decision_policy_row_json_schema()
        ),
        "minimal_delta_decision_row_contract": minimal_delta_decision_row_json_schema(),
        "portable_plan_audit_row_contract": portable_plan_audit_row_json_schema(),
        "library_coverage_map_row_contract": library_coverage_map_row_json_schema(),
        "llm_route_planner_request_contract": llm_route_planner_request_json_schema(),
        "llm_route_planner_target_theorem_context_packet_contract": (
            llm_route_planner_target_theorem_context_packet_json_schema()
        ),
        "llm_route_planner_route_planning_brief_contract": (
            llm_route_planner_route_planning_brief_json_schema()
        ),
        "llm_route_planner_response_contract": llm_route_planner_response_json_schema(),
        "llm_route_planner_response_payload_contract": (
            llm_route_planner_response_payload_schema()
        ),
        "llm_route_planner_response_payload_lean_legacy_contract": (
            _scoped_llm_response_payload_schema(
                target_prover_family="lean4",
                schema_id=LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID,
                title=(
                    "Formalization Gap Planner LLM Route Planner Response "
                    "Payload (Lean Legacy Compatible)"
                ),
                target_prover_families=("lean4",),
            )
        ),
        "llm_route_planner_response_payload_target_prover_contract": (
            _scoped_llm_response_payload_schema(
                target_prover_family="rocq",
                schema_id=LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID,
                title=(
                    "Formalization Gap Planner LLM Route Planner Response "
                    "Payload (Target-Prover Portable)"
                ),
                target_prover_families=PORTABLE_TARGET_PROVER_RESPONSE_PAYLOAD_FAMILIES,
            )
        ),
        "llm_route_planner_response_payload_validation_manifest_contract": (
            llm_route_planner_response_payload_validation_manifest_json_schema()
        ),
        "llm_route_planner_response_payload_validation_row_contract": (
            llm_route_planner_response_payload_validation_row_json_schema()
        ),
        "llm_route_planner_manifest_contract": (
            llm_route_planner_manifest_json_schema()
        ),
        "llm_route_planner_row_contract": llm_route_planner_row_json_schema(),
        "llm_route_planner_seed_route_selection_contract": (
            llm_route_planner_seed_route_selection_json_schema()
        ),
        "route_adoption_blocker_taxonomy_manifest_schema_contract": (
            route_adoption_blocker_taxonomy_manifest_json_schema()
        ),
        "route_adoption_blocker_taxonomy_contract": (
            route_adoption_blocker_taxonomy_payload()
        ),
        "primitive_action_queue_row_contract": primitive_action_queue_row_json_schema(),
        "action_resource_plan_row_contract": action_resource_plan_row_json_schema(),
        "resource_request_queue_row_contract": resource_request_queue_row_json_schema(),
        "resource_response_contract": resource_response_json_schema(),
        "resource_response_ledger_row_contract": resource_response_ledger_row_json_schema(),
        "source_grounding_row_contract": source_grounding_row_json_schema(),
        "route_revision_overlay_row_contract": route_revision_overlay_row_json_schema(),
        "route_stability_audit_row_contract": route_stability_audit_row_json_schema(),
        "route_replan_handoff_row_contract": route_replan_handoff_row_json_schema(),
        "route_replan_handoff_audit_row_contract": (
            route_replan_handoff_audit_row_json_schema()
        ),
        "runtime_handoff_audit_row_contract": runtime_handoff_audit_row_json_schema(),
        "proof_state_triage_row_contract": proof_state_triage_row_json_schema(),
        "ablation_study_row_contract": ablation_study_row_json_schema(),
        "route_alignment_edge_contract": route_alignment_edge_json_schema(),
        "portable_gap_plan_row_contract": portable_gap_plan_row_json_schema(),
        "target_intake_contract": target_intake_json_schema(),
        "target_intake_row_contract": target_intake_row_json_schema(),
        "benchmark_route_contract": benchmark_route_row_json_schema(),
        "evaluation_row_contract": evaluation_row_json_schema(),
        "adapter_registry_row_contract": adapter_registry_row_json_schema(),
        "cross_prover_matrix_audit_row_contract": (
            cross_prover_matrix_audit_row_json_schema()
        ),
        "cross_prover_target_summary_contract": (
            cross_prover_target_summary_json_schema()
        ),
        "component_resource_resource_row_contract": (
            component_resource_registry_resource_row_json_schema()
        ),
        "component_resource_component_row_contract": (
            component_resource_registry_component_row_json_schema()
        ),
        "component_resource_contract_row_contract": (
            component_resource_contract_row_json_schema()
        ),
        "component_resource_execution_plan_contract": (
            component_resource_execution_plan_json_schema()
        ),
        "interactive_route_synthesis_contract": interactive_route_synthesis_contract(),
        "evaluation_protocol": evaluation_protocol(),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _reproduction_payload(
    bundle_id: str,
    *,
    library_snapshot_ref: str,
    has_optional_plan: bool = False,
    has_optional_llm_route_planner: bool = False,
    has_optional_feedback_llm_route_planner: bool = False,
    has_optional_evaluation: bool = False,
    has_optional_interactive_session: bool = False,
    has_optional_runtime_handoff_audit: bool = False,
) -> dict[str, object]:
    standalone_input_for_planner = (
        "<bundle_dir>/artifacts/formalization_gap_planner_llm_route_planner/"
        "formalization_gap_planner_llm_route_planner_standalone_seed.json"
        if has_optional_llm_route_planner
        else "<work_dir>/formalization_gap_planner_llm_route_planner/"
        "formalization_gap_planner_llm_route_planner_standalone_seed.json"
    )
    evaluation_plan_dir = (
        "<bundle_dir>/artifacts/goal_conditioned_minimal_formalization_plan"
        if has_optional_plan
        else "<work_dir>/goal_conditioned_minimal_formalization_plan"
    )
    evaluation_ground_truth = (
        "<bundle_dir>/artifacts/formalization_gap_planner_evaluation/"
        "formalization_gap_planner_evaluation_ground_truth.json"
        if has_optional_evaluation
        else "<bundle_dir>/benchmark/formalization_gap_planner_ground_truth.json"
    )
    ablation_evaluation_dir = (
        "<bundle_dir>/artifacts/formalization_gap_planner_evaluation"
        if has_optional_evaluation
        else "<work_dir>/formalization_gap_planner_evaluation"
    )
    ablation_interactive_session_arg = (
        " --formalization-gap-planner-interactive-session-dir "
        "<bundle_dir>/artifacts/formalization_gap_planner_interactive_session"
        if has_optional_interactive_session
        else ""
    )
    entrypoints = (
        {
            "entrypoint": "formalization-gap-planner-standalone-plan",
            "purpose": "build a portable planner manifest from standalone theorem-route JSON",
            "required_input": "standalone seed emitted by formalization-gap-planner-llm-route-planner",
            "primary_output": "goal_conditioned_minimal_formalization_plan_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-llm-route-planner",
            "purpose": "stage or validate a JSON-only LLM proof-route planner response before portable planning",
            "required_input": "standalone theorem-route JSON from target intake plus optional source, coverage, and prover-feedback contexts",
            "primary_output": "formalization_gap_planner_llm_route_planner_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-llm-route-planner-response-payload-validate",
            "purpose": "preflight reviewed LLM route-planner response payloads against the public schema and staged request context",
            "required_input": "reviewed LLM route payload JSON plus the matching staged LLM route-planner request directory",
            "primary_output": "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-portable-plan-audit",
            "purpose": "validate a portable planner manifest before downstream reuse",
            "required_input": "directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
            "primary_output": "formalization_gap_planner_portable_plan_audit_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-library-coverage-map",
            "purpose": "export per-primitive informal-to-library coverage rows from a portable planner manifest",
            "required_input": "directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
            "primary_output": "formalization_gap_planner_library_coverage_map_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-primitive-action-queue",
            "purpose": "turn library coverage rows into executable primitive formalization work orders",
            "required_input": "directory containing formalization_gap_planner_library_coverage_map_manifest.json",
            "primary_output": "formalization_gap_planner_primitive_action_queue_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-minimal-delta-audit",
            "purpose": "audit AND/OR route-option costs and selected primitive deltas before repair feedback",
            "required_input": "directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
            "primary_output": "formalization_gap_planner_minimal_delta_audit_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-action-resource-plan",
            "purpose": "join primitive formalization work orders to local-first resources, frontier tools, adapters, and resource contracts",
            "required_input": "primitive action-queue directory plus component_resource_registry directory from this bundle",
            "primary_output": "formalization_gap_planner_action_resource_plan_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-resource-request-queue",
            "purpose": "expand action-resource plans into executable per-resource local-first and frontier request packets",
            "required_input": "directory containing formalization_gap_planner_action_resource_plan_manifest.json",
            "primary_output": "formalization_gap_planner_resource_request_queue_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-resource-response-ledger",
            "purpose": "validate local/frontier resource responses against request packets and convert them into bounded planner feedback",
            "required_input": "resource request-queue directory plus optional response JSONL",
            "primary_output": "formalization_gap_planner_resource_response_ledger_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-adapter-registry-audit",
            "purpose": "validate frontier-tool coverage and response contracts",
            "required_input": "adapter_registry directory from this bundle",
            "primary_output": "formalization_gap_planner_adapter_registry_audit_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-benchmark-audit",
            "purpose": "validate route-truth benchmark quality, derived evaluation splits, source refs, and proof boundary",
            "required_input": "benchmark directory from this bundle",
            "primary_output": "formalization_gap_planner_benchmark_audit_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-evaluation",
            "purpose": "score a portable planner manifest against route-truth labels",
            "required_input": "portable planner directory plus route-truth JSON",
            "primary_output": "formalization_gap_planner_evaluation_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-target-intake",
            "purpose": "normalize a new theorem request into a reusable standalone planner seed",
            "required_input": "user-supplied JSON matching contract/formalization_gap_planner_target_intake.schema.json",
            "primary_output": "formalization_gap_planner_target_intake_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-route-adoption-blocker-taxonomy",
            "purpose": "export the reusable route-adoption status and blocker vocabulary without running the planner pipeline",
            "required_input": "none",
            "primary_output": "formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-reuse-smoke",
            "purpose": (
                "run the full public planner path from target intake through "
                "LLM prompt staging, local adapters, route revision, prover "
                "adapter contracts, and publication-bundle audit"
            ),
            "required_input": (
                "target theorem request JSON or AI Statistician runtime "
                "target-intake JSON emitted by research-agent-runtime"
            ),
            "primary_output": "formalization_gap_planner_reuse_smoke_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-ablation-study",
            "purpose": "compare recorded planner metrics against no-literature, no-formal-grounding, no-proof-feedback, and no-route-planner baselines",
            "required_input": "planner, evaluation, and optional interactive-session artifact directories",
            "primary_output": "formalization_gap_planner_ablation_study_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-component-resource-registry-audit",
            "purpose": "validate planner-component coverage by local fallbacks, frontier resources, MCP/CLI surfaces, and cross-prover targets",
            "required_input": "component_resource_registry directory from this bundle",
            "primary_output": "formalization_gap_planner_component_resource_registry_audit_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-prover-adapter-contract",
            "purpose": "export portable work packets for a target prover family",
            "required_input": "portable planner directory plus target prover family and library snapshot ref",
            "primary_output": "formalization_gap_planner_prover_adapter_contract_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-refinement-queue",
            "purpose": "materialize literature, formal-library, and proof-feedback work items from a route plan",
            "required_input": "portable planner directory, optionally with evaluation or replay-calibration artifacts",
            "primary_output": "formalization_gap_planner_refinement_queue_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-refinement-adapter-responses",
            "purpose": "emit deterministic baseline responses for refinement work items",
            "required_input": "refinement queue directory plus optional benchmark ground truth",
            "primary_output": "formalization_gap_planner_refinement_adapter_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-minimal-delta-audit-feedback",
            "purpose": "merge failed minimal-delta audit decisions into route-revision refinement responses",
            "required_input": "refinement queue directory, minimal-delta audit directory, and optional base response JSONL",
            "primary_output": "formalization_gap_planner_minimal_delta_audit_feedback_adapter_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-local-literature-adapter",
            "purpose": "merge local corpus hits into refinement responses for literature-discovery items",
            "required_input": "refinement queue directory, optional base response JSONL, and local text/markdown/json corpus roots",
            "primary_output": "formalization_gap_planner_local_literature_adapter_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-local-formal-source-adapter",
            "purpose": "merge local formal-source and Lean-RAG hits into refinement responses for library-grounding items",
            "required_input": "refinement queue directory, optional base response JSONL, and local formal-source roots or Lean RAG DB",
            "primary_output": "formalization_gap_planner_local_formal_source_adapter_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-local-proof-state-adapter",
            "purpose": "merge local Lean proof-state probes into refinement responses for prover-feedback items",
            "required_input": "refinement queue directory, optional base response JSONL, and optional Lake project",
            "primary_output": "formalization_gap_planner_local_proof_state_adapter_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-prover-adapter-feedback",
            "purpose": "merge target-prover adapter validation rows into refinement prover-feedback responses",
            "required_input": "refinement queue directory plus prover-adapter contract or cross-prover matrix audit output",
            "primary_output": "formalization_gap_planner_prover_adapter_feedback_adapter_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-refinement-evidence",
            "purpose": "validate adapter responses and convert them into route-revision proposals",
            "required_input": "refinement queue directory plus merged response JSONL",
            "primary_output": "formalization_gap_planner_refinement_evidence_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-route-revision-overlay",
            "purpose": (
                "apply accepted refinement evidence and resource-response "
                "ledger feedback back onto route-plan rows"
            ),
            "required_input": (
                "portable planner directory, refinement evidence directory, "
                "and optional resource-response ledger directory"
            ),
            "primary_output": "formalization_gap_planner_route_revision_overlay_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-route-stability-audit",
            "purpose": "decide which revised routes have stabilized and which need bounded evidence expansion",
            "required_input": "portable planner, refinement evidence, and route-revision overlay directories",
            "primary_output": "formalization_gap_planner_route_stability_audit_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-route-replan-handoff",
            "purpose": "turn accepted route-revision overlays into a replayable standalone seed for the next planner round",
            "required_input": "portable planner, route-revision overlay, and optional route-stability audit directories",
            "primary_output": "formalization_gap_planner_route_replan_handoff_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-route-replan-handoff-audit",
            "purpose": "audit that the route-replan handoff is replayable and preserves selected-primitive alignment",
            "required_input": "route-replan handoff directory",
            "primary_output": "formalization_gap_planner_route_replan_handoff_audit_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-runtime-handoff-audit",
            "purpose": (
                "audit AI Statistician runtime bridge handoffs and offline "
                "prompt-only LLM route-planner replay before any live Claude API call"
            ),
            "required_input": "runtime_formalization_gap_planner_handoffs.jsonl emitted by research-agent-runtime",
            "primary_output": "formalization_gap_planner_runtime_handoff_audit_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-proof-state-triage",
            "purpose": "rank route-overlay proof-state statuses into prover repair and formal-gap work items",
            "required_input": "route-revision overlay directory",
            "primary_output": "formalization_gap_planner_proof_state_triage_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-interactive-session",
            "purpose": "summarize the next bounded interaction for each route after evidence and stability checks",
            "required_input": "portable planner directory plus optional refinement, stability, handoff, and triage artifacts",
            "primary_output": "formalization_gap_planner_interactive_session_manifest.json",
        },
        {
            "entrypoint": "formalization-gap-planner-publication-bundle-audit",
            "purpose": "audit a downloaded or regenerated publication bundle",
            "required_input": "publication bundle directory",
            "primary_output": "formalization_gap_planner_publication_bundle_audit_manifest.json",
        },
    )
    commands = (
        {
            "name": "audit_downloaded_bundle",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-publication-bundle-audit "
                "--publication-bundle-dir <bundle_dir> "
                "--out <work_dir>/formalization_gap_planner_publication_bundle_audit"
            ),
        },
        {
            "name": "audit_adapter_registry",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-adapter-registry-audit "
                "--formalization-gap-planner-adapter-registry-dir <bundle_dir>/adapter_registry "
                "--out <work_dir>/formalization_gap_planner_adapter_registry_audit"
            ),
        },
        {
            "name": "audit_benchmark",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-benchmark-audit "
                "--formalization-gap-planner-benchmark-dir <bundle_dir>/benchmark "
                "--out <work_dir>/formalization_gap_planner_benchmark_audit"
            ),
        },
        {
            "name": "audit_component_resource_registry",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-component-resource-registry-audit "
                "--formalization-gap-planner-component-resource-registry-dir "
                "<bundle_dir>/component_resource_registry "
                "--out <work_dir>/formalization_gap_planner_component_resource_registry_audit"
            ),
        },
        {
            "name": "run_evaluation",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-evaluation "
                "--goal-conditioned-minimal-formalization-plan-dir "
                f"{evaluation_plan_dir} "
                "--ground-truth "
                f"{evaluation_ground_truth} "
                "--out <work_dir>/formalization_gap_planner_evaluation"
            ),
        },
        {
            "name": "run_ablation_study",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-ablation-study "
                "--goal-conditioned-minimal-formalization-plan-dir "
                f"{evaluation_plan_dir} "
                "--formalization-gap-planner-evaluation-dir "
                f"{ablation_evaluation_dir} "
                f"{ablation_interactive_session_arg} "
                "--out <work_dir>/formalization_gap_planner_ablation_study"
            ),
        },
        {
            "name": "run_standalone_planner",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-standalone-plan "
                f"--input {standalone_input_for_planner} "
                "--out <work_dir>/goal_conditioned_minimal_formalization_plan"
            ),
        },
        {
            "name": "run_llm_route_planner",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-llm-route-planner "
                "--input <work_dir>/formalization_gap_planner_target_intake/"
                "formalization_gap_planner_target_intake_standalone_seed.json "
                "--provider anthropic "
                "--model-tier auto "
                "--max-repair-attempts 1 "
                "--formalization-gap-planner-target-intake-dir "
                "<work_dir>/formalization_gap_planner_target_intake "
                "--formalization-gap-planner-component-resource-registry-dir "
                "<bundle_dir>/component_resource_registry "
                "--out <work_dir>/formalization_gap_planner_llm_route_planner"
            ),
        },
        {
            "name": "validate_llm_route_payloads",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-llm-route-planner-response-payload-validate "
                "--input <reviewed_llm_route_payload_json> "
                "--request-context <work_dir>/formalization_gap_planner_llm_route_planner "
                "--out <work_dir>/formalization_gap_planner_llm_route_planner_response_payload_validation"
            ),
        },
        {
            "name": "run_target_intake",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-target-intake "
                "--input <bundle_dir>/examples/formalization_gap_planner_target_intake_example.json "
                "--out <work_dir>/formalization_gap_planner_target_intake"
            ),
        },
        {
            "name": "export_route_adoption_blocker_taxonomy",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-route-adoption-blocker-taxonomy "
                "--out <work_dir>/formalization_gap_planner_route_adoption_blocker_taxonomy"
            ),
        },
        {
            "name": "run_reuse_smoke",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-reuse-smoke "
                "--input <bundle_dir>/examples/formalization_gap_planner_target_intake_example.json "
                "--target-prover-family rocq "
                f"--target-library-snapshot-ref {library_snapshot_ref} "
                "--llm-route-planner-provider anthropic "
                "--llm-route-planner-model-tier auto "
                "--llm-route-planner-max-repair-attempts 1 "
                "--feedback-llm-route-planner-provider anthropic "
                "--feedback-llm-route-planner-model-tier auto "
                "--feedback-llm-route-planner-max-repair-attempts 1 "
                "--out <work_dir>/formalization_gap_planner_reuse_smoke"
            ),
        },
        {
            "name": "run_runtime_handoff_reuse_smoke",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-reuse-smoke "
                "--input "
                "<ai_statistician_runtime_dir>/runtime_formalization_gap_planner_target_intake/"
                "<runtime_target_intake_json> "
                f"--target-prover-family {PORTABLE_TARGET_PROVER_FAMILY_HINT} "
                "--target-library-snapshot-ref <runtime-library-snapshot-ref> "
                "--llm-route-planner-provider anthropic "
                "--llm-route-planner-model-tier auto "
                "--llm-route-planner-max-repair-attempts 1 "
                "--feedback-llm-route-planner-provider anthropic "
                "--feedback-llm-route-planner-model-tier auto "
                "--feedback-llm-route-planner-max-repair-attempts 1 "
                "--out <work_dir>/formalization_gap_planner_runtime_reuse_smoke"
            ),
        },
        {
            "name": "audit_standalone_plan",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-portable-plan-audit "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--out <work_dir>/formalization_gap_planner_portable_plan_audit"
            ),
        },
        {
            "name": "export_library_coverage_map",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-library-coverage-map "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--out <work_dir>/formalization_gap_planner_library_coverage_map"
            ),
        },
        {
            "name": "export_primitive_action_queue",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-primitive-action-queue "
                "--formalization-gap-planner-library-coverage-map-dir "
                "<work_dir>/formalization_gap_planner_library_coverage_map "
                "--out <work_dir>/formalization_gap_planner_primitive_action_queue"
            ),
        },
        {
            "name": "run_minimal_delta_audit",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-minimal-delta-audit "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--out <work_dir>/formalization_gap_planner_minimal_delta_audit"
            ),
        },
        {
            "name": "export_action_resource_plan",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-action-resource-plan "
                "--formalization-gap-planner-primitive-action-queue-dir "
                "<work_dir>/formalization_gap_planner_primitive_action_queue "
                "--formalization-gap-planner-component-resource-registry-dir "
                "<bundle_dir>/component_resource_registry "
                "--out <work_dir>/formalization_gap_planner_action_resource_plan"
            ),
        },
        {
            "name": "export_resource_request_queue",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-resource-request-queue "
                "--formalization-gap-planner-action-resource-plan-dir "
                "<work_dir>/formalization_gap_planner_action_resource_plan "
                "--out <work_dir>/formalization_gap_planner_resource_request_queue"
            ),
        },
        {
            "name": "export_resource_response_ledger",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-resource-response-ledger "
                "--formalization-gap-planner-resource-request-queue-dir "
                "<work_dir>/formalization_gap_planner_resource_request_queue "
                "--out <work_dir>/formalization_gap_planner_resource_response_ledger"
            ),
        },
        {
            "name": "export_target_prover_packets",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-prover-adapter-contract "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                f"--target-prover-family {PORTABLE_TARGET_PROVER_FAMILY_HINT} "
                "--library-snapshot-ref <target-library-snapshot-ref> "
                "--out <work_dir>/formalization_gap_planner_prover_adapter_contract"
            ),
        },
        {
            "name": "run_refinement_queue",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-refinement-queue "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--out <work_dir>/formalization_gap_planner_refinement_queue"
            ),
        },
        {
            "name": "run_refinement_adapter_responses",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-refinement-adapter-responses "
                "--formalization-gap-planner-refinement-queue-dir "
                "<work_dir>/formalization_gap_planner_refinement_queue "
                "--ground-truth <bundle_dir>/benchmark/formalization_gap_planner_ground_truth.json "
                "--out <work_dir>/formalization_gap_planner_refinement_adapter"
            ),
        },
        {
            "name": "run_minimal_delta_audit_feedback",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-minimal-delta-audit-feedback "
                "--formalization-gap-planner-refinement-queue-dir "
                "<work_dir>/formalization_gap_planner_refinement_queue "
                "--formalization-gap-planner-minimal-delta-audit-dir "
                "<work_dir>/formalization_gap_planner_minimal_delta_audit "
                "--base-response-jsonl "
                "<work_dir>/formalization_gap_planner_refinement_adapter/"
                "formalization_gap_planner_refinement_evidence_responses.jsonl "
                "--out <work_dir>/formalization_gap_planner_minimal_delta_audit_feedback_adapter"
            ),
        },
        {
            "name": "run_local_literature_adapter",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-local-literature-adapter "
                "--formalization-gap-planner-refinement-queue-dir "
                "<work_dir>/formalization_gap_planner_refinement_queue "
                "--base-response-jsonl "
                "<work_dir>/formalization_gap_planner_minimal_delta_audit_feedback_adapter/"
                "formalization_gap_planner_refinement_evidence_responses.jsonl "
                "--literature-root <local-paper-or-text-corpus-root> "
                "--out <work_dir>/formalization_gap_planner_local_literature_adapter"
            ),
        },
        {
            "name": "run_local_formal_source_adapter",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-local-formal-source-adapter "
                "--formalization-gap-planner-refinement-queue-dir "
                "<work_dir>/formalization_gap_planner_refinement_queue "
                "--base-response-jsonl "
                "<work_dir>/formalization_gap_planner_local_literature_adapter/"
                "formalization_gap_planner_refinement_evidence_responses.jsonl "
                "--formal-source-root <formal-source-id>=<formal-source-root> "
                "--lean-rag-db <optional-lean-rag-sqlite> "
                "--out <work_dir>/formalization_gap_planner_local_formal_source_adapter"
            ),
        },
        {
            "name": "run_local_proof_state_adapter",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-local-proof-state-adapter "
                "--formalization-gap-planner-refinement-queue-dir "
                "<work_dir>/formalization_gap_planner_refinement_queue "
                "--base-response-jsonl "
                "<work_dir>/formalization_gap_planner_local_formal_source_adapter/"
                "formalization_gap_planner_refinement_evidence_responses.jsonl "
                "--lean-project <optional-lake-project-root> "
                "--out <work_dir>/formalization_gap_planner_local_proof_state_adapter"
            ),
        },
        {
            "name": "run_prover_adapter_feedback",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-prover-adapter-feedback "
                "--formalization-gap-planner-refinement-queue-dir "
                "<work_dir>/formalization_gap_planner_refinement_queue "
                "--base-response-jsonl "
                "<work_dir>/formalization_gap_planner_local_proof_state_adapter/"
                "formalization_gap_planner_refinement_evidence_responses.jsonl "
                "--formalization-gap-planner-prover-adapter-contract-dir "
                "<work_dir>/formalization_gap_planner_prover_adapter_contract "
                "--formalization-gap-planner-cross-prover-matrix-audit-dir "
                "<work_dir>/formalization_gap_planner_cross_prover_matrix_audit "
                "--out <work_dir>/formalization_gap_planner_prover_adapter_feedback_adapter"
            ),
        },
        {
            "name": "run_refinement_evidence",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-refinement-evidence "
                "--formalization-gap-planner-refinement-queue-dir "
                "<work_dir>/formalization_gap_planner_refinement_queue "
                "--response-jsonl "
                "<work_dir>/formalization_gap_planner_prover_adapter_feedback_adapter/"
                "formalization_gap_planner_refinement_evidence_responses.jsonl "
                "--out <work_dir>/formalization_gap_planner_refinement_evidence"
            ),
        },
        {
            "name": "run_route_revision_overlay",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-route-revision-overlay "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--formalization-gap-planner-refinement-evidence-dir "
                "<work_dir>/formalization_gap_planner_refinement_evidence "
                "--formalization-gap-planner-resource-response-ledger-dir "
                "<work_dir>/formalization_gap_planner_resource_response_ledger "
                "--out <work_dir>/formalization_gap_planner_route_revision_overlay"
            ),
        },
        {
            "name": "run_route_stability_audit",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-route-stability-audit "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--formalization-gap-planner-refinement-evidence-dir "
                "<work_dir>/formalization_gap_planner_refinement_evidence "
                "--formalization-gap-planner-route-revision-overlay-dir "
                "<work_dir>/formalization_gap_planner_route_revision_overlay "
                "--out <work_dir>/formalization_gap_planner_route_stability_audit"
            ),
        },
        {
            "name": "run_route_replan_handoff",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-route-replan-handoff "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--formalization-gap-planner-route-revision-overlay-dir "
                "<work_dir>/formalization_gap_planner_route_revision_overlay "
                "--formalization-gap-planner-route-stability-audit-dir "
                "<work_dir>/formalization_gap_planner_route_stability_audit "
                "--out <work_dir>/formalization_gap_planner_route_replan_handoff"
            ),
        },
        {
            "name": "audit_route_replan_handoff",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-route-replan-handoff-audit "
                "--formalization-gap-planner-route-replan-handoff-dir "
                "<work_dir>/formalization_gap_planner_route_replan_handoff "
                "--out <work_dir>/formalization_gap_planner_route_replan_handoff_audit"
            ),
        },
        {
            "name": "audit_runtime_handoff",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-runtime-handoff-audit "
                "--runtime-formalization-gap-planner-handoffs-jsonl "
                "<ai_statistician_runtime_dir>/runtime_formalization_gap_planner_handoffs.jsonl "
                "--out <work_dir>/formalization_gap_planner_runtime_handoff_audit"
            ),
        },
        {
            "name": "run_proof_state_triage",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-proof-state-triage "
                "--formalization-gap-planner-route-revision-overlay-dir "
                "<work_dir>/formalization_gap_planner_route_revision_overlay "
                "--out <work_dir>/formalization_gap_planner_proof_state_triage"
            ),
        },
        {
            "name": "run_interactive_session",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-interactive-session "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--formalization-gap-planner-refinement-queue-dir "
                "<work_dir>/formalization_gap_planner_refinement_queue "
                "--formalization-gap-planner-refinement-evidence-dir "
                "<work_dir>/formalization_gap_planner_refinement_evidence "
                "--formalization-gap-planner-route-stability-audit-dir "
                "<work_dir>/formalization_gap_planner_route_stability_audit "
                "--formalization-gap-planner-route-replan-handoff-dir "
                "<work_dir>/formalization_gap_planner_route_replan_handoff "
                "--formalization-gap-planner-proof-state-triage-dir "
                "<work_dir>/formalization_gap_planner_proof_state_triage "
                "--formalization-gap-planner-component-resource-registry-dir "
                "<bundle_dir>/component_resource_registry "
                "--out <work_dir>/formalization_gap_planner_interactive_session"
            ),
        },
        {
            "name": "run_feedback_llm_route_planner",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-llm-route-planner "
                "--input <work_dir>/formalization_gap_planner_route_replan_handoff/"
                "formalization_gap_planner_route_replan_standalone_seed.json "
                "--provider anthropic "
                "--model-tier auto "
                "--max-repair-attempts 1 "
                "--formalization-gap-planner-target-intake-dir "
                "<work_dir>/formalization_gap_planner_target_intake "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "<work_dir>/goal_conditioned_minimal_formalization_plan "
                "--formalization-gap-planner-library-coverage-map-dir "
                "<work_dir>/formalization_gap_planner_library_coverage_map "
                "--formalization-gap-planner-source-grounding-audit-dir "
                "<work_dir>/formalization_gap_planner_source_grounding_audit "
                "--formalization-gap-planner-resource-response-ledger-dir "
                "<work_dir>/formalization_gap_planner_resource_response_ledger "
                "--formalization-gap-planner-refinement-evidence-dir "
                "<work_dir>/formalization_gap_planner_refinement_evidence "
                "--formalization-gap-planner-route-revision-overlay-dir "
                "<work_dir>/formalization_gap_planner_route_revision_overlay "
                "--formalization-gap-planner-route-replan-handoff-dir "
                "<work_dir>/formalization_gap_planner_route_replan_handoff "
                "--formalization-gap-planner-interactive-session-dir "
                "<work_dir>/formalization_gap_planner_interactive_session "
                "--formalization-gap-planner-component-resource-registry-dir "
                "<bundle_dir>/component_resource_registry "
                "--out <work_dir>/formalization_gap_planner_feedback_llm_route_planner"
            ),
        },
        {
            "name": "validate_feedback_llm_route_payloads",
            "command": (
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-llm-route-planner-response-payload-validate "
                "--input <reviewed_feedback_llm_route_payload_json> "
                "--request-context <work_dir>/formalization_gap_planner_feedback_llm_route_planner "
                "--out <work_dir>/formalization_gap_planner_feedback_llm_route_planner_response_payload_validation"
            ),
        },
    )
    bundle_relative_artifacts = (
        "contract/formalization_gap_planner_portable_contract.json",
        "contract/ai_statistician_llm_model_policy.json",
        "contract/ai_statistician_llm_model_policy.md",
        "contract/formalization_gap_planner_schema_catalog.json",
        "contract/formalization_gap_planner_schema_catalog.schema.json",
        "contract/formalization_gap_planner_publication_bundle_manifest.schema.json",
        "contract/library_aware_formalization_gap_plan.schema.json",
        "contract/formalization_gap_planner_standalone_input.schema.json",
        "contract/formalization_gap_planner_target_intake.schema.json",
        "contract/formalization_gap_planner_target_intake_row.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_request.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_target_theorem_context_packet.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_response.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_response_payload.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_response_payload_lean_legacy.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_response_payload_target_prover.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_manifest.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_row.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json",
        "contract/formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json",
        "contract/formalization_gap_planner_route_adoption_blocker_taxonomy.schema.json",
        "contract/formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.schema.json",
        "contract/formalization_gap_planner_route_adoption_blocker_taxonomy.json",
        "contract/formalization_gap_planner_prover_adapter_packet.schema.json",
        "contract/formalization_gap_planner_prover_adapter_response.schema.json",
        "contract/formalization_gap_planner_prover_adapter_response_validation_row.schema.json",
        "contract/formalization_gap_planner_refinement_work_item.schema.json",
        "contract/formalization_gap_planner_refinement_tool_response.schema.json",
        "contract/formalization_gap_planner_refinement_evidence_row.schema.json",
        "contract/formalization_gap_planner_interactive_session_row.schema.json",
        "contract/formalization_gap_planner_interactive_decision_policy_row.schema.json",
        "contract/formalization_gap_planner_minimal_delta_decision_row.schema.json",
        "contract/formalization_gap_planner_portable_plan_audit_row.schema.json",
        "contract/formalization_gap_planner_library_coverage_map_row.schema.json",
        "contract/formalization_gap_planner_primitive_action_queue_row.schema.json",
        "contract/formalization_gap_planner_action_resource_plan_row.schema.json",
        "contract/formalization_gap_planner_resource_request_queue_row.schema.json",
        "contract/formalization_gap_planner_resource_response.schema.json",
        "contract/formalization_gap_planner_resource_response_ledger_row.schema.json",
        "contract/formalization_gap_planner_source_grounding_row.schema.json",
        "contract/formalization_gap_planner_route_revision_overlay_row.schema.json",
        "contract/formalization_gap_planner_route_stability_audit_row.schema.json",
        "contract/formalization_gap_planner_route_replan_handoff_row.schema.json",
        "contract/formalization_gap_planner_route_replan_handoff_audit_row.schema.json",
        "contract/formalization_gap_planner_runtime_handoff_audit_row.schema.json",
        "contract/formalization_gap_planner_proof_state_triage_row.schema.json",
        "contract/formalization_gap_planner_ablation_study_row.schema.json",
        "contract/formalization_gap_planner_route_alignment_edge.schema.json",
        "contract/library_aware_formalization_gap_plan_row.schema.json",
        "contract/formalization_gap_planner_benchmark_route.schema.json",
        "contract/formalization_gap_planner_evaluation_row.schema.json",
        "contract/formalization_gap_planner_adapter_registry_row.schema.json",
        "contract/formalization_gap_planner_cross_prover_matrix_audit_row.schema.json",
        "contract/formalization_gap_planner_cross_prover_target_summary.schema.json",
        "contract/formalization_gap_planner_component_resource_resource_row.schema.json",
        "contract/formalization_gap_planner_component_resource_component_row.schema.json",
        "contract/formalization_gap_planner_component_resource_execution_plan.schema.json",
        "contract/formalization_gap_planner_component_resource_contract_row.schema.json",
        "benchmark/formalization_gap_planner_benchmark_manifest.json",
        "benchmark/formalization_gap_planner_benchmark_routes.jsonl",
        "benchmark/formalization_gap_planner_benchmark_route.schema.json",
        "benchmark_audit/formalization_gap_planner_benchmark_audit_manifest.json",
        "adapter_registry/formalization_gap_planner_adapter_registry_manifest.json",
        "adapter_registry/formalization_gap_planner_adapter_registry.jsonl",
        "adapter_registry/formalization_gap_planner_adapter_registry_row.schema.json",
        "component_resource_registry/formalization_gap_planner_component_resource_registry_manifest.json",
        "component_resource_registry/formalization_gap_planner_component_resource_registry.jsonl",
        "component_resource_registry/formalization_gap_planner_component_resource_resources.jsonl",
        "component_resource_registry/formalization_gap_planner_component_resource_execution_plans.jsonl",
        "component_resource_registry/formalization_gap_planner_component_resource_contracts.jsonl",
        "component_resource_registry/formalization_gap_planner_component_resource_resource_row.schema.json",
        "component_resource_registry/formalization_gap_planner_component_resource_component_row.schema.json",
        "component_resource_registry/formalization_gap_planner_component_resource_execution_plan.schema.json",
        "component_resource_registry/formalization_gap_planner_component_resource_contract_row.schema.json",
        "artifacts/formalization_gap_planner_llm_route_planner/formalization_gap_planner_llm_route_planner_manifest.json",
        "artifacts/formalization_gap_planner_llm_route_planner/formalization_gap_planner_llm_route_planner_requests.jsonl",
        "artifacts/formalization_gap_planner_llm_route_planner/formalization_gap_planner_llm_route_planner.jsonl",
        "artifacts/formalization_gap_planner_llm_route_planner/formalization_gap_planner_llm_route_planner_standalone_seed.json",
        "artifacts/formalization_gap_planner_feedback_llm_route_planner/formalization_gap_planner_llm_route_planner_manifest.json",
        "artifacts/formalization_gap_planner_feedback_llm_route_planner/formalization_gap_planner_llm_route_planner_requests.jsonl",
        "artifacts/formalization_gap_planner_feedback_llm_route_planner/formalization_gap_planner_llm_route_planner.jsonl",
        "artifacts/formalization_gap_planner_feedback_llm_route_planner/formalization_gap_planner_llm_route_planner_standalone_seed.json",
        "artifacts/formalization_gap_planner_evaluation/formalization_gap_planner_evaluation_manifest.json",
        "artifacts/formalization_gap_planner_evaluation/formalization_gap_planner_evaluation.jsonl",
        "artifacts/formalization_gap_planner_evaluation/formalization_gap_planner_evaluation_row.schema.json",
        "artifacts/formalization_gap_planner_evaluation/formalization_gap_planner_evaluation_ground_truth.json",
        "artifacts/formalization_gap_planner_action_resource_plan/formalization_gap_planner_action_resource_plan_manifest.json",
        "artifacts/formalization_gap_planner_resource_request_queue/formalization_gap_planner_resource_request_queue_manifest.json",
        "artifacts/formalization_gap_planner_resource_response_ledger/formalization_gap_planner_resource_response_ledger_manifest.json",
        "artifacts/formalization_gap_planner_route_replan_handoff/formalization_gap_planner_route_replan_handoff_manifest.json",
        "artifacts/formalization_gap_planner_route_replan_handoff_audit/formalization_gap_planner_route_replan_handoff_audit_manifest.json",
        "artifacts/formalization_gap_planner_runtime_handoff_audit/formalization_gap_planner_runtime_handoff_audit_manifest.json",
        "artifacts/formalization_gap_planner_proof_state_triage/formalization_gap_planner_proof_state_triage_manifest.json",
        "examples/formalization_gap_planner_standalone_example.json",
        "examples/formalization_gap_planner_target_intake_example.json",
        "docs/library_aware_formalization_gap_planner.md",
        "docs/evaluation_benchmark_strategy.md",
    )
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_reproduction_manifest",
        "bundle_id": bundle_id,
        "packaged_component": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "library_snapshot_ref": library_snapshot_ref,
        "has_optional_llm_route_planner": has_optional_llm_route_planner,
        "has_optional_feedback_llm_route_planner": has_optional_feedback_llm_route_planner,
        "has_optional_interactive_session": has_optional_interactive_session,
        "has_optional_runtime_handoff_audit": has_optional_runtime_handoff_audit,
        "n_entrypoints": len(entrypoints),
        "n_commands": len(commands),
        "n_bundle_relative_artifacts": len(bundle_relative_artifacts),
        "entrypoints": entrypoints,
        "commands": commands,
        "bundle_relative_artifacts": bundle_relative_artifacts,
        "portable_reuse_targets": PORTABLE_REUSE_TARGETS,
        "all_ok": True,
        "errors": (),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "commands are reproduction and integration entrypoints, not proof claims",
            "commands that reference artifacts/ require the corresponding optional run artifacts to be bundled",
            "local adapter commands can run as deterministic diagnostics, but richer evidence requires replacing local corpus, formal-source, Lean-RAG, and Lake-project placeholders",
            "target prover proof status still requires kernel replay with no placeholders",
            "replace angle-bracket placeholders before executing commands",
        ],
    }


def _reproduction_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Reproduction",
        "",
        f"- Bundle: `{payload.get('bundle_id')}`",
        f"- Entry points: {payload.get('n_entrypoints')}",
        f"- Commands: {payload.get('n_commands')}",
        f"- Reuse targets: {', '.join(str(item) for item in payload.get('portable_reuse_targets', []))}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Limitations",
        "",
    ]
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Commands",
            "",
        ]
    )
    for row in payload.get("commands", []):
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### {row.get('name')}",
                "",
                "```bash",
                str(row.get("command", "")),
                "```",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def _copy_optional_artifact(
    artifact_name: str,
    source_dir: Path | None,
    dest_dir: Path,
    errors: list[str],
) -> dict[str, object]:
    if source_dir is None:
        return {
            "artifact_name": artifact_name,
            "requested": False,
            "source_dir": "",
            "dest_dir": str(dest_dir),
            "n_files_copied": 0,
            "copied_files": (),
            "missing_files": (),
            "ok": True,
        }
    if not source_dir.exists():
        errors.append(f"missing optional artifact directory: {source_dir}")
        return {
            "artifact_name": artifact_name,
            "requested": True,
            "source_dir": str(source_dir),
            "dest_dir": str(dest_dir),
            "n_files_copied": 0,
            "copied_files": (),
            "missing_files": OPTIONAL_ARTIFACT_FILES.get(artifact_name, ()),
            "ok": False,
        }
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied_files: list[str] = []
    missing_files: list[str] = []
    for filename in OPTIONAL_ARTIFACT_FILES.get(artifact_name, ()):
        source_path = source_dir / filename
        if not source_path.exists():
            missing_files.append(filename)
            continue
        dest_path = dest_dir / filename
        shutil.copy2(source_path, dest_path)
        copied_files.append(str(dest_path))
    return {
        "artifact_name": artifact_name,
        "requested": True,
        "source_dir": str(source_dir),
        "dest_dir": str(dest_dir),
        "n_files_copied": len(copied_files),
        "copied_files": tuple(copied_files),
        "missing_files": tuple(missing_files),
        "ok": bool(copied_files) and not missing_files,
    }


def _manifest_summary(
    source_dir: Path | None,
    filename: str,
    keys: tuple[str, ...],
) -> dict[str, object]:
    if source_dir is None:
        return {
            "requested": False,
            "manifest_path": "",
            **{key: 0 for key in keys},
        }
    manifest_path = source_dir / filename
    payload = _read_json_no_error(manifest_path)
    return {
        "requested": True,
        "manifest_path": str(manifest_path),
        **{key: payload.get(key, 0) for key in keys},
    }


def _library_coverage_map_summary(source_dir: Path | None) -> dict[str, object]:
    zero_summary: dict[str, object] = {
        "requested": False,
        "manifest_path": "",
        "target_prover_family": "",
        "n_target_prover_families": 0,
        "by_target_prover_family": {},
        "n_coverage_rows": 0,
        "n_ok": 0,
        "n_failed": 0,
        "n_row_schema_valid": 0,
        "n_row_schema_invalid": 0,
        "all_ok": False,
    }
    if source_dir is None:
        return zero_summary
    manifest_path = (
        source_dir
        / "formalization_gap_planner_library_coverage_map_manifest.json"
    )
    payload = _read_json_no_error(manifest_path)
    rows = _read_jsonl_dict_rows_no_error(
        source_dir / "formalization_gap_planner_library_coverage_map.jsonl"
    )
    by_target = _count_map(payload.get("by_target_prover_family", {}))
    if not by_target and rows:
        by_target = dict(
            sorted(
                Counter(
                    _target_prover_key(row.get("target_prover_family", ""))
                    or "unknown"
                    for row in rows
                ).items()
            )
        )
    target_family = str(payload.get("target_prover_family", "") or "").strip()
    if not target_family and len(by_target) == 1:
        target_family = next(iter(by_target))
    n_target_families = int(
        payload.get("n_target_prover_families", len(by_target)) or 0
    )
    if not n_target_families and by_target:
        n_target_families = len(by_target)
    return {
        **zero_summary,
        "requested": True,
        "manifest_path": str(manifest_path),
        "target_prover_family": target_family,
        "n_target_prover_families": n_target_families,
        "by_target_prover_family": by_target,
        "n_coverage_rows": int(
            payload.get("n_coverage_rows", len(rows)) or 0
        ),
        "n_ok": int(
            payload.get(
                "n_ok",
                sum(1 for row in rows if bool(row.get("ok", False))),
            )
            or 0
        ),
        "n_failed": int(
            payload.get(
                "n_failed",
                sum(1 for row in rows if not bool(row.get("ok", False))),
            )
            or 0
        ),
        "n_row_schema_valid": int(payload.get("n_row_schema_valid", 0) or 0),
        "n_row_schema_invalid": int(payload.get("n_row_schema_invalid", 0) or 0),
        "all_ok": bool(payload.get("all_ok", False)),
    }


def _int_or_zero(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _count_map(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): _int_or_zero(count)
        for key, count in sorted(value.items(), key=lambda item: str(item[0]))
    }


def _cross_prover_formal_attempt_dependency_summary(
    source_dir: Path | None,
) -> dict[str, object]:
    zero_summary: dict[str, object] = {
        "requested": False,
        "manifest_path": "",
        "target_summary_path": "",
        "n_total_packets": 0,
        "n_total_packets_with_formal_attempt_dependency": 0,
        "n_total_packets_formal_attempt_initial_ready": 0,
        "n_total_packets_formal_attempt_waiting": 0,
        "n_total_packets_formal_attempt_missing_prerequisites": 0,
        "by_total_packet_formal_attempt_dependency_status": {},
        "n_total_response_minimal_delta_action_witnesses_required": 0,
        "n_total_response_minimal_delta_action_witnesses_acknowledged": 0,
        "n_total_response_minimal_delta_action_witnesses_unacknowledged": 0,
        "n_total_response_addressed_minimal_delta_action_witnesses": 0,
        "target_summary_consistent": False,
    }
    if source_dir is None:
        return zero_summary
    manifest_path = (
        source_dir
        / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json"
    )
    target_summary_path = (
        source_dir / "formalization_gap_planner_cross_prover_target_summary.json"
    )
    manifest = _read_json_no_error(manifest_path)
    target_summary = _read_json_no_error(target_summary_path)
    counter_fields = (
        "n_total_packets_with_formal_attempt_dependency",
        "n_total_packets_formal_attempt_initial_ready",
        "n_total_packets_formal_attempt_waiting",
        "n_total_packets_formal_attempt_missing_prerequisites",
    )
    witness_counter_fields = (
        (
            "n_response_minimal_delta_action_witnesses_required",
            "n_total_response_minimal_delta_action_witnesses_required",
        ),
        (
            "n_response_minimal_delta_action_witnesses_acknowledged",
            "n_total_response_minimal_delta_action_witnesses_acknowledged",
        ),
        (
            "n_response_minimal_delta_action_witnesses_unacknowledged",
            "n_total_response_minimal_delta_action_witnesses_unacknowledged",
        ),
        (
            "n_response_addressed_minimal_delta_action_witnesses",
            "n_total_response_addressed_minimal_delta_action_witnesses",
        ),
    )
    manifest_counters = {
        field_name: _int_or_zero(manifest.get(field_name))
        for field_name in counter_fields
    }
    target_summary_counters = {
        field_name: _int_or_zero(target_summary.get(field_name))
        for field_name in counter_fields
    }
    manifest_witness_counters = {
        target_field_name: _int_or_zero(manifest.get(manifest_field_name))
        for manifest_field_name, target_field_name in witness_counter_fields
    }
    target_summary_witness_counters = {
        target_field_name: _int_or_zero(target_summary.get(target_field_name))
        for _, target_field_name in witness_counter_fields
    }
    manifest_histogram = _count_map(
        manifest.get("by_total_packet_formal_attempt_dependency_status")
    )
    target_summary_histogram = _count_map(
        target_summary.get("by_total_packet_formal_attempt_dependency_status")
    )
    total_packets = _int_or_zero(manifest.get("n_total_packets"))
    target_total_packets = _int_or_zero(target_summary.get("n_total_packets"))
    return {
        **zero_summary,
        "requested": True,
        "manifest_path": str(manifest_path),
        "target_summary_path": str(target_summary_path),
        "n_total_packets": total_packets,
        **manifest_counters,
        **manifest_witness_counters,
        "by_total_packet_formal_attempt_dependency_status": manifest_histogram,
        "target_summary_consistent": (
            total_packets == target_total_packets
            and manifest_counters == target_summary_counters
            and manifest_witness_counters == target_summary_witness_counters
            and manifest_histogram == target_summary_histogram
        ),
    }


def _evaluation_manifest_summary(source_dir: Path | None) -> dict[str, object]:
    zero_summary: dict[str, object] = {
        "requested": False,
        "manifest_path": "",
        "n_evaluation_rows": 0,
        "n_evaluation_row_schema_valid": 0,
        "n_evaluation_row_schema_invalid": 0,
        "n_matched_ground_truth": 0,
        "n_missing_ground_truth": 0,
        "n_alignment_contract_ok": 0,
        "n_feedback_loop_ready": 0,
        "n_unaligned_primitives": 0,
        "n_minimal_delta_route_options": 0,
        "mean_minimal_delta_selected_route_cost": 0.0,
        "n_kernel_verified_ground_truth": 0,
        "n_kernel_verification_witnesses": 0,
        "n_kernel_verified_ground_truth_with_witnesses": 0,
        "mean_alignment_coverage": 0.0,
        "n_realization_missing_selected_formal_primitives": 0,
        "n_realization_missing_delta_alignment_primitives": 0,
        "n_rows_with_incomplete_cost_hint_baseline_coverage": 0,
        "n_realization_cost_hint_baseline_primitives": 0,
        "n_realization_omitted_cost_hint_primitives": 0,
        "realization_missing_selected_formal_primitives": (),
        "realization_missing_delta_alignment_primitives": (),
        "realization_cost_hint_baseline_primitives": (),
        "realization_omitted_cost_hint_primitives": (),
        "n_rows_with_llm_route_planner_residual_goal_contexts": 0,
        "n_llm_route_planner_residual_goal_contexts": 0,
        "n_llm_route_planner_residual_goal_context_source_refs": 0,
        "n_llm_route_planner_residual_goal_context_provenance_values": 0,
        "n_llm_route_planner_residual_goals_with_context": 0,
        "n_llm_route_planner_residual_goals_without_context": 0,
        "n_rows_with_llm_route_planner_route_option_selection_brief": 0,
        "n_llm_route_planner_route_option_selection_candidate_options": 0,
        "n_llm_route_planner_route_option_selection_candidate_primitives": 0,
        "n_llm_route_planner_route_option_selection_candidates_with_residual_goals": 0,
        "n_llm_route_planner_route_option_selection_candidate_residual_goals": 0,
        "n_llm_route_planner_route_option_selection_lower_bound_residual_goals": 0,
        "n_rows_with_llm_route_planner_route_option_selected_route_option": 0,
        "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals": 0,
        "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": 0,
        "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta": 0,
        "n_llm_route_planner_route_option_selected_matches_lower_bound": 0,
        "n_llm_route_planner_route_option_selected_mismatches_lower_bound": 0,
        "n_llm_route_planner_route_option_selected_matches_minimal_delta": 0,
        "n_llm_route_planner_route_option_selected_mismatches_minimal_delta": 0,
        "n_rows_with_llm_route_planner_route_adoption_status": 0,
        "n_rows_ready_for_route_adoption": 0,
        "n_rows_pending_refinement_before_route_adoption": 0,
        "n_rows_awaiting_llm_route_planner_response": 0,
        "n_rows_rejected_llm_route_plan": 0,
        "n_llm_route_adoption_blockers": 0,
        "n_llm_route_adoption_pending_quality_control_blockers": 0,
        "n_llm_route_adoption_pending_source_grounding_blockers": 0,
        "n_llm_route_adoption_pending_formal_attempt_queue_blockers": 0,
        "n_rows_with_llm_route_planner_route_adoption_preconditions": 0,
        "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions": 0,
        "n_llm_route_planner_route_adoption_precondition_known_blockers": 0,
        "n_llm_route_planner_route_adoption_precondition_required_response_fields": 0,
        "n_llm_route_planner_route_adoption_precondition_target_primitives": 0,
        "llm_route_planner_route_adoption_precondition_known_blockers": (),
        "llm_route_planner_route_adoption_precondition_required_response_fields": (),
        "llm_route_planner_route_adoption_precondition_target_primitives": (),
        "llm_route_adoption_blockers": (),
        "llm_route_adoption_blocker_counts": {},
        "llm_route_adoption_status_counts": {},
        "evaluation_by_llm_route_adoption_blocker": {},
        "llm_route_planner_provider_usage_summary": {},
        "n_rows_with_llm_route_planner_provider_usage": 0,
        "total_llm_route_planner_provider_input_tokens": 0,
        "total_llm_route_planner_provider_output_tokens": 0,
        "total_llm_route_planner_provider_cache_creation_input_tokens": 0,
        "total_llm_route_planner_provider_cache_read_input_tokens": 0,
        "total_llm_route_planner_provider_total_tokens": 0,
        "n_rows_with_quality_controls": 0,
        "n_quality_control_fields": 0,
        "quality_control_fields": (),
        "quality_control_resource_contract_ids": (),
        "quality_control_response_validation_signals": (),
        "quality_control_stop_conditions": (),
        "all_ok": False,
    }
    if source_dir is None:
        return zero_summary
    manifest_path = source_dir / "formalization_gap_planner_evaluation_manifest.json"
    payload = _read_json_no_error(manifest_path)
    rows = tuple(
        row for row in payload.get("rows", []) if isinstance(row, dict)
    )
    return {
        **zero_summary,
        "requested": True,
        "manifest_path": str(manifest_path),
        "n_evaluation_rows": int(payload.get("n_evaluation_rows", len(rows)) or 0),
        "n_evaluation_row_schema_valid": int(
            payload.get("n_evaluation_row_schema_valid", 0) or 0
        ),
        "n_evaluation_row_schema_invalid": int(
            payload.get("n_evaluation_row_schema_invalid", 0) or 0
        ),
        "n_matched_ground_truth": int(payload.get("n_matched_ground_truth", 0) or 0),
        "n_missing_ground_truth": int(payload.get("n_missing_ground_truth", 0) or 0),
        "n_alignment_contract_ok": int(
            payload.get("n_alignment_contract_ok", 0) or 0
        ),
        "n_feedback_loop_ready": int(payload.get("n_feedback_loop_ready", 0) or 0),
        "n_unaligned_primitives": int(payload.get("n_unaligned_primitives", 0) or 0),
        "n_minimal_delta_route_options": int(
            payload.get(
                "n_minimal_delta_route_options",
                sum(
                    int(row.get("minimal_delta_route_option_count", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "mean_minimal_delta_selected_route_cost": _manifest_float_or_row_mean(
            payload,
            rows,
            "mean_minimal_delta_selected_route_cost",
            "minimal_delta_selected_route_cost",
            required_bool_field="minimal_delta_cost_graph_present",
        ),
        "n_kernel_verified_ground_truth": int(
            payload.get(
                "n_kernel_verified_ground_truth",
                sum(
                    1
                    for row in rows
                    if row.get("kernel_verified_ground_truth") is True
                ),
            )
            or 0
        ),
        "n_kernel_verification_witnesses": int(
            payload.get(
                "n_kernel_verification_witnesses",
                sum(
                    len(
                        row.get("kernel_verification_witnesses", [])
                        if isinstance(row.get("kernel_verification_witnesses", []), list)
                        else []
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_kernel_verified_ground_truth_with_witnesses": int(
            payload.get(
                "n_kernel_verified_ground_truth_with_witnesses",
                sum(
                    1
                    for row in rows
                    if row.get("kernel_verified_ground_truth") is True
                    and isinstance(row.get("kernel_verification_witnesses", []), list)
                    and row.get("kernel_verification_witnesses", [])
                ),
            )
            or 0
        ),
        "mean_alignment_coverage": _manifest_float_or_row_mean(
            payload,
            rows,
            "mean_alignment_coverage",
            "alignment_coverage",
        ),
        "n_realization_missing_selected_formal_primitives": _manifest_count_or_rows(
            payload,
            rows,
            "n_realization_missing_selected_formal_primitives",
            "realization_missing_selected_formal_primitives",
        ),
        "n_realization_missing_delta_alignment_primitives": _manifest_count_or_rows(
            payload,
            rows,
            "n_realization_missing_delta_alignment_primitives",
            "realization_missing_delta_alignment_primitives",
        ),
        "n_rows_with_incomplete_cost_hint_baseline_coverage": int(
            payload.get(
                "n_rows_with_incomplete_cost_hint_baseline_coverage",
                sum(
                    1
                    for row in rows
                    if row.get("realization_cost_hint_baseline_coverage_complete")
                    is False
                ),
            )
            or 0
        ),
        "n_realization_cost_hint_baseline_primitives": _manifest_count_or_rows(
            payload,
            rows,
            "n_realization_cost_hint_baseline_primitives",
            "realization_cost_hint_baseline_primitives",
        ),
        "n_realization_omitted_cost_hint_primitives": _manifest_count_or_rows(
            payload,
            rows,
            "n_realization_omitted_cost_hint_primitives",
            "realization_omitted_cost_hint_primitives",
        ),
        "realization_missing_selected_formal_primitives": _manifest_values_or_rows(
            payload,
            rows,
            "realization_missing_selected_formal_primitives",
        ),
        "realization_missing_delta_alignment_primitives": _manifest_values_or_rows(
            payload,
            rows,
            "realization_missing_delta_alignment_primitives",
        ),
        "realization_cost_hint_baseline_primitives": _manifest_values_or_rows(
            payload,
            rows,
            "realization_cost_hint_baseline_primitives",
        ),
        "realization_omitted_cost_hint_primitives": _manifest_values_or_rows(
            payload,
            rows,
            "realization_omitted_cost_hint_primitives",
        ),
        "n_rows_with_llm_route_planner_residual_goal_contexts": int(
            payload.get(
                "n_rows_with_llm_route_planner_residual_goal_contexts",
                sum(
                    1
                    for row in rows
                    if int(
                        row.get(
                            "llm_route_planner_residual_goal_context_count",
                            0,
                        )
                        or 0
                    )
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goal_contexts": int(
            payload.get(
                "n_llm_route_planner_residual_goal_contexts",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_residual_goal_context_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goal_context_source_refs": int(
            payload.get(
                "n_llm_route_planner_residual_goal_context_source_refs",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_residual_goal_context_source_ref_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goal_context_provenance_values": int(
            payload.get(
                "n_llm_route_planner_residual_goal_context_provenance_values",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_residual_goal_context_provenance_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goals_with_context": int(
            payload.get(
                "n_llm_route_planner_residual_goals_with_context",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_residual_goals_with_context_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goals_without_context": _manifest_count_or_rows(
            payload,
            rows,
            "n_llm_route_planner_residual_goals_without_context",
            "llm_route_planner_residual_goals_without_context",
        ),
        "n_rows_with_llm_route_planner_route_option_selection_brief": int(
            payload.get(
                "n_rows_with_llm_route_planner_route_option_selection_brief",
                sum(
                    1
                    for row in rows
                    if row.get(
                        "llm_route_planner_route_option_selection_brief_present"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_candidate_options": int(
            payload.get(
                "n_llm_route_planner_route_option_selection_candidate_options",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_candidate_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_candidate_primitives": int(
            payload.get(
                "n_llm_route_planner_route_option_selection_candidate_primitives",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_candidate_primitive_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_candidates_with_residual_goals": int(
            payload.get(
                "n_llm_route_planner_route_option_selection_candidates_with_residual_goals",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_candidates_with_residual_goals",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_candidate_residual_goals": int(
            payload.get(
                "n_llm_route_planner_route_option_selection_candidate_residual_goals",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_candidate_residual_goal_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_residual_goals": int(
            payload.get(
                "n_llm_route_planner_route_option_selection_lower_bound_residual_goals",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_lower_bound_residual_goal_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_rows_with_llm_route_planner_route_option_selected_route_option": int(
            payload.get(
                "n_rows_with_llm_route_planner_route_option_selected_route_option",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals": int(
            payload.get(
                "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selected_matches_lower_bound": int(
            payload.get(
                "n_llm_route_planner_route_option_selected_matches_lower_bound",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and row.get(
                        "llm_route_planner_route_option_selected_matches_lower_bound"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selected_mismatches_lower_bound": int(
            payload.get(
                "n_llm_route_planner_route_option_selected_mismatches_lower_bound",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and str(
                        row.get(
                            "llm_route_planner_route_option_selection_lower_bound_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and row.get(
                        "llm_route_planner_route_option_selected_matches_lower_bound"
                    )
                    is not True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selected_matches_minimal_delta": int(
            payload.get(
                "n_llm_route_planner_route_option_selected_matches_minimal_delta",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and row.get(
                        "llm_route_planner_route_option_selected_matches_minimal_delta"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selected_mismatches_minimal_delta": int(
            payload.get(
                "n_llm_route_planner_route_option_selected_mismatches_minimal_delta",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and str(row.get("minimal_delta_selected_route_option_id", "") or "").strip()
                    and row.get(
                        "llm_route_planner_route_option_selected_matches_minimal_delta"
                    )
                    is not True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": int(
            payload.get(
                "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta",
                sum(
                    1
                    for row in rows
                    if row.get(
                        "llm_route_planner_route_option_selection_brief_present"
                    )
                    is True
                    and row.get(
                        "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta": int(
            payload.get(
                "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta",
                sum(
                    1
                    for row in rows
                    if row.get(
                        "llm_route_planner_route_option_selection_brief_present"
                    )
                    is True
                    and row.get(
                        "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
                    )
                    is not True
                ),
            )
            or 0
        ),
        "n_rows_with_llm_route_planner_route_adoption_status": int(
            payload.get(
                "n_rows_with_llm_route_planner_route_adoption_status",
                sum(
                    1
                    for row in rows
                    if str(row.get("llm_route_planner_route_adoption_status", "")).strip()
                ),
            )
            or 0
        ),
        "n_rows_ready_for_route_adoption": int(
            payload.get(
                "n_rows_ready_for_route_adoption",
                _row_count_with_value(
                    rows,
                    "llm_route_planner_route_adoption_status",
                    "READY_FOR_STANDALONE_REPLAY",
                ),
            )
            or 0
        ),
        "n_rows_pending_refinement_before_route_adoption": int(
            payload.get(
                "n_rows_pending_refinement_before_route_adoption",
                _row_count_with_value(
                    rows,
                    "llm_route_planner_route_adoption_status",
                    "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION",
                ),
            )
            or 0
        ),
        "n_rows_awaiting_llm_route_planner_response": int(
            payload.get(
                "n_rows_awaiting_llm_route_planner_response",
                _row_count_with_value(
                    rows,
                    "llm_route_planner_route_adoption_status",
                    "AWAITING_LLM_ROUTE_PLANNER_RESPONSE",
                ),
            )
            or 0
        ),
        "n_rows_rejected_llm_route_plan": int(
            payload.get(
                "n_rows_rejected_llm_route_plan",
                _row_count_with_value(
                    rows,
                    "llm_route_planner_route_adoption_status",
                    "REJECTED_LLM_ROUTE_PLAN",
                ),
            )
            or 0
        ),
        "n_llm_route_adoption_blockers": _manifest_count_or_rows(
            payload,
            rows,
            "n_llm_route_adoption_blockers",
            "llm_route_planner_route_adoption_blockers",
        ),
        "n_llm_route_adoption_pending_quality_control_blockers": int(
            payload.get(
                "n_llm_route_adoption_pending_quality_control_blockers",
                sum(
                    1
                    for row in rows
                    if "quality_control_obligations_pending"
                    in _str_tuple(
                        row.get("llm_route_planner_route_adoption_blockers", [])
                    )
                ),
            )
            or 0
        ),
        "n_llm_route_adoption_pending_source_grounding_blockers": int(
            payload.get(
                "n_llm_route_adoption_pending_source_grounding_blockers",
                sum(
                    1
                    for row in rows
                    if "source_grounding_obligations_pending"
                    in _str_tuple(
                        row.get("llm_route_planner_route_adoption_blockers", [])
                    )
                ),
            )
            or 0
        ),
        "n_llm_route_adoption_pending_formal_attempt_queue_blockers": int(
            payload.get(
                "n_llm_route_adoption_pending_formal_attempt_queue_blockers",
                sum(
                    1
                    for row in rows
                    if ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE
                    in _str_tuple(
                        row.get("llm_route_planner_route_adoption_blockers", [])
                    )
                ),
            )
            or 0
        ),
        "n_rows_with_llm_route_planner_route_adoption_preconditions": int(
            payload.get(
                "n_rows_with_llm_route_planner_route_adoption_preconditions",
                sum(
                    1
                    for row in rows
                    if row.get(
                        "llm_route_planner_route_adoption_precondition_present"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions": int(
            payload.get(
                "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions",
                sum(
                    1
                    for row in rows
                    if row.get(
                        "llm_route_planner_route_adoption_precondition_blocked_before_response"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_adoption_precondition_known_blockers": (
            _manifest_count_or_rows(
                payload,
                rows,
                "n_llm_route_planner_route_adoption_precondition_known_blockers",
                "llm_route_planner_route_adoption_precondition_known_blockers",
            )
        ),
        "n_llm_route_planner_route_adoption_precondition_required_response_fields": (
            _manifest_count_or_rows(
                payload,
                rows,
                "n_llm_route_planner_route_adoption_precondition_required_response_fields",
                "llm_route_planner_route_adoption_precondition_required_response_fields",
            )
        ),
        "n_llm_route_planner_route_adoption_precondition_target_primitives": (
            _manifest_count_or_rows(
                payload,
                rows,
                "n_llm_route_planner_route_adoption_precondition_target_primitives",
                "llm_route_planner_route_adoption_precondition_target_primitives",
            )
        ),
        "llm_route_planner_route_adoption_precondition_known_blockers": (
            _manifest_values_or_rows(
                payload,
                rows,
                "llm_route_planner_route_adoption_precondition_known_blockers",
            )
        ),
        "llm_route_planner_route_adoption_precondition_required_response_fields": (
            _manifest_values_or_rows(
                payload,
                rows,
                "llm_route_planner_route_adoption_precondition_required_response_fields",
            )
        ),
        "llm_route_planner_route_adoption_precondition_target_primitives": (
            _manifest_values_or_rows(
                payload,
                rows,
                "llm_route_planner_route_adoption_precondition_target_primitives",
            )
        ),
        "llm_route_adoption_blockers": _manifest_values_or_row_field(
            payload,
            rows,
            "llm_route_adoption_blockers",
            "llm_route_planner_route_adoption_blockers",
        ),
        "llm_route_adoption_blocker_counts": _llm_route_adoption_blocker_counts(
            payload,
            rows,
        ),
        "llm_route_adoption_status_counts": _llm_route_adoption_status_counts(
            payload,
            rows,
        ),
        "evaluation_by_llm_route_adoption_blocker": (
            _llm_route_adoption_blocker_summary(payload, rows)
        ),
        "llm_route_planner_provider_usage_summary": (
            _dict_value(payload, "llm_route_planner_provider_usage_summary")
        ),
        "n_rows_with_llm_route_planner_provider_usage": int(
            payload.get(
                "n_rows_with_llm_route_planner_provider_usage",
                sum(
                    1
                    for row in rows
                    if row.get("llm_route_planner_has_provider_usage") is True
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_input_tokens": int(
            payload.get(
                "total_llm_route_planner_provider_input_tokens",
                sum(
                    int(row.get("llm_route_planner_provider_input_tokens", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_output_tokens": int(
            payload.get(
                "total_llm_route_planner_provider_output_tokens",
                sum(
                    int(row.get("llm_route_planner_provider_output_tokens", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_cache_creation_input_tokens": int(
            payload.get(
                "total_llm_route_planner_provider_cache_creation_input_tokens",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_provider_cache_creation_input_tokens",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_cache_read_input_tokens": int(
            payload.get(
                "total_llm_route_planner_provider_cache_read_input_tokens",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_provider_cache_read_input_tokens",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_total_tokens": int(
            payload.get(
                "total_llm_route_planner_provider_total_tokens",
                sum(
                    int(row.get("llm_route_planner_provider_total_tokens", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "n_rows_with_quality_controls": int(
            payload.get(
                "n_rows_with_quality_controls",
                sum(1 for row in rows if row.get("quality_controls_present") is True),
            )
            or 0
        ),
        "n_quality_control_fields": _manifest_count_or_rows(
            payload,
            rows,
            "n_quality_control_fields",
            "quality_control_fields",
        ),
        "quality_control_fields": _manifest_values_or_rows(
            payload,
            rows,
            "quality_control_fields",
        ),
        "quality_control_resource_contract_ids": _manifest_values_or_rows(
            payload,
            rows,
            "quality_control_resource_contract_ids",
        ),
        "quality_control_response_validation_signals": _manifest_values_or_rows(
            payload,
            rows,
            "quality_control_response_validation_signals",
        ),
        "quality_control_stop_conditions": _manifest_values_or_rows(
            payload,
            rows,
            "quality_control_stop_conditions",
        ),
        "all_ok": bool(payload.get("all_ok", False)),
    }


def _llm_route_planner_manifest_summary(source_dir: Path | None) -> dict[str, object]:
    zero_summary: dict[str, object] = {
        "requested": False,
        "manifest_path": "",
        "jsonl_path": "",
        "provider_execution_mode": "",
        "invoke_provider": False,
        "response_json_supplied": False,
        "static_response_json_supplied": False,
        "generator_backend_supplied": False,
        "live_provider_backend_requested": False,
        "static_generator_backend_requested": False,
        "provider_generation_requested": False,
        "n_request_packets": 0,
        "n_target_theorem_context_packets": 0,
        "n_requests_with_context_packet_inventory": 0,
        "n_request_context_inventory_total_rows": 0,
        "n_rows_with_context_packet_inventory": 0,
        "n_rows_with_target_context_summary": 0,
        "n_target_context_summary_proof_source_refs": 0,
        "n_rows_with_target_context_summary_proof_source_refs": 0,
        "n_target_context_summary_proof_source_ref_support_rows": 0,
        "n_rows_with_target_context_summary_proof_source_ref_support_rows": 0,
        "n_target_context_summary_proof_source_ref_support_source_fields": 0,
        "n_requests_with_available_source_snippets": 0,
        "n_request_available_source_snippets": 0,
        "n_requests_with_target_intake_rows": 0,
        "n_request_target_intake_rows": 0,
        "n_requests_with_current_goal_plan_rows": 0,
        "n_request_current_goal_plan_rows": 0,
        "n_requests_with_route_adoption_preconditions": 0,
        "n_request_route_adoption_precondition_known_blockers": 0,
        "n_request_route_adoption_precondition_required_response_fields": 0,
        "n_request_route_adoption_precondition_target_primitives": 0,
        "n_requests_with_quality_control_obligation_inventory": 0,
        "n_requests_with_pending_quality_control_obligation_inventory": 0,
        "n_request_quality_control_obligation_fields": 0,
        "n_request_quality_control_obligation_values": 0,
        "n_request_pending_quality_control_fields": 0,
        "n_request_pending_quality_control_values": 0,
        "n_request_discharged_quality_control_fields": 0,
        "n_request_discharged_quality_control_values": 0,
        "n_requests_with_source_grounding_rows": 0,
        "n_request_source_grounding_rows": 0,
        "n_requests_with_source_grounding_obligation_inventory": 0,
        "n_requests_with_pending_source_grounding_obligation_inventory": 0,
        "n_request_source_grounding_unresolved_rows": 0,
        "n_request_residual_source_grounding_unresolved_rows": 0,
        "n_request_residual_goals": 0,
        "n_requests_with_residual_goal_contexts": 0,
        "n_request_residual_goal_contexts": 0,
        "n_request_context_residual_goal_contexts": 0,
        "n_request_inventory_residual_goal_contexts": 0,
        "n_requests_with_resource_feedback_readiness_summary": 0,
        "n_request_resource_feedback_readiness_rows": 0,
        "n_request_resource_feedback_reuse_ready_rows": 0,
        "n_requests_with_formal_source_retrieval_summary": 0,
        "n_request_formal_source_retrieval_metadata_rows": 0,
        "n_request_formal_source_semantic_rerank_rows": 0,
        "n_requests_with_formal_attempt_feedback_summary": 0,
        "n_request_formal_attempt_feedback_contexts": 0,
        "n_request_formal_attempt_feedback_residual_goals": 0,
        "n_request_formal_attempt_feedback_failed_statuses": 0,
        "n_feedback_loop_summary_prior_llm_route_planner_hook_traces": 0,
        "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces": 0,
        "n_feedback_loop_summary_interactive_resource_requests": 0,
        "n_feedback_loop_summary_interactive_resource_request_dispatch_summaries": 0,
        "n_feedback_loop_summary_interactive_resource_request_execution_commands": 0,
        "n_requests_with_component_resource_registry_context": 0,
        "n_component_resource_registry_resources_in_prompt": 0,
        "n_component_resource_registry_contracts_in_prompt": 0,
        "n_requests_with_source_theorem_semantic_primitive_bridge_context": 0,
        "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt": 0,
        "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt": 0,
        "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context": 0,
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt": 0,
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt": 0,
        "n_requests_with_source_theorem_formal_environment_bridge_context": 0,
        "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt": 0,
        "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt": 0,
        "n_requests_with_exact_source_theorem_proof_body_executor_context": 0,
        "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt": 0,
        "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt": 0,
        "n_requests_with_source_theorem_semantic_primitive_rows": 0,
        "n_request_source_theorem_semantic_primitive_rows": 0,
        "n_requests_with_proof_body_semantic_primitive_work_order_rows": 0,
        "n_request_proof_body_semantic_primitive_work_order_rows": 0,
        "n_requests_with_source_theorem_formal_environment_rows": 0,
        "n_request_source_theorem_formal_environment_rows": 0,
        "n_requests_with_source_theorem_proof_body_execution_result_rows": 0,
        "n_request_source_theorem_proof_body_execution_result_rows": 0,
        "n_requests_with_agentic_proof_execution_materializer_rows": 0,
        "n_request_agentic_proof_execution_materializer_rows": 0,
        "n_requests_with_agentic_proof_execution_artifact_verifier_rows": 0,
        "n_request_agentic_proof_execution_artifact_verifier_rows": 0,
        "n_requests_with_agentic_proof_source_theorem_promotion_rows": 0,
        "n_request_agentic_proof_source_theorem_promotion_rows": 0,
        "n_requests_with_proof_execution_feedback_summary": 0,
        "n_request_proof_execution_feedback_rows": 0,
        "n_request_proof_execution_unsupported_target_prover_rows": 0,
        "n_requests_with_patch_rerun_residual_obligation_summary": 0,
        "n_request_patch_rerun_residual_obligation_rows": 0,
        "n_request_patch_rerun_residual_obligation_source_discovery_needed": 0,
        "n_requests_with_patch_rerun_residual_followup_queue_summary": 0,
        "n_request_patch_rerun_residual_followup_queue_rows": 0,
        "n_request_patch_rerun_residual_followup_queue_ready": 0,
        "n_request_patch_rerun_residual_followup_queue_source_discovery": 0,
        "n_requests_with_agentic_proof_strategy_plan_summary": 0,
        "n_request_agentic_proof_strategy_plan_rows": 0,
        "n_request_agentic_proof_strategy_plan_ready": 0,
        "n_request_agentic_proof_strategy_plan_source_discovery_cache_items": 0,
        "n_rows": 0,
        "n_response_present": 0,
        "n_response_contract_ok": 0,
        "n_provider_failures": 0,
        "prompt_token_budget_summary": {},
        "n_prompt_token_budget_rows": 0,
        "max_estimated_prompt_input_tokens": 0,
        "prompt_token_budget_preflight_errors": (),
        "n_prompt_token_budget_preflight_blocked": 0,
        "estimated_prompt_input_tokens": 0,
        "estimated_prompt_max_output_tokens": 0,
        "estimated_prompt_total_token_budget": 0,
        "provider_usage_summary": {},
        "n_rows_with_provider_usage": 0,
        "total_provider_input_tokens": 0,
        "total_provider_output_tokens": 0,
        "total_provider_cache_creation_input_tokens": 0,
        "total_provider_cache_read_input_tokens": 0,
        "total_provider_total_tokens": 0,
        "n_generated_responses_model_tier_escalated": 0,
        "n_generated_responses_haiku_to_sonnet_escalated": 0,
        "n_repair_attempt_ledger_model_tier_escalations": 0,
        "n_model_tier_decision_ledger_rows": 0,
        "n_model_tier_decision_ledger_rows_with_escalation": 0,
        "n_model_tier_decision_ledger_provider_failure_rows": 0,
        "n_rows_with_model_tier_escalation": 0,
        "n_requests_with_model_tier_decision_evidence": 0,
        "n_request_model_tier_decision_auto_haiku_bounded": 0,
        "n_request_model_tier_decision_auto_sonnet_triggered": 0,
        "n_request_model_tier_decision_operator_override": 0,
        "n_request_model_tier_decision_sonnet_triggers": 0,
        "n_request_model_tier_decision_route_planning_evidence_gaps": 0,
        "n_request_model_tier_decision_route_planning_evidence_gap_sonnet_triggers": 0,
        "n_request_model_tier_decision_resource_feedback_readiness_rows": 0,
        "n_request_model_tier_decision_resource_feedback_reuse_ready_rows": 0,
        "n_request_model_tier_decision_resource_feedback_sonnet_triggers": 0,
        "n_request_model_tier_decision_formal_attempt_feedback_contexts": 0,
        "n_request_model_tier_decision_formal_attempt_feedback_residual_goals": 0,
        "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses": 0,
        "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers": 0,
        "n_request_model_tier_decision_evidence_invalid": 0,
        "by_request_model_tier_decision_basis": {},
        "n_request_target_prover_families": 0,
        "by_request_target_prover_family": {},
        "n_request_model_tier_haiku": 0,
        "n_request_model_tier_sonnet": 0,
        "n_request_model_tier_opus": 0,
        "by_request_model_tier": {},
        "n_requests_with_library_alignment_summary": 0,
        "n_request_library_alignment_primitives": 0,
        "n_request_library_alignment_reuse_ready_primitives": 0,
        "n_request_library_alignment_wrapper_primitives": 0,
        "n_request_library_alignment_bridge_primitives": 0,
        "n_request_library_alignment_source_port_primitives": 0,
        "n_request_library_alignment_new_definition_primitives": 0,
        "n_request_library_alignment_new_theory_primitives": 0,
        "n_request_library_alignment_unknown_primitives": 0,
        "n_request_library_alignment_bridge_or_harder_primitives": 0,
        "n_request_library_alignment_target_compatible_reuse_declarations": 0,
        "n_request_library_alignment_route_options": 0,
        "n_request_library_alignment_route_option_primitives": 0,
        "n_request_library_alignment_route_option_bridge_or_harder_primitives": 0,
        "n_request_library_alignment_route_option_target_compatible_reuse_declarations": 0,
        "total_request_library_alignment_route_option_minimum_base_cost": 0.0,
        "by_request_library_alignment_delta_class": {},
        "by_request_library_alignment_minimum_coverage_bucket": {},
        "n_requests_with_route_option_selection_brief": 0,
        "n_request_route_option_selection_candidate_options": 0,
        "n_request_route_option_selection_candidate_primitives": 0,
        "n_request_route_option_selection_candidates_with_residual_goals": 0,
        "n_request_route_option_selection_candidate_residual_goals": 0,
        "n_request_route_option_selection_lower_bound_options": 0,
        "n_request_route_option_selection_lower_bound_residual_goals": 0,
        "n_informal_knowledge_dag_nodes": 0,
        "n_formal_realization_dag_nodes": 0,
        "legacy_response_field_aliases": {},
        "n_lean_realization_dag_nodes": 0,
        "n_route_alignment_edges": 0,
        "n_search_requests": 0,
        "n_planner_next_actions": 0,
        "n_rows_with_planner_next_actions": 0,
        "n_rows_with_residual_goal_contexts": 0,
        "n_row_residual_goal_contexts": 0,
        "n_uncertainty_flags": 0,
        "n_residual_interpretations": 0,
        "n_source_snippets": 0,
        "n_rows_with_source_snippets": 0,
        "n_formal_attempt_queue_items": 0,
        "n_rows_with_formal_attempt_queue": 0,
        "n_delta_action_witness_required_primitives": 0,
        "n_delta_action_witness_missing_primitives": 0,
        "n_rows_with_delta_action_witness_obligations": 0,
        "n_rows_with_complete_delta_action_witness": 0,
        "n_rows_with_route_adoption_preconditions": 0,
        "n_row_route_adoption_precondition_known_blockers": 0,
        "n_row_route_adoption_precondition_target_primitives": 0,
        "n_accepted_route_plans": 0,
        "n_accepted_with_formal_attempt_queue": 0,
        "n_route_adoption_ready": 0,
        "n_route_adoption_pending_refinement": 0,
        "n_route_adoption_awaiting_llm_response": 0,
        "n_route_adoption_rejected": 0,
        "n_route_adoption_pending_formal_gap_boundary_blockers": 0,
        "n_route_adoption_pending_formal_attempt_queue_blockers": 0,
        "n_route_adoption_blockers": 0,
        "route_adoption_blockers": (),
        "route_adoption_blocker_counts": {},
        "by_route_adoption_status": {},
        "by_route_adoption_blocker": {},
        "standalone_replay_gate": {},
        "standalone_replay_gate_ok": False,
        "n_standalone_replay_route_candidates": 0,
        "n_standalone_replay_adoptable_route_candidates": 0,
        "n_standalone_replay_blocked_route_candidates": 0,
        "standalone_replay_gate_blockers": (),
        "n_row_schema_valid": 0,
        "n_row_schema_invalid": 0,
        "all_ok": False,
    }
    if source_dir is None:
        return zero_summary
    manifest_path = source_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
    rows_path = source_dir / "formalization_gap_planner_llm_route_planner.jsonl"
    payload = _read_json_no_error(manifest_path)
    rows = _read_jsonl_dict_rows_no_error(rows_path)
    request_packets = _dict_tuple(payload.get("request_packets", []))
    request_model_tier_counts = Counter(
        str(packet.get("model_tier", "") or "unknown") for packet in request_packets
    )
    request_target_prover_family_counts = Counter(
        _target_prover_key(packet.get("target_prover_family", "")) or "unknown"
        for packet in request_packets
    )
    decision_basis_counts = _llm_route_planner_decision_basis_counts(request_packets)
    model_tier_decision_evidence_rows = tuple(
        _dict_value(packet, "model_tier_decision_evidence")
        for packet in request_packets
    )
    request_route_adoption_preconditions = tuple(
        _dict_value(
            _dict_value(packet, "context_packet"),
            "route_adoption_preconditions",
        )
        for packet in request_packets
    )
    formal_source_retrieval_summaries = tuple(
        _dict_value(
            _dict_value(packet, "context_packet"),
            "formal_source_retrieval_summary",
        )
        for packet in request_packets
    )
    row_route_adoption_preconditions = tuple(
        _dict_value(row, "route_adoption_preconditions") for row in rows
    )
    row_target_context_summaries = tuple(
        _dict_value(row, "target_context_summary") for row in rows
    )
    library_alignment_summaries = tuple(
        _dict_value(_dict_value(packet, "context_packet"), "library_alignment_summary")
        for packet in request_packets
    )
    library_alignment_rows = tuple(
        row
        for summary in library_alignment_summaries
        for row in _dict_tuple(summary.get("primitive_alignment", []))
    )
    library_alignment_route_option_rows = tuple(
        row
        for summary in library_alignment_summaries
        for row in _dict_tuple(summary.get("route_option_alignment", []))
    )
    route_option_selection_briefs = tuple(
        _dict_value(
            _dict_value(packet, "context_packet"),
            "route_option_selection_brief",
        )
        for packet in request_packets
    )
    library_delta_class_counts = Counter(
        str(row.get("library_delta_class", "") or "unknown")
        for row in library_alignment_rows
    )
    library_minimum_bucket_counts = Counter(
        str(row.get("minimum_coverage_bucket", "") or "unknown")
        for row in library_alignment_rows
    )
    acceptance_status_counts = Counter(
        str(row.get("acceptance_status", "") or "unknown") for row in rows
    )
    route_adoption_status_counts = _llm_route_planner_status_counts(payload, rows)
    route_adoption_blocker_counts = _llm_route_planner_blocker_counts(payload, rows)
    standalone_replay_gate = _dict_value(payload, "standalone_replay_gate")
    model_tier_decision_ledger = _dict_tuple(
        payload.get("model_tier_decision_ledger", [])
    )
    return {
        **zero_summary,
        "requested": True,
        "manifest_path": str(manifest_path),
        "jsonl_path": str(rows_path),
        "provider_execution_mode": str(
            payload.get("provider_execution_mode", "") or ""
        ),
        "invoke_provider": bool(payload.get("invoke_provider", False)),
        "response_json_supplied": bool(payload.get("response_json_supplied", False)),
        "static_response_json_supplied": bool(
            payload.get("static_response_json_supplied", False)
        ),
        "generator_backend_supplied": bool(
            payload.get("generator_backend_supplied", False)
        ),
        "live_provider_backend_requested": bool(
            payload.get("live_provider_backend_requested", False)
        ),
        "static_generator_backend_requested": bool(
            payload.get("static_generator_backend_requested", False)
        ),
        "provider_generation_requested": bool(
            payload.get("provider_generation_requested", False)
        ),
        "prompt_token_budget_summary": _dict_value(
            payload,
            "prompt_token_budget_summary",
        ),
        "n_prompt_token_budget_rows": int(
            payload.get("n_prompt_token_budget_rows", 0) or 0
        ),
        "max_estimated_prompt_input_tokens": int(
            payload.get("max_estimated_prompt_input_tokens", 0) or 0
        ),
        "prompt_token_budget_preflight_errors": _dict_tuple(
            payload.get("prompt_token_budget_preflight_errors", [])
        ),
        "n_prompt_token_budget_preflight_blocked": int(
            payload.get("n_prompt_token_budget_preflight_blocked", 0) or 0
        ),
        "estimated_prompt_input_tokens": int(
            payload.get("estimated_prompt_input_tokens", 0) or 0
        ),
        "estimated_prompt_max_output_tokens": int(
            payload.get("estimated_prompt_max_output_tokens", 0) or 0
        ),
        "estimated_prompt_total_token_budget": int(
            payload.get("estimated_prompt_total_token_budget", 0) or 0
        ),
        "n_request_packets": int(
            payload.get("n_request_packets", len(rows)) or 0
        ),
        "n_target_theorem_context_packets": int(
            payload.get("n_target_theorem_context_packets", 0) or 0
        ),
        "n_requests_with_context_packet_inventory": int(
            payload.get("n_requests_with_context_packet_inventory", 0) or 0
        ),
        "n_request_context_inventory_total_rows": int(
            payload.get("n_request_context_inventory_total_rows", 0) or 0
        ),
        "n_rows_with_context_packet_inventory": int(
            payload.get(
                "n_rows_with_context_packet_inventory",
                sum(1 for row in rows if row.get("context_packet_inventory")),
            )
            or 0
        ),
        "n_rows_with_target_context_summary": int(
            payload.get(
                "n_rows_with_target_context_summary",
                sum(1 for summary in row_target_context_summaries if summary),
            )
            or 0
        ),
        "n_target_context_summary_proof_source_refs": int(
            payload.get(
                "n_target_context_summary_proof_source_refs",
                sum(
                    len(_target_context_summary_proof_source_refs(summary))
                    for summary in row_target_context_summaries
                ),
            )
            or 0
        ),
        "n_rows_with_target_context_summary_proof_source_refs": int(
            payload.get(
                "n_rows_with_target_context_summary_proof_source_refs",
                sum(
                    1
                    for summary in row_target_context_summaries
                    if _target_context_summary_proof_source_refs(summary)
                ),
            )
            or 0
        ),
        "n_target_context_summary_proof_source_ref_support_rows": int(
            payload.get(
                "n_target_context_summary_proof_source_ref_support_rows",
                sum(
                    len(
                        _target_context_summary_proof_source_ref_support_rows(
                            summary
                        )
                    )
                    for summary in row_target_context_summaries
                ),
            )
            or 0
        ),
        "n_rows_with_target_context_summary_proof_source_ref_support_rows": int(
            payload.get(
                "n_rows_with_target_context_summary_proof_source_ref_support_rows",
                sum(
                    1
                    for summary in row_target_context_summaries
                    if _target_context_summary_proof_source_ref_support_rows(summary)
                ),
            )
            or 0
        ),
        "n_target_context_summary_proof_source_ref_support_source_fields": int(
            payload.get(
                "n_target_context_summary_proof_source_ref_support_source_fields",
                sum(
                    _target_context_summary_proof_source_ref_support_source_field_count(
                        summary
                    )
                    for summary in row_target_context_summaries
                ),
            )
            or 0
        ),
        "n_requests_with_available_source_snippets": int(
            payload.get(
                "n_requests_with_available_source_snippets",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "available_source_snippets",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_available_source_snippets": int(
            payload.get(
                "n_request_available_source_snippets",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "available_source_snippets",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_target_intake_rows": int(
            payload.get(
                "n_requests_with_target_intake_rows",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "target_intake_rows",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_target_intake_rows": int(
            payload.get(
                "n_request_target_intake_rows",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "target_intake_rows",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_current_goal_plan_rows": int(
            payload.get(
                "n_requests_with_current_goal_plan_rows",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "current_goal_plan_rows",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_current_goal_plan_rows": int(
            payload.get(
                "n_request_current_goal_plan_rows",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "current_goal_plan_rows",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_route_adoption_preconditions": int(
            payload.get(
                "n_requests_with_route_adoption_preconditions",
                sum(1 for value in request_route_adoption_preconditions if value),
            )
            or 0
        ),
        "n_request_route_adoption_precondition_known_blockers": int(
            payload.get(
                "n_request_route_adoption_precondition_known_blockers",
                sum(
                    int(
                        value.get(
                            "n_known_pre_response_blockers",
                            len(_str_tuple(value.get("known_pre_response_blockers", []))),
                        )
                        or 0
                    )
                    for value in request_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_request_route_adoption_precondition_required_response_fields": int(
            payload.get(
                "n_request_route_adoption_precondition_required_response_fields",
                sum(
                    len(_str_tuple(value.get("response_required_fields", [])))
                    for value in request_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_request_route_adoption_precondition_target_primitives": int(
            payload.get(
                "n_request_route_adoption_precondition_target_primitives",
                sum(
                    len(_str_tuple(value.get("target_primitives", [])))
                    for value in request_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_requests_with_quality_control_obligation_inventory": int(
            payload.get(
                "n_requests_with_quality_control_obligation_inventory",
                0,
            )
            or 0
        ),
        "n_requests_with_pending_quality_control_obligation_inventory": int(
            payload.get(
                "n_requests_with_pending_quality_control_obligation_inventory",
                0,
            )
            or 0
        ),
        "n_request_quality_control_obligation_fields": int(
            payload.get("n_request_quality_control_obligation_fields", 0) or 0
        ),
        "n_request_quality_control_obligation_values": int(
            payload.get("n_request_quality_control_obligation_values", 0) or 0
        ),
        "n_request_pending_quality_control_fields": int(
            payload.get("n_request_pending_quality_control_fields", 0) or 0
        ),
        "n_request_pending_quality_control_values": int(
            payload.get("n_request_pending_quality_control_values", 0) or 0
        ),
        "n_request_discharged_quality_control_fields": int(
            payload.get("n_request_discharged_quality_control_fields", 0) or 0
        ),
        "n_request_discharged_quality_control_values": int(
            payload.get("n_request_discharged_quality_control_values", 0) or 0
        ),
        "n_requests_with_source_grounding_rows": int(
            payload.get("n_requests_with_source_grounding_rows", 0) or 0
        ),
        "n_request_source_grounding_rows": int(
            payload.get("n_request_source_grounding_rows", 0) or 0
        ),
        "n_requests_with_source_grounding_obligation_inventory": int(
            payload.get(
                "n_requests_with_source_grounding_obligation_inventory",
                0,
            )
            or 0
        ),
        "n_requests_with_pending_source_grounding_obligation_inventory": int(
            payload.get(
                "n_requests_with_pending_source_grounding_obligation_inventory",
                0,
            )
            or 0
        ),
        "n_request_source_grounding_unresolved_rows": int(
            payload.get("n_request_source_grounding_unresolved_rows", 0) or 0
        ),
        "n_request_residual_source_grounding_unresolved_rows": int(
            payload.get(
                "n_request_residual_source_grounding_unresolved_rows",
                0,
            )
            or 0
        ),
        "n_request_residual_goals": int(
            payload.get(
                "n_request_residual_goals",
                sum(
                    len(_str_tuple(packet.get("residual_goals", [])))
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_residual_goal_contexts": int(
            payload.get(
                "n_requests_with_residual_goal_contexts",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(packet.get("residual_goal_contexts", []))
                ),
            )
            or 0
        ),
        "n_request_residual_goal_contexts": int(
            payload.get(
                "n_request_residual_goal_contexts",
                sum(
                    len(_dict_tuple(packet.get("residual_goal_contexts", [])))
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_context_residual_goal_contexts": int(
            payload.get(
                "n_request_context_residual_goal_contexts",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "residual_goal_contexts",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_inventory_residual_goal_contexts": int(
            payload.get(
                "n_request_inventory_residual_goal_contexts",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "context_packet_inventory",
                        ).get("residual_goal_context_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_resource_feedback_readiness_summary": int(
            payload.get(
                "n_requests_with_resource_feedback_readiness_summary",
                sum(
                    1
                    for packet in request_packets
                    if int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "resource_feedback_readiness_summary",
                        ).get("total_count", 0)
                        or 0
                    )
                ),
            )
            or 0
        ),
        "n_request_resource_feedback_readiness_rows": int(
            payload.get(
                "n_request_resource_feedback_readiness_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "resource_feedback_readiness_summary",
                        ).get("total_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_resource_feedback_reuse_ready_rows": int(
            payload.get(
                "n_request_resource_feedback_reuse_ready_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "resource_feedback_readiness_summary",
                        ).get("reuse_ready_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_formal_source_retrieval_summary": int(
            payload.get(
                "n_requests_with_formal_source_retrieval_summary",
                sum(
                    1
                    for summary in formal_source_retrieval_summaries
                    if int(summary.get("total_count", 0) or 0)
                ),
            )
            or 0
        ),
        "n_request_formal_source_retrieval_metadata_rows": int(
            payload.get(
                "n_request_formal_source_retrieval_metadata_rows",
                sum(
                    int(summary.get("total_count", 0) or 0)
                    for summary in formal_source_retrieval_summaries
                ),
            )
            or 0
        ),
        "n_request_formal_source_semantic_rerank_rows": int(
            payload.get(
                "n_request_formal_source_semantic_rerank_rows",
                sum(
                    int(summary.get("semantic_rerank_count", 0) or 0)
                    for summary in formal_source_retrieval_summaries
                ),
            )
            or 0
        ),
        "n_requests_with_formal_attempt_feedback_summary": int(
            payload.get(
                "n_requests_with_formal_attempt_feedback_summary",
                sum(
                    1
                    for packet in request_packets
                    if int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "formal_attempt_feedback_summary",
                        ).get("total_count", 0)
                        or 0
                    )
                ),
            )
            or 0
        ),
        "n_request_formal_attempt_feedback_contexts": int(
            payload.get(
                "n_request_formal_attempt_feedback_contexts",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "formal_attempt_feedback_summary",
                        ).get("total_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_formal_attempt_feedback_residual_goals": int(
            payload.get(
                "n_request_formal_attempt_feedback_residual_goals",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "formal_attempt_feedback_summary",
                        ).get("residual_goal_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_formal_attempt_feedback_failed_statuses": int(
            payload.get(
                "n_request_formal_attempt_feedback_failed_statuses",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "formal_attempt_feedback_summary",
                        ).get("failed_status_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_feedback_loop_summary_prior_llm_route_planner_hook_traces": int(
            payload.get(
                "n_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
            or 0
        ),
        "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces": int(
            payload.get(
                "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
            or 0
        ),
        "n_feedback_loop_summary_interactive_resource_requests": int(
            payload.get("n_feedback_loop_summary_interactive_resource_requests", 0)
            or 0
        ),
        "n_feedback_loop_summary_interactive_resource_request_dispatch_summaries": int(
            payload.get(
                "n_feedback_loop_summary_interactive_resource_request_dispatch_summaries",
                0,
            )
            or 0
        ),
        "n_feedback_loop_summary_interactive_resource_request_execution_commands": int(
            payload.get(
                "n_feedback_loop_summary_interactive_resource_request_execution_commands",
                0,
            )
            or 0
        ),
        "n_requests_with_component_resource_registry_context": int(
            payload.get("n_requests_with_component_resource_registry_context", 0)
            or 0
        ),
        "n_component_resource_registry_resources_in_prompt": int(
            payload.get("n_component_resource_registry_resources_in_prompt", 0)
            or 0
        ),
        "n_component_resource_registry_contracts_in_prompt": int(
            payload.get("n_component_resource_registry_contracts_in_prompt", 0)
            or 0
        ),
        "n_requests_with_source_theorem_semantic_primitive_bridge_context": int(
            payload.get(
                "n_requests_with_source_theorem_semantic_primitive_bridge_context",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt",
                0,
            )
            or 0
        ),
        "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context": int(
            payload.get(
                "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt",
                0,
            )
            or 0
        ),
        "n_requests_with_source_theorem_formal_environment_bridge_context": int(
            payload.get(
                "n_requests_with_source_theorem_formal_environment_bridge_context",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt",
                0,
            )
            or 0
        ),
        "n_requests_with_exact_source_theorem_proof_body_executor_context": int(
            payload.get(
                "n_requests_with_exact_source_theorem_proof_body_executor_context",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt": int(
            payload.get(
                "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt": int(
            payload.get(
                "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt",
                0,
            )
            or 0
        ),
        "n_requests_with_source_theorem_semantic_primitive_rows": int(
            payload.get(
                "n_requests_with_source_theorem_semantic_primitive_rows",
                0,
            )
            or 0
        ),
        "n_request_source_theorem_semantic_primitive_rows": int(
            payload.get("n_request_source_theorem_semantic_primitive_rows", 0)
            or 0
        ),
        "n_requests_with_proof_body_semantic_primitive_work_order_rows": int(
            payload.get(
                "n_requests_with_proof_body_semantic_primitive_work_order_rows",
                0,
            )
            or 0
        ),
        "n_request_proof_body_semantic_primitive_work_order_rows": int(
            payload.get(
                "n_request_proof_body_semantic_primitive_work_order_rows",
                0,
            )
            or 0
        ),
        "n_requests_with_source_theorem_formal_environment_rows": int(
            payload.get(
                "n_requests_with_source_theorem_formal_environment_rows",
                0,
            )
            or 0
        ),
        "n_request_source_theorem_formal_environment_rows": int(
            payload.get("n_request_source_theorem_formal_environment_rows", 0)
            or 0
        ),
        "n_requests_with_source_theorem_proof_body_execution_result_rows": int(
            payload.get(
                "n_requests_with_source_theorem_proof_body_execution_result_rows",
                0,
            )
            or 0
        ),
        "n_request_source_theorem_proof_body_execution_result_rows": int(
            payload.get(
                "n_request_source_theorem_proof_body_execution_result_rows",
                0,
            )
            or 0
        ),
        "n_requests_with_agentic_proof_execution_materializer_rows": int(
            payload.get(
                "n_requests_with_agentic_proof_execution_materializer_rows",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "agentic_proof_execution_materializer_rows",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_execution_materializer_rows": int(
            payload.get(
                "n_request_agentic_proof_execution_materializer_rows",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "agentic_proof_execution_materializer_rows",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_agentic_proof_execution_artifact_verifier_rows": int(
            payload.get(
                "n_requests_with_agentic_proof_execution_artifact_verifier_rows",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "agentic_proof_execution_artifact_verifier_rows",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_execution_artifact_verifier_rows": int(
            payload.get(
                "n_request_agentic_proof_execution_artifact_verifier_rows",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "agentic_proof_execution_artifact_verifier_rows",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_agentic_proof_source_theorem_promotion_rows": int(
            payload.get(
                "n_requests_with_agentic_proof_source_theorem_promotion_rows",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "agentic_proof_source_theorem_promotion_rows",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_source_theorem_promotion_rows": int(
            payload.get(
                "n_request_agentic_proof_source_theorem_promotion_rows",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "agentic_proof_source_theorem_promotion_rows",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_proof_execution_feedback_summary": int(
            payload.get(
                "n_requests_with_proof_execution_feedback_summary",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "context_packet").get(
                        "proof_execution_feedback_summary"
                    )
                ),
            )
            or 0
        ),
        "n_request_proof_execution_feedback_rows": int(
            payload.get(
                "n_request_proof_execution_feedback_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "proof_execution_feedback_summary",
                        ).get("total_rows", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_proof_execution_unsupported_target_prover_rows": int(
            payload.get(
                "n_request_proof_execution_unsupported_target_prover_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "proof_execution_feedback_summary",
                        ).get("unsupported_target_prover_rows", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_patch_rerun_residual_obligation_summary": int(
            payload.get(
                "n_requests_with_patch_rerun_residual_obligation_summary",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "context_packet").get(
                        "patch_rerun_residual_obligation_summary"
                    )
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_obligation_rows": int(
            payload.get(
                "n_request_patch_rerun_residual_obligation_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_obligation_summary",
                        ).get("total_rows", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_obligation_source_discovery_needed": int(
            payload.get(
                "n_request_patch_rerun_residual_obligation_source_discovery_needed",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_obligation_summary",
                        ).get("source_discovery_needed_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_patch_rerun_residual_followup_queue_summary": int(
            payload.get(
                "n_requests_with_patch_rerun_residual_followup_queue_summary",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "context_packet").get(
                        "patch_rerun_residual_followup_queue_summary"
                    )
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_followup_queue_rows": int(
            payload.get(
                "n_request_patch_rerun_residual_followup_queue_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_followup_queue_summary",
                        ).get("total_rows", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_followup_queue_ready": int(
            payload.get(
                "n_request_patch_rerun_residual_followup_queue_ready",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_followup_queue_summary",
                        ).get("ready_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_followup_queue_source_discovery": int(
            payload.get(
                "n_request_patch_rerun_residual_followup_queue_source_discovery",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_followup_queue_summary",
                        ).get("source_discovery_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_agentic_proof_strategy_plan_summary": int(
            payload.get(
                "n_requests_with_agentic_proof_strategy_plan_summary",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "context_packet").get(
                        "agentic_proof_strategy_plan_summary"
                    )
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_strategy_plan_rows": int(
            payload.get(
                "n_request_agentic_proof_strategy_plan_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "agentic_proof_strategy_plan_summary",
                        ).get("total_rows", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_strategy_plan_ready": int(
            payload.get(
                "n_request_agentic_proof_strategy_plan_ready",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "agentic_proof_strategy_plan_summary",
                        ).get("ready_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_strategy_plan_source_discovery_cache_items": int(
            payload.get(
                "n_request_agentic_proof_strategy_plan_source_discovery_cache_items",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "agentic_proof_strategy_plan_summary",
                        ).get("source_discovery_cache_item_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_rows": int(payload.get("n_rows", len(rows)) or 0),
        "n_response_present": int(
            payload.get(
                "n_response_present",
                sum(1 for row in rows if bool(row.get("response_present", False))),
            )
            or 0
        ),
        "n_response_contract_ok": int(
            payload.get(
                "n_response_contract_ok",
                sum(
                    1
                    for row in rows
                    if bool(row.get("response_contract_ok", False))
                ),
            )
            or 0
        ),
        "n_provider_failures": int(
            payload.get(
                "n_provider_failures",
                sum(1 for row in rows if bool(row.get("provider_failure", False))),
            )
            or 0
        ),
        "provider_usage_summary": _dict_value(payload, "provider_usage_summary"),
        "n_rows_with_provider_usage": int(
            payload.get(
                "n_rows_with_provider_usage",
                len(_dict_tuple(payload.get("provider_usage_rows", []))),
            )
            or 0
        ),
        "total_provider_input_tokens": int(
            payload.get(
                "total_provider_input_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "input_tokens",
                    0,
                ),
            )
            or 0
        ),
        "total_provider_output_tokens": int(
            payload.get(
                "total_provider_output_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "output_tokens",
                    0,
                ),
            )
            or 0
        ),
        "total_provider_cache_creation_input_tokens": int(
            payload.get(
                "total_provider_cache_creation_input_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "cache_creation_input_tokens",
                    0,
                ),
            )
            or 0
        ),
        "total_provider_cache_read_input_tokens": int(
            payload.get(
                "total_provider_cache_read_input_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "cache_read_input_tokens",
                    0,
                ),
            )
            or 0
        ),
        "total_provider_total_tokens": int(
            payload.get(
                "total_provider_total_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "total_tokens",
                    0,
                ),
            )
            or 0
        ),
        "n_generated_responses_model_tier_escalated": int(
            payload.get(
                "n_generated_responses_model_tier_escalated",
                sum(1 for row in rows if _llm_row_model_tier_escalated(row)),
            )
            or 0
        ),
        "n_generated_responses_haiku_to_sonnet_escalated": int(
            payload.get(
                "n_generated_responses_haiku_to_sonnet_escalated",
                sum(1 for row in rows if _llm_row_haiku_to_sonnet_escalated(row)),
            )
            or 0
        ),
        "n_repair_attempt_ledger_model_tier_escalations": int(
            payload.get(
                "n_repair_attempt_ledger_model_tier_escalations",
                sum(
                    1
                    for row in rows
                    for ledger_row in _dict_tuple(row.get("repair_attempt_ledger"))
                    if bool(ledger_row.get("model_tier_escalated"))
                ),
            )
            or 0
        ),
        "n_model_tier_decision_ledger_rows": int(
            payload.get(
                "n_model_tier_decision_ledger_rows",
                len(model_tier_decision_ledger),
            )
            or 0
        ),
        "n_model_tier_decision_ledger_rows_with_escalation": int(
            payload.get(
                "n_model_tier_decision_ledger_rows_with_escalation",
                sum(
                    1
                    for row in model_tier_decision_ledger
                    if row.get("model_tier_escalated")
                ),
            )
            or 0
        ),
        "n_model_tier_decision_ledger_provider_failure_rows": int(
            payload.get(
                "n_model_tier_decision_ledger_provider_failure_rows",
                sum(1 for row in model_tier_decision_ledger if row.get("provider_failure")),
            )
            or 0
        ),
        "n_rows_with_model_tier_escalation": int(
            payload.get(
                "n_rows_with_model_tier_escalation",
                sum(1 for row in rows if _llm_row_model_tier_escalated(row)),
            )
            or 0
        ),
        "n_requests_with_model_tier_decision_evidence": int(
            payload.get(
                "n_requests_with_model_tier_decision_evidence",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "model_tier_decision_evidence")
                ),
            )
            or 0
        ),
        "n_request_target_prover_families": int(
            payload.get(
                "n_request_target_prover_families",
                len(request_target_prover_family_counts),
            )
            or 0
        ),
        "by_request_target_prover_family": dict(
            payload.get(
                "by_request_target_prover_family",
                dict(sorted(request_target_prover_family_counts.items())),
            )
            or {}
        ),
        "n_request_model_tier_haiku": int(
            payload.get(
                "n_request_model_tier_haiku",
                request_model_tier_counts.get("haiku", 0),
            )
            or 0
        ),
        "n_request_model_tier_sonnet": int(
            payload.get(
                "n_request_model_tier_sonnet",
                request_model_tier_counts.get("sonnet", 0),
            )
            or 0
        ),
        "n_request_model_tier_opus": int(
            payload.get(
                "n_request_model_tier_opus",
                request_model_tier_counts.get("opus", 0),
            )
            or 0
        ),
        "by_request_model_tier": dict(
            payload.get(
                "by_request_model_tier",
                dict(sorted(request_model_tier_counts.items())),
            )
            or {}
        ),
        "n_request_model_tier_decision_auto_haiku_bounded": int(
            payload.get(
                "n_request_model_tier_decision_auto_haiku_bounded",
                decision_basis_counts.get("auto_haiku_bounded_route", 0),
            )
            or 0
        ),
        "n_request_model_tier_decision_auto_sonnet_triggered": int(
            payload.get(
                "n_request_model_tier_decision_auto_sonnet_triggered",
                decision_basis_counts.get("auto_sonnet_triggers", 0),
            )
            or 0
        ),
        "n_request_model_tier_decision_operator_override": int(
            payload.get(
                "n_request_model_tier_decision_operator_override",
                decision_basis_counts.get("operator_override", 0),
            )
            or 0
        ),
        "n_request_model_tier_decision_sonnet_triggers": int(
            payload.get(
                "n_request_model_tier_decision_sonnet_triggers",
                sum(
                    len(
                        _str_tuple(
                            _dict_value(
                                packet,
                                "model_tier_decision_evidence",
                            ).get("sonnet_triggers", [])
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_route_planning_evidence_gaps": int(
            payload.get(
                "n_request_model_tier_decision_route_planning_evidence_gaps",
                sum(
                    int(
                        _dict_value(
                            row,
                            "route_planning_evidence_gap_counts",
                        ).get("total_count", 0)
                        or 0
                    )
                    for row in model_tier_decision_evidence_rows
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_route_planning_evidence_gap_sonnet_triggers": int(
            payload.get(
                "n_request_model_tier_decision_route_planning_evidence_gap_sonnet_triggers",
                sum(
                    1
                    for row in model_tier_decision_evidence_rows
                    for trigger in _str_tuple(row.get("sonnet_triggers", []))
                    if "route-planning brief evidence gap" in trigger
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_resource_feedback_readiness_rows": int(
            payload.get(
                "n_request_model_tier_decision_resource_feedback_readiness_rows",
                sum(
                    int(
                        _dict_value(row, "resource_feedback_readiness_counts").get(
                            "total_count",
                            0,
                        )
                        or 0
                    )
                    for row in model_tier_decision_evidence_rows
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_resource_feedback_reuse_ready_rows": int(
            payload.get(
                "n_request_model_tier_decision_resource_feedback_reuse_ready_rows",
                sum(
                    int(
                        _dict_value(row, "resource_feedback_readiness_counts").get(
                            "reuse_ready_count",
                            0,
                        )
                        or 0
                    )
                    for row in model_tier_decision_evidence_rows
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_resource_feedback_sonnet_triggers": int(
            payload.get(
                "n_request_model_tier_decision_resource_feedback_sonnet_triggers",
                sum(
                    1
                    for row in model_tier_decision_evidence_rows
                    for trigger in _str_tuple(row.get("sonnet_triggers", []))
                    if "resource-feedback readiness row" in trigger
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_formal_attempt_feedback_contexts": int(
            payload.get(
                "n_request_model_tier_decision_formal_attempt_feedback_contexts",
                sum(
                    int(
                        _dict_value(row, "formal_attempt_feedback_counts").get(
                            "total_count",
                            0,
                        )
                        or 0
                    )
                    for row in model_tier_decision_evidence_rows
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_formal_attempt_feedback_residual_goals": int(
            payload.get(
                "n_request_model_tier_decision_formal_attempt_feedback_residual_goals",
                sum(
                    int(
                        _dict_value(row, "formal_attempt_feedback_counts").get(
                            "residual_goal_count",
                            0,
                        )
                        or 0
                    )
                    for row in model_tier_decision_evidence_rows
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses": int(
            payload.get(
                "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses",
                sum(
                    int(
                        _dict_value(row, "formal_attempt_feedback_counts").get(
                            "failed_status_count",
                            0,
                        )
                        or 0
                    )
                    for row in model_tier_decision_evidence_rows
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers": int(
            payload.get(
                "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers",
                sum(
                    1
                    for row in model_tier_decision_evidence_rows
                    for trigger in _str_tuple(row.get("sonnet_triggers", []))
                    if "formal-attempt feedback context" in trigger
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_evidence_invalid": int(
            payload.get("n_request_model_tier_decision_evidence_invalid", 0) or 0
        ),
        "by_request_model_tier_decision_basis": dict(
            payload.get(
                "by_request_model_tier_decision_basis",
                decision_basis_counts,
            )
            or {}
        ),
        "n_requests_with_library_alignment_summary": int(
            payload.get(
                "n_requests_with_library_alignment_summary",
                sum(1 for summary in library_alignment_summaries if summary),
            )
            or 0
        ),
        "n_request_library_alignment_primitives": int(
            payload.get(
                "n_request_library_alignment_primitives",
                sum(
                    int(summary.get("n_primitives", 0) or 0)
                    for summary in library_alignment_summaries
                ),
            )
            or 0
        ),
        "n_request_library_alignment_reuse_ready_primitives": int(
            payload.get(
                "n_request_library_alignment_reuse_ready_primitives",
                library_delta_class_counts.get("reuse_ready", 0),
            )
            or 0
        ),
        "n_request_library_alignment_wrapper_primitives": int(
            payload.get(
                "n_request_library_alignment_wrapper_primitives",
                library_delta_class_counts.get("wrapper", 0),
            )
            or 0
        ),
        "n_request_library_alignment_bridge_primitives": int(
            payload.get(
                "n_request_library_alignment_bridge_primitives",
                library_delta_class_counts.get("bridge", 0),
            )
            or 0
        ),
        "n_request_library_alignment_source_port_primitives": int(
            payload.get(
                "n_request_library_alignment_source_port_primitives",
                library_delta_class_counts.get("source_port", 0),
            )
            or 0
        ),
        "n_request_library_alignment_new_definition_primitives": int(
            payload.get(
                "n_request_library_alignment_new_definition_primitives",
                library_delta_class_counts.get("new_definition", 0),
            )
            or 0
        ),
        "n_request_library_alignment_new_theory_primitives": int(
            payload.get(
                "n_request_library_alignment_new_theory_primitives",
                library_delta_class_counts.get("new_theory", 0),
            )
            or 0
        ),
        "n_request_library_alignment_unknown_primitives": int(
            payload.get(
                "n_request_library_alignment_unknown_primitives",
                library_delta_class_counts.get("unknown", 0),
            )
            or 0
        ),
        "n_request_library_alignment_bridge_or_harder_primitives": int(
            payload.get(
                "n_request_library_alignment_bridge_or_harder_primitives",
                sum(
                    int(summary.get("n_bridge_or_harder_primitives", 0) or 0)
                    for summary in library_alignment_summaries
                ),
            )
            or 0
        ),
        "n_request_library_alignment_target_compatible_reuse_declarations": int(
            payload.get(
                "n_request_library_alignment_target_compatible_reuse_declarations",
                sum(
                    int(
                        summary.get(
                            "n_target_compatible_reuse_declarations",
                            0,
                        )
                        or 0
                    )
                    for summary in library_alignment_summaries
                ),
            )
            or 0
        ),
        "n_request_library_alignment_route_options": int(
            payload.get(
                "n_request_library_alignment_route_options",
                len(library_alignment_route_option_rows),
            )
            or 0
        ),
        "n_request_library_alignment_route_option_primitives": int(
            payload.get(
                "n_request_library_alignment_route_option_primitives",
                sum(
                    int(row.get("n_selected_primitives", 0) or 0)
                    for row in library_alignment_route_option_rows
                ),
            )
            or 0
        ),
        "n_request_library_alignment_route_option_bridge_or_harder_primitives": int(
            payload.get(
                "n_request_library_alignment_route_option_bridge_or_harder_primitives",
                sum(
                    int(row.get("n_bridge_or_harder_primitives", 0) or 0)
                    for row in library_alignment_route_option_rows
                ),
            )
            or 0
        ),
        "n_request_library_alignment_route_option_target_compatible_reuse_declarations": int(
            payload.get(
                "n_request_library_alignment_route_option_target_compatible_reuse_declarations",
                sum(
                    int(row.get("n_target_compatible_reuse_declarations", 0) or 0)
                    for row in library_alignment_route_option_rows
                ),
            )
            or 0
        ),
        "total_request_library_alignment_route_option_minimum_base_cost": float(
            payload.get(
                "total_request_library_alignment_route_option_minimum_base_cost",
                sum(
                    float(row.get("minimum_route_base_cost", 0) or 0)
                    for row in library_alignment_route_option_rows
                    if isinstance(
                        row.get("minimum_route_base_cost", 0),
                        (int, float),
                    )
                ),
            )
            or 0
        ),
        "by_request_library_alignment_delta_class": dict(
            payload.get(
                "by_request_library_alignment_delta_class",
                dict(library_delta_class_counts),
            )
            or {}
        ),
        "by_request_library_alignment_minimum_coverage_bucket": dict(
            payload.get(
                "by_request_library_alignment_minimum_coverage_bucket",
                dict(library_minimum_bucket_counts),
            )
            or {}
        ),
        "n_requests_with_route_option_selection_brief": int(
            payload.get(
                "n_requests_with_route_option_selection_brief",
                sum(1 for brief in route_option_selection_briefs if brief),
            )
            or 0
        ),
        "n_request_route_option_selection_candidate_options": int(
            payload.get(
                "n_request_route_option_selection_candidate_options",
                sum(
                    len(_dict_tuple(brief.get("candidate_route_options", [])))
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_candidate_primitives": int(
            payload.get(
                "n_request_route_option_selection_candidate_primitives",
                sum(
                    int(brief.get("n_candidate_route_option_primitives", 0) or 0)
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_candidates_with_residual_goals": int(
            payload.get(
                "n_request_route_option_selection_candidates_with_residual_goals",
                sum(
                    int(
                        brief.get(
                            "n_candidate_route_options_with_residual_goals",
                            0,
                        )
                        or 0
                    )
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_candidate_residual_goals": int(
            payload.get(
                "n_request_route_option_selection_candidate_residual_goals",
                sum(
                    int(
                        brief.get(
                            "n_candidate_route_option_residual_goals",
                            0,
                        )
                        or 0
                    )
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_lower_bound_options": int(
            payload.get(
                "n_request_route_option_selection_lower_bound_options",
                sum(
                    1
                    for brief in route_option_selection_briefs
                    if str(
                        brief.get("lower_bound_selected_route_option_id", "")
                    ).strip()
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_lower_bound_residual_goals": int(
            payload.get(
                "n_request_route_option_selection_lower_bound_residual_goals",
                sum(
                    int(
                        brief.get(
                            "lower_bound_selected_residual_goal_count",
                            0,
                        )
                        or 0
                    )
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_informal_knowledge_dag_nodes": int(
            payload.get(
                "n_informal_knowledge_dag_nodes",
                _jsonl_row_collection_count(rows, "informal_knowledge_dag_nodes"),
            )
            or 0
        ),
        "n_formal_realization_dag_nodes": int(
            payload.get(
                "n_formal_realization_dag_nodes",
                _jsonl_row_collection_count(rows, "formal_realization_dag_nodes"),
            )
            or 0
        ),
        "legacy_response_field_aliases": (
            payload.get("legacy_response_field_aliases", {})
            if isinstance(payload.get("legacy_response_field_aliases", {}), dict)
            else {}
        ),
        "n_lean_realization_dag_nodes": int(
            payload.get(
                "n_lean_realization_dag_nodes",
                _jsonl_row_collection_count(rows, "lean_realization_dag_nodes"),
            )
            or 0
        ),
        "n_route_alignment_edges": int(
            payload.get(
                "n_route_alignment_edges",
                _jsonl_row_collection_count(rows, "route_alignment_edges"),
            )
            or 0
        ),
        "n_search_requests": int(
            payload.get(
                "n_search_requests",
                _jsonl_row_collection_count(rows, "search_requests"),
            )
            or 0
        ),
        "n_planner_next_actions": int(
            payload.get(
                "n_planner_next_actions",
                _jsonl_row_collection_count(rows, "planner_next_actions"),
            )
            or 0
        ),
        "n_rows_with_planner_next_actions": int(
            payload.get(
                "n_rows_with_planner_next_actions",
                sum(1 for row in rows if _dict_tuple(row.get("planner_next_actions"))),
            )
            or 0
        ),
        "n_rows_with_residual_goal_contexts": int(
            payload.get(
                "n_rows_with_residual_goal_contexts",
                sum(1 for row in rows if _dict_tuple(row.get("residual_goal_contexts"))),
            )
            or 0
        ),
        "n_row_residual_goal_contexts": int(
            payload.get(
                "n_row_residual_goal_contexts",
                _jsonl_row_collection_count(rows, "residual_goal_contexts"),
            )
            or 0
        ),
        "n_uncertainty_flags": int(
            payload.get(
                "n_uncertainty_flags",
                sum(len(_str_tuple(row.get("uncertainty_flags", []))) for row in rows),
            )
            or 0
        ),
        "n_residual_interpretations": int(
            payload.get(
                "n_residual_interpretations",
                _jsonl_row_collection_count(rows, "residual_interpretations"),
            )
            or 0
        ),
        "n_source_snippets": int(
            payload.get(
                "n_source_snippets",
                _jsonl_row_collection_count(rows, "source_snippets"),
            )
            or 0
        ),
        "n_rows_with_source_snippets": int(
            payload.get(
                "n_rows_with_source_snippets",
                sum(1 for row in rows if _dict_tuple(row.get("source_snippets"))),
            )
            or 0
        ),
        "n_formal_attempt_queue_items": int(
            payload.get(
                "n_formal_attempt_queue_items",
                _jsonl_row_collection_count(rows, "formal_attempt_queue"),
            )
            or 0
        ),
        "n_rows_with_formal_attempt_queue": int(
            payload.get(
                "n_rows_with_formal_attempt_queue",
                sum(1 for row in rows if _dict_tuple(row.get("formal_attempt_queue"))),
            )
            or 0
        ),
        "n_delta_action_witness_required_primitives": int(
            payload.get(
                "n_delta_action_witness_required_primitives",
                sum(
                    len(
                        _str_tuple(
                            _dict_value(
                                row,
                                "realization_coverage_witness",
                            ).get("delta_action_witness_required_primitives", [])
                        )
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_delta_action_witness_missing_primitives": int(
            payload.get(
                "n_delta_action_witness_missing_primitives",
                sum(
                    len(
                        _str_tuple(
                            _dict_value(
                                row,
                                "realization_coverage_witness",
                            ).get("delta_action_witness_missing_primitives", [])
                        )
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_rows_with_delta_action_witness_obligations": int(
            payload.get(
                "n_rows_with_delta_action_witness_obligations",
                sum(
                    1
                    for row in rows
                    if _str_tuple(
                        _dict_value(
                            row,
                            "realization_coverage_witness",
                        ).get("delta_action_witness_required_primitives", [])
                    )
                ),
            )
            or 0
        ),
        "n_rows_with_complete_delta_action_witness": int(
            payload.get(
                "n_rows_with_complete_delta_action_witness",
                sum(
                    1
                    for row in rows
                    if _str_tuple(
                        _dict_value(
                            row,
                            "realization_coverage_witness",
                        ).get("delta_action_witness_required_primitives", [])
                    )
                    and bool(
                        _dict_value(
                            row,
                            "realization_coverage_witness",
                        ).get("delta_action_witness_complete", False)
                    )
                ),
            )
            or 0
        ),
        "n_rows_with_route_adoption_preconditions": int(
            payload.get(
                "n_rows_with_route_adoption_preconditions",
                sum(1 for value in row_route_adoption_preconditions if value),
            )
            or 0
        ),
        "n_row_route_adoption_precondition_known_blockers": int(
            payload.get(
                "n_row_route_adoption_precondition_known_blockers",
                sum(
                    int(
                        value.get(
                            "n_known_pre_response_blockers",
                            len(_str_tuple(value.get("known_pre_response_blockers", []))),
                        )
                        or 0
                    )
                    for value in row_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_row_route_adoption_precondition_target_primitives": int(
            payload.get(
                "n_row_route_adoption_precondition_target_primitives",
                sum(
                    len(_str_tuple(value.get("target_primitives", [])))
                    for value in row_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_accepted_route_plans": int(
            payload.get(
                "n_accepted_route_plans",
                sum(
                    1
                    for row in rows
                    if str(row.get("acceptance_status", "")).startswith("ACCEPTED_")
                ),
            )
            or 0
        ),
        "n_accepted_with_formal_attempt_queue": int(
            payload.get(
                "n_accepted_with_formal_attempt_queue",
                acceptance_status_counts.get(
                    "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE",
                    0,
                ),
            )
            or 0
        ),
        "n_route_adoption_ready": route_adoption_status_counts.get(
            ROUTE_ADOPTION_READY_STATUS,
            0,
        ),
        "n_route_adoption_pending_refinement": route_adoption_status_counts.get(
            ROUTE_ADOPTION_PENDING_STATUS,
            0,
        ),
        "n_route_adoption_awaiting_llm_response": route_adoption_status_counts.get(
            ROUTE_ADOPTION_AWAITING_STATUS,
            0,
        ),
        "n_route_adoption_rejected": route_adoption_status_counts.get(
            ROUTE_ADOPTION_REJECTED_STATUS,
            0,
        ),
        "n_route_adoption_pending_formal_gap_boundary_blockers": int(
            payload.get(
                "n_route_adoption_pending_formal_gap_boundary_blockers",
                route_adoption_blocker_counts.get(
                    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES,
                    0,
                ),
            )
            or 0
        ),
        "n_route_adoption_pending_formal_attempt_queue_blockers": int(
            payload.get(
                "n_route_adoption_pending_formal_attempt_queue_blockers",
                route_adoption_blocker_counts.get(
                    ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE,
                    0,
                ),
            )
            or 0
        ),
        "n_route_adoption_blockers": sum(route_adoption_blocker_counts.values()),
        "route_adoption_blockers": tuple(route_adoption_blocker_counts),
        "route_adoption_blocker_counts": route_adoption_blocker_counts,
        "by_route_adoption_status": route_adoption_status_counts,
        "by_route_adoption_blocker": _llm_route_planner_blocker_summary(
            payload,
            rows,
        ),
        "standalone_replay_gate": dict(standalone_replay_gate),
        "standalone_replay_gate_ok": bool(
            payload.get(
                "standalone_replay_gate_ok",
                standalone_replay_gate.get("gate_ok", False),
            )
        ),
        "n_standalone_replay_route_candidates": int(
            payload.get(
                "n_standalone_replay_route_candidates",
                standalone_replay_gate.get("n_route_candidates", 0),
            )
            or 0
        ),
        "n_standalone_replay_adoptable_route_candidates": int(
            payload.get(
                "n_standalone_replay_adoptable_route_candidates",
                standalone_replay_gate.get("n_adoptable_route_candidates", 0),
            )
            or 0
        ),
        "n_standalone_replay_blocked_route_candidates": int(
            payload.get(
                "n_standalone_replay_blocked_route_candidates",
                standalone_replay_gate.get("n_blocked_route_candidates", 0),
            )
            or 0
        ),
        "standalone_replay_gate_blockers": _str_tuple(
            payload.get(
                "standalone_replay_gate_blockers",
                standalone_replay_gate.get("gate_blockers", []),
            )
        ),
        "n_row_schema_valid": int(payload.get("n_row_schema_valid", 0) or 0),
        "n_row_schema_invalid": int(payload.get("n_row_schema_invalid", 0) or 0),
        "all_ok": bool(payload.get("all_ok", False)),
    }


def _llm_route_planner_response_payload_validation_summary(
    source_dir: Path | None,
) -> dict[str, object]:
    zero_summary: dict[str, object] = {
        "requested": False,
        "manifest_path": "",
        "jsonl_path": "",
        "n_payloads": 0,
        "n_valid_payloads": 0,
        "n_invalid_payloads": 0,
        "n_request_context_packets": 0,
        "n_request_contexts_with_context_packet_inventory": 0,
        "n_request_context_inventory_total_rows": 0,
        "n_request_bound_payloads": 0,
        "n_request_bound_payloads_with_route_adoption_status": 0,
        "n_request_bound_payloads_route_adoption_ready": 0,
        "n_request_bound_payloads_route_adoption_pending_refinement": 0,
        "n_request_bound_payloads_route_adoption_rejected": 0,
        "n_request_bound_payloads_adoptable_for_standalone_replay": 0,
        "by_request_bound_payload_route_adoption_status": {},
        "request_bound_payload_route_adoption_blocker_counts": {},
        "n_request_bound_payloads_with_context_packet_inventory": 0,
        "n_request_bound_payload_context_inventory_total_rows": 0,
        "n_request_bound_payloads_with_route_adoption_preconditions": 0,
        "n_request_bound_payloads_with_blocking_route_adoption_preconditions": 0,
        "n_request_bound_payload_route_adoption_precondition_known_blockers": 0,
        "n_request_bound_payload_route_adoption_precondition_required_response_fields": 0,
        "n_request_bound_payload_route_adoption_precondition_target_primitives": 0,
        "n_request_bound_payloads_with_agentic_proof_strategy_plan": 0,
        "n_request_bound_payload_agentic_proof_strategy_plan_rows": 0,
        "n_request_bound_payload_agentic_proof_strategy_plan_ready": 0,
        "n_payloads_with_formal_attempt_queue": 0,
        "n_payload_formal_attempt_queue_items": 0,
        "n_payloads_with_formal_attempt_queue_errors": 0,
        "n_formal_attempt_queue_errors": 0,
        "n_payloads_with_agentic_proof_strategy_plan_obligation_errors": 0,
        "n_agentic_proof_strategy_plan_obligation_errors": 0,
        "n_payloads_with_declared_target_prover_family": 0,
        "n_request_bound_payloads_with_target_prover_family_mismatch": 0,
        "by_payload_target_prover_family": {},
        "by_request_context_target_prover_family": {},
        "n_schema_errors": 0,
        "n_request_context_errors": 0,
        "all_ok": False,
    }
    if source_dir is None:
        return zero_summary
    manifest_path = (
        source_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
    )
    jsonl_path = (
        source_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation.jsonl"
    )
    payload = _read_json_no_error(manifest_path)
    rows = _read_jsonl_dict_rows_no_error(jsonl_path)
    by_payload_target = payload.get("by_payload_target_prover_family", {})
    by_request_target = payload.get("by_request_context_target_prover_family", {})
    return {
        **zero_summary,
        "requested": True,
        "manifest_path": str(manifest_path),
        "jsonl_path": str(jsonl_path),
        "n_payloads": int(payload.get("n_payloads", 0) or 0),
        "n_valid_payloads": int(payload.get("n_valid_payloads", 0) or 0),
        "n_invalid_payloads": int(payload.get("n_invalid_payloads", 0) or 0),
        "n_request_context_packets": int(
            payload.get("n_request_context_packets", 0) or 0
        ),
        "n_request_contexts_with_context_packet_inventory": int(
            payload.get("n_request_contexts_with_context_packet_inventory", 0)
            or 0
        ),
        "n_request_context_inventory_total_rows": int(
            payload.get("n_request_context_inventory_total_rows", 0) or 0
        ),
        "n_request_bound_payloads": int(
            payload.get("n_request_bound_payloads", 0) or 0
        ),
        "n_request_bound_payloads_with_route_adoption_status": int(
            payload.get("n_request_bound_payloads_with_route_adoption_status", 0)
            or 0
        ),
        "n_request_bound_payloads_route_adoption_ready": int(
            payload.get("n_request_bound_payloads_route_adoption_ready", 0) or 0
        ),
        "n_request_bound_payloads_route_adoption_pending_refinement": int(
            payload.get(
                "n_request_bound_payloads_route_adoption_pending_refinement",
                0,
            )
            or 0
        ),
        "n_request_bound_payloads_route_adoption_rejected": int(
            payload.get("n_request_bound_payloads_route_adoption_rejected", 0) or 0
        ),
        "n_request_bound_payloads_adoptable_for_standalone_replay": int(
            payload.get(
                "n_request_bound_payloads_adoptable_for_standalone_replay",
                0,
            )
            or 0
        ),
        "by_request_bound_payload_route_adoption_status": (
            by_status
            if isinstance(
                by_status := payload.get(
                    "by_request_bound_payload_route_adoption_status",
                    {},
                ),
                dict,
            )
            else {}
        ),
        "request_bound_payload_route_adoption_blocker_counts": (
            blocker_counts
            if isinstance(
                blocker_counts := payload.get(
                    "request_bound_payload_route_adoption_blocker_counts",
                    {},
                ),
                dict,
            )
            else {}
        ),
        "n_request_bound_payloads_with_context_packet_inventory": int(
            payload.get(
                "n_request_bound_payloads_with_context_packet_inventory",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_context_inventory_total_rows": int(
            payload.get("n_request_bound_payload_context_inventory_total_rows", 0)
            or 0
        ),
        "n_request_bound_payloads_with_route_adoption_preconditions": int(
            payload.get(
                "n_request_bound_payloads_with_route_adoption_preconditions",
                0,
            )
            or 0
        ),
        "n_request_bound_payloads_with_blocking_route_adoption_preconditions": int(
            payload.get(
                "n_request_bound_payloads_with_blocking_route_adoption_preconditions",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_route_adoption_precondition_known_blockers": int(
            payload.get(
                "n_request_bound_payload_route_adoption_precondition_known_blockers",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_route_adoption_precondition_required_response_fields": int(
            payload.get(
                "n_request_bound_payload_route_adoption_precondition_required_response_fields",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_route_adoption_precondition_target_primitives": int(
            payload.get(
                "n_request_bound_payload_route_adoption_precondition_target_primitives",
                0,
            )
            or 0
        ),
        "n_request_bound_payloads_with_agentic_proof_strategy_plan": int(
            payload.get(
                "n_request_bound_payloads_with_agentic_proof_strategy_plan",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_agentic_proof_strategy_plan_rows": int(
            payload.get(
                "n_request_bound_payload_agentic_proof_strategy_plan_rows",
                sum(
                    int(
                        row.get(
                            "request_context_agentic_proof_strategy_plan_row_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_request_bound_payload_agentic_proof_strategy_plan_ready": int(
            payload.get(
                "n_request_bound_payload_agentic_proof_strategy_plan_ready",
                sum(
                    int(
                        row.get(
                            "request_context_agentic_proof_strategy_plan_ready_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_payloads_with_formal_attempt_queue": int(
            payload.get(
                "n_payloads_with_formal_attempt_queue",
                sum(
                    1
                    for row in rows
                    if bool(row.get("payload_formal_attempt_queue_present", False))
                ),
            )
            or 0
        ),
        "n_payload_formal_attempt_queue_items": int(
            payload.get(
                "n_payload_formal_attempt_queue_items",
                sum(
                    int(row.get("payload_formal_attempt_queue_item_count", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "n_payloads_with_formal_attempt_queue_errors": int(
            payload.get(
                "n_payloads_with_formal_attempt_queue_errors",
                sum(
                    1
                    for row in rows
                    if int(row.get("n_formal_attempt_queue_errors", 0) or 0)
                ),
            )
            or 0
        ),
        "n_formal_attempt_queue_errors": int(
            payload.get(
                "n_formal_attempt_queue_errors",
                sum(
                    int(row.get("n_formal_attempt_queue_errors", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "n_payloads_with_agentic_proof_strategy_plan_obligation_errors": int(
            payload.get(
                "n_payloads_with_agentic_proof_strategy_plan_obligation_errors",
                sum(
                    1
                    for row in rows
                    if int(
                        row.get(
                            "n_agentic_proof_strategy_plan_obligation_errors",
                            0,
                        )
                        or 0
                    )
                ),
            )
            or 0
        ),
        "n_agentic_proof_strategy_plan_obligation_errors": int(
            payload.get(
                "n_agentic_proof_strategy_plan_obligation_errors",
                sum(
                    int(
                        row.get(
                            "n_agentic_proof_strategy_plan_obligation_errors",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_payloads_with_declared_target_prover_family": int(
            payload.get("n_payloads_with_declared_target_prover_family", 0) or 0
        ),
        "n_request_bound_payloads_with_target_prover_family_mismatch": int(
            payload.get(
                "n_request_bound_payloads_with_target_prover_family_mismatch",
                0,
            )
            or 0
        ),
        "by_payload_target_prover_family": (
            dict(by_payload_target) if isinstance(by_payload_target, dict) else {}
        ),
        "by_request_context_target_prover_family": (
            dict(by_request_target) if isinstance(by_request_target, dict) else {}
        ),
        "n_schema_errors": int(payload.get("n_schema_errors", 0) or 0),
        "n_request_context_errors": int(
            payload.get("n_request_context_errors", 0) or 0
        ),
        "all_ok": bool(payload.get("all_ok", False)),
    }


def _llm_route_planner_status_counts(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    manifest_counts = payload.get("by_route_adoption_status", {})
    if isinstance(manifest_counts, dict) and manifest_counts:
        return {
            str(status): int(count or 0)
            for status, count in sorted(manifest_counts.items())
        }
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("route_adoption_status", "")).strip()
        if status:
            counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _llm_row_model_tier_escalated(row: Mapping[str, Any]) -> bool:
    metadata = row.get("generator_metadata", {})
    metadata = metadata if isinstance(metadata, Mapping) else {}
    return bool(row.get("model_tier_escalated") or metadata.get("model_tier_escalated"))


def _llm_row_haiku_to_sonnet_escalated(row: Mapping[str, Any]) -> bool:
    if not _llm_row_model_tier_escalated(row):
        return False
    metadata = row.get("generator_metadata", {})
    metadata = metadata if isinstance(metadata, Mapping) else {}
    requested = str(
        row.get("requested_model_tier")
        or metadata.get("requested_model_tier")
        or ""
    ).strip().lower()
    effective = str(
        row.get("model_tier")
        or metadata.get("effective_model_tier")
        or ""
    ).strip().lower()
    return requested == "haiku" and effective == "sonnet"


def _llm_route_planner_decision_basis_counts(
    request_packets: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for packet in request_packets:
        basis = str(
            _dict_value(packet, "model_tier_decision_evidence").get(
                "decision_basis",
                "",
            )
            or "missing"
        ).strip()
        if basis:
            counts[basis] = counts.get(basis, 0) + 1
    return dict(sorted(counts.items()))


def _llm_route_planner_blocker_counts(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    manifest_counts = payload.get("route_adoption_blocker_counts", {})
    if isinstance(manifest_counts, dict) and manifest_counts:
        return {
            str(blocker): int(count or 0)
            for blocker, count in sorted(manifest_counts.items())
        }
    counts: dict[str, int] = {}
    for row in rows:
        for blocker in _str_tuple(row.get("route_adoption_blockers", [])):
            counts[blocker] = counts.get(blocker, 0) + 1
    return dict(sorted(counts.items()))


def _llm_route_planner_blocker_summary(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
) -> dict[str, dict[str, object]]:
    manifest_summary = payload.get("by_route_adoption_blocker", {})
    if isinstance(manifest_summary, dict) and manifest_summary:
        return {
            str(blocker): dict(summary)
            for blocker, summary in sorted(manifest_summary.items())
            if isinstance(summary, dict)
        }
    counts = _llm_route_planner_blocker_counts({}, rows)
    summaries: dict[str, dict[str, object]] = {}
    for blocker, count in counts.items():
        blocker_rows = [
            row
            for row in rows
            if blocker in _str_tuple(row.get("route_adoption_blockers", []))
        ]
        by_status: dict[str, int] = {}
        by_acceptance: dict[str, int] = {}
        for row in blocker_rows:
            status = str(row.get("route_adoption_status", "")).strip()
            if status:
                by_status[status] = by_status.get(status, 0) + 1
            acceptance = str(row.get("acceptance_status", "")).strip()
            if acceptance:
                by_acceptance[acceptance] = by_acceptance.get(acceptance, 0) + 1
        summaries[blocker] = {
            "n_rows": len(blocker_rows),
            "n_blocker_occurrences": count,
            "by_route_adoption_status": dict(sorted(by_status.items())),
            "by_acceptance_status": dict(sorted(by_acceptance.items())),
            "n_response_present": sum(
                1 for row in blocker_rows if bool(row.get("response_present", False))
            ),
            "n_response_contract_ok": sum(
                1
                for row in blocker_rows
                if bool(row.get("response_contract_ok", False))
            ),
            "n_provider_failures": sum(
                1 for row in blocker_rows if bool(row.get("provider_failure", False))
            ),
        }
    return summaries


def _manifest_count_or_rows(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
    count_field: str,
    row_field: str,
) -> int:
    if count_field in payload:
        return int(payload.get(count_field, 0) or 0)
    return sum(len(_str_tuple(row.get(row_field, []))) for row in rows)


def _manifest_values_or_rows(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
    field_name: str,
) -> tuple[str, ...]:
    manifest_values = _str_tuple(payload.get(field_name, []))
    if manifest_values:
        return manifest_values
    values: list[str] = []
    for row in rows:
        values.extend(_str_tuple(row.get(field_name, [])))
    return tuple(dict.fromkeys(values))


def _manifest_values_or_row_field(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
    manifest_field: str,
    row_field: str,
) -> tuple[str, ...]:
    manifest_values = _str_tuple(payload.get(manifest_field, []))
    if manifest_values:
        return manifest_values
    values: list[str] = []
    for row in rows:
        values.extend(_str_tuple(row.get(row_field, [])))
    return tuple(dict.fromkeys(values))


def _manifest_float_or_row_mean(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
    manifest_field: str,
    row_field: str,
    *,
    required_bool_field: str | None = None,
) -> float:
    if manifest_field in payload:
        return float(payload.get(manifest_field, 0.0) or 0.0)
    values = [
        float(row.get(row_field, 0.0) or 0.0)
        for row in rows
        if required_bool_field is None or row.get(required_bool_field) is True
    ]
    if not values:
        return 0.0
    return sum(values) / len(values)


def _row_count_with_value(
    rows: tuple[dict[str, Any], ...],
    field_name: str,
    expected_value: str,
) -> int:
    return sum(
        1
        for row in rows
        if str(row.get(field_name, "")).strip() == expected_value
    )


def _llm_route_adoption_status_counts(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    by_status = payload.get("evaluation_by_llm_route_adoption_status", {})
    if isinstance(by_status, dict) and by_status:
        return {
            str(status): int(summary.get("n_rows", 0) or 0)
            for status, summary in by_status.items()
            if isinstance(summary, dict)
        }
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("llm_route_planner_route_adoption_status", "")).strip()
        if status:
            counts[status] = counts.get(status, 0) + 1
    return counts


def _llm_route_adoption_blocker_counts(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    manifest_counts = payload.get("llm_route_adoption_blocker_counts", {})
    if isinstance(manifest_counts, dict) and manifest_counts:
        return {
            str(blocker): int(count or 0)
            for blocker, count in sorted(manifest_counts.items())
        }
    counts: dict[str, int] = {}
    for row in rows:
        for blocker in _str_tuple(
            row.get("llm_route_planner_route_adoption_blockers", [])
        ):
            counts[blocker] = counts.get(blocker, 0) + 1
    return dict(sorted(counts.items()))


def _llm_route_adoption_blocker_summary(
    payload: dict[str, object],
    rows: tuple[dict[str, Any], ...],
) -> dict[str, dict[str, object]]:
    manifest_summary = payload.get("evaluation_by_llm_route_adoption_blocker", {})
    if isinstance(manifest_summary, dict) and manifest_summary:
        return {
            str(blocker): dict(summary)
            for blocker, summary in sorted(manifest_summary.items())
            if isinstance(summary, dict)
        }
    counts = _llm_route_adoption_blocker_counts({}, rows)
    summaries: dict[str, dict[str, object]] = {}
    for blocker, count in counts.items():
        blocker_rows = [
            row
            for row in rows
            if blocker
            in _str_tuple(row.get("llm_route_planner_route_adoption_blockers", []))
        ]
        by_status: dict[str, int] = {}
        for row in blocker_rows:
            status = str(row.get("llm_route_planner_route_adoption_status", "")).strip()
            if status:
                by_status[status] = by_status.get(status, 0) + 1
        summaries[blocker] = {
            "n_rows": len(blocker_rows),
            "n_blocker_occurrences": count,
            "by_route_adoption_status": dict(sorted(by_status.items())),
        }
    return summaries


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return ()


def _dict_tuple(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, (list, tuple, set)):
        return ()
    return tuple(dict(item) for item in value if isinstance(item, dict))


def _target_context_summary_proof_source_refs(
    summary: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    if not isinstance(summary, Mapping):
        return ()
    return _str_tuple(summary.get("proof_source_refs", []))


def _target_context_summary_proof_source_ref_support_rows(
    summary: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(summary, Mapping):
        return ()
    return _dict_tuple(summary.get("proof_source_ref_support_rows", []))


def _target_context_summary_proof_source_ref_support_source_field_count(
    summary: Mapping[str, Any] | None,
) -> int:
    return sum(
        len(_str_tuple(row.get("source_fields", [])))
        for row in _target_context_summary_proof_source_ref_support_rows(summary)
    )


def _dict_value(mapping: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key, {}) if isinstance(mapping, Mapping) else {}
    return dict(value) if isinstance(value, Mapping) else {}


def _source_ref_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _target_prover_key(value: object) -> str:
    key = _source_ref_key(value)
    aliases = {
        "coq": "rocq",
        "rocq_coq": "rocq",
        "coq_rocq": "rocq",
        "lean": "lean4",
        "lean_4": "lean4",
        "lean4": "lean4",
        "isabelle_hol": "isabelle",
        "hol_4": "hol4",
        "hollight": "hol_light",
        "hol_light": "hol_light",
        "set_mm": "metamath",
        "setmm": "metamath",
    }
    return aliases.get(key, key)


def _jsonl_row_collection_count(
    rows: tuple[dict[str, Any], ...],
    field_name: str,
) -> int:
    count = 0
    for row in rows:
        values = row.get(field_name)
        if isinstance(values, dict):
            count += 1
        elif isinstance(values, (list, tuple, set)):
            count += sum(1 for value in values if isinstance(value, dict))
    return count


def _read_json_no_error(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl_dict_rows_no_error(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return ()
    rows: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return tuple(rows)


def _copy_docs(docs_dir: Path, errors: list[str]) -> tuple[str, ...]:
    copied: list[str] = []
    repo_root = Path(__file__).resolve().parents[1]
    for source in (
        repo_root / "docs" / "library_aware_formalization_gap_planner.md",
        repo_root / "docs" / "evaluation_benchmark_strategy.md",
    ):
        if not source.exists():
            errors.append(f"missing publication doc source: {source}")
            continue
        dest = docs_dir / source.name
        shutil.copy2(source, dest)
        copied.append(str(dest))
    return tuple(copied)


def _copy_example_inputs(examples_dir: Path, errors: list[str]) -> tuple[dict[str, object], ...]:
    copied: list[dict[str, object]] = []
    repo_root = Path(__file__).resolve().parents[1]
    examples = (
        (
            "standalone_input_example",
            repo_root / "data" / "formalization_gap_planner_standalone_example.json",
            examples_dir / "formalization_gap_planner_standalone_example.json",
            "direct input for formalization-gap-planner-standalone-plan",
        ),
        (
            "target_intake_example",
            repo_root / "data" / "formalization_gap_planner_target_intake_example.json",
            examples_dir / "formalization_gap_planner_target_intake_example.json",
            "raw theorem request input for formalization-gap-planner-target-intake",
        ),
    )
    for example_name, source, dest, purpose in examples:
        if not source.exists():
            errors.append(f"missing publication example source: {source}")
            continue
        shutil.copy2(source, dest)
        target_prover_family = ""
        try:
            source_payload = json.loads(dest.read_text(encoding="utf-8"))
            if isinstance(source_payload, dict):
                target_prover_family = str(
                    source_payload.get("target_prover_family", "")
                ).strip()
        except Exception as exc:  # pragma: no cover - defensive bundle metadata
            errors.append(
                f"could not inspect publication example target prover: {dest}: {exc}"
            )
        copied.append(
            {
                "example_name": example_name,
                "path": str(dest),
                "bundle_relative_path": str(dest.relative_to(examples_dir.parent)),
                "purpose": purpose,
                "target_prover_family": target_prover_family,
                "ok": dest.exists(),
            }
        )
    return tuple(copied)


def _example_target_prover_families(
    copied_examples: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(row.get("target_prover_family", "")).strip().lower()
                for row in copied_examples
                if str(row.get("target_prover_family", "")).strip()
            }
        )
    )


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Publication Bundle",
        "",
        f"- Bundle id: `{payload.get('bundle_id')}`",
        f"- Packaged component: `{payload.get('packaged_component')}`",
        f"- Portable schema: `{payload.get('portable_schema_id')}`",
        f"- Core artifacts: {payload.get('n_core_artifacts_ok')}/{payload.get('n_core_artifacts')}",
        f"- Optional artifact files copied: {payload.get('n_optional_artifact_files_copied')}",
        f"- Docs copied: {payload.get('n_docs_copied')}",
        f"- Example inputs copied: {payload.get('n_example_inputs_copied')}",
        f"- Example target provers: {payload.get('example_target_prover_families')}",
        f"- Reproduction commands: {payload.get('reproduction_summary', {}).get('n_commands')}",
        f"- Benchmark-audit checks: {payload.get('benchmark_audit_summary', {}).get('n_checks')}",
        (
            f"- Benchmark route schema valid: "
            f"{payload.get('benchmark_summary', {}).get('n_route_row_schema_valid')}/"
            f"{payload.get('benchmark_summary', {}).get('n_routes')}"
        ),
        (
            f"- Evaluation rows/schema valid: "
            f"{payload.get('evaluation_summary', {}).get('n_evaluation_row_schema_valid')}/"
            f"{payload.get('evaluation_summary', {}).get('n_evaluation_rows')}"
        ),
        (
            f"- Evaluation omitted cost-hint primitives: "
            f"{payload.get('evaluation_summary', {}).get('n_realization_omitted_cost_hint_primitives')} "
            f"baseline={payload.get('evaluation_summary', {}).get('realization_cost_hint_baseline_primitives')} "
            f"omitted={payload.get('evaluation_summary', {}).get('realization_omitted_cost_hint_primitives')}"
        ),
        (
            f"- Evaluation minimal delta/alignment: "
            f"options={payload.get('evaluation_summary', {}).get('n_minimal_delta_route_options')} "
            f"selected_cost="
            f"{payload.get('evaluation_summary', {}).get('mean_minimal_delta_selected_route_cost')} "
            f"alignment={payload.get('evaluation_summary', {}).get('mean_alignment_coverage')} "
            f"kernel_truth="
            f"{payload.get('evaluation_summary', {}).get('n_kernel_verified_ground_truth')} "
            f"kernel_witnesses="
            f"{payload.get('evaluation_summary', {}).get('n_kernel_verification_witnesses')}"
        ),
        (
            f"- Evaluation route-option selection "
            f"rows/options/primitives/residual-options/residual-goals/"
            f"lower-bound-residuals/selected-residuals/lb-md-matches/"
            f"lb-md-mismatches/selected-ids/selected-lb-matches/"
            f"selected-md-matches: "
            f"{payload.get('evaluation_summary', {}).get('n_rows_with_llm_route_planner_route_option_selection_brief')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selection_candidate_options')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selection_candidate_primitives')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selection_candidates_with_residual_goals')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selection_candidate_residual_goals')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selection_lower_bound_residual_goals')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta')}/"
            f"{payload.get('evaluation_summary', {}).get('n_rows_with_llm_route_planner_route_option_selected_route_option')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selected_matches_lower_bound')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_planner_route_option_selected_matches_minimal_delta')}"
        ),
        (
            f"- Evaluation route adoption ready/pending/blockers: "
            f"{payload.get('evaluation_summary', {}).get('n_rows_ready_for_route_adoption')}/"
            f"{payload.get('evaluation_summary', {}).get('n_rows_pending_refinement_before_route_adoption')}/"
            f"{payload.get('evaluation_summary', {}).get('n_llm_route_adoption_blockers')} "
            f"source_grounding={payload.get('evaluation_summary', {}).get('n_llm_route_adoption_pending_source_grounding_blockers')} "
            f"quality_controls={payload.get('evaluation_summary', {}).get('n_llm_route_adoption_pending_quality_control_blockers')} "
            f"formal_attempt_queue={payload.get('evaluation_summary', {}).get('n_llm_route_adoption_pending_formal_attempt_queue_blockers')}"
        ),
        (
            f"- Evaluation LLM provider usage rows/input/output/total: "
            f"{payload.get('evaluation_summary', {}).get('n_rows_with_llm_route_planner_provider_usage')}/"
            f"{payload.get('evaluation_summary', {}).get('total_llm_route_planner_provider_input_tokens')}/"
            f"{payload.get('evaluation_summary', {}).get('total_llm_route_planner_provider_output_tokens')}/"
            f"{payload.get('evaluation_summary', {}).get('total_llm_route_planner_provider_total_tokens')}"
        ),
        (
            f"- Evaluation quality controls: "
            f"rows={payload.get('evaluation_summary', {}).get('n_rows_with_quality_controls')} "
            f"fields={payload.get('evaluation_summary', {}).get('quality_control_fields')}"
        ),
        (
            f"- Library coverage map target families: "
            f"{payload.get('library_coverage_map_summary', {}).get('target_prover_family')} "
            f"by={payload.get('library_coverage_map_summary', {}).get('by_target_prover_family')}"
        ),
        (
            f"- Cross-prover formal-attempt dependency: "
            f"with_dependency="
            f"{payload.get('cross_prover_formal_attempt_dependency_summary', {}).get('n_total_packets_with_formal_attempt_dependency')} "
            f"ready="
            f"{payload.get('cross_prover_formal_attempt_dependency_summary', {}).get('n_total_packets_formal_attempt_initial_ready')} "
            f"waiting="
            f"{payload.get('cross_prover_formal_attempt_dependency_summary', {}).get('n_total_packets_formal_attempt_waiting')} "
            f"missing="
            f"{payload.get('cross_prover_formal_attempt_dependency_summary', {}).get('n_total_packets_formal_attempt_missing_prerequisites')} "
            f"witness_ack="
            f"{payload.get('cross_prover_formal_attempt_dependency_summary', {}).get('n_total_response_minimal_delta_action_witnesses_acknowledged')}/"
            f"{payload.get('cross_prover_formal_attempt_dependency_summary', {}).get('n_total_response_minimal_delta_action_witnesses_required')} "
            f"target_summary_consistent="
            f"{payload.get('cross_prover_formal_attempt_dependency_summary', {}).get('target_summary_consistent')}"
        ),
        (
            f"- LLM route planner ready/pending/blockers: "
            f"{payload.get('llm_route_planner_summary', {}).get('n_route_adoption_ready')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_route_adoption_pending_refinement')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_route_adoption_blockers')} "
            f"preconditions={payload.get('llm_route_planner_summary', {}).get('n_requests_with_route_adoption_preconditions')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_request_route_adoption_precondition_known_blockers')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_request_route_adoption_precondition_required_response_fields')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_request_route_adoption_precondition_target_primitives')} "
            f"row_preconditions={payload.get('llm_route_planner_summary', {}).get('n_rows_with_route_adoption_preconditions')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_row_route_adoption_precondition_known_blockers')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_row_route_adoption_precondition_target_primitives')}"
        ),
        (
            f"- LLM standalone replay gate: "
            f"{payload.get('llm_route_planner_summary', {}).get('standalone_replay_gate_ok')} "
            f"adoptable={payload.get('llm_route_planner_summary', {}).get('n_standalone_replay_adoptable_route_candidates')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_standalone_replay_route_candidates')} "
            f"blockers={payload.get('llm_route_planner_summary', {}).get('standalone_replay_gate_blockers')}"
        ),
        (
            f"- LLM route planner source-grounding rows/pending/residual-unresolved: "
            f"{payload.get('llm_route_planner_summary', {}).get('n_request_source_grounding_rows')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_requests_with_pending_source_grounding_obligation_inventory')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_request_residual_source_grounding_unresolved_rows')} "
            f"feedback={payload.get('feedback_llm_route_planner_summary', {}).get('n_request_source_grounding_rows')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_requests_with_pending_source_grounding_obligation_inventory')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_request_residual_source_grounding_unresolved_rows')}"
        ),
        (
            f"- LLM formal-source retrieval requests/metadata/semantic-rerank: "
            f"{payload.get('llm_route_planner_summary', {}).get('n_requests_with_formal_source_retrieval_summary')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_request_formal_source_retrieval_metadata_rows')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_request_formal_source_semantic_rerank_rows')} "
            f"feedback={payload.get('feedback_llm_route_planner_summary', {}).get('n_requests_with_formal_source_retrieval_summary')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_request_formal_source_retrieval_metadata_rows')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_request_formal_source_semantic_rerank_rows')}"
        ),
        (
            f"- LLM formal-attempt queues primary/feedback: "
            f"primary_items={payload.get('llm_route_planner_summary', {}).get('n_formal_attempt_queue_items')} "
            f"primary_rows={payload.get('llm_route_planner_summary', {}).get('n_rows_with_formal_attempt_queue')} "
            f"feedback_items={payload.get('feedback_llm_route_planner_summary', {}).get('n_formal_attempt_queue_items')} "
            f"feedback_rows={payload.get('feedback_llm_route_planner_summary', {}).get('n_rows_with_formal_attempt_queue')}"
        ),
        (
            f"- LLM proof-execution feedback rows primary/feedback: "
            f"primary={payload.get('llm_route_planner_summary', {}).get('n_request_proof_execution_feedback_rows')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_request_proof_execution_unsupported_target_prover_rows')} "
            f"feedback={payload.get('feedback_llm_route_planner_summary', {}).get('n_request_proof_execution_feedback_rows')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_request_proof_execution_unsupported_target_prover_rows')}"
        ),
        (
            f"- LLM response-payload formal-attempt queue validation: "
            f"payloads={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_payloads_with_formal_attempt_queue')} "
            f"items={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_payload_formal_attempt_queue_items')} "
            f"error_payloads={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_payloads_with_formal_attempt_queue_errors')} "
            f"errors={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_formal_attempt_queue_errors')} "
            f"adoption_ready={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_request_bound_payloads_route_adoption_ready')}/"
            f"{payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_request_bound_payloads_with_route_adoption_status')} "
            f"adoptable={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_request_bound_payloads_adoptable_for_standalone_replay')} "
            f"precondition_targets={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_request_bound_payload_route_adoption_precondition_target_primitives')} "
            f"agentic_strategy_ready={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_request_bound_payload_agentic_proof_strategy_plan_ready')}/"
            f"{payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_request_bound_payload_agentic_proof_strategy_plan_rows')} "
            f"agentic_strategy_errors={payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_agentic_proof_strategy_plan_obligation_errors')}/"
            f"{payload.get('llm_route_planner_response_payload_validation_summary', {}).get('n_payloads_with_agentic_proof_strategy_plan_obligation_errors')}"
        ),
        (
            f"- LLM route planner provider usage rows/input/output/total: "
            f"{payload.get('llm_route_planner_summary', {}).get('n_rows_with_provider_usage')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('total_provider_input_tokens')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('total_provider_output_tokens')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('total_provider_total_tokens')}"
        ),
        (
            f"- LLM route planner prompt budget rows/input/max-output/total: "
            f"{payload.get('llm_route_planner_summary', {}).get('n_prompt_token_budget_rows')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('estimated_prompt_input_tokens')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('estimated_prompt_max_output_tokens')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('estimated_prompt_total_token_budget')} "
            f"cap={payload.get('llm_route_planner_summary', {}).get('max_estimated_prompt_input_tokens')} "
            f"blocks={payload.get('llm_route_planner_summary', {}).get('n_prompt_token_budget_preflight_blocked')}"
        ),
        (
            f"- LLM route planner model-tier ledger rows/escalations/provider-failures: "
            f"{payload.get('llm_route_planner_summary', {}).get('n_model_tier_decision_ledger_rows')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_model_tier_decision_ledger_rows_with_escalation')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_model_tier_decision_ledger_provider_failure_rows')}"
        ),
        (
            f"- Feedback LLM route planner ready/pending/blockers: "
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_route_adoption_ready')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_route_adoption_pending_refinement')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_route_adoption_blockers')} "
            f"preconditions={payload.get('feedback_llm_route_planner_summary', {}).get('n_requests_with_route_adoption_preconditions')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_request_route_adoption_precondition_known_blockers')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_request_route_adoption_precondition_required_response_fields')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_request_route_adoption_precondition_target_primitives')} "
            f"row_preconditions={payload.get('feedback_llm_route_planner_summary', {}).get('n_rows_with_route_adoption_preconditions')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_row_route_adoption_precondition_known_blockers')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_row_route_adoption_precondition_target_primitives')}"
        ),
        (
            f"- Feedback LLM standalone replay gate: "
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('standalone_replay_gate_ok')} "
            f"adoptable={payload.get('feedback_llm_route_planner_summary', {}).get('n_standalone_replay_adoptable_route_candidates')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_standalone_replay_route_candidates')} "
            f"blockers={payload.get('feedback_llm_route_planner_summary', {}).get('standalone_replay_gate_blockers')}"
        ),
        (
            f"- Feedback LLM route planner provider usage rows/input/output/total: "
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_rows_with_provider_usage')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('total_provider_input_tokens')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('total_provider_output_tokens')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('total_provider_total_tokens')}"
        ),
        (
            f"- Feedback LLM route planner prompt budget rows/input/max-output/total: "
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_prompt_token_budget_rows')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('estimated_prompt_input_tokens')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('estimated_prompt_max_output_tokens')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('estimated_prompt_total_token_budget')} "
            f"cap={payload.get('feedback_llm_route_planner_summary', {}).get('max_estimated_prompt_input_tokens')} "
            f"blocks={payload.get('feedback_llm_route_planner_summary', {}).get('n_prompt_token_budget_preflight_blocked')}"
        ),
        (
            f"- Feedback LLM route planner model-tier ledger rows/escalations/provider-failures: "
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_model_tier_decision_ledger_rows')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_model_tier_decision_ledger_rows_with_escalation')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_model_tier_decision_ledger_provider_failure_rows')}"
        ),
        (
            f"- LLM registry resources in prompt: "
            f"primary={payload.get('llm_route_planner_summary', {}).get('n_requests_with_component_resource_registry_context')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_resources_in_prompt')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_contracts_in_prompt')} "
            f"semantic_bridge={payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt')} "
            f"post_proof_body_semantic_bridge={payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt')} "
            f"formal_env_bridge={payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt')} "
            f"proof_body_executor={payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt')}/"
            f"{payload.get('llm_route_planner_summary', {}).get('n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt')} "
            f"feedback={payload.get('feedback_llm_route_planner_summary', {}).get('n_requests_with_component_resource_registry_context')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_resources_in_prompt')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_contracts_in_prompt')} "
            f"feedback_semantic_bridge={payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt')} "
            f"feedback_post_proof_body_semantic_bridge={payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt')} "
            f"feedback_formal_env_bridge={payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt')} "
            f"feedback_proof_body_executor={payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt')}/"
            f"{payload.get('feedback_llm_route_planner_summary', {}).get('n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt')}"
        ),
        (
            f"- Adapter registry row schema valid: "
            f"{payload.get('adapter_registry_summary', {}).get('n_adapter_row_schema_valid')}/"
            f"{payload.get('adapter_registry_summary', {}).get('n_adapters')}"
        ),
        f"- Component-resource rows: {payload.get('component_resource_registry_summary', {}).get('n_component_rows')}",
        (
            f"- Component-resource row schemas valid: "
            f"components={payload.get('component_resource_registry_summary', {}).get('n_component_row_schema_valid')}/"
            f"{payload.get('component_resource_registry_summary', {}).get('n_component_rows')}, "
            f"resources={payload.get('component_resource_registry_summary', {}).get('n_resource_row_schema_valid')}/"
            f"{payload.get('component_resource_registry_summary', {}).get('n_resources')}"
        ),
        f"- Frontier resources: {payload.get('component_resource_registry_summary', {}).get('n_frontier_resources')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Core Artifacts",
        "",
    ]
    for artifact in payload.get("core_artifacts", []):
        if not isinstance(artifact, dict):
            continue
        lines.append(
            f"- `{artifact.get('artifact_name')}` ok={artifact.get('ok')} "
            f"path={artifact.get('path')}"
        )
    lines.extend(["", "## Optional Artifacts", ""])
    for artifact in payload.get("optional_artifacts", []):
        if not isinstance(artifact, dict) or not artifact.get("requested"):
            continue
        lines.append(
            f"- `{artifact.get('artifact_name')}` copied={artifact.get('n_files_copied')} "
            f"ok={artifact.get('ok')}"
        )
    lines.extend(
        [
            "",
            "## Reuse",
            "",
            "The portable contract is prover-agnostic. A downstream prover adapter should map "
            "the work-packet contract to its own declaration index, library snapshot, and "
            "kernel-verification command before making any theorem-proof claim.",
        ]
    )
    return "\n".join(lines) + "\n"
