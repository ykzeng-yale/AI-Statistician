from __future__ import annotations

import pytest

from ai_statistician.client_tool_loop import (
    CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_SOURCE_COMMIT_TOOL,
    SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL,
    SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
    SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER,
    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
    load_scientific_code_workspace_checkpoint,
    run_scientific_code_workspace,
    run_source_owner_scientific_workspace,
    scientific_source_candidate_accepted,
    scientific_workspace_prototype_observation,
)
from ai_statistician.structured_output_retry import PacketValidationError


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


def _commit_response(call_id: str = "commit") -> ClientToolTurnResponse:
    return _response(
        ClientToolCall(
            call_id=call_id,
            name=SCIENTIFIC_SOURCE_COMMIT_TOOL,
            input={},
        )
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
            ),
            _commit_response(),
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
    assert result.evidence["submit_and_execute_atomic"] is True
    assert result.evidence["explicit_model_commit_required"] is True
    assert result.evidence["model_commit_after_observation"] is True
    assert "NameError: missing_name" in str(backend.requests[0].messages)
    assert all(request.enable_prompt_caching for request in backend.requests)
    assert all(request.disable_parallel_tool_use for request in backend.requests)
    assert [tool.name for tool in backend.requests[0].tools] == [
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
    ]
    assert SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL not in str(
        backend.requests[0].messages
    )
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
    dependency_description = submission_schema["properties"]["dependencies"][
        "description"
    ]
    assert "language=python" in dependency_description
    assert "numpy, scipy, pandas, scikit-learn, statsmodels, sympy" in (
        dependency_description
    )
    assert "language=r" in dependency_description
    assert "base, stats, utils, methods" in dependency_description


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
            _commit_response(),
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
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
    ]
    assert len(backend.requests) == 2


def test_blind_confirmatory_executes_once_after_model_owned_diagnostic_loop() -> None:
    first = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'score': 0.2}\n",
    }
    revised = {
        **first,
        "code": "def run_sandbox(seed, replicates): return {'score': 0.95}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-revised",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
                )
            ),
            _commit_response(),
        ]
    )

    class SourceAgent:
        provider = backend

        @classmethod
        def iterate_code_with_tools(cls, **kwargs):
            return run_scientific_code_workspace(
                provider=cls.provider,
                system_prompt="Use the scientific source tools.",
                user_prompt="Implement and diagnose the current simulation source.",
                model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
                model_tier="haiku",
                temperature=0.0,
                max_tokens=1200,
                max_turns=4,
                max_no_progress_turns=3,
                artifact_id=kwargs["artifact_id"],
                initial_code_draft=kwargs["code_draft"],
                initial_check_result=kwargs["initial_observation"],
                check_candidate=kwargs["check_candidate"],
                workspace_operation=kwargs["workspace_operation"],
            )

    diagnostic_sources: list[str] = []
    confirmatory_sources: list[str] = []

    def diagnostic(candidate):
        source = str(candidate["code"])
        diagnostic_sources.append(source)
        score = 0.95 if candidate == revised else 0.2
        return (
            {
                "script_hash": stable_hash(source),
                "result_hash": stable_hash({"score": score}),
                "runtime_seed": 17,
                "runtime_replicates": 200,
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": score >= 0.9,
                "metrics": {"score": score},
                "metric_gate_errors": (
                    [] if score >= 0.9 else ["diagnostic score below 0.9"]
                ),
                "metric_contract_evaluation": {
                    "evaluations": [
                        {
                            "contract_id": "diagnostic-score",
                            "passed": score >= 0.9,
                            "aggregate_value": score,
                        }
                    ]
                },
            },
            f"diagnostic:{len(diagnostic_sources)}",
        )

    def confirmatory(candidate):
        source = str(candidate["code"])
        confirmatory_sources.append(source)
        return (
            {
                "script_hash": stable_hash(source),
                "result_hash": "confirmatory-secret-result-hash",
                "runtime_seed": 29,
                "runtime_replicates": 2_000,
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": False,
                "metrics": {"score": 0.1},
                "metric_gate_errors": ["confirmatory-secret-failure"],
            },
            "confirmatory",
        )

    prototype, tool_calls = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(),
        question=object(),
        artifact_id="question:blind-simulation",
        code_draft=first,
        source_deferred=False,
        workspace_context={},
        execute_candidate=confirmatory,
        execute_authoring_diagnostic=diagnostic,
        failure_identity={"simulation_id": "blind-simulation"},
        confirmatory_result_blind=True,
    )

    assert diagnostic_sources == [first["code"], revised["code"]]
    assert confirmatory_sources == [revised["code"]]
    assert tool_calls == ["diagnostic:1", "diagnostic:2", "confirmatory"]
    assert prototype["metric_gate_errors"] == ["confirmatory-secret-failure"]
    workspace = prototype["scientific_code_workspace"]
    assert workspace["authoring_execution_phase"] == "exploratory_diagnostic"
    assert workspace["authoring_diagnostic_accepted"] is True
    assert workspace["authoring_diagnostic_runtime_replicates"] == 200
    assert workspace["confirmatory_execution_after_model_commit"] is True
    assert workspace["confirmatory_outcomes_returned_to_source_model"] is False
    transcript = str([request.messages for request in backend.requests])
    assert "diagnostic score below 0.9" not in transcript
    assert '"score":0.95' in transcript
    assert "acceptance_outcomes_withheld" in transcript
    assert "confirmatory-secret" not in transcript
    assert '"accepted":true' in str(backend.requests[0].messages)


