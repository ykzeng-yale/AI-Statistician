from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .generated_metric_repair_policy import (
    generated_metric_gate_repair_instruction,
    generated_python_sandbox_guard_repair_instruction,
    generated_python_sandbox_safe_subset_contract,
)
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion
from .theory_derivation_trace import (
    compact_theory_derivation_trace,
    theory_trace_alignment_contract,
    theory_trace_consumption_contract,
)


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
        environment_feedback: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        user_prompt = build_simulation_engineer_prompt(
            question=question,
            theory_packet=theory_packet,
            registered_problem=registered_problem,
            registered_procedures=registered_procedures,
            n_runs=n_runs,
            seed=seed,
            environment_feedback=environment_feedback or {},
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
                theory_packet=theory_packet,
                n_runs=n_runs,
                seed=seed,
            )

        requires_generated_code = _feedback_requires_generated_simulation_code(
            environment_feedback or {}
        )

        def validate_packet(packet: Mapping[str, Any]) -> list[str]:
            errors = validate_simulation_engineer_packet(packet)
            if requires_generated_code:
                errors.extend(_validate_capability_eval_generated_simulation_packet(packet))
            return sorted(set(errors))

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_packet,
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
    environment_feedback: Mapping[str, Any] | None = None,
) -> str:
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "theory_packet_summary": _compact_theory_packet_for_simulation(theory_packet),
        "theory_trace_consumption_contract": theory_trace_consumption_contract(
            theory_packet,
            consumer_subsystem="SimulationEngineer",
            max_rows=3,
            text_limit=240,
        ),
        "registered_problem": dict(registered_problem),
        "registered_procedures": [dict(row) for row in registered_procedures],
        "runtime_environment_feedback": _compact_simulation_environment_feedback(
            environment_feedback or {}
        ),
        "runtime_execution_budget": {"n_runs": n_runs, "seed": seed},
        "registered_execution_owner": "AgentRuntime ResearchSimulator.run",
        "generated_simulation_code_contract": {
            "status": "optional custom stress-test fallback",
            "language": "python",
            "entrypoint": "run_sandbox",
            "function_signature": "def run_sandbox(seed: int, replicates: int) -> dict",
            "safe_subset": generated_python_sandbox_safe_subset_contract(),
            "runtime_policy": (
                "AgentRuntime will statically inspect and execute safe drafts "
                "inside a bounded local sandbox. Failed or unsafe drafts are "
                "returned as environment feedback for repair."
            ),
        },
        "required_output_contract": SIMULATION_ENGINEER_OUTPUT_CONTRACT,
        "boundary": SIMULATION_ENGINEER_BOUNDARY,
    }
    requires_generated_code = _feedback_requires_generated_simulation_code(
        payload["runtime_environment_feedback"]
    )
    if requires_generated_code:
        payload["generated_simulation_code_contract"]["status"] = (
            "required for capability-eval simulation coding-agent evidence"
        )
        payload["generated_simulation_code_contract"]["capability_eval_default"] = (
            "include one safe simulation_code_drafts entry with entrypoint exactly "
            "run_sandbox and code defining def run_sandbox(seed: int, replicates: int) -> dict"
        )
    generated_simulation_instruction = (
        "Capability-eval mode is active: include exactly one safe "
        "simulation_code_drafts entry with entrypoint exactly \"run_sandbox\" and code "
        "defining def run_sandbox(seed: int, replicates: int) -> dict so AgentRuntime "
        "can execute and evaluate your custom stress-test code. "
        if requires_generated_code
        else ""
    )
    metric_gate_instruction = (
        generated_metric_gate_repair_instruction(
            artifact_label="generated simulation draft"
        )
        if _feedback_reports_metric_gate_failure(payload["runtime_environment_feedback"])
        else ""
    )
    sandbox_guard_instruction = (
        generated_python_sandbox_guard_repair_instruction(
            artifact_label="generated simulation draft"
        )
        if requires_generated_code
        else ""
    )
    component_gate_instruction = (
        "Coding-agent component-gate feedback is active: treat "
        "runtime_environment_feedback as calibration for the expected generated "
        "simulation repair loop, not as current-run simulation evidence. Produce "
        "a bounded safe simulation run_sandbox draft for this question, use prior "
        "failure/metric feedback only as repair-shape guidance, and let "
        "AgentRuntime execute it. Do not claim the attached component gate ran "
        "this simulation or proves the statistical theorem. "
        if _feedback_reports_coding_component_gate(payload["runtime_environment_feedback"])
        else ""
    )
    capability_feedback_instruction = (
        "Integrated coding-agent capability feedback is active: consume "
        "runtime_environment_feedback as the current generated-simulation "
        "capability gap to close. Produce exactly one bounded safe simulation "
        "run_sandbox draft, expose it through simulation_code_drafts, and let "
        "AgentRuntime execute and score the draft for this run. Do not satisfy "
        "this with a registered simulator, static replay, or component-gate "
        "artifact. "
        if _feedback_reports_coding_capability_feedback(
            payload["runtime_environment_feedback"]
        )
        else ""
    )
    theory_trace_alignment_instruction = (
        "Runtime theory-trace downstream alignment feedback is active: treat "
        "runtime_environment_feedback.theory_trace_downstream_alignment_feedback "
        "as a hard proposal-provenance repair contract. The SimulationEngineer "
        "artifact must populate theory_trace_alignment with exact derivation, "
        "equation, assumption, and formalization anchors from the supplied "
        "TheoryDerivationPacket before DGP, stress-test, or metric claims are "
        "evaluated. This alignment is not simulation execution evidence or "
        "theorem proof. "
        if _feedback_reports_theory_trace_downstream_alignment(
            payload["runtime_environment_feedback"]
        )
        else ""
    )
    return (
        "Design a simulation and stress-test plan for the SimulatorEngineer subsystem. "
        "Return ONLY one compact JSON object matching required_output_contract. Include "
        "only the required fields. Keep each list to exactly 1 short object or 1 short "
        "string. You may name one runtime diagnostic, but do not claim that simulations "
        "were run or passed. Execution is owned by AgentRuntime. Use "
        "theory_packet_summary.theory_derivation_trace to align DGPs, estimands, "
        "metrics, and stress tests with the derivation assumptions and equation-chain "
        "quantities. Populate theory_trace_alignment with exact "
        "referenced_derivation_steps, referenced_equation_steps, "
        "referenced_assumptions, and referenced_formalization_targets from the "
        "supplied trace anchors.\n\n"
        + generated_simulation_instruction
        + metric_gate_instruction
        + sandbox_guard_instruction
        + component_gate_instruction
        + capability_feedback_instruction
        + theory_trace_alignment_instruction
        + "If runtime_environment_feedback reports a rejected generated simulation "
        "draft or metric-gate failure, repair that concrete draft or omit "
        "simulation_code_drafts with a blocker; do not repeat the same unsafe, "
        "non-executable, or metric-failing code.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str)
    )


