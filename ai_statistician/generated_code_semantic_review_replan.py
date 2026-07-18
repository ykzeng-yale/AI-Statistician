from __future__ import annotations

from typing import Any, Mapping

from .agent_runtime import AgentTask
from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion
from .typed_repair_handoff import build_typed_repair_handoff_contract


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
    """Advance finding diagnostics under a theory/source lineage budget."""

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
                _normalized_text(row.get("severity")),
                _normalized_text(row.get("category")),
            )
            for row in review_packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ),
        "finding_count": len(review_packet.get("findings", []) or []),
    }
    finding_fingerprint = stable_hash(finding_signature)
    source_lineage_identity = (
        str(work_order.get("question_id", "") or ""),
        str(work_order.get("theory_packet_hash", "") or ""),
        str(work_order.get("source_subsystem", "") or ""),
    )
    source_lineage_key = stable_hash(source_lineage_identity)
    lineage_key = stable_hash(
        [
            *source_lineage_identity,
            str(review_packet.get("repair_scope", "") or ""),
            str(review_packet.get("repair_owner", "") or ""),
            finding_fingerprint,
        ]
    )
    prior_ledger = architect_context.get(
        GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY,
        {},
    )
    ledger = {
        str(key): dict(value)
        for key, value in (
            prior_ledger.items() if isinstance(prior_ledger, Mapping) else []
        )
        if isinstance(value, Mapping)
    }
    prior = dict(ledger.pop(lineage_key, {}))
    migrated_local_revisions = (
        max(0, int(prior_local_revisions or 0)) if not ledger and not prior else 0
    )
    row = {
        "lineage_key": lineage_key,
        "source_lineage_key": source_lineage_key,
        "question_id": str(work_order.get("question_id", "") or ""),
        "theory_packet_id": str(work_order.get("theory_packet_id", "") or ""),
        "theory_packet_hash": str(work_order.get("theory_packet_hash", "") or ""),
        "source_subsystem": str(work_order.get("source_subsystem", "") or ""),
        "repair_scope": str(review_packet.get("repair_scope", "") or ""),
        "repair_owner": str(review_packet.get("repair_owner", "") or ""),
        "finding_fingerprint": finding_fingerprint,
        "rejection_count": int(prior.get("rejection_count", 0) or 0) + 1,
        "local_repair_count": max(
            int(prior.get("local_repair_count", 0) or 0),
            migrated_local_revisions,
        ),
        "architect_replan_count": int(
            prior.get("architect_replan_count", 0) or 0
        ),
        "max_local_revisions": max(0, int(max_local_revisions or 0)),
        "last_action": str(prior.get("last_action", "") or ""),
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_BUDGET_NOT_PROOF_EVIDENCE"
        ),
    }
    ledger[lineage_key] = row
    source_lineage_rows = [
        candidate
        for candidate in ledger.values()
        if _source_lineage_identity(candidate) == source_lineage_identity
    ]
    source_local_repair_count = sum(
        max(0, int(candidate.get("local_repair_count", 0) or 0))
        for candidate in source_lineage_rows
    )
    source_architect_replan_count = sum(
        max(0, int(candidate.get("architect_replan_count", 0) or 0))
        for candidate in source_lineage_rows
    )
    row["source_local_repair_count"] = source_local_repair_count
    row["source_architect_replan_count"] = source_architect_replan_count
    row["source_rejection_count"] = sum(
        max(0, int(candidate.get("rejection_count", 0) or 0))
        for candidate in source_lineage_rows
    )
    if len(ledger) > 32:
        ledger = dict(list(ledger.items())[-32:])
    return {
        "lineage_key": lineage_key,
        "source_lineage_key": source_lineage_key,
        "row": row,
        "ledger": ledger,
        "local_repair_available": bool(
            row["repair_scope"] == "source_code"
            and source_local_repair_count < row["max_local_revisions"]
            and source_architect_replan_count == 0
        ),
        "architect_replan_available": source_architect_replan_count == 0,
        "lineage_budget_exhausted": source_architect_replan_count > 0,
    }


def record_generated_code_semantic_review_lineage_action(
    budget_state: Mapping[str, Any],
    *,
    action: str,
) -> dict[str, Any]:
    ledger = {
        str(key): dict(value)
        for key, value in (
            budget_state.get("ledger", {}).items()
            if isinstance(budget_state.get("ledger", {}), Mapping)
            else []
        )
        if isinstance(value, Mapping)
    }
    lineage_key = str(budget_state.get("lineage_key", "") or "")
    row = dict(ledger.get(lineage_key, budget_state.get("row", {})))
    if action == "local_repair":
        row["local_repair_count"] = int(row.get("local_repair_count", 0) or 0) + 1
    elif action == "architect_replan":
        row["architect_replan_count"] = int(
            row.get("architect_replan_count", 0) or 0
        ) + 1
    row["last_action"] = str(action)
    ledger[lineage_key] = row
    return ledger


