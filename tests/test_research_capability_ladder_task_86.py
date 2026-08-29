from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
TASK_ID = "chapman_capture_recapture_bias_r_known_result"


def test_chapman_r_l0_task_records_immutable_consumed_result() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "capture_recapture_hypergeometric_bias_r"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_hidden_theory_failed_code_and_empirical_passed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-chapman-capture-recapture-r-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "06a396b8af4db496bf274fc895adb79e30323b8baa6a2dc49bd8ed2474b84078"
    )
    assert candidate["gold_descriptor_hash"] == (
        "c58242c5e0f18761a0e7124844ad7d90a9b7617f1ab3a8f18ee5e5345c84a595"
    )
    assert evidence["visible_question_activation_commit"] == (
        "6a610cd1462972a29f5ef2984d7cb6bfbdb436e2"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 5
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 8
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["semantic_calibration_cases_correct"] == 6
    assert evidence["semantic_reference_claims_satisfied"] == 7
    assert evidence["algorithm_reference_contract_checks_passed"] is True
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["empirical_reference_designs_passed"] == 3
    assert evidence["empirical_reference_replicates_per_design"] == 12000
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 8
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["required_model_owned_estimator_language"] == "r"
    assert evidence["required_model_owned_simulation_language"] == "r"
    assert evidence["scientific_execution_profile"] == "scientific_wasm"
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["theory_developer_executed"] is True
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["activation_ledger_commit"] == (
        "60b0b731a266bdd34c0647b1588f7f4b7fdf802b"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "generated_code_semantic_review_packet_invalid"
    )
    assert evidence["runtime_product_model_turns"] == 81
    assert evidence["post_runtime_gold_model_calls"] == 1
    assert evidence["hidden_algorithm_checks_passed"] is True
    assert evidence["hidden_theory_mechanical_checks_passed"] is True
    assert evidence["hidden_theory_semantic_passed"] is False
    assert evidence["hidden_empirical_checks_passed"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["post_run_shared_mechanism_commit"] == (
        "9606ac34c19129ee7ec53808a8ccfb7b6b018374"
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == TASK_ID
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_chapman_capture_recapture"
    assert [row["name"] for row in contract["request_fields"]] == [
        "first_sample_size",
        "second_sample_size",
        "overlap",
    ]
    assert [row["name"] for row in contract["response_fields"]] == [
        "population_estimate"
    ]
    assert "language=r" in question["description"]
    assert "A=(N=60,n1=35,n2=30)" in question["description"]
    assert "B=(N=200,n1=40,n2=50)" in question["description"]
    assert "C=(N=80,n1=8,n2=12)" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "reference_estimator.R",
        "negative_petersen.R",
        "negative_wrong_shift.R",
        "negative_permissive.R",
        "semantic_reference.md",
        "candidate_mode_near_miss.md",
        "hidden_algorithm_harness.R",
        "hidden_empirical_harness.R",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 99
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 99
    assert readiness["fully_gold_configured_tasks"] == 99
    assert readiness["fully_gold_passed_tasks"] == 7
