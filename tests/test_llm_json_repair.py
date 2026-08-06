from __future__ import annotations

import json

import pytest

from ai_statistician.llm_json_repair import (
    PacketValidationError,
    _apply_typed_semantic_patch,
    _compact_response_metadata,
    _format_generation_error,
    _repair_attempt_max_tokens,
    _repair_prompt,
    _typed_semantic_patch_schema,
    _validation_error_focus_schemas,
    _validation_error_focus_values,
    extract_json_object,
    generate_validated_json_packet,
    typed_semantic_patch_payload_fingerprint,
)
from ai_statistician.model_backend import (
    GeneratorRequest,
    GeneratorResponse,
    PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY,
    PROVIDER_STRUCTURED_OUTPUT_ON_REPAIR_METADATA_KEY,
)


class _SequenceBackend:
    provider_name = "test"

    def __init__(self, responses: list[dict[str, object] | str]) -> None:
        self.responses = list(responses)
        self.requests: list[GeneratorRequest] = []

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        self.requests.append(request)
        response = self.responses.pop(0)
        return GeneratorResponse(
            text=response if isinstance(response, str) else json.dumps(response),
            provider=self.provider_name,
            model=request.model,
        )


def _request(**metadata: object) -> GeneratorRequest:
    return GeneratorRequest(
        system_prompt="Return JSON.",
        user_prompt="Produce one complete status packet.",
        model="test-haiku",
        max_tokens=128,
        schema={
            "type": "object",
            "required": ["status"],
            "properties": {"status": {"type": "string"}},
        },
        metadata=metadata,
    )


def test_extract_json_object_handles_fenced_and_trailing_text() -> None:
    assert extract_json_object(
        "```json\n{\"ok\": true, \"items\": [1, 2]}\n``` trailing",
        label="test",
    ) == {"ok": True, "items": [1, 2]}


def test_extract_json_object_preserves_decode_error() -> None:
    with pytest.raises(json.JSONDecodeError):
        extract_json_object('{"ok": true "missing": true}', label="test")


def test_format_generation_error_includes_bounded_excerpt() -> None:
    bad = '{"items": ["a" "b"], "tail": "' + ("x" * 1000) + '"}'
    with pytest.raises(json.JSONDecodeError) as caught:
        json.loads(bad)
    message = _format_generation_error(caught.value, bad)
    assert "JSONDecodeError" in message
    assert '"a" "b"' in message
    assert "x" * 500 not in message


def test_validation_error_focus_resolves_nested_rows_and_schema() -> None:
    payload = {"packets": [{"blocks": [{"id": "b0"}, {"id": "b1"}]}]}
    block_schema = {
        "type": "object",
        "required": ["id"],
        "properties": {"id": {"type": "string"}},
    }
    schema = {
        "type": "object",
        "properties": {
            "packets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "blocks": {"type": "array", "items": block_schema}
                    },
                },
            }
        },
    }
    errors = ["packets[0] blocks[1] id is invalid"]
    assert _validation_error_focus_values(payload, errors=errors) == [
        {
            "path": ["packets", 0, "blocks", 1],
            "value": {"id": "b1"},
            "value_truncated": False,
        }
    ]
    assert _validation_error_focus_schemas(schema, errors=errors) == [
        {
            "path_pattern": [
                "packets",
                "<array_index>",
                "blocks",
                "<array_index>",
            ],
            "expected_item_schema": block_schema,
        }
    ]


def test_repair_prompt_returns_full_regeneration_context() -> None:
    prior = json.dumps({"status": "invalid", "detail": "y" * 8000})
    prompt = _repair_prompt(
        original_user_prompt="START" + ("x" * 9000) + "END",
        bad_response=prior,
        errors=["status must be valid"],
        validation_label="status packet",
    )
    payload = json.loads(prompt.split("\n\n", 1)[1])
    assert payload["original_request"]["truncated"] is True
    assert payload["invalid_response_excerpt"] == prior
    instructions = " ".join(payload["repair_instructions"])
    assert "Rewrite the full JSON object from scratch" in instructions
    assert "do not emit a patch" in instructions


def test_generate_validated_packet_regenerates_complete_object() -> None:
    backend = _SequenceBackend(
        [{"status": "invalid", "keep": "context"}, {"status": "valid"}]
    )
    packet = generate_validated_json_packet(
        provider=backend,
        request=_request(),
        extract_payload=lambda text: extract_json_object(text, label="status"),
        build_packet=lambda payload, _response, _raw: dict(payload),
        validate_packet=lambda candidate: (
            [] if candidate.get("status") == "valid" else ["status must be valid"]
        ),
        validation_label="status packet",
        max_repair_attempts=1,
    )
    assert packet["status"] == "valid"
    assert [
        request.metadata["json_repair_mode"] for request in backend.requests
    ] == ["full_packet_generation", "full_packet_regeneration"]
    repair = json.loads(backend.requests[1].user_prompt.split("\n\n", 1)[1])
    assert repair["local_validation_errors"] == ["status must be valid"]
    assert '"keep": "context"' in repair["invalid_response_excerpt"]


