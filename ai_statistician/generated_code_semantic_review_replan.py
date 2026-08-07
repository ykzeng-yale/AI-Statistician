from __future__ import annotations

from typing import Any, Mapping

from .agent_runtime import AgentTask
from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion
from .semantic_review_feedback import architect_observations_without_runtime_routing


GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM = "GeneratedCodeSemanticReviewer"
GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY = (
    "runtime_generated_code_semantic_review_lineage_ledger"
)


def advance_generated_code_semantic_review_lineage_budget(
    *,
    architect_context: Mapping[str, Any],
    work_order: Mapping[str, Any],
    review_packet: Mapping[str, Any],
    max_local_revisions: int,
    prior_local_revisions: int = 0,
) -> dict[str, Any]:
    """Bound repeated Architect replans for one reviewed source lineage."""

    finding_signature = {
        "failed_dimensions": sorted(
            (
                _normalized_text(row.get("dimension")),
                _normalized_text(row.get("status")),
            )
            for row in review_packet.get("dimension_reviews", []) or []
            if isinstance(row, Mapping)
            and _normalized_text(row.get("status")) != "pass"
        ),
        "findings": sorted(
            (
                _normalized_text(row.get("finding_id")),
                _normalized_text(row.get("severity")),
                _normalized_text(row.get("category")),
                _normalized_text(row.get("summary")),
            )
            for row in review_packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ),
    }
    finding_fingerprint = stable_hash(finding_signature)
    source_lineage_identity = (
        str(work_order.get("question_id", "") or ""),
        str(work_order.get("theory_packet_hash", "") or ""),
        str(work_order.get("source_subsystem", "") or ""),
    )
    source_lineage_key = stable_hash(source_lineage_identity)
    lineage_key = stable_hash([*source_lineage_identity, finding_fingerprint])
    raw_ledger = architect_context.get(
        GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY,
        {},
    )
    ledger = {
        str(key): dict(value)
        for key, value in (
            raw_ledger.items() if isinstance(raw_ledger, Mapping) else []
        )
        if isinstance(value, Mapping)
    }
    prior = dict(ledger.get(lineage_key, {}))
    migrated_replans = (
        max(0, int(prior_local_revisions or 0)) if not ledger else 0
    )
    max_architect_replans = max(0, int(max_local_revisions or 0))
    row = {
        "lineage_key": lineage_key,
        "source_lineage_key": source_lineage_key,
        "question_id": source_lineage_identity[0],
        "theory_packet_id": str(work_order.get("theory_packet_id", "") or ""),
        "theory_packet_hash": source_lineage_identity[1],
        "source_subsystem": source_lineage_identity[2],
        "finding_fingerprint": finding_fingerprint,
        "rejection_count": int(prior.get("rejection_count", 0) or 0) + 1,
        "architect_replan_count": max(
            int(prior.get("architect_replan_count", 0) or 0),
            migrated_replans,
        ),
        "max_architect_replans": max_architect_replans,
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
    source_replan_count = sum(
        max(0, int(candidate.get("architect_replan_count", 0) or 0))
        for candidate in source_rows
    )
    row["source_architect_replan_count"] = source_replan_count
    row["source_rejection_count"] = sum(
        max(0, int(candidate.get("rejection_count", 0) or 0))
        for candidate in source_rows
    )
    row["finding_seen_in_source_lineage"] = bool(prior)
    if len(ledger) > 32:
        ledger = dict(list(ledger.items())[-32:])
    architect_replan_available = source_replan_count < max_architect_replans
    return {
        "lineage_key": lineage_key,
        "source_lineage_key": source_lineage_key,
        "row": row,
        "ledger": ledger,
        "architect_replan_available": architect_replan_available,
        "lineage_budget_exhausted": not architect_replan_available,
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
    if action == "architect_replan":
        row["architect_replan_count"] = int(
            row.get("architect_replan_count", 0) or 0
        ) + 1
    row["last_action"] = str(action)
    ledger[lineage_key] = row
    return ledger


def build_generated_code_semantic_review_architect_replan_task(
    *,
    question: OpenResearchQuestion,
    review_task_id: str,
    work_order: Mapping[str, Any],
    escalation_feedback: Mapping[str, Any],
    review_packet_id: str,
    review_execution_id: str,
    revision_count: int,
    max_revisions: int,
    lineage_ledger: Mapping[str, Any] | None = None,
) -> AgentTask:
    """Give evidence to Architect without inferring an owner or edit."""

    observations = architect_observations_without_runtime_routing(
        escalation_feedback
    )
    source_task = _mapping(work_order.get("source_task"))
    deferred_task = _mapping(work_order.get("deferred_next_task"))
    source_inputs = _mapping(source_task.get("inputs"))
    deferred_inputs = _mapping(deferred_task.get("inputs"))
    replan_context = {
        **_mapping(source_inputs.get("architect_context")),
        **_mapping(deferred_inputs.get("architect_context")),
        "environment_feedback": dict(observations),
    }
    if isinstance(lineage_ledger, Mapping):
        replan_context[GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY] = {
            str(key): dict(value)
            for key, value in lineage_ledger.items()
            if isinstance(value, Mapping)
        }

    source_lineage = _mapping(observations.get("source_lineage"))
    replan = {
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewReplanContext",
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
        "semantic_review_replan_budget": {
            "replans_used": max(0, int(revision_count or 0)),
            "max_replans": max(0, int(max_revisions or 0)),
        },
        "routing_authority": "ArchitectCoordinator_model_packet",
        "runtime_selected_owner": False,
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_REPLAN_NOT_PROOF_EVIDENCE"
        ),
    }
    replan["replan_id"] = (
        "generated_code_semantic_review_replan:"
        + stable_hash(replan)[:20]
    )
    replan_context["runtime_generated_code_semantic_review_replan"] = replan
    task_id = (
        f"semantic-review-architect-replan:{question.id}:"
        f"{stable_hash([review_execution_id, replan['replan_id']])[:8]}"
    )
    return AgentTask(
        task_id=task_id,
        owner_subsystem="ArchitectCoordinator",
        objective=(
            "Choose the next evidence-producing subsystem from the independent "
            "semantic observations and immutable artifact lineage."
        ),
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "architect_context": replan_context,
            "environment_feedback": dict(observations),
            "generated_code_semantic_review_revision_count": revision_count,
        },
        allowed_tools=("model_backend", "evidence_ledger"),
        expected_artifacts=("architect_coordinator_proposal",),
        acceptance_gate=(
            "validated Architect proposal selects the next subsystem while "
            "preserving rejected artifact lineage and the global replan budget"
        ),
        stop_condition=(
            "one model-owned route is selected or the blocker is recorded without "
            "promoting a rejected artifact"
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
