from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .fingerprint import stable_hash
from .estimator_interface_contract import (
    estimator_interface_contract_errors as shared_estimator_interface_contract_errors,
    estimator_interface_contract_id,
    project_executable_estimator_spec,
    theory_estimator_interface_contracts,
)
from .generated_metric_contract import (
    GENERATED_METRIC_CONTRACT_BOUNDARY,
    GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
    generated_metric_contract_set_id,
    generated_metric_requirement_set_id,
    materialize_generated_metric_contract_bindings,
    validate_generated_metric_contracts,
)
from .structured_output_retry import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion, research_question_payload
from .semantic_review_feedback import coding_agent_observations_only
from .scientific_sandbox import (
    generated_code_draft_json_schema,
    generated_code_execution_contract_errors,
    generated_python_syntax_errors,
    normalized_generated_code_language,
    scientific_sandbox_contract,
)
from .scientific_code_workspace import (
    SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS,
    SCIENTIFIC_SOURCE_TRANSPORT_STRUCTURED_PACKET,
    ScientificCodeWorkspaceResult,
    run_scientific_code_workspace,
)
from .theory_derivation_trace import (
    compact_theory_derivation_trace,
    document_authoritative_theory_context,
    theory_trace_alignment_contract,
    theory_trace_alignment_json_schema,
    theory_trace_alignment_output_contract,
    theory_trace_alignment_prompt_instruction,
    theory_trace_consumption_contract,
)


