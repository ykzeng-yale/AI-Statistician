from __future__ import annotations

from copy import deepcopy

from ai_statistician import research_agent_runtime as runtime_module
from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.fingerprint import stable_hash


QUESTION_ID = "generic-canonical-algorithm-handoff"
THEORY_PACKET_ID = "theory:generic-canonical-algorithm-handoff"
MANIFEST_ID = "algorithm:generic-canonical-algorithm-handoff"
MATERIALIZATION_ID = "materialization:generic-canonical-algorithm-handoff"
PACKET_ID = "review-packet:generic-canonical-algorithm-handoff"
EXECUTION_ID = "review-execution:generic-canonical-algorithm-handoff"


def _canonical_handoff_fixture() -> tuple[AgentTask, BlackboardState, dict, dict]:
    source = "def run_estimator(request):\n    return {'estimate': request['x']}\n"
    result = {"estimate": 1.0}
    source_manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": MANIFEST_ID,
        "theory_packet_id": THEORY_PACKET_ID,
        "n_generated_code_executed": 1,
        "n_passed": 1,
    }
    review_material = {
        "exact_executed_artifacts": [
            {
                "artifact_id": "estimator:generic",
                "source_row": {
                    "estimator_id": "estimator:generic",
                    "language": "python",
                    "dependencies": [],
                    "smoke_passed": True,
                    "script_hash": stable_hash(source),
                    "result_hash": stable_hash(result),
                },
                "exact_source_code": source,
                "exact_source_hash": stable_hash(source),
                "exact_result": result,
                "exact_result_hash": stable_hash(result),
            }
        ]
    }
    review_input_fingerprint = stable_hash(review_material)
    materialization = {
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewMaterialization",
        "materialization_id": MATERIALIZATION_ID,
        "question_id": QUESTION_ID,
        "review_input_fingerprint": review_input_fingerprint,
        "exact_algorithm_artifacts": (
            runtime_module._runtime_exact_algorithm_artifacts(review_material)
        ),
        "full_review_material_persisted": False,
    }
    packet = {
        "packet_id": PACKET_ID,
        "overall_verdict": "ACCEPT",
        "review_input_fingerprint": review_input_fingerprint,
    }
    execution = {
        "execution_id": EXECUTION_ID,
        "semantic_review_accepted": True,
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": MANIFEST_ID,
        "source_manifest_hash": stable_hash(source_manifest),
        "review_packet_hash": stable_hash(packet),
        "materialization_id": MATERIALIZATION_ID,
        "materialization_hash": stable_hash(materialization),
        "review_input_fingerprint": review_input_fingerprint,
    }
    handoff = runtime_module._runtime_accepted_algorithm_handoff_from_review(
        question_id=QUESTION_ID,
        theory_packet_id=THEORY_PACKET_ID,
        source_manifest=source_manifest,
        review_material=review_material,
        execution_manifest=execution,
        review_packet=packet,
    )
    task = AgentTask(
        task_id="simulation:generic-canonical-algorithm-handoff",
        owner_subsystem="SimulationEvaluator",
        objective="Consume one exact independently reviewed estimator.",
        inputs={"upstream_algorithm_handoff": handoff},
    )
    blackboard = BlackboardState(
        project_id=QUESTION_ID,
        artifacts={
            MANIFEST_ID: source_manifest,
            MATERIALIZATION_ID: materialization,
            PACKET_ID: packet,
            EXECUTION_ID: execution,
        },
    )
    return task, blackboard, handoff, review_material


def _validate(task: AgentTask, blackboard: BlackboardState) -> dict:
    return runtime_module._runtime_validated_algorithm_handoff(
        task=task,
        blackboard=blackboard,
        question_id=QUESTION_ID,
        theory_packet_id=THEORY_PACKET_ID,
        algorithm_sandbox_manifest_id=MANIFEST_ID,
    )


def test_algorithm_handoff_requires_task_owned_canonical_materialization() -> None:
    task, blackboard, handoff, _ = _canonical_handoff_fixture()

    assert _validate(task, blackboard) == handoff

    context_only = AgentTask(
        task_id=task.task_id,
        owner_subsystem=task.owner_subsystem,
        objective=task.objective,
        inputs={"architect_context": {"upstream_algorithm_handoff": handoff}},
    )
    assert _validate(context_only, blackboard) == {}


def test_algorithm_handoff_rejects_nested_legacy_review_material() -> None:
    task, blackboard, handoff, review_material = _canonical_handoff_fixture()
    legacy_materialization = deepcopy(blackboard.artifacts[MATERIALIZATION_ID])
    legacy_materialization.pop("exact_algorithm_artifacts")
    legacy_materialization["review_material"] = review_material
    legacy_materialization["full_review_material_persisted"] = True
    legacy_execution = deepcopy(blackboard.artifacts[EXECUTION_ID])
    legacy_execution["materialization_hash"] = stable_hash(legacy_materialization)
    legacy_handoff = deepcopy(handoff)
    legacy_handoff["materialization_hash"] = stable_hash(legacy_materialization)
    legacy_task = AgentTask(
        task_id=task.task_id,
        owner_subsystem=task.owner_subsystem,
        objective=task.objective,
        inputs={"upstream_algorithm_handoff": legacy_handoff},
    )
    legacy_blackboard = BlackboardState(
        project_id=QUESTION_ID,
        artifacts={
            **blackboard.artifacts,
            MATERIALIZATION_ID: legacy_materialization,
            EXECUTION_ID: legacy_execution,
        },
    )

    assert _validate(legacy_task, legacy_blackboard) == {}
