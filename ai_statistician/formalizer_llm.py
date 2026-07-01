from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .formalizer_repair_policy import (
    render_formalizer_validation_repair_policy_instructions,
)
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion
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
    "LLM Formalizer/ProofEngineer packets are formalization and proof-search "
    "proposals only. They do not count as Lean proof evidence, do not certify "
    "source theorem faithfulness, and cannot claim kernel verification. Proof "
    "evidence requires AgentRuntime to run AXLE/local Lean/kernel verification "
    "on the intended formal claim."
)
FORMALIZER_MAX_THEORY_ROWS = 3
FORMALIZER_MAX_THEOREM_GOALS = 4
FORMALIZER_MAX_PROOF_BANK_ROWS = 12
FORMALIZER_MAX_TEXT_CHARS = 300


@dataclass(frozen=True)
class FormalizerConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 6000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1


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
        request = GeneratorRequest(
            system_prompt=FORMALIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=FORMALIZER_JSON_SCHEMA,
            metadata={
                "subsystem": "FormalizerProofEngineer",
                "agent": "LLMFormalizerProofEngineerAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_formalizer_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
                theory_packet=theory_packet,
                proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary
                or {},
                environment_feedback=environment_feedback or {},
            )

        requires_lean_candidate = _feedback_requires_formalizer_lean_candidate(
            environment_feedback or {}
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
            if requires_lean_candidate:
                errors.extend(
                    _validate_capability_eval_formalizer_lean_candidate_packet(
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
        )


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
        keys=("id", "title", "claim", "statement", "conclusion", "assumptions", "proof_obligations"),
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
    initial_target_shape_contract = _initial_probability_coverage_target_shape_contract(
        question=question,
        theory_packet=theory_packet,
        theorem_goals=theorem_goals,
        registered_problem=registered_problem,
    )
    proof_memory_summary = _compact_proof_bank_runtime_memory_summary(
        proof_bank_runtime_memory_summary or {}
    )
    source_to_bridge_request_shortcuts = (
        _source_to_bridge_candidate_request_shortcuts(proof_memory_summary)
    )
    diagnostic_helper_bridge_blocker_contract = (
        _diagnostic_helper_bridge_blocker_contract(proof_memory_summary)
    )
    source_theorem_candidate_materialization_contract = (
        _source_theorem_candidate_materialization_contract(proof_memory_summary)
    )
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "prompt_mode": {
            "mode": "compact_minimal_proof_target_triage",
            "purpose": "choose minimal Lean/formal targets and proof-bank obligations before kernel gates",
            "max_items_per_list": 3,
            "do_not_expand_full_derivations": True,
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
        "runtime_environment_feedback": runtime_environment_feedback,
        "formalizer_lean_candidate_contract": {
            "capability_eval_requires_formalizer_lean_candidate": requires_lean_candidate,
            "initial_target_shape_contract": initial_target_shape_contract,
            "required_when_true": (
                "include at least one concrete safe Lean theorem sketch with "
                "expected_status=NEEDS_KERNEL_CHECK in either formal_targets or "
                "source_to_bridge_premise_derivation_candidates; "
                "proof_bank_obligation_requests alone do not satisfy this gate. "
                "A source_to_bridge_premise_derivation_candidates entry must copy "
                "premise_candidate_declaration_name from the runtime request and "
                "its Lean source must declare theorem <that exact name>. "
                "When runtime target-shape feedback says a source theorem would "
                "drift if repaired, emit that source theorem as FORMAL_GAP and "
                "route helper/premise Lean candidates separately. A separate helper "
                "formal_targets entry must set "
                "source_theorem_target_provenance.source_theorem_target_known=false "
                "so local Lean/LSP can inspect a real artifact without promoting it "
                "to source-theorem proof evidence."
            ),
            "not_proof_evidence": (
                "the Lean candidate remains a proposal until AgentRuntime runs "
                "local Lean/AXLE on that exact artifact"
            ),
        },
        "mode_specific_instructions": _formalizer_mode_specific_instructions(
            proof_memory_summary,
            runtime_environment_feedback,
        ),
        "proof_bank_obligation_request_policy": {
            "use_only_registered_catalog_ids_when_possible": True,
            "request_effect": "priority_only_for_kernel_smoke_selection",
            "runtime_filter": "AgentRuntime rejects unknown obligation IDs and filters against the current candidate set",
            "not_evidence": "A proof-bank obligation request is not Lean proof evidence and does not prove the frontier theorem.",
            "when_catalog_exhausted_by_kernel_memory": (
                "Do not request already-kernel-verified bridge obligations again. "
                "Target the theorem-level reduction closure that connects those "
                "verified bridge obligations to the remaining frontier theorem goal."
            ),
        },
        "required_output_contract": _formalizer_output_contract_for_prompt(
            has_theory_trace=bool(theory_derivation_trace)
        ),
        "boundary": FORMALIZER_BOUNDARY,
    }
    metadata_authoring_mode = bool(
        proof_memory_summary.get("source_to_bridge_metadata_authoring_required")
        or proof_memory_summary.get("recommended_formalizer_target_mode")
        == "source_to_bridge_metadata_authoring_required"
    )
    if requires_lean_candidate and metadata_authoring_mode:
        lean_candidate_instruction = (
            "Capability-eval mode is active, but source-to-bridge metadata "
            "authoring takes priority: do not emit another helper-only Lean "
            "formal_targets entry just to satisfy the Lean-candidate gate. Keep "
            "the source theorem as expected_status=FORMAL_GAP, and either emit a "
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
            "probability/coverage source-theorem target or a real "
            "source_to_bridge_premise_derivation_candidates object with copied "
            "source-binding metadata and semantic anchors. Otherwise emit the "
            "source theorem as expected_status=FORMAL_GAP with an empty Lean sketch "
            "and record the missing premise/API in gap_taxonomy/next_actions; the "
            "runtime validator accepts this fail-closed target-drift repair. "
        )
    elif requires_lean_candidate:
        lean_candidate_instruction = (
            "Capability-eval mode is active for Formalizer/ProofEngineer: include "
            "exactly one compact concrete safe Lean theorem sketch with "
            "expected_status=NEEDS_KERNEL_CHECK, either as a faithful formal_targets "
            "source-theorem candidate or as a source_to_bridge_premise_derivation_candidates "
            "repair candidate when target-shape feedback says the source theorem must "
            "remain a FORMAL_GAP. Do not satisfy the packet using only "
            "proof_bank_obligation_requests, gap taxonomy, or queue work orders. "
        )
        if initial_target_shape_contract:
            lean_candidate_instruction += (
                "Initial coverage target-shape guard is active: if a formal_targets "
                "entry represents the source theorem, its Lean sketch must preserve "
                "an explicit probability/measure coverage lower-bound conclusion. "
                "Do not put standalone rank, ceiling, monotonicity, or arithmetic "
                "helper lemmas in the source-theorem formal_targets slot; route those "
                "through support/source-to-bridge channels or mark the source theorem "
                "as FORMAL_GAP with an empty Lean sketch when faithful formalization is "
                "not feasible. "
            )
    else:
        lean_candidate_instruction = ""
    return (
        "Design formalization and proof-search artifacts for the Formalizer/ProofEngineer subsystem. "
        "Return ONLY compact JSON matching required_output_contract. Keep each list to at most 3 items. "
        "Prefer one minimal Lean target plus one or two registered proof-bank obligations over a broad "
        "formalization essay. You may propose Lean statement sketches, lemma dependency plans, source "
        "retrieval queries, and kernel-check work orders, but do not claim theorem proof, kernel "
        "verification, or source-theorem faithfulness. Use mode_specific_instructions only when "
        "their triggering memory fields are present. For proof_bank_obligation_requests, choose "
        "obligation_id values from registered_proof_bank_obligation_catalog when possible; these "
        "requests only prioritize AgentRuntime kernel-smoke work and may be filtered or rejected. "
        "Populate theory_trace_alignment with exact trace anchor ids/names. "
        "Do not use C-style comments, placeholder binder types, `/* ... */`, `placeholder`, `TODO`, "
        "`sorry`, `admit`, `axiom`, `unsafe`, or `by?` in Lean statement sketches. Mark "
        "expected_status=NEEDS_KERNEL_CHECK on every generated Lean candidate; use "
        "expected_status=FORMAL_GAP only for an unrepaired source theorem target "
        "reported outside Lean source. Every Lean candidate is only a proposal until "
        "local Lean/AXLE verifies that exact artifact. Every next_actions entry must "
        "point to an artifact or candidate actually emitted in this packet; do not tell "
        "AgentRuntime/AXLE to check a source_to_bridge_premise_derivation_candidates "
        "entry unless that exact candidate object is present. If no such candidate can "
        "be emitted, write the blocker as gap_taxonomy/proof_bank dependency work "
        "instead of a phantom executable action. "
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
            "informal_source": "string",
            "lean_statement_sketch": "string",
            "lean_imports": ["Mathlib"],
            "semantic_alignment_constraints": ["string"],
            "source_theorem_target_provenance": {
                "source_theorem_target_known": "true only for the source theorem target; false for helper/support Lean candidates",
                "target_lean_declaration": "source theorem Lean declaration, not adapter declaration",
                "source_theorem_goal_id": "registered theorem goal id",
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
    "retrieval_queries": [
        {
            "query": "string",
            "target_library": "Mathlib|StatInference|LeanRAG|OpenProver|other",
            "purpose": "string",
        }
    ],
    "proof_search_plan": {
        "preferred_tools": ["string"],
        "tactic_or_certificate_hints": ["string"],
        "kernel_check_plan": ["string"],
        "known_blockers": ["string"],
    },
    "proof_bank_obligation_requests": [
        {
            "obligation_id": "string",
            "target_theorem_card": "string",
            "reason": "string",
            "verification_priority": "high|medium|low",
        }
    ],
    "source_to_bridge_premise_derivation_candidates": [
        {
            "premise_name": "hGoodCovered",
            "premise_names": ["hGoodCovered", "hBadEvent"],
            "adapter_instantiation_group_id": "shared adapter instantiation group id when present",
            "required_bridge_premise_names_for_shared_instantiation": [
                "hGoodCovered",
                "hBadEvent",
            ],
            "target_theorem_name": "split_conformal_coverage",
            "target_lean_declaration": "split_conformal_coverage",
            "premise_candidate_declaration_name": (
                "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
            ),
            "premise_derivation_candidate_lean_source": (
                "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation ... := by\n"
                "  ..."
            ),
            "reason": "derive the adapter premise from exact source theorem hypotheses",
            "expected_status": "NEEDS_KERNEL_CHECK",
        }
    ],
    "source_to_bridge_premise_derivation_candidate_requests": [
        {
            "candidate_request_id": "request:hGoodCovered",
            "premise_name": "hGoodCovered",
            "target_theorem_name": "split_conformal",
            "target_lean_declaration": "split_conformal",
            "premise_candidate_declaration_name": (
                "split_conformal_hGoodCovered_source_to_bridge_derivation"
            ),
            "premise_target_type": "adapter premise Lean type",
            "exact_source_theorem_binders": [{"name": "hC", "type": "source hyp"}],
            "premise_semantic_anchor_binders": [{"name": "hC", "role": "anchor"}],
            "premise_semantic_anchor_binder_names": ["hC"],
            "required_semantic_anchor_reference_names": ["hC"],
            "adapter_object_names_requiring_source_instantiation": ["covered"],
            "candidate_contract": "metadata only; not executable Lean",
            "proof_evidence_status": "REQUEST_NOT_PROOF_EVIDENCE",
        }
    ],
    "gap_taxonomy": [
        {"gap": "string", "kind": "formal_primitives|semantic_alignment|proof_search|source_theorem|other", "next_owner": "string"}
    ],
    "critic_findings": [
        {"critic": "string", "finding": "string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "string", "acceptance_gate": "string"}
    ],
}


def _formalizer_output_contract_for_prompt(*, has_theory_trace: bool) -> dict[str, Any]:
    if has_theory_trace:
        return FORMALIZER_OUTPUT_CONTRACT
    contract = dict(FORMALIZER_OUTPUT_CONTRACT)
    contract.pop("theory_trace_alignment", None)
    return contract


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
        "formal_targets": {"type": "array", "minItems": 1},
        "lemma_dependency_plan": {"type": "array", "minItems": 1},
        "retrieval_queries": {"type": "array", "minItems": 1},
        "proof_search_plan": {"type": "object"},
        "proof_bank_obligation_requests": {"type": "array"},
        "source_to_bridge_premise_derivation_candidates": {"type": "array"},
        "source_to_bridge_premise_derivation_candidate_requests": {
            "type": "array"
        },
        "gap_taxonomy": {"type": "array", "minItems": 1},
        "critic_findings": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_formalizer_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "formal_targets",
        "lemma_dependency_plan",
        "retrieval_queries",
        "proof_search_plan",
        "gap_taxonomy",
        "critic_findings",
        "next_actions",
    ):
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
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
        candidate_source = str(
            row.get("premise_derivation_candidate_lean_source", "")
            or row.get("lean_statement_sketch", "")
            or row.get("candidate_lean_source", "")
            or ""
        )
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
        declaration_errors = _source_to_bridge_candidate_declaration_contract_errors(
            row,
            candidate_source,
        )
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
    errors.extend(_phantom_source_to_bridge_next_action_errors(packet))
    forbidden_packet = _contains_forbidden_proof_claim(packet)
    if forbidden_packet:
        errors.append(f"packet contains forbidden proof claim: {forbidden_packet}")
    return sorted(set(errors))


def _source_to_bridge_candidate_declaration_contract_errors(
    row: Mapping[str, Any],
    candidate_source: str,
) -> list[str]:
    if not candidate_source.strip():
        return []
    expected_names = _source_to_bridge_candidate_expected_declaration_names(row)
    if not expected_names:
        return []
    missing = [
        name
        for name in expected_names
        if not re.search(rf"\btheorem\s+{re.escape(name)}\b", candidate_source)
    ]
    if not missing:
        return []
    return [
        "source_to_bridge_premise_derivation_candidates Lean candidate must "
        "declare theorem with exact premise_candidate_declaration_name: "
        + ", ".join(missing)
    ]


def _source_to_bridge_candidate_expected_declaration_names(
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

    add_value(row.get("premise_candidate_declaration_name", ""))
    add_value(row.get("source_to_bridge_premise_candidate_declaration_name", ""))
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
            if not isinstance(raw_rows, list | tuple | set):
                continue
            for item in raw_rows:
                if isinstance(item, Mapping):
                    add_request(item)
                else:
                    add_value(item)
    if not names:
        target = str(
            row.get("target_lean_declaration", "")
            or row.get("target_theorem_name", "")
            or ""
        ).strip()
        for premise in _source_to_bridge_candidate_premise_names(row):
            generated = default_premise_candidate_declaration_name(
                {"target_lean_declaration": target, "premise_name": premise}
            )
            if generated:
                names.append(generated)
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
        if not bool(contract.get("repeated_syntax_failure", False)):
            continue
        diagnostic_classes = {
            str(value).strip()
            for value in contract.get("diagnostic_classes", []) or []
            if str(value).strip()
        }
        if (
            not diagnostic_classes
            or "lean_parser_or_syntax_error" in diagnostic_classes
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
        if "source theorem" in row_text or "coverage" in row_text:
            return True
    return False


def _lean_source_has_probability_or_measure_shape(source: str) -> bool:
    source_text = str(source or "")
    return (
        "MeasureTheory" in source_text
        or "IsProbabilityMeasure" in source_text
        or "ProbabilityTheory" in source_text
        or re.search(r"\b(?:P|μ|Pr)\s*(?:\{|\(|:)", source_text) is not None
        or re.search(r"\bMeasure\.", source_text) is not None
    )


def _initial_probability_coverage_target_shape_contract(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
    registered_problem: Mapping[str, Any],
) -> Mapping[str, Any]:
    text = " ".join(
        [
            question.id,
            question.title,
            question.description,
            " ".join(question.tags),
            json.dumps(
                _compact_value(
                    theory_packet.get("theorem_cards", [])
                    if isinstance(theory_packet, Mapping)
                    else []
                ),
                default=str,
            ),
            json.dumps(
                _compact_value(
                    theory_packet.get("formalization_requests", [])
                    if isinstance(theory_packet, Mapping)
                    else []
                ),
                default=str,
            ),
            json.dumps(_compact_value(theorem_goals), default=str),
            json.dumps(_compact_value(registered_problem), default=str),
        ]
    ).lower()
    if "coverage" not in text:
        return {}
    if not any(
        marker in text
        for marker in (
            "conformal",
            "prediction interval",
            "probability",
            "measure",
            "marginal coverage",
        )
    ):
        return {}
    return {
        "contract_kind": "initial_source_theorem_target_shape_guard",
        "required_conclusion_family": "probability_or_measure_coverage_claim",
        "required_behavior": (
            "Coverage source-theorem formal_targets with expected_status="
            "NEEDS_KERNEL_CHECK must conclude an explicit probability/measure "
            "coverage lower bound, not only an arithmetic or rank helper lemma."
        ),
        "if_not_feasible": (
            "Emit the source theorem as expected_status=FORMAL_GAP with an empty "
            "Lean sketch and route helper work through support channels."
        ),
    }


def _feedback_requires_probability_measure_coverage_shape(
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
        if (
            isinstance(contract, Mapping)
            and str(contract.get("required_conclusion_family", "") or "")
            == "probability_or_measure_coverage_claim"
        ):
            return True
    return False


def _formal_target_is_source_theorem_candidate(row: Mapping[str, Any]) -> bool:
    provenance = row.get("source_theorem_target_provenance", {})
    source_theorem_target_known = _source_theorem_target_known(provenance)
    if source_theorem_target_known is False:
        return False
    if source_theorem_target_known is True:
        return True
    row_text = " ".join(
        str(row.get(field, "") or "")
        for field in ("id", "informal_source", "claim", "statement", "reason")
    ).lower()
    return "source theorem" in row_text


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


def _packet_requires_probability_measure_coverage_shape(
    packet: Mapping[str, Any],
    formal_targets: Sequence[Mapping[str, Any]],
) -> bool:
    question = packet.get("question", {})
    question_text = json.dumps(question, default=str).lower()
    target_text = json.dumps(
        [
            {
                "id": row.get("id", ""),
                "informal_source": row.get("informal_source", ""),
                "claim": row.get("claim", ""),
            }
            for row in formal_targets
        ],
        default=str,
    ).lower()
    combined = question_text + " " + target_text
    if "coverage" not in combined:
        return False
    if not any(
        marker in combined
        for marker in (
            "conformal",
            "prediction interval",
            "probability",
            "measure",
            "marginal coverage",
        )
    ):
        return False
    return any(_formal_target_is_source_theorem_candidate(row) for row in formal_targets)


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
        and str(
            row.get("premise_derivation_candidate_lean_source", "")
            or row.get("lean_statement_sketch", "")
            or row.get("candidate_lean_source", "")
            or ""
        ).strip()
    ]
    pending_source_to_bridge_premise_names = (
        _pending_source_to_bridge_premise_names_for_capability_eval(
            environment_feedback=environment_feedback,
            proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
        )
    )
    if not candidate_targets and not source_to_bridge_candidate_targets:
        if _feedback_has_repeated_syntax_failure_contract(environment_feedback):
            if _has_explicit_source_theorem_formal_gap_target(formal_targets):
                return []
            return [
                "capability_eval repeated parser/syntax contract requires either "
                "an explicit source-theorem FORMAL_GAP formal_targets row with "
                "an empty Lean sketch, or one parser-simple support candidate in "
                "source_to_bridge_premise_derivation_candidates with copied "
                "source-binding metadata; packet has neither"
            ]
        if (
            pending_source_to_bridge_premise_names
            and _packet_has_source_to_bridge_semantic_anchor_blocker(
                packet,
                pending_source_to_bridge_premise_names,
            )
        ):
            return []
        if (
            _feedback_has_source_theorem_target_drift(environment_feedback)
            and _has_explicit_source_theorem_formal_gap_target(formal_targets)
            and not pending_source_to_bridge_premise_names
        ):
            return []
        return [
            "capability_eval requires at least one Claude/OpenAI-generated "
            "Lean statement sketch in formal_targets or "
            "source_to_bridge_premise_derivation_candidates"
        ]
    errors: list[str] = []
    requires_probability_measure_coverage_shape = (
        _feedback_requires_probability_measure_coverage_shape(environment_feedback)
        or _packet_requires_probability_measure_coverage_shape(packet, formal_targets)
    )
    for row in candidate_targets:
        target_id = str(row.get("id", "") or "<unnamed>")
        source = str(row.get("lean_statement_sketch", "") or "")
        expected_status = str(row.get("expected_status", "") or "")
        if expected_status != "NEEDS_KERNEL_CHECK":
            errors.append(
                "capability_eval formal target "
                f"{target_id} must set expected_status=NEEDS_KERNEL_CHECK"
            )
        if (
            requires_probability_measure_coverage_shape
            and _formal_target_is_source_theorem_candidate(row)
            and expected_status == "NEEDS_KERNEL_CHECK"
            and not _lean_source_has_probability_or_measure_shape(source)
        ):
            errors.append(
                "capability_eval formal target "
                f"{target_id} violates target_shape_contract: source theorem "
                "target shape requires a probability/measure coverage "
                "conclusion; route arithmetic/helper lemmas through "
                "source_to_bridge_premise_derivation_candidates or support-lemma "
                "channels and emit the source theorem as FORMAL_GAP when faithful "
                "repair is not feasible"
            )
        if not re.search(r"\b(theorem|lemma)\b", source):
            errors.append(
                "capability_eval formal target "
                f"{target_id} must contain a Lean theorem or lemma declaration"
            )
        placeholder_error = _lean_statement_placeholder_syntax_error(source)
        if placeholder_error:
            errors.append(
                "capability_eval formal target "
                f"{target_id} Lean sketch {placeholder_error}"
            )
        if _feedback_has_repeated_syntax_failure_contract(environment_feedback):
            if expected_status == "NEEDS_KERNEL_CHECK":
                errors.append(
                    "capability_eval formal target "
                    f"{target_id} violates repeated parser/syntax repair "
                    "contract: executable formal_targets are gated after a "
                    "repeated parser failure; keep the source theorem as "
                    "FORMAL_GAP and route executable helper/support work "
                    "through source_to_bridge_premise_derivation_candidates "
                    "or another support channel with copied source-binding "
                    "metadata"
                )
            for contract_error in _lean_statement_repeated_syntax_contract_errors(
                source
            ):
                errors.append(
                    "capability_eval formal target "
                    f"{target_id} Lean sketch {contract_error}"
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
        source = str(
            row.get("premise_derivation_candidate_lean_source", "")
            or row.get("lean_statement_sketch", "")
            or row.get("candidate_lean_source", "")
            or ""
        )
        expected_status = str(row.get("expected_status", "") or "")
        if expected_status != "NEEDS_KERNEL_CHECK":
            errors.append(
                "capability_eval source-to-bridge candidate "
                f"{premise_id} must set expected_status=NEEDS_KERNEL_CHECK"
            )
        if not re.search(r"\b(theorem|lemma)\b", source):
            errors.append(
                "capability_eval source-to-bridge candidate "
                f"{premise_id} must contain a Lean theorem or lemma declaration"
            )
        placeholder_error = _lean_statement_placeholder_syntax_error(source)
        if placeholder_error:
            errors.append(
                "capability_eval source-to-bridge candidate "
                f"{premise_id} Lean sketch {placeholder_error}"
            )
        if _feedback_has_repeated_syntax_failure_contract(environment_feedback):
            for contract_error in _lean_statement_repeated_syntax_contract_errors(
                source
            ):
                errors.append(
                    "capability_eval source-to-bridge candidate "
                    f"{premise_id} Lean sketch {contract_error}"
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
    return {
        "required": required,
        "target_names": list(dict.fromkeys(target_names)),
        "target_ids": list(dict.fromkeys(target_ids)),
    }


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
    raw_response: str,
    theory_packet: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any] | None = None,
    environment_feedback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body = dict(payload)
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
    _fail_closed_placeholder_lean_candidates(
        body,
        environment_feedback or {},
    )
    _normalize_executable_candidate_expected_statuses(body)
    _normalize_source_theorem_target_shape_drift(
        body,
        environment_feedback or {},
    )
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


def _normalize_required_formalizer_scaffolding_fields(packet: dict[str, Any]) -> None:
    """Fill omitted non-proof routing scaffolding so safe candidates can proceed."""

    normalized: list[str] = []
    if packet.get("lemma_dependency_plan") in (None, "", [], {}):
        packet["lemma_dependency_plan"] = [
            {
                "from": "formalizer_candidate_or_gap",
                "to": "local_lean_or_prover_feedback",
                "role": "route emitted candidates or blockers through verifier feedback",
                "risk": (
                    "auto-filled planning metadata is not proof evidence and "
                    "does not supply theorem content"
                ),
            }
        ]
        normalized.append("lemma_dependency_plan")
    if packet.get("retrieval_queries") in (None, "", [], {}):
        packet["retrieval_queries"] = [
            {
                "query": "retrieve local Lean declarations and proof-state context for emitted formalizer candidate or blocker",
                "target_library": "LeanRAG",
                "purpose": "support bounded Formalizer/ProofEngineer repair before kernel checking",
            }
        ]
        normalized.append("retrieval_queries")
    if packet.get("proof_search_plan") in (None, "", [], {}):
        packet["proof_search_plan"] = {
            "preferred_tools": ["local_lean", "lean_lsp_mcp"],
            "tactic_or_certificate_hints": [],
            "kernel_check_plan": [
                "AgentRuntime must materialize and locally check any NEEDS_KERNEL_CHECK Lean candidate"
            ],
            "known_blockers": [
                "LLM omitted proof_search_plan; runtime filled routing metadata only"
            ],
        }
        normalized.append("proof_search_plan")
    if packet.get("gap_taxonomy") in (None, "", [], {}):
        packet["gap_taxonomy"] = [
            {
                "gap": (
                    "Formalizer packet omitted gap taxonomy; keep proof claims "
                    "proposal-only until verifier feedback is available"
                ),
                "kind": "other",
                "next_owner": "FormalizerProofEngineer",
            }
        ]
        normalized.append("gap_taxonomy")
    if packet.get("critic_findings") in (None, "", [], {}):
        packet["critic_findings"] = [
            {
                "critic": "local_formalizer_packet_normalizer",
                "finding": (
                    "Inserted missing non-proof packet scaffolding so validation "
                    "can focus on candidate safety and verifier routing."
                ),
                "reroute_if_confirmed": "FormalizerProofEngineer",
            }
        ]
        normalized.append("critic_findings")
    if packet.get("next_actions") in (None, "", [], {}):
        packet["next_actions"] = [
            {
                "owner_agent": "AgentRuntime",
                "action": (
                    "Materialize verifier-eligible candidates or route explicit "
                    "formal blockers back to Formalizer/ProofEngineer."
                ),
                "acceptance_gate": (
                    "local validation accepts the packet; proof evidence still "
                    "requires local Lean/AXLE or prover feedback"
                ),
            }
        ]
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
        "AUTO_FILLED_ROUTING_SCAFFOLDING_NOT_PROOF_EVIDENCE"
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
        lean_source = str(
            row.get("premise_derivation_candidate_lean_source", "")
            or row.get("lean_statement_sketch", "")
            or row.get("candidate_lean_source", "")
            or ""
        )
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
    if not _feedback_requires_probability_measure_coverage_shape(environment_feedback):
        return

    formal_targets = [
        row
        for row in packet.get("formal_targets", []) or []
        if isinstance(row, dict)
    ]
    rerouted: list[dict[str, Any]] = []
    first_source_target_declaration = ""
    first_source_goal_id = ""
    for index, row in enumerate(formal_targets, start=1):
        lean_source = str(row.get("lean_statement_sketch", "") or "")
        if not lean_source.strip():
            continue
        if _lean_source_is_descriptive_placeholder(lean_source):
            continue
        if not _formal_target_is_source_theorem_candidate(row):
            continue
        if _lean_source_has_probability_or_measure_shape(lean_source):
            continue
        provenance = row.get("source_theorem_target_provenance", {})
        previous_provenance = dict(provenance) if isinstance(provenance, Mapping) else {}
        declaration = str(
            previous_provenance.get("target_lean_declaration", "")
            or row.get("target_lean_declaration", "")
            or ""
        ).strip()
        goal_id = str(previous_provenance.get("source_theorem_goal_id", "") or "").strip()
        if declaration and not first_source_target_declaration:
            first_source_target_declaration = declaration
        if goal_id and not first_source_goal_id:
            first_source_goal_id = goal_id
        previous_provenance["source_theorem_target_known"] = False
        previous_provenance[
            "diagnostic_helper_from_source_theorem_shape_drift"
        ] = True
        row["source_theorem_target_provenance"] = previous_provenance
        row["diagnostic_helper_not_source_theorem"] = True
        row["source_theorem_shape_normalizer_status"] = (
            "SOURCE_THEOREM_TARGET_SHAPE_DRIFT_REROUTED_TO_DIAGNOSTIC_HELPER"
        )
        if _formal_target_is_source_to_bridge_adapter_candidate(row, lean_source):
            row["runtime_materialization_route"] = (
                "source_theorem_proof_body_adapter_bridge"
            )
            row["skip_formalizer_lean_candidate_materialization"] = True
            row["adapter_candidate_route_status"] = (
                "SOURCE_THEOREM_ADAPTER_TARGET_REROUTED_TO_ADAPTER_BRIDGE"
            )
        row.setdefault(
            "proof_evidence_status",
            "SOURCE_THEOREM_SHAPE_DRIFT_REROUTED_NOT_PROOF_EVIDENCE",
        )
        rerouted.append(
            {
                "index": index,
                "id": str(row.get("id", "") or ""),
                "previous_target_lean_declaration": declaration,
                "previous_source_theorem_goal_id": goal_id,
                "runtime_materialization_route": str(
                    row.get("runtime_materialization_route", "") or ""
                ),
                "lean_source_fingerprint": stable_hash(lean_source)[:20],
            }
        )

    if not rerouted:
        return

    if not _has_explicit_source_theorem_formal_gap_target(formal_targets):
        formal_targets.append(
            {
                "id": "source_theorem_formal_gap_after_target_shape_repair",
                "informal_source": (
                    "source theorem remains a formal gap because the emitted "
                    "Lean candidate had helper/adapter shape rather than the "
                    "required probability or measure coverage conclusion"
                ),
                "lean_statement_sketch": "",
                "expected_status": "FORMAL_GAP",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": first_source_target_declaration,
                    "source_theorem_goal_id": first_source_goal_id,
                },
                "proof_evidence_status": (
                    "SOURCE_THEOREM_TARGET_SHAPE_DRIFT_FORMAL_GAP_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        packet["formal_targets"] = formal_targets

    existing = packet.get("rerouted_source_theorem_shape_drift_targets", [])
    if not isinstance(existing, list):
        existing = []
    packet["rerouted_source_theorem_shape_drift_targets"] = [
        *existing,
        *rerouted,
    ]
    gap_rows = packet.get("gap_taxonomy", [])
    if not isinstance(gap_rows, list):
        gap_rows = []
    gap_rows.append(
        {
            "gap": (
                "A Lean candidate marked as the source theorem did not preserve "
                "the required probability/measure coverage conclusion, so it was "
                "rerouted as diagnostic helper work and the source theorem remains "
                "FORMAL_GAP."
            ),
            "kind": "source_theorem_target_shape_drift_rerouted",
            "next_owner": "Formalizer/ProofEngineer",
            "proof_evidence_status": (
                "SOURCE_THEOREM_TARGET_SHAPE_DRIFT_REROUTED_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["gap_taxonomy"] = gap_rows
    findings = packet.get("critic_findings", [])
    if not isinstance(findings, list):
        findings = []
    findings.append(
        {
            "critic": "local_formalizer_packet_normalizer",
            "finding": (
                "Rerouted source-theorem-shaped provenance from Lean candidates "
                "whose conclusion was helper/adapter shaped instead of the "
                "required probability or measure coverage target."
            ),
            "proof_evidence_status": (
                "SOURCE_THEOREM_TARGET_SHAPE_DRIFT_REROUTED_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    packet["critic_findings"] = findings


def _formal_target_is_source_to_bridge_adapter_candidate(
    row: Mapping[str, Any],
    lean_source: str,
) -> bool:
    text_parts = [
        str(row.get(field, "") or "")
        for field in (
            "id",
            "informal_source",
            "target_lean_declaration",
            "source_theorem_goal_id",
            "runtime_materialization_route",
        )
    ]
    constraints = row.get("semantic_alignment_constraints", [])
    if isinstance(constraints, list | tuple | set):
        text_parts.extend(str(value or "") for value in constraints)
    text = " ".join(text_parts).lower()
    if "source_to_bridge_adapter" in text or "source-to-bridge adapter" in text:
        return True
    return bool(
        re.search(
            r"\b(?:theorem|lemma)\s+[A-Za-z_][A-Za-z0-9_'.]*source_to_bridge_adapter\b",
            lean_source,
        )
    )


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
        candidate_source = str(
            candidate.get("premise_derivation_candidate_lean_source", "")
            or candidate.get("lean_statement_sketch", "")
            or candidate.get("candidate_lean_source", "")
            or ""
        )
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
) -> None:
    if not _feedback_requests_placeholder_fail_closed(environment_feedback):
        return
    converted_targets: list[dict[str, Any]] = []
    for row in packet.get("formal_targets", []) or []:
        if not isinstance(row, dict):
            continue
        lean_source = str(row.get("lean_statement_sketch", "") or "")
        placeholder_error = _lean_statement_placeholder_syntax_error(lean_source)
        if not placeholder_error:
            continue
        converted_targets.append(
            {
                "id": str(row.get("id", "") or ""),
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
            candidate_source = str(
                candidate.get("premise_derivation_candidate_lean_source", "")
                or candidate.get("lean_statement_sketch", "")
                or candidate.get("candidate_lean_source", "")
                or ""
            )
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

    formal_targets = [
        row
        for row in packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
    ]
    if (
        _feedback_has_source_theorem_target_drift(environment_feedback)
        and not _has_explicit_source_theorem_formal_gap_target(formal_targets)
    ):
        formal_targets.append(
            {
                "id": "source_theorem_formal_gap_after_placeholder_repair",
                "informal_source": (
                    "source theorem remains unproved after placeholder Lean "
                    "sketches were removed"
                ),
                "lean_statement_sketch": "",
                "expected_status": "FORMAL_GAP",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "",
                    "source_theorem_goal_id": "",
                },
                "proof_evidence_status": (
                    "FORMAL_GAP_PLACEHOLDER_LEAN_SKETCH_REMOVED_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        packet["formal_targets"] = formal_targets

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
        candidate_source = str(
            candidate.get("premise_derivation_candidate_lean_source", "")
            or candidate.get("lean_statement_sketch", "")
            or candidate.get("candidate_lean_source", "")
            or ""
        )
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
            compact[key] = _compact_value(row.get(key))
    return compact


def _compact_premise_derivation_candidate_request(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return _compact_mapping(
        row,
        keys=(
            "artifact_kind",
            "candidate_request_id",
            "premise_name",
            "premise_target_type",
            "adapter_instantiation_group_id",
            "required_bridge_premise_names_for_shared_instantiation",
            "shared_adapter_instantiation_contract",
            "premise_candidate_declaration_name",
            "target_theorem_name",
            "target_lean_declaration",
            "required_formalizer_output_key",
            "required_candidate_fields",
            "candidate_contract",
            "premise_semantic_dependency_requirements",
            "exact_source_theorem_binders",
            "premise_semantic_anchor_binders",
            "premise_semantic_anchor_binder_names",
            "required_semantic_anchor_reference_names",
            "semantic_anchor_reference_gate",
            "bridge_object_instantiation_policy",
            "adapter_object_names_requiring_source_instantiation",
            "forbidden_actions",
            "proof_evidence_status",
        ),
    )


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
            "premise_candidate_declaration_names",
            "target_theorem_name",
            "target_lean_declaration",
            "required_formalizer_output_key",
            "required_candidate_fields",
            "candidate_contract",
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
                "premise_candidate_declaration_name",
                "premise_semantic_dependency_requirements",
                "required_semantic_anchor_reference_names",
                "adapter_object_names_requiring_source_instantiation",
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
                    "premise_candidate_declaration_name": str(
                        candidate_request.get("premise_candidate_declaration_name", "")
                        or diagnostic.get("premise_candidate_declaration_name", "")
                        or diagnostic.get(
                            "source_to_bridge_premise_candidate_declaration_name",
                            "",
                        )
                        or ""
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
        if not _source_to_bridge_candidate_has_source_binding_contract(candidate)
    ]
    allow_single_request_single_candidate_fallback = bool(
        len(unbound_candidates_before_autofill) == 1
        and len(single_request_shortcuts) == 1
        and not grouped_requests
    )
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if _source_to_bridge_candidate_has_source_binding_contract(candidate):
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
    for key in (
        "exact_source_theorem_binders",
        "premise_semantic_anchor_binders",
        "premise_semantic_anchor_binder_names",
        "required_semantic_anchor_reference_names",
        "semantic_anchor_reference_gate",
        "adapter_object_names_requiring_source_instantiation",
        "premise_target_type",
        "premise_candidate_declaration_name",
        "source_to_bridge_premise_candidate_declaration_name",
        "target_theorem_name",
        "target_lean_declaration",
        "candidate_contract",
    ):
        if candidate.get(key) in (None, "", [], {}):
            values = source.get(key, [])
            if values not in (None, "", [], {}):
                if isinstance(values, list | tuple | set):
                    candidate[key] = list(values)
                elif isinstance(values, Mapping):
                    candidate[key] = dict(values)
                else:
                    candidate[key] = values


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
    formal_blocker_resource_requests = [
        row
        for row in runtime_environment_feedback.get(
            "formal_blocker_resource_requests",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
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
    if repair_owner_agent == "ProofEngineer" or proofengineer_repair_context:
        instructions.append(
            "ProofEngineer repair loop is active: consume "
            "runtime_environment_feedback.proofengineer_repair_context, including "
            "the exact materialized Lean artifact paths, local Lean diagnostics, "
            "and available prover/search tools. Do not treat this as a fresh "
            "Formalizer proposal or a human-debugged patch; return a bounded "
            "ProofEngineer repair candidate, a smaller lemma split, or an explicit "
            "formal blocker that can be rerun by local Lean/AXLE. Prefer the "
            "prover loop lean_diagnostic_messages -> lean_goal -> "
            "lean_state_search/proof_search -> lean_multi_attempt -> "
            "local_lean_or_axle_rerun when those tools are available."
        )
        if (
            isinstance(proofengineer_repair_context, Mapping)
            and proofengineer_repair_context.get("formal_source_grounding_hits")
        ):
            instructions.append(
                "Formal-source grounding hits are available for this repair loop: "
                "use them only as API/premise suggestions from the configured prover "
                "corpus. A selected declaration or replacement still must compile "
                "under local Lean/AXLE on the exact repaired artifact before it becomes "
                "proof evidence. For unknown identifiers, replace only with a retrieved "
                "or otherwise verified local declaration, derive the fact from known "
                "primitives, or emit a FORMAL_GAP naming the missing API/dependency."
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
                "If capability-eval still needs one materialized helper, emit at "
                "most one no-import core Lean diagnostic helper over Prop variables "
                "tied to the semantic bridge; this helper is diagnostic only and "
                "not source-theorem proof evidence."
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
        if carried_local_lean_repair_contract.get("declaration_required"):
            instructions.append(
                "Mandatory declaration repair: the previous Lean source had no "
                "declaration. The next executable candidate must include one concrete "
                "`theorem` or `lemma` tied to the theorem/subclaim. "
                "Do not return only imports, comments, open commands, prose, or an "
                "empty Lean sketch."
            )
        if carried_local_lean_repair_contract.get("core_lean_only_helper_rule"):
            instructions.append(
                "Mandatory core-Lean helper repair: the active import/local Lean "
                "contract restricts no-import diagnostic helpers to Prop-level core "
                "Lean using Prop, Not, arrows, lambda/fun, and `exact`; do not use "
                "Real, <=, Nat.ceil, Finset, MeasureTheory, ENNReal, `linarith`, "
                "`ring`, or `norm_num` unless a narrow import providing those APIs "
                "has already been verified in this project. The source theorem itself "
                "must remain expected_status=FORMAL_GAP unless the real probability/"
                "measure statement can be checked."
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
            "candidate still preserves the probability/coverage conclusion. If the "
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
            "theorem as expected_status=FORMAL_GAP unless its probability/measure "
            "coverage statement can be checked, and either emit a concrete "
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
        or proof_memory_summary.get("source_to_bridge_metadata_authoring_required")
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
        target_shape_contract_text = (
            json.dumps(target_shape_contract, default=str).lower()
            if isinstance(target_shape_contract, Mapping)
            else ""
        )
        target_shape_requires_coverage = (
            "probability_or_measure_coverage_claim"
            == str(
                target_shape_contract.get("required_conclusion_family", "")
                if isinstance(target_shape_contract, Mapping)
                else ""
            )
            or (
                isinstance(target_shape_contract, Mapping)
                and "coverage" in target_shape_contract_text
                and any(
                    marker in target_shape_contract_text
                    for marker in ("probability", "measure")
                )
            )
        )
        has_forbidden_shortcut_validation = any(
            marker in validation_text
            for marker in (
                "unsupported contradiction proof shortcut",
                "absurd",
                "false.elim",
                "contradiction proof shortcut",
            )
        )
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
        if has_forbidden_shortcut_validation:
            instructions.append(
                "Mandatory forbidden-shortcut repair: do not use `absurd`, "
                "`False.elim`, fake contradictions, or fabricated impossible facts "
                "in any Lean source. If the claim cannot be derived from real source "
                "assumptions and verified helper lemmas, emit expected_status=FORMAL_GAP "
                "outside Lean source and explain the exact missing premise."
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
                target_shape_requires_coverage
                and not source_theorem_candidate_materialization_contract
            ):
                instructions.append(
                    "Mandatory coverage-theorem proof-hole reroute: because the source "
                    "theorem target is a probability/coverage claim, do not emit another "
                    "broad formal_targets NEEDS_KERNEL_CHECK coverage theorem unless the "
                    "Lean sketch has a complete no-sorry proof and preserves "
                    "target_shape_contract. If you cannot provide that complete proof, "
                    "set the source theorem formal target to expected_status=FORMAL_GAP "
                    "with no Lean sketch, then route smaller support work through "
                    "source_to_bridge_premise_derivation_candidates, lemma_dependency_plan, "
                    "or proof_bank_obligation_requests. Do not replace the source theorem "
                    "with arithmetic/rank helper lemmas in formal_targets."
                )
                if repeated_packet_failure:
                    instructions.append(
                        "Repeated coverage proof-hole escape hatch: emit the source "
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
                "Mandatory target-shape packet repair: if a source theorem is a "
                "probability/coverage claim, formal_targets with NEEDS_KERNEL_CHECK must "
                "preserve that probability/measure conclusion. Put arithmetic or rank "
                "helpers in support/source-to-bridge channels instead."
            )
            if target_drift_repair_contract:
                instructions.append(
                    "Mandatory target-drift two-lane packet repair: follow "
                    "runtime_environment_feedback.target_drift_repair_contract. "
                    "The source_theorem_lane must be either a faithful probability/"
                    "measure source theorem target or an expected_status=FORMAL_GAP "
                    "source theorem with empty Lean sketch. The support_lemma_lane is "
                    "the only place for arithmetic/order-statistic helper work."
                )
            if repeated_packet_failure and target_shape_requires_coverage:
                instructions.append(
                    "Repeated coverage target-shape failure escalation: do not emit any "
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
        has_contradiction_shortcut = (
            "false.elim" in precheck_text
            or "absurd" in precheck_text
            or "contradiction proof shortcut" in precheck_text
        )
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
                        "API. If capability-eval still needs one materialized helper, "
                        "emit at most one no-import core Lean diagnostic helper over "
                        "Prop variables tied to the semantic bridge; this helper is "
                        "diagnostic only and not source-theorem proof evidence."
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
                if local_lean_repair_contract.get("declaration_required"):
                    instructions.append(
                        "Mandatory declaration repair: the previous Lean source had no "
                        "declaration. The next executable candidate must include one "
                        "concrete `theorem` or `lemma` tied to the "
                        "theorem/subclaim. Do not return only imports, comments, open "
                        "commands, prose, or an empty Lean sketch."
                    )
                if local_lean_repair_contract.get("core_lean_only_helper_rule"):
                    instructions.append(
                        "Mandatory core-Lean helper repair: the active import/local "
                        "Lean contract restricts no-import diagnostic helpers to "
                        "Prop-level core Lean using Prop, Not, arrows, lambda/fun, "
                        "and `exact`; do not use Real, <=, Nat.ceil, Finset, "
                        "MeasureTheory, ENNReal, `linarith`, `ring`, or `norm_num` "
                        "unless a narrow import providing those APIs has already been "
                        "verified in this project. The source theorem itself must "
                        "remain expected_status=FORMAL_GAP unless the real probability/"
                        "measure statement can be checked."
                    )
                if local_lean_repair_contract.get("repeated_syntax_failure"):
                    instructions.append(
                        "Mandatory repeated parser/syntax repair: the previous repair "
                        "retry still failed the Lean parser. Do not emit another broad "
                        "formal_targets NEEDS_KERNEL_CHECK theorem with Greek or other "
                        "Unicode binders, `Type*` universe shorthand, pipeline syntax, "
                        "unsupported notation, or a large dependent statement. Emit "
                        "expected_status=FORMAL_GAP for the source theorem, or emit at "
                        "most one minimal ASCII/core Lean support lemma through a support "
                        "channel with exact source-binding metadata and rerun local Lean "
                        "before treating it as executable."
                    )
        if has_target_drift:
            instructions.append(
                "Mandatory source-theorem target-preservation repair: the previous "
                "candidate was rejected for source-theorem target drift. Preserve "
                "the source theorem's probability/coverage conclusion and semantic "
                "alignment constraints. Do not replace a coverage or marginal "
                "probability theorem with a standalone arithmetic, monotonicity, "
                "typing, or helper lemma in formal_targets. Put helper lemmas in "
                "lemma_dependency_plan/proof_bank requests, not as the claimed source "
                "theorem candidate."
            )
            instructions.append(
                "Target-drift fail-closed rule: do not satisfy capability-eval by "
                "placing an arithmetic/rank helper in formal_targets. If you cannot "
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
                    "support_lemma_lane for arithmetic/order-statistic helper work; never "
                    "put support_lemma_lane work in formal_targets as a source theorem "
                    "NEEDS_KERNEL_CHECK candidate."
                )
        if has_timeout:
            instructions.append(
                "Mandatory local-Lean timeout repair: the previous candidate reached "
                "local Lean but timed out. Prefer narrow imports and local namespaces "
                "over `import Mathlib`; keep the theorem statement small enough for "
                "local checking, but do not simplify away the source theorem's "
                "probability/coverage conclusion. If preserving the faithful theorem "
                "requires library work, return a FORMAL_GAP with a minimal dependency "
                "plan instead of a weaker theorem."
            )
            if "import mathlib" in candidate_source_text:
                instructions.append(
                    "Mandatory timeout scope-down repair: do not retry the same large "
                    "full source theorem with `import Mathlib`. Either emit the source "
                    "theorem as expected_status=FORMAL_GAP and route smaller support "
                    "work, or emit one compact Lean candidate with narrow imports that "
                    "assumes the already identified rank/coverage premise and proves "
                    "only the local arithmetic/probability lower-bound step. If the "
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
        if has_contradiction_shortcut:
            instructions.append(
                "Mandatory contradiction-shortcut repair: do not use `False.elim`, "
                "`absurd`, fake contradictory hypotheses, or fabricated impossible "
                "facts to close coverage/probability goals. Either derive the goal "
                "from real source assumptions and named bridge lemmas, or emit "
                "expected_status=FORMAL_GAP with the exact missing lemma/import in "
                "gap_taxonomy and next_actions."
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
                "Repeated invalid Lean-candidate escalation: a prior Formalizer repair "
                "attempt already returned a Lean candidate that failed runtime precheck "
                "or local Lean. Do not emit another NEEDS_KERNEL_CHECK candidate unless "
                "it removes every reported proof hole, contradiction shortcut, fake "
                "FORMAL_GAP constant, guessed import, target drift, and unknown identifier "
                "while preserving the source theorem target. If that faithful candidate "
                "cannot be written from real source assumptions, named bridge lemmas, and "
                "available imports, emit expected_status=FORMAL_GAP and list the missing "
                "lemma/import/semantic premise in gap_taxonomy and next_actions instead "
                "of retrying invalid Lean."
            )
    if proof_memory_summary.get("proof_bank_bridge_catalog_exhausted_by_memory"):
        instructions.append(
            "If proof_bank_runtime_memory_summary says "
            "proof_bank_bridge_catalog_exhausted_by_memory=true, do not spend the packet "
            "on more bridge-obligation requests; make the main formal target the "
            "theorem-level reduction closure for the listed remaining_theorem_goal_ids."
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
            "target fixed and propose a narrow proof-body repair plan using the reported "
            "Lean goal, failed tactic attempts, diagnostics, and helper lemmas. If "
            "source_theorem_exact_proof_body_verified_adapter_context_insufficient=true, "
            "preserve the kernel-verified adapter artifact/declaration as context and "
            "repair the exact source theorem proof body against the true Lean goal shape."
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
            "hypotheses such as exchangeability, quantile/rank construction, coverage-event "
            "identity, and tie-policy assumptions, or report the blocker."
        )
    if (
        mode == "source_to_bridge_premise_derivation_required"
        or proof_memory_summary.get("source_to_bridge_premise_derivation_required")
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
            "candidate. Use only those exact source binders and semantic anchors from "
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
        "proofengineer_repair_context": _compact_value(
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
        "candidate_diagnostics": _compact_value(
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
    if theory_trace_downstream_alignment_feedback:
        payload["theory_trace_downstream_alignment_feedback"] = _compact_value(
            theory_trace_downstream_alignment_feedback
        )
    formal_blocker_resource_requests = (
        feedback.get("formal_blocker_resource_requests", [])
        or input_summary.get("formal_blocker_resource_requests", [])
    )
    if formal_blocker_resource_requests:
        payload["formal_blocker_resource_requests"] = _compact_value(
            formal_blocker_resource_requests
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
    return payload


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
    validation_text = " ".join(
        str(error)
        for error in (
            feedback.get("validation_errors", [])
            or input_summary.get("validation_errors", [])
            or []
        )
    ).lower()
    if not isinstance(candidate_diagnostics, list | tuple):
        candidate_diagnostics = []
    precheck_text = " ".join(
        str(error)
        for row in candidate_diagnostics
        if isinstance(row, Mapping)
        for error in row.get("precheck_errors", []) or []
    ).lower()
    target_drift_detected = "source-theorem target drift" in precheck_text
    coverage_validation_detected = (
        "formal target" in validation_text
        and (
            "coverage" in validation_text
            or "probability" in validation_text
            or "measure" in validation_text
        )
    )
    if not target_drift_detected and not coverage_validation_detected:
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
            "Move arithmetic/order-statistic helper work to support channels such as "
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
            "standalone arithmetic inequality",
            "standalone order-statistic or ceiling bound",
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
    if "probability/coverage" in precheck_text or coverage_validation_detected:
        contract["required_conclusion_family"] = (
            "probability_or_measure_coverage_claim"
        )
        contract["required_conclusion_shape"] = (
            "The source theorem candidate must conclude an explicit probability or "
            "measure coverage lower bound tied to the prediction-set coverage event."
        )
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
    explicit_contract = dict(explicit) if isinstance(explicit, Mapping) else {}
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
    if "type mismatch" in local_lean_text or "application type mismatch" in local_lean_text:
        classes.append("lean_type_mismatch")
    if "source must contain a declaration" in local_lean_text:
        classes.append("lean_candidate_missing_declaration")
    candidate_source_text = " ".join(
        str(row.get("lean_source_excerpt", "") or "")
        for row in candidate_diagnostics
        if isinstance(row, Mapping)
    ).lower()
    if (
        "core-lean-only helper contract violation" in local_lean_text
        or "no-import helper uses non-core" in local_lean_text
        or "no-import diagnostic helper uses non-core" in local_lean_text
        or "do not use real" in local_lean_text
        or "do not use `real`" in local_lean_text
        or "le real" in local_lean_text
        or "lt real" in local_lean_text
        or "ofnat real" in local_lean_text
        or (
            "unknown tactic" in local_lean_text
            and any(
                marker in candidate_source_text
                for marker in ("real", "linarith", "norm_num", "ring")
            )
        )
    ):
        classes.append("lean_no_import_noncore_arithmetic")
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
        contract["core_lean_diagnostic_helper_shape"] = (
            "At most one no-import core Lean Prop helper may be emitted as diagnostic "
            "tooling evidence; it is not source-theorem proof evidence."
        )
        contract["core_lean_only_helper_rule"] = (
            "When the Mathlib root import is unavailable, any no-import diagnostic "
            "helper must use only core Lean propositions and functions: Prop, Not, "
            "->, lambda/fun, and `exact`. Do not use Real, <=, Nat.ceil, Finset, "
            "MeasureTheory, ENNReal, linarith, ring, or norm_num unless a narrow "
            "import providing those APIs has already been verified in the configured "
            "Lean project."
        )
        contract["core_lean_only_helper_example"] = (
            "theorem core_prop_bridge "
            "(target support : Prop) "
            "(h : support -> target) "
            "(hs : support) : target := by\n"
            "  exact h hs"
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
            "Do not retry tactics unavailable without imports; use direct core Lean "
            "`exact`/lambda proofs or emit a FORMAL_GAP/dependency blocker."
        )
    if "lean_no_import_noncore_arithmetic" in classes:
        contract["core_lean_only_helper_rule"] = (
            "If Mathlib remains unavailable, no-import helpers must use only core Lean "
            "Prop/Not/arrows/lambda/fun/exact. Do not use Real, <=, Nat.ceil, Finset, "
            "MeasureTheory, ENNReal, linarith, ring, or norm_num."
        )
        contract["core_lean_only_helper_example"] = (
            "theorem core_prop_bridge "
            "(target support : Prop) "
            "(h : support -> target) "
            "(hs : support) : target := by\n"
            "  exact h hs"
        )
    if "lean_candidate_missing_declaration" in classes:
        contract["declaration_required"] = True
        contract["declaration_repair_rule"] = (
            "The next executable Lean candidate must contain a concrete declaration "
            "introduced by `theorem` or `lemma`; auxiliary `def`/`example` "
            "declarations alone do not satisfy a Formalizer capability candidate. "
            "Do not return only imports, prose, comments, open commands, or an empty "
            "formal target. If a real theorem/lemma tied to the theorem/subclaim "
            "cannot be written, emit expected_status=FORMAL_GAP outside Lean source "
            "and name the blocker."
        )
        contract["declaration_required_keywords"] = [
            "theorem",
            "lemma",
        ]
    return _merge_feedback_local_lean_repair_contracts(
        explicit_contract,
        contract,
    )


def _merge_feedback_local_lean_repair_contracts(
    explicit_contract: Mapping[str, Any],
    derived_contract: Mapping[str, Any],
) -> Mapping[str, Any]:
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
            "declaration_required_keywords",
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
        "source_theorem_exact_proof_body_repair_required",
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
        "formal_gap_next_action_contract",
        "formal_gap_next_action_diagnostics",
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
        "formalizer_lean_candidate_component_gate_feedback_available",
        "formalizer_lean_candidate_capability_feedback_available",
        "formalizer_runtime_capability_contract_feedback_available",
        "formalizer_lean_candidate_repair_manifest_paths",
        "formalizer_lean_candidate_repair_memory",
        "formalizer_lean_candidate_proof_state_feedback_memory",
        "formalizer_lean_candidate_component_gate_feedback_memory",
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
                "exact_goal_shape_obligation_ids",
                "exact_goal_shape_obligations",
                "semantic_alignment_constraints",
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
) -> dict[str, Any]:
    if not isinstance(proof_memory_summary, Mapping):
        return {}
    required = bool(
        proof_memory_summary.get("source_theorem_candidate_materialization_required")
        or proof_memory_summary.get("recommended_formalizer_target_mode")
        == "source_theorem_exact_candidate_materialization_required"
    )
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


def _compact_value(value: Any) -> Any:
    if isinstance(value, str):
        return value[:FORMALIZER_MAX_TEXT_CHARS]
    if isinstance(value, Mapping):
        priority_keys = (
            "feedback_kind",
            "contract_kind",
            "source",
            "source_theorem_proof_body_adapter_required",
            "source_theorem_proof_body_adapter_feedback_available",
            "adapter_kernel_verified",
            "target_names",
            "diagnostics",
            "diagnostic_classes",
            "required_behavior",
            "acceptance_gate",
            "proof_evidence_status",
            "blocked_import_prefixes",
            "mathlib_import_unavailable",
            "mathlib_root_import_unavailable",
            "core_lean_only_helper_rule",
            "core_lean_only_helper_example",
            "core_lean_diagnostic_helper_shape",
            "mathlib_repair_rule",
            "import_repair_rule",
            "suggested_import_replacements",
            "unknown_identifiers",
            "unknown_identifier_repair_rule",
            "repeated_syntax_failure",
            "repeated_syntax_failure_rule",
        )
        ordered_keys: list[Any] = [
            key
            for key in priority_keys
            if key in value and value.get(key) not in (None, "", [], {})
        ]
        for key in value:
            if key not in ordered_keys and value.get(key) not in (None, "", [], {}):
                ordered_keys.append(key)
        return {
            str(key): _compact_value(child)
            for key in ordered_keys[:16]
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
        (
            r"\bFalse\.elim\b",
            "contains unsupported contradiction-elimination proof shortcut False.elim",
        ),
        (
            r"\babsurd\b",
            "contains unsupported contradiction proof shortcut absurd",
        ),
    )
    for pattern, message in patterns:
        if re.search(pattern, source, flags=re.IGNORECASE):
            return message
    return ""


def _lean_statement_repeated_syntax_contract_errors(source: str) -> list[str]:
    text = str(source or "")
    if not text:
        return []
    errors: list[str] = []
    if re.search(r"\bType\s*\*", text):
        errors.append(
            "violates repeated parser/syntax repair contract: `Type*` universe "
            "shorthand is forbidden after a repeated parser failure; use `Type`, "
            "an explicit universe, FORMAL_GAP, or a minimal ASCII/core support lemma"
        )
    if "|>" in text:
        errors.append(
            "violates repeated parser/syntax repair contract: pipeline syntax `|>` "
            "is forbidden after a repeated parser failure"
        )
    if any(ord(ch) > 127 for ch in text):
        errors.append(
            "violates repeated parser/syntax repair contract: non-ASCII Lean syntax "
            "or binders are forbidden after a repeated parser failure; use ASCII "
            "identifiers and parser-simple core Lean"
        )
    return errors


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
    for key in (
        "exact_source_theorem_binders",
        "premise_semantic_anchor_binders",
        "premise_semantic_anchor_binder_names",
        "required_semantic_anchor_reference_names",
        "adapter_object_names_requiring_source_instantiation",
    ):
        if row.get(key) not in (None, "", [], {}):
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
