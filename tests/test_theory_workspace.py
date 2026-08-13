from __future__ import annotations

import json

import pytest

from ai_statistician.client_tool_loop import ClientToolInputError
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.scientific_sandbox import ScientificSandboxExecution
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.theory_workspace import (
    THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    THEORY_SCRATCHPAD_TOOL,
    THEORY_WORKSPACE_CHECKPOINT_KIND,
    THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
    THEORY_WORKSPACE_MAX_WRITES_PER_CALL,
    THEORY_WORKSPACE_WRITE_TOOL,
    TheoryScratchpadConfig,
    _replace_theory_workspace_artifacts,
    _theory_workspace_tools,
    run_theory_artifact_workspace,
)


class ScriptedTheoryWorkspaceBackend:
    provider_name = "anthropic"

    def __init__(self, responses: list[ClientToolTurnResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[ClientToolTurnRequest] = []

    def generate_client_tool_turn(
        self,
        request: ClientToolTurnRequest,
    ) -> ClientToolTurnResponse:
        self.requests.append(request)
        return self.responses.pop(0)


def _response(*calls: ClientToolCall) -> ClientToolTurnResponse:
    return ClientToolTurnResponse(
        content_blocks=tuple(
            {
                "type": "tool_use",
                "id": call.call_id,
                "name": call.name,
                "input": dict(call.input),
            }
            for call in calls
        ),
        tool_calls=tuple(calls),
        text="",
        provider="anthropic",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        metadata={"provider_stop_reason": "tool_use"},
    )


def _artifact_writes(artifacts: dict[str, object]) -> dict[str, object]:
    return {
        "writes": [
            {"artifact_name": name, "value": value}
            for name, value in artifacts.items()
        ]
    }


def _run_workspace(backend, **overrides):
    kwargs = {
        "provider": backend,
        "system_prompt": "Use the theory workspace tools.",
        "user_prompt": "Revise the theory from independent observations.",
        "model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        "model_tier": "haiku",
        "temperature": 0.0,
        "max_tokens": 1200,
        "max_turns": 4,
        "max_reads": 2,
        "max_submissions": 2,
        "max_no_progress_turns": 2,
        "workspace_id": "theory-workspace:q1",
        "question_id": "q1",
        "authoring_binding_id": "authoring-binding:q1",
        "workspace_operation": "test_authoring",
        "initial_artifacts": {
            "problem_card": {"claim": "parent-private-claim"},
            "lemma_cards": [],
        },
        "build_candidate": lambda artifacts, changed: {
            "artifacts": dict(artifacts),
            "changed": list(changed),
        },
        "validate_candidate": lambda packet: (
            []
            if packet.get("artifacts", {}).get("problem_card", {}).get("claim")
            == "revised claim"
            and packet.get("artifacts", {}).get("lemma_cards")
            else ["revised claim and at least one lemma are required"]
        ),
    }
    kwargs.update(overrides)
    return run_theory_artifact_workspace(**kwargs)


def test_same_model_revises_workspace_after_raw_validator_observation() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-parent",
                    name="read_theory_workspace",
                    input={
                        "artifact_names": ["problem_card", "lemma_cards"]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-incomplete",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": {"claim": "revised claim"}}
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-complete",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"lemma_cards": [{"id": "lemma-1"}]}
                    ),
                )
            ),
        ]
    )

    result = _run_workspace(backend)

    assert result.core_packet["artifacts"] == {
        "problem_card": {"claim": "revised claim"},
        "lemma_cards": [{"id": "lemma-1"}],
    }
    assert result.evidence["changed_artifact_names"] == [
        "lemma_cards",
        "problem_card",
    ]
    assert result.evidence["reads"] == 1
    assert result.evidence["submissions"] == 2
    assert result.evidence["authoring_binding_id"] == (
        "authoring-binding:q1"
    )
    assert result.evidence["workspace_operation"] == "test_authoring"
    assert result.evidence["model_owned_theory"] is True
    assert result.evidence["runtime_edited_theory"] is False
    assert all(request.enable_prompt_caching for request in backend.requests)
    initial_prompt = str(backend.requests[0].messages[0]["content"])
    assert "parent-private-claim" not in initial_prompt
    assert "parent-private-claim" in str(backend.requests[1].messages)
    assert "revised claim and at least one lemma are required" in str(
        backend.requests[2].messages
    )
    incomplete_write_block = backend.requests[2].messages[-1]["content"][0]
    incomplete_write_observation = json.loads(
        incomplete_write_block["content"]
    )
    assert incomplete_write_observation["write_accepted"] is True
    assert incomplete_write_observation["workspace_valid"] is False
    assert incomplete_write_observation["omitted_artifacts_retained"] is True
    assert incomplete_write_block["is_error"] is False
    write_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == THEORY_WORKSPACE_WRITE_TOOL
    )
    writes_schema = write_schema["properties"]["writes"]
    item_schema = writes_schema["items"]
    assert write_schema["required"] == ["writes"]
    assert writes_schema["minItems"] == 1
    assert item_schema["required"] == ["artifact_name", "value"]
    assert item_schema["properties"]["artifact_name"]["enum"] == [
        "lemma_cards",
        "problem_card",
    ]
    assert item_schema["properties"]["value"]["anyOf"] == [
        {"type": "object"},
        {"type": "array"},
    ]
    write_tool = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == THEORY_WORKSPACE_WRITE_TOOL
    )
    assert write_tool.strict is False


