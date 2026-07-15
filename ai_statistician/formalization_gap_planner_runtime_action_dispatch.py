from __future__ import annotations

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


ACTION_WORK_ORDER_ARTIFACT_KIND = (
    "RuntimeFormalizationGapPlannerActionWorkOrder"
)
ACTION_WORK_ORDER_STATUS = (
    "FORMALIZATION_GAP_PLANNER_ACTION_WORK_ORDER_NOT_PROOF_EVIDENCE"
)


def validated_action_rows(
    live_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if live_manifest.get("feedback_loop_recorded") is False:
        return []
    candidates: list[Mapping[str, Any]] = []
    for outer_row in live_manifest.get("rows", []) or []:
        if not isinstance(outer_row, Mapping):
            continue
        candidates.append(outer_row)
        for assembly_row in outer_row.get("staged_followup_assembly_rows", []) or []:
            if not isinstance(assembly_row, Mapping):
                continue
            assembled_row = assembly_row.get(
                "assembled_llm_route_planner_row",
                {},
            )
            if isinstance(assembled_row, Mapping):
                candidates.append(assembled_row)

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.get("response_contract_ok") is not True:
            continue
        acceptance_status = str(
            candidate.get("acceptance_status", "") or ""
        )
        route_adoption_status = str(
            candidate.get("route_adoption_status", "") or ""
        )
        if (
            candidate.get("ok") is False
            or acceptance_status.startswith("REJECTED")
            or route_adoption_status == "REJECTED_LLM_ROUTE_PLAN"
        ):
            continue
        formal_attempt_queue = _mapping_rows(
            candidate.get("formal_attempt_queue", [])
        )
        planner_next_actions = _mapping_rows(
            candidate.get("planner_next_actions", [])
        )
        search_requests = _mapping_rows(candidate.get("search_requests", []))
        if not (formal_attempt_queue or planner_next_actions or search_requests):
            continue
        row = {
            "response_row_id": str(
                candidate.get("llm_route_planner_row_id", "")
                or candidate.get("request_id", "")
                or ""
            ),
            "request_id": str(candidate.get("request_id", "") or ""),
            "route_id": str(candidate.get("route_id", "") or ""),
            "route_adoption_status": route_adoption_status,
            "acceptance_status": acceptance_status,
            "formal_attempt_queue": formal_attempt_queue,
            "planner_next_actions": planner_next_actions,
            "search_requests": search_requests,
            "source_refs": [
                str(value)
                for value in candidate.get("source_refs", []) or []
                if str(value).strip()
            ],
            "semantic_alignment_risks": _preserved_rows(
                candidate.get("semantic_alignment_risks", [])
            ),
            "uncertainty_flags": _preserved_rows(
                candidate.get("uncertainty_flags", [])
            ),
            "response_fingerprint": stable_hash(candidate),
        }
        fingerprint = stable_hash(row)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        rows.append(row)
    return rows


def dispatch_validated_action_work_order(
    *,
    task: AgentTask,
    blackboard: BlackboardState,
    question_payload: Mapping[str, Any],
    live_manifest: Mapping[str, Any],
    schema_version: int,
    proof_evidence_boundary: str,
) -> AgentStepResult | None:
    action_rows = validated_action_rows(live_manifest)
    if not action_rows:
        return None

    question_id = str(question_payload.get("id", "") or "")
    source_question = _mapping(live_manifest.get("question", {}))
    source_question_id = str(source_question.get("id", "") or "")
    if source_question_id != question_id:
        return AgentStepResult(
            status="BLOCKED",
            rationale=(
                "FormalizationGapPlanner rejected a contract-valid response from "
                "a different question lineage before dispatch."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "formalization_gap_planner_action_cross_task_rejected"
                    ),
                    summary=(
                        f"current_question_id={question_id} "
                        f"source_question_id={source_question_id}"
                    ),
                    payload={
                        "current_question_id": question_id,
                        "source_question_id": source_question_id,
                        "proof_evidence_status": (
                            "FORMALIZATION_GAP_PLANNER_ACTION_CROSS_TASK_"
                            "REJECTED_NOT_PROOF_EVIDENCE"
                        ),
                    },
                ),
            ),
            failure_classification=(
                "formalization_gap_planner_action_cross_task_rejected"
            ),
        )
    formal_attempt_queue = _unique_action_rows(
        action_rows,
        "formal_attempt_queue",
    )
    planner_next_actions = _unique_action_rows(
        action_rows,
        "planner_next_actions",
    )
    search_requests = _unique_action_rows(action_rows, "search_requests")
    upstream_artifact_ids = {
        "theory_packet_id": _artifact_id(task, "theory_packet_id"),
        "simulation_manifest_id": _artifact_id(
            task,
            "simulation_manifest_id",
        ),
        "algorithm_sandbox_manifest_id": _artifact_id(
            task,
            "algorithm_sandbox_manifest_id",
        ),
    }
    upstream_lineage_errors = [
        f"planner action {input_name} missing"
        for input_name, artifact_id in upstream_artifact_ids.items()
        if not artifact_id
    ]
    upstream_lineage_errors.extend(
        f"planner action {input_name} artifact missing from blackboard"
        for input_name, artifact_id in upstream_artifact_ids.items()
        if artifact_id
        and not isinstance(blackboard.artifacts.get(artifact_id), Mapping)
    )
    if upstream_lineage_errors:
        return AgentStepResult(
            status="BLOCKED",
            rationale=(
                "FormalizationGapPlanner refused to dispatch validated actions "
                "without the exact upstream theory, simulation, and algorithm "
                "artifact lineage."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "formalization_gap_planner_action_upstream_lineage_blocked"
                    ),
                    summary="; ".join(upstream_lineage_errors),
                    payload={
                        "lineage_errors": upstream_lineage_errors,
                        "proof_evidence_status": (
                            "FORMALIZATION_GAP_PLANNER_ACTION_UPSTREAM_LINEAGE_"
                            "BLOCKED_NOT_PROOF_EVIDENCE"
                        ),
                    },
                ),
            ),
            failure_classification=(
                "formalization_gap_planner_action_upstream_lineage_missing"
            ),
        )
    upstream_artifact_lineage = {
        input_name: {
            "artifact_id": artifact_id,
            "artifact_fingerprint": stable_hash(
                blackboard.artifacts[artifact_id]
            ),
        }
        for input_name, artifact_id in upstream_artifact_ids.items()
    }
    source_manifest_id = str(live_manifest.get("manifest_id", "") or "")
    source_manifest_fingerprint = stable_hash(live_manifest)
    work_order_payload = {
        "question_id": question_id,
        "source_live_route_planner_manifest_id": source_manifest_id,
        "source_live_route_planner_manifest_fingerprint": (
            source_manifest_fingerprint
        ),
        "response_row_fingerprints": [
            str(row.get("response_fingerprint", "") or "")
            for row in action_rows
        ],
        **upstream_artifact_ids,
        "upstream_artifact_lineage": upstream_artifact_lineage,
        "formal_attempt_queue": formal_attempt_queue,
        "planner_next_actions": planner_next_actions,
        "search_requests": search_requests,
    }
    work_order_id = (
        "runtime_formalization_gap_planner_action_work_order:"
        + stable_hash(work_order_payload)[:20]
    )
    existing_work_order = blackboard.artifacts.get(work_order_id)
    if isinstance(existing_work_order, Mapping):
        return AgentStepResult(
            status="BLOCKED",
            rationale=(
                "FormalizationGapPlanner refused to redispatch an unchanged "
                "validated action work order after its prior ProofEngineer path."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "formalization_gap_planner_action_redispatch_blocked"
                    ),
                    summary=f"work_order_id={work_order_id}",
                    payload={
                        "work_order_id": work_order_id,
                        "source_live_route_planner_manifest_id": source_manifest_id,
                        "proof_evidence_status": (
                            "FORMALIZATION_GAP_PLANNER_ACTION_REDISPATCH_"
                            "BLOCKED_NOT_PROOF_EVIDENCE"
                        ),
                    },
                ),
            ),
            failure_classification=(
                "formalization_gap_planner_action_work_order_already_dispatched"
            ),
        )

    work_order = {
        "schema_version": schema_version,
        "artifact_kind": ACTION_WORK_ORDER_ARTIFACT_KIND,
        "work_order_id": work_order_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_task_id": task.task_id,
        "question": dict(question_payload),
        **work_order_payload,
        "validated_response_rows": action_rows,
        "proof_evidence_status": ACTION_WORK_ORDER_STATUS,
        "proof_evidence_boundary": proof_evidence_boundary,
        "boundary": (
            "This immutable work order preserves contract-valid planner actions. "
            "It is orchestration input; only subsequent local Lean/kernel checks "
            "can produce proof evidence."
        ),
    }
    work_order_hash = stable_hash(work_order)
    environment_feedback = _mapping(task.inputs.get("environment_feedback", {}))
    environment_feedback.update(
        {
            "feedback_type": "formalization_gap_planner_action_work_order",
            "failure_classification": (
                "formalization_gap_planner_action_execution_required"
            ),
            "repair_owner_agent": "ProofEngineer",
            "formalization_gap_planner_action_work_order": work_order,
            "formalization_gap_planner_action_work_order_id": work_order_id,
            "formalization_gap_planner_action_work_order_hash": work_order_hash,
            "required_repair": (
                "Execute the validated planner queue with formal-source retrieval, "
                "LLM candidate generation, and local Lean/LSP feedback while "
                "preserving the exact theorem lineage."
            ),
            "proof_evidence_status": ACTION_WORK_ORDER_STATUS,
            "proof_evidence_boundary": proof_evidence_boundary,
        }
    )
    architect_context = _mapping(task.inputs.get("architect_context", {}))
    architect_context["environment_feedback"] = environment_feedback

    next_task = AgentTask(
        task_id=(
            f"proofengineer-planner-actions:{question_id}:"
            f"{stable_hash([work_order_id, work_order_hash])[:10]}"
        ),
        owner_subsystem="ProofEngineer",
        objective=(
            "Execute the immutable, contract-valid FormalizationGapPlanner action "
            "work order with RAG, LLM candidate generation, and Lean feedback."
        ),
        inputs={
            "question": dict(question_payload),
            "architect_context": architect_context,
            "environment_feedback": environment_feedback,
            **upstream_artifact_ids,
            "formalization_gap_planner_action_work_order_id": work_order_id,
            "formalization_gap_planner_action_work_order_hash": work_order_hash,
        },
        allowed_tools=(
            "model_backend",
            "formal_source_retriever",
            "rag_memory",
            "proof_search",
            "local_lean",
            "lean_lsp_mcp",
            "evidence_ledger",
        ),
        expected_artifacts=(
            "formalizer_proposal",
            "formalization_manifest",
            "proof_state_feedback_manifest",
        ),
        acceptance_gate=(
            "planner actions yield a source-bound candidate plus local Lean/LSP "
            "feedback, or a typed dependency blocker; planner output alone is not proof"
        ),
        stop_condition=(
            "validated planner work is checked by the configured proof environment "
            "or a lineage-bound blocker is recorded"
        ),
    )
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, work_order_id])[:20],
        task_id=task.task_id,
        artifact_id=work_order_id,
        evidence_type="formalization_gap_planner_action_dispatch",
        status="VALIDATED_ACTION_WORK_ORDER_DISPATCHED_NOT_PROOF_EVIDENCE",
        boundary=proof_evidence_boundary,
        payload={
            "source_live_route_planner_manifest_id": source_manifest_id,
            "n_formal_attempts": len(formal_attempt_queue),
            "n_planner_next_actions": len(planner_next_actions),
            "n_search_requests": len(search_requests),
            "proof_evidence_status": ACTION_WORK_ORDER_STATUS,
        },
    )
    return AgentStepResult(
        status="REVISE",
        rationale=(
            "FormalizationGapPlanner compiled contract-valid action rows into an "
            "immutable ProofEngineer work order instead of returning to theory or "
            "treating planner text as proof."
        ),
        produced_artifacts={work_order_id: work_order},
        observations=(
            EnvironmentObservation(
                observation_type="formalization_gap_planner_action_dispatch",
                summary=(
                    f"formal_attempts={len(formal_attempt_queue)} "
                    f"planner_actions={len(planner_next_actions)} "
                    f"search_requests={len(search_requests)}"
                ),
                payload=evidence.payload,
            ),
        ),
        evidence_entries=(evidence,),
        next_task=next_task,
        failure_classification=(
            "formalization_gap_planner_action_execution_required"
        ),
    )


