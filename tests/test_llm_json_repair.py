from __future__ import annotations

import json

import pytest

from ai_statistician.llm_json_repair import _repair_prompt, extract_json_object


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


def test_repair_prompt_compacts_large_original_request() -> None:
    original = "START" + ("x" * 9000) + "required_output_contract"
    prompt = _repair_prompt(
        original_user_prompt=original,
        bad_response='{"ok": true "broken": true}',
        errors=["JSONDecodeError: missing comma"],
        validation_label="test packet",
    )
    payload = json.loads(prompt.split("\n\n", 1)[1])
    original_request = payload["original_request"]

    assert original_request["truncated"] is True
    assert original_request["n_chars"] == len(original)
    assert original_request["head"].startswith("START")
    assert original_request["tail"].endswith("required_output_contract")
    assert "x" * 9000 not in prompt
