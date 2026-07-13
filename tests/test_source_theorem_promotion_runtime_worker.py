from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ai_statistician.agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_agent_runtime import ProofEngineerRuntimeSubsystem
from ai_statistician.source_theorem_promotion_runtime_worker import (
    SOURCE_THEOREM_PROMOTION_RUNTIME_EXECUTION_KIND,
    SOURCE_THEOREM_PROMOTION_RUNTIME_WORK_ORDER_KIND,
    SOURCE_THEOREM_PROMOTION_SUBSYSTEM,
    SourceTheoremPromotionRuntimeWorker,
)


def _runtime_fixture(tmp_path: Path):
    source_row = {
        "schema_version": 1,
        "artifact_kind": "RuntimeSourceTheoremPromotionPlanningRow",
        "work_order_id": "source-theorem-promotion-planning-row:fixture",
        "source_formal_environment_work_order_id": (
            "source-formal-environment:fixture"
        ),
        "source_formalizer_packet_id": "formalizer-proposal:fixture",
        "source_formal_target_id": "source-target:fixture",
        "source_formalizer_lean_candidate_id": "source-target:fixture",
        "question_id": "fixture_question",
        "question_title": "Fixture",
        "target_ids": ["source-target:fixture"],
        "target_theorem_goal_ids": ["source-target:fixture"],
        "target_theorem_name": "exact_source",
        "target_lean_declaration": "exact_source",
        "target_lean_declaration_source": (
            "formalizer_structured_source_theorem_target_provenance"
        ),
        "candidate_artifact_path": "",
        "candidate_source_hash": "",
        "source_theorem_target_known": True,
        "source_theorem_target_provenance": {
            "source_theorem_question_id": "fixture_question",
            "target_lean_declaration": "exact_source",
        },
        "promotion_mode": (
            "source_theorem_exact_semantics_or_theorem_promotion"
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": [
            "semantic-support:fixture"
        ],
        "runtime_queue_status": (
            "PENDING_LLM_EXACT_SOURCE_CANDIDATE_GENERATION"
        ),
        "proof_evidence_status": (
            "SOURCE_THEOREM_PROMOTION_PLANNING_ROW_NOT_PROOF_EVIDENCE"
        ),
    }
    source_manifest_id = "formalization_manifest:fixture"
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": source_manifest_id,
        "llm_formalizer_proof_engineer_proposal_id": (
            "formalizer-proposal:fixture"
        ),
        "runtime_source_theorem_promotion_planning_rows": [source_row],
    }
    source_task = AgentTask(
        task_id="formalize:fixture",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the fixture",
        inputs={
            "question": {
                "id": "fixture_question",
                "description": "Prove the exact fixture source theorem.",
            }
        },
    )
    return_task = AgentTask(
        task_id="critic:fixture",
        owner_subsystem="CriticEvaluator",
        objective="Audit source-theorem promotion planning",
        inputs={"question": {"id": "fixture_question"}},
    )
    policy = {
        "legacy_route_probe_materialization": False,
        "legacy_source_theorem_integrator": False,
        "python_lean_parsing_or_rewrite": False,
        "next_compiler_subsystem": "ExactSourceTheoremProofBodyExecutor",
        "candidate_generation_policy": "LLM/prover with compiler feedback",
    }
    work_order_id = "runtime_source_theorem_promotion_work_order:fixture"
    work_order = {
        "schema_version": 1,
        "artifact_kind": SOURCE_THEOREM_PROMOTION_RUNTIME_WORK_ORDER_KIND,
        "work_order_id": work_order_id,
        "question_id": "fixture_question",
        "source_task_id": source_task.task_id,
        "source_subsystem": source_task.owner_subsystem,
        "target_subsystem": SOURCE_THEOREM_PROMOTION_SUBSYSTEM,
        "source_formalization_manifest_id": source_manifest_id,
        "source_formalization_manifest_hash": stable_hash(source_manifest),
        "work_order_rows": [source_row],
        "work_order_row_hashes": [stable_hash(source_row)],
        "execution_policy": policy,
        "execution_policy_fingerprint": stable_hash(policy),
        "source_task": asdict(source_task),
        "return_task": asdict(return_task),
        "proof_evidence_status": (
            "SOURCE_THEOREM_PROMOTION_RUNTIME_WORK_ORDER_NOT_PROOF_EVIDENCE"
        ),
    }
    task = AgentTask(
        task_id="source-theorem-promotion-proofengineer:fixture",
        owner_subsystem=SOURCE_THEOREM_PROMOTION_SUBSYSTEM,
        objective="Route structured exact-candidate generation",
        inputs={
            "question": {"id": "fixture_question"},
            "source_theorem_promotion_work_order_id": work_order_id,
            "source_theorem_promotion_work_order_hash": stable_hash(work_order),
        },
    )
    blackboard = BlackboardState(project_id="fixture")
    blackboard.artifacts[source_manifest_id] = source_manifest
    blackboard.artifacts[work_order_id] = work_order
    worker = SourceTheoremPromotionRuntimeWorker(
        out_root=tmp_path / "runtime",
        repair_available=True,
    )
    return worker, task, blackboard


def _rehash_fixture(task: AgentTask, blackboard: BlackboardState) -> None:
    work_order_id = str(task.inputs["source_theorem_promotion_work_order_id"])
    work_order = blackboard.artifacts[work_order_id]
    source_manifest = blackboard.artifacts[
        work_order["source_formalization_manifest_id"]
    ]
    row = work_order["work_order_rows"][0]
    source_manifest["runtime_source_theorem_promotion_planning_rows"] = [row]
    work_order["source_formalization_manifest_hash"] = stable_hash(source_manifest)
    work_order["work_order_row_hashes"] = [stable_hash(row)]
    task.inputs["source_theorem_promotion_work_order_hash"] = stable_hash(work_order)


