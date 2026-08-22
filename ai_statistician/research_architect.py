from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from .fingerprint import stable_hash
from .estimator_interface_contract import (
    ESTIMATOR_REQUEST_BINDINGS,
    estimator_interface_contract_errors,
    estimator_interface_contract_id,
    estimator_interface_contract_json_schema,
    normalize_estimator_interface_contract,
    normalize_theory_estimator_interface_contracts,
    project_executable_estimator_interface_contract,
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
from .structured_output_retry import (
    PacketValidationError,
    extract_json_object,
    generate_validated_json_packet,
)
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND,
)
from .research_schema import (
    OpenResearchQuestion,
    research_dimension_requirements,
    research_question_payload,
)
from .research_source_library import (
    ResearchSourceExecutionSpec,
    ResearchSourceSnapshot,
)
from .research_source_discovery import ResearchSourceDiscovery
from .semantic_review_feedback import model_observations_without_repair_recipes
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
    THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND,
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
THEORY_DEVELOPER_STAGE_CHECKPOINT_KIND = "TheoryDeveloperStageRecoveryCheckpoint"
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

SOURCE_REPLICATION_CHECKPOINT_REQUIRED_DIMENSIONS = frozenset(
    {"source_replication", "unresolved_gaps"}
)


def source_replication_checkpoint_allowed(
    question: OpenResearchQuestion,
    research_source_execution: ResearchSourceExecutionSpec | None,
) -> bool:
    """Allow a direct checkpoint only for an explicitly source-only objective."""

    if research_source_execution is None:
        return False
    required_dimensions = {
        str(dimension)
        for dimension, requirement in question.task_intent.items()
        if str(requirement) == "required"
    }
    return bool(
        "source_replication" in required_dimensions
        and required_dimensions.issubset(
            SOURCE_REPLICATION_CHECKPOINT_REQUIRED_DIMENSIONS
        )
    )


