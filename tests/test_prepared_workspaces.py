"""Synthetic interface checks, not live inference or mathematical certification."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from ai_statistician.client_tool_loop import (
    CLIENT_TOOL_PARENT_SESSION_METADATA_KEY,
    WORKSPACE_HISTORY_TOOL_NAME,
    ClientToolExecutionResult,
    ClientToolExecutionContext,
    ClientToolLoopError,
    ClientToolLoopResult,
    _read_workspace_history,
    client_tool_session_contract_fingerprint,
    load_client_tool_session,
    persist_client_tool_session,
    prepare_shared_client_tool_workspace,
    run_bounded_client_tool_loop,
    run_client_tool_workspace,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.lean_candidate_revision_tool_loop import (
    LEAN_SCRATCH_TOOL,
    LEAN_SOURCE_SUBMISSION_TOOL,
    prepare_lean_candidate_workspace,
)
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.packet_validation import PacketValidationError
from ai_statistician.research_source_discovery import RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_SOURCE_COMMIT_TOOL,
    SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
    SCIENTIFIC_SOURCE_READ_TOOL,
    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
    prepare_scientific_code_workspace,
)
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_COMMIT_TOOL,
    THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
    prepare_theory_artifact_workspace,
    load_theory_workspace_documents,
)


MODEL = "Qwen3-4B-Instruct-2507"


class ScriptedLocalBackend:
    provider_name = "local"

    def __init__(self, calls):
        self.calls = list(calls)
        self.requests = []

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        call = self.calls.pop(0)
        return ClientToolTurnResponse(
            content_blocks=({"type": "tool_use", "id": call.call_id,
                             "name": call.name, "input": dict(call.input)},),
            tool_calls=(call,), text="", provider="local", model=MODEL,
            metadata={"tools_executed_by_backend": False},
        )


def _case(kind, tmp_path):
    checked = []
    options = dict(system_prompt="Use the exposed tools.", user_prompt="Opaque task.",
                   model=MODEL, model_tier="local", temperature=0.0, max_tokens=1024,
                   max_turns=4, max_no_progress_turns=4)
    if kind == "theory":
        options.update(
            max_tool_calls=4, workspace_id="opaque-theory", question_id="opaque-q",
            authoring_binding_id="opaque-author", workspace_operation="initial_authoring",
            initial_artifacts={"index": {}}, initial_documents={"claim.md": "initial"},
            workspace_dir=tmp_path, require_document_authority=True,
            build_candidate=lambda artifacts, changed, manifest, paths: {
                "index": deepcopy(artifacts["index"]), "manifest": manifest,
            }, validate_candidate=lambda packet: [],
        )
        calls = [
            ClientToolCall("write", THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                           {"path": "claim.md", "content": "# Opaque revised claim\n"}),
            ClientToolCall("commit", THEORY_WORKSPACE_COMMIT_TOOL,
                           {"readiness_rationale": "Checkpoint the exact document for review."}),
        ]
        return prepare_theory_artifact_workspace, options, calls, checked
    if kind == "lean":
        def check(source, declaration):
            checked.append((source, declaration))
            return {"source_hash": stable_hash(source), "compiled": True}

        options.update(candidate_id="opaque-lean", candidate_lean_declaration="",
                       initial_source="", check_candidate=check,
                       search_formal_environment=lambda query, count: [])
        calls = [ClientToolCall("submit", LEAN_SOURCE_SUBMISSION_TOOL,
                                {"lean_source": "opaque model bytes",
                                 "candidate_declaration_name": "opaqueTarget"})]
        return prepare_lean_candidate_workspace, options, calls, checked

    def check(draft):
        checked.append(deepcopy(draft))
        return {"code_draft_hash": stable_hash(draft), "accepted": True}

    draft = {
        "language": kind, "execution_profile": "scientific_wasm" if kind == "r" else "stdlib",
        "dependencies": [], "entrypoint": "run_sandbox",
        "code": "run_sandbox <- function(seed, replicates, artifacts) list()\n" if kind == "r"
        else "def run_sandbox(seed, replicates, artifacts):\n    return {}\n",
    }
    options.update(artifact_id="opaque-code", initial_code_draft=None,
                   initial_check_result={}, check_candidate=check,
                   workspace_operation="initial_authoring")
    calls = [ClientToolCall("submit", SCIENTIFIC_SOURCE_SUBMISSION_TOOL, draft),
             ClientToolCall("execute", SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
                            {"reason": "Run exact candidate bytes."}),
             ClientToolCall("commit", SCIENTIFIC_SOURCE_COMMIT_TOOL, {})]
    return prepare_scientific_code_workspace, options, calls, checked


@pytest.mark.parametrize("kind", ["theory", "python", "r", "lean"])
def test_prepared_exhaustion_keeps_owner_checkpoint(kind, tmp_path, monkeypatch):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    prepare, options, calls, _ = _case(kind, tmp_path)
    options["max_turns"] = 1
    if kind == "theory":
        options["max_tool_calls"] = 1
    if kind == "lean":
        calls = [ClientToolCall("scratch", LEAN_SCRATCH_TOOL, {"lean_source": "opaque scratch"})]
    workspace = prepare(**options)
    with pytest.raises(PacketValidationError) as exc:
        run_client_tool_workspace(backend=ScriptedLocalBackend(calls[:1]), workspace=workspace)
    checkpoint = exc.value.recovery_checkpoint
    assert checkpoint.get("accepted") is not True
    if kind in {"python", "r"}:
        assert checkpoint["runtime_edited_source"] is False
        assert checkpoint["resumable"] is True
        assert checkpoint["current_code_draft"]["code"] == calls[0].input["code"]
    elif kind == "lean":
        assert checkpoint["kernel_verified"] is False
        assert checkpoint["resumable"] is True
        assert checkpoint["scratch_checks"] == 1
    else:
        assert checkpoint["kernel_verified"] is False
        assert checkpoint["runtime_edited_theory"] is False
        assert load_theory_workspace_documents(checkpoint)["claim.md"] == calls[0].input["content"]


def test_one_existing_loop_can_use_actual_actions_from_three_workspaces(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    workspaces = {}
    for kind in ("theory", "python", "lean"):
        prepare, options, _, _ = _case(kind, tmp_path / kind)
        workspaces[kind] = prepare(**options)
    selected = {THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL: workspaces["theory"],
                SCIENTIFIC_SOURCE_SUBMISSION_TOOL: workspaces["python"],
                SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL: workspaces["python"],
                LEAN_SCRATCH_TOOL: workspaces["lean"]}
    tools = tuple(tool for owner in workspaces.values() for tool in owner.request.tools
                  if selected.get(tool.name) is owner)
    done = ClientToolDefinition(name="finish_synthetic_check", description="Finish this mechanism check.",
                                input_schema={"type": "object", "properties": {},
                                              "additionalProperties": False}, terminal=True)
    draft = _case("python", tmp_path / "unused")[2][0].input
    calls = [ClientToolCall("scratch", LEAN_SCRATCH_TOOL, {"lean_source": "opaque scratch"}),
             ClientToolCall("submit", SCIENTIFIC_SOURCE_SUBMISSION_TOOL, draft),
             ClientToolCall("write", THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                            {"path": "claim.md", "content": "# Opaque shared-session document\n"}),
             ClientToolCall("execute", SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, {"reason": "Exact bytes."}),
             ClientToolCall("finish", done.name, {})]
    observations = []

    def execute(call, context):
        if call.name == done.name:
            return ClientToolExecutionResult(content={"ok": True}, terminal=True, terminal_payload={})
        result = selected[call.name].execute_tool(call, context)
        observations.append(result)
        return result

    request = replace(workspaces["python"].request, tools=(*tools, done),
                      system_prompt="Use any exposed tool for this synthetic mechanism check.")
    backend = ScriptedLocalBackend(calls)
    loop = run_bounded_client_tool_loop(backend=backend, request=request, execute_tool=execute,
                                       max_turns=5, max_tool_calls=5, max_no_progress_turns=5)
    assert isinstance(loop, ClientToolLoopResult)
    assert loop.turns == 5
    assert all(not result.is_error for result in observations)
    assert loop.runtime_executed_tool_calls == 5
    assert (tmp_path / "theory" / "claim.md").read_text() == calls[2].input["content"]
    assert "opaque scratch" in str(backend.requests[1].messages)
    assert "# Opaque shared-session document" not in str(backend.requests[0].messages)
    assert observations[3].content["accepted"] is True
    # This is executable tool composition, not an independent review or research result.
    assert not any(result.terminal for result in observations)


def test_scientific_result_is_a_snapshot_of_live_prepared_state(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)

    class Discovery:
        def descriptor(self):
            return {"provider": "synthetic", "source_horizon": "2025-01-01"}

        def search(self, query, *, source_kind="all", top_k=5):
            return {"ok": True, "provider": "synthetic", "source_horizon": "2025-01-01",
                    "query_hash": stable_hash(query), "source_kind": source_kind, "results": []}

    prepare, options, calls, _ = _case("python", tmp_path)
    options["research_source_discovery"] = Discovery()
    workspace = prepare(**options)
    result = run_client_tool_workspace(backend=ScriptedLocalBackend(calls), workspace=workspace)
    original = deepcopy(result.evidence)
    observation = workspace.execute_tool(
        ClientToolCall("search", RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
                       {"query": "opaque fresh observation", "source_kind": "all", "top_k": 1}),
        ClientToolExecutionContext(turn_index=4, call_index=0, calls_in_turn=1, total_calls_before=3),
    )
    assert observation.is_error is False
    assert result.evidence == original


def _shared_case(tmp_path, monkeypatch, **overrides):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    workspaces = {}
    checkpoints = []
    checks = {}

    def forbidden_role_result(*args):
        raise AssertionError("a shared conversation must not use an isolated-owner result handler")

    for kind in ("theory", "python", "r", "lean"):
        prepare, options, _, checked = _case(kind, tmp_path / kind)
        workspaces[kind] = replace(prepare(**options), on_success=forbidden_role_result,
                                   on_error=forbidden_role_result)
        checks[kind] = checked
    finish = ClientToolDefinition(
        name="finish_control", description="Return the explicitly selected synthetic study result.",
        input_schema={"type": "object", "properties": {"report": {"type": "string"}},
                      "required": ["report"], "additionalProperties": False}, terminal=True,
    )

    def execute_finish(call, context):
        return ClientToolExecutionResult(content=dict(call.input), terminal=True,
                                         terminal_payload=dict(call.input))

    options = dict(
        request=ClientToolTurnRequest(system_prompt="Use any available action for this synthetic task.",
                                      messages=({"role": "user", "content": "Opaque general task."},),
                                      tools=(), model=MODEL, max_tokens=1024),
        workspaces=workspaces, control_tools=(finish,), execute_control_tool=execute_finish,
        observe_checkpoint=lambda scope, result: checkpoints.append((scope, result)),
        max_turns=15, max_tool_calls=15, max_no_progress_turns=15,
        session_dir=tmp_path / "shared", session_id="opaque-shared-control",
    )
    options.update(overrides)
    return prepare_shared_client_tool_workspace(**options), workspaces, checkpoints, checks


def test_shared_binding_exposes_all_actual_actions_without_role_drivers(tmp_path, monkeypatch):
    workspace, owners, checkpoints, checks = _shared_case(tmp_path, monkeypatch)
    exposed = {tool.name: tool for tool in workspace.request.tools}
    assert list(exposed).count(WORKSPACE_HISTORY_TOOL_NAME) == 1
    assert {tool.name for tool in exposed.values() if tool.terminal} == {"finish_control"}
    assert len(exposed) == 2 + sum(
        sum(tool.name != WORKSPACE_HISTORY_TOOL_NAME for tool in owner.request.tools)
        for owner in owners.values()
    )
    for scope, owner in owners.items():
        for tool in owner.request.tools:
            if tool.name == WORKSPACE_HISTORY_TOOL_NAME:
                continue
            qualified = exposed[scope + "__" + tool.name]
            assert qualified.input_schema == tool.input_schema
            assert qualified.strict == tool.strict
            assert qualified.terminal is False
        assert workspace.request.metadata["shared_component_scopes"][scope][
            "component_request_contract"
        ] == client_tool_session_contract_fingerprint(owner.request)
    assert not checkpoints
    assert all(not value for value in checks.values())
    assert workspace.request.metadata["workspace_context_mode"] == "shared_conversation"
    assert workspace.request.metadata["independent_role_review"] is False


@pytest.mark.parametrize("action_budget", [2, 3])
def test_shared_component_checkpoint_spends_an_ordinary_action_unlike_owner_terminal(tmp_path, monkeypatch, action_budget):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    prepare, options, calls, owner_checks = _case("python", tmp_path / "owner")
    owner = replace(prepare(**options), max_tool_calls=action_budget)
    selected = run_client_tool_workspace(backend=ScriptedLocalBackend(calls), workspace=owner)
    assert selected.evidence["accepted"] is True
    assert len(owner_checks) == 1
    assert selected.evidence["runtime_executed_tool_calls"] == 3

    shared, _, checkpoints, shared_checks = _shared_case(
        tmp_path / "shared", monkeypatch, max_turns=4, max_tool_calls=action_budget,
    )
    backend = ScriptedLocalBackend([
        *[replace(call, name="python__" + call.name) for call in calls],
        ClientToolCall("finish", "finish_control", {"report": "Opaque observations, not science."}),
    ])
    loop = run_client_tool_workspace(backend=backend, workspace=shared)
    assert len(shared_checks["python"]) == 1
    assert len(checkpoints) == int(action_budget == 3)
    assert loop.history[2]["tool_calls"][0]["executed_by_runtime"] is (action_budget == 3)
    assert backend.requests[-1].metadata["client_tool_loop_ordinary_calls_before"] == action_budget
    assert loop.terminal_payload == {"report": "Opaque observations, not science."}
    assert loop.history[-1]["tool_calls"][0]["executed_by_runtime"] is True
    if action_budget == 2:
        assert "workspace_action_budget_exhausted" in loop.history[2]["tool_calls"][0]["result_excerpt"]


def test_shared_session_keeps_raw_feedback_and_component_checkpoints_without_promotion(tmp_path, monkeypatch):
    workspace, owners, checkpoints, checks = _shared_case(tmp_path, monkeypatch)
    python_calls = _case("python", tmp_path / "unused-python")[2]
    r_calls = _case("r", tmp_path / "unused-r")[2]
    lean_call = _case("lean", tmp_path / "unused-lean")[2][0]

    def qualified(scope, call):
        return replace(call, call_id=scope + "-" + call.call_id, name=scope + "__" + call.name)

    calls = [
        qualified("r", r_calls[0]),
        ClientToolCall("write", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                       {"path": "claim.md", "content": "# Shared opaque claim\n"}),
        qualified("lean", lean_call),
        qualified("python", python_calls[0]),
        ClientToolCall("theory-checkpoint", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL,
                       {"readiness_rationale": "Checkpoint these exact files, not a research acceptance."}),
        qualified("r", r_calls[1]), qualified("r", r_calls[2]),
        qualified("python", python_calls[1]), qualified("python", python_calls[2]),
        ClientToolCall("read-python", "python__" + SCIENTIFIC_SOURCE_READ_TOOL, {"line_start": 1, "line_end": 2}),
        # An actual owner input error is observed by this same conversation.
        replace(qualified("python", python_calls[0]), call_id="duplicate-source"),
        ClientToolCall("read-shared-catalog", WORKSPACE_HISTORY_TOOL_NAME, {}),
        ClientToolCall("finish", "finish_control", {"report": "Opaque component observations only."}),
    ]
    backend = ScriptedLocalBackend(calls)
    loop = run_client_tool_workspace(backend=backend, workspace=workspace)
    assert loop.turns == len(calls)
    assert loop.terminal_payload == {"report": "Opaque component observations only."}
    assert {scope for scope, _ in checkpoints} == {"theory", "python", "r", "lean"}
    assert all(result.terminal for _, result in checkpoints)
    assert [row["tool_calls"][0]["terminal"] for row in loop.history] == [False] * (len(calls) - 1) + [True]
    assert len(checks["python"]) == len(checks["r"]) == len(checks["lean"]) == 1
    assert "client_tool_input_rejected" in str(backend.requests[-1].messages)
    assert "byte-identical scientific source is already current" in str(backend.requests[-1].messages)
    assert "opaque model bytes" in str(backend.requests[-1].messages)
    assert (tmp_path / "theory" / "claim.md").read_text() == calls[1].input["content"]
    sessions = list((tmp_path / "shared" / ".client_tool_sessions").glob("*.json"))
    assert len(sessions) == 1
    stored = json.loads(sessions[0].read_text())
    assert stored["session_id"] == workspace.session_id
    assert stored["session_contract_fingerprint"] == client_tool_session_contract_fingerprint(workspace.request)
    assert stored["transcript_fingerprint"] == loop.transcript_fingerprint
    assert stored["messages"] == list(loop.messages)
    assert len(stored["observation_refs"]) == len(calls) - 1
    assert "python__" + SCIENTIFIC_SOURCE_SUBMISSION_TOOL in str(backend.requests[-1].messages)
    assert "observation_sha256" in str(backend.requests[-1].messages)
    for owner in owners.values():
        assert not list((owner.session_dir or tmp_path / "absent").glob(".client_tool_sessions/*.json"))
    checkpoint_tools = {"theory": THEORY_WORKSPACE_COMMIT_TOOL, "lean": LEAN_SOURCE_SUBMISSION_TOOL,
                        "python": SCIENTIFIC_SOURCE_COMMIT_TOOL, "r": SCIENTIFIC_SOURCE_COMMIT_TOOL}
    for scope, checkpoint in checkpoints:
        ref = next(ref for ref in loop.observation_refs
                   if ref["tool_name"] == scope + "__" + checkpoint_tools[scope])
        raw = json.loads((workspace.session_dir / ref["relative_path"]).read_text())
        assert raw["terminal_payload"] == checkpoint.terminal_payload
        assert raw["content"] == checkpoint.content
    before = deepcopy(checkpoints)
    workspace.execute_tool(ClientToolCall("later-read", "python__" + SCIENTIFIC_SOURCE_READ_TOOL,
                                         {"line_start": 1, "line_end": 2}),
                           ClientToolExecutionContext(13, 0, 1, 12))
    assert checkpoints == before


@pytest.mark.parametrize("finish", [True, False])
def test_shared_checkpoint_history_survives_later_source_and_theory_changes(tmp_path, monkeypatch, finish):
    workspace, _, checkpoints, checks = _shared_case(tmp_path, monkeypatch, max_turns=8)
    code_calls = _case("python", tmp_path / "unused")[2]
    earlier_document = "# Opaque claim v1\n"
    later_document = "# Opaque claim v2\n"
    later_draft = {**code_calls[0].input, "code": "def run_sandbox(seed, replicates, artifacts):\n    return {'opaque': 2}\n"}
    calls = [
        ClientToolCall("theory-write-v1", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                       {"path": "claim.md", "content": earlier_document}),
        ClientToolCall("theory-commit-v1", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL,
                       {"readiness_rationale": "First exact document checkpoint."}),
        *[replace(call, name="python__" + call.name) for call in code_calls],
        ClientToolCall("theory-write-v2", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                       {"path": "claim.md", "content": later_document}),
        ClientToolCall("theory-commit-v2", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL,
                       {"readiness_rationale": "Second exact document checkpoint."}),
        ClientToolCall("source-v2-unexecuted", "python__" + SCIENTIFIC_SOURCE_SUBMISSION_TOOL, later_draft),
    ]
    if finish:
        workspace = replace(workspace, max_turns=9)
        calls.append(ClientToolCall("finish", "finish_control", {"report": "No scientific acceptance."}))
        result = run_client_tool_workspace(backend=ScriptedLocalBackend(calls), workspace=workspace)
        assert result.terminal_payload == {"report": "No scientific acceptance."}
    else:
        with pytest.raises(ClientToolLoopError, match="turn budget exhausted") as error:
            run_client_tool_workspace(backend=ScriptedLocalBackend(calls), workspace=workspace)
        result = error.value
    assert len(checks["python"]) == 1  # Later edits were not executed or accepted.
    assert len(checkpoints) == 3
    checkpoints.clear()  # A new reader uses only the existing hash-bound observation store.
    saved = {}
    for ref in result.observation_refs:
        if ref["call_id"] not in {"theory-commit-v1", "theory-commit-v2", "commit"}:
            continue
        observation = _read_workspace_history(
            {"observation_sha256": ref["sha256"]}, session_dir=workspace.session_dir,
            session_id=workspace.session_id, request=workspace.request,
            observation_refs=result.observation_refs,
        )
        assert observation.content["complete"] is True
        assert observation.content["evidence_role"] == "historical_tool_observation_not_current_acceptance"
        saved[ref["call_id"]] = json.loads(observation.content["text"])["terminal_payload"]
    assert load_theory_workspace_documents(saved["theory-commit-v1"]) == {"claim.md": earlier_document}
    assert load_theory_workspace_documents(saved["theory-commit-v2"]) == {"claim.md": later_document}
    assert saved["theory-commit-v1"]["core_packet_hash"] != saved["theory-commit-v2"]["core_packet_hash"]
    assert saved["commit"]["code_draft"] == checks["python"][0]
    assert saved["commit"]["code_draft_hash"] == stable_hash(checks["python"][0])
    assert saved["commit"]["code_draft"] != later_draft
    assert "terminal_payload" not in json.dumps(result.messages)


def test_shared_exhaustion_records_actual_joint_session_not_owner_receipt(tmp_path, monkeypatch):
    workspace, owners, checkpoints, _ = _shared_case(tmp_path, monkeypatch, max_turns=1)
    call = ClientToolCall("write", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                          {"path": "claim.md", "content": "# Partial opaque claim\n"})
    with pytest.raises(ClientToolLoopError) as error:
        run_client_tool_workspace(backend=ScriptedLocalBackend([call]), workspace=workspace)
    assert not checkpoints
    assert error.value.turns == 1
    sessions = list((tmp_path / "shared" / ".client_tool_sessions").glob("*.json"))
    assert len(sessions) == 1
    stored = json.loads(sessions[0].read_text())
    assert stored["messages"] == error.value.messages
    assert stored["session_contract_fingerprint"] == client_tool_session_contract_fingerprint(workspace.request)
    assert (tmp_path / "theory" / "claim.md").read_text() == call.input["content"]
    # A shared transcript does not meet a private owner session's authorization.
    reference = persist_client_tool_session(
        session_dir=workspace.session_dir, session_id=workspace.session_id, request=workspace.request,
        messages=error.value.messages, observation_refs=error.value.observation_refs,
    )
    assert load_client_tool_session(reference, session_dir=workspace.session_dir,
                                    session_id=workspace.session_id, request=workspace.request) == tuple(error.value.messages)
    with pytest.raises(ValueError, match="reference identity mismatch"):
        load_client_tool_session(reference, session_dir=workspace.session_dir,
                                 session_id=workspace.session_id, request=owners["theory"].request)


@pytest.mark.parametrize("change", ["model", "temperature", "scope", "parent", "terminal_collision", "no_terminal"])
def test_shared_preparation_rejects_ambiguous_bindings_before_calls(change, tmp_path, monkeypatch):
    workspace, owners, _, _ = _shared_case(tmp_path, monkeypatch)
    base_request = replace(workspace.request, tools=(), metadata={})
    overrides = {}
    if change in {"model", "temperature"}:
        overrides["request"] = replace(base_request, **{change: "different-model" if change == "model" else 0.7})
    elif change == "scope":
        overrides["workspaces"] = {"theory__python": owners["theory"]}
    elif change == "parent":
        overrides["request"] = replace(base_request, metadata={CLIENT_TOOL_PARENT_SESSION_METADATA_KEY: {"sha256": "other"}})
    elif change == "terminal_collision":
        overrides["control_tools"] = (ClientToolDefinition("theory__" + THEORY_WORKSPACE_COMMIT_TOOL,
                                                             "Opaque final action.", {}, terminal=True),)
    else:
        overrides["control_tools"] = ()
    with pytest.raises(ValueError):
        _shared_case(tmp_path / "invalid", monkeypatch, **overrides)


def test_shared_tools_use_existing_local_wire_transport_with_raw_diagnostics(tmp_path, monkeypatch):
    diagnostic = "opaque native diagnostic\nlocal context: arbitrary alpha / beta\n" * 7
    prepare, options, _, _ = _case("lean", tmp_path / "lean")
    options["check_candidate"] = lambda source, declaration: {
        "source_hash": stable_hash(source), "compiled": False, "stderr": diagnostic,
    }
    workspace, _, checkpoints, _ = _shared_case(
        tmp_path, monkeypatch, workspaces={"lean": prepare(**options)},
    )
    calls = [ClientToolCall("scratch", "lean__" + LEAN_SCRATCH_TOOL, {"lean_source": "opaque source"}),
             ClientToolCall("finish", "finish_control", {"report": "Partial result; no proof."})]
    wire = []

    def complete(_self, payload):
        wire.append(deepcopy(payload))
        call = calls.pop(0)
        return {"model": MODEL, "choices": [{"message": {"content": "", "tool_calls": [
            {"id": call.call_id, "type": "function", "function": {
                "name": call.name, "arguments": json.dumps(dict(call.input)),
            }}]}}]}, {"tools_executed_by_backend": False}

    monkeypatch.setattr(LocalChatGeneratorBackend, "_complete", complete)
    loop = run_client_tool_workspace(backend=LocalChatGeneratorBackend(), workspace=workspace)
    assert loop.provider == "local"
    assert loop.turns == len(wire) == 2
    assert not checkpoints
    assert {tool["function"]["name"] for tool in wire[0]["tools"]} == {
        tool.name for tool in workspace.request.tools
    }
    assert all(payload["model"] == MODEL and payload["max_tokens"] == 1024 for payload in wire)
    result = next(message for message in wire[1]["messages"] if message["role"] == "tool")
    assert result["tool_call_id"] == "scratch"
    decoded = json.loads(result["content"])
    assert decoded["is_error"] is True
    assert json.loads(decoded["content"])["observation"]["stderr"] == diagnostic
    assert loop.terminal_payload == {"report": "Partial result; no proof."}


def test_shared_binding_preserves_nonterminal_result_rejection(tmp_path, monkeypatch):
    _, owners, _, _ = _shared_case(tmp_path, monkeypatch)
    broken = replace(owners["python"], execute_tool=lambda call, context: ClientToolExecutionResult(
        content={"opaque": "not a declared checkpoint"}, terminal=True, terminal_payload={"wrong": True},
    ))
    workspace, _, checkpoints, _ = _shared_case(tmp_path / "control", monkeypatch,
                                               workspaces={"python": broken})
    calls = [ClientToolCall("submit", "python__" + SCIENTIFIC_SOURCE_SUBMISSION_TOOL, {}),
             ClientToolCall("finish", "finish_control", {"report": "No checkpoint accepted."})]
    loop = run_client_tool_workspace(backend=ScriptedLocalBackend(calls), workspace=workspace)
    assert not checkpoints
    assert loop.history[0]["tool_calls"][0]["is_error"] is True
    assert "terminal_result_from_nonterminal_tool" in str(loop.messages)


def test_component_checkpoint_does_not_reset_global_turn_budget(tmp_path, monkeypatch):
    workspace, _, checkpoints, _ = _shared_case(tmp_path, monkeypatch, max_turns=2)
    lean_call = _case("lean", tmp_path / "unused")[2][0]
    calls = [replace(lean_call, name="lean__" + lean_call.name),
             ClientToolCall("write", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                            {"path": "claim.md", "content": "# Partial task\n"}),
             ClientToolCall("finish", "finish_control", {"report": "Should not execute."})]
    backend = ScriptedLocalBackend(calls)
    with pytest.raises(ClientToolLoopError, match="turn budget exhausted") as error:
        run_client_tool_workspace(backend=backend, workspace=workspace)
    assert len(backend.requests) == error.value.turns == 2
    assert [scope for scope, _ in checkpoints] == ["lean"]
    assert len(backend.calls) == 1
