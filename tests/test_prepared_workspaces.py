"""Synthetic interface checks, not live inference or mathematical certification."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from ai_statistician.client_tool_loop import (
    ClientToolExecutionResult,
    ClientToolExecutionContext,
    ClientToolLoopResult,
    run_bounded_client_tool_loop,
    run_client_tool_workspace,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.lean_candidate_revision_tool_loop import (
    LEAN_SCRATCH_TOOL,
    LEAN_SOURCE_SUBMISSION_TOOL,
    prepare_lean_candidate_workspace,
    run_lean_candidate_revision_tool_loop,
)
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnResponse,
)
from ai_statistician.packet_validation import PacketValidationError
from ai_statistician.research_source_discovery import RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_SOURCE_COMMIT_TOOL,
    SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
    prepare_scientific_code_workspace,
    run_scientific_code_workspace,
)
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_COMMIT_TOOL,
    THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
    prepare_theory_artifact_workspace,
    run_theory_artifact_workspace,
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
        return prepare_theory_artifact_workspace, run_theory_artifact_workspace, options, calls, checked
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
        return prepare_lean_candidate_workspace, run_lean_candidate_revision_tool_loop, options, calls, checked

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
    return prepare_scientific_code_workspace, run_scientific_code_workspace, options, calls, checked


@pytest.mark.parametrize("kind", ["theory", "python", "r", "lean"])
def test_prepared_actions_match_default_driver(kind, tmp_path, monkeypatch):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    prepare, run, options, calls, checked = _case(kind, tmp_path / "prepared")
    workspace = prepare(**options)
    assert not checked
    prepared_backend = ScriptedLocalBackend(calls)
    prepared = run_client_tool_workspace(backend=prepared_backend, workspace=workspace)
    actual_checks = deepcopy(checked)

    _, _, default_options, _, default_checks = _case(kind, tmp_path / "default")
    default_backend = ScriptedLocalBackend(calls)
    default = run(provider=default_backend, **default_options)
    assert actual_checks == default_checks
    assert [request.tools for request in prepared_backend.requests] == [
        request.tools for request in default_backend.requests
    ]
    assert prepared.evidence["turns"] == default.evidence["turns"]
    assert prepared.evidence["tool_calls"] == default.evidence["tool_calls"]
    assert prepared.evidence["provider"] == default.evidence["provider"] == "local"
    assert prepared.evidence["model"] == default.evidence["model"] == MODEL
    if kind != "theory":
        assert prepared_backend.requests == default_backend.requests
    if kind in {"python", "r"}:
        assert prepared.code_draft == default.code_draft
        assert prepared.check_result == default.check_result
        assert prepared.evidence["runtime_edited_source"] is False
    elif kind == "lean":
        assert prepared.lean_source == default.lean_source == "opaque model bytes"
        assert prepared.source_hash == default.source_hash
    else:
        assert prepared.evidence["submitted_core_packet_hash"] != ""
        assert prepared.evidence["runtime_edited_theory"] is False
        assert prepared.core_packet["index"] == default.core_packet["index"]


@pytest.mark.parametrize("kind", ["theory", "python", "r", "lean"])
def test_prepared_exhaustion_keeps_owner_checkpoint(kind, tmp_path, monkeypatch):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    prepare, _, options, calls, _ = _case(kind, tmp_path)
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
        prepare, _, options, _, _ = _case(kind, tmp_path / kind)
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
    draft = _case("python", tmp_path / "unused")[3][0].input
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

    prepare, _, options, calls, _ = _case("python", tmp_path)
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
