from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .formal_source_prompt_context import (
    compact_formal_source_grounding_hits_for_prompt,
)
from .formalizer_feedback import (
    formalizer_validation_feedback_envelope,
)
from .llm_json_repair import (
    PacketValidationError,
    extract_json_object,
    generate_validated_json_packet,
)
from .lean_candidate_revision_tool_loop import (
    LeanCandidateCheck,
    FormalEnvironmentSearch,
    run_lean_candidate_revision_tool_loop,
)
from .model_backend import (
    PROVIDER_STRUCTURED_OUTPUT_ON_REPAIR_METADATA_KEY,
    GeneratorBackend,
    GeneratorRequest,
    resolve_generator_model,
)
from .pseudo_formalization import (
    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
    PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND,
    PSEUDO_FORMALIZATION_SCHEMA_ID,
    PSEUDO_FORMALIZATION_SCHEMA_VERSION,
    PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    PSEUDO_FORMALIZATION_PROMOTION_GATE,
    PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES,
    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS,
    PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
    PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
    PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
    bind_model_pseudo_formal_packet_runtime_envelope,
    pseudo_formal_block_work_order_rows,
    pseudo_formal_provider_envelope_json_schema,
    pseudo_formal_routable_work_order_rows,
    pseudo_formal_work_order_row_has_required_lineage,
    pseudo_formal_work_order_row_has_reviewable_source_anchor,
    pseudo_formal_work_order_row_has_semantic_requirements,
    pseudo_formal_work_order_row_has_source_anchor,
    pseudo_formalizer_prompt_contract,
    validate_pseudo_formal_packet,
)
from .research_schema import OpenResearchQuestion
from .semantic_review_feedback import (
    PRESCRIPTIVE_REPAIR_FIELDS,
    compact_semantic_review_feedback,
    model_observations_without_repair_recipes,
)
from .source_to_bridge_metadata import (
    default_premise_candidate_declaration_name,
    ensure_premise_candidate_declaration_name,
)
from .theory_derivation_trace import (
    compact_theory_derivation_trace,
    theory_trace_alignment_contract,
    theory_trace_consumption_contract,
)


FORMALIZER_SCHEMA_VERSION = 1
FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE = "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE"
FORMALIZER_BOUNDARY = (
    "Formalizer packets are proposals, not Lean proof, source-faithfulness, or "
    "kernel evidence. Only AgentRuntime verification of the exact intended artifact "
    "through local Lean/AXLE/kernel supplies proof evidence."
)
FORMALIZER_MAX_THEORY_ROWS = 3
FORMALIZER_MAX_THEOREM_GOALS = 4
FORMALIZER_MAX_PROOF_BANK_ROWS = 12
FORMALIZER_MAX_INDEXED_ENVIRONMENT_CANDIDATES = 6
FORMALIZER_MAX_TEXT_CHARS = 200
FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE = "SOURCE_THEOREM_CANDIDATE"
FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP = "SOURCE_THEOREM_FORMAL_GAP"
FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT = "HELPER_OR_SUPPORT"
FORMAL_TARGET_ROLES = frozenset(
    {
        FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
        FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP,
        FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT,
    }
)

_RUNTIME_AUTHORED_PRESCRIPTIVE_FIELDS = PRESCRIPTIVE_REPAIR_FIELDS


def _is_runtime_authored_prescriptive_field(key: Any) -> bool:
    key_text = str(key)
    return (
        key_text in _RUNTIME_AUTHORED_PRESCRIPTIVE_FIELDS
        or key_text.endswith(("_repair_rule", "_recipe"))
    )


def _without_runtime_authored_prescriptions(value: Any) -> Any:
    return model_observations_without_repair_recipes(value)


def _is_compaction_path_key(key: Any) -> bool:
    lowered = str(key).lower()
    return (
        lowered == "path"
        or lowered.endswith("_path")
        or lowered.endswith("_paths")
        or lowered.endswith("_file")
        or lowered.endswith("_files")
    )


@dataclass(frozen=True)
class FormalizerConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 6000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1
    use_client_tool_lean_candidate_revision: bool = True
    client_tool_lean_candidate_max_turns: int = 10
    client_tool_lean_candidate_max_source_updates: int = 3
    client_tool_lean_candidate_max_searches: int = 3
    client_tool_lean_candidate_max_checks: int = 3
    client_tool_lean_candidate_max_no_progress_turns: int = 2


def formalizer_proof_construction_strategy_contract() -> dict[str, Any]:
    """Minimal ownership and evidence boundary for model-driven Lean work."""

    return {
        "schema_version": 16,
        "target_identity": (
            "Preserve the exact task-bound theorem, assumptions, declaration identity, "
            "and parent artifact lineage. Never weaken or silently replace the target."
        ),
        "model_ownership": (
            "Each iteration gives the model the complete current Lean source, exact "
            "target, raw verifier output, reviewer findings, proof state, and retrieved "
            "signatures. The model chooses every import, definition, decomposition, tactic, "
            "search query, and source change, then supplies the complete next source."
        ),
        "environment_loop": (
            "Search the active formal environment when context is missing, compile the "
            "exact current source, inspect the returned observations, and regenerate. "
            "AgentRuntime enforces budgets and identities but never edits Lean or maps an "
            "error class to a prescribed fix."
        ),
        "library_context": (
            "Infer naming, namespace, module, and theorem-organization conventions from "
            "retrieved declarations in the active Statlib/Mathlib/project environment; "
            "recheck every reused declaration in that environment."
        ),
        "evidence_boundary": (
            "Generated code, retrieval, reviewer acceptance, and successful elaboration "
            "remain observations. Only the configured exact local Lean/kernel gate may "
            "promote the unchanged target artifact to proof evidence."
        ),
    }


class LLMFormalizerProofEngineerAgent:
    """Generator-backed Formalizer/ProofEngineer proposal worker."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: FormalizerConfig = FormalizerConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def propose(
        self,
        *,
        question: OpenResearchQuestion,
        theory_packet: Mapping[str, Any],
        simulation_manifest: Mapping[str, Any],
        algorithm_manifest: Mapping[str, Any],
        registered_problem: Mapping[str, Any],
        theorem_goals: list[Mapping[str, Any]],
        proof_bank_obligation_catalog: list[Mapping[str, Any]] | None = None,
        proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
        environment_feedback: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        user_prompt = build_formalizer_prompt(
            question=question,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            algorithm_manifest=algorithm_manifest,
            registered_problem=registered_problem,
            theorem_goals=theorem_goals,
            proof_bank_obligation_catalog=proof_bank_obligation_catalog,
            proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
            environment_feedback=environment_feedback or {},
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        provider_name = str(
            getattr(self.provider, "provider_name", self.config.provider_name)
            or self.config.provider_name
        ).lower()
        requires_lean_candidate = _feedback_requires_formalizer_lean_candidate(
            environment_feedback or {}
        )
        requires_pseudo_formalization = _feedback_requires_pseudo_formalization(
            environment_feedback or {},
            proof_bank_runtime_memory_summary or {},
        )
        request = GeneratorRequest(
            system_prompt=FORMALIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=_formalizer_json_schema(
                pseudo_formalization_required=requires_pseudo_formalization,
            ),
            metadata={
                "subsystem": "FormalizerProofEngineer",
                "agent": "LLMFormalizerProofEngineerAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
                **(
                    {
                        PROVIDER_STRUCTURED_OUTPUT_ON_REPAIR_METADATA_KEY: True,
                        "provider_structured_output_initial_mode": (
                            "json_prompt_plus_local_validation"
                        ),
                    }
                    if provider_name == "anthropic"
                    else {}
                ),
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_formalizer_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                backend_provider_name=response.provider,
                raw_response=raw_text,
                theory_packet=theory_packet,
                proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary
                or {},
                environment_feedback=environment_feedback or {},
            )

        def validate_packet(packet: Mapping[str, Any]) -> list[str]:
            return _formalizer_contextual_validation_errors(
                packet,
                environment_feedback=environment_feedback or {},
                proof_bank_runtime_memory_summary=(
                    proof_bank_runtime_memory_summary or {}
                ),
                requires_lean_candidate=requires_lean_candidate,
                requires_pseudo_formalization=requires_pseudo_formalization,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_packet,
            validation_label="LLM Formalizer/ProofEngineer packet",
            max_repair_attempts=self.config.max_repair_attempts,
        )

    def revise_lean_candidate_with_client_tools(
        self,
        *,
        question: OpenResearchQuestion,
        theory_packet: Mapping[str, Any],
        parent_packet: Mapping[str, Any],
        candidate_id: str,
        candidate_source_field: str,
        candidate_lean_declaration: str,
        initial_source: str,
        environment_feedback: Mapping[str, Any],
        proof_bank_runtime_memory_summary: Mapping[str, Any] | None,
        check_candidate: LeanCandidateCheck,
        search_formal_environment: FormalEnvironmentSearch,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Revise one accepted target through model-selected Lean tool actions."""

        if not self.config.use_client_tool_lean_candidate_revision:
            raise ValueError("Formalizer Lean candidate client-tool revision is disabled")
        if not callable(getattr(self.provider, "generate_client_tool_turn", None)):
            raise ValueError("Formalizer provider does not support client-tool turns")
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        loop = run_lean_candidate_revision_tool_loop(
            provider=self.provider,
            system_prompt=(
                FORMALIZER_SYSTEM_PROMPT
                + "\nYou are revising one independently reviewed Lean target. "
                "You own every Lean edit and search query. Use the client tools to "
                "inspect the active formal environment and compile the exact current "
                "source. Do not answer with prose or JSON, and do not weaken the target."
            ),
            user_prompt=_build_lean_candidate_revision_tool_prompt(
                question=question,
                parent_packet=parent_packet,
                candidate_id=candidate_id,
                candidate_source_field=candidate_source_field,
                candidate_lean_declaration=candidate_lean_declaration,
                initial_source=initial_source,
                environment_feedback=environment_feedback,
            ),
            model=request_model,
            model_tier=self.config.model_tier,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            max_turns=max(1, self.config.client_tool_lean_candidate_max_turns),
            max_source_updates=max(
                1,
                self.config.client_tool_lean_candidate_max_source_updates,
            ),
            max_searches=max(1, self.config.client_tool_lean_candidate_max_searches),
            max_checks=max(1, self.config.client_tool_lean_candidate_max_checks),
            max_no_progress_turns=max(
                1,
                self.config.client_tool_lean_candidate_max_no_progress_turns,
            ),
            candidate_id=candidate_id,
            candidate_lean_declaration=candidate_lean_declaration,
            initial_source=initial_source,
            check_candidate=check_candidate,
            search_formal_environment=search_formal_environment,
            request_metadata={
                "subsystem": "FormalizerProofEngineer",
                "agent": "LLMFormalizerProofEngineerAgent",
                "formalizer_phase": "lean_candidate_client_tool_revision",
                "parent_packet_id": str(parent_packet.get("packet_id", "") or ""),
                "proof_evidence_status": FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE,
            },
        )
        revised_payload = _formalizer_revision_payload_from_packet(parent_packet)
        _replace_formalizer_lean_candidate_source(
            revised_payload,
            candidate_id=candidate_id,
            candidate_source_field=candidate_source_field,
            candidate_lean_declaration=candidate_lean_declaration,
            lean_source=loop.lean_source,
        )
        revised_payload["ok"] = True
        revised_payload["validation_errors"] = []
        revised_payload["llm_json_repair_attempts"] = 0
        revised_payload["llm_json_repair_history"] = []
        packet = _normalize_formalizer_packet(
            revised_payload,
            question=question,
            model=loop.evidence.get("model", request_model) or request_model,
            model_tier=self.config.model_tier,
            provider_name=self.config.provider_name,
            backend_provider_name=str(
                loop.evidence.get("provider", self.config.provider_name)
                or self.config.provider_name
            ),
            raw_response=str(loop.evidence.get("transcript_fingerprint", "") or ""),
            theory_packet=theory_packet,
            proof_bank_runtime_memory_summary=(
                proof_bank_runtime_memory_summary or {}
            ),
            environment_feedback=environment_feedback,
        )
        requires_lean_candidate = _feedback_requires_formalizer_lean_candidate(
            environment_feedback
        )
        requires_pseudo_formalization = _feedback_requires_pseudo_formalization(
            environment_feedback,
            proof_bank_runtime_memory_summary or {},
        )
        errors = _formalizer_contextual_validation_errors(
            packet,
            environment_feedback=environment_feedback,
            proof_bank_runtime_memory_summary=(
                proof_bank_runtime_memory_summary or {}
            ),
            requires_lean_candidate=requires_lean_candidate,
            requires_pseudo_formalization=requires_pseudo_formalization,
        )
        if errors:
            raise PacketValidationError(
                validation_label=(
                    "LLM Formalizer Lean candidate client-tool revision packet"
                ),
                attempts=int(loop.evidence.get("turns", 1) or 1),
                errors=sorted(set(errors)),
                history=[],
                last_invalid_packet=packet,
                recovery_checkpoint={
                    "candidate_id": candidate_id,
                    "parent_packet_id": str(
                        parent_packet.get("packet_id", "") or ""
                    ),
                    "submitted_source_hash": loop.source_hash,
                    "client_tool_loop": dict(loop.evidence),
                },
            )
        return packet, dict(loop.evidence)


def _formalizer_contextual_validation_errors(
    packet: Mapping[str, Any],
    *,
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    requires_lean_candidate: bool,
    requires_pseudo_formalization: bool,
) -> list[str]:
    errors = validate_formalizer_packet(packet)
    errors.extend(
        _validate_indexed_lean_environment_candidate_bindings(
            packet,
            environment_feedback=environment_feedback,
        )
    )
    if requires_lean_candidate:
        errors.extend(
            _validate_capability_eval_formalizer_lean_candidate_packet(
                packet,
                environment_feedback=environment_feedback,
                proof_bank_runtime_memory_summary=(
                    proof_bank_runtime_memory_summary
                ),
            )
        )
    if requires_pseudo_formalization:
        errors.extend(
            _validate_required_pseudo_formalization_packet(
                packet,
                environment_feedback=environment_feedback,
                proof_bank_runtime_memory_summary=(
                    proof_bank_runtime_memory_summary
                ),
            )
        )
    return sorted(set(errors))


_FORMALIZER_PACKET_REVISION_ENVELOPE_KEYS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "packet_id",
        "created_at",
        "source_agent",
        "provider",
        "backend_provider",
        "model",
        "model_tier",
        "question",
        "raw_response_fingerprint",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "kernel_verified",
        "full_frontier_theorem_proved",
        "theory_trace_consumption_contract",
        "theory_trace_alignment_contract",
        "runtime_architect_control",
    }
)


def _formalizer_revision_payload_from_packet(
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    if str(packet.get("artifact_kind", "") or "") != (
        "FormalizerProofEngineerProposalPacket"
    ):
        raise ValueError("parent artifact is not a Formalizer proposal packet")
    return {
        str(key): deepcopy(value)
        for key, value in packet.items()
        if key not in _FORMALIZER_PACKET_REVISION_ENVELOPE_KEYS
    }


def _replace_formalizer_lean_candidate_source(
    payload: dict[str, Any],
    *,
    candidate_id: str,
    candidate_source_field: str,
    candidate_lean_declaration: str,
    lean_source: str,
) -> None:
    """Apply model-authored source to one runtime-bound packet row."""

    source_field = str(candidate_source_field or "").strip()
    if source_field not in {
        "formal_targets",
        "source_to_bridge_premise_derivation_candidates",
    }:
        raise ValueError("unsupported Formalizer Lean candidate source field")
    rows = payload.get(source_field, [])
    if not isinstance(rows, list):
        raise ValueError("parent Formalizer candidate container is not a list")
    matches: list[dict[str, Any]] = []
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, dict):
            continue
        if source_field == "formal_targets":
            row_id = str(raw_row.get("id", "") or f"formal_target_candidate_{index}")
            row_declaration = str(
                raw_row.get("candidate_lean_declaration", "") or ""
            ).strip()
        else:
            raw_names = raw_row.get("premise_names", [])
            names = (
                [str(value).strip() for value in raw_names if str(value).strip()]
                if isinstance(raw_names, list | tuple | set)
                else []
            )
            row_id = (
                str(raw_row.get("id", "") or "").strip()
                or str(raw_row.get("candidate_request_id", "") or "").strip()
                or str(
                    raw_row.get(
                        "source_to_bridge_premise_derivation_candidate_request_id",
                        "",
                    )
                    or ""
                ).strip()
                or "_".join(names)
                or str(raw_row.get("premise_name", "") or "").strip()
                or f"source_to_bridge_premise_candidate_{index}"
            )
            row_declaration = str(
                raw_row.get("premise_candidate_declaration_name", "") or ""
            ).strip()
        if row_id == candidate_id or (
            candidate_lean_declaration
            and row_declaration == candidate_lean_declaration
        ):
            matches.append(raw_row)
    if len(matches) != 1:
        raise ValueError(
            "runtime-bound Formalizer candidate did not resolve to exactly one parent row"
        )
    row = matches[0]
    row["lean_imports"] = []
    if source_field == "formal_targets":
        row["lean_statement_sketch"] = lean_source
        row["candidate_lean_declaration"] = candidate_lean_declaration
    else:
        row["premise_derivation_candidate_lean_source"] = lean_source
        row.pop("candidate_lean_source", None)
        row["premise_candidate_declaration_name"] = candidate_lean_declaration


def _build_lean_candidate_revision_tool_prompt(
    *,
    question: OpenResearchQuestion,
    parent_packet: Mapping[str, Any],
    candidate_id: str,
    candidate_source_field: str,
    candidate_lean_declaration: str,
    initial_source: str,
    environment_feedback: Mapping[str, Any],
) -> str:
    repair_context = environment_feedback.get("proofengineer_repair_context", {})
    accepted_review = (
        dict(repair_context)
        if isinstance(repair_context, Mapping)
        else {}
    )
    runtime_observations = _complete_lean_candidate_revision_feedback(
        environment_feedback,
        candidate_id=candidate_id,
    )
    payload = {
        "task": (
            "Revise the complete exact current Lean source through search/edit/check "
            "actions. "
            "Call submit_compiled_source only after check_lean_source passes for the "
            "current source."
        ),
        "tool_workflow": (
            "Use targeted searches, then edit and compile. Preserve enough turn budget "
            "to check every changed source. When ready, check_lean_source followed by "
            "submit_compiled_source may be called in the same turn, in that order."
        ),
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
        },
        "immutable_binding": {
            "parent_packet_id": str(parent_packet.get("packet_id", "") or ""),
            "candidate_id": candidate_id,
            "candidate_source_field": candidate_source_field,
            "candidate_lean_declaration": candidate_lean_declaration,
            "source_theorem_target_identity_status": str(
                accepted_review.get("source_theorem_target_identity_status", "")
                or ""
            ),
            "formalizer_candidate_semantic_review_status": str(
                accepted_review.get(
                    "formalizer_candidate_semantic_review_status",
                    "",
                )
                or ""
            ),
            "target_theorem_statement_hash": str(
                accepted_review.get("target_theorem_statement_hash", "")
                or accepted_review.get(
                    "formalizer_candidate_semantic_review_target_statement_hash",
                    "",
                )
                or ""
            ),
        },
        "current_lean_source": initial_source,
        "runtime_observations": runtime_observations,
        "model_owned_revision_contract": (
            formalizer_proof_construction_strategy_contract()
        ),
        "boundaries": {
            "model_owns_lean_source_and_search_queries": True,
            "runtime_selected_lean_repair": False,
            "local_compile_is_not_source_theorem_semantic_acceptance": True,
            "independent_semantic_review_after_revision_required": True,
            "runtime_kernel_promotion_gate_required": True,
        },
    }
    return json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)


