from __future__ import annotations

import json
import math
import re
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    ToolCallRecord,
    agent_task_continuation_reference,
    agent_task_from_payload as _agent_task_from_runtime_payload,
    agent_task_reference,
    agent_runtime_substage,
    compact_runtime_artifact_references,
    materialize_agent_task_continuation,
    resolve_runtime_artifact_references,
    restore_agent_task_continuation,
    restore_agent_task_continuation_reference,
    runtime_artifact_reference,
)
from .architect_coordinator_llm import (
    ARCHITECT_COORDINATOR_BOUNDARY,
    ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE,
    ARCHITECT_FEEDBACK_ROUTE_OPERATION,
    LLMArchitectCoordinatorAgent,
    architect_validated_plan_reuse_metadata,
    architect_formal_target_is_completion_placeholder,
)
from .architect_metric_contract_authoring import (
    ArchitectMetricSemanticReviewRejected,
)
from .algorithm_engineer_llm import (
    ALGORITHM_ENGINEER_BOUNDARY,
    ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
    LLMAlgorithmEngineerAgent,
)
from .critic_evaluator_llm import (
    CRITIC_EVALUATOR_BOUNDARY,
    CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE,
    LLMCriticEvaluatorAgent,
)
from .fingerprint import stable_hash
from .lean_proof_agent_contract import (
    llm_proof_body_generation_contract,
)
from .generated_metric_contract import (
    GENERATED_METRIC_CONTRACT_BOUNDARY,
    GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED,
    bind_generated_metric_contract_authority,
    evaluate_generated_metric_contracts,
    generated_metric_contract_set_id,
    generated_metric_contracts_for_artifact,
    generated_metric_requirement_authority_policy_from_context,
    generated_metric_requirement_set_id,
    generated_metric_requirement_target_namespace_contract,
    generated_metric_requirements_from_context,
    generated_sandbox_runtime_replicates,
    validate_generated_metric_contracts,
)
from .generated_code_semantic_reviewer_llm import (
    GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
    GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE,
    GENERATED_CODE_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS,
    LLMGeneratedCodeSemanticReviewerAgent,
    normalize_generated_code_semantic_review_findings,
    validate_generated_code_semantic_review_packet,
)
from .generated_code_semantic_review_replan import (
    GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY,
    GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM,
    advance_generated_code_semantic_review_lineage_budget,
    build_generated_code_semantic_review_producer_revision_task,
    record_generated_code_semantic_review_lineage_action,
)
from .generated_code_semantic_review_scope import (
    generated_code_semantic_review_proposal_projection,
    generated_code_semantic_review_scope_projection,
    generated_code_semantic_review_theory_projection,
    generated_code_semantic_review_upstream_dependency_projection,
)

from .scientific_sandbox import (
    SCIENTIFIC_WASM_SANDBOX_PROFILE,
    ScientificEstimatorBinding,
    execute_scientific_sandbox,
    generated_code_execution_contract_errors,
    normalized_generated_code_language,
    normalized_generated_code_profile,
    normalized_scientific_dependencies,
)
from .scientific_code_workspace import (
    SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY,
    SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER,
    SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS,
    advance_scientific_consumer_revision_budget,
    complete_scientific_source_draft,
    scientific_consumer_dependency_context,
    scientific_consumer_replay_drafts,
    scientific_consumer_revision_sources,
    scientific_workspace_prototype_observation,
)
from .evaluation_protocol_revision import (
    architect_metric_requirement_validation_failure_result,
    architect_metric_semantic_review_validation_failure_result,
    architect_preexecution_metric_protocol_rejection_result,
    invalidate_metric_protocol_authorization,
    metric_protocol_preexecution_review_observation_blocked_result,
    metric_protocol_preexecution_review_observation_errors,
)
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND,
    METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED,
    METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING,
    build_theory_informed_metric_protocol_material,
    reviewed_metric_protocol_authority_matches_theory,
)
from .implementation_metric_handoff import (
    accepted_implementation_interface_handoff_errors,
    build_accepted_implementation_interface_handoff,
)
from .research_evaluation import build_research_evaluation_summary
from .formal_target_semantic_reviewer_llm import (
    FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
    LLMFormalTargetSemanticReviewerAgent,
)
from .formal_target_semantic_review_runtime import (
    FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM,
    FormalTargetSemanticReviewerRuntimeSubsystem,
    _runtime_formal_target_semantic_review_dispatch,
)
from .lean_candidate_identity import (
    LEAN_TARGET_STATEMENT_HASH_ALGORITHM,
    lean_source_lineage_id,
    lean_target_statement_hash,
    run_lean_candidate_identity_probe,
)
from .lean_candidate_revision_tool_loop import (
    resolve_lean_workspace_start_source,
)
from .lean_kernel_promotion import evaluate_lean_kernel_promotion
from .formalizer_llm import (
    FORMALIZER_BOUNDARY,
    FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE,
    FORMAL_TARGET_ROLES,
    FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT,
    FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
    LLMFormalizerProofEngineerAgent,
    build_formalizer_workspace_target,
    compact_lean_workspace_observation,
)
from .formalizer_feedback import (
    formalizer_tool_observation_envelope,
    formalizer_validation_feedback_envelope,
)
from .formalizer_candidate_identity import (
    build_candidate_lineage_contract,
    evaluate_candidate_lineage,
    source_theorem_explicit_target_ids,
)
from .structured_output_retry import PacketValidationError
from .semantic_review_feedback import (
    coding_agent_observations_only,
)
from .model_backend import (
    AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY,
    AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY,
    ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    SUPPORTED_GENERATOR_PROVIDERS,
    SUPPORTED_LIVE_GENERATOR_PROVIDERS,
    claude_tier_routing_contract,
    claude_model_tier_mismatch,
    is_live_generator_backend,
    llm_subsystem_expected_model_tier,
    normalize_generator_provider_name,
    resolve_generator_model,
)
from .formal_source_index import FormalSourceHit
from .formal_source_prompt_context import (
    compact_formal_source_grounding_hits_for_prompt,
    formal_source_context_for_hit,
    formalizer_feedback_with_task_bound_formal_source_queries,
    prompt_safe_formal_source_provenance,
    unique_formal_source_hit_payloads,
)
from .formal_source_topology import active_project_formal_source_scope_ids
from .lean_proof_state_trace_rag import (
    ai4slt_proof_state_trace_rag_descriptor,
    attach_ai4slt_proof_state_trace_rag,
)
from .lean_agent_providers import (
    LEAN_PROVIDER_BOUNDARY,
    LeanProofSearchProvider,
    provider_descriptor,
    provider_runtime_diagnostics,
    reset_provider_runtime_diagnostics,
)
from .proof_bank_formal_source import build_default_formal_source_retriever
from .proof_state_feedback import (
    PROOF_STATE_FEEDBACK_BOUNDARY,
    ProofStateFeedbackProvider,
    proof_state_feedback_row_to_json,
)
from .research_architect import (
    KERNEL_PROOF_BOUNDARY,
    LLMTheoryDeveloperAgent,
    THEORY_DEVELOPER_STAGE_CHECKPOINT_KIND,
    THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
    theory_developer_source_environment_feedback,
)
from .theory_workspace import THEORY_WORKSPACE_CHECKPOINT_KIND
from .theory_revision_lineage import (
    THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY,
    build_architect_routed_theory_revision_binding,
    build_theory_developer_revision_binding,
    consume_architect_routed_theory_revision,
    theory_developer_revision_binding_errors,
)
from .research_lab import ProblemFormalizer, ResearchSimulator, TheoryPlanner
from .research_knowledge import retrieve_problem_knowledge
from .research_paper_index import retrieve_paper_sources
from .research_schema import (
    CandidateProcedure,
    FormalSubclaim,
    KnowledgeCard,
    OpenResearchQuestion,
    PaperSourceHit,
    ResearchProblemSpec,
    ResearchSimulation,
    TheoremGoal,
)
from .runtime_research_problem_adapter import (
    derive_runtime_research_problem,
    legacy_runtime_research_problem_provenance,
    runtime_llm_research_authority_required,
)
from .simulation_engineer_llm import (
    EMPIRICAL_EVALUATION_PHASE_EXPLORATORY,
    LLMSimulationEngineerAgent,
    SIMULATION_ENGINEER_BOUNDARY,
    SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
)
from .task_family import primary_task_family_from_question
from .theory_derivation_trace import (
    THEORY_TRACE_ALIGNMENT_BOUNDARY,
    THEORY_TRACE_CONSUMPTION_BOUNDARY,
    theory_trace_alignment_contract,
)


RUNTIME_SCHEMA_VERSION = 1
RUNTIME_ARCHITECT_OPERATION_THEORY_PREFLIGHT = (
    "theory_execution_preflight_then_algorithm"
)
RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC = (
    "implementation_accepted_metric_authoring"
)
SIMULATION_NOT_PROOF_BOUNDARY = (
    "Executable simulation and deterministic scaffold runs are empirical "
    "environment observations. They can falsify or support a proposal, but "
    "they are not theorem proof evidence."
)
FORMALIZER_LEAN_CANDIDATE_KERNEL_BOUNDARY = (
    "Formalizer Lean candidate local compilation is verifier feedback for a "
    "generated candidate. It is not source-theorem proof evidence unless the "
    "candidate is promoted to exact source-theorem kernel verification bound "
    "to the current target; use "
    "formalizer_lean_candidate_local_lean_compiled_observed for the raw "
    "candidate compile signal."
)
FORMAL_VERIFICATION_POLICIES = ("required", "optional", "advisory")
RECOMMENDED_RESEARCH_PATHS = ("simulation_first", "proof_first", "dual_track")

@dataclass(frozen=True)
class ResearchAgentRuntimeConfig:
    n_runs: int = 100
    seed: int = 20260528
    generated_simulation_timeout_seconds: int = 60
    max_iterations: int = 12
    max_subsystem_retries: int = 1
    max_critic_revision_rounds: int = 1
    generated_code_semantic_review_max_revisions: int = 1
    metric_protocol_max_upstream_theory_revisions: int = 1
    formal_target_semantic_review_required: bool = False
    formal_target_semantic_review_max_revisions: int = 1
    resume_through_architect: bool = False
    formal_verification_policy: str = "optional"
    recommended_research_path: str = ""
    evaluation_mode: str = "debug"
    evaluation_claude_model_tier: str = ""
    evaluation_claude_model: str = ""
    formalizer_candidate_local_lean: bool = False
    formalizer_candidate_lean_project: str = ""
    formalizer_candidate_lean_timeout: int = 30
RUNTIME_RESEARCH_EVALUATION_MODES = frozenset(
    {"research_eval", "capability_eval"}
)


def _is_runtime_research_evaluation_mode(evaluation_mode: Any) -> bool:
    return str(evaluation_mode or "").strip() in RUNTIME_RESEARCH_EVALUATION_MODES


def _normalized_runtime_evaluation_model_config(
    config: ResearchAgentRuntimeConfig,
) -> ResearchAgentRuntimeConfig:
    if not _is_runtime_research_evaluation_mode(config.evaluation_mode):
        return config
    configured_tier = str(
        config.evaluation_claude_model_tier or ""
    ).strip().lower()
    configured_model = str(config.evaluation_claude_model or "").strip()
    errors: list[str] = []
    if configured_tier and configured_tier != LIVE_EVALUATION_CLAUDE_MODEL_TIER:
        errors.append(
            "research evaluation requires evaluation_claude_model_tier="
            f"{LIVE_EVALUATION_CLAUDE_MODEL_TIER}; configured {configured_tier}"
        )
    if configured_model and configured_model != LIVE_EVALUATION_CLAUDE_MODEL:
        errors.append(
            "research evaluation requires evaluation_claude_model="
            f"{LIVE_EVALUATION_CLAUDE_MODEL}; configured {configured_model}"
        )
    if errors:
        raise ValueError("; ".join(errors))
    return replace(
        config,
        evaluation_claude_model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        evaluation_claude_model=LIVE_EVALUATION_CLAUDE_MODEL,
    )


def _runtime_research_evaluation_contract_flag(
    evidence_contract: Mapping[str, Any],
    requirement: str,
) -> bool:
    return evidence_contract.get(
        f"research_evaluation_requires_{requirement}"
    ) is True


def _normalized_formal_verification_policy(policy: str) -> str:
    value = str(policy or "optional").strip().lower()
    if value not in FORMAL_VERIFICATION_POLICIES:
        raise ValueError(
            "formal_verification_policy must be one of: "
            + ", ".join(FORMAL_VERIFICATION_POLICIES)
        )
    return value


def _default_recommended_research_path_for_policy(
    formal_verification_policy: str,
) -> str:
    policy = _normalized_formal_verification_policy(formal_verification_policy)
    if policy == "required":
        return "dual_track"
    if policy == "advisory":
        return "simulation_first"
    return "dual_track"


def _normalized_recommended_research_path(
    path: str,
    *,
    formal_verification_policy: str,
) -> str:
    value = str(path or "").strip().lower()
    if not value:
        return _default_recommended_research_path_for_policy(
            formal_verification_policy
        )
    if value not in RECOMMENDED_RESEARCH_PATHS:
        raise ValueError(
            "recommended_research_path must be one of: "
            + ", ".join(RECOMMENDED_RESEARCH_PATHS)
        )
    return value






def _runtime_requested_evidence_contract(
    *,
    formal_verification_policy: str,
    recommended_research_path: str = "",
    evaluation_mode: str = "debug",
    formal_target_semantic_review_required: bool = False,
) -> dict[str, Any]:
    policy = _normalized_formal_verification_policy(formal_verification_policy)
    path = _normalized_recommended_research_path(
        recommended_research_path,
        formal_verification_policy=policy,
    )
    research_evaluation = _is_runtime_research_evaluation_mode(evaluation_mode)
    capability_eval = str(evaluation_mode or "") == "capability_eval"
    contract = {
        "formal_verification_policy": policy,
        "recommended_research_path": path,
        "formal_required_for_final": policy == "required",
        "evaluation_mode": str(evaluation_mode or "debug"),
        "research_evaluation_requires_generated_algorithm_code": (
            research_evaluation
        ),
        "research_evaluation_requires_generated_simulation_code": (
            research_evaluation
        ),
        "research_evaluation_requires_generated_code_semantic_review": (
            research_evaluation
        ),
        "research_evaluation_requires_typed_metric_contracts": research_evaluation,
        "formal_evaluation_requires_formal_target_semantic_review": bool(
            capability_eval and formal_target_semantic_review_required
        ),
        "formal_evaluation_requires_formalizer_lean_candidate": capability_eval,
        "formal_target_authoring_required": bool(
            policy == "required" or capability_eval
        ),
        "formal_target_completion_policy": (
            "the task-specific mathematical target requires exact local "
            "Lean/kernel closure before final acceptance"
            if policy == "required"
            else "formal gaps must remain explicit when the task-specific target "
            "is not kernel verified"
        ),
        "simulation_target_authoring_required": True,
        "acceptance_modes": [
            "full source theorem kernel proof required"
            if policy == "required"
            else "research candidate may be reported with disclosed formal gaps"
            if policy == "advisory"
            else "Architect may select simulation-first, proof-first, or dual-track evidence"
        ],
        "disclosure_requirements": [
            "do not call LLM proposals, retrieval hits, simulations, or static rows proof evidence",
            "report formal verification level as none, partial, or full",
        ],
    }
    return contract


def _runtime_architect_context_with_requested_evidence_contract(
    context: Mapping[str, Any],
    *,
    formal_verification_policy: str,
    recommended_research_path: str = "",
    evaluation_mode: str = "debug",
    formal_target_semantic_review_required: bool = False,
) -> dict[str, Any]:
    payload = dict(context or {})
    requested_contract = _runtime_requested_evidence_contract(
        formal_verification_policy=formal_verification_policy,
        recommended_research_path=recommended_research_path,
        evaluation_mode=evaluation_mode,
        formal_target_semantic_review_required=(
            formal_target_semantic_review_required
        ),
    )
    existing_contract = payload.get("runtime_requested_evidence_contract", {})
    if isinstance(existing_contract, Mapping):
        requested_contract = {**requested_contract, **dict(existing_contract)}
    if _is_runtime_research_evaluation_mode(evaluation_mode):
        for requirement in (
            "generated_algorithm_code",
            "generated_simulation_code",
            "generated_code_semantic_review",
            "typed_metric_contracts",
        ):
            requested_contract[
                f"research_evaluation_requires_{requirement}"
            ] = True
    if str(evaluation_mode or "") == "capability_eval":
        requested_contract[
            "formal_evaluation_requires_formalizer_lean_candidate"
        ] = True
    elif str(evaluation_mode or "") == "research_eval":
        requested_contract[
            "formal_evaluation_requires_formalizer_lean_candidate"
        ] = False
        requested_contract[
            "formal_evaluation_requires_formal_target_semantic_review"
        ] = False
    payload["runtime_requested_evidence_contract"] = requested_contract
    payload["runtime_evaluation_mode"] = str(evaluation_mode or "debug")
    return payload








def _runtime_architect_operation(task: AgentTask) -> str:
    return str(task.inputs.get("runtime_architect_operation", "") or "").strip()


_THEORY_DESCENDANT_CONTEXT_FIELDS = (
    "accepted_generated_code_semantic_reviews",
    "accepted_implementation_interface_handoff",
    "algorithm_sandbox_manifest_id",
    "architect_theory_execution_preflight_acceptance",
    "confirmatory_simulation_requires_accepted_algorithm_handoff",
    "formalization_manifest_id",
    "formalizer_lean_candidate_materialization_manifest_id",
    "runtime_generated_code_semantic_review_replan",
    "runtime_generated_code_semantic_review_replan_resolution",
    "simulation_manifest_id",
    "theory_execution_preflight_packet_hash",
    "theory_execution_preflight_packet_id",
    "upstream_algorithm_handoff",
)


def _context_with_invalidated_theory_descendants(
    architect_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Retire active descendants when their immutable theory parent changes."""

    context = dict(architect_context)
    historical_fields = {
        "algorithm_sandbox_manifest_id": "previous_algorithm_sandbox_manifest_id",
        "formalization_manifest_id": "previous_formalization_manifest_id",
        "formalizer_lean_candidate_materialization_manifest_id": (
            "previous_formalizer_lean_candidate_materialization_manifest_id"
        ),
        "simulation_manifest_id": "previous_simulation_manifest_id",
    }
    for field in _THEORY_DESCENDANT_CONTEXT_FIELDS:
        value = context.pop(field, None)
        historical_field = historical_fields.get(field, "")
        if historical_field and value not in (None, "", [], {}):
            context[historical_field] = value
    return context


def _compiled_post_theory_workspace_owner(
    architect_context: Mapping[str, Any],
    *,
    implementation_gaps: Sequence[Mapping[str, Any]],
) -> str:
    """Compile the model-authored research path into its next workspace."""

    plan = _architect_runtime_plan(architect_context)
    contract = plan.get("evidence_contract", {})
    contract = contract if isinstance(contract, Mapping) else {}
    formal_policy = str(
        contract.get("formal_verification_policy", "") or "optional"
    ).strip()
    research_path = _normalized_recommended_research_path(
        contract.get("recommended_research_path", ""),
        formal_verification_policy=formal_policy,
    )
    planned = [
        str(row.get("subsystem", "") or "").strip()
        for row in plan.get("subsystem_execution_plan", []) or []
        if isinstance(row, Mapping)
    ]
    requires_algorithm = bool(
        implementation_gaps
        and _runtime_research_evaluation_contract_flag(
            contract,
            "generated_algorithm_code",
        )
    )
    if research_path == "proof_first":
        return "FormalizationEvaluator"
    if research_path == "simulation_first":
        return "AlgorithmEngineer" if requires_algorithm else "SimulationEvaluator"
    for subsystem in planned:
        if subsystem not in {
            "AlgorithmEngineer",
            "SimulationEvaluator",
            "FormalizationEvaluator",
        }:
            continue
        if subsystem == "SimulationEvaluator" and requires_algorithm:
            return "AlgorithmEngineer"
        if subsystem == "AlgorithmEngineer" and not implementation_gaps:
            continue
        return subsystem
    return "AlgorithmEngineer" if requires_algorithm else "FormalizationEvaluator"


def _architect_theory_preflight_accepted_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    preflight_packet: Mapping[str, Any],
    runtime_config: ResearchAgentRuntimeConfig,
    blackboard: BlackboardState,
) -> AgentStepResult:
    context = dict(architect_context)
    theory_material = context.get(
        "architect_metric_protocol_theory_material", {}
    )
    theory_material = (
        dict(theory_material) if isinstance(theory_material, Mapping) else {}
    )
    theory_packet_id = str(
        theory_material.get("source_theory_packet_id", "") or ""
    )
    theory_packet_hash = str(
        theory_material.get("source_theory_packet_hash", "") or ""
    )
    theory_packet = blackboard.artifacts.get(theory_packet_id, {})
    errors: list[str] = []
    if preflight_packet.get("overall_verdict") != "ACCEPT":
        errors.append("theory execution preflight was not accepted")
    if str(preflight_packet.get("source_theory_packet_id", "") or "") != (
        theory_packet_id
    ):
        errors.append("theory execution preflight theory identity mismatch")
    if str(preflight_packet.get("source_theory_packet_hash", "") or "") != (
        theory_packet_hash
    ):
        errors.append("theory execution preflight theory hash mismatch")
    if not isinstance(theory_packet, Mapping) or stable_hash(theory_packet) != (
        theory_packet_hash
    ):
        errors.append("theory execution preflight source packet is unavailable")
    if errors:
        return AgentStepResult(
            status="BLOCKED",
            rationale=(
                "ArchitectCoordinator rejected a stale or non-accepted theory "
                "preflight before implementation execution."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type="architect_theory_preflight_acceptance_rejected",
                    summary="; ".join(errors)[:500],
                    payload={
                        "validation_errors": errors,
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                ),
            ),
            failure_classification="architect_theory_preflight_acceptance_invalid",
        )

    preflight_packet_id = str(preflight_packet.get("packet_id", "") or "")
    preflight_packet_hash = stable_hash(preflight_packet)
    acceptance = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": (
            "RuntimeArchitectTheoryExecutionPreflightAcceptance"
        ),
        "question_id": question.id,
        "source_task_id": task.task_id,
        "source_theory_packet_id": theory_packet_id,
        "source_theory_packet_hash": theory_packet_hash,
        "preflight_packet_id": preflight_packet_id,
        "preflight_packet_hash": preflight_packet_hash,
        "theory_execution_preflight_packet": runtime_artifact_reference(
            preflight_packet_id,
            preflight_packet,
        ),
        "execution_results_observed": False,
        "full_metric_authoring_completed": False,
        "algorithm_execution_available": True,
        "algorithm_execution_authorized": False,
        "formalization_evaluation_available": True,
        "confirmatory_simulation_authorized": False,
        "runtime_selected_next_owner": False,
        "runtime_selected_semantics": False,
        "proof_evidence_status": (
            "ARCHITECT_THEORY_EXECUTION_PREFLIGHT_ACCEPTANCE_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "Independent source-grounded preflight accepted the current theory "
            "for downstream evidence work selected by the Architect model. It does "
            "not select a worker, freeze empirical metrics, authorize confirmatory "
            "simulation, accept statistical performance, or prove a theorem."
        ),
    }
    acceptance_identity_payload = deepcopy(acceptance)
    acceptance_identity_payload["theory_execution_preflight_packet"] = dict(
        preflight_packet
    )
    acceptance_id = (
        "architect_theory_execution_preflight_acceptance:"
        + stable_hash(acceptance_identity_payload)[:20]
    )
    acceptance["acceptance_id"] = acceptance_id
    context["architect_theory_execution_preflight_acceptance"] = (
        runtime_artifact_reference(acceptance_id, acceptance)
    )
    context["empirical_evaluation_phase"] = (
        EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
    )
    prior_metric_gate = context.get("architect_metric_protocol_gate", {})
    prior_metric_gate = (
        dict(prior_metric_gate)
        if isinstance(prior_metric_gate, Mapping)
        else {}
    )
    upstream_theory_revision_count = max(
        0,
        int(prior_metric_gate.get("upstream_theory_revision_count", 0) or 0),
    )
    max_upstream_theory_revisions = max(
        0,
        int(
            prior_metric_gate.get("max_upstream_theory_revisions", 0)
            or runtime_config.metric_protocol_max_upstream_theory_revisions
            or 0
        ),
    )
    context["architect_metric_protocol_gate"] = {
        **{
            key: value
            for key, value in prior_metric_gate.items()
            if key
            in {
                "rejection_manifest_ids",
                "source_theory_revision_feedback_id",
            }
        },
        "artifact_kind": "RuntimeArchitectMetricProtocolGate",
        "source_theory_packet_id": theory_packet_id,
        "source_theory_packet_hash": theory_packet_hash,
        "upstream_theory_revision_count": upstream_theory_revision_count,
        "max_upstream_theory_revisions": max_upstream_theory_revisions,
        "required_disposition": (
            "IMPLEMENTATION_ACCEPTED_BEFORE_METRIC_AUTHORING"
        ),
        "execution_authorized": False,
        "algorithm_execution_available": True,
        "algorithm_execution_authorized": False,
        "confirmatory_simulation_authorized": False,
        "consumed": False,
        "preflight_acceptance_id": acceptance_id,
        "preflight_acceptance_hash": stable_hash(acceptance),
        "proof_evidence_status": (
            "ARCHITECT_METRIC_PROTOCOL_GATE_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "If the Architect model selects AlgorithmEngineer, only exploratory "
            "execution is authorized and full metric authoring remains deferred "
            "until independent implementation review accepts a hash-bound executable "
            "interface. Formalization and theory review do not depend on that "
            "empirical sequence."
        ),
    }
    requires_generated_algorithm = bool(
        _architect_runtime_plan(context)
        .get("evidence_contract", {})
        .get("research_evaluation_requires_generated_algorithm_code")
        is True
    )
    implementation_gaps = _implementation_gaps(
        theory_packet,
        [],
        require_generated_adapter=requires_generated_algorithm,
    )
    context["implementation_gaps"] = implementation_gaps
    next_workspace_owner = _compiled_post_theory_workspace_owner(
        context,
        implementation_gaps=implementation_gaps,
    )
    route_feedback_body = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": (
            "RuntimeArchitectTheoryExecutionPreflightAcceptedObservation"
        ),
        "feedback_type": "theory_execution_preflight_accepted",
        "feedback_source": "ArchitectTheoryExecutionPreflightReviewer",
        "question_id": question.id,
        "source_task_id": task.task_id,
        "source_theory_packet_id": theory_packet_id,
        "source_theory_packet_hash": theory_packet_hash,
        "preflight_packet_id": preflight_packet_id,
        "preflight_packet_hash": preflight_packet_hash,
        "preflight_acceptance_id": acceptance_id,
        "preflight_acceptance_hash": stable_hash(acceptance),
        "overall_verdict": "ACCEPT",
        "implementation_target_available": bool(implementation_gaps),
        "n_implementation_gaps": len(implementation_gaps),
        "metric_authoring_deferred": True,
        "confirmatory_simulation_authorized": False,
        "compiled_next_owner": next_workspace_owner,
        "owner_selection_source": "model_authored_architect_plan",
        "runtime_authored_research_route": False,
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        "boundary": (
            "This observation records the next workspace compiled from the already "
            "validated model-authored Architect plan. Runtime does not make a new "
            "research decision or author implementation, simulation, or proof content."
        ),
    }
    route_feedback_id = (
        "architect_theory_execution_preflight_accepted_observation:"
        + stable_hash(route_feedback_body)[:20]
    )
    route_feedback = {
        **route_feedback_body,
        "feedback_id": route_feedback_id,
        "active_observation_id": route_feedback_id,
        "observation_status": "CURRENT_ACTIVE_OBSERVATION",
    }
    context["environment_feedback"] = route_feedback
    context["runtime_feedback_loop"] = {
        **(
            dict(context.get("runtime_feedback_loop", {}))
            if isinstance(context.get("runtime_feedback_loop", {}), Mapping)
            else {}
        ),
        "source_subsystem": "ArchitectTheoryExecutionPreflightReviewer",
        "preflight_acceptance_id": acceptance_id,
        "handoff": "accepted_theory_preflight_to_planned_workspace",
        "compiled_next_owner": next_workspace_owner,
        "runtime_authored_research_route": False,
    }
    runtime_plan = _architect_runtime_plan(context)
    routing_decision = _architect_initial_routing_decision(
        question=question,
        packet=runtime_plan,
        architect_context=context,
        packet_id=str(
            context.get("architect_coordinator_proposal_id", "")
            or runtime_plan.get("packet_id", "")
            or acceptance_id
        ),
        runtime_config=runtime_config,
        blackboard=blackboard,
        requested_subsystem_override=next_workspace_owner,
        routing_source_override="architect_plan_workspace_transition",
    )
    next_task = routing_decision["task"]
    evidence = EvidenceLedgerEntry(
        evidence_id=(
            "evidence:" + stable_hash([task.task_id, acceptance_id])[:20]
        ),
        task_id=task.task_id,
        artifact_id=acceptance_id,
        evidence_type="architect_theory_execution_preflight_acceptance",
        status="THEORY_PREFLIGHT_ACCEPTED_PLAN_TRANSITION_COMPILED",
        boundary=str(acceptance["boundary"]),
        payload={
            "source_theory_packet_id": theory_packet_id,
            "preflight_packet_id": preflight_packet_id,
            "algorithm_execution_available": True,
            "algorithm_execution_authorized": False,
            "confirmatory_simulation_authorized": False,
            "compiled_next_owner": next_task.owner_subsystem,
            "owner_selection_source": "model_authored_architect_plan",
            "runtime_authored_research_route": False,
            "proof_evidence_status": acceptance["proof_evidence_status"],
        },
    )
    return AgentStepResult(
        status="REROUTE",
        rationale=(
            "Independent theory preflight accepted. AgentRuntime recorded the "
            "immutable acceptance and compiled the existing Architect research path "
            f"into the {next_task.owner_subsystem} workspace without another model "
            "routing call."
        ),
        produced_artifacts={
            preflight_packet_id: dict(preflight_packet),
            acceptance_id: acceptance,
            route_feedback_id: route_feedback,
        },
        observations=(
            EnvironmentObservation(
                observation_type="architect_theory_preflight_accepted",
                summary=(
                    "preflight accepted; existing Architect plan compiled directly "
                    "to the next workspace"
                ),
                payload={
                    "acceptance_id": acceptance_id,
                    "preflight_packet_id": preflight_packet_id,
                    "next_owner_subsystem": next_task.owner_subsystem,
                    "owner_selection_source": "model_authored_architect_plan",
                    "runtime_authored_research_route": False,
                    "execution_results_observed": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                },
            ),
        ),
        evidence_entries=(evidence,),
        next_task=next_task,
    )


_METRIC_AUTHORING_CONTEXT_FIELDS = frozenset(
    {
        "theory_packet_id",
        "previous_theory_packet_id",
        "retrieval_context",
        "retrieval_memory_manifest_id",
        "architect_runtime_plan",
        "runtime_requested_evidence_contract",
        "runtime_evaluation_mode",
        "architect_metric_protocol_theory_material",
        "architect_metric_protocol_gate",
        "architect_theory_execution_preflight_acceptance",
        "architect_metric_protocol_prior_rejection",
        "implementation_gaps",
    }
)


def _architect_post_implementation_metric_context(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    context = dict(architect_context)
    theory_packet_id = _architect_context_theory_packet_id(context)
    algorithm_manifest_id = _architect_context_algorithm_sandbox_manifest_id(
        context
    )
    raw_handoff = context.get("upstream_algorithm_handoff", {})
    validated_handoff = _runtime_validated_algorithm_handoff(
        architect_context=context,
        blackboard=blackboard,
        question_id=question.id,
        theory_packet_id=theory_packet_id,
        algorithm_sandbox_manifest_id=algorithm_manifest_id,
        upstream_algorithm_handoff=(
            raw_handoff if isinstance(raw_handoff, Mapping) else {}
        ),
    )
    errors: list[str] = []
    if not validated_handoff:
        errors.append(
            "post-implementation metric authoring requires a validated accepted "
            "AlgorithmEngineer handoff"
        )
        return {}, {}, errors
    interface_handoff = build_accepted_implementation_interface_handoff(
        validated_handoff
    )
    errors.extend(
        accepted_implementation_interface_handoff_errors(
            interface_handoff,
            question_id=question.id,
            theory_packet_id=theory_packet_id,
        )
    )
    proposal_context = {
        key: deepcopy(context[key])
        for key in _METRIC_AUTHORING_CONTEXT_FIELDS
        if key in context
    }
    proposal_context["accepted_implementation_interface_handoff"] = (
        interface_handoff
    )
    proposal_context["runtime_architect_operation"] = (
        RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC
    )
    return proposal_context, interface_handoff, errors


def _architect_feedback_runtime_progress_snapshot(
    blackboard: BlackboardState,
) -> dict[str, Any]:
    """Expose current runtime state without interpreting or selecting a route."""

    recent_handoffs = []
    for handoff in blackboard.handoff_ledger[-16:]:
        recent_handoffs.append(
            {
                "from_task_id": handoff.from_task_id,
                "to_task_id": handoff.to_task_id,
                "from_subsystem": handoff.from_subsystem,
                "to_subsystem": handoff.to_subsystem,
                "status": handoff.status,
                "produced_artifact_ids": list(handoff.produced_artifact_ids),
                "failure_classification": handoff.failure_classification,
            }
        )
    return {
        "schema_version": 1,
        "project_id": blackboard.project_id,
        "available_artifact_ids": list(blackboard.artifacts)[-24:],
        "recent_task_ids": list(blackboard.task_history)[-24:],
        "recent_handoffs": recent_handoffs,
        "active_blockers": list(blackboard.active_blockers)[-12:],
        "boundary": (
            "This is an authoritative inventory of runtime availability and recent "
            "execution state. It does not judge artifact quality, select a worker, "
            "or authorize evidence promotion."
        ),
    }


class ArchitectCoordinatorRuntimeSubsystem:
    name = "ArchitectCoordinator"

    def __init__(
        self,
        *,
        coordinator: LLMArchitectCoordinatorAgent,
        runtime_config: ResearchAgentRuntimeConfig,
        proof_search_tool_available: bool = False,
    ) -> None:
        self.coordinator = coordinator
        self.runtime_config = runtime_config
        self.proof_search_tool_available = bool(proof_search_tool_available)

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        resume_pending_task_payload = (
            task.inputs.get("resume_pending_task", {})
            if isinstance(task.inputs.get("resume_pending_task", {}), Mapping)
            else {}
        )
        if resume_pending_task_payload:
            context["runtime_resume_review"] = {
                "artifact_kind": "RuntimeArchitectResumeReviewContext",
                "pending_task_id": str(
                    resume_pending_task_payload.get("task_id", "") or ""
                ),
                "pending_owner_subsystem": str(
                    resume_pending_task_payload.get("owner_subsystem", "") or ""
                ),
                "pending_acceptance_gate": str(
                    resume_pending_task_payload.get("acceptance_gate", "") or ""
                ),
                "boundary": (
                    "This is Architect resume-routing context. It is not proof "
                    "evidence and does not imply that any theorem gap is closed."
                ),
            }
        architect_operation = _runtime_architect_operation(task)
        if architect_operation == RUNTIME_ARCHITECT_OPERATION_THEORY_PREFLIGHT:
            context = (
                _architect_context_with_rehydrated_metric_protocol_theory_material(
                    architect_context=context,
                    blackboard=blackboard,
                )
            )
            runtime_config_payload = asdict(self.runtime_config)
            runtime_config_payload["proof_search_tool_available"] = (
                self.proof_search_tool_available
            )
            try:
                preflight_packet = (
                    self.coordinator.review_theory_execution_preflight(
                        question=question,
                        architect_context=context,
                        runtime_config=runtime_config_payload,
                    )
                )
            except ArchitectMetricSemanticReviewRejected as exc:
                return architect_preexecution_metric_protocol_rejection_result(
                    task=task,
                    question=question,
                    semantic_review_history=exc.semantic_review_history,
                    architect_context=context,
                    max_upstream_theory_revisions=(
                        self.runtime_config.metric_protocol_max_upstream_theory_revisions
                    ),
                )
            except PacketValidationError as exc:
                return architect_metric_semantic_review_validation_failure_result(
                    task=task,
                    question=question,
                    architect_context=context,
                    exc=exc,
                    review_stage="theory_execution_preflight",
                )
            except ValueError as exc:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "ArchitectCoordinator rejected an unavailable or invalid "
                        "theory preflight contract before implementation."
                    ),
                    observations=(
                        EnvironmentObservation(
                            observation_type=(
                                "architect_theory_preflight_contract_rejected"
                            ),
                            summary=str(exc)[:500],
                            payload={
                                "model_call_authorized": False,
                                "implementation_authorized": False,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    failure_classification=(
                        "architect_theory_preflight_contract_invalid"
                    ),
                )
            return _architect_theory_preflight_accepted_result(
                task=task,
                question=question,
                architect_context=context,
                preflight_packet=preflight_packet,
                runtime_config=self.runtime_config,
                blackboard=blackboard,
            )
        if architect_operation == ARCHITECT_FEEDBACK_ROUTE_OPERATION:
            environment_feedback = task.inputs.get("environment_feedback", {})
            if not isinstance(environment_feedback, Mapping) or not environment_feedback:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "ArchitectCoordinator feedback routing requires immutable "
                        "environment observations before a model call."
                    ),
                    observations=(
                        EnvironmentObservation(
                            observation_type="architect_feedback_route_input_rejected",
                            summary="environment_feedback is missing or empty",
                            payload={
                                "model_call_authorized": False,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    failure_classification="architect_feedback_route_input_invalid",
                )
            for lineage_key in (
                "theory_packet_id",
                "simulation_manifest_id",
                "algorithm_sandbox_manifest_id",
                "formalization_manifest_id",
            ):
                lineage_value = str(task.inputs.get(lineage_key, "") or "").strip()
                if lineage_value:
                    context[lineage_key] = lineage_value
            try:
                feedback_architect_context = dict(context)
                feedback_architect_context["runtime_progress_snapshot"] = (
                    _architect_feedback_runtime_progress_snapshot(blackboard)
                )
                route_packet = self.coordinator.route_environment_feedback(
                    question=question,
                    architect_context=feedback_architect_context,
                    environment_feedback=environment_feedback,
                )
            except PacketValidationError as exc:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "The Architect model did not produce a valid compact feedback "
                        "route after complete-packet regeneration."
                    ),
                    observations=(
                        EnvironmentObservation(
                            observation_type="architect_feedback_route_validation_failed",
                            summary="; ".join(exc.errors)[:500],
                            payload={
                                "validation_errors": list(exc.errors),
                                "generation_history": list(exc.history),
                                "environment_feedback_fingerprint": stable_hash(
                                    dict(environment_feedback)
                                ),
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    failure_classification=(
                        "architect_feedback_route_packet_validation_failed"
                    ),
                )
            feedback_fingerprint = stable_hash(dict(environment_feedback))
            if str(
                route_packet.get("environment_feedback_fingerprint", "") or ""
            ) != feedback_fingerprint:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "Architect feedback-route identity did not match the current "
                        "immutable environment observations."
                    ),
                    failure_classification="architect_feedback_route_lineage_mismatch",
                )
            decision_id = str(
                route_packet.get("route_decision_id", "") or ""
            ).strip()
            route_artifact = deepcopy(dict(route_packet))
            route_evidence = EvidenceLedgerEntry(
                evidence_id=(
                    "evidence:" + stable_hash([task.task_id, decision_id])[:20]
                ),
                task_id=task.task_id,
                artifact_id=decision_id,
                evidence_type="llm_architect_feedback_route",
                status=(
                    "MODEL_RECORDED_TYPED_BLOCKER"
                    if route_packet.get("decision") == "BLOCK"
                    else "MODEL_ROUTE_RECORDED_REQUIRES_RUNTIME_EXECUTION"
                ),
                boundary=ARCHITECT_COORDINATOR_BOUNDARY,
                payload={
                    "runtime_executed": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                },
            )
            if route_packet.get("decision") == "BLOCK":
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=str(route_packet.get("rationale", "") or ""),
                    produced_artifacts={decision_id: route_artifact},
                    observations=(
                        EnvironmentObservation(
                            observation_type="architect_feedback_route_blocked",
                            summary=str(route_packet.get("rationale", "") or "")[:500],
                            payload={
                                "route_decision_id": decision_id,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    evidence_entries=(route_evidence,),
                    failure_classification="architect_feedback_route_blocked",
                )

            context["architect_feedback_route_decision"] = route_artifact
            context["environment_feedback"] = deepcopy(dict(environment_feedback))
            runtime_plan = _architect_runtime_plan(context)
            selected_subsystem = str(
                route_packet.get("selected_subsystem", "") or ""
            ).strip()
            if (
                selected_subsystem == "CriticEvaluator"
                and str(environment_feedback.get("feedback_type", "") or "")
                == "critic_architect_replan_observations"
            ):
                feedback_loop = (
                    dict(context.get("runtime_feedback_loop", {}))
                    if isinstance(context.get("runtime_feedback_loop", {}), Mapping)
                    else {}
                )
                feedback_loop["critic_revision_round"] = (
                    _int_like(feedback_loop.get("critic_revision_round", 0)) + 1
                )
                context["runtime_feedback_loop"] = feedback_loop
            routing_decision = _architect_initial_routing_decision(
                question=question,
                packet={
                    "packet_id": decision_id,
                    "evidence_contract": deepcopy(
                        runtime_plan.get("evidence_contract", {})
                    ),
                    "subsystem_execution_plan": deepcopy(
                        runtime_plan.get("subsystem_execution_plan", [])
                    ),
                    "next_actions": [
                        {
                            "owner_agent": selected_subsystem,
                            "action": str(route_packet.get("objective", "") or ""),
                            "acceptance_gate": _architect_acceptance_gate(
                                context,
                                selected_subsystem,
                                "new environment evidence or a typed blocker is recorded",
                            ),
                        }
                    ],
                },
                architect_context=context,
                packet_id=decision_id,
                runtime_config=self.runtime_config,
                blackboard=blackboard,
                requested_subsystem_override=selected_subsystem,
                routing_source_override="architect_feedback_route_model",
                honor_requested_subsystem=True,
            )
            next_task = routing_decision["task"]
            return AgentStepResult(
                status="REROUTE",
                rationale=str(route_packet.get("rationale", "") or ""),
                produced_artifacts={decision_id: route_artifact},
                observations=(
                    EnvironmentObservation(
                        observation_type="llm_architect_feedback_route",
                        summary=(
                            f"Architect model selected {selected_subsystem}; runtime "
                            "materialized that exact existing-agent route."
                        ),
                        payload={
                            "route_decision_id": decision_id,
                            "model_requested_subsystem": selected_subsystem,
                            "selected_subsystem": next_task.owner_subsystem,
                            "runtime_owner_override_applied": False,
                            "full_research_plan_regenerated": False,
                            "runtime_authored_candidate_fix": False,
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                evidence_entries=(route_evidence,),
                next_task=next_task,
            )
        context = _architect_context_with_rehydrated_metric_protocol_theory_material(
            architect_context=context,
            blackboard=blackboard,
        )
        runtime_config_payload = asdict(self.runtime_config)
        runtime_config_payload["proof_search_tool_available"] = (
            self.proof_search_tool_available
        )
        proposal_context = context
        if (
            architect_operation
            == RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC
        ):
            (
                proposal_context,
                implementation_interface_handoff,
                implementation_context_errors,
            ) = _architect_post_implementation_metric_context(
                question=question,
                architect_context=context,
                blackboard=blackboard,
            )
            if implementation_context_errors:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "ArchitectCoordinator rejected post-implementation metric "
                        "authoring before any model call because accepted code "
                        "lineage was missing or inconsistent."
                    ),
                    observations=(
                        EnvironmentObservation(
                            observation_type=(
                                "post_implementation_metric_authoring_input_rejected"
                            ),
                            summary="; ".join(
                                implementation_context_errors
                            )[:500],
                            payload={
                                "validation_errors": (
                                    implementation_context_errors
                                ),
                                "model_call_authorized": False,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    failure_classification=(
                        "post_implementation_metric_authoring_lineage_invalid"
                    ),
                )
            context["accepted_implementation_interface_handoff"] = (
                implementation_interface_handoff
            )
            context["algorithm_sandbox_manifest_id"] = str(
                implementation_interface_handoff.get(
                    "algorithm_sandbox_manifest_id", ""
                )
                or ""
            )
            metric_gate = context.get("architect_metric_protocol_gate", {})
            if isinstance(metric_gate, Mapping):
                metric_gate = dict(metric_gate)
                metric_gate["required_disposition"] = (
                    "PREEXECUTION_REVIEW_ACCEPTED"
                )
                metric_gate["implementation_interface_handoff_id"] = str(
                    implementation_interface_handoff.get("handoff_id", "")
                    or ""
                )
                metric_gate["implementation_interface_handoff_hash"] = (
                    stable_hash(implementation_interface_handoff)
                )
                context["architect_metric_protocol_gate"] = metric_gate
                proposal_context["architect_metric_protocol_gate"] = dict(
                    metric_gate
                )
        try:
            packet = self.coordinator.propose(
                question=question,
                architect_context=proposal_context,
                runtime_config=runtime_config_payload,
            )
        except ArchitectMetricSemanticReviewRejected as exc:
            return architect_preexecution_metric_protocol_rejection_result(
                task=task,
                question=question,
                semantic_review_history=exc.semantic_review_history,
                architect_context=context,
                max_upstream_theory_revisions=(
                    self.runtime_config.metric_protocol_max_upstream_theory_revisions
                ),
            )
        except PacketValidationError as exc:
            if exc.validation_label == "LLM Architect metric-requirement packet":
                return architect_metric_requirement_validation_failure_result(
                    task=task,
                    question=question,
                    architect_context=context,
                    blackboard=blackboard,
                    exc=exc,
                    max_upstream_theory_revisions=(
                        self.runtime_config.metric_protocol_max_upstream_theory_revisions
                    ),
                    runtime_architect_control=_architect_control_payload(
                        invalidate_metric_protocol_authorization(context),
                        "ArchitectCoordinator",
                    ),
                )
            if exc.validation_label in {
                "Architect metric semantic review packet",
                "Architect theory-to-execution preflight review packet",
            }:
                return architect_metric_semantic_review_validation_failure_result(
                    task=task,
                    question=question,
                    architect_context=context,
                    exc=exc,
                )
            raise
        except ValueError as exc:
            if (
                architect_operation
                != RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC
            ):
                raise
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "Post-implementation metric authoring rejected a stale or "
                    "incomplete result-blind contract before execution."
                ),
                observations=(
                    EnvironmentObservation(
                        observation_type=(
                            "post_implementation_metric_authoring_contract_rejected"
                        ),
                        summary=str(exc)[:500],
                        payload={
                            "confirmatory_simulation_authorized": False,
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                failure_classification=(
                    "post_implementation_metric_authoring_contract_invalid"
                ),
            )
        packet_id = str(packet["packet_id"])
        context["architect_coordinator_proposal_id"] = packet_id
        context["architect_runtime_plan"] = {
            field: deepcopy(packet.get(field))
            for field in (
                "problem_analysis",
                "evidence_contract",
                "subsystem_execution_plan",
                "retrieval_strategy",
                "iteration_policy",
                "next_actions",
            )
        }
        context["architect_runtime_plan"].update({
            "subsystem_execution_plan_provenance": packet.get(
                "subsystem_execution_plan_provenance", {}
            ),
            "validated_plan_reuse_metadata": (
                architect_validated_plan_reuse_metadata(
                    packet,
                    question_id=question.id,
                )
            ),
            "boundary": packet.get("evidence_boundary", ARCHITECT_COORDINATOR_BOUNDARY),
        })
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, packet_id])[:20],
            task_id=task.task_id,
            artifact_id=packet_id,
            evidence_type="llm_architect_coordinator_proposal",
            status="PROPOSAL_RECORDED_REQUIRES_RUNTIME_EXECUTION",
            boundary=ARCHITECT_COORDINATOR_BOUNDARY,
            payload={
                "n_subsystem_steps": len(packet.get("subsystem_execution_plan", []) or []),
                "subsystem_execution_plan_provenance": packet.get(
                    "subsystem_execution_plan_provenance", {}
                ),
                "validated_plan_reuse_provenance": packet.get(
                    "validated_plan_reuse_provenance", {}
                ),
                "fresh_architect_plan_model_invocation": packet.get(
                    "fresh_architect_plan_model_invocation", True
                ),
                "evidence_contract": packet.get("evidence_contract", {}),
                "runtime_executed": False,
                "proof_evidence_status": ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE,
            },
        )
        continuation_owner = ""
        continuation_source = ""
        if (
            architect_operation
            == RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC
        ):
            continuation_owner = _architect_metric_protocol_execution_owner(
                packet
            )
            continuation_source = "accepted_metric_protocol_target"
            if not continuation_owner:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "The independently accepted metric protocol did not resolve "
                        "to exactly one runtime execution owner from its declared "
                        "target namespace."
                    ),
                    produced_artifacts={packet_id: packet},
                    observations=(
                        EnvironmentObservation(
                            observation_type=(
                                "accepted_metric_protocol_execution_owner_invalid"
                            ),
                            summary=(
                                "validated metric targets do not resolve to one "
                                "runtime execution owner"
                            ),
                            payload={
                                "metric_requirement_set_id": str(
                                    packet.get("evidence_contract", {}).get(
                                        "empirical_metric_requirement_set_id",
                                        "",
                                    )
                                    if isinstance(
                                        packet.get("evidence_contract", {}),
                                        Mapping,
                                    )
                                    else ""
                                ),
                                "model_call_completed": True,
                                "runtime_authored_metric_target": False,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    evidence_entries=(evidence,),
                    failure_classification=(
                        "accepted_metric_protocol_execution_owner_invalid"
                    ),
                )
        routing_decision = _architect_initial_routing_decision(
            question=question,
            packet=packet,
            architect_context=context,
            packet_id=packet_id,
            runtime_config=self.runtime_config,
            blackboard=blackboard,
            requested_subsystem_override=continuation_owner,
            routing_source_override=continuation_source,
        )
        context["architect_initial_routing"] = routing_decision["record"]
        next_task = routing_decision["task"]
        rationale = str(routing_decision["rationale"])
        return AgentStepResult(
            status="REROUTE",
            rationale=rationale,
            produced_artifacts={packet_id: packet},
            observations=(
                EnvironmentObservation(
                    observation_type="llm_architect_coordinator_proposal",
                    summary=(
                        "validated ArchitectCoordinator resume review recorded"
                        if resume_pending_task_payload
                        else "validated ArchitectCoordinator execution plan recorded"
                    ),
                    payload={
                        "packet_id": packet_id,
                        "n_subsystem_steps": len(packet.get("subsystem_execution_plan", []) or []),
                        "subsystem_execution_plan_provenance": packet.get(
                            "subsystem_execution_plan_provenance", {}
                        ),
                        "evidence_contract": packet.get("evidence_contract", {}),
                        "resume_review": bool(resume_pending_task_payload),
                        "resume_pending_task_id": str(
                            resume_pending_task_payload.get("task_id", "") or ""
                        ),
                        "initial_routing": routing_decision["record"],
                        "proof_evidence_status": ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE,
                    },
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
        )


def _architect_context_with_bound_metric_protocol_theory_material(
    *,
    architect_context: Mapping[str, Any],
    theory_material: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind metric execution authority to the exact current theory artifact."""

    context = dict(architect_context)
    material = dict(theory_material)
    context["architect_metric_protocol_theory_material"] = material
    theory_packet_id = str(
        material.get("source_theory_packet_id", "") or ""
    )
    theory_packet_hash = str(
        material.get("source_theory_packet_hash", "") or ""
    )
    if not theory_packet_id or not theory_packet_hash:
        return context

    prior_contract = _architect_runtime_plan(context).get("evidence_contract", {})
    if not isinstance(prior_contract, Mapping):
        prior_contract = {}
    prior_review = prior_contract.get(
        "empirical_metric_requirements_preexecution_review", {}
    )
    if not isinstance(prior_review, Mapping):
        prior_review = {}
    accepted_authoring = context.get(
        "architect_metric_requirement_authoring", {}
    )
    metric_protocol_already_authorized = (
        reviewed_metric_protocol_authority_matches_theory(
            evidence_contract=prior_contract,
            metric_authoring=(
                accepted_authoring
                if isinstance(accepted_authoring, Mapping)
                else {}
            ),
            theory_material=material,
        )
    )
    if not metric_protocol_already_authorized:
        prior_gate = context.get("architect_metric_protocol_gate", {})
        if not isinstance(prior_gate, Mapping):
            prior_gate = {}
        context["architect_metric_protocol_gate"] = {
            **{
                key: value
                for key, value in prior_gate.items()
                if key
                in {
                    "rejection_manifest_ids",
                    "upstream_theory_revision_count",
                    "max_upstream_theory_revisions",
                    "source_theory_revision_feedback_id",
                }
            },
            "artifact_kind": "RuntimeArchitectMetricProtocolGate",
            "source_theory_packet_id": theory_packet_id,
            "source_theory_packet_hash": theory_packet_hash,
            "required_disposition": "PREEXECUTION_REVIEW_ACCEPTED",
            "execution_authorized": False,
            "consumed": False,
            "rehydrated_from_blackboard": True,
            "proof_evidence_status": (
                "ARCHITECT_METRIC_PROTOCOL_GATE_NOT_PROOF_EVIDENCE"
            ),
            "boundary": (
                "Metric execution authority is valid only for the exact source "
                "TheoryDeveloper packet ID and hash reviewed before execution. A "
                "new theory packet invalidates prior authorization without erasing "
                "its repair history; neither packet is proof evidence."
            ),
        }
        prior_claimed_authority = bool(
            prior_contract.get("metric_protocol_execution_authorized") is True
            or (
                isinstance(accepted_authoring, Mapping)
                and accepted_authoring.get("semantic_review_status") == "ACCEPT"
            )
        )
        if prior_claimed_authority:
            context["architect_metric_protocol_authority_invalidation"] = {
                "artifact_kind": (
                    "RuntimeMetricProtocolTheoryLineageInvalidation"
                ),
                "current_source_theory_packet_id": theory_packet_id,
                "current_source_theory_packet_hash": theory_packet_hash,
                "prior_contract_source_theory_packet_id": str(
                    prior_review.get("source_theory_packet_id", "") or ""
                ),
                "prior_contract_source_theory_packet_hash": str(
                    prior_review.get("source_theory_packet_hash", "") or ""
                ),
                "prior_authoring_source_theory_packet_id": str(
                    accepted_authoring.get("source_theory_packet_id", "")
                    if isinstance(accepted_authoring, Mapping)
                    else ""
                ),
                "prior_authoring_source_theory_packet_hash": str(
                    accepted_authoring.get("source_theory_packet_hash", "")
                    if isinstance(accepted_authoring, Mapping)
                    else ""
                ),
                "execution_authorized": False,
                "proof_evidence_status": (
                    "METRIC_PROTOCOL_THEORY_LINEAGE_INVALIDATION_NOT_PROOF_EVIDENCE"
                ),
            }
    else:
        context.pop("architect_metric_protocol_authority_invalidation", None)
    return context


def _architect_packet_metric_protocol_authority_matches_current_theory(
    *,
    packet: Mapping[str, Any],
    architect_context: Mapping[str, Any],
) -> bool:
    evidence_contract = packet.get("evidence_contract", {})
    evidence_contract = (
        evidence_contract if isinstance(evidence_contract, Mapping) else {}
    )
    metric_authoring = packet.get("metric_requirement_authoring", {})
    metric_authoring = (
        metric_authoring if isinstance(metric_authoring, Mapping) else {}
    )
    theory_material = architect_context.get(
        "architect_metric_protocol_theory_material", {}
    )
    theory_material = (
        theory_material if isinstance(theory_material, Mapping) else {}
    )
    return reviewed_metric_protocol_authority_matches_theory(
        evidence_contract=evidence_contract,
        metric_authoring=metric_authoring,
        theory_material=theory_material,
    )


def _architect_context_with_rehydrated_metric_protocol_theory_material(
    *,
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
) -> dict[str, Any]:
    context = dict(architect_context)
    context.pop("architect_metric_protocol_prior_rejection", None)
    existing = context.get("architect_metric_protocol_theory_material", {})
    theory_material = dict(existing) if isinstance(existing, Mapping) else {}
    theory_packet_id = _architect_context_theory_packet_id(context)
    if theory_packet_id:
        theory_packet = blackboard.artifacts.get(theory_packet_id, {})
        if isinstance(theory_packet, Mapping) and theory_packet:
            theory_material = build_theory_informed_metric_protocol_material(
                theory_packet=theory_packet,
                theory_packet_id=theory_packet_id,
                retrieval_context=(
                    context.get("retrieval_context", {})
                    if isinstance(context.get("retrieval_context", {}), Mapping)
                    else {}
                ),
            )
        elif str(
            theory_material.get("source_theory_packet_id", "") or ""
        ) != theory_packet_id:
            return context
    if not theory_material:
        return context
    context = _architect_context_with_bound_metric_protocol_theory_material(
        architect_context=context,
        theory_material=theory_material,
    )
    prior_rejection = _architect_metric_protocol_prior_rejection_context(
        architect_context=context,
        blackboard=blackboard,
        current_theory_material=theory_material,
    )
    if prior_rejection:
        context["architect_metric_protocol_prior_rejection"] = prior_rejection
    return context


def _runtime_exact_algorithm_artifacts(
    review_material: Mapping[str, Any],
) -> list[dict[str, Any]]:
    exact_artifacts: list[dict[str, Any]] = []
    for raw_row in review_material.get("exact_executed_artifacts", []) or []:
        if not isinstance(raw_row, Mapping):
            continue
        source_row = raw_row.get("source_row", {})
        source = str(raw_row.get("exact_source_code", "") or "")
        result = raw_row.get("exact_result", {})
        if not (
            isinstance(source_row, Mapping)
            and source
            and isinstance(result, Mapping)
            and source_row.get("smoke_passed") is True
            and str(source_row.get("script_hash", "") or "")
            == stable_hash(source)
            and str(source_row.get("result_hash", "") or "")
            == stable_hash(result)
            and str(raw_row.get("exact_source_hash", "") or "")
            == stable_hash(source)
            and str(raw_row.get("exact_result_hash", "") or "")
            == stable_hash(result)
        ):
            continue
        exact_artifact = {
            "estimator_id": str(
                source_row.get("estimator_id", "")
                or raw_row.get("artifact_id", "")
                or ""
            ),
            "language": str(source_row.get("language", "") or ""),
            "dependencies": list(source_row.get("dependencies", []) or []),
            "exact_source_code": source,
            "exact_source_hash": stable_hash(source),
            "exact_smoke_result": dict(result),
            "exact_smoke_result_hash": stable_hash(result),
        }
        proposal_target = source_row.get(
            "llm_algorithm_engineer_target",
            {},
        )
        proposal_target = (
            proposal_target
            if isinstance(proposal_target, Mapping)
            else {}
        )
        interface_contract = proposal_target.get(
            "estimator_interface_contract",
            {},
        )
        if isinstance(interface_contract, Mapping) and interface_contract:
            exact_artifact["estimator_interface_contract"] = dict(
                interface_contract
            )
            exact_artifact["estimator_interface_contract_id"] = str(
                proposal_target.get(
                    "estimator_interface_contract_id",
                    "",
                )
                or (
                    "estimator_interface_contract:"
                    + stable_hash(interface_contract)[:20]
                )
            )
            interface_authority = proposal_target.get(
                "estimator_interface_contract_authority",
                {},
            )
            if isinstance(interface_authority, Mapping) and interface_authority:
                exact_artifact["estimator_interface_contract_authority"] = dict(
                    interface_authority
                )
        exact_artifacts.append(exact_artifact)
    return exact_artifacts


def _runtime_materialized_exact_algorithm_artifacts(
    materialization: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Validate the compact executable projection retained after review."""

    exact_artifacts: list[dict[str, Any]] = []
    for raw_row in materialization.get("exact_algorithm_artifacts", []) or []:
        if not isinstance(raw_row, Mapping):
            return []
        row = deepcopy(dict(raw_row))
        source = str(row.get("exact_source_code", "") or "")
        result = row.get("exact_smoke_result", {})
        if not (
            str(row.get("estimator_id", "") or "").strip()
            and source
            and isinstance(result, Mapping)
            and str(row.get("exact_source_hash", "") or "")
            == stable_hash(source)
            and str(row.get("exact_smoke_result_hash", "") or "")
            == stable_hash(dict(result))
        ):
            return []
        exact_artifacts.append(row)
    return exact_artifacts


def _runtime_accepted_algorithm_handoff_from_review(
    *,
    question_id: str,
    theory_packet_id: str,
    source_manifest: Mapping[str, Any],
    review_material: Mapping[str, Any],
    execution_manifest: Mapping[str, Any],
    review_packet: Mapping[str, Any],
) -> dict[str, Any]:
    exact_artifacts = _runtime_exact_algorithm_artifacts(review_material)
    if not exact_artifacts:
        return {}
    payload = {
        "source": "accepted_algorithm_semantic_review_materialization",
        "question_id": question_id,
        "algorithm_sandbox_manifest_id": str(
            source_manifest.get("manifest_id", "") or ""
        ),
        "algorithm_sandbox_manifest_hash": stable_hash(source_manifest),
        "semantic_review_execution_id": str(
            execution_manifest.get("execution_id", "") or ""
        ),
        "semantic_review_packet_id": str(review_packet.get("packet_id", "") or ""),
        "semantic_review_packet_hash": stable_hash(review_packet),
        "materialization_id": str(
            execution_manifest.get("materialization_id", "") or ""
        ),
        "materialization_hash": str(
            execution_manifest.get("materialization_hash", "") or ""
        ),
        "theory_packet_id": theory_packet_id,
        "exact_algorithm_artifacts": exact_artifacts,
        "consumption_contract": (
            "Confirmatory SimulationEngineer evaluates these exact reviewed "
            "implementations and may not silently substitute a new estimator."
        ),
        "proof_evidence_status": "ACCEPTED_ALGORITHM_HANDOFF_NOT_PROOF_EVIDENCE",
        "boundary": (
            "This is executable implementation lineage, not confirmatory "
            "statistical acceptance or theorem proof."
        ),
    }
    payload["handoff_id"] = "accepted_algorithm_handoff:" + stable_hash(payload)[:20]
    return payload


def _runtime_retire_resolved_generated_code_semantic_review_replan(
    *,
    architect_context: Mapping[str, Any],
    accepted_review: Mapping[str, Any],
) -> dict[str, Any]:
    context = dict(architect_context)
    replan = context.get("runtime_generated_code_semantic_review_replan", {})
    if not isinstance(replan, Mapping) or not replan:
        return context
    rejected_manifest_id = str(replan.get("source_manifest_id", "") or "")
    rejected_subsystem = str(replan.get("source_subsystem", "") or "")
    accepted_manifest_id = str(
        accepted_review.get("source_manifest_id", "") or ""
    )
    accepted_subsystem = str(
        accepted_review.get("source_subsystem", "") or ""
    )
    if not (
        accepted_review.get("overall_verdict") == "ACCEPT"
        and rejected_manifest_id
        and rejected_subsystem
        and accepted_manifest_id
        and accepted_subsystem == rejected_subsystem
        and accepted_manifest_id != rejected_manifest_id
    ):
        return context

    resolution = {
        "artifact_kind": (
            "RuntimeGeneratedCodeSemanticReviewReplanResolution"
        ),
        "accepted_source_subsystem": str(
            accepted_review.get("source_subsystem", "") or ""
        ),
        "rejected_source_subsystem": str(
            replan.get("source_subsystem", "") or ""
        ),
        "rejected_source_manifest_id": rejected_manifest_id,
        "rejected_review_execution_id": str(
            replan.get("review_execution_id", "") or ""
        ),
        "accepted_source_manifest_id": accepted_manifest_id,
        "accepted_source_manifest_hash": str(
            accepted_review.get("source_manifest_hash", "") or ""
        ),
        "accepted_review_packet_id": str(
            accepted_review.get("review_packet_id", "") or ""
        ),
        "accepted_review_execution_id": str(
            accepted_review.get("execution_id", "") or ""
        ),
        "resolution_status": "SUPERSEDED_BY_FRESH_ACCEPTED_ARTIFACT",
        "next_subsystem_was_model_selected": True,
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_REPLAN_RESOLUTION_NOT_PROOF_EVIDENCE"
        ),
    }
    resolution["resolution_id"] = (
        "generated_code_semantic_review_replan_resolution:"
        + stable_hash(resolution)[:20]
    )
    context["runtime_generated_code_semantic_review_replan_resolution"] = (
        resolution
    )
    context.pop("runtime_generated_code_semantic_review_replan", None)

    stale_execution_id = str(replan.get("review_execution_id", "") or "")
    environment_feedback = context.get("environment_feedback", {})
    if isinstance(environment_feedback, Mapping) and (
        str(
            environment_feedback.get("semantic_review_execution_id", "")
            or ""
        )
        == stale_execution_id
        or str(environment_feedback.get("source_manifest_id", "") or "")
        == rejected_manifest_id
    ):
        context.pop("environment_feedback", None)
    feedback_loop = context.get("runtime_feedback_loop", {})
    if (
        isinstance(feedback_loop, Mapping)
        and str(feedback_loop.get("semantic_review_execution_id", "") or "")
        == stale_execution_id
    ):
        context.pop("runtime_feedback_loop", None)
    return context


def _runtime_validated_algorithm_handoff(
    *,
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
    question_id: str,
    theory_packet_id: str,
    algorithm_sandbox_manifest_id: str,
    task: AgentTask | None = None,
    upstream_algorithm_handoff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if upstream_algorithm_handoff is not None:
        raw: Any = upstream_algorithm_handoff
    elif task is not None:
        raw = task.inputs.get(
            "upstream_algorithm_handoff",
            architect_context.get("upstream_algorithm_handoff", {}),
        )
    else:
        raw = architect_context.get("upstream_algorithm_handoff", {})
    handoff = dict(raw) if isinstance(raw, Mapping) else {}
    manifest = blackboard.artifacts.get(algorithm_sandbox_manifest_id, {})
    execution = blackboard.artifacts.get(
        str(handoff.get("semantic_review_execution_id", "") or ""), {}
    )
    packet = blackboard.artifacts.get(
        str(handoff.get("semantic_review_packet_id", "") or ""), {}
    )
    materialization = blackboard.artifacts.get(
        str(handoff.get("materialization_id", "") or ""), {}
    )
    legacy_review_material = (
        materialization.get("review_material", {})
        if isinstance(materialization, Mapping)
        else {}
    )
    expected_artifacts = (
        _runtime_materialized_exact_algorithm_artifacts(materialization)
        if isinstance(materialization, Mapping)
        else []
    )
    if (
        not expected_artifacts
        and isinstance(legacy_review_material, Mapping)
        and legacy_review_material
    ):
        expected_artifacts = _runtime_exact_algorithm_artifacts(
            legacy_review_material
        )
    review_input_fingerprint = str(
        materialization.get("review_input_fingerprint", "") or ""
    )
    review_input_identity_valid = bool(
        review_input_fingerprint
        and review_input_fingerprint
        == execution.get("review_input_fingerprint")
        == packet.get("review_input_fingerprint")
        and (
            not legacy_review_material
            or review_input_fingerprint == stable_hash(legacy_review_material)
        )
    )
    if not (
        handoff
        and isinstance(manifest, Mapping)
        and isinstance(execution, Mapping)
        and isinstance(packet, Mapping)
        and isinstance(materialization, Mapping)
        and handoff.get("question_id") == question_id
        and handoff.get("theory_packet_id") == theory_packet_id
        and handoff.get("algorithm_sandbox_manifest_id")
        == algorithm_sandbox_manifest_id
        and handoff.get("algorithm_sandbox_manifest_hash") == stable_hash(manifest)
        and manifest.get("artifact_kind") == "RuntimeAlgorithmSandboxManifest"
        and manifest.get("theory_packet_id") == theory_packet_id
        and int(manifest.get("n_generated_code_executed", 0) or 0) > 0
        and int(manifest.get("n_passed", 0) or 0) > 0
        and execution.get("semantic_review_accepted") is True
        and execution.get("source_subsystem") == "AlgorithmEngineer"
        and execution.get("source_manifest_id") == algorithm_sandbox_manifest_id
        and execution.get("source_manifest_hash") == stable_hash(manifest)
        and execution.get("review_packet_hash") == stable_hash(packet)
        and execution.get("materialization_hash") == stable_hash(materialization)
        and packet.get("overall_verdict") == "ACCEPT"
        and review_input_identity_valid
        and handoff.get("exact_algorithm_artifacts") == expected_artifacts
        and expected_artifacts
    ):
        return {}
    return handoff


def _runtime_algorithm_handoff_receipt(
    handoff: Mapping[str, Any] | None,
    *,
    simulation_rows: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    if not isinstance(handoff, Mapping) or not handoff:
        return {}
    artifact_refs = [
        {
            "estimator_id": str(row.get("estimator_id", "") or ""),
            "language": str(row.get("language", "") or ""),
            "exact_source_hash": str(row.get("exact_source_hash", "") or ""),
            "exact_smoke_result_hash": str(
                row.get("exact_smoke_result_hash", "") or ""
            ),
            "estimator_interface_contract_id": str(
                row.get("estimator_interface_contract_id", "") or ""
            ),
        }
        for row in handoff.get("exact_algorithm_artifacts", []) or []
        if isinstance(row, Mapping)
    ]
    expected_source_hashes = {
        row["estimator_id"]: row["exact_source_hash"]
        for row in artifact_refs
        if row["estimator_id"] and row["exact_source_hash"]
    }
    invocation_evidence: list[dict[str, Any]] = []
    mechanically_invoked_estimator_ids: set[str] = set()
    for row in simulation_rows:
        if not isinstance(row, Mapping):
            continue
        raw_selected_ids = row.get("required_estimator_ids")
        if raw_selected_ids is None:
            selected_ids = tuple(expected_source_hashes)
        elif isinstance(raw_selected_ids, (list, tuple)):
            selected_ids = tuple(
                dict.fromkeys(
                    str(value or "").strip()
                    for value in raw_selected_ids
                    if str(value or "").strip()
                )
            )
        else:
            continue
        if not selected_ids or any(
            estimator_id not in expected_source_hashes
            for estimator_id in selected_ids
        ):
            continue
        selected_source_hashes = {
            estimator_id: expected_source_hashes[estimator_id]
            for estimator_id in selected_ids
        }
        raw_hashes = row.get("bound_estimator_code_hashes", {})
        raw_counts = row.get("estimator_invocation_counts", {})
        if not isinstance(raw_hashes, Mapping) or not isinstance(raw_counts, Mapping):
            continue
        bound_hashes = {str(key): str(value) for key, value in raw_hashes.items()}
        try:
            invocation_counts = {
                str(key): max(0, int(value or 0))
                for key, value in raw_counts.items()
            }
        except (TypeError, ValueError):
            continue
        if not (
            row.get("mechanical_estimator_invocation_verified") is True
            and bound_hashes == selected_source_hashes
            and str(row.get("estimator_binding_hash", "") or "")
            == stable_hash(selected_source_hashes)
            and all(
                invocation_counts.get(estimator_id, 0) > 0
                for estimator_id in selected_source_hashes
            )
            and str(row.get("script_hash", "") or "")
            and str(row.get("result_hash", "") or "")
            and str(row.get("execution_envelope_hash", "") or "")
        ):
            continue
        mechanically_invoked_estimator_ids.update(selected_ids)
        invocation_evidence.append(
            {
                "simulation_id": str(row.get("simulation_id", "") or ""),
                "required_estimator_ids": list(selected_ids),
                "simulation_source_hash": str(row.get("script_hash", "") or ""),
                "simulation_result_hash": str(row.get("result_hash", "") or ""),
                "execution_envelope_hash": str(
                    row.get("execution_envelope_hash", "") or ""
                ),
                "estimator_binding_hash": str(
                    row.get("estimator_binding_hash", "") or ""
                ),
                "bound_estimator_code_hashes": bound_hashes,
                "estimator_invocation_counts": invocation_counts,
                "mechanical_estimator_invocation_verified": True,
            }
        )
    mechanical_estimator_invocation_verified = bool(
        expected_source_hashes and invocation_evidence
    )
    all_handoff_estimators_invoked = bool(
        expected_source_hashes
        and set(expected_source_hashes).issubset(mechanically_invoked_estimator_ids)
    )
    return {
        "artifact_kind": "RuntimeAcceptedAlgorithmHandoffReceipt",
        "algorithm_sandbox_manifest_id": str(
            handoff.get("algorithm_sandbox_manifest_id", "") or ""
        ),
        "algorithm_sandbox_manifest_hash": str(
            handoff.get("algorithm_sandbox_manifest_hash", "") or ""
        ),
        "semantic_review_execution_id": str(
            handoff.get("semantic_review_execution_id", "") or ""
        ),
        "semantic_review_packet_id": str(
            handoff.get("semantic_review_packet_id", "") or ""
        ),
        "semantic_review_packet_hash": str(
            handoff.get("semantic_review_packet_hash", "") or ""
        ),
        "theory_packet_id": str(handoff.get("theory_packet_id", "") or ""),
        "exact_algorithm_artifact_refs": artifact_refs,
        "handoff_fingerprint": stable_hash(handoff),
        "exact_artifact_supplied_to_simulation_generator": bool(artifact_refs),
        "mechanical_estimator_invocation_verified": (
            mechanical_estimator_invocation_verified
        ),
        "mechanically_invoked_estimator_ids": sorted(
            mechanically_invoked_estimator_ids
        ),
        "all_handoff_estimators_invoked": all_handoff_estimators_invoked,
        "mechanical_invocation_evidence": invocation_evidence,
        "proof_evidence_status": "ALGORITHM_HANDOFF_RECEIPT_NOT_PROOF_EVIDENCE",
        "boundary": (
            "This receipt distinguishes prompt visibility from mechanical reuse. A "
            "verified invocation means the hash-bound reviewed run_estimator source "
            "was called by the generated DGP harness. It does not establish DGP, "
            "metric, statistical, or theorem correctness."
        ),
    }


def _architect_metric_protocol_prior_rejection_context(
    *,
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
    current_theory_material: Mapping[str, Any],
) -> dict[str, Any]:
    gate = architect_context.get("architect_metric_protocol_gate", {})
    if not isinstance(gate, Mapping):
        return {}
    rejection_ids = [
        str(value)
        for value in gate.get("rejection_manifest_ids", []) or []
        if str(value).strip()
    ]
    for rejection_id in reversed(rejection_ids):
        rejection = blackboard.artifacts.get(rejection_id, {})
        if (
            not isinstance(rejection, Mapping)
            or rejection.get("artifact_kind")
            != "RuntimeArchitectMetricProtocolPreExecutionRejection"
            or rejection.get("feedback_reusable_for_fresh_preexecution_authoring")
            is not True
            or rejection.get("execution_authorized") is not False
        ):
            continue
        history = rejection.get("semantic_review_history", [])
        if not isinstance(history, list) or not history:
            continue
        final_review = history[-1]
        if not isinstance(final_review, Mapping):
            continue
        theory_execution_preflight = bool(
            str(final_review.get("review_stage", "") or "")
            == "theory_execution_preflight"
        )
        if (
            not theory_execution_preflight
            and not final_review.get("empirical_metric_requirements")
        ):
            continue
        final_review_context = deepcopy(dict(final_review))
        embedded_preflight = final_review_context.pop(
            "theory_execution_preflight_packet",
            {},
        )
        if isinstance(embedded_preflight, Mapping) and embedded_preflight:
            final_review_context["theory_execution_preflight_packet_id"] = str(
                embedded_preflight.get("packet_id", "") or ""
            )
            final_review_context["theory_execution_preflight_packet_hash"] = (
                stable_hash(dict(embedded_preflight))
            )
        return {
            "artifact_kind": (
                "RuntimeArchitectMetricProtocolPriorRejectionContext"
            ),
            "source_rejection_manifest_id": rejection_id,
            "source_rejection_manifest_hash": stable_hash(dict(rejection)),
            "current_source_theory_packet_id": str(
                current_theory_material.get("source_theory_packet_id", "")
                or ""
            ),
            "current_source_theory_packet_hash": str(
                current_theory_material.get("source_theory_packet_hash", "")
                or ""
            ),
            "semantic_review_history_count": len(history),
            "semantic_review_history_fingerprint": stable_hash(history),
            "cumulative_finding_ledger": [
                deepcopy(dict(row))
                for row in final_review.get(
                    "cumulative_finding_ledger", []
                )
                or []
                if isinstance(row, Mapping)
            ],
            "final_review": final_review_context,
            "execution_results_available": False,
            "current_candidate_acceptance_eligible": False,
            "proof_evidence_status": (
                "PRIOR_METRIC_REJECTION_CONTEXT_NOT_PROOF_EVIDENCE"
            ),
            "boundary": (
                "This is immutable repair context from a rejected theory preflight "
                "or pre-execution metric contract. The current revised theory is "
                "authoritative. Prior findings guide explicit resolution review but "
                "do not authorize execution or establish statistical or proof evidence."
            ),
        }
    return {}


def _architect_selected_worker_environment_feedback(
    *,
    selected: Mapping[str, Any],
    architect_context: Mapping[str, Any],
) -> dict[str, Any]:
    explicit_feedback = selected.get("environment_feedback", {})
    if isinstance(explicit_feedback, Mapping) and explicit_feedback:
        return dict(explicit_feedback)

    feedback = architect_context.get("environment_feedback", {})
    feedback_route = architect_context.get("architect_feedback_route_decision", {})
    if (
        isinstance(feedback, Mapping)
        and feedback
        and isinstance(feedback_route, Mapping)
        and feedback_route.get("decision") == "ROUTE"
        and str(feedback_route.get("environment_feedback_fingerprint", "") or "")
        == stable_hash(dict(feedback))
    ):
        return dict(feedback)

    replan = architect_context.get(
        "runtime_generated_code_semantic_review_replan",
        {},
    )
    feedback_packet_id = (
        str(feedback.get("semantic_review_packet_id", "") or "")
        if isinstance(feedback, Mapping)
        else ""
    )
    feedback_execution_id = (
        str(feedback.get("semantic_review_execution_id", "") or "")
        if isinstance(feedback, Mapping)
        else ""
    )
    if not (
        isinstance(replan, Mapping)
        and replan
        and isinstance(feedback, Mapping)
        and feedback
        and str(feedback.get("feedback_type", "") or "")
        == "generated_code_semantic_review_feedback"
        and feedback_packet_id
        and feedback_packet_id
        == str(replan.get("review_packet_id", "") or "")
        and feedback_execution_id
        and feedback_execution_id
        == str(replan.get("review_execution_id", "") or "")
    ):
        return {}
    return dict(feedback)


def _architect_initial_routing_decision(
    *,
    question: OpenResearchQuestion,
    packet: Mapping[str, Any],
    architect_context: Mapping[str, Any],
    packet_id: str,
    runtime_config: ResearchAgentRuntimeConfig,
    blackboard: BlackboardState,
    requested_subsystem_override: str = "",
    routing_source_override: str = "",
    honor_requested_subsystem: bool = False,
) -> dict[str, Any]:
    requested_override = _canonical_architect_subsystem(
        requested_subsystem_override
    )
    if requested_override:
        selected_subsystem = (
            requested_override
            if honor_requested_subsystem
            else _architect_feasible_initial_subsystem(
                requested_override,
                architect_context=architect_context,
                blackboard=blackboard,
                question_id=question.id,
            )
        )
        selected = {
            "requested_subsystem": requested_override,
            "selected_subsystem": selected_subsystem,
            "source": (
                str(routing_source_override or "").strip()
                or "architect_runtime_continuation"
            ),
            "requires_prerequisite_theory": (
                requested_override != selected_subsystem
            ),
            "model_route_honored_exactly": bool(honor_requested_subsystem),
        }
    else:
        selected = _architect_select_initial_subsystem(
            packet=packet,
            architect_context=architect_context,
            blackboard=blackboard,
            question_id=question.id,
        )
    context = dict(architect_context)
    routed_environment_feedback = (
        _architect_selected_worker_environment_feedback(
            selected=selected,
            architect_context=architect_context,
        )
    )
    metric_protocol_execution_route_authorized = bool(
        selected["selected_subsystem"]
        in {"AlgorithmEngineer", "SimulationEvaluator"}
        and _architect_packet_metric_protocol_authority_matches_current_theory(
            packet=packet,
            architect_context=context,
        )
    )
    record = {
        "artifact_kind": "ArchitectInitialRoutingDecision",
        "question_id": question.id,
        "architect_packet_id": packet_id,
        "selected_subsystem": selected["selected_subsystem"],
        "requested_subsystem": selected["requested_subsystem"],
        "source": selected["source"],
        "requires_prerequisite_theory": bool(
            selected.get("requires_prerequisite_theory", False)
        ),
        "requires_prerequisite_algorithm": bool(
            selected.get("requires_prerequisite_algorithm", False)
        ),
        "model_route_honored_exactly": bool(
            selected.get("model_route_honored_exactly", False)
        ),
        "boundary": (
            "Architect initial routing is orchestration control only. It does "
            "not execute tools, validate generated code or simulations, or "
            "prove a theorem."
        ),
        "proof_evidence_status": "ARCHITECT_INITIAL_ROUTING_NOT_PROOF_EVIDENCE",
    }
    record["parent_artifact_ids"] = _runtime_workspace_parent_artifact_ids(
        selected["selected_subsystem"],
        context,
    )
    if routed_environment_feedback:
        record["environment_feedback_forwarded"] = True
        record["environment_feedback_type"] = str(
            routed_environment_feedback.get("feedback_type", "") or ""
        )
        record["environment_feedback_execution_id"] = str(
            routed_environment_feedback.get(
                "semantic_review_execution_id",
                "",
            )
            or ""
        )
        record["environment_feedback_hash"] = stable_hash(
            routed_environment_feedback
        )
    context["architect_initial_routing"] = record
    if metric_protocol_execution_route_authorized:
        metric_gate = context.get("architect_metric_protocol_gate", {})
        if isinstance(metric_gate, Mapping):
            consumed_gate = dict(metric_gate)
            consumed_gate["execution_authorized"] = True
            consumed_gate["consumed"] = True
            consumed_gate["accepted_requirement_set_id"] = str(
                packet.get("evidence_contract", {}).get(
                    "empirical_metric_requirement_set_id", ""
                )
                if isinstance(packet.get("evidence_contract", {}), Mapping)
                else ""
            )
            context["architect_metric_protocol_gate"] = consumed_gate
            context.pop(
                "architect_metric_protocol_authority_invalidation",
                None,
            )
            record["metric_protocol_authority_consumed"] = True
        if context.pop("empirical_evaluation_phase", None) is not None:
            record["exploratory_evaluation_phase_completed"] = True
        dependency_rebuild = context.get("runtime_dependency_rebuild", {})
        if (
            isinstance(dependency_rebuild, Mapping)
            and dependency_rebuild.get("artifact_kind")
            == "RuntimeTheoryRevisionDependencyRebuild"
            and dependency_rebuild.get(
                "confirmatory_descendant_rebuild_authorized"
            )
            is not True
            and str(
                dependency_rebuild.get("revised_theory_packet_id", "") or ""
            )
            == _architect_context_theory_packet_id(context)
        ):
            accepted_contract = packet.get("evidence_contract", {})
            accepted_contract = (
                accepted_contract
                if isinstance(accepted_contract, Mapping)
                else {}
            )
            resolved_rebuild = dict(dependency_rebuild)
            resolved_rebuild.update(
                {
                    "resolution_status": (
                        "PREEXECUTION_METRIC_PROTOCOL_ACCEPTED"
                    ),
                    "confirmatory_descendant_rebuild_authorized": True,
                    "resolved_requirement_set_id": str(
                        accepted_contract.get(
                            "empirical_metric_requirement_set_id",
                            "",
                        )
                        or ""
                    ),
                    "resolved_by_architect_packet_id": str(
                        packet.get("packet_id", "") or ""
                    ),
                    "resolution_boundary": (
                        "The revised theory now has a hash-bound, independently "
                        "accepted pre-execution metric protocol. Clearing the "
                        "temporary exploratory phase authorizes fresh descendants "
                        "to bind that protocol; it does not promote prior "
                        "exploratory results or provide proof evidence."
                    ),
                }
            )
            context["runtime_dependency_rebuild"] = resolved_rebuild
            record["theory_revision_dependency_rebuild_resolved"] = True
            record["theory_revision_dependency_rebuild_resolution_status"] = (
                resolved_rebuild["resolution_status"]
            )
    if selected["selected_subsystem"] == "TheoryDeveloper":
        feedback = routed_environment_feedback
        inputs: dict[str, Any] = {
            "question": _question_to_payload(question),
            "architect_context": context,
        }
        if isinstance(feedback, Mapping) and feedback:
            inputs["environment_feedback"] = dict(feedback)
            context["environment_feedback"] = dict(feedback)
            inputs["architect_context"] = context
        return {
            "task": AgentTask(
                task_id=f"theory:{question.id}:{stable_hash([packet_id, record])[:8]}",
                owner_subsystem="TheoryDeveloper",
                objective=_architect_initial_objective(
                    context,
                    "TheoryDeveloper",
                    "Derive a statistical theory proposal or prerequisite repair "
                    "needed by the Architect plan.",
                ),
                inputs=inputs,
                allowed_tools=("model_backend", "rag_memory", "evidence_ledger"),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "TheoryDeveloper",
                    ("theory_derivation_packet",),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "TheoryDeveloper",
                    "validated theory packet with proof boundary",
                ),
                stop_condition=(
                    "theory packet satisfies Architect routing prerequisite"
                ),
            ),
            "record": record,
            "rationale": (
                "ArchitectCoordinator recorded a compact research decision and "
                "is routing to TheoryDeveloper as the earliest feasible next "
                "subsystem for the selected obligation."
            ),
        }
    if selected["selected_subsystem"] == "SimulationEvaluator":
        feedback = routed_environment_feedback
        evidence_contract = packet.get("evidence_contract", {})
        requires_accepted_algorithm_handoff = bool(
            metric_protocol_execution_route_authorized
            and isinstance(evidence_contract, Mapping)
            and evidence_contract.get(
                "research_evaluation_requires_generated_algorithm_code"
            )
            is True
        )
        algorithm_sandbox_manifest_id = (
            _architect_context_algorithm_sandbox_manifest_id(context)
        )
        upstream_algorithm_handoff = context.get(
            "upstream_algorithm_handoff", {}
        )
        if requires_accepted_algorithm_handoff:
            context[
                "confirmatory_simulation_requires_accepted_algorithm_handoff"
            ] = True
        inputs: dict[str, Any] = {
            "question": _question_to_payload(question),
            "theory_packet_id": str(
                architect_context.get("theory_packet_id", "")
                or architect_context.get("previous_theory_packet_id", "")
                or ""
            ),
            "architect_context": context,
            "n_runs": runtime_config.n_runs,
            "seed": runtime_config.seed,
        }
        if requires_accepted_algorithm_handoff:
            inputs["algorithm_sandbox_manifest_id"] = (
                algorithm_sandbox_manifest_id
            )
            if isinstance(upstream_algorithm_handoff, Mapping):
                inputs["upstream_algorithm_handoff"] = dict(
                    upstream_algorithm_handoff
                )
        if isinstance(feedback, Mapping) and feedback:
            context["environment_feedback"] = dict(feedback)
            inputs["environment_feedback"] = dict(feedback)
            inputs["architect_context"] = context
        if selected.get("source") == "accepted_metric_protocol_target":
            routing_rationale = (
                "ArchitectCoordinator is routing directly to SimulationEvaluator "
                "because the independently accepted metric protocol declares that "
                "execution target and its required handoff artifacts exist."
            )
        else:
            routing_rationale = (
                "ArchitectCoordinator recorded a compact research decision and "
                "is routing directly to SimulationEvaluator because the model "
                "selected that worker and its required handoff artifacts exist."
            )
        return {
            "task": AgentTask(
                task_id=f"simulation:{question.id}:{stable_hash([packet_id, record])[:8]}",
                owner_subsystem="SimulationEvaluator",
                objective=_architect_initial_objective(
                    context,
                    "SimulationEvaluator",
                    "Execute simulation and generated-simulation diagnostics requested "
                    "by the Architect model plan.",
                ),
                inputs=inputs,
                allowed_tools=(
                    "model_backend",
                    "research_simulator",
                    "python",
                    "filesystem_sandbox",
                ),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "SimulationEvaluator",
                    ("simulation_manifest", "implementation_gap_manifest"),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "SimulationEvaluator",
                    "simulation manifest plus generated-simulation capability evidence or an explicit blocker",
                ),
                stop_condition="simulation diagnostics recorded for the next typed task",
            ),
            "record": record,
            "rationale": routing_rationale,
        }
    if selected["selected_subsystem"] == "AlgorithmEngineer":
        feedback = routed_environment_feedback
        simulation_manifest_id = _architect_context_simulation_manifest_id(
            architect_context
        )
        implementation_gaps = _architect_context_implementation_gaps(
            architect_context,
            blackboard=blackboard,
        )
        inputs: dict[str, Any] = {
            "question": _question_to_payload(question),
            "theory_packet_id": _architect_context_theory_packet_id(
                architect_context
            ),
            "simulation_manifest_id": simulation_manifest_id,
            "implementation_gaps": implementation_gaps,
            "architect_context": context,
            "n_runs": runtime_config.n_runs,
            "seed": runtime_config.seed,
        }
        if isinstance(feedback, Mapping) and feedback:
            context["environment_feedback"] = dict(feedback)
            inputs["environment_feedback"] = dict(feedback)
            inputs["architect_context"] = context
        metric_gate = context.get("architect_metric_protocol_gate", {})
        pre_metric_implementation = bool(
            isinstance(metric_gate, Mapping)
            and (
                metric_gate.get("algorithm_execution_available") is True
                or metric_gate.get("algorithm_execution_authorized") is True
            )
            and metric_gate.get("confirmatory_simulation_authorized") is False
            and metric_gate.get("execution_authorized") is False
            and str(metric_gate.get("preflight_acceptance_id", "") or "")
            and context.get("empirical_evaluation_phase")
            == EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
        )
        if pre_metric_implementation:
            selected_metric_gate = dict(metric_gate)
            selected_metric_gate.update(
                {
                    "algorithm_execution_authorized": True,
                    "algorithm_execution_selected_by": (
                        "model_authored_architect_plan"
                        if record.get("source")
                        == "architect_plan_workspace_transition"
                        else "ArchitectCoordinator_model_route"
                    ),
                    "algorithm_execution_route_decision_id": str(
                        record.get("architect_packet_id", "") or ""
                    ),
                }
            )
            context["architect_metric_protocol_gate"] = selected_metric_gate
            inputs["architect_context"] = context
            acceptance_id = str(
                metric_gate.get("preflight_acceptance_id", "") or ""
            )
            deferred_metric_task = AgentTask(
                task_id=(
                    f"architect-metric-after-implementation:{question.id}:"
                    f"{stable_hash([packet_id, acceptance_id])[:8]}"
                ),
                owner_subsystem="ArchitectCoordinator",
                objective=(
                    "Author and independently review the smallest confirmatory "
                    "simulation metric portfolio after implementation acceptance, "
                    "without observing implementation smoke-test results."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": context,
                    "runtime_architect_operation": (
                        RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC
                    ),
                },
                allowed_tools=(
                    "model_backend",
                    "blackboard",
                    "evidence_ledger",
                ),
                expected_artifacts=(
                    "architect_coordinator_proposal",
                    "architect_metric_requirement_authoring",
                    "architect_metric_semantic_review",
                ),
                acceptance_gate=(
                    "accepted implementation interface is result-free and the "
                    "theory-bound confirmatory simulation protocol receives "
                    "independent ACCEPT"
                ),
                stop_condition=(
                    "metric protocol is accepted and routed to confirmatory "
                    "simulation, or typed review feedback preserves exact lineage"
                ),
            )
            inputs.update(
                {
                    "empirical_evaluation_phase": (
                        EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
                    ),
                    "implementation_before_metric_freeze": True,
                    "deferred_metric_protocol_task": asdict(
                        deferred_metric_task
                    ),
                }
            )
            task_prefix = "algorithm-before-metric"
            default_objective = (
                "Generate and execute the theory-bound estimator implementation "
                "selected by the Architect model before confirmatory metrics are "
                "frozen; expose exact source and smoke feedback to an independent "
                "semantic reviewer."
            )
            default_acceptance_gate = (
                "generated implementation executes and receives independent "
                "semantic ACCEPT before deferred metric authoring resumes"
            )
            default_stop_condition = (
                "implementation review accepts the exact executable interface or "
                "returns complete observations to an existing model-owned worker"
            )
        else:
            task_prefix = "algorithm"
            default_objective = (
                "Execute algorithm sandbox and generated-code diagnostics requested "
                "by the Architect model plan."
            )
            default_acceptance_gate = (
                "algorithm sandbox manifest plus generated-code capability evidence "
                "or an explicit blocker"
            )
            default_stop_condition = (
                "algorithm sandbox diagnostics recorded for the next typed task"
            )
        return {
            "task": AgentTask(
                task_id=(
                    f"{task_prefix}:{question.id}:"
                    f"{stable_hash([packet_id, record])[:8]}"
                ),
                owner_subsystem="AlgorithmEngineer",
                objective=_architect_initial_objective(
                    context,
                    "AlgorithmEngineer",
                    default_objective,
                ),
                inputs=inputs,
                allowed_tools=("model_backend", "python", "filesystem_sandbox"),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "AlgorithmEngineer",
                    ("algorithm_sandbox_manifest",),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "AlgorithmEngineer",
                    default_acceptance_gate,
                ),
                stop_condition=default_stop_condition,
            ),
            "record": record,
            "rationale": (
                "ArchitectCoordinator recorded a compact research decision and "
                "is routing directly to AlgorithmEngineer because the model selected "
                "that worker and its required handoff artifacts exist."
            ),
        }
    if selected["selected_subsystem"] == "FormalizationEvaluator":
        feedback = routed_environment_feedback
        if not feedback:
            feedback = _formalizer_lean_candidate_revision_feedback(
                _architect_formalizer_lean_candidate_materialization(
                    architect_context=architect_context,
                    blackboard=blackboard,
                )
            )
        inputs: dict[str, Any] = {
            "question": _question_to_payload(question),
            "theory_packet_id": _architect_context_theory_packet_id(
                architect_context
            ),
            "simulation_manifest_id": _architect_context_simulation_manifest_id(
                architect_context
            ),
            "algorithm_sandbox_manifest_id": (
                _architect_context_algorithm_sandbox_manifest_id(
                    architect_context
                )
            ),
            "architect_context": context,
            "n_runs": runtime_config.n_runs,
            "seed": runtime_config.seed,
        }
        if isinstance(feedback, Mapping) and feedback:
            context["environment_feedback"] = dict(feedback)
            inputs["environment_feedback"] = dict(feedback)
            inputs["architect_context"] = context
        return {
            "task": AgentTask(
                task_id=f"formalize:{question.id}:{stable_hash([packet_id, record])[:8]}",
                owner_subsystem="FormalizationEvaluator",
                objective=_architect_initial_objective(
                    context,
                    "FormalizationEvaluator",
                    "Own the complete Lean source while using formal-source search, "
                    "proof search, and raw Lean observations to produce the next "
                    "exact-target candidate.",
                ),
                inputs=inputs,
                allowed_tools=(
                    "model_backend",
                    "local_lean",
                    "lean_lsp_mcp",
                    "formal_source_retrieval",
                    "proof_search",
                ),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "FormalizationEvaluator",
                    ("formalization_manifest", "proof_feedback"),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "FormalizationEvaluator",
                    "the complete model-authored source passes the exact environment "
                    "and review gates or records a precise blocker",
                ),
                stop_condition=(
                    "exact source is kernel promoted or the bounded model-owned "
                    "workspace records its observations and blocker"
                ),
            ),
            "record": record,
            "rationale": (
                "ArchitectCoordinator recorded a compact research decision and is "
                "routing directly to FormalizationEvaluator because the model "
                "selected that worker and its required handoff artifacts exist."
            ),
        }
    if selected["selected_subsystem"] == "CriticEvaluator":
        feedback = routed_environment_feedback
        inputs: dict[str, Any] = {
            "question": _question_to_payload(question),
            "theory_packet_id": _architect_context_theory_packet_id(
                architect_context
            ),
            "simulation_manifest_id": _architect_context_simulation_manifest_id(
                architect_context
            ),
            "algorithm_sandbox_manifest_id": (
                _architect_context_algorithm_sandbox_manifest_id(
                    architect_context
                )
            ),
            "formalization_manifest_id": (
                _architect_context_formalization_manifest_id(
                    architect_context
                )
            ),
            "architect_context": context,
        }
        if isinstance(feedback, Mapping) and feedback:
            context["environment_feedback"] = dict(feedback)
            inputs["environment_feedback"] = dict(feedback)
            inputs["architect_context"] = context
        return {
            "task": AgentTask(
                task_id=(
                    f"critic:{question.id}:"
                    f"{stable_hash([packet_id, record, feedback])[:8]}"
                ),
                owner_subsystem="CriticEvaluator",
                objective=_architect_initial_objective(
                    context,
                    "CriticEvaluator",
                    "Independently audit the current runtime artifacts, unresolved "
                    "environment observations, and evidence boundaries selected by "
                    "the Architect model.",
                ),
                inputs=inputs,
                allowed_tools=("model_backend", "blackboard", "evidence_ledger"),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "CriticEvaluator",
                    ("critic_evaluator_manifest", "critic_model_packet"),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "CriticEvaluator",
                    "critic observations preserve artifact lineage and all evidence boundaries",
                ),
                stop_condition=(
                    "critic records acceptance, complete observations for Architect, "
                    "or an explicit blocker"
                ),
            ),
            "record": record,
            "rationale": (
                "ArchitectCoordinator is routing directly to CriticEvaluator because "
                "the model selected independent audit and the current formalization "
                "artifact is available."
            ),
        }
    return {
        "task": AgentTask(
            task_id=f"retrieve:{question.id}:{stable_hash(packet_id)[:8]}",
            owner_subsystem="RetrievalMemory",
            objective=_architect_initial_objective(
                context,
                "RetrievalMemory",
                "Retrieve paper, statistical knowledge, and formal-source context "
                "before theory derivation.",
            ),
            inputs={
                "question": _question_to_payload(question),
                "architect_context": context,
            },
            allowed_tools=(
                "research_knowledge",
                "paper_index",
                "formal_source_retriever",
            ),
            expected_artifacts=_architect_expected_artifacts(
                context,
                "RetrievalMemory",
                ("retrieval_memory_manifest",),
            ),
            acceptance_gate=_architect_acceptance_gate(
                context,
                "RetrievalMemory",
                "retrieval context recorded with explicit non-proof boundary",
            ),
            stop_condition="retrieval context routed to TheoryDeveloper",
        ),
        "record": record,
        "rationale": (
            "ArchitectCoordinator recorded a compact research decision and "
            "is routing to RetrievalMemory for source and formal context."
        ),
    }


def _architect_select_initial_subsystem(
    *,
    packet: Mapping[str, Any],
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
    question_id: str = "",
) -> dict[str, Any]:
    evidence_contract = packet.get("evidence_contract", {})
    if not isinstance(evidence_contract, Mapping):
        evidence_contract = {}
    metric_protocol_phase = str(
        evidence_contract.get("empirical_metric_protocol_phase", "") or ""
    )
    requested_for_metric_gate = _architect_packet_requested_subsystem(packet)
    if (
        metric_protocol_phase
        == METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING
        and evidence_contract.get("metric_protocol_execution_authorized") is False
    ):
        has_retrieval_context = bool(
            architect_context.get("retrieval_memory_manifest_id")
            or architect_context.get("retrieval_context")
        )
        pending_selection: dict[str, Any] = {
            "requested_subsystem": requested_for_metric_gate,
            "selected_subsystem": (
                "TheoryDeveloper" if has_retrieval_context else "RetrievalMemory"
            ),
            "source": "metric_protocol_theory_prerequisite",
            "requires_prerequisite_theory": True,
        }
        return pending_selection
    requested = _architect_packet_requested_subsystem(packet)
    selected = _architect_feasible_initial_subsystem(
        requested,
        architect_context=architect_context,
        blackboard=blackboard,
        question_id=question_id,
    )
    return {
        "requested_subsystem": requested,
        "selected_subsystem": selected,
        "source": "architect_packet",
        "requires_prerequisite_theory": requested != selected,
    }


def _architect_metric_protocol_execution_owner(
    packet: Mapping[str, Any],
) -> str:
    """Resolve a reviewed metric protocol's declared runtime execution owner."""

    evidence_contract = packet.get("evidence_contract", {})
    if not isinstance(evidence_contract, Mapping) or not (
        evidence_contract.get("empirical_metric_protocol_phase")
        == METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED
        and evidence_contract.get("metric_protocol_execution_authorized") is True
    ):
        return ""
    requirements = evidence_contract.get("empirical_metric_requirements", [])
    author_targets = list(
        dict.fromkeys(
            str(target).strip()
            for row in requirements or []
            if isinstance(row, Mapping) and row.get("required") is True
            for target in row.get("target_subsystems", []) or []
            if str(target).strip()
        )
    )
    namespace = generated_metric_requirement_target_namespace_contract()
    owner_by_author = namespace.get(
        "runtime_execution_owner_by_author_subsystem", {}
    )
    owner_by_author = (
        owner_by_author if isinstance(owner_by_author, Mapping) else {}
    )
    runtime_owners = list(
        dict.fromkeys(
            _canonical_architect_subsystem(owner_by_author.get(target, ""))
            for target in author_targets
            if _canonical_architect_subsystem(
                owner_by_author.get(target, "")
            )
        )
    )
    return runtime_owners[0] if len(runtime_owners) == 1 else ""


def _architect_packet_requested_subsystem(packet: Mapping[str, Any]) -> str:
    for action in packet.get("next_actions", []) or []:
        if not isinstance(action, Mapping):
            continue
        owner = _canonical_architect_subsystem(
            action.get("owner_subsystem")
            or action.get("owner_agent")
            or action.get("owner")
        )
        if owner and owner != "ArchitectCoordinator":
            return owner
    for row in packet.get("subsystem_execution_plan", []) or []:
        if not isinstance(row, Mapping):
            continue
        subsystem = _canonical_architect_subsystem(row.get("subsystem"))
        if subsystem and subsystem != "ArchitectCoordinator":
            return subsystem
    return "RetrievalMemory"


def _architect_feasible_initial_subsystem(
    requested: str,
    *,
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
    question_id: str = "",
) -> str:
    if requested in {"RetrievalMemory", "TheoryDeveloper"}:
        return requested
    if requested == "SimulationEvaluator":
        if _architect_context_theory_packet_id(architect_context):
            return "SimulationEvaluator"
        return "TheoryDeveloper"
    if requested == "AlgorithmEngineer":
        if not _architect_context_theory_packet_id(architect_context):
            return "TheoryDeveloper"
        if not _architect_context_implementation_gaps(
            architect_context,
            blackboard=blackboard,
        ):
            return "TheoryDeveloper"
        return "AlgorithmEngineer"
    if requested == "FormalizationEvaluator":
        theory_packet_id = _architect_context_theory_packet_id(architect_context)
        if not theory_packet_id or not _architect_blackboard_artifact_present(
            blackboard,
            theory_packet_id,
        ):
            return "TheoryDeveloper"
        return "FormalizationEvaluator"
    if requested == "CriticEvaluator":
        formalization_manifest_id = _architect_context_formalization_manifest_id(
            architect_context
        )
        if formalization_manifest_id and _architect_blackboard_artifact_present(
            blackboard,
            formalization_manifest_id,
        ):
            return "CriticEvaluator"
        return _architect_feasible_initial_subsystem(
            "FormalizationEvaluator",
            architect_context=architect_context,
            blackboard=blackboard,
            question_id=question_id,
        )
    return "TheoryDeveloper" if requested else "RetrievalMemory"


def _architect_context_theory_packet_id(architect_context: Mapping[str, Any]) -> str:
    if not isinstance(architect_context, Mapping):
        return ""
    return str(
        architect_context.get("theory_packet_id", "")
        or architect_context.get("previous_theory_packet_id", "")
        or ""
    ).strip()


def _architect_context_simulation_manifest_id(
    architect_context: Mapping[str, Any],
) -> str:
    if not isinstance(architect_context, Mapping):
        return ""
    return str(architect_context.get("simulation_manifest_id", "") or "").strip()


def _architect_context_algorithm_sandbox_manifest_id(
    architect_context: Mapping[str, Any],
) -> str:
    if not isinstance(architect_context, Mapping):
        return ""
    return str(
        architect_context.get("algorithm_sandbox_manifest_id", "") or ""
    ).strip()


def _architect_context_formalizer_lean_candidate_materialization_id(
    architect_context: Mapping[str, Any],
) -> str:
    if not isinstance(architect_context, Mapping):
        return ""
    return str(
        architect_context.get("formalizer_lean_candidate_materialization_manifest_id", "")
        or architect_context.get("source_materialization_manifest_id", "")
        or ""
    ).strip()


def _architect_context_formalization_manifest_id(
    architect_context: Mapping[str, Any],
) -> str:
    if not isinstance(architect_context, Mapping):
        return ""
    return str(
        architect_context.get("formalization_manifest_id", "") or ""
    ).strip()


def _architect_blackboard_artifact_present(
    blackboard: BlackboardState,
    artifact_id: str,
) -> bool:
    artifact_id = str(artifact_id or "").strip()
    if not artifact_id:
        return False
    artifact = blackboard.artifacts.get(artifact_id, {})
    return bool(isinstance(artifact, Mapping) and artifact)


def _architect_formalizer_lean_candidate_materialization(
    *,
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
) -> dict[str, Any]:
    materialization_id = (
        _architect_context_formalizer_lean_candidate_materialization_id(
            architect_context
        )
    )
    artifact = _artifact_by_id_or_latest(
        blackboard,
        materialization_id,
        "formalizer_lean_candidate_materialization:",
    )
    if str(artifact.get("artifact_kind", "") or "") != (
        "RuntimeFormalizerLeanCandidateMaterialization"
    ):
        return {}
    return _normalize_formalizer_lean_candidate_materialization_artifact(artifact)


def _architect_context_implementation_gaps(
    architect_context: Mapping[str, Any],
    *,
    blackboard: BlackboardState,
) -> list[dict[str, Any]]:
    if not isinstance(architect_context, Mapping):
        return []
    for key in ("implementation_gaps", "previous_implementation_gaps"):
        rows = architect_context.get(key, [])
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
            normalized = [dict(row) for row in rows if isinstance(row, Mapping)]
            if normalized:
                return normalized
    simulation_manifest_id = _architect_context_simulation_manifest_id(
        architect_context
    )
    if simulation_manifest_id:
        simulation_manifest = blackboard.artifacts.get(simulation_manifest_id, {})
        if isinstance(simulation_manifest, Mapping):
            rows = simulation_manifest.get("implementation_gaps", [])
            if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
                normalized = [
                    dict(row) for row in rows if isinstance(row, Mapping)
                ]
                if normalized:
                    return normalized
    theory_packet_id = _architect_context_theory_packet_id(architect_context)
    theory_packet = blackboard.artifacts.get(theory_packet_id, {})
    if not isinstance(theory_packet, Mapping) or not theory_packet:
        return []
    return _implementation_gaps(
        theory_packet,
        [],
        require_generated_adapter=True,
    )


def _canonical_architect_subsystem(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    aliases = {
        "retrievalmemory": "RetrievalMemory",
        "retrieval": "RetrievalMemory",
        "theorydeveloper": "TheoryDeveloper",
        "theory": "TheoryDeveloper",
        "simulationevaluator": "SimulationEvaluator",
        "simulationengineer": "SimulationEvaluator",
        "simulation": "SimulationEvaluator",
        "algorithmengineer": "AlgorithmEngineer",
        "algorithm": "AlgorithmEngineer",
        "generatedcodesemanticreviewer": "GeneratedCodeSemanticReviewer",
        "codesemanticreviewer": "GeneratedCodeSemanticReviewer",
        "formaltargetsemanticreviewer": "FormalTargetSemanticReviewer",
        "theoremsemanticreviewer": "FormalTargetSemanticReviewer",
        "formalizationevaluator": "FormalizationEvaluator",
        "formalizer": "FormalizationEvaluator",
        "formalizerproofengineer": "FormalizationEvaluator",
        "formalizer/leanprover": "FormalizationEvaluator",
        "proofengineer": "FormalizationEvaluator",
        "leanprover": "FormalizationEvaluator",
        "critic": "CriticEvaluator",
        "criticevaluator": "CriticEvaluator",
        "architectcoordinator": "ArchitectCoordinator",
        "agentruntime": "AgentRuntimeOrchestrator",
        "agentruntimeorchestrator": "AgentRuntimeOrchestrator",
        "runtimeorchestrator": "AgentRuntimeOrchestrator",
    }
    if lowered in aliases:
        return aliases[lowered]
    for separator in ("/", ":", ",", "+", "&"):
        if separator in lowered:
            for part in lowered.split(separator):
                canonical = aliases.get(part.strip())
                if canonical:
                    return canonical
    for token in (" and ", " then ", " -> "):
        if token in lowered:
            for part in lowered.split(token):
                canonical = aliases.get(part.strip())
                if canonical:
                    return canonical
    if text in {
        "RetrievalMemory",
        "TheoryDeveloper",
        "SimulationEvaluator",
        "AlgorithmEngineer",
        "GeneratedCodeSemanticReviewer",
        "FormalTargetSemanticReviewer",
        "FormalizationEvaluator",
        "CriticEvaluator",
        "ArchitectCoordinator",
        "AgentRuntimeOrchestrator",
    }:
        return text
    return ""


RUNTIME_RESEARCH_WORKSPACE_BY_SUBSYSTEM = {
    "RetrievalMemory": "retrieval",
    "TheoryDeveloper": "theory",
    "SimulationEvaluator": "scientific_coding",
    "AlgorithmEngineer": "scientific_coding",
    "GeneratedCodeSemanticReviewer": "scientific_coding",
    "FormalTargetSemanticReviewer": "formalization",
    "FormalizationEvaluator": "formalization",
    "CriticEvaluator": "critic",
    "ArchitectCoordinator": "architect",
    "AgentRuntimeOrchestrator": "architect",
}


def _runtime_research_subsystem(value: Any) -> str:
    raw_subsystem = str(value or "").strip()
    canonical_subsystem = _canonical_architect_subsystem(raw_subsystem)
    if canonical_subsystem:
        return canonical_subsystem
    if raw_subsystem in RUNTIME_RESEARCH_WORKSPACE_BY_SUBSYSTEM:
        return raw_subsystem
    return ""


def _runtime_research_workspace(value: Any) -> str:
    """Return the durable workspace authorized by an Architect plan row."""

    return RUNTIME_RESEARCH_WORKSPACE_BY_SUBSYSTEM.get(
        _runtime_research_subsystem(value),
        "",
    )


RUNTIME_PRIMARY_EVIDENCE_SUBSYSTEMS = (
    "AlgorithmEngineer",
    "SimulationEvaluator",
    "FormalizationEvaluator",
)


def _runtime_outer_graph_plan(
    architect_context: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    plan = _architect_runtime_plan(architect_context)
    planned = list(
        dict.fromkeys(
            _runtime_research_subsystem(row.get("subsystem"))
            for row in plan.get("subsystem_execution_plan", []) or []
            if isinstance(row, Mapping)
            and _runtime_research_subsystem(row.get("subsystem"))
        )
    )
    primary = [
        subsystem
        for subsystem in planned
        if subsystem in RUNTIME_PRIMARY_EVIDENCE_SUBSYSTEMS
    ]
    contract = plan.get("evidence_contract", {})
    contract = dict(contract) if isinstance(contract, Mapping) else {}
    if str(contract.get("recommended_research_path", "") or "") == "proof_first":
        primary = [
            subsystem
            for subsystem in (
                "FormalizationEvaluator",
                "AlgorithmEngineer",
                "SimulationEvaluator",
            )
            if subsystem in primary
        ]
    return primary, {
        "plan": plan,
        "planned_subsystems": planned,
        "evidence_contract": contract,
    }


def _runtime_executed_subsystems(
    *,
    architect_context: Mapping[str, Any],
) -> set[str]:
    executed: set[str] = set()
    for outcome in architect_context.get(
        "runtime_outer_graph_workspace_outcomes", []
    ) or []:
        if not isinstance(outcome, Mapping):
            continue
        subsystem = str(outcome.get("source_subsystem", "") or "")
        if subsystem not in RUNTIME_PRIMARY_EVIDENCE_SUBSYSTEMS:
            continue
        expected_parents = _runtime_workspace_parent_artifact_ids(
            subsystem,
            architect_context,
        )
        observed_parents = outcome.get("parent_artifact_ids", {})
        if (
            expected_parents
            and isinstance(observed_parents, Mapping)
            and dict(observed_parents) == expected_parents
        ):
            executed.add(subsystem)
    manifest_field_by_subsystem = {
        "AlgorithmEngineer": "algorithm_sandbox_manifest_id",
        "SimulationEvaluator": "simulation_manifest_id",
    }
    for review in architect_context.get(
        "accepted_generated_code_semantic_reviews", []
    ) or []:
        if not isinstance(review, Mapping):
            continue
        subsystem = str(review.get("source_subsystem", "") or "")
        manifest_field = manifest_field_by_subsystem.get(subsystem, "")
        if (
            not manifest_field
            or str(review.get("overall_verdict", "") or "").strip().upper()
            != "ACCEPT"
        ):
            continue
        current_manifest_id = str(
            architect_context.get(manifest_field, "") or ""
        ).strip()
        expected_parents = _runtime_workspace_parent_artifact_ids(
            subsystem,
            architect_context,
        )
        observed_parents = review.get("parent_artifact_ids", {})
        if (
            current_manifest_id
            and str(review.get("source_manifest_id", "") or "").strip()
            == current_manifest_id
            and expected_parents
            and isinstance(observed_parents, Mapping)
            and dict(observed_parents) == expected_parents
        ):
            executed.add(subsystem)
    return executed


def _runtime_workspace_parent_artifact_ids(
    subsystem_name: str,
    task_inputs: Mapping[str, Any],
) -> dict[str, str]:
    """Identify the immutable parents whose change starts a fresh workspace lineage."""

    parent_fields = {
        "TheoryDeveloper": ("retrieval_memory_manifest_id",),
        "AlgorithmEngineer": ("theory_packet_id",),
        "SimulationEvaluator": (
            "theory_packet_id",
            "algorithm_sandbox_manifest_id",
        ),
        "FormalizationEvaluator": ("theory_packet_id",),
    }.get(subsystem_name, ())
    return {
        field: value
        for field in parent_fields
        if (value := str(task_inputs.get(field, "") or "").strip())
    }


def _runtime_task_parent_artifact_ids(
    subsystem_name: str,
    task_inputs: Mapping[str, Any],
) -> dict[str, str]:
    context = task_inputs.get("architect_context", {})
    parent_inputs = dict(context) if isinstance(context, Mapping) else {}
    parent_inputs.update(
        {
            field: value
            for field in (
                "retrieval_memory_manifest_id",
                "theory_packet_id",
                "algorithm_sandbox_manifest_id",
            )
            if (value := task_inputs.get(field)) not in (None, "")
        }
    )
    return _runtime_workspace_parent_artifact_ids(
        subsystem_name,
        parent_inputs,
    )


def _runtime_outer_graph_context(
    *,
    task: AgentTask,
    context_task: AgentTask | None = None,
    result: AgentStepResult,
    subsystem_name: str,
    iteration: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    context_inputs = (context_task or task).inputs
    inputs = context_inputs if isinstance(context_inputs, Mapping) else {}
    raw_context = inputs.get("architect_context", {})
    context = dict(raw_context) if isinstance(raw_context, Mapping) else {}
    context.pop("environment_feedback", None)
    context.pop("architect_feedback_route_decision", None)
    for field in (
        "theory_packet_id",
        "simulation_manifest_id",
        "algorithm_sandbox_manifest_id",
        "formalization_manifest_id",
    ):
        value = str(inputs.get(field, "") or "").strip()
        if value:
            context[field] = value
    context_field_by_kind = {
        "TheoryDerivationPacket": "theory_packet_id",
        "RuntimeTheoryDerivationPacket": "theory_packet_id",
        "RuntimeAlgorithmSandboxManifest": "algorithm_sandbox_manifest_id",
        "RuntimeSimulationManifest": "simulation_manifest_id",
        "RuntimeFormalizationManifest": "formalization_manifest_id",
    }
    for artifact_id, artifact in result.produced_artifacts.items():
        if not isinstance(artifact, Mapping):
            continue
        context_field = context_field_by_kind.get(
            str(artifact.get("artifact_kind", "") or "")
        )
        if context_field:
            context[context_field] = str(artifact_id)
    outcome = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeOuterGraphWorkspaceOutcome",
        "source_iteration": iteration,
        "source_task_id": task.task_id,
        "source_subsystem": subsystem_name,
        "local_status": result.status,
        "failure_classification": result.failure_classification,
        "rationale": result.rationale,
        "produced_artifact_ids": list(result.produced_artifacts),
        "parent_artifact_ids": _runtime_task_parent_artifact_ids(
            subsystem_name,
            task.inputs,
        ),
        "runtime_authored_research_content": False,
        "proof_evidence_status": "OUTER_GRAPH_WORKSPACE_OUTCOME_NOT_PROOF_EVIDENCE",
    }
    prior_outcomes = [
        dict(row)
        for row in context.get("runtime_outer_graph_workspace_outcomes", []) or []
        if isinstance(row, Mapping)
    ]
    outcome_lineage = (
        outcome["source_subsystem"],
        stable_hash(outcome["parent_artifact_ids"]),
    )
    prior_outcomes = [
        row
        for row in prior_outcomes
        if (
            str(row.get("source_subsystem", "") or ""),
            stable_hash(dict(row.get("parent_artifact_ids", {}) or {})),
        )
        != outcome_lineage
    ]
    prior_outcomes.append(outcome)
    context["runtime_outer_graph_workspace_outcomes"] = prior_outcomes[-12:]
    return context, outcome


def _runtime_outer_graph_continuation(
    *,
    iteration: int,
    task: AgentTask,
    subsystem_name: str,
    result: AgentStepResult,
    blackboard: BlackboardState,
    runtime_config: ResearchAgentRuntimeConfig | None,
    proposed_next_task: AgentTask | None = None,
) -> AgentStepResult | None:
    if runtime_config is None or subsystem_name in {
        "ArchitectCoordinator",
        "CriticEvaluator",
    }:
        return None
    if (
        result.status in {"BLOCKED", "FAILED"}
        and str(result.failure_classification or "").startswith(
            "scientific_consumer_"
        )
    ):
        return None
    if subsystem_name == "TheoryDeveloper" and result.status in {
        "BLOCKED",
        "FAILED",
    }:
        # Every primary evidence lane depends on a currently accepted theory
        # artifact. An older rejected parent is not a substitute for a failed
        # model-owned revision.
        return None
    context, outcome = _runtime_outer_graph_context(
        task=task,
        context_task=proposed_next_task,
        result=result,
        subsystem_name=subsystem_name,
        iteration=iteration,
    )
    primary, plan_context = _runtime_outer_graph_plan(context)
    planned = plan_context["planned_subsystems"]
    if not planned:
        return None
    executed = _runtime_executed_subsystems(architect_context=context)
    remaining = [subsystem for subsystem in primary if subsystem not in executed]
    next_owner = remaining[0] if remaining else ""
    if not next_owner and "CriticEvaluator" in planned and (
        "CriticEvaluator" not in executed
    ):
        next_owner = "CriticEvaluator"
    if not next_owner:
        return None
    theory_packet_id = _architect_context_theory_packet_id(context)
    theory_artifact_available = bool(
        theory_packet_id
        and (
            theory_packet_id in result.produced_artifacts
            or _architect_blackboard_artifact_present(
                blackboard,
                theory_packet_id,
            )
        )
    )
    if (
        next_owner in RUNTIME_PRIMARY_EVIDENCE_SUBSYSTEMS
        and not theory_artifact_available
    ):
        return None

    question_inputs = (proposed_next_task or task).inputs
    question_payload = question_inputs.get("question", {})
    if not isinstance(question_payload, Mapping) or not question_payload:
        return None
    question = _question_from_payload(question_payload)
    plan = plan_context["plan"]
    routing = _architect_initial_routing_decision(
        question=question,
        packet=plan,
        architect_context=context,
        packet_id=str(
            context.get("architect_coordinator_proposal_id", "")
            or plan.get("packet_id", "")
            or stable_hash(plan)[:20]
        ),
        runtime_config=runtime_config,
        blackboard=blackboard,
        requested_subsystem_override=next_owner,
        routing_source_override="runtime_required_evidence_topology",
        honor_requested_subsystem=True,
    )
    next_task = routing["task"]
    if next_owner == "CriticEvaluator":
        critic_inputs = dict(next_task.inputs)
        critic_context = dict(critic_inputs.get("architect_context", {}) or {})
        critic_context["environment_feedback"] = outcome
        critic_inputs["architect_context"] = critic_context
        critic_inputs["environment_feedback"] = outcome
        next_task = replace(next_task, inputs=critic_inputs)
    if result.status in {"BLOCKED", "FAILED"} and result.rationale:
        blackboard.active_blockers.append(result.rationale)
    observation = EnvironmentObservation(
        observation_type="runtime_required_evidence_lane_continuation",
        summary=(
            f"{subsystem_name} ended locally with {result.status}; outer runtime "
            f"continues the frozen evidence topology at {next_owner}."
        ),
        payload={
            "source_task_id": task.task_id,
            "source_subsystem": subsystem_name,
            "local_status": result.status,
            "local_failure_classification": result.failure_classification,
            "executed_subsystems": sorted(executed),
            "remaining_primary_subsystems": remaining,
            "next_owner_subsystem": next_owner,
            "model_routing_call_used": False,
            "runtime_authored_research_content": False,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )
    return AgentStepResult(
        status="REROUTE",
        rationale=(
            "AgentRuntime preserved the local workspace outcome and continued an "
            "unvisited workspace required by the already frozen evidence topology."
        ),
        produced_artifacts=result.produced_artifacts,
        observations=result.observations + (observation,),
        tool_calls=result.tool_calls,
        evidence_entries=result.evidence_entries,
        next_task=next_task,
        failure_classification="runtime_required_evidence_lane_continuation",
    )


def _lineage_bound_semantic_review_return_to_source_producer(
    *,
    task: AgentTask,
    subsystem_name: str,
    next_task: AgentTask,
    blackboard: BlackboardState,
) -> bool:
    """Recognize a reviewer backedge to the exact immutable source producer."""

    if (
        subsystem_name != GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
        or next_task.owner_subsystem
        not in GENERATED_CODE_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS
    ):
        return False
    work_order_id = str(task.inputs.get("work_order_id", "") or "")
    work_order = blackboard.artifacts.get(work_order_id, {})
    if not isinstance(work_order, Mapping) or not work_order:
        return False
    if (
        work_order.get("artifact_kind")
        != "RuntimeGeneratedCodeSemanticReviewWorkOrder"
        or stable_hash(work_order)
        != str(task.inputs.get("work_order_hash", "") or "")
        or str(work_order.get("source_subsystem", "") or "")
        != next_task.owner_subsystem
    ):
        return False
    source_task_continuation_id = str(
        work_order.get("source_task_continuation_id", "") or ""
    )
    source_task_continuation = blackboard.artifacts.get(
        source_task_continuation_id,
        {},
    )
    source_task_ref = work_order.get("source_task_ref", {})
    if (
        not isinstance(source_task_continuation, Mapping)
        or source_task_continuation.get("artifact_kind")
        != "RuntimeAgentTaskContinuation"
        or stable_hash(source_task_continuation)
        != str(work_order.get("source_task_continuation_hash", "") or "")
        or source_task_continuation.get("task_ref") != source_task_ref
        or not isinstance(source_task_ref, Mapping)
        or source_task_ref.get("artifact_kind") != "AgentTaskRef"
    ):
        return False
    try:
        source_task = restore_agent_task_continuation(
            source_task_continuation,
            blackboard.artifacts,
        )
    except ValueError:
        return False
    if (
        agent_task_reference(source_task) != source_task_ref
        or source_task.task_id
        != str(work_order.get("source_task_id", "") or "")
        or source_task.owner_subsystem != next_task.owner_subsystem
    ):
        return False
    feedback = next_task.inputs.get("environment_feedback", {})
    if not isinstance(feedback, Mapping) or (
        feedback.get("feedback_type")
        != "generated_code_semantic_review_feedback"
        or str(feedback.get("source_subsystem", "") or "")
        != next_task.owner_subsystem
        or not str(
            feedback.get("semantic_review_execution_id", "") or ""
        )
        or not str(feedback.get("semantic_review_packet_id", "") or "")
        or not str(feedback.get("semantic_review_packet_hash", "") or "")
    ):
        return False
    try:
        revision_count = int(
            next_task.inputs.get(
                "generated_code_semantic_review_revision_count", 0
            )
            or 0
        )
        prior_count = int(work_order.get("review_revision_count", 0) or 0)
    except (TypeError, ValueError):
        return False
    return revision_count == prior_count + 1


def _lineage_bound_execution_return_to_source_producer(
    *,
    result: AgentStepResult,
    next_task: AgentTask,
    blackboard: BlackboardState,
) -> bool:
    """Preserve a raw consumer backedge to the exact source-owning workspace."""

    feedback = next_task.inputs.get("environment_feedback", {})
    if not isinstance(feedback, Mapping):
        return False
    transport = feedback.get("observation_transport", {})
    if (
        not isinstance(transport, Mapping)
        or transport.get("same_source_producer_must_revise") is not True
        or transport.get("runtime_selected_source_edit") is not False
        or str(feedback.get("failure_classification", "") or "")
        != result.failure_classification
    ):
        return False
    source_manifest_id = str(
        feedback.get("source_manifest_artifact_id", "") or ""
    ).strip()
    expected_manifest = {
        "AlgorithmEngineer": (
            "algorithm_sandbox_manifest_id",
            "RuntimeAlgorithmSandboxManifest",
        ),
        "SimulationEvaluator": (
            "simulation_manifest_id",
            "RuntimeSimulationManifest",
        ),
    }.get(next_task.owner_subsystem)
    if not source_manifest_id or expected_manifest is None:
        return False
    manifest_field, manifest_kind = expected_manifest
    source_manifest = blackboard.artifacts.get(source_manifest_id, {})
    return bool(
        isinstance(source_manifest, Mapping)
        and source_manifest.get("artifact_kind") == manifest_kind
        and str(source_manifest.get("manifest_id", "") or "")
        == source_manifest_id
        and str(feedback.get(manifest_field, "") or "")
        == source_manifest_id
        and str(feedback.get("source_manifest_content_hash", "") or "")
        == stable_hash(dict(source_manifest))
    )


def _runtime_transition_policy(
    *,
    iteration: int,
    task: AgentTask,
    subsystem_name: str,
    result: AgentStepResult,
    blackboard: BlackboardState,
    runtime_config: ResearchAgentRuntimeConfig | None = None,
) -> AgentStepResult:
    next_task = result.next_task
    if next_task is None:
        continuation = _runtime_outer_graph_continuation(
            iteration=iteration,
            task=task,
            subsystem_name=subsystem_name,
            result=result,
            blackboard=blackboard,
            runtime_config=runtime_config,
        )
        return continuation or result
    if subsystem_name == "ArchitectCoordinator":
        return result
    if next_task.owner_subsystem == "ArchitectCoordinator":
        return result
    if next_task.owner_subsystem == subsystem_name:
        return result
    if _lineage_bound_execution_return_to_source_producer(
        result=result,
        next_task=next_task,
        blackboard=blackboard,
    ):
        return result
    if (
        subsystem_name == GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
        and next_task.owner_subsystem == "SimulationEvaluator"
        and SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY in next_task.budget
        and "consumer_resume_manifest" in next_task.inputs
    ):
        return result
    next_context = next_task.inputs.get("architect_context", {})
    completed_next_lane = bool(
        isinstance(next_context, Mapping)
        and next_task.owner_subsystem
        in _runtime_executed_subsystems(architect_context=next_context)
    )
    if completed_next_lane and subsystem_name != "CriticEvaluator":
        continuation = _runtime_outer_graph_continuation(
            iteration=iteration,
            task=task,
            subsystem_name=subsystem_name,
            result=result,
            blackboard=blackboard,
            runtime_config=runtime_config,
            proposed_next_task=next_task,
        )
        if continuation is not None:
            return continuation
    reviewer_source_revision = (
        subsystem_name == GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
        and result.status == "REVISE"
        and next_task.owner_subsystem
        in GENERATED_CODE_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS
    )
    if reviewer_source_revision:
        if _lineage_bound_semantic_review_return_to_source_producer(
            task=task,
            subsystem_name=subsystem_name,
            next_task=next_task,
            blackboard=blackboard,
        ):
            return result
        return AgentStepResult(
            status="BLOCKED",
            rationale=(
                "Generated-code semantic review proposed a source revision "
                "without a valid immutable source-task reference."
            ),
            produced_artifacts=result.produced_artifacts,
            observations=result.observations
            + (
                EnvironmentObservation(
                    observation_type=(
                        "generated_code_semantic_review_source_lineage_rejected"
                    ),
                    summary=(
                        "The reviewer backedge did not reproduce the exact "
                        "hash-bound source task recorded by its work order."
                    ),
                    payload={
                        "review_task_id": task.task_id,
                        "proposed_source_task_id": next_task.task_id,
                        "proposed_source_subsystem": (
                            next_task.owner_subsystem
                        ),
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                ),
            ),
            tool_calls=result.tool_calls,
            evidence_entries=result.evidence_entries,
            failure_classification=(
                "generated_code_semantic_review_source_lineage_invalid"
            ),
        )
    return result


def _architect_initial_objective(
    context: Mapping[str, Any],
    subsystem: str,
    default: str,
) -> str:
    feedback_route = context.get("architect_feedback_route_decision", {})
    if (
        isinstance(feedback_route, Mapping)
        and feedback_route.get("decision") == "ROUTE"
        and str(feedback_route.get("selected_subsystem", "") or "") == subsystem
    ):
        routed_objective = str(feedback_route.get("objective", "") or "").strip()
        if routed_objective:
            return routed_objective
    row = _architect_subsystem_plan(context, subsystem)
    objective = str(row.get("objective", "") or "").strip()
    return objective or default






RUNTIME_RETRIEVAL_RETURN_OWNERS = {
    "TheoryDeveloper",
    "FormalizationEvaluator",
}


def _runtime_retrieval_return_owner(task: AgentTask) -> str:
    requested = str(
        task.inputs.get("retrieval_return_to_subsystem", "")
        or task.inputs.get("return_to_subsystem", "")
        or ""
    ).strip()
    return requested if requested in RUNTIME_RETRIEVAL_RETURN_OWNERS else "TheoryDeveloper"


class RetrievalMemoryRuntimeSubsystem:
    name = "RetrievalMemory"

    def __init__(self, *, formal_source_retriever: Any | None = None) -> None:
        self.formal_source_retriever = (
            formal_source_retriever or build_default_formal_source_retriever()
        )

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        retrieval_control = _architect_control_payload(context, "RetrievalMemory")
        (
            problem,
            theorem_goals,
            problem_authority,
        ) = _formalization_runtime_problem_and_goals(
            question,
            task.inputs,
        )
        knowledge = retrieve_problem_knowledge(question, problem, theorem_goals, k=8)
        paper_sources = retrieve_paper_sources(question, problem, theorem_goals, k=5)
        reset_provider_runtime_diagnostics(self.formal_source_retriever)
        formal_hits = _runtime_formal_source_hits(
            self.formal_source_retriever,
            problem=problem,
            theorem_goals=theorem_goals,
            k=4,
        )
        formal_source_provider_diagnostics = provider_runtime_diagnostics(
            self.formal_source_retriever
        )
        formal_source_provider_topology = provider_descriptor(
            self.formal_source_retriever
        )
        return_owner = _runtime_retrieval_return_owner(task)
        manifest_id = "retrieval_memory_manifest:" + stable_hash([task.task_id, question.id, formal_hits])[:20]
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeRetrievalMemoryManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "runtime_architect_control": retrieval_control,
            "research_problem_authority": problem_authority,
            **problem_authority,
            "problem": _problem_to_json(problem),
            "theorem_goals": [_theorem_goal_to_json(row) for row in theorem_goals],
            "knowledge_cards": [_knowledge_card_to_json(row) for row in knowledge],
            "paper_sources": [_paper_source_to_json(row) for row in paper_sources],
            "formal_source_hits": formal_hits,
            "formal_source_provider_topology": formal_source_provider_topology,
            "formal_source_provider_diagnostics": formal_source_provider_diagnostics,
            "retrieval_return_to_subsystem": return_owner,
            "counts": {
                "knowledge_cards": len(knowledge),
                "paper_sources": len(paper_sources),
                "formal_source_hit_groups": len(formal_hits),
                "formal_source_hits": sum(len(row.get("hits", [])) for row in formal_hits),
                "formal_source_provider_calls": len(
                    formal_source_provider_diagnostics
                ),
                "formal_source_provider_failures": sum(
                    1
                    for row in formal_source_provider_diagnostics
                    if str(row.get("status", "") or "") != "ok"
                ),
                "formal_source_hits_with_provider_provenance": sum(
                    1
                    for group in formal_hits
                    for hit in group.get("hits", []) or []
                    if isinstance(hit, Mapping) and hit.get("provenance")
                ),
            },
            "boundary": (
                "Retrieval memory supplies source, analogy, and Lean declaration context. "
                "Retrieval hits are not proof evidence and must be checked by downstream gates."
            ),
        }
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="retrieval_memory",
            status="RETRIEVAL_CONTEXT_RECORDED",
            boundary=str(manifest["boundary"]),
            payload={
                **manifest["counts"],
                "problem_formalization_source": str(
                    problem_authority.get("problem_formalization_source", "")
                ),
                "architect_acceptance_gate": retrieval_control.get("acceptance_gate", ""),
            },
        )
        retrieval_context_body = {
            "knowledge_cards": manifest["knowledge_cards"],
            "paper_sources": manifest["paper_sources"],
            "formal_source_hits": manifest["formal_source_hits"],
            "formal_source_provider_topology": formal_source_provider_topology,
            "formal_source_provider_diagnostics": formal_source_provider_diagnostics,
            "research_problem_authority": problem_authority,
            "boundary": manifest["boundary"],
        }
        retrieval_context_id = (
            "retrieval_context:"
            + stable_hash([manifest_id, retrieval_context_body])[:20]
        )
        retrieval_context = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeRetrievalContext",
            "context_id": retrieval_context_id,
            "source_retrieval_memory_manifest_id": manifest_id,
            "source_retrieval_memory_manifest_hash": stable_hash(manifest),
            **retrieval_context_body,
            "proof_evidence_status": "RETRIEVAL_CONTEXT_NOT_PROOF_EVIDENCE",
        }
        context["retrieval_memory_manifest_id"] = manifest_id
        context["retrieval_context"] = retrieval_context
        if return_owner == "TheoryDeveloper":
            next_task = AgentTask(
                task_id=f"theory:{question.id}:{stable_hash(manifest_id)[:8]}",
                owner_subsystem="TheoryDeveloper",
                objective="Derive a statistical theory proposal using retrieval memory context.",
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": context,
                },
                allowed_tools=("model_backend", "rag_memory"),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "TheoryDeveloper",
                    ("theory_derivation_packet",),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "TheoryDeveloper",
                    "validated theory packet with proof boundary and retrieval context",
                ),
                stop_condition="theory packet routed to simulation feedback",
            )
        else:
            next_inputs = dict(task.inputs)
            next_inputs.pop("retrieval_return_to_subsystem", None)
            next_inputs.pop("return_to_subsystem", None)
            next_inputs["question"] = _question_to_payload(question)
            next_inputs["architect_context"] = context
            next_inputs["retrieval_memory_manifest_id"] = manifest_id
            next_task = AgentTask(
                task_id=(
                    f"retrieval-return:{return_owner}:{question.id}:"
                    f"{stable_hash(manifest_id)[:8]}"
                ),
                owner_subsystem=return_owner,
                objective=(
                    "Resume the pending formal task with branch-provenanced Lean "
                    "retrieval context and preserve the exact theorem lineage."
                ),
                inputs=next_inputs,
                allowed_tools=tuple(
                    dict.fromkeys(
                        (
                            *task.allowed_tools,
                            "model_backend",
                            "formal_source_retriever",
                            "proof_search",
                            "local_lean",
                        )
                    )
                ),
                expected_artifacts=task.expected_artifacts,
                acceptance_gate=(
                    task.acceptance_gate
                    or "retrieved declarations are consumed by the target owner and "
                    "any candidate is rerun under local Lean/AXLE"
                ),
                stop_condition=task.stop_condition,
            )
        return AgentStepResult(
            status="REROUTE",
            rationale=(
                "Runtime retrieval memory recorded paper, knowledge, and "
                f"formal-source context for {return_owner}."
            ),
            produced_artifacts={
                manifest_id: manifest,
                retrieval_context_id: retrieval_context,
            },
            observations=(
                EnvironmentObservation(
                    observation_type="retrieval_memory",
                    summary=(
                        f"knowledge={len(knowledge)} papers={len(paper_sources)} "
                        f"formal_hit_groups={len(formal_hits)}"
                    ),
                    payload=manifest["counts"],
                ),
            ),
            tool_calls=(
                ToolCallRecord(
                    tool_name="FormalSourceSearchProvider.search",
                    inputs={
                        "provider_topology": formal_source_provider_topology,
                        "theorem_goal_count": len(theorem_goals),
                    },
                    exit_status=(
                        "provider_failures_present"
                        if manifest["counts"]["formal_source_provider_failures"]
                        else "0"
                    ),
                    stdout_summary=(
                        "hits="
                        f"{manifest['counts']['formal_source_hits']} "
                        "provider_calls="
                        f"{manifest['counts']['formal_source_provider_calls']}"
                    ),
                    safety_boundary=LEAN_PROVIDER_BOUNDARY,
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
        )


def _runtime_metric_protocol_authoring_required(
    *,
    evidence_contract: Mapping[str, Any],
    architect_context: Mapping[str, Any],
) -> bool:
    if not _runtime_research_evaluation_contract_flag(
        evidence_contract,
        "typed_metric_contracts",
    ):
        return False
    metric_gate = architect_context.get("architect_metric_protocol_gate", {})
    explicit_gate_block = bool(
        isinstance(metric_gate, Mapping)
        and metric_gate.get("artifact_kind")
        == "RuntimeArchitectMetricProtocolGate"
        and metric_gate.get("execution_authorized") is False
    )
    accepted_protocol = bool(
        evidence_contract.get("empirical_metric_requirements")
        and evidence_contract.get("empirical_metric_protocol_phase")
        == METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED
        and evidence_contract.get("metric_protocol_execution_authorized") is True
        and not explicit_gate_block
    )
    return not accepted_protocol


def _theory_developer_revision_binding_blocked_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    validation_errors: Sequence[str],
) -> AgentStepResult:
    errors = [str(value) for value in validation_errors if str(value).strip()]
    artifact_id = "theory_developer_revision_binding_blocked:" + stable_hash(
        [task.task_id, question.id, errors]
    )[:20]
    boundary = (
        "The runtime rejected an ambiguous or stale upstream-theory revision "
        "lineage before any TheoryDeveloper model call. This control decision is "
        "not statistical acceptance or proof evidence."
    )
    artifact = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeTheoryDeveloperRevisionBindingBlocked",
        "block_id": artifact_id,
        "question_id": question.id,
        "task_id": task.task_id,
        "validation_errors": errors,
        "model_call_authorized": False,
        "execution_authorized": False,
        "proof_evidence_status": (
            "THEORY_DEVELOPER_REVISION_BINDING_BLOCKED_NOT_PROOF_EVIDENCE"
        ),
        "boundary": boundary,
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, artifact_id])[:20],
        task_id=task.task_id,
        artifact_id=artifact_id,
        evidence_type="theory_developer_revision_binding_rejection",
        status="BLOCKED_BEFORE_THEORY_MODEL_CALL",
        boundary=boundary,
        payload={
            "validation_errors": errors,
            "proof_evidence_status": artifact["proof_evidence_status"],
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "TheoryDeveloper revision feedback did not identify one exact immutable "
            "parent and review lineage."
        ),
        produced_artifacts={artifact_id: artifact},
        observations=(
            EnvironmentObservation(
                observation_type="theory_developer_revision_binding_rejected",
                summary="TheoryDeveloper revision lineage failed closed",
                payload={
                    "block_id": artifact_id,
                    "validation_errors": errors,
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification="theory_developer_revision_binding_invalid",
    )


class TheoryDeveloperRuntimeSubsystem:
    name = "TheoryDeveloper"

    def __init__(
        self,
        *,
        theory_developer: LLMTheoryDeveloperAgent,
        n_runs: int,
        seed: int,
    ) -> None:
        self.theory_developer = theory_developer
        self.n_runs = n_runs
        self.seed = seed

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        context["runtime_task"] = _runtime_task_prompt_summary(task)
        if "environment_feedback" in task.inputs:
            context["environment_feedback"] = task.inputs["environment_feedback"]
        metric_protocol_revision_feedback = (
            theory_developer_source_environment_feedback(context)
        )
        if not (
            isinstance(metric_protocol_revision_feedback, Mapping)
            and metric_protocol_revision_feedback.get("artifact_kind")
            == METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND
        ):
            metric_protocol_revision_feedback = {}
        routed_environment_feedback = context.get("environment_feedback", {})
        if metric_protocol_revision_feedback:
            parent_theory_packet_id = str(
                metric_protocol_revision_feedback.get(
                    "source_theory_packet_id", ""
                )
                or ""
            )
            parent_theory_packet = blackboard.artifacts.get(
                parent_theory_packet_id, {}
            )
            feedback_errors = (
                metric_protocol_preexecution_review_observation_errors(
                    metric_protocol_revision_feedback,
                    question_id=question.id,
                    parent_theory_packet=(
                        parent_theory_packet
                        if isinstance(parent_theory_packet, Mapping)
                        else None
                    ),
                )
            )
            if feedback_errors:
                return metric_protocol_preexecution_review_observation_blocked_result(
                    task=task,
                    question=question,
                    feedback=metric_protocol_revision_feedback,
                    validation_errors=feedback_errors,
                )
            prior_theory_material = build_theory_informed_metric_protocol_material(
                theory_packet=parent_theory_packet,
                theory_packet_id=parent_theory_packet_id,
                retrieval_context=(
                    context.get("retrieval_context", {})
                    if isinstance(context.get("retrieval_context", {}), Mapping)
                    else {}
                ),
            )
            context["metric_protocol_prior_theory_material"] = prior_theory_material
            revision_binding = build_theory_developer_revision_binding(
                revision_source="metric_protocol_preexecution_review",
                question_id=question.id,
                source_feedback=metric_protocol_revision_feedback,
                theory_material=prior_theory_material,
                feedback_id=str(
                    metric_protocol_revision_feedback.get("feedback_id", "") or ""
                ),
                upstream_theory_revision_count=int(
                    metric_protocol_revision_feedback.get(
                        "upstream_theory_revision_count", 0
                    )
                    or 0
                ),
                max_upstream_theory_revisions=int(
                    metric_protocol_revision_feedback.get(
                        "max_upstream_theory_revisions", 0
                    )
                    or 0
                ),
                execution_results_observed=False,
            )
            binding_errors = theory_developer_revision_binding_errors(
                revision_binding,
                question_id=question.id,
            )
            if binding_errors:
                return _theory_developer_revision_binding_blocked_result(
                    task=task,
                    question=question,
                    validation_errors=binding_errors,
                )
            context[THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY] = (
                revision_binding
            )
        elif (
            (
                isinstance(
                    context.get("architect_feedback_route_decision", {}),
                    Mapping,
                )
                and context.get("architect_feedback_route_decision", {}).get(
                    "artifact_kind"
                )
                == "ArchitectFeedbackRouteDecision"
                and context.get("architect_feedback_route_decision", {}).get(
                    "decision"
                )
                == "ROUTE"
                and context.get("architect_feedback_route_decision", {}).get(
                    "selected_subsystem"
                )
                == "TheoryDeveloper"
            )
            or (
                isinstance(routed_environment_feedback, Mapping)
                and routed_environment_feedback
                and routed_environment_feedback.get(
                    "model_route_required_for_cross_owner_revision"
                )
                is True
            )
        ):
            revision_binding, binding_errors = (
                build_architect_routed_theory_revision_binding(
                    architect_context=context,
                    question_id=question.id,
                    artifacts=blackboard.artifacts,
                )
            )
            if binding_errors:
                return _theory_developer_revision_binding_blocked_result(
                    task=task,
                    question=question,
                    validation_errors=binding_errors,
                )
            context[THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY] = (
                revision_binding
            )
        theory_config = getattr(self.theory_developer, "config", None)
        theory_provider = getattr(self.theory_developer, "provider", None)
        theory_provider_name = str(
            getattr(theory_provider, "provider_name", "")
            or getattr(theory_config, "provider_name", "")
            or ""
        ).strip().lower()
        environment_feedback = context.get("environment_feedback", {})
        recovery_checkpoint = (
            environment_feedback.get("recovery_checkpoint", {})
            if isinstance(environment_feedback, Mapping)
            else {}
        )
        recovering_interface_stage = bool(
            isinstance(recovery_checkpoint, Mapping)
            and recovery_checkpoint.get("failed_phase")
            == "estimator_interface_authoring"
        )
        theory_artifact_workspace_expected = bool(
            callable(
                getattr(theory_provider, "generate_client_tool_turn", None)
            )
            and not recovering_interface_stage
        )
        try:
            with agent_runtime_substage(
                "theory_packet_generation",
                metadata={
                    "model_tier": str(
                        getattr(theory_config, "serious_model_tier", "")
                        or getattr(theory_config, "model_tier", "")
                        or ""
                    ),
                    "provider": theory_provider_name,
                    "provider_structured_output_expected": bool(
                        theory_provider_name == "anthropic"
                        and not theory_artifact_workspace_expected
                    ),
                    "theory_artifact_workspace_expected": (
                        theory_artifact_workspace_expected
                    ),
                },
            ):
                packet = self.theory_developer.derive(
                    question,
                    architect_context=context,
                )
        except PacketValidationError as exc:
            return _theory_developer_packet_validation_failure_result(
                task=task,
                question=question,
                exc=exc,
            )
        active_revision_binding = context.get(
            THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY, {}
        )
        active_revision_binding = (
            dict(active_revision_binding)
            if isinstance(active_revision_binding, Mapping)
            else {}
        )
        if active_revision_binding:
            packet = dict(packet)
            packet["parent_theory_packet_id"] = str(
                active_revision_binding.get("source_theory_packet_id", "") or ""
            )
            packet["theory_developer_revision_binding_id"] = str(
                active_revision_binding.get("binding_id", "") or ""
            )
            packet["theory_developer_revision_source"] = str(
                active_revision_binding.get("revision_source", "") or ""
            )
            packet["theory_developer_revision_feedback_id"] = str(
                active_revision_binding.get("feedback_id", "") or ""
            )
            packet["runtime_revision_artifact"] = True
        if metric_protocol_revision_feedback:
            packet = dict(packet)
            packet["metric_protocol_upstream_theory_revision_feedback_id"] = str(
                metric_protocol_revision_feedback.get("feedback_id", "") or ""
            )
            packet["metric_protocol_rejection_manifest_id"] = str(
                metric_protocol_revision_feedback.get(
                    "source_metric_protocol_rejection_manifest_id", ""
                )
                or ""
            )
            packet["metric_protocol_upstream_theory_revision_count"] = int(
                metric_protocol_revision_feedback.get(
                    "upstream_theory_revision_count", 0
                )
                or 0
            )
            packet["runtime_revision_artifact"] = True
        context.pop(THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY, None)
        context.pop("theory_developer_source_environment_feedback", None)
        theory_control = _architect_control_payload(context, "TheoryDeveloper")
        packet["runtime_architect_control"] = theory_control
        packet_id = _unique_runtime_artifact_id(
            blackboard,
            str(packet["packet_id"]),
            task_id=task.task_id,
        )
        if packet_id != str(packet["packet_id"]):
            packet = dict(packet)
            packet["base_packet_id"] = str(packet["packet_id"])
            packet["packet_id"] = packet_id
            packet["runtime_revision_artifact"] = True
        prior_theory_packet_id = str(
            context.get("previous_theory_packet_id", "")
            or context.get("theory_packet_id", "")
            or ""
        ).strip()
        theory_revision = bool(
            prior_theory_packet_id and prior_theory_packet_id != packet_id
        )
        if theory_revision:
            packet = dict(packet)
            packet.setdefault("parent_theory_packet_id", prior_theory_packet_id)
            packet["runtime_revision_artifact"] = True
            context = _context_with_invalidated_theory_descendants(context)
        context["theory_packet_id"] = packet_id
        theory_derivation_contract = dict(
            packet.get("theory_derivation_contract", {}) or {}
        )
        raw_theory_workspace = packet.get("llm_client_tool_loop", {})
        theory_workspace_evidence = (
            {
                field: deepcopy(raw_theory_workspace.get(field))
                for field in (
                    "artifact_kind",
                    "artifact_id",
                    "workspace_id",
                    "workspace_operation",
                    "accepted",
                    "model_owned_theory",
                    "runtime_edited_theory",
                    "reads",
                    "submissions",
                    "changed_artifact_names",
                    "provider",
                    "model",
                    "model_tier",
                    "transcript_fingerprint",
                )
                if field in raw_theory_workspace
            }
            if isinstance(raw_theory_workspace, Mapping)
            else {}
        )
        theory_evidence_payload = {
            "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
            "kernel_verified": False,
            "architect_acceptance_gate": theory_control.get(
                "acceptance_gate", ""
            ),
            "theory_derivation_contract": theory_derivation_contract,
        }
        if theory_workspace_evidence:
            theory_evidence_payload["llm_client_tool_loop"] = (
                theory_workspace_evidence
            )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, packet_id])[:20],
            task_id=task.task_id,
            artifact_id=packet_id,
            evidence_type="llm_theory_derivation",
            status="PROPOSAL_RECORDED_REQUIRES_GATES",
            boundary=KERNEL_PROOF_BOUNDARY,
            payload=theory_evidence_payload,
        )
        simulation_task = AgentTask(
            task_id=f"simulation:{question.id}:{stable_hash(packet_id)[:8]}",
            owner_subsystem="SimulationEvaluator",
            objective=(
                "Evaluate the LLM theory proposal against executable registered "
                "simulation environments and record implementation gaps."
            ),
            inputs={
                "question": _question_to_payload(question),
                "theory_packet_id": packet_id,
                "architect_context": context,
                "n_runs": self.n_runs,
                "seed": self.seed,
            },
            allowed_tools=("research_simulator", "python"),
            expected_artifacts=_architect_expected_artifacts(
                context,
                "SimulationEvaluator",
                ("simulation_manifest", "implementation_gap_manifest"),
            ),
            acceptance_gate=_architect_acceptance_gate(
                context,
                "SimulationEvaluator",
                "simulation manifest plus explicit proof/implementation boundaries",
            ),
            stop_condition="simulation diagnostics recorded or rerouted to TheoryDeveloper",
        )
        evidence_contract = _architect_runtime_plan(context).get(
            "evidence_contract", {}
        )
        if not isinstance(evidence_contract, Mapping):
            evidence_contract = {}
        requires_generated_algorithm = bool(
            evidence_contract.get(
                "research_evaluation_requires_generated_algorithm_code"
            )
            is True
        )
        dependency_rebuild_required = bool(
            theory_revision and requires_generated_algorithm
        )
        if dependency_rebuild_required:
            dependency_rebuild = {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "RuntimeTheoryRevisionDependencyRebuild",
                "source_task_id": task.task_id,
                "parent_theory_packet_id": prior_theory_packet_id,
                "revised_theory_packet_id": packet_id,
                "invalidated_descendant_roles": [
                    "simulation_manifest",
                    "algorithm_sandbox_manifest",
                    "formalization_manifest",
                ],
                "next_dependency": "exploratory_simulation_manifest",
                "empirical_evaluation_phase": (
                    EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
                ),
                "proof_evidence_status": (
                    "THEORY_REVISION_DEPENDENCY_REBUILD_NOT_PROOF_EVIDENCE"
                ),
                "boundary": (
                    "A revised theory packet invalidates hash-bound downstream "
                    "artifacts. Exploratory regeneration is orchestration work, "
                    "not confirmatory empirical or theorem proof evidence."
                ),
            }
            packet["runtime_dependency_rebuild"] = dependency_rebuild
            context["runtime_dependency_rebuild"] = dependency_rebuild
            context["empirical_evaluation_phase"] = (
                EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            )
            simulation_inputs = dict(simulation_task.inputs)
            simulation_inputs["architect_context"] = context
            simulation_inputs["empirical_evaluation_phase"] = (
                EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            )
            simulation_task = replace(
                simulation_task,
                objective=(
                    "Regenerate a non-confirmatory, theory-bound simulation "
                    "handoff before rebuilding algorithm and confirmatory "
                    "simulation descendants."
                ),
                inputs=simulation_inputs,
            )
        current_theory_material = build_theory_informed_metric_protocol_material(
            theory_packet=packet,
            theory_packet_id=packet_id,
            retrieval_context=(
                context.get("retrieval_context", {})
                if isinstance(context.get("retrieval_context", {}), Mapping)
                else {}
            ),
        )
        context = _architect_context_with_bound_metric_protocol_theory_material(
            architect_context=context,
            theory_material=current_theory_material,
        )
        if active_revision_binding.get("revision_source") == (
            "architect_routed_environment_observations"
        ):
            context = consume_architect_routed_theory_revision(
                architect_context=context,
                revision_binding=active_revision_binding,
                revised_theory_packet_id=packet_id,
                revised_theory_packet_hash=str(
                    current_theory_material.get("source_theory_packet_hash", "")
                    or ""
                ),
            )
        implementation_gaps = _implementation_gaps(
            packet,
            [],
            require_generated_adapter=requires_generated_algorithm,
        )
        if implementation_gaps:
            context["implementation_gaps"] = implementation_gaps
        requires_metric_protocol_gate = _runtime_metric_protocol_authoring_required(
            evidence_contract=evidence_contract,
            architect_context=context,
        )
        theory_material_artifacts: dict[str, dict[str, Any]] = {}
        current_theory_material_id = (
            "theory_metric_protocol_material:"
            + stable_hash(current_theory_material)[:20]
        )
        theory_material_artifacts[current_theory_material_id] = dict(
            current_theory_material
        )
        context["architect_metric_protocol_theory_material"] = (
            current_theory_material
        )
        prior_theory_material = context.get(
            "metric_protocol_prior_theory_material", {}
        )
        if (
            isinstance(prior_theory_material, Mapping)
            and prior_theory_material.get("artifact_kind")
            == "RuntimeTheoryInformedMetricProtocolMaterial"
        ):
            prior_theory_material_id = (
                "theory_metric_protocol_material:"
                + stable_hash(dict(prior_theory_material))[:20]
            )
            theory_material_artifacts[prior_theory_material_id] = dict(
                prior_theory_material
            )
            context["metric_protocol_prior_theory_material"] = (
                prior_theory_material
            )
        simulation_inputs = dict(simulation_task.inputs)
        simulation_inputs["architect_context"] = context
        simulation_task = replace(simulation_task, inputs=simulation_inputs)
        architect_route_artifacts: dict[str, dict[str, Any]] = {}
        if requires_metric_protocol_gate:
            prior_metric_gate = context.get(
                "architect_metric_protocol_gate", {}
            )
            if not isinstance(prior_metric_gate, Mapping):
                prior_metric_gate = {}
            upstream_theory_revision_count = int(
                prior_metric_gate.get("upstream_theory_revision_count", 0) or 0
            )
            max_upstream_theory_revisions = int(
                prior_metric_gate.get("max_upstream_theory_revisions", 0) or 0
            )
            rejection_manifest_ids = [
                str(value)
                for value in prior_metric_gate.get(
                    "rejection_manifest_ids", []
                )
                or []
                if str(value).strip()
            ]
            context["theory_packet_id"] = packet_id
            context["architect_metric_protocol_theory_material"] = (
                current_theory_material
            )
            context["architect_metric_protocol_gate"] = {
                "artifact_kind": "RuntimeArchitectMetricProtocolGate",
                "source_theory_packet_id": packet_id,
                "source_theory_packet_hash": str(
                    current_theory_material.get(
                        "source_theory_packet_hash", ""
                    )
                    or ""
                ),
                "source_theory_revision_feedback_id": str(
                    metric_protocol_revision_feedback.get("feedback_id", "")
                    if metric_protocol_revision_feedback
                    else ""
                ),
                "rejection_manifest_ids": rejection_manifest_ids,
                "upstream_theory_revision_count": upstream_theory_revision_count,
                "max_upstream_theory_revisions": max_upstream_theory_revisions,
                "required_disposition": (
                    "THEORY_EXECUTION_PREFLIGHT_ACCEPTED_BEFORE_IMPLEMENTATION"
                ),
                "execution_authorized": False,
                "algorithm_execution_authorized": False,
                "confirmatory_simulation_authorized": False,
                "consumed": False,
                "proof_evidence_status": (
                    "ARCHITECT_METRIC_PROTOCOL_GATE_NOT_PROOF_EVIDENCE"
                ),
                "boundary": (
                    "Theory is available, but implementation remains blocked until "
                    "the estimand, DGP, identifiability, and executability pass "
                    "independent source-grounded preflight. Full confirmatory metric "
                    "authoring remains deferred until independent implementation "
                    "review accepts a hash-bound interface."
                ),
            }
            metric_protocol_task = AgentTask(
                task_id=(
                    f"architect-metric-protocol:{question.id}:"
                    f"{stable_hash([task.task_id, packet_id])[:8]}"
                ),
                owner_subsystem="ArchitectCoordinator",
                objective=(
                    "Independently review the theory, DGP, estimand, identifiability, "
                    "and finite executability before generated implementation and "
                    "deferred metric protocol authoring."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": context,
                    "runtime_architect_operation": (
                        RUNTIME_ARCHITECT_OPERATION_THEORY_PREFLIGHT
                    ),
                },
                allowed_tools=("model_backend", "blackboard", "evidence_ledger"),
                expected_artifacts=(
                    "architect_theory_execution_preflight",
                    "architect_theory_execution_preflight_acceptance",
                ),
                acceptance_gate=(
                    "source-grounded theory preflight receives independent ACCEPT; "
                    "only exploratory implementation is then authorized"
                ),
                stop_condition=(
                    "preflight is accepted and routed to AlgorithmEngineer, or a "
                    "typed theory revision preserves the full review lineage"
                ),
            )
            next_task = metric_protocol_task
        elif dependency_rebuild_required:
            next_task = simulation_task
        else:
            route_feedback_body = {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "RuntimeTheoryDerivationAvailableObservation",
                "feedback_type": "theory_derivation_available",
                "feedback_source": "TheoryDeveloper",
                "question_id": question.id,
                "source_task_id": task.task_id,
                "source_theory_packet_id": packet_id,
                "source_theory_packet_hash": str(
                    current_theory_material.get("source_theory_packet_hash", "")
                    or ""
                ),
                "theory_revision": theory_revision,
                "runtime_selected_owner": False,
                "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
                "boundary": (
                    "A validated model-authored theory packet is available. This "
                    "observation selects no empirical or formal worker and is not "
                    "simulation, implementation, or proof evidence."
                ),
            }
            route_feedback_id = (
                "theory_derivation_available_observation:"
                + stable_hash(route_feedback_body)[:20]
            )
            route_feedback = {
                **route_feedback_body,
                "feedback_id": route_feedback_id,
                "active_observation_id": route_feedback_id,
                "observation_status": "CURRENT_ACTIVE_OBSERVATION",
            }
            architect_route_artifacts[route_feedback_id] = route_feedback
            context["environment_feedback"] = route_feedback
            context["runtime_feedback_loop"] = {
                **(
                    dict(context.get("runtime_feedback_loop", {}))
                    if isinstance(context.get("runtime_feedback_loop", {}), Mapping)
                    else {}
                ),
                "source_subsystem": "TheoryDeveloper",
                "handoff": "validated_theory_to_architect_model",
                "source_theory_packet_id": packet_id,
                "runtime_selected_owner": False,
            }
            next_task = AgentTask(
                task_id=(
                    f"architect-after-theory:{question.id}:"
                    f"{stable_hash([task.task_id, route_feedback_id])[:8]}"
                ),
                owner_subsystem="ArchitectCoordinator",
                objective=(
                    "Choose the next evidence-producing subsystem from the validated "
                    "theory packet and current model-authored research plan."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "theory_packet_id": packet_id,
                    "architect_context": context,
                    "environment_feedback": route_feedback,
                    "runtime_architect_operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
                },
                allowed_tools=("model_backend", "blackboard", "evidence_ledger"),
                expected_artifacts=("architect_feedback_route_decision",),
                acceptance_gate=(
                    "the Architect model selects one available evidence-producing "
                    "subsystem or records a typed blocker"
                ),
                stop_condition=(
                    "Architect model selects the next worker or records a blocker"
                ),
            )
        return AgentStepResult(
            status="REROUTE",
            rationale=(
                "LLM TheoryDeveloper produced a proposal; runtime is routing it to "
                "independent source-grounded theory/executability preflight before "
                "AlgorithmEngineer; full metric authoring remains deferred until "
                "independent implementation acceptance."
                if requires_metric_protocol_gate
                else (
                    "LLM TheoryDeveloper revised the theory packet; runtime is "
                    "rebuilding hash-bound empirical descendants through a "
                    "non-confirmatory simulation handoff."
                    if dependency_rebuild_required
                    else "LLM TheoryDeveloper produced a proposal; runtime returned "
                    "the validated theory observation to ArchitectCoordinator so the "
                    "model can choose simulation-first, proof-first, or another "
                    "available evidence worker."
                )
            ),
            produced_artifacts={
                packet_id: packet,
                **theory_material_artifacts,
                **architect_route_artifacts,
            },
            observations=(
                EnvironmentObservation(
                    observation_type="llm_theory_derivation_packet",
                    summary="validated LLM theory proposal recorded for downstream gates",
                    payload={
                        "packet_id": packet_id,
                        "n_theorem_cards": len(packet.get("theorem_cards", []) or []),
                        "n_estimator_specs": len(packet.get("estimator_specs", []) or []),
                        "n_derivation_steps": theory_derivation_contract.get(
                            "n_derivation_steps", 0
                        ),
                        "n_equation_chain_steps": theory_derivation_contract.get(
                            "n_equation_chain_steps", 0
                        ),
                        "n_assumption_ledger_rows": theory_derivation_contract.get(
                            "n_assumption_ledger_rows", 0
                        ),
                        "has_formalization_handoff": theory_derivation_contract.get(
                            "has_formalization_handoff", False
                        ),
                        "theory_revision_dependency_rebuild_required": (
                            dependency_rebuild_required
                        ),
                        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
                    },
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
        )


def _theory_developer_packet_validation_failure_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    exc: PacketValidationError,
) -> AgentStepResult:
    """Record exhausted in-call validation without creating another theory task."""

    validation_errors = [str(error) for error in exc.errors if str(error)]
    raw_recovery_checkpoint = getattr(exc, "recovery_checkpoint", None)
    recovery_checkpoint = (
        deepcopy(dict(raw_recovery_checkpoint))
        if isinstance(raw_recovery_checkpoint, Mapping)
        and raw_recovery_checkpoint.get("artifact_kind")
        in {
            THEORY_DEVELOPER_STAGE_CHECKPOINT_KIND,
            THEORY_WORKSPACE_CHECKPOINT_KIND,
        }
        and raw_recovery_checkpoint.get("question_id") == question.id
        and raw_recovery_checkpoint.get("kernel_verified") is False
        else {}
    )
    truncation_detected = _packet_validation_error_truncation_detected(exc)
    failure_classification = (
        "theory_developer_packet_truncated_json"
        if truncation_detected
        else "theory_developer_packet_validation_failed"
    )
    failure_id = (
        "theory_developer_validation_failure:"
        + stable_hash([task.task_id, exc.validation_label, validation_errors, exc.history])[:20]
    )
    rejected_candidate = (
        deepcopy(dict(exc.last_invalid_packet))
        if isinstance(exc.last_invalid_packet, Mapping)
        else {}
    )
    rejected_candidate_fingerprint = (
        stable_hash(rejected_candidate) if rejected_candidate else ""
    )
    feedback = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeTheoryDeveloperValidationObservations",
        "feedback_id": failure_id,
        "feedback_type": "theory_developer_packet_validation_observations",
        "question_id": question.id,
        "source_task_id": task.task_id,
        "failure_classification": failure_classification,
        "validation_label": exc.validation_label,
        "validation_errors": validation_errors,
        "attempts": exc.attempts,
        "truncation_detected": truncation_detected,
        "rejected_candidate": rejected_candidate,
        "rejected_candidate_fingerprint": rejected_candidate_fingerprint,
        "recovery_checkpoint_available": bool(recovery_checkpoint),
        **(
            {"recovery_checkpoint": recovery_checkpoint}
            if recovery_checkpoint
            else {}
        ),
        "runtime_edits_candidate": False,
        "model_route_required_for_cross_owner_revision": False,
        "proof_evidence_status": (
            "THEORY_DEVELOPER_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "The TheoryDeveloper already received validator errors during its "
            "bounded model-owned generation or workspace call. Runtime records the "
            "available candidate and checkpoint but does not create an outer "
            "same-owner retry."
        ),
    }
    failure_artifact = {
        **feedback,
        "artifact_kind": "RuntimeTheoryDeveloperValidationFailure",
        "failure_id": failure_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": _question_to_payload(question),
        "task_id": task.task_id,
        "structured_output_retry_history": exc.history,
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, failure_id])[:20],
        task_id=task.task_id,
        artifact_id=failure_id,
        evidence_type="theory_developer_packet_validation_failure",
        status="VALIDATION_FAILED_RECORDED_NOT_THEORY_OR_PROOF_EVIDENCE",
        boundary=str(feedback["boundary"]),
        payload={
            "validation_errors": validation_errors,
            "truncation_detected": truncation_detected,
            "runtime_edits_candidate": False,
            "proof_evidence_status": feedback["proof_evidence_status"],
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "TheoryDeveloper exhausted its in-call model-owned validation loop. "
            "The rejected artifact and exact observations remain failed at their "
            "source owner; runtime did not create an Architect routing loop."
        ),
        produced_artifacts={failure_id: failure_artifact},
        observations=(
            EnvironmentObservation(
                observation_type="theory_developer_packet_validation_failure",
                summary="; ".join(validation_errors)[:500],
                payload={
                    "failure_id": failure_id,
                    "failure_classification": failure_classification,
                    "validation_errors": validation_errors,
                    "truncation_detected": truncation_detected,
                    "recovery_checkpoint_available": bool(recovery_checkpoint),
                    "proof_evidence_status": (
                        "THEORY_DEVELOPER_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
                    ),
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification=failure_classification,
    )


def _packet_validation_error_truncation_detected(
    exc: PacketValidationError,
) -> bool:
    final_row = next(
        (
            row
            for row in reversed(exc.history)
            if isinstance(row, Mapping)
        ),
        {},
    )
    metadata = final_row.get("response_metadata", {})
    if not isinstance(metadata, Mapping):
        return False
    haystack = " ".join(
        str(metadata.get(key, "") or "").lower()
        for key in ("provider_stop_reason", "provider_incomplete_details")
    )
    if any(
        marker in haystack
        for marker in ("max_tokens", "length", "output_limit")
    ):
        return True
    usage = metadata.get("provider_usage", {})
    if isinstance(usage, Mapping):
        try:
            output_tokens = int(usage.get("output_tokens", 0) or 0)
            request_tokens = int(final_row.get("request_max_tokens", 0) or 0)
        except (TypeError, ValueError):
            return False
        if request_tokens > 0 and output_tokens >= request_tokens:
            return True
    return False


def _runtime_theory_trace_consumption_contract(
    *,
    consumer_subsystem: str,
    source_theory_packet_id: str,
    theory_packet: Mapping[str, Any],
) -> dict[str, Any]:
    packet = theory_packet if isinstance(theory_packet, Mapping) else {}
    contract = (
        packet.get("theory_derivation_contract", {})
        if isinstance(packet.get("theory_derivation_contract", {}), Mapping)
        else {}
    )
    derivation = (
        packet.get("theory_derivation_packet", {})
        if isinstance(packet.get("theory_derivation_packet", {}), Mapping)
        else {}
    )
    n_derivation_steps = _runtime_safe_int(
        contract.get(
            "n_derivation_steps",
            _runtime_safe_list_len(derivation.get("derivation_steps", [])),
        )
    )
    n_equation_chain_steps = _runtime_safe_int(
        contract.get(
            "n_equation_chain_steps",
            _runtime_safe_list_len(derivation.get("equation_chain", [])),
        )
    )
    n_assumption_ledger_rows = _runtime_safe_int(
        contract.get(
            "n_assumption_ledger_rows",
            _runtime_safe_list_len(derivation.get("assumption_ledger", [])),
        )
    )
    has_formalization_handoff = bool(
        contract.get("has_formalization_handoff", False)
        or (
            isinstance(derivation.get("formalization_handoff", {}), Mapping)
            and derivation.get("formalization_handoff")
        )
    )
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "TheoryTraceConsumptionContract",
        "contract_source": "agent_runtime_handoff",
        "source_theory_packet_id": source_theory_packet_id,
        "consumer_subsystem": consumer_subsystem,
        "theory_derivation_trace_supplied": bool(packet and source_theory_packet_id),
        "n_derivation_steps_supplied": n_derivation_steps,
        "n_equation_chain_steps_supplied": n_equation_chain_steps,
        "n_assumption_ledger_rows_supplied": n_assumption_ledger_rows,
        "has_formalization_handoff": has_formalization_handoff,
        "target_ids": _source_theorem_target_ids_from_row(packet),
        "proof_evidence_status": "THEORY_TRACE_CONSUMPTION_NOT_PROOF_EVIDENCE",
        "boundary": THEORY_TRACE_CONSUMPTION_BOUNDARY,
    }


def _runtime_handoff_artifact_missing_result_if_needed(
    *,
    source_subsystem: str,
    task: AgentTask,
    question: OpenResearchQuestion,
    artifact_id: str,
    artifact: Any,
    artifact_role: str,
    expected_artifact_kind: str,
) -> AgentStepResult | None:
    if not artifact_id:
        return None
    if isinstance(artifact, Mapping) and artifact:
        return None
    feedback = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeHandoffArtifactMissingFeedback",
        "feedback_source": source_subsystem,
        "trigger": "RUNTIME_HANDOFF_ARTIFACT_MISSING",
        "failure_classification": "runtime_handoff_artifact_missing",
        "failure_classifications": [f"missing_{artifact_role}"],
        "question_id": question.id,
        "source_task_id": task.task_id,
        "source_owner_subsystem": task.owner_subsystem,
        "missing_artifact_id": artifact_id,
        "missing_artifact_role": artifact_role,
        "expected_artifact_kind": expected_artifact_kind,
        "proof_evidence_status": (
            "HANDOFF_ARTIFACT_MISSING_FEEDBACK_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "This is an AgentRuntime handoff-integrity gate. It is not simulation, "
            "algorithm execution, formalization, or Lean/kernel proof evidence."
        ),
    }
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            f"{source_subsystem} could not find the explicit upstream "
            f"{artifact_role} handoff artifact. Runtime will not regenerate a "
            "replacement because that would break immutable artifact lineage."
        ),
        observations=(
            EnvironmentObservation(
                observation_type="runtime_handoff_artifact_missing",
                summary=(
                    f"missing {artifact_role} artifact {artifact_id}; checkpoint "
                    "or artifact-store recovery is required"
                ),
                payload=feedback,
            ),
        ),
        failure_classification="runtime_handoff_artifact_missing",
    )


def _runtime_missing_simulation_handoff_result_if_needed(
    *,
    source_subsystem: str,
    task: AgentTask,
    question: OpenResearchQuestion,
    simulation_manifest_id: str,
    simulation_manifest: Any,
) -> AgentStepResult | None:
    return _runtime_handoff_artifact_missing_result_if_needed(
        source_subsystem=source_subsystem,
        task=task,
        question=question,
        artifact_id=simulation_manifest_id,
        artifact=simulation_manifest,
        artifact_role="simulation_manifest",
        expected_artifact_kind="RuntimeSimulationManifest",
    )


def _runtime_missing_algorithm_handoff_result_if_needed(
    *,
    source_subsystem: str,
    task: AgentTask,
    question: OpenResearchQuestion,
    algorithm_sandbox_manifest_id: str,
    algorithm_manifest: Any,
) -> AgentStepResult | None:
    return _runtime_handoff_artifact_missing_result_if_needed(
        source_subsystem=source_subsystem,
        task=task,
        question=question,
        artifact_id=algorithm_sandbox_manifest_id,
        artifact=algorithm_manifest,
        artifact_role="algorithm_sandbox_manifest",
        expected_artifact_kind="RuntimeAlgorithmSandboxManifest",
    )


def _runtime_missing_formalization_handoff_result_if_needed(
    *,
    source_subsystem: str,
    task: AgentTask,
    question: OpenResearchQuestion,
    formalization_manifest_id: str,
    formalization_manifest: Any,
) -> AgentStepResult | None:
    return _runtime_handoff_artifact_missing_result_if_needed(
        source_subsystem=source_subsystem,
        task=task,
        question=question,
        artifact_id=formalization_manifest_id,
        artifact=formalization_manifest,
        artifact_role="formalization_manifest",
        expected_artifact_kind="RuntimeFormalizationManifest",
    )


GENERATED_CODE_SEMANTIC_REVIEW_AUTHOR_SUBSYSTEM_BY_RUNTIME_SOURCE = {
    "AlgorithmEngineer": "AlgorithmEngineer",
    "SimulationEvaluator": "SimulationEngineer",
}


def _runtime_generated_code_semantic_review_source_responsibility_contract(
    *,
    source_subsystem: str,
    architect_evidence_contract: Mapping[str, Any],
) -> dict[str, Any]:
    author_subsystem = (
        GENERATED_CODE_SEMANTIC_REVIEW_AUTHOR_SUBSYSTEM_BY_RUNTIME_SOURCE.get(
            source_subsystem,
            "",
        )
    )
    raw_requirements = architect_evidence_contract.get(
        "empirical_metric_requirements",
        [],
    )
    all_requirements = [
        dict(row)
        for row in raw_requirements or []
        if isinstance(row, Mapping)
    ]
    assigned_requirements = generated_metric_requirements_from_context(
        all_requirements,
        target_subsystem=author_subsystem,
    )
    assigned_ids = {
        str(row.get("requirement_id", "") or "").strip()
        for row in assigned_requirements
        if str(row.get("requirement_id", "") or "").strip()
    }
    sibling_only_refs = [
        {
            "requirement_id": str(row.get("requirement_id", "") or ""),
            "target_subsystems": [
                str(value)
                for value in row.get("target_subsystems", []) or []
                if str(value).strip()
            ],
        }
        for row in all_requirements
        if str(row.get("requirement_id", "") or "").strip() not in assigned_ids
    ]
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "runtime_source_subsystem": source_subsystem,
        "generated_code_author_subsystem": author_subsystem,
        "assigned_empirical_metric_requirements": assigned_requirements,
        "assigned_requirement_ids": sorted(assigned_ids),
        "sibling_only_requirement_refs": sibling_only_refs,
        "artifact_review_rule": (
            "Judge whether this artifact computes and emits the statistic assigned by "
            "its empirical requirements, source proposal, interface, and supplied "
            "theory premises. Do not adjudicate realized threshold pass or fail; the "
            "empirical evaluator owns that decision. Exact execution may expose source "
            "semantics, interface, argument, or non-vacuity defects. A theory "
            "premise is not automatically a requirement for finite-data code to "
            "test or prove that premise at runtime. Require an observable check only "
            "when an assigned protocol, interface precondition, or explicit source "
            "claim owns it. Do not require one artifact to implement requirements "
            "assigned only to a sibling generated-code author."
        ),
        "system_coverage_owner": "CriticEvaluator",
        "system_coverage_rule": (
            "Final cross-artifact question coverage is decided only after the "
            "separately reviewed sibling artifacts are assembled by AgentRuntime "
            "and audited by CriticEvaluator. This per-artifact review must still "
            "reject unsupported claims made by its own proposal."
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_SOURCE_RESPONSIBILITY_CONTRACT_NOT_PROOF_EVIDENCE"
        ),
    }


def _runtime_generated_code_semantic_review_rows(
    manifest: Mapping[str, Any],
    *,
    source_subsystem: str,
) -> list[dict[str, Any]]:
    if source_subsystem == "SimulationEvaluator":
        raw_rows = manifest.get("generated_simulation_sandbox_prototypes", [])
        id_key = "simulation_id"
    elif source_subsystem == "AlgorithmEngineer":
        raw_rows = manifest.get("prototypes", [])
        id_key = "estimator_id"
    else:
        return []
    rows: list[dict[str, Any]] = []
    for raw_row in raw_rows or []:
        if not isinstance(raw_row, Mapping):
            continue
        row = dict(raw_row)
        if not (
            row.get("smoke_passed") is True
            or row.get("execution_smoke_passed") is True
        ):
            continue
        if not str(row.get("script_path", "") or "").strip():
            continue
        if not str(row.get("script_hash", "") or "").strip():
            continue
        if not str(row.get("result_path", "") or "").strip():
            continue
        if not str(row.get("result_hash", "") or "").strip():
            continue
        artifact_id = str(row.get(id_key, "") or "").strip()
        if not artifact_id:
            continue
        row["semantic_review_artifact_id"] = artifact_id
        rows.append(row)
    return rows


def _runtime_generated_code_semantic_review_dispatch(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    source_subsystem: str,
    source_manifest: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    proposal_packet: Mapping[str, Any] | None,
    architect_context: Mapping[str, Any],
    deferred_next_task: AgentTask,
    blackboard_artifacts: Mapping[str, Any],
    max_revisions: int,
) -> dict[str, Any] | None:
    review_rows = _runtime_generated_code_semantic_review_rows(
        source_manifest,
        source_subsystem=source_subsystem,
    )
    if not review_rows:
        return None
    manifest_id = str(source_manifest.get("manifest_id", "") or "").strip()
    theory_packet_id = str(theory_packet.get("packet_id", "") or "").strip()
    proposal = dict(proposal_packet or {})
    proposal_packet_id = str(proposal.get("packet_id", "") or "").strip()
    empirical_evaluation_phase = str(
        source_manifest.get("empirical_evaluation_phase", "") or ""
    ).strip()
    confirmatory_empirical_evidence_eligible = bool(
        source_manifest.get("confirmatory_empirical_evidence_eligible", True)
    )
    review_revision_count = max(
        0,
        int(task.inputs.get("generated_code_semantic_review_revision_count", 0) or 0),
    )
    reviewed_artifacts = [
        {
            "artifact_id": str(row["semantic_review_artifact_id"]),
            "row_hash": stable_hash(row),
            "script_path": str(row.get("script_path", "") or ""),
            "script_hash": str(row.get("script_hash", "") or ""),
            "result_path": str(row.get("result_path", "") or ""),
            "result_hash": str(row.get("result_hash", "") or ""),
            "runtime_seed": row.get("runtime_seed"),
            "runtime_replicates": row.get("runtime_replicates"),
            "metric_contract_set_id": str(
                row.get("metric_contract_set_id", "") or ""
            ),
            "metric_requirement_set_id": str(
                row.get("metric_requirement_set_id", "") or ""
            ),
        }
        for row in review_rows
    ]
    evidence_contract = _architect_control_payload(
        architect_context,
        source_subsystem,
    ).get("evidence_contract", {})
    runtime_contract = architect_context.get(
        "runtime_requested_evidence_contract",
        {},
    )
    if not isinstance(runtime_contract, Mapping):
        runtime_contract = {}
    research_evaluation = any(
        _is_runtime_research_evaluation_mode(value)
        for value in (
            evidence_contract.get("evaluation_mode", "")
            if isinstance(evidence_contract, Mapping)
            else "",
            runtime_contract.get("evaluation_mode", ""),
            architect_context.get("runtime_evaluation_mode", ""),
        )
    )
    source_responsibility_contract = (
        _runtime_generated_code_semantic_review_source_responsibility_contract(
            source_subsystem=source_subsystem,
            architect_evidence_contract=(
                evidence_contract
                if isinstance(evidence_contract, Mapping)
                else {}
            ),
        )
    )
    work_order_id = "generated_code_semantic_review_work_order:" + stable_hash(
        [task.task_id, manifest_id, reviewed_artifacts, review_revision_count]
    )[:20]
    persisted_source_task = replace(
        task,
        inputs=compact_runtime_artifact_references(
            task.inputs,
            blackboard_artifacts,
        ),
    )
    persisted_deferred_task = replace(
        deferred_next_task,
        inputs=compact_runtime_artifact_references(
            deferred_next_task.inputs,
            blackboard_artifacts,
        ),
    )
    deferred_task_payload = asdict(persisted_deferred_task)
    (
        deferred_task_continuation_id,
        deferred_task_continuation,
        deferred_task_artifacts,
    ) = materialize_agent_task_continuation(
        persisted_deferred_task,
        schema_version=RUNTIME_SCHEMA_VERSION,
    )
    deferred_task_continuation_ref = agent_task_continuation_reference(
        deferred_task_continuation
    )
    (
        source_task_continuation_id,
        source_task_continuation,
        source_task_artifacts,
    ) = materialize_agent_task_continuation(
        persisted_source_task,
        schema_version=RUNTIME_SCHEMA_VERSION,
        linked_input_references={
            stable_hash(deferred_task_payload): deferred_task_continuation_ref,
        },
    )
    continuation_artifacts = {
        **deferred_task_artifacts,
        **source_task_artifacts,
    }
    work_order = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewWorkOrder",
        "work_order_id": work_order_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "source_task_id": task.task_id,
        "source_subsystem": source_subsystem,
        "target_subsystem": GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM,
        "source_manifest_id": manifest_id,
        "source_manifest_hash": stable_hash(source_manifest),
        "theory_packet_id": theory_packet_id,
        "theory_packet_hash": stable_hash(theory_packet),
        "proposal_packet_id": proposal_packet_id,
        "proposal_packet_hash": stable_hash(proposal) if proposal else "",
        "source_agent": str(proposal.get("source_agent", "") or ""),
        "source_model": str(proposal.get("model", "") or ""),
        "source_model_tier": str(proposal.get("model_tier", "") or ""),
        "reviewed_artifacts": reviewed_artifacts,
        "architect_evidence_contract": (
            dict(evidence_contract) if isinstance(evidence_contract, Mapping) else {}
        ),
        "source_responsibility_contract": source_responsibility_contract,
        "source_responsibility_contract_fingerprint": stable_hash(
            source_responsibility_contract
        ),
        "research_evaluation": research_evaluation,
        "review_revision_count": review_revision_count,
        "max_revisions": max(0, int(max_revisions or 0)),
        "empirical_evaluation_phase": empirical_evaluation_phase,
        "confirmatory_empirical_evidence_eligible": (
            confirmatory_empirical_evidence_eligible
        ),
        "source_task_ref": agent_task_reference(persisted_source_task),
        "deferred_next_task_ref": agent_task_reference(
            persisted_deferred_task
        ),
        "source_task_continuation_id": source_task_continuation_id,
        "source_task_continuation_hash": stable_hash(
            source_task_continuation
        ),
        "deferred_next_task_continuation_id": (
            deferred_task_continuation_id
        ),
        "deferred_next_task_continuation_hash": stable_hash(
            deferred_task_continuation
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_WORK_ORDER_NOT_PROOF_EVIDENCE"
        ),
        "evidence_boundary": GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
    }
    work_order_hash = stable_hash(work_order)
    review_task = AgentTask(
        task_id=(
            f"semantic-review:{question.id}:"
            f"{stable_hash([work_order_id, work_order_hash])[:10]}"
        ),
        owner_subsystem=GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM,
        objective=(
            "Independently review the statistical and experimental semantics of "
            "the exact exploratory code, actual runtime arguments, raw diagnostics, "
            "and theory derivation without treating the run as confirmatory evidence."
            if not confirmatory_empirical_evidence_eligible
            else "Independently review the statistical and experimental semantics of "
            "the exact generated code, actual runtime arguments, result schema, "
            "theory derivation, and Architect-authored interface contract."
        ),
        inputs={
            "question": _question_to_payload(question),
            "work_order_id": work_order_id,
            "work_order_hash": work_order_hash,
        },
        allowed_tools=("model_backend", "filesystem", "blackboard"),
        expected_artifacts=(
            "generated_code_semantic_review_materialization",
            "generated_code_semantic_review_packet",
            "generated_code_semantic_review_execution_manifest",
        ),
        acceptance_gate=(
            "an independent lineage-bound semantic review accepts the exact "
            "artifact for diagnostic use without promoting empirical claims, or "
            "routes concrete feedback to its author"
            if not confirmatory_empirical_evidence_eligible
            else "an independent lineage-bound semantic review accepts every exact "
            "generated artifact or routes concrete feedback to its coding agent"
        ),
        stop_condition=(
            "semantic review is accepted, a fresh coding-agent revision is "
            "scheduled, or the bounded semantic-review loop records a blocker"
        ),
    )
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, work_order_id])[:20],
        task_id=task.task_id,
        artifact_id=work_order_id,
        evidence_type="generated_code_semantic_review_work_order",
        status="WORK_ORDER_RECORDED_NOT_SEMANTIC_ACCEPTANCE",
        boundary=GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
        payload={
            "source_subsystem": source_subsystem,
            "empirical_evaluation_phase": empirical_evaluation_phase,
            "confirmatory_empirical_evidence_eligible": (
                confirmatory_empirical_evidence_eligible
            ),
            "source_manifest_id": manifest_id,
            "n_reviewed_artifacts": len(reviewed_artifacts),
            "next_owner_subsystem": GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )
    observation = EnvironmentObservation(
        observation_type="generated_code_semantic_review_dispatched",
        summary=(
            f"{len(reviewed_artifacts)} exact generated artifact(s) routed to "
            "an independent semantic reviewer"
        ),
        payload={
            "work_order_id": work_order_id,
            "work_order_hash": work_order_hash,
            "source_subsystem": source_subsystem,
            "source_manifest_id": manifest_id,
            "reviewed_artifact_ids": [
                str(row.get("artifact_id", "")) for row in reviewed_artifacts
            ],
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )
    return {
        "work_order_id": work_order_id,
        "work_order": work_order,
        "artifacts": {
            **continuation_artifacts,
            work_order_id: work_order,
        },
        "next_task": review_task,
        "evidence": evidence,
        "observation": observation,
    }


def _runtime_generated_code_semantic_review_prior_observations(
    *,
    work_order: Mapping[str, Any],
    source_task: Mapping[str, Any],
    source_subsystem: str,
) -> dict[str, Any]:
    """Recover prior semantic observations carried by the model-selected route."""

    source_inputs = (
        source_task.get("inputs", {})
        if isinstance(source_task, Mapping)
        else {}
    )
    if not isinstance(source_inputs, Mapping):
        return {}
    architect_context = source_inputs.get("architect_context", {})
    architect_context = (
        architect_context
        if isinstance(architect_context, Mapping)
        else {}
    )
    environment_feedback = source_inputs.get("environment_feedback", {})
    environment_feedback = (
        environment_feedback
        if isinstance(environment_feedback, Mapping)
        else {}
    )
    nested_feedback = environment_feedback.get(
        "generated_code_semantic_review_feedback",
        {},
    )
    candidates = [
        architect_context.get(
            "runtime_generated_code_semantic_review_replan",
            {},
        ),
        nested_feedback,
        environment_feedback,
    ]
    question_id = str(work_order.get("question_id", "") or "").strip()
    selected: Mapping[str, Any] = {}
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or not candidate:
            continue
        candidate_question_id = str(
            candidate.get("question_id", "") or ""
        ).strip()
        if candidate_question_id and candidate_question_id != question_id:
            continue
        if not candidate.get("findings") and not candidate.get(
            "cumulative_finding_ledger"
        ):
            continue
        selected = candidate
        break
    if not selected:
        return {}

    active_ledger = [
        dict(row)
        for row in selected.get("cumulative_finding_ledger", []) or []
        if isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper()
        == "UNRESOLVED"
        and str(row.get("finding_id", "") or "").strip()
    ]
    if not active_ledger and selected.get("findings"):
        findings = normalize_generated_code_semantic_review_findings(
            question_id=question_id,
            source_subsystem=source_subsystem,
            findings=selected.get("findings", []),
        )
        active_ledger = [
            {
                "finding_id": str(row.get("finding_id", "") or ""),
                "status": "UNRESOLVED",
                "source_review_packet_ids": [
                    str(selected.get("review_packet_id", "") or "")
                ],
                "finding": row,
            }
            for row in findings
        ]
    if not active_ledger:
        return {}
    compact_active_ledger: list[dict[str, Any]] = []
    for raw_row in active_ledger:
        if not isinstance(raw_row, Mapping):
            continue
        finding_id = str(raw_row.get("finding_id", "") or "").strip()
        source_finding = raw_row.get("finding", {})
        if not isinstance(source_finding, Mapping):
            source_finding = {}
        source_finding = dict(source_finding)
        finding_id = str(
            finding_id or source_finding.get("finding_id", "") or ""
        ).strip()
        if not finding_id:
            continue
        compact_finding = {
            "finding_id": finding_id,
            "severity": str(source_finding.get("severity", "") or ""),
            "category": str(source_finding.get("category", "") or ""),
            "summary": str(source_finding.get("summary", "") or ""),
            "observed_behavior": str(
                source_finding.get("observed_behavior", "") or ""
            ),
            "expected_behavior": str(
                source_finding.get("expected_behavior", "") or ""
            ),
            "evidence_refs": [
                str(value).strip()
                for value in source_finding.get("evidence_refs", []) or []
                if str(value).strip()
            ],
        }
        compact_active_ledger.append(
            {
                "finding_id": finding_id,
                "status": "UNRESOLVED",
                "source_review_packet_ids": list(
                    dict.fromkeys(
                        str(value).strip()
                        for value in raw_row.get(
                            "source_review_packet_ids",
                            [],
                        )
                        or []
                        if str(value).strip()
                    )
                ),
                "source_finding_hash": str(
                    raw_row.get("source_finding_hash", "")
                    or stable_hash(source_finding)
                ),
                "finding": compact_finding,
            }
        )
    active_ledger = compact_active_ledger
    if not active_ledger:
        return {}
    required_ids = list(
        dict.fromkeys(
            str(row.get("finding_id", "") or "")
            for row in active_ledger
            if str(row.get("finding_id", "") or "").strip()
        )
    )
    obligations = {
        "artifact_kind": (
            "RuntimeGeneratedCodeSemanticReviewInheritedObservations"
        ),
        "question_id": question_id,
        "model_selected_subsystem": source_subsystem,
        "source_review_packet_id": str(
            selected.get("review_packet_id", "")
            or selected.get("semantic_review_packet_id", "")
            or ""
        ),
        "source_review_packet_hash": str(
            selected.get("review_packet_hash", "")
            or selected.get("semantic_review_packet_hash", "")
            or ""
        ),
        "source_review_execution_id": str(
            selected.get("review_execution_id", "")
            or selected.get("semantic_review_execution_id", "")
            or ""
        ),
        "parent_source_subsystem": str(
            selected.get("source_subsystem", "") or ""
        ),
        "required_prior_finding_ids": required_ids,
        "active_prior_finding_ledger": active_ledger,
        "review_rule": (
            "Review every active prior observation against the fresh current artifact "
            "and report whether the evidence closes it."
        ),
        "proof_evidence_status": (
            "INHERITED_GENERATED_CODE_OBSERVATIONS_NOT_PROOF_EVIDENCE"
        ),
    }
    obligations["obligation_set_fingerprint"] = stable_hash(obligations)
    return obligations


def _runtime_generated_code_semantic_review_material(
    *,
    work_order: Mapping[str, Any],
    source_task: Mapping[str, Any],
    source_manifest: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    proposal_packet: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    source_subsystem = str(work_order.get("source_subsystem", "") or "")
    source_rows = _runtime_generated_code_semantic_review_rows(
        source_manifest,
        source_subsystem=source_subsystem,
    )
    rows_by_hash = {stable_hash(row): row for row in source_rows}
    errors: list[str] = []
    exact_artifacts: list[dict[str, Any]] = []
    for descriptor in work_order.get("reviewed_artifacts", []) or []:
        if not isinstance(descriptor, Mapping):
            errors.append("reviewed_artifacts descriptor is not an object")
            continue
        row_hash = str(descriptor.get("row_hash", "") or "")
        row = rows_by_hash.get(row_hash)
        artifact_id = str(descriptor.get("artifact_id", "") or "")
        if row is None:
            errors.append(f"reviewed artifact row hash mismatch: {artifact_id}")
            continue
        if str(row.get("semantic_review_artifact_id", "") or "") != artifact_id:
            errors.append(f"reviewed artifact identity mismatch: {artifact_id}")
            continue
        script_path = Path(str(row.get("script_path", "") or ""))
        result_path = Path(str(row.get("result_path", "") or ""))
        if not script_path.is_file():
            errors.append(f"reviewed source file missing: {artifact_id}")
            continue
        source_code = script_path.read_text(encoding="utf-8")
        script_hash = stable_hash(source_code)
        if script_hash != str(row.get("script_hash", "") or ""):
            errors.append(f"reviewed source hash mismatch: {artifact_id}")
        result_payload: dict[str, Any] = {}
        if not result_path.is_file():
            errors.append(f"reviewed result file missing: {artifact_id}")
        else:
            try:
                raw_result = json.loads(result_path.read_text(encoding="utf-8"))
                if isinstance(raw_result, Mapping):
                    result_payload = dict(raw_result)
                else:
                    errors.append(f"reviewed result is not an object: {artifact_id}")
            except Exception as exc:
                errors.append(
                    f"reviewed result JSON invalid for {artifact_id}: {exc!r}"
                )
        result_hash = stable_hash(result_payload) if result_payload else ""
        if result_hash != str(row.get("result_hash", "") or ""):
            errors.append(f"reviewed result hash mismatch: {artifact_id}")
        if stable_hash(result_payload) != stable_hash(row.get("metrics", {})):
            errors.append(f"reviewed result does not match manifest metrics: {artifact_id}")
        exact_artifacts.append(
            {
                "artifact_id": artifact_id,
                "source_row": {
                    key: value
                    for key, value in row.items()
                    if key != "code_excerpt"
                },
                "exact_source_code": source_code,
                "exact_source_hash": script_hash,
                "exact_result": result_payload,
                "exact_result_hash": result_hash,
                "actual_runtime_arguments": {
                    "seed": row.get("runtime_seed"),
                    "replicates": row.get("runtime_replicates"),
                },
            }
        )
    architect_evidence_contract = dict(
        work_order.get("architect_evidence_contract", {}) or {}
    )
    source_responsibility_contract = dict(
        work_order.get("source_responsibility_contract", {}) or {}
    )
    assigned_requirements = [
        dict(row)
        for row in source_responsibility_contract.get(
            "assigned_empirical_metric_requirements",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    review_scope_projection = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "canonical_architect_evidence_contract_fingerprint": stable_hash(
            architect_evidence_contract
        ),
        "canonical_empirical_metric_requirement_set_id": str(
            architect_evidence_contract.get(
                "empirical_metric_requirement_set_id",
                "",
            )
            or generated_metric_requirement_set_id(
                [
                    dict(row)
                    for row in architect_evidence_contract.get(
                        "empirical_metric_requirements",
                        [],
                    )
                    or []
                    if isinstance(row, Mapping)
                ]
            )
        ),
        "assigned_requirement_ids": list(
            source_responsibility_contract.get("assigned_requirement_ids", [])
            or []
        ),
        "sibling_only_requirement_refs": [
            dict(row)
            for row in source_responsibility_contract.get(
                "sibling_only_requirement_refs",
                [],
            )
            or []
            if isinstance(row, Mapping)
        ],
        "projection_rule": (
            "The reviewer receives full rows only for requirements assigned to "
            "the current generated-code author. Sibling requirements remain as "
            "identity/owner references for handoff awareness and cannot fail this "
            "artifact's review. The canonical frozen contract remains immutable "
            "and is evaluated when its owning artifact executes."
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_REVIEW_SCOPE_PROJECTION_NOT_PROOF_EVIDENCE"
        ),
    }
    source_manifest_summary = {
        key: value
        for key, value in source_manifest.items()
        if key not in {"generated_simulation_sandbox_prototypes", "prototypes"}
    }
    source_inputs = (
        source_task.get("inputs", {})
        if isinstance(source_task, Mapping)
        else {}
    )
    source_context = (
        source_inputs.get("architect_context", {})
        if isinstance(source_inputs, Mapping)
        else {}
    )
    dependency_handoff = (
        source_inputs.get("upstream_algorithm_handoff", {})
        if isinstance(source_inputs, Mapping)
        else {}
    )
    if not isinstance(dependency_handoff, Mapping) or not dependency_handoff:
        dependency_handoff = (
            source_context.get("upstream_algorithm_handoff", {})
            if isinstance(source_context, Mapping)
            else {}
        )
    if not isinstance(dependency_handoff, Mapping):
        dependency_handoff = {}
    upstream_generated_dependency = (
        generated_code_semantic_review_upstream_dependency_projection(
            source_subsystem=source_subsystem,
            upstream_algorithm_handoff=dependency_handoff,
        )
    )
    if upstream_generated_dependency and any(
        not str(upstream_generated_dependency.get(field, "") or "")
        for field in (
            "algorithm_sandbox_manifest_id",
            "algorithm_sandbox_manifest_hash",
            "accepted_semantic_review_execution_id",
            "accepted_semantic_review_packet_id",
        )
    ):
        errors.append("upstream generated dependency lineage is incomplete")
    for dependency in upstream_generated_dependency.get(
        "exact_dependency_artifacts",
        [],
    ):
        if not isinstance(dependency, Mapping):
            errors.append("upstream generated dependency is not an object")
            continue
        dependency_id = str(dependency.get("artifact_id", "") or "")
        dependency_source = str(
            dependency.get("exact_source_code", "") or ""
        )
        dependency_result = dependency.get("exact_result", {})
        if not dependency_id or not dependency_source:
            errors.append("upstream generated dependency is incomplete")
            continue
        if str(dependency.get("exact_source_hash", "") or "") != stable_hash(
            dependency_source
        ):
            errors.append(
                f"upstream generated dependency source hash mismatch: {dependency_id}"
            )
        if not isinstance(dependency_result, Mapping) or str(
            dependency.get("exact_result_hash", "") or ""
        ) != stable_hash(dependency_result):
            errors.append(
                f"upstream generated dependency result hash mismatch: {dependency_id}"
            )
    material = {
        "source_subsystem": source_subsystem,
        "empirical_evaluation_phase": str(
            work_order.get("empirical_evaluation_phase", "") or ""
        ),
        "confirmatory_empirical_evidence_eligible": bool(
            work_order.get("confirmatory_empirical_evidence_eligible", True)
        ),
        "source_manifest_id": str(
            work_order.get("source_manifest_id", "") or ""
        ),
        "source_manifest_summary": (
            generated_code_semantic_review_scope_projection(
                value=source_manifest_summary,
                assigned_requirements=assigned_requirements,
            )
        ),
        "theory_packet": (
            generated_code_semantic_review_theory_projection(
                theory_packet=theory_packet,
                proposal_packet=proposal_packet,
            )
        ),
        "coding_agent_proposal_packet": (
            generated_code_semantic_review_proposal_projection(
                source_subsystem=source_subsystem,
                proposal_packet=proposal_packet,
                assigned_requirements=assigned_requirements,
            )
        ),
        "architect_frozen_evidence_contract": (
            generated_code_semantic_review_scope_projection(
                value=architect_evidence_contract,
                assigned_requirements=assigned_requirements,
            )
        ),
        "source_responsibility_contract": source_responsibility_contract,
        "review_scope_projection": review_scope_projection,
        "prior_semantic_observations": (
            _runtime_generated_code_semantic_review_prior_observations(
                work_order=work_order,
                source_task=source_task,
                source_subsystem=source_subsystem,
            )
        ),
        "upstream_generated_dependency": upstream_generated_dependency,
        "exact_executed_artifacts": exact_artifacts,
        "evidence_boundary": GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
    }
    return material, sorted(set(errors))


def _runtime_merged_accepted_generated_code_reviews(
    *,
    deferred_task_inputs: Mapping[str, Any],
    accepted_review: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Merge current accepted reviews by immutable source-parent lineage."""

    context = deferred_task_inputs.get("architect_context", {})
    context = dict(context) if isinstance(context, Mapping) else {}
    candidates: list[Mapping[str, Any]] = []
    for container in (deferred_task_inputs, context):
        candidates.extend(
            row
            for row in container.get(
                "accepted_generated_code_semantic_reviews", []
            )
            or []
            if isinstance(row, Mapping)
        )
    candidates.append(accepted_review)

    rows_by_lineage: dict[tuple[str, str], dict[str, Any]] = {}
    lineage_order: list[tuple[str, str]] = []
    for row in candidates:
        source_subsystem = str(row.get("source_subsystem", "") or "").strip()
        parents = row.get("parent_artifact_ids", {})
        parent_ids = dict(parents) if isinstance(parents, Mapping) else {}
        identity = source_subsystem or str(
            row.get("execution_id", "")
            or row.get("review_packet_id", "")
            or row.get("source_manifest_id", "")
            or stable_hash(row)
        )
        lineage = (identity, stable_hash(parent_ids))
        if lineage not in rows_by_lineage:
            lineage_order.append(lineage)
        rows_by_lineage[lineage] = deepcopy(dict(row))
    return [rows_by_lineage[lineage] for lineage in lineage_order]


class GeneratedCodeSemanticReviewerRuntimeSubsystem:
    name = GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM

    def __init__(
        self,
        *,
        reviewer: LLMGeneratedCodeSemanticReviewerAgent,
        max_revisions: int = 1,
    ) -> None:
        self.reviewer = reviewer
        self.max_revisions = max(0, int(max_revisions or 0))

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        work_order_id = str(task.inputs.get("work_order_id", "") or "")
        work_order_hash = str(task.inputs.get("work_order_hash", "") or "")
        raw_work_order = blackboard.artifacts.get(work_order_id, {})
        work_order = (
            dict(raw_work_order) if isinstance(raw_work_order, Mapping) else {}
        )
        validation_errors: list[str] = []
        if not work_order_id or not work_order:
            validation_errors.append("semantic review work order missing")
        if str(work_order.get("artifact_kind", "") or "") != (
            "RuntimeGeneratedCodeSemanticReviewWorkOrder"
        ):
            validation_errors.append("semantic review work-order kind mismatch")
        if str(work_order.get("work_order_id", "") or "") != work_order_id:
            validation_errors.append("semantic review work-order identity mismatch")
        if not work_order_hash or stable_hash(work_order) != work_order_hash:
            validation_errors.append("semantic review immutable work-order hash mismatch")
        if str(work_order.get("question_id", "") or "") != question.id:
            validation_errors.append("semantic review question identity mismatch")
        source_subsystem = str(work_order.get("source_subsystem", "") or "")
        if source_subsystem not in GENERATED_CODE_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS:
            validation_errors.append("semantic review source subsystem is invalid")
        if work_order.get("research_evaluation") is True and not all(
            str(work_order.get(field, "") or "").strip()
            for field in ("source_agent", "source_model", "source_model_tier")
        ):
            validation_errors.append(
                "research-evaluation semantic review requires complete source-agent provenance"
            )
        expected_responsibility_contract = (
            _runtime_generated_code_semantic_review_source_responsibility_contract(
                source_subsystem=source_subsystem,
                architect_evidence_contract=(
                    work_order.get("architect_evidence_contract", {})
                    if isinstance(
                        work_order.get("architect_evidence_contract", {}),
                        Mapping,
                    )
                    else {}
                ),
            )
        )
        if stable_hash(
            work_order.get("source_responsibility_contract", {})
        ) != stable_hash(expected_responsibility_contract):
            validation_errors.append(
                "semantic review source-responsibility contract mismatch"
            )
        if str(
            work_order.get(
                "source_responsibility_contract_fingerprint",
                "",
            )
            or ""
        ) != stable_hash(expected_responsibility_contract):
            validation_errors.append(
                "semantic review source-responsibility fingerprint mismatch"
            )

        def bound_artifact(
            *,
            id_field: str,
            hash_field: str,
            required: bool = True,
        ) -> dict[str, Any]:
            artifact_id = str(work_order.get(id_field, "") or "")
            expected_hash = str(work_order.get(hash_field, "") or "")
            if not artifact_id:
                if required:
                    validation_errors.append(f"{id_field} missing")
                return {}
            raw_artifact = blackboard.artifacts.get(artifact_id, {})
            if not isinstance(raw_artifact, Mapping):
                validation_errors.append(f"{id_field} missing from blackboard")
                return {}
            artifact = dict(raw_artifact)
            if not expected_hash or stable_hash(artifact) != expected_hash:
                validation_errors.append(f"{id_field} immutable hash mismatch")
            return artifact

        source_manifest = bound_artifact(
            id_field="source_manifest_id",
            hash_field="source_manifest_hash",
        )
        theory_packet = bound_artifact(
            id_field="theory_packet_id",
            hash_field="theory_packet_hash",
        )
        proposal_packet = bound_artifact(
            id_field="proposal_packet_id",
            hash_field="proposal_packet_hash",
        )
        expected_manifest_kind = (
            "RuntimeSimulationManifest"
            if source_subsystem == "SimulationEvaluator"
            else "RuntimeAlgorithmSandboxManifest"
        )
        if str(source_manifest.get("artifact_kind", "") or "") != (
            expected_manifest_kind
        ):
            validation_errors.append("semantic review source manifest kind mismatch")
        source_task_continuation = bound_artifact(
            id_field="source_task_continuation_id",
            hash_field="source_task_continuation_hash",
        )
        deferred_task_continuation = bound_artifact(
            id_field="deferred_next_task_continuation_id",
            hash_field="deferred_next_task_continuation_hash",
        )
        for label, continuation, id_field, expected_ref in (
            (
                "source",
                source_task_continuation,
                "source_task_continuation_id",
                work_order.get("source_task_ref"),
            ),
            (
                "deferred",
                deferred_task_continuation,
                "deferred_next_task_continuation_id",
                work_order.get("deferred_next_task_ref"),
            ),
        ):
            if str(continuation.get("artifact_kind", "") or "") != (
                "RuntimeAgentTaskContinuation"
            ):
                validation_errors.append(
                    f"semantic review {label} task continuation kind mismatch"
                )
            if str(continuation.get("continuation_id", "") or "") != str(
                work_order.get(id_field, "") or ""
            ):
                validation_errors.append(
                    f"semantic review {label} task continuation identity mismatch"
                )
            if continuation.get("task_ref") != expected_ref:
                validation_errors.append(
                    f"semantic review {label} task continuation ref mismatch"
                )
        source_task: AgentTask | None = None
        deferred_task: AgentTask | None = None
        try:
            persisted_source_task = restore_agent_task_continuation(
                source_task_continuation,
                blackboard.artifacts,
            )
            persisted_deferred_task = restore_agent_task_continuation(
                deferred_task_continuation,
                blackboard.artifacts,
            )
        except ValueError as exc:
            validation_errors.append(str(exc))
        else:
            if persisted_source_task.owner_subsystem != source_subsystem:
                validation_errors.append(
                    "semantic review source task owner mismatch"
                )
            if persisted_source_task.task_id != str(
                work_order.get("source_task_id", "") or ""
            ):
                validation_errors.append(
                    "semantic review source task identity mismatch"
                )
            if agent_task_reference(persisted_source_task) != work_order.get(
                "source_task_ref"
            ):
                validation_errors.append("semantic review source task ref mismatch")
            if agent_task_reference(persisted_deferred_task) != work_order.get(
                "deferred_next_task_ref"
            ):
                validation_errors.append("semantic review deferred task ref mismatch")
            try:
                source_task = replace(
                    persisted_source_task,
                    inputs=resolve_runtime_artifact_references(
                        persisted_source_task.inputs,
                        blackboard.artifacts,
                    ),
                )
                deferred_task = replace(
                    persisted_deferred_task,
                    inputs=resolve_runtime_artifact_references(
                        persisted_deferred_task.inputs,
                        blackboard.artifacts,
                    ),
                )
            except ValueError as exc:
                validation_errors.append(str(exc))
        source_task_payload = asdict(source_task) if source_task is not None else {}
        deferred_task_payload = (
            asdict(deferred_task) if deferred_task is not None else {}
        )

        review_material: dict[str, Any] = {}
        if not validation_errors:
            review_material, material_errors = (
                _runtime_generated_code_semantic_review_material(
                    work_order=work_order,
                    source_task=source_task_payload,
                    source_manifest=source_manifest,
                    theory_packet=theory_packet,
                    proposal_packet=proposal_packet,
                )
            )
            validation_errors.extend(material_errors)
        if validation_errors:
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "GeneratedCodeSemanticReviewer rejected changed, missing, or "
                    "cross-task review inputs before calling the reviewer model."
                ),
                observations=(
                    EnvironmentObservation(
                        observation_type="generated_code_semantic_review_input_rejected",
                        summary="; ".join(validation_errors)[:500],
                        payload={
                            "work_order_id": work_order_id,
                            "validation_errors": validation_errors,
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                failure_classification="generated_code_semantic_review_input_invalid",
            )

        def materialize_review(
            material: Mapping[str, Any],
        ) -> tuple[str, dict[str, Any]]:
            exact_algorithm_artifacts = (
                _runtime_exact_algorithm_artifacts(material)
                if source_subsystem == "AlgorithmEngineer"
                else []
            )
            materialization_id = (
                "generated_code_semantic_review_materialization:"
                + stable_hash([work_order_id, material])[:20]
            )
            return materialization_id, {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": (
                    "RuntimeGeneratedCodeSemanticReviewMaterialization"
                ),
                "materialization_id": materialization_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question_id": question.id,
                "work_order_id": work_order_id,
                "work_order_hash": work_order_hash,
                "review_input_fingerprint": stable_hash(material),
                "source_responsibility_contract_fingerprint": str(
                    work_order.get(
                        "source_responsibility_contract_fingerprint",
                        "",
                    )
                    or ""
                ),
                "review_input_artifact_refs": {
                    key: str(work_order.get(key, "") or "")
                    for key in (
                        "source_manifest_id",
                        "theory_packet_id",
                        "proposal_packet_id",
                    )
                },
                "exact_algorithm_artifacts": exact_algorithm_artifacts,
                "full_review_material_persisted": False,
                "proof_evidence_status": (
                    "GENERATED_CODE_SEMANTIC_REVIEW_INPUT_NOT_PROOF_EVIDENCE"
                ),
                "evidence_boundary": GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
            }

        materialization_id, materialization = materialize_review(
            review_material
        )
        review_audit_artifacts: dict[str, Any] = {}
        trusted_lineage = {
            key: work_order.get(key, "")
            for key in (
                "work_order_id",
                "source_task_id",
                "source_subsystem",
                "source_manifest_id",
                "source_manifest_hash",
                "theory_packet_id",
                "theory_packet_hash",
                "proposal_packet_id",
                "proposal_packet_hash",
                "source_agent",
                "source_model",
                "source_model_tier",
            )
        }
        trusted_lineage["work_order_hash"] = work_order_hash
        trusted_lineage["reviewed_artifacts"] = list(
            work_order.get("reviewed_artifacts", []) or []
        )
        research_evaluation = bool(work_order.get("research_evaluation", False))
        source_agent = str(work_order.get("source_agent", "") or "")
        source_model = str(work_order.get("source_model", "") or "")
        source_tier = str(work_order.get("source_model_tier", "") or "")

        def runtime_review_packet_errors(
            packet: Mapping[str, Any],
            material: Mapping[str, Any],
        ) -> list[str]:
            errors = validate_generated_code_semantic_review_packet(
                packet,
                review_material=material,
            )
            if str(
                packet.get("review_input_fingerprint", "") or ""
            ) != stable_hash(material):
                errors.append("semantic review input fingerprint mismatch")
            packet_agent = str(packet.get("source_agent", "") or "")
            packet_model = str(packet.get("model", "") or "")
            packet_tier = str(packet.get("model_tier", "") or "")
            if research_evaluation and not all(
                (source_agent, source_model, source_tier)
            ):
                errors.append(
                    "research-evaluation semantic review requires complete "
                    "source-agent provenance"
                )
            if research_evaluation and source_agent and packet_agent == source_agent:
                errors.append(
                    "research-evaluation reviewer agent must differ from source "
                    "generator agent"
                )
            if (
                research_evaluation
                and packet_tier != LIVE_EVALUATION_CLAUDE_MODEL_TIER
            ):
                errors.append(
                    "research-evaluation semantic reviewer must use the "
                    "configured evaluation tier "
                    f"{LIVE_EVALUATION_CLAUDE_MODEL_TIER}"
                )
            if (
                research_evaluation
                and packet_model != LIVE_EVALUATION_CLAUDE_MODEL
            ):
                errors.append(
                    "research-evaluation semantic reviewer must use the exact "
                    f"evaluation model {LIVE_EVALUATION_CLAUDE_MODEL}"
                )
            return errors

        try:
            with agent_runtime_substage(
                "generated_code_semantic_review",
                metadata={
                    "source_subsystem": source_subsystem,
                    "review_input_fingerprint": stable_hash(review_material),
                },
            ):
                review_packet = self.reviewer.review(
                    question=question,
                    review_material=review_material,
                    trusted_lineage=trusted_lineage,
                )
        except PacketValidationError as exc:
            last_invalid_packet = (
                deepcopy(dict(exc.last_invalid_packet))
                if isinstance(exc.last_invalid_packet, Mapping)
                else {}
            )
            invalid_review_projection = {
                key: deepcopy(last_invalid_packet.get(key))
                for key in (
                    "packet_id",
                    "review_input_fingerprint",
                    "model_requested_overall_verdict",
                    "overall_verdict",
                    "prior_finding_reviews",
                    "dimension_reviews",
                    "findings",
                    "proof_evidence_status",
                )
                if key in last_invalid_packet
            }
            validation_errors = [str(error) for error in exc.errors]
            failure_id = (
                "generated_code_semantic_review_validation_failure:"
                + stable_hash(
                    [
                        work_order_id,
                        work_order_hash,
                        exc.validation_label,
                        validation_errors,
                        exc.history,
                        invalid_review_projection,
                    ]
                )[:20]
            )
            failure_artifact = {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": (
                    "RuntimeGeneratedCodeSemanticReviewValidationFailure"
                ),
                "failure_id": failure_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question_id": question.id,
                "task_id": task.task_id,
                "work_order_id": work_order_id,
                "work_order_hash": work_order_hash,
                "materialization_id": materialization_id,
                "materialization_hash": stable_hash(materialization),
                "review_input_fingerprint": stable_hash(review_material),
                "validation_label": exc.validation_label,
                "validation_errors": validation_errors,
                "validation_attempts": exc.attempts,
                "structured_output_retry_history": [
                    deepcopy(dict(row)) for row in exc.history
                ],
                "last_invalid_packet_available": bool(last_invalid_packet),
                "last_invalid_packet_fingerprint": (
                    stable_hash(last_invalid_packet)
                    if last_invalid_packet
                    else ""
                ),
                "last_invalid_review_projection": invalid_review_projection,
                "semantic_review_acceptance_authorized": False,
                "confirmatory_empirical_evidence_eligible": bool(
                    review_material.get(
                        "confirmatory_empirical_evidence_eligible",
                        False,
                    )
                ),
                "kernel_verified": False,
                "execution_evidence_status": (
                    "GENERATED_CODE_SEMANTIC_REVIEW_VALIDATION_FAILURE_NOT_EXECUTION_EVIDENCE"
                ),
                "proof_evidence_status": (
                    "GENERATED_CODE_SEMANTIC_REVIEW_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
                ),
                "evidence_boundary": GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
            }
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "The independent semantic reviewer exhausted typed packet "
                    "repair without a contract-valid verdict."
                ),
                produced_artifacts={
                    materialization_id: materialization,
                    failure_id: failure_artifact,
                },
                observations=(
                    EnvironmentObservation(
                        observation_type="generated_code_semantic_review_packet_invalid",
                        summary=str(exc)[:500],
                        payload={
                            "work_order_id": work_order_id,
                            "failure_id": failure_id,
                            "validation_errors": validation_errors,
                            "validation_attempts": exc.attempts,
                            "semantic_review_acceptance_authorized": False,
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                failure_classification="generated_code_semantic_review_packet_invalid",
            )

        runtime_review_errors = runtime_review_packet_errors(
            review_packet,
            review_material,
        )
        if runtime_review_errors:
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "GeneratedCodeSemanticReviewer rejected an independence, "
                    "evaluation-model, or lineage-inconsistent semantic verdict."
                ),
                produced_artifacts={materialization_id: materialization},
                observations=(
                    EnvironmentObservation(
                        observation_type="generated_code_semantic_review_verdict_rejected",
                        summary="; ".join(sorted(set(runtime_review_errors)))[:500],
                        payload={
                            "work_order_id": work_order_id,
                            "validation_errors": sorted(set(runtime_review_errors)),
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                failure_classification="generated_code_semantic_review_verdict_invalid",
            )

        review_packet_id = str(review_packet.get("packet_id", "") or "")
        review_packet_hash = stable_hash(review_packet)
        reviewer_verdict = str(
            review_packet.get("overall_verdict", "") or ""
        )
        initial_materialization_id = materialization_id
        initial_review_packet_id = review_packet_id
        routed_findings = [
            dict(row)
            for row in review_packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ]
        source_revision_assessment = dict(
            review_packet.get("source_revision_assessment", {}) or {}
        )
        cross_artifact_revision_required = bool(
            reviewer_verdict == "REVISE"
            and source_revision_assessment.get(
                "current_source_edit_sufficient"
            )
            is False
        )
        reviewer_model = str(review_packet.get("model", "") or "")
        reviewer_tier = str(review_packet.get("model_tier", "") or "")
        reviewer_agent = str(review_packet.get("source_agent", "") or "")
        verdict = reviewer_verdict
        empirical_evaluation_phase = str(
            work_order.get("empirical_evaluation_phase", "") or ""
        )
        confirmatory_empirical_evidence_eligible = bool(
            work_order.get("confirmatory_empirical_evidence_eligible", True)
        )
        current_reviewed_source_artifacts = [
            {
                "artifact_id": str(row.get("artifact_id", "") or ""),
                "exact_source_hash": str(
                    row.get("exact_source_hash", "") or ""
                ),
                "exact_source_code": str(
                    row.get("exact_source_code", "") or ""
                ),
                "exact_source_code_complete": True,
                "exact_result": dict(row.get("exact_result", {}) or {}),
                "exact_result_hash": str(
                    row.get("exact_result_hash", "") or ""
                ),
                "actual_runtime_arguments": dict(
                    row.get("actual_runtime_arguments", {}) or {}
                ),
                "artifact_role": "reviewed_source",
            }
            for row in review_material.get("exact_executed_artifacts", []) or []
            if isinstance(row, Mapping)
        ]
        upstream_dependency_material = review_material.get(
            "upstream_generated_dependency",
            {},
        )
        upstream_dependency_material = (
            dict(upstream_dependency_material)
            if isinstance(upstream_dependency_material, Mapping)
            else {}
        )
        upstream_dependency_artifacts = [
            {
                "artifact_id": str(row.get("artifact_id", "") or ""),
                "exact_source_hash": str(
                    row.get("exact_source_hash", "") or ""
                ),
                "exact_source_code": str(
                    row.get("exact_source_code", "") or ""
                ),
                "exact_source_code_complete": True,
                "exact_result": dict(row.get("exact_result", {}) or {}),
                "exact_result_hash": str(
                    row.get("exact_result_hash", "") or ""
                ),
                "actual_runtime_arguments": {},
                "artifact_role": "upstream_generated_dependency",
            }
            for row in upstream_dependency_material.get(
                "exact_dependency_artifacts",
                [],
            )
            or []
            if isinstance(row, Mapping)
        ]
        reviewed_source_artifacts = [
            *current_reviewed_source_artifacts,
            *upstream_dependency_artifacts,
        ]
        source_lineage = {
            "source_manifest_id": str(
                work_order.get("source_manifest_id", "") or ""
            ),
            "source_manifest_hash": str(
                work_order.get("source_manifest_hash", "") or ""
            ),
            "theory_packet_id": str(
                work_order.get("theory_packet_id", "") or ""
            ),
            "theory_packet_hash": str(
                work_order.get("theory_packet_hash", "") or ""
            ),
            "proposal_packet_id": str(
                work_order.get("proposal_packet_id", "") or ""
            ),
            "proposal_packet_hash": str(
                work_order.get("proposal_packet_hash", "") or ""
            ),
            "architect_evidence_contract_fingerprint": str(
                review_material.get("review_scope_projection", {}).get(
                    "canonical_architect_evidence_contract_fingerprint",
                    "",
                )
                if isinstance(
                    review_material.get("review_scope_projection", {}),
                    Mapping,
                )
                else ""
            ),
            "embedded_source_is_untrusted_data": True,
            "proof_evidence_status": (
                "GENERATED_CODE_SOURCE_LINEAGE_NOT_PROOF_EVIDENCE"
            ),
        }
        execution_id = "generated_code_semantic_review_execution:" + stable_hash(
            [work_order_id, work_order_hash, review_packet_id, review_packet_hash]
        )[:20]
        execution_manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeGeneratedCodeSemanticReviewExecutionManifest",
            "execution_id": execution_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question_id": question.id,
            "task_id": task.task_id,
            "work_order_id": work_order_id,
            "work_order_hash": work_order_hash,
            "source_subsystem": source_subsystem,
            "source_manifest_id": str(
                work_order.get("source_manifest_id", "") or ""
            ),
            "source_manifest_hash": str(
                work_order.get("source_manifest_hash", "") or ""
            ),
            "materialization_id": materialization_id,
            "materialization_hash": stable_hash(materialization),
            "initial_materialization_id": initial_materialization_id,
            "review_packet_id": review_packet_id,
            "review_packet_hash": review_packet_hash,
            "initial_review_packet_id": initial_review_packet_id,
            "review_input_fingerprint": stable_hash(review_material),
            "source_responsibility_contract_fingerprint": str(
                work_order.get(
                    "source_responsibility_contract_fingerprint",
                    "",
                )
                or ""
            ),
            "source_agent": source_agent,
            "source_model": source_model,
            "source_model_tier": source_tier,
            "reviewer_agent": reviewer_agent,
            "reviewer_model": reviewer_model,
            "reviewer_model_tier": reviewer_tier,
            "independent_agent": bool(
                source_agent
                and reviewer_agent
                and reviewer_agent != source_agent
            ),
            "independent_invocation": True,
            "independent_model": bool(
                source_model
                and reviewer_model
                and reviewer_model != source_model
            ),
            "reviewer_overall_verdict": reviewer_verdict,
            "overall_verdict": verdict,
            "workflow_verdict": verdict,
            "reviewed_source_artifact_lineage": [
                {
                    "artifact_id": row["artifact_id"],
                    "exact_source_hash": row["exact_source_hash"],
                    "exact_result_hash": row["exact_result_hash"],
                    "exact_source_code_complete": row[
                        "exact_source_code_complete"
                    ],
                }
                for row in reviewed_source_artifacts
            ],
            "source_lineage_fingerprint": stable_hash(source_lineage),
            "routing_authority_on_revise": (
                "architect_model_after_source_sufficiency_observation"
                if cross_artifact_revision_required
                else "immutable_source_producer_lineage"
            ),
            "runtime_selected_owner": False,
            "reviewer_packet_accepted": reviewer_verdict == "ACCEPT",
            "semantic_review_accepted": verdict == "ACCEPT",
            "empirical_evaluation_phase": empirical_evaluation_phase,
            "confirmatory_empirical_evidence_eligible": (
                confirmatory_empirical_evidence_eligible
            ),
            "review_revision_count": int(
                work_order.get("review_revision_count", 0) or 0
            ),
            "proof_evidence_status": (
                GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE
            ),
            "evidence_boundary": GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
        }
        produced_artifacts = {
            **review_audit_artifacts,
            materialization_id: materialization,
            review_packet_id: review_packet,
            execution_id: execution_manifest,
        }
        feedback_identity = {
            "question_id": question.id,
            "source_subsystem": source_subsystem,
            "source_manifest_id": str(
                work_order.get("source_manifest_id", "") or ""
            ),
            "source_theory_packet_id": str(
                work_order.get("theory_packet_id", "") or ""
            ),
            "source_theory_packet_hash": str(
                work_order.get("theory_packet_hash", "") or ""
            ),
            "semantic_review_execution_id": execution_id,
            "semantic_review_packet_id": review_packet_id,
            "semantic_review_packet_hash": review_packet_hash,
        }
        feedback = {
            "feedback_id": (
                "generated_code_semantic_review_feedback:"
                + stable_hash(feedback_identity)[:20]
            ),
            "feedback_type": "generated_code_semantic_review_feedback",
            "feedback_source": GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM,
            **feedback_identity,
            "reviewer_overall_verdict": reviewer_verdict,
            "overall_verdict": verdict,
            "workflow_verdict": verdict,
            "routing_authority": (
                "architect_model_after_source_sufficiency_observation"
                if cross_artifact_revision_required
                else "immutable_source_producer_lineage"
            ),
            "runtime_selected_owner": False,
            "empirical_evaluation_phase": empirical_evaluation_phase,
            "confirmatory_empirical_evidence_eligible": (
                confirmatory_empirical_evidence_eligible
            ),
            "dimension_reviews": list(
                review_packet.get("dimension_reviews", []) or []
            ),
            "prior_finding_reviews": list(
                review_packet.get("prior_finding_reviews", []) or []
            ),
            "cumulative_finding_ledger": list(
                review_packet.get("cumulative_finding_ledger", []) or []
            ),
            "cumulative_finding_ledger_fingerprint": str(
                review_packet.get(
                    "cumulative_finding_ledger_fingerprint",
                    "",
                )
                or ""
            ),
            "active_unresolved_finding_ids": list(
                review_packet.get("active_unresolved_finding_ids", []) or []
            ),
            "findings": routed_findings,
            "source_revision_assessment": source_revision_assessment,
            "reviewed_source_artifacts": reviewed_source_artifacts,
            "source_lineage": source_lineage,
            "model_route_required_for_cross_owner_revision": True,
            "execution_results_observed": True,
            "execution_authorized": False,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            "evidence_boundary": GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
        }
        revision_count = int(work_order.get("review_revision_count", 0) or 0)
        max_revisions = max(
            self.max_revisions,
            int(work_order.get("max_revisions", 0) or 0),
        )
        lineage_budget_state: dict[str, Any] = {}
        if verdict == "REVISE":
            source_task_inputs_for_budget = (
                source_task_payload.get("inputs", {})
                if isinstance(source_task_payload.get("inputs", {}), Mapping)
                else {}
            )
            task_context = source_task_inputs_for_budget.get(
                "architect_context",
                {},
            )
            routing_bound_review_packet = {
                **dict(review_packet),
                "findings": routed_findings,
            }
            lineage_budget_state = (
                advance_generated_code_semantic_review_lineage_budget(
                    architect_context=(
                        task_context if isinstance(task_context, Mapping) else {}
                    ),
                    work_order=work_order,
                    review_packet=routing_bound_review_packet,
                    max_local_revisions=max_revisions,
                    prior_local_revisions=revision_count,
                )
            )
            lineage_budget_summary = {
                **dict(lineage_budget_state.get("row", {})),
                "candidate_regeneration_available": bool(
                    lineage_budget_state.get(
                        "candidate_regeneration_available"
                    )
                ),
                "lineage_budget_exhausted": bool(
                    lineage_budget_state.get("lineage_budget_exhausted")
                ),
            }
            execution_manifest["semantic_review_lineage_budget"] = (
                lineage_budget_summary
            )
            feedback["semantic_review_lineage_budget"] = lineage_budget_summary
        if verdict == "ACCEPT":
            assert deferred_task is not None
            assert source_task is not None
            next_inputs = dict(deferred_task.inputs)
            next_context = dict(next_inputs.get("architect_context", {}) or {})
            algorithm_handoff: dict[str, Any] = {}
            if source_subsystem == "AlgorithmEngineer":
                algorithm_handoff = _runtime_accepted_algorithm_handoff_from_review(
                    question_id=question.id,
                    theory_packet_id=str(
                        work_order.get("theory_packet_id", "") or ""
                    ),
                    source_manifest=source_manifest,
                    review_material=review_material,
                    execution_manifest=execution_manifest,
                    review_packet=review_packet,
                )
                if not algorithm_handoff:
                    return AgentStepResult(
                        status="BLOCKED",
                        rationale=(
                            "The accepted AlgorithmEngineer review could not produce "
                            "a hash-bound exact-source handoff for SimulationEngineer."
                        ),
                        produced_artifacts=produced_artifacts,
                        failure_classification=(
                            "accepted_algorithm_handoff_materialization_failed"
                        ),
                    )
            accepted_review = {
                "execution_id": execution_id,
                "review_packet_id": review_packet_id,
                "review_packet_hash": review_packet_hash,
                "source_subsystem": source_subsystem,
                "source_manifest_id": str(
                    work_order.get("source_manifest_id", "") or ""
                ),
                "source_manifest_hash": str(
                    work_order.get("source_manifest_hash", "") or ""
                ),
                "parent_artifact_ids": _runtime_task_parent_artifact_ids(
                    source_subsystem,
                    source_task.inputs,
                ),
                "overall_verdict": "ACCEPT",
                "empirical_evaluation_phase": empirical_evaluation_phase,
                "confirmatory_empirical_evidence_eligible": (
                    confirmatory_empirical_evidence_eligible
                ),
                "source_responsibility_contract_fingerprint": str(
                    work_order.get(
                        "source_responsibility_contract_fingerprint",
                        "",
                    )
                    or ""
                ),
            }
            accepted_reviews = _runtime_merged_accepted_generated_code_reviews(
                deferred_task_inputs=next_inputs,
                accepted_review=accepted_review,
            )
            next_inputs["accepted_generated_code_semantic_reviews"] = accepted_reviews
            next_context["accepted_generated_code_semantic_reviews"] = (
                accepted_reviews
            )
            next_context = (
                _runtime_retire_resolved_generated_code_semantic_review_replan(
                    architect_context=next_context,
                    accepted_review=accepted_review,
                )
            )
            if algorithm_handoff:
                next_inputs["upstream_algorithm_handoff"] = algorithm_handoff
                next_context["upstream_algorithm_handoff"] = algorithm_handoff
                next_inputs["algorithm_sandbox_manifest_id"] = str(
                    algorithm_handoff["algorithm_sandbox_manifest_id"]
                )
                next_context["algorithm_sandbox_manifest_id"] = str(
                    algorithm_handoff["algorithm_sandbox_manifest_id"]
                )
                accepted_task_operation = str(
                    deferred_task.inputs.get("runtime_architect_operation", "")
                    or ""
                )
                if (
                    deferred_task.owner_subsystem == "ArchitectCoordinator"
                    and accepted_task_operation
                    == RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC
                ):
                    implementation_interface_handoff = (
                        build_accepted_implementation_interface_handoff(
                            algorithm_handoff
                        )
                    )
                    implementation_interface_errors = (
                        accepted_implementation_interface_handoff_errors(
                            implementation_interface_handoff,
                            question_id=question.id,
                            theory_packet_id=str(
                                work_order.get("theory_packet_id", "") or ""
                            ),
                        )
                    )
                    if implementation_interface_errors:
                        return AgentStepResult(
                            status="BLOCKED",
                            rationale=(
                                "The accepted implementation could not be projected "
                                "into a result-blind metric-authoring interface."
                            ),
                            produced_artifacts=produced_artifacts,
                            observations=(
                                EnvironmentObservation(
                                    observation_type=(
                                        "accepted_implementation_interface_rejected"
                                    ),
                                    summary="; ".join(
                                        implementation_interface_errors
                                    )[:500],
                                    payload={
                                        "validation_errors": (
                                            implementation_interface_errors
                                        ),
                                        "deferred_metric_authoring_released": False,
                                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                                    },
                                ),
                            ),
                            failure_classification=(
                                "accepted_implementation_interface_invalid"
                            ),
                        )
                    interface_handoff_id = str(
                        implementation_interface_handoff["handoff_id"]
                    )
                    produced_artifacts[interface_handoff_id] = (
                        implementation_interface_handoff
                    )
                    next_inputs[
                        "accepted_implementation_interface_handoff"
                    ] = implementation_interface_handoff
                    next_context[
                        "accepted_implementation_interface_handoff"
                    ] = implementation_interface_handoff
            next_inputs["architect_context"] = next_context
            next_task = replace(
                deferred_task,
                task_id=(
                    f"semantic-review-accepted:{question.id}:"
                    f"{stable_hash([execution_id, deferred_task.task_id])[:8]}"
                ),
                inputs=next_inputs,
            )
            status = "REROUTE"
            rationale = (
                "Independent semantic review accepted the exact executed generated "
                "artifacts and the runtime is resuming the deferred task."
            )
            failure_classification = ""
        else:
            source_task_inputs = (
                source_task_payload.get("inputs", {})
                if isinstance(source_task_payload.get("inputs", {}), Mapping)
                else {}
            )
            source_task_feedback = source_task_inputs.get(
                "environment_feedback", {}
            )
            source_execution_feedback = work_order.get(
                "source_execution_feedback",
                {},
            )
            prior_feedback = (
                dict(source_task_feedback)
                if isinstance(source_task_feedback, Mapping)
                else {}
            )
            if (
                isinstance(source_execution_feedback, Mapping)
                and source_execution_feedback
            ):
                prior_feedback["source_execution_feedback"] = dict(
                    source_execution_feedback
                )
            revision_classification = (
                "generated_code_semantic_review_requires_source_regeneration"
            )
            revision_feedback = {
                **_generated_code_review_feedback_with_source_execution_snapshot(
                    prior_feedback=prior_feedback,
                    review_feedback=feedback,
                ),
                "failure_classification": revision_classification,
                "semantic_review_revision_budget": {
                    "revisions_used": revision_count,
                    "max_revisions": max_revisions,
                    "source_artifact_remains_unaccepted": True,
                },
            }
            lineage_budget_exhausted = (
                lineage_budget_state.get("lineage_budget_exhausted") is True
            )
            if cross_artifact_revision_required or lineage_budget_exhausted:
                if cross_artifact_revision_required:
                    failure_classification = (
                        "generated_code_semantic_review_requires_cross_artifact_resolution"
                    )
                    rationale = (
                        "Independent semantic review found that editing the current "
                        "source alone cannot close the evidence-bound findings while "
                        "its upstream artifacts remain fixed. The cross-artifact "
                        "conflict is routed to Architect without a wasted source "
                        "regeneration or runtime-authored edit."
                    )
                else:
                    failure_classification = (
                        "generated_code_semantic_review_lineage_budget_exhausted"
                    )
                    rationale = (
                        "The generated-code semantic review exhausted its global "
                        "same-producer candidate-regeneration budget. The complete "
                        "rejected artifact and exact observations are routed to the "
                        "Architect model to select theory, interface, environment, or "
                        "implementation work without a runtime-authored source change."
                    )
                lineage_ledger = (
                    record_generated_code_semantic_review_lineage_action(
                        lineage_budget_state,
                        action="architect_replan",
                    )
                )
                execution_manifest["semantic_review_lineage_budget"][
                    "selected_action"
                ] = "architect_replan"
                execution_manifest[
                    GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY
                ] = lineage_ledger
                assert source_task is not None
                source_context = source_task_inputs.get(
                    "architect_context",
                    {},
                )
                source_context = (
                    dict(source_context)
                    if isinstance(source_context, Mapping)
                    else {}
                )
                source_context[
                    GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY
                ] = lineage_ledger
                architect_observation_payload = {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "artifact_kind": "RuntimeWorkspaceObservation",
                    "source_feedback_id": str(
                        feedback.get("feedback_id", "") or ""
                    ),
                    "feedback_source": GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM,
                    "question_id": question.id,
                    "source_task_id": source_task.task_id,
                    "source_subsystem": source_subsystem,
                    "source_manifest_id": str(
                        work_order.get("source_manifest_id", "") or ""
                    ),
                    "source_theory_packet_id": str(
                        work_order.get("theory_packet_id", "") or ""
                    ),
                    "failure_classification": failure_classification,
                    "semantic_review_lineage_budget": lineage_budget_summary,
                    "semantic_review_execution_id": execution_id,
                    "semantic_review_packet_id": review_packet_id,
                    "semantic_review_packet_hash": review_packet_hash,
                    "source_revision_assessment": deepcopy(
                        source_revision_assessment
                    ),
                    "findings": deepcopy(routed_findings),
                    "dimension_reviews": deepcopy(
                        list(review_packet.get("dimension_reviews", []) or [])
                    ),
                    "active_unresolved_finding_ids": deepcopy(
                        list(
                            review_packet.get(
                                "active_unresolved_finding_ids",
                                [],
                            )
                            or []
                        )
                    ),
                    "runtime_selected_source_edit": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                }
                architect_observation_id = (
                    "runtime_workspace_observation:"
                    + stable_hash(architect_observation_payload)[:20]
                )
                architect_observation = {
                    **architect_observation_payload,
                    "observation_id": architect_observation_id,
                    "feedback_id": architect_observation_id,
                }
                produced_artifacts[architect_observation_id] = (
                    architect_observation
                )
                next_task = _independent_semantic_review_architect_escalation_task(
                    task=source_task,
                    question=question,
                    context=source_context,
                    revision_feedback=architect_observation,
                    source_artifact_id=str(
                        work_order.get("source_manifest_id", "") or ""
                    ),
                )
                status = "REROUTE"
            else:
                lineage_ledger = (
                    record_generated_code_semantic_review_lineage_action(
                        lineage_budget_state,
                        action="producer_regeneration",
                    )
                )
                execution_manifest["semantic_review_lineage_budget"][
                    "selected_action"
                ] = "producer_regeneration"
                assert source_task is not None
                next_task = build_generated_code_semantic_review_producer_revision_task(
                    question=question,
                    review_task_id=task.task_id,
                    work_order=work_order,
                    source_task=source_task,
                    review_feedback=revision_feedback,
                    review_packet_id=review_packet_id,
                    review_execution_id=execution_id,
                    revision_count=revision_count,
                    max_revisions=max_revisions,
                    lineage_ledger=lineage_ledger,
                )
                status = "REVISE"
                rationale = (
                    "Independent semantic review rejected the exact executed artifact. "
                    "The complete source, execution evidence, and observations are "
                    "returned directly to the same source producer for one full "
                    "candidate regeneration."
                )
                failure_classification = revision_classification

        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, execution_id])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="generated_code_semantic_review",
            status=(
                "EXPLORATORY_SEMANTIC_REVIEW_ACCEPTED_NOT_CONFIRMATORY"
                if verdict == "ACCEPT"
                and not confirmatory_empirical_evidence_eligible
                else
                "SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
                if verdict == "ACCEPT"
                else "SEMANTIC_REVIEW_REVISION_REQUIRED_NOT_PROOF_EVIDENCE"
            ),
            boundary=GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
            payload={
                "source_subsystem": source_subsystem,
                "source_manifest_id": str(
                    work_order.get("source_manifest_id", "") or ""
                ),
                "overall_verdict": verdict,
                "routing_authority_on_revise": (
                    "architect_model_after_source_sufficiency_observation"
                    if cross_artifact_revision_required
                    else "architect_model_after_candidate_budget"
                    if lineage_budget_state.get("lineage_budget_exhausted") is True
                    else "immutable_source_producer_lineage"
                ),
                "runtime_selected_owner": False,
                "empirical_evaluation_phase": empirical_evaluation_phase,
                "confirmatory_empirical_evidence_eligible": (
                    confirmatory_empirical_evidence_eligible
                ),
                "reviewer_model": reviewer_model,
                "reviewer_model_tier": reviewer_tier,
                "n_findings": len(routed_findings),
                "semantic_review_lineage_key": str(
                    lineage_budget_state.get("lineage_key", "") or ""
                ),
                "semantic_review_lineage_budget_exhausted": bool(
                    lineage_budget_state.get("lineage_budget_exhausted")
                ),
                "kernel_verified": False,
            },
        )
        initial_review_artifact = review_audit_artifacts.get(
            initial_review_packet_id,
            review_packet,
        )
        initial_materialization = review_audit_artifacts.get(
            initial_materialization_id,
            materialization,
        )
        initial_review_fingerprint = str(
            initial_materialization.get("review_input_fingerprint", "") or ""
        )

        def review_call_record(
            *,
            tool_name: str,
            inputs: Mapping[str, Any],
            output: Mapping[str, Any],
            summary: str,
        ) -> ToolCallRecord:
            return ToolCallRecord(
                tool_name=tool_name,
                inputs=dict(inputs),
                input_hash=stable_hash(inputs),
                output_hash=stable_hash(output),
                exit_status="0",
                stdout_summary=summary,
                safety_boundary=GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
            )

        review_tool_calls = [
            review_call_record(
                tool_name="LLMGeneratedCodeSemanticReviewerAgent.review",
                inputs={
                    "work_order_id": work_order_id,
                    "review_input_fingerprint": initial_review_fingerprint,
                    "source_subsystem": source_subsystem,
                    "feedback_revision": False,
                },
                output=initial_review_artifact,
                summary=(
                    "initial_verdict="
                    + str(
                        initial_review_artifact.get(
                            "overall_verdict",
                            "",
                        )
                        or ""
                    )
                ),
            )
        ]
        return AgentStepResult(
            status=status,
            rationale=rationale,
            produced_artifacts=produced_artifacts,
            observations=(
                EnvironmentObservation(
                    observation_type="generated_code_semantic_review_result",
                    summary=(
                        f"source={source_subsystem} verdict={verdict} "
                        f"findings={len(routed_findings)}"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "review_packet_id": review_packet_id,
                        "source_manifest_id": str(
                            work_order.get("source_manifest_id", "") or ""
                        ),
                        "overall_verdict": verdict,
                        "empirical_evaluation_phase": empirical_evaluation_phase,
                        "confirmatory_empirical_evidence_eligible": (
                            confirmatory_empirical_evidence_eligible
                        ),
                        "next_owner_subsystem": (
                            next_task.owner_subsystem if next_task else ""
                        ),
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                ),
            ),
            tool_calls=tuple(review_tool_calls),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=failure_classification,
        )




def _runtime_simulation_metric_protocol_guard(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    theory_packet_id: str,
    theory_packet: Mapping[str, Any],
    architect_context: Mapping[str, Any],
    exploratory_diagnostic: bool,
) -> AgentStepResult | None:
    evidence_contract = _architect_runtime_plan(architect_context).get(
        "evidence_contract", {}
    )
    if not isinstance(evidence_contract, Mapping):
        evidence_contract = {}
    if exploratory_diagnostic or not _runtime_metric_protocol_authoring_required(
        evidence_contract=evidence_contract,
        architect_context=architect_context,
    ):
        return None

    context = invalidate_metric_protocol_authorization(architect_context)
    context["theory_packet_id"] = theory_packet_id
    context["architect_metric_protocol_theory_material"] = (
        build_theory_informed_metric_protocol_material(
            theory_packet=theory_packet,
            theory_packet_id=theory_packet_id,
            retrieval_context=(
                context.get("retrieval_context", {})
                if isinstance(context.get("retrieval_context", {}), Mapping)
                else {}
            ),
        )
    )
    prior_gate = context.get("architect_metric_protocol_gate", {})
    prior_gate = dict(prior_gate) if isinstance(prior_gate, Mapping) else {}
    context["architect_metric_protocol_gate"] = {
        **prior_gate,
        "artifact_kind": "RuntimeArchitectMetricProtocolGate",
        "source_theory_packet_id": theory_packet_id,
        "required_disposition": "PREEXECUTION_REVIEW_ACCEPTED",
        "execution_authorized": False,
        "consumed": False,
        "proof_evidence_status": (
            "ARCHITECT_METRIC_PROTOCOL_GATE_NOT_PROOF_EVIDENCE"
        ),
    }
    block_id = "metric_protocol_execution_blocked:" + stable_hash(
        [task.task_id, theory_packet_id, evidence_contract]
    )[:20]
    manifest = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeMetricProtocolExecutionBlocked",
        "manifest_id": block_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "source_task_id": task.task_id,
        "source_theory_packet_id": theory_packet_id,
        "source_requirement_set_id": str(
            evidence_contract.get("empirical_metric_requirement_set_id", "")
            or ""
        ),
        "execution_attempted": False,
        "execution_authorized": False,
        "required_next_owner": "ArchitectCoordinator",
        "proof_evidence_status": "METRIC_PROTOCOL_GUARD_NOT_PROOF_EVIDENCE",
        "boundary": (
            "This guard blocks SimulationEngineer generation and all simulation "
            "execution until the current theory-bound metric protocol passes "
            "independent pre-execution review. It is not empirical or proof evidence."
        ),
    }
    next_task = AgentTask(
        task_id=(
            f"architect-metric-protocol-guard:{question.id}:"
            f"{stable_hash(block_id)[:8]}"
        ),
        owner_subsystem="ArchitectCoordinator",
        objective=(
            "Author and independently review the current theory-bound empirical "
            "protocol before SimulationEvaluator may run."
        ),
        inputs={
            "question": _question_to_payload(question),
            "architect_context": context,
        },
        allowed_tools=("model_backend", "blackboard", "evidence_ledger"),
        expected_artifacts=(
            "architect_coordinator_proposal",
            "architect_metric_requirement_authoring",
            "architect_metric_semantic_review",
        ),
        acceptance_gate=(
            "the current theory-bound requirement set receives an independent "
            "pre-execution ACCEPT certificate"
        ),
        stop_condition=(
            "reviewed protocol is accepted or a typed owner-specific blocker is recorded"
        ),
    )
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, block_id])[:20],
        task_id=task.task_id,
        artifact_id=block_id,
        evidence_type="metric_protocol_execution_guard",
        status="EXECUTION_BLOCKED_PREEXECUTION_REVIEW_REQUIRED",
        boundary=str(manifest["boundary"]),
        payload={
            "source_theory_packet_id": theory_packet_id,
            "execution_attempted": False,
            "execution_authorized": False,
            "kernel_verified": False,
        },
    )
    return AgentStepResult(
        status="REROUTE",
        rationale=(
            "SimulationEvaluator refused to call the simulation agent because the "
            "current theory-bound metric protocol is not independently authorized."
        ),
        produced_artifacts={block_id: manifest},
        observations=(
            EnvironmentObservation(
                observation_type="metric_protocol_execution_blocked",
                summary="simulation generation and execution blocked before API call",
                payload={
                    "manifest_id": block_id,
                    "theory_packet_id": theory_packet_id,
                    "execution_attempted": False,
                },
            ),
        ),
        evidence_entries=(evidence,),
        next_task=next_task,
        failure_classification="metric_protocol_preexecution_authorization_required",
    )


class SimulationEvaluatorRuntimeSubsystem:
    name = "SimulationEvaluator"

    def __init__(
        self,
        *,
        proposal_agent: LLMSimulationEngineerAgent | None = None,
        sandbox_root: Path = Path("runs") / "generated_simulation_sandbox",
        semantic_reviewer_available: bool = False,
        semantic_review_max_revisions: int = 1,
        timeout_s: int = 60,
    ) -> None:
        self.proposal_agent = proposal_agent
        self.sandbox_root = sandbox_root
        self.semantic_reviewer_available = bool(semantic_reviewer_available)
        self.semantic_review_max_revisions = max(
            0,
            int(semantic_review_max_revisions or 0),
        )
        self.timeout_s = max(1, int(timeout_s or 60))

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        empirical_evaluation_phase = str(
            task.inputs.get("empirical_evaluation_phase", "")
            or context.get("empirical_evaluation_phase", "")
            or ""
        ).strip()
        exploratory_diagnostic = bool(
            empirical_evaluation_phase
            == EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
        )
        if empirical_evaluation_phase:
            context["empirical_evaluation_phase"] = empirical_evaluation_phase
        environment_feedback: Mapping[str, Any] = (
            task.inputs.get("environment_feedback", {})
            if isinstance(task.inputs.get("environment_feedback", {}), Mapping)
            else {}
        )
        effective_context = _runtime_context_with_environment_feedback_contract(
            context,
            environment_feedback,
            subsystem="SimulationEvaluator",
        )
        simulation_control = _architect_control_payload(context, "SimulationEvaluator")
        packet_id = str(task.inputs.get("theory_packet_id", ""))
        packet = blackboard.artifacts.get(packet_id, {})
        if not packet_id:
            next_task = AgentTask(
                task_id=f"theory:{question.id}:{stable_hash(task.task_id)[:8]}",
                owner_subsystem="TheoryDeveloper",
                objective=(
                    "Derive the theory and estimator interface required before any "
                    "theory-bound metric authoring or simulation execution."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": context,
                },
                allowed_tools=("model_backend", "rag_memory"),
                expected_artifacts=("theory_derivation_packet",),
                acceptance_gate=(
                    "validated model-authored theory packet with explicit assumptions, "
                    "estimand, derivation, and estimator interface"
                ),
                stop_condition="theory packet is recorded or a typed blocker is returned",
            )
            return AgentStepResult(
                status="REROUTE",
                rationale=(
                    "SimulationEvaluator has no upstream theory artifact, so the "
                    "declared prerequisite edge routes directly to TheoryDeveloper "
                    "before metric authoring or execution."
                ),
                observations=(
                    EnvironmentObservation(
                        observation_type="simulation_theory_prerequisite_missing",
                        summary="no theory packet has been authored",
                        payload={
                            "question_id": question.id,
                            "execution_attempted": False,
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                next_task=next_task,
                failure_classification="simulation_theory_prerequisite_missing",
            )
        if not isinstance(packet, Mapping) or not packet:
            missing_theory = _runtime_handoff_artifact_missing_result_if_needed(
                source_subsystem="SimulationEvaluator",
                task=task,
                question=question,
                artifact_role="theory_packet",
                artifact_id=packet_id,
                artifact=packet,
                expected_artifact_kind="TheoryDerivationPacket",
            )
            if missing_theory is not None:
                return missing_theory
        metric_protocol_guard = _runtime_simulation_metric_protocol_guard(
            task=task,
            question=question,
            theory_packet_id=packet_id,
            theory_packet=packet if isinstance(packet, Mapping) else {},
            architect_context=context,
            exploratory_diagnostic=exploratory_diagnostic,
        )
        if metric_protocol_guard is not None:
            return metric_protocol_guard
        algorithm_sandbox_manifest_id = str(
            task.inputs.get("algorithm_sandbox_manifest_id", "")
            or context.get("algorithm_sandbox_manifest_id", "")
            or ""
        ).strip()
        upstream_algorithm_handoff: dict[str, Any] = {}
        requires_accepted_algorithm_handoff = bool(
            not exploratory_diagnostic
            and context.get(
                "confirmatory_simulation_requires_accepted_algorithm_handoff"
            )
            is True
        )
        if requires_accepted_algorithm_handoff:
            upstream_algorithm_handoff = (
                _runtime_validated_algorithm_handoff(
                    task=task,
                    architect_context=context,
                    blackboard=blackboard,
                    question_id=question.id,
                    theory_packet_id=packet_id,
                    algorithm_sandbox_manifest_id=(
                        algorithm_sandbox_manifest_id
                    ),
                )
            )
            if not upstream_algorithm_handoff:
                simulation_manifest_id = str(
                    context.get("simulation_manifest_id", "")
                    or ""
                )
                missing_handoff = (
                    _runtime_missing_algorithm_handoff_result_if_needed(
                        source_subsystem="SimulationEvaluator",
                        task=task,
                        question=question,
                        algorithm_sandbox_manifest_id=(
                            algorithm_sandbox_manifest_id
                        ),
                        algorithm_manifest={},
                    )
                )
                if missing_handoff is not None:
                    return missing_handoff
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "Confirmatory simulation requires a hash-bound, independently "
                        "reviewed AlgorithmEngineer artifact, but no artifact identity "
                        "was available to recover."
                    ),
                    observations=(
                        EnvironmentObservation(
                            observation_type="accepted_algorithm_handoff_missing",
                            summary=(
                                "confirmatory simulation refused to run without an "
                                "accepted algorithm artifact"
                            ),
                            payload={
                                "question_id": question.id,
                                "theory_packet_id": packet_id,
                                "algorithm_sandbox_manifest_id": (
                                    algorithm_sandbox_manifest_id
                                ),
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    failure_classification="accepted_algorithm_handoff_missing",
                )
            context["upstream_algorithm_handoff"] = (
                upstream_algorithm_handoff
            )
            environment_feedback = {
                **dict(environment_feedback),
                "upstream_algorithm_handoff": upstream_algorithm_handoff,
            }
            effective_context = (
                _runtime_context_with_environment_feedback_contract(
                    context,
                    environment_feedback,
                    subsystem="SimulationEvaluator",
                )
            )
        runtime_theory_trace_contract = _runtime_theory_trace_consumption_contract(
            consumer_subsystem="SimulationEngineer",
            source_theory_packet_id=packet_id,
            theory_packet=packet if isinstance(packet, Mapping) else {},
        )
        llm_research_authority = runtime_llm_research_authority_required(
            effective_context,
            packet if isinstance(packet, Mapping) else {},
        )
        if llm_research_authority:
            research_bundle = derive_runtime_research_problem(
                question=question,
                architect_context=effective_context,
                theory_packet=packet if isinstance(packet, Mapping) else {},
            )
            problem = research_bundle.problem
            theorem_goals = list(research_bundle.theorem_goals)
            procedures: list[CandidateProcedure] = []
            problem_authority = research_bundle.provenance()
        else:
            problem = ProblemFormalizer().formalize(question)
            procedures, theorem_goals = TheoryPlanner().plan(problem)
            problem_authority = legacy_runtime_research_problem_provenance()
        n_runs = int(task.inputs.get("n_runs", 100))
        seed = int(task.inputs.get("seed", 20260528))
        proposal_packet: dict[str, Any] | None = None
        produced_artifacts: dict[str, Any] = {}
        proposal_evidence: EvidenceLedgerEntry | None = None
        simulation_theory_trace_contract: dict[str, Any] = {}
        simulation_theory_trace_alignment_contract: dict[str, Any] = {}
        raw_consumer_resume_manifest = task.inputs.get(
            "consumer_resume_manifest",
            {},
        )
        consumer_resume_manifest = (
            dict(raw_consumer_resume_manifest)
            if isinstance(raw_consumer_resume_manifest, Mapping)
            else {}
        )
        consumer_resume_manifest_id = str(
            consumer_resume_manifest.get("manifest_id", "") or ""
        ).strip()
        consumer_resume_manifest_hash = (
            stable_hash(consumer_resume_manifest)
            if consumer_resume_manifest
            else ""
        )
        consumer_resume_code_drafts: list[dict[str, Any]] = []
        observations: list[EnvironmentObservation] = [
            EnvironmentObservation(
                observation_type="research_problem_authority",
                summary=(
                    "problem source="
                    + str(
                        problem_authority.get(
                            "problem_formalization_source", ""
                        )
                    )
                ),
                payload={
                    "problem_class": problem.problem_class,
                    "estimand": problem.estimand,
                    "diagnostics": list(problem.diagnostics),
                    **problem_authority,
                },
            )
        ]
        if raw_consumer_resume_manifest:
            proposal_id, consumer_resume_code_drafts, resume_errors = (
                scientific_consumer_replay_drafts(
                    consumer_resume_manifest,
                    question_id=question.id,
                    theory_packet_id=packet_id,
                )
            )
            prior_proposal = blackboard.artifacts.get(proposal_id, {})
            if (
                not isinstance(prior_proposal, Mapping)
                or str(prior_proposal.get("packet_id", "") or "") != proposal_id
            ):
                resume_errors.append("consumer resume proposal artifact is missing")
            else:
                proposal_packet = dict(prior_proposal)
            if resume_errors:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "SimulationEvaluator rejected a stale or incomplete scientific "
                        "consumer continuation before any model or sandbox call."
                    ),
                    observations=tuple(observations)
                    + (
                        EnvironmentObservation(
                            observation_type=(
                                "scientific_consumer_continuation_rejected"
                            ),
                            summary="; ".join(sorted(set(resume_errors)))[:500],
                            payload={
                                "consumer_resume_manifest_id": (
                                    consumer_resume_manifest_id
                                ),
                                "validation_errors": sorted(set(resume_errors)),
                                "model_call_authorized": False,
                                "execution_authorized": False,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    failure_classification=(
                        "scientific_consumer_continuation_invalid"
                    ),
                )
            theory_trace_contracts = _runtime_theory_trace_consumption_contracts(
                proposal_packet or {}
            )
            simulation_theory_trace_contract = (
                theory_trace_contracts[0] if theory_trace_contracts else {}
            )
            simulation_theory_trace_alignment_contract = dict(
                (proposal_packet or {}).get(
                    "theory_trace_alignment_contract",
                    {},
                )
                or {}
            )
            observations.append(
                EnvironmentObservation(
                    observation_type="scientific_consumer_continuation_restored",
                    summary=(
                        "The exact prior model-authored consumer source will be rerun "
                        "with the newly reviewed dependency handoff."
                    ),
                    payload={
                        "consumer_resume_manifest_id": consumer_resume_manifest_id,
                        "consumer_resume_manifest_hash": (
                            consumer_resume_manifest_hash
                        ),
                        "simulation_artifact_ids": [
                            row["simulation_id"]
                            for row in consumer_resume_code_drafts
                        ],
                        "planning_model_call_used": False,
                        "runtime_edited_source": False,
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                )
            )
        elif self.proposal_agent is not None:
            available_upstream_estimator_ids = [
                str(row.get("estimator_id", "") or "").strip()
                for row in upstream_algorithm_handoff.get(
                    "exact_algorithm_artifacts", []
                )
                or []
                if isinstance(row, Mapping)
                and str(row.get("estimator_id", "") or "").strip()
            ]
            environment_feedback = {
                **dict(environment_feedback),
                "runtime_execution_contract": {
                    "timeout_seconds": self.timeout_s,
                    "runtime_replicates": generated_sandbox_runtime_replicates(
                        n_runs
                    ),
                    "available_upstream_estimator_ids": list(
                        dict.fromkeys(available_upstream_estimator_ids)
                    ),
                    "estimator_callback_policy": (
                        "Every estimator ID selected in required_estimator_ids "
                        "must be invoked at least once on the executed path. "
                        "Estimator callbacks run exact accepted source inside the "
                        "isolated scientific runtime and may dominate cost, so "
                        "avoid redundant calls while preserving the frozen protocol."
                    ),
                    "resource_policy": (
                        "The complete confirmatory workload must finish within "
                        "timeout_seconds. A timeout is failed execution evidence "
                        "and must be repaired from exact runtime diagnostics; it "
                        "does not authorize fewer frozen replicates or weaker gates."
                    ),
                    "evidence_boundary": (
                        "This contract controls generated simulation execution "
                        "only and is not theorem proof evidence."
                    ),
                },
            }
            effective_context = _runtime_context_with_environment_feedback_contract(
                context,
                environment_feedback,
                subsystem="SimulationEvaluator",
            )
            try:
                with agent_runtime_substage("simulation_planning_envelope"):
                    proposal_packet = self.proposal_agent.propose(
                        question=question,
                        theory_packet=(
                            packet if isinstance(packet, Mapping) else {}
                        ),
                        registered_problem=_problem_to_json(problem),
                        registered_procedures=[
                            _procedure_to_json(row) for row in procedures
                        ],
                        n_runs=n_runs,
                        seed=seed,
                        environment_feedback=(
                            _runtime_environment_feedback_with_architect_directive(
                                context=effective_context,
                                subsystem="SimulationEvaluator",
                                feedback=environment_feedback,
                            )
                        ),
                    )
            except PacketValidationError as exc:
                return _simulation_engineer_packet_validation_failure_result(
                    task=task,
                    question=question,
                    theory_packet_id=packet_id,
                    exc=exc,
                )
            proposal_id = str(proposal_packet["packet_id"])
            theory_trace_contracts = _runtime_theory_trace_consumption_contracts(
                proposal_packet
            )
            simulation_theory_trace_contract = (
                theory_trace_contracts[0] if theory_trace_contracts else {}
            )
            simulation_theory_trace_alignment_contract = (
                dict(proposal_packet.get("theory_trace_alignment_contract", {}))
                if isinstance(
                    proposal_packet.get("theory_trace_alignment_contract", {}),
                    Mapping,
                )
                else {}
            )
            produced_artifacts[proposal_id] = proposal_packet
            observations.append(
                EnvironmentObservation(
                    observation_type="llm_simulation_engineer_proposal",
                    summary=(
                        "validated LLM SimulatorEngineer proposal recorded before "
                        "registered simulator execution"
                    ),
                    payload={
                        "packet_id": proposal_id,
                        "n_dgp_plan_rows": len(proposal_packet.get("dgp_plan", []) or []),
                        "n_stress_tests": len(proposal_packet.get("stress_tests", []) or []),
                        "n_simulation_code_drafts": len(
                            proposal_packet.get("simulation_code_drafts", []) or []
                        ),
                        "simulation_evidence_status": SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
                        "runtime_theory_trace_consumption_contract": runtime_theory_trace_contract,
                        "theory_trace_consumption_contract": simulation_theory_trace_contract,
                        "theory_trace_alignment_contract": simulation_theory_trace_alignment_contract,
                    },
                )
            )
            proposal_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proposal_id])[:20],
                task_id=task.task_id,
                artifact_id=proposal_id,
                evidence_type="llm_simulation_engineer_proposal",
                status="PROPOSAL_RECORDED_REQUIRES_RUNTIME_EXECUTION",
                boundary=SIMULATION_ENGINEER_BOUNDARY,
                payload={
                    "n_dgp_plan_rows": len(proposal_packet.get("dgp_plan", []) or []),
                    "n_stress_tests": len(proposal_packet.get("stress_tests", []) or []),
                    "n_simulation_code_drafts": len(
                        proposal_packet.get("simulation_code_drafts", []) or []
                    ),
                    "simulations_executed": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    "runtime_theory_trace_consumption_contract": runtime_theory_trace_contract,
                    "theory_trace_consumption_contract": simulation_theory_trace_contract,
                    "theory_trace_alignment_contract": simulation_theory_trace_alignment_contract,
                },
            )
        requires_generated_simulation_code = bool(
            llm_research_authority
            or _runtime_requires_generated_simulation_code(
                effective_context,
                environment_feedback,
            )
        )
        requires_typed_metric_contracts = _runtime_requires_typed_metric_contracts(
            effective_context,
            environment_feedback,
            subsystem="SimulationEvaluator",
        ) and not exploratory_diagnostic
        agentic_simulation_authority = bool(
            llm_research_authority or requires_generated_simulation_code
        )
        if agentic_simulation_authority:
            simulations: list[ResearchSimulation] = []
            registered_baseline_skip_reason = (
                "Agentic runs evaluate LLM-generated simulation code; registered "
                "task-family simulators are optional legacy baselines and cannot "
                "satisfy the agentic evidence gate."
            )
        else:
            simulations = ResearchSimulator(n_runs=n_runs, seed=seed).run(
                problem,
                procedures,
            )
            registered_baseline_skip_reason = ""
        registered_simulator_tool_calls = (
            ()
            if agentic_simulation_authority
            else (
                ToolCallRecord(
                    tool_name="ResearchSimulator.run",
                    inputs={
                        "n_runs": n_runs,
                        "seed": seed,
                        "n_procedures": len(procedures),
                    },
                    exit_status="0",
                    stdout_summary=f"{len(simulations)} simulation rows recorded",
                    safety_boundary=SIMULATION_NOT_PROOF_BOUNDARY,
                ),
            )
        )
        generated_simulation_rows: list[dict[str, Any]] = []
        generated_simulation_tool_calls: list[ToolCallRecord] = []
        generated_simulation_dir = (
            self.sandbox_root
            / _safe_identifier(question.id)
            / stable_hash([task.task_id, packet_id])[:12]
        )
        (
            simulation_metric_requirements,
            simulation_metric_authority_policy,
            simulation_metric_authority_required,
        ) = _runtime_generated_metric_requirement_authority(
            effective_context,
            environment_feedback,
            architect_subsystem="SimulationEvaluator",
            target_subsystem="SimulationEngineer",
        )
        if exploratory_diagnostic:
            simulation_metric_requirements = []
            simulation_metric_authority_policy = (
                GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
            )
            simulation_metric_authority_required = False
        simulation_code_drafts = (
            consumer_resume_code_drafts
            if consumer_resume_manifest_id
            else _simulation_code_drafts(proposal_packet)
        )
        if (
            requires_generated_simulation_code
            and self.proposal_agent is not None
            and proposal_packet is not None
            and not simulation_code_drafts
        ):
            generated_simulation_rows.append(
                _annotate_generated_sandbox_prototype_provenance(
                    {
                        "simulation_id": "generated_simulation_required",
                        "prototype_status": (
                            "GENERATED_SIMULATION_CODE_REQUIRED_BUT_MISSING"
                        ),
                        "executor": "generated_simulation_sandbox",
                        "reason": (
                            "Agentic simulation authority requires an LLM-generated "
                            "simulation_code_drafts entry. Registered simulators are "
                            "optional baselines and cannot satisfy this evidence gate."
                        ),
                        "smoke_passed": False,
                        "execution_smoke_passed": False,
                        "simulation_evidence_status": (
                            "GENERATED_SIMULATION_SANDBOX_EXECUTION_MISSING"
                        ),
                    },
                    proposal_packet=proposal_packet,
                    source_feedback=environment_feedback,
                )
            )
        for draft in simulation_code_drafts:
            simulation_id = str(draft.get("simulation_id", "") or "simulation_draft")
            simulation_metric_contracts = generated_metric_contracts_for_artifact(
                (proposal_packet or {}).get("metric_contracts", []),
                artifact_id=simulation_id,
            )
            if requires_typed_metric_contracts and not simulation_metric_contracts:
                generated_simulation_rows.append(
                    _annotate_generated_sandbox_prototype_provenance(
                        {
                            "simulation_id": simulation_id,
                            "prototype_status": (
                                "TYPED_METRIC_CONTRACT_REQUIRED_BUT_MISSING"
                            ),
                            "executor": "generated_simulation_sandbox",
                            "reason": (
                                "Capability evaluation requires at least one "
                                "validated typed metric contract bound to this "
                                "generated simulation_id before execution."
                            ),
                            "metric_contracts": [],
                            "metric_contract_set_id": "",
                            "metric_contract_evaluation": {},
                            "metric_contract_proof_evidence_status": (
                                GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
                            ),
                            "metric_contract_boundary": (
                                GENERATED_METRIC_CONTRACT_BOUNDARY
                            ),
                            "metric_gate_policy_mode": (
                                "typed_artifact_bound_required_missing"
                            ),
                            "smoke_passed": False,
                            "execution_smoke_passed": False,
                            "simulation_evidence_status": (
                                "GENERATED_SIMULATION_TYPED_METRIC_CONTRACT_MISSING"
                            ),
                        },
                        proposal_packet=proposal_packet,
                        source_feedback=environment_feedback,
                    )
                )
                continue
            (
                simulation_metric_contracts,
                metric_authority_errors,
            ) = _runtime_bind_and_validate_generated_metric_authority(
                simulation_metric_contracts,
                artifact_id=simulation_id,
                authoritative_requirements=simulation_metric_requirements,
                target_subsystem="SimulationEngineer",
                require_authoritative_requirements=(
                    simulation_metric_authority_required
                ),
            )
            if metric_authority_errors:
                generated_simulation_rows.append(
                    _annotate_generated_sandbox_prototype_provenance(
                        {
                            "simulation_id": simulation_id,
                            "prototype_status": (
                                "METRIC_REQUIREMENT_AUTHORITY_REJECTED"
                            ),
                            "executor": "generated_simulation_sandbox",
                            "reason": (
                                "Generated required metric contracts did not "
                                "preserve the independent Architect requirement set."
                            ),
                            "metric_contracts": simulation_metric_contracts,
                            "metric_contract_set_id": (
                                generated_metric_contract_set_id(
                                    simulation_metric_contracts
                                )
                            ),
                            "metric_requirement_set_id": (
                                generated_metric_requirement_set_id(
                                    simulation_metric_requirements
                                )
                            ),
                            "metric_requirement_authority_policy": (
                                simulation_metric_authority_policy
                            ),
                            "metric_requirement_authority_required": (
                                simulation_metric_authority_required
                            ),
                            "metric_requirement_authority_errors": (
                                metric_authority_errors
                            ),
                            "metric_requirement_authority_validated": False,
                            "metric_contract_evaluation": {},
                            "metric_contract_proof_evidence_status": (
                                GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
                            ),
                            "metric_contract_boundary": (
                                GENERATED_METRIC_CONTRACT_BOUNDARY
                            ),
                            "metric_gate_policy_mode": (
                                "architect_requirement_authority_rejected"
                            ),
                            "smoke_passed": False,
                            "execution_smoke_passed": False,
                            "simulation_evidence_status": (
                                "GENERATED_SIMULATION_METRIC_REQUIREMENT_AUTHORITY_REJECTED"
                            ),
                        },
                        proposal_packet=proposal_packet,
                        source_feedback=environment_feedback,
                    )
                )
                continue
            execution_kwargs = {
                "sandbox_dir": generated_simulation_dir,
                "simulation_id": simulation_id,
                "proposal_packet": proposal_packet or {},
                "metric_contracts": simulation_metric_contracts,
                "validation_context": {
                    "question": _question_to_payload(question),
                    "architect_context": effective_context,
                    "environment_feedback": dict(environment_feedback),
                    "authoritative_metric_requirements": (
                        simulation_metric_requirements
                    ),
                    "metric_requirement_authority_policy": (
                        simulation_metric_authority_policy
                    ),
                    "require_authoritative_metric_requirements": (
                        simulation_metric_authority_required
                    ),
                    "metric_requirement_target_subsystem": (
                        "SimulationEngineer"
                    ),
                },
                "upstream_algorithm_handoff": upstream_algorithm_handoff,
                "n_runs": n_runs,
                "seed": seed,
                "timeout_s": self.timeout_s,
            }
            prototype, source_tool_calls = (
                _run_source_owner_scientific_workspace(
                    proposal_agent=self.proposal_agent,
                    question=question,
                    artifact_id=f"{question.id}:{simulation_id}",
                    code_draft=draft,
                    source_deferred=(
                        not consumer_resume_manifest_id
                        and _proposal_defers_scientific_source(proposal_packet)
                    ),
                    workspace_context={
                        "theory_packet_id": packet_id,
                        "simulation_id": simulation_id,
                        "simulation_target": next(
                            (
                                dict(row)
                                for row in (proposal_packet or {}).get(
                                    "simulation_targets", []
                                )
                                or []
                                if isinstance(row, Mapping)
                                and str(row.get("procedure_id", "") or "")
                                == simulation_id
                            ),
                            {},
                        ),
                        "theory_simulation_spec": dict(
                            packet.get("simulation_ademp_spec", {})
                            if isinstance(
                                packet.get("simulation_ademp_spec", {}),
                                Mapping,
                            )
                            else {}
                        ),
                        "metric_contracts": (
                            _scientific_workspace_metric_contracts(
                                simulation_metric_contracts
                            )
                        ),
                        "required_estimator_ids": list(
                            draft.get("required_estimator_ids", []) or []
                        ),
                        "upstream_algorithm_handoff": (
                            _scientific_workspace_algorithm_handoff(
                                upstream_algorithm_handoff
                            )
                        ),
                        "run_sandbox_contract": (
                            "run_sandbox(seed: int, replicates: int, estimators: "
                            "dict) returns named JSON-finite raw measurements at "
                            "every frozen metric_path"
                            if upstream_algorithm_handoff
                            else "run_sandbox(seed: int, replicates: int) returns "
                            "named JSON-finite raw measurements at every frozen "
                            "metric_path"
                        ),
                    },
                    execute_candidate=lambda candidate: (
                        _run_generated_simulation_sandbox(
                            code_draft=candidate,
                            **execution_kwargs,
                        )
                    ),
                    failure_identity={
                        "simulation_id": simulation_id,
                        "executor": "generated_simulation_sandbox",
                    },
                )
            )
            generated_simulation_tool_calls.extend(source_tool_calls)
            generated_simulation_rows.append(
                _annotate_generated_sandbox_prototype_provenance(
                    prototype,
                    proposal_packet=proposal_packet,
                    source_feedback=environment_feedback,
                )
            )
        n_generated_simulation_executed = sum(
            1
            for row in generated_simulation_rows
            if _generated_sandbox_row_executed(row)
        )
        n_live_generated_simulation_executed = sum(
            1
            for row in generated_simulation_rows
            if _generated_sandbox_row_executed(row)
            and _generated_sandbox_row_live_generated(row)
        )
        n_generated_simulation_execution_attempted = sum(
            1
            for row in generated_simulation_rows
            if _generated_sandbox_row_execution_attempted(row)
        )
        n_live_generated_simulation_execution_attempted = sum(
            1
            for row in generated_simulation_rows
            if _generated_sandbox_row_execution_attempted(row)
            and _generated_sandbox_row_live_generated(row)
        )
        n_generated_simulation_execution_failed = sum(
            1
            for row in generated_simulation_rows
            if row.get("prototype_status") == "FAILED"
        )
        n_live_generated_simulation_execution_failed = sum(
            1
            for row in generated_simulation_rows
            if row.get("prototype_status") == "FAILED"
            and _generated_sandbox_row_live_generated(row)
        )
        n_generated_simulation_estimator_binding_failed = sum(
            1
            for row in generated_simulation_rows
            if row.get("estimator_binding_errors")
        )
        n_generated_simulation_estimator_runtime_failed = sum(
            1
            for row in generated_simulation_rows
            if row.get("estimator_runtime_errors")
        )
        n_generated_simulation_passed = sum(
            1 for row in generated_simulation_rows if row.get("smoke_passed") is True
        )
        n_live_generated_simulation_passed = sum(
            1
            for row in generated_simulation_rows
            if row.get("smoke_passed") is True
            and _generated_sandbox_row_live_generated(row)
        )
        n_generated_simulation_metric_gate_failed = sum(
            1
            for row in generated_simulation_rows
            if row.get("prototype_status") == "FAILED_METRIC_GATE"
        )
        n_live_generated_simulation_metric_gate_failed = sum(
            1
            for row in generated_simulation_rows
            if row.get("prototype_status") == "FAILED_METRIC_GATE"
            and _generated_sandbox_row_live_generated(row)
        )
        n_unsafe_generated_simulation_rejected = sum(
            1
            for row in generated_simulation_rows
            if row.get("prototype_status") == "REJECTED_UNSAFE_GENERATED_CODE"
        )
        n_live_unsafe_generated_simulation_rejected = sum(
            1
            for row in generated_simulation_rows
            if row.get("prototype_status") == "REJECTED_UNSAFE_GENERATED_CODE"
            and _generated_sandbox_row_live_generated(row)
        )
        n_generated_simulation_typed_metric_contracts_declared = sum(
            len(row.get("metric_contracts", []) or [])
            for row in generated_simulation_rows
        )
        n_generated_simulation_typed_metric_contracts_evaluated = sum(
            _generated_metric_contract_evaluation_count(row, "n_contracts")
            for row in generated_simulation_rows
        )
        n_generated_simulation_typed_metric_contracts_passed = sum(
            _generated_metric_contract_evaluation_count(row, "n_passed")
            for row in generated_simulation_rows
        )
        n_generated_simulation_typed_metric_contracts_failed = sum(
            _generated_metric_contract_evaluation_count(row, "n_failed")
            for row in generated_simulation_rows
        )
        generated_simulation_rows_all_passed = bool(
            generated_simulation_rows
        ) and all(
            row.get("smoke_passed") is True
            for row in generated_simulation_rows
        )
        generated_simulation_revision_required = bool(
            self.proposal_agent is not None
            and (
                (
                    requires_generated_simulation_code
                    and (
                        not generated_simulation_rows_all_passed
                        or n_unsafe_generated_simulation_rejected > 0
                    )
                )
                or (
                    generated_simulation_rows
                    and not requires_generated_simulation_code
                    and not generated_simulation_rows_all_passed
                )
            )
        )
        registered_simulation_passed = bool(simulations) and all(
            row.passed for row in simulations
        )
        generated_simulation_passed = bool(
            n_generated_simulation_executed > 0
            and n_generated_simulation_passed > 0
            and generated_simulation_rows_all_passed
            and not generated_simulation_revision_required
        )
        simulation_passed = (
            generated_simulation_passed
            if agentic_simulation_authority
            else registered_simulation_passed
        )
        simulation_evidence_source = (
            "generated_simulation_sandbox"
            if agentic_simulation_authority
            else "registered_research_simulator_baseline"
        )
        requires_generated_algorithm_code = bool(
            llm_research_authority
            or _runtime_requires_generated_algorithm_code(
                effective_context,
                environment_feedback,
            )
        )
        implementation_gaps = _implementation_gaps(
            packet,
            procedures,
            require_generated_adapter=requires_generated_algorithm_code,
        )
        confirmatory_empirical_evidence_eligible = not exploratory_diagnostic
        confirmatory_simulation_passed = bool(
            simulation_passed and confirmatory_empirical_evidence_eligible
        )
        manifest_id = "simulation_manifest:" + stable_hash([task.task_id, packet_id, n_runs, seed])[:20]
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeSimulationManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "consumer_resume_manifest_id": consumer_resume_manifest_id,
            "consumer_resume_manifest_hash": consumer_resume_manifest_hash,
            "consumer_resume_exact_source_replayed": bool(
                consumer_resume_manifest_id
            ),
            "empirical_evaluation_phase": empirical_evaluation_phase,
            "exploratory_diagnostic": exploratory_diagnostic,
            "confirmatory_empirical_evidence_eligible": (
                confirmatory_empirical_evidence_eligible
            ),
            "upstream_algorithm_handoff_receipt": (
                _runtime_algorithm_handoff_receipt(
                    upstream_algorithm_handoff,
                    simulation_rows=generated_simulation_rows,
                )
            ),
            "exploratory_simulation_passed": bool(
                simulation_passed and exploratory_diagnostic
            ),
            "runtime_architect_control": simulation_control,
            "research_problem_authority": problem_authority,
            **problem_authority,
            "theory_trace_consumption_contract": runtime_theory_trace_contract,
            "llm_simulation_engineer_proposal_id": (
                str(proposal_packet.get("packet_id", "")) if proposal_packet else ""
            ),
            "llm_simulation_engineer_theory_trace_consumption_contract": (
                simulation_theory_trace_contract
            ),
            "llm_simulation_engineer_theory_trace_alignment_contract": (
                simulation_theory_trace_alignment_contract
            ),
            "problem": _problem_to_json(problem),
            "registered_procedures": [_procedure_to_json(row) for row in procedures],
            "registered_baseline_execution_skipped": bool(
                registered_baseline_skip_reason
            ),
            "registered_baseline_execution_skipped_reason": (
                registered_baseline_skip_reason
            ),
            "theorem_goals": [_theorem_goal_to_json(row) for row in theorem_goals],
            "simulations": [_simulation_to_json(row) for row in simulations],
            "generated_simulation_sandbox_prototypes": generated_simulation_rows,
            "n_generated_simulation_sandbox_prototypes": len(generated_simulation_rows),
            "n_generated_simulation_sandbox_executed": n_generated_simulation_executed,
            "n_live_generated_simulation_sandbox_executed": (
                n_live_generated_simulation_executed
            ),
            "n_generated_simulation_sandbox_execution_attempted": (
                n_generated_simulation_execution_attempted
            ),
            "n_live_generated_simulation_sandbox_execution_attempted": (
                n_live_generated_simulation_execution_attempted
            ),
            "n_generated_simulation_sandbox_execution_failed": (
                n_generated_simulation_execution_failed
            ),
            "n_live_generated_simulation_sandbox_execution_failed": (
                n_live_generated_simulation_execution_failed
            ),
            "n_generated_simulation_estimator_binding_failed": (
                n_generated_simulation_estimator_binding_failed
            ),
            "n_generated_simulation_estimator_runtime_failed": (
                n_generated_simulation_estimator_runtime_failed
            ),
            "n_generated_simulation_sandbox_passed": (
                n_generated_simulation_passed
                if confirmatory_empirical_evidence_eligible
                else 0
            ),
            "n_live_generated_simulation_sandbox_passed": (
                n_live_generated_simulation_passed
                if confirmatory_empirical_evidence_eligible
                else 0
            ),
            "n_exploratory_generated_simulation_sandbox_passed": (
                n_generated_simulation_passed if exploratory_diagnostic else 0
            ),
            "n_live_exploratory_generated_simulation_sandbox_passed": (
                n_live_generated_simulation_passed
                if exploratory_diagnostic
                else 0
            ),
            "n_generated_simulation_sandbox_metric_gate_failed": (
                n_generated_simulation_metric_gate_failed
            ),
            "n_live_generated_simulation_sandbox_metric_gate_failed": (
                n_live_generated_simulation_metric_gate_failed
            ),
            "n_unsafe_generated_simulation_code_rejected": n_unsafe_generated_simulation_rejected,
            "n_live_unsafe_generated_simulation_code_rejected": (
                n_live_unsafe_generated_simulation_rejected
            ),
            "n_generated_simulation_typed_metric_contracts_declared": (
                n_generated_simulation_typed_metric_contracts_declared
            ),
            "n_generated_simulation_typed_metric_contracts_evaluated": (
                n_generated_simulation_typed_metric_contracts_evaluated
            ),
            "n_generated_simulation_typed_metric_contracts_passed": (
                n_generated_simulation_typed_metric_contracts_passed
            ),
            "n_generated_simulation_typed_metric_contracts_failed": (
                n_generated_simulation_typed_metric_contracts_failed
            ),
            "generated_code_semantic_reviewer_available": (
                self.semantic_reviewer_available
            ),
            "generated_code_semantic_review_pending": bool(
                self.semantic_reviewer_available
                and not generated_simulation_revision_required
                and any(
                    row.get("smoke_passed") is True
                    or row.get("execution_smoke_passed") is True
                    for row in generated_simulation_rows
                )
            ),
            "typed_metric_contract_proof_evidence_status": (
                GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
            ),
            "simulation_passed": confirmatory_simulation_passed,
            "registered_simulation_passed": registered_simulation_passed,
            "generated_simulation_passed": bool(
                generated_simulation_passed
                and confirmatory_empirical_evidence_eligible
            ),
            "simulation_evidence_source": simulation_evidence_source,
            "implementation_gaps": implementation_gaps,
            "proof_evidence_status": "SIMULATION_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": SIMULATION_NOT_PROOF_BOUNDARY,
        }
        produced_artifacts[manifest_id] = manifest
        observations.append(
            EnvironmentObservation(
                observation_type="simulation_result",
                summary=(
                    f"source={simulation_evidence_source} "
                    f"diagnostic_passed={simulation_passed} "
                    f"confirmatory_passed={confirmatory_simulation_passed}"
                ),
                payload={
                    "n_simulations": len(simulations),
                    "simulation_passed": confirmatory_simulation_passed,
                    "exploratory_simulation_passed": bool(
                        simulation_passed and exploratory_diagnostic
                    ),
                    "empirical_evaluation_phase": empirical_evaluation_phase,
                    "confirmatory_empirical_evidence_eligible": (
                        confirmatory_empirical_evidence_eligible
                    ),
                    "simulation_evidence_source": simulation_evidence_source,
                    "registered_baseline_execution_skipped": bool(
                        registered_baseline_skip_reason
                    ),
                    "procedure_ids": [row.procedure_id for row in simulations],
                    "failed_procedure_ids": [row.procedure_id for row in simulations if not row.passed],
                    "n_generated_simulation_sandbox_executed": n_generated_simulation_executed,
                    "n_generated_simulation_sandbox_execution_attempted": (
                        n_generated_simulation_execution_attempted
                    ),
                    "n_generated_simulation_sandbox_execution_failed": (
                        n_generated_simulation_execution_failed
                    ),
                    "n_generated_simulation_sandbox_passed": (
                        n_generated_simulation_passed
                        if confirmatory_empirical_evidence_eligible
                        else 0
                    ),
                    "n_exploratory_generated_simulation_sandbox_passed": (
                        n_generated_simulation_passed
                        if exploratory_diagnostic
                        else 0
                    ),
                    "n_generated_simulation_sandbox_metric_gate_failed": (
                        n_generated_simulation_metric_gate_failed
                    ),
                    "n_unsafe_generated_simulation_code_rejected": n_unsafe_generated_simulation_rejected,
                    "n_generated_simulation_typed_metric_contracts_evaluated": (
                        n_generated_simulation_typed_metric_contracts_evaluated
                    ),
                    "n_generated_simulation_typed_metric_contracts_failed": (
                        n_generated_simulation_typed_metric_contracts_failed
                    ),
                },
            )
        )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="simulation",
            status=(
                "EXPLORATORY_EXECUTED_NOT_CONFIRMATORY"
                if exploratory_diagnostic
                and (simulations or n_generated_simulation_executed > 0)
                else "EXECUTED_REPRODUCIBLY"
                if simulations or n_generated_simulation_executed > 0
                else "NO_EXECUTABLE_SIMULATION"
            ),
            boundary=SIMULATION_NOT_PROOF_BOUNDARY,
            payload={
                "n_runs": n_runs,
                "seed": seed,
                "simulation_passed": confirmatory_simulation_passed,
                "exploratory_simulation_passed": bool(
                    simulation_passed and exploratory_diagnostic
                ),
                "empirical_evaluation_phase": empirical_evaluation_phase,
                "confirmatory_empirical_evidence_eligible": (
                    confirmatory_empirical_evidence_eligible
                ),
                "simulation_evidence_source": simulation_evidence_source,
                "problem_formalization_source": str(
                    problem_authority.get("problem_formalization_source", "")
                ),
                "n_generated_simulation_sandbox_executed": n_generated_simulation_executed,
                "n_generated_simulation_sandbox_execution_attempted": (
                    n_generated_simulation_execution_attempted
                ),
                "n_generated_simulation_sandbox_execution_failed": (
                    n_generated_simulation_execution_failed
                ),
                "n_generated_simulation_sandbox_passed": (
                    n_generated_simulation_passed
                    if confirmatory_empirical_evidence_eligible
                    else 0
                ),
                "n_exploratory_generated_simulation_sandbox_passed": (
                    n_generated_simulation_passed
                    if exploratory_diagnostic
                    else 0
                ),
                "n_generated_simulation_sandbox_metric_gate_failed": (
                    n_generated_simulation_metric_gate_failed
                ),
                "n_live_generated_simulation_sandbox_executed": (
                    n_live_generated_simulation_executed
                ),
                "n_live_generated_simulation_sandbox_execution_attempted": (
                    n_live_generated_simulation_execution_attempted
                ),
                "n_live_generated_simulation_sandbox_execution_failed": (
                    n_live_generated_simulation_execution_failed
                ),
                "n_live_generated_simulation_sandbox_passed": (
                    n_live_generated_simulation_passed
                ),
                "n_live_generated_simulation_sandbox_metric_gate_failed": (
                    n_live_generated_simulation_metric_gate_failed
                ),
                "n_unsafe_generated_simulation_code_rejected": n_unsafe_generated_simulation_rejected,
                "n_generated_simulation_typed_metric_contracts_evaluated": (
                    n_generated_simulation_typed_metric_contracts_evaluated
                ),
                "n_generated_simulation_typed_metric_contracts_passed": (
                    n_generated_simulation_typed_metric_contracts_passed
                ),
                "n_generated_simulation_typed_metric_contracts_failed": (
                    n_generated_simulation_typed_metric_contracts_failed
                ),
                "typed_metric_contract_proof_evidence_status": (
                    GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
                ),
                "architect_acceptance_gate": simulation_control.get("acceptance_gate", ""),
            },
        )
        if generated_simulation_revision_required:
            generated_simulation_failure_classification = (
                "accepted_algorithm_estimator_abi_failed"
                if n_generated_simulation_estimator_binding_failed > 0
                else "accepted_algorithm_estimator_runtime_failed"
                if n_generated_simulation_estimator_runtime_failed > 0
                else "generated_simulation_sandbox_metric_gate_failed"
                if n_generated_simulation_metric_gate_failed > 0
                else "generated_simulation_typed_metric_contract_missing"
                if any(
                    row.get("prototype_status")
                    == "TYPED_METRIC_CONTRACT_REQUIRED_BUT_MISSING"
                    for row in generated_simulation_rows
                )
                else "generated_simulation_sandbox_execution_failed"
                if n_generated_simulation_execution_failed > 0
                else "generated_simulation_sandbox_no_executable_draft"
            )
            feedback = _generated_simulation_revision_feedback(
                manifest=manifest,
                boundary=SIMULATION_NOT_PROOF_BOUNDARY,
                failure_classification=generated_simulation_failure_classification,
            )
            algorithm_dependency_failed = bool(
                n_generated_simulation_estimator_binding_failed > 0
                or n_generated_simulation_estimator_runtime_failed > 0
            )
            source_algorithm_manifest_id = str(
                upstream_algorithm_handoff.get(
                    "algorithm_sandbox_manifest_id", ""
                )
                or ""
            )
            source_algorithm_manifest = blackboard.artifacts.get(
                source_algorithm_manifest_id, {}
            )
            if (
                algorithm_dependency_failed
                and source_algorithm_manifest_id
                and isinstance(source_algorithm_manifest, Mapping)
                and source_algorithm_manifest
            ):
                (
                    dependency_context,
                    dependency_context_errors,
                ) = scientific_consumer_dependency_context(
                    generated_simulation_rows
                )
                if (
                    str(dependency_context.get("source_manifest_id", "") or "")
                    != source_algorithm_manifest_id
                    or str(
                        dependency_context.get("source_manifest_hash", "") or ""
                    )
                    != stable_hash(dict(source_algorithm_manifest))
                ):
                    dependency_context_errors.append(
                        "consumer dependency does not match the accepted source manifest"
                    )
                (
                    consumer_task_budget,
                    consumer_budget_state,
                    consumer_budget_errors,
                ) = advance_scientific_consumer_revision_budget(
                    task_budget=task.budget,
                    question_id=question.id,
                    theory_packet_id=packet_id,
                    dependency_context=dependency_context,
                    failure_classification=(
                        generated_simulation_failure_classification
                    ),
                    max_revisions=self.semantic_review_max_revisions,
                )
                consumer_errors = sorted(
                    set(dependency_context_errors + consumer_budget_errors)
                )
                if consumer_errors or consumer_budget_state.get(
                    "budget_exhausted"
                ) is True:
                    failure_classification = (
                        "scientific_consumer_lineage_invalid"
                        if consumer_errors
                        else "scientific_consumer_revision_budget_exhausted"
                    )
                    observations.append(
                        EnvironmentObservation(
                            observation_type=failure_classification,
                            summary=(
                                "; ".join(consumer_errors)[:500]
                                if consumer_errors
                                else "The frozen consumer-to-source revision budget "
                                "is exhausted for this exact consumer lineage."
                            ),
                            payload={
                                "simulation_manifest_id": manifest_id,
                                "source_algorithm_manifest_id": (
                                    source_algorithm_manifest_id
                                ),
                                "dependency_context": dependency_context,
                                "consumer_revision_budget": consumer_budget_state,
                                "validation_errors": consumer_errors,
                                "next_owner_subsystem": "",
                                "runtime_edited_source": False,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        )
                    )
                    return AgentStepResult(
                        status="BLOCKED",
                        rationale=(
                            "The exact scientific consumer lineage cannot schedule "
                            "another source-owner revision. The last raw observation "
                            "remains unresolved and no unrelated evidence lane is run."
                        ),
                        produced_artifacts=produced_artifacts,
                        observations=tuple(observations),
                        tool_calls=(
                            *registered_simulator_tool_calls,
                            *generated_simulation_tool_calls,
                        ),
                        evidence_entries=tuple(
                            row
                            for row in (proposal_evidence, evidence)
                            if row is not None
                        ),
                        failure_classification=failure_classification,
                    )
                resume_inputs = deepcopy(dict(task.inputs))
                resume_context = deepcopy(dict(effective_context))
                resume_context["simulation_manifest_id"] = manifest_id
                resume_context["algorithm_sandbox_manifest_id"] = (
                    source_algorithm_manifest_id
                )
                resume_inputs["architect_context"] = resume_context
                resume_inputs["consumer_resume_manifest"] = manifest
                consumer_resume_task = replace(
                    task,
                    task_id=(
                        f"simulation-consumer-resume:{question.id}:"
                        f"{stable_hash([manifest_id, consumer_budget_state])[:8]}"
                    ),
                    objective=(
                        "Rerun the exact failed model-authored scientific consumer "
                        "after its revised dependency passes independent review."
                    ),
                    inputs=resume_inputs,
                    budget=consumer_task_budget,
                )
                (
                    _consumer_continuation_id,
                    consumer_continuation,
                    consumer_continuation_artifacts,
                ) = materialize_agent_task_continuation(
                    consumer_resume_task,
                    linked_input_references={
                        stable_hash(manifest): runtime_artifact_reference(
                            manifest_id,
                            manifest,
                        )
                    },
                )
                produced_artifacts.update(consumer_continuation_artifacts)
                consumer_continuation_ref = agent_task_continuation_reference(
                    consumer_continuation
                )
                algorithm_feedback = _algorithm_sandbox_revision_feedback(
                    manifest=source_algorithm_manifest,
                    boundary=str(
                        source_algorithm_manifest.get("boundary", "")
                        or SIMULATION_NOT_PROOF_BOUNDARY
                    ),
                    failure_classification=(
                        generated_simulation_failure_classification
                    ),
                )
                algorithm_feedback.pop("prototypes", None)
                observation_transport = dict(
                    algorithm_feedback.get("observation_transport", {}) or {}
                )
                observation_transport["complete_candidate_rows"] = False
                observation_transport["source_scope"] = (
                    "exact_failed_dependency_artifacts"
                )
                observation_transport["source_retrieval"] = (
                    "hash_bound_blackboard_manifest"
                )
                algorithm_feedback["observation_transport"] = observation_transport
                algorithm_feedback["consumer_source_owner"] = dependency_context
                algorithm_feedback["runtime_selected_source_edit"] = False
                algorithm_feedback["feedback_id"] = (
                    "algorithm_sandbox_execution_feedback:"
                    + stable_hash(algorithm_feedback)[:20]
                )
                revision_context = dict(effective_context)
                revision_context["simulation_manifest_id"] = manifest_id
                revision_context["algorithm_sandbox_manifest_id"] = (
                    source_algorithm_manifest_id
                )
                revision_context["runtime_feedback_loop"] = {
                    **(
                        dict(
                            revision_context.get("runtime_feedback_loop", {})
                        )
                        if isinstance(
                            revision_context.get("runtime_feedback_loop", {}),
                            Mapping,
                        )
                        else {}
                    ),
                    "source_subsystem": "AlgorithmEngineer",
                    "handoff": "algorithm_sandbox_execution_feedback",
                }
                next_task = AgentTask(
                    task_id=(
                        f"algorithm-consumer-observation:{question.id}:"
                        f"{stable_hash(algorithm_feedback)[:8]}"
                    ),
                    owner_subsystem="AlgorithmEngineer",
                    objective=(
                        "Revise only the exact failed algorithm source artifacts from "
                        "their parent source and raw consumer execution observation."
                    ),
                    inputs={
                        "question": _question_to_payload(question),
                        "theory_packet_id": packet_id,
                        "simulation_manifest_id": manifest_id,
                        "implementation_gaps": implementation_gaps,
                        "n_runs": n_runs,
                        "seed": seed,
                        "architect_context": revision_context,
                        "environment_feedback": algorithm_feedback,
                        "consumer_source_manifest": source_algorithm_manifest,
                        "source_revision_artifact_ids": deepcopy(
                            dependency_context.get(
                                "dependency_artifact_ids",
                                [],
                            )
                        ),
                        "deferred_consumer_task_continuation_ref": (
                            consumer_continuation_ref
                        ),
                    },
                    allowed_tools=("python", "filesystem_sandbox"),
                    budget=consumer_task_budget,
                    expected_artifacts=_architect_expected_artifacts(
                        context,
                        "AlgorithmEngineer",
                        ("algorithm_sandbox_manifest",),
                    ),
                    acceptance_gate=_architect_acceptance_gate(
                        context,
                        "AlgorithmEngineer",
                        "regenerated algorithm source executes and exports its "
                        "declared consumer interface",
                    ),
                    stop_condition="new algorithm execution observation recorded",
                )
                return AgentStepResult(
                    status="REROUTE",
                    rationale=(
                        "A real consumer execution failed inside the accepted "
                        "algorithm dependency, so only its exact source artifacts and "
                        "raw observation return to AlgorithmEngineer. The failed "
                        "consumer is retained as the deferred continuation."
                    ),
                    produced_artifacts=produced_artifacts,
                    observations=tuple(observations),
                    tool_calls=(
                        *registered_simulator_tool_calls,
                        *generated_simulation_tool_calls,
                    ),
                    evidence_entries=tuple(
                        row
                        for row in (
                            proposal_evidence,
                            evidence,
                        )
                        if row is not None
                    ),
                    next_task=next_task,
                    failure_classification=(
                        generated_simulation_failure_classification
                    ),
                )
            deferred_metric_protocol_payload = task.inputs.get(
                "deferred_metric_protocol_task", {}
            )
            if (
                exploratory_diagnostic
                and isinstance(deferred_metric_protocol_payload, Mapping)
                and deferred_metric_protocol_payload
            ):
                deferred_gate = _agent_task_from_runtime_payload(
                    deferred_metric_protocol_payload
                )
                deferred_inputs = dict(deferred_gate.inputs)
                deferred_context = dict(
                    deferred_inputs.get("architect_context", {}) or {}
                )
                deferred_context["exploratory_diagnostic_feedback"] = feedback
                deferred_inputs["architect_context"] = deferred_context
                deferred_inputs["environment_feedback"] = feedback
                next_task = replace(
                    deferred_gate,
                    task_id=(
                        f"exploration-workspace-yield:{question.id}:"
                        f"{stable_hash([manifest_id, deferred_gate.task_id])[:8]}"
                    ),
                    inputs=deferred_inputs,
                )
                observation_type = (
                    "exploratory_simulation_workspace_yield_to_metric_protocol"
                )
                summary = (
                    "The bounded model-owned simulation workspace did not produce "
                    "accepted code. Its non-confirmatory observations remain visible "
                    "while the existing metric-protocol gate resumes."
                )
                simulation_rationale = summary
                result_status = "REROUTE"
            else:
                next_task = None
                observation_type = "simulation_workspace_blocked"
                summary = (
                    "The model-owned simulation workspace ended without accepted "
                    "source after its direct execution-feedback budget. The exact "
                    "artifact remains failed without an Architect routing loop."
                )
                simulation_rationale = summary
                result_status = "BLOCKED"
            observations.append(
                EnvironmentObservation(
                    observation_type=observation_type,
                    summary=summary,
                    payload={
                        "simulation_manifest_id": manifest_id,
                        "failure_classification": (
                            generated_simulation_failure_classification
                        ),
                        "next_owner_subsystem": (
                            next_task.owner_subsystem
                            if next_task is not None
                            else ""
                        ),
                        "n_open_implementation_gaps": len(implementation_gaps),
                        "runtime_edited_source": False,
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                )
            )
            return AgentStepResult(
                status=result_status,
                rationale=simulation_rationale,
                produced_artifacts=produced_artifacts,
                observations=tuple(observations),
                tool_calls=(
                    *registered_simulator_tool_calls,
                    *generated_simulation_tool_calls,
                ),
                evidence_entries=tuple(
                    row
                    for row in (
                        proposal_evidence,
                        evidence,
                    )
                    if row is not None
                ),
                next_task=next_task,
                failure_classification=generated_simulation_failure_classification,
            )
        generated_algorithm_sandbox_manifest_id = ""
        if implementation_gaps and requires_generated_algorithm_code:
            generated_algorithm_sandbox_manifest_id = (
                _runtime_generated_algorithm_sandbox_passed_manifest_id(
                    blackboard,
                    question_id=question.id,
                    theory_packet_id=packet_id,
                    required_estimator_ids=_implementation_gap_estimator_ids(
                        implementation_gaps
                    ),
                )
            )
        if implementation_gaps:
            if generated_algorithm_sandbox_manifest_id:
                observations.append(
                    EnvironmentObservation(
                        observation_type=(
                            "implementation_gap_covered_by_generated_algorithm_sandbox"
                        ),
                        summary=(
                            "Implementation gaps remain unregistered production "
                            "adapters, but capability-eval generated algorithm "
                            "sandbox evidence already passed for the gap ids."
                        ),
                        payload={
                            "implementation_gaps": implementation_gaps,
                            "algorithm_sandbox_manifest_id": (
                                generated_algorithm_sandbox_manifest_id
                            ),
                            "boundary": (
                                "Generated algorithm sandbox evidence is executable "
                                "engineering evidence only; it is not production "
                                "registration and not theorem proof evidence."
                            ),
                        },
                    )
                )
            else:
                observations.append(
                    EnvironmentObservation(
                        observation_type="implementation_gap",
                        summary=(
                            "LLM estimator specs are not yet executable registered "
                            "algorithms."
                        ),
                        payload={"implementation_gaps": implementation_gaps},
                    )
                )
        if simulation_passed:
            deferred_metric_protocol_payload = task.inputs.get(
                "deferred_metric_protocol_task", {}
            )
            if (
                exploratory_diagnostic
                and isinstance(deferred_metric_protocol_payload, Mapping)
                and deferred_metric_protocol_payload
            ):
                next_task = _agent_task_from_runtime_payload(
                    deferred_metric_protocol_payload
                )
            elif implementation_gaps and not generated_algorithm_sandbox_manifest_id:
                next_task = AgentTask(
                    task_id=f"algorithm:{question.id}:{stable_hash([packet_id, manifest_id])[:8]}",
                    owner_subsystem="AlgorithmEngineer",
                    objective=(
                        "Build and run sandbox prototypes for LLM estimator specs "
                        "that do not yet have registered executable algorithms."
                    ),
                    inputs={
                        "question": _question_to_payload(question),
                        "theory_packet_id": packet_id,
                        "simulation_manifest_id": manifest_id,
                        "implementation_gaps": implementation_gaps,
                        "n_runs": n_runs,
                        "seed": seed,
                        "architect_context": effective_context,
                    },
                    allowed_tools=("python", "filesystem_sandbox"),
                    expected_artifacts=_architect_expected_artifacts(
                        effective_context,
                        "AlgorithmEngineer",
                        ("algorithm_sandbox_manifest",),
                    ),
                    acceptance_gate=_architect_acceptance_gate(
                        effective_context,
                        "AlgorithmEngineer",
                        "sandbox prototype executed or explicit unsupported-prototype gap recorded",
                    ),
                    stop_condition="algorithm sandbox feedback recorded",
                )
            else:
                next_task = _post_empirical_evidence_task(
                    question=question,
                    packet_id=packet_id,
                    simulation_manifest_id=manifest_id,
                    algorithm_sandbox_manifest_id=(
                        generated_algorithm_sandbox_manifest_id
                    ),
                    architect_context=effective_context,
                )
            semantic_review_evidence: EvidenceLedgerEntry | None = None
            if self.semantic_reviewer_available:
                semantic_review_dispatch = (
                    _runtime_generated_code_semantic_review_dispatch(
                        task=task,
                        question=question,
                        source_subsystem="SimulationEvaluator",
                        source_manifest=manifest,
                        theory_packet=(
                            packet if isinstance(packet, Mapping) else {}
                        ),
                        proposal_packet=proposal_packet,
                        architect_context=effective_context,
                        deferred_next_task=next_task,
                        blackboard_artifacts=blackboard.artifacts,
                        max_revisions=self.semantic_review_max_revisions,
                    )
                )
                if semantic_review_dispatch is not None:
                    produced_artifacts.update(
                        {
                            str(artifact_id): artifact
                            for artifact_id, artifact in dict(
                                semantic_review_dispatch.get("artifacts", {})
                            ).items()
                        }
                    )
                    observations.append(semantic_review_dispatch["observation"])
                    semantic_review_evidence = semantic_review_dispatch["evidence"]
                    next_task = semantic_review_dispatch["next_task"]
            return AgentStepResult(
                status="REROUTE",
                rationale=(
                    "Runtime recorded non-promotable exploratory diagnostics and is "
                    "routing to the independent confirmatory metric-protocol gate."
                    if exploratory_diagnostic
                    else "Runtime recorded executable simulation feedback and is routing "
                    "remaining implementation/formalization feedback through the agent runtime."
                ),
                produced_artifacts=produced_artifacts,
                observations=tuple(observations),
                tool_calls=(
                    *registered_simulator_tool_calls,
                    *generated_simulation_tool_calls,
                ),
                evidence_entries=tuple(
                    row
                    for row in (
                        proposal_evidence,
                        evidence,
                        semantic_review_evidence,
                    )
                    if row is not None
                ),
                next_task=next_task,
            )
        feedback = {
            "simulation_manifest_id": manifest_id,
            "simulation_passed": simulation_passed,
            "failed_simulations": [
                _simulation_to_json(row)
                for row in simulations
                if not row.passed
            ],
            "implementation_gaps": implementation_gaps,
            "boundary": SIMULATION_NOT_PROOF_BOUNDARY,
        }
        revision_context = dict(context)
        revision_context["previous_theory_packet_id"] = packet_id
        revision_context["environment_feedback"] = feedback
        next_task = AgentTask(
            task_id=f"simulation-replan:{question.id}:{stable_hash(feedback)[:8]}",
            owner_subsystem="ArchitectCoordinator",
            objective=(
                "Choose the next subsystem from the complete simulation candidate "
                "and raw execution observations."
            ),
            inputs={
                "question": _question_to_payload(question),
                "architect_context": revision_context,
                "environment_feedback": feedback,
                "runtime_architect_operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
            },
            expected_artifacts=("architect_feedback_route_decision",),
            acceptance_gate="Architect packet selects a feasible next subsystem",
            stop_condition="Architect replans or classifies a blocker",
        )
        return AgentStepResult(
            status="REROUTE",
            rationale=(
                "Simulation did not pass; the runtime is returning the complete "
                "observations to ArchitectCoordinator without assigning a fixed "
                "theory or coding owner."
            ),
            produced_artifacts=produced_artifacts,
            observations=tuple(observations),
            tool_calls=(
                *registered_simulator_tool_calls,
                *generated_simulation_tool_calls,
            ),
            evidence_entries=tuple(row for row in (proposal_evidence, evidence) if row is not None),
            next_task=next_task,
            failure_classification="simulation_diagnostic_failure",
        )


class AlgorithmEngineerRuntimeSubsystem:
    name = "AlgorithmEngineer"

    def __init__(
        self,
        *,
        out_dir: Path,
        n_runs: int,
        seed: int,
        proposal_agent: LLMAlgorithmEngineerAgent | None = None,
        timeout_s: int = 60,
        semantic_reviewer_available: bool = False,
        semantic_review_max_revisions: int = 1,
    ) -> None:
        self.out_dir = out_dir
        self.n_runs = n_runs
        self.seed = seed
        self.proposal_agent = proposal_agent
        self.timeout_s = timeout_s
        self.semantic_reviewer_available = bool(semantic_reviewer_available)
        self.semantic_review_max_revisions = max(
            0,
            int(semantic_review_max_revisions or 0),
        )

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        implementation_before_metric_freeze = bool(
            task.inputs.get("implementation_before_metric_freeze") is True
        )
        deferred_metric_protocol_payload = task.inputs.get(
            "deferred_metric_protocol_task", {}
        )
        pre_metric_contract_errors: list[str] = []
        if implementation_before_metric_freeze:
            if str(task.inputs.get("empirical_evaluation_phase", "") or "") != (
                EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            ):
                pre_metric_contract_errors.append(
                    "pre-metric implementation must be exploratory"
                )
            if not isinstance(deferred_metric_protocol_payload, Mapping):
                pre_metric_contract_errors.append(
                    "pre-metric implementation requires a deferred Architect task"
                )
                deferred_metric_protocol_payload = {}
            if str(
                deferred_metric_protocol_payload.get("owner_subsystem", "") or ""
            ) != "ArchitectCoordinator":
                pre_metric_contract_errors.append(
                    "pre-metric deferred task must be owned by ArchitectCoordinator"
                )
            deferred_inputs = deferred_metric_protocol_payload.get("inputs", {})
            if not isinstance(deferred_inputs, Mapping) or str(
                deferred_inputs.get("runtime_architect_operation", "") or ""
            ) != RUNTIME_ARCHITECT_OPERATION_POST_IMPLEMENTATION_METRIC:
                pre_metric_contract_errors.append(
                    "pre-metric deferred task must request post-implementation "
                    "metric authoring"
                )
            metric_gate = context.get("architect_metric_protocol_gate", {})
            if not (
                isinstance(metric_gate, Mapping)
                and metric_gate.get("algorithm_execution_authorized") is True
                and metric_gate.get("confirmatory_simulation_authorized") is False
                and str(metric_gate.get("preflight_acceptance_id", "") or "")
            ):
                pre_metric_contract_errors.append(
                    "pre-metric implementation requires a preflight-bound "
                    "implementation-only gate"
                )
        if pre_metric_contract_errors:
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "AlgorithmEngineer rejected an ambiguous pre-metric execution "
                    "request before any model or sandbox call."
                ),
                observations=(
                    EnvironmentObservation(
                        observation_type=(
                            "algorithm_pre_metric_execution_contract_rejected"
                        ),
                        summary="; ".join(pre_metric_contract_errors)[:500],
                        payload={
                            "validation_errors": pre_metric_contract_errors,
                            "model_call_authorized": False,
                            "execution_authorized": False,
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                failure_classification=(
                    "algorithm_pre_metric_execution_contract_invalid"
                ),
            )
        environment_feedback: Mapping[str, Any] = (
            task.inputs.get("environment_feedback", {})
            if isinstance(task.inputs.get("environment_feedback", {}), Mapping)
            else {}
        )
        effective_context = _runtime_context_with_environment_feedback_contract(
            context,
            environment_feedback,
            subsystem="AlgorithmEngineer",
        )
        algorithm_control = _architect_control_payload(context, "AlgorithmEngineer")
        packet_id = str(task.inputs.get("theory_packet_id", ""))
        packet = blackboard.artifacts.get(packet_id, {})
        runtime_theory_trace_contract = _runtime_theory_trace_consumption_contract(
            consumer_subsystem="AlgorithmEngineer",
            source_theory_packet_id=packet_id,
            theory_packet=packet if isinstance(packet, Mapping) else {},
        )
        simulation_manifest_id = str(task.inputs.get("simulation_manifest_id", ""))
        simulation_manifest = blackboard.artifacts.get(simulation_manifest_id, {})
        if not implementation_before_metric_freeze:
            missing_simulation_result = (
                _runtime_missing_simulation_handoff_result_if_needed(
                    source_subsystem="AlgorithmEngineer",
                    task=task,
                    question=question,
                    simulation_manifest_id=simulation_manifest_id,
                    simulation_manifest=simulation_manifest,
                )
            )
            if missing_simulation_result is not None:
                return missing_simulation_result
        implementation_gaps = [
            row for row in task.inputs.get("implementation_gaps", []) or [] if isinstance(row, Mapping)
        ]
        source_revision_artifact_ids = [
            str(value or "").strip()
            for value in task.inputs.get("source_revision_artifact_ids", []) or []
            if str(value or "").strip()
        ]
        consumer_continuation_ref = task.inputs.get(
            "deferred_consumer_task_continuation_ref",
            {},
        )
        consumer_revision_mode = bool(
            source_revision_artifact_ids or consumer_continuation_ref
        )
        consumer_revision_budget = task.budget.get(
            SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY,
            {},
        )
        if not isinstance(consumer_revision_budget, Mapping):
            consumer_revision_budget = {}
        consumer_source_manifest: dict[str, Any] = {}
        consumer_source_rows_by_id: dict[str, dict[str, Any]] = {}
        deferred_consumer_task: AgentTask | None = None
        proposal_packet: dict[str, Any] | None = None
        proposal_evidence: EvidenceLedgerEntry | None = None
        algorithm_theory_trace_contract: dict[str, Any] = {}
        algorithm_theory_trace_alignment_contract: dict[str, Any] = {}
        produced_artifacts: dict[str, Any] = {}
        observations: list[EnvironmentObservation] = []
        if consumer_revision_mode:
            consumer_errors: list[str] = []
            if not self.semantic_reviewer_available:
                consumer_errors.append(
                    "revised dependency source requires independent semantic review"
                )
            if not (
                self.proposal_agent is not None
                and callable(
                    getattr(self.proposal_agent, "iterate_code_with_tools", None)
                )
                and callable(
                    getattr(
                        getattr(self.proposal_agent, "provider", None),
                        "generate_client_tool_turn",
                        None,
                    )
                )
            ):
                consumer_errors.append(
                    "AlgorithmEngineer source workspace is unavailable"
                )
            source_owner = environment_feedback.get("consumer_source_owner", {})
            if not isinstance(source_owner, Mapping):
                source_owner = {}
            source_manifest_id = str(
                source_owner.get("source_manifest_id", "") or ""
            ).strip()
            raw_source_manifest = task.inputs.get(
                "consumer_source_manifest",
                {},
            )
            if isinstance(raw_source_manifest, Mapping):
                consumer_source_manifest = dict(raw_source_manifest)
            consumer_source_rows_by_id, source_errors = (
                scientific_consumer_revision_sources(
                    consumer_source_manifest,
                    dependency_context=source_owner,
                    revision_artifact_ids=source_revision_artifact_ids,
                    implementation_artifact_ids=[
                        str(row.get("estimator_id", "") or "").strip()
                        for row in implementation_gaps
                    ],
                    theory_packet_id=packet_id,
                )
            )
            consumer_errors.extend(source_errors)
            if (
                not isinstance(consumer_continuation_ref, Mapping)
                or not consumer_continuation_ref
            ):
                consumer_errors.append(
                    "scientific consumer continuation reference is missing"
                )
            try:
                deferred_consumer_task = restore_agent_task_continuation_reference(
                    consumer_continuation_ref,
                    blackboard.artifacts,
                )
            except ValueError as exc:
                consumer_errors.append(str(exc))
            else:
                deferred_resume_manifest = deferred_consumer_task.inputs.get(
                    "consumer_resume_manifest",
                    {},
                )
                deferred_resume_manifest_id = (
                    str(deferred_resume_manifest.get("artifact_id", "") or "")
                    if isinstance(deferred_resume_manifest, Mapping)
                    and deferred_resume_manifest.get("artifact_kind")
                    == "RuntimeArtifactRef"
                    else str(
                        deferred_resume_manifest.get("manifest_id", "") or ""
                    )
                    if isinstance(deferred_resume_manifest, Mapping)
                    else ""
                )
                if (
                    deferred_consumer_task.owner_subsystem != "SimulationEvaluator"
                    or deferred_consumer_task.budget != task.budget
                    or deferred_resume_manifest_id != simulation_manifest_id
                ):
                    consumer_errors.append(
                        "deferred scientific consumer continuation does not match "
                        "the current revision lineage"
                    )
            prior_proposal_id = str(
                consumer_source_manifest.get(
                    "llm_algorithm_engineer_proposal_id",
                    "",
                )
                or ""
            ).strip()
            prior_proposal = blackboard.artifacts.get(prior_proposal_id, {})
            if (
                not isinstance(prior_proposal, Mapping)
                or str(prior_proposal.get("packet_id", "") or "")
                != prior_proposal_id
            ):
                consumer_errors.append(
                    "parent AlgorithmEngineer proposal artifact is missing"
                )
            else:
                proposal_packet = dict(prior_proposal)
            if consumer_errors:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "AlgorithmEngineer rejected a stale scientific consumer "
                        "backedge before any planning, source, or sandbox call."
                    ),
                    observations=(
                        EnvironmentObservation(
                            observation_type="scientific_consumer_backedge_rejected",
                            summary="; ".join(sorted(set(consumer_errors)))[:500],
                            payload={
                                "validation_errors": sorted(set(consumer_errors)),
                                "source_revision_artifact_ids": (
                                    source_revision_artifact_ids
                                ),
                                "planning_model_call_authorized": False,
                                "source_model_call_authorized": False,
                                "runtime_edited_source": False,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    failure_classification="scientific_consumer_lineage_invalid",
                )
            theory_trace_contracts = _runtime_theory_trace_consumption_contracts(
                proposal_packet or {}
            )
            algorithm_theory_trace_contract = (
                theory_trace_contracts[0] if theory_trace_contracts else {}
            )
            algorithm_theory_trace_alignment_contract = dict(
                (proposal_packet or {}).get(
                    "theory_trace_alignment_contract",
                    {},
                )
                or {}
            )
            observations.append(
                EnvironmentObservation(
                    observation_type="algorithm_consumer_source_workspace_resumed",
                    summary=(
                        "AlgorithmEngineer will revise only the hash-bound dependency "
                        "sources named by the failed consumer observation."
                    ),
                    payload={
                        "source_manifest_id": source_manifest_id,
                        "source_revision_artifact_ids": (
                            source_revision_artifact_ids
                        ),
                        "deferred_consumer_task_ref": agent_task_reference(
                            deferred_consumer_task
                        ),
                        "planning_model_call_used": False,
                        "runtime_edited_source": False,
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                )
            )
        elif self.proposal_agent is not None and implementation_gaps:
            try:
                effective_context = _runtime_context_with_environment_feedback_contract(
                    context,
                    environment_feedback,
                    subsystem="AlgorithmEngineer",
                )
                with agent_runtime_substage("algorithm_planning_envelope"):
                    proposal_packet = self.proposal_agent.propose(
                        question=question,
                        theory_packet=(
                            packet if isinstance(packet, Mapping) else {}
                        ),
                        simulation_manifest=(
                            simulation_manifest
                            if isinstance(simulation_manifest, Mapping)
                            else {}
                        ),
                        implementation_gaps=implementation_gaps,
                        environment_feedback=(
                            _runtime_environment_feedback_with_architect_directive(
                                context=effective_context,
                                subsystem="AlgorithmEngineer",
                                feedback=environment_feedback,
                            )
                        ),
                    )
            except PacketValidationError as exc:
                return _algorithm_engineer_packet_validation_failure_result(
                    task=task,
                    question=question,
                    theory_packet_id=packet_id,
                    simulation_manifest_id=simulation_manifest_id,
                    implementation_gaps=implementation_gaps,
                    exc=exc,
                )
            proposal_id = str(proposal_packet["packet_id"])
            theory_trace_contracts = _runtime_theory_trace_consumption_contracts(
                proposal_packet
            )
            algorithm_theory_trace_contract = (
                theory_trace_contracts[0] if theory_trace_contracts else {}
            )
            algorithm_theory_trace_alignment_contract = (
                dict(proposal_packet.get("theory_trace_alignment_contract", {}))
                if isinstance(
                    proposal_packet.get("theory_trace_alignment_contract", {}),
                    Mapping,
                )
                else {}
            )
            produced_artifacts[proposal_id] = proposal_packet
            observations.append(
                EnvironmentObservation(
                    observation_type="llm_algorithm_engineer_proposal",
                    summary=(
                        "validated LLM AlgorithmEngineer proposal recorded before "
                        "runtime sandbox execution"
                    ),
                    payload={
                        "packet_id": proposal_id,
                        "n_implementation_targets": len(
                            proposal_packet.get("implementation_targets", []) or []
                        ),
                        "execution_evidence_status": ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
                        "runtime_theory_trace_consumption_contract": runtime_theory_trace_contract,
                        "theory_trace_consumption_contract": algorithm_theory_trace_contract,
                        "theory_trace_alignment_contract": algorithm_theory_trace_alignment_contract,
                    },
                )
            )
            proposal_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proposal_id])[:20],
                task_id=task.task_id,
                artifact_id=proposal_id,
                evidence_type="llm_algorithm_engineer_proposal",
                status="PROPOSAL_RECORDED_REQUIRES_SANDBOX",
                boundary=ALGORITHM_ENGINEER_BOUNDARY,
                payload={
                    "n_implementation_targets": len(
                        proposal_packet.get("implementation_targets", []) or []
                    ),
                    "sandbox_executed": False,
                    "production_registered": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    "runtime_theory_trace_consumption_contract": runtime_theory_trace_contract,
                    "theory_trace_consumption_contract": algorithm_theory_trace_contract,
                    "theory_trace_alignment_contract": algorithm_theory_trace_alignment_contract,
                },
            )
        sandbox_dir = self.out_dir / _safe_identifier(question.id) / stable_hash([task.task_id, packet_id])[:12]
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        if consumer_revision_mode:
            reused_prototype_rows = []
            for estimator_id, source_row in consumer_source_rows_by_id.items():
                if estimator_id in source_revision_artifact_ids:
                    continue
                reused_row = deepcopy(source_row)
                reused_row["prototype_status"] = "REUSED_REVIEWED_SOURCE"
                reused_row["source_reused_without_execution"] = True
                reused_row["source_reuse_lineage"] = {
                    "parent_manifest_id": str(
                        consumer_source_manifest.get("manifest_id", "") or ""
                    ),
                    "parent_manifest_hash": stable_hash(consumer_source_manifest),
                    "parent_script_hash": str(
                        source_row.get("script_hash", "") or ""
                    ),
                    "runtime_edited_source": False,
                    "proof_evidence_status": "SOURCE_REUSE_NOT_PROOF_EVIDENCE",
                }
                reused_prototype_rows.append(reused_row)
            execution_gaps = [
                row
                for row in implementation_gaps
                if str(row.get("estimator_id", "") or "")
                in source_revision_artifact_ids
            ]
        else:
            reused_prototype_rows = []
            execution_gaps = implementation_gaps
        prototype_rows: list[dict[str, Any]] = list(reused_prototype_rows)
        tool_calls: list[ToolCallRecord] = []
        requires_generated_algorithm_code = _runtime_requires_generated_algorithm_code(
            effective_context,
            environment_feedback,
        )
        for gap in execution_gaps:
            estimator_id = str(gap.get("estimator_id", ""))
            spec = _estimator_spec(packet, estimator_id)
            proposal_target = _algorithm_proposal_for_estimator(proposal_packet, estimator_id)
            external_initial_observation: dict[str, Any] | None = None
            if consumer_revision_mode:
                parent_source_row = consumer_source_rows_by_id.get(
                    estimator_id,
                    {},
                )
                code_draft, parent_source_errors = (
                    complete_scientific_source_draft(parent_source_row)
                )
                if parent_source_errors:
                    code_draft = {}
                external_initial_observation = {
                    "artifact_kind": "ScientificConsumerExecutionObservation",
                    "source_manifest_id": str(
                        consumer_source_manifest.get("manifest_id", "") or ""
                    ),
                    "source_artifact_id": estimator_id,
                    "source_artifact_hash": str(
                        parent_source_row.get("script_hash", "") or ""
                    ),
                    "consumer_observations": deepcopy(
                        list(
                            (
                                environment_feedback.get(
                                    "consumer_source_owner",
                                    {},
                                )
                                or {}
                            ).get(
                                "consumer_observations_by_dependency",
                                {},
                            ).get(estimator_id, [])
                            or []
                        )
                    ),
                    "runtime_selected_source_edit": False,
                    "proof_evidence_status": (
                        "SCIENTIFIC_CONSUMER_OBSERVATION_NOT_PROOF_EVIDENCE"
                    ),
                }
            else:
                code_draft = _algorithm_code_draft_for_estimator(
                    proposal_packet,
                    estimator_id,
                )
            if code_draft:
                execution_kwargs = {
                    "sandbox_dir": sandbox_dir,
                    "estimator_id": estimator_id,
                    "spec": spec,
                    "metric_contracts": (),
                    "validation_context": {
                        "question": _question_to_payload(question),
                        "architect_context": effective_context,
                        "environment_feedback": dict(environment_feedback),
                        "implementation_gap": dict(gap),
                    },
                    "n_runs": int(
                        task.inputs.get("n_runs", self.n_runs) or self.n_runs
                    ),
                    "seed": int(task.inputs.get("seed", self.seed) or self.seed),
                    "timeout_s": self.timeout_s,
                    "required_callable_exports": ("run_estimator",),
                }
                prototype, source_tool_calls = (
                    _run_source_owner_scientific_workspace(
                        proposal_agent=self.proposal_agent,
                        question=question,
                        artifact_id=f"{question.id}:{estimator_id}",
                        code_draft=code_draft,
                        source_deferred=(
                            not consumer_revision_mode
                            and _proposal_defers_scientific_source(proposal_packet)
                        ),
                        workspace_context={
                            "theory_packet_id": packet_id,
                            "simulation_manifest_id": simulation_manifest_id,
                            "implementation_gap": dict(gap),
                            "estimator_spec": dict(spec),
                            "required_callable_exports": [
                                "run_estimator",
                                "run_sandbox",
                            ],
                            "run_estimator_contract": (
                                "run_estimator(request: dict) returns one named "
                                "JSON-finite object matching estimator_spec"
                            ),
                            "run_sandbox_contract": (
                                "run_sandbox(seed: int, replicates: int) returns "
                                "named JSON-finite smoke diagnostics and exercises "
                                "run_estimator"
                            ),
                            "consumer_execution_observation": (
                                external_initial_observation or {}
                            ),
                        },
                        execute_candidate=lambda candidate: (
                            _run_generated_code_sandbox(
                                code_draft=candidate,
                                **execution_kwargs,
                            )
                        ),
                        failure_identity={
                            "estimator_id": estimator_id,
                            "executor": "generated_python_sandbox",
                            "spec": dict(spec),
                        },
                        external_initial_observation=(
                            external_initial_observation
                        ),
                    )
                )
                tool_calls.extend(source_tool_calls)
                prototype["llm_algorithm_engineer_target"] = proposal_target
                prototype_rows.append(
                    _annotate_generated_sandbox_prototype_provenance(
                        prototype,
                        proposal_packet=proposal_packet,
                        source_feedback=environment_feedback,
                    )
                )
            else:
                prototype_rows.append(
                    _annotate_generated_sandbox_prototype_provenance(
                        {
                            "estimator_id": estimator_id,
                            "prototype_status": "MODEL_CODE_REQUIRED_BUT_MISSING",
                            "executor": "generated_python_sandbox",
                            "spec": dict(spec),
                            "reason": (
                                "AlgorithmEngineer did not return a complete executable "
                                "sandbox_code_drafts entry for this estimator. AgentRuntime "
                                "does not substitute registered or handwritten source."
                            ),
                            "promotion_ready": False,
                            "llm_algorithm_engineer_target": proposal_target,
                        },
                        proposal_packet=proposal_packet,
                        source_feedback=environment_feedback,
                    )
                )
        if consumer_revision_mode:
            estimator_order = {
                str(row.get("estimator_id", "") or ""): index
                for index, row in enumerate(implementation_gaps)
            }
            prototype_rows.sort(
                key=lambda row: estimator_order.get(
                    str(row.get("estimator_id", "") or ""),
                    len(estimator_order),
                )
            )
        n_generated_code_execution_attempted = sum(
            1
            for row in prototype_rows
            if row.get("executor") == "generated_python_sandbox"
            and _generated_sandbox_row_execution_attempted(row)
        )
        n_live_generated_code_execution_attempted = sum(
            1
            for row in prototype_rows
            if row.get("executor") == "generated_python_sandbox"
            and _generated_sandbox_row_execution_attempted(row)
            and _generated_sandbox_row_live_generated(row)
        )
        n_generated_code_execution_failed = sum(
            1
            for row in prototype_rows
            if row.get("executor") == "generated_python_sandbox"
            and row.get("prototype_status") == "FAILED"
        )
        n_live_generated_code_execution_failed = sum(
            1
            for row in prototype_rows
            if row.get("executor") == "generated_python_sandbox"
            and row.get("prototype_status") == "FAILED"
            and _generated_sandbox_row_live_generated(row)
        )
        n_typed_metric_contracts_declared = sum(
            len(row.get("metric_contracts", []) or [])
            for row in prototype_rows
        )
        n_typed_metric_contracts_evaluated = sum(
            _generated_metric_contract_evaluation_count(row, "n_contracts")
            for row in prototype_rows
        )
        n_typed_metric_contracts_passed = sum(
            _generated_metric_contract_evaluation_count(row, "n_passed")
            for row in prototype_rows
        )
        n_typed_metric_contracts_failed = sum(
            _generated_metric_contract_evaluation_count(row, "n_failed")
            for row in prototype_rows
        )
        manifest_id = "algorithm_sandbox_manifest:" + stable_hash([task.task_id, prototype_rows])[:20]
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeAlgorithmSandboxManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "empirical_evaluation_phase": str(
                task.inputs.get("empirical_evaluation_phase", "") or ""
            ),
            "implementation_before_metric_freeze": (
                implementation_before_metric_freeze
            ),
            "full_metric_authoring_completed": bool(
                not implementation_before_metric_freeze
                and isinstance(
                    algorithm_control.get("evidence_contract", {}), Mapping
                )
                and algorithm_control.get("evidence_contract", {}).get(
                    "empirical_metric_protocol_phase"
                )
                == METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED
                and algorithm_control.get("evidence_contract", {}).get(
                    "metric_protocol_execution_authorized"
                )
                is True
            ),
            "runtime_architect_control": algorithm_control,
            "theory_trace_consumption_contract": runtime_theory_trace_contract,
            "llm_algorithm_engineer_proposal_id": (
                str(proposal_packet.get("packet_id", "")) if proposal_packet else ""
            ),
            "llm_algorithm_engineer_theory_trace_consumption_contract": (
                algorithm_theory_trace_contract
            ),
            "llm_algorithm_engineer_theory_trace_alignment_contract": (
                algorithm_theory_trace_alignment_contract
            ),
            "consumer_source_revision": consumer_revision_mode,
            "consumer_parent_algorithm_manifest_id": str(
                consumer_source_manifest.get("manifest_id", "") or ""
            ),
            "consumer_parent_algorithm_manifest_hash": (
                stable_hash(consumer_source_manifest)
                if consumer_source_manifest
                else ""
            ),
            "consumer_source_revision_artifact_ids": (
                source_revision_artifact_ids
            ),
            "n_consumer_source_artifacts_revised": (
                len(source_revision_artifact_ids)
                if consumer_revision_mode
                else 0
            ),
            "n_consumer_source_artifacts_reused": (
                len(reused_prototype_rows)
                if consumer_revision_mode
                else 0
            ),
            "consumer_source_revision_lineage_id": str(
                consumer_revision_budget.get("lineage_id", "") or ""
            ),
            "prototypes": prototype_rows,
            "n_prototypes": len(prototype_rows),
            "n_executed": sum(
                1
                for row in prototype_rows
                if row.get("prototype_status") in {"EXECUTED", "FAILED_METRIC_GATE"}
            ),
            "n_passed": sum(1 for row in prototype_rows if row.get("smoke_passed") is True),
            "n_metric_gate_failed": sum(
                1
                for row in prototype_rows
                if row.get("prototype_status") == "FAILED_METRIC_GATE"
            ),
            "n_generated_code_executed": sum(
                1
                for row in prototype_rows
                if row.get("executor") == "generated_python_sandbox"
                and _generated_sandbox_row_executed(row)
            ),
            "n_generated_code_passed": sum(
                1
                for row in prototype_rows
                if row.get("executor") == "generated_python_sandbox"
                and row.get("smoke_passed") is True
            ),
            "n_live_generated_code_executed": sum(
                1
                for row in prototype_rows
                if row.get("executor") == "generated_python_sandbox"
                and _generated_sandbox_row_executed(row)
                and _generated_sandbox_row_live_generated(row)
            ),
            "n_generated_code_execution_attempted": (
                n_generated_code_execution_attempted
            ),
            "n_live_generated_code_execution_attempted": (
                n_live_generated_code_execution_attempted
            ),
            "n_generated_code_execution_failed": n_generated_code_execution_failed,
            "n_live_generated_code_execution_failed": (
                n_live_generated_code_execution_failed
            ),
            "n_live_generated_code_metric_gate_failed": sum(
                1
                for row in prototype_rows
                if row.get("executor") == "generated_python_sandbox"
                and row.get("prototype_status") == "FAILED_METRIC_GATE"
                and _generated_sandbox_row_live_generated(row)
            ),
            "n_unsafe_generated_code_rejected": sum(
                1
                for row in prototype_rows
                if row.get("prototype_status") == "REJECTED_UNSAFE_GENERATED_CODE"
            ),
            "n_live_unsafe_generated_code_rejected": sum(
                1
                for row in prototype_rows
                if row.get("prototype_status") == "REJECTED_UNSAFE_GENERATED_CODE"
                and _generated_sandbox_row_live_generated(row)
            ),
            "n_typed_metric_contracts_declared": n_typed_metric_contracts_declared,
            "n_typed_metric_contracts_evaluated": n_typed_metric_contracts_evaluated,
            "n_typed_metric_contracts_passed": n_typed_metric_contracts_passed,
            "n_typed_metric_contracts_failed": n_typed_metric_contracts_failed,
            "confirmatory_empirical_evidence_eligible": False,
            "generated_code_semantic_reviewer_available": (
                self.semantic_reviewer_available
            ),
            "generated_code_semantic_review_pending": bool(
                self.semantic_reviewer_available
                and any(
                    row.get("executor") == "generated_python_sandbox"
                    and (
                        row.get("smoke_passed") is True
                        or row.get("execution_smoke_passed") is True
                    )
                    for row in prototype_rows
                )
            ),
            "typed_metric_contract_proof_evidence_status": (
                GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
            ),
            "promotion_ready": False,
            "boundary": (
                "Algorithm sandbox prototypes are executable engineering evidence. "
                "They are not registered production algorithms and are not theorem proof evidence."
            ),
        }
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="algorithm_sandbox",
            status="EXECUTED_SANDBOX_PROTOTYPES" if manifest["n_executed"] else "NO_EXECUTABLE_PROTOTYPE",
            boundary=str(manifest["boundary"]),
            payload={
                "n_prototypes": manifest["n_prototypes"],
                "n_executed": manifest["n_executed"],
                "n_passed": manifest["n_passed"],
                "n_generated_code_executed": manifest["n_generated_code_executed"],
                "n_generated_code_execution_attempted": manifest[
                    "n_generated_code_execution_attempted"
                ],
                "n_generated_code_execution_failed": manifest[
                    "n_generated_code_execution_failed"
                ],
                "n_generated_code_passed": manifest["n_generated_code_passed"],
                "n_generated_code_metric_gate_failed": manifest[
                    "n_metric_gate_failed"
                ],
                "n_live_generated_code_executed": manifest[
                    "n_live_generated_code_executed"
                ],
                "n_live_generated_code_execution_attempted": manifest[
                    "n_live_generated_code_execution_attempted"
                ],
                "n_live_generated_code_execution_failed": manifest[
                    "n_live_generated_code_execution_failed"
                ],
                "n_live_generated_code_metric_gate_failed": manifest[
                    "n_live_generated_code_metric_gate_failed"
                ],
                "n_unsafe_generated_code_rejected": manifest["n_unsafe_generated_code_rejected"],
                "n_typed_metric_contracts_evaluated": manifest[
                    "n_typed_metric_contracts_evaluated"
                ],
                "n_typed_metric_contracts_passed": manifest[
                    "n_typed_metric_contracts_passed"
                ],
                "n_typed_metric_contracts_failed": manifest[
                    "n_typed_metric_contracts_failed"
                ],
                "typed_metric_contract_proof_evidence_status": (
                    GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
                ),
                "promotion_ready": False,
                "architect_acceptance_gate": algorithm_control.get("acceptance_gate", ""),
            },
        )
        produced_artifacts[manifest_id] = manifest
        has_deferred_metric_protocol = bool(
            isinstance(deferred_metric_protocol_payload, Mapping)
            and deferred_metric_protocol_payload
        )
        revision_required = bool(
            self.proposal_agent is not None
            and implementation_gaps
            and (
                (
                    requires_generated_algorithm_code
                    and (
                        manifest["n_generated_code_executed"] == 0
                        or manifest["n_unsafe_generated_code_rejected"] > 0
                        or (
                            manifest["n_generated_code_executed"] > 0
                            and manifest["n_passed"] == 0
                        )
                    )
                )
                or manifest["n_executed"] == 0
                or (
                    manifest["n_generated_code_executed"] > 0
                    and manifest["n_passed"] == 0
                )
            )
        )
        manifest["generated_code_semantic_review_pending"] = bool(
            manifest.get("generated_code_semantic_review_pending")
            and not revision_required
        )
        revision_failure_classification = (
            "scientific_consumer_source_workspace_exhausted"
            if consumer_revision_mode
            else
            "generated_algorithm_sandbox_metric_gate_failed"
            if int(manifest.get("n_metric_gate_failed", 0) or 0) > 0
            else "generated_algorithm_typed_metric_contract_missing"
            if any(
                row.get("prototype_status")
                == "TYPED_METRIC_CONTRACT_REQUIRED_BUT_MISSING"
                for row in prototype_rows
            )
            else "generated_algorithm_sandbox_execution_failed"
            if int(manifest.get("n_generated_code_execution_failed", 0) or 0) > 0
            else "generated_algorithm_sandbox_required_not_executed"
            if requires_generated_algorithm_code
            and manifest["n_generated_code_executed"] == 0
            else "generated_algorithm_source_revision_required"
            if requires_generated_algorithm_code
            else "algorithm_sandbox_no_executable_prototype"
        )
        if revision_required:
            feedback = _algorithm_sandbox_revision_feedback(
                manifest=manifest,
                boundary=str(manifest["boundary"]),
                failure_classification=revision_failure_classification,
            )
            observations.append(
                EnvironmentObservation(
                    observation_type="algorithm_workspace_blocked",
                    summary=(
                        "The bounded model-owned algorithm workspace ended without "
                        "accepted source after its direct execution-feedback budget. "
                        "The exact artifact remains failed without an Architect "
                        "routing loop."
                    ),
                    payload={
                        "algorithm_sandbox_manifest_id": manifest_id,
                        "failure_classification": revision_failure_classification,
                        "complete_parent_source_supplied": all(
                            row.get("parent_source_complete") is True
                            for row in feedback.get("prototypes", [])
                            if isinstance(row, Mapping)
                        ),
                        "runtime_edited_source": False,
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                )
            )
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "AlgorithmEngineer exhausted its direct model-owned source and "
                    "execution-feedback loop without satisfying the sandbox gate."
                ),
                produced_artifacts=produced_artifacts,
                observations=tuple(observations),
                tool_calls=tuple(tool_calls),
                evidence_entries=tuple(
                    row
                    for row in (proposal_evidence, evidence)
                    if row is not None
                ),
                failure_classification=revision_failure_classification,
            )
        if consumer_revision_mode:
            assert deferred_consumer_task is not None
            next_task = deferred_consumer_task
        elif has_deferred_metric_protocol:
            deferred_gate = _agent_task_from_runtime_payload(
                deferred_metric_protocol_payload
            )
            deferred_inputs = dict(deferred_gate.inputs)
            deferred_context = dict(
                deferred_inputs.get("architect_context", {}) or {}
            )
            deferred_context["previous_algorithm_sandbox_manifest_id"] = manifest_id
            deferred_context["algorithm_sandbox_manifest_id"] = manifest_id
            deferred_context["implementation_gaps"] = implementation_gaps
            deferred_inputs["architect_context"] = deferred_context
            next_task = replace(
                deferred_gate,
                task_id=(
                    f"algorithm-accepted-metric-protocol:{question.id}:"
                    f"{stable_hash([manifest_id, deferred_gate.task_id])[:8]}"
                ),
                inputs=deferred_inputs,
            )
        else:
            next_task = _post_empirical_evidence_task(
                question=question,
                packet_id=packet_id,
                simulation_manifest_id=simulation_manifest_id,
                algorithm_sandbox_manifest_id=manifest_id,
                architect_context=effective_context,
            )
        semantic_review_evidence: EvidenceLedgerEntry | None = None
        if implementation_before_metric_freeze and not self.semantic_reviewer_available:
            observations.append(
                EnvironmentObservation(
                    observation_type=(
                        "algorithm_pre_metric_semantic_reviewer_unavailable"
                    ),
                    summary=(
                        "implementation recorded but deferred metric authoring "
                        "remains blocked without an independent semantic reviewer"
                    ),
                    payload={
                        "manifest_id": manifest_id,
                        "deferred_metric_authoring_released": False,
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                )
            )
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "Pre-metric implementation cannot release confirmatory metric "
                    "authoring without independent semantic review."
                ),
                produced_artifacts=produced_artifacts,
                observations=tuple(observations),
                tool_calls=tuple(tool_calls),
                evidence_entries=tuple(
                    row for row in (proposal_evidence, evidence) if row is not None
                ),
                failure_classification=(
                    "pre_metric_implementation_semantic_reviewer_unavailable"
                ),
            )
        if self.semantic_reviewer_available:
            semantic_review_dispatch = _runtime_generated_code_semantic_review_dispatch(
                task=task,
                question=question,
                source_subsystem="AlgorithmEngineer",
                source_manifest=manifest,
                theory_packet=packet if isinstance(packet, Mapping) else {},
                proposal_packet=proposal_packet,
                architect_context=effective_context,
                deferred_next_task=next_task,
                blackboard_artifacts=blackboard.artifacts,
                max_revisions=self.semantic_review_max_revisions,
            )
            if semantic_review_dispatch is not None:
                produced_artifacts.update(
                    {
                        str(artifact_id): artifact
                        for artifact_id, artifact in dict(
                            semantic_review_dispatch.get("artifacts", {})
                        ).items()
                    }
                )
                observations.append(semantic_review_dispatch["observation"])
                semantic_review_evidence = semantic_review_dispatch["evidence"]
                next_task = semantic_review_dispatch["next_task"]
            elif implementation_before_metric_freeze:
                observations.append(
                    EnvironmentObservation(
                        observation_type=(
                            "algorithm_pre_metric_semantic_review_not_dispatchable"
                        ),
                        summary=(
                            "no exact successful generated artifact was eligible "
                            "for independent semantic review"
                        ),
                        payload={
                            "manifest_id": manifest_id,
                            "deferred_metric_authoring_released": False,
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    )
                )
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "Pre-metric implementation did not produce an exact artifact "
                        "that could be independently reviewed."
                    ),
                    produced_artifacts=produced_artifacts,
                    observations=tuple(observations),
                    tool_calls=tuple(tool_calls),
                    evidence_entries=tuple(
                        row
                        for row in (proposal_evidence, evidence)
                        if row is not None
                    ),
                    failure_classification=(
                        "pre_metric_implementation_review_not_dispatchable"
                    ),
                )
        observations.append(
            EnvironmentObservation(
                observation_type="algorithm_sandbox_result",
                summary=(
                    f"prototypes={manifest['n_prototypes']} executed={manifest['n_executed']} "
                    f"passed={manifest['n_passed']} promotion_ready=false"
                ),
                payload={
                    "manifest_id": manifest_id,
                    "llm_algorithm_engineer_proposal_id": manifest["llm_algorithm_engineer_proposal_id"],
                    "n_prototypes": manifest["n_prototypes"],
                    "n_executed": manifest["n_executed"],
                    "n_passed": manifest["n_passed"],
                    "n_generated_code_executed": manifest["n_generated_code_executed"],
                    "n_generated_code_execution_attempted": manifest[
                        "n_generated_code_execution_attempted"
                    ],
                    "n_generated_code_execution_failed": manifest[
                        "n_generated_code_execution_failed"
                    ],
                    "n_unsafe_generated_code_rejected": manifest["n_unsafe_generated_code_rejected"],
                    "promotion_ready": False,
                },
            )
        )
        evidence_entries = [
            row
            for row in (
                proposal_evidence,
                evidence,
                semantic_review_evidence,
            )
            if row is not None
        ]
        if next_task.owner_subsystem == "SimulationEvaluator":
            algorithm_rationale = (
                "AlgorithmEngineer recorded sandbox executable feedback, but "
                "the capability-eval contract still requires generated "
                "simulation sandbox evidence before formalization."
            )
        elif (
            next_task.owner_subsystem
            == GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
        ):
            algorithm_rationale = (
                "AlgorithmEngineer executed the generated candidate and is routing "
                "its exact source, runtime arguments, and result to independent "
                "semantic review before any downstream acceptance."
            )
        else:
            algorithm_rationale = (
                "AlgorithmEngineer recorded sandbox executable feedback for unregistered "
                "LLM estimator specs and is routing to formalization/proof feedback."
            )
        return AgentStepResult(
            status="REROUTE",
            rationale=algorithm_rationale,
            produced_artifacts=produced_artifacts,
            observations=tuple(observations),
            tool_calls=tuple(tool_calls),
            evidence_entries=tuple(evidence_entries),
            next_task=next_task,
            failure_classification="",
        )


def _independent_semantic_review_architect_escalation_task(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    context: Mapping[str, Any],
    revision_feedback: Mapping[str, Any],
    source_artifact_id: str,
) -> AgentTask:
    """Escalate an independently reviewed cross-artifact semantic conflict."""

    failure_classification = str(
        revision_feedback.get("failure_classification", "") or ""
    )
    if (
        revision_feedback.get("feedback_source")
        != GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
        or failure_classification
        not in {
            "generated_code_semantic_review_lineage_budget_exhausted",
            "generated_code_semantic_review_requires_cross_artifact_resolution",
        }
    ):
        raise ValueError(
            "Architect escalation requires an independent semantic-review conflict "
            "with cross-artifact evidence"
        )
    replan_context = dict(context)
    replan_context.pop("environment_feedback", None)
    observation_artifact_id = str(
        revision_feedback.get("observation_id", "")
        or revision_feedback.get("feedback_id", "")
        or ""
    ).strip()
    if not observation_artifact_id:
        raise ValueError(
            "Architect escalation requires a content-addressed observation identity"
        )
    observation_ref = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeWorkspaceObservationRef",
        "feedback_type": "workspace_replan_observation_ref",
        "feedback_id": str(revision_feedback.get("feedback_id", "") or ""),
        "source_task_id": task.task_id,
        "source_subsystem": task.owner_subsystem,
        "source_artifact_id": source_artifact_id,
        "source_observation_hash": stable_hash(dict(revision_feedback)),
        "observation_artifact_ref": runtime_artifact_reference(
            observation_artifact_id,
            revision_feedback,
        ),
        "failure_classification": failure_classification,
        "unchanged_source_retry_authorized": False,
        "source_failure_classification": str(
            revision_feedback.get("source_failure_classification", "") or ""
        ),
        "validation_errors": [
            str(value)
            for value in revision_feedback.get("validation_errors", []) or []
            if str(value)
        ],
        "related_artifact_ids": {
            str(key): str(value)
            for key, value in revision_feedback.items()
            if str(key).endswith("_id")
            and key not in {"feedback_id", "source_task_id"}
            and isinstance(value, (str, int))
            and str(value)
        },
        "runtime_edits_candidate": False,
        "proof_evidence_status": str(
            revision_feedback.get("proof_evidence_status", "NOT_PROOF_EVIDENCE")
            or "NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "This compact control-plane reference identifies the immutable source "
            "artifact and failure class. AgentRuntime resolves the hash-bound, bounded "
            "reviewer observation for Architect, while complete source remains in the "
            "artifact store and Architect does not receive or author a patch."
        ),
    }
    replan_context["workspace_replan"] = {
        "artifact_kind": "RuntimeWorkspaceReplanContext",
        "source_task_id": task.task_id,
        "source_subsystem": task.owner_subsystem,
        "source_artifact_id": source_artifact_id,
        "source_artifact_ref": {
            "artifact_kind": "RuntimeArtifactRef",
            "artifact_id": source_artifact_id,
        },
        "feedback_id": str(observation_ref["feedback_id"]),
        "feedback_hash": stable_hash(dict(revision_feedback)),
        "failure_classification": failure_classification,
        "unchanged_source_retry_authorized": False,
        "implementation_gaps": [
            dict(row)
            for row in task.inputs.get("implementation_gaps", []) or []
            if isinstance(row, Mapping)
        ],
        "routing_contract": (
            "Select the next typed owner from the exact candidate and observations. "
            "Do not prescribe a source patch, invent statistical acceptance, treat "
            "a failed implementation as accepted, or use formalization progress to "
            "close the empirical blocker."
        ),
        "proof_evidence_status": (
            "SOURCE_WORKSPACE_REPLAN_NOT_PROOF_EVIDENCE"
        ),
    }
    return AgentTask(
        task_id=(
            f"architect-workspace-replan:{question.id}:"
            f"{stable_hash([task.task_id, source_artifact_id, revision_feedback])[:8]}"
        ),
        owner_subsystem="ArchitectCoordinator",
        objective=(
            "Resolve a cross-workspace semantic conflict independently established "
            "by source review."
        ),
        inputs={
            "question": _question_to_payload(question),
            "architect_context": replan_context,
            "environment_feedback": observation_ref,
            "runtime_architect_operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
        },
        allowed_tools=("model_backend", "evidence_ledger"),
        expected_artifacts=("architect_feedback_route_decision",),
        acceptance_gate=(
            "validated Architect proposal routes to an evidence-producing owner or "
            "records a typed blocker without weakening execution gates"
        ),
        stop_condition=(
            "amended route selects a theory, code, interface, or environment owner"
        ),
    )


def _formalizer_semantic_review_continuation_task(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    context: Mapping[str, Any],
    workspace_feedback: Mapping[str, Any],
    source_artifact_id: str,
) -> AgentTask:
    """Return independent target-review observations to the same Lean workspace."""

    continuation_context = dict(context)
    continuation_context["environment_feedback"] = deepcopy(
        dict(workspace_feedback)
    )
    continuation_inputs = dict(task.inputs)
    continuation_inputs.update(
        {
            "question": _question_to_payload(question),
            "architect_context": continuation_context,
            "environment_feedback": deepcopy(dict(workspace_feedback)),
        }
    )
    return replace(
        task,
        task_id=(
            f"formalizer-semantic-review-continuation:{question.id}:"
            f"{stable_hash([task.task_id, source_artifact_id, workspace_feedback])[:8]}"
        ),
        owner_subsystem="FormalizationEvaluator",
        objective=(
            "Continue the same model-owned Lean workspace from the exact source, "
            "raw Lean observations, and independent target-semantic review."
        ),
        inputs=continuation_inputs,
        allowed_tools=tuple(
            dict.fromkeys(
                (
                    *task.allowed_tools,
                    "model_backend",
                    "local_lean",
                    "lean_lsp_mcp",
                    "formal_source_retrieval",
                    "proof_search",
                )
            )
        ),
    )


def _simulation_engineer_packet_validation_failure_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    theory_packet_id: str,
    exc: PacketValidationError,
) -> AgentStepResult:
    architect_context = task.inputs.get("architect_context", {})
    if not isinstance(architect_context, Mapping):
        architect_context = {}
    empirical_evaluation_phase = str(
        task.inputs.get("empirical_evaluation_phase", "")
        or architect_context.get("empirical_evaluation_phase", "")
        or ""
    ).strip()
    validation_errors = [str(error) for error in exc.errors]
    failure_classification = "simulation_engineer_packet_validation_failed"
    failure_id = "simulation_engineer_validation_failure:" + stable_hash(
        [task.task_id, theory_packet_id, validation_errors, exc.history]
    )[:20]
    rejected_candidate = (
        deepcopy(dict(exc.last_invalid_packet))
        if isinstance(exc.last_invalid_packet, Mapping)
        else {}
    )
    regeneration_feedback = {
        "feedback_id": failure_id,
        "feedback_type": "simulation_engineer_packet_validation_feedback",
        "question_id": question.id,
        "source_theory_packet_id": theory_packet_id,
        "failure_classification": failure_classification,
        "validation_label": exc.validation_label,
        "validation_errors": validation_errors,
        "model_generation_attempt_history": deepcopy(exc.history),
        "last_attempt_summary": exc.history[-1] if exc.history else {},
        "rejected_candidate": rejected_candidate,
        "rejected_candidate_fingerprint": (
            stable_hash(rejected_candidate) if rejected_candidate else ""
        ),
        "empirical_evaluation_phase": empirical_evaluation_phase,
        "model_route_required_for_cross_owner_revision": False,
        "execution_results_observed": False,
        "execution_authorized": False,
        "execution_evidence_status": (
            "SIMULATION_ENGINEER_PACKET_VALIDATION_FAILURE_NOT_EXECUTION_EVIDENCE"
        ),
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        "boundary": SIMULATION_ENGINEER_BOUNDARY,
    }
    failure_artifact = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeSimulationEngineerValidationFailure",
        "failure_id": failure_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": _question_to_payload(question),
        "task_id": task.task_id,
        "theory_packet_id": theory_packet_id,
        "empirical_evaluation_phase": empirical_evaluation_phase,
        "validation_label": exc.validation_label,
        "failure_classification": failure_classification,
        "validation_errors": validation_errors,
        "structured_output_retry_history": exc.history,
        "rejected_candidate": rejected_candidate,
        "rejected_candidate_fingerprint": regeneration_feedback[
            "rejected_candidate_fingerprint"
        ],
        "execution_evidence_status": regeneration_feedback[
            "execution_evidence_status"
        ],
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        "boundary": SIMULATION_ENGINEER_BOUNDARY,
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, failure_id])[:20],
        task_id=task.task_id,
        artifact_id=failure_id,
        evidence_type="simulation_engineer_packet_validation_failure",
        status="VALIDATION_FAILED_RECORDED_NOT_EXECUTION_EVIDENCE",
        boundary=SIMULATION_ENGINEER_BOUNDARY,
        payload={
            "failure_classification": failure_classification,
            "validation_errors": validation_errors,
            "attempts": exc.attempts,
            "execution_evidence_status": regeneration_feedback[
                "execution_evidence_status"
            ],
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "SimulationEngineer exhausted its in-call structured-output retry. The "
            "complete rejected candidate and exact validator observations remain "
            "failed at their source owner without an Architect routing loop."
        ),
        produced_artifacts={failure_id: failure_artifact},
        observations=(
            EnvironmentObservation(
                observation_type="simulation_engineer_packet_validation_failure",
                summary="; ".join(validation_errors)[:500],
                payload={
                    "failure_id": failure_id,
                    "validation_errors": validation_errors,
                    "execution_evidence_status": regeneration_feedback[
                        "execution_evidence_status"
                    ],
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification=failure_classification,
    )


def _algorithm_engineer_packet_validation_failure_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    theory_packet_id: str,
    simulation_manifest_id: str,
    implementation_gaps: list[Mapping[str, Any]],
    exc: PacketValidationError,
) -> AgentStepResult:
    validation_errors = [str(error) for error in exc.errors if str(error)]
    failure_classification = "algorithm_engineer_packet_validation_failed"
    failure_id = (
        "algorithm_engineer_validation_failure:"
        + stable_hash([task.task_id, exc.validation_label, validation_errors, exc.history])[:20]
    )
    rejected_candidate = (
        deepcopy(dict(exc.last_invalid_packet))
        if isinstance(exc.last_invalid_packet, Mapping)
        else {}
    )
    failure_artifact = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeAlgorithmEngineerValidationFailure",
        "failure_id": failure_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": _question_to_payload(question),
        "task_id": task.task_id,
        "theory_packet_id": theory_packet_id,
        "simulation_manifest_id": simulation_manifest_id,
        "implementation_gaps": [dict(row) for row in implementation_gaps],
        "validation_label": exc.validation_label,
        "failure_classification": failure_classification,
        "validation_errors": validation_errors,
        "structured_output_retry_history": exc.history,
        "rejected_candidate": rejected_candidate,
        "rejected_candidate_fingerprint": (
            stable_hash(rejected_candidate) if rejected_candidate else ""
        ),
        "execution_evidence_status": "ALGORITHM_ENGINEER_PACKET_VALIDATION_FAILURE_NOT_EXECUTION_EVIDENCE",
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        "boundary": (
            "This artifact records a local validator failure from an LLM "
            "AlgorithmEngineer proposal. No code was executed, no registered template "
            "was used as capability evidence, and this is not proof evidence."
        ),
    }
    regeneration_feedback = {
        "feedback_id": failure_id,
        "feedback_type": "algorithm_engineer_packet_validation_feedback",
        "question_id": question.id,
        "source_theory_packet_id": theory_packet_id,
        "failure_classification": failure_classification,
        "validation_label": exc.validation_label,
        "validation_errors": validation_errors,
        "model_generation_attempt_history": deepcopy(exc.history),
        "last_attempt_summary": exc.history[-1] if exc.history else {},
        "rejected_candidate": rejected_candidate,
        "rejected_candidate_fingerprint": (
            stable_hash(rejected_candidate) if rejected_candidate else ""
        ),
        "model_route_required_for_cross_owner_revision": False,
        "execution_results_observed": False,
        "execution_authorized": False,
        "execution_evidence_status": "ALGORITHM_ENGINEER_PACKET_VALIDATION_FAILURE_NOT_EXECUTION_EVIDENCE",
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        "boundary": ALGORITHM_ENGINEER_BOUNDARY,
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, failure_id])[:20],
        task_id=task.task_id,
        artifact_id=failure_id,
        evidence_type="algorithm_engineer_packet_validation_failure",
        status="VALIDATION_FAILED_RECORDED_NOT_EXECUTION_EVIDENCE",
        boundary=ALGORITHM_ENGINEER_BOUNDARY,
        payload={
            "failure_classification": failure_classification,
            "validation_errors": validation_errors,
            "attempts": exc.attempts,
            "execution_evidence_status": (
                "ALGORITHM_ENGINEER_PACKET_VALIDATION_FAILURE_NOT_EXECUTION_EVIDENCE"
            ),
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "AlgorithmEngineer exhausted its in-call structured-output retry. The "
            "complete rejected candidate and exact validator observations remain "
            "failed at their source owner without an Architect routing loop."
        ),
        produced_artifacts={failure_id: failure_artifact},
        observations=(
            EnvironmentObservation(
                observation_type="algorithm_engineer_packet_validation_failure",
                summary="; ".join(validation_errors)[:500],
                payload={
                    "failure_id": failure_id,
                    "failure_classification": failure_classification,
                    "validation_errors": validation_errors,
                    "execution_evidence_status": (
                        "ALGORITHM_ENGINEER_PACKET_VALIDATION_FAILURE_NOT_EXECUTION_EVIDENCE"
                    ),
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification=failure_classification,
    )






































class FormalizerWorkspaceRuntimeSubsystem:
    """One model-owned Lean workspace exposed through two task entry names."""

    def __init__(
        self,
        *,
        proposal_agent: LLMFormalizerProofEngineerAgent | None = None,
        proof_state_provider: ProofStateFeedbackProvider | None = None,
        formal_source_retriever: Any | None = None,
        proof_search_provider: LeanProofSearchProvider | None = None,
        lean_candidate_root: Path = Path("runs") / "formalizer_lean_candidates",
        lean_candidate_local_lean: bool = False,
        lean_candidate_lean_project: Path | None = None,
        lean_candidate_lean_timeout: int = 30,
        architect_coordinator_available: bool = False,
        formal_target_semantic_reviewer_available: bool = False,
        formal_target_semantic_review_max_revisions: int = 1,
        runtime_config: ResearchAgentRuntimeConfig = ResearchAgentRuntimeConfig(),
    ) -> None:
        self.proposal_agent = proposal_agent
        self.proof_state_provider = proof_state_provider
        self.lean_candidate_root = lean_candidate_root
        self.lean_candidate_local_lean = lean_candidate_local_lean
        self.lean_candidate_lean_project = lean_candidate_lean_project
        self.lean_candidate_lean_timeout = lean_candidate_lean_timeout
        self.architect_coordinator_available = architect_coordinator_available
        self.formal_target_semantic_reviewer_available = bool(
            formal_target_semantic_reviewer_available
        )
        self.formal_target_semantic_review_max_revisions = max(
            0,
            int(formal_target_semantic_review_max_revisions or 0),
        )
        self.runtime_config = runtime_config
        self.formal_source_retriever = formal_source_retriever
        self.proof_search_provider = proof_search_provider

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        subsystem_name = (
            task.owner_subsystem
            if task.owner_subsystem == "FormalizationEvaluator"
            else "FormalizationEvaluator"
        )
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        context["runtime_task"] = _runtime_task_prompt_summary(task)
        environment_feedback: Mapping[str, Any] = (
            task.inputs.get("environment_feedback", {})
            if isinstance(task.inputs.get("environment_feedback", {}), Mapping)
            else {}
        )
        if str(environment_feedback.get("artifact_kind", "") or "") == (
            "RuntimeWorkspaceObservationRef"
        ):
            source_artifact_id = str(
                environment_feedback.get("source_artifact_id", "") or ""
            )
            stored_feedback = blackboard.artifacts.get(source_artifact_id, {})
            expected_source_artifact_hash = str(
                environment_feedback.get("source_artifact_hash", "") or ""
            )
            stored_feedback_valid = bool(
                isinstance(stored_feedback, Mapping)
                and stored_feedback
                and (
                    not expected_source_artifact_hash
                    or stable_hash(stored_feedback)
                    == expected_source_artifact_hash
                )
            )
            if stored_feedback_valid:
                environment_feedback = stored_feedback
                resolved_inputs = dict(task.inputs)
                resolved_inputs["environment_feedback"] = deepcopy(
                    dict(stored_feedback)
                )
                task = replace(task, inputs=resolved_inputs)
            else:
                return AgentStepResult(
                    status="BLOCKED",
                    rationale=(
                        "Formalizer workspace continuation could not resolve its "
                        "exact hash-bound observation artifact."
                    ),
                    observations=(
                        EnvironmentObservation(
                            observation_type=(
                                "formalizer_workspace_observation_ref_rejected"
                            ),
                            summary=(
                                "The referenced workspace observation was missing "
                                "or did not match its recorded artifact hash."
                            ),
                            payload={
                                "source_artifact_id": source_artifact_id,
                                "source_artifact_present": bool(stored_feedback),
                                "source_artifact_hash_expected": (
                                    expected_source_artifact_hash
                                ),
                                "source_artifact_hash_observed": (
                                    stable_hash(stored_feedback)
                                    if isinstance(stored_feedback, Mapping)
                                    and stored_feedback
                                    else ""
                                ),
                                "runtime_edits_candidate": False,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                            },
                        ),
                    ),
                    failure_classification=(
                        "formalizer_workspace_observation_ref_invalid"
                    ),
                )
        if environment_feedback:
            context["environment_feedback"] = environment_feedback
        context = _runtime_context_with_environment_feedback_contract(
            context,
            environment_feedback,
            subsystem=subsystem_name,
        )
        formalization_control = _architect_control_payload(context, subsystem_name)
        formalization_control_seed = _runtime_architect_control_seed_from_control(
            formalization_control,
            control_source="formalization_architect_control",
        )
        packet_id = str(task.inputs.get("theory_packet_id", ""))
        packet = blackboard.artifacts.get(packet_id, {})
        runtime_theory_trace_contract = _runtime_theory_trace_consumption_contract(
            consumer_subsystem="FormalizerProofEngineer",
            source_theory_packet_id=packet_id,
            theory_packet=packet if isinstance(packet, Mapping) else {},
        )
        simulation_manifest_id = str(task.inputs.get("simulation_manifest_id", ""))
        algorithm_sandbox_manifest_id = str(task.inputs.get("algorithm_sandbox_manifest_id", ""))
        simulation_manifest = blackboard.artifacts.get(simulation_manifest_id, {})
        algorithm_manifest = blackboard.artifacts.get(algorithm_sandbox_manifest_id, {})
        missing_simulation_result = (
            _runtime_missing_simulation_handoff_result_if_needed(
                source_subsystem=subsystem_name,
                task=task,
                question=question,
                simulation_manifest_id=simulation_manifest_id,
                simulation_manifest=simulation_manifest,
            )
        )
        if missing_simulation_result is not None:
            return missing_simulation_result
        missing_algorithm_result = (
            _runtime_missing_algorithm_handoff_result_if_needed(
                source_subsystem=subsystem_name,
                task=task,
                question=question,
                algorithm_sandbox_manifest_id=algorithm_sandbox_manifest_id,
                algorithm_manifest=algorithm_manifest,
            )
        )
        if missing_algorithm_result is not None:
            return missing_algorithm_result
        llm_research_authority = runtime_llm_research_authority_required(
            context,
            packet if isinstance(packet, Mapping) else {},
        )
        if llm_research_authority:
            research_bundle = derive_runtime_research_problem(
                question=question,
                architect_context=context,
                theory_packet=packet if isinstance(packet, Mapping) else {},
            )
            problem = research_bundle.problem
            theorem_goals = list(research_bundle.theorem_goals)
            problem_authority = research_bundle.provenance()
        else:
            problem = ProblemFormalizer().formalize(question)
            _procedures, theorem_goals = TheoryPlanner().plan(problem)
            problem_authority = legacy_runtime_research_problem_provenance()
        proposal_packet: dict[str, Any] | None = None
        proposal_evidence: EvidenceLedgerEntry | None = None
        produced_artifacts: dict[str, Any] = {}
        observations: list[EnvironmentObservation] = []
        proposal_source = ""
        formalizer_theory_trace_contract: dict[str, Any] = {}
        formalizer_theory_trace_alignment_contract: dict[str, Any] = {}
        lean_candidate_revision_feedback: dict[str, Any] | None = None
        lean_candidate_materialization: dict[str, Any] | None = None
        lean_candidate_client_tool_loop_evidence: dict[str, Any] = {}
        lean_candidate_client_tool_loop_ledger_entry: (
            EvidenceLedgerEntry | None
        ) = None
        kernel_promotion: dict[str, Any] | None = None
        kernel_promotion_evidence: EvidenceLedgerEntry | None = None
        source_theorem_kernel_verified = False

        kernel_promotion = evaluate_lean_kernel_promotion(
            blackboard_artifacts=blackboard.artifacts,
            environment_feedback=environment_feedback,
            lean_project=self.lean_candidate_lean_project,
            lean_timeout=self.lean_candidate_lean_timeout,
        )
        if kernel_promotion is not None:
            promotion_id = str(kernel_promotion["promotion_id"])
            kernel_promotion = _runtime_artifact_with_architect_control(
                promotion_id,
                kernel_promotion,
                formalization_control_seed,
                subsystem_override=subsystem_name,
            )
            produced_artifacts[promotion_id] = kernel_promotion
            source_theorem_kernel_verified = bool(
                kernel_promotion.get("source_theorem_kernel_verified", False)
            )
            observations.append(
                EnvironmentObservation(
                    observation_type="lean_kernel_promotion",
                    summary=(
                        "exact reviewed model source passed the local Lean identity gate"
                        if source_theorem_kernel_verified
                        else "; ".join(kernel_promotion.get("blockers", []) or [])[:500]
                    ),
                    payload={
                        "promotion_id": promotion_id,
                        "candidate_id": str(
                            kernel_promotion.get("candidate_id", "") or ""
                        ),
                        "candidate_source_hash": str(
                            kernel_promotion.get("candidate_source_hash", "") or ""
                        ),
                        "source_theorem_kernel_verified": (
                            source_theorem_kernel_verified
                        ),
                        "blockers": list(kernel_promotion.get("blockers", []) or []),
                        "proof_evidence_status": str(
                            kernel_promotion.get("proof_evidence_status", "") or ""
                        ),
                    },
                )
            )
            kernel_promotion_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:"
                + stable_hash([task.task_id, promotion_id])[:20],
                task_id=task.task_id,
                artifact_id=promotion_id,
                evidence_type="lean_kernel_promotion",
                status=(
                    "EXACT_MODEL_SOURCE_KERNEL_VERIFIED"
                    if source_theorem_kernel_verified
                    else "LEAN_KERNEL_PROMOTION_BLOCKED"
                ),
                boundary=KERNEL_PROOF_BOUNDARY,
                payload={
                    "candidate_id": str(
                        kernel_promotion.get("candidate_id", "") or ""
                    ),
                    "candidate_source_hash": str(
                        kernel_promotion.get("candidate_source_hash", "") or ""
                    ),
                    "target_ids": list(
                        kernel_promotion.get("target_ids", []) or []
                    ),
                    "runtime_edited_source": False,
                },
            )
            if source_theorem_kernel_verified:
                materialization_id = str(
                    kernel_promotion.get("candidate_materialization_id", "") or ""
                )
                materialization = blackboard.artifacts.get(materialization_id, {})
                if isinstance(materialization, Mapping):
                    lean_candidate_materialization = dict(materialization)
                    parent_packet_id = str(
                        materialization.get("source_formalizer_packet_id", "") or ""
                    )
                    parent_packet = blackboard.artifacts.get(parent_packet_id, {})
                    if isinstance(parent_packet, Mapping):
                        proposal_packet = dict(parent_packet)
                proposal_source = "reviewed_model_source_kernel_promotion"
            else:
                environment_feedback = {
                    **dict(environment_feedback),
                    "lean_kernel_promotion_observation": kernel_promotion,
                }

        if source_theorem_kernel_verified:
            pass
        elif self.proposal_agent is not None:
            try:
                environment_feedback = (
                    _runtime_environment_feedback_with_architect_directive(
                        context=context,
                        subsystem=subsystem_name,
                        feedback=environment_feedback,
                    )
                )
                environment_feedback = (
                    formalizer_feedback_with_task_bound_formal_source_queries(
                        environment_feedback,
                        question=question,
                        theory_packet=(
                            packet if isinstance(packet, Mapping) else {}
                        ),
                        theorem_goals=[
                            _theorem_goal_to_json(row) for row in theorem_goals
                        ],
                    )
                )
                environment_feedback = (
                    _formalizer_environment_feedback_with_formal_source_grounding(
                        environment_feedback,
                        formal_source_retriever=self.formal_source_retriever,
                    )
                )
                formal_source_grounding_summary = (
                    _formalizer_environment_feedback_formal_source_grounding_summary(
                        environment_feedback
                    )
                )
                if formal_source_grounding_summary:
                    observations.append(
                        EnvironmentObservation(
                            observation_type=(
                                "formalizer_environment_feedback_formal_source_grounding"
                            ),
                            summary=(
                                "Formalizer tool observations enriched "
                                "with bounded formal-source grounding hits before "
                                "LLM proposal; grounding is not proof evidence"
                            ),
                            payload=formal_source_grounding_summary,
                        )
                    )
                theory_context = packet if isinstance(packet, Mapping) else {}

                def run_client_tool_workspace() -> (
                    tuple[dict[str, Any], dict[str, Any]] | None
                ):
                    return _runtime_formalizer_lean_candidate_client_tool_workspace(
                        proposal_agent=self.proposal_agent,
                        question=question,
                        task=task,
                        blackboard=blackboard,
                        theory_packet=theory_context,
                        environment_feedback=environment_feedback,
                        formal_source_retriever=self.formal_source_retriever,
                        proof_search_provider=self.proof_search_provider,
                        proof_state_provider=self.proof_state_provider,
                        lean_candidate_root=self.lean_candidate_root,
                        lean_candidate_local_lean=(
                            self.lean_candidate_local_lean
                        ),
                        lean_candidate_lean_project=(
                            self.lean_candidate_lean_project
                        ),
                        lean_candidate_lean_timeout=(
                            self.lean_candidate_lean_timeout
                        ),
                        registered_problem=_problem_to_json(problem),
                        theorem_goals=[
                            _theorem_goal_to_json(row) for row in theorem_goals
                        ],
                    )

                client_tool_workspace_available = (
                    _runtime_formalizer_client_tool_workspace_available(
                        proposal_agent=self.proposal_agent,
                        lean_candidate_local_lean=(
                            self.lean_candidate_local_lean
                        ),
                        lean_candidate_lean_project=(
                            self.lean_candidate_lean_project
                        ),
                    )
                )
                if client_tool_workspace_available:
                    with agent_runtime_substage(
                        "formalizer_direct_lean_workspace"
                    ):
                        client_tool_workspace = run_client_tool_workspace()
                    if client_tool_workspace is None:
                        raise PacketValidationError(
                            validation_label="Formalizer direct Lean workspace",
                            attempts=1,
                            errors=[
                                "the configured direct Lean workspace could not start"
                            ],
                            history=[],
                        )
                    proposal_packet, lean_candidate_client_tool_loop_evidence = (
                        client_tool_workspace
                    )
                else:
                    with agent_runtime_substage("formalizer_planning_envelope"):
                        proposal_packet = self.proposal_agent.propose(
                            question=question,
                            theory_packet=theory_context,
                            simulation_manifest=(
                                simulation_manifest
                                if isinstance(simulation_manifest, Mapping)
                                else {}
                            ),
                            algorithm_manifest=(
                                algorithm_manifest
                                if isinstance(algorithm_manifest, Mapping)
                                else {}
                            ),
                            registered_problem=_problem_to_json(problem),
                            theorem_goals=[
                                _theorem_goal_to_json(row) for row in theorem_goals
                            ],
                            environment_feedback=environment_feedback,
                        )
            except PacketValidationError as exc:
                return _formalizer_packet_validation_failure_result(
                        task=task,
                        question=question,
                        theory_packet_id=packet_id,
                        simulation_manifest_id=simulation_manifest_id,
                        algorithm_sandbox_manifest_id=algorithm_sandbox_manifest_id,
                        exc=exc,
                        environment_feedback=environment_feedback,
                        workspace_artifacts=produced_artifacts,
                )
            except Exception as exc:
                return _formalizer_provider_failure_result(
                        task=task,
                        question=question,
                        theory_packet_id=packet_id,
                        simulation_manifest_id=simulation_manifest_id,
                        algorithm_sandbox_manifest_id=algorithm_sandbox_manifest_id,
                        environment_feedback=environment_feedback,
                        exc=exc,
                        max_provider_retries=(
                            self.runtime_config.max_subsystem_retries
                        ),
                )
            proposal_source = "llm_formalizer_proof_engineer_proposal"
        if proposal_packet is not None:
            proposal_id = str(proposal_packet["packet_id"])
            proposal_packet = _runtime_artifact_with_architect_control(
                proposal_id,
                proposal_packet,
                formalization_control_seed,
                subsystem_override=subsystem_name,
            )
            theory_trace_contracts = _runtime_theory_trace_consumption_contracts(
                proposal_packet
            )
            formalizer_theory_trace_contract = (
                theory_trace_contracts[0] if theory_trace_contracts else {}
            )
            formalizer_theory_trace_alignment_contract = (
                dict(proposal_packet.get("theory_trace_alignment_contract", {}))
                if isinstance(
                    proposal_packet.get("theory_trace_alignment_contract", {}),
                    Mapping,
                )
                else {}
            )
            precomputed_materialization: dict[str, Any] | None = None
            if not lean_candidate_client_tool_loop_evidence:
                precomputed_materialization = (
                    _materialize_formalizer_lean_candidate_artifacts(
                        root=self.lean_candidate_root,
                        question=question,
                        task=task,
                        proposal_packet=proposal_packet,
                        local_lean=self.lean_candidate_local_lean,
                        lean_project=self.lean_candidate_lean_project,
                        lean_timeout=self.lean_candidate_lean_timeout,
                    )
                )
            produced_artifacts[proposal_id] = proposal_packet
            if lean_candidate_client_tool_loop_evidence:
                loop_artifact_id = str(
                    lean_candidate_client_tool_loop_evidence.get(
                        "artifact_id",
                        "",
                    )
                    or "formalizer_lean_candidate_client_tool_loop:"
                    + stable_hash(
                        [
                            task.task_id,
                            proposal_id,
                            lean_candidate_client_tool_loop_evidence,
                        ]
                    )[:20]
                )
                lean_candidate_client_tool_loop_evidence["artifact_id"] = (
                    loop_artifact_id
                )
                produced_artifacts[loop_artifact_id] = (
                    _runtime_artifact_with_architect_control(
                        loop_artifact_id,
                        lean_candidate_client_tool_loop_evidence,
                        formalization_control_seed,
                        subsystem_override=subsystem_name,
                    )
                )
                lean_candidate_client_tool_loop_ledger_entry = (
                    EvidenceLedgerEntry(
                        evidence_id="evidence:"
                        + stable_hash([task.task_id, loop_artifact_id])[:20],
                        task_id=task.task_id,
                        artifact_id=loop_artifact_id,
                        evidence_type=(
                            "formalizer_lean_candidate_client_tool_loop"
                        ),
                        status=(
                            "LEAN_CANDIDATE_CLIENT_TOOL_LOOP_RECORDED_"
                            "NOT_PROOF_EVIDENCE"
                        ),
                        boundary=FORMALIZER_BOUNDARY,
                        payload={
                            "candidate_id": str(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "candidate_id",
                                    "",
                                )
                                or ""
                            ),
                            "parent_source_hash": str(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "parent_source_hash",
                                    "",
                                )
                                or ""
                            ),
                            "submitted_source_hash": str(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "submitted_source_hash",
                                    "",
                                )
                                or ""
                            ),
                            "runtime_executed_tool_calls": int(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "runtime_executed_tool_calls",
                                    0,
                                )
                                or 0
                            ),
                            "source_changed": bool(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "source_changed", False
                                )
                            ),
                            "source_updates": int(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "source_updates", 0
                                )
                                or 0
                            ),
                            "local_lean_checks": int(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "local_lean_checks", 0
                                )
                                or 0
                            ),
                            "latest_check_compiled": bool(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "latest_check_compiled", False
                                )
                            ),
                            "provider": str(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "provider", ""
                                )
                                or ""
                            ),
                            "model": str(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "model", ""
                                )
                                or ""
                            ),
                            "model_owned_lean_code": bool(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "model_owned_lean_code", False
                                )
                            ),
                            "runtime_selected_lean_code": bool(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "runtime_selected_lean_code", False
                                )
                            ),
                            "independent_semantic_review_required": True,
                            "kernel_verified": False,
                        },
                    )
                )
                observations.append(
                    EnvironmentObservation(
                        observation_type=(
                            "formalizer_lean_candidate_client_tool_loop"
                        ),
                        summary=(
                            "model-owned Lean edit/search/check loop submitted a "
                            "locally compiling candidate for independent review"
                        ),
                        payload={
                            "artifact_id": loop_artifact_id,
                            "candidate_id": str(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "candidate_id",
                                    "",
                                )
                                or ""
                            ),
                            "turns": int(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "turns",
                                    0,
                                )
                                or 0
                            ),
                            "tool_calls": int(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "tool_calls",
                                    0,
                                )
                                or 0
                            ),
                            "runtime_executed_tool_calls": int(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "runtime_executed_tool_calls",
                                    0,
                                )
                                or 0
                            ),
                            "proof_evidence_status": str(
                                lean_candidate_client_tool_loop_evidence.get(
                                    "proof_evidence_status",
                                    "",
                                )
                                or ""
                            ),
                        },
                    )
                )
            lean_candidate_materialization = (
                precomputed_materialization
                if precomputed_materialization is not None
                else _materialize_formalizer_lean_candidate_artifacts(
                    root=self.lean_candidate_root,
                    question=question,
                    task=task,
                    proposal_packet=proposal_packet,
                    local_lean=self.lean_candidate_local_lean,
                    lean_project=self.lean_candidate_lean_project,
                    lean_timeout=self.lean_candidate_lean_timeout,
                )
            )
            lean_candidate_materialization = _runtime_artifact_with_architect_control(
                str(lean_candidate_materialization.get("manifest_id", "")),
                lean_candidate_materialization,
                formalization_control_seed,
                subsystem_override=subsystem_name,
            )
            if (
                _runtime_context_requires_formalizer_lean_candidate(context)
                and int(
                    lean_candidate_materialization.get("n_candidate_sources", 0)
                    or 0
                )
                == 0
            ):
                validation_task = AgentTask(
                    task_id=task.task_id,
                    owner_subsystem=task.owner_subsystem,
                    objective=task.objective,
                    inputs={**task.inputs, "architect_context": context},
                    allowed_tools=task.allowed_tools,
                    budget=task.budget,
                    expected_artifacts=task.expected_artifacts,
                    acceptance_gate=task.acceptance_gate,
                    stop_condition=task.stop_condition,
                )
                return _formalizer_packet_validation_failure_result(
                        task=validation_task,
                        question=question,
                        theory_packet_id=packet_id,
                        simulation_manifest_id=simulation_manifest_id,
                        algorithm_sandbox_manifest_id=algorithm_sandbox_manifest_id,
                        exc=PacketValidationError(
                            validation_label=(
                                "Formalizer capability-eval Lean candidate"
                            ),
                            attempts=1,
                            errors=[
                                "capability_eval requires at least one model-authored "
                                "complete Lean source in formal_targets"
                            ],
                            history=[
                                {
                                    "packet_id": proposal_id,
                                    "n_candidate_sources": 0,
                                    "runtime_requested_evidence_contract": dict(
                                        context.get(
                                            "runtime_requested_evidence_contract",
                                            {},
                                        )
                                        if isinstance(
                                            context.get(
                                                "runtime_requested_evidence_contract",
                                                {},
                                            ),
                                            Mapping,
                                        )
                                        else {}
                                    ),
                                }
                            ],
                        ),
                        environment_feedback=environment_feedback,
                        workspace_artifacts=produced_artifacts,
                    )
            if lean_candidate_materialization["n_candidate_sources"] > 0:
                produced_artifacts[
                    str(lean_candidate_materialization["manifest_id"])
                ] = lean_candidate_materialization
                lean_candidate_revision_feedback = (
                    _formalizer_lean_candidate_revision_feedback(
                        lean_candidate_materialization,
                        formal_source_retriever=self.formal_source_retriever,
                        prior_environment_feedback=environment_feedback,
                    )
                )
            is_deterministic_closure = (
                proposal_source == "deterministic_theorem_closure_work_order_seed"
            )
            observations.append(
                EnvironmentObservation(
                    observation_type=proposal_source,
                    summary=(
                        "deterministic theorem-closure work-order seed recorded after "
                        "runtime memory exhausted the registered proof-bank bridge catalog"
                        if is_deterministic_closure
                        else "validated LLM Formalizer/ProofEngineer proposal recorded "
                        "before proof-bank/kernel evaluation"
                    ),
                    payload={
                        "packet_id": proposal_id,
                        "source_agent": str(proposal_packet.get("source_agent", "")),
                        "n_formal_targets": len(proposal_packet.get("formal_targets", []) or []),
                        "n_retrieval_queries": len(proposal_packet.get("retrieval_queries", []) or []),
                        "n_proof_bank_obligation_requests": len(
                            proposal_packet.get("proof_bank_obligation_requests", []) or []
                        ),
                        "n_lean_candidate_sources": int(
                            lean_candidate_materialization.get(
                                "n_candidate_sources",
                                0,
                            )
                        ),
                        "n_lean_candidate_artifacts_written": int(
                            lean_candidate_materialization.get(
                                "n_candidate_artifacts_written",
                                0,
                            )
                        ),
                        "proof_evidence_status": str(
                            proposal_packet.get(
                                "proof_evidence_status",
                                FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE,
                            )
                        ),
                        "runtime_theory_trace_consumption_contract": runtime_theory_trace_contract,
                        "theory_trace_consumption_contract": formalizer_theory_trace_contract,
                        "theory_trace_alignment_contract": formalizer_theory_trace_alignment_contract,
                    },
                )
            )
            proposal_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proposal_id])[:20],
                task_id=task.task_id,
                artifact_id=proposal_id,
                evidence_type=proposal_source,
                status=(
                    "WORK_ORDER_SEED_RECORDED_NOT_PROOF_EVIDENCE"
                    if is_deterministic_closure
                    else "PROPOSAL_RECORDED_REQUIRES_KERNEL_VERIFICATION"
                ),
                boundary=FORMALIZER_BOUNDARY,
                payload={
                    "source_agent": str(proposal_packet.get("source_agent", "")),
                    "n_formal_targets": len(proposal_packet.get("formal_targets", []) or []),
                    "n_retrieval_queries": len(proposal_packet.get("retrieval_queries", []) or []),
                    "n_lean_candidate_sources": int(
                        lean_candidate_materialization.get("n_candidate_sources", 0)
                    ),
                    "n_lean_candidate_artifacts_written": int(
                        lean_candidate_materialization.get(
                            "n_candidate_artifacts_written",
                            0,
                        )
                    ),
                    "n_local_lean_checked": int(
                        lean_candidate_materialization.get("n_local_lean_checked", 0)
                        or 0
                    ),
                    "n_local_lean_compiled": int(
                        lean_candidate_materialization.get("n_local_lean_compiled", 0)
                        or 0
                    ),
                    "source_llm_proposal_live_generator": (
                        _runtime_llm_proposal_packet_live_generator(proposal_packet)
                    ),
                    "lean_candidate_materialization_manifest_id": str(
                        lean_candidate_materialization.get("manifest_id", "")
                    ),
                    "kernel_verified": False,
                    "full_frontier_theorem_proved": False,
                    "runtime_theory_trace_consumption_contract": runtime_theory_trace_contract,
                    "theory_trace_consumption_contract": formalizer_theory_trace_contract,
                    "theory_trace_alignment_contract": formalizer_theory_trace_alignment_contract,
                },
            )
        manifest_id = "formalization_manifest:" + stable_hash([task.task_id, packet_id])[:20]
        deterministic_formalizer_work_order_seed_used = (
            proposal_source == "deterministic_theorem_closure_work_order_seed"
        )
        llm_formalizer_proof_engineer_proposal_observed = (
            proposal_source == "llm_formalizer_proof_engineer_proposal"
        )
        live_llm_formalizer_proof_engineer_proposal_observed = (
            llm_formalizer_proof_engineer_proposal_observed
            and isinstance(proposal_packet, Mapping)
            and _runtime_llm_proposal_packet_live_generator(proposal_packet)
        )
        proposal_backend_provider = (
            _runtime_llm_proposal_packet_backend_provider(proposal_packet)
            if isinstance(proposal_packet, Mapping)
            else ""
        )
        proposal_provider = (
            _runtime_llm_proposal_packet_provider(proposal_packet)
            if isinstance(proposal_packet, Mapping)
            else ""
        )
        if live_llm_formalizer_proof_engineer_proposal_observed:
            formalizer_agentic_capability_evidence_status = (
                "LIVE_LLM_FORMALIZER_PROOFENGINEER_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE"
            )
        elif llm_formalizer_proof_engineer_proposal_observed:
            formalizer_agentic_capability_evidence_status = (
                "LLM_FORMALIZER_PROOFENGINEER_PROPOSAL_WITHOUT_LIVE_BACKEND_NOT_AGENTIC_CAPABILITY"
            )
        elif deterministic_formalizer_work_order_seed_used:
            formalizer_agentic_capability_evidence_status = (
                "DETERMINISTIC_WORK_ORDER_SEED_NOT_AGENTIC_CAPABILITY"
            )
        else:
            formalizer_agentic_capability_evidence_status = (
                "NO_FORMALIZER_PROPOSAL_RECORDED"
            )
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeFormalizationManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "algorithm_sandbox_manifest_id": algorithm_sandbox_manifest_id,
            "runtime_architect_control": formalization_control,
            "research_problem_authority": problem_authority,
            **problem_authority,
            "theory_trace_consumption_contract": runtime_theory_trace_contract,
            "llm_formalizer_proof_engineer_proposal_id": (
                str(proposal_packet.get("packet_id", "")) if proposal_packet else ""
            ),
            "llm_formalizer_proof_engineer_theory_trace_consumption_contract": (
                formalizer_theory_trace_contract
            ),
            "llm_formalizer_proof_engineer_theory_trace_alignment_contract": (
                formalizer_theory_trace_alignment_contract
            ),
            "formalizer_proposal_source": proposal_source,
            "llm_formalizer_proof_engineer_proposal_observed": (
                llm_formalizer_proof_engineer_proposal_observed
            ),
            "live_llm_formalizer_proof_engineer_proposal_observed": (
                live_llm_formalizer_proof_engineer_proposal_observed
            ),
            "llm_formalizer_proof_engineer_proposal_provider": (
                proposal_provider
            ),
            "llm_formalizer_proof_engineer_proposal_backend_provider": (
                proposal_backend_provider
            ),
            "deterministic_formalizer_work_order_seed_used": (
                deterministic_formalizer_work_order_seed_used
            ),
            "lean_kernel_promotion_id": str(
                kernel_promotion.get("promotion_id", "")
                if kernel_promotion
                else ""
            ),
            "lean_candidate_client_tool_loop_id": str(
                lean_candidate_client_tool_loop_evidence.get("artifact_id", "")
                if lean_candidate_client_tool_loop_evidence
                else ""
            ),
            "source_theorem_kernel_verified": source_theorem_kernel_verified,
            "source_theorem_kernel_verified_target_ids": (
                list(kernel_promotion.get("target_ids", []) or [])
                if source_theorem_kernel_verified and kernel_promotion
                else []
            ),
            "source_theorem_kernel_verified_target_names": (
                [
                    str(kernel_promotion.get("target_lean_declaration", "") or "")
                ]
                if source_theorem_kernel_verified
                and kernel_promotion
                and str(kernel_promotion.get("target_lean_declaration", "") or "")
                else []
            ),
            "formalizer_agentic_capability_evidence_status": (
                formalizer_agentic_capability_evidence_status
            ),
            "formalizer_agentic_capability_boundary": (
                "Only live Claude/OpenAI Formalizer/ProofEngineer proposals "
                "can support formalizer capability claims. Deterministic "
                "theorem-closure packets are work-order scaffolds and are not "
                "agentic capability or proof evidence."
            ),
            "problem": _problem_to_json(problem),
            "llm_formalization_requests": (
                list(packet.get("formalization_requests", []) or [])
                if isinstance(packet, Mapping)
                else []
            ),
            "llm_proof_bank_obligation_requests": (
                list(proposal_packet.get("proof_bank_obligation_requests", []) or [])
                if isinstance(proposal_packet, Mapping)
                else []
            ),
            "llm_formalizer_gap_taxonomy": (
                list(proposal_packet.get("gap_taxonomy", []) or [])
                if isinstance(proposal_packet, Mapping)
                else []
            ),
            "deterministic_theorem_goals": [_theorem_goal_to_json(row) for row in theorem_goals],
            "counts": {
                "source_theorem_kernel_verified": int(
                    source_theorem_kernel_verified
                ),
            },
            "full_frontier_theorem_proved": False,
            "proof_evidence_status": (
                "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
                if source_theorem_kernel_verified
                else "NO_EXACT_SOURCE_THEOREM_KERNEL_PROOF"
            ),
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        }
        manifest = _runtime_artifact_with_architect_control(
            manifest_id,
            manifest,
            formalization_control_seed,
            subsystem_override=subsystem_name,
        )
        produced_artifacts[manifest_id] = manifest
        evidence_status = (
            "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
            if source_theorem_kernel_verified
            else "FORMALIZER_WORKSPACE_OBSERVATIONS_RECORDED_NOT_PROOF_EVIDENCE"
        )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="formalization_proof_feedback",
            status=evidence_status,
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "counts": manifest["counts"],
                "full_frontier_theorem_proved": False,
                "source_theorem_kernel_verified": (
                    source_theorem_kernel_verified
                ),
                "source_theorem_kernel_verified_target_ids": manifest[
                    "source_theorem_kernel_verified_target_ids"
                ],
                "architect_acceptance_gate": formalization_control.get("acceptance_gate", ""),
            },
        )
        observations.append(
            EnvironmentObservation(
                observation_type="formalization_proof_feedback",
                summary=(
                    "exact source theorem kernel verified"
                    if source_theorem_kernel_verified
                    else "model-authored formalization observations recorded"
                ),
                payload={
                    "counts": manifest["counts"],
                    "proof_evidence_status": manifest["proof_evidence_status"],
                    "full_frontier_theorem_proved": False,
                },
            )
        )
        formal_target_semantic_review_dispatch_evidence: (
            EvidenceLedgerEntry | None
        ) = None
        if lean_candidate_revision_feedback is not None:
            observations.append(
                EnvironmentObservation(
                    observation_type="formalizer_lean_candidate_local_lean_feedback",
                    summary=str(
                        lean_candidate_revision_feedback.get(
                            "failure_classification",
                            "formalizer_lean_candidate_local_lean_failed",
                        )
                    ),
                    payload=lean_candidate_revision_feedback,
                )
            )
        tool_calls: list[ToolCallRecord] = []
        if lean_candidate_client_tool_loop_evidence:
            loop_turns = int(
                lean_candidate_client_tool_loop_evidence.get("turns", 0) or 0
            )
            loop_tool_calls = int(
                lean_candidate_client_tool_loop_evidence.get("tool_calls", 0)
                or 0
            )
            loop_lean_checks = int(
                lean_candidate_client_tool_loop_evidence.get(
                    "local_lean_checks",
                    0,
                )
                or 0
            )
            tool_calls.append(
                ToolCallRecord(
                    tool_name=(
                        "LLMFormalizerProofEngineerAgent."
                        "run_lean_candidate_workspace_with_client_tools"
                    ),
                    inputs={
                        "candidate_id": str(
                            lean_candidate_client_tool_loop_evidence.get(
                                "candidate_id",
                                "",
                            )
                            or ""
                        ),
                        "parent_source_hash": str(
                            lean_candidate_client_tool_loop_evidence.get(
                                "parent_source_hash",
                                "",
                            )
                            or ""
                        ),
                        "model": str(
                            lean_candidate_client_tool_loop_evidence.get(
                                "model",
                                "",
                            )
                            or ""
                        ),
                        "model_tier": str(
                            lean_candidate_client_tool_loop_evidence.get(
                                "model_tier",
                                "",
                            )
                            or ""
                        ),
                    },
                    output_hash=str(
                        lean_candidate_client_tool_loop_evidence.get(
                            "submitted_source_hash",
                            "",
                        )
                        or ""
                    ),
                    exit_status="0",
                    stdout_summary=(
                        f"turns={loop_turns} tool_calls={loop_tool_calls} "
                        f"local_lean_checks={loop_lean_checks}"
                    ),
                    safety_boundary=FORMALIZER_BOUNDARY,
                )
            )
        if lean_candidate_revision_feedback is not None:
            workspace_feedback = {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "RuntimeFormalizerWorkspaceObservations",
                "feedback_type": "formalizer_workspace_observations",
                "question_id": question.id,
                "failure_classification": "formalizer_workspace_exhausted",
                "source_failure_classification": str(
                    lean_candidate_revision_feedback.get(
                        "failure_classification",
                        "",
                    )
                    or ""
                ),
                "formalization_manifest_id": manifest_id,
                "candidate_materialization_manifest_id": str(
                    lean_candidate_revision_feedback.get(
                        "source_manifest_id",
                        "",
                    )
                    or ""
                ),
                "tool_loop_artifact_id": str(
                    lean_candidate_client_tool_loop_evidence.get(
                        "artifact_id",
                        "",
                    )
                    or ""
                ),
                "model_owned_source": True,
                "runtime_selected_source_edit": False,
                "model_route_required_for_cross_owner_revision": False,
                "proof_evidence_status": (
                    "FORMALIZER_WORKSPACE_FAILURE_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                "boundary": (
                    "The referenced manifests contain the exact model source, tool "
                    "transcript, and Lean observations. This compact handoff does not "
                    "copy them or prescribe a proof strategy."
                ),
            }
            workspace_feedback["feedback_id"] = (
                "formalizer_workspace_observations:"
                + stable_hash(workspace_feedback)[:20]
            )
            formal_target_review_dispatch = (
                _runtime_formal_target_semantic_review_dispatch(
                    task=task,
                    question=question,
                    source_subsystem=subsystem_name,
                    candidate_materialization=(
                        lean_candidate_materialization
                        if isinstance(lean_candidate_materialization, Mapping)
                        else {}
                    ),
                    theory_packet=(
                        packet if isinstance(packet, Mapping) else {}
                    ),
                    proposal_packet=(
                        proposal_packet
                        if isinstance(proposal_packet, Mapping)
                        else {}
                    ),
                    candidate_feedback=lean_candidate_revision_feedback,
                    architect_context=context,
                    deferred_next_task=(
                        _formalizer_semantic_review_continuation_task(
                            task=task,
                            question=question,
                            context=context,
                            workspace_feedback=workspace_feedback,
                            source_artifact_id=manifest_id,
                        )
                    ),
                    blackboard_artifacts=blackboard.artifacts,
                    max_revisions=(
                        self.formal_target_semantic_review_max_revisions
                    ),
                )
                if self.formal_target_semantic_reviewer_available
                else None
            )
            if formal_target_review_dispatch is not None:
                review_dispatch_blocked = str(
                    formal_target_review_dispatch.get(
                        "dispatch_status", "READY"
                    )
                    or "READY"
                ) == "BLOCKED"
                formal_target_review_work_order_id = str(
                    formal_target_review_dispatch.get("work_order_id", "")
                    or ""
                )
                produced_artifacts.update(
                    {
                        str(artifact_id): artifact
                        for artifact_id, artifact in dict(
                            formal_target_review_dispatch.get("artifacts", {})
                        ).items()
                    }
                )
                observations.append(
                    formal_target_review_dispatch["observation"]
                )
                formal_target_semantic_review_dispatch_evidence = (
                    formal_target_review_dispatch["evidence"]
                )
                next_task = formal_target_review_dispatch["next_task"]
                result_status = "REROUTE"
                if review_dispatch_blocked:
                    result_rationale = (
                        "Independent exact-target review is required, but its lineage "
                        "contract is incomplete or inconsistent; the reviewer task "
                        "fails closed before any downstream replan."
                    )
                    failure_classification = (
                        "formal_target_semantic_review_dispatch_input_invalid"
                    )
                else:
                    result_rationale = (
                        "Runtime materialized a hash-bound exact theorem target; "
                        "independent mathematical semantic review must accept the "
                        "statement before kernel promotion or any cross-workspace "
                        "decision."
                    )
                    failure_classification = (
                        "formal_target_semantic_review_required_before_replan"
                    )
            else:
                next_task = None
                observations.append(
                    EnvironmentObservation(
                        observation_type="formalizer_workspace_blocked",
                        summary=(
                            "The bounded model-owned Lean workspace ended without an "
                            "accepted exact-target candidate. Exact source and raw Lean "
                            "observations remain failed at the Formalizer workspace."
                        ),
                        payload={
                            "formalization_manifest_id": manifest_id,
                            "source_failure_classification": str(
                                lean_candidate_revision_feedback.get(
                                    "failure_classification",
                                    "",
                                )
                                or ""
                            ),
                            "runtime_edited_source": False,
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    )
                )
                result_status = "BLOCKED"
                result_rationale = (
                    "The Formalizer consumed local Lean/proof-state feedback inside "
                    "its direct full-source tool loop and ended without "
                    "kernel-eligible source; no independent exact-target reviewer is "
                    "available, so the source owner fails closed without routing."
                )
                failure_classification = "formalizer_workspace_exhausted"
        else:
            critic_task = AgentTask(
                task_id=f"critic:{question.id}:{stable_hash(manifest_id)[:8]}",
                owner_subsystem="CriticEvaluator",
                objective=(
                    "Independently evaluate the referenced research artifacts, "
                    "preserve evidence boundaries, and identify only whether any "
                    "remaining conflict crosses workspace ownership."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "theory_packet_id": packet_id,
                    "formalization_manifest_id": manifest_id,
                    "architect_context": context,
                },
                allowed_tools=("model_backend", "blackboard", "evidence_ledger"),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "CriticEvaluator",
                    ("critic_evaluator_manifest", "critic_model_packet"),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "CriticEvaluator",
                    "critic observations remain independent and do not prescribe source edits",
                ),
                stop_condition=(
                    "critic records an evidence-grounded assessment and either "
                    "accepts, reports a blocker, or requests cross-workspace coordination"
                ),
            )
            compiled_exact_review_feedback = (
                _formalizer_compiled_exact_candidate_semantic_review_feedback(
                    lean_candidate_materialization
                )
                if self.formal_target_semantic_reviewer_available
                and isinstance(lean_candidate_materialization, Mapping)
                else None
            )
            compiled_exact_review_dispatch: dict[str, Any] | None = None
            if compiled_exact_review_feedback is not None:
                compiled_next_inputs = dict(task.inputs)
                compiled_next_inputs["environment_feedback"] = (
                    compiled_exact_review_feedback
                )
                compiled_exact_proofengineer_task = AgentTask(
                    task_id=(
                        f"compiled-exact-target-proofengineer:{question.id}:"
                        f"{stable_hash([manifest_id, compiled_exact_review_feedback])[:8]}"
                    ),
                    owner_subsystem="FormalizationEvaluator",
                    objective=(
                        "Consume an independently reviewed, already-compiling exact "
                        "theorem target through the typed source-proof gate."
                    ),
                    inputs=compiled_next_inputs,
                    allowed_tools=tuple(
                        dict.fromkeys(
                            (
                                *task.allowed_tools,
                                "model_backend",
                                "local_lean",
                                "lean_lsp_mcp",
                                "formal_source_retrieval",
                                "proof_search",
                            )
                        )
                    ),
                    expected_artifacts=task.expected_artifacts,
                    acceptance_gate=(
                        "independent semantic acceptance plus an exact runtime-owned "
                        "kernel rerun is required for source-theorem promotion"
                    ),
                    stop_condition=(
                        "exact source theorem is kernel verified or an explicit "
                        "formal blocker is recorded"
                    ),
                )
                compiled_exact_review_dispatch = (
                    _runtime_formal_target_semantic_review_dispatch(
                        task=task,
                        question=question,
                        source_subsystem=subsystem_name,
                        candidate_materialization=lean_candidate_materialization,
                        theory_packet=(
                            packet if isinstance(packet, Mapping) else {}
                        ),
                        proposal_packet=(
                            proposal_packet
                            if isinstance(proposal_packet, Mapping)
                            else {}
                        ),
                        candidate_feedback=compiled_exact_review_feedback,
                        architect_context=context,
                        deferred_next_task=compiled_exact_proofengineer_task,
                        blackboard_artifacts=blackboard.artifacts,
                        max_revisions=(
                            self.formal_target_semantic_review_max_revisions
                        ),
                    )
                )
            if compiled_exact_review_dispatch is not None:
                compiled_review_dispatch_blocked = str(
                    compiled_exact_review_dispatch.get(
                        "dispatch_status", "READY"
                    )
                    or "READY"
                ) == "BLOCKED"
                compiled_review_work_order_id = str(
                    compiled_exact_review_dispatch.get("work_order_id", "") or ""
                )
                produced_artifacts.update(
                    {
                        str(artifact_id): artifact
                        for artifact_id, artifact in dict(
                            compiled_exact_review_dispatch.get("artifacts", {})
                        ).items()
                    }
                )
                observations.append(compiled_exact_review_dispatch["observation"])
                formal_target_semantic_review_dispatch_evidence = (
                    compiled_exact_review_dispatch["evidence"]
                )
                next_task = compiled_exact_review_dispatch["next_task"]
                result_rationale = (
                    "Independent exact-target review is required, but its lineage "
                    "contract is incomplete or inconsistent; the reviewer task "
                    "will fail closed before source-proof promotion."
                    if compiled_review_dispatch_blocked
                    else "Runtime observed an already-compiling exact theorem "
                    "artifact, but routed it through independent whole-target "
                    "mathematical review before source-proof promotion or further "
                    "prover work."
                )
            else:
                next_task = critic_task
                result_rationale = (
                    "Runtime recorded the model-owned formalization workspace. The "
                    "theorem remains unproved unless the unchanged exact target is "
                    "closed by the kernel; references now route to the independent "
                    "CriticEvaluator."
                )
            result_status = "REROUTE"
            failure_classification = ""
        return AgentStepResult(
            status=result_status,
            rationale=result_rationale,
            produced_artifacts=produced_artifacts,
            observations=tuple(observations),
            tool_calls=tuple(tool_calls),
            evidence_entries=tuple(
                row
                for row in (
                    kernel_promotion_evidence,
                    proposal_evidence,
                    evidence,
                    lean_candidate_client_tool_loop_ledger_entry,
                    formal_target_semantic_review_dispatch_evidence,
                )
                if row is not None
            ),
            next_task=next_task,
            failure_classification=failure_classification,
        )


def _formalizer_provider_failure_classification(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    haystack = f"{name} {text}"
    if "timeout" in haystack or "timed out" in haystack:
        return "provider_timeout_error"
    if (
        "connection" in haystack
        or "network" in haystack
        or "dns" in haystack
        or "host resolution" in haystack
        or "temporarily unavailable" in haystack
        or "server error" in haystack
        or "overloaded" in haystack
    ):
        return "provider_connection_error"
    return "formalizer_provider_generation_failed"




def _formalizer_provider_failure_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    theory_packet_id: str,
    simulation_manifest_id: str,
    algorithm_sandbox_manifest_id: str,
    environment_feedback: Mapping[str, Any],
    exc: Exception,
    max_provider_retries: int = 1,
) -> AgentStepResult:
    """Return a transport failure to the same source-producing agent."""

    failure_classification = _formalizer_provider_failure_classification(exc)
    retry_attempt = max(
        0,
        _int_like(task.inputs.get("formalizer_provider_retry_attempt", 0)),
    )
    max_provider_retries = max(0, int(max_provider_retries or 0))
    retry_allowed = retry_attempt < max_provider_retries
    failure_summary = f"{type(exc).__name__}: {str(exc)[:2000]}"
    failure_id = "formalizer_provider_failure:" + stable_hash(
        [
            task.task_id,
            theory_packet_id,
            failure_classification,
            retry_attempt,
            failure_summary,
        ]
    )[:20]
    prior_observations = coding_agent_observations_only(environment_feedback)
    feedback = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "FormalizerProviderObservation",
        "failure_id": failure_id,
        "failure_classification": failure_classification,
        "provider_error": failure_summary,
        "attempt": retry_attempt + 1,
        "max_retries": max_provider_retries,
        "retry_allowed": retry_allowed,
        "prior_environment_observations": prior_observations,
        "runtime_edits_source": False,
        "runtime_selects_mathematics_or_lean": False,
        "proof_evidence_status": "FORMALIZER_PROVIDER_FAILURE_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }
    artifact = {
        **feedback,
        "artifact_kind": "RuntimeFormalizerProviderFailure",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": _question_to_payload(question),
        "task_id": task.task_id,
        "theory_packet_id": theory_packet_id,
        "simulation_manifest_id": simulation_manifest_id,
        "algorithm_sandbox_manifest_id": algorithm_sandbox_manifest_id,
    }

    next_task: AgentTask | None = None
    if retry_allowed:
        next_inputs = dict(task.inputs)
        next_inputs["environment_feedback"] = feedback
        next_inputs["formalizer_provider_retry_attempt"] = retry_attempt + 1
        next_task = replace(
            task,
            task_id=(
                f"formalizer-provider-retry:{question.id}:"
                f"{stable_hash([failure_id, retry_attempt])[:8]}"
            ),
            objective=(
                "Retry the same Formalizer workspace after the recorded provider "
                "transport failure; preserve the unchanged target and source lineage."
            ),
            inputs=next_inputs,
        )

    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, failure_id])[:20],
        task_id=task.task_id,
        artifact_id=failure_id,
        evidence_type="formalizer_provider_failure",
        status="FORMALIZER_PROVIDER_FAILURE_RECORDED_NOT_PROOF_EVIDENCE",
        boundary=KERNEL_PROOF_BOUNDARY,
        payload={
            "failure_classification": failure_classification,
            "retry_allowed": retry_allowed,
            "proof_evidence_status": artifact["proof_evidence_status"],
        },
    )
    return AgentStepResult(
        status="REVISE" if retry_allowed else "BLOCKED",
        rationale=(
            "The provider failure and prior observations were returned unchanged to "
            "the same Formalizer workspace for one bounded retry."
            if retry_allowed
            else "The bounded provider retry budget was exhausted without proof evidence."
        ),
        produced_artifacts={failure_id: artifact},
        observations=(
            EnvironmentObservation(
                observation_type="formalizer_provider_failure",
                summary=failure_classification,
                payload=feedback,
            ),
        ),
        evidence_entries=(evidence,),
        next_task=next_task,
        failure_classification=(
            failure_classification
            if retry_allowed
            else "formalizer_provider_retry_exhausted"
        ),
    )

def _formalizer_packet_validation_failure_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    theory_packet_id: str,
    simulation_manifest_id: str,
    algorithm_sandbox_manifest_id: str,
    exc: PacketValidationError,
    environment_feedback: Mapping[str, Any] | None = None,
    workspace_artifacts: Mapping[str, Any] | None = None,
) -> AgentStepResult:
    """Record exhausted validation without inventing a source-level repair."""
    validation_errors = [str(error) for error in exc.errors if str(error)]
    prior_feedback = (
        environment_feedback
        if isinstance(environment_feedback, Mapping)
        else (
            task.inputs.get("environment_feedback", {})
            if isinstance(task.inputs.get("environment_feedback", {}), Mapping)
            else {}
        )
    )
    prior_observations = compact_lean_workspace_observation(
        prior_feedback
    )
    last_invalid_packet = (
        deepcopy(dict(exc.last_invalid_packet))
        if isinstance(exc.last_invalid_packet, Mapping)
        else {}
    )
    recovery_checkpoint = (
        deepcopy(dict(exc.recovery_checkpoint))
        if isinstance(exc.recovery_checkpoint, Mapping)
        else {}
    )
    checkpoint_source = str(
        recovery_checkpoint.get("current_source", "") or ""
    )
    checkpoint_source_hash = str(
        recovery_checkpoint.get("current_source_hash", "") or ""
    )
    complete_current_source_checkpoint_provided = bool(
        checkpoint_source.strip()
        and checkpoint_source_hash == stable_hash(checkpoint_source)
        and recovery_checkpoint.get("model_owned_lean_code") is True
        and recovery_checkpoint.get("runtime_selected_lean_code") is False
    )
    attempt_history_rows = [
        deepcopy(dict(row)) for row in exc.history if isinstance(row, Mapping)
    ]
    attempt_history_hash = stable_hash(attempt_history_rows)
    attempt_history_id = (
        "formalizer_attempt_history:" + attempt_history_hash[:20]
        if attempt_history_rows
        else ""
    )
    failure_id = (
        "formalizer_validation_failure:"
        + stable_hash(
            [
                task.task_id,
                exc.validation_label,
                validation_errors,
                attempt_history_hash,
                last_invalid_packet,
                recovery_checkpoint,
            ]
        )[:20]
    )
    rejected_candidate_fingerprint = (
        stable_hash(last_invalid_packet) if last_invalid_packet else ""
    )
    validation_feedback = formalizer_validation_feedback_envelope(
        validation_errors,
        validation_label=exc.validation_label,
        invalid_packet=last_invalid_packet,
        attempt_history=exc.history,
        retry_depth=0,
    )
    validation_boundary = {
        "complete_rejected_candidate_provided": bool(last_invalid_packet),
        "complete_current_source_checkpoint_provided": (
            complete_current_source_checkpoint_provided
        ),
        "raw_validation_observations_provided": True,
        "runtime_edits_candidate": False,
        "runtime_selects_mathematics_or_lean": False,
        "response_schema_unchanged": True,
        "local_validators_unchanged": True,
        "kernel_gate_unchanged": True,
    }
    lean_workspace_observation_available = bool(
        str(recovery_checkpoint.get("artifact_kind", "") or "")
        in {
            "LeanCandidateWorkspaceRecoveryCheckpoint",
            "LeanCandidateRevisionRecoveryCheckpoint",
        }
    )
    history_tool_calls = [
        dict(call)
        for row in attempt_history_rows
        for call in row.get("tool_calls", []) or []
        if isinstance(call, Mapping)
    ]
    tool_name_counts = {
        name: sum(
            1
            for call in history_tool_calls
            if str(call.get("name", "") or "") == name
        )
        for name in {
            str(call.get("name", "") or "")
            for call in history_tool_calls
            if str(call.get("name", "") or "")
        }
    }
    last_check = recovery_checkpoint.get("last_check", {})
    if not isinstance(last_check, Mapping):
        last_check = recovery_checkpoint.get("latest_check_observation", {})
    if not isinstance(last_check, Mapping):
        last_check = {}
    parent_source_hash = str(
        recovery_checkpoint.get("parent_source_hash", "") or ""
    )
    client_tool_loop_observation = (
        {
            "candidate_source_hash": checkpoint_source_hash,
            "parent_source_hash": parent_source_hash,
            "source_changed": bool(
                parent_source_hash
                and checkpoint_source_hash
                and parent_source_hash != checkpoint_source_hash
            ),
            "source_updates": _int_like(
                recovery_checkpoint.get("source_updates", 0)
            ),
            "local_lean_checks": _int_like(
                recovery_checkpoint.get("checks", 0)
            ),
            "latest_check_compiled": _bool_like(
                last_check.get("compiled", False)
            ),
            "n_client_tool_calls": len(history_tool_calls),
            "n_formal_source_search_calls": tool_name_counts.get(
                "search_formal_environment", 0
            ),
            "n_proof_candidate_search_calls": tool_name_counts.get(
                "search_proof_candidates", 0
            ),
            "n_formal_rag_tool_calls": (
                tool_name_counts.get("search_formal_environment", 0)
                + tool_name_counts.get("search_proof_candidates", 0)
            ),
            "provider": str(recovery_checkpoint.get("provider", "") or ""),
            "model": str(recovery_checkpoint.get("model", "") or ""),
            "model_owned_lean_code": _bool_like(
                recovery_checkpoint.get("model_owned_lean_code", False)
            ),
            "runtime_selected_lean_code": False,
        }
        if lean_workspace_observation_available
        else {}
    )
    failure_classification = (
        "formalizer_client_tool_loop_exhausted"
        if lean_workspace_observation_available
        else "formalizer_packet_validation_failed"
    )
    feedback = {
        **deepcopy(dict(prior_observations)),
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "FormalizerPacketValidationObservations",
        "feedback_type": "formalizer_packet_validation_observations",
        "feedback_id": str(validation_feedback["feedback_id"]),
        "failure_id": failure_id,
        "failure_classification": failure_classification,
        "validation_label": exc.validation_label,
        "validation_errors": validation_errors,
        "formalizer_validation_feedback": validation_feedback,
        "rejected_candidate": last_invalid_packet,
        "rejected_candidate_complete": bool(last_invalid_packet),
        "rejected_candidate_fingerprint": rejected_candidate_fingerprint,
        "formalizer_recovery_checkpoint": recovery_checkpoint,
        "complete_current_source_checkpoint_provided": (
            complete_current_source_checkpoint_provided
        ),
        "attempt_history_ref": (
            {
                "artifact_id": attempt_history_id,
                "content_hash": attempt_history_hash,
                "n_rows": len(attempt_history_rows),
            }
            if attempt_history_id
            else {}
        ),
        "validation_boundary": validation_boundary,
        "proof_evidence_status": (
            "FORMALIZER_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }
    failure_artifact = {
        **feedback,
        "artifact_kind": "RuntimeFormalizerValidationFailure",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": _question_to_payload(question),
        "task_id": task.task_id,
        "theory_packet_id": theory_packet_id,
        "simulation_manifest_id": simulation_manifest_id,
        "algorithm_sandbox_manifest_id": algorithm_sandbox_manifest_id,
        "model_generation_attempts": max(0, int(exc.attempts or 0)),
        "client_tool_turns": (
            len(attempt_history_rows) if lean_workspace_observation_available else 0
        ),
        "boundary": (
            "This artifact records the exact model artifact available at failure "
            "and the raw environment observations. A complete structured rejected "
            "packet and a complete current model-authored source checkpoint are "
            "reported separately; neither is a runtime source edit or proof artifact."
        ),
    }
    result_rationale = (
        "The bounded model-owned Lean workspace exhausted its direct tool loop "
        "without a valid exact-target source. The runtime preserved its complete "
        "transcript, current source checkpoint, and raw observations as a blocker "
        "without launching a packet-regeneration session."
        if lean_workspace_observation_available
        else "Formalizer packet validation exhausted its model-owned structured "
        "generation budget. The runtime recorded the rejected packet and raw "
        "observations as a blocker without launching another generation session."
    )
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, failure_id])[:20],
        task_id=task.task_id,
        artifact_id=failure_id,
        evidence_type="formalizer_packet_validation_failure",
        status="VALIDATION_FAILED_RECORDED_NOT_PROOF_EVIDENCE",
        boundary=FORMALIZER_BOUNDARY,
        payload={
            "validation_errors": validation_errors,
            "same_owner_subsystem": task.owner_subsystem,
            "runtime_edits_candidate": False,
            **client_tool_loop_observation,
            "proof_evidence_status": (
                "FORMALIZER_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
            ),
        },
    )
    produced_artifacts = {
        str(artifact_id): deepcopy(dict(artifact))
        for artifact_id, artifact in (workspace_artifacts or {}).items()
        if str(artifact_id).strip() and isinstance(artifact, Mapping)
    }
    if attempt_history_id:
        produced_artifacts[attempt_history_id] = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "FormalizerAttemptHistory",
            "artifact_id": attempt_history_id,
            "content_hash": attempt_history_hash,
            "validation_label": exc.validation_label,
            "attempts": attempt_history_rows,
            "proof_evidence_status": (
                "FORMALIZER_ATTEMPT_HISTORY_NOT_PROOF_EVIDENCE"
            ),
        }
    produced_artifacts[failure_id] = failure_artifact
    return AgentStepResult(
        status="BLOCKED",
        rationale=result_rationale,
        produced_artifacts=produced_artifacts,
        observations=(
            EnvironmentObservation(
                observation_type="formalizer_packet_validation_failure",
                summary="; ".join(validation_errors)[:500],
                payload={
                    "failure_id": failure_id,
                    "validation_errors": validation_errors,
                    "same_owner_subsystem": task.owner_subsystem,
                    "runtime_edits_candidate": False,
                    **client_tool_loop_observation,
                    "proof_evidence_status": (
                        "FORMALIZER_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
                    ),
                },
            ),
        ),
        evidence_entries=(evidence,),
        next_task=None,
        failure_classification=failure_classification,
    )


def _materialize_formalizer_lean_candidate_artifacts(
    *,
    root: Path,
    question: OpenResearchQuestion,
    task: AgentTask,
    proposal_packet: Mapping[str, Any],
    local_lean: bool = False,
    lean_project: Path | None = None,
    lean_timeout: int = 30,
) -> dict[str, Any]:
    candidate_sources = _formalizer_lean_candidate_sources(proposal_packet)
    environment_feedback = (
        task.inputs.get("environment_feedback", {})
        if isinstance(task.inputs.get("environment_feedback", {}), Mapping)
        else {}
    )
    candidate_lineage_contract = build_candidate_lineage_contract(
        owner_subsystem=task.owner_subsystem,
        environment_feedback=environment_feedback,
        schema_version=RUNTIME_SCHEMA_VERSION,
        proof_evidence_boundary=KERNEL_PROOF_BOUNDARY,
    )
    architect_context = (
        task.inputs.get("architect_context", {})
        if isinstance(task.inputs.get("architect_context", {}), Mapping)
        else {}
    )
    structured_candidate_identity_required = bool(
        _runtime_context_requires_formalizer_lean_candidate(architect_context)
        or candidate_lineage_contract.get("required", False)
    )
    manifest_id = (
        "formalizer_lean_candidate_materialization:"
        + stable_hash([task.task_id, proposal_packet.get("packet_id", ""), candidate_sources])[:20]
    )
    artifact_dir = (
        root
        / _safe_identifier(question.id)
        / stable_hash([task.task_id, proposal_packet.get("packet_id", "")])[:12]
    )
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidate_sources, start=1):
        declared_lean_imports = [
            str(value).strip()
            for value in candidate.get("lean_imports", []) or []
            if str(value).strip()
        ]
        source = str(candidate.get("lean_source", "") or "").strip()
        candidate_id = str(candidate.get("candidate_id", "") or f"candidate_{index}")
        candidate_metadata = dict(candidate.get("candidate_metadata", {}) or {})
        candidate_lean_declaration = str(
            candidate.get("candidate_lean_declaration", "") or ""
        ).strip()
        source_boundary_errors = _formalizer_lean_candidate_source_boundary_errors(
            source,
        )
        identity_binding_errors: list[str] = []
        if not candidate_lean_declaration:
            if structured_candidate_identity_required:
                identity_binding_errors.append(
                    "Lean candidate missing structured candidate_lean_declaration; "
                    "AgentRuntime will not infer declaration identity from Lean source"
                )
        precheck_errors = sorted(
            set([*source_boundary_errors, *identity_binding_errors])
        )
        blocking_precheck_errors = list(source_boundary_errors)
        artifact_path = ""
        source_hash = stable_hash(source)
        if not blocking_precheck_errors:
            artifact_dir.mkdir(parents=True, exist_ok=True)
            path = artifact_dir / (
                f"{index:03d}_{_safe_identifier(candidate_id)}_{source_hash[:10]}.lean"
            )
            path.write_text(source, encoding="utf-8")
            artifact_path = str(path)
        proof_state_artifact_path = (
            _formalizer_lean_candidate_project_local_proof_state_artifact(
                source=source,
                lean_project=lean_project,
                question_id=question.id,
                task_id=task.task_id,
                candidate_id=candidate_id,
                source_hash=source_hash,
                index=index,
            )
            if artifact_path
            else ""
        )
        local_lean_result = (
            _run_formalizer_lean_candidate_local_check(
                artifact_path=Path(artifact_path),
                candidate_lean_declaration=candidate_lean_declaration,
                lean_project=lean_project,
                lean_timeout=lean_timeout,
            )
            if local_lean and artifact_path
            else {
                "local_lean_attempted": False,
                "local_lean_compiled": False,
                "local_lean_source_compiled": False,
                "local_lean_source_exit_status": "",
                "local_lean_exit_status": "",
                "local_lean_stdout": "",
                "local_lean_stderr": "",
                "local_lean_command": [],
                "local_lean_project": str(lean_project or ""),
                "local_lean_timeout": lean_timeout,
                "local_lean_skipped_reason": (
                    "local_lean_disabled"
                    if not local_lean
                    else "candidate_rejected_by_precheck_or_not_materialized"
                ),
                "candidate_identity_lean_checked": False,
                "candidate_identity_lean_verified": False,
                "candidate_identity_probe_artifact_path": "",
                "candidate_identity_lean_exit_status": "",
                "candidate_identity_lean_stdout": "",
                "candidate_identity_lean_stderr": "",
                "candidate_identity_lean_command": [],
            }
        )
        candidate_identity_lean_checked = _bool_like(
            local_lean_result.get("candidate_identity_lean_checked", False)
        )
        candidate_identity_lean_verified = _bool_like(
            local_lean_result.get("candidate_identity_lean_verified", False)
        )
        source_theorem_target_known = _source_theorem_target_known_value(
            candidate_metadata.get("source_theorem_target_provenance", {})
        )
        candidate_target_source = dict(candidate)
        candidate_target_source["candidate_metadata"] = candidate_metadata
        candidate_target_source["candidate_lean_declaration"] = (
            candidate_lean_declaration
        )
        candidate_target_source["target_lean_declaration"] = (
            candidate_lean_declaration
        )
        target_context = _formalizer_lean_candidate_target_context(
            candidate_target_source
        )
        candidate_lineage = evaluate_candidate_lineage(
            contract=candidate_lineage_contract,
            candidate_id=candidate_id,
            actual_target_lean_declaration=candidate_lean_declaration,
            target_context=target_context,
        )
        candidate_kind = str(candidate.get("candidate_kind", "") or "")
        formal_target_role, formal_target_role_source = (
            _formalizer_candidate_formal_target_role(candidate_target_source)
        )
        formal_target_role_unbound_not_source_theorem = bool(
            candidate_kind == "formal_target_lean_statement_sketch"
            and formal_target_role
            not in {
                FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
                FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT,
            }
        )
        support_candidate_not_source_theorem = (
            formal_target_role == FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT
        )
        diagnostic_helper_not_source_theorem = bool(
            formal_target_role == FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT
            or formal_target_role_unbound_not_source_theorem
        )
        target_identity_not_source_theorem = bool(
            candidate_lineage.get(
                "target_identity_mismatch_not_source_theorem",
                False,
            )
            or candidate_lineage.get(
                "target_identity_unbound_not_source_theorem",
                False,
            )
            or not candidate_lean_declaration
            or (
                candidate_identity_lean_checked
                and not candidate_identity_lean_verified
            )
        )
        structured_candidate_identity_available = bool(
            candidate_lean_declaration
        )
        source_theorem_candidate_evidence_eligible = (
            formal_target_role == FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE
            and source_theorem_target_known is not None
            and not diagnostic_helper_not_source_theorem
            and not support_candidate_not_source_theorem
            and not target_identity_not_source_theorem
            and (
                not candidate_identity_lean_checked
                or candidate_identity_lean_verified
            )
        )
        local_lean_compiled = _bool_like(
            local_lean_result.get("local_lean_compiled", False)
        )
        proof_evidence_status = _formalizer_candidate_proof_evidence_status(
            local_lean_compiled=local_lean_compiled,
            diagnostic_helper_not_source_theorem=(
                diagnostic_helper_not_source_theorem
            ),
            support_candidate_not_source_theorem=(
                support_candidate_not_source_theorem
            ),
            target_identity_not_source_theorem=target_identity_not_source_theorem,
        )
        rows.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "candidate_id": candidate_id,
                "candidate_kind": candidate_kind,
                "formal_target_role": formal_target_role,
                "formal_target_role_source": formal_target_role_source,
                "formal_target_role_unbound_not_source_theorem": (
                    formal_target_role_unbound_not_source_theorem
                ),
                "source_packet_id": str(proposal_packet.get("packet_id", "") or ""),
                "source_field": str(candidate.get("source_field", "") or ""),
                "source_hash": source_hash,
                "lean_imports": declared_lean_imports,
                "lean_environment_source": (
                    f"{str(candidate.get('source_field', '') or '')}.lean_imports"
                    if declared_lean_imports
                    else ""
                ),
                "lean_source": source,
                "lean_source_excerpt": source,
                "artifact_path": artifact_path,
                "kernel_check_artifact_path": artifact_path,
                "proof_state_artifact_path": proof_state_artifact_path,
                "target_lean_file": str(proof_state_artifact_path or artifact_path or ""),
                "target_lean_declaration": candidate_lean_declaration,
                "candidate_lean_declaration": candidate_lean_declaration,
                "candidate_lean_declaration_source": str(
                    candidate.get("candidate_lean_declaration_source", "") or ""
                ),
                "structured_candidate_identity_required": (
                    structured_candidate_identity_required
                ),
                "structured_candidate_identity_available": (
                    structured_candidate_identity_available
                ),
                "candidate_identity_lean_checked": (
                    candidate_identity_lean_checked
                ),
                "candidate_identity_lean_verified": (
                    candidate_identity_lean_verified
                ),
                "candidate_identity_probe_artifact_path": str(
                    local_lean_result.get(
                        "candidate_identity_probe_artifact_path",
                        "",
                    )
                    or ""
                ),
                "candidate_identity_lean_exit_status": str(
                    local_lean_result.get(
                        "candidate_identity_lean_exit_status",
                        "",
                    )
                    or ""
                ),
                "candidate_identity_lean_stdout": str(
                    local_lean_result.get(
                        "candidate_identity_lean_stdout",
                        "",
                    )
                    or ""
                ),
                "candidate_identity_lean_stderr": str(
                    local_lean_result.get(
                        "candidate_identity_lean_stderr",
                        "",
                    )
                    or ""
                ),
                "candidate_identity_lean_command": list(
                    local_lean_result.get(
                        "candidate_identity_lean_command",
                        [],
                    )
                    or []
                ),
                "target_ids": list(target_context.get("target_ids", []) or []),
                "target_theorem_goal_ids": list(
                    target_context.get("target_theorem_goal_ids", []) or []
                ),
                "target_theorem_name": str(
                    target_context.get("target_theorem_name", "") or ""
                ),
                "source_theorem_target_provenance": dict(
                    target_context.get("source_theorem_target_provenance", {})
                    or {}
                ),
                "precheck_status": (
                    "REJECTED_BY_RUNTIME_PRECHECK"
                    if blocking_precheck_errors
                    else (
                        "MATERIALIZED_WITH_PRECHECK_DIAGNOSTICS_REQUIRES_LOCAL_LEAN_OR_AXLE"
                        if precheck_errors
                        else "MATERIALIZED_REQUIRES_LOCAL_LEAN_OR_AXLE"
                    )
                ),
                "precheck_errors": precheck_errors,
                "blocking_precheck_errors": blocking_precheck_errors,
                "source_boundary_errors": source_boundary_errors,
                "identity_binding_errors": identity_binding_errors,
                "local_lean_attempted": _bool_like(
                    local_lean_result.get("local_lean_attempted", False)
                ),
                "local_lean_compiled": _bool_like(
                    local_lean_result.get("local_lean_compiled", False)
                ),
                "local_lean_source_compiled": _bool_like(
                    local_lean_result.get("local_lean_source_compiled", False)
                ),
                "local_lean_source_exit_status": str(
                    local_lean_result.get("local_lean_source_exit_status", "")
                    or ""
                ),
                "local_lean_exit_status": str(
                    local_lean_result.get("local_lean_exit_status", "") or ""
                ),
                "local_lean_stdout": str(
                    local_lean_result.get("local_lean_stdout", "") or ""
                ),
                "local_lean_stderr": str(
                    local_lean_result.get("local_lean_stderr", "") or ""
                ),
                "local_lean_command": list(
                    local_lean_result.get("local_lean_command", []) or []
                ),
                "local_lean_project": str(
                    local_lean_result.get("local_lean_project", "") or ""
                ),
                "local_lean_timeout": int(
                    local_lean_result.get("local_lean_timeout", lean_timeout) or lean_timeout
                ),
                "local_lean_skipped_reason": str(
                    local_lean_result.get("local_lean_skipped_reason", "") or ""
                ),
                **_formalizer_candidate_kernel_scope_fields(
                    local_lean_compiled=local_lean_compiled
                ),
                "source_theorem_target_known": source_theorem_target_known,
                "diagnostic_helper_not_source_theorem": (
                    diagnostic_helper_not_source_theorem
                ),
                "support_candidate_not_source_theorem": (
                    support_candidate_not_source_theorem
                ),
                **candidate_lineage,
                "source_theorem_candidate_evidence_eligible": (
                    source_theorem_candidate_evidence_eligible
                ),
                "proof_evidence_status": proof_evidence_status,
                "source_theorem_proof_evidence_status": (
                    _formalizer_candidate_source_theorem_proof_evidence_status(
                        local_lean_compiled=local_lean_compiled,
                        source_theorem_candidate_evidence_eligible=(
                            source_theorem_candidate_evidence_eligible
                        ),
                    )
                ),
                "boundary": (
                    _formalizer_candidate_proof_boundary(
                        diagnostic_helper_not_source_theorem=(
                            diagnostic_helper_not_source_theorem
                        ),
                        support_candidate_not_source_theorem=(
                            support_candidate_not_source_theorem
                        ),
                        target_identity_not_source_theorem=(
                            target_identity_not_source_theorem
                        ),
                    )
                ),
                "candidate_metadata": candidate_metadata,
            }
        )
    written_rows = [row for row in rows if row.get("artifact_path")]
    rejected_rows = [
        row
        for row in rows
        if row.get("precheck_status") == "REJECTED_BY_RUNTIME_PRECHECK"
    ]
    local_checked_rows = [
        row for row in rows if _bool_like(row.get("local_lean_attempted", False))
    ]
    local_compiled_rows = [
        row for row in rows if _bool_like(row.get("local_lean_compiled", False))
    ]
    compiled_source_candidate_rows = [
        row
        for row in local_compiled_rows
        if _bool_like(row.get("source_theorem_candidate_evidence_eligible", False))
    ]
    compiled_support_candidate_rows = [
        row
        for row in local_compiled_rows
        if _bool_like(row.get("support_candidate_not_source_theorem", False))
    ]
    compiled_diagnostic_helper_rows = [
        row
        for row in local_compiled_rows
        if _bool_like(row.get("diagnostic_helper_not_source_theorem", False))
    ]
    question_payload = _question_to_payload(question)
    manifest_path = (
        artifact_dir / "formalizer_lean_candidate_materialization_manifest.json"
        if candidate_sources
        else None
    )
    manifest_payload = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeFormalizerLeanCandidateMaterialization",
        "manifest_id": manifest_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": question_payload,
        "task_id": task.task_id,
        "task_owner_subsystem": task.owner_subsystem,
        "source_formalizer_packet_id": str(proposal_packet.get("packet_id", "") or ""),
        "candidate_lineage_contract": candidate_lineage_contract,
        "candidate_rows": rows,
        "n_candidate_sources": len(candidate_sources),
        "n_candidate_artifacts_written": len(written_rows),
        "n_precheck_rejected": len(rejected_rows),
        "local_lean_requested": bool(local_lean),
        "local_lean_attempted": bool(local_checked_rows),
        "n_local_lean_checked": len(local_checked_rows),
        "n_local_lean_compiled": len(local_compiled_rows),
        "n_local_lean_compiled_diagnostic_helpers": len(
            compiled_diagnostic_helper_rows
        ),
        "n_local_lean_compiled_support_candidates": len(
            compiled_support_candidate_rows
        ),
        "n_local_lean_compiled_source_theorem_candidates": len(
            compiled_source_candidate_rows
        ),
        "kernel_verified": False,
        "candidate_kernel_verified": bool(local_compiled_rows),
        "local_lean_compiled_observed": bool(local_compiled_rows),
        "candidate_kernel_verified_scope": "candidate_artifact_only",
        "candidate_kernel_verified_boundary": (
            FORMALIZER_LEAN_CANDIDATE_KERNEL_BOUNDARY
        ),
        "source_theorem_kernel_verified": False,
        "lean_project": str(lean_project or ""),
        "lean_timeout": lean_timeout,
        "artifact_dir": str(artifact_dir) if candidate_sources else "",
        "manifest_path": str(manifest_path or ""),
        "proof_evidence_status": (
            "FORMALIZER_LEAN_CANDIDATE_LOCAL_LEAN_KERNEL_VERIFIED"
            if compiled_source_candidate_rows
            else (
                "FORMALIZER_SUPPORT_LEAN_CANDIDATE_LOCAL_LEAN_KERNEL_VERIFIED_"
                "NOT_SOURCE_THEOREM_PROOF"
                if compiled_support_candidate_rows
                else (
                    "FORMALIZER_DIAGNOSTIC_HELPER_LOCAL_LEAN_KERNEL_VERIFIED_"
                    "NOT_SOURCE_THEOREM_PROOF"
                    if local_compiled_rows
                    else "FORMALIZER_LEAN_CANDIDATE_MATERIALIZATION_NOT_PROOF_EVIDENCE"
                )
            )
        ),
        "source_theorem_proof_evidence_status": (
            "SOURCE_THEOREM_CANDIDATE_REQUIRES_SEMANTIC_AUDIT"
            if compiled_source_candidate_rows
            else (
                "NOT_SOURCE_THEOREM_PROOF_EVIDENCE"
                if local_compiled_rows
                else "FORMALIZER_LEAN_CANDIDATE_MATERIALIZATION_NOT_PROOF_EVIDENCE"
            )
        ),
        "boundary": (
            "Formalizer Lean candidate materialization creates concrete files for "
            "ProofEngineer consumption. It is only kernel proof evidence for the "
            "exact candidate artifact. HELPER_OR_SUPPORT or role-unbound rows are "
            "diagnostic/support evidence only; source-to-bridge premise derivation "
            "candidates are support evidence only. No candidate proves the source "
            "theorem before semantic review and the source-theorem proof gate."
        ),
    }
    manifest_payload = _normalize_formalizer_lean_candidate_materialization_artifact(
        manifest_payload
    )
    if manifest_path is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest_payload, indent=2, default=str),
            encoding="utf-8",
        )
    return manifest_payload


def _formalizer_lean_candidate_project_local_proof_state_artifact(
    *,
    source: str,
    lean_project: Path | None,
    question_id: str,
    task_id: str,
    candidate_id: str,
    source_hash: str,
    index: int,
) -> str:
    """Mirror generated Lean inside the configured project for LSP-style tools.

    The runtime keeps the canonical candidate under ``runs/`` for audit and
    local-kernel replay. Lean LSP/MCP tools, however, usually require the file to
    have a Lean project ancestor. This ignored mirror is diagnostic/search
    context only; it is not a separate proof artifact.
    """

    if lean_project is None:
        return ""
    try:
        project = Path(lean_project)
        mirror_dir = (
            project
            / ".lake"
            / "ai_statistician_formalizer_candidates"
            / _safe_identifier(question_id)
            / stable_hash([task_id, source_hash])[:12]
        )
        mirror_dir.mkdir(parents=True, exist_ok=True)
        mirror_path = mirror_dir / (
            f"{index:03d}_{_safe_identifier(candidate_id)}_{source_hash[:10]}.lean"
        )
        mirror_path.write_text(source, encoding="utf-8")
        return str(mirror_path.resolve())
    except OSError:
        return ""


def _formalizer_candidate_proof_evidence_status(
    *,
    local_lean_compiled: bool,
    diagnostic_helper_not_source_theorem: bool,
    support_candidate_not_source_theorem: bool = False,
    target_identity_not_source_theorem: bool = False,
) -> str:
    if not local_lean_compiled:
        return "FORMALIZER_LEAN_CANDIDATE_MATERIALIZATION_NOT_PROOF_EVIDENCE"
    if support_candidate_not_source_theorem:
        return (
            "FORMALIZER_SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_"
            "LOCAL_LEAN_KERNEL_VERIFIED_SUPPORT_ONLY"
        )
    if diagnostic_helper_not_source_theorem:
        return (
            "FORMALIZER_DIAGNOSTIC_HELPER_LOCAL_LEAN_KERNEL_VERIFIED_"
            "NOT_SOURCE_THEOREM_PROOF"
        )
    if target_identity_not_source_theorem:
        return (
            "FORMALIZER_CANDIDATE_LINEAGE_DRIFT_LOCAL_LEAN_KERNEL_VERIFIED_"
            "CANDIDATE_ONLY"
        )
    return "FORMALIZER_LEAN_CANDIDATE_LOCAL_LEAN_KERNEL_VERIFIED"


def _formalizer_candidate_source_theorem_proof_evidence_status(
    *,
    local_lean_compiled: bool,
    source_theorem_candidate_evidence_eligible: bool,
) -> str:
    if not source_theorem_candidate_evidence_eligible:
        return "NOT_SOURCE_THEOREM_PROOF_EVIDENCE"
    if local_lean_compiled:
        return "SOURCE_THEOREM_CANDIDATE_REQUIRES_SEMANTIC_AUDIT"
    return "NOT_KERNEL_VERIFIED_SOURCE_THEOREM_PROOF_EVIDENCE"




def _formalizer_candidate_proof_boundary(
    *,
    diagnostic_helper_not_source_theorem: bool,
    support_candidate_not_source_theorem: bool = False,
    target_identity_not_source_theorem: bool = False,
) -> str:
    if support_candidate_not_source_theorem:
        return (
            "This row materializes an LLM-generated source-to-bridge premise "
            "derivation candidate. A local Lean compile verifies only that "
            "support lemma artifact; it is not proof evidence for the exact "
            "source theorem or any "
            "full frontier theorem."
        )
    if diagnostic_helper_not_source_theorem:
        return (
            "This row materializes an LLM-generated diagnostic/helper Lean "
            "candidate with source_theorem_target_known=false. A local Lean compile "
            "verifies only this helper artifact; it is not proof evidence for the "
            "source theorem or any full "
            "frontier theorem."
        )
    if target_identity_not_source_theorem:
        return (
            "This row materializes an LLM-generated repair whose declaration does "
            "not match, or cannot be uniquely bound to, the immutable parent target "
            "identity. A local Lean compile verifies only the emitted candidate "
            "artifact; it is not proof evidence for the parent source theorem."
        )
    return (
        "This row materializes an LLM-generated Lean candidate. It is proof "
        "evidence only when local_lean_compiled=true for this exact candidate "
        "artifact and still requires semantic/source-theorem faithfulness auditing "
        "before any source theorem proof claim."
    )


def _formalizer_candidate_kernel_scope_fields(
    *,
    local_lean_compiled: bool,
) -> dict[str, Any]:
    local_lean_compiled = _bool_like(local_lean_compiled)
    return {
        # Generic proof consumers must not treat an unreviewed statement as the
        # requested theorem merely because Lean compiled that candidate.
        "kernel_verified": False,
        "candidate_kernel_verified": local_lean_compiled,
        "local_lean_compiled_observed": local_lean_compiled,
        "candidate_kernel_verified_scope": "candidate_artifact_only",
        "candidate_kernel_verified_boundary": (
            FORMALIZER_LEAN_CANDIDATE_KERNEL_BOUNDARY
        ),
    }


def _formalizer_candidate_formal_target_role(
    candidate: Mapping[str, Any],
) -> tuple[str, str]:
    """Resolve routing metadata without inferring theorem semantics from Lean text."""

    metadata = (
        candidate.get("candidate_metadata", {})
        if isinstance(candidate.get("candidate_metadata", {}), Mapping)
        else {}
    )
    for source in (candidate, metadata):
        raw_role = str(source.get("formal_target_role", "") or "").strip()
        if not raw_role:
            continue
        role = raw_role.upper()
        if role in FORMAL_TARGET_ROLES:
            return role, "EXPLICIT"
        return "", "INVALID"

    target_known = _source_theorem_target_known_value(candidate)
    if target_known is None:
        for source in (candidate, metadata):
            provenance = source.get("source_theorem_target_provenance", {})
            target_known = _source_theorem_target_known_value(provenance)
            if target_known is not None:
                break
    if target_known is True:
        return FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE, "LEGACY_PROVENANCE"
    if target_known is False:
        return FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT, "LEGACY_PROVENANCE"
    return "", "UNBOUND"


def _normalize_formalizer_lean_candidate_materialization_artifact(
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = dict(artifact)
    manifest_candidate_lineage_contract = (
        dict(normalized.get("candidate_lineage_contract", {}) or {})
        if isinstance(
            normalized.get("candidate_lineage_contract", {}), Mapping
        )
        else {}
    )
    manifest_candidate_lineage_required = bool(
        _bool_like(normalized.get("candidate_lineage_required", False))
        or _bool_like(
            manifest_candidate_lineage_contract.get("required", False)
        )
    )
    candidate_rows = [
        row
        for row in normalized.get("candidate_rows", []) or []
        if isinstance(row, Mapping)
    ]
    rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        candidate = dict(row)
        candidate_kind = str(candidate.get("candidate_kind", "") or "")
        source_theorem_target_known = candidate.get("source_theorem_target_known", None)
        if source_theorem_target_known is not None:
            parsed_source_theorem_target_known = _source_theorem_target_known_value(
                {"source_theorem_target_known": source_theorem_target_known}
            )
            if parsed_source_theorem_target_known is not None:
                source_theorem_target_known = parsed_source_theorem_target_known
        if source_theorem_target_known is None:
            candidate_metadata = (
                candidate.get("candidate_metadata", {})
                if isinstance(candidate.get("candidate_metadata", {}), Mapping)
                else {}
            )
            source_theorem_target_known = _source_theorem_target_known_value(
                candidate_metadata.get("source_theorem_target_provenance", {})
            )
        formal_target_role, formal_target_role_source = (
            _formalizer_candidate_formal_target_role(candidate)
        )
        support_candidate_not_source_theorem = _bool_like(
            candidate.get("support_candidate_not_source_theorem", False)
        ) or formal_target_role == FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT
        formal_target_role_unbound_not_source_theorem = bool(
            candidate_kind == "formal_target_lean_statement_sketch"
            and formal_target_role
            not in {
                FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
                FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT,
            }
        )
        diagnostic_helper_not_source_theorem = _bool_like(
            candidate.get("diagnostic_helper_not_source_theorem", False)
        ) or bool(
            formal_target_role == FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT
            or formal_target_role_unbound_not_source_theorem
        )
        candidate_lineage_required = bool(
            _bool_like(candidate.get("candidate_lineage_required", False))
            or manifest_candidate_lineage_required
        )
        actual_target_lean_declaration = str(
            candidate.get("target_lean_declaration", "")
            or candidate.get("actual_target_lean_declaration", "")
            or ""
        ).strip()
        identity_contract = dict(manifest_candidate_lineage_contract)
        identity_contract["required"] = candidate_lineage_required
        candidate_lineage = evaluate_candidate_lineage(
            contract=identity_contract,
            candidate_id=str(candidate.get("candidate_id", "") or ""),
            actual_target_lean_declaration=actual_target_lean_declaration,
            target_context=_formalizer_lean_candidate_target_context(candidate),
        )
        expected_target_lean_declaration = str(
            candidate_lineage.get("expected_target_lean_declaration", "") or ""
        ).strip()
        target_identity_mismatch_not_source_theorem = _bool_like(
            candidate_lineage.get(
                "target_identity_mismatch_not_source_theorem",
                False,
            )
        )
        target_identity_unbound_not_source_theorem = _bool_like(
            candidate_lineage.get(
                "target_identity_unbound_not_source_theorem",
                False,
            )
        )
        target_identity_not_source_theorem = bool(
            target_identity_mismatch_not_source_theorem
            or target_identity_unbound_not_source_theorem
        )
        candidate_identity_lean_checked = _bool_like(
            candidate.get("candidate_identity_lean_checked", False)
        )
        candidate_identity_lean_verified = _bool_like(
            candidate.get("candidate_identity_lean_verified", False)
        )
        source_theorem_candidate_evidence_eligible = (
            formal_target_role == FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE
            and source_theorem_target_known is not None
            and not diagnostic_helper_not_source_theorem
            and not support_candidate_not_source_theorem
            and not target_identity_not_source_theorem
            and (
                not candidate_identity_lean_checked
                or candidate_identity_lean_verified
            )
        )
        local_lean_attempted = _bool_like(
            candidate.get("local_lean_attempted", False)
        )
        local_lean_compiled = _bool_like(candidate.get("local_lean_compiled", False))
        candidate["local_lean_attempted"] = local_lean_attempted
        candidate["local_lean_compiled"] = local_lean_compiled
        candidate["source_theorem_target_known"] = source_theorem_target_known
        candidate["formal_target_role"] = formal_target_role
        candidate["formal_target_role_source"] = formal_target_role_source
        candidate["formal_target_role_unbound_not_source_theorem"] = (
            formal_target_role_unbound_not_source_theorem
        )
        candidate["diagnostic_helper_not_source_theorem"] = (
            diagnostic_helper_not_source_theorem
        )
        candidate["support_candidate_not_source_theorem"] = (
            support_candidate_not_source_theorem
        )
        candidate.update(candidate_lineage)
        candidate["expected_target_lean_declaration"] = (
            expected_target_lean_declaration
        )
        candidate["actual_target_lean_declaration"] = (
            actual_target_lean_declaration
        )
        candidate["target_identity_mismatch_not_source_theorem"] = (
            target_identity_mismatch_not_source_theorem
        )
        candidate["target_identity_unbound_not_source_theorem"] = (
            target_identity_unbound_not_source_theorem
        )
        candidate["source_theorem_candidate_evidence_eligible"] = (
            source_theorem_candidate_evidence_eligible
        )
        candidate.update(
            _formalizer_candidate_kernel_scope_fields(
                local_lean_compiled=local_lean_compiled
            )
        )
        candidate["proof_evidence_status"] = _formalizer_candidate_proof_evidence_status(
            local_lean_compiled=local_lean_compiled,
            diagnostic_helper_not_source_theorem=(
                diagnostic_helper_not_source_theorem
            ),
            support_candidate_not_source_theorem=support_candidate_not_source_theorem,
            target_identity_not_source_theorem=target_identity_not_source_theorem,
        )
        candidate["source_theorem_proof_evidence_status"] = (
            _formalizer_candidate_source_theorem_proof_evidence_status(
                local_lean_compiled=local_lean_compiled,
                source_theorem_candidate_evidence_eligible=(
                    source_theorem_candidate_evidence_eligible
                ),
            )
        )
        candidate["boundary"] = _formalizer_candidate_proof_boundary(
            diagnostic_helper_not_source_theorem=diagnostic_helper_not_source_theorem,
            support_candidate_not_source_theorem=support_candidate_not_source_theorem,
            target_identity_not_source_theorem=target_identity_not_source_theorem,
        )
        rows.append(candidate)

    local_checked_rows = [
        row for row in rows if _bool_like(row.get("local_lean_attempted", False))
    ]
    local_compiled_rows = [
        row for row in rows if _bool_like(row.get("local_lean_compiled", False))
    ]
    compiled_source_candidate_rows = [
        row
        for row in local_compiled_rows
        if _bool_like(row.get("source_theorem_candidate_evidence_eligible", False))
    ]
    compiled_support_candidate_rows = [
        row
        for row in local_compiled_rows
        if _bool_like(row.get("support_candidate_not_source_theorem", False))
    ]
    compiled_diagnostic_helper_rows = [
        row
        for row in local_compiled_rows
        if _bool_like(row.get("diagnostic_helper_not_source_theorem", False))
    ]
    compiled_target_identity_drift_rows = [
        row
        for row in local_compiled_rows
        if _bool_like(
            row.get("target_identity_mismatch_not_source_theorem", False)
        )
        or _bool_like(
            row.get("target_identity_unbound_not_source_theorem", False)
        )
    ]
    formal_target_role_unbound_rows = [
        row
        for row in rows
        if _bool_like(
            row.get("formal_target_role_unbound_not_source_theorem", False)
        )
    ]
    normalized["candidate_rows"] = rows
    normalized["n_candidate_sources"] = len(rows)
    normalized["n_candidate_artifacts_written"] = len(
        [row for row in rows if row.get("artifact_path")]
    )
    normalized["n_precheck_rejected"] = len(
        [
            row
            for row in rows
            if row.get("precheck_status") == "REJECTED_BY_RUNTIME_PRECHECK"
        ]
    )
    normalized["local_lean_attempted"] = bool(local_checked_rows)
    normalized["n_local_lean_checked"] = len(local_checked_rows)
    normalized["n_local_lean_compiled"] = len(local_compiled_rows)
    normalized["n_local_lean_compiled_diagnostic_helpers"] = len(
        compiled_diagnostic_helper_rows
    )
    normalized["n_local_lean_compiled_support_candidates"] = len(
        compiled_support_candidate_rows
    )
    normalized["n_local_lean_compiled_source_theorem_candidates"] = len(
        compiled_source_candidate_rows
    )
    normalized["n_formal_target_role_unbound"] = len(
        formal_target_role_unbound_rows
    )
    normalized["n_local_lean_compiled_target_identity_drift_candidates"] = len(
        compiled_target_identity_drift_rows
    )
    normalized["candidate_lineage_required"] = (
        manifest_candidate_lineage_required
    )
    normalized["kernel_verified"] = False
    normalized["candidate_kernel_verified"] = bool(local_compiled_rows)
    normalized["local_lean_compiled_observed"] = bool(local_compiled_rows)
    normalized["candidate_kernel_verified_scope"] = "candidate_artifact_only"
    normalized["candidate_kernel_verified_boundary"] = (
        FORMALIZER_LEAN_CANDIDATE_KERNEL_BOUNDARY
    )
    normalized["source_theorem_kernel_verified"] = False
    normalized["proof_evidence_status"] = (
        "FORMALIZER_LEAN_CANDIDATE_LOCAL_LEAN_KERNEL_VERIFIED"
        if compiled_source_candidate_rows
        else (
            "FORMALIZER_SUPPORT_LEAN_CANDIDATE_LOCAL_LEAN_KERNEL_VERIFIED_"
            "NOT_SOURCE_THEOREM_PROOF"
            if compiled_support_candidate_rows
            else (
                "FORMALIZER_CANDIDATE_LINEAGE_DRIFT_LOCAL_LEAN_KERNEL_"
                "VERIFIED_CANDIDATE_ONLY"
                if compiled_target_identity_drift_rows
                else (
                    "FORMALIZER_DIAGNOSTIC_HELPER_LOCAL_LEAN_KERNEL_VERIFIED_"
                    "NOT_SOURCE_THEOREM_PROOF"
                    if compiled_diagnostic_helper_rows
                    else "FORMALIZER_LEAN_CANDIDATE_MATERIALIZATION_NOT_PROOF_EVIDENCE"
                )
            )
        )
    )
    normalized["source_theorem_proof_evidence_status"] = (
        "SOURCE_THEOREM_CANDIDATE_REQUIRES_SEMANTIC_AUDIT"
        if compiled_source_candidate_rows
        else (
            "NOT_SOURCE_THEOREM_PROOF_EVIDENCE"
            if local_compiled_rows
            else "FORMALIZER_LEAN_CANDIDATE_MATERIALIZATION_NOT_PROOF_EVIDENCE"
        )
    )
    normalized["boundary"] = (
        "Formalizer Lean candidate materialization creates concrete files for "
        "ProofEngineer consumption. It is only kernel proof evidence for the "
        "exact candidate artifact. Rows with source_theorem_target_known=false "
        "are diagnostic/helper evidence only; source-to-bridge premise "
        "derivation candidates and model revisions that drift from an "
        "immutable parent target are support evidence only. None of these "
        "categories proves the source theorem."
    )
    return normalized


def _runtime_task_hash_bound_artifact_ids(
    task: AgentTask | Mapping[str, Any] | None,
    artifacts: Mapping[str, Any],
) -> frozenset[str]:
    """Return the transitive artifact closure protected by persisted hashes."""

    if isinstance(task, AgentTask):
        task_payload: Any = asdict(task)
    elif isinstance(task, Mapping):
        task_payload = task
    else:
        task_payload = {}

    def bound_references(value: Any) -> list[str]:
        references: list[str] = []
        if isinstance(value, Mapping):
            if value.get("artifact_kind") == "RuntimeArtifactRef":
                artifact_id = str(value.get("artifact_id", "") or "").strip()
                content_hash = str(value.get("content_hash", "") or "").strip()
                artifact = artifacts.get(artifact_id)
                if (
                    artifact_id
                    and content_hash
                    and artifact is not None
                    and stable_hash(artifact) == content_hash
                ):
                    references.append(artifact_id)
            for raw_key, raw_id in value.items():
                key = str(raw_key)
                if not key.endswith("_id"):
                    continue
                hash_key = key[:-3] + "_hash"
                if not str(value.get(hash_key, "") or "").strip():
                    continue
                artifact_id = str(raw_id or "").strip()
                if artifact_id and artifact_id in artifacts:
                    references.append(artifact_id)
            for child in value.values():
                references.extend(bound_references(child))
        elif isinstance(value, (list, tuple)):
            for child in value:
                references.extend(bound_references(child))
        return references

    pending = list(dict.fromkeys(bound_references(task_payload)))
    protected: set[str] = set()
    while pending:
        artifact_id = pending.pop(0)
        if artifact_id in protected or artifact_id not in artifacts:
            continue
        protected.add(artifact_id)
        pending.extend(
            reference
            for reference in bound_references(artifacts[artifact_id])
            if reference not in protected
        )
    return frozenset(protected)


def _normalize_runtime_blackboard_artifacts(
    artifacts: Mapping[str, Any],
    *,
    architect_control_exempt_artifact_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Migrate rehydrated artifacts without mutating hash-bound metadata."""

    control_exempt_ids = {
        str(artifact_id)
        for artifact_id in architect_control_exempt_artifact_ids
        if str(artifact_id).strip()
    }
    normalized: dict[str, Any] = {}
    for artifact_id, artifact in artifacts.items():
        if (
            isinstance(artifact, Mapping)
            and str(artifact.get("artifact_kind", "") or "")
            == "RuntimeFormalizerLeanCandidateMaterialization"
        ):
            normalized[str(artifact_id)] = (
                _normalize_formalizer_lean_candidate_materialization_artifact(
                    artifact
                )
            )
        else:
            normalized[str(artifact_id)] = deepcopy(artifact)
    control_seed = _runtime_architect_control_seed_from_artifacts(normalized)
    if not control_seed:
        return normalized
    return {
        artifact_id: (
            artifact
            if artifact_id in control_exempt_ids
            else _runtime_artifact_with_architect_control(
                artifact_id,
                artifact,
                control_seed,
            )
        )
        for artifact_id, artifact in normalized.items()
    }


def _runtime_architect_control_seed_from_control(
    control: Any,
    *,
    control_source: str,
    require_architect_proposal_id: bool = False,
) -> dict[str, Any]:
    if not isinstance(control, Mapping):
        return {}
    contract = control.get("evidence_contract", {})
    if not isinstance(contract, Mapping) or not contract:
        return {}
    proposal_id = str(control.get("architect_coordinator_proposal_id", "") or "")
    if require_architect_proposal_id and not proposal_id:
        return {}
    return {
        "architect_coordinator_proposal_id": proposal_id,
        "evidence_contract": dict(contract),
        "formal_verification_policy": str(
            control.get("formal_verification_policy", "")
            or contract.get("formal_verification_policy", "")
            or ""
        ),
        "recommended_research_path": str(
            control.get("recommended_research_path", "")
            or contract.get("recommended_research_path", "")
            or ""
        ),
        "formal_required_for_final": _bool_like(
            control.get(
                "formal_required_for_final",
                contract.get("formal_required_for_final", False),
            )
        ),
        "control_source": control_source,
        "boundary": str(
            control.get("boundary", "")
            or "Architect control is orchestration metadata only; it does not "
            "prove a theorem, validate generated code, or close a formal gap."
        ),
    }


def _runtime_architect_control_seed_from_architect_proposal(
    artifact_id: str,
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    artifact_kind = str(artifact.get("artifact_kind", "") or "")
    if artifact_kind != "ArchitectCoordinatorProposalPacket" and not str(
        artifact_id
    ).startswith("architect_coordinator_proposal:"):
        return {}
    contract = artifact.get("evidence_contract", {})
    if not isinstance(contract, Mapping) or not contract:
        return {}
    proposal_id = str(
        artifact.get("packet_id", "")
        or artifact.get("proposal_id", "")
        or artifact_id
    )
    return {
        "architect_coordinator_proposal_id": proposal_id,
        "evidence_contract": dict(contract),
        "formal_verification_policy": str(
            contract.get("formal_verification_policy", "") or ""
        ),
        "recommended_research_path": str(
            contract.get("recommended_research_path", "") or ""
        ),
        "formal_required_for_final": _bool_like(
            contract.get("formal_required_for_final", False)
        ),
        "control_source": "architect_coordinator_proposal",
        "boundary": str(
            artifact.get("evidence_boundary", "")
            or artifact.get("boundary", "")
            or ARCHITECT_COORDINATOR_BOUNDARY
        ),
    }


def _runtime_architect_control_seed_from_artifacts(
    artifacts: Mapping[str, Any],
) -> dict[str, Any]:
    controlled_seed: dict[str, Any] = {}
    for artifact_id, artifact in artifacts.items():
        if not isinstance(artifact, Mapping):
            continue
        proposal_seed = _runtime_architect_control_seed_from_architect_proposal(
            str(artifact_id),
            artifact,
        )
        if proposal_seed:
            return proposal_seed
        if not controlled_seed:
            controlled_seed = _runtime_architect_control_seed_from_control(
                artifact.get("runtime_architect_control", {}),
                control_source="existing_runtime_architect_control",
                require_architect_proposal_id=True,
            )
    return controlled_seed


def _runtime_architect_control_seed_from_context(
    context: Any,
    *,
    subsystem: str,
) -> dict[str, Any]:
    if not isinstance(context, Mapping):
        return {}
    return _runtime_architect_control_seed_from_control(
        _architect_control_payload(context, subsystem),
        control_source="architect_context",
    )


def _runtime_architect_control_subsystem_for_artifact(
    artifact_id: str,
    artifact: Mapping[str, Any],
) -> str:
    for key in (
        "owner_subsystem",
        "subsystem",
        "source_subsystem",
        "producer_subsystem",
    ):
        value = str(artifact.get(key, "") or "").strip()
        if value:
            return value
    artifact_kind = str(artifact.get("artifact_kind", "") or "")
    kind_map = {
        "ArchitectCoordinatorProposalPacket": "ArchitectCoordinator",
        "RuntimeQuestionMetadata": "ArchitectCoordinator",
        "RuntimeRetrievalMemoryManifest": "RetrievalMemory",
        "TheoryDerivationPacket": "TheoryDeveloper",
        "RuntimeTheoryDerivationPacket": "TheoryDeveloper",
        "SimulationEngineerProposalPacket": "SimulationEvaluator",
        "RuntimeSimulationManifest": "SimulationEvaluator",
        "AlgorithmEngineerProposalPacket": "AlgorithmEngineer",
        "RuntimeAlgorithmSandboxManifest": "AlgorithmEngineer",
        "FormalizerProofEngineerProposalPacket": "FormalizationEvaluator",
        "RuntimeFormalizationManifest": "FormalizationEvaluator",
        "RuntimeFormalizerLeanCandidateMaterialization": "FormalizationEvaluator",
        "LeanCandidateRevisionClientToolLoop": "FormalizationEvaluator",
        "LeanCandidateClientToolWorkspace": "FormalizationEvaluator",
        "LeanKernelPromotionResult": "FormalizationEvaluator",
        "RuntimeCriticEvaluatorManifest": "CriticEvaluator",
    }
    if artifact_kind in kind_map:
        return kind_map[artifact_kind]
    artifact_id_text = str(artifact_id)
    prefix_map = (
        ("architect_coordinator_proposal:", "ArchitectCoordinator"),
        ("runtime_question_metadata:", "ArchitectCoordinator"),
        ("retrieval_memory_manifest:", "RetrievalMemory"),
        ("theory_derivation:", "TheoryDeveloper"),
        ("simulation_manifest:", "SimulationEvaluator"),
        ("algorithm_sandbox_manifest:", "AlgorithmEngineer"),
        ("formalizer_proposal:", "FormalizationEvaluator"),
        ("formalization_manifest:", "FormalizationEvaluator"),
        ("formalizer_lean_candidate_materialization:", "FormalizationEvaluator"),
        ("formalizer_lean_candidate_client_tool_loop:", "FormalizationEvaluator"),
        ("lean_kernel_promotion:", "FormalizationEvaluator"),
        ("critic_evaluator_manifest:", "CriticEvaluator"),
    )
    for prefix, subsystem in prefix_map:
        if artifact_id_text.startswith(prefix):
            return subsystem
    source_agent = str(artifact.get("source_agent", "") or "")
    if "Formalizer" in source_agent or "FormalizationEvaluator" in source_agent:
        return "FormalizationEvaluator"
    if "Simulation" in source_agent:
        return "SimulationEvaluator"
    if "Algorithm" in source_agent:
        return "AlgorithmEngineer"
    if "Theory" in source_agent:
        return "TheoryDeveloper"
    if "Critic" in source_agent:
        return "CriticEvaluator"
    if "Architect" in source_agent:
        return "ArchitectCoordinator"
    return artifact_kind or "unknown"


def _runtime_artifact_with_architect_control(
    artifact_id: str,
    artifact: Any,
    control_seed: Mapping[str, Any],
    *,
    subsystem_override: str = "",
) -> Any:
    if not isinstance(artifact, Mapping):
        return artifact
    contract = control_seed.get("evidence_contract", {})
    if not isinstance(contract, Mapping) or not contract:
        return deepcopy(dict(artifact))
    payload = deepcopy(dict(artifact))
    existing_control = payload.get("runtime_architect_control", {})
    control = dict(existing_control) if isinstance(existing_control, Mapping) else {}
    control_contract = control.get("evidence_contract", {})
    if not isinstance(control_contract, Mapping) or not control_contract:
        control["evidence_contract"] = dict(contract)
        control_contract = contract
    subsystem = str(subsystem_override or control.get("subsystem", "") or "").strip()
    if not subsystem:
        subsystem = _runtime_architect_control_subsystem_for_artifact(
            artifact_id,
            payload,
        )
    if not str(control.get("architect_coordinator_proposal_id", "") or "").strip():
        control["architect_coordinator_proposal_id"] = str(
            control_seed.get("architect_coordinator_proposal_id", "") or ""
        )
    control["subsystem"] = subsystem
    if not str(control.get("formal_verification_policy", "") or "").strip():
        control["formal_verification_policy"] = str(
            control_seed.get("formal_verification_policy", "")
            or control_contract.get("formal_verification_policy", "")
            or ""
        )
    if not str(control.get("recommended_research_path", "") or "").strip():
        control["recommended_research_path"] = str(
            control_seed.get("recommended_research_path", "")
            or control_contract.get("recommended_research_path", "")
            or ""
        )
    control["formal_required_for_final"] = _bool_like(
        control.get(
            "formal_required_for_final",
            control_seed.get(
                "formal_required_for_final",
                control_contract.get("formal_required_for_final", False),
            ),
        )
    )
    if not str(control.get("control_source", "") or "").strip():
        control["control_source"] = str(
            control_seed.get("control_source", "") or "runtime_architect_control"
        )
    control.setdefault("architect_control_propagated", True)
    if not str(control.get("boundary", "") or "").strip():
        control["boundary"] = str(
            control_seed.get("boundary", "")
            or "Architect control is orchestration metadata only; it does not "
            "prove a theorem, validate generated code, or close a formal gap."
    )
    payload["runtime_architect_control"] = control
    return payload


def _formalizer_lean_candidate_target_context(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Return canonical source-theorem target context for Lean-candidate memory."""

    metadata = (
        candidate.get("candidate_metadata", {})
        if isinstance(candidate.get("candidate_metadata", {}), Mapping)
        else {}
    )
    target_row: dict[str, Any] = {}
    source_target_provenance: dict[str, Any] = {}
    for source in (metadata, candidate):
        if not isinstance(source, Mapping):
            continue
        nested = source.get("source_theorem_target_provenance", {})
        if isinstance(nested, Mapping):
            source_target_provenance.update(
                {
                    str(key): value
                    for key, value in nested.items()
                    if value not in ("", [], {}, None)
                }
            )
        for key in (
            "target_ids",
            "target_id",
            "target_theorem_goal_ids",
            "source_theorem_goal_id",
            "target_theorem_name",
            "target_lean_declaration",
            "question_id",
            "source_theorem_question_id",
            "semantic_alignment_constraints",
            "source_theorem_target_known",
            "formal_target_role",
        ):
            if key in source and source.get(key) not in ("", [], {}, None):
                target_row.setdefault(key, source.get(key))
    if source_target_provenance:
        target_row["source_theorem_target_provenance"] = source_target_provenance
    target_ids = _source_theorem_target_ids_from_row(
        target_row,
        fallback_target_theorem_name=str(
            target_row.get("target_theorem_name", "") or ""
        ),
        fallback_source_formal_target_id=str(
            target_row.get("target_lean_declaration", "") or ""
        ),
    )
    source_target_provenance = _source_theorem_target_provenance_from_row(target_row)
    theorem_goal_ids = source_theorem_explicit_target_ids(target_row)
    if not theorem_goal_ids:
        theorem_goal_ids = [
            str(value).strip()
            for value in _str_tuple(target_row.get("target_theorem_goal_ids", []))
            if str(value).strip()
        ]
    if not theorem_goal_ids and str(
        target_row.get("target_theorem_name", "") or ""
    ).strip():
        theorem_goal_ids = [str(target_row.get("target_theorem_name", "") or "")]
    theorem_goal_ids = list(dict.fromkeys(theorem_goal_ids))
    target_theorem_name = str(target_row.get("target_theorem_name", "") or "")
    if not target_theorem_name:
        target_theorem_name = str(
            source_target_provenance.get("source_theorem_goal_id", "")
            or (theorem_goal_ids[0] if theorem_goal_ids else "")
            or ""
        )
    formal_target_role, formal_target_role_source = (
        _formalizer_candidate_formal_target_role(candidate)
    )
    return {
        "target_ids": target_ids,
        "target_theorem_goal_ids": list(theorem_goal_ids),
        "target_theorem_name": target_theorem_name,
        "source_theorem_target_provenance": source_target_provenance,
        "formal_target_role": formal_target_role,
        "formal_target_role_source": formal_target_role_source,
    }




def _formalizer_lean_candidate_revision_feedback(
    manifest: Mapping[str, Any],
    *,
    formal_source_retriever: Any | None = None,
    prior_environment_feedback: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return complete Lean tool observations to the source-producing model."""

    del formal_source_retriever
    candidate_rows = [
        deepcopy(dict(row))
        for row in manifest.get("candidate_rows", []) or []
        if isinstance(row, Mapping)
    ]
    compiled_non_diagnostic_rows = [
        row
        for row in candidate_rows
        if _bool_like(row.get("local_lean_compiled", False))
        and not _bool_like(row.get("diagnostic_helper_not_source_theorem", False))
    ]
    failed_rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        row["local_lean_attempted"] = _bool_like(
            row.get("local_lean_attempted", False)
        )
        row["local_lean_compiled"] = _bool_like(
            row.get("local_lean_compiled", False)
        )
        precheck_failed = str(row.get("precheck_status", "") or "") == (
            "REJECTED_BY_RUNTIME_PRECHECK"
        )
        precheck_diagnostic_failed = bool(
            str(row.get("precheck_status", "") or "")
            == "MATERIALIZED_WITH_PRECHECK_DIAGNOSTICS_REQUIRES_LOCAL_LEAN_OR_AXLE"
            and row.get("precheck_errors", [])
        )
        local_lean_failed = bool(
            _bool_like(row.get("local_lean_attempted", False))
            and not _bool_like(row.get("local_lean_compiled", False))
        )
        target_identity_failed = bool(
            not _bool_like(row.get("diagnostic_helper_not_source_theorem", False))
            and not _bool_like(row.get("support_candidate_not_source_theorem", False))
            and (
                _bool_like(
                    row.get("target_identity_mismatch_not_source_theorem", False)
                )
                or _bool_like(
                    row.get("target_identity_unbound_not_source_theorem", False)
                )
            )
        )
        if (
            _bool_like(row.get("diagnostic_helper_not_source_theorem", False))
            and compiled_non_diagnostic_rows
            and (precheck_failed or precheck_diagnostic_failed or local_lean_failed)
        ):
            continue
        if not (
            precheck_failed
            or precheck_diagnostic_failed
            or local_lean_failed
            or target_identity_failed
        ):
            continue
        if not str(row.get("lean_source", "") or ""):
            source = str(row.get("lean_source_excerpt", "") or "")
            artifact_path = str(row.get("artifact_path", "") or "")
            if not source and artifact_path:
                try:
                    source = Path(artifact_path).expanduser().read_text(
                        encoding="utf-8"
                    )
                except OSError:
                    source = ""
            if source:
                row["lean_source"] = source
        failed_rows.append(row)
    if not failed_rows:
        return None

    prior_feedback = coding_agent_observations_only(
        prior_environment_feedback
        if isinstance(prior_environment_feedback, Mapping)
        else {}
    )
    prior_context = (
        deepcopy(dict(prior_feedback.get("formalizer_workspace_context", {}) or {}))
        if isinstance(
            prior_feedback.get("formalizer_workspace_context", {}),
            Mapping,
        )
        else {}
    )
    current_context = _formalizer_candidate_workspace_context(
        manifest=manifest,
        diagnostics=failed_rows,
    )
    candidate_context = {**prior_context, **current_context}
    for runtime_authored_strategy_field in (
        "owner_subsystem",
        "repair_scope",
        "required_behavior",
        "acceptance_gate",
        "proof_body_generation_contract",
        "proof_search_role",
    ):
        candidate_context.pop(runtime_authored_strategy_field, None)
    candidate_context.update(
        {
            "context_kind": "model_owned_complete_lean_revision_observations",
            "model_owns_next_action": True,
            "runtime_selected_source_edit": False,
            "routing_authority_after_revision_budget": (
                "ArchitectCoordinator_model_packet"
            ),
        }
    )

    feedback = {
        "schema_version": manifest.get("schema_version", RUNTIME_SCHEMA_VERSION),
        "source_artifact_kind": str(manifest.get("artifact_kind", "") or ""),
        "source_manifest_id": str(manifest.get("manifest_id", "") or ""),
        "source_manifest_path": str(manifest.get("manifest_path", "") or ""),
        "question": deepcopy(manifest.get("question", {})),
        "task_id": str(manifest.get("task_id", "") or ""),
        "source_formalizer_packet_id": str(
            manifest.get("source_formalizer_packet_id", "") or ""
        ),
        "n_candidate_sources": len(candidate_rows),
        "n_candidate_artifacts_written": int(
            manifest.get("n_candidate_artifacts_written", 0) or 0
        ),
        "n_precheck_rejected": int(manifest.get("n_precheck_rejected", 0) or 0),
        "n_local_lean_checked": int(
            manifest.get("n_local_lean_checked", 0) or 0
        ),
        "n_local_lean_compiled": int(
            manifest.get("n_local_lean_compiled", 0) or 0
        ),
        "feedback_id": (
            "formalizer_lean_candidate_observation:"
            + stable_hash(
                [
                    manifest.get("manifest_id", ""),
                    failed_rows,
                    prior_feedback,
                ]
            )[:20]
        ),
        "feedback_type": "formalizer_lean_candidate_local_lean_feedback",
        "failure_classification": "formalizer_lean_candidate_tool_rejected",
        "candidate_rows": candidate_rows,
        "candidate_diagnostics": failed_rows,
        "formalizer_workspace_context": candidate_context,
        "model_owned_complete_source_regeneration": True,
        "runtime_selected_source_edit": False,
        "proof_evidence_status": (
            "FORMALIZER_LEAN_CANDIDATE_TOOL_OBSERVATIONS_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }
    if prior_feedback:
        feedback["prior_environment_feedback"] = prior_feedback
    return feedback


def _formalizer_candidate_workspace_context(
    *,
    manifest: Mapping[str, Any],
    diagnostics: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind a hash-verified complete candidate to downstream tool observations.

    Lean owns declaration grammar and elaboration. This function checks only
    artifact identity, immutable source hashes, and typed target lineage; it
    neither parses proof bodies nor proposes a proof strategy.
    """

    question = (
        manifest.get("question", {})
        if isinstance(manifest.get("question", {}), Mapping)
        else {}
    )
    question_id = str(question.get("id", "") or "").strip()
    for diagnostic in diagnostics:
        if (
            _bool_like(
                diagnostic.get("diagnostic_helper_not_source_theorem", False)
            )
            or _bool_like(
                diagnostic.get("support_candidate_not_source_theorem", False)
            )
            or _bool_like(
                diagnostic.get(
                    "target_identity_mismatch_not_source_theorem",
                    False,
                )
            )
            or _bool_like(
                diagnostic.get(
                    "target_identity_unbound_not_source_theorem",
                    False,
                )
            )
            or not _bool_like(
                diagnostic.get(
                    "source_theorem_candidate_evidence_eligible",
                    False,
                )
            )
        ):
            continue

        formal_target_role, formal_target_role_source = (
            _formalizer_candidate_formal_target_role(diagnostic)
        )
        if (
            formal_target_role
            != FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE
            or str(diagnostic.get("source_field", "") or "").strip()
            != "formal_targets"
            or _bool_like(
                diagnostic.get(
                    "formal_target_role_unbound_not_source_theorem",
                    False,
                )
            )
        ):
            continue

        provenance = (
            dict(diagnostic.get("source_theorem_target_provenance", {}) or {})
            if isinstance(
                diagnostic.get("source_theorem_target_provenance", {}),
                Mapping,
            )
            else {}
        )
        target_known = _source_theorem_target_known_value(diagnostic)
        if target_known is None:
            target_known = _source_theorem_target_known_value(provenance)
        if target_known is None:
            continue

        target_declaration = str(
            diagnostic.get("actual_target_lean_declaration", "")
            or diagnostic.get("target_lean_declaration", "")
            or ""
        ).strip()
        expected_declaration = str(
            diagnostic.get("expected_target_lean_declaration", "")
            or target_declaration
        ).strip()
        target_ids = tuple(
            dict.fromkeys(
                str(value).strip()
                for value in diagnostic.get("target_ids", []) or []
                if str(value).strip()
            )
        )
        artifact_path_text = str(
            diagnostic.get("artifact_path", "") or ""
        ).strip()
        expected_source_hash = str(
            diagnostic.get("source_hash", "") or ""
        ).strip()
        identity_errors = tuple(
            str(value).strip()
            for value in diagnostic.get("target_identity_errors", []) or []
            if str(value).strip()
        )
        if (
            not target_declaration
            or not expected_declaration
            or expected_declaration != target_declaration
            or not target_ids
            or not artifact_path_text
            or not expected_source_hash
            or identity_errors
        ):
            continue
        if (
            _bool_like(diagnostic.get("candidate_lineage_required", False))
            and str(
                diagnostic.get("candidate_lineage_binding_status", "")
                or ""
            )
            != "BOUND"
        ):
            continue

        artifact_path = Path(artifact_path_text).expanduser()
        try:
            source = artifact_path.read_text(encoding="utf-8")
        except OSError:
            continue
        if stable_hash(source) != expected_source_hash:
            continue

        provenance.update(
            {
                "source_theorem_target_known": target_known is True,
                "formal_target_role": formal_target_role,
                "target_lean_declaration": target_declaration,
                "target_ids": list(target_ids),
            }
        )
        if question_id:
            provenance["source_theorem_question_id"] = question_id

        def string_tuple(value: Any) -> tuple[str, ...]:
            values = value if isinstance(value, (list, tuple, set)) else [value]
            return tuple(
                dict.fromkeys(
                    str(item).strip()
                    for item in values
                    if str(item or "").strip()
                )
            )

        compiler_diagnostics = string_tuple(
            [
                *(diagnostic.get("precheck_errors", []) or []),
                diagnostic.get("local_lean_stdout_excerpt", ""),
                diagnostic.get("local_lean_stderr_excerpt", ""),
            ]
        )
        exit_status = str(
            diagnostic.get("local_lean_exit_status", "") or ""
        ).strip()
        try:
            compiler_returncode = int(exit_status)
        except ValueError:
            compiler_returncode = -1
        target_statement = str(
            diagnostic.get("target_theorem_statement", "") or source
        )
        lineage_payload = {
            "lineage_candidate_artifact_path": artifact_path_text,
            "lineage_candidate_artifact_hash": expected_source_hash,
            "target_declaration_source_hash": expected_source_hash,
            "target_theorem_statement_hash": (
                lean_target_statement_hash(target_statement)
            ),
            "target_theorem_statement_hash_algorithm": (
                LEAN_TARGET_STATEMENT_HASH_ALGORITHM
            ),
            "expected_target_lean_declaration": expected_declaration,
            "target_lean_declaration": target_declaration,
            "target_ids": list(target_ids),
        }
        context = {
            "context_kind": "model_owned_complete_lean_candidate",
            "candidate_id": str(diagnostic.get("candidate_id", "") or ""),
            "target_lean_declaration": target_declaration,
            "target_ids": list(target_ids),
            "source_theorem_target_known": target_known is True,
            "source_theorem_target_identity_status": (
                "SOURCE_THEOREM_TARGET_KNOWN"
                if target_known is True
                else "GENERATED_FORMAL_TARGET_PENDING_SEMANTIC_REVIEW"
            ),
            "source_theorem_target_provenance": provenance,
            **lineage_payload,
            "source_lineage_id": lean_source_lineage_id(
                lineage_payload
            ),
            "target_identity_status": "TARGET_DECLARATION_MATCHED",
            "target_identity_errors": list(identity_errors),
            "target_identity_source": (
                "runtime_formalizer_candidate_artifact_and_upstream_target"
            ),
            "source_theorem_kernel_evidence_eligible": False,
            "candidate_artifact_path": artifact_path_text,
            "source_candidate_artifact_path": artifact_path_text,
            "candidate_source": source,
            "target_theorem_statement": target_statement,
            "semantic_alignment_constraints": list(
                string_tuple(
                    provenance.get("semantic_alignment_constraints", [])
                )
            ),
            "semantic_alignment_blockers": list(
                string_tuple(provenance.get("semantic_alignment_blockers", []))
            ),
            "compiler_feedback": {
                "provider": "configured_local_lean_or_lsp",
                "checked": _bool_like(
                    diagnostic.get("local_lean_attempted", False)
                ),
                "returncode": compiler_returncode,
                "diagnostics": list(compiler_diagnostics),
                "candidate_artifact_hash": expected_source_hash,
            },
            "proof_evidence_status": (
                "MODEL_OWNED_COMPLETE_LEAN_CANDIDATE_NOT_PROOF_EVIDENCE"
            ),
        }
        return {
            **context,
            "formal_target_role": formal_target_role,
            "formal_target_role_source": formal_target_role_source,
            "formalizer_candidate_exact_search_eligible": True,
            "formalizer_candidate_semantic_review_status": (
                "INDEPENDENT_SEMANTIC_FAITHFULNESS_REVIEW_REQUIRED"
            ),
            "source_theorem_promotion_blockers": [
                "A Formalizer-generated declaration requires independent semantic "
                "faithfulness review before it can be promoted as the source theorem."
            ],
        }
    return {}


def _formalizer_compiled_exact_candidate_semantic_review_feedback(
    manifest: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Bind an already-compiling exact candidate to whole-target review.

    Local Lean establishes only that the generated artifact compiles. The same
    immutable target must still pass independent mathematical review before it
    can enter the source-theorem kernel promotion gate.
    """

    compiled_exact_rows = [
        dict(row)
        for row in manifest.get("candidate_rows", []) or []
        if isinstance(row, Mapping)
        and _bool_like(row.get("local_lean_compiled", False))
        and _bool_like(
            row.get("source_theorem_candidate_evidence_eligible", False)
        )
        and not _bool_like(
            row.get("diagnostic_helper_not_source_theorem", False)
        )
        and not _bool_like(row.get("support_candidate_not_source_theorem", False))
    ]
    if not compiled_exact_rows:
        return None
    context = _formalizer_candidate_workspace_context(
        manifest=manifest,
        diagnostics=compiled_exact_rows,
    )
    if not context:
        return None
    for runtime_authored_strategy_field in (
        "owner_subsystem",
        "repair_scope",
        "required_behavior",
        "acceptance_gate",
        "proof_body_generation_contract",
        "proof_search_role",
    ):
        context.pop(runtime_authored_strategy_field, None)
    return {
        "feedback_type": "formal_target_semantic_review_required_feedback",
        "failure_classification": (
            "formal_target_semantic_review_required_before_kernel_promotion"
        ),
        "source_manifest_id": str(manifest.get("manifest_id", "") or ""),
        "formalizer_workspace_context": context,
        "required_review": (
            "Independently compare the exact theorem statement and full Lean "
            "source with the question, TheoryDeveloper derivation, assumptions, "
            "quantifiers, conclusion, and semantic constraints."
        ),
        "proof_evidence_status": (
            "COMPILED_FORMAL_TARGET_REQUIRES_SEMANTIC_REVIEW_NOT_SOURCE_PROOF"
        ),
        "proof_evidence_boundary": FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
    }


def _formalizer_environment_feedback_with_formal_source_grounding(
    feedback: Mapping[str, Any] | None,
    *,
    formal_source_retriever: Any | None = None,
) -> dict[str, Any]:
    """Attach bounded formal-source grounding to carried observations."""

    payload = dict(feedback) if isinstance(feedback, Mapping) else {}
    payload = (
        _formalizer_environment_feedback_with_refreshed_validation_feedback(
            payload
        )
    )
    workspace_context = (
        payload.get("formalizer_workspace_context", {})
        if isinstance(payload.get("formalizer_workspace_context", {}), Mapping)
        else {}
    )
    if not workspace_context:
        return payload
    payload["formalizer_workspace_context"] = (
        _formalizer_workspace_context_with_formal_source_grounding(
            workspace_context,
            formal_source_retriever=formal_source_retriever,
        )
    )
    return payload

def _formalizer_environment_feedback_with_refreshed_validation_feedback(
    feedback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Keep exact validator observations available on carried pending tasks."""

    payload = dict(feedback) if isinstance(feedback, Mapping) else {}
    validation_errors = _feedback_text_values(payload.get("validation_errors", []))
    if not validation_errors:
        return payload
    existing = payload.get("formalizer_validation_feedback", {})
    if (
        isinstance(existing, Mapping)
        and list(existing.get("validation_error_messages", []) or [])
        == validation_errors
    ):
        return payload
    payload["formalizer_validation_feedback"] = (
        formalizer_validation_feedback_envelope(
            validation_errors,
            validation_label=str(payload.get("validation_label", "") or ""),
            retry_depth=0,
        )
    )
    return payload


def _feedback_text_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Mapping):
        return [json.dumps(value, sort_keys=True, default=str)]
    if isinstance(value, Iterable):
        return [str(item) for item in value if str(item).strip()]
    text = str(value)
    return [text] if text.strip() else []


def _formalizer_environment_feedback_formal_source_grounding_summary(
    feedback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize prompt-time formal-source grounding without serializing prompts."""

    if not isinstance(feedback, Mapping):
        return {}
    workspace_context = feedback.get("formalizer_workspace_context", {})
    if not isinstance(workspace_context, Mapping):
        return {}
    groups = [
        group
        for group in workspace_context.get("formal_source_grounding_hits", []) or []
        if isinstance(group, Mapping)
    ]
    if not groups:
        return {}
    top_hit_names: list[str] = []
    n_hits = 0
    for group in groups:
        hits = [hit for hit in group.get("hits", []) or [] if isinstance(hit, Mapping)]
        n_hits += len(hits)
        for hit in hits:
            name = str(hit.get("name", "") or "").strip()
            if name and name not in top_hit_names:
                top_hit_names.append(name)
            if len(top_hit_names) >= 8:
                break
        if len(top_hit_names) >= 8:
            break
    return {
        "n_formal_source_grounding_query_groups": len(groups),
        "n_formal_source_grounding_hits": n_hits,
        "n_duplicate_formal_source_grounding_hits_omitted": sum(
            int(group.get("duplicate_hits_omitted", 0) or 0)
            for group in groups
        ),
        "query_roles": [
            str(group.get("query_role", "") or "")
            for group in groups[:5]
            if str(group.get("query_role", "") or "")
        ],
        "query_fingerprints": [
            str(group.get("query_fingerprint", "") or "")
            for group in groups[:5]
            if str(group.get("query_fingerprint", "") or "")
        ],
        "unknown_identifiers": [
            str(group.get("unknown_identifier", "") or "")
            for group in groups[:5]
            if str(group.get("unknown_identifier", "") or "")
        ],
        "top_hit_names": top_hit_names,
        "proof_evidence_status": (
            "FORMAL_SOURCE_RETRIEVAL_GROUNDING_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _formalizer_workspace_context_with_formal_source_grounding(
    context: Mapping[str, Any],
    *,
    formal_source_retriever: Any | None = None,
) -> dict[str, Any]:
    """Run model/task-selected formal-source queries without treating hits as proof."""

    payload = dict(context) if isinstance(context, Mapping) else {}
    query_seeds = [
        str(seed).strip()
        for seed in payload.get("retrieval_query_seeds", []) or []
        if str(seed).strip()
    ]
    source_scope_ids = _formalizer_formal_source_scope_ids(payload)
    if (
        not source_scope_ids
        and str(payload.get("context_kind", "") or "")
        == "task_bound_formal_source_grounding"
    ):
        source_scope_ids = (
            active_project_formal_source_scope_ids(
                getattr(
                    formal_source_retriever,
                    "lean_rag_source_topology",
                    (),
                )
            )
        )
        if source_scope_ids:
            payload["formal_source_scope_ids"] = list(source_scope_ids)
            payload["formal_source_scope_origin"] = (
                "retriever_active_project_topology_default"
            )
            payload["formal_source_scope_policy"] = (
                "active_project_plus_declared_dependencies_first"
            )
    semantic_query_role = (
        "initial_formalization_context"
        if str(payload.get("context_kind", "") or "")
        == "task_bound_formal_source_grounding"
        else "model_or_task_selected_query"
    )
    query_rows = _formalizer_formal_source_query_rows(
        query_seeds=query_seeds,
        semantic_query_role=semantic_query_role,
    )
    existing_groups = [
        dict(group)
        for group in payload.get("formal_source_grounding_hits", []) or []
        if isinstance(group, Mapping)
    ]
    existing_groups_are_current = (
        existing_groups
        and _formalizer_formal_source_grounding_matches_query_rows(
            existing_groups,
            query_rows=query_rows,
            source_scope_ids=source_scope_ids,
        )
    )
    if existing_groups and existing_groups_are_current:
        grounded = _formalizer_workspace_context_ordered_with_formal_source_grounding(
            payload,
            immediate_fields={"formal_source_grounding_hits": existing_groups},
        )
        return attach_ai4slt_proof_state_trace_rag(
            grounded,
            formal_source_retriever=formal_source_retriever,
        )
    if formal_source_retriever is None:
        if existing_groups and query_rows:
            payload.pop("formal_source_grounding_hits", None)
            payload["formal_source_grounding_status"] = (
                "stale_hits_removed_retriever_unavailable"
            )
        return attach_ai4slt_proof_state_trace_rag(payload)
    groups = _formalizer_formal_source_grounding_hit_groups(
        formal_source_retriever,
        query_seeds=query_seeds,
        source_scope_ids=source_scope_ids,
        semantic_query_role=semantic_query_role,
    )
    if not groups:
        return attach_ai4slt_proof_state_trace_rag(
            payload,
            formal_source_retriever=formal_source_retriever,
        )
    trailing_fields: dict[str, Any] = {}
    trailing_fields["formal_source_grounding_policy"] = (
        "Formal-source retrieval hits are API/premise suggestions for the "
        "ProofEngineer loop, not proof evidence. Every selected declaration or "
        "replacement must still be checked by the configured local Lean/AXLE gate; "
        "if no verified replacement exists, emit a FORMAL_GAP naming the missing "
        "API/dependency."
    )
    trailing_fields["formal_source_grounding_status"] = (
        "retrieved_hits"
        if any(group.get("hits") for group in groups)
        else "retrieval_attempted_no_hits"
    )
    grounded = _formalizer_workspace_context_ordered_with_formal_source_grounding(
        payload,
        immediate_fields={"formal_source_grounding_hits": groups},
        trailing_fields=trailing_fields,
    )
    return attach_ai4slt_proof_state_trace_rag(
        grounded,
        formal_source_retriever=formal_source_retriever,
    )


def _formalizer_workspace_context_ordered_with_formal_source_grounding(
    context: Mapping[str, Any],
    *,
    immediate_fields: Mapping[str, Any],
    trailing_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Keep compact prompt-visible grounding next to retrieval query seeds."""

    trailing_fields = trailing_fields or {}
    insert_after_key = "retrieval_query_seeds"
    ordered: dict[str, Any] = {}
    inserted = False
    grounding_keys = set(immediate_fields) | set(trailing_fields)
    for key, value in context.items():
        if key in grounding_keys:
            continue
        ordered[key] = value
        if key == insert_after_key:
            ordered.update(dict(immediate_fields))
            inserted = True
    if not inserted:
        ordered.update(dict(immediate_fields))
    ordered.update(dict(trailing_fields))
    return ordered


def _formalizer_formal_source_grounding_hit_groups(
    formal_source_retriever: Any,
    *,
    query_seeds: Sequence[str],
    source_scope_ids: Sequence[str] = (),
    semantic_query_role: str = "model_or_task_selected_query",
    k: int = 2,
    max_groups: int = 3,
) -> list[dict[str, Any]]:
    query_rows = _formalizer_formal_source_query_rows(
        query_seeds=query_seeds,
        semantic_query_role=semantic_query_role,
    )
    groups: list[dict[str, Any]] = []
    seen_queries: set[str] = set()
    seen_hit_keys: set[tuple[str, str, str, str]] = set()
    normalized_source_scopes = tuple(
        dict.fromkeys(
            str(value).strip()
            for value in source_scope_ids
            if str(value).strip()
        )
    )
    for row in query_rows:
        query = str(row.get("query", "") or "").strip()
        if not query or query in seen_queries:
            continue
        seen_queries.add(query)
        group: dict[str, Any] = {
            "query": query,
            "query_role": row.get("query_role", ""),
            "query_fingerprint": stable_hash(query),
            "proof_evidence_status": (
                "FORMAL_SOURCE_RETRIEVAL_GROUNDING_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        }
        if row.get("unknown_identifier"):
            group["unknown_identifier"] = row["unknown_identifier"]
        if normalized_source_scopes:
            group["source_scope_ids"] = list(normalized_source_scopes)
            group["source_scope_semantics"] = (
                "main_retrieval_allowlist_with_anchor_scoped_support_corpora"
            )
        try:
            scoped_search = getattr(
                formal_source_retriever,
                "search_with_source_scope",
                None,
            )
            if normalized_source_scopes and callable(scoped_search):
                hits = scoped_search(
                    query,
                    source_scope_ids=normalized_source_scopes,
                    k=k,
                )
            else:
                hits = formal_source_retriever.search(query, k=k)
                if normalized_source_scopes:
                    raw_hits = list(hits)
                    allowed_source_ids = set(normalized_source_scopes)
                    hits = [
                        hit
                        for hit in raw_hits
                        if str(
                            getattr(
                                getattr(hit, "declaration", None),
                                "source_id",
                                "",
                            )
                            or ""
                        )
                        in allowed_source_ids
                    ]
                    group["source_scope_enforcement"] = (
                        "runtime_unscoped_fallback_filtered_by_source_allowlist"
                    )
                    group["n_out_of_scope_hits_dropped"] = (
                        len(raw_hits) - len(hits)
                    )
        except Exception as exc:  # pragma: no cover - defensive runtime path
            group["hits"] = []
            group["retrieval_error"] = type(exc).__name__ + ": " + str(exc)[:240]
        else:
            context_hit_limit = 2 if normalized_source_scopes else 1
            unique_hits, duplicate_hit_count = unique_formal_source_hit_payloads(
                [
                    _formal_source_hit_to_json(
                        hit,
                        formal_source_retriever=(
                            formal_source_retriever
                            if index < context_hit_limit
                            else None
                        ),
                    )
                    for index, hit in enumerate(hits)
                ],
                seen_hit_keys=seen_hit_keys,
            )
            group["hits"] = unique_hits
            if duplicate_hit_count:
                group["duplicate_hits_omitted"] = duplicate_hit_count
        groups.append(group)
        if len(groups) >= max_groups:
            break
    return groups


def _formalizer_formal_source_query_rows(
    *,
    query_seeds: Sequence[str],
    semantic_query_role: str = "model_or_task_selected_query",
) -> list[dict[str, str]]:
    """Preserve model/task-selected query strings and their order exactly."""

    rows = [
        {
            "query": str(seed).strip(),
            "query_role": str(semantic_query_role).strip()
            or "model_or_task_selected_query",
            "unknown_identifier": "",
        }
        for seed in query_seeds
        if str(seed).strip()
    ]
    unique_rows: list[dict[str, str]] = []
    seen_queries: set[str] = set()
    for row in rows:
        query = row["query"]
        if query in seen_queries:
            continue
        seen_queries.add(query)
        unique_rows.append(row)
    return unique_rows


def _formalizer_formal_source_grounding_matches_query_rows(
    groups: Sequence[Mapping[str, Any]],
    *,
    query_rows: Sequence[Mapping[str, Any]],
    source_scope_ids: Sequence[str],
    max_groups: int = 3,
) -> bool:
    """Reject carried declaration hits when the live Lean query has changed."""

    expected_rows = list(query_rows[: max(0, int(max_groups))])
    if not expected_rows:
        return True
    observed_rows = list(groups[: len(expected_rows)])
    if len(observed_rows) != len(expected_rows):
        return False
    expected_scopes = tuple(
        dict.fromkeys(
            str(value).strip()
            for value in source_scope_ids
            if str(value).strip()
        )
    )
    for observed, expected in zip(observed_rows, expected_rows, strict=True):
        query = str(expected.get("query", "") or "").strip()
        if str(observed.get("query_fingerprint", "") or "") != stable_hash(query):
            return False
        if str(observed.get("query_role", "") or "") != str(
            expected.get("query_role", "") or ""
        ):
            return False
        observed_scopes = tuple(
            str(value).strip()
            for value in observed.get("source_scope_ids", []) or []
            if str(value).strip()
        )
        if observed_scopes != expected_scopes:
            return False
    return True


def _formalizer_formal_source_scope_ids(
    context: Mapping[str, Any],
) -> tuple[str, ...]:
    raw_scopes = context.get("formal_source_scope_ids", []) or []
    if isinstance(raw_scopes, str):
        raw_scopes = [raw_scopes]
    discovered: list[str] = [
        str(value).strip()
        for value in raw_scopes
        if str(value).strip()
    ]
    provenance_rows: list[Mapping[str, Any]] = []
    direct_provenance = context.get("source_theorem_target_provenance", {})
    if isinstance(direct_provenance, Mapping):
        provenance_rows.append(direct_provenance)
    for provenance in provenance_rows:
        for key in ("source_id", "corpus_id", "formal_source_scope_id"):
            candidate = str(provenance.get(key, "") or "").strip()
            if candidate:
                discovered.append(candidate)
    return tuple(dict.fromkeys(discovered))


def _formalizer_declared_lean_imports(row: Mapping[str, Any]) -> list[str]:
    raw_imports = row.get("lean_imports", row.get("target_imports", []))
    if not isinstance(raw_imports, list | tuple):
        return []
    return list(
        dict.fromkeys(
            str(value).strip()
            for value in raw_imports
            if str(value).strip()
        )
    )


def _formalizer_lean_candidate_sources(
    proposal_packet: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(proposal_packet.get("formal_targets", []) or [], start=1):
        if not isinstance(row, Mapping):
            continue
        source = str(row.get("lean_statement_sketch", "") or "").strip()
        if not source:
            continue
        expected_status = str(row.get("expected_status", "") or "")
        if expected_status not in {"NEEDS_KERNEL_CHECK", "OPEN"}:
            continue
        candidate_id = (
            str(row.get("id", "") or "").strip()
            or f"formal_target_candidate_{index}"
        )
        provenance = (
            dict(row.get("source_theorem_target_provenance", {}) or {})
            if isinstance(
                row.get("source_theorem_target_provenance", {}),
                Mapping,
            )
            else {}
        )
        candidate_lean_declaration = str(
            row.get("candidate_lean_declaration", "") or ""
        ).strip()
        candidate_lean_declaration_source = (
            "formal_targets.candidate_lean_declaration"
            if candidate_lean_declaration
            else ""
        )
        formal_target_role = str(
            row.get("formal_target_role", "") or ""
        ).strip().upper()
        lean_imports = _formalizer_declared_lean_imports(row)
        if (
            not candidate_lean_declaration
            and _source_theorem_target_known_value(provenance) is True
        ):
            candidate_lean_declaration = str(
                provenance.get("target_lean_declaration", "") or ""
            ).strip()
            if candidate_lean_declaration:
                candidate_lean_declaration_source = (
                    "formal_targets.source_theorem_target_provenance."
                    "target_lean_declaration"
                )
        rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_kind": "formal_target_lean_statement_sketch",
                "source_field": "formal_targets",
                "formal_target_role": formal_target_role,
                "lean_source": source,
                "lean_imports": lean_imports,
                "candidate_lean_declaration": candidate_lean_declaration,
                "candidate_lean_declaration_source": (
                    candidate_lean_declaration_source
                ),
                "candidate_metadata": {
                    "expected_status": expected_status,
                    "formal_target_role": formal_target_role,
                    "candidate_lean_declaration": candidate_lean_declaration,
                    "lean_imports": lean_imports,
                    "informal_source": str(row.get("informal_source", "") or ""),
                    "semantic_alignment_constraints": list(
                        row.get("semantic_alignment_constraints", []) or []
                    )
                    if isinstance(
                        row.get("semantic_alignment_constraints", []),
                        list | tuple | set,
                    )
                    else [],
                    "source_theorem_target_provenance": provenance,
                },
            }
        )
    return rows


def _run_formalizer_lean_candidate_local_check(
    *,
    artifact_path: Path,
    candidate_lean_declaration: str = "",
    lean_project: Path | None,
    lean_timeout: int,
) -> dict[str, Any]:
    return dict(
        run_lean_candidate_identity_probe(
            artifact_path=artifact_path,
            candidate_lean_declaration=candidate_lean_declaration,
            lean_project=lean_project,
            lean_timeout=lean_timeout,
        )
    )


def _runtime_formalizer_client_tool_workspace_available(
    *,
    proposal_agent: LLMFormalizerProofEngineerAgent,
    lean_candidate_local_lean: bool,
    lean_candidate_lean_project: Path | None,
) -> bool:
    config = getattr(proposal_agent, "config", None)
    provider = getattr(proposal_agent, "provider", None)
    return bool(
        lean_candidate_local_lean
        and lean_candidate_lean_project is not None
        and Path(lean_candidate_lean_project).exists()
        and getattr(config, "use_client_tool_lean_candidate_workspace", False)
        and callable(getattr(provider, "generate_client_tool_turn", None))
        and callable(
            getattr(
                proposal_agent,
                "run_lean_candidate_workspace_with_client_tools",
                None,
            )
        )
    )


def _runtime_formalizer_lean_candidate_client_tool_workspace(
    *,
    proposal_agent: LLMFormalizerProofEngineerAgent,
    question: OpenResearchQuestion,
    task: AgentTask,
    blackboard: BlackboardState,
    theory_packet: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
    registered_problem: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
    formal_source_retriever: Any | None,
    proof_search_provider: LeanProofSearchProvider | None,
    proof_state_provider: ProofStateFeedbackProvider | None = None,
    lean_candidate_root: Path,
    lean_candidate_local_lean: bool,
    lean_candidate_lean_project: Path | None,
    lean_candidate_lean_timeout: int,
    candidate_materialization: Mapping[str, Any] | None = None,
    parent_formalizer_packet: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Run one direct model-owned Lean workspace for initial or revised source."""

    if not _runtime_formalizer_client_tool_workspace_available(
        proposal_agent=proposal_agent,
        lean_candidate_local_lean=lean_candidate_local_lean,
        lean_candidate_lean_project=lean_candidate_lean_project,
    ):
        return None
    parent_packet = (
        parent_formalizer_packet
        if isinstance(parent_formalizer_packet, Mapping)
        else {}
    )
    materialization = (
        candidate_materialization
        if isinstance(candidate_materialization, Mapping)
        else {}
    )
    materialization_id = str(
        materialization.get("manifest_id", "")
        or environment_feedback.get("candidate_materialization_id", "")
        or environment_feedback.get("source_manifest_id", "")
        or ""
    ).strip()
    if not materialization:
        materialization = blackboard.artifacts.get(materialization_id, {})
    initial_authoring = not (
        isinstance(materialization, Mapping)
        and str(materialization.get("artifact_kind", "") or "")
        == "RuntimeFormalizerLeanCandidateMaterialization"
    )
    artifact_path_text = ""
    if initial_authoring:
        parent_packet = build_formalizer_workspace_target(
            question=question,
            theory_packet=theory_packet,
            registered_problem=registered_problem,
            theorem_goals=theorem_goals,
        )
        target = parent_packet.get("formal_target", {})
        if not isinstance(target, Mapping):
            return None
        candidate = target
        candidate_id = str(target.get("id", "") or "").strip()
        candidate_declaration = ""
        source_field = "formal_targets"
        parent_source = ""
        expected_source_hash = stable_hash(parent_source)
        parent_packet_id = str(
            parent_packet.get("target_ref_id", "") or ""
        ).strip()
        if not parent_packet_id:
            return None
        recovery_checkpoint = environment_feedback.get(
            "formalizer_recovery_checkpoint", {}
        )
        recovery_checkpoint = (
            recovery_checkpoint
            if isinstance(recovery_checkpoint, Mapping)
            else {}
        )
        expected_target_hash = str(
            recovery_checkpoint.get(
                "parent_formalizer_workspace_target_hash", ""
            )
            or ""
        ).strip()
        if expected_target_hash and expected_target_hash != stable_hash(parent_packet):
            raise PacketValidationError(
                validation_label="Formalizer workspace target lineage",
                attempts=1,
                errors=[
                    "the task-bound theorem target changed across workspace resume"
                ],
                history=[],
                recovery_checkpoint=recovery_checkpoint,
            )
    else:
        if not isinstance(materialization, Mapping) or str(
            materialization.get("artifact_kind", "") or ""
        ) != "RuntimeFormalizerLeanCandidateMaterialization":
            return None
        requested_candidate_id = str(
            environment_feedback.get("candidate_id", "") or ""
        ).strip()
        diagnostic_ids = {
            str(row.get("candidate_id", "") or "").strip()
            for row in environment_feedback.get("candidate_diagnostics", []) or []
            if isinstance(row, Mapping)
            and str(row.get("candidate_id", "") or "").strip()
        }
        if not requested_candidate_id and len(diagnostic_ids) == 1:
            requested_candidate_id = next(iter(diagnostic_ids))
        candidate_rows = [
            row
            for row in materialization.get("candidate_rows", []) or []
            if isinstance(row, Mapping)
            and (
                not requested_candidate_id
                or str(row.get("candidate_id", "") or "")
                == requested_candidate_id
            )
        ]
        if len(candidate_rows) != 1:
            return None
        candidate = candidate_rows[0]
        candidate_id = str(candidate.get("candidate_id", "") or "").strip()
        candidate_declaration = str(
            candidate.get("candidate_lean_declaration", "")
            or candidate.get("target_lean_declaration", "")
            or ""
        ).strip()
        source_field = str(candidate.get("source_field", "") or "").strip()
        artifact_path_text = str(candidate.get("artifact_path", "") or "")
        artifact_path = Path(artifact_path_text)
        expected_source_hash = str(candidate.get("source_hash", "") or "").strip()
        if source_field != "formal_targets":
            return None
        try:
            parent_source = artifact_path.read_text(encoding="utf-8")
        except OSError:
            return None
        if (
            not expected_source_hash
            or stable_hash(parent_source) != expected_source_hash
        ):
            raise PacketValidationError(
                validation_label="Formalizer Lean workspace lineage",
                attempts=1,
                errors=["current candidate artifact is missing or hash-stale"],
                history=[],
            )
        parent_packet_id = str(
            materialization.get("source_formalizer_packet_id", "") or ""
        ).strip()
        if not parent_packet:
            parent_packet = blackboard.artifacts.get(parent_packet_id, {})
        if not isinstance(parent_packet, Mapping) or str(
            parent_packet.get("packet_id", "") or ""
        ) != parent_packet_id:
            raise PacketValidationError(
                validation_label="Formalizer Lean workspace lineage",
                attempts=1,
                errors=["current Formalizer packet is missing or hash-stale"],
                history=[],
            )
    if not candidate_id or (not initial_authoring and not candidate_declaration):
        return None

    revision_context_payload = environment_feedback.get(
        "formalizer_workspace_context", {}
    )
    revision_context = (
        dict(revision_context_payload)
        if isinstance(revision_context_payload, Mapping)
        else {}
    )
    initial_source, candidate_declaration, revision_start = (
        resolve_lean_workspace_start_source(
            candidate_id=candidate_id,
            candidate_lean_declaration=candidate_declaration,
            parent_source=parent_source,
            environment_feedback=environment_feedback,
        )
    )

    workspace_root = (
        Path(lean_candidate_root)
        / _safe_identifier(question.id)
        / "client_tool_workspace"
        / stable_hash(
            [task.task_id, materialization_id, candidate_id, expected_source_hash]
        )[:12]
    )

    def check_candidate(
        source: str,
        submitted_declaration: str,
    ) -> Mapping[str, Any]:
        source_hash = stable_hash(source)
        precheck_errors = _formalizer_lean_candidate_source_boundary_errors(
            source,
        )
        blocking_errors = list(precheck_errors)
        if blocking_errors:
            return {
                "source_hash": source_hash,
                "compiled": False,
                "precheck_errors": precheck_errors,
                "blocking_precheck_errors": blocking_errors,
                "local_lean_attempted": False,
                "local_lean_exit_status": "",
                "local_lean_stdout": "",
                "local_lean_stderr": "",
                "candidate_lean_declaration": submitted_declaration,
            }
        workspace_root.mkdir(parents=True, exist_ok=True)
        path = workspace_root / (
            _safe_identifier(candidate_id) + "_" + source_hash[:12] + ".lean"
        )
        path.write_text(source, encoding="utf-8")
        proof_state_artifact_path = (
            _formalizer_lean_candidate_project_local_proof_state_artifact(
                source=source,
                lean_project=Path(lean_candidate_lean_project),
                question_id=question.id,
                task_id=task.task_id,
                candidate_id=candidate_id,
                source_hash=source_hash,
                index=1,
            )
        )
        local_result = _run_formalizer_lean_candidate_local_check(
            artifact_path=path,
            candidate_lean_declaration=submitted_declaration,
            lean_project=Path(lean_candidate_lean_project),
            lean_timeout=lean_candidate_lean_timeout,
        )
        return {
            "source_hash": source_hash,
            "candidate_lean_declaration": submitted_declaration,
            "compiled": _bool_like(
                local_result.get("local_lean_compiled", False)
            ),
            "artifact_path": str(path),
            "proof_state_artifact_path": proof_state_artifact_path,
            "precheck_errors": precheck_errors,
            "blocking_precheck_errors": blocking_errors,
            "local_lean_attempted": _bool_like(
                local_result.get("local_lean_attempted", False)
            ),
            "local_lean_source_compiled": _bool_like(
                local_result.get("local_lean_source_compiled", False)
            ),
            "local_lean_exit_status": str(
                local_result.get("local_lean_exit_status", "") or ""
            ),
            "local_lean_stdout": str(
                local_result.get("local_lean_stdout", "") or ""
            ),
            "local_lean_stderr": str(
                local_result.get("local_lean_stderr", "") or ""
            ),
            "candidate_identity_lean_checked": _bool_like(
                local_result.get("candidate_identity_lean_checked", False)
            ),
            "candidate_identity_lean_verified": _bool_like(
                local_result.get("candidate_identity_lean_verified", False)
            ),
            "candidate_identity_lean_stdout": str(
                local_result.get("candidate_identity_lean_stdout", "") or ""
            ),
            "candidate_identity_lean_stderr": str(
                local_result.get("candidate_identity_lean_stderr", "") or ""
            ),
            "local_lean_command": list(
                local_result.get("local_lean_command", []) or []
            ),
            "local_lean_project": str(lean_candidate_lean_project),
        }

    source_scope_ids = _formalizer_formal_source_scope_ids(revision_context)

    def search_formal_environment(query: str, k: int) -> Any:
        if formal_source_retriever is None:
            return {
                "query": query,
                "hits": [],
                "retrieval_status": "formal_source_retriever_unavailable",
            }
        groups = _formalizer_formal_source_grounding_hit_groups(
            formal_source_retriever,
            query_seeds=(query,),
            source_scope_ids=source_scope_ids,
            semantic_query_role="model_selected_lean_query",
            k=k,
            max_groups=1,
        )
        compact_groups = compact_formal_source_grounding_hits_for_prompt(groups)
        if not compact_groups:
            return {
                "query": query,
                "hits": [],
                "retrieval_status": "no_prompt_safe_formal_source_hits",
            }
        return {
            "query": query,
            **compact_groups[0],
            "retrieval_status": "prompt_safe_signature_hits",
        }

    def search_proof_candidates(
        source: str,
        query: str,
        k: int,
        last_check: Mapping[str, Any],
    ) -> Any:
        if proof_search_provider is None:
            return {
                "status": "UNAVAILABLE",
                "query": query,
                "source_theorem_candidate_proof_bodies": [],
            }
        diagnostics = [
            str(value)
            for value in (
                last_check.get("local_lean_stderr", ""),
                last_check.get("local_lean_stdout", ""),
                last_check.get("candidate_identity_lean_stderr", ""),
            )
            if str(value).strip()
        ]
        request = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "FormalizerProofSearchToolRequest",
            "question_id": question.id,
            "candidate_id": candidate_id,
            "target_lean_declaration": str(
                last_check.get("candidate_lean_declaration", "")
                or candidate_declaration
            ),
            "target_theorem_statement": source,
            "current_lean_source": source,
            "current_lean_source_hash": stable_hash(source),
            "model_query": query,
            "compiler_feedback": {"diagnostics": diagnostics},
            "proof_evidence_status": "PROOF_SEARCH_REQUEST_NOT_PROOF_EVIDENCE",
        }
        request["request_fingerprint"] = stable_hash(request)
        try:
            raw = proof_search_provider.run(request)
        except Exception as exc:
            return {
                "status": "PROVIDER_ERROR",
                "provider": str(
                    getattr(
                        proof_search_provider,
                        "name",
                        type(proof_search_provider).__name__,
                    )
                ),
                "error": f"{type(exc).__name__}: {exc}"[:4000],
                "query": query,
                "source_theorem_candidate_proof_bodies": [],
                "proof_evidence_status": "PROOF_SEARCH_ERROR_NOT_PROOF_EVIDENCE",
            }
        if not isinstance(raw, Mapping):
            return {
                "status": "PROVIDER_ERROR",
                "error": "proof search provider returned a non-object result",
                "query": query,
                "source_theorem_candidate_proof_bodies": [],
                "proof_evidence_status": "PROOF_SEARCH_ERROR_NOT_PROOF_EVIDENCE",
            }
        result = dict(raw)
        return {
            "status": str(result.get("status", "") or ""),
            "provider": str(result.get("provider", "") or ""),
            "query": query,
            "source_theorem_candidate_proof_bodies": [
                str(value)
                for value in result.get(
                    "source_theorem_candidate_proof_bodies", []
                )
                or []
                if str(value).strip()
            ][:k],
            "verified_support_assets": [
                deepcopy(dict(value))
                for value in result.get("verified_support_assets", []) or []
                if isinstance(value, Mapping)
            ][:k],
            "failure_feedback": [
                deepcopy(dict(value))
                for value in result.get("failure_feedback", []) or []
                if isinstance(value, Mapping)
            ][:k],
            "openprover_summary": deepcopy(
                dict(result.get("openprover_summary", {}) or {})
            ),
            "proof_evidence_status": "PROOF_SEARCH_RESULT_NOT_PROOF_EVIDENCE",
            "runtime_applied_candidate": False,
        }

    def inspect_lean_state(
        source: str,
        last_check: Mapping[str, Any],
    ) -> Any:
        if proof_state_provider is None:
            return {
                "status": "UNAVAILABLE",
                "provider": "",
                "rows": [],
                "proof_evidence_status": (
                    "LEAN_STATE_INSPECTION_UNAVAILABLE_NOT_PROOF_EVIDENCE"
                ),
            }
        source_hash = stable_hash(source)
        if str(last_check.get("source_hash", "") or "") != source_hash:
            raise PacketValidationError(
                validation_label="Formalizer Lean state inspection lineage",
                attempts=1,
                errors=["Lean state inspection is not bound to current source hash"],
                history=[],
            )
        check_artifact_path = str(
            last_check.get("proof_state_artifact_path", "")
            or last_check.get("artifact_path", "")
            or ""
        )
        subclaim = FormalSubclaim(
            id="formalizer_lean_candidate:" + _safe_identifier(candidate_id),
            title="Model-requested Lean state inspection",
            status="FAILED",
            claim=(
                "Inspect the exact current source for candidate " + candidate_id
            ),
            claim_type="lean_obligation",
            proof_obligation_id=candidate_id,
            lean_statement=source,
            formalization_status="model_requested_lean_state_inspection",
            verifier=str(
                getattr(
                    proof_state_provider,
                    "name",
                    type(proof_state_provider).__name__,
                )
            ),
            verification_strength="diagnostic_only",
            kernel_verified=False,
            errors=[
                str(value)
                for value in (
                    last_check.get("local_lean_stderr", ""),
                    last_check.get("local_lean_stdout", ""),
                )
                if str(value).strip()
            ],
            artifact_path=check_artifact_path or None,
        )
        rows = proof_state_provider.inspect((subclaim,))
        return {
            "status": "OBSERVED" if rows else "NO_OBSERVATION",
            "provider": str(
                getattr(
                    proof_state_provider,
                    "name",
                    type(proof_state_provider).__name__,
                )
            ),
            "source_hash": source_hash,
            "rows": [proof_state_feedback_row_to_json(row) for row in rows],
            "proof_evidence_status": (
                "MODEL_REQUESTED_LEAN_STATE_INSPECTION_NOT_PROOF_EVIDENCE"
            ),
        }

    declaration_inspector = getattr(
        proof_state_provider,
        "inspect_declaration",
        None,
    )

    def active_project_declaration_path(symbol: str) -> Path | None:
        if formal_source_retriever is None:
            return None
        try:
            hits = formal_source_retriever.search(symbol, k=8)
        except Exception:
            return None
        project_root = Path(lean_candidate_lean_project).resolve()
        for hit in hits:
            declaration = getattr(hit, "declaration", None)
            if str(getattr(declaration, "name", "") or "") != symbol:
                continue
            path_text = str(getattr(declaration, "path", "") or "").strip()
            if not path_text:
                continue
            path = Path(path_text).expanduser()
            resolved = (
                path if path.is_absolute() else project_root / path
            ).resolve()
            if resolved.is_file() and project_root in resolved.parents:
                return resolved
        return None

    def inspect_lean_declaration(
        source: str,
        symbol: str,
        context_lines: int,
        last_check: Mapping[str, Any],
    ) -> Any:
        source_hash = stable_hash(source)
        candidate_source_checked = bool(last_check)
        if candidate_source_checked:
            if str(last_check.get("source_hash", "") or "") != source_hash:
                raise PacketValidationError(
                    validation_label=(
                        "Formalizer Lean declaration inspection lineage"
                    ),
                    attempts=1,
                    errors=[
                        "Lean declaration inspection is not bound to current source hash"
                    ],
                    history=[],
                )
        active_declaration_path = active_project_declaration_path(symbol)
        if active_declaration_path is not None:
            check_artifact_path = active_declaration_path
            inspection_binding = "active_project_declaration_source"
        elif candidate_source_checked:
            check_artifact_path = Path(
                str(
                    last_check.get("proof_state_artifact_path", "")
                    or last_check.get("artifact_path", "")
                    or ""
                )
            )
            try:
                checked_source = check_artifact_path.read_text(encoding="utf-8")
            except OSError as exc:
                raise PacketValidationError(
                    validation_label=(
                        "Formalizer Lean declaration inspection lineage"
                    ),
                    attempts=1,
                    errors=[f"checked Lean artifact is unavailable: {exc}"],
                    history=[],
                ) from exc
            if stable_hash(checked_source) != source_hash:
                raise PacketValidationError(
                    validation_label=(
                        "Formalizer Lean declaration inspection lineage"
                    ),
                    attempts=1,
                    errors=[
                        "checked Lean artifact is not bound to current source hash"
                    ],
                    history=[],
                )
            inspection_binding = "checked_candidate_source"
        else:
            return {
                "ok": False,
                "status": "ACTIVE_PROJECT_DECLARATION_NOT_FOUND",
                "symbol": symbol,
                "error": (
                    "No exact active-project declaration path was found for "
                    "this model-selected symbol. Search the formal environment "
                    "for its exact qualified name before retrying inspection."
                ),
                "candidate_source_hash": source_hash,
                "candidate_source_checked": False,
                "proof_evidence_status": (
                    "LEAN_DECLARATION_INSPECTION_NOT_PROOF_EVIDENCE"
                ),
            }
        raw = declaration_inspector(
            artifact_path=str(check_artifact_path),
            symbol=symbol,
            context_lines=context_lines,
        )
        if not isinstance(raw, Mapping):
            return {
                "ok": False,
                "status": "PROVIDER_ERROR",
                "provider": str(
                    getattr(
                        proof_state_provider,
                        "name",
                        type(proof_state_provider).__name__,
                    )
                ),
                "error": "declaration inspection provider returned a non-object",
                "proof_evidence_status": (
                    "LEAN_DECLARATION_INSPECTION_NOT_PROOF_EVIDENCE"
                ),
            }
        result = deepcopy(dict(raw))
        result.update(
            {
                "inspection_binding": inspection_binding,
                "candidate_source_hash": source_hash,
                "candidate_source_checked": candidate_source_checked,
            }
        )
        return result

    try:
        revised_packet, loop_evidence = (
            proposal_agent.run_lean_candidate_workspace_with_client_tools(
                question=question,
                theory_packet=theory_packet,
                parent_packet=parent_packet,
                candidate_id=candidate_id,
                candidate_source_field=source_field,
                candidate_lean_declaration=candidate_declaration,
                initial_source=initial_source,
                environment_feedback=environment_feedback,
                check_candidate=check_candidate,
                search_formal_environment=search_formal_environment,
                search_proof_candidates=(
                    search_proof_candidates
                    if proof_search_provider is not None
                    else None
                ),
                inspect_lean_state=(
                    inspect_lean_state
                    if proof_state_provider is not None
                    else None
                ),
                inspect_lean_declaration=(
                    inspect_lean_declaration
                    if callable(declaration_inspector)
                    else None
                ),
            )
        )
    except PacketValidationError as exc:
        checkpoint = (
            deepcopy(dict(exc.recovery_checkpoint))
            if isinstance(exc.recovery_checkpoint, Mapping)
            else {}
        )
        checkpoint["parent_formalizer_artifact_id"] = parent_packet_id
        if initial_authoring:
            checkpoint.update(
                {
                    "parent_formalizer_workspace_target_id": parent_packet_id,
                    "parent_formalizer_workspace_target_hash": stable_hash(
                        parent_packet
                    ),
                }
            )
        else:
            checkpoint["parent_formalizer_packet_id"] = parent_packet_id
        raise PacketValidationError(
            validation_label=exc.validation_label,
            attempts=exc.attempts,
            errors=list(exc.errors),
            history=[dict(row) for row in exc.history],
            last_invalid_packet=exc.last_invalid_packet,
            recovery_checkpoint=checkpoint,
        ) from exc
    evidence = {
        **dict(loop_evidence),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "task_id": task.task_id,
        "workspace_phase": (
            "initial_authoring" if initial_authoring else "revision"
        ),
        "parent_materialization_manifest_id": materialization_id,
        "parent_formalizer_artifact_id": parent_packet_id,
        "parent_formalizer_packet_id": (
            parent_packet_id if not initial_authoring else ""
        ),
        "parent_formalizer_workspace_target_id": (
            parent_packet_id if initial_authoring else ""
        ),
        "parent_formalizer_workspace_target_hash": (
            stable_hash(parent_packet) if initial_authoring else ""
        ),
        "parent_candidate_artifact_path": artifact_path_text,
        "parent_candidate_source_hash": expected_source_hash,
        **revision_start,
        "active_lean_project": str(lean_candidate_lean_project),
        "source_scope_ids": list(source_scope_ids),
    }
    evidence["artifact_id"] = (
        "formalizer_lean_candidate_client_tool_loop:"
        + stable_hash(evidence)[:20]
    )
    return revised_packet, evidence


def _formalizer_lean_candidate_source_boundary_errors(
    source: str,
) -> list[str]:
    text = str(source or "")
    if not text.strip():
        return ["empty Lean candidate source"]
    if len(text) > 20000:
        return ["Lean candidate source exceeds the 20000-character artifact boundary"]
    return []


def _source_theorem_target_known_value(provenance: object) -> bool | None:
    if not isinstance(provenance, Mapping):
        return None
    value = provenance.get("source_theorem_target_known")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    return None


def _critic_packet_validation_failure_bundle(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    retrieval_manifest: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    algorithm_manifest: Mapping[str, Any],
    formalization_manifest: Mapping[str, Any],
    runtime_observations: Mapping[str, Any],
    exc: PacketValidationError,
) -> tuple[str, dict[str, Any], dict[str, Any], EnvironmentObservation, EvidenceLedgerEntry]:
    validation_errors = [str(error) for error in exc.errors if str(error)]
    failure_id = (
        "critic_validation_failure:"
        + stable_hash(
            [task.task_id, exc.validation_label, validation_errors, exc.history]
        )[:20]
    )
    rejected_candidate = (
        dict(exc.last_invalid_packet)
        if isinstance(exc.last_invalid_packet, Mapping)
        else {}
    )
    input_refs = {
        "retrieval_manifest": {
            "artifact_id": str(
                retrieval_manifest.get("manifest_id", "")
                or retrieval_manifest.get("memory_id", "")
                or ""
            ),
            "content_hash": stable_hash(dict(retrieval_manifest)),
        },
        "theory_packet": {
            "artifact_id": str(theory_packet.get("packet_id", "") or ""),
            "content_hash": stable_hash(dict(theory_packet)),
        },
        "simulation_manifest": {
            "artifact_id": str(simulation_manifest.get("manifest_id", "") or ""),
            "content_hash": stable_hash(dict(simulation_manifest)),
        },
        "algorithm_manifest": {
            "artifact_id": str(algorithm_manifest.get("manifest_id", "") or ""),
            "content_hash": stable_hash(dict(algorithm_manifest)),
        },
        "formalization_manifest": {
            "artifact_id": str(formalization_manifest.get("manifest_id", "") or ""),
            "content_hash": stable_hash(dict(formalization_manifest)),
        },
        "runtime_observations_hash": stable_hash(dict(runtime_observations)),
    }
    feedback = {
        "artifact_kind": "RuntimeCriticValidationObservations",
        "feedback_id": failure_id,
        "feedback_type": "critic_packet_validation_observations",
        "feedback_source": "CriticEvaluator",
        "failure_classification": "critic_packet_validation_failed",
        "validation_label": exc.validation_label,
        "validation_errors": validation_errors,
        "attempts": exc.attempts,
        "last_attempt_summary": exc.history[-1] if exc.history else {},
        "rejected_candidate": rejected_candidate,
        "critic_input_refs": input_refs,
        "validation_boundary": {
            "in_call_structured_output_retry_exhausted": True,
            "runtime_edits_candidate": False,
            "outer_same_owner_retry_created": False,
        },
        "proof_evidence_status": (
            "CRITIC_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }
    failure_artifact = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeCriticEvaluatorValidationFailure",
        "failure_id": failure_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": _question_to_payload(question),
        "task_id": task.task_id,
        "validation_label": exc.validation_label,
        "failure_classification": "critic_packet_validation_failed",
        "validation_errors": validation_errors,
        "structured_output_retry_history": exc.history,
        "rejected_candidate": rejected_candidate,
        "critic_input_refs": input_refs,
        "proof_evidence_status": (
            "CRITIC_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "boundary": (
            "This artifact records a rejected CriticEvaluator model packet and "
            "the exact validator observations after bounded in-call regeneration. "
            "Runtime does not edit the packet or create an outer Critic retry."
        ),
    }
    observation = EnvironmentObservation(
        observation_type="critic_packet_validation_failure",
        summary="; ".join(validation_errors)[:500],
        payload={
            "failure_id": failure_id,
            "failure_classification": "critic_packet_validation_failed",
            "validation_errors": validation_errors,
            "proof_evidence_status": (
                "CRITIC_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
            ),
        },
    )
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, failure_id])[:20],
        task_id=task.task_id,
        artifact_id=failure_id,
        evidence_type="critic_packet_validation_failure",
        status="VALIDATION_FAILED_RECORDED_NOT_PROOF_EVIDENCE",
        boundary=CRITIC_EVALUATOR_BOUNDARY,
        payload={
            "failure_classification": "critic_packet_validation_failed",
            "validation_errors": validation_errors,
            "attempts": exc.attempts,
            "proof_evidence_status": (
                "CRITIC_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
            ),
        },
    )
    return failure_id, failure_artifact, feedback, observation, evidence


class CriticEvaluatorRuntimeSubsystem:
    name = "CriticEvaluator"

    def __init__(
        self,
        *,
        proposal_agent: LLMCriticEvaluatorAgent | None = None,
        runtime_config: ResearchAgentRuntimeConfig = ResearchAgentRuntimeConfig(),
    ) -> None:
        self.proposal_agent = proposal_agent
        self.runtime_config = runtime_config

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        critic_control = _architect_control_payload(context, "CriticEvaluator")
        retrieval_manifest = _latest_artifact(blackboard, "retrieval_memory_manifest:")
        retrieval_manifest_id = str(
            retrieval_manifest.get("manifest_id", "") or ""
        )
        requested_theory_packet_id = str(task.inputs.get("theory_packet_id", "") or "")
        if requested_theory_packet_id:
            raw_theory_packet = blackboard.artifacts.get(requested_theory_packet_id, {})
            theory_packet = (
                dict(raw_theory_packet) if isinstance(raw_theory_packet, Mapping) else {}
            )
        else:
            theory_packet = _latest_artifact(blackboard, "theory_derivation:")
        theory_packet_id = str(
            requested_theory_packet_id
            or theory_packet.get("packet_id", "")
            or ""
        )
        requested_simulation_manifest_id = str(
            task.inputs.get("simulation_manifest_id", "") or ""
        )
        simulation_manifest = _artifact_by_id_or_latest(
            blackboard,
            requested_simulation_manifest_id,
            "simulation_manifest:",
        )
        missing_simulation_result = (
            _runtime_missing_simulation_handoff_result_if_needed(
                source_subsystem="CriticEvaluator",
                task=task,
                question=question,
                simulation_manifest_id=requested_simulation_manifest_id,
                simulation_manifest=simulation_manifest,
            )
        )
        if missing_simulation_result is not None:
            return missing_simulation_result
        simulation_manifest_id = str(
            requested_simulation_manifest_id
            or simulation_manifest.get("manifest_id", "")
            or ""
        )
        requested_algorithm_manifest_id = str(
            task.inputs.get("algorithm_sandbox_manifest_id", "") or ""
        )
        algorithm_manifest = _artifact_by_id_or_latest(
            blackboard,
            requested_algorithm_manifest_id,
            "algorithm_sandbox_manifest:",
        )
        missing_algorithm_result = (
            _runtime_missing_algorithm_handoff_result_if_needed(
                source_subsystem="CriticEvaluator",
                task=task,
                question=question,
                algorithm_sandbox_manifest_id=requested_algorithm_manifest_id,
                algorithm_manifest=algorithm_manifest,
            )
        )
        if missing_algorithm_result is not None:
            return missing_algorithm_result
        algorithm_manifest_id = str(
            requested_algorithm_manifest_id
            or algorithm_manifest.get("manifest_id", "")
            or ""
        )
        requested_formalization_manifest_id = str(
            task.inputs.get("formalization_manifest_id", "") or ""
        )
        formalization_manifest = _artifact_by_id_or_latest(
            blackboard,
            requested_formalization_manifest_id,
            "formalization_manifest:",
        )
        missing_formalization_result = (
            _runtime_missing_formalization_handoff_result_if_needed(
                source_subsystem="CriticEvaluator",
                task=task,
                question=question,
                formalization_manifest_id=requested_formalization_manifest_id,
                formalization_manifest=formalization_manifest,
            )
        )
        if missing_formalization_result is not None:
            return missing_formalization_result
        formalization_manifest_id = str(
            requested_formalization_manifest_id
            or formalization_manifest.get("manifest_id", "")
            or ""
        )
        critic_round = _critic_revision_round(context)
        max_critic_revision_rounds = _effective_critic_revision_rounds(
            context,
            self.runtime_config,
        )
        critic_evidence_contract = (
            critic_control.get("evidence_contract", {})
            if isinstance(critic_control.get("evidence_contract", {}), Mapping)
            else {}
        )
        explicit_formal_verification_policy = str(
            critic_evidence_contract.get("formal_verification_policy", "") or ""
        ).strip()
        formal_verification_policy = _normalized_formal_verification_policy(
            explicit_formal_verification_policy or "optional"
        )
        formal_required_for_final = formal_verification_policy == "required"
        formal_debt_blocks_research_acceptance = bool(
            formal_required_for_final or not explicit_formal_verification_policy
        )
        critic_environment_feedback = (
            task.inputs.get("environment_feedback", {})
            if isinstance(task.inputs.get("environment_feedback", {}), Mapping)
            else context.get("environment_feedback", {})
            if isinstance(context.get("environment_feedback", {}), Mapping)
            else {}
        )
        formalization_counts = (
            dict(formalization_manifest.get("counts", {}))
            if isinstance(formalization_manifest.get("counts", {}), Mapping)
            else {}
        )
        formal_proof_work_pending = bool(
            int(formalization_counts.get("formal_gap", 0) or 0) > 0
            or not _bool_like(
                formalization_manifest.get("full_frontier_theorem_proved", False)
            )
        )
        formal_debt_deferred_nonblocking = bool(
            formal_proof_work_pending
            and not formal_debt_blocks_research_acceptance
        )
        critic_runtime_observations = {
            "feedback_type": "critic_runtime_observations",
            "feedback_source": "CriticEvaluator",
            "question_id": question.id,
            "critic_round": critic_round,
            "max_critic_rounds": max_critic_revision_rounds,
            "retrieval_memory_manifest_id": retrieval_manifest_id,
            "theory_packet_id": theory_packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "formalization_manifest_id": formalization_manifest_id,
            "formalization_counts": formalization_counts,
            "formal_proof_work_pending": formal_proof_work_pending,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        }
        proposal_packet: dict[str, Any] | None = None
        proposal_evidence: EvidenceLedgerEntry | None = None
        proposal_validation_failure_id = ""
        proposal_validation_failure_feedback: dict[str, Any] | None = None
        proposal_validation_failure_evidence: EvidenceLedgerEntry | None = None
        produced_artifacts: dict[str, Any] = {}
        observations: list[EnvironmentObservation] = []
        if self.proposal_agent is not None:
            try:
                with agent_runtime_substage("critic_evaluation"):
                    proposal_packet = self.proposal_agent.propose(
                        question=question,
                        retrieval_manifest=retrieval_manifest,
                        theory_packet=theory_packet,
                        simulation_manifest=simulation_manifest,
                        algorithm_manifest=algorithm_manifest,
                        formalization_manifest=formalization_manifest,
                        environment_feedback=critic_environment_feedback,
                    )
            except PacketValidationError as exc:
                (
                    proposal_validation_failure_id,
                    failure_artifact,
                    proposal_validation_failure_feedback,
                    failure_observation,
                    proposal_validation_failure_evidence,
                ) = _critic_packet_validation_failure_bundle(
                    task=task,
                    question=question,
                    retrieval_manifest=retrieval_manifest,
                    theory_packet=theory_packet,
                    simulation_manifest=simulation_manifest,
                    algorithm_manifest=algorithm_manifest,
                    formalization_manifest=formalization_manifest,
                    runtime_observations=critic_runtime_observations,
                    exc=exc,
                )
                produced_artifacts[proposal_validation_failure_id] = (
                    failure_artifact
                )
                observations.append(failure_observation)
            if proposal_packet is not None:
                proposal_id = str(proposal_packet["packet_id"])
                observation_assessment = proposal_packet.get(
                    "current_observation_assessment",
                    {},
                )
                if not isinstance(observation_assessment, Mapping):
                    observation_assessment = {}
                produced_artifacts[proposal_id] = proposal_packet
                observations.append(
                    EnvironmentObservation(
                        observation_type="llm_critic_evaluator_proposal",
                        summary=(
                            "validated observation-only LLM CriticEvaluator packet "
                            "recorded without a runtime-authored source-edit agenda"
                        ),
                        payload={
                            "packet_id": proposal_id,
                            "n_boundary_audit_rows": len(
                                proposal_packet.get("evidence_boundary_audit", [])
                                or []
                            ),
                            "n_causal_hypotheses": len(
                                observation_assessment.get(
                                    "causal_hypotheses",
                                    [],
                                )
                                or []
                            ),
                            "proof_evidence_status": (
                                CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE
                            ),
                        },
                    )
                )
                proposal_evidence = EvidenceLedgerEntry(
                    evidence_id="evidence:"
                    + stable_hash([task.task_id, proposal_id])[:20],
                    task_id=task.task_id,
                    artifact_id=proposal_id,
                    evidence_type="llm_critic_evaluator_proposal",
                    status="PROPOSAL_RECORDED_NOT_AUTHORITY_GATE",
                    boundary=CRITIC_EVALUATOR_BOUNDARY,
                    payload={
                        "n_boundary_audit_rows": len(
                            proposal_packet.get("evidence_boundary_audit", []) or []
                        ),
                        "n_learning_updates": len(
                            proposal_packet.get("learning_updates", []) or []
                        ),
                        "kernel_verified": False,
                        "full_frontier_theorem_proved": False,
                    },
                )
        coordination_assessment = (
            proposal_packet.get("coordination_assessment", {})
            if isinstance(proposal_packet, Mapping)
            and isinstance(
                proposal_packet.get("coordination_assessment", {}), Mapping
            )
            else {}
        )
        coordination_scope = str(
            coordination_assessment.get("scope", "none") or "none"
        ).strip()
        conflicting_artifact_ids = list(
            dict.fromkeys(
                str(value).strip()
                for value in coordination_assessment.get(
                    "conflicting_artifact_ids", []
                )
                or []
                if str(value).strip()
            )
        )
        artifact_owner_by_id = {
            str(artifact_id): handoff.from_subsystem
            for handoff in blackboard.handoff_ledger
            for artifact_id in handoff.produced_artifact_ids
            if str(artifact_id) and handoff.from_subsystem
        }
        conflicting_artifact_owners = sorted(
            {
                artifact_owner_by_id[artifact_id]
                for artifact_id in conflicting_artifact_ids
                if artifact_id in artifact_owner_by_id
            }
        )
        cross_workspace_conflict_verified = bool(
            coordination_scope == "cross_workspace"
            and len(conflicting_artifact_ids) >= 2
            and all(
                artifact_id in blackboard.artifacts
                for artifact_id in conflicting_artifact_ids
            )
            and len(conflicting_artifact_owners) >= 2
        )
        architect_replan_required = bool(
            cross_workspace_conflict_verified
            and critic_round < max_critic_revision_rounds
        )
        evidence_contract_decision = _critic_evidence_contract_decision(
            critic_control=critic_control,
            formalization_manifest=formalization_manifest,
            revision_required=bool(
                architect_replan_required
                or proposal_validation_failure_feedback is not None
            ),
        )
        manifest_id = "critic_evaluator_manifest:" + stable_hash(
            [
                task.task_id,
                str(proposal_packet.get("packet_id", ""))
                if proposal_packet
                else "",
                formalization_counts,
            ]
        )[:20]
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeCriticEvaluatorManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "formalization_manifest_id": formalization_manifest_id,
            "runtime_architect_control": critic_control,
            "llm_critic_evaluator_proposal_id": (
                str(proposal_packet.get("packet_id", "")) if proposal_packet else ""
            ),
            "llm_critic_evaluator_validation_failure_id": (
                proposal_validation_failure_id
            ),
            "coordination_assessment": dict(coordination_assessment),
            "critic_revision_round": critic_round,
            "max_critic_revision_rounds": max_critic_revision_rounds,
            "runtime_reroute_decision": {
                "routing_authority": "ArchitectCoordinator_model_packet",
                "architect_replan_required": architect_replan_required,
                "legacy_owner_routes_disabled": True,
                "reroute_to_theory_developer": False,
                "reroute_to_formalizer_proofengineer": False,
                "observed_conditions": {
                    "coordination_scope": coordination_scope,
                    "cross_workspace_conflict_verified": (
                        cross_workspace_conflict_verified
                    ),
                    "conflicting_artifact_ids": conflicting_artifact_ids,
                    "conflicting_artifact_owners": conflicting_artifact_owners,
                    "formal_proof_work_pending": formal_proof_work_pending,
                },
                "formal_verification_policy": formal_verification_policy,
                "formal_verification_policy_explicit": bool(
                    explicit_formal_verification_policy
                ),
                "formal_debt_deferred_nonblocking": (
                    formal_debt_deferred_nonblocking
                ),
                "reason": (
                    "Critic classified an evidence-grounded cross-workspace conflict; "
                    "Architect must coordinate artifact ownership."
                    if architect_replan_required
                    else "No artifact-bound cross-workspace conflict with available "
                    "revision budget was verified."
                ),
                "environment_feedback": (
                    critic_runtime_observations
                    if architect_replan_required
                    else {}
                ),
            },
            "evidence_contract_decision": evidence_contract_decision,
            "counts": {
                "kernel_verified": int(
                    (formalization_manifest.get("counts", {}) if isinstance(formalization_manifest, Mapping) else {}).get(
                        "kernel_verified", 0
                    )
                    or 0
                ),
                "formal_gaps": int(
                    (formalization_manifest.get("counts", {}) if isinstance(formalization_manifest, Mapping) else {}).get(
                        "formal_gap", 0
                    )
                    or 0
                ),
            },
            "boundary": (
                "Critic rows are observation and coordination-scope signals only. "
                "They do not prescribe source edits, choose a same-workspace repair "
                "strategy, or promote non-kernel artifacts to proof evidence."
            ),
        }
        produced_artifacts[manifest_id] = manifest
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="critic_evaluator",
            status="CRITIC_OBSERVATIONS_RECORDED",
            boundary=str(manifest["boundary"]),
            payload={
                **manifest["counts"],
                "architect_acceptance_gate": critic_control.get("acceptance_gate", ""),
                "evidence_contract_decision": evidence_contract_decision,
            },
        )
        observations.append(
            EnvironmentObservation(
                observation_type="critic_evaluator",
                summary=(
                    f"critic_revision_round={critic_round}/{max_critic_revision_rounds} "
                    f"coordination_scope={coordination_scope} "
                    f"formal_proof_work_pending={formal_proof_work_pending}"
                ),
                payload={
                    **manifest["counts"],
                    "critic_revision_round": critic_round,
                    "max_critic_revision_rounds": max_critic_revision_rounds,
                    "routing_authority": "ArchitectCoordinator_model_packet",
                    "architect_replan_required": architect_replan_required,
                    "legacy_owner_routes_disabled": True,
                    "observed_conditions": {
                        "coordination_scope": coordination_scope,
                        "cross_workspace_conflict_verified": (
                            cross_workspace_conflict_verified
                        ),
                        "conflicting_artifact_ids": conflicting_artifact_ids,
                        "conflicting_artifact_owners": conflicting_artifact_owners,
                        "formal_proof_work_pending": formal_proof_work_pending,
                    },
                    "formal_verification_policy": formal_verification_policy,
                    "formal_verification_policy_explicit": bool(
                        explicit_formal_verification_policy
                    ),
                    "formal_debt_deferred_nonblocking": (
                        formal_debt_deferred_nonblocking
                    ),
                    "final_acceptance_status": evidence_contract_decision[
                        "final_acceptance_status"
                    ],
                },
            )
        )
        if architect_replan_required and proposal_validation_failure_feedback is None:
            runtime_observations = {
                "coordination_scope": coordination_scope,
                "cross_workspace_conflict_verified": (
                    cross_workspace_conflict_verified
                ),
                "conflicting_artifact_ids": conflicting_artifact_ids,
                "conflicting_artifact_owners": conflicting_artifact_owners,
                "coordination_rationale": str(
                    coordination_assessment.get("rationale", "") or ""
                ),
                "formal_proof_work_pending": formal_proof_work_pending,
                "formal_debt_blocks_research_acceptance": (
                    formal_debt_blocks_research_acceptance
                ),
                "formal_debt_deferred_nonblocking": (
                    formal_debt_deferred_nonblocking
                ),
            }
            replan_feedback_body = {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "RuntimeCriticArchitectReplanObservations",
                "feedback_type": "critic_architect_replan_observations",
                "active_observation_id": str(
                    critic_environment_feedback.get(
                        "active_observation_id",
                        "",
                    )
                    or critic_environment_feedback.get("feedback_id", "")
                    or ""
                ),
                "failure_classification": str(
                    critic_environment_feedback.get(
                        "failure_classification",
                        "",
                    )
                    or ""
                ),
                "question_id": question.id,
                "source_theory_packet_id": str(
                    theory_packet.get("packet_id", "")
                    or context.get("theory_packet_id", "")
                    or ""
                ),
                "source_theory_packet_hash": (
                    stable_hash(dict(theory_packet)) if theory_packet else ""
                ),
                "critic_evaluator_manifest_id": manifest_id,
                "current_environment_observation": dict(
                    critic_environment_feedback
                ),
                "critic_model_packet_id": (
                    str(proposal_packet.get("packet_id", "") or "")
                    if proposal_packet is not None
                    else ""
                ),
                "runtime_observations": runtime_observations,
                "critic_environment_observations": {
                    "critic_feedback": dict(critic_runtime_observations),
                },
                "artifact_refs": {
                    "retrieval_manifest_id": retrieval_manifest_id,
                    "theory_packet_id": theory_packet_id,
                    "simulation_manifest_id": simulation_manifest_id,
                    "algorithm_manifest_id": algorithm_manifest_id,
                    "formalization_manifest_id": formalization_manifest_id,
                },
                "evidence_contract_decision": dict(evidence_contract_decision),
                "routing_authority": "ArchitectCoordinator_model_packet",
                "runtime_selected_owner": False,
                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            }
            replan_feedback = {
                **replan_feedback_body,
                "feedback_id": (
                    "critic_architect_replan_feedback:"
                    + stable_hash(replan_feedback_body)[:20]
                ),
            }
            replan_context = dict(context)
            replan_context["environment_feedback"] = replan_feedback
            replan_context["critic_architect_replan_observations"] = (
                replan_feedback
            )
            replan_context["runtime_feedback_loop"] = {
                **(
                    dict(context.get("runtime_feedback_loop", {}))
                    if isinstance(context.get("runtime_feedback_loop", {}), Mapping)
                    else {}
                ),
                "source_subsystem": "CriticEvaluator",
                "critic_revision_round": critic_round,
                "max_critic_revision_rounds": max_critic_revision_rounds,
                "critic_evaluator_manifest_id": manifest_id,
                "handoff": "critic_observations_to_architect_model",
                "runtime_selected_owner": False,
            }
            next_task = AgentTask(
                task_id=(
                    f"architect-critic-replan:{question.id}:"
                    f"{stable_hash([manifest_id, replan_feedback])[:8]}"
                ),
                owner_subsystem="ArchitectCoordinator",
                objective=(
                    "Choose the next evidence-producing worker from the complete "
                    "Critic model packet and exact runtime observations without "
                    "weakening evidence gates."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": replan_context,
                    "environment_feedback": replan_feedback,
                    "runtime_architect_operation": (
                        ARCHITECT_FEEDBACK_ROUTE_OPERATION
                    ),
                },
                allowed_tools=("model_backend", "blackboard", "evidence_ledger"),
                expected_artifacts=("architect_feedback_route_decision",),
                acceptance_gate=(
                    "a validated Architect model packet selects the next worker or "
                    "records a terminal blocker while preserving all evidence gates"
                ),
                stop_condition=(
                    "Architect model selects the next worker or records a blocker"
                ),
            )
            return AgentStepResult(
                status="REROUTE",
                rationale=(
                    "CriticEvaluator recorded unresolved observations and returned "
                    "the complete artifact lineage to ArchitectCoordinator; runtime "
                    "did not select a source-edit owner."
                ),
                produced_artifacts=produced_artifacts,
                observations=tuple(observations),
                evidence_entries=tuple(
                    row
                    for row in (
                        proposal_evidence,
                        evidence,
                    )
                    if row is not None
                ),
                next_task=next_task,
                failure_classification="critic_requested_architect_model_replan",
            )
        if proposal_validation_failure_feedback is not None:
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "CriticEvaluator exhausted its in-call structured-output "
                    "validation. The rejected packet and exact observations are "
                    "recorded at their source owner without an Architect routing "
                    "loop or outer Critic retry."
                ),
                produced_artifacts=produced_artifacts,
                observations=tuple(observations),
                evidence_entries=tuple(
                    row
                    for row in (
                        proposal_validation_failure_evidence,
                        evidence,
                    )
                    if row is not None
                ),
                failure_classification="critic_packet_validation_failed",
            )
        final_runtime_status = str(evidence_contract_decision["runtime_status"])
        final_acceptance_status = str(
            evidence_contract_decision["final_acceptance_status"]
        )
        return AgentStepResult(
            status=final_runtime_status,
            rationale=(
                "CriticEvaluator recorded an independent observation packet; "
                f"evidence_contract_status={final_acceptance_status}."
            ),
            produced_artifacts=produced_artifacts,
            observations=tuple(observations),
            evidence_entries=tuple(
                row
                for row in (
                    proposal_evidence,
                    proposal_validation_failure_evidence,
                    evidence,
                )
                if row is not None
            ),
            failure_classification=str(
                evidence_contract_decision.get("failure_classification", "") or ""
            ),
        )


def _persist_runtime_artifact_store(
    *,
    artifacts: Mapping[str, Any],
    out_dir: Path,
    question_id: str,
) -> tuple[dict[str, dict[str, Any]], Path]:
    """Persist blackboard payloads once and return compact content references."""

    store_root = out_dir / "runtime_artifact_store"
    blob_root = store_root / "blobs"
    index_root = store_root / "indexes"
    index_root.mkdir(parents=True, exist_ok=True)
    references: dict[str, dict[str, Any]] = {}
    for raw_artifact_id, payload in sorted(
        artifacts.items(), key=lambda item: str(item[0])
    ):
        artifact_id = str(raw_artifact_id)
        content_hash = stable_hash(payload)
        blob_path = blob_root / content_hash[:2] / f"{content_hash}.json"
        serialized = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        if not blob_path.exists():
            blob_path.parent.mkdir(parents=True, exist_ok=True)
            blob_path.write_text(serialized, encoding="utf-8")
        payload_kind = (
            str(payload.get("artifact_kind", "") or "")
            if isinstance(payload, Mapping)
            else ""
        )
        references[artifact_id] = {
            "artifact_kind": "RuntimeArtifactRef",
            "artifact_id": artifact_id,
            "content_hash": content_hash,
            "content_hash_algorithm": "sha256_stable_json_v1",
            "payload_kind": payload_kind,
            "payload_type": type(payload).__name__,
            "payload_keys": (
                sorted(str(key) for key in payload)
                if isinstance(payload, Mapping)
                else []
            ),
            "path": str(blob_path),
            "byte_size": len(serialized.encode("utf-8")),
            "evidence_status": "REFERENCE_ONLY_NOT_EVIDENCE",
        }
    index = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeArtifactStoreIndex",
        "question_id": question_id,
        "n_artifacts": len(references),
        "n_unique_blobs": len(
            {row["content_hash"] for row in references.values()}
        ),
        "artifacts": references,
        "boundary": (
            "Artifact references provide storage identity and lineage only. "
            "They are not statistical, simulation, or proof evidence."
        ),
    }
    index_path = index_root / f"{_safe_identifier(question_id)}.json"
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return references, index_path


def _runtime_task_payload_reference(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a stable task reference without retaining recursive task inputs."""

    try:
        reference = agent_task_reference(_agent_task_from_runtime_payload(payload))
    except ValueError:
        reference = None
    if reference is not None:
        return reference
    inputs = payload.get("inputs", {})
    return {
        "artifact_kind": "AgentTaskRef",
        "task_id": str(payload.get("task_id", "") or ""),
        "owner_subsystem": str(payload.get("owner_subsystem", "") or ""),
        "task_snapshot_hash": stable_hash(dict(payload)),
        "inputs_hash": stable_hash(inputs),
        "input_keys": (
            sorted(str(key) for key in inputs)
            if isinstance(inputs, Mapping)
            else []
        ),
    }


def formalizer_workspace_runtime_bindings(
    workspace: FormalizerWorkspaceRuntimeSubsystem,
) -> dict[str, FormalizerWorkspaceRuntimeSubsystem]:
    """Expose the single model-owned formalization workspace."""

    return {"FormalizationEvaluator": workspace}


def run_research_agent_runtime(
    questions: list[OpenResearchQuestion],
    out_dir: Path,
    *,
    theory_developer: LLMTheoryDeveloperAgent,
    architect_coordinator: LLMArchitectCoordinatorAgent | None = None,
    simulation_engineer: LLMSimulationEngineerAgent | None = None,
    algorithm_engineer: LLMAlgorithmEngineerAgent | None = None,
    formalizer: LLMFormalizerProofEngineerAgent | None = None,
    critic_evaluator: LLMCriticEvaluatorAgent | None = None,
    generated_code_semantic_reviewer: (
        LLMGeneratedCodeSemanticReviewerAgent | None
    ) = None,
    formal_target_semantic_reviewer: (
        LLMFormalTargetSemanticReviewerAgent | None
    ) = None,
    proof_state_provider: ProofStateFeedbackProvider | None = None,
    formal_source_retriever: Any | None = None,
    proof_search_provider: LeanProofSearchProvider | None = None,
    config: ResearchAgentRuntimeConfig = ResearchAgentRuntimeConfig(),
    architect_context: Mapping[str, Any] | None = None,
    initial_task_overrides: Mapping[str, AgentTask] | None = None,
    initial_blackboard_artifacts: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    config = _normalized_runtime_evaluation_model_config(config)
    if (
        _is_runtime_research_evaluation_mode(config.evaluation_mode)
        and generated_code_semantic_reviewer is None
    ):
        raise ValueError(
            "research evaluation requires an independent "
            "GeneratedCodeSemanticReviewer"
        )
    if (
        config.formal_target_semantic_review_required
        and formal_target_semantic_reviewer is None
    ):
        raise ValueError(
            "formal_target_semantic_review_required requires an independent "
            "FormalTargetSemanticReviewer"
        )
    formal_verification_policy = _normalized_formal_verification_policy(
        config.formal_verification_policy
    )
    requested_research_path = (
        _normalized_recommended_research_path(
            config.recommended_research_path,
            formal_verification_policy=formal_verification_policy,
        )
        if str(config.recommended_research_path or "").strip()
        else ""
    )
    runtime_architect_context = (
        _runtime_architect_context_with_requested_evidence_contract(
            architect_context or {},
            formal_verification_policy=formal_verification_policy,
            recommended_research_path=requested_research_path,
            evaluation_mode=config.evaluation_mode,
            formal_target_semantic_review_required=(
                config.formal_target_semantic_review_required
            ),
        )
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    persisted_trace_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    handoff_rows: list[dict[str, Any]] = []
    observation_rows: list[dict[str, Any]] = []
    tool_call_rows: list[dict[str, Any]] = []
    artifact_store_index_paths: list[str] = []
    progress_path = out_dir / "runtime_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    shared_formal_source_retriever = (
        formal_source_retriever or build_default_formal_source_retriever()
    )
    formal_source_provider_descriptor = provider_descriptor(
        shared_formal_source_retriever
    )
    proof_search_provider_descriptor = (
        provider_descriptor(proof_search_provider)
        if proof_search_provider is not None
        else {"configured": False}
    )
    proof_state_retrieval_descriptor = (
        ai4slt_proof_state_trace_rag_descriptor()
    )
    lean_provider_topology = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeLeanProviderTopology",
        "manifest_id": "runtime_lean_provider_topology:"
        + stable_hash(
            [
                formal_source_provider_descriptor,
                proof_search_provider_descriptor,
                proof_state_retrieval_descriptor,
            ]
        )[:20],
        "formal_source_retriever": formal_source_provider_descriptor,
        "proof_search_provider": proof_search_provider_descriptor,
        "proof_state_retrieval": proof_state_retrieval_descriptor,
        "proof_evidence_status": "LEAN_PROVIDER_TOPOLOGY_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": LEAN_PROVIDER_BOUNDARY,
    }
    llm_topology = _runtime_llm_topology(
        architect_coordinator=architect_coordinator,
        theory_developer=theory_developer,
        simulation_engineer=simulation_engineer,
        algorithm_engineer=algorithm_engineer,
        formalizer=formalizer,
        critic_evaluator=critic_evaluator,
        generated_code_semantic_reviewer=generated_code_semantic_reviewer,
        formal_target_semantic_reviewer=formal_target_semantic_reviewer,
        proof_state_provider=proof_state_provider,
        evaluation_claude_model_tier=config.evaluation_claude_model_tier,
        evaluation_claude_model=config.evaluation_claude_model,
    )
    if llm_topology["policy_status"] != "OK":
        raise ValueError(
            "LLM topology policy violation: "
            + "; ".join(str(row) for row in llm_topology["policy_violations"])
        )
    initial_task_overrides = dict(initial_task_overrides or {})
    initial_blackboard_artifacts = dict(initial_blackboard_artifacts or {})
    resume_hash_bound_artifact_ids_by_question = {
        str(question_id): sorted(
            _runtime_task_hash_bound_artifact_ids(
                task,
                (
                    initial_blackboard_artifacts.get(question_id, {})
                    if isinstance(
                        initial_blackboard_artifacts.get(question_id, {}),
                        Mapping,
                    )
                    else {}
                ),
            )
        )
        for question_id, task in initial_task_overrides.items()
    }
    resume_context = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeResumeContext",
        "n_initial_task_overrides": len(initial_task_overrides),
        "n_rehydrated_blackboard_artifact_sets": len(initial_blackboard_artifacts),
        "n_rehydrated_blackboard_artifacts": sum(
            len(value)
            for value in initial_blackboard_artifacts.values()
            if isinstance(value, Mapping)
        ),
        "question_ids": sorted(str(key) for key in initial_task_overrides),
        "resumed_from_pending_task": bool(initial_task_overrides),
        "n_hash_bound_resume_artifacts_preserved": sum(
            len(artifact_ids)
            for artifact_ids in (
                resume_hash_bound_artifact_ids_by_question.values()
            )
        ),
        "hash_bound_resume_artifact_ids_by_question": (
            resume_hash_bound_artifact_ids_by_question
        ),
        "boundary": (
            "Resume context preserves orchestration state across iteration budgets. "
            "Artifacts transitively bound by the pending task's persisted hashes "
            "are exempt from Architect-control metadata backfill, while proof-safety "
            "schema migrations remain fail-closed. Resume state is not proof "
            "evidence and does not imply that any theorem gap is closed."
        ),
    }
    for question in questions:
        resume_pending_task = initial_task_overrides.get(question.id)
        blackboard = BlackboardState(project_id=f"ai_statistician:{question.id}")
        rehydrated_artifacts = initial_blackboard_artifacts.get(question.id, {})
        if isinstance(rehydrated_artifacts, Mapping):
            blackboard.artifacts.update(
                _normalize_runtime_blackboard_artifacts(
                    rehydrated_artifacts,
                    architect_control_exempt_artifact_ids=(
                        resume_hash_bound_artifact_ids_by_question.get(
                            question.id,
                            [],
                        )
                    ),
                )
            )
        question_metadata = {
            "artifact_kind": "RuntimeQuestionMetadata",
            "question": _question_to_payload(question),
            "primary_task_family": _question_primary_task_family(question),
            "task_family_boundary": (
                "Task-family metadata is evaluation scope only. It is not proof "
                "evidence and does not imply theorem generalization."
            ),
        }
        blackboard.artifacts[f"runtime_question_metadata:{question.id}"] = (
            question_metadata
        )
        blackboard.artifacts[llm_topology["manifest_id"]] = llm_topology
        blackboard.artifacts[lean_provider_topology["manifest_id"]] = (
            lean_provider_topology
        )
        formalizer_workspace = FormalizerWorkspaceRuntimeSubsystem(
            proposal_agent=formalizer,
            proof_state_provider=proof_state_provider,
            formal_source_retriever=shared_formal_source_retriever,
            proof_search_provider=proof_search_provider,
            lean_candidate_root=out_dir / "formalizer_lean_candidates",
            lean_candidate_local_lean=config.formalizer_candidate_local_lean,
            lean_candidate_lean_project=(
                Path(config.formalizer_candidate_lean_project)
                if config.formalizer_candidate_lean_project
                else None
            ),
            lean_candidate_lean_timeout=config.formalizer_candidate_lean_timeout,
            architect_coordinator_available=architect_coordinator is not None,
            formal_target_semantic_reviewer_available=(
                formal_target_semantic_reviewer is not None
            ),
            formal_target_semantic_review_max_revisions=(
                config.formal_target_semantic_review_max_revisions
            ),
            runtime_config=config,
        )
        subsystems: dict[str, Any] = {
            "RetrievalMemory": RetrievalMemoryRuntimeSubsystem(
                formal_source_retriever=shared_formal_source_retriever,
            ),
            "TheoryDeveloper": TheoryDeveloperRuntimeSubsystem(
                theory_developer=theory_developer,
                n_runs=config.n_runs,
                seed=config.seed,
            ),
            "SimulationEvaluator": SimulationEvaluatorRuntimeSubsystem(
                proposal_agent=simulation_engineer,
                sandbox_root=out_dir / "generated_simulation_sandbox",
                timeout_s=config.generated_simulation_timeout_seconds,
                semantic_reviewer_available=(
                    generated_code_semantic_reviewer is not None
                ),
                semantic_review_max_revisions=(
                    config.generated_code_semantic_review_max_revisions
                ),
            ),
            "AlgorithmEngineer": AlgorithmEngineerRuntimeSubsystem(
                out_dir=out_dir / "algorithm_sandbox",
                n_runs=config.n_runs,
                seed=config.seed,
                proposal_agent=algorithm_engineer,
                semantic_reviewer_available=(
                    generated_code_semantic_reviewer is not None
                ),
                semantic_review_max_revisions=(
                    config.generated_code_semantic_review_max_revisions
                ),
            ),
            **formalizer_workspace_runtime_bindings(formalizer_workspace),
            "CriticEvaluator": CriticEvaluatorRuntimeSubsystem(
                proposal_agent=critic_evaluator,
                runtime_config=config,
            ),
        }
        if generated_code_semantic_reviewer is not None:
            subsystems[GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM] = (
                GeneratedCodeSemanticReviewerRuntimeSubsystem(
                    reviewer=generated_code_semantic_reviewer,
                    max_revisions=(
                        config.generated_code_semantic_review_max_revisions
                    ),
                )
            )
        if formal_target_semantic_reviewer is not None:
            subsystems[FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM] = (
                FormalTargetSemanticReviewerRuntimeSubsystem(
                    reviewer=formal_target_semantic_reviewer,
                    max_revisions=(
                        config.formal_target_semantic_review_max_revisions
                    ),
                )
            )
        if architect_coordinator is not None:
            subsystems = {
                "ArchitectCoordinator": ArchitectCoordinatorRuntimeSubsystem(
                    coordinator=architect_coordinator,
                    runtime_config=config,
                    proof_search_tool_available=(
                        proof_search_provider is not None
                    ),
                ),
                **subsystems,
            }
        runtime = AgentRuntime(
            subsystems=subsystems,
            blackboard=blackboard,
            handoff_policy=(
                (
                    lambda **kwargs: _runtime_transition_policy(
                        **kwargs,
                        runtime_config=config,
                    )
                )
                if architect_coordinator is not None
                else None
            ),
        )
        def record_progress(row: dict[str, Any]) -> None:
            _append_jsonl_row(
                progress_path,
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "question_id": question.id,
                    "question_title": question.title,
                    **row,
                },
            )

        if (
            resume_pending_task is not None
            and config.resume_through_architect
            and architect_coordinator is not None
        ):
            initial_task = AgentTask(
                task_id=f"architect-resume:{question.id}:{stable_hash(asdict(resume_pending_task))[:8]}",
                owner_subsystem="ArchitectCoordinator",
                objective=(
                    "Review the resumed pending AgentRuntime task, refresh the "
                    "Architect evidence contract, and route back to the pending "
                    "subsystem without claiming proof evidence."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": dict(runtime_architect_context),
                    "resume_pending_task": asdict(resume_pending_task),
                    "resume_review_contract": {
                        "artifact_kind": "RuntimeArchitectResumeReviewContract",
                        "pending_task_id": resume_pending_task.task_id,
                        "pending_owner_subsystem": resume_pending_task.owner_subsystem,
                        "proof_evidence_status": (
                            "ARCHITECT_RESUME_REVIEW_NOT_PROOF_EVIDENCE"
                        ),
                        "boundary": (
                            "Architect resume review is orchestration evidence only. "
                            "It may refresh routing context but cannot prove a theorem, "
                            "validate generated code, or close a formal gap."
                        ),
                    },
                },
                allowed_tools=("model_backend", "blackboard"),
                expected_artifacts=(
                    "architect_coordinator_proposal",
                    "architect_resume_review_handoff",
                ),
                acceptance_gate=(
                    "validated coordinator packet refreshes evidence contract "
                    "and returns to the pending task"
                ),
                stop_condition="coordinator routes back to the pending subsystem",
            )
        else:
            initial_task = resume_pending_task or (
                AgentTask(
                    task_id=f"architect:{question.id}",
                    owner_subsystem="ArchitectCoordinator",
                    objective=(
                        "Create the top-level AI Statistician execution plan, evidence gates, "
                        "retrieval priorities, and iteration policy before runtime execution."
                    ),
                    inputs={
                        "question": _question_to_payload(question),
                        "architect_context": dict(runtime_architect_context),
                    },
                    allowed_tools=("model_backend", "blackboard"),
                    expected_artifacts=("architect_coordinator_proposal",),
                    acceptance_gate="validated coordinator packet with explicit non-proof boundary",
                    stop_condition="coordinator routes to RetrievalMemory",
                )
                if architect_coordinator is not None
                else AgentTask(
                    task_id=f"retrieve:{question.id}",
                    owner_subsystem="RetrievalMemory",
                    objective="Retrieve paper, statistical knowledge, and formal-source context before theory derivation.",
                    inputs={
                        "question": _question_to_payload(question),
                        "architect_context": dict(runtime_architect_context),
                    },
                    allowed_tools=("research_knowledge", "paper_index", "formal_source_retriever"),
                    expected_artifacts=("retrieval_memory_manifest",),
                    acceptance_gate="retrieval context recorded with explicit non-proof boundary",
                    stop_condition="retrieval context routed to TheoryDeveloper",
                )
            )
        if (
            resume_pending_task is not None
            and not (
                config.resume_through_architect and architect_coordinator is not None
            )
            and runtime_architect_context
        ):
            initial_task = _merge_resume_task_architect_context(
                initial_task,
                runtime_architect_context,
            )
        result = runtime.run(
            initial_task,
            max_iterations=config.max_iterations,
            max_transient_subsystem_retries=config.max_subsystem_retries,
            progress_callback=record_progress,
        )
        result_json = result.to_json(include_task_payloads=True)
        persisted_result_json = result.to_json(include_task_payloads=False)
        persisted_result_json["trace_task_payload_policy"] = (
            "content_addressed_refs"
        )
        artifact_refs, artifact_store_index_path = (
            _persist_runtime_artifact_store(
                artifacts=result.blackboard.artifacts,
                out_dir=out_dir,
                question_id=question.id,
            )
        )
        persisted_result_json["blackboard"]["artifacts"] = artifact_refs
        persisted_result_json["blackboard_artifact_payload_policy"] = (
            "content_addressed_refs"
        )
        persisted_result_json["blackboard_artifact_store_index"] = str(
            artifact_store_index_path
        )
        artifact_store_index_paths.append(str(artifact_store_index_path))
        result_path = out_dir / f"{_safe_identifier(question.id)}_runtime_result.json"
        result_path.write_text(
            json.dumps(persisted_result_json, indent=2, default=str),
            encoding="utf-8",
        )
        result_json["artifact_path"] = str(result_path)
        results.append(result_json)
        blackboard_json = (
            result_json.get("blackboard", {})
            if isinstance(result_json.get("blackboard", {}), Mapping)
            else {}
        )
        raw_evidence_ledger = (
            blackboard_json.get("evidence_ledger", [])
            if isinstance(blackboard_json.get("evidence_ledger", []), list)
            else []
        )
        for evidence_index, evidence in enumerate(raw_evidence_ledger):
            if not isinstance(evidence, Mapping):
                continue
            evidence_rows.append(
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "question_id": question.id,
                    "question_title": question.title,
                    "project_id": str(blackboard_json.get("project_id", "") or ""),
                    "evidence_index": evidence_index,
                    **dict(evidence),
                }
            )
        raw_handoff_ledger = (
            blackboard_json.get("handoff_ledger", [])
            if isinstance(blackboard_json.get("handoff_ledger", []), list)
            else []
        )
        for handoff in raw_handoff_ledger:
            if not isinstance(handoff, Mapping):
                continue
            handoff_rows.append(
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "question_id": question.id,
                    "question_title": question.title,
                    "project_id": str(blackboard_json.get("project_id", "") or ""),
                    **dict(handoff),
                }
            )
        for trace_index, trace in enumerate(result_json["traces"]):
            trace_rows.append(
                {
                    "question_id": question.id,
                    "question_title": question.title,
                    **trace,
                }
            )
            persisted_trace = persisted_result_json["traces"][trace_index]
            persisted_trace_rows.append(
                {
                    "question_id": question.id,
                    "question_title": question.title,
                    **persisted_trace,
                }
            )
            task_payload = (
                trace.get("task", {})
                if isinstance(trace.get("task", {}), Mapping)
                else {}
            )
            raw_observations = (
                trace.get("observations", [])
                if isinstance(trace.get("observations", []), list)
                else []
            )
            for observation_index, observation in enumerate(raw_observations):
                if not isinstance(observation, Mapping):
                    continue
                observation_rows.append(
                    {
                        "schema_version": RUNTIME_SCHEMA_VERSION,
                        "question_id": question.id,
                        "question_title": question.title,
                        "trace_index": trace_index,
                        "iteration": int(trace.get("iteration", 0) or 0),
                        "task_id": str(task_payload.get("task_id", "") or ""),
                        "subsystem": str(trace.get("subsystem", "") or ""),
                        "status": str(trace.get("status", "") or ""),
                        "observation_index": observation_index,
                        **dict(observation),
                    }
                )
            raw_tool_calls = (
                trace.get("tool_calls", [])
                if isinstance(trace.get("tool_calls", []), list)
                else []
            )
            for tool_call_index, tool_call in enumerate(raw_tool_calls):
                if not isinstance(tool_call, Mapping):
                    continue
                tool_call_rows.append(
                    {
                        "schema_version": RUNTIME_SCHEMA_VERSION,
                        "question_id": question.id,
                        "question_title": question.title,
                        "trace_index": trace_index,
                        "iteration": int(trace.get("iteration", 0) or 0),
                        "task_id": str(task_payload.get("task_id", "") or ""),
                        "subsystem": str(trace.get("subsystem", "") or ""),
                        "status": str(trace.get("status", "") or ""),
                        "tool_call_index": tool_call_index,
                        **dict(tool_call),
                    }
                )

    traces_path = out_dir / "runtime_traces.jsonl"
    _write_jsonl(traces_path, persisted_trace_rows)
    evidence_ledger_path = out_dir / "runtime_evidence_ledger.jsonl"
    _write_jsonl(evidence_ledger_path, evidence_rows)
    task_handoffs_path = out_dir / "runtime_task_handoffs.jsonl"
    _write_jsonl(task_handoffs_path, handoff_rows)
    observations_path = out_dir / "runtime_observations.jsonl"
    _write_jsonl(observations_path, observation_rows)
    tool_calls_path = out_dir / "runtime_tool_calls.jsonl"
    _write_jsonl(tool_calls_path, tool_call_rows)
    llm_topology_path = out_dir / "runtime_llm_topology.json"
    llm_topology_path.write_text(json.dumps(llm_topology, indent=2, default=str), encoding="utf-8")
    manifest_path = out_dir / "research_agent_runtime_manifest.json"
    n_architect_coordinator_traces = sum(
        1
        for row in trace_rows
        if str(row.get("subsystem", "") or "") == "ArchitectCoordinator"
    )
    status_counts: dict[str, int] = {}
    for row in results:
        status = str(row["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    completion_summary = _runtime_completion_summary(results)
    failure_summary = _runtime_failure_summary(completion_summary)
    pending_next_task_rows = _runtime_pending_next_task_rows(
        completion_summary
    )
    completion_summary_path = out_dir / "runtime_completion_summary.json"
    failure_summary_path = out_dir / "runtime_failure_summary.json"
    completion_summary_path.write_text(
        json.dumps(completion_summary, indent=2, default=str),
        encoding="utf-8",
    )
    failure_summary_path.write_text(
        json.dumps(failure_summary, indent=2, default=str),
        encoding="utf-8",
    )
    latest_evidence: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in evidence_rows:
        payload = row.get("payload", {})
        if not isinstance(payload, Mapping):
            continue
        latest_evidence[
            (
                str(row.get("question_id", "") or ""),
                str(row.get("evidence_type", "") or ""),
            )
        ] = payload

    def payloads(evidence_type: str) -> list[Mapping[str, Any]]:
        return [
            payload
            for (_question_id, row_type), payload in latest_evidence.items()
            if row_type == evidence_type
        ]

    def payload_int(payload: Mapping[str, Any], key: str) -> int:
        try:
            return max(0, int(payload.get(key, 0) or 0))
        except (TypeError, ValueError):
            return 0

    algorithm_payloads = payloads("algorithm_sandbox")
    simulation_payloads = payloads("simulation")
    formalization_payloads = payloads("formalization_proof_feedback")
    formalizer_payloads = payloads("llm_formalizer_proof_engineer_proposal")
    formalizer_failure_payloads = payloads("formalizer_packet_validation_failure")
    formalizer_client_tool_payloads = [
        payload
        for payload in formalizer_failure_payloads
        if _bool_like(payload.get("model_owned_lean_code", False))
        and not _bool_like(payload.get("runtime_selected_lean_code", True))
        and bool(str(payload.get("candidate_source_hash", "") or ""))
    ]
    n_kernel_verified_subclaims = sum(
        payload_int(
            payload.get("counts", {})
            if isinstance(payload.get("counts", {}), Mapping)
            else {},
            "kernel_verified",
        )
        for payload in formalization_payloads
    )
    n_formal_gaps = sum(
        payload_int(
            payload.get("counts", {})
            if isinstance(payload.get("counts", {}), Mapping)
            else {},
            "formal_gap",
        )
        for payload in formalization_payloads
    )
    n_full_frontier_theorem_proved = sum(
        1
        for payload in formalization_payloads
        if _bool_like(payload.get("source_theorem_kernel_verified", False))
        and bool(payload.get("source_theorem_kernel_verified_target_ids", []) or [])
    )
    formal_closure_summary = _runtime_formal_closure_summary(
        completion_summary=completion_summary,
        n_materialized_formal_gap_rows=n_formal_gaps,
    )
    formalizer_client_tool_observation_summary = {
        "n_workspaces_observed": len(formalizer_client_tool_payloads),
        "n_source_updates": sum(
            payload_int(payload, "source_updates")
            for payload in formalizer_client_tool_payloads
        ),
        "n_local_lean_checks": sum(
            payload_int(payload, "local_lean_checks")
            for payload in formalizer_client_tool_payloads
        ),
        "n_formal_rag_tool_calls": sum(
            payload_int(payload, "n_formal_rag_tool_calls")
            for payload in formalizer_client_tool_payloads
        ),
        "n_compiled_checkpoints": sum(
            1
            for payload in formalizer_client_tool_payloads
            if _bool_like(payload.get("latest_check_compiled", False))
        ),
        "proof_evidence_status": "FORMALIZER_CLIENT_TOOL_OBSERVATIONS_NOT_PROOF_EVIDENCE",
    }
    runtime_resume_policy = (
        "fresh_start"
        if not initial_task_overrides
        else "architect_resume_review"
        if config.resume_through_architect and architect_coordinator is not None
        else "direct_pending_task"
    )
    artifacts = {
        "runtime_progress_jsonl": str(progress_path),
        "runtime_traces_jsonl": str(traces_path),
        "runtime_evidence_ledger_jsonl": str(evidence_ledger_path),
        "runtime_task_handoffs_jsonl": str(task_handoffs_path),
        "runtime_observations_jsonl": str(observations_path),
        "runtime_tool_calls_jsonl": str(tool_calls_path),
        "runtime_llm_topology_json": str(llm_topology_path),
        "per_question_results": [str(row["artifact_path"]) for row in results],
        "runtime_artifact_store_indexes": list(artifact_store_index_paths),
    }
    artifacts["runtime_completion_summary_json"] = str(
        completion_summary_path
    )
    artifacts["runtime_failure_summary_json"] = str(failure_summary_path)

    manifest = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "ResearchAgentRuntimeManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_endpoint": "typed_agent_runtime",
        "runtime_formal_capability_source": "integrated_agent_runtime_only",
        "runtime_evaluation_mode": config.evaluation_mode,
        "runtime_trace_task_payload_policy": "content_addressed_refs",
        "runtime_blackboard_artifact_payload_policy": "content_addressed_refs",
        "runtime_evaluation_claude_model_tier": (
            config.evaluation_claude_model_tier
        ),
        "runtime_evaluation_claude_model": config.evaluation_claude_model,
        "n_questions": len(questions),
        "question_ids": [question.id for question in questions],
        "question_titles": [question.title for question in questions],
        "question_task_families": {
            question.id: _question_primary_task_family(question)
            for question in questions
        },
        "config": asdict(config),
        "runtime_input_context": _runtime_input_context_summary(
            runtime_architect_context
        ),
        "runtime_resume_context": resume_context,
        "runtime_resume_policy": runtime_resume_policy,
        "runtime_architect_coordinator_registered": (
            architect_coordinator is not None
        ),
        "runtime_architect_coordinator_executed": (
            n_architect_coordinator_traces > 0
        ),
        "n_runtime_architect_coordinator_traces": (
            n_architect_coordinator_traces
        ),
        "status_counts": dict(sorted(status_counts.items())),
        "runtime_completion_summary": completion_summary,
        "runtime_failure_summary": failure_summary,
        "runtime_terminal_kind": failure_summary["terminal_kind"],
        "research_evaluation_summary": build_research_evaluation_summary(
            results,
            evaluation_mode=config.evaluation_mode,
            schema_version=RUNTIME_SCHEMA_VERSION,
        ),
        "n_runtime_traces": len(trace_rows),
        "n_runtime_evidence_ledger_rows": len(evidence_rows),
        "n_runtime_task_handoffs": len(handoff_rows),
        "n_runtime_observations": len(observation_rows),
        "n_runtime_tool_calls": len(tool_call_rows),
        "n_generated_code_sandbox_executed": sum(
            payload_int(payload, "n_generated_code_executed")
            for payload in algorithm_payloads
        ),
        "n_live_generated_code_sandbox_executed": sum(
            payload_int(payload, "n_live_generated_code_executed")
            for payload in algorithm_payloads
        ),
        "n_generated_simulation_sandbox_executed": sum(
            payload_int(payload, "n_generated_simulation_sandbox_executed")
            for payload in simulation_payloads
        ),
        "n_live_generated_simulation_sandbox_executed": sum(
            payload_int(payload, "n_live_generated_simulation_sandbox_executed")
            for payload in simulation_payloads
        ),
        "n_live_llm_formalizer_proof_engineer_proposals": sum(
            1
            for payload in formalizer_payloads
            if _bool_like(payload.get("source_llm_proposal_live_generator", False))
        ),
        "n_kernel_verified_subclaims": n_kernel_verified_subclaims,
        "n_materialized_formal_gap_rows": n_formal_gaps,
        "n_formal_gaps": n_formal_gaps,
        "formal_closure_summary": formal_closure_summary,
        "n_full_frontier_theorem_proved": n_full_frontier_theorem_proved,
        "formalizer_client_tool_observation_summary": (
            formalizer_client_tool_observation_summary
        ),
        "n_formalizer_lean_candidate_local_lean_checked": sum(
            payload_int(payload, "n_local_lean_checked")
            for payload in formalizer_payloads
        ) + sum(
            1
            for payload in formalizer_client_tool_payloads
            if payload_int(payload, "local_lean_checks") > 0
        ),
        "n_formalizer_lean_candidate_local_lean_compiled": sum(
            payload_int(payload, "n_local_lean_compiled")
            for payload in formalizer_payloads
        ) + sum(
            1
            for payload in formalizer_client_tool_payloads
            if _bool_like(payload.get("latest_check_compiled", False))
        ),
        "llm_topology_policy_ok": llm_topology["policy_status"] == "OK",
        "llm_runtime_topology": llm_topology,
        "lean_provider_topology": lean_provider_topology,
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "simulation_evidence_boundary": SIMULATION_NOT_PROOF_BOUNDARY,
        "manifest_boundary": (
            "This compact manifest indexes runtime traces, observations, tool "
            "calls, and evidence. It does not infer capability or prescribe a "
            "repair; the independent audit reads the referenced primary records."
        ),
        "artifacts": artifacts,
    }
    if pending_next_task_rows:
        exported_pending_rows = [
            {
                **dict(row),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "runtime_task_handoffs_jsonl": str(task_handoffs_path),
                "source_manifest_path": str(manifest_path),
            }
            for row in pending_next_task_rows
        ]
        pending_next_tasks_path = out_dir / "runtime_pending_next_tasks.jsonl"
        _write_jsonl(pending_next_tasks_path, exported_pending_rows)
        manifest["n_incomplete_pending_next_tasks"] = len(
            exported_pending_rows
        )
        manifest["incomplete_pending_next_tasks"] = (
            pending_next_task_rows
        )
        manifest["artifacts"]["runtime_pending_next_tasks_jsonl"] = str(
            pending_next_tasks_path
        )

    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return manifest



def _runtime_llm_topology(
    *,
    architect_coordinator: LLMArchitectCoordinatorAgent | None,
    theory_developer: LLMTheoryDeveloperAgent,
    simulation_engineer: LLMSimulationEngineerAgent | None,
    algorithm_engineer: LLMAlgorithmEngineerAgent | None,
    formalizer: LLMFormalizerProofEngineerAgent | None,
    critic_evaluator: LLMCriticEvaluatorAgent | None,
    generated_code_semantic_reviewer: (
        LLMGeneratedCodeSemanticReviewerAgent | None
    ) = None,
    formal_target_semantic_reviewer: (
        LLMFormalTargetSemanticReviewerAgent | None
    ) = None,
    proof_state_provider: ProofStateFeedbackProvider | None,
    evaluation_claude_model_tier: str = "",
    evaluation_claude_model: str = "",
) -> dict[str, Any]:
    agents = [
        _llm_agent_topology_row(
            "ArchitectCoordinator",
            architect_coordinator,
            role="top-level research plan, evidence gates, and subsystem routing",
        ),
        _llm_agent_topology_row(
            "ArchitectMetricSemanticReviewer",
            (
                architect_coordinator.metric_semantic_reviewer
                if architect_coordinator is not None
                else None
            ),
            role=(
                "independent pre-execution semantic and mathematical review of "
                "Architect-authored typed empirical metric contracts"
            ),
        ),
        _llm_agent_topology_row(
            "TheoryDeveloper",
            theory_developer,
            role="deductive statistical theory discovery and theorem/procedure proposal",
        ),
        _llm_agent_topology_row(
            "SimulationEngineer",
            simulation_engineer,
            role="simulation and falsifier proposal under runtime execution gates",
        ),
        _llm_agent_topology_row(
            "AlgorithmEngineer",
            algorithm_engineer,
            role="algorithm prototype and stress-test implementation proposal",
        ),
        _llm_agent_topology_row(
            "FormalizerProofEngineer",
            formalizer,
            role="Lean/formal-target/proof-search proposal before kernel gates",
        ),
        _llm_agent_topology_row(
            "GeneratedCodeSemanticReviewer",
            generated_code_semantic_reviewer,
            role=(
                "independent semantic review of exact executed generated code, "
                "runtime arguments, metrics, theory, and frozen protocols"
            ),
        ),
        _llm_agent_topology_row(
            "FormalTargetSemanticReviewer",
            formal_target_semantic_reviewer,
            role=(
                "independent mathematical review of exact theorem statements "
                "against the question, derivation, assumptions, and constraints"
            ),
        ),
        _llm_agent_topology_row(
            "CriticEvaluator",
            critic_evaluator,
            role="boundary audit, learning rows, and next-action triage",
        ),
    ]
    enabled = [row for row in agents if row["enabled"]]
    evaluation_claude_model_tier = str(
        evaluation_claude_model_tier or ""
    ).strip().lower()
    evaluation_claude_model = str(evaluation_claude_model or "").strip()
    if evaluation_claude_model_tier:
        for row in agents:
            row["production_expected_model_tier"] = str(
                row.get("expected_model_tier", "") or ""
            )
            row["expected_model_tier"] = evaluation_claude_model_tier
            if "serious_model_tier" in row:
                row["production_expected_serious_model_tier"] = str(
                    row.get("expected_serious_model_tier", "") or ""
                )
                row["expected_serious_model_tier"] = (
                    evaluation_claude_model_tier
                )
    by_tier: dict[str, int] = {}
    by_provider: dict[str, int] = {}
    for row in enabled:
        tier = str(row.get("model_tier", ""))
        provider = str(row.get("provider_name", ""))
        by_tier[tier] = by_tier.get(tier, 0) + 1
        by_provider[provider] = by_provider.get(provider, 0) + 1
    claude_tier_contract = claude_tier_routing_contract()
    resolved_claude_models_by_tier = dict(
        claude_tier_contract.get("resolved_claude_models_by_tier", {})
    )
    resolved_claude_model_tier_policy_violations = list(
        claude_tier_contract.get("resolved_claude_model_tier_policy_violations", ())
    )
    resolved_claude_model_freshness_warnings = list(
        claude_tier_contract.get("resolved_claude_model_freshness_warnings", ())
    )
    violations = _llm_topology_policy_violations(agents) + [
        "resolved Claude model tier policy violation: " + violation
        for violation in resolved_claude_model_tier_policy_violations
    ]
    if evaluation_claude_model:
        for row in enabled:
            providers = {
                str(row.get("provider_name", "") or "").strip().lower(),
                str(row.get("backend_provider_name", "") or "").strip().lower(),
            }
            backend_provider = str(
                row.get("backend_provider_name", "") or ""
            ).strip().lower()
            if (
                backend_provider in SUPPORTED_LIVE_GENERATOR_PROVIDERS
                and backend_provider != "anthropic"
            ):
                violations.append(
                    f"{row.get('subsystem')} research evaluation requires the "
                    "Anthropic Haiku backend but resolved "
                    f"{backend_provider}"
                )
                continue
            if "anthropic" not in providers:
                continue
            if str(row.get("model", "") or "") != evaluation_claude_model:
                violations.append(
                    f"{row.get('subsystem')} live evaluation requires model "
                    f"{evaluation_claude_model} but resolved "
                    f"{str(row.get('model', '') or 'missing')}"
                )
            serious_model = str(row.get("serious_model", "") or "")
            if serious_model and serious_model != evaluation_claude_model:
                violations.append(
                    f"{row.get('subsystem')} serious live evaluation requires "
                    f"model {evaluation_claude_model} but resolved {serious_model}"
                )
    agents_by_subsystem = {str(row.get("subsystem", "")): row for row in agents}

    def _subsystem_field(subsystem: str, field: str) -> str:
        return str(agents_by_subsystem.get(subsystem, {}).get(field, "") or "")

    manifest = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeLLMTopologyManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "default_live_provider": "anthropic",
            "supported_live_generator_providers": list(SUPPORTED_LIVE_GENERATOR_PROVIDERS),
            "supported_generator_providers": list(SUPPORTED_GENERATOR_PROVIDERS),
            "claude_model_selection": ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
            "claude_tier_routing_contract": claude_tier_contract,
            "resolved_claude_models_by_tier": resolved_claude_models_by_tier,
            "resolved_claude_model_tier_policy_status": (
                claude_tier_contract.get(
                    "resolved_claude_model_tier_policy_status",
                    "",
                )
            ),
            "resolved_claude_model_tier_policy_violations": (
                resolved_claude_model_tier_policy_violations
            ),
            "resolved_claude_model_freshness_status": (
                claude_tier_contract.get(
                    "resolved_claude_model_freshness_status",
                    "",
                )
            ),
            "resolved_claude_model_freshness_warnings": (
                resolved_claude_model_freshness_warnings
            ),
            "expected_subsystem_model_tiers": (
                AI_STATISTICIAN_LLM_SUBSYSTEM_MODEL_TIER_POLICY
            ),
            "expected_contextual_model_tiers": (
                AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY
            ),
            "model_tier_assignment_policy": (
                "centralized_subsystem_policy_from_model_backend"
            ),
            "evaluation_claude_model_tier": evaluation_claude_model_tier,
            "evaluation_claude_model": evaluation_claude_model,
            "backend_boundary": (
                "LLM backends generate structured proposals only. AgentRuntime owns "
                "tool use, filesystem changes, execution, tests, Lean checks, and evidence promotion."
            ),
        },
        "llm_agents": agents,
        "provider_counts": dict(sorted(by_provider.items())),
        "model_tier_counts": dict(sorted(by_tier.items())),
        "unsupported_provider_count": sum(
            1 for row in enabled if _has_unsupported_generator_provider(row)
        ),
        "generator_only_all_enabled": all(
            bool(row.get("generator_only", False)) for row in enabled
        ),
        "default_provider": "anthropic",
        "architect_provider": _subsystem_field("ArchitectCoordinator", "provider_name"),
        "architect_metric_semantic_reviewer_provider": _subsystem_field(
            "ArchitectMetricSemanticReviewer", "provider_name"
        ),
        "theory_developer_provider": _subsystem_field("TheoryDeveloper", "provider_name"),
        "simulation_engineer_provider": _subsystem_field(
            "SimulationEngineer", "provider_name"
        ),
        "algorithm_engineer_provider": _subsystem_field(
            "AlgorithmEngineer", "provider_name"
        ),
        "formalizer_provider": _subsystem_field(
            "FormalizerProofEngineer", "provider_name"
        ),
        "critic_evaluator_provider": _subsystem_field(
            "CriticEvaluator", "provider_name"
        ),
        "generated_code_semantic_reviewer_provider": _subsystem_field(
            "GeneratedCodeSemanticReviewer", "provider_name"
        ),
        "formal_target_semantic_reviewer_provider": _subsystem_field(
            "FormalTargetSemanticReviewer", "provider_name"
        ),
        "architect_model": _subsystem_field("ArchitectCoordinator", "model"),
        "architect_metric_semantic_reviewer_model": _subsystem_field(
            "ArchitectMetricSemanticReviewer", "model"
        ),
        "theory_developer_model": _subsystem_field("TheoryDeveloper", "model"),
        "theory_developer_serious_model": _subsystem_field(
            "TheoryDeveloper", "serious_model"
        ),
        "simulation_engineer_model": _subsystem_field("SimulationEngineer", "model"),
        "algorithm_engineer_model": _subsystem_field("AlgorithmEngineer", "model"),
        "formalizer_model": _subsystem_field("FormalizerProofEngineer", "model"),
        "critic_evaluator_model": _subsystem_field("CriticEvaluator", "model"),
        "generated_code_semantic_reviewer_model": _subsystem_field(
            "GeneratedCodeSemanticReviewer", "model"
        ),
        "formal_target_semantic_reviewer_model": _subsystem_field(
            "FormalTargetSemanticReviewer", "model"
        ),
        "architect_model_tier": _subsystem_field("ArchitectCoordinator", "model_tier"),
        "architect_metric_semantic_reviewer_model_tier": _subsystem_field(
            "ArchitectMetricSemanticReviewer", "model_tier"
        ),
        "theory_developer_model_tier": _subsystem_field("TheoryDeveloper", "model_tier"),
        "theory_developer_serious_model_tier": _subsystem_field(
            "TheoryDeveloper", "serious_model_tier"
        ),
        "simulation_engineer_model_tier": _subsystem_field(
            "SimulationEngineer", "model_tier"
        ),
        "algorithm_engineer_model_tier": _subsystem_field(
            "AlgorithmEngineer", "model_tier"
        ),
        "formalizer_model_tier": _subsystem_field(
            "FormalizerProofEngineer", "model_tier"
        ),
        "critic_evaluator_model_tier": _subsystem_field(
            "CriticEvaluator", "model_tier"
        ),
        "generated_code_semantic_reviewer_model_tier": _subsystem_field(
            "GeneratedCodeSemanticReviewer", "model_tier"
        ),
        "formal_target_semantic_reviewer_model_tier": _subsystem_field(
            "FormalTargetSemanticReviewer", "model_tier"
        ),
        "policy_status": "OK" if not violations else "POLICY_VIOLATION",
        "policy_violations": violations,
        "non_llm_runtime_providers": {
            "proof_state_provider": getattr(proof_state_provider, "name", "") if proof_state_provider else "",
            "proof_state_feedback_is_proof_evidence": False,
        },
        "counts": {
            "llm_agents_total": len(agents),
            "llm_agents_enabled": len(enabled),
            "llm_agents_disabled": len(agents) - len(enabled),
            "enabled_by_model_tier": dict(sorted(by_tier.items())),
            "enabled_by_provider": dict(sorted(by_provider.items())),
            "unsupported_generator_backends_enabled": sum(
                1 for row in enabled if _has_unsupported_generator_provider(row)
            ),
            "anthropic_model_tier_mismatches": sum(
                1 for row in enabled if _anthropic_model_tier_mismatch(row)
            ),
            "anthropic_serious_model_tier_mismatches": sum(
                1
                for row in enabled
                if _anthropic_serious_model_tier_mismatch(row)
            ),
            "subsystem_model_tier_policy_mismatches": sum(
                1 for row in enabled if _subsystem_model_tier_mismatch(row)
            ),
            "contextual_model_tier_policy_mismatches": sum(
                1 for row in enabled if _contextual_model_tier_mismatch(row)
            ),
            "resolved_claude_model_tier_policy_violations": len(
                resolved_claude_model_tier_policy_violations
            ),
        },
        "boundary": (
            "This manifest is runtime/model provenance and cost-control metadata. "
            "It is not proof, simulation, or implementation evidence."
        ),
    }
    manifest["manifest_id"] = "runtime_llm_topology:" + stable_hash(
        [
            manifest["policy"],
            manifest["llm_agents"],
            manifest["non_llm_runtime_providers"],
        ]
    )[:20]
    return manifest


def _merge_resume_task_architect_context(
    task: AgentTask,
    architect_context: Mapping[str, Any],
) -> AgentTask:
    """Attach fresh run context to a resumed task without dropping resume state."""

    if not architect_context:
        return task
    inputs = dict(task.inputs)
    existing_context = (
        inputs.get("architect_context", {})
        if isinstance(inputs.get("architect_context", {}), Mapping)
        else {}
    )
    merged_context = dict(existing_context)
    merged_context.pop("runtime_learning_memory", None)
    merged_context.pop("runtime_capability_gap_routing", None)
    for key, value in architect_context.items():
        if key not in {"runtime_learning_memory", "runtime_capability_gap_routing"}:
            merged_context[key] = value
    inputs["architect_context"] = merged_context
    return replace(task, inputs=inputs)
























def _runtime_llm_topology_enabled_agent_rows(
    topology: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    agents = topology.get("llm_agents", [])
    if not isinstance(agents, list):
        return []
    return [
        row
        for row in agents
        if isinstance(row, Mapping) and bool(row.get("enabled", False))
    ]


def _runtime_llm_topology_row_is_live_generator(row: Mapping[str, Any]) -> bool:
    if not bool(row.get("enabled", False)):
        return False
    provider = normalize_generator_provider_name(row.get("provider_name", ""))
    backend_provider = normalize_generator_provider_name(
        row.get("backend_provider_name", "")
    )
    return is_live_generator_backend(provider, backend_provider)


def _runtime_llm_proposal_packet_provider(packet: Mapping[str, Any]) -> str:
    return normalize_generator_provider_name(
        packet.get("provider", "") or packet.get("provider_name", "")
    )


def _runtime_llm_proposal_packet_backend_provider(packet: Mapping[str, Any]) -> str:
    return normalize_generator_provider_name(
        packet.get("backend_provider", "") or packet.get("backend_provider_name", "")
    )


def _runtime_llm_proposal_packet_live_generator(packet: Mapping[str, Any]) -> bool:
    provider = _runtime_llm_proposal_packet_provider(packet)
    backend_provider = _runtime_llm_proposal_packet_backend_provider(packet)
    return is_live_generator_backend(provider, backend_provider)


_GENERATED_SANDBOX_EXECUTION_FEEDBACK_TYPES = frozenset(
    {
        "algorithm_sandbox_execution_feedback",
        "generated_simulation_sandbox_execution_feedback",
    }
)


def _generated_sandbox_execution_feedback_snapshot(
    feedback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return the ID-bearing sandbox feedback without semantic-review overlays."""

    if not isinstance(feedback, Mapping):
        return {}
    nested = feedback.get("source_execution_feedback", {})
    candidates = (
        nested if isinstance(nested, Mapping) else {},
        feedback,
    )
    for candidate in candidates:
        feedback_type = str(candidate.get("feedback_type", "") or "").strip()
        if (
            feedback_type not in _GENERATED_SANDBOX_EXECUTION_FEEDBACK_TYPES
            or not str(candidate.get("feedback_id", "") or "").strip()
        ):
            continue
        snapshot_keys = (
            "feedback_id",
            "feedback_type",
            "algorithm_sandbox_manifest_id",
            "simulation_manifest_id",
            "failure_classification",
            "prototypes",
            "generated_simulation_prototypes",
            "boundary",
        )
        return {
            key: deepcopy(candidate[key])
            for key in snapshot_keys
            if key in candidate
        }
    return {}


def _generated_code_review_feedback_with_source_execution_snapshot(
    *,
    prior_feedback: Mapping[str, Any] | None,
    review_feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Make the current review authoritative without discarding prior observations."""

    prior = deepcopy(dict(prior_feedback)) if isinstance(prior_feedback, Mapping) else {}
    merged = deepcopy(dict(review_feedback))
    merged["observation_status"] = "CURRENT_ACTIVE_OBSERVATION"
    source_execution_feedback = _generated_sandbox_execution_feedback_snapshot(
        prior
    )
    if source_execution_feedback:
        merged["source_execution_feedback"] = source_execution_feedback
    if prior:
        prior_history = prior.pop("superseded_observations", [])
        prior.pop("observation_time_contract", None)
        prior["observation_status"] = (
            "SUPERSEDED_BY_SUBSEQUENT_CANDIDATE_REVIEW"
        )
        history = [
            deepcopy(dict(row))
            for row in prior_history
            if isinstance(row, Mapping)
        ]
        history.append(
            {
                "observation_status": "SUPERSEDED_BY_SUBSEQUENT_CANDIDATE_REVIEW",
                "superseded_feedback_id": str(prior.get("feedback_id", "") or ""),
                "superseded_feedback_type": str(
                    prior.get("feedback_type", "") or ""
                ),
                "superseded_failure_classification": str(
                    prior.get("failure_classification", "") or ""
                ),
                "observation": prior,
            }
        )
        merged["superseded_observations"] = history
    merged["observation_time_contract"] = {
        "top_level_observation_is_current": True,
        "superseded_observations_are_historical_only": True,
        "historical_error_is_not_an_active_blocker_unless_reobserved": True,
        "complete_history_preserved": True,
    }
    return merged


def _annotate_generated_sandbox_prototype_provenance(
    prototype: Mapping[str, Any],
    *,
    proposal_packet: Mapping[str, Any] | None,
    source_feedback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    annotated = dict(prototype)
    packet = proposal_packet if isinstance(proposal_packet, Mapping) else {}
    annotated["source_llm_proposal_id"] = str(packet.get("packet_id", "") or "")
    annotated["source_llm_proposal_agent"] = str(packet.get("source_agent", "") or "")
    annotated["source_llm_proposal_provider"] = (
        _runtime_llm_proposal_packet_provider(packet) if packet else ""
    )
    annotated["source_llm_proposal_backend_provider"] = (
        _runtime_llm_proposal_packet_backend_provider(packet) if packet else ""
    )
    annotated["source_llm_proposal_model"] = str(packet.get("model", "") or "")
    annotated["source_llm_proposal_model_tier"] = str(
        packet.get("model_tier", "") or ""
    )
    annotated["source_llm_proposal_live_generator"] = (
        _runtime_llm_proposal_packet_live_generator(packet) if packet else False
    )
    annotated["prototype_artifact_id"] = _generated_sandbox_prototype_artifact_id(
        annotated
    )
    feedback = source_feedback if isinstance(source_feedback, Mapping) else {}
    source_execution_feedback = _generated_sandbox_execution_feedback_snapshot(
        feedback
    )
    if source_execution_feedback:
        lineage_feedback: Mapping[str, Any] = source_execution_feedback
    else:
        lineage_feedback = feedback
    feedback_id = str(lineage_feedback.get("feedback_id", "") or "").strip()
    parent_manifest_id = str(
        lineage_feedback.get("algorithm_sandbox_manifest_id", "")
        or lineage_feedback.get("simulation_manifest_id", "")
        or ""
    ).strip()
    parent_rows = lineage_feedback.get("prototypes", [])
    if not isinstance(parent_rows, list) or not parent_rows:
        parent_rows = lineage_feedback.get(
            "generated_simulation_prototypes", []
        )
    if not isinstance(parent_rows, list):
        parent_rows = []
    parent_artifact_ids = [
        str(row.get("prototype_artifact_id", "") or "").strip()
        for row in parent_rows
        if isinstance(row, Mapping)
        and str(row.get("prototype_artifact_id", "") or "").strip()
    ]
    parent_script_hashes = [
        str(row.get("script_hash", "") or "").strip()
        for row in parent_rows
        if isinstance(row, Mapping)
        and str(row.get("script_hash", "") or "").strip()
    ]
    if feedback_id and parent_manifest_id and parent_artifact_ids:
        annotated["source_revision_lineage"] = {
            "schema_version": 1,
            "artifact_kind": "GeneratedSourceRevisionLineage",
            "feedback_id": feedback_id,
            "feedback_type": str(
                lineage_feedback.get("feedback_type", "") or ""
            ),
            "feedback_failure_classification": str(
                lineage_feedback.get("failure_classification", "") or ""
            ),
            "parent_manifest_id": parent_manifest_id,
            "parent_prototype_artifact_ids": list(dict.fromkeys(parent_artifact_ids)),
            "parent_script_hashes": list(dict.fromkeys(parent_script_hashes)),
            "child_prototype_artifact_id": annotated["prototype_artifact_id"],
            "child_script_hash": _generated_sandbox_prototype_script_hash(annotated),
            "child_proposal_id": annotated["source_llm_proposal_id"],
            "feedback_supplied_to_generator": True,
            "lineage_contract_complete": True,
            "semantic_review_execution_id": str(
                feedback.get("semantic_review_execution_id", "") or ""
            ),
            "semantic_review_packet_id": str(
                feedback.get("semantic_review_packet_id", "") or ""
            ),
            "semantic_review_packet_hash": str(
                feedback.get("semantic_review_packet_hash", "") or ""
            ),
            "semantic_review_feedback_supplied_to_generator": bool(
                str(feedback.get("semantic_review_execution_id", "") or "")
                and str(feedback.get("semantic_review_packet_id", "") or "")
            ),
            "boundary": (
                "This lineage records which failed generated artifact and runtime "
                "feedback were supplied to the next LLM proposal. It is execution "
                "provenance, not statistical or theorem proof evidence."
            ),
        }
    return annotated


def _generated_sandbox_prototype_script_hash(row: Mapping[str, Any]) -> str:
    script_hash = str(row.get("script_hash", "") or "").strip()
    if script_hash:
        return script_hash
    code_excerpt = str(row.get("code_excerpt", "") or "")
    return stable_hash(code_excerpt) if code_excerpt else ""


def _generated_sandbox_prototype_artifact_id(row: Mapping[str, Any]) -> str:
    scope_id = str(
        row.get("simulation_id", "")
        or row.get("estimator_id", "")
        or "generated_sandbox"
    )
    identity = {
        "executor": str(row.get("executor", "") or ""),
        "scope_id": scope_id,
        "script_hash": _generated_sandbox_prototype_script_hash(row),
        "source_llm_proposal_id": str(
            row.get("source_llm_proposal_id", "") or ""
        ),
    }
    if not identity["script_hash"]:
        identity["missing_code_identity"] = stable_hash(
            {
                "status": str(row.get("prototype_status", "") or ""),
                "reason": str(row.get("reason", "") or ""),
                "spec": row.get("spec", {}),
            }
        )
    return "generated_sandbox_prototype:" + stable_hash(identity)[:20]


def _generated_sandbox_feedback_id(
    *,
    feedback_type: str,
    source_manifest_id: str,
    failure_classification: str,
    prototype_rows: Sequence[Mapping[str, Any]],
) -> str:
    snapshot = [
        {
            "prototype_artifact_id": _generated_sandbox_prototype_artifact_id(row),
            "script_hash": _generated_sandbox_prototype_script_hash(row),
            "prototype_status": str(row.get("prototype_status", "") or ""),
            "smoke_passed": row.get("smoke_passed"),
            "metric_gate_errors": list(_str_tuple(row.get("metric_gate_errors", []))),
            "safety_errors": list(_str_tuple(row.get("safety_errors", []))),
            "returncode": row.get("returncode"),
            "stderr_summary_hash": stable_hash(
                str(row.get("stderr_summary", "") or "")
            ),
            "result_parse_error": str(row.get("result_parse_error", "") or ""),
        }
        for row in list(prototype_rows)[:5]
        if isinstance(row, Mapping)
    ]
    return "generated_sandbox_feedback:" + stable_hash(
        [
            feedback_type,
            source_manifest_id,
            failure_classification,
            snapshot,
        ]
    )[:20]


def _generated_sandbox_row_executed(row: Mapping[str, Any]) -> bool:
    return str(row.get("prototype_status", "") or "") in {
        "EXECUTED",
        "FAILED_METRIC_GATE",
    }


def _generated_sandbox_row_execution_attempted(row: Mapping[str, Any]) -> bool:
    return str(row.get("prototype_status", "") or "") in {
        "EXECUTED",
        "FAILED",
        "FAILED_METRIC_GATE",
    }


def _generated_sandbox_row_live_generated(row: Mapping[str, Any]) -> bool:
    provider = normalize_generator_provider_name(
        row.get("source_llm_proposal_provider", "")
    )
    backend_provider = normalize_generator_provider_name(
        row.get("source_llm_proposal_backend_provider", "") or ""
    )
    return (
        row.get("source_llm_proposal_live_generator") is True
        and is_live_generator_backend(provider, backend_provider)
    )


def _runtime_artifacts_with_generated_sandbox_live_provenance(
    artifacts: Mapping[str, Any],
) -> dict[str, Any]:
    proposal_packets = _runtime_llm_proposal_packets_by_id(artifacts)
    live_topology_by_subsystem = _runtime_live_generator_topology_by_subsystem(
        artifacts
    )
    enriched: dict[str, Any] = {}
    for artifact_id, artifact in artifacts.items():
        if not isinstance(artifact, Mapping):
            enriched[artifact_id] = artifact
            continue
        kind = str(artifact.get("artifact_kind", "") or "")
        if kind == "RuntimeAlgorithmSandboxManifest":
            enriched[artifact_id] = _generated_sandbox_manifest_with_live_provenance(
                artifact,
                proposal_packets=proposal_packets,
                live_topology_by_subsystem=live_topology_by_subsystem,
                subsystem="AlgorithmEngineer",
                proposal_id_keys=("llm_algorithm_engineer_proposal_id",),
                prototype_key="prototypes",
                generated_executor="generated_python_sandbox",
                missing_statuses={"MODEL_CODE_REQUIRED_BUT_MISSING"},
            )
        elif kind == "RuntimeSimulationManifest":
            enriched[artifact_id] = _generated_sandbox_manifest_with_live_provenance(
                artifact,
                proposal_packets=proposal_packets,
                live_topology_by_subsystem=live_topology_by_subsystem,
                subsystem="SimulationEngineer",
                proposal_id_keys=("llm_simulation_engineer_proposal_id",),
                prototype_key="generated_simulation_sandbox_prototypes",
                generated_executor="generated_simulation_sandbox",
                missing_statuses={"GENERATED_SIMULATION_CODE_REQUIRED_BUT_MISSING"},
            )
        else:
            enriched[artifact_id] = artifact
    return enriched


def _runtime_llm_proposal_packets_by_id(
    artifacts: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    proposal_kinds = {
        "ArchitectCoordinatorProposalPacket",
        "SimulationEngineerProposalPacket",
        "AlgorithmEngineerProposalPacket",
        "FormalizerProofEngineerProposalPacket",
        "CriticEvaluatorProposalPacket",
    }
    proposal_source_agents = {
        "LLMArchitectCoordinatorAgent",
        "LLMSimulationEngineerAgent",
        "LLMAlgorithmEngineerAgent",
        "LLMFormalizerProofEngineerAgent",
        "LLMCriticEvaluatorAgent",
    }
    packets: dict[str, Mapping[str, Any]] = {}
    for artifact_id, artifact in artifacts.items():
        if not isinstance(artifact, Mapping):
            continue
        kind = str(artifact.get("artifact_kind", "") or "")
        source_agent = str(artifact.get("source_agent", "") or "")
        if kind not in proposal_kinds and source_agent not in proposal_source_agents:
            continue
        packet_id = str(artifact.get("packet_id", "") or artifact_id or "").strip()
        if not packet_id:
            continue
        if not (
            source_agent or artifact.get("provider") or artifact.get("provider_name")
        ):
            continue
        packets[packet_id] = artifact
    return packets


def _runtime_live_generator_topology_by_subsystem(
    artifacts: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    rows: dict[str, Mapping[str, Any]] = {}
    for artifact in artifacts.values():
        if not isinstance(artifact, Mapping):
            continue
        if str(artifact.get("artifact_kind", "") or "") != (
            "RuntimeLLMTopologyManifest"
        ):
            continue
        agents = artifact.get("llm_agents", [])
        if not isinstance(agents, list):
            continue
        for row in agents:
            if not isinstance(row, Mapping):
                continue
            subsystem = str(row.get("subsystem", "") or "").strip()
            if subsystem and _runtime_llm_topology_row_is_live_generator(row):
                rows[subsystem] = row
    return rows


def _generated_sandbox_manifest_with_live_provenance(
    manifest: Mapping[str, Any],
    *,
    proposal_packets: Mapping[str, Mapping[str, Any]],
    live_topology_by_subsystem: Mapping[str, Mapping[str, Any]],
    subsystem: str,
    proposal_id_keys: tuple[str, ...],
    prototype_key: str,
    generated_executor: str,
    missing_statuses: set[str],
) -> Mapping[str, Any]:
    rows = manifest.get(prototype_key, [])
    if not isinstance(rows, list) or not rows:
        return manifest
    proposal_id = ""
    for key in proposal_id_keys:
        proposal_id = str(manifest.get(key, "") or "").strip()
        if proposal_id:
            break
    proposal_packet = proposal_packets.get(proposal_id, {})
    topology_row = live_topology_by_subsystem.get(subsystem, {})
    if not proposal_packet and not topology_row:
        return manifest
    enriched_rows: list[Any] = []
    changed = False
    for row in rows:
        if not isinstance(row, Mapping):
            enriched_rows.append(row)
            continue
        if not _generated_sandbox_row_needs_provenance(
            row,
            generated_executor=generated_executor,
            missing_statuses=missing_statuses,
        ):
            enriched_rows.append(row)
            continue
        enriched_row = _generated_sandbox_row_with_live_provenance(
            row,
            proposal_packet=proposal_packet,
            topology_row=topology_row,
        )
        changed = changed or enriched_row is not row
        enriched_rows.append(enriched_row)
    if not changed:
        return manifest
    enriched_manifest = dict(manifest)
    enriched_manifest[prototype_key] = enriched_rows
    return enriched_manifest


def _generated_sandbox_row_needs_provenance(
    row: Mapping[str, Any],
    *,
    generated_executor: str,
    missing_statuses: set[str],
) -> bool:
    return (
        str(row.get("executor", "") or "") == generated_executor
        or str(row.get("prototype_status", "") or "") in missing_statuses
    )


def _generated_sandbox_row_with_live_provenance(
    row: Mapping[str, Any],
    *,
    proposal_packet: Mapping[str, Any],
    topology_row: Mapping[str, Any],
) -> Mapping[str, Any]:
    if _generated_sandbox_row_live_generated(row):
        return row
    row_backend = normalize_generator_provider_name(
        row.get("source_llm_proposal_backend_provider", "")
    )
    if row_backend:
        return row
    provider = normalize_generator_provider_name(
        row.get("source_llm_proposal_provider", "")
    ) or _runtime_llm_proposal_packet_provider(proposal_packet)
    backend_provider = _runtime_llm_proposal_packet_backend_provider(proposal_packet)
    topology_provider = normalize_generator_provider_name(
        topology_row.get("provider_name", "")
    )
    topology_backend = normalize_generator_provider_name(
        topology_row.get("backend_provider_name", "")
    )
    if (
        provider
        and not backend_provider
        and topology_provider == provider
        and is_live_generator_backend(topology_provider, topology_backend)
    ):
        proposal_model = str(proposal_packet.get("model", "") or "").strip()
        topology_model = str(topology_row.get("model", "") or "").strip()
        if not proposal_model or not topology_model or proposal_model == topology_model:
            backend_provider = topology_backend
    if not is_live_generator_backend(provider, backend_provider):
        return row
    enriched = dict(row)
    enriched.setdefault(
        "source_llm_proposal_id", str(proposal_packet.get("packet_id", "") or "")
    )
    enriched.setdefault(
        "source_llm_proposal_agent", str(proposal_packet.get("source_agent", "") or "")
    )
    enriched["source_llm_proposal_provider"] = provider
    enriched["source_llm_proposal_backend_provider"] = backend_provider
    enriched.setdefault(
        "source_llm_proposal_model", str(proposal_packet.get("model", "") or "")
    )
    enriched.setdefault(
        "source_llm_proposal_model_tier",
        str(proposal_packet.get("model_tier", "") or ""),
    )
    enriched["source_llm_proposal_live_generator"] = True
    if not _runtime_llm_proposal_packet_backend_provider(proposal_packet):
        enriched["source_llm_proposal_backend_inferred_from_topology"] = True
    return enriched


def _generated_sandbox_metric_contract_counts_from_row(
    row: Mapping[str, Any],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    contracts = row.get("metric_contracts", [])
    if isinstance(contracts, list):
        counts["typed_metric_contracts_declared"] += sum(
            1 for contract in contracts if isinstance(contract, Mapping)
        )
        counts["typed_metric_contracts_authority_bound"] += sum(
            1
            for contract in contracts
            if isinstance(contract, Mapping)
            and str(
                contract.get("authority_requirement_fingerprint", "") or ""
            ).strip()
        )
    authority_required = bool(
        row.get("metric_requirement_authority_required", False)
    )
    authority_validated = bool(
        row.get("metric_requirement_authority_validated", False)
    )
    if authority_required:
        counts["typed_metric_contract_artifacts_authority_required"] += 1
    if authority_validated:
        counts["typed_metric_contract_artifacts_authority_validated"] += 1
    if str(row.get("prototype_status", "") or "") == (
        "METRIC_REQUIREMENT_AUTHORITY_REJECTED"
    ):
        counts["typed_metric_contract_artifacts_authority_rejected"] += 1
    evaluation = row.get("metric_contract_evaluation", {})
    if not isinstance(evaluation, Mapping):
        return counts
    n_contracts = _generated_metric_contract_evaluation_count(row, "n_contracts")
    if n_contracts <= 0:
        return counts
    counts["typed_metric_contract_artifacts_evaluated"] += 1
    counts["typed_metric_contracts_evaluated"] += n_contracts
    counts["typed_metric_contracts_passed"] += (
        _generated_metric_contract_evaluation_count(row, "n_passed")
    )
    counts["typed_metric_contracts_failed"] += (
        _generated_metric_contract_evaluation_count(row, "n_failed")
    )
    if evaluation.get("all_required_passed") is True:
        counts["typed_metric_contract_artifacts_all_required_passed"] += 1
        if authority_validated or evaluation.get(
            "metric_requirement_authority_validated"
        ) is True:
            counts[
                "typed_metric_contract_artifacts_authority_validated_all_required_passed"
            ] += 1
    else:
        counts["typed_metric_contract_artifacts_with_required_failure"] += 1
    return counts


def _llm_topology_policy_violations(agents: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    for row in agents:
        if not row.get("enabled"):
            continue
        unsupported = _unsupported_generator_providers(row)
        if unsupported:
            violations.append(
                f"{row.get('subsystem')} uses unsupported generator provider(s): "
                + ", ".join(sorted(unsupported))
            )
        mismatch = _anthropic_model_tier_mismatch(row)
        if mismatch:
            violations.append(mismatch)
        serious_mismatch = _anthropic_serious_model_tier_mismatch(row)
        if serious_mismatch:
            violations.append(serious_mismatch)
        subsystem_tier_mismatch = _subsystem_model_tier_mismatch(row)
        if subsystem_tier_mismatch:
            violations.append(subsystem_tier_mismatch)
        contextual_tier_mismatch = _contextual_model_tier_mismatch(row)
        if contextual_tier_mismatch:
            violations.append(contextual_tier_mismatch)
    return violations


def _has_unsupported_generator_provider(row: Mapping[str, Any]) -> bool:
    return bool(_unsupported_generator_providers(row))


def _unsupported_generator_providers(row: Mapping[str, Any]) -> set[str]:
    allowed = set(SUPPORTED_GENERATOR_PROVIDERS)
    providers = {
        str(row.get("provider_name", "") or "").strip().lower(),
        str(row.get("backend_provider_name", "") or "").strip().lower(),
    }
    providers.discard("")
    return {provider for provider in providers if provider not in allowed}


def _anthropic_model_tier_mismatch(row: Mapping[str, Any]) -> str:
    providers = {
        str(row.get("provider_name", "") or "").strip().lower(),
        str(row.get("backend_provider_name", "") or "").strip().lower(),
    }
    if "anthropic" not in providers:
        return ""
    return claude_model_tier_mismatch(
        str(row.get("model", "") or "").strip(),
        str(row.get("model_tier", "") or "").strip().lower(),
        subject=str(row.get("subsystem", "") or "").strip(),
    )


def _anthropic_serious_model_tier_mismatch(row: Mapping[str, Any]) -> str:
    if not str(row.get("serious_model_tier", "") or "").strip():
        return ""
    providers = {
        str(row.get("provider_name", "") or "").strip().lower(),
        str(row.get("backend_provider_name", "") or "").strip().lower(),
    }
    if "anthropic" not in providers:
        return ""
    return claude_model_tier_mismatch(
        str(row.get("serious_model", "") or "").strip(),
        str(row.get("serious_model_tier", "") or "").strip().lower(),
        subject=f"{str(row.get('subsystem', '') or '').strip()} serious workspace",
    )


def _subsystem_model_tier_mismatch(row: Mapping[str, Any]) -> str:
    expected = str(row.get("expected_model_tier", "") or "").strip().lower()
    configured = str(row.get("model_tier", "") or "").strip().lower()
    if not expected or expected == "auto":
        return ""
    if configured == expected:
        return ""
    return (
        f"{row.get('subsystem')} expected model_tier {expected} by "
        f"AI Statistician LLM subsystem policy but is configured with "
        f"{configured or 'missing'}"
    )


def _contextual_model_tier_mismatch(row: Mapping[str, Any]) -> str:
    expected = str(
        row.get("expected_serious_model_tier", "") or ""
    ).strip().lower()
    configured = str(row.get("serious_model_tier", "") or "").strip().lower()
    if not expected or configured == expected:
        return ""
    return (
        f"{row.get('subsystem')} serious workspace expected model_tier "
        f"{expected} by AI Statistician contextual LLM policy but is configured "
        f"with {configured or 'missing'}"
    )


def _llm_agent_topology_row(
    subsystem: str,
    agent: Any | None,
    *,
    role: str,
) -> dict[str, Any]:
    expected_model_tier = llm_subsystem_expected_model_tier(subsystem)
    if agent is None:
        return {
            "subsystem": subsystem,
            "enabled": False,
            "provider_name": "",
            "backend_provider_name": "",
            "model": "",
            "model_tier": expected_model_tier,
            "expected_model_tier": expected_model_tier,
            "role": role,
            "generator_only": True,
            "acts_in_environment": False,
        }
    config = getattr(agent, "config", None)
    provider = getattr(agent, "provider", None)
    provider_name = str(getattr(config, "provider_name", "") or getattr(provider, "provider_name", "") or "")
    config_model_tier = str(
        getattr(config, "model_tier", "") or expected_model_tier
    )
    requested_model = str(getattr(config, "model", "") or "")
    resolved_model = resolve_generator_model(
        provider_name=provider_name,
        requested_model=requested_model,
        model_tier=config_model_tier,
    )
    row = {
        "subsystem": subsystem,
        "enabled": True,
        "provider_name": provider_name,
        "backend_provider_name": str(getattr(provider, "provider_name", provider_name) or ""),
        "model": resolved_model,
        "configured_model": requested_model,
        "model_tier": config_model_tier,
        "expected_model_tier": expected_model_tier,
        "role": role,
        "generator_only": True,
        "acts_in_environment": False,
        "max_tokens": int(getattr(config, "max_tokens", 0) or 0),
        "temperature": float(getattr(config, "temperature", 0.0) or 0.0),
    }
    if subsystem == "TheoryDeveloper":
        serious_model_tier = str(
            getattr(config, "serious_model_tier", "")
            or AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY.get(
                "TheoryDeveloper:serious", ""
            )
        )
        row.update(
            {
                "serious_model": resolve_generator_model(
                    provider_name=provider_name,
                    requested_model=str(
                        getattr(config, "serious_model", "") or ""
                    ),
                    model_tier=serious_model_tier,
                ),
                "configured_serious_model": str(
                    getattr(config, "serious_model", "") or ""
                ),
                "serious_model_tier": serious_model_tier,
                "expected_serious_model_tier": (
                    AI_STATISTICIAN_LLM_CONTEXTUAL_MODEL_TIER_POLICY.get(
                        "TheoryDeveloper:serious", ""
                    )
                ),
                "serious_max_tokens": int(
                    getattr(config, "serious_max_tokens", 0) or 0
                ),
            }
        )
    return row


def _implementation_gaps(
    packet: Any,
    procedures: list[CandidateProcedure],
    *,
    require_generated_adapter: bool = False,
) -> list[dict[str, Any]]:
    if not isinstance(packet, Mapping):
        return []
    registered_ids = {row.id for row in procedures}
    registered_algorithms = {row.algorithm for row in procedures}
    gaps: list[dict[str, Any]] = []
    for row in packet.get("estimator_specs", []) or []:
        if not isinstance(row, Mapping):
            continue
        estimator_id = str(row.get("id") or row.get("name") or "").strip()
        if not estimator_id:
            continue
        if (
            not require_generated_adapter
            and (
                estimator_id in registered_ids
                or estimator_id in registered_algorithms
            )
        ):
            continue
        gaps.append(
            {
                "estimator_id": estimator_id,
                "status": (
                    "REQUIRES_GENERATED_ALGORITHM_ENGINEER_ADAPTER"
                    if require_generated_adapter
                    else "REQUIRES_ALGORITHM_ENGINEER_ADAPTER"
                ),
                "reason": (
                    "Agentic execution requires this LLM estimator spec to pass "
                    "through generated code, sandbox execution, and independent "
                    "semantic review. DGP-based statistical-performance gates belong "
                    "to the downstream SimulationEngineer experiment. A registered "
                    "template cannot satisfy this generated-artifact evidence gate."
                    if require_generated_adapter
                    else "LLM estimator spec has no registered executable algorithm "
                    "in this runtime slice."
                ),
            }
        )
    return gaps


def _critic_revision_round(context: Mapping[str, Any]) -> int:
    loop = context.get("runtime_feedback_loop")
    if not isinstance(loop, Mapping):
        return 0
    try:
        return max(0, int(loop.get("critic_revision_round", 0) or 0))
    except (TypeError, ValueError):
        return 0


def _unique_runtime_artifact_id(
    blackboard: BlackboardState,
    artifact_id: str,
    *,
    task_id: str,
) -> str:
    if artifact_id not in blackboard.artifacts:
        return artifact_id
    return f"{artifact_id}:runtime_revision:{stable_hash(task_id)[:8]}"


def _effective_critic_revision_rounds(
    context: Mapping[str, Any],
    config: ResearchAgentRuntimeConfig,
) -> int:
    configured = max(0, int(config.max_critic_revision_rounds))
    policy = _architect_runtime_plan(context).get("iteration_policy", {})
    if not isinstance(policy, Mapping):
        return configured
    try:
        architect_max = int(policy.get("max_revision_rounds", configured) or configured)
    except (TypeError, ValueError):
        return configured
    return max(0, min(configured, architect_max))




def _critic_evidence_contract_decision(
    *,
    critic_control: Mapping[str, Any],
    formalization_manifest: Mapping[str, Any],
    revision_required: bool,
) -> dict[str, Any]:
    """Classify terminal critic status under the Architect evidence contract."""

    contract = (
        critic_control.get("evidence_contract", {})
        if isinstance(critic_control, Mapping)
        else {}
    )
    if not isinstance(contract, Mapping):
        contract = {}
    policy = (
        str(contract.get("formal_verification_policy", "") or "optional")
        .strip()
        .lower()
    )
    if policy not in {"required", "optional", "advisory"}:
        policy = "optional"
    counts = (
        formalization_manifest.get("counts", {})
        if isinstance(formalization_manifest, Mapping)
        and isinstance(formalization_manifest.get("counts", {}), Mapping)
        else {}
    )
    formal_gaps = _int_like(counts.get("formal_gap", 0))
    kernel_verified = _int_like(counts.get("kernel_verified", 0))
    full_theorem_proved = _bool_like(
        formalization_manifest.get("full_frontier_theorem_proved", False)
        if isinstance(formalization_manifest, Mapping)
        else False
    )
    formal_satisfied = bool(
        formal_gaps <= 0 and (full_theorem_proved or kernel_verified > 0)
    )
    if revision_required:
        final_status = "REROUTE_REQUIRED_BEFORE_FINAL"
        runtime_status = "REVISE"
        failure_classification = ""
    elif policy == "required" and not formal_satisfied:
        final_status = "FORMAL_REQUIRED_BLOCKED"
        runtime_status = "BLOCKED"
        failure_classification = "formal_required_unverified"
    elif policy == "advisory":
        final_status = "RESEARCH_CANDIDATE_ACCEPTED_FORMAL_ADVISORY"
        runtime_status = "ACCEPTED"
        failure_classification = ""
    elif policy == "optional" and not formal_satisfied:
        final_status = "RESEARCH_CANDIDATE_ACCEPTED_WITH_FORMAL_GAPS"
        runtime_status = "ACCEPTED"
        failure_classification = ""
    else:
        final_status = "FORMAL_CONTRACT_SATISFIED"
        runtime_status = "ACCEPTED"
        failure_classification = ""
    return {
        "formal_verification_policy": policy,
        "recommended_research_path": str(
            contract.get("recommended_research_path", "") or ""
        ),
        "formal_required_for_final": _bool_like(
            contract.get("formal_required_for_final", policy == "required")
        ),
        "simulation_required_for_final": _bool_like(
            contract.get("simulation_required_for_final", False)
        ),
        "must_disclose_formal_gaps": _bool_like(
            contract.get("must_disclose_formal_gaps", True)
        ),
        "formal_gaps": formal_gaps,
        "kernel_verified": kernel_verified,
        "full_frontier_theorem_proved": full_theorem_proved,
        "formal_satisfied": formal_satisfied,
        "runtime_status": runtime_status,
        "final_acceptance_status": final_status,
        "failure_classification": failure_classification,
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }


































def _architect_runtime_plan(context: Mapping[str, Any]) -> dict[str, Any]:
    plan = context.get("architect_runtime_plan")
    if isinstance(plan, Mapping):
        return dict(plan)
    contract = context.get("runtime_requested_evidence_contract")
    if isinstance(contract, Mapping) and contract:
        return {
            "subsystem_execution_plan": [],
            "evidence_contract": dict(contract),
            "evidence_gates": [
                {
                    "artifact_kind": "runtime requested evidence contract",
                    "required_evidence": (
                        "follow formal_verification_policy and "
                        "recommended_research_path until an Architect packet "
                        "overrides them"
                    ),
                    "not_evidence": (
                        "requested policy/path is orchestration control, not "
                        "proof, simulation, or implementation evidence"
                    ),
                }
            ],
            "boundary": (
                "Runtime requested evidence contract is orchestration control "
                "metadata. It does not prove or validate any statistical claim "
                "and must not replace live Architect reasoning in capability "
                "evaluations."
            ),
        }
    return {}


def _architect_subsystem_plan(context: Mapping[str, Any], subsystem: str) -> dict[str, Any]:
    plan = _architect_runtime_plan(context)
    for row in plan.get("subsystem_execution_plan", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("subsystem", "")).strip() == subsystem:
            return dict(row)
    return {}


def _architect_acceptance_gate(
    context: Mapping[str, Any],
    subsystem: str,
    default: str,
) -> str:
    row = _architect_subsystem_plan(context, subsystem)
    gate = str(row.get("acceptance_gate", "")).strip()
    return gate or default


def _architect_expected_artifacts(
    context: Mapping[str, Any],
    subsystem: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    row = _architect_subsystem_plan(context, subsystem)
    artifacts = [
        str(item).strip()
        for item in row.get("expected_artifacts", []) or []
        if str(item).strip()
    ]
    return tuple(artifacts) if artifacts else default


def _architect_control_payload(context: Mapping[str, Any], subsystem: str) -> dict[str, Any]:
    plan = _architect_runtime_plan(context)
    row = deepcopy(_architect_subsystem_plan(context, subsystem))
    if not plan and not row:
        return {}
    iteration_policy = plan.get("iteration_policy", {})
    retrieval_strategy = plan.get("retrieval_strategy", {})
    problem_analysis = plan.get("problem_analysis", {})
    evidence_contract = plan.get("evidence_contract", {})
    if not isinstance(evidence_contract, Mapping):
        evidence_contract = {}
    return {
        "architect_coordinator_proposal_id": str(
            context.get("architect_coordinator_proposal_id", "")
        ),
        "subsystem": subsystem,
        "subsystem_plan": deepcopy(row),
        "acceptance_gate": str(row.get("acceptance_gate", "")).strip(),
        "expected_artifacts": [
            str(item).strip()
            for item in row.get("expected_artifacts", []) or []
            if str(item).strip()
        ],
        "iteration_policy": deepcopy(dict(iteration_policy)) if isinstance(iteration_policy, Mapping) else {},
        "retrieval_strategy": deepcopy(dict(retrieval_strategy)) if isinstance(retrieval_strategy, Mapping) else {},
        "problem_analysis": deepcopy(dict(problem_analysis)) if isinstance(problem_analysis, Mapping) else {},
        "evidence_contract": deepcopy(dict(evidence_contract)),
        "formal_verification_policy": str(
            evidence_contract.get("formal_verification_policy", "") or ""
        ),
        "recommended_research_path": str(
            evidence_contract.get("recommended_research_path", "") or ""
        ),
        "formal_required_for_final": _bool_like(
            evidence_contract.get("formal_required_for_final", False)
        ),
        "boundary": str(plan.get("boundary", "")),
    }


def _runtime_environment_feedback_with_architect_directive(
    *,
    context: Mapping[str, Any],
    subsystem: str,
    feedback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(feedback) if isinstance(feedback, Mapping) else {}
    empirical_evaluation_phase = str(
        context.get("empirical_evaluation_phase", "") or ""
    ).strip()
    if empirical_evaluation_phase:
        payload.setdefault(
            "empirical_evaluation_phase",
            empirical_evaluation_phase,
        )
    runtime_task = context.get("runtime_task", {})
    if isinstance(runtime_task, Mapping) and runtime_task:
        payload.setdefault("runtime_task", dict(runtime_task))
    requested_contract = context.get("runtime_requested_evidence_contract", {})
    if isinstance(requested_contract, Mapping) and requested_contract:
        payload.setdefault("runtime_requested_evidence_contract", dict(requested_contract))
    architect_contract = context.get("architect_evidence_contract", {})
    if isinstance(architect_contract, Mapping) and architect_contract:
        payload.setdefault("architect_evidence_contract", dict(architect_contract))
    control = _architect_control_payload(context, subsystem)
    if not control:
        return payload
    evidence_contract = control.get("evidence_contract", {})
    if isinstance(evidence_contract, Mapping) and evidence_contract:
        payload.setdefault("architect_evidence_contract", dict(evidence_contract))
    for key in (
        "formal_verification_policy",
        "recommended_research_path",
        "formal_required_for_final",
    ):
        if control.get(key) not in (None, "", [], {}):
            payload.setdefault(f"architect_{key}", control.get(key))
    if control.get("acceptance_gate"):
        payload.setdefault(
            "architect_subsystem_acceptance_gate",
            str(control.get("acceptance_gate", "")),
        )
    return payload
















def _runtime_context_contract_flag(
    context: Mapping[str, Any],
    *,
    subsystem: str,
    flag: str,
) -> bool:
    requested_contract = context.get("runtime_requested_evidence_contract", {})
    if isinstance(requested_contract, Mapping) and requested_contract.get(flag) is True:
        return True
    control = _architect_control_payload(context, subsystem)
    evidence_contract = control.get("evidence_contract", {})
    return bool(
        isinstance(evidence_contract, Mapping)
        and evidence_contract.get(flag) is True
    )


def _runtime_environment_feedback_contract_flag(
    feedback: Mapping[str, Any] | None,
    *,
    flag: str,
) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    sources: list[Mapping[str, Any]] = [feedback]
    input_summary = feedback.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        sources.append(input_summary)
    architect_context = feedback.get("architect_context", {})
    if isinstance(architect_context, Mapping):
        sources.append(architect_context)
    for source in sources:
        for contract_key in (
            "runtime_requested_evidence_contract",
            "architect_evidence_contract",
        ):
            contract = source.get(contract_key, {})
            if isinstance(contract, Mapping) and contract.get(flag) is True:
                return True
    return False


def _runtime_context_with_environment_feedback_contract(
    context: Mapping[str, Any],
    feedback: Mapping[str, Any] | None,
    *,
    subsystem: str,
) -> dict[str, Any]:
    merged = dict(context) if isinstance(context, Mapping) else {}
    if not isinstance(feedback, Mapping):
        return merged
    requested_contract = (
        dict(merged.get("runtime_requested_evidence_contract", {}))
        if isinstance(merged.get("runtime_requested_evidence_contract", {}), Mapping)
        else {}
    )
    feedback_sources: list[Mapping[str, Any]] = [feedback]
    input_summary = feedback.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        feedback_sources.append(input_summary)
    for source in feedback_sources:
        for contract_key in (
            "runtime_requested_evidence_contract",
            "architect_evidence_contract",
        ):
            contract = source.get(contract_key, {})
            if not isinstance(contract, Mapping):
                continue
            for key, value in contract.items():
                if str(key).startswith(
                    ("research_evaluation_requires_", "formal_evaluation_requires_")
                ) and value is True:
                    requested_contract[str(key)] = True
    if requested_contract:
        merged["runtime_requested_evidence_contract"] = requested_contract
    if str(merged.get("runtime_evaluation_mode", "") or "") == "":
        if any(
            str(key).startswith("formal_evaluation_requires_") and value is True
            for key, value in requested_contract.items()
        ):
            merged["runtime_evaluation_mode"] = "capability_eval"
        elif any(
            str(key).startswith("research_evaluation_requires_") and value is True
            for key, value in requested_contract.items()
        ):
            merged["runtime_evaluation_mode"] = "research_eval"
    if subsystem and requested_contract:
        control = _architect_control_payload(merged, subsystem)
        evidence_contract = (
            dict(control.get("evidence_contract", {}))
            if isinstance(control.get("evidence_contract", {}), Mapping)
            else {}
        )
        for key, value in requested_contract.items():
            if str(key).startswith(
                ("research_evaluation_requires_", "formal_evaluation_requires_")
            ) and value is True:
                evidence_contract.setdefault(str(key), True)
        if evidence_contract:
            control = dict(control)
            control["evidence_contract"] = evidence_contract
            controls = dict(merged.get("architect_control", {})) if isinstance(merged.get("architect_control", {}), Mapping) else {}
            controls[subsystem] = control
            merged["architect_control"] = controls
    return merged


def _runtime_requires_generated_algorithm_code(
    context: Mapping[str, Any],
    environment_feedback: Mapping[str, Any] | None = None,
) -> bool:
    return _runtime_context_contract_flag(
        context,
        subsystem="AlgorithmEngineer",
        flag="research_evaluation_requires_generated_algorithm_code",
    ) or _runtime_environment_feedback_contract_flag(
        environment_feedback,
        flag="research_evaluation_requires_generated_algorithm_code",
    )


def _runtime_requires_typed_metric_contracts(
    context: Mapping[str, Any],
    environment_feedback: Mapping[str, Any] | None = None,
    *,
    subsystem: str,
) -> bool:
    if subsystem == "AlgorithmEngineer":
        return False
    return _runtime_context_contract_flag(
        context,
        subsystem=subsystem,
        flag="research_evaluation_requires_typed_metric_contracts",
    ) or _runtime_environment_feedback_contract_flag(
        environment_feedback,
        flag="research_evaluation_requires_typed_metric_contracts",
    )


def _runtime_generated_metric_requirement_authority(
    context: Mapping[str, Any],
    environment_feedback: Mapping[str, Any] | None,
    *,
    architect_subsystem: str,
    target_subsystem: str,
) -> tuple[list[dict[str, Any]], str, bool]:
    authority_context = _runtime_environment_feedback_with_architect_directive(
        context=context,
        subsystem=architect_subsystem,
        feedback=environment_feedback,
    )
    requirements = generated_metric_requirements_from_context(
        authority_context,
        target_subsystem=target_subsystem,
    )
    policy = generated_metric_requirement_authority_policy_from_context(
        authority_context
    )
    if target_subsystem == "AlgorithmEngineer":
        return (
            [],
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
            False,
        )
    return (
        requirements,
        policy,
        policy == GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED,
    )


def _runtime_bind_and_validate_generated_metric_authority(
    contracts: Sequence[Mapping[str, Any]],
    *,
    artifact_id: str,
    authoritative_requirements: Sequence[Mapping[str, Any]],
    target_subsystem: str,
    require_authoritative_requirements: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not authoritative_requirements and not require_authoritative_requirements:
        return [dict(contract) for contract in contracts], []
    bound = bind_generated_metric_contract_authority(
        contracts,
        authoritative_requirements=authoritative_requirements,
        target_subsystem=target_subsystem,
    )
    errors = validate_generated_metric_contracts(
        bound,
        expected_artifact_ids=(artifact_id,),
        required_artifact_ids=(artifact_id,),
        authoritative_requirements=list(authoritative_requirements),
        target_subsystem=target_subsystem,
        require_authoritative_requirements=require_authoritative_requirements,
    )
    return bound, errors














def _runtime_requires_generated_simulation_code(
    context: Mapping[str, Any],
    environment_feedback: Mapping[str, Any] | None = None,
) -> bool:
    return _runtime_context_contract_flag(
        context,
        subsystem="SimulationEvaluator",
        flag="research_evaluation_requires_generated_simulation_code",
    ) or _runtime_environment_feedback_contract_flag(
        environment_feedback,
        flag="research_evaluation_requires_generated_simulation_code",
    )




def _implementation_gap_estimator_ids(
    implementation_gaps: Iterable[Mapping[str, Any]],
) -> set[str]:
    ids: set[str] = set()
    for row in implementation_gaps:
        if not isinstance(row, Mapping):
            continue
        estimator_id = str(row.get("estimator_id", "") or "").strip()
        if estimator_id:
            ids.add(estimator_id)
    return ids


def _runtime_generated_algorithm_sandbox_passed_manifest_id(
    blackboard: BlackboardState,
    *,
    question_id: str = "",
    theory_packet_id: str = "",
    required_estimator_ids: Iterable[str] = (),
) -> str:
    required_ids = {
        str(row).strip()
        for row in required_estimator_ids
        if str(row).strip()
    }
    for artifact in blackboard.artifacts.values():
        if not isinstance(artifact, Mapping):
            continue
        if artifact.get("artifact_kind") != "RuntimeAlgorithmSandboxManifest":
            continue
        if question_id:
            artifact_question = artifact.get("question", {})
            artifact_question_id = (
                str(artifact_question.get("id", "") or "")
                if isinstance(artifact_question, Mapping)
                else ""
            )
            if artifact_question_id and artifact_question_id != question_id:
                continue
        artifact_packet_id = str(artifact.get("theory_packet_id", "") or "")
        if theory_packet_id and artifact_packet_id != theory_packet_id:
            continue
        passed_ids: set[str] = set()
        for row in artifact.get("prototypes", []) or []:
            if not isinstance(row, Mapping):
                continue
            if (
                str(row.get("executor", "") or "") == "generated_python_sandbox"
                and row.get("prototype_status") == "EXECUTED"
                and row.get("smoke_passed") is True
            ):
                estimator_id = str(row.get("estimator_id", "") or "").strip()
                if estimator_id:
                    passed_ids.add(estimator_id)
        if required_ids and not required_ids.issubset(passed_ids):
            continue
        if passed_ids or int(artifact.get("n_passed", 0) or 0) > 0:
            return str(artifact.get("manifest_id", "") or "")
    return ""


def _latest_artifact(blackboard: BlackboardState, prefix: str) -> dict[str, Any]:
    for key in reversed(list(blackboard.artifacts.keys())):
        if key.startswith(prefix) and isinstance(blackboard.artifacts[key], dict):
            return dict(blackboard.artifacts[key])
    return {}


def _artifact_by_id_or_latest(
    blackboard: BlackboardState,
    artifact_id: str,
    prefix: str,
) -> dict[str, Any]:
    if artifact_id:
        artifact = blackboard.artifacts.get(artifact_id, {})
        return dict(artifact) if isinstance(artifact, Mapping) else {}
    return _latest_artifact(blackboard, prefix)


def _algorithm_proposal_for_estimator(
    proposal_packet: Mapping[str, Any] | None,
    estimator_id: str,
) -> dict[str, Any]:
    if not isinstance(proposal_packet, Mapping):
        return {}
    for row in proposal_packet.get("implementation_targets", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("estimator_id", "")) == estimator_id:
            return dict(row)
    return {}


def _algorithm_code_draft_for_estimator(
    proposal_packet: Mapping[str, Any] | None,
    estimator_id: str,
) -> dict[str, Any]:
    if not isinstance(proposal_packet, Mapping):
        return {}
    for row in proposal_packet.get("sandbox_code_drafts", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("estimator_id", "")) == estimator_id:
            return dict(row)
    return {}






_SOURCE_THEOREM_TARGET_PROVENANCE_STRING_KEYS = (
    "source_formalization_manifest_id",
    "source_formalizer_packet_id",
    "source_formal_target_id",
    "source_runtime_learning_task",
    "question_id",
    "source_theorem_target_resolution_id",
    "source_theorem_promotion_id",
    "source_theorem_route_id",
    "source_theorem_queue_item_id",
    "source_theorem_replay_id",
    "source_theorem_task_id",
    "source_theorem_question_id",
    "source_theorem_goal_id",
    "source_theorem_statement",
    "source_theorem_skeleton",
    "source_theorem_lean_file",
    "target_lean_declaration",
    "artifact_verification_id",
    "artifact_verifier_manifest",
    "materialization_id",
    "execution_queue_id",
)




def _source_theorem_target_provenance_from_row(row: Mapping[str, Any]) -> dict[str, Any]:
    sources: list[Mapping[str, Any]] = [row]
    for nested_key in (
        "source_theorem_target_provenance",
        "source_theorem_target_context",
        "kernel_overlay_context",
        "overlay_row",
    ):
        nested = row.get(nested_key, {})
        if isinstance(nested, Mapping):
            sources.append(nested)
    provenance: dict[str, Any] = {}
    if any("source_theorem_target_known" in source for source in sources):
        known_values = tuple(
            value
            for value in (
                _source_theorem_target_known_value(source)
                for source in sources
                if "source_theorem_target_known" in source
            )
            if value is not None
        )
        if known_values:
            provenance["source_theorem_target_known"] = any(known_values)
    constraints: list[str] = []
    for source in sources:
        for key in _SOURCE_THEOREM_TARGET_PROVENANCE_STRING_KEYS:
            if key in provenance:
                continue
            value = str(source.get(key, "") or "").strip()
            if value:
                provenance[key] = value
        constraints.extend(
            str(value).strip()
            for value in source.get("semantic_alignment_constraints", []) or []
            if str(value).strip()
        )
    if constraints:
        provenance["semantic_alignment_constraints"] = list(dict.fromkeys(constraints))
    return provenance






def _source_theorem_target_ids_from_row(
    row: Mapping[str, Any],
    *,
    fallback_target_theorem_name: str = "",
    fallback_source_formal_target_id: str = "",
) -> list[str]:
    sources: list[Mapping[str, Any]] = [row]
    for nested_key in (
        "source_theorem_target_provenance",
        "source_theorem_target_context",
        "kernel_overlay_context",
        "overlay_row",
        "input_summary",
    ):
        nested = row.get(nested_key, {})
        if isinstance(nested, Mapping):
            sources.append(nested)
    for source in tuple(sources):
        nested = source.get("source_theorem_target_provenance", {})
        if isinstance(nested, Mapping):
            sources.append(nested)

    target_ids: list[str] = source_theorem_explicit_target_ids(row)
    if not target_ids:
        for source in sources:
            for value in _str_tuple(source.get("target_theorem_goal_ids", [])):
                text = str(value or "").strip()
                if text:
                    target_ids.append(text)

    if not target_ids:
        for fallback in (
            fallback_target_theorem_name,
            fallback_source_formal_target_id,
        ):
            text = str(fallback or "").strip()
            if text:
                target_ids.append(text)
                break
    return list(dict.fromkeys(target_ids))


def _int_like(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)






















def _runtime_context_requires_formalizer_contract_flag(
    context: Mapping[str, Any],
    flag: str,
) -> bool:
    if not isinstance(context, Mapping):
        return False
    if _runtime_context_contract_flag(
        context,
        subsystem="FormalizationEvaluator",
        flag=flag,
    ) or _runtime_context_contract_flag(
        context,
        subsystem="FormalizationEvaluator",
        flag=flag,
    ):
        return True
    environment_feedback = context.get("environment_feedback", {})
    if _runtime_environment_feedback_contract_flag(environment_feedback, flag=flag):
        return True
    candidate_contracts: list[Any] = [
        context.get("runtime_requested_evidence_contract", {}),
        context.get("architect_evidence_contract", {}),
    ]
    plan = context.get("architect_runtime_plan", {})
    if isinstance(plan, Mapping):
        candidate_contracts.append(plan.get("evidence_contract", {}))
    for contract in candidate_contracts:
        if isinstance(contract, Mapping) and contract.get(flag) is True:
            return True
    return False


def _runtime_context_requires_formalizer_lean_candidate(
    context: Mapping[str, Any],
) -> bool:
    """Return whether the current runtime contract requires live Formalizer output."""

    return _runtime_context_requires_formalizer_contract_flag(
        context,
        "formal_evaluation_requires_formalizer_lean_candidate",
    )


def _runtime_context_requires_formalizer_live_prover_tool_call(
    context: Mapping[str, Any],
) -> bool:
    return _runtime_context_requires_formalizer_contract_flag(
        context,
        "formal_evaluation_requires_formalizer_live_prover_tool_call",
    )




def _theorem_goal_id(row: Any) -> str:
    if isinstance(row, Mapping):
        return str(row.get("id", "") or "").strip()
    return str(getattr(row, "id", "") or "").strip()


def _runtime_input_context_summary(
    architect_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Record only immutable run contracts, never historical routing policy."""

    requested_contract = (
        architect_context.get("runtime_requested_evidence_contract", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if not isinstance(requested_contract, Mapping):
        requested_contract = {}
    protocol = (
        architect_context.get("cross_family_evaluation_protocol", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    protocol_supplied = bool(
        isinstance(protocol, Mapping)
        and protocol.get("artifact_kind")
        == "CrossFamilyEndToEndEvaluationPanelSelection"
    )
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeInputContextSummary",
        "runtime_cross_family_evaluation_protocol_supplied": protocol_supplied,
        "runtime_cross_family_evaluation_protocol": (
            dict(protocol) if protocol_supplied else {}
        ),
        "runtime_requested_evidence_contract": dict(requested_contract),
        "historical_routing_policy_applied": False,
        "boundary": (
            "Runtime input context contains immutable evaluation and evidence "
            "contracts only. It is not source, execution, or proof evidence."
        ),
    }


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        return tuple(str(key) for key in value.keys() if str(key))
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else ()


def _runtime_completion_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    counts = {
        "accepted": 0,
        "failed": 0,
        "blocked": 0,
        "formal_required_blocked": 0,
        "max_iterations_reached": 0,
        "budget_exhausted_with_pending_next_task": 0,
        "budget_exhausted_after_revision_request": 0,
    }
    final_acceptance_status_counts: dict[str, int] = {}
    for result in results:
        traces = result.get("traces", []) if isinstance(result.get("traces"), list) else []
        final_trace = traces[-1] if traces and isinstance(traces[-1], Mapping) else {}
        first_trace = traces[0] if traces and isinstance(traces[0], Mapping) else {}
        first_task = first_trace.get("task", {}) if isinstance(first_trace.get("task"), Mapping) else {}
        first_inputs = first_task.get("inputs", {}) if isinstance(first_task.get("inputs"), Mapping) else {}
        question = first_inputs.get("question", {}) if isinstance(first_inputs.get("question"), Mapping) else {}
        first_architect_context = (
            first_inputs.get("architect_context", {})
            if isinstance(first_inputs.get("architect_context", {}), Mapping)
            else {}
        )
        requested_evidence_contract = (
            first_architect_context.get("runtime_requested_evidence_contract", {})
            if isinstance(
                first_architect_context.get(
                    "runtime_requested_evidence_contract",
                    {},
                ),
                Mapping,
            )
            else {}
        )
        artifacts = (
            result.get("blackboard", {}).get("artifacts", {})
            if isinstance(result.get("blackboard", {}), Mapping)
            and isinstance(result.get("blackboard", {}).get("artifacts", {}), Mapping)
            else {}
        )
        critic_decision: dict[str, Any] = {}
        for key in reversed(list(artifacts.keys())):
            artifact = artifacts.get(key, {})
            if not (
                str(key).startswith("critic_evaluator_manifest:")
                and isinstance(artifact, Mapping)
            ):
                continue
            decision = artifact.get("evidence_contract_decision", {})
            if isinstance(decision, Mapping):
                critic_decision = dict(decision)
            break
        final_acceptance_status = str(
            critic_decision.get("final_acceptance_status", "") or ""
        )
        if final_acceptance_status:
            final_acceptance_status_counts[final_acceptance_status] = (
                final_acceptance_status_counts.get(final_acceptance_status, 0) + 1
            )
        status = str(result.get("status", "") or "")
        pending_task_payload = (
            result.get("pending_task", {})
            if isinstance(result.get("pending_task"), Mapping)
            else {}
        )
        if not pending_task_payload and status == "MAX_ITERATIONS_REACHED":
            pending_task_payload = (
                final_trace.get("next_task", {})
                if isinstance(final_trace.get("next_task"), Mapping)
                else {}
            )
        pending_next_task = (
            _runtime_task_payload_reference(pending_task_payload)
            if pending_task_payload
            else {}
        )
        pending_next_task_id = str(
            pending_next_task.get("task_id", "") or ""
        )
        pending_task_continuation_ref = (
            dict(result.get("pending_task_continuation_ref", {}))
            if isinstance(
                result.get("pending_task_continuation_ref", {}),
                Mapping,
            )
            else {}
        )
        pending_task_checkpoint_reason = str(
            result.get("pending_task_checkpoint_reason", "") or ""
        )
        failure_classification = str(final_trace.get("failure_classification", "") or "")
        final_task_payload = (
            final_trace.get("task", {})
            if isinstance(final_trace.get("task"), Mapping)
            else {}
        )
        last_task_id = str(final_task_payload.get("task_id", "") or "")
        max_iterations_reached = status == "MAX_ITERATIONS_REACHED"
        budget_exhausted_with_pending = bool(max_iterations_reached and pending_next_task_id)
        budget_exhausted_after_revision = bool(
            budget_exhausted_with_pending
            and (
                "critic" in pending_next_task_id
                or "revise" in pending_next_task_id
                or "revision" in failure_classification
                or last_task_id.startswith("theory-critic-revise:")
            )
        )
        formal_required_policy_block = bool(
            status == "BLOCKED"
            and final_acceptance_status == "FORMAL_REQUIRED_BLOCKED"
        )
        if status == "ACCEPTED":
            terminal_kind = "accepted"
            counts["accepted"] += 1
        elif status == "FAILED":
            terminal_kind = "failed"
            counts["failed"] += 1
        elif formal_required_policy_block:
            terminal_kind = "formal_required_blocked"
            counts["blocked"] += 1
            counts["formal_required_blocked"] += 1
        elif status == "BLOCKED":
            terminal_kind = "blocked"
            counts["blocked"] += 1
        elif max_iterations_reached and pending_next_task_id:
            terminal_kind = "budget_exhausted_with_pending_next_task"
            counts["max_iterations_reached"] += 1
            counts["budget_exhausted_with_pending_next_task"] += 1
        elif max_iterations_reached:
            terminal_kind = "budget_exhausted_without_pending_next_task"
            counts["max_iterations_reached"] += 1
        else:
            terminal_kind = status.lower() or "unknown"
        if budget_exhausted_after_revision:
            counts["budget_exhausted_after_revision_request"] += 1
        rows.append(
            {
                "question_id": str(question.get("id", "") or ""),
                "question_title": str(question.get("title", "") or ""),
                "status": status,
                "terminal_kind": terminal_kind,
                "n_iterations": len(traces),
                "final_task_id": str(result.get("final_task_id", "") or ""),
                "last_completed_task_id": last_task_id,
                "last_completed_subsystem": str(final_trace.get("subsystem", "") or ""),
                "last_completed_status": str(final_trace.get("status", "") or ""),
                "last_failure_classification": failure_classification,
                "final_acceptance_status": final_acceptance_status,
                "formal_verification_policy": str(
                    critic_decision.get("formal_verification_policy", "")
                    or requested_evidence_contract.get(
                        "formal_verification_policy",
                        "",
                    )
                    or ""
                ),
                "recommended_research_path": str(
                    critic_decision.get("recommended_research_path", "")
                    or requested_evidence_contract.get(
                        "recommended_research_path",
                        "",
                    )
                    or ""
                ),
                "formal_satisfied": bool(critic_decision.get("formal_satisfied", False)),
                "full_frontier_theorem_proved": bool(
                    critic_decision.get("full_frontier_theorem_proved", False)
                ),
                "formal_gaps": _int_like(critic_decision.get("formal_gaps", 0)),
                "pending_next_task_id": pending_next_task_id,
                "pending_next_task": pending_next_task,
                "pending_task_continuation_ref": (
                    pending_task_continuation_ref
                ),
                "pending_task_checkpoint_reason": (
                    pending_task_checkpoint_reason
                ),
                "max_iterations_reached": max_iterations_reached,
                "budget_exhausted_with_pending_next_task": budget_exhausted_with_pending,
                "budget_exhausted_after_revision_request": budget_exhausted_after_revision,
            }
        )
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeCompletionSummary",
        "n_questions": len(results),
        **counts,
        "final_acceptance_status_counts": dict(
            sorted(final_acceptance_status_counts.items())
        ),
        "rows": rows,
        "payload_policy": "content_addressed_task_continuations",
        "boundary": (
            "Runtime completion status describes orchestration progress and budget exhaustion only. "
            "final_acceptance_status records the Architect evidence-contract decision, "
            "not theorem proof evidence. Completion status is not simulation evidence "
            "or a claim that remaining formal gaps are closed."
        ),
    }


def _runtime_formal_closure_summary(
    *,
    completion_summary: Mapping[str, Any],
    n_materialized_formal_gap_rows: int,
) -> dict[str, Any]:
    """Separate observed gap rows from target-bound formal closure."""

    raw_rows = completion_summary.get("rows", [])
    rows = (
        [row for row in raw_rows if isinstance(row, Mapping)]
        if isinstance(raw_rows, list)
        else []
    )
    n_questions = len(rows)
    n_satisfied = sum(
        1 for row in rows if _bool_like(row.get("formal_satisfied", False))
    )
    n_unverified = max(0, n_questions - n_satisfied)
    materialized_rows = max(0, int(n_materialized_formal_gap_rows or 0))
    if not n_questions:
        closure_status = "NO_QUESTION_ROWS"
    elif n_unverified:
        closure_status = "FORMAL_CLOSURE_UNVERIFIED"
    else:
        closure_status = "ALL_QUESTIONS_FORMALLY_SATISFIED"
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeFormalClosureSummary",
        "n_questions": n_questions,
        "n_questions_formal_satisfied": n_satisfied,
        "n_questions_formal_unverified": n_unverified,
        "n_materialized_formal_gap_rows": materialized_rows,
        "formal_closure_verified_for_all_questions": bool(
            n_questions and not n_unverified
        ),
        "formal_closure_status": closure_status,
        "formal_gap_inventory_status": (
            "MATERIALIZED_GAP_ROWS_PRESENT"
            if materialized_rows
            else "NO_MATERIALIZED_GAP_ROWS"
        ),
        "boundary": (
            "Materialized formal-gap rows are an observed inventory, not an "
            "exhaustive complement of proof. Zero rows never imply formal closure; "
            "closure requires each question's target-bound formal_satisfied gate."
        ),
    }


def _runtime_failure_summary(completion_summary: Mapping[str, Any]) -> dict[str, Any]:
    rows = completion_summary.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    policy_block_rows = [
        row for row in rows
        if isinstance(row, Mapping)
        and str(row.get("terminal_kind", "") or "") == "formal_required_blocked"
    ]
    failure_rows = [
        row for row in rows
        if isinstance(row, Mapping)
        and str(row.get("terminal_kind", "") or "") in {
            "failed",
            "blocked",
        }
    ]
    incomplete_rows = [
        row for row in rows
        if isinstance(row, Mapping)
        and str(row.get("terminal_kind", "") or "") in {
            "budget_exhausted_with_pending_next_task",
            "budget_exhausted_without_pending_next_task",
        }
    ]
    pending_rows = [
        row
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get("pending_next_task_id", "") or "").strip()
        and isinstance(row.get("pending_next_task", {}), Mapping)
        and bool(row.get("pending_next_task", {}))
    ]
    first_failure = failure_rows[0] if failure_rows else {}
    first_policy_block = policy_block_rows[0] if policy_block_rows else {}
    first_pending = pending_rows[0] if pending_rows else {}
    first_terminal = (
        first_failure
        or first_policy_block
        or (incomplete_rows[0] if incomplete_rows else {})
    )
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeFailureSummary",
        "n_failure_rows": len(failure_rows),
        "n_policy_block_rows": len(policy_block_rows),
        "n_incomplete_rows": len(incomplete_rows),
        "has_failure": bool(failure_rows),
        "has_policy_block": bool(policy_block_rows),
        "has_incomplete_pending_work": bool(incomplete_rows),
        "n_pending_next_tasks": len(pending_rows),
        "terminal_question_id": str(first_terminal.get("question_id", "") or ""),
        "terminal_subsystem": str(first_terminal.get("last_completed_subsystem", "") or ""),
        "terminal_task_id": str(
            first_terminal.get("last_completed_task_id", "")
            or first_terminal.get("final_task_id", "")
            or ""
        ),
        "terminal_status": str(first_terminal.get("status", "") or ""),
        "terminal_kind": str(first_terminal.get("terminal_kind", "") or ""),
        "terminal_classification": str(first_terminal.get("last_failure_classification", "") or ""),
        "failed_question_id": str(first_failure.get("question_id", "") or ""),
        "failed_subsystem": str(first_failure.get("last_completed_subsystem", "") or ""),
        "failed_task_id": str(
            first_failure.get("last_completed_task_id", "")
            or first_failure.get("final_task_id", "")
            or ""
        ),
        "failure_status": str(first_failure.get("status", "") or ""),
        "failure_terminal_kind": str(first_failure.get("terminal_kind", "") or ""),
        "failure_classification": str(first_failure.get("last_failure_classification", "") or ""),
        "policy_block_question_id": str(first_policy_block.get("question_id", "") or ""),
        "policy_block_subsystem": str(
            first_policy_block.get("last_completed_subsystem", "") or ""
        ),
        "policy_block_task_id": str(
            first_policy_block.get("last_completed_task_id", "")
            or first_policy_block.get("final_task_id", "")
            or ""
        ),
        "policy_block_status": str(first_policy_block.get("status", "") or ""),
        "policy_block_terminal_kind": str(
            first_policy_block.get("terminal_kind", "") or ""
        ),
        "policy_block_classification": str(
            first_policy_block.get("last_failure_classification", "") or ""
        ),
        "pending_question_id": str(first_pending.get("question_id", "") or ""),
        "pending_next_task_id": str(
            first_pending.get("pending_next_task_id", "") or ""
        ),
        "pending_next_task": (
            dict(first_pending.get("pending_next_task", {}))
            if isinstance(first_pending.get("pending_next_task"), Mapping)
            else {}
        ),
        "pending_task_continuation_ref": (
            dict(first_pending.get("pending_task_continuation_ref", {}))
            if isinstance(
                first_pending.get("pending_task_continuation_ref"),
                Mapping,
            )
            else {}
        ),
        "pending_task_checkpoint_reason": str(
            first_pending.get("pending_task_checkpoint_reason", "") or ""
        ),
        "payload_policy": "content_addressed_task_continuations",
        "boundary": (
            "Runtime terminal status is an orchestration diagnostic. Budget exhaustion "
            "with a pending next task is incomplete work, not a subsystem failure. A "
            "formal-required policy block means the evidence contract correctly refused "
            "final acceptance without required kernel proof; it is not theorem success. "
            "This summary does not downgrade kernel-verified subclaims or promote "
            "partial runtime progress to theorem proof evidence."
        ),
    }


def _runtime_pending_next_task_rows(
    completion_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return every question-bound continuation without promoting its evidence."""

    completion_rows = completion_summary.get("rows", [])
    if not isinstance(completion_rows, list):
        return []
    rows: list[dict[str, Any]] = []
    for completion_row in completion_rows:
        if not isinstance(completion_row, Mapping):
            continue
        pending_next_task_id = str(
            completion_row.get("pending_next_task_id", "") or ""
        ).strip()
        pending_next_task = completion_row.get("pending_next_task", {})
        if not pending_next_task_id or not isinstance(
            pending_next_task,
            Mapping,
        ) or not pending_next_task:
            continue
        continuation_ref = completion_row.get(
            "pending_task_continuation_ref",
            {},
        )
        if not (
            isinstance(continuation_ref, Mapping)
            and continuation_ref.get("artifact_kind")
            == "RuntimeAgentTaskContinuationRef"
        ):
            raise ValueError(
                "pending runtime task is missing its content-addressed continuation"
            )
        rows.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "RuntimePendingNextTask",
                "question_id": str(
                    completion_row.get("question_id", "") or ""
                ),
                "question_title": str(
                    completion_row.get("question_title", "") or ""
                ),
                "pending_next_task_id": pending_next_task_id,
                "pending_next_task": dict(pending_next_task),
                "pending_task_continuation_ref": dict(continuation_ref),
                "pending_task_checkpoint_reason": str(
                    completion_row.get(
                        "pending_task_checkpoint_reason",
                        "",
                    )
                    or ""
                ),
                "payload_policy": "content_addressed_task_continuations",
                "terminal_kind": str(
                    completion_row.get("terminal_kind", "") or ""
                ),
                "terminal_status": str(
                    completion_row.get("status", "") or ""
                ),
                "last_completed_subsystem": str(
                    completion_row.get("last_completed_subsystem", "") or ""
                ),
                "last_failure_classification": str(
                    completion_row.get(
                        "last_failure_classification",
                        "",
                    )
                    or ""
                ),
                "proof_evidence_status": (
                    "PENDING_RUNTIME_TASK_NOT_PROOF_EVIDENCE"
                ),
                "boundary": (
                    "A pending runtime task preserves question-bound orchestration "
                    "state for continuation. It is not empirical, simulation, or "
                    "theorem proof evidence."
                ),
            }
        )
    return rows


LEAN_LSP_MCP_EXECUTED_TOOL_STATUSES = frozenset(
    {
        "mcp_tool_call_failed",
        "mcp_tool_call_succeeded",
        "mcp_tool_call_timeout",
    }
)


def generated_sandbox_workspace_closure_counts(
    artifacts: Mapping[str, Any],
) -> dict[str, int]:
    """Count direct model-owned failed-to-passed workspace trajectories."""

    artifacts = _runtime_artifacts_with_generated_sandbox_live_provenance(artifacts)
    counts = {
        "algorithm_failed_then_passed": 0,
        "simulation_failed_then_passed": 0,
    }
    for artifact in artifacts.values():
        if not isinstance(artifact, Mapping):
            continue
        kind = str(artifact.get("artifact_kind", "") or "")
        if kind == "RuntimeAlgorithmSandboxManifest":
            rows = artifact.get("prototypes", [])
            counter_key = "algorithm_failed_then_passed"
        elif kind == "RuntimeSimulationManifest":
            rows = artifact.get("generated_simulation_sandbox_prototypes", [])
            counter_key = "simulation_failed_then_passed"
        else:
            continue
        question = (
            artifact.get("question", {})
            if isinstance(artifact.get("question", {}), Mapping)
            else {}
        )
        question_id = str(question.get("id", "") or "").strip()
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, Mapping) or not _generated_sandbox_row_live_generated(row):
                continue
            workspace = row.get("scientific_code_workspace", {})
            if not isinstance(workspace, Mapping):
                continue
            parent_hash = str(workspace.get("parent_code_draft_hash", "") or "")
            child_hash = str(workspace.get("submitted_code_draft_hash", "") or "")
            workspace_artifact_id = str(workspace.get("artifact_id", "") or "")
            closed = bool(
                workspace.get("initial_check_accepted") is False
                and workspace.get("accepted") is True
                and workspace.get("model_owned_source") is True
                and workspace.get("runtime_edited_source") is False
                and workspace.get("source_changed") is True
                and parent_hash
                and child_hash
                and parent_hash != child_hash
                and str(row.get("prototype_artifact_id", "") or "")
                == _generated_sandbox_prototype_artifact_id(row)
                and workspace_artifact_id
                and (not question_id or workspace_artifact_id.startswith(question_id + ":"))
                and str(workspace.get("initial_check_result_hash", "") or "")
                and str(workspace.get("terminal_check_result_hash", "") or "")
                and str(workspace.get("transcript_fingerprint", "") or "")
                and _runtime_safe_int(workspace.get("source_updates")) > 0
                and _runtime_safe_int(workspace.get("sandbox_checks")) > 0
                and _runtime_safe_int(workspace.get("runtime_executed_tool_calls"))
                >= 2
            )
            if closed:
                counts[counter_key] += 1
    return counts


def _runtime_safe_list_len(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _runtime_safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0




RUNTIME_REQUIRED_THEORY_TRACE_CONSUMERS = (
    "SimulationEngineer",
    "AlgorithmEngineer",
    "FormalizerProofEngineer",
)


def _runtime_theory_trace_consumption_contracts(
    artifact: Mapping[str, Any],
) -> list[dict[str, Any]]:
    contract_keys = (
        "theory_trace_consumption_contract",
        "llm_simulation_engineer_theory_trace_consumption_contract",
        "llm_algorithm_engineer_theory_trace_consumption_contract",
        "llm_formalizer_proof_engineer_theory_trace_consumption_contract",
    )
    contracts: list[dict[str, Any]] = []
    for key in contract_keys:
        contract = artifact.get(key)
        if isinstance(contract, Mapping) and contract:
            contracts.append(dict(contract))
    return contracts


def _runtime_theory_trace_alignment_consumer_from_artifact(
    artifact: Mapping[str, Any],
) -> str:
    kind = str(artifact.get("artifact_kind", "") or "")
    source_agent = str(artifact.get("source_agent", "") or "")
    if kind == "SimulationEngineerProposalPacket" or source_agent == (
        "LLMSimulationEngineerAgent"
    ):
        return "SimulationEngineer"
    if kind == "AlgorithmEngineerProposalPacket" or source_agent == (
        "LLMAlgorithmEngineerAgent"
    ):
        return "AlgorithmEngineer"
    if kind == "FormalizerProofEngineerProposalPacket" or source_agent == (
        "LLMFormalizerProofEngineerAgent"
    ):
        return "FormalizerProofEngineer"
    return ""








def _append_runtime_architect_initial_routing_record(
    records: list[dict[str, Any]],
    seen: set[str],
    value: Any,
) -> None:
    if not (
        isinstance(value, Mapping)
        and value.get("artifact_kind") == "ArchitectInitialRoutingDecision"
    ):
        return
    record = dict(value)
    fingerprint = json.dumps(record, sort_keys=True, default=str)
    if fingerprint in seen:
        return
    seen.add(fingerprint)
    records.append(record)




def _runtime_formal_source_hits(
    retriever: Any,
    *,
    problem: ResearchProblemSpec,
    theorem_goals: list[TheoremGoal],
    k: int,
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for goal in theorem_goals:
        query = " ".join(
            [
                problem.problem_class,
                problem.dgp,
                problem.estimand,
                " ".join(problem.assumptions),
                goal.title,
                goal.informal_statement,
                goal.proof_strategy,
                " ".join(goal.required_primitives),
                " ".join(goal.proof_obligations),
            ]
        )
        hits = retriever.search(query, k=k) if retriever is not None else []
        groups.append(
            {
                "theorem_goal_id": goal.id,
                "query_fingerprint": stable_hash(query),
                "hits": [
                    _formal_source_hit_to_json(
                        row,
                        formal_source_retriever=(retriever if index == 0 else None),
                    )
                    for index, row in enumerate(hits)
                ],
            }
        )
    return groups


def _knowledge_card_to_json(card: KnowledgeCard) -> dict[str, Any]:
    return asdict(card)


def _paper_source_to_json(source: PaperSourceHit) -> dict[str, Any]:
    return asdict(source)


def _formal_source_hit_to_json(
    hit: FormalSourceHit,
    *,
    formal_source_retriever: Any | None = None,
) -> dict[str, Any]:
    declaration = hit.declaration
    row = {
        "source_id": declaration.source_id,
        "source_type": declaration.source_type,
        "path": declaration.path,
        "line": declaration.line,
        "kind": declaration.kind,
        "name": declaration.name,
        "namespace": declaration.namespace,
        "signature": declaration.signature,
        "imports": list(declaration.imports),
        "reference": declaration.reference,
        "reference_aliases": list(declaration.reference_aliases),
        "module_summary": declaration.module_summary,
        "declaration_doc": declaration.declaration_doc,
        "section_summary": declaration.section_summary,
        "module_group": declaration.module_group,
        "module_group_summary": declaration.module_group_summary,
        "score": round(hit.score, 4),
        "matched_terms": list(hit.matched_terms),
    }
    provenance = getattr(hit, "provenance", {})
    if isinstance(provenance, Mapping) and provenance:
        row["provenance"] = prompt_safe_formal_source_provenance(provenance)
    if formal_source_retriever is not None:
        source_context = formal_source_context_for_hit(
            retriever=formal_source_retriever,
            hit=hit,
        )
        if source_context:
            row["declaration_source_context"] = source_context
    return row


def _runtime_evaluation_mode_from_context(
    architect_context: Mapping[str, Any] | None,
) -> str:
    context = architect_context if isinstance(architect_context, Mapping) else {}
    plan = context.get("architect_runtime_plan", {})
    plan_contract = (
        plan.get("evidence_contract", {}) if isinstance(plan, Mapping) else {}
    )
    requested_contract = context.get("runtime_requested_evidence_contract", {})
    for value in (
        plan_contract.get("evaluation_mode", "")
        if isinstance(plan_contract, Mapping)
        else "",
        requested_contract.get("evaluation_mode", "")
        if isinstance(requested_contract, Mapping)
        else "",
        context.get("runtime_evaluation_mode", ""),
    ):
        normalized = str(value or "").strip()
        if normalized:
            return normalized
    return "debug"


def _research_evaluation_critic_task(
    *,
    question: OpenResearchQuestion,
    packet_id: str,
    simulation_manifest_id: str,
    algorithm_sandbox_manifest_id: str,
    architect_context: Mapping[str, Any] | None = None,
) -> AgentTask:
    context = dict(architect_context or {})
    return AgentTask(
        task_id=(
            f"critic-research-eval:{question.id}:"
            f"{stable_hash([packet_id, simulation_manifest_id, algorithm_sandbox_manifest_id])[:8]}"
        ),
        owner_subsystem="CriticEvaluator",
        objective=(
            "Evaluate the serious theory, generated algorithm, frozen empirical "
            "protocol, generated simulation, and independent semantic reviews. "
            "Report formalization status separately without requiring the strict "
            "formal lane in this research evaluation."
        ),
        inputs={
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "algorithm_sandbox_manifest_id": algorithm_sandbox_manifest_id,
            "architect_context": context,
        },
        allowed_tools=("model_backend", "blackboard", "evidence_ledger"),
        expected_artifacts=_architect_expected_artifacts(
            context,
            "CriticEvaluator",
            ("critic_evaluator_manifest", "critic_model_packet"),
        ),
        acceptance_gate=_architect_acceptance_gate(
            context,
            "CriticEvaluator",
            "all required research artifacts are lineage-bound, independently reviewed, and accepted without promoting them to proof evidence",
        ),
        stop_condition="critic records the research-evaluation decision and open formal debt",
    )


def _post_empirical_evidence_task(
    *,
    question: OpenResearchQuestion,
    packet_id: str,
    simulation_manifest_id: str,
    algorithm_sandbox_manifest_id: str = "",
    architect_context: Mapping[str, Any] | None = None,
) -> AgentTask:
    if _runtime_evaluation_mode_from_context(architect_context) == "research_eval":
        return _research_evaluation_critic_task(
            question=question,
            packet_id=packet_id,
            simulation_manifest_id=simulation_manifest_id,
            algorithm_sandbox_manifest_id=algorithm_sandbox_manifest_id,
            architect_context=architect_context,
        )
    return _formalization_task(
        question=question,
        packet_id=packet_id,
        simulation_manifest_id=simulation_manifest_id,
        algorithm_sandbox_manifest_id=algorithm_sandbox_manifest_id,
        architect_context=architect_context,
    )


def _formalization_task(
    *,
    question: OpenResearchQuestion,
    packet_id: str,
    simulation_manifest_id: str,
    algorithm_sandbox_manifest_id: str = "",
    architect_context: Mapping[str, Any] | None = None,
) -> AgentTask:
    context = dict(architect_context or {})
    return AgentTask(
        task_id=f"formalize:{question.id}:{stable_hash([packet_id, simulation_manifest_id, algorithm_sandbox_manifest_id])[:8]}",
        owner_subsystem="FormalizationEvaluator",
        objective=(
            "Run formal subclaim/proof-gap evaluation for the supported theory "
            "proposal and record proved rows versus formal gaps."
        ),
        inputs={
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "algorithm_sandbox_manifest_id": algorithm_sandbox_manifest_id,
            "architect_context": context,
        },
        allowed_tools=("proof_bank_retriever", "formal_source_retriever", "proof_verifier"),
        expected_artifacts=_architect_expected_artifacts(
            context,
            "FormalizationEvaluator",
            ("formalization_manifest",),
        ),
        acceptance_gate=_architect_acceptance_gate(
            context,
            "FormalizationEvaluator",
            "formalization manifest distinguishes proved subclaims from formal gaps",
        ),
        stop_condition="formalization/proof feedback recorded",
    )


def _generated_sandbox_observation_envelope(
    *,
    manifest: Mapping[str, Any],
    feedback_id: str,
    feedback_type: str,
    source_manifest_key: str,
    source_manifest_id: str,
    failure_classification: str,
    boundary: str,
    prototype_key: str,
    prototypes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Carry complete executor observations without interpreting or editing code."""

    return {
        "feedback_id": feedback_id,
        "feedback_type": feedback_type,
        source_manifest_key: source_manifest_id,
        "source_manifest_artifact_id": source_manifest_id,
        "source_manifest_content_hash": stable_hash(dict(manifest)),
        "failure_classification": failure_classification,
        "boundary": boundary,
        prototype_key: [deepcopy(dict(row)) for row in prototypes],
        "observation_transport": {
            "complete_candidate_rows": True,
            "runtime_interpreted_failure": False,
            "runtime_selected_source_edit": False,
            "same_source_producer_must_revise": True,
        },
    }


def _algorithm_sandbox_revision_feedback(
    *,
    manifest: Mapping[str, Any],
    boundary: str,
    failure_classification: str = "algorithm_sandbox_no_executable_prototype",
) -> dict[str, Any]:
    prototypes = [
        row for row in manifest.get("prototypes", []) or [] if isinstance(row, Mapping)
    ]
    feedback_type = "algorithm_sandbox_execution_feedback"
    source_manifest_id = str(manifest.get("manifest_id", "") or "")
    feedback_id = _generated_sandbox_feedback_id(
        feedback_type=feedback_type,
        source_manifest_id=source_manifest_id,
        failure_classification=failure_classification,
        prototype_rows=prototypes,
    )
    return _generated_sandbox_observation_envelope(
        manifest=manifest,
        feedback_id=feedback_id,
        feedback_type=feedback_type,
        source_manifest_key="algorithm_sandbox_manifest_id",
        source_manifest_id=source_manifest_id,
        failure_classification=failure_classification,
        boundary=boundary,
        prototype_key="prototypes",
        prototypes=prototypes,
    )


def _simulation_code_drafts(proposal_packet: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(proposal_packet, Mapping):
        return []
    return [
        dict(row)
        for row in proposal_packet.get("simulation_code_drafts", []) or []
        if isinstance(row, Mapping)
    ]


def _proposal_defers_scientific_source(
    proposal_packet: Mapping[str, Any] | None,
) -> bool:
    return bool(
        isinstance(proposal_packet, Mapping)
        and proposal_packet.get("scientific_source_transport")
        == SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
    )


def _run_source_owner_scientific_workspace(
    *,
    proposal_agent: Any,
    question: OpenResearchQuestion,
    artifact_id: str,
    code_draft: Mapping[str, Any],
    source_deferred: bool,
    workspace_context: Mapping[str, Any],
    execute_candidate: Callable[
        [Mapping[str, Any]], tuple[dict[str, Any], ToolCallRecord]
    ],
    failure_identity: Mapping[str, Any],
    external_initial_observation: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], list[ToolCallRecord]]:
    """Execute one initial or revision source loop without a second scheduler."""

    can_use_workspace = bool(
        proposal_agent is not None
        and callable(
            getattr(
                getattr(proposal_agent, "provider", None),
                "generate_client_tool_turn",
                None,
            )
        )
        and callable(getattr(proposal_agent, "iterate_code_with_tools", None))
    )
    tool_calls: list[ToolCallRecord] = []
    last_checked_prototype: dict[str, Any] = {}
    bound_execution_fields = {
        "required_estimator_ids": deepcopy(
            list(code_draft.get("required_estimator_ids", []) or [])
        )
    } if "required_estimator_ids" in code_draft else {}

    def check_candidate(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        execution_candidate = {
            **dict(candidate),
            **bound_execution_fields,
        }
        prototype, tool_call = execute_candidate(execution_candidate)
        last_checked_prototype.clear()
        last_checked_prototype.update(deepcopy(dict(prototype)))
        tool_calls.append(tool_call)
        check = {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": prototype.get("smoke_passed") is True,
            "prototype": scientific_workspace_prototype_observation(prototype),
        }
        disposition = str(
            prototype.get("source_iteration_disposition", "") or ""
        ).strip()
        if disposition:
            check["source_iteration_disposition"] = disposition
        source_owner = prototype.get("source_owner", {})
        if isinstance(source_owner, Mapping) and source_owner:
            check["source_owner"] = deepcopy(dict(source_owner))
        return check

    if source_deferred:
        if not can_use_workspace:
            return (
                {
                    **dict(failure_identity),
                    "prototype_status": "MODEL_SOURCE_WORKSPACE_UNAVAILABLE",
                    "smoke_passed": False,
                    "execution_smoke_passed": False,
                    "reason": (
                        "The planning envelope deferred source to native client "
                        "tools, but the source-owning provider has no callable "
                        "workspace."
                    ),
                },
                tool_calls,
            )
        workspace_draft: Mapping[str, Any] | None = None
        workspace_operation = "initial_authoring"
        initial_observation = {
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "artifact_id": artifact_id,
            "execution_attempted": False,
            "observation": (
                "No source exists yet; author and run the complete candidate in "
                "this workspace."
            ),
        }
        prototype = {
            **dict(failure_identity),
            "prototype_status": "MODEL_SOURCE_WORKSPACE_FAILED",
            "smoke_passed": False,
            "execution_smoke_passed": False,
        }
    elif external_initial_observation and can_use_workspace:
        workspace_draft = {
            key: deepcopy(code_draft[key])
            for key in (
                "language",
                "execution_profile",
                "dependencies",
                "entrypoint",
                "code",
            )
            if key in code_draft
        }
        workspace_operation = "targeted_revision"
        initial_observation = {
            **deepcopy(dict(external_initial_observation)),
            "code_draft_hash": stable_hash(workspace_draft),
            "accepted": False,
        }
        prototype = {
            **dict(failure_identity),
            "prototype_status": "MODEL_SOURCE_WORKSPACE_FAILED",
            "smoke_passed": False,
            "execution_smoke_passed": False,
        }
    else:
        prototype, tool_call = execute_candidate(code_draft)
        tool_calls.append(tool_call)
        if (
            prototype.get("smoke_passed") is True
            or prototype.get("source_iteration_disposition")
            == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
            or not can_use_workspace
        ):
            return prototype, tool_calls
        workspace_draft = {
            key: deepcopy(code_draft[key])
            for key in (
                "language",
                "execution_profile",
                "dependencies",
                "entrypoint",
                "code",
            )
            if key in code_draft
        }
        workspace_operation = "targeted_revision"
        initial_observation = {
            "code_draft_hash": stable_hash(workspace_draft),
            "accepted": False,
            "prototype": scientific_workspace_prototype_observation(prototype),
        }

    try:
        workspace_result = proposal_agent.iterate_code_with_tools(
            question=question,
            artifact_id=artifact_id,
            code_draft=workspace_draft,
            initial_observation=initial_observation,
            workspace_context=dict(workspace_context),
            check_candidate=check_candidate,
            workspace_operation=workspace_operation,
        )
    except PacketValidationError as exc:
        if last_checked_prototype:
            prototype = deepcopy(last_checked_prototype)
        prototype["scientific_code_workspace_failure"] = {
            "validation_errors": list(exc.errors),
            "attempts": exc.attempts,
            "history": [dict(row) for row in exc.history],
            "recovery_checkpoint": dict(exc.recovery_checkpoint or {}),
            "runtime_edited_source": False,
        }
        return prototype, tool_calls

    if not last_checked_prototype:
        raise RuntimeError(
            "scientific workspace accepted without a persisted sandbox result"
        )
    prototype = deepcopy(last_checked_prototype)
    prototype["scientific_code_workspace"] = dict(workspace_result.evidence)
    return prototype, tool_calls


def _scientific_workspace_algorithm_handoff(
    value: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    artifacts = []
    for row in value.get("exact_algorithm_artifacts", []) or []:
        if not isinstance(row, Mapping):
            continue
        artifacts.append(
            {
                "estimator_id": str(row.get("estimator_id", "") or ""),
                "language": str(row.get("language", "") or ""),
                "dependencies": list(row.get("dependencies", []) or []),
                "exact_source_hash": str(
                    row.get("exact_source_hash", "") or ""
                ),
                "estimator_interface_contract_id": str(
                    row.get("estimator_interface_contract_id", "") or ""
                ),
                "estimator_interface_contract": deepcopy(
                    dict(row.get("estimator_interface_contract", {}))
                    if isinstance(
                        row.get("estimator_interface_contract", {}), Mapping
                    )
                    else {}
                ),
            }
        )
    return {
        "handoff_id": str(value.get("handoff_id", "") or ""),
        "algorithm_sandbox_manifest_id": str(
            value.get("algorithm_sandbox_manifest_id", "") or ""
        ),
        "semantic_review_packet_id": str(
            value.get("semantic_review_packet_id", "") or ""
        ),
        "exact_algorithm_artifacts": artifacts,
        "boundary": (
            "This projection exposes immutable estimator identities and ABI contracts "
            "to the source-owning simulation model. Runtime executes the exact "
            "reviewed source behind each estimator ID; this is not proof evidence."
        ),
    }


def _scientific_workspace_metric_contracts(
    values: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Project frozen contracts to fields needed for source authoring."""

    fields = (
        "contract_id",
        "requirement_id",
        "artifact_id",
        "metric_path",
        "metric_semantics",
        "measurement_protocol",
        "required_runtime_replicates",
    )
    return [
        {field: deepcopy(row.get(field)) for field in fields}
        for row in values
        if isinstance(row, Mapping)
    ]


def _generated_metric_contract_evaluation_count(
    row: Mapping[str, Any],
    key: str,
) -> int:
    evaluation = row.get("metric_contract_evaluation", {})
    if not isinstance(evaluation, Mapping):
        return 0
    try:
        return max(0, int(evaluation.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0














def _generated_simulation_revision_feedback(
    *,
    manifest: Mapping[str, Any],
    boundary: str,
    failure_classification: str = "generated_simulation_sandbox_no_executable_draft",
) -> dict[str, Any]:
    prototypes = [
        row
        for row in manifest.get("generated_simulation_sandbox_prototypes", []) or []
        if isinstance(row, Mapping)
    ]
    feedback_type = "generated_simulation_sandbox_execution_feedback"
    source_manifest_id = str(manifest.get("manifest_id", "") or "")
    feedback_id = _generated_sandbox_feedback_id(
        feedback_type=feedback_type,
        source_manifest_id=source_manifest_id,
        failure_classification=failure_classification,
        prototype_rows=prototypes,
    )
    return _generated_sandbox_observation_envelope(
        manifest=manifest,
        feedback_id=feedback_id,
        feedback_type=feedback_type,
        source_manifest_key="simulation_manifest_id",
        source_manifest_id=source_manifest_id,
        failure_classification=failure_classification,
        boundary=boundary,
        prototype_key="generated_simulation_prototypes",
        prototypes=prototypes,
    )

def _run_generated_simulation_sandbox(
    *,
    sandbox_dir: Path,
    simulation_id: str,
    code_draft: Mapping[str, Any],
    proposal_packet: Mapping[str, Any] | None = None,
    metric_contracts: Sequence[Mapping[str, Any]] | None = None,
    validation_context: Mapping[str, Any] | None = None,
    upstream_algorithm_handoff: Mapping[str, Any] | None = None,
    n_runs: int,
    seed: int,
    timeout_s: int,
) -> tuple[dict[str, Any], ToolCallRecord]:
    all_estimator_bindings = tuple(
        ScientificEstimatorBinding(
            artifact_id=str(row.get("estimator_id", "") or "").strip(),
            language=str(row.get("language", "") or "").strip(),
            code=str(row.get("exact_source_code", "") or ""),
            code_hash=str(row.get("exact_source_hash", "") or "").strip(),
            dependencies=tuple(
                str(value)
                for value in row.get("dependencies", []) or []
                if str(value).strip()
            ),
        )
        for row in (upstream_algorithm_handoff or {}).get(
            "exact_algorithm_artifacts", []
        )
        if isinstance(row, Mapping)
    )
    available_estimator_bindings = {
        binding.artifact_id: binding
        for binding in all_estimator_bindings
        if binding.artifact_id
    }
    selection_contract_errors: list[str] = []
    if "required_estimator_ids" not in code_draft:
        required_estimator_ids = tuple(available_estimator_bindings)
        estimator_bindings = all_estimator_bindings
    else:
        raw_required_estimator_ids = code_draft.get("required_estimator_ids")
        if not isinstance(raw_required_estimator_ids, list):
            selection_contract_errors.append(
                "generated simulation required_estimator_ids must be an array"
            )
            required_estimator_ids = ()
        else:
            required_estimator_ids = tuple(
                dict.fromkeys(
                    str(value or "").strip()
                    for value in raw_required_estimator_ids
                    if str(value or "").strip()
                )
            )
        unknown_estimator_ids = sorted(
            set(required_estimator_ids) - set(available_estimator_bindings)
        )
        if unknown_estimator_ids:
            selection_contract_errors.append(
                "generated simulation selected unknown accepted estimator ids: "
                + ", ".join(unknown_estimator_ids)
            )
        if available_estimator_bindings and not required_estimator_ids:
            selection_contract_errors.append(
                "generated simulation must select at least one accepted estimator"
            )
        if not available_estimator_bindings and required_estimator_ids:
            selection_contract_errors.append(
                "generated simulation cannot select an estimator without an accepted handoff"
            )
        estimator_bindings = tuple(
            available_estimator_bindings[estimator_id]
            for estimator_id in required_estimator_ids
            if estimator_id in available_estimator_bindings
        )
    selected_metric_contracts = (
        [dict(row) for row in metric_contracts]
        if metric_contracts is not None
        else generated_metric_contracts_for_artifact(
            (proposal_packet or {}).get("metric_contracts", []),
            artifact_id=simulation_id,
        )
    )
    prototype, tool_call = _run_generated_code_sandbox(
        sandbox_dir=sandbox_dir,
        estimator_id=simulation_id,
        spec={
            "id": simulation_id,
            "artifact_kind": "generated_simulation_sandbox",
            "simulation_targets": list(
                (proposal_packet or {}).get("simulation_targets", []) or []
            ),
        },
        code_draft=code_draft,
        metric_contracts=selected_metric_contracts,
        validation_context={
            "proposal_packet": proposal_packet or {},
            "simulation_id": simulation_id,
            **(dict(validation_context or {})),
        },
        estimator_bindings=estimator_bindings,
        additional_contract_errors=selection_contract_errors,
        n_runs=n_runs,
        seed=seed,
        timeout_s=timeout_s,
    )
    simulation_boundary = (
        "Generated simulation sandbox drafts are untrusted LLM stress-test "
        "proposals. AgentRuntime runs only drafts accepted by the selected "
        "bounded stdlib or scientific-WASM profile. Passing results are "
        "simulation evidence only, not theorem proof evidence."
    )
    prototype = dict(prototype)
    prototype["simulation_id"] = simulation_id
    prototype["required_estimator_ids"] = list(required_estimator_ids)
    prototype["available_upstream_estimator_ids"] = list(
        available_estimator_bindings
    )
    prototype["executor"] = "generated_simulation_sandbox"
    prototype["simulation_evidence_status"] = (
        "GENERATED_SIMULATION_SANDBOX_EXECUTION_NOT_PROOF_EVIDENCE"
    )
    execution_smoke_passed = bool(
        prototype.get("execution_smoke_passed", prototype.get("smoke_passed") is True)
    )
    metric_gate_errors = list(_str_tuple(prototype.get("metric_gate_errors", [])))
    prototype["execution_smoke_passed"] = execution_smoke_passed
    prototype["metric_gate_errors"] = metric_gate_errors
    prototype["smoke_passed"] = execution_smoke_passed and not metric_gate_errors
    if execution_smoke_passed and metric_gate_errors:
        prototype["prototype_status"] = "FAILED_METRIC_GATE"
    prototype["boundary"] = simulation_boundary
    dependency_failure_ids = list(
        prototype.get("estimator_runtime_failure_ids", []) or []
    )
    if prototype.get("estimator_binding_errors") and not dependency_failure_ids:
        dependency_failure_ids = list(required_estimator_ids)
    source_manifest_id = str(
        (upstream_algorithm_handoff or {}).get(
            "algorithm_sandbox_manifest_id", ""
        )
        or ""
    ).strip()
    source_manifest_hash = str(
        (upstream_algorithm_handoff or {}).get(
            "algorithm_sandbox_manifest_hash", ""
        )
        or ""
    ).strip()
    bound_hashes = dict(prototype.get("bound_estimator_code_hashes", {}) or {})
    exact_dependency_binding = bool(
        dependency_failure_ids
        and source_manifest_id
        and source_manifest_hash
        and all(
            str(bound_hashes.get(artifact_id, "") or "").strip()
            for artifact_id in dependency_failure_ids
        )
    )
    if exact_dependency_binding:
        prototype["source_iteration_disposition"] = (
            SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
        )
        prototype["source_owner"] = {
            "owner_subsystem": "AlgorithmEngineer",
            "source_manifest_id": source_manifest_id,
            "source_manifest_hash": source_manifest_hash,
            "artifact_ids": dependency_failure_ids,
            "artifact_hashes": {
                artifact_id: str(bound_hashes.get(artifact_id, "") or "")
                for artifact_id in dependency_failure_ids
            },
        }
    tool_language = normalized_generated_code_language(code_draft.get("language"))
    wrapped_tool_call = ToolCallRecord(
        tool_name=(
            f"{tool_language}.generated_simulation_sandbox"
            if tool_call.tool_name.endswith(".generated_algorithm_sandbox")
            else f"{tool_language}.generated_simulation_sandbox_precheck"
        ),
        inputs={
            **dict(tool_call.inputs),
            "simulation_id": simulation_id,
            "required_estimator_ids": list(required_estimator_ids),
        },
        output_paths=tuple(tool_call.output_paths),
        input_hash=tool_call.input_hash,
        output_hash=tool_call.output_hash,
        exit_status=tool_call.exit_status,
        stdout_summary=tool_call.stdout_summary,
        stderr_summary=tool_call.stderr_summary,
        safety_boundary=simulation_boundary,
    )
    return prototype, wrapped_tool_call




def _generated_sandbox_metric_gate_result(
    metrics: Any,
    *,
    context: Mapping[str, Any] | None = None,
    code: str = "",
) -> tuple[list[str], dict[str, Any], str]:
    metric_context = dict(context or {})
    contracts = [
        dict(row)
        for row in metric_context.get("typed_metric_contracts", []) or []
        if isinstance(row, Mapping)
    ]
    if contracts:
        artifact_id = str(
            metric_context.get("metric_contract_artifact_id", "")
            or metric_context.get("estimator_id", "")
            or contracts[0].get("artifact_id", "")
        ).strip()
        evaluation = evaluate_generated_metric_contracts(
            metrics,
            contracts=contracts,
            artifact_id=artifact_id,
            runtime_replicates=metric_context.get("runtime_replicates"),
            authoritative_requirements=metric_context.get(
                "authoritative_metric_requirements"
            ),
            target_subsystem=str(
                metric_context.get("metric_requirement_target_subsystem", "")
                or ""
            ),
            require_authoritative_requirements=bool(
                metric_context.get(
                    "require_authoritative_metric_requirements", False
                )
            ),
        )
        errors = list(_str_tuple(evaluation.get("required_failure_errors", [])))
        return sorted(set(errors)), evaluation, "typed_artifact_bound"
    return [], {}, "execution_only_no_typed_contract"


def _estimator_spec(packet: Any, estimator_id: str) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {}
    for row in packet.get("estimator_specs", []) or []:
        if not isinstance(row, Mapping):
            continue
        row_id = str(row.get("id") or row.get("name") or "")
        if row_id == estimator_id:
            return dict(row)
    return {}


def _generated_sandbox_diagnostic_excerpt(
    value: Any,
) -> str:
    """Preserve the exact tool observation supplied to the coding model."""

    return str(value or "").strip()


def _run_generated_code_sandbox(
    *,
    sandbox_dir: Path,
    estimator_id: str,
    spec: Mapping[str, Any],
    code_draft: Mapping[str, Any],
    validation_context: Mapping[str, Any] | None = None,
    n_runs: int,
    seed: int,
    timeout_s: int,
    metric_contracts: Sequence[Mapping[str, Any]] = (),
    estimator_bindings: Sequence[ScientificEstimatorBinding] = (),
    additional_contract_errors: Sequence[str] = (),
    required_callable_exports: Sequence[str] = (),
) -> tuple[dict[str, Any], ToolCallRecord]:
    """Execute every generated draft through one isolated runtime path."""

    normalized_draft = dict(code_draft)
    language = normalized_generated_code_language(normalized_draft.get("language"))
    profile = normalized_generated_code_profile(
        normalized_draft.get("execution_profile"),
        language=language,
    )
    normalized_draft["language"] = language
    normalized_draft["execution_profile"] = profile
    normalized_draft["dependencies"] = list(
        normalized_scientific_dependencies(
            normalized_draft.get("dependencies", []),
            language=language,
        )
    )
    contract_errors = sorted(
        set(
            [
                *generated_code_execution_contract_errors(code_draft),
                *(str(error) for error in additional_contract_errors if str(error)),
            ]
        )
    )
    return _run_generated_scientific_sandbox(
        sandbox_dir=sandbox_dir,
        estimator_id=estimator_id,
        spec=spec,
        code_draft=normalized_draft,
        validation_context=validation_context,
        n_runs=n_runs,
        seed=seed,
        timeout_s=timeout_s,
        metric_contracts=metric_contracts,
        contract_errors=contract_errors,
        estimator_bindings=estimator_bindings,
        required_callable_exports=required_callable_exports,
    )


def _run_generated_scientific_sandbox(
    *,
    sandbox_dir: Path,
    estimator_id: str,
    spec: Mapping[str, Any],
    code_draft: Mapping[str, Any],
    validation_context: Mapping[str, Any] | None,
    n_runs: int,
    seed: int,
    timeout_s: int,
    metric_contracts: Sequence[Mapping[str, Any]],
    contract_errors: Sequence[str] = (),
    estimator_bindings: Sequence[ScientificEstimatorBinding] = (),
    required_callable_exports: Sequence[str] = (),
) -> tuple[dict[str, Any], ToolCallRecord]:
    code = str(code_draft.get("code", "") or "")
    language = normalized_generated_code_language(code_draft.get("language"))
    requested_profile = normalized_generated_code_profile(
        code_draft.get("execution_profile"),
        language=language,
    )
    dependencies = normalized_scientific_dependencies(
        code_draft.get("dependencies", []),
        language=language,
    )
    validation_payload = dict(validation_context or {})
    typed_metric_contracts = [dict(row) for row in metric_contracts]
    metric_contract_set_id = generated_metric_contract_set_id(
        typed_metric_contracts
    )
    authoritative_metric_requirements = [
        dict(row)
        for row in validation_payload.get(
            "authoritative_metric_requirements", []
        )
        or []
        if isinstance(row, Mapping)
    ]
    metric_requirement_set_id = generated_metric_requirement_set_id(
        authoritative_metric_requirements
    )
    metric_requirement_authority_policy = str(
        validation_payload.get("metric_requirement_authority_policy", "") or ""
    )
    metric_requirement_authority_required = bool(
        validation_payload.get("require_authoritative_metric_requirements", False)
    )
    replicates = generated_sandbox_runtime_replicates(n_runs)
    execution = None
    if not contract_errors:
        execution = execute_scientific_sandbox(
            sandbox_dir=sandbox_dir,
            artifact_id=estimator_id,
            language=language,
            code=code,
            dependencies=dependencies,
            seed=seed,
            replicates=replicates,
            timeout_s=timeout_s,
            estimator_bindings=estimator_bindings,
            required_callable_exports=required_callable_exports,
        )
    errors = list(contract_errors)
    if execution is not None:
        errors.extend(execution.errors)
    estimator_binding_errors = (
        list(execution.estimator_binding_errors) if execution is not None else []
    )
    estimator_runtime_failure_ids = (
        list(execution.estimator_runtime_failure_ids) if execution is not None else []
    )
    estimator_runtime_errors = (
        list(execution.estimator_runtime_errors) if execution is not None else []
    )
    metrics = dict(execution.metrics) if execution is not None else {}
    execution_smoke_passed = bool(
        execution is not None
        and execution.status == "EXECUTED"
        and metrics
        and not bool(metrics.get("sandbox_failed", False))
        and _metrics_are_finite(metrics)
    )
    metric_gate_policy_mode = (
        "typed_artifact_bound"
        if typed_metric_contracts
        else "execution_only_no_typed_contract"
    )
    metric_context = {
        "estimator_id": estimator_id,
        "metric_contract_artifact_id": estimator_id,
        "typed_metric_contracts": typed_metric_contracts,
        "runtime_replicates": replicates,
        "spec": spec,
        "code_draft": code_draft,
        **validation_payload,
    }
    metric_gate_errors, metric_contract_evaluation, metric_gate_policy_mode = (
        _generated_sandbox_metric_gate_result(
            metrics,
            context=metric_context,
            code=code,
        )
        if execution_smoke_passed
        else ([], {}, metric_gate_policy_mode)
    )
    smoke_passed = execution_smoke_passed and not metric_gate_errors
    prototype_status = "FAILED"
    if contract_errors or (
        execution is not None and execution.status == "REJECTED_CONTRACT"
    ):
        prototype_status = "REJECTED_UNSAFE_GENERATED_CODE"
    elif execution is not None and execution.status in {
        "RUNTIME_UNAVAILABLE",
        "DEPENDENCY_CACHE_UNPREPARED",
    }:
        prototype_status = "SCIENTIFIC_RUNTIME_UNAVAILABLE"
    elif execution_smoke_passed:
        prototype_status = "FAILED_METRIC_GATE" if metric_gate_errors else "EXECUTED"
    boundary = (
        execution.boundary
        if execution is not None
        else (
            "Generated scientific code is an untrusted implementation proposal. "
            "Rejected metadata or source is not execution evidence and never proof evidence."
        )
    )
    script_path = execution.code_path if execution is not None else ""
    result_path = execution.result_path if execution is not None else ""
    execution_envelope_path = (
        execution.execution_envelope_path if execution is not None else ""
    )
    request_path = execution.request_path if execution is not None else ""
    returncode = execution.returncode if execution is not None else -1
    stdout_summary = (
        _generated_sandbox_diagnostic_excerpt(execution.stdout_summary)
        if execution is not None
        else ""
    )
    stderr_summary = (
        _generated_sandbox_diagnostic_excerpt(execution.stderr_summary)
        if execution is not None
        else _generated_sandbox_diagnostic_excerpt("; ".join(errors))
    )
    metric_gate_targets = (
        {
            "metric_contract_set_id": metric_contract_set_id,
            "n_metric_contracts": len(typed_metric_contracts),
            "runtime_replicates": replicates,
        }
        if typed_metric_contracts
        else {}
    )
    expected_estimator_code_hashes = {
        binding.artifact_id: binding.code_hash for binding in estimator_bindings
    }
    estimator_invocation_counts = (
        dict(execution.estimator_invocation_counts)
        if execution is not None
        else {}
    )
    estimator_invocation_samples = (
        deepcopy(dict(execution.estimator_invocation_samples))
        if execution is not None
        else {}
    )
    mechanical_estimator_invocation_verified = bool(
        estimator_bindings
        and execution is not None
        and execution.status == "EXECUTED"
        and bool(execution.execution_envelope_hash)
        and execution.estimator_code_hashes == expected_estimator_code_hashes
        and all(
            estimator_invocation_counts.get(binding.artifact_id, 0) > 0
            for binding in estimator_bindings
        )
    )
    prototype = {
        "estimator_id": estimator_id,
        "prototype_status": prototype_status,
        "executor": "generated_python_sandbox",
        "executor_family": "generated_algorithm_sandbox",
        "executor_profile": (
            SCIENTIFIC_WASM_SANDBOX_PROFILE
            if estimator_bindings
            else requested_profile
        ),
        "requested_execution_profile": requested_profile,
        "language": language,
        "dependencies": list(dependencies),
        "backend": (
            execution.backend
            if execution is not None
            else ("webr" if language == "r" else "pyodide")
        ),
        "isolation_provider": (
            execution.isolation_provider if execution is not None else ""
        ),
        "spec": dict(spec),
        "script_path": script_path,
        "request_path": request_path,
        "runner_path": "",
        "result_path": result_path,
        "execution_envelope_path": execution_envelope_path,
        "execution_envelope_hash": (
            execution.execution_envelope_hash if execution is not None else ""
        ),
        "estimator_binding_hash": (
            execution.estimator_binding_hash if execution is not None else ""
        ),
        "bound_estimator_code_hashes": (
            dict(execution.estimator_code_hashes) if execution is not None else {}
        ),
        "estimator_invocation_counts": estimator_invocation_counts,
        "estimator_invocation_samples": estimator_invocation_samples,
        "mechanical_estimator_invocation_verified": (
            mechanical_estimator_invocation_verified
        ),
        "required_callable_exports": [
            str(value) for value in required_callable_exports
        ],
        "script_hash": stable_hash(code),
        "source_code": code,
        "request_hash": execution.request_hash if execution is not None else "",
        "code_excerpt": code[:2000],
        "runtime_seed": seed,
        "runtime_replicates": replicates,
        "result_hash": stable_hash(metrics) if metrics else "",
        "returncode": returncode,
        "execution_attempted": bool(
            execution is not None and execution.execution_attempted
        ),
        "subprocess_environment_keys": (
            list(execution.subprocess_environment_keys)
            if execution is not None
            else []
        ),
        "resource_limits": (
            dict(execution.resource_limits) if execution is not None else {}
        ),
        "stdout_summary": stdout_summary,
        "stderr_summary": stderr_summary,
        "result_parse_error": (
            execution.result_parse_error if execution is not None else ""
        ),
        "safety_errors": (
            errors if prototype_status == "REJECTED_UNSAFE_GENERATED_CODE" else []
        ),
        "runtime_errors": (
            errors if prototype_status != "REJECTED_UNSAFE_GENERATED_CODE" else []
        ),
        "estimator_binding_errors": estimator_binding_errors,
        "estimator_runtime_failure_ids": estimator_runtime_failure_ids,
        "estimator_runtime_errors": estimator_runtime_errors,
        "metrics": metrics,
        "metric_gate_targets": metric_gate_targets,
        "metric_contracts": typed_metric_contracts,
        "metric_contract_set_id": metric_contract_set_id,
        "metric_requirement_set_id": metric_requirement_set_id,
        "metric_requirement_authority_policy": metric_requirement_authority_policy,
        "metric_requirement_authority_required": metric_requirement_authority_required,
        "metric_requirement_authority_validated": bool(
            metric_contract_evaluation.get(
                "metric_requirement_authority_validated", False
            )
        ),
        "metric_contract_evaluation": metric_contract_evaluation,
        "metric_contract_proof_evidence_status": (
            GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
        ),
        "metric_contract_boundary": GENERATED_METRIC_CONTRACT_BOUNDARY,
        "metric_gate_policy_mode": metric_gate_policy_mode,
        "execution_smoke_passed": execution_smoke_passed,
        "metric_gate_errors": metric_gate_errors,
        "smoke_passed": smoke_passed,
        "promotion_ready": False,
        "boundary": boundary,
    }
    tool_call = ToolCallRecord(
        tool_name=(
            f"{language}.generated_algorithm_sandbox"
            if execution is not None and execution.execution_attempted
            else f"{language}.generated_sandbox_precheck"
        ),
        inputs={
            "replicates": replicates,
            "seed": seed,
            "script_path": script_path,
            "entrypoint": "run_sandbox",
            "language": language,
            "execution_profile": requested_profile,
            "dependencies": list(dependencies),
            "bound_estimator_code_hashes": expected_estimator_code_hashes,
            "required_callable_exports": [
                str(value) for value in required_callable_exports
            ],
        },
        output_paths=tuple(
            path
            for path in (request_path, execution_envelope_path, result_path)
            if path
        ),
        input_hash=stable_hash(
            {
                "code": code,
                "replicates": replicates,
                "seed": seed,
                "language": language,
                "dependencies": list(dependencies),
                "bound_estimator_code_hashes": expected_estimator_code_hashes,
                "required_callable_exports": [
                    str(value) for value in required_callable_exports
                ],
            }
        ),
        output_hash=stable_hash(metrics) if metrics else "",
        exit_status=(
            str(returncode)
            if execution is not None and execution.execution_attempted
            else "rejected"
            if prototype_status == "REJECTED_UNSAFE_GENERATED_CODE"
            else "blocked"
        ),
        stdout_summary=stdout_summary,
        stderr_summary=stderr_summary,
        safety_boundary=boundary,
    )
    return prototype, tool_call


def _metrics_are_finite(metrics: Mapping[str, Any]) -> bool:
    for value in metrics.values():
        if isinstance(value, bool) or value is None or isinstance(value, str):
            continue
        if isinstance(value, int):
            continue
        if isinstance(value, float):
            if not math.isfinite(value):
                return False
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    if not math.isfinite(float(item)):
                        return False
            continue
        if isinstance(value, Mapping):
            if not _metrics_are_finite(value):
                return False
            continue
    return True


def _question_to_payload(question: OpenResearchQuestion) -> dict[str, Any]:
    return {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }


def _question_primary_task_family(question: OpenResearchQuestion) -> str:
    return primary_task_family_from_question(question)


def _runtime_task_prompt_summary(task: AgentTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "owner_subsystem": task.owner_subsystem,
        "objective": task.objective,
        "allowed_tools": list(task.allowed_tools),
        "expected_artifacts": list(task.expected_artifacts),
        "acceptance_gate": task.acceptance_gate,
        "stop_condition": task.stop_condition,
    }


def _question_from_payload(payload: Mapping[str, Any]) -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id=str(payload["id"]),
        title=str(payload.get("title", payload["id"])),
        description=str(payload["description"]),
        tags=tuple(str(row) for row in payload.get("tags", ()) or ()),
    )


def _research_problem_from_payload(payload: Mapping[str, Any]) -> ResearchProblemSpec:
    return ResearchProblemSpec(
        question_id=str(payload.get("question_id", "") or ""),
        problem_class=str(payload.get("problem_class", "") or "custom_formalization_eval"),
        dgp=str(payload.get("dgp", "") or ""),
        estimand=str(payload.get("estimand", "") or ""),
        assumptions=tuple(str(row) for row in payload.get("assumptions", []) or []),
        asymptotic_regime=str(payload.get("asymptotic_regime", "") or ""),
        diagnostics=tuple(str(row) for row in payload.get("diagnostics", []) or []),
        stress_tests=tuple(str(row) for row in payload.get("stress_tests", []) or []),
        extraction_evidence=dict(payload.get("extraction_evidence", {}) or {}),
    )


def _theorem_goal_from_payload(payload: Mapping[str, Any]) -> TheoremGoal:
    return TheoremGoal(
        id=str(payload.get("id", "") or ""),
        title=str(payload.get("title", "") or payload.get("id", "") or ""),
        informal_statement=str(
            payload.get("informal_statement", "")
            or payload.get("claim", "")
            or payload.get("statement", "")
            or ""
        ),
        proof_strategy=str(payload.get("proof_strategy", "") or ""),
        status=(
            "PROVABLE_NOW"
            if str(payload.get("status", "") or "") == "PROVABLE_NOW"
            else "FORMAL_GAP"
        ),
        required_primitives=tuple(
            str(row) for row in payload.get("required_primitives", []) or []
        ),
        proof_obligations=tuple(
            str(row) for row in payload.get("proof_obligations", []) or []
        ),
    )


def _formalization_runtime_problem_and_goals(
    question: OpenResearchQuestion,
    task_inputs: Mapping[str, Any],
) -> tuple[ResearchProblemSpec, list[TheoremGoal], dict[str, Any]]:
    problem_override = task_inputs.get("registered_problem_override", {})
    goals_override = task_inputs.get("theorem_goals_override", [])
    if isinstance(problem_override, Mapping) and isinstance(goals_override, list):
        goals = [
            _theorem_goal_from_payload(row)
            for row in goals_override
            if isinstance(row, Mapping)
        ]
        if goals:
            problem = _research_problem_from_payload(
                {
                    "question_id": question.id,
                    **dict(problem_override),
                }
            )
            return problem, goals, {
                "problem_formalization_source": "explicit_runtime_override",
                "theorem_goal_source": "explicit_runtime_override",
                "legacy_problem_formalizer_used": False,
                "legacy_theory_planner_used": False,
                "legacy_baseline_skipped_reason": (
                    "Explicit typed runtime overrides were supplied."
                ),
            }
    architect_context = (
        dict(task_inputs.get("architect_context", {}) or {})
        if isinstance(task_inputs.get("architect_context", {}), Mapping)
        else {}
    )
    if runtime_llm_research_authority_required(architect_context):
        bundle = derive_runtime_research_problem(
            question=question,
            architect_context=architect_context,
        )
        return bundle.problem, list(bundle.theorem_goals), bundle.provenance()
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    return (
        problem,
        theorem_goals,
        legacy_runtime_research_problem_provenance(),
    )


def _problem_to_json(problem: ResearchProblemSpec) -> dict[str, Any]:
    row = asdict(problem)
    row["assumptions"] = list(problem.assumptions)
    row["diagnostics"] = list(problem.diagnostics)
    row["stress_tests"] = list(problem.stress_tests)
    return row


def _procedure_to_json(procedure: CandidateProcedure) -> dict[str, Any]:
    return asdict(procedure)


def _theorem_goal_to_json(goal: TheoremGoal) -> dict[str, Any]:
    return asdict(goal)


def _simulation_to_json(simulation: ResearchSimulation) -> dict[str, Any]:
    return asdict(simulation)


def _formal_subclaim_to_json(subclaim: FormalSubclaim) -> dict[str, Any]:
    return asdict(subclaim)


def _safe_identifier(raw: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", raw.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "question"


def _write_jsonl(path: Path, rows: Sequence[Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")








def _append_jsonl_row(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")
        handle.flush()