def test_workspace_exhaustion_preserves_model_owned_checkpoint() -> None:
    rejected_call = ClientToolCall(
        call_id="edit-rejected",
        name=THEORY_WORKSPACE_WRITE_TOOL,
        input=_artifact_writes(
            {"problem_card": {"claim": "still invalid"}}
        ),
    )
    backend = ScriptedTheoryWorkspaceBackend([_response(rejected_call)])

    with pytest.raises(PacketValidationError) as exc_info:
        _run_workspace(
            backend,
            max_turns=4,
            max_reads=1,
            max_submissions=1,
            max_no_progress_turns=1,
        )

    checkpoint = exc_info.value.recovery_checkpoint
    assert checkpoint["artifact_kind"] == THEORY_WORKSPACE_CHECKPOINT_KIND
    assert checkpoint["authoring_binding_id"] == "authoring-binding:q1"
    assert checkpoint["workspace_operation"] == "test_authoring"
    assert checkpoint["current_artifacts"]["problem_card"] == {
        "claim": "still invalid"
    }
    assert checkpoint["changed_artifact_names"] == ["problem_card"]
    assert checkpoint["last_validation_errors"] == [
        "revised claim and at least one lemma are required"
    ]
    assert checkpoint["model_owned_theory"] is True
    assert checkpoint["runtime_edited_theory"] is False
    assert checkpoint["kernel_verified"] is False
    assert len(backend.requests) == 1


def test_targeted_revision_uses_atomic_model_owned_artifact_writes() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-revision-inputs",
                    name="read_theory_workspace",
                    input={
                        "artifact_names": ["problem_card", "lemma_cards"]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-related-values",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
        ]
    )

    result = _run_workspace(backend)

    assert result.core_packet["artifacts"] == {
        "problem_card": {"claim": "revised claim"},
        "lemma_cards": [{"id": "lemma-1"}],
    }
    assert result.evidence["write_transport"] == (
        THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT
    )
    assert result.evidence["n_model_artifact_writes"] == 2
    assert result.evidence["model_artifact_writes"] == [
        {
            "submission_index": 0,
            "artifact_name": "problem_card",
            "value_hash": stable_hash({"claim": "revised claim"}),
        },
        {
            "submission_index": 0,
            "artifact_name": "lemma_cards",
            "value_hash": stable_hash([{"id": "lemma-1"}]),
        },
    ]
    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert tool_names == [
        "read_theory_workspace",
        THEORY_WORKSPACE_WRITE_TOOL,
    ]
    prompt = str(backend.requests[0].messages[0]["content"])
    assert "complete model-authored JSON values" in prompt
    assert "without merging, patching, or inventing content" in prompt
    write_tool = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == THEORY_WORKSPACE_WRITE_TOOL
    )
    assert "does not merge or infer content" in write_tool.description


