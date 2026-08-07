from __future__ import annotations

from copy import deepcopy
import json
from dataclasses import replace
from typing import Any, Callable, Mapping

from .model_backend import (
    PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY,
    PROVIDER_STRUCTURED_OUTPUT_ON_REPAIR_METADATA_KEY,
    GeneratorBackend,
    GeneratorRequest,
    GeneratorResponse,
)


PacketBuilder = Callable[[Mapping[str, Any], GeneratorResponse, str], dict[str, Any]]
PacketValidator = Callable[[Mapping[str, Any]], list[str]]
PayloadExtractor = Callable[[str], dict[str, Any]]


_TRUNCATION_REGENERATION_MAX_TOKENS = 16000
_MAX_TRUNCATION_REGENERATIONS = 1


class PacketValidationError(ValueError):
    """Structured packet validation failure for runtime learning feedback."""

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


def generate_validated_json_packet(
    *,
    provider: GeneratorBackend,
    request: GeneratorRequest,
    extract_payload: PayloadExtractor,
    build_packet: PacketBuilder,
    validate_packet: PacketValidator,
    validation_label: str,
    max_repair_attempts: int = 1,
) -> dict[str, Any]:
    """Generate, locally validate, and regenerate a structured LLM packet.

    The model backend remains a generator only. This helper owns the
    validation-feedback iteration: it calls the generator, extracts JSON locally,
    runs the subsystem validator, and asks the same model for a complete new
    candidate when the packet is invalid. It never edits a candidate itself.
    """

    original_user_prompt = request.user_prompt
    user_prompt = original_user_prompt
    history: list[dict[str, Any]] = []
    last_errors: list[str] = []
    last_invalid_packet: dict[str, Any] | None = None
    semantic_regenerations_remaining = max(0, max_repair_attempts)
    truncation_regenerations_remaining = _MAX_TRUNCATION_REGENERATIONS
    attempt_index = 0
    while True:
        truncation_regeneration_mode = bool(
            history and _history_row_indicates_truncation(history[-1])
        )
        request_max_tokens = _regeneration_attempt_max_tokens(
            request.max_tokens,
            truncation_regeneration_mode=truncation_regeneration_mode,
        )
        attempt_metadata = {
            **dict(request.metadata),
            "json_repair_attempt": attempt_index,
            "json_repair_max_attempts": max_repair_attempts,
            "json_repair_previous_attempt_truncated": truncation_regeneration_mode,
            "json_repair_truncation_repair_mode": truncation_regeneration_mode,
            "json_truncation_regenerations_remaining": (
                truncation_regenerations_remaining
            ),
            "json_truncation_regeneration_limit": (
                _MAX_TRUNCATION_REGENERATIONS
            ),
            "json_repair_request_max_tokens": request_max_tokens,
            "json_repair_mode": (
                "full_packet_generation"
                if attempt_index == 0
                else "full_packet_regeneration"
            ),
        }
        if (
            attempt_index > 0
            and request.metadata.get(
                PROVIDER_STRUCTURED_OUTPUT_ON_REPAIR_METADATA_KEY
            )
            is True
        ):
            attempt_metadata[PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY] = True
        response = provider.generate(
            replace(
                request,
                user_prompt=user_prompt,
                max_tokens=request_max_tokens,
                schema=request.schema,
                metadata=attempt_metadata,
            )
        )
        raw_text = response.text
        payload: dict[str, Any] | None = None
        packet: dict[str, Any] | None = None
        try:
            payload = extract_payload(raw_text)
            packet = build_packet(payload, response, raw_text)
            errors = validate_packet(packet)
        except Exception as exc:
            generation_error = _format_generation_error(exc, raw_text)
            errors = [generation_error]
        last_errors = [str(error) for error in errors]
        if packet is not None and last_errors:
            last_invalid_packet = deepcopy(packet)
        history_row = {
            "attempt_index": attempt_index,
            "provider": response.provider,
            "model": response.model,
            "ok": not last_errors,
            "errors": last_errors,
            "repair_mode": (
                "full_packet_generation"
                if attempt_index == 0
                else "full_packet_regeneration"
            ),
            "raw_response_fingerprint": _stable_text_fingerprint(raw_text),
            "response_text_chars": len(raw_text),
            "request_max_tokens": request_max_tokens,
            "payload_extracted": payload is not None,
            "packet_built": packet is not None,
            "response_metadata": _compact_response_metadata(response.metadata),
        }
        truncation_detected = _response_indicates_truncation(
            response,
            request_max_tokens=request_max_tokens,
        )
        history_row["truncation_detected"] = truncation_detected
        history.append(history_row)
        if packet is not None and not last_errors:
            packet["validation_errors"] = []
            packet["ok"] = True
            packet["llm_json_repair_attempts"] = attempt_index
            packet["llm_json_repair_history"] = history
            return packet
        if (
            not truncation_detected
            and len(history) >= 2
            and history[-1]["errors"] == history[-2]["errors"]
            and history[-1]["raw_response_fingerprint"]
            == history[-2]["raw_response_fingerprint"]
        ):
            history[-1]["no_progress_detected"] = True
            history[-1]["no_progress_reason"] = (
                "validator_errors_unchanged_after_full_regeneration"
            )
            break
        if truncation_detected:
            if truncation_regenerations_remaining <= 0:
                break
            truncation_regenerations_remaining -= 1
        else:
            if semantic_regenerations_remaining <= 0:
                break
            semantic_regenerations_remaining -= 1
        user_prompt = _regeneration_prompt(
            original_user_prompt=original_user_prompt,
            previous_response=raw_text,
            errors=last_errors,
            validation_label=validation_label,
            truncation_detected=truncation_detected,
        )
        attempt_index += 1
    raise PacketValidationError(
        validation_label=validation_label,
        attempts=len(history),
        errors=last_errors,
        history=history,
        last_invalid_packet=last_invalid_packet,
    )

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
    return "; last_attempt_summary=" + json.dumps(last, sort_keys=True, default=str)[:1200]


