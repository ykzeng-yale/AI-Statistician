from __future__ import annotations

from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER,
    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
    run_scientific_code_workspace,
    scientific_workspace_prototype_observation,
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
                    call_id="submit-1",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
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
    assert result.evidence["runtime_executed_tool_calls"] == 1
    assert result.evidence["submit_and_execute_atomic"] is True
    assert "NameError: missing_name" in str(backend.requests[0].messages)
    assert [tool.name for tool in backend.requests[0].tools] == [
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL
    ]
    submission_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == SCIENTIFIC_SOURCE_SUBMISSION_TOOL
    )
    assert "required_estimator_ids" not in submission_schema["properties"]
    assert submission_schema["properties"]["execution_profile"]["enum"] == [
        "stdlib",
        "scientific_wasm",
    ]
    assert "json" not in submission_schema["properties"]["dependencies"][
        "items"
    ]["enum"]


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
                    call_id="submit-1",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=authored,
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
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL
    ]
    assert len(backend.requests) == 1


def test_dependency_owner_failure_terminates_without_more_local_edits() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 0}\n",
    }
    submitted = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 1}\n",
    }
    unused = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 2}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-1",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=submitted,
                )
            ),
            _response(
                ClientToolCall(
                    call_id="must-not-run",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=unused,
                )
            ),
        ]
    )
    source_owner = {
        "owner_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm:accepted",
        "source_manifest_hash": "sha256:manifest",
        "artifact_ids": ["estimator-a"],
        "artifact_hashes": {"estimator-a": "sha256:source"},
    }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise only source owned by this workspace.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:dependency-observation",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "local callback mismatch",
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": False,
            "source_iteration_disposition": (
                SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
            ),
            "source_owner": source_owner,
            "stderr": "bound dependency failed in consumer execution",
        },
    )

    assert dict(result.code_draft) == submitted
    assert result.check_result["accepted"] is False
    assert result.evidence["accepted"] is False
    assert result.evidence["source_iteration_disposition"] == (
        SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
    )
    assert result.evidence["source_owner"] == source_owner
    assert result.evidence["source_updates"] == 1
    assert result.evidence["sandbox_checks"] == 1
    assert len(backend.requests) == 1


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
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=initial,
                )
            ),
            _response(
                ClientToolCall(
                    call_id="submit-2",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
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


def test_scientific_workspace_retains_complete_bounded_transcript() -> None:
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
            _response(
                ClientToolCall(
                    call_id=f"submit-{index}",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=draft,
                )
            )
            for index, draft in enumerate(drafts)
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
        max_turns=5,
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
    assert result.evidence["max_retained_tool_turns"] == 5
    assert [len(request.messages) for request in backend.requests] == [1, 3, 5, 7, 9]
    assert "at most 5 total model/tool turns" in str(backend.requests[0].messages)
    assert "attempt': 0" in str(backend.requests[-1].messages)
    assert "attempt': 3" in str(backend.requests[-1].messages)
    assert all(
        [tool.name for tool in request.tools]
        == [SCIENTIFIC_SOURCE_SUBMISSION_TOOL]
        for request in backend.requests
    )


def test_execution_observation_omits_stale_callback_samples_after_binding_passes() -> None:
    prototype = {
        "execution_attempted": True,
        "execution_smoke_passed": True,
        "mechanical_estimator_invocation_verified": True,
        "estimator_invocation_counts": {"estimator": 100},
        "estimator_invocation_samples": {
            "estimator": [{"request": {"sample": list(range(100))}}]
        },
        "metric_gate_errors": ["coverage failed"],
    }

    compact = scientific_workspace_prototype_observation(prototype)
    failed_binding = scientific_workspace_prototype_observation(
        {
            **prototype,
            "mechanical_estimator_invocation_verified": False,
        }
    )

    assert compact["estimator_invocation_counts"] == {"estimator": 100}
    assert "estimator_invocation_samples" not in compact
    assert "estimator_invocation_samples" in failed_binding
