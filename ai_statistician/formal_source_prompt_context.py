from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion


FORMAL_SOURCE_OUTLINE_PROMPT_POLICY = (
    "The model receives a bounded local signature bundle: the qualified target, its "
    "Lean module, direct imports, and dependency-ordered premise modules, names, and "
    "signatures. Source-scoped queries may retain two ranked target candidates. Rich "
    "provenance, source prose, citation crosswalks, architecture summaries, nearby "
    "naming examples, downstream declarations, and proof bodies remain in runtime "
    "artifacts but are omitted from the model prompt. Per-hit source activation says "
    "whether a declaration is in the active import closure, a direct dependency, or "
    "an external port candidate. It is routing context, not proof evidence. Retrieved "
    "declarations remain candidate context until the exact target artifact passes "
    "active-project Lean/kernel checking."
)
FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS = 5600
PROOFENGINEER_REPAIR_QUERY_ROLES = frozenset(
    {
        "live_proof_state_or_diagnostic",
        "repair_context_seed",
        "unknown_identifier_api_repair",
    }
)


def compact_formal_source_grounding_hits_for_prompt(value: Any) -> list[dict[str, Any]]:
    """Project retrieval groups into a bounded, query-diverse signature bundle."""

    if not isinstance(value, list | tuple):
        return []
    groups = [group for group in value[:3] if isinstance(group, Mapping)]
    selected: list[
        tuple[Mapping[str, Any], list[Mapping[str, Any]]]
    ] = []
    seen_hits: set[tuple[str, str, int, str, str]] = set()
    for group in groups:
        source_scoped = bool(group.get("source_scope_ids"))
        exact_target_query = _formal_source_group_has_exact_target_query(group)
        hit_limit = 2 if source_scoped and not exact_target_query else 1
        group_hits: list[Mapping[str, Any]] = []
        for hit in group.get("hits", []) or []:
            if not isinstance(hit, Mapping):
                continue
            identity = _formal_source_hit_prompt_identity(hit)
            if identity in seen_hits:
                continue
            seen_hits.add(identity)
            group_hits.append(hit)
            if len(group_hits) >= hit_limit:
                break
        if group_hits:
            selected.append((group, group_hits))
    if not selected:
        return []

    projected_groups: list[dict[str, Any]] = []
    for group_index, (group, hits) in enumerate(selected):
        query_role = str(group.get("query_role", "") or "")[:120]
        repair_focused = query_role in PROOFENGINEER_REPAIR_QUERY_ROLES
        projected_group: dict[str, Any] = {
            "query_role": query_role,
            "hits": [
                _compact_formal_source_hit_for_prompt(
                    hit,
                    primary=group_index == 0 and hit_index == 0,
                    repair_focused=repair_focused,
                )
                for hit_index, hit in enumerate(hits)
            ],
        }
        unknown_identifier = str(
            group.get("unknown_identifier", "") or ""
        ).strip()
        if unknown_identifier:
            projected_group["unknown_identifier"] = unknown_identifier[:240]
        projected_groups.append(
            {
                key: child
                for key, child in projected_group.items()
                if child not in (None, "", [], {})
            }
        )
    _fit_formal_source_prompt_projection(projected_groups)
    return projected_groups


def _formal_source_group_has_exact_target_query(group: Mapping[str, Any]) -> bool:
    query = " ".join(str(group.get("query", "") or "").split())
    hits = group.get("hits", []) or []
    if not query or not isinstance(hits, list | tuple) or not hits:
        return False
    first_hit = hits[0]
    if not isinstance(first_hit, Mapping):
        return False
    name = str(first_hit.get("name", "") or "").strip()
    return bool(name and query in {name, name.rsplit(".", 1)[-1]})


def _formal_source_hit_prompt_identity(
    hit: Mapping[str, Any],
) -> tuple[str, str, int, str, str]:
    signature = " ".join(str(hit.get("signature", "") or "").split())
    return (
        str(hit.get("source_id", "") or ""),
        str(hit.get("path", "") or ""),
        int(hit.get("line", 0) or 0),
        str(hit.get("name", "") or ""),
        signature,
    )


def _compact_formal_source_hit_for_prompt(
    hit: Mapping[str, Any],
    *,
    primary: bool,
    repair_focused: bool,
) -> dict[str, Any]:
    payload = {
        "source_id": str(hit.get("source_id", "") or "")[:120],
        "name": str(hit.get("name", "") or "")[:240],
    }
    signature = str(hit.get("signature", "") or "")
    if signature:
        payload["signature"] = signature
    context = hit.get("declaration_source_context", {})
    if isinstance(context, Mapping):
        source_activation = _compact_formal_source_activation_for_prompt(context)
        if source_activation:
            payload["source_activation"] = source_activation
        payload["declaration_source_context"] = (
            _compact_declaration_source_context_for_prompt(
                context,
                primary=primary,
                repair_focused=repair_focused,
            )
        )
    return {
        key: child
        for key, child in payload.items()
        if child not in (None, "", [], {})
    }


