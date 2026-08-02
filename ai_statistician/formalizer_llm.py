from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .formal_source_prompt_context import (
    compact_formal_source_grounding_hits_for_prompt,
)
from .formalizer_repair_policy import (
    formalizer_validation_repair_policy,
    render_formalizer_validation_repair_policy_instructions,
)
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .lean_proof_agent_contract import without_legacy_python_lean_strategy_fields
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .pseudo_formalization import (
    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
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
    normalize_pseudo_formal_packet,
    pseudo_formal_block_work_order_rows,
    pseudo_formal_provider_envelope_json_schema,
    pseudo_formal_routable_work_order_rows,
    pseudo_formal_validation_issue_repair_actions,
    pseudo_formal_validation_issue_summary,
    pseudo_formal_work_order_row_has_required_lineage,
    pseudo_formal_work_order_row_has_semantic_requirements,
    pseudo_formal_work_order_row_has_source_anchor,
    pseudo_formalizer_prompt_contract,
    validate_pseudo_formal_packet,
)
from .research_schema import OpenResearchQuestion
from .semantic_review_feedback import compact_semantic_review_feedback
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


def formalizer_proof_construction_strategy_contract() -> dict[str, Any]:
    """Context-efficient, feedback-driven policy for Lean proof construction."""

    return {
        "schema_version": 12,
        "specification": (
            "Bind the exact Lean target to its faithful mathematical statement and "
            "assumptions, qualified local signatures, current lemma frontier, and "
            "verification boundary. Never weaken the target."
        ),
        "context_policy": (
            "Use qualified signatures and active import visibility, keeping module and "
            "namespace identity separate. Source docs, naming, and textbook citations "
            "rank candidates only. Initial authoring may receive one bounded intent "
            "anchor; repairs receive the live Lean goal or diagnostic and only relevant "
            "premise signatures. Never send source files or proof bodies."
        ),
        "statement_audit": (
            "Audit domain, measurability, integrability, finiteness, nonemptiness, "
            "topology, quantifiers, and nontrivial inequalities. Persistent failure "
            "triggers independent statement and counterexample review."
        ),
        "decomposition": (
            "Emit only the current dependency-ordered frontier. Keep one semantic "
            "obligation per node, explicit support edges, and a leaf small enough for "
            "one compiler-feedback episode. Preserve verified ancestors; use an empty "
            "lemma_dependency_plan for a direct proof."
        ),
        "feedback_loop": (
            "Fix Lean errors one-by-one from the smallest diagnostic. Every retry "
            "binds the failed candidate and changed proof state; do not repeat an "
            "unchanged attempt or rewrite a sound proof structure without evidence."
        ),
        "library_design": (
            "Build at the lowest reusable mathematical layer. Follow source-local "
            "namespace/module organization and stable semantic names; textbook numbers "
            "remain citation metadata, not declaration names."
        ),
        "reuse_policy": (
            "Reuse exact visible declarations first. Version-mismatched retrieval is "
            "context only; re-elaborate every selected declaration and generated "
            "candidate in the active project, then remove warnings and dead facts."
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
        requires_repeated_syntax_contract = (
            _feedback_has_repeated_syntax_failure_contract(
                environment_feedback or {}
            )
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
                    {"provider_structured_output": True}
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
            errors = validate_formalizer_packet(packet)
            errors.extend(
                _validate_source_theorem_candidate_materialization_packet(
                    packet,
                    environment_feedback=environment_feedback or {},
                    proof_bank_runtime_memory_summary=(
                        proof_bank_runtime_memory_summary or {}
                    ),
                )
            )
            errors.extend(
                _validate_exact_source_theorem_whole_proof_repair_packet(
                    packet,
                    proof_bank_runtime_memory_summary=(
                        proof_bank_runtime_memory_summary or {}
                    ),
                )
            )
            if requires_lean_candidate or requires_repeated_syntax_contract:
                errors.extend(
                    _validate_capability_eval_formalizer_lean_candidate_packet(
                        packet,
                        environment_feedback=environment_feedback or {},
                        proof_bank_runtime_memory_summary=(
                            proof_bank_runtime_memory_summary or {}
                        ),
                    )
                )
            if requires_pseudo_formalization:
                errors.extend(
                    _validate_required_pseudo_formalization_packet(
                        packet,
                        environment_feedback=environment_feedback or {},
                        proof_bank_runtime_memory_summary=(
                            proof_bank_runtime_memory_summary or {}
                        ),
                    )
                )
            return sorted(set(errors))

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_packet,
            validation_label="LLM Formalizer/ProofEngineer packet",
            max_repair_attempts=self.config.max_repair_attempts,
            repair_context_builder=lambda **kwargs: _formalizer_repair_context(
                errors=kwargs.get("errors", []),
                question=question,
                theory_packet=theory_packet,
                theorem_goals=theorem_goals,
                invalid_packet=kwargs.get("invalid_packet"),
                environment_feedback=environment_feedback or {},
                proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary
                or {},
            ),
            semantic_patch_repair=True,
        )


def _formalizer_repair_context(
    *,
    errors: Sequence[Any],
    question: OpenResearchQuestion | None = None,
    theory_packet: Mapping[str, Any] | None = None,
    theorem_goals: Sequence[Mapping[str, Any]] | None = None,
    invalid_packet: Mapping[str, Any] | None = None,
    environment_feedback: Mapping[str, Any] | None = None,
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    error_rows = list(
        dict.fromkeys(str(error) for error in errors if str(error).strip())
    )
    error_text = " ".join(error_rows).lower()
    pseudo_formal_required = _feedback_requires_pseudo_formalization(
        environment_feedback or {},
        proof_bank_runtime_memory_summary or {},
    )
    pseudo_formal_error = any(
        marker in error_text
        for marker in (
            "pseudo_formal",
            "pf/bv",
            "missing source_anchors",
            "missing conclusion",
            "lane-routable",
            "block_verification",
        )
    )
    whole_proof_repair_error = any(
        marker in error_text
        for marker in (
            "exact source theorem whole-proof repair",
            "target_theorem_statement exactly",
            "provenance must keep target_lean_declaration",
        )
    )
    typed_packet_repair_context = _formalizer_typed_packet_repair_context(
        errors=error_rows,
        theory_packet=theory_packet or {},
        theorem_goals=theorem_goals or (),
        invalid_packet=invalid_packet,
    )
    if whole_proof_repair_error:
        diagnostics = [
            row
            for row in (proof_bank_runtime_memory_summary or {}).get(
                "source_theorem_exact_proof_body_repair_diagnostics", []
            )
            or []
            if isinstance(row, Mapping)
        ]
        diagnostic = diagnostics[0] if diagnostics else {}
        return {
            **typed_packet_repair_context,
            "repair_mode": "exact_source_theorem_whole_proof_repair",
            "target_lean_declaration": str(
                diagnostic.get("target_theorem_name", "") or ""
            ),
            "target_theorem_statement": str(
                diagnostic.get("target_theorem_statement", "") or ""
            ),
            "required_outcomes": [
                "preserve target_theorem_statement exactly modulo whitespace and replace only the proof after `:= by`",
                "or remove the invalid source candidate and emit a typed FORMAL_GAP with a concrete retrieval/dependency work order",
            ],
            "forbidden_repairs": [
                "renaming the target declaration",
                "changing binders or conclusion",
                "sorry/admit/axiom/unsafe placeholders",
                "inventing an unverified helper while presenting the source theorem as executable",
            ],
        }
    if not pseudo_formal_required and not pseudo_formal_error:
        return typed_packet_repair_context

    validation_issue_summary = pseudo_formal_validation_issue_summary(error_rows)
    issue_specific_repair_actions = (
        pseudo_formal_validation_issue_repair_actions(validation_issue_summary)
    )
    required_target_lanes = _required_pseudo_formal_target_lanes(
        environment_feedback or {},
        proof_bank_runtime_memory_summary or {},
    )
    component_gate_failure_repair_seed = (
        _pseudo_formal_component_gate_failure_repair_seed(
            proof_bank_runtime_memory_summary or {},
            required_target_lanes=required_target_lanes,
        )
    )
    packet_seed = component_gate_failure_repair_seed or (
        _pseudo_formalization_required_packet_seed(
            question=question,
            theory_packet=theory_packet or {},
            environment_feedback=environment_feedback or {},
            proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary or {},
        )
    )
    concrete_repair_seed = _pseudo_formal_concrete_lane_routable_repair_seed(
        packet_seed,
        required_target_lanes=required_target_lanes,
    )
    copy_fragment = _pseudo_formalization_required_copy_fragment(
        packet_seed,
        required_target_lanes=required_target_lanes,
    )
    if copy_fragment.get("pseudo_formal_proof_packets"):
        concrete_repair_seed = dict(
            copy_fragment["pseudo_formal_proof_packets"][0]
        )
    suggested_target_lanes = [
        PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
        PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
        PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
    ]
    return {
        **typed_packet_repair_context,
        "context_kind": "formalizer_validation_repair_context",
        "context_reason": "pseudo_formal_packet_repair",
        "pseudo_formal_activation_required": pseudo_formal_required,
        "detected_validation_errors": error_rows[:6],
        "pseudo_formal_validation_issue_summary": validation_issue_summary,
        "pseudo_formal_issue_specific_repair_actions": issue_specific_repair_actions,
        "validation_repair_policy": formalizer_validation_repair_policy(error_rows),
        "repair_prompt_priority_instructions": [
            (
                "PF/BV repair is binding: emit pseudo_formal_proof_packets; do "
                "not answer only with formal_targets, gap_taxonomy, or next_actions."
            ),
            (
                "Copy subsystem_repair_context.pseudo_formal_required_repair_blueprint."
                "copy_ready_response_fragment.pseudo_formal_proof_packets[0] "
                "or concrete_lane_routable_repair_seed into pseudo_formal_proof_packets[0] "
                "when present; preserve conclusion, source_anchors, "
                "semantic_primitive_requirements, lean_feasibility, "
                "faithfulness_status, proof_evidence_status, kernel_verified=false, "
                "and source_theorem_kernel_verified=false."
            ),
            (
                "Treat pseudo_formal_required_repair_blueprint."
                "copy_ready_response_fragment.validator_ready_copy_contract as a "
                "machine-checkable copy contract. Copy the listed source path to "
                "the listed output path before adding optional prose or Lean targets."
            ),
            (
                "The repaired PF/BV packet must produce at least one effective "
                "lane-routable work-order row; for "
                "source_theorem_exact_semantic_definition use "
                "faithfulness_status=faithful, "
                "lean_feasibility=needs_semantic_definition, and non-empty "
                "semantic_primitive_requirements."
            ),
            (
                "Every PF/BV block must keep top-level conclusion and source_anchors "
                "fields; do not move them into prose, proof_text, anchors, or "
                "next_actions."
            ),
        ],
        "repair_prompt_required_output_paths": [
            "pseudo_formal_proof_packets[0].blocks[0].conclusion",
            "pseudo_formal_proof_packets[0].blocks[0].source_anchors",
            "pseudo_formal_proof_packets[0].blocks[0].semantic_primitive_requirements",
            "pseudo_formal_proof_packets[0].blocks[0].lean_feasibility",
        ],
        "pseudo_formal_required_repair_blueprint": {
            "output_key": "pseudo_formal_proof_packets",
            "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
            "kernel_verified": False,
            "source_theorem_kernel_verified": False,
            "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
            "method_contract_id": PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
            "required_target_lanes": required_target_lanes,
            "suggested_target_lanes_when_unspecified": suggested_target_lanes,
            "allowed_target_lanes": list(PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES),
            "copy_or_complete_this_packet_seed": packet_seed,
            "concrete_lane_routable_repair_seed": concrete_repair_seed,
            "component_gate_failure_repair_seed": (
                component_gate_failure_repair_seed
            ),
            "copy_ready_response_fragment": copy_fragment,
            "validator_ready_copy_contract": (
                copy_fragment.get("validator_ready_copy_contract", {})
                if isinstance(copy_fragment, Mapping)
                else {}
            ),
            "concrete_repair_seed_usage": (
                "Copy copy_ready_response_fragment.pseudo_formal_proof_packets[0] "
                "or concrete_lane_routable_repair_seed into "
                "pseudo_formal_proof_packets[0] when the prior packet missed "
                "conclusion, source_anchors, semantic_primitive_requirements, "
                "or lane-routable exact-semantic-definition/source_to_bridge "
                "rows. Preserve its non-proof boundary."
            ),
            "minimum_valid_packet": {
                "theorem_id": "<copy the blocked theorem/source theorem id>",
                "source_artifact_id": "<copy theory packet, proof body, or source artifact id>",
                "blocks": [
                    {
                        "block_id": "pf_block_1",
                        "block_type": "lemma",
                        "block_depth": 1,
                        "premises": ["<bounded local premise text>"],
                        "conclusion": "<required non-empty local mathematical claim>",
                        "proof_text": "<bounded local source proof text or blocker rationale>",
                        "dependency_ids": [],
                        "scope_parent_id": "",
                        "dependency_scope": "earlier_block_statement_only",
                        "inherited_scope": [],
                        "source_anchors": [
                            {
                                "kind": "theory_trace|paper|proof_body|theorem_card|other",
                                "id": "<required non-empty source id>",
                                "excerpt": "<required bounded source excerpt or pointer>",
                            }
                        ],
                        "semantic_primitive_requirements": [
                            "<non-empty primitive/source object id when routing exact-semantic-definition or source_to_bridge work>"
                        ],
                        "lean_feasibility": "needs_semantic_definition",
                        "faithfulness_status": "faithful",
                        "faithfulness_repair": {
                            "status": "not_required",
                            "attempts": 0,
                            "flagged_discrepancies": [],
                        },
                        "block_verification": {
                            "verdict": "unknown",
                            "verifier_provenance": "not_run",
                            "independent_verifier": False,
                            "rollout_count": 0,
                        },
                    }
                ],
            },
            "field_inferred_lane_recipes": [
                {
                    "target_lane": PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
                    "required_block_fields": {
                        "faithfulness_status": "faithful",
                        "lean_feasibility": "needs_semantic_definition",
                        "semantic_primitive_requirements": [
                            "<one or more primitive/source object ids to define>"
                        ],
                    },
                },
                {
                    "target_lane": PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
                    "required_block_fields": {
                        "faithfulness_status": "faithful",
                        "lean_feasibility": "needs_rag",
                    },
                },
                {
                    "target_lane": PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
                    "required_block_fields": {
                        "faithfulness_status": "faithful",
                        "semantic_primitive_requirements": ["<one or more primitive ids>"],
                    },
                },
                {
                    "target_lane": PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS,
                    "required_block_fields": {
                        "faithfulness_status": "faithful",
                        "lean_feasibility": "lean_now",
                        "block_verification": {
                            "verdict": "accepted",
                            "rollout_count": "integer >= 1",
                            "independent_verifier": True,
                        },
                    },
                },
                {
                    "target_lane": PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                    "required_block_fields": {
                        "faithfulness_status": "needs_review|unfaithful|unchecked",
                        "repair_metadata": "faithfulness_repair explains the blocker",
                    },
                },
            ],
            "do_not_repeat": [
                "do not omit top-level conclusion",
                "do not omit source_anchors or leave id/excerpt empty",
                "do not use needs_review as block_verification.verdict",
                "do not emit exact semantic-definition rows without semantic_primitive_requirements",
                "do not claim kernel verification or proof evidence",
                "do not return only generic diagnostic rows when a target lane is required",
            ],
        },
    }


def _formalizer_typed_packet_repair_context(
    *,
    errors: Sequence[str],
    theory_packet: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
    invalid_packet: Mapping[str, Any] | None,
) -> dict[str, Any]:
    rejected_packet = dict(invalid_packet) if isinstance(invalid_packet, Mapping) else {}
    rejected_targets = [
        deepcopy(dict(row))
        for row in rejected_packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
    ][:3]
    source_target_binding_options: list[dict[str, Any]] = []
    seen_binding_options: set[str] = set()

    def add_source_identity(
        raw_goal: Mapping[str, Any],
        *,
        source_kind: str,
        source_path: str,
    ) -> None:
        source_theorem_goal_id = next(
            (
                str(raw_goal.get(key, "") or "").strip()
                for key in ("goal_id", "theorem_id", "target_id", "id")
                if str(raw_goal.get(key, "") or "").strip()
            ),
            "",
        )
        declaration_keys = (
            ("target_lean_declaration", "lean_declaration", "name")
            if source_kind == "theorem_goal"
            else ("target_lean_declaration", "lean_declaration")
        )
        target_lean_declaration = next(
            (
                str(raw_goal.get(key, "") or "").strip()
                for key in declaration_keys
                if str(raw_goal.get(key, "") or "").strip()
            ),
            "",
        )
        if source_theorem_goal_id or target_lean_declaration:
            binding_option = {
                "source_kind": source_kind,
                "source_path": source_path,
                "source_theorem_goal_id": source_theorem_goal_id,
                "target_lean_declaration": target_lean_declaration,
                "semantic_statement": next(
                    (
                        deepcopy(raw_goal[key])
                        for key in (
                            "statement",
                            "informal_statement",
                            "claim",
                            "conclusion",
                        )
                        if raw_goal.get(key) not in (None, "", [], {})
                    ),
                    "",
                ),
            }
            binding_fingerprint = stable_hash(
                {
                    key: value
                    for key, value in binding_option.items()
                    if key != "source_path"
                }
            )
            if binding_fingerprint not in seen_binding_options:
                seen_binding_options.add(binding_fingerprint)
                source_target_binding_options.append(binding_option)

    for index, raw_goal in enumerate(
        theorem_goals[:FORMALIZER_MAX_THEOREM_GOALS]
    ):
        if not isinstance(raw_goal, Mapping):
            continue
        add_source_identity(
            raw_goal,
            source_kind="theorem_goal",
            source_path=f"theorem_goals[{index}]",
        )

    derivation_packet = theory_packet.get("theory_derivation_packet", {})
    if not isinstance(derivation_packet, Mapping):
        derivation_packet = {}
    theorem_card_sources = (
        ("theory_packet.theorem_cards", theory_packet.get("theorem_cards", [])),
        (
            "theory_packet.theory_derivation_packet.theorem_cards",
            derivation_packet.get("theorem_cards", []),
        ),
    )
    for source_path, raw_cards in theorem_card_sources:
        if not isinstance(raw_cards, (list, tuple)):
            continue
        for index, raw_card in enumerate(raw_cards[:FORMALIZER_MAX_THEOREM_GOALS]):
            if not isinstance(raw_card, Mapping):
                continue
            add_source_identity(
                raw_card,
                source_kind="theorem_card",
                source_path=f"{source_path}[{index}]",
            )

    formalization_request_context: list[dict[str, Any]] = []
    for raw_request in theory_packet.get("formalization_requests", []) or []:
        if not isinstance(raw_request, Mapping):
            continue
        request_row = {
            key: deepcopy(raw_request[key])
            for key in (
                "id",
                "target",
                "target_theorem_card",
                "claim",
                "statement",
                "lean_stub",
                "lean4_sketch",
                "open_obligations",
            )
            if raw_request.get(key) not in (None, "", [], {})
        }
        if request_row:
            formalization_request_context.append(request_row)
        if len(formalization_request_context) >= FORMALIZER_MAX_THEOREM_GOALS:
            break
    return {
        "context_kind": "formalizer_validation_repair_context",
        "context_reason": "typed_packet_contract_repair",
        "detected_validation_errors": [str(error) for error in errors[:8]],
        "rejected_packet_fingerprint": (
            stable_hash(rejected_packet) if rejected_packet else ""
        ),
        "rejected_packet_excerpt": {
            "formal_targets": rejected_targets,
            "theory_trace_alignment": deepcopy(
                rejected_packet.get("theory_trace_alignment", {})
            ),
            "gap_taxonomy": [
                deepcopy(dict(row))
                for row in rejected_packet.get("gap_taxonomy", []) or []
                if isinstance(row, Mapping)
            ][:3],
            "next_actions": [
                deepcopy(dict(row))
                for row in rejected_packet.get("next_actions", []) or []
                if isinstance(row, Mapping)
            ][:3],
        },
        "source_target_binding_options": source_target_binding_options,
        "source_target_identity_available": bool(source_target_binding_options),
        "formalization_request_context": formalization_request_context,
        "formal_target_role_contract": {
            FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE: {
                "expected_status": "NEEDS_KERNEL_CHECK",
                "lean_statement_sketch": "nonempty whole-target candidate",
                "candidate_lean_declaration": "required exact emitted declaration",
                "source_identity": (
                    "AgentRuntime mechanically binds candidate_lean_declaration as "
                    "the candidate target declaration; bind a matching source theorem "
                    "goal id when one is available"
                ),
            },
            FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP: {
                "expected_status": "FORMAL_GAP",
                "lean_statement_sketch": "empty",
                "candidate_lean_declaration": "empty",
                "source_identity": (
                    "target_lean_declaration or source_theorem_goal_id required"
                ),
            },
            FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT: {
                "expected_status": "NEEDS_KERNEL_CHECK or FORMAL_GAP",
                "lean_statement_sketch": (
                    "nonempty exactly when expected_status=NEEDS_KERNEL_CHECK"
                ),
                "candidate_lean_declaration": (
                    "required exactly when a Lean candidate is emitted"
                ),
                "source_identity": "must not claim source-theorem identity",
            },
        },
        "repair_prompt_priority_instructions": [
            (
                "Use rejected_packet_excerpt as the exact normalized failed packet; "
                "preserve unaffected content and repair every detected validation error."
            ),
            (
                "Choose exactly one formal_target_role contract per row and make its "
                "status, Lean source, candidate declaration, and source identity "
                "coherent; never combine fields from different roles."
            ),
            (
                "When a source-theorem gap lacks identity, copy a semantically exact "
                "goal id or declaration from source_target_binding_options. Theorem "
                "card ids are valid source_theorem_goal_id values when that card is "
                "the exact target. Do not invent a binding merely to pass validation."
            ),
            (
                "Retain SOURCE_THEOREM_CANDIDATE "
                "only when its whole-target Lean candidate is complete, placeholder-"
                "free, and has an exact emitted candidate_lean_declaration; AgentRuntime "
                "mechanically binds that duplicate candidate declaration into source "
                "provenance. Otherwise fail closed to SOURCE_THEOREM_FORMAL_GAP, clear "
                "both Lean fields, and bind the semantically matching theorem-card/goal "
                "id."
            ),
            (
                "If source_target_identity_available=false, do not retain a "
                "SOURCE_THEOREM_CANDIDATE or SOURCE_THEOREM_FORMAL_GAP claim: relabel "
                "genuine support as HELPER_OR_SUPPORT or remove the row and record "
                "the missing source identity as a typed gap."
            ),
            (
                "Keep the repaired packet compact and leave optional arrays empty when "
                "unused; do not expand the packet while fixing a local contract error."
            ),
        ],
    }


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
        keys=("id", "title", "claim", "claim_type", "statement", "proof_obligations"),
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
    runtime_environment_feedback = _compact_formalizer_environment_feedback(
        environment_feedback or {}
    )
    requires_lean_candidate = _feedback_requires_formalizer_lean_candidate(
        environment_feedback or {}
    )
    has_source_theorem_target_drift = _feedback_has_source_theorem_target_drift(
        environment_feedback or {}
    )
    repeated_syntax_fail_closed_active = (
        _feedback_has_repeated_syntax_failure_contract(environment_feedback or {})
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
    pseudo_formalization_active = _feedback_suggests_pseudo_formalization(
        environment_feedback or {},
        proof_memory_summary,
    )
    pseudo_formalization_required = _feedback_requires_pseudo_formalization(
        environment_feedback or {},
        proof_memory_summary,
    )
    required_pseudo_formal_target_lanes = _required_pseudo_formal_target_lanes(
        environment_feedback or {},
        proof_memory_summary,
    )
    component_gate_failure_repair_seed = (
        _pseudo_formal_component_gate_failure_repair_seed(
            proof_memory_summary,
            required_target_lanes=required_pseudo_formal_target_lanes,
        )
        if pseudo_formalization_required
        else {}
    )
    pseudo_formalization_packet_seed = (
        component_gate_failure_repair_seed
        or _pseudo_formalization_required_packet_seed(
            question=question,
            theory_packet=theory_packet,
            environment_feedback=environment_feedback or {},
            proof_bank_runtime_memory_summary=proof_memory_summary,
        )
        if pseudo_formalization_required
        else {}
    )
    pseudo_formalization_copy_fragment = (
        _pseudo_formalization_required_copy_fragment(
            pseudo_formalization_packet_seed,
            required_target_lanes=required_pseudo_formal_target_lanes,
        )
        if pseudo_formalization_required
        else {}
    )
    source_to_bridge_request_shortcuts = (
        _source_to_bridge_candidate_request_shortcuts(proof_memory_summary)
    )
    diagnostic_helper_bridge_blocker_contract = (
        _diagnostic_helper_bridge_blocker_contract(proof_memory_summary)
    )
    exact_semantic_definition_gate_active = (
        _source_theorem_exact_semantic_definition_gate_active(
            environment_feedback=environment_feedback or {},
            proof_bank_runtime_memory_summary=proof_memory_summary,
        )
    )
    source_theorem_candidate_materialization_contract = (
        {}
        if repeated_syntax_fail_closed_active or exact_semantic_definition_gate_active
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
        "proof_construction_strategy_contract": (
            formalizer_proof_construction_strategy_contract()
        ),
        "registered_proof_bank_obligation_catalog": catalog_rows,
        "registered_proof_bank_obligation_catalog_total": _safe_len(
            proof_bank_obligation_catalog or theorem_goals
        ),
        "proof_bank_runtime_memory_summary": proof_memory_summary,
        "source_to_bridge_candidate_request_shortcuts": (
            source_to_bridge_request_shortcuts
        ),
        "diagnostic_helper_bridge_blocker_contract": (
            diagnostic_helper_bridge_blocker_contract
        ),
        "source_theorem_candidate_materialization_contract": (
            source_theorem_candidate_materialization_contract
        ),
        "pseudo_formalization_contract": (
            pseudo_formalizer_prompt_contract()
            if pseudo_formalization_active
            else {}
        ),
        "pseudo_formalization_required_packet_seed": pseudo_formalization_packet_seed,
        "pseudo_formalization_component_gate_failure_repair_seed": (
            component_gate_failure_repair_seed
        ),
        "pseudo_formalization_required_copy_fragment": (
            pseudo_formalization_copy_fragment
        ),
        "runtime_environment_feedback": runtime_environment_feedback,
        "formalizer_lean_candidate_contract": (
            {
                "capability_eval_requires_formalizer_lean_candidate": True,
                "task_bound_formal_target_contract_fingerprint": (
                    task_bound_formal_target_contract.get("contract_fingerprint", "")
                ),
                "required_when_true": (
                    "include at least one concrete safe Lean theorem sketch with "
                    "expected_status=NEEDS_KERNEL_CHECK in either formal_targets or "
                    "source_to_bridge_premise_derivation_candidates; "
                    "proof_bank_obligation_requests alone do not satisfy this gate. "
                    "Every formal_targets Lean candidate must also provide "
                    "candidate_lean_declaration as the exact Lean-resolvable declaration "
                    "name emitted by lean_statement_sketch, including namespace "
                    "qualification when needed; this candidate identity is separate from "
                    "source_theorem_target_provenance.target_lean_declaration, and "
                    "AgentRuntime will not infer it by parsing generated Lean text and "
                    "will ask Lean to #check it. "
                    "A source_to_bridge_premise_derivation_candidates entry must copy "
                    "premise_candidate_declaration_name from the runtime request. "
                    "AgentRuntime will compile the exact source and ask Lean to #check "
                    "that identity; use the declaration kind and namespace organization "
                    "appropriate to the source library rather than encoding them as "
                    "validator assumptions. "
                    "When runtime target-shape feedback says a source theorem would "
                    "drift if repaired, emit that source theorem as FORMAL_GAP and "
                    "route helper/premise Lean candidates separately. A separate helper "
                    "formal_targets entry must set formal_target_role=HELPER_OR_SUPPORT "
                    "so local Lean/LSP can inspect a real artifact without promoting it "
                    "to source-theorem proof evidence. Use "
                    "formal_target_role=SOURCE_THEOREM_CANDIDATE only for a candidate "
                    "intended to preserve the whole task-bound theorem, and "
                    "formal_target_role=SOURCE_THEOREM_FORMAL_GAP for its empty-Lean "
                    "fail-closed gap row. formal_target_role is the single generated "
                    "routing authority; AgentRuntime derives legacy target-known metadata "
                    "from it. Roles are routing metadata, not proof claims."
                ),
                "not_proof_evidence": (
                    "the Lean candidate remains a proposal until AgentRuntime runs "
                    "local Lean/AXLE on that exact artifact"
                ),
            }
            if requires_lean_candidate
            else {}
        ),
        "mode_specific_instructions": _formalizer_mode_specific_instructions(
            proof_memory_summary,
            runtime_environment_feedback,
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
    metadata_authoring_mode = bool(
        _formalizer_bool_like(
            proof_memory_summary.get("source_to_bridge_metadata_authoring_required")
        )
        or proof_memory_summary.get("recommended_formalizer_target_mode")
        == "source_to_bridge_metadata_authoring_required"
    )
    if requires_lean_candidate and metadata_authoring_mode:
        lean_candidate_instruction = (
            "Capability-eval mode is active, but source-to-bridge metadata "
            "authoring takes priority: do not emit another helper-only Lean "
            "formal_targets entry just to satisfy the Lean-candidate gate. Keep "
            "the source theorem as expected_status=FORMAL_GAP with "
            "formal_target_role=SOURCE_THEOREM_FORMAL_GAP, and either emit a "
            "structured source_to_bridge_premise_derivation_candidate_requests "
            "object with the exact source-binding metadata, including "
            "premise_candidate_declaration_name, or record the missing metadata "
            "fields as a source_to_bridge_metadata_blocker. "
        )
    elif requires_lean_candidate and has_source_theorem_target_drift:
        lean_candidate_instruction = (
            "Capability-eval mode is active, but target-shape feedback takes "
            "priority: do not force a helper/arithmetic Lean sketch into "
            "formal_targets just to satisfy the candidate gate. Emit a "
            "NEEDS_KERNEL_CHECK Lean candidate only if it is either a faithful "
            "task-bound source-theorem target or a real "
            "source_to_bridge_premise_derivation_candidates object with copied "
            "source-binding metadata and semantic anchors. Otherwise emit the "
            "source theorem as expected_status=FORMAL_GAP with an empty Lean sketch "
            "and formal_target_role=SOURCE_THEOREM_FORMAL_GAP, "
            "and record the missing premise/API in gap_taxonomy/next_actions; the "
            "runtime validator accepts this fail-closed target-drift repair. "
        )
    elif requires_lean_candidate:
        lean_candidate_instruction = (
            "Capability-eval mode is active for Formalizer/ProofEngineer: include "
            "one compact concrete Lean theorem sketch with "
            "expected_status=NEEDS_KERNEL_CHECK and set candidate_lean_declaration "
            "to the exact declaration emitted by that sketch. Prefer the exact "
            "task-bound source "
            "theorem only when its objects, assumptions, quantifiers, and conclusion "
            "can be represented faithfully; mark that row "
            "formal_target_role=SOURCE_THEOREM_CANDIDATE. Otherwise keep that source "
            "theorem as FORMAL_GAP with "
            "formal_target_role=SOURCE_THEOREM_FORMAL_GAP and emit a clearly "
            "provenance-marked support row with "
            "formal_target_role=HELPER_OR_SUPPORT or a "
            "source_to_bridge candidate that advances a named dependency. Do not "
            "satisfy the packet using only "
            "proof_bank_obligation_requests, gap taxonomy, or queue work orders. "
        )
    else:
        lean_candidate_instruction = ""
    if pseudo_formalization_required:
        pseudo_formalization_instruction = (
            "Source theorem proof-body repair is blocked in the PF/BV activation "
            "regime: you must emit at least one pseudo_formal_proof_packets entry "
            "following pseudo_formalization_contract. The packet must decompose the "
            "blocked proof text into source-anchored blocks, record faithfulness/"
            "block-verification status, and produce at least one lane-routable "
            "residual block. Treat "
            "runtime_environment_feedback.pseudo_formalization_repair_contract, "
            "pseudo_formalization_validation_issue_summary, and "
            "pseudo_formalization_validation_issue_repair_actions as binding "
            "retry feedback when present; repair those exact issues before "
            "changing Lean targets. Start from "
            "pseudo_formalization_required_copy_fragment.pseudo_formal_proof_packets "
            "when present; otherwise start from pseudo_formalization_required_packet_seed. "
            "The copy fragment includes validator_ready_copy_contract; treat that "
            "contract as the shortest valid path and copy it before reconstructing "
            "PF/BV fields yourself. "
            "Copy its theorem_id, "
            "source_artifact_id, block_id pattern, conclusion, source_anchors, "
            "faithfulness_status, lean_feasibility, and non-proof boundary unless "
            "the runtime feedback gives a more specific source-bound replacement. "
            "Every block must carry a top-level conclusion field "
            "and at least one source_anchors object with a non-empty id or excerpt, "
            "for example {\"kind\":\"theory_trace\",\"id\":\"source_step\","
            "\"excerpt\":\"source proof step requiring exact grounding\"}. Do not "
            "put anchor names only in prose, comments, or next_actions. If "
            "block_verification.verdict "
            "is accepted, block_verification.rollout_count must be an integer >= 1; "
            "otherwise use a valid non-accepted block_verification.verdict value "
            "such as not_run, unknown, or failed rather than claiming accepted. "
            "Use needs_review only as a faithfulness_status value, not as a "
            "block_verification verdict. Runtime target-lane routing is inferred "
            "from block fields, not from prose: to route exact semantic-definition "
            "work, set faithfulness_status=faithful and "
            "lean_feasibility=needs_semantic_definition, and include non-empty "
            "semantic_primitive_requirements naming the primitive/source object "
            "that source lookup must define; to route Lean/RAG grounding, set "
            "faithfulness_status=faithful and lean_feasibility=needs_rag; to route "
            "source_to_bridge work, set faithfulness_status=faithful and include "
            "non-empty semantic_primitive_requirements. A packet with only needs_review or "
            "generic not_run blocks produces generic review rows and does not "
            "satisfy required PF/BV activation. These packets are decomposition and "
            "routing artifacts only: "
            "they do not satisfy the Lean-candidate gate, cannot claim kernel "
            "verification, and must route residual blocks through formal_targets, "
            "retrieval_queries, gap_taxonomy, source_to_bridge candidates/requests, "
            "or next_actions. "
        )
    elif pseudo_formalization_active:
        pseudo_formalization_instruction = (
            "When source theorem proof repair is blocked by missing semantic anchors, missing "
            "library support, or an overlarge proof step, you may emit pseudo_formal_proof_packets "
            "following pseudo_formalization_contract. Those packets are decomposition and routing "
            "artifacts only: they do not satisfy the Lean-candidate gate, cannot claim kernel "
            "verification, and must route residual blocks through formal_targets, retrieval_queries, "
            "gap_taxonomy, source_to_bridge candidates/requests, or next_actions. "
        )
    else:
        pseudo_formalization_instruction = ""
    return (
        "Return ONLY compact JSON matching required_output_contract, with at most 3 "
        "current-active-frontier items/list. Keep unrelated obligations separate "
        "across later packets rather than merging them. Treat "
        "task_bound_formal_target_contract as semantic authority and follow only "
        "activated mode_specific_instructions. Retrieved declarations are support APIs "
        "unless exact lineage identifies the source theorem; preserve that target and "
        "await AgentRuntime checking of the exact artifact. "
        + pseudo_formalization_instruction
        +
        "Do not use placeholder binder types, `sorry`, `admit`, "
        "`axiom`, `unsafe`, or `by?` in Lean sketches. Set candidate status to "
        "NEEDS_KERNEL_CHECK; use FORMAL_GAP only for an unrepaired source target with "
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
                    "sorry/admit/by?/exact?, or prose"
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
                "required_semantic_anchor_reference_names": [
                    "copy required semantic anchors and reference them in Lean source"
                ],
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
            "copy_from": (
                "pseudo_formalization_required_copy_fragment."
                "pseudo_formal_proof_packets"
            ),
            "validator_ready_copy_contract_path": (
                "pseudo_formalization_required_copy_fragment."
                "validator_ready_copy_contract"
            ),
            "validator_ready_copy_rule": (
                "Copy validator_ready_copy_contract.copy_source_path into "
                "validator_ready_copy_contract.copy_destination_path before "
                "optional edits; preserve every required_preserved_paths entry."
            ),
            "minimum_items": 1,
            "first_packet_must_include": [
                "blocks[0].conclusion",
                "blocks[0].source_anchors",
                "blocks[0].semantic_primitive_requirements",
                "blocks[0].faithfulness_status=faithful",
                "blocks[0].lean_feasibility=needs_semantic_definition|needs_rag",
                "kernel_verified=false",
                "source_theorem_kernel_verified=false",
                "proof_evidence_status=not_proof_evidence",
            ],
            "routing_gate": (
                "must produce at least one effective lane-routable PF/BV "
                "work-order row; generic diagnostic-only rows do not satisfy "
                "required PF/BV activation"
            ),
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


def _bind_formal_target_role_provenance(packet: dict[str, Any]) -> None:
    bindings: list[dict[str, Any]] = []
    for row in packet.get("formal_targets", []) or []:
        if not isinstance(row, dict):
            continue
        role = _formal_target_role(row)
        if role not in FORMAL_TARGET_ROLES:
            continue
        raw_provenance = row.get("source_theorem_target_provenance", {})
        provenance = (
            dict(raw_provenance) if isinstance(raw_provenance, Mapping) else {}
        )
        previous = _source_theorem_target_known(provenance)
        target_declaration_binding_source = str(
            provenance.get("target_lean_declaration_binding_source", "") or ""
        ).strip()
        if role == FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP:
            canonical = True
        elif role == FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT:
            canonical = False
        else:
            canonical = previous if previous is not None else False
            candidate_declaration = str(
                row.get("candidate_lean_declaration", "") or ""
            ).strip()
            target_declaration = str(
                provenance.get("target_lean_declaration", "") or ""
            ).strip()
            if candidate_declaration and not target_declaration:
                provenance["target_lean_declaration"] = candidate_declaration
                target_declaration_binding_source = "candidate_lean_declaration"
                provenance["target_lean_declaration_binding_source"] = (
                    target_declaration_binding_source
                )
        provenance["source_theorem_target_known"] = canonical
        row["source_theorem_target_provenance"] = provenance
        binding = {
            "target_id": str(row.get("id", "") or ""),
            "formal_target_role": role,
            "previous_source_theorem_target_known": previous,
            "source_theorem_target_known": canonical,
        }
        if target_declaration_binding_source:
            binding["target_lean_declaration_binding_source"] = (
                target_declaration_binding_source
            )
        bindings.append(binding)
    if bindings:
        packet["formal_target_role_provenance_bindings"] = bindings


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
        provenance = row.get("source_theorem_target_provenance", {})
        if isinstance(provenance, Mapping):
            declaration_error = _target_lean_declaration_identifier_error(
                provenance.get("target_lean_declaration", "")
            )
            if declaration_error:
                errors.append(
                    "source_theorem_target_provenance.target_lean_declaration "
                    + declaration_error
                )
        lean_statement_sketch = str(row.get("lean_statement_sketch", "") or "")
        placeholder_error = _lean_statement_placeholder_syntax_error(
            lean_statement_sketch
        )
        if placeholder_error:
            errors.append(f"formal target Lean sketch {placeholder_error}")
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
        declaration_errors = _source_to_bridge_candidate_declaration_contract_errors(row)
        errors.extend(declaration_errors)
        if not _source_to_bridge_candidate_has_source_binding_contract(row):
            errors.append(
                "source_to_bridge_premise_derivation_candidates entry missing "
                "source-binding contract metadata; include a "
                "source_to_bridge_premise_derivation_candidate_request_id/object, "
                "a source_to_bridge_grouped_premise_derivation_candidate_request_id/object, "
                "or explicit required_semantic_anchor_reference_names and "
                "adapter_object_names_requiring_source_instantiation from the "
                "runtime memory request"
            )
        placeholder_error = _lean_statement_placeholder_syntax_error(candidate_source)
        if placeholder_error:
            errors.append(
                "source_to_bridge_premise_derivation_candidates Lean candidate "
                + placeholder_error
            )
        vacuous_error = _source_to_bridge_candidate_vacuous_truth_error(
            candidate_source
        )
        if vacuous_error:
            errors.append(
                "source_to_bridge_premise_derivation_candidates Lean candidate "
                + vacuous_error
            )
        missing_anchor_names = _source_to_bridge_candidate_missing_anchor_references(
            row,
            candidate_source,
        )
        if missing_anchor_names:
            errors.append(
                "source_to_bridge_premise_derivation_candidates Lean candidate "
                "missing required semantic anchor references: "
                + ", ".join(missing_anchor_names)
            )
        uninstantiated_adapter_object_binders = (
            _source_to_bridge_candidate_uninstantiated_adapter_object_binders(
                row,
                candidate_source,
            )
        )
        if uninstantiated_adapter_object_binders:
            errors.append(
                "source_to_bridge_premise_derivation_candidates Lean candidate "
                "takes adapter objects as theorem binders instead of deriving "
                "them from source binders: "
                + ", ".join(uninstantiated_adapter_object_binders)
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


def _feedback_has_repeated_syntax_failure_contract(
    feedback: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    input_summary = (
        feedback.get("input_summary", {})
        if isinstance(feedback.get("input_summary", {}), Mapping)
        else {}
    )
    for source in (feedback, input_summary):
        if not isinstance(source, Mapping):
            continue
        contract = (
            source.get("local_lean_repair_contract", {})
            if isinstance(source.get("local_lean_repair_contract", {}), Mapping)
            else {}
        )
        diagnostic_classes = {
            str(value).strip()
            for value in contract.get("diagnostic_classes", []) or []
            if str(value).strip()
        }
        if (
            bool(contract.get("repeated_syntax_failure", False))
            and (
                not diagnostic_classes
                or "lean_parser_or_syntax_error" in diagnostic_classes
            )
        ):
            return True
        if (
            bool(source.get("repeated_formalizer_lean_candidate_failure", False))
            and "lean_parser_or_syntax_error" in diagnostic_classes
        ):
            return True
    return False


def _feedback_has_source_theorem_target_drift(
    feedback: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    input_summary = feedback.get("input_summary", {})
    contracts = [
        feedback.get("target_shape_contract", {}),
        input_summary.get("target_shape_contract", {})
        if isinstance(input_summary, Mapping)
        else {},
    ]
    for contract in contracts:
        if not isinstance(contract, Mapping):
            continue
        contract_text = json.dumps(contract, default=str).lower()
        if (
            str(contract.get("contract_kind", "") or "")
            == "source_theorem_target_preservation"
            or "source theorem target" in contract_text
            or "source-theorem target" in contract_text
        ):
            return True
    diagnostics = []
    for source in (feedback, input_summary):
        if isinstance(source, Mapping):
            rows = source.get("candidate_diagnostics", []) or []
            if isinstance(rows, list | tuple):
                diagnostics.extend(rows)
    diagnostic_text = " ".join(
        str(error)
        for row in diagnostics
        if isinstance(row, Mapping)
        for error in row.get("precheck_errors", []) or []
    ).lower()
    return "source-theorem target drift" in diagnostic_text


def _feedback_suggests_pseudo_formalization(
    *sources: Mapping[str, Any] | None,
) -> bool:
    for source in sources:
        if not isinstance(source, Mapping) or not source:
            continue
        marker_source: Mapping[str, Any] = source
        if str(source.get("feedback_type", "") or "") == (
            "formalizer_task_bound_formal_source_context"
        ):
            marker_source = {
                key: value
                for key, value in source.items()
                if key != "proofengineer_repair_context"
            }
        text = json.dumps(_compact_value(marker_source), default=str).lower()
        if any(
            marker in text
            for marker in (
                "source_theorem_proof_body",
                "proof_body_adapter",
                "semantic_alignment_unreviewed",
                "semantic anchor",
                "semantic_definition",
                "missing import",
                "library support",
                "overlarge proof",
                "pseudo_formal",
                "pseudo-formal",
                "block-verification",
            )
        ):
            return True
    return False


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
    """Return true only for blockers where PF/BV should be a required repair pass."""

    explicit_flags = {
        "pseudo_formalization_required",
        "requires_pseudo_formalization",
        "requires_pseudo_formal_block_verification",
        "requires_pf_bv",
        "exact_semantic_definition_structural_reformulation_required",
        "source_theorem_exact_semantic_definition_structural_reformulation_required",
        "formalizer_pseudo_formal_packet_component_gate_failure_available",
        "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_available",
    }
    required_markers = (
        "pseudo_formalization_required",
        "requires_pseudo_formalization",
        "requires pseudo-formalization",
        "requires pseudo formalization",
        "requires pseudo-formal",
        "requires pf/bv",
        "pf/bv activation required",
        "pseudo-formalization activation required",
        "pseudo formalization activation required",
        "must emit pseudo_formal_proof_packets",
        "must emit pseudo-formal proof packets",
        "exact_semantic_definition_structural_reformulation_required",
        "source_theorem_exact_semantic_definition_structural_reformulation_required",
        "pending_exact_semantic_definition_structural_reformulation",
        "proof_body_reached_semantic_alignment_unreviewed",
        "proof body reached semantic alignment unreviewed",
        "proof-body goal reached with semantic blockers",
        "overlarge proof step requires block verification",
    )
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
        text = json.dumps(
            _compact_value(
                _strip_false_pseudo_formal_required_flags(
                    source,
                    flag_keys=explicit_flags,
                )
            ),
            default=str,
        ).lower()
        if any(marker in text for marker in required_markers):
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
    valid_packets: list[Mapping[str, Any]] = []
    for index, pseudo_packet in enumerate(pseudo_packets):
        errors = validate_pseudo_formal_packet(pseudo_packet)
        if errors:
            validation_errors.append(
                f"pseudo_formal_proof_packets[{index}] invalid: "
                + "; ".join(errors[:6])
            )
        else:
            valid_packets.append(pseudo_packet)
    if not valid_packets:
        return [
            "pseudo_formalization_required: no locally valid "
            "pseudo_formal_proof_packets entry was emitted; "
            + " | ".join(validation_errors[:3])
        ]
    work_order_rows: list[dict[str, Any]] = []
    for pseudo_packet in valid_packets:
        work_order_rows.extend(pseudo_formal_block_work_order_rows(pseudo_packet))
    routable_work_order_rows = pseudo_formal_routable_work_order_rows(
        work_order_rows
    )
    if not routable_work_order_rows:
        return [
            "pseudo_formalization_required: valid PF/BV packet did not produce "
            "any effective lane-routable pseudo-formal work-order rows; blocked "
            "or pending rows do not satisfy required PF/BV activation. At least "
            "one block must be faithful BV-accepted for Lean seeding, require "
            "RAG/library/semantic-definition follow-up, fail BV, need "
            "faithfulness review, or carry semantic_primitive_requirements"
        ]
    required_target_lanes = _required_pseudo_formal_target_lanes(
        environment_feedback or {},
        proof_bank_runtime_memory_summary or {},
    )
    if required_target_lanes:
        target_lane_rows = [
            row
            for row in routable_work_order_rows
            if str(row.get("target_lane", "") or "") in required_target_lanes
            or str(row.get("row_kind", "") or "")
            == PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND
        ]
        if not target_lane_rows:
            return [
                "pseudo_formalization_required: valid PF/BV packet produced "
                "only generic review rows and did not route any effective row "
                "to required target lanes "
                + ", ".join(required_target_lanes)
                + " or to independent block verification. Runtime routing is "
                "field-inferred: for source_theorem_exact_semantic_definition use "
                "faithfulness_status=faithful with "
                "lean_feasibility=needs_semantic_definition and non-empty "
                "semantic_primitive_requirements naming the primitive/source object "
                "to define; for lean_rag use "
                "faithfulness_status=faithful with lean_feasibility=needs_rag; "
                "for source_to_bridge use faithfulness_status=faithful with "
                "semantic_primitive_requirements; generic needs_review/not_run "
                "blocks are diagnostic only"
            ]
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
        ):
            return [
                "pseudo_formalization_required: required "
                "source_theorem_exact_semantic_definition routing was not "
                "materialized as an exact semantic-definition work-order row. "
                "Independent block verification alone is useful diagnostic PF/BV "
                "feedback, but exact semantic-definition repair must also emit a "
                "faithful block with lean_feasibility=needs_semantic_definition "
                "and non-empty semantic_primitive_requirements."
            ]
        exact_semantic_row_errors = (
            _required_exact_semantic_work_order_row_errors(exact_semantic_rows)
        )
        if exact_semantic_row_errors:
            return exact_semantic_row_errors
    copy_contract_errors = _required_pseudo_formal_copy_contract_errors(
        packet,
        proof_bank_runtime_memory_summary or {},
        required_target_lanes=required_target_lanes,
    )
    if copy_contract_errors:
        return copy_contract_errors
    return []


_COPY_CONTRACT_MISSING = object()


def _required_pseudo_formal_copy_contract_errors(
    packet: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    *,
    required_target_lanes: Sequence[str],
) -> list[str]:
    if not isinstance(proof_bank_runtime_memory_summary, Mapping):
        return []
    candidate_rows = [
        row
        for row in proof_bank_runtime_memory_summary.get(
            "formalizer_pseudo_formal_packet_component_gate_failure_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    candidate_rows.extend(
        row
        for row in proof_bank_runtime_memory_summary.get(
            "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    )
    for row in candidate_rows:
        copy_summary = row.get(
            "validator_ready_copy_contract_summary",
            row.get("pseudo_formal_failure_copy_contract_summary", {}),
        )
        if not (
            isinstance(copy_summary, Mapping)
            and _formalizer_bool_like(
                copy_summary.get("validator_ready_copy_contract_satisfied")
            )
        ):
            continue
        raw_seed = row.get(
            "concrete_lane_routable_repair_seed",
            row.get(
                "pseudo_formal_failure_concrete_lane_routable_repair_seed",
                {},
            ),
        )
        if not isinstance(raw_seed, Mapping) or not raw_seed:
            continue
        copy_fragment = _pseudo_formalization_required_copy_fragment(
            raw_seed,
            required_target_lanes=required_target_lanes,
        )
        copy_contract = (
            copy_fragment.get("validator_ready_copy_contract", {})
            if isinstance(copy_fragment, Mapping)
            else {}
        )
        if not isinstance(copy_contract, Mapping) or not copy_contract:
            continue
        required_paths = [
            str(value).strip()
            for value in copy_contract.get("required_preserved_paths", []) or []
            if str(value).strip()
        ]
        mismatched_paths: list[str] = []
        for path in required_paths:
            expected = _pseudo_formal_copy_contract_path_value(copy_fragment, path)
            actual = _pseudo_formal_copy_contract_path_value(packet, path)
            if expected is _COPY_CONTRACT_MISSING:
                continue
            if actual is _COPY_CONTRACT_MISSING or not _copy_contract_value_preserved(
                actual,
                expected,
            ):
                mismatched_paths.append(path)
        if mismatched_paths:
            return [
                "pseudo_formalization_required: runtime memory supplied a "
                "satisfied validator_ready_copy_contract, but the response did "
                "not preserve required PF/BV copy path(s): "
                + ", ".join(mismatched_paths[:6])
                + ". Copy pseudo_formalization_required_copy_fragment."
                "pseudo_formal_proof_packets into pseudo_formal_proof_packets "
                "before optional edits, preserving source_anchors, conclusion, "
                "semantic_primitive_requirements, lean_feasibility, and the "
                "non-proof boundary."
            ]
    return []


def _pseudo_formal_copy_contract_path_value(source: Any, path: str) -> Any:
    current = source
    for part in str(path or "").split("."):
        if not part:
            return _COPY_CONTRACT_MISSING
        for match in re.finditer(r"([^\[\]]+)|\[(\d+)\]", part):
            key = match.group(1)
            index = match.group(2)
            if key is not None:
                if not isinstance(current, Mapping) or key not in current:
                    return _COPY_CONTRACT_MISSING
                current = current[key]
                continue
            if index is None:
                return _COPY_CONTRACT_MISSING
            if not isinstance(current, Sequence) or isinstance(
                current,
                (str, bytes, bytearray),
            ):
                return _COPY_CONTRACT_MISSING
            item_index = int(index)
            if item_index >= len(current):
                return _COPY_CONTRACT_MISSING
            current = current[item_index]
    return current


def _copy_contract_value_preserved(actual: Any, expected: Any) -> bool:
    if isinstance(expected, Mapping):
        if not isinstance(actual, Mapping):
            return False
        return all(
            key in actual and _copy_contract_value_preserved(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, Sequence) and not isinstance(
        expected,
        (str, bytes, bytearray),
    ):
        if not isinstance(actual, Sequence) or isinstance(
            actual,
            (str, bytes, bytearray),
        ):
            return False
        return all(
            any(_copy_contract_value_preserved(candidate, item) for candidate in actual)
            for item in expected
        )
    return (
        json.dumps(actual, sort_keys=True, default=str)
        == json.dumps(expected, sort_keys=True, default=str)
    )


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
            "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory",
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


def _pseudo_formalization_required_packet_seed(
    *,
    question: OpenResearchQuestion | None,
    theory_packet: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
) -> dict[str, Any]:
    """Build prompt-only PF/BV scaffolding from existing source context."""

    required_target_lanes = list(
        _required_pseudo_formal_target_lanes(
            environment_feedback,
            proof_bank_runtime_memory_summary,
        )
    )
    if not required_target_lanes:
        required_target_lanes = [PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION]
    theorem_id = _pseudo_formal_seed_theorem_id(
        question=question,
        theory_packet=theory_packet,
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
    )
    source_artifact_id = _pseudo_formal_seed_source_artifact_id(
        question=question,
        theory_packet=theory_packet,
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
    )
    derivation_step = _pseudo_formal_seed_derivation_step(theory_packet)
    conclusion = _pseudo_formal_seed_conclusion(
        theory_packet=theory_packet,
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
        derivation_step=derivation_step,
    )
    proof_text = _pseudo_formal_seed_proof_text(
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
        derivation_step=derivation_step,
    )
    source_anchor = _pseudo_formal_seed_source_anchor(
        theory_packet=theory_packet,
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
        derivation_step=derivation_step,
        fallback_excerpt=conclusion,
    )
    semantic_primitives = _pseudo_formal_seed_semantic_primitives(
        required_target_lanes=required_target_lanes,
        source_anchor=source_anchor,
        conclusion=conclusion,
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
    )
    lean_feasibility = _pseudo_formal_seed_lean_feasibility(required_target_lanes)
    block_id = "pf_block:" + stable_hash(
        {
            "theorem_id": theorem_id,
            "source_artifact_id": source_artifact_id,
            "source_anchor": source_anchor,
            "conclusion": conclusion,
        }
    )[:12]
    packet_id = "pseudo_formal_packet_seed:" + stable_hash(
        {
            "theorem_id": theorem_id,
            "source_artifact_id": source_artifact_id,
            "block_id": block_id,
            "required_target_lanes": required_target_lanes,
        }
    )[:16]
    return {
        "packet_id": packet_id,
        "theorem_id": theorem_id,
        "source_artifact_id": source_artifact_id,
        "prompt_scaffold_origin": {
            "artifact_kind": "PseudoFormalPromptScaffoldOrigin",
            "scaffold_kind": "pseudo_formalization_required_packet_seed",
            "source": "FormalizerPrompt",
            "required_output_key": "pseudo_formal_proof_packets",
            "source_theorem_id": theorem_id,
            "source_artifact_id": source_artifact_id,
            "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        },
        "pseudo_formal_method_contract_id": PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
        "required_target_lanes_to_satisfy": required_target_lanes,
        "blocks": [
            {
                "block_id": block_id,
                "block_type": "claim",
                "block_depth": 1,
                "premises": _pseudo_formal_seed_premises(
                    environment_feedback=environment_feedback,
                    proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
                ),
                "conclusion": conclusion,
                "proof_text": proof_text,
                "dependency_ids": [],
                "scope_parent_id": "",
                "dependency_scope": "earlier_block_statement_only",
                "inherited_scope": [],
                "source_anchors": [source_anchor],
                "semantic_primitive_requirements": semantic_primitives,
                "lean_feasibility": lean_feasibility,
                "faithfulness_status": "faithful",
                "faithfulness_repair": {
                    "status": "not_required",
                    "attempts": 0,
                    "flagged_discrepancies": [],
                },
                "block_verification": {
                    "verdict": "unknown",
                    "reason": (
                        "PF/BV packet seed for source-anchored decomposition; "
                        "independent BlockVerifier has not accepted this block"
                    ),
                    "verifier_provenance": "not_run",
                    "independent_verifier": False,
                    "rollout_count": 0,
                },
                "kernel_verified": False,
            }
        ],
        "seed_usage_instruction": (
            "Prompt-only scaffold: copy or complete this packet in "
            "pseudo_formal_proof_packets; do not treat the seed itself as proof "
            "or as an emitted runtime artifact."
        ),
    }


def _pseudo_formal_concrete_lane_routable_repair_seed(
    packet_seed: Mapping[str, Any],
    *,
    required_target_lanes: Sequence[str],
) -> dict[str, Any]:
    """Make the prompt repair seed directly materialize a routable PF lane."""

    seed = deepcopy(dict(packet_seed or {}))
    blocks = seed.get("blocks", [])
    block = (
        deepcopy(dict(blocks[0]))
        if isinstance(blocks, Sequence)
        and not isinstance(blocks, (str, bytes, bytearray))
        and blocks
        and isinstance(blocks[0], Mapping)
        else {}
    )
    target_lanes = [
        str(lane).strip()
        for lane in required_target_lanes
        if str(lane).strip()
    ] or [PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION]
    primary_lane = _pseudo_formal_primary_repair_target_lane(target_lanes)
    conclusion = str(
        block.get("conclusion", "")
        or seed.get("conclusion", "")
        or "the blocked source proof step requires exact semantic grounding"
    ).strip()
    source_anchors = _pseudo_formal_repair_seed_source_anchors(
        block.get("source_anchors", []),
        fallback_id=str(seed.get("source_artifact_id", "") or ""),
        fallback_excerpt=conclusion,
    )
    semantic_requirements = _pseudo_formal_repair_seed_semantic_requirements(
        block.get("semantic_primitive_requirements", []),
        source_anchors=source_anchors,
        conclusion=conclusion,
        target_lane=primary_lane,
    )
    block.update(
        {
            "block_id": str(block.get("block_id", "") or "pf_block_1"),
            "block_type": str(block.get("block_type", "") or "claim"),
            "block_depth": int(block.get("block_depth", 1) or 1),
            "premises": _pseudo_formal_repair_seed_string_list(
                block.get("premises", [])
            )
            or ["source proof context supplied by runtime feedback"],
            "conclusion": conclusion,
            "proof_text": str(
                block.get("proof_text", "")
                or "PF/BV repair seed: route this source-anchored semantic step."
            ),
            "dependency_ids": _pseudo_formal_repair_seed_string_list(
                block.get("dependency_ids", [])
            ),
            "scope_parent_id": str(block.get("scope_parent_id", "") or ""),
            "dependency_scope": str(
                block.get("dependency_scope", "")
                or "earlier_block_statement_only"
            ),
            "inherited_scope": _pseudo_formal_repair_seed_string_list(
                block.get("inherited_scope", [])
            ),
            "source_anchors": source_anchors,
            "semantic_primitive_requirements": semantic_requirements,
            "faithfulness_status": "faithful",
            "faithfulness_repair": {
                "status": "not_required",
                "attempts": 0,
                "flagged_discrepancies": [],
            },
            "block_verification": {
                "verdict": "unknown",
                "reason": (
                    "repair seed for routing only; independent BV/Lean has not "
                    "accepted this block"
                ),
                "verifier_provenance": "not_run",
                "independent_verifier": False,
                "rollout_count": 0,
            },
            "kernel_verified": False,
            "target_lane_materialization_hint": primary_lane,
        }
    )
    if primary_lane == PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION:
        block["lean_feasibility"] = "needs_semantic_definition"
    elif primary_lane == PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG:
        block["lean_feasibility"] = "needs_rag"
    elif primary_lane == PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS:
        block["lean_feasibility"] = "lean_now"
    else:
        block["lean_feasibility"] = str(
            block.get("lean_feasibility", "") or "needs_semantic_definition"
        )
    seed.update(
        {
            "schema_version": PSEUDO_FORMALIZATION_SCHEMA_VERSION,
            "schema_id": PSEUDO_FORMALIZATION_SCHEMA_ID,
            "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
            "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
            "kernel_verified": False,
            "source_theorem_kernel_verified": False,
            "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
            "pseudo_formal_method_contract_id": (
                PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
            ),
            "pseudo_formal_pipeline_stages": [
                PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE
            ],
            "required_target_lanes_to_satisfy": target_lanes,
            "primary_target_lane_to_materialize": primary_lane,
            "blocks": [block],
        }
    )
    return seed


def _pseudo_formalization_required_copy_fragment(
    packet_seed: Mapping[str, Any],
    *,
    required_target_lanes: Sequence[str],
) -> dict[str, Any]:
    if not isinstance(packet_seed, Mapping) or not packet_seed:
        return {}
    concrete_seed = _pseudo_formal_concrete_lane_routable_repair_seed(
        packet_seed,
        required_target_lanes=required_target_lanes,
    )
    scaffold_origin = dict(
        concrete_seed.get("prompt_scaffold_origin", {})
        if isinstance(concrete_seed.get("prompt_scaffold_origin", {}), Mapping)
        else {}
    )
    scaffold_origin.update(
        {
            "artifact_kind": "PseudoFormalPromptScaffoldOrigin",
            "scaffold_kind": "pseudo_formalization_required_copy_fragment",
            "source": "FormalizerPrompt",
            "required_output_key": "pseudo_formal_proof_packets",
            "copy_fragment_id": "pseudo_formal_copy_fragment:"
            + stable_hash(
                {
                    "packet_id": concrete_seed.get("packet_id", ""),
                    "required_target_lanes": list(required_target_lanes),
                }
            )[:16],
            "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        }
    )
    concrete_seed["prompt_scaffold_origin"] = scaffold_origin
    routable_rows = pseudo_formal_routable_work_order_rows(
        pseudo_formal_block_work_order_rows(concrete_seed)
    )
    routable_target_lanes = sorted(
        {
            str(row.get("target_lane", "") or "")
            for row in routable_rows
            if str(row.get("target_lane", "") or "")
        }
    )
    return {
        "required_output_key": "pseudo_formal_proof_packets",
        "copy_instruction": (
            "Copy this fragment's pseudo_formal_proof_packets list into the "
            "Formalizer response before adding optional Lean targets or prose. "
            "Then minimally adapt mathematical text only if runtime feedback "
            "provides a more precise source-bound claim."
        ),
        "validator_ready_copy_contract": {
            "copy_source_path": (
                "pseudo_formalization_required_copy_fragment."
                "pseudo_formal_proof_packets"
            ),
            "copy_destination_path": "pseudo_formal_proof_packets",
            "first_packet_copy_source_path": (
                "pseudo_formalization_required_copy_fragment."
                "pseudo_formal_proof_packets[0]"
            ),
            "first_packet_destination_path": "pseudo_formal_proof_packets[0]",
            "required_preserved_paths": [
                "pseudo_formal_proof_packets[0].blocks[0].conclusion",
                "pseudo_formal_proof_packets[0].blocks[0].source_anchors",
                (
                    "pseudo_formal_proof_packets[0].blocks[0]."
                    "semantic_primitive_requirements"
                ),
                "pseudo_formal_proof_packets[0].blocks[0].lean_feasibility",
                "pseudo_formal_proof_packets[0].blocks[0].faithfulness_status",
                "pseudo_formal_proof_packets[0].proof_evidence_status",
                "pseudo_formal_proof_packets[0].kernel_verified",
                "pseudo_formal_proof_packets[0].source_theorem_kernel_verified",
            ],
            "routable_work_order_rows_if_copied": len(routable_rows),
            "routable_target_lanes_if_copied": routable_target_lanes,
            "copy_is_not_proof_evidence": True,
            "validation_note": (
                "This fragment is constructed to satisfy local PF/BV packet "
                "structure and produce lane-routable routing rows when copied "
                "without deleting required fields."
            ),
        },
        "pseudo_formal_proof_packets": [concrete_seed],
        "validator_alignment": {
            "must_have_top_level_block_conclusion": True,
            "must_have_source_anchors": True,
            "must_have_semantic_primitive_requirements_for_exact_semantic_lane": (
                True
            ),
            "must_produce_lane_routable_work_order_rows": True,
            "kernel_verified": False,
            "source_theorem_kernel_verified": False,
            "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        },
        "boundary": (
            "This copy fragment is prompt scaffolding and routing memory only; "
            "it is not source theorem proof, Lean proof, verifier evidence, or "
            "kernel evidence."
        ),
    }


def _pseudo_formal_component_gate_failure_repair_seed(
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    *,
    required_target_lanes: Sequence[str],
) -> dict[str, Any]:
    if not isinstance(proof_bank_runtime_memory_summary, Mapping):
        return {}
    failure_rows = [
        row
        for row in proof_bank_runtime_memory_summary.get(
            "formalizer_pseudo_formal_packet_component_gate_failure_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    feedback_rows = [
        row
        for row in proof_bank_runtime_memory_summary.get(
            "formalizer_pseudo_formal_packet_component_gate_feedback_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    retry_agenda_rows = [
        row
        for row in proof_bank_runtime_memory_summary.get(
            "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    candidate_rows: list[tuple[Mapping[str, Any], str]] = [
        (
            row,
            "formalizer_pseudo_formal_packet_component_gate_failure_memory",
        )
        for row in failure_rows
    ]
    candidate_rows.extend(
        (
            row,
            "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory",
        )
        for row in retry_agenda_rows
    )
    candidate_rows.extend(
        (
            row,
            "formalizer_pseudo_formal_packet_component_gate_feedback_memory",
        )
        for row in feedback_rows
    )
    for row, row_memory_source in candidate_rows:
        copy_contract_summary = row.get(
            "validator_ready_copy_contract_summary",
            row.get("pseudo_formal_failure_copy_contract_summary", {}),
        )
        if (
            isinstance(copy_contract_summary, Mapping)
            and copy_contract_summary
            and not copy_contract_summary.get(
                "validator_ready_copy_contract_satisfied",
                False,
            )
        ):
            continue
        raw_seed = row.get(
            "concrete_lane_routable_repair_seed",
            row.get(
                "pseudo_formal_failure_concrete_lane_routable_repair_seed",
                {},
            ),
        )
        if not isinstance(raw_seed, Mapping):
            continue
        raw_blocks = raw_seed.get("blocks", [])
        if not isinstance(raw_blocks, Sequence) or isinstance(
            raw_blocks,
            (str, bytes, bytearray),
        ):
            continue
        if not any(isinstance(block, Mapping) for block in raw_blocks):
            continue
        row_target_lanes = [
            str(value).strip()
            for key in (
                "required_target_lanes",
                "pseudo_formal_failure_required_target_lanes",
                "pseudo_formal_routable_target_lanes",
            )
            for value in row.get(key, []) or []
            if str(value).strip()
        ]
        seed_target_lanes = [
            str(value).strip()
            for value in raw_seed.get("required_target_lanes_to_satisfy", []) or []
            if str(value).strip()
        ]
        target_lanes = list(
            dict.fromkeys(
                [
                    *[
                        str(lane).strip()
                        for lane in required_target_lanes
                        if str(lane).strip()
                    ],
                    *row_target_lanes,
                    *seed_target_lanes,
                ]
            )
        ) or [PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION]
        seed = _pseudo_formal_concrete_lane_routable_repair_seed(
            raw_seed,
            required_target_lanes=target_lanes,
        )
        scaffold_origin = (
            dict(seed.get("prompt_scaffold_origin", {}))
            if isinstance(seed.get("prompt_scaffold_origin", {}), Mapping)
            else {}
        )
        scaffold_origin.update(
            {
                "artifact_kind": "PseudoFormalPromptScaffoldOrigin",
                "scaffold_kind": (
                    "formalizer_pseudo_formal_packet_component_gate_failure_"
                    "repair_seed"
                ),
                "source": row_memory_source,
                "component_eval_manifest_path": str(
                    row.get("component_eval_manifest_path", "") or ""
                ),
                "agenda_id": str(row.get("agenda_id", "") or ""),
                "work_order_id": str(row.get("work_order_id", "") or ""),
                "runtime_queue_status": str(
                    row.get("runtime_queue_status", "") or ""
                ),
                "validation_issue_summary": (
                    dict(row.get("validation_issue_summary", {}))
                    if isinstance(row.get("validation_issue_summary", {}), Mapping)
                    else dict(
                        row.get(
                            "pseudo_formal_failure_validation_issue_summary",
                            {},
                        )
                    )
                    if isinstance(
                        row.get(
                            "pseudo_formal_failure_validation_issue_summary",
                            {},
                        ),
                        Mapping,
                    )
                    else {}
                ),
                "required_target_lanes": target_lanes,
                "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
            }
        )
        seed["prompt_scaffold_origin"] = scaffold_origin
        seed["component_gate_failure_seed_source"] = row_memory_source
        seed["seed_usage_instruction"] = (
            "Copy this prior component-gate repair seed into "
            "pseudo_formal_proof_packets[0] and preserve conclusion, "
            "source_anchors, semantic_primitive_requirements, target lanes, "
            "kernel_verified=false, source_theorem_kernel_verified=false, and "
            "the non-proof PF/BV boundary."
        )
        return seed
    return {}


def _pseudo_formal_primary_repair_target_lane(target_lanes: Sequence[str]) -> str:
    for lane in (
        PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
        PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
        PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
        PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS,
        PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
    ):
        if lane in target_lanes:
            return lane
    return PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION


def _pseudo_formal_repair_seed_source_anchors(
    value: Any,
    *,
    fallback_id: str,
    fallback_excerpt: str,
) -> list[dict[str, str]]:
    anchors: list[dict[str, str]] = []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            if not isinstance(item, Mapping):
                continue
            anchor_id = str(item.get("id", "") or "").strip()
            excerpt = str(item.get("excerpt", "") or "").strip()
            if not anchor_id and not excerpt:
                continue
            anchors.append(
                {
                    "kind": str(item.get("kind", "") or "proof_body"),
                    "id": anchor_id or fallback_id or "proof_body:blocked_step",
                    "excerpt": _truncate_formalizer_text(
                        excerpt or fallback_excerpt,
                        280,
                    ),
                }
            )
    if anchors:
        return anchors[:3]
    return [
        {
            "kind": "proof_body",
            "id": fallback_id or "proof_body:blocked_step",
            "excerpt": _truncate_formalizer_text(fallback_excerpt, 280),
        }
    ]


def _pseudo_formal_repair_seed_semantic_requirements(
    value: Any,
    *,
    source_anchors: Sequence[Mapping[str, Any]],
    conclusion: str,
    target_lane: str,
) -> list[str]:
    requirements = _pseudo_formal_repair_seed_string_list(value)
    if requirements:
        return requirements[:3]
    if target_lane not in {
        PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
        PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
    }:
        return []
    anchor_id = ""
    for anchor in source_anchors:
        anchor_id = str(anchor.get("id", "") or "").strip()
        if anchor_id:
            break
    suffix_source = anchor_id or conclusion or "blocked_source_step"
    suffix = re.sub(r"[^A-Za-z0-9_]+", "_", suffix_source).strip("_").lower()
    return [f"semantic_primitive:{suffix or 'blocked_source_step'}"]


def _pseudo_formal_repair_seed_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]
    return []


def _pseudo_formal_seed_derivation_step(
    theory_packet: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(theory_packet, Mapping):
        return {}
    for container_key in ("theory_derivation_trace", "theory_derivation_packet"):
        container = theory_packet.get(container_key, {})
        if not isinstance(container, Mapping):
            continue
        for step_key in ("derivation_steps", "steps", "equation_steps"):
            rows = container.get(step_key, [])
            if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
                continue
            for row in rows:
                if isinstance(row, Mapping):
                    return row
    return {}


def _pseudo_formal_seed_theorem_id(
    *,
    question: OpenResearchQuestion | None,
    theory_packet: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
) -> str:
    for value in _pseudo_formal_nested_strings(
        (environment_feedback, proof_bank_runtime_memory_summary),
        (
            "source_theorem_id",
            "target_theorem_id",
            "target_theorem_name",
            "source_theorem_goal_id",
        ),
    ):
        return value
    theorem_cards = theory_packet.get("theorem_cards", []) if isinstance(theory_packet, Mapping) else []
    if isinstance(theorem_cards, Sequence) and not isinstance(theorem_cards, (str, bytes, bytearray)):
        for row in theorem_cards:
            if not isinstance(row, Mapping):
                continue
            for key in ("id", "theorem_id", "target_theorem_id", "title"):
                value = str(row.get(key, "") or "").strip()
                if value:
                    return value
    if question is not None and question.id:
        return f"theorem:{question.id}"
    return "source_theorem:unknown"


def _pseudo_formal_seed_source_artifact_id(
    *,
    question: OpenResearchQuestion | None,
    theory_packet: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
) -> str:
    for source in (theory_packet, environment_feedback, proof_bank_runtime_memory_summary):
        if not isinstance(source, Mapping):
            continue
        for key in (
            "source_artifact_id",
            "proof_body_id",
            "source_proof_body_id",
            "packet_id",
            "trace_id",
        ):
            value = str(source.get(key, "") or "").strip()
            if value:
                return value
    for value in _pseudo_formal_nested_strings(
        (environment_feedback, proof_bank_runtime_memory_summary),
        ("source_artifact_id", "proof_body_id", "source_proof_body_id"),
    ):
        return value
    if question is not None and question.id:
        return f"question:{question.id}"
    return "source_artifact:unknown"


def _pseudo_formal_seed_conclusion(
    *,
    theory_packet: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    derivation_step: Mapping[str, Any],
) -> str:
    for source in (derivation_step,):
        for key in ("claim", "conclusion", "statement", "goal"):
            value = str(source.get(key, "") or "").strip()
            if value:
                return value
    for value in _pseudo_formal_nested_strings(
        (environment_feedback, proof_bank_runtime_memory_summary),
        ("source_block_conclusion", "blocked_conclusion", "desired_conclusion"),
    ):
        return value
    theorem_cards = theory_packet.get("theorem_cards", []) if isinstance(theory_packet, Mapping) else []
    if isinstance(theorem_cards, Sequence) and not isinstance(theorem_cards, (str, bytes, bytearray)):
        for row in theorem_cards:
            if not isinstance(row, Mapping):
                continue
            for key in ("claim", "conclusion", "statement", "title"):
                value = str(row.get(key, "") or "").strip()
                if value:
                    return value
    return (
        "the blocked source proof step requires exact semantic grounding before "
        "source theorem Lean replay"
    )


def _pseudo_formal_seed_proof_text(
    *,
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    derivation_step: Mapping[str, Any],
) -> str:
    for key in ("proof_text", "proof", "rationale", "reason"):
        value = str(derivation_step.get(key, "") or "").strip()
        if value:
            return _truncate_formalizer_text(value, 420)
    for value in _pseudo_formal_nested_strings(
        (environment_feedback, proof_bank_runtime_memory_summary),
        ("message", "diagnostic", "reason", "failure_classification", "proof_text"),
    ):
        return _truncate_formalizer_text(value, 420)
    return (
        "Runtime feedback says proof-body repair is blocked; decompose this "
        "source step into PF/BV blocks and route exact semantic-definition work."
    )


def _pseudo_formal_seed_source_anchor(
    *,
    theory_packet: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    derivation_step: Mapping[str, Any],
    fallback_excerpt: str,
) -> dict[str, str]:
    for source in (derivation_step,):
        anchor_id = str(
            source.get("anchor_id", "")
            or source.get("step_id", "")
            or source.get("id", "")
            or ""
        ).strip()
        excerpt = str(
            source.get("claim", "")
            or source.get("conclusion", "")
            or source.get("statement", "")
            or fallback_excerpt
            or ""
        ).strip()
        if anchor_id or excerpt:
            return {
                "kind": "theory_trace",
                "id": anchor_id or "theory_trace:blocked_step",
                "excerpt": _truncate_formalizer_text(excerpt, 280),
            }
    for value in _pseudo_formal_nested_strings(
        (environment_feedback, proof_bank_runtime_memory_summary),
        ("source_anchor_id", "anchor_id", "source_block_id", "proof_body_id"),
    ):
        return {
            "kind": "proof_body",
            "id": value,
            "excerpt": _truncate_formalizer_text(fallback_excerpt, 280),
        }
    packet_id = str(
        theory_packet.get("packet_id", "") if isinstance(theory_packet, Mapping) else ""
    ).strip()
    return {
        "kind": "theory_trace" if packet_id else "proof_body",
        "id": packet_id or "proof_body:blocked_step",
        "excerpt": _truncate_formalizer_text(fallback_excerpt, 280),
    }


def _pseudo_formal_seed_semantic_primitives(
    *,
    required_target_lanes: Sequence[str],
    source_anchor: Mapping[str, Any],
    conclusion: str,
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
) -> list[str]:
    explicit = list(
        _pseudo_formal_nested_strings(
            (environment_feedback, proof_bank_runtime_memory_summary),
            (
                "semantic_primitive",
                "semantic_primitive_id",
                "missing_semantic_primitive",
                "required_semantic_primitive",
            ),
            limit=3,
        )
    )
    if explicit:
        return explicit
    if not (
        PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE in required_target_lanes
        or PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
        in required_target_lanes
    ):
        return []
    anchor_id = str(source_anchor.get("id", "") or "").strip() or conclusion
    suffix = re.sub(r"[^A-Za-z0-9_]+", "_", anchor_id).strip("_").lower()
    return [f"semantic_primitive:{suffix or 'blocked_source_step'}"]


def _pseudo_formal_seed_lean_feasibility(required_target_lanes: Sequence[str]) -> str:
    if PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION in required_target_lanes:
        return "needs_semantic_definition"
    if PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG in required_target_lanes:
        return "needs_rag"
    if PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS in required_target_lanes:
        return "lean_now"
    if PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP in required_target_lanes:
        return "pseudo_only"
    return "needs_semantic_definition"


def _pseudo_formal_seed_premises(
    *,
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
) -> list[str]:
    premises = list(
        _pseudo_formal_nested_strings(
            (environment_feedback, proof_bank_runtime_memory_summary),
            ("premise", "source_premise", "assumption", "hypothesis"),
            limit=2,
        )
    )
    return premises or ["source proof context supplied by runtime feedback"]


def _pseudo_formal_nested_strings(
    sources: Sequence[Any],
    keys: Sequence[str],
    *,
    limit: int = 1,
    max_depth: int = 4,
) -> tuple[str, ...]:
    key_set = {key for key in keys}
    out: list[str] = []

    def visit(value: Any, depth: int) -> None:
        if len(out) >= limit or depth > max_depth:
            return
        if isinstance(value, Mapping):
            for key in keys:
                raw = value.get(key)
                if isinstance(raw, str) and raw.strip():
                    out.append(raw.strip())
                    if len(out) >= limit:
                        return
                elif isinstance(raw, Sequence) and not isinstance(
                    raw,
                    (str, bytes, bytearray),
                ):
                    for item in raw:
                        if isinstance(item, str) and item.strip():
                            out.append(item.strip())
                            if len(out) >= limit:
                                return
            for nested_key, nested_value in value.items():
                if nested_key in key_set:
                    continue
                visit(nested_value, depth + 1)
                if len(out) >= limit:
                    return
        elif isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes, bytearray),
        ):
            for item in list(value)[:8]:
                visit(item, depth + 1)
                if len(out) >= limit:
                    return

    for source in sources:
        visit(source, 0)
        if len(out) >= limit:
            break
    return tuple(dict.fromkeys(item for item in out if item))


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
        if (
            _feedback_has_source_theorem_target_drift(environment_feedback)
            and _has_explicit_source_theorem_formal_gap_target(formal_targets)
            and not pending_source_to_bridge_premise_names
        ):
            return role_errors
        unbound_gap_synthesis = packet.get(
            "source_theorem_formal_gap_synthesis_skipped", {}
        )
        if (
            _feedback_has_source_theorem_target_drift(environment_feedback)
            and isinstance(unbound_gap_synthesis, Mapping)
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
        source = str(row.get("lean_statement_sketch", "") or "")
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
        placeholder_error = _lean_statement_placeholder_syntax_error(source)
        if placeholder_error:
            errors.append(
                "capability_eval formal target "
                f"{target_id} Lean sketch {placeholder_error}"
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
        source = _source_to_bridge_candidate_lean_source(row)
        expected_status = str(row.get("expected_status", "") or "")
        if expected_status != "NEEDS_KERNEL_CHECK":
            errors.append(
                "capability_eval source-to-bridge candidate "
                f"{premise_id} must set expected_status=NEEDS_KERNEL_CHECK"
            )
        placeholder_error = _lean_statement_placeholder_syntax_error(source)
        if placeholder_error:
            errors.append(
                "capability_eval source-to-bridge candidate "
                f"{premise_id} Lean sketch {placeholder_error}"
            )
    return errors


def _source_theorem_candidate_materialization_context(
    *,
    environment_feedback: Mapping[str, Any] | None = None,
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    proof_summary = (
        proof_bank_runtime_memory_summary
        if isinstance(proof_bank_runtime_memory_summary, Mapping)
        else {}
    )
    feedback = environment_feedback if isinstance(environment_feedback, Mapping) else {}
    required = bool(
        proof_summary.get("source_theorem_candidate_materialization_required")
        or proof_summary.get("recommended_formalizer_target_mode")
        == "source_theorem_exact_candidate_materialization_required"
    )
    target_names = [
        str(value).strip()
        for value in proof_summary.get(
            "source_theorem_candidate_materialization_required_target_names",
            [],
        )
        or []
        if str(value).strip()
    ]
    target_ids = [
        str(value).strip()
        for value in proof_summary.get(
            "source_theorem_candidate_materialization_required_target_ids",
            [],
        )
        or []
        if str(value).strip()
    ]
    for row in feedback.get("high_priority_agenda", []) or []:
        if not isinstance(row, Mapping):
            continue
        if (
            str(row.get("id", "") or "")
            == "formal_gap:source_theorem_candidate_materialization"
            or str(row.get("recommended_formalizer_target_mode", "") or "")
            == "source_theorem_exact_candidate_materialization_required"
        ):
            required = True
            target_ids.extend(
                str(value).strip()
                for value in row.get("target_ids", []) or []
                if str(value).strip()
            )
    for row in feedback.get("formal_blocker_resource_requests", []) or []:
        if not isinstance(row, Mapping):
            continue
        if (
            str(row.get("blocker_kind", "") or "")
            == "SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED"
        ):
            required = True
            target_ids.extend(
                str(value).strip()
                for value in row.get("target_ids", []) or []
                if str(value).strip()
            )
    if _source_theorem_exact_semantic_definition_gate_active(
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
    ):
        required = False
    return {
        "required": required,
        "target_names": list(dict.fromkeys(target_names)),
        "target_ids": list(dict.fromkeys(target_ids)),
    }


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


def _validate_exact_source_theorem_whole_proof_repair_packet(
    packet: Mapping[str, Any],
    *,
    proof_bank_runtime_memory_summary: Mapping[str, Any],
) -> list[str]:
    if str(
        proof_bank_runtime_memory_summary.get(
            "recommended_formalizer_target_mode", ""
        )
        or ""
    ) != "source_theorem_exact_proof_body_repair":
        return []
    diagnostics = [
        row
        for row in proof_bank_runtime_memory_summary.get(
            "source_theorem_exact_proof_body_repair_diagnostics", []
        )
        or []
        if isinstance(row, Mapping)
    ]
    repair_context = next(
        (
            row
            for row in diagnostics
            if str(row.get("proof_body_repair_scope", "") or "")
            == "replace_entire_exact_declaration_proof_body"
            and str(row.get("target_theorem_statement", "") or "").strip()
        ),
        None,
    )
    if repair_context is None:
        return []
    expected_statement = str(
        repair_context.get("target_theorem_statement", "") or ""
    ).strip()
    expected_declaration = str(
        repair_context.get("target_theorem_name", "")
        or repair_context.get("target_lean_declaration", "")
        or ""
    ).strip()
    if not expected_declaration:
        expected_declaration = _formalizer_lean_declaration_name(expected_statement)
    expected_signature = _normalized_lean_declaration_signature(expected_statement)
    lean_targets = [
        row
        for row in packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
        and str(row.get("lean_statement_sketch", "") or "").strip()
    ]
    source_targets: list[Mapping[str, Any]] = []
    for row in lean_targets:
        source = str(row.get("lean_statement_sketch", "") or "").strip()
        provenance = (
            row.get("source_theorem_target_provenance", {})
            if isinstance(
                row.get("source_theorem_target_provenance", {}), Mapping
            )
            else {}
        )
        provenance_declaration = str(
            provenance.get("target_lean_declaration", "") or ""
        ).strip()
        source_target_known = _source_theorem_target_known(provenance)
        if (
            source_target_known is True
            or _formalizer_lean_declaration_name(source) == expected_declaration
            or (
                source_target_known is not False
                and provenance_declaration == expected_declaration
            )
        ):
            source_targets.append(row)
    if not source_targets:
        if _exact_source_theorem_whole_proof_typed_blocker_present(
            packet,
            expected_declaration=expected_declaration,
        ):
            return []
        return [
            "exact source theorem whole-proof repair requires either a complete "
            "Lean source-theorem candidate preserving target_theorem_statement "
            "or a typed FORMAL_GAP with a concrete retrieval/dependency work order"
        ]

    observed_declarations: list[str] = []
    exact_signature_candidate_found = False
    provenance_mismatches: list[str] = []
    missing_complete_proof_body = False
    for target in source_targets:
        source = str(target.get("lean_statement_sketch", "") or "").strip()
        declaration = _formalizer_lean_declaration_name(source)
        if declaration:
            observed_declarations.append(declaration)
        provenance = (
            target.get("source_theorem_target_provenance", {})
            if isinstance(
                target.get("source_theorem_target_provenance", {}), Mapping
            )
            else {}
        )
        provenance_declaration = str(
            provenance.get("target_lean_declaration", "") or ""
        ).strip()
        if (
            expected_declaration
            and provenance_declaration
            and provenance_declaration != expected_declaration
        ):
            provenance_mismatches.append(provenance_declaration)
        proof_match = re.search(r":=\s*by\b", source)
        if not proof_match:
            missing_complete_proof_body = True
            continue
        candidate_signature = _normalized_lean_declaration_signature(
            source[: proof_match.start()]
        )
        if (
            (not expected_declaration or declaration == expected_declaration)
            and candidate_signature == expected_signature
            and source[proof_match.end() :].strip()
        ):
            exact_signature_candidate_found = True

    errors: list[str] = []
    if not exact_signature_candidate_found:
        if expected_declaration and expected_declaration not in observed_declarations:
            errors.append(
                "exact source theorem whole-proof repair must preserve declaration "
                f"name {expected_declaration!r}; observed: "
                + ", ".join(observed_declarations or ["<none>"])
            )
        errors.append(
            "exact source theorem whole-proof repair must preserve "
            "target_theorem_statement exactly modulo whitespace and replace only "
            "the complete proof after `:= by`"
        )
    if provenance_mismatches:
        errors.append(
            "exact source theorem whole-proof repair provenance must keep "
            f"target_lean_declaration={expected_declaration!r}; observed: "
            + ", ".join(dict.fromkeys(provenance_mismatches))
        )
    if missing_complete_proof_body and not exact_signature_candidate_found:
        errors.append(
            "exact source theorem whole-proof repair candidate must include a "
            "nonempty complete proof after `:= by`"
        )
    return sorted(set(errors))


def _formalizer_lean_declaration_name(source: str) -> str:
    match = re.search(
        r"\b(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
        str(source or ""),
    )
    return match.group(1) if match else ""


def _exact_source_theorem_whole_proof_typed_blocker_present(
    packet: Mapping[str, Any],
    *,
    expected_declaration: str,
) -> bool:
    formal_gap_targets = [
        row
        for row in packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
        and str(row.get("expected_status", "") or "") == "FORMAL_GAP"
    ]
    matching_gap_target = any(
        expected_declaration
        in {
            str(row.get("id", "") or "").strip(),
            str(
                (
                    row.get("source_theorem_target_provenance", {})
                    if isinstance(
                        row.get("source_theorem_target_provenance", {}), Mapping
                    )
                    else {}
                ).get("target_lean_declaration", "")
                or ""
            ).strip(),
        }
        for row in formal_gap_targets
    )
    typed_gaps = [
        row
        for row in packet.get("gap_taxonomy", []) or []
        if isinstance(row, Mapping)
        and str(
            row.get("gap", "")
            or row.get("description", "")
            or row.get("blocker", "")
            or ""
        ).strip()
        and str(
            row.get("kind", "")
            or row.get("gap_type", "")
            or row.get("category", "")
            or ""
        ).strip()
    ]
    dependency_work_available = bool(
        packet.get("retrieval_queries", [])
        or packet.get("source_to_bridge_premise_derivation_candidate_requests", [])
        or packet.get("proof_bank_obligation_requests", [])
    )
    return bool(matching_gap_target and typed_gaps and dependency_work_available)


def _normalized_lean_declaration_signature(source: str) -> str:
    return re.sub(r"\s+", " ", str(source or "").strip())


def _validate_source_theorem_candidate_materialization_packet(
    packet: Mapping[str, Any],
    *,
    environment_feedback: Mapping[str, Any] | None = None,
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    context = _source_theorem_candidate_materialization_context(
        environment_feedback=environment_feedback,
        proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
    )
    if not context["required"]:
        return []
    formal_targets = [
        row
        for row in packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
    ]
    if _feedback_has_repeated_syntax_failure_contract(environment_feedback):
        source_to_bridge_candidate_targets = [
            row
            for row in packet.get(
                "source_to_bridge_premise_derivation_candidates", []
            )
            or []
            if isinstance(row, Mapping)
            and _source_to_bridge_candidate_lean_source(row).strip()
        ]
        if (
            _has_explicit_source_theorem_formal_gap_target(formal_targets)
            or source_to_bridge_candidate_targets
        ):
            return []
    source_candidates: list[Mapping[str, Any]] = []
    for row in formal_targets:
        source = str(row.get("lean_statement_sketch", "") or "").strip()
        provenance = (
            row.get("source_theorem_target_provenance", {})
            if isinstance(row.get("source_theorem_target_provenance", {}), Mapping)
            else {}
        )
        if (
            str(row.get("expected_status", "") or "") == "NEEDS_KERNEL_CHECK"
            and source
            and not source.startswith("FORMAL_GAP")
            and re.search(r"\b(theorem|lemma)\b", source)
            and _source_theorem_target_known(provenance) is True
        ):
            source_candidates.append(row)
    errors: list[str] = []
    if not source_candidates:
        errors.append(
            "source_theorem_exact_candidate_materialization_required requires "
            "a concrete source-theorem formal_targets entry with "
            "expected_status=NEEDS_KERNEL_CHECK, nonempty Lean theorem/lemma "
            "sketch, and source_theorem_target_provenance. "
            "source_theorem_target_known=true; FORMAL_GAP and helper/support "
            "candidates do not satisfy this materialization gate"
        )
        return errors
    requested_targets = set(context["target_ids"] or context["target_names"])
    if requested_targets:
        matched = any(
            requested_targets
            & _formal_target_materialization_identity_tokens(row)
            for row in source_candidates
        )
        if not matched:
            errors.append(
                "source_theorem_exact_candidate_materialization_required "
                "formal_targets candidate must preserve a requested target "
                "id/name: "
                + ", ".join(sorted(requested_targets))
            )
    return sorted(set(errors))


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
    body = dict(payload)
    _normalize_formalizer_candidate_lean_source_aliases(body)
    _normalize_required_formalizer_scaffolding_fields(body)
    _enrich_source_to_bridge_candidates_from_memory(
        body,
        proof_bank_runtime_memory_summary or {},
    )
    _enrich_source_to_bridge_candidates_from_packet_requests(body)
    _quarantine_unbound_source_to_bridge_candidates(
        body,
        proof_bank_runtime_memory_summary or {},
    )
    _drop_source_to_bridge_candidates_with_uninstantiated_adapter_binders(body)
    _drop_semantically_unanchored_source_to_bridge_candidates(body)
    _drop_phantom_source_to_bridge_next_actions(body)
    _ensure_diagnostic_helper_bridge_or_blocker_packet(
        body,
        proof_bank_runtime_memory_summary or {},
    )
    _normalize_pseudo_formal_proof_packets(body)
    _bind_formal_target_role_provenance(body)
    _fail_closed_placeholder_lean_candidates(
        body,
        environment_feedback or {},
        proof_bank_runtime_memory_summary or {},
    )
    _normalize_executable_candidate_expected_statuses(body)
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


def _normalize_pseudo_formal_proof_packets(packet: dict[str, Any]) -> None:
    rows = packet.get("pseudo_formal_proof_packets", [])
    if rows in (None, "", [], {}):
        packet["pseudo_formal_proof_packets"] = []
        return
    if not isinstance(rows, list | tuple):
        packet["pseudo_formal_proof_packets"] = []
        packet["pseudo_formal_proof_packets_normalizer_status"] = (
            "dropped_non_list_container"
        )
        return
    normalized_rows = [
        normalize_pseudo_formal_packet(row)
        for row in rows
        if isinstance(row, Mapping)
    ]
    if len(normalized_rows) != len(rows):
        packet["pseudo_formal_proof_packets_normalizer_status"] = (
            "dropped_non_object_rows"
        )
    elif normalized_rows:
        packet["pseudo_formal_proof_packets_normalizer_status"] = (
            "normalized_non_proof_boundary"
        )
    packet["pseudo_formal_proof_packets"] = normalized_rows
    validation_errors = []
    for index, row in enumerate(normalized_rows):
        errors = validate_pseudo_formal_packet(row)
        if errors:
            validation_errors.append(
                {
                    "index": index,
                    "packet_id": row.get("packet_id", ""),
                    "errors": errors,
                }
            )
    if validation_errors:
        packet["pseudo_formal_proof_packet_validation_errors"] = validation_errors


def _normalize_required_formalizer_scaffolding_fields(packet: dict[str, Any]) -> None:
    """Normalize optional routing fields without fabricating work or findings."""

    normalized: list[str] = []
    if (
        "lemma_dependency_plan" not in packet
        or packet.get("lemma_dependency_plan") in (None, "", {})
    ):
        packet["lemma_dependency_plan"] = []
        normalized.append("lemma_dependency_plan")
    if "retrieval_queries" not in packet or packet.get("retrieval_queries") in (
        None,
        "",
        {},
    ):
        packet["retrieval_queries"] = []
        normalized.append("retrieval_queries")
    if "proof_search_plan" not in packet or packet.get("proof_search_plan") in (
        None,
        "",
        [],
    ):
        packet["proof_search_plan"] = {}
        normalized.append("proof_search_plan")
    if "gap_taxonomy" not in packet or packet.get("gap_taxonomy") in (
        None,
        "",
        {},
    ):
        packet["gap_taxonomy"] = []
        normalized.append("gap_taxonomy")
    if "critic_findings" not in packet or packet.get("critic_findings") in (
        None,
        "",
        {},
    ):
        packet["critic_findings"] = []
        normalized.append("critic_findings")
    if "next_actions" not in packet or packet.get("next_actions") in (
        None,
        "",
        {},
    ):
        packet["next_actions"] = []
        normalized.append("next_actions")
    if not normalized:
        return

    existing = packet.get("normalized_missing_required_scaffolding_fields", [])
    if not isinstance(existing, list):
        existing = []
    packet["normalized_missing_required_scaffolding_fields"] = [
        *existing,
        *normalized,
    ]
    packet["scaffolding_normalizer_proof_evidence_status"] = (
        "EMPTY_OPTIONAL_ROUTING_FIELDS_NOT_PROOF_EVIDENCE"
    )


def _normalize_formalizer_candidate_lean_source_aliases(packet: dict[str, Any]) -> None:
    """Canonicalize harmless Lean-source field aliases before validation.

    This does not make a candidate executable or proved. It only maps common LLM
    schema aliases onto the fields that the runtime validators and materializers
    already require.
    """

    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(packet.get("formal_targets", []) or [], start=1):
        if not isinstance(row, dict):
            continue
        if str(row.get("lean_statement_sketch", "") or "").strip():
            continue
        for alias_key in (
            "lean_source",
            "lean_code",
            "candidate_lean_source",
            "formal_statement_lean",
            "lean_theorem",
            "theorem_lean_source",
            "statement",
            "lean_statement",
        ):
            alias_value = str(row.get(alias_key, "") or "").strip()
            if not alias_value:
                continue
            row["lean_statement_sketch"] = alias_value
            row["lean_statement_sketch_normalized_from"] = alias_key
            normalized.append(
                {
                    "channel": "formal_targets",
                    "index": index,
                    "id": str(row.get("id", "") or ""),
                    "normalized_from": alias_key,
                    "lean_source_fingerprint": stable_hash(alias_value)[:20],
                }
            )
            break

    for index, row in enumerate(
        packet.get("source_to_bridge_premise_derivation_candidates", []) or [],
        start=1,
    ):
        if not isinstance(row, dict):
            continue
        if str(row.get("premise_derivation_candidate_lean_source", "") or "").strip():
            continue
        for alias_key in (
            "lean_source",
            "lean_code",
            "candidate_lean_source",
            "lean_statement_sketch",
            "premise_candidate_lean_source",
            "premise_lean_source",
            "source",
        ):
            alias_value = str(row.get(alias_key, "") or "").strip()
            if not alias_value:
                continue
            row["premise_derivation_candidate_lean_source"] = alias_value
            row["premise_derivation_candidate_lean_source_normalized_from"] = alias_key
            normalized.append(
                {
                    "channel": "source_to_bridge_premise_derivation_candidates",
                    "index": index,
                    "premise_name": str(row.get("premise_name", "") or ""),
                    "normalized_from": alias_key,
                    "lean_source_fingerprint": stable_hash(alias_value)[:20],
                }
            )
            break

    if not normalized:
        return
    existing = packet.get("normalized_lean_source_aliases", [])
    if not isinstance(existing, list):
        existing = []
    packet["normalized_lean_source_aliases"] = [*existing, *normalized]
    packet["lean_source_alias_normalizer_proof_evidence_status"] = (
        "LEAN_SOURCE_ALIAS_NORMALIZED_NOT_PROOF_EVIDENCE"
    )


def _normalize_executable_candidate_expected_statuses(
    packet: dict[str, Any],
) -> None:
    """Generated Lean is executable work and must be sent through kernel checking."""

    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(packet.get("formal_targets", []) or [], start=1):
        if not isinstance(row, dict):
            continue
        lean_source = str(row.get("lean_statement_sketch", "") or "")
        if not lean_source.strip():
            continue
        if _lean_source_is_descriptive_placeholder(lean_source):
            continue
        previous = str(row.get("expected_status", "") or "")
        if previous == "NEEDS_KERNEL_CHECK":
            continue
        if previous not in {"", "OPEN", "FORMAL_GAP"}:
            continue
        row["expected_status"] = "NEEDS_KERNEL_CHECK"
        row["expected_status_normalized_from"] = previous or "<missing>"
        row["expected_status_normalizer_status"] = (
            "EXECUTABLE_LEAN_CANDIDATE_REQUIRES_KERNEL_CHECK"
        )
        row.setdefault(
            "proof_evidence_status",
            "FORMALIZER_EXECUTABLE_CANDIDATE_STATUS_NORMALIZED_NOT_PROOF_EVIDENCE",
        )
        normalized.append(
            {
                "channel": "formal_targets",
                "index": index,
                "id": str(row.get("id", "") or ""),
                "previous_expected_status": previous or "<missing>",
                "new_expected_status": "NEEDS_KERNEL_CHECK",
                "lean_source_fingerprint": stable_hash(lean_source)[:20],
            }
        )

    for index, row in enumerate(
        packet.get("source_to_bridge_premise_derivation_candidates", []) or [],
        start=1,
    ):
        if not isinstance(row, dict):
            continue
        lean_source = _source_to_bridge_candidate_lean_source(row)
        if not lean_source.strip():
            continue
        if _lean_source_is_descriptive_placeholder(lean_source):
            continue
        previous = str(row.get("expected_status", "") or "")
        if previous == "NEEDS_KERNEL_CHECK":
            continue
        if previous not in {"", "OPEN", "FORMAL_GAP"}:
            continue
        row["expected_status"] = "NEEDS_KERNEL_CHECK"
        row["expected_status_normalized_from"] = previous or "<missing>"
        row["expected_status_normalizer_status"] = (
            "EXECUTABLE_SOURCE_TO_BRIDGE_CANDIDATE_REQUIRES_KERNEL_CHECK"
        )
        row.setdefault(
            "proof_evidence_status",
            "FORMALIZER_EXECUTABLE_CANDIDATE_STATUS_NORMALIZED_NOT_PROOF_EVIDENCE",
        )
        normalized.append(
            {
                "channel": "source_to_bridge_premise_derivation_candidates",
                "index": index,
                "premise_name": str(row.get("premise_name", "") or ""),
                "previous_expected_status": previous or "<missing>",
                "new_expected_status": "NEEDS_KERNEL_CHECK",
                "lean_source_fingerprint": stable_hash(lean_source)[:20],
            }
        )

    if not normalized:
        return

    existing = packet.get("normalized_executable_candidate_expected_statuses", [])
    if not isinstance(existing, list):
        existing = []
    packet["normalized_executable_candidate_expected_statuses"] = [
        *existing,
        *normalized,
    ]
    findings = packet.get("critic_findings", [])
    if not isinstance(findings, list):
        findings = []
    findings.append(
        {
            "critic": "local_formalizer_packet_normalizer",
            "finding": (
                "Normalized Lean-bearing formalizer candidates to "
                "expected_status=NEEDS_KERNEL_CHECK. FORMAL_GAP is reserved "
                "for empty, non-executable gap records."
            ),
            "proof_evidence_status": (
                "EXECUTABLE_CANDIDATE_STATUS_NORMALIZATION_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["critic_findings"] = findings


def _normalize_source_theorem_target_shape_drift(
    packet: dict[str, Any],
    environment_feedback: Mapping[str, Any],
) -> None:
    """Deprecated: independent semantic review owns task-target alignment."""

    del packet, environment_feedback


def _drop_semantically_unanchored_source_to_bridge_candidates(
    packet: dict[str, Any],
) -> None:
    candidates = packet.get("source_to_bridge_premise_derivation_candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return

    kept: list[Any] = []
    dropped: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, Mapping):
            kept.append(candidate)
            continue
        candidate_source = _source_to_bridge_candidate_lean_source(candidate)
        missing_anchor_names = _source_to_bridge_candidate_missing_anchor_references(
            candidate,
            candidate_source,
        )
        if not missing_anchor_names:
            kept.append(candidate)
            continue
        premise_names = _source_to_bridge_candidate_premise_names(candidate)
        dropped.append(
            {
                "index": index,
                "premise_name": str(candidate.get("premise_name", "") or ""),
                "premise_names": premise_names,
                "missing_required_semantic_anchor_reference_names": list(
                    missing_anchor_names
                ),
                "lean_source_fingerprint": stable_hash(candidate_source)[:20],
                "proof_evidence_status": (
                    "SEMANTICALLY_UNANCHORED_SOURCE_TO_BRIDGE_CANDIDATE_DROPPED_NOT_PROOF_EVIDENCE"
                ),
            }
        )

    if not dropped:
        return

    packet["source_to_bridge_premise_derivation_candidates"] = kept
    existing = packet.get(
        "dropped_semantic_anchor_source_to_bridge_candidates",
        [],
    )
    if not isinstance(existing, list):
        existing = []
    packet["dropped_semantic_anchor_source_to_bridge_candidates"] = [
        *existing,
        *dropped,
    ]

    blocked_premise_names = list(
        dict.fromkeys(
            name
            for row in dropped
            for name in (
                row.get("premise_names", [])
                if isinstance(row.get("premise_names", []), list)
                else []
            )
            if str(name).strip()
        )
    )
    missing_anchor_names = list(
        dict.fromkeys(
            str(name).strip()
            for row in dropped
            for name in row.get(
                "missing_required_semantic_anchor_reference_names",
                [],
            )
            if str(name).strip()
        )
    )
    gap_rows = packet.get("gap_taxonomy", [])
    if not isinstance(gap_rows, list):
        gap_rows = []
    gap_rows.append(
        {
            "gap": (
                "Dropped executable source-to-bridge premise candidate(s) "
                "because their Lean source did not reference every required "
                "semantic anchor outside comments. Emit no executable candidate "
                "until the anchors can be used non-vacuously."
            ),
            "kind": "source_to_bridge_semantic_anchor_blocker",
            "next_owner": "TheoryDeveloper/Formalizer/ProofEngineer",
            "premise_names": blocked_premise_names,
            "missing_required_semantic_anchor_reference_names": missing_anchor_names,
            "proof_evidence_status": (
                "SOURCE_TO_BRIDGE_SEMANTIC_ANCHOR_BLOCKER_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["gap_taxonomy"] = gap_rows

    actions = packet.get("next_actions", [])
    if not isinstance(actions, list):
        actions = []
    action_text = " ".join(
        " ".join(
            str(action.get(key, "") or "")
            for key in ("owner_agent", "action", "acceptance_gate")
        ).lower()
        for action in actions
        if isinstance(action, Mapping)
    )
    if "semantic anchor" not in action_text:
        actions.append(
            {
                "owner_agent": "TheoryDeveloper/Formalizer/ProofEngineer",
                "action": (
                    "Repair the source-to-bridge premise derivation by using "
                    "the required semantic anchors non-vacuously, or keep the "
                    "premise as a semantic-anchor blocker without executable "
                    "Lean."
                ),
                "acceptance_gate": (
                    "a later source-to-bridge candidate references every required "
                    "semantic anchor outside comments and passes local Lean/AXLE"
                ),
            }
        )
    packet["next_actions"] = actions

    findings = packet.get("critic_findings", [])
    if not isinstance(findings, list):
        findings = []
    findings.append(
        {
            "critic": "local_formalizer_packet_normalizer",
            "finding": (
                "Dropped source-to-bridge premise candidates that omitted "
                "required semantic-anchor references, converting them to "
                "non-executable semantic blockers instead of proof work."
            ),
            "proof_evidence_status": (
                "SOURCE_TO_BRIDGE_SEMANTIC_ANCHOR_BLOCKER_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["critic_findings"] = findings


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


def _lean_source_is_descriptive_placeholder(source: str) -> bool:
    return bool(re.search(r"\.\.\.", str(source or "")))


def _feedback_requests_placeholder_fail_closed(
    environment_feedback: Mapping[str, Any],
) -> bool:
    if not isinstance(environment_feedback, Mapping):
        return False
    local_lean_repair_contract = (
        environment_feedback.get("local_lean_repair_contract", {})
        if isinstance(environment_feedback.get("local_lean_repair_contract", {}), Mapping)
        else {}
    )
    if bool(local_lean_repair_contract.get("repeated_syntax_failure", False)):
        return True
    input_summary = (
        environment_feedback.get("input_summary", {})
        if isinstance(environment_feedback.get("input_summary", {}), Mapping)
        else {}
    )
    failure_classification = str(
        environment_feedback.get("failure_classification", "")
        or input_summary.get("failure_classification", "")
        or ""
    )
    if failure_classification != "formalizer_packet_validation_failed":
        return False
    validation_errors = [
        str(error)
        for error in (
            environment_feedback.get("validation_errors", [])
            or input_summary.get("validation_errors", [])
            or []
        )
        if str(error).strip()
    ]
    validation_text = " ".join(validation_errors).lower()
    has_placeholder_failure = any(
        marker in validation_text
        for marker in (
            "lean sorry placeholder",
            "lean admit placeholder",
            "interactive proof-hole marker",
            "unsupported tactic hole",
            " exact?",
            " by?",
            "admit",
            "sorry",
        )
    )
    if not has_placeholder_failure:
        return False
    retry_depth = _feedback_int(
        environment_feedback.get("formalizer_packet_repair_retry_depth", 0)
        or input_summary.get("formalizer_packet_repair_retry_depth", 0)
    )
    attempts = _feedback_int(
        environment_feedback.get("attempts", 0) or input_summary.get("attempts", 0)
    )
    repeated = bool(
        environment_feedback.get("repeated_formalizer_packet_validation_failure")
        or input_summary.get("repeated_formalizer_packet_validation_failure")
        or retry_depth > 0
        or attempts > 1
    )
    return repeated or _feedback_has_source_theorem_target_drift(environment_feedback)


def _fail_closed_placeholder_lean_candidates(
    packet: dict[str, Any],
    environment_feedback: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
) -> None:
    placeholder_fail_closed_requested = _feedback_requests_placeholder_fail_closed(
        environment_feedback
    )
    required_pf_bv_route_available = (
        _feedback_requires_pseudo_formalization(
            environment_feedback,
            proof_bank_runtime_memory_summary or {},
        )
        and not _validate_required_pseudo_formalization_packet(
            packet,
            environment_feedback=environment_feedback,
            proof_bank_runtime_memory_summary=(
                proof_bank_runtime_memory_summary or {}
            ),
        )
    )
    if not (placeholder_fail_closed_requested or required_pf_bv_route_available):
        return
    converted_targets: list[dict[str, Any]] = []
    for row in packet.get("formal_targets", []) or []:
        if not isinstance(row, dict):
            continue
        lean_source = str(row.get("lean_statement_sketch", "") or "")
        placeholder_error = _lean_statement_placeholder_syntax_error(lean_source)
        if not placeholder_error:
            continue
        previous_role = _formal_target_role(row)
        provenance = row.get("source_theorem_target_provenance", {})
        target_known = _source_theorem_target_known(provenance)
        normalized_role = previous_role
        if (
            previous_role == FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE
            or previous_role == FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP
            or target_known is True
        ):
            normalized_role = FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP
        elif previous_role == FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT or target_known is False:
            normalized_role = FORMAL_TARGET_ROLE_HELPER_OR_SUPPORT
        converted_targets.append(
            {
                "id": str(row.get("id", "") or ""),
                "previous_formal_target_role": previous_role,
                "new_formal_target_role": normalized_role,
                "previous_expected_status": str(
                    row.get("expected_status", "") or ""
                ),
                "placeholder_error": placeholder_error,
                "lean_source_fingerprint": stable_hash(lean_source)[:20],
                "proof_evidence_status": (
                    "PLACEHOLDER_LEAN_SKETCH_REMOVED_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        row["expected_status"] = "FORMAL_GAP"
        row["lean_statement_sketch"] = ""
        row["candidate_lean_declaration"] = ""
        if normalized_role:
            row["formal_target_role"] = normalized_role
        row["proof_evidence_status"] = (
            "FORMAL_GAP_PLACEHOLDER_LEAN_SKETCH_REMOVED_NOT_PROOF_EVIDENCE"
        )
        row["normalizer_status"] = (
            "FAIL_CLOSED_PLACEHOLDER_LEAN_SKETCH_TO_FORMAL_GAP"
        )

    source_to_bridge_candidates = packet.get(
        "source_to_bridge_premise_derivation_candidates",
        [],
    )
    dropped_source_to_bridge: list[dict[str, Any]] = []
    kept_source_to_bridge: list[Any] = []
    if isinstance(source_to_bridge_candidates, list):
        for index, candidate in enumerate(source_to_bridge_candidates, start=1):
            if not isinstance(candidate, Mapping):
                kept_source_to_bridge.append(candidate)
                continue
            candidate_source = _source_to_bridge_candidate_lean_source(candidate)
            placeholder_error = _lean_statement_placeholder_syntax_error(
                candidate_source
            )
            if not placeholder_error:
                kept_source_to_bridge.append(candidate)
                continue
            dropped_source_to_bridge.append(
                {
                    "index": index,
                    "premise_name": str(candidate.get("premise_name", "") or ""),
                    "placeholder_error": placeholder_error,
                    "lean_source_fingerprint": stable_hash(candidate_source)[:20],
                    "proof_evidence_status": (
                        "PLACEHOLDER_SOURCE_TO_BRIDGE_CANDIDATE_DROPPED_NOT_PROOF_EVIDENCE"
                    ),
                }
            )
        if dropped_source_to_bridge:
            packet["source_to_bridge_premise_derivation_candidates"] = (
                kept_source_to_bridge
            )

    if not converted_targets and not dropped_source_to_bridge:
        return

    _bind_formal_target_role_provenance(packet)

    formal_targets = [
        row
        for row in packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
    ]
    source_theorem_target_drift = _feedback_has_source_theorem_target_drift(
        environment_feedback
    )
    if (
        source_theorem_target_drift
        and not _has_explicit_source_theorem_formal_gap_target(formal_targets)
    ):
        packet["source_theorem_formal_gap_synthesis_skipped"] = {
            "reason": "source_theorem_gap_requires_explicit_agent_target",
            "proof_evidence_status": (
                "SOURCE_THEOREM_GAP_NOT_SYNTHESIZED_NOT_PROOF_EVIDENCE"
            ),
        }

    gap_rows = packet.get("gap_taxonomy", [])
    if not isinstance(gap_rows, list):
        gap_rows = []
    gap_rows.append(
        {
            "gap": (
                "placeholder Lean proof sketches were fail-closed to FORMAL_GAP"
            ),
            "kind": "proof_hole_placeholder_removed",
            "next_owner": "Formalizer",
            "proof_evidence_status": (
                "PLACEHOLDER_LEAN_SKETCH_REMOVED_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["gap_taxonomy"] = gap_rows

    if converted_targets:
        packet["fail_closed_placeholder_formal_targets"] = converted_targets
    if dropped_source_to_bridge:
        existing_dropped = packet.get(
            "dropped_placeholder_source_to_bridge_candidates",
            [],
        )
        if not isinstance(existing_dropped, list):
            existing_dropped = []
        packet["dropped_placeholder_source_to_bridge_candidates"] = [
            *existing_dropped,
            *dropped_source_to_bridge,
        ]

    findings = packet.get("critic_findings", [])
    if not isinstance(findings, list):
        findings = []
    findings.append(
        {
            "critic": "local_formalizer_packet_normalizer",
            "finding": (
                "Removed placeholder Lean proof sketches after repeated packet "
                "validation feedback and converted the affected executable work "
                "to explicit FORMAL_GAP/non-executable gap records."
            ),
            "proof_evidence_status": (
                "PLACEHOLDER_LEAN_SKETCH_REMOVED_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["critic_findings"] = findings


def _source_to_bridge_candidate_names(packet: Mapping[str, Any]) -> set[str]:
    candidate_names: set[str] = set()
    for row in packet.get("source_to_bridge_premise_derivation_candidates", []) or []:
        if not isinstance(row, Mapping):
            continue
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
    return candidate_names


def _source_to_bridge_next_action_is_phantom(
    action: Mapping[str, Any],
    *,
    has_candidates: bool,
    candidate_names: set[str],
) -> bool:
    action_text = " ".join(
        str(action.get(key, "") or "")
        for key in ("owner_agent", "action", "acceptance_gate")
    ).lower()
    if "source_to_bridge_premise_derivation_candidates" not in action_text:
        return False
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
        return False
    if not has_candidates:
        return True
    return " entry " in action_text and not any(
        name and name in action_text for name in candidate_names
    )


def _drop_phantom_source_to_bridge_next_actions(packet: dict[str, Any]) -> None:
    actions = packet.get("next_actions", [])
    if not isinstance(actions, list) or not actions:
        return
    candidates = [
        row
        for row in packet.get("source_to_bridge_premise_derivation_candidates", [])
        or []
        if isinstance(row, Mapping)
    ]
    candidate_names = _source_to_bridge_candidate_names(packet)
    kept: list[Any] = []
    dropped: list[dict[str, Any]] = []
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, Mapping):
            kept.append(action)
            continue
        if _source_to_bridge_next_action_is_phantom(
            action,
            has_candidates=bool(candidates),
            candidate_names=candidate_names,
        ):
            dropped.append(
                {
                    "index": index,
                    "owner_agent": str(action.get("owner_agent", "") or ""),
                    "action": str(action.get("action", "") or "")[:500],
                    "reason": (
                        "next action requested execution of absent or unmatched "
                        "source-to-bridge premise candidate work"
                    ),
                }
            )
            continue
        kept.append(action)
    if not dropped:
        return
    if not kept:
        kept = [
            {
                "owner_agent": "Formalizer",
                "action": (
                    "Record the missing premise-derivation work as a "
                    "non-executable gap/dependency until a concrete candidate "
                    "object with source-binding metadata is emitted."
                ),
                "acceptance_gate": (
                    "gap_taxonomy or lemma_dependency_plan names the missing "
                    "source-binding metadata"
                ),
            }
        ]
    packet["next_actions"] = kept
    existing_dropped = packet.get(
        "dropped_phantom_source_to_bridge_next_actions",
        [],
    )
    if not isinstance(existing_dropped, list):
        existing_dropped = []
    packet["dropped_phantom_source_to_bridge_next_actions"] = [
        *existing_dropped,
        *dropped,
    ]
    findings = packet.get("critic_findings", [])
    if not isinstance(findings, list):
        findings = []
    findings.append(
        {
            "critic": "local_formalizer_packet_normalizer",
            "finding": (
                "Dropped phantom next_actions that requested runtime execution "
                "of absent source-to-bridge premise candidates. The dropped "
                "actions are not proof evidence and were converted into a "
                "non-executable gap/dependency action."
            ),
            "proof_evidence_status": "DROPPED_PHANTOM_NEXT_ACTION_NOT_PROOF_EVIDENCE",
        }
    )
    packet["critic_findings"] = findings


def _quarantine_unbound_source_to_bridge_candidates(
    packet: dict[str, Any],
    proof_memory_summary: Mapping[str, Any],
) -> None:
    """Drop unrequested source-to-bridge candidates before they block generic Lean checks."""

    candidates = packet.get("source_to_bridge_premise_derivation_candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return
    shortcuts = _source_to_bridge_candidate_request_shortcuts(
        _compact_proof_bank_runtime_memory_summary(proof_memory_summary)
    )
    if shortcuts:
        return
    kept: list[Any] = []
    dropped: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, Mapping):
            kept.append(candidate)
            continue
        if _source_to_bridge_candidate_has_source_binding_contract(candidate):
            kept.append(candidate)
            continue
        premise_name = str(candidate.get("premise_name", "") or "").strip()
        premise_names = [
            str(value).strip()
            for value in candidate.get("premise_names", []) or []
            if str(value).strip()
        ] if isinstance(candidate.get("premise_names", []), list | tuple | set) else []
        dropped.append(
            {
                "index": index,
                "premise_name": premise_name,
                "premise_names": premise_names,
                "reason": (
                    "source-to-bridge premise candidate omitted because the "
                    "runtime memory did not expose a matching source-binding "
                    "candidate request; this is not proof evidence"
                ),
            }
        )
    if not dropped:
        return
    packet["source_to_bridge_premise_derivation_candidates"] = kept
    existing_dropped = packet.get(
        "dropped_source_to_bridge_premise_derivation_candidates",
        [],
    )
    if not isinstance(existing_dropped, list):
        existing_dropped = []
    packet["dropped_source_to_bridge_premise_derivation_candidates"] = [
        *existing_dropped,
        *dropped,
    ]
    findings = packet.get("critic_findings", [])
    if not isinstance(findings, list):
        findings = []
    findings.append(
        {
            "critic": "local_formalizer_packet_normalizer",
            "finding": (
                "Dropped source_to_bridge_premise_derivation_candidates that "
                "lacked source-binding metadata while no runtime request "
                "shortcut was available. Use ordinary formal_targets for "
                "generic Lean candidate checks, or wait for a source-to-bridge "
                "ProofEngineer request before emitting premise candidates."
            ),
            "proof_evidence_status": "DROPPED_UNBOUND_SOURCE_TO_BRIDGE_CANDIDATE_NOT_PROOF_EVIDENCE",
        }
    )
    packet["critic_findings"] = findings


def _drop_source_to_bridge_candidates_with_uninstantiated_adapter_binders(
    packet: dict[str, Any],
) -> None:
    """Quarantine candidates that turn required adapter objects into assumptions."""

    candidates = packet.get("source_to_bridge_premise_derivation_candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return
    kept: list[Any] = []
    dropped: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, Mapping):
            kept.append(candidate)
            continue
        candidate_source = _source_to_bridge_candidate_lean_source(candidate)
        uninstantiated_adapter_binders = (
            _source_to_bridge_candidate_uninstantiated_adapter_object_binders(
                candidate,
                candidate_source,
            )
        )
        if not uninstantiated_adapter_binders:
            kept.append(candidate)
            continue
        premise_names = (
            [
                str(value).strip()
                for value in candidate.get("premise_names", []) or []
                if str(value).strip()
            ]
            if isinstance(candidate.get("premise_names", []), list | tuple | set)
            else []
        )
        dropped.append(
            {
                "index": index,
                "premise_name": str(candidate.get("premise_name", "") or ""),
                "premise_names": premise_names,
                "uninstantiated_adapter_object_binders": list(
                    uninstantiated_adapter_binders
                ),
                "reason": (
                    "source-to-bridge premise candidate omitted because it used "
                    "adapter objects requiring source instantiation as theorem "
                    "binders instead of deriving them from exact source binders; "
                    "this is not proof evidence"
                ),
                "failure_classification": (
                    "source_to_bridge_candidate_uninstantiated_adapter_objects"
                ),
            }
        )
    if not dropped:
        return
    packet["source_to_bridge_premise_derivation_candidates"] = kept
    existing_dropped = packet.get(
        "dropped_source_to_bridge_premise_derivation_candidates",
        [],
    )
    if not isinstance(existing_dropped, list):
        existing_dropped = []
    packet["dropped_source_to_bridge_premise_derivation_candidates"] = [
        *existing_dropped,
        *dropped,
    ]
    findings = packet.get("critic_findings", [])
    if not isinstance(findings, list):
        findings = []
    findings.append(
        {
            "critic": "local_formalizer_packet_normalizer",
            "finding": (
                "Dropped source_to_bridge_premise_derivation_candidates that "
                "introduced adapter objects as fresh theorem binders. The "
                "candidate must derive those objects from exact source binders "
                "or remain a formal blocker."
            ),
            "proof_evidence_status": (
                "DROPPED_UNINSTANTIATED_SOURCE_TO_BRIDGE_CANDIDATE_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["critic_findings"] = findings


def _diagnostic_helper_bridge_mode_active(
    proof_memory_summary: Mapping[str, Any],
) -> bool:
    mode = str(
        proof_memory_summary.get("recommended_formalizer_target_mode", "") or ""
    )
    return bool(
        mode == "source_theorem_diagnostic_helper_bridge_or_blocker"
        or proof_memory_summary.get("formalizer_diagnostic_helper_integration_required")
        or proof_memory_summary.get("formalizer_diagnostic_helper_memory")
    )


def _diagnostic_helper_bridge_blocker_contract(
    proof_memory_summary: Mapping[str, Any],
) -> dict[str, Any]:
    if not _diagnostic_helper_bridge_mode_active(proof_memory_summary):
        return {}
    if _source_to_bridge_candidate_request_shortcuts(proof_memory_summary):
        return {}
    helper_ids = [
        str(row.get("candidate_id", "") or "").strip()
        for row in proof_memory_summary.get("formalizer_diagnostic_helper_memory", [])
        or []
        if isinstance(row, Mapping) and str(row.get("candidate_id", "") or "").strip()
    ][:6]
    return {
        "contract_kind": "diagnostic_helper_bridge_or_blocker",
        "trigger": "compiled_diagnostic_helper_without_source_binding_request",
        "prior_helper_candidate_ids": helper_ids,
        "required_behavior": (
            "Do not repeat helper-only formal_targets as source-theorem progress. "
            "Emit a concrete source_to_bridge_premise_derivation_candidates object "
            "only when source-binding request metadata and semantic anchors are "
            "available to copy; otherwise record a gap_taxonomy row with "
            "kind=source_to_bridge_metadata_blocker and route source-binding "
            "metadata retrieval/authoring to AgentRuntime/ProofEngineer."
        ),
        "forbidden_resolution": (
            "Do not invent source_to_bridge_premise_derivation_candidates without "
            "a copied candidate request/source-binding contract, and do not ask "
            "AgentRuntime/AXLE/local Lean to execute helper-only candidates as if "
            "they advanced the source theorem proof."
        ),
        "proof_evidence_status": (
            "DIAGNOSTIC_HELPER_BRIDGE_BLOCKER_CONTRACT_NOT_PROOF_EVIDENCE"
        ),
    }


def _packet_has_source_to_bridge_metadata_blocker(
    packet: Mapping[str, Any],
) -> bool:
    blocker_markers = (
        "source_to_bridge_metadata_blocker",
        "source-binding metadata",
        "source binding metadata",
        "source-binding request",
        "source binding request",
        "semantic anchor",
        "semantic-anchor",
    )
    for row in packet.get("gap_taxonomy", []) or []:
        if not isinstance(row, Mapping):
            continue
        text = " ".join(
            str(row.get(key, "") or "")
            for key in ("gap", "kind", "next_owner")
        ).lower()
        if "source" in text and "bridge" in text and any(
            marker in text for marker in blocker_markers
        ):
            return True
    return False


def _packet_has_standard_source_to_bridge_metadata_blocker(
    packet: Mapping[str, Any],
) -> bool:
    return any(
        isinstance(row, Mapping)
        and str(row.get("kind", "") or "") == "source_to_bridge_metadata_blocker"
        for row in packet.get("gap_taxonomy", []) or []
    )


def _formal_target_is_diagnostic_helper(row: Mapping[str, Any]) -> bool:
    provenance = (
        row.get("source_theorem_target_provenance", {})
        if isinstance(row.get("source_theorem_target_provenance", {}), Mapping)
        else {}
    )
    known = provenance.get("source_theorem_target_known", None)
    known_text = str(known).strip().lower()
    return bool(
        known is False
        or known_text == "false"
        or row.get("diagnostic_helper_not_source_theorem") is True
        or str(row.get("proof_evidence_status", "") or "").startswith(
            "FORMALIZER_DIAGNOSTIC_HELPER"
        )
    )


def _diagnostic_helper_action_should_be_dropped(
    action: Mapping[str, Any],
    *,
    helper_names: set[str],
) -> bool:
    action_text = " ".join(
        str(action.get(key, "") or "")
        for key in ("owner_agent", "action", "acceptance_gate")
    ).lower()
    if not any(
        marker in action_text
        for marker in (
            "run ",
            "check",
            "compile",
            "verify",
            "kernel",
            "local lean",
            "axle",
        )
    ):
        return False
    if helper_names and any(name in action_text for name in helper_names):
        return True
    return bool("helper" in action_text and "formal_targets" in action_text)


def _ensure_diagnostic_helper_bridge_or_blocker_packet(
    packet: dict[str, Any],
    proof_memory_summary: Mapping[str, Any],
) -> None:
    compact_memory = _compact_proof_bank_runtime_memory_summary(
        proof_memory_summary or {}
    )
    contract = _diagnostic_helper_bridge_blocker_contract(compact_memory)
    if not contract:
        return
    candidates = [
        row
        for row in packet.get("source_to_bridge_premise_derivation_candidates", [])
        or []
        if isinstance(row, Mapping)
    ]
    if candidates:
        return
    gap_rows = packet.get("gap_taxonomy", [])
    if not isinstance(gap_rows, list):
        gap_rows = []
    added_blocker = False
    if (
        not _packet_has_source_to_bridge_metadata_blocker(packet)
        or not _packet_has_standard_source_to_bridge_metadata_blocker(packet)
    ):
        gap_rows.append(
            {
                "gap": (
                    "Compiled diagnostic helper evidence is not source-theorem proof "
                    "and cannot be promoted until runtime exposes exact "
                    "source-to-bridge source-binding request metadata plus semantic "
                    "anchor references to copy."
                ),
                "kind": "source_to_bridge_metadata_blocker",
                "next_owner": "AgentRuntime/ProofEngineer",
                "proof_evidence_status": (
                    "DIAGNOSTIC_HELPER_BRIDGE_BLOCKER_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        packet["gap_taxonomy"] = gap_rows
        added_blocker = True

    helper_names: set[str] = set()
    for target in packet.get("formal_targets", []) or []:
        if not isinstance(target, Mapping) or not _formal_target_is_diagnostic_helper(
            target
        ):
            continue
        for key in ("id", "target_lean_declaration"):
            value = str(target.get(key, "") or "").strip().lower()
            if value:
                helper_names.add(value)
        provenance = (
            target.get("source_theorem_target_provenance", {})
            if isinstance(target.get("source_theorem_target_provenance", {}), Mapping)
            else {}
        )
        declaration = str(
            provenance.get("target_lean_declaration", "") or ""
        ).strip().lower()
        if declaration:
            helper_names.add(declaration)

    actions = packet.get("next_actions", [])
    dropped_actions: list[dict[str, Any]] = []
    if isinstance(actions, list) and actions:
        kept_actions: list[Any] = []
        for index, action in enumerate(actions, start=1):
            if not isinstance(action, Mapping):
                kept_actions.append(action)
                continue
            if _diagnostic_helper_action_should_be_dropped(
                action,
                helper_names=helper_names,
            ):
                dropped_actions.append(
                    {
                        "index": index,
                        "owner_agent": str(action.get("owner_agent", "") or ""),
                        "action": str(action.get("action", "") or "")[:500],
                        "reason": (
                            "helper-only local Lean/AXLE work is diagnostic and "
                            "must not be routed as source-theorem bridge progress"
                        ),
                    }
                )
                continue
            kept_actions.append(action)
        if dropped_actions:
            actions = kept_actions

    blocker_action = {
        "owner_agent": "AgentRuntime/ProofEngineer",
        "action": (
            "Produce exact source-to-bridge premise-derivation request metadata "
            "or source semantic anchor definitions before asking Formalizer for "
            "an executable source_to_bridge_premise_derivation_candidates object."
        ),
        "acceptance_gate": (
            "proof_bank_runtime_memory_summary exposes a "
            "source_to_bridge_premise_derivation_candidate_request or grouped "
            "candidate request with source-binding metadata and semantic anchors"
        ),
    }
    existing_action_text = " ".join(
        " ".join(
            str(action.get(key, "") or "")
            for key in ("owner_agent", "action", "acceptance_gate")
        ).lower()
        for action in actions
        if isinstance(action, Mapping)
    )
    if "source-to-bridge" not in existing_action_text and "source_to_bridge" not in existing_action_text:
        actions = [blocker_action, *list(actions if isinstance(actions, list) else [])]
    if not actions:
        actions = [blocker_action]
    packet["next_actions"] = list(actions)

    packet["diagnostic_helper_bridge_blocker_status"] = (
        "SOURCE_TO_BRIDGE_METADATA_BLOCKER_RECORDED_NOT_PROOF_EVIDENCE"
        if added_blocker
        else "SOURCE_TO_BRIDGE_METADATA_BLOCKER_PRESERVED_NOT_PROOF_EVIDENCE"
    )
    if dropped_actions:
        existing_dropped = packet.get(
            "dropped_diagnostic_helper_only_next_actions",
            [],
        )
        if not isinstance(existing_dropped, list):
            existing_dropped = []
        packet["dropped_diagnostic_helper_only_next_actions"] = [
            *existing_dropped,
            *dropped_actions,
        ]
    findings = packet.get("critic_findings", [])
    if not isinstance(findings, list):
        findings = []
    findings.append(
        {
            "critic": "local_formalizer_packet_normalizer",
            "finding": (
                "Diagnostic-helper bridge mode has no source-to-bridge request "
                "shortcut; recorded an explicit non-proof metadata blocker and "
                "removed helper-only executable next_actions when present."
            ),
            "proof_evidence_status": (
                "DIAGNOSTIC_HELPER_BRIDGE_BLOCKER_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["critic_findings"] = findings


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


def _compact_formal_blocker_resource_requests(rows: Any) -> list[dict[str, Any]]:
    return _compact_rows(
        [
            row
            for row in rows or []
            if isinstance(row, Mapping)
        ],
        keys=(
            "request_id",
            "source",
            "blocker_kind",
            "blocker",
            "next_owner",
            "target_ids",
            "target_id",
            "target_names",
            "target_name",
            "target_theorem_name",
            "target_lean_declaration",
            "placeholder_symbol",
            "candidate_artifact_path",
            "definition_only_candidate_artifact_path",
            "source_candidate_artifact_path",
            "adapter_candidate_artifact_path",
            "adapter_candidate_artifact_paths",
            "premise_candidate_artifact_path",
            "proof_body_candidate_artifact_path",
            "runtime_queue_status",
            "proof_body_gate_status",
            "failure_classification",
            "unavailable_import",
            "unavailable_import_exact",
            "unknown_identifier",
            "missing_formal_symbols",
            "typeclass_blockers",
            "formal_source_queries",
            "source_lookup_hits",
            "recommended_tools",
            "recommended_repair_tasks",
            "semantic_alignment_blockers",
            "semantic_definition_risks",
            "local_definition_lean_checked",
            "local_definition_lean_compiled",
            "semantic_definition_typecheck_evidence_status",
            "source_theorem_exact_semantic_definition_typechecked_candidate",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ),
        limit=8,
    )


def _exact_semantic_repair_diagnostics_by_placeholder(
    *feedback_payloads: Any,
) -> dict[tuple[str, str], Mapping[str, Any]]:
    diagnostics_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for payload in feedback_payloads:
        if not isinstance(payload, Mapping):
            continue
        exact_feedback = payload.get(
            "source_theorem_exact_semantic_definition_repair_feedback",
            {},
        )
        if isinstance(exact_feedback, Mapping):
            diagnostics = exact_feedback.get("diagnostics", [])
        else:
            diagnostics = []
        work_order_feedback = payload.get(
            "runtime_exact_semantic_definition_work_order_feedback",
            {},
        )
        work_orders = (
            work_order_feedback.get("work_orders", [])
            if isinstance(work_order_feedback, Mapping)
            else []
        )
        for row in list(diagnostics or []) + list(work_orders or []):
            if not isinstance(row, Mapping):
                continue
            placeholder = str(row.get("placeholder_symbol", "") or "").strip()
            if not placeholder:
                continue
            target_ids = [
                str(value).strip()
                for value in row.get("target_ids", []) or []
                if str(value).strip()
            ]
            target_names = [
                str(value).strip()
                for value in row.get("target_names", []) or []
                if str(value).strip()
            ]
            target_name = str(
                row.get("target_theorem_name", "") or row.get("target_name", "") or ""
            ).strip()
            targets = (
                target_ids
                or target_names
                or ([target_name] if target_name else [""])
            )
            for target in targets:
                diagnostics_by_key.setdefault((placeholder, target), row)
    return diagnostics_by_key


def _formal_blocker_resource_requests_with_exact_semantic_artifacts(
    rows: Any,
    *,
    feedback: Mapping[str, Any],
    input_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(rows, list | tuple):
        return []
    diagnostics_by_key = _exact_semantic_repair_diagnostics_by_placeholder(
        feedback,
        input_summary,
    )
    hydrated: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        copied = dict(row)
        placeholder = str(copied.get("placeholder_symbol", "") or "").strip()
        if not placeholder:
            hydrated.append(copied)
            continue
        target_ids = [
            str(value).strip()
            for value in copied.get("target_ids", []) or []
            if str(value).strip()
        ]
        target_names = [
            str(value).strip()
            for value in copied.get("target_names", []) or []
            if str(value).strip()
        ]
        target_name = str(
            copied.get("target_theorem_name", "")
            or copied.get("target_name", "")
            or ""
        ).strip()
        targets = (
            target_ids
            or target_names
            or ([target_name] if target_name else [""])
        )
        diagnostic = next(
            (
                diagnostics_by_key.get((placeholder, target))
                for target in targets
                if diagnostics_by_key.get((placeholder, target))
            ),
            diagnostics_by_key.get((placeholder, "")),
        )
        if not isinstance(diagnostic, Mapping):
            hydrated.append(copied)
            continue
        definition_only_path = str(
            diagnostic.get("definition_only_candidate_artifact_path", "") or ""
        ).strip()
        candidate_path = str(
            diagnostic.get("candidate_artifact_path", "")
            or diagnostic.get("synthesized_candidate_artifact_path", "")
            or definition_only_path
            or ""
        ).strip()
        for key, value in (
            ("definition_only_candidate_artifact_path", definition_only_path),
            ("candidate_artifact_path", candidate_path),
            (
                "semantic_definition_typecheck_evidence_status",
                diagnostic.get("semantic_definition_typecheck_evidence_status"),
            ),
            (
                "local_definition_lean_checked",
                diagnostic.get("local_definition_lean_checked"),
            ),
            (
                "local_definition_lean_compiled",
                diagnostic.get("local_definition_lean_compiled"),
            ),
            (
                "source_theorem_exact_semantic_definition_typechecked_candidate",
                diagnostic.get(
                    "source_theorem_exact_semantic_definition_typechecked_candidate"
                ),
            ),
        ):
            if copied.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
                copied[key] = value
        if (
            copied.get("proof_evidence_status") in (None, "")
            and definition_only_path
        ):
            copied["proof_evidence_status"] = (
                "FORMAL_BLOCKER_RESOURCE_REQUEST_NOT_PROOF_EVIDENCE"
            )
        hydrated.append(copied)
    return hydrated


def _compact_mapping(row: Mapping[str, Any], *, keys: tuple[str, ...]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key in keys:
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


_SOURCE_TO_BRIDGE_POLICY_LINEAGE_KEYS = (
    "premise_semantic_dependency_source",
    "source_to_bridge_policy_pack_ids",
    "source_to_bridge_policy_ids",
    "source_to_bridge_policy_scopes",
    "source_to_bridge_policy_required_anchor_names",
    "source_to_bridge_policy_dependency_requirements",
)


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
    lines = text.splitlines()
    theorem_start = 0
    for index, line in enumerate(lines):
        if re.search(r"\b(?:theorem|lemma)\s+[A-Za-z_][A-Za-z0-9_'.]*\b", line):
            theorem_start = max(0, index - 8)
            break
    return "\n".join(lines[theorem_start : theorem_start + max_lines])[:max_chars]


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
            "shared_adapter_instantiation_contract",
            "premise_candidate_declaration_name",
            "premise_candidate_artifact_path",
            "source_to_bridge_premise_candidate_artifact_path",
            "premise_derivation_candidate_skeleton_lean_source_excerpt",
            "premise_candidate_skeleton_lean_source_excerpt",
            "target_theorem_name",
            "target_lean_declaration",
            "required_formalizer_output_key",
            "required_candidate_fields",
            "candidate_contract",
            *_SOURCE_TO_BRIDGE_POLICY_LINEAGE_KEYS,
            "premise_semantic_dependency_requirements",
            "exact_source_theorem_binders",
            "premise_semantic_anchor_binders",
            "premise_semantic_anchor_binder_names",
            "required_semantic_anchor_reference_names",
            "semantic_anchor_reference_gate",
            "bridge_object_instantiation_policy",
            "adapter_object_names_requiring_source_instantiation",
            "proof_body_goal_context",
            "proof_body_goal_binder_names",
            "proof_body_goal_conclusion",
            "source_to_bridge_premise_goal_context",
            "source_to_bridge_premise_goal_binder_names",
            "source_to_bridge_premise_goal_conclusion",
            "forbidden_actions",
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
            "shared_adapter_instantiation_contract",
            "adapter_object_names_requiring_source_instantiation",
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
            "candidate_contract",
            *_SOURCE_TO_BRIDGE_POLICY_LINEAGE_KEYS,
            "exact_source_theorem_binders",
            "premise_semantic_anchor_binders",
            "premise_semantic_anchor_binder_names",
            "required_semantic_anchor_reference_names",
            "premise_semantic_dependency_requirements",
            "forbidden_actions",
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
                *_SOURCE_TO_BRIDGE_POLICY_LINEAGE_KEYS,
                "premise_semantic_dependency_requirements",
                "required_semantic_anchor_reference_names",
                "adapter_object_names_requiring_source_instantiation",
                "proof_body_goal_binder_names",
                "proof_body_goal_conclusion",
            ),
            limit=6,
        )
    return compact


def _source_to_bridge_candidate_request_shortcuts(
    proof_memory_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Surface exact premise request metadata where the model can copy it."""

    shortcuts: list[dict[str, Any]] = []
    seen: set[str] = set()
    metadata_request_rows = proof_memory_summary.get(
        "source_to_bridge_metadata_authoring_candidate_requests",
        [],
    )
    diagnostics = [
        *(
            list(metadata_request_rows)
            if isinstance(metadata_request_rows, list | tuple)
            else []
        ),
        *(
            list(
                proof_memory_summary.get(
                    "source_to_bridge_premise_derivation_diagnostics", []
                )
            )
            if isinstance(
                proof_memory_summary.get(
                    "source_to_bridge_premise_derivation_diagnostics", []
                ),
                list | tuple,
            )
            else []
        ),
    ]
    if not isinstance(diagnostics, list | tuple):
        return shortcuts
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, Mapping):
            continue
        grouped_request = diagnostic.get(
            "source_to_bridge_grouped_premise_derivation_candidate_request", {}
        )
        if isinstance(grouped_request, Mapping) and grouped_request:
            grouped_request = dict(grouped_request)
            for lineage_key in _SOURCE_TO_BRIDGE_POLICY_LINEAGE_KEYS:
                if grouped_request.get(lineage_key) in (None, "", [], {}) and (
                    diagnostic.get(lineage_key) not in (None, "", [], {})
                ):
                    grouped_request[lineage_key] = diagnostic[lineage_key]
            grouped_id = str(
                diagnostic.get(
                    "source_to_bridge_grouped_premise_derivation_candidate_request_id",
                    "",
                )
                or grouped_request.get("grouped_candidate_request_id", "")
                or ""
            ).strip()
            key = f"group:{grouped_id or stable_hash(grouped_request)[:12]}"
            if key not in seen:
                seen.add(key)
                shortcuts.append(
                    {
                        "copy_this_grouped_request_id": grouped_id,
                        "copy_this_grouped_request": (
                            _compact_grouped_premise_derivation_candidate_request(
                                grouped_request
                            )
                        ),
                        "premise_names": list(
                            grouped_request.get("premise_names", [])
                            or diagnostic.get("premise_names", [])
                            or []
                        ),
                        "required_semantic_anchor_reference_names": list(
                            grouped_request.get(
                                "required_semantic_anchor_reference_names",
                                [],
                            )
                            or diagnostic.get(
                                "required_semantic_anchor_reference_names",
                                [],
                            )
                            or []
                        ),
                        "adapter_object_names_requiring_source_instantiation": list(
                            grouped_request.get(
                                "adapter_object_names_requiring_source_instantiation",
                                [],
                            )
                            or diagnostic.get(
                                "adapter_object_names_requiring_source_instantiation",
                                [],
                            )
                            or []
                        ),
                    }
                )
        candidate_request = diagnostic.get(
            "source_to_bridge_premise_derivation_candidate_request", {}
        )
        if not candidate_request and str(
            diagnostic.get("candidate_request_id", "") or ""
        ).strip():
            candidate_request = diagnostic
        if isinstance(candidate_request, Mapping) and candidate_request:
            candidate_request = dict(candidate_request)
            ensure_premise_candidate_declaration_name(candidate_request)
            for lineage_key in _SOURCE_TO_BRIDGE_POLICY_LINEAGE_KEYS:
                if candidate_request.get(lineage_key) in (None, "", [], {}) and (
                    diagnostic.get(lineage_key) not in (None, "", [], {})
                ):
                    candidate_request[lineage_key] = diagnostic[lineage_key]
            request_id = str(
                diagnostic.get(
                    "source_to_bridge_premise_derivation_candidate_request_id",
                    "",
                )
                or diagnostic.get("candidate_request_id", "")
                or candidate_request.get("candidate_request_id", "")
                or ""
            ).strip()
            key = f"single:{request_id or stable_hash(candidate_request)[:12]}"
            if key in seen:
                continue
            seen.add(key)
            shortcuts.append(
                {
                    "copy_this_candidate_request_id": request_id,
                    "copy_this_candidate_request": (
                        _compact_premise_derivation_candidate_request(
                            candidate_request
                        )
                    ),
                    "premise_name": str(
                        candidate_request.get("premise_name", "")
                        or diagnostic.get("premise_name", "")
                        or ""
                    ),
                    "premise_target_type": str(
                        candidate_request.get("premise_target_type", "")
                        or diagnostic.get("premise_target_type", "")
                        or ""
                    ),
                    "premise_target_source": str(
                        candidate_request.get("premise_target_source", "")
                        or diagnostic.get("premise_target_source", "")
                        or ""
                    ),
                    "proof_body_goal_binder_names": list(
                        candidate_request.get(
                            "proof_body_goal_binder_names",
                            [],
                        )
                        or candidate_request.get(
                            "source_to_bridge_premise_goal_binder_names",
                            [],
                        )
                        or diagnostic.get("proof_body_goal_binder_names", [])
                        or diagnostic.get(
                            "source_to_bridge_premise_goal_binder_names",
                            [],
                        )
                        or []
                    ),
                    "proof_body_goal_conclusion": str(
                        candidate_request.get("proof_body_goal_conclusion", "")
                        or candidate_request.get(
                            "source_to_bridge_premise_goal_conclusion",
                            "",
                        )
                        or diagnostic.get("proof_body_goal_conclusion", "")
                        or diagnostic.get(
                            "source_to_bridge_premise_goal_conclusion",
                            "",
                        )
                        or ""
                    ),
                    "premise_candidate_declaration_name": str(
                        candidate_request.get("premise_candidate_declaration_name", "")
                        or diagnostic.get("premise_candidate_declaration_name", "")
                        or diagnostic.get(
                            "source_to_bridge_premise_candidate_declaration_name",
                            "",
                        )
                        or ""
                    ),
                    "premise_candidate_artifact_path": (
                        _source_to_bridge_premise_candidate_artifact_path(
                            candidate_request
                        )
                        or _source_to_bridge_premise_candidate_artifact_path(
                            diagnostic
                        )
                    ),
                    "premise_derivation_candidate_skeleton_lean_source_excerpt": (
                        _source_to_bridge_candidate_skeleton_lean_source_excerpt(
                            candidate_request
                        )
                        or _source_to_bridge_candidate_skeleton_lean_source_excerpt(
                            diagnostic
                        )
                    ),
                    "required_semantic_anchor_reference_names": list(
                        candidate_request.get(
                            "required_semantic_anchor_reference_names",
                            [],
                        )
                        or diagnostic.get(
                            "required_semantic_anchor_reference_names",
                            [],
                        )
                        or []
                    ),
                    "adapter_object_names_requiring_source_instantiation": list(
                        candidate_request.get(
                            "adapter_object_names_requiring_source_instantiation",
                            [],
                        )
                        or diagnostic.get(
                            "adapter_object_names_requiring_source_instantiation",
                            [],
                        )
                        or []
                    ),
                }
            )
        if len(shortcuts) >= 6:
            break
    return shortcuts[:6]


def _enrich_source_to_bridge_candidates_from_memory(
    packet: dict[str, Any],
    proof_memory_summary: Mapping[str, Any],
) -> None:
    """Attach source-binding request metadata to matching generated candidates."""

    shortcuts = _source_to_bridge_candidate_request_shortcuts(
        _compact_proof_bank_runtime_memory_summary(proof_memory_summary)
    )
    _enrich_source_to_bridge_candidates_from_shortcuts(
        packet,
        shortcuts,
        autofill_source="runtime_memory",
    )


def _enrich_source_to_bridge_candidates_from_packet_requests(
    packet: dict[str, Any],
) -> None:
    """Allow a packet to emit request metadata and the executable candidate together."""

    request_rows = packet.get(
        "source_to_bridge_premise_derivation_candidate_requests", []
    )
    if not isinstance(request_rows, list | tuple) or not request_rows:
        return
    shortcuts = _source_to_bridge_candidate_request_shortcuts(
        {"source_to_bridge_metadata_authoring_candidate_requests": list(request_rows)}
    )
    _enrich_source_to_bridge_candidates_from_shortcuts(
        packet,
        shortcuts,
        autofill_source="same_packet_candidate_request",
    )


def _enrich_source_to_bridge_candidates_from_shortcuts(
    packet: dict[str, Any],
    shortcuts: Sequence[Mapping[str, Any]],
    *,
    autofill_source: str,
) -> None:
    candidates = packet.get("source_to_bridge_premise_derivation_candidates", [])
    if not isinstance(candidates, list) or not shortcuts:
        return
    single_by_premise: dict[str, Mapping[str, Any]] = {}
    grouped_requests: list[Mapping[str, Any]] = []
    single_request_shortcuts: list[Mapping[str, Any]] = []
    for shortcut in shortcuts:
        if shortcut.get("copy_this_candidate_request"):
            single_request_shortcuts.append(shortcut)
            premise = str(shortcut.get("premise_name", "") or "").strip()
            if premise:
                single_by_premise[premise] = shortcut
        if shortcut.get("copy_this_grouped_request"):
            grouped_requests.append(shortcut)
    candidate_dicts = [candidate for candidate in candidates if isinstance(candidate, dict)]
    unbound_candidates_before_autofill = [
        candidate
        for candidate in candidate_dicts
        if not _source_to_bridge_candidate_has_copied_request_contract(candidate)
    ]
    allow_single_request_single_candidate_fallback = bool(
        len(unbound_candidates_before_autofill) == 1
        and len(single_request_shortcuts) == 1
        and not grouped_requests
    )
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if _source_to_bridge_candidate_has_copied_request_contract(candidate):
            continue
        premise_names = [
            str(value).strip()
            for value in candidate.get("premise_names", []) or []
            if str(value).strip()
        ]
        premise_name = str(candidate.get("premise_name", "") or "").strip()
        if premise_name and not premise_names:
            premise_names = [premise_name]
        matched_group = None
        for shortcut in grouped_requests:
            group_names = {
                str(value).strip()
                for value in shortcut.get("premise_names", []) or []
                if str(value).strip()
            }
            if group_names and set(premise_names).issubset(group_names):
                matched_group = shortcut
                break
        if matched_group is not None:
            if matched_group.get("copy_this_grouped_request_id"):
                candidate[
                    "source_to_bridge_grouped_premise_derivation_candidate_request_id"
                ] = matched_group["copy_this_grouped_request_id"]
            candidate[
                "source_to_bridge_grouped_premise_derivation_candidate_request"
            ] = matched_group["copy_this_grouped_request"]
            if isinstance(matched_group.get("copy_this_grouped_request"), Mapping):
                _copy_missing_candidate_metadata(
                    candidate,
                    matched_group["copy_this_grouped_request"],
                )
            _copy_missing_candidate_metadata(candidate, matched_group)
            _mark_source_to_bridge_candidate_metadata_autofill(
                candidate,
                autofill_source=autofill_source,
                autofill_mode="premise_group_match",
            )
            continue
        if premise_name and premise_name in single_by_premise:
            shortcut = single_by_premise[premise_name]
            _attach_single_source_to_bridge_request_shortcut(
                candidate,
                shortcut,
                autofill_source=autofill_source,
            )
            continue
        if (
            allow_single_request_single_candidate_fallback
            and candidate is unbound_candidates_before_autofill[0]
        ):
            _attach_single_source_to_bridge_request_shortcut(
                candidate,
                single_request_shortcuts[0],
                align_premise_name=True,
                autofill_mode="single_request_single_candidate_fallback",
                autofill_source=autofill_source,
            )


def _copy_missing_candidate_metadata(
    candidate: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    def merged_metadata_sequence(
        existing_values: Sequence[Any],
        source_values: Sequence[Any],
    ) -> list[Any]:
        merged: list[Any] = []
        seen: set[str] = set()
        for item in [*existing_values, *source_values]:
            key = json.dumps(item, sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged

    list_merge_keys = {
        "exact_source_theorem_binders",
        "premise_semantic_anchor_binders",
        "premise_semantic_anchor_binder_names",
        "required_semantic_anchor_reference_names",
        "adapter_object_names_requiring_source_instantiation",
        "proof_body_goal_binder_names",
        "source_to_bridge_premise_goal_binder_names",
        "premise_candidate_declaration_names",
    }
    for key in (
        "exact_source_theorem_binders",
        "premise_semantic_anchor_binders",
        "premise_semantic_anchor_binder_names",
        "required_semantic_anchor_reference_names",
        "semantic_anchor_reference_gate",
        "adapter_object_names_requiring_source_instantiation",
        "premise_target_type",
        "premise_target_source",
        "source_to_bridge_premise_target_type",
        "premise_candidate_declaration_name",
        "source_to_bridge_premise_candidate_declaration_name",
        "premise_candidate_artifact_path",
        "source_to_bridge_premise_candidate_artifact_path",
        "premise_derivation_candidate_skeleton_lean_source_excerpt",
        "premise_candidate_skeleton_lean_source_excerpt",
        "proof_body_goal_context",
        "proof_body_goal_binder_names",
        "proof_body_goal_conclusion",
        "source_to_bridge_premise_goal_context",
        "source_to_bridge_premise_goal_binder_names",
        "source_to_bridge_premise_goal_conclusion",
        "premise_candidate_declaration_names",
        "target_theorem_name",
        "target_lean_declaration",
        "candidate_contract",
    ):
        values = source.get(key, [])
        if candidate.get(key) in (None, "", [], {}):
            if values not in (None, "", [], {}):
                if isinstance(values, list | tuple | set):
                    candidate[key] = list(values)
                elif isinstance(values, Mapping):
                    candidate[key] = dict(values)
                else:
                    candidate[key] = values
        elif key in list_merge_keys and isinstance(values, list | tuple | set):
            existing = candidate.get(key, [])
            if isinstance(existing, list | tuple | set):
                candidate[key] = merged_metadata_sequence(
                    list(existing),
                    list(values),
                )


def _attach_single_source_to_bridge_request_shortcut(
    candidate: dict[str, Any],
    shortcut: Mapping[str, Any],
    *,
    align_premise_name: bool = False,
    autofill_mode: str = "premise_name_match",
    autofill_source: str = "runtime_memory",
) -> None:
    if shortcut.get("copy_this_candidate_request_id"):
        candidate["source_to_bridge_premise_derivation_candidate_request_id"] = (
            shortcut["copy_this_candidate_request_id"]
        )
    request = shortcut.get("copy_this_candidate_request", {})
    if isinstance(request, Mapping):
        candidate["source_to_bridge_premise_derivation_candidate_request"] = dict(
            request
        )
        _copy_missing_candidate_metadata(candidate, request)
    _copy_missing_candidate_metadata(candidate, shortcut)
    request_premise_name = str(shortcut.get("premise_name", "") or "").strip()
    current_premise_name = str(candidate.get("premise_name", "") or "").strip()
    if align_premise_name and request_premise_name:
        if current_premise_name and current_premise_name != request_premise_name:
            candidate["model_premise_name_before_runtime_autofill"] = (
                current_premise_name
            )
        candidate["premise_name"] = request_premise_name
        premise_names = [
            str(value).strip()
            for value in candidate.get("premise_names", []) or []
            if str(value).strip()
        ]
        candidate["premise_names"] = list(
            dict.fromkeys([request_premise_name, *premise_names])
        )
    _mark_source_to_bridge_candidate_metadata_autofill(
        candidate,
        autofill_source=autofill_source,
        autofill_mode=autofill_mode,
    )


def _mark_source_to_bridge_candidate_metadata_autofill(
    candidate: dict[str, Any],
    *,
    autofill_source: str,
    autofill_mode: str,
) -> None:
    if autofill_source == "same_packet_candidate_request":
        candidate[
            "source_binding_metadata_autofilled_from_packet_candidate_request"
        ] = True
    else:
        candidate["source_binding_metadata_autofilled_from_runtime_memory"] = True
    candidate["source_binding_metadata_autofill_source"] = autofill_source
    candidate["source_binding_metadata_autofill_mode"] = autofill_mode


def _feedback_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _blocked_import_prefixes_for_prompt(
    local_lean_repair_contract: Mapping[str, Any],
) -> list[str]:
    """Return import prefixes that should remain hard-blocked in prompt text."""

    blocked_import_prefixes = [
        str(value).strip()
        for value in local_lean_repair_contract.get("blocked_import_prefixes", []) or []
        if str(value).strip()
    ]
    if local_lean_repair_contract.get("mathlib_import_unavailable"):
        return [value for value in blocked_import_prefixes if value != "Mathlib"]
    return blocked_import_prefixes


def _formalizer_mode_specific_instructions(
    proof_memory_summary: Mapping[str, Any],
    runtime_environment_feedback: Mapping[str, Any],
) -> list[str]:
    instructions: list[str] = []
    mode = str(proof_memory_summary.get("recommended_formalizer_target_mode", "") or "")
    repeated_syntax_fail_closed_active = (
        _feedback_has_repeated_syntax_failure_contract(runtime_environment_feedback)
    )
    integration_action = str(
        proof_memory_summary.get("recommended_source_theorem_integration_action", "")
        or ""
    )
    feedback_failure = str(
        runtime_environment_feedback.get("failure_classification", "") or ""
    )
    repair_owner_agent = str(
        runtime_environment_feedback.get("repair_owner_agent", "") or ""
    )
    proofengineer_repair_context = runtime_environment_feedback.get(
        "proofengineer_repair_context",
        {},
    )
    initial_formal_source_grounding = (
        _is_initial_formal_source_grounding_context(
            proofengineer_repair_context
        )
    )
    formal_source_grounding_available = bool(
        isinstance(proofengineer_repair_context, Mapping)
        and proofengineer_repair_context.get("formal_source_grounding_hits")
    )
    source_theorem_promotion_generation_request = (
        runtime_environment_feedback.get(
            "source_theorem_promotion_generation_request",
            {},
        )
        if isinstance(
            runtime_environment_feedback.get(
                "source_theorem_promotion_generation_request",
                {},
            ),
            Mapping,
        )
        else {}
    )
    formalization_gap_planner_action_work_order = (
        runtime_environment_feedback.get(
            "formalization_gap_planner_action_work_order",
            {},
        )
        if isinstance(
            runtime_environment_feedback.get(
                "formalization_gap_planner_action_work_order",
                {},
            ),
            Mapping,
        )
        else {}
    )
    feedback_input_summary = (
        runtime_environment_feedback.get("input_summary", {})
        if isinstance(runtime_environment_feedback.get("input_summary", {}), Mapping)
        else {}
    )
    source_to_bridge_request_shortcuts = (
        _source_to_bridge_candidate_request_shortcuts(proof_memory_summary)
    )
    if str(
        runtime_environment_feedback.get("feedback_type", "") or ""
    ).strip() == "formal_target_semantic_review_feedback":
        instructions.append(
            "An independent formal-target semantic review is active. Treat its "
            "dimension reviews, findings, and repair instructions as binding repair "
            "feedback for the exact candidate. Preserve the source theorem target, "
            "address the cited defect, and leave closure open until the revised exact "
            "artifact is independently reviewed and kernel checked."
        )
    if formalization_gap_planner_action_work_order:
        instructions.append(
            "A contract-valid FormalizationGapPlanner action work order is active. "
            "Treat its formal_attempt_queue, planner_next_actions, and search_requests "
            "as prioritized, immutable orchestration input. Use the available formal "
            "source retriever/RAG context and model reasoning to materialize concrete "
            "source-bound formal_targets for executable attempts, then let local "
            "Lean/LSP diagnostics drive revision. Preserve the requested theorem and "
            "declaration lineage; return a typed missing dependency when an action "
            "cannot yet be materialized. Do not copy planner prose as a proof, invent "
            "kernel success, restart statistical theory, or silently substitute a "
            "weaker target. Consume the work order verbatim from "
            "runtime_environment_feedback.formalization_gap_planner_action_work_order."
        )
    if source_theorem_promotion_generation_request:
        promotion_target_rows = [
            row
            for row in source_theorem_promotion_generation_request.get(
                "target_rows",
                [],
            )
            or []
            if isinstance(row, Mapping)
        ]
        promotion_targets = [
            {
                "source_formal_target_id": str(
                    row.get("source_formal_target_id", "") or ""
                ),
                "target_lean_declaration": str(
                    row.get("target_lean_declaration", "") or ""
                ),
                "target_ids": [
                    str(value)
                    for value in row.get("target_ids", []) or []
                    if str(value)
                ],
                "source_theorem_target_provenance": dict(
                    row.get("source_theorem_target_provenance", {}) or {}
                )
                if isinstance(
                    row.get("source_theorem_target_provenance", {}), Mapping
                )
                else {},
            }
            for row in promotion_target_rows
        ]
        instructions.append(
            "Typed source-theorem promotion generation is active. Emit exactly one "
            "executable formal_targets entry for every row in "
            "runtime_environment_feedback.source_theorem_promotion_generation_request."
            "target_rows. Preserve each source_formal_target_id as formal_targets.id, "
            "preserve target_lean_declaration in both the target and "
            "source_theorem_target_provenance, preserve the requested target ids in "
            "source_theorem_target_provenance.source_theorem_goal_id when a single "
            "goal is supplied, set source_theorem_target_known=true and "
            "expected_status=NEEDS_KERNEL_CHECK, and emit a complete nonempty exact "
            "Lean declaration in lean_statement_sketch. Use signed formal RAG and the "
            "available model/prover reasoning. Do not emit a route probe, weaken the "
            "target, rename the declaration, substitute a helper theorem, or treat "
            "this generation request as proof evidence. The unchanged candidate will "
            "be passed to ExactSourceTheoremProofBodyExecutor and local Lean/AXLE. "
            "Requested target contract: "
            + json.dumps(promotion_targets, sort_keys=True, default=str)
        )
    if any(
        shortcut.get("premise_candidate_artifact_path")
            or shortcut.get("premise_derivation_candidate_skeleton_lean_source_excerpt")
            or (
                isinstance(shortcut.get("copy_this_candidate_request", {}), Mapping)
                and (
                    shortcut.get("copy_this_candidate_request", {}).get(
                        "premise_candidate_artifact_path"
                    )
                    or shortcut.get("copy_this_candidate_request", {}).get(
                        "premise_derivation_candidate_skeleton_lean_source_excerpt"
                    )
                )
            )
        for shortcut in source_to_bridge_request_shortcuts
    ):
        instructions.append(
            "Source-to-bridge skeleton guidance is available: when a copied "
            "candidate request includes premise_candidate_artifact_path or "
            "premise_derivation_candidate_skeleton_lean_source_excerpt, reuse that "
            "generated theorem name/header as the executable Lean envelope and "
            "replace only the proof body or explicitly report the missing semantic "
            "primitive as FORMAL_GAP. Do not invent a different binder list, do not "
            "turn the target premise into an assumption, and do not treat the "
            "skeleton excerpt itself as proof evidence."
        )
    formal_blocker_resource_requests = _formal_blocker_resource_requests_with_exact_semantic_artifacts(
        [
            row
            for row in runtime_environment_feedback.get(
                "formal_blocker_resource_requests",
                [],
            )
            or []
            if isinstance(row, Mapping)
        ],
        feedback=runtime_environment_feedback,
        input_summary=feedback_input_summary,
    )
    high_priority_agenda = [
        row
        for row in runtime_environment_feedback.get("high_priority_agenda", []) or []
        if isinstance(row, Mapping)
    ]
    formal_gap_next_action_agenda_rows = [
        row
        for row in high_priority_agenda
        if str(row.get("id", "") or "").strip()
        in {
            "formal_gap:proof_bank_expansion",
            "formal_gap:gap_planner_handoff",
        }
        or str(row.get("trigger", "") or "").strip()
        in {
            "FORMAL_GAP",
            "FORMAL_GAP_WITH_RUNTIME_GAP_PLANNER_SEED",
        }
    ]
    theory_trace_downstream_alignment_feedback = (
        _theory_trace_downstream_alignment_feedback(runtime_environment_feedback)
    )
    if _feedback_requires_source_grounded_exact_semantic_authoring_handoff(
        runtime_environment_feedback
    ):
        instructions.append(
            "Source-grounded exact semantic-definition authoring handoff is required: "
            "route the next exact semantic-definition work through source theorem "
            "binders, required anchor bindings, complete required anchors, "
            "source-anchor context, and Lean authoring environment binders. If those "
            "anchors are unavailable, emit a machine-routable source lookup or "
            "formal-gap work order instead of an empty-shell definition request. "
            "This handoff is runtime capability evidence for downstream Lean/RAG/"
            "ProofEngineer workers, not theorem proof evidence."
        )
    if _feedback_requires_exact_semantic_candidate_materialization_contract(
        runtime_environment_feedback
    ):
        instructions.append(
            "Exact semantic-definition candidate materialization feedback contract is "
            "required: when exact semantic-definition authoring is used, emit "
            "definition-only candidate packets with stable candidate ids, Lean "
            "declaration names, source-anchor provenance, and enough binder context "
            "for the candidate materializer to create materialized Lean repair tasks. "
            "Route those tasks through local Lean/AXLE diagnostics and persist "
            "runtime learning feedback rows back to Formalizer/ProofEngineer. If the "
            "packet cannot be materialized, emit a machine-routable formal-gap or "
            "source-lookup work order naming the missing API, import, binder, anchor, "
            "or semantic definition. This is runtime repair-loop evidence, not "
            "theorem proof evidence."
        )
    materialization_agenda_rows = [
        row
        for row in high_priority_agenda
        if str(row.get("trigger", "") or "")
        == "EXACT_SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED"
        or str(row.get("recommended_formalizer_target_mode", "") or "")
        == "source_theorem_exact_candidate_materialization_required"
        or str(row.get("id", "") or "")
        == "formal_gap:source_theorem_candidate_materialization"
    ]
    materialization_resource_requests = [
        row
        for row in formal_blocker_resource_requests
        if str(row.get("blocker_kind", "") or "")
        == "SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED"
    ]
    source_theorem_candidate_materialization_required = bool(
        proof_memory_summary.get("source_theorem_candidate_materialization_required")
        or mode == "source_theorem_exact_candidate_materialization_required"
        or materialization_agenda_rows
        or materialization_resource_requests
    )
    exact_semantic_definition_gate_active = (
        _source_theorem_exact_semantic_definition_gate_active(
            environment_feedback=runtime_environment_feedback,
            proof_bank_runtime_memory_summary=proof_memory_summary,
        )
    )
    if (
        source_theorem_candidate_materialization_required
        and exact_semantic_definition_gate_active
    ):
        source_theorem_candidate_materialization_required = False
        instructions.append(
            "Exact semantic-definition gate override: suspend exact source-theorem "
            "candidate materialization for this packet because reviewed/imported "
            "semantic definitions are still required before proof-body or signature "
            "work. Emit the source theorem as expected_status=FORMAL_GAP with an "
            "empty lean_statement_sketch, then route executable work only through "
            "source_to_bridge_premise_derivation_candidates, exact semantic-definition "
            "candidate requests, or other support channels with copied provenance. "
            "Do not broaden this into theory revision and do not claim proof evidence."
        )
    if source_theorem_candidate_materialization_required and repeated_syntax_fail_closed_active:
        instructions.append(
            "Repeated Lean compiler feedback is active: keep exact source-theorem "
            "candidate materialization enabled, consume the verbatim parser/LSP "
            "diagnostics, generate a revised candidate, and rerun Lean. Do not replay "
            "an identical failed artifact. Valid Lean syntax, including Unicode and "
            "pipeline notation, is allowed when the configured Lean environment "
            "accepts it. Emit FORMAL_GAP only when the dependency or semantics truly "
            "cannot be supplied; compiler feedback is not proof evidence."
        )
    source_theorem_proof_body_adapter_feedback = (
        runtime_environment_feedback.get(
            "source_theorem_proof_body_adapter_feedback",
            {},
        )
        if isinstance(
            runtime_environment_feedback.get(
                "source_theorem_proof_body_adapter_feedback",
                {},
            ),
            Mapping,
        )
        else {}
    )
    if (
        repair_owner_agent == "ProofEngineer"
        or (proofengineer_repair_context and not initial_formal_source_grounding)
    ):
        instructions.append(
            "ProofEngineer repair loop is active: consume "
            "runtime_environment_feedback.proofengineer_repair_context, including "
            "the exact materialized Lean artifact paths when available, registered "
            "formal-subclaim statements and lineage, local Lean/proof-state "
            "diagnostics, residual goals, and available prover/search tools. Do not "
            "treat this as a fresh "
            "Formalizer proposal or a human-debugged patch; return a bounded "
            "ProofEngineer repair candidate, a smaller lemma split, or an explicit "
            "formal blocker that can be rerun by local Lean/AXLE. Prefer the "
            "prover loop lean_diagnostic_messages -> lean_goal -> "
            "lean_state_search/proof_search -> lean_multi_attempt -> "
            "local_lean_or_axle_rerun when those tools are available. Generate the "
            "Lean repair with model reasoning over that context; there is no "
            "runtime-authored assumption/simp tactic fallback."
        )
        if (
            isinstance(proofengineer_repair_context, Mapping)
            and proofengineer_repair_context.get("proof_state_trace_rag")
        ):
            instructions.append(
                "AI4SLT proof-state transitions are available in "
                "proofengineer_repair_context.proof_state_trace_rag. Use them only "
                "as analogies between a prior local goal, one tactic action, and its "
                "next state. Do not copy them as templates or treat them as proof "
                "evidence: check premise visibility and current indexed signatures, "
                "choose the smallest action justified by the present goal and "
                "diagnostics, then rerun the exact current artifact through local "
                "Lean/AXLE. If the same obstruction persists, reconsider the target "
                "statement, assumptions, or lemma decomposition rather than replaying "
                "an unchanged tactic."
            )
        if (
            isinstance(proofengineer_repair_context, Mapping)
            and proofengineer_repair_context.get("external_proof_search_result")
        ):
            instructions.append(
                "External proof-search feedback is available in "
                "proofengineer_repair_context.external_proof_search_result. Treat "
                "source_theorem_candidate_proof_bodies as whole-body proposals for "
                "the exact target declaration and verified_support_assets as candidate "
                "dependencies. When exact_candidate_rerun is present, repair from its "
                "local Lean precheck/diagnostics instead of asking a human to edit the "
                "artifact. Do not copy a nested residual goal into a weaker theorem, "
                "and do not treat the provider report as final proof evidence. Preserve "
                "target_theorem_statement exactly, emit the complete declaration, and "
                "let the AI Statistician local Lean/AXLE gate rerun it."
            )
    if formal_source_grounding_available:
        instructions.append(
            "Formal-source grounding hits are available: use qualified names and "
            "premise_declaration_outlines in dependency order; use "
            "nearby_declaration_outlines only as bounded fallback. Names, citations, "
            "and the source architecture route are orientation, not authority. "
            "Revalidate every selection in the exact local Lean/AXLE project; emit "
            "FORMAL_GAP when the required API is unavailable."
        )
    if formal_blocker_resource_requests:
        instructions.append(
            "Formal blocker resource requests are active: consume "
            "runtime_environment_feedback.formal_blocker_resource_requests as typed "
            "retrieval/prover work items. For each blocker, use formal-source retrieval, "
            "proof search, Lean/LSP diagnostics, or local Lean/AXLE to identify a verified "
            "declaration/import or a smaller semantic primitive. Do not emit an executable "
            "Lean candidate that reuses an unresolved API, import, semantic definition, or "
            "proof-search blocker; if the request cannot be resolved, keep the affected "
            "source theorem as FORMAL_GAP and name the exact missing resource."
        )
        exact_semantic_artifact_rows = [
            row
            for row in formal_blocker_resource_requests
            if (
                str(row.get("definition_only_candidate_artifact_path", "") or "").strip()
                or str(row.get("candidate_artifact_path", "") or "").strip()
            )
            and (
                "exact_semantic" in str(row.get("blocker_kind", "") or "").lower()
                or "exact_semantic" in str(row.get("source", "") or "").lower()
                or str(row.get("proof_body_gate_status", "") or "").strip()
                == "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY"
            )
        ][:5]
        if exact_semantic_artifact_rows:
            artifact_clauses: list[str] = []
            for row in exact_semantic_artifact_rows:
                placeholder = str(row.get("placeholder_symbol", "") or "").strip()
                artifact_path = str(
                    row.get("definition_only_candidate_artifact_path", "")
                    or row.get("candidate_artifact_path", "")
                    or ""
                ).strip()
                if placeholder and artifact_path:
                    artifact_clauses.append(f"{placeholder}: {artifact_path}")
            artifact_clause = (
                " Artifact(s): " + "; ".join(artifact_clauses) + "."
                if artifact_clauses
                else ""
            )
            instructions.append(
                "Exact semantic-definition blocker artifacts are available in "
                "formal_blocker_resource_requests: inspect and review the listed "
                "definition_only_candidate_artifact_path/candidate_artifact_path "
                "for each placeholder, then emit an exact semantic-definition "
                "repair/review target or a blocker that preserves the same artifact "
                "path and names the remaining semantic-review criterion. Do not "
                "start exact source-theorem proof-body search while "
                "proof_body_gate_status=SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY, "
                "and do not treat a locally compiled definition-only artifact as "
                "source-theorem Lean/kernel proof evidence."
                + artifact_clause
            )
    if theory_trace_downstream_alignment_feedback:
        instructions.append(
            "Runtime theory-trace downstream alignment feedback is active: treat "
            "runtime_environment_feedback.theory_trace_downstream_alignment_feedback "
            "as a hard proposal-provenance repair contract. The Formalizer/"
            "ProofEngineer packet must populate theory_trace_alignment with exact "
            "derivation, equation, assumption, and formalization anchors from the "
            "supplied TheoryDerivationPacket before any Lean target, proof-bank "
            "request, or gap taxonomy is evaluated. This alignment is not Lean/"
            "kernel proof evidence; every formal claim still needs local Lean/AXLE "
            "verification."
        )
    formal_gap_next_action_active = bool(
        proof_memory_summary.get("formal_gap_next_action_routing_active")
        or proof_memory_summary.get("formalization_gap_planner_handoff_required")
        or proof_memory_summary.get("formal_gap_proof_bank_expansion_required")
        or formal_gap_next_action_agenda_rows
    )
    if formal_gap_next_action_active:
        target_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "formal_gap_next_action_target_ids",
                [],
            )
            or []
            if str(value).strip()
        ][:6]
        for row in formal_gap_next_action_agenda_rows:
            target_ids.extend(
                str(value).strip()
                for value in row.get("target_ids", []) or []
                if str(value).strip()
            )
            target_id = str(row.get("target_id", "") or "").strip()
            if target_id:
                target_ids.append(target_id)
        target_ids = list(dict.fromkeys(target_ids))[:6]
        bridge_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "formalization_gap_planner_bridge_ids",
                [],
            )
            or []
            if str(value).strip()
        ][:4]
        for row in formal_gap_next_action_agenda_rows:
            bridge_ids.extend(
                str(value).strip()
                for value in (
                    row.get("supporting_formalization_gap_planner_bridge_ids", [])
                    or []
                )
                if str(value).strip()
            )
            bridge_id = str(
                row.get("formalization_gap_planner_bridge_id", "") or ""
            ).strip()
            if bridge_id:
                bridge_ids.append(bridge_id)
        bridge_ids = list(dict.fromkeys(bridge_ids))[:4]
        seed_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "formalization_gap_planner_standalone_seed_artifact_ids",
                [],
            )
            or []
            if str(value).strip()
        ][:4]
        for row in formal_gap_next_action_agenda_rows:
            seed_ids.extend(
                str(value).strip()
                for value in (
                    row.get("supporting_standalone_seed_artifact_ids", []) or []
                )
                if str(value).strip()
            )
            seed_id = str(row.get("standalone_seed_artifact_id", "") or "").strip()
            if seed_id:
                seed_ids.append(seed_id)
        seed_ids = list(dict.fromkeys(seed_ids))[:4]
        handoff_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "formalization_gap_planner_handoff_ids",
                [],
            )
            or []
            if str(value).strip()
        ][:4]
        for row in formal_gap_next_action_agenda_rows:
            handoff_ids.extend(
                str(value).strip()
                for value in (
                    row.get(
                        "supporting_formalization_gap_planner_handoff_ids",
                        [],
                    )
                    or []
                )
                if str(value).strip()
            )
            handoff_id = str(
                row.get("formalization_gap_planner_handoff_id", "")
                or row.get("handoff_id", "")
                or ""
            ).strip()
            if handoff_id:
                handoff_ids.append(handoff_id)
        handoff_ids = list(dict.fromkeys(handoff_ids))[:4]
        execution_contexts: list[Mapping[str, Any]] = []

        def _add_execution_contexts(value: Any) -> None:
            if isinstance(value, Mapping):
                value = [value]
            for item in value or []:
                if isinstance(item, Mapping):
                    execution_contexts.append(item)

        _add_execution_contexts(
            proof_memory_summary.get(
                "formalization_gap_planner_execution_contexts",
                [],
            )
        )
        contract = proof_memory_summary.get("formal_gap_next_action_contract", {})
        if isinstance(contract, Mapping):
            _add_execution_contexts(
                contract.get("formalization_gap_planner_execution_contexts", [])
            )
        for row in proof_memory_summary.get(
            "formal_gap_next_action_diagnostics",
            [],
        ) or []:
            if isinstance(row, Mapping):
                _add_execution_contexts(
                    row.get("formalization_gap_planner_execution_contexts", [])
                )
        for row in formal_gap_next_action_agenda_rows:
            _add_execution_contexts(
                row.get("formalization_gap_planner_execution_contexts", [])
            )
            scalar_context = {
                key: row.get(key)
                for key in (
                    "formalization_gap_planner_bridge_id",
                    "formalization_gap_planner_handoff_id",
                    "standalone_seed_artifact_id",
                    "standalone_seed_path",
                    "target_intake_path",
                    "target_intake_cli",
                    "component_resource_registry_cli",
                    "standalone_plan_cli",
                    "llm_route_planner_prompt_cli",
                    "llm_route_planner_live_cli",
                    "reuse_smoke_cli",
                    "recommended_llm_provider",
                    "recommended_model_tier",
                    "target_prover_family",
                    "proof_evidence_status",
                    "proof_evidence_boundary",
                )
                if row.get(key)
            }
            if scalar_context:
                _add_execution_contexts(scalar_context)
        execution_contexts = list(
            {
                stable_hash(context): context
                for context in execution_contexts
            }.values()
        )[:3]
        acceptance_gates = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "formal_gap_next_action_acceptance_gates",
                [],
            )
            or []
            if str(value).strip()
        ][:3]
        for row in formal_gap_next_action_agenda_rows:
            acceptance_gate = str(row.get("acceptance_gate", "") or "").strip()
            if acceptance_gate:
                acceptance_gates.append(acceptance_gate)
        acceptance_gates = list(dict.fromkeys(acceptance_gates))[:3]
        route_feedback_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "formal_gap_route_planner_contract_feedback_ids",
                [],
            )
            or []
            if str(value).strip()
        ]
        route_failure_classes = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "formal_gap_route_planner_failure_classifications",
                [],
            )
            or []
            if str(value).strip()
        ]
        staged_error_preview = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "formal_gap_route_planner_staged_assembly_error_preview",
                [],
            )
            or []
            if str(value).strip()
        ]
        if isinstance(contract, Mapping):
            route_feedback_ids.extend(
                str(value).strip()
                for value in contract.get("route_planner_contract_feedback_ids", [])
                or []
                if str(value).strip()
            )
            route_failure_classes.extend(
                str(value).strip()
                for value in contract.get("failure_classifications", []) or []
                if str(value).strip()
            )
            staged_error_preview.extend(
                str(value).strip()
                for value in contract.get("staged_followup_assembly_error_preview", [])
                or []
                if str(value).strip()
            )
        for row in formal_gap_next_action_agenda_rows:
            route_feedback_ids.extend(
                str(value).strip()
                for value in (
                    row.get("route_planner_contract_feedback_ids", [])
                    or [
                        row.get("route_planner_contract_feedback_id", ""),
                    ]
                )
                if str(value).strip()
            )
            route_failure_classes.extend(
                str(value).strip()
                for value in (
                    row.get("failure_classifications", [])
                    or [
                        row.get("failure_classification", ""),
                    ]
                )
                if str(value).strip()
            )
            staged_error_preview.extend(
                str(value).strip()
                for value in (
                    row.get("staged_followup_assembly_error_preview", []) or []
                )
                if str(value).strip()
            )
        route_feedback_ids = list(dict.fromkeys(route_feedback_ids))[:4]
        route_failure_classes = list(dict.fromkeys(route_failure_classes))[:4]
        staged_error_preview = list(dict.fromkeys(staged_error_preview))[:6]
        instruction = (
            "Formal-gap next-action routing is active: consume "
            "proof_bank_runtime_memory_summary.formal_gap_next_action_contract "
            "and diagnostics as an orchestration contract before broad theory "
            "expansion. Reuse retrieved formal-source/prover context, stage the "
            "runtime formalization-gap planner prompt packets from the bridge/seed "
            "when present, run the standalone minimal-delta gap planner, and replay "
            "target-prover/local Lean checks before promoting any obligation or "
            "theorem claim. Do not replace the planner path with hardcoded "
            "corner-case Lean or informal derivation claims; if the route cannot be "
            "completed, keep the affected target as FORMAL_GAP and name the exact "
            "missing prover API, source theorem primitive, bridge premise, or "
            "gap-planner artifact. These routing rows are not proof evidence."
        )
        if target_ids:
            instruction += " Target(s): " + ", ".join(target_ids) + "."
        if bridge_ids:
            instruction += " Gap-planner bridge(s): " + ", ".join(bridge_ids) + "."
        if seed_ids:
            instruction += " Standalone seed(s): " + ", ".join(seed_ids) + "."
        if handoff_ids:
            instruction += " Gap-planner handoff(s): " + ", ".join(handoff_ids) + "."
        if execution_contexts:
            context_snippets = []
            for context in execution_contexts[:2]:
                parts = []
                for label, key in (
                    ("seed path", "standalone_seed_path"),
                    ("target intake", "target_intake_path"),
                    ("standalone plan CLI", "standalone_plan_cli"),
                    ("target-intake CLI", "target_intake_cli"),
                    (
                        "component-resource CLI",
                        "component_resource_registry_cli",
                    ),
                    ("offline LLM route-planner CLI", "llm_route_planner_prompt_cli"),
                    ("reuse-smoke CLI", "reuse_smoke_cli"),
                    ("optional live LLM CLI", "llm_route_planner_live_cli"),
                ):
                    value = str(context.get(key, "") or "").strip()
                    if value:
                        parts.append(f"{label}: {value}")
                if parts:
                    context_snippets.append("; ".join(parts))
            if context_snippets:
                instruction += (
                    " Gap-planner execution context(s): "
                    + " | ".join(context_snippets)
                    + "."
                )
        if acceptance_gates:
            instruction += " Acceptance gate(s): " + "; ".join(acceptance_gates) + "."
        if route_feedback_ids or route_failure_classes or staged_error_preview:
            instruction += (
                " Route-planner contract repair is active: preserve the same "
                "handoff/seed and revise the route response against the exact "
                "contract feedback before any target-prover replay."
            )
        if route_feedback_ids:
            instruction += (
                " Contract feedback id(s): " + ", ".join(route_feedback_ids) + "."
            )
        if route_failure_classes:
            instruction += (
                " Failure class(es): " + ", ".join(route_failure_classes) + "."
            )
        if staged_error_preview:
            instruction += (
                " Staged assembly error preview(s): "
                + " | ".join(staged_error_preview)
                + "."
            )
        instructions.append(instruction)
    pseudo_formal_memory = [
        row
        for row in proof_memory_summary.get("pseudo_formal_block_routing_memory", [])
        or []
        if isinstance(row, Mapping)
    ]
    pseudo_formal_diagnostic_memory = [
        row
        for row in proof_memory_summary.get(
            "pseudo_formal_block_routing_diagnostic_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    pseudo_formal_independent_bv_feedback_memory = [
        row
        for row in proof_memory_summary.get(
            "pseudo_formal_independent_block_verification_feedback_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    pseudo_formal_packet_gate_failure_memory = [
        row
        for row in proof_memory_summary.get(
            "formalizer_pseudo_formal_packet_component_gate_failure_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get(
            "formalizer_pseudo_formal_packet_component_gate_failure_available",
            False,
        )
        or pseudo_formal_packet_gate_failure_memory
    ):
        target_lanes: list[str] = []
        issue_kinds: list[str] = []
        manifest_paths: list[str] = []
        copy_contract_paths: list[str] = []
        copy_ready_summaries: list[str] = []
        copy_blocked_summaries: list[str] = []
        for row in pseudo_formal_packet_gate_failure_memory[:3]:
            manifest_path = str(row.get("component_eval_manifest_path", "") or "")
            if manifest_path:
                manifest_paths.append(manifest_path)
            target_lanes.extend(
                str(value).strip()
                for value in row.get("required_target_lanes", []) or []
                if str(value).strip()
            )
            issue_summary = row.get("validation_issue_summary", {})
            if isinstance(issue_summary, Mapping):
                issue_kinds.extend(
                    str(value).strip()
                    for value in issue_summary.get("blocking_issue_kinds", []) or []
                    if str(value).strip()
                )
            copy_summary = row.get("validator_ready_copy_contract_summary", {})
            copy_summary_present = isinstance(copy_summary, Mapping) and bool(
                copy_summary
            )
            copy_summary_satisfied = (
                bool(copy_summary.get("validator_ready_copy_contract_satisfied"))
                if isinstance(copy_summary, Mapping)
                else False
            )
            copy_contract = row.get("validator_ready_copy_contract", {})
            if isinstance(copy_contract, Mapping):
                copy_path = str(copy_contract.get("copy_source_path", "") or "")
                if copy_path and (not copy_summary_present or copy_summary_satisfied):
                    copy_contract_paths.append(copy_path)
            if copy_summary_present:
                if copy_summary_satisfied:
                    copy_ready_summaries.append("copy_contract_satisfied")
                if copy_summary.get(
                    "exact_semantic_definition_lane_ready_if_copied"
                ):
                    copy_ready_summaries.append(
                        "exact_semantic_definition_lane_ready_if_copied"
                    )
                if not copy_summary_satisfied:
                    copy_blocked_summaries.append(
                        "copy_contract_failed_runtime_recompute"
                    )
        instruction = (
            "Formalizer PF/BV packet component-gate failure memory is active: "
            "proof_bank_runtime_memory_summary."
            "formalizer_pseudo_formal_packet_component_gate_failure_memory "
            "contains a concrete_lane_routable_repair_seed and validation issue "
            "taxonomy from the prior failed packet eval. Copy or minimally adapt "
            "that seed into pseudo_formal_proof_packets before changing Lean "
            "targets. The seed is non-proof repair guidance only; do not count it "
            "as Lean proof, source theorem proof, source faithfulness evidence, or "
            "kernel verification. Preserve its source_anchors, conclusion, "
            "semantic_primitive_requirements, required target lanes, and PF/BV "
            "non-proof boundary."
        )
        if copy_contract_paths:
            instruction += (
                " A validator_ready_copy_contract is available; copy "
                + ", ".join(list(dict.fromkeys(copy_contract_paths))[:3])
                + " into pseudo_formal_proof_packets before optional edits."
            )
        if copy_ready_summaries:
            instruction += (
                " Runtime recomputed the copied seed as "
                + ", ".join(list(dict.fromkeys(copy_ready_summaries))[:3])
                + "; preserve those fields instead of reconstructing the packet."
            )
        if copy_blocked_summaries:
            instruction += (
                " A validator_ready_copy_contract was present but did not pass "
                "runtime recomputation; do not copy its raw repair seed verbatim. "
                "Repair from validation_issue_summary and emit a fresh locally "
                "valid, lane-routable pseudo_formal_proof_packets entry."
            )
        if target_lanes:
            instruction += (
                " Required target lane(s): "
                + ", ".join(list(dict.fromkeys(target_lanes))[:5])
                + "."
            )
        if issue_kinds:
            instruction += (
                " Prior issue kind(s): "
                + ", ".join(list(dict.fromkeys(issue_kinds))[:6])
                + "."
            )
        if manifest_paths:
            instruction += (
                " Source component manifest(s): "
                + ", ".join(list(dict.fromkeys(manifest_paths))[:3])
                + "."
            )
        instructions.append(instruction)
    pf_copy_ready_retry_agenda_memory = [
        row
        for row in proof_memory_summary.get(
            "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get(
            "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_available",
            False,
        )
        or pf_copy_ready_retry_agenda_memory
    ):
        agenda_ids: list[str] = []
        work_order_ids: list[str] = []
        target_lanes: list[str] = []
        queue_statuses: list[str] = []
        manifest_paths: list[str] = []
        for row in pf_copy_ready_retry_agenda_memory[:3]:
            agenda_id = str(row.get("agenda_id", "") or "").strip()
            if agenda_id:
                agenda_ids.append(agenda_id)
            work_order_id = str(row.get("work_order_id", "") or "").strip()
            if work_order_id:
                work_order_ids.append(work_order_id)
            queue_status = str(row.get("runtime_queue_status", "") or "").strip()
            if queue_status:
                queue_statuses.append(queue_status)
            manifest_path = str(row.get("component_eval_manifest_path", "") or "")
            if manifest_path:
                manifest_paths.append(manifest_path)
            target_lanes.extend(
                str(value).strip()
                for value in row.get("required_target_lanes", []) or []
                if str(value).strip()
            )
        instruction = (
            "Formalizer PF/BV copy-ready retry agenda is active: consume "
            "proof_bank_runtime_memory_summary."
            "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory "
            "as the operational rerun instruction. Copy or minimally adapt the "
            "validator-ready PF/BV repair fragment into "
            "pseudo_formal_proof_packets, preserving source_anchors, conclusion, "
            "semantic_primitive_requirements, required target lanes, packet "
            "lineage, and the PF/BV non-proof boundary. This is non-proof retry "
            "agenda memory only; do not count it as Lean proof, source theorem "
            "proof, source faithfulness evidence, or kernel verification."
        )
        if work_order_ids:
            instruction += (
                " Retry work order id(s): "
                + ", ".join(list(dict.fromkeys(work_order_ids))[:3])
                + "."
            )
        if agenda_ids:
            instruction += (
                " Agenda id(s): "
                + ", ".join(list(dict.fromkeys(agenda_ids))[:3])
                + "."
            )
        if queue_statuses:
            instruction += (
                " Runtime queue status(es): "
                + ", ".join(list(dict.fromkeys(queue_statuses))[:3])
                + "."
            )
        if target_lanes:
            instruction += (
                " Required target lane(s): "
                + ", ".join(list(dict.fromkeys(target_lanes))[:5])
                + "."
            )
        if manifest_paths:
            instruction += (
                " Source component manifest(s): "
                + ", ".join(list(dict.fromkeys(manifest_paths))[:3])
                + "."
            )
        instructions.append(instruction)
    pf_component_gate_handoff_diagnostics = [
        row
        for row in proof_memory_summary.get(
            "formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get(
            "formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_available",
            False,
        )
        or pf_component_gate_handoff_diagnostics
    ):
        exact_rows_paths = [
            str(row.get("source_component_gate_exact_rows_jsonl", "") or "").strip()
            for row in pf_component_gate_handoff_diagnostics[:3]
            if str(row.get("source_component_gate_exact_rows_jsonl", "") or "").strip()
        ]
        failure_classes = [
            str(row.get("failure_classification", "") or "").strip()
            for row in pf_component_gate_handoff_diagnostics[:3]
            if str(row.get("failure_classification", "") or "").strip()
        ]
        owner_subsystems = [
            str(row.get("next_owner_subsystem", "") or "").strip()
            for row in pf_component_gate_handoff_diagnostics[:3]
            if str(row.get("next_owner_subsystem", "") or "").strip()
        ]
        instruction = (
            "Formalizer PF/BV component-gate exact-row handoff is blocked: "
            "the runtime did not materialize source-theorem exact semantic-definition "
            "work orders from the component-gate exact-lane artifact. Do not assume "
            "source lookup, exact semantic-definition authoring, or proof-body repair "
            "has consumed those rows. Regenerate, rehydrate, or request the exact rows "
            "JSONL artifact before treating PF/BV exact-lane routing as downstream "
            "source-lookup progress. This is handoff recovery memory only, not proof "
            "or kernel evidence."
        )
        if exact_rows_paths:
            instruction += (
                " Exact-row artifact path(s): "
                + ", ".join(list(dict.fromkeys(exact_rows_paths))[:3])
                + "."
            )
        if failure_classes:
            instruction += (
                " Failure class(es): "
                + ", ".join(list(dict.fromkeys(failure_classes))[:4])
                + "."
            )
        if owner_subsystems:
            instruction += (
                " Next owner(s): "
                + ", ".join(list(dict.fromkeys(owner_subsystems))[:3])
                + "."
            )
        instructions.append(instruction)
    if proof_memory_summary.get("pseudo_formal_block_routing_active") or pseudo_formal_memory:
        target_lanes = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "pseudo_formal_block_routing_target_lanes",
                [],
            )
            or []
            if str(value).strip()
        ]
        target_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "pseudo_formal_block_routing_target_ids",
                [],
            )
            or []
            if str(value).strip()
        ][:5]
        work_order_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "pseudo_formal_block_routing_work_order_ids",
                [],
            )
            or []
            if str(value).strip()
        ][:5]
        for row in pseudo_formal_memory:
            lane = str(row.get("target_lane", "") or "").strip()
            if lane:
                target_lanes.append(lane)
            target_ids.extend(
                str(value).strip()
                for value in row.get("target_ids", []) or []
                if str(value).strip()
            )
            work_order_id = str(
                row.get("source_pseudo_formal_work_order_id", "") or ""
            ).strip()
            if work_order_id:
                work_order_ids.append(work_order_id)
        target_lanes = list(dict.fromkeys(target_lanes))[:5]
        target_ids = list(dict.fromkeys(target_ids))[:5]
        work_order_ids = list(dict.fromkeys(work_order_ids))[:5]
        instruction = (
            "Pseudo-formal/block-verification routing memory is active: consume "
            "proof_bank_runtime_memory_summary.pseudo_formal_block_routing_contract "
            "and pseudo_formal_block_routing_memory before proposing new broad proof "
            "work. These rows decompose blocked proof text into lane-specific tasks; "
            "they are not Lean kernel evidence and do not prove the source theorem. "
            "Preserve block_depth, scope_parent_id scope-inheritance forest, "
            "statement-level dependency_scope, faithfulness repair status, and "
            "BV calibration strictness when regenerating or rerouting PF/BV packets. "
            "For target_lane=formal_targets, emit a bounded concrete Lean candidate "
            "for the named block and require local Lean/AXLE replay. For "
            "target_lane=lean_rag, emit retrieval_queries or formal-source grounding "
            "requests for exact declarations. For target_lane=source_to_bridge, emit "
            "a source-backed semantic primitive or premise-derivation request. For "
            "target_lane=source_theorem_exact_semantic_definition, author or request "
            "exact semantic definitions before proof-body search resumes. For "
            "target_lane=formal_gap, split or reroute the residual block through "
            "gap_taxonomy/next_actions or the FormalizationGapPlanner. Do not satisfy "
            "the Lean-candidate gate with pseudo_formal_proof_packets alone, and do "
            "not hardcode corner-case proof rules in place of the requested lane."
        )
        if target_lanes:
            instruction += " Target lane(s): " + ", ".join(target_lanes) + "."
        if target_ids:
            instruction += " Target id(s): " + ", ".join(target_ids) + "."
        if work_order_ids:
            instruction += " PF/BV work order(s): " + ", ".join(work_order_ids) + "."
        instructions.append(instruction)
    if (
        proof_memory_summary.get(
            "pseudo_formal_independent_block_verification_feedback_active"
        )
        or pseudo_formal_independent_bv_feedback_memory
    ):
        bv_work_order_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "pseudo_formal_independent_block_verification_work_order_ids",
                [],
            )
            or []
            if str(value).strip()
        ][:5]
        bv_verdicts = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "pseudo_formal_independent_block_verification_verdicts",
                [],
            )
            or []
            if str(value).strip()
        ][:5]
        bv_provenances: list[str] = []
        bv_block_ids: list[str] = []
        for row in pseudo_formal_independent_bv_feedback_memory:
            provenance = str(
                row.get("block_verification_verifier_provenance", "") or ""
            ).strip()
            if provenance:
                bv_provenances.append(provenance)
            block_id = str(row.get("source_block_id", "") or "").strip()
            if block_id:
                bv_block_ids.append(block_id)
        bv_provenances = list(dict.fromkeys(bv_provenances))[:5]
        bv_block_ids = list(dict.fromkeys(bv_block_ids))[:5]
        instruction = (
            "Independent pseudo-formal block-verifier feedback is available: "
            "consume proof_bank_runtime_memory_summary."
            "pseudo_formal_independent_block_verification_feedback_memory as "
            "calibrated PF/BV feedback over the exact explicit premises, "
            "statement-only dependency context, conclusion, and local proof text "
            "used by the verifier. Accepted verdicts may unblock regeneration or "
            "rerouting of the bounded PF block, but they are not Lean kernel "
            "evidence. Failed verdicts require repairing, splitting, or rerouting "
            "the PF block before any downstream Lean/RAG/source-to-bridge lane."
        )
        if bv_verdicts:
            instruction += " BV verdict(s): " + ", ".join(bv_verdicts) + "."
        if bv_provenances:
            instruction += (
                " Independent verifier provenance(s): "
                + ", ".join(bv_provenances)
                + "."
            )
        if bv_block_ids:
            instruction += " Source block id(s): " + ", ".join(bv_block_ids) + "."
        if bv_work_order_ids:
            instruction += " PF/BV work order(s): " + ", ".join(bv_work_order_ids) + "."
        instructions.append(instruction)
    if (
        proof_memory_summary.get("pseudo_formal_block_routing_diagnostic_active")
        or pseudo_formal_diagnostic_memory
    ):
        diagnostic_lanes = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "pseudo_formal_block_routing_diagnostic_target_lanes",
                [],
            )
            or []
            if str(value).strip()
        ]
        diagnostic_work_order_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "pseudo_formal_block_routing_diagnostic_work_order_ids",
                [],
            )
            or []
            if str(value).strip()
        ][:5]
        diagnostic_row_kinds = []
        for row in pseudo_formal_diagnostic_memory:
            row_kind = str(row.get("row_kind", "") or "").strip()
            if row_kind:
                diagnostic_row_kinds.append(row_kind)
            lane = str(row.get("target_lane", "") or "").strip()
            if lane:
                diagnostic_lanes.append(lane)
            work_order_id = str(
                row.get("source_pseudo_formal_work_order_id", "") or ""
            ).strip()
            if work_order_id:
                diagnostic_work_order_ids.append(work_order_id)
        diagnostic_lanes = list(dict.fromkeys(diagnostic_lanes))[:5]
        diagnostic_row_kinds = list(dict.fromkeys(diagnostic_row_kinds))[:5]
        diagnostic_work_order_ids = list(dict.fromkeys(diagnostic_work_order_ids))[:5]
        instruction = (
            "Pseudo-formal/block-verification diagnostic memory is active: prior "
            "PF/BV rows are not lane-routable and must not be treated as Lean/RAG/"
            "source-to-bridge work-order activation. Repair the PF/BV packet first: "
            "resolve packet validation quarantine, missing faithfulness repair, "
            "pending/failed block verification, or missing accepted BV rollout_count "
            "before emitting downstream lane work. These diagnostics remain "
            "non-proof evidence and do not satisfy required PF/BV activation."
        )
        if diagnostic_row_kinds:
            instruction += " Diagnostic row kind(s): " + ", ".join(diagnostic_row_kinds) + "."
        if diagnostic_lanes:
            instruction += " Blocked target lane(s): " + ", ".join(diagnostic_lanes) + "."
        if diagnostic_work_order_ids:
            instruction += (
                " Diagnostic PF/BV work order(s): "
                + ", ".join(diagnostic_work_order_ids)
                + "."
            )
        instructions.append(instruction)
    if source_theorem_candidate_materialization_required:
        targets = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "source_theorem_candidate_materialization_required_target_names",
                [],
            )
            or []
            if str(value).strip()
        ]
        target_ids = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "source_theorem_candidate_materialization_required_target_ids",
                [],
            )
            or []
            if str(value).strip()
        ]
        for row in materialization_agenda_rows:
            targets.extend(
                str(value).strip()
                for value in row.get("target_ids", []) or []
                if str(value).strip()
            )
            target_ids.extend(
                str(value).strip()
                for value in row.get("target_ids", []) or []
                if str(value).strip()
            )
        targets = list(dict.fromkeys(targets))[:4]
        target_ids = list(dict.fromkeys(target_ids))[:4]
        statuses = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "source_theorem_candidate_materialization_required_statuses",
                [],
            )
            or []
            if str(value).strip()
        ]
        for row in materialization_agenda_rows:
            statuses.extend(
                str(value).strip()
                for value in row.get("candidate_materialization_statuses", []) or []
                if str(value).strip()
            )
        statuses = list(dict.fromkeys(statuses))[:5]
        materialization_contract = str(
            proof_memory_summary.get(
                "source_theorem_candidate_materialization_contract",
                "",
            )
            or ""
        ).strip()
        if not materialization_contract:
            materialization_contract = next(
                (
                    str(row.get("acceptance_gate", "") or "").strip()
                    for row in materialization_agenda_rows
                    if str(row.get("acceptance_gate", "") or "").strip()
                ),
                "",
            )
        if not materialization_contract:
            materialization_contract = next(
                (
                    str(row.get("required_resolution", "") or "").strip()
                    for row in materialization_resource_requests
                    if str(row.get("required_resolution", "") or "").strip()
                ),
                "",
            )
        instruction = (
            "For source_theorem_exact_candidate_materialization_required, make the "
            "main output a concrete exact source-theorem formal_targets candidate "
            "that AgentRuntime can materialize into a Lean artifact and then send "
            "through signature probes. Do not treat this as proof-body repair, "
            "semantic-definition review, or proof evidence. Preserve the exact source "
            "theorem target/provenance, name the target Lean declaration when known, "
            "include retrieval/prover queries for missing imports or APIs, and only "
            "ask local Lean/AXLE/signature-probe tools to check candidates actually "
            "emitted in this packet."
        )
        if targets:
            instruction += " Materialization target(s): " + ", ".join(targets) + "."
        if target_ids:
            instruction += (
                " Materialization target id(s): "
                + ", ".join(target_ids)
                + "."
            )
        if statuses:
            instruction += " Blocking status(es): " + ", ".join(statuses) + "."
        if materialization_contract:
            instruction += " Acceptance gate: " + materialization_contract
        instructions.append(instruction)
    if source_theorem_proof_body_adapter_feedback:
        instructions.append(
            "Source theorem proof-body adapter feedback is active: consume "
            "runtime_environment_feedback.source_theorem_proof_body_adapter_feedback "
            "as proof-route context. If adapter_kernel_verified=false, strengthen the "
            "source-to-bridge adapter or derive missing bridge premises from exact "
            "source hypotheses before retrying the exact source theorem. If "
            "adapter_kernel_verified=true, use the verified adapter only as context "
            "for an exact source-theorem proof-body retry. Adapter rows are not full "
            "source-theorem proof evidence."
        )
    carried_local_lean_repair_contract = (
        runtime_environment_feedback.get("local_lean_repair_contract", {})
        if isinstance(
            runtime_environment_feedback.get("local_lean_repair_contract", {}),
            Mapping,
        )
        else {}
    )
    if carried_local_lean_repair_contract and feedback_failure not in {
        "formalizer_lean_candidate_precheck_rejected",
        "formalizer_lean_candidate_local_lean_failed",
    }:
        instructions.append(
            "Carried Local-Lean repair contract is still mandatory: even though the "
            "current wrapper failure is packet validation, the next packet must also "
            "satisfy runtime_environment_feedback.local_lean_repair_contract before "
            "emitting another NEEDS_KERNEL_CHECK candidate."
        )
        blocked_import_prefixes = _blocked_import_prefixes_for_prompt(
            carried_local_lean_repair_contract
        )
        if blocked_import_prefixes:
            quoted_prefixes = ", ".join(
                f"`{value}`" for value in blocked_import_prefixes[:8]
            )
            instructions.append(
                "Mandatory unavailable-import-prefix repair: local Lean reported "
                f"unknown/unavailable module prefix(es): {quoted_prefixes}. Do not "
                "import any blocked prefix or submodule in the next candidate. Use no "
                "imports, an import already verified in this same configured Lake "
                "project, or emit a FORMAL_GAP/dependency blocker instead of retrying "
                "the same module path."
            )
        if carried_local_lean_repair_contract.get("mathlib_import_unavailable"):
            instructions.append(
                "Mandatory Mathlib-root repair: this configured Lean environment "
                "reported the umbrella import `import Mathlib` as unavailable. Do "
                "not retry that umbrella import. This is not by itself proof that "
                "every `Mathlib.*` submodule is unavailable: use only a narrow "
                "module import already verified by runtime/precheck, or a listed "
                "suggested_import_replacement. If the source theorem still needs "
                "missing measure/probability APIs, keep it as "
                "expected_status=FORMAL_GAP and name the exact missing import/API. "
                "Any revised executable candidate must preserve its typed target "
                "lineage and return through the configured Lean compiler."
            )
        carried_diagnostic_classes = {
            str(value).strip()
            for value in carried_local_lean_repair_contract.get(
                "diagnostic_classes",
                [],
            )
            or []
            if str(value).strip()
        }
        if carried_diagnostic_classes & {
            "lean_unknown_tactic",
            "lean_typeclass_synthesis_failed",
        }:
            instructions.append(
                "Mandatory compiler-diagnostic repair: consume the exact "
                "unknown-tactic/typeclass diagnostics, available imports, retrieved "
                "local declarations/instances, and Lean proof state. Generate a "
                "revised proof and rerun Lean; do not substitute a runtime-authored "
                "tactic or typeclass recipe."
            )
        verified_narrow_imports = [
            str(value).strip()
            for value in carried_local_lean_repair_contract.get(
                "verified_narrow_imports",
                [],
            )
            or []
            if str(value).strip()
        ]
        if verified_narrow_imports:
            instructions.append(
                "Mandatory verified-narrow-import repair: runtime/precheck already "
                "verified these narrow module imports in the configured Lake project: "
                + ", ".join(f"`{value}`" for value in verified_narrow_imports[:8])
                + ". If the repaired candidate needs those APIs, import one of these "
                "modules exactly; otherwise use no import or emit a FORMAL_GAP. Do not "
                "retry `import Mathlib`."
            )
    prior_lean_candidate_repair_memory = [
        row
        for row in proof_memory_summary.get(
            "formalizer_lean_candidate_repair_memory", []
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get("formalizer_lean_candidate_repair_required")
        or prior_lean_candidate_repair_memory
    ):
        import_replacement_rows = [
            replacement
            for row in prior_lean_candidate_repair_memory
            if isinstance(row.get("local_lean_repair_contract", {}), Mapping)
            for replacement in row.get("local_lean_repair_contract", {}).get(
                "suggested_import_replacements",
                [],
            )
            or []
            if isinstance(replacement, Mapping)
        ]
        instructions.append(
            "Prior Formalizer Lean-candidate repair memory is active: before "
            "proposing unrelated new formal targets, inspect "
            "proof_bank_runtime_memory_summary.formalizer_lean_candidate_repair_memory "
            "and repair the listed artifact_path/source_manifest_path diagnostics. "
            "Use local_lean_diagnostic_classes plus stdout/stderr excerpts to fix "
            "unknown identifiers, imports, syntax, or type mismatches. These rows are "
            "repair memory only, not proof evidence. If a row has lean_timeout, treat "
            "it as a candidate-size/search-shape failure: split the candidate into a "
            "smaller checked helper or premise-derivation task, prefer narrow imports, "
            "and keep the source theorem target as FORMAL_GAP unless the repaired "
            "candidate still preserves the task-bound source-theorem conclusion. If the "
            "faithful target cannot be repaired, emit expected_status=FORMAL_GAP with "
            "the exact missing import, API, lemma, or semantic premise instead of "
            "weakening the theorem."
        )
        if import_replacement_rows:
            replacement_text = "; ".join(
                (
                    f"replace {row.get('unavailable_module')} with "
                    f"{', '.join(str(value) for value in row.get('suggested_modules', []) or [])}"
                )
                for row in import_replacement_rows[:3]
            )
            instructions.append(
                "Mandatory suggested-import repair: prior repair memory includes "
                f"suggested_import_replacements ({replacement_text}). The next Lean "
                "source must not import any listed unavailable_module. Use the first "
                "matching suggested module exactly when it matches the dependency, "
                "or remove the guessed import and report a dependency FORMAL_GAP. "
                "This import-replacement rule overrides timeout scope-down and applies "
                "to every new compact helper, arithmetic lower-bound lemma, and "
                "source-to-bridge premise candidate; do not reintroduce an unavailable "
                "module while changing candidate shape."
            )
    prior_diagnostic_helper_memory = [
        row
        for row in proof_memory_summary.get(
            "formalizer_diagnostic_helper_memory",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get("formalizer_diagnostic_helper_integration_required")
        or prior_diagnostic_helper_memory
        or mode == "source_theorem_diagnostic_helper_bridge_or_blocker"
    ):
        instructions.append(
            "Compiled diagnostic-helper integration is active: prior Lean helpers "
            "compiled with source_theorem_target_known=false, so they exercise the "
            "local verifier but are not source-theorem proof. Do not repeat another "
            "helper-only formal_targets candidate as progress. Keep the source "
            "theorem as expected_status=FORMAL_GAP unless its exact task-bound "
            "statement can be checked, and either emit a concrete "
            "source_to_bridge_premise_derivation_candidates object with exact "
            "source-binding metadata plus semantic-anchor references, or record an "
            "explicit gap_taxonomy blocker naming the missing source-binding "
            "premise/API/import/semantic anchor. A source-to-bridge candidate must "
            "carry premise_name, target_theorem_name, target_lean_declaration, "
            "premise_derivation_candidate_lean_source, and one copied candidate "
            "request/source-binding contract; otherwise it is a phantom action and "
            "must not be listed in next_actions."
        )
    if (
        mode == "source_to_bridge_metadata_authoring_required"
        or _formalizer_bool_like(
            proof_memory_summary.get("source_to_bridge_metadata_authoring_required")
        )
    ):
        instructions.append(
            "Source-to-bridge metadata authoring is active: consume "
            "proof_bank_runtime_memory_summary.source_to_bridge_metadata_authoring_contract "
            "and diagnostics before emitting any executable premise candidate. "
            "The immediate task is to author or retrieve the exact "
            "source_to_bridge_premise_derivation_candidate_request metadata: "
            "premise_name, target theorem/declaration, exact_source_theorem_binders, "
            "premise_semantic_dependency_requirements, "
            "premise_semantic_anchor_binders, premise_semantic_anchor_binder_names, "
            "required_semantic_anchor_reference_names, semantic_anchor_reference_gate, "
            "and adapter_object_names_requiring_source_instantiation. Prefer "
            "requirements grounded in retrieved formal-source declarations, prover "
            "diagnostics, or exact theorem binders over task-family heuristics. Emit a "
            "source_to_bridge_premise_derivation_candidates object only if that "
            "candidate includes a copied request object/id and non-vacuous Lean source "
            "using those binders and anchors. If you can author the metadata but "
            "not the executable Lean premise derivation yet, put the structured "
            "request object in source_to_bridge_premise_derivation_candidate_requests "
            "and do not ask AgentRuntime/AXLE to check it. If you cannot author the "
            "metadata, keep the source theorem as "
            "expected_status=FORMAL_GAP and record a gap_taxonomy row with "
            "kind=source_to_bridge_metadata_blocker plus next_actions for "
            "AgentRuntime/ProofEngineer to materialize the request metadata. This "
            "metadata-authoring queue is not proof evidence."
        )
    prior_lean_candidate_proof_state_feedback = [
        row
        for row in proof_memory_summary.get(
            "formalizer_lean_candidate_proof_state_feedback_memory", []
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get(
            "formalizer_lean_candidate_proof_state_feedback_available"
        )
        or prior_lean_candidate_proof_state_feedback
    ):
        instructions.append(
            "Prior Formalizer Lean-candidate proof-state feedback is active: "
            "consume proof_bank_runtime_memory_summary."
            "formalizer_lean_candidate_proof_state_feedback_memory before "
            "proposing a new Lean candidate. Treat residual_goals, diagnostics, "
            "executed_tools, tool_call_trace, requested_tools, and "
            "source_materialization_manifest_id as the ProofEngineer repair "
            "context. Use executed_tools/tool_call_trace as the verifier "
            "observations that actually ran; use requested_tools as pending "
            "Lean-LSP/search/multi-attempt work to perform next. Follow the "
            "prover loop requested there (lean_diagnostic_messages, lean_goal, "
            "lean_state_search or proof_search, lean_multi_attempt, then local "
            "Lean/AXLE rerun). "
            "Do not replace this with a broad fresh theorem or a human-debugged "
            "patch; emit a bounded repaired candidate, a smaller lemma split, "
            "or a formal blocker. These rows are repair memory only, not proof "
            "evidence."
        )
    unbound_lean_candidate_proof_state_feedback = [
        row
        for row in proof_memory_summary.get(
            "formalizer_lean_candidate_unbound_proof_state_feedback_memory", []
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get(
            "formalizer_lean_candidate_unbound_proof_state_feedback_available"
        )
        or unbound_lean_candidate_proof_state_feedback
    ):
        instructions.append(
            "Unbound Formalizer Lean-candidate proof-state feedback was rejected "
            "by AgentRuntime lineage checks: inspect "
            "proof_bank_runtime_memory_summary."
            "formalizer_lean_candidate_unbound_proof_state_feedback_memory only "
            "as a lineage blocker. Do not use it as proof-state observations, "
            "residual goals, or repair evidence. First load or regenerate the "
            "matching Lean-candidate materialization feedback row, then rerun "
            "proof-state feedback against that exact artifact."
        )
    component_gate_feedback_memory = [
        row
        for row in proof_memory_summary.get(
            "formalizer_lean_candidate_component_gate_feedback_memory", []
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get(
            "formalizer_lean_candidate_component_gate_feedback_available"
        )
        or component_gate_feedback_memory
    ):
        instructions.append(
            "Formalizer component-gate feedback is active: consume "
            "proof_bank_runtime_memory_summary."
            "formalizer_lean_candidate_component_gate_feedback_memory as "
            "calibration for the expected prover feedback loop. It may show that "
            "a synthetic helper repair gate injected prior local-Lean/proof-state "
            "feedback, ran a bounded Formalizer/ProofEngineer repair task, and "
            "reran local Lean. Do not cite that helper as source-theorem proof or "
            "semantic faithfulness evidence. For the current source theorem, use "
            "the same loop shape only when the target artifact is actually the "
            "current source-theorem candidate: failed Lean diagnostics -> "
            "ProofEngineer feedback -> bounded repair -> local Lean/AXLE rerun, "
            "otherwise disclose a FORMAL_GAP."
        )
    capability_feedback_memory = [
        row
        for row in proof_memory_summary.get(
            "formalizer_lean_candidate_capability_feedback_memory", []
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get(
            "formalizer_lean_candidate_capability_feedback_available"
        )
        or capability_feedback_memory
    ):
        instructions.append(
            "Integrated Formalizer/ProofEngineer capability feedback is active: "
            "consume proof_bank_runtime_memory_summary."
            "formalizer_lean_candidate_capability_feedback_memory as the current "
            "runtime capability gap to close. If it asks for proof-state routing, "
            "local Lean tool calls, live prover tool calls, or a fail-then-pass "
            "Lean-candidate repair loop, emit a bounded source-theorem candidate, "
            "proof-state request, or formal blocker that drives that exact loop "
            "inside AgentRuntime. Do not satisfy this with static replay, attached "
            "component calibration, or a generic proof-bank queue."
        )
    runtime_contract_feedback_memory = [
        row
        for row in proof_memory_summary.get(
            "formalizer_runtime_capability_contract_feedback_memory", []
        )
        or []
        if isinstance(row, Mapping)
    ]
    if (
        proof_memory_summary.get(
            "formalizer_runtime_capability_contract_feedback_available"
        )
        or runtime_contract_feedback_memory
    ):
        instructions.append(
            "Prior Formalizer runtime capability-contract feedback is active: "
            "consume proof_bank_runtime_memory_summary."
            "formalizer_runtime_capability_contract_feedback_memory before "
            "proposing the next packet. These rows identify unmet AgentRuntime "
            "tool/evidence contracts, not theorem proof failures. If the row "
            "requires runtime configuration such as local Lean or Lean-LSP/MCP, "
            "do not claim the gap is closed with Lean text alone; emit a bounded "
            "candidate or explicit formal blocker that lets AgentRuntime rerun "
            "the requested tool path. If the row requires Formalizer behavior "
            "such as a concrete theorem/lemma/def declaration or proof-state "
            "request metadata, preserve the listed runtime_requested_evidence_contract "
            "flags and drive exactly those counters. These rows are not proof "
            "evidence."
        )
    if feedback_failure == "formalizer_packet_validation_failed":
        packet_attempts = _feedback_int(
            runtime_environment_feedback.get("attempts", 0)
        )
        packet_retry_depth = _feedback_int(
            runtime_environment_feedback.get(
                "formalizer_packet_repair_retry_depth", 0
            )
        )
        repeated_packet_failure = bool(
            runtime_environment_feedback.get(
                "repeated_formalizer_packet_validation_failure", False
            )
            or packet_retry_depth > 0
            or packet_attempts > 1
        )
        missing_anchors = [
            str(anchor).strip()
            for anchor in runtime_environment_feedback.get(
                "missing_semantic_anchor_references", []
            )
            if str(anchor).strip()
        ]
        uninstantiated_adapter_binders = [
            str(binder).strip()
            for binder in runtime_environment_feedback.get(
                "uninstantiated_adapter_object_binders", []
            )
            if str(binder).strip()
        ]
        missing_source_binding_contract_metadata = bool(
            runtime_environment_feedback.get(
                "missing_source_binding_contract_metadata", False
            )
        )
        validation_errors = [
            str(error)
            for error in runtime_environment_feedback.get("validation_errors", [])
            or []
            if str(error).strip()
        ]
        validation_repair_directives = [
            str(directive)
            for directive in runtime_environment_feedback.get(
                "validation_repair_directives",
                [],
            )
            or []
            if str(directive).strip()
        ]
        validation_text = " ".join(validation_errors).lower()
        target_shape_contract = (
            runtime_environment_feedback.get("target_shape_contract", {})
            if isinstance(
                runtime_environment_feedback.get("target_shape_contract", {}),
                Mapping,
            )
            else {}
        )
        target_drift_repair_contract = (
            runtime_environment_feedback.get("target_drift_repair_contract", {})
            if isinstance(
                runtime_environment_feedback.get("target_drift_repair_contract", {}),
                Mapping,
            )
            else {}
        )
        next_action_reference_contract = (
            runtime_environment_feedback.get("next_action_reference_contract", {})
            if isinstance(
                runtime_environment_feedback.get(
                    "next_action_reference_contract", {}
                ),
                Mapping,
            )
            else {}
        )
        source_theorem_candidate_materialization_contract = (
            runtime_environment_feedback.get(
                "source_theorem_candidate_materialization_contract",
                {},
            )
            if isinstance(
                runtime_environment_feedback.get(
                    "source_theorem_candidate_materialization_contract",
                    {},
                ),
                Mapping,
            )
            else {}
        )
        target_shape_contract_active = bool(target_shape_contract)
        has_expected_status_validation = (
            "must set expected_status=needs_kernel_check" in validation_text
        )
        has_hole_validation = any(
            marker in validation_text
            for marker in (
                "lean sorry placeholder",
                "unsupported tactic hole",
                " exact?",
                " by?",
                "admit",
            )
        )
        has_target_shape_validation = "violates target_shape_contract" in validation_text
        has_phantom_source_to_bridge_action = (
            "next_actions reference source_to_bridge_premise_derivation_candidates"
            in validation_text
        )
        missing_anchor_text = ", ".join(missing_anchors)
        uninstantiated_binder_text = ", ".join(uninstantiated_adapter_binders)
        instructions.append(
            "If runtime_environment_feedback reports formalizer_packet_validation_failed, "
            "repair the exact validation_errors before adding new targets. If it "
            "lists missing_semantic_anchor_references, reference each listed anchor name "
            "outside comments in every source_to_bridge_premise_derivation_candidates Lean "
            "source, preserve source-binding request metadata, and avoid new unverified "
            "assumptions. If the exact source hypotheses cannot supply an anchor, report "
            "that semantic blocker in gap_taxonomy/next_actions."
        )
        instructions.extend(
            render_formalizer_validation_repair_policy_instructions(
                runtime_environment_feedback
            )
        )
        if validation_errors:
            instructions.append(
                "Mandatory packet-validator repair: treat these validation_errors as "
                "hard local contract failures, not proof-search suggestions. Do not "
                "repeat any listed failure: "
                + " | ".join(validation_errors[:4])
            )
        if validation_repair_directives:
            instructions.append(
                "Mandatory validation repair directives: "
                + " ".join(validation_repair_directives[:4])
            )
        if source_theorem_candidate_materialization_contract:
            materialization_target_ids = [
                str(value).strip()
                for value in source_theorem_candidate_materialization_contract.get(
                    "target_ids",
                    [],
                )
                or []
                if str(value).strip()
            ]
            materialization_target_names = [
                str(value).strip()
                for value in source_theorem_candidate_materialization_contract.get(
                    "target_names",
                    [],
                )
                or []
                if str(value).strip()
            ]
            materialization_targets = list(
                dict.fromkeys(
                    [*materialization_target_ids, *materialization_target_names]
                )
            )
            instruction = (
                "Mandatory source-theorem candidate-materialization repair: emit a "
                "concrete exact source-theorem formal_targets Lean theorem/lemma "
                "candidate with expected_status=NEEDS_KERNEL_CHECK, nonempty "
                "lean_statement_sketch, "
                "source_theorem_target_provenance.source_theorem_target_known=true, "
                "and the requested target identity preserved. Do not satisfy this "
                "mode with FORMAL_GAP-only, helper-only, support-only, or "
                "source-to-bridge-only outputs; do not claim proof until Lean/AXLE "
                "kernel verification checks the exact candidate."
            )
            if materialization_targets:
                instruction += (
                    " Requested target id/name(s): "
                    + ", ".join(materialization_targets)
                    + "."
                )
            instructions.append(instruction)
        if next_action_reference_contract:
            instructions.append(
                "Mandatory next_action_reference_contract repair: every next_actions "
                "entry must reference only artifacts, formal_targets, "
                "proof_bank_obligation_requests, lemma_dependency_plan entries, or "
                "source_to_bridge_premise_derivation_candidates objects that this same "
                "packet actually emits. If no concrete source_to_bridge candidate is "
                "emitted, no next_actions field may name "
                "source_to_bridge_premise_derivation_candidates or ask AgentRuntime/"
                "AXLE/local Lean to execute one."
            )
            if repeated_packet_failure:
                instructions.append(
                    "Repeated next_action_reference_contract failure: prefer deleting "
                    "the phantom executable next_actions entry entirely and record the "
                    "missing work in gap_taxonomy, lemma_dependency_plan, or "
                    "proof_bank_obligation_requests. Do not create a placeholder "
                    "source_to_bridge_premise_derivation_candidates object just to "
                    "satisfy next_actions."
                )
        if has_expected_status_validation:
            instructions.append(
                "Mandatory expected-status repair: every generated Lean candidate in "
                "formal_targets or source_to_bridge_premise_derivation_candidates must "
                "set expected_status=NEEDS_KERNEL_CHECK. Use FORMAL_GAP only for an "
                "unrepaired source-theorem target with no Lean sketch."
            )
        if has_hole_validation:
            instructions.append(
                "Mandatory proof-hole packet repair: remove `sorry`, `admit`, `by?`, "
                "`exact?`, and placeholder proof holes from Lean source; emit a complete "
                "candidate or an explicit FORMAL_GAP."
            )
            if (
                target_shape_contract_active
                and not source_theorem_candidate_materialization_contract
            ):
                instructions.append(
                    "Mandatory source-theorem proof-hole reroute: do not emit another "
                    "broad formal_targets NEEDS_KERNEL_CHECK theorem unless the Lean "
                    "sketch has a complete no-hole proof and preserves the supplied "
                    "task-bound target_shape_contract. If you cannot provide that proof, "
                    "set the source theorem formal target to expected_status=FORMAL_GAP "
                    "with no Lean sketch, then route smaller support work through "
                    "source_to_bridge_premise_derivation_candidates, lemma_dependency_plan, "
                    "or proof_bank_obligation_requests. Do not replace the source theorem "
                    "with a helper lemma in formal_targets."
                )
                if repeated_packet_failure:
                    instructions.append(
                        "Repeated source-theorem proof-hole escape hatch: emit the source "
                        "theorem formal_targets entry as expected_status=FORMAL_GAP "
                        "with an empty lean_statement_sketch. To keep capability-eval "
                        "Lean tooling live, you may additionally emit exactly one "
                        "narrow support/helper formal_targets entry with "
                        "expected_status=NEEDS_KERNEL_CHECK and "
                        "source_theorem_target_provenance.source_theorem_target_known=false. "
                        "That helper must not be described as the source theorem, must "
                        "avoid `sorry`/`admit`/`by?`/`exact?`, and remains diagnostic "
                        "Lean evidence only until AgentRuntime checks it."
                    )
        if has_target_shape_validation:
            instructions.append(
                "Mandatory target-shape packet repair: formal_targets with "
                "NEEDS_KERNEL_CHECK must preserve the supplied task-bound objects, "
                "assumptions, quantifiers, and conclusion. Put narrower helpers in "
                "support/source-to-bridge channels instead."
            )
            if target_drift_repair_contract:
                instructions.append(
                    "Mandatory target-drift two-lane packet repair: follow "
                    "runtime_environment_feedback.target_drift_repair_contract. "
                    "The source_theorem_lane must be either a faithful task-bound "
                    "source theorem target or an expected_status=FORMAL_GAP source "
                    "theorem with empty Lean sketch. The support_lemma_lane is the "
                    "place for narrower helper work."
                )
            if repeated_packet_failure and target_shape_contract_active:
                instructions.append(
                    "Repeated target-shape failure escalation: do not emit any "
                    "formal_targets entry with expected_status=NEEDS_KERNEL_CHECK for the "
                    "source theorem in this repair. The source theorem formal_targets entry "
                    "must be expected_status=FORMAL_GAP with an empty Lean sketch and a "
                    "precise gap_taxonomy/next_actions explanation. If you have a smaller "
                    "helper or premise idea, put it only in "
                    "source_to_bridge_premise_derivation_candidates, lemma_dependency_plan, "
                    "or proof_bank_obligation_requests with exact provenance; do not claim "
                    "it as the source theorem."
                )
        if has_phantom_source_to_bridge_action:
            instructions.append(
                "Mandatory executable-work-item repair: remove every next_actions "
                "instruction that names source_to_bridge_premise_derivation_candidates "
                "unless the packet also includes the exact candidate object in "
                "source_to_bridge_premise_derivation_candidates with Lean source, "
                "expected_status=NEEDS_KERNEL_CHECK, and source-binding metadata. "
                "If no candidate can be emitted, keep the source theorem as "
                "FORMAL_GAP and write the missing work as gap_taxonomy, "
                "lemma_dependency_plan, or proof_bank_obligation_requests only."
            )
        if missing_anchors:
            instructions.append(
                "Mandatory semantic-anchor repair: the exact missing anchor names are "
                f"{missing_anchor_text}. Every emitted "
                "source_to_bridge_premise_derivation_candidates Lean source must contain "
                "each of these exact identifiers in executable Lean code outside comments. "
                "If you cannot reference all of them non-vacuously, emit no "
                "source_to_bridge_premise_derivation_candidates entry and instead put the "
                "specific semantic blocker in gap_taxonomy/next_actions."
            )
        if uninstantiated_adapter_binders:
            instructions.append(
                "Mandatory source-binding repair: the previous candidate put these "
                "adapter objects in theorem binders instead of deriving them from exact "
                f"source binders: {uninstantiated_binder_text}. Do not include these "
                "identifiers as theorem parameters, implicit parameters, or assumptions "
                "in source_to_bridge_premise_derivation_candidates. Define them inside "
                "the candidate from exact source hypotheses, or emit no candidate and "
                "record the semantic blocker in gap_taxonomy/next_actions."
            )
        if missing_source_binding_contract_metadata:
            instructions.append(
                "Mandatory source-binding metadata repair: every emitted "
                "source_to_bridge_premise_derivation_candidates entry must copy one "
                "source_to_bridge_premise_derivation_candidate_request_id/object or one "
                "source_to_bridge_grouped_premise_derivation_candidate_request_id/object "
                "from source_to_bridge_candidate_request_shortcuts or "
                "proof_bank_runtime_memory_summary/runtime_environment_feedback. "
                "If you cannot copy that runtime memory request metadata exactly, emit "
                "no source_to_bridge_premise_derivation_candidates entry and report the "
                "metadata blocker in gap_taxonomy/next_actions."
            )
        if repeated_packet_failure:
            instructions.append(
                "Repeated packet-validation escalation: the previous Formalizer repair "
                "attempt still failed local packet validation. Do not try another broad "
                "candidate packet. Emit at most one narrow candidate only if all required "
                "source-binding metadata and semantic anchors can be copied exactly from "
                "runtime memory. Otherwise emit no Lean candidate and return an "
                "expected_status=FORMAL_GAP target plus gap_taxonomy/next_actions naming "
                "the precise validator blocker for ProofEngineer/Architect rerouting."
            )
    if feedback_failure in {
        "formalizer_lean_candidate_precheck_rejected",
        "formalizer_lean_candidate_local_lean_failed",
    }:
        lean_retry_depth = _feedback_int(
            runtime_environment_feedback.get(
                "formalizer_lean_repair_retry_depth", 0
            )
        )
        repeated_lean_candidate_failure = bool(
            runtime_environment_feedback.get(
                "repeated_formalizer_lean_candidate_failure", False
            )
            or lean_retry_depth > 0
        )
        candidate_diagnostics = [
            row
            for row in runtime_environment_feedback.get("candidate_diagnostics", [])
            or []
            if isinstance(row, Mapping)
        ]
        precheck_text = " ".join(
            str(error)
            for row in candidate_diagnostics
            for error in row.get("precheck_errors", []) or []
        ).lower()
        local_lean_text = " ".join(
            " ".join(
                [
                    str(row.get("local_lean_exit_status", "") or ""),
                    str(row.get("local_lean_stdout_excerpt", "") or ""),
                    str(row.get("local_lean_stderr_excerpt", "") or ""),
                ]
            )
            for row in candidate_diagnostics
        ).lower()
        candidate_source_text = " ".join(
            str(row.get("lean_source_excerpt", "") or "")
            for row in candidate_diagnostics
        ).lower()
        target_shape_contract = runtime_environment_feedback.get(
            "target_shape_contract",
            {},
        )
        target_drift_repair_contract = runtime_environment_feedback.get(
            "target_drift_repair_contract",
            {},
        )
        has_target_drift = "source-theorem target drift" in precheck_text or (
            isinstance(target_shape_contract, Mapping)
            and str(target_shape_contract.get("contract_kind", "") or "")
            == "source_theorem_target_preservation"
        )
        has_timeout = "timeout" in local_lean_text
        has_proof_hole = "exact?" in precheck_text or "by?" in precheck_text
        has_formal_gap_placeholder = (
            "formal_gap" in precheck_text or "formal_gap" in candidate_source_text
        )
        has_missing_import = (
            "object file" in local_lean_text
            and (".olean" in local_lean_text or "does not exist" in local_lean_text)
        ) or "unknown module" in local_lean_text or "imports unavailable module" in precheck_text
        instructions.append(
            "If runtime_environment_feedback reports a Formalizer Lean candidate "
            "precheck or local Lean failure, repair that exact generated Lean "
            "candidate before proposing new proof-bank work. Keep the candidate "
            "non-vacuous, tied to the statistical theorem/subclaim, and do not claim "
            "kernel verification. If a faithful candidate is not feasible, emit a "
            "FORMAL_GAP formal target and explain the precise blocker instead of "
            "weakening the theorem."
        )
        if runtime_environment_feedback.get("local_lean_repair_contract"):
            local_lean_repair_contract = runtime_environment_feedback.get(
                "local_lean_repair_contract",
                {},
            )
            instructions.append(
                "Local-Lean repair contract is mandatory: satisfy "
                "runtime_environment_feedback.local_lean_repair_contract before "
                "emitting another NEEDS_KERNEL_CHECK candidate. For parser/import/API "
                "or type errors, repair the exact diagnostic first. If the full source "
                "theorem cannot be repaired using known local APIs, emit the source "
                "theorem as expected_status=FORMAL_GAP and route a smaller support "
                "lemma or premise-derivation task instead of regenerating another "
                "broad theorem."
            )
            if isinstance(local_lean_repair_contract, Mapping):
                unknown_identifiers = [
                    str(value).strip()
                    for value in local_lean_repair_contract.get(
                        "unknown_identifiers",
                        [],
                    )
                    or []
                    if str(value).strip()
                ]
                if unknown_identifiers:
                    instructions.append(
                        "Mandatory unknown-identifier repair: do not reference these "
                        "unknown Lean constants/identifiers again: "
                        + ", ".join(unknown_identifiers[:8])
                        + ". Replace them with verified local project declarations, "
                        "derive the fact from known primitives, or emit a FORMAL_GAP "
                        "naming the missing API/dependency."
                    )
                blocked_import_prefixes = _blocked_import_prefixes_for_prompt(
                    local_lean_repair_contract
                )
                if blocked_import_prefixes:
                    quoted_prefixes = ", ".join(
                        f"`{value}`" for value in blocked_import_prefixes[:8]
                    )
                    instructions.append(
                        "Mandatory unavailable-import-prefix repair: local Lean "
                        f"reported unknown/unavailable module prefix(es): {quoted_prefixes}. "
                        "Do not import any blocked prefix or submodule in the next "
                        "candidate. Use no imports, an import already verified in this "
                        "same configured Lake project, or emit a FORMAL_GAP/dependency "
                        "blocker instead of retrying the same module path."
                    )
                if local_lean_repair_contract.get("mathlib_import_unavailable"):
                    instructions.append(
                        "Mandatory Mathlib-root repair: this configured Lean environment "
                        "reported the umbrella import `import Mathlib` as unavailable. "
                        "Do not retry that umbrella import. This is not by itself proof "
                        "that every `Mathlib.*` submodule is unavailable: use only a "
                        "narrow module import already verified by runtime/precheck, or "
                        "a listed suggested_import_replacement. If the source theorem "
                        "still needs missing measure/probability APIs, keep it as "
                        "expected_status=FORMAL_GAP and name the exact missing import/"
                        "API. Any revised executable candidate must preserve its typed "
                        "target lineage and return through the configured Lean compiler."
                    )
                diagnostic_classes = {
                    str(value).strip()
                    for value in local_lean_repair_contract.get(
                        "diagnostic_classes",
                        [],
                    )
                    or []
                    if str(value).strip()
                }
                if diagnostic_classes & {
                    "lean_unknown_tactic",
                    "lean_typeclass_synthesis_failed",
                }:
                    instructions.append(
                        "Mandatory compiler-diagnostic repair: consume the exact "
                        "unknown-tactic/typeclass diagnostics, available imports, "
                        "retrieved local declarations/instances, and Lean proof state. "
                        "Generate a revised proof and rerun Lean; do not substitute a "
                        "runtime-authored tactic or typeclass recipe."
                    )
                verified_narrow_imports = [
                    str(value).strip()
                    for value in local_lean_repair_contract.get(
                        "verified_narrow_imports",
                        [],
                    )
                    or []
                    if str(value).strip()
                ]
                if verified_narrow_imports:
                    instructions.append(
                        "Mandatory verified-narrow-import repair: runtime/precheck "
                        "already verified these narrow module imports in the configured "
                        "Lake project: "
                        + ", ".join(
                            f"`{value}`" for value in verified_narrow_imports[:8]
                        )
                        + ". If the repaired candidate needs those APIs, import one of "
                        "these modules exactly; otherwise use no import or emit a "
                        "FORMAL_GAP. Do not retry `import Mathlib`."
                    )
                if local_lean_repair_contract.get("repeated_syntax_failure"):
                    instructions.append(
                        "Mandatory compiler-feedback repair: consume the previous "
                        "Lean parser/LSP diagnostics verbatim, revise the candidate, "
                        "and rerun the configured Lean environment. Do not replay the "
                        "identical failed artifact and do not impose a Python-side "
                        "ASCII, Unicode, notation, API, or tactic whitelist."
                    )
        if has_target_drift:
            instructions.append(
                "Mandatory source-theorem target-preservation repair: the previous "
                "candidate was rejected for source-theorem target drift. Preserve "
                "the source theorem's task-bound objects, assumptions, quantifiers, "
                "conclusion, and semantic alignment constraints. Do not replace it "
                "with a standalone arithmetic, monotonicity, typing, or helper lemma "
                "in formal_targets. Put helper lemmas in "
                "lemma_dependency_plan/proof_bank requests, not as the claimed source "
                "theorem candidate."
            )
            instructions.append(
                "Target-drift fail-closed rule: do not satisfy capability-eval by "
                "placing a narrower helper in formal_targets. If you cannot "
                "emit a faithful source-theorem NEEDS_KERNEL_CHECK candidate, emit the "
                "source theorem as expected_status=FORMAL_GAP with an empty Lean sketch. "
                "Only emit a smaller executable Lean candidate through "
                "source_to_bridge_premise_derivation_candidates when exact source-binding "
                "metadata and semantic anchors are present; otherwise report the blocker "
                "instead of inventing a misaligned formal target."
            )
            if runtime_environment_feedback.get("target_shape_contract"):
                instructions.append(
                    "Target-shape contract is mandatory: copy and satisfy "
                    "runtime_environment_feedback.target_shape_contract when emitting "
                    "formal_targets with expected_status=NEEDS_KERNEL_CHECK. If you only "
                    "have a helper lemma matching candidate_reroute_options, do not claim "
                    "it as the source theorem; emit the source theorem target as "
                    "expected_status=FORMAL_GAP and route the helper separately."
                )
            if isinstance(target_drift_repair_contract, Mapping) and target_drift_repair_contract:
                instructions.append(
                    "Mandatory target-drift two-lane repair: follow "
                    "runtime_environment_feedback.target_drift_repair_contract exactly. "
                    "Use source_theorem_lane only for a faithful source theorem target "
                    "that preserves target_shape_contract, or fail closed there with "
                    "expected_status=FORMAL_GAP and an empty Lean sketch. Use "
                    "support_lemma_lane for narrower helper work; never "
                    "put support_lemma_lane work in formal_targets as a source theorem "
                    "NEEDS_KERNEL_CHECK candidate."
                )
        if has_timeout:
            instructions.append(
                "Mandatory local-Lean timeout repair: the previous candidate reached "
                "local Lean but timed out. Prefer narrow imports and local namespaces "
                "over `import Mathlib`; keep the theorem statement small enough for "
                "local checking, but do not simplify away the source theorem's "
                "task-bound conclusion. If preserving the faithful theorem "
                "requires library work, return a FORMAL_GAP with a minimal dependency "
                "plan instead of a weaker theorem."
            )
            if "import mathlib" in candidate_source_text:
                instructions.append(
                    "Mandatory timeout scope-down repair: do not retry the same large "
                    "full source theorem with `import Mathlib`. Either emit the source "
                    "theorem as expected_status=FORMAL_GAP and route smaller support "
                    "work, or emit one compact Lean candidate with narrow imports that "
                    "uses an already identified named premise and proves only the "
                    "corresponding local dependency. If the "
                    "needed source-to-bridge premise still lacks explicit semantic "
                    "anchors, emit a source_to_bridge_premise_derivation_candidates "
                    "work item with copied source-binding metadata instead of another "
                    "broad NEEDS_KERNEL_CHECK theorem."
                )
        if has_missing_import:
            instructions.append(
                "Mandatory import repair: local Lean reported a missing module/object "
                "file. Do not import guessed Mathlib module paths or retry any module "
                "prefix that local Lean reported as unknown. Prefer no imports, imports "
                "already verified in the configured project, or a FORMAL_GAP/dependency "
                "blocker. If the needed module is unavailable, report the dependency as "
                "a FORMAL_GAP outside Lean source rather than inventing an import."
            )
        if has_proof_hole:
            instructions.append(
                "Mandatory proof-hole repair: do not use `exact?`, `by?`, `sorry`, "
                "`admit`, or exploratory tactic holes in Lean statement sketches. "
                "Return a complete candidate or an explicit FORMAL_GAP."
            )
        if has_formal_gap_placeholder:
            instructions.append(
                "Mandatory FORMAL_GAP placeholder repair: never place identifiers such "
                "as `FORMAL_GAP_*` inside Lean source. If a theorem cannot be proved "
                "yet, set expected_status=FORMAL_GAP and put the missing lemma, import, "
                "or semantic blocker in gap_taxonomy/next_actions instead of emitting "
                "a fake Lean constant."
            )
        if repeated_lean_candidate_failure:
            instructions.append(
                "Repeated Lean-candidate compiler repair: a prior generated candidate "
                "failed runtime evidence checks or the configured Lean environment. "
                "Consume the exact diagnostics and proof state, preserve the target and "
                "lineage, generate a revised candidate, and rerun Lean. Do not replay an "
                "identical artifact or replace compiler feedback with a Python-authored "
                "tactic/grammar policy. Emit expected_status=FORMAL_GAP only for a real "
                "semantic or dependency blocker, and never treat compiler feedback as "
                "proof evidence."
            )
    if proof_memory_summary.get("proof_bank_bridge_catalog_exhausted_by_memory"):
        instructions.append(
            "If proof_bank_runtime_memory_summary says "
            "proof_bank_bridge_catalog_exhausted_by_memory=true, do not spend the packet "
            "on more bridge-obligation requests; make the main formal target the "
            "theorem-level reduction closure for the listed remaining_theorem_goal_ids."
        )
    if (
        mode == "source_theorem_exact_semantic_definition_structural_reformulation"
        or proof_memory_summary.get(
            "source_theorem_exact_semantic_definition_structural_reformulation_required"
        )
        or "structural_reformulate_exact_semantic_definition_with_pf_bv"
        in integration_action
    ):
        instructions.append(
            "For source_theorem_exact_semantic_definition_structural_reformulation, "
            "treat repeated Lean API/syntax/typeclass hard-negative feedback as a "
            "semantic-design blocker. You must emit pseudo_formal_proof_packets that "
            "decompose the exact semantic-definition obligation into source-anchored "
            "blocks before proposing another Lean definition. Route residual blocks "
            "using runtime-consumed fields, not a prose-only target_lane label: use "
            "faithfulness_status=faithful with "
            "lean_feasibility=needs_semantic_definition for "
            "source_theorem_exact_semantic_definition work, plus non-empty "
            "semantic_primitive_requirements naming the primitive/source object "
            "that source lookup must define; use "
            "faithfulness_status=faithful with lean_feasibility=needs_rag for "
            "lean_rag library grounding; use faithfulness_status=faithful plus "
            "non-empty semantic_primitive_requirements for source_to_bridge "
            "primitive/premise work. Generic needs_review/not_run blocks alone only "
            "create review rows and fail required PF/BV activation. Do not "
            "directly retry sibling Lean APIs, guessed imports, or previously rejected "
            "syntax fragments; reformulate around project-verified primitives, explicit "
            "parameters, or declare the missing semantic primitive/formal library gap. "
            "If source_theorem_exact_candidate_repair_diagnostics includes "
            "response_validation_feedback.unverified_required_imports, treat those "
            "module names as hard-negative rejected imports: do not reuse them as Lean "
            "candidate required_imports, and cite the blocked import/API as a PF/BV "
            "work-order constraint for lean_rag or exact semantic-definition grounding "
            "instead of retrying the import."
        )
    if (
        mode == "source_theorem_exact_semantic_definition_repair"
        or proof_memory_summary.get("source_theorem_exact_semantic_definition_repair_required")
        or "repair_reviewed_exact_semantic_definitions" in integration_action
    ):
        instructions.append(
            "For source_theorem_exact_semantic_definition_repair, make the main formal "
            "target a reviewed/imported exact semantic definition repair for listed "
            "placeholder symbols and semantic_definition_risks; do not attempt "
            "source-theorem proof-body search or promotion until that semantic-definition "
            "repair passes local Lean/AXLE. If diagnostics include proof_body_gate_status="
            "PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED or failure_classification="
            "proof_body_reached_semantic_alignment_unreviewed, treat that as a theorem/"
            "semantic-definition repair gate and propose reviewed semantics, an explicit "
            "tie policy/no-tie assumption, or theorem-assumption revision."
        )
    if (
        mode == "source_theorem_exact_proof_body_repair"
        or (
            proof_memory_summary.get("source_theorem_exact_candidate_requires_repair")
            and not source_theorem_candidate_materialization_required
            and not proof_memory_summary.get(
                "source_to_bridge_metadata_authoring_required"
            )
        )
        or "repair_exact_source_theorem_candidate_proof_body" in integration_action
    ):
        instructions.append(
            "For source_theorem_exact_proof_body_repair, keep the exact source theorem "
            "target fixed and consume source_theorem_exact_proof_body_repair_diagnostics "
            "as a lineage-bound ProofEngineer task. When proof_body_repair_scope is "
            "replace_entire_exact_declaration_proof_body, preserve target_theorem_statement "
            "exactly and replace the complete proof after `:= by`; use a provided "
            "target_declaration_source_excerpt when it is source-bound, otherwise use "
            "candidate_source_excerpt plus target_lean_declaration and compiler feedback. "
            "Do not ask Python to parse a Lean declaration to manufacture missing context. "
            "proof_body_goal_excerpt is a residual subgoal produced while "
            "elaborating the current proof and may be nested inside a bad tactic term; do "
            "not silently change the theorem statement to that residual goal. Emit a "
            "complete exact-declaration formal_targets candidate for local Lean/AXLE, a "
            "smaller lineage-bound lemma/dependency request, or a typed mathematical/"
            "formal-library blocker. If "
            "source_theorem_exact_proof_body_verified_adapter_context_insufficient=true, "
            "preserve the kernel-verified adapter artifact/declaration as context and "
            "repair the exact source theorem proof body against the true Lean goal shape."
        )
    if proof_memory_summary.get(
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
    ):
        open_targets = [
            str(value).strip()
            for value in proof_memory_summary.get(
                "source_theorem_exact_proof_body_gate_open_target_names", []
            )
            or []
            if str(value).strip()
        ]
        target_clause = (
            " Targets: " + ", ".join(open_targets[:5]) + "."
            if open_targets
            else ""
        )
        instructions.append(
            "The exact source proof-body gate is open for kernel-eligible repair: "
            "a local Lean proof-body goal was reached, semantic blockers are empty, "
            "and source_theorem_kernel_evidence_eligible=true, but "
            "source_theorem_kernel_verified is still false."
            + target_clause
            + " Do not route this target back to exact semantic-definition review "
            "unless new semantic_alignment_blockers, verifier_gate_blockers, known_gaps, "
            "or semantic_definition_risks are present. Continue with exact proof-body "
            "repair or the required source-to-bridge adapter using proof_body_goal_excerpt "
            "and proof_body_attempt_summaries, then require local Lean/AXLE kernel "
            "verification before claiming proof evidence."
        )
    if (
        mode == "source_theorem_proof_body_adapter_required"
        or proof_memory_summary.get("source_theorem_proof_body_adapter_required")
    ):
        instructions.append(
            "For source_theorem_proof_body_adapter_required, make the main formal target "
            "a concrete source-to-bridge/reduction adapter candidate, not the source theorem "
            "itself and not a vacuous True theorem. Preserve source_theorem_target_provenance "
            "and `source_theorem_target_provenance.target_lean_declaration` as the exact "
            "source theorem declaration identifier only; do not put a full Lean theorem "
            "statement in that field. Name the adapter theorem `<source theorem declaration>"
            "_source_to_bridge_adapter`, use proof_body_goal_excerpt, "
            "proof_body_attempt_summaries, memory_kernel_verified_theorem_reduction_closure_"
            "signature_excerpts, and do not guess closure theorem fields. If "
            "verified_source_to_bridge_premise_derivation_signature_excerpts are "
            "present, consume those exact checked theorem headers as dependency "
            "context for the adapter instead of inventing new bridge premise binders."
        )
    if proof_memory_summary.get(
        "source_theorem_proof_body_adapter_unproven_bridge_premises_required"
    ):
        instructions.append(
            "If source_theorem_proof_body_adapter_unproven_bridge_premises_required=true, "
            "the listed source_theorem_proof_body_adapter_unproven_bridge_premise_names "
            "are forbidden as new adapter binder assumptions. Do not write an adapter "
            "that takes those names as inputs; derive each premise from exact source "
            "hypotheses, retrieved declarations, derivation anchors, and the task's "
            "assumption ledger, or report the blocker."
        )
    if (
        mode == "source_to_bridge_premise_derivation_required"
        or _formalizer_bool_like(
            proof_memory_summary.get("source_to_bridge_premise_derivation_required")
        )
    ):
        instructions.append(
            "For source_to_bridge_premise_derivation_required, make the main formal target "
            "one or more concrete source-to-bridge premise derivation candidates, not the "
            "full source theorem and not another generic adapter. Put concrete Lean attempts "
            "in source_to_bridge_premise_derivation_candidates, derive them from exact source "
            "hypotheses, use source_to_bridge_premise_derivation_candidate_request or "
            "source_to_bridge_grouped_premise_derivation_candidate_request exactly, and "
            "prefer one source_to_bridge_premise_derivation_candidates object when a grouped "
            "adapter_instantiation_group_id is supplied. If "
            "source_to_bridge_candidate_request_shortcuts is nonempty, copy one of its "
            "copy_this_*_request_id and copy_this_*_request objects into every emitted "
            "candidate. Copy the exact premise_candidate_declaration_name for a single "
            "request or premise_candidate_declaration_names in premise order for a "
            "grouped request; declaration identity is structured data and is never "
            "inferred by parsing generated Lean. Use only those exact source binders "
            "and semantic anchors from "
            "runtime memory; do not introduce new assumptions or adapter objects as "
            "free theorem parameters. If a prior diagnostic says "
            "premise_candidate_references_semantic_anchor=false or lists "
            "missing_premise_semantic_anchor_binder_names, reference each missing binder "
            "name in the Lean proof body outside comments and do not repeat a candidate "
            "that only mentions those binders in the theorem header, a comment, or an "
            "unused assumption. Do not return a `fail_if_success`, `True := by trivial`, "
            "or comment-only skeleton. Return a non-vacuous Lean candidate or report the "
            "missing semantic primitive with failure_classification="
            "premise_derivation_candidate_missing_nonvacuous_source. If the prior "
            "candidate was not evidence-eligible, treat local Lean skipped as a "
            "validator outcome, not as proof-search evidence; repair the evidence "
            "eligibility blocker before asking Lean to check the candidate."
        )
    return instructions


def _is_initial_formal_source_grounding_context(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    if str(value.get("context_kind", "") or "") != (
        "task_bound_formal_source_grounding"
    ):
        return False
    repair_keys = (
        "candidate_diagnostics",
        "proof_state_trace_rag",
        "external_proof_search_result",
        "candidate_rerun_specs",
        "unknown_identifiers",
    )
    if any(value.get(key) not in (None, "", [], {}) for key in repair_keys):
        return False
    query_roles = {
        str(group.get("query_role", "") or "")
        for group in value.get("formal_source_grounding_hits", []) or []
        if isinstance(group, Mapping)
    }
    return not query_roles or query_roles == {"initial_formalization_context"}


def _compact_proofengineer_context_for_prompt(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    if (
        _is_initial_formal_source_grounding_context(value)
        and value.get("formal_source_grounding_hits")
    ):
        return {
            "context_kind": "task_bound_formal_source_grounding",
            "formal_source_grounding_hits": (
                compact_formal_source_grounding_hits_for_prompt(
                    value.get("formal_source_grounding_hits")
                )
            ),
        }
    compact = _compact_value(value)
    return compact if isinstance(compact, dict) else {}


def _compact_formalizer_environment_feedback(
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(feedback, Mapping):
        return {}
    input_summary = (
        feedback.get("input_summary", {})
        if isinstance(feedback.get("input_summary", {}), Mapping)
        else {}
    )
    target_shape_contract = _feedback_target_shape_contract(
        feedback,
        input_summary=input_summary,
    )
    local_lean_repair_contract = _feedback_local_lean_repair_contract(
        feedback,
        input_summary=input_summary,
    )
    candidate_reroute_options = _feedback_candidate_reroute_options(
        feedback,
        input_summary=input_summary,
        target_shape_contract=target_shape_contract,
    )
    target_drift_repair_contract = _feedback_target_drift_repair_contract(
        feedback,
        input_summary=input_summary,
        target_shape_contract=target_shape_contract,
    )
    theory_trace_downstream_alignment_feedback = (
        _theory_trace_downstream_alignment_feedback(feedback)
    )
    payload = {
        "architect_evidence_contract": _compact_value(
            feedback.get("architect_evidence_contract", {})
        ),
        "runtime_requested_evidence_contract": _compact_value(
            feedback.get("runtime_requested_evidence_contract", {})
        ),
        "architect_recommended_research_path": _compact_value(
            feedback.get("architect_recommended_research_path", "")
        ),
        "architect_formal_verification_policy": _compact_value(
            feedback.get("architect_formal_verification_policy", "")
        ),
        "architect_subsystem_acceptance_gate": _compact_value(
            feedback.get("architect_subsystem_acceptance_gate", "")
        ),
        "feedback_type": _compact_value(
            feedback.get("feedback_type", "")
            or input_summary.get("trigger", "")
            or "formalizer_validation_feedback"
        ),
        "repair_owner_agent": _compact_value(
            feedback.get("repair_owner_agent", "")
            or input_summary.get("repair_owner_agent", "")
        ),
        "formalization_gap_planner_action_work_order": _compact_value(
            feedback.get("formalization_gap_planner_action_work_order", {})
            or input_summary.get(
                "formalization_gap_planner_action_work_order",
                {},
            )
        ),
        "formalization_gap_planner_action_work_order_id": _compact_value(
            feedback.get("formalization_gap_planner_action_work_order_id", "")
            or input_summary.get(
                "formalization_gap_planner_action_work_order_id",
                "",
            )
        ),
        "formalization_gap_planner_action_work_order_hash": _compact_value(
            feedback.get("formalization_gap_planner_action_work_order_hash", "")
            or input_summary.get(
                "formalization_gap_planner_action_work_order_hash",
                "",
            )
        ),
        "formal_target_semantic_review": compact_semantic_review_feedback(
            feedback,
            expected_feedback_type="formal_target_semantic_review_feedback",
        ),
        "proofengineer_repair_context": _compact_proofengineer_context_for_prompt(
            feedback.get("proofengineer_repair_context", {})
            or input_summary.get("proofengineer_repair_context", {})
        ),
        "failure_classification": _compact_value(
            feedback.get("failure_classification", "")
            or input_summary.get("failure_classification", "")
        ),
        "validation_label": _compact_value(
            feedback.get("validation_label", "")
            or input_summary.get("validation_label", "")
        ),
        "validation_errors": _compact_value(
            feedback.get("validation_errors", [])
            or input_summary.get("validation_errors", [])
        ),
        "validation_repair_directives": _compact_value(
            feedback.get("validation_repair_directives", [])
            or input_summary.get("validation_repair_directives", [])
        ),
        "pseudo_formalization_required": bool(
            feedback.get("pseudo_formalization_required", False)
            or input_summary.get("pseudo_formalization_required", False)
        ),
        "requires_pseudo_formalization": bool(
            feedback.get("requires_pseudo_formalization", False)
            or input_summary.get("requires_pseudo_formalization", False)
        ),
        "pseudo_formalization_required_reason": _compact_value(
            feedback.get("pseudo_formalization_required_reason", "")
            or input_summary.get("pseudo_formalization_required_reason", "")
        ),
        "pseudo_formalization_required_missing_work_order_rows": bool(
            feedback.get(
                "pseudo_formalization_required_missing_work_order_rows",
                False,
            )
            or input_summary.get(
                "pseudo_formalization_required_missing_work_order_rows",
                False,
            )
        ),
        "pseudo_formalization_required_invalid_packets": bool(
            feedback.get(
                "pseudo_formalization_required_invalid_packets",
                False,
            )
            or input_summary.get(
                "pseudo_formalization_required_invalid_packets",
                False,
            )
        ),
        "pseudo_formalization_required_no_lane_routable_rows": bool(
            feedback.get(
                "pseudo_formalization_required_no_lane_routable_rows",
                False,
            )
            or input_summary.get(
                "pseudo_formalization_required_no_lane_routable_rows",
                False,
            )
        ),
        "pseudo_formalization_validation_issue_summary": _compact_value(
            feedback.get("pseudo_formalization_validation_issue_summary", {})
            or input_summary.get(
                "pseudo_formalization_validation_issue_summary",
                {},
            )
        ),
        "pseudo_formalization_validation_issue_repair_actions": _compact_value(
            feedback.get(
                "pseudo_formalization_validation_issue_repair_actions",
                [],
            )
            or input_summary.get(
                "pseudo_formalization_validation_issue_repair_actions",
                [],
            )
        ),
        "pseudo_formalization_repair_contract": _compact_value(
            feedback.get("pseudo_formalization_repair_contract", {})
            or input_summary.get("pseudo_formalization_repair_contract", {})
        ),
        "attempts": _compact_value(
            feedback.get("attempts", "")
            or input_summary.get("attempts", "")
        ),
        "formalizer_packet_repair_retry_depth": _compact_value(
            feedback.get("formalizer_packet_repair_retry_depth", "")
            or input_summary.get("formalizer_packet_repair_retry_depth", "")
        ),
        "repeated_formalizer_packet_validation_failure": bool(
            feedback.get("repeated_formalizer_packet_validation_failure", False)
            or input_summary.get(
                "repeated_formalizer_packet_validation_failure", False
            )
        ),
        "formalizer_lean_repair_retry_depth": _compact_value(
            feedback.get("formalizer_lean_repair_retry_depth", "")
            or input_summary.get("formalizer_lean_repair_retry_depth", "")
        ),
        "repeated_formalizer_lean_candidate_failure": bool(
            feedback.get("repeated_formalizer_lean_candidate_failure", False)
            or input_summary.get(
                "repeated_formalizer_lean_candidate_failure", False
            )
        ),
        "formalizer_proof_state_repair_round": _compact_value(
            feedback.get("formalizer_proof_state_repair_round", "")
            or input_summary.get("formalizer_proof_state_repair_round", "")
        ),
        "next_formalizer_proof_state_repair_round": _compact_value(
            feedback.get("next_formalizer_proof_state_repair_round", "")
            or input_summary.get(
                "next_formalizer_proof_state_repair_round",
                "",
            )
        ),
        "max_formalizer_proof_state_repair_rounds": _compact_value(
            feedback.get("max_formalizer_proof_state_repair_rounds", "")
            or input_summary.get(
                "max_formalizer_proof_state_repair_rounds",
                "",
            )
        ),
        "formalization_manifest_id": _compact_value(
            feedback.get("formalization_manifest_id", "")
            or input_summary.get("formalization_manifest_id", "")
        ),
        "proof_state_feedback_manifest_id": _compact_value(
            feedback.get("proof_state_feedback_manifest_id", "")
            or input_summary.get("proof_state_feedback_manifest_id", "")
        ),
        "candidate_proof_state_feedback_manifest_id": _compact_value(
            feedback.get("candidate_proof_state_feedback_manifest_id", "")
            or input_summary.get(
                "candidate_proof_state_feedback_manifest_id",
                "",
            )
        ),
        "candidate_materialization_manifest_id": _compact_value(
            feedback.get("candidate_materialization_manifest_id", "")
            or input_summary.get("candidate_materialization_manifest_id", "")
        ),
        "parent_formalizer_proof_state_feedback": _compact_value(
            feedback.get("parent_formalizer_proof_state_feedback", {})
            or input_summary.get("parent_formalizer_proof_state_feedback", {})
        ),
        "candidate_diagnostics": _compact_formalizer_candidate_diagnostics(
            feedback.get("candidate_diagnostics", [])
            or input_summary.get("candidate_diagnostics", [])
        ),
        "target_shape_contract": _compact_value(target_shape_contract),
        "target_drift_repair_contract": _compact_value(
            target_drift_repair_contract
        ),
        "next_action_reference_contract": _compact_value(
            feedback.get("next_action_reference_contract", {})
            or input_summary.get("next_action_reference_contract", {})
        ),
        "source_theorem_candidate_materialization_contract": _compact_value(
            feedback.get("source_theorem_candidate_materialization_contract", {})
            or input_summary.get("source_theorem_candidate_materialization_contract", {})
        ),
        "candidate_reroute_options": _compact_value(candidate_reroute_options),
        "local_lean_repair_contract": _compact_value(local_lean_repair_contract),
        "n_local_lean_checked": _compact_value(
            feedback.get("n_local_lean_checked", "")
            or input_summary.get("n_local_lean_checked", "")
        ),
        "n_local_lean_compiled": _compact_value(
            feedback.get("n_local_lean_compiled", "")
            or input_summary.get("n_local_lean_compiled", "")
        ),
        "missing_semantic_anchor_references": _compact_value(
            feedback.get("missing_semantic_anchor_references", [])
            or input_summary.get("missing_semantic_anchor_references", [])
        ),
        "source_to_bridge_premise_derivation_feedback": _compact_value(
            feedback.get("source_to_bridge_premise_derivation_feedback", {})
            or input_summary.get("source_to_bridge_premise_derivation_feedback", {})
        ),
        "source_to_bridge_premise_derivation_diagnostics": _compact_value(
            feedback.get("source_to_bridge_premise_derivation_diagnostics", [])
            or input_summary.get(
                "source_to_bridge_premise_derivation_diagnostics", []
            )
        ),
        "uninstantiated_adapter_object_binders": _compact_value(
            feedback.get("uninstantiated_adapter_object_binders", [])
            or input_summary.get("uninstantiated_adapter_object_binders", [])
        ),
        "missing_source_binding_contract_metadata": bool(
            feedback.get("missing_source_binding_contract_metadata", False)
            or input_summary.get("missing_source_binding_contract_metadata", False)
        ),
        "last_attempt_summary": _compact_value(
            feedback.get("last_attempt_summary", {})
            or input_summary.get("last_attempt_summary", {})
        ),
        "required_repair": _compact_value(
            feedback.get("required_repair", "")
            or feedback.get("target_behavior", "")
        ),
        "proof_evidence_status": _compact_value(
            feedback.get("proof_evidence_status", "")
        ),
        "boundary": _compact_value(
            feedback.get("boundary", "")
            or feedback.get("proof_evidence_boundary", "")
        ),
    }
    promotion_generation_fields = {
        "source_theorem_promotion_execution_id": (
            feedback.get("source_theorem_promotion_execution_id", "")
            or input_summary.get("source_theorem_promotion_execution_id", "")
        ),
        "source_theorem_promotion_generation_request_id": (
            feedback.get("source_theorem_promotion_generation_request_id", "")
            or input_summary.get(
                "source_theorem_promotion_generation_request_id",
                "",
            )
        ),
        "source_theorem_promotion_generation_request_hash": (
            feedback.get("source_theorem_promotion_generation_request_hash", "")
            or input_summary.get(
                "source_theorem_promotion_generation_request_hash",
                "",
            )
        ),
        "source_theorem_promotion_generation_request": (
            feedback.get("source_theorem_promotion_generation_request", {})
            or input_summary.get(
                "source_theorem_promotion_generation_request",
                {},
            )
        ),
    }
    if any(promotion_generation_fields.values()):
        payload.update(
            {
                key: _compact_value(value)
                for key, value in promotion_generation_fields.items()
            }
        )
    if theory_trace_downstream_alignment_feedback:
        payload["theory_trace_downstream_alignment_feedback"] = _compact_value(
            theory_trace_downstream_alignment_feedback
        )
    formal_blocker_resource_requests = (
        feedback.get("formal_blocker_resource_requests", [])
        or input_summary.get("formal_blocker_resource_requests", [])
    )
    if formal_blocker_resource_requests:
        payload["formal_blocker_resource_requests"] = (
            _compact_formal_blocker_resource_requests(
                _formal_blocker_resource_requests_with_exact_semantic_artifacts(
                    formal_blocker_resource_requests,
                    feedback=feedback,
                    input_summary=input_summary,
                )
            )
        )
    high_priority_agenda = (
        feedback.get("high_priority_agenda", [])
        or input_summary.get("high_priority_agenda", [])
    )
    if high_priority_agenda:
        payload["high_priority_agenda"] = _compact_rows(
            [
                row
                for row in high_priority_agenda
                if isinstance(row, Mapping)
            ],
            keys=(
                "id",
                "owner_subsystem",
                "trigger",
                "action",
                "acceptance_gate",
                "target_ids",
                "target_id",
                "formalization_gap_planner_bridge_id",
                "supporting_formalization_gap_planner_bridge_ids",
                "standalone_seed_artifact_id",
                "supporting_standalone_seed_artifact_ids",
                "formalization_gap_planner_handoff_id",
                "supporting_formalization_gap_planner_handoff_ids",
                "formalization_gap_planner_execution_contexts",
                "formalization_gap_planner_execution_plan_stage_ids",
                "standalone_seed_path",
                "target_intake_path",
                "target_intake_cli",
                "component_resource_registry_cli",
                "standalone_plan_cli",
                "llm_route_planner_prompt_cli",
                "llm_route_planner_live_cli",
                "reuse_smoke_cli",
                "recommended_llm_provider",
                "recommended_model_tier",
                "target_prover_family",
                "candidate_materialization_statuses",
                "failure_classifications",
                "recommended_formalizer_target_mode",
                "runtime_queue_status",
                "priority",
                "proof_evidence_status",
                "proof_boundary",
                "boundary",
            ),
            limit=5,
        )
    source_theorem_proof_body_adapter_feedback = (
        feedback.get("source_theorem_proof_body_adapter_feedback", {})
        or input_summary.get("source_theorem_proof_body_adapter_feedback", {})
    )
    if source_theorem_proof_body_adapter_feedback:
        payload["source_theorem_proof_body_adapter_feedback"] = _compact_value(
            source_theorem_proof_body_adapter_feedback
        )
    return {
        key: value
        for key, value in payload.items()
        if value not in (None, "", [], {}, False)
    }


def _compact_formalizer_candidate_diagnostics(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return _compact_rows(
        [row for row in value if isinstance(row, Mapping)],
        keys=(
            "candidate_id",
            "candidate_kind",
            "source_field",
            "artifact_path",
            "target_lean_file",
            "target_lean_line",
            "target_lean_column",
            "target_lean_declaration",
            "source_hash",
            "target_ids",
            "target_theorem_goal_ids",
            "target_theorem_name",
            "repair_target_identity_required",
            "repair_target_identity_binding_status",
            "repair_target_identity_binding_id",
            "repair_parent_candidate_id",
            "expected_target_lean_declaration",
            "actual_target_lean_declaration",
            "target_identity_mismatch_not_source_theorem",
            "target_identity_unbound_not_source_theorem",
            "target_identity_errors",
            "lean_source_excerpt",
            "precheck_status",
            "precheck_errors",
            "local_lean_attempted",
            "local_lean_compiled",
            "local_lean_exit_status",
            "local_lean_stdout_excerpt",
            "local_lean_stderr_excerpt",
            "local_lean_command",
            "local_lean_project",
            "local_lean_timeout",
            "local_lean_skipped_reason",
        ),
        limit=3,
    )


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
        "required_repair": (
            source.get("required_repair", "") or source.get("target_behavior", "")
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


def _feedback_target_shape_contract(
    feedback: Mapping[str, Any],
    *,
    input_summary: Mapping[str, Any],
) -> Mapping[str, Any]:
    explicit = feedback.get("target_shape_contract", {}) or input_summary.get(
        "target_shape_contract",
        {},
    )
    if isinstance(explicit, Mapping) and explicit:
        return explicit
    candidate_diagnostics = (
        feedback.get("candidate_diagnostics", [])
        or input_summary.get("candidate_diagnostics", [])
        or []
    )
    if not isinstance(candidate_diagnostics, list | tuple):
        candidate_diagnostics = []
    precheck_text = " ".join(
        str(error)
        for row in candidate_diagnostics
        if isinstance(row, Mapping)
        for error in row.get("precheck_errors", []) or []
    ).lower()
    target_drift_detected = "source-theorem target drift" in precheck_text
    if not target_drift_detected:
        return {}
    contract: dict[str, Any] = {
        "contract_kind": "source_theorem_target_preservation",
        "required_behavior": (
            "A formal target that claims NEEDS_KERNEL_CHECK for a known source theorem "
            "must preserve the source theorem conclusion shape. Do not replace it with "
            "a narrower helper lemma."
        ),
        "source_theorem_target_action": (
            "Use formal_targets for the known source theorem only when the Lean sketch "
            "preserves the required conclusion family; otherwise emit the source theorem "
            "as expected_status=FORMAL_GAP with an empty Lean sketch."
        ),
        "helper_lemma_action": (
            "Move narrower helper work to support channels such as "
            "source_to_bridge_premise_derivation_candidates, lemma_dependency_plan, "
            "proof_bank_obligation_requests, gap_taxonomy, or next_actions."
        ),
        "forbidden_output_action": (
            "Do not emit helper lemma work as a source-theorem formal_targets "
            "NEEDS_KERNEL_CHECK candidate."
        ),
        "allowed_support_channels": [
            "source_to_bridge_premise_derivation_candidates",
            "lemma_dependency_plan",
            "proof_bank_obligation_requests",
            "gap_taxonomy",
            "next_actions",
        ],
        "forbidden_replacement_shapes": [
            "narrow result that omits task-bound objects or assumptions",
            "result with weaker or different quantifiers",
            "typing lemma",
            "monotonicity lemma",
            "helper lemma without the source theorem conclusion",
        ],
        "if_not_feasible": (
            "Emit expected_status=FORMAL_GAP for the source theorem target and route "
            "helper lemmas separately through support-lemma/proof-bank channels."
        ),
        "fail_closed_source_theorem_formal_target": {
            "expected_status": "FORMAL_GAP",
            "lean_statement_sketch": "",
        },
    }
    return contract


def _feedback_candidate_reroute_options(
    feedback: Mapping[str, Any],
    *,
    input_summary: Mapping[str, Any],
    target_shape_contract: Mapping[str, Any],
) -> list[Any]:
    explicit = feedback.get("candidate_reroute_options", []) or input_summary.get(
        "candidate_reroute_options",
        [],
    )
    if isinstance(explicit, list | tuple) and explicit:
        return list(explicit)
    if not target_shape_contract:
        return []
    return [
        (
            "If the generated theorem is only a support/helper lemma, do not place it "
            "in formal_targets as the source theorem. Emit the source theorem as "
            "FORMAL_GAP and route the helper separately."
        )
    ]


def _feedback_target_drift_repair_contract(
    feedback: Mapping[str, Any],
    *,
    input_summary: Mapping[str, Any],
    target_shape_contract: Mapping[str, Any],
) -> Mapping[str, Any]:
    explicit = feedback.get("target_drift_repair_contract", {}) or input_summary.get(
        "target_drift_repair_contract",
        {},
    )
    if isinstance(explicit, Mapping) and explicit:
        return explicit
    if not target_shape_contract:
        return {}
    return {
        "contract_kind": "source_theorem_target_two_lane_repair",
        "source_theorem_lane": {
            "output_key": "formal_targets",
            "allowed_needs_kernel_check_shape": (
                "known source theorem preserving the required conclusion family"
            ),
            "fail_closed_shape": (
                "known source theorem expected_status=FORMAL_GAP with empty "
                "lean_statement_sketch"
            ),
        },
        "support_lemma_lane": {
            "allowed_output_keys": [
                "source_to_bridge_premise_derivation_candidates",
                "lemma_dependency_plan",
                "proof_bank_obligation_requests",
                "gap_taxonomy",
                "next_actions",
            ],
            "forbidden_output_key": (
                "formal_targets with source_theorem_target_known=true and "
                "expected_status=NEEDS_KERNEL_CHECK"
            ),
        },
        "acceptance_gate": (
            "Either preserve the source theorem target shape, or mark the source "
            "theorem as FORMAL_GAP and route helper work outside the source theorem slot."
        ),
    }


def _feedback_local_lean_repair_contract(
    feedback: Mapping[str, Any],
    *,
    input_summary: Mapping[str, Any],
) -> Mapping[str, Any]:
    explicit = feedback.get("local_lean_repair_contract", {}) or input_summary.get(
        "local_lean_repair_contract",
        {},
    )
    explicit_contract = without_legacy_python_lean_strategy_fields(
        explicit if isinstance(explicit, Mapping) else {}
    )
    candidate_diagnostics = (
        feedback.get("candidate_diagnostics", [])
        or input_summary.get("candidate_diagnostics", [])
        or []
    )
    if not isinstance(candidate_diagnostics, list | tuple):
        return explicit_contract
    precheck_text = " ".join(
        str(error)
        for row in candidate_diagnostics
        if isinstance(row, Mapping)
        for error in row.get("precheck_errors", []) or []
    )
    local_lean_text = " ".join(
        " ".join(
            [
                precheck_text,
                str(row.get("local_lean_exit_status", "") or ""),
                str(row.get("local_lean_stdout_excerpt", "") or ""),
                str(row.get("local_lean_stderr_excerpt", "") or ""),
            ]
        )
        for row in candidate_diagnostics
        if isinstance(row, Mapping)
    ).lower()
    if not local_lean_text.strip():
        return explicit_contract
    classes: list[str] = []
    if "unexpected token" in local_lean_text or "expected term" in local_lean_text:
        classes.append("lean_parser_or_syntax_error")
    if (
        "unknown module prefix" in local_lean_text
        or "no directory" in local_lean_text
        or "imports unavailable module" in local_lean_text
        or "imports unavailable umbrella module" in local_lean_text
    ):
        classes.append("lean_import_environment_missing")
    if (
        "unknown identifier" in local_lean_text
        or "unknown constant" in local_lean_text
        or "lean.unknownidentifier" in local_lean_text
    ):
        classes.append("lean_unknown_identifier")
    if "unknown tactic" in local_lean_text:
        classes.append("lean_unknown_tactic")
    if (
        "lean.synthinstancefailed" in local_lean_text
        or "failed to synthesize instance" in local_lean_text
    ):
        classes.append("lean_typeclass_synthesis_failed")
    if "type mismatch" in local_lean_text or "application type mismatch" in local_lean_text:
        classes.append("lean_type_mismatch")
    if not classes:
        classes.append("lean_local_check_failed")
    contract: dict[str, Any] = {
        "contract_kind": "formalizer_local_lean_repair",
        "diagnostic_classes": classes,
        "required_behavior": (
            "Repair the exact local Lean diagnostic. If the full source theorem is too "
            "large for a reliable repair, emit FORMAL_GAP and route a smaller support lemma."
        ),
    }
    unavailable_prefixes = _feedback_unavailable_import_prefixes(candidate_diagnostics)
    mathlib_root_import_unavailable = (
        "Mathlib" in unavailable_prefixes
        and _feedback_diagnostics_import_exact_module(
            candidate_diagnostics,
            "Mathlib",
        )
    )
    blocked_import_prefixes = [
        value
        for value in unavailable_prefixes
        if not (value == "Mathlib" and mathlib_root_import_unavailable)
    ]
    if blocked_import_prefixes:
        contract["blocked_import_prefixes"] = blocked_import_prefixes
        contract["blocked_import_repair_rule"] = (
            "Do not import any blocked prefix or submodule in the next candidate. "
            "Use no imports, an import already verified in this same configured "
            "Lake project, or emit a FORMAL_GAP/dependency blocker."
        )
    if mathlib_root_import_unavailable or "Mathlib" in unavailable_prefixes:
        contract["mathlib_import_unavailable"] = True
        contract["mathlib_root_import_unavailable"] = True
        contract["mathlib_repair_rule"] = (
            "Do not retry the umbrella import `import Mathlib` after local Lean "
            "reported the Mathlib root module unavailable. This does not block "
            "narrow `Mathlib.*` module imports that are verified in the configured "
            "Lake project or listed as suggested_import_replacements."
        )
    verified_narrow_imports = _feedback_verified_narrow_imports(candidate_diagnostics)
    if verified_narrow_imports:
        contract["verified_narrow_imports"] = verified_narrow_imports
        contract["verified_narrow_import_rule"] = (
            "If the next candidate needs Mathlib APIs after an umbrella-import "
            "rejection, import one of these verified narrow modules exactly, and "
            "only when it matches the dependency. Do not retry `import Mathlib`."
        )
    unknown_identifiers = _feedback_unknown_identifiers(candidate_diagnostics)
    if unknown_identifiers:
        contract["unknown_identifiers"] = unknown_identifiers
        contract["unknown_identifier_repair_rule"] = (
            "Do not reference any listed unknown identifier again; replace it "
            "with an existing local declaration, prove the fact from known "
            "primitives, or emit a FORMAL_GAP naming the missing API."
        )
    if "lean_unknown_tactic" in classes:
        contract["unknown_tactic_repair_rule"] = (
            "Use the exact unknown-tactic diagnostic, available imports, retrieved "
            "local declarations, and Lean proof state to generate a revised proof. "
            "Do not substitute a hardcoded tactic list."
        )
    if "lean_typeclass_synthesis_failed" in classes:
        contract["typeclass_repair_rule"] = (
            "Use the exact typeclass-synthesis diagnostic, configured imports, "
            "retrieved local instances/declarations, and Lean proof state to revise "
            "the candidate. Do not infer a replacement type or instance in Python."
        )
    return _merge_feedback_local_lean_repair_contracts(
        explicit_contract,
        contract,
    )


def _merge_feedback_local_lean_repair_contracts(
    explicit_contract: Mapping[str, Any],
    derived_contract: Mapping[str, Any],
) -> Mapping[str, Any]:
    explicit_contract = without_legacy_python_lean_strategy_fields(explicit_contract)
    if not explicit_contract:
        return dict(derived_contract)
    if not derived_contract:
        return dict(explicit_contract)

    merged = dict(explicit_contract)
    explicit_classes = [
        str(value).strip()
        for value in explicit_contract.get("diagnostic_classes", []) or []
        if str(value).strip()
    ]
    derived_classes = [
        str(value).strip()
        for value in derived_contract.get("diagnostic_classes", []) or []
        if str(value).strip()
    ]
    classes: list[str] = []
    has_specific_class = any(
        value != "lean_local_check_failed"
        for value in [*explicit_classes, *derived_classes]
    )
    for value in [*explicit_classes, *derived_classes]:
        if value == "lean_local_check_failed" and has_specific_class:
            continue
        if value not in classes:
            classes.append(value)
    if classes:
        merged["diagnostic_classes"] = classes

    for key, value in derived_contract.items():
        if key == "diagnostic_classes":
            continue
        if key in {
            "blocked_import_prefixes",
            "unknown_identifiers",
            "verified_narrow_imports",
        }:
            existing_values = [
                str(item).strip()
                for item in merged.get(key, []) or []
                if str(item).strip()
            ]
            for item in value or []:
                item_text = str(item).strip()
                if item_text and item_text not in existing_values:
                    existing_values.append(item_text)
            if existing_values:
                merged[key] = existing_values
            continue
        if key not in merged or not merged.get(key):
            merged[key] = value
    return merged


def _feedback_unavailable_import_prefixes(
    diagnostics: Sequence[Mapping[str, Any]],
) -> list[str]:
    patterns = (
        re.compile(
            r"unknown module prefix\s+[`'](?P<prefix>[A-Za-z0-9_.]+)[`']",
            re.IGNORECASE,
        ),
        re.compile(
            r"No directory\s+[`'](?P<prefix>[A-Za-z0-9_.]+)[`']\s+or file",
            re.IGNORECASE,
        ),
        re.compile(
            r"Lean candidate imports unavailable module in configured project:\s*"
            r"(?P<prefix>[A-Za-z0-9_.]+)",
            re.IGNORECASE,
        ),
        re.compile(
            r"Lean candidate imports unavailable umbrella module in configured project:\s*"
            r"(?P<prefix>[A-Za-z0-9_.]+)",
            re.IGNORECASE,
        ),
    )
    prefixes: list[str] = []
    seen: set[str] = set()
    for row in diagnostics:
        text = " ".join(
            str(row.get(key, "") or "")
            for key in (
                "local_lean_stdout",
                "local_lean_stderr",
                "local_lean_stdout_excerpt",
                "local_lean_stderr_excerpt",
            )
        )
        precheck_errors = " ".join(
            str(error) for error in row.get("precheck_errors", []) or []
        )
        text = f"{precheck_errors} {text}"
        for pattern in patterns:
            for match in pattern.finditer(text):
                prefix = match.group("prefix").strip().strip(".")
                if prefix and prefix not in seen:
                    seen.add(prefix)
                    prefixes.append(prefix)
    return prefixes[:8]


def _feedback_diagnostics_import_exact_module(
    diagnostics: Sequence[Mapping[str, Any]],
    module: str,
) -> bool:
    pattern = re.compile(r"^\s*import\s+(?P<modules>.+?)\s*$")
    for row in diagnostics:
        source = str(row.get("lean_source_excerpt", "") or "")
        for line in source.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            modules = [value.strip() for value in match.group("modules").split()]
            if module in modules:
                return True
    return False


def _feedback_verified_narrow_imports(
    diagnostics: Sequence[Mapping[str, Any]],
) -> list[str]:
    pattern = re.compile(
        r"verified narrow module\(s\):\s*(?P<modules>[^;\n]+)",
        re.IGNORECASE,
    )
    modules: list[str] = []
    seen: set[str] = set()
    for row in diagnostics:
        text = " ".join(
            [
                " ".join(str(error) for error in row.get("precheck_errors", []) or []),
                str(row.get("local_lean_stdout", "") or ""),
                str(row.get("local_lean_stderr", "") or ""),
                str(row.get("local_lean_stdout_excerpt", "") or ""),
                str(row.get("local_lean_stderr_excerpt", "") or ""),
            ]
        )
        for match in pattern.finditer(text):
            for module in match.group("modules").split(","):
                module = module.strip().strip(".")
                if module and module not in seen:
                    seen.add(module)
                    modules.append(module)
                    if len(modules) >= 8:
                        return modules
    return modules


def _feedback_unknown_identifiers(
    diagnostics: Sequence[Mapping[str, Any]],
) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(
        r"Unknown\s+(?:identifier|constant)\s+[`'](?P<name>[A-Za-z0-9_.'·]+)[`']",
        re.IGNORECASE,
    )
    for row in diagnostics:
        text = " ".join(
            str(row.get(key, "") or "")
            for key in (
                "local_lean_stdout",
                "local_lean_stderr",
                "local_lean_stdout_excerpt",
                "local_lean_stderr_excerpt",
            )
        )
        for match in pattern.finditer(text):
            name = match.group("name").strip()
            if name and name not in seen:
                seen.add(name)
                names.append(name)
    return names[:8]


def _compact_proof_bank_runtime_memory_summary(row: Mapping[str, Any]) -> dict[str, Any]:
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
        "source_theorem_exact_candidate_placeholder_resolution_plan",
        "source_theorem_exact_candidate_repair_diagnostics",
        "exact_source_theorem_binders",
        "premise_semantic_anchor_binders",
        "premise_semantic_anchor_binder_names",
        "required_bridge_premise_names_for_shared_instantiation",
        "source_to_bridge_adapter_instantiation_group_id",
        "source_to_bridge_adapter_object_names_requiring_source_instantiation",
        "source_to_bridge_grouped_premise_derivation_candidate_request_id",
        "exact_goal_shape_obligation_ids",
        "candidate_definition_request",
        "formalizer_lean_candidate_repair_required",
        "formalizer_lean_candidate_proof_state_feedback_available",
        "formalizer_lean_candidate_unbound_proof_state_feedback_available",
        "n_formalizer_lean_candidate_unbound_proof_state_feedback_rows",
        "formalizer_lean_candidate_component_gate_feedback_available",
        "formalizer_pseudo_formal_packet_component_gate_feedback_available",
        "formalizer_pseudo_formal_packet_component_gate_failure_available",
        "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_available",
        "n_formalizer_pseudo_formal_packet_copy_ready_retry_agenda_rows",
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
        "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory",
        "formalizer_pseudo_formal_packet_component_gate_handoff_diagnostic_memory",
        "formalizer_lean_candidate_capability_feedback_memory",
        "formalizer_runtime_capability_contract_feedback_memory",
        "recommended_source_theorem_integration_action",
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
                "trigger",
                "placeholder_symbol",
                "failure_classification",
                "structural_reformulation_required",
                "pseudo_formalization_required",
                "runtime_queue_status",
                "validation_errors",
                "retry_validation_errors",
                "source_failed_candidate_packet_id",
                "response_validation_feedback",
                "source_theorem_exact_semantic_definition_structural_reformulation_route",
                "definition_contract",
                "required_next_checks",
                "source_lookup_hits",
                "exact_source_theorem_binders",
                "premise_semantic_anchor_binders",
                "premise_semantic_anchor_binder_names",
                "required_bridge_premise_names_for_shared_instantiation",
                "source_to_bridge_adapter_instantiation_group_id",
                "source_to_bridge_adapter_object_names_requiring_source_instantiation",
                "source_to_bridge_grouped_premise_derivation_candidate_request_id",
                "exact_goal_shape_obligation_ids",
                "candidate_definition_request",
                "candidate_artifact_path",
                "definition_only_candidate_artifact_path",
                "diagnostics",
                "semantic_definition_risks",
                "semantic_alignment_blockers",
                "local_definition_lean_compiled",
                "semantic_definition_typecheck_evidence_status",
                "recommended_repair_tasks",
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
                "next_owner_subsystem",
                "proof_body_repair_scope",
                "target_declaration_source_excerpt",
                "candidate_source_excerpt",
                "target_theorem_statement",
                "current_proof_body_excerpt",
                "residual_goal_role",
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
                "recommended_repair_tasks",
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
                "next_owner_subsystem",
                "proof_body_repair_scope",
                "target_declaration_source_excerpt",
                "candidate_source_excerpt",
                "target_theorem_statement",
                "current_proof_body_excerpt",
                "residual_goal_role",
                "exact_goal_shape_obligation_ids",
                "exact_goal_shape_obligations",
                "semantic_alignment_constraints",
                "semantic_alignment_blockers",
                "source_theorem_kernel_evidence_eligible",
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
                "proof_body_adapter_required_reasons",
                "kernel_verified_theorem_reduction_closure_declarations",
                "verified_theorem_reduction_closure_artifact_paths",
                "kernel_verified_theorem_reduction_closure_signature_excerpts",
                "kernel_verified_theorem_reduction_closure_target_ids",
                "recommended_repair_tasks",
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
                "prompt_scaffold_origin",
                "source_prompt_scaffold_kind",
                "source_prompt_scaffold_id",
                "source_prompt_scaffold_required_output_key",
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
                "pseudo_formal_block_verifier_worker",
                "recommended_commands",
                "recommended_next_action",
                "target_behavior",
                "acceptance_gate",
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
                "prompt_scaffold_origin",
                "source_prompt_scaffold_kind",
                "source_prompt_scaffold_id",
                "source_prompt_scaffold_required_output_key",
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
                "pseudo_formal_block_verifier_worker",
                "recommended_commands",
                "recommended_next_action",
                "target_behavior",
                "acceptance_gate",
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
                    "prompt_scaffold_origin",
                    "source_prompt_scaffold_kind",
                    "source_prompt_scaffold_id",
                    "source_prompt_scaffold_required_output_key",
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
                    "reason",
                    "runtime_queue_status",
                    "pseudo_formal_block_verifier_worker",
                    "recommended_commands",
                    "recommended_next_action",
                    "target_behavior",
                    "acceptance_gate",
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
                    "prompt_scaffold_origin",
                    "source_prompt_scaffold_kind",
                    "source_prompt_scaffold_id",
                    "source_prompt_scaffold_required_output_key",
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
                    "pseudo_formal_block_verifier_worker",
                    "recommended_commands",
                    "recommended_next_action",
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
                    "premise_semantic_anchor_binders",
                    "premise_semantic_anchor_binder_names",
                    "required_semantic_anchor_reference_names",
                    "semantic_anchor_reference_gate",
                    "adapter_object_names_requiring_source_instantiation",
                    "candidate_contract",
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
                "candidate_contract",
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
                "premise_candidate_assumes_forbidden_premise",
                "premise_candidate_uninstantiated_adapter_object_binders",
                "premise_candidate_references_semantic_anchor",
                "missing_premise_semantic_anchor_binder_names",
                "exact_source_theorem_binders",
                "premise_semantic_anchor_binders",
                "premise_semantic_anchor_binder_names",
                "required_semantic_anchor_reference_names",
                "semantic_anchor_reference_gate",
                "source_context_status",
                "source_theorem_signature_excerpt",
                "adapter_signature_excerpt",
                "premise_target_status",
                "premise_target_matched_binder",
                "premise_target_type",
                "adapter_instantiation_group_id",
                "required_bridge_premise_names_for_shared_instantiation",
                "shared_adapter_instantiation_contract",
                "premise_derivation_gap_kind",
                "premise_derivation_gap_summary",
                "premise_semantic_dependency_status",
                *_SOURCE_TO_BRIDGE_POLICY_LINEAGE_KEYS,
                "premise_semantic_dependency_requirements",
                "source_to_bridge_premise_derivation_candidate_request_id",
                "source_to_bridge_premise_derivation_candidate_request",
                "source_to_bridge_grouped_premise_derivation_candidate_request_id",
                "source_to_bridge_grouped_premise_derivation_candidate_request",
                "proof_body_goal_excerpt",
                "proof_body_attempt_summaries",
                "kernel_verified_theorem_reduction_closure_declarations",
                "verified_theorem_reduction_closure_artifact_paths",
                "recommended_repair_tasks",
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
                "precheck_status",
                "precheck_errors",
                "local_lean_attempted",
                "local_lean_compiled",
                "local_lean_exit_status",
                "local_lean_project",
                "local_lean_diagnostic_classes",
                "local_lean_repair_contract",
                "local_lean_stdout_excerpt",
                "local_lean_stderr_excerpt",
                "next_action",
                "proof_evidence_status",
            ),
            limit=3,
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
                "local_lean_compiled",
                "source_theorem_target_known",
                "diagnostic_helper_not_source_theorem",
                "lean_source_excerpt",
                "next_action",
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
                "target_behavior",
                "acceptance_gate",
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
                "target_behavior",
                "acceptance_gate",
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
                "pseudo_formal_failure_required_target_lanes",
                "pseudo_formal_failure_validation_issue_summary",
                "pseudo_formal_failure_issue_specific_repair_actions",
                "pseudo_formal_failure_concrete_lane_routable_repair_seed",
                "pseudo_formal_failure_validator_ready_copy_contract",
                "pseudo_formal_failure_copy_contract_summary",
                "pseudo_formal_failure_copy_ready",
                "pseudo_formal_failure_copy_exact_semantic_definition_ready",
                "pseudo_formal_failure_repair_seed_available",
                "pseudo_formal_routable_target_lanes",
                "n_pseudo_formal_routable_work_order_rows",
                "exact_semantic_definition_lane_present",
                "target_behavior",
                "acceptance_gate",
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
                "validation_issue_summary",
                "issue_specific_repair_actions",
                "concrete_lane_routable_repair_seed",
                "validator_ready_copy_contract",
                "validator_ready_copy_contract_summary",
                "validator_ready_copy_contract_satisfied",
                "copy_ready_for_exact_semantic_definition",
                "proof_evidence_status",
                "boundary",
            ),
            limit=3,
        )
    if isinstance(
        row.get("formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory"),
        list,
    ):
        compact[
            "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory"
        ] = _compact_rows(
            row.get(
                "formalizer_pseudo_formal_packet_copy_ready_retry_agenda_memory",
                [],
            ),
            keys=(
                "learning_task",
                "question_id",
                "agenda_id",
                "trigger",
                "source_learning_task",
                "work_order_id",
                "component_eval_manifest_path",
                "target_ids",
                "target_theorem_name",
                "target_packet_id",
                "runtime_queue_status",
                "runtime_generated_queue_name",
                "required_target_lanes",
                "concrete_lane_routable_repair_seed",
                "validator_ready_copy_contract",
                "validator_ready_copy_contract_summary",
                "copy_contract_summary",
                "target_behavior",
                "recommended_next_action",
                "action",
                "acceptance_gate",
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
                "target_behavior",
                "acceptance_gate",
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
                "missing_contracts",
                "runtime_requested_evidence_contract",
                "required_runtime_configuration",
                "required_formalizer_behavior",
                "formalizer_candidate_local_lean",
                "proof_state_provider",
                "n_candidate_sources",
                "n_local_lean_checked",
                "n_live_proof_state_requests",
                "n_lean_lsp_mcp_ready_requests",
                "candidate_proof_state_manifest_id",
                "target_behavior",
                "acceptance_gate",
                "proof_evidence_status",
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
                "premise_semantic_anchor_binders",
                "premise_semantic_anchor_binder_names",
                "source_to_bridge_adapter_instantiation_group_id",
                "candidate_definition_request",
                "failure_classification",
                "proof_evidence_status",
            ),
            limit=4,
        )
    if isinstance(row.get("source_theorem_exact_candidate_placeholder_resolution_plan"), list):
        compact["source_theorem_exact_candidate_placeholder_resolution_plan"] = _compact_rows(
            row.get("source_theorem_exact_candidate_placeholder_resolution_plan", []),
            keys=(
                "placeholder_symbol",
                "replacement_strategy",
                "candidate_registered_obligation_ids",
                "source_theorem_target_identity_status",
            ),
            limit=4,
        )
    return compact


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
    if str(key) in {
        "target_declaration_source_excerpt",
        "candidate_source_excerpt",
        "target_theorem_statement",
        "current_proof_body_excerpt",
    } and isinstance(value, str):
        limits = {
            "target_declaration_source_excerpt": 12000,
            "candidate_source_excerpt": 12000,
            "target_theorem_statement": 9000,
            "current_proof_body_excerpt": 6000,
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
    if key in (
        "validator_ready_copy_contract_summary",
        "pseudo_formal_failure_copy_contract_summary",
    ) and isinstance(value, Mapping):
        return _compact_mapping(
            value,
            keys=(
                "validator_ready_copy_contract_present",
                "validator_ready_copy_contract_satisfied",
                "exact_semantic_definition_lane_ready_if_copied",
                "repair_seed_valid",
                "copy_source_path",
                "copy_destination_path",
                "copy_destination_path_ok",
                "n_routable_work_order_rows_if_copied",
                "routable_target_lanes_if_copied",
                "contract_target_lanes_covered_if_copied",
                "n_exact_semantic_definition_rows_if_copied",
                "n_exact_semantic_definition_rows_with_source_anchors_if_copied",
                "n_exact_semantic_definition_rows_with_semantic_requirements_if_copied",
                "n_exact_semantic_definition_rows_with_lineage_if_copied",
                "validation_errors",
                "proof_evidence_status",
                "boundary",
            ),
        )
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
            "proof_search_result_use",
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
            "hard_negative_rejected_imports",
            "source_failed_candidate_packet_id",
            "required_block_schema_hints",
            "lane_activation_hints",
            "validation_issue_summary",
            "validation_issue_repair_actions",
            "validation_issue_kinds",
            "source",
            "source_theorem_proof_body_adapter_required",
            "source_theorem_proof_body_adapter_feedback_available",
            "adapter_kernel_verified",
            "diagnostics",
            "diagnostic_classes",
            "required_behavior",
            "acceptance_gate",
            "source_theorem_candidate_proof_bodies",
            "verified_support_assets",
            "failure_feedback",
            "exact_candidate_rerun",
            "proof_evidence_status",
            "blocked_import_prefixes",
            "mathlib_import_unavailable",
            "mathlib_root_import_unavailable",
            "mathlib_repair_rule",
            "import_repair_rule",
            "suggested_import_replacements",
            "unknown_identifiers",
            "unknown_identifier_repair_rule",
            "repeated_syntax_failure",
        )
        ordered_keys: list[Any] = [
            key
            for key in priority_keys
            if key in value and value.get(key) not in (None, "", [], {})
        ]
        for key in value:
            if key not in ordered_keys and value.get(key) not in (None, "", [], {}):
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


def _target_lean_declaration_identifier_error(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if (
        re.search(r"\s", text)
        or lowered.startswith(("theorem ", "lemma ", "def "))
        or ":=" in text
        or ":" in text
    ):
        return "must be a Lean declaration identifier, not a full theorem statement"
    return ""


def _lean_statement_placeholder_syntax_error(source: str) -> str:
    if not source:
        return ""
    patterns = (
        (r"/\*|\*/", "contains C-style placeholder comment syntax"),
        (r"\bplaceholder\b", "contains placeholder text inside Lean syntax"),
        (r"\bTODO\b", "contains TODO marker inside Lean syntax"),
        (r"\bfail_if_success\b", "contains ProofEngineer skeleton marker fail_if_success"),
        (r"\bsorry\b", "contains Lean sorry placeholder"),
        (r"\badmit\b", "contains Lean admit placeholder"),
        (r"\baxiom\b", "contains Lean axiom declaration"),
        (r"\bunsafe\b", "contains unsafe Lean declaration"),
        (r"\bby\?", "contains interactive proof-hole marker by?"),
        (r"\bexact\?", "contains interactive proof-hole marker exact?"),
    )
    for pattern, message in patterns:
        if re.search(pattern, source, flags=re.IGNORECASE):
            return message
    return ""


def _source_to_bridge_candidate_vacuous_truth_error(source: str) -> str:
    if not source:
        return ""
    if re.search(
        r"\b(?:theorem|lemma)\b[\s\S]*?:\s*True\s*:=\s*by\b",
        source,
        flags=re.IGNORECASE,
    ):
        return "contains vacuous True source-to-bridge premise candidate"
    return ""


def _source_to_bridge_candidate_missing_anchor_references(
    row: Mapping[str, Any],
    source: str,
) -> tuple[str, ...]:
    anchor_names = _source_to_bridge_candidate_required_anchor_names(row)
    if not anchor_names or not source:
        return ()
    stripped = _strip_lean_comments(source)
    missing = [
        name
        for name in anchor_names
        if not _source_to_bridge_anchor_has_substantive_reference(stripped, name)
    ]
    return tuple(missing)


def _source_to_bridge_candidate_required_anchor_names(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    values: list[str] = []
    sources: list[Mapping[str, Any]] = [row]
    for key in (
        "source_to_bridge_premise_derivation_candidate_request",
        "source_to_bridge_grouped_premise_derivation_candidate_request",
    ):
        nested = row.get(key, {})
        if isinstance(nested, Mapping):
            sources.append(nested)
    for source in sources:
        for key in (
            "required_semantic_anchor_reference_names",
            "premise_semantic_anchor_binder_names",
        ):
            raw = source.get(key, [])
            candidates = raw if isinstance(raw, list | tuple | set) else [raw]
            for value in candidates:
                text = str(value or "").strip()
                if text:
                    values.append(text)
        for binder in source.get("premise_semantic_anchor_binders", []) or []:
            if isinstance(binder, Mapping):
                name = str(binder.get("name", "") or "").strip()
                if name:
                    values.append(name)
    return tuple(dict.fromkeys(values))


def _source_to_bridge_anchor_has_substantive_reference(source: str, name: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not pattern.search(line):
            continue
        if _source_to_bridge_anchor_reference_line_is_noop(line, name):
            continue
        return True
    return False


def _source_to_bridge_anchor_reference_line_is_noop(line: str, name: str) -> bool:
    name_pat = re.escape(name)
    noop_patterns = (
        rf"^(?:have|let)\s+_\s*(?::[^:=]+)?\s*:=\s*{name_pat}\s*$",
        rf"^(?:have|let)\s+[A-Za-z_][A-Za-z0-9_'.]*\s*(?::[^:=]+)?\s*:=\s*{name_pat}\s*$",
    )
    return any(re.search(pattern, line) for pattern in noop_patterns)


def _source_to_bridge_candidate_uninstantiated_adapter_object_binders(
    row: Mapping[str, Any],
    source: str,
) -> tuple[str, ...]:
    adapter_object_names = _source_to_bridge_candidate_adapter_object_names(row)
    if not adapter_object_names or not source:
        return ()
    header = _lean_theorem_header_without_comments(source)
    found: list[str] = []
    for inner in _top_level_parenthesized_groups(header):
        if ":" not in inner:
            continue
        names_text, _binder_type = inner.split(":", 1)
        binder_names = {value.strip() for value in names_text.split() if value.strip()}
        for name in adapter_object_names:
            if name in binder_names:
                found.append(name)
    return tuple(dict.fromkeys(found))


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
    has_exact_source_binders = row.get("exact_source_theorem_binders") not in (
        None,
        "",
        [],
        {},
    )
    has_anchor_metadata = any(
        row.get(key) not in (None, "", [], {})
        for key in (
            "premise_semantic_anchor_binders",
            "premise_semantic_anchor_binder_names",
            "required_semantic_anchor_reference_names",
        )
    )
    has_adapter_instantiation_metadata = row.get(
        "adapter_object_names_requiring_source_instantiation"
    ) not in (None, "", [], {})
    has_premise_identity = bool(_source_to_bridge_candidate_premise_names(row))
    has_target_identity = bool(
        str(
            row.get("target_lean_declaration", "")
            or row.get("target_theorem_name", "")
            or ""
        ).strip()
    )
    return bool(
        (has_exact_source_binders and has_anchor_metadata)
        or (has_anchor_metadata and has_adapter_instantiation_metadata)
        or has_adapter_instantiation_metadata
        or (has_premise_identity and has_target_identity and has_anchor_metadata)
    )


def _source_to_bridge_candidate_has_copied_request_contract(
    row: Mapping[str, Any],
) -> bool:
    for key in (
        "source_to_bridge_premise_derivation_candidate_request",
        "source_to_bridge_grouped_premise_derivation_candidate_request",
    ):
        nested = row.get(key, {})
        if isinstance(nested, Mapping) and nested:
            return True
    return False


def _source_to_bridge_candidate_adapter_object_names(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    values: list[str] = []
    sources: list[Mapping[str, Any]] = [row]
    for key in (
        "source_to_bridge_premise_derivation_candidate_request",
        "source_to_bridge_grouped_premise_derivation_candidate_request",
    ):
        nested = row.get(key, {})
        if isinstance(nested, Mapping):
            sources.append(nested)
    for source in sources:
        raw = source.get("adapter_object_names_requiring_source_instantiation", [])
        candidates = raw if isinstance(raw, list | tuple | set) else [raw]
        for value in candidates:
            text = str(value or "").strip()
            if text:
                values.append(text)
    return tuple(dict.fromkeys(values))


def _lean_theorem_header_without_comments(source: str) -> str:
    text = _strip_lean_comments(source)
    match = re.search(r"\b(?:theorem|lemma)\s+[A-Za-z_][A-Za-z0-9_'.]*\b", text)
    if not match:
        return text
    theorem_text = text[match.start() :]
    marker = theorem_text.find(":=")
    return theorem_text if marker < 0 else theorem_text[:marker]


def _top_level_parenthesized_groups(text: str) -> tuple[str, ...]:
    groups: list[str] = []
    depth = 0
    start: int | None = None
    for index, char in enumerate(text):
        if char == "(":
            if depth == 0:
                start = index + 1
            depth += 1
        elif char == ")":
            if depth <= 0:
                continue
            depth -= 1
            if depth == 0 and start is not None:
                groups.append(text[start:index])
                start = None
    return tuple(groups)


def _strip_lean_comments(source: str) -> str:
    without_block_comments = re.sub(r"/-.*?-/", "", source, flags=re.DOTALL)
    return "\n".join(line.split("--", 1)[0] for line in without_block_comments.splitlines())
