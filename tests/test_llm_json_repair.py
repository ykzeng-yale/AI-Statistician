from __future__ import annotations

import json

import pytest

from ai_statistician.llm_json_repair import (
    _repair_prompt,
    extract_json_object,
    generate_validated_json_packet,
)
from ai_statistician.model_backend import GeneratorRequest, GeneratorResponse


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


def test_generate_validated_json_packet_escalates_haiku_repair_to_sonnet() -> None:
    class FakeAnthropicBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            ok = len(self.requests) > 1
            return GeneratorResponse(
                text=json.dumps({"ok": ok}),
                provider="anthropic",
                model=request.model,
                metadata=dict(request.metadata),
            )

    backend = FakeAnthropicBackend()
    request = GeneratorRequest(
        system_prompt="return json",
        user_prompt="make packet",
        model="claude-haiku-4-5-20251001",
        schema={"type": "object"},
        metadata={
            "provider_name": "anthropic",
            "model_tier": "haiku",
            "resolved_model": "claude-haiku-4-5-20251001",
        },
    )

    packet = generate_validated_json_packet(
        provider=backend,
        request=request,
        extract_payload=extract_json_object,
        build_packet=lambda payload, response, _raw_text: {
            "ok": payload.get("ok"),
            "model": response.model,
            "model_tier": response.metadata.get("effective_model_tier"),
        },
        validate_packet=lambda packet: [] if packet.get("ok") else ["not ok"],
        validation_label="test packet",
        max_repair_attempts=1,
    )

    assert [item.model for item in backend.requests] == [
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-6",
    ]
    assert packet["model"] == "claude-sonnet-4-6"
    assert packet["model_tier"] == "sonnet"
    assert packet["llm_json_repair_attempts"] == 1
    assert packet["llm_json_repair_history"][1]["model_tier_escalated"] is True
    expected_reason = (
        "auto escalated Anthropic JSON repair from Claude Haiku to Claude "
        "Sonnet after local validation failed"
    )
    assert (
        packet["llm_json_repair_history"][1]["model_tier_escalation_reason"]
        == expected_reason
    )


def test_generate_validated_json_packet_keeps_explicit_custom_model_on_repair() -> None:
    class FakeAnthropicBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            ok = len(self.requests) > 1
            return GeneratorResponse(
                text=json.dumps({"ok": ok}),
                provider="anthropic",
                model=request.model,
                metadata=dict(request.metadata),
            )

    backend = FakeAnthropicBackend()
    request = GeneratorRequest(
        system_prompt="return json",
        user_prompt="make packet",
        model="claude-haiku-custom",
        schema={"type": "object"},
        metadata={
            "provider_name": "anthropic",
            "model_tier": "haiku",
            "resolved_model": "claude-haiku-custom",
            "explicit_model_configured": True,
        },
    )

    packet = generate_validated_json_packet(
        provider=backend,
        request=request,
        extract_payload=extract_json_object,
        build_packet=lambda payload, response, _raw_text: {
            "ok": payload.get("ok"),
            "model": response.model,
            "model_tier": response.metadata.get("effective_model_tier"),
        },
        validate_packet=lambda packet: [] if packet.get("ok") else ["not ok"],
        validation_label="test packet",
        max_repair_attempts=1,
    )

    assert [item.model for item in backend.requests] == [
        "claude-haiku-custom",
        "claude-haiku-custom",
    ]
    assert packet["model"] == "claude-haiku-custom"
    assert packet["model_tier"] == "haiku"
    assert packet["llm_json_repair_attempts"] == 1
    assert packet["llm_json_repair_history"][1]["model_tier_escalated"] is False
