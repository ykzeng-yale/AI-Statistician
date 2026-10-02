from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from dataclasses import replace

import pytest

from ai_statistician.client_tool_loop import (
    CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY,
    CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY,
    CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    ClientToolRuntimeError,
    apply_model_exact_text_edits,
    model_exact_text_edit_json_schema,
    model_exact_text_edits_json_schema,
    load_client_tool_session,
    persist_client_tool_session,
    resume_client_tool_session_from_checkpoint,
    run_bounded_client_tool_loop,
    workspace_history_tool,
)
from ai_statistician import client_tool_loop
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
    LiveGeneratorTimeoutError,
)


class ScriptedToolTurnBackend:
    provider_name = "scripted_tool_turn"

    def __init__(
        self,
        responses: list[ClientToolTurnResponse | Exception],
    ) -> None:
        self.responses = list(responses)
        self.requests: list[ClientToolTurnRequest] = []

    def generate_client_tool_turn(
        self,
        request: ClientToolTurnRequest,
    ) -> ClientToolTurnResponse:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("ScriptedToolTurnBackend exhausted")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _tool(name: str, *, terminal: bool = False) -> ClientToolDefinition:
    return ClientToolDefinition(
        name=name,
        description=f"Execute {name}.",
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
        terminal=terminal,
    )


def _response(
    *calls: ClientToolCall,
    text: str = "",
    stop_reason: str = "tool_use",
) -> ClientToolTurnResponse:
    blocks = []
    if text:
        blocks.append({"type": "text", "text": text})
    blocks.extend(
        {
            "type": "tool_use",
            "id": call.call_id,
            "name": call.name,
            "input": dict(call.input),
        }
        for call in calls
    )
    return ClientToolTurnResponse(
        content_blocks=tuple(blocks),
        tool_calls=tuple(calls),
        text=text,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        metadata={
            "client_tool_transport": True,
            "tools_executed_by_backend": False,
            "provider_stop_reason": stop_reason,
            "provider_usage": {"input_tokens": 11, "output_tokens": 3},
        },
    )


def _request() -> ClientToolTurnRequest:
    return ClientToolTurnRequest(
        system_prompt="Use runtime tools.",
        messages=({"role": "user", "content": "Repair the artifact."},),
        tools=(
            _tool("edit"),
            _tool("check"),
            _tool("submit", terminal=True),
        ),
        model="claude-haiku-4-5-20251001",
        metadata={
            "model_tier": "haiku",
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: "auth:q1:v1",
        },
    )


def _history_request():
    request = _request()
    return replace(request, tools=(*request.tools, workspace_history_tool()))


def _history_checkpoint(tmp_path, request, content):
    backend = ScriptedToolTurnBackend([
        _response(ClientToolCall(call_id="opaque-check", name="check", input={})),
        _response(ClientToolCall(call_id="save", name="submit", input={})),
    ])

    def execute(call, _context):
        if call.name == "check":
            return ClientToolExecutionResult(content=content, is_error=True)
        return ClientToolExecutionResult(content={"saved": True}, terminal=True,
                                         terminal_payload={"disposition": "checkpoint"})

    result = run_bounded_client_tool_loop(
        backend=backend, request=request, execute_tool=execute,
        max_turns=2, max_tool_calls=2, max_no_progress_turns=2,
        session_dir=tmp_path, session_id="history-owner",
    )
    ref = persist_client_tool_session(
        session_dir=tmp_path, session_id="history-owner", request=request,
        messages=result.messages, observation_refs=result.observation_refs,
        durable_state_identity="checkpoint",
    )
    return ref, result, backend


@pytest.mark.parametrize("opaque_content", [
    "opaque prefix\n" + "unresolved\n" * 10000 + "original-tail-37",
    "\u03b1 = \u03b2 + \u03b3\n" * 10000 + "original-tail-61",
    {"observations": ["opaque unresolved"] * 10000, "tail": "original-tail-83"},
])
def test_exact_oversized_observation_survives_two_context_windows(tmp_path, opaque_content):
    request = _history_request()
    first, result, backend = _history_checkpoint(tmp_path, request, opaque_content)
    assert len(result.observation_refs) == 2
    encoded = (tmp_path / result.observation_refs[0]["relative_path"]).read_text()
    assert json.loads(encoded)["content"] == opaque_content
    omitted = json.loads(backend.requests[1].messages[-1]["content"][0]["content"])
    assert omitted["content_omitted_atomically"] is True
    assert omitted["workspace_history"] == {"observation_sha256": result.observation_refs[0]["sha256"]}
    assert omitted["read_tool"] == "read_workspace_history"
    resumed, _ = resume_client_tool_session_from_checkpoint(
        first, session_dir=tmp_path, session_id="history-owner", request=request,
        checkpoint_identity="checkpoint", require_durable_state_binding=True,
    )
    second, _, _ = _history_checkpoint(tmp_path, resumed, "a later observation")
    second_payload = json.loads((tmp_path / second["relative_path"]).read_text())
    assert second_payload["parent_session_ref"] == first
    assert len(second_payload["observation_refs"]) == 2
    assert "original-tail" not in json.dumps(second_payload["messages"])
    latest, _ = resume_client_tool_session_from_checkpoint(
        second, session_dir=tmp_path, session_id="history-owner", request=request,
        checkpoint_identity="checkpoint", require_durable_state_binding=True,
    )
    scripted = ScriptedToolTurnBackend([
        _response(ClientToolCall(call_id="old-tail", name="read_workspace_history", input={
            **omitted["workspace_history"],
            "character_start": len(encoded) - 1000, "character_end": len(encoded),
        })),
        _response(ClientToolCall(call_id="save-latest", name="submit", input={})),
    ])
    executed = []

    def execute(call, _context):
        executed.append(call.name)
        return ClientToolExecutionResult(content={"saved": True}, terminal=True,
                                         terminal_payload={"disposition": "checkpoint"})

    recovered = run_bounded_client_tool_loop(
        backend=scripted, request=latest, execute_tool=execute,
        max_turns=2, max_tool_calls=2, max_no_progress_turns=2,
        session_dir=tmp_path, session_id="history-owner",
    )
    observation = json.loads(scripted.requests[1].messages[-1]["content"][0]["content"])
    assert observation["text"] == encoded[-1000:]
    assert observation["sha256"] == result.observation_refs[0]["sha256"]
    assert observation["session_sha256"] == first["sha256"]
    assert observation["evidence_role"] == "historical_tool_observation_not_current_acceptance"
    assert executed == ["submit"]  # Old tools never execute again.
    assert len(recovered.observation_refs) == 1  # A history read is not copied into the archive.
    assert recovered.terminal_payload == {"disposition": "checkpoint"}