def theory_handoff_requirements(
    question: OpenResearchQuestion,
    *,
    formalization_authoring_required: bool,
) -> dict[str, bool]:
    """Select only the compact handoffs required by the frozen task intent."""

    dimensions = research_dimension_requirements(question.task_intent)
    legacy_full_handoff = not dimensions
    implementation_required = bool(
        legacy_full_handoff
        or dimensions["scientific_code"] == "required"
    )
    formal_handoff_required = bool(
        legacy_full_handoff
        or formalization_authoring_required
        or dimensions["formal"] == "required"
    )
    return {
        "problem_card": True,
        "theory_derivation_packet": True,
        "estimator_specs": implementation_required,
        "theorem_cards": formal_handoff_required,
        "proof_plan": formal_handoff_required,
        "simulation_ademp_spec": bool(
            legacy_full_handoff or dimensions["empirical"] == "required"
        ),
        "formalization_requests": bool(formalization_authoring_required),
    }


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
    for field, required in requirements.items():
        if required or field not in output:
            continue
        output[field] = [] if isinstance(output[field], list) else {}
    if not formalization_authoring_required:
        derivation_contract = output.get("theory_derivation_packet", {})
        if isinstance(derivation_contract, dict):
            derivation_contract["formalization_handoff"] = {}
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
    max_validation_retries: int = 2
    theory_workspace_max_turns: int = 12
    theory_workspace_max_tool_calls: int = 24
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
        formalization_authoring_required = (
            _theory_formalization_authoring_required(context)
        )
        serious_theory_mode = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
        transport_recovery = _theory_developer_transport_recovery(context)
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
        backend_provider_name = str(
            getattr(self.provider, "provider_name", self.config.provider_name)
            or self.config.provider_name
        ).strip().lower()
        use_provider_structured_output = backend_provider_name == "anthropic"
        effective_max_validation_retries = (
            min(self.config.max_validation_retries, 1)
            if transport_recovery
            else self.config.max_validation_retries
        )
        revision_inputs: Mapping[str, Any] | None = None
        document_workspace_required = bool(
            theory_workspace_root is not None or serious_theory_mode
        )
        recovered_core_packet = _theory_developer_recovered_core_checkpoint(
            context,
            question=question,
            theory_prompt_mode=theory_prompt_mode,
        )
        progress_checkpoint_state = (
            _theory_developer_progress_checkpoint_state(
                context,
                question=question,
                theory_prompt_mode=theory_prompt_mode,
            )
        )
        if (
            recovered_core_packet is not None
            and progress_checkpoint_state is not None
        ):
            raise PacketValidationError(
                validation_label="TheoryDeveloper recovery checkpoint",
                attempts=0,
                errors=[
                    "interface-stage and theory-progress recovery cannot be active "
                    "at the same time"
                ],
                history=[],
            )
        if (
            (
                self.research_sources is not None
                or self.research_source_discovery is not None
            )
            and recovered_core_packet is None
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
        if recovered_core_packet is not None:
            if document_workspace_required and recovered_core_packet.get(
                "theory_content_authority"
            ) != THEORY_WORKSPACE_CONTENT_AUTHORITY:
                raise PacketValidationError(
                    validation_label="LLM TheoryDeveloper document workspace",
                    attempts=0,
                    errors=[
                        "AgentRuntime and serious theory recovery require a "
                        "model-authored Markdown/LaTeX checkpoint; a legacy "
                        "JSON-only core packet cannot become the theory authority"
                    ],
                    history=[],
                )
            core_packet = recovered_core_packet
        elif theory_prompt_mode == THEORY_PROMPT_MODE_SERIOUS_REVISION:
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
            if document_workspace_required:
                raise PacketValidationError(
                    validation_label="LLM TheoryDeveloper document workspace",
                    attempts=0,
                    errors=[
                        "AgentRuntime and serious theory authoring require native "
                        "client-tool turns with model-authored Markdown/LaTeX; "
                        "the legacy JSON-only theory transport is not a valid fallback"
                    ],
                    history=[],
                )
            user_prompt = build_theory_developer_prompt(
                question,
                architect_context=context,
            )
            request = GeneratorRequest(
                system_prompt=THEORY_DEVELOPER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=request_model,
                max_tokens=effective_max_tokens,
                temperature=self.config.temperature,
                schema=_theory_developer_core_json_schema(
                    theory_prompt_mode=theory_prompt_mode,
                    transport_recovery=transport_recovery,
                    formalization_authoring_required=(
                        formalization_authoring_required
                    ),
                ),
                metadata={
                    "subsystem": "TheoryDeveloper",
                    "agent": "LLMTheoryDeveloperAgent",
                    "theory_developer_phase": "core_theory_workspace",
                    "provider_name": self.config.provider_name,
                    "model_tier": effective_model_tier,
                    "base_model_tier": self.config.model_tier,
                    "configured_serious_model": self.config.serious_model,
                    "serious_model_tier": self.config.serious_model_tier,
                    "theory_prompt_mode": theory_prompt_mode,
                    "serious_theory_mode": serious_theory_mode,
                    "transport_recovery": transport_recovery,
                    "effective_max_validation_retries": effective_max_validation_retries,
                    "resolved_model": request_model,
                    **(
                        {"provider_structured_output": True}
                        if use_provider_structured_output
                        else {}
                    ),
                },
            )

            def build_packet(
                raw_payload: Mapping[str, Any],
                response: Any,
                raw_text: str,
            ) -> dict[str, Any]:
                return _normalize_theory_packet(
                    raw_payload,
                    question=question,
                    model=response.model or request_model,
                    model_tier=effective_model_tier,
                    provider_name=self.config.provider_name or response.provider,
                    raw_response=raw_text,
                    theory_prompt_mode=theory_prompt_mode,
                    formalization_authoring_required=(
                        formalization_authoring_required
                    ),
                )

            core_packet = generate_validated_json_packet(
                provider=self.provider,
                request=request,
                extract_payload=_extract_json_object,
                build_packet=build_packet,
                validate_packet=validate_theory_core_packet,
                validation_label="LLM TheoryDeveloper core packet",
                max_validation_retries=effective_max_validation_retries,
            )
        if (
            core_packet.get("artifact_kind")
            == SOURCE_REPLICATION_CHECKPOINT_KIND
        ):
            return core_packet
        # Test doubles may return a sentinel without running the supplied builder.
        if not core_packet.get("estimator_specs"):
            return core_packet
        if not validate_theory_packet(core_packet):
            return core_packet
        return _complete_theory_estimator_interfaces(
            core_packet,
            question=question,
            provider=self.provider,
            provider_name=self.config.provider_name,
            request_model=request_model,
            model_tier=effective_model_tier,
            temperature=self.config.temperature,
            max_tokens=effective_max_tokens,
            max_validation_retries=effective_max_validation_retries,
            use_provider_structured_output=use_provider_structured_output,
            parent_estimator_interface_bindings=(
                revision_inputs.get("parent_estimator_interface_bindings", [])
                if isinstance(revision_inputs, Mapping)
                else []
            ),
            parent_estimator_interface_authoring=(
                revision_inputs.get("parent_estimator_interface_authoring", {})
                if isinstance(revision_inputs, Mapping)
                else {}
            ),
        )


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



def build_theory_developer_prompt(
    question: OpenResearchQuestion,
    *,
    architect_context: Mapping[str, Any],
) -> str:
    theory_prompt_mode = _theory_developer_prompt_mode(architect_context)
    if theory_prompt_mode == THEORY_PROMPT_MODE_SERIOUS_REVISION:
        return _theory_workspace_revision_prompt(
            question=question,
            revision_inputs=build_theory_developer_revision_inputs(
                architect_context,
                question=question,
            ),
        )

    compact_context = _compact_architect_context_for_prompt(architect_context)
    serious_theory_mode = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
    transport_recovery = _theory_developer_transport_recovery(architect_context)
    formalization_authoring_required = (
        _theory_formalization_authoring_required(architect_context)
    )
    required_output_contract, handoff_requirements = (
        _theory_output_contract_for_question(
            THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT,
            question=question,
            formalization_authoring_required=formalization_authoring_required,
        )
    )
    if serious_theory_mode:
        prompt_mode = {
            "mode": theory_prompt_mode,
            "purpose": (
                "derive or revise a research-grade statistical procedure with a "
                "coherent equation chain, assumption audit, feasibility analysis, "
                "and critic pass to support independent downstream authoring"
            ),
            "do_not_expand_full_retrieval_or_architect_json": True,
        }
        output_budget_key = "serious_theory_output_budget"
        output_budget = {
            **(
                {
                    "max_derivation_steps": 5,
                    "max_equation_chain_steps": 4,
                    "max_sanity_checks": 3,
                    "max_candidate_procedures": 1,
                    "max_theorem_goals": 1,
                    "max_lemma_cards": 2,
                    "max_formalization_requests": (
                        1 if formalization_authoring_required else 0
                    ),
                    "max_critic_findings": 2,
                    "max_simulation_predictions": 2,
                    "max_next_actions": 1,
                    "max_string_chars": 320,
                }
                if transport_recovery
                else {
                    "row_count_policy": "model_selected_within_token_budget",
                    "per_field_row_caps": None,
                    "per_string_character_caps": None,
                }
            ),
            "transport_recovery": transport_recovery,
            "formalization_requests_required": bool(
                formalization_authoring_required
            ),
            "instruction": (
                (
                    "This is a transport recovery after a truncated response. "
                    "Return the minimum complete serious-theory handoff while "
                    "preserving every active mathematical obligation. "
                )
                if transport_recovery
                else (
                    "Use as many dependency-linked claims, equations, lemmas, "
                    "counterchecks, and alternatives as the argument needs within "
                    "the model token budget. The schema does not define research "
                    "quality through row counts or string lengths. "
                )
            ) + (
                "Return one complete valid JSON object. Build a coherent mathematical "
                "workspace at the level required by the question: derive claims from "
                "the stated setup and assumptions, link equations and lemmas by id, "
                "and independently check the claims most likely to invalidate the "
                "procedure. Keep the DGP, estimand, procedure, theorem, executable "
                "semantics and simulation plan mutually consistent. "
                + (
                    "Keep the formal target consistent with them. "
                    if formalization_authoring_required
                    else "Do not invent a formalization handoff for this task. "
                )
                + "When evidence is insufficient or a contradiction remains, record it "
                "as an unresolved critic finding instead of inventing certainty. Use "
                "only the rows the argument needs, state each definition or equation "
                "once, and refer to its id elsewhere. On a revision turn, use the "
                "supplied candidate and reviewer observations as evidence, reconsider "
                "the approach freely, and regenerate the entire packet."
            ),
        }
    else:
        prompt_mode = {
            "mode": THEORY_PROMPT_MODE_COMPACT,
            "purpose": "derive the core statistical object, procedure, theorem goals, and proof obligations without replaying full retrieval artifacts",
            "do_not_expand_full_retrieval_or_architect_json": True,
        }
        output_budget_key = "concise_output_budget"
        output_budget = {
            "max_derivation_steps": 5,
            "max_equation_chain_steps": 5,
            "max_sanity_checks": 3,
            "max_candidate_procedures": 1,
            "max_theorem_goals": 1,
            "max_lemma_cards": 1,
            "max_formalization_requests": (
                1 if formalization_authoring_required else 0
            ),
            "max_critic_findings": 1,
            "max_simulation_predictions": 1,
            "max_next_actions": 1,
            "max_string_chars": 180,
            "instruction": (
                "Return a complete valid JSON object within this budget. Author one "
                "primary estimator and theorem target. "
                + (
                    "Author one formalization request. "
                    if formalization_authoring_required
                    else "Leave formalization artifacts empty. "
                )
                + "Choose "
                "the number of derivation, equation, lemma, sanity-check, critic, and "
                "action rows from the argument itself; optional lists may be empty. "
                "Keep every string one sentence or one equation fragment. Do not "
                "include essays, tables, Markdown, or long simulation instructions."
            ),
        }
    payload = {
        "question": research_question_payload(
            question,
            include_task_intent=True,
        ),
        "prompt_mode": prompt_mode,
        "architect_context": compact_context,
        "required_output_contract": required_output_contract,
        "structured_handoff_requirements": handoff_requirements,
        output_budget_key: output_budget,
        "proof_boundary": KERNEL_PROOF_BOUNDARY,
    }
    serious_mode_label = (
        "upstream-theory revision"
        if theory_prompt_mode == THEORY_PROMPT_MODE_SERIOUS_REVISION
        else "capability-theory pass"
    )
    mode_instruction = (
        f"This is a serious {serious_mode_label}: produce a rigorous equation and "
        "lemma dependency trace, audit assumptions, and preserve every active "
        "review observation. Choose the number and organization of mathematical "
        "objects from the argument itself; row counts are not a quality metric."
        if serious_theory_mode
        else "This is a focused first-pass discovery packet with one primary "
        "procedure and theorem target. Choose all supporting "
        "row counts from the argument; counts are not a quality metric."
    )
    return (
        "Derive statistical theory artifacts for the Architect loop. Return ONLY one "
        "JSON object matching required_output_contract. You own all mathematical "
        "content and may change the approach when observations warrant it; the runtime "
        "does not provide issue-specific corrections. State the setup and assumptions, "
        "give an explicit dependency-linked derivation, define the procedure, expose "
        "uncertainty, and align the theorem, simulation, executable, and formalization "
        "handoffs. Use retrieved declarations as context, never as proof evidence. Do "
        "not emit estimator_interface_contract in this core phase; the same "
        "TheoryDeveloper authors the bounded interface after the core packet is frozen. "
        "Do not claim Lean or kernel verification. Check the output contract before "
        "returning and avoid repeating content across fields. "
        + mode_instruction
        + " Keep the packet within its declared budget and finish as one valid JSON "
        "object; do not trade JSON completeness for detail.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


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
    if (
        isinstance(evidence_contract, Mapping)
        and evidence_contract.get("evaluation_mode")
        in {"research_eval", "capability_eval"}
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


def _theory_developer_transport_recovery(
    architect_context: Mapping[str, Any],
) -> bool:
    feedback = architect_context.get("environment_feedback", {})
    return bool(
        isinstance(feedback, Mapping)
        and feedback.get("artifact_kind")
        == "RuntimeTheoryDeveloperValidationFeedback"
        and feedback.get("truncation_detected") is True
    )


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
        "proof_evidence_status": (
            "THEORY_PROGRESS_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }


def _theory_developer_recovered_core_checkpoint(
    architect_context: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    theory_prompt_mode: str,
) -> dict[str, Any] | None:
    """Resume interface authoring from one validator-bound completed core phase."""

    feedback = architect_context.get("environment_feedback", {})
    checkpoint = (
        feedback.get("recovery_checkpoint", {})
        if isinstance(feedback, Mapping)
        and feedback.get("artifact_kind")
        == "RuntimeTheoryDeveloperValidationFeedback"
        else {}
    )
    if not isinstance(checkpoint, Mapping) or not checkpoint:
        return None

    errors: list[str] = []
    if checkpoint.get("artifact_kind") != THEORY_DEVELOPER_STAGE_CHECKPOINT_KIND:
        errors.append("TheoryDeveloper recovery checkpoint has the wrong artifact kind")
    if checkpoint.get("failed_phase") != "estimator_interface_authoring":
        errors.append("TheoryDeveloper recovery checkpoint is not for interface authoring")
    if str(checkpoint.get("question_id", "") or "") != question.id:
        errors.append("TheoryDeveloper recovery checkpoint belongs to another question")
    if checkpoint.get("kernel_verified") is not False:
        errors.append("TheoryDeveloper recovery checkpoint must remain non-proof")

    raw_core_packet = checkpoint.get("validated_core_packet", {})
    core_packet = (
        deepcopy(dict(raw_core_packet))
        if isinstance(raw_core_packet, Mapping)
        else {}
    )
    if not core_packet:
        errors.append("TheoryDeveloper recovery checkpoint has no completed core packet")
    expected_fingerprint = str(
        checkpoint.get("validated_core_packet_fingerprint", "") or ""
    )
    actual_fingerprint = stable_hash(core_packet) if core_packet else ""
    if not expected_fingerprint or expected_fingerprint != actual_fingerprint:
        errors.append("TheoryDeveloper recovery checkpoint fingerprint does not match")
    if core_packet:
        errors.extend(validate_theory_core_packet(core_packet))

    if theory_prompt_mode == THEORY_PROMPT_MODE_SERIOUS_REVISION and core_packet:
        revision_inputs = build_theory_developer_revision_inputs(
            architect_context,
            question=question,
        )
        transport = core_packet.get("theory_revision_transport", {})
        if not isinstance(transport, Mapping) or not transport:
            errors.append("recovered targeted core has no revision transport lineage")
        else:
            if transport.get("source_theory_packet_id") != revision_inputs.get(
                "source_theory_packet_id"
            ):
                errors.append("recovered targeted core parent packet id changed")
            if transport.get("source_theory_packet_hash") != revision_inputs.get(
                "source_theory_packet_hash"
            ):
                errors.append("recovered targeted core parent packet hash changed")
            if transport.get("feedback_id") != revision_inputs.get("feedback_id"):
                errors.append("recovered targeted core feedback lineage changed")
            if transport.get("revision_binding_id") != revision_inputs.get(
                "revision_binding_id"
            ):
                errors.append("recovered targeted core revision binding changed")

    if errors:
        raise PacketValidationError(
            validation_label="TheoryDeveloper stage recovery checkpoint",
            attempts=0,
            errors=list(dict.fromkeys(errors)),
            history=[],
        )
    return core_packet


def _theory_developer_serious_mode(
    architect_context: Mapping[str, Any],
) -> bool:
    return (
        _theory_developer_prompt_mode(architect_context)
        in THEORY_SERIOUS_PROMPT_MODES
    )


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

    environment_feedback = context.get("environment_feedback")
    if isinstance(environment_feedback, Mapping):
        compact["environment_feedback"] = _compact_environment_feedback_for_prompt(environment_feedback)

    source_environment_feedback = context.get(
        "theory_developer_source_environment_feedback"
    )
    if isinstance(source_environment_feedback, Mapping) and source_environment_feedback:
        compact["theory_developer_source_environment_feedback"] = (
            _compact_environment_feedback_for_prompt(source_environment_feedback)
        )

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
            keys=("stop_conditions", "max_revision_rounds"),
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


def _compact_prompt_rows(
    rows: Any,
    *,
    keys: tuple[str, ...],
    limit: int,
    list_limit: int,
    text_limit: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, (list, tuple)):
        return []
    return [
        _compact_prompt_mapping(row, keys=keys, list_limit=list_limit, text_limit=text_limit)
        if isinstance(row, Mapping)
        else {"summary": _truncate_text(row, text_limit)}
        for row in list(rows)[:limit]
    ]


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


def _compact_environment_feedback_for_prompt(feedback: Mapping[str, Any]) -> dict[str, Any]:
    feedback = model_observations_without_repair_recipes(feedback)
    high_priority_agenda = list(feedback.get("high_priority_agenda", []) or [])
    formal_subclaims = list(feedback.get("formal_subclaim_feedback", []) or [])
    failed_simulations = list(feedback.get("failed_simulations", []) or [])
    implementation_gaps = list(feedback.get("implementation_gaps", []) or [])
    rejected_candidate = feedback.get("rejected_candidate", {})
    compact = {
        "artifact_kind": feedback.get("artifact_kind", ""),
        "feedback_id": feedback.get("feedback_id", ""),
        "feedback_source": feedback.get("feedback_source", ""),
        "feedback_type": feedback.get("feedback_type", ""),
        "trigger": feedback.get("trigger", ""),
        "failure_classification": feedback.get("failure_classification", ""),
        "failure_classifications": _compact_learning_memory_value(
            feedback.get("failure_classifications", [])
        ),
        "validation_errors": _compact_learning_memory_value(
            feedback.get("validation_errors", [])
        ),
        "rejected_candidate": (
            deepcopy(dict(rejected_candidate))
            if isinstance(rejected_candidate, Mapping)
            else {}
        ),
        "rejected_candidate_fingerprint": feedback.get(
            "rejected_candidate_fingerprint", ""
        ),
        "retry_mode": feedback.get("retry_mode", ""),
        "truncation_detected": feedback.get("truncation_detected", ""),
        "question_id": feedback.get("question_id", ""),
        "source_task_id": feedback.get("source_task_id", ""),
        "source_owner_subsystem": feedback.get("source_owner_subsystem", ""),
        "source_theory_packet_id": feedback.get("source_theory_packet_id", ""),
        "source_theory_packet_hash": feedback.get("source_theory_packet_hash", ""),
        "source_metric_protocol_rejection_manifest_id": feedback.get(
            "source_metric_protocol_rejection_manifest_id", ""
        ),
        "target_consumer_subsystem": feedback.get("target_consumer_subsystem", ""),
        "ownership_clarification_required": feedback.get(
            "ownership_clarification_required", ""
        ),
        "upstream_theory_revision_count": feedback.get(
            "upstream_theory_revision_count", ""
        ),
        "continuation_budget_authority": feedback.get(
            "continuation_budget_authority", ""
        ),
        "critic_revision_round": feedback.get("critic_revision_round", ""),
        "next_critic_revision_round": feedback.get("next_critic_revision_round", ""),
        "max_critic_revision_rounds": feedback.get("max_critic_revision_rounds", ""),
        "theory_packet_id": feedback.get("theory_packet_id", ""),
        "simulation_manifest_id": feedback.get("simulation_manifest_id", ""),
        "formalization_manifest_id": feedback.get("formalization_manifest_id", ""),
        "formalization_counts": feedback.get("formalization_counts", {}),
        "simulation_passed": feedback.get("simulation_passed", ""),
        "high_priority_agenda": [_compact_feedback_row(row) for row in high_priority_agenda[:5]],
        "formal_subclaim_feedback": [_compact_feedback_row(row) for row in formal_subclaims[:8]],
        "failed_simulations": [_compact_feedback_row(row) for row in failed_simulations[:5]],
        "implementation_gaps": [_compact_feedback_row(row) for row in implementation_gaps[:5]],
        "acceptance_gate": _truncate_text(feedback.get("acceptance_gate", ""), 720),
        "proof_evidence_status": _truncate_text(
            feedback.get("proof_evidence_status", ""), 240
        ),
        "proof_evidence_boundary": _truncate_text(feedback.get("proof_evidence_boundary", ""), 400),
        "boundary": _truncate_text(feedback.get("boundary", ""), 400),
    }
    metric_protocol_findings = feedback.get("findings", [])
    if isinstance(metric_protocol_findings, list) and metric_protocol_findings:
        compact["metric_protocol_findings"] = [
            _compact_feedback_row(row) for row in metric_protocol_findings[:8]
        ]
    metric_protocol_dimension_reviews = feedback.get("dimension_reviews", [])
    if (
        isinstance(metric_protocol_dimension_reviews, list)
        and metric_protocol_dimension_reviews
    ):
        compact["metric_protocol_dimension_reviews"] = [
            _compact_feedback_row(row)
            for row in metric_protocol_dimension_reviews[:8]
        ]
    theory_alignment_feedback = feedback.get("theory_trace_downstream_alignment_feedback")
    if isinstance(theory_alignment_feedback, Mapping) and theory_alignment_feedback:
        compact["theory_trace_downstream_alignment_feedback"] = _compact_feedback_row(
            theory_alignment_feedback
        )
    theory_alignment_contract = feedback.get("theory_trace_downstream_alignment_contract")
    if isinstance(theory_alignment_contract, Mapping) and theory_alignment_contract:
        compact["theory_trace_downstream_alignment_contract"] = _compact_feedback_row(
            theory_alignment_contract
        )
    formal_blocker_resource_requests = feedback.get("formal_blocker_resource_requests")
    has_exact_semantic_blocker_rows = (
        isinstance(formal_blocker_resource_requests, (list, tuple))
        and bool(formal_blocker_resource_requests)
    )
    if has_exact_semantic_blocker_rows:
        compact["formal_blocker_resource_requests"] = (
            _compact_exact_semantic_feedback_rows(formal_blocker_resource_requests)
        )
    for exact_semantic_feedback_key in (
        "source_theorem_exact_semantic_definition_repair_feedback",
        "runtime_exact_semantic_definition_work_order_feedback",
        "source_theorem_exact_semantic_definition_work_order_feedback",
    ):
        exact_semantic_feedback = feedback.get(exact_semantic_feedback_key)
        if isinstance(exact_semantic_feedback, Mapping) and exact_semantic_feedback:
            compact[exact_semantic_feedback_key] = (
                _compact_exact_semantic_feedback_mapping(
                    exact_semantic_feedback,
                    include_row_containers=not has_exact_semantic_blocker_rows,
                )
            )
    additional_feedback = feedback.get("additional_runtime_feedback", [])
    if isinstance(additional_feedback, list) and additional_feedback:
        compact["additional_runtime_feedback"] = [
            _compact_feedback_row(row) for row in additional_feedback[:4]
        ]
    return {
        key: value
        for key, value in compact.items()
        if value not in (None, "", [], {})
    }


def _compact_learning_memory_value(value: Any) -> Any:
    if isinstance(value, str):
        return _truncate_text(value, 320)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_compact_learning_memory_value(item) for item in value[:6]]
    if isinstance(value, Mapping):
        return {
            str(key): _compact_learning_memory_value(child)
            for key, child in list(value.items())[:6]
            if child not in (None, "", [], {})
        }
    return _truncate_text(value, 320)


_EXACT_SEMANTIC_FEEDBACK_MAPPING_KEYS = (
    "artifact_kind",
    "feedback_type",
    "trigger",
    "question_id",
    "source_task_id",
    "source_owner_subsystem",
    "target_consumer_subsystem",
    "target_theorem_name",
    "target_lean_declaration",
    "failure_classification",
    "acceptance_gate",
    "proof_body_gate_status",
    "proof_body_goal_reached",
    "source_theorem_kernel_verified",
    "source_theorem_kernel_evidence_eligible",
    "proof_evidence_status",
    "proof_evidence_boundary",
    "boundary",
)


_EXACT_SEMANTIC_FEEDBACK_ROW_KEYS = (
    "work_order_id",
    "repair_feedback_id",
    "diagnostic_id",
    "placeholder_symbol",
    "semantic_primitive_id",
    "target_theorem_name",
    "target_lean_declaration",
    "target_ids",
    "target_lane",
    "lane",
    "action_type",
    "request_type",
    "replacement_strategy",
    "search_targets",
    "semantic_primitives",
    "semantic_primitive_requirements",
    "failure_classification",
    "runtime_queue_status",
    "verification_status",
    "proof_body_gate_status",
    "proof_body_goal_reached",
    "candidate_artifact_path",
    "definition_only_candidate_artifact_path",
    "source_candidate_artifact_path",
    "adapter_candidate_artifact_path",
    "adapter_candidate_artifact_paths",
    "premise_candidate_artifact_path",
    "proof_body_candidate_artifact_path",
    "source_theorem_exact_semantic_definition_typechecked_candidate",
    "source_theorem_kernel_verified",
    "source_theorem_kernel_evidence_eligible",
    "proof_evidence_status",
    "boundary",
)


_EXACT_SEMANTIC_FEEDBACK_ROW_CONTAINER_KEYS = (
    "formal_blocker_resource_requests",
    "diagnostics",
    "work_orders",
    "rows",
    "source_theorem_exact_semantic_definition_typechecked_candidates",
)


def _prompt_key_is_path_like(key: Any) -> bool:
    key_text = str(key).lower()
    return (
        key_text.endswith("_path")
        or key_text.endswith("_paths")
        or key_text.endswith("_jsonl")
        or key_text.endswith("_manifest")
        or "artifact_path" in key_text
    )


def _compact_prompt_value_for_key(
    key: Any,
    value: Any,
    *,
    list_limit: int = 8,
    mapping_limit: int = 10,
    text_limit: int = 320,
    path_limit: int = 1024,
) -> Any:
    string_limit = path_limit if _prompt_key_is_path_like(key) else text_limit
    if isinstance(value, str):
        return _truncate_text(value, string_limit)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [
            _compact_prompt_value_for_key(
                key,
                item,
                list_limit=list_limit,
                mapping_limit=mapping_limit,
                text_limit=text_limit,
                path_limit=path_limit,
            )
            for item in value[:list_limit]
        ]
    if isinstance(value, Mapping):
        return {
            str(child_key): _compact_prompt_value_for_key(
                child_key,
                child_value,
                list_limit=list_limit,
                mapping_limit=mapping_limit,
                text_limit=text_limit,
                path_limit=path_limit,
            )
            for child_key, child_value in list(value.items())[:mapping_limit]
            if child_value not in (None, "", [], {})
        }
    return _truncate_text(value, string_limit)


def _compact_exact_semantic_feedback_mapping(
    value: Any,
    *,
    include_row_containers: bool = True,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    compact: dict[str, Any] = {}
    for key in _EXACT_SEMANTIC_FEEDBACK_MAPPING_KEYS:
        if value.get(key) not in (None, "", [], {}):
            compact[key] = _compact_prompt_value_for_key(key, value.get(key))
    if include_row_containers:
        for key in _EXACT_SEMANTIC_FEEDBACK_ROW_CONTAINER_KEYS:
            rows = value.get(key)
            if isinstance(rows, (list, tuple)) and rows:
                compact[key] = _compact_exact_semantic_feedback_rows(rows)
            elif isinstance(rows, Mapping) and rows:
                compact[key] = _compact_exact_semantic_feedback_row(rows)
    else:
        for key in _EXACT_SEMANTIC_FEEDBACK_ROW_CONTAINER_KEYS:
            rows = value.get(key)
            if isinstance(rows, (list, tuple)) and rows:
                compact[f"n_{key}"] = len(rows)
            elif isinstance(rows, Mapping) and rows:
                compact[f"{key}_present"] = True
    return {
        key: row_value
        for key, row_value in compact.items()
        if row_value not in (None, "", [], {})
    }


def _compact_exact_semantic_feedback_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, (list, tuple)):
        return []
    return [_compact_exact_semantic_feedback_row(row) for row in list(rows)[:6]]


def _compact_exact_semantic_feedback_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    compact: dict[str, Any] = {}
    for key in _EXACT_SEMANTIC_FEEDBACK_ROW_KEYS:
        if row.get(key) not in (None, "", [], {}):
            compact[key] = _compact_prompt_value_for_key(key, row.get(key))
    for key, value in row.items():
        key_text = str(key)
        if key_text in compact or value in (None, "", [], {}):
            continue
        if _prompt_key_is_path_like(key_text) or (
            "source_theorem_exact_semantic_definition" in key_text
        ):
            compact[key_text] = _compact_prompt_value_for_key(key_text, value)
    return compact


def _compact_feedback_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    compact: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            compact[str(key)] = _compact_prompt_value_for_key(key, value)
        elif isinstance(value, list):
            compact[str(key)] = [
                _compact_prompt_value_for_key(key, item)
                for item in value[:8]
            ]
        elif isinstance(value, Mapping):
            compact[str(key)] = {
                str(k): _compact_prompt_value_for_key(k, v)
                for k, v in list(value.items())[:10]
                if v not in (None, "", [], {})
            }
    return compact


def _truncate_text(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, (list, tuple)) else 0


THEORY_DEVELOPER_SYSTEM_PROMPT = """\
You are the LLM TheoryDeveloper inside an AI Statistician Architect.

Your job is research-level statistical theory development, not template
classification. Given an open research question, derive the mathematical setup,
estimand, procedure, theorem candidates, lemma DAG, proof plan, simulation
predictions, and formalization obligations. Use equation-level reasoning and
self-critique. Before offering a checkpoint, reread the central argument as a
skeptical referee: independently recompute pivotal identities, test the smallest
nontrivial and boundary cases, and verify that each implication uses only stated
assumptions. Correct defects you find or mark the claim unresolved; do not let a
plausible narrative substitute for a derivation. Preserve uncertainty and semantic
risks. Do not claim formal proof or Lean kernel verification.
"""


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

THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT = deepcopy(
    THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
)
THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT["estimator_specs"][0][
    "estimator_interface_contract"
] = deepcopy(
    THEORY_DEVELOPER_OUTPUT_CONTRACT["estimator_specs"][0][
        "estimator_interface_contract"
    ]
)
THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT["theory_derivation_packet"] = {
    "derivation_summary": (
        "short cross-agent summary; full mathematics lives in referenced documents"
    ),
    "claim_index": [
        {
            "id": "stable claim or equation id",
            "kind": "definition|assumption|lemma|theorem|equation|counterexample",
            "document_path": "workspace-relative .md or .tex path",
            "depends_on": ["direct predecessor claim_index ids"],
            "status": "OPEN|SUPPORTED|REJECTED|INCONCLUSIVE",
        }
    ],
    "sanity_check_index": [
        {
            "id": "stable check id",
            "claim_ref": "claim_index id",
            "document_path": "workspace-relative .md or .tex path",
            "status": "PASS|FAIL|INCONCLUSIVE",
        }
    ],
    "formalization_handoff": deepcopy(
        THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT["theory_derivation_packet"][
            "formalization_handoff"
        ]
    ),
    "self_critique": ["short unresolved-risk summary with claim IDs and document paths"],
    "rejected_alternatives": [
        {
            "name": "short id",
            "reason": "short summary with claim ID or document path",
        }
    ],
}


def _json_schema_from_output_contract(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        properties = {
            str(key): _json_schema_from_output_contract(item)
            for key, item in value.items()
        }
        return {
            "type": "object",
            "additionalProperties": False,
            "required": list(properties),
            "properties": properties,
        }
    if isinstance(value, list):
        item_contract = value[0] if value else "string"
        return {
            "type": "array",
            "items": _json_schema_from_output_contract(item_contract),
        }
    return {"type": "string"}


THEORY_DEVELOPER_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    **_json_schema_from_output_contract(THEORY_DEVELOPER_OUTPUT_CONTRACT),
}
THEORY_DEVELOPER_JSON_SCHEMA["properties"]["estimator_specs"]["items"][
    "properties"
]["estimator_interface_contract"] = estimator_interface_contract_json_schema()


def _theory_developer_json_schema(
    *,
    theory_prompt_mode: str,
    transport_recovery: bool = False,
    formalization_authoring_required: bool = True,
) -> dict[str, Any]:
    """Return the output contract with the prompt's size budget made explicit."""

    serious_theory_mode = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
    if serious_theory_mode:
        max_string_chars = 320 if transport_recovery else None
    else:
        max_string_chars = 180
    schema = _bounded_theory_schema_value(
        THEORY_DEVELOPER_JSON_SCHEMA,
        max_string_chars=max_string_chars,
        default_max_items=(
            12 if not serious_theory_mode or transport_recovery else None
        ),
    )
    properties = schema["properties"]
    derivation_schema = properties["theory_derivation_packet"]
    derivation = derivation_schema["properties"]

    unbounded_serious = serious_theory_mode and not transport_recovery
    if serious_theory_mode:
        derivation_step_bounds = (
            1,
            None if unbounded_serious else 5,
        )
        equation_chain_bounds = (
            1,
            None if unbounded_serious else 4,
        )
        sanity_check_bounds = (
            1,
            None if unbounded_serious else 3,
        )
        if unbounded_serious:
            top_level_maxima = dict.fromkeys(
                (
                    "estimator_specs",
                    "theorem_cards",
                    "lemma_cards",
                    "formalization_requests",
                    "critic_findings",
                    "next_actions",
                )
            )
        else:
            top_level_maxima = {
                "estimator_specs": 1,
                "theorem_cards": 1,
                "lemma_cards": 2,
                "formalization_requests": 1,
                "critic_findings": 2,
                "next_actions": 1,
            }
    else:
        derivation_step_bounds = (1, 5)
        equation_chain_bounds = (1, 5)
        sanity_check_bounds = (1, 3)
        top_level_maxima = {
            "estimator_specs": 1,
            "theorem_cards": 1,
            "lemma_cards": 1,
            "formalization_requests": 1,
            "critic_findings": 1,
            "next_actions": 1,
        }

    _set_theory_schema_array_bounds(
        derivation["derivation_steps"], *derivation_step_bounds
    )
    _set_theory_schema_array_bounds(
        derivation["equation_chain"], *equation_chain_bounds
    )
    _set_theory_schema_array_bounds(
        derivation["assumption_ledger"], 1, None if unbounded_serious else 10
    )
    _set_theory_schema_array_bounds(
        derivation["sanity_checks"], *sanity_check_bounds
    )
    _set_theory_schema_array_bounds(
        derivation["self_critique"], 1, None if unbounded_serious else 4
    )
    _set_theory_schema_array_bounds(
        derivation["rejected_alternatives"],
        0,
        None if unbounded_serious else 3,
    )
    optional_list_fields = {"lemma_cards", "critic_findings", "next_actions"}
    for field, maximum in top_level_maxima.items():
        _set_theory_schema_array_bounds(
            properties[field],
            (
                0
                if field in optional_list_fields
                or (
                    field == "formalization_requests"
                    and not formalization_authoring_required
                )
                else 1
            ),
            maximum,
        )
    if not formalization_authoring_required:
        derivation_schema["required"] = [
            field
            for field in derivation_schema.get("required", [])
            if field != "formalization_handoff"
        ]
    return schema


def _theory_developer_core_json_schema(
    *,
    theory_prompt_mode: str,
    transport_recovery: bool = False,
    formalization_authoring_required: bool = True,
) -> dict[str, Any]:
    """Return the bounded core-theory schema without executable interfaces."""

    schema = _theory_developer_json_schema(
        theory_prompt_mode=theory_prompt_mode,
        transport_recovery=transport_recovery,
        formalization_authoring_required=formalization_authoring_required,
    )
    estimator_item = schema["properties"]["estimator_specs"]["items"]
    estimator_item["properties"].pop("estimator_interface_contract", None)
    estimator_item["required"] = [
        field
        for field in estimator_item.get("required", [])
        if field != "estimator_interface_contract"
    ]
    return schema


def _bounded_theory_schema_value(
    value: Any,
    *,
    max_string_chars: int | None,
    default_max_items: int | None,
) -> Any:
    if isinstance(value, Mapping):
        bounded = {
            str(key): _bounded_theory_schema_value(
                child,
                max_string_chars=max_string_chars,
                default_max_items=default_max_items,
            )
            for key, child in value.items()
        }
        if bounded.get("type") == "string":
            bounded["minLength"] = 1
            if max_string_chars is not None:
                bounded["maxLength"] = max_string_chars
        elif bounded.get("type") == "array":
            if default_max_items is not None:
                bounded.setdefault("maxItems", default_max_items)
        return bounded
    if isinstance(value, list):
        return [
            _bounded_theory_schema_value(
                child,
                max_string_chars=max_string_chars,
                default_max_items=default_max_items,
            )
            for child in value
        ]
    return deepcopy(value)


def _set_theory_schema_array_bounds(
    schema: dict[str, Any],
    minimum: int,
    maximum: int | None,
) -> None:
    schema["minItems"] = max(0, int(minimum))
    if maximum is None:
        schema.pop("maxItems", None)
    else:
        schema["maxItems"] = max(schema["minItems"], int(maximum))


def validate_theory_packet(packet: Mapping[str, Any]) -> list[str]:
    return _validate_theory_packet(
        packet,
        require_estimator_interfaces=True,
    )


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
        if str(row.get("kind", "") or "") not in {
            "definition",
            "assumption",
            "lemma",
            "theorem",
            "equation",
            "counterexample",
        }:
            errors.append(f"claim_index[{index}] has invalid kind")
        if str(row.get("status", "") or "") not in {
            "OPEN",
            "SUPPORTED",
            "REJECTED",
            "INCONCLUSIVE",
        }:
            errors.append(f"claim_index[{index}] has invalid status")
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

    check_rows = derivation.get("sanity_check_index", [])
    if not isinstance(check_rows, list) or not check_rows:
        errors.append("theory_derivation_packet.sanity_check_index must be non-empty")
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
        if str(row.get("status", "") or "") not in {
            "PASS",
            "FAIL",
            "INCONCLUSIVE",
        }:
            errors.append(f"sanity_check_index[{index}] has invalid status")
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
    derivation_steps = derivation.get("derivation_steps", [])
    if not isinstance(derivation_steps, list) or not derivation_steps:
        errors.append(
            "theory_derivation_packet.derivation_steps must be a non-empty list"
        )
    else:
        for idx, row in enumerate(derivation_steps, start=1):
            if not isinstance(row, Mapping):
                errors.append(
                    "theory_derivation_packet.derivation_steps entries must be objects"
                )
                continue
            if not str(row.get("id", "")).strip():
                errors.append(f"derivation step {idx} missing id")
            if not str(row.get("claim", "")).strip():
                errors.append(f"derivation step {idx} missing claim")
            if not str(row.get("equation_or_argument", "")).strip():
                errors.append(f"derivation step {idx} missing equation_or_argument")
    equation_chain = derivation.get("equation_chain", [])
    if not isinstance(equation_chain, list) or not equation_chain:
        errors.append(
            "theory_derivation_packet.equation_chain must be a non-empty list"
        )
    else:
        for idx, row in enumerate(equation_chain, start=1):
            if not isinstance(row, Mapping):
                errors.append(
                    "theory_derivation_packet.equation_chain entries must be objects"
                )
                continue
            if not str(row.get("lhs", "")).strip() or not str(
                row.get("rhs", "")
            ).strip():
                errors.append(f"equation_chain row {idx} must include lhs and rhs")
            if not str(row.get("justification", "")).strip():
                errors.append(f"equation_chain row {idx} missing justification")
    assumption_ledger = derivation.get("assumption_ledger", [])
    if not isinstance(assumption_ledger, list) or not assumption_ledger:
        errors.append("theory_derivation_packet.assumption_ledger must be non-empty")
    else:
        for idx, row in enumerate(assumption_ledger, start=1):
            if not isinstance(row, Mapping):
                errors.append(
                    "theory_derivation_packet.assumption_ledger entries must be objects"
                )
                continue
            if not str(row.get("assumption", "")).strip():
                errors.append(f"assumption_ledger row {idx} missing assumption")
            if not row.get("used_in"):
                errors.append(f"assumption_ledger row {idx} missing used_in")
    sanity_checks = derivation.get("sanity_checks", [])
    if not isinstance(sanity_checks, list) or not sanity_checks:
        errors.append(
            "theory_derivation_packet.sanity_checks must be a non-empty list"
        )
    if isinstance(sanity_checks, list):
        for idx, row in enumerate(sanity_checks):
            if not isinstance(row, Mapping):
                errors.append(
                    f"theory_derivation_packet.sanity_checks[{idx}] must be an object"
                )
                continue
            missing_fields = [
                field
                for field in (
                    "id",
                    "claim_ref",
                    "check_type",
                    "recomputation",
                    "result",
                )
                if not str(row.get(field, "") or "").strip()
            ]
            if missing_fields:
                errors.append(
                    f"theory_derivation_packet.sanity_checks[{idx}] missing "
                    "required fields: " + ", ".join(missing_fields)
                )
    return errors


def _validate_theory_packet(
    packet: Mapping[str, Any],
    *,
    require_estimator_interfaces: bool,
) -> list[str]:
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
    document_authority = (
        packet.get("theory_content_authority")
        == THEORY_WORKSPACE_CONTENT_AUTHORITY
    )
    errors: list[str] = _output_contract_shape_errors(
        packet,
        THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT,
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
        elif (
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
    elif handoff_requirements.get("formalization_requests", False) and not formalization_requests:
        errors.append("formalization_requests must be a non-empty list")
    for list_field in ("lemma_cards", "critic_findings", "next_actions"):
        if not isinstance(packet.get(list_field), list):
            errors.append(f"{list_field} must be a list")
    allowed_derivation_refs = theory_semantic_reference_ids(packet)
    estimator_ids: list[str] = []
    for idx, row in enumerate(packet.get("estimator_specs", []) or []):
        if not isinstance(row, Mapping):
            errors.append("estimator_specs entries must be objects")
            continue
        for field in ("id", "name", "formula", "algorithm_sketch"):
            if not str(row.get(field, "") or "").strip():
                errors.append(f"estimator_specs[{idx}].{field} must be non-empty")
        estimator_id = str(row.get("id", "") or "").strip()
        if estimator_id:
            estimator_ids.append(estimator_id)
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
            "n_sanity_check_index_rows": _safe_len(
                derivation.get("sanity_check_index", [])
            ),
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
            isinstance(derivation.get("formalization_handoff", {}), Mapping)
            and derivation.get("formalization_handoff")
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
        for field in THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
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
    parent_estimator_interface_bindings: list[dict[str, Any]] = []
    raw_specs = base_core_payload.get("estimator_specs", [])
    if isinstance(raw_specs, list):
        workspace_specs: list[Any] = []
        for index, raw_spec in enumerate(raw_specs):
            if not isinstance(raw_spec, Mapping):
                errors.append(f"prior estimator_specs[{index}] must be an object")
                workspace_specs.append(deepcopy(raw_spec))
                continue
            workspace_spec = deepcopy(dict(raw_spec))
            interface_contract = workspace_spec.get(
                "estimator_interface_contract"
            )
            interface_contract_id = workspace_spec.pop(
                "estimator_interface_contract_id",
                None,
            )
            core_spec = deepcopy(workspace_spec)
            core_spec.pop("estimator_interface_contract", None)
            estimator_id = str(workspace_spec.get("id", "") or "").strip()
            if (
                estimator_id
                and isinstance(interface_contract, Mapping)
                and interface_contract
            ):
                parent_estimator_interface_bindings.append(
                    {
                        "estimator_id": estimator_id,
                        "core_spec_fingerprint": stable_hash(core_spec),
                        "estimator_interface_contract": deepcopy(
                            dict(interface_contract)
                        ),
                        "estimator_interface_contract_id": str(
                            interface_contract_id
                            or estimator_interface_contract_id(
                                interface_contract
                            )
                        ),
                    }
                )
            workspace_specs.append(workspace_spec)
        base_core_payload["estimator_specs"] = workspace_specs
    else:
        errors.append("prior estimator_specs must be a list")

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
        "base_core_payload": base_core_payload,
        "base_core_payload_fingerprint": stable_hash(base_core_payload),
        "parent_estimator_interface_bindings": (
            parent_estimator_interface_bindings
        ),
        "parent_estimator_interface_authoring": deepcopy(
            dict(semantic_material.get("estimator_interface_authoring", {}))
            if isinstance(
                semantic_material.get("estimator_interface_authoring", {}),
                Mapping,
            )
            else {}
        ),
    }


def _theory_workspace_read_only_observations(
    revision_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    feedback = revision_inputs.get("feedback", {})
    reviewer_observations = (
        model_observations_without_repair_recipes(feedback)
        if isinstance(feedback, Mapping)
        else {}
    )
    reviewer_observations = deepcopy(dict(reviewer_observations))
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
    if not research_dimension_requirements(question.task_intent):
        return tuple(
            field
            for field in THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
            if field in artifacts
        )
    requirements = theory_handoff_requirements(
        question,
        formalization_authoring_required=formalization_authoring_required,
    )
    selected = {
        field for field, required in requirements.items() if required
    }
    if requirements["theorem_cards"]:
        selected.add("lemma_cards")
    selected.update(
        field
        for field, value in artifacts.items()
        if value not in (None, "", [], {})
    )
    return tuple(
        field
        for field in THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT
        if field in artifacts and field in selected
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
            "optional_full_theory_checkpoint": required_output_contract,
        }
    else:
        output_contract = required_output_contract
    return {
        "initial_authoring_context": {
            "research_question": research_question_payload(
                question,
                include_task_intent=True,
            ),
            "architect_context": _compact_architect_context_for_prompt(
                architect_context
            ),
            "required_output_contract": output_contract,
            "authoring_policy": {
                "theory_prompt_mode": theory_prompt_mode,
                "serious_theory_mode": serious,
                "required_nonempty_structures": [
                    "model-authored Markdown/LaTeX mathematical documents",
                    "claim_index",
                    "sanity_check_index",
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
            "Complete the explicitly source-replication-only objective for question "
            f"{question.id!r} in the persistent research workspace. First read the "
            "single initial_authoring_context artifact and inspect the supplied sources. "
            "Run the immutable published source exactly once, inspect its raw stdout and "
            "stderr, and use your own statistical judgment to write a durable Markdown "
            "report covering source and environment identity, reproduced outputs, "
            "comparison, interpretation, and caveats. Record unresolved gaps honestly, "
            "then commit a source-replication checkpoint. You may continue into a full "
            "theory checkpoint when useful, but do not fabricate theory, estimator, "
            "simulation, formalization, or novelty fields. Runtime applies your exact "
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
        "initial_authoring_context remains available. "
        if continuing_from_progress
        else (
            "Author the initial TheoryDeveloper research workspace for the supplied "
            f"question {question.id!r} in mode {theory_prompt_mode!r}. First read the "
            "single initial_authoring_context artifact. "
        )
    )
    return (
        opening
        + "Then use your own statistical "
        "judgment to write durable Markdown/LaTeX mathematics and only the "
        "task-intent-required, shape-typed cross-agent handoff. The documents, "
        "not JSON rows, are the "
        "authority for definitions, assumptions, equation-by-equation derivations, "
        "counterexamples, and unresolved arguments. Use stable claim IDs and document "
        "paths in the compact claim_index and sanity_check_index. Headings and LaTeX "
        "labels may help readers navigate, but runtime does not parse or require any "
        "Markdown anchor syntax. Record only direct claim dependencies in "
        "claim_index.depends_on so "
        "the resulting graph remains reviewable; keep the mathematical argument in "
        "the documents rather than copying it into the index. You may edit a "
        "coherent subset and use the raw validator observation to complete or revise the "
        "workspace in the same model session. A successful partial write remains in "
        "the workspace even while the combined workspace is invalid, so edit only "
        "the still-empty or intentionally revised artifacts on the next call. You "
        f"have one shared budget of at most {max(1, int(max_tool_calls))} ordinary "
        "tool calls for reads, searches, writes, edits, and scratch actions; there "
        "is no separate read or write quota, so allocate those calls according to "
        "the mathematical work. Use write_theory_document(path, content) for one complete new or "
        "replacement Markdown/LaTeX/BibTeX document. Use edit_theory_document for a "
        "hash-bound local text edit, and use write_theory_workspace only for compact "
        "structured handoff values. Do not put document bodies in the structured "
        "handoff. Every accepted call is retained. Authoritative documents must "
        "separate the argument you currently endorse from exploration: remove false "
        "or abandoned intermediate claims, or mark them explicitly as rejected so "
        "they cannot read as proof steps or support the claim index. Derive "
        "definitions and claims rather "
        "than treating retrieval as an answer key. Keep assumptions, equations, "
        "every authored downstream handoff mutually consistent. Treat IDs and document "
        "paths as exact references. When estimator_specs is required, author its exact "
        "executable estimator_interface_contract in this same workspace session; the "
        "runtime validates its shape and claim references but does not translate or "
        "rewrite it. The required compact handoffs are: "
        + required_handoffs
        + ". Handoffs not required by this task intent may remain empty: "
        + optional_handoffs
        + ". Do not copy a "
        "long derivation back into JSON; structured fields are only a compact index, "
        "ABI, and handoff. Any Python or R scratchpad result is an exploratory "
        "diagnostic tied to its exact observation, never a confirmatory result, frozen "
        "acceptance gate, theorem validation, or license to choose a favorable "
        "threshold. Confirmatory evidence belongs to the later independently reviewed "
        "and pre-outcome-frozen simulation lane. "
        + (
            "The formalization handoff and every formalization request must name an "
            "existing theorem-card ID. "
            if formalization_authoring_required
            else "Formalization is not requested for this task: leave "
            "formalization_requests empty and omit formalization_handoff rather than "
            "inventing Lean work. "
        )
        + "Record "
        "uncertainty explicitly. A failed scratch execution is diagnostic only; do "
        "not promote guessed or model-computed numbers from it into observed results. "
        "Keep PASS, FAIL, and INCONCLUSIVE sanity-check outcomes explicit. A failed "
        "check may guide exploratory work, but it cannot support confirmatory "
        "acceptance; revise the affected theory or report a grounded theory gap. "
        "Do not claim execution, Lean "
        "proof, or kernel verification. The runtime applies only your exact edits and "
        "will not choose, fill, or rewrite any substantive field."
    )


def _theory_workspace_revision_prompt(
    *,
    question: OpenResearchQuestion,
    revision_inputs: Mapping[str, Any],
    continuing_from_progress: bool = False,
) -> str:
    read_only_observations = _theory_workspace_read_only_observations(
        revision_inputs
    )
    reviewer_observations = read_only_observations["reviewer_observations"]
    payload: dict[str, Any] = {
        "question": research_question_payload(question),
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
            "n_findings": len(reviewer_observations.get("findings", []) or []),
        },
        "workspace_artifacts": list(THEORY_DEVELOPER_FILE_HANDOFF_CONTRACT),
        "instructions": [
            (
                "First read prior_theory_progress_checkpoint, inspect its exact next "
                "step, then read only the current documents and handoff artifacts "
                "needed to continue the same revision lineage."
                if continuing_from_progress
                else (
                    "First read reviewer_observations by itself. Do not request every "
                    "workspace artifact in one read. After identifying the actual "
                    "failed claim or execution behavior, read only the parent "
                    "artifacts needed for that mathematical decision."
                )
            ),
            (
                "Reviewer observations remain available as the independent source of "
                "the revision request; inspect them when the continued next step "
                "depends on the original finding."
                if continuing_from_progress
                else "Keep the inspected reviewer finding bound to this revision."
            ),
            (
                "Use your own statistical judgment. Reviewer observations identify "
                "possible defects and are not an answer key or repair recipe."
            ),
            (
                "Use write_theory_document for one complete new or replacement "
                "Markdown/LaTeX/BibTeX file, edit_theory_document for a hash-bound "
                "local text edit, and write_theory_workspace only for compact "
                "structured handoff values whose semantics you choose to change. "
                "Never place document bodies in the structured handoff. Unsubmitted "
                "material remains byte-identical."
            ),
            (
                "Propagate each chosen revision through the authoritative documents and "
                "all dependent estimator/theorem indices, simulation predictions, and "
                "formalization requests that need to change. A self-critique, status "
                "label, critic finding, or next action does not override contradictory "
                "mathematics; rewrite every affected document before submitting."
            ),
            (
                "The estimator interface contract is part of estimator_specs in this "
                "same workspace. When estimator semantics or outputs change, inspect and "
                "revise that executable ABI yourself; when they do not change, preserve "
                "the parent value exactly. Runtime validates shape and claim references "
                "but never authors the interface."
            ),
            (
                "Keep only the current endorsed argument as authoritative mathematics. "
                "Delete abandoned or false intermediate claims, or label them "
                "explicitly as rejected so they cannot be read as proof steps or "
                "support a claim-index entry."
            ),
            (
                "Recompute every affected sanity check and preserve PASS, FAIL, or "
                "INCONCLUSIVE honestly. Do not relabel a failed calculation; use it as "
                "exploratory evidence, revise the mathematics, or report a theory gap."
            ),
            (
                "A scratch execution with a failed status or nonempty errors is "
                "diagnostic only. Do not promote guessed or model-computed numbers "
                "from it into observed results or empirical evidence."
            ),
            (
                "A successful Python or R scratch observation is also exploratory. It "
                "may falsify or motivate theory, but it cannot be relabeled "
                "confirmatory, choose an acceptance threshold after outcomes, or "
                "validate a theorem."
            ),
            (
                "Keep unresolved concerns explicit. Do not claim execution, observed "
                "simulation results, Lean proof, or kernel verification."
            ),
            (
                "The runtime stores your artifact values unchanged and performs only "
                "identity, budget, lineage, and schema validation. Independent review "
                "owns acceptance."
            ),
        ],
        "proof_boundary": KERNEL_PROOF_BOUNDARY,
    }
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
        for field in THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
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
    require_workspace_edit_evidence: bool = False,
) -> list[str]:
    errors = validate_theory_packet(packet)
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
        for field in THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
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
            "n_sanity_check_index_rows": _safe_len(
                packet.get("theory_derivation_packet", {}).get(
                    "sanity_check_index", []
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
        read_only_artifacts=read_only_artifacts,
        build_candidate=build_candidate,
        validate_candidate=validate_theory_packet,
        scratchpad=theory_scratchpad,
        research_sources=research_sources,
        research_source_discovery=research_source_discovery,
        research_source_execution=research_source_execution,
        allow_source_replication_checkpoint=allow_source_checkpoint,
        task_intent=question.task_intent,
        workspace_dir=workspace_dir,
        require_document_authority=True,
        writable_artifact_names=_theory_workspace_writable_handoff_names(
            question=question,
            formalization_authoring_required=(
                formalization_authoring_required
            ),
            artifacts=initial_artifacts,
        ),
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
        prior_client_tool_session_ref=(
            progress_checkpoint.get("client_tool_session_ref", {})
            if progress_checkpoint
            else None
        ),
        request_metadata={
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
    errors = validate_theory_packet(packet)
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
            "n_sanity_check_index_rows": _safe_len(
                packet.get("theory_derivation_packet", {}).get(
                    "sanity_check_index", []
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
        build_candidate=build_candidate,
        validate_candidate=lambda packet: (
            _validate_theory_workspace_revision_packet(
                packet,
                revision_inputs=revision_inputs,
                workspace_id=workspace_id,
            )
        ),
        scratchpad=theory_scratchpad,
        research_sources=research_sources,
        research_source_discovery=research_source_discovery,
        research_source_execution=research_source_execution,
        workspace_dir=workspace_dir,
        require_document_authority=True,
        writable_artifact_names=_theory_workspace_writable_handoff_names(
            question=question,
            formalization_authoring_required=(
                formalization_authoring_required
            ),
            artifacts=initial_artifacts,
        ),
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
        prior_client_tool_session_ref=(
            parent_client_tool_session_ref or None
        ),
        request_metadata={
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


THEORY_ESTIMATOR_INTERFACE_SYSTEM_PROMPT = """\
You are the interface-authoring phase of the AI Statistician TheoryDeveloper.

The core mathematical workspace is frozen. Translate each frozen estimator into
one typed request/response contract. Do not revise the estimand, formula,
algorithm, assumptions, theorem, or derivation. Every response normalization must
cite an exact semantic id supplied in the prompt. This
artifact is an executable handoff specification, not proof evidence. Preserve
the frozen outputs exactly: do not invent status, unavailable, diagnostic, or
resource fields that the core theory did not declare. Runtime owns operational
execution status. Mathematical rates and asymptotic claims remain authoritative
only in the frozen Markdown/LaTeX workspace; do not duplicate them in this ABI.
The runtime validates shape and references but never interprets mathematics.
"""


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


def _reusable_parent_estimator_interfaces(
    core_packet: Mapping[str, Any],
    parent_bindings: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return exact parent ABIs only when every estimator core is unchanged."""

    expected_ids = _theory_estimator_ids(core_packet)
    bindings_by_id = {
        str(row.get("estimator_id", "") or "").strip(): row
        for row in parent_bindings
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "").strip()
    }
    if not expected_ids or set(bindings_by_id) != set(expected_ids):
        return {}

    allowed_refs = theory_semantic_reference_ids(core_packet)
    reusable: dict[str, dict[str, Any]] = {}
    for raw_spec in core_packet.get("estimator_specs", []) or []:
        if not isinstance(raw_spec, Mapping):
            return {}
        spec = deepcopy(dict(raw_spec))
        spec.pop("estimator_interface_contract", None)
        spec.pop("estimator_interface_contract_id", None)
        estimator_id = str(spec.get("id", "") or "").strip()
        binding = bindings_by_id.get(estimator_id, {})
        if str(binding.get("core_spec_fingerprint", "") or "") != stable_hash(
            spec
        ):
            return {}
        contract = binding.get("estimator_interface_contract", {})
        if not isinstance(contract, Mapping) or not contract:
            return {}
        contract = deepcopy(dict(contract))
        if str(
            binding.get("estimator_interface_contract_id", "") or ""
        ) != estimator_interface_contract_id(contract):
            return {}
        if estimator_interface_contract_errors(
            contract,
            label=f"estimator_specs[{estimator_id!r}].estimator_interface_contract",
            required=True,
            allowed_derivation_refs=allowed_refs,
        ):
            return {}
        if contract != project_executable_estimator_interface_contract(
            contract
        ):
            return {}
        expected_outputs = spec.get("outputs", [])
        response_fields = contract.get("response_fields", [])
        if (
            isinstance(expected_outputs, list)
            and expected_outputs
            and (
                not isinstance(response_fields, list)
                or len(response_fields) != len(expected_outputs)
            )
        ):
            return {}
        reusable[estimator_id] = contract
    return reusable


def _theory_core_generation_phase_record(
    core_packet: Mapping[str, Any],
) -> dict[str, Any]:
    phase: dict[str, Any] = {
        "phase": _theory_core_generation_phase(core_packet),
        "model": str(core_packet.get("model", "")),
        "model_tier": str(core_packet.get("model_tier", "")),
        "structured_output_retry_attempts": core_packet.get(
            "structured_output_retry_attempts", 0
        ),
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


def _complete_theory_estimator_interfaces(
    core_packet: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    provider: GeneratorBackend,
    provider_name: str,
    request_model: str,
    model_tier: str,
    temperature: float,
    max_tokens: int,
    max_validation_retries: int,
    use_provider_structured_output: bool,
    parent_estimator_interface_bindings: Sequence[Mapping[str, Any]] = (),
    parent_estimator_interface_authoring: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Author bounded executable interfaces after core theory is frozen."""

    reusable_interfaces = _reusable_parent_estimator_interfaces(
        core_packet,
        parent_estimator_interface_bindings,
    )
    if reusable_interfaces:
        merged = deepcopy(dict(core_packet))
        merged_specs: list[Any] = []
        for raw_spec in merged.get("estimator_specs", []) or []:
            if not isinstance(raw_spec, Mapping):
                merged_specs.append(raw_spec)
                continue
            spec = dict(raw_spec)
            estimator_id = str(spec.get("id", "") or "").strip()
            spec["estimator_interface_contract"] = deepcopy(
                reusable_interfaces[estimator_id]
            )
            spec.pop("estimator_interface_contract_id", None)
            merged_specs.append(spec)
        merged["estimator_specs"] = merged_specs
        normalize_theory_estimator_interface_contracts(merged)
        parent_authoring = (
            dict(parent_estimator_interface_authoring)
            if isinstance(parent_estimator_interface_authoring, Mapping)
            else {}
        )
        parent_packet_id = str(
            (
                core_packet.get("theory_revision_transport", {})
                if isinstance(
                    core_packet.get("theory_revision_transport", {}), Mapping
                )
                else {}
            ).get("source_theory_packet_id", "")
            or ""
        )
        reuse_identity = {
            "source_theory_packet_id": str(core_packet.get("packet_id", "")),
            "parent_theory_packet_id": parent_packet_id,
            "interface_contract_ids": {
                estimator_id: estimator_interface_contract_id(contract)
                for estimator_id, contract in reusable_interfaces.items()
            },
        }
        merged["estimator_interface_authoring"] = {
            "artifact_kind": "TheoryEstimatorInterfaceReuseRecord",
            "artifact_id": (
                "theory_estimator_interfaces_reuse:"
                + stable_hash(reuse_identity)[:24]
            ),
            **reuse_identity,
            "provider": str(parent_authoring.get("provider", "") or ""),
            "model": str(parent_authoring.get("model", "") or ""),
            "model_tier": str(parent_authoring.get("model_tier", "") or ""),
            "n_interfaces": len(reusable_interfaces),
            "n_interfaces_reused": len(reusable_interfaces),
            "model_call_used": False,
            "runtime_edited_interfaces": False,
            "reuse_basis": "exact_unchanged_estimator_core_fingerprints",
            "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
            "kernel_verified": False,
        }
        merged["theory_generation_phases"] = [
            _theory_core_generation_phase_record(core_packet),
            {
                "phase": "estimator_interface_reuse",
                "model": str(parent_authoring.get("model", "") or ""),
                "model_tier": str(
                    parent_authoring.get("model_tier", "") or ""
                ),
                "model_call_used": False,
                "n_interfaces_reused": len(reusable_interfaces),
            },
        ]
        _refresh_theory_packet_id(merged, question=question)
        errors = validate_theory_packet(merged)
        if errors:
            raise PacketValidationError(
                validation_label="reused TheoryDeveloper estimator interfaces",
                attempts=0,
                errors=errors,
                history=[],
                last_invalid_packet=merged,
            )
        merged["validation_errors"] = []
        merged["ok"] = True
        return merged

    interface_schema = _theory_estimator_interface_authoring_json_schema(
        core_packet
    )
    request = GeneratorRequest(
        system_prompt=THEORY_ESTIMATOR_INTERFACE_SYSTEM_PROMPT,
        user_prompt=_theory_estimator_interface_authoring_prompt(core_packet),
        model=request_model,
        max_tokens=min(max_tokens, 8000),
        temperature=temperature,
        schema=interface_schema,
        metadata={
            "subsystem": "TheoryDeveloper",
            "agent": "LLMTheoryDeveloperAgent",
            "theory_developer_phase": "estimator_interface_authoring",
            "provider_name": provider_name,
            "model_tier": model_tier,
            "resolved_model": request_model,
            "source_theory_packet_id": str(core_packet.get("packet_id", "")),
            **(
                {"provider_structured_output": True}
                if use_provider_structured_output
                else {}
            ),
        },
    )

    def build_packet(
        raw_payload: Mapping[str, Any],
        response: Any,
        raw_text: str,
    ) -> dict[str, Any]:
        raw_interfaces = raw_payload.get("interfaces", [])
        interfaces = _canonical_theory_estimator_interface_rows(
            raw_interfaces,
            estimator_ids=_theory_estimator_ids(core_packet),
        )
        body = {
            "source_theory_packet_id": str(core_packet.get("packet_id", "")),
            "interfaces": interfaces,
            "interface_transport_shape": (
                "exact_key_object"
                if isinstance(raw_interfaces, Mapping)
                else "invalid_non_object"
            ),
            "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
            "kernel_verified": False,
        }
        artifact_id = stable_hash(
            {
                "provider": provider_name,
                "model": response.model or request_model,
                "model_tier": model_tier,
                "body": body,
            }
        )[:24]
        return {
            "schema_version": ARCHITECT_SCHEMA_VERSION,
            "artifact_kind": "TheoryEstimatorInterfaceAuthoringPacket",
            "artifact_id": f"theory_estimator_interfaces:{artifact_id}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_agent": "LLMTheoryDeveloperAgent",
            "provider": provider_name or response.provider,
            "model": response.model or request_model,
            "model_tier": model_tier,
            "raw_response_fingerprint": stable_hash(raw_text),
            **body,
        }

    try:
        interface_packet = generate_validated_json_packet(
            provider=provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=lambda packet: (
                _validate_theory_estimator_interface_authoring_packet(
                    packet,
                    core_packet=core_packet,
                )
            ),
            validation_label="LLM TheoryDeveloper estimator interface packet",
            max_validation_retries=min(max(0, max_validation_retries), 1),
        )
    except PacketValidationError as exc:
        completed_phase = _theory_core_generation_phase(core_packet)
        checkpoint = {
            "schema_version": ARCHITECT_SCHEMA_VERSION,
            "artifact_kind": THEORY_DEVELOPER_STAGE_CHECKPOINT_KIND,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question_id": question.id,
            "completed_phase": completed_phase,
            "failed_phase": "estimator_interface_authoring",
            "validated_core_packet_fingerprint": (
                stable_hash(core_packet)
            ),
            "validated_core_packet": deepcopy(dict(core_packet)),
            "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
            "kernel_verified": False,
            "boundary": (
                "This checkpoint preserves a locally validated TheoryDeveloper core "
                "for bounded interface-stage recovery. It is not execution, review "
                "acceptance, or theorem proof evidence."
            ),
        }
        raise PacketValidationError(
            validation_label=exc.validation_label,
            attempts=exc.attempts,
            errors=exc.errors,
            history=exc.history,
            last_invalid_packet=exc.last_invalid_packet,
            recovery_checkpoint=checkpoint,
        ) from exc
    merged = deepcopy(dict(core_packet))
    authored_by_id = {
        str(row.get("estimator_id", "") or "").strip(): deepcopy(
            row.get("estimator_interface_contract", {})
        )
        for row in interface_packet.get("interfaces", []) or []
        if isinstance(row, Mapping)
    }
    merged_specs: list[Any] = []
    for raw_spec in merged.get("estimator_specs", []) or []:
        if not isinstance(raw_spec, Mapping):
            merged_specs.append(raw_spec)
            continue
        spec = dict(raw_spec)
        estimator_id = str(spec.get("id", "") or "").strip()
        spec["estimator_interface_contract"] = deepcopy(
            authored_by_id[estimator_id]
        )
        spec.pop("estimator_interface_contract_id", None)
        merged_specs.append(spec)
    merged["estimator_specs"] = merged_specs
    normalize_theory_estimator_interface_contracts(merged)
    merged["estimator_interface_authoring"] = {
        "artifact_kind": interface_packet["artifact_kind"],
        "artifact_id": interface_packet["artifact_id"],
        "source_theory_packet_id": interface_packet["source_theory_packet_id"],
        "provider": interface_packet["provider"],
        "model": interface_packet["model"],
        "model_tier": interface_packet["model_tier"],
        "n_interfaces": len(authored_by_id),
        "structured_output_retry_attempts": interface_packet.get(
            "structured_output_retry_attempts", 0
        ),
        "structured_output_retry_history": deepcopy(
            interface_packet.get("structured_output_retry_history", [])
        ),
        "raw_response_fingerprint": interface_packet.get(
            "raw_response_fingerprint", ""
        ),
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
    }
    merged["theory_generation_phases"] = [
        _theory_core_generation_phase_record(core_packet),
        {
            "phase": "estimator_interface_authoring",
            "model": interface_packet["model"],
            "model_tier": interface_packet["model_tier"],
            "structured_output_retry_attempts": interface_packet.get(
                "structured_output_retry_attempts", 0
            ),
        },
    ]
    _refresh_theory_packet_id(merged, question=question)
    errors = validate_theory_packet(merged)
    if errors:
        raise PacketValidationError(
            validation_label="merged LLM TheoryDeveloper packet",
            attempts=1
            + int(interface_packet.get("structured_output_retry_attempts", 0) or 0),
            errors=errors,
            history=interface_packet.get("structured_output_retry_history", []),
            last_invalid_packet=merged,
        )
    merged["validation_errors"] = []
    merged["ok"] = True
    return merged


def _theory_estimator_interface_authoring_json_schema(
    core_packet: Mapping[str, Any],
) -> dict[str, Any]:
    estimator_ids = _theory_estimator_ids(core_packet)
    base_contract_schema = _bounded_theory_schema_value(
        estimator_interface_contract_json_schema(),
        max_string_chars=600,
        default_max_items=12,
    )
    contract_schemas: dict[str, dict[str, Any]] = {}
    specs_by_id = {
        str(row.get("id", "") or "").strip(): row
        for row in core_packet.get("estimator_specs", []) or []
        if isinstance(row, Mapping)
        and str(row.get("id", "") or "").strip()
    }
    for estimator_id in estimator_ids:
        contract_schema = deepcopy(base_contract_schema)
        outputs = specs_by_id.get(estimator_id, {}).get("outputs", [])
        if isinstance(outputs, list) and outputs:
            response_schema = contract_schema["properties"]["response_fields"]
            response_schema["minItems"] = len(outputs)
            response_schema["maxItems"] = len(outputs)
        contract_schemas[estimator_id] = contract_schema
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["interfaces"],
        "properties": {
            "interfaces": {
                "type": "object",
                "additionalProperties": False,
                "required": estimator_ids,
                "properties": {
                    estimator_id: contract_schemas[estimator_id]
                    for estimator_id in estimator_ids
                },
            }
        },
    }


def _theory_estimator_interface_authoring_prompt(
    core_packet: Mapping[str, Any],
) -> str:
    problem = core_packet.get("problem_card", {})
    if not isinstance(problem, Mapping):
        problem = {}
    estimator_rows = []
    for row in core_packet.get("estimator_specs", []) or []:
        if not isinstance(row, Mapping):
            continue
        estimator_rows.append(
            {
                field: _compact_prompt_value_for_key(field, row.get(field))
                for field in (
                    "id",
                    "name",
                    "formula",
                    "algorithm_sketch",
                    "inputs",
                    "outputs",
                    "tuning",
                    "required_assumptions",
                )
                if row.get(field) not in (None, "", [], {})
            }
        )
    payload = {
        "frozen_core_theory": {
            "source_theory_packet_id": core_packet.get("packet_id", ""),
            "problem_card": {
                field: _compact_prompt_value_for_key(field, problem.get(field))
                for field in (
                    "observed_data",
                    "dgp",
                    "estimand",
                    "assumptions",
                    "asymptotic_regime",
                )
                if problem.get(field) not in (None, "", [], {})
            },
            "estimator_specs": estimator_rows,
            "semantic_reference_catalog": _theory_semantic_reference_catalog(
                core_packet
            ),
            "allowed_semantic_reference_ids": sorted(
                theory_semantic_reference_ids(core_packet)
            ),
            "active_revision_finding_ids": list(
                (
                    core_packet.get("theory_revision_transport", {})
                    if isinstance(
                        core_packet.get("theory_revision_transport", {}),
                        Mapping,
                    )
                    else {}
                ).get("active_unresolved_finding_ids", [])
                or []
            ),
        },
        "required_output_schema": (
            _theory_estimator_interface_authoring_json_schema(core_packet)
        ),
        "frozen_output_contract": {
            str(row.get("id", "") or "").strip(): deepcopy(
                row.get("outputs", [])
            )
            for row in core_packet.get("estimator_specs", []) or []
            if isinstance(row, Mapping)
            and str(row.get("id", "") or "").strip()
            and isinstance(row.get("outputs", []), list)
            and row.get("outputs", [])
        },
        "regeneration_contract": {
            "candidate_scope": "complete_interfaces_object",
            "mathematical_owner": "TheoryDeveloper",
            "runtime_role": "schema_reference_lineage_validation_only",
            "independent_acceptance_owner": "semantic_reviewer",
        },
        "proof_boundary": KERNEL_PROOF_BOUNDARY,
    }
    return (
        "Return ONLY one JSON object matching required_output_schema. Emit exactly "
        "one interfaces object property for every frozen estimator_id and no other "
        "keys; each property value is that estimator's interface contract, without "
        "repeating estimator_id inside the value. Infer no "
        "new mathematics: request fields expose the frozen algorithm inputs and "
        "lifecycle; response fields correspond one-for-one, in order, to the exact "
        "frozen outputs. Do not add operational status or unavailable fields unless "
        "one is itself a frozen output. Include the exact value normalization needed "
        "for a caller to consume each output. Cite only ids in "
        "semantic_reference_catalog for derivation_ref. Do not copy asymptotic rates, "
        "orders, theorem conclusions, or explanatory derivations into this executable "
        "interface; they remain in the frozen Markdown/LaTeX workspace. Do not edit or restate the "
        "core theory, keep prose fields concise, and do not claim proof evidence.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


def _theory_semantic_reference_catalog(
    core_packet: Mapping[str, Any],
) -> list[dict[str, str]]:
    derivation = core_packet.get("theory_derivation_packet", {})
    if not isinstance(derivation, Mapping):
        derivation = {}
    rows: list[dict[str, str]] = []
    for collection, id_field, text_fields in (
        ("derivation_steps", "id", ("claim", "equation_or_argument")),
        ("equation_chain", "step_id", ("lhs", "relation", "rhs")),
        ("sanity_checks", "id", ("recomputation", "result")),
        (
            "claim_index",
            "id",
            ("kind", "document_path", "depends_on", "status"),
        ),
        (
            "sanity_check_index",
            "id",
            ("claim_ref", "document_path", "status"),
        ),
    ):
        for raw_row in derivation.get(collection, []) or []:
            if not isinstance(raw_row, Mapping):
                continue
            reference_id = str(raw_row.get(id_field, "") or "").strip()
            if not reference_id:
                continue
            rows.append(
                {
                    "id": reference_id,
                    "kind": collection,
                    "claim": _truncate_text(
                        " | ".join(
                            str(raw_row.get(field, "") or "").strip()
                            for field in text_fields
                            if str(raw_row.get(field, "") or "").strip()
                        ),
                        480,
                    ),
                }
            )
    for collection, text_fields in (
        ("theorem_cards", ("informal_statement", "rate_or_limit_law")),
        ("lemma_cards", ("statement",)),
    ):
        for raw_row in core_packet.get(collection, []) or []:
            if not isinstance(raw_row, Mapping):
                continue
            reference_id = str(raw_row.get("id", "") or "").strip()
            if not reference_id:
                continue
            rows.append(
                {
                    "id": reference_id,
                    "kind": collection,
                    "claim": _truncate_text(
                        " | ".join(
                            str(raw_row.get(field, "") or "").strip()
                            for field in text_fields
                            if str(raw_row.get(field, "") or "").strip()
                        ),
                        480,
                    ),
                }
            )
    return rows


def _canonical_theory_estimator_interface_rows(
    raw: Any,
    *,
    estimator_ids: Sequence[str],
) -> Any:
    """Convert the exact-key provider transport into the canonical row shape."""

    if not isinstance(raw, Mapping):
        return deepcopy(raw)
    return [
        {
            "estimator_id": str(estimator_id),
            "estimator_interface_contract": (
                normalize_estimator_interface_contract(raw.get(estimator_id))
                if isinstance(raw.get(estimator_id), Mapping)
                else deepcopy(raw.get(estimator_id))
            ),
        }
        for estimator_id in estimator_ids
        if estimator_id in raw
    ]


def _theory_estimator_ids(packet: Mapping[str, Any]) -> list[str]:
    return [
        str(row.get("id", "") or "").strip()
        for row in packet.get("estimator_specs", []) or []
        if isinstance(row, Mapping) and str(row.get("id", "") or "").strip()
    ]


def _validate_theory_estimator_interface_authoring_packet(
    packet: Mapping[str, Any],
    *,
    core_packet: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if packet.get("interface_transport_shape") != "exact_key_object":
        errors.append("interface transport must be an exact-key object")
    expected_ids = _theory_estimator_ids(core_packet)
    if len(expected_ids) != len(set(expected_ids)):
        errors.append("frozen core estimator ids must be unique")
    rows = packet.get("interfaces", [])
    if not isinstance(rows, list):
        return ["interfaces must be a list"]
    observed_ids: list[str] = []
    allowed_refs = theory_semantic_reference_ids(core_packet)
    specs_by_id = {
        str(row.get("id", "") or "").strip(): row
        for row in core_packet.get("estimator_specs", []) or []
        if isinstance(row, Mapping)
        and str(row.get("id", "") or "").strip()
    }
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"interfaces[{index}] must be an object")
            continue
        estimator_id = str(row.get("estimator_id", "") or "").strip()
        interface_label = (
            f"interfaces[{json.dumps(estimator_id, ensure_ascii=False)}]"
            if estimator_id
            else f"interfaces[{index}]"
        )
        observed_ids.append(estimator_id)
        if estimator_id not in expected_ids:
            errors.append(
                f"{interface_label}.estimator_id must name a frozen estimator"
            )
        errors.extend(
            estimator_interface_contract_errors(
                row.get("estimator_interface_contract"),
                label=interface_label,
                required=True,
                allowed_derivation_refs=allowed_refs,
            )
        )
        contract = row.get("estimator_interface_contract", {})
        if (
            isinstance(contract, Mapping)
            and dict(contract)
            != project_executable_estimator_interface_contract(contract)
        ):
            errors.append(
                f"{interface_label} must contain only executable ABI fields; "
                "mathematical rates and orders belong in theory documents"
            )
        expected_outputs = specs_by_id.get(estimator_id, {}).get("outputs", [])
        response_fields = (
            contract.get("response_fields", [])
            if isinstance(contract, Mapping)
            else []
        )
        if (
            isinstance(expected_outputs, list)
            and expected_outputs
            and isinstance(response_fields, list)
            and len(response_fields) != len(expected_outputs)
        ):
            errors.append(
                f"{interface_label} response_fields must correspond one-for-one "
                f"to the {len(expected_outputs)} frozen outputs; received "
                f"{len(response_fields)}"
            )
    if len(observed_ids) != len(set(observed_ids)):
        errors.append("interface estimator ids must be unique")
    if set(observed_ids) != set(expected_ids) or len(observed_ids) != len(
        expected_ids
    ):
        errors.append(
            "interfaces must contain exactly one row for every frozen estimator id"
        )
    if packet.get("proof_evidence_status") != THEORY_DERIVATION_NOT_PROOF_EVIDENCE:
        errors.append("interface packet must preserve the LLM-not-proof boundary")
    if packet.get("kernel_verified") is not False:
        errors.append("interface packet cannot set kernel_verified=true")
    errors.extend(_forbidden_proof_claims(packet))
    return sorted(set(errors))


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


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM TheoryDeveloper")


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
