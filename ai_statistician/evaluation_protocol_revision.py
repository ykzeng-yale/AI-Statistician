from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
)
from .fingerprint import stable_hash
from .llm_json_repair import PacketValidationError
from .generated_metric_contract import (
    generated_metric_requirement_set_id,
    is_generated_metric_numeric_authority_error,
)
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
)
from .architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY,
)
from .architect_metric_repair_ownership_router_llm import (
    ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED,
)
from .research_schema import OpenResearchQuestion


EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION = 1


def invalidate_metric_protocol_authorization(
    architect_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Return context for a new theory/protocol candidate with no stale authority."""

    context = deepcopy(dict(architect_context))
    plan = context.get("architect_runtime_plan", {})
    plan = deepcopy(dict(plan)) if isinstance(plan, Mapping) else {}
    contract = plan.get("evidence_contract", {})
    contract = deepcopy(dict(contract)) if isinstance(contract, Mapping) else {}
    for field in (
        "empirical_metric_requirement_set_id",
        "empirical_metric_requirements_frozen_from_prior_architect_plan",
        "empirical_metric_requirements_frozen_from_metric_planner",
        "empirical_metric_requirements_preexecution_review",
    ):
        contract.pop(field, None)
    contract["empirical_metric_requirements"] = []
    contract["empirical_metric_protocol_phase"] = (
        METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED
    )
    contract["metric_protocol_execution_authorized"] = False
    plan["evidence_contract"] = contract
    context["architect_runtime_plan"] = plan
    context.pop("architect_metric_requirement_authoring", None)
    return context


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


def architect_metric_requirement_validation_failure_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
    exc: PacketValidationError,
    max_upstream_theory_revisions: int,
    runtime_architect_control: Mapping[str, Any] | None = None,
) -> AgentStepResult:
    """Fail closed after exhausted authoring without laundering candidate choices."""

    validation_errors = [str(error) for error in exc.errors if str(error)]
    numeric_authority_failure = any(
        is_generated_metric_numeric_authority_error(error)
        for error in validation_errors
    )
    context = invalidate_metric_protocol_authorization(architect_context)
    theory_material = context.get(
        "architect_metric_protocol_theory_material",
        {},
    )
    theory_material = (
        dict(theory_material) if isinstance(theory_material, Mapping) else {}
    )
    source_theory_packet_id = str(
        theory_material.get("source_theory_packet_id", "")
        or context.get("theory_packet_id", "")
        or ""
    )
    parent_theory_packet = blackboard.artifacts.get(
        source_theory_packet_id,
        {},
    )
    parent_theory_packet = (
        dict(parent_theory_packet)
        if isinstance(parent_theory_packet, Mapping)
        else {}
    )
    source_theory_packet_hash = (
        stable_hash(parent_theory_packet) if parent_theory_packet else ""
    )
    metric_gate = context.get("architect_metric_protocol_gate", {})
    metric_gate = dict(metric_gate) if isinstance(metric_gate, Mapping) else {}
    revisions_used = max(
        0,
        int(metric_gate.get("upstream_theory_revision_count", 0) or 0),
    )
    revision_limit = max(0, int(max_upstream_theory_revisions or 0))
    failure_id = "architect_metric_requirement_validation_failure:" + stable_hash(
        [
            question.id,
            task.task_id,
            source_theory_packet_id,
            validation_errors,
            exc.history,
        ]
    )[:20]
    boundary = (
        "This artifact records an LLM metric-authoring packet rejected by the "
        "runtime validator before generated execution. Candidate-owned numeric "
        "choices remain metric-contract defects and cannot trigger a theory revision; "
        "neither the failed packet nor its values are statistical acceptance or "
        "theorem proof evidence."
    )
    failure_artifact = {
        "schema_version": EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION,
        "artifact_kind": "RuntimeArchitectMetricRequirementValidationFailure",
        "failure_id": failure_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "task_id": task.task_id,
        "validation_label": exc.validation_label,
        "validation_errors": validation_errors,
        "validation_attempts": exc.attempts,
        "llm_json_repair_history": [dict(row) for row in exc.history],
        "numeric_authority_failure": numeric_authority_failure,
        "source_theory_packet_id": source_theory_packet_id,
        "source_theory_packet_hash": source_theory_packet_hash,
        "upstream_theory_revisions_used": revisions_used,
        "max_upstream_theory_revisions": revision_limit,
        "repair_owner": "metric_contract",
        "upstream_theory_revision_routed": False,
        "execution_authorized": False,
        "proof_evidence_status": (
            "ARCHITECT_METRIC_REQUIREMENT_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
        ),
        "boundary": boundary,
    }
    architect_control = deepcopy(dict(runtime_architect_control or {}))
    if architect_control:
        failure_artifact["runtime_architect_control"] = architect_control
    produced_artifacts: dict[str, dict[str, Any]] = {failure_id: failure_artifact}
    failure_classification = (
        "architect_metric_requirement_candidate_authority_invalid"
        if numeric_authority_failure
        else "architect_metric_requirement_packet_validation_failed"
    )
    rationale = (
        "Architect metric authoring exhausted local packet repair and remained "
        "blocked. Candidate-owned gate choices stay with the metric contract rather "
        "than being copied into TheoryDeveloper; generated execution stays "
        "unauthorized."
    )

    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, failure_id])[:20],
        task_id=task.task_id,
        artifact_id=failure_id,
        evidence_type="architect_metric_requirement_validation_failure",
        status="METRIC_AUTHORING_VALIDATION_BLOCKED_NOT_EVIDENCE",
        boundary=boundary,
        payload={
            "validation_errors": validation_errors,
            "numeric_authority_failure": numeric_authority_failure,
            "repair_owner": "metric_contract",
            "upstream_theory_revision_routed": False,
            "execution_authorized": False,
            "kernel_verified": False,
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=rationale,
        produced_artifacts=produced_artifacts,
        observations=(
            EnvironmentObservation(
                observation_type=(
                    "architect_metric_requirement_validation_failure"
                ),
                summary=rationale[:500],
                payload={
                    "failure_id": failure_id,
                    "validation_errors": validation_errors,
                    "next_owner_subsystem": "",
                    "execution_authorized": False,
                    "proof_evidence_status": failure_artifact[
                        "proof_evidence_status"
                    ],
                },
            ),
        ),
        evidence_entries=(evidence,),
        next_task=None,
        failure_classification=failure_classification,
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
        next_context = invalidate_metric_protocol_authorization(context)
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
    max_fresh_candidate_revisions: int = 0,
    base_seed: int = 0,
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
    structural_findings = _post_result_protocol_structural_findings(replan)
    prior_cycle = architect_context.get(
        "runtime_evaluation_protocol_revision_cycle", {}
    )
    if not isinstance(prior_cycle, Mapping):
        prior_cycle = {}
    try:
        revisions_used = max(
            0, int(prior_cycle.get("fresh_candidate_revisions_used", 0) or 0)
        )
    except (TypeError, ValueError):
        revisions_used = 0
    max_revisions = max(0, int(max_fresh_candidate_revisions or 0))
    fresh_candidate_auto_routed = bool(
        requirement_set_id
        and requirement_rows
        and structural_findings
        and revisions_used < max_revisions
    )
    next_revision_count = (
        revisions_used + 1 if fresh_candidate_auto_routed else revisions_used
    )
    fresh_candidate_id = ""
    fresh_candidate_seed: int | None = None
    if fresh_candidate_auto_routed:
        fresh_candidate_id = "evaluation_protocol_candidate:" + stable_hash(
            [
                question.id,
                requirement_set_id,
                replan.get("review_execution_id", ""),
                next_revision_count,
            ]
        )[:20]
        fresh_candidate_seed = _versioned_fresh_candidate_seed(
            base_seed=base_seed,
            question_id=question.id,
            source_requirement_set_id=requirement_set_id,
            source_review_execution_id=str(
                replan.get("review_execution_id", "") or ""
            ),
            revision_count=next_revision_count,
        )
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
        "fresh_candidate_auto_routed": fresh_candidate_auto_routed,
        "fresh_candidate_id": fresh_candidate_id,
        "fresh_candidate_seed": fresh_candidate_seed,
        "fresh_candidate_revision_count": next_revision_count,
        "max_fresh_candidate_revisions": max_revisions,
        "fresh_candidate_feedback_sanitized": True,
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
    next_task: AgentTask | None = None
    status = "BLOCKED"
    failure_classification = "evaluation_protocol_revision_required"
    rationale = (
        "Independent post-execution semantic review identified the frozen "
        "metric contract as the blocker. The current candidate is stopped with "
        "EVALUATION_PROTOCOL_REVISION_REQUIRED; its artifacts and requirement "
        "fingerprint are preserved, and only a fresh independently reviewed "
        "protocol run may continue."
    )
    if fresh_candidate_auto_routed and fresh_candidate_seed is not None:
        next_context = _fresh_protocol_candidate_architect_context(
            architect_context=architect_context,
            revision_manifest=manifest,
            source_requirement_rows=requirement_rows,
            structural_findings=structural_findings,
            fresh_candidate_id=fresh_candidate_id,
            fresh_candidate_seed=fresh_candidate_seed,
            revision_count=next_revision_count,
            max_revisions=max_revisions,
        )
        next_task = AgentTask(
            task_id=(
                f"architect-fresh-metric-protocol:{question.id}:"
                f"{stable_hash([manifest_id, fresh_candidate_id])[:8]}"
            ),
            owner_subsystem="ArchitectCoordinator",
            objective=(
                "Author and independently review a versioned fresh metric "
                "protocol after preserving the rejected candidate."
            ),
            inputs={
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "description": question.description,
                    "tags": list(question.tags),
                },
                "architect_context": next_context,
                "environment_feedback": next_context[
                    "architect_metric_protocol_fresh_candidate_revision"
                ],
            },
            allowed_tools=("model_backend", "blackboard", "evidence_ledger"),
            expected_artifacts=("architect_coordinator_proposal",),
            acceptance_gate=(
                "a different requirement-set fingerprint passes independent "
                "pre-execution review before fresh-seed execution"
            ),
            stop_condition=(
                "fresh candidate executes under its new frozen protocol or the "
                "bounded revision budget fails closed"
            ),
        )
        status = "REROUTE"
        failure_classification = "evaluation_protocol_fresh_candidate_requested"
        rationale = (
            "The rejected candidate and requirement fingerprint remain immutable. "
            "Within the configured budget, ArchitectCoordinator is starting a "
            "versioned candidate from sanitized structural feedback; its protocol "
            "must receive independent pre-execution review and all confirmatory "
            "simulation must rerun under a fresh seed."
        )
    return AgentStepResult(
        status=status,
        rationale=rationale,
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
                    "fresh_candidate_auto_routed": fresh_candidate_auto_routed,
                    "fresh_candidate_id": fresh_candidate_id,
                    "fresh_candidate_seed": fresh_candidate_seed,
                    "proof_evidence_status": manifest["proof_evidence_status"],
                },
            ),
        ),
        evidence_entries=(evidence,),
        next_task=next_task,
        failure_classification=failure_classification,
    )


def _post_result_protocol_structural_findings(
    replan: Mapping[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for index, row in enumerate(replan.get("findings", []) or []):
        if not isinstance(row, Mapping):
            continue
        required_change = str(row.get("required_change", "") or "").strip()
        if not required_change:
            continue
        findings.append(
            {
                "source_finding_index": index,
                "severity": str(row.get("severity", "") or ""),
                "category": str(row.get("category", "") or ""),
                "required_change": required_change,
            }
        )
    return findings


def _versioned_fresh_candidate_seed(
    *,
    base_seed: int,
    question_id: str,
    source_requirement_set_id: str,
    source_review_execution_id: str,
    revision_count: int,
) -> int:
    modulus = 2_147_483_647
    seed = int(
        stable_hash(
            [
                int(base_seed),
                question_id,
                source_requirement_set_id,
                source_review_execution_id,
                int(revision_count),
            ]
        )[:12],
        16,
    ) % modulus
    if seed == int(base_seed) % modulus:
        seed = (seed + 1) % modulus
    return seed or 1


def _fresh_protocol_candidate_architect_context(
    *,
    architect_context: Mapping[str, Any],
    revision_manifest: Mapping[str, Any],
    source_requirement_rows: list[dict[str, Any]],
    structural_findings: list[dict[str, Any]],
    fresh_candidate_id: str,
    fresh_candidate_seed: int,
    revision_count: int,
    max_revisions: int,
) -> dict[str, Any]:
    context = invalidate_metric_protocol_authorization(architect_context)

    for field in (
        "architect_metric_requirement_authoring",
        "architect_metric_protocol_prior_rejection",
        "runtime_generated_code_semantic_review_replan",
        "runtime_metric_gate_replan",
        "runtime_feedback_loop",
        "simulation_manifest_id",
    ):
        context.pop(field, None)
    source_manifest_id = str(
        revision_manifest.get("source_manifest_id", "") or ""
    )
    if source_manifest_id:
        context["previous_simulation_manifest_id"] = source_manifest_id

    theory_material = context.get(
        "architect_metric_protocol_theory_material", {}
    )
    if not isinstance(theory_material, Mapping):
        theory_material = {}

    revision_context = {
        "artifact_kind": "RuntimeEvaluationProtocolFreshCandidateContext",
        "source_revision_manifest_id": str(
            revision_manifest.get("manifest_id", "") or ""
        ),
        "source_revision_manifest_hash": stable_hash(dict(revision_manifest)),
        "source_requirement_set_id": str(
            revision_manifest.get("source_requirement_set_id", "") or ""
        ),
        "source_requirement_set_fingerprint": str(
            revision_manifest.get("source_requirement_set_fingerprint", "") or ""
        ),
        "source_requirement_rows": deepcopy(source_requirement_rows),
        "structural_review_findings": deepcopy(structural_findings),
        "current_source_theory_packet_id": str(
            theory_material.get("source_theory_packet_id", "") or ""
        ),
        "current_source_theory_packet_hash": str(
            theory_material.get("source_theory_packet_hash", "") or ""
        ),
        "fresh_candidate_id": fresh_candidate_id,
        "fresh_candidate_seed": fresh_candidate_seed,
        "fresh_candidate_revision_count": revision_count,
        "max_fresh_candidate_revisions": max_revisions,
        "prior_candidate_execution_observed": True,
        "raw_execution_artifacts_included": False,
        "structural_feedback_may_summarize_prior_observations": True,
        "post_result_threshold_relaxation_allowed": False,
        "different_requirement_set_required": True,
        "all_confirmatory_artifacts_must_rerun": True,
        "proof_evidence_status": (
            "EVALUATION_PROTOCOL_FRESH_CANDIDATE_CONTEXT_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "This context excludes raw execution artifacts but exposes prior frozen "
            "requirements and reviewer-authored structural changes, which may "
            "summarize observed failures. It may start a versioned candidate but "
            "cannot rehabilitate the failed candidate or authorize post-result "
            "threshold relaxation."
        ),
    }
    context["architect_metric_protocol_fresh_candidate_revision"] = (
        revision_context
    )
    context["environment_feedback"] = revision_context
    context["runtime_candidate_id"] = fresh_candidate_id
    context["runtime_candidate_seed"] = fresh_candidate_seed
    context["runtime_evaluation_protocol_revision_cycle"] = {
        "artifact_kind": "RuntimeEvaluationProtocolRevisionCycle",
        "fresh_candidate_revisions_used": revision_count,
        "max_fresh_candidate_revisions": max_revisions,
        "current_candidate_id": fresh_candidate_id,
        "source_revision_manifest_id": revision_context[
            "source_revision_manifest_id"
        ],
        "proof_evidence_status": (
            "EVALUATION_PROTOCOL_REVISION_CYCLE_NOT_PROOF_EVIDENCE"
        ),
    }

    metric_gate = context.get("architect_metric_protocol_gate", {})
    metric_gate = dict(metric_gate) if isinstance(metric_gate, Mapping) else {}
    for field in ("accepted_requirement_set_id", "deferred_next_task"):
        metric_gate.pop(field, None)
    metric_gate.update(
        {
            "artifact_kind": "RuntimeArchitectMetricProtocolGate",
            "source_requirement_set_id": revision_context[
                "source_requirement_set_id"
            ],
            "fresh_candidate_id": fresh_candidate_id,
            "fresh_candidate_revision_count": revision_count,
            "max_fresh_candidate_revisions": max_revisions,
            "required_disposition": "FRESH_PREEXECUTION_REVIEW_ACCEPTED",
            "execution_authorized": False,
            "consumed": False,
            "proof_evidence_status": (
                "ARCHITECT_METRIC_PROTOCOL_GATE_NOT_PROOF_EVIDENCE"
            ),
        }
    )
    context["architect_metric_protocol_gate"] = metric_gate
    return context