def _task_bound_formal_target_contract(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
    registered_problem: Mapping[str, Any],
) -> dict[str, Any]:
    derivation_packet = (
        theory_packet.get("theory_derivation_packet", {})
        if isinstance(theory_packet, Mapping)
        else {}
    )
    if not isinstance(derivation_packet, Mapping):
        derivation_packet = {}
    formalization_handoff = derivation_packet.get("formalization_handoff", {})
    if not isinstance(formalization_handoff, Mapping):
        formalization_handoff = theory_packet.get("formalization_handoff", {})
    if not isinstance(formalization_handoff, Mapping):
        formalization_handoff = {}

    theorem_card_rows = _task_contract_rows(
        theory_packet.get("theorem_cards", []),
        keys=(
            "id",
            "title",
            "claim",
            "statement",
            "informal_statement",
            "conclusion",
            "assumptions",
            "assumptions_used",
            "rate_or_limit_law",
            "proof_strategy",
            "semantic_risks",
        ),
        limit=FORMALIZER_MAX_THEORY_ROWS,
    )
    theorem_goal_rows = _task_contract_rows(
        theorem_goals,
        keys=(
            "id",
            "title",
            "claim",
            "statement",
            "conclusion",
            "assumptions",
            "proof_obligations",
        ),
        limit=FORMALIZER_MAX_THEOREM_GOALS,
    )
    formalization_request_rows = _task_contract_rows(
        theory_packet.get("formalization_requests", []),
        keys=(
            "id",
            "target",
            "target_theorem_card",
            "claim",
            "statement",
            "reason",
            "semantic_alignment_constraints",
            "proof_obligations",
            "kernel_status",
        ),
        limit=FORMALIZER_MAX_THEORY_ROWS,
    )
    derivation_rows = _task_contract_rows(
        derivation_packet.get("derivation_steps", []),
        keys=("id", "claim", "equation_or_argument", "depends_on", "formal_goal", "risk"),
        limit=8,
    )
    equation_rows = _task_contract_rows(
        derivation_packet.get("equation_chain", []),
        keys=("step_id", "lhs", "relation", "rhs", "justification", "depends_on"),
        limit=8,
    )
    assumption_rows = _task_contract_rows(
        derivation_packet.get("assumption_ledger", []),
        keys=("assumption", "role", "used_in", "risk_if_dropped"),
        limit=12,
    )
    source_target = _task_contract_text(
        formalization_handoff.get("source_theorem_target", ""),
        limit=500,
    )
    candidate_declarations = _task_contract_text_list(
        formalization_handoff.get("candidate_lean_targets", []),
        limit=12,
        char_limit=1000,
    )
    semantic_snapshot = {
        "question_id": question.id,
        "source_theorem_target_id": source_target,
        "registered_theorem_goals": theorem_goal_rows,
        "theory_theorem_cards": theorem_card_rows,
        "formalization_requests": formalization_request_rows,
        "registered_problem": _task_contract_mapping(
            registered_problem,
            keys=(
                "question_id",
                "problem_class",
                "dgp",
                "observed_data",
                "estimand",
                "nuisance_quantities",
                "assumptions",
                "asymptotic_regime",
            ),
        ),
        "derivation_support": {
            "derivation_steps": derivation_rows,
            "equation_chain": equation_rows,
            "assumption_ledger": assumption_rows,
            "self_critique": _task_contract_text_list(
                derivation_packet.get("self_critique", []),
                limit=8,
                char_limit=2000,
            ),
        },
        "formalization_handoff": {
            "source_theorem_target": source_target,
            "candidate_lean_targets": candidate_declarations,
            "required_definitions": _task_contract_text_list(
                formalization_handoff.get("required_definitions", []),
                limit=12,
                char_limit=1800,
            ),
            "lemma_dependencies": _task_contract_text_list(
                formalization_handoff.get("lemma_dependencies", []),
                limit=12,
                char_limit=1000,
            ),
            "semantic_alignment_constraints": _task_contract_text_list(
                formalization_handoff.get("semantic_alignment_constraints", []),
                limit=12,
                char_limit=2400,
            ),
        },
    }
    contract: dict[str, Any] = {
        "schema_version": 1,
        "contract_kind": "task_bound_formal_target",
        "question_id": question.id,
        "source_theorem_target_id": source_target,
        "registered_theorem_goal_ids": [
            str(row.get("id", "") or "").strip()
            for row in theorem_goal_rows
            if str(row.get("id", "") or "").strip()
        ],
        "theory_theorem_card_ids": [
            str(row.get("id", "") or "").strip()
            for row in theorem_card_rows
            if str(row.get("id", "") or "").strip()
        ],
        "formalization_request_ids": [
            str(row.get("id", "") or "").strip()
            for row in formalization_request_rows
            if str(row.get("id", "") or "").strip()
        ],
        "authoritative_payload_paths": {
            "registered_problem": "registered_problem",
            "registered_theorem_goals": "registered_theorem_goals",
            "theory": "theory_packet_summary",
            "derivation": "theory_packet_summary.theory_derivation_trace",
            "runtime_feedback": "runtime_environment_feedback",
        },
        "semantic_authority_order": [
            "registered problem and theorem goal",
            "theory derivation and formalization handoff",
            "review feedback",
        ],
        "candidate_declaration_boundary": (
            "Retrieved declarations are support candidates until task alignment and "
            "local kernel checking both succeed."
        ),
        "generation_policy": (
            "Preserve task-bound objects, assumptions, quantifiers, and conclusion. "
            "Route unavailable prerequisites separately instead of weakening the target."
        ),
    }
    contract["contract_fingerprint"] = stable_hash(semantic_snapshot)
    return contract


def _task_contract_rows(
    value: Any,
    *,
    keys: Sequence[str],
    limit: int,
) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [
        _task_contract_mapping(row, keys=keys)
        for row in value[:limit]
        if isinstance(row, Mapping)
    ]


def _task_contract_mapping(
    value: Mapping[str, Any],
    *,
    keys: Sequence[str],
) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for key in keys:
        child = value.get(key)
        if isinstance(child, Mapping):
            compact_child: Any = {
                str(child_key): _task_contract_text(child_value, limit=2000)
                for child_key, child_value in list(child.items())[:12]
            }
        elif isinstance(child, list | tuple):
            compact_child = _task_contract_text_list(
                child,
                limit=12,
                char_limit=2000,
            )
        else:
            compact_child = _task_contract_text(child, limit=2400)
        if compact_child not in (None, "", [], {}):
            row[key] = compact_child
    return row


def _task_contract_text_list(
    value: Any,
    *,
    limit: int,
    char_limit: int,
) -> list[str]:
    rows = value if isinstance(value, list | tuple) else [value]
    return [
        _task_contract_text(row, limit=char_limit)
        for row in rows[:limit]
        if str(row or "").strip()
    ]


