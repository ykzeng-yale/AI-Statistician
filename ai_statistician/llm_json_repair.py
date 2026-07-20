from __future__ import annotations

from copy import deepcopy
import json
from dataclasses import replace
from typing import Any, Callable, Mapping

from .model_backend import GeneratorBackend, GeneratorRequest, GeneratorResponse


PacketBuilder = Callable[[Mapping[str, Any], GeneratorResponse, str], dict[str, Any]]
PacketValidator = Callable[[Mapping[str, Any]], list[str]]
PayloadExtractor = Callable[[str], dict[str, Any]]
RepairContextBuilder = Callable[..., Mapping[str, Any] | None]


_TYPED_SEMANTIC_PATCH_MAX_VALIDATION_ERRORS = 8
_TYPED_SEMANTIC_PATCH_MAX_UPDATES = 16
_TYPED_SEMANTIC_PATCH_MAX_PATH_DEPTH = 8
_TYPED_SEMANTIC_PATCH_MAX_TOKENS = 5000
_TYPED_SEMANTIC_PATCH_PROMPT_WRAPPER_KEYS = frozenset(
    {
        "base_payload_excerpt",
        "top_level_outline",
    }
)
_TYPED_SEMANTIC_PATCH_MAX_RAW_PATH_DEPTH = (
    _TYPED_SEMANTIC_PATCH_MAX_PATH_DEPTH
    + len(_TYPED_SEMANTIC_PATCH_PROMPT_WRAPPER_KEYS)
)
_TYPED_SEMANTIC_PATCH_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["base_payload_fingerprint", "updates"],
    "properties": {
        "base_payload_fingerprint": {"type": "string"},
        "updates": {
            "type": "array",
            "minItems": 1,
            "maxItems": _TYPED_SEMANTIC_PATCH_MAX_UPDATES,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "replacement_json"],
                "properties": {
                    "path": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": _TYPED_SEMANTIC_PATCH_MAX_RAW_PATH_DEPTH,
                        "items": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "integer", "minimum": 0},
                            ]
                        },
                    },
                    "replacement_json": {"type": "string"},
                },
            },
        },
    },
}


