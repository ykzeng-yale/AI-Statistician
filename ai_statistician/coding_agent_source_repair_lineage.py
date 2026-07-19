from __future__ import annotations

from typing import Any, Mapping, Sequence

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    ToolCallRecord,
)
from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion


CODING_AGENT_SOURCE_OWNED_FAILURE_CLASSIFICATIONS = frozenset(
    {
        "generated_algorithm_sandbox_execution_failed",
        "generated_algorithm_sandbox_required_not_executed",
        "generated_algorithm_sandbox_repair_required",
        "algorithm_sandbox_no_executable_prototype",
    }
)


def coding_agent_source_repair_lineage_state(
    *,
    question_id: str,
    source_subsystem: str,
    theory_packet_id: str,
    implementation_gaps: Sequence[Mapping[str, Any]],
    architect_context: Mapping[str, Any],
    yield_after_attempts: int,
) -> dict[str, Any]:
    lineage_key = stable_hash(
        {
            "question_id": question_id,
            "source_subsystem": source_subsystem,
            "theory_packet_id": theory_packet_id,
            "implementation_gaps": [dict(row) for row in implementation_gaps],
        }
    )
    ledger = architect_context.get(
        "runtime_coding_agent_source_repair_lineage_ledger", {}
    )
    ledger = dict(ledger) if isinstance(ledger, Mapping) else {}
    prior = ledger.get(lineage_key, {})
    prior = dict(prior) if isinstance(prior, Mapping) else {}
    return {
        "lineage_key": lineage_key,
        "ledger": ledger,
        "dispatches_used": int(prior.get("dispatches_used", 0) or 0),
        "max_dispatches": max(1, int(yield_after_attempts or 0)),
    }


def coding_agent_source_repair_lineage_exhausted_result(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    source_manifest_id: str,
    lineage_state: Mapping[str, Any],
    produced_artifacts: Mapping[str, Any],
    observations: Sequence[EnvironmentObservation],
    tool_calls: Sequence[ToolCallRecord],
    evidence_entries: Sequence[EvidenceLedgerEntry | None],
) -> AgentStepResult:
    exhaustion_id = "coding_agent_source_repair_exhausted:" + stable_hash(
        [question.id, lineage_state.get("lineage_key", "")]
    )[:20]
    boundary = (
        "The source coding agent exhausted its global theory-bound repair budget. "
        "Failed source remains rejected; accepted theory and metric authority are "
        "not reset, and this blocker is not research or proof evidence."
    )
    artifact = {
        "schema_version": 1,
        "artifact_kind": "RuntimeCodingAgentSourceRepairLineageExhaustion",
        "exhaustion_id": exhaustion_id,
        "question_id": question.id,
        "source_subsystem": task.owner_subsystem,
        "source_manifest_id": source_manifest_id,
        "source_repair_lineage_key": str(
            lineage_state.get("lineage_key", "") or ""
        ),
        "dispatches_used": int(lineage_state.get("dispatches_used", 0) or 0),
        "max_dispatches": int(lineage_state.get("max_dispatches", 0) or 0),
        "proof_evidence_status": (
            "CODING_AGENT_SOURCE_REPAIR_EXHAUSTED_NOT_PROOF_EVIDENCE"
        ),
        "boundary": boundary,
    }
    exhaustion_evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, exhaustion_id])[:20],
        task_id=task.task_id,
        artifact_id=exhaustion_id,
        evidence_type="coding_agent_source_repair_lineage_exhaustion",
        status="SOURCE_REPAIR_LINEAGE_EXHAUSTED_BLOCKED",
        boundary=boundary,
        payload={
            "source_manifest_id": source_manifest_id,
            "dispatches_used": artifact["dispatches_used"],
            "max_dispatches": artifact["max_dispatches"],
            "proof_evidence_status": artifact["proof_evidence_status"],
        },
    )
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "Runtime stopped a repeated source-owned coding failure at its global "
            "lineage budget without replanning unrelated theory."
        ),
        produced_artifacts={**dict(produced_artifacts), exhaustion_id: artifact},
        observations=(
            *observations,
            EnvironmentObservation(
                observation_type="coding_agent_source_repair_lineage_exhaustion",
                summary=f"source repair lineage exhausted for {task.owner_subsystem}",
                payload={
                    "exhaustion_id": exhaustion_id,
                    "dispatches_used": artifact["dispatches_used"],
                    "max_dispatches": artifact["max_dispatches"],
                },
            ),
        ),
        tool_calls=tuple(tool_calls),
        evidence_entries=tuple(
            row for row in (*evidence_entries, exhaustion_evidence) if row is not None
        ),
        failure_classification=(
            "coding_agent_source_repair_lineage_budget_exhausted"
        ),
    )