def test_history_reads_current_observation_without_exposing_private_reasoning(tmp_path):
    request = _history_request()
    first = _response(ClientToolCall(call_id="observe", name="check", input={}))
    first = replace(first, content_blocks=(
        {"type": "thinking", "thinking": "private-model-reasoning", "signature": "opaque-signature"},
        *first.content_blocks,
    ))
    class HistoryReaderBackend(ScriptedToolTurnBackend):
        def generate_client_tool_turn(self, request):
            if len(self.requests) == 2:
                catalog = json.loads(request.messages[-1]["content"][0]["content"])
                ref = json.loads(catalog["text"])[0]
                self.responses[0] = _response(ClientToolCall(
                    call_id="read", name="read_workspace_history", input={"observation_sha256": ref["sha256"]},
                ))
            return super().generate_client_tool_turn(request)

    backend = HistoryReaderBackend([
        first,
        _response(ClientToolCall(call_id="catalog", name="read_workspace_history", input={})),
        _response(),
        _response(ClientToolCall(call_id="save", name="submit", input={})),
    ])

    def execute(call, _context):
        return ClientToolExecutionResult(content={"opaque": "observed-result"},
            terminal=call.name == "submit", terminal_payload={"disposition": "checkpoint"})

    result = run_bounded_client_tool_loop(
        backend=backend, request=request, execute_tool=execute,
        max_turns=4, max_tool_calls=4, max_no_progress_turns=2,
        session_dir=tmp_path, session_id="history-owner",
    )
    catalog = json.loads(backend.requests[2].messages[-1]["content"][0]["content"])
    assert catalog["parent_session_sha256"] == "" and catalog["observation_count"] == 1
    read = json.loads(backend.requests[3].messages[-1]["content"][0]["content"])
    assert json.loads(read["text"])["content"] == {"opaque": "observed-result"}
    assert "private-model-reasoning" not in read["text"]
    assert "opaque-signature" not in read["text"]
    assert len(result.observation_refs) == 2


@pytest.mark.parametrize("mutation", ["observation_bytes", "session_bytes", "authorization", "root", "session_id"])
def test_history_requires_original_store_bytes_and_workspace_authority(tmp_path, mutation):
    request = _history_request()
    reference, result, _ = _history_checkpoint(tmp_path, request, "private-to-this-workspace")
    resumed, _ = resume_client_tool_session_from_checkpoint(
        reference, session_dir=tmp_path, session_id="history-owner", request=request,
        checkpoint_identity="checkpoint",
    )
    root, session_id = tmp_path, "history-owner"
    if mutation == "observation_bytes":
        (tmp_path / result.observation_refs[0]["relative_path"]).write_text("changed bytes")
    elif mutation == "session_bytes":
        (tmp_path / reference["relative_path"]).write_text("changed bytes")
    elif mutation == "authorization":
        resumed = replace(resumed, metadata={**resumed.metadata,
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: "different-reviewer"})
    elif mutation == "root":
        root = tmp_path / "foreign-store"
        root.mkdir()
    else:
        session_id = "different-owner"
    with pytest.raises(ValueError):
        client_tool_loop._read_workspace_history(
            {"session_sha256": reference["sha256"], "observation_sha256": result.observation_refs[0]["sha256"]},
            session_dir=root, session_id=session_id, request=resumed, observation_refs=(),
        )


def test_history_cannot_select_unlinked_windows_or_escape_observation_store(tmp_path):
    request = _history_request()
    reference, result, _ = _history_checkpoint(tmp_path, request, "scoped-observation")
    with pytest.raises(ClientToolInputError, match="authorized parent chain"):
        client_tool_loop._read_workspace_history(
            {"session_sha256": reference["sha256"]}, session_dir=tmp_path,
            session_id="history-owner", request=request, observation_refs=(),
        )
    forged = {**result.observation_refs[0], "relative_path": "../outside.json"}
    with pytest.raises(ValueError, match="escapes"):
        client_tool_loop._read_workspace_history(
            {"observation_sha256": forged["sha256"]}, session_dir=tmp_path, session_id="history-owner",
            request=request, observation_refs=[forged],
        )


def test_interrupted_loop_preserves_original_observation_refs(tmp_path):
    request = _history_request()
    backend = ScriptedToolTurnBackend([
        _response(ClientToolCall(call_id="check-before-stop", name="check", input={})),
        _response(text="unfinished checkpoint", stop_reason="end_turn"),
    ])
    with pytest.raises(ClientToolLoopError) as error:
        run_bounded_client_tool_loop(
            backend=backend, request=request,
            execute_tool=lambda *_: ClientToolExecutionResult(content="opaque-checkpoint-observation"),
            max_turns=3, max_tool_calls=3, max_no_progress_turns=2,
            session_dir=tmp_path, session_id="history-owner",
        )
    assert len(error.value.observation_refs) == 1
    saved = json.loads((tmp_path / error.value.observation_refs[0]["relative_path"]).read_text())
    assert saved["content"] == "opaque-checkpoint-observation"


def test_observation_storage_failure_stops_without_reexecuting_source(tmp_path, monkeypatch):
    def cannot_store(*_args):
        raise OSError("synthetic private filesystem detail")

    monkeypatch.setattr(client_tool_loop, "_persist_workspace_observation", cannot_store)
    backend = ScriptedToolTurnBackend([
        _response(ClientToolCall(call_id="check", name="check", input={})),
    ])
    executions = []

    def execute(call, _context):
        executions.append(call.call_id)
        return ClientToolExecutionResult(content="opaque result", state_changed=True)

    with pytest.raises(ClientToolLoopError, match="observation persistence failed") as error:
        run_bounded_client_tool_loop(
            backend=backend, request=_history_request(), execute_tool=execute,
            max_turns=3, max_tool_calls=3, max_no_progress_turns=2,
            session_dir=tmp_path, session_id="history-owner",
        )
    assert executions == ["check"] and len(backend.requests) == 1
    assert "synthetic private filesystem detail" not in str(error.value)


