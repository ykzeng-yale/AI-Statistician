from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping


class PacketValidationError(ValueError):
    """Typed validation failure with exact observations and optional checkpoint."""

    def __init__(
        self,
        *,
        validation_label: str,
        attempts: int,
        errors: list[str],
        history: list[dict[str, Any]],
        last_invalid_packet: Mapping[str, Any] | None = None,
        recovery_checkpoint: Mapping[str, Any] | None = None,
    ) -> None:
        self.validation_label = validation_label
        self.attempts = attempts
        self.errors = [str(error) for error in errors]
        self.history = [dict(row) for row in history]
        self.last_invalid_packet = (
            deepcopy(dict(last_invalid_packet))
            if isinstance(last_invalid_packet, Mapping)
            else None
        )
        self.recovery_checkpoint = (
            deepcopy(dict(recovery_checkpoint))
            if isinstance(recovery_checkpoint, Mapping)
            else None
        )
        super().__init__(
            f"{validation_label} failed validation after {attempts} attempt(s): "
            + "; ".join(self.errors)
            + _failure_history_suffix(self.history)
        )


def extract_json_object(text: str, *, label: str = "LLM response") -> dict[str, Any]:
    """Read one JSON object without calling a model or repairing its content."""

    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = _strip_outer_code_fence(stripped)
    try:
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            return payload
        raise ValueError(f"expected JSON object from {label}")
    except json.JSONDecodeError as original_exc:
        candidates = _json_object_candidates(stripped)
        last_exc: Exception = original_exc
        for candidate in candidates:
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError as exc:
                last_exc = exc
                continue
            if isinstance(payload, dict):
                return payload
            last_exc = ValueError(f"expected JSON object from {label}")
        raise last_exc


def _failure_history_suffix(history: list[dict[str, Any]]) -> str:
    if not history:
        return ""
    last = {
        key: history[-1].get(key)
        for key in (
            "attempt_index",
            "provider",
            "model",
            "response_text_chars",
            "request_max_tokens",
            "response_metadata",
            "raw_response_fingerprint",
        )
        if history[-1].get(key) not in (None, "", [], {})
    }
    return "; last_attempt_summary=" + json.dumps(
        last, sort_keys=True, default=str
    )[:1200]


def _strip_outer_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _json_object_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    for block in _fenced_blocks(text):
        candidates.extend(_balanced_json_objects(block))
    candidates.extend(_balanced_json_objects(text))
    if not candidates:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidates.append(text[start : end + 1])
    return list(dict.fromkeys(value.strip() for value in candidates if value.strip()))


def _fenced_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    in_block = False
    current: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            if in_block:
                blocks.append("\n".join(current).strip())
                current = []
            in_block = not in_block
            continue
        if in_block:
            current.append(line)
    return [block for block in blocks if block]


def _balanced_json_objects(text: str) -> list[str]:
    objects: list[str] = []
    start: int | None = None
    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(text):
        if escape:
            escape = False
            continue
        if char == "\\" and in_string:
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : index + 1])
                start = None
    return objects
