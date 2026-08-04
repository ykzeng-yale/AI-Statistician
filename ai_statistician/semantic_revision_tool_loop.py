from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .llm_json_repair import (
    PacketValidationError,
    apply_typed_semantic_patch,
    typed_semantic_patch_payload_fingerprint,
)
from .model_backend import (
    ClientToolDefinition,
    ClientToolTurnRequest,
    GeneratorResponse,
)


FeedbackDecisionValidator = Callable[..., list[str]]
PacketBuilder = Callable[
    [Mapping[str, Any], GeneratorResponse, str],
    dict[str, Any],
]
PacketValidator = Callable[[Mapping[str, Any]], list[str]]


@dataclass(frozen=True)
class SemanticRevisionToolLoopResult:
    packet: Mapping[str, Any]
    evidence: Mapping[str, Any]


def run_semantic_revision_tool_loop(
    *,
    provider: Any,
    system_prompt: str,
    user_prompt: str,
    model: str,
    model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_updates: int,
    max_no_progress_turns: int,
    base_payload: Mapping[str, Any],
    base_fingerprint: str,
    feedback_decision_contract: Mapping[str, Any],
    validate_feedback_decisions: FeedbackDecisionValidator,
    build_packet: PacketBuilder,
    validate_packet: PacketValidator,
    validation_label: str,
    evidence_status: str,
    request_metadata: Mapping[str, Any] | None = None,
) -> SemanticRevisionToolLoopResult:
    """Run a reusable native-value semantic revision loop on one immutable parent."""

    if max_updates < 1:
        raise ValueError("semantic revision requires a positive update budget")
    frozen_base = deepcopy(dict(base_payload))
    decision_bindings = {
        int(row.get("finding_index", -1)): deepcopy(dict(row))
        for row in feedback_decision_contract.get("decision_bindings", []) or []
        if isinstance(row, Mapping)
        and not isinstance(row.get("finding_index"), bool)
        and isinstance(row.get("finding_index"), int)
        and int(row.get("finding_index", -1)) >= 0
        and str(row.get("decision_key", "") or "")
    }
    state: dict[str, Any] = {"feedback_decisions": {}, "updates": []}
    tools = _semantic_revision_tools(
        valid_sections=sorted(str(key) for key in frozen_base),
        finding_indices=sorted(decision_bindings),
    )
    runtime_response = GeneratorResponse(
        text="",
        provider=str(getattr(provider, "provider_name", "") or ""),
        model=model,
        metadata={
            "client_tool_transport": True,
            "tools_executed_by_backend": False,
        },
    )

    def candidate_payload(
        updates: Sequence[Mapping[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], list[list[str | int]]]:
        relative_updates = [
            deepcopy(dict(row))
            for row in (state["updates"] if updates is None else updates)
            if isinstance(row, Mapping)
        ]
        if not relative_updates:
            return deepcopy(frozen_base), []
        canonical_updates = [
            {
                "path": [
                    str(row.get("section", "") or ""),
                    *list(row.get("relative_path", []) or []),
                ],
                "replacement_json": row.get("replacement_json"),
            }
            for row in relative_updates
        ]
        patched, applied_paths, normalizations = apply_typed_semantic_patch(
            base_payload=frozen_base,
            expected_base_fingerprint=base_fingerprint,
            patch_envelope={
                "base_payload_fingerprint": base_fingerprint,
                "updates": canonical_updates,
            },
            max_updates=max_updates,
            allow_new_object_keys=False,
        )
        if normalizations:
            raise ClientToolInputError(
                "semantic revision paths may not require runtime normalization"
            )
        return patched, applied_paths

    def candidate_packet_and_errors() -> tuple[dict[str, Any] | None, list[str]]:
        if not state["updates"]:
            return None, ["semantic revision must apply at least one update"]
        try:
            raw_payload = {
                "feedback_decisions": deepcopy(state["feedback_decisions"]),
                "updates": deepcopy(state["updates"]),
            }
            raw_text = _json_text(raw_payload)
            packet = build_packet(raw_payload, runtime_response, raw_text)
            return packet, validate_packet(packet)
        except (KeyError, TypeError, ValueError) as exc:
            return None, [f"{type(exc).__name__}: {exc}"]
        except Exception as exc:
            return None, [
                f"{type(exc).__name__}: internal packet assembly detail withheld"
            ]

    def execute_unchecked(call, context):
        del context
        tool_input = dict(call.input)
        if call.name == "record_feedback_decision":
            required = {
                "finding_index",
                "selected_resolution",
                "rationale",
                "rejected_alternatives",
            }
            if set(tool_input) != required:
                raise ClientToolInputError(
                    "feedback-decision input must contain exactly the required fields"
                )
            finding_index = tool_input.get("finding_index")
            if isinstance(finding_index, bool) or not isinstance(
                finding_index, int
            ):
                raise ClientToolInputError("finding_index must be an integer")
            binding = decision_bindings.get(finding_index)
            if binding is None:
                raise ClientToolInputError(
                    "finding_index is not present in the frozen contract"
                )
            decision_key = str(binding.get("decision_key", "") or "")
            decision = {
                "selected_resolution": tool_input.get("selected_resolution"),
                "rationale": tool_input.get("rationale"),
                "rejected_alternatives": deepcopy(
                    tool_input.get("rejected_alternatives")
                ),
            }
            errors = validate_feedback_decisions(
                {decision_key: decision},
                decision_contract={"decision_bindings": [binding]},
            )
            if errors:
                return ClientToolExecutionResult(
                    content={"ok": False, "validation_errors": errors},
                    is_error=True,
                    observation_key="decision_error:" + stable_hash(errors),
                )
            previous = state["feedback_decisions"].get(decision_key)
            state["feedback_decisions"][decision_key] = deepcopy(decision)
            changed = previous != decision
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "finding_index": finding_index,
                    "recorded_decisions": len(state["feedback_decisions"]),
                    "required_decisions": len(decision_bindings),
                },
                state_changed=changed,
                observation_key=(
                    "decision:"
                    + str(finding_index)
                    + ":"
                    + stable_hash(decision)
                ),
            )
        if call.name == "replace_artifact_value":
            if set(tool_input) != {"section", "relative_path", "replacement"}:
                raise ClientToolInputError(
                    "replace input requires section, relative_path, and replacement"
                )
            if len(state["updates"]) >= max_updates:
                raise ClientToolInputError("semantic revision update budget is exhausted")
            section, relative_path = _validated_relative_path(
                tool_input,
                base_payload=frozen_base,
            )
            before, _ = candidate_payload()
            existing_value = _artifact_value_at_path(
                before,
                section=section,
                relative_path=relative_path,
            )
            replacement = tool_input.get("replacement")
            _validate_replacement_shape(
                existing_value,
                replacement,
                full_path=[section, *relative_path],
            )
            try:
                replacement_json = json.dumps(
                    replacement,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                )
            except (TypeError, ValueError) as exc:
                raise ClientToolInputError(
                    "replacement must be one finite JSON value"
                ) from exc
            update = {
                "section": section,
                "relative_path": relative_path,
                "replacement_json": replacement_json,
            }
            candidate_updates = [*state["updates"], update]
            after, applied_paths = candidate_payload(candidate_updates)
            changed = (
                typed_semantic_patch_payload_fingerprint(before)
                != typed_semantic_patch_payload_fingerprint(after)
            )
            if changed:
                state["updates"].append(update)
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "applied": changed,
                    "full_path": [section, *relative_path],
                    "successful_updates": len(state["updates"]),
                    "maximum_updates": max_updates,
                    "remaining_updates": max_updates - len(state["updates"]),
                    "candidate_fingerprint": (
                        typed_semantic_patch_payload_fingerprint(after)
                    ),
                    "applied_paths": applied_paths[-1:] if changed else [],
                },
                state_changed=changed,
                observation_key="replace:" + stable_hash([update, changed]),
            )
        if call.name == "append_artifact_list_item":
            if set(tool_input) != {"section", "relative_path", "item"}:
                raise ClientToolInputError(
                    "append input requires section, relative_path, and item"
                )
            if len(state["updates"]) >= max_updates:
                raise ClientToolInputError(
                    "semantic revision update budget is exhausted; validate and submit "
                    "the current candidate or revise an earlier edit"
                )
            section, relative_path = _validated_relative_path(
                tool_input,
                base_payload=frozen_base,
            )
            before, _ = candidate_payload()
            existing_value = _artifact_value_at_path(
                before,
                section=section,
                relative_path=relative_path,
            )
            if not isinstance(existing_value, list):
                raise ClientToolInputError(
                    "append_artifact_list_item requires an existing array path; "
                    f"full_path={[section, *relative_path]!r} resolves to "
                    f"{_json_value_kind(existing_value)}"
                )
            item = deepcopy(tool_input.get("item"))
            _validate_append_item_shape(
                existing_value,
                item,
                full_path=[section, *relative_path],
            )
            appended = [*deepcopy(existing_value), item]
            try:
                replacement_json = json.dumps(
                    appended,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                )
            except (TypeError, ValueError) as exc:
                raise ClientToolInputError(
                    "item must be one finite native JSON value"
                ) from exc
            update = {
                "section": section,
                "relative_path": relative_path,
                "replacement_json": replacement_json,
            }
            candidate_updates = [*state["updates"], update]
            after, applied_paths = candidate_payload(candidate_updates)
            state["updates"].append(update)
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "applied": True,
                    "full_path": [section, *relative_path],
                    "appended_index": len(existing_value),
                    "successful_updates": len(state["updates"]),
                    "maximum_updates": max_updates,
                    "remaining_updates": max_updates - len(state["updates"]),
                    "candidate_fingerprint": (
                        typed_semantic_patch_payload_fingerprint(after)
                    ),
                    "applied_paths": applied_paths[-1:],
                },
                state_changed=True,
                observation_key="append:" + stable_hash(update),
            )
        if call.name == "submit_revision":
            if tool_input:
                raise ClientToolInputError("submit_revision takes an empty object")
            packet, errors = candidate_packet_and_errors()
            content = {
                "ok": not errors,
                "validation_errors": errors[:12],
                "n_validation_errors": len(errors),
                "recorded_decisions": len(state["feedback_decisions"]),
                "required_decisions": len(decision_bindings),
                "successful_updates": len(state["updates"]),
            }
            observation_key = "validation:" + stable_hash(content)
            if not errors:
                return ClientToolExecutionResult(
                    content={**content, "submitted": True},
                    terminal=True,
                    terminal_payload={
                        "feedback_decisions": deepcopy(
                            state["feedback_decisions"]
                        ),
                        "updates": deepcopy(state["updates"]),
                    },
                    observation_key=observation_key,
                )
            return ClientToolExecutionResult(
                content=content,
                is_error=True,
                observation_key=observation_key,
            )
        raise ClientToolInputError("unsupported semantic-revision client tool")

    def execute_tool(call, context):
        try:
            return execute_unchecked(call, context)
        except ClientToolInputError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise ClientToolInputError(str(exc)) from exc

    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=({"role": "user", "content": user_prompt},),
        tools=tools,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tool_choice="any",
        metadata={
            **dict(request_metadata or {}),
            "model_tier": model_tier,
            "semantic_revision_parent_fingerprint": base_fingerprint,
            "evidence_status": evidence_status,
        },
    )
    max_tool_calls = max_updates + len(decision_bindings) + max_turns
    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
        )
    except ClientToolLoopError as exc:
        last_packet, last_errors = candidate_packet_and_errors()
        if (
            exc.reason == "global client-tool turn budget exhausted"
            and last_packet is not None
            and not last_errors
        ):
            evidence = _semantic_revision_tool_loop_evidence(
                turns=exc.turns,
                tool_calls=exc.tool_calls,
                max_turns=max_turns,
                max_tool_calls=max_tool_calls,
                max_no_progress_turns=max_no_progress_turns,
                tools=tools,
                history=exc.history,
                transcript_fingerprint=exc.transcript_fingerprint,
                provider=exc.provider,
                model=exc.model,
                response_metadata=exc.final_response_metadata,
                provider_usage=exc.provider_usage,
                evidence_status=evidence_status,
                model_explicit_submit=False,
                budget_exhausted=True,
                runtime_executed_tool_calls=(
                    exc.runtime_executed_tool_calls
                ),
            )
            return SemanticRevisionToolLoopResult(
                packet=last_packet,
                evidence=evidence,
            )
        raise PacketValidationError(
            validation_label=validation_label,
            attempts=exc.turns,
            errors=[exc.reason, *last_errors],
            history=[deepcopy(dict(row)) for row in exc.history],
            last_invalid_packet=last_packet,
        ) from exc

    raw_text = _json_text(
        {
            "transcript_fingerprint": loop.transcript_fingerprint,
            "terminal_payload": loop.terminal_payload,
        }
    )
    response = GeneratorResponse(
        text=raw_text,
        provider=loop.provider,
        model=loop.model,
        metadata=deepcopy(dict(loop.final_response_metadata)),
    )
    packet = build_packet(loop.terminal_payload, response, raw_text)
    errors = validate_packet(packet)
    if errors:
        raise PacketValidationError(
            validation_label=validation_label,
            attempts=loop.turns,
            errors=errors,
            history=[deepcopy(dict(row)) for row in loop.history],
            last_invalid_packet=packet,
        )
    evidence = _semantic_revision_tool_loop_evidence(
        turns=loop.turns,
        tool_calls=loop.tool_calls,
        max_turns=max_turns,
        max_tool_calls=max_tool_calls,
        max_no_progress_turns=max_no_progress_turns,
        tools=tools,
        history=loop.history,
        transcript_fingerprint=loop.transcript_fingerprint,
        provider=loop.provider,
        model=loop.model,
        response_metadata=loop.final_response_metadata,
        provider_usage=loop.provider_usage,
        evidence_status=evidence_status,
        model_explicit_submit=True,
        budget_exhausted=False,
        runtime_executed_tool_calls=loop.runtime_executed_tool_calls,
    )
    return SemanticRevisionToolLoopResult(packet=packet, evidence=evidence)


