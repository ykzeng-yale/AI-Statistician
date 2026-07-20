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


def test_generate_validated_json_packet_includes_subsystem_repair_context() -> None:
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
        user_prompt="Produce a packet.",
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
        else ["missing subsystem-specific field"],
        validation_label="test packet",
        max_repair_attempts=1,
        repair_context_builder=lambda **kwargs: {
            "context_kind": "subsystem_repair_context",
            "errors_seen": kwargs["errors"],
            "invalid_packet_seen": kwargs["invalid_packet"],
            "required_field": "semantic_anchor",
            "repair_prompt_priority_instructions": [
                "Copy subsystem seed into candidate field."
            ],
        },
    )

    assert packet["ok"] is True
    repair_payload = json.loads(backend.requests[1].user_prompt.split("\n\n", 1)[1])
    assert repair_payload["subsystem_repair_context"] == {
        "context_kind": "subsystem_repair_context",
        "errors_seen": ["missing subsystem-specific field"],
        "invalid_packet_seen": {"ok": False},
        "required_field": "semantic_anchor",
        "repair_prompt_priority_instructions": [
            "Copy subsystem seed into candidate field."
        ],
    }
    assert (
        "Copy subsystem seed into candidate field."
        in repair_payload["repair_instructions"]
    )


def test_semantic_patch_repair_preserves_unaffected_large_payload() -> None:
    large_candidate = "candidate:" + ("x" * 9000)

    class PatchBackend:
        provider_name = "test"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                response = {
                    "formal_targets": [
                        {
                            "id": "FT1",
                            "provenance": {"source_goal_id": ""},
                        }
                    ],
                    "large_candidate": large_candidate,
                }
            else:
                repair_payload = json.loads(
                    request.user_prompt.split("\n\n", 1)[1]
                )
                response = {
                    "base_payload_fingerprint": repair_payload[
                        "base_payload_fingerprint"
                    ],
                    "updates": [
                        {
                            "path": [
                                "base_payload_excerpt",
                                "top_level_outline",
                                "formal_targets",
                                0,
                                "provenance",
                                "source_goal_id",
                            ],
                            "replacement_json": json.dumps("THM1"),
                        }
                    ],
                }
            return GeneratorResponse(
                text=json.dumps(response),
                provider=self.provider_name,
                model=request.model,
            )

    backend = PatchBackend()
    packet = generate_validated_json_packet(
        provider=backend,
        request=GeneratorRequest(
            system_prompt="Return JSON.",
            user_prompt="Produce a large typed packet.",
            model="test-model",
            max_tokens=6000,
            schema={"type": "object"},
        ),
        extract_payload=lambda text: extract_json_object(
            text,
            label="large typed packet",
        ),
        build_packet=lambda payload, response, raw_text: dict(payload),
        validate_packet=lambda candidate: (
            []
            if candidate["formal_targets"][0]["provenance"][
                "source_goal_id"
            ]
            else ["formal target FT1 must preserve source_goal_id"]
        ),
        validation_label="large typed packet",
        max_repair_attempts=1,
        semantic_patch_repair=True,
    )

    assert len(backend.requests) == 2
    assert backend.requests[1].metadata["json_repair_mode"] == (
        "typed_semantic_patch"
    )
    assert backend.requests[1].max_tokens == 3000
    assert backend.requests[1].schema is not None
    assert set(backend.requests[1].schema["required"]) == {
        "base_payload_fingerprint",
        "updates",
    }
    repair_payload = json.loads(
        backend.requests[1].user_prompt.split("\n\n", 1)[1]
    )
    assert repair_payload["base_payload_excerpt"]["formal_targets"][0][
        "id"
    ] == "FT1"
    assert "top_level_outline" not in repair_payload["base_payload_excerpt"]
    assert repair_payload["base_payload_excerpt_metadata"]["truncated"] is True
    assert (
        repair_payload["base_payload_excerpt_metadata"][
            "excerpt_is_payload_root"
        ]
        is True
    )
    assert any(
        "relative to the base payload root" in instruction
        and "first component must be an actual top-level packet field" in instruction
        for instruction in repair_payload["repair_instructions"]
    )
    assert large_candidate not in backend.requests[1].user_prompt
    assert packet["large_candidate"] == large_candidate
    assert packet["formal_targets"][0]["provenance"]["source_goal_id"] == (
        "THM1"
    )
    assert packet["llm_json_repair_history"][0]["repair_mode"] == (
        "full_packet_generation"
    )
    patch_history = packet["llm_json_repair_history"][1]
    assert patch_history["repair_mode"] == "typed_semantic_patch"
    assert patch_history["patched_paths"] == [
        ["formal_targets", 0, "provenance", "source_goal_id"]
    ]
    assert patch_history["patch_path_normalizations"] == [
        {
            "update_index": 0,
            "stripped_prompt_wrapper_prefixes": [
                "base_payload_excerpt",
                "top_level_outline",
            ],
            "normalized_path": [
                "formal_targets",
                0,
                "provenance",
                "source_goal_id",
            ],
        }
    ]
    assert patch_history["base_payload_fingerprint"]
    assert patch_history["patched_payload_fingerprint"]


