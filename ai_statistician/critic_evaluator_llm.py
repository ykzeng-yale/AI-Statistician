from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion


CRITIC_EVALUATOR_SCHEMA_VERSION = 1
CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE = "LLM_CRITIC_EVALUATOR_PROPOSAL_NOT_PROOF_EVIDENCE"
CRITIC_EVALUATOR_BOUNDARY = (
    "LLM CriticEvaluator packets are orchestration, boundary-audit, and learning "
    "proposals only. They do not promote retrieval hits, simulations, sandbox "
    "code, or LLM formalization plans to theorem proof evidence. Proof evidence "
    "requires explicit AXLE/local Lean/kernel verification records."
)


@dataclass(frozen=True)
class CriticEvaluatorConfig:
    model: str = ""
    model_tier: str = "haiku"
    max_tokens: int = 5000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1


class LLMCriticEvaluatorAgent:
    """Generator-backed critic for runtime trace review and learning proposals."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: CriticEvaluatorConfig = CriticEvaluatorConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def propose(
        self,
        *,
        question: OpenResearchQuestion,
        retrieval_manifest: Mapping[str, Any],
        theory_packet: Mapping[str, Any],
        simulation_manifest: Mapping[str, Any],
        algorithm_manifest: Mapping[str, Any],
        formalization_manifest: Mapping[str, Any],
        deterministic_agenda: list[Mapping[str, Any]],
        deterministic_learning_rows: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        user_prompt = build_critic_evaluator_prompt(
            question=question,
            retrieval_manifest=retrieval_manifest,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            algorithm_manifest=algorithm_manifest,
            formalization_manifest=formalization_manifest,
            deterministic_agenda=deterministic_agenda,
            deterministic_learning_rows=deterministic_learning_rows,
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        request = GeneratorRequest(
            system_prompt=CRITIC_EVALUATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=CRITIC_EVALUATOR_JSON_SCHEMA,
            metadata={
                "subsystem": "CriticEvaluator",
                "agent": "LLMCriticEvaluatorAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_critic_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_critic_evaluator_packet,
            validation_label="LLM CriticEvaluator packet",
            max_repair_attempts=self.config.max_repair_attempts,
        )


def build_critic_evaluator_prompt(
    *,
    question: OpenResearchQuestion,
    retrieval_manifest: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    algorithm_manifest: Mapping[str, Any],
    formalization_manifest: Mapping[str, Any],
    deterministic_agenda: list[Mapping[str, Any]],
    deterministic_learning_rows: list[Mapping[str, Any]],
) -> str:
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "runtime_artifacts": {
            "retrieval": _small_manifest(retrieval_manifest),
            "theory": _small_manifest(theory_packet),
            "simulation": _small_manifest(simulation_manifest),
            "algorithm": _small_manifest(algorithm_manifest),
            "formalization": _small_manifest(formalization_manifest),
        },
        "deterministic_next_action_agenda": [dict(row) for row in deterministic_agenda],
        "deterministic_learning_rows": [dict(row) for row in deterministic_learning_rows],
        "required_output_contract": CRITIC_EVALUATOR_OUTPUT_CONTRACT,
        "boundary": CRITIC_EVALUATOR_BOUNDARY,
    }
    return (
        "Review this AI Statistician runtime trace as the CriticEvaluator. Return ONLY JSON "
        "matching required_output_contract. Audit evidence boundaries, identify reroute priorities, "
        "propose learning rows, and propose frontier benchmark expansions. Do not promote any "
        "artifact to proof evidence; only AXLE/local Lean/kernel records can do that.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )


CRITIC_EVALUATOR_SYSTEM_PROMPT = """\
You are the LLM CriticEvaluator inside an AI Statistician AgentRuntime.

