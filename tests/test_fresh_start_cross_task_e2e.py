from __future__ import annotations

from copy import deepcopy

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.fresh_start_cross_task_e2e import (
    audit_fresh_start_cross_task_e2e,
)
from ai_statistician.research_agent_runtime import (
    _generated_sandbox_feedback_id,
    _generated_sandbox_prototype_artifact_id,
)


def _theory_contract(packet_id: str, consumer: str) -> dict[str, object]:
    return {
        "artifact_kind": "TheoryTraceConsumptionContract",
        "source_theory_packet_id": packet_id,
        "consumer_subsystem": consumer,
        "theory_derivation_trace_supplied": True,
        "n_derivation_steps_supplied": 3,
        "n_equation_chain_steps_supplied": 2,
        "n_assumption_ledger_rows_supplied": 2,
        "has_formalization_handoff": True,
    }


def _complete_task(
    question_id: str,
    task_family: str,
) -> tuple[dict[str, object], dict[str, object]]:
    packet_id = f"theory_derivation:{question_id}"
    simulation_id = f"simulation_manifest:{question_id}"
    algorithm_id = f"algorithm_sandbox_manifest:{question_id}"
    formalization_id = f"formalization_manifest:{question_id}"
    target_id = f"{question_id}:source_theorem"
    lineage_id = f"source_lineage:{question_id}"
    proof_manifest_id = f"external_exact_proof_candidate_rerun:{question_id}"
    proof_state_feedback_id = f"proof_state_feedback:{question_id}"
    question = {"id": question_id, "tags": [f"task_family:{task_family}"]}
    algorithm_failed_id = f"algorithm_sandbox_manifest:{question_id}:failed"
    simulation_failed_id = f"simulation_manifest:{question_id}:failed"
    algorithm_failed_prototype = {
        "estimator_id": f"algorithm:{question_id}",
        "executor": "generated_python_sandbox",
        "prototype_status": "FAILED",
        "script_hash": stable_hash(f"bad algorithm code:{question_id}"),
        "smoke_passed": False,
        "execution_smoke_passed": False,
        "stderr_summary": "NameError: generated estimator did not execute",
        "source_llm_proposal_id": f"algorithm_proposal:{question_id}:failed",
        "source_llm_proposal_provider": "anthropic",
        "source_llm_proposal_backend_provider": "anthropic",
        "source_llm_proposal_live_generator": True,
    }
    algorithm_failed_prototype["prototype_artifact_id"] = (
        _generated_sandbox_prototype_artifact_id(algorithm_failed_prototype)
    )
    algorithm_feedback_id = _generated_sandbox_feedback_id(
        feedback_type="algorithm_sandbox_execution_feedback",
        source_manifest_id=algorithm_failed_id,
        failure_classification="generated_algorithm_sandbox_execution_failed",
        prototype_rows=[algorithm_failed_prototype],
    )
    algorithm_passed_prototype = {
        "estimator_id": f"algorithm:{question_id}",
        "executor": "generated_python_sandbox",
        "prototype_status": "EXECUTED",
        "script_hash": stable_hash(f"repaired algorithm code:{question_id}"),
        "smoke_passed": True,
        "source_llm_proposal_id": f"algorithm_proposal:{question_id}:repaired",
        "source_llm_proposal_provider": "anthropic",
        "source_llm_proposal_backend_provider": "anthropic",
        "source_llm_proposal_live_generator": True,
    }
    algorithm_passed_prototype["prototype_artifact_id"] = (
        _generated_sandbox_prototype_artifact_id(algorithm_passed_prototype)
    )
    algorithm_passed_prototype["repair_lineage"] = {
        "feedback_id": algorithm_feedback_id,
        "feedback_type": "algorithm_sandbox_execution_feedback",
        "feedback_failure_classification": (
            "generated_algorithm_sandbox_execution_failed"
        ),
        "parent_manifest_id": algorithm_failed_id,
        "parent_prototype_artifact_ids": [
            algorithm_failed_prototype["prototype_artifact_id"]
        ],
        "parent_script_hashes": [algorithm_failed_prototype["script_hash"]],
        "child_prototype_artifact_id": algorithm_passed_prototype[
            "prototype_artifact_id"
        ],
        "child_script_hash": algorithm_passed_prototype["script_hash"],
        "child_proposal_id": algorithm_passed_prototype[
            "source_llm_proposal_id"
        ],
        "feedback_supplied_to_generator": True,
        "lineage_contract_complete": True,
    }
    simulation_failed_prototype = {
        "simulation_id": f"simulation:{question_id}",
        "executor": "generated_simulation_sandbox",
        "prototype_status": "FAILED_METRIC_GATE",
        "script_hash": stable_hash(f"bad simulation code:{question_id}"),
        "smoke_passed": False,
        "metric_gate_errors": ["coverage below target"],
        "source_llm_proposal_id": f"simulation_proposal:{question_id}:failed",
        "source_llm_proposal_provider": "anthropic",
        "source_llm_proposal_backend_provider": "anthropic",
        "source_llm_proposal_live_generator": True,
    }
    simulation_failed_prototype["prototype_artifact_id"] = (
        _generated_sandbox_prototype_artifact_id(simulation_failed_prototype)
    )
    simulation_feedback_id = _generated_sandbox_feedback_id(
        feedback_type="generated_simulation_sandbox_execution_feedback",
        source_manifest_id=simulation_failed_id,
        failure_classification="generated_simulation_sandbox_metric_gate_failed",
        prototype_rows=[simulation_failed_prototype],
    )
    simulation_passed_prototype = {
        "simulation_id": f"simulation:{question_id}",
        "executor": "generated_simulation_sandbox",
        "prototype_status": "EXECUTED",
        "script_hash": stable_hash(f"repaired simulation code:{question_id}"),
        "smoke_passed": True,
        "source_llm_proposal_id": f"simulation_proposal:{question_id}:repaired",
        "source_llm_proposal_provider": "anthropic",
        "source_llm_proposal_backend_provider": "anthropic",
        "source_llm_proposal_live_generator": True,
    }
    simulation_passed_prototype["prototype_artifact_id"] = (
        _generated_sandbox_prototype_artifact_id(simulation_passed_prototype)
    )
    simulation_passed_prototype["repair_lineage"] = {
        "feedback_id": simulation_feedback_id,
        "feedback_type": "generated_simulation_sandbox_execution_feedback",
        "feedback_failure_classification": (
            "generated_simulation_sandbox_metric_gate_failed"
        ),
        "parent_manifest_id": simulation_failed_id,
        "parent_prototype_artifact_ids": [
            simulation_failed_prototype["prototype_artifact_id"]
        ],
        "parent_script_hashes": [simulation_failed_prototype["script_hash"]],
        "child_prototype_artifact_id": simulation_passed_prototype[
            "prototype_artifact_id"
        ],
        "child_script_hash": simulation_passed_prototype["script_hash"],
        "child_proposal_id": simulation_passed_prototype[
            "source_llm_proposal_id"
        ],
        "feedback_supplied_to_generator": True,
        "lineage_contract_complete": True,
    }
    artifacts: dict[str, object] = {
        f"architect_coordinator_proposal:{question_id}": {
            "artifact_kind": "ArchitectCoordinatorProposalPacket",
            "packet_id": f"architect_coordinator_proposal:{question_id}",
            "provider": "anthropic",
            "backend_provider": "anthropic",
            "ok": True,
            "question": question,
            "subsystem_execution_plan": [
                {"subsystem": "TheoryDeveloper", "acceptance_gate": "structured theory"}
            ],
        },
        packet_id: {
            "artifact_kind": "TheoryDerivationPacket",
            "packet_id": packet_id,
            "provider": "anthropic",
            "backend_provider": "anthropic",
            "ok": True,
            "question": question,
            "theory_derivation_packet": {
                "derivation_steps": [
                    {"id": "D1", "claim": "identify target"},
                    {"id": "D2", "claim": "derive estimator"},
                    {"id": "D3", "claim": "bound remainder"},
                ],
                "equation_chain": [
                    {"step_id": "E1", "lhs": "theta_hat", "rhs": "theta + R1"},
                    {"step_id": "E2", "lhs": "R1", "rhs": "o_p(1)"},
                ],
                "assumption_ledger": [
                    {"assumption": "regularity A", "used_in": ["D1"]},
                    {"assumption": "regularity B", "used_in": ["D3"]},
                ],
                "formalization_handoff": {
                    "source_theorem_target": target_id,
                    "semantic_alignment_constraints": ["preserve exact target"],
                },
            },
        },
        f"retrieval_memory_manifest:{question_id}": {
            "artifact_kind": "RuntimeRetrievalMemoryManifest",
            "question": question,
            "counts": {"formal_source_hits": 1},
            "formal_source_hits": [
                {
                    "theorem_goal_id": target_id,
                    "hits": [
                        {
                            "source_id": "local_formal_library",
                            "path": "FormalLibrary/Source.lean",
                            "name": target_id,
                        }
                    ],
                }
            ],
        },
        simulation_failed_id: {
            "artifact_kind": "RuntimeSimulationManifest",
            "manifest_id": simulation_failed_id,
            "created_at": "2026-07-12T00:00:01Z",
            "question": question,
            "theory_packet_id": packet_id,
            "generated_simulation_sandbox_prototypes": [
                simulation_failed_prototype
            ],
            "n_generated_simulation_sandbox_metric_gate_failed": 1,
        },
        simulation_id: {
            "artifact_kind": "RuntimeSimulationManifest",
            "manifest_id": simulation_id,
            "created_at": "2026-07-12T00:00:02Z",
            "question": question,
            "theory_packet_id": packet_id,
            "n_live_generated_simulation_sandbox_executed": 1,
            "n_live_generated_simulation_sandbox_passed": 1,
            "confirmatory_empirical_evidence_eligible": True,
            "generated_simulation_sandbox_prototypes": [
                simulation_passed_prototype
            ],
            "theory_trace_consumption_contract": _theory_contract(
                packet_id, "SimulationEngineer"
            ),
        },
        algorithm_failed_id: {
            "artifact_kind": "RuntimeAlgorithmSandboxManifest",
            "manifest_id": algorithm_failed_id,
            "created_at": "2026-07-12T00:00:03Z",
            "question": question,
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_id,
            "prototypes": [algorithm_failed_prototype],
            "n_generated_code_execution_failed": 1,
        },
        algorithm_id: {
            "artifact_kind": "RuntimeAlgorithmSandboxManifest",
            "manifest_id": algorithm_id,
            "created_at": "2026-07-12T00:00:04Z",
            "question": question,
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_id,
            "n_live_generated_code_executed": 1,
            "n_passed": 1,
            "prototypes": [algorithm_passed_prototype],
            "theory_trace_consumption_contract": _theory_contract(
                packet_id, "AlgorithmEngineer"
            ),
        },
        f"generated_code_semantic_review_execution:{question_id}:algorithm": {
            "artifact_kind": (
                "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
            ),
            "execution_id": (
                f"generated_code_semantic_review_execution:{question_id}:algorithm"
            ),
            "question_id": question_id,
            "source_subsystem": "AlgorithmEngineer",
            "source_manifest_id": algorithm_id,
            "semantic_review_accepted": True,
            "independent_agent": True,
            "independent_invocation": True,
            "independent_model": True,
            "reviewer_model_tier": "sonnet",
            "confirmatory_empirical_evidence_eligible": True,
        },
        f"generated_code_semantic_review_execution:{question_id}:simulation": {
            "artifact_kind": (
                "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
            ),
            "execution_id": (
                f"generated_code_semantic_review_execution:{question_id}:simulation"
            ),
            "question_id": question_id,
            "source_subsystem": "SimulationEvaluator",
            "source_manifest_id": simulation_id,
            "semantic_review_accepted": True,
            "independent_agent": True,
            "independent_invocation": True,
            "independent_model": True,
            "reviewer_model_tier": "sonnet",
            "confirmatory_empirical_evidence_eligible": True,
        },
        f"formalizer_proposal:{question_id}": {
            "artifact_kind": "FormalizerProofEngineerProposalPacket",
            "packet_id": f"formalizer_proposal:{question_id}",
            "provider": "anthropic",
            "backend_provider": "anthropic",
            "ok": True,
            "question": question,
            "theory_trace_consumption_contract": _theory_contract(
                packet_id, "FormalizerProofEngineer"
            ),
        },
        formalization_id: {
            "artifact_kind": "RuntimeFormalizationManifest",
            "manifest_id": formalization_id,
            "question": question,
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_id,
            "algorithm_sandbox_manifest_id": algorithm_id,
            "proof_state_feedback_manifest_id": proof_state_feedback_id,
            "full_frontier_current_target_ids": [target_id],
            "counts": {"formal_gap": 0},
        },
        proof_state_feedback_id: {
            "artifact_kind": "RuntimeFormalizerLeanCandidateProofStateFeedbackManifest",
            "manifest_id": proof_state_feedback_id,
            "question": question,
            "lean_lsp_mcp_live_called": True,
            "source_materialization_manifest_id": f"materialization:{question_id}",
        },
        proof_manifest_id: {
            "artifact_kind": "RuntimeExternalExactProofCandidateRerunManifest",
            "manifest_id": proof_manifest_id,
            "execution_id": f"proof_execution:{question_id}",
            "input_fingerprint": f"input-fingerprint-{question_id}",
            "question_id": question_id,
            "source_lineage_id": lineage_id,
            "source_task_id": f"proof_task:{question_id}",
            "source_work_order_id": f"proof_work_order:{question_id}",
            "execution_queue_id": f"proof_queue:{question_id}",
            "provider": "openprover_hlm_controller",
            "provider_result_id": f"openprover_result:{question_id}",
            "n_runtime_generated_proof_bodies": 0,
            "proof_body_generation_contract": {
                "mode": "llm_zero_shot_with_lean_compile_feedback",
                "compiler_feedback_retry": True,
                "static_tactic_fallback": False,
            },
            "source_theorem_kernel_verified": True,
            "n_source_theorem_kernel_verified": 1,
            "n_local_lean_checked": 1,
            "n_local_lean_compiled": 1,
            "source_theorem_kernel_verified_target_ids": [target_id],
            "rows": [
                {
                    "question_id": question_id,
                    "source_lineage_id": lineage_id,
                    "candidate_origin": "external_llm_or_prover_provider",
                    "runtime_generated_proof_body": False,
                    "target_ids": [target_id],
                    "exact_signature_preserved": True,
                    "local_lean_checked": True,
                    "local_lean_compiled": True,
                    "source_theorem_kernel_verified": True,
                }
            ],
        },
    }
    result = {
        "status": "ACCEPTED",
        "final_task_id": f"critic:{question_id}",
        "blackboard": {
            "project_id": f"ai_statistician:{question_id}",
            "artifacts": artifacts,
        },
        "traces": [
            {
                "iteration": 1,
                "subsystem": "ArchitectCoordinator",
                "status": "REROUTE",
            }
        ],
    }
    summary = {
        "question_id": question_id,
        "task_family": task_family,
        "ok": True,
        "errors": [],
        "architect_coordinator_enabled": True,
        "n_live_generated_code_sandbox_executed": 1,
        "n_live_generated_simulation_sandbox_executed": 1,
        "n_live_generated_code_sandbox_failed_then_passed_repair_sequences": 1,
        "n_live_generated_simulation_sandbox_failed_then_passed_repair_sequences": 1,
        "n_lean_lsp_mcp_live_calls": 1,
        "n_formal_gaps": 0,
    }
    return result, summary


