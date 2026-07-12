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
from ai_statistician.fingerprint import stable_hash
from ai_statistician.source_semantic_proofengineer_runtime_worker import (
    SOURCE_SEMANTIC_PROOFENGINEER_SUBSYSTEM,
    SOURCE_SEMANTIC_RUNTIME_EXECUTION_KIND,
    SOURCE_SEMANTIC_RUNTIME_WORK_ORDER_KIND,
    SourceSemanticProofEngineerRuntimeWorker,
)
from ai_statistician.source_theorem_semantic_primitive_proofengineer_bridge import (
    ARTIFACT_KIND as SOURCE_SEMANTIC_BRIDGE_ARTIFACT_KIND,
)


def _runtime_fixture(
    tmp_path: Path,
    *,
    local_lean: bool,
    verified_support: bool,
):
    source_row = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
        "work_order_id": "source-semantic:fixture",
        "semantic_primitive_id": "semantic_primitive:fixture",
        "semantic_primitive_gap": "Formalize the exact statistical primitive.",
        "semantic_primitive_gap_kind": "formal_primitive",
        "source_formalizer_packet_id": "formalizer-proposal:fixture",
        "question_id": "fixture_question",
        "question_title": "Fixture",
        "target_theorem_goal_ids": ["source_target"],
        "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
    }
    source_manifest_id = "formalization_manifest:fixture"
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": source_manifest_id,
        "llm_formalizer_proof_engineer_proposal_id": (
            "formalizer-proposal:fixture"
        ),
        "runtime_source_semantic_work_orders": [source_row],
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
        objective="Audit semantic support evidence",
        inputs={"question": {"id": "fixture_question"}},
    )
    policy = {
        "local_lean": local_lean,
        "lean_project": "",
        "lean_timeout": 30,
        "registered_support_policy": "support only",
        "candidate_source_policy": "LLM generation only",
    }
    work_order_id = "runtime_source_semantic_work_order:fixture"
    work_order = {
        "schema_version": 1,
        "artifact_kind": SOURCE_SEMANTIC_RUNTIME_WORK_ORDER_KIND,
        "work_order_id": work_order_id,
        "question_id": "fixture_question",
        "source_task_id": source_task.task_id,
        "source_subsystem": source_task.owner_subsystem,
        "target_subsystem": SOURCE_SEMANTIC_PROOFENGINEER_SUBSYSTEM,
        "source_formalization_manifest_id": source_manifest_id,
        "source_formalization_manifest_hash": stable_hash(source_manifest),
        "work_order_rows": [source_row],
        "work_order_row_hashes": [stable_hash(source_row)],
        "execution_policy": policy,
        "execution_policy_fingerprint": stable_hash(policy),
        "source_task": asdict(source_task),
        "return_task": asdict(return_task),
        "proof_evidence_status": (
            "SOURCE_SEMANTIC_RUNTIME_WORK_ORDER_NOT_PROOF_EVIDENCE"
        ),
    }
    task = AgentTask(
        task_id="source-semantic-proofengineer:fixture",
        owner_subsystem=SOURCE_SEMANTIC_PROOFENGINEER_SUBSYSTEM,
        objective="Evaluate exact semantic support",
        inputs={
            "question": {"id": "fixture_question"},
            "source_semantic_work_order_id": work_order_id,
            "source_semantic_work_order_hash": stable_hash(work_order),
        },
    )
    blackboard = BlackboardState(project_id="fixture")
    blackboard.artifacts[source_manifest_id] = source_manifest
    blackboard.artifacts[work_order_id] = work_order
    calls = {"bridge": 0}

    def bridge_runner(**kwargs):
        calls["bridge"] += 1
        bridge_dir = Path(kwargs["out_dir"])
        bridge_dir.mkdir(parents=True, exist_ok=True)
        learning_path = bridge_dir / "runtime_learning_rows.jsonl"
        learning_row = {
            "learning_task": "source_theorem_semantic_primitive_kernel_overlay",
            "target_ids": ["source_target"],
            "kernel_verified_source_theorem_semantic_support_obligation_ids": (
                ["registered_support:fixture"] if verified_support else []
            ),
            "proof_evidence_status": "LEARNING_ROW_NOT_PROOF_EVIDENCE",
        }
        learning_path.write_text(
            json.dumps(learning_row, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        audit_path = bridge_dir / "proof_audit_manifest.json"
        if verified_support:
            audit_path.write_text(
                json.dumps(
                    {
                        "n_kernel_verified": 1,
                        "checks": [
                            {
                                "obligation_id": (
                                    "registered_support:fixture"
                                ),
                                "kernel_verified": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
        check = {
            "work_order_id": source_row["work_order_id"],
            "semantic_primitive_id": source_row["semantic_primitive_id"],
            "registered_candidate_obligation_ids": [
                "registered_support:fixture"
            ],
            "kernel_verified_registered_obligation_ids": (
                ["registered_support:fixture"] if verified_support else []
            ),
            "source_theorem_ready_for_exact_proof_body": False,
        }
        return {
            "schema_version": 1,
            "artifact_kind": SOURCE_SEMANTIC_BRIDGE_ARTIFACT_KIND,
            "source_queue_jsonl": str(kwargs["queue_jsonl"]),
            "source_proof_audit_manifest": (
                str(audit_path) if verified_support else ""
            ),
            "runtime_learning_rows_jsonl": str(learning_path),
            "local_lean_requested": local_lean,
            "n_work_orders": 1,
            "checks": [check],
            "source_theorem_ready_for_exact_proof_body": False,
            "proof_evidence_status": (
                "KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT_PRESENT"
                if verified_support
                else "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
            ),
        }

    worker = SourceSemanticProofEngineerRuntimeWorker(
        out_root=tmp_path / "runtime",
        source_rows_resolver=lambda manifest: [
            dict(row)
            for row in manifest.get("runtime_source_semantic_work_orders", [])
        ],
        bridge_runner=bridge_runner,
        repair_available=True,
    )
    return worker, task, blackboard, calls


def test_source_semantic_runtime_routes_unresolved_work_to_llm(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        verified_support=False,
    )

    result = worker.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ProofEngineer"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["registered_support_is_source_theorem_proof"] is False
    assert "Python must not generate Lean grammar" in feedback[
        "candidate_generation_contract"
    ]
    assert calls == {"bridge": 1}


def test_source_semantic_runtime_keeps_verified_support_below_theorem_boundary(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        verified_support=True,
    )

    result = worker.run(task, blackboard)

    execution = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == SOURCE_SEMANTIC_RUNTIME_EXECUTION_KIND
    )
    assert result.status == "REVISE"
    assert execution["execution_contract_satisfied"] is True
    assert execution["kernel_verified_support_ids"] == [
        "registered_support:fixture"
    ]
    assert execution["source_theorem_kernel_verified"] is False
    assert execution["registered_support_is_source_theorem_proof"] is False
    assert execution["runtime_generated_lean"] is False
    assert calls == {"bridge": 1}


def test_source_semantic_runtime_rejects_forged_support_without_local_lean(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _calls = _runtime_fixture(
        tmp_path,
        local_lean=False,
        verified_support=True,
    )

    result = worker.run(task, blackboard)

    execution = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == SOURCE_SEMANTIC_RUNTIME_EXECUTION_KIND
    )
    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    assert execution["execution_contract_satisfied"] is False
    assert (
        "kernel-verified semantic support lacks requested local Lean"
        in execution["contract_errors"]
    )


def test_source_semantic_runtime_rejects_support_missing_from_bound_audit(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        verified_support=True,
    )
    original_bridge = worker.bridge_runner

    def forged_bridge(**kwargs):
        payload = dict(original_bridge(**kwargs))
        audit_path = Path(payload["source_proof_audit_manifest"])
        audit_path.write_text(
            json.dumps({"n_kernel_verified": 0, "checks": []}),
            encoding="utf-8",
        )
        return payload

    worker.bridge_runner = forged_bridge

    result = worker.run(task, blackboard)

    execution = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == SOURCE_SEMANTIC_RUNTIME_EXECUTION_KIND
    )
    assert result.status == "REROUTE"
    assert execution["execution_contract_satisfied"] is False
    assert (
        "semantic support ids are not kernel verified in bound audit"
        in execution["contract_errors"]
    )


def test_source_semantic_runtime_rejects_tamper_before_bridge(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        verified_support=False,
    )
    work_order_id = task.inputs["source_semantic_work_order_id"]
    blackboard.artifacts[work_order_id]["work_order_rows"][0][
        "semantic_primitive_id"
    ] = "changed"

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == "source_semantic_work_order_invalid"
    assert calls == {"bridge": 0}


def test_source_semantic_runtime_replays_without_bridge(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        verified_support=False,
    )
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)

    replay = worker.run(task, blackboard)

    assert replay.status == "REVISE"
    assert calls == {"bridge": 1}
    assert replay.observations[0].payload["execution_replayed"] is True
    assert replay.observations[0].payload["bridge_or_lean_reexecuted"] is False


def test_source_semantic_worker_is_agent_runtime_child_before_llm_repair(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, calls = _runtime_fixture(
        tmp_path,
        local_lean=True,
        verified_support=False,
    )

    class ProofEngineer:
        name = "ProofEngineer"

        def run(self, _task, _blackboard):
            return AgentStepResult(
                status="COMPLETED",
                rationale="LLM ProofEngineer consumed semantic feedback.",
            )

    result = AgentRuntime(
        subsystems={
            SOURCE_SEMANTIC_PROOFENGINEER_SUBSYSTEM: worker,
            "ProofEngineer": ProofEngineer(),
        },
        blackboard=blackboard,
    ).run(task, max_iterations=2)

    assert result.status == "COMPLETED"
    assert [trace.subsystem for trace in result.traces] == [
        SOURCE_SEMANTIC_PROOFENGINEER_SUBSYSTEM,
        "ProofEngineer",
    ]
    assert calls == {"bridge": 1}
