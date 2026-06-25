from __future__ import annotations

import json

import pytest

from ai_statistician.llm_json_repair import (
    _format_generation_error,
    _repair_prompt,
    extract_json_object,
    generate_validated_json_packet,
)
from ai_statistician.model_backend import (
    GeneratorRequest,
    GeneratorResponse,
)


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


def test_format_generation_error_includes_bounded_json_error_excerpt() -> None:
    bad_response = '{"ok": true, "items": ["a", "b" "c"], "tail": "' + ("x" * 1000) + '"}'
    with pytest.raises(json.JSONDecodeError) as caught:
        json.loads(bad_response)

    message = _format_generation_error(caught.value, bad_response)

    assert "JSONDecodeError" in message
    assert "response_excerpt_around_error=" in message
    assert '"b" "c"' in message
    assert "x" * 500 not in message


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
    assert (
        "Rewrite the full JSON object from scratch; do not continue or patch the invalid response."
        in payload["repair_instructions"]
    )
    assert (
        "Use exactly one item for required arrays unless the original contract explicitly requires more."
        in payload["repair_instructions"]
    )
    assert (
        "Keep string fields under 240 characters and avoid multiline derivation essays."
        in payload["repair_instructions"]
    )


def test_generate_validated_json_packet_feeds_validation_errors_into_repair_prompt() -> None:
    class SequencedBackend:
        provider_name = "test"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []
            self.responses = ['{"ok": false}', '{"ok": true}']

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            return GeneratorResponse(
                text=self.responses.pop(0),
                provider=self.provider_name,
                model=request.model,
            )

    backend = SequencedBackend()
    request = GeneratorRequest(
        system_prompt="Return JSON.",
        user_prompt="Produce a packet with required semantic anchors.",
        model="test-model",
        max_tokens=128,
    )

    packet = generate_validated_json_packet(
        provider=backend,
        request=request,
        extract_payload=lambda text: extract_json_object(text, label="test packet"),
        build_packet=lambda payload, response, raw_text: dict(payload),
        validate_packet=lambda candidate: []
        if candidate.get("ok") is True
        else ["missing required semantic anchor references: hRank"],
        validation_label="test packet",
        max_repair_attempts=1,
    )

    assert packet["ok"] is True
    assert packet["llm_json_repair_attempts"] == 1
    assert len(backend.requests) == 2
    repair_prompt = backend.requests[1].user_prompt
    assert "local_validation_errors" in repair_prompt
    assert "missing required semantic anchor references: hRank" in repair_prompt
    assert '"invalid_response_excerpt": "{\\"ok\\": false}"' in repair_prompt
