from __future__ import annotations

from typing import Any, Mapping

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    EnvironmentObservation,
    EvidenceLedgerEntry,
)
from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion
from .typed_repair_handoff import build_typed_repair_handoff_contract


GENERATED_CODE_SEMANTIC_REVIEWER_SUBSYSTEM = "GeneratedCodeSemanticReviewer"
GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY = (
    "runtime_generated_code_semantic_review_lineage_ledger"
)
GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_LEDGER_KEY = (
    "runtime_generated_code_semantic_review_upstream_theory_revision_ledger"
)


def generated_code_semantic_review_upstream_theory_revision_state(
    *,
    architect_context: Mapping[str, Any],
    question_id: str,
    max_revisions: int,
) -> dict[str, Any]:
    """Read one question-global budget across all generated-code review lanes."""

    replan = _mapping(
        architect_context.get("runtime_generated_code_semantic_review_replan")
    )
    active = bool(
        replan.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewReplanContext"
        and replan.get("repair_scope") == "upstream_theory"
        and replan.get("review_execution_id")
        and replan.get("source_subsystem")
    )
    lineage_key = stable_hash(
        [question_id, "generated_code_semantic_review", "upstream_theory"]
    )
    active_legacy_lineage_key = stable_hash(
        [
            question_id,
            str(replan.get("source_subsystem", "") or ""),
            "upstream_theory",
        ]
    )
    prior_ledger = architect_context.get(
        GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_LEDGER_KEY,
        {},
    )
    ledger = {
        str(key): dict(value)
        for key, value in (
            prior_ledger.items() if isinstance(prior_ledger, Mapping) else []
        )
        if isinstance(value, Mapping)
    }
    canonical_row = _mapping(ledger.get(lineage_key))
    if canonical_row:
        budget_rows = [(lineage_key, canonical_row)]
    else:
        # Runs written before the question-global budget used one row per source
        # subsystem. Aggregate those rows so resumed work cannot reopen the budget
        # merely by moving a finding between Algorithm and Simulation.
        budget_rows = [
            (key, row)
            for key, row in ledger.items()
            if key == active_legacy_lineage_key
            or (
                str(row.get("question_id", "") or "") == question_id
                and str(row.get("repair_scope", "") or "")
                == "upstream_theory"
            )
        ]
    consumed_review_execution_ids = list(
        dict.fromkeys(
            str(value)
            for _, row in budget_rows
            for value in row.get("consumed_review_execution_ids", []) or []
            if str(value).strip()
        )
    )
    recorded_revision_counts = [
        max(0, int(row.get("revisions_used", 0) or 0))
        for _, row in budget_rows
    ]
    if canonical_row:
        revisions_used = max(recorded_revision_counts or [0])
    elif consumed_review_execution_ids:
        revisions_used = max(
            len(consumed_review_execution_ids),
            max(recorded_revision_counts or [0]),
        )
    else:
        revisions_used = sum(recorded_revision_counts)
    source_subsystems = list(
        dict.fromkeys(
            str(value)
            for _, row in budget_rows
            for value in (
                list(row.get("source_subsystems", []) or [])
                + [row.get("source_subsystem", "")]
            )
            if str(value).strip()
        )
    )
    prior = dict(budget_rows[-1][1]) if budget_rows else {}
    prior.update(
        {
            "lineage_key": lineage_key,
            "question_id": question_id,
            "repair_scope": "upstream_theory",
            "budget_scope": "question_global",
            "revisions_used": revisions_used,
            "consumed_review_execution_ids": consumed_review_execution_ids,
            "source_subsystems": source_subsystems,
        }
    )
    revision_limit = max(0, int(max_revisions or 0))
    return {
        "active": active,
        "lineage_key": lineage_key,
        "ledger": ledger,
        "legacy_lineage_keys": [
            key for key, _ in budget_rows if key != lineage_key
        ],
        "row": prior,
        "replan": replan,
        "revisions_used": revisions_used,
        "max_revisions": revision_limit,
        "budget_exhausted": bool(
            active and revision_limit > 0 and revisions_used >= revision_limit
        ),
    }