def test_same_theory_model_runs_exact_scratch_source_then_revises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    source = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'counterexample_gap': 0.25, 'seed': seed}\n"
    )
    captured: dict[str, object] = {}

    def fake_execute_scientific_sandbox(**kwargs):
        captured.update(kwargs)
        return ScientificSandboxExecution(
            status="EXECUTED",
            language="python",
            execution_profile="scientific_wasm",
            backend="pyodide",
            isolation_provider="test-isolation",
            dependencies=("numpy",),
            execution_attempted=True,
            returncode=0,
            metrics={"counterexample_gap": 0.25, "seed": 17},
            errors=(),
            stdout_summary="exact scratch stdout",
            stderr_summary="",
            result_parse_error="",
            code_path=str(tmp_path / "scratch.py"),
            request_path=str(tmp_path / "request.json"),
            result_path=str(tmp_path / "result.json"),
            code_hash=stable_hash(source),
            request_hash="scratch-request-hash",
            result_hash=stable_hash(
                {"counterexample_gap": 0.25, "seed": 17}
            ),
            subprocess_environment_keys=("HOME", "PATH"),
            resource_limits={"cpu_seconds": 9},
        )

    monkeypatch.setattr(
        "ai_statistician.theory_workspace.execute_scientific_sandbox",
        fake_execute_scientific_sandbox,
    )
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="run-counterexample",
                    name=THEORY_SCRATCHPAD_TOOL,
                    input={
                        "language": "python",
                        "execution_profile": "scientific_wasm",
                        "dependencies": ["numpy"],
                        "entrypoint": "run_sandbox",
                        "code": source,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="revise-from-counterexample",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [
                                {"id": "counterexample-qualified-lemma"}
                            ],
                        }
                    ),
                )
            ),
        ]
    )

    result = _run_workspace(
        backend,
        scratchpad=TheoryScratchpadConfig(
            sandbox_dir=tmp_path / "theory-scratch",
            seed=17,
            replicates=12,
            timeout_s=9,
            max_runs=1,
        ),
    )

    assert captured["code"] == source
    assert captured["language"] == "python"
    assert captured["dependencies"] == ["numpy"]
    assert captured["seed"] == 17
    assert captured["replicates"] == 12
    assert captured["timeout_s"] == 9
    assert captured["max_output_bytes"] == 64 * 1024
    assert result.core_packet["artifacts"]["problem_card"]["claim"] == (
        "revised claim"
    )
    assert result.evidence["scratchpad_enabled"] is True
    assert result.evidence["scratch_runs"] == 1
    scratch = result.evidence["scratch_execution_refs"][0]
    assert scratch["metrics_hash"] == stable_hash(
        {"counterexample_gap": 0.25, "seed": 17}
    )
    assert scratch["code_hash"] == stable_hash(source)
    assert scratch["runtime_edited_source"] is False
    assert scratch["runtime_edited_theory"] is False
    assert scratch["proof_evidence_status"] == (
        THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE
    )
    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert tool_names == [
        "read_theory_workspace",
        THEORY_SCRATCHPAD_TOOL,
        THEORY_WORKSPACE_WRITE_TOOL,
    ]
    first_prompt = str(backend.requests[0].messages[0]["content"])
    assert "Never promote finite scratch output" in first_prompt
    observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert observation["status"] == "EXECUTED"
    assert observation["metrics"]["counterexample_gap"] == 0.25
    assert observation["proof_evidence_status"] == (
        THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE
    )
    assert "not confirmatory simulation" in observation["boundary"]


