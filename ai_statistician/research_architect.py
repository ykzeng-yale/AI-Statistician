from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from .client_tool_loop import (
    CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY,
    externalize_client_tool_text_documents,
    read_hash_bound_utf8_file,
)
from .fingerprint import stable_hash
from .estimator_interface_contract import (
    ESTIMATOR_REQUEST_BINDINGS,
    frozen_estimator_execution_contract_alignment_errors,
    estimator_interface_contract_errors,
    estimator_interface_contract_id,
    normalize_theory_estimator_interface_contracts,
    theory_semantic_reference_ids,
)
from .model_backend import (
    AnthropicGeneratorBackend,
    GeneratorBackend,
    GeneratorRequest,
    GeneratorResponse,
    StaticJSONGeneratorBackend,
    resolve_generator_model,
)
from .packet_validation import PacketValidationError
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND,
)
from .research_schema import (
    OpenResearchQuestion,
    research_dimension_requirements,
    research_question_payload,
    research_workspace_authorization_fingerprint,
)
from .research_source_library import (
    ResearchSourceExecutionSpec,
    ResearchSourceSnapshot,
)
from .research_source_discovery import ResearchSourceDiscovery
from .theory_revision_lineage import (
    THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY,
    THEORY_DEVELOPER_RESOLVED_PARENT_MATERIAL_CONTEXT_KEY,
    theory_developer_revision_binding_errors,
)
from .theory_workspace import (
    SOURCE_REPLICATION_CHECKPOINT_KIND,
    THEORY_WORKSPACE_CONTENT_AUTHORITY,
    THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
    THEORY_WORKSPACE_HANDOFF_ROLE,
    THEORY_MODEL_REASONING_CONTRACT,
    THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND,
    THEORY_FILE_CLAIM_KINDS,
    THEORY_FILE_CLAIM_STATUSES,
    THEORY_FILE_SANITY_STATUSES,
    TheoryScratchpadConfig,
    load_theory_progress_checkpoint_state,
    load_theory_workspace_documents,
    run_theory_artifact_workspace,
    theory_workspace_manifest_errors,
)


ARCHITECT_SCHEMA_VERSION = 1
THEORY_DERIVATION_NOT_PROOF_EVIDENCE = "LLM_THEORY_DERIVATION_NOT_PROOF_EVIDENCE"
THEORY_PROMPT_MODE_COMPACT = "compact_theory_discovery_packet"
THEORY_PROMPT_MODE_SERIOUS_CAPABILITY = "serious_capability_theory_workspace"
THEORY_PROMPT_MODE_SERIOUS_REVISION = "serious_upstream_theory_revision"
THEORY_SERIOUS_PROMPT_MODES = (
    THEORY_PROMPT_MODE_SERIOUS_CAPABILITY,
    THEORY_PROMPT_MODE_SERIOUS_REVISION,
)
THEORY_DEVELOPER_PROGRESS_CHECKPOINT_CONTEXT_KEY = (
    "theory_developer_progress_checkpoint"
)
KERNEL_PROOF_BOUNDARY = (
    "LLM derivations, retrieval hits, and simulation predictions are proposal "
    "or diagnostic evidence only. Formal proof evidence requires AXLE/local "
    "Lean kernel verification of the intended formal claim."
)
THEORY_FORMAL_SOURCE_PROMPT_POLICY = (
    "Three ranked qualified declaration signatures are retained for semantic route "
    "comparison. Only the primary hit may carry one bounded declaration doc or "
    "citation; broad module prose and proof bodies are omitted."
)

def source_replication_checkpoint_allowed(
    question: OpenResearchQuestion,
    research_source_execution: ResearchSourceExecutionSpec | None,
) -> bool:
    """Use a narrow source checkpoint only when downstream theory is excluded."""
    if research_source_execution is None:
        return False
    requirements = research_dimension_requirements(question.task_intent)
    theory = requirements.get("theory")
    downstream = {requirements.get(d) for d in ("scientific_code", "empirical", "formal")}
    return bool(
        question.task_intent.get("source_replication") == "required"
        and (theory == "not_applicable" or (theory == "optional" and downstream == {"not_applicable"}))
    )


def theory_handoff_requirements(
    question: OpenResearchQuestion,
    *,
    formalization_authoring_required: bool,
) -> dict[str, bool]:
    """Select only the compact handoffs required by the frozen task intent."""

    dimensions = research_dimension_requirements(question.task_intent)
    implementation_required = bool(
        dimensions.get("scientific_code") == "required"
    )
    formal_handoff_required = bool(
        dimensions.get("formal") == "required"
        or (
            formalization_authoring_required
            and dimensions.get("formal") != "not_applicable"
        )
    )
    return {
        "problem_card": True,
        "theory_derivation_packet": True,
        "estimator_specs": implementation_required,
        "theorem_cards": formal_handoff_required,
        "simulation_ademp_spec": bool(
            dimensions.get("empirical") == "required"
        ),
        "formalization_requests": formal_handoff_required and formalization_authoring_required,
    }


def _selected_theory_handoff_fields(
    *,
    question: OpenResearchQuestion,
    formalization_authoring_required: bool,
    available_fields: Sequence[str],
) -> tuple[str, ...]:
    """Keep the prompt contract and writable tool surface capability-accurate."""

    requirements = theory_handoff_requirements(
        question,
        formalization_authoring_required=formalization_authoring_required,
    )
    selected = {
        field for field, required in requirements.items() if required
    }
    return tuple(field for field in available_fields if field in selected)


def _theory_output_contract_for_question(
    contract: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    formalization_authoring_required: bool,
) -> tuple[dict[str, Any], dict[str, bool]]:
    output = deepcopy(dict(contract))
    requirements = theory_handoff_requirements(
        question,
        formalization_authoring_required=formalization_authoring_required,
    )
    selected_fields = _selected_theory_handoff_fields(
        question=question,
        formalization_authoring_required=formalization_authoring_required,
        available_fields=tuple(output),
    )
    output = {
        field: output[field]
        for field in selected_fields
    }
    if not formalization_authoring_required:
        derivation_contract = output.get("theory_derivation_packet", {})
        if isinstance(derivation_contract, dict):
            derivation_contract.pop("formalization_handoff", None)
    return output, requirements


class ArchitectLLMProvider(GeneratorBackend, Protocol):
    """Compatibility alias for the older Architect provider boundary."""


class StaticArchitectLLMProvider(StaticJSONGeneratorBackend):
    """Offline provider for deterministic tests and reviewed response replay."""

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        return self.generate(
            GeneratorRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        ).text


class AnthropicArchitectLLMProvider(AnthropicGeneratorBackend):
    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        return self.generate(
            GeneratorRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        ).text


@dataclass(frozen=True)
class ResearchArchitectConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 4500
    serious_model: str = ""
    serious_model_tier: str = "sonnet"
    serious_max_tokens: int = 10000
    temperature: float = 0.2
    provider_name: str = "anthropic"
    theory_workspace_max_turns: int = 48
    theory_workspace_max_tool_calls: int = 96
    theory_workspace_max_no_progress_turns: int = 2


@dataclass(frozen=True)
class EvidenceLedgerRow:
    evidence_id: str
    question_id: str
    artifact_id: str
    artifact_kind: str
    source_agent: str
    evidence_status: str
    proof_evidence_status: str
    boundary: str
    created_at: str


class LLMTheoryDeveloperAgent:
    """LLM-backed statistical theory developer.

    This is the first runtime layer for the canonical Architect goal: it asks a
    frontier model to derive statistical theory artifacts, then validates and
    records them without promoting them to proof evidence.
    """

    def __init__(
        self,
        *,
        provider: GeneratorBackend | None = None,
        config: ResearchArchitectConfig = ResearchArchitectConfig(),
        research_sources: ResearchSourceSnapshot | None = None,
        research_source_discovery: ResearchSourceDiscovery | None = None,
        research_source_execution: ResearchSourceExecutionSpec | None = None,
    ) -> None:
        self.provider = provider or AnthropicArchitectLLMProvider()
        self.config = config
        self.research_sources = research_sources
        self.research_source_discovery = research_source_discovery
        self.research_source_execution = research_source_execution
        if research_source_execution is not None and research_sources is None:
            raise ValueError(
                "research source execution requires a research source snapshot"
            )

    def derive(
        self,
        question: OpenResearchQuestion,
        *,
        architect_context: Mapping[str, Any] | None = None,
        theory_scratchpad: TheoryScratchpadConfig | None = None,
        theory_workspace_root: Path | None = None,
    ) -> dict[str, Any]:
        context = dict(architect_context or {})
        theory_prompt_mode = _theory_developer_prompt_mode(context)
        dimension_requirements = research_dimension_requirements(
            question.task_intent
        )
        formal_requirement = dimension_requirements.get("formal")
        formalization_authoring_required = (
            formal_requirement == "required"
            if formal_requirement in {"required", "not_applicable"}
            else _theory_formalization_authoring_required(context)
        )
        serious_theory_mode = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
        effective_model_tier = (
            self.config.serious_model_tier
            if serious_theory_mode
            else self.config.model_tier
        )
        effective_max_tokens = (
            self.config.serious_max_tokens
            if serious_theory_mode
            else self.config.max_tokens
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=(
                self.config.serious_model
                if serious_theory_mode
                else self.config.model
            ),
            model_tier=effective_model_tier,
        )
        progress_checkpoint_state = (
            _theory_developer_progress_checkpoint_state(
                context,
                question=question,
                theory_prompt_mode=theory_prompt_mode,
            )
        )
        if (
            (
                self.research_sources is not None
                or self.research_source_discovery is not None
            )
            and not callable(
                getattr(self.provider, "generate_client_tool_turn", None)
            )
        ):
            raise PacketValidationError(
                validation_label="LLM TheoryDeveloper research-source workspace",
                attempts=0,
                errors=[
                    "configured research sources require native client-tool turns"
                ],
                history=[],
            )
        if theory_prompt_mode == THEORY_PROMPT_MODE_SERIOUS_REVISION:
            revision_inputs = build_theory_developer_revision_inputs(
                context,
                question=question,
            )
            if not callable(
                getattr(self.provider, "generate_client_tool_turn", None)
            ):
                raise PacketValidationError(
                    validation_label="LLM TheoryDeveloper artifact workspace",
                    attempts=0,
                    errors=[
                        "serious theory revision requires native client-tool turns"
                    ],
                    history=[],
                )
            core_packet = _generate_theory_workspace_revision(
                provider=self.provider,
                provider_name=self.config.provider_name,
                question=question,
                revision_inputs=revision_inputs,
                root_authorization_context=context,
                request_model=request_model,
                model_tier=effective_model_tier,
                base_model_tier=self.config.model_tier,
                configured_serious_model=self.config.serious_model,
                serious_model_tier=self.config.serious_model_tier,
                temperature=self.config.temperature,
                max_tokens=effective_max_tokens,
                max_turns=self.config.theory_workspace_max_turns,
                max_tool_calls=self.config.theory_workspace_max_tool_calls,
                max_no_progress_turns=(
                    self.config.theory_workspace_max_no_progress_turns
                ),
                formalization_authoring_required=(
                    formalization_authoring_required
                ),
                theory_scratchpad=theory_scratchpad,
                research_sources=self.research_sources,
                research_source_discovery=self.research_source_discovery,
                research_source_execution=self.research_source_execution,
                theory_workspace_root=theory_workspace_root,
                progress_checkpoint_state=progress_checkpoint_state,
            )
        elif callable(
            getattr(self.provider, "generate_client_tool_turn", None)
        ):
            core_packet = _generate_initial_theory_artifact_workspace(
                provider=self.provider,
                provider_name=self.config.provider_name,
                question=question,
                architect_context=context,
                theory_prompt_mode=theory_prompt_mode,
                request_model=request_model,
                model_tier=effective_model_tier,
                base_model_tier=self.config.model_tier,
                configured_serious_model=self.config.serious_model,
                serious_model_tier=self.config.serious_model_tier,
                temperature=self.config.temperature,
                max_tokens=effective_max_tokens,
                max_turns=self.config.theory_workspace_max_turns,
                max_tool_calls=self.config.theory_workspace_max_tool_calls,
                max_no_progress_turns=(
                    self.config.theory_workspace_max_no_progress_turns
                ),
                formalization_authoring_required=(
                    formalization_authoring_required
                ),
                theory_scratchpad=theory_scratchpad,
                research_sources=self.research_sources,
                research_source_discovery=self.research_source_discovery,
                research_source_execution=self.research_source_execution,
                theory_workspace_root=theory_workspace_root,
                progress_checkpoint_state=progress_checkpoint_state,
            )
        else:
            raise PacketValidationError(
                validation_label="LLM TheoryDeveloper document workspace",
                attempts=0,
                errors=[
                    "TheoryDeveloper requires native client-tool turns with a "
                    "model-authored Markdown/LaTeX workspace; JSON-only theory "
                    "generation is not a valid fallback"
                ],
                history=[],
            )
        if (
            core_packet.get("artifact_kind")
            == SOURCE_REPLICATION_CHECKPOINT_KIND
        ):
            return core_packet
        validation_errors = _validate_theory_packet_for_question(
            core_packet,
            question=question,
        )
        if validation_errors:
            raise PacketValidationError(
                validation_label="LLM TheoryDeveloper document workspace",
                attempts=0,
                errors=validation_errors,
                history=[],
                last_invalid_packet=core_packet,
            )
        return core_packet


