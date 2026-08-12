from __future__ import annotations

import json

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_CHECKPOINT_KIND,
    THEORY_WORKSPACE_JSON_PATCH_TRANSPORT,
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


def _run_patch_workspace(backend, **overrides):
    return _run_workspace(
        backend,
        workspace_operation="targeted_revision",
        write_transport=THEORY_WORKSPACE_JSON_PATCH_TRANSPORT,
        **overrides,
    )


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
                    call_id="submit-incomplete",
                    name="submit_theory_artifacts",
                    input={
                        "problem_card": {"claim": "revised claim"},
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="submit-complete",
                    name="submit_theory_artifacts",
                    input={
                        "lemma_cards": [{"id": "lemma-1"}],
                    },
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
    submission_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == "submit_theory_artifacts"
    )
    assert submission_schema["properties"]["problem_card"]["type"] == (
        "object"
    )
    assert submission_schema["properties"]["lemma_cards"]["type"] == "array"
    assert "replacements" not in submission_schema["properties"]


def test_workspace_exhaustion_preserves_model_owned_checkpoint() -> None:
    rejected_call = ClientToolCall(
        call_id="submit-rejected",
        name="submit_theory_artifacts",
        input={
            "problem_card": {"claim": "still invalid"},
        },
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


def test_targeted_revision_uses_atomic_model_owned_json_edits() -> None:
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
                    name="edit_theory_workspace",
                    input={
                        "operations": [
                            {
                                "op": "replace",
                                "artifact_name": "problem_card",
                                "path": "/claim",
                                "value": "revised claim",
                            },
                            {
                                "op": "add",
                                "artifact_name": "lemma_cards",
                                "path": "/-",
                                "value": {"id": "lemma-1"},
                            },
                        ]
                    },
                )
            ),
        ]
    )

    result = _run_patch_workspace(backend)

    assert result.core_packet["artifacts"] == {
        "problem_card": {"claim": "revised claim"},
        "lemma_cards": [{"id": "lemma-1"}],
    }
    assert result.evidence["write_transport"] == (
        THEORY_WORKSPACE_JSON_PATCH_TRANSPORT
    )
    assert result.evidence["n_model_edit_operations"] == 2
    assert result.evidence["model_edit_operations"] == [
        {
            "submission_index": 0,
            "operation_index": 0,
            "op": "replace",
            "artifact_name": "problem_card",
            "path": "/claim",
            "value_hash": stable_hash("revised claim"),
        },
        {
            "submission_index": 0,
            "operation_index": 1,
            "op": "add",
            "artifact_name": "lemma_cards",
            "path": "/-",
            "value_hash": stable_hash({"id": "lemma-1"}),
        },
    ]
    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert tool_names == [
        "read_theory_workspace",
        "edit_theory_workspace",
    ]
    assert "submit_theory_artifacts" not in tool_names
    prompt = str(backend.requests[0].messages[0]["content"])
    assert "RFC 6902" in prompt
    assert "runtime applies those exact operations" in prompt


def test_targeted_revision_retains_valid_edits_across_raw_validator_feedback() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="edit-incomplete",
                    name="edit_theory_workspace",
                    input={
                        "operations": [
                            {
                                "op": "replace",
                                "artifact_name": "problem_card",
                                "path": "/claim",
                                "value": "revised claim",
                            }
                        ]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-after-observation",
                    name="edit_theory_workspace",
                    input={
                        "operations": [
                            {
                                "op": "add",
                                "artifact_name": "lemma_cards",
                                "path": "/-",
                                "value": {"id": "lemma-1"},
                            }
                        ]
                    },
                )
            ),
        ]
    )

    result = _run_patch_workspace(backend)

    assert result.evidence["submissions"] == 2
    assert result.evidence["n_model_edit_operations"] == 2
    assert [
        row["submission_index"]
        for row in result.evidence["model_edit_operations"]
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
        THEORY_WORKSPACE_JSON_PATCH_TRANSPORT
    )


def test_targeted_revision_rejects_noop_edit_then_returns_observation() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="noop-edit",
                    name="edit_theory_workspace",
                    input={
                        "operations": [
                            {
                                "op": "replace",
                                "artifact_name": "problem_card",
                                "path": "/claim",
                                "value": "parent-private-claim",
                            }
                        ]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="substantive-edit-after-noop",
                    name="edit_theory_workspace",
                    input={
                        "operations": [
                            {
                                "op": "replace",
                                "artifact_name": "problem_card",
                                "path": "/claim",
                                "value": "revised claim",
                            },
                            {
                                "op": "add",
                                "artifact_name": "lemma_cards",
                                "path": "/-",
                                "value": {"id": "lemma-1"},
                            },
                        ]
                    },
                )
            ),
        ]
    )

    result = _run_patch_workspace(backend)

    assert result.evidence["submissions"] == 2
    assert result.evidence["n_model_edit_operations"] == 2
    no_op_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert no_op_observation["state_changed"] is False
    assert no_op_observation["workspace_valid"] is False
    assert no_op_observation["validation_errors"] == [
        "the submitted theory workspace is unchanged from its parent"
    ]


def test_targeted_revision_rejects_invalid_patch_atomically() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="invalid-atomic-edit",
                    name="edit_theory_workspace",
                    input={
                        "operations": [
                            {
                                "op": "replace",
                                "artifact_name": "problem_card",
                                "path": "/claim",
                                "value": "must not persist",
                            },
                            {
                                "op": "remove",
                                "artifact_name": "problem_card",
                                "path": "/missing",
                            },
                        ]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="valid-atomic-edit",
                    name="edit_theory_workspace",
                    input={
                        "operations": [
                            {
                                "op": "replace",
                                "artifact_name": "problem_card",
                                "path": "/claim",
                                "value": "revised claim",
                            },
                            {
                                "op": "add",
                                "artifact_name": "lemma_cards",
                                "path": "/-",
                                "value": {"id": "lemma-1"},
                            },
                        ]
                    },
                )
            ),
        ]
    )

    result = _run_patch_workspace(backend)

    assert result.core_packet["artifacts"]["problem_card"] == {
        "claim": "revised claim"
    }
    assert result.evidence["submissions"] == 1
    assert result.evidence["n_model_edit_operations"] == 2
    rejected_observation = backend.requests[1].messages[-1]["content"][0]
    assert rejected_observation["is_error"] is True
    rejected_payload = json.loads(rejected_observation["content"])
    assert rejected_payload["error"] == "client_tool_input_rejected"
    assert "non-existent object 'missing'" in rejected_payload["detail"]
