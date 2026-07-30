from __future__ import annotations

from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion


def task_bound_formal_source_query_seeds(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
    max_queries: int = 3,
) -> list[str]:
    """Derive bounded semantic and declaration-name queries without domain rules."""

    candidates: list[str] = []

    def add_row(row: Mapping[str, Any], fields: Sequence[str]) -> None:
        parts = [
            str(row.get(field, "") or "").strip()
            for field in fields
            if str(row.get(field, "") or "").strip()
        ]
        if parts:
            candidates.append(" ".join(parts)[:1800])

    for row in theorem_goals[:1]:
        if isinstance(row, Mapping):
            add_row(row, ("title", "claim", "statement", "conclusion"))

    for row in theory_packet.get("formalization_requests", []) or []:
        if not isinstance(row, Mapping):
            continue
        add_row(row, ("target", "claim", "statement", "reason"))
        if len(candidates) >= 2:
            break

    derivation = theory_packet.get("theory_derivation_packet", {})
    handoff = (
        derivation.get("formalization_handoff", {})
        if isinstance(derivation, Mapping)
        else {}
    )
    if not isinstance(handoff, Mapping):
        handoff = {}
    for field in (
        "candidate_lean_targets",
        "required_definitions",
        "lemma_dependencies",
    ):
        for value in handoff.get(field, []) or []:
            text = str(value).strip()
            if text:
                candidates.append(text[:1000])

    if not candidates:
        candidates.append(
            " ".join(
                value
                for value in (question.title.strip(), question.description.strip())
                if value
            )[:1800]
        )
    return [
        value
        for value in dict.fromkeys(candidates)
        if value
    ][: max(0, int(max_queries))]


def formalizer_feedback_with_task_bound_formal_source_queries(
    feedback: Mapping[str, Any] | None,
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Seed a Formalizer turn through the existing bounded retrieval channel."""

    payload = dict(feedback) if isinstance(feedback, Mapping) else {}
    repair_context = (
        dict(payload.get("proofengineer_repair_context", {}) or {})
        if isinstance(payload.get("proofengineer_repair_context", {}), Mapping)
        else {}
    )
    if repair_context.get("formal_source_grounding_hits"):
        return payload

    existing_queries = [
        str(value).strip()
        for value in repair_context.get("retrieval_query_seeds", []) or []
        if str(value).strip()
    ]
    task_queries = task_bound_formal_source_query_seeds(
        question=question,
        theory_packet=theory_packet,
        theorem_goals=theorem_goals,
    )
    query_seeds = list(dict.fromkeys([*existing_queries, *task_queries]))[:5]
    if not query_seeds:
        return payload

    repair_context.setdefault(
        "context_kind",
        "task_bound_formal_source_grounding",
    )
    repair_context.setdefault("owner_subsystem", "FormalizerProofEngineer")
    repair_context["retrieval_query_seeds"] = query_seeds
    repair_context.setdefault(
        "retrieval_boundary",
        (
            "Retrieved declarations are prompt context only; the exact generated "
            "artifact must still pass active-project Lean/kernel verification."
        ),
    )
    payload["proofengineer_repair_context"] = repair_context
    payload.setdefault(
        "feedback_type",
        "formalizer_task_bound_formal_source_context",
    )
    payload.setdefault("repair_owner_agent", "FormalizerProofEngineer")
    return payload


def prompt_safe_formal_source_provenance(value: Any) -> Any:
    """Remove executable proof bodies from nested generic RAG provenance."""

    if isinstance(value, Mapping):
        payload = {
            str(key): prompt_safe_formal_source_provenance(child)
            for key, child in value.items()
            if str(key) != "candidate_proof_body"
        }
        candidate_proof_body = value.get("candidate_proof_body", "")
        if candidate_proof_body:
            body_text = str(candidate_proof_body)
            payload.setdefault("candidate_proof_body_hash", stable_hash(body_text))
            payload["candidate_proof_body_chars"] = len(body_text)
            payload["candidate_proof_body_prompt_policy"] = (
                "omitted_from_generic_rag_context_fetch_only_for_exact_candidate_execution"
            )
        return payload
    if isinstance(value, (list, tuple)):
        return [prompt_safe_formal_source_provenance(child) for child in value]
    return value


def unique_formal_source_hit_payloads(
    hit_payloads: Sequence[Mapping[str, Any]],
    *,
    seen_hit_keys: set[tuple[str, str, str, str]],
) -> tuple[list[dict[str, Any]], int]:
    """Deduplicate declaration outlines across prompt query groups."""

    unique_hits: list[dict[str, Any]] = []
    duplicate_hit_count = 0
    for raw_payload in hit_payloads:
        hit_payload = dict(raw_payload)
        hit_key = (
            str(hit_payload.get("source_id", "") or ""),
            str(hit_payload.get("path", "") or ""),
            str(hit_payload.get("line", 0) or 0),
            str(hit_payload.get("name", "") or ""),
        )
        if hit_key in seen_hit_keys:
            duplicate_hit_count += 1
            continue
        seen_hit_keys.add(hit_key)
        unique_hits.append(hit_payload)
    return unique_hits, duplicate_hit_count
