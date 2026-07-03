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
from .algorithm_template_registry import (
    registered_algorithm_template_hint_contract,
    registered_algorithm_template_ids,
    registered_algorithm_template_prompt_rows,
)
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion
from .theory_derivation_trace import (
    compact_theory_derivation_trace,
    theory_trace_alignment_contract,
    theory_trace_consumption_contract,
)


ALGORITHM_ENGINEER_SCHEMA_VERSION = 1
ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE = "LLM_ALGORITHM_PROPOSAL_NOT_EXECUTION_EVIDENCE"
ALGORITHM_ENGINEER_BOUNDARY = (
    "LLM AlgorithmEngineer packets are implementation proposals only. They do "
    "not prove statistical claims, do not register production algorithms, and "
    "do not count as executable evidence until the AgentRuntime sandbox runs "
    "the selected code path reproducibly."
)


@dataclass(frozen=True)
class AlgorithmEngineerConfig:
    model: str = ""
    model_tier: str = "haiku"
    max_tokens: int = 5000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1


class LLMAlgorithmEngineerAgent:
    """Generator-backed AlgorithmEngineer proposal worker.

    The model proposes implementation strategy, sandbox shape, stress tests,
    and promotion gates. The runtime owns code execution and validation.
    """

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: AlgorithmEngineerConfig = AlgorithmEngineerConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def propose(
        self,
        *,
        question: OpenResearchQuestion,
        theory_packet: Mapping[str, Any],
        simulation_manifest: Mapping[str, Any],
        implementation_gaps: list[Mapping[str, Any]],
        environment_feedback: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        user_prompt = build_algorithm_engineer_prompt(
            question=question,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            implementation_gaps=implementation_gaps,
            environment_feedback=environment_feedback or {},
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        request = GeneratorRequest(
            system_prompt=ALGORITHM_ENGINEER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=ALGORITHM_ENGINEER_JSON_SCHEMA,
            metadata={
                "subsystem": "AlgorithmEngineer",
                "agent": "LLMAlgorithmEngineerAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_algorithm_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                backend_provider_name=response.provider,
                raw_response=raw_text,
                theory_packet=theory_packet,
                implementation_gaps=implementation_gaps,
            )

        requires_generated_code = _feedback_requires_generated_algorithm_code(
            environment_feedback or {}
        )

        def validate_packet(packet: Mapping[str, Any]) -> list[str]:
            errors = validate_algorithm_engineer_packet(packet)
            if requires_generated_code:
                errors.extend(
                    _validate_capability_eval_generated_algorithm_packet(
                        packet,
                        implementation_gaps=implementation_gaps,
                    )
                )
            return sorted(set(errors))

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_packet,
            validation_label="LLM AlgorithmEngineer packet",
            max_repair_attempts=self.config.max_repair_attempts,
        )


def build_algorithm_engineer_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    implementation_gaps: list[Mapping[str, Any]],
    environment_feedback: Mapping[str, Any] | None = None,
) -> str:
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "theory_packet_summary": _compact_theory_packet_for_algorithm(theory_packet),
        "theory_trace_consumption_contract": theory_trace_consumption_contract(
            theory_packet,
            consumer_subsystem="AlgorithmEngineer",
            max_rows=3,
            text_limit=240,
        ),
        "simulation_manifest_summary": _compact_simulation_manifest_for_algorithm(simulation_manifest),
        "implementation_gaps": _compact_implementation_gaps(implementation_gaps),
        "runtime_environment_feedback": _compact_algorithm_environment_feedback(
            environment_feedback or {}
        ),
        "registered_runtime_templates": registered_algorithm_template_prompt_rows(),
        "generated_code_sandbox_contract": {
            "status": "optional fallback when no registered template matches",
            "language": "python",
            "entrypoint": "run_sandbox",
            "function_signature": "def run_sandbox(seed: int, replicates: int) -> dict",
            "default": "leave sandbox_code_drafts empty when a registered template matches",
            "safe_subset": generated_python_sandbox_safe_subset_contract(),
            "runtime_policy": (
                "AgentRuntime will statically inspect and execute safe drafts only "
                "inside a bounded sandbox; unsafe or nonconforming drafts are rejected."
            ),
            "forbidden_claims": [
                "do not claim the draft was executed",
                "do not claim production registration",
                "do not claim theorem proof evidence",
            ],
        },
        "required_output_contract": ALGORITHM_ENGINEER_OUTPUT_CONTRACT,
        "boundary": ALGORITHM_ENGINEER_BOUNDARY,
    }
    requires_generated_code = _feedback_requires_generated_algorithm_code(
        payload["runtime_environment_feedback"]
    )
    if requires_generated_code:
        payload["generated_code_sandbox_contract"]["status"] = (
            "required for capability-eval coding-agent evidence"
        )
        payload["generated_code_sandbox_contract"]["default"] = (
            "include one safe sandbox_code_drafts entry even when a registered "
            "template also matches; the template may be referenced only as a baseline"
        )
    generated_code_instruction = (
        "Capability-eval mode is active: include exactly one safe "
        "sandbox_code_drafts entry with entrypoint exactly \"run_sandbox\" and code "
        "defining def run_sandbox(seed: int, replicates: int) -> dict. Set every "
        "implementation_targets row registered_template_hint to none so AgentRuntime "
        "can test Claude-generated algorithm code execution. Registered templates may "
        "be named only in prose as baselines; they will not be executed for this "
        "capability gate. "
        if requires_generated_code
        else (
            "Prefer registered runtime templates over sandbox_code_drafts; leave "
            "sandbox_code_drafts empty whenever a template matches. "
        )
    )
    metric_gate_instruction = (
        generated_metric_gate_repair_instruction(
            artifact_label="generated algorithm draft"
        )
        if _feedback_reports_metric_gate_failure(payload["runtime_environment_feedback"])
        else ""
    )
    sandbox_guard_instruction = (
        generated_python_sandbox_guard_repair_instruction(
            artifact_label="generated algorithm draft"
        )
        if requires_generated_code
        else ""
    )
    component_gate_instruction = (
        "Coding-agent component-gate feedback is active: treat "
        "runtime_environment_feedback as calibration for the expected generated-code "
        "repair loop, not as current-run execution evidence. Produce a bounded safe "
        "algorithm run_sandbox draft for this question, use prior failure/metric "
        "feedback only as repair-shape guidance, and let AgentRuntime execute it. "
        "Do not claim the attached component gate executed this draft or proves the "
        "statistical theorem. "
        if _feedback_reports_coding_component_gate(payload["runtime_environment_feedback"])
        else ""
    )
    capability_feedback_instruction = (
        "Integrated coding-agent capability feedback is active: consume "
        "runtime_environment_feedback as the current capability gap to close. "
        "Produce exactly one bounded safe algorithm run_sandbox draft, expose it "
        "through sandbox_code_drafts, and let AgentRuntime execute and score the "
        "draft for this run. Do not satisfy this with a registered template, "
        "static replay, or component-gate artifact. "
        if _feedback_reports_coding_capability_feedback(
            payload["runtime_environment_feedback"]
        )
        else ""
    )
    theory_trace_alignment_instruction = (
        "Runtime theory-trace downstream alignment feedback is active: treat "
        "runtime_environment_feedback.theory_trace_downstream_alignment_feedback "
        "as a hard proposal-provenance repair contract. The AlgorithmEngineer "
        "artifact must populate theory_trace_alignment with exact derivation, "
        "equation, assumption, and formalization anchors from the supplied "
        "TheoryDerivationPacket before code or adapter claims are evaluated. "
        "This alignment is not code execution evidence or theorem proof. "
        if _feedback_reports_theory_trace_downstream_alignment(
            payload["runtime_environment_feedback"]
        )
        else ""
    )
    return (
        "Design implementation and sandbox-validation artifacts for the AlgorithmEngineer subsystem. "
        "Return ONLY one compact JSON object matching required_output_contract. Keep each list to "
        "exactly 1 short object or 1 short string. Include only required fields. "
        + generated_code_instruction
        + metric_gate_instruction
        + sandbox_guard_instruction
        + component_gate_instruction
        + capability_feedback_instruction
        + theory_trace_alignment_instruction
        + "You may "
        "propose code and tests, but "
        "you must not claim you executed code, wrote files, promoted a production algorithm, or proved "
        "any theorem. Pick registered runtime templates only when their contract matches the estimator. "
        "Use theory_packet_summary.theory_derivation_trace to align generated code, validation metrics, "
        "and risk controls with the derivation assumptions and equation-chain quantities. "
        "Populate theory_trace_alignment with exact referenced_derivation_steps, "
        "referenced_equation_steps, referenced_assumptions, and referenced_formalization_targets "
        "from the supplied trace anchors. "
        "If runtime_environment_feedback reports rejected or failed sandbox code, repair that concrete "
        "draft or switch to a supported registered-template/adapter plan; do not repeat the same unsafe "
        "or non-executable code. "
        "For sandbox_code_drafts, obey the generated_code_sandbox_contract safe_subset exactly: do not "
        "use imports other than plain import math/statistics/random; do not use from-import helper aliases, "
        "NumPy/SciPy/sklearn/pandas/statsmodels/torch/JAX, class definitions, file/network "
        "operations, method calls, or attribute access except math.*, statistics.*, random.*, and list append/sort. "
        "Do not call bare helpers such as mean(), stdev(), or sqrt(); use sum(values) / len(values), explicit "
        "variance/std loops, or module-qualified calls such as statistics.mean(values), statistics.stdev(values), "
        "and math.sqrt(x). If runtime_environment_feedback.forbidden_generated_code_calls is nonempty, do not reuse "
        "those names as bare calls in the next draft. If the requested "
        "prototype needs those tools, omit sandbox_code_drafts and describe the registered-template or "
        "human-reviewed adapter plan instead. For this compact packet, do not include "
        "sandbox_code_drafts unless registered_template_hint is none for every implementation target.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str)
    )