@pytest.mark.parametrize("tool_input", [
    {"observation_sha256": True}, {"observation_sha256": ""},
    {"character_start": -1}, {"character_start": True}, {"character_end": 0},
    {"character_end": 999999}, {"session_sha256": {}}, {"path": "/host-file"},
])
def test_history_read_range_and_selection_errors_are_model_actionable(tmp_path, tool_input):
    request = _history_request()
    _, result, _ = _history_checkpoint(tmp_path, request, "source-owned observation")
    with pytest.raises(ClientToolInputError):
        client_tool_loop._read_workspace_history(
            tool_input, session_dir=tmp_path, session_id="history-owner",
            request=request, observation_refs=result.observation_refs,
        )


def test_exact_text_edits_support_count_checked_repeated_literals() -> None:
    revised, records = apply_model_exact_text_edits(
        '{"lower":"-2.0","upper":"2.0","copy":"-2.0"}',
        edits=[
            {
                "old_text": '"-2.0"',
                "new_text": "-2.0",
                "expected_occurrences": 2,
            },
            {"old_text": '"2.0"', "new_text": "2.0"},
        ],
        replacement_key="new_text",
    )

    assert revised == '{"lower":-2.0,"upper":2.0,"copy":-2.0}'
    assert records[0]["occurrences_replaced"] == 2
    assert "occurrences_replaced" not in records[1]
    with pytest.raises(ClientToolInputError, match="expected 3, observed 2"):
        apply_model_exact_text_edits(
            '"x" "x"',
            edits=[{
                "old_text": '"x"',
                "new_text": '"y"',
                "expected_occurrences": 3,
            }],
            replacement_key="new_text",
        )


def test_exact_text_edit_batch_schema_is_shared_and_strict() -> None:
    single = model_exact_text_edit_json_schema()
    schema = model_exact_text_edits_json_schema()

    assert single["type"] == "object"
    assert single["required"] == ["old_text", "new_text"]
    assert single["additionalProperties"] is False
    assert schema["type"] == "array"
    assert schema["minItems"] == 1
    assert schema["items"] == single
    assert set(single["properties"]) == {
        "old_text",
        "new_text",
        "expected_occurrences",
    }
    assert not {"oneOf", "anyOf", "allOf"}.intersection(schema)


def test_exact_text_edit_errors_name_missing_and_unexpected_fields() -> None:
    with pytest.raises(ClientToolInputError) as exc_info:
        apply_model_exact_text_edits(
            "old",
            edits=[{
                " old_text": "old",
                "new_text": "new",
                "expected_occurrences": 1,
            }],
            replacement_key="new_text",
        )

    detail = str(exc_info.value)
    assert "missing=['old_text']" in detail
    assert "unexpected=[' old_text']" in detail
    assert "optional=['expected_occurrences']" in detail


def test_long_tool_observation_is_omitted_atomically() -> None:
    text = "grant=true\n" + ("restriction=middle\n" * 80) + "restriction=end"

    bounded = client_tool_loop._client_tool_result_text(text, max_chars=512)
    observation = json.loads(bounded)

    assert len(bounded) <= 512
    assert "grant=true" not in bounded
    assert "restriction=end" not in bounded
    assert observation == {
        "content_omitted_atomically": True,
        "detail": (
            "The complete tool observation exceeded the model boundary. No partial "
            "payload was delivered; use a narrower read or inspection action and do "
            "not infer success or authorization."
        ),
        "error": "client_tool_observation_exceeds_boundary",
        "observation_complete": False,
        "ok": False,
        "original_chars": len(text),
        "original_lines": len(text.splitlines()),
        "original_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


@pytest.mark.parametrize("as_input_error", [False, True])
def test_oversized_tool_result_reaches_same_model_as_incomplete_error(
    as_input_error: bool,
) -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall(call_id="read-1", name="check", input={})),
            _response(ClientToolCall(call_id="submit-1", name="submit", input={})),
        ]
    )
    large_observation = {
        "grant": True,
        "restrictions": ["must remain visible"] * 10_000,
    }
    detail = json.dumps(large_observation)
    expected_observation = (
        {
            "ok": False,
            "error": "client_tool_input_rejected",
            "exception_type": "ClientToolInputError",
            "detail": detail,
        }
        if as_input_error else large_observation
    )

    def execute_tool(call, _context):
        if call.name == "check":
            if as_input_error:
                raise ClientToolInputError(detail)
            return ClientToolExecutionResult(
                content=large_observation,
                state_changed=True,
                model_content_blocks=(
                    {"type": "image", "source": {"type": "base64", "data": "raw"}},
                ),
            )
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"accepted": True},
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute_tool,
        max_turns=2,
        max_tool_calls=1,
        max_no_progress_turns=2,
    )

    delivered = backend.requests[1].messages[-1]["content"][0]
    observation = json.loads(delivered["content"])
    assert delivered["is_error"] is True
    assert observation["observation_complete"] is False
    assert observation["content_omitted_atomically"] is True
    assert observation["original_sha256"] == hashlib.sha256(
        json.dumps(
            expected_observation,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    assert result.history[0]["tool_calls"][0][
        "model_observation_complete"
    ] is False
    assert result.history[0]["tool_calls"][0]["is_error"] is True


def test_client_tool_session_roundtrips_exact_transcript(tmp_path) -> None:
    request = _request()
    messages = (
        *request.messages,
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "call-edit",
                    "name": "edit",
                    "input": {"value": 2},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "call-edit",
                    "content": '{"ok":true,"value":2}',
                    "is_error": False,
                }
            ],
        },
    )

    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
        messages=messages,
    )

    assert reference["message_count"] == len(messages)
    assert reference["root_path"] == str(tmp_path.resolve())
    assert reference["relative_path"].startswith(".client_tool_sessions/")
    assert reference["authorization_fingerprint"] == "auth:q1:v1"
    assert load_client_tool_session(
        reference,
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
    ) == messages


