from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Callable, Mapping

from .model_backend import GeneratorBackend, GeneratorRequest, GeneratorResponse


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
    for attempt_index in range(attempts):
        response = provider.generate(
            replace(
                request,
                user_prompt=user_prompt,
                metadata={
                    **dict(request.metadata),
                    "json_repair_attempt": attempt_index,
                    "json_repair_max_attempts": max_repair_attempts,
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
            errors = [f"{type(exc).__name__}: {exc}"]
        last_errors = [str(error) for error in errors]
        history.append(
            {
                "attempt_index": attempt_index,
                "provider": response.provider,
                "model": response.model,
                "ok": not last_errors,
                "errors": last_errors,
                "raw_response_fingerprint": _stable_text_fingerprint(raw_text),
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
    raise ValueError(
        f"{validation_label} failed validation after {attempts} attempt(s): "
        + "; ".join(last_errors)
    )


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
            "Satisfy the original required_output_contract exactly.",
            "Keep all fields concise so the corrected JSON finishes within the response budget.",
            "Preserve all evidence boundaries.",
            "Do not claim tool execution, simulation execution, production promotion, Lean proof, or kernel verification.",
        ],
        "original_request": original_user_prompt,
    }
    return (
        "Your previous response failed AI Statistician local validation. "
        "Repair the packet. Return ONLY corrected JSON.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )


def _stable_text_fingerprint(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
