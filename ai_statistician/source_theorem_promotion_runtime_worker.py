from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
)
from .fingerprint import stable_hash
from .exact_source_theorem_proof_body_runtime_worker import (
    EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM,
)
from .research_architect import KERNEL_PROOF_BOUNDARY


RUNTIME_SCHEMA_VERSION = 1
SOURCE_THEOREM_PROMOTION_SUBSYSTEM = "SourceTheoremPromotionProofEngineer"
SOURCE_THEOREM_PROMOTION_RUNTIME_WORK_ORDER_KIND = (
    "RuntimeSourceTheoremPromotionProofEngineerWorkOrder"
)
SOURCE_THEOREM_PROMOTION_RUNTIME_EXECUTION_KIND = (
    "RuntimeSourceTheoremPromotionProofEngineerExecutionManifest"
)


def _bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def bound_generation_request(
    *,
    task: AgentTask,
    blackboard: BlackboardState,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Load and verify the immutable promotion request before model execution."""

    feedback = (
        task.inputs.get("environment_feedback", {})
        if isinstance(task.inputs.get("environment_feedback", {}), Mapping)
        else {}
    )
    copied_request = (
        dict(feedback.get("source_theorem_promotion_generation_request", {}) or {})
        if isinstance(
            feedback.get("source_theorem_promotion_generation_request", {}),
            Mapping,
        )
        else {}
    )
    request_id = str(
        task.inputs.get("source_theorem_promotion_generation_request_id", "")
        or feedback.get("source_theorem_promotion_generation_request_id", "")
        or copied_request.get("request_id", "")
        or ""
    )
    expected_request_hash = str(
        task.inputs.get("source_theorem_promotion_generation_request_hash", "")
        or feedback.get("source_theorem_promotion_generation_request_hash", "")
        or ""
    )
    execution_id = str(
        task.inputs.get("source_theorem_promotion_execution_id", "")
        or feedback.get("source_theorem_promotion_execution_id", "")
        or ""
    )
    if not copied_request and not request_id and not execution_id:
        return {}, ()

    errors: list[str] = []
    if task.owner_subsystem != "ProofEngineer":
        errors.append("promotion generation request is not ProofEngineer-owned")
    if not request_id:
        errors.append("promotion generation request id missing")
    if not expected_request_hash:
        errors.append("promotion generation request hash missing")
    if not execution_id:
        errors.append("promotion execution id missing")
    raw_request = blackboard.artifacts.get(request_id, {})
    request = dict(raw_request) if isinstance(raw_request, Mapping) else {}
    if not request:
        errors.append("promotion generation request missing from blackboard")
    request_copy_contract_keys = (
        "artifact_kind",
        "request_id",
        "question_id",
        "source_promotion_work_order_id",
        "source_formalization_manifest_id",
        "target_rows",
        "target_ids",
        "target_declarations",
        "generation_contract",
        "next_compiler_subsystem",
        "proof_evidence_status",
        "proof_evidence_boundary",
    )
    request_copy_mismatch_keys = [
        key
        for key in request_copy_contract_keys
        if copied_request.get(key) != request.get(key)
    ]
    if copied_request and request_copy_mismatch_keys:
        errors.append(
            "promotion generation request feedback contract mismatch: "
            + ", ".join(request_copy_mismatch_keys)
        )
    if str(request.get("artifact_kind", "") or "") != (
        "RuntimeExactSourceCandidateGenerationRequest"
    ):
        errors.append("promotion generation request artifact_kind mismatch")
    if str(request.get("request_id", "") or "") != request_id:
        errors.append("promotion generation request identity mismatch")
    if not expected_request_hash or stable_hash(request) != expected_request_hash:
        errors.append("promotion generation request immutable hash mismatch")

    raw_execution = blackboard.artifacts.get(execution_id, {})
    execution = dict(raw_execution) if isinstance(raw_execution, Mapping) else {}
    if not execution:
        errors.append("promotion execution manifest missing from blackboard")
    if str(execution.get("artifact_kind", "") or "") != (
        SOURCE_THEOREM_PROMOTION_RUNTIME_EXECUTION_KIND
    ):
        errors.append("promotion execution artifact_kind mismatch")
    if str(execution.get("manifest_id", "") or "") != execution_id:
        errors.append("promotion execution identity mismatch")
    if str(execution.get("generation_request_id", "") or "") != request_id:
        errors.append("promotion execution request identity mismatch")
    if str(execution.get("generation_request_hash", "") or "") != (
        expected_request_hash
    ):
        errors.append("promotion execution request hash mismatch")

    source_work_order_id = str(
        request.get("source_promotion_work_order_id", "") or ""
    )
    raw_work_order = blackboard.artifacts.get(source_work_order_id, {})
    work_order = dict(raw_work_order) if isinstance(raw_work_order, Mapping) else {}
    if not source_work_order_id or not work_order:
        errors.append("promotion source work order missing from blackboard")
    if str(work_order.get("artifact_kind", "") or "") != (
        SOURCE_THEOREM_PROMOTION_RUNTIME_WORK_ORDER_KIND
    ):
        errors.append("promotion source work-order artifact_kind mismatch")
    if str(execution.get("work_order_id", "") or "") != source_work_order_id:
        errors.append("promotion execution source work-order identity mismatch")
    if work_order and stable_hash(work_order) != str(
        execution.get("work_order_hash", "") or ""
    ):
        errors.append("promotion source work-order immutable hash mismatch")

    question_payload = task.inputs.get("question", {})
    question_id = str(
        question_payload.get("id", "")
        if isinstance(question_payload, Mapping)
        else ""
    )
    if str(request.get("question_id", "") or "") != question_id:
        errors.append("promotion generation request question mismatch")
    if str(request.get("next_compiler_subsystem", "") or "") != (
        EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM
    ):
        errors.append("promotion generation request compiler route mismatch")
    target_rows = [
        dict(row)
        for row in request.get("target_rows", []) or []
        if isinstance(row, Mapping)
    ]
    if not target_rows:
        errors.append("promotion generation request has no target rows")
    if work_order and target_rows != list(work_order.get("work_order_rows", []) or []):
        errors.append("promotion generation request rows differ from work order")
    for row in target_rows:
        if not str(row.get("source_formal_target_id", "") or ""):
            errors.append("promotion request source formal target id missing")
        if not str(row.get("target_lean_declaration", "") or ""):
            errors.append("promotion request target declaration missing")
        if str(row.get("target_lean_declaration_source", "") or "") != (
            "formalizer_structured_source_theorem_target_provenance"
        ):
            errors.append("promotion request target declaration was inferred")
        if str(row.get("candidate_artifact_path", "") or "") or str(
            row.get("candidate_source_hash", "") or ""
        ):
            errors.append("promotion request row already carries candidate lineage")
    return request, tuple(dict.fromkeys(errors))


def bind_generation_response(
    *,
    proposal_packet: Mapping[str, Any],
    generation_request: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    """Bind model output to request identities without parsing or rewriting Lean."""

    requested_rows = [
        dict(row)
        for row in generation_request.get("target_rows", []) or []
        if isinstance(row, Mapping)
    ]
    formal_targets = [
        dict(row)
        for row in proposal_packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
    ]
    requested_ids = [
        str(row.get("source_formal_target_id", "") or "")
        for row in requested_rows
    ]
    response_ids = [str(row.get("id", "") or "") for row in formal_targets]
    errors: list[str] = []
    if len(formal_targets) != len(requested_rows) or sorted(response_ids) != sorted(
        requested_ids
    ):
        errors.append(
            "promotion response formal target set differs from the requested target set"
        )
    bindings: list[dict[str, Any]] = []
    for requested in requested_rows:
        requested_id = str(requested.get("source_formal_target_id", "") or "")
        requested_declaration = str(
            requested.get("target_lean_declaration", "") or ""
        )
        requested_target_ids = [
            str(value)
            for value in requested.get("target_ids", []) or []
            if str(value)
        ]
        matches = [row for row in formal_targets if str(row.get("id", "") or "") == requested_id]
        if len(matches) != 1:
            errors.append(
                f"promotion response target {requested_id} must occur exactly once"
            )
            continue
        target = matches[0]
        provenance = (
            dict(target.get("source_theorem_target_provenance", {}) or {})
            if isinstance(target.get("source_theorem_target_provenance", {}), Mapping)
            else {}
        )
        response_declaration = str(
            target.get("target_lean_declaration", "")
            or provenance.get("target_lean_declaration", "")
            or ""
        )
        if response_declaration != requested_declaration:
            errors.append(
                f"promotion response target {requested_id} changed declaration"
            )
        if str(provenance.get("target_lean_declaration", "") or "") != (
            requested_declaration
        ):
            errors.append(
                f"promotion response target {requested_id} provenance declaration mismatch"
            )
        if not _bool_like(provenance.get("source_theorem_target_known", False)):
            errors.append(
                f"promotion response target {requested_id} is not marked known"
            )
        if str(target.get("expected_status", "") or "") != "NEEDS_KERNEL_CHECK":
            errors.append(
                f"promotion response target {requested_id} must require kernel check"
            )
        candidate_source = str(target.get("lean_statement_sketch", "") or "")
        if not candidate_source.strip():
            errors.append(
                f"promotion response target {requested_id} has no candidate source"
            )
        source_goal_id = str(provenance.get("source_theorem_goal_id", "") or "")
        if requested_target_ids and source_goal_id not in requested_target_ids:
            errors.append(
                f"promotion response target {requested_id} changed target ids"
            )
        bindings.append(
            {
                "source_formal_target_id": requested_id,
                "target_lean_declaration": requested_declaration,
                "target_ids": requested_target_ids,
                "source_theorem_goal_id": source_goal_id,
                "candidate_source_hash": stable_hash(candidate_source),
                "candidate_source_present": bool(candidate_source.strip()),
                "expected_status": str(target.get("expected_status", "") or ""),
                "source_theorem_target_known": _bool_like(
                    provenance.get("source_theorem_target_known", False)
                ),
                "proof_evidence_status": (
                    "PROMOTION_GENERATION_RESPONSE_BINDING_NOT_PROOF_EVIDENCE"
                ),
            }
        )
    return bindings, tuple(dict.fromkeys(errors))


def generation_lineage_failure_result(
    *,
    task: AgentTask,
    errors: Sequence[str],
) -> AgentStepResult:
    failure_id = "source_theorem_promotion_generation_lineage_failure:" + stable_hash(
        [task.task_id, list(errors)]
    )[:20]
    artifact = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeSourceTheoremPromotionGenerationLineageFailure",
        "failure_id": failure_id,
        "task_id": task.task_id,
        "validation_errors": list(errors),
        "proof_evidence_status": (
            "PROMOTION_GENERATION_LINEAGE_REJECTED_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "ProofEngineer rejected a missing, changed, or unbound source-theorem "
            "promotion generation request before any model or prover call."
        ),
        produced_artifacts={failure_id: artifact},
        observations=(
            EnvironmentObservation(
                observation_type=(
                    "source_theorem_promotion_generation_lineage_rejected"
                ),
                summary="; ".join(str(value) for value in errors)[:500],
                payload={
                    "failure_id": failure_id,
                    "validation_errors": list(errors),
                    "proof_evidence_status": artifact["proof_evidence_status"],
                },
            ),
        ),
        evidence_entries=(
            EvidenceLedgerEntry(
                evidence_id="evidence:"
                + stable_hash([task.task_id, failure_id])[:20],
                task_id=task.task_id,
                artifact_id=failure_id,
                evidence_type="source_theorem_promotion_generation_lineage_failure",
                status=artifact["proof_evidence_status"],
                boundary=KERNEL_PROOF_BOUNDARY,
                payload={"validation_errors": list(errors)},
            ),
        ),
        failure_classification=(
            "source_theorem_promotion_generation_lineage_invalid"
        ),
    )


def _task_from_payload(payload: Mapping[str, Any]) -> AgentTask:
    task_id = str(payload.get("task_id", "") or "")
    owner = str(payload.get("owner_subsystem", "") or "")
    if not task_id or not owner:
        raise ValueError("runtime task payload must include task_id and owner_subsystem")
    return AgentTask(
        task_id=task_id,
        owner_subsystem=owner,
        objective=str(payload.get("objective", "") or ""),
        inputs=(
            dict(payload.get("inputs", {}))
            if isinstance(payload.get("inputs", {}), Mapping)
            else {}
        ),
        allowed_tools=tuple(
            str(value) for value in payload.get("allowed_tools", []) or []
        ),
        budget=(
            dict(payload.get("budget", {}))
            if isinstance(payload.get("budget", {}), Mapping)
            else {}
        ),
        expected_artifacts=tuple(
            str(value) for value in payload.get("expected_artifacts", []) or []
        ),
        acceptance_gate=str(payload.get("acceptance_gate", "") or ""),
        stop_condition=str(payload.get("stop_condition", "") or ""),
    )


def _with_architect_control(
    artifact: Mapping[str, Any],
    work_order: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(artifact)
    raw_control = work_order.get("runtime_architect_control", {})
    if isinstance(raw_control, Mapping) and raw_control:
        control = dict(raw_control)
        control["subsystem"] = SOURCE_THEOREM_PROMOTION_SUBSYSTEM
        payload["runtime_architect_control"] = control
    return payload


def _execution_replay_fingerprint(manifest: Mapping[str, Any]) -> str:
    return stable_hash(
        {
            key: manifest.get(key)
            for key in (
                "artifact_kind",
                "manifest_id",
                "question_id",
                "task_id",
                "work_order_id",
                "work_order_hash",
                "source_formalization_manifest_id",
                "source_formalization_manifest_hash",
                "source_work_order_ids",
                "source_work_order_row_hashes",
                "execution_policy_fingerprint",
                "generation_request_id",
                "generation_request_hash",
                "proof_evidence_status",
                "resume_next_task",
                "execution_result_status",
                "execution_failure_classification",
            )
        }
    )


def _blocked_result(
    *,
    observation_type: str,
    rationale: str,
    failure_classification: str,
    work_order_id: str,
    errors: Sequence[str],
    execution_id: str = "",
) -> AgentStepResult:
    return AgentStepResult(
        status="BLOCKED",
        rationale=rationale,
        observations=(
            EnvironmentObservation(
                observation_type=observation_type,
                summary="; ".join(errors)[:500],
                payload={
                    "execution_id": execution_id,
                    "work_order_id": work_order_id,
                    "validation_errors": list(errors),
                    "proof_evidence_status": (
                        "SOURCE_THEOREM_PROMOTION_RUNTIME_INPUT_REJECTED_"
                        "NOT_PROOF_EVIDENCE"
                    ),
                },
            ),
        ),
        failure_classification=failure_classification,
    )


class SourceTheoremPromotionRuntimeWorker:
    """Typed exact-candidate promotion planner with immutable replay."""

    name = SOURCE_THEOREM_PROMOTION_SUBSYSTEM

    def __init__(
        self,
        *,
        out_root: Path,
        repair_available: bool = False,
    ) -> None:
        self.out_root = out_root
        self.repair_available = bool(repair_available)

    def run(
        self,
        task: AgentTask,
        blackboard: BlackboardState,
    ) -> AgentStepResult:
        question_payload = task.inputs.get("question", {})
        question_id = str(
            question_payload.get("id", "")
            if isinstance(question_payload, Mapping)
            else ""
        )
        work_order_id = str(
            task.inputs.get("source_theorem_promotion_work_order_id", "") or ""
        )
        expected_work_order_hash = str(
            task.inputs.get("source_theorem_promotion_work_order_hash", "") or ""
        )
        raw_work_order = blackboard.artifacts.get(work_order_id, {})
        work_order = (
            dict(raw_work_order) if isinstance(raw_work_order, Mapping) else {}
        )
        errors: list[str] = []
        if not question_id:
            errors.append("question id missing")
        if not work_order_id:
            errors.append("work_order_id missing")
        if not work_order:
            errors.append("work order missing from blackboard")
        if str(work_order.get("artifact_kind", "") or "") != (
            SOURCE_THEOREM_PROMOTION_RUNTIME_WORK_ORDER_KIND
        ):
            errors.append("work-order artifact_kind mismatch")
        if str(work_order.get("work_order_id", "") or "") != work_order_id:
            errors.append("work-order identity mismatch")
        if not expected_work_order_hash or stable_hash(work_order) != (
            expected_work_order_hash
        ):
            errors.append("immutable work-order hash mismatch")
        if str(work_order.get("question_id", "") or "") != question_id:
            errors.append("work-order question_id mismatch")
        if str(work_order.get("target_subsystem", "") or "") != self.name:
            errors.append("work-order target_subsystem mismatch")

        source_manifest_id = str(
            work_order.get("source_formalization_manifest_id", "") or ""
        )
        source_manifest_hash = str(
            work_order.get("source_formalization_manifest_hash", "") or ""
        )
        raw_source_manifest = blackboard.artifacts.get(source_manifest_id, {})
        source_manifest = (
            dict(raw_source_manifest)
            if isinstance(raw_source_manifest, Mapping)
            else {}
        )
        if not source_manifest_id or not source_manifest:
            errors.append("source formalization manifest missing from blackboard")
        elif stable_hash(source_manifest) != source_manifest_hash:
            errors.append("source formalization manifest hash mismatch")

        rows = [
            dict(row)
            for row in work_order.get("work_order_rows", []) or []
            if isinstance(row, Mapping)
        ]
        expected_rows = [
            dict(row)
            for row in source_manifest.get(
                "runtime_source_theorem_promotion_planning_rows", []
            )
            or []
            if isinstance(row, Mapping)
        ]
        row_hashes = [stable_hash(row) for row in rows]
        if not rows:
            errors.append("work order contains no promotion-planning rows")
        if rows != expected_rows:
            errors.append("work-order rows differ from source manifest projection")
        if list(work_order.get("work_order_row_hashes", []) or []) != row_hashes:
            errors.append("work-order row hashes mismatch")
        row_ids = [str(row.get("work_order_id", "") or "") for row in rows]
        if any(not value for value in row_ids):
            errors.append("promotion-planning row identity missing")
        if len(set(row_ids)) != len(row_ids):
            errors.append("promotion-planning row identities are not unique")
        expected_packet_id = str(
            source_manifest.get(
                "llm_formalizer_proof_engineer_proposal_id", ""
            )
            or ""
        )
        for row in rows:
            if str(row.get("question_id", "") or "") != question_id:
                errors.append("promotion-planning row question_id mismatch")
            if str(row.get("source_formalizer_packet_id", "") or "") != (
                expected_packet_id
            ):
                errors.append("promotion-planning Formalizer packet mismatch")
            if not str(row.get("source_formal_target_id", "") or ""):
                errors.append("promotion-planning formal target identity missing")
            if not str(row.get("target_lean_declaration", "") or ""):
                errors.append("promotion-planning target declaration missing")
            if str(
                row.get("target_lean_declaration_source", "") or ""
            ) != "formalizer_structured_source_theorem_target_provenance":
                errors.append("promotion-planning target declaration was inferred")
            if not list(row.get("target_ids", []) or []):
                errors.append("promotion-planning target ids missing")
            if str(row.get("candidate_artifact_path", "") or ""):
                errors.append(
                    "promotion-planning row already has an exact candidate; "
                    "route it to ExactSourceTheoremProofBodyExecutor"
                )
            if str(row.get("candidate_source_hash", "") or ""):
                errors.append("candidate hash present without typed exact execution")
            if str(row.get("promotion_mode", "") or "") not in {
                "source_theorem_exact_semantics_or_theorem_promotion",
                "source_theorem_exact_proof_body_repair",
                "source_theorem_proof_body_adapter_required",
            }:
                errors.append("promotion-planning mode invalid")

        execution_policy = (
            dict(work_order.get("execution_policy", {}))
            if isinstance(work_order.get("execution_policy", {}), Mapping)
            else {}
        )
        policy_fingerprint = str(
            work_order.get("execution_policy_fingerprint", "") or ""
        )
        if stable_hash(execution_policy) != policy_fingerprint:
            errors.append("execution policy fingerprint mismatch")
        if execution_policy.get("legacy_route_probe_materialization") is not False:
            errors.append("typed promotion work cannot materialize legacy route probes")
        if execution_policy.get("python_lean_parsing_or_rewrite") is not False:
            errors.append("typed promotion work cannot parse or rewrite Lean")
        return_task_payload = (
            dict(work_order.get("return_task", {}))
            if isinstance(work_order.get("return_task", {}), Mapping)
            else {}
        )
        if str(return_task_payload.get("owner_subsystem", "") or "") != (
            "CriticEvaluator"
        ):
            errors.append("return task is not CriticEvaluator-owned")
        if errors:
            return _blocked_result(
                observation_type="source_theorem_promotion_work_order_rejected",
                rationale=(
                    "SourceTheoremPromotionProofEngineer rejected a missing, changed, "
                    "candidate-bearing, or inferred-target work order before routing "
                    "any coding-agent request."
                ),
                failure_classification="source_theorem_promotion_work_order_invalid",
                work_order_id=work_order_id,
                errors=errors,
            )

        execution_id = "runtime_source_theorem_promotion_execution:" + stable_hash(
            [work_order_id, expected_work_order_hash, policy_fingerprint]
        )[:20]
        replay = self._replay(
            task=task,
            blackboard=blackboard,
            execution_id=execution_id,
            question_id=question_id,
            work_order_id=work_order_id,
            work_order_hash=expected_work_order_hash,
            policy_fingerprint=policy_fingerprint,
        )
        if replay is not None:
            return replay

        generation_request = _with_architect_control(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "RuntimeExactSourceCandidateGenerationRequest",
                "request_id": "runtime_exact_source_candidate_generation_request:"
                + stable_hash([work_order_id, row_hashes])[:20],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question_id": question_id,
                "source_promotion_work_order_id": work_order_id,
                "source_formalization_manifest_id": source_manifest_id,
                "target_rows": rows,
                "target_ids": list(
                    dict.fromkeys(
                        str(value)
                        for row in rows
                        for value in row.get("target_ids", []) or []
                        if str(value)
                    )
                ),
                "target_declarations": list(
                    dict.fromkeys(
                        str(row.get("target_lean_declaration", "") or "")
                        for row in rows
                        if str(row.get("target_lean_declaration", "") or "")
                    )
                ),
                "generation_contract": (
                    "Use the LLM/prover coding agent with signed formal RAG and "
                    "compiler/LSP feedback to emit a complete exact source-theorem "
                    "candidate. Preserve the structured declaration and target ids. "
                    "Do not ask Python to infer Lean grammar, synthesize a route "
                    "probe, rewrite a declaration, or select tactics."
                ),
                "next_compiler_subsystem": "ExactSourceTheoremProofBodyExecutor",
                "proof_evidence_status": (
                    "EXACT_SOURCE_CANDIDATE_GENERATION_REQUEST_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            },
            work_order,
        )
        generation_request_id = str(generation_request["request_id"])
        generation_request_hash = stable_hash(generation_request)

        try:
            return_task = _task_from_payload(return_task_payload)
        except ValueError as exc:
            return _blocked_result(
                observation_type="source_theorem_promotion_return_task_invalid",
                rationale=(
                    "SourceTheoremPromotionProofEngineer could not reconstruct its "
                    "bound Critic return task."
                ),
                failure_classification=(
                    "source_theorem_promotion_return_task_invalid"
                ),
                work_order_id=work_order_id,
                errors=[str(exc)],
                execution_id=execution_id,
            )
        if self.repair_available:
            next_task = self._repair_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                generation_request=generation_request,
            )
            result_status = "REVISE"
            failure_classification = (
                "source_theorem_exact_candidate_generation_required"
            )
        else:
            next_task = self._critic_task(
                return_task,
                question_id=question_id,
                execution_id=execution_id,
                generation_request=generation_request,
            )
            result_status = "REROUTE"
            failure_classification = (
                "source_theorem_exact_candidate_generation_required"
            )
        execution_manifest = _with_architect_control(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": SOURCE_THEOREM_PROMOTION_RUNTIME_EXECUTION_KIND,
                "manifest_id": execution_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question_id": question_id,
                "task_id": task.task_id,
                "work_order_id": work_order_id,
                "work_order_hash": expected_work_order_hash,
                "source_formalization_manifest_id": source_manifest_id,
                "source_formalization_manifest_hash": source_manifest_hash,
                "source_work_order_ids": row_ids,
                "source_work_order_row_hashes": row_hashes,
                "execution_policy_fingerprint": policy_fingerprint,
                "generation_request_id": generation_request_id,
                "generation_request_hash": generation_request_hash,
                "n_generation_targets": len(rows),
                "legacy_route_probe_materializer_invoked": False,
                "legacy_source_theorem_integrator_invoked": False,
                "python_lean_parsing_or_rewrite": False,
                "runtime_generated_lean": False,
                "source_theorem_kernel_verified": False,
                "n_source_theorem_kernel_verified": 0,
                "proof_evidence_status": (
                    "SOURCE_THEOREM_PROMOTION_PLANNING_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                "resume_next_task": asdict(next_task),
                "execution_result_status": result_status,
                "execution_failure_classification": failure_classification,
            },
            work_order,
        )
        execution_manifest["execution_replay_fingerprint"] = (
            _execution_replay_fingerprint(execution_manifest)
        )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:"
            + stable_hash([task.task_id, execution_id])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="source_theorem_promotion_planning",
            status="SOURCE_THEOREM_PROMOTION_PLANNING_NOT_PROOF_EVIDENCE",
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "generation_request_id": generation_request_id,
                "n_generation_targets": len(rows),
                "source_theorem_kernel_verified": False,
                "legacy_route_probe_materializer_invoked": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "The typed promotion child routed a structured exact-candidate "
                "generation request to the LLM/prover without materializing a "
                "route probe or parsing Lean in Python."
            ),
            produced_artifacts={
                execution_id: execution_manifest,
                generation_request_id: generation_request,
            },
            observations=(
                EnvironmentObservation(
                    observation_type="source_theorem_promotion_planning",
                    summary=(
                        f"targets={len(rows)} next_owner={next_task.owner_subsystem} "
                        "source_theorem_kernel_verified=0"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "generation_request_id": generation_request_id,
                        "next_owner_subsystem": next_task.owner_subsystem,
                        "legacy_route_probe_materializer_invoked": False,
                        "source_theorem_kernel_verified": False,
                    },
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=failure_classification,
        )

    @staticmethod
    def _repair_task(
        work_order: Mapping[str, Any],
        *,
        question_id: str,
        execution_id: str,
        generation_request: Mapping[str, Any],
    ) -> AgentTask:
        source = _task_from_payload(
            work_order.get("source_task", {})
            if isinstance(work_order.get("source_task", {}), Mapping)
            else {}
        )
        inputs = dict(source.inputs)
        feedback = (
            dict(inputs.get("environment_feedback", {}) or {})
            if isinstance(inputs.get("environment_feedback", {}), Mapping)
            else {}
        )
        feedback.update(
            {
                "failure_classification": (
                    "source_theorem_exact_candidate_generation_required"
                ),
                "repair_owner_agent": "ProofEngineer",
                "source_theorem_promotion_execution_id": execution_id,
                "source_theorem_promotion_generation_request_id": str(
                    generation_request.get("request_id", "") or ""
                ),
                "source_theorem_promotion_generation_request_hash": stable_hash(
                    dict(generation_request)
                ),
                "source_theorem_promotion_generation_request": dict(
                    generation_request
                ),
                "candidate_generation_contract": str(
                    generation_request.get("generation_contract", "") or ""
                ),
                "next_compiler_subsystem": (
                    "ExactSourceTheoremProofBodyExecutor"
                ),
            }
        )
        inputs["environment_feedback"] = feedback
        inputs["source_theorem_promotion_execution_id"] = execution_id
        inputs["source_theorem_promotion_generation_request_id"] = str(
            generation_request.get("request_id", "") or ""
        )
        inputs["source_theorem_promotion_generation_request_hash"] = stable_hash(
            dict(generation_request)
        )
        context = (
            dict(inputs.get("architect_context", {}) or {})
            if isinstance(inputs.get("architect_context", {}), Mapping)
            else {}
        )
        context["environment_feedback"] = feedback
        inputs["architect_context"] = context
        return replace(
            source,
            task_id=(
                f"source-theorem-promotion-proofengineer:{question_id}:"
                f"{stable_hash(execution_id)[:8]}"
            ),
            owner_subsystem="ProofEngineer",
            inputs=inputs,
        )

    @staticmethod
    def _critic_task(
        base: AgentTask,
        *,
        question_id: str,
        execution_id: str,
        generation_request: Mapping[str, Any],
    ) -> AgentTask:
        inputs = dict(base.inputs)
        inputs["source_theorem_promotion_feedback"] = {
            "failure_classification": (
                "source_theorem_exact_candidate_generation_required"
            ),
            "generation_request": dict(generation_request),
            "source_theorem_kernel_verified": False,
        }
        return replace(
            base,
            task_id=(
                f"critic-source-theorem-promotion:{question_id}:"
                f"{stable_hash(execution_id)[:8]}"
            ),
            inputs=inputs,
        )

    @staticmethod
    def _replay(
        *,
        task: AgentTask,
        blackboard: BlackboardState,
        execution_id: str,
        question_id: str,
        work_order_id: str,
        work_order_hash: str,
        policy_fingerprint: str,
    ) -> AgentStepResult | None:
        if execution_id not in blackboard.artifacts:
            return None
        raw = blackboard.artifacts.get(execution_id, {})
        execution = dict(raw) if isinstance(raw, Mapping) else {}
        errors: list[str] = []
        if str(execution.get("artifact_kind", "") or "") != (
            SOURCE_THEOREM_PROMOTION_RUNTIME_EXECUTION_KIND
        ):
            errors.append("existing execution artifact_kind mismatch")
        if str(execution.get("manifest_id", "") or "") != execution_id:
            errors.append("existing execution identity mismatch")
        if str(execution.get("question_id", "") or "") != question_id:
            errors.append("existing execution question_id mismatch")
        if str(execution.get("task_id", "") or "") != task.task_id:
            errors.append("existing execution task_id mismatch")
        if str(execution.get("work_order_id", "") or "") != work_order_id:
            errors.append("existing execution work-order identity mismatch")
        if str(execution.get("work_order_hash", "") or "") != work_order_hash:
            errors.append("existing execution work-order hash mismatch")
        if str(execution.get("execution_policy_fingerprint", "") or "") != (
            policy_fingerprint
        ):
            errors.append("existing execution policy fingerprint mismatch")
        if str(execution.get("execution_replay_fingerprint", "") or "") != (
            _execution_replay_fingerprint(execution)
        ):
            errors.append("existing execution replay fingerprint mismatch")
        result_status = str(execution.get("execution_result_status", "") or "")
        if result_status not in {"REVISE", "REROUTE"}:
            errors.append("existing execution result status invalid")
        next_payload = execution.get("resume_next_task", {})
        try:
            next_task = _task_from_payload(
                next_payload if isinstance(next_payload, Mapping) else {}
            )
        except ValueError as exc:
            errors.append(f"existing execution resume task invalid: {exc}")
            next_task = None
        if errors or next_task is None:
            return _blocked_result(
                observation_type=(
                    "source_theorem_promotion_execution_replay_rejected"
                ),
                rationale=(
                    "SourceTheoremPromotionProofEngineer rejected a changed or "
                    "incomplete persisted execution before replay."
                ),
                failure_classification=(
                    "source_theorem_promotion_execution_replay_invalid"
                ),
                work_order_id=work_order_id,
                execution_id=execution_id,
                errors=errors,
            )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:"
            + stable_hash([task.task_id, execution_id, "replay"])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="source_theorem_promotion_planning_replay",
            status=str(execution.get("proof_evidence_status", "") or ""),
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "execution_replayed": True,
                "coding_agent_or_materializer_reexecuted": False,
                "source_theorem_kernel_verified": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "SourceTheoremPromotionProofEngineer replayed the immutable "
                "planning execution and resumed its bound next task without "
                "rerunning a coding agent or route-probe materializer."
            ),
            produced_artifacts={execution_id: execution},
            observations=(
                EnvironmentObservation(
                    observation_type="source_theorem_promotion_execution_replayed",
                    summary=(
                        f"execution_id={execution_id} "
                        "coding_agent_or_materializer_reexecuted=0"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "execution_replayed": True,
                        "coding_agent_or_materializer_reexecuted": False,
                        "source_theorem_kernel_verified": False,
                    },
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=str(
                execution.get("execution_failure_classification", "") or ""
            ),
        )
