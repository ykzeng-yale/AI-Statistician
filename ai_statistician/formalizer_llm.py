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
from .structured_output_retry import (
    PacketValidationError,
    extract_json_object,
    generate_validated_json_packet,
)
from .lean_candidate_revision_tool_loop import (
    LeanCandidateCheck,
    LeanDeclarationInspection,
    LeanStateInspection,
    FormalEnvironmentSearch,
    ProofCandidateSearch,
    run_lean_candidate_revision_tool_loop,
)
from .model_backend import (
    PROVIDER_STRUCTURED_OUTPUT_ON_RETRY_METADATA_KEY,
    GeneratorBackend,
    GeneratorRequest,
    resolve_generator_model,
)
from .research_schema import OpenResearchQuestion
from .semantic_review_feedback import (
    PRESCRIPTIVE_REPAIR_FIELDS,
    coding_agent_observations_only,
)
from .theory_derivation_trace import (
    compact_theory_derivation_trace,
    theory_trace_alignment_contract,
    theory_trace_alignment_json_schema,
    theory_trace_alignment_output_contract,
    theory_trace_alignment_prompt_instruction,
    theory_trace_consumption_contract,
)
from .theory_workspace import (
    externalize_theory_document_rows,
    load_theory_workspace_document_rows,
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
FORMALIZER_MAX_INDEXED_ENVIRONMENT_CANDIDATES = 6
FORMALIZER_MAX_TEXT_CHARS = 200
FORMALIZER_MAX_ACTIVE_TARGETS = 1
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
    return coding_agent_observations_only(value)


@dataclass(frozen=True)
class FormalizerConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 6000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_validation_retries: int = 1
    use_client_tool_lean_candidate_workspace: bool = True
    client_tool_lean_candidate_max_turns: int = 20
    client_tool_lean_candidate_max_no_progress_turns: int = 2


def formalizer_proof_construction_strategy_contract() -> dict[str, Any]:
    """Minimal ownership and evidence boundary for model-driven Lean work."""

    return {
        "schema_version": 16,
        "target_identity": (
            "Preserve the exact task-bound theorem, assumptions, declaration identity, "
            "and parent artifact lineage. Never weaken or replace the target."
        ),
        "model_ownership": (
            "The model receives the complete current Lean source, exact target, raw verifier output, "
            "review, and retrieval; it chooses every import, query, scratch experiment, and source change."
        ),
        "environment_loop": (
            "Search or run scratch when needed, compile the exact current source, and revise "
            "from observations. AgentRuntime enforces budgets and identity but never edits Lean."
        ),
        "library_context": (
            "Infer APIs from the active Statlib/Mathlib/project environment and recheck "
            "every reused declaration there."
        ),
        "evidence_boundary": (
            "Source, scratch, retrieval, review, and elaboration are observations. Only "
            "the exact local Lean/kernel gate may promote the unchanged target."
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
        environment_feedback: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        user_prompt = build_formalizer_prompt(
            question=question,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            algorithm_manifest=algorithm_manifest,
            registered_problem=registered_problem,
            theorem_goals=theorem_goals,
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
        request = GeneratorRequest(
            system_prompt=FORMALIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=_formalizer_json_schema(theory_packet=theory_packet),
            metadata={
                "subsystem": "FormalizerProofEngineer",
                "agent": "LLMFormalizerProofEngineerAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
                **(
                    {
                        PROVIDER_STRUCTURED_OUTPUT_ON_RETRY_METADATA_KEY: True,
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
                environment_feedback=environment_feedback or {},
            )

        def validate_packet(packet: Mapping[str, Any]) -> list[str]:
            return _formalizer_contextual_validation_errors(
                packet,
                requires_lean_candidate=requires_lean_candidate,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_packet,
            validation_label="LLM Formalizer/ProofEngineer packet",
            max_validation_retries=self.config.max_validation_retries,
        )

    def run_lean_candidate_workspace_with_client_tools(
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
        check_candidate: LeanCandidateCheck,
        search_formal_environment: FormalEnvironmentSearch,
        search_proof_candidates: ProofCandidateSearch | None = None,
        inspect_lean_state: LeanStateInspection | None = None,
        inspect_lean_declaration: LeanDeclarationInspection | None = None,
        session_dir: Path | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Author or revise one hash-bound target through model-selected tools."""

        if not self.config.use_client_tool_lean_candidate_workspace:
            raise ValueError("Formalizer Lean candidate client-tool workspace is disabled")
        if not callable(getattr(self.provider, "generate_client_tool_turn", None)):
            raise ValueError("Formalizer provider does not support client-tool turns")
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        workspace_turn_budget = max(
            1,
            self.config.client_tool_lean_candidate_max_turns,
        )
        workspace_context = environment_feedback.get(
            "formalizer_workspace_context", {}
        )
        workspace_context = (
            dict(workspace_context)
            if isinstance(workspace_context, Mapping)
            else {}
        )
        semantic_revision_required = str(
            workspace_context.get(
                "formalizer_candidate_semantic_review_status", ""
            )
            or ""
        ) == "INDEPENDENT_SEMANTIC_REVIEW_REVISE_NOT_PROOF_EVIDENCE"
        rejected_source_hash = ""
        if semantic_revision_required:
            rejected_source_hash = str(
                workspace_context.get(
                    "formalizer_candidate_semantic_review_candidate_source_hash",
                    "",
                )
                or environment_feedback.get("candidate_source_hash", "")
                or ""
            ).strip()
            if not rejected_source_hash:
                raise ValueError(
                    "formal-target semantic revision lacks its rejected source hash"
                )
        theory_document_rows = load_theory_workspace_document_rows(theory_packet)
        theory_document_manifest, _ = externalize_theory_document_rows(
            theory_document_rows
        )
        theory_document_set_hash = (
            stable_hash(
                [
                    (row["path"], row["sha256"])
                    for row in theory_document_manifest
                ]
            )
            if theory_document_manifest
            else ""
        )
        loop = run_lean_candidate_revision_tool_loop(
            provider=self.provider,
            system_prompt=(
                FORMALIZER_SYSTEM_PROMPT
                + "\nOwn the complete Lean source and every search query for this "
                "unchanged hash-bound target; do not answer with prose or JSON. Use "
                "the tools to read Theory context, run independent Lean scratch, inspect "
                "the active environment, and compile early. Retrieval and review are observations, "
                "not proof. A diagnostic caused by your own submitted source is revision "
                "feedback, not a foundation gap. Treat inspected declaration source as "
                "the executable API, including its importable module and lexical context. "
                "After a compiler diagnostic, prioritize a model-authored exact edit or "
                "complete source replacement; search again only for a concrete unresolved "
                "environment question. The same tools remain available during standard "
                "turns, and independent read-only calls may be batched. Temporary admitted "
                "sources, #check, and #print are diagnostic only and must be replaced by a "
                "complete proof. Report a formal gap only after active-environment evidence "
                "establishes a missing primitive required by the unchanged target. Finish "
                "with an exact source action or a grounded formal-gap action."
            ),
            user_prompt=_build_lean_candidate_workspace_tool_prompt(
                question=question,
                theory_packet=theory_packet,
                parent_packet=parent_packet,
                candidate_id=candidate_id,
                candidate_source_field=candidate_source_field,
                candidate_lean_declaration=candidate_lean_declaration,
                initial_source=initial_source,
                environment_feedback=environment_feedback,
                authoritative_theory_document_count=len(
                    theory_document_manifest
                ),
                authoritative_theory_document_set_hash=(
                    theory_document_set_hash
                ),
            ),
            model=request_model,
            model_tier=self.config.model_tier,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            max_turns=workspace_turn_budget,
            max_no_progress_turns=max(
                1,
                self.config.client_tool_lean_candidate_max_no_progress_turns,
            ),
            candidate_id=candidate_id,
            candidate_lean_declaration=candidate_lean_declaration,
            initial_source=initial_source,
            check_candidate=check_candidate,
            search_formal_environment=search_formal_environment,
            search_proof_candidates=search_proof_candidates,
            inspect_lean_state=inspect_lean_state,
            inspect_lean_declaration=inspect_lean_declaration,
            rejected_source_hash=rejected_source_hash,
            allow_formal_gap=True,
            recovery_checkpoint=(
                environment_feedback.get("formalizer_recovery_checkpoint", {})
                if isinstance(
                    environment_feedback.get(
                        "formalizer_recovery_checkpoint", {}
                    ),
                    Mapping,
                )
                else {}
            ),
            session_dir=session_dir,
            authoritative_theory_document_rows=theory_document_rows,
            request_metadata={
                "subsystem": "FormalizerProofEngineer",
                "agent": "LLMFormalizerProofEngineerAgent",
                "formalizer_phase": (
                    "lean_candidate_initial_authoring"
                    if not initial_source.strip()
                    else "lean_candidate_revision"
                ),
                "parent_artifact_id": _formalizer_parent_artifact_id(parent_packet),
                "proof_evidence_status": FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE,
            },
        )
        if str(parent_packet.get("artifact_kind", "") or "") == (
            "FormalizerWorkspaceTarget"
        ):
            revised_payload = _formalizer_payload_from_workspace_target(
                parent_packet,
                disposition=loop.disposition,
                formal_gap=loop.formal_gap,
            )
        else:
            revised_payload = _formalizer_revision_payload_from_packet(parent_packet)
        if loop.disposition == "AUTHOR_LEAN":
            _bind_model_authored_lean_candidate_source(
                revised_payload,
                candidate_id=candidate_id,
                candidate_source_field=candidate_source_field,
                candidate_lean_declaration=loop.candidate_lean_declaration,
                lean_source=loop.lean_source,
            )
        elif loop.disposition == "FORMAL_GAP":
            _bind_model_reported_formal_gap(
                revised_payload,
                candidate_id=candidate_id,
                candidate_source_field=candidate_source_field,
                formal_gap=loop.formal_gap,
            )
        revised_payload["ok"] = True
        revised_payload["validation_errors"] = []
        revised_payload["structured_output_retry_attempts"] = 0
        revised_payload["structured_output_retry_history"] = []
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
            environment_feedback=environment_feedback,
        )
        requires_lean_candidate = (
            loop.disposition == "AUTHOR_LEAN"
            and _feedback_requires_formalizer_lean_candidate(environment_feedback)
        )
        errors = _formalizer_contextual_validation_errors(
            packet,
            requires_lean_candidate=requires_lean_candidate,
        )
        if errors:
            raise PacketValidationError(
                validation_label=(
                    "LLM Formalizer Lean candidate client-tool workspace packet"
                ),
                attempts=int(loop.evidence.get("turns", 1) or 1),
                errors=sorted(set(errors)),
                history=[],
                last_invalid_packet=packet,
                recovery_checkpoint={
                    "candidate_id": candidate_id,
                    "parent_artifact_id": _formalizer_parent_artifact_id(
                        parent_packet
                    ),
                    "submitted_source_hash": loop.source_hash,
                    "client_tool_loop": dict(loop.evidence),
                },
            )
        return packet, dict(loop.evidence)


def _formalizer_contextual_validation_errors(
    packet: Mapping[str, Any],
    *,
    requires_lean_candidate: bool,
) -> list[str]:
    errors = validate_formalizer_packet(packet)
    if requires_lean_candidate:
        errors.extend(
            _validate_capability_eval_formalizer_lean_candidate_packet(
                packet,
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


def build_formalizer_workspace_target(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    registered_problem: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Resolve one upstream-owned theorem goal without another model call."""

    target_contract = _task_bound_formal_target_contract(
        question=question,
        theory_packet=theory_packet,
        theorem_goals=theorem_goals,
        registered_problem=registered_problem,
    )
    goal_rows = [dict(row) for row in theorem_goals if isinstance(row, Mapping)]
    requested_id = str(
        target_contract.get("source_theorem_target_id", "") or ""
    ).strip()
    if requested_id:
        matches = [
            row
            for row in goal_rows
            if str(row.get("id", "") or "").strip() == requested_id
        ]
    else:
        matches = goal_rows if len(goal_rows) == 1 else []
    if len(matches) != 1:
        available_ids = sorted(
            str(row.get("id", "") or "").strip()
            for row in goal_rows
            if str(row.get("id", "") or "").strip()
        )
        raise PacketValidationError(
            validation_label="Formalizer workspace target identity",
            attempts=1,
            errors=[
                "the outer research graph must bind exactly one registered theorem "
                f"goal before Lean authoring; requested={requested_id!r}, "
                f"available={available_ids}"
            ],
            history=[],
        )
    goal = matches[0]
    goal_id = str(goal.get("id", "") or "").strip()
    informal_source = str(
        goal.get("informal_statement", "")
        or goal.get("statement", "")
        or goal.get("claim", "")
        or goal.get("conclusion", "")
        or ""
    ).strip()
    if not informal_source:
        raise PacketValidationError(
            validation_label="Formalizer workspace target identity",
            attempts=1,
            errors=[f"registered theorem goal {goal_id!r} has no informal statement"],
            history=[],
        )
    derivation_packet = theory_packet.get("theory_derivation_packet", {})
    derivation_packet = (
        derivation_packet if isinstance(derivation_packet, Mapping) else {}
    )
    handoff = derivation_packet.get("formalization_handoff", {})
    if not isinstance(handoff, Mapping):
        handoff = theory_packet.get("formalization_handoff", {})
    handoff = handoff if isinstance(handoff, Mapping) else {}
    constraints = _task_contract_text_list(
        handoff.get("semantic_alignment_constraints", []),
        limit=12,
        char_limit=2400,
    )
    if not constraints:
        constraints = [
            "Preserve the registered theorem goal's assumptions, quantifiers, and "
            "conclusion exactly."
        ]
    target = {
        "id": goal_id,
        "formal_target_role": FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
        "informal_source": informal_source,
        "lean_statement_sketch": "",
        "candidate_lean_declaration": "",
        "lean_imports": [],
        "semantic_alignment_constraints": constraints,
        "source_theorem_target_provenance": {
            "target_lean_declaration": "",
            "source_theorem_goal_id": goal_id,
            "source_theorem_target_known": True,
        },
        "expected_status": "NEEDS_KERNEL_CHECK",
    }
    body = {
        "artifact_kind": "FormalizerWorkspaceTarget",
        "question_id": question.id,
        "formal_target": target,
        "task_bound_formal_target_contract_fingerprint": str(
            target_contract.get("contract_fingerprint", "") or ""
        ),
        "proof_evidence_status": "TASK_BOUND_TARGET_REFERENCE_NOT_PROOF_EVIDENCE",
    }
    return {
        **body,
        "target_ref_id": "formalizer_workspace_target:" + stable_hash(body)[:24],
    }


def _formalizer_parent_artifact_id(packet: Mapping[str, Any]) -> str:
    return str(
        packet.get("packet_id", "")
        or packet.get("target_ref_id", "")
        or ""
    )


def _formalizer_payload_from_workspace_target(
    packet: Mapping[str, Any],
    *,
    disposition: str,
    formal_gap: Mapping[str, Any],
) -> dict[str, Any]:
    if str(packet.get("artifact_kind", "") or "") != (
        "FormalizerWorkspaceTarget"
    ):
        raise ValueError("parent artifact is not a Formalizer workspace target")
    target = packet.get("formal_target", {})
    if not isinstance(target, Mapping):
        raise ValueError("Formalizer workspace target has no formal_target object")
    target_row = deepcopy(dict(target))
    if disposition == "FORMAL_GAP":
        target_row.update(
            {
                "formal_target_role": FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP,
                "lean_statement_sketch": "",
                "candidate_lean_declaration": "",
                "lean_imports": [],
                "expected_status": "FORMAL_GAP",
                "formal_gap": deepcopy(dict(formal_gap)),
            }
        )
    return {
        "formal_targets": [target_row],
        "retrieval_queries": [],
        "gap_taxonomy": [deepcopy(dict(formal_gap))] if formal_gap else [],
    }


def _bind_model_authored_lean_candidate_source(
    payload: dict[str, Any],
    *,
    candidate_id: str,
    candidate_source_field: str,
    candidate_lean_declaration: str,
    lean_source: str,
) -> None:
    """Bind exact model-authored source to one immutable candidate row."""

    source_field = str(candidate_source_field or "").strip()
    if source_field != "formal_targets":
        raise ValueError("unsupported Formalizer Lean candidate source field")
    rows = payload.get(source_field, [])
    if not isinstance(rows, list):
        raise ValueError("parent Formalizer candidate container is not a list")
    matches: list[dict[str, Any]] = []
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, dict):
            continue
        row_id = str(raw_row.get("id", "") or f"formal_target_candidate_{index}")
        row_declaration = str(
            raw_row.get("candidate_lean_declaration", "") or ""
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
    row["lean_statement_sketch"] = lean_source
    row["candidate_lean_declaration"] = candidate_lean_declaration
    provenance = row.get("source_theorem_target_provenance", {})
    provenance = dict(provenance) if isinstance(provenance, Mapping) else {}
    provenance["target_lean_declaration"] = candidate_lean_declaration
    row["source_theorem_target_provenance"] = provenance


def _bind_model_reported_formal_gap(
    payload: dict[str, Any],
    *,
    candidate_id: str,
    candidate_source_field: str,
    formal_gap: Mapping[str, Any],
) -> None:
    """Bind one model-reported non-proof blocker to the active target row."""

    source_field = str(candidate_source_field or "").strip()
    if source_field != "formal_targets":
        raise ValueError("unsupported Formalizer formal-gap source field")
    rows = payload.get(source_field, [])
    if not isinstance(rows, list):
        raise ValueError("parent Formalizer candidate container is not a list")
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and str(row.get("id", "") or "") == candidate_id
    ]
    if len(matches) != 1:
        raise ValueError(
            "runtime-bound Formalizer gap did not resolve to exactly one parent row"
        )
    gap = deepcopy(dict(formal_gap))
    matches[0].update(
        {
            "formal_target_role": FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP,
            "lean_statement_sketch": "",
            "candidate_lean_declaration": "",
            "lean_imports": [],
            "expected_status": "FORMAL_GAP",
            "formal_gap": gap,
        }
    )
    payload["gap_taxonomy"] = [gap]


def _build_lean_candidate_workspace_tool_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    parent_packet: Mapping[str, Any],
    candidate_id: str,
    candidate_source_field: str,
    candidate_lean_declaration: str,
    initial_source: str,
    environment_feedback: Mapping[str, Any],
    authoritative_theory_document_count: int = 0,
    authoritative_theory_document_set_hash: str = "",
) -> str:
    indexed_environment_candidates = (
        _formalizer_indexed_lean_environment_candidates(environment_feedback)
    )
    review_context_payload = environment_feedback.get(
        "formalizer_workspace_context", {}
    )
    review_context = (
        dict(review_context_payload)
        if isinstance(review_context_payload, Mapping)
        else {}
    )
    runtime_observations = _complete_lean_candidate_revision_feedback(
        environment_feedback,
        candidate_id=candidate_id,
    )
    raw_target_rows = parent_packet.get("formal_targets", []) or []
    if str(parent_packet.get("artifact_kind", "") or "") == (
        "FormalizerWorkspaceTarget"
    ):
        raw_target_rows = [parent_packet.get("formal_target", {})]
    target_rows = [
        row
        for row in raw_target_rows
        if isinstance(row, Mapping)
        and (
            str(row.get("id", "") or "") == candidate_id
            or (
                candidate_lean_declaration
                and str(row.get("candidate_lean_declaration", "") or "")
                == candidate_lean_declaration
            )
        )
    ]
    target_row = target_rows[0] if len(target_rows) == 1 else {}
    exact_target_contract = {
        field: deepcopy(target_row[field])
        for field in (
            "id",
            "formal_target_role",
            "informal_source",
            "candidate_lean_declaration",
            "semantic_alignment_constraints",
            "source_theorem_target_provenance",
            "expected_status",
        )
        if target_row.get(field) not in (None, "", [], {})
    }
    initial_authoring = not initial_source.strip()
    payload = {
        "task": (
            ("Author" if initial_authoring else "Revise")
            + " the complete exact current Lean source through model-selected "
            "search, inspection, and atomic source actions. A successful source action "
            "hands the exact current source to independent semantic review."
        ),
        "workspace_phase": (
            "initial_authoring" if initial_authoring else "revision"
        ),
        "tool_workflow": (
            "Choose tools from current observations. Edit the exact current source for "
            "a local change or submit one complete standalone source for initial "
            "authoring, declaration changes, or replacement. Supply the exact Lean "
            "declaration identifier and every import; the runtime checks those bytes "
            "immediately and never edits them. Read accepted Theory documents on demand, "
            "compile early, and search for concrete unresolved environment questions. "
            "Raw observations return to this same source owner; successful source bytes "
            "go to independent semantic review."
            + (
                " Inspect carried indexed declarations and their exact modules first; "
                "do not repeat a search for the same identity unless Lean reports "
                "that it is stale or incompatible."
                if indexed_environment_candidates
                else ""
            )
            + (
                " Report a non-proof formal gap only when active-environment evidence "
                "establishes a required missing primitive."
                if initial_authoring
                else ""
            )
        ),
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
        },
        "immutable_binding": {
            "parent_artifact_id": _formalizer_parent_artifact_id(parent_packet),
            "candidate_id": candidate_id,
            "candidate_source_field": candidate_source_field,
            **(
                {"candidate_lean_declaration": candidate_lean_declaration}
                if candidate_lean_declaration
                else {}
            ),
            "source_theorem_target_identity_status": str(
                review_context.get("source_theorem_target_identity_status", "")
                or ""
            ),
            "formalizer_candidate_semantic_review_status": str(
                review_context.get(
                    "formalizer_candidate_semantic_review_status",
                    "",
                )
                or ""
            ),
            "target_theorem_statement_hash": str(
                review_context.get("target_theorem_statement_hash", "")
                or review_context.get(
                    "formalizer_candidate_semantic_review_target_statement_hash",
                    "",
                )
                or ""
            ),
        },
        "exact_target_contract": exact_target_contract,
        **(
            {
                "indexed_lean_environment_candidates": (
                    indexed_environment_candidates
                )
            }
            if indexed_environment_candidates
            else {}
        ),
        "task_bound_theory_context": {
            "theory_packet_id": str(theory_packet.get("packet_id", "") or ""),
            "theorem_cards": _compact_rows(
                theory_packet.get("theorem_cards", []),
                keys=(
                    "id",
                    "title",
                    "claim",
                    "statement",
                    "conclusion",
                    "assumptions",
                    "proof_strategy",
                    "proof_obligations",
                ),
                limit=FORMALIZER_MAX_THEORY_ROWS,
            ),
            "formalization_requests": _compact_rows(
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
                ),
                limit=FORMALIZER_MAX_THEORY_ROWS,
            ),
            "theory_derivation_trace": compact_theory_derivation_trace(
                theory_packet
            ),
            "n_authoritative_theory_documents": (
                authoritative_theory_document_count
            ),
            "authoritative_theory_document_set_hash": (
                authoritative_theory_document_set_hash
            ),
            "document_content_transport": (
                "hash_bound_read_only_client_tools"
                if authoritative_theory_document_count
                else ""
            ),
            "theory_trace_consumption_contract": (
                theory_trace_consumption_contract(
                    theory_packet,
                    consumer_subsystem="FormalizerProofEngineer",
                )
            ),
        },
        "runtime_observations": runtime_observations,
        "model_owned_revision_contract": (
            formalizer_proof_construction_strategy_contract()
        ),
        "boundaries": {
            "model_owns_lean_source_and_search_queries": True,
            "runtime_selected_lean_code": False,
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
            "informal_statement",
            "claim",
            "statement",
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
            "informal_statement",
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
    review_context = environment_feedback.get("formalizer_workspace_context", {})
    if isinstance(review_context, Mapping):
        contexts.append(review_context)
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



def build_formalizer_prompt(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    algorithm_manifest: Mapping[str, Any],
    registered_problem: Mapping[str, Any],
    theorem_goals: list[Mapping[str, Any]],
    environment_feedback: Mapping[str, Any] | None = None,
) -> str:
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
            "active_formal_target_count": FORMALIZER_MAX_ACTIVE_TARGETS,
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
            "authoritative_theory_documents": (
                load_theory_workspace_document_rows(theory_packet)
            ),
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
        "runtime_environment_feedback": runtime_environment_feedback,
        "formalizer_lean_candidate_contract": (
            {
                "formal_evaluation_requires_formalizer_lean_candidate": True,
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
                runtime_environment_feedback,
            )
        ),
        "required_output_contract": _formalizer_output_contract_for_prompt(
            theory_packet=theory_packet,
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
            "The historical lean_statement_sketch field must contain the complete "
            "standalone model-authored Lean source, including every selected import, "
            "namespace/open command, declaration, and proof term. lean_imports is only "
            "a model-authored retrieval/lineage inventory; AgentRuntime does not inject "
            "it into or otherwise edit lean_statement_sketch. "
        )
    else:
        lean_candidate_instruction = ""
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
        + "Set candidate status to NEEDS_KERNEL_CHECK; use FORMAL_GAP only for an "
        "unresolved source target with no Lean source. Leave retrieval_queries and "
        "gap_taxonomy empty unless the current workspace has a concrete need; never "
        "invent work orders or routing scaffolding. "
        + theory_trace_alignment_prompt_instruction(theory_packet)
        + lean_candidate_instruction
        + "\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


FORMALIZER_SYSTEM_PROMPT = """\
You own one complete Lean source for one unchanged task-bound target. Choose every
import, definition, tactic, query, scratch experiment, and source revision from the
supplied theory, review findings, active-project tools, and raw Lean observations.
Compile early; use retrieval or scratch for concrete unresolved API and proof questions.
Never weaken the target or present admitted or diagnostic source as proof. Report a
precise active-environment gap instead of inventing an API. AgentRuntime preserves
identity, budgets, review, and kernel authority but never writes Lean for you.
"""


FORMALIZER_OUTPUT_CONTRACT: dict[str, Any] = {
    "theory_trace_alignment": {
        "referenced_claim_ids": ["exact claim_index ids consumed by this artifact"],
        "rationale": "short reason these claims are directly consumed",
    },
    "formal_targets": [
        {
            "id": "string",
            "formal_target_role": (
                "SOURCE_THEOREM_CANDIDATE|SOURCE_THEOREM_FORMAL_GAP|"
                "HELPER_OR_SUPPORT; single generated routing authority, not proof evidence"
            ),
            "informal_source": "string",
            "lean_statement_sketch": (
                "complete standalone model-authored Lean source, including imports, "
                "declarations, and proof term when expected_status is NEEDS_KERNEL_CHECK; "
                "AgentRuntime does not inject imports or edit this source"
            ),
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
    "retrieval_queries": [],
    "gap_taxonomy": [],
}


def _formalizer_output_contract_for_prompt(
    *,
    theory_packet: Mapping[str, Any],
) -> dict[str, Any]:
    contract = deepcopy(FORMALIZER_OUTPUT_CONTRACT)
    contract.pop("theory_trace_alignment", None)
    if compact_theory_derivation_trace(theory_packet):
        contract["theory_trace_alignment"] = theory_trace_alignment_output_contract(
            theory_packet
        )
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
        "retrieval_queries",
        "gap_taxonomy",
    ],
    "properties": {
        "formal_targets": {
            "type": "array",
            "minItems": 1,
            "maxItems": FORMALIZER_MAX_ACTIVE_TARGETS,
            "items": FORMAL_TARGET_PROVIDER_JSON_SCHEMA,
        },
        "retrieval_queries": {"type": "array"},
        "gap_taxonomy": {"type": "array"},
    },
}


def _formalizer_json_schema(
    *,
    theory_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    schema = deepcopy(FORMALIZER_JSON_SCHEMA)
    if compact_theory_derivation_trace(theory_packet or {}):
        schema["properties"]["theory_trace_alignment"] = (
            theory_trace_alignment_json_schema(theory_packet or {})
        )
        schema["required"].append("theory_trace_alignment")
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
    elif not isinstance(packet.get("formal_targets"), list):
        errors.append("formal_targets must be an array")
    elif len(packet["formal_targets"]) != FORMALIZER_MAX_ACTIVE_TARGETS:
        errors.append(
            "Formalizer workspace must own exactly one active formal target"
        )
    for field in ("retrieval_queries", "gap_taxonomy"):
        if not isinstance(packet.get(field), list):
            errors.append(f"missing or invalid field: {field}")
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
    return sorted(set(errors))


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
            and contract.get("formal_evaluation_requires_formalizer_lean_candidate")
            is True
        ):
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
) -> list[str]:
    """Require one complete model-authored Lean candidate for capability evals."""

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
    if not candidate_targets:
        return [
            *role_errors,
            "capability_eval requires at least one model-authored complete Lean "
            "source in formal_targets"
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
    return errors


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
    environment_feedback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    del environment_feedback
    body = deepcopy(dict(payload))
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


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM Formalizer/ProofEngineer")


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
        compact[key] = _compact_value(row.get(key))
    return compact


def _model_owned_formalizer_feedback_instructions(
    runtime_environment_feedback: Mapping[str, Any],
) -> list[str]:
    if not runtime_environment_feedback:
        return []

    return [
        (
            "Treat current workspace state and environment feedback as observations, "
            "not as a runtime-authored proof or edit plan. They are tool results; "
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
            "Use the provider output schema to return the next complete candidate. "
            "When the available source and verifier observations are insufficient, "
            "return a precise blocker naming the missing evidence instead of inventing it."
        ),
    ]


def _complete_lean_candidate_revision_feedback(
    feedback: Mapping[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    """Carry source-relevant observations without replaying prior tool transcripts."""

    if not isinstance(feedback, Mapping):
        return {}
    context_payload = feedback.get("formalizer_workspace_context", {})
    context = (
        context_payload if isinstance(context_payload, Mapping) else {}
    )
    context_fields = (
        "context_kind",
        "target_lean_declaration",
        "target_theorem_name",
        "target_theorem_statement",
        "target_theorem_statement_hash",
        "target_theorem_statement_hash_algorithm",
        "source_theorem_target_identity_status",
        "source_theorem_target_provenance",
        "semantic_alignment_constraints",
        "compiler_feedback",
        "formalizer_candidate_semantic_review_status",
        "formalizer_candidate_semantic_review_execution_id",
        "formalizer_candidate_semantic_review_packet_id",
        "formalizer_candidate_semantic_review_packet_hash",
        "formalizer_candidate_semantic_review_candidate_source_hash",
        "formalizer_candidate_semantic_review_target_statement_hash",
        "formalizer_candidate_semantic_review_target_statement_hash_algorithm",
        "formal_source_grounding_policy",
        "source_scope_ids",
    )
    target_observations = {
        field: deepcopy(context[field])
        for field in context_fields
        if context.get(field) not in (None, "", [], {})
    }

    candidate_fields = (
        "candidate_id",
        "candidate_kind",
        "source_hash",
        "candidate_lean_declaration",
        "target_lean_declaration",
        "precheck_errors",
        "blocking_precheck_errors",
        "local_lean_attempted",
        "local_lean_source_compiled",
        "local_lean_compiled",
        "local_lean_exit_status",
        "local_lean_stdout",
        "local_lean_stderr",
        "candidate_identity_lean_checked",
        "candidate_identity_lean_verified",
        "candidate_identity_lean_exit_status",
        "candidate_identity_lean_stdout",
        "candidate_identity_lean_stderr",
        "candidate_declaration_elaborated",
        "candidate_development_status",
        "candidate_axiom_names",
        "candidate_untrusted_axiom_names",
        "candidate_axiom_audit_checked",
        "candidate_axiom_audit_clean",
        "proof_evidence_status",
    )
    candidate_observation: dict[str, Any] = {}
    for collection_name in ("candidate_diagnostics", "candidate_rows"):
        rows = feedback.get(collection_name, [])
        if not isinstance(rows, list | tuple):
            continue
        match = next(
            (
                row
                for row in rows
                if isinstance(row, Mapping)
                and (
                    not candidate_id
                    or str(row.get("candidate_id", "") or "") == candidate_id
                )
            ),
            None,
        )
        if isinstance(match, Mapping):
            candidate_observation = {
                field: deepcopy(match[field])
                for field in candidate_fields
                if field in match
                and match.get(field) not in (None, "", [], {})
            }
            break

    checkpoint_payload = feedback.get("formalizer_recovery_checkpoint", {})
    checkpoint = (
        checkpoint_payload if isinstance(checkpoint_payload, Mapping) else {}
    )
    checkpoint_fields = (
        "artifact_kind",
        "candidate_id",
        "candidate_lean_declaration",
        "parent_source_hash",
        "current_source_hash",
        "checkpoint_id",
        "resumed_from_checkpoint_id",
        "resumable",
        "source_updates",
        "declaration_updates",
        "searches",
        "proof_searches",
        "state_inspections",
        "declaration_inspections",
        "checks",
        "turns",
        "tool_calls",
        "transcript_fingerprint",
        "provider",
        "model",
        "model_tier",
        "runtime_selected_lean_code",
        "model_owned_lean_code",
        "kernel_verified",
        "proof_evidence_status",
    )
    model_checkpoint = {
        field: deepcopy(checkpoint[field])
        for field in checkpoint_fields
        if field in checkpoint
    }

    validation_payload = feedback.get("formalizer_validation_feedback", {})
    validation = (
        validation_payload if isinstance(validation_payload, Mapping) else {}
    )
    validation_observation = {
        field: deepcopy(validation[field])
        for field in (
            "feedback_id",
            "validation_label",
            "validation_error_messages",
            "validation_error_fingerprint",
            "rejected_packet_fingerprint",
            "rejected_packet_projection",
            "retry_depth",
        )
        if validation.get(field) not in (None, "", [], {})
    }
    payload = {
        "active_candidate_id": candidate_id,
        "feedback_type": str(feedback.get("feedback_type", "") or ""),
        "failure_classification": str(
            feedback.get("failure_classification", "") or ""
        ),
        "overall_verdict": str(feedback.get("overall_verdict", "") or ""),
        "target_and_environment_observations": target_observations,
        "candidate_diagnostics": (
            [candidate_observation] if candidate_observation else []
        ),
        "semantic_review": {
            "dimension_reviews": deepcopy(
                list(feedback.get("dimension_reviews", []) or [])
            ),
            "findings": deepcopy(list(feedback.get("findings", []) or [])),
            "semantic_review_execution_id": str(
                feedback.get("semantic_review_execution_id", "") or ""
            ),
            "semantic_review_packet_id": str(
                feedback.get("semantic_review_packet_id", "") or ""
            ),
            "semantic_review_packet_hash": str(
                feedback.get("semantic_review_packet_hash", "") or ""
            ),
        },
        "model_revision_checkpoint": model_checkpoint,
        "validator_observation": validation_observation,
        "validation_errors": deepcopy(
            list(feedback.get("validation_errors", []) or [])
        ),
        "lineage_refs": {
            field: deepcopy(feedback[field])
            for field in (
                "feedback_id",
                "failure_id",
                "source_manifest_id",
                "source_manifest_path",
                "candidate_materialization_id",
                "candidate_source_hash",
                "source_formalizer_packet_id",
                "source_theory_packet_id",
                "source_theory_packet_hash",
                "target_theorem_statement_hash",
                "target_theorem_statement_hash_algorithm",
            )
            if feedback.get(field) not in (None, "", [], {})
        },
        "boundaries": {
            field: deepcopy(feedback[field])
            for field in (
                "evidence_boundary",
                "proof_evidence_boundary",
                "proof_evidence_status",
            )
            if feedback.get(field) not in (None, "", [], {})
        },
    }
    return payload


def compact_lean_workspace_observation(
    feedback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project one resumable Lean observation without copying workspace history."""

    if not isinstance(feedback, Mapping):
        return {}
    context = feedback.get("formalizer_workspace_context", {})
    candidate_id = str(feedback.get("candidate_id", "") or "")
    if not candidate_id and isinstance(context, Mapping):
        candidate_id = str(context.get("candidate_id", "") or "")
    projected = _complete_lean_candidate_revision_feedback(
        feedback,
        candidate_id=candidate_id,
    )
    compact = deepcopy(dict(projected.get("lineage_refs", {}) or {}))
    for field in (
        "source_artifact_kind",
        "feedback_type",
        "failure_classification",
        "overall_verdict",
        "proof_evidence_status",
        "proof_evidence_boundary",
    ):
        if feedback.get(field) not in (None, "", [], {}):
            compact[field] = deepcopy(feedback[field])
    target = projected.get("target_and_environment_observations", {})
    if isinstance(target, Mapping) and target:
        compact["formalizer_workspace_context"] = deepcopy(dict(target))
    diagnostics = projected.get("candidate_diagnostics", [])
    if isinstance(diagnostics, list) and diagnostics:
        compact["candidate_diagnostics"] = deepcopy(diagnostics)
    semantic_review = projected.get("semantic_review", {})
    if isinstance(semantic_review, Mapping):
        for field, value in semantic_review.items():
            if value not in (None, "", [], {}):
                compact[str(field)] = deepcopy(value)
    compact["source_observation_hash"] = stable_hash(dict(feedback))
    compact["source_observation_keys"] = sorted(str(key) for key in feedback)
    return compact


def _complete_formalizer_environment_observations(
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Preserve observations while withholding runtime-authored fix routing."""

    if not isinstance(feedback, Mapping):
        return {}
    projected = _without_runtime_authored_prescriptions(feedback)

    def compact_retrieval(child: Any) -> Any:
        if isinstance(child, Mapping):
            result: dict[str, Any] = {}
            for key, item in child.items():
                key_text = str(key)
                if key_text.endswith("_repair_feedback"):
                    key_text = (
                        key_text[: -len("_repair_feedback")]
                        + "_observations"
                    )
                if key_text == "formalizer_workspace_context":
                    key_text = "target_and_environment_observations"
                    if (
                        isinstance(item, Mapping)
                        and item.get("context_kind")
                        == "task_bound_formal_source_grounding"
                    ):
                        item = {
                            "context_kind": item.get("context_kind"),
                            "formal_source_grounding_hits": item.get(
                                "formal_source_grounding_hits", []
                            ),
                        }
                result[key_text] = (
                    compact_formal_source_grounding_hits_for_prompt(item)
                    if key_text == "formal_source_grounding_hits"
                    else compact_retrieval(item)
                )
            return result
        if isinstance(child, list | tuple):
            return [compact_retrieval(item) for item in child]
        return deepcopy(child)

    return compact_retrieval(projected)


def _compact_value(value: Any, *, depth: int = 0) -> Any:
    if isinstance(value, str):
        if len(value) <= FORMALIZER_MAX_TEXT_CHARS:
            return value
        marker = f"\n... <{len(value) - FORMALIZER_MAX_TEXT_CHARS} chars omitted> ...\n"
        head_chars = FORMALIZER_MAX_TEXT_CHARS // 2
        tail_chars = FORMALIZER_MAX_TEXT_CHARS - head_chars
        return value[:head_chars] + marker + value[-tail_chars:]
    if depth >= 4:
        return "<nested value omitted>"
    if isinstance(value, Mapping):
        return {
            str(key): _compact_value(child, depth=depth + 1)
            for key, child in list(value.items())[:24]
            if not _is_runtime_authored_prescriptive_field(key)
            and child not in (None, "", [], {})
        }
    if isinstance(value, list | tuple):
        return [_compact_value(child, depth=depth + 1) for child in list(value)[:8]]
    return value


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, list | tuple) else 0