def _complete_suite() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    causal = _complete_task("causal_ate_holdout", "causal")
    multiple_testing = _complete_task("online_fdr_holdout", "multiple_testing")
    manifest = {
        "runtime_resume_policy": "fresh_start",
        "runtime_resumed_from_pending_task": False,
        "runtime_resume_context": {"resumed_from_pending_task": False},
        "runtime_input_context": {
            "runtime_learning_memory_supplied": False,
            "runtime_learning_memory_rows_loaded": 0,
        },
        "n_live_generator_agents_enabled": 7,
        "n_static_generator_agents_enabled": 0,
        "unsupported_generator_backends_enabled": 0,
    }
    return manifest, [causal[0], multiple_testing[0]], [causal[1], multiple_testing[1]]


def test_fresh_start_cross_task_e2e_requires_two_complete_per_task_lineages() -> None:
    manifest, results, summaries = _complete_suite()

    audit = audit_fresh_start_cross_task_e2e(
        runtime_manifest=manifest,
        result_payloads=results,
        row_summaries=summaries,
    )

    assert audit["cross_task_full_e2e_generalization_demonstrated"] is True
    assert audit["n_complete_tasks"] == 2
    assert audit["complete_task_families"] == ["causal", "multiple_testing"]
    assert all(row["complete"] is True for row in audit["task_rows"])
    assert len(audit["complete_source_proof_lineage_ids"]) == 2