def test_checkpoint_window_validates_parent_without_replaying_it(tmp_path) -> None:
    request = _request()
    prior_messages = (
        *request.messages,
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "prior-private-call",
                    "name": "edit",
                    "input": {"value": 2},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "prior-private-call",
                    "content": '{"ok":true,"value":2}',
                    "is_error": False,
                }
            ],
        },
    )
    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
        messages=prior_messages,
        durable_state_identity="theory-checkpoint:q1",
    )

    resumed_request, window = resume_client_tool_session_from_checkpoint(
        reference,
        session_dir=tmp_path,
        session_id="theory:q1",
        checkpoint_identity="theory-checkpoint:q1",
        request=request,
        require_durable_state_binding=True,
    )

    assert len(resumed_request.messages) == len(request.messages) == 1
    resumed_content = str(resumed_request.messages[0]["content"])
    assert "prior-private-call" not in resumed_content
    assert "Repair the artifact." in resumed_content
    assert "authoritative current checkpoint state" in resumed_content
    assert window == resumed_request.metadata["client_tool_checkpoint_window"]
    assert window["policy"] == CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY
    assert window["parent_message_count"] == len(prior_messages)
    assert window["checkpoint_identity"] == "theory-checkpoint:q1"
    assert window["parent_durable_state_identity"] == "theory-checkpoint:q1"
    assert window["authorization_fingerprint"] == "auth:q1:v1"
    assert window["parent_transcript_fingerprint"] == reference[
        "transcript_fingerprint"
    ]
    assert window["prior_transcript_replayed"] is False
    assert window["summary_used"] is False
    assert CLIENT_TOOL_TRANSCRIPT_POLICY.endswith("checkpoint_windows_v4")
    with pytest.raises(ValueError, match="identity mismatch"):
        resume_client_tool_session_from_checkpoint(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            checkpoint_identity="another-theory-checkpoint",
            request=request,
            require_durable_state_binding=True,
        )
    with pytest.raises(ValueError, match="requires checkpoint identity"):
        resume_client_tool_session_from_checkpoint(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            checkpoint_identity="",
            request=request,
            require_durable_state_binding=True,
        )
    missing_authorization = replace(
        request,
        metadata={"model_tier": "haiku"},
    )
    with pytest.raises(ValueError, match="root authorization fingerprint"):
        resume_client_tool_session_from_checkpoint(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            checkpoint_identity="theory-checkpoint:q1",
            request=missing_authorization,
            require_durable_state_binding=True,
        )
    unbound_reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1-unbound",
        request=request,
        messages=prior_messages,
    )
    with pytest.raises(ValueError, match="requires a durable state identity"):
        resume_client_tool_session_from_checkpoint(
            unbound_reference,
            session_dir=tmp_path,
            session_id="theory:q1-unbound",
            checkpoint_identity="theory-checkpoint:q1",
            request=request,
            require_durable_state_binding=True,
        )


def test_checkpoint_window_replays_recent_complete_tool_rounds(tmp_path) -> None:
    parent_request = _request()
    prior_messages = (
        *parent_request.messages,
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "prior-complete-call",
                    "name": "edit",
                    "input": {"value": 2},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "prior-complete-call",
                    "content": '{"ok":true,"value":2}',
                    "is_error": False,
                }
            ],
        },
    )
    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=parent_request,
        messages=prior_messages,
        durable_state_identity="theory-checkpoint:q1",
    )
    current_request = replace(
        parent_request,
        messages=(
            {
                "role": "user",
                "content": "Continue from the current checkpoint catalog.",
            },
        ),
    )

    resumed_request, window = resume_client_tool_session_from_checkpoint(
        reference,
        session_dir=tmp_path,
        session_id="theory:q1",
        checkpoint_identity="theory-checkpoint:q1",
        request=current_request,
        replay_recent_tool_rounds=1,
        require_durable_state_binding=True,
    )

    assert window["policy"] == CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY
    assert window["prior_transcript_replayed"] is True
    assert window["replayed_tool_rounds"] == 1
    assert window["replayed_message_count"] == 2
    assert window["replayed_messages_fingerprint"]
    assert window["parent_opening_replayed"] is False
    assert window["current_opening_authoritative"] is True
    assert window["current_opening_fingerprint"]
    assert len(resumed_request.messages) == 3
    assert [row["role"] for row in resumed_request.messages] == [
        "user",
        "assistant",
        "user",
    ]
    assert resumed_request.messages[0] == current_request.messages[0]
    resumed_text = str(resumed_request.messages)
    assert "prior-complete-call" in resumed_text
    assert "Continue from the current checkpoint catalog." in resumed_text
    assert "Repair the artifact." not in resumed_text
    assert "budget counters in them belong to the old window" in resumed_text


def test_client_tool_session_rejects_contract_drift_and_tampering(tmp_path) -> None:
    request = _request()
    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=request,
        messages=request.messages,
    )

    changed_sampling = replace(request, max_tokens=request.max_tokens + 1)
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_sampling,
        )

    changed_authorization = replace(
        request,
        metadata={
            **dict(request.metadata),
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: "auth:q1:v2",
        },
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_authorization,
        )

    changed_tools = replace(
        request,
        tools=(*request.tools, _tool("search")),
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_tools,
        )

    changed_tool_description = replace(
        request,
        tools=(
            replace(request.tools[0], description="Use a changed edit contract."),
            *request.tools[1:],
        ),
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_tool_description,
        )

    changed_tool_schema = replace(
        request,
        tools=(
            replace(
                request.tools[0],
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"value": {"type": "integer"}},
                    "required": ["value"],
                },
            ),
            *request.tools[1:],
        ),
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=changed_tool_schema,
        )

    for field_name, changed_value in (
        ("max_tokens", request.max_tokens + 1),
        ("temperature", 0.25),
        ("tool_choice", "submit"),
        ("disable_parallel_tool_use", True),
        ("enable_prompt_caching", True),
    ):
        changed_sampling_contract = replace(
            request,
            **{field_name: changed_value},
        )
        with pytest.raises(ValueError, match="identity mismatch"):
            load_client_tool_session(
                reference,
                session_dir=tmp_path,
                session_id="theory:q1",
                request=changed_sampling_contract,
            )

    with pytest.raises(ValueError, match="identity mismatch"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path / "different-workspace",
            session_id="theory:q1",
            request=request,
        )

    session_path = tmp_path / reference["relative_path"]
    session_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="bytes do not match"):
        load_client_tool_session(
            reference,
            session_dir=tmp_path,
            session_id="theory:q1",
            request=request,
        )


