from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion


SIMULATION_ENGINEER_SCHEMA_VERSION = 1
SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE = "LLM_SIMULATION_PROPOSAL_NOT_EXECUTION_EVIDENCE"
SIMULATION_ENGINEER_BOUNDARY = (
    "LLM SimulatorEngineer packets are simulation-design proposals only. They "
    "do not execute Monte Carlo code, do not validate an estimator empirically, "
    "and do not count as proof evidence. Executable simulation evidence requires "
    "AgentRuntime to run registered simulator code with recorded seed and metrics."
)


@dataclass(frozen=True)
class SimulationEngineerConfig:
    model: str = ""
    model_tier: str = "haiku"
    max_tokens: int = 5000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1


class LLMSimulationEngineerAgent:
    """Generator-backed SimulatorEngineer proposal worker."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: SimulationEngineerConfig = SimulationEngineerConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def propose(
        self,
        *,
        question: OpenResearchQuestion,
        theory_packet: Mapping[str, Any],
        registered_problem: Mapping[str, Any],
        registered_procedures: list[Mapping[str, Any]],
        n_runs: int,
        seed: int,
    ) -> dict[str, Any]:
        user_prompt = build_simulation_engineer_prompt(
            question=question,
            theory_packet=theory_packet,
            registered_problem=registered_problem,
            registered_procedures=registered_procedures,
            n_runs=n_runs,
            seed=seed,
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        request = GeneratorRequest(
            system_prompt=SIMULATION_ENGINEER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=SIMULATION_ENGINEER_JSON_SCHEMA,
            metadata={
                "subsystem": "SimulatorEngineer",
                "agent": "LLMSimulationEngineerAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_simulation_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
                n_runs=n_runs,
                seed=seed,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_simulation_engineer_packet,
            validation_label="LLM SimulatorEngineer packet",
            max_repair_attempts=self.config.max_repair_attempts,
        )


def build_simulation_engineer_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    registered_problem: Mapping[str, Any],
    registered_procedures: list[Mapping[str, Any]],
    n_runs: int,
    seed: int,
) -> str:
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "theory_packet_summary": {
            "packet_id": theory_packet.get("packet_id", ""),
            "problem_card": theory_packet.get("problem_card", {}),
            "estimator_specs": theory_packet.get("estimator_specs", []),
            "theorem_cards": theory_packet.get("theorem_cards", []),
            "simulation_ademp_spec": theory_packet.get("simulation_ademp_spec", {}),
        },
        "registered_problem": dict(registered_problem),
        "registered_procedures": [dict(row) for row in registered_procedures],
        "runtime_execution_budget": {"n_runs": n_runs, "seed": seed},
        "registered_execution_owner": "AgentRuntime ResearchSimulator.run",
        "required_output_contract": SIMULATION_ENGINEER_OUTPUT_CONTRACT,
        "boundary": SIMULATION_ENGINEER_BOUNDARY,
    }
    return (
        "Design a simulation and stress-test plan for the SimulatorEngineer subsystem. "
        "Return ONLY JSON matching required_output_contract. You may critique the theory "
        "packet and propose DGPs, metrics, stress tests, and failure interpretation, but "
        "do not claim that simulations were run or passed. Execution is owned by AgentRuntime.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )


SIMULATION_ENGINEER_SYSTEM_PROMPT = """\
You are the LLM SimulatorEngineer inside an AI Statistician AgentRuntime.

