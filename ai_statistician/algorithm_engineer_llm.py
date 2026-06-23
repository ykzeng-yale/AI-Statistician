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
                "explicit_model_configured": bool(self.config.model),
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_algorithm_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=str(
                    response.metadata.get("effective_model_tier", "")
                    or self.config.model_tier
                ),
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
        "theory_packet_summary": _compact_theory_packet_for_algorithm(theory_packet),
        "simulation_manifest_summary": _compact_simulation_manifest_for_algorithm(simulation_manifest),
        "implementation_gaps": _compact_implementation_gaps(implementation_gaps),
        "registered_runtime_templates": [
            {
                "template_id": "crossfit_aipw",
                "capability": "AIPW binary-treatment ATE sandbox with stress metrics",
                "execution_owner": "AgentRuntime",
            },
            {
                "template_id": "split_conformal_interval",
                "capability": "trusted split-conformal regression interval sandbox",
                "execution_owner": "AgentRuntime",
            }
        ],
        "generated_code_sandbox_contract": {
            "status": "optional fallback when no registered template matches",
            "language": "python",
            "entrypoint": "run_sandbox(seed: int, replicates: int) -> dict",
            "default": "leave sandbox_code_drafts empty when a registered template matches",
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
                    "sum",
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
        "Return ONLY one compact JSON object matching required_output_contract. Keep each list to "
        "exactly 1 short object or 1 short string. Include only required fields. Prefer registered runtime templates over "
        "sandbox_code_drafts; leave sandbox_code_drafts empty whenever a template matches. You may "
        "propose code and tests, but "
        "you must not claim you executed code, wrote files, promoted a production algorithm, or proved "
        "any theorem. Pick registered runtime templates only when their contract matches the estimator. "
        "For sandbox_code_drafts, obey the generated_code_sandbox_contract safe_subset exactly: do not "
        "use imports, NumPy/SciPy/sklearn/pandas/statsmodels/torch/JAX, class definitions, file/network "
        "operations, method calls, or attribute access except math.* and statistics.*. If the requested "
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
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)] + "...[truncated]"


ALGORITHM_ENGINEER_OUTPUT_CONTRACT: dict[str, Any] = {
    "implementation_targets": [
        {
            "estimator_id": "string",
            "adapter_strategy": "short string",
            "registered_template_hint": "crossfit_aipw|split_conformal_interval|none",
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
