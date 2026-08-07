from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    ToolCallRecord,
)
from .fingerprint import stable_hash
from .research_architect import KERNEL_PROOF_BOUNDARY
from .theorem_reduction_closure_proofengineer_bridge import (
    run_theorem_reduction_closure_proofengineer_bridge,
)


RUNTIME_SCHEMA_VERSION = 1
THEOREM_REDUCTION_CLOSURE_RUNTIME_WORK_ORDER_KIND = (
    "RuntimeTheoremReductionClosureProofEngineerWorkOrder"
)
THEOREM_REDUCTION_CLOSURE_RUNTIME_EXECUTION_KIND = (
    "RuntimeTheoremReductionClosureProofEngineerExecutionManifest"
)
THEOREM_REDUCTION_CLOSURE_RUNTIME_GENERATION_REQUEST_KIND = (
    "RuntimeTheoremReductionClosureCandidateGenerationRequest"
)
THEOREM_REDUCTION_CLOSURE_PROOFENGINEER_SUBSYSTEM = (
    "TheoremReductionClosureProofEngineer"
)


SourceRowsResolver = Callable[[Mapping[str, Any]], list[dict[str, Any]]]
BridgeRunner = Callable[..., Mapping[str, Any]]


def _bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _json_mapping(path_value: Any) -> dict[str, Any]:
    path_text = str(path_value or "").strip()
    if not path_text:
        return {}
    try:
        value = json.loads(Path(path_text).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _jsonl_mapping_rows(path_value: Any) -> list[dict[str, Any]]:
    path_text = str(path_value or "").strip()
    if not path_text:
        return []
    path = Path(path_text)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            rows.append(dict(value))
    return rows


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _task_from_payload(payload: Mapping[str, Any]) -> AgentTask:
    task_id = str(payload.get("task_id", "") or "")
    owner_subsystem = str(payload.get("owner_subsystem", "") or "")
    if not task_id or not owner_subsystem:
        raise ValueError(
            "runtime task payload must include task_id and owner_subsystem"
        )
    return AgentTask(
        task_id=task_id,
        owner_subsystem=owner_subsystem,
        objective=str(payload.get("objective", "") or ""),
        inputs=(
            dict(payload.get("inputs", {}))
            if isinstance(payload.get("inputs", {}), Mapping)
            else {}
        ),
        allowed_tools=tuple(
            str(item)
            for item in payload.get("allowed_tools", []) or []
            if str(item)
        ),
        budget=(
            dict(payload.get("budget", {}))
            if isinstance(payload.get("budget", {}), Mapping)
            else {}
        ),
        expected_artifacts=tuple(
            str(item)
            for item in payload.get("expected_artifacts", []) or []
            if str(item)
        ),
        acceptance_gate=str(payload.get("acceptance_gate", "") or ""),
        stop_condition=str(payload.get("stop_condition", "") or ""),
    )


def _with_bound_architect_control(
    artifact: Mapping[str, Any],
    work_order: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(artifact)
    raw_control = work_order.get("runtime_architect_control", {})
    if not isinstance(raw_control, Mapping) or not raw_control:
        return payload
    control = dict(raw_control)
    control["subsystem"] = THEOREM_REDUCTION_CLOSURE_PROOFENGINEER_SUBSYSTEM
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
                "bridge_result_hash",
                "generation_request_id",
                "generation_request_hash",
                "all_kernel_verified",
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
                        "THEOREM_REDUCTION_CLOSURE_RUNTIME_INPUT_REJECTED_NOT_PROOF_EVIDENCE"
                    ),
                },
            ),
        ),
        failure_classification=failure_classification,
    )


