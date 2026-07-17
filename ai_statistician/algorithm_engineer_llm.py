from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .generated_metric_repair_policy import (
    generated_code_sandbox_guard_repair_instruction,
    generated_python_sandbox_safe_subset_contract,
    generated_python_syntax_errors,
)
from .generated_metric_contract import (
    GENERATED_METRIC_CONTRACT_BOUNDARY,
    GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
    generated_metric_contract_set_id,
    generated_metric_requirements_for_subsystem,
    generated_metric_requirement_set_id,
    materialize_generated_metric_contract_bindings,
    validate_generated_metric_contracts,
)
from .algorithm_template_registry import (
    registered_algorithm_template_hint_contract,
    registered_algorithm_template_ids,
    registered_algorithm_template_prompt_rows,
)
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion
from .semantic_review_feedback import compact_semantic_review_feedback
from .scientific_sandbox import (
    PYTHON_SCIENTIFIC_DEPENDENCIES,
    R_SCIENTIFIC_DEPENDENCIES,
    generated_code_execution_contract_errors,
    normalized_generated_code_language,
    normalized_generated_code_profile,
    normalized_scientific_dependencies,
    scientific_sandbox_contract,
)
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
    model_tier: str = "sonnet"
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
        feedback = environment_feedback or {}
        requires_generated_code = _feedback_requires_generated_algorithm_code(
            feedback
        )
        user_prompt = build_algorithm_engineer_prompt(
            question=question,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            implementation_gaps=implementation_gaps,
            environment_feedback=feedback,
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        response_schema = _algorithm_engineer_response_schema(
            implementation_gaps=implementation_gaps,
            requires_generated_code=requires_generated_code,
        )
        provider_name = str(
            getattr(self.provider, "provider_name", self.config.provider_name)
            or self.config.provider_name
        ).lower()
        use_provider_structured_output = bool(
            requires_generated_code and provider_name == "anthropic"
        )
        request = GeneratorRequest(
            system_prompt=ALGORITHM_ENGINEER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=response_schema,
            metadata={
                "subsystem": "AlgorithmEngineer",
                "agent": "LLMAlgorithmEngineerAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
                **(
                    {"provider_structured_output": True}
                    if use_provider_structured_output
                    else {}
                ),
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
                requires_generated_code=requires_generated_code,
                authoritative_metric_requirements=[],
                metric_requirement_authority_policy=(
                    GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
                ),
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

        def build_repair_context(**_kwargs: Any) -> dict[str, Any]:
            return {
                "canonical_implementation_gap_ids": (
                    _canonical_implementation_gap_ids(implementation_gaps)
                ),
                "metric_contracts_required": False,
                "repair_prompt_priority_instructions": [
                    "Preserve every canonical estimator_id unchanged.",
                    "Repair the exact packet or generated-code defect.",
                    "Return metric_contracts as an empty array.",
                ],
                "boundary": ALGORITHM_ENGINEER_BOUNDARY,
            }

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_packet,
            validation_label="LLM AlgorithmEngineer packet",
            max_repair_attempts=self.config.max_repair_attempts,
            repair_context_builder=build_repair_context,
        )


def build_algorithm_engineer_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    implementation_gaps: list[Mapping[str, Any]],
    environment_feedback: Mapping[str, Any] | None = None,
) -> str:
    runtime_environment_feedback = _compact_algorithm_environment_feedback(
        environment_feedback or {}
    )
    requires_generated_code = _feedback_requires_generated_algorithm_code(
        runtime_environment_feedback
    )
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
        "canonical_implementation_gap_ids": _canonical_implementation_gap_ids(
            implementation_gaps
        ),
        "typed_metric_contract_schema": {},
        "metric_evaluation_semantics": {},
        "authoritative_empirical_metric_requirements": [],
        "metric_requirement_authority_policy": (
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
        ),
        "runtime_environment_feedback": runtime_environment_feedback,
        "registered_runtime_templates": registered_algorithm_template_prompt_rows(),
        "generated_code_sandbox_contract": {
            "status": "optional fallback when no registered template matches",
            "entrypoint": "run_sandbox",
            "function_signature": "def run_sandbox(seed: int, replicates: int) -> dict",
            "r_function_signature": "run_sandbox <- function(seed, replicates)",
            "estimator_entrypoint": "run_estimator",
            "estimator_function_signature": (
                "def run_estimator(request: dict) -> dict"
            ),
            "r_estimator_function_signature": (
                "run_estimator <- function(request)"
            ),
            "default": "leave sandbox_code_drafts empty when a registered template matches",
            "execution_contract": scientific_sandbox_contract(),
            "stdlib_safe_subset": generated_python_sandbox_safe_subset_contract(),
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
        "required_output_contract": _algorithm_engineer_output_contract(
            requires_generated_code=requires_generated_code,
        ),
        "boundary": ALGORITHM_ENGINEER_BOUNDARY,
    }
    if requires_generated_code:
        payload["generated_code_sandbox_contract"]["status"] = (
            "required for capability-eval coding-agent evidence"
        )
        payload["generated_code_sandbox_contract"]["default"] = (
            "include one safe sandbox_code_drafts entry for every canonical "
            "implementation gap even when a registered template also matches; "
            "templates may be referenced only as baselines"
        )
    generated_code_instruction = (
        (
            "Capability-eval mode is active: for every ID in "
            "canonical_implementation_gap_ids, include exactly one matching "
            "implementation_targets row and one safe sandbox_code_drafts row. "
            "Set metric_contracts to an empty array. Return meaningful finite "
            "smoke diagnostics that let the independent reviewer inspect implementation "
            "semantics. Do not invent a finite-sample performance gate: the downstream "
            "SimulationEngineer owns DGP-based statistical evaluation of this exact "
            "algorithm artifact. Define a domain-general JSON ABI entrypoint "
            "run_estimator(request) returning a named JSON-finite object, and make "
            "run_sandbox exercise that same function for smoke diagnostics. The "
            "request schema is owned by this generated algorithm and the supplied "
            "theory, not by AgentRuntime. Keep the metadata entrypoint exactly "
            "\"run_sandbox\" and code defining either Python "
            "def run_sandbox(seed: int, replicates: int) -> dict or R "
            "run_sandbox <- function(seed, replicates). Declare language, "
            "execution_profile, and only dependencies actually imported. Set every "
            "implementation_targets row registered_template_hint to none so AgentRuntime "
            "can test Claude-generated algorithm code execution. Registered templates may "
            "be named only in prose as baselines; they will not be executed for this "
            "capability gate. Treat each supplied implementation_gaps estimator_id as "
            "an exact task-artifact foreign key: copy it unchanged into the matching "
            "implementation_targets and sandbox_code_drafts rows rather than inventing "
            "a clearer alias. Use execution_profile=scientific_wasm when mature "
            "scientific Python libraries or R materially improve implementation "
            "fidelity; otherwise use the stdlib Python profile. "
        )
        if requires_generated_code
        else (
            "Prefer registered runtime templates over sandbox_code_drafts; leave "
            "sandbox_code_drafts empty whenever a template matches. "
        )
    )
    sandbox_guard_instruction = (
        generated_code_sandbox_guard_repair_instruction(
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
        "Produce one bounded safe algorithm run_sandbox draft for every canonical "
        "implementation-gap ID, expose run_estimator(request) in that exact source, "
        "exercise it from run_sandbox, expose the source through sandbox_code_drafts, leave "
        "metric_contracts empty, and let AgentRuntime execute it for this run. "
        "Do not satisfy this with a registered template, "
        "static replay, or component-gate artifact. "
        if _feedback_reports_coding_capability_feedback(
            payload["runtime_environment_feedback"]
        )
        else ""
    )
    packet_validation_instruction = (
        "Local packet-validator feedback is active: read every exact "
        "runtime_environment_feedback.validation_errors row and rebuild the full "
        "packet. Preserve every canonical estimator_id, repair the exact generated "
        "source or envelope defect, and leave metric_contracts empty. Statistical "
        "performance requirements belong to the downstream SimulationEngineer. "
        if str(
            payload["runtime_environment_feedback"].get("feedback_type", "") or ""
        )
        == "algorithm_engineer_packet_validation_feedback"
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
    semantic_review_instruction = (
        "Independent generated-code semantic review feedback is active: treat "
        "runtime_environment_feedback.generated_code_semantic_review as binding. "
        "Repair every rejected semantic dimension and finding against the exact "
        "reviewed source, runtime arguments, results, theory trace, and frozen metric "
        "protocol. Regenerate the draft and let AgentRuntime execute it again; do not "
        "respond by only changing metric paths or weakening a gate. "
        if payload["runtime_environment_feedback"].get(
            "generated_code_semantic_review"
        )
        else ""
    )
    estimator_abi_instruction = (
        "Mechanical estimator-ABI feedback is active: the independently reviewed "
        "algorithm source could not be invoked by the confirmatory DGP harness. Read "
        "runtime_environment_feedback.validation_errors, regenerate the exact source "
        "with callable run_estimator(request) returning a named JSON-finite object, "
        "and make run_sandbox exercise that same implementation before AgentRuntime "
        "executes and independently reviews it again. Do not change the estimator_id "
        "or move estimator semantics into SimulationEngineer. "
        if str(payload["runtime_environment_feedback"].get("feedback_type", "") or "")
        == "accepted_algorithm_estimator_abi_feedback"
        else ""
    )
    return (
        "Design implementation and sandbox-validation artifacts for the AlgorithmEngineer subsystem. "
        "Return ONLY one compact JSON object matching required_output_contract. Keep "
        "descriptive lists short, but include one implementation target, generated "
        "draft for every canonical gap ID, and an empty metric_contracts array. "
        "Include only required fields. "
        + generated_code_instruction
        + sandbox_guard_instruction
        + component_gate_instruction
        + capability_feedback_instruction
        + packet_validation_instruction
        + theory_trace_alignment_instruction
        + semantic_review_instruction
        + estimator_abi_instruction
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
        "For sandbox_code_drafts, obey the selected profile in "
        "generated_code_sandbox_contract. The stdlib profile permits only its "
        "listed pure-Python subset. Do not call bare helpers in that profile; "
        "use module-qualified calls. The scientific_wasm profile permits only "
        "declared pinned scientific packages or base R packages and forbids "
        "file/network/subprocess/host-bridge/reflection access. Prefer mature "
        "package APIs for numerical and statistical machinery. If the requested "
        "prototype cannot run under either profile, omit the draft and report the "
        "actual missing runtime capability. For this compact packet, do not include "
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
            feedback.get("architect_evidence_contract", {}),
            target_subsystem="AlgorithmEngineer",
        ),
        "runtime_requested_evidence_contract": _compact_architect_evidence_contract(
            feedback.get("runtime_requested_evidence_contract", {}),
            target_subsystem="AlgorithmEngineer",
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
        "generated_code_semantic_review": compact_semantic_review_feedback(
            feedback,
            expected_feedback_type="generated_code_semantic_review_feedback",
        ),
        "algorithm_sandbox_manifest_id": _truncate_text(
            feedback.get("algorithm_sandbox_manifest_id", ""),
            limit=180,
        ),
        "failure_classification": _truncate_text(
            feedback.get("failure_classification", ""),
            limit=180,
        ),
        "validation_label": _truncate_text(
            feedback.get("validation_label", ""),
            limit=180,
        ),
        "validation_errors": _compact_string_list(
            feedback.get("validation_errors", []),
            limit=12,
            char_limit=420,
        ),
        "validation_error_fingerprint": _truncate_text(
            feedback.get("validation_error_fingerprint", ""),
            limit=120,
        ),
        "same_error_runtime_round": feedback.get("same_error_runtime_round"),
        "packet_validation_replan_after_attempts": feedback.get(
            "packet_validation_replan_after_attempts"
        ),
        "packet_validation_replan_required": feedback.get(
            "packet_validation_replan_required"
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
                "metric_gate_policy_mode": _truncate_text(
                    row.get("metric_gate_policy_mode", ""),
                    limit=80,
                ),
                "metric_contract_set_id": _truncate_text(
                    row.get("metric_contract_set_id", ""),
                    limit=120,
                ),
                "metric_contracts": [
                    dict(contract)
                    for contract in _first_mapping_rows(
                        row.get("metric_contracts", []),
                        limit=4,
                    )
                ],
                "metric_contract_evaluation": _compact_mapping(
                    row.get("metric_contract_evaluation", {}),
                    limit=8,
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


def _compact_architect_evidence_contract(
    value: Any,
    *,
    target_subsystem: str,
) -> dict[str, Any]:
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
        "capability_eval_requires_typed_metric_contracts",
        "generated_metric_contract_policy",
        "generated_metric_requirement_authority_policy",
        "empirical_metric_requirements",
    )
    compact: dict[str, Any] = {}
    for key in keys:
        if key not in value:
            continue
        row = value.get(key)
        if key == "empirical_metric_requirements" and isinstance(row, list):
            compact[key] = generated_metric_requirements_for_subsystem(
                row,
                target_subsystem=target_subsystem,
            )[:8]
        elif isinstance(row, list):
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


def _canonical_implementation_gap_ids(value: Any) -> list[str]:
    """Return every nonempty Architect-owned implementation artifact key."""

    if not isinstance(value, list):
        return []
    return list(
        dict.fromkeys(
            str(row.get("estimator_id", row.get("id", "")) or "").strip()
            for row in value
            if isinstance(row, Mapping)
            and str(row.get("estimator_id", row.get("id", "")) or "").strip()
        )
    )


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


def _algorithm_engineer_output_contract(*, requires_generated_code: bool) -> dict[str, Any]:
    contract = dict(ALGORITHM_ENGINEER_OUTPUT_CONTRACT)
    if requires_generated_code:
        contract["sandbox_code_drafts"] = [
            {
                "estimator_id": (
                    "one row per canonical_implementation_gap_ids value; copy the "
                    "corresponding ID unchanged"
                ),
                "language": "python",
                "execution_profile": "stdlib or scientific_wasm",
                "dependencies": [],
                "entrypoint": "run_sandbox",
                "code": (
                    "def run_sandbox(seed: int, replicates: int) -> dict:\n"
                    "    return {'sandbox_failed': False}"
                ),
            }
        ]
        contract["metric_contracts"] = []
    return contract


def _algorithm_engineer_response_schema(
    *,
    implementation_gaps: list[Mapping[str, Any]],
    requires_generated_code: bool,
) -> dict[str, Any]:
    """Build a compact provider-native envelope for generated-code mode."""

    if not requires_generated_code:
        return ALGORITHM_ENGINEER_JSON_SCHEMA
    gap_ids = _canonical_implementation_gap_ids(implementation_gaps)
    estimator_id_schema: dict[str, Any] = {"type": "string", "minLength": 1}
    if gap_ids:
        estimator_id_schema["enum"] = gap_ids
    required_artifact_rows = max(1, len(gap_ids))
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "theory_trace_alignment",
            "implementation_targets",
            "sandbox_code_drafts",
            "metric_contracts",
            "next_actions",
        ],
        "properties": {
            "theory_trace_alignment": _theory_trace_alignment_json_schema(),
            "implementation_targets": {
                "type": "array",
                "minItems": required_artifact_rows,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["estimator_id", "registered_template_hint"],
                    "properties": {
                        "estimator_id": estimator_id_schema,
                        "adapter_strategy": {"type": "string"},
                        "registered_template_hint": {
                            "type": "string",
                            "enum": ["none"],
                        },
                        "data_contract": _string_array_json_schema(),
                        "validation_metrics": _string_array_json_schema(),
                        "risk_controls": _string_array_json_schema(),
                    },
                },
            },
            "sandbox_code_drafts": {
                "type": "array",
                "minItems": required_artifact_rows,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "estimator_id",
                        "language",
                        "execution_profile",
                        "dependencies",
                        "entrypoint",
                        "code",
                    ],
                    "properties": {
                        "estimator_id": estimator_id_schema,
                        "language": {"type": "string", "enum": ["python", "r"]},
                        "execution_profile": {
                            "type": "string",
                            "enum": ["stdlib", "scientific_wasm"],
                        },
                        "dependencies": {
                            "type": "array",
                            "uniqueItems": True,
                            "items": {
                                "type": "string",
                                "enum": list(
                                    PYTHON_SCIENTIFIC_DEPENDENCIES
                                    + R_SCIENTIFIC_DEPENDENCIES
                                ),
                            },
                        },
                        "entrypoint": {
                            "type": "string",
                            "enum": ["run_sandbox"],
                        },
                        "code": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 12000,
                        },
                    },
                },
            },
            "metric_contracts": {
                "type": "array",
                "maxItems": 0,
            },
            "next_actions": _next_actions_json_schema(),
        },
    }


