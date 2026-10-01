"""Research-control state/execution tests, not mathematical or model efficacy."""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from ai_statistician.client_tool_loop import (
    ClientToolLoopError,
    read_hash_bound_utf8_file,
    run_client_tool_workspace,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.model_backend import ClientToolCall, ClientToolTurnRequest, ClientToolTurnResponse
from ai_statistician.research_control import RESEARCH_CONTROL_SUBMISSION_TOOL, prepare_research_control_workspace
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_SOURCE_COMMIT_TOOL, SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
    SCIENTIFIC_SOURCE_SUBMISSION_TOOL, prepare_scientific_code_workspace,
)
from ai_statistician.scientific_sandbox import (
    ScientificInputArtifactBinding, discover_scientific_sandbox_runtime, execute_scientific_sandbox,
)
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_COMMIT_TOOL, THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
    load_theory_workspace_documents, prepare_theory_artifact_workspace,
)


MODEL = "Qwen3-4B-Instruct-2507"


def _checkpoint_refs(messages):
    refs = {}
    for message in messages:
        if message.get("role") != "user" or not isinstance(message.get("content"), list):
            continue
        for block in message["content"]:
            if block.get("type") != "tool_result" or not isinstance(block.get("content"), list):
                continue
            for part in block["content"]:
                value = json.loads(part["text"])
                if "shared_checkpoint_ref" in value:
                    ref = value["shared_checkpoint_ref"]
                    refs.setdefault(ref["scope"], []).append(ref)
    return refs


class ScriptedBackend:
    provider_name = "local"

    def __init__(self, calls):
        self.calls = list(calls)
        self.requests = []

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        item = self.calls.pop(0)
        call = item(request) if callable(item) else item
        return ClientToolTurnResponse(
            content_blocks=({"type": "tool_use", "id": call.call_id,
                             "name": call.name, "input": dict(call.input)},),
            tool_calls=(call,), text="", provider="local", model=MODEL,
            metadata={"tools_executed_by_backend": False},
        )


def _control(tmp_path, monkeypatch, language, *, workflow="", max_turns=12):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    current_theory = {}
    executions = []

    def forbidden(*args):
        raise AssertionError("shared controls cannot manufacture an isolated-owner result")

    theory = prepare_theory_artifact_workspace(
        system_prompt="Private specialist system prompt.", user_prompt="Private specialist instruction.",
        model=MODEL, model_tier="local", temperature=0, max_tokens=1024,
        max_turns=12, max_tool_calls=12, max_no_progress_turns=12,
        workspace_id="opaque-theory", question_id="opaque-q", authoring_binding_id="opaque-binding",
        workspace_operation="initial_authoring", initial_artifacts={"index": {}},
        initial_documents={"claim.md": "initial opaque text"}, workspace_dir=tmp_path / "theory",
        require_document_authority=True,
        build_candidate=lambda artifacts, changed, manifest, paths: {"theory_workspace_manifest": manifest},
        validate_candidate=lambda packet: [],
    )

    def check(draft):
        documents = load_theory_workspace_documents(current_theory["payload"])
        content = documents["claim.md"]
        sha = hashlib.sha256(content.encode()).hexdigest()
        execution = execute_scientific_sandbox(
            sandbox_dir=tmp_path / "executions" / str(len(executions)), artifact_id="opaque-code",
            language=draft["language"], code=draft["code"], dependencies=draft["dependencies"],
            project_files=draft.get("project_files", []), seed=3, replicates=1, timeout_s=30,
            input_artifacts=(ScientificInputArtifactBinding("claim.md", content, sha, "text/markdown"),),
        )
        executions.append(execution)
        return {"code_draft_hash": stable_hash(draft), "accepted": execution.status == "EXECUTED",
                "checkpoint_inputs": {"theory": current_theory["hash"]}, "execution": execution.to_json()}

    scientific = prepare_scientific_code_workspace(
        system_prompt="Private source-owner prompt.", user_prompt="Private source-owner instruction.",
        model=MODEL, model_tier="local", temperature=0, max_tokens=1024,
        max_turns=12, max_no_progress_turns=12, artifact_id="opaque-code",
        initial_code_draft=None, initial_check_result={}, check_candidate=check,
        workspace_operation="initial_authoring", session_dir=tmp_path / "code",
    )

    def inputs(scope, payload):
        if scope == "theory":
            current_theory.update(hash=stable_hash(payload), payload=deepcopy(payload))
            return {}
        return payload["check_result"]["checkpoint_inputs"]

    question = OpenResearchQuestion("opaque-q", "Opaque objective", "Opaque task, not a statistical benchmark.",
                                    task_intent={"theory": "required", "formal": "optional"})
    workspace = prepare_research_control_workspace(
        question=question,
        request=ClientToolTurnRequest(system_prompt="Common public research objective.",
                                      messages=({"role": "user", "content": "Common task access."},),
                                      tools=(), model=MODEL, max_tokens=1024),
        workspaces={"theory": replace(theory, on_success=forbidden, on_error=forbidden),
                    "code": replace(scientific, on_success=forbidden, on_error=forbidden)},
        checkpoint_inputs=inputs, session_dir=tmp_path / "control", session_id="opaque-control",
        max_turns=max_turns, max_tool_calls=max_turns, max_no_progress_turns=max_turns,
        workflow_instructions=workflow,
    )
    draft = {"language": language, "execution_profile": "stdlib" if language == "python" else "scientific_wasm",
             "dependencies": [], "entrypoint": "run_sandbox", "code": (
                 "def run_sandbox(seed, replicates, artifacts):\n    return {'length': len(artifacts['claim.md']['content'])}\n"
                 if language == "python" else
                 "run_sandbox <- function(seed, replicates, artifacts) list(length=nchar(artifacts[['claim.md']]$content))\n")}
    calls = [
        ClientToolCall("write-v1", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                       {"path": "claim.md", "content": "# Opaque version one\n"}),
        ClientToolCall("commit-v1", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL,
                       {"readiness_rationale": "Save this exact working document."}),
        ClientToolCall("source", "code__" + SCIENTIFIC_SOURCE_SUBMISSION_TOOL, draft),
        ClientToolCall("execute", "code__" + SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, {"reason": "Inspect exact input bytes."}),
        ClientToolCall("code-commit", "code__" + SCIENTIFIC_SOURCE_COMMIT_TOOL, {}),
        ClientToolCall("write-v2", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                       {"path": "claim.md", "content": "# A different opaque version two\n"}),
        ClientToolCall("commit-v2", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL,
                       {"readiness_rationale": "Save another exact document checkpoint."}),
    ]
    return workspace, question, calls, executions


