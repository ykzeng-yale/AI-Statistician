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
        "entrypoint": "run_sandbox",
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
    replace_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == "replace_scientific_source"
    )
    assert "required_estimator_ids" not in replace_schema["properties"]


def test_same_model_authors_initial_source_before_sandbox_execution() -> None:
    authored = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": (
            "def run_estimator(request):\n"
            "    return {'estimate': 0.0}\n\n"
            "def run_sandbox(seed, replicates):\n"
            "    return run_estimator({})\n"
        ),
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="author-1",
                    name="replace_scientific_source",
                    input=authored,
                )
            ),
            _response(
                ClientToolCall(
                    call_id="run-1",
                    name="run_scientific_source",
                    input={},
                )
            ),
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Author the estimator from the bound theory contract.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:initial-estimator",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == authored,
            "stdout": "{\"estimate\":0.0}",
            "stderr": "",
        },
        workspace_operation="initial_authoring",
    )

    assert dict(result.code_draft) == authored
    assert result.evidence["workspace_operation"] == "initial_authoring"
    assert result.evidence["parent_code_draft_hash"] == ""
    assert result.evidence["source_updates"] == 1
    assert result.evidence["sandbox_checks"] == 1
    assert [tool.name for tool in backend.requests[0].tools] == [
        "replace_scientific_source"
    ]
    assert {tool.name for tool in backend.requests[1].tools} == {
        "replace_scientific_source",
        "run_scientific_source",
    }


def test_byte_identical_replacement_is_returned_to_same_model_as_noop() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 0}\n",
    }
    revised = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 1}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="noop-1",
                    name="replace_scientific_source",
                    input=initial,
                )
            ),
            _response(
                ClientToolCall(
                    call_id="replace-2",
                    name="replace_scientific_source",
                    input=revised,
                ),
                ClientToolCall(
                    call_id="run-2",
                    name="run_scientific_source",
                    input={},
                ),
            ),
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise the failed source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:no-op-replacement",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "assertion failed",
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == revised,
        },
    )

    assert dict(result.code_draft) == revised
    assert result.evidence["source_updates"] == 1
    noop = result.evidence["history"][0]["tool_calls"][0]
    assert noop["is_error"] is True
    assert "byte-identical" in noop["result_excerpt"]
    assert "byte-identical" in str(backend.requests[1].messages)


def test_global_budget_does_not_revoke_scientific_edit_or_execution() -> None:
    drafts = [
        {
            "language": "python",
            "execution_profile": "stdlib",
            "dependencies": [],
            "entrypoint": "run_sandbox",
            "code": (
                "def run_sandbox(seed, replicates):\n"
                f"    return {{'attempt': {index}}}\n"
            ),
        }
        for index in range(5)
    ]
    backend = ScriptedScientificBackend(
        [
            response
            for index, draft in enumerate(drafts)
            for response in (
                _response(
                    ClientToolCall(
                        call_id=f"replace-{index}",
                        name="replace_scientific_source",
                        input=draft,
                    )
                ),
                _response(
                    ClientToolCall(
                        call_id=f"run-{index}",
                        name="run_scientific_source",
                        input={},
                    )
                ),
            )
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Keep revising from each exact sandbox observation.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=10,
        max_no_progress_turns=2,
        artifact_id="question:global-code-budget",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == drafts[-1],
            "stderr": "assertion failed"
            if dict(candidate) != drafts[-1]
            else "",
        },
        workspace_operation="initial_authoring",
    )

    assert dict(result.code_draft) == drafts[-1]
    assert result.evidence["source_updates"] == 5
    assert result.evidence["sandbox_checks"] == 5
    assert all(
        "replace_scientific_source" in {
            tool.name for tool in request.tools
        }
        for request in backend.requests
    )