def test_promotion_runtime_routes_structured_generation_request_to_llm(
    tmp_path: Path,
) -> None:
    worker, task, blackboard = _runtime_fixture(tmp_path)

    result = worker.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ProofEngineer"
    request = result.next_task.inputs["environment_feedback"][
        "source_theorem_promotion_generation_request"
    ]
    assert request["target_declarations"] == ["exact_source"]
    assert request["target_ids"] == ["source-target:fixture"]
    assert request["next_compiler_subsystem"] == (
        "ExactSourceTheoremProofBodyExecutor"
    )
    assert "signed formal RAG" in request["generation_contract"]


def test_promotion_runtime_never_materializes_or_claims_proof(
    tmp_path: Path,
) -> None:
    worker, task, blackboard = _runtime_fixture(tmp_path)

    result = worker.run(task, blackboard)

    execution = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == SOURCE_THEOREM_PROMOTION_RUNTIME_EXECUTION_KIND
    )
    assert execution["legacy_route_probe_materializer_invoked"] is False
    assert execution["legacy_source_theorem_integrator_invoked"] is False
    assert execution["python_lean_parsing_or_rewrite"] is False
    assert execution["runtime_generated_lean"] is False
    assert execution["source_theorem_kernel_verified"] is False
    assert execution["n_source_theorem_kernel_verified"] == 0


def test_promotion_runtime_rejects_inferred_target_before_llm_route(
    tmp_path: Path,
) -> None:
    worker, task, blackboard = _runtime_fixture(tmp_path)
    work_order = blackboard.artifacts[
        task.inputs["source_theorem_promotion_work_order_id"]
    ]
    work_order["work_order_rows"][0]["target_lean_declaration_source"] = (
        "legacy_lean_scan"
    )
    _rehash_fixture(task, blackboard)

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "source_theorem_promotion_work_order_invalid"
    )
    assert not result.produced_artifacts
    assert "target declaration was inferred" in result.observations[0].summary


def test_promotion_runtime_rejects_candidate_bearing_row(
    tmp_path: Path,
) -> None:
    worker, task, blackboard = _runtime_fixture(tmp_path)
    work_order = blackboard.artifacts[
        task.inputs["source_theorem_promotion_work_order_id"]
    ]
    work_order["work_order_rows"][0]["candidate_artifact_path"] = (
        "/tmp/exact_source.lean"
    )
    work_order["work_order_rows"][0]["candidate_source_hash"] = "candidate-hash"
    _rehash_fixture(task, blackboard)

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert "route it to ExactSourceTheoremProofBodyExecutor" in (
        result.observations[0].summary
    )


def test_promotion_runtime_replays_without_rerouting_generation(
    tmp_path: Path,
) -> None:
    worker, task, blackboard = _runtime_fixture(tmp_path)
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)

    replay = worker.run(task, blackboard)

    assert replay.status == "REVISE"
    assert replay.observations[0].payload["execution_replayed"] is True
    assert replay.observations[0].payload[
        "coding_agent_or_materializer_reexecuted"
    ] is False


def test_promotion_worker_is_agent_runtime_child_before_llm(
    tmp_path: Path,
) -> None:
    worker, task, blackboard = _runtime_fixture(tmp_path)

    class ProofEngineer:
        name = "ProofEngineer"

        def run(self, _task, _blackboard):
            request = _task.inputs["environment_feedback"][
                "source_theorem_promotion_generation_request"
            ]
            assert request["target_declarations"] == ["exact_source"]
            return AgentStepResult(
                status="COMPLETED",
                rationale="LLM ProofEngineer consumed the generation request.",
            )

    result = AgentRuntime(
        subsystems={
            SOURCE_THEOREM_PROMOTION_SUBSYSTEM: worker,
            "ProofEngineer": ProofEngineer(),
        },
        blackboard=blackboard,
    ).run(task, max_iterations=2)

    assert result.status == "COMPLETED"
    assert [trace.subsystem for trace in result.traces] == [
        SOURCE_THEOREM_PROMOTION_SUBSYSTEM,
        "ProofEngineer",
    ]


def test_proofengineer_rejects_tampered_generation_request_before_model_call(
    tmp_path: Path,
) -> None:
    worker, task, blackboard = _runtime_fixture(tmp_path)
    promotion = worker.run(task, blackboard)
    assert promotion.next_task is not None
    blackboard.artifacts.update(promotion.produced_artifacts)
    request_id = str(
        promotion.next_task.inputs[
            "source_theorem_promotion_generation_request_id"
        ]
    )
    blackboard.artifacts[request_id]["target_declarations"] = [
        "changed_after_request_binding"
    ]

    class ExplodingProposalAgent:
        def __init__(self) -> None:
            self.calls = 0

        def propose(self, **_kwargs):
            self.calls += 1
            raise AssertionError("model call must not run after lineage tampering")

    proposal_agent = ExplodingProposalAgent()
    proofengineer = ProofEngineerRuntimeSubsystem(
        proposal_agent=proposal_agent,
        lean_candidate_root=tmp_path / "candidates",
    )

    result = proofengineer.run(promotion.next_task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "source_theorem_promotion_generation_lineage_invalid"
    )
    assert proposal_agent.calls == 0
    failure = next(iter(result.produced_artifacts.values()))
    assert failure["artifact_kind"] == (
        "RuntimeSourceTheoremPromotionGenerationLineageFailure"
    )
    assert "immutable hash mismatch" in " ".join(failure["validation_errors"])
    assert failure["proof_evidence_status"] == (
        "PROMOTION_GENERATION_LINEAGE_REJECTED_NOT_PROOF_EVIDENCE"
    )