SIMULATION_ENGINEER_SYSTEM_PROMPT = """\
You are the LLM SimulatorEngineer inside an AI Statistician AgentRuntime.

Your job is to design rigorous ADeMP-style simulation diagnostics, stress tests,
metrics, and failure interpretation for proposed statistical theory. You are a
generator, not the executor. Do not run code, do not report simulated results,
and do not claim proof evidence.
"""


def _compact_theory_packet_for_simulation(theory_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Expose only simulator-relevant theory fields to keep Haiku packets short."""

    problem_card = _mapping(theory_packet.get("problem_card", {}))
    simulation_spec = _mapping(theory_packet.get("simulation_ademp_spec", {}))
    return {
        "packet_id": theory_packet.get("packet_id", ""),
        "problem_card": {
            key: _compact_string_or_list(problem_card.get(key, ""))
            for key in ("estimand", "assumptions", "desired_theorem_type")
        },
        "estimator_specs": [
            {
                "id": _truncate_text(row.get("id", ""), limit=120),
                "name": _truncate_text(row.get("name", ""), limit=180),
                "algorithm_sketch": _truncate_text(row.get("algorithm_sketch", ""), limit=500),
            }
            for row in _first_mapping_rows(theory_packet.get("estimator_specs", []), limit=2)
        ],
        "theorem_cards": [
            {
                "id": _truncate_text(row.get("id", ""), limit=120),
                "conclusion": _truncate_text(row.get("conclusion", ""), limit=500),
                "semantic_risks": _compact_string_list(row.get("semantic_risks", []), limit=2),
            }
            for row in _first_mapping_rows(theory_packet.get("theorem_cards", []), limit=2)
        ],
        "simulation_ademp_spec": {
            key: _compact_string_or_list(simulation_spec.get(key, ""))
            for key in ("aim", "dgps", "methods", "performance_measures", "stress_tests")
        },
        "theory_derivation_trace": compact_theory_derivation_trace(
            theory_packet,
            max_rows=3,
            text_limit=240,
        ),
    }


def _compact_simulation_environment_feedback(feedback: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(feedback, Mapping):
        return {}
    prototype_rows = feedback.get("generated_simulation_prototypes", [])
    if not isinstance(prototype_rows, list):
        prototype_rows = []
    theory_alignment_feedback = _compact_theory_trace_downstream_alignment_feedback(
        feedback
    )
    return {
        "architect_evidence_contract": _compact_architect_evidence_contract(
            feedback.get("architect_evidence_contract", {})
        ),
        "runtime_requested_evidence_contract": _compact_architect_evidence_contract(
            feedback.get("runtime_requested_evidence_contract", {})
        ),
        "architect_recommended_research_path": _truncate_text(
            feedback.get("architect_recommended_research_path", ""),
            limit=120,
        ),
        "architect_formal_verification_policy": _truncate_text(
            feedback.get("architect_formal_verification_policy", ""),
            limit=120,
        ),
        "architect_subsystem_acceptance_gate": _truncate_text(
            feedback.get("architect_subsystem_acceptance_gate", ""),
            limit=240,
        ),
        "feedback_type": _truncate_text(feedback.get("feedback_type", ""), limit=180),
        "capability_id": _truncate_text(feedback.get("capability_id", ""), limit=180),
        "target_component": _truncate_text(
            feedback.get("target_component", ""),
            limit=80,
        ),
        "target_behavior": _truncate_text(
            feedback.get("target_behavior", ""),
            limit=360,
        ),
        "recommended_capability_eval_command": _truncate_text(
            feedback.get("recommended_capability_eval_command", ""),
            limit=360,
        ),
        "success_metric": _truncate_text(feedback.get("success_metric", ""), limit=240),
        "blocker": _truncate_text(feedback.get("blocker", ""), limit=240),
        "evidence": _truncate_text(feedback.get("evidence", ""), limit=240),
        "component_eval": _truncate_text(feedback.get("component_eval", ""), limit=180),
        "component_eval_manifest_path": _truncate_text(
            feedback.get("component_eval_manifest_path", ""),
            limit=240,
        ),
        "live_generator": feedback.get("live_generator"),
        "static_or_fixture_only": feedback.get("static_or_fixture_only"),
        "capability_evidence_ok": feedback.get("capability_evidence_ok"),
        "algorithm_capability_evidence_ok": feedback.get(
            "algorithm_capability_evidence_ok"
        ),
        "simulation_capability_evidence_ok": feedback.get(
            "simulation_capability_evidence_ok"
        ),
        "algorithm_repair_sequences": feedback.get("algorithm_repair_sequences"),
        "simulation_repair_sequences": feedback.get("simulation_repair_sequences"),
        "algorithm_live_repair_sequences": feedback.get(
            "algorithm_live_repair_sequences"
        ),
        "simulation_live_repair_sequences": feedback.get(
            "simulation_live_repair_sequences"
        ),
        "capability_evidence_scope": _truncate_text(
            feedback.get("capability_evidence_scope", ""),
            limit=180,
        ),
        "proof_evidence_status": _truncate_text(
            feedback.get("proof_evidence_status", ""),
            limit=180,
        ),
        "proof_evidence_boundary": _truncate_text(
            feedback.get("proof_evidence_boundary", ""),
            limit=240,
        ),
        "failure_classification": _truncate_text(
            feedback.get("failure_classification", ""),
            limit=180,
        ),
        "theory_trace_downstream_alignment_feedback": theory_alignment_feedback,
        "simulation_manifest_id": _truncate_text(
            feedback.get("simulation_manifest_id", ""),
            limit=180,
        ),
        "generated_simulation_prototypes": [
            {
                "simulation_id": _truncate_text(row.get("simulation_id", ""), limit=120),
                "prototype_status": _truncate_text(
                    row.get("prototype_status", ""),
                    limit=160,
                ),
                "executor": _truncate_text(row.get("executor", ""), limit=160),
                "smoke_passed": row.get("smoke_passed"),
                "execution_smoke_passed": row.get("execution_smoke_passed"),
                "metric_gate_errors": _compact_string_list(
                    row.get("metric_gate_errors", []),
                    limit=3,
                    char_limit=220,
                ),
                "safety_errors": _compact_string_list(
                    row.get("safety_errors", []),
                    limit=3,
                    char_limit=220,
                ),
                "code_excerpt": _truncate_text(
                    row.get("code_excerpt", ""),
                    limit=500,
                ),
                "stderr_summary": _truncate_text(
                    row.get("stderr_summary", ""),
                    limit=240,
                ),
                "reason": _truncate_text(row.get("reason", ""), limit=240),
            }
            for row in _first_mapping_rows(prototype_rows, limit=3)
        ],
        "required_repair": _truncate_text(feedback.get("required_repair", ""), limit=360),
        "boundary": _truncate_text(feedback.get("boundary", ""), limit=240),
    }


def _feedback_reports_metric_gate_failure(feedback: Mapping[str, Any]) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    failure = str(feedback.get("failure_classification", "") or "")
    if "metric_gate" in failure:
        return True
    for row in feedback.get("generated_simulation_prototypes", []) or []:
        if isinstance(row, Mapping) and row.get("metric_gate_errors"):
            return True
    return False


def _feedback_reports_coding_component_gate(feedback: Mapping[str, Any]) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    return str(feedback.get("feedback_type", "") or "") == (
        "coding_agent_generated_code_component_gate_feedback"
    )


def _feedback_reports_coding_capability_feedback(feedback: Mapping[str, Any]) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    return str(feedback.get("feedback_type", "") or "") == (
        "coding_agent_generated_code_capability_feedback"
    )


def _compact_theory_trace_downstream_alignment_feedback(
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(feedback, Mapping):
        return {}
    if str(feedback.get("feedback_type", "") or "") == (
        "theory_trace_downstream_alignment_feedback"
    ):
        source: Mapping[str, Any] = feedback
    else:
        nested = feedback.get("theory_trace_downstream_alignment_feedback", {})
        source = nested if isinstance(nested, Mapping) else {}
    if not source:
        return {}
    input_summary = (
        source.get("input_summary", {})
        if isinstance(source.get("input_summary", {}), Mapping)
        else {}
    )
    contract = (
        source.get("theory_trace_downstream_alignment_contract", {})
        if isinstance(
            source.get("theory_trace_downstream_alignment_contract", {}),
            Mapping,
        )
        else {}
    )
    return {
        "feedback_type": "theory_trace_downstream_alignment_feedback",
        "trigger": _truncate_text(
            input_summary.get("trigger", "")
            or contract.get("trigger", "")
            or "RUNTIME_THEORY_TRACE_DOWNSTREAM_ALIGNMENT_MISSING",
            limit=140,
        ),
        "target_consumer_subsystem": _truncate_text(
            source.get("target_consumer_subsystem", "")
            or input_summary.get("target_consumer_subsystem", "")
            or contract.get("target_consumer_subsystem", ""),
            limit=120,
        ),
        "failure_classifications": _compact_string_list(
            source.get(
                "failure_classifications",
                input_summary.get(
                    "failure_classifications",
                    contract.get("failure_classifications", []),
                ),
            ),
            limit=4,
            char_limit=180,
        ),
        "target_ids": _compact_string_list(
            source.get(
                "target_ids",
                input_summary.get("target_ids", contract.get("target_ids", [])),
            ),
            limit=5,
            char_limit=160,
        ),
        "required_repair": _truncate_text(
            source.get("required_repair", "") or source.get("target_behavior", ""),
            limit=360,
        ),
        "acceptance_gate": _truncate_text(
            source.get("acceptance_gate", "") or contract.get("acceptance_gate", ""),
            limit=360,
        ),
        "proof_evidence_status": _truncate_text(
            source.get("proof_evidence_status", "")
            or contract.get("proof_evidence_status", ""),
            limit=180,
        ),
        "boundary": _truncate_text(source.get("boundary", ""), limit=240),
    }


def _feedback_reports_theory_trace_downstream_alignment(
    feedback: Mapping[str, Any],
) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    if str(feedback.get("feedback_type", "") or "") == (
        "theory_trace_downstream_alignment_feedback"
    ):
        return True
    nested = feedback.get("theory_trace_downstream_alignment_feedback", {})
    return isinstance(nested, Mapping) and bool(nested)


def _compact_architect_evidence_contract(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    keys = (
        "formal_verification_policy",
        "recommended_research_path",
        "formal_required_for_final",
        "formal_targets",
        "simulation_targets",
        "acceptance_modes",
        "disclosure_requirements",
        "evaluation_mode",
        "capability_eval_requires_generated_algorithm_code",
        "capability_eval_requires_generated_simulation_code",
    )
    compact: dict[str, Any] = {}
    for key in keys:
        if key not in value:
            continue
        row = value.get(key)
        if isinstance(row, list):
            compact[key] = _compact_string_list(row, limit=3, char_limit=180)
        elif isinstance(row, bool):
            compact[key] = row
        else:
            compact[key] = _truncate_text(row, limit=180)
    return compact


def _first_mapping_rows(value: Any, *, limit: int) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value[:limit] if isinstance(row, Mapping)]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _compact_string_or_list(value: Any) -> str | list[str]:
    if isinstance(value, list):
        return _compact_string_list(value, limit=2)
    return _truncate_text(value)


def _compact_string_list(value: Any, *, limit: int, char_limit: int = 220) -> list[str]:
    if isinstance(value, str):
        rows = [value]
    elif isinstance(value, list):
        rows = value
    else:
        rows = []
    return [_truncate_text(row, limit=char_limit) for row in rows[:limit]]


def _truncate_text(value: Any, *, limit: int = 360) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)] + "...[truncated]"


SIMULATION_ENGINEER_OUTPUT_CONTRACT: dict[str, Any] = {
    "theory_trace_alignment": {
        "referenced_derivation_steps": ["derivation step ids from theory trace"],
        "referenced_equation_steps": ["equation step_ids from theory trace"],
        "referenced_assumptions": ["assumption names from theory trace"],
        "referenced_formalization_targets": ["formalization targets from theory trace"],
        "rationale": "short string",
    },
    "simulation_targets": [
        {
            "procedure_id": "string",
            "estimand": "short string",
        }
    ],
    "runtime_execution_plan": {
        "registered_simulator": "ResearchSimulator.run",
        "n_runs": "integer",
        "seed": "integer",
    },
    "critic_findings": [
        {"critic": "string", "finding": "short string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "short string", "acceptance_gate": "short string"}
    ],
    "simulation_code_drafts": [
        {
            "simulation_id": "string",
            "language": "python",
            "entrypoint": "run_sandbox",
            "code": "optional safe Python code",
        }
    ],
}


SIMULATION_ENGINEER_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "simulation_targets",
        "runtime_execution_plan",
        "critic_findings",
        "next_actions",
    ],
    "properties": {
        "simulation_targets": {"type": "array", "minItems": 1},
        "dgp_plan": {"type": "array"},
        "metric_plan": {"type": "array"},
        "stress_tests": {"type": "array"},
        "failure_interpretation": {"type": "array"},
        "simulation_code_drafts": {"type": "array"},
        "runtime_execution_plan": {"type": "object"},
        "critic_findings": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_simulation_engineer_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "simulation_targets",
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
    for row in packet.get("simulation_code_drafts", []) or []:
        if not isinstance(row, Mapping):
            errors.append("simulation_code_drafts entries must be objects")
            continue
        if str(row.get("language", "")).strip().lower() != "python":
            errors.append("simulation_code_drafts language must be python")
        if str(row.get("entrypoint", "")).strip() not in {"", "run_sandbox"}:
            errors.append("simulation_code_drafts entrypoint must be run_sandbox")
        if not str(row.get("simulation_id", "")).strip():
            errors.append("simulation_code_drafts entry missing simulation_id")
        code = str(row.get("code", ""))
        if not code.strip():
            errors.append("simulation_code_drafts entry missing code")
        if len(code) > 12000:
            errors.append("simulation_code_drafts code exceeds 12000 characters")
    runtime_plan = packet.get("runtime_execution_plan", {})
    if isinstance(runtime_plan, Mapping):
        if str(runtime_plan.get("registered_simulator", "")) != "ResearchSimulator.run":
            errors.append("runtime_execution_plan.registered_simulator must be ResearchSimulator.run")
    else:
        errors.append("runtime_execution_plan must be an object")
    return sorted(set(errors))


def _feedback_requires_generated_simulation_code(feedback: Mapping[str, Any]) -> bool:
    """Return true when the Architect contract is testing simulation-code capacity."""

    if not isinstance(feedback, Mapping):
        return False
    failure = str(feedback.get("failure_classification", "") or "")
    if failure in {
        "generated_simulation_sandbox_metric_gate_failed",
        "generated_simulation_sandbox_no_executable_draft",
        "coding_agent_component_gate_calibration_required",
    }:
        return True
    for row in feedback.get("generated_simulation_prototypes", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("executor", "") or "") == "generated_simulation_sandbox":
            return True
    contract_candidates = (
        feedback.get("architect_evidence_contract", {}),
        feedback.get("runtime_requested_evidence_contract", {}),
        _mapping(feedback.get("architect_context", {})).get(
            "runtime_requested_evidence_contract",
            {},
        ),
    )
    return any(
        isinstance(contract, Mapping)
        and contract.get("capability_eval_requires_generated_simulation_code") is True
        for contract in contract_candidates
    )


def _validate_capability_eval_generated_simulation_packet(
    packet: Mapping[str, Any],
) -> list[str]:
    """Capability eval must exercise generated stress-test code, not simulator-only rows."""

    drafts = [row for row in packet.get("simulation_code_drafts", []) or [] if isinstance(row, Mapping)]
    if drafts:
        return []
    return [
        "capability_eval requires at least one Claude/OpenAI-generated simulation_code_drafts entry"
    ]


def _normalize_simulation_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    theory_packet: Mapping[str, Any],
    n_runs: int,
    seed: int,
) -> dict[str, Any]:
    body = dict(payload)
    _normalize_simulation_code_draft_metadata(body)
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
    body["theory_trace_consumption_contract"] = theory_trace_consumption_contract(
        theory_packet,
        consumer_subsystem="SimulationEngineer",
        max_rows=3,
        text_limit=240,
    )
    body["theory_trace_alignment_contract"] = theory_trace_alignment_contract(
        theory_packet,
        body.get("theory_trace_alignment", {}),
        consumer_subsystem="SimulationEngineer",
        max_rows=3,
        text_limit=240,
    )
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


def _normalize_simulation_code_draft_metadata(body: dict[str, Any]) -> None:
    raw_drafts = body.get("simulation_code_drafts", [])
    if not isinstance(raw_drafts, list):
        return
    normalized_drafts: list[Any] = []
    for row in raw_drafts:
        if not isinstance(row, Mapping):
            normalized_drafts.append(row)
            continue
        normalized = dict(row)
        language = str(normalized.get("language", "") or "").strip().lower()
        if language in {"", "py", "py3", "python3", "python 3"} and str(
            normalized.get("code", "") or ""
        ).strip():
            normalized["language"] = "python"
        entrypoint = str(normalized.get("entrypoint", "") or "").strip()
        if _is_run_sandbox_signature_entrypoint(entrypoint):
            normalized["entrypoint"] = "run_sandbox"
        normalized_drafts.append(normalized)
    body["simulation_code_drafts"] = normalized_drafts


def _is_run_sandbox_signature_entrypoint(entrypoint: str) -> bool:
    compact = entrypoint.strip().replace(" ", "")
    return bool(
        compact
        and (
            compact == "run_sandbox"
            or compact.startswith("run_sandbox(")
            or compact.startswith("defrun_sandbox(")
        )
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM SimulatorEngineer")
