from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Mapping

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    runtime_artifact_reference,
)
from .architect_theory_execution_preflight import (
    architect_theory_preflight_workspace_continuation_errors,
)
from .fingerprint import stable_hash
from .structured_output_retry import PacketValidationError
from .generated_metric_contract import (
    is_generated_metric_numeric_authority_error,
)
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND,
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
)
from .research_schema import OpenResearchQuestion, research_question_payload
from .theory_revision_lineage import (
    RUNTIME_THEORY_REVISION_PROGRESS_CONTEXT_KEY,
)
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


def metric_protocol_preexecution_review_observation_errors(
    feedback: Mapping[str, Any],
    *,
    question_id: str,
    parent_theory_packet: Mapping[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    if feedback.get("artifact_kind") != (
        METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND
    ):
        errors.append("feedback artifact_kind is not a pre-execution review observation")
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
    if feedback.get("execution_authorized") is not False:
        errors.append("feedback must keep generated execution unauthorized")
    findings = feedback.get("findings", [])
    if not isinstance(findings, list):
        errors.append("feedback findings must be an array")
        findings = []
    if not findings:
        errors.append("feedback requires an observed finding")
    if findings:
        for index, finding in enumerate(findings):
            if not isinstance(finding, Mapping):
                errors.append(f"feedback finding {index} is not an object")

    try:
        revision_count = int(
            feedback.get("upstream_theory_revision_count", 0) or 0
        )
    except (TypeError, ValueError):
        revision_count = 0
        errors.append("feedback theory revision count is not integer-valued")
    if revision_count <= 0:
        errors.append("feedback upstream theory revision count must be positive")
    if feedback.get("continuation_budget_authority") != (
        "AgentRuntime.max_iterations"
    ):
        errors.append("feedback continuation budget authority is invalid")

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


def metric_protocol_preexecution_review_observation_blocked_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    feedback: Mapping[str, Any],
    validation_errors: list[str],
) -> AgentStepResult:
    errors = [str(value) for value in validation_errors if str(value).strip()]
    artifact_id = "metric_protocol_preexecution_observation_blocked:" + stable_hash(
        [question.id, task.task_id, feedback.get("feedback_id", ""), errors]
    )[:20]
    artifact = {
        "schema_version": EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION,
        "artifact_kind": "RuntimeMetricProtocolPreExecutionReviewObservationBlocked",
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
            "METRIC_PROTOCOL_PREEXECUTION_OBSERVATION_INVALID_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "The runtime rejected incomplete or mismatched pre-execution observation "
            "lineage before calling the selected model. This is a control-plane blocker, "
            "not generated execution, statistical acceptance, or proof evidence."
        ),
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, artifact_id])[:20],
        task_id=task.task_id,
        artifact_id=artifact_id,
        evidence_type="metric_protocol_preexecution_observation_rejection",
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
            "The Architect-routed pre-execution observation could not be bound to its "
            "immutable parent theory packet, so the selected model was not called."
        ),
        produced_artifacts={artifact_id: artifact},
        observations=(
            EnvironmentObservation(
                observation_type="metric_protocol_preexecution_observation_invalid",
                summary="pre-execution observation lineage failed closed",
                payload={
                    "artifact_id": artifact_id,
                    "validation_errors": errors,
                    "execution_authorized": False,
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification="metric_protocol_preexecution_observation_invalid",
    )


def architect_metric_requirement_validation_failure_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    blackboard: BlackboardState,
    exc: PacketValidationError,
    runtime_architect_control: Mapping[str, Any] | None = None,
) -> AgentStepResult:
    """Fail closed after exhausted authoring without laundering candidate choices."""

    validation_errors = [str(error) for error in exc.errors if str(error)]
    raw_workspace_checkpoint = getattr(exc, "recovery_checkpoint", None)
    workspace_checkpoint = (
        deepcopy(dict(raw_workspace_checkpoint))
        if isinstance(raw_workspace_checkpoint, Mapping)
        and raw_workspace_checkpoint.get("artifact_kind")
        == "MetricProtocolWorkspaceCheckpoint"
        and raw_workspace_checkpoint.get("runtime_edited_content") is False
        and raw_workspace_checkpoint.get("automatic_retry_authorized") is False
        else {}
    )
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
    final_invalid_packet = (
        dict(exc.last_invalid_packet)
        if isinstance(exc.last_invalid_packet, Mapping)
        else {}
    )
    final_invalid_requirements = [
        dict(row)
        for row in final_invalid_packet.get(
            "empirical_metric_requirements", []
        )
        if isinstance(row, Mapping)
    ]
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
        "structured_output_retry_history": [dict(row) for row in exc.history],
        "metric_protocol_workspace_checkpoint_available": bool(
            workspace_checkpoint
        ),
        **(
            {"metric_protocol_workspace_checkpoint": workspace_checkpoint}
            if workspace_checkpoint
            else {}
        ),
        "final_invalid_packet_available": bool(final_invalid_packet),
        "final_invalid_packet_fingerprint": (
            stable_hash(final_invalid_packet) if final_invalid_packet else ""
        ),
        "final_invalid_empirical_metric_requirements": (
            final_invalid_requirements
        ),
        "numeric_authority_failure": numeric_authority_failure,
        "source_theory_packet_id": source_theory_packet_id,
        "source_theory_packet_hash": source_theory_packet_hash,
        "upstream_theory_revisions_used": revisions_used,
        "continuation_budget_authority": "AgentRuntime.max_iterations",
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
        "Architect metric authoring exhausted bounded packet validation retries "
        "and remained blocked. Candidate-owned gate choices stay with the metric "
        "contract rather than being copied into TheoryDeveloper; generated "
        "execution stays unauthorized."
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
                    "metric_protocol_workspace_checkpoint_available": bool(
                        workspace_checkpoint
                    ),
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


def architect_metric_semantic_review_validation_failure_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    exc: PacketValidationError,
    review_stage: str = "metric_semantic_review",
) -> AgentStepResult:
    """Preserve an exhausted reviewer packet as typed control-plane evidence."""

    context = invalidate_metric_protocol_authorization(architect_context)
    theory_preflight = review_stage == "theory_execution_preflight"
    recovery_checkpoint_value = getattr(exc, "recovery_checkpoint", None)
    recovery_checkpoint = (
        deepcopy(dict(recovery_checkpoint_value))
        if theory_preflight and isinstance(recovery_checkpoint_value, Mapping)
        else {}
    )
    prior_checkpoint_value = task.inputs.get(
        "theory_preflight_workspace_checkpoint", {}
    )
    prior_checkpoint = (
        dict(prior_checkpoint_value)
        if isinstance(prior_checkpoint_value, Mapping)
        else {}
    )
    workspace_continuation_errors = (
        architect_theory_preflight_workspace_continuation_errors(
            recovery_checkpoint,
            prior_checkpoint=prior_checkpoint or None,
        )
        if recovery_checkpoint
        else ["independent referee returned no workspace checkpoint"]
    ) if theory_preflight else []
    workspace_continuation_allowed = bool(
        theory_preflight
        and recovery_checkpoint
        and not workspace_continuation_errors
    )
    checkpoint_id = (
        str(recovery_checkpoint.get("checkpoint_id", "") or "")
        if workspace_continuation_allowed
        else ""
    )
    continuation_count = int(
        task.inputs.get("theory_preflight_workspace_continuation_count", 0) or 0
    ) + int(workspace_continuation_allowed)
    validation_errors = [str(error) for error in exc.errors if str(error)]
    authoring_packet_value = getattr(exc, "authoring_packet", None)
    authoring_packet = (
        deepcopy(dict(authoring_packet_value))
        if isinstance(authoring_packet_value, Mapping)
        else {}
    )
    authoring_packet_id = str(authoring_packet.get("packet_id", "") or "")
    observed_authoring_packet_hash = (
        stable_hash(authoring_packet) if authoring_packet else ""
    )
    trusted_review_lineage_value = getattr(
        exc, "trusted_review_lineage", None
    )
    trusted_review_lineage = (
        deepcopy(dict(trusted_review_lineage_value))
        if isinstance(trusted_review_lineage_value, Mapping)
        else {}
    )
    expected_authoring_packet_hash = str(
        getattr(exc, "authoring_packet_hash", "") or ""
    )
    authoring_packet_persisted = bool(
        authoring_packet
        and authoring_packet.get("artifact_kind")
        == "ArchitectMetricRequirementAuthoringPacket"
        and authoring_packet_id
        and str(authoring_packet.get("question_id", "") or "") == question.id
        and not authoring_packet.get("semantic_review_status")
        and not authoring_packet.get("semantic_review_packet")
        and authoring_packet.get("metric_protocol_execution_authorized") is not True
        and expected_authoring_packet_hash == observed_authoring_packet_hash
        and str(trusted_review_lineage.get("authoring_packet_id", "") or "")
        == authoring_packet_id
        and str(trusted_review_lineage.get("authoring_packet_hash", "") or "")
        == observed_authoring_packet_hash
    )
    authoring_packet_integrity_errors = (
        []
        if not authoring_packet or authoring_packet_persisted
        else ["attached authoring packet failed replay-lineage validation"]
    )
    semantic_review_history_value = getattr(
        exc, "semantic_review_history", None
    )
    semantic_review_history = (
        [
            deepcopy(dict(row))
            for row in semantic_review_history_value
            if isinstance(row, Mapping)
        ]
        if isinstance(semantic_review_history_value, list)
        else []
    )
    last_invalid_packet = (
        dict(exc.last_invalid_packet)
        if isinstance(exc.last_invalid_packet, Mapping)
        else {}
    )
    review_projection = {
        key: deepcopy(last_invalid_packet.get(key))
        for key in (
            "packet_id",
            "authoring_packet_id",
            "authoring_packet_hash",
            "reviewed_empirical_metric_requirement_set_id",
            "review_input_fingerprint",
            "model_requested_overall_verdict",
            "overall_verdict",
            "prior_finding_reviews",
            "requirement_reviews",
            "portfolio_review",
            "estimator_execution_checks",
            "findings",
            "proof_evidence_status",
        )
        if key in last_invalid_packet
    }
    failure_id = (
        (
            "architect_theory_execution_preflight_validation_failure:"
            if theory_preflight
            else "architect_metric_semantic_review_validation_failure:"
        )
        + stable_hash(
            [
                question.id,
                task.task_id,
                validation_errors,
                exc.history,
                review_projection,
                authoring_packet_id,
                observed_authoring_packet_hash,
                int(getattr(exc, "revision_index", 0) or 0),
                str(getattr(exc, "review_material_fingerprint", "") or ""),
                checkpoint_id,
            ]
        )[:20]
    )
    boundary = (
        "This artifact records an independently generated theory/executability "
        "preflight packet that remained structurally invalid after bounded client-"
        "tool feedback. It authorizes neither implementation nor confirmatory "
        "simulation and is not statistical acceptance or theorem proof evidence."
        if theory_preflight
        else (
            "This artifact records an independently generated pre-execution metric "
            "review packet that remained structurally invalid after bounded repair. "
            "Its locally validated author candidate is preserved for deterministic "
            "review replay when exact lineage is available, but remains unauthorized. "
            "The invalid review is feedback for the reviewer interface and is not "
            "execution, statistical acceptance, or theorem proof evidence."
        )
    )
    artifact = {
        "schema_version": EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION,
        "artifact_kind": (
            "RuntimeArchitectTheoryExecutionPreflightValidationFailure"
            if theory_preflight
            else "RuntimeArchitectMetricSemanticReviewValidationFailure"
        ),
        "failure_id": failure_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "task_id": task.task_id,
        "validation_label": exc.validation_label,
        "validation_errors": validation_errors,
        "validation_attempts": exc.attempts,
        "structured_output_retry_history": [dict(row) for row in exc.history],
        "authoring_packet_available": bool(authoring_packet),
        "authoring_packet_id": authoring_packet_id,
        "authoring_packet_hash": observed_authoring_packet_hash,
        "authoring_packet_persisted": authoring_packet_persisted,
        "authoring_packet_integrity_errors": authoring_packet_integrity_errors,
        "semantic_review_revision_index": int(
            getattr(exc, "revision_index", 0) or 0
        ),
        "review_material_fingerprint": str(
            getattr(exc, "review_material_fingerprint", "") or ""
        ),
        "trusted_review_lineage": trusted_review_lineage,
        "prior_semantic_review_history": semantic_review_history,
        "prior_semantic_review_history_fingerprint": (
            stable_hash(semantic_review_history)
            if semantic_review_history
            else ""
        ),
        "last_invalid_packet_available": bool(last_invalid_packet),
        "last_invalid_packet_fingerprint": (
            stable_hash(last_invalid_packet) if last_invalid_packet else ""
        ),
        "last_invalid_review_projection": review_projection,
        **(
            {
                "referee_workspace_checkpoint_available": bool(
                    recovery_checkpoint
                ),
                "referee_workspace_checkpoint_id": checkpoint_id,
                "referee_workspace_checkpoint_hash": (
                    stable_hash(recovery_checkpoint)
                    if recovery_checkpoint
                    else ""
                ),
                "referee_workspace_continuation_allowed": (
                    workspace_continuation_allowed
                ),
                "referee_workspace_continuation_errors": (
                    workspace_continuation_errors
                ),
                "referee_workspace_continuation_count": continuation_count,
            }
            if theory_preflight
            else {}
        ),
        "metric_protocol_execution_authorized": False,
        "implementation_authorized": False,
        "runtime_architect_control": {
            "metric_protocol_execution_authorized": False,
            "architect_context_fingerprint": stable_hash(context),
        },
        "proof_evidence_status": (
            "ARCHITECT_THEORY_EXECUTION_PREFLIGHT_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
            if theory_preflight
            else "ARCHITECT_METRIC_SEMANTIC_REVIEW_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
        ),
        "boundary": boundary,
    }
    produced_artifacts = {}
    if authoring_packet_persisted:
        produced_artifacts[authoring_packet_id] = authoring_packet
    if workspace_continuation_allowed:
        produced_artifacts[checkpoint_id] = recovery_checkpoint
    produced_artifacts[failure_id] = artifact
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, failure_id])[:20],
        task_id=task.task_id,
        artifact_id=failure_id,
        evidence_type=(
            "architect_theory_execution_preflight_validation_failure"
            if theory_preflight
            else "architect_metric_semantic_review_validation_failure"
        ),
        status="PREEXECUTION_REVIEW_PACKET_INVALID_NOT_EVIDENCE",
        boundary=boundary,
        payload={
            "validation_errors": validation_errors,
            "validation_attempts": exc.attempts,
            "authoring_packet_id": authoring_packet_id,
            "authoring_packet_hash": observed_authoring_packet_hash,
            "authoring_packet_persisted": authoring_packet_persisted,
            "metric_protocol_execution_authorized": False,
            "implementation_authorized": False,
            **(
                {
                    "referee_workspace_checkpoint_id": checkpoint_id,
                    "referee_workspace_continuation_allowed": (
                        workspace_continuation_allowed
                    ),
                }
                if theory_preflight
                else {}
            ),
            "kernel_verified": False,
        },
    )
    next_task = None
    if workspace_continuation_allowed:
        next_inputs = deepcopy(dict(task.inputs))
        next_inputs["theory_preflight_workspace_checkpoint"] = (
            runtime_artifact_reference(checkpoint_id, recovery_checkpoint)
        )
        next_inputs["theory_preflight_workspace_continuation_count"] = (
            continuation_count
        )
        next_task = replace(
            task,
            task_id=(
                f"theory-preflight-progress:{question.id}:"
                f"{continuation_count}:{checkpoint_id.rsplit(':', 1)[-1][:10]}"
            ),
            objective=(
                "Continue the same independent theory-referee workspace from its "
                "exact document, source, scratch, and validator observations."
            ),
            inputs=next_inputs,
        )
    return AgentStepResult(
        status="REVISE" if workspace_continuation_allowed else "BLOCKED",
        rationale=(
            "The independent theory referee made new environment-observed progress; "
            "its content-addressed workspace returns to the same reviewer through "
            "the existing outer runtime without Architect replanning."
            if theory_preflight and workspace_continuation_allowed
            else "The independent theory/executability preflight exhausted its "
            "bounded source-review turns without new resumable progress; its exact "
            "lineage was preserved without authorizing implementation or simulation."
            if theory_preflight
            else (
                "The independent metric reviewer exhausted bounded packet repair; "
                "its exact validation lineage was preserved without authorizing "
                "generated execution."
            )
        ),
        produced_artifacts=produced_artifacts,
        observations=(
            EnvironmentObservation(
                observation_type=(
                    "architect_theory_execution_preflight_packet_invalid"
                    if theory_preflight
                    else "architect_metric_semantic_review_packet_invalid"
                ),
                summary="; ".join(validation_errors)[:500],
                payload={
                    "failure_id": failure_id,
                    "validation_errors": validation_errors,
                    "validation_attempts": exc.attempts,
                    "authoring_packet_id": authoring_packet_id,
                    "authoring_packet_hash": observed_authoring_packet_hash,
                    "authoring_packet_persisted": authoring_packet_persisted,
                    "metric_protocol_execution_authorized": False,
                    "implementation_authorized": False,
                    **(
                        {
                            "referee_workspace_checkpoint_id": checkpoint_id,
                            "referee_workspace_continuation_allowed": (
                                workspace_continuation_allowed
                            ),
                            "referee_workspace_continuation_errors": (
                                workspace_continuation_errors
                            ),
                        }
                        if theory_preflight
                        else {}
                    ),
                    "proof_evidence_status": artifact[
                        "proof_evidence_status"
                    ],
                },
            ),
        ),
        evidence_entries=(evidence,),
        next_task=next_task,
        failure_classification=(
            "architect_theory_execution_preflight_workspace_progress"
            if theory_preflight and workspace_continuation_allowed
            else "architect_theory_execution_preflight_packet_validation_failed"
            if theory_preflight
            else "architect_metric_semantic_review_packet_validation_failed"
        ),
    )


