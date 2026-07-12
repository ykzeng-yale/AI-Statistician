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
from .exact_source_theorem_proof_body_executor import (
    SOURCE_KERNEL_STATUS,
    export_exact_source_theorem_proof_body_execution_results,
)
from .fingerprint import stable_hash
from .research_architect import KERNEL_PROOF_BOUNDARY
from .source_theorem_formal_environment_proofengineer_bridge import (
    run_source_theorem_formal_environment_proofengineer_bridge,
)


RUNTIME_SCHEMA_VERSION = 1
EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM = "ExactSourceTheoremProofBodyExecutor"
EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_WORK_ORDER_KIND = (
    "RuntimeExactSourceTheoremProofBodyWorkOrder"
)
EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_EXECUTION_KIND = (
    "RuntimeExactSourceTheoremProofBodyExecutionManifest"
)


SourceRowsResolver = Callable[[Mapping[str, Any]], list[dict[str, Any]]]
BridgeRunner = Callable[..., Mapping[str, Any]]
ExecutorRunner = Callable[..., Mapping[str, Any]]


def _bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


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
        allowed_tools=tuple(str(value) for value in payload.get("allowed_tools", []) or []),
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


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path_value: Any) -> list[dict[str, Any]]:
    path_text = str(path_value or "").strip()
    if not path_text:
        return []
    try:
        lines = Path(path_text).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            rows.append(dict(value))
    return rows


def _with_architect_control(
    artifact: Mapping[str, Any],
    work_order: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(artifact)
    raw_control = work_order.get("runtime_architect_control", {})
    if isinstance(raw_control, Mapping) and raw_control:
        control = dict(raw_control)
        control["subsystem"] = EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM
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
                "source_candidate_artifact_bindings",
                "execution_policy_fingerprint",
                "bridge_manifest_hash",
                "executor_manifest_hash",
                "n_source_theorem_kernel_verified",
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
                        "EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_INPUT_REJECTED_"
                        "NOT_PROOF_EVIDENCE"
                    ),
                },
            ),
        ),
        failure_classification=failure_classification,
    )


