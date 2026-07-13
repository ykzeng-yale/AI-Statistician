from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from ai_statistician.agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
)
from ai_statistician.exact_semantic_definition_runtime_worker import (
    EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM,
    EXACT_SEMANTIC_DEFINITION_REVIEW_WORK_ORDER_KIND,
    EXACT_SEMANTIC_DEFINITION_RUNTIME_EXECUTION_KIND,
    EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_KIND,
    EXACT_SEMANTIC_DEFINITION_SUBSYSTEM,
    ExactSemanticDefinitionRuntimeWorker,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.source_theorem_exact_semantic_definition_authoring_worker import (
    ARTIFACT_KIND as AUTHORING_ARTIFACT_KIND,
    MATERIALIZER_ARTIFACT_KIND,
    AuthoringWorkerConfig,
)
from ai_statistician.source_theorem_exact_semantic_definition_lean_repair_executor import (
    ARTIFACT_KIND as LEAN_REPAIR_ARTIFACT_KIND,
)
from ai_statistician.source_theorem_exact_semantic_definition_proofengineer_bridge import (
    ARTIFACT_KIND as BRIDGE_ARTIFACT_KIND,
)
from ai_statistician.source_theorem_exact_semantic_definition_source_lookup import (
    ARTIFACT_KIND as SOURCE_LOOKUP_ARTIFACT_KIND,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _persist_manifest(out_dir: Path, payload: dict[str, object]) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    manifest = {**payload, "manifest_path": str(manifest_path)}
    manifest_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return manifest


def _runtime_fixture(
    tmp_path: Path,
    *,
    question_id: str = "survival_model_consistency",
    target_theorem_name: str = "cox_partial_likelihood_consistency",
    placeholder_symbol: str = "baselineHazard",
    authoring_enabled: bool = False,
    emit_authoring_task: bool = False,
    forge_source_theorem_claim: bool = False,
):
    candidate = tmp_path / f"{placeholder_symbol}.lean"
    candidate.write_text(
        f"def {placeholder_symbol} (x : Nat) : Nat := x\n",
        encoding="utf-8",
    )
    source_row = {
        "schema_version": 1,
        "artifact_kind": "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder",
        "work_order_id": f"exact-semantic:{question_id}:{placeholder_symbol}",
        "question_id": question_id,
        "target_theorem_name": target_theorem_name,
        "placeholder_symbol": placeholder_symbol,
        "candidate_artifact_path": str(candidate),
        "candidate_definition_request": {
            "semantic_intent": (
                f"Recover the source definition of {placeholder_symbol} for "
                f"{target_theorem_name}."
            ),
        },
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
    }
    source_manifest_id = f"formalization_manifest:{question_id}"
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": source_manifest_id,
        "runtime_exact_semantic_definition_work_orders": [source_row],
    }
    source_task = AgentTask(
        task_id=f"formalize:{question_id}",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the source theorem.",
        inputs={"question": {"id": question_id}},
    )
    return_task = AgentTask(
        task_id=f"critic:{question_id}",
        owner_subsystem="CriticEvaluator",
        objective="Audit exact semantic-definition feedback.",
        inputs={"question": {"id": question_id}},
    )
    policy = {
        "source_roots": [],
        "max_hits_per_work_order": 8,
        "proofengineer_bridge_enabled": True,
        "lean_repair_executor_enabled": True,
        "local_lean": False,
        "lean_project": "",
        "lean_timeout": 90,
        "authoring_worker_enabled": authoring_enabled,
        "generation_policy": (
            "dedicated LLM authoring worker with source lookup and compiler feedback"
        ),
        "python_lean_grammar_generation_or_repair": False,
    }
    work_order_id = f"runtime_exact_semantic_definition_work_order:{question_id}"
    work_order = {
        "schema_version": 1,
        "artifact_kind": EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_KIND,
        "work_order_id": work_order_id,
        "question_id": question_id,
        "source_task_id": source_task.task_id,
        "source_subsystem": source_task.owner_subsystem,
        "target_subsystem": EXACT_SEMANTIC_DEFINITION_SUBSYSTEM,
        "source_formalization_manifest_id": source_manifest_id,
        "source_formalization_manifest_hash": stable_hash(source_manifest),
        "work_order_rows": [source_row],
        "work_order_row_hashes": [stable_hash(source_row)],
        "candidate_artifact_bindings": [
            {
                "source_field": "candidate_artifact_path",
                "artifact_path": str(candidate),
                "artifact_present": True,
                "artifact_content_hash": stable_hash(candidate.read_text(encoding="utf-8")),
                "artifact_utf8_bytes": len(candidate.read_bytes()),
            }
        ],
        "execution_policy": policy,
        "execution_policy_fingerprint": stable_hash(policy),
        "source_task": asdict(source_task),
        "return_task": asdict(return_task),
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_RUNTIME_WORK_ORDER_NOT_PROOF_EVIDENCE"
        ),
    }
    task = AgentTask(
        task_id=f"exact-semantic-definition:{question_id}",
        owner_subsystem=EXACT_SEMANTIC_DEFINITION_SUBSYSTEM,
        objective="Run exact semantic-definition coding-agent feedback.",
        inputs={
            "question": {"id": question_id},
            "exact_semantic_definition_work_order_id": work_order_id,
            "exact_semantic_definition_work_order_hash": stable_hash(work_order),
        },
    )
    blackboard = BlackboardState(project_id=question_id)
    blackboard.artifacts[source_manifest_id] = source_manifest
    blackboard.artifacts[work_order_id] = work_order
    calls: dict[str, int | list[dict[str, object]]] = {
        "lookup": 0,
        "bridge": 0,
        "repair": 0,
        "authoring": 0,
        "materializer": 0,
        "lookup_rows": [],
    }

    def lookup_runner(**kwargs):
        calls["lookup"] += 1
        rows = [
            json.loads(line)
            for line in Path(kwargs["queue_jsonl"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        calls["lookup_rows"] = rows
        learning = Path(kwargs["out_dir"]) / "learning.jsonl"
        _write_jsonl(learning, [{"learning_task": "source_lookup"}])
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": SOURCE_LOOKUP_ARTIFACT_KIND,
                "source_work_orders_jsonl": str(kwargs["queue_jsonl"]),
                "runtime_learning_rows_jsonl": str(learning),
                "n_work_orders": len(rows),
                "n_lookup_rows": len(rows),
                "proof_evidence_status": "SOURCE_LOOKUP_NOT_PROOF_EVIDENCE",
            },
        )

    def bridge_runner(**kwargs):
        calls["bridge"] += 1
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": BRIDGE_ARTIFACT_KIND,
                "source_lookup_manifest": str(kwargs["lookup_manifest"]),
                "n_review_packets": 1,
                "n_repair_packets": 1,
                "n_lean_repair_tasks": 1,
                "proof_evidence_status": (
                    "EXACT_SEMANTIC_DEFINITION_PROOFENGINEER_BRIDGE_NOT_PROOF_EVIDENCE"
                ),
            },
        )

    def repair_runner(**kwargs):
        calls["repair"] += 1
        out_dir = Path(kwargs["out_dir"])
        authoring_tasks = out_dir / "authoring_tasks.jsonl"
        _write_jsonl(
            authoring_tasks,
            ([{"task_id": f"author:{question_id}"}] if emit_authoring_task else []),
        )
        results = out_dir / "results.jsonl"
        _write_jsonl(
            results,
            [
                {
                    "question_id": question_id,
                    "target_theorem_name": target_theorem_name,
                    "placeholder_symbol": placeholder_symbol,
                    "local_lean_checked": False,
                    "source_theorem_kernel_verified": False,
                }
            ],
        )
        source_key = (
            "source_materializer_manifest"
            if "materializer_manifest" in kwargs
            else "source_bridge_manifest"
        )
        source_value = kwargs.get("materializer_manifest") or kwargs.get(
            "bridge_manifest"
        )
        return _persist_manifest(
            out_dir,
            {
                "artifact_kind": LEAN_REPAIR_ARTIFACT_KIND,
                source_key: str(source_value),
                "execution_results_jsonl": str(results),
                "exact_semantic_definition_authoring_tasks_jsonl": str(
                    authoring_tasks
                ),
                "n_tasks": 1,
                "n_results": 1,
                "n_local_lean_checked": 0,
                "n_local_lean_compiled": 0,
                "local_lean_requested": False,
                "source_theorem_kernel_verified": forge_source_theorem_claim,
                "proof_evidence_status": (
                    "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
                ),
            },
        )

    def authoring_runner(**kwargs):
        calls["authoring"] += 1
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": AUTHORING_ARTIFACT_KIND,
                "source_authoring_tasks_jsonl": str(kwargs["authoring_tasks_jsonl"]),
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
        return _persist_manifest(
            Path(kwargs["out_dir"]),
            {
                "artifact_kind": MATERIALIZER_ARTIFACT_KIND,
                "source_authoring_worker_manifest": str(
                    kwargs["authoring_worker_manifest"]
                ),
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

    worker = ExactSemanticDefinitionRuntimeWorker(
        out_root=tmp_path / "runtime",
        source_rows_resolver=lambda manifest: [
            dict(row)
            for row in manifest.get(
                "runtime_exact_semantic_definition_work_orders", []
            )
        ],
        authoring_provider=(object() if authoring_enabled else None),
        authoring_enabled=authoring_enabled,
        authoring_config=AuthoringWorkerConfig(
            provider_name="static" if authoring_enabled else "none",
            dry_run=not authoring_enabled,
        ),
        repair_available=True,
        source_lookup_runner=lookup_runner,
        bridge_runner=bridge_runner,
        lean_repair_runner=repair_runner,
        authoring_runner=authoring_runner,
        materializer_runner=materializer_runner,
    )
    return worker, task, blackboard, calls, candidate


def _execution(result: AgentStepResult) -> dict[str, object]:
    return next(
        dict(artifact)
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == EXACT_SEMANTIC_DEFINITION_RUNTIME_EXECUTION_KIND
    )


def test_exact_semantic_worker_is_typed_agent_runtime_child_before_llm_repair(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(tmp_path)

    class ProofEngineer:
        name = "ProofEngineer"

        def run(self, routed_task, _blackboard):
            feedback = routed_task.inputs["environment_feedback"]
            assert feedback["source_theorem_kernel_verified"] is False
            assert feedback["repair_owner_agent"] == "ProofEngineer"
            return AgentStepResult(
                status="ACCEPTED",
                rationale="LLM ProofEngineer consumed exact compiler feedback.",
            )

    result = AgentRuntime(
        subsystems={
            EXACT_SEMANTIC_DEFINITION_SUBSYSTEM: worker,
            "ProofEngineer": ProofEngineer(),
        },
        blackboard=blackboard,
    ).run(task, max_iterations=2)

    assert result.status == "ACCEPTED"
    assert [trace.subsystem for trace in result.traces] == [
        EXACT_SEMANTIC_DEFINITION_SUBSYSTEM,
        "ProofEngineer",
    ]
    assert calls["lookup"] == 1
    assert calls["bridge"] == 1
    assert calls["repair"] == 1
    execution = next(
        artifact
        for artifact in blackboard.artifacts.values()
        if artifact.get("artifact_kind")
        == EXACT_SEMANTIC_DEFINITION_RUNTIME_EXECUTION_KIND
    )
    assert execution["execution_contract_satisfied"] is True
    assert execution["source_theorem_kernel_verified"] is False
    assert execution["runtime_generated_lean"] is False
    assert execution["python_lean_grammar_generation_or_repair"] is False


def test_exact_semantic_worker_dispatches_hash_bound_review_continuation(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(
        tmp_path,
        authoring_enabled=True,
        emit_authoring_task=True,
    )
    review_policy = {
        "authoring_enabled": True,
        "runtime_generated_lean": False,
        "python_lean_grammar_generation_or_repair": False,
    }
    work_order_id = task.inputs["exact_semantic_definition_work_order_id"]
    work_order = blackboard.artifacts[work_order_id]
    work_order["review_execution_policy"] = review_policy
    work_order["review_execution_policy_fingerprint"] = stable_hash(
        review_policy
    )
    task = AgentTask(
        task_id=task.task_id,
        owner_subsystem=task.owner_subsystem,
        objective=task.objective,
        inputs={
            **task.inputs,
            "exact_semantic_definition_work_order_hash": stable_hash(work_order),
        },
    )
    worker.review_worker_available = True
    worker.review_execution_policy = review_policy

    result = worker.run(task, blackboard)
    execution = _execution(result)
    review_work_order = next(
        dict(artifact)
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == EXACT_SEMANTIC_DEFINITION_REVIEW_WORK_ORDER_KIND
    )

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == (
        EXACT_SEMANTIC_DEFINITION_REVIEW_SUBSYSTEM
    )
    assert calls["authoring"] == 1
    assert calls["repair"] == 2
    assert review_work_order["parent_work_order_id"] == work_order_id
    assert review_work_order["source_repair_manifest_id"]
    assert review_work_order["source_repair_manifest_hash"]
    assert review_work_order["input_file_bindings"][0]["present"] is True
    assert execution["review_continuation_dispatched"] is True
    assert execution["review_continuation_work_order_id"] == (
        review_work_order["work_order_id"]
    )


def test_exact_semantic_worker_replay_rejects_review_work_order_swap(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(
        tmp_path,
        authoring_enabled=True,
        emit_authoring_task=True,
    )
    review_policy = {"authoring_enabled": True}
    work_order_id = task.inputs["exact_semantic_definition_work_order_id"]
    work_order = blackboard.artifacts[work_order_id]
    work_order["review_execution_policy"] = review_policy
    work_order["review_execution_policy_fingerprint"] = stable_hash(
        review_policy
    )
    task = AgentTask(
        task_id=task.task_id,
        owner_subsystem=task.owner_subsystem,
        objective=task.objective,
        inputs={
            **task.inputs,
            "exact_semantic_definition_work_order_hash": stable_hash(work_order),
        },
    )
    worker.review_worker_available = True
    worker.review_execution_policy = review_policy
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)
    first_counts = dict(calls)
    review_id = _execution(first)["review_continuation_work_order_id"]
    blackboard.artifacts[review_id]["question_id"] = "changed_question"

    replay = worker.run(task, blackboard)

    assert replay.status == "BLOCKED"
    assert replay.failure_classification == (
        "exact_semantic_definition_execution_replay_invalid"
    )
    assert calls == first_counts


def test_exact_semantic_worker_rejects_work_order_tamper_before_lookup(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(tmp_path)
    work_order_id = task.inputs["exact_semantic_definition_work_order_id"]
    blackboard.artifacts[work_order_id]["work_order_rows"][0][
        "target_theorem_name"
    ] = "changed_target"

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "exact_semantic_definition_work_order_invalid"
    )
    assert calls["lookup"] == 0


def test_exact_semantic_worker_rejects_returned_manifest_disk_mismatch(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(tmp_path)
    source_lookup_runner = worker.source_lookup_runner

    def mismatched_lookup_runner(**kwargs):
        manifest = dict(source_lookup_runner(**kwargs))
        manifest["n_lookup_rows"] = 99
        return manifest

    worker.source_lookup_runner = mismatched_lookup_runner

    result = worker.run(task, blackboard)
    execution = _execution(result)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    assert execution["execution_contract_satisfied"] is False
    assert "source_lookup: persisted manifest content mismatch" in execution[
        "contract_errors"
    ]
    assert calls["lookup"] == 1
    assert calls["bridge"] == 0


def test_exact_semantic_worker_rejects_same_path_candidate_swap(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, candidate = _runtime_fixture(tmp_path)
    candidate.write_text("def swapped : Bool := true\n", encoding="utf-8")

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert calls["lookup"] == 0
    assert "candidate artifact content binding mismatch" in result.observations[
        0
    ].payload["validation_errors"]


def test_exact_semantic_worker_allows_bound_missing_candidate_for_source_recovery(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, candidate = _runtime_fixture(tmp_path)
    candidate.unlink()
    work_order_id = task.inputs["exact_semantic_definition_work_order_id"]
    work_order = blackboard.artifacts[work_order_id]
    work_order["candidate_artifact_bindings"][0].update(
        {
            "artifact_present": False,
            "artifact_content_hash": "",
            "artifact_utf8_bytes": 0,
        }
    )
    task = AgentTask(
        **{
            **asdict(task),
            "inputs": {
                **task.inputs,
                "exact_semantic_definition_work_order_hash": stable_hash(
                    work_order
                ),
            },
        }
    )

    result = worker.run(task, blackboard)

    assert result.status == "REVISE"
    assert calls["lookup"] == 1


def test_exact_semantic_worker_rejects_file_appearing_after_missing_binding(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, candidate = _runtime_fixture(tmp_path)
    candidate.unlink()
    work_order_id = task.inputs["exact_semantic_definition_work_order_id"]
    work_order = blackboard.artifacts[work_order_id]
    work_order["candidate_artifact_bindings"][0].update(
        {
            "artifact_present": False,
            "artifact_content_hash": "",
            "artifact_utf8_bytes": 0,
        }
    )
    task = AgentTask(
        **{
            **asdict(task),
            "inputs": {
                **task.inputs,
                "exact_semantic_definition_work_order_hash": stable_hash(
                    work_order
                ),
            },
        }
    )
    candidate.write_text("def lateReplacement : Nat := 0\n", encoding="utf-8")

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert calls["lookup"] == 0
    assert "candidate artifact presence binding mismatch" in result.observations[
        0
    ].payload["validation_errors"]


def test_exact_semantic_worker_replays_without_reexecuting_stages(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(tmp_path)
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)

    replay = worker.run(task, blackboard)

    assert replay.status == "REVISE"
    assert calls["lookup"] == 1
    assert calls["bridge"] == 1
    assert calls["repair"] == 1
    assert replay.observations[0].payload["execution_replayed"] is True
    assert replay.observations[0].payload[
        "coding_agent_or_compiler_reexecuted"
    ] is False


def test_exact_semantic_worker_rejects_tampered_stage_on_replay(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(tmp_path)
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)
    execution = _execution(first)
    stage_id = execution["stage_artifact_ids"][0]
    blackboard.artifacts[stage_id]["n_lookup_rows"] = 99

    replay = worker.run(task, blackboard)

    assert replay.status == "BLOCKED"
    assert replay.failure_classification == (
        "exact_semantic_definition_execution_replay_invalid"
    )
    assert calls["lookup"] == 1


def test_exact_semantic_worker_rejects_forged_source_theorem_claim(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(
        tmp_path,
        forge_source_theorem_claim=True,
    )

    result = worker.run(task, blackboard)
    execution = _execution(result)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    assert execution["execution_contract_satisfied"] is False
    assert execution["source_theorem_kernel_verified"] is False
    assert "exact-semantic repair claimed source-theorem proof" in execution[
        "contract_errors"
    ]
    assert calls["repair"] == 1


@pytest.mark.parametrize(
    ("question_id", "target", "placeholder"),
    [
        (
            "survival_model_consistency",
            "cox_partial_likelihood_consistency",
            "baselineHazard",
        ),
        (
            "spatial_point_process_limit",
            "poisson_functional_clt",
            "compensatorMeasure",
        ),
    ],
)
def test_exact_semantic_authoring_loop_preserves_unrelated_task_identity(
    tmp_path: Path,
    question_id: str,
    target: str,
    placeholder: str,
) -> None:
    worker, task, blackboard, calls, _candidate = _runtime_fixture(
        tmp_path,
        question_id=question_id,
        target_theorem_name=target,
        placeholder_symbol=placeholder,
        authoring_enabled=True,
        emit_authoring_task=True,
    )

    result = worker.run(task, blackboard)
    execution = _execution(result)

    assert result.status == "REVISE"
    assert execution["authoring_worker_ran"] is True
    assert execution["authoring_model_invoked"] is True
    assert execution["n_materialized_candidates"] == 1
    assert calls["authoring"] == 1
    assert calls["materializer"] == 1
    assert calls["repair"] == 2
    assert calls["lookup_rows"][0]["question_id"] == question_id
    assert calls["lookup_rows"][0]["target_theorem_name"] == target
    assert calls["lookup_rows"][0]["placeholder_symbol"] == placeholder