def test_fresh_start_cross_task_e2e_accepts_first_pass_correct_agents() -> None:
    manifest, results, summaries = _complete_suite()
    for result, summary in zip(results, summaries, strict=True):
        artifacts = result["blackboard"]["artifacts"]
        for artifact_id in list(artifacts):
            if artifact_id.endswith(":failed"):
                del artifacts[artifact_id]
        for artifact in artifacts.values():
            if not isinstance(artifact, dict):
                continue
            for key in ("prototypes", "generated_simulation_sandbox_prototypes"):
                for prototype in artifact.get(key, []) or []:
                    if isinstance(prototype, dict):
                        prototype.pop("repair_lineage", None)
        summary[
            "n_live_generated_code_sandbox_failed_then_passed_repair_sequences"
        ] = 0
        summary[
            "n_live_generated_simulation_sandbox_failed_then_passed_repair_sequences"
        ] = 0

    audit = audit_fresh_start_cross_task_e2e(
        runtime_manifest=manifest,
        result_payloads=results,
        row_summaries=summaries,
    )

    assert audit["cross_task_full_e2e_generalization_demonstrated"] is True
    assert all(row["algorithm_failure_observed"] is False for row in audit["task_rows"])
    assert all(row["simulation_failure_observed"] is False for row in audit["task_rows"])


