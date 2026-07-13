from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ai_statistician.agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
)
from ai_statistician.exact_source_theorem_proof_body_executor import (
    SOURCE_KERNEL_STATUS,
)
from ai_statistician.exact_source_theorem_proof_body_runtime_worker import (
    EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_EXECUTION_KIND,
    EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_WORK_ORDER_KIND,
    EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM,
    ExactSourceTheoremProofBodyRuntimeWorker,
)
from ai_statistician.fingerprint import stable_hash


def _runtime_fixture(
    tmp_path: Path,
    *,
    local_lean: bool,
    kernel_verified: bool,
):
    candidate = tmp_path / "candidate.lean"
    candidate_source = (
        "theorem exact_source (p : Prop) (hp : p) : p := by\n"
        "  exact hp\n"
    )
    candidate.write_text(candidate_source, encoding="utf-8")
    source_row = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
        "work_order_id": "source-formal-environment:fixture",
        "source_formalizer_packet_id": "formalizer-proposal:fixture",
        "source_formal_target_id": "exact_source_target",
        "source_formalizer_lean_candidate_id": "exact_source_target",
        "question_id": "fixture_question",
        "question_title": "Fixture",
        "target_theorem_name": "exact_source",
        "target_lean_declaration": "exact_source",
        "target_lean_declaration_source": (
            "formalizer_structured_source_theorem_target_provenance"
        ),
        "target_lean_file": str(candidate),
        "target_lean_line": 0,
        "target_lean_column": 0,
        "candidate_artifact_path": str(candidate),
        "candidate_source_hash": stable_hash(candidate_source),
        "source_theorem_target_known": True,
        "source_theorem_target_provenance": {
            "source_theorem_question_id": "fixture_question",
            "target_lean_declaration": "exact_source",
        },
    }
    source_manifest_id = "formalization_manifest:fixture"
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": source_manifest_id,
        "llm_formalizer_proof_engineer_proposal_id": (
            "formalizer-proposal:fixture"
        ),
        "runtime_exact_source_theorem_proof_body_rows": [source_row],
    }
    source_task = AgentTask(
        task_id="formalize:fixture",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the fixture",
        inputs={"question": {"id": "fixture_question"}},
    )
    return_task = AgentTask(
        task_id="critic:fixture",
        owner_subsystem="CriticEvaluator",
        objective="Audit exact proof evidence",
        inputs={"question": {"id": "fixture_question"}},
    )
    policy = {
        "run_signature_probes": False,
        "local_lean": local_lean,
        "overwrite": False,
        "lean_project": "",
        "lean_timeout": 30,
    }
    binding = {
        "path": str(candidate),
        "content_hash": stable_hash(candidate_source),
        "utf8_bytes": len(candidate_source.encode("utf-8")),
    }
    work_order_id = "runtime_exact_source_theorem_proof_body_work_order:fixture"
    work_order = {
        "schema_version": 1,
        "artifact_kind": EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_WORK_ORDER_KIND,
        "work_order_id": work_order_id,
        "question_id": "fixture_question",
        "source_task_id": source_task.task_id,
        "source_subsystem": source_task.owner_subsystem,
        "target_subsystem": EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM,
        "source_formalization_manifest_id": source_manifest_id,
        "source_formalization_manifest_hash": stable_hash(source_manifest),
        "work_order_rows": [source_row],
        "work_order_row_hashes": [stable_hash(source_row)],
        "source_candidate_artifact_bindings": [binding],
        "execution_policy": policy,
        "execution_policy_fingerprint": stable_hash(policy),
        "source_task": asdict(source_task),
        "return_task": asdict(return_task),
        "proof_evidence_status": (
            "EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_WORK_ORDER_NOT_PROOF_EVIDENCE"
        ),
    }
    work_order_hash = stable_hash(work_order)
    task = AgentTask(
        task_id="exact-source-proof-body:fixture",
        owner_subsystem=EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM,
        objective="Run the exact source theorem compiler gate",
        inputs={
            "question": {"id": "fixture_question"},
            "exact_source_theorem_proof_body_work_order_id": work_order_id,
            "exact_source_theorem_proof_body_work_order_hash": work_order_hash,
        },
    )
    blackboard = BlackboardState(project_id="fixture")
    blackboard.artifacts[source_manifest_id] = source_manifest
    blackboard.artifacts[work_order_id] = work_order
    calls = {"bridge": 0, "executor": 0}

    def bridge_runner(**kwargs):
        calls["bridge"] += 1
        bridge_dir = Path(kwargs["out_dir"])
        queue_dir = bridge_dir / "exact_source_theorem_proof_body_execution_queue"
        queue_dir.mkdir(parents=True, exist_ok=True)
        queue_manifest_path = (
            queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
        )
        queue_row = {
            "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
            "execution_queue_id": "exact-source-queue:fixture",
            "source_work_order_id": source_row["work_order_id"],
            "question_id": "fixture_question",
            "target_lean_declaration": "exact_source",
            "expected_target_lean_declaration": "exact_source",
            "target_identity_status": "TARGET_DECLARATION_MATCHED",
            "target_identity_source": (
                "upstream_structured_target_declaration_and_artifact_hash"
            ),
            "signature_probe_artifact_hash": stable_hash(candidate_source),
        }
        queue_manifest_path.write_text(
            json.dumps({"rows": [queue_row]}),
            encoding="utf-8",
        )
        return {
            "artifact_kind": "SourceTheoremFormalEnvironmentProofEngineerBridgeManifest",
            "source_queue_jsonl": str(kwargs["queue_jsonl"]),
            "n_work_orders": 1,
            "signature_probes_requested": False,
            "proof_body_execution_queue_manifest": str(queue_manifest_path),
            "n_proof_body_execution_queue_rows": 1,
            "runtime_learning_rows_jsonl": "",
        }

    def executor_runner(queue_dir: Path, **_kwargs):
        calls["executor"] += 1
        queue_manifest_path = (
            Path(queue_dir)
            / "exact_source_theorem_proof_body_execution_queue_manifest.json"
        )
        row = {
            "artifact_kind": "ExactSourceTheoremProofBodyExecutionResultRow",
            "execution_queue_id": "exact-source-queue:fixture",
            "source_work_order_id": source_row["work_order_id"],
            "target_identity_status": "TARGET_DECLARATION_MATCHED",
            "target_identity_source": (
                "upstream_structured_target_declaration_and_artifact_hash"
            ),
            "signature_probe_artifact_hash_verified": True,
            "target_artifact_lineage_verified": True,
            "local_lean_requested": local_lean,
            "local_lean_checked": local_lean,
            "local_lean_compiled": kernel_verified,
            "artifact_kernel_verified": kernel_verified,
            "source_theorem_kernel_verified": kernel_verified,
            "returncode": 0 if kernel_verified else 1,
            "diagnostics": [] if kernel_verified else ["unsolved goals\n⊢ p"],
            "proofengineer_repair_context": {
                "target_lean_declaration": "exact_source",
                "compiler_feedback": {"diagnostics": ["unsolved goals\n⊢ p"]},
            },
            "proof_evidence_status": (
                SOURCE_KERNEL_STATUS
                if kernel_verified
                else "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
            ),
        }
        learning_path = Path(queue_dir) / "runtime_learning_rows.jsonl"
        learning_path.write_text(
            json.dumps(
                {
                    "learning_task": "exact_source_compiler_feedback",
                    "target_ids": ["exact_source_target"],
                    "source_work_order_id": source_row["work_order_id"],
                    "compiler_diagnostics": row["diagnostics"],
                    "proof_evidence_status": "LEARNING_ROW_NOT_PROOF_EVIDENCE",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "artifact_kind": "ExactSourceTheoremProofBodyExecutionResultManifest",
            "exact_source_theorem_proof_body_execution_queue_manifest": str(
                queue_manifest_path
            ),
            "n_execution_result_rows": 1,
            "n_source_theorem_kernel_verified": int(kernel_verified),
            "rows": [row],
            "runtime_learning_export": {
                "runtime_learning_rows_jsonl": str(learning_path)
            },
        }

    worker = ExactSourceTheoremProofBodyRuntimeWorker(
        out_root=tmp_path / "runtime",
        source_rows_resolver=lambda manifest: [
            dict(row)
            for row in manifest.get(
                "runtime_exact_source_theorem_proof_body_rows",
                [],
            )
        ],
        bridge_runner=bridge_runner,
        executor_runner=executor_runner,
        repair_available=True,
    )
    return worker, task, blackboard, candidate, calls


def test_exact_source_runtime_routes_compiler_feedback_to_llm(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _candidate, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        kernel_verified=False,
    )

    result = worker.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ProofEngineer"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["compiler_diagnostics"] == [["unsolved goals\n⊢ p"]]
    assert feedback["runtime_learning_rows"][0]["learning_task"] == (
        "exact_source_compiler_feedback"
    )
    assert feedback["runtime_learning_rows"][0]["target_ids"] == [
        "exact_source_target"
    ]
    assert "Python must not synthesize Lean grammar" in feedback[
        "candidate_generation_contract"
    ]
    assert calls == {"bridge": 1, "executor": 1}


def test_exact_source_runtime_promotes_only_bound_local_lean_result(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _candidate, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        kernel_verified=True,
    )

    result = worker.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    execution = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_EXECUTION_KIND
    )
    assert execution["execution_contract_satisfied"] is True
    assert execution["all_source_theorems_kernel_verified"] is True
    assert execution["n_source_theorem_kernel_verified"] == 1
    assert execution["runtime_generated_lean"] is False
    queue_manifest = json.loads(
        Path(execution["proof_body_execution_queue_manifest"]).read_text(
            encoding="utf-8"
        )
    )
    assert queue_manifest["queue_source_mode"] == (
        "agent_runtime_hash_bound_candidate_direct_compiler_gate"
    )
    assert queue_manifest["python_lean_parsing_or_rewrite"] is False
    assert queue_manifest["rows"][0]["proof_body_attempts"] == []
    assert queue_manifest["rows"][0]["live_proof_state_request"] == {}
    assert queue_manifest["rows"][0]["target_lean_line"] == 0
    assert calls == {"bridge": 1, "executor": 1}


def test_exact_source_runtime_rejects_forged_kernel_without_local_lean(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _candidate, _calls = _runtime_fixture(
        tmp_path,
        local_lean=False,
        kernel_verified=True,
    )

    result = worker.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    execution = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == EXACT_SOURCE_THEOREM_PROOF_BODY_RUNTIME_EXECUTION_KIND
    )
    assert execution["execution_contract_satisfied"] is False
    assert execution["all_source_theorems_kernel_verified"] is False
    assert "kernel-verified row lacks requested local Lean" in execution[
        "contract_errors"
    ]


def test_exact_source_runtime_rejects_candidate_tamper_before_tools(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, candidate, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        kernel_verified=False,
    )
    candidate.write_text("theorem changed : True := by trivial\n", encoding="utf-8")

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "exact_source_theorem_proof_body_work_order_invalid"
    )
    assert calls == {"bridge": 0, "executor": 0}


def test_exact_source_runtime_replays_without_reexecuting_tools(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _candidate, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        kernel_verified=False,
    )
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)

    replay = worker.run(task, blackboard)

    assert replay.status == "REVISE"
    assert calls == {"bridge": 1, "executor": 1}
    assert replay.observations[0].payload["execution_replayed"] is True
    assert replay.observations[0].payload["bridge_or_compiler_reexecuted"] is False


def test_exact_source_worker_is_an_agent_runtime_child_before_critic(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _candidate, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        kernel_verified=True,
    )

    class Critic:
        name = "CriticEvaluator"

        def run(self, _task, _blackboard):
            return AgentStepResult(
                status="COMPLETED",
                rationale="Critic consumed the typed exact-source evidence.",
            )

    result = AgentRuntime(
        subsystems={
            EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM: worker,
            "CriticEvaluator": Critic(),
        },
        blackboard=blackboard,
    ).run(task, max_iterations=2)

    assert result.status == "COMPLETED"
    assert [trace.subsystem for trace in result.traces] == [
        EXACT_SOURCE_THEOREM_PROOF_BODY_SUBSYSTEM,
        "CriticEvaluator",
    ]
    assert calls == {"bridge": 1, "executor": 1}
