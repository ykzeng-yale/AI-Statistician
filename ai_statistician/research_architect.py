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
from .research_schema import OpenResearchQuestion
from .semantic_review_feedback import model_observations_without_repair_recipes
from .theory_revision_lineage import (
    THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY,
    build_theory_developer_revision_binding,
    theory_developer_revision_binding_errors,
)
from .theory_workspace import run_theory_artifact_workspace


ARCHITECT_SCHEMA_VERSION = 1
THEORY_DERIVATION_NOT_PROOF_EVIDENCE = "LLM_THEORY_DERIVATION_NOT_PROOF_EVIDENCE"
THEORY_MIN_DERIVATION_STEPS = 3
THEORY_MIN_EQUATION_CHAIN_STEPS = 2
THEORY_SERIOUS_MIN_DERIVATION_STEPS = 5
THEORY_SERIOUS_MIN_EQUATION_CHAIN_STEPS = 4
THEORY_SERIOUS_MIN_SANITY_CHECKS = 3
THEORY_PROMPT_MODE_COMPACT = "compact_theory_discovery_packet"
THEORY_PROMPT_MODE_SERIOUS_CAPABILITY = "serious_capability_theory_workspace"
THEORY_PROMPT_MODE_SERIOUS_REVISION = "serious_upstream_theory_revision"
THEORY_SERIOUS_PROMPT_MODES = (
    THEORY_PROMPT_MODE_SERIOUS_CAPABILITY,
    THEORY_PROMPT_MODE_SERIOUS_REVISION,
)
THEORY_DEVELOPER_STAGE_CHECKPOINT_KIND = "TheoryDeveloperStageRecoveryCheckpoint"
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
    theory_workspace_max_turns: int = 8
    theory_workspace_max_reads: int = 4
    theory_workspace_max_submissions: int = 3
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
    ) -> None:
        self.provider = provider or AnthropicArchitectLLMProvider()
        self.config = config

    def derive(
        self,
        question: OpenResearchQuestion,
        *,
        architect_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = dict(architect_context or {})
        theory_prompt_mode = _theory_developer_prompt_mode(context)
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
        recovered_core_packet = _theory_developer_recovered_core_checkpoint(
            context,
            question=question,
            theory_prompt_mode=theory_prompt_mode,
        )
        if recovered_core_packet is not None:
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
                max_reads=self.config.theory_workspace_max_reads,
                max_submissions=self.config.theory_workspace_max_submissions,
                max_no_progress_turns=(
                    self.config.theory_workspace_max_no_progress_turns
                ),
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
                max_submissions=self.config.theory_workspace_max_submissions,
                max_no_progress_turns=(
                    self.config.theory_workspace_max_no_progress_turns
                ),
            )
        else:
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
    if serious_theory_mode:
        prompt_mode = {
            "mode": theory_prompt_mode,
            "purpose": (
                "derive or revise a research-grade statistical procedure with a "
                "long enough equation chain, assumption audit, feasibility analysis, "
                "and critic pass to support independent downstream authoring"
            ),
            "do_not_expand_full_retrieval_or_architect_json": True,
        }
        output_budget_key = "serious_theory_output_budget"
        output_budget = {
            "min_derivation_steps": THEORY_SERIOUS_MIN_DERIVATION_STEPS,
            "max_derivation_steps": (
                THEORY_SERIOUS_MIN_DERIVATION_STEPS
                if transport_recovery
                else 8
            ),
            "min_equation_chain_steps": THEORY_SERIOUS_MIN_EQUATION_CHAIN_STEPS,
            "max_equation_chain_steps": (
                THEORY_SERIOUS_MIN_EQUATION_CHAIN_STEPS
                if transport_recovery
                else 8
            ),
            "min_sanity_checks": THEORY_SERIOUS_MIN_SANITY_CHECKS,
            "max_sanity_checks": (
                THEORY_SERIOUS_MIN_SANITY_CHECKS
                if transport_recovery
                else 6
            ),
            "max_candidate_procedures": 1 if transport_recovery else 2,
            "max_theorem_goals": 1 if transport_recovery else 2,
            "max_lemma_cards": 2 if transport_recovery else 4,
            "max_formalization_requests": 1 if transport_recovery else 2,
            "max_critic_findings": 2 if transport_recovery else 4,
            "max_simulation_predictions": 2 if transport_recovery else 4,
            "max_next_actions": 1 if transport_recovery else 3,
            "max_string_chars": 320 if transport_recovery else 420,
            "transport_recovery": transport_recovery,
            "instruction": (
                (
                    "This is a transport recovery after a truncated response. "
                    "Return the minimum complete serious-theory handoff while "
                    "preserving every active mathematical obligation. "
                )
                if transport_recovery
                else ""
            ) + (
                "Return one complete valid JSON object. Build a coherent mathematical "
                "workspace at the level required by the question: derive claims from "
                "the stated setup and assumptions, link equations and lemmas by id, "
                "and independently check the claims most likely to invalidate the "
                "procedure. Keep the DGP, estimand, procedure, theorem, executable "
                "semantics, simulation plan, and formal target mutually consistent. "
                "When evidence is insufficient or a contradiction remains, record it "
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
            "min_derivation_steps": THEORY_MIN_DERIVATION_STEPS,
            "max_derivation_steps": 5,
            "min_equation_chain_steps": THEORY_MIN_EQUATION_CHAIN_STEPS,
            "max_candidate_procedures": 1,
            "max_theorem_goals": 1,
            "max_lemma_cards": 1,
            "max_formalization_requests": 1,
            "max_critic_findings": 1,
            "max_simulation_predictions": 1,
            "max_next_actions": 1,
            "max_string_chars": 180,
            "instruction": (
                "Return a complete valid JSON object within this budget. Use exactly "
                "one item in estimator_specs, theorem_cards, lemma_cards, "
                "formalization_requests, critic_findings, and next_actions. Use at "
                "least three and at most five derivation_steps, plus at least two "
                "equation_chain rows and an assumption_ledger. Keep every string one "
                "sentence or one equation fragment. Do not include essays, tables, "
                "Markdown, or long simulation instructions."
            ),
        }
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "prompt_mode": prompt_mode,
        "architect_context": compact_context,
        "required_output_contract": THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT,
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
        else "This is a focused first-pass discovery packet: exactly one primary "
        "procedure, one theorem card, one lemma card, one formalization request, one "
        "critic finding, and one next action, but at least three derivation steps and "
        "two equation-chain rows."
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

    prior_theory_material = context.get(
        "metric_protocol_prior_theory_material", {}
    )
    if (
        isinstance(prior_theory_material, Mapping)
        and prior_theory_material.get("artifact_kind")
        == "RuntimeTheoryInformedMetricProtocolMaterial"
        and prior_theory_material.get("execution_results_available") is False
        and isinstance(
            prior_theory_material.get("theory_semantic_material"), Mapping
        )
    ):
        compact["metric_protocol_prior_theory_material"] = {
            "artifact_kind": prior_theory_material.get("artifact_kind", ""),
            "source_theory_packet_id": prior_theory_material.get(
                "source_theory_packet_id", ""
            ),
            "source_theory_packet_hash": prior_theory_material.get(
                "source_theory_packet_hash", ""
            ),
            "theory_semantic_material": dict(
                prior_theory_material.get("theory_semantic_material", {})
            ),
            "execution_results_available": False,
            "proof_evidence_status": prior_theory_material.get(
                "proof_evidence_status", ""
            ),
            "boundary": prior_theory_material.get("boundary", ""),
        }

    return compact


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
        "max_upstream_theory_revisions": feedback.get(
            "max_upstream_theory_revisions", ""
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
self-critique. Preserve uncertainty and semantic risks. Do not claim formal proof
or Lean kernel verification.
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
                "result": "computed or logically reduced result",
                "conclusion": "PASS|FAIL and the theory revision made if FAIL",
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
            "normalization": "string",
            "sample_size_order": "string",
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
                        "sample_size_order": "explicit order in sample size",
                        "sample_size_rate": {
                            "scale": "polynomial_log_n|constant|not_indexed|other",
                            "index_symbol": "n or the actual asymptotic index",
                            "polynomial_exponent": (
                                "numeric exponent of index_symbol"
                            ),
                            "log_exponent": (
                                "numeric exponent of log(index_symbol)"
                            ),
                            "contributions": [
                                {
                                    "quantity": "factor or aggregation cardinality",
                                    "polynomial_exponent": "signed numeric contribution",
                                    "log_exponent": "signed numeric contribution",
                                    "justification_ref": (
                                        "derivation, equation, or sanity-check id"
                                    ),
                                }
                            ],
                        },
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
]["estimator_interface_contract"] = estimator_interface_contract_json_schema(
    require_typed_rate=True
)


def _theory_developer_json_schema(
    *,
    theory_prompt_mode: str,
    transport_recovery: bool = False,
) -> dict[str, Any]:
    """Return the output contract with the prompt's size budget made explicit."""

    serious_theory_mode = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
    max_string_chars = (
        320 if serious_theory_mode and transport_recovery
        else 420 if serious_theory_mode
        else 180
    )
    schema = _bounded_theory_schema_value(
        THEORY_DEVELOPER_JSON_SCHEMA,
        max_string_chars=max_string_chars,
        default_max_items=12,
    )
    properties = schema["properties"]
    derivation = properties["theory_derivation_packet"]["properties"]

    if serious_theory_mode:
        derivation_step_bounds = (
            THEORY_SERIOUS_MIN_DERIVATION_STEPS,
            THEORY_SERIOUS_MIN_DERIVATION_STEPS if transport_recovery else 8,
        )
        equation_chain_bounds = (
            THEORY_SERIOUS_MIN_EQUATION_CHAIN_STEPS,
            THEORY_SERIOUS_MIN_EQUATION_CHAIN_STEPS if transport_recovery else 8,
        )
        sanity_check_bounds = (
            THEORY_SERIOUS_MIN_SANITY_CHECKS,
            THEORY_SERIOUS_MIN_SANITY_CHECKS if transport_recovery else 6,
        )
        top_level_maxima = {
            "estimator_specs": 1 if transport_recovery else 2,
            "theorem_cards": 1 if transport_recovery else 2,
            "lemma_cards": 2 if transport_recovery else 4,
            "formalization_requests": 1 if transport_recovery else 2,
            "critic_findings": 2 if transport_recovery else 4,
            "next_actions": 1 if transport_recovery else 3,
        }
    else:
        derivation_step_bounds = (THEORY_MIN_DERIVATION_STEPS, 5)
        equation_chain_bounds = (THEORY_MIN_EQUATION_CHAIN_STEPS, 5)
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
        derivation["assumption_ledger"], 1, 10
    )
    _set_theory_schema_array_bounds(
        derivation["sanity_checks"], *sanity_check_bounds
    )
    _set_theory_schema_array_bounds(derivation["self_critique"], 1, 4)
    _set_theory_schema_array_bounds(derivation["rejected_alternatives"], 0, 3)
    for field, maximum in top_level_maxima.items():
        _set_theory_schema_array_bounds(properties[field], 1, maximum)
    return schema