class PacketValidationError(ValueError):
    """Structured packet validation failure for runtime learning feedback."""

    def __init__(
        self,
        *,
        validation_label: str,
        attempts: int,
        errors: list[str],
        history: list[dict[str, Any]],
    ) -> None:
        self.validation_label = validation_label
        self.attempts = attempts
        self.errors = [str(error) for error in errors]
        self.history = [dict(row) for row in history]
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
    repair_context_builder: RepairContextBuilder | None = None,
    semantic_patch_repair: bool = False,
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
    semantic_patch_base_payload: dict[str, Any] | None = None
    semantic_patch_base_fingerprint = ""
    attempts = max(0, max_repair_attempts) + 1
    for attempt_index in range(attempts):
        typed_semantic_patch_mode = bool(
            semantic_patch_repair and semantic_patch_base_payload is not None
        )
        truncation_repair_mode = bool(
            history and _history_row_indicates_truncation(history[-1])
        )
        request_max_tokens = _repair_attempt_max_tokens(
            request.max_tokens,
            truncation_repair_mode=truncation_repair_mode,
        )
        if typed_semantic_patch_mode:
            request_max_tokens = min(
                request_max_tokens,
                _TYPED_SEMANTIC_PATCH_MAX_TOKENS,
            )
        response = provider.generate(
            replace(
                request,
                user_prompt=user_prompt,
                max_tokens=request_max_tokens,
                schema=(
                    _TYPED_SEMANTIC_PATCH_SCHEMA
                    if typed_semantic_patch_mode
                    else request.schema
                ),
                metadata={
                    **dict(request.metadata),
                    "json_repair_attempt": attempt_index,
                    "json_repair_max_attempts": max_repair_attempts,
                    "json_repair_previous_attempt_truncated": truncation_repair_mode,
                    "json_repair_truncation_repair_mode": truncation_repair_mode,
                    "json_repair_request_max_tokens": request_max_tokens,
                    "json_repair_mode": (
                        "typed_semantic_patch"
                        if typed_semantic_patch_mode
                        else "full_packet_generation"
                        if attempt_index == 0
                        else "full_packet_regeneration"
                    ),
                },
            )
        )
        raw_text = response.text
        payload: dict[str, Any] | None = None
        packet: dict[str, Any] | None = None
        patched_paths: list[list[str | int]] = []
        patch_path_normalizations: list[dict[str, Any]] = []
        patched_payload_fingerprint = ""
        try:
            effective_raw_text = raw_text
            if typed_semantic_patch_mode:
                patch_envelope = extract_json_object(
                    raw_text,
                    label=f"{validation_label} typed semantic patch",
                )
                (
                    payload,
                    patched_paths,
                    patch_path_normalizations,
                ) = _apply_typed_semantic_patch(
                    base_payload=semantic_patch_base_payload or {},
                    expected_base_fingerprint=semantic_patch_base_fingerprint,
                    patch_envelope=patch_envelope,
                )
                patched_payload_fingerprint = _stable_payload_fingerprint(payload)
                effective_raw_text = json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                    ensure_ascii=False,
                )
            else:
                payload = extract_payload(raw_text)
            packet = build_packet(payload, response, effective_raw_text)
            errors = validate_packet(packet)
        except Exception as exc:
            generation_error = _format_generation_error(exc, raw_text)
            errors = (
                list(
                    dict.fromkeys(
                        [
                            *(
                                history[-1].get("errors", [])
                                if history
                                and isinstance(history[-1].get("errors", []), list)
                                else []
                            ),
                            "typed semantic patch repair failed: "
                            + generation_error,
                        ]
                    )
                )
                if typed_semantic_patch_mode
                else [generation_error]
            )
        last_errors = [str(error) for error in errors]
        history_row = {
            "attempt_index": attempt_index,
            "provider": response.provider,
            "model": response.model,
            "ok": not last_errors,
            "errors": last_errors,
            "repair_mode": (
                "typed_semantic_patch"
                if typed_semantic_patch_mode
                else "full_packet_generation"
                if attempt_index == 0
                else "full_packet_regeneration"
            ),
            "raw_response_fingerprint": _stable_text_fingerprint(raw_text),
            "response_text_chars": len(raw_text),
            "request_max_tokens": request_max_tokens,
            "response_metadata": _compact_response_metadata(response.metadata),
        }
        if typed_semantic_patch_mode:
            history_row.update(
                {
                    "base_payload_fingerprint": semantic_patch_base_fingerprint,
                    "patched_paths": patched_paths,
                    "patch_path_normalizations": patch_path_normalizations,
                    "patched_payload_fingerprint": patched_payload_fingerprint,
                }
            )
        history.append(history_row)
        if packet is not None and not last_errors:
            packet["validation_errors"] = []
            packet["ok"] = True
            packet["llm_json_repair_attempts"] = attempt_index
            packet["llm_json_repair_history"] = history
            return packet
        if attempt_index < attempts - 1:
            repair_context = (
                repair_context_builder(
                    original_user_prompt=original_user_prompt,
                    bad_response=raw_text,
                    invalid_packet=(dict(packet) if packet is not None else None),
                    errors=last_errors,
                    validation_label=validation_label,
                    truncation_detected=_response_indicates_truncation(
                        response,
                        request_max_tokens=request_max_tokens,
                    ),
                )
                if repair_context_builder is not None
                else None
            )
            truncation_detected = _response_indicates_truncation(
                response,
                request_max_tokens=request_max_tokens,
            )
            if (
                semantic_patch_repair
                and payload is not None
                and not truncation_detected
                and _typed_semantic_patch_fits_update_budget(last_errors)
            ):
                semantic_patch_base_payload = deepcopy(payload)
                semantic_patch_base_fingerprint = _stable_payload_fingerprint(
                    semantic_patch_base_payload
                )
                user_prompt = _typed_semantic_patch_prompt(
                    original_user_prompt=original_user_prompt,
                    errors=last_errors,
                    validation_label=validation_label,
                    base_payload=semantic_patch_base_payload,
                    base_payload_fingerprint=semantic_patch_base_fingerprint,
                    repair_context=repair_context,
                )
            else:
                semantic_patch_base_payload = None
                semantic_patch_base_fingerprint = ""
                user_prompt = _repair_prompt(
                    original_user_prompt=original_user_prompt,
                    bad_response=raw_text,
                    errors=last_errors,
                    validation_label=validation_label,
                    truncation_detected=truncation_detected,
                    repair_context=repair_context,
                )
    raise PacketValidationError(
        validation_label=validation_label,
        attempts=attempts,
        errors=last_errors,
        history=history,
    )


