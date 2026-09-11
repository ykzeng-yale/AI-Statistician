from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

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
    GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES,
    generated_metric_requirement_set_id,
    generated_metric_shared_runtime_replicates,
    generated_sandbox_runtime_replicates,
    validate_generated_metric_requirements,
)
from .packet_validation import PacketValidationError, extract_json_object
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PHASE_NOT_REQUIRED,
    METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED,
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
    METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING,
    METRIC_PROTOCOL_PHASES,
    metric_protocol_authority_matches_theory,
    theory_informed_metric_protocol_material,
)
from .model_backend import (
    GeneratorBackend,
    GeneratorRequest,
    GeneratorResponse,
    resolve_generator_model,
)
from .research_schema import (
    OpenResearchQuestion,
    RESEARCH_EVIDENCE_DIMENSIONS,
    TASK_INTENT_REQUIREMENTS,
    research_dimension_requirements,
    research_question_payload,
)
from .scientific_code_workspace import (
    SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY,
)
from .theory_revision_lineage import (
    RUNTIME_THEORY_REVISION_PROGRESS_CONTEXT_KEY,
    runtime_theory_revision_count,
)


ARCHITECT_COORDINATOR_SCHEMA_VERSION = 2
ARCHITECT_CONTROL_ENVELOPE_TRANSPORT = (
    "provider_structured_output_single_call_v1"
)
ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE = "LLM_ARCHITECT_COORDINATOR_PROPOSAL_NOT_PROOF_EVIDENCE"
ARCHITECT_COORDINATOR_BOUNDARY = (
    "LLM ArchitectCoordinator packets are orchestration proposals only. They "
    "can choose unfrozen evidence dimensions, the research path, mathematical "
    "targets, retrieval priorities, and one next workspace action. Runtime owns "
    "operator-frozen task intent, mandatory "
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
ARCHITECT_WORKSPACE_CAPABILITIES = {
    "RetrievalMemory": "task-bound paper, statistical, and formal-source retrieval",
    "TheoryDeveloper": (
        "persistent Markdown/LaTeX theory, source discovery, exact published-source "
        "execution and replication reporting, and exploratory Python/R scratch"
    ),
    "AlgorithmEngineer": "model-owned Python/R source with direct sandbox feedback",
    "SimulationEvaluator": (
        "model-owned simulation source, exploratory diagnostics, and frozen "
        "confirmatory execution"
    ),
    "GeneratedCodeSemanticReviewer": "independent review of exact executed source",
    "FormalizationEvaluator": (
        "model-owned Lean source with declaration search, proof state, and compiler feedback"
    ),
    "FormalTargetSemanticReviewer": "independent review of the exact formal statement",
    "CriticEvaluator": "terminal multidimensional evidence and gap assessment",
}


def _architect_available_subsystems(
    architect_context: Mapping[str, Any],
) -> tuple[str, ...]:
    raw = architect_context.get("runtime_available_subsystems", ())
    allowed = (
        set(map(str, raw))
        if isinstance(raw, (list, tuple, set)) and raw
        else set(ARCHITECT_RUNTIME_SUBSYSTEMS)
    )
    return tuple(
        subsystem for subsystem in ARCHITECT_RUNTIME_SUBSYSTEMS
        if subsystem in allowed
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
    metric_semantic_reviewer_model: str = ""
    metric_semantic_reviewer_model_tier: str = "sonnet"
    metric_semantic_reviewer_max_tokens: int = 7000
    metric_semantic_reviewer_max_revisions: int = 1


def _generate_single_architect_control_envelope(
    *,
    provider: GeneratorBackend,
    request: GeneratorRequest,
    build_packet: Callable[
        [Mapping[str, Any], GeneratorResponse, str], dict[str, Any]
    ],
    validate_packet: Callable[[Mapping[str, Any]], list[str]],
    validation_label: str,
) -> dict[str, Any]:
    """Generate exactly one Architect control envelope and fail closed."""

    response = provider.generate(request)
    raw_text = response.text
    payload: dict[str, Any] | None = None
    packet: dict[str, Any] | None = None
    try:
        payload = _extract_json_object(raw_text)
        packet = build_packet(payload, response, raw_text)
        errors = [str(error) for error in validate_packet(packet)]
    except Exception as exc:
        errors = [f"{type(exc).__name__}: {exc}"]
    if packet is None and not errors:
        errors = ["Architect control envelope was not built"]
    history = [
        {
            "attempt_index": 0,
            "provider": response.provider,
            "model": response.model,
            "ok": not errors,
            "errors": list(errors),
            "transport": ARCHITECT_CONTROL_ENVELOPE_TRANSPORT,
            "raw_response_fingerprint": stable_hash(raw_text),
            "response_text_chars": len(raw_text),
            "payload_extracted": payload is not None,
            "packet_built": packet is not None,
        }
    ]
    if packet is not None and not errors:
        packet["validation_errors"] = []
        packet["ok"] = True
        packet["control_envelope_transport"] = (
            ARCHITECT_CONTROL_ENVELOPE_TRANSPORT
        )
        packet["control_envelope_model_calls"] = 1
        return packet
    raise PacketValidationError(
        validation_label=validation_label,
        attempts=1,
        errors=errors,
        history=history,
        last_invalid_packet=packet,
    )


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
        preflight_research_sources: Any = None,
        preflight_research_source_discovery: Any = None,
        metric_protocol_workspace_root: Path | None = None,
    ) -> None:
        self.provider = provider
        self.config = config
        self.metric_protocol_workspace_root = metric_protocol_workspace_root
        self.metric_review_scratchpad = None
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
                    research_sources=preflight_research_sources,
                    research_source_discovery=(
                        preflight_research_source_discovery
                    ),
                )
            )

    def review_theory_execution_preflight(
        self,
        *,
        question: OpenResearchQuestion,
        architect_context: Mapping[str, Any],
        runtime_config: Mapping[str, Any],
        author_scratch_execution_refs: tuple[Mapping[str, Any], ...] = (),
        theory_scratchpad: Any = None,
        recovery_checkpoint: Mapping[str, Any] | None = None,
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
            author_scratch_execution_refs=author_scratch_execution_refs,
            theory_scratchpad=theory_scratchpad,
            recovery_checkpoint=recovery_checkpoint,
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
                    max_tokens=max(
                        self.config.max_tokens,
                        ArchitectMetricContractAuthoringConfig().max_tokens,
                    ),
                    model_tier=self.config.model_tier,
                    provider_name=self.config.provider_name,
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
                metric_protocol_workspace_root=(
                    self.metric_protocol_workspace_root
                ),
                theory_scratchpad=self.metric_review_scratchpad,
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
        available_subsystems = _architect_available_subsystems(
            effective_architect_context
        )
        request_schema = deepcopy(ARCHITECT_COORDINATOR_JSON_SCHEMA)
        owner_schema = request_schema["properties"]["next_actions"]["items"]
        owner_schema = owner_schema["properties"]["owner_agent"]
        owner_schema["enum"] = list(available_subsystems)
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
            schema=request_schema,
            metadata={
                "subsystem": "ArchitectCoordinator",
                "agent": "LLMArchitectCoordinatorAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
                "provider_structured_output": True,
                "control_envelope_transport": (
                    ARCHITECT_CONTROL_ENVELOPE_TRANSPORT
                ),
                "validation_regeneration_authorized": False,
                "available_subsystems": list(available_subsystems),
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
                "model_call_budget": 1,
                "packet_regeneration_authorized": False,
                "metric_protocol_authored": bool(metric_authoring_packet),
            },
        ):
            return _generate_single_architect_control_envelope(
                provider=self.provider,
                request=request,
                build_packet=build_packet,
                validate_packet=validate_architect_coordinator_packet,
                validation_label="LLM ArchitectCoordinator packet",
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
        terminal_gap_report_required = _architect_terminal_gap_report_required(
            architect_context=architect_context,
            environment_feedback=environment_feedback,
            available_subsystems=available_route_subsystems,
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
                "control_envelope_transport": (
                    ARCHITECT_CONTROL_ENVELOPE_TRANSPORT
                ),
                "validation_regeneration_authorized": False,
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
                "model_call_budget": 1,
                "packet_regeneration_authorized": False,
                "full_research_plan_regeneration": False,
            },
        ):
            return _generate_single_architect_control_envelope(
                provider=self.provider,
                request=request,
                build_packet=build_packet,
                validate_packet=lambda packet: validate_architect_feedback_route_packet(
                    packet,
                    available_subsystems=available_route_subsystems,
                    required_terminal_reporter=(
                        "CriticEvaluator" if terminal_gap_report_required else ""
                    ),
                ),
                validation_label="LLM Architect feedback-route packet",
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
            RUNTIME_THEORY_REVISION_PROGRESS_CONTEXT_KEY,
            "runtime_progress_snapshot",
            "architect_metric_protocol_gate",
        )
        if key in architect_context
    }
    active_runtime_context[RUNTIME_THEORY_REVISION_PROGRESS_CONTEXT_KEY] = {
        "revisions_used": runtime_theory_revision_count(architect_context),
        "continuation_budget_authority": "AgentRuntime.max_iterations",
        "reset_scope": "fresh_question_runtime_only",
    }
    active_runtime_context["active_artifact_refs"] = {
        str(key): deepcopy(value)
        for key, value in architect_context.items()
        if (
            (str(key).endswith("_id") or str(key).endswith("_hash"))
            and value not in (None, "", [], {})
        )
    }
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
    terminal_gap_report_required = _architect_terminal_gap_report_required(
        architect_context=architect_context,
        environment_feedback=environment_feedback,
        available_subsystems=available_route_subsystems,
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
        "question": research_question_payload(
            question,
            include_task_intent=True,
        ),
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
        "environment_observations": deepcopy(dict(environment_feedback)),
        "environment_feedback_fingerprint": stable_hash(dict(environment_feedback)),
        "terminal_gap_report_required": terminal_gap_report_required,
        "routing_contract": {
            "owner_selected_by_architect_model": True,
            "selected_worker_receives_complete_feedback": True,
            "current_source_owner_is_identity_not_causal_attribution": True,
            "selected_source_editor_must_own_the_target_artifact": True,
            "source_rewrite_stays_with_exact_source_owner": True,
            "source_only_review_cannot_be_reclassified_as_parent_defect": True,
            "confirmatory_unchanged_source_retry_is_forbidden": True,
            "outcome_informed_new_source_requires_fresh_cohort": True,
            "aggregate_confirmatory_failure_is_not_component_attribution": True,
            "outcome_only_failure_routes_to_gap_reporting": True,
            "required_terminal_gap_report_cannot_be_skipped_by_block": True,
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
        "terminal_gap_report_required": payload[
            "terminal_gap_report_required"
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
        "observed. Quote a frozen requirement's operator, threshold, lower, upper, and "
        "tolerance exactly from its authoritative row; never recompute or invent a gate "
        "from prose. If the frozen row's declared returned metric and numeric gate are "
        "already in conflicting coordinates, choose BLOCK because post-execution source "
        "or theory revision cannot repair an invalid frozen protocol. When "
        "an aggregate confirmatory gate fails without a component-specific executable "
        "diagnostic, intervention, compiler error, or independent reference mismatch, it "
        "falsifies only the current end-to-end candidate and does not identify an "
        "AlgorithmEngineer or TheoryDeveloper defect. If source execution and independent "
        "semantic review succeeded, route CriticEvaluator to report the unresolved "
        "empirical gap, or choose BLOCK when CriticEvaluator is unavailable; do not request "
        "an outcome-driven source rewrite. When "
        "active_source_revision_assessment says the current source edit "
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
        "remains. When terminal_gap_report_required is true, route CriticEvaluator; "
        "BLOCK would suppress required evidence reporting and is invalid.\n"
        "7. Choose BLOCK only when no available subsystem can produce the next evidence. "
        "Return only one JSON object matching required_output.\n\n"
        + json.dumps(bounded_payload, separators=(",", ":"), default=str)
    )


def validate_architect_feedback_route_packet(
    packet: Mapping[str, Any],
    *,
    available_subsystems: tuple[str, ...] = ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS,
    required_terminal_reporter: str = "",
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
    if required_terminal_reporter and not (
        decision == "ROUTE" and selected == required_terminal_reporter
    ):
        errors.append(
            "terminal evidence reporting requires ROUTE to "
            f"{required_terminal_reporter}"
        )
    if str(packet.get("operation", "") or "") != ARCHITECT_FEEDBACK_ROUTE_OPERATION:
        errors.append("operation must identify the Architect feedback route")
    if not str(packet.get("environment_feedback_fingerprint", "") or ""):
        errors.append("environment_feedback_fingerprint must be nonempty")
    return errors


def _architect_terminal_gap_report_required(
    *,
    architect_context: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
    available_subsystems: tuple[str, ...],
) -> bool:
    """Require the terminal reporter once no substantive evidence lane remains."""

    confirmatory_terminal = bool(
        environment_feedback.get("terminal_gap_reporting_required") is True
        or (
            environment_feedback.get("feedback_type")
            == "confirmatory_simulation_outcome"
            and environment_feedback.get("source_execution_valid") is True
            and environment_feedback.get("execution_results_observed") is True
            and environment_feedback.get("unchanged_source_retry_authorized")
            is False
        )
    )
    if not confirmatory_terminal or "CriticEvaluator" not in available_subsystems:
        return False
    progress = architect_context.get("runtime_progress_snapshot", {})
    inventory = (
        progress.get("evidence_lane_inventory", {})
        if isinstance(progress, Mapping)
        else {}
    )
    remaining_primary = (
        inventory.get("remaining_primary_subsystems", [])
        if isinstance(inventory, Mapping)
        else []
    )
    return not any(
        str(subsystem) in available_subsystems
        for subsystem in remaining_primary or []
    )


def _architect_feedback_route_subsystems(
    *,
    architect_context: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
) -> tuple[str, ...]:
    """Apply immutable lineage budgets to the model's route choices."""

    budget = architect_context.get("candidate_lineage_budget", {})
    configured = set(_architect_available_subsystems(architect_context))
    available = [
        subsystem for subsystem in ARCHITECT_FEEDBACK_ROUTE_SUBSYSTEMS
        if subsystem in configured
    ]
    unavailable: set[str] = set()
    failure = str(
        environment_feedback.get("failure_classification", "") or ""
    )
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
        "runtime_model_routed_theory_revision_resolution", {}
    )
    invalidation = architect_context.get(
        "architect_metric_protocol_authority_invalidation", {}
    )
    feedback_route = architect_context.get(
        "architect_feedback_route_decision", {}
    )
    routing = architect_context.get("architect_initial_routing", {})
    route_decision_id = str(
        feedback_route.get("route_decision_id", "")
        if isinstance(feedback_route, Mapping)
        else ""
    )
    feedback_fingerprint = str(
        resolution.get("source_feedback_fingerprint", "")
        if isinstance(resolution, Mapping)
        else ""
    )
    if not (
        isinstance(resolution, Mapping)
        and resolution.get("artifact_kind")
        == "RuntimeModelRoutedTheoryRevisionResolution"
        and resolution.get("resolution_status")
        == "CONSUMED_BY_MODEL_ROUTED_THEORY_REVISION"
        and resolution.get("execution_results_observed") is True
        and str(resolution.get("source_feedback_id", "") or "")
        and feedback_fingerprint
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
        and isinstance(feedback_route, Mapping)
        and feedback_route.get("artifact_kind")
        == "ArchitectFeedbackRouteDecision"
        and feedback_route.get("decision") == "ROUTE"
        and feedback_route.get("selected_subsystem") == "TheoryDeveloper"
        and route_decision_id
        and str(
            feedback_route.get("environment_feedback_fingerprint", "") or ""
        )
        == feedback_fingerprint
        and isinstance(routing, Mapping)
        and routing.get("artifact_kind") == "ArchitectInitialRoutingDecision"
        and routing.get("source") == "architect_feedback_route_model"
        and routing.get("requested_subsystem") == "TheoryDeveloper"
        and routing.get("selected_subsystem") == "TheoryDeveloper"
        and str(routing.get("architect_packet_id", "") or "")
        == route_decision_id
        and str(routing.get("environment_feedback_hash", "") or "")
        == feedback_fingerprint
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
    prior_theory_packet_hash = str(
        resolution.get("prior_theory_packet_hash", "") or ""
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
        and str(prior_review.get("source_theory_packet_hash", "") or "")
        == prior_theory_packet_hash
        and str(
            invalidation.get("prior_contract_source_theory_packet_id", "") or ""
        )
        == prior_theory_packet_id
        and str(
            invalidation.get("prior_contract_source_theory_packet_hash", "") or ""
        )
        == prior_theory_packet_hash
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
            resolution.get("source_review_execution_id", "") or ""
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
        "metric_protocol_workspace": deepcopy(
            dict(packet.get("metric_protocol_workspace", {}))
        )
        if isinstance(packet.get("metric_protocol_workspace"), Mapping)
        else {},
        "theory_execution_preflight": (
            _architect_theory_execution_preflight_summary(packet)
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
    runtime_owned_contract = _architect_runtime_owned_evidence_contract(
        architect_context=architect_context,
        runtime_config=runtime_config,
    )
    formal_verification_policy = str(
        runtime_owned_contract.get("formal_verification_policy", "optional")
        or "optional"
    )
    requested_evidence_contract = {
        **runtime_owned_contract,
        "requested_research_path": str(
            runtime_owned_contract.get("recommended_research_path", "")
            or runtime_config.get("recommended_research_path", "")
            or ""
        ),
        "formal_required_for_final": bool(
            runtime_owned_contract.get(
                "formal_required_for_final",
                formal_verification_policy == "required",
            )
        ),
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
        architect_context
    )
    available_subsystems = _architect_available_subsystems(architect_context)
    payload = {
        "question": {
            **research_question_payload(question, include_task_intent=False),
            "task_intent": deepcopy(runtime_owned_contract.get("dimension_requirements", {})),
        },
        "architect_context": model_architect_context,
        "runtime_config": withhold_confirmatory_evaluation_seed(
            runtime_config,
            parent_key="runtime_config",
        ),
        "available_subsystems": list(available_subsystems),
        "unavailable_subsystems": sorted(
            set(ARCHITECT_RUNTIME_SUBSYSTEMS) - set(available_subsystems)
        ),
        "workspace_capabilities": {
            subsystem: ARCHITECT_WORKSPACE_CAPABILITIES[subsystem]
            for subsystem in available_subsystems
        },
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
            "task_intent_rule": (
                "Honor question.task_intent exactly when supplied; it contains only "
                "operator-frozen dimensions. If empty, revise all four model-owned "
                "dimensions from current evidence. This plan is not evidence."
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
        "boundary": ARCHITECT_COORDINATOR_BOUNDARY,
    }
    return (
        "Act as the top-level ArchitectCoordinator for the AI Statistician runtime. "
        "Return only one compact JSON object matching the provider schema exactly. "
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
        "Keep analysis inside the structured response "
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
                    "items": {"type": "string"},
                },
                "assumption_dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "likely_analogy_classes": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "key_obstacles": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                },
                "missing_information": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "evidence_contract": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "dimension_requirements",
                "recommended_research_path",
                "formal_targets",
                "simulation_targets",
            ],
            "properties": {
                "dimension_requirements": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(RESEARCH_EVIDENCE_DIMENSIONS),
                    "properties": {
                        dimension: {
                            "type": "string",
                            "enum": sorted(TASK_INTENT_REQUIREMENTS),
                        }
                        for dimension in RESEARCH_EVIDENCE_DIMENSIONS
                    },
                },
                "recommended_research_path": {
                    "type": "string",
                    "enum": ["simulation_first", "proof_first", "dual_track"],
                },
                "formal_targets": {
                    "type": "array",
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
                "stop_conditions",
            ],
            "properties": {
                "stop_conditions": {
                    "type": "array",
                    "minItems": 1,
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
    dimension_requirements: dict[str, str] = {}
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
            if field not in problem_analysis:
                errors.append(f"problem_analysis missing field: {field}")
        for field in ("theorem_family", "statistical_objects", "key_obstacles"):
            if problem_analysis.get(field) in (None, "", [], {}):
                errors.append(f"problem_analysis missing or empty field: {field}")
    evaluation_mode = ""
    evidence_contract = packet.get("evidence_contract", {})
    if isinstance(evidence_contract, Mapping):
        explicit_dimension_requirements = evidence_contract.get(
            "dimension_requirements", {}
        )
        if not isinstance(explicit_dimension_requirements, Mapping):
            errors.append("evidence_contract.dimension_requirements must be an object")
        else:
            try:
                dimension_requirements = research_dimension_requirements(
                    explicit_dimension_requirements
                )
            except ValueError as exc:
                errors.append(str(exc))
        if set(dimension_requirements) != set(RESEARCH_EVIDENCE_DIMENSIONS):
            errors.append(
                "evidence_contract.dimension_requirements must resolve all "
                "research evidence dimensions"
            )
        source_replication_requirement = str(
            evidence_contract.get("source_replication_requirement", "optional")
            or "optional"
        )
        if source_replication_requirement not in TASK_INTENT_REQUIREMENTS:
            errors.append(
                "evidence_contract.source_replication_requirement must be required, "
                "optional, or not_applicable"
            )
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
        raw_typed_required = evidence_contract.get(
            "research_evaluation_requires_typed_metric_contracts"
        )
        raw_executable_evaluator_required = evidence_contract.get(
            "research_evaluation_requires_executable_evaluator_source"
        )
        typed_required = _research_evaluation_contract_flag(
            evidence_contract,
            "typed_metric_contracts",
        )
        executable_evaluator_required = _research_evaluation_contract_flag(
            evidence_contract,
            "executable_evaluator_source",
        )
        if raw_typed_required is not None and not isinstance(
            raw_typed_required, bool
        ):
            errors.append(
                "evidence_contract.research_evaluation_requires_typed_metric_contracts "
                "must be a boolean"
            )
        if raw_executable_evaluator_required is not None and not isinstance(
            raw_executable_evaluator_required, bool
        ):
            errors.append(
                "evidence_contract.research_evaluation_requires_executable_evaluator_source "
                "must be a boolean"
            )
        if (
            research_evaluation
            and _research_evaluation_contract_flag(
                evidence_contract,
                "generated_simulation_code",
            )
            and typed_required is not True
            and executable_evaluator_required is not True
        ):
            errors.append(
                "research evaluation with generated simulation requires either "
                "an executable evaluator source or the legacy typed metric protocol"
            )
        if authority_policy and authority_policy not in {
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED,
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
        }:
            errors.append(
                "evidence_contract.generated_metric_requirement_authority_policy "
                "must be architect-authored and coding-agent-bound"
            )
        if research_evaluation and typed_required is True and (
            metric_policy != "typed_artifact_bound_required"
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
        max_runtime_replicates = evidence_contract.get(
            "generated_sandbox_max_runtime_replicates"
        )
        if research_evaluation and typed_required is True and (
            isinstance(expected_runtime_replicates, bool)
            or not isinstance(expected_runtime_replicates, int)
            or expected_runtime_replicates <= 0
        ):
            errors.append(
                "research evaluation requires a positive pre-execution "
                "generated_sandbox_runtime_replicates value"
            )
        if research_evaluation and typed_required is True and (
            isinstance(max_runtime_replicates, bool)
            or not isinstance(max_runtime_replicates, int)
            or max_runtime_replicates <= 0
        ):
            errors.append(
                "research evaluation requires a positive sandbox replicate safety capacity"
            )
        if requirements not in (None, [], {}):
            if research_evaluation and typed_required is True and (
                metric_protocol_phase
                != METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED
                or metric_protocol_execution_authorized is not True
            ):
                errors.append(
                    "research-evaluation metric requirements authorize execution only "
                    "after independent pre-execution review acceptance"
                )
            if research_evaluation and typed_required is True:
                _shared_replicates, replicate_errors = (
                    generated_metric_shared_runtime_replicates(
                        [
                            dict(row)
                            for row in requirements
                            if isinstance(row, Mapping)
                        ],
                        max_runtime_replicates=(
                            max_runtime_replicates
                            if isinstance(max_runtime_replicates, int)
                            and not isinstance(max_runtime_replicates, bool)
                            else GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES
                        ),
                    )
                )
                errors.extend(replicate_errors)
            errors.extend(
                validate_generated_metric_requirements(
                    requirements,
                    required_target_subsystems=(
                        GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                    )
                    if research_evaluation and typed_required is True
                    else (),
                    expected_runtime_replicates=(
                        expected_runtime_replicates
                        if research_evaluation and typed_required is True
                        and isinstance(expected_runtime_replicates, int)
                        and not isinstance(expected_runtime_replicates, bool)
                        else None
                    ),
                )
            )
            if research_evaluation and typed_required is True:
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
        elif research_evaluation and typed_required is True:
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
        for field in ("acceptance_modes", "disclosure_requirements"):
            if evidence_contract.get(field) in (None, "", [], {}):
                errors.append(f"evidence_contract missing or empty field: {field}")
        target_requirements = {
            "formal_targets": bool(
                evidence_contract.get("formal_target_authoring_required") is True
            ),
            "simulation_targets": bool(
                evidence_contract.get("simulation_target_authoring_required") is True
            ),
        }
        for field, required in target_requirements.items():
            value = evidence_contract.get(field)
            if not isinstance(value, list):
                errors.append(f"evidence_contract.{field} must be a list")
            elif required and not value:
                errors.append(f"evidence_contract missing or empty field: {field}")
        if (
            dimension_requirements.get("formal") == "not_applicable"
            and evidence_contract.get("formal_targets")
        ):
            errors.append(
                "evidence_contract.formal_targets must be empty when formal evidence "
                "is not applicable"
            )
        if (
            dimension_requirements.get("empirical") == "not_applicable"
            and evidence_contract.get("simulation_targets")
        ):
            errors.append(
                "evidence_contract.simulation_targets must be empty when empirical "
                "evidence is not applicable"
            )
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
    raw_available = packet.get("available_subsystems", ())
    available_subsystems = (
        set(map(str, raw_available))
        if isinstance(raw_available, (list, tuple, set)) and raw_available
        else set(ARCHITECT_RUNTIME_SUBSYSTEMS)
    )
    for action in packet.get("next_actions", []) or []:
        owner = str(action.get("owner_agent", "") or "") if isinstance(action, Mapping) else ""
        if owner and owner not in available_subsystems:
            errors.append(f"next_actions selects unavailable subsystem: {owner}")
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
    errors.extend(
        "subsystem_execution_plan requires unavailable subsystem: " + subsystem
        for subsystem in sorted(planned_subsystems - available_subsystems)
    )
    for subsystem in _required_architect_plan_subsystems(evidence_contract):
        if subsystem not in planned_subsystems:
            errors.append(
                "subsystem_execution_plan missing evidence-contract-required "
                f"subsystem: {subsystem}"
            )
    formal_requirement = dimension_requirements.get("formal", "")
    if evaluation_mode == "research_eval" and formal_requirement != "required":
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
        "dimension_requirements",
        "disclosure_requirements",
        "evaluation_mode",
        "formal_target_authoring_required",
        "formal_target_completion_policy",
        "formal_evaluation_requires_formal_target_semantic_review",
        "formal_evaluation_requires_formalizer_lean_candidate",
        "independent_theory_review_required",
        "research_evaluation_requires_generated_algorithm_code",
        "research_evaluation_requires_generated_code_semantic_review",
        "research_evaluation_requires_generated_simulation_code",
        "research_evaluation_requires_executable_evaluator_source",
        "research_evaluation_requires_typed_metric_contracts",
        "recommended_research_path_frozen",
        "simulation_target_authoring_required",
        "source_replication_requirement",
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
    for field in tuple(evaluation_contract):
        if field in requested_contract:
            evaluation_contract[field] = requested_contract[field]
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
        requested_contract.get("formal_verification_policy", "")
        or config.get("formal_verification_policy", "")
        or "optional"
    ).strip().lower()
    contract["formal_verification_policy"] = policy
    contract["formal_required_for_final"] = policy == "required"
    requested_path = ""
    if requested_contract.get("recommended_research_path_frozen") is True:
        requested_path = str(
            requested_contract.get("recommended_research_path", "") or ""
        ).strip()
    elif isinstance(prior_contract, Mapping):
        requested_path = str(
            prior_contract.get("recommended_research_path", "") or ""
        ).strip()
    if requested_path:
        contract["recommended_research_path"] = requested_path
    contract.update(evaluation_contract)
    accepted_metric_rows = [
        dict(row)
        for row in contract.get("empirical_metric_requirements", []) or []
        if isinstance(row, Mapping)
    ]
    if accepted_metric_rows:
        reviewed_replicates, replicate_errors = (
            generated_metric_shared_runtime_replicates(
                accepted_metric_rows,
                max_runtime_replicates=int(
                    contract["generated_sandbox_max_runtime_replicates"]
                ),
            )
        )
        if reviewed_replicates is not None and not replicate_errors:
            contract["generated_sandbox_runtime_replicates"] = reviewed_replicates
            contract["generated_sandbox_runtime_replicates_source"] = (
                "accepted_model_authored_metric_requirements"
            )
    if not _research_evaluation_contract_flag(
        contract,
        "typed_metric_contracts",
    ):
        contract["generated_metric_contract_policy"] = (
            "typed_artifact_bound_preferred"
        )
        contract["generated_metric_requirement_authority_policy"] = (
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
        )
    strict_metric_protocol_required = _research_evaluation_contract_flag(
        contract,
        "typed_metric_contracts",
    )
    accepted_requirements = bool(contract.get("empirical_metric_requirements"))
    if not strict_metric_protocol_required:
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
    runtime_owned_contract = _architect_runtime_owned_evidence_contract(
        architect_context=architect_context,
        runtime_config=runtime_config,
    )
    normalized_contract.update(runtime_owned_contract)
    frozen_dimensions = runtime_owned_contract.get("dimension_requirements")
    raw_dimensions = frozen_dimensions if isinstance(frozen_dimensions, Mapping) else normalized_contract.get("dimension_requirements", {})
    dimension_requirements = research_dimension_requirements(raw_dimensions if isinstance(raw_dimensions, Mapping) else {})
    if dimension_requirements:
        operator_formal = not isinstance(frozen_dimensions, Mapping) and runtime_owned_contract.get("formal_required_for_final") is True
        if operator_formal:
            dimension_requirements["formal"] = "required"
        required = {key: value == "required" for key, value in dimension_requirements.items()}
        if isinstance(frozen_dimensions, Mapping):
            source = "operator_frozen_task_intent"
        elif operator_formal:
            source = "architect_model_plan_with_operator_formal_requirement"
        else:
            source = "architect_model_plan"
        normalized_contract.update({
            "dimension_requirements": dimension_requirements,
            "dimension_requirements_source": source,
            "independent_theory_review_required": required["theory"],
            "research_evaluation_requires_generated_algorithm_code": required["scientific_code"],
            "research_evaluation_requires_generated_simulation_code": required["empirical"],
            "research_evaluation_requires_generated_code_semantic_review": required["scientific_code"] or required["empirical"],
            "research_evaluation_requires_executable_evaluator_source": required["empirical"],
            "simulation_target_authoring_required": required["empirical"],
            "formal_target_authoring_required": required["formal"],
            "formal_evaluation_requires_formalizer_lean_candidate": required["formal"],
            "formal_evaluation_requires_formal_target_semantic_review": required["formal"] and bool((runtime_config or {}).get("formal_target_semantic_review_required", False)),
            "formal_required_for_final": required["formal"],
        })
        if required["formal"]:
            normalized_contract["formal_verification_policy"] = "required"
        for dimension, target in (("formal", "formal_targets"), ("empirical", "simulation_targets")):
            if dimension_requirements[dimension] == "not_applicable":
                normalized_contract[target] = []
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
    body["available_subsystems"] = list(
        _architect_available_subsystems(architect_context or {})
    )
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
            **research_question_payload(question, include_task_intent=False,
                                        include_estimator_execution_contract=False),
            "task_intent": deepcopy(runtime_owned_contract.get("dimension_requirements", {})),
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
    return {
        "evaluation_mode": evaluation_mode,
        "research_evaluation_requires_generated_algorithm_code": False,
        "research_evaluation_requires_generated_simulation_code": False,
        "research_evaluation_requires_generated_code_semantic_review": False,
        "research_evaluation_requires_executable_evaluator_source": False,
        "research_evaluation_requires_typed_metric_contracts": False,
        "formal_evaluation_requires_formal_target_semantic_review": False,
        "formal_evaluation_requires_formalizer_lean_candidate": False,
        "generated_sandbox_runtime_replicates": (
            generated_sandbox_runtime_replicates(
                int(runtime_config.get("n_runs", 100) or 100)
            )
        ),
        "generated_sandbox_max_runtime_replicates": (
            GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES
        ),
        "generated_simulation_timeout_seconds": max(
            1,
            int(runtime_config.get("generated_simulation_timeout_seconds", 60) or 60),
        ),
        "generated_metric_contract_policy": (
            "typed_artifact_bound_preferred"
        ),
        "generated_metric_requirement_authority_policy": (
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
        ),
        "formal_evaluation_exposes_proof_search_tool": (
            bool(runtime_config.get("proof_search_tool_available", False))
        ),
    }


def _required_architect_plan_subsystems(
    evidence_contract: Mapping[str, Any],
) -> tuple[str, ...]:
    required: set[str] = set()
    evaluation_mode = str(evidence_contract.get("evaluation_mode", "") or "")
    if evaluation_mode in RESEARCH_EVALUATION_MODES:
        required.add("CriticEvaluator")
        dimensions = evidence_contract.get("dimension_requirements", {})
        if (
            not isinstance(dimensions, Mapping)
            or not dimensions
            or evidence_contract.get("independent_theory_review_required") is True
            or evidence_contract.get("source_replication_requirement") == "required"
        ):
            required.update(("RetrievalMemory", "TheoryDeveloper"))
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
        if evidence_contract.get(
            "formal_evaluation_requires_formal_target_semantic_review"
        ) is True:
            required.add("FormalTargetSemanticReviewer")
        if evidence_contract.get(
            "formal_evaluation_requires_formalizer_lean_candidate"
        ) is True:
            required.add("FormalizationEvaluator")
    if (
        evidence_contract.get("formal_required_for_final") is True
        or str(evidence_contract.get("formal_verification_policy", "") or "")
        == "required"
    ):
        required.add("FormalizationEvaluator")
    if evidence_contract.get("source_replication_requirement") == "required":
        required.update(("RetrievalMemory", "TheoryDeveloper"))
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
