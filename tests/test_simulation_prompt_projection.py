from __future__ import annotations

import json

from ai_statistician import research_agent_runtime as runtime_module
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.scientific_project import (
    normalized_scientific_project_files,
    scientific_project_hash,
)
from ai_statistician.simulation_engineer_llm import (
    LLMSimulationEngineerAgent,
    SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
    SimulationEngineerConfig,
)


def _large_algorithm_handoff() -> dict[str, object]:
    source = (
        "def run_estimator(request):\n"
        "    # SOURCE_SENTINEL_MUST_NOT_REACH_SIMULATION_MODEL\n"
        "    return {'estimate': request['x']}\n"
    )
    smoke_result = {
        "rows": [
            {
                "estimate": float(index),
                "variance": float(index + 1),
                "diagnostic": float(index + 2),
            }
            for index in range(20_000)
        ],
        "private_note": "RESULT_SENTINEL_MUST_NOT_REACH_SIMULATION_MODEL",
    }
    project_files = [
        row.to_json()
        for row in normalized_scientific_project_files(
            [
                {
                    "path": "helper.py",
                    "content": (
                        "# PROJECT_SENTINEL_MUST_NOT_REACH_SIMULATION_MODEL\n"
                        "def transform(value): return value\n"
                    ),
                }
            ],
            language="python",
        )
    ]
    project_hash = scientific_project_hash(
        language="python",
        code=source,
        project_files=project_files,
    )
    return {
        "source": "accepted_algorithm_semantic_review_materialization",
        "algorithm_sandbox_manifest_id": "algorithm:accepted",
        "algorithm_sandbox_manifest_hash": "manifest-hash",
        "semantic_review_execution_id": "review:execution",
        "semantic_review_packet_id": "review:packet",
        "semantic_review_packet_hash": "review-packet-hash",
        "theory_packet_id": "theory:accepted",
        "exact_algorithm_artifacts": [
            {
                "estimator_id": "candidate",
                "language": "python",
                "dependencies": ["numpy"],
                "exact_source_code": source,
                "exact_source_hash": stable_hash(source),
                "exact_project_files": project_files,
                "exact_project_hash": project_hash,
                "exact_smoke_result": smoke_result,
                "exact_smoke_result_hash": stable_hash(smoke_result),
                "estimator_interface_contract_id": "interface:candidate",
                "estimator_interface_contract": {
                    "request_fields": [
                        {"name": "x", "meaning": "Observed scalar", "binding": "replicate"}
                    ],
                    "response_fields": [
                        {
                            "name": "estimate",
                            "meaning": "Adjusted estimate",
                            "normalization": "identity",
                            "sample_size_order": "constant",
                            "derivation_ref": "claim:C1",
                        }
                    ],
                },
            }
        ],
        "consumption_contract": "Execute the exact accepted estimator.",
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        "boundary": "Executable lineage only.",
    }


