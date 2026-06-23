from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion


FORMALIZER_SCHEMA_VERSION = 1
FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE = "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE"
FORMALIZER_BOUNDARY = (
    "LLM Formalizer/ProofEngineer packets are formalization and proof-search "
    "proposals only. They do not count as target-prover proof evidence, do not "
    "certify source theorem faithfulness, and cannot claim kernel verification. "
    "Proof evidence requires AgentRuntime to run AXLE/local Lean or another "
    "target-prover kernel verification on the intended formal claim."
)
FORMALIZER_MAX_THEORY_ROWS = 3
FORMALIZER_MAX_THEOREM_GOALS = 4
FORMALIZER_MAX_PROOF_BANK_ROWS = 12
FORMALIZER_MAX_TEXT_CHARS = 420


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
                "explicit_model_configured": bool(self.config.model),
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_formalizer_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=str(
                    response.metadata.get("effective_model_tier", "")
                    or self.config.model_tier
                ),
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_formalizer_packet,
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
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "prompt_mode": {
            "mode": "compact_minimal_proof_target_triage",
            "purpose": "choose minimal formal targets and proof-bank obligations before kernel gates",
            "max_items_per_list": 3,
            "do_not_expand_full_derivations": True,
        },
        "theory_packet_summary": {
            "packet_id": theory_packet.get("packet_id", ""),
            "theorem_cards": theorem_cards,
            "lemma_cards": lemma_cards,
            "proof_plan": _compact_value(theory_packet.get("proof_plan", {}) if isinstance(theory_packet, Mapping) else {}),
            "formalization_requests": formalization_requests,
            "omitted_counts": {
                "theorem_cards": _safe_len(theory_packet.get("theorem_cards", []) if isinstance(theory_packet, Mapping) else []),
                "lemma_cards": _safe_len(theory_packet.get("lemma_cards", []) if isinstance(theory_packet, Mapping) else []),
                "formalization_requests": _safe_len(theory_packet.get("formalization_requests", []) if isinstance(theory_packet, Mapping) else []),
            },
        },
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
        "proof_bank_runtime_memory_summary": _compact_proof_bank_runtime_memory_summary(
            proof_bank_runtime_memory_summary or {}
        ),
        "proof_bank_obligation_request_policy": {
            "use_only_registered_catalog_ids_when_possible": True,
            "request_effect": "priority_only_for_kernel_smoke_selection",
            "runtime_filter": "AgentRuntime rejects unknown obligation IDs and filters against the current candidate set",
            "not_evidence": (
                "A proof-bank obligation request is not target-prover proof "
                "evidence and does not prove the frontier theorem."
            ),
            "when_catalog_exhausted_by_kernel_memory": (
                "Do not request already-kernel-verified bridge obligations again. "
                "Target the theorem-level reduction closure that connects those "
                "verified bridge obligations to the remaining frontier theorem goal."
            ),
        },
        "formal_target_portability_policy": {
            "preferred_fields": [
                "target_prover_family",
                "formal_statement_sketch",
                "formal_imports",
            ],
            "lean_legacy_aliases": ["lean_statement_sketch", "lean_imports"],
            "alias_policy": (
                "Use lean_* aliases only for Lean targets. For Rocq/Coq, "
                "Isabelle, Agda, HOL4, or other target provers, use only "
                "target-prover-neutral formal_* fields."
            ),
        },
        "required_output_contract": FORMALIZER_OUTPUT_CONTRACT,
        "boundary": FORMALIZER_BOUNDARY,
    }
    return (
        "Design formalization and proof-search artifacts for the Formalizer/ProofEngineer subsystem. "
        "Return ONLY compact JSON matching required_output_contract. Keep each list to at most 3 items. "
        "Prefer one minimal formal target plus one or two registered proof-bank obligations over a broad "
        "formalization essay. Use target-prover-neutral formal_statement_sketch/formal_imports "
        "fields, with lean_statement_sketch/lean_imports only as Lean legacy aliases. "
        "You may propose formal statement sketches, lemma dependency plans, source "
        "retrieval queries, and kernel-check work orders, but do not claim the theorem is proved, do not "
        "claim kernel verification, and do not hide formal gaps. "
        "For proof_bank_obligation_requests, choose obligation_id values from "
        "registered_proof_bank_obligation_catalog when possible; these requests only prioritize "
        "AgentRuntime kernel-smoke work and may be filtered or rejected by the runtime. "
        "If proof_bank_runtime_memory_summary says proof_bank_bridge_catalog_exhausted_by_memory=true, "
        "do not spend the packet on more bridge-obligation requests; make the main formal target "
        "the theorem-level reduction closure for the listed remaining_theorem_goal_ids.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str)
    )


FORMALIZER_SYSTEM_PROMPT = """\
You are the LLM Formalizer/ProofEngineer inside an AI Statistician AgentRuntime.

Your job is to translate statistical theorem proposals into Lean/formal target plans,
dependency DAGs, proof-search tasks, and kernel-verification work orders. You
are a generator, not the verifier. Do not report target-prover proofs as checked
unless AgentRuntime provides AXLE/local Lean or target-prover kernel evidence.
"""


