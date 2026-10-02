"""Prospective draw/accounting mechanics with mocked HTTP, not scientific gold."""

from copy import deepcopy
from io import BytesIO
import json
from urllib.error import HTTPError

import pytest

from benchmarks.publication.run_control_draw import run_single_context_research_draw
from ai_statistician.algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from ai_statistician.client_tool_loop import ClientToolLoopError
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_reviewer_llm import GeneratedCodeSemanticReviewerConfig, LLMGeneratedCodeSemanticReviewerAgent
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.model_backend import ClientToolTurnRequest
from ai_statistician.research_architect import LLMTheoryDeveloperAgent, ResearchArchitectConfig
from ai_statistician.research_schema import OpenResearchQuestion, research_question_payload
from ai_statistician.simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig


MODEL = "Qwen3-4B-Instruct-2507"


def draw_options(tmp_path, monkeypatch, *, workflow="", limit=2):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    backend = LocalChatGeneratorBackend()
    common = dict(provider_name="local", model=MODEL, model_tier="local", max_tokens=1024, temperature=0)
    return dict(
        question=OpenResearchQuestion("opaque-draw", "Opaque draw", "Unresolved mechanism fixture.",
            task_intent={"theory": "required", "scientific_code": "not_applicable",
                         "empirical": "not_applicable", "formal": "not_applicable"}),
        request=ClientToolTurnRequest(system_prompt="Research the supplied question.", messages=(), tools=(),
                                     model=MODEL, max_tokens=1024), backend=backend,
        theory_agent=LLMTheoryDeveloperAgent(provider=backend, config=ResearchArchitectConfig(
            **common, serious_model=MODEL, serious_model_tier="local")),
        algorithm_agent=LLMAlgorithmEngineerAgent(provider=backend, config=AlgorithmEngineerConfig(**common)),
        simulation_agent=LLMSimulationEngineerAgent(provider=backend, config=SimulationEngineerConfig(**common)),
        estimator_ids=("opaque",), out_dir=tmp_path / "draw", n_runs=3, seed=7, timeout_s=30,
        max_turns=8, max_tool_calls=8, max_no_progress_turns=8, local_model_call_limit=limit,
        workflow_instructions=workflow, confirmatory_seeds=(918007, 918011),
    )


