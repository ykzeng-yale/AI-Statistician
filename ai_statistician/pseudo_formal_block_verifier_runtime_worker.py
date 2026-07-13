from __future__ import annotations

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
from .model_backend import GeneratorBackend
from .pseudo_formal_block_verifier_worker import (
    pseudo_formal_block_verifier_request_rows,
    run_pseudo_formal_block_verifier_rows,
)
from .pseudo_formalization import PSEUDO_FORMALIZATION_PROOF_BOUNDARY


RUNTIME_SCHEMA_VERSION = 1
PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM = "PseudoFormalBlockVerifier"
PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_WORK_ORDER_KIND = (
    "RuntimePseudoFormalBlockVerifierWorkOrder"
)
PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_EXECUTION_KIND = (
    "RuntimePseudoFormalBlockVerifierExecutionManifest"
)
PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_NOT_PROOF_EVIDENCE = (
    "PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_FEEDBACK_NOT_PROOF_EVIDENCE"
)
PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_WORK_ORDER_NOT_PROOF_EVIDENCE = (
    "PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_WORK_ORDER_NOT_PROOF_EVIDENCE"
)
PSEUDO_FORMAL_BLOCK_VERIFIER_INDEPENDENCE_CONTRACT = (
    "Use a fresh BlockVerifier prompt with explicit premises, inherited scope, "
    "dependency statements, conclusion, and local proof text only. Do not expose "
    "hidden dependency proof bodies or treat the verdict as target-prover evidence."
)


SourceRowsResolver = Callable[[Mapping[str, Any]], list[dict[str, Any]]]


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
    control = work_order.get("runtime_architect_control", {})
    if isinstance(control, Mapping) and control:
        payload["runtime_architect_control"] = {
            **dict(control),
            "subsystem": PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM,
        }
    return payload


def _execution_replay_fingerprint(manifest: Mapping[str, Any]) -> str:
    return stable_hash(
        {
            key: manifest.get(key)
            for key in (
                "artifact_kind",
                "manifest_id",
                "question_id",
                "work_order_id",
                "work_order_hash",
                "source_formalization_manifest_id",
                "source_formalization_manifest_hash",
                "source_work_order_row_hashes",
                "runtime_turn_hash",
                "n_request_rows",
                "n_valid_responses",
                "n_runtime_learning_rows",
                "live_generator",
                "execution_contract_satisfied",
                "proof_evidence_status",
                "resume_next_task",
                "execution_result_status",
                "execution_failure_classification",
            )
        }
    )


def _blocked_result(
    *,
    task: AgentTask,
    work_order_id: str,
    errors: Sequence[str],
) -> AgentStepResult:
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            "PseudoFormalBlockVerifier rejected a missing, changed, or cross-task "
            "work order before making an LLM call."
        ),
        observations=(
            EnvironmentObservation(
                observation_type="pseudo_formal_block_verifier_work_order_rejected",
                summary="; ".join(errors)[:500],
                payload={
                    "task_id": task.task_id,
                    "work_order_id": work_order_id,
                    "validation_errors": list(errors),
                    "proof_evidence_status": (
                        PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_NOT_PROOF_EVIDENCE
                    ),
                },
            ),
        ),
        failure_classification="pseudo_formal_block_verifier_work_order_invalid",
    )