def _format_generation_error(exc: Exception, raw_text: str) -> str:
    message = f"{type(exc).__name__}: {exc}"
    if isinstance(exc, json.JSONDecodeError):
        excerpt = _single_line_excerpt(raw_text, center=exc.pos, radius=320)
        if excerpt:
            message += f"; response_excerpt_around_error={excerpt!r}"
    return message


def _response_indicates_truncation(
    response: GeneratorResponse,
    *,
    request_max_tokens: int,
) -> bool:
    metadata = response.metadata
    stop_reason = str(metadata.get("provider_stop_reason", "") or "").lower()
    incomplete_reason = str(
        metadata.get("provider_incomplete_details", "") or ""
    ).lower()
    if any(
        marker in f"{stop_reason} {incomplete_reason}"
        for marker in ("max_tokens", "length", "output_limit")
    ):
        return True
    usage = metadata.get("provider_usage", {})
    if isinstance(usage, Mapping):
        output_tokens = usage.get("output_tokens")
        try:
            requested = int(request_max_tokens or 0)
            observed = int(output_tokens or 0)
        except (TypeError, ValueError):
            return False
        return requested > 0 and observed >= requested
    return False


def _history_row_indicates_truncation(row: Mapping[str, Any]) -> bool:
    metadata = row.get("response_metadata", {})
    if not isinstance(metadata, Mapping):
        return False
    stop_reason = str(metadata.get("provider_stop_reason", "") or "").lower()
    incomplete_reason = str(
        metadata.get("provider_incomplete_details", "") or ""
    ).lower()
    if any(
        marker in f"{stop_reason} {incomplete_reason}"
        for marker in ("max_tokens", "length", "output_limit")
    ):
        return True
    usage = metadata.get("provider_usage", {})
    if isinstance(usage, Mapping):
        output_tokens = usage.get("output_tokens")
        try:
            requested = int(row.get("request_max_tokens", 0) or 0)
            observed = int(output_tokens or 0)
        except (TypeError, ValueError):
            return False
        return requested > 0 and observed >= requested
    return False


def _regeneration_attempt_max_tokens(
    base_max_tokens: int,
    *,
    truncation_regeneration_mode: bool,
) -> int:
    base = max(1, int(base_max_tokens or 1))
    if not truncation_regeneration_mode:
        return base
    return max(
        base,
        min(
            max(base * 2, base + 1024),
            _TRUNCATION_REGENERATION_MAX_TOKENS,
        ),
    )