Your job is to critique the completed runtime trace, preserve evidence honesty,
suggest reroutes, extract learning signals, and recommend benchmark expansion.
You are a generator, not the authority gate. Do not claim theorem proof evidence.
"""


CRITIC_EVALUATOR_OUTPUT_CONTRACT: dict[str, Any] = {
    "evidence_boundary_audit": [
        {
            "artifact_id": "string",
            "evidence_type": "string",
            "boundary_ok": "boolean",
            "risk": "string",
            "required_followup": "string",
        }
    ],
    "reroute_recommendations": [
        {
            "owner_subsystem": "string",
            "trigger": "string",
            "action": "string",
            "priority": "low|medium|high",
            "acceptance_gate": "string",
        }
    ],
    "learning_updates": [
        {
            "learning_task": "string",
            "input_signal": "string",
            "target_behavior": "string",
            "negative_example": "string",
        }
    ],
    "benchmark_expansion_plan": [
        {
            "benchmark_item": "string",
            "capability_target": "string",
            "success_evidence": "string",
        }
    ],
    "kernel_evidence_requirements": ["string"],
    "critic_findings": [
        {"critic": "string", "finding": "string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "string", "acceptance_gate": "string"}
    ],
}


CRITIC_EVALUATOR_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "evidence_boundary_audit",
        "reroute_recommendations",
        "learning_updates",
        "benchmark_expansion_plan",
        "kernel_evidence_requirements",
        "critic_findings",
        "next_actions",
    ],
    "properties": {
        "evidence_boundary_audit": {"type": "array", "minItems": 1},
        "reroute_recommendations": {"type": "array", "minItems": 1},
        "learning_updates": {"type": "array", "minItems": 1},
        "benchmark_expansion_plan": {"type": "array", "minItems": 1},
        "kernel_evidence_requirements": {"type": "array", "minItems": 1},
        "critic_findings": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_critic_evaluator_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "evidence_boundary_audit",
        "reroute_recommendations",
        "learning_updates",
        "benchmark_expansion_plan",
        "kernel_evidence_requirements",
        "critic_findings",
        "next_actions",
    ):
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    if packet.get("proof_evidence_status") != CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE:
        errors.append("proof_evidence_status must preserve critic proposal boundary")
    if packet.get("kernel_verified") is not False:
        errors.append("LLM CriticEvaluator packet cannot set kernel_verified=true")
    if packet.get("full_frontier_theorem_proved") is not False:
        errors.append("LLM CriticEvaluator packet cannot set full_frontier_theorem_proved=true")
    for row in packet.get("evidence_boundary_audit", []) or []:
        if not isinstance(row, Mapping):
            errors.append("evidence_boundary_audit entries must be objects")
            continue
        if not str(row.get("artifact_id", "")).strip():
            errors.append("evidence_boundary_audit entry missing artifact_id")
    forbidden = _contains_forbidden_proof_claim(packet)
    if forbidden:
        errors.append(f"packet contains forbidden proof claim: {forbidden}")
    return sorted(set(errors))


def _normalize_critic_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    body = dict(payload)
    body["proof_evidence_status"] = CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE
    body["evidence_boundary"] = CRITIC_EVALUATOR_BOUNDARY
    body["kernel_verified"] = False
    body["full_frontier_theorem_proved"] = False
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
        "schema_version": CRITIC_EVALUATOR_SCHEMA_VERSION,
        "artifact_kind": "CriticEvaluatorProposalPacket",
        "packet_id": f"critic_evaluator_proposal:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMCriticEvaluatorAgent",
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


def _small_manifest(row: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "manifest_id",
        "packet_id",
        "artifact_kind",
        "counts",
        "proof_evidence_status",
        "simulation_passed",
        "n_executed",
        "n_passed",
        "promotion_ready",
        "full_frontier_theorem_proved",
        "boundary",
        "proof_evidence_boundary",
    )
    return {key: row.get(key) for key in keys if key in row}


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM CriticEvaluator")


def _contains_forbidden_proof_claim(value: Any) -> str:
    text = json.dumps(value, default=str).lower()
    forbidden = (
        "kernel_verified\": true",
        "full_frontier_theorem_proved\": true",
        "qed verified",
        "lean verified",
        "kernel verified theorem",
        "theorem proved",
    )
    for token in forbidden:
        if token in text:
            return token
    return ""
