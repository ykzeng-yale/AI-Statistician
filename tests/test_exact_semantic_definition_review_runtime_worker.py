from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ai_statistician.agent_runtime import AgentStepResult, AgentTask, BlackboardState
from ai_statistician.exact_semantic_definition_review_runtime_worker import (
    ExactSemanticDefinitionReviewRuntimeWorker,
    _source_candidate_bindings,
)
from ai_statistician.exact_semantic_definition_runtime_worker import (
    EXACT_SEMANTIC_DEFINITION_REVIEW_EXECUTION_KIND,
    EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
    EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_KIND,
    EXACT_SEMANTIC_DEFINITION_SUBSYSTEM,
    _review_continuation_work_order,
)
from ai_statistician.exact_source_theorem_proof_body_executor import (
    SOURCE_KERNEL_STATUS,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.source_theorem_exact_semantic_definition_authoring_worker import (
    ARTIFACT_KIND as AUTHORING_ARTIFACT_KIND,
    MATERIALIZER_ARTIFACT_KIND,
    AuthoringCandidateMaterializerConfig,
    AuthoringWorkerConfig,
)
from ai_statistician.source_theorem_exact_semantic_definition_lean_environment_repair_executor import (
    ARTIFACT_KIND as ENVIRONMENT_ARTIFACT_KIND,
    PROOF_EVIDENCE_STATUS as ENVIRONMENT_PROOF_STATUS,
)
from ai_statistician.source_theorem_exact_semantic_definition_lean_repair_executor import (
    ARTIFACT_KIND as LEAN_REPAIR_ARTIFACT_KIND,
)
from ai_statistician.source_theorem_exact_semantic_definition_source_lookup import (
    TYPECHECKED_REVIEW_RECHECK_QUEUE_PROOF_EVIDENCE_STATUS,
)
from ai_statistician.source_theorem_exact_semantic_definition_verifier_gate_executor import (
    ARTIFACT_KIND as VERIFIER_ARTIFACT_KIND,
    PROOF_EVIDENCE_STATUS as VERIFIER_PROOF_STATUS,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _persist_manifest(
    out_dir: Path,
    payload: dict[str, object],
    *,
    filename: str = "manifest.json",
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / filename
    manifest_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return {**payload, "manifest_path": str(manifest_path)}


def _review_fixture(
    tmp_path: Path,
    *,
    question_id: str = "survival_model_consistency",
    target_theorem_name: str = "cox_partial_likelihood_consistency",
    placeholder_symbol: str = "baselineHazard",
    verifier_approved: bool = True,
    forge_verifier_source_proof: bool = False,
):
    lean_project = tmp_path / "lean_project"
    lean_project.mkdir()
    candidate = tmp_path / f"{placeholder_symbol}.lean"
    candidate_source = (
        f"def {placeholder_symbol} (x : Nat) : Nat := x\n"
        f"theorem {target_theorem_name} : True := by trivial\n"
    )
    candidate.write_text(candidate_source, encoding="utf-8")
    reviewed_candidate = tmp_path / f"reviewed_{placeholder_symbol}.lean"
    source_row = {
        "schema_version": 1,
        "artifact_kind": "RuntimeExactSourceTheoremProofBodyRow",
        "work_order_id": f"source-proof:{question_id}",
        "question_id": question_id,
        "question_title": "Cox model consistency",
        "target_theorem_name": target_theorem_name,
        "target_lean_declaration": (
            f"theorem {target_theorem_name} : True := by trivial"
        ),
        "target_ids": [target_theorem_name],
        "candidate_artifact_path": str(candidate),
        "candidate_source_hash": stable_hash(candidate_source),
        "source_theorem_target_known": True,
        "source_theorem_target_provenance": {"source": "typed_formalization_manifest"},
        "semantic_alignment_constraints": [],
        "semantic_alignment_blockers": [],
        "source_theorem_kernel_evidence_eligible": True,
        "source_theorem_kernel_verified": False,
    }
    source_manifest_id = f"formalization_manifest:{question_id}"
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": source_manifest_id,
        "runtime_exact_source_theorem_proof_body_rows": [source_row],
    }
    source_task = AgentTask(
        task_id=f"formalize:{question_id}",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the exact source theorem.",
        inputs={"question": {"id": question_id}},
    )
    return_task = AgentTask(
        task_id=f"critic:{question_id}",
        owner_subsystem="CriticEvaluator",
        objective="Audit exact theorem evidence.",
        inputs={"question": {"id": question_id}},
    )
    authoring_config = AuthoringWorkerConfig(
        provider_name="static",
        dry_run=False,
    )
    materializer_config = AuthoringCandidateMaterializerConfig()
    review_policy = {
        "environment_preflight_enabled": True,
        "authoring_enabled": True,
        "authoring_config_fingerprint": stable_hash(asdict(authoring_config)),
        "materializer_config_fingerprint": stable_hash(asdict(materializer_config)),
        "local_lean": True,
        "lean_project": str(lean_project),
        "lean_timeout": 90,
        "proof_body_execute": True,
        "proof_body_local_lean": True,
        "proof_body_lean_project": str(lean_project),
        "proof_body_lean_timeout": 90,
        "proof_body_overwrite": False,
        "runtime_generated_lean": False,
        "python_lean_grammar_generation_or_repair": False,
    }
    parent_work_order_id = f"runtime-exact-semantic:{question_id}"
    parent_work_order = {
        "schema_version": 1,
        "artifact_kind": EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_KIND,
        "work_order_id": parent_work_order_id,
        "question_id": question_id,
        "target_subsystem": EXACT_SEMANTIC_DEFINITION_SUBSYSTEM,
        "source_formalization_manifest_id": source_manifest_id,
        "source_formalization_manifest_hash": stable_hash(source_manifest),
        "source_proof_body_rows": [source_row],
        "source_proof_body_row_hashes": [stable_hash(source_row)],
        "source_proof_body_candidate_bindings": [
            {
                "path": str(candidate),
                "present": True,
                "content_hash": stable_hash(candidate_source),
                "utf8_bytes": len(candidate_source.encode("utf-8")),
            }
        ],
        "review_execution_policy": review_policy,
        "review_execution_policy_fingerprint": stable_hash(review_policy),
        "source_task": asdict(source_task),
        "return_task": asdict(return_task),
        "source_theorem_kernel_verified": False,
    }

    continuation_dir = tmp_path / "continuation"
    authoring_tasks_path = continuation_dir / "authoring_tasks.jsonl"
    environment_tasks_path = continuation_dir / "environment_tasks.jsonl"
    review_packets_path = continuation_dir / "review_packets.jsonl"
    _write_jsonl(
        authoring_tasks_path,
        [
            {
                "authoring_task_id": f"review:{question_id}",
                "question_id": question_id,
                "target_theorem_name": target_theorem_name,
                "placeholder_symbol": placeholder_symbol,
                "authoring_mode": ("review_typechecked_semantic_definition_candidate"),
                "candidate_artifact_path": str(candidate),
                "definition_only_candidate_artifact_path": str(candidate),
            }
        ],
    )
    _write_jsonl(
        environment_tasks_path,
        [
            {
                "question_id": question_id,
                "target_theorem_name": target_theorem_name,
                "placeholder_symbol": placeholder_symbol,
                "candidate_source_file": str(candidate),
                "candidate_lean_project_hint": str(lean_project),
            }
        ],
    )
    _write_jsonl(review_packets_path, [])
    source_repair_manifest_path = continuation_dir / "source_repair_manifest.json"
    source_repair_manifest = {
        "schema_version": 1,
        "artifact_kind": LEAN_REPAIR_ARTIFACT_KIND,
        "manifest_path": str(source_repair_manifest_path),
        "exact_semantic_definition_authoring_tasks_jsonl": str(authoring_tasks_path),
        "lean_environment_repair_tasks_jsonl": str(environment_tasks_path),
        "typechecked_candidate_review_packets_jsonl": str(review_packets_path),
        "source_theorem_kernel_verified": False,
    }
    source_repair_manifest_path.write_text(
        json.dumps(
            {
                key: value
                for key, value in source_repair_manifest.items()
                if key != "manifest_path"
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    source_repair_id = f"runtime-stage-repair:{question_id}"
    review_work_order = _review_continuation_work_order(
        question_id=question_id,
        parent_work_order=parent_work_order,
        stage_manifests={source_repair_id: source_repair_manifest},
        latest_repair_manifest=source_repair_manifest,
    )
    review_work_order_id = str(review_work_order["work_order_id"])
    task = AgentTask(
        task_id=f"exact-semantic-review:{question_id}",
        owner_subsystem=EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
        objective="Review the exact semantic definition and continue proof.",
        inputs={
            "question": {"id": question_id},
            "exact_semantic_definition_review_work_order_id": (review_work_order_id),
            "exact_semantic_definition_review_work_order_hash": stable_hash(
                review_work_order
            ),
        },
    )
    blackboard = BlackboardState(project_id=question_id)
    blackboard.artifacts.update(
        {
            source_manifest_id: source_manifest,
            parent_work_order_id: parent_work_order,
            source_repair_id: source_repair_manifest,
            review_work_order_id: review_work_order,
        }
    )
    calls = {
        "environment": 0,
        "authoring": 0,
        "materializer": 0,
        "repair": 0,
        "recheck": 0,
        "verifier": 0,
        "executor": 0,
    }

    def environment_runner(**kwargs):
        calls["environment"] += 1
        rows = [
            json.loads(line)
            for line in Path(kwargs["environment_tasks_jsonl"])
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        results = Path(kwargs["out_dir"]) / "environment_results.jsonl"
        _write_jsonl(results, [{"ready_to_rerun_lean_repair": True}])
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": ENVIRONMENT_ARTIFACT_KIND,
                "source_environment_tasks_jsonl": str(
                    kwargs["environment_tasks_jsonl"]
                ),
                "environment_repair_results_jsonl": str(results),
                "n_tasks": len(rows),
                "n_results": len(rows),
                "n_ready_to_rerun_lean_repair": len(rows),
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": ENVIRONMENT_PROOF_STATUS,
            },
        )

    def authoring_runner(**kwargs):
        calls["authoring"] += 1
        reviewed_candidate.write_text(candidate_source, encoding="utf-8")
        packets = Path(kwargs["out_dir"]) / "candidate_packets.jsonl"
        _write_jsonl(
            packets,
            [
                {
                    "question_id": question_id,
                    "target_theorem_name": target_theorem_name,
                    "placeholder_symbol": placeholder_symbol,
                    "candidate_artifact_path": str(reviewed_candidate),
                    "definition_only_candidate_artifact_path": str(reviewed_candidate),
                    "semantic_review_decision": "approved_definition_candidate",
                    "semantic_review_evidence": ["matched source binders"],
                }
            ],
        )
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": AUTHORING_ARTIFACT_KIND,
                "source_authoring_tasks_jsonl": str(kwargs["authoring_tasks_jsonl"]),
                "authoring_candidate_packets_jsonl": str(packets),
                "n_authoring_tasks": 1,
                "n_prompt_packets": 1,
                "n_prompt_packets_with_source_grounded_authoring_handoff": 1,
                "n_llm_attempted": 1,
                "n_live_llm_attempted": 0,
                "n_candidate_packets": 1,
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "EXACT_SEMANTIC_DEFINITION_AUTHORING_WORKER_NOT_PROOF_EVIDENCE"
                ),
            },
        )

    def materializer_runner(**kwargs):
        calls["materializer"] += 1
        tasks_path = Path(kwargs["out_dir"]) / "lean_repair_tasks.jsonl"
        _write_jsonl(
            tasks_path,
            [
                {
                    "question_id": question_id,
                    "target_theorem_name": target_theorem_name,
                    "placeholder_symbol": placeholder_symbol,
                    "candidate_artifact_path": str(reviewed_candidate),
                }
            ],
        )
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": MATERIALIZER_ARTIFACT_KIND,
                "source_authoring_worker_manifest": str(
                    kwargs["authoring_worker_manifest"]
                ),
                "materialized_lean_repair_tasks_jsonl": str(tasks_path),
                "n_candidate_packets": 1,
                "n_materialization_rows": 1,
                "n_materialized_lean_repair_tasks": 1,
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_"
                    "MATERIALIZATION_NOT_PROOF_EVIDENCE"
                ),
            },
        )

    def repair_runner(**kwargs):
        calls["repair"] += 1
        review_path = Path(kwargs["out_dir"]) / "review_packets.jsonl"
        results_path = Path(kwargs["out_dir"]) / "repair_results.jsonl"
        _write_jsonl(
            review_path,
            [
                {
                    "review_packet_id": f"packet:{question_id}",
                    "question_id": question_id,
                    "target_theorem_name": target_theorem_name,
                    "target_ids": [target_theorem_name],
                    "placeholder_symbol": placeholder_symbol,
                    "candidate_artifact_path": str(reviewed_candidate),
                    "definition_only_candidate_artifact_path": str(reviewed_candidate),
                    "local_definition_lean_checked": True,
                    "local_definition_lean_compiled": True,
                    "semantic_review_decision": "approved_definition_candidate",
                    "semantic_review_evidence": ["matched source binders"],
                    "source_anchor_context": [{"anchor_id": "source-definition"}],
                    "known_gaps": [],
                    "source_theorem_kernel_verified": False,
                }
            ],
        )
        _write_jsonl(results_path, [{"local_lean_compiled": True}])
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": LEAN_REPAIR_ARTIFACT_KIND,
                "source_materializer_manifest": str(kwargs["materializer_manifest"]),
                "execution_results_jsonl": str(results_path),
                "typechecked_candidate_review_packets_jsonl": str(review_path),
                "n_tasks": 1,
                "n_results": 1,
                "n_local_lean_checked": 1,
                "n_local_lean_compiled": 1,
                "local_lean_requested": True,
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_"
                    "NOT_SOURCE_THEOREM_PROOF"
                ),
            },
        )

    def recheck_runner(**kwargs):
        calls["recheck"] += 1
        review_rows = [
            json.loads(line)
            for line in Path(kwargs["review_packets_jsonl"])
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        queue_path = Path(kwargs["out_dir"]) / (
            "exact_source_theorem_proof_body_execution_queue.jsonl"
        )
        verifier_orders_path = Path(kwargs["out_dir"]) / "verifier_orders.jsonl"
        if calls["recheck"] == 1:
            queue_rows: list[dict[str, object]] = []
            verifier_orders = [
                {
                    **review_rows[0],
                    "work_order_id": f"verify:{question_id}",
                }
            ]
        else:
            queue_rows = [
                {
                    "execution_queue_id": f"queue:{question_id}",
                    "question_id": question_id,
                }
            ]
            verifier_orders = []
        _write_jsonl(queue_path, queue_rows)
        _write_jsonl(verifier_orders_path, verifier_orders)
        payload = {
            "artifact_kind": (
                "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedReviewRecheckQueueManifest"
            ),
            "source_review_packets_jsonl": str(kwargs["review_packets_jsonl"]),
            "proof_body_execution_queue_jsonl": str(queue_path),
            "verifier_gate_work_orders_jsonl": str(verifier_orders_path),
            "n_review_packets": len(review_rows),
            "n_source_proof_body_rows": 1,
            "n_verifier_gate_work_orders": len(verifier_orders),
            "n_execution_queue_rows": len(queue_rows),
            "source_theorem_kernel_verified": False,
            "source_theorem_kernel_evidence_eligible": False,
            "proof_evidence_status": (
                TYPECHECKED_REVIEW_RECHECK_QUEUE_PROOF_EVIDENCE_STATUS
            ),
            "rows": queue_rows,
        }
        manifest = _persist_manifest(
            Path(kwargs["out_dir"]),
            payload,
            filename=("exact_source_theorem_proof_body_execution_queue_manifest.json"),
        )
        manifest["queue_jsonl"] = str(queue_path)
        return manifest

    def verifier_runner(**kwargs):
        calls["verifier"] += 1
        work_orders = [
            json.loads(line)
            for line in Path(kwargs["work_orders_jsonl"])
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        approved_path = Path(kwargs["out_dir"]) / "approved_packets.jsonl"
        results_path = Path(kwargs["out_dir"]) / "verifier_results.jsonl"
        approved_rows = (
            [
                {
                    **work_orders[0],
                    "artifact_kind": (
                        "SourceTheoremExactSemanticDefinitionVerifierApprovedReviewPacket"
                    ),
                    "source_theorem_ready_for_exact_proof_body": True,
                    "source_theorem_kernel_verified": False,
                }
            ]
            if verifier_approved
            else []
        )
        _write_jsonl(approved_path, approved_rows)
        _write_jsonl(
            results_path,
            [
                {
                    "verifier_gate_status": (
                        "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK"
                        if verifier_approved
                        else "VERIFIER_BLOCKED"
                    )
                }
            ],
        )
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": VERIFIER_ARTIFACT_KIND,
                "source_verifier_gate_work_orders_jsonl": str(
                    kwargs["work_orders_jsonl"]
                ),
                "verifier_approved_review_packets_jsonl": str(approved_path),
                "verifier_gate_results_jsonl": str(results_path),
                "n_work_orders": len(work_orders),
                "n_results": len(work_orders),
                "n_verifier_approved": len(approved_rows),
                "local_lean_requested": True,
                "source_theorem_kernel_verified": (forge_verifier_source_proof),
                "source_theorem_kernel_evidence_eligible": False,
                "proof_evidence_status": VERIFIER_PROOF_STATUS,
            },
        )

    def proof_body_executor(queue_dir, *, out_dir, **_kwargs):
        calls["executor"] += 1
        queue_manifest_path = Path(queue_dir) / (
            "exact_source_theorem_proof_body_execution_queue_manifest.json"
        )
        row = {
            "source_theorem_kernel_verified": True,
            "local_lean_requested": True,
            "local_lean_checked": True,
            "local_lean_compiled": True,
            "artifact_kernel_verified": True,
            "returncode": 0,
            "proof_evidence_status": SOURCE_KERNEL_STATUS,
            "target_identity_status": "TARGET_DECLARATION_MATCHED",
            "target_identity_source": (
                "upstream_structured_target_declaration_and_artifact_hash"
            ),
            "signature_probe_artifact_hash_verified": True,
            "target_artifact_lineage_verified": True,
        }
        payload = {
            "artifact_kind": ("ExactSourceTheoremProofBodyExecutionResultManifest"),
            "exact_source_theorem_proof_body_execution_queue_manifest": str(
                queue_manifest_path
            ),
            "n_execution_result_rows": 1,
            "n_source_theorem_kernel_verified": 1,
            "all_source_theorems_kernel_verified": True,
            "rows": [row],
            "proof_evidence_status": SOURCE_KERNEL_STATUS,
        }
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        manifest_path = Path(out_dir) / "execution_manifest.json"
        payload["execution_result_manifest"] = str(manifest_path)
        manifest_path.write_text(
            json.dumps(payload, sort_keys=True),
            encoding="utf-8",
        )
        return payload

    worker = ExactSemanticDefinitionReviewRuntimeWorker(
        out_root=tmp_path / "runtime",
        source_proof_body_rows_resolver=lambda manifest: [
            dict(row)
            for row in manifest.get(
                "runtime_exact_source_theorem_proof_body_rows",
                [],
            )
        ],
        source_roots=(),
        local_lean=True,
        lean_project=lean_project,
        lean_timeout=90,
        authoring_provider=object(),
        authoring_enabled=True,
        authoring_config=authoring_config,
        materializer_config=materializer_config,
        review_execution_policy=review_policy,
        repair_available=True,
        environment_runner=environment_runner,
        authoring_runner=authoring_runner,
        materializer_runner=materializer_runner,
        lean_repair_runner=repair_runner,
        recheck_runner=recheck_runner,
        verifier_runner=verifier_runner,
        proof_body_executor=proof_body_executor,
    )
    return worker, task, blackboard, calls, candidate, reviewed_candidate