def test_bounded_client_tool_loop_returns_terminal_runtime_payload() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(
                ClientToolCall("call-edit", "edit", {"value": 2}),
                ClientToolCall("call-check", "check", {}),
            ),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    state = {"value": 1}

    def execute(call, context):
        if call.name == "edit":
            state["value"] = call.input["value"]
            return ClientToolExecutionResult(
                content={"ok": True, "value": state["value"]},
                state_changed=True,
                observation_key="edited:2",
            )
        if call.name == "check":
            return ClientToolExecutionResult(
                content={"ok": state["value"] == 2},
                observation_key="check:passed",
            )
        assert context.call_index == context.calls_in_turn - 1
        return ClientToolExecutionResult(
            content={"ok": True, "submitted": True},
            terminal=True,
            terminal_payload={"value": state["value"]},
            observation_key="submitted:2",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=3,
        max_tool_calls=5,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"value": 2}
    assert result.turns == 2
    assert result.tool_calls == 3
    assert result.runtime_executed_tool_calls == 3
    assert result.provider_usage == {"input_tokens": 22, "output_tokens": 6}
    assert result.transcript_fingerprint
    assert len(backend.requests) == 2
    second_messages = backend.requests[1].messages
    assert second_messages[-2]["role"] == "assistant"
    assert second_messages[-1]["content"][0]["type"] == "tool_result"
    first_observation = json.loads(
        second_messages[-1]["content"][0]["content"]
    )
    assert first_observation == {"ok": True, "value": 2}
    assert result.history[0]["tool_calls"][0]["name"] == "edit"
    assert '"value":2' in result.history[0]["tool_calls"][0][
        "result_excerpt"
    ]
    assert result.history[0]["response_metadata"][
        "tools_executed_by_backend"
    ] is False


def test_bounded_client_tool_loop_returns_native_media_to_same_model() -> None:
    backend = ScriptedToolTurnBackend([
        _response(ClientToolCall("call-inspect", "inspect", {})),
        _response(ClientToolCall("call-submit", "submit", {})),
    ])
    media = {"type": "image", "source": {
        "type": "base64", "media_type": "image/png", "data": "aW1hZ2U="}}

    def execute(call, _context):
        if call.name == "inspect":
            return ClientToolExecutionResult(
                content={"ok": True, "sha256": "a" * 64},
                model_content_blocks=(media,), observation_key="image:a",
            )
        return ClientToolExecutionResult(
            content={"ok": True}, terminal=True,
            terminal_payload={"submitted": True}, observation_key="submitted",
        )

    request = replace(_request(), tools=(_tool("inspect"), _tool("submit", terminal=True)))
    result = run_bounded_client_tool_loop(
        backend=backend, request=request, execute_tool=execute,
        max_turns=2, max_tool_calls=2, max_no_progress_turns=2,
    )

    tool_content = backend.requests[1].messages[-1]["content"][0]["content"]
    assert tool_content[0]["type"] == "text"
    assert json.loads(tool_content[0]["text"])["ok"] is True
    assert tool_content[1] == media
    assert result.terminal_payload == {"submitted": True}


def test_bounded_client_tool_loop_never_executes_truncated_tool_input() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(
                ClientToolCall("call-truncated", "edit", {}),
                stop_reason="max_tokens",
            ),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    executed_tools: list[str] = []

    def execute(call, _context):
        executed_tools.append(call.name)
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=call.name == "submit",
            terminal_payload={"submitted": True} if call.name == "submit" else None,
            observation_key=call.name,
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=2,
        max_tool_calls=2,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert executed_tools == ["submit"]
    assert result.runtime_executed_tool_calls == 1
    truncated = result.history[0]
    assert truncated["provider_output_truncated"] is True
    assert truncated["tool_calls"][0]["executed_by_runtime"] is False
    assert truncated["tool_calls"][0]["is_error"] is True
    assert "provider_tool_input_truncated" in str(
        backend.requests[1].messages[-1]["content"]
    )


def test_bounded_client_tool_loop_keeps_one_linear_model_tool_history() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit-1", "edit", {"value": 1})),
            _response(ClientToolCall("call-edit-2", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    state = {"value": 0}

    def execute(call, _context):
        if call.name == "edit":
            state["value"] = int(call.input["value"])
            return ClientToolExecutionResult(
                content={"ok": True, "value": state["value"]},
                state_changed=True,
                observation_key=f"edited:{state['value']}",
            )
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"value": state["value"]},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=3,
        max_tool_calls=3,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"value": 2}
    assert [len(request.messages) for request in backend.requests] == [1, 3, 5]
    assert backend.requests[-1].messages[0] == backend.requests[0].messages[0]
    final_context = str(backend.requests[-1].messages)
    assert "<rollout_budget>" not in final_context
    assert "call-edit-1" in final_context
    assert "call-edit-2" in final_context
    assert "'value': 1" in final_context
    assert "'value': 2" in final_context


def test_bounded_client_tool_loop_stops_without_forced_terminal_phase() -> None:
    response = _response(text="I will describe the change instead.")
    backend = ScriptedToolTurnBackend([response, response, response, response])

    with pytest.raises(
        ClientToolLoopError,
        match="model ended the workspace turn without a client tool call",
    ) as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=lambda call, context: ClientToolExecutionResult({}),
            max_turns=4,
            max_tool_calls=5,
            max_no_progress_turns=2,
        )

    assert exc.value.tool_calls == 0
    assert exc.value.turns == 1
    assert len(backend.requests) == 1
    assert exc.value.messages
    assert exc.value.messages[-1] == {
        "role": "assistant",
        "content": [{"type": "text", "text": response.text}],
    }
    assert exc.value.provider == "anthropic"
    assert exc.value.model == "claude-haiku-4-5-20251001"
    assert exc.value.transcript_fingerprint


def test_bounded_client_tool_loop_does_not_accept_early_terminal_call() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(
                ClientToolCall("call-submit", "submit", {}),
                ClientToolCall("call-edit", "edit", {}),
            ),
            _response(ClientToolCall("call-submit-final", "submit", {})),
        ]
    )

    executed_tools = []

    def execute(call, context):
        executed_tools.append(call.name)
        if call.name == "submit":
            return ClientToolExecutionResult(
                content={"ok": True},
                terminal=True,
                terminal_payload={"accepted": True},
            )
        return ClientToolExecutionResult(
            content={"ok": True},
            observation_key="edit-after-submit",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=replace(
            _request(),
            tools=(_tool("edit"), _tool("submit", terminal=True)),
        ),
        execute_tool=execute,
        max_turns=2,
        max_tool_calls=3,
        max_no_progress_turns=2,
    )

    first_turn = backend.requests[0]
    assert first_turn.tool_choice == "any"
    assert [tool.name for tool in first_turn.tools] == ["edit", "submit"]
    assert first_turn.disable_parallel_tool_use is False
    assert executed_tools == ["edit", "submit"]
    assert result.terminal_payload == {"accepted": True}