class ExactSourceTheoremProofBodyRuntimeWorker:
    """Typed exact-source compiler worker with immutable resume replay."""

    name = EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM

    def __init__(
        self,
        *,
        out_root: Path,
        source_rows_resolver: SourceRowsResolver,
        bridge_runner: BridgeRunner = (
            run_source_theorem_formal_environment_proofengineer_bridge
        ),
        executor_runner: ExecutorRunner = (
            export_exact_source_theorem_proof_body_execution_results
        ),
        repair_available: bool = False,
    ) -> None:
        self.out_root = out_root
        self.source_rows_resolver = source_rows_resolver
        self.bridge_runner = bridge_runner
        self.executor_runner = executor_runner
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
            task.inputs.get("exact_source_theorem_proof_body_work_order_id", "")
            or ""
        )
        expected_work_order_hash = str(
            task.inputs.get("exact_source_theorem_proof_body_work_order_hash", "")
            or ""
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
            EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_WORK_ORDER_KIND
        ):
            errors.append("work-order artifact_kind mismatch")
        if str(work_order.get("work_order_id", "") or "") != work_order_id:
            errors.append("work-order identity mismatch")
        actual_work_order_hash = stable_hash(work_order) if work_order else ""
        if (
            not expected_work_order_hash
            or actual_work_order_hash != expected_work_order_hash
        ):
            errors.append("immutable work-order hash mismatch")
        if str(work_order.get("question_id", "") or "") != question_id:
            errors.append("work-order question_id mismatch")
        if str(work_order.get("target_subsystem", "") or "") != self.name:
            errors.append("work-order target_subsystem mismatch")

        source_manifest_id = str(
            work_order.get("source_formalization_manifest_id", "") or ""
        )
        raw_source_manifest = blackboard.artifacts.get(source_manifest_id, {})
        source_manifest = (
            dict(raw_source_manifest)
            if isinstance(raw_source_manifest, Mapping)
            else {}
        )
        source_manifest_hash = str(
            work_order.get("source_formalization_manifest_hash", "") or ""
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
        expected_rows = (
            self.source_rows_resolver(source_manifest) if source_manifest else []
        )
        row_hashes = [stable_hash(row) for row in rows]
        if not rows:
            errors.append("work order contains no exact-source rows")
        if rows != expected_rows:
            errors.append("work-order rows differ from source manifest projection")
        if list(work_order.get("work_order_row_hashes", []) or []) != row_hashes:
            errors.append("work-order row hashes mismatch")
        row_ids = [str(row.get("work_order_id", "") or "") for row in rows]
        if any(not row_id for row_id in row_ids):
            errors.append("source work-order identity missing")
        if len(set(row_ids)) != len(row_ids):
            errors.append("source work-order identities are not unique")
        for row in rows:
            if str(row.get("question_id", "") or "") != question_id:
                errors.append("source work-order question_id mismatch")
            if not str(row.get("target_lean_declaration", "") or ""):
                errors.append("source work-order target declaration missing")
            if str(
                row.get("target_lean_declaration_source", "") or ""
            ) != "formalizer_structured_source_theorem_target_provenance":
                errors.append("source work-order target declaration was inferred")
            source_target_id = str(
                row.get("source_formal_target_id", "") or ""
            )
            candidate_id = str(
                row.get("source_formalizer_lean_candidate_id", "") or ""
            )
            if not source_target_id:
                errors.append("source formal target identity missing")
            if not candidate_id or candidate_id != source_target_id:
                errors.append(
                    "materialized candidate identity does not match source formal target"
                )
            if str(row.get("source_formalizer_packet_id", "") or "") != str(
                source_manifest.get(
                    "llm_formalizer_proof_engineer_proposal_id",
                    "",
                )
                or ""
            ):
                errors.append(
                    "source work-order Formalizer packet identity mismatch"
                )

        candidate_bindings = [
            dict(binding)
            for binding in work_order.get("source_candidate_artifact_bindings", [])
            or []
            if isinstance(binding, Mapping)
        ]
        expected_candidate_paths = sorted(
            {
                str(row.get("candidate_artifact_path", "") or "")
                for row in rows
                if str(row.get("candidate_artifact_path", "") or "")
            }
        )
        if sorted(str(row.get("path", "") or "") for row in candidate_bindings) != (
            expected_candidate_paths
        ):
            errors.append("source candidate artifact binding coverage mismatch")
        for binding in candidate_bindings:
            path = Path(str(binding.get("path", "") or ""))
            try:
                source = path.read_text(encoding="utf-8")
            except OSError:
                errors.append(f"source candidate artifact missing: {path}")
                continue
            if stable_hash(source) != str(binding.get("content_hash", "") or ""):
                errors.append(f"source candidate artifact hash mismatch: {path}")

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
        if _bool_like(execution_policy.get("run_signature_probes", False)):
            errors.append(
                "typed exact-source work order cannot enable legacy source-rewriting "
                "signature probes"
            )
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
                observation_type="exact_source_theorem_proof_body_work_order_rejected",
                rationale=(
                    "ExactSourceTheoremProofBodyExecutor rejected a missing, changed, "
                    "cross-task, or grammar-inferred work order before calling the "
                    "bridge or Lean executor."
                ),
                failure_classification=(
                    "exact_source_theorem_proof_body_work_order_invalid"
                ),
                work_order_id=work_order_id,
                errors=errors,
            )

        execution_id = (
            "runtime_exact_source_theorem_proof_body_execution:"
            + stable_hash(
                [work_order_id, expected_work_order_hash, policy_fingerprint]
            )[:20]
        )
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

        execution_dir = self.out_root / "runtime_exact_source_theorem_proof_body" / (
            stable_hash([question_id, execution_id])[:20]
        )
        execution_dir.mkdir(parents=True, exist_ok=True)
        source_queue_path = execution_dir / "source_formal_environment_work_orders.jsonl"
        _write_jsonl(source_queue_path, rows)
        lean_project_text = str(execution_policy.get("lean_project", "") or "")
        lean_project = Path(lean_project_text) if lean_project_text else None
        lean_timeout = max(1, int(execution_policy.get("lean_timeout", 90) or 90))
        run_signature_probes = False
        local_lean = _bool_like(execution_policy.get("local_lean", False))
        overwrite = _bool_like(execution_policy.get("overwrite", False))

        bridge_error = ""
        bridge_manifest: dict[str, Any] = {}
        try:
            raw_bridge = self.bridge_runner(
                out_dir=execution_dir / "formal_environment_bridge",
                queue_jsonl=source_queue_path,
                question_id=question_id,
                run_signature_probes=run_signature_probes,
                lean_project=lean_project,
                lean_timeout=lean_timeout,
            )
            if not isinstance(raw_bridge, Mapping):
                raise TypeError("formal-environment bridge must return a mapping")
            bridge_manifest = dict(raw_bridge)
        except Exception as exc:
            bridge_error = f"{type(exc).__name__}: {exc}"

        bridge_errors = self._bridge_errors(
            bridge_manifest=bridge_manifest,
            source_queue_path=source_queue_path,
            source_rows=rows,
            run_signature_probes=run_signature_probes,
            bridge_error=bridge_error,
        )
        executor_manifest: dict[str, Any] = {}
        executor_error = ""
        queue_manifest_path = self._write_direct_execution_queue(
            source_rows=rows,
            execution_dir=execution_dir,
        )
        if not bridge_errors and queue_manifest_path.exists():
            try:
                raw_executor = self.executor_runner(
                    queue_manifest_path.parent,
                    out_dir=execution_dir / "proof_body_executor",
                    overwrite=overwrite,
                    local_lean=local_lean,
                    lean_project=lean_project,
                    lean_timeout=lean_timeout,
                )
                if not isinstance(raw_executor, Mapping):
                    raise TypeError("proof-body executor must return a mapping")
                executor_manifest = dict(raw_executor)
            except Exception as exc:
                executor_error = f"{type(exc).__name__}: {exc}"
        executor_errors = self._executor_errors(
            executor_manifest=executor_manifest,
            queue_manifest_path=queue_manifest_path,
            local_lean=local_lean,
            executor_error=executor_error,
        )
        contract_errors = [*bridge_errors, *executor_errors]
        executor_rows = [
            dict(row)
            for row in executor_manifest.get("rows", []) or []
            if isinstance(row, Mapping)
        ]
        kernel_rows = [
            row for row in executor_rows if _bool_like(row.get("source_theorem_kernel_verified"))
        ]
        repair_rows = [
            row
            for row in executor_rows
            if not _bool_like(row.get("source_theorem_kernel_verified"))
        ]
        all_kernel_verified = bool(executor_rows) and len(kernel_rows) == len(
            executor_rows
        )

        try:
            return_task = _task_from_payload(return_task_payload)
        except ValueError as exc:
            contract_errors.append(f"return task invalid: {exc}")
            return_task = None
        if contract_errors or return_task is None:
            next_task = self._critic_task(
                return_task_payload,
                question_id=question_id,
                execution_id=execution_id,
                feedback={
                    "failure_classification": (
                        "exact_source_theorem_proof_body_verifier_contract_invalid"
                    ),
                    "contract_errors": contract_errors,
                    "bridge_manifest": bridge_manifest,
                    "executor_manifest": executor_manifest,
                },
            )
            result_status = "REROUTE"
            failure_classification = (
                "exact_source_theorem_proof_body_verifier_contract_invalid"
            )
        elif all_kernel_verified:
            next_task = return_task
            result_status = "REROUTE"
            failure_classification = ""
        elif self.repair_available:
            next_task = self._repair_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                feedback={
                    "failure_classification": (
                        "exact_source_theorem_proof_body_candidate_or_compiler_feedback"
                    ),
                    "executor_rows": repair_rows[:4],
                    "compiler_diagnostics": [
                        list(row.get("diagnostics", []) or [])[:24]
                        for row in repair_rows[:4]
                    ],
                    "proofengineer_repair_contexts": [
                        dict(row.get("proofengineer_repair_context", {}) or {})
                        for row in repair_rows[:4]
                        if isinstance(row.get("proofengineer_repair_context", {}), Mapping)
                    ],
                    "candidate_generation_contract": (
                        "Generate or repair Lean through the LLM/prover coding agent; "
                        "preserve the structured target identity and rerun this exact "
                        "compiler worker. Python must not synthesize Lean grammar or tactics."
                    ),
                },
            )
            result_status = "REVISE"
            failure_classification = (
                "exact_source_theorem_proof_body_candidate_or_compiler_feedback"
            )
        else:
            next_task = return_task
            result_status = "REROUTE"
            failure_classification = (
                "exact_source_theorem_proof_body_candidate_or_compiler_feedback"
            )

        bridge_manifest_id = (
            "runtime_exact_source_formal_environment_bridge:"
            + stable_hash(bridge_manifest)[:20]
        )
        executor_manifest_id = (
            "runtime_exact_source_theorem_proof_body_executor_result:"
            + stable_hash(executor_manifest)[:20]
        )
        learning_rows = self._learning_rows(bridge_manifest, executor_manifest)
        proof_status = (
            "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
            if all_kernel_verified and not contract_errors
            else "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_NOT_PROOF_EVIDENCE"
        )
        execution_manifest = _with_architect_control(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": (
                    EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_EXECUTION_KIND
                ),
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
                "source_candidate_artifact_bindings": candidate_bindings,
                "execution_policy_fingerprint": policy_fingerprint,
                "source_queue_jsonl": str(source_queue_path),
                "proof_body_execution_queue_manifest": str(
                    queue_manifest_path
                ),
                "queue_source_mode": (
                    "agent_runtime_hash_bound_candidate_direct_compiler_gate"
                ),
                "bridge_manifest_path": str(
                    execution_dir
                    / "formal_environment_bridge"
                    / "source_theorem_formal_environment_proofengineer_bridge_manifest.json"
                ),
                "bridge_manifest_id": bridge_manifest_id,
                "bridge_manifest_hash": stable_hash(bridge_manifest),
                "bridge_manifest": bridge_manifest,
                "executor_manifest_id": executor_manifest_id,
                "executor_manifest_hash": stable_hash(executor_manifest),
                "executor_manifest": executor_manifest,
                "executor_manifest_path": str(
                    executor_manifest.get("execution_result_manifest", "") or ""
                ),
                "runtime_learning_rows": learning_rows,
                "n_execution_rows": len(executor_rows),
                "n_source_theorem_kernel_verified": len(kernel_rows),
                "all_source_theorems_kernel_verified": (
                    all_kernel_verified and not contract_errors
                ),
                "contract_errors": contract_errors,
                "execution_contract_satisfied": not contract_errors,
                "runtime_generated_lean": False,
                "structured_target_identity_required": True,
                "python_lean_grammar_generation_or_repair": False,
                "proof_evidence_status": proof_status,
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
        produced_artifacts = {
            execution_id: execution_manifest,
            bridge_manifest_id: _with_architect_control(bridge_manifest, work_order),
            executor_manifest_id: _with_architect_control(executor_manifest, work_order),
        }
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, execution_id])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="exact_source_theorem_proof_body_execution",
            status=proof_status,
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "n_execution_rows": len(executor_rows),
                "n_source_theorem_kernel_verified": len(kernel_rows),
                "all_source_theorems_kernel_verified": (
                    all_kernel_verified and not contract_errors
                ),
                "runtime_generated_lean": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "The typed exact-source worker kernel-verified every bound source "
                "theorem candidate and returned to CriticEvaluator."
                if all_kernel_verified and not contract_errors
                else "The typed exact-source worker returned exact compiler feedback "
                "to the LLM ProofEngineer without synthesizing Lean."
                if result_status == "REVISE"
                else "The typed exact-source worker failed closed on verifier or "
                "candidate evidence and returned the bound result to CriticEvaluator."
            ),
            produced_artifacts=produced_artifacts,
            observations=(
                EnvironmentObservation(
                    observation_type="exact_source_theorem_proof_body_execution",
                    summary=(
                        f"rows={len(executor_rows)} kernel_verified={len(kernel_rows)} "
                        f"contract_errors={len(contract_errors)}"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "proof_evidence_status": proof_status,
                        "repair_routed": result_status == "REVISE",
                    },
                ),
            ),
            tool_calls=(
                ToolCallRecord(
                    tool_name="ExactSourceTheoremProofBodyExecutor.run",
                    inputs={
                        "work_order_id": work_order_id,
                        "source_queue_jsonl": str(source_queue_path),
                        "local_lean": local_lean,
                        "lean_project": lean_project_text,
                    },
                    output_paths=tuple(
                        value
                        for value in (
                            str(bridge_manifest.get("proof_body_execution_queue_manifest", "") or ""),
                            str(executor_manifest.get("execution_results_jsonl", "") or ""),
                        )
                        if value
                    ),
                    exit_status=(
                        "0"
                        if all_kernel_verified and not contract_errors
                        else "candidate_compiler_or_contract_feedback"
                    ),
                    stdout_summary=(
                        f"rows={len(executor_rows)} kernel_verified={len(kernel_rows)}"
                    ),
                    safety_boundary=KERNEL_PROOF_BOUNDARY,
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=failure_classification,
        )

    @staticmethod
    def _write_direct_execution_queue(
        *,
        source_rows: Sequence[Mapping[str, Any]],
        execution_dir: Path,
    ) -> Path:
        queue_dir = execution_dir / "proof_body_execution_queue"
        candidate_dir = queue_dir / "candidate_artifacts"
        transcript_dir = queue_dir / "execution_transcripts"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        transcript_dir.mkdir(parents=True, exist_ok=True)
        queue_rows: list[dict[str, Any]] = []
        for index, source_row in enumerate(source_rows, start=1):
            source_path = str(source_row.get("candidate_artifact_path", "") or "")
            source_hash = str(source_row.get("candidate_source_hash", "") or "")
            source_work_order_id = str(source_row.get("work_order_id", "") or "")
            target_declaration = str(
                source_row.get("target_lean_declaration", "") or ""
            )
            target_ids = [
                str(value)
                for value in (
                    source_row.get("target_ids", [])
                    or source_row.get("target_theorem_goal_ids", [])
                    or [target_declaration]
                )
                if str(value)
            ]
            row_fingerprint = stable_hash(
                [source_work_order_id, source_path, source_hash, target_declaration]
            )
            semantic_blockers = list(
                source_row.get("semantic_alignment_blockers", []) or []
            )
            queue_row = {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": (
                    "runtime_exact_source_theorem_proof_body_queue:"
                    + row_fingerprint[:20]
                ),
                "source_work_order_id": source_work_order_id,
                "question_id": str(source_row.get("question_id", "") or ""),
                "question_title": str(
                    source_row.get("question_title", "") or ""
                ),
                "target_theorem_name": str(
                    source_row.get("target_theorem_name", "")
                    or target_declaration
                ),
                "target_ids": target_ids,
                "target_theorem_goal_ids": target_ids,
                "target_lean_declaration": target_declaration,
                "expected_target_lean_declaration": target_declaration,
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "target_identity_source": (
                    "upstream_structured_target_declaration_and_artifact_hash"
                ),
                "source_theorem_target_known": bool(
                    source_row.get("source_theorem_target_known", False)
                ),
                "source_theorem_target_identity_status": (
                    "SOURCE_THEOREM_TARGET_KNOWN"
                ),
                "source_theorem_target_provenance": dict(
                    source_row.get("source_theorem_target_provenance", {}) or {}
                ),
                "semantic_alignment_constraints": list(
                    source_row.get("semantic_alignment_constraints", []) or []
                ),
                "semantic_alignment_blockers": semantic_blockers,
                "source_theorem_kernel_evidence_eligible": bool(
                    source_row.get(
                        "source_theorem_kernel_evidence_eligible",
                        not semantic_blockers,
                    )
                )
                and not semantic_blockers,
                "source_candidate_artifact_path": source_path,
                "signature_probe_artifact_path": source_path,
                "source_theorem_signature_probe_artifact_path": source_path,
                "proof_body_signature_probe_artifact_path": source_path,
                "signature_probe_artifact_hash": source_hash,
                "expected_signature_probe_artifact_hash": source_hash,
                "candidate_artifact_path": str(
                    candidate_dir / f"candidate_{index:03d}_{row_fingerprint[:12]}.lean"
                ),
                "execution_transcript_path": str(
                    transcript_dir / f"execution_{index:03d}_{row_fingerprint[:12]}.jsonl"
                ),
                "target_lean_file": source_path,
                "target_lean_line": 0,
                "target_lean_column": 0,
                "target_lean_location_source": "not_required_for_compiler_gate",
                "live_goal_location_ready": False,
                "live_proof_state_request": {},
                "already_repaired_environment": dict(
                    source_row.get("already_repaired_environment", {}) or {}
                ),
                "proof_body_attempts": [],
                "proof_body_attempt_source": "llm_prover_generation_required",
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                "proof_evidence_status": (
                    "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
                ),
                "boundary": (
                    "This queue copies an immutable coding-agent candidate directly "
                    "to the compiler gate. Python does not parse or rewrite Lean."
                ),
            }
            for key in (
                "kernel_verified_theorem_reduction_closure_declarations",
                "verified_theorem_reduction_closure_artifact_paths",
                "kernel_verified_theorem_reduction_closure_target_ids",
                "source_theorem_proof_body_adapter_feedback_available",
                "source_theorem_proof_body_adapter_kernel_verified",
                "kernel_verified_source_theorem_proof_body_adapter_ids",
                "verified_source_theorem_proof_body_adapter_artifact_paths",
                "verified_source_theorem_proof_body_adapter_declarations",
                "kernel_verified_source_to_bridge_premise_derivation_ids",
                "verified_source_to_bridge_premise_derivation_artifact_paths",
                "verified_source_to_bridge_premise_derivation_declarations",
                "exact_semantic_definition_context",
            ):
                if key in source_row:
                    queue_row[key] = source_row.get(key)
            queue_rows.append(queue_row)
        rows_path = queue_dir / "exact_source_theorem_proof_body_execution_queue.jsonl"
        manifest_path = (
            queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
        )
        _write_jsonl(rows_path, queue_rows)
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
                    "proof_body_execution_queue_jsonl": str(rows_path),
                    "candidate_artifacts_dir": str(candidate_dir),
                    "execution_transcripts_dir": str(transcript_dir),
                    "n_execution_queue_rows": len(queue_rows),
                    "n_ready": len(queue_rows),
                    "n_live_goal_requests": 0,
                    "queue_source_mode": (
                        "agent_runtime_hash_bound_candidate_direct_compiler_gate"
                    ),
                    "runtime_generated_lean": False,
                    "python_lean_parsing_or_rewrite": False,
                    "rows": queue_rows,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return manifest_path

    @staticmethod
    def _bridge_errors(
        *,
        bridge_manifest: Mapping[str, Any],
        source_queue_path: Path,
        source_rows: Sequence[Mapping[str, Any]],
        run_signature_probes: bool,
        bridge_error: str,
    ) -> list[str]:
        errors: list[str] = []
        if bridge_error:
            errors.append(bridge_error)
        if not bridge_manifest:
            errors.append("formal-environment bridge manifest missing")
            return errors
        try:
            observed_queue = Path(
                str(bridge_manifest.get("source_queue_jsonl", "") or "")
            ).resolve()
        except OSError:
            observed_queue = Path()
        if observed_queue != source_queue_path.resolve():
            errors.append("formal-environment bridge source queue mismatch")
        if int(bridge_manifest.get("n_work_orders", 0) or 0) != len(source_rows):
            errors.append("formal-environment bridge work-order count mismatch")
        if bridge_manifest.get("signature_probes_requested") is not bool(
            run_signature_probes
        ):
            errors.append("formal-environment signature-probe policy mismatch")
        return errors

    @staticmethod
    def _executor_errors(
        *,
        executor_manifest: Mapping[str, Any],
        queue_manifest_path: Path,
        local_lean: bool,
        executor_error: str,
    ) -> list[str]:
        errors: list[str] = []
        if executor_error:
            errors.append(executor_error)
        if not executor_manifest:
            errors.append("exact proof-body executor manifest missing")
            return errors
        if str(executor_manifest.get("artifact_kind", "") or "") != (
            "ExactSourceTheoremProofBodyExecutionResultManifest"
        ):
            errors.append("exact proof-body executor artifact_kind mismatch")
        try:
            observed_queue = Path(
                str(
                    executor_manifest.get(
                        "exact_source_theorem_proof_body_execution_queue_manifest",
                        "",
                    )
                    or ""
                )
            ).resolve()
        except OSError:
            observed_queue = Path()
        if observed_queue != queue_manifest_path.resolve():
            errors.append("exact proof-body executor queue manifest mismatch")
        rows = [
            dict(row)
            for row in executor_manifest.get("rows", []) or []
            if isinstance(row, Mapping)
        ]
        if int(executor_manifest.get("n_execution_result_rows", 0) or 0) != len(rows):
            errors.append("exact proof-body executor result count mismatch")
        verified = 0
        for row in rows:
            if not _bool_like(row.get("source_theorem_kernel_verified")):
                continue
            verified += 1
            if not local_lean or not _bool_like(row.get("local_lean_requested")):
                errors.append("kernel-verified row lacks requested local Lean")
            if not _bool_like(row.get("local_lean_checked")):
                errors.append("kernel-verified row lacks local Lean attempt")
            if not _bool_like(row.get("local_lean_compiled")):
                errors.append("kernel-verified row lacks successful local Lean compile")
            if not _bool_like(row.get("artifact_kernel_verified")):
                errors.append("source theorem promotion lacks artifact kernel evidence")
            if int(row.get("returncode", -1) or 0) != 0:
                errors.append("kernel-verified row has nonzero Lean return code")
            if str(row.get("proof_evidence_status", "") or "") != SOURCE_KERNEL_STATUS:
                errors.append("kernel-verified row proof evidence status mismatch")
            if str(row.get("target_identity_status", "") or "") != (
                "TARGET_DECLARATION_MATCHED"
            ):
                errors.append("kernel-verified row target identity mismatch")
            if str(row.get("target_identity_source", "") or "") != (
                "upstream_structured_target_declaration_and_artifact_hash"
            ):
                errors.append("kernel-verified row target identity was inferred")
            if not _bool_like(row.get("signature_probe_artifact_hash_verified")):
                errors.append("kernel-verified row lacks bound signature artifact hash")
            if not _bool_like(row.get("target_artifact_lineage_verified")):
                errors.append("kernel-verified row lacks exact target artifact lineage")
        if int(executor_manifest.get("n_source_theorem_kernel_verified", 0) or 0) != verified:
            errors.append("executor kernel-verification summary mismatch")
        return errors

    @staticmethod
    def _learning_rows(
        bridge_manifest: Mapping[str, Any],
        executor_manifest: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        rows.extend(_read_jsonl(bridge_manifest.get("runtime_learning_rows_jsonl", "")))
        export = executor_manifest.get("runtime_learning_export", {})
        if isinstance(export, Mapping):
            rows.extend(_read_jsonl(export.get("runtime_learning_rows_jsonl", "")))
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in rows:
            fingerprint = stable_hash(row)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            deduped.append(row)
        return deduped

    @staticmethod
    def _repair_task(
        work_order: Mapping[str, Any],
        *,
        question_id: str,
        execution_id: str,
        feedback: Mapping[str, Any],
    ) -> AgentTask:
        source = _task_from_payload(
            work_order.get("source_task", {})
            if isinstance(work_order.get("source_task", {}), Mapping)
            else {}
        )
        inputs = dict(source.inputs)
        prior_feedback = (
            dict(inputs.get("environment_feedback", {}) or {})
            if isinstance(inputs.get("environment_feedback", {}), Mapping)
            else {}
        )
        prior_feedback.update(dict(feedback))
        inputs["environment_feedback"] = prior_feedback
        context = dict(inputs.get("architect_context", {}) or {})
        context["environment_feedback"] = prior_feedback
        inputs["architect_context"] = context
        return replace(
            source,
            task_id=(
                f"exact-source-proof-body-repair:{question_id}:"
                f"{stable_hash(execution_id)[:8]}"
            ),
            owner_subsystem="ProofEngineer",
            inputs=inputs,
        )

    @staticmethod
    def _critic_task(
        payload: Mapping[str, Any],
        *,
        question_id: str,
        execution_id: str,
        feedback: Mapping[str, Any],
    ) -> AgentTask:
        base = _task_from_payload(payload)
        inputs = dict(base.inputs)
        inputs["exact_source_theorem_proof_body_feedback"] = dict(feedback)
        return replace(
            base,
            task_id=(
                f"critic-exact-source-proof-body:{question_id}:"
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
            EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_EXECUTION_KIND
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
                    "exact_source_theorem_proof_body_execution_replay_rejected"
                ),
                rationale=(
                    "ExactSourceTheoremProofBodyExecutor rejected a changed or "
                    "incomplete persisted execution before replaying tools."
                ),
                failure_classification=(
                    "exact_source_theorem_proof_body_execution_replay_invalid"
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
            evidence_type="exact_source_theorem_proof_body_execution_replay",
            status=str(execution.get("proof_evidence_status", "") or ""),
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "execution_replayed": True,
                "bridge_or_compiler_reexecuted": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "ExactSourceTheoremProofBodyExecutor replayed the immutable "
                "persisted execution and resumed its bound next task without "
                "rerunning the bridge, compiler, or coding agent."
            ),
            produced_artifacts={execution_id: execution},
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "exact_source_theorem_proof_body_execution_replayed"
                    ),
                    summary=(
                        f"execution_id={execution_id} bridge_or_compiler_reexecuted=0"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "execution_replayed": True,
                        "bridge_or_compiler_reexecuted": False,
                    },
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=str(
                execution.get("execution_failure_classification", "") or ""
            ),
        )
