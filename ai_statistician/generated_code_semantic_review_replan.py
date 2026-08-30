from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .agent_runtime import AgentTask, RUNTIME_CONTINUATION_BUDGET_MARKER_KEY
from .fingerprint import stable_hash
from .generated_code_semantic_reviewer_llm import (
    generated_code_semantic_review_prompt_projection,
)
from .research_schema import OpenResearchQuestion, research_question_payload


GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM = "GeneratedCodeSemanticReviewer"


def generated_code_semantic_review_producer_observations(
    review_feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the exact review observations authorized for the source owner."""

    observations = deepcopy(dict(review_feedback))
    if observations.get("confirmatory_empirical_evidence_eligible") is True:
        observations = generated_code_semantic_review_prompt_projection(observations)
        observations["confirmatory_result_values_withheld_from_source"] = True
    for row in observations.get("reviewed_source_artifacts", []) or []:
        if isinstance(row, dict) and row.get("artifact_role") != "upstream_generated_dependency":
            row.pop("exact_source_code", None); row.pop("exact_source_code_complete", None)
            row["exact_source_available_via"] = "current_source_owner_workspace"
    return observations


def build_generated_code_semantic_review_producer_revision_task(
    *,
    question: OpenResearchQuestion,
    review_task_id: str,
    work_order: Mapping[str, Any],
    source_task: AgentTask,
    review_feedback: Mapping[str, Any],
    review_packet_id: str,
    review_execution_id: str,
    revision_count: int,
) -> AgentTask:
    """Return complete review feedback to the immutable source producer."""

    observations = generated_code_semantic_review_producer_observations(review_feedback)
    source_inputs = source_task.inputs
    source_subsystem = str(work_order.get("source_subsystem", "") or "")
    if not source_subsystem or source_task.owner_subsystem != source_subsystem:
        raise ValueError(
            "semantic-review producer revision requires an immutable source owner"
        )
    replan_context = _mapping(source_inputs.get("architect_context"))
    replan_context.pop("environment_feedback", None)

    source_lineage = _mapping(observations.get("source_lineage"))
    replan = {
        "artifact_kind": (
            "RuntimeGeneratedCodeSemanticReviewProducerRevisionContext"
        ),
        "question_id": question.id,
        "source_review_task_id": review_task_id,
        "source_task_id": str(work_order.get("source_task_id", "") or ""),
        "source_subsystem": str(work_order.get("source_subsystem", "") or ""),
        "source_manifest_id": str(
            work_order.get("source_manifest_id", "") or ""
        ),
        "source_manifest_hash": str(
            work_order.get("source_manifest_hash", "") or ""
        ),
        "work_order_id": str(work_order.get("work_order_id", "") or ""),
        "review_packet_id": review_packet_id,
        "review_packet_hash": str(
            observations.get("semantic_review_packet_hash", "") or ""
        ),
        "review_execution_id": review_execution_id,
        "source_lineage": source_lineage,
        "theory_packet_id": str(
            source_lineage.get("theory_packet_id", "")
            or work_order.get("theory_packet_id", "")
            or ""
        ),
        "theory_packet_hash": str(
            source_lineage.get("theory_packet_hash", "")
            or work_order.get("theory_packet_hash", "")
            or ""
        ),
        "routing_authority": "immutable_source_producer_lineage",
        "runtime_selected_owner": False,
        "exact_source_workspace_continuation_required": True,
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_REPLAN_NOT_PROOF_EVIDENCE"
        ),
    }
    replan["revision_context_id"] = (
        "generated_code_semantic_review_revision_context:" + stable_hash(replan)[:20])
    replan_context["runtime_generated_code_semantic_review_replan"] = replan
    task_id = (
        f"semantic-review-producer-regenerate:{question.id}:"
        f"{stable_hash([review_execution_id, replan['revision_context_id']])[:8]}"
    )
    revision_inputs = deepcopy(source_inputs)
    # A semantic revision supersedes older progress/replay continuations.
    revision_inputs.pop("scientific_code_workspace_progress_manifest", None)
    revision_inputs.pop("scientific_code_workspace_continuation_count", None)
    revision_inputs.pop("consumer_resume_manifest", None)
    revision_inputs["question"] = research_question_payload(
        question,
        include_task_intent=True,
    )
    revision_inputs["architect_context"] = replan_context
    revision_inputs["environment_feedback"] = dict(observations)
    revision_inputs["generated_code_semantic_review_revision_count"] = (
        max(0, int(revision_count or 0)) + 1
    )
    revision_budget = deepcopy(source_task.budget)
    revision_budget.pop(RUNTIME_CONTINUATION_BUDGET_MARKER_KEY, None)
    return AgentTask(
        task_id=task_id,
        owner_subsystem=source_subsystem,
        objective=(
            "Continue the exact source-owner workspace from its reviewed candidate, "
            "execution result, and independent semantic-review observations."
        ),
        inputs=revision_inputs,
        allowed_tools=source_task.allowed_tools,
        budget=revision_budget,
        expected_artifacts=source_task.expected_artifacts,
        acceptance_gate=(
            "a changed complete model-generated candidate executes and passes a new "
            "independent semantic review"
        ),
        stop_condition=(
            "the source producer emits a complete replacement candidate or the "
            "source owner reports an unresolved blocker"
        ),
    )


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
