from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_statistician.agent_runtime import BlackboardState
from ai_statistician.research_agent_runtime import (
    FormalizerWorkspaceRuntimeSubsystem,
    RetrievalMemoryRuntimeSubsystem,
    _formalization_runtime_problem_and_goals,
    _question_from_payload,
    _question_to_payload,
)
from ai_statistician.runtime_research_problem_adapter import (
    frozen_direct_initial_task as _frozen_direct_initial_task,
    is_frozen_formal_only_question as _is_frozen_formal_only_question,
)
from ai_statistician.research_lab import load_open_research_questions
from ai_statistician.research_schema import OpenResearchQuestion


LEAN_SOURCE_PREFIX = """import Statlib.Inference

namespace FormalTargetTest

theorem frozenTarget : True := by
"""


def _formal_target_contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "target_id": "frozen_target",
        "declaration_name": "FormalTargetTest.frozenTarget",
        "lean_source_prefix": LEAN_SOURCE_PREFIX,
        "lean_source_prefix_sha256": hashlib.sha256(
            LEAN_SOURCE_PREFIX.encode("utf-8")
        ).hexdigest(),
        "proof_visibility": "hidden",
        "lean_environment": {
            "project_id": "statlib-test-project",
            "lean_toolchain": "leanprover/lean4:v4.30.0",
            "lake_manifest_sha256": "a" * 64,
        },
        "required_primitives": ["True"],
    }


def _formal_only_question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="frozen-formal-only",
        title="Prove one exact target",
        description="Complete the operator-frozen Lean declaration.",
        task_intent={
            "source_replication": "not_applicable",
            "theory": "not_applicable",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "required",
            "novelty": "not_applicable",
            "unresolved_gaps": "required",
        },
        formal_target_contract=_formal_target_contract(),
    )


def test_formal_target_contract_loads_and_round_trips(tmp_path: Path) -> None:
    question = _formal_only_question()
    path = tmp_path / "questions.json"
    path.write_text(
        json.dumps({"questions": [_question_to_payload(question)]}),
        encoding="utf-8",
    )

    loaded = load_open_research_questions(path)[0]
    payload = _question_to_payload(loaded)

    assert loaded.formal_target_contract == question.formal_target_contract
    assert _question_from_payload(payload).formal_target_contract == (
        question.formal_target_contract
    )


def test_formal_target_contract_rejects_source_hash_drift(tmp_path: Path) -> None:
    question = _question_to_payload(_formal_only_question())
    question["formal_target_contract"]["lean_source_prefix"] += "  trivial\n"
    path = tmp_path / "questions.json"
    path.write_text(json.dumps({"questions": [question]}), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match source"):
        load_open_research_questions(path)


class _NoopFormalRetriever:
    def search(self, query: str, k: int = 5) -> list[object]:
        return []


class _CapturingFormalizer:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def propose(self, **kwargs: object) -> dict[str, object]:
        self.kwargs = kwargs
        raise RuntimeError("stop after capturing exact target")


def test_formal_only_target_routes_retrieval_directly_to_formalizer() -> None:
    question = _formal_only_question()
    assert _is_frozen_formal_only_question(question)
    initial_task = _frozen_direct_initial_task(
        question=question,
        architect_context={},
    )
    assert initial_task is not None
    assert initial_task.owner_subsystem == "RetrievalMemory"
    assert initial_task.inputs["retrieval_return_to_subsystem"] == (
        "FormalizationEvaluator"
    )

    blackboard = BlackboardState(project_id="formal-target-test")
    retrieval = RetrievalMemoryRuntimeSubsystem(
        formal_source_retriever=_NoopFormalRetriever()
    ).run(initial_task, blackboard)
    assert retrieval.next_task is not None
    assert retrieval.next_task.owner_subsystem == "FormalizationEvaluator"
    blackboard.artifacts.update(retrieval.produced_artifacts)

    problem, goals, provenance = _formalization_runtime_problem_and_goals(
        question,
        retrieval.next_task.inputs,
        theory_packet={},
    )
    assert problem.problem_class == "operator_frozen_exact_lean_target"
    assert [goal.id for goal in goals] == ["frozen_target"]
    assert goals[0].informal_statement == LEAN_SOURCE_PREFIX
    assert provenance["theorem_goal_source"] == "explicit_runtime_override"

    proposal_agent = _CapturingFormalizer()
    result = FormalizerWorkspaceRuntimeSubsystem(
        proposal_agent=proposal_agent,
    ).run(retrieval.next_task, blackboard)

    captured_goals = proposal_agent.kwargs["theorem_goals"]
    assert captured_goals[0]["id"] == "frozen_target"
    assert captured_goals[0]["informal_statement"] == LEAN_SOURCE_PREFIX
    assert result.failure_classification == "formalizer_provider_generation_failed"