def consume_generated_code_semantic_review_upstream_theory_replan(
    *,
    architect_context: Mapping[str, Any],
    question_id: str,
    revised_theory_packet_id: str,
    revised_theory_packet_hash: str,
    max_revisions: int,
) -> dict[str, Any]:
    """Retire feedback once a fresh theory packet has consumed it."""

    context = dict(architect_context)
    state = generated_code_semantic_review_upstream_theory_revision_state(
        architect_context=context,
        question_id=question_id,
        max_revisions=max_revisions,
    )
    if not state["active"]:
        return context
    replan = dict(state["replan"])
    pending_ids = _mapping(replan.get("pending_artifact_ids"))
    prior_theory_packet_id = str(
        pending_ids.get("theory_packet_id", "") or ""
    )
    revised_theory_packet_id = str(revised_theory_packet_id or "")
    revised_theory_packet_hash = str(revised_theory_packet_hash or "")
    if not (
        prior_theory_packet_id
        and revised_theory_packet_id
        and revised_theory_packet_hash
        and revised_theory_packet_id != prior_theory_packet_id
    ):
        return context

    review_execution_id = str(replan.get("review_execution_id", "") or "")
    lineage_key = str(state["lineage_key"])
    ledger = dict(state["ledger"])
    prior_row = dict(state["row"])
    consumed_review_execution_ids = [
        str(value)
        for value in prior_row.get("consumed_review_execution_ids", []) or []
        if str(value).strip()
    ]
    revisions_used = int(state["revisions_used"])
    if review_execution_id not in consumed_review_execution_ids:
        consumed_review_execution_ids.append(review_execution_id)
        revisions_used += 1
    source_subsystems = list(
        dict.fromkeys(
            [
                str(value)
                for value in prior_row.get("source_subsystems", []) or []
                if str(value).strip()
            ]
            + [str(replan.get("source_subsystem", "") or "")]
        )
    )
    for legacy_lineage_key in state.get("legacy_lineage_keys", []) or []:
        ledger.pop(str(legacy_lineage_key), None)
    ledger[lineage_key] = {
        "lineage_key": lineage_key,
        "question_id": question_id,
        "source_subsystem": str(replan.get("source_subsystem", "") or ""),
        "source_subsystems": source_subsystems,
        "repair_scope": "upstream_theory",
        "budget_scope": "question_global",
        "revisions_used": revisions_used,
        "max_revisions": int(state["max_revisions"]),
        "consumed_review_execution_ids": consumed_review_execution_ids,
        "last_prior_theory_packet_id": prior_theory_packet_id,
        "last_revised_theory_packet_id": revised_theory_packet_id,
        "last_revised_theory_packet_hash": revised_theory_packet_hash,
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_"
            "BUDGET_NOT_PROOF_EVIDENCE"
        ),
    }
    context[
        GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_LEDGER_KEY
    ] = ledger

    resolution = {
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewReplanResolution",
        "source_subsystem": str(replan.get("source_subsystem", "") or ""),
        "rejected_source_manifest_id": str(
            replan.get("source_manifest_id", "") or ""
        ),
        "rejected_review_packet_id": str(
            replan.get("review_packet_id", "") or ""
        ),
        "rejected_review_execution_id": review_execution_id,
        "prior_theory_packet_id": prior_theory_packet_id,
        "revised_theory_packet_id": revised_theory_packet_id,
        "revised_theory_packet_hash": revised_theory_packet_hash,
        "upstream_theory_revisions_used": revisions_used,
        "max_upstream_theory_revisions": int(state["max_revisions"]),
        "resolution_status": "CONSUMED_BY_FRESH_THEORY_REVISION",
        "requires_fresh_metric_protocol_review": True,
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_REPLAN_RESOLUTION_NOT_PROOF_EVIDENCE"
        ),
    }
    resolution["resolution_id"] = (
        "generated_code_semantic_review_replan_resolution:"
        + stable_hash(resolution)[:20]
    )
    context["runtime_generated_code_semantic_review_replan_resolution"] = resolution
    context.pop("runtime_generated_code_semantic_review_replan", None)

    feedback = context.get("environment_feedback", {})
    if isinstance(feedback, Mapping) and str(
        feedback.get("semantic_review_execution_id", "") or ""
    ) == review_execution_id:
        context.pop("environment_feedback", None)
    feedback_loop = context.get("runtime_feedback_loop", {})
    if isinstance(feedback_loop, Mapping) and str(
        feedback_loop.get("semantic_review_execution_id", "") or ""
    ) == review_execution_id:
        context.pop("runtime_feedback_loop", None)
    return context