def _theory_trace_alignment_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "referenced_derivation_steps",
            "referenced_equation_steps",
            "referenced_assumptions",
            "referenced_formalization_targets",
            "rationale",
        ],
        "properties": {
            "referenced_derivation_steps": _string_array_json_schema(),
            "referenced_equation_steps": _string_array_json_schema(),
            "referenced_assumptions": _string_array_json_schema(),
            "referenced_formalization_targets": _string_array_json_schema(),
            "rationale": {"type": "string"},
        },
    }


def _next_actions_json_schema() -> dict[str, Any]:
    return {
        "type": "array",
        "minItems": 1,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["owner_agent", "action", "acceptance_gate"],
            "properties": {
                "owner_agent": {"type": "string", "minLength": 1},
                "action": {"type": "string", "minLength": 1},
                "acceptance_gate": {"type": "string", "minLength": 1},
            },
        },
    }


def _string_array_json_schema() -> dict[str, Any]:
    return {
        "type": "array",
        "items": {"type": "string"},
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
        "metric_contracts": {"type": "array"},
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
        errors.extend(generated_code_execution_contract_errors(row))
        if str(row.get("entrypoint", "")).strip() not in {"", "run_sandbox"}:
            errors.append("sandbox_code_drafts entrypoint must be run_sandbox")
        if not str(row.get("estimator_id", "")).strip():
            errors.append("sandbox_code_drafts entry missing estimator_id")
        code = str(row.get("code", ""))
        if not code.strip():
            errors.append("sandbox_code_drafts entry missing code")
        if len(code) > 12000:
            errors.append("sandbox_code_drafts code exceeds 12000 characters")
    metric_contracts = packet.get("metric_contracts", [])
    if metric_contracts not in (None, [], {}):
        errors.extend(
            validate_generated_metric_contracts(
                metric_contracts,
                expected_artifact_ids=tuple(
                    str(row.get("estimator_id", "") or "").strip()
                    for row in packet.get("implementation_targets", []) or []
                    if isinstance(row, Mapping)
                    and str(row.get("estimator_id", "") or "").strip()
                ),
            )
        )
    return sorted(set(errors))


def _feedback_requires_generated_algorithm_code(feedback: Mapping[str, Any]) -> bool:
    """Return true when the Architect contract is testing coding-agent capacity."""

    if not isinstance(feedback, Mapping):
        return False
    semantic_review = feedback.get("generated_code_semantic_review", {})
    semantic_review = (
        semantic_review if isinstance(semantic_review, Mapping) else {}
    )
    if (
        str(
            feedback.get("feedback_type", "")
            or semantic_review.get("feedback_type", "")
            or ""
        )
        == "generated_code_semantic_review_feedback"
        and str(
            feedback.get("source_subsystem", "")
            or semantic_review.get("source_subsystem", "")
            or ""
        )
        == "AlgorithmEngineer"
    ):
        return True
    failure = str(feedback.get("failure_classification", "") or "")
    if failure in {
        "generated_algorithm_sandbox_metric_gate_failed",
        "generated_algorithm_sandbox_execution_failed",
        "generated_algorithm_sandbox_required_not_executed",
        "generated_algorithm_sandbox_repair_required",
        "coding_agent_component_gate_calibration_required",
        "accepted_algorithm_estimator_abi_failed",
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
    for row in drafts:
        if normalized_generated_code_language(row.get("language")) == "python":
            errors.extend(generated_python_syntax_errors(str(row.get("code", ""))))
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
    draft_ids = {
        str(row.get("estimator_id", "")).strip()
        for row in drafts
        if str(row.get("estimator_id", "")).strip()
    }
    expected_ids = gap_ids or target_ids
    missing_ids = expected_ids - draft_ids
    if missing_ids:
        errors.append(
            "capability_eval sandbox_code_drafts must bind every canonical "
            "implementation-gap estimator_id; missing: "
            + ", ".join(sorted(missing_ids))
        )
    if packet.get("metric_contracts", []) not in (None, [], {}):
        errors.append(
            "AlgorithmEngineer must leave metric_contracts empty; downstream "
            "SimulationEngineer owns empirical performance acceptance"
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
    requires_generated_code: bool = False,
    authoritative_metric_requirements: list[Mapping[str, Any]] | None = None,
    metric_requirement_authority_policy: str = "",
) -> dict[str, Any]:
    body = dict(payload)
    _normalize_algorithm_implementation_targets(
        body,
        implementation_gaps=implementation_gaps,
        requires_generated_code=requires_generated_code,
    )
    _normalize_algorithm_sandbox_code_drafts(
        body,
        implementation_gaps=implementation_gaps,
    )
    _normalize_algorithm_metric_contract_artifact_ids(
        body,
        implementation_gaps=implementation_gaps,
    )
    raw_metric_contracts = body.get("metric_contracts", [])
    metric_contract_values = (
        raw_metric_contracts if isinstance(raw_metric_contracts, list) else []
    )
    metric_contract_rows = [
        dict(row)
        for row in metric_contract_values
        if isinstance(row, Mapping)
    ]
    authority_rows = [
        dict(row)
        for row in authoritative_metric_requirements or []
        if isinstance(row, Mapping)
    ]
    metric_contract_rows = materialize_generated_metric_contract_bindings(
        metric_contract_rows,
        authoritative_requirements=authority_rows,
        target_subsystem="AlgorithmEngineer",
    )
    body["metric_contracts"] = metric_contract_rows
    body["metric_contract_set_id"] = generated_metric_contract_set_id(
        metric_contract_rows
    )
    body["empirical_metric_requirements"] = authority_rows
    body["metric_requirement_set_id"] = generated_metric_requirement_set_id(
        authority_rows
    )
    body["metric_requirement_authority_policy"] = (
        metric_requirement_authority_policy
    )
    body["metric_contract_proof_evidence_status"] = (
        GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
    )
    body["metric_contract_boundary"] = GENERATED_METRIC_CONTRACT_BOUNDARY
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
    canonical_gap_id = _single_algorithm_gap_estimator_id(implementation_gaps)
    default_estimator_id = _single_algorithm_estimator_id(
        body.get("implementation_targets", []),
        implementation_gaps=implementation_gaps,
    )
    mapping_draft_count = sum(isinstance(row, Mapping) for row in raw_drafts)
    normalized_drafts: list[Any] = []
    for row in raw_drafts:
        if not isinstance(row, Mapping):
            normalized_drafts.append(row)
            continue
        normalized = dict(row)
        if not str(normalized.get("estimator_id", "") or "").strip():
            alias = _algorithm_estimator_id_alias(normalized)
            if alias:
                normalized["estimator_id"] = alias
        language = normalized_generated_code_language(normalized.get("language"))
        normalized["language"] = language
        normalized["execution_profile"] = normalized_generated_code_profile(
            normalized.get("execution_profile"),
            language=language,
        )
        normalized["dependencies"] = list(
            normalized_scientific_dependencies(
                normalized.get("dependencies", []),
                language=language,
            )
        )
        if (
            default_estimator_id
            and not str(normalized.get("estimator_id", "") or "").strip()
        ):
            normalized["estimator_id"] = default_estimator_id
        if canonical_gap_id and mapping_draft_count == 1:
            _bind_algorithm_estimator_id_to_gap(
                normalized,
                canonical_gap_id=canonical_gap_id,
            )
        entrypoint = str(normalized.get("entrypoint", "") or "").strip()
        if _is_run_sandbox_signature_entrypoint(entrypoint):
            normalized["entrypoint"] = "run_sandbox"
        normalized_drafts.append(normalized)
    body["sandbox_code_drafts"] = normalized_drafts


def _normalize_algorithm_metric_contract_artifact_ids(
    body: dict[str, Any],
    *,
    implementation_gaps: list[Mapping[str, Any]],
) -> None:
    raw_contracts = body.get("metric_contracts", [])
    if not isinstance(raw_contracts, list):
        return
    canonical_gap_id = _single_algorithm_gap_estimator_id(implementation_gaps)
    if not canonical_gap_id:
        return
    normalized_contracts: list[Any] = []
    for row in raw_contracts:
        if not isinstance(row, Mapping):
            normalized_contracts.append(row)
            continue
        normalized = dict(row)
        source_artifact_id = str(
            normalized.get("artifact_id", "") or ""
        ).strip()
        if source_artifact_id != canonical_gap_id:
            normalized["artifact_id"] = canonical_gap_id
            normalized["artifact_id_binding"] = {
                "source_artifact_id": source_artifact_id,
                "canonical_artifact_id": canonical_gap_id,
                "binding_strategy": "single_gap_task_contract",
            }
        normalized_contracts.append(normalized)
    body["metric_contracts"] = normalized_contracts


def _normalize_algorithm_implementation_targets(
    body: dict[str, Any],
    *,
    implementation_gaps: list[Mapping[str, Any]],
    requires_generated_code: bool,
) -> None:
    raw_targets = body.get("implementation_targets", [])
    if not isinstance(raw_targets, list):
        return
    raw_drafts = body.get("sandbox_code_drafts", [])
    draft_rows = raw_drafts if isinstance(raw_drafts, list) else []
    has_code_draft = any(
        isinstance(row, Mapping) and str(row.get("code", "") or "").strip()
        for row in draft_rows
    )
    canonical_gap_id = _single_algorithm_gap_estimator_id(implementation_gaps)
    default_estimator_id = _single_algorithm_estimator_id(
        raw_targets,
        implementation_gaps=implementation_gaps,
    )
    mapping_target_count = sum(isinstance(row, Mapping) for row in raw_targets)
    normalized_targets: list[Any] = []
    for row in raw_targets:
        if not isinstance(row, Mapping):
            normalized_targets.append(row)
            continue
        normalized = dict(row)
        if not str(normalized.get("estimator_id", "") or "").strip():
            alias = _algorithm_estimator_id_alias(normalized)
            if alias:
                normalized["estimator_id"] = alias
            elif default_estimator_id:
                normalized["estimator_id"] = default_estimator_id
        if canonical_gap_id and mapping_target_count == 1:
            _bind_algorithm_estimator_id_to_gap(
                normalized,
                canonical_gap_id=canonical_gap_id,
            )
        if requires_generated_code and has_code_draft:
            normalized["registered_template_hint"] = "none"
        normalized_targets.append(normalized)
    body["implementation_targets"] = normalized_targets


def _algorithm_estimator_id_alias(row: Mapping[str, Any]) -> str:
    for key in (
        "estimator_id",
        "estimator",
        "target_estimator_id",
        "implementation_target_id",
        "id",
    ):
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _single_algorithm_gap_estimator_id(
    implementation_gaps: list[Mapping[str, Any]],
) -> str:
    ids = {
        str(row.get("estimator_id", row.get("id", "")) or "").strip()
        for row in implementation_gaps
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", row.get("id", "")) or "").strip()
    }
    return next(iter(ids)) if len(ids) == 1 else ""


def _bind_algorithm_estimator_id_to_gap(
    row: dict[str, Any],
    *,
    canonical_gap_id: str,
) -> None:
    """Bind one unambiguous generated target to the Architect-owned gap key."""

    source_id = str(row.get("estimator_id", "") or "").strip()
    row["estimator_id"] = canonical_gap_id
    if source_id and source_id != canonical_gap_id:
        row["estimator_id_binding"] = {
            "source_estimator_id": source_id,
            "canonical_estimator_id": canonical_gap_id,
            "binding_strategy": "single_gap_task_contract",
            "boundary": (
                "This is task-artifact identity normalization only; it does not "
                "change generated code or provide execution/proof evidence."
            ),
        }


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