def _semantic_revision_tool_loop_evidence(
    *,
    turns: int,
    tool_calls: int,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    tools: Sequence[ClientToolDefinition],
    history: Sequence[Mapping[str, Any]],
    transcript_fingerprint: str,
    provider: str,
    model: str,
    response_metadata: Mapping[str, Any],
    provider_usage: Mapping[str, int],
    evidence_status: str,
    model_explicit_submit: bool,
    budget_exhausted: bool,
    runtime_executed_tool_calls: int,
) -> dict[str, Any]:
    return {
        "artifact_kind": "SemanticRevisionClientToolLoopEvidence",
        "transport": "native_client_tools",
        "provider": provider,
        "model": model,
        "turns": turns,
        "tool_calls": tool_calls,
        "runtime_executed_tool_calls": runtime_executed_tool_calls,
        "max_turns": max_turns,
        "max_tool_calls": max_tool_calls,
        "max_no_progress_turns": max_no_progress_turns,
        "tool_names": [tool.name for tool in tools],
        "history": [deepcopy(dict(row)) for row in history],
        "transcript_fingerprint": transcript_fingerprint,
        "handoff_mode": (
            "model_submit"
            if model_explicit_submit
            else "turn_budget_validated_candidate"
        ),
        "model_explicit_submit": model_explicit_submit,
        "explicit_submit_locally_valid": model_explicit_submit,
        "budget_exhausted": budget_exhausted,
        "local_candidate_validation_passed": True,
        "tools_executed_by_runtime": bool(runtime_executed_tool_calls > 0),
        "tools_executed_by_backend": bool(
            response_metadata.get("tools_executed_by_backend", False)
        ),
        "provider_capability_fallback_count": int(
            response_metadata.get("provider_capability_fallback_count", 0)
            or 0
        ),
        "provider_usage": dict(provider_usage),
        "identity_binding": "finding_index_to_runtime_decision_key",
        "runtime_selected_semantics": False,
        "independent_acceptance_required": True,
        "evidence_status": evidence_status,
        "kernel_verified": False,
    }