def test_targeted_revision_retains_valid_edits_across_raw_validator_feedback() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="edit-incomplete",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": {"claim": "revised claim"}}
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-after-observation",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"lemma_cards": [{"id": "lemma-1"}]}
                    ),
                )
            ),
        ]
    )

    result = _run_workspace(backend)

    assert result.evidence["submissions"] == 2
    assert result.evidence["n_model_artifact_writes"] == 2
    assert [
        row["submission_index"]
        for row in result.evidence["model_artifact_writes"]
    ] == [0, 1]
    assert "revised claim and at least one lemma are required" in str(
        backend.requests[1].messages
    )
    observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert observation["write_accepted"] is True
    assert observation["workspace_valid"] is False
    assert observation["write_transport"] == (
        THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT
    )


def test_targeted_revision_rejects_noop_edit_then_returns_observation() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="noop-edit",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {
                                "claim": "parent-private-claim"
                            }
                        }
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="substantive-edit-after-noop",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
        ]
    )

    result = _run_workspace(backend)

    assert result.evidence["submissions"] == 2
    assert result.evidence["n_model_artifact_writes"] == 2
    no_op_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert no_op_observation["state_changed"] is False
    assert no_op_observation["workspace_valid"] is False
    assert no_op_observation["validation_errors"] == [
        "the submitted theory workspace is unchanged from its parent"
    ]


def test_targeted_revision_rejects_invalid_artifact_shape_atomically() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="invalid-atomic-edit",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": ["invalid object replacement"]}
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="valid-atomic-edit",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
        ]
    )

    result = _run_workspace(backend)

    assert result.core_packet["artifacts"]["problem_card"] == {
        "claim": "revised claim"
    }
    assert result.evidence["submissions"] == 1
    assert result.evidence["n_model_artifact_writes"] == 2
    rejected_observation = backend.requests[1].messages[-1]["content"][0]
    assert rejected_observation["is_error"] is True
    rejected_payload = json.loads(rejected_observation["content"])
    assert rejected_payload["error"] == "client_tool_input_rejected"
    assert "problem_card to remain object" in rejected_payload["detail"]


def test_targeted_revision_rejects_duplicate_artifact_names_atomically() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="duplicate-artifact-edit",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input={
                        "writes": [
                            {
                                "artifact_name": "problem_card",
                                "value": {"claim": "first revision"},
                            },
                            {
                                "artifact_name": "problem_card",
                                "value": {"claim": "second revision"},
                            },
                        ]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="valid-edit-after-duplicate",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
        ]
    )

    result = _run_workspace(backend)

    assert result.core_packet["artifacts"]["problem_card"] == {
        "claim": "revised claim"
    }
    assert result.evidence["submissions"] == 1
    rejected_observation = backend.requests[1].messages[-1]["content"][0]
    assert rejected_observation["is_error"] is True
    rejected_payload = json.loads(rejected_observation["content"])
    assert rejected_payload["error"] == "client_tool_input_rejected"
    assert "repeats 'problem_card'" in rejected_payload["detail"]


def test_theory_workspace_bounds_each_complete_write_batch() -> None:
    tools = _theory_workspace_tools(
        {
            "problem_card": "object",
            "lemma_cards": "array",
            "theorem_cards": "array",
        },
        {
            "problem_card": "object",
            "lemma_cards": "array",
            "theorem_cards": "array",
        },
        scratchpad_enabled=False,
    )
    write_tool = next(tool for tool in tools if tool.name == THEORY_WORKSPACE_WRITE_TOOL)

    assert write_tool.input_schema["properties"]["writes"]["maxItems"] == (
        THEORY_WORKSPACE_MAX_WRITES_PER_CALL
    )

    with pytest.raises(ClientToolInputError, match="at most two"):
        _replace_theory_workspace_artifacts(
            {
                "problem_card": {},
                "lemma_cards": [],
                "theorem_cards": [],
            },
            [
                {"artifact_name": "problem_card", "value": {"claim": "x"}},
                {"artifact_name": "lemma_cards", "value": [{"id": "l"}]},
                {"artifact_name": "theorem_cards", "value": [{"id": "t"}]},
            ],
            writable_artifact_shapes={
                "problem_card": "object",
                "lemma_cards": "array",
                "theorem_cards": "array",
            },
        )