def test_semantic_patch_does_not_strip_a_real_wrapper_named_payload_field() -> None:
    class WrapperFieldBackend:
        provider_name = "test"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                response = {
                    "base_payload_excerpt": {"status": "invalid"},
                }
            else:
                repair_payload = json.loads(
                    request.user_prompt.split("\n\n", 1)[1]
                )
                response = {
                    "base_payload_fingerprint": repair_payload[
                        "base_payload_fingerprint"
                    ],
                    "updates": [
                        {
                            "path": ["base_payload_excerpt", "status"],
                            "replacement_json": json.dumps("valid"),
                        }
                    ],
                }
            return GeneratorResponse(
                text=json.dumps(response),
                provider=self.provider_name,
                model=request.model,
            )

    packet = generate_validated_json_packet(
        provider=WrapperFieldBackend(),
        request=GeneratorRequest(
            system_prompt="Return JSON.",
            user_prompt="Produce a wrapper-named packet.",
            model="test-model",
            max_tokens=1000,
            schema={"type": "object"},
        ),
        extract_payload=lambda text: extract_json_object(
            text,
            label="wrapper-named packet",
        ),
        build_packet=lambda payload, response, raw_text: dict(payload),
        validate_packet=lambda candidate: (
            []
            if candidate["base_payload_excerpt"]["status"] == "valid"
            else ["status must be valid"]
        ),
        validation_label="wrapper-named packet",
        max_repair_attempts=1,
        semantic_patch_repair=True,
    )

    assert packet["base_payload_excerpt"]["status"] == "valid"
    history = packet["llm_json_repair_history"][1]
    assert history["patched_paths"] == [["base_payload_excerpt", "status"]]
    assert history["patch_path_normalizations"] == []


def test_semantic_patch_defers_broad_defects_then_repairs_residual() -> None:
    class AdaptiveRepairBackend:
        provider_name = "test"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                response = {"generation": 0, "status": "broadly_invalid"}
            elif len(self.requests) == 2:
                response = {"generation": 1, "status": "one_residual"}
            else:
                repair_payload = json.loads(
                    request.user_prompt.split("\n\n", 1)[1]
                )
                response = {
                    "base_payload_fingerprint": repair_payload[
                        "base_payload_fingerprint"
                    ],
                    "updates": [
                        {
                            "path": ["status"],
                            "replacement_json": json.dumps("valid"),
                        }
                    ],
                }
            return GeneratorResponse(
                text=json.dumps(response),
                provider=self.provider_name,
                model=request.model,
            )

    def validate(candidate: dict[str, object]) -> list[str]:
        if candidate.get("generation") == 0:
            return [f"independent broad defect {index}" for index in range(9)]
        if candidate.get("status") != "valid":
            return ["one residual semantic defect"]
        return []

    backend = AdaptiveRepairBackend()
    packet = generate_validated_json_packet(
        provider=backend,
        request=GeneratorRequest(
            system_prompt="Return JSON.",
            user_prompt="Produce a typed packet.",
            model="test-haiku",
            max_tokens=5000,
            schema={"type": "object"},
        ),
        extract_payload=lambda text: extract_json_object(
            text,
            label="adaptive typed packet",
        ),
        build_packet=lambda payload, response, raw_text: dict(payload),
        validate_packet=validate,
        validation_label="adaptive typed packet",
        max_repair_attempts=2,
        semantic_patch_repair=True,
    )

    assert [
        request.metadata["json_repair_mode"] for request in backend.requests
    ] == [
        "full_packet_generation",
        "full_packet_regeneration",
        "typed_semantic_patch",
    ]
    assert backend.requests[2].max_tokens == 3000
    assert packet["generation"] == 1
    assert packet["status"] == "valid"
    assert packet["llm_json_repair_attempts"] == 2