def _semantic_revision_tools(
    *,
    valid_sections: list[str],
    finding_indices: list[int],
) -> tuple[ClientToolDefinition, ...]:
    tools: list[ClientToolDefinition] = []
    if finding_indices:
        tools.append(
            ClientToolDefinition(
                name="record_feedback_decision",
                description=(
                    "Record the model's semantic resolution for one runtime-listed "
                    "review finding."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "finding_index",
                        "selected_resolution",
                        "rationale",
                        "rejected_alternatives",
                    ],
                    "properties": {
                        "finding_index": {
                            "type": "integer",
                            "enum": finding_indices,
                        },
                        "selected_resolution": {"type": "string", "minLength": 1},
                        "rationale": {"type": "string", "minLength": 1},
                        "rejected_alternatives": {
                            "type": "array",
                            "maxItems": 5,
                            "items": {"type": "string", "minLength": 1},
                        },
                    },
                },
            )
        )
    path_properties = {
        "section": {"type": "string", "enum": valid_sections},
        "relative_path": {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string", "minLength": 1},
                    {"type": "integer", "minimum": 0},
                ]
            },
        },
    }
    tools.extend(
        [
            ClientToolDefinition(
                name="replace_artifact_value",
                description=(
                    "Replace one existing section-relative artifact value with a "
                    "native JSON value of the same structural kind. Use the append "
                    "tool when adding a row to an existing list."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["section", "relative_path", "replacement"],
                    "properties": {
                        **deepcopy(path_properties),
                        "replacement": {},
                    },
                },
            ),
            ClientToolDefinition(
                name="append_artifact_list_item",
                description=(
                    "Append one model-authored native JSON item to an existing "
                    "section-relative list while preserving the parent artifact."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["section", "relative_path", "item"],
                    "properties": {
                        **deepcopy(path_properties),
                        "item": {},
                    },
                },
            ),
            ClientToolDefinition(
                name="submit_revision",
                description=(
                    "Run the unchanged local validators and submit only on success. "
                    "This must be the final tool call in the turn."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {},
                },
                terminal=True,
            ),
        ]
    )
    return tuple(tools)


