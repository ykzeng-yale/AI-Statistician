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
from .model_backend import GeneratorBackend
from .research_architect import KERNEL_PROOF_BOUNDARY
from .source_theorem_exact_semantic_definition_authoring_worker import (
    ARTIFACT_KIND as AUTHORING_ARTIFACT_KIND,
    MATERIALIZER_ARTIFACT_KIND,
    AuthoringCandidateMaterializerConfig,
    AuthoringWorkerConfig,
    run_source_theorem_exact_semantic_definition_authoring_candidate_materializer,
    run_source_theorem_exact_semantic_definition_authoring_worker,
)
from .source_theorem_exact_semantic_definition_lean_repair_executor import (
    ARTIFACT_KIND as LEAN_REPAIR_ARTIFACT_KIND,
    run_source_theorem_exact_semantic_definition_lean_repair_executor,
)
from .source_theorem_exact_semantic_definition_proofengineer_bridge import (
    ARTIFACT_KIND as BRIDGE_ARTIFACT_KIND,
    run_source_theorem_exact_semantic_definition_proofengineer_bridge,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    ARTIFACT_KIND as SOURCE_LOOKUP_ARTIFACT_KIND,
    run_source_theorem_exact_semantic_definition_source_lookup,
)


RUNTIME_SCHEMA_VERSION = 1
EXACT_SEMANTIC_DEFINITION_SUBSYSTEM = "ExactSemanticDefinitionProofEngineer"
EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_KIND = (
    "RuntimeExactSemanticDefinitionProofEngineerWorkOrder"
)
EXACT_SEMANTIC_DEFINITION_RUNTIME_EXECUTION_KIND = (
    "RuntimeExactSemanticDefinitionProofEngineerExecutionManifest"
)
EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM = (
    "ExactSemanticDefinitionReviewProofEngineer"
)
EXACT_SEMANTIC_DEFINITION_REVIEW_WORK_ORDER_KIND = (
    "RuntimeExactSemanticDefinitionReviewWorkOrder"
)
EXACT_SEMANTIC_DEFINITION_REVIEW_EXECUTION_KIND = (
    "RuntimeExactSemanticDefinitionReviewExecutionManifest"
)
SOURCE_GROUNDED_AUTHORING_COUNT_KEY = (
    "n_prompt_packets_with_source_grounded_authoring_handoff"
)


SourceRowsResolver = Callable[[Mapping[str, Any]], list[dict[str, Any]]]
SourceLookupRunner = Callable[..., Mapping[str, Any]]
BridgeRunner = Callable[..., Mapping[str, Any]]
LeanRepairRunner = Callable[..., Mapping[str, Any]]
AuthoringRunner = Callable[..., Mapping[str, Any]]
MaterializerRunner = Callable[..., Mapping[str, Any]]


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
        "".join(json.dumps(dict(row), sort_keys=True, default=str) + "\n" for row in rows),
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


def _same_path(left: Any, right: Any) -> bool:
    left_text = str(left or "").strip()
    right_text = str(right or "").strip()
    if not left_text or not right_text:
        return False
    try:
        return Path(left_text).resolve() == Path(right_text).resolve()
    except OSError:
        return False


def _with_architect_control(
    artifact: Mapping[str, Any],
    work_order: Mapping[str, Any],
    *,
    subsystem: str = EXACT_SEMANTIC_DEFINITION_SUBSYSTEM,
) -> dict[str, Any]:
    payload = dict(artifact)
    raw_control = work_order.get("runtime_architect_control", {})
    if isinstance(raw_control, Mapping) and raw_control:
        control = dict(raw_control)
        control["subsystem"] = subsystem
        payload["runtime_architect_control"] = control
    return payload


def _bound_text_file(path_value: Any, *, role: str) -> dict[str, Any]:
    path_text = str(path_value or "").strip()
    if not path_text:
        return {
            "role": role,
            "path": "",
            "present": False,
            "content_hash": "",
            "utf8_bytes": 0,
        }
    path = Path(path_text)
    try:
        source = path.read_bytes()
        present = True
    except OSError:
        source = b""
        present = False
    return {
        "role": role,
        "path": path_text,
        "present": present,
        "content_hash": (
            stable_hash(source.decode("utf-8", errors="replace"))
            if present
            else ""
        ),
        "utf8_bytes": len(source),
    }


def _candidate_file_bindings_from_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    path_keys = (
        "candidate_artifact_path",
        "definition_only_candidate_artifact_path",
        "candidate_source_file",
        "signature_probe_artifact_path",
        "source_theorem_signature_probe_artifact_path",
        "proof_body_signature_probe_artifact_path",
    )
    bindings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        containers = [row]
        for key in (
            "candidate_definition_request",
            "source_theorem_exact_semantic_definition_typechecked_candidate",
        ):
            value = row.get(key, {})
            if isinstance(value, Mapping):
                containers.append(value)
        for container in containers:
            for key in path_keys:
                path_text = str(container.get(key, "") or "").strip()
                marker = (key, path_text)
                if not path_text or marker in seen:
                    continue
                seen.add(marker)
                bindings.append(_bound_text_file(path_text, role=key))
    return bindings


def _stage_artifact_id(stage: str, manifest: Mapping[str, Any]) -> str:
    return f"runtime_exact_semantic_definition_{stage}:" + stable_hash(manifest)[:20]


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
                "source_lookup_manifest_hash",
                "proofengineer_bridge_manifest_hash",
                "initial_lean_repair_manifest_hash",
                "authoring_worker_manifest_hash",
                "candidate_materializer_manifest_hash",
                "materialized_lean_repair_manifest_hash",
                "stage_artifact_hashes",
                "review_continuation_work_order_id",
                "review_continuation_work_order_hash",
                "n_work_orders",
                "n_source_lookup_rows",
                "n_authoring_tasks",
                "authoring_worker_ran",
                "authoring_model_invoked",
                "authoring_live_model_invoked",
                "n_authoring_candidate_packets",
                "n_materialization_rows",
                "n_materialized_candidates",
                "n_followup_authoring_tasks",
                "n_environment_repair_tasks",
                "n_typechecked_review_packets",
                "review_continuation_dispatched",
                "n_local_lean_checked",
                "n_local_lean_compiled",
                "source_theorem_kernel_verified",
                "semantic_definition_kernel_verified",
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