def architect_preexecution_metric_protocol_rejection_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    semantic_review_history: list[dict[str, Any]],
    architect_context: Mapping[str, Any] | None = None,
) -> AgentStepResult:
    context = dict(architect_context or {})
    history = [dict(row) for row in semantic_review_history]
    final_review = history[-1] if history else {}
    preexecution_review_stage = str(
        final_review.get("review_stage", "") or "metric_contract_review"
    )
    theory_execution_preflight_rejected = bool(
        preexecution_review_stage == "theory_execution_preflight"
    )
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
    metric_gate = context.get("architect_metric_protocol_gate", {})
    if not isinstance(metric_gate, Mapping):
        metric_gate = {}
    upstream_theory_revision_count = int(
        metric_gate.get("upstream_theory_revision_count", 0) or 0
    )
    prior_finding_resolution_summary = final_review.get(
        "prior_finding_resolution_summary", {}
    )
    prior_finding_resolution_summary = (
        dict(prior_finding_resolution_summary)
        if isinstance(prior_finding_resolution_summary, Mapping)
        else {}
    )
    prior_active_finding_ids = list(
        prior_finding_resolution_summary.get("prior_active_finding_ids", [])
        or []
    )
    prior_finding_progress_made = bool(
        prior_finding_resolution_summary.get("closed_prior_finding_ids", [])
        or prior_finding_resolution_summary.get(
            "resolved_prior_finding_ids", []
        )
        or prior_finding_resolution_summary.get(
            "retracted_prior_finding_ids", []
        )
    )
    if not prior_active_finding_ids:
        prior_finding_progress_made = bool(
            prior_finding_resolution_summary.get("progress_made", False)
        )
    preflight_revision_progressed = bool(
        not theory_execution_preflight_rejected
        or not prior_active_finding_ids
        or prior_finding_progress_made
    )
    theory_revision_continuation_authorized = bool(
        theory_execution_preflight_rejected
        and preflight_revision_progressed
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
        "disposition": (
            "THEORY_EXECUTION_PREFLIGHT_REJECTED"
            if theory_execution_preflight_rejected
            else "METRIC_PROTOCOL_PREEXECUTION_REJECTED"
        ),
        "preexecution_review_stage": preexecution_review_stage,
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
        "prior_finding_resolution_summary": prior_finding_resolution_summary,
        "preflight_revision_progressed": preflight_revision_progressed,
        "preflight_revision_stalled": bool(
            theory_execution_preflight_rejected
            and not preflight_revision_progressed
        ),
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
        "requirement_reviews": [
            dict(row)
            for row in final_review.get("requirement_reviews", []) or []
            if isinstance(row, Mapping)
        ],
        "portfolio_review": dict(
            final_review.get("portfolio_review", {}) or {}
        ),
        "generated_code_observed": False,
        "simulation_results_observed": False,
        "preexecution_evidence_authority": {
            "source_grounded_semantic_review": True,
            "generated_code_observed": False,
            "simulation_results_observed": False,
            "empirical_measurements_observed": False,
            "numeric_execution_claims_authoritative": False,
            "routing_contract": (
                "Treat source-grounded mathematical findings as review judgments. "
                "Any claim that requires generated code, Monte Carlo output, or an "
                "empirical metric must be produced by AlgorithmEngineer or "
                "SimulationEngineer before it can justify theory revision."
            ),
        },
        "current_candidate_acceptance_eligible": False,
        "execution_authorized": False,
        "rejected_lineage_preserved": True,
        "feedback_reusable_for_fresh_preexecution_authoring": True,
        "upstream_theory_revision_count": upstream_theory_revision_count,
        "continuation_budget_authority": "AgentRuntime.max_iterations",
        "upstream_theory_revision_routed": False,
        "architect_route_requested": False,
        "runtime_selected_owner": False,
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
    failure_classification = (
        "architect_theory_execution_preflight_rejected"
        if theory_execution_preflight_rejected
        else "architect_metric_protocol_source_workspace_exhausted"
    )
    status = "BLOCKED"
    rationale = (
        (
            "Independent theory-to-execution preflight rejected the current "
            "TheoryDeveloper handoff before metric authoring. Full review lineage "
            "is preserved for same-owner revision under the existing outer runtime "
            "budget; no coding or simulation execution is authorized."
        )
        if theory_execution_preflight_rejected
        else (
            "Independent pre-execution semantic review rejected every bounded "
            "metric-protocol candidate after the source-owning metric author received "
            "the exact reviewer findings. Full candidate and review lineage is "
            "preserved, the source workspace is blocked, and no coding or simulation "
            "execution is authorized."
        )
    )
    if (
        theory_execution_preflight_rejected
        and not preflight_revision_progressed
    ):
        failure_classification = "architect_theory_execution_preflight_stalled"
        rationale = (
            "Fresh independent review closed none of the prior theory-preflight "
            "findings, so the lineage is stagnant. No coding or simulation execution "
            "is authorized."
        )
    if theory_revision_continuation_authorized:
        next_revision_count = upstream_theory_revision_count + 1
        observed_findings = [
            {
                key: deepcopy(row[key])
                for key in (
                    "finding_id",
                    "severity",
                    "category",
                    "summary",
                    "observed_behavior",
                    "expected_behavior",
                    "evidence_refs",
                    "source_evidence_refs",
                )
                if key in row
            }
            for row in final_review.get("findings", []) or []
            if isinstance(row, Mapping)
        ]
        current_unresolved_finding_reviews = [
            {
                key: deepcopy(row[key])
                for key in (
                    "finding_id",
                    "status",
                    "rationale",
                    "evidence_refs",
                    "source_evidence_refs",
                )
                if key in row
            }
            for row in final_review.get("prior_finding_reviews", []) or []
            if isinstance(row, Mapping)
            and str(row.get("status", "") or "").strip().upper()
            == "UNRESOLVED"
        ]
        feedback_id = "metric_protocol_preexecution_observation:" + stable_hash(
            [
                manifest_id,
                next_revision_count,
                observed_findings,
                current_unresolved_finding_reviews,
            ]
        )[:20]
        feedback = {
            "schema_version": EVALUATION_PROTOCOL_REVISION_SCHEMA_VERSION,
            "artifact_kind": METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND,
            "feedback_id": feedback_id,
            "feedback_source": "ArchitectMetricSemanticReviewer",
            "feedback_type": "preexecution_metric_protocol_review_observation",
            "observation_status": "CURRENT_ACTIVE_OBSERVATION",
            "preexecution_review_stage": preexecution_review_stage,
            "trigger": "THEORY_EXECUTION_PREFLIGHT_REJECTED",
            "failure_classification": (
                "architect_metric_protocol_preexecution_review_rejected"
            ),
            "question_id": question.id,
            "source_task_id": task.task_id,
            "source_owner_subsystem": task.owner_subsystem,
            "source_metric_protocol_rejection_manifest_id": manifest_id,
            "source_theory_packet_id": source_theory_packet_id,
            "source_theory_packet_hash": source_theory_packet_hash,
            "upstream_theory_revision_count": next_revision_count,
            "continuation_budget_authority": "AgentRuntime.max_iterations",
            "requirement_reviews": [
                dict(row)
                for row in final_review.get("requirement_reviews", []) or []
                if isinstance(row, Mapping)
            ],
            "portfolio_review": dict(
                final_review.get("portfolio_review", {}) or {}
            ),
            "findings": observed_findings,
            "current_unresolved_finding_reviews": (
                current_unresolved_finding_reviews
            ),
            "active_unresolved_finding_ids": [
                str(value)
                for value in final_review.get(
                    "active_unresolved_finding_ids", []
                )
                or []
                if str(value).strip()
            ],
            "acceptance_gate": (
                "The same TheoryDeveloper workspace revises its exact parent against "
                "the independent preflight observations; the new candidate then "
                "receives fresh independent review before generated execution."
            ),
            "generated_code_observed": False,
            "simulation_results_observed": False,
            "preexecution_evidence_authority": dict(
                manifest["preexecution_evidence_authority"]
            ),
            "execution_authorized": False,
            "proof_evidence_status": (
                "METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_NOT_PROOF_EVIDENCE"
            ),
            "observation_time_contract": {
                "top_level_observation_is_current": True,
                "historical_error_is_not_an_active_blocker_unless_reobserved": True,
            },
            "progress_observation": {
                "prior_finding_progress_made": preflight_revision_progressed,
                "same_lineage_no_progress_observed": bool(
                    theory_execution_preflight_rejected
                    and not preflight_revision_progressed
                ),
                "runtime_selected_disposition": False,
            },
            "boundary": (
                "This is a current pre-execution semantic observation. A theory-stage "
                "rejection returns to the source-producing TheoryDeveloper workspace by "
                "stage ownership. It contains no runtime-authored repair recipe and is "
                "not execution, statistical acceptance, or proof evidence."
            ),
        }
        produced_artifacts[feedback_id] = feedback
        next_context = invalidate_metric_protocol_authorization(context)
        next_context.pop("architect_metric_protocol_theory_material", None)
        next_context["previous_theory_packet_id"] = source_theory_packet_id
        next_context["environment_feedback"] = feedback
        next_context["theory_developer_source_environment_feedback"] = feedback
        next_context.pop("architect_feedback_route_decision", None)
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
            "continuation_budget_authority": "AgentRuntime.max_iterations",
            "required_disposition": (
                "SOURCE_THEORY_WORKSPACE_REVISION_THEN_FRESH_PREEXECUTION_REVIEW"
            ),
            "execution_authorized": False,
            "consumed": False,
            "proof_evidence_status": (
                "ARCHITECT_METRIC_PROTOCOL_GATE_NOT_PROOF_EVIDENCE"
            ),
        }
        next_context[RUNTIME_THEORY_REVISION_PROGRESS_CONTEXT_KEY] = {
            "revisions_used": next_revision_count,
            "continuation_budget_authority": "AgentRuntime.max_iterations",
            "reset_scope": "fresh_question_runtime_only",
        }
        status = "REROUTE"
        manifest["upstream_theory_revision_routed"] = True
        next_task = AgentTask(
            task_id=(
                f"theory-preflight-revision:{question.id}:"
                f"{stable_hash([feedback_id, next_revision_count])[:8]}"
            ),
            owner_subsystem="TheoryDeveloper",
            objective=(
                "Revise the exact parent theory artifact against the independent "
                "source-grounded preflight observations."
            ),
            inputs={
                "question": research_question_payload(
                    question, include_task_intent=True
                ),
                "architect_context": next_context,
                "environment_feedback": feedback,
                "theory_packet_id": source_theory_packet_id,
            },
            allowed_tools=("model_backend", "rag_memory", "evidence_ledger"),
            expected_artifacts=("theory_derivation_packet",),
            acceptance_gate=str(feedback["acceptance_gate"]),
            stop_condition=(
                "TheoryDeveloper emits one fresh parent-bound candidate or a typed "
                "workspace blocker"
            ),
        )
        failure_classification = (
            "theory_execution_preflight_returned_to_source_workspace"
        )
        rationale = (
            "Independent theory preflight rejected the current source artifact. "
            "The exact observations return directly to the same TheoryDeveloper "
            "workspace under the existing AgentRuntime iteration budget; no "
            "Architect routing model call or runtime-authored repair is used."
        )

    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
        task_id=task.task_id,
        artifact_id=manifest_id,
        evidence_type="metric_protocol_preexecution_rejection",
        status=(
            "THEORY_PREFLIGHT_REJECTED_SOURCE_WORKSPACE_REVISION_REQUESTED"
            if theory_revision_continuation_authorized
            else "PREEXECUTION_PROTOCOL_REJECTED_SOURCE_WORKSPACE_EXHAUSTED"
            if not theory_execution_preflight_rejected
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
