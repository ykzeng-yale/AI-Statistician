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
from .architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY,
)
from .architect_metric_repair_ownership_router_llm import (
    ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED,
)
from .research_schema import OpenResearchQuestion


EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION = 1


def metric_protocol_upstream_theory_revision_feedback_errors(
    feedback: Mapping[str, Any],
    *,
    question_id: str,
    parent_theory_packet: Mapping[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    if feedback.get("artifact_kind") != (
        "RuntimeMetricProtocolUpstreamTheoryRevisionFeedback"
    ):
        errors.append("feedback artifact_kind is not upstream theory revision")
    ownership_clarification_required = (
        feedback.get("ownership_clarification_required") is True
    )
    expected_repair_scope = (
        ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
        if ownership_clarification_required
        else ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY
    )
    if feedback.get("recommended_repair_scope") != expected_repair_scope:
        errors.append(
            "feedback repair scope does not match its theory revision or "
            "ownership-clarification route"
        )
    if str(feedback.get("question_id", "") or "") != str(question_id or ""):
        errors.append("feedback question_id does not match the runtime question")
    for field in (
        "feedback_id",
        "source_metric_protocol_rejection_manifest_id",
        "source_theory_packet_id",
        "source_theory_packet_hash",
    ):
        if not str(feedback.get(field, "") or "").strip():
            errors.append(f"feedback missing {field}")
    if feedback.get("target_consumer_subsystem") != "TheoryDeveloper":
        errors.append("feedback target consumer is not TheoryDeveloper")
    if feedback.get("execution_authorized") is not False:
        errors.append("feedback must keep generated execution unauthorized")

    findings = feedback.get("findings", [])
    if not isinstance(findings, list) or not findings:
        errors.append("feedback requires at least one owned upstream finding")
    else:
        for index, finding in enumerate(findings):
            if not isinstance(finding, Mapping):
                errors.append(f"feedback finding {index} is not an object")
                continue
            if finding.get("repair_scope") != expected_repair_scope:
                errors.append(
                    f"feedback finding {index} does not match the routed scope"
                )
            if not str(finding.get("required_change", "") or "").strip():
                errors.append(f"feedback finding {index} missing required_change")

    try:
        revision_count = int(
            feedback.get("upstream_theory_revision_count", 0) or 0
        )
        max_revisions = int(feedback.get("max_upstream_theory_revisions", 0) or 0)
    except (TypeError, ValueError):
        revision_count = 0
        max_revisions = 0
        errors.append("feedback revision budget is not integer-valued")
    if revision_count <= 0:
        errors.append("feedback upstream theory revision count must be positive")
    if max_revisions <= 0 or revision_count > max_revisions:
        errors.append("feedback upstream theory revision budget is invalid")

    parent = parent_theory_packet or {}
    if not isinstance(parent, Mapping) or not parent:
        errors.append("immutable parent theory packet is missing from the blackboard")
    else:
        source_packet_id = str(
            feedback.get("source_theory_packet_id", "") or ""
        )
        parent_packet_id = str(parent.get("packet_id", "") or "")
        if parent_packet_id and parent_packet_id != source_packet_id:
            errors.append("parent theory packet_id does not match feedback lineage")
        expected_hash = str(
            feedback.get("source_theory_packet_hash", "") or ""
        )
        if expected_hash and stable_hash(dict(parent)) != expected_hash:
            errors.append("parent theory packet hash does not match feedback lineage")
    return list(dict.fromkeys(errors))


def metric_protocol_upstream_theory_revision_blocked_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    feedback: Mapping[str, Any],
    validation_errors: list[str],
) -> AgentStepResult:
    errors = [str(value) for value in validation_errors if str(value).strip()]
    artifact_id = "metric_protocol_theory_revision_blocked:" + stable_hash(
        [question.id, task.task_id, feedback.get("feedback_id", ""), errors]
    )[:20]
    artifact = {
        "schema_version": EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION,
        "artifact_kind": "RuntimeMetricProtocolUpstreamTheoryRevisionBlocked",
        "artifact_id": artifact_id,
        "question_id": question.id,
        "task_id": task.task_id,
        "feedback_id": str(feedback.get("feedback_id", "") or ""),
        "source_metric_protocol_rejection_manifest_id": str(
            feedback.get("source_metric_protocol_rejection_manifest_id", "") or ""
        ),
        "source_theory_packet_id": str(
            feedback.get("source_theory_packet_id", "") or ""
        ),
        "source_theory_packet_hash": str(
            feedback.get("source_theory_packet_hash", "") or ""
        ),
        "validation_errors": errors,
        "execution_authorized": False,
        "model_call_authorized": False,
        "proof_evidence_status": (
            "METRIC_PROTOCOL_THEORY_REVISION_CONTEXT_INVALID_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "The runtime rejected incomplete or mismatched upstream theory-revision "
            "lineage before calling the model. This is a control-plane blocker, not "
            "generated execution, statistical acceptance, or theorem proof evidence."
        ),
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, artifact_id])[:20],
        task_id=task.task_id,
        artifact_id=artifact_id,
        evidence_type="metric_protocol_theory_revision_context_rejection",
        status="BLOCKED_BEFORE_THEORY_MODEL_CALL",
        boundary=str(artifact["boundary"]),
        payload={
            "validation_errors": errors,
            "execution_authorized": False,
            "model_call_authorized": False,
            "kernel_verified": False,
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "Upstream metric-review feedback could not be bound to its immutable "
            "parent theory packet, so TheoryDeveloper was not called."
        ),
        produced_artifacts={artifact_id: artifact},
        observations=(
            EnvironmentObservation(
                observation_type="metric_protocol_theory_revision_context_invalid",
                summary="upstream theory revision lineage failed closed",
                payload={
                    "artifact_id": artifact_id,
                    "validation_errors": errors,
                    "execution_authorized": False,
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification=(
            "metric_protocol_upstream_theory_revision_context_invalid"
        ),
    )


def architect_preexecution_metric_protocol_rejection_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    semantic_review_history: list[dict[str, Any]],
    architect_context: Mapping[str, Any] | None = None,
    max_upstream_theory_revisions: int = 0,
) -> AgentStepResult:
    context = dict(architect_context or {})
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
    recommended_repair_scope = str(
        final_review.get("recommended_repair_scope", "") or "metric_contract"
    )
    metric_gate = context.get("architect_metric_protocol_gate", {})
    if not isinstance(metric_gate, Mapping):
        metric_gate = {}
    upstream_theory_revision_count = int(
        metric_gate.get("upstream_theory_revision_count", 0) or 0
    )
    max_theory_revisions = max(0, int(max_upstream_theory_revisions or 0))
    ownership_clarification_required = bool(
        recommended_repair_scope == ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
    )
    route_upstream_theory = bool(
        recommended_repair_scope
        in {
            ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY,
            ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED,
        }
        and upstream_theory_revision_count < max_theory_revisions
    )
    source_theory_packet_id = str(
        final_review.get("source_theory_packet_id", "")
        or metric_gate.get("source_theory_packet_id", "")
        or context.get("theory_packet_id", "")
        or ""
    )
    source_theory_packet_hash = str(
        final_review.get("source_theory_packet_hash", "") or ""
    )
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
        "cumulative_finding_ledger": [
            dict(row)
            for row in final_review.get("cumulative_finding_ledger", []) or []
            if isinstance(row, Mapping)
        ],
        "cumulative_finding_ledger_fingerprint": str(
            final_review.get("cumulative_finding_ledger_fingerprint", "")
            or ""
        ),
        "active_unresolved_finding_ids": [
            str(value)
            for value in final_review.get(
                "active_unresolved_finding_ids", []
            )
            or []
            if str(value).strip()
        ],
        "recommended_repair_scope": recommended_repair_scope,
        "source_theory_packet_id": source_theory_packet_id,
        "source_theory_packet_hash": source_theory_packet_hash,
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
        "upstream_theory_revision_count": upstream_theory_revision_count,
        "max_upstream_theory_revisions": max_theory_revisions,
        "upstream_theory_revision_routed": route_upstream_theory,
        "ownership_clarification_required": ownership_clarification_required,
        "proof_evidence_status": (
            "METRIC_PROTOCOL_PREEXECUTION_REJECTION_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "This artifact records independently rejected protocol candidates before "
            "generated code or simulation execution. It is reusable authoring feedback, "
            "but it is not execution, statistical acceptance, or theorem proof evidence."
        ),
    }
    produced_artifacts: dict[str, dict[str, Any]] = {manifest_id: manifest}
    next_task: AgentTask | None = None
    failure_classification = "architect_metric_protocol_preexecution_rejected"
    status = "BLOCKED"
    rationale = (
        "Independent pre-execution semantic review rejected every bounded "
        "metric-protocol candidate. Full candidate and review lineage is "
        "preserved for a fresh theory-informed authoring turn; no coding or "
        "simulation execution is authorized."
    )
    if route_upstream_theory:
        next_revision_count = upstream_theory_revision_count + 1
        routed_finding_scope = (
            ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
            if ownership_clarification_required
            else ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY
        )
        upstream_findings = [
            dict(row)
            for row in final_review.get("findings", []) or []
            if isinstance(row, Mapping)
            and row.get("repair_scope") == routed_finding_scope
        ]
        if not upstream_findings:
            upstream_findings = [
                dict(row)
                for row in final_review.get("findings", []) or []
                if isinstance(row, Mapping)
            ]
        upstream_repair_instructions = list(
            dict.fromkeys(
                str(row.get("required_change", "") or "").strip()
                for row in upstream_findings
                if str(row.get("required_change", "") or "").strip()
            )
        )
        feedback_id = "metric_protocol_upstream_theory_feedback:" + stable_hash(
            [manifest_id, next_revision_count, upstream_findings]
        )[:20]
        feedback = {
            "schema_version": EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION,
            "artifact_kind": "RuntimeMetricProtocolUpstreamTheoryRevisionFeedback",
            "feedback_id": feedback_id,
            "feedback_source": (
                "ArchitectMetricRepairOwnershipRouter"
                if final_review.get("repair_ownership_packet_id")
                else "ArchitectMetricSemanticReviewer"
            ),
            "feedback_type": "preexecution_metric_protocol_upstream_theory_revision",
            "trigger": (
                "METRIC_PROTOCOL_REVIEW_REQUIRES_OWNER_CLARIFICATION"
                if ownership_clarification_required
                else "METRIC_PROTOCOL_REVIEW_REQUIRES_UPSTREAM_THEORY_REVISION"
            ),
            "failure_classification": (
                "architect_metric_protocol_upstream_theory_revision_required"
            ),
            "question_id": question.id,
            "source_task_id": task.task_id,
            "source_owner_subsystem": task.owner_subsystem,
            "target_consumer_subsystem": "TheoryDeveloper",
            "source_metric_protocol_rejection_manifest_id": manifest_id,
            "repair_ownership_packet_id": str(
                final_review.get("repair_ownership_packet_id", "") or ""
            ),
            "repair_ownership_packet_hash": str(
                final_review.get("repair_ownership_packet_hash", "") or ""
            ),
            "source_theory_packet_id": source_theory_packet_id,
            "source_theory_packet_hash": source_theory_packet_hash,
            "recommended_repair_scope": recommended_repair_scope,
            "ownership_clarification_required": (
                ownership_clarification_required
            ),
            "upstream_theory_revision_count": next_revision_count,
            "max_upstream_theory_revisions": max_theory_revisions,
            "dimension_reviews": [
                dict(row)
                for row in final_review.get("dimension_reviews", []) or []
                if isinstance(row, Mapping)
            ],
            "findings": upstream_findings,
            "repair_instructions": upstream_repair_instructions,
            "high_priority_agenda": upstream_findings,
            "required_revision": (
                (
                    "Clarify or revise the TheoryDeveloper packet so the unresolved "
                    "artifact ownership can be decided from explicit estimand, DGP, "
                    "derivation, calibration, and feasibility material. Do not patch "
                    "the rejected metric rows or invent observed results."
                )
                if ownership_clarification_required
                else (
                    "Revise the TheoryDeveloper packet itself so its estimand, "
                    "procedure, estimator, DGP, assumptions, derivation, and "
                    "feasibility claims are internally consistent and sufficiently "
                    "specified for independent metric authoring. Do not patch the "
                    "rejected metric rows or invent observed results."
                )
            ),
            "acceptance_gate": (
                "A fresh structured TheoryDeveloper packet addresses every routed "
                "upstream finding; a fresh metric candidate then receives independent "
                "pre-execution review before any generated execution."
            ),
            "generated_code_observed": False,
            "simulation_results_observed": False,
            "execution_authorized": False,
            "proof_evidence_status": (
                "METRIC_PROTOCOL_UPSTREAM_THEORY_FEEDBACK_NOT_PROOF_EVIDENCE"
            ),
            "boundary": (
                "This is pre-execution semantic feedback for LLM theory revision. "
                "It is not generated execution, statistical acceptance, or theorem "
                "proof evidence."
            ),
        }
        produced_artifacts[feedback_id] = feedback
        next_context = dict(context)
        next_context.pop("architect_metric_protocol_theory_material", None)
        next_context["previous_theory_packet_id"] = source_theory_packet_id
        next_context["environment_feedback"] = feedback
        prior_rejection_ids = [
            str(value)
            for value in metric_gate.get("rejection_manifest_ids", []) or []
            if str(value).strip()
        ]
        next_context["architect_metric_protocol_gate"] = {
            **dict(metric_gate),
            "artifact_kind": "RuntimeArchitectMetricProtocolGate",
            "source_theory_packet_id": source_theory_packet_id,
            "source_theory_revision_feedback_id": feedback_id,
            "rejection_manifest_ids": list(
                dict.fromkeys([*prior_rejection_ids, manifest_id])
            ),
            "upstream_theory_revision_count": next_revision_count,
            "max_upstream_theory_revisions": max_theory_revisions,
            "required_disposition": "REVISED_THEORY_THEN_PREEXECUTION_REVIEW_ACCEPTED",
            "execution_authorized": False,
            "consumed": False,
            "proof_evidence_status": (
                "ARCHITECT_METRIC_PROTOCOL_GATE_NOT_PROOF_EVIDENCE"
            ),
        }
        next_task = AgentTask(
            task_id=(
                f"theory-metric-protocol-revision:{question.id}:"
                f"{stable_hash([feedback_id, next_revision_count])[:8]}"
            ),
            owner_subsystem="TheoryDeveloper",
            objective=(
                "Clarify or revise the upstream statistical theory from independent "
                "pre-execution metric-review feedback."
            ),
            inputs={
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "description": question.description,
                    "tags": list(question.tags),
                },
                "architect_context": next_context,
                "environment_feedback": feedback,
            },
            allowed_tools=("model_backend", "rag_memory", "evidence_ledger"),
            expected_artifacts=("theory_derivation_packet",),
            acceptance_gate=str(feedback["acceptance_gate"]),
            stop_condition=(
                "revised theory is independently re-reviewed through a fresh "
                "pre-execution metric protocol"
            ),
        )
        status = "REROUTE"
        failure_classification = (
            "architect_metric_protocol_upstream_theory_revision_requested"
        )
        rationale = (
            (
                "Independent ownership review could not determine whether the metric "
                "author can repair the finding without additional source-theory "
                "semantics. The rejected lineage is preserved and the finding is "
                "routed to TheoryDeveloper for bounded clarification; no coding or "
                "simulation execution is authorized."
            )
            if ownership_clarification_required
            else (
                "Independent pre-execution review found an upstream theory defect. "
                "The rejected metric lineage is preserved and the typed findings are "
                "routed to TheoryDeveloper within the configured revision budget; no "
                "coding or simulation execution is authorized."
            )
        )

    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
        task_id=task.task_id,
        artifact_id=manifest_id,
        evidence_type="metric_protocol_preexecution_rejection",
        status=(
            "PREEXECUTION_PROTOCOL_REJECTED_THEORY_REVISION_ROUTED"
            if route_upstream_theory
            else "PREEXECUTION_PROTOCOL_REJECTED_NO_EXECUTION_AUTHORIZED"
        ),
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
        status=status,
        rationale=rationale,
        produced_artifacts=produced_artifacts,
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
        next_task=next_task,
        failure_classification=failure_classification,
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
