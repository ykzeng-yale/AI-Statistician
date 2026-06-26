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
        environment_feedback: Mapping[str, Any] | None = None,
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
            environment_feedback=environment_feedback or {},
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
    environment_feedback: Mapping[str, Any] | None = None,
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
        "deterministic_next_action_agenda": _compact_rows(deterministic_agenda, limit=4),
        "deterministic_learning_rows": _compact_rows(deterministic_learning_rows, limit=4),
        "critic_environment_feedback": _compact_mapping(
            environment_feedback or {},
            limit=10,
        ),
        "required_output_contract": CRITIC_EVALUATOR_OUTPUT_CONTRACT,
        "boundary": CRITIC_EVALUATOR_BOUNDARY,
    }
    return (
        "Review this AI Statistician runtime trace as the CriticEvaluator. Return ONLY JSON "
        "matching required_output_contract. Include only required fields. Keep each list to exactly "
        "1 short object or 1 short string. Audit evidence boundaries and identify one reroute "
        "priority. Do not promote any "
        "artifact to proof evidence; only AXLE/local Lean/kernel records can do that.\n\n"
        "If deterministic context reports source_to_bridge_premise_derivation_required "
        "or SOURCE_TO_BRIDGE_PREMISE_DERIVATION_GAP, recommend a REVISE/reroute to "
        "TheoryDeveloper/Formalizer/ProofEngineer for the concrete premise targets. "
        "If deterministic context reports source_theorem_truth_table_feedback or "
        "RUNTIME_EVIDENCE_TRUTH_TABLE with source_theorem_kernel_verified=false, keep the "
        "verdict at REVISE unless the next action directly targets ProofEngineer/LeanProver "
        "or upstream premise repair; do not broaden retrieval as a substitute for the open "
        "source-theorem proof gate. "
        "Do not summarize that state as accepted theorem proof.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
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
            "trigger": "short string",
            "action": "short string",
            "priority": "low|medium|high",
            "acceptance_gate": "short string",
        }
    ],
    "critic_findings": [
        {"critic": "string", "finding": "short string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "short string", "acceptance_gate": "short string"}
    ],
}


CRITIC_EVALUATOR_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "evidence_boundary_audit",
        "reroute_recommendations",
        "critic_findings",
        "next_actions",
    ],
    "properties": {
        "evidence_boundary_audit": {"type": "array", "minItems": 1},
        "reroute_recommendations": {"type": "array", "minItems": 1},
        "learning_updates": {"type": "array"},
        "benchmark_expansion_plan": {"type": "array"},
        "kernel_evidence_requirements": {"type": "array"},
        "critic_findings": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_critic_evaluator_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "evidence_boundary_audit",
        "reroute_recommendations",
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
        "runtime_architect_control",
        "simulation_passed",
        "n_executed",
        "n_passed",
        "promotion_ready",
        "full_frontier_theorem_proved",
        "source_to_bridge_premise_derivation_required",
        "source_to_bridge_premise_derivation_pending_premise_names",
        "boundary",
        "proof_evidence_boundary",
    )
    compact: dict[str, Any] = {}
    for key in keys:
        if key not in row:
            continue
        value = row.get(key)
        if key == "runtime_architect_control" and isinstance(value, Mapping):
            compact[key] = _compact_runtime_architect_control(value)
            continue
        if isinstance(value, Mapping):
            compact[key] = {
                str(nested_key): _truncate_text(nested_value)
                for nested_key, nested_value in list(value.items())[:8]
            }
        else:
            compact[key] = _truncate_text(value)
    return compact


def _compact_runtime_architect_control(row: Mapping[str, Any]) -> dict[str, Any]:
    evidence_contract = (
        row.get("evidence_contract", {})
        if isinstance(row.get("evidence_contract", {}), Mapping)
        else {}
    )
    return {
        "formal_verification_policy": _truncate_text(
            row.get("formal_verification_policy", "")
            or evidence_contract.get("formal_verification_policy", "")
        ),
        "recommended_research_path": _truncate_text(
            row.get("recommended_research_path", "")
            or evidence_contract.get("recommended_research_path", "")
        ),
        "formal_required_for_final": bool(
            row.get("formal_required_for_final", False)
            or evidence_contract.get("formal_required_for_final", False)
        ),
        "acceptance_gate": _truncate_text(row.get("acceptance_gate", "")),
    }


def _compact_rows(rows: list[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for row in rows[:limit]:
        if not isinstance(row, Mapping):
            continue
        compact.append(
            {
                str(key): _truncate_text(value)
                for key, value in row.items()
                if key in {
                    "id",
                    "artifact_id",
                    "evidence_type",
                    "owner_subsystem",
                    "trigger",
                    "action",
                    "acceptance_gate",
                    "priority",
                    "learning_task",
                    "input_signal",
                    "input_summary",
                    "target_behavior",
                    "gap_reason",
                    "semantic_primitive_id",
                    "target_theorem_name",
                    "premise_name",
                    "premise_target_status",
                    "premise_target_type",
                    "premise_derivation_gap_kind",
                    "premise_derivation_gap_summary",
                    "premise_semantic_dependency_status",
                    "premise_semantic_dependency_requirements",
                    "runtime_queue_status",
                }
            }
        )
    return compact


def _compact_mapping(row: Mapping[str, Any], *, limit: int) -> dict[str, str]:
    compact: dict[str, str] = {}
    for index, (key, value) in enumerate(row.items()):
        if index >= limit:
            break
        compact[str(key)] = _truncate_text(value)
    return compact


def _truncate_text(value: Any, *, limit: int = 300) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)] + "...[truncated]"


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