def _compact_response_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    keep_keys = (
        "provider_stop_reason",
        "provider_stop_sequence",
        "provider_status",
        "provider_incomplete_details",
        "provider_usage",
        "retry_count",
        "provider_capability_fallback_count",
        "provider_structured_output_requested",
        "provider_structured_output_applied",
        "provider_structured_output_schema_fingerprint",
        "provider_structured_output_fallback_count",
        "provider_structured_output_fallback_reason",
        "provider_structured_output_cached_fallback",
        "omitted_unsupported_request_parameters",
        "cached_unsupported_request_parameters",
        "timeout_seconds",
        "requested_model",
        "provider_reported_model",
        "request_model_tier",
        "provider_reported_model_tier",
        "provider_reported_model_tier_mismatch",
        "requested_model_tier_mismatch",
    )
    compact: dict[str, Any] = {}
    for key in keep_keys:
        value = metadata.get(key)
        if value not in (None, "", [], {}):
            compact[key] = _compact_metadata_value(value)
    return compact


def _compact_metadata_value(value: Any) -> Any:
    if isinstance(value, str):
        return value if len(value) <= 400 else value[:397] + "..."
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _compact_metadata_value(child)
            for key, child in list(value.items())[:12]
            if child not in (None, "", [], {})
        }
    if isinstance(value, list):
        return [_compact_metadata_value(item) for item in value[:8]]
    return str(value)[:400]


def _regeneration_prompt(
    *,
    original_user_prompt: str,
    previous_response: str,
    errors: list[str],
    validation_label: str,
    truncation_detected: bool = False,
) -> str:
    original_request = str(original_user_prompt or "")
    previous_candidate = str(previous_response or "")
    regeneration_requirements = [
        "Return only a single JSON object.",
        (
            "Rewrite the full JSON object from scratch using the original request, "
            "schema, prior response, and validator feedback; do not emit a patch."
        ),
        "Satisfy the original required_output_contract exactly.",
        "Resolve every local_validation_errors row in the regenerated object.",
        (
            "You own the regenerated model-authored content and may revise its approach, "
            "decomposition, or implementation wherever the feedback warrants it."
        ),
        "Preserve all evidence boundaries.",
        "Do not claim tool execution, simulation execution, production promotion, Lean proof, or kernel verification.",
        "Do not weaken or alter immutable targets, authority, lineage, or acceptance gates.",
    ]
    if truncation_detected:
        regeneration_requirements.insert(
            0,
            (
                "The previous response stopped because the provider hit the max "
                "token/output limit. The runtime has expanded the output budget; "
                "regenerate one complete JSON object."
            ),
        )
    payload = {
        "validation_label": validation_label,
        "local_validation_errors": errors,
        "truncation_detected": truncation_detected,
        "previous_candidate": previous_candidate,
        "regeneration_requirements": regeneration_requirements,
        "original_request": original_request,
    }
    return (
        "Your previous response failed AI Statistician local validation. "
        "Generate a complete new candidate. Return ONLY the regenerated JSON.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )


def _single_line_excerpt(text: str, *, center: int, radius: int) -> str:
    raw = str(text or "")
    if not raw:
        return ""
    start = max(0, center - max(0, radius))
    end = min(len(raw), center + max(0, radius))
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(raw) else ""
    excerpt = raw[start:end].replace("\n", "\\n")
    return prefix + excerpt + suffix


def extract_json_object(text: str, *, label: str = "LLM response") -> dict[str, Any]:
    """Extract one JSON object from a generator response.

    LLMs often wrap JSON in Markdown or add brief prose. Prefer exact parsing,
    then parse the first fenced block, then fall back to the first balanced JSON
    object. The balanced scan avoids the old greedy regex path that could grab
    prose braces across a whole response and make repair noisier.
    """

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
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        key = candidate.strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def _fenced_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    lines = text.splitlines()
    in_block = False
    current: list[str] = []
    for line in lines:
        if line.strip().startswith("```"):
            if in_block:
                blocks.append("\n".join(current).strip())
                current = []
                in_block = False
            else:
                in_block = True
                current = []
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
            continue
        if char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : index + 1])
                start = None
    return objects


def _stable_text_fingerprint(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