ALGORITHM_ENGINEER_SCHEMA_VERSION = 2
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
    max_validation_retries: int = 1
    use_client_tool_code_workspace: bool = True
    client_tool_code_max_turns: int = 24
    client_tool_code_max_no_progress_turns: int = 2


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

    def source_workspace_owns_planning(self) -> bool:
        """Return whether one native source session can own planning and code."""

        return bool(
            self.config.use_client_tool_code_workspace
            and callable(
                getattr(self.provider, "generate_client_tool_turn", None)
            )
        )

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
        defer_source_authoring = bool(
            requires_generated_code
            and self.config.use_client_tool_code_workspace
            and callable(
                getattr(self.provider, "generate_client_tool_turn", None)
            )
        )
        user_prompt = build_algorithm_engineer_prompt(
            question=question,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            implementation_gaps=implementation_gaps,
            environment_feedback=feedback,
            defer_source_authoring=defer_source_authoring,
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        response_schema = _algorithm_engineer_response_schema(
            implementation_gaps=implementation_gaps,
            requires_generated_code=requires_generated_code,
            defer_source_authoring=defer_source_authoring,
            theory_packet=theory_packet,
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
                scientific_source_transport=(
                    SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
                    if defer_source_authoring
                    else SCIENTIFIC_SOURCE_TRANSPORT_STRUCTURED_PACKET
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

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_packet,
            validation_label="LLM AlgorithmEngineer packet",
            max_validation_retries=self.config.max_validation_retries,
        )

    def iterate_code_with_tools(
        self,
        *,
        question: OpenResearchQuestion,
        artifact_id: str,
        code_draft: Mapping[str, Any] | None,
        initial_observation: Mapping[str, Any],
        workspace_context: Mapping[str, Any],
        check_candidate: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        workspace_operation: str = "targeted_revision",
        allow_current_source_run: bool = False,
        recovery_checkpoint: Mapping[str, Any] | None = None,
        session_dir: Path | None = None,
    ) -> ScientificCodeWorkspaceResult:
        """Run one direct model -> sandbox -> same-model source loop."""

        if not self.config.use_client_tool_code_workspace:
            raise ValueError("AlgorithmEngineer client-tool code workspace is disabled")
        model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        return run_scientific_code_workspace(
            provider=self.provider,
            system_prompt=ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
            user_prompt=(
                "Continue the bound implementation workspace for this research task. "
                "The runtime executes source unchanged and supplies no correction rule.\n"
                + json.dumps(
                    {
                        "question": research_question_payload(question),
                        "workspace_context": dict(workspace_context),
                    },
                    separators=(",", ":"),
                    default=str,
                )
            ),
            model=model,
            model_tier=self.config.model_tier,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            max_turns=max(1, self.config.client_tool_code_max_turns),
            max_no_progress_turns=max(
                1, self.config.client_tool_code_max_no_progress_turns
            ),
            artifact_id=artifact_id,
            initial_code_draft=code_draft,
            initial_check_result=initial_observation,
            check_candidate=check_candidate,
            workspace_operation=workspace_operation,
            allow_current_source_run=allow_current_source_run,
            recovery_checkpoint=recovery_checkpoint,
            session_dir=session_dir,
            request_metadata={
                "subsystem": "AlgorithmEngineer",
                "agent": "LLMAlgorithmEngineerAgent",
                "phase": "scientific_code_workspace",
            },
        )


def build_algorithm_engineer_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    implementation_gaps: list[Mapping[str, Any]],
    environment_feedback: Mapping[str, Any] | None = None,
    defer_source_authoring: bool = False,
) -> str:
    runtime_environment_feedback = _algorithm_environment_observations(
        environment_feedback or {}
    )
    requires_generated_code = _feedback_requires_generated_algorithm_code(
        runtime_environment_feedback
    )
    payload = {
        "question": research_question_payload(question),
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
        "generated_code_sandbox_contract": {
            "status": "primary model-authored implementation path",
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
            "default": (
                "author complete source in the bound client-tool workspace"
                if defer_source_authoring
                else "generate complete sandbox source for each implementation gap"
            ),
            "execution_contract": scientific_sandbox_contract(),
            "runtime_policy": (
                "AgentRuntime validates the execution contract and runs drafts only "
                "inside a secret-free, network-denied, resource-bounded WebAssembly "
                "sandbox; raw failures are returned unchanged."
            ),
            "forbidden_claims": [
                "do not claim the draft was executed",
                "do not claim production registration",
                "do not claim theorem proof evidence",
            ],
        },
        "required_output_contract": _algorithm_engineer_output_contract(
            requires_generated_code=requires_generated_code,
            defer_source_authoring=defer_source_authoring,
            theory_packet=theory_packet,
        ),
        "boundary": ALGORITHM_ENGINEER_BOUNDARY,
    }
    if requires_generated_code:
        payload["generated_code_sandbox_contract"]["status"] = (
            "required for capability-eval coding-agent evidence"
        )
        payload["generated_code_sandbox_contract"]["default"] = (
            "include one safe sandbox_code_drafts entry for every canonical "
            "implementation gap"
        )
    if requires_generated_code and defer_source_authoring:
        generated_code_instruction = (
            "Capability-eval mode is active. For every canonical implementation-gap "
            "ID, emit exactly one matching implementation_targets row and one "
            "sandbox_code_drafts identity row. Copy each estimator_id unchanged. "
            "Do not embed source, language, dependencies, execution profile, or "
            "entrypoint in this planning envelope. Set metric_contracts to an empty "
            "array. After this envelope is accepted, the same source-owning model "
            "receives direct source and sandbox tools and must author and execute the "
            "complete candidate against the immutable TheoryDeveloper ABI. "
        )
    elif requires_generated_code:
        generated_code_instruction = (
            "Capability-eval mode is active. For every canonical implementation-gap "
            "ID, emit one matching target and complete source draft. Copy estimator_id "
            "unchanged, leave metric_contracts empty, export run_estimator(request) "
            "and run_sandbox(seed, replicates), and preserve the immutable "
            "TheoryDeveloper ABI. Declare the exact language, execution profile, and "
            "dependencies. Do not claim execution or statistical acceptance. "
        )
    else:
        generated_code_instruction = (
            "Use model-authored complete sandbox source for implementation gaps. "
        )
    feedback_regeneration_instruction = (
        "A previous candidate and its exact validator, execution, or independent-"
        "review observations are supplied in runtime_environment_feedback. When a "
        "complete hash-bound parent_source is present, treat it as immutable lineage. "
        + (
            "Regenerate only this compact planning envelope; source revision occurs "
            "in the following bound client-tool workspace. "
            if defer_source_authoring
            else "Regenerate the complete packet and complete source. "
        )
        + "Preserve immutable identities and contracts. You choose every source "
        "change; AgentRuntime does not propose edits. Treat the top-level "
        "CURRENT_ACTIVE_OBSERVATION as the current failure. Superseded observations "
        "are complete history for avoiding repeated failures, not active errors unless "
        "the current candidate re-observes them. "
        if payload["runtime_environment_feedback"]
        else ""
    )
    source_stage_instruction = (
        "Source selection, complete Python/R authoring, sandbox execution, and any "
        "revision happen only in the following bound client-tool workspace. "
        if defer_source_authoring
        else (
            "For each source draft, obey generated_code_sandbox_contract. Declare "
            "the exact profile and dependencies, use mature package APIs when useful, "
            "and avoid file, network, subprocess, host-bridge, or reflection access. "
            "Regenerate failed source from exact observations; AgentRuntime never "
            "edits model-authored source. "
        )
    )
    return (
        "Design implementation and sandbox-validation artifacts for the AlgorithmEngineer subsystem. "
        "Return ONLY one compact JSON object matching required_output_contract. Keep "
        "descriptive lists short, but include one implementation target, generated "
        "draft for every canonical gap ID, and an empty metric_contracts array. "
        "Include only required fields. "
        + generated_code_instruction
        + feedback_regeneration_instruction
        + "You may "
        "propose code and tests, but "
        "you must not claim you executed code, wrote files, promoted a production algorithm, or proved "
        "any theorem. "
        "When theory_packet_summary.document_authoritative is true, read every "
        "authoritative_theory_documents row as the mathematical authority; use "
        "theory_derivation_trace and estimator_specs only for claim identity and "
        "the executable ABI. Otherwise use the supplied legacy theory trace. "
        + theory_trace_alignment_prompt_instruction(theory_packet)
        + source_stage_instruction
        + "\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str)
    )


ALGORITHM_ENGINEER_SYSTEM_PROMPT = """\
You are the LLM AlgorithmEngineer inside an AI Statistician AgentRuntime.

Your job is to turn theory-derived estimator specs into concrete implementation
plans, sandbox prototypes, data contracts, stress-test designs, and promotion
gates. You are a generator, not the executor. Do not run tools, do not write
files, do not report tests as passed, and do not claim proof evidence.
"""


ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT = """\
You are the AlgorithmEngineer source owner inside an AI Statistician workspace.
Own one complete executable Python or R estimator candidate. Use the supplied
client tools to replace and run the exact source. Read every raw sandbox
observation and choose every source change yourself. The runtime executes source
unchanged and never supplies a correction rule. Do not answer with prose, delegate
an edit, weaken the task contract, or claim theorem-proof evidence.
Before commit_scientific_source, use submit_scientific_source to test the complete
immutable public ABI: valid and rejected requests, response schema, and transformations.
When workspace_context.theory_context.document_authoritative is true, read its
exact authoritative_theory_documents as the mathematical authority; structured
theory fields carry only claim identity and executable ABI.
"""


def _compact_theory_packet_for_algorithm(theory_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Expose only implementation-relevant theory fields to keep Haiku packets short."""

    theory_context = document_authoritative_theory_context(
        theory_packet,
        max_rows=3,
        text_limit=240,
    )
    if theory_context.get("document_authoritative"):
        return {
            "packet_id": theory_packet.get("packet_id", ""),
            "estimator_specs": [
                project_executable_estimator_spec(row)
                for row in _first_mapping_rows(
                    theory_packet.get("estimator_specs", []),
                    limit=2,
                )
            ],
            **theory_context,
        }

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
                "formula": _truncate_text(row.get("formula", ""), limit=600),
                "algorithm_sketch": _truncate_text(row.get("algorithm_sketch", ""), limit=500),
                "estimator_interface_contract": deepcopy(
                    row.get("estimator_interface_contract", {})
                ),
                "estimator_interface_contract_id": str(
                    row.get("estimator_interface_contract_id", "") or ""
                ),
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
        "theory_derivation_trace": theory_context.get(
            "theory_derivation_trace", {}
        ),
        "authoritative_theory_documents": [],
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


def _algorithm_environment_observations(
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Keep raw observations while withholding downstream acceptance gates."""

    if not isinstance(feedback, Mapping):
        return {}
    observations = coding_agent_observations_only(feedback)
    for contract_key in (
        "architect_evidence_contract",
        "runtime_requested_evidence_contract",
    ):
        contract = observations.get(contract_key)
        if not isinstance(contract, Mapping):
            continue
        projected_contract = dict(contract)
        projected_contract.pop("empirical_metric_requirements", None)
        observations[contract_key] = projected_contract
    return observations


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
        "referenced_claim_ids": ["exact claim_index ids consumed by this artifact"],
        "rationale": "short reason these claims are directly consumed",
    },
    "implementation_targets": [
        {
            "estimator_id": "string",
            "adapter_strategy": "short string",
            "data_contract": ["one short string"],
            "validation_metrics": ["one short string"],
            "risk_controls": ["one short string"],
        }
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "short string", "acceptance_gate": "short string"}
    ],
}


