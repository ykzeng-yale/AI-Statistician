from __future__ import annotations

from copy import deepcopy
import json
import math
import re
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
RepairContextBuilder = Callable[..., Mapping[str, Any] | None]
RetryPromptBuilder = Callable[..., str]


_TYPED_SEMANTIC_PATCH_MAX_VALIDATION_ERRORS = 8
_TYPED_SEMANTIC_PATCH_MAX_UPDATES_PER_VALIDATION_ERROR = 4
_TYPED_SEMANTIC_PATCH_MAX_UPDATES = (
    _TYPED_SEMANTIC_PATCH_MAX_VALIDATION_ERRORS
    * _TYPED_SEMANTIC_PATCH_MAX_UPDATES_PER_VALIDATION_ERROR
)
_TYPED_SEMANTIC_PATCH_MAX_FOCUS_VALUE_CHARS = 4000
_TRUNCATION_REPAIR_MAX_TOKENS = 16000
_TYPED_SEMANTIC_PATCH_PROMPT_WRAPPER_KEYS = frozenset(
    {
        "base_payload_excerpt",
        "top_level_outline",
    }
)
_TYPED_SEMANTIC_PATCH_PATH_SCHEMA: dict[str, Any] = {
    "type": "array",
    "minItems": 1,
    "items": {
        "anyOf": [
            {"type": "string"},
            {"type": "integer", "minimum": 0},
        ]
    },
}
_TYPED_SEMANTIC_PATCH_DIRECT_REPLACEMENT_SCHEMA: dict[str, Any] = {
    "anyOf": [
        {"type": "string"},
        {"type": "number"},
        {"type": "boolean"},
        {"type": "null"},
    ]
}
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
                "anyOf": [
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["path", "replacement"],
                        "properties": {
                            "path": _TYPED_SEMANTIC_PATCH_PATH_SCHEMA,
                            "replacement": (
                                _TYPED_SEMANTIC_PATCH_DIRECT_REPLACEMENT_SCHEMA
                            ),
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["path", "replacement_json"],
                        "properties": {
                            "path": _TYPED_SEMANTIC_PATCH_PATH_SCHEMA,
                            "replacement_json": {"type": "string"},
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["path", "remove"],
                        "properties": {
                            "path": _TYPED_SEMANTIC_PATCH_PATH_SCHEMA,
                            "remove": {"type": "boolean", "const": True},
                        },
                    },
                ]
            },
        },
    },
}
_VALIDATION_ERROR_ARRAY_PATH_CHAIN = re.compile(
    r"\b[A-Za-z_][A-Za-z0-9_]*\[\d+\]"
    r"(?:(?:\s+|\.)[A-Za-z_][A-Za-z0-9_]*\[\d+\])*"
)
_VALIDATION_ERROR_ARRAY_PATH_SEGMENT = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]"
)
_TYPED_SEMANTIC_PATCH_NONLOCAL_SHAPE_ERROR_PATTERNS = (
    re.compile(r"\bcannot PASS\b", re.IGNORECASE),
    re.compile(r"\bcannot be consistent\b", re.IGNORECASE),
    re.compile(r"\bmust contain each required\b", re.IGNORECASE),
    re.compile(r"\bmust contain\b.*\bexactly once\b", re.IGNORECASE),
    re.compile(
        r"\bmust (?:have|contain|include) exactly \d+\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bexactly one\b.*\b(?:for each|for every)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\btransport must be an exact-key object\b", re.IGNORECASE),
    re.compile(
        r"\b(?:array|list|collection)\b.*\b(?:cardinality|length|size)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:too many|too few) (?:items|rows|entries|elements)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:minitems|maxitems)\b", re.IGNORECASE),
)


def _typed_semantic_patch_schema(*, max_updates: int) -> dict[str, Any]:
    schema = deepcopy(_TYPED_SEMANTIC_PATCH_SCHEMA)
    schema["properties"]["updates"]["maxItems"] = max(1, int(max_updates))
    return schema


