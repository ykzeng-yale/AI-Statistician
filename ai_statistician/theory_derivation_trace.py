from __future__ import annotations

from typing import Any, Mapping


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


def compact_theory_derivation_trace(
    theory_packet: Mapping[str, Any],
    *,
    max_rows: int = 5,
    text_limit: int = 360,
) -> dict[str, Any]:
    """Return a bounded derivation trace for downstream LLM workers.

    The trace is proposal context only. It helps coding and proof agents align
    generated artifacts to assumptions, equations, and theorem targets without
    upgrading any LLM derivation into execution or proof evidence.
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


def _compact_rows(
    value: Any,
    *,
    keys: tuple[str, ...],
    limit: int,
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
        if len(rows) >= limit:
            break
    return rows


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