def test_uncommitted_workspace_failure_cannot_promote_last_executed_source() -> None:
    candidate = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'score': 1.0}\n",
    }

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake source owner controls this workspace")

    class SourceAgent:
        provider = Provider()

        @staticmethod
        def iterate_code_with_tools(**kwargs):
            check = kwargs["check_candidate"](candidate)
            assert check["accepted"] is True
            raise PacketValidationError(
                validation_label="scientific source workspace",
                attempts=1,
                errors=["terminal source was not explicitly committed"],
                history=[],
            )

    def execute(candidate_draft):
        source = str(candidate_draft["code"])
        return (
            {
                "script_hash": stable_hash(source),
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": True,
                "metric_contract_evaluation": {"evaluations": []},
            },
            "sandbox",
        )

    prototype, tool_calls = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(),
        question=object(),
        artifact_id="question:uncommitted-source",
        code_draft={},
        source_deferred=True,
        workspace_context={},
        execute_candidate=execute,
        failure_identity={"simulation_id": "uncommitted-source"},
        confirmatory_result_blind=True,
    )

    assert tool_calls == ["sandbox"]
    assert prototype["execution_smoke_passed"] is True
    assert prototype["scientific_code_workspace_failure"][
        "validation_errors"
    ] == ["terminal source was not explicitly committed"]
    assert scientific_source_candidate_accepted(
        prototype,
        confirmatory_result_blind=True,
    ) is False


def test_same_model_can_revise_after_technically_successful_execution() -> None:
    first = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'passed': False}\n",
    }
    revised = {
        **first,
        "code": "def run_sandbox(seed, replicates): return {'passed': True}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-first",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=first,
                )
            ),
            _response(
                ClientToolCall(
                    call_id="submit-revised",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
                )
            ),
            _commit_response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        candidate = dict(candidate)
        checked.append(candidate)
        return {
            "code_draft_hash": stable_hash(candidate),
            "accepted": True,
            "metrics": {
                "self_diagnostic": {
                    "passed": candidate == revised,
                }
            },
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Inspect execution output before accepting the source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:successful-process-failed-diagnostic",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=check,
        workspace_operation="initial_authoring",
    )

    assert checked == [first, revised]
    assert dict(result.code_draft) == revised
    assert '"passed":false' in str(backend.requests[1].messages).lower()
    assert result.evidence["sandbox_checks"] == 2
    assert result.evidence["model_commit_after_observation"] is True


def test_model_cannot_submit_and_commit_before_observing_execution() -> None:
    source = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'value': 1}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=source,
                ),
                ClientToolCall(
                    call_id="premature-commit",
                    name=SCIENTIFIC_SOURCE_COMMIT_TOOL,
                    input={},
                ),
            ),
            _commit_response("observed-commit"),
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Execute, inspect, then commit.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=2,
        artifact_id="question:observation-before-commit",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": True,
            "stdout": "execution complete",
        },
        workspace_operation="initial_authoring",
    )

    premature = result.evidence["history"][0]["tool_calls"][1]
    assert premature["is_error"] is True
    assert "subsequent model turn" in premature["result_excerpt"]
    assert dict(result.code_draft) == source
    assert result.evidence["sandbox_checks"] == 1
    assert result.evidence["model_commit_after_observation"] is True


