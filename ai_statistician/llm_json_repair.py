from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Callable, Mapping

from .model_backend import (
    GeneratorBackend,
    GeneratorRequest,
    GeneratorResponse,
    resolve_generator_model,
)


PacketBuilder = Callable[[Mapping[str, Any], GeneratorResponse, str], dict[str, Any]]
PacketValidator = Callable[[Mapping[str, Any]], list[str]]
PayloadExtractor = Callable[[str], dict[str, Any]]


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
    """Generate, locally validate, and retry a structured LLM packet.

    The model backend remains a generator only. This helper owns the
    validate-repair iteration: it calls the generator, extracts JSON locally,
    runs the subsystem's semantic validator, and sends one or more repair
    prompts when the packet is malformed or unsafe.
    """

    original_user_prompt = request.user_prompt
    user_prompt = original_user_prompt
    history: list[dict[str, Any]] = []
    last_errors: list[str] = []
    attempts = max(0, max_repair_attempts) + 1
    requested_model_tier = _request_model_tier(request.metadata)
    effective_model_tier = requested_model_tier
    model_tier_escalated = False
    model_tier_escalation_reason = ""
    for attempt_index in range(attempts):
        request_model = _model_for_repair_attempt(
            provider,
            request,
            effective_model_tier=effective_model_tier,
            requested_model_tier=requested_model_tier,
        )
        response = provider.generate(
            replace(
                request,
                user_prompt=user_prompt,
                model=request_model,
                metadata={
                    **dict(request.metadata),
                    "json_repair_attempt": attempt_index,
                    "json_repair_max_attempts": max_repair_attempts,
                    "requested_model_tier": requested_model_tier,
                    "effective_model_tier": effective_model_tier,
                    "model_tier_escalated": model_tier_escalated,
                    "model_tier_escalation_reason": model_tier_escalation_reason,
                },
            )
        )
        raw_text = response.text
        packet: dict[str, Any] | None = None
        try:
            payload = extract_payload(raw_text)
            packet = build_packet(payload, response, raw_text)
            errors = validate_packet(packet)
        except Exception as exc:
            errors = [_format_generation_error(exc, raw_text)]
        last_errors = [str(error) for error in errors]
        history.append(
            {
                "attempt_index": attempt_index,
                "provider": response.provider,
                "model": response.model,
                "requested_model_tier": requested_model_tier,
                "effective_model_tier": effective_model_tier,
                "model_tier_escalated": model_tier_escalated,
                "model_tier_escalation_reason": model_tier_escalation_reason,
                "ok": not last_errors,
                "errors": last_errors,
                "raw_response_fingerprint": _stable_text_fingerprint(raw_text),
                "response_text_chars": len(raw_text),
                "response_metadata": _compact_response_metadata(response.metadata),
            }
        )
        if packet is not None and not last_errors:
            packet["validation_errors"] = []
            packet["ok"] = True
            packet["llm_json_repair_attempts"] = attempt_index
            packet["llm_json_repair_history"] = history
            return packet
        if attempt_index < attempts - 1:
            user_prompt = _repair_prompt(
                original_user_prompt=original_user_prompt,
                bad_response=raw_text,
                errors=last_errors,
                validation_label=validation_label,
            )
            next_model_tier, escalation_reason = _next_repair_model_tier(
                provider,
                request,
                current_model_tier=effective_model_tier,
            )
            if next_model_tier != effective_model_tier:
                model_tier_escalated = True
                model_tier_escalation_reason = escalation_reason
            effective_model_tier = next_model_tier
    raise ValueError(
        f"{validation_label} failed validation after {attempts} attempt(s): "
        + "; ".join(last_errors)
        + _failure_history_suffix(history)
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


def _compact_response_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    keep_keys = (
        "provider_stop_reason",
        "provider_stop_sequence",
        "provider_status",
        "provider_incomplete_details",
        "provider_usage",
        "retry_count",
        "timeout_seconds",
        "requested_model",
        "provider_reported_model",
        "request_model_tier",
        "provider_reported_model_tier",
        "provider_reported_model_tier_mismatch",
        "requested_model_tier_mismatch",
        "requested_model_tier",
        "effective_model_tier",
        "model_tier_escalated",
        "model_tier_escalation_reason",
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


def _request_model_tier(metadata: Mapping[str, Any]) -> str:
    for key in ("effective_model_tier", "model_tier", "requested_model_tier"):
        tier = str(metadata.get(key, "") or "").strip().lower()
        if tier:
            return tier
    return ""


def _provider_name(provider: GeneratorBackend, request: GeneratorRequest) -> str:
    return str(
        request.metadata.get("provider_name", "")
        or getattr(provider, "provider_name", "")
        or ""
    ).strip().lower()


def _model_for_repair_attempt(
    provider: GeneratorBackend,
    request: GeneratorRequest,
    *,
    effective_model_tier: str,
    requested_model_tier: str,
) -> str:
    provider_name = _provider_name(provider, request)
    if (
        provider_name == "anthropic"
        and effective_model_tier
        and requested_model_tier
        and effective_model_tier != requested_model_tier
    ):
        return resolve_generator_model(
            provider_name=provider_name,
            model_tier=effective_model_tier,
        )
    return request.model


def _next_repair_model_tier(
    provider: GeneratorBackend,
    request: GeneratorRequest,
    *,
    current_model_tier: str,
) -> tuple[str, str]:
    current = str(current_model_tier or "").strip().lower()
    if _provider_name(provider, request) != "anthropic" or current != "haiku":
        return current, ""
    if _explicit_model_override_blocks_escalation(request, current_model_tier=current):
        return current, ""
    return (
        "sonnet",
        (
            "auto escalated Anthropic JSON repair from Claude Haiku to Claude "
            "Sonnet after local validation failed"
        ),
    )


def _explicit_model_override_blocks_escalation(
    request: GeneratorRequest,
    *,
    current_model_tier: str,
) -> bool:
    metadata = request.metadata
    if bool(metadata.get("json_repair_model_tier_escalation_disabled", False)):
        return True
    explicit = bool(
        metadata.get("explicit_model_configured", False)
        or metadata.get("explicit_model_override", False)
    )
    if not explicit:
        return False
    provider_name = str(metadata.get("provider_name", "") or "").strip().lower()
    configured_model = str(request.model or "").strip()
    tier_default = resolve_generator_model(
        provider_name=provider_name or "anthropic",
        model_tier=current_model_tier,
    )
    return bool(configured_model and configured_model != tier_default)


def _repair_prompt(
    *,
    original_user_prompt: str,
    bad_response: str,
    errors: list[str],
    validation_label: str,
) -> str:
    payload = {
        "validation_label": validation_label,
        "local_validation_errors": errors,
        "invalid_response_excerpt": bad_response[:2000],
        "repair_instructions": [
            "Return only a single JSON object.",
            "Rewrite the full JSON object from scratch; do not continue or patch the invalid response.",
            "Satisfy the original required_output_contract exactly.",
            "Keep all fields concise so the corrected JSON finishes within the response budget.",
            "Use exactly one item for required arrays unless the original contract explicitly requires more.",
            "Keep string fields under 240 characters and avoid multiline derivation essays.",
            "Preserve all evidence boundaries.",
            "Do not claim tool execution, simulation execution, production promotion, Lean proof, or kernel verification.",
        ],
        "original_request": _compact_original_request(original_user_prompt),
    }
    return (
        "Your previous response failed AI Statistician local validation. "
        "Repair the packet. Return ONLY corrected JSON.\n\n"
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


def _compact_original_request(
    prompt: str,
    *,
    head_chars: int = 2500,
    tail_chars: int = 4500,
) -> dict[str, Any]:
    """Keep repair prompts bounded while preserving instructions and contract.

    The first attempt already receives the complete prompt. Re-sending that
    full prompt inside the repair payload can make the repair request longer
    than the request that failed, especially for Architect packets with runtime
    memory. Most subsystem prompts put role instructions at the start and the
    serialized output contract/context near the end, so keep both ends and make
    the truncation explicit.
    """

    text = str(prompt or "")
    limit = max(0, head_chars) + max(0, tail_chars)
    if len(text) <= limit:
        return {
            "truncated": False,
            "text": text,
            "n_chars": len(text),
        }
    return {
        "truncated": True,
        "n_chars": len(text),
        "head": text[: max(0, head_chars)],
        "tail": text[-max(0, tail_chars) :] if tail_chars > 0 else "",
        "omitted_chars": max(0, len(text) - limit),
    }