def _task_contract_text(value: Any, *, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _formalizer_indexed_lean_environment_candidates(
    environment_feedback: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Expose executable module identities without turning retrieval into proof."""

    if not isinstance(environment_feedback, Mapping):
        return []
    contexts: list[Mapping[str, Any]] = []
    repair_context = environment_feedback.get("proofengineer_repair_context", {})
    if isinstance(repair_context, Mapping):
        contexts.append(repair_context)
    if environment_feedback.get("formal_source_grounding_hits"):
        contexts.append(environment_feedback)

    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for context in contexts:
        compact_groups = compact_formal_source_grounding_hits_for_prompt(
            context.get("formal_source_grounding_hits", [])
        )
        for group in compact_groups:
            query_role = str(group.get("query_role", "") or "").strip()
            for hit_index, hit in enumerate(group.get("hits", []) or []):
                if not isinstance(hit, Mapping):
                    continue
                declaration_context = hit.get("declaration_source_context", {})
                if not isinstance(declaration_context, Mapping):
                    declaration_context = {}
                module = str(declaration_context.get("module", "") or "").strip()
                declaration = str(hit.get("name", "") or "").strip()
                if not module or not declaration:
                    continue
                identity = (module, declaration)
                if identity in seen:
                    continue
                seen.add(identity)
                activation = hit.get("source_activation", {})
                if not isinstance(activation, Mapping):
                    activation = {}
                relation = str(
                    activation.get("relation_to_active_project", "") or ""
                ).strip()
                if relation == "active_project":
                    import_readiness = "active_project_indexed_module"
                elif relation == "direct_lake_dependency":
                    import_readiness = "direct_dependency_indexed_module"
                elif relation:
                    import_readiness = (
                        "port_or_discovery_candidate_requires_target_project_check"
                    )
                else:
                    import_readiness = "indexed_candidate_requires_target_project_check"
                candidate = {
                    "source_id": str(hit.get("source_id", "") or "")[:120],
                    "module": module[:240],
                    "qualified_declaration": declaration[:240],
                    "query_role": query_role[:120],
                    "relation_to_active_project": relation[:120],
                    "candidate_classification": str(
                        activation.get("classification", "") or ""
                    )[:160],
                    "import_readiness": import_readiness,
                }
                if hit_index == 0:
                    signature = str(hit.get("signature", "") or "")
                    signature_status = str(
                        hit.get("signature_status", "") or ""
                    ).strip()
                    if signature:
                        candidate["signature"] = signature
                    elif signature_status:
                        candidate["signature_status"] = signature_status[:160]
                candidates.append(candidate)
                if (
                    len(candidates)
                    >= FORMALIZER_MAX_INDEXED_ENVIRONMENT_CANDIDATES
                ):
                    return candidates
    return candidates


def _validate_indexed_lean_environment_candidate_bindings(
    packet: Mapping[str, Any],
    *,
    environment_feedback: Mapping[str, Any],
) -> list[str]:
    """Keep model-selected indexed theorem provenance bound to generated source."""

    import_ready_candidates = {
        row["qualified_declaration"]: row
        for row in _formalizer_indexed_lean_environment_candidates(
            environment_feedback
        )
        if row.get("import_readiness")
        in {
            "active_project_indexed_module",
            "direct_dependency_indexed_module",
        }
    }
    if not import_ready_candidates:
        return []

    errors: list[str] = []
    for row in packet.get("formal_targets", []) or []:
        if not isinstance(row, Mapping):
            continue
        if _formal_target_role(row) != FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE:
            continue
        provenance = row.get("source_theorem_target_provenance", {})
        if not isinstance(provenance, Mapping) or not _formalizer_bool_like(
            provenance.get("source_theorem_target_known", False)
        ):
            continue
        target_declaration = str(
            provenance.get("target_lean_declaration", "") or ""
        ).strip()
        indexed = import_ready_candidates.get(target_declaration)
        if indexed is None:
            continue
        target_id = str(row.get("id", "") or "<unnamed>")
        lean_imports = {
            str(value).strip()
            for value in row.get("lean_imports", []) or []
            if str(value).strip()
        }
        expected_module = indexed["module"]
        if expected_module not in lean_imports:
            errors.append(
                f"formal target {target_id} binds indexed source theorem "
                f"{target_declaration} but lean_imports omits its exact indexed "
                f"module {expected_module}"
            )
        lean_source = str(row.get("lean_statement_sketch", "") or "")
        if target_declaration not in lean_source:
            errors.append(
                f"formal target {target_id} binds indexed source theorem "
                f"{target_declaration} in provenance but the generated Lean source "
                "does not reference that exact qualified declaration; importing its "
                "module or copying its name only into provenance is not adoption"
            )
    return errors


def build_formalizer_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    algorithm_manifest: Mapping[str, Any],
    registered_problem: Mapping[str, Any],
    theorem_goals: list[Mapping[str, Any]],
    proof_bank_obligation_catalog: list[Mapping[str, Any]] | None = None,
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
    environment_feedback: Mapping[str, Any] | None = None,
) -> str:
    catalog_rows = [
        _compact_mapping(
            row,
            keys=("obligation_id", "candidate_rank", "candidate_sources", "catalog_scope", "target_kind"),
        )
        for row in (proof_bank_obligation_catalog or _proof_bank_catalog_from_theorem_goals(theorem_goals))
        if isinstance(row, Mapping)
    ][:FORMALIZER_MAX_PROOF_BANK_ROWS]
    theorem_cards = _compact_rows(
        theory_packet.get("theorem_cards", []) if isinstance(theory_packet, Mapping) else [],
        keys=(
            "id",
            "title",
            "claim",
            "statement",
            "informal_statement",
            "conclusion",
            "assumptions",
            "assumptions_used",
            "rate_or_limit_law",
            "proof_strategy",
            "semantic_risks",
            "proof_obligations",
        ),
        limit=FORMALIZER_MAX_THEORY_ROWS,
    )
    lemma_cards = _compact_rows(
        theory_packet.get("lemma_cards", []) if isinstance(theory_packet, Mapping) else [],
        keys=("id", "title", "claim", "statement", "role", "depends_on"),
        limit=FORMALIZER_MAX_THEORY_ROWS,
    )
    formalization_requests = _compact_rows(
        theory_packet.get("formalization_requests", []) if isinstance(theory_packet, Mapping) else [],
        keys=("id", "target", "claim", "statement", "reason", "proof_obligations"),
        limit=FORMALIZER_MAX_THEORY_ROWS,
    )
    theorem_goal_rows = _compact_rows(
        theorem_goals,
        keys=(
            "id",
            "title",
            "informal_statement",
            "claim",
            "claim_type",
            "statement",
            "proof_strategy",
            "required_primitives",
            "proof_obligations",
        ),
        limit=FORMALIZER_MAX_THEOREM_GOALS,
    )
    raw_theory_derivation_packet = (
        theory_packet.get("theory_derivation_packet", {})
        if isinstance(theory_packet, Mapping)
        else {}
    )
    theory_derivation_packet = (
        raw_theory_derivation_packet
        if isinstance(raw_theory_derivation_packet, Mapping)
        else {}
    )
    theory_derivation_trace = compact_theory_derivation_trace(theory_packet)
    runtime_environment_feedback = _complete_formalizer_environment_observations(
        environment_feedback or {}
    )
    indexed_lean_environment_candidates = (
        _formalizer_indexed_lean_environment_candidates(environment_feedback or {})
    )
    requires_lean_candidate = _feedback_requires_formalizer_lean_candidate(
        environment_feedback or {}
    )
    task_bound_formal_target_contract = _task_bound_formal_target_contract(
        question=question,
        theory_packet=theory_packet,
        theorem_goals=theorem_goals,
        registered_problem=registered_problem,
    )
    proof_memory_summary = _compact_proof_bank_runtime_memory_summary(
        proof_bank_runtime_memory_summary or {}
    )
    pseudo_formalization_required = _feedback_requires_pseudo_formalization(
        environment_feedback or {},
        proof_memory_summary,
    )
    pseudo_formalization_active = pseudo_formalization_required
    required_pseudo_formal_target_lanes = _required_pseudo_formal_target_lanes(
        environment_feedback or {},
        proof_memory_summary,
    )
    exact_semantic_definition_gate_active = (
        _source_theorem_exact_semantic_definition_gate_active(
            environment_feedback=environment_feedback or {},
            proof_bank_runtime_memory_summary=proof_memory_summary,
        )
    )
    source_theorem_candidate_materialization_contract = (
        {}
        if exact_semantic_definition_gate_active
        else _source_theorem_candidate_materialization_contract(
            proof_memory_summary,
            environment_feedback=environment_feedback or {},
        )
    )
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "prompt_mode": {
            "mode": "target_bound_formalization_specification",
            "max_items_per_list": 3,
            "list_scope": "current_active_frontier_only",
            "lemma_dependency_plan_scope": "current_packet_only",
            "do_not_merge_unrelated_obligations_to_fit_transport_cap": True,
            "expand_target_bound_derivation": True,
            "do_not_expand_unrelated_derivations": True,
        },
        "indexed_lean_environment_candidates": indexed_lean_environment_candidates,
        "theory_packet_summary": {
            "packet_id": theory_packet.get("packet_id", ""),
            "theorem_cards": theorem_cards,
            "lemma_cards": lemma_cards,
            "theory_derivation_trace": theory_derivation_trace,
            "proof_plan": _compact_value(theory_packet.get("proof_plan", {}) if isinstance(theory_packet, Mapping) else {}),
            "formalization_requests": formalization_requests,
            "omitted_counts": {
                "theorem_cards": _safe_len(theory_packet.get("theorem_cards", []) if isinstance(theory_packet, Mapping) else []),
                "lemma_cards": _safe_len(theory_packet.get("lemma_cards", []) if isinstance(theory_packet, Mapping) else []),
                "formalization_requests": _safe_len(theory_packet.get("formalization_requests", []) if isinstance(theory_packet, Mapping) else []),
                "derivation_steps": _safe_len(
                    theory_derivation_packet.get("derivation_steps", [])
                ),
            },
        },
        "theory_trace_consumption_contract": theory_trace_consumption_contract(
            theory_packet,
            consumer_subsystem="FormalizerProofEngineer",
        ),
        "simulation_manifest_summary": {
            "manifest_id": simulation_manifest.get("manifest_id", ""),
            "simulation_passed": simulation_manifest.get("simulation_passed"),
            "proof_evidence_status": simulation_manifest.get("proof_evidence_status", ""),
        },
        "algorithm_manifest_summary": {
            "manifest_id": algorithm_manifest.get("manifest_id", ""),
            "n_executed": algorithm_manifest.get("n_executed", 0),
            "promotion_ready": algorithm_manifest.get("promotion_ready", False),
        },
        "registered_problem": _compact_mapping(
            registered_problem,
            keys=("question_id", "problem_class", "dgp", "estimand", "assumptions", "asymptotic_regime"),
        ),
        "registered_theorem_goals": theorem_goal_rows,
        "registered_theorem_goals_total": _safe_len(theorem_goals),
        "task_bound_formal_target_contract": task_bound_formal_target_contract,
        "model_owned_formalizer_contract": (
            formalizer_proof_construction_strategy_contract()
        ),
        "registered_proof_bank_obligation_catalog": catalog_rows,
        "registered_proof_bank_obligation_catalog_total": _safe_len(
            proof_bank_obligation_catalog or theorem_goals
        ),
        "proof_bank_runtime_memory_summary": proof_memory_summary,
        "source_theorem_candidate_materialization_contract": (
            source_theorem_candidate_materialization_contract
        ),
        "pseudo_formalization_contract": (
            pseudo_formalizer_prompt_contract()
            if pseudo_formalization_active
            else {}
        ),
        "pseudo_formalization_required_target_lanes": list(
            required_pseudo_formal_target_lanes
        ),
        "runtime_environment_feedback": runtime_environment_feedback,
        "formalizer_lean_candidate_contract": (
            {
                "capability_eval_requires_formalizer_lean_candidate": True,
                "task_bound_formal_target_contract_fingerprint": (
                    task_bound_formal_target_contract.get("contract_fingerprint", "")
                ),
                "required_when_true": (
                    "Return at least one complete Lean candidate in the required schema, "
                    "including its exact declaration identity and whether it represents "
                    "the unchanged source theorem, an explicit formal gap, or helper "
                    "support. AgentRuntime compiles the exact supplied source and asks "
                    "Lean to check the supplied declaration; it does not parse, edit, or "
                    "complete Lean on the model's behalf. Routing roles are metadata, not "
                    "proof claims."
                ),
                "not_proof_evidence": (
                    "the Lean candidate remains a proposal until AgentRuntime runs "
                    "local Lean/AXLE on that exact artifact"
                ),
            }
            if requires_lean_candidate
            else {}
        ),
        "model_owned_feedback_instructions": (
            _model_owned_formalizer_feedback_instructions(
            proof_memory_summary,
            runtime_environment_feedback,
            )
        ),
        "proof_bank_obligation_request_policy": (
            {
                "use_only_registered_catalog_ids_when_possible": True,
                "request_effect": "priority_only_for_kernel_smoke_selection",
                "runtime_gate": "unknown ids rejected; requests are not proof evidence",
                "when_catalog_exhausted_by_kernel_memory": (
                    "skip verified bridge obligations and target theorem-level "
                    "reduction closure"
                ),
            }
            if catalog_rows or proof_memory_summary
            else {}
        ),
        "required_output_contract": _formalizer_output_contract_for_prompt(
            has_theory_trace=bool(theory_derivation_trace),
            pseudo_formalization_active=pseudo_formalization_active,
            pseudo_formalization_required=pseudo_formalization_required,
            source_theorem_candidate_materialization_contract=(
                source_theorem_candidate_materialization_contract
            ),
            task_bound_formal_target_contract=task_bound_formal_target_contract,
            source_to_bridge_premise_derivation_required=bool(
                proof_memory_summary.get(
                    "source_to_bridge_premise_derivation_required"
                )
                or proof_memory_summary.get("recommended_formalizer_target_mode")
                == "source_to_bridge_premise_derivation_required"
            ),
        ),
        "boundary": FORMALIZER_BOUNDARY,
    }
    payload = {
        key: value
        for key, value in payload.items()
        if value not in (None, "", [], {}, ())
    }
    if requires_lean_candidate:
        lean_candidate_instruction = (
            "Capability-eval requests a complete Lean candidate for the unchanged "
            "task-bound target when the supplied source, retrieval, and environment "
            "observations make one supportable. Choose the formalization, definitions, "
            "decomposition, imports, and tactics yourself. If essential context is "
            "missing, return the most precise typed blocker supported by the output "
            "schema instead of weakening the target or inventing evidence. Generated "
            "Lean remains a proposal until the exact local Lean/kernel gate accepts it. "
        )
    else:
        lean_candidate_instruction = ""
    if pseudo_formalization_required:
        pseudo_formalization_instruction = (
            "PF/BV decomposition is required for this turn. Author at least one "
            "pseudo_formal_proof_packets entry from the source artifacts, current "
            "provider schema, pseudo_formalization_contract, requested target lanes, "
            "and exact environment observations. Choose the mathematical blocks and "
            "routing yourself; the runtime does not provide a copy-ready answer or an "
            "error-specific repair recipe. The unchanged PF/BV validator will return "
            "any remaining structural or routing errors as the next observation. "
            "PF/BV output is routing memory only and cannot claim Lean or kernel proof. "
        )
    else:
        pseudo_formalization_instruction = ""
    indexed_environment_instruction = (
        "When indexed_lean_environment_candidates is present, use it as the first "
        "executable environment catalog. For a semantically matching active-project "
        "or direct-dependency row, put its exact module in lean_imports. If you select "
        "that row as target or support, the generated Lean source must reference its "
        "exact qualified_declaration and use its supplied signature; merely importing "
        "the module is not adoption. Do not replace an indexed declaration with "
        "invented binder types, an invented namespace, or a guessed neighboring API. "
        "Do not derive or guess a module path from a namespace or declaration name. "
        "candidate_lean_declaration must name the declaration actually introduced by "
        "lean_statement_sketch. A port/discovery row remains guidance until "
        "target-project feedback confirms it. If no indexed row supports the target, "
        "emit a precise FORMAL_GAP or retrieval request instead of invented Lean. "
        if indexed_lean_environment_candidates
        else ""
    )
    return (
        "Return ONLY compact JSON matching required_output_contract, with at most 3 "
        "current-active-frontier items/list. Keep unrelated obligations separate "
        "across later packets rather than merging them. Treat "
        "task_bound_formal_target_contract as semantic authority and use "
        "model_owned_feedback_instructions as the correction boundary. Retrieved "
        "declarations are support APIs "
        "unless exact lineage identifies the source theorem; preserve that target and "
        "await AgentRuntime checking of the exact artifact. "
        + indexed_environment_instruction
        + pseudo_formalization_instruction
        + "Set candidate status to NEEDS_KERNEL_CHECK; use FORMAL_GAP only for an "
        "unresolved source target with "
        "no Lean source. Leave optional retrieval, gap, critic, and action lists empty "
        "unless this packet has a concrete need; never invent scaffolding rows. Every "
        "next_actions entry must point to an artifact or candidate "
        "actually emitted; otherwise record a typed blocker, not a phantom executable "
        "action. "
        + lean_candidate_instruction
        + "\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


FORMALIZER_SYSTEM_PROMPT = """\
You are the LLM Formalizer/ProofEngineer inside an AI Statistician AgentRuntime.

Your job is to translate statistical theorem proposals into Lean target plans,
dependency DAGs, proof-search tasks, and kernel-verification work orders. You
are a generator, not the verifier. Do not report Lean proofs as checked unless
AgentRuntime provides AXLE/local Lean evidence.
"""


FORMALIZER_OUTPUT_CONTRACT: dict[str, Any] = {
    "theory_trace_alignment": {
        "referenced_derivation_steps": ["trace step ids"],
        "referenced_equation_steps": ["trace equation step_ids"],
        "referenced_assumptions": ["trace assumption names"],
        "referenced_formalization_targets": ["trace formalization targets"],
        "rationale": "short string",
    },
    "formal_targets": [
        {
            "id": "string",
            "formal_target_role": (
                "SOURCE_THEOREM_CANDIDATE|SOURCE_THEOREM_FORMAL_GAP|"
                "HELPER_OR_SUPPORT; single generated routing authority, not proof evidence"
            ),
            "informal_source": "string",
            "lean_statement_sketch": "string",
            "candidate_lean_declaration": (
                "exact Lean-resolvable declaration name emitted by "
                "lean_statement_sketch, namespace-qualified when needed; candidate "
                "identity checked by Lean, not source-theorem provenance"
            ),
            "lean_imports": ["Mathlib"],
            "semantic_alignment_constraints": ["string"],
            "source_theorem_target_provenance": {
                "target_lean_declaration": "source theorem Lean declaration, not adapter declaration",
                "source_theorem_goal_id": "registered theorem goal id",
                "source_theorem_target_known": (
                    "boolean routing provenance; true only for the exact source theorem"
                ),
            },
            "expected_status": "NEEDS_KERNEL_CHECK|FORMAL_GAP",
        }
    ],
    "lemma_dependency_plan": [
        {
            "from": "string",
            "to": "string",
            "role": "string",
            "risk": "string",
        }
    ],
    "retrieval_queries": [],
    "proof_search_plan": {
        "preferred_tools": ["string"],
        "tactic_or_certificate_hints": ["string"],
        "kernel_check_plan": ["string"],
        "known_blockers": ["string"],
    },
    "proof_bank_obligation_requests": [],
    "gap_taxonomy": [],
    "critic_findings": [],
    "next_actions": [],
}


def _formalizer_output_contract_for_prompt(
    *,
    has_theory_trace: bool,
    pseudo_formalization_active: bool = False,
    pseudo_formalization_required: bool = False,
    source_theorem_candidate_materialization_contract: Mapping[str, Any] | None = None,
    task_bound_formal_target_contract: Mapping[str, Any] | None = None,
    source_to_bridge_premise_derivation_required: bool = False,
) -> dict[str, Any]:
    contract = dict(FORMALIZER_OUTPUT_CONTRACT)
    contract.pop("theory_trace_alignment", None)
    if has_theory_trace:
        contract["theory_trace_alignment"] = FORMALIZER_OUTPUT_CONTRACT[
            "theory_trace_alignment"
        ]
    materialization_contract = (
        source_theorem_candidate_materialization_contract
        if isinstance(source_theorem_candidate_materialization_contract, Mapping)
        else {}
    )
    task_contract = (
        task_bound_formal_target_contract
        if isinstance(task_bound_formal_target_contract, Mapping)
        else {}
    )
    if materialization_contract:
        target_ids = [
            str(value).strip()
            for value in materialization_contract.get("target_ids", []) or []
            if str(value).strip()
        ]
        target_names = [
            str(value).strip()
            for value in materialization_contract.get("target_names", []) or []
            if str(value).strip()
        ]
        target_identity = (target_ids or target_names or ["requested_source_theorem_target"])[0]
        contract["formal_targets"] = [
            {
                "id": target_identity,
                "formal_target_role": FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
                "informal_source": (
                    "exact source theorem candidate, not a helper/support lemma"
                ),
                "lean_statement_sketch": (
                    "concrete theorem/lemma declaration for the exact source theorem; "
                    "must preserve the task-bound objects, assumptions, quantifiers, "
                    "and conclusion and "
                    "must not be FORMAL_GAP, helper-only, source-to-bridge-only, "
                    "or prose"
                ),
                "candidate_lean_declaration": target_identity,
                "lean_imports": [
                    "narrow verified imports only; do not guess unavailable Mathlib root"
                ],
                "semantic_alignment_constraints": [
                    (
                        "copy requested target identity and preserve the exact "
                        "task-bound semantic contract"
                    ),
                    (
                        "do not assume the requested conclusion or replace it with "
                        "a support result"
                    ),
                ],
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": target_identity,
                    "source_theorem_goal_id": target_identity,
                    "target_ids": target_ids or [target_identity],
                    "target_names": target_names or [target_identity],
                },
                "expected_status": "NEEDS_KERNEL_CHECK",
            }
        ]
        contract["source_theorem_candidate_materialization_required"] = {
            "required": True,
            "forbidden_substitutes": [
                "FORMAL_GAP-only formal_targets row",
                "helper/support formal target",
                "source_to_bridge_premise_derivation_candidates-only packet",
                "next_actions for candidates absent from this packet",
            ],
            "proof_boundary": (
                "materialization is not proof evidence until local Lean/AXLE "
                "checks the exact emitted candidate"
            ),
            "task_bound_formal_target_contract_fingerprint": str(
                task_contract.get("contract_fingerprint", "") or ""
            ),
        }
    if source_to_bridge_premise_derivation_required:
        contract["source_to_bridge_premise_derivation_candidates"] = [
            {
                "premise_name": "copy pending premise_name from runtime memory",
                "premise_names": ["copy pending premise_name(s) from runtime memory"],
                "premise_candidate_declaration_name": (
                    "copy exact premise_candidate_declaration_name when supplied"
                ),
                "premise_candidate_declaration_names": [
                    "for a grouped request, copy one exact declaration identity "
                    "per premise_name in the same order"
                ],
                "premise_derivation_candidate_lean_source": (
                    "canonical Lean source field; emit the exact structured "
                    "premise_candidate_declaration_name using source-local declaration "
                    "and namespace conventions. AgentRuntime compiles the source and "
                    "asks Lean to #check that identity; do not use lean_source/lean_code "
                    "aliases in the final JSON"
                ),
                "source_to_bridge_premise_derivation_candidate_request_id": (
                    "copy runtime request id when supplied"
                ),
                "source_to_bridge_premise_derivation_candidate_request": (
                    "copy runtime request object when supplied"
                ),
                "expected_status": "NEEDS_KERNEL_CHECK",
            }
        ]
        contract["source_to_bridge_premise_derivation_candidate_requests"] = []
    if pseudo_formalization_active:
        contract["pseudo_formal_proof_packets"] = (
            "optional PF/BV routing packets; omit unless the active feedback "
            "identifies a source-anchored structural block"
        )
    if pseudo_formalization_required:
        contract["pseudo_formal_proof_packets"] = {
            "required": True,
            "minimum_items": 1,
            "author_against": [
                "current provider JSON schema",
                "pseudo_formalization_contract",
                "source artifacts and theory trace",
                "exact validator and environment observations",
                "pseudo_formalization_required_target_lanes",
            ],
            "validation_authority": "unchanged local PF/BV validator",
            "runtime_selected_mathematical_content": False,
            "boundary": "PF/BV packet is routing memory, not Lean/kernel proof evidence",
        }
    return contract


FORMAL_TARGET_PROVIDER_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "required": [
        "id",
        "formal_target_role",
        "informal_source",
        "lean_statement_sketch",
        "candidate_lean_declaration",
        "lean_imports",
        "semantic_alignment_constraints",
        "source_theorem_target_provenance",
        "expected_status",
    ],
    "properties": {
        "id": {"type": "string"},
        "formal_target_role": {
            "type": "string",
            "enum": sorted(FORMAL_TARGET_ROLES),
        },
        "informal_source": {"type": "string"},
        "lean_statement_sketch": {"type": "string"},
        "candidate_lean_declaration": {"type": "string"},
        "lean_imports": {
            "type": "array",
            "items": {"type": "string"},
        },
        "semantic_alignment_constraints": {
            "type": "array",
            "items": {"type": "string"},
        },
        "source_theorem_target_provenance": {
            "type": "object",
            "additionalProperties": True,
            "required": [
                "target_lean_declaration",
                "source_theorem_goal_id",
                "source_theorem_target_known",
            ],
            "properties": {
                "target_lean_declaration": {"type": "string"},
                "source_theorem_goal_id": {"type": "string"},
                "source_theorem_target_known": {"type": "boolean"},
            },
        },
        "expected_status": {
            "type": "string",
            "enum": ["NEEDS_KERNEL_CHECK", "FORMAL_GAP"],
        },
    },
}


FORMALIZER_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "formal_targets",
        "lemma_dependency_plan",
        "retrieval_queries",
        "proof_search_plan",
        "gap_taxonomy",
        "critic_findings",
        "next_actions",
    ],
    "properties": {
        "formal_targets": {
            "type": "array",
            "minItems": 1,
            "items": FORMAL_TARGET_PROVIDER_JSON_SCHEMA,
        },
        "lemma_dependency_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["from", "to"],
                "properties": {
                    "from": {"type": "string", "minLength": 1},
                    "to": {"type": "string", "minLength": 1},
                    "role": {"type": "string"},
                    "risk": {"type": "string"},
                },
            },
        },
        "retrieval_queries": {"type": "array"},
        "proof_search_plan": {"type": "object"},
        "proof_bank_obligation_requests": {"type": "array"},
        "source_to_bridge_premise_derivation_candidates": {"type": "array"},
        "source_to_bridge_premise_derivation_candidate_requests": {
            "type": "array"
        },
        "pseudo_formal_proof_packets": {"type": "array"},
        "gap_taxonomy": {"type": "array"},
        "critic_findings": {"type": "array"},
        "next_actions": {"type": "array"},
    },
}


def _formalizer_json_schema(
    *,
    pseudo_formalization_required: bool,
) -> dict[str, Any]:
    schema = deepcopy(FORMALIZER_JSON_SCHEMA)
    if not pseudo_formalization_required:
        return schema

    required = list(schema.get("required", []) or [])
    if "pseudo_formal_proof_packets" not in required:
        required.append("pseudo_formal_proof_packets")
    schema["required"] = required

    schema["properties"]["pseudo_formal_proof_packets"] = {
        "type": "array",
        "minItems": 1,
        "items": pseudo_formal_provider_envelope_json_schema(),
    }
    return schema


def _formal_target_role(row: Mapping[str, Any]) -> str:
    return str(row.get("formal_target_role", "") or "").strip().upper()




def _formal_target_role_contract_errors(
    row: Mapping[str, Any],
    *,
    require_role: bool,
) -> list[str]:
    target_id = str(row.get("id", "") or "<unnamed>")
    role = _formal_target_role(row)
    if not role:
        return (
            [
                f"formal target {target_id} must provide formal_target_role as one "
                "of SOURCE_THEOREM_CANDIDATE, SOURCE_THEOREM_FORMAL_GAP, or "
                "HELPER_OR_SUPPORT"
            ]
            if require_role
            else []
        )
    if role not in FORMAL_TARGET_ROLES:
        return [
            f"formal target {target_id} has unsupported formal_target_role: {role}"
        ]

    errors: list[str] = []
    expected_status = str(row.get("expected_status", "") or "")
    lean_source = str(row.get("lean_statement_sketch", "") or "").strip()
    candidate_declaration = str(
        row.get("candidate_lean_declaration", "") or ""
    ).strip()
    provenance = row.get("source_theorem_target_provenance", {})
    provenance_mapping = provenance if isinstance(provenance, Mapping) else {}
    target_known = _source_theorem_target_known(provenance_mapping)

    if role == FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE:
        if expected_status != "NEEDS_KERNEL_CHECK":
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_CANDIDATE must set "
                "expected_status=NEEDS_KERNEL_CHECK"
            )
        if not lean_source:
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_CANDIDATE must provide a "
                "nonempty Lean candidate"
            )
        if not candidate_declaration:
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_CANDIDATE must provide "
                "candidate_lean_declaration"
            )
        if target_known is None:
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_CANDIDATE must provide an "
                "explicit boolean source_theorem_target_known provenance value"
            )
        if not str(provenance_mapping.get("target_lean_declaration", "") or "").strip():
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_CANDIDATE must bind "
                "source_theorem_target_provenance.target_lean_declaration"
            )
    elif role == FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP:
        if expected_status != "FORMAL_GAP":
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_FORMAL_GAP must set "
                "expected_status=FORMAL_GAP"
            )
        if lean_source or candidate_declaration:
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_FORMAL_GAP must keep Lean source "
                "and candidate_lean_declaration empty"
            )
        if target_known is not True:
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_FORMAL_GAP must bind a known "
                "source theorem using source_theorem_target_known=true"
            )
        if not any(
            str(provenance_mapping.get(key, "") or "").strip()
            for key in ("target_lean_declaration", "source_theorem_goal_id")
        ):
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=SOURCE_THEOREM_FORMAL_GAP must preserve a "
                "target_lean_declaration or source_theorem_goal_id"
            )
    else:
        if expected_status not in {"NEEDS_KERNEL_CHECK", "FORMAL_GAP"}:
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=HELPER_OR_SUPPORT must set expected_status to "
                "NEEDS_KERNEL_CHECK for executable support or FORMAL_GAP for an "
                "empty fail-closed support blocker"
            )
        if expected_status == "NEEDS_KERNEL_CHECK" and (
            not lean_source or not candidate_declaration
        ):
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=HELPER_OR_SUPPORT must provide a nonempty Lean "
                "candidate and candidate_lean_declaration"
            )
        if expected_status == "FORMAL_GAP" and (
            lean_source or candidate_declaration
        ):
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=HELPER_OR_SUPPORT and expected_status=FORMAL_GAP "
                "must keep Lean source and candidate_lean_declaration empty"
            )
        if target_known is not False:
            errors.append(
                f"formal target {target_id} with "
                "formal_target_role=HELPER_OR_SUPPORT must set "
                "source_theorem_target_known=false"
            )
    return errors


def validate_formalizer_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("formal_targets") in (None, "", [], {}):
        errors.append("missing or empty field: formal_targets")
    for field in (
        "retrieval_queries",
        "gap_taxonomy",
        "critic_findings",
        "next_actions",
    ):
        if not isinstance(packet.get(field), list):
            errors.append(f"missing or invalid field: {field}")
    if not isinstance(packet.get("proof_search_plan"), Mapping):
        errors.append("missing or invalid field: proof_search_plan")
    lemma_plan = packet.get("lemma_dependency_plan")
    if not isinstance(lemma_plan, list):
        errors.append("missing or invalid field: lemma_dependency_plan")
    else:
        for index, edge in enumerate(lemma_plan):
            if not isinstance(edge, Mapping):
                errors.append(
                    f"lemma_dependency_plan[{index}] must be an object"
                )
                continue
            for endpoint in ("from", "to"):
                if not str(edge.get(endpoint, "") or "").strip():
                    errors.append(
                        f"lemma_dependency_plan[{index}] missing {endpoint}"
                    )
    if packet.get("proof_evidence_status") != FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE:
        errors.append("proof_evidence_status must preserve proposal-only boundary")
    if packet.get("kernel_verified") is not False:
        errors.append("LLM Formalizer packet cannot set kernel_verified=true")
    if packet.get("full_frontier_theorem_proved") is not False:
        errors.append("LLM Formalizer packet cannot set full_frontier_theorem_proved=true")
    for row in packet.get("formal_targets", []) or []:
        if not isinstance(row, Mapping):
            errors.append("formal_targets entries must be objects")
            continue
        if not str(row.get("id", "")).strip():
            errors.append("formal target missing id")
        if str(row.get("expected_status", "OPEN")) not in {"OPEN", "FORMAL_GAP", "NEEDS_KERNEL_CHECK"}:
            errors.append(f"unsupported formal target expected_status: {row.get('expected_status')}")
        errors.extend(
            _formal_target_role_contract_errors(row, require_role=False)
        )
        forbidden = _contains_forbidden_proof_claim(row)
        if forbidden:
            errors.append(f"formal target contains forbidden proof claim: {forbidden}")
    for row in packet.get("proof_bank_obligation_requests", []) or []:
        if not isinstance(row, Mapping):
            errors.append("proof_bank_obligation_requests entries must be objects")
            continue
        if not str(row.get("obligation_id", "")).strip():
            errors.append("proof_bank_obligation_requests entry missing obligation_id")
        priority = str(row.get("verification_priority", "medium") or "medium")
        if priority not in {"high", "medium", "low"}:
            errors.append(f"unsupported proof_bank_obligation_requests priority: {priority}")
        forbidden = _contains_forbidden_proof_claim(row)
        if forbidden:
            errors.append(f"proof_bank_obligation_requests entry contains forbidden proof claim: {forbidden}")
    for row in packet.get("source_to_bridge_premise_derivation_candidates", []) or []:
        if not isinstance(row, Mapping):
            errors.append("source_to_bridge_premise_derivation_candidates entries must be objects")
            continue
        canonical_candidate_source = str(
            row.get("premise_derivation_candidate_lean_source", "") or ""
        ).strip()
        candidate_source = _source_to_bridge_candidate_lean_source(row)
        premise_names = [
            str(value).strip()
            for value in row.get("premise_names", []) or []
            if str(value).strip()
        ] if isinstance(row.get("premise_names", []), list | tuple | set) else []
        if not str(row.get("premise_name", "")).strip() and not premise_names:
            errors.append(
                "source_to_bridge_premise_derivation_candidates entry missing "
                "premise_name or premise_names"
            )
        if not candidate_source.strip():
            errors.append(
                "source_to_bridge_premise_derivation_candidates entry missing Lean candidate source"
            )
        elif not canonical_candidate_source:
            errors.append(
                "source_to_bridge_premise_derivation_candidates entry must provide "
                "Lean source in canonical field "
                "premise_derivation_candidate_lean_source"
            )
        declaration_errors = _source_to_bridge_candidate_declaration_contract_errors(row)
        errors.extend(declaration_errors)
        if not _source_to_bridge_candidate_has_source_binding_contract(row):
            errors.append(
                "source_to_bridge_premise_derivation_candidates entry missing "
                "source-binding contract metadata; include a "
                "source_to_bridge_premise_derivation_candidate_request_id/object, "
                "or a source_to_bridge_grouped_premise_derivation_candidate_request_id/object "
                "from the immutable runtime request"
            )
        forbidden = _contains_forbidden_proof_claim(row)
        if forbidden:
            errors.append(
                "source_to_bridge_premise_derivation_candidates entry contains "
                f"forbidden proof claim: {forbidden}"
            )
    for index, row in enumerate(packet.get("pseudo_formal_proof_packets", []) or []):
        if not isinstance(row, Mapping):
            errors.append("pseudo_formal_proof_packets entries must be objects")
            continue
        for error in validate_pseudo_formal_packet(row):
            errors.append(f"pseudo_formal_proof_packets[{index}] {error}")
    errors.extend(_phantom_source_to_bridge_next_action_errors(packet))
    forbidden_packet = _contains_forbidden_proof_claim(packet)
    if forbidden_packet:
        errors.append(f"packet contains forbidden proof claim: {forbidden_packet}")
    return sorted(set(errors))


def _source_to_bridge_candidate_declaration_contract_errors(
    row: Mapping[str, Any],
) -> list[str]:
    scalar_names = tuple(
        dict.fromkeys(
            str(row.get(key, "") or "").strip()
            for key in (
                "premise_candidate_declaration_name",
                "source_to_bridge_premise_candidate_declaration_name",
            )
            if str(row.get(key, "") or "").strip()
        )
    )
    raw_grouped_names = row.get("premise_candidate_declaration_names", [])
    if not isinstance(raw_grouped_names, list | tuple):
        return [
            "source_to_bridge_premise_derivation_candidates "
            "premise_candidate_declaration_names must be an array"
        ]
    grouped_names = tuple(
        str(value).strip()
        for value in raw_grouped_names
        if str(value).strip()
    )
    raw_premise_names = row.get("premise_names", [])
    if not isinstance(raw_premise_names, list | tuple):
        return [
            "source_to_bridge_premise_derivation_candidates premise_names "
            "must be an array"
        ]
    premise_names = tuple(
        str(value).strip()
        for value in raw_premise_names
        if str(value).strip()
    )
    if len(grouped_names) != len(set(grouped_names)):
        return [
            "source_to_bridge_premise_derivation_candidates grouped declaration "
            "identities must be unique"
        ]
    if len(premise_names) != len(set(premise_names)):
        return [
            "source_to_bridge_premise_derivation_candidates premise_names must "
            "be unique"
        ]
    if len(premise_names) > 1:
        if len(grouped_names) != len(premise_names):
            return [
                "grouped source_to_bridge_premise_derivation_candidates entry "
                "must provide one structured premise_candidate_declaration_names "
                "identity per premise_name"
            ]
        if scalar_names and any(name not in grouped_names for name in scalar_names):
            return [
                "grouped source_to_bridge_premise_derivation_candidates entry has "
                "a scalar declaration identity outside premise_candidate_declaration_names"
            ]
        row_names = grouped_names
    else:
        row_names = scalar_names or grouped_names
    if not row_names:
        return [
            "source_to_bridge_premise_derivation_candidates entry missing "
            "structured premise candidate declaration identity; AgentRuntime does not "
            "infer declaration identity by parsing generated Lean source"
        ]
    if len(premise_names) <= 1 and len(row_names) != 1:
        return [
            "source_to_bridge_premise_derivation_candidates entry has conflicting "
            "structured premise candidate declaration identities: "
            + ", ".join(row_names)
        ]

    request_names = _source_to_bridge_candidate_request_declaration_names(row)
    if (
        len(premise_names) > 1
        and request_names
        and row_names != request_names
    ):
        return [
            "grouped source_to_bridge_premise_derivation_candidates declaration "
            "identities must preserve runtime request order"
        ]
    unknown_names = set(row_names) - set(request_names) if request_names else set()
    if unknown_names:
        return [
            "source_to_bridge_premise_derivation_candidates structured premise "
            "candidate declaration identity does not match the runtime request: "
            + ", ".join(sorted(unknown_names))
            + " not in "
            + ", ".join(request_names)
        ]
    return []


def _source_to_bridge_candidate_request_declaration_names(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    names: list[str] = []

    def add_value(value: Any) -> None:
        text = str(value or "").strip()
        if text:
            names.append(text)

    def add_request(request: Mapping[str, Any]) -> None:
        add_value(request.get("premise_candidate_declaration_name", ""))
        add_value(
            request.get("source_to_bridge_premise_candidate_declaration_name", "")
        )
        generated = default_premise_candidate_declaration_name(request)
        if generated:
            names.append(generated)

    single_request = row.get("source_to_bridge_premise_derivation_candidate_request", {})
    if isinstance(single_request, Mapping):
        add_request(single_request)

    grouped_request = row.get(
        "source_to_bridge_grouped_premise_derivation_candidate_request",
        {},
    )
    if isinstance(grouped_request, Mapping):
        for key in (
            "premise_candidate_declaration_names",
            "per_premise_candidate_requests",
        ):
            raw_rows = grouped_request.get(key, [])
            if not isinstance(raw_rows, list | tuple):
                continue
            for item in raw_rows:
                if isinstance(item, Mapping):
                    add_request(item)
                else:
                    add_value(item)
    return tuple(dict.fromkeys(name for name in names if name))


def _phantom_source_to_bridge_next_action_errors(
    packet: Mapping[str, Any],
) -> list[str]:
    """Reject next actions that point at nonexistent source-to-bridge work items."""

    candidates = [
        row
        for row in packet.get("source_to_bridge_premise_derivation_candidates", [])
        or []
        if isinstance(row, Mapping)
    ]
    candidate_names: set[str] = set()
    for row in candidates:
        for key in (
            "candidate_id",
            "id",
            "premise_name",
            "premise_candidate_declaration_name",
            "target_lean_declaration",
        ):
            value = str(row.get(key, "") or "").strip()
            if value:
                candidate_names.add(value.lower())
        premise_names = row.get("premise_names", [])
        if isinstance(premise_names, list | tuple | set):
            candidate_names.update(
                str(value).strip().lower()
                for value in premise_names
                if str(value).strip()
            )
        declaration_names = row.get("premise_candidate_declaration_names", [])
        if isinstance(declaration_names, list | tuple | set):
            candidate_names.update(
                str(value).strip().lower()
                for value in declaration_names
                if str(value).strip()
            )

    errors: list[str] = []
    for action in packet.get("next_actions", []) or []:
        if not isinstance(action, Mapping):
            continue
        action_text = " ".join(
            str(action.get(key, "") or "")
            for key in ("owner_agent", "action", "acceptance_gate")
        ).lower()
        if "source_to_bridge_premise_derivation_candidates" not in action_text:
            continue
        requests_execution = any(
            marker in action_text
            for marker in (
                "run ",
                "check",
                "compile",
                "verify",
                "promote",
                "kernel",
                "local lean",
                "axle",
            )
        )
        if not requests_execution:
            continue
        if not candidates:
            errors.append(
                "next_actions reference source_to_bridge_premise_derivation_candidates "
                "but packet contains no source_to_bridge_premise_derivation_candidates "
                "entries; emit a real candidate object or rewrite the action as a "
                "FORMAL_GAP/proof-bank dependency task"
            )
            continue
        if " entry " in action_text and not any(
            name and name in action_text for name in candidate_names
        ):
            errors.append(
                "next_actions reference a source_to_bridge_premise_derivation_candidates "
                "entry that does not match any emitted candidate id or premise name"
            )
    return errors


def _feedback_requires_formalizer_lean_candidate(
    feedback: Mapping[str, Any],
) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    contracts = (
        feedback,
        feedback.get("architect_evidence_contract", {}),
        feedback.get("runtime_requested_evidence_contract", {}),
        feedback.get("input_summary", {}),
    )
    for contract in contracts:
        if (
            isinstance(contract, Mapping)
            and contract.get("capability_eval_requires_formalizer_lean_candidate")
            is True
        ):
            return True
    return False


def _feedback_contract_flag(feedback: Mapping[str, Any] | None, flag: str) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    sources: list[Mapping[str, Any]] = [feedback]
    for key in (
        "architect_evidence_contract",
        "runtime_requested_evidence_contract",
        "input_summary",
    ):
        value = feedback.get(key, {})
        if isinstance(value, Mapping):
            sources.append(value)
    input_summary = feedback.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        for key in ("architect_evidence_contract", "runtime_requested_evidence_contract"):
            value = input_summary.get(key, {})
            if isinstance(value, Mapping):
                sources.append(value)
    return any(source.get(flag) is True for source in sources)


def _feedback_requires_source_grounded_exact_semantic_authoring_handoff(
    feedback: Mapping[str, Any] | None,
) -> bool:
    return _feedback_contract_flag(
        feedback,
        "capability_eval_requires_exact_semantic_definition_source_grounded_authoring_handoff",
    )


def _feedback_requires_exact_semantic_candidate_materialization_contract(
    feedback: Mapping[str, Any] | None,
) -> bool:
    return any(
        _feedback_contract_flag(feedback, flag)
        for flag in (
            "capability_eval_requires_exact_semantic_definition_candidate_materializer",
            "capability_eval_requires_exact_semantic_definition_materialized_lean_repair",
            "capability_eval_requires_exact_semantic_definition_materialized_feedback_rows",
        )
    )


def _formalizer_bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"", "0", "false", "no", "none", "null", "off"}:
            return False
        if normalized in {"1", "true", "yes", "on"}:
            return True
    return bool(value)


def _strip_false_pseudo_formal_required_flags(
    value: Any,
    *,
    flag_keys: set[str],
) -> Any:
    if isinstance(value, Mapping):
        stripped: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if key_text in flag_keys and not _formalizer_bool_like(child):
                continue
            stripped[key_text] = _strip_false_pseudo_formal_required_flags(
                child,
                flag_keys=flag_keys,
            )
        return stripped
    if isinstance(value, list | tuple):
        return [
            _strip_false_pseudo_formal_required_flags(child, flag_keys=flag_keys)
            for child in value
        ]
    return value


def _feedback_requires_pseudo_formalization(
    *sources: Mapping[str, Any] | None,
) -> bool:
    """Return true only when a typed runtime contract explicitly requires PF/BV."""

    explicit_flags = {
        "pseudo_formalization_required",
        "requires_pseudo_formalization",
        "requires_pseudo_formal_block_verification",
        "requires_pf_bv",
        "exact_semantic_definition_structural_reformulation_required",
        "source_theorem_exact_semantic_definition_structural_reformulation_required",
        "formalizer_pseudo_formal_packet_component_gate_failure_available",
    }
    for source in sources:
        if not isinstance(source, Mapping) or not source:
            continue
        nested_sources = [
            source,
            source.get("input_summary", {}),
            source.get("architect_evidence_contract", {}),
            source.get("runtime_requested_evidence_contract", {}),
            source.get("proofengineer_repair_context", {}),
        ]
        for nested in nested_sources:
            if not isinstance(nested, Mapping):
                continue
            if any(
                _formalizer_bool_like(nested.get(flag, False))
                for flag in explicit_flags
            ):
                return True
    return False


def _validate_required_pseudo_formalization_packet(
    packet: Mapping[str, Any],
    *,
    environment_feedback: Mapping[str, Any] | None = None,
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    if not _feedback_requires_pseudo_formalization(
        environment_feedback or {},
        proof_bank_runtime_memory_summary or {},
    ):
        return []
    pseudo_packets = [
        row
        for row in packet.get("pseudo_formal_proof_packets", []) or []
        if isinstance(row, Mapping)
    ]
    if not pseudo_packets:
        return [
            "pseudo_formalization_required: proof-body/PF activation feedback "
            "requires at least one pseudo_formal_proof_packets entry with "
            "source-anchored blocks, PF/BV method lineage, and non-proof boundary"
        ]
    validation_errors: list[str] = []
    valid_packets: list[tuple[int, Mapping[str, Any]]] = []
    for index, pseudo_packet in enumerate(pseudo_packets):
        errors = validate_pseudo_formal_packet(pseudo_packet)
        if errors:
            validation_errors.append(
                f"pseudo_formal_proof_packets[{index}] invalid: "
                + "; ".join(errors[:6])
            )
        else:
            valid_packets.append((index, pseudo_packet))
    if not valid_packets:
        return [
            "pseudo_formalization_required: no locally valid "
            "pseudo_formal_proof_packets entry was emitted; "
            + " | ".join(validation_errors[:3])
        ]
    work_order_rows: list[dict[str, Any]] = []
    for _, pseudo_packet in valid_packets:
        work_order_rows.extend(pseudo_formal_block_work_order_rows(pseudo_packet))
    routable_work_order_rows = pseudo_formal_routable_work_order_rows(
        work_order_rows
    )
    required_target_lanes = _required_pseudo_formal_target_lanes(
        environment_feedback or {},
        proof_bank_runtime_memory_summary or {},
    )
    required_lane_review_block_ids = {
        str(row.get("source_block_id", "") or "")
        for row in work_order_rows
        if str(row.get("blocked_target_lane", "") or "")
        in set(required_target_lanes)
    }
    required_lane_review_candidates = [
        row
        for row in routable_work_order_rows
        if str(row.get("row_kind", "") or "")
        == PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND
        and str(row.get("source_block_id", "") or "")
        in required_lane_review_block_ids
    ]
    required_lane_review_rows = [
        row
        for row in required_lane_review_candidates
        if pseudo_formal_work_order_row_has_reviewable_source_anchor(row)
    ]
    if required_lane_review_candidates and not required_lane_review_rows:
        return _pseudo_formal_routing_observation_errors(
            valid_packets,
            required_target_lanes=required_target_lanes,
            status="independent_review_source_context_incomplete",
        )
    if not routable_work_order_rows:
        return _pseudo_formal_routing_observation_errors(
            valid_packets,
            required_target_lanes=required_target_lanes,
            status="no_effective_routable_rows",
        )
    if required_target_lanes:
        target_lane_rows = [
            row
            for row in routable_work_order_rows
            if str(row.get("target_lane", "") or "") in required_target_lanes
            or str(row.get("row_kind", "") or "")
            == PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND
            or row in required_lane_review_rows
        ]
        if not target_lane_rows:
            return _pseudo_formal_routing_observation_errors(
                valid_packets,
                required_target_lanes=required_target_lanes,
                status="required_target_lane_not_observed",
            )
        exact_semantic_rows = [
            row
            for row in target_lane_rows
            if str(row.get("target_lane", "") or "")
            == PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
        ]
        if (
            PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
            in required_target_lanes
            and not exact_semantic_rows
            and not required_lane_review_rows
        ):
            return _pseudo_formal_routing_observation_errors(
                valid_packets,
                required_target_lanes=(
                    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
                ),
                status="required_target_lane_not_observed",
            )
        exact_semantic_row_errors = (
            _required_exact_semantic_work_order_row_errors(exact_semantic_rows)
        )
        if exact_semantic_row_errors:
            return exact_semantic_row_errors
    return []


def _pseudo_formal_routing_observation_errors(
    valid_packets: Sequence[tuple[int, Mapping[str, Any]]],
    *,
    required_target_lanes: Sequence[str],
    status: str,
) -> list[str]:
    """Return bounded tool observations without prescribing a packet repair."""

    packet_rows: list[tuple[int, Mapping[str, Any], list[dict[str, Any]]]] = []
    all_rows: list[dict[str, Any]] = []
    for packet_index, pseudo_packet in valid_packets:
        rows = pseudo_formal_block_work_order_rows(pseudo_packet)
        packet_rows.append((packet_index, pseudo_packet, rows))
        all_rows.extend(rows)
    routable_rows = pseudo_formal_routable_work_order_rows(all_rows)
    summary = {
        "status": status,
        "required_target_lanes": sorted(
            {str(value) for value in required_target_lanes if str(value).strip()}
        ),
        "observed_routable_target_lanes": sorted(
            {
                str(row.get("target_lane", "") or "")
                for row in routable_rows
                if str(row.get("target_lane", "") or "").strip()
            }
        ),
        "observed_routable_row_kinds": sorted(
            {
                str(row.get("row_kind", "") or "")
                for row in routable_rows
                if str(row.get("row_kind", "") or "").strip()
            }
        ),
    }
    errors = [
        "pseudo_formalization_required: routing_observation="
        + json.dumps(summary, sort_keys=True, separators=(",", ":"))
    ]

    block_observations: list[tuple[bool, int, int, dict[str, Any]]] = []
    required_lane_set = set(summary["required_target_lanes"])
    for packet_index, pseudo_packet, rows in packet_rows:
        blocks = pseudo_packet.get("blocks", []) or []
        for block_index, block in enumerate(blocks):
            if not isinstance(block, Mapping):
                continue
            block_id = str(block.get("block_id", "") or "")
            emitted_rows = [
                row
                for row in rows
                if str(row.get("source_block_id", "") or "") == block_id
            ]
            emitted_routable_rows = pseudo_formal_routable_work_order_rows(emitted_rows)
            blocked_target_lanes = sorted(
                {
                    str(row.get("blocked_target_lane", "") or "")
                    for row in emitted_rows
                    if str(row.get("blocked_target_lane", "") or "").strip()
                }
            )
            observation = {
                "block_id": block_id,
                "block_type": str(block.get("block_type", "") or ""),
                "faithfulness_status": str(
                    block.get("faithfulness_status", "") or ""
                ),
                "lean_feasibility": str(block.get("lean_feasibility", "") or ""),
                "semantic_primitive_requirement_count": len(
                    block.get("semantic_primitive_requirements", []) or []
                ),
                "source_anchor_count": len(block.get("source_anchors", []) or []),
                "source_anchor_excerpt_count": sum(
                    1
                    for anchor in block.get("source_anchors", []) or []
                    if isinstance(anchor, Mapping)
                    and str(anchor.get("excerpt", "") or "").strip()
                ),
                "block_verification_verdict": str(
                    (
                        block.get("block_verification", {})
                        if isinstance(block.get("block_verification", {}), Mapping)
                        else {}
                    ).get("verdict", "")
                    or ""
                ),
                "observed_row_kinds": sorted(
                    {
                        str(row.get("row_kind", "") or "")
                        for row in emitted_rows
                        if str(row.get("row_kind", "") or "").strip()
                    }
                ),
                "observed_routable_target_lanes": sorted(
                    {
                        str(row.get("target_lane", "") or "")
                        for row in emitted_routable_rows
                        if str(row.get("target_lane", "") or "").strip()
                    }
                ),
                "observed_blocked_target_lanes": blocked_target_lanes,
            }
            is_relevant = bool(
                required_lane_set.intersection(blocked_target_lanes)
                or required_lane_set.intersection(
                    observation["observed_routable_target_lanes"]
                )
            )
            block_observations.append(
                (is_relevant, packet_index, block_index, observation)
            )

    block_observations.sort(key=lambda row: (not row[0], row[1], row[2]))
    for _, packet_index, block_index, observation in block_observations[:3]:
        errors.append(
            f"pseudo_formal_proof_packets[{packet_index}] blocks[{block_index}] "
            "routing_observation="
            + json.dumps(observation, sort_keys=True, separators=(",", ":"))
        )
    return errors


def _required_exact_semantic_work_order_row_errors(
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    if not rows:
        return []
    missing_source_anchors = [
        str(row.get("source_block_id", "") or f"row:{index}")
        for index, row in enumerate(rows)
        if not pseudo_formal_work_order_row_has_source_anchor(row)
    ]
    missing_semantic_requirements = [
        str(row.get("source_block_id", "") or f"row:{index}")
        for index, row in enumerate(rows)
        if not pseudo_formal_work_order_row_has_semantic_requirements(row)
    ]
    missing_lineage = [
        str(row.get("source_block_id", "") or f"row:{index}")
        for index, row in enumerate(rows)
        if not pseudo_formal_work_order_row_has_required_lineage(row)
    ]
    errors: list[str] = []
    if missing_source_anchors:
        errors.append(
            "pseudo_formalization_required: source_theorem_exact_semantic_definition "
            "rows must carry source_anchors with a non-empty id or excerpt; missing "
            + ", ".join(missing_source_anchors)
        )
    if missing_semantic_requirements:
        errors.append(
            "pseudo_formalization_required: source_theorem_exact_semantic_definition "
            "rows must carry non-empty semantic_primitive_requirements naming the "
            "primitive/source object to define; missing "
            + ", ".join(missing_semantic_requirements)
        )
    if missing_lineage:
        errors.append(
            "pseudo_formalization_required: source_theorem_exact_semantic_definition "
            "rows must preserve PF work-order lineage; missing "
            + ", ".join(missing_lineage)
        )
    return errors


def _required_pseudo_formal_target_lanes(
    *sources: Mapping[str, Any],
) -> tuple[str, ...]:
    lanes: list[str] = []
    structural_required = False
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        repair_contract = (
            source.get("pseudo_formalization_repair_contract", {})
            if isinstance(
                source.get("pseudo_formalization_repair_contract", {}),
                Mapping,
            )
            else {}
        )
        nested_sources: list[Any] = [
            source,
            repair_contract,
            source.get("input_summary", {}),
            repair_contract.get("input_summary", {}),
        ]
        for memory_key in (
            "formalizer_pseudo_formal_packet_component_gate_failure_memory",
            "formalizer_pseudo_formal_packet_component_gate_feedback_memory",
        ):
            memory_rows = source.get(memory_key, [])
            if isinstance(memory_rows, Sequence) and not isinstance(
                memory_rows,
                (str, bytes, bytearray),
            ):
                nested_sources.extend(
                    row for row in memory_rows if isinstance(row, Mapping)
                )
        for nested in nested_sources:
            if not isinstance(nested, Mapping):
                continue
            structural_required = structural_required or any(
                _formalizer_bool_like(nested.get(flag, False))
                for flag in (
                    "exact_semantic_definition_structural_reformulation_required",
                    (
                        "source_theorem_exact_semantic_definition_"
                        "structural_reformulation_required"
                    ),
                )
            )
            for key in (
                "pseudo_formal_block_routing_target_lanes",
                "target_lanes",
                "required_target_lanes",
                "pseudo_formal_failure_required_target_lanes",
                "pseudo_formal_routable_target_lanes",
            ):
                value = nested.get(key, [])
                if isinstance(value, str):
                    if value.strip():
                        lanes.append(value.strip())
                elif isinstance(value, Sequence) and not isinstance(
                    value,
                    (bytes, bytearray),
                ):
                    lanes.extend(str(item).strip() for item in value if str(item))
    if structural_required and not lanes:
        lanes.extend(
            [
                "source_theorem_exact_semantic_definition",
                "lean_rag",
                "source_to_bridge",
            ]
        )
    return tuple(dict.fromkeys(lane for lane in lanes if lane))


def _truncate_formalizer_text(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)].rstrip() + "..."


def _has_explicit_source_theorem_formal_gap_target(
    formal_targets: Sequence[Mapping[str, Any]],
) -> bool:
    for row in formal_targets:
        if str(row.get("expected_status", "") or "") != "FORMAL_GAP":
            continue
        if str(row.get("lean_statement_sketch", "") or "").strip():
            continue
        provenance = row.get("source_theorem_target_provenance", {})
        if _source_theorem_target_known(provenance) is False:
            continue
        if (
            isinstance(provenance, Mapping)
            and provenance.get("source_theorem_target_known") is True
        ):
            return True
        row_text = " ".join(
            [
                str(row.get("id", "") or ""),
                str(row.get("informal_source", "") or ""),
                str(row.get("reason", "") or ""),
            ]
        ).lower()
        if "source theorem" in row_text:
            return True
    return False


def _source_theorem_target_known(provenance: object) -> bool | None:
    if not isinstance(provenance, Mapping):
        return None
    value = provenance.get("source_theorem_target_known")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    return None


def _validate_capability_eval_formalizer_lean_candidate_packet(
    packet: Mapping[str, Any],
    *,
    environment_feedback: Mapping[str, Any] | None = None,
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Require generated Lean candidate evidence for Formalizer capability evals."""

    formal_targets = [
        row
        for row in packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
    ]
    role_errors = [
        error
        for row in formal_targets
        for error in _formal_target_role_contract_errors(row, require_role=True)
    ]
    candidate_targets = [
        row
        for row in formal_targets
        if str(row.get("lean_statement_sketch", "") or "").strip()
    ]
    source_to_bridge_candidate_targets = [
        row
        for row in packet.get("source_to_bridge_premise_derivation_candidates", [])
        or []
        if isinstance(row, Mapping)
        and _source_to_bridge_candidate_lean_source(row).strip()
    ]
    pending_source_to_bridge_premise_names = (
        _pending_source_to_bridge_premise_names_for_capability_eval(
            environment_feedback=environment_feedback,
            proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
        )
    )
    if not candidate_targets and not source_to_bridge_candidate_targets:
        if _feedback_requires_pseudo_formalization(
            environment_feedback or {},
            proof_bank_runtime_memory_summary or {},
        ) and not _validate_required_pseudo_formalization_packet(
            packet,
            environment_feedback=environment_feedback or {},
            proof_bank_runtime_memory_summary=(
                proof_bank_runtime_memory_summary or {}
            ),
        ):
            return role_errors
        if (
            pending_source_to_bridge_premise_names
            and _packet_has_source_to_bridge_semantic_anchor_blocker(
                packet,
                pending_source_to_bridge_premise_names,
            )
        ):
            return role_errors
        unbound_gap_synthesis = packet.get(
            "source_theorem_formal_gap_synthesis_skipped", {}
        )
        if (
            isinstance(unbound_gap_synthesis, Mapping)
            and unbound_gap_synthesis.get("reason")
            == "source_theorem_gap_requires_explicit_agent_target"
            and not pending_source_to_bridge_premise_names
        ):
            return role_errors
        return [
            *role_errors,
            "capability_eval requires at least one Claude/OpenAI-generated "
            "Lean statement sketch in formal_targets or "
            "source_to_bridge_premise_derivation_candidates"
        ]
    errors: list[str] = list(role_errors)
    for row in candidate_targets:
        target_id = str(row.get("id", "") or "<unnamed>")
        expected_status = str(row.get("expected_status", "") or "")
        if expected_status != "NEEDS_KERNEL_CHECK":
            errors.append(
                "capability_eval formal target "
                f"{target_id} must set expected_status=NEEDS_KERNEL_CHECK"
            )
        candidate_declaration = str(
            row.get("candidate_lean_declaration", "") or ""
        ).strip()
        if not candidate_declaration:
            errors.append(
                "capability_eval formal target "
                f"{target_id} must provide candidate_lean_declaration for the "
                "exact declaration emitted by lean_statement_sketch"
            )
    if pending_source_to_bridge_premise_names:
        candidate_premise_names = {
            name
            for row in source_to_bridge_candidate_targets
            for name in _source_to_bridge_candidate_premise_names(row)
        }
        missing_premise_names = [
            name
            for name in pending_source_to_bridge_premise_names
            if name not in candidate_premise_names
            and not _packet_has_source_to_bridge_semantic_anchor_blocker(
                packet,
                [name],
            )
        ]
        if missing_premise_names:
            errors.append(
                "capability_eval source-to-bridge premise derivation contract "
                "requires source_to_bridge_premise_derivation_candidates for "
                "pending premise(s): "
                + ", ".join(missing_premise_names)
                + "; helper-only formal_targets do not satisfy this gate"
            )
    for row in source_to_bridge_candidate_targets:
        premise_id = str(
            row.get("premise_name", "")
            or ",".join(str(value) for value in row.get("premise_names", []) or [])
            or "<unnamed>"
        )
        expected_status = str(row.get("expected_status", "") or "")
        if expected_status != "NEEDS_KERNEL_CHECK":
            errors.append(
                "capability_eval source-to-bridge candidate "
                f"{premise_id} must set expected_status=NEEDS_KERNEL_CHECK"
            )
    return errors


def _source_theorem_exact_semantic_definition_gate_active(
    *,
    environment_feedback: Mapping[str, Any] | None = None,
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
) -> bool:
    """Return true when exact source theorem proof work is blocked by semantics.

    Candidate materialization is useful only after source theorem identity and
    exact semantic definitions are reviewed enough for proof-body/signature
    work. When the runtime has an active semantic-definition gate, the
    Formalizer should emit a FORMAL_GAP/source-to-bridge support lane instead
    of inventing a broad Lean source theorem artifact.
    """

    sources: list[Mapping[str, Any]] = []
    for source in (proof_bank_runtime_memory_summary, environment_feedback):
        if isinstance(source, Mapping):
            sources.append(source)
            input_summary = source.get("input_summary", {})
            if isinstance(input_summary, Mapping):
                sources.append(input_summary)

    def _flag(name: str) -> bool:
        return any(_formalizer_bool_like(source.get(name)) for source in sources)

    if _flag("source_theorem_exact_proof_body_gate_open_for_kernel_repair") or _flag(
        "source_theorem_ready_for_exact_proof_body"
    ):
        return False

    for source in sources:
        if _formalizer_bool_like(
            source.get("source_theorem_exact_semantic_definition_repair_required")
        ):
            return True
        if (
            str(source.get("recommended_formalizer_target_mode", "") or "")
            == "source_theorem_exact_semantic_definition_repair"
        ):
            return True
        repair_feedback = source.get(
            "source_theorem_exact_semantic_definition_repair_feedback",
            {},
        )
        if isinstance(repair_feedback, Mapping) and (
            _formalizer_bool_like(
                repair_feedback.get(
                    "source_theorem_exact_semantic_definition_repair_required"
                )
            )
            or bool(repair_feedback.get("diagnostics"))
        ):
            return True
        for row in source.get("high_priority_agenda", []) or []:
            if not isinstance(row, Mapping):
                continue
            if str(row.get("id", "") or "") == (
                "formal_gap:source_theorem_exact_semantic_definition_repair"
            ):
                return True
            if str(row.get("trigger", "") or "") in {
                "SOURCE_THEOREM_EXACT_SEMANTIC_DEFINITION_REVIEW_REQUIRED",
                "EXACT_SOURCE_SEMANTIC_DEFINITION_TYPECHECKED_SEMANTIC_REVIEW_REQUIRED",
            }:
                return True
        for row in source.get("formal_blocker_resource_requests", []) or []:
            if not isinstance(row, Mapping):
                continue
            source_name = str(row.get("source", "") or "")
            blocker_kind = str(row.get("blocker_kind", "") or "")
            if "exact_semantic_definition" in source_name:
                return True
            if blocker_kind in {
                "source_theorem_exact_semantic_definition_repair_required",
                "typechecked_exact_semantic_definition_candidate_review_required",
                "LEAN_IMPORT_PREFIX_UNAVAILABLE_IN_PROJECT",
            }:
                return True
            if "EXACT_SEMANTIC_DEFINITION" in blocker_kind:
                return True
        for row in source.get(
            "source_theorem_exact_semantic_definition_typechecked_candidates",
            [],
        ) or []:
            if not isinstance(row, Mapping):
                continue
            gate_status = str(row.get("proof_body_gate_status", "") or "")
            evidence_status = str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            )
            queue_status = str(row.get("runtime_queue_status", "") or "")
            if (
                "SEMANTIC_REVIEW_REQUIRED" in gate_status
                or "REVIEW_REQUIRED" in evidence_status
                or "EXACT_SEMANTIC_DEFINITION" in queue_status
            ):
                return True
    return False


def _formal_target_materialization_identity_tokens(
    row: Mapping[str, Any],
) -> set[str]:
    provenance = (
        row.get("source_theorem_target_provenance", {})
        if isinstance(row.get("source_theorem_target_provenance", {}), Mapping)
        else {}
    )
    tokens: list[str] = []
    for source in (row, provenance):
        for key in (
            "id",
            "target_id",
            "target_ids",
            "target_theorem_goal_ids",
            "target_theorem_name",
            "target_lean_declaration",
            "source_theorem_goal_id",
            "source_theorem_goal_ids",
            "source_formal_target_id",
        ):
            value = source.get(key)
            if isinstance(value, list | tuple | set):
                tokens.extend(str(item).strip() for item in value)
            else:
                tokens.append(str(value or "").strip())
    return {token for token in tokens if token}



def _pending_source_to_bridge_premise_names_for_capability_eval(
    *,
    environment_feedback: Mapping[str, Any] | None = None,
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    contracts: list[Mapping[str, Any]] = []
    for source in (proof_bank_runtime_memory_summary, environment_feedback):
        if not isinstance(source, Mapping):
            continue
        contracts.append(source)
        input_summary = source.get("input_summary", {})
        if isinstance(input_summary, Mapping):
            contracts.append(input_summary)
            nested_input_feedback = input_summary.get(
                "source_to_bridge_premise_derivation_feedback",
                {},
            )
            if isinstance(nested_input_feedback, Mapping):
                contracts.append(nested_input_feedback)
        nested_feedback = source.get("source_to_bridge_premise_derivation_feedback", {})
        if isinstance(nested_feedback, Mapping):
            contracts.append(nested_feedback)

    required = False
    premise_names: list[str] = []
    for contract in contracts:
        required = required or bool(
            contract.get("source_to_bridge_premise_derivation_required", False)
        )
        required = required or str(
            contract.get("recommended_formalizer_target_mode", "") or ""
        ) == "source_to_bridge_premise_derivation_required"
        pending_names = _string_list_values(
            contract,
            "source_to_bridge_premise_derivation_pending_premise_names",
            "pending_premise_names",
        )
        if pending_names:
            required = True
            premise_names.extend(pending_names)
        for row_key in (
            "source_to_bridge_premise_derivation_diagnostics",
            "diagnostics",
            "source_to_bridge_metadata_authoring_candidate_requests",
            "source_to_bridge_premise_derivation_candidate_requests",
        ):
            rows = contract.get(row_key, [])
            if not isinstance(rows, list | tuple):
                continue
            if rows:
                required = True
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                premise_names.extend(_source_to_bridge_candidate_premise_names(row))

    premise_names = list(dict.fromkeys(name for name in premise_names if name))
    if not premise_names or not required:
        return []
    return premise_names


def _source_to_bridge_candidate_premise_names(row: Mapping[str, Any]) -> list[str]:
    names = _string_list_values(
        row,
        "premise_name",
        "premise_names",
        "source_to_bridge_premise_name",
        "source_to_bridge_premise_names",
    )
    for nested_key in (
        "source_to_bridge_premise_derivation_candidate_request",
        "source_to_bridge_grouped_premise_derivation_candidate_request",
    ):
        nested = row.get(nested_key, {})
        if isinstance(nested, Mapping):
            names.extend(
                _string_list_values(
                    nested,
                    "premise_name",
                    "premise_names",
                    "source_to_bridge_premise_name",
                    "source_to_bridge_premise_names",
                )
            )
    return list(dict.fromkeys(name for name in names if name))


def _source_to_bridge_candidate_lean_source(row: Mapping[str, Any]) -> str:
    for key in (
        "premise_derivation_candidate_lean_source",
        "lean_statement_sketch",
        "candidate_lean_source",
        "lean_source",
        "lean_code",
        "premise_candidate_lean_source",
        "premise_lean_source",
        "source",
    ):
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _string_list_values(row: Mapping[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        raw = row.get(key)
        candidates = raw if isinstance(raw, list | tuple | set) else [raw]
        for value in candidates:
            if isinstance(value, Mapping):
                text = str(value.get("name", "") or "").strip()
            else:
                text = str(value or "").strip()
            if text:
                values.append(text)
    return values


def _normalize_formalizer_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    backend_provider_name: str,
    raw_response: str,
    theory_packet: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
    environment_feedback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    del proof_bank_runtime_memory_summary, environment_feedback
    body = deepcopy(dict(payload))
    pseudo_formal_rows = body.get("pseudo_formal_proof_packets")
    if isinstance(pseudo_formal_rows, list):
        body["pseudo_formal_proof_packets"] = [
            bind_model_pseudo_formal_packet_runtime_envelope(row)
            if isinstance(row, Mapping)
            else deepcopy(row)
            for row in pseudo_formal_rows
        ]
    body["proof_evidence_status"] = FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE
    body["proof_evidence_boundary"] = FORMALIZER_BOUNDARY
    body["kernel_verified"] = False
    body["full_frontier_theorem_proved"] = False
    body["theory_trace_consumption_contract"] = theory_trace_consumption_contract(
        theory_packet,
        consumer_subsystem="FormalizerProofEngineer",
    )
    body["theory_trace_alignment_contract"] = theory_trace_alignment_contract(
        theory_packet,
        body.get("theory_trace_alignment", {}),
        consumer_subsystem="FormalizerProofEngineer",
    )
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "backend_provider": backend_provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
        }
    )[:24]
    return {
        "schema_version": FORMALIZER_SCHEMA_VERSION,
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": f"formalizer_proposal:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMFormalizerProofEngineerAgent",
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
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _packet_has_source_to_bridge_semantic_anchor_blocker(
    packet: Mapping[str, Any],
    premise_names: Sequence[str] = (),
) -> bool:
    wanted = {str(name).strip() for name in premise_names if str(name).strip()}
    blocker_premises: set[str] = set()
    for row in packet.get("dropped_semantic_anchor_source_to_bridge_candidates", []) or []:
        if not isinstance(row, Mapping):
            continue
        for name in _source_to_bridge_candidate_premise_names(row):
            blocker_premises.add(name)
        if str(row.get("premise_name", "") or "").strip():
            blocker_premises.add(str(row.get("premise_name", "") or "").strip())
    for row in packet.get("gap_taxonomy", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("kind", "") or "") != "source_to_bridge_semantic_anchor_blocker":
            continue
        for name in _source_to_bridge_candidate_premise_names(row):
            blocker_premises.add(name)
        if str(row.get("premise_name", "") or "").strip():
            blocker_premises.add(str(row.get("premise_name", "") or "").strip())
    if not wanted:
        return bool(blocker_premises)
    return bool(blocker_premises) and wanted.issubset(blocker_premises)






def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM Formalizer/ProofEngineer")


def _proof_bank_catalog_from_theorem_goals(theorem_goals: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for goal in theorem_goals:
        if not isinstance(goal, Mapping):
            continue
        goal_id = str(goal.get("id", "") or "")
        for obligation_id in goal.get("proof_obligations", []) or []:
            obligation = str(obligation_id or "").strip()
            if not obligation or obligation in seen:
                continue
            seen.add(obligation)
            rows.append(
                {
                    "obligation_id": obligation,
                    "candidate_rank": len(rows) + 1,
                    "candidate_sources": [f"theorem_goal:{goal_id}" if goal_id else "theorem_goal"],
                    "catalog_scope": "theorem_goal_declared_obligation",
                }
            )
    return rows


def _compact_rows(
    rows: Any,
    *,
    keys: tuple[str, ...],
    limit: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list | tuple):
        return []
    compact: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, Mapping):
            compact.append(_compact_mapping(row, keys=keys))
        else:
            compact.append({"value": _compact_value(row)})
        if len(compact) >= limit:
            break
    return compact


def _compact_mapping(row: Mapping[str, Any], *, keys: tuple[str, ...]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key in keys:
        if _is_runtime_authored_prescriptive_field(key):
            continue
        if key not in row or row.get(key) in (None, "", [], {}):
            continue
        if (
            key == "source_to_bridge_grouped_premise_derivation_candidate_request"
            and isinstance(row.get(key), Mapping)
        ):
            compact[key] = _compact_grouped_premise_derivation_candidate_request(
                row[key]
            )
        elif (
            key == "source_to_bridge_premise_derivation_candidate_request"
            and isinstance(row.get(key), Mapping)
        ):
            compact[key] = _compact_premise_derivation_candidate_request(row[key])
        else:
            compact[key] = _compact_value_for_key(key, row.get(key))
    return compact


def _source_to_bridge_premise_candidate_artifact_path(
    row: Mapping[str, Any],
) -> str:
    for key in (
        "premise_candidate_artifact_path",
        "source_to_bridge_premise_candidate_artifact_path",
    ):
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _source_to_bridge_candidate_skeleton_lean_source_excerpt(
    row: Mapping[str, Any],
    *,
    max_lines: int = 80,
    max_chars: int = 8000,
) -> str:
    for key in (
        "premise_derivation_candidate_skeleton_lean_source_excerpt",
        "premise_candidate_skeleton_lean_source_excerpt",
    ):
        value = str(row.get(key, "") or "").strip()
        if value:
            return value[:max_chars]

    artifact_path = _source_to_bridge_premise_candidate_artifact_path(row)
    if not artifact_path:
        return ""
    path = Path(artifact_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(text.splitlines()[:max_lines])[:max_chars]


def _compact_premise_derivation_candidate_request(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    compact = _compact_mapping(
        row,
        keys=(
            "artifact_kind",
            "candidate_request_id",
            "premise_name",
            "premise_target_type",
            "premise_target_source",
            "source_to_bridge_premise_target_type",
            "adapter_instantiation_group_id",
            "required_bridge_premise_names_for_shared_instantiation",
            "premise_candidate_declaration_name",
            "premise_candidate_artifact_path",
            "source_to_bridge_premise_candidate_artifact_path",
            "premise_derivation_candidate_skeleton_lean_source_excerpt",
            "premise_candidate_skeleton_lean_source_excerpt",
            "target_theorem_name",
            "target_lean_declaration",
            "required_formalizer_output_key",
            "required_candidate_fields",
            "exact_source_theorem_binders",
            "proof_body_goal_context",
            "proof_body_goal_binder_names",
            "proof_body_goal_conclusion",
            "source_to_bridge_premise_goal_context",
            "source_to_bridge_premise_goal_binder_names",
            "source_to_bridge_premise_goal_conclusion",
            "proof_evidence_status",
        ),
    )
    artifact_path = _source_to_bridge_premise_candidate_artifact_path(row)
    if artifact_path:
        compact.setdefault("premise_candidate_artifact_path", artifact_path)
    excerpt = _source_to_bridge_candidate_skeleton_lean_source_excerpt(row)
    if excerpt:
        compact.setdefault(
            "premise_derivation_candidate_skeleton_lean_source_excerpt",
            excerpt,
        )
    return compact


def _compact_grouped_premise_derivation_candidate_request(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    compact = _compact_mapping(
        row,
        keys=(
            "artifact_kind",
            "grouped_candidate_request_id",
            "adapter_instantiation_group_id",
            "premise_names",
            "required_bridge_premise_names_for_shared_instantiation",
            "proof_body_goal_context",
            "proof_body_goal_binder_names",
            "proof_body_goal_conclusion",
            "source_to_bridge_premise_goal_context",
            "source_to_bridge_premise_goal_binder_names",
            "source_to_bridge_premise_goal_conclusion",
            "premise_candidate_declaration_names",
            "premise_candidate_artifact_paths",
            "premise_derivation_candidate_skeleton_lean_source_excerpts",
            "target_theorem_name",
            "target_lean_declaration",
            "required_formalizer_output_key",
            "required_candidate_fields",
            "exact_source_theorem_binders",
            "proof_evidence_status",
        ),
    )
    if isinstance(row.get("per_premise_candidate_requests"), list):
        compact["per_premise_candidate_requests"] = _compact_rows(
            row.get("per_premise_candidate_requests", []),
            keys=(
                "candidate_request_id",
                "premise_name",
                "premise_target_type",
                "premise_target_source",
                "premise_candidate_declaration_name",
                "premise_candidate_artifact_path",
                "source_to_bridge_premise_candidate_artifact_path",
                "premise_derivation_candidate_skeleton_lean_source_excerpt",
                "premise_candidate_skeleton_lean_source_excerpt",
                "proof_body_goal_binder_names",
                "proof_body_goal_conclusion",
            ),
            limit=6,
        )
    return compact


def _model_owned_formalizer_feedback_instructions(
    proof_memory_summary: Mapping[str, Any],
    runtime_environment_feedback: Mapping[str, Any],
) -> list[str]:
    if not proof_memory_summary and not runtime_environment_feedback:
        return []

    return [
        (
            "Treat prior runtime memory and environment feedback as observations, not "
            "as a runtime-authored proof or edit plan. They are typed tool results; "
            "inspect the complete current "
            "candidate, exact target statement, raw Lean/LSP/compiler output, proof "
            "state, retrieved declarations, and independent reviewer findings that are "
            "present. Choose and author every definition, import, lemma decomposition, "
            "tactic, and source change yourself; choose the next Lean candidate yourself. "
            "AgentRuntime supplies no Python-authored Lean grammar and does not prescribe "
            "field-specific corrections."
        ),
        (
            "Generate a complete replacement packet or candidate for the unchanged "
            "task-bound target. Preserve exact declaration, artifact, request, parent, "
            "and target identities supplied by the runtime. Do not weaken the theorem "
            "or promote search, review, compilation, or helper results to source-theorem "
            "proof evidence; only the configured local Lean/kernel gate may do that."
        ),
        (
            "Use the provider output schema and typed routing fields to return the next "
            "candidate. When the available source and verifier observations are "
            "insufficient, return a precise typed blocker naming the missing evidence "
            "instead of inventing it. Runtime mode labels and legacy recommendation "
            "fields are control-plane history, not instructions for how to write Lean."
        ),
    ]


def _complete_lean_candidate_revision_feedback(
    feedback: Mapping[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    """Carry complete producer, verifier, retrieval, and reviewer observations."""

    if not isinstance(feedback, Mapping):
        return {}
    payload = _complete_formalizer_environment_observations(feedback)
    if candidate_id:
        payload["active_candidate_id"] = candidate_id
    return payload


def _complete_formalizer_environment_observations(
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Transport the complete environment packet without interpreting its fields."""

    if not isinstance(feedback, Mapping):
        return {}
    return deepcopy(dict(feedback))


def _theory_trace_downstream_alignment_feedback(
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
        "trigger": (
            input_summary.get("trigger", "")
            or contract.get("trigger", "")
            or "RUNTIME_THEORY_TRACE_DOWNSTREAM_ALIGNMENT_MISSING"
        ),
        "target_consumer_subsystem": (
            source.get("target_consumer_subsystem", "")
            or input_summary.get("target_consumer_subsystem", "")
            or contract.get("target_consumer_subsystem", "")
        ),
        "failure_classifications": (
            source.get(
                "failure_classifications",
                input_summary.get(
                    "failure_classifications",
                    contract.get("failure_classifications", []),
                ),
            )
            or []
        ),
        "target_ids": (
            source.get(
                "target_ids",
                input_summary.get("target_ids", contract.get("target_ids", [])),
            )
            or []
        ),
        "acceptance_gate": (
            source.get("acceptance_gate", "") or contract.get("acceptance_gate", "")
        ),
        "proof_evidence_status": (
            source.get("proof_evidence_status", "")
            or contract.get("proof_evidence_status", "")
        ),
        "boundary": source.get("boundary", ""),
    }


def _compact_proof_bank_runtime_memory_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    raw_row = row
    observation_row = model_observations_without_repair_recipes(row)
    if not isinstance(observation_row, Mapping):
        return {}
    row = observation_row
    keys = (
        "artifact_kind",
        "proof_bank_bridge_catalog_size",
        "proof_bank_bridge_catalog_exhausted_by_memory",
        "theorem_reduction_closure_required",
        "recommended_formalizer_target_mode",
        "remaining_theorem_goal_ids",
        "remaining_unverified_proof_bank_obligation_ids",
        "memory_kernel_verified_proof_obligation_ids",
        "memory_kernel_verified_theorem_reduction_closure_work_order_ids",
        "memory_kernel_verified_theorem_reduction_closure_target_ids",
        "memory_kernel_verified_theorem_reduction_closure_declarations",
        "memory_verified_theorem_reduction_closure_artifact_paths",
        "memory_kernel_verified_theorem_reduction_closure_signature_excerpts",
        "memory_kernel_verified_theorem_reduction_closure_goal_ids",
        "memory_kernel_verified_source_theorem_semantic_support_obligation_ids",
        "memory_kernel_verified_source_theorem_semantic_primitive_ids",
        "memory_kernel_verified_source_theorem_semantic_definition_ids",
        "source_theorem_semantic_primitive_support_already_kernel_verified",
        "source_theorem_semantic_support_only",
        "semantic_closure_status",
        "placeholder_definition_status",
        "source_theorem_ready_for_exact_proof_body",
        "required_source_theorem_semantic_primitive_support_ids",
        "missing_source_theorem_semantic_primitive_support_ids",
        "unresolved_source_theorem_semantic_primitive_placeholder_symbols",
        "source_theorem_promotion_ready_but_unproved",
        "source_theorem_promotion_ready_but_unproved_target_names",
        "source_theorem_integrator_blocked",
        "source_theorem_integrator_blocked_target_names",
        "source_theorem_integrator_blocker_triggers",
        "source_theorem_exact_candidate_requires_repair",
        "source_theorem_exact_candidate_repair_target_names",
        "source_theorem_exact_candidate_repair_triggers",
        "source_theorem_exact_candidate_failure_classifications",
        "source_theorem_exact_candidate_environment_gap",
        "source_theorem_candidate_materialization_required",
        "source_theorem_candidate_materialization_required_target_names",
        "source_theorem_candidate_materialization_required_target_ids",
        "source_theorem_candidate_materialization_required_statuses",
        "source_theorem_candidate_materialization_missing_formal_symbols",
        "source_theorem_candidate_materialization_contract",
        "source_theorem_exact_semantic_definition_repair_required",
        "source_theorem_exact_semantic_definition_structural_reformulation_required",
        "source_theorem_exact_semantic_definition_structural_reformulation_target_names",
        "source_theorem_exact_semantic_definition_structural_reformulation_placeholder_symbols",
        "pseudo_formalization_required",
        "requires_pseudo_formalization",
        "pseudo_formalization_required_reason",
        "source_theorem_exact_proof_body_repair_required",
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
        "source_theorem_exact_proof_body_gate_open_target_names",
        "formalizer_diagnostic_helper_integration_required",
        "formalizer_diagnostic_helper_memory",
        "source_theorem_exact_proof_body_verified_adapter_context_insufficient",
        "source_theorem_exact_proof_body_verified_adapter_context_insufficient_target_names",
        "source_theorem_proof_body_adapter_required",
        "source_theorem_proof_body_adapter_feedback_available",
        "source_theorem_proof_body_adapter_kernel_verified",
        "kernel_verified_source_theorem_proof_body_adapter_ids",
        "verified_source_theorem_proof_body_adapter_artifact_paths",
        "verified_source_theorem_proof_body_adapter_declarations",
        "source_theorem_proof_body_adapter_feedback_target_names",
        "source_theorem_proof_body_adapter_target_names",
        "source_theorem_proof_body_adapter_unproven_bridge_premises_required",
        "source_theorem_proof_body_adapter_unproven_bridge_premise_target_names",
        "source_theorem_proof_body_adapter_unproven_bridge_premise_names",
        "source_to_bridge_premise_derivation_required",
        "source_to_bridge_premise_derivation_pending_premise_names",
        "source_to_bridge_premise_derivation_verified_premise_names",
        "source_to_bridge_premise_derivation_diagnostics",
        "verified_source_to_bridge_premise_derivation_signature_excerpts",
        "source_to_bridge_metadata_authoring_required",
        "source_to_bridge_metadata_authoring_target_ids",
        "source_to_bridge_metadata_authoring_helper_candidate_ids",
        "source_to_bridge_metadata_authoring_source_formalizer_packet_ids",
        "source_to_bridge_metadata_authoring_statuses",
        "source_to_bridge_metadata_authoring_contract",
        "source_to_bridge_metadata_authoring_diagnostics",
        "source_to_bridge_metadata_authoring_candidate_requests",
        "source_to_bridge_metadata_authoring_request_shells",
        "source_to_bridge_metadata_authoring_complete_candidate_requests_available",
        "source_to_bridge_metadata_authoring_missing_request_fields",
        "formal_gap_next_action_routing_active",
        "formal_gap_next_action_target_ids",
        "formal_gap_proof_bank_expansion_required",
        "formalization_gap_planner_handoff_required",
        "formalization_gap_planner_bridge_ids",
        "formalization_gap_planner_handoff_ids",
        "formalization_gap_planner_standalone_seed_artifact_ids",
        "formalization_gap_planner_execution_plan_stage_ids",
        "formalization_gap_planner_execution_contexts",
        "formal_gap_next_action_acceptance_gates",
        "formal_gap_live_route_planner_contract_repair_required",
        "formal_gap_route_planner_contract_feedback_ids",
        "formal_gap_route_planner_failure_classifications",
        "formal_gap_route_planner_staged_assembly_error_preview",
        "formal_gap_next_action_contract",
        "formal_gap_next_action_diagnostics",
        "pseudo_formal_block_routing_active",
        "pseudo_formal_block_routing_diagnostic_active",
        "n_pseudo_formal_block_routing_memory_rows",
        "n_pseudo_formal_block_routing_effective_memory_rows",
        "n_pseudo_formal_block_routing_diagnostic_memory_rows",
        "pseudo_formal_block_routing_target_lanes",
        "pseudo_formal_block_routing_diagnostic_target_lanes",
        "pseudo_formal_block_routing_target_ids",
        "pseudo_formal_block_routing_work_order_ids",
        "pseudo_formal_block_routing_diagnostic_work_order_ids",
        "pseudo_formal_independent_block_verification_feedback_active",
        "pseudo_formal_independent_block_verification_pending",
        "n_pseudo_formal_independent_block_verification_feedback_rows",
        "n_pseudo_formal_independent_block_verification_pending_rows",
        "pseudo_formal_independent_block_verification_work_order_ids",
        "pseudo_formal_independent_block_verification_verdicts",
        "pseudo_formal_independent_block_verification_feedback_memory",
        "pseudo_formal_independent_block_verification_pending_memory",
        "pseudo_formal_block_routing_contract",
        "pseudo_formal_block_routing_memory_boundary",
        "pseudo_formal_block_routing_memory",
        "pseudo_formal_block_routing_diagnostic_memory",
        "source_theorem_proof_body_adapter_diagnostics",
        "source_theorem_exact_proof_body_repair_target_names",
        "source_theorem_exact_proof_body_repair_diagnostics",
        "source_theorem_exact_semantic_definition_typechecked_candidates",
        "source_theorem_exact_candidate_repair_placeholder_symbols",
        "source_theorem_exact_candidate_repair_diagnostics",
        "exact_source_theorem_binders",
        "required_bridge_premise_names_for_shared_instantiation",
        "source_to_bridge_adapter_instantiation_group_id",
        "source_to_bridge_grouped_premise_derivation_candidate_request_id",
        "exact_goal_shape_obligation_ids",
        "formalizer_lean_candidate_repair_required",
        "formalizer_lean_candidate_proof_state_feedback_available",
        "formalizer_lean_candidate_unbound_proof_state_feedback_available",
        "n_formalizer_lean_candidate_unbound_proof_state_feedback_rows",
        "formalizer_lean_candidate_component_gate_feedback_available",
        "formalizer_pseudo_formal_packet_component_gate_feedback_available",
        "formalizer_pseudo_formal_packet_component_gate_failure_available",
        "formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_available",
        "n_formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_rows",
        "formalizer_lean_candidate_capability_feedback_available",
        "formalizer_runtime_capability_contract_feedback_available",
        "formalizer_lean_candidate_repair_manifest_paths",
        "formalizer_lean_candidate_repair_memory",
        "formalizer_lean_candidate_proof_state_feedback_memory",
        "formalizer_lean_candidate_unbound_proof_state_feedback_memory",
        "formalizer_lean_candidate_component_gate_feedback_memory",
        "formalizer_pseudo_formal_packet_component_gate_feedback_memory",
        "formalizer_pseudo_formal_packet_component_gate_failure_memory",
        "formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_memory",
        "formalizer_lean_candidate_capability_feedback_memory",
        "formalizer_runtime_capability_contract_feedback_memory",
        "critic_high_priority_agenda_ids",
    )
    compact = _compact_mapping(row, keys=keys)
    if "memory_kernel_verified_proof_obligation_ids" in compact:
        values = compact["memory_kernel_verified_proof_obligation_ids"]
        if isinstance(values, list):
            compact["memory_kernel_verified_proof_obligation_ids"] = values[:12]
    if isinstance(row.get("source_theorem_exact_candidate_repair_diagnostics"), list):
        compact["source_theorem_exact_candidate_repair_diagnostics"] = _compact_rows(
            row.get("source_theorem_exact_candidate_repair_diagnostics", []),
            keys=(
                "target_theorem_name",
                "target_lean_declaration",
                "target_declaration_source_excerpt",
                "target_theorem_statement",
                "current_proof_body_excerpt",
                "residual_goal_excerpt",
                "trigger",
                "placeholder_symbol",
                "missing_formal_symbols",
                "typeclass_blockers",
                "failure_classification",
                "structural_reformulation_required",
                "pseudo_formalization_required",
                "runtime_queue_status",
                "validation_errors",
                "retry_validation_errors",
                "source_failed_candidate_packet_id",
                "response_validation_feedback",
                "source_theorem_exact_semantic_definition_structural_reformulation_route",
                "source_lookup_hits",
                "exact_source_theorem_binders",
                "required_bridge_premise_names_for_shared_instantiation",
                "source_to_bridge_adapter_instantiation_group_id",
                "source_to_bridge_grouped_premise_derivation_candidate_request_id",
                "exact_goal_shape_obligation_ids",
                "candidate_artifact_path",
                "definition_only_candidate_artifact_path",
                "diagnostics",
                "semantic_definition_risks",
                "semantic_alignment_blockers",
                "local_definition_lean_compiled",
                "semantic_definition_typecheck_evidence_status",
                "proof_body_gate_status",
                "proof_body_goal_reached",
                "proof_body_attempted",
                "proof_body_attempt_count",
                "proof_body_attempt_summaries",
                "proof_body_goal_excerpt",
            ),
            limit=3,
        )
    if isinstance(row.get("source_theorem_exact_proof_body_repair_diagnostics"), list):
        compact["source_theorem_exact_proof_body_repair_diagnostics"] = _compact_rows(
            row.get("source_theorem_exact_proof_body_repair_diagnostics", []),
            keys=(
                "target_theorem_name",
                "trigger",
                "failure_classification",
                "candidate_artifact_path",
                "proof_body_gate_status",
                "proof_body_goal_reached",
                "proof_body_attempted",
                "proof_body_attempt_count",
                "proof_body_attempt_summaries",
                "proof_body_goal_excerpt",
                "target_declaration_source_excerpt",
                "candidate_source_excerpt",
                "target_theorem_statement",
                "current_proof_body_excerpt",
                "semantic_alignment_blockers",
                "source_theorem_kernel_evidence_eligible",
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
                "exact_goal_shape_obligation_ids",
                "exact_goal_shape_obligations",
                "adapter_kernel_verified",
                "kernel_verified_source_theorem_proof_body_adapter_ids",
                "adapter_candidate_artifact_path",
                "adapter_declaration_name",
                "diagnostics",
            ),
            limit=3,
        )
    if isinstance(row.get("source_theorem_proof_body_adapter_diagnostics"), list):
        compact["source_theorem_proof_body_adapter_diagnostics"] = _compact_rows(
            row.get("source_theorem_proof_body_adapter_diagnostics", []),
            keys=(
                "target_theorem_name",
                "trigger",
                "failure_classification",
                "candidate_artifact_path",
                "adapter_candidate_artifact_path",
                "adapter_declaration_name",
                "verified_source_to_bridge_premise_derivation_artifact_paths",
                "verified_source_to_bridge_premise_derivation_declarations",
                "verified_source_to_bridge_premise_derivation_signature_excerpts",
                "adapter_kernel_verified",
                "adapter_candidate_requires_unproven_bridge_premises",
                "unproven_bridge_premise_names",
                "proof_body_gate_status",
                "runtime_queue_status",
                "proof_body_goal_reached",
                "proof_body_goal_excerpt",
                "proof_body_attempt_summaries",
                "target_declaration_source_excerpt",
                "candidate_source_excerpt",
                "target_theorem_statement",
                "current_proof_body_excerpt",
                "exact_goal_shape_obligation_ids",
                "exact_goal_shape_obligations",
                "semantic_alignment_constraints",
                "semantic_alignment_blockers",
                "source_theorem_kernel_evidence_eligible",
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
                "kernel_verified_theorem_reduction_closure_declarations",
                "verified_theorem_reduction_closure_artifact_paths",
                "kernel_verified_theorem_reduction_closure_signature_excerpts",
                "kernel_verified_theorem_reduction_closure_target_ids",
            ),
            limit=3,
        )
    if isinstance(row.get("source_to_bridge_metadata_authoring_diagnostics"), list):
        compact["source_to_bridge_metadata_authoring_diagnostics"] = _compact_rows(
            row.get("source_to_bridge_metadata_authoring_diagnostics", []),
            keys=(
                "trigger",
                "agenda_id",
                "runtime_queue_status",
                "source_to_bridge_metadata_blocker_status",
                "source_to_bridge_metadata_blocker_kind",
                "target_ids",
                "diagnostic_helper_candidate_ids",
                "source_formalizer_packet_ids",
                "owner_subsystem",
                "target_behavior",
                "acceptance_gate",
                "proof_evidence_status",
            ),
            limit=4,
        )
    if isinstance(row.get("formal_gap_next_action_diagnostics"), list):
        compact["formal_gap_next_action_diagnostics"] = _compact_rows(
            row.get("formal_gap_next_action_diagnostics", []),
            keys=(
                "agenda_id",
                "trigger",
                "route_stage",
                "owner_subsystem",
                "target_ids",
                "formalization_gap_planner_bridge_ids",
                "formalization_gap_planner_handoff_ids",
                "standalone_seed_artifact_ids",
                "formalization_gap_planner_execution_plan_stage_ids",
                "formalization_gap_planner_execution_contexts",
                "target_behavior",
                "acceptance_gate",
                "proof_boundary",
                "proof_evidence_status",
            ),
            limit=4,
        )
    if isinstance(row.get("pseudo_formal_block_routing_memory"), list):
        compact["pseudo_formal_block_routing_memory"] = _compact_rows(
            row.get("pseudo_formal_block_routing_memory", []),
            keys=(
                "learning_task",
                "source_pseudo_formal_work_order_id",
                "source_agenda_id",
                "source_formalizer_proposal_id",
                "source_formalization_manifest_id",
                "source_packet_id",
                "source_theorem_id",
                "source_block_id",
                "source_block_type",
                "source_block_conclusion",
                "block_depth",
                "dependency_scope",
                "dependency_ids",
                "dependency_statement_context",
                "scope_parent_id",
                "inherited_scope",
                "source_block_premises",
                "source_block_proof_text",
                "structural_quality",
                "structural_quality_ok",
                "structural_quality_issues",
                "faithfulness_status",
                "faithfulness_repair_status",
                "block_verification",
                "block_verifier_feedback_id",
                "block_verifier_prompt_packet_id",
                "block_verifier_review_content_fingerprint",
                "block_verification_verifier_provenance",
                "block_verification_independent",
                "independent_block_verification_required",
                "independent_block_verification_status",
                "independent_block_verification_completed",
                "bv_calibration",
                "source_anchors",
                "row_kind",
                "pseudo_formal_routable",
                "target_lane",
                "target_ids",
                "target_theorem_name",
                "semantic_primitive_id",
                "reason",
                "runtime_queue_status",
                "proof_evidence_status",
                "proof_evidence_boundary",
            ),
            limit=6,
        )
    if isinstance(row.get("pseudo_formal_block_routing_diagnostic_memory"), list):
        compact["pseudo_formal_block_routing_diagnostic_memory"] = _compact_rows(
            row.get("pseudo_formal_block_routing_diagnostic_memory", []),
            keys=(
                "learning_task",
                "source_pseudo_formal_work_order_id",
                "source_agenda_id",
                "source_formalizer_proposal_id",
                "source_formalization_manifest_id",
                "source_packet_id",
                "source_theorem_id",
                "source_block_id",
                "source_block_type",
                "source_block_conclusion",
                "block_depth",
                "dependency_scope",
                "dependency_ids",
                "dependency_statement_context",
                "scope_parent_id",
                "inherited_scope",
                "source_block_premises",
                "source_block_proof_text",
                "structural_quality",
                "structural_quality_ok",
                "structural_quality_issues",
                "faithfulness_status",
                "faithfulness_repair_status",
                "block_verification",
                "block_verification_verifier_provenance",
                "block_verification_independent",
                "independent_block_verification_required",
                "independent_block_verification_status",
                "independent_block_verification_completed",
                "bv_calibration",
                "source_anchors",
                "row_kind",
                "pseudo_formal_routable",
                "target_lane",
                "target_ids",
                "target_theorem_name",
                "semantic_primitive_id",
                "reason",
                "runtime_queue_status",
                "proof_evidence_status",
                "proof_evidence_boundary",
            ),
            limit=6,
        )
    if isinstance(
        row.get("pseudo_formal_independent_block_verification_feedback_memory"),
        list,
    ):
        compact["pseudo_formal_independent_block_verification_feedback_memory"] = (
            _compact_rows(
                row.get(
                    "pseudo_formal_independent_block_verification_feedback_memory",
                    [],
                ),
                keys=(
                    "learning_task",
                    "source_pseudo_formal_work_order_id",
                    "source_agenda_id",
                    "source_formalizer_proposal_id",
                    "source_formalization_manifest_id",
                    "source_packet_id",
                    "source_theorem_id",
                    "source_block_id",
                    "source_block_type",
                    "source_block_conclusion",
                    "block_depth",
                    "dependency_scope",
                    "dependency_ids",
                    "dependency_statement_context",
                    "scope_parent_id",
                    "inherited_scope",
                    "source_block_premises",
                    "source_block_proof_text",
                    "structural_quality",
                    "structural_quality_ok",
                    "structural_quality_issues",
                    "faithfulness_status",
                    "faithfulness_repair_status",
                    "block_verification",
                    "block_verifier_feedback_id",
                    "block_verifier_prompt_packet_id",
                    "block_verifier_review_content_fingerprint",
                    "block_verification_verifier_provenance",
                    "block_verification_independent",
                    "independent_block_verification_required",
                    "independent_block_verification_status",
                    "independent_block_verification_completed",
                    "bv_calibration",
                    "source_anchors",
                    "row_kind",
                    "pseudo_formal_routable",
                    "target_lane",
                    "target_ids",
                    "target_theorem_name",
                    "reason",
                    "runtime_queue_status",
                    "proof_evidence_status",
                    "proof_evidence_boundary",
                ),
                limit=6,
            )
        )
    if isinstance(
        row.get("pseudo_formal_independent_block_verification_pending_memory"),
        list,
    ):
        compact["pseudo_formal_independent_block_verification_pending_memory"] = (
            _compact_rows(
                row.get(
                    "pseudo_formal_independent_block_verification_pending_memory",
                    [],
                ),
                keys=(
                    "learning_task",
                    "source_pseudo_formal_work_order_id",
                    "source_agenda_id",
                    "source_packet_id",
                    "source_theorem_id",
                    "source_block_id",
                    "source_block_conclusion",
                    "dependency_statement_context",
                    "source_block_premises",
                    "source_block_proof_text",
                    "structural_quality",
                    "structural_quality_ok",
                    "structural_quality_issues",
                    "block_verification",
                    "block_verification_verifier_provenance",
                    "block_verification_independent",
                    "independent_block_verification_required",
                    "independent_block_verification_status",
                    "row_kind",
                    "target_lane",
                    "target_ids",
                    "target_theorem_name",
                    "runtime_queue_status",
                    "proof_evidence_status",
                    "proof_evidence_boundary",
                ),
                limit=6,
            )
        )
    if isinstance(row.get("source_to_bridge_metadata_authoring_candidate_requests"), list):
        compact["source_to_bridge_metadata_authoring_candidate_requests"] = (
            _compact_rows(
                row.get("source_to_bridge_metadata_authoring_candidate_requests", []),
                keys=(
                    "candidate_request_id",
                    "source_to_bridge_premise_derivation_candidate_request_id",
                    "source_to_bridge_premise_derivation_candidate_request",
                    "premise_name",
                    "premise_names",
                    "target_theorem_name",
                    "target_lean_declaration",
                    "premise_target_type",
                    "premise_candidate_artifact_path",
                    "source_to_bridge_premise_candidate_artifact_path",
                    "premise_derivation_candidate_skeleton_lean_source_excerpt",
                    "premise_candidate_skeleton_lean_source_excerpt",
                    "exact_source_theorem_binders",
                    "missing_required_metadata_fields",
                    "request_complete",
                    "metadata_authoring_status",
                    "proof_evidence_status",
                ),
                limit=4,
            )
        )
    if isinstance(row.get("source_to_bridge_metadata_authoring_request_shells"), list):
        compact["source_to_bridge_metadata_authoring_request_shells"] = _compact_rows(
            row.get("source_to_bridge_metadata_authoring_request_shells", []),
            keys=(
                "candidate_request_id",
                "target_theorem_name",
                "target_lean_declaration",
                "target_theorem_goal_ids",
                "required_candidate_fields",
                "missing_required_metadata_fields",
                "metadata_authoring_status",
                "source_formalizer_packet_id",
                "proof_evidence_status",
            ),
            limit=4,
        )
    if isinstance(row.get("source_to_bridge_premise_derivation_diagnostics"), list):
        compact["source_to_bridge_premise_derivation_diagnostics"] = _compact_rows(
            row.get("source_to_bridge_premise_derivation_diagnostics", []),
            keys=(
                "target_theorem_name",
                "trigger",
                "failure_classification",
                "runtime_queue_status",
                "premise_name",
                "premise_names",
                "premise_derivation_kernel_verified",
                "premise_candidate_artifact_path",
                "premise_candidate_declaration_name",
                "premise_derivation_candidate_skeleton_lean_source_excerpt",
                "premise_candidate_skeleton_lean_source_excerpt",
                "premise_candidate_signature_excerpts",
                "premise_candidate_evidence_eligible",
                "exact_source_theorem_binders",
                "source_context_status",
                "source_theorem_signature_excerpt",
                "adapter_signature_excerpt",
                "premise_target_status",
                "premise_target_matched_binder",
                "premise_target_type",
                "adapter_instantiation_group_id",
                "required_bridge_premise_names_for_shared_instantiation",
                "premise_derivation_gap_kind",
                "premise_derivation_gap_summary",
                "premise_semantic_dependency_status",
                "source_to_bridge_premise_derivation_candidate_request_id",
                "source_to_bridge_premise_derivation_candidate_request",
                "source_to_bridge_grouped_premise_derivation_candidate_request_id",
                "source_to_bridge_grouped_premise_derivation_candidate_request",
                "proof_body_goal_excerpt",
                "proof_body_attempt_summaries",
                "kernel_verified_theorem_reduction_closure_declarations",
                "verified_theorem_reduction_closure_artifact_paths",
                "diagnostics",
            ),
            limit=4,
        )
    if isinstance(row.get("formalizer_lean_candidate_repair_memory"), list):
        compact["formalizer_lean_candidate_repair_memory"] = _compact_rows(
            row.get("formalizer_lean_candidate_repair_memory", []),
            keys=(
                "candidate_id",
                "candidate_kind",
                "source_field",
                "source_manifest_path",
                "artifact_path",
                "lean_source",
                "lean_source_excerpt",
                "precheck_status",
                "local_lean_attempted",
                "local_lean_compiled",
                "local_lean_exit_status",
                "local_lean_project",
                "local_lean_diagnostic_classes",
                "local_lean_stdout",
                "local_lean_stderr",
                "local_lean_stdout_excerpt",
                "local_lean_stderr_excerpt",
                "proof_evidence_status",
            ),
            limit=max(
                1,
                len(row.get("formalizer_lean_candidate_repair_memory", [])),
            ),
        )
    if isinstance(row.get("formalizer_diagnostic_helper_memory"), list):
        compact["formalizer_diagnostic_helper_memory"] = _compact_rows(
            row.get("formalizer_diagnostic_helper_memory", []),
            keys=(
                "candidate_id",
                "candidate_kind",
                "source_field",
                "source_manifest_path",
                "artifact_path",
                "target_ids",
                "target_theorem_goal_ids",
                "target_theorem_name",
                "source_theorem_target_provenance",
                "local_lean_compiled",
                "source_theorem_target_known",
                "diagnostic_helper_not_source_theorem",
                "lean_source",
                "lean_source_excerpt",
                "memory_status",
                "proof_evidence_status",
            ),
            limit=3,
        )
    if isinstance(
        row.get("formalizer_lean_candidate_proof_state_feedback_memory"),
        list,
    ):
        compact["formalizer_lean_candidate_proof_state_feedback_memory"] = _compact_rows(
            row.get("formalizer_lean_candidate_proof_state_feedback_memory", []),
            keys=(
                "learning_task",
                "question_id",
                "source_manifest_id",
                "source_materialization_manifest_id",
                "provider_name",
                "n_feedback_rows",
                "attempt_status",
                "residual_goals",
                "diagnostics",
                "requested_tools",
                "executed_tools",
                "tool_call_trace",
                "lean_lsp_mcp_live_called",
                "proof_evidence_status",
            ),
            limit=3,
        )
    if isinstance(
        row.get("formalizer_lean_candidate_unbound_proof_state_feedback_memory"),
        list,
    ):
        compact[
            "formalizer_lean_candidate_unbound_proof_state_feedback_memory"
        ] = _compact_rows(
            row.get(
                "formalizer_lean_candidate_unbound_proof_state_feedback_memory",
                [],
            ),
            keys=(
                "learning_task",
                "question_id",
                "source_manifest_id",
                "source_materialization_manifest_id",
                "provider_name",
                "n_feedback_rows",
                "attempt_status",
                "rejection_reason",
                "target_behavior",
                "proof_evidence_status",
            ),
            limit=3,
        )
    if isinstance(
        row.get("formalizer_lean_candidate_component_gate_feedback_memory"),
        list,
    ):
        compact["formalizer_lean_candidate_component_gate_feedback_memory"] = _compact_rows(
            row.get("formalizer_lean_candidate_component_gate_feedback_memory", []),
            keys=(
                "learning_task",
                "component_eval",
                "component_eval_manifest_path",
                "provider_name",
                "model",
                "live_generator",
                "static_or_fixture_only",
                "capability_evidence_ok",
                "repair_sequences",
                "local_lean_checked",
                "local_lean_compiled",
                "proofengineer_repair_task_observed",
                "prior_feedback_proof_state_rows",
                "candidate_kernel_verified",
                "source_theorem_kernel_verified",
                "proof_evidence_status",
                "boundary",
            ),
            limit=3,
        )
    if isinstance(
        row.get("formalizer_pseudo_formal_packet_component_gate_feedback_memory"),
        list,
    ):
        compact["formalizer_pseudo_formal_packet_component_gate_feedback_memory"] = _compact_rows(
            row.get(
                "formalizer_pseudo_formal_packet_component_gate_feedback_memory",
                [],
            ),
            keys=(
                "learning_task",
                "component_eval",
                "component_eval_manifest_path",
                "provider_name",
                "model",
                "live_generator",
                "static_or_fixture_only",
                "capability_evidence_ok",
                "fixture_plumbing_ok",
                "result_status",
                "failure_type",
                "errors",
                "formalizer_validation_feedback",
                "model_owned_repair_required",
                "runtime_selected_mathematical_content",
                "pseudo_formal_failure_required_target_lanes",
                "pseudo_formal_routable_target_lanes",
                "n_pseudo_formal_routable_work_order_rows",
                "exact_semantic_definition_lane_present",
                "proof_evidence_status",
                "boundary",
            ),
            limit=3,
        )
    if isinstance(
        row.get("formalizer_pseudo_formal_packet_component_gate_failure_memory"),
        list,
    ):
        compact["formalizer_pseudo_formal_packet_component_gate_failure_memory"] = _compact_rows(
            row.get(
                "formalizer_pseudo_formal_packet_component_gate_failure_memory",
                [],
            ),
            keys=(
                "component_eval_manifest_path",
                "result_status",
                "failure_type",
                "errors",
                "required_target_lanes",
                "formalizer_validation_feedback",
                "model_owned_repair_required",
                "runtime_selected_mathematical_content",
                "proof_evidence_status",
                "boundary",
            ),
            limit=3,
        )
    if isinstance(
        row.get(
            "formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_memory"
        ),
        list,
    ):
        compact[
            "formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_memory"
        ] = _compact_rows(
            row.get(
                "formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_memory",
                [],
            ),
            keys=(
                "learning_task",
                "question_id",
                "work_order_id",
                "next_owner_subsystem",
                "source_component_gate",
                "component_eval_manifest_path",
                "source_component_gate_exact_rows_jsonl",
                "missing_artifact_id",
                "missing_artifact_role",
                "failure_classification",
                "failure_classifications",
                "failure_detail",
                "n_exact_rows_read",
                "proof_evidence_status",
                "boundary",
            ),
            limit=3,
        )
    if isinstance(
        row.get("formalizer_runtime_capability_contract_feedback_memory"),
        list,
    ):
        compact["formalizer_runtime_capability_contract_feedback_memory"] = _compact_rows(
            row.get("formalizer_runtime_capability_contract_feedback_memory", []),
            keys=(
                "learning_task",
                "source_failure_id",
                "source_materialization_manifest_id",
                "next_owner_subsystem",
                "failure_classification",
                "runtime_requested_evidence_contract",
                "formalizer_candidate_local_lean",
                "proof_state_provider",
                "n_candidate_sources",
                "n_local_lean_checked",
                "n_live_proof_state_requests",
                "n_lean_lsp_mcp_ready_requests",
                "candidate_proof_state_manifest_id",
                "proof_evidence_status",
            ),
            limit=3,
        )
    if isinstance(
        row.get("formalizer_lean_candidate_capability_feedback_memory"),
        list,
    ):
        compact["formalizer_lean_candidate_capability_feedback_memory"] = _compact_rows(
            row.get("formalizer_lean_candidate_capability_feedback_memory", []),
            keys=(
                "learning_task",
                "capability_id",
                "next_owner_subsystem",
                "blocker",
                "evidence",
                "component_eval",
                "component_eval_manifest_path",
                "live_generator",
                "static_or_fixture_only",
                "capability_evidence_ok",
                "failure_classification",
                "n_candidate_sources",
                "n_local_lean_checked",
                "n_live_proof_state_requests",
                "n_lean_lsp_mcp_ready_requests",
                "proof_evidence_status",
                "boundary",
            ),
            limit=3,
        )
    if isinstance(
        row.get("source_theorem_exact_semantic_definition_typechecked_candidates"),
        list,
    ):
        compact["source_theorem_exact_semantic_definition_typechecked_candidates"] = _compact_rows(
            row.get("source_theorem_exact_semantic_definition_typechecked_candidates", []),
            keys=(
                "target_theorem_name",
                "placeholder_symbol",
                "definition_only_candidate_artifact_path",
                "local_definition_lean_compiled",
                "semantic_definition_typecheck_evidence_status",
                "exact_source_theorem_binders",
                "source_to_bridge_adapter_instantiation_group_id",
                "failure_classification",
                "proof_evidence_status",
            ),
            limit=4,
        )
    raw_exact_candidate_failures = raw_row.get(
        "source_theorem_exact_candidate_repair_diagnostics",
        [],
    )
    raw_exact_proof_state_failures = raw_row.get(
        "source_theorem_exact_proof_body_repair_diagnostics",
        [],
    )
    prior_exact_candidate_failures = [
        *(
            raw_exact_candidate_failures
            if isinstance(raw_exact_candidate_failures, list)
            else []
        ),
        *(
            raw_exact_proof_state_failures
            if isinstance(raw_exact_proof_state_failures, list)
            else []
        ),
    ]
    if prior_exact_candidate_failures:
        compact["source_theorem_exact_candidate_tool_observations"] = _compact_rows(
            prior_exact_candidate_failures,
            keys=(
                "target_theorem_name",
                "target_lean_declaration",
                "target_declaration_source_excerpt",
                "target_theorem_statement",
                "current_proof_body_excerpt",
                "residual_goal_excerpt",
                "trigger",
                "placeholder_symbol",
                "verification_status",
                "failure_classification",
                "candidate_artifact_path",
                "candidate_source_file",
                "local_lean_compiled",
                "diagnostics",
                "validation_errors",
                "source_lookup_hits",
                "missing_formal_symbols",
                "typeclass_blockers",
                "source_theorem_target_identity_status",
                "semantic_definition_risks",
                "semantic_alignment_blockers",
                "semantic_alignment_constraints",
                "proof_body_gate_status",
                "proof_body_goal_reached",
                "proof_body_goal_excerpt",
                "proof_body_attempt_summaries",
            ),
            limit=6,
        )
        compact["source_theorem_exact_candidate_tool_failure_observed"] = True
    prior_lean_failures = raw_row.get(
        "formalizer_lean_candidate_repair_memory",
        [],
    )
    if isinstance(prior_lean_failures, list) and prior_lean_failures:
        compact["formalizer_lean_candidate_tool_observations"] = _compact_rows(
            prior_lean_failures,
            keys=(
                "candidate_id",
                "candidate_kind",
                "source_field",
                "source_manifest_path",
                "artifact_path",
                "source_hash",
                "target_lean_declaration",
                "target_ids",
                "target_theorem_goal_ids",
                "target_theorem_name",
                "lean_source",
                "lean_source_excerpt",
                "precheck_status",
                "local_lean_attempted",
                "local_lean_compiled",
                "local_lean_exit_status",
                "local_lean_project",
                "local_lean_command",
                "local_lean_stdout",
                "local_lean_stderr",
                "local_lean_stdout_excerpt",
                "local_lean_stderr_excerpt",
                "proof_evidence_status",
            ),
            limit=max(1, len(prior_lean_failures)),
        )
        compact["formalizer_lean_candidate_tool_failure_observed"] = True
    prior_manifest_paths = raw_row.get(
        "formalizer_lean_candidate_repair_manifest_paths",
        [],
    )
    if isinstance(prior_manifest_paths, list) and prior_manifest_paths:
        compact["formalizer_lean_candidate_tool_observation_manifest_paths"] = [
            str(value)
            for value in prior_manifest_paths
            if str(value).strip()
        ]
    projected = model_observations_without_repair_recipes(compact)
    return dict(projected) if isinstance(projected, Mapping) else {}


def _source_theorem_candidate_materialization_contract(
    proof_memory_summary: Mapping[str, Any],
    *,
    environment_feedback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(proof_memory_summary, Mapping):
        return {}
    required = bool(
        proof_memory_summary.get("source_theorem_candidate_materialization_required")
        or proof_memory_summary.get("recommended_formalizer_target_mode")
        == "source_theorem_exact_candidate_materialization_required"
    )
    if required and _source_theorem_exact_semantic_definition_gate_active(
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_memory_summary,
    ):
        required = False
    if not required:
        return {}
    return {
        "required": True,
        "recommended_formalizer_target_mode": (
            "source_theorem_exact_candidate_materialization_required"
        ),
        "target_names": [
            str(value).strip()
            for value in proof_memory_summary.get(
                "source_theorem_candidate_materialization_required_target_names",
                [],
            )
            or []
            if str(value).strip()
        ],
        "target_ids": [
            str(value).strip()
            for value in proof_memory_summary.get(
                "source_theorem_candidate_materialization_required_target_ids",
                [],
            )
            or []
            if str(value).strip()
        ],
        "blocking_statuses": [
            str(value).strip()
            for value in proof_memory_summary.get(
                "source_theorem_candidate_materialization_required_statuses",
                [],
            )
            or []
            if str(value).strip()
        ],
        "missing_formal_symbols": [
            str(value).strip()
            for value in proof_memory_summary.get(
                "source_theorem_candidate_materialization_missing_formal_symbols",
                [],
            )
            or []
            if str(value).strip()
        ],
        "acceptance_gate": str(
            proof_memory_summary.get(
                "source_theorem_candidate_materialization_contract",
                "",
            )
            or ""
        ).strip(),
        "proof_evidence_boundary": (
            "Candidate materialization only creates a runnable Lean target for "
            "signature probes/local Lean. It is not source-theorem proof evidence "
            "until AgentRuntime obtains local Lean/AXLE kernel verification."
        ),
    }


def _compact_value_for_key(key: Any, value: Any) -> Any:
    if str(key) == "formalization_gap_planner_execution_contexts" and isinstance(
        value,
        list | tuple,
    ):
        return _compact_rows(
            value,
            keys=(
                "bridge_id",
                "handoff_id",
                "standalone_seed_artifact_id",
                "standalone_seed_artifact_path",
                "standalone_seed_path",
                "target_intake_path",
                "target_ids",
                "execution_plan_stage_ids",
                "handoff_status",
                "proof_evidence_status",
            ),
            limit=4,
        )
    if str(key) in {
        "lean_source",
        "lean_source_excerpt",
        "target_declaration_source_excerpt",
        "candidate_source_excerpt",
        "target_theorem_statement",
        "current_proof_body_excerpt",
        "local_lean_stdout",
        "local_lean_stderr",
        "local_lean_stdout_excerpt",
        "local_lean_stderr_excerpt",
        "candidate_identity_lean_stdout",
        "candidate_identity_lean_stderr",
        "candidate_identity_lean_stdout_excerpt",
        "candidate_identity_lean_stderr_excerpt",
    } and isinstance(value, str):
        return value
    if str(key) in {
        "validation_errors",
        "retry_validation_errors",
        "precheck_errors",
        "blocking_precheck_errors",
        "diagnostics",
        "residual_goals",
        "proof_body_goal_excerpt",
        "proof_body_attempt_summaries",
    }:
        return _without_runtime_authored_prescriptions(value)
    if str(key) == "formal_source_grounding_hits":
        return compact_formal_source_grounding_hits_for_prompt(value)
    if str(key) == "retrieval_query_seeds" and isinstance(value, list | tuple):
        return [str(item)[:400] for item in list(value)[:3] if str(item).strip()]
    if str(key) == "proof_state_trace_rag" and isinstance(value, Mapping):
        return _compact_mapping(
            value,
            keys=(
                "schema_version",
                "provider",
                "source_id",
                "anchor_source_ids",
                "dataset_id",
                "dataset_url",
                "repository_url",
                "license",
                "dataset_revision",
                "trace_sha256",
                "split",
                "toolchain",
                "mathlib_revision",
                "query_fingerprint",
                "query_roles",
                "declaration_rag_anchors",
                "n_hits",
                "n_target_name_overlap_hits",
                "n_declaration_aligned_hits",
                "hits",
                "selection_policy",
                "use_policy",
                "version_boundary",
                "evaluation_contamination_policy",
                "proof_evidence_status",
            ),
        )
    if str(key) in {
        "source_theorem_statement",
        "state_before",
        "state_after",
        "tactic",
        "current_signature",
    } and isinstance(value, str):
        limits = {
            "source_theorem_statement": 1800,
            "state_before": 2600,
            "state_after": 1800,
            "tactic": 1000,
            "current_signature": 1400,
        }
        return value[: limits[str(key)]]
    if str(key) == "source_theorem_candidate_proof_bodies" and isinstance(
        value,
        list | tuple,
    ):
        return [str(child)[:12000] for child in list(value)[:4] if str(child)]
    if str(key) == "verified_support_assets" and isinstance(value, list | tuple):
        return [
            {
                str(asset_key): (
                    str(asset_value)[:20000]
                    if str(asset_key) in {"theorem_src", "proof"}
                    else _compact_value_for_key(asset_key, asset_value)
                )
                for asset_key, asset_value in asset.items()
                if str(asset_key)
                in {
                    "name",
                    "statement",
                    "proof",
                    "theorem_src",
                    "call_expr",
                    "axioms_report",
                    "proof_source",
                }
                and asset_value not in (None, "", [], {})
            }
            for asset in list(value)[:8]
            if isinstance(asset, Mapping)
        ]
    if str(key) == "candidate_feedback_rows" and isinstance(value, list | tuple):
        return [
            _compact_external_candidate_feedback_row(row)
            for row in list(value)[:4]
            if isinstance(row, Mapping)
        ]
    if str(key) == "source_theorem_target_provenance" and isinstance(
        value,
        Mapping,
    ):
        return _compact_mapping(value, keys=tuple(value.keys())[:24])
    if str(key) == "external_proof_search_result" and isinstance(value, Mapping):
        return _compact_mapping(
            value,
            keys=(
                "result_id",
                "provider",
                "request_fingerprint",
                "target_lean_declaration",
                "status",
                "openprover_summary",
                "source_theorem_candidate_proof_bodies",
                "verified_support_assets",
                "failure_feedback",
                "exact_candidate_rerun",
                "report_path",
                "checkpoint_path",
                "blocker",
                "error",
                "proof_evidence_status",
                "proof_evidence_boundary",
            ),
        )
    if str(key) == "exact_candidate_rerun" and isinstance(value, Mapping):
        return _compact_mapping(
            value,
            keys=(
                "manifest_id",
                "execution_id",
                "input_fingerprint",
                "provider_result_fingerprint",
                "verification_config_fingerprint",
                "request_fingerprint",
                "question_id",
                "source_task_id",
                "source_lineage_id",
                "source_work_order_id",
                "execution_queue_id",
                "target_ids",
                "target_lean_declaration",
                "target_theorem_statement",
                "verification_scope",
                "exact_target_prefix_hash",
                "source_after_exact_target_marker_hash",
                "source_suffix_commands_executed",
                "source_candidate_artifact_path",
                "source_candidate_artifact_hash",
                "proof_body_signature_probe_artifact_path",
                "proof_body_signature_probe_artifact_hash",
                "n_candidate_proof_bodies",
                "n_result_rows",
                "n_precheck_rejected",
                "n_local_lean_checked",
                "n_local_lean_compiled",
                "n_artifact_kernel_verified",
                "n_source_theorem_kernel_verified",
                "source_theorem_kernel_verified",
                "source_theorem_kernel_verified_target_ids",
                "source_theorem_kernel_verified_target_names",
                "runtime_verification_contract_satisfied",
                "runtime_verification_contract_errors",
                "reported_source_theorem_kernel_verified",
                "runtime_owned_local_lean_checked",
                "runtime_owned_local_lean_compiled",
                "runtime_owned_source_theorem_kernel_verified",
                "candidate_feedback_rows",
                "error",
                "proof_evidence_status",
                "proof_evidence_boundary",
            ),
        )
    if str(key) in {"semantic_alignment_blockers", "semantic_alignment_constraints"}:
        if isinstance(value, str):
            return value[:280]
        if isinstance(value, list | tuple):
            return [
                child[:280] if isinstance(child, str) else _compact_value(child)
                for child in list(value)[:5]
            ]
    if _is_compaction_path_key(key):
        if isinstance(value, str):
            return value
        if isinstance(value, list | tuple):
            return [
                child if isinstance(child, str) else _compact_value(child)
                for child in list(value)[:8]
            ]
    return _compact_value(value)


def _compact_external_candidate_feedback_row(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    keys = (
        "candidate_index",
        "candidate_proof_body",
        "candidate_proof_body_hash",
        "candidate_artifact_path",
        "candidate_artifact_hash",
        "request_fingerprint",
        "input_fingerprint",
        "execution_id",
        "question_id",
        "source_task_id",
        "source_lineage_id",
        "source_work_order_id",
        "execution_queue_id",
        "source_candidate_artifact_hash",
        "materialized_verified_support_asset_names",
        "materialized_verified_support_asset_hashes",
        "verification_scope",
        "exact_target_prefix_hash",
        "source_after_exact_target_marker_hash",
        "source_suffix_commands_executed",
        "exact_signature_preserved",
        "precheck_errors",
        "source_theorem_evidence_blockers",
        "runtime_structural_contract_errors",
        "local_lean_checked",
        "local_lean_compiled",
        "returncode",
        "diagnostics",
        "runtime_owned_local_lean_checked",
        "runtime_owned_local_lean_compiled",
        "runtime_owned_local_lean_returncode",
        "runtime_owned_local_lean_diagnostics",
        "artifact_kernel_verified",
        "reported_artifact_kernel_verified",
        "reported_source_theorem_kernel_verified",
        "source_theorem_kernel_verified",
        "proof_evidence_status",
        "status",
    )
    compact: dict[str, Any] = {}
    for key in keys:
        value = row.get(key)
        if value in (None, "", [], {}):
            continue
        if key == "candidate_proof_body" and isinstance(value, str):
            compact[key] = value[:12000]
        elif key in {
            "precheck_errors",
            "source_theorem_evidence_blockers",
            "runtime_structural_contract_errors",
            "diagnostics",
            "runtime_owned_local_lean_diagnostics",
        } and isinstance(value, list | tuple):
            compact[key] = [
                _compact_external_candidate_diagnostic(str(child))
                for child in list(value)[:24]
            ]
        elif _is_compaction_path_key(key) and isinstance(value, str):
            compact[key] = value
        elif isinstance(value, str):
            compact[key] = value[:2000]
        else:
            compact[key] = _compact_value(value)
    return compact


def _compact_external_candidate_diagnostic(
    value: str,
    *,
    max_chars: int = 2400,
) -> str:
    if len(value) <= max_chars:
        return value
    head_chars = 700
    tail_chars = max_chars - head_chars - 5
    return value[:head_chars] + " ... " + value[-tail_chars:]


def _compact_value(value: Any) -> Any:
    if isinstance(value, str):
        return value[:FORMALIZER_MAX_TEXT_CHARS]
    if isinstance(value, Mapping):
        priority_keys = (
            "context_kind",
            "repair_scope",
            "target_lean_declaration",
            "target_ids",
            "source_theorem_target_known",
            "source_theorem_target_identity_status",
            "source_theorem_target_provenance",
            "target_identity_status",
            "target_identity_errors",
            "source_theorem_kernel_evidence_eligible",
            "expected_target_lean_declaration",
            "source_work_order_id",
            "execution_queue_id",
            "source_lineage_id",
            "candidate_artifact_path",
            "source_candidate_artifact_path",
            "lineage_candidate_artifact_path",
            "lineage_candidate_artifact_hash",
            "target_declaration_source_hash",
            "target_theorem_statement_hash",
            "proof_body_signature_probe_artifact_path",
            "proof_body_signature_probe_artifact_hash",
            "target_theorem_statement",
            "current_proof_body_excerpt",
            "compiler_feedback",
            "prior_exact_candidate_feedback",
            "proof_body_generation_contract",
            "proof_state_trace_rag",
            "formal_environment_placeholder_symbols",
            "formal_environment_typeclass_blockers",
            "semantic_alignment_constraints",
            "semantic_alignment_blockers",
            "external_proof_search_result",
            "repair_target_identity_contract",
            "feedback_kind",
            "contract_kind",
            "required_output_key",
            "pseudo_formalization_required_reason",
            "target_lanes",
            "target_names",
            "placeholder_symbols",
            "response_validation_feedback",
            "unverified_required_imports",
            "source_failed_candidate_packet_id",
            "validation_issue_summary",
            "validation_issue_kinds",
            "source",
            "source_theorem_proof_body_adapter_required",
            "source_theorem_proof_body_adapter_feedback_available",
            "adapter_kernel_verified",
            "diagnostics",
            "diagnostic_classes",
            "acceptance_gate",
            "source_theorem_candidate_proof_bodies",
            "verified_support_assets",
            "failure_feedback",
            "exact_candidate_rerun",
            "proof_evidence_status",
            "unknown_identifiers",
            "repeated_syntax_failure",
        )
        excluded_keys = {
            "blocked_import_prefixes",
            "hard_negative_rejected_imports",
            "concrete_lane_routable_repair_seed",
            "lane_activation_hints",
            "mathlib_import_unavailable",
            "mathlib_root_import_unavailable",
            "pseudo_formal_failure_concrete_lane_routable_repair_seed",
            "pseudo_formal_failure_copy_contract_summary",
            "pseudo_formal_failure_validator_ready_copy_contract",
            "required_block_schema_hints",
            "suggested_import_replacements",
            "validation_issue_repair_actions",
            "validator_ready_copy_contract",
            "validator_ready_copy_contract_summary",
        }
        ordered_keys: list[Any] = [
            key
            for key in priority_keys
            if key not in excluded_keys
            and not _is_runtime_authored_prescriptive_field(key)
            and key in value
            and value.get(key) not in (None, "", [], {})
        ]
        for key in value:
            key_text = str(key)
            if (
                key not in ordered_keys
                and key_text not in excluded_keys
                and not _is_runtime_authored_prescriptive_field(key)
                and value.get(key) not in (None, "", [], {})
            ):
                ordered_keys.append(key)
        mapping_limit = (
            40
            if str(value.get("context_kind", ""))
            == "exact_source_theorem_whole_proof_repair"
            or "external_proof_search_result" in value
            else 16
        )
        return {
            str(key): _compact_value_for_key(key, child)
            for key in ordered_keys[:mapping_limit]
            for child in (value.get(key),)
        }
    if isinstance(value, list | tuple):
        return [_compact_value(child) for child in list(value)[:5]]
    return value


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, list | tuple) else 0


def _contains_forbidden_proof_claim(value: Any) -> str:
    text = json.dumps(value, default=str).lower()
    forbidden = (
        "kernel_verified\": true",
        "full_frontier_theorem_proved\": true",
        "qed verified",
        "lean verified",
        "kernel verified",
        "theorem proved",
    )
    for token in forbidden:
        if token in text:
            return token
    return ""


def _source_to_bridge_candidate_has_source_binding_contract(
    row: Mapping[str, Any],
) -> bool:
    if str(row.get("source_to_bridge_premise_derivation_candidate_request_id", "") or "").strip():
        return True
    if str(row.get("source_to_bridge_grouped_premise_derivation_candidate_request_id", "") or "").strip():
        return True
    for key in (
        "source_to_bridge_premise_derivation_candidate_request",
        "source_to_bridge_grouped_premise_derivation_candidate_request",
    ):
        nested = row.get(key, {})
        if isinstance(nested, Mapping) and nested:
            return True
    return False