def test_model_selects_dependency_handoff_after_raw_consumer_failure() -> None:
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
                    call_id="report-dependency",
                    name=SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL,
                    input={
                        "reason": (
                            "The exact bound estimator returned a non-finite response "
                            "for a valid request; the current consumer cannot repair it."
                        )
                    },
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
            "source_owner": source_owner,
            "prototype": {
                "estimator_runtime_failure_ids": ["estimator-a"],
                "estimator_runtime_errors": [
                    "accepted estimator returned a non-finite response"
                ],
            },
            "stderr": "bound dependency failed in consumer execution",
        },
        allow_dependency_handoff=True,
    )

    assert dict(result.code_draft) == submitted
    assert result.check_result["accepted"] is False
    assert result.evidence["accepted"] is False
    assert result.evidence["source_iteration_disposition"] == (
        SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
    )
    assert result.evidence["source_owner"] == source_owner
    assert result.check_result["dependency_failure_report"]["model_selected"] is True
    assert result.evidence["source_updates"] == 1
    assert result.evidence["sandbox_checks"] == 1
    assert len(backend.requests) == 2
    assert [tool.name for tool in backend.requests[0].tools] == [
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
        SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL,
    ]


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
            _commit_response(),
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


def test_model_can_run_current_source_in_changed_dependency_environment() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 0}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="run-current",
                    name=SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
                    input={
                        "reason": (
                            "This artifact satisfies its owned interface; another "
                            "bound dependency caused the consumer failure."
                        )
                    },
                )
            ),
            _commit_response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        checked.append(dict(candidate))
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": True,
            "stdout": "dependency integration passed",
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Resolve the bound consumer observation.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:run-current",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "another dependency failed",
        },
        check_candidate=check,
        allow_current_source_run=True,
    )

    assert dict(result.code_draft) == initial
    assert checked == [initial]
    assert result.evidence["source_changed"] is False
    assert result.evidence["source_updates"] == 0
    assert result.evidence["sandbox_checks"] == 1
    assert result.evidence["current_source_run_requested"] is True
    assert result.evidence["current_source_run_requests"] == 1
    assert result.evidence["accepted"] is True
    assert [tool.name for tool in backend.requests[0].tools] == [
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
        SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
    ]


def test_current_source_runs_at_most_once_per_dependency_environment() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'value': 0}\n",
    }
    revised = {
        **initial,
        "code": "def run_sandbox(seed, replicates): return {'value': 1}\n",
    }
    run_current_call = {
        "reason": "Another bound dependency owns the observed failure."
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    "run-current-1",
                    SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
                    run_current_call,
                )
            ),
            _response(
                ClientToolCall(
                    "run-current-2",
                    SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
                    run_current_call,
                )
            ),
            _response(
                ClientToolCall(
                    "submit-revision",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    revised,
                )
            ),
            _commit_response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        checked.append(dict(candidate))
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == revised,
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Resolve the bound consumer observation.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:single-parent-reexecution",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
        },
        check_candidate=check,
        allow_current_source_run=True,
    )

    assert dict(result.code_draft) == revised
    assert checked == [initial, revised]
    repeated = result.evidence["history"][1]["tool_calls"][0]
    assert repeated["is_error"] is True
    assert "current dependency environment" in repeated["result_excerpt"]