@pytest.mark.parametrize("language", ["python", "r"])
def test_control_runs_exact_inputs_and_rejects_a_stale_final_join(tmp_path, monkeypatch, language):
    runtime = discover_scientific_sandbox_runtime()
    if not (runtime.python_available if language == "python" else runtime.r_available):
        pytest.skip("pinned scientific runtime is not installed")
    workspace, question, calls, executions = _control(tmp_path, monkeypatch, language)
    frozen_intent = deepcopy(question.task_intent)
    question.task_intent["formal"] = "not_applicable"  # Cannot change the frozen submission intent.
    report = "# Opaque submission\n\nThese are working artifacts, not a certified research result.\n"

    def submit(request, *, stale):
        refs = _checkpoint_refs(request.messages)
        return ClientToolCall("stale" if stale else "consistent", RESEARCH_CONTROL_SUBMISSION_TOOL,
                              {"report_markdown": report, "selected_checkpoints": {
                                  "theory": refs["theory"][-1 if stale else 0]["payload_hash"],
                                  "code": refs["code"][0]["payload_hash"],
                              }})

    backend = ScriptedBackend([*calls, lambda req: submit(req, stale=True), lambda req: submit(req, stale=False)])
    result = run_client_tool_workspace(backend=backend, workspace=workspace)
    assert len(executions) == 1
    assert executions[0].status == "EXECUTED"
    assert executions[0].metrics == {"length": len(calls[0].input["content"])}
    assert Path(executions[0].code_path).read_text() == calls[2].input["code"]
    assert executions[0].input_artifact_hashes == {"claim.md": hashlib.sha256(calls[0].input["content"].encode()).hexdigest()}
    assert "selected checkpoint inputs do not match" in str(backend.requests[-1].messages)
    assert result.turns == 9
    assert result.terminal_payload["task_intent"] == frozen_intent
    assert result.terminal_payload["control_mode"] == "free_planning"
    assert result.terminal_payload["independent_role_review"] is False
    assert result.terminal_payload["evidence_role"] == "submission_not_scientific_acceptance"
    body, errors = read_hash_bound_utf8_file(result.terminal_payload["report_ref"])
    assert not errors and body == report
    selection = result.terminal_payload["selected_checkpoints"]
    assert selection["code"]["inputs"] == {"theory": selection["theory"]["payload_hash"]}
    assert "Private specialist" not in str(backend.requests[0])
    assert "Private source-owner" not in str(backend.requests[0])
    assert "mathematical_documents" in str(backend.requests[0].messages)
    assert "Opaque task" in str(backend.requests[0].messages)
    assert not list((tmp_path / "theory" / ".client_tool_sessions").glob("*.json"))


