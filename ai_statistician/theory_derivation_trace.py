from __future__ import annotations

import re
from typing import Any, Mapping

from .theory_workspace import (
    THEORY_WORKSPACE_CONTENT_AUTHORITY,
    THEORY_WORKSPACE_HANDOFF_ROLE,
    load_theory_workspace_document_rows,
)


DERIVATION_STEP_KEYS = (
    "id",
    "claim",
    "equation_or_argument",
    "depends_on",
    "formal_goal",
    "risk",
)
EQUATION_CHAIN_KEYS = (
    "step_id",
    "lhs",
    "relation",
    "rhs",
    "justification",
    "depends_on",
)
ASSUMPTION_LEDGER_KEYS = (
    "assumption",
    "role",
    "used_in",
    "risk_if_dropped",
)
CLAIM_INDEX_KEYS = (
    "id",
    "kind",
    "document_path",
    "anchor",
    "depends_on",
    "status",
)
SANITY_CHECK_INDEX_KEYS = (
    "id",
    "claim_ref",
    "document_path",
    "anchor",
    "status",
)

THEORY_TRACE_CONSUMPTION_BOUNDARY = (
    "Theory trace consumption records proposal-context provenance only. It "
    "does not count as code execution, simulation evidence, or Lean/kernel "
    "proof evidence."
)
THEORY_TRACE_ALIGNMENT_BOUNDARY = (
    "Theory trace alignment records LLM proposal-to-trace provenance only. It "
    "does not count as code execution, simulation evidence, or Lean/kernel "
    "proof evidence."
)
DOCUMENT_AUTHORITATIVE_THEORY_CONTEXT_BOUNDARY = (
    "Exact model-authored theory documents are the mathematical content "
    "authority for this handoff. The structured trace and ABI carry identity "
    "only. Neither the documents nor the index count as code execution, "
    "simulation evidence, or Lean/kernel proof evidence."
)


def document_authoritative_theory_context(
    theory_packet: Mapping[str, Any],
    *,
    max_rows: int = 5,
    text_limit: int = 360,
) -> dict[str, Any]:
    """Return one exact, reusable theory context for model-owned workspaces."""

    if not isinstance(theory_packet, Mapping):
        return {}
    documents = load_theory_workspace_document_rows(theory_packet)
    manifest = theory_packet.get("theory_workspace_manifest", {})
    manifest = manifest if isinstance(manifest, Mapping) else {}
    content_authority = str(
        theory_packet.get("theory_content_authority", "")
        or manifest.get("content_authority", "")
        or ""
    )
    handoff_role = str(
        theory_packet.get("structured_handoff_role", "")
        or manifest.get("structured_handoff_role", "")
        or ""
    )
    if documents and (
        content_authority != THEORY_WORKSPACE_CONTENT_AUTHORITY
        or handoff_role != THEORY_WORKSPACE_HANDOFF_ROLE
    ):
        raise ValueError("theory document authority metadata is invalid")
    return {
        "source_theory_packet_id": str(theory_packet.get("packet_id", "") or ""),
        "document_authoritative": bool(documents),
        "theory_content_authority": (
            content_authority if documents else "legacy_structured_packet"
        ),
        "structured_handoff_role": (
            handoff_role if documents else "legacy_structured_packet"
        ),
        "theory_derivation_trace": compact_theory_derivation_trace(
            theory_packet,
            max_rows=max_rows,
            text_limit=text_limit,
        ),
        "authoritative_theory_documents": documents,
        "boundary": DOCUMENT_AUTHORITATIVE_THEORY_CONTEXT_BOUNDARY,
    }


