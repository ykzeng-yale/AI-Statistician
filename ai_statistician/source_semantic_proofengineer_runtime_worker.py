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
from .source_theorem_semantic_primitive_proofengineer_bridge import (
    ARTIFACT_KIND as SOURCE_SEMANTIC_BRIDGE_ARTIFACT_KIND,
    run_source_theorem_semantic_primitive_proofengineer_bridge,
)


RUNTIME_SCHEMA_VERSION = 1
SOURCE_SEMANTIC_PROOFENGINEER_SUBSYSTEM = "SourceSemanticProofEngineer"
SOURCE_SEMANTIC_RUNTIME_WORK_ORDER_KIND = (
    "RuntimeSourceSemanticProofEngineerWorkOrder"
)
SOURCE_SEMANTIC_RUNTIME_EXECUTION_KIND = (
    "RuntimeSourceSemanticProofEngineerExecutionManifest"
)


SourceRowsResolver = Callable[[Mapping[str, Any]], list[dict[str, Any]]]
BridgeRunner = Callable[..., Mapping[str, Any]]


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
        control["subsystem"] = SOURCE_SEMANTIC_PROOFENGINEER_SUBSYSTEM
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
                "bridge_manifest_hash",
                "n_kernel_verified_support_ids",
                "n_work_orders_with_kernel_verified_support",
                "all_work_orders_have_kernel_verified_support",
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
                        "SOURCE_SEMANTIC_RUNTIME_INPUT_REJECTED_NOT_PROOF_EVIDENCE"
                    ),
                },
            ),
        ),
        failure_classification=failure_classification,
    )