ALGORITHM_ENGINEER_SYSTEM_PROMPT = """\
You are the LLM AlgorithmEngineer inside an AI Statistician AgentRuntime.

Your job is to turn theory-derived estimator specs into concrete implementation
plans, sandbox prototypes, data contracts, stress-test designs, and promotion
gates. You are a generator, not the executor. Do not run tools, do not write
files, do not report tests as passed, and do not claim proof evidence.
"""


def _compact_theory_packet_for_algorithm(theory_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Expose only implementation-relevant theory fields to keep Haiku packets short."""

    problem_card = _mapping(theory_packet.get("problem_card", {}))
    simulation_spec = _mapping(theory_packet.get("simulation_ademp_spec", {}))
    return {
        "packet_id": theory_packet.get("packet_id", ""),
        "problem_card": {
            key: _truncate_text(problem_card.get(key, ""))
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
            key: _compact_string_list(simulation_spec.get(key, []), limit=2)
            for key in ("methods", "performance_measures", "stress_tests")
        },
        "theory_derivation_trace": compact_theory_derivation_trace(
            theory_packet,
            max_rows=3,
            text_limit=240,
        ),
    }


def _compact_simulation_manifest_for_algorithm(simulation_manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "manifest_id": simulation_manifest.get("manifest_id", ""),
        "simulation_passed": simulation_manifest.get("simulation_passed"),
        "registered_procedures": [
            {
                "procedure_id": _truncate_text(
                    row.get("procedure_id", row.get("id", row.get("name", ""))),
                    limit=160,
                ),
                "registered_simulator": _truncate_text(row.get("registered_simulator", ""), limit=160),
            }
            for row in _first_mapping_rows(simulation_manifest.get("registered_procedures", []), limit=3)
        ],
        "simulations": [
            {
                "procedure_id": _truncate_text(row.get("procedure_id", row.get("id", "")), limit=160),
                "passed": row.get("passed", row.get("simulation_passed", row.get("smoke_passed"))),
                "metrics": _compact_mapping(row.get("metrics", {}), limit=4),
            }
            for row in _first_mapping_rows(simulation_manifest.get("simulations", []), limit=2)
        ],
        "implementation_gaps": _compact_implementation_gaps(
            simulation_manifest.get("implementation_gaps", [])
        ),
    }


def _compact_algorithm_environment_feedback(feedback: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(feedback, Mapping):
        return {}
    prototype_rows = feedback.get("prototypes", [])
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
        "theory_trace_downstream_alignment_feedback": theory_alignment_feedback,
        "algorithm_sandbox_manifest_id": _truncate_text(
            feedback.get("algorithm_sandbox_manifest_id", ""),
            limit=180,
        ),
        "failure_classification": _truncate_text(
            feedback.get("failure_classification", ""),
            limit=180,
        ),
        "forbidden_generated_code_calls": _compact_string_list(
            feedback.get("forbidden_generated_code_calls", []),
            limit=6,
            char_limit=80,
        ),
        "prototypes": [
            {
                "estimator_id": _truncate_text(row.get("estimator_id", ""), limit=120),
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
                "forbidden_generated_code_calls": _compact_string_list(
                    row.get("forbidden_generated_code_calls", []),
                    limit=5,
                    char_limit=80,
                ),
                "metrics": _compact_mapping(row.get("metrics", {}), limit=6),
                "metric_gate_targets": _compact_mapping(
                    row.get("metric_gate_targets", {}),
                    limit=4,
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
    for row in feedback.get("prototypes", []) or []:
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


def _compact_implementation_gaps(value: Any) -> list[dict[str, Any]]:
    return [
        {
            "estimator_id": _truncate_text(row.get("estimator_id", row.get("id", "")), limit=160),
            "status": _truncate_text(row.get("status", ""), limit=180),
            "reason": _truncate_text(row.get("reason", ""), limit=360),
        }
        for row in _first_mapping_rows(value, limit=3)
    ]


def _first_mapping_rows(value: Any, *, limit: int) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value[:limit] if isinstance(row, Mapping)]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _compact_mapping(value: Any, *, limit: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    compact: dict[str, Any] = {}
    for index, (key, row_value) in enumerate(value.items()):
        if index >= limit:
            break
        compact[str(key)] = _truncate_text(row_value, limit=180)
    return compact


def _compact_string_list(value: Any, *, limit: int, char_limit: int = 220) -> list[str]:
    if isinstance(value, str):
        rows = [value]
    elif isinstance(value, list):
        rows = value
    else:
        rows = []
    return [_truncate_text(row, limit=char_limit) for row in rows[:limit]]


def _truncate_text(value: Any, *, limit: int = 360) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)] + "...[truncated]"


ALGORITHM_ENGINEER_OUTPUT_CONTRACT: dict[str, Any] = {
    "theory_trace_alignment": {
        "referenced_derivation_steps": ["derivation step ids from theory trace"],
        "referenced_equation_steps": ["equation step_ids from theory trace"],
        "referenced_assumptions": ["assumption names from theory trace"],
        "referenced_formalization_targets": ["formalization targets from theory trace"],
        "rationale": "short string",
    },
    "implementation_targets": [
        {
            "estimator_id": "string",
            "adapter_strategy": "short string",
            "registered_template_hint": registered_algorithm_template_hint_contract(),
            "data_contract": ["one short string"],
            "validation_metrics": ["one short string"],
            "risk_controls": ["one short string"],
        }
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "short string", "acceptance_gate": "short string"}
    ],
}


ALGORITHM_ENGINEER_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "implementation_targets",
        "next_actions",
    ],
    "properties": {
        "implementation_targets": {"type": "array", "minItems": 1},
        "sandbox_plan": {"type": "object"},
        "code_generation_plan": {"type": "object"},
        "sandbox_code_drafts": {"type": "array"},
        "promotion_gate": {"type": "object"},
        "critic_findings": {"type": "array"},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_algorithm_engineer_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "implementation_targets",
        "next_actions",
    ):
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    if packet.get("execution_evidence_status") != ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE:
        errors.append("execution_evidence_status must preserve proposal-only boundary")
    if packet.get("sandbox_executed") is not False:
        errors.append("LLM AlgorithmEngineer packet cannot set sandbox_executed=true")
    if packet.get("production_registered") is not False:
        errors.append("LLM AlgorithmEngineer packet cannot set production_registered=true")
    if packet.get("proof_evidence_status") != "NOT_PROOF_EVIDENCE":
        errors.append("LLM AlgorithmEngineer packet cannot claim proof evidence")
    for row in packet.get("implementation_targets", []) or []:
        if not isinstance(row, Mapping):
            errors.append("implementation_targets entries must be objects")
            continue
        if not str(row.get("estimator_id", "")).strip():
            errors.append("implementation target missing estimator_id")
        template = str(row.get("registered_template_hint", "none") or "none")
        if template not in {*registered_algorithm_template_ids(), "none"}:
            errors.append(f"unsupported registered_template_hint: {template}")
    for row in packet.get("sandbox_code_drafts", []) or []:
        if not isinstance(row, Mapping):
            errors.append("sandbox_code_drafts entries must be objects")
            continue
        if str(row.get("language", "")).strip().lower() != "python":
            errors.append("sandbox_code_drafts language must be python")
        if str(row.get("entrypoint", "")).strip() not in {"", "run_sandbox"}:
            errors.append("sandbox_code_drafts entrypoint must be run_sandbox")
        if not str(row.get("estimator_id", "")).strip():
            errors.append("sandbox_code_drafts entry missing estimator_id")
        code = str(row.get("code", ""))
        if not code.strip():
            errors.append("sandbox_code_drafts entry missing code")
        if len(code) > 12000:
            errors.append("sandbox_code_drafts code exceeds 12000 characters")
    return sorted(set(errors))


def _feedback_requires_generated_algorithm_code(feedback: Mapping[str, Any]) -> bool:
    """Return true when the Architect contract is testing coding-agent capacity."""

    if not isinstance(feedback, Mapping):
        return False
    failure = str(feedback.get("failure_classification", "") or "")
    if failure in {
        "generated_algorithm_sandbox_metric_gate_failed",
        "generated_algorithm_sandbox_required_not_executed",
        "generated_algorithm_sandbox_repair_required",
        "coding_agent_component_gate_calibration_required",
    }:
        return True
    for row in feedback.get("prototypes", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("executor", "") or "") == "generated_python_sandbox":
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
        and contract.get("capability_eval_requires_generated_algorithm_code") is True
        for contract in contract_candidates
    )


def _validate_capability_eval_generated_algorithm_packet(
    packet: Mapping[str, Any],
    *,
    implementation_gaps: list[Mapping[str, Any]],
) -> list[str]:
    """Capability eval must exercise Claude-generated code, not a template path."""

    errors: list[str] = []
    targets = [row for row in packet.get("implementation_targets", []) or [] if isinstance(row, Mapping)]
    drafts = [row for row in packet.get("sandbox_code_drafts", []) or [] if isinstance(row, Mapping)]
    if not drafts:
        errors.append(
            "capability_eval requires at least one Claude/OpenAI-generated sandbox_code_drafts entry"
        )
    for row in targets:
        template = str(row.get("registered_template_hint", "none") or "none").strip()
        if template != "none":
            errors.append(
                "capability_eval requires registered_template_hint=none for every implementation target"
            )
    target_ids = {
        str(row.get("estimator_id", "")).strip()
        for row in targets
        if str(row.get("estimator_id", "")).strip()
    }
    gap_ids = {
        str(row.get("estimator_id", row.get("id", ""))).strip()
        for row in implementation_gaps
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", row.get("id", ""))).strip()
    }
    expected_ids = target_ids or gap_ids
    draft_ids = {
        str(row.get("estimator_id", "")).strip()
        for row in drafts
        if str(row.get("estimator_id", "")).strip()
    }
    if expected_ids and draft_ids and expected_ids.isdisjoint(draft_ids):
        errors.append(
            "capability_eval sandbox_code_drafts estimator_id must match an implementation target or gap"
        )
    return errors


def _normalize_algorithm_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    backend_provider_name: str,
    raw_response: str,
    theory_packet: Mapping[str, Any],
    implementation_gaps: list[Mapping[str, Any]],
) -> dict[str, Any]:
    body = dict(payload)
    _normalize_algorithm_sandbox_code_drafts(
        body,
        implementation_gaps=implementation_gaps,
    )
    body["execution_evidence_status"] = ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE
    body["execution_evidence_boundary"] = ALGORITHM_ENGINEER_BOUNDARY
    body["proof_evidence_status"] = "NOT_PROOF_EVIDENCE"
    body["sandbox_executed"] = False
    body["production_registered"] = False
    body["theory_trace_consumption_contract"] = theory_trace_consumption_contract(
        theory_packet,
        consumer_subsystem="AlgorithmEngineer",
        max_rows=3,
        text_limit=240,
    )
    body["theory_trace_alignment_contract"] = theory_trace_alignment_contract(
        theory_packet,
        body.get("theory_trace_alignment", {}),
        consumer_subsystem="AlgorithmEngineer",
        max_rows=3,
        text_limit=240,
    )
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "backend_provider": backend_provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
            "implementation_gaps": [dict(row) for row in implementation_gaps],
        }
    )[:24]
    return {
        "schema_version": ALGORITHM_ENGINEER_SCHEMA_VERSION,
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": f"algorithm_engineer_proposal:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMAlgorithmEngineerAgent",
        "provider": provider_name,
        "backend_provider": backend_provider_name,
        "model": model,
        "model_tier": model_tier,
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "implementation_gaps": [dict(row) for row in implementation_gaps],
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _normalize_algorithm_sandbox_code_drafts(
    body: dict[str, Any],
    *,
    implementation_gaps: list[Mapping[str, Any]],
) -> None:
    """Normalize harmless sandbox draft metadata before validation.

    The runtime still executes only Python drafts that pass the static sandbox
    guard. This normalization prevents live generators from burning repair
    loops on metadata variants such as ``Python``/``python3`` or an omitted
    estimator id when the task has exactly one implementation target.
    """

    raw_drafts = body.get("sandbox_code_drafts", [])
    if not isinstance(raw_drafts, list):
        return
    default_estimator_id = _single_algorithm_estimator_id(
        body.get("implementation_targets", []),
        implementation_gaps=implementation_gaps,
    )
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
        if (
            default_estimator_id
            and not str(normalized.get("estimator_id", "") or "").strip()
        ):
            normalized["estimator_id"] = default_estimator_id
        entrypoint = str(normalized.get("entrypoint", "") or "").strip()
        if _is_run_sandbox_signature_entrypoint(entrypoint):
            normalized["entrypoint"] = "run_sandbox"
        normalized_drafts.append(normalized)
    body["sandbox_code_drafts"] = normalized_drafts


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


def _single_algorithm_estimator_id(
    implementation_targets: Any,
    *,
    implementation_gaps: list[Mapping[str, Any]],
) -> str:
    ids: set[str] = set()
    for row in implementation_targets or []:
        if isinstance(row, Mapping):
            estimator_id = str(row.get("estimator_id", "") or "").strip()
            if estimator_id:
                ids.add(estimator_id)
    for row in implementation_gaps:
        if isinstance(row, Mapping):
            estimator_id = str(row.get("estimator_id", row.get("id", "")) or "").strip()
            if estimator_id:
                ids.add(estimator_id)
    return next(iter(ids)) if len(ids) == 1 else ""


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM AlgorithmEngineer")