def algorithm_source_workspace_plan(
    *,
    proposal_agent: Any,
    enabled: bool,
    question_id: str,
    theory_packet_id: str,
    expected_estimator_ids: list[str],
) -> dict[str, Any]:
    """Select the single-session Codex-shaped planning/source path."""

    capability = getattr(proposal_agent, "source_workspace_owns_planning", None)
    owns_planning = bool(enabled and callable(capability) and capability())
    return {
        "owns_planning": owns_planning,
        "intent_id": (
            "algorithm_source_workspace_intent:"
            + stable_hash(
                [question_id, theory_packet_id, expected_estimator_ids]
            )[:20]
            if owns_planning
            else ""
        ),
    }


def materialize_algorithm_source_workspace_packet(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    implementation_gaps: list[Mapping[str, Any]],
    source_rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Project accepted model-owned source sessions into the review ABI."""

    expected_ids = [
        str(row.get("estimator_id", row.get("id", "")) or "").strip()
        for row in implementation_gaps
        if str(row.get("estimator_id", row.get("id", "")) or "").strip()
    ]
    rows_by_id = {
        str(row.get("estimator_id", "") or "").strip(): row
        for row in source_rows
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "").strip()
    }
    errors: list[str] = []
    source_artifacts: list[dict[str, Any]] = []
    providers: set[str] = set()
    models: set[str] = set()
    model_tiers: set[str] = set()
    for estimator_id in expected_ids:
        row = rows_by_id.get(estimator_id, {})
        workspace = row.get("scientific_code_workspace", {})
        workspace = workspace if isinstance(workspace, Mapping) else {}
        source_hash = str(row.get("script_hash", "") or "").strip()
        source_code = str(row.get("source_code", "") or "")
        if (
            row.get("smoke_passed") is not True
            or not source_code
            or source_hash != stable_hash(source_code)
        ):
            errors.append(f"{estimator_id}: accepted source bytes are not hash-bound")
        if not (
            workspace.get("accepted") is True
            and workspace.get("model_owned_source") is True
            and workspace.get("runtime_edited_source") is False
            and str(workspace.get("artifact_id", "") or "").strip()
            and str(
                workspace.get("transcript_fingerprint", "") or ""
            ).strip()
        ):
            errors.append(f"{estimator_id}: model-owned source evidence is invalid")
        source_artifacts.append(
            {
                "estimator_id": estimator_id,
                "source_hash": source_hash,
                "workspace_artifact_id": str(
                    workspace.get("artifact_id", "") or ""
                ),
                "workspace_transcript_fingerprint": str(
                    workspace.get("transcript_fingerprint", "") or ""
                ),
            }
        )
        for values, value in (
            (providers, workspace.get("provider", "")),
            (models, workspace.get("model", "")),
            (model_tiers, workspace.get("model_tier", "")),
        ):
            normalized = str(value or "").strip()
            if normalized:
                values.add(normalized)
    if not expected_ids or len(expected_ids) != len(set(expected_ids)):
        errors.append("source workspace estimator identities are empty or duplicated")
    if set(rows_by_id) != set(expected_ids):
        errors.append("source workspace rows do not exactly cover estimator IDs")
    if any(len(values) != 1 for values in (providers, models, model_tiers)):
        errors.append("source workspaces do not share one model identity")
    if errors:
        raise ValueError("; ".join(sorted(set(errors))))

    payload = {
        "implementation_targets": [
            {"estimator_id": estimator_id} for estimator_id in expected_ids
        ],
        "sandbox_code_drafts": [
            {"estimator_id": estimator_id} for estimator_id in expected_ids
        ],
        "metric_contracts": [],
        "next_actions": [],
        "source_workspace_planning_owned": True,
        "planning_model_call_used": False,
        "source_workspace_artifacts": source_artifacts,
    }
    packet = _normalize_algorithm_packet(
        payload,
        question=question,
        model=next(iter(models)),
        model_tier=next(iter(model_tiers)),
        provider_name=next(iter(providers)),
        backend_provider_name=next(iter(providers)),
        raw_response=json.dumps(source_artifacts, separators=(",", ":")),
        theory_packet=theory_packet,
        implementation_gaps=implementation_gaps,
        requires_generated_code=True,
        authoritative_metric_requirements=[],
        metric_requirement_authority_policy=(
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
        ),
        scientific_source_transport=(
            SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
        ),
    )
    validation_errors = validate_algorithm_engineer_packet(packet)
    validation_errors.extend(
        _validate_capability_eval_generated_algorithm_packet(
            packet,
            implementation_gaps=implementation_gaps,
        )
    )
    if validation_errors:
        raise ValueError("; ".join(sorted(set(validation_errors))))
    return packet


def _algorithm_engineer_output_contract(
    *,
    requires_generated_code: bool,
    defer_source_authoring: bool = False,
    theory_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = dict(ALGORITHM_ENGINEER_OUTPUT_CONTRACT)
    contract["theory_trace_alignment"] = theory_trace_alignment_output_contract(
        theory_packet or {}
    )
    if requires_generated_code:
        draft_contract = {
            "estimator_id": (
                "one row per canonical_implementation_gap_ids value; copy the "
                "corresponding ID unchanged"
            ),
        }
        if not defer_source_authoring:
            draft_contract.update(
                {
                    "language": "python or R",
                    "execution_profile": "stdlib or scientific_wasm",
                    "dependencies": (
                        "empty array for stdlib; otherwise include only packages "
                        "actually imported for scientific_wasm"
                    ),
                    "entrypoint": "run_sandbox",
                    "code": (
                        "complete source with module-level exported "
                        "run_estimator(request) and run_sandbox(seed, replicates); "
                        "run_sandbox exercises the exported estimator"
                    ),
                }
            )
        contract["sandbox_code_drafts"] = [draft_contract]
        contract["metric_contracts"] = []
    return contract


def _algorithm_engineer_response_schema(
    *,
    implementation_gaps: list[Mapping[str, Any]],
    requires_generated_code: bool,
    defer_source_authoring: bool = False,
    theory_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact provider-native envelope for generated-code mode."""

    if not requires_generated_code:
        schema = deepcopy(ALGORITHM_ENGINEER_JSON_SCHEMA)
        schema["properties"]["theory_trace_alignment"] = (
            theory_trace_alignment_json_schema(theory_packet or {})
        )
        return schema
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
            "theory_trace_alignment": theory_trace_alignment_json_schema(
                theory_packet or {}
            ),
            "implementation_targets": {
                "type": "array",
                "minItems": required_artifact_rows,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "estimator_id",
                    ],
                    "properties": {
                        "estimator_id": estimator_id_schema,
                        "adapter_strategy": {"type": "string"},
                        "data_contract": _string_array_json_schema(),
                        "validation_metrics": _string_array_json_schema(),
                        "risk_controls": _string_array_json_schema(),
                    },
                },
            },
            "sandbox_code_drafts": {
                "type": "array",
                "minItems": required_artifact_rows,
                "items": (
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["estimator_id"],
                        "properties": {
                            "estimator_id": estimator_id_schema,
                        },
                    }
                    if defer_source_authoring
                    else generated_code_draft_json_schema(
                        artifact_required=["estimator_id"],
                        artifact_properties={
                            "estimator_id": estimator_id_schema,
                        },
                    )
                ),
            },
            "metric_contracts": {
                "type": "array",
                "maxItems": 0,
            },
            "next_actions": _next_actions_json_schema(),
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
    source_workspace_planning_owned = bool(
        packet.get("source_workspace_planning_owned") is True
    )
    source_deferred = bool(
        packet.get("scientific_source_transport")
        == SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
    )
    required_fields = ["implementation_targets"]
    if not source_workspace_planning_owned:
        required_fields.append("next_actions")
    for field in required_fields:
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    if source_workspace_planning_owned:
        if packet.get("planning_model_call_used") is not False:
            errors.append("source-owned planning cannot claim a planning model call")
        artifacts = packet.get("source_workspace_artifacts", [])
        if not isinstance(artifacts, list) or not artifacts:
            errors.append("source-owned planning requires accepted source artifacts")
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
        interface_errors = _estimator_interface_contract_errors(
            row.get("estimator_interface_contract"),
            label=(
                "implementation target "
                + str(row.get("estimator_id", "") or "<unknown>")
            ),
            required=False,
        )
        errors.extend(interface_errors)
        interface = row.get("estimator_interface_contract")
        if isinstance(interface, Mapping):
            expected_interface_id = (
                "estimator_interface_contract:"
                + stable_hash(interface)[:20]
            )
            observed_interface_id = str(
                row.get("estimator_interface_contract_id", "") or ""
            )
            if (
                observed_interface_id
                and observed_interface_id != expected_interface_id
            ):
                errors.append(
                    "implementation target estimator interface contract id mismatch"
                )
        authority = row.get("estimator_interface_contract_authority", {})
        if isinstance(authority, Mapping) and authority.get("transport_status") == (
            "REJECTED_ALGORITHM_REDEFINITION"
        ):
            errors.append(
                "AlgorithmEngineer cannot redefine the TheoryDeveloper estimator "
                "interface contract"
            )
    for row in packet.get("sandbox_code_drafts", []) or []:
        if not isinstance(row, Mapping):
            errors.append("sandbox_code_drafts entries must be objects")
            continue
        if not str(row.get("estimator_id", "")).strip():
            errors.append("sandbox_code_drafts entry missing estimator_id")
        if source_deferred:
            unexpected = set(row) - {"estimator_id"}
            if unexpected:
                errors.append(
                    "client-tool source descriptors may contain only estimator_id"
                )
            continue
        errors.extend(generated_code_execution_contract_errors(row))
        if str(row.get("entrypoint", "")).strip() not in {"", "run_sandbox"}:
            errors.append("sandbox_code_drafts entrypoint must be run_sandbox")
        code = str(row.get("code", ""))
        if not code.strip():
            errors.append("sandbox_code_drafts entry missing code")
        if len(code) > 100_000:
            errors.append("sandbox_code_drafts code exceeds artifact-size boundary")
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
        "generated_algorithm_source_revision_required",
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
        and contract.get("research_evaluation_requires_generated_algorithm_code") is True
        for contract in contract_candidates
    )