def test_bounded_client_tool_loop_keeps_normal_final_turn_model_directed() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=lambda call, context: ClientToolExecutionResult(
            content={"ok": True},
            state_changed=call.name == "edit",
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        ),
        max_turns=2,
        max_tool_calls=2,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert [tool.name for tool in backend.requests[0].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert [tool.name for tool in backend.requests[1].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert backend.requests[1].tool_choice == "any"
    assert backend.requests[1].disable_parallel_tool_use is False


def test_terminal_call_does_not_consume_workspace_action_budget() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=lambda call, context: ClientToolExecutionResult(
            content={"ok": True},
            state_changed=call.name == "edit",
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        ),
        max_turns=3,
        max_tool_calls=1,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 2
    assert result.tool_calls == 2
    assert result.runtime_executed_tool_calls == 2
    final_action_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert final_action_observation == {"ok": True}
    assert "client_tool_loop_terminal_decision_turn" not in backend.requests[1].metadata


def test_last_workspace_action_does_not_trigger_hidden_terminal_turn() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    executed_tools: list[str] = []

    def execute(call, _context):
        executed_tools.append(call.name)
        return ClientToolExecutionResult(
            content={"ok": True},
            state_changed=call.name == "edit",
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        )

    with pytest.raises(ClientToolLoopError, match="turn budget exhausted") as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=execute,
            max_turns=1,
            max_tool_calls=4,
            max_no_progress_turns=2,
        )

    assert exc.value.turns == 1
    assert executed_tools == ["edit"]
    assert len(backend.requests) == 1
    assert "client_tool_loop_terminal_continuation" not in (
        backend.requests[0].metadata
    )


def test_rejected_terminal_at_explicit_limit_is_not_retried() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    terminal_attempts = 0

    def execute(call, _context):
        nonlocal terminal_attempts
        if call.name == "edit":
            return ClientToolExecutionResult(
                content={"ok": True},
                state_changed=True,
                observation_key="edited",
            )
        terminal_attempts += 1
        if terminal_attempts == 1:
            raise ClientToolInputError("terminal packet is incomplete")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    with pytest.raises(ClientToolLoopError, match="turn budget exhausted") as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=execute,
            max_turns=2,
            max_tool_calls=4,
            max_no_progress_turns=2,
        )

    assert terminal_attempts == 1
    assert len(backend.requests) == 2
    assert "terminal packet is incomplete" in str(exc.value.messages[-1])
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests
    )
    assert all(
        "client_tool_loop_terminal_rejection_followup" not in request.metadata
        for request in backend.requests
    )


def test_rejected_terminal_is_an_ordinary_same_model_observation() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    terminal_attempts = 0

    def execute(call, context):
        nonlocal terminal_attempts
        if call.name == "edit":
            return ClientToolExecutionResult(
                content={"ok": True},
                state_changed=True,
                observation_key="edited",
            )
        terminal_attempts += 1
        if terminal_attempts == 1:
            raise ClientToolInputError("submitted packet is incomplete")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=3,
        max_tool_calls=3,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 3
    assert terminal_attempts == 2
    assert [tool.name for tool in backend.requests[2].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert backend.requests[2].tool_choice == "any"
    assert "client_tool_loop_terminal_decision_turn" not in backend.requests[2].metadata


@pytest.mark.parametrize("source_size", [16, 4096])
@pytest.mark.parametrize(
    "diagnostic",
    [
        "parser rejected the current file",
        "unfamiliar diagnostic\n" + "model-visible details\n" * 128 + "last constraint",
    ],
    ids=["short", "long"],
)
def test_rejected_terminal_can_be_followed_by_model_selected_edit(
    diagnostic: str, source_size: int,
) -> None:
    sources = [hashlib.sha256(str(i).encode()).hexdigest() * source_size for i in range(2)]
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit-initial", "edit", {"value": sources[0]})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-edit-recovery", "edit", {"value": sources[1]})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    submissions = 0
    executed_tools: list[str] = []
    authored_sources: list[str] = []

    def execute(call, _context):
        nonlocal submissions
        executed_tools.append(call.name)
        if call.name == "edit":
            authored_sources.append(call.input["value"])
            return ClientToolExecutionResult(
                content={"ok": True, "value": call.input["value"]},
                state_changed=True,
                observation_key=f"edit:{call.input['value']}",
            )
        submissions += 1
        assert authored_sources == sources[:submissions]
        if submissions == 1:
            raise ClientToolInputError(diagnostic)
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=4,
        max_tool_calls=2,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 4
    assert executed_tools == ["edit", "submit", "edit", "submit"]
    assert authored_sources == sources
    assert "client_tool_loop_terminal_recovery_action_allowed" not in backend.requests[2].metadata
    assert "client_tool_loop_terminal_recovery_action_allowed" not in backend.requests[3].metadata
    recovery_call = result.history[2]["tool_calls"][0]
    assert recovery_call["executed_by_runtime"] is True
    assert recovery_call["state_changed"] is True
    delivered = backend.requests[2].messages[-1]["content"][0]
    assert delivered["is_error"] is True
    assert json.loads(delivered["content"])["detail"] == diagnostic
    assert result.history[1]["tool_calls"][0]["model_observation_complete"] is True


def test_terminal_rejection_can_be_inspected_edited_and_resubmitted() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit-initial", "edit", {"value": 1})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-check-recovery", "check", {})),
            _response(ClientToolCall("call-edit-recovery", "edit", {"value": 2})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    submissions = 0
    executed_tools: list[str] = []

    def execute(call, _context):
        nonlocal submissions
        executed_tools.append(call.name)
        if call.name == "check":
            return ClientToolExecutionResult(
                content={"ok": True, "current_value": 1},
                observation_key="checked:1",
            )
        if call.name == "edit":
            return ClientToolExecutionResult(
                content={"ok": True, "value": call.input["value"]},
                state_changed=True,
                observation_key=f"edit:{call.input['value']}",
            )
        submissions += 1
        if submissions == 1:
            return ClientToolExecutionResult(
                content={
                    "ok": False,
                    "error": "validator rejected the forced commit",
                },
                is_error=True,
                observation_key="forced-commit-rejected",
            )
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=5,
        max_tool_calls=3,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 5
    assert executed_tools == ["edit", "submit", "check", "edit", "submit"]
    assert all(
        "client_tool_loop_terminal_recovery_action_allowed" not in request.metadata
        for request in backend.requests
    )
    assert "validator rejected the forced commit" in str(
        backend.requests[2].messages[-1]["content"]
    )


def test_duplicate_terminal_rejection_hits_generic_no_progress_bound() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-submit-standard", "submit", {})),
            _response(ClientToolCall("call-submit-recovery", "submit", {})),
            _response(ClientToolCall("call-submit-final", "submit", {})),
        ]
    )

    with pytest.raises(ClientToolLoopError) as raised:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=lambda _call, _context: ClientToolExecutionResult(
                content={"ok": False, "error": "same validator rejection"},
                is_error=True,
                observation_key="same-validator-rejection",
            ),
            max_turns=3,
            max_tool_calls=1,
            max_no_progress_turns=1,
        )

    assert "no new progress" in raised.value.reason
    assert len(backend.requests) == 2