def compact_theory_derivation_trace(
    theory_packet: Mapping[str, Any],
    *,
    max_rows: int = 5,
    text_limit: int = 360,
) -> dict[str, Any]:
    """Return compact theory provenance for downstream LLM workers.

    Rich legacy rows remain bounded, while the document-native claim index is
    complete so a row limit cannot silently sever claim identities or dependency
    edges. The trace is proposal context only and does not upgrade an LLM
    derivation into execution or proof evidence.
    """

    if not isinstance(theory_packet, Mapping):
        return {}
    raw_derivation = theory_packet.get("theory_derivation_packet", {})
    if not isinstance(raw_derivation, Mapping):
        return {}
    compact = {
        "derivation_summary": _compact_value(
            raw_derivation.get("derivation_summary", ""),
            text_limit=text_limit,
        ),
        "derivation_steps": _compact_rows(
            raw_derivation.get("derivation_steps", []),
            keys=DERIVATION_STEP_KEYS,
            limit=max_rows,
            text_limit=text_limit,
        ),
        "equation_chain": _compact_rows(
            raw_derivation.get("equation_chain", []),
            keys=EQUATION_CHAIN_KEYS,
            limit=max_rows,
            text_limit=text_limit,
        ),
        "assumption_ledger": _compact_rows(
            raw_derivation.get("assumption_ledger", []),
            keys=ASSUMPTION_LEDGER_KEYS,
            limit=max_rows,
            text_limit=text_limit,
        ),
        "claim_index": _compact_claim_index_rows(
            raw_derivation.get("claim_index", []),
            text_limit=text_limit,
        ),
        "sanity_check_index": _compact_rows(
            raw_derivation.get("sanity_check_index", []),
            keys=SANITY_CHECK_INDEX_KEYS,
            limit=max_rows,
            text_limit=text_limit,
        ),
        "formalization_handoff": _compact_value(
            raw_derivation.get("formalization_handoff", {}),
            text_limit=text_limit,
        ),
    }
    return {
        key: value
        for key, value in compact.items()
        if value not in (None, "", [], {})
    }


def theory_trace_claim_ids(theory_packet: Mapping[str, Any]) -> list[str]:
    """Return complete, exact document-claim identities in source order."""

    trace = compact_theory_derivation_trace(theory_packet)
    return _exact_unique_strings(
        row.get("id", "")
        for row in trace.get("claim_index", [])
        if isinstance(row, Mapping)
    )


def theory_trace_alignment_output_contract(
    theory_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the smallest model-facing provenance envelope for this packet."""

    if theory_trace_claim_ids(theory_packet):
        return {
            "referenced_claim_ids": [
                "one or more exact ids selected from theory_derivation_trace.claim_index"
            ],
            "rationale": "short reason these claims are directly consumed",
        }
    return {
        "referenced_derivation_steps": ["derivation step ids from theory trace"],
        "referenced_equation_steps": ["equation step_ids from theory trace"],
        "referenced_assumptions": ["assumption names from theory trace"],
        "referenced_formalization_targets": [
            "formalization targets from theory trace"
        ],
        "rationale": "short string",
    }


def theory_trace_alignment_json_schema(
    theory_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind model-authored provenance to exact claim IDs when available."""

    claim_ids = theory_trace_claim_ids(theory_packet)
    if claim_ids:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["referenced_claim_ids", "rationale"],
            "properties": {
                "referenced_claim_ids": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"type": "string", "enum": claim_ids},
                },
                "rationale": {"type": "string"},
            },
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "referenced_derivation_steps",
            "referenced_equation_steps",
            "referenced_assumptions",
            "referenced_formalization_targets",
            "rationale",
        ],
        "properties": {
            "referenced_derivation_steps": _string_array_json_schema(),
            "referenced_equation_steps": _string_array_json_schema(),
            "referenced_assumptions": _string_array_json_schema(),
            "referenced_formalization_targets": _string_array_json_schema(),
            "rationale": {"type": "string"},
        },
    }


def theory_trace_alignment_prompt_instruction(
    theory_packet: Mapping[str, Any],
) -> str:
    if theory_trace_claim_ids(theory_packet):
        return (
            "Populate theory_trace_alignment.referenced_claim_ids with the exact "
            "claim_index IDs directly implemented, tested, or formalized by this "
            "artifact. Select claims rather than copying prose; AgentRuntime resolves "
            "their declared dependency closure for independent review. "
        )
    return (
        "Populate theory_trace_alignment with exact referenced_derivation_steps, "
        "referenced_equation_steps, referenced_assumptions, and "
        "referenced_formalization_targets from the supplied legacy trace anchors. "
    )