def test_generate_validated_json_packet_escalates_truncated_repair_budget() -> None:
    class TruncatingThenValidBackend:
        provider_name = "test"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                return GeneratorResponse(
                    text='{"ok": true, "items": ["unfinished"',
                    provider=self.provider_name,
                    model=request.model,
                    metadata={
                        "provider_stop_reason": "max_tokens",
                        "provider_usage": {"output_tokens": request.max_tokens},
                    },
                )
            return GeneratorResponse(
                text='{"ok": true}',
                provider=self.provider_name,
                model=request.model,
                metadata={"provider_stop_reason": "end_turn"},
            )

    backend = TruncatingThenValidBackend()
    request = GeneratorRequest(
        system_prompt="Return JSON.",
        user_prompt="Produce a packet with required semantic anchors." + ("x" * 9000),
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
        else ["missing ok"],
        validation_label="test packet",
        max_repair_attempts=1,
    )

    assert packet["ok"] is True
    assert len(backend.requests) == 2
    assert backend.requests[1].max_tokens > backend.requests[0].max_tokens
    assert backend.requests[1].metadata[
        "json_repair_previous_attempt_truncated"
    ] is True
    repair_payload = json.loads(backend.requests[1].user_prompt.split("\n\n", 1)[1])
    assert repair_payload["truncation_detected"] is True
    assert "provider hit the max token/output limit" in " ".join(
        repair_payload["repair_instructions"]
    )
    assert repair_payload["original_request"]["truncated"] is True
    assert repair_payload["original_request"]["omitted_chars"] > 0
    assert packet["llm_json_repair_history"][0]["request_max_tokens"] == 128
    assert packet["llm_json_repair_history"][1]["request_max_tokens"] > 128


def test_generate_validated_json_packet_keeps_escalated_budget_after_truncation_mode() -> None:
    class TruncatingThenInvalidThenValidBackend:
        provider_name = "test"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                return GeneratorResponse(
                    text='{"ok": true, "items": ["unfinished"',
                    provider=self.provider_name,
                    model=request.model,
                    metadata={
                        "provider_stop_reason": "max_tokens",
                        "provider_usage": {"output_tokens": request.max_tokens},
                    },
                )
            if len(self.requests) == 2:
                return GeneratorResponse(
                    text='{"ok": false}',
                    provider=self.provider_name,
                    model=request.model,
                    metadata={"provider_stop_reason": "end_turn"},
                )
            return GeneratorResponse(
                text='{"ok": true}',
                provider=self.provider_name,
                model=request.model,
                metadata={"provider_stop_reason": "end_turn"},
            )

    backend = TruncatingThenInvalidThenValidBackend()
    request = GeneratorRequest(
        system_prompt="Return JSON.",
        user_prompt="Produce a packet with required semantic anchors." + ("x" * 9000),
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
        else ["missing ok"],
        validation_label="test packet",
        max_repair_attempts=2,
    )

    assert packet["ok"] is True
    assert [request.max_tokens for request in backend.requests] == [128, 1152, 1152]
    assert backend.requests[2].metadata["json_repair_truncation_repair_mode"] is True
    third_repair_payload = json.loads(
        backend.requests[2].user_prompt.split("\n\n", 1)[1]
    )
    assert third_repair_payload["truncation_detected"] is True