def _theory_developer_core_json_schema(
    *,
    theory_prompt_mode: str,
    transport_recovery: bool = False,
) -> dict[str, Any]:
    """Return the bounded core-theory schema without executable interfaces."""

    schema = _theory_developer_json_schema(
        theory_prompt_mode=theory_prompt_mode,
        transport_recovery=transport_recovery,
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
    max_string_chars: int,
    default_max_items: int,
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
            bounded["maxLength"] = max_string_chars
        elif bounded.get("type") == "array":
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
    maximum: int,
) -> None:
    schema["minItems"] = max(0, int(minimum))
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


def _validate_theory_packet(
    packet: Mapping[str, Any],
    *,
    require_estimator_interfaces: bool,
) -> list[str]:
    errors: list[str] = []
    serious_theory_mode = packet.get("serious_theory_mode") is True
    minimum_derivation_steps = (
        THEORY_SERIOUS_MIN_DERIVATION_STEPS
        if serious_theory_mode
        else THEORY_MIN_DERIVATION_STEPS
    )
    minimum_equation_chain_steps = (
        THEORY_SERIOUS_MIN_EQUATION_CHAIN_STEPS
        if serious_theory_mode
        else THEORY_MIN_EQUATION_CHAIN_STEPS
    )
    for field in (
        "problem_card",
        "theory_derivation_packet",
        "estimator_specs",
        "theorem_cards",
        "lemma_cards",
        "proof_plan",
        "formalization_requests",
        "simulation_ademp_spec",
        "critic_findings",
        "next_actions",
    ):
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
        derivation_steps = derivation.get("derivation_steps", [])
        if (
            not isinstance(derivation_steps, list)
            or len(derivation_steps) < minimum_derivation_steps
        ):
            errors.append(
                "theory_derivation_packet.derivation_steps must contain at least "
                f"{minimum_derivation_steps} steps"
            )
        else:
            for idx, row in enumerate(derivation_steps, start=1):
                if not isinstance(row, Mapping):
                    errors.append("theory_derivation_packet.derivation_steps entries must be objects")
                    continue
                if not str(row.get("id", "")).strip():
                    errors.append(f"derivation step {idx} missing id")
                if not str(row.get("claim", "")).strip():
                    errors.append(f"derivation step {idx} missing claim")
                if not str(row.get("equation_or_argument", "")).strip():
                    errors.append(f"derivation step {idx} missing equation_or_argument")
        equation_chain = derivation.get("equation_chain", [])
        if (
            not isinstance(equation_chain, list)
            or len(equation_chain) < minimum_equation_chain_steps
        ):
            errors.append(
                "theory_derivation_packet.equation_chain must contain at least "
                f"{minimum_equation_chain_steps} equation rows"
            )
        else:
            for idx, row in enumerate(equation_chain, start=1):
                if not isinstance(row, Mapping):
                    errors.append("theory_derivation_packet.equation_chain entries must be objects")
                    continue
                if not str(row.get("lhs", "")).strip() or not str(row.get("rhs", "")).strip():
                    errors.append(f"equation_chain row {idx} must include lhs and rhs")
                if not str(row.get("justification", "")).strip():
                    errors.append(f"equation_chain row {idx} missing justification")
        assumption_ledger = derivation.get("assumption_ledger", [])
        if not isinstance(assumption_ledger, list) or not assumption_ledger:
            errors.append("theory_derivation_packet.assumption_ledger must be non-empty")
        else:
            for idx, row in enumerate(assumption_ledger, start=1):
                if not isinstance(row, Mapping):
                    errors.append("theory_derivation_packet.assumption_ledger entries must be objects")
                    continue
                if not str(row.get("assumption", "")).strip():
                    errors.append(f"assumption_ledger row {idx} missing assumption")
                if not row.get("used_in"):
                    errors.append(f"assumption_ledger row {idx} missing used_in")
        sanity_checks = derivation.get("sanity_checks", [])
        if serious_theory_mode and (
            not isinstance(sanity_checks, list)
            or len(sanity_checks) < THEORY_SERIOUS_MIN_SANITY_CHECKS
        ):
            errors.append(
                "theory_derivation_packet.sanity_checks must contain at least "
                f"{THEORY_SERIOUS_MIN_SANITY_CHECKS} explicit recomputations in "
                "serious theory mode"
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
                        "conclusion",
                    )
                    if not str(row.get(field, "") or "").strip()
                ]
                if missing_fields:
                    errors.append(
                        f"theory_derivation_packet.sanity_checks[{idx}] missing "
                        "required fields: " + ", ".join(missing_fields)
                    )
        formalization_handoff = derivation.get("formalization_handoff", {})
        if not isinstance(formalization_handoff, Mapping) or not formalization_handoff:
            errors.append("theory_derivation_packet.formalization_handoff must be non-empty")
        elif not formalization_handoff.get("semantic_alignment_constraints"):
            errors.append(
                "theory_derivation_packet.formalization_handoff.semantic_alignment_constraints must be non-empty"
            )
    for list_field in ("estimator_specs", "theorem_cards", "lemma_cards", "formalization_requests"):
        if not isinstance(packet.get(list_field), list) or not packet.get(list_field):
            errors.append(f"{list_field} must be a non-empty list")
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
                    require_typed_rate=True,
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
    if isinstance(simulation_ademp_spec, Mapping):
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
    for row in packet.get("theorem_cards", []) or []:
        if not isinstance(row, Mapping):
            errors.append("theorem_cards entries must be objects")
            continue
        if not str(row.get("informal_statement", "")).strip():
            errors.append("theorem card missing informal_statement")
        if not str(row.get("proof_strategy", "")).strip():
            errors.append("theorem card missing proof_strategy")
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
) -> dict[str, Any]:
    body = dict(payload)
    serious_theory_mode = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
    body["theory_prompt_mode"] = theory_prompt_mode
    body["serious_theory_mode"] = serious_theory_mode
    derivation_packet = body.get("theory_derivation_packet")
    if isinstance(derivation_packet, Mapping):
        body["theory_derivation_packet"] = _canonicalize_theory_derivation_packet(
            derivation_packet,
            formalization_requests=body.get("formalization_requests", []),
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
    body["theory_derivation_contract"] = {
        "min_derivation_steps": (
            THEORY_SERIOUS_MIN_DERIVATION_STEPS
            if serious_theory_mode
            else THEORY_MIN_DERIVATION_STEPS
        ),
        "min_equation_chain_steps": (
            THEORY_SERIOUS_MIN_EQUATION_CHAIN_STEPS
            if serious_theory_mode
            else THEORY_MIN_EQUATION_CHAIN_STEPS
        ),
        "min_sanity_checks": (
            THEORY_SERIOUS_MIN_SANITY_CHECKS if serious_theory_mode else 0
        ),
        "theory_prompt_mode": theory_prompt_mode,
        "n_derivation_steps": _safe_len(derivation.get("derivation_steps", [])),
        "n_equation_chain_steps": _safe_len(derivation.get("equation_chain", [])),
        "n_assumption_ledger_rows": _safe_len(derivation.get("assumption_ledger", [])),
        "n_sanity_checks": _safe_len(derivation.get("sanity_checks", [])),
        "has_formalization_handoff": bool(
            isinstance(derivation.get("formalization_handoff", {}), Mapping)
            and derivation.get("formalization_handoff")
        ),
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "boundary": (
            "Theory derivation traces are structured LLM reasoning proposals for "
            "simulation/formalization handoff, not proof evidence."
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
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _theory_developer_revision_binding_from_context(
    architect_context: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
) -> dict[str, Any]:
    """Normalize legacy and current feedback into one parent-bound contract."""

    raw_binding = architect_context.get(
        THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY, {}
    )
    if isinstance(raw_binding, Mapping) and raw_binding:
        binding = deepcopy(dict(raw_binding))
    else:
        feedback = theory_developer_source_environment_feedback(architect_context)
        material = architect_context.get("metric_protocol_prior_theory_material", {})
        if not (
            isinstance(feedback, Mapping)
            and feedback.get("artifact_kind")
            == METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND
        ):
            raise PacketValidationError(
                validation_label="TheoryDeveloper targeted revision inputs",
                attempts=0,
                errors=[
                    "revision feedback must be a parent-bound TheoryDeveloper "
                    "revision binding or pre-execution review observation"
                ],
                history=[],
            )
        material = material if isinstance(material, Mapping) else {}
        binding = build_theory_developer_revision_binding(
            revision_source="metric_protocol_preexecution_review",
            question_id=question.id,
            source_feedback=feedback,
            theory_material=material,
            feedback_id=str(feedback.get("feedback_id", "") or ""),
            upstream_theory_revision_count=int(
                feedback.get("upstream_theory_revision_count", 0) or 0
            ),
            max_upstream_theory_revisions=int(
                feedback.get("max_upstream_theory_revisions", 0) or 0
            ),
            execution_results_observed=False,
        )

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
    material = binding.get("theory_material", {})
    material = dict(material) if isinstance(material, Mapping) else {}
    errors: list[str] = []

    material_packet_id = str(
        material.get("source_theory_packet_id", "") or ""
    ).strip()
    material_packet_hash = str(
        material.get("source_theory_packet_hash", "") or ""
    ).strip()

    semantic_material = material.get("theory_semantic_material", {})
    if not isinstance(semantic_material, Mapping) or not semantic_material:
        errors.append("prior theory material must contain lossless semantic material")
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
        for field in THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
        if field in semantic_material
    }
    raw_specs = base_core_payload.get("estimator_specs", [])
    if isinstance(raw_specs, list):
        stripped_specs: list[Any] = []
        for index, raw_spec in enumerate(raw_specs):
            if not isinstance(raw_spec, Mapping):
                errors.append(f"prior estimator_specs[{index}] must be an object")
                stripped_specs.append(deepcopy(raw_spec))
                continue
            spec = deepcopy(dict(raw_spec))
            spec.pop("estimator_interface_contract", None)
            spec.pop("estimator_interface_contract_id", None)
            stripped_specs.append(spec)
        base_core_payload["estimator_specs"] = stripped_specs
    else:
        errors.append("prior estimator_specs must be a list")

    derivation = base_core_payload.get("theory_derivation_packet", {})
    if isinstance(derivation, Mapping):
        derivation = deepcopy(dict(derivation))
        derivation.setdefault("self_critique", [])
        derivation.setdefault("rejected_alternatives", [])
        base_core_payload["theory_derivation_packet"] = derivation
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
        "max_upstream_theory_revisions": binding.get(
            "max_upstream_theory_revisions", 0
        ),
        "feedback": deepcopy(dict(feedback)),
        "transport_feedback": transport_feedback,
        "base_core_payload": base_core_payload,
        "base_core_payload_fingerprint": stable_hash(base_core_payload),
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


def _empty_theory_core_workspace() -> dict[str, Any]:
    """Return shape-only writable artifacts without seeded research content."""

    workspace: dict[str, Any] = {}
    for name, contract in THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT.items():
        if isinstance(contract, Mapping):
            workspace[name] = {}
        elif isinstance(contract, list):
            workspace[name] = []
        else:
            raise TypeError(
                f"unsupported theory workspace contract shape for {name}"
            )
    return workspace


def _initial_theory_workspace_read_only_artifacts(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    theory_prompt_mode: str,
    max_submissions: int,
) -> dict[str, Any]:
    serious = theory_prompt_mode in THEORY_SERIOUS_PROMPT_MODES
    return {
        "initial_authoring_context": {
            "research_question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "architect_context": _compact_architect_context_for_prompt(
                architect_context
            ),
            "required_output_contract": deepcopy(
                THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
            ),
            "authoring_policy": {
                "theory_prompt_mode": theory_prompt_mode,
                "serious_theory_mode": serious,
                "minimum_derivation_steps": (
                    THEORY_SERIOUS_MIN_DERIVATION_STEPS
                    if serious
                    else THEORY_MIN_DERIVATION_STEPS
                ),
                "minimum_equation_chain_steps": (
                    THEORY_SERIOUS_MIN_EQUATION_CHAIN_STEPS
                    if serious
                    else THEORY_MIN_EQUATION_CHAIN_STEPS
                ),
                "minimum_independent_sanity_checks": (
                    THEORY_SERIOUS_MIN_SANITY_CHECKS if serious else 1
                ),
                "maximum_submissions": max(1, int(max_submissions)),
                "row_counts_are_not_quality_metrics": True,
                "substantive_author": "TheoryDeveloper model",
                "runtime_role": (
                    "store exact replacements, validate structure and lineage, "
                    "and return raw observations without editing research content"
                ),
                "proof_boundary": KERNEL_PROOF_BOUNDARY,
            },
        }
    }


def _initial_theory_workspace_prompt(
    *,
    question: OpenResearchQuestion,
    theory_prompt_mode: str,
    max_submissions: int,
) -> str:
    return (
        "Author the initial TheoryDeveloper research workspace for the supplied "
        f"question {question.id!r} in mode {theory_prompt_mode!r}. First read the "
        "single initial_authoring_context artifact. Then use your own statistical "
        "judgment to submit complete theory artifacts. You may submit a coherent "
        "subset and use the raw validator observation to complete or revise the "
        "workspace in the same model session. A successful partial write remains in "
        "the workspace even while the combined workspace is invalid, so submit only "
        "the still-empty or intentionally revised artifacts on the next call. You "
        f"have at most {max(1, int(max_submissions))} "
        "submissions: group related artifacts, and use the final submission to fill "
        "every still-empty required artifact. Derive definitions and claims rather "
        "than treating retrieval as an answer key. Keep assumptions, equations, "
        "estimators, theorem cards, simulation semantics, and formal targets mutually "
        "consistent. Record uncertainty explicitly. Do not claim execution, Lean "
        "proof, or kernel verification. The runtime will not fill, patch, or rewrite "
        "any substantive field."
    )


def _theory_workspace_revision_prompt(
    *,
    question: OpenResearchQuestion,
    revision_inputs: Mapping[str, Any],
) -> str:
    read_only_observations = _theory_workspace_read_only_observations(
        revision_inputs
    )
    reviewer_observations = read_only_observations["reviewer_observations"]
    payload: dict[str, Any] = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "revision_mode": "model_owned_theory_artifact_workspace",
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
        "workspace_artifacts": list(THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT),
        "instructions": [
            (
                "Use read_theory_workspace to inspect the exact parent artifacts "
                "needed for your mathematical decision."
            ),
            (
                "Use your own statistical judgment. Reviewer observations identify "
                "possible defects and are not an answer key or repair recipe."
            ),
            (
                "Submit complete replacements for every artifact whose semantics you "
                "choose to change. Omitted artifacts remain byte-identical."
            ),
            (
                "Propagate each chosen revision through all dependent equations, "
                "assumptions, estimators, theorem cards, simulation predictions, and "
                "formalization requests that need to change."
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
        "Revise the persistent TheoryDeveloper artifact workspace with client tools.\n\n"
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
        "revision_mode": "model_owned_artifact_workspace",
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
        "max_upstream_theory_revisions": revision_inputs.get(
            "max_upstream_theory_revisions", 0
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
        "model_owned_artifact_replacements": True,
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
        "revision_mode": "model_owned_artifact_workspace",
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
) -> list[str]:
    errors = validate_theory_core_packet(packet)
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
    if not isinstance(changed, list) or not changed:
        errors.append("theory workspace revision must change at least one artifact")
    elif set(changed) - set(THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT):
        errors.append("theory workspace revision names an unknown artifact")
    if transport.get("model_owned_artifact_replacements") is not True:
        errors.append("theory workspace revision is not model-owned")
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
    max_submissions: int,
    max_no_progress_turns: int,
) -> dict[str, Any]:
    initial_artifacts = _empty_theory_core_workspace()
    read_only_artifacts = _initial_theory_workspace_read_only_artifacts(
        question=question,
        architect_context=architect_context,
        theory_prompt_mode=theory_prompt_mode,
        max_submissions=max_submissions,
    )
    authoring_binding_id = "initial_theory_authoring:" + stable_hash(
        [question.id, theory_prompt_mode, read_only_artifacts]
    )[:20]
    workspace_id = "theory_workspace:" + stable_hash(
        [authoring_binding_id, initial_artifacts]
    )[:20]

    def build_candidate(
        artifacts: Mapping[str, Any],
        changed_artifact_names: tuple[str, ...],
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
        return _normalize_theory_packet(
            artifacts,
            question=question,
            model=request_model,
            model_tier=model_tier,
            provider_name=provider_name,
            raw_response=raw_response,
            theory_prompt_mode=theory_prompt_mode,
        )

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
            max_submissions=max_submissions,
        ),
        model=request_model,
        model_tier=model_tier,
        temperature=temperature,
        max_tokens=max_tokens,
        max_turns=max(1, max_turns),
        max_reads=1,
        max_submissions=max(1, max_submissions),
        max_no_progress_turns=max(1, max_no_progress_turns),
        workspace_id=workspace_id,
        question_id=question.id,
        authoring_binding_id=authoring_binding_id,
        workspace_operation="initial_discovery",
        initial_artifacts=initial_artifacts,
        read_only_artifacts=read_only_artifacts,
        build_candidate=build_candidate,
        validate_candidate=validate_theory_core_packet,
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
            "authoring_mode": "model_owned_artifact_workspace",
        },
    )
    packet = deepcopy(dict(result.core_packet))
    workspace_evidence = deepcopy(dict(result.evidence))
    packet["llm_client_tool_loop"] = workspace_evidence
    errors = validate_theory_core_packet(packet)
    changed = set(workspace_evidence.get("changed_artifact_names", []) or [])
    expected = set(THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT)
    if changed != expected:
        errors.append(
            "initial theory workspace did not author every required artifact"
        )
    if workspace_evidence.get("workspace_operation") != "initial_discovery":
        errors.append("initial theory workspace operation identity mismatch")
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
    max_reads: int,
    max_submissions: int,
    max_no_progress_turns: int,
) -> dict[str, Any]:
    initial_artifacts = revision_inputs.get("base_core_payload", {})
    if not isinstance(initial_artifacts, Mapping):
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=0,
            errors=["parent theory workspace is not an object"],
            history=[],
        )
    workspace_id = "theory_workspace:" + stable_hash(
        [
            question.id,
            revision_inputs.get("revision_binding_id", ""),
            revision_inputs.get("base_core_payload_fingerprint", ""),
        ]
    )[:20]

    def build_candidate(
        artifacts: Mapping[str, Any],
        changed_artifact_names: tuple[str, ...],
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
        )
        return _attach_theory_workspace_revision_transport(
            packet,
            revision_inputs=revision_inputs,
            provider_name=provider_name,
            model=request_model,
            model_tier=model_tier,
            workspace_id=workspace_id,
            changed_artifact_names=changed_artifact_names,
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
        ),
        model=request_model,
        model_tier=model_tier,
        temperature=temperature,
        max_tokens=max_tokens,
        max_turns=max(1, max_turns),
        max_reads=max(1, max_reads),
        max_submissions=max(1, max_submissions),
        max_no_progress_turns=max(1, max_no_progress_turns),
        workspace_id=workspace_id,
        question_id=question.id,
        authoring_binding_id=str(
            revision_inputs.get("revision_binding_id", "") or ""
        ),
        workspace_operation="targeted_revision",
        initial_artifacts=initial_artifacts,
        read_only_artifacts=_theory_workspace_read_only_observations(
            revision_inputs
        ),
        build_candidate=build_candidate,
        validate_candidate=lambda packet: (
            _validate_theory_workspace_revision_packet(
                packet,
                revision_inputs=revision_inputs,
                workspace_id=workspace_id,
            )
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
            "revision_generation_mode": "model_owned_artifact_workspace",
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
    packet["theory_revision_transport"] = transport
    errors = _validate_theory_workspace_revision_packet(
        packet,
        revision_inputs=revision_inputs,
        workspace_id=workspace_id,
    )
    if errors:
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=int(workspace_evidence.get("turns", 0) or 0),
            errors=errors,
            history=workspace_evidence.get("history", []),
            last_invalid_packet=packet,
        )
    return packet


