from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .schema import FormalObligation


_PROOF_BANK_PATH = Path(__file__).resolve().parent / "resources" / "proof_bank.json"


def _obligation(row: Mapping[str, Any]) -> FormalObligation:
    return FormalObligation(
        id=str(row["id"]),
        title=str(row["title"]),
        english=str(row["english"]),
        formal_statement=str(row["formal_statement"]),
        proof_body=str(row["proof_body"]),
        tags=tuple(str(value) for value in row.get("tags", [])),
        expected_lemmas=tuple(
            str(value) for value in row.get("expected_lemmas", [])
        ),
        source=str(row.get("source", "Mathlib")),
        depends_on=tuple(str(value) for value in row.get("depends_on", [])),
    )


def _load_obligations() -> dict[str, FormalObligation]:
    payload = json.loads(_PROOF_BANK_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("proof-bank resource must be an array")
    obligations = [_obligation(row) for row in payload if isinstance(row, Mapping)]
    indexed = {row.id: row for row in obligations}
    if len(indexed) != len(payload):
        raise ValueError("proof-bank resource has missing or duplicate obligation IDs")
    return indexed


FORMAL_OBLIGATIONS = _load_obligations()


def all_obligations() -> list[FormalObligation]:
    return list(FORMAL_OBLIGATIONS.values())


def proof_bank_fingerprint() -> str:
    return stable_hash(
        [
            {
                "id": obligation.id,
                "title": obligation.title,
                "english": obligation.english,
                "formal_statement": obligation.formal_statement,
                "proof_body": obligation.proof_body,
                "tags": obligation.tags,
                "expected_lemmas": obligation.expected_lemmas,
                "source": obligation.source,
                "depends_on": obligation.depends_on,
            }
            for obligation in sorted(all_obligations(), key=lambda row: row.id)
        ]
    )


def get_obligation(obligation_id: str) -> FormalObligation:
    try:
        return FORMAL_OBLIGATIONS[obligation_id]
    except KeyError as exc:
        raise KeyError(f"unknown formal obligation: {obligation_id}") from exc


def obligations_by_tags(
    tags: set[str], *, require_all: bool = False
) -> list[FormalObligation]:
    if not tags:
        return all_obligations()
    if require_all:
        return [row for row in all_obligations() if tags.issubset(set(row.tags))]
    return [row for row in all_obligations() if set(row.tags) & tags]