class TheoremReductionClosureRuntimeWorker:
    """Typed theorem-closure compiler worker with immutable resume replay."""

    name = THEOREM_REDUCTION_CLOSURE_PROOFENGINEER_SUBSYSTEM

    def __init__(
        self,
        *,
        out_root: Path,
        source_rows_resolver: SourceRowsResolver,
        bridge_runner: BridgeRunner = (
            run_theorem_reduction_closure_proofengineer_bridge
        ),
        repair_available: bool = False,
    ) -> None:
        self.out_root = out_root
        self.source_rows_resolver = source_rows_resolver
        self.bridge_runner = bridge_runner
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
            task.inputs.get("theorem_reduction_closure_work_order_id", "")
            or ""
        )
        expected_work_order_hash = str(
            task.inputs.get("theorem_reduction_closure_work_order_hash", "")
            or ""
        )
        raw_work_order = blackboard.artifacts.get(work_order_id, {})
        work_order = (
            dict(raw_work_order)
            if isinstance(raw_work_order, Mapping)
            else {}
        )
        validation_errors: list[str] = []
        if not question_id:
            validation_errors.append("task question_id missing")
        if not work_order_id:
            validation_errors.append("work_order_id missing")
        if not work_order:
            validation_errors.append("work order missing from blackboard")
        if str(work_order.get("artifact_kind", "") or "") != (
            THEOREM_REDUCTION_CLOSURE_RUNTIME_WORK_ORDER_KIND
        ):
            validation_errors.append("work-order artifact_kind mismatch")
        if str(work_order.get("work_order_id", "") or "") != work_order_id:
            validation_errors.append("work-order identity mismatch")
        if not expected_work_order_hash or stable_hash(work_order) != (
            expected_work_order_hash
        ):
            validation_errors.append("immutable work-order hash mismatch")
        if str(work_order.get("question_id", "") or "") != question_id:
            validation_errors.append("work-order question_id mismatch")
        if str(work_order.get("target_subsystem", "") or "") != self.name:
            validation_errors.append("work-order target subsystem mismatch")

        source_manifest_id = str(
            work_order.get("source_formalization_manifest_id", "") or ""
        )
        raw_source_manifest = blackboard.artifacts.get(source_manifest_id, {})
        source_manifest = (
            dict(raw_source_manifest)
            if isinstance(raw_source_manifest, Mapping)
            else {}
        )
        if not source_manifest:
            validation_errors.append("source formalization manifest missing")
        if str(source_manifest.get("artifact_kind", "") or "") != (
            "RuntimeFormalizationManifest"
        ):
            validation_errors.append(
                "source formalization artifact_kind mismatch"
            )
        if str(source_manifest.get("manifest_id", "") or "") != (
            source_manifest_id
        ):
            validation_errors.append("source formalization identity mismatch")
        if stable_hash(source_manifest) != str(
            work_order.get("source_formalization_manifest_hash", "") or ""
        ):
            validation_errors.append(
                "source formalization immutable hash mismatch"
            )

        work_order_rows = [
            dict(row)
            for row in work_order.get("work_order_rows", []) or []
            if isinstance(row, Mapping)
        ]
        if not work_order_rows:
            validation_errors.append("work-order rows missing")
        expected_rows = (
            self.source_rows_resolver(source_manifest)
            if source_manifest
            else []
        )
        if stable_hash(work_order_rows) != stable_hash(expected_rows):
            validation_errors.append(
                "work-order rows do not match source manifest"
            )
        recorded_row_hashes = [
            str(value)
            for value in work_order.get("work_order_row_hashes", []) or []
        ]
        if recorded_row_hashes != [
            stable_hash(row) for row in work_order_rows
        ]:
            validation_errors.append("work-order row hash mismatch")
        source_work_order_ids = [
            str(row.get("work_order_id", "") or "").strip()
            for row in work_order_rows
        ]
        if any(not row_id for row_id in source_work_order_ids):
            validation_errors.append("inner work-order identity missing")
        if len(set(source_work_order_ids)) != len(source_work_order_ids):
            validation_errors.append("inner work-order identity duplicated")
        for row in work_order_rows:
            source = str(row.get("lean_statement_sketch", "") or "")
            expected_source_hash = stable_hash(source) if source else ""
            if str(row.get("candidate_source_hash", "") or "") != (
                expected_source_hash
            ):
                validation_errors.append(
                    "work-order candidate source hash mismatch: "
                    + str(row.get("work_order_id", "") or "")
                )
            if source.strip() and not str(
                row.get("target_lean_declaration", "") or ""
            ).strip():
                validation_errors.append(
                    "work-order structured target declaration missing: "
                    + str(row.get("work_order_id", "") or "")
                )

        return_task_payload = (
            work_order.get("return_task", {})
            if isinstance(work_order.get("return_task", {}), Mapping)
            else {}
        )
        source_task_payload = (
            work_order.get("source_task", {})
            if isinstance(work_order.get("source_task", {}), Mapping)
            else {}
        )
        if str(return_task_payload.get("owner_subsystem", "") or "") != (
            "CriticEvaluator"
        ):
            validation_errors.append(
                "return task is not CriticEvaluator-owned"
            )
        if str(source_task_payload.get("task_id", "") or "") != str(
            work_order.get("source_task_id", "") or ""
        ):
            validation_errors.append("source task identity mismatch")
        if str(source_task_payload.get("owner_subsystem", "") or "") != str(
            work_order.get("source_subsystem", "") or ""
        ):
            validation_errors.append("source task subsystem mismatch")

        execution_policy = (
            dict(work_order.get("execution_policy", {}) or {})
            if isinstance(work_order.get("execution_policy", {}), Mapping)
            else {}
        )
        execution_policy_fingerprint = str(
            work_order.get("execution_policy_fingerprint", "") or ""
        )
        if not execution_policy:
            validation_errors.append("execution policy missing")
        if not execution_policy_fingerprint or (
            execution_policy_fingerprint != stable_hash(execution_policy)
        ):
            validation_errors.append("execution policy fingerprint mismatch")
        if validation_errors:
            return _blocked_result(
                observation_type=(
                    "theorem_reduction_closure_work_order_rejected"
                ),
                rationale=(
                    "ProofEngineer rejected a missing, changed, or cross-task "
                    "theorem closure work order before materialization or "
                    "compiler execution."
                ),
                failure_classification=(
                    "theorem_reduction_closure_work_order_invalid"
                ),
                work_order_id=work_order_id,
                errors=validation_errors,
            )

        execution_id = (
            "runtime_theorem_reduction_closure_execution:"
            + stable_hash(
                [
                    work_order_id,
                    expected_work_order_hash,
                    execution_policy_fingerprint,
                ]
            )[:20]
        )
        replay = self._replay(
            task=task,
            blackboard=blackboard,
            execution_id=execution_id,
            question_id=question_id,
            work_order_id=work_order_id,
            work_order_hash=expected_work_order_hash,
            execution_policy_fingerprint=execution_policy_fingerprint,
        )
        if replay is not None:
            return replay

        local_lean = _bool_like(execution_policy.get("local_lean", False))
        lean_project_text = str(
            execution_policy.get("lean_project", "") or ""
        )
        lean_project = Path(lean_project_text) if lean_project_text else None
        lean_timeout = int(execution_policy.get("lean_timeout", 240) or 240)
        execution_dir = (
            self.out_root
            / "runtime_theorem_reduction_closure_proofengineer_worker"
            / stable_hash([work_order_id, expected_work_order_hash])[:16]
        )
        queue_path = execution_dir / "work_orders.jsonl"
        execution_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(queue_path, work_order_rows)

        bridge_error = ""
        try:
            raw_bridge_result = self.bridge_runner(
                out_dir=execution_dir / "bridge",
                queue_jsonl=queue_path,
                question_id=question_id,
                local_lean=local_lean,
                lean_project=lean_project,
                lean_timeout=lean_timeout,
            )
            if not isinstance(raw_bridge_result, Mapping):
                raise TypeError(
                    "theorem closure bridge runner must return a mapping"
                )
            bridge_result = dict(raw_bridge_result)
        except Exception as exc:
            bridge_error = f"{type(exc).__name__}: {exc}"
            bridge_result = {
                "artifact_kind": (
                    "TheoremReductionClosureProofEngineerBridgeFailure"
                ),
                "n_work_orders": len(work_order_rows),
                "n_kernel_verified": 0,
                "runtime_learning_ready": False,
                "proof_evidence_status": (
                    "THEOREM_REDUCTION_CLOSURE_BRIDGE_FAILED_NOT_PROOF_EVIDENCE"
                ),
            }

        audit_payload = _json_mapping(bridge_result.get("audit_manifest", ""))
        learning_rows = _jsonl_mapping_rows(
            bridge_result.get("runtime_learning_rows_jsonl", "")
        )
        checks = [
            dict(row)
            for row in audit_payload.get("checks", []) or []
            if isinstance(row, Mapping)
        ]
        generation_rows = [
            row
            for row in work_order_rows
            if _bool_like(row.get("candidate_generation_required", False))
            or not str(row.get("lean_statement_sketch", "") or "").strip()
        ]
        n_kernel_verified = int(
            bridge_result.get("n_kernel_verified", 0) or 0
        )
        contract_errors = self._bridge_contract_errors(
            bridge_result=bridge_result,
            audit_payload=audit_payload,
            checks=checks,
            work_order_rows=work_order_rows,
            queue_path=queue_path,
            n_kernel_verified=n_kernel_verified,
            local_lean=local_lean,
            bridge_error=bridge_error,
        )
        all_kernel_verified = bool(
            local_lean
            and work_order_rows
            and n_kernel_verified == len(work_order_rows)
            and not contract_errors
        )
        bridge_manifest_path = (
            execution_dir
            / "bridge"
            / "theorem_reduction_closure_proofengineer_bridge_manifest.json"
        )

        generation_request_id = ""
        generation_request_hash = ""
        generation_request: dict[str, Any] | None = None
        if generation_rows:
            generation_request_id = (
                "runtime_theorem_reduction_closure_generation_request:"
                + stable_hash([work_order_id, generation_rows])[:20]
            )
            generation_request = _with_bound_architect_control(
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "artifact_kind": (
                        THEOREM_REDUCTION_CLOSURE_RUNTIME_GENERATION_REQUEST_KIND
                    ),
                    "request_id": generation_request_id,
                    "question_id": question_id,
                    "work_order_id": work_order_id,
                    "work_order_hash": expected_work_order_hash,
                    "source_formalization_manifest_id": source_manifest_id,
                    "generation_rows": generation_rows,
                    "required_behavior": (
                        "LLM ProofEngineer emits a complete target-preserving "
                        "Lean candidate. AgentRuntime passes the exact bytes to "
                        "the configured compiler and returns diagnostics unchanged."
                    ),
                    "runtime_generated_lean": False,
                    "proof_evidence_status": (
                        "LLM_THEOREM_CLOSURE_CANDIDATE_GENERATION_REQUIRED_NOT_PROOF_EVIDENCE"
                    ),
                    "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                },
                work_order,
            )
            generation_request_hash = stable_hash(generation_request)

        failure_classification = (
            "theorem_reduction_closure_kernel_verified"
            if all_kernel_verified
            else "theorem_reduction_closure_execution_contract_invalid"
            if contract_errors
            else "theorem_reduction_closure_candidate_generation_required"
            if generation_rows
            else "theorem_reduction_closure_local_lean_not_requested"
            if not local_lean
            else "theorem_reduction_closure_local_lean_failed"
        )
        feedback = {
            "feedback_type": "theorem_reduction_closure_execution_feedback",
            "failure_classification": failure_classification,
            "source_execution_manifest_id": execution_id,
            "source_work_order_id": work_order_id,
            "source_formalization_manifest_id": source_manifest_id,
            "candidate_generation_request_id": generation_request_id,
            "candidate_generation_rows": generation_rows,
            "compiler_feedback_rows": checks,
            "runtime_learning_rows": learning_rows,
            "execution_contract_errors": contract_errors,
            "n_work_orders": len(work_order_rows),
            "n_kernel_verified": n_kernel_verified,
            "all_kernel_verified": all_kernel_verified,
            "proof_evidence_status": (
                "THEOREM_REDUCTION_CLOSURE_EXECUTION_FEEDBACK_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        }
        repair_required = bool(
            not all_kernel_verified
            and not contract_errors
            and self.repair_available
            and (generation_rows or local_lean)
        )
        next_task = self._task_with_feedback(
            source_task_payload if repair_required else return_task_payload,
            feedback=feedback,
            execution_id=execution_id,
            question_id=question_id,
            repair=repair_required,
        )
        result_status = "REVISE" if repair_required else "REROUTE"
        result_failure = "" if all_kernel_verified else failure_classification

        execution_manifest = _with_bound_architect_control(
            {
                **bridge_result,
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": (
                    THEOREM_REDUCTION_CLOSURE_RUNTIME_EXECUTION_KIND
                ),
                "manifest_id": execution_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question_id": question_id,
                "task_id": task.task_id,
                "work_order_id": work_order_id,
                "work_order_hash": expected_work_order_hash,
                "source_formalization_manifest_id": source_manifest_id,
                "source_formalization_manifest_hash": str(
                    work_order.get(
                        "source_formalization_manifest_hash",
                        "",
                    )
                    or ""
                ),
                "source_work_order_ids": source_work_order_ids,
                "source_work_order_row_hashes": [
                    stable_hash(row) for row in work_order_rows
                ],
                "execution_policy_fingerprint": (
                    execution_policy_fingerprint
                ),
                "source_bridge_artifact_kind": str(
                    bridge_result.get("artifact_kind", "") or ""
                ),
                "bridge_result_hash": stable_hash(bridge_result),
                "bridge_manifest_path": str(bridge_manifest_path),
                "runtime_owned_execution": True,
                "runtime_learning_rows": learning_rows,
                "n_runtime_learning_rows": len(learning_rows),
                "candidate_bytes_preserved": True,
                "runtime_generated_lean": False,
                "n_candidate_generation_required": len(generation_rows),
                "generation_request_id": generation_request_id,
                "generation_request_hash": generation_request_hash,
                "execution_contract_satisfied": not contract_errors,
                "execution_contract_errors": contract_errors,
                "all_kernel_verified": all_kernel_verified,
                "resume_next_task": asdict(next_task),
                "execution_result_status": result_status,
                "execution_failure_classification": result_failure,
                "proof_evidence_status": (
                    "KERNEL_VERIFIED_THEOREM_CLOSURE_PRESENT"
                    if all_kernel_verified
                    else "THEOREM_REDUCTION_CLOSURE_EXECUTION_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                "boundary": (
                    "This AgentRuntime ProofEngineer execution preserves each "
                    "coding-agent candidate byte-for-byte and records compiler "
                    "diagnostics. Python does not parse or synthesize Lean. Only "
                    "bound local Lean/AXLE rows with kernel_verified=true are "
                    "proof evidence for their exact closure artifact; neither "
                    "the work order nor feedback proves the source theorem."
                ),
            },
            work_order,
        )
        execution_manifest["execution_replay_fingerprint"] = (
            _execution_replay_fingerprint(execution_manifest)
        )
        produced_artifacts: dict[str, Any] = {
            execution_id: execution_manifest
        }
        if generation_request is not None:
            produced_artifacts[generation_request_id] = generation_request

        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:"
            + stable_hash([task.task_id, execution_id])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type=(
                "theorem_reduction_closure_proofengineer_execution"
            ),
            status=(
                "KERNEL_VERIFIED_THEOREM_CLOSURE_PRESENT"
                if all_kernel_verified
                else "THEOREM_REDUCTION_CLOSURE_EXECUTION_RECORDED_NOT_PROOF_EVIDENCE"
            ),
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "n_work_orders": len(work_order_rows),
                "n_kernel_verified": n_kernel_verified,
                "all_kernel_verified": all_kernel_verified,
                "candidate_bytes_preserved": True,
                "runtime_generated_lean": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "ProofEngineer verified every theorem-reduction closure row "
                "under the configured local Lean gate and is returning to "
                "CriticEvaluator."
                if all_kernel_verified
                else "ProofEngineer returned missing-candidate or compiler "
                "feedback to the LLM ProofEngineer inside AgentRuntime; no "
                "closure proof was promoted."
                if repair_required
                else "ProofEngineer recorded theorem-closure work as pending "
                "or failed and routed the exact diagnostics to CriticEvaluator."
            ),
            produced_artifacts=produced_artifacts,
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "theorem_reduction_closure_proofengineer_execution"
                    ),
                    summary=(
                        f"work_orders={len(work_order_rows)} "
                        f"kernel_verified={n_kernel_verified} "
                        f"generation_required={len(generation_rows)}"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "candidate_generation_request_id": (
                            generation_request_id
                        ),
                        "all_kernel_verified": all_kernel_verified,
                        "repair_routed": repair_required,
                        "proof_evidence_status": execution_manifest[
                            "proof_evidence_status"
                        ],
                    },
                ),
            ),
            tool_calls=(
                ToolCallRecord(
                    tool_name=(
                        "TheoremReductionClosureProofEngineerBridge.run"
                    ),
                    inputs={
                        "work_order_id": work_order_id,
                        "queue_path": str(queue_path),
                        "local_lean": local_lean,
                        "lean_project": lean_project_text,
                    },
                    output_paths=tuple(
                        str(value)
                        for value in (
                            bridge_manifest_path,
                            bridge_result.get("audit_manifest", ""),
                            bridge_result.get(
                                "runtime_learning_rows_jsonl",
                                "",
                            ),
                        )
                        if str(value)
                    ),
                    exit_status=(
                        "0"
                        if all_kernel_verified
                        else "candidate_or_kernel_feedback_required"
                    ),
                    stdout_summary=(
                        f"work_orders={len(work_order_rows)} "
                        f"kernel_verified={n_kernel_verified}"
                    ),
                    safety_boundary=KERNEL_PROOF_BOUNDARY,
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=result_failure,
        )

    @staticmethod
    def _task_with_feedback(
        payload: Mapping[str, Any],
        *,
        feedback: Mapping[str, Any],
        execution_id: str,
        question_id: str,
        repair: bool,
    ) -> AgentTask:
        base = _task_from_payload(payload)
        next_inputs = dict(base.inputs)
        prior_feedback = (
            dict(next_inputs.get("environment_feedback", {}) or {})
            if isinstance(
                next_inputs.get("environment_feedback", {}),
                Mapping,
            )
            else {}
        )
        prior_feedback.update(feedback)
        next_inputs["environment_feedback"] = prior_feedback
        next_context = dict(next_inputs.get("architect_context", {}) or {})
        next_context["environment_feedback"] = prior_feedback
        next_inputs["architect_context"] = next_context
        return replace(
            base,
            task_id=(
                f"theorem-closure-repair:{question_id}:"
                f"{stable_hash([execution_id, repair])[:8]}"
                if repair
                else f"critic-theorem-closure:{question_id}:"
                f"{stable_hash(execution_id)[:8]}"
            ),
            owner_subsystem=(
                "ProofEngineer" if repair else "CriticEvaluator"
            ),
            inputs=next_inputs,
        )

    @staticmethod
    def _bridge_contract_errors(
        *,
        bridge_result: Mapping[str, Any],
        audit_payload: Mapping[str, Any],
        checks: Sequence[Mapping[str, Any]],
        work_order_rows: Sequence[Mapping[str, Any]],
        queue_path: Path,
        n_kernel_verified: int,
        local_lean: bool,
        bridge_error: str,
    ) -> list[str]:
        errors: list[str] = []
        if int(bridge_result.get("n_work_orders", 0) or 0) != len(
            work_order_rows
        ):
            errors.append("bridge work-order count mismatch")
        try:
            bridge_queue_path = Path(
                str(bridge_result.get("source_queue_jsonl", "") or "")
            ).resolve()
        except OSError:
            bridge_queue_path = Path()
        if bridge_queue_path != queue_path.resolve():
            errors.append("bridge source queue path mismatch")
        if not audit_payload:
            errors.append("bridge audit manifest missing or unreadable")
        elif int(audit_payload.get("n_work_orders", 0) or 0) != len(
            work_order_rows
        ):
            errors.append("audit work-order count mismatch")
        if audit_payload:
            try:
                audit_queue_path = Path(
                    str(audit_payload.get("source_queue_jsonl", "") or "")
                ).resolve()
            except OSError:
                audit_queue_path = Path()
            if audit_queue_path != queue_path.resolve():
                errors.append("audit source queue path mismatch")
        checks_by_id = {
            str(check.get("work_order_id", "") or ""): check
            for check in checks
            if str(check.get("work_order_id", "") or "")
        }
        if audit_payload and len(checks_by_id) != len(work_order_rows):
            errors.append("audit check identity coverage mismatch")
        for row in work_order_rows:
            row_id = str(row.get("work_order_id", "") or "")
            source = str(row.get("lean_statement_sketch", "") or "")
            check = checks_by_id.get(row_id, {})
            if not check:
                continue
            if str(check.get("kernel_checked_source_excerpt", "") or "") != (
                source[:4000]
            ):
                errors.append(
                    f"audit candidate source excerpt mismatch: {row_id}"
                )
            if int(check.get("kernel_checked_source_bytes", -1) or 0) != len(
                source.encode("utf-8")
            ):
                errors.append(
                    f"audit candidate source byte count mismatch: {row_id}"
                )
            if check.get("candidate_bytes_preserved") is not True:
                errors.append(
                    f"audit candidate preservation flag missing: {row_id}"
                )
            if str(check.get("target_lean_declaration", "") or "") != str(
                row.get("target_lean_declaration", "") or ""
            ):
                errors.append(
                    f"audit structured target declaration mismatch: {row_id}"
                )
            if source.strip():
                try:
                    exported_source = Path(
                        str(check.get("lean_export_path", "") or "")
                    ).read_text(encoding="utf-8")
                except OSError:
                    errors.append(f"audit candidate artifact missing: {row_id}")
                else:
                    if exported_source != source:
                        errors.append(
                            f"audit candidate artifact bytes changed: {row_id}"
                        )
            if check.get("kernel_verified") is True:
                if check.get("local_lean_attempted") is not True:
                    errors.append(
                        f"kernel-verified row lacks local Lean attempt: {row_id}"
                    )
                if int(check.get("local_lean_returncode", -1) or 0) != 0:
                    errors.append(
                        f"kernel-verified row has nonzero Lean return code: {row_id}"
                    )
                if str(check.get("status", "") or "") != "KERNEL_VERIFIED":
                    errors.append(
                        f"kernel-verified row status mismatch: {row_id}"
                    )
                if str(check.get("proof_evidence_status", "") or "") != (
                    "KERNEL_VERIFIED_THEOREM_CLOSURE"
                ):
                    errors.append(
                        f"kernel-verified row evidence status mismatch: {row_id}"
                    )
        if n_kernel_verified < 0 or n_kernel_verified > len(work_order_rows):
            errors.append("bridge kernel-verified count invalid")
        audit_verified = int(
            audit_payload.get("n_kernel_verified", 0) or 0
        )
        checks_verified = sum(
            1 for check in checks if check.get("kernel_verified") is True
        )
        if n_kernel_verified != audit_verified:
            errors.append("bridge and audit kernel-verified counts differ")
        if audit_verified != checks_verified:
            errors.append(
                "audit summary and check kernel-verified counts differ"
            )
        if n_kernel_verified and not local_lean:
            errors.append(
                "bridge claimed kernel verification without local Lean"
            )
        if n_kernel_verified:
            if bridge_result.get("local_lean_requested") is not True:
                errors.append(
                    "kernel verification lacks bridge local Lean request"
                )
            if audit_payload.get("local_lean_requested") is not True:
                errors.append(
                    "kernel verification lacks audit local Lean request"
                )
            if audit_payload.get("all_kernel_verified") is not True:
                errors.append(
                    "kernel verification lacks audit all-kernel-verified gate"
                )
            if str(
                audit_payload.get("proof_evidence_status", "") or ""
            ) != "KERNEL_VERIFIED_THEOREM_CLOSURE_PRESENT":
                errors.append(
                    "kernel verification audit evidence status mismatch"
                )
            if str(
                bridge_result.get("proof_evidence_status", "") or ""
            ) != "KERNEL_VERIFIED_THEOREM_CLOSURE_PRESENT":
                errors.append(
                    "kernel verification bridge evidence status mismatch"
                )
        if bridge_error:
            errors.append(bridge_error)
        return errors

    @staticmethod
    def _replay(
        *,
        task: AgentTask,
        blackboard: BlackboardState,
        execution_id: str,
        question_id: str,
        work_order_id: str,
        work_order_hash: str,
        execution_policy_fingerprint: str,
    ) -> AgentStepResult | None:
        if execution_id not in blackboard.artifacts:
            return None
        raw_execution = blackboard.artifacts.get(execution_id)
        execution = (
            dict(raw_execution)
            if isinstance(raw_execution, Mapping)
            else {}
        )
        errors: list[str] = []
        if not execution:
            errors.append("existing execution manifest is not a mapping")
        if str(execution.get("artifact_kind", "") or "") != (
            THEOREM_REDUCTION_CLOSURE_RUNTIME_EXECUTION_KIND
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
        if str(
            execution.get("execution_policy_fingerprint", "") or ""
        ) != execution_policy_fingerprint:
            errors.append("existing execution policy fingerprint mismatch")
        recorded_fingerprint = str(
            execution.get("execution_replay_fingerprint", "") or ""
        )
        if not recorded_fingerprint or recorded_fingerprint != (
            _execution_replay_fingerprint(execution)
        ):
            errors.append("existing execution replay fingerprint mismatch")

        result_status = str(
            execution.get("execution_result_status", "") or ""
        )
        if result_status not in {"REVISE", "REROUTE"}:
            errors.append("existing execution result status invalid")
        next_task_payload = (
            execution.get("resume_next_task", {})
            if isinstance(execution.get("resume_next_task", {}), Mapping)
            else {}
        )
        next_task: AgentTask | None = None
        if not next_task_payload:
            errors.append("existing execution resume task missing")
        else:
            try:
                next_task = _task_from_payload(next_task_payload)
            except (TypeError, ValueError) as exc:
                errors.append(
                    f"existing execution resume task invalid: {exc}"
                )
        if next_task is not None:
            expected_owner = (
                "ProofEngineer"
                if result_status == "REVISE"
                else "CriticEvaluator"
            )
            if next_task.owner_subsystem != expected_owner:
                errors.append(
                    "existing execution resume task owner does not match "
                    "result status"
                )

        produced_artifacts: dict[str, Any] = {execution_id: execution}
        generation_request_id = str(
            execution.get("generation_request_id", "") or ""
        )
        if generation_request_id:
            raw_request = blackboard.artifacts.get(generation_request_id)
            request = (
                dict(raw_request)
                if isinstance(raw_request, Mapping)
                else {}
            )
            if not request:
                errors.append("existing candidate generation request missing")
            elif str(request.get("artifact_kind", "") or "") != (
                THEOREM_REDUCTION_CLOSURE_RUNTIME_GENERATION_REQUEST_KIND
            ):
                errors.append(
                    "existing candidate generation request artifact_kind mismatch"
                )
            elif stable_hash(request) != str(
                execution.get("generation_request_hash", "") or ""
            ):
                errors.append(
                    "existing candidate generation request hash mismatch"
                )
            else:
                produced_artifacts[generation_request_id] = request
        if errors:
            return _blocked_result(
                observation_type=(
                    "theorem_reduction_closure_execution_replay_rejected"
                ),
                rationale=(
                    "ProofEngineer rejected a changed or incomplete persisted "
                    "theorem-closure execution before replaying or calling tools."
                ),
                failure_classification=(
                    "theorem_reduction_closure_execution_replay_invalid"
                ),
                work_order_id=work_order_id,
                execution_id=execution_id,
                errors=errors,
            )

        all_kernel_verified = _bool_like(
            execution.get("all_kernel_verified", False)
        )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:"
            + stable_hash([task.task_id, execution_id, "replay"])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="theorem_reduction_closure_execution_replay",
            status=(
                "KERNEL_VERIFIED_THEOREM_CLOSURE_PRESENT"
                if all_kernel_verified
                else "THEOREM_REDUCTION_CLOSURE_EXECUTION_REPLAYED_NOT_PROOF_EVIDENCE"
            ),
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "execution_replayed": True,
                "bridge_or_compiler_reexecuted": False,
                "all_kernel_verified": all_kernel_verified,
            },
        )
        return AgentStepResult(
            status="REVISE" if result_status == "REVISE" else "REROUTE",
            rationale=(
                "ProofEngineer replayed the immutable persisted theorem-closure "
                "execution and resumed its bound next task without rerunning the "
                "bridge, compiler, or coding agent."
            ),
            produced_artifacts=produced_artifacts,
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "theorem_reduction_closure_execution_replayed"
                    ),
                    summary=(
                        f"execution_id={execution_id} "
                        "bridge_or_compiler_reexecuted=0"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "execution_replayed": True,
                        "bridge_or_compiler_reexecuted": False,
                        "proof_evidence_status": str(
                            execution.get("proof_evidence_status", "") or ""
                        ),
                    },
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=str(
                execution.get("execution_failure_classification", "") or ""
            ),
        )