def _compact_formal_source_activation_for_prompt(
    context: Mapping[str, Any],
) -> dict[str, str]:
    dependency_context = context.get("dependency_context", {})
    if not isinstance(dependency_context, Mapping):
        return {}
    topology = dependency_context.get("source_topology", {})
    candidate_policy = dependency_context.get("candidate_use_policy", {})
    if not isinstance(topology, Mapping):
        topology = {}
    if not isinstance(candidate_policy, Mapping):
        candidate_policy = {}
    payload = {
        "role": str(topology.get("role", "") or "")[:120],
        "relation_to_active_project": str(
            topology.get("relation_to_active_project", "") or ""
        )[:120],
        "compatibility_status": str(
            topology.get("compatibility_status", "") or ""
        )[:160],
        "classification": str(
            candidate_policy.get("classification", "") or ""
        )[:160],
        "activation_gate": str(
            candidate_policy.get("activation_gate", "") or ""
        )[:420],
    }
    return {
        key: value
        for key, value in payload.items()
        if value
    }


def _compact_declaration_source_context_for_prompt(
    context: Any,
    *,
    primary: bool,
    repair_focused: bool,
) -> dict[str, Any]:
    if not isinstance(context, Mapping):
        return {}
    premise_rows = [
        row
        for row in context.get("premise_declaration_outlines", []) or []
        if isinstance(row, Mapping)
    ][:6]
    import_limit = 4 if repair_focused else 6 if primary else 3
    selected_rows: list[Mapping[str, Any]] = []
    if primary:
        for scope, limit in (("statement", 1), ("proof", 2), ("unspecified", 1)):
            scoped_rows = [
                row
                for row in premise_rows
                if str(row.get("dependency_scope", "") or "") == scope
            ]
            selected_rows.extend(scoped_rows[:limit])
        for row in premise_rows:
            if len(selected_rows) >= 3:
                break
            if row not in selected_rows:
                selected_rows.append(row)
        selected_rows = selected_rows[:3]
    signature_budget = 3200 if primary else 0
    outlines: list[dict[str, Any]] = []
    for row in selected_rows:
        signature = str(row.get("signature", "") or "")
        if not signature or len(signature) > signature_budget:
            continue
        outline = {
            "dependency_scope": str(row.get("dependency_scope", "") or "")[:20],
            "module": str(row.get("module", "") or "")[:240],
            "name": str(row.get("name", "") or "")[:240],
            "signature": signature,
        }
        signature_budget -= len(signature)
        outlines.append(outline)
    payload: dict[str, Any] = {
        "module": str(context.get("module", "") or "")[:240],
        "imports": [
            str(item)[:180]
            for item in list(context.get("imports", []) or [])[:import_limit]
        ],
        "premise_declaration_outlines": outlines,
    }
    return {
        key: value
        for key, value in payload.items()
        if value not in (None, "", [], {})
    }


def _fit_formal_source_prompt_projection(groups: list[dict[str, Any]]) -> None:
    """Drop complete lower-value rows without emitting malformed signatures."""

    if not groups:
        return
    hit = groups[0]["hits"][0]
    context = hit.get("declaration_source_context", {})
    if _prompt_json_chars(groups) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS:
        return
    for group in groups[1:]:
        for secondary in group["hits"]:
            secondary.get("source_activation", {}).pop("activation_gate", None)
            secondary_context = secondary.get(
                "declaration_source_context",
                {},
            )
            secondary_context.pop("imports", None)
    if _prompt_json_chars(groups) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS:
        return
    context.pop("imports", None)
    if _prompt_json_chars(groups) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS:
        return
    for group in reversed(groups[1:]):
        while (
            _prompt_json_chars(groups)
            > FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS
            and len(group.get("hits", [])) > 1
        ):
            group["hits"].pop()
    while (
        _prompt_json_chars(groups) > FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS
        and len(groups) > 1
    ):
        groups.pop()
    if _prompt_json_chars(groups) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS:
        return

    primary_group = groups[0]
    primary_hit = primary_group["hits"][0]
    primary_context = primary_hit.get("declaration_source_context", {})
    while (
        _prompt_json_chars(groups) > FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS
        and len(primary_group.get("hits", [])) > 1
    ):
        primary_group["hits"].pop()
    if _prompt_json_chars(groups) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS:
        return

    premise_rows = primary_context.get("premise_declaration_outlines", []) or []
    while (
        _prompt_json_chars(groups) > FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS
        and premise_rows
    ):
        premise_rows.pop()
    if _prompt_json_chars(groups) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS:
        return

    primary_context.pop("premise_declaration_outlines", None)
    if _prompt_json_chars(groups) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS:
        return

    if primary_hit.pop("signature", None):
        primary_hit["signature_status"] = (
            "OMITTED_EXCEEDS_PROMPT_BOUND_QUERY_ACTIVE_LEAN_OUTLINE"
        )
    if _prompt_json_chars(groups) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS:
        return

    minimal_hit = {
        key: value
        for key, value in primary_hit.items()
        if key
        in {
            "source_id",
            "name",
            "signature",
            "signature_status",
            "source_activation",
        }
        and value not in (None, "", [], {})
    }
    module = str(primary_context.get("module", "") or "").strip()
    if module:
        minimal_hit["declaration_source_context"] = {"module": module[:240]}
    groups[:] = [
        {
            key: value
            for key, value in primary_group.items()
            if key
            in {
                "query_role",
                "unknown_identifier",
            }
            and value not in (None, "", [], {})
        }
        | {"hits": [minimal_hit]}
    ]


