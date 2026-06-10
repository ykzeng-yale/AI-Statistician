from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion


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
    ) -> dict[str, Any]:
        user_prompt = build_algorithm_engineer_prompt(
            question=question,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            implementation_gaps=implementation_gaps,
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
                raw_response=raw_text,
                implementation_gaps=implementation_gaps,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_algorithm_engineer_packet,
            validation_label="LLM AlgorithmEngineer packet",
            max_repair_attempts=self.config.max_repair_attempts,
        )


def build_algorithm_engineer_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    implementation_gaps: list[Mapping[str, Any]],
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
        "simulation_manifest_summary": {
            "manifest_id": simulation_manifest.get("manifest_id", ""),
            "simulation_passed": simulation_manifest.get("simulation_passed"),
            "registered_procedures": simulation_manifest.get("registered_procedures", []),
            "simulations": simulation_manifest.get("simulations", []),
            "implementation_gaps": simulation_manifest.get("implementation_gaps", []),
        },
        "implementation_gaps": [dict(row) for row in implementation_gaps],
        "registered_runtime_templates": [
            {
                "template_id": "crossfit_aipw",
                "capability": "sandbox AIPW-style binary-treatment ATE prototype with nuisance fits and coverage stress metrics",
                "execution_owner": "AgentRuntime",
            },
            {
                "template_id": "split_conformal_interval",
                "capability": (
                    "trusted split-conformal regression interval sandbox with "
                    "exchangeable train/calibration/test simulation, empirical "
                    "coverage, interval width, and calibration quantile metrics"
                ),
                "execution_owner": "AgentRuntime",
            }
        ],
        "generated_code_sandbox_contract": {
            "status": "optional fallback when no registered template matches",
            "language": "python",
            "entrypoint": "run_sandbox(seed: int, replicates: int) -> dict",
            "safe_subset": {
                "allowed_globals": [
                    "math",
                    "statistics",
                    "abs",
                    "bool",
                    "dict",
                    "enumerate",
                    "float",
                    "int",
                    "len",
                    "list",
                    "max",
                    "min",
                    "pow",
                    "range",
                    "round",
                    "sorted",
                    "str",
                    "sum",
                    "tuple",
                ],
                "forbidden_dependencies": [
                    "numpy",
                    "scipy",
                    "sklearn",
                    "pandas",
                    "statsmodels",
                    "torch",
                    "jax",
                ],
                "forbidden_syntax": [
                    "import or from-import statements",
                    "class definitions",
                    "with blocks",
                    "global/nonlocal",
                    "file I/O, network, subprocess, eval, exec",
                    "method calls or attribute access except math.* and statistics.*",
                ],
                "fallback_rule": (
                    "If you cannot express the draft in this pure-Python safe subset, "
                    "leave sandbox_code_drafts empty and put the implementation details "
                    "in sandbox_plan/code_generation_plan instead."
                ),
            },
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
    return (
        "Design implementation and sandbox-validation artifacts for the AlgorithmEngineer subsystem. "
        "Return ONLY JSON matching required_output_contract. You may propose code and tests, but "
        "you must not claim you executed code, wrote files, promoted a production algorithm, or proved "
        "any theorem. Pick registered runtime templates only when their contract matches the estimator. "
        "For sandbox_code_drafts, obey the generated_code_sandbox_contract safe_subset exactly: do not "
        "use imports, NumPy/SciPy/sklearn/pandas/statsmodels/torch/JAX, class definitions, file/network "
        "operations, method calls, or attribute access except math.* and statistics.*. If the requested "
        "prototype needs those tools, omit sandbox_code_drafts and describe the registered-template or "
        "human-reviewed adapter plan instead.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )


ALGORITHM_ENGINEER_SYSTEM_PROMPT = """\
You are the LLM AlgorithmEngineer inside an AI Statistician AgentRuntime.

Your job is to turn theory-derived estimator specs into concrete implementation
plans, sandbox prototypes, data contracts, stress-test designs, and promotion
gates. You are a generator, not the executor. Do not run tools, do not write
files, do not report tests as passed, and do not claim proof evidence.
"""


ALGORITHM_ENGINEER_OUTPUT_CONTRACT: dict[str, Any] = {
    "implementation_targets": [
        {
            "estimator_id": "string",
            "adapter_strategy": "string",
            "registered_template_hint": "crossfit_aipw|split_conformal_interval|none",
            "data_contract": ["string"],
            "validation_metrics": ["string"],
            "risk_controls": ["string"],
        }
    ],
    "sandbox_plan": {
        "prototype_steps": ["string"],
        "stress_tests": ["string"],
        "expected_outputs": ["string"],
        "expected_failure_modes": ["string"],
    },
    "code_generation_plan": {
        "files_to_generate": ["string"],
        "functions_to_implement": ["string"],
        "dependencies": ["string"],
        "runtime_executor": "AgentRuntime",
    },
    "sandbox_code_drafts": [
        {
            "estimator_id": "string",
            "language": "python",
            "entrypoint": "run_sandbox",
            "code": (
                "def run_sandbox(seed: int, replicates: int) -> dict: ... "
                "# pure Python only: no imports, no numpy/sklearn/pandas/scipy, "
                "no method calls, no attribute access except math.* and statistics.*"
            ),
            "intended_metrics": ["string"],
            "safety_notes": ["string"],
        }
    ],
    "promotion_gate": {
        "required_tests": ["string"],
        "required_reproducibility_evidence": ["string"],
        "production_registration_requirements": ["string"],
    },
    "critic_findings": [
        {"critic": "string", "finding": "string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "string", "acceptance_gate": "string"}
    ],
}


ALGORITHM_ENGINEER_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "implementation_targets",
        "sandbox_plan",
        "code_generation_plan",
        "promotion_gate",
        "critic_findings",
        "next_actions",
    ],
    "properties": {
        "implementation_targets": {"type": "array", "minItems": 1},
        "sandbox_plan": {"type": "object"},
        "code_generation_plan": {"type": "object"},
        "sandbox_code_drafts": {"type": "array"},
        "promotion_gate": {"type": "object"},
        "critic_findings": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_algorithm_engineer_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "implementation_targets",
        "sandbox_plan",
        "code_generation_plan",
        "promotion_gate",
        "critic_findings",
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
        if template not in {"crossfit_aipw", "split_conformal_interval", "none"}:
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


def _normalize_algorithm_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    implementation_gaps: list[Mapping[str, Any]],
) -> dict[str, Any]:
    body = dict(payload)
    body["execution_evidence_status"] = ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE
    body["execution_evidence_boundary"] = ALGORITHM_ENGINEER_BOUNDARY
    body["proof_evidence_status"] = "NOT_PROOF_EVIDENCE"
    body["sandbox_executed"] = False
    body["production_registered"] = False
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
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


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM AlgorithmEngineer")
