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


FORMALIZER_SCHEMA_VERSION = 1
FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE = "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE"
FORMALIZER_BOUNDARY = (
    "LLM Formalizer/ProofEngineer packets are formalization and proof-search "
    "proposals only. They do not count as Lean proof evidence, do not certify "
    "source theorem faithfulness, and cannot claim kernel verification. Proof "
    "evidence requires AgentRuntime to run AXLE/local Lean/kernel verification "
    "on the intended formal claim."
)


@dataclass(frozen=True)
class FormalizerConfig:
    model: str = default_generator_model("anthropic", model_tier="sonnet")
    max_tokens: int = 6000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1


class LLMFormalizerProofEngineerAgent:
    """Generator-backed Formalizer/ProofEngineer proposal worker."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: FormalizerConfig = FormalizerConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def propose(
        self,
        *,
        question: OpenResearchQuestion,
        theory_packet: Mapping[str, Any],
        simulation_manifest: Mapping[str, Any],
        algorithm_manifest: Mapping[str, Any],
        registered_problem: Mapping[str, Any],
        theorem_goals: list[Mapping[str, Any]],
        proof_bank_obligation_catalog: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        user_prompt = build_formalizer_prompt(
            question=question,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            algorithm_manifest=algorithm_manifest,
            registered_problem=registered_problem,
            theorem_goals=theorem_goals,
            proof_bank_obligation_catalog=proof_bank_obligation_catalog,
        )
        request = GeneratorRequest(
            system_prompt=FORMALIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=FORMALIZER_JSON_SCHEMA,
            metadata={"subsystem": "FormalizerProofEngineer", "agent": "LLMFormalizerProofEngineerAgent"},
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_formalizer_packet(
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
            validate_packet=validate_formalizer_packet,
            validation_label="LLM Formalizer/ProofEngineer packet",
            max_repair_attempts=self.config.max_repair_attempts,
        )


def build_formalizer_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    algorithm_manifest: Mapping[str, Any],
    registered_problem: Mapping[str, Any],
    theorem_goals: list[Mapping[str, Any]],
    proof_bank_obligation_catalog: list[Mapping[str, Any]] | None = None,
) -> str:
    catalog_rows = [
        dict(row)
        for row in (proof_bank_obligation_catalog or _proof_bank_catalog_from_theorem_goals(theorem_goals))
        if isinstance(row, Mapping)
    ]
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "theory_packet_summary": {
            "packet_id": theory_packet.get("packet_id", ""),
            "theorem_cards": theory_packet.get("theorem_cards", []),
            "lemma_cards": theory_packet.get("lemma_cards", []),
            "proof_plan": theory_packet.get("proof_plan", {}),
            "formalization_requests": theory_packet.get("formalization_requests", []),
        },
        "simulation_manifest_summary": {
            "manifest_id": simulation_manifest.get("manifest_id", ""),
            "simulation_passed": simulation_manifest.get("simulation_passed"),
            "proof_evidence_status": simulation_manifest.get("proof_evidence_status", ""),
        },
        "algorithm_manifest_summary": {
            "manifest_id": algorithm_manifest.get("manifest_id", ""),
            "n_executed": algorithm_manifest.get("n_executed", 0),
            "promotion_ready": algorithm_manifest.get("promotion_ready", False),
        },
        "registered_problem": dict(registered_problem),
        "registered_theorem_goals": [dict(row) for row in theorem_goals],
        "registered_proof_bank_obligation_catalog": catalog_rows,
        "proof_bank_obligation_request_policy": {
            "use_only_registered_catalog_ids_when_possible": True,
            "request_effect": "priority_only_for_kernel_smoke_selection",
            "runtime_filter": "AgentRuntime rejects unknown obligation IDs and filters against the current candidate set",
            "not_evidence": "A proof-bank obligation request is not Lean proof evidence and does not prove the frontier theorem.",
        },
        "required_output_contract": FORMALIZER_OUTPUT_CONTRACT,
        "boundary": FORMALIZER_BOUNDARY,
    }
    return (
        "Design formalization and proof-search artifacts for the Formalizer/ProofEngineer subsystem. "
        "Return ONLY JSON matching required_output_contract. You may propose Lean statement sketches, "
        "lemma dependency plans, source retrieval queries, and kernel-check work orders, but do not claim "
        "the theorem is proved, do not claim kernel verification, and do not hide formal gaps. "
        "For proof_bank_obligation_requests, choose obligation_id values from "
        "registered_proof_bank_obligation_catalog when possible; these requests only prioritize "
        "AgentRuntime kernel-smoke work and may be filtered or rejected by the runtime.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )


FORMALIZER_SYSTEM_PROMPT = """\
You are the LLM Formalizer/ProofEngineer inside an AI Statistician AgentRuntime.