def _prompt_json_chars(value: Any) -> int:
    return len(json.dumps(value, separators=(",", ":"), ensure_ascii=False, default=str))


def task_bound_formal_source_query_seeds(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
    max_queries: int = 3,
) -> list[str]:
    """Derive exact-name-first, bounded semantic queries without domain rules."""

    exact_candidates: list[str] = []
    reference_candidates: list[str] = []
    semantic_candidates: list[str] = []
    support_candidates: list[str] = []

    def add_row(
        destination: list[str],
        row: Mapping[str, Any],
        fields: Sequence[str],
    ) -> None:
        parts = [
            str(row.get(field, "") or "").strip()
            for field in fields
            if str(row.get(field, "") or "").strip()
        ]
        if parts:
            destination.append(" ".join(parts)[:1800])

    def add_values(destination: list[str], values: Any) -> None:
        rows = values if isinstance(values, (list, tuple)) else [values]
        for value in rows:
            if isinstance(value, Mapping):
                parts = [
                    str(value.get(field, "") or "").strip()
                    for field in (
                        "citation",
                        "reference",
                        "source_ref",
                        "title",
                        "theorem",
                        "location",
                        "query",
                    )
                    if str(value.get(field, "") or "").strip()
                ]
                text = " ".join(dict.fromkeys(parts)).strip()
            else:
                text = str(value or "").strip()
            if text:
                destination.append(text[:1000])

    # A source-authored declaration identity is the most context-efficient
    # query when one is available. It is still only a retrieval hint: the
    # returned signature/import must be checked in the active project.
    for row in theorem_goals[:2]:
        if not isinstance(row, Mapping):
            continue
        for field in (
            "target_lean_declaration",
            "candidate_lean_declaration",
            "lean_declaration",
        ):
            add_values(exact_candidates, row.get(field, ""))

    derivation = theory_packet.get("theory_derivation_packet", {})
    handoff = (
        derivation.get("formalization_handoff", {})
        if isinstance(derivation, Mapping)
        else {}
    )
    if not isinstance(handoff, Mapping):
        handoff = {}
    add_values(exact_candidates, handoff.get("candidate_lean_targets", []))

    # Source citations are a separate retrieval lane from Lean declaration
    # identity and theorem semantics. Only explicit upstream values are used;
    # the runtime neither invents citations nor maps book titles to theorems.
    reference_fields = (
        "formal_source_queries",
        "source_references",
        "source_citations",
        "known_proof_sources",
    )
    for row in theorem_goals[:2]:
        if not isinstance(row, Mapping):
            continue
        for field in reference_fields:
            add_values(reference_candidates, row.get(field, []))
    for field in reference_fields:
        add_values(reference_candidates, handoff.get(field, []))
        add_values(reference_candidates, theory_packet.get(field, []))

    # Keep the natural-language theorem meaning separate from exact names. A
    # failed or stale declaration hint therefore cannot crowd semantic search
    # out of the bounded first-turn query set.
    for row in theorem_goals[:1]:
        if isinstance(row, Mapping):
            add_row(
                semantic_candidates,
                row,
                (
                    "title",
                    "informal_statement",
                    "claim",
                    "statement",
                    "conclusion",
                ),
            )
            add_row(
                support_candidates,
                row,
                ("proof_strategy",),
            )
            add_values(
                support_candidates,
                row.get("required_primitives", []),
            )

    for row in theory_packet.get("formalization_requests", []) or []:
        if not isinstance(row, Mapping):
            continue
        for field in reference_fields:
            add_values(reference_candidates, row.get(field, []))
        add_row(
            semantic_candidates,
            row,
            ("target", "claim", "statement", "reason"),
        )
        if semantic_candidates:
            break

    for field in (
        "required_definitions",
        "lemma_dependencies",
    ):
        add_values(support_candidates, handoff.get(field, []))

    if (
        not exact_candidates
        and not reference_candidates
        and not semantic_candidates
        and not support_candidates
    ):
        semantic_candidates.append(
            " ".join(
                value
                for value in (question.title.strip(), question.description.strip())
                if value
            )[:1800]
        )

    limit = max(0, int(max_queries))
    if limit == 0:
        return []
    ordered: list[str] = []
    if exact_candidates:
        ordered.append(exact_candidates[0])
    if reference_candidates and len(ordered) < limit:
        ordered.append(reference_candidates[0])
    if semantic_candidates and len(ordered) < limit:
        ordered.append(semantic_candidates[0])
    if support_candidates and len(ordered) < limit:
        ordered.append(support_candidates[0])
    ordered.extend(exact_candidates[1:])
    ordered.extend(reference_candidates[1:])
    ordered.extend(semantic_candidates[1:])
    ordered.extend(support_candidates[1:])
    return [value for value in dict.fromkeys(ordered) if value][:limit]


