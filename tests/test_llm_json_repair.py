from __future__ import annotations

import json

import pytest

from ai_statistician.llm_json_repair import extract_json_object


def test_extract_json_object_handles_fenced_json() -> None:
    payload = extract_json_object(
        "```json\n{\"ok\": true, \"items\": [1, 2]}\n```",
        label="test",
    )

    assert payload == {"ok": True, "items": [1, 2]}


def test_extract_json_object_uses_first_balanced_object_not_greedy_tail() -> None:
    text = (
        "Here is the packet:\n"
        "{\"ok\": true, \"note\": \"brace in string { kept }\"}\n"
        "Trailing explanation with another {not json} brace."
    )

    assert extract_json_object(text, label="test") == {
        "ok": True,
        "note": "brace in string { kept }",
    }


def test_extract_json_object_preserves_decode_error_for_almost_json() -> None:
    with pytest.raises(json.JSONDecodeError):
        extract_json_object('{"ok": true "missing_comma": true}', label="test")