class PseudoFormalBlockVerifierRuntimeWorker:
    """Independent PF block verification inside the single AgentRuntime loop."""

    name = PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM

    def __init__(
        self,
        *,
        out_root: Path,
        source_rows_resolver: SourceRowsResolver,
        provider: GeneratorBackend,
        provider_name: str,
        model: str = "",
        model_tier: str = "sonnet",
        max_packets: int = 8,
        max_tokens: int = 2000,
        temperature: float = 0.0,
        max_repair_attempts: int = 1,
    ) -> None:
        self.out_root = out_root
        self.source_rows_resolver = source_rows_resolver
        self.provider = provider
        self.provider_name = str(provider_name or "")
        self.model = str(model or "")
        self.model_tier = str(model_tier or "sonnet")
        self.max_packets = max(1, int(max_packets))
        self.max_tokens = max(1, int(max_tokens))
        self.temperature = float(temperature)
        self.max_repair_attempts = max(0, int(max_repair_attempts))

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
            task.inputs.get("pseudo_formal_block_verifier_work_order_id", "")
            or ""
        )
        expected_work_order_hash = str(
            task.inputs.get("pseudo_formal_block_verifier_work_order_hash", "")
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
            PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_WORK_ORDER_KIND
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
        else:
            if str(source_manifest.get("manifest_id", "") or "") != (
                source_manifest_id
            ):
                errors.append("source formalization manifest identity mismatch")
            if stable_hash(source_manifest) != source_manifest_hash:
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
            errors.append("work order contains no pending PF/BV request rows")
        if rows != expected_rows:
            errors.append("work-order rows differ from source manifest projection")
        if list(work_order.get("work_order_row_hashes", []) or []) != row_hashes:
            errors.append("work-order row hashes mismatch")
        if pseudo_formal_block_verifier_request_rows(
            rows,
            max_packets=max(len(rows), 1),
        ) != rows:
            errors.append("work order contains a completed or non-PF/BV request row")

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
        if execution_policy.get("independence_contract") != (
            PSEUDO_FORMAL_BLOCK_VERIFIER_INDEPENDENCE_CONTRACT
        ):
            errors.append("execution policy independence contract mismatch")
        for key, expected in (
            ("provider_name", self.provider_name),
            ("model", self.model),
            ("model_tier", self.model_tier),
            ("max_packets", self.max_packets),
            ("max_tokens", self.max_tokens),
            ("temperature", self.temperature),
            ("max_repair_attempts", self.max_repair_attempts),
        ):
            if execution_policy.get(key) != expected:
                errors.append(f"execution policy {key} mismatch")
        try:
            source_task = _task_from_payload(
                work_order.get("source_task", {})
                if isinstance(work_order.get("source_task", {}), Mapping)
                else {}
            )
        except ValueError as exc:
            errors.append(f"source task invalid: {exc}")
            source_task = None
        if source_task is not None and source_task.owner_subsystem not in {
            "FormalizationEvaluator",
            "ProofEngineer",
        }:
            errors.append("source task is not FormalizationEvaluator/ProofEngineer-owned")
        try:
            return_task = _task_from_payload(
                work_order.get("return_task", {})
                if isinstance(work_order.get("return_task", {}), Mapping)
                else {}
            )
        except ValueError as exc:
            errors.append(f"return task invalid: {exc}")
            return_task = None
        if return_task is not None and return_task.owner_subsystem != "CriticEvaluator":
            errors.append("return task is not CriticEvaluator-owned")
        if errors or source_task is None or return_task is None:
            return _blocked_result(
                task=task,
                work_order_id=work_order_id,
                errors=errors,
            )

        execution_id = "runtime_pseudo_formal_block_verifier_execution:" + stable_hash(
            [work_order_id, expected_work_order_hash, policy_fingerprint]
        )[:20]
        replay = self._replay(
            task=task,
            blackboard=blackboard,
            execution_id=execution_id,
            question_id=question_id,
            work_order_id=work_order_id,
            work_order_hash=expected_work_order_hash,
        )
        if replay is not None:
            return replay

        execution_dir = (
            self.out_root
            / "runtime_pseudo_formal_block_verifier"
            / stable_hash([question_id, execution_id])[:20]
        )
        runtime_turn = run_pseudo_formal_block_verifier_rows(
            rows,
            provider=self.provider,
            provider_name=self.provider_name,
            model=self.model,
            model_tier=self.model_tier,
            max_packets=self.max_packets,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            max_repair_attempts=self.max_repair_attempts,
            question_id=question_id,
            out_dir=execution_dir / "verifier_turn",
        )
        learning_rows = [
            dict(row)
            for row in runtime_turn.get("runtime_learning_rows", []) or []
            if isinstance(row, Mapping)
        ]
        runtime_turn_id = str(runtime_turn.get("manifest_id", "") or "")
        all_ok = bool(runtime_turn.get("all_ok", False))
        if all_ok:
            next_task = self._proofengineer_task(
                source_task,
                question_id=question_id,
                execution_id=execution_id,
                runtime_turn=runtime_turn,
                learning_rows=learning_rows,
            )
            result_status = "REVISE"
            failure_classification = "pseudo_formal_block_verification_feedback"
        else:
            next_task = self._critic_task(
                return_task,
                question_id=question_id,
                execution_id=execution_id,
                runtime_turn=runtime_turn,
            )
            result_status = "REROUTE"
            failure_classification = (
                "pseudo_formal_block_verifier_response_contract_invalid"
            )

        execution_manifest = _with_architect_control(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": (
                    PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_EXECUTION_KIND
                ),
                "manifest_id": execution_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question_id": question_id,
                "task_id": task.task_id,
                "work_order_id": work_order_id,
                "work_order_hash": expected_work_order_hash,
                "source_formalization_manifest_id": source_manifest_id,
                "source_formalization_manifest_hash": source_manifest_hash,
                "source_work_order_row_hashes": row_hashes,
                "execution_policy_fingerprint": policy_fingerprint,
                "runtime_turn_id": runtime_turn_id,
                "runtime_turn_hash": stable_hash(runtime_turn),
                "runtime_turn_manifest_path": str(
                    runtime_turn.get("manifest_path", "") or ""
                ),
                "runtime_learning_rows": learning_rows,
                "n_request_rows": int(runtime_turn.get("n_request_rows", 0) or 0),
                "n_valid_responses": int(
                    runtime_turn.get("n_valid_responses", 0) or 0
                ),
                "n_runtime_learning_rows": len(learning_rows),
                "n_accepted_blocks": int(
                    runtime_turn.get("n_accepted_blocks", 0) or 0
                ),
                "n_failed_blocks": int(
                    runtime_turn.get("n_failed_blocks", 0) or 0
                ),
                "live_generator": bool(runtime_turn.get("live_generator", False)),
                "static_or_fixture_only": bool(
                    runtime_turn.get("static_or_fixture_only", True)
                ),
                "capability_evidence_ok": bool(
                    all_ok and runtime_turn.get("live_generator", False)
                ),
                "execution_contract_satisfied": all_ok,
                "kernel_verified": False,
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_NOT_PROOF_EVIDENCE
                ),
                "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
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
            evidence_type="pseudo_formal_block_verifier_runtime_feedback",
            status=PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_NOT_PROOF_EVIDENCE,
            boundary=PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "n_request_rows": execution_manifest["n_request_rows"],
                "n_valid_responses": execution_manifest["n_valid_responses"],
                "n_runtime_learning_rows": len(learning_rows),
                "live_generator": execution_manifest["live_generator"],
                "kernel_verified": False,
                "source_theorem_kernel_verified": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "The independent PF/BV worker returned validated block feedback "
                "to ProofEngineer inside the same AgentRuntime; the feedback "
                "remains below the theorem-proof evidence boundary."
                if all_ok
                else "The independent PF/BV worker failed its response contract "
                "and routed exact diagnostics to CriticEvaluator without "
                "promoting a block or theorem."
            ),
            produced_artifacts={
                execution_id: execution_manifest,
                runtime_turn_id: runtime_turn,
            },
            observations=(
                EnvironmentObservation(
                    observation_type="pseudo_formal_block_verifier_runtime_feedback",
                    summary=(
                        f"requests={execution_manifest['n_request_rows']} "
                        f"valid={execution_manifest['n_valid_responses']} "
                        f"accepted={execution_manifest['n_accepted_blocks']} "
                        f"failed={execution_manifest['n_failed_blocks']}"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "runtime_turn_id": runtime_turn_id,
                        "execution_contract_satisfied": all_ok,
                        "proof_evidence_status": (
                            PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_NOT_PROOF_EVIDENCE
                        ),
                    },
                ),
            ),
            tool_calls=(
                ToolCallRecord(
                    tool_name="LLMPseudoFormalBlockVerifier.verify_blocks",
                    inputs={
                        "work_order_id": work_order_id,
                        "provider_name": self.provider_name,
                        "model_tier": self.model_tier,
                        "n_request_rows": len(rows),
                        "hidden_dependency_proof_bodies_available": False,
                    },
                    output_paths=tuple(
                        value
                        for value in (
                            str(runtime_turn.get("manifest_path", "") or ""),
                            str(
                                runtime_turn.get(
                                    "runtime_learning_rows_jsonl", ""
                                )
                                or ""
                            ),
                        )
                        if value
                    ),
                    exit_status="0" if all_ok else "response_contract_feedback",
                    stdout_summary=(
                        f"valid={execution_manifest['n_valid_responses']} "
                        f"learning_rows={len(learning_rows)}"
                    ),
                    safety_boundary=PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=failure_classification,
        )

    @staticmethod
    def _proofengineer_task(
        source_task: AgentTask,
        *,
        question_id: str,
        execution_id: str,
        runtime_turn: Mapping[str, Any],
        learning_rows: Sequence[Mapping[str, Any]],
    ) -> AgentTask:
        inputs = dict(source_task.inputs)
        architect_context = (
            dict(inputs.get("architect_context", {}))
            if isinstance(inputs.get("architect_context", {}), Mapping)
            else {}
        )
        existing_memory = (
            dict(architect_context.get("runtime_learning_memory", {}))
            if isinstance(
                architect_context.get("runtime_learning_memory", {}), Mapping
            )
            else {}
        )
        existing_rows = [
            dict(row)
            for row in existing_memory.get("rows", []) or []
            if isinstance(row, Mapping)
        ]
        merged_rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in [*existing_rows, *learning_rows]:
            fingerprint = stable_hash(row)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            merged_rows.append(dict(row))
        counts = (
            existing_memory.get("counts", {})
            if isinstance(existing_memory.get("counts", {}), Mapping)
            else {}
        )
        row_limit = max(int(counts.get("max_rows", 0) or 0), 20, len(learning_rows))
        merged_rows = merged_rows[-row_limit:]
        memory_context = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeLearningMemoryContext",
            "source_paths": list(existing_memory.get("source_paths", []) or []),
            "rows": merged_rows,
            "counts": {
                "rows_loaded": len(merged_rows),
                "rows_seen": len(existing_rows) + len(learning_rows),
                "source_paths": len(existing_memory.get("source_paths", []) or []),
                "errors": 0,
                "max_rows": row_limit,
                "retention_policy": "priority_pinned_latest_rows",
            },
            "errors": [],
            "boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        }
        architect_context["runtime_learning_memory"] = memory_context
        feedback = (
            dict(inputs.get("environment_feedback", {}))
            if isinstance(inputs.get("environment_feedback", {}), Mapping)
            else {}
        )
        feedback.update(
            {
                "failure_classification": (
                    "pseudo_formal_block_verification_feedback"
                ),
                "pseudo_formal_block_verifier_runtime_execution_id": execution_id,
                "pseudo_formal_independent_block_verification_feedback_active": True,
                "pseudo_formal_independent_block_verification_feedback_memory": [
                    dict(row) for row in learning_rows
                ],
                "n_pseudo_formal_independent_block_verification_feedback_rows": len(
                    learning_rows
                ),
                "pseudo_formal_block_verification_verdicts": [
                    str(
                        (
                            row.get("block_verification", {})
                            if isinstance(row.get("block_verification", {}), Mapping)
                            else {}
                        ).get("verdict", "")
                        or ""
                    )
                    for row in learning_rows
                ],
                "proof_evidence_status": (
                    PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_NOT_PROOF_EVIDENCE
                ),
                "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
            }
        )
        architect_context["environment_feedback"] = feedback
        inputs["architect_context"] = architect_context
        inputs["environment_feedback"] = feedback
        inputs["pseudo_formal_block_verifier_runtime_turn_id"] = str(
            runtime_turn.get("manifest_id", "") or ""
        )
        return replace(
            source_task,
            task_id=(
                f"proofengineer-pseudo-formal-bv:{question_id}:"
                f"{stable_hash(execution_id)[:8]}"
            ),
            owner_subsystem="ProofEngineer",
            inputs=inputs,
            allowed_tools=tuple(
                dict.fromkeys(
                    (
                        *source_task.allowed_tools,
                        "model_backend",
                        "formal_source_retrieval",
                        "proof_search",
                        "local_lean",
                        "lean_lsp_mcp",
                    )
                )
            ),
        )

    @staticmethod
    def _critic_task(
        return_task: AgentTask,
        *,
        question_id: str,
        execution_id: str,
        runtime_turn: Mapping[str, Any],
    ) -> AgentTask:
        inputs = dict(return_task.inputs)
        inputs["pseudo_formal_block_verifier_feedback"] = {
            "failure_classification": (
                "pseudo_formal_block_verifier_response_contract_invalid"
            ),
            "execution_id": execution_id,
            "errors": list(runtime_turn.get("errors", []) or []),
            "proof_evidence_status": (
                PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_NOT_PROOF_EVIDENCE
            ),
            "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        }
        return replace(
            return_task,
            task_id=(
                f"critic-pseudo-formal-bv:{question_id}:"
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
    ) -> AgentStepResult | None:
        if execution_id not in blackboard.artifacts:
            return None
        raw = blackboard.artifacts.get(execution_id, {})
        execution = dict(raw) if isinstance(raw, Mapping) else {}
        errors: list[str] = []
        if str(execution.get("artifact_kind", "") or "") != (
            PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_EXECUTION_KIND
        ):
            errors.append("existing execution artifact_kind mismatch")
        if str(execution.get("manifest_id", "") or "") != execution_id:
            errors.append("existing execution identity mismatch")
        if str(execution.get("question_id", "") or "") != question_id:
            errors.append("existing execution question_id mismatch")
        if str(execution.get("work_order_id", "") or "") != work_order_id:
            errors.append("existing execution work-order identity mismatch")
        if str(execution.get("work_order_hash", "") or "") != work_order_hash:
            errors.append("existing execution work-order hash mismatch")
        if str(execution.get("execution_replay_fingerprint", "") or "") != (
            _execution_replay_fingerprint(execution)
        ):
            errors.append("existing execution replay fingerprint mismatch")
        result_status = str(execution.get("execution_result_status", "") or "")
        if result_status not in {"REVISE", "REROUTE"}:
            errors.append("existing execution result status invalid")
        try:
            next_task = _task_from_payload(
                execution.get("resume_next_task", {})
                if isinstance(execution.get("resume_next_task", {}), Mapping)
                else {}
            )
        except ValueError as exc:
            errors.append(f"existing execution resume task invalid: {exc}")
            next_task = None
        if errors or next_task is None:
            return _blocked_result(
                task=task,
                work_order_id=work_order_id,
                errors=errors,
            )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "Replayed the immutable PF/BV runtime execution without another "
                "LLM call."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type="pseudo_formal_block_verifier_execution_replay",
                    summary=f"execution_id={execution_id}",
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "proof_evidence_status": (
                            PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_NOT_PROOF_EVIDENCE
                        ),
                    },
                ),
            ),
            next_task=next_task,
            failure_classification=str(
                execution.get("execution_failure_classification", "") or ""
            ),
        )