def test_full_regeneration_reuses_provider_schema_and_strict_output() -> None:
    backend = _SequenceBackend([{"status": "invalid"}, {"status": "valid"}])
    generate_validated_json_packet(
        provider=backend,
        request=_request(
            **{PROVIDER_STRUCTURED_OUTPUT_ON_REPAIR_METADATA_KEY: True}
        ),
        extract_payload=lambda text: extract_json_object(text, label="status"),
        build_packet=lambda payload, _response, _raw: dict(payload),
        validate_packet=lambda candidate: (
            [] if candidate.get("status") == "valid" else ["status must be valid"]
        ),
        validation_label="status packet",
        max_repair_attempts=1,
    )
    assert backend.requests[1].schema == backend.requests[0].schema
    assert backend.requests[1].metadata[PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY]


def test_regeneration_includes_subsystem_context() -> None:
    backend = _SequenceBackend([{"status": "invalid"}, {"status": "valid"}])
    generate_validated_json_packet(
        provider=backend,
        request=_request(),
        extract_payload=lambda text: extract_json_object(text, label="status"),
        build_packet=lambda payload, _response, _raw: dict(payload),
        validate_packet=lambda candidate: (
            [] if candidate.get("status") == "valid" else ["status must be valid"]
        ),
        validation_label="status packet",
        max_repair_attempts=1,
        repair_context_builder=lambda **kwargs: {
            "errors_seen": kwargs["errors"],
            "invalid_payload_seen": kwargs["invalid_payload"],
        },
    )
    repair = json.loads(backend.requests[1].user_prompt.split("\n\n", 1)[1])
    assert repair["subsystem_repair_context"] == {
        "errors_seen": ["status must be valid"],
        "invalid_payload_seen": {"status": "invalid"},
    }


def test_validation_error_preserves_final_invalid_packet() -> None:
    backend = _SequenceBackend([{"status": "bad"}, {"status": "still-bad"}])
    with pytest.raises(PacketValidationError) as caught:
        generate_validated_json_packet(
            provider=backend,
            request=_request(),
            extract_payload=lambda text: extract_json_object(text, label="status"),
            build_packet=lambda payload, _response, _raw: dict(payload),
            validate_packet=lambda _candidate: ["status must be valid"],
            validation_label="status packet",
            max_repair_attempts=1,
        )
    assert caught.value.last_invalid_packet == {"status": "still-bad"}
    assert caught.value.attempts == 2


def test_truncation_regeneration_increases_output_budget() -> None:
    class _TruncatedSequenceBackend(_SequenceBackend):
        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            response = super().generate(request)
            if len(self.requests) == 1:
                response.metadata["provider_stop_reason"] = "max_tokens"
            return response

    backend = _TruncatedSequenceBackend(
        ['{"status": "unfinished"', {"status": "valid"}]
    )
    packet = generate_validated_json_packet(
        provider=backend,
        request=_request(),
        extract_payload=lambda text: extract_json_object(text, label="status"),
        build_packet=lambda payload, _response, _raw: dict(payload),
        validate_packet=lambda candidate: (
            [] if candidate.get("status") == "valid" else ["status must be valid"]
        ),
        validation_label="status packet",
        max_repair_attempts=1,
    )
    assert packet["status"] == "valid"
    assert backend.requests[1].max_tokens == _repair_attempt_max_tokens(
        128, truncation_repair_mode=True
    )


def test_generic_typed_edit_remains_available_for_explicit_artifact_revision() -> None:
    base = {"rows": [{"status": "keep"}, {"status": "replace"}]}
    fingerprint = typed_semantic_patch_payload_fingerprint(base)
    patched, paths, annotations = _apply_typed_semantic_patch(
        base_payload=base,
        expected_base_fingerprint=fingerprint,
        patch_envelope={
            "base_payload_fingerprint": fingerprint,
            "updates": [
                {"path": ["rows", 1, "status"], "replacement": "valid"}
            ],
        },
        max_updates=1,
    )
    assert patched == {"rows": [{"status": "keep"}, {"status": "valid"}]}
    assert paths == [["rows", 1, "status"]]
    assert annotations == []
    assert _typed_semantic_patch_schema(max_updates=1)["properties"][
        "updates"
    ]["maxItems"] == 1


def test_compact_response_metadata_preserves_structured_output_fallback() -> None:
    assert _compact_response_metadata(
        {
            "provider_structured_output_requested": True,
            "provider_structured_output_applied": False,
            "provider_structured_output_fallback_reason": "unsupported",
            "ignored": "x" * 1000,
        }
    ) == {
        "provider_structured_output_requested": True,
        "provider_structured_output_applied": False,
        "provider_structured_output_fallback_reason": "unsupported",
    }