def test_duplicate_ordinary_no_progress_has_no_hidden_terminal_turn() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit-first", "edit", {})),
            _response(ClientToolCall("call-edit-duplicate", "edit", {})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    def execute(call, _context):
        if call.name == "submit":
            return ClientToolExecutionResult(
                content={"ok": True},
                terminal=True,
                terminal_payload={"submitted": True},
                observation_key="submitted",
            )
        return ClientToolExecutionResult(
            content={"ok": False, "error": "same invalid ordinary action"},
            is_error=True,
            observation_key="same-invalid-ordinary-action",
        )

    with pytest.raises(ClientToolLoopError, match="no new progress") as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=execute,
            max_turns=5,
            max_tool_calls=5,
            max_no_progress_turns=1,
        )

    assert exc.value.turns == 2
    assert len(backend.requests) == 2


def test_terminal_only_tool_surface_remains_model_directed() -> None:
    backend = ScriptedToolTurnBackend([_response(text="The workspace is not ready.")])
    request = replace(
        _request(),
        tools=(_tool("submit", terminal=True),),
        tool_choice="auto",
        disable_parallel_tool_use=False,
    )

    with pytest.raises(ClientToolLoopError, match="model ended the workspace turn"):
        run_bounded_client_tool_loop(
            backend=backend,
            request=request,
            execute_tool=lambda call, context: pytest.fail("no tool was selected"),
            max_turns=1,
            max_tool_calls=1,
            max_no_progress_turns=1,
        )

    observed = backend.requests[0]
    assert observed.tool_choice == "auto"
    assert observed.disable_parallel_tool_use is False
    assert "client_tool_loop_terminal_only_turn" not in observed.metadata


@pytest.mark.parametrize("thinking_budget", [0, 1024])
def test_no_tool_response_requires_explicit_workspace_continuation(thinking_budget) -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {})),
            _response(text="I am not ready."),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    with pytest.raises(
        ClientToolLoopError,
        match="model ended the workspace turn without a client tool call",
    ) as exc:
        run_bounded_client_tool_loop(
            backend=backend,
            request=replace(_request(), thinking_budget_tokens=thinking_budget),
            execute_tool=lambda call, context: ClientToolExecutionResult(
                content={"ok": True},
                state_changed=call.name == "edit",
                terminal=call.name == "submit",
                terminal_payload=(
                    {"submitted": True} if call.name == "submit" else None
                ),
                observation_key=call.name,
            ),
            max_turns=3,
            max_tool_calls=3,
            max_no_progress_turns=2,
        )

    assert exc.value.turns == 2
    assert exc.value.tool_calls == 1
    assert len(backend.requests) == 2
    assert [tool.name for tool in backend.requests[-1].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert backend.requests[-1].messages[-1]["role"] == "user"
    assert "No client tool was called" not in str(exc.value.messages)


def test_action_budget_keeps_tools_visible_but_does_not_execute_late_action() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {"value": 2})),
            _response(ClientToolCall("call-check-late", "check", {})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    executed_tools: list[str] = []

    def execute(call, _context):
        executed_tools.append(call.name)
        return ClientToolExecutionResult(
            content={"ok": True},
            state_changed=call.name == "edit",
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=3,
        max_tool_calls=1,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert executed_tools == ["edit", "submit"]
    rejected = result.history[1]["tool_calls"][0]
    assert rejected["executed_by_runtime"] is False
    assert "workspace_action_budget_exhausted" in rejected["result_excerpt"]
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests
    )


def test_repeated_observation_can_still_be_followed_by_model_submission() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-check-1", "check", {})),
            _response(ClientToolCall("call-check-2", "check", {})),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=lambda call, context: ClientToolExecutionResult(
            content={"ok": True},
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
            observation_key=call.name,
        ),
        max_turns=5,
        max_tool_calls=3,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 3
    assert [tool.name for tool in backend.requests[-1].tools] == [
        "edit",
        "check",
        "submit",
    ]
    assert "client_tool_loop_terminal_decision_reason" not in backend.requests[-1].metadata


def test_rejected_submission_can_be_resubmitted_within_generic_turn_budget() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-check-1", "check", {})),
            _response(ClientToolCall("call-check-2", "check", {})),
            _response(ClientToolCall("call-submit-invalid", "submit", {})),
            _response(ClientToolCall("call-submit-valid", "submit", {})),
        ]
    )
    submissions = 0

    def execute(call, _context):
        nonlocal submissions
        if call.name == "check":
            return ClientToolExecutionResult(
                content={"ok": True},
                observation_key="same-check",
            )
        submissions += 1
        if submissions == 1:
            raise ClientToolInputError("compiler rejected the first source")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=5,
        max_tool_calls=4,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 4
    assert submissions == 2
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests[-2:]
    )
    assert "compiler rejected the first source" in str(
        backend.requests[-1].messages[-1]["content"]
    )


def test_multiple_rejected_submissions_share_the_same_generic_turn_budget() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-submit-early", "submit", {})),
            _response(ClientToolCall("call-check", "check", {})),
            _response(ClientToolCall("call-submit-final", "submit", {})),
            _response(ClientToolCall("call-submit-recovery", "submit", {})),
        ]
    )
    submissions = 0

    def execute(call, _context):
        nonlocal submissions
        if call.name == "check":
            return ClientToolExecutionResult(
                content={"ok": True, "observation": "new context"},
                observation_key="new-context",
            )
        submissions += 1
        if submissions < 3:
            raise ClientToolInputError(f"raw compiler failure {submissions}")
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"submitted": True},
            observation_key="submitted",
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=4,
        max_tool_calls=4,
        max_no_progress_turns=2,
    )

    assert result.terminal_payload == {"submitted": True}
    assert result.turns == 4
    assert submissions == 3
    assert all(
        [tool.name for tool in request.tools] == ["edit", "check", "submit"]
        for request in backend.requests[-2:]
    )
    assert "raw compiler failure 2" in str(
        backend.requests[-1].messages[-1]["content"]
    )