def theory_trace_consumption_contract(
    theory_packet: Mapping[str, Any],
    *,
    consumer_subsystem: str,
    max_rows: int = 5,
    text_limit: int = 360,
) -> dict[str, Any]:
    """Describe which compact theory trace a downstream worker received.

    This is provenance metadata for runtime auditability. It records that the
    worker prompt/artifact was grounded in an upstream TheoryDeveloper packet,
    while preserving that the trace remains LLM proposal context.
    """

    trace = compact_theory_derivation_trace(
        theory_packet,
        max_rows=max_rows,
        text_limit=text_limit,
    )
    return {
        "artifact_kind": "TheoryTraceConsumptionContract",
        "source_theory_packet_id": str(theory_packet.get("packet_id", "") or "")
        if isinstance(theory_packet, Mapping)
        else "",
        "consumer_subsystem": consumer_subsystem,
        "theory_derivation_trace_supplied": bool(trace),
        "n_derivation_steps_supplied": _safe_list_len(trace.get("derivation_steps", [])),
        "n_equation_chain_steps_supplied": _safe_list_len(trace.get("equation_chain", [])),
        "n_assumption_ledger_rows_supplied": _safe_list_len(
            trace.get("assumption_ledger", [])
        ),
        "n_claim_index_rows_supplied": _safe_list_len(
            trace.get("claim_index", [])
        ),
        "n_claim_dependency_edges_supplied": sum(
            _safe_list_len(row.get("depends_on", []))
            for row in trace.get("claim_index", [])
            if isinstance(row, Mapping)
        ),
        "n_sanity_check_index_rows_supplied": _safe_list_len(
            trace.get("sanity_check_index", [])
        ),
        "n_authoritative_theory_documents_supplied": _safe_list_len(
            (
                theory_packet.get("theory_workspace_manifest", {}).get(
                    "documents", []
                )
                if isinstance(
                    theory_packet.get("theory_workspace_manifest", {}),
                    Mapping,
                )
                else []
            )
            if isinstance(theory_packet, Mapping)
            else []
        ),
        "has_formalization_handoff": bool(trace.get("formalization_handoff")),
        "boundary": THEORY_TRACE_CONSUMPTION_BOUNDARY,
    }


def theory_trace_anchor_summary(
    theory_packet: Mapping[str, Any],
    *,
    max_rows: int = 5,
    text_limit: int = 360,
) -> dict[str, Any]:
    trace = compact_theory_derivation_trace(
        theory_packet,
        max_rows=max_rows,
        text_limit=text_limit,
    )
    formalization_handoff = trace.get("formalization_handoff", {})
    formalization_targets: list[str] = []
    if isinstance(formalization_handoff, Mapping):
        for key in (
            "source_theorem_target",
            "candidate_lean_targets",
            "required_definitions",
            "lemma_dependencies",
            "semantic_alignment_constraints",
        ):
            formalization_targets.extend(_string_values(formalization_handoff.get(key)))
    for theorem_card in theory_packet.get("theorem_cards", []) or []:
        if not isinstance(theorem_card, Mapping):
            continue
        for key in (
            "id",
            "informal_statement",
            "conclusion",
            "proof_strategy",
            "semantic_risks",
        ):
            formalization_targets.extend(_string_values(theorem_card.get(key)))
    for request in theory_packet.get("formalization_requests", []) or []:
        if not isinstance(request, Mapping):
            continue
        for key in (
            "id",
            "target_theorem_card",
            "lean_statement_sketch",
            "semantic_alignment_constraints",
        ):
            formalization_targets.extend(_string_values(request.get(key)))
        formalization_targets.extend(
            _lean_declaration_names(request.get("lean_statement_sketch", ""))
        )
    return {
        "claim_ids": _exact_unique_strings(
            row.get("id", "")
            for row in trace.get("claim_index", [])
            if isinstance(row, Mapping)
        ),
        "derivation_step_ids": _unique_strings(
            [
                row.get("id", "")
                for row in trace.get("derivation_steps", [])
                if isinstance(row, Mapping)
            ]
            + [
                row.get("id", "")
                for row in trace.get("claim_index", [])
                if isinstance(row, Mapping)
            ]
        ),
        "equation_step_ids": _unique_strings(
            row.get("step_id", "")
            for row in trace.get("equation_chain", [])
            if isinstance(row, Mapping)
        ),
        "assumption_names": _unique_strings(
            [
                row.get("assumption", "")
                for row in trace.get("assumption_ledger", [])
                if isinstance(row, Mapping)
            ]
            + [
                row.get("id", "")
                for row in trace.get("claim_index", [])
                if isinstance(row, Mapping)
                and str(row.get("kind", "") or "").strip().lower()
                == "assumption"
            ]
        ),
        "formalization_targets": _unique_strings(formalization_targets),
        "n_claim_dependency_edges": sum(
            _safe_list_len(row.get("depends_on", []))
            for row in trace.get("claim_index", [])
            if isinstance(row, Mapping)
        ),
    }