def _typed_semantic_patch_prompt(
    *,
    original_user_prompt: str,
    errors: list[str],
    validation_label: str,
    base_payload: Mapping[str, Any],
    base_payload_fingerprint: str,
    repair_context: Mapping[str, Any] | None = None,
) -> str:
    base_payload_excerpt, base_payload_excerpt_metadata = (
        _compact_patch_base_payload(base_payload)
    )
    payload: dict[str, Any] = {
        "validation_label": validation_label,
        "local_validation_errors": errors,
        "base_payload_fingerprint": base_payload_fingerprint,
        "base_payload_excerpt": base_payload_excerpt,
        "base_payload_excerpt_metadata": base_payload_excerpt_metadata,
        "patch_contract": {
            "base_payload_fingerprint": (
                "copy the supplied fingerprint exactly"
            ),
            "updates": [
                {
                    "path": ["top_level_field", 0, "nested_field"],
                    "replacement_json": (
                        "JSON-encoded replacement value, supplied as a string"
                    ),
                }
            ],
            "maximum_updates": _TYPED_SEMANTIC_PATCH_MAX_UPDATES,
            "maximum_path_depth": _TYPED_SEMANTIC_PATCH_MAX_PATH_DEPTH,
        },
        "repair_instructions": [
            "Return only the typed patch envelope, not the full packet.",
            "Copy base_payload_fingerprint exactly.",
            "Update only paths needed to resolve every local_validation_error.",
            "Preserve every unmentioned field byte-for-structure in the base payload.",
            (
                "Every update path is relative to the base payload root shown inside "
                "base_payload_excerpt. Its first component must be an actual "
                "top-level packet field, never a prompt-wrapper or excerpt-metadata "
                "label."
            ),
            "Use integer path components only for array indices.",
            "replacement_json must itself decode as one valid JSON value.",
            (
                "When several fields in one object must change, replace the "
                "smallest parent object that contains them in one update instead "
                "of spending one update per field."
            ),
            "Do not remove evidence boundaries or claim unexecuted verification.",
        ],
        "original_request": _compact_original_request(
            original_user_prompt,
            head_chars=600,
            tail_chars=1200,
        ),
    }
    payload["repair_instructions"].extend(
        _subsystem_priority_repair_instructions(repair_context)
    )
    if repair_context:
        payload["subsystem_repair_context"] = repair_context
    return (
        "Your previous JSON packet parsed, but failed local semantic validation. "
        "Return ONLY a compact typed patch envelope.\n\n"
        + json.dumps(payload, indent=2, default=str, ensure_ascii=False)
    )


def _apply_typed_semantic_patch(
    *,
    base_payload: Mapping[str, Any],
    expected_base_fingerprint: str,
    patch_envelope: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    list[list[str | int]],
    list[dict[str, Any]],
]:
    supplied_fingerprint = str(
        patch_envelope.get("base_payload_fingerprint", "") or ""
    )
    if not expected_base_fingerprint or supplied_fingerprint != expected_base_fingerprint:
        raise ValueError(
            "typed semantic patch base_payload_fingerprint does not match the "
            "lineage-bound base payload"
        )
    raw_updates = patch_envelope.get("updates", [])
    if not isinstance(raw_updates, list) or not raw_updates:
        raise ValueError("typed semantic patch must contain at least one update")
    if len(raw_updates) > _TYPED_SEMANTIC_PATCH_MAX_UPDATES:
        raise ValueError(
            "typed semantic patch exceeds the bounded update count "
            f"{_TYPED_SEMANTIC_PATCH_MAX_UPDATES}; received {len(raw_updates)}"
        )

    patched = deepcopy(dict(base_payload))
    applied_paths: list[list[str | int]] = []
    path_normalizations: list[dict[str, Any]] = []
    for update_index, raw_update in enumerate(raw_updates):
        if not isinstance(raw_update, Mapping):
            raise ValueError(
                f"typed semantic patch update {update_index} must be an object"
            )
        raw_path = raw_update.get("path", [])
        if not isinstance(raw_path, list) or not raw_path:
            raise ValueError(
                f"typed semantic patch update {update_index} must contain a path"
            )
        if len(raw_path) > _TYPED_SEMANTIC_PATCH_MAX_RAW_PATH_DEPTH:
            raise ValueError(
                f"typed semantic patch update {update_index} exceeds maximum raw path depth"
            )
        path: list[str | int] = []
        for component in raw_path:
            if isinstance(component, bool) or not isinstance(component, (str, int)):
                raise ValueError(
                    f"typed semantic patch update {update_index} has an invalid path component"
                )
            if isinstance(component, int) and component < 0:
                raise ValueError(
                    f"typed semantic patch update {update_index} has a negative array index"
                )
            if isinstance(component, str) and not component:
                raise ValueError(
                    f"typed semantic patch update {update_index} has an empty object key"
                )
            path.append(component)
        normalized_path, stripped_prefixes = (
            _normalize_typed_semantic_patch_path(
                base_payload=base_payload,
                path=path,
            )
        )
        if len(normalized_path) > _TYPED_SEMANTIC_PATCH_MAX_PATH_DEPTH:
            raise ValueError(
                f"typed semantic patch update {update_index} exceeds maximum path depth"
            )
        replacement_json = raw_update.get("replacement_json")
        if not isinstance(replacement_json, str):
            raise ValueError(
                f"typed semantic patch update {update_index} replacement_json must be a string"
            )
        try:
            replacement = json.loads(replacement_json)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"typed semantic patch update {update_index} replacement_json is invalid: {exc}"
            ) from exc
        _replace_typed_patch_path(
            patched,
            path=normalized_path,
            replacement=replacement,
        )
        applied_paths.append(normalized_path)
        if stripped_prefixes:
            path_normalizations.append(
                {
                    "update_index": update_index,
                    "stripped_prompt_wrapper_prefixes": stripped_prefixes,
                    "normalized_path": normalized_path,
                }
            )
    return patched, applied_paths, path_normalizations