FORMALIZER_OUTPUT_CONTRACT: dict[str, Any] = {
    "formal_targets": [
        {
            "id": "string",
            "informal_source": "string",
            "target_prover_family": "lean4|rocq|isabelle|agda|hol4|other",
            "formal_statement_sketch": "target-prover statement sketch",
            "formal_imports": ["target prover imports/theories"],
            "lean_statement_sketch": "Lean-only legacy alias for formal_statement_sketch",
            "lean_imports": ["Lean-only legacy alias for formal_imports"],
            "semantic_alignment_constraints": ["string"],
            "expected_status": "OPEN",
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
        target_prover_key = _formal_target_prover_key(row)
        if not target_prover_key:
            errors.append("formal target missing target_prover_family")
        formal_statement = str(row.get("formal_statement_sketch", "") or "").strip()
        lean_statement = str(row.get("lean_statement_sketch", "") or "").strip()
        if not formal_statement and not lean_statement:
            errors.append("formal target missing formal_statement_sketch")
        if target_prover_key and target_prover_key != "lean4":
            if lean_statement or "lean_statement_sketch" in row:
                errors.append(
                    "non-Lean formal target must use formal_statement_sketch, not lean_statement_sketch"
                )
            if row.get("lean_imports"):
                errors.append(
                    "non-Lean formal target must use formal_imports, not lean_imports"
                )
        if str(row.get("expected_status", "OPEN")) not in {"OPEN", "FORMAL_GAP", "NEEDS_KERNEL_CHECK"}:
            errors.append(f"unsupported formal target expected_status: {row.get('expected_status')}")
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
    forbidden_packet = _contains_forbidden_proof_claim(packet)
    if forbidden_packet:
        errors.append(f"packet contains forbidden proof claim: {forbidden_packet}")
    return sorted(set(errors))


def _normalize_formalizer_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    body = dict(payload)
    body["formal_targets"] = _normalize_formal_targets(body.get("formal_targets", []))
    body["proof_evidence_status"] = FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE
    body["proof_evidence_boundary"] = FORMALIZER_BOUNDARY
    body["kernel_verified"] = False
    body["full_frontier_theorem_proved"] = False
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


def _normalize_formal_targets(value: Any) -> list[Any]:
    if not isinstance(value, list | tuple):
        return []
    normalized: list[Any] = []
    for item in value:
        if not isinstance(item, Mapping):
            normalized.append(item)
            continue
        row = dict(item)
        target_prover_family = str(
            row.get("target_prover_family")
            or row.get("prover_family")
            or row.get("target_prover")
            or "lean4"
        ).strip()
        row["target_prover_family"] = target_prover_family
        target_prover_key = _formal_target_prover_key(row)
        formal_statement = str(row.get("formal_statement_sketch", "") or "").strip()
        lean_statement = str(row.get("lean_statement_sketch", "") or "").strip()
        if not formal_statement and lean_statement:
            row["formal_statement_sketch"] = lean_statement
        elif formal_statement and target_prover_key == "lean4" and not lean_statement:
            row["lean_statement_sketch"] = formal_statement
        formal_imports = _string_list(row.get("formal_imports", []))
        lean_imports = _string_list(row.get("lean_imports", []))
        if not formal_imports and lean_imports:
            row["formal_imports"] = lean_imports
        elif formal_imports and target_prover_key == "lean4" and not lean_imports:
            row["lean_imports"] = formal_imports
        normalized.append(row)
    return normalized


def _formal_target_prover_key(row: Mapping[str, Any]) -> str:
    target = str(
        row.get("target_prover_family")
        or row.get("prover_family")
        or row.get("target_prover")
        or ""
    ).strip().lower()
    aliases = {
        "lean": "lean4",
        "lean4": "lean4",
        "mathlib": "lean4",
        "coq": "rocq",
        "coq8": "rocq",
        "rocq": "rocq",
        "isabelle": "isabelle",
        "isabelle/hol": "isabelle",
        "agda": "agda",
        "hol4": "hol4",
    }
    return aliases.get(target, target)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


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
    return {
        key: _compact_value(row.get(key))
        for key in keys
        if key in row and row.get(key) not in (None, "", [], {})
    }


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
        "memory_kernel_verified_theorem_reduction_closure_goal_ids",
        "memory_kernel_verified_source_theorem_semantic_support_obligation_ids",
        "memory_kernel_verified_source_theorem_semantic_primitive_ids",
        "source_theorem_semantic_primitive_support_already_kernel_verified",
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
        "source_theorem_exact_candidate_placeholder_resolution_plan",
        "source_theorem_exact_candidate_repair_diagnostics",
        "recommended_source_theorem_integration_action",
        "critic_high_priority_agenda_ids",
    )
    compact = _compact_mapping(row, keys=keys)
    if "memory_kernel_verified_proof_obligation_ids" in compact:
        values = compact["memory_kernel_verified_proof_obligation_ids"]
        if isinstance(values, list):
            compact["memory_kernel_verified_proof_obligation_ids"] = values[:12]
    return compact


def _compact_value(value: Any) -> Any:
    if isinstance(value, str):
        return value[:FORMALIZER_MAX_TEXT_CHARS]
    if isinstance(value, Mapping):
        return {
            str(key): _compact_value(child)
            for key, child in list(value.items())[:6]
            if child not in (None, "", [], {})
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