def theory_trace_alignment_contract(
    theory_packet: Mapping[str, Any],
    alignment: Mapping[str, Any] | None,
    *,
    consumer_subsystem: str,
    max_rows: int = 5,
    text_limit: int = 360,
) -> dict[str, Any]:
    anchors = theory_trace_anchor_summary(
        theory_packet,
        max_rows=max_rows,
        text_limit=text_limit,
    )
    raw_alignment = alignment if isinstance(alignment, Mapping) else {}
    referenced_claim_ids = _exact_unique_strings(
        raw_alignment.get("referenced_claim_ids", [])
    )
    claim_id_alignment = "referenced_claim_ids" in raw_alignment
    supported_claim_ids, unsupported_claim_ids = _split_exact_supported_refs(
        referenced_claim_ids,
        anchors.get("claim_ids", []),
    )
    referenced_derivation_steps = _unique_strings(
        raw_alignment.get("referenced_derivation_steps", [])
    )
    referenced_equation_steps = _unique_strings(
        raw_alignment.get("referenced_equation_steps", [])
    )
    referenced_assumptions = _unique_strings(
        raw_alignment.get("referenced_assumptions", [])
    )
    referenced_formalization_targets = _unique_strings(
        raw_alignment.get("referenced_formalization_targets", [])
    )
    supported_derivation_steps, unsupported_derivation_steps = _split_supported_refs(
        referenced_derivation_steps,
        anchors.get("derivation_step_ids", []),
    )
    supported_equation_steps, unsupported_equation_steps = _split_supported_refs(
        referenced_equation_steps,
        anchors.get("equation_step_ids", []),
    )
    supported_assumptions, unsupported_assumptions = _split_supported_refs(
        referenced_assumptions,
        anchors.get("assumption_names", []),
    )
    supported_formalization_targets, unsupported_formalization_targets = (
        _split_supported_refs(
            referenced_formalization_targets,
            anchors.get("formalization_targets", []),
        )
    )
    if claim_id_alignment:
        n_supported_anchor_references = len(supported_claim_ids)
        n_unsupported_anchor_references = len(unsupported_claim_ids)
    else:
        n_supported_anchor_references = (
            len(supported_derivation_steps)
            + len(supported_equation_steps)
            + len(supported_assumptions)
            + len(supported_formalization_targets)
        )
        n_unsupported_anchor_references = (
            len(unsupported_derivation_steps)
            + len(unsupported_equation_steps)
            + len(unsupported_assumptions)
            + len(unsupported_formalization_targets)
        )
    llm_alignment_claimed = any(
        (
            referenced_claim_ids,
            referenced_derivation_steps,
            referenced_equation_steps,
            referenced_assumptions,
            referenced_formalization_targets,
            str(raw_alignment.get("rationale", "") or "").strip(),
        )
    )
    structured_alignment_observed = (
        bool(
            llm_alignment_claimed
            and supported_claim_ids
            and n_unsupported_anchor_references == 0
        )
        if claim_id_alignment
        else bool(
            llm_alignment_claimed
            and supported_assumptions
            and (
                supported_derivation_steps
                or supported_equation_steps
                or supported_formalization_targets
            )
            and n_unsupported_anchor_references == 0
        )
    )
    claim_dependency_closure = _claim_dependency_closure(
        theory_packet,
        supported_claim_ids,
    )
    return {
        "artifact_kind": "TheoryTraceAlignmentContract",
        "source_theory_packet_id": str(theory_packet.get("packet_id", "") or "")
        if isinstance(theory_packet, Mapping)
        else "",
        "consumer_subsystem": consumer_subsystem,
        "alignment_mode": (
            "exact_claim_id_v1" if claim_id_alignment else "legacy_anchor_v1"
        ),
        "llm_alignment_claimed": llm_alignment_claimed,
        "structured_alignment_observed": structured_alignment_observed,
        "referenced_claim_ids": referenced_claim_ids,
        "supported_claim_ids": supported_claim_ids,
        "unsupported_claim_ids": unsupported_claim_ids,
        "claim_dependency_closure": claim_dependency_closure,
        "referenced_derivation_steps": referenced_derivation_steps,
        "referenced_equation_steps": referenced_equation_steps,
        "referenced_assumptions": referenced_assumptions,
        "referenced_formalization_targets": referenced_formalization_targets,
        "supported_derivation_steps": supported_derivation_steps,
        "supported_equation_steps": supported_equation_steps,
        "supported_assumptions": supported_assumptions,
        "supported_formalization_targets": supported_formalization_targets,
        "unsupported_derivation_steps": unsupported_derivation_steps,
        "unsupported_equation_steps": unsupported_equation_steps,
        "unsupported_assumptions": unsupported_assumptions,
        "unsupported_formalization_targets": unsupported_formalization_targets,
        "n_supported_anchor_references": n_supported_anchor_references,
        "n_unsupported_anchor_references": n_unsupported_anchor_references,
        "source_anchor_counts": {
            "claim_ids": _safe_list_len(anchors.get("claim_ids")),
            "claim_dependency_edges": int(
                anchors.get("n_claim_dependency_edges", 0) or 0
            ),
            "derivation_step_ids": _safe_list_len(anchors.get("derivation_step_ids")),
            "equation_step_ids": _safe_list_len(anchors.get("equation_step_ids")),
            "assumption_names": _safe_list_len(anchors.get("assumption_names")),
            "formalization_targets": _safe_list_len(
                anchors.get("formalization_targets")
            ),
        },
        "rationale": _truncate_text(raw_alignment.get("rationale", ""), limit=240),
        "boundary": THEORY_TRACE_ALIGNMENT_BOUNDARY,
    }