def _normalize_typed_semantic_patch_path(
    *,
    base_payload: Mapping[str, Any],
    path: list[str | int],
) -> tuple[list[str | int], list[str]]:
    """Remove only non-payload prompt wrappers from an otherwise typed path."""

    normalized = list(path)
    stripped_prefixes: list[str] = []
    while (
        normalized
        and isinstance(normalized[0], str)
        and normalized[0] in _TYPED_SEMANTIC_PATCH_PROMPT_WRAPPER_KEYS
        and normalized[0] not in base_payload
    ):
        stripped_prefixes.append(str(normalized.pop(0)))
    if not normalized:
        raise ValueError(
            "typed semantic patch path contains only prompt-wrapper labels"
        )
    return normalized, stripped_prefixes


def _replace_typed_patch_path(
    payload: dict[str, Any],
    *,
    path: list[str | int],
    replacement: Any,
) -> None:
    parent: Any = payload
    for depth, component in enumerate(path[:-1]):
        if isinstance(parent, dict):
            if not isinstance(component, str) or component not in parent:
                raise ValueError(
                    "typed semantic patch path does not resolve at component "
                    f"{depth}: {component!r}"
                )
            parent = parent[component]
        elif isinstance(parent, list):
            if (
                not isinstance(component, int)
                or isinstance(component, bool)
                or component >= len(parent)
            ):
                raise ValueError(
                    "typed semantic patch array path does not resolve at component "
                    f"{depth}: {component!r}"
                )
            parent = parent[component]
        else:
            raise ValueError(
                "typed semantic patch path traverses a scalar at component "
                f"{depth}: {component!r}"
            )

    final_component = path[-1]
    if isinstance(parent, dict):
        if not isinstance(final_component, str):
            raise ValueError("typed semantic patch object replacement requires a string key")
        parent[final_component] = replacement
        return
    if isinstance(parent, list):
        if (
            not isinstance(final_component, int)
            or isinstance(final_component, bool)
            or final_component >= len(parent)
        ):
            raise ValueError(
                "typed semantic patch array replacement requires an existing index"
            )
        parent[final_component] = replacement
        return
    raise ValueError("typed semantic patch replacement parent is a scalar")


def _stable_payload_fingerprint(payload: Mapping[str, Any]) -> str:
    import hashlib

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _compact_patch_base_payload(
    payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )
    if len(serialized) <= 6000:
        return deepcopy(dict(payload)), {
            "truncated": False,
            "full_payload_chars": len(serialized),
            "excerpt_is_payload_root": True,
        }

    outline: dict[str, Any] = {}
    truncated_fields: list[dict[str, Any]] = []
    for key, value in payload.items():
        if isinstance(value, list):
            encoded = json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
                ensure_ascii=False,
            )
            outline[str(key)] = (
                deepcopy(value[:2])
                if len(encoded) <= 1200
                else [
                    _compact_patch_excerpt_leaf(item) for item in value[:2]
                ]
            )
            if len(value) > 2 or len(encoded) > 1200:
                truncated_fields.append(
                    {
                        "path": [str(key)],
                        "value_kind": "array",
                        "item_count": len(value),
                        "shown_items": min(2, len(value)),
                    }
                )
        elif isinstance(value, Mapping):
            encoded = json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
                ensure_ascii=False,
            )
            outline[str(key)] = (
                deepcopy(dict(value))
                if len(encoded) <= 1200
                else {
                    str(child): _compact_patch_excerpt_leaf(item)
                    for child, item in list(value.items())[:12]
                }
            )
            if len(encoded) > 1200:
                truncated_fields.append(
                    {
                        "path": [str(key)],
                        "value_kind": "object",
                        "object_keys": [str(child) for child in value.keys()],
                        "shown_keys": [
                            str(child) for child in list(value.keys())[:12]
                        ],
                    }
                )
        elif isinstance(value, str) and len(value) > 400:
            outline[str(key)] = value[:397] + "..."
            truncated_fields.append(
                {
                    "path": [str(key)],
                    "value_kind": "string",
                    "value_chars": len(value),
                    "shown_chars": 400,
                }
            )
        else:
            outline[str(key)] = deepcopy(value)
    return outline, {
        "truncated": True,
        "full_payload_chars": len(serialized),
        "excerpt_is_payload_root": True,
        "truncated_fields": truncated_fields,
    }


