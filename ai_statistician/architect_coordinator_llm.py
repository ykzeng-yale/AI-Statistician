from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .agent_runtime import agent_runtime_substage

from .architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY,
    ArchitectMetricSemanticReviewerConfig,
    LLMArchitectMetricSemanticReviewerAgent,
)
from .architect_metric_contract_authoring import (
    ArchitectMetricContractAuthoringConfig,
    author_reviewed_architect_metric_requirements,
    review_architect_theory_execution_preflight,
)
from .fingerprint import stable_hash
from .generated_metric_contract import (
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED,
    GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS,
    generated_metric_requirement_set_id,
    generated_sandbox_runtime_replicates,
    validate_generated_metric_requirements,
)
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PHASE_NOT_REQUIRED,
    METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED,
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
    METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING,
    METRIC_PROTOCOL_PHASES,
    metric_protocol_authority_matches_theory,
    theory_informed_metric_protocol_material,
)
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion
from .semantic_review_feedback import (
    architect_observations_without_runtime_routing,
)


ARCHITECT_COORDINATOR_SCHEMA_VERSION = 1
ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE = "LLM_ARCHITECT_COORDINATOR_PROPOSAL_NOT_PROOF_EVIDENCE"
ARCHITECT_COORDINATOR_BOUNDARY = (
    "LLM ArchitectCoordinator packets are orchestration proposals only. They "
    "can choose subsystem order, evidence gates, retrieval priorities, and "
    "iteration policy, but they do not execute tools, validate simulations, "
    "or prove theorems. Runtime validators and AXLE/local Lean remain the "
    "authority gates."
)
ARCHITECT_CAPABILITY_GAP_ROUTING_BOUNDARY = (
    "Runtime capability-gap routing is Architect orchestration input only. "
    "It may prioritize subsystem work and capability-eval reruns, but it is "
    "not proof evidence, simulation evidence, generated-code evidence, or "
    "verifier evidence."
)
ARCHITECT_RUNTIME_SUBSYSTEMS = (
    "RetrievalMemory",
    "TheoryDeveloper",
    "SimulationEvaluator",
    "AlgorithmEngineer",
    "GeneratedCodeSemanticReviewer",
    "FormalTargetSemanticReviewer",
    "FormalizationEvaluator",
    "TheoremReductionClosureProofEngineer",
    "ExactSourceTheoremProofBodyExecutor",
    "SourceSemanticProofEngineer",
    "PseudoFormalBlockVerifier",
    "SourceTheoremPromotionProofEngineer",
    "ProofEngineer",
    "ExactSourceTheoremProver",
    "FormalizationGapPlanner",
    "CriticEvaluator",
)
RESEARCH_EVALUATION_MODES = frozenset({"research_eval", "capability_eval"})
RESEARCH_EVAL_FORBIDDEN_FORMAL_SUBSYSTEMS = frozenset(
    {
        "FormalTargetSemanticReviewer",
        "FormalizationEvaluator",
        "TheoremReductionClosureProofEngineer",
        "ExactSourceTheoremProofBodyExecutor",
        "SourceSemanticProofEngineer",
        "PseudoFormalBlockVerifier",
        "SourceTheoremPromotionProofEngineer",
        "ProofEngineer",
        "ExactSourceTheoremProver",
        "FormalizationGapPlanner",
    }
)
ARCHITECT_REUSABLE_VALIDATED_PLAN_FIELDS = (
    "intake_assessment",
    "problem_analysis",
    "stat_knowledge_bank_plan",
    "literature_fair_comparison_plan",
    "evidence_contract",
    "subsystem_execution_plan",
    "retrieval_strategy",
    "iteration_policy",
    "evidence_gates",
    "risk_register",
    "next_actions",
)
ARCHITECT_VALIDATED_PLAN_REUSE_METADATA_KIND = (
    "ArchitectValidatedPlanReuseMetadata"
)
ARCHITECT_REUSE_RUNTIME_METRIC_LIFECYCLE_FIELDS = frozenset(
    {
        "empirical_metric_requirements",
        "empirical_metric_requirement_set_id",
        "empirical_metric_protocol_phase",
        "metric_protocol_execution_authorized",
        "empirical_metric_requirements_preexecution_review",
        "empirical_metric_requirements_frozen_from_prior_architect_plan",
        "empirical_metric_requirements_frozen_from_metric_planner",
    }
)


def _research_evaluation_contract_flag(
    evidence_contract: Mapping[str, Any],
    requirement: str,
) -> bool:
    canonical = f"research_evaluation_requires_{requirement}"
    legacy = f"capability_eval_requires_{requirement}"
    value = evidence_contract.get(canonical)
    if isinstance(value, bool):
        return value
    return evidence_contract.get(legacy) is True

LONG_HORIZON_RESEARCH_GUIDANCE: dict[str, Any] = {
    "problem_analysis_before_retrieval": [
        "classify theorem family, statistical object, likely analogy class, and key obstacle before choosing searches",
        "separate missing mathematical insight from missing implementation, simulation, or formal-library support",
    ],
    "dynamic_stat_knowledge_bank": [
        "record similar theorem families, source refs, assumption matches, assumption mismatches, proof skeletons, and failed attempts",
        "treat the knowledge bank as prompt memory and routing evidence, not proof evidence",
    ],
    "literature_fair_comparison_gate": [
        "for every borrowed theorem family, state matched DGP/estimand/regime pieces and mismatched or unsafe-transfer pieces",
        "do not let embedding/RAG similarity substitute for semantic compatibility",
    ],
    "proposer_verifier_iteration": [
        "let proposer agents draft derivations and routes, then route verifier/critic objections back into the next theory pass",
        "only Lean/AXLE/local kernel rows can promote theorem proof claims",
    ],
}

ARCHITECT_FORMAL_TARGET_AUTHORING_CONTRACT: dict[str, Any] = {
    "content_owner": "ArchitectCoordinator",
    "required_content": [
        "task-specific mathematical object or estimand",
        "assumptions and quantification needed to state the claim",
        "mathematical conclusion to retrieve, derive, and formalize",
    ],
    "forbidden_substitutes": [
        "proof-completion policy",
        "kernel-verification status",
        "generic evidence-gate prose",
    ],
    "initial_plan_rule": (
        "author the mathematical target from the research question and current "
        "theory analysis; runtime owns only how completion is verified"
    ),
    "replan_rule": (
        "preserve formal_targets from the first accepted Architect plan unless an "
        "explicit fresh evaluation protocol replaces the research target"
    ),
}

_LEGACY_RUNTIME_FORMAL_TARGET_PLACEHOLDERS = frozenset(
    {
        "source theorem or required subclaims kernel verified",
        "formalize high-value kernels when feasible",
    }
)


def architect_formal_target_is_completion_placeholder(value: Any) -> bool:
    """Identify legacy runtime policies that were incorrectly stored as targets."""

    return str(value or "").strip().lower() in (
        _LEGACY_RUNTIME_FORMAL_TARGET_PLACEHOLDERS
    )


@dataclass(frozen=True)
class ArchitectCoordinatorConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 5000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 2
    metric_semantic_reviewer_model: str = ""
    metric_semantic_reviewer_model_tier: str = "sonnet"
    metric_semantic_reviewer_max_tokens: int = 7000
    metric_semantic_reviewer_max_revisions: int = 2