def _source_lineage_identity(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("question_id", "") or ""),
        str(row.get("theory_packet_hash", "") or ""),
        str(row.get("source_subsystem", "") or ""),
    )


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
    repair_task_payload = _mapping(work_order.get("repair_task"))
    deferred_task_payload = _mapping(work_order.get("deferred_next_task"))
    repair_inputs = _mapping(repair_task_payload.get("inputs"))
    deferred_inputs = _mapping(deferred_task_payload.get("inputs"))
    repair_context = _mapping(repair_inputs.get("architect_context"))
    deferred_context = _mapping(deferred_inputs.get("architect_context"))
    replan_context = {**repair_context, **deferred_context}
    replan_context["environment_feedback"] = dict(escalation_feedback)
    if isinstance(lineage_ledger, Mapping):
        replan_context[GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY] = {
            str(key): dict(value)
            for key, value in lineage_ledger.items()
            if isinstance(value, Mapping)
        }

    pending_artifact_ids: dict[str, str] = {}
    for source in (
        work_order,
        repair_inputs,
        deferred_inputs,
        repair_context,
        deferred_context,
    ):
        pending_artifact_ids.update(
            {
                str(key): str(value)
                for key, value in source.items()
                if str(key).endswith("_id") and str(value).strip()
            }
        )
    next_task_id = (
        f"semantic-review-architect-replan:{question.id}:"
        f"{stable_hash([review_execution_id, pending_artifact_ids])[:8]}"
    )
    replan_context["runtime_generated_code_semantic_review_replan"] = {
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewReplanContext",
        "source_review_task_id": review_task_id,
        "source_task_id": str(work_order.get("source_task_id", "") or ""),
        "source_subsystem": str(work_order.get("source_subsystem", "") or ""),
        "source_manifest_id": str(
            work_order.get("source_manifest_id", "") or ""
        ),
        "work_order_id": str(work_order.get("work_order_id", "") or ""),
        "review_packet_id": review_packet_id,
        "review_execution_id": review_execution_id,
        "repair_scope": str(
            escalation_feedback.get("repair_scope", "") or ""
        ),
        "findings": [
            dict(row)
            for row in escalation_feedback.get("findings", []) or []
            if isinstance(row, Mapping)
        ],
        "repair_instructions": list(
            escalation_feedback.get("repair_instructions", []) or []
        ),
        "semantic_review_revision_budget": {
            "revisions_used": revision_count,
            "max_revisions": max_revisions,
        },
        "deferred_next_owner_subsystem": str(
            deferred_task_payload.get("owner_subsystem", "") or ""
        ),
        "pending_artifact_ids": pending_artifact_ids,
        "protocol_revision_policy": (
            "Do not weaken, delete, or reinterpret a frozen requirement after "
            "observing results. If exact independent review demonstrates that the "
            "frozen protocol or its theory premise is malformed, retain the old "
            "requirement fingerprint and failed artifact, record "
            "EVALUATION_PROTOCOL_REVISION_REQUIRED, and require a fresh candidate "
            "run under a newly reviewed protocol."
        ),
        "routing_contract": (
            "ArchitectCoordinator must route the exact semantic findings to the "
            "earliest evidence-producing owner. It cannot convert this review, the "
            "failed execution, or a replacement threshold into acceptance or proof "
            "evidence."
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_REPLAN_NOT_PROOF_EVIDENCE"
        ),
    }
    handoff_revision_count = max(1, revision_count)
    handoff_max_revisions = max(handoff_revision_count, max_revisions)
    replan_context["runtime_feedback_loop"] = {
        **_mapping(replan_context.get("runtime_feedback_loop")),
        "source_subsystem": GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM,
        "handoff": "generated_code_semantic_review_architect_replan",
        "semantic_review_execution_id": review_execution_id,
        "generated_code_semantic_review_revision_count": revision_count,
        "direct_repair_handoff_contract": build_typed_repair_handoff_contract(
            source_reviewer_subsystem=(
                GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM
            ),
            source_task_id=review_task_id,
            target_repair_subsystem="ArchitectCoordinator",
            target_task_id=next_task_id,
            feedback_artifact_id=review_packet_id,
            feedback_artifact_kind="GeneratedCodeSemanticReviewPacket",
            feedback_execution_id=review_execution_id,
            feedback_execution_artifact_kind=(
                "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
            ),
            feedback_type="generated_code_semantic_review_feedback",
            revision_count=handoff_revision_count,
            max_revisions=handoff_max_revisions,
        ),
    }
    return AgentTask(
        task_id=next_task_id,
        owner_subsystem="ArchitectCoordinator",
        objective=(
            "Replan from exact independent generated-code semantic findings, "
            "distinguishing source-code repair from malformed protocol or theory "
            "without weakening frozen evidence gates."
        ),
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "architect_context": replan_context,
            "environment_feedback": dict(escalation_feedback),
            "generated_code_semantic_review_revision_count": revision_count,
        },
        allowed_tools=("model_backend", "evidence_ledger"),
        expected_artifacts=("architect_coordinator_proposal",),
        acceptance_gate=(
            "validated Architect proposal routes an evidence-producing repair or "
            "records a fresh-run protocol blocker while preserving failed lineage"
        ),
        stop_condition=(
            "next owner selected, malformed protocol marked for a fresh run when "
            "needed, and no rejected artifact promoted"
        ),
    )


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _normalized_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())