def typed_semantic_patch_schema(*, max_updates: int) -> dict[str, Any]:
    """Return the bounded patch envelope schema for subsystem-owned revision loops."""

    return _typed_semantic_patch_schema(max_updates=max_updates)


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
    repair_context_builder: RepairContextBuilder | None = None,
    retry_prompt_builder: RetryPromptBuilder | None = None,
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
    last_invalid_packet: dict[str, Any] | None = None
    attempts = max(0, max_repair_attempts) + 1
    for attempt_index in range(attempts):
        truncation_repair_mode = bool(
            history and _history_row_indicates_truncation(history[-1])
        )
        request_max_tokens = _repair_attempt_max_tokens(
            request.max_tokens,
            truncation_repair_mode=truncation_repair_mode,
        )
        attempt_metadata = {
            **dict(request.metadata),
            "json_repair_attempt": attempt_index,
            "json_repair_max_attempts": max_repair_attempts,
            "json_repair_previous_attempt_truncated": truncation_repair_mode,
            "json_repair_truncation_repair_mode": truncation_repair_mode,
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
                    invalid_payload=(
                        deepcopy(dict(payload))
                        if isinstance(payload, Mapping)
                        else None
                    ),
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
            repair_context = dict(repair_context or {})
            if isinstance(payload, Mapping):
                focused_values = _validation_error_focus_values(
                    payload,
                    errors=last_errors,
                )
                if focused_values:
                    repair_context["validation_error_focus_values"] = focused_values
                focused_schemas = _validation_error_focus_schemas(
                    request.schema or {},
                    errors=last_errors,
                )
                if focused_schemas:
                    repair_context["validation_error_focus_schemas"] = focused_schemas
            truncation_detected = _response_indicates_truncation(
                response,
                request_max_tokens=request_max_tokens,
            )
            retry_prompt_kwargs = {
                "original_user_prompt": original_user_prompt,
                "bad_response": raw_text,
                "errors": last_errors,
                "validation_label": validation_label,
                "truncation_detected": truncation_detected,
                "repair_context": repair_context or None,
            }
            user_prompt = (
                retry_prompt_builder(**retry_prompt_kwargs)
                if retry_prompt_builder is not None
                else _repair_prompt(**retry_prompt_kwargs)
            )
    raise PacketValidationError(
        validation_label=validation_label,
        attempts=len(history),
        errors=last_errors,
        history=history,
        last_invalid_packet=last_invalid_packet,
    )


def _typed_semantic_patch_prompt(
    *,
    original_user_prompt: str,
    errors: list[str],
    validation_label: str,
    base_payload: Mapping[str, Any],
    base_payload_fingerprint: str,
    repair_context: Mapping[str, Any] | None = None,
    max_updates: int,
    source_schema: Mapping[str, Any] | None = None,
) -> str:
    base_payload_excerpt, base_payload_excerpt_metadata = (
        _compact_patch_base_payload(base_payload)
    )
    validation_error_focus_values = _validation_error_focus_values(
        base_payload,
        errors=errors,
    )
    validation_error_focus_schemas = _validation_error_focus_schemas(
        source_schema or {},
        errors=errors,
    )
    payload: dict[str, Any] = {
        "validation_label": validation_label,
        "local_validation_errors": errors,
        "base_payload_fingerprint": base_payload_fingerprint,
        "base_payload_excerpt": base_payload_excerpt,
        "base_payload_excerpt_metadata": base_payload_excerpt_metadata,
        "validation_error_focus_values": validation_error_focus_values,
        "patch_contract": {
            "base_payload_fingerprint": (
                "copy the supplied fingerprint exactly"
            ),
            "updates": [
                {
                    "path": ["top_level_field", 0, "nested_field"],
                    "replacement": "direct scalar value",
                },
                {
                    "path": ["top_level_field", 1, "nested_object"],
                    "replacement_json": "JSON-encoded complex object or array",
                },
                {
                    "path": ["top_level_array"],
                    "replacement_json": (
                        "JSON-encoded complete replacement array when adding, "
                        "removing, or reordering rows"
                    ),
                },
                {
                    "path": ["top_level_array", 2],
                    "remove": True,
                },
            ],
            "maximum_updates": max_updates,
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
            (
                "Use integer path components only for array indices. Every array "
                "index is zero-based; copy exact path arrays from "
                "subsystem_repair_context when they are supplied."
            ),
            (
                "Array-index paths may replace existing elements only. Never use "
                "an index equal to the current array length. To add, remove, or "
                "reorder rows, target the containing array field and provide the "
                "complete replacement array with replacement_json. For one existing "
                "array item, prefer remove=true at its exact index."
            ),
            (
                "Use replacement directly only for a string, number, boolean, or "
                "null; do not JSON-encode that scalar value."
            ),
            (
                "Use replacement_json for every object or array, including arrays "
                "of strings, and make "
                "that string decode as exactly one valid JSON value. Include exactly "
                "one of replacement, replacement_json, or remove in each update."
            ),
            (
                "Use remove=true only on an existing array-item path. Runtime removes "
                "exactly that model-selected item and then reruns the unchanged "
                "packet validator."
            ),
            (
                "When several fields in one object must change, replace the "
                "smallest parent object only when it is safely expressible as one "
                "replacement_json value; otherwise use bounded leaf updates."
            ),
            (
                "validation_error_focus_values shows exact current values at the "
                "original array indices named by local validation errors. Use those "
                "original paths even when base_payload_excerpt omits other rows."
            ),
            (
                "When validation_error_focus_values names an exact nested row, patch "
                "only the implicated leaf fields in that row. Do not replace its "
                "containing array unless the validator requires adding, removing, or "
                "reordering rows."
            ),
            (
                "validation_error_focus_schemas, when present, is the authoritative "
                "source schema for validator-named rows. Use its exact required keys, "
                "item shapes, enums, and cardinality constraints."
            ),
            "Do not remove evidence boundaries or claim unexecuted verification.",
        ],
        "original_request": _compact_original_request(
            original_user_prompt,
            head_chars=600,
            tail_chars=1200,
        ),
    }
    if validation_error_focus_schemas:
        payload["validation_error_focus_schemas"] = (
            validation_error_focus_schemas
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
    max_updates: int,
    allow_new_object_keys: bool = True,
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
    if len(raw_updates) > max_updates:
        raise ValueError(
            "typed semantic patch exceeds the bounded update count "
            f"{max_updates}; received {len(raw_updates)}"
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
        has_direct_replacement = "replacement" in raw_update
        has_json_replacement = "replacement_json" in raw_update
        has_remove = "remove" in raw_update
        if sum(
            (has_direct_replacement, has_json_replacement, has_remove)
        ) != 1:
            raise ValueError(
                f"typed semantic patch update {update_index} must contain exactly "
                "one of replacement, replacement_json, or remove"
            )
        if has_remove:
            if raw_update.get("remove") is not True:
                raise ValueError(
                    f"typed semantic patch update {update_index} remove must be true"
                )
            _remove_typed_patch_path(patched, path=normalized_path)
            replacement = None
        elif has_direct_replacement:
            replacement = raw_update.get("replacement")
            if not _is_typed_semantic_patch_direct_replacement(replacement):
                raise ValueError(
                    f"typed semantic patch update {update_index} replacement must "
                    "be a finite JSON scalar"
                )
            replacement = deepcopy(replacement)
        else:
            replacement_json = raw_update.get("replacement_json")
            if not isinstance(replacement_json, str):
                raise ValueError(
                    f"typed semantic patch update {update_index} replacement_json "
                    "must be a string"
                )
            try:
                replacement = json.loads(replacement_json)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"typed semantic patch update {update_index} replacement_json "
                    f"is invalid: {exc}"
                ) from exc
        if not has_remove:
            _replace_typed_patch_path(
                patched,
                path=normalized_path,
                replacement=replacement,
                allow_new_object_keys=allow_new_object_keys,
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


def apply_typed_semantic_patch(
    *,
    base_payload: Mapping[str, Any],
    expected_base_fingerprint: str,
    patch_envelope: Mapping[str, Any],
    max_updates: int,
    allow_new_object_keys: bool = True,
) -> tuple[
    dict[str, Any],
    list[list[str | int]],
    list[dict[str, Any]],
]:
    """Apply a lineage-bound typed patch without exposing mutable runtime metadata."""

    return _apply_typed_semantic_patch(
        base_payload=base_payload,
        expected_base_fingerprint=expected_base_fingerprint,
        patch_envelope=patch_envelope,
        max_updates=max_updates,
        allow_new_object_keys=allow_new_object_keys,
    )


def _is_typed_semantic_patch_direct_replacement(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False


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
    allow_new_object_keys: bool = True,
) -> None:
    parent: Any = payload
    for depth, component in enumerate(path[:-1]):
        if isinstance(parent, dict):
            if not isinstance(component, str) or component not in parent:
                available_keys = sorted(str(key) for key in parent)[:16]
                raise ValueError(
                    "typed semantic patch path does not resolve at component "
                    f"{depth}: {component!r}; full_path={path!r}; "
                    f"available_keys={available_keys!r}"
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
                    f"{depth}: {component!r}; full_path={path!r}; "
                    f"array_length={len(parent)}"
                )
            parent = parent[component]
        else:
            raise ValueError(
                "typed semantic patch path traverses a scalar at component "
                f"{depth}: {component!r}; full_path={path!r}"
            )

    final_component = path[-1]
    if isinstance(parent, dict):
        if not isinstance(final_component, str):
            raise ValueError("typed semantic patch object replacement requires a string key")
        if not allow_new_object_keys and final_component not in parent:
            available_keys = sorted(str(key) for key in parent)[:16]
            raise ValueError(
                "typed semantic patch may replace only an existing object key; "
                f"full_path={path!r}; available_keys={available_keys!r}"
            )
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


def _remove_typed_patch_path(
    payload: dict[str, Any],
    *,
    path: list[str | int],
) -> None:
    parent: Any = payload
    for depth, component in enumerate(path[:-1]):
        if isinstance(parent, dict):
            if not isinstance(component, str) or component not in parent:
                available_keys = sorted(str(key) for key in parent)[:16]
                raise ValueError(
                    "typed semantic patch remove path does not resolve at component "
                    f"{depth}: {component!r}; full_path={path!r}; "
                    f"available_keys={available_keys!r}"
                )
            parent = parent[component]
        elif isinstance(parent, list):
            if (
                not isinstance(component, int)
                or isinstance(component, bool)
                or component >= len(parent)
            ):
                raise ValueError(
                    "typed semantic patch remove array path does not resolve at "
                    f"component {depth}: {component!r}; full_path={path!r}; "
                    f"array_length={len(parent)}"
                )
            parent = parent[component]
        else:
            raise ValueError(
                "typed semantic patch remove path traverses a scalar at component "
                f"{depth}: {component!r}; full_path={path!r}"
            )

    final_component = path[-1]
    if not isinstance(parent, list):
        raise ValueError(
            "typed semantic patch remove requires an existing array-item path"
        )
    if (
        not isinstance(final_component, int)
        or isinstance(final_component, bool)
        or final_component >= len(parent)
    ):
        raise ValueError(
            "typed semantic patch remove requires an existing array index"
        )
    parent.pop(final_component)


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


def typed_semantic_patch_payload_fingerprint(payload: Mapping[str, Any]) -> str:
    """Fingerprint the exact base payload expected by a typed patch envelope."""

    return _stable_payload_fingerprint(payload)


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


def _validation_error_focus_values(
    payload: Mapping[str, Any],
    *,
    errors: list[str],
) -> list[dict[str, Any]]:
    """Expose exact rows named by validators without expanding the whole packet."""

    focused: list[dict[str, Any]] = []
    seen: set[tuple[str | int, ...]] = set()
    for path in _validation_error_array_paths(errors):
        identity = tuple(path)
        if identity in seen:
            continue
        row = _value_at_array_path(payload, path)
        if row is _MISSING_ARRAY_PATH_VALUE:
            continue
        seen.add(identity)
        row = deepcopy(row)
        encoded = json.dumps(
            row,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
        value_truncated = len(encoded) > _TYPED_SEMANTIC_PATCH_MAX_FOCUS_VALUE_CHARS
        focused.append(
            {
                "path": list(path),
                "value": (
                    _compact_patch_excerpt_leaf(row)
                    if value_truncated
                    else row
                ),
                "value_truncated": value_truncated,
            }
        )
        if len(focused) >= _TYPED_SEMANTIC_PATCH_MAX_VALIDATION_ERRORS:
            return focused
    return focused


def _validation_error_focus_schemas(
    schema: Mapping[str, Any],
    *,
    errors: list[str],
) -> list[dict[str, Any]]:
    """Expose bounded source schemas for validator-named nested array rows."""

    focused: list[dict[str, Any]] = []
    seen: set[tuple[str | int, ...]] = set()
    for path in _validation_error_array_paths(errors):
        identity = tuple(path)
        if identity in seen:
            continue
        item_schema = _schema_at_array_path(schema, path)
        if not item_schema:
            continue
        encoded = json.dumps(
            item_schema,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
        if len(encoded) > _TYPED_SEMANTIC_PATCH_MAX_FOCUS_VALUE_CHARS:
            continue
        seen.add(identity)
        focused.append(
            {
                "path_pattern": [
                    "<array_index>" if isinstance(component, int) else component
                    for component in path
                ],
                "expected_item_schema": deepcopy(dict(item_schema)),
            }
        )
        if len(focused) >= _TYPED_SEMANTIC_PATCH_MAX_VALIDATION_ERRORS:
            return focused
    return focused


_MISSING_ARRAY_PATH_VALUE = object()


def _validation_error_array_paths(
    errors: list[str],
) -> list[list[str | int]]:
    paths: list[list[str | int]] = []
    seen: set[tuple[str | int, ...]] = set()
    for error in errors:
        for chain in _VALIDATION_ERROR_ARRAY_PATH_CHAIN.findall(str(error)):
            path: list[str | int] = []
            for field, raw_index in _VALIDATION_ERROR_ARRAY_PATH_SEGMENT.findall(chain):
                path.extend((field, int(raw_index)))
            identity = tuple(path)
            if path and identity not in seen:
                seen.add(identity)
                paths.append(path)
    return paths


def _value_at_array_path(
    payload: Mapping[str, Any],
    path: list[str | int],
) -> Any:
    current: Any = payload
    for component in path:
        if isinstance(component, str):
            if not isinstance(current, Mapping) or component not in current:
                return _MISSING_ARRAY_PATH_VALUE
            current = current[component]
        else:
            if (
                not isinstance(current, (list, tuple))
                or component < 0
                or component >= len(current)
            ):
                return _MISSING_ARRAY_PATH_VALUE
            current = current[component]
    return current


def _schema_at_array_path(
    schema: Mapping[str, Any],
    path: list[str | int],
) -> Mapping[str, Any]:
    current: Any = schema
    for component in path:
        if isinstance(component, str):
            properties = current.get("properties", {}) if isinstance(current, Mapping) else {}
            if not isinstance(properties, Mapping):
                return {}
            current = properties.get(component, {})
        else:
            if not isinstance(current, Mapping):
                return {}
            current = current.get("items", {})
        if not isinstance(current, Mapping) or not current:
            return {}
    return current


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
    return max(
        base,
        min(max(base * 2, base + 1024), _TRUNCATION_REPAIR_MAX_TOKENS),
    )


def _typed_semantic_patch_fits_update_budget(errors: list[str]) -> bool:
    """Use patch mode only when the residual fits its bounded edit envelope."""

    return (
        0 < len(errors) <= _TYPED_SEMANTIC_PATCH_MAX_VALIDATION_ERRORS
        and not any(
            pattern.search(str(error))
            for error in errors
            for pattern in _TYPED_SEMANTIC_PATCH_NONLOCAL_SHAPE_ERROR_PATTERNS
        )
    )


def _typed_semantic_patch_update_budget(errors: list[str]) -> int:
    return min(
        _TYPED_SEMANTIC_PATCH_MAX_UPDATES,
        max(1, len(errors))
        * _TYPED_SEMANTIC_PATCH_MAX_UPDATES_PER_VALIDATION_ERROR,
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
        bad_response[:4000] if truncation_detected else bad_response[:20000]
    )
    repair_instructions = [
        "Return only a single JSON object.",
        (
            "Rewrite the full JSON object from scratch using the original request, "
            "schema, prior response, and validator feedback; do not emit a patch."
        ),
        "Satisfy the original required_output_contract exactly.",
        "Resolve every local_validation_errors row in the regenerated object.",
        "Preserve valid mathematical and coding decisions unless an error implicates them.",
        "Preserve all evidence boundaries.",
        "Do not claim tool execution, simulation execution, production promotion, Lean proof, or kernel verification.",
        (
            "Treat local_validation_errors as hard constraints; do not repeat "
            "invalid identifiers, imports, claims, or statuses named in them "
            "unless the original contract gives an explicit verified repair path."
        ),
    ]
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
                "array and keep the regenerated packet compact enough to finish."
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