def _compact_rows(
    value: Any,
    *,
    keys: tuple[str, ...],
    limit: int | None,
    text_limit: int,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, Any]] = []
    for raw_row in value:
        if not isinstance(raw_row, Mapping):
            continue
        row: dict[str, Any] = {}
        for key in keys:
            if key not in raw_row:
                continue
            compact = _compact_value(raw_row.get(key), text_limit=text_limit)
            if compact not in (None, "", [], {}):
                row[key] = compact
        if row:
            rows.append(row)
        if limit is not None and len(rows) >= limit:
            break
    return rows


def _compact_claim_index_rows(
    value: Any,
    *,
    text_limit: int,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, Any]] = []
    for raw_row in value:
        if not isinstance(raw_row, Mapping):
            continue
        row: dict[str, Any] = {}
        for key in CLAIM_INDEX_KEYS:
            if key not in raw_row:
                continue
            if key == "depends_on":
                compact = _exact_unique_strings(raw_row.get(key, []))
            elif key in {"id", "document_path"}:
                compact = str(raw_row.get(key, "") or "").strip()
            else:
                compact = _compact_value(raw_row.get(key), text_limit=text_limit)
            if compact not in (None, "", [], {}):
                row[key] = compact
        if row:
            rows.append(row)
    return rows


def _safe_list_len(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _unique_strings(values: Any) -> list[str]:
    seen: set[str] = set()
    strings: list[str] = []
    for value in _string_values(values):
        normalized = _normalize_anchor(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        strings.append(value)
    return strings


def _exact_unique_strings(values: Any) -> list[str]:
    seen: set[str] = set()
    strings: list[str] = []
    for value in _string_values(values):
        if not value or value in seen:
            continue
        seen.add(value)
        strings.append(value)
    return strings


def _split_exact_supported_refs(
    refs: list[str],
    anchors: Any,
) -> tuple[list[str], list[str]]:
    allowed = set(_exact_unique_strings(anchors))
    return (
        [ref for ref in refs if ref in allowed],
        [ref for ref in refs if ref not in allowed],
    )


def _claim_dependency_closure(
    theory_packet: Mapping[str, Any],
    root_claim_ids: list[str],
) -> list[str]:
    trace = compact_theory_derivation_trace(theory_packet)
    rows = [
        row
        for row in trace.get("claim_index", [])
        if isinstance(row, Mapping) and str(row.get("id", "") or "")
    ]
    dependencies = {
        str(row.get("id", "")): _exact_unique_strings(row.get("depends_on", []))
        for row in rows
    }
    selected: set[str] = set()
    frontier = list(root_claim_ids)
    while frontier:
        claim_id = frontier.pop()
        if claim_id in selected or claim_id not in dependencies:
            continue
        selected.add(claim_id)
        frontier.extend(dependencies[claim_id])
    return [
        str(row.get("id", ""))
        for row in rows
        if str(row.get("id", "")) in selected
    ]


def _string_array_json_schema() -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}}


def _string_values(values: Any) -> list[str]:
    if isinstance(values, str):
        return [values.strip()] if values.strip() else []
    if isinstance(values, Mapping):
        return [
            str(value).strip()
            for value in values.values()
            if str(value or "").strip()
        ]
    if isinstance(values, (list, tuple, set)):
        return [
            str(value).strip()
            for value in values
            if str(value or "").strip()
        ]
    try:
        iterator = iter(values)
    except TypeError:
        iterator = None
    if iterator is not None:
        return [
            str(value).strip()
            for value in iterator
            if str(value or "").strip()
        ]
    if values in (None, "", [], {}):
        return []
    text = str(values).strip()
    return [text] if text else []