def generated_code_semantic_review_upstream_theory_budget_exhausted_result(
    *,
    task: AgentTask,
    question_id: str,
    budget_state: Mapping[str, Any],
) -> AgentStepResult:
    """Stop before another TheoryDeveloper call when the review lane is spent."""

    replan = _mapping(budget_state.get("replan"))
    artifact_id = (
        "generated_code_semantic_review_upstream_theory_revision_exhausted:"
        + stable_hash(
            [question_id, budget_state.get("lineage_key", "")]
        )[:20]
    )
    boundary = (
        "The independent generated-code review exhausted its global upstream "
        "theory-revision budget. The rejected generated artifact remains "
        "unaccepted; stopping this feedback lineage is not research or proof evidence."
    )
    artifact = {
        "schema_version": 1,
        "artifact_kind": (
            "RuntimeGeneratedCodeSemanticReviewUpstreamTheoryRevisionExhaustion"
        ),
        "exhaustion_id": artifact_id,
        "question_id": question_id,
        "source_subsystem": str(replan.get("source_subsystem", "") or ""),
        "source_manifest_id": str(replan.get("source_manifest_id", "") or ""),
        "review_packet_id": str(replan.get("review_packet_id", "") or ""),
        "review_execution_id": str(
            replan.get("review_execution_id", "") or ""
        ),
        "upstream_theory_revisions_used": int(
            budget_state.get("revisions_used", 0) or 0
        ),
        "max_upstream_theory_revisions": int(
            budget_state.get("max_revisions", 0) or 0
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_"
            "EXHAUSTED_NOT_PROOF_EVIDENCE"
        ),
        "boundary": boundary,
    }
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, artifact_id])[:20],
        task_id=task.task_id,
        artifact_id=artifact_id,
        evidence_type=(
            "generated_code_semantic_review_upstream_theory_revision_exhaustion"
        ),
        status="UPSTREAM_THEORY_REVISION_LINEAGE_EXHAUSTED_BLOCKED",
        boundary=boundary,
        payload={
            "source_manifest_id": artifact["source_manifest_id"],
            "upstream_theory_revisions_used": artifact[
                "upstream_theory_revisions_used"
            ],
            "max_upstream_theory_revisions": artifact[
                "max_upstream_theory_revisions"
            ],
            "proof_evidence_status": artifact["proof_evidence_status"],
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "Runtime stopped a repeated upstream semantic-review theory lineage "
            "before another TheoryDeveloper provider call."
        ),
        produced_artifacts={artifact_id: artifact},
        observations=(
            EnvironmentObservation(
                observation_type=(
                    "generated_code_semantic_review_upstream_theory_revision_"
                    "exhaustion"
                ),
                summary="upstream semantic-review theory revision budget exhausted",
                payload={
                    "exhaustion_id": artifact_id,
                    "upstream_theory_revisions_used": artifact[
                        "upstream_theory_revisions_used"
                    ],
                    "max_upstream_theory_revisions": artifact[
                        "max_upstream_theory_revisions"
                    ],
                },
            ),
        ),
        evidence_entries=(evidence,),
        failure_classification=(
            "generated_code_semantic_review_upstream_theory_revision_budget_"
            "exhausted"
        ),
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
    finding_seen_in_source_lineage = bool(prior)
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
        "post_replan_local_repair_count": int(
            prior.get("post_replan_local_repair_count", 0) or 0
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
    source_post_replan_local_repair_count = sum(
        max(
            0,
            int(candidate.get("post_replan_local_repair_count", 0) or 0),
        )
        for candidate in source_lineage_rows
    )
    row["source_local_repair_count"] = source_local_repair_count
    row["source_architect_replan_count"] = source_architect_replan_count
    row["source_post_replan_local_repair_count"] = (
        source_post_replan_local_repair_count
    )
    row["source_rejection_count"] = sum(
        max(0, int(candidate.get("rejection_count", 0) or 0))
        for candidate in source_lineage_rows
    )
    post_replan_local_repair_available = bool(
        row["repair_scope"] == "source_code"
        and row["max_local_revisions"] > 0
        and source_architect_replan_count == 1
        and source_post_replan_local_repair_count == 0
        and source_local_repair_count < row["max_local_revisions"] + 1
        and not finding_seen_in_source_lineage
    )
    row["finding_seen_in_source_lineage"] = finding_seen_in_source_lineage
    row["post_replan_local_repair_available"] = (
        post_replan_local_repair_available
    )
    if len(ledger) > 32:
        ledger = dict(list(ledger.items())[-32:])
    return {
        "lineage_key": lineage_key,
        "source_lineage_key": source_lineage_key,
        "row": row,
        "ledger": ledger,
        "local_repair_available": bool(
            (
                row["repair_scope"] == "source_code"
                and source_local_repair_count < row["max_local_revisions"]
                and source_architect_replan_count == 0
            )
            or post_replan_local_repair_available
        ),
        "architect_replan_available": source_architect_replan_count == 0,
        "lineage_budget_exhausted": bool(
            source_architect_replan_count > 0
            and not post_replan_local_repair_available
        ),
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
        if row.get("post_replan_local_repair_available") is True:
            row["post_replan_local_repair_count"] = int(
                row.get("post_replan_local_repair_count", 0) or 0
            ) + 1
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
        "repair_scopes": [
            str(value)
            for value in escalation_feedback.get("repair_scopes", []) or []
            if str(value)
        ],
        "repair_plan": [
            dict(row)
            for row in escalation_feedback.get("repair_plan", []) or []
            if isinstance(row, Mapping)
        ],
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
