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
from .exact_semantic_definition_runtime_worker import (
    EXACT_SEMANTIC_DEFINITION_REVIEW_EXECUTION_KIND,
    EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
    EXACT_SEMANTIC_DEFINITION_REVIEW_WORK_ORDER_KIND,
    EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_KIND,
    ExactSemanticDefinitionRuntimeWorker,
    _bound_text_file,
    _candidate_file_bindings_from_rows,
    _read_jsonl,
    _same_path,
    _task_from_payload,
    _with_architect_control,
)
from .exact_source_theorem_proof_body_executor import (
    SOURCE_KERNEL_STATUS,
    export_exact_source_theorem_proof_body_execution_results,
)
from .exact_source_theorem_proof_body_runtime_worker import (
    ExactSourceTheoremProofBodyRuntimeWorker,
)
from .fingerprint import stable_hash
from .model_backend import GeneratorBackend
from .research_architect import KERNEL_PROOF_BOUNDARY
from .source_theorem_exact_semantic_definition_authoring_worker import (
    AuthoringCandidateMaterializerConfig,
    AuthoringWorkerConfig,
    run_source_theorem_exact_semantic_definition_authoring_candidate_materializer,
    run_source_theorem_exact_semantic_definition_authoring_worker,
)
from .source_theorem_exact_semantic_definition_lean_environment_repair_executor import (
    ARTIFACT_KIND as ENVIRONMENT_ARTIFACT_KIND,
    PROOF_EVIDENCE_STATUS as ENVIRONMENT_PROOF_STATUS,
    run_source_theorem_exact_semantic_definition_lean_environment_repair_executor,
)
from .source_theorem_exact_semantic_definition_lean_repair_executor import (
    run_source_theorem_exact_semantic_definition_lean_repair_executor,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    TYPECHECKED_REVIEW_RECHECK_QUEUE_PROOF_EVIDENCE_STATUS,
    run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue,
)
from .source_theorem_exact_semantic_definition_verifier_gate_executor import (
    ARTIFACT_KIND as VERIFIER_ARTIFACT_KIND,
    PROOF_EVIDENCE_STATUS as VERIFIER_PROOF_STATUS,
    run_source_theorem_exact_semantic_definition_verifier_gate_executor,
)


RUNTIME_SCHEMA_VERSION = 1
RECHECK_ARTIFACT_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedReviewRecheckQueueManifest"
)
REVIEW_FEEDBACK_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_REVIEW_FEEDBACK_NOT_SOURCE_THEOREM_PROOF"
)


SourceRowsResolver = Callable[[Mapping[str, Any]], list[dict[str, Any]]]
StageRunner = Callable[..., Mapping[str, Any]]


def _bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _stage_artifact_id(stage: str, manifest: Mapping[str, Any]) -> str:
    return (
        f"runtime_exact_semantic_definition_review_{stage}:"
        f"{stable_hash(dict(manifest))[:20]}"
    )


def _source_candidate_bindings(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for path_text in sorted(
        {
            str(row.get("candidate_artifact_path", "") or "")
            for row in rows
            if str(row.get("candidate_artifact_path", "") or "")
        }
    ):
        path = Path(path_text)
        try:
            source = path.read_text(encoding="utf-8")
            present = True
        except OSError:
            source = ""
            present = False
        bindings.append(
            {
                "path": path_text,
                "present": present,
                "content_hash": stable_hash(source) if present else "",
                "utf8_bytes": len(source.encode("utf-8")),
            }
        )
    return bindings


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
                "parent_work_order_id",
                "parent_work_order_hash",
                "source_formalization_manifest_id",
                "source_formalization_manifest_hash",
                "source_repair_manifest_id",
                "source_repair_manifest_hash",
                "source_proof_body_row_hashes",
                "review_execution_policy_fingerprint",
                "stage_artifact_hashes",
                "output_file_bindings",
                "n_environment_tasks",
                "n_authoring_tasks",
                "n_review_packets",
                "n_verifier_gate_work_orders",
                "n_verifier_approved",
                "n_proof_body_execution_rows",
                "n_source_theorem_kernel_verified",
                "source_theorem_kernel_verified",
                "runtime_generated_lean",
                "python_lean_grammar_generation_or_repair",
                "execution_contract_satisfied",
                "proof_evidence_status",
                "resume_next_task",
                "execution_result_status",
                "execution_failure_classification",
            )
        }
    )