def test_bounded_client_tool_loop_never_executes_unknown_tool() -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(
                ClientToolCall("call-unknown", "shell", {"cmd": "rm -rf /"})
            ),
            _response(ClientToolCall("call-submit", "submit", {})),
        ]
    )
    executions = 0

    def execute(call, context):
        nonlocal executions
        executions += 1
        return ClientToolExecutionResult(
            content={"ok": True},
            terminal=call.name == "submit",
            terminal_payload=(
                {"submitted": True} if call.name == "submit" else None
            ),
        )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=_request(),
        execute_tool=execute,
        max_turns=2,
        max_tool_calls=2,
        max_no_progress_turns=1,
    )

    assert executions == 1
    assert result.runtime_executed_tool_calls == 1
    assert result.terminal_payload == {"submitted": True}
    assert result.history[0]["tool_calls"][0]["executed_by_runtime"] is False


def test_bounded_client_tool_loop_returns_only_declared_input_errors_to_model() -> None:
    safe_backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-safe", "edit", {})),
            _response(text="stop"),
            _response(ClientToolCall("call-submit", "submit", {})),
            _response(ClientToolCall("call-submit-followup", "submit", {})),
        ]
    )

    with pytest.raises(ClientToolLoopError):
        run_bounded_client_tool_loop(
            backend=safe_backend,
            request=_request(),
            execute_tool=lambda call, context: (_ for _ in ()).throw(
                ClientToolInputError("safe validator detail")
            ),
            max_turns=2,
            max_tool_calls=2,
            max_no_progress_turns=1,
        )

    internal_backend = ScriptedToolTurnBackend(
        [_response(ClientToolCall("call-internal", "edit", {}))]
    )
    secret = "private-runtime-detail"

    with pytest.raises(ClientToolRuntimeError) as exc:
        run_bounded_client_tool_loop(
            backend=internal_backend,
            request=_request(),
            execute_tool=lambda call, context: (_ for _ in ()).throw(
                RuntimeError(secret)
            ),
            max_turns=2,
            max_tool_calls=2,
            max_no_progress_turns=1,
        )

    safe_result = safe_backend.requests[1].messages[-1]["content"][0]
    assert "safe validator detail" in safe_result["content"]
    assert len(internal_backend.requests) == 1
    assert exc.value.tool_name == "edit"
    assert exc.value.exception_type == "RuntimeError"
    assert isinstance(exc.value, ClientToolLoopError)
    assert exc.value.turns == 1
    assert len(exc.value.messages) == 2
    assert exc.value.history[0]["tool_calls"][0]["is_error"] is True
    assert secret not in str(exc.value)
    assert exc.value.__context__ is None


@pytest.mark.parametrize("failure", [
    LiveGeneratorTimeoutError("private provider detail"), RuntimeError("private provider detail"),
    ValueError("private provider detail"), OSError("private provider detail"),
])
def test_terminal_provider_error_preserves_pending_workspace_input(tmp_path, failure) -> None:
    backend = ScriptedToolTurnBackend(
        [
            _response(ClientToolCall("call-edit", "edit", {})),
            failure,
        ]
    )

    with pytest.raises(ClientToolLoopError) as exc_info:
        run_bounded_client_tool_loop(
            backend=backend,
            request=_request(),
            execute_tool=lambda call, context: ClientToolExecutionResult(
                content={"ok": True, "artifact_hash": "updated"},
                state_changed=True,
            ),
            max_turns=3,
            max_tool_calls=3,
            max_no_progress_turns=2,
        )

    error = exc_info.value
    assert len(backend.requests) == 2
    assert error.turns == 2
    assert error.tool_calls == 1
    assert [message["role"] for message in error.messages] == [
        "user",
        "assistant",
        "user",
    ]
    assert error.history[-1]["stop_reason"] == "provider_terminal_error"
    metadata = error.history[-1]["response_metadata"]
    assert metadata["exception_type"] == type(failure).__name__
    assert metadata["exception_module"] == type(failure).__module__
    assert metadata["pending_workspace_input_preserved"] is True
    assert metadata["automatic_turn_restart"] is False
    assert "private provider detail" not in str(error)

    reference = persist_client_tool_session(
        session_dir=tmp_path,
        session_id="theory:q1",
        request=_request(),
        messages=error.messages,
    )
    assert load_client_tool_session(
        reference,
        session_dir=tmp_path,
        session_id="theory:q1",
        request=_request(),
    ) == tuple(error.messages)


def test_bounded_client_tool_loop_uses_existing_runtime_substage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = []

    @contextmanager
    def record_substage(name, *, metadata):
        details = dict(metadata)
        observed.append(("start", name, dict(details)))
        yield details
        observed.append(("finish", name, dict(details)))

    monkeypatch.setattr(
        "ai_statistician.client_tool_loop.agent_runtime_substage",
        record_substage,
    )
    backend = ScriptedToolTurnBackend(
        [_response(ClientToolCall("call-submit", "submit", {}))]
    )

    result = run_bounded_client_tool_loop(
        backend=backend,
        request=replace(
            _request(),
            metadata={
                "model_tier": "haiku",
                "subsystem": "TheoryReferee",
                "agent": "IndependentTheoryRefereeAgent",
                "review_stage": "theory_execution_preflight",
            },
        ),
        execute_tool=lambda call, context: ClientToolExecutionResult(
            content={"ok": True},
            terminal=True,
            terminal_payload={"ok": True},
        ),
        max_turns=2,
        max_tool_calls=2,
        max_no_progress_turns=1,
    )

    assert result.terminal_payload == {"ok": True}
    assert [row[:2] for row in observed] == [
        ("start", "client_tool_model_turn"),
        ("finish", "client_tool_model_turn"),
        ("start", "client_tool_execution"),
        ("finish", "client_tool_execution"),
    ]
    assert observed[0][2]["turn_index"] == 0
    assert observed[0][2]["model"] == "claude-haiku-4-5-20251001"
    assert observed[0][2]["workspace_subsystem"] == "TheoryReferee"
    assert observed[0][2]["workspace_agent"] == (
        "IndependentTheoryRefereeAgent"
    )
    assert observed[0][2]["workspace_stage"] == (
        "theory_execution_preflight"
    )
    assert observed[2][2]["tool_name"] == "submit"
    assert observed[3][2]["tool_terminal"] is True
    assert observed[3][2]["tool_result_is_error"] is False