class LLMArchitectCoordinatorAgent:
    """Generator-backed top-level Architect/Coordinator proposal worker."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: ArchitectCoordinatorConfig = ArchitectCoordinatorConfig(),
        metric_semantic_reviewer: (
            LLMArchitectMetricSemanticReviewerAgent | None
        ) = None,
        preflight_source_retriever: Any = None,
    ) -> None:
        self.provider = provider
        self.config = config
        self.metric_semantic_reviewer = metric_semantic_reviewer
        if (
            self.metric_semantic_reviewer is None
            and str(config.provider_name or "").strip().lower() == "anthropic"
        ):
            self.metric_semantic_reviewer = (
                LLMArchitectMetricSemanticReviewerAgent(
                    provider=provider,
                    config=ArchitectMetricSemanticReviewerConfig(
                        model=config.metric_semantic_reviewer_model,
                        model_tier=config.metric_semantic_reviewer_model_tier,
                        max_tokens=config.metric_semantic_reviewer_max_tokens,
                        temperature=0.0,
                        provider_name=config.provider_name,
                    ),
                    source_retriever=preflight_source_retriever,
                )
            )

    def review_theory_execution_preflight(
        self,
        *,
        question: OpenResearchQuestion,
        architect_context: Mapping[str, Any],
        runtime_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Run the independent pre-code gate without authoring metrics."""

        return review_architect_theory_execution_preflight(
            semantic_reviewer=self.metric_semantic_reviewer,
            question=question,
            runtime_contract=_architect_runtime_owned_evidence_contract(
                architect_context=architect_context,
                runtime_config=runtime_config,
            ),
            theory_protocol_material=(
                theory_informed_metric_protocol_material(architect_context)
            ),
            prior_rejection_context=(
                architect_context.get(
                    "architect_metric_protocol_prior_rejection", {}
                )
                if isinstance(
                    architect_context.get(
                        "architect_metric_protocol_prior_rejection", {}
                    ),
                    Mapping,
                )
                else {}
            ),
        )

    def propose(
        self,
        *,
        question: OpenResearchQuestion,
        architect_context: Mapping[str, Any],
        runtime_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        metric_authoring_packet: dict[str, Any] = {}
        if not _architect_metric_authoring_deferred_for_active_replan(
            architect_context
        ):
            metric_authoring_packet = author_reviewed_architect_metric_requirements(
                provider=self.provider,
                config=ArchitectMetricContractAuthoringConfig(
                    max_tokens=self.config.max_tokens,
                    model_tier=self.config.model_tier,
                    provider_name=self.config.provider_name,
                    max_repair_attempts=self.config.max_repair_attempts,
                    metric_semantic_reviewer_max_revisions=(
                        self.config.metric_semantic_reviewer_max_revisions
                    ),
                ),
                request_model=request_model,
                semantic_reviewer=self.metric_semantic_reviewer,
                question=question,
                runtime_contract=_architect_runtime_owned_evidence_contract(
                    architect_context=architect_context,
                    runtime_config=runtime_config,
                ),
                theory_protocol_material=(
                    theory_informed_metric_protocol_material(architect_context)
                ),
                prior_rejection_context=(
                    architect_context.get(
                        "architect_metric_protocol_prior_rejection", {}
                    )
                    if isinstance(
                        architect_context.get(
                            "architect_metric_protocol_prior_rejection", {}
                        ),
                        Mapping,
                    )
                    else {}
                ),
                fresh_candidate_revision_context=(
                    architect_context.get(
                        "architect_metric_protocol_fresh_candidate_revision", {}
                    )
                    if isinstance(
                        architect_context.get(
                            "architect_metric_protocol_fresh_candidate_revision",
                            {},
                        ),
                        Mapping,
                    )
                    else {}
                ),
                frozen_requirement_rebinding_context=(
                    _architect_frozen_metric_protocol_rebinding_context(
                        architect_context
                    )
                ),
                accepted_theory_preflight_context=(
                    architect_context.get(
                        "architect_theory_execution_preflight_acceptance", {}
                    )
                    if isinstance(
                        architect_context.get(
                            "architect_theory_execution_preflight_acceptance", {}
                        ),
                        Mapping,
                    )
                    else {}
                ),
                accepted_implementation_interface_context=(
                    architect_context.get(
                        "accepted_implementation_interface_handoff", {}
                    )
                    if isinstance(
                        architect_context.get(
                            "accepted_implementation_interface_handoff", {}
                        ),
                        Mapping,
                    )
                    else {}
                ),
            )
        effective_architect_context = (
            _architect_context_with_metric_requirement_authoring(
                architect_context,
                metric_authoring_packet,
            )
        )
        reused_packet = _architect_packet_from_validated_plan_reuse(
            question=question,
            architect_context=effective_architect_context,
            runtime_config=runtime_config,
            metric_authoring_packet=metric_authoring_packet,
        )
        if reused_packet is not None:
            with agent_runtime_substage(
                "architect_plan_reuse",
                metadata={
                    "fresh_architect_plan_model_invocation": False,
                    "metric_protocol_authored": True,
                    "source_architect_packet_id": reused_packet[
                        "validated_plan_reuse_provenance"
                    ]["source_architect_packet_id"],
                },
            ):
                return reused_packet
        user_prompt = build_architect_coordinator_prompt(
            question=question,
            architect_context=effective_architect_context,
            runtime_config=runtime_config,
        )
        request = GeneratorRequest(
            system_prompt=ARCHITECT_COORDINATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=ARCHITECT_COORDINATOR_JSON_SCHEMA,
            metadata={
                "subsystem": "ArchitectCoordinator",
                "agent": "LLMArchitectCoordinatorAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
                "provider_structured_output": True,
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            packet = _normalize_architect_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
                runtime_config=runtime_config,
                architect_context=effective_architect_context,
            )
            if metric_authoring_packet:
                packet["metric_requirement_authoring"] = (
                    _architect_metric_requirement_authoring_summary(
                        metric_authoring_packet
                    )
                )
            return packet

        with agent_runtime_substage(
            "architect_plan_generation",
            metadata={
                "model_tier": self.config.model_tier,
                "max_packet_regeneration_attempts": self.config.max_repair_attempts,
                "metric_protocol_authored": bool(metric_authoring_packet),
            },
        ):
            return generate_validated_json_packet(
                provider=self.provider,
                request=request,
                extract_payload=_extract_json_object,
                build_packet=build_packet,
                validate_packet=validate_architect_coordinator_packet,
                validation_label="LLM ArchitectCoordinator packet",
                max_repair_attempts=self.config.max_repair_attempts,
            )


def architect_validated_plan_reuse_metadata(
    packet: Mapping[str, Any],
    *,
    question_id: str,
) -> dict[str, Any]:
    plan_projection = _architect_reusable_validated_plan_projection(packet)
    return {
        "artifact_kind": ARCHITECT_VALIDATED_PLAN_REUSE_METADATA_KIND,
        "question_id": question_id,
        "source_architect_packet_id": str(packet.get("packet_id", "") or ""),
        "source_architect_packet_hash": stable_hash(packet),
        "source_architect_model": str(packet.get("model", "") or ""),
        "source_architect_model_tier": str(
            packet.get("model_tier", "") or ""
        ),
        "source_architect_provider": str(packet.get("provider", "") or ""),
        "validated_plan_fingerprint": stable_hash(plan_projection),
        "fresh_architect_plan_model_invocation_required_after_metric_review": (
            False
        ),
        "runtime_may_generate_research_content": False,
        "proof_evidence_status": (
            "ARCHITECT_VALIDATED_PLAN_REUSE_METADATA_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "This metadata permits reuse only of an already validated, hash-bound "
            "LLM Architect plan. Runtime may attach a separately authored and "
            "independently accepted metric protocol, but may not create or revise "
            "research semantics."
        ),
    }


def _architect_packet_from_validated_plan_reuse(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    runtime_config: Mapping[str, Any],
    metric_authoring_packet: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not metric_authoring_packet:
        return None
    authoring_summary = architect_context.get(
        "architect_metric_requirement_authoring", {}
    )
    if not (
        isinstance(authoring_summary, Mapping)
        and authoring_summary.get("semantic_review_status") == "ACCEPT"
        and authoring_summary.get("semantic_review_independent_agent") is True
        and authoring_summary.get("semantic_review_independent_invocation") is True
        and str(authoring_summary.get("source_theory_packet_id", "") or "")
        and str(authoring_summary.get("source_theory_packet_hash", "") or "")
        and theory_informed_metric_protocol_material(architect_context)
    ):
        return None
    prior_plan = architect_context.get("architect_runtime_plan", {})
    prior_plan = prior_plan if isinstance(prior_plan, Mapping) else {}
    reuse_metadata = prior_plan.get("validated_plan_reuse_metadata", {})
    if not (
        isinstance(reuse_metadata, Mapping)
        and reuse_metadata.get("artifact_kind")
        == ARCHITECT_VALIDATED_PLAN_REUSE_METADATA_KIND
        and str(reuse_metadata.get("question_id", "") or "") == question.id
        and str(
            reuse_metadata.get("source_architect_packet_id", "") or ""
        )
        and str(
            reuse_metadata.get("source_architect_packet_hash", "") or ""
        )
    ):
        return None
    plan_projection = _architect_reusable_validated_plan_projection(prior_plan)
    if (
        any(value in (None, "", [], {}) for value in plan_projection.values())
        or stable_hash(plan_projection)
        != str(reuse_metadata.get("validated_plan_fingerprint", "") or "")
    ):
        return None
    plan_projection["subsystem_execution_plan"] = [
        deepcopy(dict(row)) if isinstance(row, Mapping) else deepcopy(row)
        for row in plan_projection["subsystem_execution_plan"]
        if not (
            isinstance(row, Mapping)
            and row.get("llm_authored") is False
            and row.get("runtime_defaults_required") is True
        )
    ]
    source_model = str(
        reuse_metadata.get("source_architect_model", "") or ""
    )
    source_model_tier = str(
        reuse_metadata.get("source_architect_model_tier", "") or ""
    )
    source_provider = str(
        reuse_metadata.get("source_architect_provider", "") or ""
    )
    if not all((source_model, source_model_tier, source_provider)):
        return None
    packet = _normalize_architect_packet(
        plan_projection,
        question=question,
        model=source_model,
        model_tier=source_model_tier,
        provider_name=source_provider,
        raw_response=(
            "validated-plan-reuse:"
            + str(reuse_metadata["source_architect_packet_id"])
        ),
        runtime_config=runtime_config,
        architect_context=architect_context,
    )
    packet["metric_requirement_authoring"] = (
        _architect_metric_requirement_authoring_summary(
            metric_authoring_packet
        )
    )
    packet["plan_generation_mode"] = (
        "validated_plan_reuse_with_independent_metric_attachment"
    )
    packet["fresh_architect_plan_model_invocation"] = False
    packet["validated_plan_reuse_provenance"] = {
        "artifact_kind": "ArchitectValidatedPlanReuseProvenance",
        "source_architect_packet_id": str(
            reuse_metadata["source_architect_packet_id"]
        ),
        "source_architect_packet_hash": str(
            reuse_metadata["source_architect_packet_hash"]
        ),
        "validated_plan_fingerprint": str(
            reuse_metadata["validated_plan_fingerprint"]
        ),
        "metric_authoring_packet_id": str(
            metric_authoring_packet.get("packet_id", "") or ""
        ),
        "metric_authoring_packet_hash": stable_hash(metric_authoring_packet),
        "semantic_review_packet_id": str(
            authoring_summary.get("semantic_review_packet_id", "") or ""
        ),
        "semantic_review_packet_hash": str(
            authoring_summary.get("semantic_review_packet_hash", "") or ""
        ),
        "fresh_architect_plan_model_invocation": False,
        "runtime_only_attachment": True,
        "runtime_may_generate_research_content": False,
        "proof_evidence_status": (
            "ARCHITECT_VALIDATED_PLAN_REUSE_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "The statistical plan is reused byte-for-structure from a validated "
            "LLM Architect packet. Runtime only attaches the current theory-bound "
            "metric protocol after independent acceptance; this is orchestration "
            "provenance, not execution or proof evidence."
        ),
    }
    if validate_architect_coordinator_packet(packet):
        return None
    return packet


def _architect_reusable_validated_plan_projection(
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Fingerprint research semantics without runtime-owned metric lifecycle state."""

    projection = {
        field: deepcopy(plan.get(field))
        for field in ARCHITECT_REUSABLE_VALIDATED_PLAN_FIELDS
    }
    contract = projection.get("evidence_contract", {})
    if isinstance(contract, Mapping):
        stable_contract = deepcopy(dict(contract))
        for field in ARCHITECT_REUSE_RUNTIME_METRIC_LIFECYCLE_FIELDS:
            stable_contract.pop(field, None)
        projection["evidence_contract"] = stable_contract
    return projection


def _architect_metric_authoring_deferred_for_active_replan(
    architect_context: Mapping[str, Any],
) -> bool:
    """Keep metric planning from intercepting an unrelated feedback turn."""

    code_replan = architect_context.get(
        "runtime_generated_code_semantic_review_replan", {}
    )
    if isinstance(code_replan, Mapping) and code_replan:
        resolution = architect_context.get(
            "runtime_generated_code_semantic_review_replan_resolution", {}
        )
        if _generated_code_semantic_review_replan_is_resolved(
            replan=code_replan,
            resolution=resolution,
        ):
            return False
        return True
    packet_replan = architect_context.get("runtime_packet_validation_replan", {})
    return bool(isinstance(packet_replan, Mapping) and packet_replan)


def _generated_code_semantic_review_replan_is_resolved(
    *,
    replan: Mapping[str, Any],
    resolution: Any,
) -> bool:
    if not isinstance(resolution, Mapping):
        return False
    rejected_manifest_id = str(
        replan.get("source_manifest_id", "")
        or ""
    )
    rejected_subsystem = str(
        replan.get("source_subsystem", "")
        or ""
    )
    return bool(
        resolution.get("resolution_status")
        == "SUPERSEDED_BY_FRESH_ACCEPTED_ARTIFACT"
        and rejected_manifest_id
        and resolution.get("rejected_source_manifest_id")
        == rejected_manifest_id
        and resolution.get("rejected_source_subsystem") == rejected_subsystem
        and str(resolution.get("accepted_source_manifest_id", "") or "")
        and resolution.get("accepted_source_manifest_id")
        != rejected_manifest_id
        and str(resolution.get("accepted_review_execution_id", "") or "")
    )


def _architect_frozen_metric_protocol_rebinding_context(
    architect_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Carry a frozen gate portfolio across an upstream theory revision."""

    theory_material = theory_informed_metric_protocol_material(
        architect_context
    )
    if not theory_material:
        return {}
    current_theory_packet_id = str(
        theory_material.get("source_theory_packet_id", "") or ""
    )
    current_theory_packet_hash = str(
        theory_material.get("source_theory_packet_hash", "") or ""
    )
    resolution = architect_context.get(
        "runtime_generated_code_semantic_review_replan_resolution", {}
    )
    invalidation = architect_context.get(
        "architect_metric_protocol_authority_invalidation", {}
    )
    routing = architect_context.get("architect_initial_routing", {})
    architect_packet_id = str(
        architect_context.get("architect_coordinator_proposal_id", "") or ""
    )
    if not (
        isinstance(resolution, Mapping)
        and resolution.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewReplanResolution"
        and resolution.get("resolution_status")
        == "CONSUMED_BY_FRESH_THEORY_REVISION"
        and resolution.get("requires_fresh_metric_protocol_review") is True
        and str(resolution.get("revised_theory_packet_id", "") or "")
        == current_theory_packet_id
        and str(resolution.get("revised_theory_packet_hash", "") or "")
        == current_theory_packet_hash
        and isinstance(invalidation, Mapping)
        and invalidation.get("artifact_kind")
        == "RuntimeMetricProtocolTheoryLineageInvalidation"
        and str(
            invalidation.get("current_source_theory_packet_id", "") or ""
        )
        == current_theory_packet_id
        and str(
            invalidation.get("current_source_theory_packet_hash", "") or ""
        )
        == current_theory_packet_hash
        and architect_packet_id
        and str(resolution.get("architect_packet_id", "") or "")
        == architect_packet_id
        and isinstance(routing, Mapping)
        and routing.get("artifact_kind") == "ArchitectInitialRoutingDecision"
        and routing.get("source") == "architect_packet"
        and routing.get("requested_subsystem") == "TheoryDeveloper"
        and routing.get("selected_subsystem") == "TheoryDeveloper"
        and str(routing.get("architect_packet_id", "") or "")
        == architect_packet_id
        and str(routing.get("environment_feedback_execution_id", "") or "")
        == str(resolution.get("rejected_review_execution_id", "") or "")
    ):
        return {}

    prior_plan = architect_context.get("architect_runtime_plan", {})
    prior_contract = (
        prior_plan.get("evidence_contract", {})
        if isinstance(prior_plan, Mapping)
        else {}
    )
    if not isinstance(prior_contract, Mapping):
        return {}
    requirements = prior_contract.get("empirical_metric_requirements", [])
    prior_review = prior_contract.get(
        "empirical_metric_requirements_preexecution_review", {}
    )
    source_requirement_set_id = str(
        prior_contract.get("empirical_metric_requirement_set_id", "") or ""
    )
    prior_theory_packet_id = str(
        resolution.get("prior_theory_packet_id", "") or ""
    )
    if not (
        isinstance(requirements, list)
        and requirements
        and all(isinstance(row, Mapping) for row in requirements)
        and isinstance(prior_review, Mapping)
        and prior_review.get("overall_verdict") == "ACCEPT"
        and prior_review.get("independent_agent") is True
        and prior_review.get("independent_invocation") is True
        and prior_review.get("execution_results_observed") is False
        and str(prior_review.get("source_theory_packet_id", "") or "")
        == prior_theory_packet_id
        and str(
            prior_review.get(
                "reviewed_empirical_metric_requirement_set_id", ""
            )
            or ""
        )
        == source_requirement_set_id
        and generated_metric_requirement_set_id(
            [
                dict(row)
                for row in requirements
                if isinstance(row, Mapping)
            ]
        )
        == source_requirement_set_id
        and source_requirement_set_id
    ):
        return {}

    source_requirement_rows = [
        dict(row) for row in requirements if isinstance(row, Mapping)
    ]
    allowed_mutable_requirement_fields = [
        "source_anchors",
        "acceptance_authority_rationale",
    ]
    if any(
        "gate_field_authorities" in row
        for row in source_requirement_rows
    ):
        allowed_mutable_requirement_fields.append(
            "gate_field_authorities"
        )

    return {
        "schema_version": 1,
        "artifact_kind": "RuntimeFrozenMetricProtocolTheoryRebindingContext",
        "source_requirement_set_id": source_requirement_set_id,
        "source_requirement_rows": source_requirement_rows,
        "prior_review_packet_id": str(
            prior_review.get("review_packet_id", "") or ""
        ),
        "prior_source_theory_packet_id": prior_theory_packet_id,
        "prior_source_theory_packet_hash": str(
            prior_review.get("source_theory_packet_hash", "") or ""
        ),
        "current_source_theory_packet_id": current_theory_packet_id,
        "current_source_theory_packet_hash": current_theory_packet_hash,
        "source_review_execution_id": str(
            resolution.get("rejected_review_execution_id", "") or ""
        ),
        "raw_execution_artifacts_included": False,
        "post_result_gate_changes_allowed": False,
        "allowed_mutable_requirement_fields": (
            allowed_mutable_requirement_fields
        ),
        "proof_evidence_status": (
            "FROZEN_METRIC_PROTOCOL_THEORY_REBINDING_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "The exact accepted empirical gate portfolio remains frozen after "
            "execution. A revised theory may only rebind exact source anchors and "
            "their explanatory rationale, including field-level gate authority "
            "bindings when present, before a fresh independent review; it cannot "
            "add, remove, relax, or reinterpret a gate or change any field's "
            "authority kind."
        ),
    }


def _architect_theory_execution_preflight_summary(
    metric_authoring_packet: Mapping[str, Any],
) -> dict[str, Any]:
    preflight = metric_authoring_packet.get(
        "theory_execution_preflight_packet", {}
    )
    if not isinstance(preflight, Mapping) or not preflight:
        return {}
    return {
        "packet_id": str(preflight.get("packet_id", "") or ""),
        "packet_hash": str(
            metric_authoring_packet.get(
                "theory_execution_preflight_packet_hash", ""
            )
            or ""
        ),
        "source_theory_packet_id": str(
            preflight.get("source_theory_packet_id", "") or ""
        ),
        "source_theory_packet_hash": str(
            preflight.get("source_theory_packet_hash", "") or ""
        ),
        "overall_verdict": str(preflight.get("overall_verdict", "") or ""),
        "model": str(preflight.get("model", "") or ""),
        "model_tier": str(preflight.get("model_tier", "") or ""),
        "llm_json_repair_attempts": int(
            preflight.get("llm_json_repair_attempts", 0) or 0
        ),
        "n_findings": len(preflight.get("findings", []) or []),
        "proof_evidence_status": str(
            preflight.get("proof_evidence_status", "") or ""
        ),
        "boundary": str(preflight.get("boundary", "") or ""),
    }


def _architect_context_with_metric_requirement_authoring(
    architect_context: Mapping[str, Any],
    metric_authoring_packet: Mapping[str, Any],
) -> dict[str, Any]:
    context = dict(architect_context)
    if metric_authoring_packet:
        semantic_review = metric_authoring_packet.get(
            "semantic_review_packet", {}
        )
        if not isinstance(semantic_review, Mapping):
            semantic_review = {}
        context["architect_metric_requirement_authoring"] = {
            "artifact_kind": str(
                metric_authoring_packet.get("artifact_kind", "") or ""
            ),
            "packet_id": str(metric_authoring_packet.get("packet_id", "") or ""),
            "source_theory_packet_id": str(
                metric_authoring_packet.get("source_theory_packet_id", "") or ""
            ),
            "source_theory_packet_hash": str(
                metric_authoring_packet.get("source_theory_packet_hash", "") or ""
            ),
            "empirical_metric_requirements": [
                dict(row)
                for row in metric_authoring_packet.get(
                    "empirical_metric_requirements", []
                )
                if isinstance(row, Mapping)
            ],
            "empirical_metric_requirement_set_id": str(
                metric_authoring_packet.get(
                    "empirical_metric_requirement_set_id", ""
                )
                or ""
            ),
            "runtime_owned_requirement_bindings": dict(
                metric_authoring_packet.get(
                    "runtime_owned_requirement_bindings", {}
                )
            )
            if isinstance(
                metric_authoring_packet.get(
                    "runtime_owned_requirement_bindings"
                ),
                Mapping,
            )
            else {},
            "theory_execution_preflight": (
                _architect_theory_execution_preflight_summary(
                    metric_authoring_packet
                )
            ),
            "semantic_review_status": str(
                metric_authoring_packet.get("semantic_review_status", "") or ""
            ),
            "semantic_review_packet_id": str(
                semantic_review.get("packet_id", "") or ""
            ),
            "semantic_review_packet_hash": str(
                metric_authoring_packet.get("semantic_review_packet_hash", "")
                or ""
            ),
            "semantic_review_model": str(
                semantic_review.get("model", "") or ""
            ),
            "semantic_review_model_tier": str(
                semantic_review.get("model_tier", "") or ""
            ),
            "semantic_review_independent_agent": bool(
                semantic_review.get("independent_agent")
            ),
            "semantic_review_independent_invocation": bool(
                semantic_review.get("independent_invocation")
            ),
            "semantic_review_independent_model": bool(
                semantic_review.get("independent_model")
            ),
            "semantic_review_independent_model_tier": bool(
                semantic_review.get("independent_model_tier")
            ),
            "cumulative_finding_ledger": [
                dict(row)
                for row in metric_authoring_packet.get(
                    "cumulative_finding_ledger", []
                )
                or []
                if isinstance(row, Mapping)
            ],
            "cumulative_finding_ledger_fingerprint": str(
                metric_authoring_packet.get(
                    "cumulative_finding_ledger_fingerprint", ""
                )
                or ""
            ),
            "frozen_metric_protocol_rebinding": bool(
                metric_authoring_packet.get(
                    "frozen_metric_protocol_rebinding"
                )
            ),
            "frozen_source_requirement_set_id": str(
                metric_authoring_packet.get(
                    "frozen_source_requirement_set_id", ""
                )
                or ""
            ),
            "frozen_gate_semantics_preserved": bool(
                metric_authoring_packet.get(
                    "frozen_gate_semantics_preserved"
                )
            ),
            "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
        }
    return context


def _architect_metric_requirement_authoring_summary(
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    history = packet.get("llm_json_repair_history", [])
    last_history = (
        history[-1]
        if isinstance(history, list)
        and history
        and isinstance(history[-1], Mapping)
        else {}
    )
    response_metadata = (
        last_history.get("response_metadata", {})
        if isinstance(last_history, Mapping)
        else {}
    )
    if not isinstance(response_metadata, Mapping):
        response_metadata = {}
    semantic_review = packet.get("semantic_review_packet", {})
    if not isinstance(semantic_review, Mapping):
        semantic_review = {}
    review_history = packet.get("semantic_review_history", [])
    if not isinstance(review_history, list):
        review_history = []
    return {
        "artifact_kind": str(packet.get("artifact_kind", "") or ""),
        "packet_id": str(packet.get("packet_id", "") or ""),
        "source_theory_packet_id": str(
            packet.get("source_theory_packet_id", "") or ""
        ),
        "source_theory_packet_hash": str(
            packet.get("source_theory_packet_hash", "") or ""
        ),
        "provider_name": str(packet.get("provider_name", "") or ""),
        "model": str(packet.get("model", "") or ""),
        "model_tier": str(packet.get("model_tier", "") or ""),
        "empirical_metric_requirement_set_id": str(
            packet.get("empirical_metric_requirement_set_id", "") or ""
        ),
        "runtime_owned_requirement_bindings": dict(
            packet.get("runtime_owned_requirement_bindings", {})
        )
        if isinstance(
            packet.get("runtime_owned_requirement_bindings"),
            Mapping,
        )
        else {},
        "theory_execution_preflight": (
            _architect_theory_execution_preflight_summary(packet)
        ),
        "llm_json_repair_attempts": int(
            packet.get("llm_json_repair_attempts", 0) or 0
        ),
        "provider_structured_output_requested": bool(
            response_metadata.get("provider_structured_output_requested")
        ),
        "provider_structured_output_applied": bool(
            response_metadata.get("provider_structured_output_applied")
        ),
        "semantic_review_status": str(
            packet.get("semantic_review_status", "") or ""
        ),
        "semantic_review_packet_id": str(
            semantic_review.get("packet_id", "") or ""
        ),
        "semantic_review_packet_hash": str(
            packet.get("semantic_review_packet_hash", "") or ""
        ),
        "semantic_review_model": str(semantic_review.get("model", "") or ""),
        "semantic_review_model_tier": str(
            semantic_review.get("model_tier", "") or ""
        ),
        "semantic_review_independent_agent": bool(
            semantic_review.get("independent_agent")
        ),
        "semantic_review_independent_invocation": bool(
            semantic_review.get("independent_invocation")
        ),
        "semantic_review_independent_model": bool(
            semantic_review.get("independent_model")
        ),
        "semantic_review_independent_model_tier": bool(
            semantic_review.get("independent_model_tier")
        ),
        "semantic_review_revision_count": int(
            packet.get("semantic_review_revision_count", 0) or 0
        ),
        "semantic_review_history": [
            dict(row) for row in review_history if isinstance(row, Mapping)
        ],
        "cumulative_finding_ledger": [
            dict(row)
            for row in packet.get("cumulative_finding_ledger", []) or []
            if isinstance(row, Mapping)
        ],
        "cumulative_finding_ledger_fingerprint": str(
            packet.get("cumulative_finding_ledger_fingerprint", "") or ""
        ),
        "frozen_metric_protocol_rebinding": bool(
            packet.get("frozen_metric_protocol_rebinding")
        ),
        "frozen_source_requirement_set_id": str(
            packet.get("frozen_source_requirement_set_id", "") or ""
        ),
        "frozen_gate_semantics_preserved": bool(
            packet.get("frozen_gate_semantics_preserved")
        ),
        "semantic_review_boundary": str(
            packet.get("semantic_review_boundary", "") or ""
        ),
        "proof_evidence_status": str(
            packet.get("proof_evidence_status", "") or ""
        ),
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }


def build_architect_coordinator_prompt(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    runtime_config: Mapping[str, Any],
) -> str:
    capability_gap_routing_agenda = architect_capability_gap_routing_agenda(
        architect_context
    )
    formal_verification_policy = str(
        runtime_config.get("formal_verification_policy", "optional") or "optional"
    )
    requested_evidence_contract = {
        **_architect_runtime_owned_evidence_contract(
            architect_context=architect_context,
            runtime_config=runtime_config,
        ),
        "requested_research_path": str(
            runtime_config.get("recommended_research_path", "") or ""
        ),
        "formal_required_for_final": formal_verification_policy == "required",
        **_architect_runtime_evaluation_contract(runtime_config),
        "policy_semantics": {
            "required": (
                "full formal proof is an acceptance gate; unresolved formal "
                "gaps block final theorem acceptance"
            ),
            "optional": (
                "Architect chooses simulation-first, proof-first, or "
                "dual-track based on problem type and verification cost; "
                "formal gaps must still be disclosed"
            ),
            "advisory": (
                "formal tools are diagnostic only; final research-candidate "
                "acceptance may rely on derivation, implementation, "
                "simulation stress tests, and critic review with explicit "
                "non-formal-proof disclosure"
            ),
        },
        "allowed_research_paths": [
            "simulation_first",
            "proof_first",
            "dual_track",
        ],
    }
    required_plan_subsystems = _required_architect_plan_subsystems(
        requested_evidence_contract
    )
    evaluation_mode = str(
        requested_evidence_contract.get("evaluation_mode", "debug") or "debug"
    )
    model_architect_context = architect_observations_without_runtime_routing(
        architect_context
    )
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "architect_context": model_architect_context,
        "runtime_config": dict(runtime_config),
        "available_subsystems": list(ARCHITECT_RUNTIME_SUBSYSTEMS),
        "execution_plan_contract": {
            "required_subsystems": list(required_plan_subsystems),
            "forbidden_subsystems": (
                sorted(RESEARCH_EVAL_FORBIDDEN_FORMAL_SUBSYSTEMS)
                if evaluation_mode == "research_eval"
                else []
            ),
            "planning_rule": (
                "author compact rows for the research path and any anticipated "
                "worker; AgentRuntime will append provenance-marked empty plan "
                "shells for mandatory evidence stages omitted by the proposal, "
                "without inventing objectives, artifacts, statistical content, "
                "code, or proof content. Order authored rows by intended execution "
                "and represent same-owner retries in iteration_policy rather than "
                "duplicate stage rows"
            ),
            "resume_rule": (
                "on plan repair or resume, return the complete amended remaining "
                "worker graph, not only the pending worker"
            ),
        },
        "authority_gates": [
            "schema validation for all LLM packets",
            "AgentRuntime owns shell/filesystem/simulation execution",
            "simulation evidence is empirical, not proof evidence",
            "algorithm sandbox evidence is not production promotion",
            "runnable generated code requires independent semantic review before downstream acceptance",
            "AXLE/local Lean/kernel evidence is required for theorem proof claims",
        ],
        "runtime_capability_gap_routing_agenda": capability_gap_routing_agenda,
        "long_horizon_research_guidance": LONG_HORIZON_RESEARCH_GUIDANCE,
        "requested_evidence_contract": requested_evidence_contract,
        "formal_target_authoring_contract": (
            ARCHITECT_FORMAL_TARGET_AUTHORING_CONTRACT
        ),
        "required_output_contract": ARCHITECT_COORDINATOR_OUTPUT_CONTRACT,
        "boundary": ARCHITECT_COORDINATOR_BOUNDARY,
    }
    return (
        "Act as the top-level ArchitectCoordinator for the AI Statistician runtime. "
        "Return only one compact JSON object matching required_output_contract exactly. "
        "Use the question, current artifacts, raw environment observations, reviewer "
        "findings, and runtime memory to choose the research plan and next subsystem. "
        "Treat feedback as evidence for your own reasoning, not as a Python-authored "
        "edit recipe. When a model-authored artifact is rejected, route the complete "
        "artifact and exact observations to its owning model for full regeneration; "
        "do not prescribe a field-level patch or synthesize replacement content. "
        "Obey execution_plan_contract, requested_evidence_contract, and the evidence "
        "boundary. Preserve accepted targets, artifact identities, hashes, frozen gates, "
        "and lineage. Empirical metric requirements are authored by their dedicated "
        "model after theory and implementation context exists, so do not duplicate them. "
        "Return the complete remaining graph on resume. Keep analysis inside the JSON "
        "fields, and do not include Markdown, code, claimed executions, simulation "
        "results, or proof claims.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


def architect_capability_gap_routing_agenda(
    architect_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Project capability-gap observations without prescribing an Architect route."""
    if not isinstance(architect_context, Mapping):
        return {}
    context = architect_context.get("runtime_capability_gap_routing", {})
    if not (
        isinstance(context, Mapping)
        and context.get("artifact_kind") == "RuntimeCapabilityGapRoutingContext"
    ):
        return {}
    raw_rows = context.get("rows", [])
    if not isinstance(raw_rows, list):
        return {}
    rows: list[dict[str, Any]] = []
    owner_subsystems: set[str] = set()
    for raw_row in raw_rows:
        if not isinstance(raw_row, Mapping):
            continue
        requirement_id = _clean_architect_gap_text(
            raw_row.get("requirement_id") or raw_row.get("id")
        )
        if not requirement_id:
            continue
        next_owner = _clean_architect_gap_text(
            raw_row.get("next_owner_subsystem") or "ArchitectCoordinator"
        )
        if next_owner:
            owner_subsystems.add(next_owner)
        agenda_row = {
            "requirement_id": requirement_id,
            "scope": _clean_architect_gap_text(raw_row.get("scope")),
            "gap_status": _clean_architect_gap_text(raw_row.get("gap_status"))
            or "OPEN",
            "next_owner_subsystem": next_owner or "ArchitectCoordinator",
            "success_metric": _clean_architect_gap_text(
                raw_row.get("success_metric")
            ),
            "blocker": _clean_architect_gap_text(raw_row.get("blocker")),
            "retention_selection": _clean_architect_gap_text(
                raw_row.get("retention_selection")
            ),
            "retention_selection_boundary": _clean_architect_gap_text(
                raw_row.get("retention_selection_boundary")
            ),
            "routing_boundary": _clean_architect_gap_text(
                raw_row.get("routing_boundary")
            )
            or ARCHITECT_CAPABILITY_GAP_ROUTING_BOUNDARY,
        }
        scorecard_payload = _architect_gap_scorecard_payload(
            raw_row.get("scorecard_payload", {})
        )
        if scorecard_payload:
            agenda_row["scorecard_payload"] = scorecard_payload
        rows.append(agenda_row)
    if not rows:
        return {}
    counts = context.get("counts", {})
    if not isinstance(counts, Mapping):
        counts = {}
    rows_loaded = _architect_gap_int(counts.get("rows_loaded"), fallback=len(rows))
    rows_seen = _architect_gap_int(counts.get("rows_seen"), fallback=len(rows))
    return {
        "artifact_kind": "ArchitectCapabilityGapRoutingAgenda",
        "source_artifact_kind": "RuntimeCapabilityGapRoutingContext",
        "counts": {
            "rows_loaded": rows_loaded,
            "rows_seen": rows_seen,
            "errors": _architect_gap_int(counts.get("errors"), fallback=0),
            "max_rows": _architect_gap_int(counts.get("max_rows"), fallback=0),
            "retention_policy": _clean_architect_gap_text(
                counts.get("retention_policy")
            ),
            "input_context_truncated": rows_seen > rows_loaded,
        },
        "owner_subsystems": sorted(owner_subsystems),
        "rows": rows,
        "source_paths": _architect_gap_source_paths(context.get("source_paths", [])),
        "boundary": ARCHITECT_CAPABILITY_GAP_ROUTING_BOUNDARY,
    }


def _clean_architect_gap_text(value: Any) -> str:
    return str(value or "").strip()


def _architect_gap_scorecard_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    scorecard_row = (
        value.get("scorecard_row", {})
        if isinstance(value.get("scorecard_row", {}), Mapping)
        else {}
    )
    audit_metrics = (
        value.get("audit_metrics", {})
        if isinstance(value.get("audit_metrics", {}), Mapping)
        else {}
    )
    if not scorecard_row and not audit_metrics:
        return {}
    return {
        "artifact_kind": _clean_architect_gap_text(
            value.get("artifact_kind")
        )
        or "RuntimeCapabilityGapScorecardPayload",
        "requirement_id": _clean_architect_gap_text(value.get("requirement_id")),
        "scorecard_row": {
            str(key): _architect_gap_compact_value(nested)
            for key, nested in list(scorecard_row.items())[:10]
        },
        "audit_metrics": {
            key: _architect_gap_compact_value(nested)
            for key, nested in _architect_gap_metric_items(
                audit_metrics,
                limit=24,
            )
        },
        "proof_evidence_status": _clean_architect_gap_text(
            value.get("proof_evidence_status")
        ),
        "boundary": _clean_architect_gap_text(value.get("boundary")),
    }


def _architect_gap_metric_items(
    audit_metrics: Mapping[str, Any],
    *,
    limit: int,
) -> list[tuple[str, Any]]:
    indexed_items = [
        (str(key), value, index)
        for index, (key, value) in enumerate(audit_metrics.items())
    ]

    def priority(item: tuple[str, Any, int]) -> tuple[int, int]:
        key, value, index = item
        score = 0
        if _architect_gap_metric_has_signal(key, value):
            score -= 100
        for token, weight in (
            ("contract_issues", 35),
            ("missing", 30),
            ("invalid", 30),
            ("required", 25),
            ("inherited_scope", 20),
            ("scope_parent", 20),
            ("contract_complete", 15),
        ):
            if token in key:
                score -= weight
        return (score, index)

    return [
        (key, value)
        for key, value, _ in sorted(indexed_items, key=priority)[: max(limit, 0)]
    ]


def _architect_gap_metric_has_signal(key: str, value: Any) -> bool:
    if isinstance(value, bool):
        return value is False if "complete" in key or "passed" in key else value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    return value is not None


def _architect_gap_compact_value(value: Any) -> Any:
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, str):
        return value[:500]
    if isinstance(value, Mapping):
        return {
            str(key): _architect_gap_compact_value(nested)
            for key, nested in list(value.items())[:10]
        }
    if isinstance(value, list):
        return [_architect_gap_compact_value(item) for item in value[:10]]
    return str(value)[:500]


def _architect_gap_int(value: Any, *, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def _architect_gap_source_paths(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(path) for path in value]
    if value in (None, ""):
        return []
    return [str(value)]


ARCHITECT_COORDINATOR_SYSTEM_PROMPT = """\
You are the top-level ArchitectCoordinator inside an AI Statistician AgentRuntime.

Your job is to coordinate specialized LLM workers and runtime validators for an
open statistical research task. You plan, route, and set evidence gates; you are
not the executor or verifier. Keep proof, simulation, retrieval, and sandbox
evidence boundaries explicit.
"""


ARCHITECT_COORDINATOR_OUTPUT_CONTRACT: dict[str, Any] = {
    "intake_assessment": {
        "problem_type": "string",
        "frontier_difficulty": "low|medium|high",
        "primary_success_criteria": ["one short string"],
        "known_risks": ["one short string"],
    },
    "problem_analysis": {
        "theorem_family": "one short string",
        "statistical_objects": ["one short string"],
        "likely_analogy_classes": ["one short string"],
        "key_obstacles": ["one short string"],
        "missing_information": ["one short string"],
    },
    "stat_knowledge_bank_plan": {
        "source_families_to_collect": ["one short string"],
        "assumption_dimensions": ["one short string"],
        "proof_skeletons_to_track": ["one short string"],
        "failed_attempt_memory_policy": "one short string",
    },
    "literature_fair_comparison_plan": [
        {
            "candidate_source_family": "one short string",
            "must_match": ["one short string"],
            "likely_mismatches": ["one short string"],
            "unsafe_transfer_risks": ["one short string"],
        }
    ],
    "evidence_contract": {
        "recommended_research_path": "simulation_first|proof_first|dual_track",
        "formal_targets": [
            (
                "one precise task-specific mathematical claim naming its object, "
                "assumptions or quantifiers, and conclusion"
            )
        ],
        "simulation_targets": ["one short string"],
    },
    "subsystem_execution_plan": [
        {
            "subsystem": "RetrievalMemory",
            "objective": "one short string",
            "inputs_needed": ["one short string"],
            "expected_artifacts": ["one short string"],
            "acceptance_gate": "one short string",
        }
    ],
    "retrieval_strategy": {
        "paper_queries": ["one short string"],
        "formal_source_queries": ["one short string"],
        "lean_rag_priorities": ["one short string"],
    },
    "iteration_policy": {
        "reroute_triggers": ["one short string"],
        "max_repair_rounds": "integer",
        "stop_conditions": ["one short string"],
    },
    "evidence_gates": [
        {
            "artifact_kind": "string",
            "required_evidence": "one short string",
            "not_evidence": "one short string",
        }
    ],
    "risk_register": [
        {"risk": "one short string", "mitigation": "one short string", "owner_subsystem": "string"}
    ],
    "next_actions": [
        {"owner_agent": "RetrievalMemory", "action": "one short string", "acceptance_gate": "one short string"}
    ],
}


ARCHITECT_COORDINATOR_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "intake_assessment",
        "problem_analysis",
        "stat_knowledge_bank_plan",
        "literature_fair_comparison_plan",
        "evidence_contract",
        "subsystem_execution_plan",
        "retrieval_strategy",
        "iteration_policy",
        "evidence_gates",
        "risk_register",
        "next_actions",
    ],
    "properties": {
        "intake_assessment": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "problem_type",
                "frontier_difficulty",
                "primary_success_criteria",
                "known_risks",
            ],
            "properties": {
                "problem_type": {"type": "string"},
                "frontier_difficulty": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "primary_success_criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "known_risks": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "problem_analysis": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "theorem_family",
                "statistical_objects",
                "likely_analogy_classes",
                "key_obstacles",
                "missing_information",
            ],
            "properties": {
                "theorem_family": {"type": "string"},
                "statistical_objects": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "likely_analogy_classes": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "key_obstacles": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "missing_information": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "stat_knowledge_bank_plan": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "source_families_to_collect",
                "assumption_dimensions",
                "proof_skeletons_to_track",
                "failed_attempt_memory_policy",
            ],
            "properties": {
                "source_families_to_collect": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "assumption_dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "proof_skeletons_to_track": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "failed_attempt_memory_policy": {"type": "string"},
            },
        },
        "literature_fair_comparison_plan": {
            "type": "array",
            "minItems": 1,
            "maxItems": 2,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "candidate_source_family",
                    "must_match",
                    "likely_mismatches",
                    "unsafe_transfer_risks",
                ],
                "properties": {
                    "candidate_source_family": {"type": "string"},
                    "must_match": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                    "likely_mismatches": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                    "unsafe_transfer_risks": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "evidence_contract": {
            "type": "object",
            "additionalProperties": False,
            "required": list(
                ARCHITECT_COORDINATOR_OUTPUT_CONTRACT["evidence_contract"]
            ),
            "properties": {
                "recommended_research_path": {
                    "type": "string",
                    "enum": ["simulation_first", "proof_first", "dual_track"],
                },
                "formal_targets": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "string",
                        "minLength": 1,
                        "description": (
                            "Task-specific mathematical claim with object, "
                            "assumptions or quantifiers, and conclusion; not a "
                            "proof-completion or kernel-status policy."
                        ),
                    },
                },
                "simulation_targets": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                },
            },
        },
        "subsystem_execution_plan": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "subsystem",
                    "objective",
                    "inputs_needed",
                    "expected_artifacts",
                    "acceptance_gate",
                ],
                "properties": {
                    "subsystem": {"type": "string"},
                    "objective": {"type": "string"},
                    "inputs_needed": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "expected_artifacts": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "acceptance_gate": {"type": "string"},
                },
            },
        },
        "retrieval_strategy": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "paper_queries",
                "formal_source_queries",
                "lean_rag_priorities",
            ],
            "properties": {
                "paper_queries": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "formal_source_queries": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "lean_rag_priorities": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "iteration_policy": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "reroute_triggers",
                "max_repair_rounds",
                "stop_conditions",
            ],
            "properties": {
                "reroute_triggers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "max_repair_rounds": {"type": "integer"},
                "stop_conditions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "evidence_gates": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["artifact_kind", "required_evidence", "not_evidence"],
                "properties": {
                    "artifact_kind": {"type": "string"},
                    "required_evidence": {"type": "string"},
                    "not_evidence": {"type": "string"},
                },
            },
        },
        "risk_register": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["risk", "mitigation", "owner_subsystem"],
                "properties": {
                    "risk": {"type": "string"},
                    "mitigation": {"type": "string"},
                    "owner_subsystem": {"type": "string"},
                },
            },
        },
        "next_actions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["owner_agent", "action", "acceptance_gate"],
                "properties": {
                    "owner_agent": {"type": "string"},
                    "action": {"type": "string"},
                    "acceptance_gate": {"type": "string"},
                },
            },
        },
    },
}


def validate_architect_coordinator_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "intake_assessment",
        "problem_analysis",
        "stat_knowledge_bank_plan",
        "literature_fair_comparison_plan",
        "evidence_contract",
        "subsystem_execution_plan",
        "retrieval_strategy",
        "iteration_policy",
        "evidence_gates",
        "risk_register",
        "next_actions",
    ):
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    if packet.get("proof_evidence_status") != ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE:
        errors.append("proof_evidence_status must preserve architect proposal boundary")
    if packet.get("runtime_executed") is not False:
        errors.append("LLM ArchitectCoordinator packet cannot set runtime_executed=true")
    if packet.get("kernel_verified") is not False:
        errors.append("LLM ArchitectCoordinator packet cannot set kernel_verified=true")
    problem_analysis = packet.get("problem_analysis", {})
    if isinstance(problem_analysis, Mapping):
        for field in (
            "theorem_family",
            "statistical_objects",
            "likely_analogy_classes",
            "key_obstacles",
            "missing_information",
        ):
            if problem_analysis.get(field) in (None, "", [], {}):
                errors.append(f"problem_analysis missing or empty field: {field}")
    knowledge_plan = packet.get("stat_knowledge_bank_plan", {})
    if isinstance(knowledge_plan, Mapping):
        for field in (
            "source_families_to_collect",
            "assumption_dimensions",
            "proof_skeletons_to_track",
            "failed_attempt_memory_policy",
        ):
            if knowledge_plan.get(field) in (None, "", [], {}):
                errors.append(f"stat_knowledge_bank_plan missing or empty field: {field}")
    for row in packet.get("literature_fair_comparison_plan", []) or []:
        if not isinstance(row, Mapping):
            errors.append("literature_fair_comparison_plan entries must be objects")
            continue
        for field in (
            "candidate_source_family",
            "must_match",
            "likely_mismatches",
            "unsafe_transfer_risks",
        ):
            if row.get(field) in (None, "", [], {}):
                errors.append(
                    f"literature_fair_comparison_plan entry missing or empty field: {field}"
                )
    evaluation_mode = ""
    evidence_contract = packet.get("evidence_contract", {})
    if isinstance(evidence_contract, Mapping):
        policy = str(
            evidence_contract.get("formal_verification_policy", "") or ""
        ).strip().lower()
        if policy not in {"required", "optional", "advisory"}:
            errors.append(
                "evidence_contract.formal_verification_policy must be required, "
                "optional, or advisory"
            )
        path = str(
            evidence_contract.get("recommended_research_path", "") or ""
        ).strip().lower()
        if path not in {"simulation_first", "proof_first", "dual_track"}:
            errors.append(
                "evidence_contract.recommended_research_path must be "
                "simulation_first, proof_first, or dual_track"
            )
        if not isinstance(evidence_contract.get("formal_required_for_final"), bool):
            errors.append(
                "evidence_contract.formal_required_for_final must be a boolean"
            )
        evaluation_mode = str(
            evidence_contract.get("evaluation_mode", "") or ""
        ).strip()
        research_evaluation = evaluation_mode in RESEARCH_EVALUATION_MODES
        metric_policy = str(
            evidence_contract.get("generated_metric_contract_policy", "") or ""
        ).strip()
        authority_policy = str(
            evidence_contract.get(
                "generated_metric_requirement_authority_policy", ""
            )
            or ""
        ).strip()
        if metric_policy and metric_policy not in {
            "typed_artifact_bound_required",
            "typed_artifact_bound_preferred",
        }:
            errors.append(
                "evidence_contract.generated_metric_contract_policy must be "
                "typed_artifact_bound_required or typed_artifact_bound_preferred"
            )
        typed_required = _research_evaluation_contract_flag(
            evidence_contract,
            "typed_metric_contracts",
        )
        if typed_required is not None and not isinstance(typed_required, bool):
            errors.append(
                "evidence_contract.capability_eval_requires_typed_metric_contracts "
                "must be a boolean"
            )
        if authority_policy and authority_policy not in {
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED,
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
        }:
            errors.append(
                "evidence_contract.generated_metric_requirement_authority_policy "
                "must be architect-authored and coding-agent-bound"
            )
        if research_evaluation and (
            typed_required is not True
            or metric_policy != "typed_artifact_bound_required"
            or authority_policy
            != GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED
            or not _research_evaluation_contract_flag(
                evidence_contract,
                "generated_code_semantic_review",
            )
        ):
            errors.append(
                "research evaluation requires typed artifact-bound contracts backed "
                "by Architect-authored metric requirements and independent "
                "generated-code semantic review"
            )
        requirements = evidence_contract.get("empirical_metric_requirements", [])
        metric_protocol_phase = str(
            evidence_contract.get("empirical_metric_protocol_phase", "") or ""
        ).strip()
        metric_protocol_execution_authorized = evidence_contract.get(
            "metric_protocol_execution_authorized"
        )
        if metric_protocol_phase not in METRIC_PROTOCOL_PHASES:
            errors.append(
                "evidence_contract.empirical_metric_protocol_phase must be a "
                "recognized runtime phase"
            )
        if not isinstance(metric_protocol_execution_authorized, bool):
            errors.append(
                "evidence_contract.metric_protocol_execution_authorized must be a "
                "boolean"
            )
        expected_runtime_replicates = evidence_contract.get(
            "generated_sandbox_runtime_replicates"
        )
        if research_evaluation and (
            isinstance(expected_runtime_replicates, bool)
            or not isinstance(expected_runtime_replicates, int)
            or expected_runtime_replicates <= 0
        ):
            errors.append(
                "research evaluation requires a positive runtime-owned "
                "generated_sandbox_runtime_replicates value"
            )
        if requirements not in (None, [], {}):
            if research_evaluation and (
                metric_protocol_phase
                != METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED
                or metric_protocol_execution_authorized is not True
            ):
                errors.append(
                    "research-evaluation metric requirements authorize execution only "
                    "after independent pre-execution review acceptance"
                )
            errors.extend(
                validate_generated_metric_requirements(
                    requirements,
                    required_target_subsystems=(
                        GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                    )
                    if research_evaluation
                    else (),
                    expected_runtime_replicates=(
                        expected_runtime_replicates
                        if research_evaluation
                        and isinstance(expected_runtime_replicates, int)
                        and not isinstance(expected_runtime_replicates, bool)
                        else None
                    ),
                )
            )
            if research_evaluation:
                review = evidence_contract.get(
                    "empirical_metric_requirements_preexecution_review", {}
                )
                if not isinstance(review, Mapping):
                    errors.append(
                        "research-evaluation metric requirements require a typed "
                        "pre-execution semantic review certificate"
                    )
                else:
                    if review.get("overall_verdict") != "ACCEPT":
                        errors.append(
                            "research-evaluation metric requirements require an ACCEPT "
                            "pre-execution semantic review"
                        )
                    for field in (
                        "review_packet_id",
                        "review_packet_hash",
                        "reviewed_empirical_metric_requirement_set_id",
                        "source_theory_packet_id",
                        "source_theory_packet_hash",
                        "reviewer_model",
                        "reviewer_model_tier",
                    ):
                        if not str(review.get(field, "") or "").strip():
                            errors.append(
                                "metric pre-execution review certificate missing "
                                f"{field}"
                            )
                    if any(
                        review.get(field) is not True
                        for field in (
                            "independent_agent",
                            "independent_invocation",
                        )
                    ):
                        errors.append(
                            "metric pre-execution review certificate must record "
                            "an independent agent and separate blinded invocation"
                        )
                    if str(
                        review.get(
                            "reviewed_empirical_metric_requirement_set_id", ""
                        )
                        or ""
                    ) != generated_metric_requirement_set_id(
                        [
                            dict(row)
                            for row in requirements
                            if isinstance(row, Mapping)
                        ]
                    ):
                        errors.append(
                            "metric pre-execution review certificate is not bound "
                            "to the frozen requirement set"
                        )
        elif research_evaluation:
            if (
                metric_protocol_phase
                not in {
                    METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING,
                    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
                }
                or metric_protocol_execution_authorized is not False
            ):
                errors.append(
                    "research evaluation may omit empirical_metric_requirements only "
                    "while the TheoryDeveloper prerequisite or an explicit "
                    "theory-informed authoring turn remains pending and metric "
                    "protocol execution stays unauthorized"
                )
        for field in (
            "formal_targets",
            "simulation_targets",
            "acceptance_modes",
            "disclosure_requirements",
        ):
            if evidence_contract.get(field) in (None, "", [], {}):
                errors.append(f"evidence_contract missing or empty field: {field}")
        formal_targets = evidence_contract.get("formal_targets", [])
        if isinstance(formal_targets, list):
            for index, target in enumerate(formal_targets):
                target_text = str(target or "").strip()
                if architect_formal_target_is_completion_placeholder(target_text):
                    errors.append(
                        "evidence_contract.formal_targets must contain a "
                        "task-specific mathematical claim rather than the legacy "
                        f"runtime completion placeholder at index {index}"
                    )
    planned_subsystems: set[str] = set()
    for row in packet.get("subsystem_execution_plan", []) or []:
        if not isinstance(row, Mapping):
            errors.append("subsystem_execution_plan entries must be objects")
            continue
        subsystem = str(row.get("subsystem", "") or "").strip()
        if not subsystem:
            errors.append("subsystem_execution_plan entry missing subsystem")
            continue
        planned_subsystems.add(subsystem)
    for subsystem in _required_architect_plan_subsystems(evidence_contract):
        if subsystem not in planned_subsystems:
            errors.append(
                "subsystem_execution_plan missing evidence-contract-required "
                f"subsystem: {subsystem}"
            )
    if evaluation_mode == "research_eval":
        forbidden_formal_subsystems = sorted(
            planned_subsystems & RESEARCH_EVAL_FORBIDDEN_FORMAL_SUBSYSTEMS
        )
        if forbidden_formal_subsystems:
            errors.append(
                "research_eval must keep the strict formal lane out of this run; "
                "remove formal subsystems: "
                + ", ".join(forbidden_formal_subsystems)
            )
    forbidden = _contains_forbidden_claim(packet)
    if forbidden:
        errors.append(f"packet contains forbidden execution/proof claim: {forbidden}")
    return sorted(set(errors))


def _architect_runtime_owned_evidence_contract(
    *,
    architect_context: Mapping[str, Any] | None,
    runtime_config: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Preserve runtime gates and accepted task targets without content override."""

    context = architect_context or {}
    config = runtime_config or {}
    requested = context.get("runtime_requested_evidence_contract", {})
    requested_contract = dict(requested) if isinstance(requested, Mapping) else {}
    contract: dict[str, Any] = {}
    for field in (
        "acceptance_modes",
        "disclosure_requirements",
        "formal_target_authoring_required",
        "formal_target_completion_policy",
        "simulation_target_authoring_required",
    ):
        value = requested_contract.get(field)
        if value not in (None, "", [], {}):
            contract[field] = value
    prior_plan = context.get("architect_runtime_plan", {})
    prior_contract = (
        prior_plan.get("evidence_contract", {})
        if isinstance(prior_plan, Mapping)
        else {}
    )
    if not isinstance(prior_contract, Mapping):
        prior_contract = {}
    theory_material = theory_informed_metric_protocol_material(context)
    evaluation_contract = _architect_runtime_evaluation_contract(config)
    strict_metric_protocol = _research_evaluation_contract_flag(
        evaluation_contract,
        "typed_metric_contracts",
    )
    prior_review = prior_contract.get(
        "empirical_metric_requirements_preexecution_review", {}
    )
    if not isinstance(prior_review, Mapping):
        prior_review = {}
    prior_requirements_match_current_theory = bool(
        (not theory_material and not strict_metric_protocol)
        or (
            theory_material
            and metric_protocol_authority_matches_theory(
                source_theory_packet_id=prior_review.get(
                    "source_theory_packet_id", ""
                ),
                source_theory_packet_hash=prior_review.get(
                    "source_theory_packet_hash", ""
                ),
                theory_material=theory_material,
            )
        )
    )
    for field in ("formal_targets", "simulation_targets"):
        prior_value = prior_contract.get(field)
        if prior_value not in (None, "", [], {}):
            contract[field] = (
                list(prior_value)
                if isinstance(prior_value, (list, tuple))
                else prior_value
            )
    prior_requirements = prior_contract.get("empirical_metric_requirements", [])
    metric_authoring = context.get("architect_metric_requirement_authoring", {})
    authored_requirements = (
        metric_authoring.get("empirical_metric_requirements", [])
        if isinstance(metric_authoring, Mapping)
        else []
    )
    authored_requirements_independently_accepted = bool(
        isinstance(metric_authoring, Mapping)
        and metric_authoring.get("semantic_review_status") == "ACCEPT"
        and metric_authoring.get("semantic_review_independent_agent") is True
        and metric_authoring.get("semantic_review_independent_invocation") is True
        and (
            (not theory_material and not strict_metric_protocol)
            or (
                theory_material
                and metric_protocol_authority_matches_theory(
                    source_theory_packet_id=metric_authoring.get(
                        "source_theory_packet_id", ""
                    ),
                    source_theory_packet_hash=metric_authoring.get(
                        "source_theory_packet_hash", ""
                    ),
                    theory_material=theory_material,
                )
            )
        )
    )
    if (
        isinstance(prior_requirements, list)
        and prior_requirements
        and prior_requirements_match_current_theory
    ):
        contract["empirical_metric_requirements"] = [
            dict(row) if isinstance(row, Mapping) else row
            for row in prior_requirements
        ]
        contract["empirical_metric_requirement_set_id"] = (
            generated_metric_requirement_set_id(
                [
                    dict(row)
                    for row in prior_requirements
                    if isinstance(row, Mapping)
                ]
            )
        )
        contract[
            "empirical_metric_requirements_frozen_from_prior_architect_plan"
        ] = True
        if isinstance(prior_review, Mapping) and prior_review:
            contract["empirical_metric_requirements_preexecution_review"] = dict(
                prior_review
            )
    elif (
        isinstance(authored_requirements, list)
        and authored_requirements
        and authored_requirements_independently_accepted
    ):
        contract["empirical_metric_requirements"] = [
            dict(row) if isinstance(row, Mapping) else row
            for row in authored_requirements
        ]
        contract["empirical_metric_requirement_set_id"] = (
            generated_metric_requirement_set_id(
                [
                    dict(row)
                    for row in authored_requirements
                    if isinstance(row, Mapping)
                ]
            )
        )
        contract[
            "empirical_metric_requirements_frozen_from_metric_planner"
        ] = True
        contract["empirical_metric_requirements_preexecution_review"] = {
            "artifact_kind": "ArchitectMetricPreExecutionReviewCertificate",
            "overall_verdict": "ACCEPT",
            "review_packet_id": str(
                metric_authoring.get("semantic_review_packet_id", "") or ""
            ),
            "review_packet_hash": str(
                metric_authoring.get("semantic_review_packet_hash", "") or ""
            ),
            "reviewed_empirical_metric_requirement_set_id": str(
                metric_authoring.get("empirical_metric_requirement_set_id", "")
                or ""
            ),
            "source_theory_packet_id": str(
                metric_authoring.get("source_theory_packet_id", "") or ""
            ),
            "source_theory_packet_hash": str(
                metric_authoring.get("source_theory_packet_hash", "") or ""
            ),
            "reviewer_model": str(
                metric_authoring.get("semantic_review_model", "") or ""
            ),
            "reviewer_model_tier": str(
                metric_authoring.get("semantic_review_model_tier", "") or ""
            ),
            "independent_agent": bool(
                metric_authoring.get("semantic_review_independent_agent")
            ),
            "independent_invocation": bool(
                metric_authoring.get("semantic_review_independent_invocation")
            ),
            "independent_model": bool(
                metric_authoring.get("semantic_review_independent_model")
            ),
            "independent_model_tier": bool(
                metric_authoring.get("semantic_review_independent_model_tier")
            ),
            "pre_execution_review": True,
            "execution_results_observed": False,
            "proof_evidence_status": (
                "ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE"
            ),
            "boundary": ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY,
        }
    policy = str(
        config.get("formal_verification_policy", "")
        or requested_contract.get("formal_verification_policy", "")
        or "optional"
    ).strip().lower()
    contract["formal_verification_policy"] = policy
    contract["formal_required_for_final"] = policy == "required"
    requested_path = str(
        requested_contract.get("recommended_research_path", "")
        or config.get("recommended_research_path", "")
        or ""
    ).strip()
    if requested_path:
        contract["recommended_research_path"] = requested_path
    contract.update(evaluation_contract)
    capability_eval = _research_evaluation_contract_flag(
        contract,
        "typed_metric_contracts",
    )
    accepted_requirements = bool(contract.get("empirical_metric_requirements"))
    if not capability_eval:
        contract["empirical_metric_protocol_phase"] = (
            METRIC_PROTOCOL_PHASE_NOT_REQUIRED
        )
        contract["metric_protocol_execution_authorized"] = True
    elif accepted_requirements:
        contract["empirical_metric_protocol_phase"] = (
            METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED
        )
        contract["metric_protocol_execution_authorized"] = True
    elif theory_material:
        contract["empirical_metric_requirements"] = []
        contract["empirical_metric_protocol_phase"] = (
            METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED
        )
        contract["metric_protocol_execution_authorized"] = False
    else:
        contract["empirical_metric_requirements"] = []
        contract["empirical_metric_protocol_phase"] = (
            METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING
        )
        contract["metric_protocol_execution_authorized"] = False
    return contract


def _normalize_architect_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    runtime_config: Mapping[str, Any] | None = None,
    architect_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body = dict(payload)
    evidence_contract = body.get("evidence_contract", {})
    if isinstance(evidence_contract, Mapping):
        normalized_contract = dict(evidence_contract)
    else:
        normalized_contract = {}
    for key, value in _architect_runtime_owned_evidence_contract(
        architect_context=architect_context,
        runtime_config=runtime_config,
    ).items():
        normalized_contract[key] = value
    requirements = normalized_contract.get("empirical_metric_requirements", [])
    if isinstance(requirements, list) and requirements:
        normalized_contract["empirical_metric_requirement_set_id"] = (
            generated_metric_requirement_set_id(
                [dict(row) for row in requirements if isinstance(row, Mapping)]
            )
        )
        normalized_contract.setdefault(
            "empirical_metric_requirements_frozen_from_prior_architect_plan",
            False,
        )
    body["evidence_contract"] = normalized_contract
    (
        body["subsystem_execution_plan"],
        body["subsystem_execution_plan_provenance"],
    ) = _elaborate_architect_subsystem_execution_plan(
        body.get("subsystem_execution_plan", []),
        evidence_contract=normalized_contract,
    )
    body["proof_evidence_status"] = ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE
    body["evidence_boundary"] = ARCHITECT_COORDINATOR_BOUNDARY
    body["runtime_executed"] = False
    body["kernel_verified"] = False
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
        }
    )[:24]
    return {
        "schema_version": ARCHITECT_COORDINATOR_SCHEMA_VERSION,
        "artifact_kind": "ArchitectCoordinatorProposalPacket",
        "packet_id": f"architect_coordinator_proposal:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMArchitectCoordinatorAgent",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _elaborate_architect_subsystem_execution_plan(
    value: Any,
    *,
    evidence_contract: Mapping[str, Any],
) -> tuple[list[Any], dict[str, Any]]:
    """Compile mandatory evidence topology without synthesizing research content."""

    source_rows = list(value) if isinstance(value, list) else []
    plan_rows: list[Any] = [
        dict(row) if isinstance(row, Mapping) else row for row in source_rows
    ]
    llm_authored_subsystems = [
        str(row.get("subsystem", "") or "").strip()
        for row in source_rows
        if isinstance(row, Mapping)
        and str(row.get("subsystem", "") or "").strip()
    ]
    planned_subsystems = set(llm_authored_subsystems)
    runtime_elaborated_subsystems: list[str] = []
    for subsystem in _required_architect_plan_subsystems(evidence_contract):
        if subsystem in planned_subsystems:
            continue
        plan_rows.append(
            {
                "subsystem": subsystem,
                "objective": "",
                "inputs_needed": [],
                "expected_artifacts": [],
                "acceptance_gate": "",
                "plan_row_source": "runtime_required_evidence_contract",
                "llm_authored": False,
                "runtime_defaults_required": True,
            }
        )
        planned_subsystems.add(subsystem)
        runtime_elaborated_subsystems.append(subsystem)
    provenance = {
        "artifact_kind": "ArchitectSubsystemExecutionPlanProvenance",
        "llm_authored_subsystems": llm_authored_subsystems,
        "runtime_elaborated_subsystems": runtime_elaborated_subsystems,
        "runtime_elaboration_only_adds_empty_mandatory_stage_shells": True,
        "runtime_elaboration_may_generate_research_content": False,
        "evidence_contract_fingerprint": stable_hash(dict(evidence_contract)),
        "boundary": (
            "Runtime elaboration records mandatory typed evidence topology only. "
            "It does not author statistical objectives, expected results, code, "
            "Lean declarations, proof steps, or evidence claims."
        ),
    }
    return plan_rows, provenance


def _architect_runtime_evaluation_contract(
    runtime_config: Mapping[str, Any],
) -> dict[str, Any]:
    evaluation_mode = str(runtime_config.get("evaluation_mode", "debug") or "debug")
    research_evaluation = evaluation_mode in RESEARCH_EVALUATION_MODES
    capability_eval = evaluation_mode == "capability_eval"
    return {
        "evaluation_mode": evaluation_mode,
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
        "capability_eval_requires_generated_algorithm_code": research_evaluation,
        "capability_eval_requires_generated_simulation_code": research_evaluation,
        "capability_eval_requires_generated_code_semantic_review": research_evaluation,
        "capability_eval_requires_formal_target_semantic_review": bool(
            capability_eval
            and runtime_config.get(
                "formal_target_semantic_review_required", False
            )
        ),
        "capability_eval_requires_typed_metric_contracts": research_evaluation,
        "capability_eval_requires_formalizer_lean_candidate": capability_eval,
        "generated_sandbox_runtime_replicates": (
            generated_sandbox_runtime_replicates(
                int(runtime_config.get("n_runs", 100) or 100)
            )
        ),
        "generated_metric_contract_policy": (
            "typed_artifact_bound_required"
            if research_evaluation
            else "typed_artifact_bound_preferred"
        ),
        "generated_metric_requirement_authority_policy": (
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED
            if research_evaluation
            else GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
        ),
        "capability_eval_requires_exact_source_theorem_prover": (
            capability_eval
            and bool(runtime_config.get("exact_source_theorem_prover_available", False))
        ),
        "theorem_reduction_closure_proofengineer_required": bool(
            evaluation_mode != "research_eval"
            and runtime_config.get(
                "theorem_closure_proofengineer_bridge", False
            )
        ),
        "exact_source_theorem_proof_body_executor_required": bool(
            evaluation_mode != "research_eval"
            and runtime_config.get(
                "source_theorem_formal_environment_proofengineer_bridge",
                False,
            )
            and runtime_config.get(
                "source_theorem_formal_environment_proofengineer_execute_proof_body",
                False,
            )
        ),
        "source_semantic_proofengineer_required": bool(
            evaluation_mode != "research_eval"
            and runtime_config.get("source_semantic_proofengineer_bridge", False)
        ),
        "pseudo_formal_block_verifier_required": bool(
            evaluation_mode != "research_eval"
            and runtime_config.get("pseudo_formal_block_verifier_runtime", False)
        ),
        "source_theorem_promotion_proofengineer_required": bool(
            evaluation_mode != "research_eval"
            and runtime_config.get(
                "source_theorem_promotion_proofengineer_bridge", False
            )
        ),
    }


def _required_architect_plan_subsystems(
    evidence_contract: Mapping[str, Any],
) -> tuple[str, ...]:
    required: set[str] = set()
    evaluation_mode = str(evidence_contract.get("evaluation_mode", "") or "")
    if evaluation_mode in RESEARCH_EVALUATION_MODES:
        required.update(("RetrievalMemory", "TheoryDeveloper", "CriticEvaluator"))
        if _research_evaluation_contract_flag(
            evidence_contract,
            "generated_simulation_code",
        ):
            required.add("SimulationEvaluator")
        if _research_evaluation_contract_flag(
            evidence_contract,
            "generated_algorithm_code",
        ):
            required.add("AlgorithmEngineer")
        if _research_evaluation_contract_flag(
            evidence_contract,
            "generated_code_semantic_review",
        ):
            required.add("GeneratedCodeSemanticReviewer")
        if (
            evaluation_mode == "capability_eval"
            and evidence_contract.get(
                "capability_eval_requires_formal_target_semantic_review"
            )
            is True
        ):
            required.add("FormalTargetSemanticReviewer")
        if (
            evaluation_mode == "capability_eval"
            and evidence_contract.get(
                "capability_eval_requires_formalizer_lean_candidate"
            )
            is True
        ):
            required.add("FormalizationEvaluator")
        if (
            evaluation_mode == "capability_eval"
            and evidence_contract.get(
                "capability_eval_requires_exact_source_theorem_prover"
            )
            is True
        ):
            required.add("ExactSourceTheoremProver")
    if (
        evidence_contract.get("formal_required_for_final") is True
        or str(evidence_contract.get("formal_verification_policy", "") or "")
        == "required"
    ):
        required.update(
            (
                "FormalizationEvaluator",
                "ProofEngineer",
                "FormalizationGapPlanner",
            )
        )
    if (
        evidence_contract.get(
            "theorem_reduction_closure_proofengineer_required"
        )
        is True
    ):
        required.add("TheoremReductionClosureProofEngineer")
    if (
        evidence_contract.get(
            "exact_source_theorem_proof_body_executor_required"
        )
        is True
    ):
        required.add("ExactSourceTheoremProofBodyExecutor")
    if evidence_contract.get("source_semantic_proofengineer_required") is True:
        required.add("SourceSemanticProofEngineer")
    if evidence_contract.get("pseudo_formal_block_verifier_required") is True:
        required.add("PseudoFormalBlockVerifier")
    if (
        evidence_contract.get(
            "source_theorem_promotion_proofengineer_required"
        )
        is True
    ):
        required.add("SourceTheoremPromotionProofEngineer")
    return tuple(
        subsystem
        for subsystem in ARCHITECT_RUNTIME_SUBSYSTEMS
        if subsystem in required
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM ArchitectCoordinator")


def _contains_forbidden_claim(value: Any) -> str:
    text = json.dumps(value, default=str).lower()
    forbidden = (
        "runtime_executed\": true",
        "kernel_verified\": true",
        "simulation passed",
        "theorem proved",
        "kernel verified theorem",
    )
    for token in forbidden:
        if token in text:
            return token
    return ""