def mock_wire(monkeypatch, options, actions, *, failure="", mutate=None):
    requests = []
    before = deepcopy(research_question_payload(options["question"], include_task_intent=True))

    class Opener:
        def open(self, request, *, timeout):
            frozen = json.loads((options["out_dir"] / "frozen_draw.json").read_text())
            assert frozen["question"] == before  # Freeze precedes the first transport call.
            assert frozen["request"]["tools"]
            assert frozen["frozen_draw_hash"] == stable_hash({key: value for key, value in frozen.items()
                                                            if key != "frozen_draw_hash"})
            payload = json.loads(request.data)
            assert "918007" not in json.dumps(payload) and "918011" not in json.dumps(payload)
            requests.append(payload)
            if mutate is not None:
                mutate()
            if failure == "http":
                raise HTTPError(request.full_url, 400, "Bad Request", {}, BytesIO(b'opaque transport failure'))
            name, arguments = actions.pop(0)
            return BytesIO(json.dumps({
                "model": "wrong-model" if failure == "model" else MODEL,
                "choices": [{"message": {"content": "", "tool_calls": [{
                    "id": "call-" + str(len(requests)), "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)},
                }]}, "finish_reason": "tool_calls"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                          "prompt_tokens_details": {"cached_tokens": 2}},
            }).encode())

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    return requests


@pytest.mark.parametrize("workflow", ["", "Use the same declared research workflow."])
@pytest.mark.parametrize("write_first", [False, True])
def test_control_final_selection_uses_graph_accounting_without_scientific_acceptance(tmp_path, monkeypatch, workflow, write_first):
    count = 2 if write_first else 1
    options = draw_options(tmp_path, monkeypatch, workflow=workflow, limit=count)
    actions = [("theory__write_theory_document", {"path": "claim.md", "content": "# Unresolved note\n"})] if write_first else []
    actions.append(("submit_research_result", {"selected_checkpoints": {}, "report_markdown": "# Unresolved final report\n"}))
    requests = mock_wire(monkeypatch, options, actions,
        mutate=lambda: options["question"].task_intent.update(formal="required"))
    result, submission = run_single_context_research_draw(**options)
    assert result.status == "REROUTE" and result.pending_task is None
    assert len(result.traces) == result.outer_graph_iterations_consumed == 1
    assert result.traces[0].subsystem == "SingleResearcher" and result.traces[0].next_task is None
    assert result.blackboard.evidence_ledger == [] and result.workspace_continuations_consumed == 0
    assert submission["selected_checkpoints"] == {} and submission["checkpoint_payloads"] == {}
    assert submission["report_markdown"] == "# Unresolved final report\n"
    assert submission["independent_role_review"] is False
    assert submission["task_intent"]["formal"] == "not_applicable"
    assert submission["control_mode"] == ("same_workflow" if workflow else "free_planning")
    usage = result.local_model_usage
    assert len(requests) == usage["attempted_requests"] == count and usage["denied_requests"] == 0
    assert usage["reported_usage_totals"] == {
        "input_tokens": 10 * count, "output_tokens": 5 * count, "total_tokens": 15 * count,
        "cache_read_input_tokens": 2 * count,
    }
    saved = json.loads((options["out_dir"] / "runtime_result.json").read_text())
    assert saved == result.to_json()
    original = {path: path.read_bytes() for path in options["out_dir"].rglob("*") if path.is_file()}
    with pytest.raises(FileExistsError):
        run_single_context_research_draw(**options)
    assert len(requests) == count and all(path.read_bytes() == data for path, data in original.items())


@pytest.mark.parametrize("failure", ["budget", "http", "model"])
def test_failed_draw_preserves_observations_and_never_salvages_a_final_report(tmp_path, monkeypatch, failure):
    options = draw_options(tmp_path, monkeypatch, limit=1)
    requests = mock_wire(monkeypatch, options, [
        ("theory__write_theory_document", {"path": "claim.md", "content": "# Saved unresolved work\n"}),
    ], failure=failure)
    result, submission = run_single_context_research_draw(**options)
    assert result.status == ("BLOCKED" if failure == "budget" else "FAILED") and submission is None
    assert result.pending_task is not None and result.blackboard.evidence_ledger == []
    assert "final_submission_ref" not in result.blackboard.artifacts
    assert len(requests) == result.local_model_usage["attempted_requests"] == 1
    assert result.local_model_usage["denied_requests"] == int(failure == "budget")
    assert list((options["out_dir"] / "author" / ".client_tool_sessions").glob("*.json"))
    assert not list((options["out_dir"] / "author" / ".client_tool_sessions" / "reports").glob("*.md"))
    if failure == "budget":
        notes = list((options["out_dir"] / "author" / "theory").rglob("claim.md"))
        assert notes and all(path.read_text() == "# Saved unresolved work\n" for path in notes)
    elif failure == "http":
        assert result.local_model_usage["requests_with_complete_token_usage"] == 0
        assert result.local_model_usage["reported_usage_totals"] == {}


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_draw_call_limit_fails_before_preparation(tmp_path, monkeypatch, limit):
    options = draw_options(tmp_path, monkeypatch, limit=limit)
    with pytest.raises(ValueError, match="positive integer"):
        run_single_context_research_draw(**options)
    assert not options["out_dir"].exists()


def test_control_draw_rejects_cloud_before_preparation(tmp_path, monkeypatch):
    options = draw_options(tmp_path, monkeypatch)
    options["backend"].provider_name = "anthropic"
    with pytest.raises(ValueError, match="local provider"):
        run_single_context_research_draw(**options)
    assert not options["out_dir"].exists()


def test_failed_tool_loop_preserves_raw_history_without_accepting_or_restarting(tmp_path, monkeypatch):
    options = draw_options(tmp_path, monkeypatch)
    error = ClientToolLoopError(
        reason="opaque environment failure", turns=1, tool_calls=1, runtime_executed_tool_calls=1,
        history=[{"tool_calls": [{"name": "opaque-tool", "output": {"stderr": "opaque raw observation"}}]}],
        messages=[{"role": "user", "content": "unresolved source-owned input"}], provider="local", model=MODEL,
        observation_refs=[{"path": "opaque-observation", "sha256": "opaque-digest"}])
    calls = []

    def failed_loop(**kwargs):
        calls.append(kwargs)
        raise error

    monkeypatch.setattr("benchmarks.publication.run_control_draw.run_client_tool_workspace", failed_loop)
    result, submission = run_single_context_research_draw(**options)
    saved = json.loads((options["out_dir"] / "failed_tool_loop.json").read_text())
    assert saved["history"] == error.history and saved["messages"] == error.messages
    assert saved["observation_refs"] == list(error.observation_refs)
    assert saved["transcript_fingerprint"] == stable_hash(error.messages)
    assert saved["scientific_evidence"] is False and saved["automatic_restart"] is False
    assert result.status == "FAILED" and submission is None and len(calls) == 1
    assert result.blackboard.evidence_ledger == [] and not result.local_model_usage["attempted_requests"]


@pytest.mark.parametrize("limit", [1, 2])
def test_self_review_actions_share_the_draw_budget_and_frozen_configuration(tmp_path, monkeypatch, limit):
    options = draw_options(tmp_path, monkeypatch, limit=limit)
    config = GeneratedCodeSemanticReviewerConfig(provider_name="local", model=MODEL, model_tier="local", max_tokens=1024, temperature=0)
    options["code_reviewer"] = LLMGeneratedCodeSemanticReviewerAgent(provider=options["backend"], config=config)
    requests = mock_wire(monkeypatch, options, [
        ("code_review__submit_generated_code_semantic_review", {}),
        ("submit_research_result", {"selected_checkpoints": {}, "report_markdown": "# Unresolved final report\n"}),
    ])
    result, submission = run_single_context_research_draw(**options)
    assert len(requests) == result.local_model_usage["attempted_requests"] == limit
    assert result.local_model_usage["denied_requests"] == int(limit == 1)
    assert result.status == ("BLOCKED" if limit == 1 else "REROUTE")
    assert result.blackboard.evidence_ledger == []
    assert submission is None if limit == 1 else submission["independent_role_review"] is False
    frozen = json.loads((options["out_dir"] / "frozen_draw.json").read_text())
    assert frozen["role_configs"]["code_reviewer"]["model"] == MODEL
    assert frozen["role_configs"]["code_reviewer"]["provider_name"] == "local"
    assert any(row["name"] == "code_review__run_exact_estimator_review_probe" for row in frozen["request"]["tools"])