def _compact_patch_excerpt_leaf(value: Any, *, depth: int = 0) -> Any:
    if isinstance(value, str):
        return value if len(value) <= 240 else value[:237] + "..."
    if isinstance(value, list):
        if depth >= 3:
            return []
        return [
            _compact_patch_excerpt_leaf(item, depth=depth + 1)
            for item in value[:1]
        ]
    if isinstance(value, Mapping):
        if depth >= 3:
            return {}
        return {
            str(key): _compact_patch_excerpt_leaf(item, depth=depth + 1)
            for key, item in list(value.items())[:6]
        }
    return deepcopy(value)


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


def _repair_attempt_max_tokens(
    base_max_tokens: int,
    *,
    truncation_repair_mode: bool,
) -> int:
    base = max(1, int(base_max_tokens or 1))
    if not truncation_repair_mode:
        return base
    return min(max(base * 2, base + 1024), 8000)


def _typed_semantic_patch_fits_update_budget(errors: list[str]) -> bool:
    """Use patch mode only when the residual fits its bounded edit envelope."""

    return 0 < len(errors) <= _TYPED_SEMANTIC_PATCH_MAX_VALIDATION_ERRORS


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


def _repair_prompt(
    *,
    original_user_prompt: str,
    bad_response: str,
    errors: list[str],
    validation_label: str,
    truncation_detected: bool = False,
    repair_context: Mapping[str, Any] | None = None,
) -> str:
    original_request = (
        _compact_original_request(original_user_prompt, head_chars=1600, tail_chars=2600)
        if truncation_detected
        else _compact_original_request(original_user_prompt)
    )
    invalid_response_excerpt = (
        bad_response[:1200] if truncation_detected else bad_response[:2000]
    )
    repair_instructions = [
        "Return only a single JSON object.",
        "Rewrite the full JSON object from scratch; do not continue or patch the invalid response.",
        "Satisfy the original required_output_contract exactly.",
        "Keep all fields concise so the corrected JSON finishes within the response budget.",
        "Use exactly one item for required arrays unless the original contract explicitly requires more.",
        "Keep string fields under 240 characters and avoid multiline derivation essays.",
        "Preserve all evidence boundaries.",
        "Do not claim tool execution, simulation execution, production promotion, Lean proof, or kernel verification.",
        (
            "Treat local_validation_errors as hard constraints; do not repeat "
            "invalid identifiers, imports, claims, or statuses named in them "
            "unless the original contract gives an explicit verified repair path."
        ),
    ]
    repair_instructions.extend(_subsystem_priority_repair_instructions(repair_context))
    if truncation_detected:
        repair_instructions.insert(
            0,
            (
                "The previous response stopped because the provider hit the max "
                "token/output limit; produce a deliberately compact complete JSON "
                "object, not a longer explanation."
            ),
        )
        repair_instructions.insert(
            5,
            (
                "Use the minimum validator-satisfying number of rows for each "
                "array and keep mathematical strings symbolic but short."
            ),
        )
    payload = {
        "validation_label": validation_label,
        "local_validation_errors": errors,
        "truncation_detected": truncation_detected,
        "invalid_response_excerpt": invalid_response_excerpt,
        "repair_instructions": repair_instructions,
        "original_request": original_request,
    }
    if repair_context:
        payload["subsystem_repair_context"] = repair_context
    return (
        "Your previous response failed AI Statistician local validation. "
        "Repair the packet. Return ONLY corrected JSON.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )


def _subsystem_priority_repair_instructions(
    repair_context: Mapping[str, Any] | None,
) -> list[str]:
    if not isinstance(repair_context, Mapping):
        return []
    raw_instructions = repair_context.get("repair_prompt_priority_instructions", [])
    if isinstance(raw_instructions, str):
        candidates = [raw_instructions]
    elif isinstance(raw_instructions, list | tuple):
        candidates = [str(item) for item in raw_instructions]
    else:
        candidates = []
    return [
        instruction.strip()
        for instruction in candidates[:6]
        if instruction.strip()
    ]


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