Your job is to translate statistical theorem proposals into Lean target plans,
dependency DAGs, proof-search tasks, and kernel-verification work orders. You
are a generator, not the verifier. Do not report Lean proofs as checked unless
AgentRuntime provides AXLE/local Lean evidence.
"""


FORMALIZER_OUTPUT_CONTRACT: dict[str, Any] = {
    "formal_targets": [
        {
            "id": "string",
            "informal_source": "string",
            "lean_statement_sketch": "string",
            "semantic_alignment_constraints": ["string"],
            "expected_status": "OPEN",
        }
    ],
    "lemma_dependency_plan": [
        {
            "from": "string",
            "to": "string",
            "role": "string",
            "risk": "string",
        }
    ],
    "retrieval_queries": [
        {
            "query": "string",
            "target_library": "Mathlib|StatInference|LeanRAG|OpenProver|other",
            "purpose": "string",
        }
    ],
    "proof_search_plan": {
        "preferred_tools": ["string"],
        "tactic_or_certificate_hints": ["string"],
        "kernel_check_plan": ["string"],
        "known_blockers": ["string"],
    },
    "proof_bank_obligation_requests": [
        {
            "obligation_id": "string",
            "target_theorem_card": "string",
            "reason": "string",
            "verification_priority": "high|medium|low",
        }
    ],
    "gap_taxonomy": [
        {"gap": "string", "kind": "formal_primitives|semantic_alignment|proof_search|source_theorem|other", "next_owner": "string"}
    ],
    "critic_findings": [
        {"critic": "string", "finding": "string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "string", "acceptance_gate": "string"}
    ],
}


FORMALIZER_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "formal_targets",
        "lemma_dependency_plan",
        "retrieval_queries",
        "proof_search_plan",
        "gap_taxonomy",
        "critic_findings",
        "next_actions",
    ],
    "properties": {
        "formal_targets": {"type": "array", "minItems": 1},
        "lemma_dependency_plan": {"type": "array", "minItems": 1},
        "retrieval_queries": {"type": "array", "minItems": 1},
        "proof_search_plan": {"type": "object"},
        "proof_bank_obligation_requests": {"type": "array"},
        "gap_taxonomy": {"type": "array", "minItems": 1},
        "critic_findings": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_formalizer_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "formal_targets",
        "lemma_dependency_plan",
        "retrieval_queries",
        "proof_search_plan",
        "gap_taxonomy",
        "critic_findings",
        "next_actions",
    ):
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    if packet.get("proof_evidence_status") != FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE:
        errors.append("proof_evidence_status must preserve proposal-only boundary")
    if packet.get("kernel_verified") is not False:
        errors.append("LLM Formalizer packet cannot set kernel_verified=true")
    if packet.get("full_frontier_theorem_proved") is not False:
        errors.append("LLM Formalizer packet cannot set full_frontier_theorem_proved=true")
    for row in packet.get("formal_targets", []) or []:
        if not isinstance(row, Mapping):
            errors.append("formal_targets entries must be objects")
            continue
        if not str(row.get("id", "")).strip():
            errors.append("formal target missing id")
        if str(row.get("expected_status", "OPEN")) not in {"OPEN", "FORMAL_GAP", "NEEDS_KERNEL_CHECK"}:
            errors.append(f"unsupported formal target expected_status: {row.get('expected_status')}")
        forbidden = _contains_forbidden_proof_claim(row)
        if forbidden:
            errors.append(f"formal target contains forbidden proof claim: {forbidden}")
    for row in packet.get("proof_bank_obligation_requests", []) or []:
        if not isinstance(row, Mapping):
            errors.append("proof_bank_obligation_requests entries must be objects")
            continue
        if not str(row.get("obligation_id", "")).strip():
            errors.append("proof_bank_obligation_requests entry missing obligation_id")
        priority = str(row.get("verification_priority", "medium") or "medium")
        if priority not in {"high", "medium", "low"}:
            errors.append(f"unsupported proof_bank_obligation_requests priority: {priority}")
        forbidden = _contains_forbidden_proof_claim(row)
        if forbidden:
            errors.append(f"proof_bank_obligation_requests entry contains forbidden proof claim: {forbidden}")
    forbidden_packet = _contains_forbidden_proof_claim(packet)
    if forbidden_packet:
        errors.append(f"packet contains forbidden proof claim: {forbidden_packet}")
    return sorted(set(errors))


def _normalize_formalizer_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    body = dict(payload)
    body["proof_evidence_status"] = FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE
    body["proof_evidence_boundary"] = FORMALIZER_BOUNDARY
    body["kernel_verified"] = False
    body["full_frontier_theorem_proved"] = False
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "model": model,
            "body": body,
        }
    )[:24]
    return {
        "schema_version": FORMALIZER_SCHEMA_VERSION,
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": f"formalizer_proposal:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMFormalizerProofEngineerAgent",
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
        raise ValueError("expected JSON object from LLM Formalizer/ProofEngineer")
    return payload


def _proof_bank_catalog_from_theorem_goals(theorem_goals: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for goal in theorem_goals:
        if not isinstance(goal, Mapping):
            continue
        goal_id = str(goal.get("id", "") or "")
        for obligation_id in goal.get("proof_obligations", []) or []:
            obligation = str(obligation_id or "").strip()
            if not obligation or obligation in seen:
                continue
            seen.add(obligation)
            rows.append(
                {
                    "obligation_id": obligation,
                    "candidate_rank": len(rows) + 1,
                    "candidate_sources": [f"theorem_goal:{goal_id}" if goal_id else "theorem_goal"],
                    "catalog_scope": "theorem_goal_declared_obligation",
                }
            )
    return rows


def _contains_forbidden_proof_claim(value: Any) -> str:
    text = json.dumps(value, default=str).lower()
    forbidden = (
        "kernel_verified\": true",
        "full_frontier_theorem_proved\": true",
        "qed verified",
        "lean verified",
        "kernel verified",
        "theorem proved",
    )
    for token in forbidden:
        if token in text:
            return token
    return ""
