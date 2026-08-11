from __future__ import annotations

import pytest

from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_CHECKPOINT_KIND,
    run_theory_revision_workspace,
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
        "revision_binding_id": "revision-binding:q1",
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
    return run_theory_revision_workspace(**kwargs)


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
                    name="submit_theory_workspace_revision",
                    input={
                        "problem_card": {"claim": "revised claim"},
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="submit-complete",
                    name="submit_theory_workspace_revision",
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
    assert result.evidence["model_owned_theory"] is True
    assert result.evidence["runtime_edited_theory"] is False
    initial_prompt = str(backend.requests[0].messages[0]["content"])
    assert "parent-private-claim" not in initial_prompt
    assert "parent-private-claim" in str(backend.requests[1].messages)
    assert "revised claim and at least one lemma are required" in str(
        backend.requests[2].messages
    )
    submission_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == "submit_theory_workspace_revision"
    )
    assert submission_schema["properties"]["problem_card"]["type"] == (
        "object"
    )
    assert submission_schema["properties"]["lemma_cards"]["type"] == "array"
    assert "replacements" not in submission_schema["properties"]


def test_workspace_exhaustion_preserves_model_owned_checkpoint() -> None:
    rejected_call = ClientToolCall(
        call_id="submit-rejected",
        name="submit_theory_workspace_revision",
        input={
            "problem_card": {"claim": "still invalid"},
        },
    )
    backend = ScriptedTheoryWorkspaceBackend(
        [_response(rejected_call), _response(rejected_call)]
    )

    with pytest.raises(PacketValidationError) as exc_info:
        _run_workspace(
            backend,
            max_turns=1,
            max_reads=1,
            max_submissions=1,
            max_no_progress_turns=1,
        )

    checkpoint = exc_info.value.recovery_checkpoint
    assert checkpoint["artifact_kind"] == THEORY_WORKSPACE_CHECKPOINT_KIND
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