def test_scientific_workspace_does_not_reexecute_an_older_source() -> None:
    def draft(value: int) -> dict[str, object]:
        return {
            "language": "python",
            "execution_profile": "stdlib",
            "dependencies": [],
            "entrypoint": "run_sandbox",
            "code": (
                "def run_sandbox(seed, replicates):\n"
                f"    return {{'value': {value}}}\n"
            ),
        }

    initial = draft(0)
    first_revision = draft(1)
    accepted_revision = draft(2)
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    "submit-first",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    first_revision,
                )
            ),
            _response(
                ClientToolCall(
                    "submit-old",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    initial,
                )
            ),
            _response(
                ClientToolCall(
                    "submit-accepted",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    accepted_revision,
                )
            ),
            _commit_response(),
        ]
    )
    executed_hashes: list[str] = []

    def check(candidate):
        candidate_hash = stable_hash(dict(candidate))
        executed_hashes.append(candidate_hash)
        return {
            "code_draft_hash": candidate_hash,
            "accepted": dict(candidate) == accepted_revision,
        }

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
        artifact_id="question:no-source-cycling",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "initial failure",
        },
        check_candidate=check,
    )

    assert dict(result.code_draft) == accepted_revision
    assert executed_hashes == [
        stable_hash(first_revision),
        stable_hash(accepted_revision),
    ]
    assert result.evidence["source_updates"] == 2
    old = result.evidence["history"][1]["tool_calls"][0]
    assert old["executed_by_runtime"] is True
    assert old["is_error"] is True
    assert "previously executed" in old["result_excerpt"]


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
        + [_commit_response()]
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
    assert result.evidence["transcript_policy"] == CLIENT_TOOL_TRANSCRIPT_POLICY
    assert [len(request.messages) for request in backend.requests] == [
        1,
        3,
        5,
        7,
        9,
        11,
    ]
    assert "at most 5 total model/tool turns" in str(backend.requests[0].messages)
    assert "attempt': 0" in str(backend.requests[-1].messages)
    assert "attempt': 3" in str(backend.requests[-1].messages)
    assert all(
        [tool.name for tool in request.tools]
        == [SCIENTIFIC_SOURCE_SUBMISSION_TOOL, SCIENTIFIC_SOURCE_COMMIT_TOOL]
        for request in backend.requests
    )