def _validate_capability_eval_generated_algorithm_packet(
    packet: Mapping[str, Any],
    *,
    implementation_gaps: list[Mapping[str, Any]],
) -> list[str]:
    """Capability eval must exercise model-generated code."""

    errors: list[str] = []
    targets = [row for row in packet.get("implementation_targets", []) or [] if isinstance(row, Mapping)]
    drafts = [row for row in packet.get("sandbox_code_drafts", []) or [] if isinstance(row, Mapping)]
    source_deferred = bool(
        packet.get("scientific_source_transport")
        == SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
    )
    if not drafts:
        errors.append(
            "capability_eval requires at least one model-owned sandbox source descriptor"
        )
    if not source_deferred:
        for row in drafts:
            if normalized_generated_code_language(row.get("language")) == "python":
                errors.extend(generated_python_syntax_errors(str(row.get("code", ""))))
    target_ids = {
        str(row.get("estimator_id", "")).strip()
        for row in targets
        if str(row.get("estimator_id", "")).strip()
    }
    for row in targets:
        errors.extend(
            _estimator_interface_contract_errors(
                row.get("estimator_interface_contract"),
                label=(
                    "capability_eval implementation target "
                    + str(row.get("estimator_id", "") or "<unknown>")
                ),
                required=True,
            )
        )
        authority = row.get("estimator_interface_contract_authority", {})
        if not isinstance(authority, Mapping) or authority.get("owner_agent") != (
            "TheoryDeveloper"
        ):
            errors.append(
                "capability_eval estimator interface must be owned by TheoryDeveloper"
            )
        elif authority.get("transport_status") not in {
            "RUNTIME_BOUND_FROM_THEORY",
            "EXACT_MODEL_COPY",
        }:
            errors.append(
                "capability_eval estimator interface must be an exact immutable "
                "TheoryDeveloper contract"
            )
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
    scientific_source_transport: str = SCIENTIFIC_SOURCE_TRANSPORT_STRUCTURED_PACKET,
) -> dict[str, Any]:
    body = dict(payload)
    _normalize_algorithm_estimator_interface_contracts(
        body,
        theory_packet=theory_packet,
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
    body["scientific_source_transport"] = scientific_source_transport
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
        "question": research_question_payload(
            question,
            include_estimator_execution_contract=False,
        ),
        "implementation_gaps": [dict(row) for row in implementation_gaps],
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _normalize_algorithm_estimator_interface_contracts(
    body: dict[str, Any],
    *,
    theory_packet: Mapping[str, Any],
) -> None:
    targets = body.get("implementation_targets", [])
    if not isinstance(targets, list):
        return
    theory_contracts = theory_estimator_interface_contracts(theory_packet)
    source_theory_packet_id = str(theory_packet.get("packet_id", "") or "")
    source_theory_packet_hash = stable_hash(theory_packet)
    normalized_targets: list[Any] = []
    for row in targets:
        if not isinstance(row, Mapping):
            normalized_targets.append(row)
            continue
        normalized = dict(row)
        estimator_id = str(normalized.get("estimator_id", "") or "").strip()
        supplied_interface = normalized.get("estimator_interface_contract")
        theory_contract = theory_contracts.get(estimator_id)
        if theory_contract is not None:
            exact_interface = deepcopy(theory_contract["contract"])
            if not isinstance(supplied_interface, Mapping):
                transport_status = "RUNTIME_BOUND_FROM_THEORY"
            elif dict(supplied_interface) == exact_interface:
                transport_status = "EXACT_MODEL_COPY"
            else:
                transport_status = "REJECTED_ALGORITHM_REDEFINITION"
            normalized["estimator_interface_contract"] = exact_interface
            normalized["estimator_interface_contract_id"] = theory_contract[
                "contract_id"
            ]
            normalized["estimator_interface_contract_authority"] = {
                "owner_agent": "TheoryDeveloper",
                "source_theory_packet_id": source_theory_packet_id,
                "source_theory_packet_hash": source_theory_packet_hash,
                "source_estimator_ref": theory_contract["source_ref"],
                "transport_status": transport_status,
            }
        elif isinstance(supplied_interface, Mapping):
            interface_row = deepcopy(dict(supplied_interface))
            normalized["estimator_interface_contract"] = interface_row
            normalized["estimator_interface_contract_id"] = (
                estimator_interface_contract_id(interface_row)
            )
            normalized["estimator_interface_contract_authority"] = {
                "owner_agent": "UNBOUND_LEGACY",
                "source_theory_packet_id": source_theory_packet_id,
                "source_theory_packet_hash": source_theory_packet_hash,
                "source_estimator_ref": "",
                "transport_status": "UNBOUND_LEGACY_ALGORITHM_CONTRACT",
            }
        normalized_targets.append(normalized)
    body["implementation_targets"] = normalized_targets


def _estimator_interface_contract_errors(
    value: Any,
    *,
    label: str,
    required: bool,
) -> list[str]:
    return shared_estimator_interface_contract_errors(
        value,
        label=label,
        required=required,
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM AlgorithmEngineer")