Your job is to design rigorous ADeMP-style simulation diagnostics, stress tests,
metrics, and failure interpretation for proposed statistical theory. You are a
generator, not the executor. Do not run code, do not report simulated results,
and do not claim proof evidence.
"""


SIMULATION_ENGINEER_OUTPUT_CONTRACT: dict[str, Any] = {
    "simulation_targets": [
        {
            "procedure_id": "string",
            "estimand": "string",
            "primary_question": "string",
            "target_theorem_card": "string",
        }
    ],
    "dgp_plan": [
        {
            "id": "string",
            "description": "string",
            "parameters": ["string"],
            "assumptions_stressed": ["string"],
            "expected_behavior": "string",
        }
    ],
    "metric_plan": ["string"],
    "stress_tests": ["string"],
    "failure_interpretation": [
        {"diagnostic": "string", "possible_cause": "string", "reroute_to": "string"}
    ],
    "runtime_execution_plan": {
        "registered_simulator": "ResearchSimulator.run",
        "n_runs": "integer",
        "seed": "integer",
        "notes": ["string"],
    },
    "critic_findings": [
        {"critic": "string", "finding": "string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "string", "acceptance_gate": "string"}
    ],
}


SIMULATION_ENGINEER_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "simulation_targets",
        "dgp_plan",
        "metric_plan",
        "stress_tests",
        "failure_interpretation",
        "runtime_execution_plan",
        "critic_findings",
        "next_actions",
    ],
    "properties": {
        "simulation_targets": {"type": "array", "minItems": 1},
        "dgp_plan": {"type": "array", "minItems": 1},
        "metric_plan": {"type": "array", "minItems": 1},
        "stress_tests": {"type": "array", "minItems": 1},
        "failure_interpretation": {"type": "array", "minItems": 1},
        "runtime_execution_plan": {"type": "object"},
        "critic_findings": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_simulation_engineer_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "simulation_targets",
        "dgp_plan",
        "metric_plan",
        "stress_tests",
        "failure_interpretation",
        "runtime_execution_plan",
        "critic_findings",
        "next_actions",
    ):
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    if packet.get("simulation_evidence_status") != SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE:
        errors.append("simulation_evidence_status must preserve proposal-only boundary")
    if packet.get("simulations_executed") is not False:
        errors.append("LLM SimulatorEngineer packet cannot set simulations_executed=true")
    if packet.get("proof_evidence_status") != "NOT_PROOF_EVIDENCE":
        errors.append("LLM SimulatorEngineer packet cannot claim proof evidence")
    for row in packet.get("simulation_targets", []) or []:
        if not isinstance(row, Mapping):
            errors.append("simulation_targets entries must be objects")
            continue
        if not str(row.get("procedure_id", "")).strip():
            errors.append("simulation target missing procedure_id")
    runtime_plan = packet.get("runtime_execution_plan", {})
    if isinstance(runtime_plan, Mapping):
        if str(runtime_plan.get("registered_simulator", "")) != "ResearchSimulator.run":
            errors.append("runtime_execution_plan.registered_simulator must be ResearchSimulator.run")
    else:
        errors.append("runtime_execution_plan must be an object")
    return sorted(set(errors))


def _normalize_simulation_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    n_runs: int,
    seed: int,
) -> dict[str, Any]:
    body = dict(payload)
    runtime_plan = body.get("runtime_execution_plan", {})
    if not isinstance(runtime_plan, Mapping):
        runtime_plan = {}
    else:
        runtime_plan = dict(runtime_plan)
    requested_registered_simulator = str(runtime_plan.get("registered_simulator", "") or "").strip()
    runtime_plan["llm_requested_registered_simulator"] = requested_registered_simulator
    runtime_plan["registered_simulator"] = "ResearchSimulator.run"
    runtime_plan["n_runs"] = n_runs
    runtime_plan["seed"] = seed
    runtime_plan["canonicalization_boundary"] = (
        "AgentRuntime owns simulator selection and execution. The LLM may propose "
        "simulation diagnostics, but the registered simulator field is canonicalized "
        "to the trusted ResearchSimulator.run entrypoint before validation."
    )
    body["runtime_execution_plan"] = runtime_plan
    body["simulation_evidence_status"] = SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE
    body["simulation_evidence_boundary"] = SIMULATION_ENGINEER_BOUNDARY
    body["proof_evidence_status"] = "NOT_PROOF_EVIDENCE"
    body["simulations_executed"] = False
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
            "n_runs": n_runs,
            "seed": seed,
        }
    )[:24]
    return {
        "schema_version": SIMULATION_ENGINEER_SCHEMA_VERSION,
        "artifact_kind": "SimulationEngineerProposalPacket",
        "packet_id": f"simulation_engineer_proposal:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMSimulationEngineerAgent",
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
        "runtime_budget": {"n_runs": n_runs, "seed": seed},
        **body,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM SimulatorEngineer")