def _split_supported_refs(
    refs: list[str],
    anchors: Any,
) -> tuple[list[str], list[str]]:
    anchor_values = _string_values(anchors)
    anchor_aliases = [
        _anchor_aliases(anchor)
        for anchor in anchor_values
    ]
    supported: list[str] = []
    unsupported: list[str] = []
    for ref in refs:
        if _reference_matches_any_anchor(ref, anchor_values, anchor_aliases):
            supported.append(ref)
        else:
            unsupported.append(ref)
    return supported, unsupported


def _normalize_anchor(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("‑", "-").replace("–", "-").replace("—", "-")
    text = text.replace("'", "")
    text = " ".join(text.split())
    return text


def _anchor_aliases(value: Any) -> set[str]:
    """Return provenance-only aliases for matching LLM anchor references."""

    normalized = _normalize_anchor(value)
    aliases = {normalized} if normalized else set()
    if not normalized:
        return aliases
    prefix = normalized.split(":", 1)[0].strip()
    if prefix and prefix != normalized:
        aliases.add(prefix)
    id_match = _ANCHOR_ID_PATTERN.match(normalized)
    if id_match:
        aliases.add(id_match.group("id"))
    for declaration_name in _lean_declaration_names(value):
        aliases.add(_normalize_anchor(declaration_name))
    return {alias for alias in aliases if alias}


def _reference_matches_any_anchor(
    ref: str,
    anchor_values: list[str],
    anchor_aliases: list[set[str]],
) -> bool:
    ref_aliases = _anchor_aliases(ref)
    if any(ref_aliases & aliases for aliases in anchor_aliases):
        return True
    ref_norm = _normalize_anchor(ref)
    if not ref_norm:
        return False
    for anchor, aliases in zip(anchor_values, anchor_aliases, strict=False):
        if any(
            len(alias) >= 8 and (alias in ref_norm or ref_norm in alias)
            for alias in aliases
        ):
            return True
        if _anchor_token_overlap_supported(ref_norm, _normalize_anchor(anchor)):
            return True
    return False


_ANCHOR_ID_PATTERN = re.compile(
    r"^(?P<id>[a-z]+[0-9]+)\b(?:\s*[:\-.].*)?$"
)


_ANCHOR_TOKEN_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "must",
    "of",
    "or",
    "the",
    "to",
    "when",
    "with",
}


def _anchor_token_overlap_supported(ref_norm: str, anchor_norm: str) -> bool:
    ref_tokens = _anchor_tokens(ref_norm)
    anchor_tokens = _anchor_tokens(anchor_norm)
    if len(ref_tokens) < 3 or len(anchor_tokens) < 3:
        return False
    overlap = ref_tokens & anchor_tokens
    if len(overlap) < 3:
        return False
    return len(overlap) / max(1, min(len(ref_tokens), len(anchor_tokens))) >= 0.6


def _anchor_tokens(value: str) -> set[str]:
    raw_tokens = re.findall(r"[a-z0-9_]+", value.lower().replace("_", " "))
    tokens: set[str] = set()
    for token in raw_tokens:
        if token in _ANCHOR_TOKEN_STOPWORDS:
            continue
        if token.endswith("ing") and len(token) > 5:
            token = token[:-3]
        if token:
            tokens.add(token)
    return tokens


def _lean_declaration_names(value: Any) -> list[str]:
    text = str(value or "")
    if not text.strip():
        return []
    names: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(
        r"\b(?:theorem|lemma|def|abbrev|structure|class|inductive)\s+"
        r"(?P<name>[A-Za-z_][A-Za-z0-9_'.]*)",
        text,
    ):
        name = match.group("name").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _compact_value(value: Any, *, text_limit: int) -> Any:
    if isinstance(value, str):
        return _truncate_text(value, limit=text_limit)
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, list):
        return [
            _compact_value(row, text_limit=text_limit)
            for row in value[:5]
            if row not in (None, "", [], {})
        ]
    if isinstance(value, Mapping):
        compact: dict[str, Any] = {}
        for index, (key, row_value) in enumerate(value.items()):
            if index >= 8:
                break
            compact_value = _compact_value(row_value, text_limit=text_limit)
            if compact_value not in (None, "", [], {}):
                compact[str(key)] = compact_value
        return compact
    return _truncate_text(value, limit=text_limit)


def _truncate_text(value: Any, *, limit: int) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)] + "...[truncated]"