def test_simulation_intent_projects_large_dependency_artifacts_once() -> None:
    handoff = _large_algorithm_handoff()
    environment_feedback = {
        "upstream_algorithm_handoff": handoff,
        "architect_context": {"upstream_algorithm_handoff": handoff},
        "runtime_requested_evidence_contract": {
            "research_evaluation_requires_generated_simulation_code": True,
        },
    }
    assert len(json.dumps(environment_feedback)) > 1_000_000

    class Provider:
        provider_name = "anthropic"

        @staticmethod
        def generate_client_tool_turn(_request):
            raise AssertionError("intent construction must not start the workspace")

    packet = LLMSimulationEngineerAgent(
        provider=Provider(),
        config=SimulationEngineerConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
        ),
    ).create_source_workspace_intent(
        question=OpenResearchQuestion(
            id="generic-large-handoff",
            title="Generic large dependency handoff",
            description="Design a simulation around one accepted estimator.",
        ),
        theory_packet={},
        n_runs=100,
        seed=7,
        environment_feedback=environment_feedback,
    )
    serialized = json.dumps(packet)
    projected = packet["upstream_algorithm_handoff"]
    artifact = projected["exact_algorithm_artifacts"][0]

    assert len(serialized) < 80_000
    assert "SOURCE_SENTINEL_MUST_NOT_REACH_SIMULATION_MODEL" not in serialized
    assert "RESULT_SENTINEL_MUST_NOT_REACH_SIMULATION_MODEL" not in serialized
    assert "PROJECT_SENTINEL_MUST_NOT_REACH_SIMULATION_MODEL" not in serialized
    assert artifact["estimator_id"] == "candidate"
    assert artifact["estimator_interface_contract"]["response_fields"][0][
        "meaning"
    ] == "Adjusted estimate"
    assert artifact["exact_source_hash"]
    assert artifact["exact_project_hash"]
    assert artifact["project_files"] == [
        {
            "path": "helper.py",
            "content_sha256": handoff["exact_algorithm_artifacts"][0][
                "exact_project_files"
            ][0]["content_sha256"],
        }
    ]
    assert artifact["exact_smoke_result_hash"]
    assert "content" not in artifact["project_files"][0]
    assert "exact_source_code" not in artifact
    assert "exact_smoke_result" not in artifact
    assert projected["exact_source_included"] is False
    assert projected["execution_results_included"] is False
    assert packet["source_workspace_planning_owned"] is True
    assert packet["planning_model_call_used"] is False


def test_accepted_algorithm_handoff_references_smoke_result_by_hash() -> None:
    handoff_fixture = _large_algorithm_handoff()
    artifact = handoff_fixture["exact_algorithm_artifacts"][0]
    source = artifact["exact_source_code"]
    result = artifact["exact_smoke_result"]
    source_row = {
        "estimator_id": "candidate",
        "language": "python",
        "dependencies": ["numpy"],
        "smoke_passed": True,
        "script_hash": stable_hash(source),
        "result_hash": stable_hash(result),
        "project_hash": artifact["exact_project_hash"],
        "algorithm_source_workspace_target": {
            "estimator_interface_contract_id": "interface:candidate",
            "estimator_interface_contract": artifact[
                "estimator_interface_contract"
            ],
        },
    }
    review_material = {
        "exact_executed_artifacts": [
            {
                "artifact_id": "candidate",
                "source_row": source_row,
                "exact_source_code": source,
                "exact_source_hash": stable_hash(source),
                "exact_project_files": artifact["exact_project_files"],
                "exact_project_hash": artifact["exact_project_hash"],
                "exact_project_files_complete": True,
                "exact_result": result,
                "exact_result_hash": stable_hash(result),
            }
        ]
    }

    handoff = runtime_module._runtime_accepted_algorithm_handoff_from_review(
        question_id="generic-large-handoff",
        theory_packet_id="theory:accepted",
        source_manifest={"manifest_id": "algorithm:accepted"},
        review_material=review_material,
        execution_manifest={
            "execution_id": "review:execution",
            "materialization_id": "materialization:accepted",
            "materialization_hash": stable_hash(review_material),
        },
        review_packet={"packet_id": "review:packet", "overall_verdict": "ACCEPT"},
    )
    projected = handoff["exact_algorithm_artifacts"][0]

    assert projected["exact_source_code"] == source
    assert projected["exact_source_hash"] == stable_hash(source)
    assert projected["exact_project_hash"] == artifact["exact_project_hash"]
    assert projected["exact_project_files"] == artifact["exact_project_files"]
    assert projected["exact_smoke_result_hash"] == stable_hash(result)
    assert "exact_smoke_result" not in projected
    assert len(json.dumps(handoff)) < 25_000


def test_executable_evaluator_workspace_makes_source_the_preregistration() -> None:
    workspace_prompt = SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    assert "small non-confirmatory tool" in workspace_prompt
    assert "never reject or" in workspace_prompt
    assert "acceptance_passed may be false" in workspace_prompt
    assert "top-level" in workspace_prompt
    assert "run_sandbox result, not an input-validation name" in workspace_prompt
    assert (
        "compact Theory or handoff summaries cannot weaken it"
        in workspace_prompt
    )
