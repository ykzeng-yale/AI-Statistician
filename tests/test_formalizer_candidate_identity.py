from ai_statistician.agent_runtime import AgentTask
from ai_statistician.formalizer_candidate_identity import (
    source_theorem_explicit_target_ids,
)
from ai_statistician.research_agent_runtime import (
    _formalizer_semantic_review_continuation_task,
    _formalizer_lean_candidate_target_context,
)
from ai_statistician.research_schema import OpenResearchQuestion


def test_source_theorem_explicit_target_ids_reads_nested_identity_fields() -> None:
    row = {
        "target_id": "target:root",
        "source_theorem_target_context": {
            "target_ids": ["target:nested", "target:root"],
            "source_theorem_target_provenance": {
                "source_theorem_goal_id": "goal:source",
            },
        },
        "target_theorem_goal_ids": ["fallback:is-not-explicit"],
    }

    assert source_theorem_explicit_target_ids(row) == [
        "target:root",
        "target:nested",
        "goal:source",
    ]


def test_formalizer_target_context_uses_shared_identity_parser() -> None:
    context = _formalizer_lean_candidate_target_context(
        {
            "candidate_metadata": {
                "target_ids": ["target:one"],
                "source_theorem_goal_id": "goal:one",
                "target_theorem_name": "Example.target",
                "target_lean_declaration": "Example.target",
            }
        }
    )

    assert context["target_ids"] == ["target:one", "goal:one"]
    assert context["target_theorem_goal_ids"] == ["target:one", "goal:one"]
    assert context["target_theorem_name"] == "Example.target"


def test_formal_target_review_returns_to_same_model_owned_workspace() -> None:
    question = OpenResearchQuestion(
        id="generic-formal-task",
        title="Generic formal task",
        description="Formalize a task without theorem-specific runtime rules.",
    )
    source_task = AgentTask(
        task_id="formalize:generic-formal-task",
        owner_subsystem="FormalizationEvaluator",
        objective="Author and check the exact target.",
        inputs={"question": {"id": question.id}},
        allowed_tools=("model_backend", "local_lean"),
        budget={"model_turns": 4},
    )
    feedback = {
        "feedback_id": "formalizer-feedback:one",
        "feedback_type": "formalizer_lean_candidate_local_lean_feedback",
        "raw_lean_stderr": "unknown identifier",
    }

    continuation = _formalizer_semantic_review_continuation_task(
        task=source_task,
        question=question,
        context={"architect_coordinator_proposal_id": "architect:one"},
        workspace_feedback=feedback,
        source_artifact_id="formalization_manifest:one",
    )

    assert continuation.owner_subsystem == "FormalizationEvaluator"
    assert continuation.inputs["environment_feedback"] == feedback
    assert continuation.inputs["architect_context"]["environment_feedback"] == feedback
    assert continuation.budget == source_task.budget
    assert "local_lean" in continuation.allowed_tools
    assert "formal_source_retrieval" in continuation.allowed_tools