@pytest.mark.parametrize(
    ("mutation", "missing_gate"),
    [
        ("resume", None),
        ("same_family", None),
        ("aggregate_only_repair", "algorithm_feedback_closed_if_failure_observed"),
        ("same_script_replay", "algorithm_feedback_closed_if_failure_observed"),
        ("forged_prototype_id", "algorithm_feedback_closed_if_failure_observed"),
        ("cross_task_feedback", "algorithm_feedback_closed_if_failure_observed"),
        ("proof_target_drift", "exact_source_theorem_kernel_verified"),
        ("runtime_generated_proof", "exact_source_theorem_kernel_verified"),
        ("fixture_provider", "exact_source_theorem_kernel_verified"),
    ],
)
def test_fresh_start_cross_task_e2e_fails_closed(
    mutation: str,
    missing_gate: str | None,
) -> None:
    manifest, results, summaries = _complete_suite()
    manifest = deepcopy(manifest)
    results = deepcopy(results)
    summaries = deepcopy(summaries)

    if mutation == "resume":
        manifest["runtime_resume_policy"] = "direct_pending_task"
        manifest["runtime_resumed_from_pending_task"] = True
    elif mutation == "same_family":
        summaries[1]["task_family"] = "causal"
    elif mutation == "aggregate_only_repair":
        algorithm_manifest = next(
            row
            for row in results[1]["blackboard"]["artifacts"].values()
            if row.get("artifact_kind") == "RuntimeAlgorithmSandboxManifest"
            and row.get("n_passed") == 1
        )
        algorithm_manifest["prototypes"][0].pop("repair_lineage")
    elif mutation in {
        "same_script_replay",
        "forged_prototype_id",
        "cross_task_feedback",
    }:
        second_artifacts = results[1]["blackboard"]["artifacts"]
        failed_manifest = next(
            row
            for row in second_artifacts.values()
            if row.get("artifact_kind") == "RuntimeAlgorithmSandboxManifest"
            and row.get("n_passed") is None
        )
        passed_manifest = next(
            row
            for row in second_artifacts.values()
            if row.get("artifact_kind") == "RuntimeAlgorithmSandboxManifest"
            and row.get("n_passed") == 1
        )
        failed_prototype = failed_manifest["prototypes"][0]
        passed_prototype = passed_manifest["prototypes"][0]
        lineage = passed_prototype["repair_lineage"]
        if mutation == "same_script_replay":
            passed_prototype["script_hash"] = failed_prototype["script_hash"]
            passed_prototype["prototype_artifact_id"] = (
                _generated_sandbox_prototype_artifact_id(passed_prototype)
            )
            lineage["child_script_hash"] = passed_prototype["script_hash"]
            lineage["child_prototype_artifact_id"] = passed_prototype[
                "prototype_artifact_id"
            ]
        elif mutation == "forged_prototype_id":
            passed_prototype["prototype_artifact_id"] = "forged:prototype"
        else:
            first_artifacts = results[0]["blackboard"]["artifacts"]
            foreign_manifest = next(
                row
                for row in first_artifacts.values()
                if row.get("artifact_kind") == "RuntimeAlgorithmSandboxManifest"
                and row.get("n_passed") is None
            )
            foreign_prototype = foreign_manifest["prototypes"][0]
            lineage["parent_manifest_id"] = foreign_manifest["manifest_id"]
            lineage["parent_prototype_artifact_ids"] = [
                foreign_prototype["prototype_artifact_id"]
            ]
            lineage["parent_script_hashes"] = [foreign_prototype["script_hash"]]
            lineage["feedback_id"] = _generated_sandbox_feedback_id(
                feedback_type="algorithm_sandbox_execution_feedback",
                source_manifest_id=foreign_manifest["manifest_id"],
                failure_classification=(
                        "generated_algorithm_sandbox_execution_failed"
                ),
                prototype_rows=[foreign_prototype],
            )
    else:
        proof = next(
            row
            for row in results[1]["blackboard"]["artifacts"].values()
            if row.get("artifact_kind")
            == "RuntimeExternalExactProofCandidateRerunManifest"
        )
        if mutation == "proof_target_drift":
            proof["source_theorem_kernel_verified_target_ids"] = ["other:target"]
        elif mutation == "runtime_generated_proof":
            proof["n_runtime_generated_proof_bodies"] = 1
            proof["rows"][0]["runtime_generated_proof_body"] = True
        elif mutation == "fixture_provider":
            proof["provider"] = "openprover_fixture_payload"

    audit = audit_fresh_start_cross_task_e2e(
        runtime_manifest=manifest,
        result_payloads=results,
        row_summaries=summaries,
    )

    assert audit["cross_task_full_e2e_generalization_demonstrated"] is False
    if missing_gate:
        assert missing_gate in audit["task_rows"][1]["missing_requirements"]