THEORY_ESTIMATOR_INTERFACE_SYSTEM_PROMPT = """\
You are the interface-authoring phase of the AI Statistician TheoryDeveloper.

The core mathematical workspace is frozen. Translate each frozen estimator into
one typed request/response contract. Do not revise the estimand, formula,
algorithm, assumptions, theorem, or derivation. Every response normalization and
sample-size rate must cite an exact semantic id supplied in the prompt. This
artifact is an executable handoff specification, not proof evidence. Preserve
the frozen outputs exactly: do not invent status, unavailable, diagnostic, or
resource fields that the core theory did not declare. Runtime owns operational
execution status. You own the mathematical rate statement: author the aggregate
rate exponents and their cited explanatory contributions from the frozen theory.
The runtime validates shape and references but never computes or overwrites a rate.
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
) -> dict[str, Any]:
    """Author bounded executable interfaces after core theory is frozen."""

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
    core_phase = {
        "phase": _theory_core_generation_phase(core_packet),
        "model": str(core_packet.get("model", "")),
        "model_tier": str(core_packet.get("model_tier", "")),
        "structured_output_retry_attempts": core_packet.get(
            "structured_output_retry_attempts", 0
        ),
    }
    core_client_tool_loop = core_packet.get("llm_client_tool_loop", {})
    if isinstance(core_client_tool_loop, Mapping) and core_client_tool_loop:
        core_phase["client_tool_transport"] = str(
            core_client_tool_loop.get("transport", "") or ""
        )
        core_phase["client_tool_turns"] = int(
            core_client_tool_loop.get("turns", 0) or 0
        )
        core_phase["client_tool_calls"] = int(
            core_client_tool_loop.get("tool_calls", 0) or 0
        )
    merged["theory_generation_phases"] = [
        core_phase,
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
        estimator_interface_contract_json_schema(
            require_typed_rate=True,
        ),
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
        "one is itself a frozen output. Include normalization and complete sample-size "
        "order. For a genuinely rate-bearing output, author the typed primary-index "
        "polynomial/log projection and its explanatory cited contributions. The "
        "aggregate exponents are your mathematical conclusion; runtime will preserve "
        "them exactly and an independent semantic reviewer will check them. Do not "
        "assume contributions combine by summation unless the frozen derivation says "
        "that they do. For "
        "an output with no sample-size indexing, emit exactly "
        "sample_size_rate={\"scale\":\"not_indexed\"} and do not fabricate "
        "exponents or contributions. "
        "Cite only ids in semantic_reference_catalog for derivation_ref and "
        "justification_ref. Keep additional dimensions and non-polynomial factors in "
        "sample_size_order and use scale=other when needed. Do not edit or restate the "
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
        ("sanity_checks", "id", ("recomputation", "result", "conclusion")),
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
                require_typed_rate=True,
            )
        )
        expected_outputs = specs_by_id.get(estimator_id, {}).get("outputs", [])
        contract = row.get("estimator_interface_contract", {})
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