def _review_continuation_work_order(
    *,
    question_id: str,
    parent_work_order: Mapping[str, Any],
    stage_manifests: Mapping[str, Mapping[str, Any]],
    latest_repair_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    path_fields = {
        "followup_authoring_tasks": (
            "exact_semantic_definition_authoring_tasks_jsonl"
        ),
        "environment_repair_tasks": "lean_environment_repair_tasks_jsonl",
        "typechecked_review_packets": (
            "typechecked_candidate_review_packets_jsonl"
        ),
    }
    input_bindings = [
        _bound_text_file(
            latest_repair_manifest.get(source_key, ""),
            role=role,
        )
        for role, source_key in path_fields.items()
        if str(latest_repair_manifest.get(source_key, "") or "").strip()
    ]
    input_rows = [
        row
        for binding in input_bindings
        for row in _read_jsonl(binding.get("path", ""))
    ]
    candidate_bindings = _candidate_file_bindings_from_rows(input_rows)
    source_stage_artifact_hashes = {
        str(artifact_id): stable_hash(dict(artifact))
        for artifact_id, artifact in stage_manifests.items()
    }
    latest_repair_manifest_path = str(
        latest_repair_manifest.get("manifest_path", "") or ""
    )
    source_repair_manifest_id = next(
        (
            str(artifact_id)
            for artifact_id, artifact in stage_manifests.items()
            if _same_path(
                artifact.get("manifest_path", ""),
                latest_repair_manifest_path,
            )
        ),
        "",
    )
    source_repair_manifest_hash = source_stage_artifact_hashes.get(
        source_repair_manifest_id,
        "",
    )
    review_policy = dict(
        parent_work_order.get("review_execution_policy", {}) or {}
    )
    source_task_payload = parent_work_order.get("source_task", {})
    return_task_payload = parent_work_order.get("return_task", {})
    work_order_id = "runtime_exact_semantic_definition_review_work_order:" + stable_hash(
        [
            parent_work_order.get("work_order_id", ""),
            source_stage_artifact_hashes,
            source_repair_manifest_id,
            source_repair_manifest_hash,
            input_bindings,
            candidate_bindings,
            parent_work_order.get("source_proof_body_row_hashes", []),
            review_policy,
        ]
    )[:20]
    work_order = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": EXACT_SEMANTIC_DEFINITION_REVIEW_WORK_ORDER_KIND,
        "work_order_id": work_order_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question_id,
        "source_subsystem": EXACT_SEMANTIC_DEFINITION_SUBSYSTEM,
        "target_subsystem": EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
        "parent_work_order_id": str(
            parent_work_order.get("work_order_id", "") or ""
        ),
        "parent_work_order_hash": stable_hash(dict(parent_work_order)),
        "source_formalization_manifest_id": str(
            parent_work_order.get("source_formalization_manifest_id", "") or ""
        ),
        "source_formalization_manifest_hash": str(
            parent_work_order.get("source_formalization_manifest_hash", "") or ""
        ),
        "source_stage_artifact_ids": list(source_stage_artifact_hashes),
        "source_stage_artifact_hashes": source_stage_artifact_hashes,
        "source_repair_manifest_id": source_repair_manifest_id,
        "source_repair_manifest_hash": source_repair_manifest_hash,
        "input_file_bindings": input_bindings,
        "candidate_artifact_bindings": candidate_bindings,
        "source_proof_body_rows": [
            dict(row)
            for row in parent_work_order.get("source_proof_body_rows", []) or []
            if isinstance(row, Mapping)
        ],
        "source_proof_body_row_hashes": list(
            parent_work_order.get("source_proof_body_row_hashes", []) or []
        ),
        "source_proof_body_candidate_bindings": [
            dict(binding)
            for binding in parent_work_order.get(
                "source_proof_body_candidate_bindings",
                [],
            )
            or []
            if isinstance(binding, Mapping)
        ],
        "review_execution_policy": review_policy,
        "review_execution_policy_fingerprint": stable_hash(review_policy),
        "source_task": (
            dict(source_task_payload)
            if isinstance(source_task_payload, Mapping)
            else {}
        ),
        "return_task": (
            dict(return_task_payload)
            if isinstance(return_task_payload, Mapping)
            else {}
        ),
        "runtime_generated_lean": False,
        "python_lean_grammar_generation_or_repair": False,
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_REVIEW_WORK_ORDER_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }
    return _with_architect_control(
        work_order,
        parent_work_order,
        subsystem=EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
    )


def _review_continuation_dispatch_task(
    *,
    question: Mapping[str, Any],
    architect_context: Mapping[str, Any],
    work_order: Mapping[str, Any],
) -> AgentTask:
    work_order_id = str(work_order.get("work_order_id", "") or "")
    question_id = str(question.get("id", "") or "")
    return AgentTask(
        task_id=(
            f"exact-semantic-review:{question_id}:"
            f"{stable_hash(work_order_id)[:8]}"
        ),
        owner_subsystem=EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
        objective=(
            "Consume compiler-emitted exact-semantic follow-up tasks. Run the "
            "LLM semantic reviewer, environment preflight, verifier gate, and only "
            "then an exact-source proof-body recheck."
        ),
        inputs={
            "question": dict(question),
            "architect_context": dict(architect_context),
            "exact_semantic_definition_review_work_order_id": work_order_id,
            "exact_semantic_definition_review_work_order_hash": stable_hash(
                dict(work_order)
            ),
        },
        allowed_tools=(
            "blackboard",
            "model_backend",
            "formal_source_retrieval",
            "local_lean",
            "lean_lsp_mcp",
            "evidence_ledger",
        ),
        expected_artifacts=(
            "exact_semantic_definition_review_execution",
            "verifier_gate_execution",
            "exact_source_theorem_proof_body_recheck",
        ),
        acceptance_gate=(
            "LLM semantic approval remains non-proof evidence until the bound "
            "candidate passes the verifier gate; source theorem proof requires the "
            "exact preserved target to pass local Lean/kernel verification"
        ),
        stop_condition=(
            "the exact source theorem is kernel verified, or immutable semantic, "
            "environment, verifier, or compiler feedback returns to ProofEngineer"
        ),
    )