class SourceSemanticProofEngineerRuntimeWorker:
    """Typed semantic-support evaluator with LLM feedback and immutable replay."""

    name = SOURCE_SEMANTIC_PROOFENGINEER_SUBSYSTEM

    def __init__(
        self,
        *,
        out_root: Path,
        source_rows_resolver: SourceRowsResolver,
        bridge_runner: BridgeRunner = (
            run_source_theorem_semantic_primitive_proofengineer_bridge
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
            task.inputs.get("source_semantic_work_order_id", "") or ""
        )
        expected_work_order_hash = str(
            task.inputs.get("source_semantic_work_order_hash", "") or ""
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
            SOURCE_SEMANTIC_RUNTIME_WORK_ORDER_KIND
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
            errors.append("work order contains no semantic-support rows")
        if rows != expected_rows:
            errors.append("work-order rows differ from source manifest projection")
        if list(work_order.get("work_order_row_hashes", []) or []) != row_hashes:
            errors.append("work-order row hashes mismatch")
        row_ids = [str(row.get("work_order_id", "") or "") for row in rows]
        if any(not value for value in row_ids):
            errors.append("source semantic work-order identity missing")
        if len(set(row_ids)) != len(row_ids):
            errors.append("source semantic work-order identities are not unique")
        for row in rows:
            if str(row.get("question_id", "") or "") != question_id:
                errors.append("source semantic work-order question_id mismatch")
            if not str(row.get("semantic_primitive_id", "") or ""):
                errors.append("semantic primitive identity missing")

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
                observation_type="source_semantic_work_order_rejected",
                rationale=(
                    "SourceSemanticProofEngineer rejected a missing, changed, or "
                    "cross-task work order before invoking retrieval or Lean."
                ),
                failure_classification="source_semantic_work_order_invalid",
                work_order_id=work_order_id,
                errors=errors,
            )

        execution_id = "runtime_source_semantic_execution:" + stable_hash(
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

        execution_dir = self.out_root / "runtime_source_semantic_proofengineer" / (
            stable_hash([question_id, execution_id])[:20]
        )
        execution_dir.mkdir(parents=True, exist_ok=True)
        source_queue_path = execution_dir / "source_semantic_work_orders.jsonl"
        _write_jsonl(source_queue_path, rows)
        local_lean = _bool_like(execution_policy.get("local_lean", False))
        lean_project_text = str(execution_policy.get("lean_project", "") or "")
        lean_project = Path(lean_project_text) if lean_project_text else None
        lean_timeout = max(1, int(execution_policy.get("lean_timeout", 90) or 90))

        bridge_error = ""
        bridge_manifest: dict[str, Any] = {}
        try:
            raw_bridge = self.bridge_runner(
                out_dir=execution_dir / "semantic_support_bridge",
                queue_jsonl=source_queue_path,
                question_id=question_id,
                local_lean=local_lean,
                lean_project=lean_project,
                lean_timeout=lean_timeout,
            )
            if not isinstance(raw_bridge, Mapping):
                raise TypeError("source-semantic bridge must return a mapping")
            bridge_manifest = dict(raw_bridge)
        except Exception as exc:
            bridge_error = f"{type(exc).__name__}: {exc}"

        contract_errors = self._bridge_errors(
            bridge_manifest=bridge_manifest,
            source_queue_path=source_queue_path,
            source_rows=rows,
            local_lean=local_lean,
            bridge_error=bridge_error,
        )
        checks = [
            dict(row)
            for row in bridge_manifest.get("checks", []) or []
            if isinstance(row, Mapping)
        ]
        verified_support_ids = list(
            dict.fromkeys(
                str(value)
                for row in checks
                for value in row.get(
                    "kernel_verified_registered_obligation_ids", []
                )
                or []
                if str(value)
            )
        )
        n_supported_work_orders = sum(
            1
            for row in checks
            if row.get("kernel_verified_registered_obligation_ids")
        )
        all_supported = bool(checks) and n_supported_work_orders == len(checks)
        learning_rows = _read_jsonl(
            bridge_manifest.get("runtime_learning_rows_jsonl", "")
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
                        "source_semantic_verifier_contract_invalid"
                    ),
                    "contract_errors": contract_errors,
                },
            )
            result_status = "REROUTE"
            failure_classification = "source_semantic_verifier_contract_invalid"
        elif self.repair_available:
            next_task = self._repair_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                feedback={
                    "failure_classification": (
                        "source_semantic_definition_or_proof_required"
                    ),
                    "source_semantic_bridge_checks": checks[:8],
                    "runtime_learning_rows": learning_rows[:12],
                    "kernel_verified_registered_support_ids": (
                        verified_support_ids
                    ),
                    "registered_support_is_source_theorem_proof": False,
                    "candidate_generation_contract": (
                        "Use the LLM Formalizer/ProofEngineer with signed RAG, "
                        "Lean compiler/LSP diagnostics, and exact source context. "
                        "Registered support is retrieval/calibration context only; "
                        "Python must not generate Lean grammar or tactics."
                    ),
                },
            )
            result_status = "REVISE"
            failure_classification = (
                "source_semantic_definition_or_proof_required"
            )
        else:
            next_task = return_task
            result_status = "REROUTE"
            failure_classification = (
                "source_semantic_definition_or_proof_required"
            )

        bridge_manifest_id = "runtime_source_semantic_bridge:" + stable_hash(
            bridge_manifest
        )[:20]
        proof_status = (
            "KERNEL_VERIFIED_SOURCE_SEMANTIC_SUPPORT_PRESENT"
            if verified_support_ids and not contract_errors
            else "SOURCE_SEMANTIC_EXECUTION_NOT_PROOF_EVIDENCE"
        )
        execution_manifest = _with_architect_control(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": SOURCE_SEMANTIC_RUNTIME_EXECUTION_KIND,
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
                "source_queue_jsonl": str(source_queue_path),
                "bridge_manifest_id": bridge_manifest_id,
                "bridge_manifest_hash": stable_hash(bridge_manifest),
                "bridge_manifest_path": str(
                    execution_dir
                    / "semantic_support_bridge"
                    / "source_theorem_semantic_primitive_proofengineer_bridge_manifest.json"
                ),
                "bridge_manifest": bridge_manifest,
                "runtime_learning_rows": learning_rows,
                "n_work_orders": len(rows),
                "n_kernel_verified_support_ids": len(verified_support_ids),
                "kernel_verified_support_ids": verified_support_ids,
                "n_work_orders_with_kernel_verified_support": (
                    n_supported_work_orders
                ),
                "all_work_orders_have_kernel_verified_support": all_supported,
                "source_theorem_kernel_verified": False,
                "registered_support_is_source_theorem_proof": False,
                "runtime_generated_lean": False,
                "python_lean_grammar_generation_or_repair": False,
                "contract_errors": contract_errors,
                "execution_contract_satisfied": not contract_errors,
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
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:"
            + stable_hash([task.task_id, execution_id])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="source_semantic_support_execution",
            status=proof_status,
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "n_work_orders": len(rows),
                "n_kernel_verified_support_ids": len(verified_support_ids),
                "source_theorem_kernel_verified": False,
                "registered_support_is_source_theorem_proof": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "The typed source-semantic child returned registered support and "
                "unresolved semantic work to the LLM ProofEngineer without "
                "generating Lean."
                if result_status == "REVISE"
                else "The typed source-semantic child failed closed on its bound "
                "contract and returned the result to CriticEvaluator."
            ),
            produced_artifacts={
                execution_id: execution_manifest,
                bridge_manifest_id: _with_architect_control(
                    bridge_manifest, work_order
                ),
            },
            observations=(
                EnvironmentObservation(
                    observation_type="source_semantic_support_execution",
                    summary=(
                        f"work_orders={len(rows)} support_ids="
                        f"{len(verified_support_ids)} contract_errors="
                        f"{len(contract_errors)}"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "proof_evidence_status": proof_status,
                        "source_theorem_kernel_verified": False,
                        "repair_routed": result_status == "REVISE",
                    },
                ),
            ),
            tool_calls=(
                ToolCallRecord(
                    tool_name="SourceSemanticProofEngineer.evaluate_support",
                    inputs={
                        "work_order_id": work_order_id,
                        "source_queue_jsonl": str(source_queue_path),
                        "local_lean": local_lean,
                        "lean_project": lean_project_text,
                    },
                    output_paths=tuple(
                        value
                        for value in (
                            str(
                                bridge_manifest.get(
                                    "source_proof_audit_manifest", ""
                                )
                                or ""
                            ),
                            str(
                                bridge_manifest.get(
                                    "runtime_learning_rows_jsonl", ""
                                )
                                or ""
                            ),
                        )
                        if value
                    ),
                    exit_status=(
                        "0" if not contract_errors else "contract_feedback"
                    ),
                    safety_boundary=KERNEL_PROOF_BOUNDARY,
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=failure_classification,
        )

    @staticmethod
    def _bridge_errors(
        *,
        bridge_manifest: Mapping[str, Any],
        source_queue_path: Path,
        source_rows: Sequence[Mapping[str, Any]],
        local_lean: bool,
        bridge_error: str,
    ) -> list[str]:
        errors: list[str] = []
        if bridge_error:
            errors.append(bridge_error)
        if not bridge_manifest:
            errors.append("source-semantic bridge manifest missing")
            return errors
        if str(bridge_manifest.get("artifact_kind", "") or "") != (
            SOURCE_SEMANTIC_BRIDGE_ARTIFACT_KIND
        ):
            errors.append("source-semantic bridge artifact_kind mismatch")
        try:
            observed_queue = Path(
                str(bridge_manifest.get("source_queue_jsonl", "") or "")
            ).resolve()
        except OSError:
            observed_queue = Path()
        if observed_queue != source_queue_path.resolve():
            errors.append("source-semantic bridge source queue mismatch")
        if int(bridge_manifest.get("n_work_orders", 0) or 0) != len(source_rows):
            errors.append("source-semantic bridge work-order count mismatch")
        if bridge_manifest.get("local_lean_requested") is not bool(local_lean):
            errors.append("source-semantic bridge local-Lean policy mismatch")
        checks = [
            dict(row)
            for row in bridge_manifest.get("checks", []) or []
            if isinstance(row, Mapping)
        ]
        if len(checks) != len(source_rows):
            errors.append("source-semantic bridge check count mismatch")
        source_ids = [str(row.get("work_order_id", "") or "") for row in source_rows]
        check_ids = [str(row.get("work_order_id", "") or "") for row in checks]
        if check_ids != source_ids:
            errors.append("source-semantic bridge work-order lineage mismatch")
        verified_ids = [
            str(value)
            for row in checks
            for value in row.get("kernel_verified_registered_obligation_ids", [])
            or []
            if str(value)
        ]
        if verified_ids and not local_lean:
            errors.append("kernel-verified semantic support lacks requested local Lean")
        if verified_ids:
            audit_path = Path(
                str(bridge_manifest.get("source_proof_audit_manifest", "") or "")
            )
            if not audit_path.exists():
                errors.append("kernel-verified semantic support audit manifest missing")
            else:
                try:
                    audit_payload = json.loads(
                        audit_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError):
                    audit_payload = {}
                audit_checks = [
                    row
                    for row in (
                        audit_payload.get("checks", [])
                        if isinstance(audit_payload, Mapping)
                        else []
                    )
                    or []
                    if isinstance(row, Mapping)
                ]
                audit_verified_ids = {
                    str(row.get("obligation_id", "") or "")
                    for row in audit_checks
                    if _bool_like(row.get("kernel_verified", False))
                    and str(row.get("obligation_id", "") or "")
                }
                if not set(verified_ids).issubset(audit_verified_ids):
                    errors.append(
                        "semantic support ids are not kernel verified in bound audit"
                    )
                if int(
                    audit_payload.get("n_kernel_verified", 0)
                    if isinstance(audit_payload, Mapping)
                    else 0
                ) != len(audit_verified_ids):
                    errors.append(
                        "semantic support audit kernel-verification count mismatch"
                    )
        if _bool_like(bridge_manifest.get("source_theorem_ready_for_exact_proof_body")):
            errors.append(
                "registered semantic-support bridge cannot certify exact proof-body readiness"
            )
        return errors

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
        context = (
            dict(inputs.get("architect_context", {}) or {})
            if isinstance(inputs.get("architect_context", {}), Mapping)
            else {}
        )
        context["environment_feedback"] = prior_feedback
        inputs["architect_context"] = context
        return replace(
            source,
            task_id=(
                f"source-semantic-proofengineer:{question_id}:"
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
        inputs["source_semantic_feedback"] = dict(feedback)
        return replace(
            base,
            task_id=(
                f"critic-source-semantic:{question_id}:"
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
            SOURCE_SEMANTIC_RUNTIME_EXECUTION_KIND
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
                observation_type="source_semantic_execution_replay_rejected",
                rationale=(
                    "SourceSemanticProofEngineer rejected a changed or incomplete "
                    "persisted execution before replaying tools."
                ),
                failure_classification="source_semantic_execution_replay_invalid",
                work_order_id=work_order_id,
                execution_id=execution_id,
                errors=errors,
            )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:"
            + stable_hash([task.task_id, execution_id, "replay"])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="source_semantic_support_execution_replay",
            status=str(execution.get("proof_evidence_status", "") or ""),
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "execution_replayed": True,
                "bridge_or_lean_reexecuted": False,
                "source_theorem_kernel_verified": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "SourceSemanticProofEngineer replayed its immutable execution and "
                "resumed the bound next task without rerunning retrieval or Lean."
            ),
            produced_artifacts={execution_id: execution},
            observations=(
                EnvironmentObservation(
                    observation_type="source_semantic_execution_replayed",
                    summary=(
                        f"execution_id={execution_id} bridge_or_lean_reexecuted=0"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "execution_replayed": True,
                        "bridge_or_lean_reexecuted": False,
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
