from __future__ import annotations

from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.scientific_code_workspace import (
    run_scientific_code_workspace,
)


class ScriptedScientificBackend:
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


def test_same_model_rewrites_complete_source_from_raw_sandbox_observation() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "code": "def run_estimator(data):\n    return missing_name\n",
    }
    revised = {
        **initial,
        "code": "def run_estimator(data):\n    return 0.0\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="replace-1",
                    name="replace_scientific_source",
                    input=revised,
                ),
                ClientToolCall(
                    call_id="run-1",
                    name="run_scientific_source",
                    input={},
                ),
            )
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        row = dict(candidate)
        checked.append(row)
        return {
            "code_draft_hash": stable_hash(row),
            "accepted": row == revised,
            "stdout": "{\"estimate\":0.0}",
            "stderr": "",
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Implement the exact estimator.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_source_updates=2,
        max_checks=2,
        max_no_progress_turns=2,
        artifact_id="question:estimator",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stdout": "",
            "stderr": "NameError: missing_name",
        },
        check_candidate=check,
    )

    assert dict(result.code_draft) == revised
    assert checked == [revised]
    assert result.evidence["model_owned_source"] is True
    assert result.evidence["runtime_edited_source"] is False
    assert result.evidence["initial_check_accepted"] is False
    assert result.evidence["source_changed"] is True
    assert result.evidence["parent_code_draft_hash"] != result.evidence[
        "submitted_code_draft_hash"
    ]
    assert result.evidence["runtime_executed_tool_calls"] == 2
    assert "NameError: missing_name" in str(backend.requests[0].messages)
    assert {tool.name for tool in backend.requests[0].tools} == {
        "replace_scientific_source",
        "run_scientific_source",
    }
