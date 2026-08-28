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
GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY = \
    "runtime_generated_code_semantic_review_lineage_ledger"


def advance_generated_code_semantic_review_lineage_budget(
    *,
    architect_context: Mapping[str, Any],
    work_order: Mapping[str, Any],
    review_packet: Mapping[str, Any],
    max_local_revisions: int,
    prior_local_revisions: int = 0,
) -> dict[str, Any]:
    """Bound repeated producer regenerations for one reviewed source lineage."""

    finding_signature = {"findings": sorted(
        (_normalized_text(row.get("finding_id")),
         _normalized_text(row.get("severity")),
         _normalized_text(row.get("category")),
         _normalized_text(row.get("summary")))
        for row in review_packet.get("findings", []) or []
        if isinstance(row, Mapping)
    )}
    finding_fingerprint = stable_hash(finding_signature)
    source_lineage_identity = (
        str(work_order.get("question_id", "") or ""),
        str(work_order.get("theory_packet_hash", "") or ""),
        str(work_order.get("source_subsystem", "") or ""),
    )
    source_lineage_key = stable_hash(source_lineage_identity)
    lineage_key = stable_hash([*source_lineage_identity, finding_fingerprint])
    raw_ledger = architect_context.get(GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY, {})
    ledger = {str(key): dict(value) for key, value in (
        raw_ledger.items() if isinstance(raw_ledger, Mapping) else []
    ) if isinstance(value, Mapping)}
    prior = dict(ledger.get(lineage_key, {}))
    migrated_regenerations = max(0, int(prior_local_revisions or 0)) if not ledger else 0
    max_candidate_regenerations = max(0, int(max_local_revisions or 0))
    row = {
        "lineage_key": lineage_key,
        "source_lineage_key": source_lineage_key,
        "question_id": source_lineage_identity[0],
        "theory_packet_id": str(work_order.get("theory_packet_id", "") or ""),
        "theory_packet_hash": source_lineage_identity[1],
        "source_subsystem": source_lineage_identity[2],
        "finding_fingerprint": finding_fingerprint,
        "rejection_count": int(prior.get("rejection_count", 0) or 0) + 1,
        "candidate_regeneration_count": max(
            int(prior.get("candidate_regeneration_count", 0) or 0),
            migrated_regenerations,
        ),
        "max_candidate_regenerations": max_candidate_regenerations,
        "last_action": str(prior.get("last_action", "") or ""),
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_BUDGET_NOT_PROOF_EVIDENCE"
        ),
    }
    ledger[lineage_key] = row
    source_rows = [
        candidate
        for candidate in ledger.values()
        if _source_lineage_identity(candidate) == source_lineage_identity
    ]
    source_regeneration_count = sum(
        max(0, int(candidate.get("candidate_regeneration_count", 0) or 0))
        for candidate in source_rows
    )
    row["source_candidate_regeneration_count"] = source_regeneration_count
    row["source_rejection_count"] = sum(
        max(0, int(candidate.get("rejection_count", 0) or 0))
        for candidate in source_rows
    )
    row["finding_seen_in_source_lineage"] = bool(prior)
    if len(ledger) > 32:
        ledger = dict(list(ledger.items())[-32:])
    candidate_regeneration_available = (
        source_regeneration_count < max_candidate_regenerations
    )
    return {
        "lineage_key": lineage_key,
        "source_lineage_key": source_lineage_key,
        "row": row,
        "ledger": ledger,
        "candidate_regeneration_available": candidate_regeneration_available,
        "lineage_budget_exhausted": not candidate_regeneration_available,
    }


def record_generated_code_semantic_review_lineage_action(
    budget_state: Mapping[str, Any],
    *,
    action: str,
) -> dict[str, Any]:
    raw_ledger = budget_state.get("ledger", {})
    ledger = {
        str(key): dict(value)
        for key, value in (
            raw_ledger.items() if isinstance(raw_ledger, Mapping) else []
        )
        if isinstance(value, Mapping)
    }
    lineage_key = str(budget_state.get("lineage_key", "") or "")
    row = dict(ledger.get(lineage_key, budget_state.get("row", {})))
    if action == "producer_regeneration":
        row["candidate_regeneration_count"] = int(
            row.get("candidate_regeneration_count", 0) or 0
        ) + 1
    row["last_action"] = str(action)
    ledger[lineage_key] = row
    return ledger


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
    max_revisions: int,
    lineage_ledger: Mapping[str, Any] | None = None,
) -> AgentTask:
    """Return complete review feedback to the immutable source producer."""

    observations = deepcopy(dict(review_feedback))
    if observations.get("confirmatory_empirical_evidence_eligible") is True:
        observations = generated_code_semantic_review_prompt_projection(
            observations
        )
        observations["confirmatory_result_values_withheld_from_source"] = True
    source_inputs = source_task.inputs
    source_subsystem = str(work_order.get("source_subsystem", "") or "")
    if not source_subsystem or source_task.owner_subsystem != source_subsystem:
        raise ValueError(
            "semantic-review producer revision requires an immutable source owner"
        )
    replan_context = _mapping(source_inputs.get("architect_context"))
    replan_context.pop("environment_feedback", None)
    if isinstance(lineage_ledger, Mapping):
        replan_context[GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY] = {
            str(key): dict(value)
            for key, value in lineage_ledger.items()
            if isinstance(value, Mapping)
        }

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
        "semantic_review_revision_budget": {
            "candidate_regenerations_used": max(
                0, int(revision_count or 0)
            ),
            "max_candidate_regenerations": max(
                0, int(max_revisions or 0)
            ),
        },
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
            "bounded lineage records a blocker"
        ),
    )


def _source_lineage_identity(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("question_id", "") or ""),
        str(row.get("theory_packet_hash", "") or ""),
        str(row.get("source_subsystem", "") or ""),
    )


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _normalized_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())