def _execution(result: AgentStepResult) -> dict[str, object]:
    return next(
        dict(artifact)
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == EXACT_SEMANTIC_DEFINITION_REVIEW_EXECUTION_KIND
    )


def test_review_worker_runs_llm_verifier_and_exact_kernel_gate(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate, _reviewed = _review_fixture(tmp_path)

    result = worker.run(task, blackboard)
    execution = _execution(result)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    assert calls == {
        "environment": 1,
        "authoring": 1,
        "materializer": 1,
        "repair": 1,
        "recheck": 2,
        "verifier": 1,
        "executor": 1,
    }
    assert execution["execution_contract_satisfied"] is True
    assert execution["semantic_definition_verifier_approved"] is True
    assert execution["source_theorem_kernel_verified"] is True
    assert execution["n_source_theorem_kernel_verified"] == 1
    assert execution["proof_evidence_status"] == SOURCE_KERNEL_STATUS
    assert execution["runtime_generated_lean"] is False
    assert execution["python_lean_grammar_generation_or_repair"] is False


def test_llm_semantic_approval_without_verifier_does_not_prove(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate, _reviewed = _review_fixture(
        tmp_path,
        verifier_approved=False,
    )

    result = worker.run(task, blackboard)
    execution = _execution(result)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ProofEngineer"
    assert calls["verifier"] == 1
    assert calls["executor"] == 0
    assert execution["source_theorem_kernel_verified"] is False
    assert execution["n_source_theorem_kernel_verified"] == 0
    assert not execution["proof_evidence_status"].endswith("SOURCE_KERNEL_VERIFIED")


def test_forged_verifier_source_proof_claim_is_contract_error(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate, _reviewed = _review_fixture(
        tmp_path,
        forge_verifier_source_proof=True,
    )

    result = worker.run(task, blackboard)
    execution = _execution(result)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    assert calls["executor"] == 0
    assert execution["execution_contract_satisfied"] is False
    assert execution["source_theorem_kernel_verified"] is False
    assert (
        "semantic verifier claimed source-theorem proof" in execution["contract_errors"]
    )


def test_review_worker_rejects_same_path_candidate_swap_before_tools(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, candidate, _reviewed = _review_fixture(tmp_path)
    candidate.write_text("def changed : Bool := true\n", encoding="utf-8")

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "exact_semantic_definition_review_work_order_invalid"
    )
    assert all(value == 0 for value in calls.values())


def test_source_candidate_binding_distinguishes_missing_from_empty_file(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    rows = [{"candidate_artifact_path": str(candidate)}]

    missing_binding = _source_candidate_bindings(rows)
    candidate.write_text("", encoding="utf-8")
    empty_binding = _source_candidate_bindings(rows)

    assert missing_binding[0]["present"] is False
    assert missing_binding[0]["content_hash"] == ""
    assert empty_binding[0]["present"] is True
    assert empty_binding[0]["content_hash"] == stable_hash("")
    assert missing_binding != empty_binding


def test_review_worker_replay_does_not_repeat_model_or_lean_calls(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate, _reviewed = _review_fixture(tmp_path)
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)
    first_counts = dict(calls)

    replay = worker.run(task, blackboard)

    assert replay.status == first.status
    assert replay.next_task == first.next_task
    assert calls == first_counts
    assert replay.observations[0].payload["execution_replayed"] is True


def test_review_worker_replay_rejects_generated_candidate_swap(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate, reviewed = _review_fixture(tmp_path)
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)
    first_counts = dict(calls)
    reviewed.write_text("def replacedOutput : Bool := true\n", encoding="utf-8")

    replay = worker.run(task, blackboard)

    assert replay.status == "BLOCKED"
    assert replay.failure_classification == (
        "exact_semantic_definition_review_execution_replay_invalid"
    )
    assert calls == first_counts


def test_review_worker_rejects_cross_task_reuse_before_tools(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate, _reviewed = _review_fixture(tmp_path)
    cross_task = AgentTask(
        task_id=task.task_id,
        owner_subsystem=task.owner_subsystem,
        objective=task.objective,
        inputs={**task.inputs, "question": {"id": "unrelated_bandit_regret"}},
    )

    result = worker.run(cross_task, blackboard)

    assert result.status == "BLOCKED"
    assert all(value == 0 for value in calls.values())


def test_review_worker_is_parameterized_for_unrelated_statistical_family(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _calls, _candidate, _reviewed = _review_fixture(
        tmp_path,
        question_id="adaptive_trial_martingale",
        target_theorem_name="always_valid_type_i_error_control",
        placeholder_symbol="predictableBoundary",
    )

    result = worker.run(task, blackboard)
    execution = _execution(result)

    assert result.status == "REROUTE"
    assert execution["question_id"] == "adaptive_trial_martingale"
    assert execution["source_theorem_kernel_verified"] is True
