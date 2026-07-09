from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion


ARCHITECT_COORDINATOR_SCHEMA_VERSION = 1
ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE = "LLM_ARCHITECT_COORDINATOR_PROPOSAL_NOT_PROOF_EVIDENCE"
ARCHITECT_COORDINATOR_BOUNDARY = (
    "LLM ArchitectCoordinator packets are orchestration proposals only. They "
    "can choose subsystem order, evidence gates, retrieval priorities, and "
    "iteration policy, but they do not execute tools, validate simulations, "
    "or prove theorems. Runtime validators and AXLE/local Lean remain the "
    "authority gates."
)

FORMAL_VERIFICATION_POLICIES = frozenset(("required", "optional", "advisory"))
RESEARCH_PATH_POLICIES = frozenset(("simulation_first", "proof_first", "dual_track"))

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


@dataclass(frozen=True)
class ArchitectCoordinatorConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 5000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1


class LLMArchitectCoordinatorAgent:
    """Generator-backed top-level Architect/Coordinator proposal worker."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: ArchitectCoordinatorConfig = ArchitectCoordinatorConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def propose(
        self,
        *,
        question: OpenResearchQuestion,
        architect_context: Mapping[str, Any],
        runtime_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        user_prompt = build_architect_coordinator_prompt(
            question=question,
            architect_context=architect_context,
            runtime_config=runtime_config,
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
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
                "explicit_model_configured": bool(self.config.model),
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_architect_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=str(
                    response.metadata.get("effective_model_tier", "")
                    or self.config.model_tier
                ),
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_architect_coordinator_packet,
            validation_label="LLM ArchitectCoordinator packet",
            max_repair_attempts=self.config.max_repair_attempts,
        )


def build_architect_coordinator_prompt(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    runtime_config: Mapping[str, Any],
) -> str:
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "architect_context": dict(architect_context),
        "runtime_config": dict(runtime_config),
        "available_subsystems": [
            "RetrievalMemory",
            "TheoryDeveloper",
            "SimulationEvaluator",
            "AlgorithmEngineer",
            "FormalizationEvaluator",
            "CriticEvaluator",
        ],
        "authority_gates": [
            "schema validation for all LLM packets",
            "AgentRuntime owns shell/filesystem/simulation execution",
            "simulation evidence is empirical, not proof evidence",
            "algorithm sandbox evidence is not production promotion",
            "AXLE/local Lean/kernel evidence is required for theorem proof claims",
        ],
        "long_horizon_research_guidance": LONG_HORIZON_RESEARCH_GUIDANCE,
        "required_output_contract": ARCHITECT_COORDINATOR_OUTPUT_CONTRACT,
        "boundary": ARCHITECT_COORDINATOR_BOUNDARY,
    }
    return (
        "Act as the top-level ArchitectCoordinator for the AI Statistician runtime. "
        "Return ONLY one compact JSON object matching required_output_contract. The object "
        "must contain exactly the required top-level fields unless a field is needed for "
        "schema repair. Keep each list to at most 2 short strings or 1 short object. Do not "
        "include paragraphs, Markdown, LaTeX derivations, optional long-form analysis sections, "
        "or code. Route first to RetrievalMemory and leave detailed derivation to TheoryDeveloper. "
        "Do not execute tools, do not claim simulations ran, and do not claim proof evidence.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str)
    )


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
        "formal_verification_policy": "required|optional|advisory",
        "recommended_research_path": "simulation_first|proof_first|dual_track",
        "formal_required_for_final": "boolean",
        "simulation_required_for_final": "boolean",
        "must_disclose_formal_gaps": "boolean",
        "rationale": "one short string",
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
    "additionalProperties": True,
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
        "intake_assessment": {"type": "object"},
        "problem_analysis": {"type": "object"},
        "stat_knowledge_bank_plan": {"type": "object"},
        "literature_fair_comparison_plan": {"type": "array", "minItems": 1},
        "evidence_contract": {"type": "object"},
        "subsystem_execution_plan": {"type": "array", "minItems": 1},
        "retrieval_strategy": {"type": "object"},
        "iteration_policy": {"type": "object"},
        "evidence_gates": {"type": "array", "minItems": 1},
        "risk_register": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
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
    evidence_contract = packet.get("evidence_contract", {})
    if isinstance(evidence_contract, Mapping):
        formal_policy = str(
            evidence_contract.get("formal_verification_policy", "") or ""
        )
        research_path = str(evidence_contract.get("recommended_research_path", "") or "")
        if formal_policy not in FORMAL_VERIFICATION_POLICIES:
            errors.append(
                "evidence_contract.formal_verification_policy must be one of: "
                + ", ".join(sorted(FORMAL_VERIFICATION_POLICIES))
            )
        if research_path not in RESEARCH_PATH_POLICIES:
            errors.append(
                "evidence_contract.recommended_research_path must be one of: "
                + ", ".join(sorted(RESEARCH_PATH_POLICIES))
            )
        for field in (
            "formal_required_for_final",
            "simulation_required_for_final",
            "must_disclose_formal_gaps",
        ):
            if not isinstance(evidence_contract.get(field), bool):
                errors.append(f"evidence_contract.{field} must be boolean")
        if formal_policy == "required" and evidence_contract.get("formal_required_for_final") is not True:
            errors.append(
                "evidence_contract.formal_required_for_final must be true when formal_verification_policy=required"
            )
        if formal_policy in {"optional", "advisory"} and evidence_contract.get("must_disclose_formal_gaps") is not True:
            errors.append(
                "evidence_contract.must_disclose_formal_gaps must be true unless full formal verification is required and complete"
            )
        if not str(evidence_contract.get("rationale", "") or "").strip():
            errors.append("evidence_contract.rationale must be nonempty")
    elif evidence_contract in (None, "", [], {}):
        pass
    else:
        errors.append("evidence_contract must be an object")
    for row in packet.get("subsystem_execution_plan", []) or []:
        if not isinstance(row, Mapping):
            errors.append("subsystem_execution_plan entries must be objects")
            continue
        if not str(row.get("subsystem", "")).strip():
            errors.append("subsystem_execution_plan entry missing subsystem")
    forbidden = _contains_forbidden_claim(packet)
    if forbidden:
        errors.append(f"packet contains forbidden execution/proof claim: {forbidden}")
    return sorted(set(errors))


def _normalize_architect_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    body = dict(payload)
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
