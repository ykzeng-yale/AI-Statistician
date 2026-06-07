from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .llm_json_repair import generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, default_generator_model
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
    model: str = default_generator_model("anthropic", model_tier="sonnet")
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
        request = GeneratorRequest(
            system_prompt=ARCHITECT_COORDINATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=ARCHITECT_COORDINATOR_JSON_SCHEMA,
            metadata={"subsystem": "ArchitectCoordinator", "agent": "LLMArchitectCoordinatorAgent"},
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_architect_packet(
                payload,
                question=question,
                model=response.model or self.config.model,
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
        "Return ONLY JSON matching required_output_contract. Start with problem analysis, "
        "then define the execution graph, subsystem priorities, dynamic knowledge-bank plan, "
        "literature fair-comparison gate, retrieval/search strategy, iteration policy, and "
        "evidence gates. Do not execute tools, do not claim simulations ran, and do not claim "
        "proof evidence.\n\n"
        + json.dumps(payload, indent=2, default=str)
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
        "primary_success_criteria": ["string"],
        "known_risks": ["string"],
    },
    "subsystem_execution_plan": [
        {
            "subsystem": "string",
            "objective": "string",
            "inputs_needed": ["string"],
            "expected_artifacts": ["string"],
            "acceptance_gate": "string",
        }
    ],
    "retrieval_strategy": {
        "paper_queries": ["string"],
        "formal_source_queries": ["string"],
        "lean_rag_priorities": ["string"],
    },
    "problem_analysis": {
        "theorem_family": "string",
        "statistical_objects": ["string"],
        "likely_analogy_classes": ["string"],
        "key_obstacles": ["string"],
        "missing_information": ["string"],
    },
    "stat_knowledge_bank_plan": {
        "source_families_to_collect": ["string"],
        "assumption_dimensions": ["string"],
        "proof_skeletons_to_track": ["string"],
        "failed_attempt_memory_policy": "string",
    },
    "literature_fair_comparison_plan": [
        {
            "candidate_source_family": "string",
            "must_match": ["string"],
            "likely_mismatches": ["string"],
            "unsafe_transfer_risks": ["string"],
        }
    ],
    "iteration_policy": {
        "reroute_triggers": ["string"],
        "max_repair_rounds": "integer",
        "stop_conditions": ["string"],
    },
    "evidence_gates": [
        {"artifact_kind": "string", "required_evidence": "string", "not_evidence": "string"}
    ],
    "risk_register": [
        {"risk": "string", "mitigation": "string", "owner_subsystem": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "string", "acceptance_gate": "string"}
    ],
}


ARCHITECT_COORDINATOR_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "intake_assessment",
        "subsystem_execution_plan",
        "retrieval_strategy",
        "iteration_policy",
        "evidence_gates",
        "risk_register",
        "next_actions",
    ],
    "properties": {
        "intake_assessment": {"type": "object"},
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
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            raise
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("expected JSON object from LLM ArchitectCoordinator")
    return payload


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
