from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    EnvironmentObservation,
    EvidenceLedgerEntry,
)
from .fingerprint import stable_hash
from .generated_metric_contract import generated_metric_requirement_set_id
from .research_schema import OpenResearchQuestion


EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION = 1


def architect_preexecution_metric_protocol_rejection_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    semantic_review_history: list[dict[str, Any]],
) -> AgentStepResult:
    history = [dict(row) for row in semantic_review_history]
    final_review = history[-1] if history else {}
    manifest_id = "metric_protocol_preexecution_rejection:" + stable_hash(
        [question.id, task.task_id, history]
    )[:20]
    candidate_packet_ids = [
        str(row.get("authoring_packet_id", "") or "")
        for row in history
        if str(row.get("authoring_packet_id", "") or "").strip()
    ]
    review_packet_ids = [
        str(row.get("semantic_review_packet_id", "") or "")
        for row in history
        if str(row.get("semantic_review_packet_id", "") or "").strip()
    ]
    manifest = {
        "schema_version": EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION,
        "artifact_kind": "RuntimeArchitectMetricProtocolPreExecutionRejection",
        "manifest_id": manifest_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "task_id": task.task_id,
        "disposition": "METRIC_PROTOCOL_PREEXECUTION_REJECTED",
        "semantic_review_attempts": len(history),
        "candidate_authoring_packet_ids": candidate_packet_ids,
        "semantic_review_packet_ids": review_packet_ids,
        "semantic_review_history": history,
        "final_overall_verdict": str(
            final_review.get("overall_verdict", "") or ""
        ),
        "final_findings": [
            dict(row)
            for row in final_review.get("findings", []) or []
            if isinstance(row, Mapping)
        ],
        "final_repair_instructions": [
            str(value)
            for value in final_review.get("repair_instructions", []) or []
            if str(value).strip()
        ],
        "generated_code_observed": False,
        "simulation_results_observed": False,
        "current_candidate_acceptance_eligible": False,
        "execution_authorized": False,
        "rejected_lineage_preserved": True,
        "feedback_reusable_for_fresh_preexecution_authoring": True,
        "proof_evidence_status": (
            "METRIC_PROTOCOL_PREEXECUTION_REJECTION_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "This artifact records independently rejected protocol candidates before "
            "generated code or simulation execution. It is reusable authoring feedback, "
            "but it is not execution, statistical acceptance, or theorem proof evidence."
        ),
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
        task_id=task.task_id,
        artifact_id=manifest_id,
        evidence_type="metric_protocol_preexecution_rejection",
        status="PREEXECUTION_PROTOCOL_REJECTED_NO_EXECUTION_AUTHORIZED",
        boundary=str(manifest["boundary"]),
        payload={
            "disposition": manifest["disposition"],
            "semantic_review_attempts": len(history),
            "current_candidate_acceptance_eligible": False,
            "execution_authorized": False,
            "kernel_verified": False,
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "Independent pre-execution semantic review rejected every bounded "
            "metric-protocol candidate. Full candidate and review lineage is "
            "preserved for a fresh theory-informed authoring turn; no coding or "
            "simulation execution is authorized."
        ),
        produced_artifacts={manifest_id: manifest},
        observations=(
            EnvironmentObservation(
                observation_type="metric_protocol_preexecution_rejection",
                summary=(
                    "bounded pre-execution protocol authoring rejected with full "
                    "review history preserved"
                ),
                payload={
                    "manifest_id": manifest_id,
                    "disposition": manifest["disposition"],
                    "semantic_review_attempts": len(history),
                    "execution_authorized": False,
                    "proof_evidence_status": manifest["proof_evidence_status"],
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification="architect_metric_protocol_preexecution_rejected",
    )


def _architect_post_result_metric_protocol_revision_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
) -> AgentStepResult | None:
    replan = architect_context.get(
        "runtime_generated_code_semantic_review_replan", {}
    )
    if not (
        isinstance(replan, Mapping)
        and replan.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewReplanContext"
        and replan.get("repair_scope") == "upstream_metric_contract"
    ):
        return None
    prior_plan = architect_context.get("architect_runtime_plan", {})
    prior_contract = (
        prior_plan.get("evidence_contract", {})
        if isinstance(prior_plan, Mapping)
        else {}
    )
    if not isinstance(prior_contract, Mapping):
        prior_contract = {}
    requirement_rows = [
        dict(row)
        for row in prior_contract.get("empirical_metric_requirements", []) or []
        if isinstance(row, Mapping)
    ]
    requirement_set_id = str(
        prior_contract.get("empirical_metric_requirement_set_id", "") or ""
    )
    if not requirement_set_id and requirement_rows:
        requirement_set_id = generated_metric_requirement_set_id(requirement_rows)
    pending_artifact_ids = {
        str(key): str(value)
        for key, value in (
            replan.get("pending_artifact_ids", {}).items()
            if isinstance(replan.get("pending_artifact_ids", {}), Mapping)
            else ()
        )
        if str(value).strip()
    }
    manifest_id = "evaluation_protocol_revision_required:" + stable_hash(
        [
            question.id,
            task.task_id,
            requirement_set_id,
            replan.get("review_packet_id", ""),
            replan.get("review_execution_id", ""),
            pending_artifact_ids,
        ]
    )[:20]
    manifest = {
        "schema_version": EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION,
        "artifact_kind": "RuntimeEvaluationProtocolRevisionRequired",
        "manifest_id": manifest_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "task_id": task.task_id,
        "disposition": "EVALUATION_PROTOCOL_REVISION_REQUIRED",
        "repair_scope": "upstream_metric_contract",
        "source_requirement_set_id": requirement_set_id,
        "source_requirement_set_fingerprint": (
            stable_hash(requirement_rows) if requirement_rows else ""
        ),
        "source_preexecution_review": (
            dict(
                prior_contract.get(
                    "empirical_metric_requirements_preexecution_review", {}
                )
            )
            if isinstance(
                prior_contract.get(
                    "empirical_metric_requirements_preexecution_review", {}
                ),
                Mapping,
            )
            else {}
        ),
        "source_semantic_review_packet_id": str(
            replan.get("review_packet_id", "") or ""
        ),
        "source_semantic_review_execution_id": str(
            replan.get("review_execution_id", "") or ""
        ),
        "source_review_task_id": str(
            replan.get("source_review_task_id", "") or ""
        ),
        "source_manifest_id": str(replan.get("source_manifest_id", "") or ""),
        "pending_artifact_ids": pending_artifact_ids,
        "findings": [
            dict(row)
            for row in replan.get("findings", []) or []
            if isinstance(row, Mapping)
        ],
        "repair_instructions": list(
            replan.get("repair_instructions", []) or []
        ),
        "current_candidate_acceptance_eligible": False,
        "current_candidate_artifacts_preserved": True,
        "post_result_protocol_mutation_allowed": False,
        "fresh_candidate_required": True,
        "fresh_candidate_entry_gate": (
            "Author a new versioned metric requirement set before execution, pass "
            "independent ArchitectMetricSemanticReviewer review, and rerun every "
            "empirical artifact under that frozen accepted set."
        ),
        "proof_evidence_status": "EVALUATION_PROTOCOL_REVISION_NOT_PROOF_EVIDENCE",
        "boundary": (
            "This disposition blocks post-result mutation of a frozen empirical "
            "protocol. It preserves the failed candidate and reviewer lineage, but "
            "it is not execution, acceptance, statistical, or theorem proof evidence."
        ),
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
        task_id=task.task_id,
        artifact_id=manifest_id,
        evidence_type="evaluation_protocol_revision_required",
        status="CURRENT_CANDIDATE_BLOCKED_FRESH_PROTOCOL_RUN_REQUIRED",
        boundary=str(manifest["boundary"]),
        payload={
            "disposition": manifest["disposition"],
            "source_requirement_set_id": requirement_set_id,
            "source_semantic_review_packet_id": manifest[
                "source_semantic_review_packet_id"
            ],
            "current_candidate_acceptance_eligible": False,
            "fresh_candidate_required": True,
            "kernel_verified": False,
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "Independent post-execution semantic review identified the frozen "
            "metric contract as the blocker. The current candidate is stopped with "
            "EVALUATION_PROTOCOL_REVISION_REQUIRED; its artifacts and requirement "
            "fingerprint are preserved, and only a fresh independently reviewed "
            "protocol run may continue."
        ),
        produced_artifacts={manifest_id: manifest},
        observations=(
            EnvironmentObservation(
                observation_type="evaluation_protocol_revision_required",
                summary=(
                    "current candidate blocked; fresh independently reviewed "
                    "metric protocol required"
                ),
                payload={
                    "manifest_id": manifest_id,
                    "disposition": manifest["disposition"],
                    "source_requirement_set_id": requirement_set_id,
                    "fresh_candidate_required": True,
                    "proof_evidence_status": manifest["proof_evidence_status"],
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification="evaluation_protocol_revision_required",
    )
