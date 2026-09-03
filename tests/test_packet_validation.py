from __future__ import annotations

import importlib.util
import json

import pytest

from ai_statistician.packet_validation import (
    PacketValidationError,
    extract_json_object,
)


def test_extract_json_object_handles_fenced_and_trailing_text() -> None:
    assert extract_json_object(
        "```json\n{\"ok\": true, \"items\": [1, 2]}\n``` trailing",
        label="test",
    ) == {"ok": True, "items": [1, 2]}


def test_extract_json_object_preserves_decode_error() -> None:
    with pytest.raises(json.JSONDecodeError):
        extract_json_object('{"ok": true "missing": true}', label="test")


def test_packet_validation_error_preserves_observations_without_generation() -> None:
    invalid = {"status": "bad"}
    checkpoint = {"checkpoint_id": "checkpoint:1"}
    error = PacketValidationError(
        validation_label="status packet",
        attempts=1,
        errors=["status must be valid"],
        history=[{"attempt_index": 0, "provider": "fixture"}],
        last_invalid_packet=invalid,
        recovery_checkpoint=checkpoint,
    )
    invalid["status"] = "mutated"
    checkpoint["checkpoint_id"] = "mutated"

    assert error.last_invalid_packet == {"status": "bad"}
    assert error.recovery_checkpoint == {"checkpoint_id": "checkpoint:1"}
    assert error.history == [{"attempt_index": 0, "provider": "fixture"}]
    assert "status must be valid" in str(error)


def test_retired_structured_output_retry_module_is_absent() -> None:
    assert importlib.util.find_spec(
        "ai_statistician.structured_output_retry"
    ) is None