def _validated_relative_path(
    tool_input: Mapping[str, Any],
    *,
    base_payload: Mapping[str, Any],
) -> tuple[str, list[str | int]]:
    section = tool_input.get("section")
    relative_path = tool_input.get("relative_path")
    if not isinstance(section, str) or section not in base_payload:
        raise ClientToolInputError(
            "section must name one existing top-level artifact value"
        )
    if not isinstance(relative_path, list):
        raise ClientToolInputError("relative_path must be an array")
    path: list[str | int] = []
    for component in relative_path:
        if isinstance(component, bool) or not isinstance(component, (str, int)):
            raise ClientToolInputError("relative_path has an invalid component")
        if isinstance(component, int) and component < 0:
            raise ClientToolInputError("relative_path has a negative index")
        if isinstance(component, str) and not component:
            raise ClientToolInputError("relative_path has an empty key")
        path.append(component)
    return section, path


def _artifact_value_at_path(
    payload: Mapping[str, Any],
    *,
    section: str,
    relative_path: Sequence[str | int],
) -> Any:
    current: Any = payload[section]
    traversed: list[str | int] = [section]
    for component in relative_path:
        if isinstance(component, int):
            if not isinstance(current, list) or component >= len(current):
                raise ClientToolInputError(
                    f"full_path={traversed + [component]!r} does not resolve to an "
                    "existing array item"
                )
            current = current[component]
        else:
            if not isinstance(current, Mapping) or component not in current:
                available = (
                    sorted(str(key) for key in current)
                    if isinstance(current, Mapping)
                    else []
                )
                raise ClientToolInputError(
                    f"full_path={traversed + [component]!r} does not resolve to an "
                    f"existing object value; available_keys={available!r}"
                )
            current = current[component]
        traversed.append(component)
    return current