def task_bound_formal_source_scope_ids(
    *,
    theory_packet: Mapping[str, Any],
    theorem_goals: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    """Carry explicit source provenance into Formalizer retrieval."""

    discovered: list[str] = []

    def add_values(values: Any) -> None:
        rows = values if isinstance(values, (list, tuple)) else [values]
        discovered.extend(
            str(value).strip()
            for value in rows
            if not isinstance(value, Mapping) and str(value).strip()
        )

    def add_provenance(value: Any) -> None:
        if not isinstance(value, Mapping):
            return
        for field in ("source_id", "corpus_id", "formal_source_scope_id"):
            candidate = str(value.get(field, "") or "").strip()
            if candidate:
                discovered.append(candidate)

    derivation = theory_packet.get("theory_derivation_packet", {})
    handoff = (
        derivation.get("formalization_handoff", {})
        if isinstance(derivation, Mapping)
        else {}
    )
    if not isinstance(handoff, Mapping):
        handoff = {}
    for row in theorem_goals[:2]:
        if not isinstance(row, Mapping):
            continue
        add_values(row.get("formal_source_scope_ids", []))
        add_provenance(row.get("source_theorem_target_provenance", {}))
    for row in (theory_packet, handoff):
        add_values(row.get("formal_source_scope_ids", []))
        add_provenance(row.get("source_theorem_target_provenance", {}))
    for row in theory_packet.get("formalization_requests", []) or []:
        if not isinstance(row, Mapping):
            continue
        add_values(row.get("formal_source_scope_ids", []))
        add_provenance(row.get("source_theorem_target_provenance", {}))
    return tuple(dict.fromkeys(discovered))


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
    source_scope_ids = task_bound_formal_source_scope_ids(
        theory_packet=theory_packet,
        theorem_goals=theorem_goals,
    )
    if not query_seeds:
        return payload

    repair_context.setdefault(
        "context_kind",
        "task_bound_formal_source_grounding",
    )
    repair_context["retrieval_query_seeds"] = query_seeds
    if source_scope_ids:
        repair_context["formal_source_scope_ids"] = list(source_scope_ids)
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


def formal_source_context_for_hit(
    *,
    retriever: Any,
    hit: Any,
    max_outline_declarations: int = 2,
    max_outline_chars: int = 1600,
    max_dependency_neighbors: int = 10,
    max_premise_declarations: int = 6,
    max_premise_chars: int = 4200,
) -> dict[str, Any]:
    """Build a dependency-first, context-efficient declaration packet."""

    declaration = getattr(hit, "declaration", None)
    if declaration is None:
        return {}
    path = str(getattr(declaration, "path", "") or "")
    source_id = str(getattr(declaration, "source_id", "") or "")
    target_line = int(getattr(declaration, "line", 0) or 0)
    imports = [
        str(value)
        for value in getattr(declaration, "imports", ()) or ()
        if str(value).strip()
    ]
    dependency_context = _formal_source_dependency_context(
        retriever,
        str(getattr(declaration, "name", "") or ""),
        source_id=source_id,
        path=path,
        limit=max_dependency_neighbors,
    )
    premise_outline_rows = _formal_source_dependency_outline_rows(
        retriever,
        dependency_context=dependency_context,
        source_id=source_id,
        max_declarations=max_premise_declarations,
        max_chars=max_premise_chars,
    )
    premise_names = {
        str(row.get("name", "") or "")
        for row in premise_outline_rows
        if str(row.get("name", "") or "")
    }
    all_same_file = list(
        _formal_source_outline_rows_by_file(retriever).get((source_id, path), ())
    )
    prior_same_file = [
        row
        for row in all_same_file
        if not (
            int(getattr(row, "line", 0) or 0) == target_line
            and str(getattr(row, "name", "") or "")
            == str(getattr(declaration, "name", "") or "")
        )
        and (
            target_line <= 0
            or int(getattr(row, "line", 0) or 0) < target_line
        )
    ]
    same_file = [
        row
        for row in prior_same_file
        if str(getattr(row, "name", "") or "") not in premise_names
    ]
    same_file.sort(
        key=lambda row: (
            (
                target_line - int(getattr(row, "line", 0) or 0)
                if target_line > 0
                else int(getattr(row, "line", 0) or 0)
            ),
            str(getattr(row, "name", "") or ""),
        )
    )
    local_naming_rows = sorted(
        prior_same_file,
        key=lambda row: (
            (
                target_line - int(getattr(row, "line", 0) or 0)
                if target_line > 0
                else int(getattr(row, "line", 0) or 0)
            ),
            str(getattr(row, "name", "") or ""),
        ),
    )[:4]
    local_naming_examples = [
        {
            "kind": str(getattr(row, "kind", "") or ""),
            "name": str(getattr(row, "name", "") or ""),
            "namespace": str(getattr(row, "namespace", "") or ""),
        }
        for row in local_naming_rows
        if str(getattr(row, "name", "") or "").strip()
    ]
    outline_rows: list[dict[str, Any]] = []
    outline_chars = 0
    for row in same_file:
        if len(outline_rows) >= max(0, int(max_outline_declarations)):
            break
        signature = str(getattr(row, "signature", "") or "")[:1800]
        if not signature:
            continue
        remaining = max(0, int(max_outline_chars) - outline_chars)
        if remaining <= 0:
            break
        signature = signature[:remaining]
        outline_rows.append(
            {
                "line": int(getattr(row, "line", 0) or 0),
                "kind": str(getattr(row, "kind", "") or ""),
                "name": str(getattr(row, "name", "") or ""),
                "namespace": str(getattr(row, "namespace", "") or ""),
                "signature": signature,
                "reference": str(getattr(row, "reference", "") or ""),
                "reference_aliases": [
                    str(value)
                    for value in getattr(row, "reference_aliases", ()) or ()
                    if str(value).strip()
                ],
            }
        )
        outline_chars += len(signature)
    outline_rows.sort(key=lambda row: (int(row["line"]), str(row["name"])))

    if not any(
        (
            path,
            imports,
            premise_outline_rows,
            outline_rows,
            dependency_context,
            getattr(declaration, "declaration_doc", ""),
            getattr(declaration, "section_summary", ""),
            getattr(declaration, "module_group", ""),
        )
    ):
        return {}
    module = str(dependency_context.get("module", "") or "").strip()
    if not module:
        module = _formal_source_module_name(path, imports)
    payload: dict[str, Any] = {
        "module": module,
        "module_summary": str(
            getattr(declaration, "module_summary", "") or ""
        )[:800],
        "module_group": str(
            getattr(declaration, "module_group", "") or ""
        )[:240],
        "module_group_summary": str(
            getattr(declaration, "module_group_summary", "") or ""
        )[:800],
        "path": path,
        "imports": imports[:12],
        "premise_declaration_outlines": premise_outline_rows,
        "nearby_declaration_outlines": outline_rows,
        "local_naming_examples": local_naming_examples,
        "n_same_file_declarations": len(all_same_file),
        "n_prior_same_file_declarations": len(prior_same_file),
        "n_direct_premise_declaration_outlines": len(
            premise_outline_rows
        ),
        "n_prior_same_file_fallback_candidates": len(same_file),
        "n_downstream_same_file_declarations_omitted": sum(
            1
            for row in all_same_file
            if target_line > 0
            and int(getattr(row, "line", 0) or 0) > target_line
        ),
        "outline_selection": (
            "direct_statement_dependencies_then_direct_proof_dependencies_"
            "then_nearest_prior_same_file_fallback"
        ),
        "prompt_policy": FORMAL_SOURCE_OUTLINE_PROMPT_POLICY,
    }
    if dependency_context:
        payload["dependency_context"] = dependency_context
    source_architecture_route = _formal_source_architecture_route(
        retriever,
        source_id=source_id,
        target_module=module,
        target_layer=str(getattr(declaration, "module_group", "") or ""),
        dependency_context=dependency_context,
    )
    if source_architecture_route:
        payload["source_architecture_route"] = source_architecture_route
    return payload


def _formal_source_retriever_declarations(retriever: Any) -> tuple[Any, ...]:
    cached = getattr(retriever, "_prompt_outline_declarations", None)
    if isinstance(cached, tuple):
        return cached
    rows = getattr(retriever, "declarations", None)
    if rows is None:
        loader = getattr(retriever, "load_declarations", None)
        if callable(loader):
            try:
                rows = loader()
            except Exception:
                rows = ()
    declarations = tuple(rows or ())
    try:
        setattr(retriever, "_prompt_outline_declarations", declarations)
    except Exception:
        pass
    return declarations


def _formal_source_outline_rows_by_name(
    retriever: Any,
) -> tuple[
    dict[tuple[str, str], tuple[Any, ...]],
    dict[tuple[str, str], tuple[Any, ...]],
]:
    cached = getattr(retriever, "_prompt_outline_rows_by_name", None)
    if (
        isinstance(cached, tuple)
        and len(cached) == 2
        and all(isinstance(value, dict) for value in cached)
    ):
        return cached
    by_name: dict[tuple[str, str], list[Any]] = {}
    by_short_name: dict[tuple[str, str], list[Any]] = {}
    for row in _formal_source_retriever_declarations(retriever):
        source_id = str(getattr(row, "source_id", "") or "")
        name = str(getattr(row, "name", "") or "")
        if not name:
            continue
        by_name.setdefault((source_id, name), []).append(row)
        by_short_name.setdefault(
            (source_id, name.rsplit(".", 1)[-1]),
            [],
        ).append(row)
    index = (
        {key: tuple(rows) for key, rows in by_name.items()},
        {key: tuple(rows) for key, rows in by_short_name.items()},
    )
    try:
        setattr(retriever, "_prompt_outline_rows_by_name", index)
    except Exception:
        pass
    return index


def _formal_source_dependency_outline_rows(
    retriever: Any,
    *,
    dependency_context: Mapping[str, Any],
    source_id: str,
    max_declarations: int,
    max_chars: int,
) -> list[dict[str, Any]]:
    if not dependency_context:
        return []
    by_name, by_short_name = _formal_source_outline_rows_by_name(retriever)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int, str]] = set()
    used_chars = 0
    scope_limit = max(1, int(max_declarations) // 2)
    target_module = str(dependency_context.get("module", "") or "").strip()
    module_root = target_module.split(".", 1)[0] if target_module else ""
    for dependency_scope, field in (
        ("statement", "statement_uses"),
        ("proof", "proof_uses"),
        ("unspecified", "uses"),
    ):
        candidates_for_scope: list[tuple[int, Any]] = []
        for position, dependency_name in enumerate(
            dependency_context.get(field, []) or []
        ):
            name = str(dependency_name or "").strip()
            if not name:
                continue
            candidates = list(by_name.get((source_id, name), ()))
            if not candidates:
                short_candidates = by_short_name.get(
                    (source_id, name.rsplit(".", 1)[-1]),
                    (),
                )
                if len(short_candidates) == 1:
                    candidates = list(short_candidates)
            if len(candidates) == 1:
                candidates_for_scope.append((position, candidates[0]))
        if dependency_scope == "proof":
            kind_priority = {
                "theorem": 0,
                "lemma": 1,
                "instance": 2,
                "def": 3,
            }
            candidates_for_scope.sort(
                key=lambda item: (
                    kind_priority.get(
                        str(getattr(item[1], "kind", "") or ""),
                        4,
                    ),
                    item[0],
                )
            )
        n_scope_rows = 0
        for _position, declaration in candidates_for_scope:
            if len(rows) >= max(0, int(max_declarations)):
                return rows
            if (
                dependency_scope != "unspecified"
                and n_scope_rows >= scope_limit
            ):
                break
            key = (
                str(getattr(declaration, "source_id", "") or ""),
                str(getattr(declaration, "path", "") or ""),
                int(getattr(declaration, "line", 0) or 0),
                str(getattr(declaration, "name", "") or ""),
            )
            if key in seen:
                continue
            signature = str(getattr(declaration, "signature", "") or "")
            remaining = max(0, int(max_chars) - used_chars)
            if not signature or remaining <= 0:
                return rows
            if len(signature) > min(1800, remaining):
                continue
            seen.add(key)
            used_chars += len(signature)
            n_scope_rows += 1
            imports = [
                str(value)
                for value in getattr(declaration, "imports", ()) or ()
                if str(value).strip()
            ]
            rows.append(
                {
                    "dependency_scope": dependency_scope,
                    "line": key[2],
                    "kind": str(getattr(declaration, "kind", "") or ""),
                    "name": key[3],
                    "namespace": str(
                        getattr(declaration, "namespace", "") or ""
                    ),
                    "module": _formal_source_module_name(
                        key[1],
                        imports,
                        module_root=module_root,
                    ),
                    "path": key[1],
                    "signature": signature,
                    "reference": str(
                        getattr(declaration, "reference", "") or ""
                    ),
                    "reference_aliases": [
                        str(value)
                        for value in getattr(
                            declaration,
                            "reference_aliases",
                            (),
                        )
                        or ()
                        if str(value).strip()
                    ],
                }
            )
    return rows


def _formal_source_outline_rows_by_file(
    retriever: Any,
) -> dict[tuple[str, str], tuple[Any, ...]]:
    cached = getattr(retriever, "_prompt_outline_rows_by_file", None)
    if isinstance(cached, dict):
        return cached
    grouped: dict[tuple[str, str], list[Any]] = {}
    for row in _formal_source_retriever_declarations(retriever):
        key = (
            str(getattr(row, "source_id", "") or ""),
            str(getattr(row, "path", "") or ""),
        )
        grouped.setdefault(key, []).append(row)
    index = {key: tuple(rows) for key, rows in grouped.items()}
    try:
        setattr(retriever, "_prompt_outline_rows_by_file", index)
    except Exception:
        pass
    return index


def _formal_source_module_layer_index(
    retriever: Any,
) -> dict[tuple[str, str], str]:
    cached = getattr(retriever, "_prompt_module_layer_index", None)
    if isinstance(cached, dict):
        return cached
    index: dict[tuple[str, str], str] = {}
    for declaration in _formal_source_retriever_declarations(retriever):
        source_id = str(getattr(declaration, "source_id", "") or "")
        module = _formal_source_module_name(
            str(getattr(declaration, "path", "") or ""),
            tuple(getattr(declaration, "imports", ()) or ()),
        )
        layer = str(getattr(declaration, "module_group", "") or "").strip()
        if source_id and module and layer:
            index.setdefault((source_id, module), layer)
    try:
        setattr(retriever, "_prompt_module_layer_index", index)
    except Exception:
        pass
    return index


def _formal_source_module_layer(
    module_layers: Mapping[tuple[str, str], str],
    *,
    source_id: str,
    module: str,
) -> str:
    exact = str(module_layers.get((source_id, module), "") or "")
    if exact:
        return exact
    suffix_layers = {
        layer
        for (candidate_source_id, candidate_module), layer in module_layers.items()
        if candidate_source_id == source_id
        and candidate_module
        and module.endswith("." + candidate_module)
        and layer
    }
    return next(iter(suffix_layers)) if len(suffix_layers) == 1 else ""


def _formal_source_architecture_route(
    retriever: Any,
    *,
    source_id: str,
    target_module: str,
    target_layer: str,
    dependency_context: Mapping[str, Any],
) -> dict[str, Any]:
    if not dependency_context:
        return {}
    module_layers = _formal_source_module_layer_index(retriever)
    resolved_target_layer = target_layer.strip() or _formal_source_module_layer(
        module_layers,
        source_id=source_id,
        module=target_module,
    )
    raw_route = dependency_context.get("module_dependency_route", []) or []
    route: list[tuple[int, str]] = []
    for raw_row in raw_route:
        if isinstance(raw_row, Mapping):
            depth = int(raw_row.get("depth", 0) or 0)
            module = str(raw_row.get("module", "") or "").strip()
        elif isinstance(raw_row, (list, tuple)) and len(raw_row) >= 2:
            depth = int(raw_row[0] or 0)
            module = str(raw_row[1] or "").strip()
        else:
            continue
        if depth > 0 and module and module != target_module:
            route.append((depth, module))
    if not route:
        route = [
            (1, str(module).strip())
            for module in dependency_context.get("direct_module_imports", []) or []
            if str(module).strip() and str(module).strip() != target_module
        ]
    if not route and not resolved_target_layer:
        return {}

    grouped: dict[tuple[int, str], list[str]] = {}
    for depth, module in sorted(set(route), key=lambda row: (row[0], row[1])):
        layer = _formal_source_module_layer(
            module_layers,
            source_id=source_id,
            module=module,
        )
        modules = grouped.setdefault((depth, layer), [])
        if module not in modules:
            modules.append(module)
    upstream_layers = [
        {
            "depth": depth,
            "layer": layer,
            "modules": modules[:3],
        }
        for (depth, layer), modules in sorted(
            grouped.items(),
            key=lambda item: (item[0][0], item[0][1], item[1]),
        )[:8]
    ]
    return {
        "target_module": target_module,
        "target_layer": resolved_target_layer,
        "upstream_layers": upstream_layers,
        "evidence_status": (
            "SOURCE_IMPORT_GRAPH_AND_SOURCE_AUTHORED_LAYER_CONTEXT_NOT_PROOF_EVIDENCE"
        ),
    }


def _formal_source_dependency_context(
    retriever: Any,
    declaration_name: str,
    *,
    source_id: str,
    path: str,
    limit: int,
) -> dict[str, Any]:
    provider = getattr(retriever, "dependency_retriever", None)
    if provider is None and callable(getattr(retriever, "dependency_context", None)):
        provider = retriever
    context_loader = getattr(provider, "dependency_context", None)
    if not declaration_name or not callable(context_loader):
        return {}
    try:
        context = context_loader(
            declaration_name,
            limit=max(0, int(limit)),
            source_id=source_id,
            path=path,
        )
    except TypeError:
        try:
            context = context_loader(
                declaration_name,
                limit=max(0, int(limit)),
            )
        except Exception:
            return {}
    except Exception:
        return {}
    if context is None:
        return {}
    payload = {
        "provider": str(getattr(provider, "source", provider.__class__.__name__)),
        "corpus_id": str(getattr(context, "source_id", "") or source_id),
        "module": str(getattr(context, "module", "") or ""),
        "module_ancestry": [
            str(value)
            for value in getattr(context, "module_ancestry", ()) or ()
            if str(value).strip()
        ],
        "direct_module_imports": [
            str(value)
            for value in getattr(context, "direct_module_imports", ()) or ()
        ],
        "module_dependency_route": [
            {"depth": int(depth), "module": str(module)}
            for depth, module in (
                getattr(context, "module_dependency_route", ()) or ()
            )
            if int(depth) > 0 and str(module).strip()
        ],
        "module_import_visibility_enforced": bool(
            getattr(context, "module_import_visibility_enforced", False)
        ),
        "fan_in": int(getattr(context, "fan_in", 0) or 0),
        "fan_out": int(getattr(context, "fan_out", 0) or 0),
        "n_downstream_declarations_omitted": len(
            getattr(context, "used_by", ()) or ()
        ),
        "downstream_declarations_prompt_policy": (
            "omitted_from_target_proof_context"
        ),
        "dependency_resolution_policy": str(
            getattr(context, "dependency_resolution_policy", "") or ""
        ),
        "declaration_reference_policy": str(
            getattr(context, "declaration_reference_policy", "") or ""
        ),
        "dependency_kind": "source_visible_declaration_reference",
        "evidence_status": "SOURCE_DERIVED_DEPENDENCY_CONTEXT_NOT_PROOF_EVIDENCE",
    }
    raw_snapshot_metadata = getattr(context, "source_snapshot_metadata", ()) or ()
    try:
        snapshot_metadata = dict(raw_snapshot_metadata)
    except (TypeError, ValueError):
        snapshot_metadata = {}
    snapshot_status = str(
        getattr(context, "source_snapshot_status", "") or ""
    )
    topology_id = str(getattr(context, "source_topology_id", "") or "")
    source_role = str(getattr(context, "source_role", "") or "")
    source_relation = str(
        getattr(context, "source_relation_to_active_project", "") or ""
    )
    compatibility_status = str(
        getattr(context, "source_compatibility_status", "") or ""
    )
    source_reuse_policy = str(
        getattr(context, "source_reuse_policy", "") or ""
    )
    if topology_id:
        payload["source_topology"] = {
            "topology_id": topology_id,
            "role": source_role,
            "relation_to_active_project": source_relation,
            "compatibility_status": compatibility_status,
            "reuse_policy": source_reuse_policy,
            "identity_basis": [
                str(value)
                for value in (
                    getattr(context, "source_topology_identity_basis", ()) or ()
                )
                if str(value).strip()
            ],
            "evidence_status": str(
                getattr(context, "source_topology_evidence_status", "")
                or "SOURCE_TOPOLOGY_NOT_PROOF_EVIDENCE"
            ),
        }
    if snapshot_status or snapshot_metadata:
        payload["source_snapshot"] = {
            "status": snapshot_status or "UNBOUND",
            "bound": bool(getattr(context, "source_snapshot_bound", False)),
            "match": getattr(context, "source_snapshot_match", None),
            "metadata": snapshot_metadata,
            "evidence_status": (
                "SOURCE_SNAPSHOT_IDENTITY_NOT_ACTIVE_PROJECT_PROOF_EVIDENCE"
            ),
        }
        canonical_import_closure = bool(
            snapshot_status == "BOUND_MATCH"
            and snapshot_metadata.get("entry_module")
            and snapshot_metadata.get("corpus_scope_policy")
            == "recursive_import_closure_v1"
        )
        classification = (
            "version_bound_canonical_import_closure_candidate"
            if canonical_import_closure
            else "version_bound_external_source_candidate"
            if snapshot_status == "BOUND_MATCH"
            else "unbound_or_stale_source_candidate"
        )
        activation_gate = (
            "require target-project import visibility and exact local Lean "
            "re-elaboration before reuse"
        )
        if topology_id and snapshot_status == "BOUND_MATCH":
            if source_relation == "active_project":
                classification = "active_project_import_closure_candidate"
            elif source_relation == "direct_lake_dependency":
                classification = "direct_dependency_import_closure_candidate"
            elif source_relation == "external_companion":
                classification = "external_companion_port_candidate"
                activation_gate = (
                    "port into the active Lean and Mathlib toolchain, expose through "
                    "the target import closure, and exactly re-elaborate locally "
                    "before reuse"
                )
        payload["candidate_use_policy"] = {
            "classification": classification,
            "snapshot_meaning": (
                "source freshness only; not active-project compatibility or proof"
            ),
            "activation_gate": activation_gate,
        }
    statement_uses = [
        str(value)
        for value in getattr(context, "statement_uses", ()) or ()
    ]
    proof_uses = [
        str(value)
        for value in getattr(context, "proof_uses", ()) or ()
    ]
    if statement_uses or proof_uses:
        payload["statement_uses"] = statement_uses
        payload["proof_uses"] = proof_uses
        if proof_uses:
            payload["proof_dependency_origin"] = (
                "explicit_references_extracted_from_target_source_proof"
            )
            payload["proof_dependency_evaluation_policy"] = (
                "permitted_for_production_source_reuse_but_excluded_from_held_out_"
                "or_from_scratch_prover_generalization_claims"
            )
    else:
        payload["uses"] = [
            str(value)
            for value in getattr(context, "uses", ()) or ()
        ]
    cross_source_statement_uses = _cross_source_reference_payloads(
        getattr(context, "cross_source_statement_uses", ()) or ()
    )
    cross_source_proof_uses = _cross_source_reference_payloads(
        getattr(context, "cross_source_proof_uses", ()) or ()
    )
    if cross_source_statement_uses or cross_source_proof_uses:
        payload["cross_source_statement_uses"] = cross_source_statement_uses
        payload["cross_source_proof_uses"] = cross_source_proof_uses
        payload["cross_source_dependency_policy"] = str(
            getattr(context, "cross_source_dependency_policy", "") or ""
        )
        payload["cross_source_evidence_status"] = str(
            getattr(context, "cross_source_evidence_status", "")
            or "SOURCE_DERIVED_CROSS_CORPUS_REFERENCE_NOT_PROOF_EVIDENCE"
        )
        if cross_source_proof_uses:
            payload["cross_source_proof_dependency_origin"] = (
                "explicit_references_extracted_from_target_source_proof"
            )
            payload["cross_source_proof_dependency_evaluation_policy"] = (
                "permitted_for_production_source_reuse_but_excluded_from_held_out_"
                "or_from_scratch_prover_generalization_claims"
            )
    return payload


def _cross_source_reference_payloads(
    references: Sequence[Any],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for reference in references:
        source_id = str(getattr(reference, "source_id", "") or "").strip()
        declaration_name = str(
            getattr(reference, "declaration_name", "") or ""
        ).strip()
        match_kind = str(getattr(reference, "match_kind", "") or "").strip()
        if not source_id or not declaration_name:
            continue
        rows.append(
            {
                "source_id": source_id,
                "name": declaration_name,
                "match_kind": match_kind,
            }
        )
    return rows


def _formal_source_module_name(
    path: str,
    imports: Sequence[str],
    *,
    module_root: str = "",
) -> str:
    normalized = path.replace("\\", "/").strip("/")
    if normalized.endswith(".lean"):
        normalized = normalized[:-5]
    module = normalized.replace("/", ".")
    import_roots = {
        value.split(".", 1)[0]
        for value in imports
        if "." in value and value.split(".", 1)[0]
    }
    root = str(module_root or "").strip().split(".", 1)[0]
    if not root and len(import_roots) == 1:
        root = next(iter(import_roots))
    if root:
        if module != root and not module.startswith(root + "."):
            module = root + "." + module
    return module


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