def test_same_workflow_control_records_explicit_instructions_without_independent_review(tmp_path, monkeypatch):
    workspace, _, _, executions = _control(tmp_path, monkeypatch, "python", workflow="Opaque declared workflow.")
    call = ClientToolCall("submit", RESEARCH_CONTROL_SUBMISSION_TOOL,
                          {"selected_checkpoints": {}, "report_markdown": "# Honest partial submission\n"})
    result = run_client_tool_workspace(backend=ScriptedBackend([call]), workspace=workspace)
    assert result.terminal_payload["control_mode"] == "same_workflow"
    assert result.terminal_payload["selected_checkpoints"] == {}
    assert result.terminal_payload["independent_role_review"] is False
    assert workspace.request.metadata["workflow_instructions_hash"] == stable_hash("Opaque declared workflow.")
    assert "Opaque declared workflow." in str(workspace.request.messages)
    assert not executions


def test_control_exhaustion_preserves_refs_without_auto_submitting_a_report(tmp_path, monkeypatch):
    workspace, _, calls, executions = _control(tmp_path, monkeypatch, "python", max_turns=2)
    with pytest.raises(ClientToolLoopError, match="turn budget exhausted") as error:
        run_client_tool_workspace(backend=ScriptedBackend(calls[:2]), workspace=workspace)
    assert len(error.value.observation_refs) == 2
    raw = json.loads((workspace.session_dir / error.value.observation_refs[-1]["relative_path"]).read_text())
    ref = json.loads(raw["model_content_blocks"][0]["text"])["shared_checkpoint_ref"]
    assert ref["scope"] == "theory" and ref["payload_hash"] == stable_hash(raw["terminal_payload"])
    assert len(list((workspace.session_dir / ".client_tool_sessions").glob("*.json"))) == 1
    assert not (workspace.session_dir / ".client_tool_sessions" / "reports").exists()
    assert not executions


@pytest.mark.skipif(os.environ.get("AI_STATISTICIAN_LOCAL_MODEL_CONFORMANCE") != "1",
                    reason="opt-in pinned local Qwen, synthetic control conformance only")
def test_live_local_control_selects_its_actual_checkpoint_and_writes_a_report(tmp_path, monkeypatch):
    workspace, _, _, executions = _control(tmp_path, monkeypatch, "python", max_turns=8)
    workspace = replace(workspace, request=replace(workspace.request, messages=(*workspace.request.messages, {
        "role": "user", "content": (
            "Transport conformance only, not research. Write probe.md with the exact text "
            "'opaque observation' using theory__write_theory_document, then commit that theory "
            "checkpoint. Finally use submit_research_result with a Markdown report and select "
            "the theory payload_hash from the shared_checkpoint_ref you actually receive. "
            "No code or scientific execution is requested."
        ),
    })))
    result = run_client_tool_workspace(backend=LocalChatGeneratorBackend(timeout_s=120), workspace=workspace)
    assert result.model == MODEL and result.provider == "local"
    assert result.terminal_payload["selected_checkpoints"]["theory"]["payload_hash"]
    assert result.terminal_payload["evidence_role"] == "submission_not_scientific_acceptance"
    report, errors = read_hash_bound_utf8_file(result.terminal_payload["report_ref"])
    assert not errors and report.strip()
    assert "opaque observation" in (tmp_path / "theory" / "probe.md").read_text()
    assert not executions
    print(json.dumps({"scope": "synthetic_native_control_conformance_not_scientific_evidence",
                      "turns": result.turns, "tool_calls": result.tool_calls,
                      "usage": result.provider_usage, "transcript_fingerprint": result.transcript_fingerprint,
                      "workspace": str(workspace.session_dir)}, sort_keys=True))
