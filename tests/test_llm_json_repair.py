from __future__ import annotations

import json

import pytest

from ai_statistician.llm_json_repair import (
    PacketValidationError,
    _compact_response_metadata,
    _format_generation_error,
    _regeneration_attempt_max_tokens,
    _regeneration_prompt,
    extract_json_object,
    generate_validated_json_packet,
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


def test_regeneration_prompt_returns_full_model_context() -> None:
    prior = json.dumps({"status": "invalid", "detail": "y" * 8000})
    prompt = _regeneration_prompt(
        original_user_prompt="START" + ("x" * 9000) + "END",
        previous_response=prior,
        errors=["status must be valid"],
        validation_label="status packet",
    )
    payload = json.loads(prompt.split("\n\n", 1)[1])
    assert payload["original_request"] == "START" + ("x" * 9000) + "END"
    assert payload["previous_candidate"] == prior
    requirements = " ".join(payload["regeneration_requirements"])
    assert "Rewrite the full JSON object from scratch" in requirements
    assert "do not emit a patch" in requirements


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
    regeneration = json.loads(
        backend.requests[1].user_prompt.split("\n\n", 1)[1]
    )
    assert regeneration["local_validation_errors"] == ["status must be valid"]
    assert '"keep": "context"' in regeneration["previous_candidate"]


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


def test_regeneration_has_no_subsystem_repair_adapter() -> None:
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
    )
    regeneration = json.loads(
        backend.requests[1].user_prompt.split("\n\n", 1)[1]
    )
    assert "subsystem_repair_context" not in regeneration
    assert regeneration["local_validation_errors"] == ["status must be valid"]
    assert regeneration["previous_candidate"] == '{"status": "invalid"}'


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


def test_full_regeneration_stops_when_validator_feedback_is_unchanged() -> None:
    backend = _SequenceBackend(
        [
            {"status": "bad", "version": 1},
            {"status": "bad", "version": 1},
            {"status": "unused", "version": 3},
        ]
    )

    with pytest.raises(PacketValidationError) as caught:
        generate_validated_json_packet(
            provider=backend,
            request=_request(),
            extract_payload=lambda text: extract_json_object(text, label="status"),
            build_packet=lambda payload, _response, _raw: dict(payload),
            validate_packet=lambda _candidate: ["status must be valid"],
            validation_label="status packet",
            max_repair_attempts=2,
        )

    assert len(backend.requests) == 2
    assert caught.value.attempts == 2
    assert caught.value.last_invalid_packet == {
        "status": "bad",
        "version": 1,
    }
    assert caught.value.history[-1]["no_progress_detected"] is True
    assert caught.value.history[-1]["no_progress_reason"] == (
        "validator_errors_unchanged_after_full_regeneration"
    )


def test_full_regeneration_continues_when_candidate_changes() -> None:
    backend = _SequenceBackend(
        [
            {"status": "bad", "version": 1},
            {"status": "still-bad", "version": 2},
            {"status": "valid", "version": 3},
        ]
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
        max_repair_attempts=2,
    )

    assert packet["status"] == "valid"
    assert len(backend.requests) == 3


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
    assert backend.requests[1].max_tokens == _regeneration_attempt_max_tokens(
        128, truncation_regeneration_mode=True
    )


def test_final_semantic_attempt_truncation_gets_one_transport_regeneration() -> None:
    class _FinalAttemptTruncatedBackend(_SequenceBackend):
        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            response = super().generate(request)
            if len(self.requests) == 2:
                response.metadata["provider_stop_reason"] = "max_tokens"
            return response

    backend = _FinalAttemptTruncatedBackend(
        [
            {"status": "invalid"},
            '{"status": "unfinished"',
            {"status": "valid"},
        ]
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
    assert len(backend.requests) == 3
    assert backend.requests[2].max_tokens == _regeneration_attempt_max_tokens(
        128,
        truncation_regeneration_mode=True,
    )
    assert packet["llm_json_repair_history"][1]["truncation_detected"] is True


def test_transport_regeneration_is_bounded() -> None:
    class _RepeatedTruncationBackend(_SequenceBackend):
        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            response = super().generate(request)
            if len(self.requests) >= 2:
                response.metadata["provider_stop_reason"] = "max_tokens"
            return response

    backend = _RepeatedTruncationBackend(
        [
            {"status": "invalid"},
            '{"status": "unfinished"',
            '{"status": "still unfinished"',
        ]
    )

    with pytest.raises(PacketValidationError) as caught:
        generate_validated_json_packet(
            provider=backend,
            request=_request(),
            extract_payload=lambda text: extract_json_object(text, label="status"),
            build_packet=lambda payload, _response, _raw: dict(payload),
            validate_packet=lambda candidate: (
                []
                if candidate.get("status") == "valid"
                else ["status must be valid"]
            ),
            validation_label="status packet",
            max_repair_attempts=1,
        )

    assert caught.value.attempts == 3
    assert len(backend.requests) == 3


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