class ExactSemanticDefinitionReviewRuntimeWorker:
    """Continue exact-semantic LLM/compiler feedback inside AgentRuntime."""

    name = EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM

    def __init__(
        self,
        *,
        out_root: Path,
        source_proof_body_rows_resolver: SourceRowsResolver,
        source_roots: Sequence[Path] = (),
        local_lean: bool = False,
        lean_project: Path | None = None,
        lean_timeout: int = 90,
        authoring_provider: GeneratorBackend | None = None,
        authoring_enabled: bool = False,
        authoring_config: AuthoringWorkerConfig = AuthoringWorkerConfig(),
        materializer_config: AuthoringCandidateMaterializerConfig = (
            AuthoringCandidateMaterializerConfig()
        ),
        review_execution_policy: Mapping[str, Any] | None = None,
        repair_available: bool = False,
        environment_runner: StageRunner = (
            run_source_theorem_exact_semantic_definition_lean_environment_repair_executor
        ),
        authoring_runner: StageRunner = (
            run_source_theorem_exact_semantic_definition_authoring_worker
        ),
        materializer_runner: StageRunner = (
            run_source_theorem_exact_semantic_definition_authoring_candidate_materializer
        ),
        lean_repair_runner: StageRunner = (
            run_source_theorem_exact_semantic_definition_lean_repair_executor
        ),
        recheck_runner: StageRunner = (
            run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue
        ),
        verifier_runner: StageRunner = (
            run_source_theorem_exact_semantic_definition_verifier_gate_executor
        ),
        proof_body_executor: StageRunner = (
            export_exact_source_theorem_proof_body_execution_results
        ),
    ) -> None:
        self.out_root = out_root
        self.source_proof_body_rows_resolver = source_proof_body_rows_resolver
        self.source_roots = tuple(Path(value) for value in source_roots)
        self.local_lean = bool(local_lean)
        self.lean_project = lean_project
        self.lean_timeout = max(1, int(lean_timeout))
        self.authoring_provider = authoring_provider
        self.authoring_enabled = bool(authoring_enabled)
        self.authoring_config = authoring_config
        self.materializer_config = materializer_config
        self.review_execution_policy = dict(review_execution_policy or {})
        self.repair_available = bool(repair_available)
        self.environment_runner = environment_runner
        self.authoring_runner = authoring_runner
        self.materializer_runner = materializer_runner
        self.lean_repair_runner = lean_repair_runner
        self.recheck_runner = recheck_runner
        self.verifier_runner = verifier_runner
        self.proof_body_executor = proof_body_executor

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question_payload = task.inputs.get("question", {})
        question_id = str(
            question_payload.get("id", "")
            if isinstance(question_payload, Mapping)
            else ""
        )
        work_order_id = str(
            task.inputs.get(
                "exact_semantic_definition_review_work_order_id",
                "",
            )
            or ""
        )
        expected_work_order_hash = str(
            task.inputs.get(
                "exact_semantic_definition_review_work_order_hash",
                "",
            )
            or ""
        )
        raw_work_order = blackboard.artifacts.get(work_order_id, {})
        work_order = dict(raw_work_order) if isinstance(raw_work_order, Mapping) else {}
        validation_errors = self._work_order_errors(
            question_id=question_id,
            work_order_id=work_order_id,
            expected_work_order_hash=expected_work_order_hash,
            work_order=work_order,
            blackboard=blackboard,
        )
        if validation_errors:
            return self._blocked_result(
                task=task,
                work_order_id=work_order_id,
                errors=validation_errors,
                failure_classification=(
                    "exact_semantic_definition_review_work_order_invalid"
                ),
            )

        policy_fingerprint = str(
            work_order.get("review_execution_policy_fingerprint", "") or ""
        )
        execution_id = (
            "runtime_exact_semantic_definition_review_execution:"
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

        execution_dir = (
            self.out_root
            / "runtime_exact_semantic_definition_review_proofengineer"
            / stable_hash([question_id, execution_id])[:20]
        )
        execution_dir.mkdir(parents=True, exist_ok=True)
        input_paths = {
            str(binding.get("role", "") or ""): Path(str(binding.get("path", "") or ""))
            for binding in work_order.get("input_file_bindings", []) or []
            if isinstance(binding, Mapping)
            and str(binding.get("role", "") or "")
            and str(binding.get("path", "") or "")
        }
        environment_tasks_path = input_paths.get("environment_repair_tasks")
        authoring_tasks_path = input_paths.get("followup_authoring_tasks")
        source_review_packets_path = input_paths.get("typechecked_review_packets")
        environment_tasks = _read_jsonl(environment_tasks_path)
        authoring_tasks = _read_jsonl(authoring_tasks_path)
        source_review_packets = _read_jsonl(source_review_packets_path)
        source_proof_body_rows = [
            dict(row)
            for row in work_order.get("source_proof_body_rows", []) or []
            if isinstance(row, Mapping)
        ]

        stage_manifests: dict[str, dict[str, Any]] = {}
        contract_errors: list[str] = []
        operational_feedback: list[str] = []
        tool_calls: list[ToolCallRecord] = []

        environment_manifest: dict[str, Any] = {}
        if environment_tasks and environment_tasks_path is not None:
            if self.review_execution_policy.get(
                "environment_preflight_enabled",
                False,
            ):
                stage_errors: list[str] = []
                environment_manifest = self._run_stage(
                    "environment_preflight",
                    stage_errors,
                    lambda: self.environment_runner(
                        out_dir=execution_dir / "environment_preflight",
                        environment_tasks_jsonl=environment_tasks_path,
                    ),
                )
                stage_errors.extend(
                    self._environment_errors(
                        environment_manifest,
                        source_path=environment_tasks_path,
                        expected_tasks=len(environment_tasks),
                    )
                )
                contract_errors.extend(stage_errors)
                tool_calls.append(
                    self._tool_call(
                        "ExactSemanticDefinitionReview.environment_preflight",
                        environment_tasks_path,
                        environment_manifest,
                        stage_errors,
                    )
                )
                if int(
                    environment_manifest.get(
                        "n_ready_to_rerun_lean_repair",
                        0,
                    )
                    or 0
                ) < len(environment_tasks):
                    operational_feedback.append(
                        "Lean project or dependency preflight remains unresolved"
                    )
            else:
                operational_feedback.append(
                    "Lean environment preflight is disabled for pending tasks"
                )

        authoring_manifest: dict[str, Any] = {}
        materializer_manifest: dict[str, Any] = {}
        materialized_repair_manifest: dict[str, Any] = {}
        authoring_model_expected = bool(
            authoring_tasks
            and self.authoring_enabled
            and self.authoring_provider is not None
            and not self.authoring_config.dry_run
        )
        if authoring_tasks and authoring_tasks_path is not None:
            if self.authoring_enabled and not contract_errors:
                stage_errors = []
                authoring_manifest = self._run_stage(
                    "semantic_review_authoring",
                    stage_errors,
                    lambda: self.authoring_runner(
                        out_dir=execution_dir / "semantic_review_authoring",
                        authoring_tasks_jsonl=authoring_tasks_path,
                        provider=self.authoring_provider,
                        config=self.authoring_config,
                    ),
                )
                stage_errors.extend(
                    ExactSemanticDefinitionRuntimeWorker._authoring_errors(
                        authoring_manifest,
                        authoring_tasks_path,
                        len(authoring_tasks),
                        model_attempt_required=authoring_model_expected,
                    )
                )
                contract_errors.extend(stage_errors)
                tool_calls.append(
                    self._tool_call(
                        "ExactSemanticDefinitionReview.semantic_review_model",
                        authoring_tasks_path,
                        authoring_manifest,
                        stage_errors,
                    )
                )
                if not authoring_model_expected:
                    operational_feedback.append(
                        "Pending semantic review has no configured live LLM attempt"
                    )
            else:
                operational_feedback.append(
                    "LLM semantic-review authoring is disabled for pending tasks"
                )

        authoring_manifest_path = str(authoring_manifest.get("manifest_path", "") or "")
        if (
            authoring_manifest
            and not contract_errors
            and int(authoring_manifest.get("n_candidate_packets", 0) or 0) > 0
        ):
            stage_errors = []
            materializer_manifest = self._run_stage(
                "semantic_review_materializer",
                stage_errors,
                lambda: self.materializer_runner(
                    out_dir=execution_dir / "semantic_review_materializer",
                    authoring_worker_manifest=Path(authoring_manifest_path),
                    config=self.materializer_config,
                ),
            )
            stage_errors.extend(
                ExactSemanticDefinitionRuntimeWorker._materializer_errors(
                    materializer_manifest,
                    authoring_manifest_path,
                    int(authoring_manifest.get("n_candidate_packets", 0) or 0),
                )
            )
            contract_errors.extend(stage_errors)
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinitionReview.candidate_materializer",
                    Path(authoring_manifest_path),
                    materializer_manifest,
                    stage_errors,
                )
            )

        materializer_manifest_path = str(
            materializer_manifest.get("manifest_path", "") or ""
        )
        if (
            materializer_manifest
            and not contract_errors
            and int(
                materializer_manifest.get(
                    "n_materialized_lean_repair_tasks",
                    0,
                )
                or 0
            )
            > 0
        ):
            stage_errors = []
            materialized_repair_manifest = self._run_stage(
                "semantic_review_lean_repair",
                stage_errors,
                lambda: self.lean_repair_runner(
                    out_dir=execution_dir / "semantic_review_lean_repair",
                    materializer_manifest=Path(materializer_manifest_path),
                    source_roots=self.source_roots,
                    local_lean=self.local_lean,
                    lean_project=self.lean_project,
                    lean_timeout=self.lean_timeout,
                ),
            )
            stage_errors.extend(
                ExactSemanticDefinitionRuntimeWorker._repair_errors(
                    self,
                    materialized_repair_manifest,
                    source_manifest_path=materializer_manifest_path,
                    source_key="source_materializer_manifest",
                    expected_tasks=int(
                        materializer_manifest.get(
                            "n_materialized_lean_repair_tasks",
                            0,
                        )
                        or 0
                    ),
                )
            )
            contract_errors.extend(stage_errors)
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinitionReview.local_lean_feedback",
                    Path(materializer_manifest_path),
                    materialized_repair_manifest,
                    stage_errors,
                )
            )

        review_packets_path = source_review_packets_path
        review_packets = source_review_packets
        if authoring_manifest:
            latest_review_path = str(
                materialized_repair_manifest.get(
                    "typechecked_candidate_review_packets_jsonl",
                    "",
                )
                or ""
            )
            review_packets_path = (
                Path(latest_review_path) if latest_review_path else None
            )
            review_packets = _read_jsonl(review_packets_path)
        if authoring_tasks and not authoring_manifest:
            review_packets_path = None
            review_packets = []

        direct_queue_manifest: dict[str, Any] = {}
        direct_queue_manifest_path: Path | None = None
        if review_packets and source_proof_body_rows and not contract_errors:
            direct_queue_manifest_path = (
                ExactSourceTheoremProofBodyRuntimeWorker._write_direct_execution_queue(
                    source_rows=source_proof_body_rows,
                    execution_dir=execution_dir / "bound_source_proof_body_queue",
                )
            )
            try:
                raw_direct_queue = json.loads(
                    direct_queue_manifest_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                contract_errors.append(
                    "bound source proof-body queue unreadable: "
                    f"{type(exc).__name__}: {exc}"
                )
            else:
                if isinstance(raw_direct_queue, Mapping):
                    direct_queue_manifest = dict(raw_direct_queue)
                    direct_queue_manifest["manifest_path"] = str(
                        direct_queue_manifest_path
                    )
                    contract_errors.extend(
                        self._direct_queue_errors(
                            direct_queue_manifest,
                            expected_rows=len(source_proof_body_rows),
                        )
                    )
                else:
                    contract_errors.append(
                        "bound source proof-body queue manifest is not an object"
                    )
        elif review_packets and not source_proof_body_rows:
            operational_feedback.append(
                "No hash-bound exact source theorem rows are available for recheck"
            )

        initial_recheck_manifest: dict[str, Any] = {}
        if (
            review_packets
            and review_packets_path is not None
            and direct_queue_manifest_path is not None
            and not contract_errors
        ):
            stage_errors = []
            initial_recheck_manifest = self._run_stage(
                "typechecked_review_recheck",
                stage_errors,
                lambda: self.recheck_runner(
                    out_dir=execution_dir / "typechecked_review_recheck",
                    review_packets_jsonl=review_packets_path,
                    proof_body_queue_manifest=direct_queue_manifest_path,
                ),
                transient_keys=("queue_jsonl",),
            )
            stage_errors.extend(
                self._recheck_errors(
                    initial_recheck_manifest,
                    review_packets_path=review_packets_path,
                    expected_review_packets=len(review_packets),
                    expected_source_rows=len(source_proof_body_rows),
                )
            )
            contract_errors.extend(stage_errors)
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinitionReview.semantic_recheck_queue",
                    review_packets_path,
                    initial_recheck_manifest,
                    stage_errors,
                )
            )

        verifier_manifest: dict[str, Any] = {}
        verifier_work_orders_path = Path(
            str(
                initial_recheck_manifest.get(
                    "verifier_gate_work_orders_jsonl",
                    "",
                )
                or ""
            )
        )
        n_verifier_work_orders = int(
            initial_recheck_manifest.get("n_verifier_gate_work_orders", 0) or 0
        )
        if (
            n_verifier_work_orders > 0
            and verifier_work_orders_path.exists()
            and not contract_errors
        ):
            stage_errors = []
            verifier_manifest = self._run_stage(
                "semantic_verifier_gate",
                stage_errors,
                lambda: self.verifier_runner(
                    out_dir=execution_dir / "semantic_verifier_gate",
                    work_orders_jsonl=verifier_work_orders_path,
                    local_lean=self.local_lean,
                    lean_project=self.lean_project,
                    lean_timeout=self.lean_timeout,
                ),
            )
            stage_errors.extend(
                self._verifier_errors(
                    verifier_manifest,
                    work_orders_path=verifier_work_orders_path,
                    expected_work_orders=n_verifier_work_orders,
                )
            )
            contract_errors.extend(stage_errors)
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinitionReview.semantic_verifier_gate",
                    verifier_work_orders_path,
                    verifier_manifest,
                    stage_errors,
                )
            )
            if int(verifier_manifest.get("n_verifier_approved", 0) or 0) < (
                n_verifier_work_orders
            ):
                operational_feedback.append(
                    "Semantic verifier gate returned compiler or source-anchor blockers"
                )

        approved_recheck_manifest: dict[str, Any] = {}
        approved_packets_path = Path(
            str(
                verifier_manifest.get(
                    "verifier_approved_review_packets_jsonl",
                    "",
                )
                or ""
            )
        )
        n_verifier_approved = int(verifier_manifest.get("n_verifier_approved", 0) or 0)
        if (
            n_verifier_approved > 0
            and approved_packets_path.exists()
            and direct_queue_manifest_path is not None
            and not contract_errors
        ):
            stage_errors = []
            approved_recheck_manifest = self._run_stage(
                "verifier_approved_recheck",
                stage_errors,
                lambda: self.recheck_runner(
                    out_dir=execution_dir / "verifier_approved_recheck",
                    review_packets_jsonl=approved_packets_path,
                    proof_body_queue_manifest=direct_queue_manifest_path,
                ),
                transient_keys=("queue_jsonl",),
            )
            stage_errors.extend(
                self._recheck_errors(
                    approved_recheck_manifest,
                    review_packets_path=approved_packets_path,
                    expected_review_packets=n_verifier_approved,
                    expected_source_rows=len(source_proof_body_rows),
                )
            )
            contract_errors.extend(stage_errors)
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinitionReview.verifier_approved_recheck",
                    approved_packets_path,
                    approved_recheck_manifest,
                    stage_errors,
                )
            )

        executor_manifest: dict[str, Any] = {}
        approved_recheck_manifest_path = Path(
            str(approved_recheck_manifest.get("manifest_path", "") or "")
        )
        n_proof_body_rows = int(
            approved_recheck_manifest.get("n_execution_queue_rows", 0) or 0
        )
        if n_proof_body_rows > 0 and not contract_errors:
            if self.review_execution_policy.get("proof_body_execute", False):
                stage_errors = []
                executor_manifest = self._run_executor_stage(
                    stage_errors,
                    lambda: self.proof_body_executor(
                        approved_recheck_manifest_path.parent,
                        out_dir=execution_dir / "exact_source_proof_body_executor",
                        overwrite=bool(
                            self.review_execution_policy.get(
                                "proof_body_overwrite",
                                False,
                            )
                        ),
                        local_lean=bool(
                            self.review_execution_policy.get(
                                "proof_body_local_lean",
                                False,
                            )
                        ),
                        lean_project=(
                            Path(
                                str(
                                    self.review_execution_policy.get(
                                        "proof_body_lean_project",
                                        "",
                                    )
                                    or ""
                                )
                            )
                            if str(
                                self.review_execution_policy.get(
                                    "proof_body_lean_project",
                                    "",
                                )
                                or ""
                            )
                            else None
                        ),
                        lean_timeout=int(
                            self.review_execution_policy.get(
                                "proof_body_lean_timeout",
                                90,
                            )
                            or 90
                        ),
                    ),
                )
                stage_errors.extend(
                    ExactSourceTheoremProofBodyRuntimeWorker._executor_errors(
                        executor_manifest=executor_manifest,
                        queue_manifest_path=approved_recheck_manifest_path,
                        local_lean=bool(
                            self.review_execution_policy.get(
                                "proof_body_local_lean",
                                False,
                            )
                        ),
                        executor_error="",
                    )
                )
                if (
                    int(executor_manifest.get("n_execution_result_rows", 0) or 0)
                    != n_proof_body_rows
                ):
                    stage_errors.append(
                        "exact proof-body executor/recheck row count mismatch"
                    )
                contract_errors.extend(stage_errors)
                tool_calls.append(
                    self._tool_call(
                        "ExactSemanticDefinitionReview.exact_source_proof_body",
                        approved_recheck_manifest_path,
                        executor_manifest,
                        stage_errors,
                    )
                )
            else:
                operational_feedback.append(
                    "Exact source proof-body execution is disabled after verifier approval"
                )

        raw_executor_rows = executor_manifest.get("rows", [])
        executor_rows = [
            dict(row) for row in raw_executor_rows if isinstance(row, Mapping)
        ]
        n_kernel_verified = sum(
            1
            for row in executor_rows
            if _bool_like(row.get("source_theorem_kernel_verified", False))
        )
        all_kernel_verified = bool(executor_rows) and all(
            _bool_like(row.get("source_theorem_kernel_verified", False))
            for row in executor_rows
        )
        all_kernel_verified = bool(
            all_kernel_verified
            and not contract_errors
            and len(executor_rows) == n_proof_body_rows
            and _bool_like(
                executor_manifest.get(
                    "all_source_theorems_kernel_verified",
                    False,
                )
            )
        )

        output_binding_rows = [
            row
            for manifest, path_keys in (
                (
                    authoring_manifest,
                    ("authoring_candidate_packets_jsonl",),
                ),
                (
                    materializer_manifest,
                    ("materialization_rows_jsonl",),
                ),
                (
                    materialized_repair_manifest,
                    (
                        "execution_results_jsonl",
                        "typechecked_candidate_review_packets_jsonl",
                    ),
                ),
                (
                    initial_recheck_manifest,
                    (
                        "proof_body_execution_queue_jsonl",
                        "blocked_review_packets_jsonl",
                    ),
                ),
                (
                    verifier_manifest,
                    (
                        "verifier_gate_results_jsonl",
                        "verifier_approved_review_packets_jsonl",
                    ),
                ),
                (
                    approved_recheck_manifest,
                    ("proof_body_execution_queue_jsonl",),
                ),
            )
            for path_key in path_keys
            for row in _read_jsonl(manifest.get(path_key, ""))
        ]
        output_binding_rows.extend(executor_rows)
        output_file_bindings = _candidate_file_bindings_from_rows(output_binding_rows)

        for stage, manifest in (
            ("environment_preflight", environment_manifest),
            ("semantic_review_authoring", authoring_manifest),
            ("semantic_review_materializer", materializer_manifest),
            ("semantic_review_lean_repair", materialized_repair_manifest),
            ("bound_source_proof_body_queue", direct_queue_manifest),
            ("typechecked_review_recheck", initial_recheck_manifest),
            ("semantic_verifier_gate", verifier_manifest),
            ("verifier_approved_recheck", approved_recheck_manifest),
            ("exact_source_proof_body_executor", executor_manifest),
        ):
            if manifest:
                artifact = _with_architect_control(
                    manifest,
                    work_order,
                    subsystem=EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
                )
                stage_manifests[_stage_artifact_id(stage, artifact)] = artifact

        if contract_errors:
            next_task = self._critic_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                feedback={
                    "failure_classification": (
                        "exact_semantic_definition_review_contract_invalid"
                    ),
                    "contract_errors": contract_errors,
                },
                source_theorem_kernel_verified=False,
            )
            result_status = "REROUTE"
            failure_classification = "exact_semantic_definition_review_contract_invalid"
        elif all_kernel_verified:
            next_task = self._critic_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                feedback={
                    "failure_classification": (
                        "exact_source_theorem_kernel_verified_after_semantic_review"
                    ),
                    "exact_source_proof_body_executor_manifest_id": (
                        self._stage_id_for(
                            "exact_source_proof_body_executor",
                            stage_manifests,
                        )
                    ),
                    "n_source_theorem_kernel_verified": n_kernel_verified,
                },
                source_theorem_kernel_verified=True,
            )
            result_status = "REROUTE"
            failure_classification = (
                "exact_source_theorem_kernel_verified_after_semantic_review"
            )
        elif self.repair_available:
            next_task = self._repair_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                feedback=self._feedback_payload(
                    stage_manifests=stage_manifests,
                    operational_feedback=operational_feedback,
                    materialized_repair_manifest=materialized_repair_manifest,
                    initial_recheck_manifest=initial_recheck_manifest,
                    verifier_manifest=verifier_manifest,
                    executor_manifest=executor_manifest,
                ),
            )
            result_status = "REVISE"
            failure_classification = "exact_semantic_definition_review_feedback_ready"
        else:
            next_task = self._critic_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                feedback=self._feedback_payload(
                    stage_manifests=stage_manifests,
                    operational_feedback=operational_feedback,
                    materialized_repair_manifest=materialized_repair_manifest,
                    initial_recheck_manifest=initial_recheck_manifest,
                    verifier_manifest=verifier_manifest,
                    executor_manifest=executor_manifest,
                ),
                source_theorem_kernel_verified=False,
            )
            result_status = "REROUTE"
            failure_classification = "exact_semantic_definition_review_feedback_ready"

        proof_status = (
            SOURCE_KERNEL_STATUS if all_kernel_verified else REVIEW_FEEDBACK_STATUS
        )
        execution_manifest = _with_architect_control(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": EXACT_SEMANTIC_DEFINITION_REVIEW_EXECUTION_KIND,
                "manifest_id": execution_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question_id": question_id,
                "task_id": task.task_id,
                "work_order_id": work_order_id,
                "work_order_hash": expected_work_order_hash,
                "parent_work_order_id": str(
                    work_order.get("parent_work_order_id", "") or ""
                ),
                "parent_work_order_hash": str(
                    work_order.get("parent_work_order_hash", "") or ""
                ),
                "source_formalization_manifest_id": str(
                    work_order.get("source_formalization_manifest_id", "") or ""
                ),
                "source_formalization_manifest_hash": str(
                    work_order.get("source_formalization_manifest_hash", "") or ""
                ),
                "source_repair_manifest_id": str(
                    work_order.get("source_repair_manifest_id", "") or ""
                ),
                "source_repair_manifest_hash": str(
                    work_order.get("source_repair_manifest_hash", "") or ""
                ),
                "source_proof_body_row_hashes": list(
                    work_order.get("source_proof_body_row_hashes", []) or []
                ),
                "review_execution_policy_fingerprint": policy_fingerprint,
                "stage_artifact_ids": list(stage_manifests),
                "stage_artifact_hashes": {
                    artifact_id: stable_hash(artifact)
                    for artifact_id, artifact in stage_manifests.items()
                },
                "output_file_bindings": output_file_bindings,
                "n_environment_tasks": len(environment_tasks),
                "n_authoring_tasks": len(authoring_tasks),
                "authoring_model_expected": authoring_model_expected,
                "authoring_model_invoked": int(
                    authoring_manifest.get("n_llm_attempted", 0) or 0
                )
                > 0,
                "authoring_live_model_invoked": int(
                    authoring_manifest.get("n_live_llm_attempted", 0) or 0
                )
                > 0,
                "n_review_packets": len(review_packets),
                "n_verifier_gate_work_orders": n_verifier_work_orders,
                "n_verifier_approved": n_verifier_approved,
                "n_proof_body_execution_rows": len(executor_rows),
                "n_source_theorem_kernel_verified": n_kernel_verified,
                "source_theorem_kernel_verified": all_kernel_verified,
                "semantic_definition_verifier_approved": bool(
                    n_verifier_approved > 0
                    and n_verifier_approved == n_verifier_work_orders
                ),
                "runtime_generated_lean": False,
                "python_lean_grammar_generation_or_repair": False,
                "operational_feedback": operational_feedback,
                "contract_errors": contract_errors,
                "execution_contract_satisfied": not contract_errors,
                "proof_evidence_status": proof_status,
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                "resume_next_task": asdict(next_task),
                "execution_result_status": result_status,
                "execution_failure_classification": failure_classification,
            },
            work_order,
            subsystem=EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
        )
        execution_manifest["execution_replay_fingerprint"] = (
            _execution_replay_fingerprint(execution_manifest)
        )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:"
            + stable_hash([task.task_id, execution_id, proof_status])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type=(
                "exact_source_theorem_kernel_verification"
                if all_kernel_verified
                else "exact_semantic_definition_review_feedback"
            ),
            status=proof_status,
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "n_verifier_approved": n_verifier_approved,
                "n_source_theorem_kernel_verified": n_kernel_verified,
                "source_theorem_kernel_verified": all_kernel_verified,
                "runtime_generated_lean": False,
                "python_lean_grammar_generation_or_repair": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "The exact preserved source theorem passed the verifier-approved "
                "semantic continuation and local Lean/kernel proof-body gate."
                if all_kernel_verified
                else "The typed semantic-review child returned exact LLM, source, "
                "verifier, and compiler feedback without promoting non-proof evidence."
            ),
            produced_artifacts={execution_id: execution_manifest, **stage_manifests},
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "exact_source_theorem_kernel_verified"
                        if all_kernel_verified
                        else "exact_semantic_definition_review_feedback"
                    ),
                    summary=(
                        f"review_packets={len(review_packets)} "
                        f"verifier_approved={n_verifier_approved} "
                        f"kernel_verified={n_kernel_verified} "
                        f"contract_errors={len(contract_errors)}"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "stage_artifact_ids": list(stage_manifests),
                        "proof_evidence_status": proof_status,
                        "source_theorem_kernel_verified": all_kernel_verified,
                    },
                ),
            ),
            tool_calls=tuple(tool_calls),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=failure_classification,
        )

    def _work_order_errors(
        self,
        *,
        question_id: str,
        work_order_id: str,
        expected_work_order_hash: str,
        work_order: Mapping[str, Any],
        blackboard: BlackboardState,
    ) -> list[str]:
        errors: list[str] = []
        if not question_id:
            errors.append("question id missing")
        if not work_order_id:
            errors.append("review work_order_id missing")
        if str(work_order.get("artifact_kind", "") or "") != (
            EXACT_SEMANTIC_DEFINITION_REVIEW_WORK_ORDER_KIND
        ):
            errors.append("review work-order artifact_kind mismatch")
        if str(work_order.get("work_order_id", "") or "") != work_order_id:
            errors.append("review work-order identity mismatch")
        if not expected_work_order_hash or stable_hash(dict(work_order)) != (
            expected_work_order_hash
        ):
            errors.append("immutable review work-order hash mismatch")
        if str(work_order.get("question_id", "") or "") != question_id:
            errors.append("review work-order question_id mismatch")
        if str(work_order.get("target_subsystem", "") or "") != self.name:
            errors.append("review work-order target_subsystem mismatch")

        parent_id = str(work_order.get("parent_work_order_id", "") or "")
        raw_parent = blackboard.artifacts.get(parent_id, {})
        parent = dict(raw_parent) if isinstance(raw_parent, Mapping) else {}
        if not parent:
            errors.append("parent exact-semantic work order missing")
        else:
            if str(parent.get("artifact_kind", "") or "") != (
                EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_KIND
            ):
                errors.append("parent exact-semantic artifact_kind mismatch")
            if stable_hash(parent) != str(
                work_order.get("parent_work_order_hash", "") or ""
            ):
                errors.append("parent exact-semantic work-order hash mismatch")
            if str(parent.get("question_id", "") or "") != question_id:
                errors.append("parent exact-semantic question_id mismatch")

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
            errors.append("source formalization manifest missing")
        elif stable_hash(source_manifest) != str(
            work_order.get("source_formalization_manifest_hash", "") or ""
        ):
            errors.append("source formalization manifest hash mismatch")
        if parent and source_manifest_id != str(
            parent.get("source_formalization_manifest_id", "") or ""
        ):
            errors.append("parent/source formalization manifest identity mismatch")

        stage_ids = [
            str(value)
            for value in work_order.get("source_stage_artifact_ids", []) or []
        ]
        stage_hashes_raw = work_order.get("source_stage_artifact_hashes", {})
        stage_hashes = (
            dict(stage_hashes_raw) if isinstance(stage_hashes_raw, Mapping) else {}
        )
        if stage_ids != list(stage_hashes):
            errors.append("source stage artifact identity/hash coverage mismatch")
        for artifact_id in stage_ids:
            raw_artifact = blackboard.artifacts.get(artifact_id, {})
            if not isinstance(raw_artifact, Mapping):
                errors.append("source stage artifact missing")
                continue
            if stable_hash(dict(raw_artifact)) != str(
                stage_hashes.get(artifact_id, "") or ""
            ):
                errors.append("source stage artifact hash mismatch")

        source_repair_id = str(work_order.get("source_repair_manifest_id", "") or "")
        raw_source_repair = blackboard.artifacts.get(source_repair_id, {})
        source_repair = (
            dict(raw_source_repair) if isinstance(raw_source_repair, Mapping) else {}
        )
        if not source_repair_id or source_repair_id not in stage_hashes:
            errors.append("source repair manifest is not stage-bound")
        if not source_repair:
            errors.append("source repair manifest missing")
        elif stable_hash(source_repair) != str(
            work_order.get("source_repair_manifest_hash", "") or ""
        ):
            errors.append("source repair manifest hash mismatch")

        path_fields = {
            "followup_authoring_tasks": (
                "exact_semantic_definition_authoring_tasks_jsonl"
            ),
            "environment_repair_tasks": "lean_environment_repair_tasks_jsonl",
            "typechecked_review_packets": (
                "typechecked_candidate_review_packets_jsonl"
            ),
        }
        expected_bindings = [
            _bound_text_file(
                source_repair.get(source_key, ""),
                role=role,
            )
            for role, source_key in path_fields.items()
            if str(source_repair.get(source_key, "") or "").strip()
        ]
        observed_bindings = [
            dict(binding)
            for binding in work_order.get("input_file_bindings", []) or []
            if isinstance(binding, Mapping)
        ]
        if observed_bindings != expected_bindings:
            errors.append("review input file bindings changed or lack producer lineage")
        input_rows = [
            row
            for binding in observed_bindings
            for row in _read_jsonl(binding.get("path", ""))
        ]
        if not input_rows:
            errors.append("review work order contains no continuation rows")
        for row in input_rows:
            row_question_id = str(row.get("question_id", "") or "")
            if row_question_id and row_question_id != question_id:
                errors.append("review continuation row question_id mismatch")
        expected_candidate_bindings = _candidate_file_bindings_from_rows(input_rows)
        observed_candidate_bindings = [
            dict(binding)
            for binding in work_order.get("candidate_artifact_bindings", []) or []
            if isinstance(binding, Mapping)
        ]
        if observed_candidate_bindings != expected_candidate_bindings:
            errors.append("review candidate artifact binding mismatch")

        source_rows = [
            dict(row)
            for row in work_order.get("source_proof_body_rows", []) or []
            if isinstance(row, Mapping)
        ]
        expected_source_rows = (
            self.source_proof_body_rows_resolver(source_manifest)
            if source_manifest
            else []
        )
        if source_rows != expected_source_rows:
            errors.append("source proof-body rows differ from manifest projection")
        if list(work_order.get("source_proof_body_row_hashes", []) or []) != [
            stable_hash(row) for row in source_rows
        ]:
            errors.append("source proof-body row hashes mismatch")
        if [
            dict(binding)
            for binding in work_order.get(
                "source_proof_body_candidate_bindings",
                [],
            )
            or []
            if isinstance(binding, Mapping)
        ] != _source_candidate_bindings(source_rows):
            errors.append("source proof-body candidate binding mismatch")
        for row in source_rows:
            if str(row.get("question_id", "") or "") != question_id:
                errors.append("source proof-body row question_id mismatch")
            if _bool_like(row.get("source_theorem_kernel_verified", False)):
                errors.append("already verified source theorem entered review loop")

        policy = (
            dict(work_order.get("review_execution_policy", {}))
            if isinstance(
                work_order.get("review_execution_policy", {}),
                Mapping,
            )
            else {}
        )
        if not policy or stable_hash(policy) != str(
            work_order.get("review_execution_policy_fingerprint", "") or ""
        ):
            errors.append("review execution policy fingerprint mismatch")
        if policy != self.review_execution_policy:
            errors.append("review execution policy differs from registered worker")
        if policy.get("authoring_enabled") is not self.authoring_enabled:
            errors.append("review authoring policy mismatch")
        if str(policy.get("authoring_config_fingerprint", "") or "") != (
            stable_hash(asdict(self.authoring_config))
        ):
            errors.append("review authoring config fingerprint mismatch")
        if str(policy.get("materializer_config_fingerprint", "") or "") != (
            stable_hash(asdict(self.materializer_config))
        ):
            errors.append("review materializer config fingerprint mismatch")
        if policy.get("local_lean") is not self.local_lean:
            errors.append("review local Lean policy mismatch")
        if str(policy.get("lean_project", "") or "") != str(self.lean_project or ""):
            errors.append("review Lean project mismatch")
        if int(policy.get("lean_timeout", 0) or 0) != self.lean_timeout:
            errors.append("review Lean timeout mismatch")
        if _bool_like(work_order.get("runtime_generated_lean", False)):
            errors.append("review work order claims runtime-generated Lean")
        if _bool_like(
            work_order.get("python_lean_grammar_generation_or_repair", False)
        ):
            errors.append("review work order enables Python Lean grammar repair")
        if _bool_like(work_order.get("source_theorem_kernel_verified", False)):
            errors.append("review work order claimed source-theorem proof")
        try:
            _task_from_payload(
                work_order.get("source_task", {})
                if isinstance(work_order.get("source_task", {}), Mapping)
                else {}
            )
        except ValueError as exc:
            errors.append(f"review source task invalid: {exc}")
        try:
            return_task = _task_from_payload(
                work_order.get("return_task", {})
                if isinstance(work_order.get("return_task", {}), Mapping)
                else {}
            )
        except ValueError as exc:
            errors.append(f"review return task invalid: {exc}")
        else:
            if return_task.owner_subsystem != "CriticEvaluator":
                errors.append("review return task is not CriticEvaluator-owned")
        return list(dict.fromkeys(errors))

    @staticmethod
    def _run_stage(
        stage: str,
        errors: list[str],
        runner: Callable[[], Mapping[str, Any]],
        *,
        transient_keys: Sequence[str] = (),
    ) -> dict[str, Any]:
        try:
            raw_manifest = runner()
            if not isinstance(raw_manifest, Mapping):
                raise TypeError(f"{stage} runner must return a mapping")
            manifest = dict(raw_manifest)
            manifest_path_text = str(manifest.get("manifest_path", "") or "")
            if not manifest_path_text:
                errors.append(f"{stage}: persisted manifest path missing")
                return manifest
            try:
                persisted = json.loads(
                    Path(manifest_path_text).read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(
                    f"{stage}: persisted manifest unreadable: "
                    f"{type(exc).__name__}: {exc}"
                )
                return manifest
            expected = dict(manifest)
            expected.pop("manifest_path", None)
            for key in transient_keys:
                expected.pop(str(key), None)
            if not isinstance(persisted, Mapping) or stable_hash(
                dict(persisted)
            ) != stable_hash(expected):
                errors.append(f"{stage}: persisted manifest content mismatch")
            return manifest
        except Exception as exc:
            errors.append(f"{stage}: {type(exc).__name__}: {exc}")
            return {}

    @staticmethod
    def _run_executor_stage(
        errors: list[str],
        runner: Callable[[], Mapping[str, Any]],
    ) -> dict[str, Any]:
        try:
            raw_manifest = runner()
            if not isinstance(raw_manifest, Mapping):
                raise TypeError("proof-body executor runner must return a mapping")
            manifest = dict(raw_manifest)
            manifest_path_text = str(
                manifest.get("execution_result_manifest", "") or ""
            ).strip()
            if not manifest_path_text:
                errors.append("proof-body executor persisted manifest missing")
                return manifest
            manifest_path = Path(manifest_path_text)
            if not manifest_path.is_file():
                errors.append("proof-body executor persisted manifest missing")
                return manifest
            persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(persisted, Mapping) or stable_hash(
                dict(persisted)
            ) != stable_hash(manifest):
                errors.append("proof-body executor persisted manifest mismatch")
            return manifest
        except Exception as exc:
            errors.append(f"proof_body_executor: {type(exc).__name__}: {exc}")
            return {}

    @staticmethod
    def _environment_errors(
        manifest: Mapping[str, Any],
        *,
        source_path: Path,
        expected_tasks: int,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != ENVIRONMENT_ARTIFACT_KIND:
            errors.append("environment preflight artifact_kind mismatch")
        if not _same_path(
            manifest.get("source_environment_tasks_jsonl", ""),
            source_path,
        ):
            errors.append("environment preflight task lineage mismatch")
        if int(manifest.get("n_tasks", 0) or 0) != expected_tasks:
            errors.append("environment preflight task count mismatch")
        if int(manifest.get("n_results", 0) or 0) != expected_tasks:
            errors.append("environment preflight result count mismatch")
        if str(manifest.get("proof_evidence_status", "") or "") != (
            ENVIRONMENT_PROOF_STATUS
        ):
            errors.append("environment preflight proof boundary mismatch")
        if _bool_like(manifest.get("source_theorem_kernel_verified", False)):
            errors.append("environment preflight claimed source-theorem proof")
        return errors

    @staticmethod
    def _direct_queue_errors(
        manifest: Mapping[str, Any],
        *,
        expected_rows: int,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != (
            "ExactSourceTheoremProofBodyExecutionQueueManifest"
        ):
            errors.append("bound source proof-body queue artifact_kind mismatch")
        if int(manifest.get("n_execution_queue_rows", 0) or 0) != expected_rows:
            errors.append("bound source proof-body queue row count mismatch")
        if manifest.get("runtime_generated_lean") is not False:
            errors.append("bound source proof-body queue generated Lean in runtime")
        if manifest.get("python_lean_parsing_or_rewrite") is not False:
            errors.append("bound source proof-body queue rewrote Lean in Python")
        rows = [
            dict(row)
            for row in manifest.get("rows", []) or []
            if isinstance(row, Mapping)
        ]
        if len(rows) != expected_rows:
            errors.append("bound source proof-body queue embedded row mismatch")
        return errors

    @staticmethod
    def _recheck_errors(
        manifest: Mapping[str, Any],
        *,
        review_packets_path: Path,
        expected_review_packets: int,
        expected_source_rows: int,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != RECHECK_ARTIFACT_KIND:
            errors.append("typechecked review recheck artifact_kind mismatch")
        if not _same_path(
            manifest.get("source_review_packets_jsonl", ""),
            review_packets_path,
        ):
            errors.append("typechecked review packet lineage mismatch")
        if int(manifest.get("n_review_packets", 0) or 0) != (expected_review_packets):
            errors.append("typechecked review packet count mismatch")
        if int(manifest.get("n_source_proof_body_rows", 0) or 0) != (
            expected_source_rows
        ):
            errors.append("typechecked recheck source proof-body count mismatch")
        if str(manifest.get("proof_evidence_status", "") or "") != (
            TYPECHECKED_REVIEW_RECHECK_QUEUE_PROOF_EVIDENCE_STATUS
        ):
            errors.append("typechecked review recheck proof boundary mismatch")
        if _bool_like(manifest.get("source_theorem_kernel_verified", False)):
            errors.append("typechecked review recheck claimed source-theorem proof")
        if _bool_like(manifest.get("source_theorem_kernel_evidence_eligible", False)):
            errors.append("typechecked review recheck claimed kernel eligibility")
        return errors

    def _verifier_errors(
        self,
        manifest: Mapping[str, Any],
        *,
        work_orders_path: Path,
        expected_work_orders: int,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != VERIFIER_ARTIFACT_KIND:
            errors.append("semantic verifier artifact_kind mismatch")
        if not _same_path(
            manifest.get("source_verifier_gate_work_orders_jsonl", ""),
            work_orders_path,
        ):
            errors.append("semantic verifier work-order lineage mismatch")
        if int(manifest.get("n_work_orders", 0) or 0) != expected_work_orders:
            errors.append("semantic verifier work-order count mismatch")
        if int(manifest.get("n_results", 0) or 0) != expected_work_orders:
            errors.append("semantic verifier result count mismatch")
        if manifest.get("local_lean_requested") is not self.local_lean:
            errors.append("semantic verifier local Lean policy mismatch")
        if str(manifest.get("proof_evidence_status", "") or "") != (
            VERIFIER_PROOF_STATUS
        ):
            errors.append("semantic verifier proof boundary mismatch")
        if _bool_like(manifest.get("source_theorem_kernel_verified", False)):
            errors.append("semantic verifier claimed source-theorem proof")
        if _bool_like(manifest.get("source_theorem_kernel_evidence_eligible", False)):
            errors.append("semantic verifier claimed source theorem eligibility")
        return errors

    @staticmethod
    def _tool_call(
        tool_name: str,
        input_path: Path,
        manifest: Mapping[str, Any],
        errors: Sequence[str],
    ) -> ToolCallRecord:
        output_paths = tuple(
            value
            for value in (
                str(manifest.get("manifest_path", "") or ""),
                str(manifest.get("execution_result_manifest", "") or ""),
                str(manifest.get("runtime_learning_rows_jsonl", "") or ""),
                str(manifest.get("execution_results_jsonl", "") or ""),
            )
            if value
        )
        return ToolCallRecord(
            tool_name=tool_name,
            inputs={"input_path": str(input_path)},
            output_paths=output_paths,
            exit_status="0" if manifest and not errors else "contract_feedback",
            stdout_summary=(
                f"artifact_kind={manifest.get('artifact_kind', '')} "
                f"contract_errors={len(errors)}"
            ),
            safety_boundary=KERNEL_PROOF_BOUNDARY,
        )

    @staticmethod
    def _stage_id_for(
        stage: str,
        stage_manifests: Mapping[str, Mapping[str, Any]],
    ) -> str:
        prefix = f"runtime_exact_semantic_definition_review_{stage}:"
        return next(
            (
                artifact_id
                for artifact_id in stage_manifests
                if artifact_id.startswith(prefix)
            ),
            "",
        )

    def _feedback_payload(
        self,
        *,
        stage_manifests: Mapping[str, Mapping[str, Any]],
        operational_feedback: Sequence[str],
        materialized_repair_manifest: Mapping[str, Any],
        initial_recheck_manifest: Mapping[str, Any],
        verifier_manifest: Mapping[str, Any],
        executor_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "failure_classification": (
                "exact_semantic_definition_review_feedback_ready"
            ),
            "stage_artifact_ids": list(stage_manifests),
            "operational_feedback": list(operational_feedback),
            "lean_repair_execution_results": _read_jsonl(
                materialized_repair_manifest.get("execution_results_jsonl", "")
            )[:12],
            "semantic_review_blocked_packets": _read_jsonl(
                initial_recheck_manifest.get("blocked_review_packets_jsonl", "")
            )[:12],
            "verifier_gate_results": _read_jsonl(
                verifier_manifest.get("verifier_gate_results_jsonl", "")
            )[:12],
            "proof_body_execution_results": [
                dict(row)
                for row in executor_manifest.get("rows", []) or []
                if isinstance(row, Mapping)
            ][:12],
            "source_theorem_kernel_verified": False,
            "candidate_generation_contract": (
                "Use the LLM coding agent with the bound source context and exact "
                "Lean diagnostics. Preserve the source target and candidate bytes; "
                "Python does not synthesize Lean grammar or tactics."
            ),
        }

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
        prior_feedback["exact_semantic_definition_review_execution_id"] = execution_id
        prior_feedback["repair_owner_agent"] = "ProofEngineer"
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
                f"proofengineer-exact-semantic-review:{question_id}:"
                f"{stable_hash(execution_id)[:8]}"
            ),
            owner_subsystem="ProofEngineer",
            inputs=inputs,
        )

    @staticmethod
    def _critic_task(
        work_order: Mapping[str, Any],
        *,
        question_id: str,
        execution_id: str,
        feedback: Mapping[str, Any],
        source_theorem_kernel_verified: bool,
    ) -> AgentTask:
        base = _task_from_payload(
            work_order.get("return_task", {})
            if isinstance(work_order.get("return_task", {}), Mapping)
            else {}
        )
        inputs = dict(base.inputs)
        inputs["exact_semantic_definition_review_feedback"] = {
            **dict(feedback),
            "execution_id": execution_id,
            "source_theorem_kernel_verified": bool(source_theorem_kernel_verified),
        }
        return replace(
            base,
            task_id=(
                f"critic-exact-semantic-review:{question_id}:"
                f"{stable_hash(execution_id)[:8]}"
            ),
            inputs=inputs,
        )

    def _replay(
        self,
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
        raw_execution = blackboard.artifacts.get(execution_id, {})
        execution = dict(raw_execution) if isinstance(raw_execution, Mapping) else {}
        errors: list[str] = []
        if str(execution.get("artifact_kind", "") or "") != (
            EXACT_SEMANTIC_DEFINITION_REVIEW_EXECUTION_KIND
        ):
            errors.append("existing review execution artifact_kind mismatch")
        if str(execution.get("manifest_id", "") or "") != execution_id:
            errors.append("existing review execution identity mismatch")
        if str(execution.get("question_id", "") or "") != question_id:
            errors.append("existing review execution question_id mismatch")
        if str(execution.get("task_id", "") or "") != task.task_id:
            errors.append("existing review execution task_id mismatch")
        if str(execution.get("work_order_id", "") or "") != work_order_id:
            errors.append("existing review execution work-order mismatch")
        if str(execution.get("work_order_hash", "") or "") != work_order_hash:
            errors.append("existing review execution work-order hash mismatch")
        if (
            str(execution.get("review_execution_policy_fingerprint", "") or "")
            != policy_fingerprint
        ):
            errors.append("existing review execution policy mismatch")
        if str(execution.get("execution_replay_fingerprint", "") or "") != (
            _execution_replay_fingerprint(execution)
        ):
            errors.append("existing review execution replay fingerprint mismatch")
        stage_hashes_raw = execution.get("stage_artifact_hashes", {})
        stage_hashes = (
            dict(stage_hashes_raw) if isinstance(stage_hashes_raw, Mapping) else {}
        )
        if not stage_hashes:
            errors.append("existing review execution stage hashes missing")
        for artifact_id, expected_hash in stage_hashes.items():
            raw_artifact = blackboard.artifacts.get(str(artifact_id), {})
            if not isinstance(raw_artifact, Mapping):
                errors.append("existing review execution stage artifact missing")
            elif stable_hash(dict(raw_artifact)) != str(expected_hash or ""):
                errors.append("existing review execution stage hash mismatch")
        output_bindings = execution.get("output_file_bindings", [])
        if not isinstance(output_bindings, Sequence) or isinstance(
            output_bindings,
            (str, bytes),
        ):
            errors.append("existing review execution output bindings invalid")
        else:
            for raw_binding in output_bindings:
                if not isinstance(raw_binding, Mapping):
                    errors.append(
                        "existing review execution output binding is not an object"
                    )
                    continue
                binding = dict(raw_binding)
                observed = _bound_text_file(
                    binding.get("path", ""),
                    role=str(binding.get("role", "") or ""),
                )
                if observed != binding:
                    errors.append(
                        "existing review execution output file binding mismatch"
                    )
        try:
            next_task = _task_from_payload(
                execution.get("resume_next_task", {})
                if isinstance(execution.get("resume_next_task", {}), Mapping)
                else {}
            )
        except ValueError as exc:
            errors.append(f"existing review resume task invalid: {exc}")
            next_task = None
        if errors or next_task is None:
            return self._blocked_result(
                task=task,
                work_order_id=work_order_id,
                errors=errors,
                failure_classification=(
                    "exact_semantic_definition_review_execution_replay_invalid"
                ),
            )
        return AgentStepResult(
            status=str(execution.get("execution_result_status", "") or "REROUTE"),
            rationale=(
                "Replayed the persisted exact-semantic review execution without "
                "repeating model, verifier, or Lean calls."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "exact_semantic_definition_review_execution_replayed"
                    ),
                    summary=f"replayed execution {execution_id}",
                    payload={
                        "execution_id": execution_id,
                        "execution_replayed": True,
                        "coding_agent_or_compiler_reexecuted": False,
                        "proof_evidence_status": str(
                            execution.get("proof_evidence_status", "") or ""
                        ),
                    },
                ),
            ),
            next_task=next_task,
            failure_classification=str(
                execution.get("execution_failure_classification", "") or ""
            ),
        )

    @staticmethod
    def _blocked_result(
        *,
        task: AgentTask,
        work_order_id: str,
        errors: Sequence[str],
        failure_classification: str,
    ) -> AgentStepResult:
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:"
            + stable_hash([task.task_id, work_order_id, list(errors)])[:20],
            task_id=task.task_id,
            artifact_id=work_order_id,
            evidence_type="exact_semantic_definition_review_rejection",
            status=(
                "EXACT_SEMANTIC_DEFINITION_REVIEW_INPUT_REJECTED_NOT_PROOF_EVIDENCE"
            ),
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={"validation_errors": list(errors)},
        )
        return AgentStepResult(
            status="BLOCKED",
            rationale=(
                "ExactSemanticDefinitionReviewProofEngineer rejected changed, "
                "cross-task, or unbound inputs before model or Lean execution."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type=(
                        "exact_semantic_definition_review_runtime_rejected"
                    ),
                    summary="; ".join(str(value) for value in errors)[:500],
                    payload={
                        "work_order_id": work_order_id,
                        "validation_errors": list(errors),
                        "proof_evidence_status": evidence.status,
                    },
                ),
            ),
            evidence_entries=(evidence,),
            failure_classification=failure_classification,
        )