def _json_value_kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, Mapping):
        return "object"
    return type(value).__name__


def _validate_replacement_shape(
    existing_value: Any,
    replacement: Any,
    *,
    full_path: Sequence[str | int],
) -> None:
    existing_kind = _json_value_kind(existing_value)
    replacement_kind = _json_value_kind(replacement)
    if "null" in {existing_kind, replacement_kind} or existing_kind == replacement_kind:
        return
    raise ClientToolInputError(
        "replace_artifact_value cannot change the JSON structural kind at "
        f"full_path={list(full_path)!r}: existing={existing_kind}, "
        f"replacement={replacement_kind}. Replace it with a {existing_kind} value, "
        "or use append_artifact_list_item on the parent array when adding a row."
    )


def _validate_append_item_shape(
    existing_items: Sequence[Any],
    item: Any,
    *,
    full_path: Sequence[str | int],
) -> None:
    observed_kinds = {
        _json_value_kind(existing)
        for existing in existing_items
        if existing is not None
    }
    item_kind = _json_value_kind(item)
    if len(observed_kinds) == 1 and item is not None:
        expected_kind = next(iter(observed_kinds))
        if item_kind != expected_kind:
            raise ClientToolInputError(
                "append_artifact_list_item must preserve the observed list item kind "
                f"at full_path={list(full_path)!r}: expected={expected_kind}, "
                f"item={item_kind}"
            )
    object_rows = [row for row in existing_items if isinstance(row, Mapping)]
    if not object_rows or len(object_rows) != len(existing_items) or not isinstance(item, Mapping):
        return
    common_keys = set(object_rows[0])
    for row in object_rows[1:]:
        common_keys.intersection_update(row)
    missing_keys = sorted(str(key) for key in common_keys if key not in item)
    if missing_keys:
        raise ClientToolInputError(
            "appended object is missing fields shared by existing sibling rows at "
            f"full_path={list(full_path)!r}: missing_keys={missing_keys!r}"
        )
    for key in sorted(common_keys, key=str):
        sibling_kinds = {
            _json_value_kind(row[key])
            for row in object_rows
            if row.get(key) is not None
        }
        if len(sibling_kinds) != 1 or item.get(key) is None:
            continue
        expected_kind = next(iter(sibling_kinds))
        observed_kind = _json_value_kind(item[key])
        if observed_kind != expected_kind:
            raise ClientToolInputError(
                "appended object field must preserve the observed sibling field kind "
                f"at full_path={list(full_path) + [str(key)]!r}: "
                f"expected={expected_kind}, item={observed_kind}"
            )


def _json_text(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )
