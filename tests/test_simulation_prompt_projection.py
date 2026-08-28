from __future__ import annotations

import json

from ai_statistician import research_agent_runtime as runtime_module
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.simulation_engineer_llm import (
    SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
    build_simulation_engineer_prompt,
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


def test_simulation_prompt_projects_large_dependency_artifacts_once() -> None:
    handoff = _large_algorithm_handoff()
    environment_feedback = {
        "upstream_algorithm_handoff": handoff,
        "architect_context": {"upstream_algorithm_handoff": handoff},
        "runtime_requested_evidence_contract": {
            "research_evaluation_requires_generated_simulation_code": True,
        },
    }
    assert len(json.dumps(environment_feedback)) > 1_000_000

    prompt = build_simulation_engineer_prompt(
        question=OpenResearchQuestion(
            id="generic-large-handoff",
            title="Generic large dependency handoff",
            description="Design a simulation around one accepted estimator.",
        ),
        theory_packet={},
        registered_problem={},
        registered_procedures=[],
        n_runs=100,
        seed=7,
        environment_feedback=environment_feedback,
        defer_source_authoring=True,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    projected = payload["upstream_algorithm_handoff"]
    artifact = projected["exact_algorithm_artifacts"][0]

    assert len(prompt) < 80_000
    assert "SOURCE_SENTINEL_MUST_NOT_REACH_SIMULATION_MODEL" not in prompt
    assert "RESULT_SENTINEL_MUST_NOT_REACH_SIMULATION_MODEL" not in prompt
    assert artifact["estimator_id"] == "candidate"
    assert artifact["estimator_interface_contract"]["response_fields"][0][
        "meaning"
    ] == "Adjusted estimate"
    assert artifact["exact_source_hash"]
    assert artifact["exact_smoke_result_hash"]
    assert "exact_source_code" not in artifact
    assert "exact_smoke_result" not in artifact
    assert projected["exact_source_included"] is False
    assert projected["execution_results_included"] is False
    assert "upstream_algorithm_handoff" not in json.dumps(
        payload["runtime_environment_feedback"]
    )


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
        "llm_algorithm_engineer_target": {
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
    assert projected["exact_smoke_result_hash"] == stable_hash(result)
    assert "exact_smoke_result" not in projected
    assert len(json.dumps(handoff)) < 25_000


def test_executable_evaluator_prompt_makes_source_the_preregistration() -> None:
    prompt = build_simulation_engineer_prompt(
        question=OpenResearchQuestion(
            id="generic-executable-evaluator",
            title="Generic executable evaluator",
            description="Evaluate one theory claim without a prose translation step.",
        ),
        theory_packet={},
        registered_problem={},
        registered_procedures=[],
        n_runs=100_000,
        seed=7,
        environment_feedback={
            "executable_evaluator_source_authority": True,
            "empirical_evaluation_phase": "executable_evaluator_authoring",
            "runtime_requested_evidence_contract": {
                "research_evaluation_requires_generated_simulation_code": True,
            },
        },
        defer_source_authoring=True,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert payload["authoritative_empirical_metric_requirements"] == []
    assert payload["required_output_contract"]["metric_contracts"] == []
    assert "exact source the complete executable preregistration" in prompt
    assert "requested_runtime_replicates" in prompt
    assert "SimulationEngineer later implements" not in prompt
    workspace_prompt = SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    assert "small non-confirmatory tool" in workspace_prompt
    assert "never reject or" in workspace_prompt
    assert "acceptance_passed may be false" in workspace_prompt
    assert (
        "compact Theory or handoff summaries cannot weaken it"
        in workspace_prompt
    )
