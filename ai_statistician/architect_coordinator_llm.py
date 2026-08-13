from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .agent_runtime import agent_runtime_substage
from .cross_family_eval_protocol import withhold_confirmatory_evaluation_seed

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
from .structured_output_retry import extract_json_object, generate_validated_json_packet
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND,
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
from .scientific_code_workspace import (
    SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY,
)
from .theory_revision_lineage import (
    RUNTIME_THEORY_REVISION_BUDGET_CONTEXT_KEY,
    runtime_theory_revision_budget,
)


ARCHITECT_COORDINATOR_SCHEMA_VERSION = 1
ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE = "LLM_ARCHITECT_COORDINATOR_PROPOSAL_NOT_PROOF_EVIDENCE"
ARCHITECT_COORDINATOR_BOUNDARY = (
    "LLM ArchitectCoordinator packets are orchestration proposals only. They "
    "can choose the research path, mathematical targets, retrieval priorities, "
    "iteration policy, and one next workspace action. Runtime owns mandatory "
    "evidence topology, budgets, lineage, and authority gates. Architect packets "
    "do not execute tools, validate simulations, or prove theorems; runtime "
    "validators and AXLE/local Lean remain the authority gates."
)
ARCHITECT_RUNTIME_SUBSYSTEMS = (
    "RetrievalMemory",
    "TheoryDeveloper",
    "AlgorithmEngineer",
    "SimulationEvaluator",
    "GeneratedCodeSemanticReviewer",
    "FormalizationEvaluator",
    "FormalTargetSemanticReviewer",
    "CriticEvaluator",
)
ARCHITECT_FEEDBACK_ROUTE_OPERATION = "environment_feedback_route"
ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS = (
    "RetrievalMemory",
    "TheoryDeveloper",
    "SimulationEvaluator",
    "AlgorithmEngineer",
    "FormalizationEvaluator",
    "CriticEvaluator",
)
ARCHITECT_FEEDBACK_ROUTE_NOT_EVIDENCE = (
    "LLM_ARCHITECT_FEEDBACK_ROUTE_NOT_PROOF_OR_EXECUTION_EVIDENCE"
)
ARCHITECT_FEEDBACK_ROUTE_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "decision",
        "selected_subsystem",
        "objective",
        "rationale",
    ],
    "properties": {
        "decision": {"type": "string", "enum": ["ROUTE", "BLOCK"]},
        "selected_subsystem": {
            "type": "string",
            "enum": [*ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS, "NONE"],
        },
        "objective": {"type": "string"},
        "rationale": {"type": "string"},
    },
}
RESEARCH_EVALUATION_MODES = frozenset({"research_eval", "capability_eval"})
RESEARCH_EVAL_FORBIDDEN_FORMAL_SUBSYSTEMS = frozenset(
    {
        "FormalTargetSemanticReviewer",
        "FormalizationEvaluator",
    }
)
ARCHITECT_REUSABLE_VALIDATED_PLAN_FIELDS = (
    "problem_analysis",
    "evidence_contract",
    "retrieval_strategy",
    "iteration_policy",
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
    return evidence_contract.get(
        f"research_evaluation_requires_{requirement}"
    ) is True

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
    max_tokens: int = 3000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_validation_retries: int = 2
    metric_semantic_reviewer_model: str = ""
    metric_semantic_reviewer_model_tier: str = "sonnet"
    metric_semantic_reviewer_max_tokens: int = 7000
    metric_semantic_reviewer_max_revisions: int = 1


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
                    max_validation_retries=min(
                        self.config.max_validation_retries,
                        ArchitectMetricContractAuthoringConfig().max_validation_retries,
                    ),
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
                "max_packet_regeneration_attempts": self.config.max_validation_retries,
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
                max_validation_retries=self.config.max_validation_retries,
            )

    def route_environment_feedback(
        self,
        *,
        question: OpenResearchQuestion,
        architect_context: Mapping[str, Any],
        environment_feedback: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Choose one next owner without regenerating the research plan.

        This is the same Architect model and provider used by ``propose``. The
        runtime supplies observations and validates identity/budget boundaries;
        it never infers an owner or authors a candidate fix.
        """

        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        feedback_fingerprint = stable_hash(dict(environment_feedback))
        available_route_subsystems = _architect_feedback_route_subsystems(
            architect_context=architect_context,
            environment_feedback=environment_feedback,
        )
        request = GeneratorRequest(
            system_prompt=ARCHITECT_COORDINATOR_SYSTEM_PROMPT,
            user_prompt=build_architect_feedback_route_prompt(
                question=question,
                architect_context=architect_context,
                environment_feedback=environment_feedback,
            ),
            model=request_model,
            max_tokens=min(max(512, int(self.config.max_tokens or 0)), 2000),
            temperature=self.config.temperature,
            schema=ARCHITECT_FEEDBACK_ROUTE_JSON_SCHEMA,
            metadata={
                "subsystem": "ArchitectCoordinator",
                "agent": "LLMArchitectCoordinatorAgent",
                "operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
                "provider_structured_output": True,
                "environment_feedback_fingerprint": feedback_fingerprint,
                "available_route_subsystems": list(available_route_subsystems),
            },
        )

        def build_packet(
            payload: Mapping[str, Any],
            response: Any,
            raw_text: str,
        ) -> dict[str, Any]:
            normalized = {
                "schema_version": ARCHITECT_COORDINATOR_SCHEMA_VERSION,
                "artifact_kind": "ArchitectFeedbackRouteDecision",
                "question_id": question.id,
                "decision": str(payload.get("decision", "") or "").strip(),
                "selected_subsystem": str(
                    payload.get("selected_subsystem", "") or ""
                ).strip(),
                "objective": str(payload.get("objective", "") or "").strip(),
                "rationale": str(payload.get("rationale", "") or "").strip(),
                "model": response.model or request_model,
                "model_tier": self.config.model_tier,
                "provider": self.config.provider_name or response.provider,
                "backend_provider": response.provider,
                "source_agent": "LLMArchitectCoordinatorAgent",
                "operation": ARCHITECT_FEEDBACK_ROUTE_OPERATION,
                "environment_feedback_fingerprint": feedback_fingerprint,
                "raw_response": raw_text,
                "proof_evidence_status": ARCHITECT_FEEDBACK_ROUTE_NOT_EVIDENCE,
                "evidence_boundary": ARCHITECT_COORDINATOR_BOUNDARY,
            }
            normalized["route_decision_id"] = (
                "architect_feedback_route:"
                + stable_hash(
                    {
                        "question_id": question.id,
                        "feedback_fingerprint": feedback_fingerprint,
                        "decision": normalized["decision"],
                        "selected_subsystem": normalized["selected_subsystem"],
                        "objective": normalized["objective"],
                        "rationale": normalized["rationale"],
                    }
                )[:20]
            )
            return normalized

        with agent_runtime_substage(
            "architect_feedback_route",
            metadata={
                "model_tier": self.config.model_tier,
                "max_packet_regeneration_attempts": self.config.max_validation_retries,
                "full_research_plan_regeneration": False,
            },
        ):
            return generate_validated_json_packet(
                provider=self.provider,
                request=request,
                extract_payload=_extract_json_object,
                build_packet=build_packet,
                validate_packet=lambda packet: validate_architect_feedback_route_packet(
                    packet,
                    available_subsystems=available_route_subsystems,
                ),
                validation_label="LLM Architect feedback-route packet",
                max_validation_retries=self.config.max_validation_retries,
            )


def build_architect_feedback_route_prompt(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
) -> str:
    """Build a compact routing prompt; the selected worker gets full feedback."""

    runtime_plan = architect_context.get("architect_runtime_plan", {})
    runtime_plan = runtime_plan if isinstance(runtime_plan, Mapping) else {}
    active_runtime_context = {
        key: deepcopy(architect_context[key])
        for key in (
            "runtime_evaluation_mode",
            "empirical_evaluation_phase",
            "candidate_lineage_budget",
            RUNTIME_THEORY_REVISION_BUDGET_CONTEXT_KEY,
            "runtime_progress_snapshot",
            "architect_metric_protocol_gate",
        )
        if key in architect_context
    }
    active_runtime_context["active_artifact_refs"] = {
        str(key): deepcopy(value)
        for key, value in architect_context.items()
        if (
            (str(key).endswith("_id") or str(key).endswith("_hash"))
            and value not in (None, "", [], {})
        )
    }
    active_runtime_context = architect_observations_without_runtime_routing(
        active_runtime_context
    )
    available_route_subsystems = _architect_feedback_route_subsystems(
        architect_context=architect_context,
        environment_feedback=environment_feedback,
    )
    current_source_owner = str(
        environment_feedback.get("source_subsystem", "") or ""
    ).strip()
    consumer_source_owner_value = environment_feedback.get(
        "consumer_source_owner",
        {},
    )
    consumer_source_owner = (
        dict(consumer_source_owner_value)
        if isinstance(consumer_source_owner_value, Mapping)
        else {}
    )
    active_artifact_ownership = {
        "current_observation_source": {
            "owner_subsystem": current_source_owner or "NONE",
            "artifact_id": str(
                environment_feedback.get("source_manifest_id", "")
                or environment_feedback.get("source_artifact_id", "")
                or "NONE"
            ),
        },
        "upstream_dependencies": {
            "owner_subsystem": str(
                consumer_source_owner.get("source_owner_subsystem", "")
                or "NONE"
            ),
            "artifact_ids": [
                str(value)
                for value in consumer_source_owner.get(
                    "dependency_artifact_ids",
                    [],
                )
                or []
                if str(value).strip()
            ],
            "identity_only": bool(
                environment_feedback.get(
                    "consumer_source_owner_is_dependency_identity_only",
                    False,
                )
            ),
        },
    }
    unavailable_route_subsystems = sorted(
        set(ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS)
        - set(available_route_subsystems)
    )
    source_revision_assessment: Mapping[str, Any] = {}
    for candidate in (
        environment_feedback,
        environment_feedback.get("observation_artifact_ref", {}),
        environment_feedback.get("current_environment_observation", {}),
    ):
        if not isinstance(candidate, Mapping):
            continue
        assessment = candidate.get("source_revision_assessment", {})
        if isinstance(assessment, Mapping) and assessment:
            source_revision_assessment = assessment
            break
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "available_route_subsystems": list(available_route_subsystems),
        "unavailable_route_subsystems": unavailable_route_subsystems,
        "current_source_owner": current_source_owner or "NONE",
        "active_artifact_ownership": active_artifact_ownership,
        "active_source_revision_assessment": deepcopy(
            dict(source_revision_assessment)
        ),
        "current_validated_plan": {
            key: deepcopy(runtime_plan.get(key))
            for key in (
                "problem_analysis",
                "subsystem_execution_plan",
                "next_actions",
                "evidence_gates",
                "risk_register",
                "evidence_contract",
            )
            if key in runtime_plan
        },
        "active_runtime_context": active_runtime_context,
        "environment_observations": architect_observations_without_runtime_routing(
            environment_feedback
        ),
        "environment_feedback_fingerprint": stable_hash(dict(environment_feedback)),
        "routing_contract": {
            "owner_selected_by_architect_model": True,
            "selected_worker_receives_complete_feedback": True,
            "current_source_owner_is_identity_not_causal_attribution": True,
            "selected_source_editor_must_own_the_target_artifact": True,
            "source_rewrite_stays_with_exact_source_owner": True,
            "source_only_review_cannot_be_reclassified_as_parent_defect": True,
            "confirmatory_unchanged_source_retry_is_forbidden": True,
            "outcome_informed_new_source_requires_fresh_cohort": True,
            "unvisited_required_lanes_are_independent": True,
            "critic_requires_no_routable_required_lane": True,
            "new_repair_patch_or_adapter_subsystem_forbidden": True,
            "immutable_evidence_gates_cannot_be_weakened": True,
            "block_only_when_no_available_owner_can_produce_evidence": True,
        },
        "required_output": {
            "decision": "ROUTE or BLOCK",
            "selected_subsystem": (
                "one available_route_subsystems value for ROUTE; NONE for BLOCK"
            ),
            "objective": "one concrete next evidence-producing objective",
            "rationale": (
                "why this owner is appropriate, or the exact blocking condition"
            ),
        },
    }
    bounded_payload = {
        "question": payload["question"],
        "available_route_subsystems": payload["available_route_subsystems"],
        "unavailable_route_subsystems": payload[
            "unavailable_route_subsystems"
        ],
        "current_source_owner": payload["current_source_owner"],
        "active_artifact_ownership": payload["active_artifact_ownership"],
        "active_source_revision_assessment": payload[
            "active_source_revision_assessment"
        ],
        "environment_observations": _bounded_architect_route_prompt_value(
            payload["environment_observations"],
            max_chars=48_000,
        ),
        "current_validated_plan": _bounded_architect_route_prompt_value(
            payload["current_validated_plan"],
            max_chars=6_000,
        ),
        "active_runtime_context": _bounded_architect_route_prompt_value(
            payload["active_runtime_context"],
            max_chars=8_000,
        ),
        "environment_feedback_fingerprint": payload[
            "environment_feedback_fingerprint"
        ],
        "routing_contract": payload["routing_contract"],
        "required_output": payload["required_output"],
    }
    return (
        "Choose one next evidence-producing owner as the existing AI Statistician "
        "ArchitectCoordinator. Do not regenerate the research plan or prescribe an "
        "implementation. The selected worker receives the complete unabridged feedback.\n\n"
        "Routing rules:\n"
        "1. Use CURRENT_ACTIVE_OBSERVATION; superseded observations are history unless "
        "the current artifact re-observes them. Treat current_validated_plan as prior "
        "intent and runtime_progress_snapshot as the authority for availability.\n"
        "2. current_source_owner identifies the artifact producer, not the cause. Route "
        "a source rewrite only to that exact owner; route an upstream dependency only "
        "when the observation and lineage support it. A consumer_source_owner field "
        "does not itself prove causation. Use active_artifact_ownership to distinguish "
        "the current observation source from upstream dependency identities. Content "
        "implemented inside the current source, including its DGP, stress test, metric "
        "calculation, or simulation protocol, stays with current_observation_source; "
        "choose an upstream dependency owner only when the raw observation localizes "
        "the defect to that dependency's interface or output.\n"
        "3. Route missing mathematical assumptions, definitions, or derivations to "
        "TheoryDeveloper; route Lean elaboration, proof-state, and proof-source failures "
        "to FormalizationEvaluator. Lean must not substitute for missing upstream "
        "mathematics; candidate-source failures and missing proof dependencies are not "
        "theory defects.\n"
        "4. Never rerun an unchanged confirmatory source, weaken a frozen gate, or invent "
        "a repair, patch, correction, or adapter agent. A statistically non-diagnostic "
        "result does not justify a source or theory revision. Numbers in reviewer prose "
        "are not execution observations unless the supplied authority marks them as "
        "observed. When active_source_revision_assessment says the current source edit "
        "is sufficient or no parent artifact change is required, do not reinterpret "
        "source-budget exhaustion as a TheoryDeveloper defect; choose an available "
        "unvisited independent lane or BLOCK.\n"
        "5. Required evidence lanes are independent once their actual prerequisites "
        "exist. Before repeating a visited lane, prefer an available unvisited required "
        "lane unless the current observation establishes a missing mathematical "
        "prerequisite. Simulation and algorithm artifacts are not prerequisites for "
        "starting formalization.\n"
        "6. This decision materializes exactly one task; no lane runs in the background. "
        "CriticEvaluator is terminal and is allowed only when no routable required lane "
        "remains.\n"
        "7. Choose BLOCK only when no available subsystem can produce the next evidence. "
        "Return only one JSON object matching required_output.\n\n"
        + json.dumps(bounded_payload, separators=(",", ":"), default=str)
    )


def validate_architect_feedback_route_packet(
    packet: Mapping[str, Any],
    *,
    available_subsystems: tuple[str, ...] = ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS,
) -> list[str]:
    errors: list[str] = []
    decision = str(packet.get("decision", "") or "").strip()
    selected = str(packet.get("selected_subsystem", "") or "").strip()
    objective = str(packet.get("objective", "") or "").strip()
    rationale = str(packet.get("rationale", "") or "").strip()
    if decision not in {"ROUTE", "BLOCK"}:
        errors.append("decision must be ROUTE or BLOCK")
    if not rationale:
        errors.append("rationale must be nonempty")
    if decision == "ROUTE":
        if selected not in available_subsystems:
            errors.append("ROUTE requires one available selected_subsystem")
        if not objective:
            errors.append("ROUTE requires a nonempty objective")
    elif decision == "BLOCK":
        if selected != "NONE":
            errors.append("BLOCK requires selected_subsystem NONE")
        if objective:
            errors.append("BLOCK must leave objective empty")
    if str(packet.get("operation", "") or "") != ARCHITECT_FEEDBACK_ROUTE_OPERATION:
        errors.append("operation must identify the Architect feedback route")
    if not str(packet.get("environment_feedback_fingerprint", "") or ""):
        errors.append("environment_feedback_fingerprint must be nonempty")
    return errors


def _architect_feedback_route_subsystems(
    *,
    architect_context: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
) -> tuple[str, ...]:
    """Apply immutable lineage budgets to the model's route choices."""

    budget = architect_context.get("candidate_lineage_budget", {})
    available = list(ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS)
    unavailable: set[str] = set()
    failure = str(
        environment_feedback.get("failure_classification", "") or ""
    )
    if failure.endswith("_lineage_budget_exhausted"):
        exhausted_source = str(
            environment_feedback.get("source_subsystem", "") or ""
        )
        if exhausted_source:
            unavailable.add(exhausted_source)
    consumer_budget = environment_feedback.get(
        SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY,
        {},
    )
    if isinstance(consumer_budget, Mapping) and consumer_budget:
        revisions_used = _architect_gap_int(
            consumer_budget.get("revisions_used", 0), fallback=0
        )
        max_consumer_revisions = _architect_gap_int(
            consumer_budget.get("max_revisions", 0), fallback=0
        )
        consumer_budget_exhausted = bool(
            consumer_budget.get("budget_exhausted") is True
            or max_consumer_revisions <= 0
            or revisions_used >= max_consumer_revisions
        )
        source_owner = environment_feedback.get("consumer_source_owner", {})
        source_owner = source_owner if isinstance(source_owner, Mapping) else {}
        exhausted_owner = str(
            source_owner.get("source_owner_subsystem", "") or ""
        ).strip()
        if consumer_budget_exhausted and exhausted_owner:
            unavailable.add(exhausted_owner)
    revisions_used, max_revisions = runtime_theory_revision_budget(
        architect_context
    )
    reserved_preexecution_revision = bool(
        environment_feedback.get("artifact_kind")
        == METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND
        and revisions_used > 0
        and revisions_used
        == _architect_gap_int(
            environment_feedback.get("upstream_theory_revision_count", 0),
            fallback=0,
        )
        and revisions_used <= max_revisions
    )
    if (
        max_revisions <= 0
        or (
            revisions_used >= max_revisions
            and not reserved_preexecution_revision
        )
    ):
        available = [
            subsystem
            for subsystem in available
            if subsystem != "TheoryDeveloper"
        ]
    if isinstance(budget, Mapping):
        feedback_id = str(
            environment_feedback.get("active_observation_id", "")
            or environment_feedback.get("feedback_id", "")
            or ""
        )
        budget_feedback_id = str(budget.get("feedback_id", "") or "")
        same_observation = bool(
            (feedback_id and budget_feedback_id == feedback_id)
            or (
                not budget_feedback_id
                and failure
                == str(budget.get("failure_classification", "") or "")
            )
        )
        attempts_used = _architect_gap_int(
            budget.get("attempts_used", 0), fallback=0
        )
        max_attempts = _architect_gap_int(
            budget.get("max_attempts", 0), fallback=0
        )
        exhausted = bool(
            budget.get("budget_exhausted") is True
            or (max_attempts > 0 and attempts_used >= max_attempts)
        )
        if same_observation and exhausted:
            exhausted_source = str(
                budget.get("source_subsystem", "") or ""
            )
            unavailable.add(exhausted_source)

    latest_outcome_by_owner: dict[str, Mapping[str, Any]] = {}
    for raw_outcome in architect_context.get(
        "runtime_outer_graph_workspace_outcomes", []
    ) or []:
        if not isinstance(raw_outcome, Mapping):
            continue
        owner = str(raw_outcome.get("source_subsystem", "") or "")
        if owner:
            latest_outcome_by_owner[owner] = raw_outcome
    for owner, outcome in latest_outcome_by_owner.items():
        parent_ids = outcome.get("parent_artifact_ids", {})
        if (
            str(outcome.get("local_status", "") or "") not in {"BLOCKED", "FAILED"}
            or not isinstance(parent_ids, Mapping)
            or not parent_ids
        ):
            continue
        same_parent_lineage = all(
            str(architect_context.get(str(field), "") or "") == str(value or "")
            for field, value in parent_ids.items()
            if str(value or "")
        )
        if same_parent_lineage:
            unavailable.add(owner)

    if (
        _architect_context_requires_accepted_algorithm_handoff(
            architect_context
        )
        and not _architect_context_has_accepted_algorithm_handoff(
            architect_context
        )
    ):
        unavailable.add("SimulationEvaluator")

    progress = architect_context.get("runtime_progress_snapshot", {})
    inventory = progress.get("evidence_lane_inventory", {}) if isinstance(
        progress, Mapping
    ) else {}
    remaining_primary = (
        inventory.get("remaining_primary_subsystems", [])
        if isinstance(inventory, Mapping)
        else []
    )
    if any(
        str(subsystem) in available and str(subsystem) not in unavailable
        for subsystem in remaining_primary
    ):
        unavailable.add("CriticEvaluator")

    return tuple(
        subsystem
        for subsystem in available
        if subsystem not in unavailable
    )


def _architect_context_has_accepted_algorithm_handoff(
    architect_context: Mapping[str, Any],
) -> bool:
    handoff = architect_context.get("upstream_algorithm_handoff", {})
    return bool(
        isinstance(handoff, Mapping)
        and str(handoff.get("handoff_id", "") or "").startswith(
            "accepted_algorithm_handoff:"
        )
        and list(handoff.get("exact_algorithm_artifacts", []) or [])
    )


def _architect_context_requires_accepted_algorithm_handoff(
    architect_context: Mapping[str, Any],
) -> bool:
    plan = architect_context.get("architect_runtime_plan", {})
    contract = plan.get("evidence_contract", {}) if isinstance(plan, Mapping) else {}
    return bool(
        isinstance(contract, Mapping)
        and contract.get("metric_protocol_execution_authorized") is True
        and contract.get(
            "research_evaluation_requires_generated_algorithm_code"
        )
        is True
    )


def _bounded_architect_route_prompt_value(
    value: Any,
    *,
    depth: int = 0,
    max_chars: int = 24_000,
) -> Any:
    """Bound transport size without interpreting diagnostics or choosing a route."""

    return _bounded_architect_route_prompt_value_with_budget(
        value,
        depth=depth,
        remaining=[max(1, int(max_chars))],
    )


def _bounded_architect_route_prompt_value_with_budget(
    value: Any,
    *,
    depth: int,
    remaining: list[int],
) -> Any:
    if remaining[0] <= 0:
        return "[routing-view-truncated; selected worker receives complete artifact]"

    if depth >= 7:
        remaining[0] -= 15
        return "[depth-limited]"
    if isinstance(value, Mapping):
        rows = list(value.items())
        bounded: dict[str, Any] = {}
        for key, child in rows:
            if remaining[0] <= 0:
                break
            key_text = str(key)
            remaining[0] -= len(key_text)
            bounded[key_text] = _bounded_architect_route_prompt_value_with_budget(
                child,
                depth=depth + 1,
                remaining=remaining,
            )
        if len(bounded) < len(rows):
            bounded["_omitted_mapping_items"] = len(rows) - len(bounded)
        return bounded
    if isinstance(value, (list, tuple)):
        rows = list(value)
        bounded_rows: list[Any] = []
        for child in rows[:24]:
            if remaining[0] <= 0:
                break
            bounded_rows.append(
                _bounded_architect_route_prompt_value_with_budget(
                    child,
                    depth=depth + 1,
                    remaining=remaining,
                )
            )
        if len(rows) > 24:
            bounded_rows.append({"_omitted_sequence_items": len(rows) - 24})
        return bounded_rows
    if isinstance(value, str):
        text = value if len(value) <= 1600 else value[:1597] + "..."
        allowed = max(0, min(len(text), remaining[0]))
        remaining[0] -= allowed
        if allowed < len(text):
            return text[: max(0, allowed - 3)] + "..." if allowed >= 3 else ""
        return text
    if isinstance(value, (int, float, bool)) or value is None:
        remaining[0] -= len(str(value))
        return value
    text = str(value)[:1600]
    allowed = max(0, min(len(text), remaining[0]))
    remaining[0] -= allowed
    return text[:allowed]


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
    preflight = dict(preflight) if isinstance(preflight, Mapping) else {}
    packet_id = str(
        preflight.get("packet_id", "")
        or metric_authoring_packet.get(
            "theory_execution_preflight_packet_id", ""
        )
        or ""
    )
    if not packet_id:
        return {}
    return {
        "packet_id": packet_id,
        "packet_hash": str(
            metric_authoring_packet.get(
                "theory_execution_preflight_packet_hash", ""
            )
            or ""
        ),
        "source_theory_packet_id": str(
            preflight.get("source_theory_packet_id", "")
            or metric_authoring_packet.get("source_theory_packet_id", "")
            or ""
        ),
        "source_theory_packet_hash": str(
            preflight.get("source_theory_packet_hash", "")
            or metric_authoring_packet.get("source_theory_packet_hash", "")
            or ""
        ),
        "overall_verdict": str(
            preflight.get("overall_verdict", "") or "ACCEPT"
        ),
        "model": str(
            preflight.get("model", "")
            or metric_authoring_packet.get(
                "theory_execution_preflight_model", ""
            )
            or ""
        ),
        "model_tier": str(
            preflight.get("model_tier", "")
            or metric_authoring_packet.get(
                "theory_execution_preflight_model_tier", ""
            )
            or ""
        ),
        "structured_output_retry_attempts": int(
            preflight.get("structured_output_retry_attempts", 0)
            or metric_authoring_packet.get(
                "theory_execution_preflight_retry_attempts", 0
            )
            or 0
        ),
        "n_findings": len(preflight.get("findings", []) or []),
        "proof_evidence_status": str(
            preflight.get("proof_evidence_status", "")
            or metric_authoring_packet.get(
                "theory_execution_preflight_proof_evidence_status", ""
            )
            or ""
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
    history = packet.get("structured_output_retry_history", [])
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
        "structured_output_retry_attempts": int(
            packet.get("structured_output_retry_attempts", 0) or 0
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
        "research_path_semantics": {
            "simulation_first": (
                "attempt the empirical implementation/simulation lane before the "
                "formal lane when the accepted theory supports it"
            ),
            "proof_first": (
                "after theory review, schedule FormalizationEvaluator before "
                "AlgorithmEngineer or SimulationEvaluator unless a concrete missing "
                "mathematical prerequisite blocks formalization; empirical artifacts "
                "are not prerequisites"
            ),
            "dual_track": (
                "interleave empirical and formal evidence by scheduling one real task "
                "now and the other on a later Architect turn; neither lane is a "
                "prerequisite for starting the other"
            ),
        },
    }
    model_architect_context = withhold_confirmatory_evaluation_seed(
        architect_observations_without_runtime_routing(architect_context)
    )
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "architect_context": model_architect_context,
        "runtime_config": withhold_confirmatory_evaluation_seed(
            runtime_config,
            parent_key="runtime_config",
        ),
        "available_subsystems": list(ARCHITECT_RUNTIME_SUBSYSTEMS),
        "orchestration_contract": {
            "model_owns": (
                "research analysis, lane choice, retrieval priorities, mathematical "
                "targets, and exactly one next workspace action"
            ),
            "runtime_owns": (
                "required workspace topology, evidence authority, budgets, artifact "
                "lineage, execution, and terminal verification"
            ),
            "planning_rule": (
                "Do not enumerate a global subsystem schedule. Choose one next "
                "workspace action; later routing decisions will use fresh artifacts "
                "and raw environment observations. Same-workspace iteration happens "
                "inside that model-owned workspace."
            ),
            "resume_rule": (
                "on a genuine cross-workspace replan, choose one next workspace from "
                "the current evidence rather than regenerating the whole graph"
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
        "Use the question, current workspace artifacts, raw environment observations, "
        "and reviewer findings to choose the research plan and next subsystem. "
        "Treat feedback as evidence for your own reasoning, not as a Python-authored "
        "edit recipe. When a model-authored artifact is rejected, route the complete "
        "artifact and exact observations to its owning model for full regeneration; "
        "do not prescribe a field-level patch or synthesize replacement content. "
        "Obey orchestration_contract, requested_evidence_contract, and the evidence "
        "boundary. Preserve accepted targets, artifact identities, hashes, frozen gates, "
        "and lineage. Empirical metric requirements are authored by their dedicated "
        "model after theory and implementation context exists, so do not duplicate them. "
        "Keep analysis inside the JSON "
        "fields, and do not include Markdown, code, claimed executions, simulation "
        "results, or proof claims. Do not route a theory artifact through the global "
        "Critic merely to "
        "review it before coding or formalization; the independent theory preflight "
        "already owns that local review.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


def _architect_gap_int(value: Any, *, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


ARCHITECT_COORDINATOR_SYSTEM_PROMPT = """\
You are the top-level ArchitectCoordinator inside an AI Statistician AgentRuntime.

Analyze the open statistical research task, choose its research path and targets,
and select exactly one next specialized workspace action from current evidence.
Do not enumerate a global subsystem schedule or act as a routine message router.
Runtime owns mandatory evidence topology, budgets, artifact lineage, execution,
and authority gates. You are not the executor or verifier; keep proof, simulation,
retrieval, and sandbox evidence boundaries explicit.
"""


ARCHITECT_COORDINATOR_OUTPUT_CONTRACT: dict[str, Any] = {
    "problem_analysis": {
        "theorem_family": "one short string",
        "statistical_objects": ["one short string"],
        "assumption_dimensions": ["one short string"],
        "likely_analogy_classes": ["one short string"],
        "key_obstacles": ["one short string"],
        "missing_information": ["one short string"],
    },
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
    "retrieval_strategy": {
        "paper_queries": ["one short string"],
        "formal_source_queries": ["one short string"],
        "lean_rag_priorities": ["one short string"],
    },
    "iteration_policy": {
        "max_revision_rounds": "integer",
        "stop_conditions": ["one short string"],
    },
    "next_actions": [
        {"owner_agent": "RetrievalMemory", "action": "one short string", "acceptance_gate": "one short string"}
    ],
}


ARCHITECT_COORDINATOR_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "problem_analysis",
        "evidence_contract",
        "retrieval_strategy",
        "iteration_policy",
        "next_actions",
    ],
    "properties": {
        "problem_analysis": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "theorem_family",
                "statistical_objects",
                "assumption_dimensions",
                "likely_analogy_classes",
                "key_obstacles",
                "missing_information",
            ],
            "properties": {
                "theorem_family": {"type": "string"},
                "statistical_objects": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "assumption_dimensions": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 6,
                    "items": {"type": "string"},
                },
                "likely_analogy_classes": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "key_obstacles": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 5,
                    "items": {"type": "string"},
                },
                "missing_information": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 5,
                    "items": {"type": "string"},
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
                    "maxItems": 4,
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
                    "maxItems": 4,
                    "items": {"type": "string"},
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
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "formal_source_queries": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "lean_rag_priorities": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
            },
        },
        "iteration_policy": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "max_revision_rounds",
                "stop_conditions",
            ],
            "properties": {
                "max_revision_rounds": {"type": "integer", "minimum": 0},
                "stop_conditions": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 5,
                    "items": {"type": "string"},
                },
            },
        },
        "next_actions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["owner_agent", "action", "acceptance_gate"],
                "properties": {
                    "owner_agent": {
                        "type": "string",
                        "enum": list(ARCHITECT_RUNTIME_SUBSYSTEMS),
                    },
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
        "problem_analysis",
        "evidence_contract",
        "retrieval_strategy",
        "iteration_policy",
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
            "assumption_dimensions",
            "likely_analogy_classes",
            "key_obstacles",
            "missing_information",
        ):
            if problem_analysis.get(field) in (None, "", [], {}):
                errors.append(f"problem_analysis missing or empty field: {field}")
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
                "evidence_contract.research_evaluation_requires_typed_metric_contracts "
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
    planned_subsystem_sequence: list[str] = []
    for row in packet.get("subsystem_execution_plan", []) or []:
        if not isinstance(row, Mapping):
            errors.append("subsystem_execution_plan entries must be objects")
            continue
        subsystem = str(row.get("subsystem", "") or "").strip()
        if not subsystem:
            errors.append("subsystem_execution_plan entry missing subsystem")
            continue
        planned_subsystems.add(subsystem)
        planned_subsystem_sequence.append(subsystem)
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
    ) = _runtime_required_workspace_plan(
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


def _runtime_required_workspace_plan(
    *,
    evidence_contract: Mapping[str, Any],
) -> tuple[list[Any], dict[str, Any]]:
    """Build runtime-owned evidence topology without research content."""

    required_subsystems = _required_architect_plan_subsystems(evidence_contract)
    plan_rows = [
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
        for subsystem in required_subsystems
    ]
    provenance = {
        "artifact_kind": "ArchitectSubsystemExecutionPlanProvenance",
        "llm_authored_subsystems": [],
        "runtime_elaborated_subsystems": list(required_subsystems),
        "runtime_owns_required_workspace_topology": True,
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
        "formal_evaluation_requires_formal_target_semantic_review": bool(
            capability_eval
            and runtime_config.get(
                "formal_target_semantic_review_required", False
            )
        ),
        "formal_evaluation_requires_formalizer_lean_candidate": capability_eval,
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
        "formal_evaluation_exposes_proof_search_tool": (
            capability_eval
            and bool(runtime_config.get("proof_search_tool_available", False))
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
                "formal_evaluation_requires_formal_target_semantic_review"
            )
            is True
        ):
            required.add("FormalTargetSemanticReviewer")
        if (
            evaluation_mode == "capability_eval"
            and evidence_contract.get(
                "formal_evaluation_requires_formalizer_lean_candidate"
            )
            is True
        ):
            required.add("FormalizationEvaluator")
    if (
        evidence_contract.get("formal_required_for_final") is True
        or str(evidence_contract.get("formal_verification_policy", "") or "")
        == "required"
    ):
        required.add("FormalizationEvaluator")
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