def validate_action_work_order_binding(
    *,
    task: AgentTask,
    blackboard: BlackboardState,
    question_id: str,
) -> tuple[dict[str, Any], list[str]]:
    feedback = _mapping(task.inputs.get("environment_feedback", {}))
    work_order_id = str(
        task.inputs.get("formalization_gap_planner_action_work_order_id", "")
        or ""
    )
    work_order_hash = str(
        task.inputs.get("formalization_gap_planner_action_work_order_hash", "")
        or ""
    )
    binding_requested = bool(
        work_order_id
        or work_order_hash
        or feedback.get("formalization_gap_planner_action_work_order_id")
        or feedback.get("formalization_gap_planner_action_work_order_hash")
        or feedback.get("formalization_gap_planner_action_work_order")
    )
    if not binding_requested:
        return {}, []

    errors: list[str] = []
    raw_work_order = blackboard.artifacts.get(work_order_id)
    work_order = _mapping(raw_work_order)
    if not work_order_id:
        errors.append("planner action work_order_id missing")
    if not work_order:
        errors.append("planner action work order missing from blackboard")
        return {}, errors
    if work_order.get("artifact_kind") != ACTION_WORK_ORDER_ARTIFACT_KIND:
        errors.append("planner action work-order artifact_kind mismatch")
    if str(work_order.get("work_order_id", "") or "") != work_order_id:
        errors.append("planner action work-order identity mismatch")
    if not work_order_hash or stable_hash(work_order) != work_order_hash:
        errors.append("planner action work-order hash mismatch")
    if str(work_order.get("question_id", "") or "") != question_id:
        errors.append("planner action work-order question_id mismatch")
    upstream_artifact_lineage = _mapping(
        work_order.get("upstream_artifact_lineage", {})
    )
    for input_name in (
        "theory_packet_id",
        "simulation_manifest_id",
        "algorithm_sandbox_manifest_id",
    ):
        expected_artifact_id = str(work_order.get(input_name, "") or "")
        task_artifact_id = str(task.inputs.get(input_name, "") or "")
        if not expected_artifact_id:
            errors.append(f"planner action work-order {input_name} missing")
            continue
        if task_artifact_id != expected_artifact_id:
            errors.append(f"planner action task {input_name} mismatch")
        artifact = blackboard.artifacts.get(expected_artifact_id)
        if not isinstance(artifact, Mapping):
            errors.append(
                f"planner action {input_name} artifact missing from blackboard"
            )
            continue
        lineage_row = _mapping(upstream_artifact_lineage.get(input_name, {}))
        if str(lineage_row.get("artifact_id", "") or "") != expected_artifact_id:
            errors.append(f"planner action {input_name} lineage identity mismatch")
        if str(lineage_row.get("artifact_fingerprint", "") or "") != stable_hash(
            artifact
        ):
            errors.append(
                f"planner action {input_name} artifact fingerprint mismatch"
            )

    if str(
        feedback.get("formalization_gap_planner_action_work_order_id", "") or ""
    ) != work_order_id:
        errors.append("planner action feedback work_order_id mismatch")
    if str(
        feedback.get("formalization_gap_planner_action_work_order_hash", "") or ""
    ) != work_order_hash:
        errors.append("planner action feedback work_order_hash mismatch")
    feedback_work_order = _mapping(
        feedback.get("formalization_gap_planner_action_work_order", {})
    )
    if stable_hash(feedback_work_order) != stable_hash(work_order):
        errors.append("planner action feedback work-order payload mismatch")

    source_manifest_id = str(
        work_order.get("source_live_route_planner_manifest_id", "") or ""
    )
    source_manifest = _mapping(blackboard.artifacts.get(source_manifest_id))
    if not source_manifest:
        errors.append("planner action source live manifest missing from blackboard")
    else:
        source_question = _mapping(source_manifest.get("question", {}))
        source_question_id = str(source_question.get("id", "") or "")
        if source_question_id != question_id:
            errors.append("planner action source live manifest question_id mismatch")
        expected_source_fingerprint = str(
            work_order.get(
                "source_live_route_planner_manifest_fingerprint",
                "",
            )
            or ""
        )
        if stable_hash(source_manifest) != expected_source_fingerprint:
            errors.append("planner action source live manifest fingerprint mismatch")
        expected_action_rows = validated_action_rows(source_manifest)
        if stable_hash(expected_action_rows) != stable_hash(
            work_order.get("validated_response_rows", [])
        ):
            errors.append("planner action validated response rows changed")
    return work_order, errors


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in value or [] if isinstance(row, Mapping)]


def _preserved_rows(value: Any) -> list[Any]:
    return [dict(row) if isinstance(row, Mapping) else str(row) for row in value or []]


def _unique_action_rows(
    action_rows: list[dict[str, Any]],
    field: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for response_row in action_rows:
        for raw_row in response_row.get(field, []) or []:
            if not isinstance(raw_row, Mapping):
                continue
            row = dict(raw_row)
            fingerprint = stable_hash(row)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            rows.append(row)
    return rows


def _artifact_id(
    task: AgentTask,
    input_name: str,
) -> str:
    return str(task.inputs.get(input_name, "") or "")
