"""One prospective control draw through the existing research graph and loop.

This is benchmark assembly, not a new agent controller or scientific evaluator.
The study caller owns task/gold qualification, model deployment pins and matching
the remaining arms. Never use it to resume or reassess a consumed draw.
"""

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ai_statistician.agent_runtime import (
    AgentRuntime, AgentRuntimeResult, AgentStepResult, AgentTask, BlackboardState,
)
from ai_statistician.client_tool_loop import run_client_tool_workspace
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import ClientToolTurnRequest
from ai_statistician.research_control import (
    load_research_control_submission, prepare_single_context_research_workspace,
)
from ai_statistician.research_schema import OpenResearchQuestion, research_question_payload


def run_single_context_research_draw(
    *, question: OpenResearchQuestion, request: ClientToolTurnRequest, backend: Any,
    theory_agent: Any, algorithm_agent: Any, simulation_agent: Any,
    estimator_ids: Sequence[str], out_dir: Path, n_runs: int, seed: int,
    timeout_s: int, max_turns: int, max_tool_calls: int, max_no_progress_turns: int,
    local_model_call_limit: int | None = None, workflow_instructions: str = "",
    theory_reviewer: Any = None, code_reviewer: Any = None, confirmatory_seeds: Sequence[int] = (),
    study_provenance: Mapping[str, Any] | None = None,
) -> tuple[AgentRuntimeResult, dict[str, Any] | None]:
    """Run actual production actions in one model-owned conversation.

    One AgentRuntime subsystem executes the prepared workspace, so all its local
    requests share the same accounting/cap as a complete multi-role graph. There
    is no handoff policy, independent referee invocation, retry or source repair.
    A valid final selection terminates with REROUTE and no next task: it is handed
    out to the caller's independent evaluator, not accepted as science here.
    Failure does not salvage an earlier checkpoint as the final submission.
    """

    if getattr(backend, "provider_name", None) != "local":
        raise ValueError("publication control draws require the frozen local provider")
    if local_model_call_limit is not None and (
        type(local_model_call_limit) is not int or local_model_call_limit < 1
    ):
        raise ValueError("local model call limit must be a positive integer or None")
    question = deepcopy(question)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=False)
    session_dir = out_dir / "author"
    session_dir.mkdir()
    workspace = prepare_single_context_research_workspace(
        question=question, request=request, theory_agent=theory_agent,
        algorithm_agent=algorithm_agent, simulation_agent=simulation_agent,
        estimator_ids=estimator_ids, session_dir=session_dir, session_id="research-control",
        n_runs=n_runs, seed=seed, timeout_s=timeout_s, max_turns=max_turns,
        max_tool_calls=max_tool_calls, max_no_progress_turns=max_no_progress_turns,
        workflow_instructions=workflow_instructions, theory_reviewer=theory_reviewer, code_reviewer=code_reviewer,
        confirmatory_seeds=confirmatory_seeds,
    )
    public = research_question_payload(question, include_task_intent=True)
    frozen = {
        "question": public, "question_hash": stable_hash(public),
        "request": asdict(workspace.request),
        "role_configs": {name: asdict(agent.config) for name, agent in (
            ("theory", theory_agent), ("algorithm", algorithm_agent),
            ("simulation", simulation_agent), ("theory_reviewer", theory_reviewer),
            ("code_reviewer", code_reviewer),
        ) if agent is not None},
        "local_model_call_limit": local_model_call_limit,
        "max_turns": max_turns, "max_tool_calls": max_tool_calls,
        "max_no_progress_turns": max_no_progress_turns,
        "estimator_ids": list(estimator_ids), "n_runs": n_runs, "seed": seed,
        "timeout_seconds": timeout_s, "confirmatory_seeds": list(confirmatory_seeds),
        "provider": backend.provider_name, "backend_class": type(backend).__qualname__,
        "base_url": getattr(backend, "base_url", None),
        "study_provenance": deepcopy(dict(study_provenance or {})),
        "authority": "one_control_draw_not_scientific_acceptance",
    }
    frozen_hash = stable_hash(frozen)
    with (out_dir / "frozen_draw.json").open("x", encoding="utf-8") as stream:
        json.dump({**frozen, "frozen_draw_hash": frozen_hash}, stream, indent=2)
    submission = None

    class SingleResearcher:
        name = "SingleResearcher"

        def run(self, task, blackboard):
            nonlocal submission
            loop = run_client_tool_workspace(backend=backend, workspace=workspace)
            submission = load_research_control_submission(loop, question=question, session_dir=session_dir)
            return AgentStepResult(
                status="REROUTE", rationale="Final selection awaits external scientific evaluation.",
                produced_artifacts={"final_submission_ref": deepcopy(loop.terminal_payload)},
            )

    def record_progress(row):
        with (out_dir / "progress.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")

    result = AgentRuntime(
        subsystems={"SingleResearcher": SingleResearcher()},
        blackboard=BlackboardState(project_id=question.id),
    ).run(
        AgentTask(task_id="control:" + question.id, owner_subsystem="SingleResearcher",
                  objective=question.description, inputs={"frozen_draw_hash": frozen_hash}),
        max_iterations=1, progress_callback=record_progress,
        local_model_call_limit=local_model_call_limit,
    )
    with (out_dir / "runtime_result.json").open("x", encoding="utf-8") as stream:
        json.dump(result.to_json(), stream, indent=2)
    return result, submission