def test_scientific_workspace_resumes_exact_progress_checkpoint(tmp_path) -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return missing\n",
    }
    first_revision = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': missing}\n",
    }
    accepted_revision = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 1.0}\n",
    }
    first_backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-first",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=first_revision,
                )
            ),
            _response(),
        ]
    )

    def check(candidate):
        candidate = dict(candidate)
        return {
            "code_draft_hash": stable_hash(candidate),
            "accepted": candidate == accepted_revision,
            "stderr": "" if candidate == accepted_revision else "NameError: missing",
        }

    with pytest.raises(PacketValidationError) as exc_info:
        run_scientific_code_workspace(
            provider=first_backend,
            system_prompt="Use tools.",
            user_prompt="Repair from exact execution feedback.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=1,
            max_no_progress_turns=1,
            artifact_id="question:durable-source",
            initial_code_draft=initial,
            initial_check_result={
                "code_draft_hash": stable_hash(initial),
                "accepted": False,
                "stderr": "NameError: missing",
            },
            check_candidate=check,
            session_dir=tmp_path / "scientific-session",
        )

    checkpoint = exc_info.value.recovery_checkpoint
    checkpoint_draft, checkpoint_observation = (
        load_scientific_code_workspace_checkpoint(
            checkpoint,
            artifact_id="question:durable-source",
        )
    )
    assert checkpoint_draft == first_revision
    assert checkpoint_observation["stderr"] == "NameError: missing"
    assert checkpoint["source_updates"] == 1
    assert checkpoint["checks"] == 1
    assert checkpoint["resumable"] is True
    session_ref = checkpoint["client_tool_session_ref"]
    assert session_ref["artifact_kind"] == "ClientToolWorkspaceSessionRef"

    second_backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-accepted",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=accepted_revision,
                )
            ),
            _commit_response(),
        ]
    )
    executed: list[dict] = []

    def resumed_check(candidate):
        executed.append(dict(candidate))
        return check(candidate)

    result = run_scientific_code_workspace(
        provider=second_backend,
        system_prompt="Use tools.",
        user_prompt="Continue the exact workspace.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=1,
        max_no_progress_turns=1,
        artifact_id="question:durable-source",
        initial_code_draft=checkpoint_draft,
        initial_check_result=checkpoint_observation,
        check_candidate=resumed_check,
        recovery_checkpoint=checkpoint,
        session_dir=tmp_path / "scientific-session",
    )

    assert executed == [accepted_revision]
    assert dict(result.code_draft) == accepted_revision
    assert result.evidence["resumed_from_checkpoint_id"] == checkpoint[
        "checkpoint_id"
    ]
    assert result.evidence["source_updates"] == 2
    assert result.evidence["sandbox_checks"] == 2
    assert result.evidence["client_tool_session_lineage_continued"] is True
    assert result.evidence["resumed_from_client_tool_session_ref"] == session_ref
    window = result.evidence["client_tool_checkpoint_window"]
    assert window["policy"] == CLIENT_TOOL_CHECKPOINT_WINDOW_POLICY
    assert window["parent_message_count"] == session_ref["message_count"]
    assert window["checkpoint_identity"] == checkpoint["checkpoint_id"]
    assert window["prior_transcript_replayed"] is False
    assert result.evidence["transcript_policy"] == CLIENT_TOOL_TRANSCRIPT_POLICY
    assert checkpoint["checkpoint_id"] in str(second_backend.requests[0].messages)
    assert "submit-first" not in str(second_backend.requests[0].messages)
    assert len(second_backend.requests[0].messages) == 1

    tampered = {**checkpoint, "current_code_draft_hash": "tampered"}
    with pytest.raises(ValueError, match="identity mismatch"):
        load_scientific_code_workspace_checkpoint(
            tampered,
            artifact_id="question:durable-source",
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


def test_confirmatory_source_observation_withholds_realized_outcomes() -> None:
    observation = scientific_workspace_prototype_observation(
        {
            "prototype_status": "FAILED_METRIC_GATE",
            "execution_attempted": True,
            "execution_smoke_passed": True,
            "smoke_passed": False,
            "returncode": 0,
            "stdout_summary": "metric=0.2",
            "stderr_summary": "",
            "script_hash": "source-hash",
            "mechanical_estimator_invocation_verified": False,
            "estimator_runtime_failure_ids": ["candidate"],
            "estimator_runtime_errors": ["AttributeError: incompatible request"],
            "estimator_invocation_samples": {
                "candidate": [
                    {
                        "invocation_index": 1,
                        "request": {"mode": "withheld-realized-value"},
                        "response": {"estimate": 0.2},
                        "request_shape": {
                            "type": "object",
                            "fields": {
                                "mode": {"type": "string", "length": 23}
                            },
                        },
                        "response_status": "ERROR",
                        "error_type": "AttributeError",
                    }
                ]
            },
            "execution_envelope_hash": "outcome-derived-envelope-hash",
            "result_hash": "result-hash",
            "metric_gate_errors": ["observed 0.2 is below 0.9"],
            "metric_contracts": [
                {
                    "contract_id": "frozen-gate",
                    "metric_value_kind": "boolean",
                    "operator": "==",
                    "aggregation": "at_least_fraction",
                    "threshold": 1,
                    "tolerance": 0.0,
                    "minimum_pass_fraction": 0.92,
                    "required_runtime_replicates": 80,
                }
            ],
            "metric_contract_evaluation": {
                "evaluations": [
                    {
                        "contract_id": "frozen-gate",
                        "requirement_id": "frozen-requirement",
                        "metric_path": ["metric"],
                        "passed": False,
                        "resolved_values_preview": [0.2],
                        "aggregate_value": 0.2,
                        "measurement_interface_valid": False,
                        "measurement_interface_status": "VALUE_TYPE_INVALID",
                        "measurement_interface_errors": [
                            "metric contract frozen-gate: metric_path resolved a "
                            "nonnumeric or nonfinite value"
                        ],
                    }
                ]
            },
            "metrics": {"metric": 0.2},
        },
        include_empirical_outcomes=False,
    )

    assert observation["execution_smoke_passed"] is True
    assert observation["empirical_outcomes_withheld"] is True
    assert observation["empirical_outcome_authority"] == "EmpiricalEvaluator"
    assert observation["measurement_interface_failures"] == [
        {
            "contract_id": "frozen-gate",
            "requirement_id": "frozen-requirement",
            "metric_path": ["metric"],
            "metric_value_kind": "boolean",
            "operator": "==",
            "aggregation": "at_least_fraction",
            "threshold": 1,
            "tolerance": 0.0,
            "minimum_pass_fraction": 0.92,
            "required_runtime_replicates": 80,
            "measurement_interface_status": "VALUE_TYPE_INVALID",
            "measurement_interface_errors": [
                "metric contract frozen-gate: metric_path resolved a "
                "nonnumeric or nonfinite value"
            ],
        }
    ]
    invocation = observation["estimator_invocation_samples"]["candidate"][0]
    assert invocation["request_shape"]["fields"]["mode"] == {"type": "string"}
    assert "invocation_index" not in invocation
    assert "request" not in invocation
    assert "response" not in invocation
    for key in (
        "prototype_status",
        "smoke_passed",
        "stdout_summary",
        "result_hash",
        "execution_envelope_hash",
        "metric_gate_errors",
        "failed_metric_contracts",
        "metrics_preview",
    ):
        assert key not in observation
    assert "0.2" not in str(observation)
    assert "withheld-realized-value" not in str(observation)
    assert "23" not in str(observation)