class ExactSemanticDefinitionRuntimeWorker:
    """Run the existing exact-semantic coding-agent/compiler loop as one typed child."""

    name = EXACT_SEMANTIC_DEFINITION_SUBSYSTEM

    def __init__(
        self,
        *,
        out_root: Path,
        source_rows_resolver: SourceRowsResolver,
        source_proof_body_rows_resolver: SourceRowsResolver | None = None,
        source_roots: Sequence[Path] = (),
        max_hits_per_work_order: int = 8,
        local_lean: bool = False,
        lean_project: Path | None = None,
        lean_timeout: int = 90,
        authoring_provider: GeneratorBackend | None = None,
        authoring_enabled: bool = False,
        authoring_config: AuthoringWorkerConfig = AuthoringWorkerConfig(),
        materializer_config: AuthoringCandidateMaterializerConfig = (
            AuthoringCandidateMaterializerConfig()
        ),
        review_worker_available: bool = False,
        review_execution_policy: Mapping[str, Any] | None = None,
        repair_available: bool = False,
        source_lookup_runner: SourceLookupRunner = (
            run_source_theorem_exact_semantic_definition_source_lookup
        ),
        bridge_runner: BridgeRunner = (
            run_source_theorem_exact_semantic_definition_proofengineer_bridge
        ),
        lean_repair_runner: LeanRepairRunner = (
            run_source_theorem_exact_semantic_definition_lean_repair_executor
        ),
        authoring_runner: AuthoringRunner = (
            run_source_theorem_exact_semantic_definition_authoring_worker
        ),
        materializer_runner: MaterializerRunner = (
            run_source_theorem_exact_semantic_definition_authoring_candidate_materializer
        ),
    ) -> None:
        self.out_root = out_root
        self.source_rows_resolver = source_rows_resolver
        self.source_proof_body_rows_resolver = source_proof_body_rows_resolver
        self.source_roots = tuple(Path(value) for value in source_roots)
        self.max_hits_per_work_order = max(0, int(max_hits_per_work_order))
        self.local_lean = bool(local_lean)
        self.lean_project = lean_project
        self.lean_timeout = max(1, int(lean_timeout))
        self.authoring_provider = authoring_provider
        self.authoring_enabled = bool(authoring_enabled)
        self.authoring_config = authoring_config
        self.materializer_config = materializer_config
        self.review_worker_available = bool(review_worker_available)
        self.review_execution_policy = dict(review_execution_policy or {})
        self.repair_available = bool(repair_available)
        self.source_lookup_runner = source_lookup_runner
        self.bridge_runner = bridge_runner
        self.lean_repair_runner = lean_repair_runner
        self.authoring_runner = authoring_runner
        self.materializer_runner = materializer_runner

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question_payload = task.inputs.get("question", {})
        question_id = str(
            question_payload.get("id", "")
            if isinstance(question_payload, Mapping)
            else ""
        )
        work_order_id = str(
            task.inputs.get("exact_semantic_definition_work_order_id", "") or ""
        )
        expected_work_order_hash = str(
            task.inputs.get("exact_semantic_definition_work_order_hash", "") or ""
        )
        raw_work_order = blackboard.artifacts.get(work_order_id, {})
        work_order = dict(raw_work_order) if isinstance(raw_work_order, Mapping) else {}
        errors = self._work_order_errors(
            question_id=question_id,
            work_order_id=work_order_id,
            expected_work_order_hash=expected_work_order_hash,
            work_order=work_order,
            blackboard=blackboard,
        )
        if errors:
            return self._blocked_result(
                task=task,
                work_order_id=work_order_id,
                errors=errors,
                failure_classification="exact_semantic_definition_work_order_invalid",
            )

        source_manifest_id = str(
            work_order.get("source_formalization_manifest_id", "") or ""
        )
        source_manifest_hash = str(
            work_order.get("source_formalization_manifest_hash", "") or ""
        )
        rows = [
            dict(row)
            for row in work_order.get("work_order_rows", []) or []
            if isinstance(row, Mapping)
        ]
        row_hashes = [stable_hash(row) for row in rows]
        row_ids = [str(row.get("work_order_id", "") or "") for row in rows]
        policy_fingerprint = str(
            work_order.get("execution_policy_fingerprint", "") or ""
        )
        execution_id = "runtime_exact_semantic_definition_execution:" + stable_hash(
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

        execution_dir = (
            self.out_root
            / "runtime_exact_semantic_definition_proofengineer"
            / stable_hash([question_id, execution_id])[:20]
        )
        execution_dir.mkdir(parents=True, exist_ok=True)
        source_queue_path = execution_dir / "exact_semantic_definition_work_orders.jsonl"
        _write_jsonl(source_queue_path, rows)

        stage_manifests: dict[str, dict[str, Any]] = {}
        contract_errors: list[str] = []
        tool_calls: list[ToolCallRecord] = []
        lookup_manifest = self._run_stage(
            "source_lookup",
            contract_errors,
            lambda: self.source_lookup_runner(
                out_dir=execution_dir / "source_lookup",
                queue_jsonl=source_queue_path,
                source_roots=list(self.source_roots),
                max_hits_per_work_order=self.max_hits_per_work_order,
            ),
        )
        contract_errors.extend(
            self._lookup_errors(lookup_manifest, source_queue_path, len(rows))
        )
        lookup_manifest_path = str(lookup_manifest.get("manifest_path", "") or "")
        tool_calls.append(
            self._tool_call(
                "ExactSemanticDefinition.source_lookup",
                source_queue_path,
                lookup_manifest,
                contract_errors,
            )
        )

        bridge_manifest: dict[str, Any] = {}
        initial_repair_manifest: dict[str, Any] = {}
        if not contract_errors:
            bridge_manifest = self._run_stage(
                "proofengineer_bridge",
                contract_errors,
                lambda: self.bridge_runner(
                    out_dir=execution_dir / "proofengineer_bridge",
                    lookup_manifest=Path(lookup_manifest_path),
                    question_id=question_id,
                ),
            )
            contract_errors.extend(
                self._bridge_errors(bridge_manifest, lookup_manifest_path, len(rows))
            )
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinition.proofengineer_bridge",
                    Path(lookup_manifest_path),
                    bridge_manifest,
                    contract_errors,
                )
            )
        bridge_manifest_path = str(bridge_manifest.get("manifest_path", "") or "")
        if not contract_errors:
            initial_repair_manifest = self._run_stage(
                "lean_repair",
                contract_errors,
                lambda: self.lean_repair_runner(
                    out_dir=execution_dir / "lean_repair",
                    bridge_manifest=Path(bridge_manifest_path),
                    source_roots=self.source_roots,
                    local_lean=self.local_lean,
                    lean_project=self.lean_project,
                    lean_timeout=self.lean_timeout,
                ),
            )
            contract_errors.extend(
                self._repair_errors(
                    initial_repair_manifest,
                    source_manifest_path=bridge_manifest_path,
                    source_key="source_bridge_manifest",
                    expected_tasks=int(bridge_manifest.get("n_lean_repair_tasks", 0) or 0),
                )
            )
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinition.lean_repair",
                    Path(bridge_manifest_path),
                    initial_repair_manifest,
                    contract_errors,
                )
            )

        authoring_tasks = _read_jsonl(
            initial_repair_manifest.get(
                "exact_semantic_definition_authoring_tasks_jsonl",
                "",
            )
        )
        authoring_manifest: dict[str, Any] = {}
        materializer_manifest: dict[str, Any] = {}
        materialized_repair_manifest: dict[str, Any] = {}
        authoring_stage_ran = bool(
            authoring_tasks
            and self.authoring_enabled
            and not contract_errors
        )
        authoring_model_expected = bool(
            authoring_stage_ran
            and self.authoring_provider is not None
            and not self.authoring_config.dry_run
        )
        authoring_model_invoked = False
        authoring_live_model_invoked = False
        if authoring_stage_ran:
            authoring_tasks_path = Path(
                str(
                    initial_repair_manifest.get(
                        "exact_semantic_definition_authoring_tasks_jsonl",
                        "",
                    )
                    or ""
                )
            )
            authoring_manifest = self._run_stage(
                "authoring_worker",
                contract_errors,
                lambda: self.authoring_runner(
                    out_dir=execution_dir / "authoring_worker",
                    authoring_tasks_jsonl=authoring_tasks_path,
                    provider=self.authoring_provider,
                    config=self.authoring_config,
                ),
            )
            contract_errors.extend(
                self._authoring_errors(
                    authoring_manifest,
                    authoring_tasks_path,
                    len(authoring_tasks),
                    model_attempt_required=authoring_model_expected,
                )
            )
            authoring_model_invoked = bool(
                int(authoring_manifest.get("n_llm_attempted", 0) or 0) > 0
            )
            authoring_live_model_invoked = bool(
                int(authoring_manifest.get("n_live_llm_attempted", 0) or 0) > 0
            )
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinition.authoring_model",
                    authoring_tasks_path,
                    authoring_manifest,
                    contract_errors,
                )
            )
        authoring_manifest_path = str(authoring_manifest.get("manifest_path", "") or "")
        if (
            authoring_stage_ran
            and not contract_errors
            and int(authoring_manifest.get("n_candidate_packets", 0) or 0) > 0
        ):
            materializer_manifest = self._run_stage(
                "candidate_materializer",
                contract_errors,
                lambda: self.materializer_runner(
                    out_dir=execution_dir / "candidate_materializer",
                    authoring_worker_manifest=Path(authoring_manifest_path),
                    config=self.materializer_config,
                ),
            )
            contract_errors.extend(
                self._materializer_errors(
                    materializer_manifest,
                    authoring_manifest_path,
                    int(authoring_manifest.get("n_candidate_packets", 0) or 0),
                )
            )
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinition.candidate_materializer",
                    Path(authoring_manifest_path),
                    materializer_manifest,
                    contract_errors,
                )
            )
        materializer_manifest_path = str(
            materializer_manifest.get("manifest_path", "") or ""
        )
        if materializer_manifest and not contract_errors:
            materialized_repair_manifest = self._run_stage(
                "materialized_lean_repair",
                contract_errors,
                lambda: self.lean_repair_runner(
                    out_dir=execution_dir / "materialized_lean_repair",
                    materializer_manifest=Path(materializer_manifest_path),
                    source_roots=self.source_roots,
                    local_lean=self.local_lean,
                    lean_project=self.lean_project,
                    lean_timeout=self.lean_timeout,
                ),
            )
            contract_errors.extend(
                self._repair_errors(
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
            tool_calls.append(
                self._tool_call(
                    "ExactSemanticDefinition.materialized_lean_repair",
                    Path(materializer_manifest_path),
                    materialized_repair_manifest,
                    contract_errors,
                )
            )

        for stage, manifest in (
            ("source_lookup", lookup_manifest),
            ("proofengineer_bridge", bridge_manifest),
            ("initial_lean_repair", initial_repair_manifest),
            ("authoring_worker", authoring_manifest),
            ("candidate_materializer", materializer_manifest),
            ("materialized_lean_repair", materialized_repair_manifest),
        ):
            if manifest:
                stage_manifests[_stage_artifact_id(stage, manifest)] = (
                    _with_architect_control(manifest, work_order)
                )

        learning_rows = [
            row
            for manifest in (
                lookup_manifest,
                bridge_manifest,
                initial_repair_manifest,
                authoring_manifest,
                materializer_manifest,
                materialized_repair_manifest,
            )
            for row in _read_jsonl(manifest.get("runtime_learning_rows_jsonl", ""))
        ]
        latest_repair_manifest = (
            materialized_repair_manifest or initial_repair_manifest
        )
        execution_results = _read_jsonl(
            latest_repair_manifest.get("execution_results_jsonl", "")
        )
        followup_authoring_tasks = _read_jsonl(
            latest_repair_manifest.get(
                "exact_semantic_definition_authoring_tasks_jsonl",
                "",
            )
        )
        environment_repair_tasks = _read_jsonl(
            latest_repair_manifest.get(
                "lean_environment_repair_tasks_jsonl",
                "",
            )
        )
        typechecked_review_packets = _read_jsonl(
            latest_repair_manifest.get(
                "typechecked_candidate_review_packets_jsonl",
                "",
            )
        )
        review_continuation_needed = bool(
            followup_authoring_tasks
            or environment_repair_tasks
            or typechecked_review_packets
        )
        review_work_order: dict[str, Any] = {}
        if (
            self.review_worker_available
            and review_continuation_needed
            and latest_repair_manifest
            and not contract_errors
        ):
            review_work_order = _review_continuation_work_order(
                question_id=question_id,
                parent_work_order=work_order,
                stage_manifests=stage_manifests,
                latest_repair_manifest=latest_repair_manifest,
            )
        try:
            return_task = _task_from_payload(
                work_order.get("return_task", {})
                if isinstance(work_order.get("return_task", {}), Mapping)
                else {}
            )
        except ValueError as exc:
            contract_errors.append(f"return task invalid: {exc}")
            return_task = None

        if contract_errors or return_task is None:
            next_task = self._critic_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                feedback={
                    "failure_classification": (
                        "exact_semantic_definition_runtime_contract_invalid"
                    ),
                    "contract_errors": contract_errors,
                },
            )
            result_status = "REROUTE"
            failure_classification = (
                "exact_semantic_definition_runtime_contract_invalid"
            )
        elif review_work_order:
            question = (
                dict(question_payload)
                if isinstance(question_payload, Mapping)
                else {"id": question_id}
            )
            architect_context = (
                dict(task.inputs.get("architect_context", {}) or {})
                if isinstance(task.inputs.get("architect_context", {}), Mapping)
                else {}
            )
            next_task = _review_continuation_dispatch_task(
                question=question,
                architect_context=architect_context,
                work_order=review_work_order,
            )
            result_status = "REROUTE"
            failure_classification = (
                "exact_semantic_definition_review_continuation_ready"
            )
        elif self.repair_available:
            next_task = self._repair_task(
                work_order,
                question_id=question_id,
                execution_id=execution_id,
                feedback={
                    "failure_classification": (
                        "exact_semantic_definition_feedback_ready"
                    ),
                    "source_lookup_manifest_id": _stage_artifact_id(
                        "source_lookup", lookup_manifest
                    ),
                    "proofengineer_bridge_manifest_id": (
                        _stage_artifact_id("proofengineer_bridge", bridge_manifest)
                        if bridge_manifest
                        else ""
                    ),
                    "initial_lean_repair_manifest_id": (
                        _stage_artifact_id("initial_lean_repair", initial_repair_manifest)
                        if initial_repair_manifest
                        else ""
                    ),
                    "authoring_worker_manifest_id": (
                        _stage_artifact_id("authoring_worker", authoring_manifest)
                        if authoring_manifest
                        else ""
                    ),
                    "candidate_materializer_manifest_id": (
                        _stage_artifact_id("candidate_materializer", materializer_manifest)
                        if materializer_manifest
                        else ""
                    ),
                    "materialized_lean_repair_manifest_id": (
                        _stage_artifact_id(
                            "materialized_lean_repair",
                            materialized_repair_manifest,
                        )
                        if materialized_repair_manifest
                        else ""
                    ),
                    "runtime_learning_rows": learning_rows[:24],
                    "exact_semantic_definition_execution_results": (
                        execution_results[:12]
                    ),
                    "authoring_tasks_pending": bool(
                        authoring_tasks and not authoring_model_invoked
                    ),
                    "authoring_worker_ran": authoring_stage_ran,
                    "authoring_model_invoked": authoring_model_invoked,
                    "authoring_live_model_invoked": authoring_live_model_invoked,
                    "source_theorem_kernel_verified": False,
                    "candidate_generation_contract": (
                        "Use the LLM coding agent with the bound source lookup, "
                        "authoring, and exact Lean compiler feedback. Preserve the "
                        "source theorem target and semantic binders; do not replace "
                        "them with a helper, route probe, or runtime-authored tactic."
                    ),
                },
            )
            result_status = "REVISE"
            failure_classification = "exact_semantic_definition_feedback_ready"
        else:
            next_task = return_task
            result_status = "REROUTE"
            failure_classification = (
                "exact_semantic_definition_feedback_ready"
            )

        source_lookup_hash = stable_hash(lookup_manifest) if lookup_manifest else ""
        bridge_hash = stable_hash(bridge_manifest) if bridge_manifest else ""
        initial_repair_hash = (
            stable_hash(initial_repair_manifest) if initial_repair_manifest else ""
        )
        authoring_hash = stable_hash(authoring_manifest) if authoring_manifest else ""
        materializer_hash = (
            stable_hash(materializer_manifest) if materializer_manifest else ""
        )
        materialized_repair_hash = (
            stable_hash(materialized_repair_manifest)
            if materialized_repair_manifest
            else ""
        )
        execution_manifest = _with_architect_control(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": EXACT_SEMANTIC_DEFINITION_RUNTIME_EXECUTION_KIND,
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
                "source_lookup_manifest_hash": source_lookup_hash,
                "proofengineer_bridge_manifest_hash": bridge_hash,
                "initial_lean_repair_manifest_hash": initial_repair_hash,
                "authoring_worker_manifest_hash": authoring_hash,
                "candidate_materializer_manifest_hash": materializer_hash,
                "materialized_lean_repair_manifest_hash": materialized_repair_hash,
                "review_continuation_work_order_id": str(
                    review_work_order.get("work_order_id", "") or ""
                ),
                "review_continuation_work_order_hash": (
                    stable_hash(review_work_order) if review_work_order else ""
                ),
                "stage_artifact_ids": list(stage_manifests),
                "stage_artifact_hashes": {
                    artifact_id: stable_hash(artifact)
                    for artifact_id, artifact in stage_manifests.items()
                },
                "runtime_learning_rows": learning_rows,
                "exact_semantic_definition_execution_results": execution_results,
                "n_work_orders": len(rows),
                "n_source_lookup_rows": int(
                    lookup_manifest.get("n_lookup_rows", 0) or 0
                ),
                "n_authoring_tasks": len(authoring_tasks),
                "authoring_worker_ran": authoring_stage_ran,
                "authoring_model_invoked": authoring_model_invoked,
                "authoring_live_model_invoked": authoring_live_model_invoked,
                "n_authoring_candidate_packets": int(
                    authoring_manifest.get("n_candidate_packets", 0) or 0
                ),
                "n_materialization_rows": int(
                    materializer_manifest.get("n_materialization_rows", 0) or 0
                ),
                "n_materialized_candidates": int(
                    materializer_manifest.get(
                        "n_materialized_lean_repair_tasks",
                        0,
                    )
                    or 0
                ),
                "n_followup_authoring_tasks": len(followup_authoring_tasks),
                "n_environment_repair_tasks": len(environment_repair_tasks),
                "n_typechecked_review_packets": len(typechecked_review_packets),
                "review_continuation_dispatched": bool(review_work_order),
                "n_local_lean_checked": int(
                    (materialized_repair_manifest or initial_repair_manifest).get(
                        "n_local_lean_checked",
                        0,
                    )
                    or 0
                ),
                "n_local_lean_compiled": int(
                    (materialized_repair_manifest or initial_repair_manifest).get(
                        "n_local_lean_compiled",
                        0,
                    )
                    or 0
                ),
                "source_theorem_kernel_verified": False,
                "semantic_definition_kernel_verified": False,
                "runtime_generated_lean": False,
                "python_lean_grammar_generation_or_repair": False,
                "contract_errors": contract_errors,
                "execution_contract_satisfied": not contract_errors,
                "proof_evidence_status": (
                    "EXACT_SEMANTIC_DEFINITION_RUNTIME_FEEDBACK_NOT_SOURCE_THEOREM_PROOF"
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
            evidence_id="evidence:" + stable_hash([task.task_id, execution_id])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="exact_semantic_definition_runtime_feedback",
            status=execution_manifest["proof_evidence_status"],
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "work_order_id": work_order_id,
                "n_work_orders": len(rows),
                "n_authoring_tasks": len(authoring_tasks),
                "authoring_worker_ran": authoring_stage_ran,
                "authoring_model_invoked": authoring_model_invoked,
                "authoring_live_model_invoked": authoring_live_model_invoked,
                "n_local_lean_checked": execution_manifest["n_local_lean_checked"],
                "n_local_lean_compiled": execution_manifest["n_local_lean_compiled"],
                "review_continuation_work_order_id": str(
                    review_work_order.get("work_order_id", "") or ""
                ),
                "source_theorem_kernel_verified": False,
            },
        )
        return AgentStepResult(
            status=result_status,
            rationale=(
                "The typed exact-semantic child emitted an immutable review "
                "continuation for compiler-produced semantic, environment, and "
                "verifier feedback without claiming source-theorem proof."
                if review_work_order
                else "The typed exact-semantic child returned source lookup, LLM "
                "authoring, and compiler feedback to ProofEngineer without "
                "claiming source-theorem proof."
                if result_status == "REVISE"
                else "The typed exact-semantic child recorded non-proof feedback "
                "and returned control to CriticEvaluator."
            ),
            produced_artifacts={
                execution_id: execution_manifest,
                **stage_manifests,
                **(
                    {
                        str(review_work_order["work_order_id"]): review_work_order,
                    }
                    if review_work_order
                    else {}
                ),
            },
            observations=(
                EnvironmentObservation(
                    observation_type="exact_semantic_definition_runtime_feedback",
                    summary=(
                        f"work_orders={len(rows)} authoring_tasks={len(authoring_tasks)} "
                        f"authoring_worker={str(authoring_stage_ran).lower()} "
                        f"authoring_model={str(authoring_model_invoked).lower()} "
                        f"contract_errors={len(contract_errors)}"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "work_order_id": work_order_id,
                        "stage_artifact_ids": list(stage_manifests),
                        "proof_evidence_status": execution_manifest[
                            "proof_evidence_status"
                        ],
                        "source_theorem_kernel_verified": False,
                        "repair_routed": result_status == "REVISE",
                        "review_continuation_dispatched": bool(review_work_order),
                        "review_continuation_work_order_id": str(
                            review_work_order.get("work_order_id", "") or ""
                        ),
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
            errors.append("work_order_id missing")
        if not work_order:
            errors.append("work order missing from blackboard")
        if str(work_order.get("artifact_kind", "") or "") != (
            EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_KIND
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
        if not source_manifest_id or not source_manifest:
            errors.append("source formalization manifest missing from blackboard")
        elif stable_hash(source_manifest) != str(
            work_order.get("source_formalization_manifest_hash", "") or ""
        ):
            errors.append("source formalization manifest hash mismatch")
        rows = [
            dict(row)
            for row in work_order.get("work_order_rows", []) or []
            if isinstance(row, Mapping)
        ]
        expected_rows = self.source_rows_resolver(source_manifest) if source_manifest else []
        if not rows:
            errors.append("work order contains no exact-semantic rows")
        if rows != expected_rows:
            errors.append("work-order rows differ from source manifest projection")
        row_hashes = [stable_hash(row) for row in rows]
        if list(work_order.get("work_order_row_hashes", []) or []) != row_hashes:
            errors.append("work-order row hashes mismatch")
        row_ids = [str(row.get("work_order_id", "") or "") for row in rows]
        if any(not value for value in row_ids):
            errors.append("exact-semantic work-order identity missing")
        if len(set(row_ids)) != len(row_ids):
            errors.append("exact-semantic work-order identities are not unique")
        for row in rows:
            if str(row.get("question_id", "") or "") != question_id:
                errors.append("exact-semantic work-order question_id mismatch")
            if not str(row.get("target_theorem_name", "") or ""):
                errors.append("exact-semantic target theorem name missing")
            if not str(row.get("placeholder_symbol", "") or ""):
                errors.append("exact-semantic placeholder symbol missing")
            if _bool_value(row.get("source_theorem_kernel_verified", False)):
                errors.append("already verified source theorem must not enter repair")
        source_proof_body_rows = [
            dict(row)
            for row in work_order.get("source_proof_body_rows", []) or []
            if isinstance(row, Mapping)
        ]
        if self.source_proof_body_rows_resolver is not None:
            expected_source_proof_body_rows = (
                self.source_proof_body_rows_resolver(source_manifest)
                if source_manifest
                else []
            )
            if source_proof_body_rows != expected_source_proof_body_rows:
                errors.append(
                    "source proof-body rows differ from source manifest projection"
                )
            if list(
                work_order.get("source_proof_body_row_hashes", []) or []
            ) != [stable_hash(row) for row in source_proof_body_rows]:
                errors.append("source proof-body row hashes mismatch")
            expected_source_paths = sorted(
                {
                    str(row.get("candidate_artifact_path", "") or "")
                    for row in source_proof_body_rows
                    if str(row.get("candidate_artifact_path", "") or "")
                }
            )
            source_bindings = [
                dict(binding)
                for binding in work_order.get(
                    "source_proof_body_candidate_bindings",
                    [],
                )
                or []
                if isinstance(binding, Mapping)
            ]
            if sorted(
                str(binding.get("path", "") or "")
                for binding in source_bindings
            ) != expected_source_paths:
                errors.append("source proof-body candidate binding coverage mismatch")
            for binding in source_bindings:
                path = Path(str(binding.get("path", "") or ""))
                try:
                    source = path.read_text(encoding="utf-8")
                except OSError:
                    errors.append("source proof-body candidate artifact missing")
                    continue
                if stable_hash(source) != str(
                    binding.get("content_hash", "") or ""
                ):
                    errors.append("source proof-body candidate artifact hash mismatch")
        for binding in work_order.get("candidate_artifact_bindings", []) or []:
            if not isinstance(binding, Mapping):
                errors.append("candidate artifact binding is not an object")
                continue
            path_text = str(binding.get("artifact_path", "") or "").strip()
            expected_hash = str(
                binding.get("artifact_content_hash", "") or ""
            ).strip()
            expected_bytes = int(binding.get("artifact_utf8_bytes", 0) or 0)
            expected_present = _bool_value(binding.get("artifact_present", False))
            if not path_text:
                errors.append("candidate artifact binding is incomplete")
                continue
            try:
                source = Path(path_text).read_bytes()
                observed_present = True
            except OSError:
                source = b""
                observed_present = False
            if observed_present is not expected_present:
                errors.append("candidate artifact presence binding mismatch")
                continue
            if not expected_present:
                if expected_hash or expected_bytes != 0:
                    errors.append("absent candidate artifact binding is inconsistent")
                continue
            if not expected_hash or expected_bytes < 0:
                errors.append("candidate artifact binding is incomplete")
                continue
            observed_hash = stable_hash(
                source.decode("utf-8", errors="replace")
            )
            if observed_hash != expected_hash or len(source) != expected_bytes:
                errors.append("candidate artifact content binding mismatch")
        execution_policy = (
            dict(work_order.get("execution_policy", {}))
            if isinstance(work_order.get("execution_policy", {}), Mapping)
            else {}
        )
        if stable_hash(execution_policy) != str(
            work_order.get("execution_policy_fingerprint", "") or ""
        ):
            errors.append("execution policy fingerprint mismatch")
        configured_policy = {
            "source_roots": [str(value) for value in self.source_roots],
            "max_hits_per_work_order": self.max_hits_per_work_order,
            "proofengineer_bridge_enabled": True,
            "lean_repair_executor_enabled": True,
            "local_lean": self.local_lean,
            "lean_project": str(self.lean_project or ""),
            "lean_timeout": self.lean_timeout,
            "authoring_worker_enabled": self.authoring_enabled,
            "generation_policy": (
                "dedicated LLM authoring worker with source lookup and compiler feedback"
            ),
            "python_lean_grammar_generation_or_repair": False,
        }
        if execution_policy != configured_policy:
            errors.append("execution policy differs from registered worker configuration")
        review_policy = (
            dict(work_order.get("review_execution_policy", {}))
            if isinstance(work_order.get("review_execution_policy", {}), Mapping)
            else {}
        )
        if self.review_worker_available:
            if not review_policy:
                errors.append("review execution policy missing")
            if stable_hash(review_policy) != str(
                work_order.get("review_execution_policy_fingerprint", "") or ""
            ):
                errors.append("review execution policy fingerprint mismatch")
            if review_policy != self.review_execution_policy:
                errors.append(
                    "review execution policy differs from registered worker configuration"
                )
        return_payload = work_order.get("return_task", {})
        if not isinstance(return_payload, Mapping) or str(
            return_payload.get("owner_subsystem", "") or ""
        ) != "CriticEvaluator":
            errors.append("return task is not CriticEvaluator-owned")
        return list(dict.fromkeys(errors))

    @staticmethod
    def _lookup_errors(
        manifest: Mapping[str, Any],
        source_queue_path: Path,
        expected_rows: int,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != SOURCE_LOOKUP_ARTIFACT_KIND:
            errors.append("source lookup artifact_kind mismatch")
        if not _same_path(manifest.get("source_work_orders_jsonl", ""), source_queue_path):
            errors.append("source lookup queue lineage mismatch")
        if int(manifest.get("n_work_orders", 0) or 0) != expected_rows:
            errors.append("source lookup work-order count mismatch")
        if int(manifest.get("n_lookup_rows", 0) or 0) != expected_rows:
            errors.append("source lookup row count mismatch")
        if str(manifest.get("proof_evidence_status", "") or "") != (
            "SOURCE_LOOKUP_NOT_PROOF_EVIDENCE"
        ):
            errors.append("source lookup proof boundary mismatch")
        if not str(manifest.get("manifest_path", "") or ""):
            errors.append("source lookup manifest path missing")
        return errors

    @staticmethod
    def _bridge_errors(
        manifest: Mapping[str, Any],
        lookup_manifest_path: str,
        expected_rows: int,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != BRIDGE_ARTIFACT_KIND:
            errors.append("exact-semantic bridge artifact_kind mismatch")
        if not _same_path(manifest.get("source_lookup_manifest", ""), lookup_manifest_path):
            errors.append("exact-semantic bridge lookup lineage mismatch")
        for key in ("n_review_packets", "n_repair_packets", "n_lean_repair_tasks"):
            if int(manifest.get(key, 0) or 0) != expected_rows:
                errors.append(f"exact-semantic bridge {key} mismatch")
        if str(manifest.get("proof_evidence_status", "") or "") != (
            "EXACT_SEMANTIC_DEFINITION_PROOFENGINEER_BRIDGE_NOT_PROOF_EVIDENCE"
        ):
            errors.append("exact-semantic bridge proof boundary mismatch")
        if not str(manifest.get("manifest_path", "") or ""):
            errors.append("exact-semantic bridge manifest path missing")
        return errors

    def _repair_errors(
        self,
        manifest: Mapping[str, Any],
        *,
        source_manifest_path: str,
        source_key: str,
        expected_tasks: int,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != LEAN_REPAIR_ARTIFACT_KIND:
            errors.append("exact-semantic Lean repair artifact_kind mismatch")
        if not _same_path(manifest.get(source_key, ""), source_manifest_path):
            errors.append("exact-semantic Lean repair source lineage mismatch")
        if int(manifest.get("n_tasks", 0) or 0) != expected_tasks:
            errors.append("exact-semantic Lean repair task count mismatch")
        if int(manifest.get("n_results", 0) or 0) != expected_tasks:
            errors.append("exact-semantic Lean repair result count mismatch")
        if manifest.get("local_lean_requested") is not self.local_lean:
            errors.append("exact-semantic Lean repair local-Lean policy mismatch")
        if str(manifest.get("proof_evidence_status", "") or "") != (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
        ):
            errors.append("exact-semantic Lean repair proof boundary mismatch")
        if _bool_value(manifest.get("source_theorem_kernel_verified", False)):
            errors.append("exact-semantic repair claimed source-theorem proof")
        if not str(manifest.get("manifest_path", "") or ""):
            errors.append("exact-semantic Lean repair manifest path missing")
        return errors

    @staticmethod
    def _authoring_errors(
        manifest: Mapping[str, Any],
        source_tasks_path: Path,
        expected_tasks: int,
        *,
        model_attempt_required: bool,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != AUTHORING_ARTIFACT_KIND:
            errors.append("exact-semantic authoring artifact_kind mismatch")
        if not _same_path(manifest.get("source_authoring_tasks_jsonl", ""), source_tasks_path):
            errors.append("exact-semantic authoring task lineage mismatch")
        if int(manifest.get("n_authoring_tasks", 0) or 0) != expected_tasks:
            errors.append("exact-semantic authoring task count mismatch")
        if int(manifest.get("n_prompt_packets", 0) or 0) != expected_tasks:
            errors.append("exact-semantic authoring prompt count mismatch")
        if int(manifest.get(SOURCE_GROUNDED_AUTHORING_COUNT_KEY, 0) or 0) != (
            expected_tasks
        ):
            errors.append("exact-semantic authoring source grounding incomplete")
        if model_attempt_required and int(
            manifest.get("n_llm_attempted", 0) or 0
        ) <= 0:
            errors.append("exact-semantic authoring model attempt missing")
        if str(manifest.get("proof_evidence_status", "") or "") != (
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_WORKER_NOT_PROOF_EVIDENCE"
        ):
            errors.append("exact-semantic authoring proof boundary mismatch")
        if _bool_value(manifest.get("source_theorem_kernel_verified", False)):
            errors.append("exact-semantic authoring claimed source-theorem proof")
        if not str(manifest.get("manifest_path", "") or ""):
            errors.append("exact-semantic authoring manifest path missing")
        return errors

    @staticmethod
    def _materializer_errors(
        manifest: Mapping[str, Any],
        source_authoring_manifest_path: str,
        expected_candidates: int,
    ) -> list[str]:
        errors: list[str] = []
        if str(manifest.get("artifact_kind", "") or "") != MATERIALIZER_ARTIFACT_KIND:
            errors.append("exact-semantic materializer artifact_kind mismatch")
        if not _same_path(
            manifest.get("source_authoring_worker_manifest", ""),
            source_authoring_manifest_path,
        ):
            errors.append("exact-semantic materializer authoring lineage mismatch")
        if int(manifest.get("n_candidate_packets", 0) or 0) != expected_candidates:
            errors.append("exact-semantic materializer candidate count mismatch")
        if int(manifest.get("n_materialization_rows", 0) or 0) != expected_candidates:
            errors.append("exact-semantic materializer row count mismatch")
        n_repair_tasks = int(
            manifest.get("n_materialized_lean_repair_tasks", 0) or 0
        )
        if n_repair_tasks < 0 or n_repair_tasks > expected_candidates:
            errors.append("exact-semantic materializer repair-task count invalid")
        if str(manifest.get("proof_evidence_status", "") or "") != (
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_MATERIALIZATION_NOT_PROOF_EVIDENCE"
        ):
            errors.append("exact-semantic materializer proof boundary mismatch")
        if _bool_value(manifest.get("source_theorem_kernel_verified", False)):
            errors.append("exact-semantic materializer claimed source-theorem proof")
        if not str(manifest.get("manifest_path", "") or ""):
            errors.append("exact-semantic materializer manifest path missing")
        return errors

    @staticmethod
    def _run_stage(
        stage: str,
        errors: list[str],
        runner: Callable[[], Mapping[str, Any]],
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
            expected_persisted = dict(manifest)
            expected_persisted.pop("manifest_path", None)
            if not isinstance(persisted, Mapping) or stable_hash(
                dict(persisted)
            ) != stable_hash(expected_persisted):
                errors.append(f"{stage}: persisted manifest content mismatch")
            return manifest
        except Exception as exc:
            errors.append(f"{stage}: {type(exc).__name__}: {exc}")
            return {}

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
        prior_feedback["exact_semantic_definition_execution_id"] = execution_id
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
                f"proofengineer-exact-semantic-definition:{question_id}:"
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
    ) -> AgentTask:
        payload = (
            work_order.get("return_task", {})
            if isinstance(work_order.get("return_task", {}), Mapping)
            else {}
        )
        base = _task_from_payload(payload)
        inputs = dict(base.inputs)
        inputs["exact_semantic_definition_feedback"] = {
            **dict(feedback),
            "execution_id": execution_id,
            "source_theorem_kernel_verified": False,
        }
        return replace(
            base,
            task_id=(
                f"critic-exact-semantic-definition:{question_id}:"
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
        raw = blackboard.artifacts.get(execution_id, {})
        execution = dict(raw) if isinstance(raw, Mapping) else {}
        errors: list[str] = []
        if str(execution.get("artifact_kind", "") or "") != (
            EXACT_SEMANTIC_DEFINITION_RUNTIME_EXECUTION_KIND
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
        stage_hashes = execution.get("stage_artifact_hashes", {})
        if not isinstance(stage_hashes, Mapping):
            errors.append("existing execution stage artifact hashes missing")
        else:
            for artifact_id, expected_hash in stage_hashes.items():
                raw_stage = blackboard.artifacts.get(str(artifact_id), {})
                if not isinstance(raw_stage, Mapping):
                    errors.append("existing execution stage artifact missing")
                    continue
                if stable_hash(dict(raw_stage)) != str(expected_hash or ""):
                    errors.append("existing execution stage artifact hash mismatch")
        review_work_order_id = str(
            execution.get("review_continuation_work_order_id", "") or ""
        )
        review_work_order_hash = str(
            execution.get("review_continuation_work_order_hash", "") or ""
        )
        if review_work_order_id or review_work_order_hash:
            raw_review_work_order = blackboard.artifacts.get(
                review_work_order_id,
                {},
            )
            if not review_work_order_id or not review_work_order_hash:
                errors.append(
                    "existing execution review continuation binding incomplete"
                )
            elif not isinstance(raw_review_work_order, Mapping):
                errors.append(
                    "existing execution review continuation artifact missing"
                )
            elif stable_hash(dict(raw_review_work_order)) != review_work_order_hash:
                errors.append(
                    "existing execution review continuation artifact hash mismatch"
                )
        next_payload = execution.get("resume_next_task", {})
        try:
            next_task = _task_from_payload(
                next_payload if isinstance(next_payload, Mapping) else {}
            )
        except ValueError as exc:
            errors.append(f"existing execution resume task invalid: {exc}")
            next_task = None
        if errors or next_task is None:
            return self._blocked_result(
                task=task,
                work_order_id=work_order_id,
                errors=errors,
                failure_classification=(
                    "exact_semantic_definition_execution_replay_invalid"
                ),
            )
        return AgentStepResult(
            status=str(execution.get("execution_result_status", "") or "REROUTE"),
            rationale=(
                "Replayed the persisted exact-semantic execution without repeating "
                "source lookup, model authoring, materialization, or Lean."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type="exact_semantic_definition_execution_replayed",
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
        return AgentStepResult(
            status="BLOCKED",
            rationale=(
                "ExactSemanticDefinitionProofEngineer rejected missing, changed, "
                "or cross-task lineage before model or compiler execution."
            ),
            observations=(
                EnvironmentObservation(
                    observation_type="exact_semantic_definition_runtime_rejected",
                    summary="; ".join(str(value) for value in errors)[:500],
                    payload={
                        "work_order_id": work_order_id,
                        "validation_errors": list(errors),
                        "proof_evidence_status": (
                            "EXACT_SEMANTIC_DEFINITION_RUNTIME_INPUT_REJECTED_NOT_PROOF_EVIDENCE"
                        ),
                    },
                ),
            ),
            evidence_entries=(
                EvidenceLedgerEntry(
                    evidence_id="evidence:"
                    + stable_hash([task.task_id, work_order_id, list(errors)])[:20],
                    task_id=task.task_id,
                    artifact_id=work_order_id,
                    evidence_type="exact_semantic_definition_runtime_rejection",
                    status=(
                        "EXACT_SEMANTIC_DEFINITION_RUNTIME_INPUT_REJECTED_NOT_PROOF_EVIDENCE"
                    ),
                    boundary=KERNEL_PROOF_BOUNDARY,
                    payload={"validation_errors": list(errors)},
                ),
            ),
            failure_classification=failure_classification,
        )


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