class ResearchArchitectAgent:
    """First runtime slice for Architect-dispatched theory artifacts.

    This records LLM TheoryDeveloper output and evidence boundaries. It is not
    the complete plan-act-observe-revise AgentRuntime described in the project
    goal document.
    """

    def __init__(
        self,
        *,
        theory_developer: LLMTheoryDeveloperAgent,
        out_dir: Path,
    ) -> None:
        self.theory_developer = theory_developer
        self.out_dir = out_dir

    def run_theory_development(
        self,
        questions: list[OpenResearchQuestion],
        *,
        architect_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        packets: list[dict[str, Any]] = []
        ledger_rows: list[EvidenceLedgerRow] = []
        for question in questions:
            packet = self.theory_developer.derive(
                question,
                architect_context=architect_context or {},
                theory_workspace_root=self.out_dir / "theory_workspaces",
            )
            packets.append(packet)
            ledger_rows.append(_ledger_row_for_packet(packet, question))

        packet_path = self.out_dir / "theory_derivation_packets.jsonl"
        ledger_path = self.out_dir / "evidence_ledger.jsonl"
        project_state_path = self.out_dir / "architect_project_state.json"
        manifest_path = self.out_dir / "research_architect_manifest.json"
        report_path = self.out_dir / "research_architect.md"
        _write_jsonl(packet_path, packets)
        _write_jsonl(ledger_path, [asdict(row) for row in ledger_rows])
        project_state = _project_state(questions, packets, ledger_rows)
        project_state_path.write_text(json.dumps(project_state, indent=2, default=str), encoding="utf-8")
        manifest: dict[str, Any] = {
            "schema_version": ARCHITECT_SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "architect_stage": "llm_theory_development",
            "n_questions": len(questions),
            "n_theory_derivation_packets": len(packets),
            "n_evidence_ledger_rows": len(ledger_rows),
            "all_packets_ok": all(bool(packet.get("ok")) for packet in packets),
            "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            "artifacts": {
                "project_state": str(project_state_path),
                "theory_derivation_packets": str(packet_path),
                "evidence_ledger": str(ledger_path),
                "report": str(report_path),
            },
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        report_path.write_text(_markdown_report(manifest, packets), encoding="utf-8")
        return manifest



def _theory_developer_prompt_mode(
    architect_context: Mapping[str, Any],
) -> str:
    revision_binding = architect_context.get(
        THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY, {}
    )
    if isinstance(revision_binding, Mapping) and revision_binding:
        return THEORY_PROMPT_MODE_SERIOUS_REVISION
    environment_feedback = theory_developer_source_environment_feedback(
        architect_context
    )
    if (
        isinstance(environment_feedback, Mapping)
        and environment_feedback.get("artifact_kind")
        == METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND
    ):
        return THEORY_PROMPT_MODE_SERIOUS_REVISION
    architect_plan = architect_context.get("architect_runtime_plan", {})
    evidence_contract = (
        architect_plan.get("evidence_contract", {})
        if isinstance(architect_plan, Mapping)
        else {}
    )
    requested_contract = architect_context.get(
        "runtime_requested_evidence_contract", {}
    )
    if any(
        isinstance(contract, Mapping)
        and contract.get("evaluation_mode") in {"research_eval", "capability_eval"}
        for contract in (evidence_contract, requested_contract)
    ):
        return THEORY_PROMPT_MODE_SERIOUS_CAPABILITY
    return THEORY_PROMPT_MODE_COMPACT


def _theory_formalization_authoring_required(
    architect_context: Mapping[str, Any],
) -> bool:
    """Read the runtime-owned task intent without letting theory lower the gate."""

    contracts: list[Mapping[str, Any]] = []
    requested = architect_context.get("runtime_requested_evidence_contract", {})
    if isinstance(requested, Mapping):
        contracts.append(requested)
    architect_plan = architect_context.get("architect_runtime_plan", {})
    if isinstance(architect_plan, Mapping):
        plan_contract = architect_plan.get("evidence_contract", {})
        if isinstance(plan_contract, Mapping):
            contracts.append(plan_contract)
    for contract in contracts:
        explicit = contract.get("formal_target_authoring_required")
        if isinstance(explicit, bool):
            return explicit
        evaluation_mode = str(contract.get("evaluation_mode", "") or "")
        if evaluation_mode == "research_eval":
            return False
        if evaluation_mode == "capability_eval":
            return True
    return True


def theory_developer_source_environment_feedback(
    architect_context: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Return substantive feedback preserved across transport-level retries."""

    source_feedback = architect_context.get(
        "theory_developer_source_environment_feedback", {}
    )
    if isinstance(source_feedback, Mapping) and source_feedback:
        return source_feedback
    environment_feedback = architect_context.get("environment_feedback", {})
    if isinstance(environment_feedback, Mapping):
        return environment_feedback
    return {}


def _theory_developer_progress_checkpoint_state(
    architect_context: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    theory_prompt_mode: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]] | None:
    raw_checkpoint = architect_context.get(
        THEORY_DEVELOPER_PROGRESS_CHECKPOINT_CONTEXT_KEY,
        {},
    )
    if not raw_checkpoint:
        return None
    if not isinstance(raw_checkpoint, Mapping):
        raise PacketValidationError(
            validation_label="TheoryDeveloper progress checkpoint",
            attempts=0,
            errors=["TheoryDeveloper progress checkpoint must be an object"],
            history=[],
        )
    checkpoint = deepcopy(dict(raw_checkpoint))
    errors: list[str] = []
    expected_operation = (
        "targeted_revision"
        if theory_prompt_mode == THEORY_PROMPT_MODE_SERIOUS_REVISION
        else "initial_discovery"
    )
    if checkpoint.get("artifact_kind") != (
        THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND
    ):
        errors.append("TheoryDeveloper progress checkpoint kind mismatch")
    if checkpoint.get("workspace_operation") != expected_operation:
        errors.append(
            "TheoryDeveloper progress checkpoint operation does not match the "
            "current theory mode"
        )
    try:
        artifacts, documents = load_theory_progress_checkpoint_state(
            checkpoint,
            question_id=question.id,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(str(exc))
        artifacts, documents = {}, {}
    if artifacts:
        expected_fields = set(THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT)
        actual_fields = set(artifacts)
        missing_fields = sorted(expected_fields - actual_fields)
        extra_fields = sorted(actual_fields - expected_fields)
        if missing_fields:
            errors.append(
                "TheoryDeveloper progress checkpoint is missing handoff fields: "
                + ", ".join(missing_fields)
            )
        if extra_fields:
            errors.append(
                "TheoryDeveloper progress checkpoint has unknown handoff fields: "
                + ", ".join(extra_fields)
            )
        errors.extend(
            _output_contract_shape_errors(
                artifacts,
                THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT,
                path="",
            )
        )
    if errors:
        raise PacketValidationError(
            validation_label="TheoryDeveloper progress checkpoint",
            attempts=0,
            errors=list(dict.fromkeys(errors)),
            history=[],
        )
    return checkpoint, artifacts, documents


def _theory_progress_prompt_artifact(
    checkpoint: Mapping[str, Any],
) -> dict[str, Any]:
    progress = checkpoint.get("progress", {})
    progress = dict(progress) if isinstance(progress, Mapping) else {}
    scratch_keys = (
        "scratch_run",
        "status",
        "language",
        "execution_attempted",
        "returncode",
        "errors",
        "code_hash",
        "request_hash",
        "result_hash",
        "metrics_hash",
        "proof_evidence_status",
    )
    source_run_keys = (
        "artifact_id",
        "execution_status",
        "execution_attempted",
        "returncode",
        "errors",
        "stdout_sha256",
        "stderr_sha256",
        "manifest_hash",
        "proof_evidence_status",
    )
    return {
        "checkpoint_id": checkpoint.get("checkpoint_id", ""),
        "summary": progress.get("summary", ""),
        "evidence_refs": list(progress.get("evidence_refs", []) or []),
        "next_step": progress.get("next_step", ""),
        "current_workspace_hash": checkpoint.get("current_workspace_hash", ""),
        "changed_artifact_names": list(
            checkpoint.get("changed_artifact_names", []) or []
        ),
        "changed_document_paths": list(
            checkpoint.get("changed_document_paths", []) or []
        ),
        "removed_document_paths": list(
            checkpoint.get("removed_document_paths", []) or []
        ),
        "cumulative_tool_state": {
            "scratch_runs": int(checkpoint.get("scratch_runs", 0) or 0),
            "scratch_executions": [
                {
                    key: deepcopy(row[key])
                    for key in scratch_keys
                    if key in row
                }
                for row in checkpoint.get("scratch_execution_refs", []) or []
                if isinstance(row, Mapping)
            ],
            "source_searches": len(
                checkpoint.get("source_search_refs", []) or []
            ),
            "source_reads": len(
                checkpoint.get("source_read_refs", []) or []
            ),
            "public_source_searches": len(
                checkpoint.get("source_discovery_search_refs", []) or []
            ),
            "public_source_reads": len(
                checkpoint.get("source_discovery_read_refs", []) or []
            ),
            "source_replication_runs": int(
                checkpoint.get("source_replication_runs", 0) or 0
            ),
            "source_replication_executions": [
                {
                    key: deepcopy(row[key])
                    for key in source_run_keys
                    if key in row
                }
                for row in checkpoint.get(
                    "source_replication_manifests", []
                )
                or []
                if isinstance(row, Mapping)
            ],
            "source_result_reads": len(
                checkpoint.get("source_result_read_refs", []) or []
            ),
            "boundary": (
                "These are exact cumulative environment identities from the "
                "same source-owning workspace. They are observations, not "
                "mathematical acceptance, confirmatory evidence, or proof."
            ),
        },
        "proof_evidence_status": (
            "THEORY_PROGRESS_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }


def _compact_architect_context_for_prompt(context: Mapping[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {
        "compaction_note": (
            "This is a bounded TheoryDeveloper prompt view. Full Architect, "
            "retrieval, and trace artifacts remain in runtime outputs."
        )
    }
    for key in (
        "architect_coordinator_proposal_id",
        "retrieval_memory_manifest_id",
        "previous_theory_packet_id",
        "simulation_manifest_id",
        "formalization_manifest_id",
    ):
        if context.get(key) not in (None, "", [], {}):
            compact[key] = _truncate_text(context.get(key), 180)

    architect_plan = context.get("architect_runtime_plan")
    if isinstance(architect_plan, Mapping):
        compact["architect_runtime_plan_summary"] = _compact_architect_runtime_plan_for_prompt(architect_plan)

    retrieval_context = context.get("retrieval_context")
    if isinstance(retrieval_context, Mapping):
        compact["retrieval_context"] = _compact_retrieval_context_for_prompt(retrieval_context)

    runtime_task = context.get("runtime_task")
    if isinstance(runtime_task, Mapping):
        compact["runtime_task"] = {
            key: runtime_task.get(key)
            for key in (
                "task_id",
                "owner_subsystem",
                "objective",
                "allowed_tools",
                "expected_artifacts",
                "acceptance_gate",
                "stop_condition",
            )
            if key in runtime_task
        }

    return compact


def _initial_theory_authoring_binding_id(
    *,
    question_id: str,
    theory_prompt_mode: str,
    read_only_artifacts: Mapping[str, Any],
) -> str:
    binding_artifacts = deepcopy(dict(read_only_artifacts))
    initial_context = binding_artifacts.get("initial_authoring_context", {})
    if isinstance(initial_context, Mapping):
        initial_context = deepcopy(dict(initial_context))
        prompt_context = initial_context.get("architect_context", {})
        if isinstance(prompt_context, Mapping):
            prompt_context = deepcopy(dict(prompt_context))
            runtime_task = prompt_context.get("runtime_task", {})
            if isinstance(runtime_task, Mapping):
                runtime_task = deepcopy(dict(runtime_task))
                # A continuation is a new scheduling message for the same workspace.
                runtime_task.pop("task_id", None)
                prompt_context["runtime_task"] = runtime_task
            initial_context["architect_context"] = prompt_context
        binding_artifacts["initial_authoring_context"] = initial_context
    return "initial_theory_authoring:" + stable_hash(
        [question_id, theory_prompt_mode, binding_artifacts]
    )[:20]


def _compact_architect_runtime_plan_for_prompt(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "problem_analysis": _compact_prompt_mapping(
            plan.get("problem_analysis", {}),
            keys=(
                "theorem_family",
                "statistical_objects",
                "assumption_dimensions",
                "likely_analogy_classes",
                "key_obstacles",
                "missing_information",
            ),
            list_limit=4,
            text_limit=240,
        ),
        "retrieval_strategy": _compact_prompt_mapping(
            plan.get("retrieval_strategy", {}),
            keys=("paper_queries", "formal_source_queries", "lean_rag_priorities"),
            list_limit=3,
            text_limit=180,
        ),
        "evidence_contract": _compact_prompt_mapping(
            plan.get("evidence_contract", {}),
            keys=(
                "formal_verification_policy",
                "recommended_research_path",
                "formal_required_for_final",
                "formal_targets",
                "simulation_targets",
                "acceptance_modes",
                "disclosure_requirements",
            ),
            list_limit=3,
            text_limit=220,
        ),
        "iteration_policy": _compact_prompt_mapping(
            plan.get("iteration_policy", {}),
            keys=("stop_conditions",),
            list_limit=3,
            text_limit=220,
        ),
        "boundary": _truncate_text(plan.get("boundary", ""), 360),
    }


def _compact_retrieval_context_for_prompt(retrieval_context: Mapping[str, Any]) -> dict[str, Any]:
    knowledge_cards = list(retrieval_context.get("knowledge_cards", []) or [])
    paper_sources = list(retrieval_context.get("paper_sources", []) or [])
    formal_source_hits = list(retrieval_context.get("formal_source_hits", []) or [])
    return {
        "counts": {
            "knowledge_cards": len(knowledge_cards),
            "paper_sources": len(paper_sources),
            "formal_source_hit_groups": len(formal_source_hits),
            "formal_source_hits": sum(
                len(row.get("hits", []) or [])
                for row in formal_source_hits
                if isinstance(row, Mapping)
            ),
        },
        "knowledge_cards": [_compact_knowledge_card(row) for row in knowledge_cards[:3]],
        "paper_sources": [_compact_paper_source(row) for row in paper_sources[:3]],
        "formal_source_prompt_policy": THEORY_FORMAL_SOURCE_PROMPT_POLICY,
        "formal_source_hits": [_compact_formal_hit_group(row) for row in formal_source_hits[:2]],
        "boundary": retrieval_context.get("boundary", ""),
        "compaction_note": (
            "Full retrieval artifacts remain in runtime outputs; this prompt view "
            "is bounded to reduce API cost and connection fragility."
        ),
    }


def _compact_knowledge_card(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    return {
        "id": row.get("id", ""),
        "title": row.get("title", ""),
        "source_type": row.get("source_type", ""),
        "summary": _truncate_text(row.get("summary", ""), 240),
        "tags": list(row.get("tags", []) or [])[:6],
    }


def _compact_paper_source(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    return {
        "id": row.get("id", ""),
        "title": row.get("title", ""),
        "journal": row.get("journal", ""),
        "topic": row.get("topic", ""),
        "publication_date": row.get("publication_date", ""),
        "summary": _truncate_text(row.get("summary", ""), 240),
        "matched_terms": list(row.get("matched_terms", []) or [])[:8],
    }


def _compact_formal_hit_group(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240), "hits": []}
    hits = list(row.get("hits", []) or [])
    return {
        "theorem_goal_id": row.get("theorem_goal_id", ""),
        "n_hits": len(hits),
        "hits": [
            _compact_formal_hit(hit, primary=index == 0)
            for index, hit in enumerate(hits[:3])
        ],
    }


def _compact_formal_hit(hit: Any, *, primary: bool) -> dict[str, Any]:
    if not isinstance(hit, Mapping):
        return {"summary": _truncate_text(hit, 240)}
    compact = {
        "source_id": hit.get("source_id", ""),
        "path": hit.get("path", ""),
        "line": hit.get("line", ""),
        "kind": hit.get("kind", ""),
        "name": _truncate_text(hit.get("name", ""), 140),
        "namespace": _truncate_text(hit.get("namespace", ""), 140),
        "score": hit.get("score", ""),
        "matched_terms": list(hit.get("matched_terms", []) or [])[:8],
        "proof_body_included": False,
    }
    for key, limit in (("signature", 520),):
        value = str(hit.get(key, "") or "").strip()
        if value:
            compact[key] = _truncate_text(value, limit)
    if primary:
        for key, limit in (("declaration_doc", 320), ("reference", 180)):
            value = str(hit.get(key, "") or "").strip()
            if value:
                compact[key] = _truncate_text(value, limit)
    return {
        key: value
        for key, value in compact.items()
        if value not in (None, "", [], {})
    }


def _compact_prompt_mapping(
    row: Any,
    *,
    keys: tuple[str, ...],
    list_limit: int,
    text_limit: int,
) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {}
    return {
        key: _compact_prompt_value(row.get(key), list_limit=list_limit, text_limit=text_limit)
        for key in keys
        if row.get(key) not in (None, "", [], {})
    }


def _compact_prompt_value(value: Any, *, list_limit: int, text_limit: int) -> Any:
    if isinstance(value, str):
        return _truncate_text(value, text_limit)
    if isinstance(value, Mapping):
        return {
            str(key): _compact_prompt_value(child, list_limit=list_limit, text_limit=text_limit)
            for key, child in list(value.items())[:list_limit]
            if child not in (None, "", [], {})
        }
    if isinstance(value, (list, tuple)):
        return [
            _compact_prompt_value(child, list_limit=list_limit, text_limit=text_limit)
            for child in list(value)[:list_limit]
        ]
    return value


def _truncate_text(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, (list, tuple)) else 0


THEORY_DEVELOPER_SYSTEM_PROMPT = (
    "You are the TheoryDeveloper inside an AI Statistician. Develop research-level "
    "statistical theory with equation-level reasoning in durable Markdown or LaTeX. "
    "Own the setup, estimand, procedure semantics, claims, derivations, uncertainty, "
    "and compact downstream interfaces; AlgorithmEngineer owns deliverable Python or "
    "R source. Scratch and retrieval are observations, never substitutes for an "
    "argument. Treat active documents as the publishable current theory rather than a "
    "chronology: remove false work or delimit it as SCRATCH or REJECTED. "
    + THEORY_MODEL_REASONING_CONTRACT
    + " Before checkpoint, inspect the current argument as its skeptical author and "
    "leave unresolved mathematics explicit. Do not claim execution, independent "
    "review, empirical confirmation, formal proof, or kernel authority."
)


THEORY_DEVELOPER_OUTPUT_CONTRACT: dict[str, Any] = {
    "problem_card": {
        "observed_data": "string",
        "dgp": "string",
        "estimand": "string",
        "nuisance_quantities": ["string"],
        "assumptions": ["string"],
        "asymptotic_regime": "string",
        "desired_theorem_type": "string",
    },
    "theory_derivation_packet": {
        "derivation_summary": "string",
        "derivation_steps": [
            {
                "id": "short id",
                "claim": "string",
                "equation_or_argument": "string",
                "depends_on": ["ids"],
                "formal_goal": "theorem_card_id or lemma_card_id",
                "risk": "string",
            }
        ],
        "equation_chain": [
            {
                "step_id": "short id",
                "lhs": "string",
                "relation": "=|≈|<=|=>|converges_to|implies",
                "rhs": "string",
                "justification": "string",
                "depends_on": ["derivation_step ids"],
            }
        ],
        "assumption_ledger": [
            {
                "assumption": "string",
                "role": "optional short semantic label, such as identification or regularity",
                "used_in": ["derivation/equation/theorem ids"],
                "risk_if_dropped": "string",
            }
        ],
        "sanity_checks": [
            {
                "id": "short id",
                "claim_ref": "derivation/equation/assumption/procedure id",
                "check_type": (
                    "direct_substitution|normalization|boundary_case|"
                    "uncertainty_scale|inequality_direction|dimensional_consistency"
                ),
                "recomputation": "explicit substituted expression or calculation",
                "result": (
                    "computed or logically reduced result with an explicit model-authored "
                    "PASS|FAIL|INCONCLUSIVE disposition; never hide an unresolved check"
                ),
                "depends_on": ["source ids"],
            }
        ],
        "formalization_handoff": {
            "source_theorem_target": "theorem_card_id",
            "candidate_lean_targets": ["string"],
            "required_definitions": ["string"],
            "lemma_dependencies": ["lemma_card or derivation ids"],
            "semantic_alignment_constraints": ["string"],
        },
        "self_critique": ["string"],
        "rejected_alternatives": [{"name": "string", "reason": "string"}],
    },
    "estimator_specs": [
        {
            "id": "short id",
            "name": "string",
            "formula": "string",
            "algorithm_sketch": "string",
            "inputs": ["string"],
            "outputs": ["string"],
            "output_contract": (
                "typed behavior for every admitted input, including bounded, "
                "censored, unavailable, or timeout outcomes when applicable"
            ),
            "termination_guarantee": (
                "why execution is total, or the exact resource bound and typed "
                "outcome used when the ideal procedure does not terminate"
            ),
            "normalization": "string",
            "tuning": ["string"],
            "required_assumptions": ["string"],
            "estimator_interface_contract": {
                "request_fields": [
                    {
                        "name": "field name",
                        "meaning": "statistical meaning",
                        "binding": "|".join(ESTIMATOR_REQUEST_BINDINGS),
                    }
                ],
                "response_fields": [
                    {
                        "name": "field name",
                        "meaning": "statistical meaning",
                        "normalization": "exact finite-sample or asymptotic convention",
                        "derivation_ref": (
                            "derivation, equation, sanity-check, theorem, or lemma id"
                        ),
                    }
                ],
            },
        }
    ],
    "theorem_cards": [
        {
            "id": "short id",
            "informal_statement": "string",
            "assumptions_used": ["string"],
            "conclusion": "string",
            "rate_or_limit_law": "string",
            "proof_strategy": "string",
            "semantic_risks": ["string"],
        }
    ],
    "lemma_cards": [
        {
            "id": "short id",
            "statement": "string",
            "depends_on": ["ids"],
            "used_by": ["ids"],
            "formalization_difficulty": "low|medium|high",
        }
    ],
    "proof_plan": {
        "proof_dependency_dag": [{"from": "id", "to": "id"}],
        "required_primitives": ["string"],
        "acceptable_strengthening": ["string"],
        "unacceptable_changes": ["string"],
    },
    "formalization_requests": [
        {
            "id": "short id",
            "target_theorem_card": "id",
            "lean_statement_sketch": "string",
            "semantic_alignment_constraints": ["string"],
            "kernel_status": "OPEN",
        }
    ],
    "simulation_ademp_spec": {
        "aim": "string",
        "dgps": ["string"],
        "methods": ["string"],
        "performance_measures": ["string"],
        "stress_tests": ["string"],
        "expected_theoretical_behavior": ["string"],
    },
    "critic_findings": [
        {"critic": "string", "finding": "string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "string", "acceptance_gate": "string"}
    ],
}


THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT = deepcopy(
    THEORY_DEVELOPER_OUTPUT_CONTRACT
)
del THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT["estimator_specs"][0][
    "estimator_interface_contract"
]

THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT: dict[str, Any] = {
    "problem_card": {
        "claim_ids": [
            "claim_index ids that locate the load-bearing setup and research target"
        ],
    },
    "theory_derivation_packet": {
        "claim_index": [
            {
                "id": "stable claim or equation id",
                "kind": "|".join(THEORY_FILE_CLAIM_KINDS),
                "document_path": "workspace-relative .md or .tex path",
                "depends_on": ["direct predecessor claim_index ids"],
                "status": "|".join(THEORY_FILE_CLAIM_STATUSES),
            }
        ],
        "formalization_handoff": {
            "source_theorem_target": "exact theorem_cards id",
        },
    },
    "estimator_specs": [
        {
            "id": "stable executable estimator id",
            "name": "short human-readable name",
            "estimator_interface_contract": deepcopy(
                THEORY_DEVELOPER_OUTPUT_CONTRACT["estimator_specs"][0][
                    "estimator_interface_contract"
                ]
            ),
        }
    ],
    "theorem_cards": [
        {
            "id": "exact theorem claim_index id",
            "document_path": "workspace-relative .md or .tex path",
        }
    ],
    "formalization_requests": [
        {
            "id": "stable formalization request id",
            "target_theorem_card": "exact theorem_cards id",
        }
    ],
    "simulation_ademp_spec": {
        "claim_ids": [
            "claim_index ids whose predictions the Simulation owner should investigate"
        ],
    },
}


def validate_theory_packet(packet: Mapping[str, Any]) -> list[str]:
    return _validate_theory_packet(
        packet,
        require_estimator_interfaces=True,
    )


def _validate_theory_packet_for_question(
    packet: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
) -> list[str]:
    errors = validate_theory_packet(packet)
    errors.extend(_canonical_estimator_interface_alignment_errors(packet))
    errors.extend(
        frozen_estimator_execution_contract_alignment_errors(
            packet,
            question.estimator_execution_contract,
        )
    )
    return list(dict.fromkeys(errors))


def _canonical_estimator_interface_alignment_errors(
    packet: Mapping[str, Any],
) -> list[str]:
    """Keep the committed cross-agent ABI exact without interpreting statistics."""

    errors: list[str] = []
    for index, row in enumerate(packet.get("estimator_specs", []) or []):
        if not isinstance(row, Mapping):
            continue
        contract = row.get("estimator_interface_contract")
        if not isinstance(contract, Mapping):
            continue
        unexpected_paths = _unexpected_executable_interface_paths(contract)
        if unexpected_paths:
            errors.append(
                f"estimator_specs[{index}].estimator_interface_contract has "
                "unsupported fields: "
                + ", ".join(unexpected_paths)
                + "; allowed executable ABI fields are request_fields[*]."
                "{name,meaning,binding} and response_fields[*]."
                "{name,meaning,normalization,derivation_ref}"
            )
        outputs = row.get("outputs", [])
        response_fields = contract.get("response_fields", [])
        if (
            isinstance(outputs, list)
            and outputs
            and isinstance(response_fields, list)
            and len(response_fields) != len(outputs)
        ):
            errors.append(
                f"estimator_specs[{index}] response_fields must correspond "
                f"one-for-one to the {len(outputs)} estimator outputs; received "
                f"{len(response_fields)}"
            )
    return errors


def _unexpected_executable_interface_paths(
    contract: Mapping[str, Any],
) -> list[str]:
    """Name unsupported ABI paths so the source owner can revise its own payload."""

    allowed_rows = {
        "request_fields": {"name", "meaning", "binding"},
        "response_fields": {
            "name",
            "meaning",
            "normalization",
            "derivation_ref",
        },
    }
    paths = [str(key) for key in sorted(set(contract) - set(allowed_rows))]
    for collection, allowed_fields in allowed_rows.items():
        rows = contract.get(collection, [])
        if not isinstance(rows, list):
            continue
        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                continue
            paths.extend(
                f"{collection}[{row_index}].{key}"
                for key in sorted(set(row) - allowed_fields)
            )
    return paths


def validate_theory_core_packet(packet: Mapping[str, Any]) -> list[str]:
    """Validate mathematical content before executable interface authoring."""

    return _validate_theory_packet(
        packet,
        require_estimator_interfaces=False,
    )


def _output_contract_shape_errors(
    value: Any,
    contract: Any,
    *,
    path: str,
) -> list[str]:
    """Validate present values against the declared transport shape."""

    if isinstance(contract, Mapping):
        if not isinstance(value, Mapping):
            return [f"{path} must be an object"]
        return [
            error
            for key, child_contract in contract.items()
            if key in value
            for error in _output_contract_shape_errors(
                value[key],
                child_contract,
                path=f"{path}.{key}" if path else str(key),
            )
        ]
    if isinstance(contract, list):
        if not isinstance(value, list):
            return [f"{path} must be a list"]
        if not contract:
            return []
        return [
            error
            for index, child in enumerate(value)
            for error in _output_contract_shape_errors(
                child,
                contract[0],
                path=f"{path}[{index}]",
            )
        ]
    if not isinstance(value, str):
        return [f"{path} must be a string"]
    return []


def _file_theory_index_errors(
    derivation: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    manifest = packet.get("theory_workspace_manifest", {})
    document_paths = {
        str(row.get("relative_path", "") or "")
        for row in (
            manifest.get("documents", [])
            if isinstance(manifest, Mapping)
            else []
        )
        if isinstance(row, Mapping)
    }
    claim_rows = derivation.get("claim_index", [])
    if not isinstance(claim_rows, list) or not claim_rows:
        errors.append("theory_derivation_packet.claim_index must be non-empty")
        claim_rows = []
    claim_ids: list[str] = []
    claim_dependencies: dict[str, tuple[str, ...]] = {}
    for index, row in enumerate(claim_rows):
        if not isinstance(row, Mapping):
            errors.append(f"claim_index[{index}] must be an object")
            continue
        missing = [
            field
            for field in ("id", "kind", "document_path", "status")
            if not str(row.get(field, "") or "").strip()
        ]
        if missing:
            errors.append(
                f"claim_index[{index}] missing required fields: "
                + ", ".join(missing)
            )
        claim_id = str(row.get("id", "") or "").strip()
        if claim_id:
            claim_ids.append(claim_id)
        raw_dependencies = row.get("depends_on")
        if not isinstance(raw_dependencies, list):
            errors.append(f"claim_index[{index}].depends_on must be a list")
            dependencies: list[str] = []
        else:
            dependencies = [
                str(value).strip()
                for value in raw_dependencies
                if str(value).strip()
            ]
            if len(dependencies) != len(raw_dependencies):
                errors.append(
                    f"claim_index[{index}].depends_on entries must be non-empty text"
                )
            if len(dependencies) != len(set(dependencies)):
                errors.append(
                    f"claim_index[{index}].depends_on entries must be unique"
                )
        if claim_id:
            claim_dependencies[claim_id] = tuple(dependencies)
        path = str(row.get("document_path", "") or "").strip()
        if path and path not in document_paths:
            errors.append(f"claim_index[{index}] references an unknown document")
        kind = str(row.get("kind", "") or "")
        if kind not in THEORY_FILE_CLAIM_KINDS:
            errors.append(
                f"claim_index[{index}].kind must be one of "
                f"{', '.join(THEORY_FILE_CLAIM_KINDS)}; received {kind!r}"
            )
        status = str(row.get("status", "") or "")
        if status not in THEORY_FILE_CLAIM_STATUSES:
            errors.append(
                f"claim_index[{index}].status must be one of "
                f"{', '.join(THEORY_FILE_CLAIM_STATUSES)}; received {status!r}"
            )
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("claim_index ids must be unique")
    claim_id_set = set(claim_ids)
    for claim_id, dependencies in claim_dependencies.items():
        if claim_id in dependencies:
            errors.append(f"claim_index[{claim_id!r}] cannot depend on itself")
        unknown_dependencies = sorted(set(dependencies) - claim_id_set)
        if unknown_dependencies:
            errors.append(
                f"claim_index[{claim_id!r}] has unknown dependencies: "
                + ", ".join(unknown_dependencies)
            )
    dependency_cycle = _claim_dependency_cycle(
        {
            claim_id: tuple(
                dependency
                for dependency in dependencies
                if dependency in claim_id_set
            )
            for claim_id, dependencies in claim_dependencies.items()
        }
    )
    if dependency_cycle:
        errors.append(
            "claim_index dependency graph must be acyclic: "
            + " -> ".join(dependency_cycle)
        )

    # Historical v2 document packets may carry this non-authoritative index.
    check_rows = derivation.get("sanity_check_index", [])
    if not isinstance(check_rows, list):
        errors.append("theory_derivation_packet.sanity_check_index must be a list")
        check_rows = []
    check_ids: list[str] = []
    for index, row in enumerate(check_rows):
        if not isinstance(row, Mapping):
            errors.append(f"sanity_check_index[{index}] must be an object")
            continue
        missing = [
            field
            for field in ("id", "claim_ref", "document_path", "status")
            if not str(row.get(field, "") or "").strip()
        ]
        if missing:
            errors.append(
                f"sanity_check_index[{index}] missing required fields: "
                + ", ".join(missing)
            )
        check_id = str(row.get("id", "") or "").strip()
        if check_id:
            check_ids.append(check_id)
        claim_ref = str(row.get("claim_ref", "") or "").strip()
        if claim_ref and claim_ref not in set(claim_ids):
            errors.append(f"sanity_check_index[{index}] has unknown claim_ref")
        path = str(row.get("document_path", "") or "").strip()
        if path and path not in document_paths:
            errors.append(
                f"sanity_check_index[{index}] references an unknown document"
            )
        status = str(row.get("status", "") or "")
        if status not in THEORY_FILE_SANITY_STATUSES:
            errors.append(
                f"sanity_check_index[{index}].status must be one of "
                f"{', '.join(THEORY_FILE_SANITY_STATUSES)}; received {status!r}"
            )
    if len(check_ids) != len(set(check_ids)):
        errors.append("sanity_check_index ids must be unique")
    indexed_ids = set(claim_ids)
    for field in ("estimator_specs", "theorem_cards", "lemma_cards"):
        for index, row in enumerate(packet.get(field, []) or []):
            if not isinstance(row, Mapping):
                continue
            row_id = str(row.get("id", "") or "").strip()
            if row_id and row_id not in indexed_ids:
                errors.append(f"{field}[{index}].id is absent from claim_index")
    return errors


def _file_theory_handoff_reference_errors(
    packet: Mapping[str, Any],
    *,
    handoff_requirements: Mapping[str, bool],
) -> list[str]:
    """Validate navigation references without interpreting document mathematics."""

    derivation = packet.get("theory_derivation_packet", {})
    claim_rows = (
        derivation.get("claim_index", [])
        if isinstance(derivation, Mapping)
        else []
    )
    claims_by_id = {
        str(row.get("id", "") or "").strip(): dict(row)
        for row in claim_rows
        if isinstance(row, Mapping) and str(row.get("id", "") or "").strip()
    }
    errors: list[str] = []

    def reject_extra(value: Any, label: str, allowed: set[str]) -> None:
        if not isinstance(value, Mapping):
            return
        unexpected = sorted(set(value) - allowed)
        if unexpected:
            errors.append(
                f"{label} contains non-reference fields: {', '.join(unexpected)}; "
                "put substantive theory in Markdown/LaTeX documents"
            )

    problem_card = packet.get("problem_card", {})
    simulation_spec = packet.get("simulation_ademp_spec", {})
    for label, value, allowed in (
        (
            "theory_derivation_packet",
            derivation,
            {"claim_index", "formalization_handoff", "sanity_check_index"},
        ),
        ("problem_card", problem_card, {"claim_ids"}),
        ("simulation_ademp_spec", simulation_spec, {"claim_ids"}),
        (
            "theory_derivation_packet.formalization_handoff",
            (
                derivation.get("formalization_handoff", {})
                if isinstance(derivation, Mapping)
                else {}
            ),
            {"source_theorem_target"},
        ),
    ):
        reject_extra(value, label, allowed)

    indexed_row_shapes = (
        (
            "theory_derivation_packet.claim_index",
            claim_rows,
            {"id", "kind", "document_path", "anchor", "depends_on", "status"},
        ),
        (
            "theorem_cards",
            packet.get("theorem_cards", []),
            {"id", "document_path"},
        ),
        (
            "estimator_specs",
            packet.get("estimator_specs", []),
            {
                "id",
                "name",
                "estimator_interface_contract",
                "estimator_interface_contract_id",
            },
        ),
        (
            "formalization_requests",
            packet.get("formalization_requests", []),
            {"id", "target_theorem_card"},
        ),
    )
    for label, rows, allowed in indexed_row_shapes:
        for index, row in enumerate(rows or []):
            reject_extra(row, f"{label}[{index}]", allowed)

    for field, value, required in (
        ("problem_card", problem_card, handoff_requirements.get("problem_card", True)),
        (
            "simulation_ademp_spec",
            simulation_spec,
            handoff_requirements.get("simulation_ademp_spec", False),
        ),
    ):
        claim_ids = value.get("claim_ids", []) if isinstance(value, Mapping) else []
        label = f"{field}.claim_ids"
        if not isinstance(claim_ids, list):
            errors.append(f"{label} must be a list")
            continue
        normalized = [str(item or "").strip() for item in claim_ids]
        if required and not normalized:
            errors.append(f"{label} must be a non-empty list")
        if any(not item for item in normalized):
            errors.append(f"{label} entries must be non-empty claim_index ids")
        if len(normalized) != len(set(normalized)):
            errors.append(f"{label} entries must be unique")
        unknown = sorted({item for item in normalized if item} - set(claims_by_id))
        if unknown:
            errors.append(f"{label} has unknown claim_index ids: " + ", ".join(unknown))

    for index, row in enumerate(packet.get("theorem_cards", []) or []):
        if not isinstance(row, Mapping):
            continue
        theorem_id = str(row.get("id", "") or "").strip()
        claim = claims_by_id.get(theorem_id, {})
        if theorem_id and claim and claim.get("kind") != "theorem":
            errors.append(
                f"theorem_cards[{index}].id must reference a theorem claim_index row"
            )
        document_path = str(row.get("document_path", "") or "").strip()
        if not document_path:
            errors.append(f"theorem_cards[{index}].document_path must be non-empty")
        elif claim and document_path != str(claim.get("document_path", "") or ""):
            errors.append(
                f"theorem_cards[{index}].document_path must match its claim_index row"
            )
    return errors


def _claim_dependency_cycle(
    dependencies: Mapping[str, Sequence[str]],
) -> tuple[str, ...]:
    """Return one deterministic cycle from a model-authored claim graph."""

    visiting: set[str] = set()
    visited: set[str] = set()
    path: list[str] = []

    def visit(claim_id: str) -> tuple[str, ...]:
        if claim_id in visited:
            return ()
        if claim_id in visiting:
            cycle_start = path.index(claim_id)
            return tuple([*path[cycle_start:], claim_id])
        visiting.add(claim_id)
        path.append(claim_id)
        for dependency in dependencies.get(claim_id, ()):
            cycle = visit(str(dependency))
            if cycle:
                return cycle
        path.pop()
        visiting.remove(claim_id)
        visited.add(claim_id)
        return ()

    for claim_id in sorted(dependencies):
        cycle = visit(claim_id)
        if cycle:
            return cycle
    return ()


def _legacy_structured_derivation_errors(
    derivation: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    required_fields = {
        "derivation_steps": ("id", "claim", "equation_or_argument"),
        "equation_chain": ("lhs", "rhs", "justification"),
        "assumption_ledger": ("assumption", "used_in"),
        "sanity_checks": ("id", "claim_ref", "check_type", "recomputation", "result"),
    }
    for field, fields in required_fields.items():
        rows = derivation.get(field, [])
        if not isinstance(rows, list) or not rows:
            errors.append(f"theory_derivation_packet.{field} must be a non-empty list")
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"theory_derivation_packet.{field}[{index}] must be an object")
                continue
            missing = [name for name in fields if not row.get(name)]
            if missing:
                errors.append(f"theory_derivation_packet.{field}[{index}] missing required fields: " + ", ".join(missing))
    return errors


def _validate_theory_packet(
    packet: Mapping[str, Any],
    *,
    require_estimator_interfaces: bool,
) -> list[str]:
    document_authority = (
        packet.get("theory_content_authority")
        == THEORY_WORKSPACE_CONTENT_AUTHORITY
    )
    formalization_authoring_required = (
        packet.get("runtime_formalization_authoring_required") is not False
    )
    raw_handoff_requirements = packet.get(
        "runtime_theory_handoff_requirements", {}
    )
    handoff_requirements = (
        {
            str(field): bool(required)
            for field, required in raw_handoff_requirements.items()
        }
        if isinstance(raw_handoff_requirements, Mapping)
        and raw_handoff_requirements
        else (
            {
                "problem_card": True,
                "theory_derivation_packet": True,
                "estimator_specs": False,
                "theorem_cards": formalization_authoring_required,
                "simulation_ademp_spec": False,
                "formalization_requests": formalization_authoring_required,
            }
            if document_authority
            else {
                "problem_card": True,
                "theory_derivation_packet": True,
                "estimator_specs": True,
                "theorem_cards": True,
                "proof_plan": True,
                "simulation_ademp_spec": True,
                "formalization_requests": formalization_authoring_required,
            }
        )
    )
    errors: list[str] = _output_contract_shape_errors(
        packet,
        (
            THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
            if document_authority
            else THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
        ),
        path="",
    )
    errors.extend(
        theory_workspace_manifest_errors(
            packet,
            required=document_authority,
        )
    )
    if document_authority and packet.get("structured_handoff_role") != (
        THEORY_WORKSPACE_HANDOFF_ROLE
    ):
        errors.append("theory workspace structured handoff role mismatch")
    required_nonempty_fields = [
        field for field, required in handoff_requirements.items() if required
    ]
    for field in required_nonempty_fields:
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    problem_card = packet.get("problem_card", {})
    if not document_authority:
        if isinstance(problem_card, Mapping):
            for field in (
                "observed_data",
                "dgp",
                "estimand",
                "asymptotic_regime",
                "desired_theorem_type",
            ):
                if not str(problem_card.get(field, "") or "").strip():
                    errors.append(f"problem_card.{field} must be non-empty")
            assumptions = problem_card.get("assumptions", [])
            if not isinstance(assumptions, list) or not assumptions:
                errors.append("problem_card.assumptions must be a non-empty list")
        elif problem_card not in (None, "", [], {}):
            errors.append("problem_card must be an object")
    derivation = packet.get("theory_derivation_packet", {})
    if not isinstance(derivation, Mapping):
        errors.append("theory_derivation_packet must be an object")
    else:
        if document_authority:
            errors.extend(
                _file_theory_index_errors(
                    derivation,
                    packet,
                )
            )
        else:
            errors.extend(_legacy_structured_derivation_errors(derivation))
        formalization_handoff = derivation.get("formalization_handoff", {})
        if formalization_authoring_required and (
            not isinstance(formalization_handoff, Mapping)
            or not formalization_handoff
        ):
            errors.append(
                "theory_derivation_packet.formalization_handoff must be non-empty"
            )
        elif not document_authority and (
            isinstance(formalization_handoff, Mapping)
            and formalization_handoff
            and not formalization_handoff.get("semantic_alignment_constraints")
        ):
            errors.append(
                "theory_derivation_packet.formalization_handoff.semantic_alignment_constraints must be non-empty"
            )
    for list_field in ("estimator_specs", "theorem_cards"):
        value = packet.get(list_field)
        if not isinstance(value, list):
            errors.append(f"{list_field} must be a list")
        elif handoff_requirements.get(list_field, True) and not value:
            errors.append(f"{list_field} must be a non-empty list")
    formalization_requests = packet.get("formalization_requests", [])
    if not isinstance(formalization_requests, list):
        errors.append("formalization_requests must be a list")
    elif (
        handoff_requirements.get("formalization_requests", False)
        and not formalization_requests
    ):
        errors.append("formalization_requests must be a non-empty list")
    if document_authority:
        errors.extend(
            _file_theory_handoff_reference_errors(
                packet,
                handoff_requirements=handoff_requirements,
            )
        )
    else:
        for list_field in ("lemma_cards", "critic_findings", "next_actions"):
            if not isinstance(packet.get(list_field), list):
                errors.append(f"{list_field} must be a list")
    allowed_derivation_refs = theory_semantic_reference_ids(packet)
    estimator_ids: list[str] = []
    for idx, row in enumerate(packet.get("estimator_specs", []) or []):
        if not isinstance(row, Mapping):
            errors.append("estimator_specs entries must be objects")
            continue
        required_estimator_fields = (
            ("id", "name")
            if document_authority
            else ("id", "name", "formula", "algorithm_sketch")
        )
        for field in required_estimator_fields:
            if not str(row.get(field, "") or "").strip():
                errors.append(f"estimator_specs[{idx}].{field} must be non-empty")
        estimator_id = str(row.get("id", "") or "").strip()
        if estimator_id:
            estimator_ids.append(estimator_id)
        if not document_authority:
            required_assumptions = row.get("required_assumptions", [])
            if not isinstance(required_assumptions, list) or not required_assumptions:
                errors.append(
                    f"estimator_specs[{idx}].required_assumptions must be non-empty"
                )
        if require_estimator_interfaces:
            contract = row.get("estimator_interface_contract")
            errors.extend(
                estimator_interface_contract_errors(
                    contract,
                    label=f"estimator_specs[{idx}]",
                    required=True,
                    allowed_derivation_refs=allowed_derivation_refs,
                )
            )
            if isinstance(contract, Mapping):
                expected_contract_id = estimator_interface_contract_id(contract)
                if str(row.get("estimator_interface_contract_id", "") or "") != (
                    expected_contract_id
                ):
                    errors.append(
                        f"estimator_specs[{idx}].estimator_interface_contract_id "
                        "does not match the immutable contract"
                    )
    if len(estimator_ids) != len(set(estimator_ids)):
        errors.append("estimator_specs ids must be unique")
    simulation_ademp_spec = packet.get("simulation_ademp_spec", {})
    if not document_authority:
        if isinstance(simulation_ademp_spec, Mapping) and (
            simulation_ademp_spec
            or handoff_requirements.get("simulation_ademp_spec", True)
        ):
            if not str(simulation_ademp_spec.get("aim", "") or "").strip():
                errors.append("simulation_ademp_spec.aim must be non-empty")
            for field in (
                "dgps",
                "methods",
                "performance_measures",
                "expected_theoretical_behavior",
            ):
                value = simulation_ademp_spec.get(field, [])
                if not isinstance(value, list) or not value:
                    errors.append(
                        f"simulation_ademp_spec.{field} must be a non-empty list"
                    )
        elif simulation_ademp_spec not in (None, "", [], {}):
            errors.append("simulation_ademp_spec must be an object")
    theorem_card_ids: list[str] = []
    for idx, row in enumerate(packet.get("theorem_cards", []) or []):
        if not isinstance(row, Mapping):
            errors.append("theorem_cards entries must be objects")
            continue
        theorem_card_id = str(row.get("id", "") or "").strip()
        if not theorem_card_id:
            errors.append(f"theorem_cards[{idx}].id must be non-empty")
        else:
            theorem_card_ids.append(theorem_card_id)
        if not document_authority:
            if not str(row.get("informal_statement", "")).strip():
                errors.append("theorem card missing informal_statement")
            if not str(row.get("proof_strategy", "")).strip():
                errors.append("theorem card missing proof_strategy")
    if len(theorem_card_ids) != len(set(theorem_card_ids)):
        errors.append("theorem_cards ids must be unique")

    theorem_card_id_set = set(theorem_card_ids)
    formalization_handoff = (
        derivation.get("formalization_handoff", {})
        if isinstance(derivation, Mapping)
        else {}
    )
    source_theorem_target = (
        str(formalization_handoff.get("source_theorem_target", "") or "").strip()
        if isinstance(formalization_handoff, Mapping)
        else ""
    )
    if formalization_authoring_required and not source_theorem_target:
        errors.append(
            "theory_derivation_packet.formalization_handoff."
            "source_theorem_target must be non-empty"
        )
    elif source_theorem_target and source_theorem_target not in theorem_card_id_set:
        errors.append(
            "theory_derivation_packet.formalization_handoff."
            "source_theorem_target must exactly match a theorem_cards id; "
            f"got {source_theorem_target!r}, available={sorted(theorem_card_id_set)}"
        )

    formalization_request_ids: list[str] = []
    formalization_request_targets: list[str] = []
    for idx, row in enumerate(packet.get("formalization_requests", []) or []):
        if not isinstance(row, Mapping):
            errors.append("formalization_requests entries must be objects")
            continue
        request_id = str(row.get("id", "") or "").strip()
        if not request_id:
            errors.append(f"formalization_requests[{idx}].id must be non-empty")
        else:
            formalization_request_ids.append(request_id)
        request_target = str(row.get("target_theorem_card", "") or "").strip()
        if not request_target:
            errors.append(
                f"formalization_requests[{idx}].target_theorem_card must be non-empty"
            )
        else:
            formalization_request_targets.append(request_target)
            if request_target not in theorem_card_id_set:
                errors.append(
                    f"formalization_requests[{idx}].target_theorem_card must "
                    "exactly match a theorem_cards id; "
                    f"got {request_target!r}, "
                    f"available={sorted(theorem_card_id_set)}"
                )
    if len(formalization_request_ids) != len(set(formalization_request_ids)):
        errors.append("formalization_requests ids must be unique")
    if (
        source_theorem_target
        and source_theorem_target in theorem_card_id_set
        and source_theorem_target not in formalization_request_targets
    ):
        errors.append(
            "theory_derivation_packet.formalization_handoff."
            "source_theorem_target must be targeted by a formalization request"
        )
    if packet.get("proof_evidence_status") != THEORY_DERIVATION_NOT_PROOF_EVIDENCE:
        errors.append("proof_evidence_status must preserve LLM-not-proof boundary")
    if packet.get("kernel_verified") is not False:
        errors.append("LLM theory packet cannot set kernel_verified=true")
    errors.extend(_forbidden_proof_claims(packet))
    return sorted(set(errors))


def _normalize_theory_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    theory_prompt_mode: str = THEORY_PROMPT_MODE_COMPACT,
    formalization_authoring_required: bool = True,
) -> dict[str, Any]:
    body = dict(payload)
    serious_theory_mode = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
    body["theory_prompt_mode"] = theory_prompt_mode
    body["serious_theory_mode"] = serious_theory_mode
    body["runtime_formalization_authoring_required"] = bool(
        formalization_authoring_required
    )
    body["runtime_theory_handoff_requirements"] = theory_handoff_requirements(
        question,
        formalization_authoring_required=formalization_authoring_required,
    )
    derivation_packet = body.get("theory_derivation_packet")
    document_index_handoff = bool(
        isinstance(derivation_packet, Mapping)
        and "claim_index" in derivation_packet
    )
    if isinstance(derivation_packet, Mapping):
        body["theory_derivation_packet"] = (
            deepcopy(dict(derivation_packet))
            if document_index_handoff
            else _canonicalize_theory_derivation_packet(
                derivation_packet,
                formalization_requests=body.get("formalization_requests", []),
            )
        )
    normalize_theory_estimator_interface_contracts(body)
    body["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    body["proof_evidence_boundary"] = KERNEL_PROOF_BOUNDARY
    body["kernel_verified"] = False
    body["verified_theorem_count"] = 0
    derivation = (
        body.get("theory_derivation_packet", {})
        if isinstance(body.get("theory_derivation_packet", {}), Mapping)
        else {}
    )
    derivation_counts = (
        {
            "n_claim_index_rows": _safe_len(derivation.get("claim_index", [])),
        }
        if document_index_handoff
        else {
            "n_derivation_steps": _safe_len(
                derivation.get("derivation_steps", [])
            ),
            "n_equation_chain_steps": _safe_len(
                derivation.get("equation_chain", [])
            ),
            "n_assumption_ledger_rows": _safe_len(
                derivation.get("assumption_ledger", [])
            ),
            "n_sanity_checks": _safe_len(derivation.get("sanity_checks", [])),
        }
    )
    body["theory_derivation_contract"] = {
        "row_count_policy": "model_selected_nonempty_required_structures",
        "quality_authority": "independent_theory_preflight_and_critic",
        "theory_prompt_mode": theory_prompt_mode,
        **derivation_counts,
        "has_formalization_handoff": bool(
            body.get("formalization_requests")
            if document_index_handoff
            else (
                isinstance(derivation.get("formalization_handoff", {}), Mapping)
                and derivation.get("formalization_handoff")
            )
        ),
        "formalization_authoring_required": bool(
            formalization_authoring_required
        ),
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "boundary": (
            "The mathematical documents are authoritative and this structured "
            "claim index is only a cross-agent handoff, not proof evidence."
            if document_index_handoff
            else "Theory derivation traces are structured LLM reasoning proposals "
            "for simulation/formalization handoff, not proof evidence."
        ),
    }
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
        "schema_version": ARCHITECT_SCHEMA_VERSION,
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": f"theory_derivation:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMTheoryDeveloperAgent",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "question": research_question_payload(
            question,
            include_task_intent=True,
            include_estimator_execution_contract=False,
        ),
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _theory_developer_revision_binding_from_context(
    architect_context: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
) -> dict[str, Any]:
    """Require the runtime-authored parent/feedback revision contract."""

    raw_binding = architect_context.get(
        THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY, {}
    )
    if not isinstance(raw_binding, Mapping) or not raw_binding:
        raise PacketValidationError(
            validation_label="TheoryDeveloper targeted revision inputs",
            attempts=0,
            errors=[
                "revision feedback requires a runtime parent-bound "
                "TheoryDeveloper revision binding"
            ],
            history=[],
        )
    binding = deepcopy(dict(raw_binding))

    errors = theory_developer_revision_binding_errors(
        binding,
        question_id=question.id,
    )
    if errors:
        raise PacketValidationError(
            validation_label="TheoryDeveloper targeted revision inputs",
            attempts=0,
            errors=errors,
            history=[],
        )
    return binding


def build_theory_developer_revision_inputs(
    architect_context: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
) -> dict[str, Any]:
    """Bind an upstream-theory revision to one immutable accepted parent packet."""

    binding = _theory_developer_revision_binding_from_context(
        architect_context,
        question=question,
    )
    feedback = binding.get("source_feedback", {})
    feedback = dict(feedback) if isinstance(feedback, Mapping) else {}
    material = architect_context.get(
        THEORY_DEVELOPER_RESOLVED_PARENT_MATERIAL_CONTEXT_KEY,
        {},
    )
    material = dict(material) if isinstance(material, Mapping) else {}
    errors: list[str] = []

    material_packet_id = str(
        material.get("source_theory_packet_id", "") or ""
    ).strip()
    material_packet_hash = str(
        material.get("source_theory_packet_hash", "") or ""
    ).strip()
    if material_packet_id != str(
        binding.get("source_theory_packet_id", "") or ""
    ).strip():
        errors.append("resolved parent material packet id does not match binding")
    if material_packet_hash != str(
        binding.get("source_theory_packet_hash", "") or ""
    ).strip():
        errors.append("resolved parent material packet hash does not match binding")

    semantic_material = material.get("theory_semantic_material", {})
    if not isinstance(semantic_material, Mapping) or not semantic_material:
        errors.append("prior theory material must contain current semantic material")
        semantic_material = {}
    semantic_packet_id = str(semantic_material.get("packet_id", "") or "").strip()
    if semantic_packet_id and semantic_packet_id != material_packet_id:
        errors.append("prior semantic material packet_id does not match its lineage")
    semantic_question = semantic_material.get("question", {})
    semantic_question_id = (
        str(semantic_question.get("id", "") or "").strip()
        if isinstance(semantic_question, Mapping)
        else ""
    )
    if semantic_question_id and semantic_question_id != question.id:
        errors.append("prior semantic material belongs to a different question")

    missing_core_fields = [
        field
        for field in THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
        if field not in semantic_material
    ]
    if missing_core_fields:
        errors.append(
            "prior semantic material is missing core fields: "
            + ", ".join(missing_core_fields)
        )
    base_core_payload = {
        field: deepcopy(semantic_material[field])
        for field in THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
        if field in semantic_material
    }
    for field in (
        "theory_workspace_manifest",
        "theory_content_authority",
        "structured_handoff_role",
    ):
        if field in semantic_material:
            base_core_payload[field] = deepcopy(semantic_material[field])
    raw_specs = base_core_payload.get("estimator_specs", [])
    if not isinstance(raw_specs, list):
        errors.append("prior estimator_specs must be a list")
    else:
        for index, raw_spec in enumerate(raw_specs):
            if not isinstance(raw_spec, Mapping):
                errors.append(f"prior estimator_specs[{index}] must be an object")

    derivation = base_core_payload.get("theory_derivation_packet", {})
    if isinstance(derivation, Mapping):
        base_core_payload["theory_derivation_packet"] = deepcopy(
            dict(derivation)
        )
    else:
        errors.append("prior theory_derivation_packet must be an object")

    if errors:
        raise PacketValidationError(
            validation_label="TheoryDeveloper targeted revision inputs",
            attempts=0,
            errors=errors,
            history=[],
        )
    environment_feedback = architect_context.get("environment_feedback", {})
    transport_feedback = (
        deepcopy(dict(environment_feedback))
        if isinstance(environment_feedback, Mapping)
        and environment_feedback.get("artifact_kind")
        == "RuntimeTheoryDeveloperValidationFeedback"
        else {}
    )
    return {
        "revision_binding_id": str(binding.get("binding_id", "") or ""),
        "revision_source": str(binding.get("revision_source", "") or ""),
        "source_theory_packet_id": material_packet_id,
        "source_theory_packet_hash": material_packet_hash,
        "feedback_id": str(binding.get("feedback_id", "") or "").strip(),
        "source_feedback_fingerprint": str(
            binding.get("source_feedback_fingerprint", "") or ""
        ),
        "source_review_packet_id": str(
            binding.get("source_review_packet_id", "") or ""
        ),
        "source_review_execution_id": str(
            binding.get("source_review_execution_id", "") or ""
        ),
        "execution_results_observed": bool(
            binding.get("execution_results_observed") is True
        ),
        "upstream_theory_revision_count": binding.get(
            "upstream_theory_revision_count", 0
        ),
        "continuation_budget_authority": binding.get(
            "continuation_budget_authority", ""
        ),
        "feedback": deepcopy(dict(feedback)),
        "transport_feedback": transport_feedback,
        "parent_client_tool_session_ref": deepcopy(
            dict(material.get("parent_client_tool_session_ref", {}))
            if isinstance(
                material.get("parent_client_tool_session_ref", {}), Mapping
            )
            else {}
        ),
        "parent_scratch_execution_refs": deepcopy(list(
            material.get("parent_scratch_execution_refs", []))
            if isinstance(material.get("parent_scratch_execution_refs", []), list)
            else []),
        "base_core_payload": base_core_payload,
        "base_core_payload_fingerprint": stable_hash(base_core_payload),
    }


def _theory_workspace_read_only_observations(
    revision_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    feedback = revision_inputs.get("feedback", {})
    reviewer_observations = (
        deepcopy(dict(feedback))
        if isinstance(feedback, Mapping)
        else {}
    )
    report_ref = reviewer_observations.get("review_document_ref", {})
    report_content = ""
    report_document_path = ""
    if isinstance(report_ref, Mapping) and report_ref:
        report_content, errors = read_hash_bound_utf8_file(report_ref)
        if report_ref.get("persisted") is not True or errors:
            raise ValueError("stale theory review document reference: " + ",".join(errors))
        report_sha256 = str(report_ref.get("sha256", "") or "")
        report_document_path = f"feedback/current_referee_report-{report_sha256[:20]}.md"
        model_ref = deepcopy(dict(report_ref))
        model_ref.pop("path", None)
        model_ref["workspace_document_path"] = report_document_path
        model_ref["line_count"] = len(report_content.splitlines())
        reviewer_observations["review_document_ref"] = model_ref
        findings = reviewer_observations.pop("findings", [])
        index_keys = ("finding_id", "severity", "category", "evidence_refs")
        reviewer_observations["finding_index"] = [
            {key: deepcopy(row[key]) for key in index_keys if key in row}
            for row in findings
            if isinstance(row, Mapping)
        ]
    embedded_preflight = reviewer_observations.pop(
        "theory_execution_preflight_packet",
        {},
    )
    if isinstance(embedded_preflight, Mapping) and embedded_preflight:
        reviewer_observations["theory_execution_preflight_packet_id"] = str(
            embedded_preflight.get("packet_id", "") or ""
        )
        reviewer_observations["theory_execution_preflight_packet_hash"] = (
            stable_hash(dict(embedded_preflight))
        )
    observations: dict[str, Any] = {
        "reviewer_observations": reviewer_observations,
    }
    if report_content:
        observations["read_only_documents"] = {
            report_document_path: report_content,
        }
    transport_feedback = revision_inputs.get("transport_feedback", {})
    if isinstance(transport_feedback, Mapping) and transport_feedback:
        observations["transport_observations"] = deepcopy(
            dict(transport_feedback)
        )
    return observations


def _empty_theory_core_workspace(
    *,
    file_authority: bool = False,
) -> dict[str, Any]:
    """Return shape-only handoff artifacts without seeded research content."""

    workspace: dict[str, Any] = {}
    contract_source = (
        THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
        if file_authority
        else THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
    )
    for name, contract in contract_source.items():
        if isinstance(contract, Mapping):
            workspace[name] = {}
        elif isinstance(contract, list):
            workspace[name] = []
        else:
            raise TypeError(
                f"unsupported theory workspace contract shape for {name}"
            )
    return workspace


def _theory_workspace_writable_handoff_names(
    *,
    question: OpenResearchQuestion,
    formalization_authoring_required: bool,
    artifacts: Mapping[str, Any],
) -> tuple[str, ...]:
    selected_fields = _selected_theory_handoff_fields(
        question=question,
        formalization_authoring_required=formalization_authoring_required,
        available_fields=tuple(THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT),
    )
    return tuple(
        field for field in selected_fields if field in artifacts
    )


def _initial_theory_workspace_read_only_artifacts(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    theory_prompt_mode: str,
    max_tool_calls: int,
    formalization_authoring_required: bool,
    allow_source_replication_checkpoint: bool = False,
) -> dict[str, Any]:
    serious = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
    required_output_contract, handoff_requirements = (
        _theory_output_contract_for_question(
            THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT,
            question=question,
            formalization_authoring_required=formalization_authoring_required,
        )
    )
    output_contract: dict[str, Any]
    if allow_source_replication_checkpoint:
        output_contract = {
            "source_replication_checkpoint": {
                "required": [
                    "one immutable source execution",
                    "one model-authored Markdown report",
                    "explicit unresolved gaps",
                ],
                "evidence_role": "source replication only",
                "not_evidence_for": ["theory", "simulation", "formal proof"],
            },
        }
    else:
        output_contract = required_output_contract
    context = _compact_architect_context_for_prompt(architect_context)
    read_only_documents: dict[str, str] = {}
    for key in ("environment_feedback", "theory_developer_source_environment_feedback"):
        feedback = architect_context.get(key)
        if isinstance(feedback, Mapping) and feedback:
            path = f"feedback/{key}-{stable_hash(dict(feedback))[:20]}.md"
            observation, documents, _ = externalize_client_tool_text_documents(
                dict(feedback), min_characters=1024, path_prefix=f"feedback/{key}",
            )
            read_only_documents.update(documents)
            read_only_documents[path] = json.dumps(
                observation, indent=2, sort_keys=True, ensure_ascii=False, default=str,
            )
            context[key] = {"workspace_document_path": path}
    return {
        "read_only_documents": read_only_documents,
        "initial_authoring_context": {
            "research_question": research_question_payload(
                question,
                include_task_intent=True,
            ),
            "architect_context": context,
            "required_output_contract": output_contract,
            "authoring_policy": {
                "theory_prompt_mode": theory_prompt_mode,
                "serious_theory_mode": serious,
                "required_nonempty_structures": [
                    "model-authored Markdown/LaTeX mathematical documents",
                    "claim_index",
                ],
                "maximum_tool_calls": max(1, int(max_tool_calls)),
                "read_write_quota_policy": "one_shared_tool_call_budget",
                "row_count_policy": "model_selected",
                "row_counts_are_not_quality_metrics": True,
                "formalization_authoring_required": bool(
                    formalization_authoring_required
                ),
                "structured_handoff_requirements": handoff_requirements,
                "source_replication_checkpoint_allowed": bool(
                    allow_source_replication_checkpoint
                ),
                "substantive_author": "TheoryDeveloper model",
                "mathematical_content_authority": (
                    THEORY_WORKSPACE_CONTENT_AUTHORITY
                ),
                "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
                "runtime_role": (
                    "apply exact model-authored edits, validate structure and "
                    "lineage, and return raw observations without choosing "
                    "research content"
                ),
                "proof_boundary": KERNEL_PROOF_BOUNDARY,
            },
        }
    }


def _initial_theory_workspace_prompt(
    *,
    question: OpenResearchQuestion,
    theory_prompt_mode: str,
    max_tool_calls: int,
    formalization_authoring_required: bool,
    allow_source_replication_checkpoint: bool = False,
    continuing_from_progress: bool = False,
) -> str:
    if allow_source_replication_checkpoint:
        return (
            "Complete the source-replication prerequisite for question "
            f"{question.id!r} in the persistent research workspace. First read the "
            "single initial_authoring_context artifact and inspect the supplied sources. "
            "Run the immutable published source exactly once, inspect its raw stdout and "
            "stderr, and use your own statistical judgment to write a durable Markdown "
            "report covering source and environment identity, reproduced outputs, "
            "comparison, interpretation, and caveats. Record unresolved gaps honestly, "
            "then commit a source-replication checkpoint. The outer graph will follow "
            "the frozen remaining plan; do not fabricate theory, estimator, simulation, "
            "formalization, or novelty fields. Runtime applies your exact "
            "document bytes and validates identity and lineage; it does not interpret "
            "the scientific result or promote it to proof evidence."
        )
    handoff_requirements = theory_handoff_requirements(
        question,
        formalization_authoring_required=formalization_authoring_required,
    )
    required_handoffs = ", ".join(
        field for field, required in handoff_requirements.items() if required
    )
    optional_handoffs = ", ".join(
        field for field, required in handoff_requirements.items() if not required
    )
    opening = (
        "Continue the existing document-backed TheoryDeveloper research workspace "
        f"for question {question.id!r} in mode {theory_prompt_mode!r}. First read "
        "prior_theory_progress_checkpoint, inspect its next step, and read the exact "
        "current documents or handoff artifacts needed to continue. The original "
        "initial_authoring_context remains available. Tool observations and "
        "execution counts are cumulative across context windows; inspect the "
        "checkpoint state rather than repeating a prior scratch or immutable "
        "source execution as if this were a fresh workspace. "
        if continuing_from_progress
        else (
            "Author the initial TheoryDeveloper research workspace for the supplied "
            f"question {question.id!r} in mode {theory_prompt_mode!r}. First read the "
            "single initial_authoring_context artifact. "
        )
    )
    return (
        opening
        + "Use your own statistical judgment in durable Markdown/LaTeX. Documents are "
        "the authority for mathematics; JSON is only a compact claim index, ABI, and "
        "cross-agent handoff. Put every formula, assumption, theorem statement, proof "
        "argument, simulation design, and semantic constraint in those documents; the "
        "structured handoff may only point to claim IDs or define an executable estimator "
        "ABI. Keep the current endorsed argument coherent, remove or "
        "clearly reject false exploration, and make each requested conclusion's scope, "
        "assumptions, dependencies, implementation meaning, and uncertainty reviewable. "
        "A case split must exhaust the asserted domain; otherwise narrow the claim or "
        "report the unresolved gap. Give falsifiable claims stable IDs and record only "
        "direct dependencies. The Simulation owner controls executable confirmatory "
        "protocols and outcomes. Scratch calculations are exploratory observations only. "
        f"Use one shared budget of at most {max(1, int(max_tool_calls))} ordinary tool "
        "calls, with no separate read or write quota. Use write_theory_document for a "
        "complete text file, edit_theory_document for a hash-bound local edit, and "
        "write_theory_workspace only for compact structured handoffs. Preserve any "
        "frozen estimator ABI exactly; otherwise author required executable interfaces "
        "without runtime translation. The required compact handoffs are: "
        + required_handoffs
        + ". Handoffs not required by this task intent may remain empty: "
        + optional_handoffs
        + ". "
        + (
            "Formalization requests must name an existing theorem-card ID. "
            if formalization_authoring_required
            else "Formalization is not requested; do not invent Lean work. "
        )
        + "Runtime applies only your exact edits and structural checks. Do not claim "
        "confirmatory execution, Lean proof, or kernel verification. Before checkpoint, "
        "re-read the exact frozen question and current documents, recompute the requested "
        "dependency chain, then perform a whole-document contradiction sweep. Never "
        "commit from first-draft memory or its summary."
    )


def _theory_workspace_revision_prompt(
    *,
    question: OpenResearchQuestion,
    revision_inputs: Mapping[str, Any],
    formalization_authoring_required: bool,
    continuing_from_progress: bool = False,
) -> str:
    read_only_observations = _theory_workspace_read_only_observations(
        revision_inputs
    )
    reviewer_observations = read_only_observations["reviewer_observations"]
    finding_index = reviewer_observations.get(
        "finding_index",
        reviewer_observations.get("findings", []),
    )
    review_document_ref = reviewer_observations.get("review_document_ref", {})
    writable_artifacts = _theory_workspace_writable_handoff_names(
        question=question,
        formalization_authoring_required=formalization_authoring_required,
        artifacts=revision_inputs.get("base_core_payload", {}),
    )
    payload: dict[str, Any] = {
        "question": research_question_payload(
            question,
            include_task_intent=True,
        ),
        "revision_mode": "model_owned_document_workspace",
        "immutable_lineage": {
            "revision_binding_id": revision_inputs.get("revision_binding_id", ""),
            "revision_source": revision_inputs.get("revision_source", ""),
            "source_theory_packet_id": revision_inputs.get(
                "source_theory_packet_id", ""
            ),
            "source_theory_packet_hash": revision_inputs.get(
                "source_theory_packet_hash", ""
            ),
            "feedback_id": revision_inputs.get("feedback_id", ""),
            "source_feedback_fingerprint": revision_inputs.get(
                "source_feedback_fingerprint", ""
            ),
            "parent_core_payload_fingerprint": revision_inputs.get(
                "base_core_payload_fingerprint", ""
            ),
        },
        "reviewer_observations": {
            "workspace_artifact": "reviewer_observations",
            "content_hash": stable_hash(reviewer_observations),
            "feedback_id": revision_inputs.get("feedback_id", ""),
            "active_unresolved_finding_ids": list(
                reviewer_observations.get(
                    "active_unresolved_finding_ids",
                    [],
                )
                or []
            ),
            "n_findings": len(finding_index or []),
            **(
                {
                    "current_review_document": {
                        key: review_document_ref[key]
                        for key in (
                            "workspace_document_path",
                            "sha256",
                            "line_count",
                        )
                        if key in review_document_ref
                    }
                }
                if isinstance(review_document_ref, Mapping)
                and review_document_ref.get("workspace_document_path")
                else {}
            ),
        },
        "workspace_artifacts": list(writable_artifacts),
        "instructions": [
            (
                "Read prior_theory_progress_checkpoint and continue its exact lineage; "
                "tool observations and counts are cumulative."
                if continuing_from_progress
                else (
                    "First read the reviewer_observations index by itself. When it "
                    "names current_review_document, inspect that exact report with "
                    "read_theory_document, then read only relevant parent material."
                )
            ),
            "Treat the hash-bound referee document as an observation, not an answer key "
            "or editable theory file; use your own statistical judgment.",
            "Use write_theory_document or hash-bound edit_theory_document for text, and "
            "write_theory_workspace only for compact handoffs. Omitted material remains "
            "byte-identical.",
            "Propagate a chosen correction through every dependent authoritative claim "
            "and writable handoff. Remove or explicitly reject false derivations.",
            "A later correction does not deactivate earlier false text. Keep abandoned "
            "work in scratch or delimit it explicitly as SCRATCH or REJECTED.",
            "Keep failed checks and unresolved concerns honest. Scratch observations are "
            "exploratory, not confirmatory evidence or theorem validation.",
            "Runtime enforces identity, budget, lineage, and schema only; independent "
            "review owns acceptance, and kernel proof must not be claimed here.",
        ],
        "proof_boundary": KERNEL_PROOF_BOUNDARY,
    }
    if "estimator_specs" in writable_artifacts:
        payload["instructions"].append(
            "The estimator interface contract is part of estimator_specs in this "
            "same workspace. When estimator semantics or outputs change, inspect and "
            "revise that executable ABI yourself; when they do not change, preserve "
            "the parent value exactly. Runtime validates shape and claim references "
            "but never authors the interface. When the question supplies a frozen "
            "estimator execution contract, its estimator_id, request and response "
            "field names and order, and request bindings remain exact external ABI "
            "identity."
        )
    if "transport_observations" in read_only_observations:
        payload["transport_observations"] = {
            "workspace_artifact": "transport_observations",
            "content_hash": stable_hash(
                read_only_observations["transport_observations"]
            ),
        }
    return (
        "Revise the persistent TheoryDeveloper document workspace with client tools.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


def _attach_theory_workspace_revision_transport(
    packet: Mapping[str, Any],
    *,
    revision_inputs: Mapping[str, Any],
    provider_name: str,
    model: str,
    model_tier: str,
    workspace_id: str,
    changed_artifact_names: Sequence[str],
    changed_document_paths: Sequence[str],
) -> dict[str, Any]:
    result = deepcopy(dict(packet))
    revised_core = {
        field: deepcopy(result[field])
        for field in THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
        if field in result
    }
    feedback = revision_inputs.get("feedback", {})
    feedback = dict(feedback) if isinstance(feedback, Mapping) else {}
    result["theory_revision_transport"] = {
        "artifact_kind": "TheoryDeveloperWorkspaceRevisionTransport",
        "revision_mode": "model_owned_document_workspace",
        "workspace_id": workspace_id,
        "revision_binding_id": revision_inputs.get("revision_binding_id", ""),
        "revision_source": revision_inputs.get("revision_source", ""),
        "source_theory_packet_id": revision_inputs.get(
            "source_theory_packet_id", ""
        ),
        "source_theory_packet_hash": revision_inputs.get(
            "source_theory_packet_hash", ""
        ),
        "feedback_id": revision_inputs.get("feedback_id", ""),
        "source_feedback_fingerprint": revision_inputs.get(
            "source_feedback_fingerprint", ""
        ),
        "source_review_packet_id": revision_inputs.get(
            "source_review_packet_id", ""
        ),
        "source_review_execution_id": revision_inputs.get(
            "source_review_execution_id", ""
        ),
        "execution_results_observed": bool(
            revision_inputs.get("execution_results_observed") is True
        ),
        "upstream_theory_revision_count": revision_inputs.get(
            "upstream_theory_revision_count", 0
        ),
        "continuation_budget_authority": revision_inputs.get(
            "continuation_budget_authority", ""
        ),
        "active_unresolved_finding_ids": [
            str(value)
            for value in feedback.get("active_unresolved_finding_ids", []) or []
            if str(value).strip()
        ],
        "parent_core_payload_fingerprint": revision_inputs.get(
            "base_core_payload_fingerprint", ""
        ),
        "revised_core_payload_fingerprint": stable_hash(revised_core),
        "changed_artifact_names": sorted(
            {str(name) for name in changed_artifact_names if str(name)}
        ),
        "changed_document_paths": sorted(
            {str(path) for path in changed_document_paths if str(path)}
        ),
        "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
        "model_owned_artifact_edits": True,
        "model_owned_document_edits": bool(changed_document_paths),
        "theory_content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
        "runtime_edited_theory": False,
        "semantic_revision_owner": "TheoryDeveloper",
        "validation_owner": "AgentRuntime",
        "acceptance_owner": "ArchitectTheoryExecutionPreflightReviewer",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
    }
    return result


def _theory_revision_transport_lineage_errors(
    transport: Mapping[str, Any],
    *,
    revision_inputs: Mapping[str, Any],
) -> list[str]:
    expected = {
        "artifact_kind": "TheoryDeveloperWorkspaceRevisionTransport",
        "revision_mode": "model_owned_document_workspace",
        "revision_binding_id": revision_inputs.get("revision_binding_id", ""),
        "source_theory_packet_id": revision_inputs.get(
            "source_theory_packet_id", ""
        ),
        "source_theory_packet_hash": revision_inputs.get(
            "source_theory_packet_hash", ""
        ),
        "feedback_id": revision_inputs.get("feedback_id", ""),
        "source_feedback_fingerprint": revision_inputs.get(
            "source_feedback_fingerprint", ""
        ),
        "parent_core_payload_fingerprint": revision_inputs.get(
            "base_core_payload_fingerprint", ""
        ),
        "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
        "model_owned_artifact_edits": True,
        "theory_content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
    }
    return [
        f"theory revision transport {field} mismatch"
        for field, value in expected.items()
        if transport.get(field) != value
    ]


def _validate_theory_workspace_revision_packet(
    packet: Mapping[str, Any],
    *,
    revision_inputs: Mapping[str, Any],
    workspace_id: str,
    question: OpenResearchQuestion,
    require_workspace_edit_evidence: bool = False,
) -> list[str]:
    errors = _validate_theory_packet_for_question(packet, question=question)
    transport = packet.get("theory_revision_transport", {})
    if not isinstance(transport, Mapping):
        return [*errors, "theory workspace revision transport must be an object"]
    errors.extend(
        _theory_revision_transport_lineage_errors(
            transport,
            revision_inputs=revision_inputs,
        )
    )
    if transport.get("workspace_id") != workspace_id:
        errors.append("theory workspace revision transport workspace_id mismatch")
    changed = transport.get("changed_artifact_names", [])
    changed_documents = transport.get("changed_document_paths", [])
    if not isinstance(changed, list):
        errors.append("theory workspace changed artifact names must be an array")
        changed = []
    if not isinstance(changed_documents, list):
        errors.append("theory workspace changed document paths must be an array")
        changed_documents = []
    if not changed and not changed_documents:
        errors.append("theory workspace revision must change theory material")
    if set(changed) - set(THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT):
        errors.append("theory workspace revision names an unknown artifact")
    if transport.get("model_owned_artifact_edits") is not True:
        errors.append("theory workspace revision is not model-owned")
    if require_workspace_edit_evidence:
        write_count = transport.get("model_artifact_write_count", 0)
        document_write_count = transport.get("model_document_write_count", 0)
        if (
            not isinstance(write_count, int)
            or not isinstance(document_write_count, int)
            or write_count + document_write_count < 1
        ):
            errors.append("theory workspace revision has no model-authored writes")
        workspace_evidence = packet.get("llm_client_tool_loop", {})
        if not isinstance(workspace_evidence, Mapping):
            errors.append("theory workspace revision has no workspace evidence")
        else:
            writes = workspace_evidence.get("model_artifact_writes", [])
            if not isinstance(writes, list):
                errors.append("theory workspace write evidence is not an array")
                writes = []
            if write_count != len(writes):
                errors.append("theory workspace artifact write count mismatch")
            if transport.get("model_artifact_writes_hash") != stable_hash(
                writes
            ):
                errors.append("theory workspace artifact write hash mismatch")
            document_writes = workspace_evidence.get(
                "model_document_writes", []
            )
            if not isinstance(document_writes, list):
                errors.append("theory workspace document write evidence is not an array")
                document_writes = []
            if document_write_count != len(document_writes):
                errors.append("theory workspace document write count mismatch")
            if transport.get("model_document_writes_hash") != stable_hash(
                document_writes
            ):
                errors.append("theory workspace document write hash mismatch")
            if workspace_evidence.get("write_transport") != (
                THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT
            ):
                errors.append("theory workspace write transport evidence mismatch")
    if transport.get("runtime_edited_theory") is not False:
        errors.append("runtime cannot edit theory workspace semantics")
    revised_core = {
        field: deepcopy(packet[field])
        for field in THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
        if field in packet
    }
    if transport.get("revised_core_payload_fingerprint") != stable_hash(
        revised_core
    ):
        errors.append("theory workspace revision payload fingerprint mismatch")
    return list(dict.fromkeys(errors))


def _generate_initial_theory_artifact_workspace(
    *,
    provider: GeneratorBackend,
    provider_name: str,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    theory_prompt_mode: str,
    request_model: str,
    model_tier: str,
    base_model_tier: str,
    configured_serious_model: str,
    serious_model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    formalization_authoring_required: bool,
    theory_scratchpad: TheoryScratchpadConfig | None = None,
    research_sources: ResearchSourceSnapshot | None = None,
    research_source_discovery: ResearchSourceDiscovery | None = None,
    research_source_execution: ResearchSourceExecutionSpec | None = None,
    theory_workspace_root: Path | None = None,
    progress_checkpoint_state: (
        tuple[dict[str, Any], dict[str, Any], dict[str, str]] | None
    ) = None,
) -> dict[str, Any]:
    allow_source_checkpoint = source_replication_checkpoint_allowed(
        question,
        research_source_execution,
    )
    progress_checkpoint: dict[str, Any] = {}
    if progress_checkpoint_state is None:
        initial_artifacts = _empty_theory_core_workspace(file_authority=True)
        initial_documents: dict[str, str] = {}
    else:
        (
            progress_checkpoint,
            initial_artifacts,
            initial_documents,
        ) = progress_checkpoint_state
    read_only_artifacts = _initial_theory_workspace_read_only_artifacts(
        question=question,
        architect_context=architect_context,
        theory_prompt_mode=theory_prompt_mode,
        max_tool_calls=max_tool_calls,
        formalization_authoring_required=formalization_authoring_required,
        allow_source_replication_checkpoint=allow_source_checkpoint,
    )
    if progress_checkpoint:
        expected_authoring_binding_id = _initial_theory_authoring_binding_id(
            question_id=question.id,
            theory_prompt_mode=theory_prompt_mode,
            read_only_artifacts=read_only_artifacts,
        )
        authoring_binding_id = str(
            progress_checkpoint.get("authoring_binding_id", "") or ""
        )
        if authoring_binding_id != expected_authoring_binding_id:
            raise PacketValidationError(
                validation_label="TheoryDeveloper progress checkpoint",
                attempts=0,
                errors=[
                    "TheoryDeveloper initial progress checkpoint context mismatch"
                ],
                history=[],
            )
        read_only_artifacts["prior_theory_progress_checkpoint"] = (
            _theory_progress_prompt_artifact(progress_checkpoint)
        )
        workspace_id = str(
            progress_checkpoint.get("workspace_id", "") or ""
        )
    else:
        authoring_binding_id = _initial_theory_authoring_binding_id(
            question_id=question.id,
            theory_prompt_mode=theory_prompt_mode,
            read_only_artifacts=read_only_artifacts,
        )
        workspace_id = "theory_workspace:" + stable_hash(
            [authoring_binding_id, initial_artifacts]
        )[:20]
    workspace_dir = (
        theory_workspace_root / workspace_id.replace(":", "-")
        if theory_workspace_root is not None
        else None
    )
    writable_artifact_names = _theory_workspace_writable_handoff_names(
        question=question,
        formalization_authoring_required=formalization_authoring_required,
        artifacts=initial_artifacts,
    )

    def build_candidate(
        artifacts: Mapping[str, Any],
        changed_artifact_names: tuple[str, ...],
        document_manifest: Mapping[str, Any],
        changed_document_paths: tuple[str, ...],
    ) -> dict[str, Any]:
        raw_response = json.dumps(
            {
                "workspace_id": workspace_id,
                "artifact_hashes": {
                    name: stable_hash(value)
                    for name, value in artifacts.items()
                },
                "changed_artifact_names": list(changed_artifact_names),
            },
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
        packet = _normalize_theory_packet(
            artifacts,
            question=question,
            model=request_model,
            model_tier=model_tier,
            provider_name=provider_name,
            raw_response=raw_response,
            theory_prompt_mode=theory_prompt_mode,
            formalization_authoring_required=(
                formalization_authoring_required
            ),
        )
        packet["theory_workspace_manifest"] = deepcopy(
            dict(document_manifest)
        )
        packet["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
        packet["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
        packet["theory_derivation_contract"] = {
            **dict(packet.get("theory_derivation_contract", {}) or {}),
            "content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
            "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
            "n_documents": len(document_manifest.get("documents", []) or []),
            "n_claim_index_rows": _safe_len(
                packet.get("theory_derivation_packet", {}).get(
                    "claim_index", []
                )
            ),
            "changed_document_paths": list(changed_document_paths),
        }
        _refresh_theory_packet_id(packet, question=question)
        return packet

    result = run_theory_artifact_workspace(
        provider=provider,
        system_prompt=(
            THEORY_DEVELOPER_SYSTEM_PROMPT
            + "\nUse the supplied client tools as the sole write path for the "
            "current theory workspace."
        ),
        user_prompt=_initial_theory_workspace_prompt(
            question=question,
            theory_prompt_mode=theory_prompt_mode,
            max_tool_calls=max_tool_calls,
            formalization_authoring_required=(
                formalization_authoring_required
            ),
            allow_source_replication_checkpoint=allow_source_checkpoint,
            continuing_from_progress=bool(progress_checkpoint),
        ),
        model=request_model,
        model_tier=model_tier,
        temperature=temperature,
        max_tokens=max_tokens,
        max_turns=max(1, max_turns),
        max_tool_calls=max(1, max_tool_calls),
        max_no_progress_turns=max(1, max_no_progress_turns),
        workspace_id=workspace_id,
        question_id=question.id,
        authoring_binding_id=authoring_binding_id,
        workspace_operation="initial_discovery",
        initial_artifacts=initial_artifacts,
        initial_documents=initial_documents,
        read_only_documents=read_only_artifacts.pop("read_only_documents", {}),
        read_only_artifacts=read_only_artifacts,
        build_candidate=build_candidate,
        validate_candidate=lambda packet: _validate_theory_packet_for_question(
            packet,
            question=question,
        ),
        scratchpad=theory_scratchpad,
        research_sources=research_sources,
        research_source_discovery=research_source_discovery,
        research_source_execution=research_source_execution,
        allow_source_replication_checkpoint=allow_source_checkpoint,
        task_intent=question.task_intent,
        workspace_dir=workspace_dir,
        require_document_authority=True,
        writable_artifact_names=writable_artifact_names,
        prior_changed_artifact_names=(
            progress_checkpoint.get("changed_artifact_names", [])
            if progress_checkpoint
            else ()
        ),
        prior_changed_document_paths=(
            progress_checkpoint.get("changed_document_paths", [])
            if progress_checkpoint
            else ()
        ),
        prior_removed_document_paths=(
            progress_checkpoint.get("removed_document_paths", [])
            if progress_checkpoint
            else ()
        ),
        prior_client_tool_session_ref=(
            progress_checkpoint.get("client_tool_session_ref", {})
            if progress_checkpoint
            else None
        ),
        prior_workspace_checkpoint=(
            progress_checkpoint if progress_checkpoint else None
        ),
        request_metadata={
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: research_workspace_authorization_fingerprint(
                question, architect_context, {"subsystem": "TheoryDeveloper", "workspace_id": workspace_id}),
            "subsystem": "TheoryDeveloper",
            "agent": "LLMTheoryDeveloperAgent",
            "theory_developer_phase": "initial_artifact_workspace",
            "provider_name": provider_name,
            "model_tier": model_tier,
            "base_model_tier": base_model_tier,
            "configured_serious_model": configured_serious_model,
            "serious_model_tier": serious_model_tier,
            "theory_prompt_mode": theory_prompt_mode,
            "serious_theory_mode": (
                theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
            ),
            "resolved_model": request_model,
            "authoring_mode": "model_owned_document_workspace",
        },
    )
    packet = deepcopy(dict(result.core_packet))
    workspace_evidence = deepcopy(dict(result.evidence))
    packet["llm_client_tool_loop"] = workspace_evidence
    if packet.get("artifact_kind") == SOURCE_REPLICATION_CHECKPOINT_KIND:
        return packet
    packet = _finalize_document_workspace_estimator_interfaces(
        packet,
        question=question,
    )
    errors = _validate_theory_packet_for_question(packet, question=question)
    changed = set(workspace_evidence.get("changed_artifact_names", []) or [])
    required_authored_artifacts = {
        field
        for field, required in theory_handoff_requirements(
            question,
            formalization_authoring_required=formalization_authoring_required,
        ).items()
        if required
    }
    if not required_authored_artifacts.issubset(changed):
        errors.append(
            "initial theory workspace did not author every required nonempty artifact"
        )
    if workspace_evidence.get("workspace_operation") != "initial_discovery":
        errors.append("initial theory workspace operation identity mismatch")
    if workspace_evidence.get("write_transport") != (
        THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT
    ):
        errors.append("initial theory workspace write transport mismatch")
    if int(workspace_evidence.get("n_model_artifact_writes", 0) or 0) < 1:
        errors.append("initial theory workspace has no model-authored writes")
    if workspace_evidence.get("runtime_edited_theory") is not False:
        errors.append("runtime cannot edit initial theory workspace semantics")
    if errors:
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper initial artifact workspace",
            attempts=int(workspace_evidence.get("turns", 0) or 0),
            errors=list(dict.fromkeys(errors)),
            history=workspace_evidence.get("history", []),
            last_invalid_packet=packet,
        )
    packet["validation_errors"] = []
    packet["ok"] = True
    return packet


def _generate_theory_workspace_revision(
    *,
    provider: GeneratorBackend,
    provider_name: str,
    question: OpenResearchQuestion,
    revision_inputs: Mapping[str, Any],
    root_authorization_context: Mapping[str, Any],
    request_model: str,
    model_tier: str,
    base_model_tier: str,
    configured_serious_model: str,
    serious_model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    formalization_authoring_required: bool,
    theory_scratchpad: TheoryScratchpadConfig | None = None,
    research_sources: ResearchSourceSnapshot | None = None,
    research_source_discovery: ResearchSourceDiscovery | None = None,
    research_source_execution: ResearchSourceExecutionSpec | None = None,
    theory_workspace_root: Path | None = None,
    progress_checkpoint_state: (
        tuple[dict[str, Any], dict[str, Any], dict[str, str]] | None
    ) = None,
) -> dict[str, Any]:
    raw_parent_payload = revision_inputs.get("base_core_payload", {})
    if not isinstance(raw_parent_payload, Mapping):
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=0,
            errors=["parent theory workspace is not an object"],
            history=[],
        )
    progress_checkpoint: dict[str, Any] = {}
    parent_client_tool_session_ref = revision_inputs.get(
        "parent_client_tool_session_ref", {}
    )
    parent_client_tool_session_ref = (
        deepcopy(dict(parent_client_tool_session_ref))
        if isinstance(parent_client_tool_session_ref, Mapping)
        else {}
    )
    if progress_checkpoint_state is None:
        initial_artifacts = {
            field: deepcopy(raw_parent_payload[field])
            for field in THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
            if field in raw_parent_payload
        }
        workspace_id = str(
            parent_client_tool_session_ref.get("session_id", "") or ""
        ).strip()
        if not workspace_id:
            workspace_id = "theory_workspace:" + stable_hash(
                [
                    question.id,
                    revision_inputs.get("revision_binding_id", ""),
                    revision_inputs.get("base_core_payload_fingerprint", ""),
                ]
            )[:20]
        try:
            initial_documents = load_theory_workspace_documents(
                raw_parent_payload
            )
        except (OSError, UnicodeError, ValueError) as exc:
            raise PacketValidationError(
                validation_label="LLM TheoryDeveloper document workspace",
                attempts=0,
                errors=[str(exc)],
                history=[],
            ) from exc
    else:
        (
            progress_checkpoint,
            initial_artifacts,
            initial_documents,
        ) = progress_checkpoint_state
        if str(
            progress_checkpoint.get("authoring_binding_id", "") or ""
        ) != str(revision_inputs.get("revision_binding_id", "") or ""):
            raise PacketValidationError(
                validation_label="TheoryDeveloper progress checkpoint",
                attempts=0,
                errors=[
                    "TheoryDeveloper revision progress checkpoint binding mismatch"
                ],
                history=[],
            )
        workspace_id = str(
            progress_checkpoint.get("workspace_id", "") or ""
        )
        parent_client_tool_session_ref = deepcopy(
            dict(progress_checkpoint.get("client_tool_session_ref", {}))
            if isinstance(
                progress_checkpoint.get("client_tool_session_ref", {}),
                Mapping,
            )
            else {}
        )
    workspace_dir = (
        theory_workspace_root / workspace_id.replace(":", "-")
        if theory_workspace_root is not None
        else None
    )
    writable_artifact_names = _theory_workspace_writable_handoff_names(
        question=question,
        formalization_authoring_required=formalization_authoring_required,
        artifacts=initial_artifacts,
    )

    def build_candidate(
        artifacts: Mapping[str, Any],
        changed_artifact_names: tuple[str, ...],
        document_manifest: Mapping[str, Any],
        changed_document_paths: tuple[str, ...],
    ) -> dict[str, Any]:
        raw_response = json.dumps(
            {
                "workspace_id": workspace_id,
                "artifact_hashes": {
                    name: stable_hash(value) for name, value in artifacts.items()
                },
                "changed_artifact_names": list(changed_artifact_names),
            },
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
        packet = _normalize_theory_packet(
            artifacts,
            question=question,
            model=request_model,
            model_tier=model_tier,
            provider_name=provider_name,
            raw_response=raw_response,
            theory_prompt_mode=THEORY_PROMPT_MODE_SERIOUS_REVISION,
            formalization_authoring_required=(
                formalization_authoring_required
            ),
        )
        packet["theory_workspace_manifest"] = deepcopy(
            dict(document_manifest)
        )
        packet["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
        packet["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
        packet["theory_derivation_contract"] = {
            **dict(packet.get("theory_derivation_contract", {}) or {}),
            "content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
            "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
            "n_documents": len(document_manifest.get("documents", []) or []),
            "n_claim_index_rows": _safe_len(
                packet.get("theory_derivation_packet", {}).get(
                    "claim_index", []
                )
            ),
            "changed_document_paths": list(changed_document_paths),
        }
        _refresh_theory_packet_id(packet, question=question)
        return _attach_theory_workspace_revision_transport(
            packet,
            revision_inputs=revision_inputs,
            provider_name=provider_name,
            model=request_model,
            model_tier=model_tier,
            workspace_id=workspace_id,
            changed_artifact_names=changed_artifact_names,
            changed_document_paths=changed_document_paths,
        )

    read_only_artifacts = _theory_workspace_read_only_observations(
        revision_inputs
    )
    read_only_documents = deepcopy(
        dict(read_only_artifacts.pop("read_only_documents", {}))
    )
    if progress_checkpoint:
        read_only_artifacts["prior_theory_progress_checkpoint"] = (
            _theory_progress_prompt_artifact(progress_checkpoint)
        )
    result = run_theory_artifact_workspace(
        provider=provider,
        system_prompt=(
            THEORY_DEVELOPER_SYSTEM_PROMPT
            + "\nUse the supplied client tools as the sole write path for the "
            "current theory workspace."
        ),
        user_prompt=_theory_workspace_revision_prompt(
            question=question,
            revision_inputs=revision_inputs,
            formalization_authoring_required=(
                formalization_authoring_required
            ),
            continuing_from_progress=bool(progress_checkpoint),
        ),
        model=request_model,
        model_tier=model_tier,
        temperature=temperature,
        max_tokens=max_tokens,
        max_turns=max(1, max_turns),
        max_tool_calls=max(1, max_tool_calls),
        max_no_progress_turns=max(1, max_no_progress_turns),
        workspace_id=workspace_id,
        question_id=question.id,
        authoring_binding_id=str(
            revision_inputs.get("revision_binding_id", "") or ""
        ),
        workspace_operation="targeted_revision",
        initial_artifacts=initial_artifacts,
        initial_documents=initial_documents,
        read_only_artifacts=read_only_artifacts,
        read_only_documents=read_only_documents,
        build_candidate=build_candidate,
        validate_candidate=lambda packet: (
            _validate_theory_workspace_revision_packet(
                packet,
                revision_inputs=revision_inputs,
                workspace_id=workspace_id,
                question=question,
            )
        ),
        scratchpad=theory_scratchpad,
        research_sources=research_sources,
        research_source_discovery=research_source_discovery,
        research_source_execution=research_source_execution,
        task_intent=question.task_intent,
        workspace_dir=workspace_dir,
        require_document_authority=True,
        writable_artifact_names=writable_artifact_names,
        prior_changed_artifact_names=(
            progress_checkpoint.get("changed_artifact_names", [])
            if progress_checkpoint
            else ()
        ),
        prior_changed_document_paths=(
            progress_checkpoint.get("changed_document_paths", [])
            if progress_checkpoint
            else ()
        ),
        prior_removed_document_paths=(
            progress_checkpoint.get("removed_document_paths", [])
            if progress_checkpoint
            else ()
        ),
        prior_client_tool_session_ref=(
            parent_client_tool_session_ref or None
        ),
        prior_workspace_checkpoint=(
            progress_checkpoint if progress_checkpoint else None
        ),
        prior_scratch_execution_refs=revision_inputs.get(
            "parent_scratch_execution_refs", ()
        ),
        request_metadata={
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: research_workspace_authorization_fingerprint(
                question, root_authorization_context, {"subsystem": "TheoryDeveloper", "workspace_id": workspace_id}),
            "subsystem": "TheoryDeveloper",
            "agent": "LLMTheoryDeveloperAgent",
            "theory_developer_phase": "artifact_workspace_revision",
            "provider_name": provider_name,
            "model_tier": model_tier,
            "base_model_tier": base_model_tier,
            "configured_serious_model": configured_serious_model,
            "serious_model_tier": serious_model_tier,
            "theory_prompt_mode": THEORY_PROMPT_MODE_SERIOUS_REVISION,
            "serious_theory_mode": True,
            "resolved_model": request_model,
            "source_theory_packet_id": revision_inputs.get(
                "source_theory_packet_id", ""
            ),
            "revision_binding_id": revision_inputs.get("revision_binding_id", ""),
            "revision_source": revision_inputs.get("revision_source", ""),
            "revision_generation_mode": "model_owned_document_workspace",
            "parent_core_payload_fingerprint": revision_inputs.get(
                "base_core_payload_fingerprint", ""
            ),
        },
    )
    packet = deepcopy(dict(result.core_packet))
    workspace_evidence = deepcopy(dict(result.evidence))
    packet["llm_client_tool_loop"] = workspace_evidence
    transport = dict(packet.get("theory_revision_transport", {}) or {})
    transport["workspace_evidence_id"] = str(
        workspace_evidence.get("artifact_id", "") or ""
    )
    transport["workspace_evidence_hash"] = stable_hash(workspace_evidence)
    transport["model_artifact_write_count"] = int(
        workspace_evidence.get("n_model_artifact_writes", 0) or 0
    )
    transport["model_artifact_writes_hash"] = stable_hash(
        workspace_evidence.get("model_artifact_writes", [])
    )
    transport["model_document_write_count"] = int(
        workspace_evidence.get("n_model_document_writes", 0) or 0
    )
    transport["model_document_writes_hash"] = stable_hash(
        workspace_evidence.get("model_document_writes", [])
    )
    packet["theory_revision_transport"] = transport
    packet = _finalize_document_workspace_estimator_interfaces(
        packet,
        question=question,
    )
    errors = _validate_theory_workspace_revision_packet(
        packet,
        revision_inputs=revision_inputs,
        workspace_id=workspace_id,
        question=question,
        require_workspace_edit_evidence=True,
    )
    if errors:
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=int(workspace_evidence.get("turns", 0) or 0),
            errors=errors,
            history=workspace_evidence.get("history", []),
            last_invalid_packet=packet,
        )
    packet["validation_errors"] = []
    packet["ok"] = True
    return packet


def _theory_core_generation_phase(core_packet: Mapping[str, Any]) -> str:
    client_tool_loop = core_packet.get("llm_client_tool_loop", {})
    if (
        isinstance(client_tool_loop, Mapping)
        and client_tool_loop.get("workspace_operation")
        == "initial_discovery"
    ):
        return "initial_artifact_workspace"
    transport = core_packet.get("theory_revision_transport", {})
    if not isinstance(transport, Mapping) or not transport:
        return "core_theory_workspace"
    if transport.get("artifact_kind") == (
        "TheoryDeveloperWorkspaceRevisionTransport"
    ):
        return "artifact_workspace_revision"
    return "full_core_revision"


def _theory_core_generation_phase_record(
    core_packet: Mapping[str, Any],
) -> dict[str, Any]:
    phase: dict[str, Any] = {
        "phase": _theory_core_generation_phase(core_packet),
        "model": str(core_packet.get("model", "")),
        "model_tier": str(core_packet.get("model_tier", "")),
    }
    client_tool_loop = core_packet.get("llm_client_tool_loop", {})
    if isinstance(client_tool_loop, Mapping) and client_tool_loop:
        phase["client_tool_transport"] = str(
            client_tool_loop.get("transport", "") or ""
        )
        phase["client_tool_turns"] = int(
            client_tool_loop.get("turns", 0) or 0
        )
        phase["client_tool_calls"] = int(
            client_tool_loop.get("tool_calls", 0) or 0
        )
    return phase


def _finalize_document_workspace_estimator_interfaces(
    packet: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
) -> dict[str, Any]:
    """Record exact ABIs authored or retained by the document workspace."""

    merged = deepcopy(dict(packet))
    specs = merged.get("estimator_specs", [])
    if not isinstance(specs, list) or not specs:
        return merged
    normalize_theory_estimator_interface_contracts(merged)
    workspace_evidence = merged.get("llm_client_tool_loop", {})
    workspace_evidence = (
        dict(workspace_evidence)
        if isinstance(workspace_evidence, Mapping)
        else {}
    )
    changed_artifacts = {
        str(name)
        for name in workspace_evidence.get("changed_artifact_names", []) or []
        if str(name)
    }
    interface_rows = {
        str(spec.get("id", "") or ""): str(
            spec.get("estimator_interface_contract_id", "") or ""
        )
        for spec in merged.get("estimator_specs", []) or []
        if isinstance(spec, Mapping) and str(spec.get("id", "") or "")
    }
    interface_authored = "estimator_specs" in changed_artifacts
    disposition = (
        "model_authored_or_revised_in_workspace"
        if interface_authored
        else "parent_workspace_value_retained"
    )
    source_packet_id = str(merged.get("packet_id", "") or "")
    authoring_identity = {
        "source_theory_packet_id": source_packet_id,
        "workspace_evidence_id": str(
            workspace_evidence.get("artifact_id", "") or ""
        ),
        "interface_contract_ids": interface_rows,
        "disposition": disposition,
    }
    merged["estimator_interface_authoring"] = {
        "artifact_kind": "TheoryEstimatorInterfaceWorkspaceRecord",
        "artifact_id": (
            "theory_estimator_interfaces_workspace:"
            + stable_hash(authoring_identity)[:24]
        ),
        **authoring_identity,
        "provider": str(merged.get("provider", "") or ""),
        "model": str(merged.get("model", "") or ""),
        "model_tier": str(merged.get("model_tier", "") or ""),
        "n_interfaces": len(interface_rows),
        "n_interfaces_authored_or_revised": (
            len(interface_rows) if interface_authored else 0
        ),
        "n_interfaces_reused": 0 if interface_authored else len(interface_rows),
        "model_call_used": interface_authored,
        "dedicated_model_call_used": False,
        "workspace_session_used": True,
        "runtime_edited_interfaces": False,
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
    }
    phase = _theory_core_generation_phase_record(merged)
    phase.update(
        {
            "estimator_interface_disposition": disposition,
            "dedicated_estimator_interface_model_call_used": False,
        }
    )
    merged["theory_generation_phases"] = [phase]
    _refresh_theory_packet_id(merged, question=question)
    return merged


def _refresh_theory_packet_id(
    packet: dict[str, Any],
    *,
    question: OpenResearchQuestion,
) -> None:
    body_fields = [
        *THEORY_DEVELOPER_OUTPUT_CONTRACT,
        "theory_prompt_mode",
        "serious_theory_mode",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "kernel_verified",
        "verified_theorem_count",
        "theory_derivation_contract",
        "theory_workspace_manifest",
        "theory_content_authority",
        "structured_handoff_role",
    ]
    body = {
        field: deepcopy(packet[field])
        for field in body_fields
        if field in packet
    }
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": packet.get("provider", ""),
            "model": packet.get("model", ""),
            "model_tier": packet.get("model_tier", ""),
            "body": body,
        }
    )[:24]
    packet["packet_id"] = f"theory_derivation:{packet_id}"


def _canonicalize_theory_derivation_packet(
    derivation: Mapping[str, Any],
    *,
    formalization_requests: Any,
) -> dict[str, Any]:
    packet = dict(derivation)
    packet["derivation_steps"] = [
        _canonicalize_derivation_step(row, index)
        for index, row in enumerate(packet.get("derivation_steps", []) or [], start=1)
        if isinstance(row, Mapping)
    ]
    packet["equation_chain"] = [
        _canonicalize_equation_row(row, index)
        for index, row in enumerate(packet.get("equation_chain", []) or [], start=1)
        if isinstance(row, Mapping)
    ]
    derivation_step_ids = [
        str(row.get("id", "") or "").strip()
        for row in packet["derivation_steps"]
        if str(row.get("id", "") or "").strip()
    ]
    packet["assumption_ledger"] = [
        _canonicalize_assumption_row(row, derivation_step_ids)
        for row in packet.get("assumption_ledger", []) or []
        if isinstance(row, Mapping)
    ]
    packet["sanity_checks"] = [
        dict(row)
        for row in packet.get("sanity_checks", []) or []
        if isinstance(row, Mapping)
    ]
    handoff = packet.get("formalization_handoff", {})
    if not isinstance(handoff, Mapping) or not handoff:
        handoff = _formalization_handoff_from_requests(formalization_requests)
    packet["formalization_handoff"] = dict(handoff) if isinstance(handoff, Mapping) else {}
    return packet


def _canonicalize_derivation_step(row: Mapping[str, Any], index: int) -> dict[str, Any]:
    canonical = dict(row)
    canonical["id"] = _first_nonempty(row, "id", "step_id", "name") or f"D{index}"
    canonical["claim"] = _first_nonempty(
        row,
        "claim",
        "statement",
        "result",
        "goal",
        "description",
        "summary",
    )
    canonical["equation_or_argument"] = _first_nonempty(
        row,
        "equation_or_argument",
        "argument",
        "equation",
        "justification",
        "reasoning",
        "derivation",
        "proof_idea",
    )
    return canonical


def _canonicalize_equation_row(row: Mapping[str, Any], index: int) -> dict[str, Any]:
    canonical = dict(row)
    canonical["step_id"] = _first_nonempty(row, "step_id", "id", "name") or f"E{index}"
    canonical["lhs"] = _first_nonempty(row, "lhs", "left", "from", "start")
    canonical["rhs"] = _first_nonempty(row, "rhs", "right", "to", "end")
    canonical["justification"] = _first_nonempty(
        row,
        "justification",
        "reason",
        "argument",
        "because",
        "explanation",
    )
    return canonical


def _canonicalize_assumption_row(
    row: Mapping[str, Any],
    derivation_step_ids: list[str],
) -> dict[str, Any]:
    canonical = dict(row)
    canonical["assumption"] = _first_nonempty(
        row,
        "assumption",
        "name",
        "label",
        "condition",
        "statement",
        "description",
    )
    used_in = row.get("used_in")
    if not used_in:
        used_in = row.get("used_by") or row.get("supports") or row.get("depends_on")
    if not used_in and derivation_step_ids:
        used_in = derivation_step_ids[:2]
        canonical["used_in_inferred_by_runtime"] = True
    canonical["used_in"] = used_in
    return canonical


def _formalization_handoff_from_requests(requests: Any) -> dict[str, Any]:
    request_rows = [row for row in (requests or []) if isinstance(row, Mapping)]
    if not request_rows:
        return {}
    first = request_rows[0] if request_rows else {}
    target = _first_nonempty(first, "target_theorem_card", "id", "target", "name")
    lean_target = _first_nonempty(
        first,
        "lean_statement_sketch",
        "lean_statement",
        "statement",
        "target",
    )
    constraints = first.get("semantic_alignment_constraints", [])
    if isinstance(constraints, str):
        constraints = [constraints]
    if not constraints:
        constraints = [
            "preserve the informal theorem semantics; local Lean kernel evidence is required before proof claims"
        ]
    return {
        "source_theorem_target": target,
        "candidate_lean_targets": [lean_target] if lean_target else [],
        "required_definitions": [],
        "lemma_dependencies": [],
        "semantic_alignment_constraints": list(constraints),
        "runtime_inferred_from_formalization_requests": True,
    }


def _first_nonempty(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", [], {}):
            return value
    return ""



def _ledger_row_for_packet(packet: Mapping[str, Any], question: OpenResearchQuestion) -> EvidenceLedgerRow:
    artifact_id = str(packet.get("packet_id", ""))
    return EvidenceLedgerRow(
        evidence_id="evidence:" + stable_hash([question.id, artifact_id])[:20],
        question_id=question.id,
        artifact_id=artifact_id,
        artifact_kind="TheoryDerivationPacket",
        source_agent="LLMTheoryDeveloperAgent",
        evidence_status="PROPOSAL_RECORDED_REQUIRES_GATES",
        proof_evidence_status=THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        boundary=KERNEL_PROOF_BOUNDARY,
        created_at=datetime.now(timezone.utc).isoformat(),
    )



def _project_state(
    questions: list[OpenResearchQuestion],
    packets: list[dict[str, Any]],
    ledger_rows: list[EvidenceLedgerRow],
) -> dict[str, Any]:
    return {
        "schema_version": ARCHITECT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "state_kind": "ResearchArchitectProjectState",
        "status": "LLM_THEORY_DEVELOPMENT_RECORDED_REQUIRES_VERIFIER_SIMULATION_GATES",
        "questions": [
            {"id": row.id, "title": row.title, "description": row.description, "tags": list(row.tags)}
            for row in questions
        ],
        "active_artifacts": [packet.get("packet_id", "") for packet in packets],
        "evidence_rows": [row.evidence_id for row in ledger_rows],
        "next_required_gates": [
            "source_grounding_review",
            "simulation_ademp_execution",
            "formalization_request_semantic_alignment",
            "AXLE_or_local_Lean_kernel_verification_for_formal_claims",
        ],
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _forbidden_proof_claims(value: Any, *, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            key_text = str(key).lower()
            if key_text in {"kernel_verified", "lean_verified", "theorem_verified"} and child is True:
                errors.append(f"forbidden proof claim at {child_path}")
            if key_text in {"proof_evidence_status", "kernel_status", "verification_strength"}:
                text = str(child).upper()
                if text in {"PROVED", "VERIFIED", "KERNEL_VERIFIED", "CLOSED"}:
                    errors.append(f"forbidden proof status at {child_path}: {child}")
            errors.extend(_forbidden_proof_claims(child, path=child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            errors.extend(_forbidden_proof_claims(child, path=f"{path}[{idx}]"))
    return errors


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, default=str, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _markdown_report(manifest: Mapping[str, Any], packets: list[Mapping[str, Any]]) -> str:
    lines = [
        "# Research Architect Theory Development",
        "",
        f"- Questions: {manifest.get('n_questions')}",
        f"- Theory packets: {manifest.get('n_theory_derivation_packets')}",
        f"- Proof evidence: `{THEORY_DERIVATION_NOT_PROOF_EVIDENCE}`",
        "",
        "## Packets",
        "",
    ]
    for packet in packets:
        question = packet.get("question", {}) if isinstance(packet.get("question"), Mapping) else {}
        lines.append(f"- `{packet.get('packet_id', '')}` for `{question.get('id', '')}`")
        for theorem in packet.get("theorem_cards", []) or []:
            if isinstance(theorem, Mapping):
                lines.append(f"  - theorem `{theorem.get('id', '')}`: {theorem.get('conclusion', '')}")
    lines.extend(["", "## Boundary", "", KERNEL_PROOF_BOUNDARY, ""])
    return "\n".join(lines)
