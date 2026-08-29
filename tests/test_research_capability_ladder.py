from __future__ import annotations

import hashlib
import json
from pathlib import Path


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
LATEST_SHARED_MECHANISM_HEAD = "2a988ca8a86030d90e790530db22ea38138f3259"
TASK_79_ACTIVATION_LEDGER_HEAD = "a6745543c662200fb39806cea5bb970532357cf0"
TASK_79_SHARED_MECHANISM_HEAD = "492d11120fbae8b630fa01af8bb11d6da131f5b9"
TASK_80_ACTIVATION_LEDGER_HEAD = "eb6ddd325f7d8969c1f446c97ceb56860b9a4add"
TASK_80_SHARED_MECHANISM_HEAD = "1ebed16db58f8edb8e3658eb94f693ce1a14223a"
TASK_81_ACTIVATION_LEDGER_HEAD = "2c8478731c9e0472227342b1fd1f30ead752d9b8"
TASK_82_ACTIVATION_LEDGER_HEAD = "6623cee3f6f4a1540c4c258fdb9181e740fecf7c"
TASK_78_SHARED_MECHANISM_HEAD = "81349094a4d8b67dbc1e744c7b45aba6a7c448b4"
TASK_77_ACTIVATION_LEDGER_HEAD = "a16fc8bd1ce52638770fcfec52356c7c538f6a76"
TASK_75_SHARED_MECHANISM_HEAD = "af132404602d0c9ce621b47c979a90424ffa4536"
TASK_74_SHARED_MECHANISM_HEAD = "7d9278b769be47b2c119c08d5b63832974940afb"
TASK_68_SHARED_MECHANISM_HEAD = "f2e39edbea3c6f0122a14827d8d996c1854966bd"
CURRENT_SCORED_TASKS = 99
CURRENT_CONSUMED_TASKS = 99
CURRENT_OPERATOR_INVALID_TASKS = 17
CURRENT_SOURCE_REPLICATION_COMPONENTS_READY = 9
TASK_63_SHARED_MECHANISM_HEAD = "b567aaa68195e85cc6f799f727b415903251af46"
TASK_62_INTEGRATED_SEMANTIC_HEAD = "2696ebb5b9bec0e8a7f15d61dfc44ff288f35b60"
TASK_62_SHARED_MECHANISM_HEAD = "ccaca8d7ffcc9cecd0380c0cb07879bcc395647f"
TASK_61_SHARED_MECHANISM_HEAD = "f44fcd21cee441f0a2f9bf90a29083c09157422d"
TASK_60_SHARED_MECHANISM_HEAD = "24de629178cb2c8214dcefe5c553ef1015378052"
TASK_59_SHARED_MECHANISM_HEAD = "6fda37bbc9ce8b9f3a6a55574047d8f995de3626"
TASK_58_SHARED_MECHANISM_HEAD = "f56db3a789de9ed25e86ed492a52ae7f6e6062a6"
TASK_57_SHARED_MECHANISM_HEAD = "0824246428d4695bf273e578372cf0fae3d469de"


def _load_ladder() -> dict:
    return json.loads(LADDER_PATH.read_text(encoding="utf-8"))


def test_research_ladder_separates_product_and_strict_formal_authority() -> None:
    ladder = _load_ladder()
    authority = ladder["authority_boundary"]

    assert authority["product_research_authority"] is True
    assert authority["strict_formal_protocol_unchanged"] is True
    assert authority["aggregate_score_may_override_required_dimension"] is False
    assert authority["open_problem_model_agreement_is_correctness_evidence"] is False
    assert Path(authority["strict_formal_capability_protocol"]).exists()


def test_research_ladder_has_progressive_evidence_and_no_fixed_replication_rule() -> None:
    ladder = _load_ladder()

    assert [level["id"] for level in ladder["levels"]] == [
        "L0",
        "L1",
        "L2",
        "L3",
        "L4",
        "L5",
        "L6",
    ]
    assert ladder["levels"][-1]["correctness_scored"] is False
    assert ladder["simulation_precision_contract"][
        "universal_fixed_replication_count"
    ] is None
    assert ladder["simulation_precision_contract"][
        "confirmatory_rule_frozen_before_outcomes"
    ] is True
    assert ladder["formalization_contract"]["optional_gap_blocks_nonformal_dimensions"] is False
    assert ladder["formalization_contract"]["nonproof_evidence_may_be_promoted_to_proof"] is False


def test_ladder_counts_scored_and_consumed_tasks_without_embedding_gold() -> None:
    ladder = _load_ladder()
    candidates = ladder["initial_candidate_queue"]

    assert candidates
    scored = [
        candidate
        for candidate in candidates
        if candidate["status"] in {"active_scored", "consumed_scored"}
    ]
    pending = [
        candidate
        for candidate in candidates
        if candidate["status"].startswith("proposed_pending_")
    ]
    unconsumed = [
        candidate for candidate in scored if candidate["status"] == "active_scored"
    ]
    consumed = [
        candidate for candidate in scored if candidate["status"] == "consumed_scored"
    ]
    assert scored
    assert ladder["current_readiness"]["scored_tasks_total"] == len(scored)
    assert ladder["current_readiness"]["unconsumed_scored_tasks"] == len(
        unconsumed
    )
    assert ladder["current_readiness"]["consumed_scored_tasks"] == len(consumed)
    assert ladder["current_readiness"]["fully_gold_configured_tasks"] == len(scored)
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == sum(
        candidate["activation_evidence"].get("full_task_passed") is True
        for candidate in scored
    )
    assert len({candidate["id"] for candidate in candidates}) == len(candidates)
    assert all(
        candidate["activation_status"].startswith("frozen_ready_")
        for candidate in unconsumed
    )
    assert all(
        not candidate["activation_status"].startswith("frozen_ready_")
        for candidate in consumed
    )
    for candidate in scored:
        assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
        assert candidate["activation_status"].startswith(
            ("full_task_gold_", "fresh_live_v1_", "frozen_ready_")
        )
        assert Path(candidate["visible_questions_path"]).is_file()
        assert "gold_manifest" not in candidate
        assert candidate["gold_authority"] == (
            "operator_provisioned_outside_repository_and_model_workspace"
        )
        assert len(candidate["gold_manifest_sha256"]) == 64
    assert len(scored) + len(pending) == len(candidates)
    assert (
        ladder["current_readiness"]["latest_shared_mechanism_head"]
        == LATEST_SHARED_MECHANISM_HEAD
    )
    forbidden_keys = {
        "expected_answer",
        "expected_results",
        "theorem_statement",
        "proof",
        "reference_code",
    }
    assert all(forbidden_keys.isdisjoint(candidate) for candidate in candidates)
    assert all(
        candidate["level"] in {"L0", "L1", "L2", "L3"}
        for candidate in candidates
    )


def test_ladder_live_evaluation_policy_is_exact_haiku() -> None:
    model_policy = _load_ladder()["model_policy"]

    assert model_policy["live_evaluation_model"] == "claude-haiku-4-5-20251001"
    assert model_policy["live_evaluation_model_tier"] == "haiku"
    assert model_policy["sonnet_live_calls_allowed"] is False
    assert model_policy["opus_live_calls_allowed"] is False
    assert model_policy["automatic_tier_escalation_allowed"] is False


def test_neyman_allocation_l0_records_one_operator_invalidated_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "neyman_stratified_allocation_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "stratified_sampling_allocation"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_automated_pass_operator_invalidated_required_boundary_claims"
    )
    assert candidate["gold_manifest_sha256"] == (
        "1983cc5278e4b7e56436841031048d8040460bf244924421424c850f80ff9e19"
    )
    assert candidate["gold_descriptor_hash"] == (
        "8734135bdebe64342d9a20a24dcfb3f9d9db45f2f7f9dee4ecc138cd0bfae162"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "08666146d91fc7a91443ed4b7c86028ac86f9b3a"
    )
    assert evidence["activation_identity_commit"] == (
        "e7bd1646c17bca803a1f3852a295b1e60f801a25"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "e7bd1646c17bca803a1f3852a295b1e60f801a25"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_status"] == "ACCEPTED_AUTOMATED_FALSE_POSITIVE"
    assert evidence["runtime_outer_traces"] == 4
    assert evidence["product_model_calls"] == 22
    assert evidence["theory_workspace_successful_scratch_executions"] == 3
    assert evidence["independent_theory_review_successful_scratch_executions"] == 2
    assert evidence["independent_theory_review_verdict"] == (
        "ACCEPT_AUTOMATED_FALSE_POSITIVE"
    )
    assert evidence["terminal_critic_status"] == "ACCEPTED_AUTOMATED_FALSE_POSITIVE"
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["automated_full_task_passed"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["operator_audit_disposition"] == "INVALIDATED"
    assert evidence["operator_theory_status"] == (
        "failed_required_zero_variance_feasibility_and_active_variant_claims"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["ladder_score_after_consumption"] == "4/45"
    assert Path(evidence["operator_audit_path"]).is_file()


    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == (
        "10.1111/j.2397-2335.1934.tb04184.x"
    )
    assert "estimator_execution_contract" not in question

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_weighted_isotonic_pava_l0_records_one_closed_theory_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "weighted_isotonic_regression_pava_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "shape_constrained_regression"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_theory_transport_and_operator_invalidated_math"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-weighted-isotonic-pava-20260826-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "8932a6410471d12432fd9623a3782299941eedcb1286bbd72b8980a38d6afc2c"
    )
    assert candidate["gold_descriptor_hash"] == (
        "72c82a8b019967ca07e752954c4fe0a94aaa05aef8a89de3860bb7884bf60d7e"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "05e5b2a7d4447791419408ebaa85258d453e3bb2"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["algorithm_reference_contract_checks"] == "12/12"
    assert evidence["empirical_reference_replicates_per_dgp"] == 2000
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_attempts"] == 4
    assert evidence["semantic_calibration_total_model_calls"] == 36
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 36
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "2720809ddfc1ff333b9f7c4faf1246c2c428e880"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "theory_developer_reported_gap"
    )
    assert evidence["runtime_product_model_calls"] == 35
    assert evidence["runtime_client_tool_model_turns"] == 34
    assert evidence["theory_workspace_tool_calls"] == 38
    assert evidence["theory_workspace_submissions"] == 15
    assert evidence["theory_workspace_document_lines"] == 308
    assert evidence["theory_workspace_successful_scratch_executions"] == 2
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["hidden_theory_semantic_execution_attempted"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_UNACCEPTED_THEORY"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_58_SHARED_MECHANISM_HEAD
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1214/aoms/1177728423"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_weighted_isotonic_pava"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_orthogonal_lasso_l0_records_one_consumed_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "orthogonal_lasso_soft_threshold_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "sparse_linear_regression_regularization"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_metric_authoring_"
        "theory_and_scientific_code_failed_empirical_hidden_passed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-orthogonal-lasso-soft-threshold-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "42e54dd9bf97884a3d30d90b7b295ecd85fb118b816c6aaa6f98b4d5dd343e4e"
    )
    assert candidate["gold_descriptor_hash"] == (
        "475f8e52f4f3d6f5dc1f6b30bcf1c440ef145ad90a1ec079269d7ea100da1f53"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "3b7d98165c1ced62040ca4ef0898d9355720fc22"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 5
    assert evidence["algorithm_reference_contract_checks"] == "13/13"
    assert evidence["empirical_reference_replicates_per_dgp"] == 2000
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 9
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 9
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "ee796e5a212aff555949fc444b13cdf31c989026"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "architect_metric_requirement_packet_validation_failed"
    )
    assert evidence["runtime_outer_traces"] == 10
    assert evidence["runtime_architect_traces"] == 4
    assert evidence["runtime_handoffs"] == 9
    assert evidence["runtime_observations"] == 12
    assert evidence["runtime_outer_tool_calls"] == 5
    assert evidence["runtime_same_owner_workspace_continuations"] == 0
    assert evidence["accepted_theory_packet_id"] == (
        "theory_derivation:28305876afc3c4d10e5b9f0d"
    )
    assert evidence["accepted_theory_document_count"] == 2
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "10/10"
    assert evidence["hidden_theory_semantic_claims"].startswith("7/8")
    assert evidence["accepted_algorithm_handoff_id"] == (
        "accepted_algorithm_handoff:34027fcfe882f20e548b"
    )
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["hidden_algorithm_execution_attempted"] is True
    assert evidence["hidden_algorithm_checks"].startswith("11/13")
    assert evidence["generated_simulation_executed"] is False
    assert evidence["hidden_empirical_execution_attempted"] is True
    assert evidence["hidden_empirical_checks"].startswith("10/10")
    assert evidence["hidden_gold_tasks_evaluated"] == 1
    assert evidence["automated_full_task_passed"] is False
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_THEORY_AND_SCIENTIFIC_CODE"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_59_SHARED_MECHANISM_HEAD
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/59"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1111/j.2517-6161.1996.tb02080.x"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_orthogonal_lasso_soft_threshold"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_uniform_spacings_l0_records_one_consumed_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "uniform_spacings_dirichlet_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "order_statistics_uniform_spacings"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_metric_authoring_"
        "theory_failed_code_and_hidden_empirical_passed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-uniform-spacings-dirichlet-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "dce1bdf5f46a4ef75d9a1cd6ad511664f51bc629d6d0905b20eb7b7edce75dd5"
    )
    assert candidate["gold_descriptor_hash"] == (
        "0e2753282d39d160da1f3088ac2bd616fbd5fe03f2f7c392d8fdd4e5261abf45"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "855641ced4205b5f8fb97c03f3cc18bb993986a4"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 7
    assert evidence["algorithm_reference_contract_checks"] == "11/11"
    assert evidence["empirical_reference_replicates_per_dgp"] == 4000
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_sample_sizes"] == [1, 3, 8]
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 9
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 9
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "c19816e141713c2f388ef4365fb2ea7bd9aa7123"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "architect_metric_requirement_candidate_authority_invalid"
    )
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "10/10"
    assert evidence["hidden_theory_semantic_claims"].startswith("1/8")
    assert evidence["accepted_algorithm_handoff_id"] == (
        "accepted_algorithm_handoff:e489dec62fb74bd8fe63"
    )
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["hidden_algorithm_checks"] == "11/11"
    assert evidence["generated_simulation_executed"] is False
    assert evidence["hidden_empirical_checks"].startswith("9/9")
    assert evidence["hidden_gold_tasks_evaluated"] == 1
    assert evidence["automated_full_task_passed"] is False
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_ACTIVE_THEORY"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_60_SHARED_MECHANISM_HEAD
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )
    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1111/j.2517-6161.1965.tb00602.x"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_uniform_order_spacings"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_exact_permutation_l0_records_one_consumed_operator_invalidated_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "exact_two_sample_permutation_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "finite_randomization_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_metric_authoring_"
        "operator_invalidated_theory_and_code_hidden_empirical_passed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-exact-two-sample-permutation-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "d0427bdb74640f5649aa6b8f69ae2764a8b00e853d01ec4df7d53901058f63ba"
    )
    assert candidate["gold_descriptor_hash"] == (
        "841463c2f4be3010ef110644e6be2ad675becadf77146d60e55584507004a7b5"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "3ca8bd627972128e8c3e65e7ec33d8467d37ccd85ec53c1a7d85f71a266d7ab3"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "65c970b7c0629e0d38429720c5c3473960016bdf"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 7
    assert evidence["algorithm_reference_contract_checks"] == "13/13"
    assert evidence["empirical_reference_replicates_per_dgp"] == 4000
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_alpha"] == 0.1
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 9
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 9
    assert evidence["activation_seal_commit"] == (
        "e6fa0a87d4adf76a31e34c74d49b2a3939e8cf36"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "architect_metric_requirement_packet_validation_failed"
    )
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == (
        "8/8 satisfied; candidate PASS"
    )
    assert "false-accepted" in evidence["operator_theory_finding"]
    assert evidence["hidden_algorithm_checks"] == (
        "11/13; all_contract_checks and invalid_requests_rejected failed"
    )
    assert "1e-15" in evidence["operator_algorithm_finding"]
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is False
    assert evidence["hidden_empirical_checks"] == (
        "9/9 across 12000 estimator invocations"
    )
    assert evidence["automated_full_task_passed"] is False
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_ACTIVE_THEORY_THEORY_REVIEW_AND_SCIENTIFIC_CODE"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_61_SHARED_MECHANISM_HEAD
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/61"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == "10.2307/2984124"
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_exact_two_sample_permutation"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_gamma_poisson_l0_records_one_consumed_operator_invalidated_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "gamma_poisson_negative_binomial_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "count_mixture_distributions"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_metric_review_"
        "operator_invalidated_active_theory_hidden_components_passed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-gamma-poisson-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "72b6562378baad55df6c4817a38c83d85b1103eedfe6e58449fcc51e5b4fee7f"
    )
    assert candidate["gold_descriptor_hash"] == (
        "9fbec7f397c0a49c41e9662acace3579809f8bd2eb534acc937b807ef12c1a0f"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "a6e67611b08f24c1371b456d734fd59a95c74500e95ea60e75489439fc9d0f40"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "77e5230545bdea590280674f6f3dae33326ee317"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 7
    assert evidence["algorithm_reference_contract_checks"] == "12/12"
    assert evidence["empirical_reference_replicates_per_dgp"] == 8000
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 8
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 8
    assert evidence["preactivation_failed_negative_controls"] == 1
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    consumed = candidate["consumption_evidence"]
    assert consumed["runtime_code_head"] == (
        "fd3584a235a76bdf1b5247addb23af80b2bc0a5e"
    )
    assert "claude-haiku-4-5-20251001" in consumed["model_policy"]
    assert consumed["llm_topology_policy_ok"] is True
    assert consumed["outer_graph_iterations_consumed"] == 7
    assert consumed["runtime_status"] == "BLOCKED"
    assert consumed["runtime_failure_classification"] == (
        "architect_metric_semantic_review_packet_validation_failed"
    )
    assert consumed["hidden_theory_mechanical_checks"] == "7/7"
    assert consumed["hidden_theory_semantic_calibration"] == "10/10"
    assert consumed["hidden_theory_semantic_claims"].startswith("7/7")
    assert "Fano factor remains 1+t/beta" in consumed["operator_theory_finding"]
    assert consumed["hidden_algorithm_checks"] == "12/12"
    assert consumed["hidden_empirical_checks"] == "11/11"
    assert consumed["generated_algorithm_executed"] is True
    assert consumed["generated_simulation_executed"] is False
    assert consumed["hidden_gold_tasks_evaluated"] == 1
    assert consumed["automated_full_task_passed"] is False
    assert consumed["operator_disposition"] == (
        "OPERATOR_INVALIDATED_ACTIVE_THEORY_AND_THEORY_REVIEW_RUNTIME_INCOMPLETE"
    )
    assert Path(consumed["operator_audit"]).is_file()
    assert consumed["post_run_shared_mechanism_commit"] == (
        TASK_62_SHARED_MECHANISM_HEAD
    )
    assert consumed["post_run_integrated_semantic_evaluator_commit"] == (
        TASK_62_INTEGRATED_SEMANTIC_HEAD
    )
    assert consumed["model_draw_resampling_blocked"] is True
    assert consumed["formalization_requirement"] == "not_applicable"
    assert consumed["formalizer_executed"] is False
    assert consumed["full_task_passed"] is False
    assert consumed["trusted_capability_credit"] is False
    assert consumed["ladder_score_after_consumption"] == "4/62"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1111/j.2397-2335.1920.tb00606.x"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_gamma_poisson_mixture"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_pinball_quantile_l0_records_consumed_operator_invalidated_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "pinball_loss_quantile_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "statistical_decision_theory_quantiles"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_inconclusive_operator_invalidated_"
        "theory_and_code"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-pinball-quantile-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "9ce2a15c306d54a30d5f26d33dbad9ee296bf09a199438058d5cc0c110e31a2f"
    )
    assert candidate["gold_descriptor_hash"] == (
        "d02540b9e9387faa9162290657d1f2feb079ce76c74d2ba1679f545b95f814b0"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "de7633f76aa7e966e0d49cc59b803cfccc00d32d6f0f190831b603242e26dd61"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "d59bc7d792165c4fa174157d674dd6a77957267c"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 7
    assert evidence["algorithm_reference_contract_checks"] == "11/11"
    assert evidence["empirical_reference_replicates_per_dgp"] == 3000
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 4
    assert evidence["semantic_calibration_cases_correct"] == 9
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 4
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "cb7a08bc82d83598d79cc0b78ea78f56d21739ef"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "critic_scientific_inconclusive"
    )
    assert evidence["runtime_outer_graph_iterations"] == 12
    assert evidence["runtime_research_eval"] == (
        "0/1; mode conformant 1/1; not complete"
    )
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "9/9"
    assert evidence["hidden_algorithm_checks"] == "9/11"
    assert evidence["hidden_empirical_checks"] == (
        "10/10 over 18000 estimator invocations"
    )
    assert evidence["automated_hidden_evaluation"] == "0/1"
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_ACTIVE_THEORY_AND_CODE_RUNTIME_EMPIRICAL_"
        "INCONCLUSIVE"
    )
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_63_SHARED_MECHANISM_HEAD
    )
    assert evidence["runtime_manifest_sha256"] == (
        "8296fc8375cce751f4e7c3d4f848dbf670ffe330c943b9170717de61bac6b736"
    )
    assert evidence["hidden_gold_evaluation_sha256"] == (
        "1bfade2e7b8965eeeec5e7c55fb4038b40da635cc659efc1f71c21e841cd224c"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1016/j.ijforecast.2009.12.015"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_pinball_lower_quantile"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_gaussian_kde_l0_records_one_consumed_theory_block() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "gaussian_kde_amise_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "nonparametric_density_estimation"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_at_theory_with_referee_document_transport_gap"
    )
    assert candidate["gold_manifest_sha256"] == (
        "af0d690219e383497ec91c6d13b6fbe11d8b18394ec31cfe819109cfeaff06b1"
    )
    assert candidate["gold_descriptor_hash"] == (
        "70e93c13b7b8450ffb8aa0352bca2418b97b877ca3cfeddb712edba72559e220"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "d7d0fdcdcf1b1adbf09be9d84d0fb959ed84486c"
    )
    assert evidence["activation_identity_commit"] == (
        "812de9e8d17d7a499171202d756f4ec93c1ea448"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_head"] == (
        "812de9e8d17d7a499171202d756f4ec93c1ea448"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "theory_developer_reported_gap"
    )
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["algorithm_reference_contract_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_checks"] == "8/8"
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 14
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["full_task_score"] == "0/1 under the pre-frozen protocol"
    assert evidence["ladder_score_after_consumption"] == "4/44"
    assert Path(evidence["operator_audit_path"]).is_file()


    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aoms/1177704472"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_gaussian_kde"
    assert contract["entrypoint"] == "run_estimator"
    assert len(contract["request_fields"]) == 3
    assert len(contract["response_fields"]) == 3
    assert len(contract["empirical_claims"]) == 2

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "reference_estimator.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_kendall_tau_l0_records_one_consumed_draw_and_operator_override() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "kendall_tau_a_independence_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "rank_correlation_independence"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_with_operator_theory_override"
    )
    assert candidate["gold_manifest_sha256"] == (
        "6f85710ffb5a79d715f0eda341ad212aee21289f521d7d4e3b57f5da08d29ca8"
    )
    assert candidate["gold_descriptor_hash"] == (
        "d9d44aa733ef5d07c4206a0b9a054bca153ed32e890c6f131a6a4ddc5420cfad"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "e6ab1afb4d0796544d79278ff3ee652b961766f4"
    )
    assert evidence["activation_identity_commit"] == (
        "9d00edec736611b14d8802433fdda8213d4549a3"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_head"] == (
        "9d00edec736611b14d8802433fdda8213d4549a3"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "critic_scientific_rejected"
    )
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["algorithm_reference_contract_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_checks"] == "9/9"
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 14
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["operator_theory_status"] == (
        "failed_false_intermediate_covariance_and_overlap_count_with_cancelling_errors"
    )
    assert evidence["runtime_manifest_sha256"] == (
        "86e8d830dbeb2fcab952defad516b0225a9c5c98a1230403e6120ae0521cc2b5"
    )
    assert evidence["runtime_result_sha256"] == (
        "412ab04b077178dbc37d239a782d5b5d0895817aa77aa405dd211735d42f04c2"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "14d9aa18ba1a1714bd35f7a04973509f10cbf939dfa38aec21559adc8b91fbf4"
    )
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/kendall_tau_a_l0_v1.md"
    )
    assert evidence["post_run_shared_change_commit"] == (
        "a55517140acd3185e20531f147cbc9309238a78b"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is True
    assert evidence["full_task_passed"] is False


    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1093/biomet/30.1-2.81"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_kendall_tau_a"
    assert contract["entrypoint"] == "run_estimator"
    assert len(contract["request_fields"]) == 2
    assert len(contract["response_fields"]) == 9
    assert len(contract["empirical_claims"]) == 4

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "reference_estimator.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_hotelling_t2_l0_preserves_its_only_consumed_product_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "hotelling_one_sample_t2_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "multivariate_normal_mean_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_algorithm_contract_and_runtime_review_transport"
    )
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "dc0d323eca5fe8eecb0f7a28476950e02a8275da"
    )
    assert evidence["activation_identity_commit"] == (
        "4a25311b1ed168f99a41bf9f38dd97975b801aeb"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "570d78a58bfdb3d22f092ddf02a1808c001c2c25"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_tier"] == "haiku"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "generated_code_semantic_review_packet_invalid"
    )
    assert evidence["runtime_outer_traces"] == 16
    assert evidence["runtime_research_eval_complete"] is False
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["semantic_calibration_cases_correct"] == 14
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["algorithm_reference_contract_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_checks"] == "9/9"
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["hidden_theory_mechanics_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_checks"] == "9/9"
    assert evidence["hidden_theory_combined_passed"] is True
    assert evidence["hidden_algorithm_checks"] == "8/9"
    assert evidence["hidden_algorithm_estimator_invocations"] == 13
    assert evidence["hidden_empirical_checks"] == "9/9"
    assert evidence["hidden_empirical_estimator_invocations"] == 12000
    assert evidence["hidden_empirical_status"] == (
        "hidden_gold_passed_runtime_not_accepted"
    )
    assert evidence["runtime_manifest_sha256"] == (
        "d53e4a5158a9eca7c99f601fc70616d6dc94ce703c36d05eb31344bf2baba54f"
    )
    assert evidence["runtime_result_sha256"] == (
        "7100837bf25b8a680149e401425da482db24e6a4657fddbd7cf0cc42ea71b477"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "0d2eca983fa15cb2f4edca1d67d91dbbabb251ee8db0ed025aed84d0dbfef520"
    )
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/hotelling_t2_l0_v1.md"
    )
    assert evidence["post_run_shared_change_commit"] == (
        "ea0118067a2f9f2558db300c76c3fd74675725b9"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is True
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aoms/1177732979"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_hotelling_one_sample"
    assert contract["entrypoint"] == "run_estimator"
    assert len(contract["response_fields"]) == 9

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "reference_estimator.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_quantile_l0_freezes_theory_only_failure_without_resampling() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "sample_quantile_clt_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_evidence"]["fresh_live_runs"] == 1
    assert candidate["activation_evidence"]["fresh_live_runtime_status"] == "BLOCKED"
    assert candidate["activation_evidence"]["fresh_live_hidden_gold_result"].startswith(
        "0/1"
    )
    assert candidate["activation_evidence"]["model_draw_resampling_blocked"] is True
    assert candidate["activation_evidence"]["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        candidate["activation_evidence"]["visible_questions_sha256"]
    )


def test_doubleml_l1_freezes_exact_replication_without_conflating_l2() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "double_machine_learning_public_replication"
    )

    assert candidate["level"] == "L1"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_before_checkpoint_promotion"
    )
    assert candidate["activation_evidence"]["fresh_live_runs"] == 1
    assert candidate["activation_evidence"]["fresh_live_runtime_status"] == (
        "BLOCKED"
    )
    assert candidate["activation_evidence"][
        "fresh_live_source_execution_status"
    ] == "EXECUTED"
    assert candidate["activation_evidence"][
        "fresh_live_hidden_gold_result"
    ].startswith("0/1")
    assert candidate["activation_evidence"][
        "runtime_source_replication_lane_available"
    ] is True
    assert candidate["activation_evidence"][
        "source_only_checkpoint_runtime_regression_passed"
    ] is True
    assert candidate["activation_evidence"]["mechanism_exact_source_runs"] == 1
    assert candidate["activation_evidence"][
        "mechanism_stdout_hash_matched_frozen_rerun"
    ] is True
    assert candidate["task_intent"] == {
        "source_replication": "required",
        "theory": "optional",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        candidate["activation_evidence"]["visible_questions_sha256"]
    )
    assert len(candidate["source_snapshot_hash"]) == 64
    assert len(candidate["source_manifest_sha256"]) == 64
    assert len(candidate["gold_manifest_sha256"]) == 64


def test_model_x_l2_hides_author_code_and_freezes_gold_before_first_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "model_x_public_paper_to_code_reproduction"
    )

    assert candidate["level"] == "L2"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_by_theory_progress_context_binding"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["author_implementation_hidden_from_l2_runtime"] is True
    assert evidence["gold_activated_before_first_runtime_model_call"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_runtime_status"] == "BLOCKED"
    assert evidence["fresh_live_runtime_research_eval"] == "0/1 complete"
    assert evidence["fresh_live_accepted_theory_packet"] is False
    assert evidence["fresh_live_algorithm_executions"] == 0
    assert evidence["fresh_live_simulation_executions"] == 0
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert len(evidence["post_run_shared_continuation_fix_commit"]) == 40
    assert evidence["semantic_calibration_cases"] == 10
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["algorithm_reference_checks"] == "7/7"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert len(candidate["source_snapshot_hash"]) == 64
    assert len(candidate["source_manifest_sha256"]) == 64
    assert len(candidate["gold_manifest_sha256"]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert "author implementation and gold outcomes are withheld" in question[
        "description"
    ]
    assert "downstream knockoff-filter FDR theorem" in question["description"]


def test_horvitz_thompson_l0_freezes_gold_without_embedding_evaluator() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "poisson_horvitz_thompson_total_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "survey_sampling"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_by_redundant_nonformal_theorem_handoff"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_runtime_status"] == "BLOCKED"
    assert evidence["fresh_live_research_eval_result"] == "0/1"
    assert evidence["fresh_live_hidden_gold_result"].startswith(
        "0/1_not_executed"
    )
    assert evidence["fresh_live_accepted_theory_packet"] is False
    assert evidence["fresh_live_algorithm_executions"] == 0
    assert evidence["fresh_live_simulation_executions"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["semantic_calibration_cases"] == 10
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["algorithm_reference_checks"] == "8/8"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert len(candidate["source_snapshot_hash"]) == 64
    assert len(candidate["source_manifest_sha256"]) == 64
    assert len(candidate["gold_manifest_sha256"]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "est_poisson_horvitz_thompson" in question["description"]
    assert "Lean formalization" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_unweighted.py",
        "negative_hajek.py",
        "negative_variance_denominator.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_normal_sample_variance_l0_records_operator_invalidated_single_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "normal_sample_variance_chi_square_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "mathematical_statistics"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_operator_invalidated_theory_review_false_positive"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_runtime_status"] == (
        "ACCEPTED_AUTOMATED_FALSE_POSITIVE"
    )
    assert evidence["operator_audit_disposition"] == "INVALIDATED"
    assert evidence["fresh_live_algorithm_executions"] == 1
    assert evidence["fresh_live_simulation_executions"] == 1
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["algorithm_reference_checks"] == "8/8"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_cases"] == 10
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert Path(evidence["operator_audit_path"]).is_file()
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_normal_sample_variance" in question["description"]
    assert "Lean formalization" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_divisor_n.py",
        "negative_uncentered.py",
        "negative_wrong_pivot.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_median_of_means_l0_is_frozen_after_its_only_live_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "median_of_means_finite_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "robust_statistics"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_preflight_transport_and_operator_math_audit"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_v1_runtime_status"] == "FAILED"
    assert evidence["fresh_v1_runtime_research_eval"] == "0/1 complete"
    assert len(evidence["fresh_v1_runtime_manifest_sha256"]) == 64
    assert evidence["fresh_v1_independent_preflight_verdict"] == "not produced"
    assert evidence["fresh_v1_algorithm_executions"] == 0
    assert evidence["fresh_v1_simulation_executions"] == 0
    assert evidence["fresh_v1_formalizer_executions"] == 0
    assert evidence["operator_audit_disposition"] == "FAILED_CLOSED"
    assert Path(evidence["operator_audit_path"]).is_file()
    assert evidence["algorithm_reference_checks"] == "8/8"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 12000
    assert evidence["semantic_calibration_cases"] == 11
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_median_of_means" in question["description"]
    assert "Lean formalization" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_sample_mean.py",
        "negative_radius.py",
        "negative_failure_exponent.py",
        "negative_block_layout.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_benjamini_hochberg_l0_single_live_draw_is_frozen_failed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "benjamini_hochberg_independence_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "multiple_testing"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_theory_index_anchor_transport"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 12000
    assert evidence["semantic_calibration_cases"] == 11
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "theory_developer_reported_gap"
    )
    assert evidence["research_eval_complete"] is False
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["runtime_traces"] == 3
    assert evidence["theory_model_turns"] == 10
    assert evidence["theory_tool_executions"] == 10
    assert evidence["theory_workspace_submissions"] == 5
    assert evidence["authoritative_theory_documents"] == 1
    assert evidence["theory_document_lines"] == 192
    assert evidence["theory_document_bytes"] == 10051
    assert evidence["accepted_theory_packet"] is False
    assert evidence["algorithm_executions"] == 0
    assert evidence["simulation_executions"] == 0
    assert evidence["formalizer_executions"] == 0
    assert evidence["operator_audit"] == (
        "docs/operator_audits/benjamini_hochberg_l0_v1.md"
    )
    assert evidence["post_run_shared_fix_verification"] == "761 passed"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    for field in (
        "runtime_manifest_sha256",
        "hidden_gold_report_sha256",
        "theory_document_sha256",
    ):
        assert len(evidence[field]) == 64
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "optional",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_benjamini_hochberg" in question["description"]
    assert "Lean formalization is optional" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_step_down.py",
        "negative_strict_boundary.py",
        "negative_sorted_output.py",
        "negative_unadjusted_values.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_wilson_score_l0_single_live_draw_is_frozen_failed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "wilson_score_binomial_interval_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "binomial_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_preflight_transport_and_operator_math_audit"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 12000
    assert evidence["semantic_calibration_cases"] == 11
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "architect_theory_execution_preflight_packet_validation_failed"
    )
    assert evidence["research_eval_complete"] is False
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["runtime_traces"] == 4
    assert evidence["theory_model_turns"] == 11
    assert evidence["theory_tool_executions"] == 11
    assert evidence["theory_workspace_submissions"] == 3
    assert evidence["theory_workspace_checkpoint_committed"] is True
    assert evidence["authoritative_theory_documents"] == 1
    assert evidence["theory_document_lines"] == 347
    assert evidence["theory_document_bytes"] == 13964
    assert evidence["independent_theory_preflight_accepted"] is False
    assert evidence["accepted_theory_packet"] is False
    assert evidence["algorithm_executions"] == 0
    assert evidence["simulation_executions"] == 0
    assert evidence["formalizer_executions"] == 0
    assert evidence["operator_audit"] == (
        "docs/operator_audits/wilson_score_l0_v1.md"
    )
    assert evidence["post_run_shared_fix_commit"] == (
        "fe65d1f3fb3c5bbdb58e040c15e11fcc8bdc2fc8"
    )
    assert evidence["post_run_shared_fix_verification"] == "763 passed"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    for field in (
        "runtime_manifest_sha256",
        "hidden_gold_report_sha256",
        "runtime_failure_summary_sha256",
        "theory_document_sha256",
    ):
        assert len(evidence[field]) == 64
    assert Path(evidence["operator_audit"]).is_file()
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "optional",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_wilson_score_interval" in question["description"]
    assert "Lean formalization is optional" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_wald.py",
        "negative_missing_denominator.py",
        "negative_one_sided_quantile.py",
        "negative_linear_adjustment.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_jackknife_mean_l0_freezes_invalid_design_and_terminal_budget_block() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "jackknife_sample_mean_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "resampling"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_invalid_evaluation_design_and_theory_terminal_budget_blocked"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 12000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["fresh_live_runtime_status"] == "BLOCKED"
    assert evidence["fresh_live_terminal_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["fresh_live_runtime_traces"] == 3
    assert evidence["fresh_live_theory_model_turns"] == 11
    assert evidence["fresh_live_theory_tool_executions"] == 12
    assert evidence["fresh_live_theory_document_lines"] == 240
    assert evidence["fresh_live_theory_document_bytes"] == 8521
    assert evidence["fresh_live_last_write_workspace_valid"] is True
    assert evidence["fresh_live_last_write_checkpoint_commit_ready"] is True
    assert evidence["fresh_live_last_write_model_tool_calls_remaining"] == 0
    assert evidence["fresh_live_last_write_standard_turns_remaining"] == 1
    assert evidence["fresh_live_next_model_tool_blocked_before_execution"] is True
    assert evidence["fresh_live_independent_theory_review_attempted"] is False
    assert evidence["fresh_live_accepted_theory_packet"] is False
    assert evidence["fresh_live_algorithm_executions"] == 0
    assert evidence["fresh_live_simulation_executions"] == 0
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["evaluator_design_valid"] is False
    assert evidence["hidden_algorithm_failure_attribution_allowed"] is False
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "0d8a01e5a2af00a3223df413f1909a11a56e6997"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "fresh_live_runtime_manifest_sha256",
        "fresh_live_hidden_gold_report_sha256",
        "fresh_live_runtime_failure_summary_sha256",
        "fresh_live_theory_document_sha256",
    ):
        assert len(evidence[field]) == 64
    assert Path(evidence["operator_audit_path"]).is_file()
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX theory workspace" in question["description"]
    assert "est_jackknife_mean_variance" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_wrong_prefactor.py",
        "negative_wrong_delete_denominator.py",
        "negative_returns_sample_variance.py",
        "negative_duplicate_replicate.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_ar1_ols_l0_freezes_consumed_collaboration_failure_without_resampling() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "stationary_ar1_zero_mean_ols_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "time_series"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == "full_task_gold_frozen_consumed_closed"
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_runtime_status"] == "MAX_ITERATIONS_REACHED"
    assert evidence["fresh_live_runtime_terminal_kind"] == (
        "budget_exhausted_with_pending_next_task"
    )
    assert evidence["fresh_live_theory_checkpoint_committed"] is True
    assert evidence["fresh_live_independent_theory_review_accepted"] is True
    assert evidence["fresh_live_algorithm_execution_passed"] is True
    assert evidence["fresh_live_algorithm_semantic_review_accepted"] is True
    assert evidence["fresh_live_metric_protocol_preexecution_review_accepted"] is True
    assert evidence["fresh_live_simulation_accepted"] is False
    assert evidence["fresh_live_critic_accepted"] is False
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    assert Path(evidence["operator_audit_path"]).is_file()
    for field in (
        "fresh_live_runtime_manifest_sha256",
        "fresh_live_hidden_gold_report_sha256",
        "fresh_live_runtime_failure_summary_sha256",
        "fresh_live_runtime_completion_summary_sha256",
    ):
        assert len(evidence[field]) == 64
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }


def test_fisher_z_l0_is_consumed_closed_after_one_runtime_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "bivariate_normal_fisher_z_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "correlation_multivariate"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == "full_task_gold_consumed_closed"
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_contract_checks"] == "12/12"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 9000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["fresh_live_runtime_status"] == "BLOCKED"
    assert evidence["fresh_live_runtime_terminal_kind"] == "blocked"
    assert evidence["fresh_live_runtime_terminal_classification"] == (
        "architect_metric_requirement_packet_validation_failed"
    )
    assert evidence["fresh_live_theory_checkpoint_committed"] is True
    assert evidence["fresh_live_independent_theory_review_accepted"] is True
    assert evidence["fresh_live_hidden_theory_semantic_passed"] is False
    assert evidence["fresh_live_algorithm_execution_passed"] is True
    assert evidence["fresh_live_algorithm_semantic_review_accepted"] is True
    assert evidence["fresh_live_metric_protocol_preexecution_review_accepted"] is False
    assert evidence["fresh_live_simulation_accepted"] is False
    assert evidence["fresh_live_critic_accepted"] is False
    assert evidence["fresh_live_formalizer_executions"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    assert evidence["activation_commit"] == (
        "6b871aa078f61e08c495cdf1753c40c3b9867f43"
    )
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64
    for field in (
        "fresh_live_runtime_manifest_sha256",
        "fresh_live_hidden_gold_report_sha256",
        "fresh_live_runtime_failure_summary_sha256",
        "fresh_live_runtime_completion_summary_sha256",
    ):
        assert len(evidence[field]) == 64
    assert Path(evidence["operator_audit_path"]).is_file()
    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_fisher_pearson_z" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_uncentered_correlation.py",
        "negative_double_fisher_z.py",
        "negative_clipped_correlation.py",
        "negative_asymptotic_standard_error.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_paired_ratio_l0_draw_is_consumed_and_hash_bound() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "paired_ratio_of_means_delta_method_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "ratio_metrics"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_shared_terminal_disposition_budget"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_contract_checks"] == "14/14"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 9000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["activation_commit"] == (
        "bc5eb28c6e09ddffda15e4d6c0d32108cea2c273"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["final_workspace_valid"] is True
    assert evidence["final_checkpoint_commit_ready"] is True
    assert evidence["final_terminal_tool_call_returned_by_model"] is True
    assert evidence["final_terminal_tool_call_executed_by_runtime"] is False
    assert evidence["independently_accepted_theory_packet"] is False
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "3bfa8daa378480fdd1e11acae3b229abf3abd3d7"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_paired_ratio_delta" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_mean_of_ratios.py",
        "negative_omit_covariance.py",
        "negative_population_normalization.py",
        "negative_standard_error_scaling.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_scalar_control_variate_l0_frozen_draw_is_consumed_and_closed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "scalar_control_variate_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "monte_carlo_variance_reduction"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "full_task_gold_frozen_v1_failed_shared_simulation_prompt_artifact_expansion"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["algorithm_reference_contract_checks"] == "13/13"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 9000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["activation_commit"] == (
        "e1e1f975322b4eaafc2809a112ac30b445753aa5"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_traces"] == 10
    assert evidence["runtime_task_handoffs"] == 9
    assert evidence["theory_checkpoint_committed"] is True
    assert evidence["independent_theory_preflight_accepted"] is True
    assert evidence["generated_algorithm_executions"] == 1
    assert evidence["independent_algorithm_semantic_review_accepted"] is True
    assert evidence["independent_metric_protocol_accepted"] is True
    assert evidence["generated_simulation_executions"] == 0
    assert evidence["hidden_theory_semantic_status"] == "INCONCLUSIVE"
    assert evidence["hidden_algorithm_acceptance_checks_passed"] is False
    assert evidence["hidden_empirical_checks_passed"] is True
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "dd3cb36c236e360c52f397998464997b0c08c7c8"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_scalar_control_variate" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_wrong_adjustment_sign.py",
        "negative_population_normalization.py",
        "negative_omit_covariance.py",
        "negative_standard_error_scaling.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_pearson_multinomial_gof_l0_frozen_draw_is_consumed_and_closed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "pearson_multinomial_gof_known_result"
    )

    assert ladder["model_policy"] == {
        "provider": "anthropic",
        "live_evaluation_model_tier": "haiku",
        "live_evaluation_model": "claude-haiku-4-5-20251001",
        "sonnet_live_calls_allowed": False,
        "opus_live_calls_allowed": False,
        "automatic_tier_escalation_allowed": False,
    }
    assert candidate["level"] == "L0"
    assert candidate["family"] == "categorical_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == "full_task_gold_frozen_consumed_closed"
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_terminal_status"] == "BLOCKED"
    assert evidence["fresh_live_terminal_classification"] == (
        "generated_code_semantic_review_input_invalid"
    )
    assert evidence["fresh_live_outer_traces"] == 9
    assert evidence["fresh_live_generated_algorithm_executions"] == 1
    assert evidence["fresh_live_generated_simulation_executions"] == 1
    assert evidence["fresh_live_runtime_metric_contracts_passed"] == "8/8"
    assert evidence["fresh_live_simulation_estimator_invocations"] == 75006
    assert evidence["fresh_live_theory_structural_checks_passed"] is True
    assert evidence["fresh_live_theory_semantic_status"] == "INCONCLUSIVE"
    assert evidence["fresh_live_algorithm_harness_execution_passed"] is True
    assert evidence["fresh_live_algorithm_acceptance_checks_passed"] is False
    assert evidence["fresh_live_empirical_checks_passed"] is True
    assert evidence["fresh_live_empirical_estimator_invocations"] == 15000
    assert evidence["post_run_shared_mechanism_commit"] == "f4fe83ed"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_multinomial_pearson_gof" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_absolute_residual.py",
        "negative_pvalue_cdf.py",
        "negative_uniform_null.py",
        "negative_wrong_df.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_exponential_rate_mle_l0_authority_is_consumed_after_one_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "exponential_rate_mle_pivot_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "lifetime_rate_inference"
    assert candidate["status"] == "consumed_scored"
    assert (
        candidate["activation_status"]
        == "full_task_gold_frozen_consumed_closed"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "2097c3102b7a4b936a1a0669bdb5e4f8f716f5ba"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_terminal_status"] == "ACCEPTED"
    assert evidence["fresh_live_outer_traces"] == 11
    assert evidence["fresh_live_task_handoffs"] == 10
    assert evidence["fresh_live_client_tool_model_turns"] == 24
    assert evidence["fresh_live_generated_algorithm_executions"] == 1
    assert evidence["fresh_live_generated_simulation_executions"] == 1
    assert evidence["fresh_live_runtime_metric_contracts_passed"] == "8/8"
    assert evidence["fresh_live_simulation_estimator_invocations"] == 65020
    assert evidence["fresh_live_research_eval_ready"] is True
    assert evidence["fresh_live_theory_structural_checks_passed"] is True
    assert evidence["fresh_live_theory_semantic_status"] == "FAIL"
    assert evidence["fresh_live_theory_gold_validated"] is False
    assert evidence["fresh_live_algorithm_harness_execution_passed"] is True
    assert evidence["fresh_live_algorithm_acceptance_checks_passed"] is False
    assert evidence["fresh_live_algorithm_acceptance_checks"] == "5/7"
    assert evidence["fresh_live_algorithm_invalid_requests_rejected"] is False
    assert evidence["fresh_live_empirical_checks_passed"] is True
    assert evidence["fresh_live_empirical_acceptance_checks"] == "8/8"
    assert evidence["fresh_live_empirical_estimator_invocations"] == 15000
    assert evidence["post_run_shared_mechanism_change"] == "none"
    assert evidence["algorithm_reference_contract_checks"] == "11/11"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_identity_agreements"] == 15000
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False
    for field in (
        "source_snapshot_hash",
        "source_manifest_sha256",
        "gold_manifest_sha256",
        "gold_descriptor_hash",
    ):
        assert len(candidate[field]) == 64

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "est_exponential_rate_interval" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]
    assert candidate["task_intent"] == question["task_intent"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_scale_parameter.py",
        "negative_unbiased_as_mle.py",
        "negative_missing_factor_two.py",
        "negative_wald_interval.py",
        "semantic_reference.md",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_its_time_l1_draw_is_consumed_without_posthoc_rescore() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "its_time_niv_figure5_public_replication"
    )

    assert candidate["level"] == "L1"
    assert candidate["family"] == "instrumental_time_series"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_before_source_replication"
    )
    assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["hidden_gold_activated_before_first_product_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["fresh_live_runs"] == 1
    assert evidence["independent_reruns"] == "4/4"
    assert evidence["source_replication_calibration_cases"] == "8/8"
    assert evidence["semantic_calibration_cases"] == "6/6"
    assert evidence["semantic_calibration_model"] == "claude-haiku-4-5-20251001"
    assert evidence["semantic_calibration_model_calls"] == 2
    assert evidence["dynamic_report_evidence_binding"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_roles"] == 7
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_source_replication_manifest_observed"] is False
    assert evidence["hidden_gold_full_task_result"] == "0/1"
    assert "never rerun" in evidence["post_run_policy"].lower()
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert "operator-pinned source without editing or wrapping it" in question["description"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert candidate["task_intent"] == question["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_statlib_formal_l0_draw_is_consumed_without_proof_credit() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "statlib_uniform_consistency_implies_consistency_formal_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == "fresh_live_v1_hidden_gold_failed"
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_model"] == "claude-haiku-4-5-20251001"
    assert evidence["fresh_live_terminal_status"] == "BLOCKED"
    assert evidence["formalizer_source_updates"] == 24
    assert evidence["formalizer_local_lean_checks"] == 24
    assert evidence["formalizer_formal_rag_calls"] == 10
    assert evidence["kernel_verified_subclaims"] == 0
    assert evidence["full_theorem_proved"] is False
    assert evidence["hidden_evaluator_runs"] == 1
    assert evidence["runtime_manifest_sha256"] == (
        "290038d990aed7fbac801cf0cd1a71296cdd678e5addc0642f896a7b3ee18ea0"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "1c23f19bd19b23fee40e9f2c0f4e4c857c535ccb99ceb05d0b84d1c09a7e5739"
    )
    assert evidence["hidden_formal_harness_calibration_cases"] == "5/5"
    assert evidence["hidden_gold_kernel_compiled"] is True
    assert evidence["formalization_requirement"] == "required"
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    contract = question["formal_target_contract"]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "required",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert contract["proof_visibility"] == "hidden"
    assert contract["declaration_name"] == (
        "AIStatisticianBench.uniformlyConsistent_implies_consistent"
    )
    assert hashlib.sha256(
        contract["lean_source_prefix"].encode("utf-8")
    ).hexdigest() == contract["lean_source_prefix_sha256"]
    assert contract["lean_source_prefix"].rstrip().endswith(":= by")
    assert "tendsto_of_tendsto" not in contract["lean_source_prefix"]
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True


def test_variance_affine_formal_l0_draw_is_consumed_without_proof_credit() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "statlib_variance_affine_formal_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_hidden_gold_failed_missing_formal_only_semantic_authority"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["fresh_live_model"] == "claude-haiku-4-5-20251001"
    assert evidence["sonnet_or_opus_calls_allowed"] is False
    assert evidence["hidden_formal_harness_calibration_cases"] == "5/5"
    assert evidence["hidden_gold_kernel_compiled"] is True
    assert evidence["negative_weakened_conclusion_rejected"] is True
    assert evidence["negative_extra_assumption_rejected"] is True
    assert evidence["negative_sorry_rejected"] is True
    assert evidence["negative_custom_axiom_rejected"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["formalizer_candidate_compiled"] == 1
    assert evidence["compiled_candidate_identity_verified"] is True
    assert evidence["compiled_candidate_axiom_audit_clean"] is True
    assert evidence["independent_semantic_reviewer_model_calls"] == 0
    assert evidence["kernel_verified_subclaims"] == 0
    assert evidence["full_theorem_proved"] is False
    assert evidence["hidden_evaluator_runs"] == 1
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/56"
    assert (
        ladder["current_readiness"]["consumed_scored_tasks"]
        == CURRENT_CONSUMED_TASKS
    )
    assert ladder["current_readiness"]["fully_gold_passed_tasks"] == 7
    assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    contract = question["formal_target_contract"]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "required"
    assert contract["proof_visibility"] == "hidden"
    assert contract["declaration_name"] == "AIStatisticianBench.variance_affine"
    assert hashlib.sha256(
        contract["lean_source_prefix"].encode("utf-8")
    ).hexdigest() == contract["lean_source_prefix_sha256"]
    assert contract["lean_source_prefix"].rstrip().endswith(":= by")
    assert "variance_add_const" not in contract["lean_source_prefix"]


def test_score_information_l0_draw_is_consumed_without_review_credit() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "scalar_score_information_bound_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "parametric_information_bounds"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_hidden_gold_failed_missing_independent_theory_review"
    )
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_model"] == "claude-haiku-4-5-20251001"
    assert evidence["fresh_live_terminal_status"] == "ACCEPTED"
    assert evidence["fresh_live_research_eval_ready"] is True
    assert evidence["fresh_live_runtime_traces"] == 4
    assert evidence["fresh_live_theory_model_turns"] == 10
    assert evidence["fresh_live_theory_checkpoint_committed"] is True
    assert evidence["fresh_live_independent_theory_review_attempted"] is False
    assert evidence["fresh_live_independent_theory_review_accepted"] is False
    assert evidence["fresh_live_critic_accepted"] is True
    assert evidence["fresh_live_hidden_theory_execution_attempted"] is False
    assert evidence["fresh_live_hidden_theory_semantic_execution_attempted"] is False
    assert evidence["runtime_manifest_sha256"] == (
        "7431cd7af241a48712eab0f18128aa23ac5119c0b01d32f2c0ca1439b50f2a8c"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "908efc77f125bbe44e779bf0a353881ca1b22f57ffbf53fedcc067d346f12e59"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 6
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_calibration_model_calls"] == 2
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["authority_binding_commit"] == (
        "c0065450d8d8e0b0b79ca79a74444391f9394857"
    )
    assert evidence[
        "authority_binding_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "9fbbeaba610a48bfbce84a80b4b91802fe301ba9"
    )
    assert evidence["post_run_shared_mechanism_fix_verification"] == (
        "214 focused tests and 860/860 full-suite tests passed"
    )
    assert evidence["formalization_requirement"] == "not_applicable"

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_basu_theory_l0_draw_is_consumed_after_missing_routed_review() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "basu_complete_sufficient_ancillary_independence_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "statistical_structure_and_ancillarity"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_hidden_gold_failed_missing_routed_independent_theory_review"
    )
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 13
    assert evidence["fresh_live_runs"] == 1
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 7
    assert evidence["semantic_calibration_cases"] == 13
    assert evidence["semantic_calibration_cases_correct"] == 13
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_calibration_model_calls"] == 2
    assert evidence["authority_binding_commit"] == (
        "7a0ee06b1b0f4507df40aaaf53c7092cde4e48d5"
    )
    assert evidence[
        "authority_binding_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "required_independent_theory_review_missing"
    )
    assert evidence["independent_theory_review_attempted"] is False
    assert evidence["critic_model_call_attempted"] is False
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/basu_independence_l0_v1.md"
    )
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "8ef61b0b9625bf99e4f783dad7781b4c1bfdba77"
    )
    assert evidence["post_run_shared_mechanism_fix_verification"] == (
        "123 focused tests and 861/861 full-suite tests passed"
    )
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_uniform_endpoint_l0_draw_is_consumed_after_hidden_gold_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "uniform_endpoint_maximum_exact_interval_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "nonregular_endpoint_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_hidden_gold_failed_theory_semantics_and_executable_interface"
    )
    assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
    assert candidate["gold_manifest_sha256"] == (
        "9da0e97e77651d97994823a0c94d883a387680e8640bdc374c1c30b55f59ca45"
    )
    assert candidate["gold_descriptor_hash"] == (
        "6d971a027858bce4dd91c2af1a6dfc09a497899f148b1726790837439f42ab1e"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 24
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_iterations"] == 10
    assert evidence["visible_research_evaluation"] == (
        "1/1_complete_mode_conformant_ready"
    )
    assert evidence["hidden_gold_evaluation"] == "0/1_failed"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "12/12"
    assert evidence["hidden_theory_semantic_candidate_status"] == "FAIL"
    assert evidence["hidden_algorithm_acceptance_checks"] == "6/8"
    assert evidence["hidden_algorithm_failure"] == "invalid_requests_rejected"
    assert evidence["hidden_empirical_checks"] == "8/8"
    assert evidence["hidden_empirical_estimator_invocations"] == 15000
    assert evidence["runtime_manifest_sha256"] == (
        "01085f72d445675faaea88cce6de93fa84f1359e9c65f38e42293305a14ac2b8"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "30a0b5e1fa2fc27d9bb72283ac967e66a225a6b856ce16d785390ceb7e8bc396"
    )
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/uniform_endpoint_l0_v1.md"
    )
    assert evidence["post_run_shared_mechanism_fix_commit"] == "b49a8f5a"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert candidate["task_intent"] == question["task_intent"]
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
    assert contract["estimator_id"] == "est_uniform_endpoint_interval"
    assert contract["entrypoint"] == "run_estimator"
    assert [row["name"] for row in contract["request_fields"]] == ["sample", "alpha"]
    assert [row["name"] for row in contract["response_fields"]] == [
        "sample_size",
        "sample_maximum",
        "mle_endpoint",
        "unbiased_endpoint",
        "confidence_level",
        "exact_ci_lower",
        "exact_ci_upper",
    ]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_aitken_gls_l0_records_sole_consumed_draw_and_operator_caveats() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "aitken_gls_blue_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "generalized_least_squares_efficiency"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_passed_with_operator_semantic_and_"
        "referee_evidence_caveats"
    )
    assert candidate["gold_manifest_sha256"] == (
        "cb98d48380c2abec6e966f4392d0665c7c4d6778ee11082702ec5c5da1dd86e7"
    )
    assert candidate["gold_descriptor_hash"] == (
        "8663823e035146515f30e2b17bfd9c36c7260d0e93c54a4c30cba64341584685"
    )
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "a25ec10ebcbf6830ffa4385ae37a10463bada434"
    )
    assert evidence["activation_binding_commit"] == (
        "ccb34f7c280585c19396f43ea400a7ecccd0cacb"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_head"] == (
        "ccb34f7c280585c19396f43ea400a7ecccd0cacb"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_evaluation"] == (
        "1/1_complete_and_mode_conformant"
    )
    assert evidence["hidden_gold_evaluation"] == "1/1"
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 7
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases"] == 13
    assert evidence["semantic_calibration_cases_correct"] == 13
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "8/8"
    assert evidence["runtime_outer_traces"] == 4
    assert evidence["runtime_architect_traces"] == 2
    assert evidence["runtime_handoffs"] == 3
    assert evidence["runtime_observations"] == 5
    assert evidence["runtime_outer_tool_calls"] == 0
    assert evidence["product_model_calls"] == 22
    assert evidence["product_model_call_breakdown"] == {
        "architect_plan": 1,
        "theory_workspace": 7,
        "independent_theory_referee": 13,
        "terminal_critic": 1,
    }
    assert evidence["theory_document_lines"] == 352
    assert evidence["theory_document_bytes"] == 13772
    assert evidence["theory_document_sha256"] == (
        "61d6d49743d17d57e11ff054aaf8d13ef6b1a26890cdcd07280e6e94c16e7f39"
    )
    assert evidence["independent_theory_review_verdict"] == "ACCEPT"
    assert evidence["independent_theory_review_blocking_findings"] == 0
    assert evidence["independent_theory_review_successful_scratch_executions"] == 0
    assert evidence["independent_theory_review_non_success_scratch_executions"] == 2
    assert evidence["independent_theory_review_scratch_statuses"] == [
        "REJECTED_CONTRACT",
        "FAILED",
    ]
    assert evidence["terminal_critic_status"] == "ACCEPTED"
    assert evidence["runtime_manifest_sha256"] == (
        "9f693352731ba91992ef537816f990402770901387cb403199e3a25ff4e56348"
    )
    assert evidence["runtime_result_sha256"] == (
        "f04e917e8341d6354798188935a117ac400dc8ddcb39f0c0a14cc23fb22f0c9d"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "2f516f696602f8299f89eec9acfb6487d1c8aadf3bc5b1da52f4db014560c1ae"
    )
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/aitken_gls_blue_l0_v1.md"
    )
    assert evidence["post_run_shared_change_commit"] == (
        "4ebef6c57ea2a279faf59bca2bd29e219be120ba"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["full_task_passed"] is True

    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        "95946f5c5588f3bfef10038a363467b327680e72bc395abcf711eaa2926f4fe5"
    )
    assert evidence["visible_question_hash"] == (
        "9cc72caef038a2ee127bad74dcebba91c9df6e397ea1249860fcde1c07c6dc5f"
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["year"] == 1936
    assert question["source"]["doi"] == "10.1017/S0370164600014346"
    assert "estimator_execution_contract" not in question

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_huber_location_l0_draw_is_consumed_after_review_packet_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "huber_location_m_estimator_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "robust_location_m_estimation"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_invalid_generated_code_semantic_review_packet"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["authority_binding_commit"] == (
        "03558bacee39ea28d00fa962383f1d1aaaabc31d"
    )
    assert evidence[
        "authority_binding_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 30
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "generated_code_semantic_review_packet_invalid"
    )
    assert evidence["theory_model_tool_turns"] == 13
    assert evidence["independent_theory_review_model_tool_turns"] == 10
    assert evidence["independent_theory_review_accepted"] is True
    assert evidence["algorithm_model_tool_turns"] == 3
    assert evidence["algorithm_source_executions"] == 2
    assert evidence["algorithm_source_owner_revision_observed"] is True
    assert evidence["generated_code_semantic_review_attempts"] == 3
    assert evidence["generated_code_semantic_review_accepted"] is False
    assert evidence["generated_code_semantic_review_validation_error"] == (
        "dimension_reviews must cover each required dimension in order"
    )
    assert evidence["generated_simulation_executed"] is False
    assert evidence["visible_research_evaluation"] == (
        "0/1_incomplete_mode_conformant"
    )
    assert evidence["hidden_gold_evaluation"] == "0/1_failed"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "12/12"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "8/9"
    assert evidence["hidden_theory_semantic_candidate_status"] == "INCONCLUSIVE"
    assert evidence["hidden_theory_semantic_inconclusive_claim"] == (
        "empirical_targets"
    )
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/huber_location_l0_v1.md"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["post_run_shared_mechanism_fix_commits"] == [
        "82083807eb29b57453a9819f308a60e9b27feeda",
        "f5822f58",
        "a73be809",
    ]
    assert "No second model draw occurred" in evidence[
        "post_run_generic_transport_calibration"
    ]
    assert "remains 0/1" in evidence["post_run_shared_mechanism_boundary"]
    assert evidence["algorithm_reference_contract_checks"] == "7/7"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_negative_variants_rejected"] == 3
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_huber_location"
    assert [row["name"] for row in contract["request_fields"]] == [
        "sample",
        "tuning_constant",
    ]
    assert contract["entrypoint"] == "run_estimator"
    assert [row["name"] for row in contract["response_fields"]] == [
        "sample_size",
        "tuning_constant",
        "location_estimate",
        "active_fraction",
        "asymptotic_variance_factor",
        "standard_error",
    ]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_ridge_bias_variance_l0_draw_is_consumed_after_review_tool_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "fixed_design_ridge_bias_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "fixed_design_ridge_regression"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_blocked_invalid_generated_code_semantic_review_packet"
    )
    assert candidate["gold_manifest_sha256"] == (
        "6f977e367f5c110f9960767718f8e8c38af16501a5d797e8432cb3b15c4bb800"
    )
    assert candidate["gold_descriptor_hash"] == (
        "a46c2e1edcddb7495baa80188ffc312085c491af94568a780b372c67de5a75bc"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["visible_question_activation_commit"] == (
        "bf599f4b19ae45bc0ebe8e0b707360188b64c721"
    )
    assert evidence[
        "visible_question_activation_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 26
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "generated_code_semantic_review_packet_invalid"
    )
    assert evidence["runtime_iterations"] == 6
    assert evidence["runtime_traces"] == 6
    assert evidence["runtime_task_handoffs"] == 5
    assert evidence["theory_model_tool_turns"] == 12
    assert evidence["theory_derivation_lines"] == 206
    assert evidence["theory_derivation_sha256"] == (
        "4301d0e2d265968925c39d1b1ee9e3b4a106668d294e403fda804022d1b5dc1a"
    )
    assert evidence["independent_theory_review_model_tool_turns"] == 10
    assert evidence["independent_theory_review_accepted"] is True
    assert evidence["independent_theory_review_lines"] == 281
    assert evidence["independent_theory_review_sha256"] == (
        "fdc6a5b4c598004f8003ffb30ae5ff5dedc40ddd8a35956a7b22f21328627e13"
    )
    assert evidence["algorithm_model_tool_turns"] == 2
    assert evidence["algorithm_source_executions"] == 1
    assert evidence["algorithm_final_source_lines"] == 202
    assert evidence["algorithm_final_source_sha256"] == (
        "f84a9e96b6b8b26e642eda9cd6cccb128b33f5ef446e99dfe4a49c72098d5691"
    )
    assert evidence["generated_code_semantic_review_attempts"] == 1
    assert evidence["generated_code_semantic_review_substantive_verdict"] == (
        "ACCEPT"
    )
    assert evidence["generated_code_semantic_review_accepted"] is False
    assert "RFC 6901" in evidence[
        "generated_code_semantic_review_validation_error"
    ]
    assert evidence["generated_simulation_executed"] is False
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "12/12"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "8/9"
    assert evidence["hidden_theory_semantic_candidate_status"] == "INCONCLUSIVE"
    assert evidence["hidden_theory_combined_passed"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "cb9dcbe9d1d1cd38d73f43c6892c2234d9bca7be"
    )
    assert "same isolated reviewer context" in evidence[
        "post_run_shared_mechanism_fix"
    ]
    assert "remains 0/1" in evidence["post_run_shared_mechanism_boundary"]
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/ridge_bias_variance_l0_v1.md"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert visible_path.is_file()
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    contract = question["estimator_execution_contract"]
    assert question["id"] == candidate["id"]
    assert candidate["task_intent"] == question["task_intent"]
    assert contract["estimator_id"] == "est_fixed_design_ridge"
    assert contract["entrypoint"] == "run_estimator"
    assert [row["name"] for row in contract["request_fields"]] == [
        "design_matrix",
        "response",
        "penalty",
    ]
    assert [row["name"] for row in contract["response_fields"]] == [
        "n_observations",
        "n_features",
        "penalty",
        "coefficients",
        "fitted_values",
        "residual_sum_squares",
        "effective_degrees_of_freedom",
    ]
    assert "authoritative Markdown/LaTeX derivation" in question["description"]
    assert "Lean formalization is not applicable" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_trimmed_match_l1_draw_is_consumed_without_posthoc_rescore() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "trimmed_match_aoas_example_dataset_public_replication"
    )

    assert candidate["level"] == "L1"
    assert candidate["family"] == "causal_geo_experiment_source_replication"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == "fresh_live_v1_hidden_gold_failed"
    assert candidate["gold_runtime_visibility"] == "evaluator_only_after_runtime"
    evidence = candidate["activation_evidence"]
    assert evidence["preactivation_code_head"] == (
        "f290118eaf043f10d28acfc5b93f8ef884c71711"
    )
    assert evidence["activation_commit"] == (
        "68b59afce691fb975d9a35ea48545412f6c076da"
    )
    assert evidence["activation_push_confirmed_before_product_run"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["hidden_gold_activated_before_first_product_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["fresh_live_runs"] == 1
    assert evidence["fresh_live_model"] == "claude-haiku-4-5-20251001"
    assert evidence["fresh_live_model_tier"] == "haiku"
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_iterations"] == 3
    assert evidence["visible_research_evaluation"] == (
        "1/1_complete_conformant_ready"
    )
    assert evidence["hidden_gold_evaluation"] == "0/1_failed"
    assert evidence["independent_reruns"] == "3/3_byte_identical"
    assert evidence["source_replication_calibration_cases"] == "8/8"
    assert evidence["semantic_calibration_cases"] == "6/6"
    assert evidence["semantic_calibration_model"] == "claude-haiku-4-5-20251001"
    assert evidence["semantic_calibration_model_calls"] == 2
    assert evidence["bounded_source_result_projection"] is True
    assert evidence["hash_bound_result_line_reader"] is True
    assert evidence["hidden_identity_harness_execution_attempted"] is False
    assert evidence["hidden_identity_harness_transport_failure"] == (
        "generated code draft exceeds artifact-size boundary"
    )
    assert evidence["hidden_source_report_semantic_judge_calibrated"] is True
    assert evidence["hidden_source_report_semantic_calibration_cases"] == "6/6"
    assert evidence["hidden_source_report_semantic_candidate_status"] == "FAIL"
    assert evidence["post_consumption_shared_harness_fix_commit"] == (
        "c653295a3314589e4bea224c5b56635aaa4750ec"
    )
    assert evidence["post_consumption_score_changed"] is False
    assert evidence["rerun_resume_repair_or_rescore_performed"] is False
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert candidate["task_intent"] == question["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_beta_binomial_l0_draw_is_consumed_as_first_full_task_pass() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "beta_binomial_conjugate_predictive_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "bayesian_conjugate_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == "fresh_live_v1_full_task_gold_passed"
    assert candidate["gold_manifest_sha256"] == (
        "0146a264fcdb3be8bf56d5ba266c9eab041cb64990060cbbeb17567bf22a4d5b"
    )
    assert candidate["gold_descriptor_hash"] == (
        "21d41355b5d992d38d5754e9965bc1335647d844386201f0f7aa81a5a1f10272"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["visible_question_activation_commit"] == (
        "9129db099bdc5bc475766277cb024d201dbc1bee"
    )
    assert evidence[
        "visible_question_activation_push_confirmed_on_work_branch_and_main"
    ] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_iterations"] == 10
    assert evidence["client_tool_model_turns"] == 29
    assert evidence["theory_document_count"] == 2
    assert evidence["theory_document_lines"] == 450
    assert evidence["theory_same_session_tool_error_corrected"] is True
    assert evidence["independent_theory_review_accepted"] is True
    assert evidence["algorithm_source_executions"] == 2
    assert evidence["algorithm_same_session_execution_feedback_corrected"] is True
    assert evidence["algorithm_semantic_review_accepted"] is True
    assert evidence["metric_protocol_preexecution_review_accepted"] is True
    assert evidence["runtime_metric_contracts_passed"] == "8/8"
    assert evidence["simulation_source_executions"] == 1
    assert evidence["simulation_semantic_review_accepted"] is True
    assert evidence["critic_research_disposition"] == "ACCEPT"
    assert evidence["critic_gap_disclosure"] == "COMPLETE"
    assert evidence["hidden_gold_evaluation"] == "1/1_passed"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "12/12"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "9/9"
    assert evidence["hidden_algorithm_checks"] == "10/10"
    assert evidence["hidden_empirical_checks"] == "10/10"
    assert evidence["post_run_generic_metric_review_fix_commit"] == (
        "91fff005efc8a49f4aacb3b3fcd5d619a8884e46"
    )
    assert "did not rerun" in evidence["post_run_shared_mechanism_boundary"]
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is True
    scored = [
        row
        for row in ladder["initial_candidate_queue"]
        if row["status"] in {"active_scored", "consumed_scored"}
    ]
    consumed = [
        row
        for row in scored
        if row["status"] == "consumed_scored"
    ]
    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == len(scored)
    assert readiness["unconsumed_scored_tasks"] == len(scored) - len(consumed)
    assert readiness["consumed_scored_tasks"] == len(consumed)
    assert readiness["fully_gold_configured_tasks"] == len(scored)
    assert readiness["fully_gold_passed_tasks"] == sum(
        row["activation_evidence"].get("full_task_passed") is True
        for row in scored
    )
    assert (
        ladder["current_readiness"]["latest_shared_mechanism_head"]
        == LATEST_SHARED_MECHANISM_HEAD
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_beta_binomial_posterior"
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_pymle_l1_draw_is_consumed_as_first_source_replication_pass() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "pymle_jss_cir_example_public_replication"
    )

    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_passed_with_operator_semantic_caveat"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_iterations"] == 3
    assert evidence["source_replication_runs"] == 1
    assert evidence["runtime_outer_tool_calls"] == 0
    assert evidence["hidden_source_replication_checks"] == "11/11"
    assert evidence["hidden_source_report_semantic_calibration"] == "6/6"
    assert evidence["hidden_gold_evaluation"] == (
        "1/1_passed_under_frozen_evaluator"
    )
    assert "false-accepted" in evidence["operator_semantic_audit"]
    assert evidence["post_run_grounded_semantic_judgment_commit"] == (
        "3c00a515040dff2e21e4ec4666fce7e70b45a8b7"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is True
    readiness = ladder["current_readiness"]
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["source_replication_components_passed"] == 2
    assert readiness["source_replication_full_tasks_passed"] == 1

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]


def test_poisson_garwood_r_l0_records_one_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "poisson_garwood_rate_interval_r_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "poisson_exposure_rate_exact_inference_r"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_with_evaluator_scope_caveat"
    )
    assert candidate["gold_manifest_sha256"] == (
        "b19e33dabf7c585451a822833d3ab4729ca244130d89a2a4719ce4d1becdbfaa"
    )
    assert candidate["gold_descriptor_hash"] == (
        "f6c1ca29ca9be25ccd97e0a5030286640e21d00e041f55dce8ac6bcfc45fcdf1"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["activation_commit"] == (
        "158bb602cb5719ee611baad6865a16c70243f8e1"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["required_model_owned_estimator_language"] == "r"
    assert evidence["required_model_owned_simulation_language"] == "r"
    assert evidence["webr_available"] is True
    assert evidence["algorithm_reference_contract_checks"] == "10/10"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 16000
    assert evidence["semantic_calibration_attempts"] == 3
    assert evidence["semantic_calibration_model_calls"] == 6
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["visible_research_evaluation"] == (
        "1/1_complete_conformant_ready"
    )
    assert evidence["algorithm_final_source_language"] == "r"
    assert evidence["algorithm_final_source_backend"] == "webr"
    assert evidence["simulation_final_source_language"] == "r"
    assert evidence["simulation_final_source_backend"] == "webr"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "8/8"
    assert evidence["hidden_algorithm_checks"] == "8/10"
    assert evidence["hidden_algorithm_failed_atomic_check"] == (
        "invalid_requests_rejected"
    )
    assert evidence["hidden_empirical_checks"] == "6/6"
    assert evidence["hidden_gold_evaluation"] == "0/1_failed_scientific_code"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_poisson_garwood_rate"
    )
    assert "Do not substitute Python" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.R",
        "hidden_empirical_harness.R",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_rao_blackwell_poisson_theory_l0_records_one_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "rao_blackwell_poisson_variance_reduction_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "conditional_expectation_variance_reduction"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_hidden_gold_failed_theory_only_estimator_gate_conflation"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-rao-blackwell-poisson-20260825-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "92b0e4f3edc66351dea4ce459ec371111720e6dfb0e2742bad16e5afde5f05e0"
    )
    assert candidate["gold_descriptor_hash"] == (
        "ff98c895c2f8971093808e8feae0d098c4e64f3d618bf2640bb866388aaa4574"
    )
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )
    assert evidence["preactivation_code_head"] == (
        "1ac05127683e4b37fb45266842fb7c5c2de7f7cb"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "c776b8f0ec8fbd9c6ed2bf3d76ffe4611e735fe1"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["product_model_calls"] == 51
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_head"] == (
        "5c6f77569df0caa37069b756d76448b95e28021f"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["runtime_outer_traces"] == 5
    assert evidence["runtime_architect_traces"] == 3
    assert evidence["runtime_handoffs"] == 4
    assert evidence["runtime_observations"] == 5
    assert evidence["runtime_outer_tool_calls"] == 0
    assert evidence["theory_initial_client_tool_model_turns"] == 9
    assert evidence["theory_revision_client_tool_model_turns"] == 13
    assert evidence["theory_total_client_tool_model_turns"] == 22
    assert evidence["independent_theory_preflight_segments"] == 2
    assert evidence["independent_theory_preflight_client_tool_model_turns"] == 28
    assert evidence["independent_theory_review_attempted"] is True
    assert evidence["independent_theory_review_accepted"] is False
    assert evidence["independent_referee_report_model_verdict"] == "ACCEPT"
    assert (
        evidence[
            "independent_referee_accept_submissions_rejected_for_missing_estimator"
        ]
        == 2
    )
    assert evidence["preflight_final_overall_verdict"] == "REVISE"
    assert evidence["visible_research_evaluation"] == (
        "0/1 incomplete but mode-conformant"
    )
    assert evidence["hidden_gold_evaluation"] == (
        "0/1; no independently accepted serious theory packet was observed, so "
        "hidden structural and semantic theory evaluators did not execute"
    )
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["hidden_theory_semantic_execution_attempted"] is False
    assert evidence["post_run_shared_change_commit"] == (
        "3a6af4086eb229d6ff4f0fee393cb56e37da9d60"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 7
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases"] == 11
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aoms/1177730497"
    assert question["secondary_source"]["year"] == 1945

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_neyman_pearson_theory_l0_draw_is_consumed_and_failed_closed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "neyman_pearson_bernoulli_randomized_test_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "simple_hypothesis_testing"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_failed_theory_revision_task_intent_loss"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-neyman-pearson-bernoulli-20260825-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "afc2124039a126c814295626ce5583e3c44e0074b8ad267c703272b21628dca7"
    )
    assert candidate["gold_descriptor_hash"] == (
        "630230baf92a8ee56dd5fd9aa2411ea9d5aa86f4eccae87dee8cd2ad373854a7"
    )
    assert candidate["gold_runtime_visibility"] == (
        "evaluator_only_after_runtime"
    )
    assert evidence["preactivation_code_head"] == (
        "767768f80d6a38be8d2e803ff70fabe5290a1dee"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "3cc278540dd9bbd2f82d0a45ceba5dcddc3d3c2b"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["runtime_iterations"] == 4
    assert evidence["product_model_calls"] == 36
    assert evidence["client_tool_model_turns"] == 35
    assert evidence["independent_theory_review_accepted"] is False
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["hidden_gold_evaluation"] == (
        "0/1_not_executed_without_independently_accepted_theory"
    )
    assert evidence["post_run_shared_change_commit"] == (
        "8c736798bbcf39ef3b91be199c5bc9be05be0f6c"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 7
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases"] == 11
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1098/rsta.1933.0009"
    assert question["source"]["year"] == 1933

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_complete_randomization_l0_draw_is_consumed_and_failed_closed() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "complete_randomization_neyman_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "finite_population_randomization_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_metric_protocol_and_operator_theory"
    )
    assert candidate["gold_manifest_sha256"] == (
        "fd54b0f306ab7d1a5cb31bc295a58f96a09103889550875d7f17f9ba3bfc9967"
    )
    assert candidate["gold_descriptor_hash"] == (
        "4dfb3bd9a11f4d81881286301cb35e05c0befb575aaa98322eee8518c19fa749"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "7db5330283f32cf4f296b3615568ac3de16b23d9"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_head"] == (
        "0ef27a25e97d24965d6df9d60a4ee46b3f0ea43d"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_kind"] == "blocked"
    assert evidence["runtime_failure_classification"] == (
        "architect_metric_protocol_source_workspace_exhausted"
    )
    assert evidence["runtime_outer_iterations"] == 7
    assert evidence["runtime_task_handoffs"] == 6
    assert evidence["runtime_client_tool_model_turns"] == 35
    assert evidence["theory_developer_model_turns"] == 13
    assert evidence["theory_preflight_model_turns"] == 10
    assert evidence["algorithm_engineer_model_turns"] == 5
    assert evidence["generated_code_semantic_reviewer_model_turns"] == 2
    assert evidence["metric_author_model_turns"] == 2
    assert evidence["metric_semantic_reviewer_model_turns"] == 2
    assert evidence["architect_initial_model_turns"] == 1
    assert evidence["algorithm_reference_contract_checks"] == "15/15"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_populations_passed"] == 3
    assert evidence["empirical_reference_assignments_enumerated"] == 70
    assert evidence["empirical_reference_checks"] == "8/8"
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["theory_markdown_checkpoint_committed"] is True
    assert evidence["theory_preexecution_review_accepted"] is True
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_algorithm_runtime_review_accepted"] is True
    assert evidence["metric_protocol_independently_accepted"] is False
    assert evidence["metric_protocol_candidate_count"] == 2
    assert evidence["metric_protocol_unresolved_high_findings"] == 2
    assert evidence["generated_simulation_executed"] is False
    assert evidence["visible_research_evaluation"] == "0/1"
    assert evidence["hidden_algorithm_checks"] == "13/15"
    assert evidence["hidden_algorithm_failed_atomic_checks"] == [
        "reject_missing_or_extra_request_keys",
        "reject_outcome_entries",
    ]
    assert evidence["hidden_empirical_checks"] == "8/8"
    assert evidence["hidden_empirical_assignments_enumerated"] == 70
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "9/9 SATISFIED"
    assert "false intermediate" in evidence["operator_theory_audit"]
    assert evidence["hidden_gold_evaluation"] == "0/1"
    assert evidence["runtime_manifest_sha256"] == (
        "60c5d5b64aab812015bfcfcccf6f176ee3873f8f4ddf0f5e5b0eb00d83106b35"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "5f1a116d4bde2546d4d0a73cdd1015dab3d8b80976c51f5bd49eb4db55a32492"
    )
    assert evidence["runtime_result_sha256"] == (
        "b52959cde21e5d1dcdea436ac44f0316b8ba71a8bef3defb8dd3d5d6b587cdcc"
    )
    assert evidence["runtime_progress_sha256"] == (
        "ac29391b71af5e3a30d496893315a5bfd621d7e4538be02fc43cfb01c26dda55"
    )
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/complete_randomization_neyman_l0_v1.md"
    )
    assert evidence["post_consumption_shared_metric_source_loop_head"] == (
        "e7d0174a0028aa8ee9371bf2794660a045c465d0"
    )
    assert evidence["post_consumption_shared_metric_source_loop_evidence"] == (
        "future_tasks_regression_only_no_rerun_repair_rescore_or_capability_credit"
    )
    assert evidence["post_consumption_shared_theory_reconstruction_head"] == (
        "b9ece43923ab05cb1185e1493e360658ae14c8fb"
    )
    assert evidence["post_consumption_shared_theory_reconstruction_evidence"] == (
        "future_tasks_regression_only_no_rerun_repair_rescore_or_capability_credit"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False


    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_complete_randomization_neyman"
    assert any(
        row["clause_id"] == "invariant.closed_object_contract"
        for row in contract["invariants"]
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_bootstrap_mean_l0_records_one_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "nonparametric_bootstrap_mean_variance_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "nonparametric_bootstrap"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_scientific_code_and_simulation"
    )
    assert candidate["gold_manifest_sha256"] == (
        "0ba332fbcb78cd99803ba6bec40bb7c4e215cc2a824ff0d667da4a279c450402"
    )
    assert candidate["gold_descriptor_hash"] == (
        "7c1c5be3b4df99de1adb31d53dc74f244cceff8db988928bc81a7a952eb26bb0"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "6034652636448eaf76bcd3eefe1b8fea00501130"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "critic_scientific_rejected"
    )
    assert evidence["runtime_iterations"] == 10
    assert evidence["runtime_architect_traces"] == 3
    assert evidence["algorithm_reference_contract_checks"] == "13/13"
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["empirical_reference_samples_passed"] == 4
    assert evidence["empirical_reference_resamples_enumerated"] == 3664
    assert evidence["empirical_reference_checks"] == "6/6"
    assert evidence["semantic_calibration_cases"] == 9
    assert evidence["semantic_calibration_cases_correct"] == 9
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["blind_reconstruction_mechanism_head"] == (
        "b9ece43923ab05cb1185e1493e360658ae14c8fb"
    )
    assert evidence["metric_source_owner_mechanism_head"] == (
        "e7d0174a0028aa8ee9371bf2794660a045c465d0"
    )
    assert evidence["theory_model_tool_turns"] == 12
    assert evidence["theory_document_count"] == 2
    assert evidence["theory_checkpoint_explicitly_committed"] is True
    assert evidence["independent_theory_review_accepted"] is True
    assert evidence["independent_theory_candidate_document_reads"] == 7
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_calibration"] == "9/9"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == "7/7"
    assert evidence["hidden_algorithm_checks"] == "12/13"
    assert evidence["hidden_algorithm_failed_public_clause"] == (
        "request_fields.sample.edge_cases:no_silent_coercion"
    )
    assert evidence["hidden_empirical_checks"] == "6/6"
    assert evidence["runtime_metric_contracts_passed"] == "7/8"
    assert evidence["runtime_metric_contract_failed"] == "location_equivariant"
    assert evidence["simulation_semantic_review_target_focus_valid"] is False
    assert evidence["hidden_gold_evaluation"] == (
        "0/1_failed_scientific_code_and_runtime_empirical_acceptance"
    )
    assert evidence["post_consumption_shared_diagnostic_boundary_head"] == (
        "26b8e12449aac0f4b6f031cf65896768ae7316ac"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aos/1176344552"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_bootstrap_mean_variance"
    assert {row["clause_id"] for row in contract["empirical_claims"]} == {
        "claim.empirical.protocol_identity",
        "claim.empirical.conditional_mean",
        "claim.empirical.conditional_variance",
        "claim.empirical.normalization_link",
        "claim.empirical.constant_boundary",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_mann_whitney_u_r_l0_records_sole_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "mann_whitney_u_null_moments_r_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "two_sample_rank_inference_r"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_metric_protocol_liveness"
    )
    assert candidate["gold_manifest_sha256"] == (
        "798d7289053073417c44922f0fe8f7f21c91da6015ed8d701a9188598c167994"
    )
    assert candidate["gold_descriptor_hash"] == (
        "677c9b8330d4ee88ca16b4d5f620773b4449af665f5c9dea61a4840fa87a7193"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "8e8d2e7db9328298eb1215cb5b137c70e8f07c33"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["required_model_owned_estimator_language"] == "r"
    assert evidence["required_model_owned_simulation_language"] == "r"
    assert evidence["webr_available"] is True
    assert evidence["algorithm_reference_contract_checks"] == "14/14"
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["empirical_reference_configurations_passed"] == 4
    assert evidence["empirical_reference_assignments_enumerated"] == 41
    assert evidence["empirical_reference_checks"] == "6/6"
    assert evidence["semantic_calibration_cases"] == 9
    assert evidence["semantic_calibration_cases_correct"] == 9
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["exact_estimator_reviewer_probe_mechanism_head"] == (
        "5daec039b8564100b9d2f812bfefdc8cb6e2b24b"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "architect_metric_requirement_packet_validation_failed"
    )
    assert evidence["runtime_research_evaluation"] == "0/1"
    assert evidence["hidden_gold_evaluation"] == "0/1"
    assert evidence["hidden_theory_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_checks"] == "7/7"
    assert evidence["hidden_algorithm_checks"] == "14/14"
    assert evidence["hidden_empirical_checks"] == "6/6"
    assert evidence["generated_code_reviewer_exact_estimator_probes"] == 2
    assert evidence["post_consumption_external_metric_workspace_head"] == (
        "be8d57ab6ec06ffa52f88e3a0e5ddd4a94ec9379"
    )
    assert evidence["metric_protocol_truncated_terminal_inputs"] == 4
    assert evidence["metric_protocol_executed_rejected_submissions"] == 1
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aoms/1177730491"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_mann_whitney_u_moments"
    assert "using language=r" in question["description"]
    assert {row["clause_id"] for row in contract["empirical_claims"]} == {
        "claim.empirical.protocol_identity",
        "claim.empirical.exact_mean",
        "claim.empirical.exact_variance",
        "claim.empirical.complement_symmetry",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.R",
        "hidden_empirical_harness.R",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_inverse_variance_meta_analysis_r_l0_records_sole_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "inverse_variance_fixed_effect_meta_analysis_r_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "fixed_effect_meta_analysis_r"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_metric_protocol_and_algorithm_contract"
    )
    assert candidate["gold_manifest_sha256"] == (
        "8005263b0d339b04aeba9a3417c217c90814544dd9aa7fd223bda8fff9b34ef1"
    )
    assert candidate["gold_descriptor_hash"] == (
        "136f974374dc57862c0d5e91c7caaff23f7c95bef3df4ce553ad68d8f7af581a"
    )
    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["required_model_owned_estimator_language"] == "r"
    assert evidence["required_model_owned_simulation_language"] == "r"
    assert evidence["webr_available"] is True
    assert evidence["algorithm_reference_contract_checks"] == "14/14"
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["empirical_reference_configurations_passed"] == 3
    assert evidence["empirical_reference_estimator_invocations"] == 12000
    assert evidence["empirical_reference_checks"] == "7/7"
    assert evidence["semantic_calibration_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 4
    assert evidence["semantic_calibration_initial_cases_correct"] == 8
    assert evidence["semantic_calibration_final_cases_correct"] == 9
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["activation_commit"] == (
        "74ceafe62d5e22618dd96356252cce949a55e58c"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["external_metric_workspace_mechanism_head"] == (
        "be8d57ab6ec06ffa52f88e3a0e5ddd4a94ec9379"
    )
    assert evidence["runtime_head"] == (
        "a0186de603283986360724ee7ddfce853a67b911"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "architect_metric_requirement_packet_validation_failed"
    )
    assert evidence["runtime_outer_traces"] == 7
    assert evidence["runtime_architect_traces"] == 3
    assert evidence["runtime_handoffs"] == 6
    assert evidence["hidden_theory_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "7/7"
    assert evidence["hidden_algorithm_checks"] == "12/15"
    assert evidence["hidden_empirical_checks"] == "7/7"
    assert evidence["metric_protocol_workspace_messages"] == 21
    assert evidence["metric_protocol_model_tool_calls"] == 10
    assert evidence["metric_protocol_rejected_commits"] == 3
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.2307/3001666"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_fixed_effect_inverse_variance"
    assert "using language=r" in question["description"]
    assert {row["name"] for row in contract["request_fields"]} == {
        "estimates",
        "variances",
        "theta0",
    }
    assert {row["name"] for row in contract["response_fields"]} == {
        "k",
        "weights",
        "estimate",
        "variance",
        "standard_error",
        "z",
    }
    assert {row["clause_id"] for row in contract["empirical_claims"]} == {
        "claim.empirical.protocol_identity",
        "claim.empirical.gaussian_calibration",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.R",
        "hidden_empirical_harness.R",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_mcnemar_exact_l0_records_sole_consumed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "mcnemar_exact_paired_binary_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "paired_binary_exact_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_failed_theory_packet_validation"
    )
    assert candidate["gold_manifest_sha256"] == (
        "92a2ab75e36d7bda98429dd0577627eb17121d3c943820979cd7b6b257e6795e"
    )
    assert candidate["gold_descriptor_hash"] == (
        "bbe929ed2d2e24d93b488014095ffcff5b9f512c2c0bc4d29bd6f2e2e7f7819b"
    )
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "9648fa2b059fddcaa8d76cbb155ef036d989d001"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["mechanical_reference_checks"] == "9/9"
    assert evidence["mechanical_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_dgps"] == 3
    assert evidence["empirical_reference_replicates_per_dgp"] == 4000
    assert evidence["empirical_reference_identity_agreements"] == 12000
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases"] == 12
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["runtime_head"] == (
        "a50a5d18c534a5ebd78a08d11066580cd9732cae"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["runtime_research_evaluation"] == "0/1"
    assert evidence["runtime_outer_traces"] == 3
    assert evidence["runtime_architect_traces"] == 1
    assert evidence["runtime_handoffs"] == 2
    assert evidence["product_model_calls"] == 14
    assert evidence["theory_workspace_model_turns"] == 13
    assert evidence["theory_workspace_tool_executions"] == 13
    assert evidence["theory_workspace_tool_errors"] == 2
    assert evidence["theory_document_lines"] == 210
    assert evidence["theory_document_bytes"] == 10479
    assert evidence["theory_document_sha256"] == (
        "c55db91ae350b12cefd5acd9bb6da4e9181ea412da4195a8f440d9b467590c5a"
    )
    assert evidence["unresolved_compact_derivation_refs"] == 2
    assert evidence["independent_theory_review_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["post_run_shared_change_commit"] == (
        "1a1f11d993654cef8760d1296701155f9b3c68fd"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False

    assert candidate["id"] not in {
        row["id"] for row in ladder["evidence_dimensions"]
    }

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        "5f06fdb9c34813b4fb33f2754dac35a374e9b60fba9a3e7abf74b11ebd8c8d7e"
    )
    assert evidence["visible_question_hash"] == (
        "500a529a0467a2d53f1fbd169f273dec125db0b550d0978d9c9ddc9b4dcb52fb"
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["year"] == 1947
    assert question["source"]["doi"] == "10.1007/BF02295996"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_mcnemar_exact"
    assert evidence["estimator_execution_contract_id"] == (
        "frozen_estimator_execution_contract:0200bfb192384beeecf5"
    )
    assert {row["name"] for row in contract["request_fields"]} == {
        "pairs",
        "alpha",
    }
    assert {row["name"] for row in contract["response_fields"]} == {
        "n_pairs",
        "count_00",
        "count_01",
        "count_10",
        "count_11",
        "discordant_total",
        "marginal_difference",
        "exact_two_sided_p_value",
        "reject",
    }
    assert {row["clause_id"] for row in contract["empirical_claims"]} == {
        "claim.empirical.conditional_exact_size",
        "claim.empirical.null_type_one_calibration",
        "claim.empirical.cell_and_pvalue_identity",
        "claim.empirical.protocol_identity",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_hoeffding_u_statistic_l0_records_one_consumed_caveated_pass() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "hoeffding_degree_two_u_statistic_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "u_statistic_projection_asymptotics"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_full_task_gold_passed_with_operator_math_evaluator_and_"
        "duplicate_handoff_caveats"
    )
    assert candidate["gold_manifest_sha256"] == (
        "0b03e9695a7c4d4fe5c59df963aaf94248ff38c643d29cf8a886dde3edbcfe4c"
    )
    assert candidate["gold_descriptor_hash"] == (
        "176699537cf56b645f1757343e3398e6de64241f91a13ecca99ab19e3605b5b4"
    )
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 7
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases"] == 14
    assert evidence["semantic_calibration_cases_correct"] == 14
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == "claude-haiku-4-5-20251001"
    assert evidence["activation_commit"] == (
        "e35c3d65fee7cf1d869dd5f5bde2de706a1584ff"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_binding_commit"] == (
        "bf0fb93eade11d5d195fe9aaafdc015f388c677a"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_evaluation"] == (
        "1/1_complete_and_mode_conformant"
    )
    assert evidence["hidden_gold_evaluation"] == "1/1"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "8/8"
    assert evidence["runtime_outer_traces"] == 6
    assert evidence["runtime_architect_traces"] == 3
    assert evidence["runtime_handoffs"] == 5
    assert evidence["runtime_observations"] == 7
    assert evidence["runtime_outer_tool_calls"] == 0
    assert evidence["product_model_calls"] == 47
    assert evidence["product_model_call_breakdown"] == {
        "architect_plan": 1,
        "theory_workspace": 22,
        "independent_theory_referee": 23,
        "terminal_critic": 1,
    }
    assert evidence["theory_revision_rounds"] == 1
    assert evidence["first_theory_review_verdict"] == "REVISE"
    assert evidence["first_theory_review_blocking_findings"] == 1
    assert evidence["accepted_theory_review_verdict"] == "ACCEPT"
    assert evidence["accepted_theory_review_blocking_findings"] == 0
    assert evidence["theory_document_sha256"] == (
        "338790b9ecc3b0bc63406e2097ef62dbe743e0310364d0fb555c6aa761c535fb"
    )
    assert evidence["runtime_manifest_sha256"] == (
        "bc06c9a119c612f58932716e72190d12fc36174db437e7642c5879c01e0da725"
    )
    assert evidence["runtime_result_sha256"] == (
        "c334fb7cbcab24bf9426a8f468163735fb01b0c71081875ef03660d503526ed1"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "df57e04aa39730ee5177ef9772ef3777b00a2c68c7decc1d3934da5ce6768892"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is False
    assert evidence["generated_simulation_executed"] is False
    assert evidence["post_run_shared_change_commit"] == (
        "75f05e46a6ff39adda0c694054bdd087cbbd7779"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["full_task_passed"] is True


    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aoms/1177730196"
    assert "conditional-degeneracy" in question["description"]
    assert "Lean formalization" in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_normal_normal_conjugate_l0_records_one_consumed_invalidated_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "normal_normal_conjugate_predictive_known_result"
    )

    assert candidate["level"] == "L0"
    assert candidate["family"] == "bayesian_normal_conjugacy"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_runtime_accepted_hidden_theory_failed_operator_"
        "invalidated_weight_normalization"
    )
    assert candidate["gold_manifest_sha256"] == (
        "e98b0c0e7e7d4e3b5cf1632a89eeaa4e73b7320c6d79fed909e2333b69370914"
    )
    assert candidate["gold_descriptor_hash"] == (
        "96e597b9c538ad8576f0b7ab0616fd3fbad4be8f5a790cd71f0e60f304c313d1"
    )
    assert candidate["task_intent"] == {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }

    evidence = candidate["activation_evidence"]
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "b4c52e9a886d86032f420a7fbbde75e30de8252a"
    )
    assert evidence["activation_identity_commit"] == (
        "a792b7d44f53153852996d3e8c3e32ac0d30d212"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "a792b7d44f53153852996d3e8c3e32ac0d30d212"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_status"] == (
        "ACCEPTED_RUNTIME_HIDDEN_THEORY_FAILED_OPERATOR_INVALIDATED"
    )
    assert evidence["estimator_execution_contract_id"] == (
        "frozen_estimator_execution_contract:f5e43cb7418fde804fd9"
    )
    assert evidence["algorithm_reference_contract_checks"] == "12/12"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_checks"] == "8/8"
    assert evidence["empirical_reference_estimator_invocations"] == 64000
    assert evidence["empirical_negative_variants_rejected"] == 3
    assert evidence["semantic_calibration_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 4
    assert evidence["semantic_calibration_initial_cases_correct"] == 15
    assert evidence["semantic_calibration_final_cases_correct"] == 15
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["runtime_outer_traces"] == 19
    assert evidence["runtime_handoffs"] == 18
    assert evidence["runtime_observations"] == 53
    assert evidence["product_model_calls"] == 123
    assert sum(evidence["product_model_call_breakdown"].values()) == 123
    assert evidence["client_tool_model_turns"] == 119
    assert evidence["client_tool_executions"] == 120
    assert evidence["theory_workspace_model_turns"] == 13
    assert evidence["independent_theory_review_model_turns"] == 12
    assert evidence["independent_theory_review_verdict"] == (
        "ACCEPT_AUTOMATED_FALSE_POSITIVE"
    )
    assert evidence["terminal_critic_status"] == (
        "ACCEPTED_AUTOMATED_FALSE_POSITIVE"
    )
    assert evidence["generated_algorithm_hidden_checks"] == "12/12"
    assert evidence["generated_empirical_hidden_checks"] == (
        "8/8 over 64000 evaluator invocations"
    )
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == (
        "eight SATISFIED plus one INCONCLUSIVE"
    )
    assert evidence["runtime_manifest_sha256"] == (
        "6e4a68442e73d54278d8cd6edabb9c7c60400aad1f39c19e1cc01ff057d91220"
    )
    assert evidence["runtime_result_sha256"] == (
        "8536931e6d7e85158bf1d191faf13d01ea1430fedb644241bfe0b2bf1d4c8c3e"
    )
    assert evidence["hidden_gold_report_sha256"] == (
        "1d78f6ea68ff2b5d23c4ec48fab130e6bc3463a45efa683cd2cde2c804e2b607"
    )
    assert evidence["operator_audit_disposition"] == "INVALIDATED"
    assert evidence["operator_theory_status"] == (
        "failed_required_posterior_weight_normalization"
    )
    assert Path(evidence["operator_audit_path"]).is_file()
    assert evidence["post_run_shared_change_commit"] == (
        "39d42c18b09c34221f6b09dc6f5f49991b9540f6"
    )
    assert evidence["post_run_shared_review_trace_commit"] == (
        "ea2b8bad4b735ba963904a299837d560ed016442"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is True
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["ladder_score_after_consumption"] == "4/46"


    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["doi"] == "10.1214/aos/1176344611"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_normal_normal_predictive"
    assert contract["entrypoint"] == "run_estimator"
    assert {row["name"] for row in contract["request_fields"]} == {
        "prior_mean",
        "prior_variance",
        "observation_variance",
        "observations",
    }
    assert {row["name"] for row in contract["response_fields"]} == {
        "n",
        "sample_mean",
        "prior_precision",
        "data_precision",
        "posterior_mean",
        "posterior_variance",
        "posterior_standard_deviation",
        "predictive_mean",
        "predictive_variance",
        "predictive_standard_deviation",
    }

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "reference_estimator.py",
    ):
        assert hidden_name not in runtime_visible


def test_srswor_l0_records_one_consumed_hidden_code_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "srswor_finite_population_mean_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "finite_population_design_based_sampling"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_runtime_accepted_hidden_code_failed_operator_invalidated"
    )
    assert candidate["gold_manifest_sha256"] == (
        "e8df6ef6ce7281e7cd8bc09fa69a2b05ab6de7b22adf5618a455dd1b79a80697"
    )
    assert candidate["gold_descriptor_hash"] == (
        "10f10d98142c406f5bcf11167c3053f80c93076708bfdc9c5872f2730cc1f97e"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "247a439013d6e317c5fc6e724b6354f57c6c7f72"
    )
    assert evidence["activation_identity_commit"] == (
        "791fe29880da501da0ce696c789b7a3497d1ffe2"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "791fe29880da501da0ce696c789b7a3497d1ffe2"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_model_policy_status"] == "OK"
    assert evidence["runtime_enabled_llm_agents_exact_haiku"] == 7
    assert evidence["runtime_sonnet_or_opus_calls"] == 0
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_eval_complete"] is True
    assert evidence["runtime_outer_traces"] == 17
    assert evidence["runtime_architect_traces"] == 6
    assert evidence["estimator_execution_contract_id"] == (
        "frozen_estimator_execution_contract:8ddd8c21a18449b379bf"
    )
    assert evidence["algorithm_reference_contract_checks"] == "12/12"
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_checks"] == "6/6"
    assert evidence["empirical_reference_estimator_invocations"] == 96000
    assert evidence["empirical_negative_variants_rejected"] == 3
    assert evidence["semantic_calibration_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 4
    assert evidence["semantic_calibration_cases_correct"] == 13
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is True
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "10/10 SATISFIED"
    assert evidence["hidden_algorithm_contract_checks"] == "11/12"
    assert evidence["hidden_empirical_checks"] == "6/6"
    assert evidence["hidden_empirical_estimator_invocations"] == 96000
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["operator_audit_disposition"] == "INVALIDATED"
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["ladder_score_after_consumption"] == "4/47"
    assert Path(evidence["operator_audit_path"]).is_file()


    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["isbn"] == "9780471162407"
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_srswor_population_mean"
    assert contract["entrypoint"] == "run_estimator"
    assert {row["name"] for row in contract["request_fields"]} == {
        "population_size",
        "sample_values",
    }
    assert len(contract["response_fields"]) == 9
    assert len(contract["empirical_claims"]) == 5

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "reference_estimator.py",
    ):
        assert hidden_name not in runtime_visible


def test_normal_variance_ratio_l0_consumed_draw_is_operator_invalid_and_immutable() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "two_sample_normal_variance_ratio_f_interval_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "two_sample_normal_variance_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_runtime_blocked_hidden_not_executed_operator_invalidated"
    )
    assert candidate["gold_manifest_sha256"] == (
        "c57df47a5e98be8f1703d0b88f34410baf813de0fe2ee0cc517011c1aa029df9"
    )
    assert candidate["gold_descriptor_hash"] == (
        "e9799114dbb4acf033fdc4edf394c9c8f84be32ebbf39bda46c91c08c02d975b"
    )
    assert evidence["activation_commit"] == (
        "ef93a91da4f90422790a41f886ad3f5b207c6191"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_calibration_cases_correct"] == 13
    assert evidence["algorithm_reference_contract_checks"] == "12/12"
    assert evidence["empirical_reference_estimator_invocations"] == 48000
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_llm_agents_exact_haiku"] == 7
    assert evidence["runtime_sonnet_or_opus_calls"] == 0
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is False
    assert evidence["operator_audit_disposition"] == (
        "OPERATOR_INVALID_BENCHMARK"
    )
    assert evidence["trusted_capability_credit"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["post_run_score_changed"] is False
    assert (
        ladder["current_readiness"]["operator_invalid_tasks"]
        == CURRENT_OPERATOR_INVALID_TASKS
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_normal_variance_ratio_interval"
    assert {row["name"] for row in contract["request_fields"]} == {
        "sample_x",
        "sample_y",
        "alpha",
    }
    assert len(contract["response_fields"]) == 9
    assert len(contract["empirical_claims"]) == 5

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "reference_estimator.py",
    ):
        assert hidden_name not in runtime_visible


def test_one_way_anova_l0_records_its_only_consumed_product_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "one_way_normal_anova_f_test_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "one_way_normal_anova"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_runtime_accepted_hidden_theory_failed_operator_false_acceptance"
    )
    assert candidate["gold_manifest_sha256"] == (
        "b6871aae214cff9ec364d9022c580ca3cdab2b8aab7806c1324473ef0ca14569"
    )
    assert candidate["gold_descriptor_hash"] == (
        "df12d2accdeb8abc017404323166fcbb37a36dc537cc0aaaa9d09f189f04ec76"
    )
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 2
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "12582911c5aff9705e675da9095545871b459527"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["activation_identity_commit"] == (
        "9685cce1f187db754f521b677b08b428d1c4f707"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["semantic_calibration_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 4
    assert evidence["semantic_calibration_initial_cases_correct"] == 11
    assert evidence["semantic_calibration_final_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["algorithm_reference_checks"] == "8/8"
    assert evidence["algorithm_reference_estimator_invocations"] == 17
    assert evidence["algorithm_negative_variants_rejected"] == 1
    assert evidence["empirical_reference_checks"] == "8/8"
    assert evidence["empirical_reference_estimator_invocations"] == 12000
    assert evidence["empirical_negative_variants_rejected"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "ACCEPTED_RUNTIME_OPERATOR_FAILED_THEORY"
    assert evidence["runtime_research_evaluation"] == (
        "1/1 complete and mode-conformant"
    )
    assert evidence["runtime_outer_traces"] == 10
    assert evidence["runtime_architect_traces"] == 3
    assert evidence["runtime_client_tool_model_turns"] == 51
    assert evidence["theory_authoritative_document_lines"] == 502
    assert evidence["independent_theory_referee_verdict"].startswith("FALSE_ACCEPT")
    assert "omits N(Y_bar_all-mu)^2" in evidence["operator_theory_defect"]
    assert evidence["hidden_theory_mechanical_checks"].startswith("6/7")
    assert evidence["hidden_theory_semantic_claims"].startswith("9/9 SATISFIED")
    assert evidence["hidden_algorithm_checks"] == (
        "8/8 over 17 exact estimator invocations"
    )
    assert evidence["hidden_empirical_checks"] == (
        "8/8 over four frozen Gaussian-null designs and 12,000 exact estimator invocations"
    )
    assert evidence["runtime_metric_contracts"] == "8/8 passed"
    assert evidence["hidden_gold_evaluation"] == (
        "0/1; required theory failed; code and empirical components passed"
    )
    assert evidence["operator_audit_disposition"] == "OPERATOR_FAILED_THEORY"
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "6658c7626664b0287eaa1afc3d6cb14252225599"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_one_way_anova"
    assert {row["name"] for row in contract["request_fields"]} == {"groups"}
    assert len(contract["response_fields"]) == 8
    assert len(contract["empirical_claims"]) == 5

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "reference_estimator.py",
        "negative_open_request_contract.py",
        "negative_scaled_f.py",
    ):
        assert hidden_name not in runtime_visible


def test_two_period_panel_did_l0_records_one_consumed_operator_invalid_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "two_period_panel_did_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "two_period_panel_difference_in_differences"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_operator_invalidated_theory_code_contract_"
        "failed_confirmatory_empirical_not_run"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-two-period-panel-did-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "42861f1008104b3e77db93376784eaec699abe181664b675bbbdba5b9cc20653"
    )
    assert candidate["gold_descriptor_hash"] == (
        "78fd9fc658b3acf29a57d2949a69f831a4ad385596abef03a056e2fe974156f1"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "78fd9fc658b3acf29a57d2949a69f831a4ad385596abef03a056e2fe974156f1"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "a8d193f806af81e5000e1227e3e29c5792df3a8b"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 6
    assert evidence["algorithm_reference_contract_checks"] == "19/19"
    assert evidence["algorithm_reference_maximum_absolute_error"] == 0.0
    assert evidence["empirical_reference_replicates_per_dgp"] == 2000
    assert evidence["empirical_reference_dgps_passed"] == 8
    assert evidence["empirical_reference_invocation_failures"] == 0
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["runtime_head"] == (
        "d388a0ce6d9e27ce7fbf2075d4b3657b9cabce1c"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_sonnet_or_opus_calls"] == 0
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_outer_iterations"] == 8
    assert evidence["runtime_failure_classification"] == (
        "critic_scientific_inconclusive"
    )
    assert evidence["runtime_research_evaluation"].startswith("0/1")
    assert evidence["automated_hidden_evaluation"] == "0/1"
    assert evidence["hidden_theory_checks"].startswith("7/7")
    assert "operator-invalidated" in evidence["hidden_theory_checks"]
    assert evidence["hidden_algorithm_checks"].startswith("17/19")
    assert evidence["hidden_empirical_checks"].startswith("13/13")
    assert evidence["runtime_manifest_sha256"] == (
        "a990b80871166265c7af04d514530fa2f9d871a2b5e867eba949230b8ec5203c"
    )
    assert evidence["runtime_result_sha256"] == (
        "ad3925dbb8964a4eb2e92ba6a037634687cecdbbdd78aa14e1e843ade930eaee"
    )
    assert evidence["hidden_gold_evaluation_sha256"] == (
        "b820f353e865594feb3430505ca302c4f16ba4e421e2c6802ba44541ab8411e2"
    )
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_THEORY_CODE_CONTRACT_FAILED_CONFIRMATORY_"
        "EMPIRICAL_NOT_RUN"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        "9dcd43555dc489790ae2dc091f161b9ab319e48f"
    )
    assert "same model session" in evidence["post_run_shared_mechanism_change"]
    assert "986/986" in evidence["post_run_regression_evidence"]
    assert evidence["ladder_score_after_consumption"] == "4/67"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1111/0034-6527.00321"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_two_period_panel_did"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_pyod_abod_l1_records_one_consumed_semantic_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "pyod_abod_example_public_replication"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L1"
    assert candidate["family"] == "anomaly_detection_source_replication"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_runtime_accepted_hidden_source_report_semantic_failed"
    )
    assert candidate["source_snapshot_hash"] == (
        "aa5219ef58f5b24ae3bd8477668d7cb65163fed4e74f6e0d33bc66f324e2c82d"
    )
    assert candidate["source_repository_commit"] == (
        "690a0f25987fab0664b014bbc7121d999c92f5f6"
    )
    assert candidate["gold_manifest_sha256"] == (
        "01502bf0c6e40745f35c2d6fcce68c212e6e31d9d0f93b5a0973de6f23a71ee6"
    )
    assert candidate["gold_descriptor_hash"] == (
        "2e0c3bb81dfe3ef3747912513f8afd62bee7e95ad879190ca945edfe24b9bdce"
    )
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 0
    assert evidence["activation_negative_controls_rejected"] == 0
    assert evidence["source_harness_reference_passed"] is True
    assert evidence["source_harness_negative_controls_rejected"] == 8
    assert evidence["source_harness_calibration_cases"] == "9/9"
    assert evidence["independent_source_reruns"].startswith("3/3")
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == "6/6"
    assert evidence["semantic_reference_claims"] == 6
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "7669de368038b9a7dc3534c1551cfe71b464ebcc"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["activation_identity_commit"] == (
        "45a2271677b7428512f996fb5497451055c13581"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_evaluation"] == (
        "1/1 complete and mode-conformant"
    )
    assert evidence["runtime_outer_traces"] == 3
    assert evidence["runtime_architect_traces"] == 1
    assert evidence["runtime_handoffs"] == 2
    assert evidence["runtime_observations"] == 5
    assert evidence["runtime_outer_tool_calls"] == 0
    assert evidence["runtime_product_model_calls"] == 29
    assert evidence["source_replication_runs"] == 1
    assert evidence["source_replication_checkpoint_id"] == (
        "source_replication_checkpoint:842653347b820d07a10c"
    )
    assert evidence["source_replication_manifest_hash"] == (
        "996ac281eeb4eb53f20412cab1a0eb6f8b8875536033f84a751b7c1acd93d116"
    )
    assert evidence["source_report_sha256"] == (
        "2e78ef9ba61465a31616db28c5abea16d98ffd682d9ff1019449b6592e2276d3"
    )
    assert evidence["hidden_source_replication_checks"] == "12/12"
    assert evidence["hidden_source_report_semantic_calibration"] == "6/6"
    assert evidence["hidden_source_report_semantic_claims"] == (
        "5/6 SATISFIED; claim 5 VIOLATED; candidate FAIL"
    )
    assert evidence["hidden_gold_evaluation"] == (
        "0/1; exact source mechanics passed but required source-report semantics failed"
    )
    assert "n_neighbors" in evidence["hidden_semantic_failure"]
    assert evidence["operator_audit_disposition"] == (
        "OPERATOR_CONFIRMED_HIDDEN_SOURCE_REPORT_FAILURE"
    )
    assert evidence["post_run_shared_mechanism_fix_commit"] == (
        "936bd137ed6ebfa01b0751f24a7f963afd645c7a"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["runtime_source_replication_components_ready"] == (
        CURRENT_SOURCE_REPLICATION_COMPONENTS_READY
    )
    assert readiness["source_replication_components_passed"] == 2
    assert readiness["source_replication_full_tasks_passed"] == 1

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert "v1.1.3" in question["description"]
    assert "v0.7.0" not in question["description"]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_weighted_partial_regression_l0_records_its_only_consumed_failed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "weighted_partial_regression_identity_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "weighted_partitioned_regression"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_failed_theory_and_reviewer_lifecycle"
    )
    assert candidate["gold_manifest_sha256"] == (
        "7255132932bd1425c42406522b88b2f6d5f4709fac01b9a07b238cad3a4a1f75"
    )
    assert candidate["gold_descriptor_hash"] == (
        "c6a0c78a48b3339dbba508dd064e11938e6a8c3ec21ce0aaba2a4959c6528b35"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "a1ca9c327ed7606795a562ab4f86cc46a9e12139"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 5
    assert evidence["mechanical_reference_checks"] == "5/5"
    assert evidence["algorithm_reference_checks"] == "17/17"
    assert evidence["algorithm_reference_estimator_invocations"] == 22
    assert evidence["algorithm_negative_variants_rejected"] == 3
    assert evidence["empirical_reference_checks"] == "10/10"
    assert evidence["empirical_reference_scenarios"] == 4
    assert evidence["empirical_reference_estimator_invocations"] == 12000
    assert evidence["empirical_negative_variants_rejected"] == 2
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 14
    assert evidence["semantic_reference_claims"] == 11
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_status"].startswith("BLOCKED after 20 outer traces")
    assert evidence["runtime_product_model_calls"] == 128
    assert evidence["runtime_client_tool_model_turns"] == 126
    assert evidence["runtime_direct_architect_calls"] == 2
    assert evidence["hidden_theory_mechanical_checks"].startswith("4/5")
    assert evidence["hidden_theory_semantic_claims"].startswith("10/11 SATISFIED")
    assert evidence["accepted_algorithm_handoff"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["hidden_gold_evaluation"].startswith("0/1")
    assert evidence["post_run_shared_harness_commit"] == (
        "de531ad8d4173cc406593edb76606cb10be158b7"
    )
    assert "future-task" in evidence[
        "post_run_shared_harness_evidence"
    ].lower()
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == "10.2307/1907330"
    assert question["source"]["extension_paper"]["doi"] == (
        "10.1080/01621459.1963.10480682"
    )
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_weighted_partial_regression"
    assert contract["entrypoint"] == "run_estimator"
    assert len(contract["request_fields"]) == 4
    assert len(contract["response_fields"]) == 8
    assert len(contract["invariants"]) == 5
    assert len(contract["empirical_claims"]) == 5

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "reference_estimator.py",
        "theory_reference.md",
        "theory_rubric.json",
        "theory_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_clopper_pearson_l0_single_draw_is_consumed_and_scored() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "clopper_pearson_binomial_interval_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "exact_binomial_confidence_intervals"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_theory_and_scientific_code_failed_empirical_passed"
    )
    assert candidate["gold_manifest_sha256"] == (
        "5f9a02121cbf139753c0f185d3b4d369a91b2e5427e65d6231ec747b5eb5d565"
    )
    assert candidate["gold_descriptor_hash"] == (
        "757e30849fdbee046f7d6759f91ee52db1aafc2a742437adef57e12fef63958b"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "73248fc8eda1e9ec52fdcbb1b6fe41b10aa6ce99"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 7
    assert evidence["mechanical_reference_checks"] == "5/5"
    assert evidence["algorithm_reference_checks"] == "11/11"
    assert evidence["algorithm_reference_estimator_invocations"] == 34
    assert evidence["algorithm_negative_variants_rejected"] == 4
    assert evidence["empirical_reference_checks"] == "8/8"
    assert evidence["empirical_reference_scenarios"] == 4
    assert evidence["empirical_reference_estimator_invocations"] == 16213
    assert evidence["empirical_negative_variants_rejected"] == 3
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "254a7aef345bc780bbe3d9fa71dbf32c6c49480d"
    )
    assert evidence["runtime_outer_traces"] == 33
    assert evidence["runtime_outer_graph_iterations"] == 32
    assert evidence["runtime_same_owner_workspace_continuations"] == 1
    assert evidence["runtime_client_tool_model_turns"] == 199
    assert evidence["runtime_client_tool_executions"] == 203
    assert evidence["accepted_theory_packet_id"] == (
        "theory_derivation:dcec30e6a486e1dc77a0ab46"
    )
    assert evidence["evaluated_algorithm_source_sha256"] == (
        "1a7187842d7e0a6138de4c674632d45cc0e5870b01b8a9f42cf827461db00922"
    )
    assert evidence["hidden_algorithm_execution_attempted"] is True
    assert evidence["hidden_empirical_execution_attempted"] is True
    assert evidence["hidden_empirical_checks"].startswith("8/8")
    assert evidence["post_run_shared_harness_commit"] == (
        "54e5ca52eca6192885a8a11775f7728997610ac7"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1093/biomet/26.4.404"
    )
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_clopper_pearson_interval"
    assert contract["entrypoint"] == "run_estimator"
    assert len(contract["request_fields"]) == 3
    assert len(contract["response_fields"]) == 4
    assert len(contract["invariants"]) == 4
    assert len(contract["empirical_claims"]) == 4

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "reference_estimator.py",
        "theory_reference.md",
        "theory_rubric.json",
        "theory_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_ols_press_l0_consumed_draw_preserves_component_evidence() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "ols_press_leave_one_out_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "ordinary_least_squares_leave_one_out"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_metric_authoring_"
        "scientific_code_failed_theory_and_hidden_empirical_passed"
    )
    assert candidate["gold_manifest_sha256"] == (
        "4823a8c255b621a1adf9c69d8cd5cb581827f9f21e0b553c4c89ef88dd6b14fa"
    )
    assert candidate["gold_descriptor_hash"] == (
        "b93c763e1eb1bad38d6dfbfeb9c339e02df869fdbd9b1e1c501387817d8cefbe"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "abecde67d90b48dfc0ca1b7e45fbea270140c198"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 3
    assert evidence["algorithm_reference_checks"] == "9/9"
    assert evidence["algorithm_reference_valid_cases"] == 4
    assert evidence["algorithm_reference_invalid_requests_rejected"] == 18
    assert evidence["empirical_reference_checks"] == "11/11"
    assert evidence["empirical_reference_scenarios"] == 4
    assert evidence["empirical_reference_estimator_invocations"] == 2000
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 14
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "769054e214df0c875399db59e7addcdc6150d1dd"
    )
    assert evidence["runtime_product_model_calls"] == 49
    assert evidence["runtime_client_tool_model_turns"] == 48
    assert evidence["runtime_client_tool_executions"] == 48
    assert evidence["runtime_outer_traces"] == 7
    assert evidence["runtime_handoffs"] == 6
    assert evidence["accepted_theory_packet_hash"] == (
        "516538ffe16745c261c8619d57f5a2b3a12433aab50e04c1c28314e075add189"
    )
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"].startswith("10/10")
    assert evidence["hidden_algorithm_checks"].startswith("8/9")
    assert evidence["hidden_empirical_checks"].startswith("11/11")
    assert evidence["generated_simulation_executed"] is False
    assert evidence["post_run_shared_harness_commit"] == (
        "ea907357214d7193e59e87405a8917cecda5849d"
    )
    assert evidence["post_run_score_changed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1080/00401706.1974.10489157"
    )
    assert question["source"]["implementation_convention"]["commit"] == (
        "9307ef1b3a975a3807009432cbb489c4ae6f5c60"
    )
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_ols_press"
    assert contract["entrypoint"] == "run_estimator"
    assert len(contract["request_fields"]) == 2
    assert len(contract["response_fields"]) == 6
    assert len(contract["invariants"]) == 5
    assert len(contract["empirical_claims"]) == 4

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "reference_estimator.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_rdrobust_senate_l1_records_consumed_operator_false_acceptance() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"]
        == "rdrobust_senate_python_illustration_public_replication"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L1"
    assert candidate["family"] == "regression_discontinuity_source_replication"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_runtime_accepted_hidden_source_report_semantic_automated_"
        "pass_operator_false_acceptance"
    )
    assert candidate["source_snapshot_hash"] == (
        "9afb817e88f385b6cdda4048ff0f1903c0e7d88f6799ca9128ec113b2613a954"
    )
    assert candidate["source_repository_commit"] == (
        "7dd25671b8f28fc8618b1b7aa4a981564ee53f75"
    )
    assert candidate["gold_manifest_sha256"] == (
        "d6686927069f8bb6228c8175165a6456dcfbd3c99f671196a55280bcd53a339d"
    )
    assert candidate["gold_descriptor_hash"] == (
        "7937cfc1340318ee29c10ffcd2359a25dae806202fde5cd015b05574530e7a18"
    )
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 0
    assert evidence["activation_negative_controls_rejected"] == 0
    assert evidence["source_harness_reference_passed"] is True
    assert evidence["source_harness_negative_controls_rejected"] == 10
    assert evidence["source_harness_calibration_cases"] == "11/11"
    assert evidence["independent_source_reruns"].startswith("3/3")
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == "8/8"
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "3e844a12fa25a77830aa81b1784b18e64a2f139d"
    )
    assert evidence["activation_identity_commit"] == (
        "fba535c8462205c19ed783c57f4b47c9e1006181"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "fba535c8462205c19ed783c57f4b47c9e1006181"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_evaluation"].startswith("1/1")
    assert evidence["runtime_product_model_calls"] == 18
    assert evidence["runtime_traces"] == 3
    assert evidence["runtime_architect_calls"] == 1
    assert evidence["runtime_handoffs"] == 2
    assert evidence["runtime_observations"] == 5
    assert evidence["runtime_outer_tool_calls"] == 0
    assert evidence["source_workspace_model_turns"] == 16
    assert evidence["source_workspace_tools"] == 20
    assert sum(evidence["source_workspace_tool_breakdown"].values()) == 20
    assert evidence["hidden_source_checks"] == "10/10"
    assert evidence["hidden_semantic_calibration_cases_correct"] == "8/8"
    assert "operator audit" in evidence["hidden_semantic_claim_assessments"]
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_SOURCE_REPORT_FALSE_ACCEPTANCE"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        "0134c4cb5361956ed328dfd0de3db77210695a88"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/54"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["runtime_source_replication_components_ready"] == (
        CURRENT_SOURCE_REPLICATION_COMPONENTS_READY
    )
    assert readiness["source_replication_components_passed"] == 2
    assert readiness["source_replication_full_tasks_passed"] == 1
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["repository_commit"] == (
        candidate["source_repository_commit"]
    )
    assert question["source"]["research_source_snapshot_hash"] == (
        candidate["source_snapshot_hash"]
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_statsmodels_adf_kpss_l1_records_consumed_operator_false_acceptance() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "statsmodels_adf_kpss_sunspots_public_replication"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L1"
    assert candidate["family"] == "time_series_stationarity_source_replication"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_runtime_accepted_hidden_source_report_semantic_automated_"
        "pass_operator_false_acceptance"
    )
    assert candidate["source_snapshot_hash"] == (
        "83a0acc9580245724b081e5aca45bedde3feb3ffd95966b5049a05b71bb6ee0c"
    )
    assert candidate["source_repository_commit"] == (
        "40e6a84d26ac74623c6b94b718f0987ef0351c53"
    )
    assert candidate["gold_manifest_sha256"] == (
        "d8c055edeaf77324a951f39b4a7578e314b702bdacaddec683cacdca57057bc0"
    )
    assert candidate["gold_descriptor_hash"] == (
        "02d124ccc856c0b760b00fef1aa588e501ad9bb360818c13a6654d5993d021c2"
    )
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 0
    assert evidence["activation_negative_controls_rejected"] == 0
    assert evidence["source_harness_reference_passed"] is True
    assert evidence["source_harness_negative_controls_rejected"] == 11
    assert evidence["source_harness_calibration_cases"] == "12/12"
    assert evidence["independent_source_reruns"].startswith("3/3")
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == "9/9"
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_commit"] == (
        "b0ce95568be18cde682d8e57b1de6141c8e35acd"
    )
    assert evidence["activation_identity_commit"] == (
        "85c5db1bbe65b9be10d0a7029f5ef75c0d5b70a7"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "85c5db1bbe65b9be10d0a7029f5ef75c0d5b70a7"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_evaluation"].startswith("1/1")
    assert evidence["runtime_product_model_calls"] == 38
    assert evidence["runtime_traces"] == 3
    assert evidence["runtime_architect_calls"] == 1
    assert evidence["runtime_handoffs"] == 2
    assert evidence["runtime_observations"] == 5
    assert evidence["runtime_outer_tool_calls"] == 0
    assert evidence["source_workspace_model_turns"] == 22
    assert evidence["source_workspace_tools"] == 28
    assert sum(evidence["source_workspace_tool_breakdown"].values()) == 28
    assert evidence["hidden_source_checks"] == "11/11"
    assert evidence["hidden_semantic_calibration_cases_correct"] == "9/9"
    assert "operator audit" in evidence["hidden_semantic_claim_assessments"]
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_SOURCE_REPORT_AND_REVIEWER_FALSE_ACCEPTANCE"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        "e5cccbb276bb1ef66bb5f387b1bc992b4dfaa74c"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is True
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/55"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["runtime_source_replication_components_ready"] == (
        CURRENT_SOURCE_REPLICATION_COMPONENTS_READY
    )
    assert readiness["source_replication_components_passed"] == 2
    assert readiness["source_replication_full_tasks_passed"] == 1
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["repository_commit"] == (
        candidate["source_repository_commit"]
    )
    assert question["source"]["research_source_snapshot_hash"] == (
        candidate["source_snapshot_hash"]
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_source_replication_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_nadaraya_watson_l0_records_consumed_operator_invalidated_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "nadaraya_watson_pointwise_asymptotics_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "nonparametric_kernel_regression"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_runtime_and_hidden_automated_pass_operator_invalidated_theory"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-nadaraya-watson-20260826-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "8729698eabacda0ebbe7a6ad9ab4358c1b436f923010344b0b8761e8ee184329"
    )
    assert candidate["gold_descriptor_hash"] == (
        "6a69d4af60704985bd28417a5c569d47b275550c777c92ad363f7a49d5808770"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["schema2_authority_binding_commit"] == (
        "5c3adcf2818c6897391ba2084838f8a50bd5af54"
    )
    assert evidence["authority_binding_commit"] == (
        "8364ff9aa2c14ca6746cfee6fc5d7ca29f1e0f11"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 0
    assert evidence["activation_negative_controls_rejected"] == 0
    assert evidence["preactivation_failed_launches"] == 1
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["mechanical_reference_checks"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == 7
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "46cfc2cef08380f6a3c9e503687af63c88671c78"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_product_model_calls"] == 86
    assert evidence["automated_hidden_evaluation"] == "1/1"
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_THEORY_AND_REVIEWER_FALSE_ACCEPTANCE"
    )
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_57_SHARED_MECHANISM_HEAD
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == "10.1137/1109020"
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_brier_bernoulli_l0_records_one_consumed_empirical_authority_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "brier_score_bernoulli_mean_known_result"
    )
    evidence = candidate["activation_evidence"]
    result = candidate["evaluation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "proper_scoring_rules_binary_forecasts"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_false_accept_empirical_evidence_missing"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-brier-bernoulli-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "d597aeb11154a1c4bebc48350a2314b7fad2eb01384d24819bea17d338d56411"
    )
    assert candidate["gold_descriptor_hash"] == (
        "bcd952c7722cb8c41d0ba0e9bcd2bfbb34dbf21be449c579dfc7693036d38547"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "f5671e18f3063be80f5b1703ee89a959acfd6896968fe1bc7933453855cf7552"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "56c66b561a394de933569f65cb5efe4e45cf1b9b"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 5
    assert evidence["algorithm_reference_contract_checks"] == "11/11"
    assert evidence["empirical_reference_replicates_per_dgp"] == 3000
    assert evidence["empirical_reference_dgps_passed"] == 3
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 8
    assert evidence["semantic_reference_claims"] == 6
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    assert result["runtime_head"] == (
        "c3df994833e20b35e0229358998d5938090702ac"
    )
    assert result["runtime_model"] == "claude-haiku-4-5-20251001"
    assert result["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert result["runtime_sonnet_or_opus_calls"] == 0
    assert result["runtime_status"] == "ACCEPTED"
    assert result["runtime_research_evaluation"].startswith("0/1")
    assert result["automated_hidden_evaluation"] == "0/1"
    assert "7/7" in result["theory_result"]
    assert "6/6" in result["theory_result"]
    assert "not attempted" in result["algorithm_result"]
    assert "acceptance_passed" in result["empirical_finding"]
    assert "false ACCEPT" in result["critic_finding"]
    assert "retired" in result["hidden_evaluator_finding"]
    assert result["operator_disposition"] == (
        "RUNTIME_FALSE_ACCEPTED_EMPIRICAL_EVIDENCE_MISSING"
    )
    assert Path(result["operator_audit"]).is_file()
    assert result["post_run_shared_mechanism_commits"] == [
        "7e7c1a2e5837308a77770bbca994e0e059842294",
        "b55a163388ba795d05bb48cd4194881ede829223",
    ]
    assert result["full_task_passed"] is False
    assert result["trusted_capability_credit"] is False
    assert result["ladder_score_after_consumption"] == "4/64"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_warner_randomized_response_l0_records_one_immutable_failed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "warner_randomized_response_prevalence_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "survey_privacy_randomized_response"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_skipped_required_empirical_lane_"
        "code_contract_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-warner-randomized-response-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "a59d1376ac69b07c50239da0407356d1c1cec9d8a5a5e85dcf275e89ab3d60bc"
    )
    assert candidate["gold_descriptor_hash"] == (
        "6145f22c0360cf8fe0a9b8c1488d338bbcbc52b3231a2e9041499021c01aa274"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "6145f22c0360cf8fe0a9b8c1488d338bbcbc52b3231a2e9041499021c01aa274"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "1980112d55ce962d006742fa6db9fd108e8555aa"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 7
    assert evidence["algorithm_reference_contract_checks"] == "12/12"
    assert evidence["empirical_reference_replicates_per_dgp"] == 3000
    assert evidence["empirical_reference_dgps_passed"] == 10
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 10
    assert evidence["semantic_reference_claims"] == 7
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False

    assert evidence["runtime_head"] == (
        "08346840eb328332c8c78d06af218c997c7fabcc"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_sonnet_or_opus_calls"] == 0
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_outer_iterations"] == 8
    assert evidence["runtime_failure_classification"] == (
        "critic_packet_validation_failed"
    )
    assert evidence["runtime_research_evaluation"].startswith("0/1")
    assert evidence["automated_hidden_evaluation"] == "0/1"
    assert evidence["hidden_theory_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_checks"] == "7/7"
    assert evidence["hidden_algorithm_checks"] == "10/12"
    assert evidence["hidden_empirical_checks"].startswith("10/10")
    assert "Simulation" in evidence["runtime_topology_finding"]
    assert evidence["operator_disposition"] == (
        "RUNTIME_SKIPPED_REQUIRED_EMPIRICAL_LANE_CODE_CONTRACT_FAILED"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        "5f0626727c99f0aa013ab83d004be56d12d3516b"
    )
    assert evidence["ladder_score_after_consumption"] == "4/65"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1080/01621459.1965.10480775"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_measurement_error_attenuation_l0_records_one_immutable_failed_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "classical_measurement_error_attenuation_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "classical_predictor_measurement_error"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_code_contract_failed_simulation_handoff_"
        "review_blocked"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-measurement-error-attenuation-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "240c6cbf3616848df264fab248a4c46e2b84413d13132090df8b600d23fdb4b7"
    )
    assert candidate["gold_descriptor_hash"] == (
        "b446f2e8de37f105e9229c57ed69ceac96826a5f48c210338b9f2d0bfbefb84f"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "b446f2e8de37f105e9229c57ed69ceac96826a5f48c210338b9f2d0bfbefb84f"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "025a4f769db89c890fb26452746f3d9738004d45"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 6
    assert evidence["algorithm_reference_contract_checks"] == "15/15"
    assert evidence["algorithm_reference_maximum_absolute_error"] == 0.0
    assert evidence["empirical_reference_replicates_per_dgp"] == 2000
    assert evidence["empirical_reference_dgps_passed"] == 8
    assert evidence["empirical_reference_nonpositive_denominator_rejections"] == 0
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 11
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["runtime_head"] == (
        "43b97dbf940ef2789675b7c83dbf8fce5267d03a"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_sonnet_or_opus_calls"] == 0
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_outer_iterations"] == 10
    assert evidence["runtime_failure_classification"] == (
        "architect_feedback_route_blocked"
    )
    assert evidence["runtime_research_evaluation"].startswith("0/1")
    assert evidence["automated_hidden_evaluation"] == "0/1"
    assert evidence["hidden_theory_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_checks"].startswith("8/8")
    assert evidence["hidden_algorithm_checks"].startswith("0/15")
    assert evidence["hidden_empirical_checks"].startswith("11/11")
    assert evidence["runtime_manifest_sha256"] == (
        "52befe0bb5b4fa6ead7f4b30242185dfb8ebdc5f209d0157546913a2f627d968"
    )
    assert evidence["runtime_result_sha256"] == (
        "c0aae56ff1d35e812aebce3049c90d3e9a91ccc64e9c9467c60d58b89bfa1ef5"
    )
    assert evidence["hidden_gold_evaluation_sha256"] == (
        "3a00bd04ae31d49e30b1dd21866c570a8f4478483ce8e4be156d01a92a3ed699"
    )
    assert evidence["operator_disposition"] == (
        "CODE_CONTRACT_FAILED_SIMULATION_HANDOFF_AND_REVIEW_BLOCKED"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        "464cba39753ff2959e5d0f2c08491c982745cc60"
    )
    assert evidence["ladder_score_after_consumption"] == "4/66"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1080/01621459.1978.10480011"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_measurement_error_correction"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
    ):
        assert hidden_name not in runtime_visible


def test_welch_satterthwaite_l0_consumed_draw_is_operator_invalidated() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "welch_satterthwaite_two_sample_interval_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "heteroskedastic_two_sample_mean_inference"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_operator_invalidated_theory_code_contract_"
        "failed_runtime_false_rejected_revised_confirmatory_source"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-welch-satterthwaite-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "a7075f583f3f1803555fa2ab36edb2f398ab555acc831746c906b8bdf9415224"
    )
    assert candidate["gold_descriptor_hash"] == (
        "84fb96f205ebb757402a027bd94177c474317a3d5e3c6366487b9ed3d7fc4b6e"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "84fb96f205ebb757402a027bd94177c474317a3d5e3c6366487b9ed3d7fc4b6e"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["authority_binding_commit"] == (
        "ba48a3c244a5ccf1d5849aca046983f474bda553"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 3
    assert evidence["algorithm_reference_contract_checks"] == "16/16"
    assert evidence["algorithm_reference_maximum_absolute_error"] == 0.0
    assert evidence["empirical_reference_replicates_per_dgp"] == 2000
    assert evidence["empirical_reference_dgps_passed"] == 8
    assert evidence["empirical_reference_invocation_failures"] == 0
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 2
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 2
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "c62e01b7e0a38c3ae874687c387401c6bd4e8560"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_sonnet_or_opus_calls"] == 0
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_outer_iterations"] == 12
    assert evidence["runtime_failure_classification"] == (
        "architect_feedback_route_blocked"
    )
    assert evidence["runtime_research_evaluation"] == (
        "0/1 complete; 1/1 mode-conformant"
    )
    assert evidence["automated_hidden_evaluation"] == "0/1"
    assert "operator-invalidated" in evidence["hidden_theory_checks"]
    assert evidence["hidden_algorithm_checks"].startswith("15/17")
    assert evidence["hidden_empirical_checks"].startswith("11/11")
    assert evidence["runtime_manifest_sha256"] == (
        "b4cd1df56bec18c84840806915ddd651fff5fcecf72b802c47301183203d01b9"
    )
    assert evidence["runtime_result_sha256"] == (
        "cf4dbaf5dec00b6826cfefc83ad298925d21916ef9f3406e4af4a10bba334f58"
    )
    assert evidence["hidden_gold_evaluation_sha256"] == (
        "f9a082fb11739c2227acd5496770806a1032583f2747c13037d6db8d506491e9"
    )
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_THEORY_CODE_CONTRACT_FAILED_RUNTIME_FALSE_"
        "REJECTED_REVISED_CONFIRMATORY_SOURCE"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_68_SHARED_MECHANISM_HEAD
    )
    assert "same isolated reviewer session" in evidence[
        "post_run_shared_mechanism_change"
    ]
    assert "988/988" in evidence["post_run_regression_evidence"]
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/68"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD
    assert "long-form near miss" in readiness["executable_activation_gate"]

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1093/biomet/34.1-2.28"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_welch_satterthwaite_interval"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "reference_estimator.py",
        "negative_pooled_interval.py",
        "negative_permissive.py",
    ):
        assert hidden_name not in runtime_visible


def test_neyman_scott_l0_automated_pass_is_operator_invalidated() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "neyman_scott_fixed_group_variance_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == (
        "fixed_group_incidental_parameter_variance_inconsistency"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_operator_invalidated_active_theory_and_"
        "correlated_review_false_positive"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-neyman-scott-20260827-v2"
    )
    assert candidate["gold_manifest_sha256"] == (
        "c53f443ec4764d77cd4f66cf0f705145ee9eef367fc1e9c5505f32a6ba1c2de8"
    )
    assert evidence["gold_manifest_file_sha256"] == (
        "4fae41b5a1092b425b3882e845d7958ecbee4580fe57d3a5c4550d521e6acfb8"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["activation_schema_version"] == 3
    assert evidence["semantic_calibration_attempts"] == 1
    assert evidence["semantic_calibration_cases_correct"] == 12
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_head"] == (
        "18019bb7f213042ae32e791febc45c89f5ba1326"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_sonnet_or_opus_calls"] == 0
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_outer_iterations"] == 11
    assert evidence["runtime_research_evaluation"].startswith("1/1")
    assert evidence["automated_hidden_evaluation"] == "1/1"
    assert "operator-invalidated" in evidence["hidden_theory_checks"]
    assert evidence["hidden_algorithm_checks"] == "15/15"
    assert evidence["hidden_empirical_checks"].startswith("12/12")
    assert evidence["runtime_manifest_sha256"] == (
        "f156fcd031764ff7ae507b047f4febe1f0d76e5bff6cd5f4de35cfe680e9f480"
    )
    assert evidence["runtime_result_sha256"] == (
        "3cc9983efde2a67e4b33b7babe603284a65df1492f8da48e19bbc16701693184"
    )
    assert evidence["hidden_gold_evaluation_sha256"] == (
        "0627929ab887214f3277203ae9b3c01512a2e96712b254f4c7d689c01300818f"
    )
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_ACTIVE_THEORY_AND_CORRELATED_REVIEW_FALSE_POSITIVE"
    )
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["post_run_product_mechanism_change"] == "none"
    assert "exact integrated candidate path" in evidence["post_run_design_decision"]
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/69"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS
    assert readiness["latest_shared_mechanism_head"] == LATEST_SHARED_MECHANISM_HEAD
    assert "long-form near miss" in readiness["executable_activation_gate"]

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == "10.2307/1914288"
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_neyman_scott_variance"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "reference_estimator.py",
    ):
        assert hidden_name not in runtime_visible


def test_fieller_ratio_l0_preserves_theory_component_and_full_task_failure() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "fieller_bivariate_normal_ratio_confidence_set_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "bivariate_normal_ratio_confidence_set_geometry"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_hidden_theory_pass_algorithm_uncommitted_"
        "full_task_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-fieller-ratio-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "87136c34aeb25352ff26e8f663d6873b236be81e10b96d4a286ecc09943b6340"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_schema_version"] == 4
    assert evidence["semantic_protocol_version"] == 8
    assert evidence["semantic_calibration_cases"] == 4
    assert evidence["semantic_calibration_cases_correct"] == 4
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["runtime_enabled_model_tiers"] == {"haiku": 7}
    assert evidence["runtime_sonnet_or_opus_calls"] == 0
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_outer_iterations"] == 10
    assert evidence["runtime_research_evaluation"].startswith("0/1")
    assert evidence["automated_hidden_evaluation"] == "0/1"
    assert evidence["hidden_theory_checks"].startswith("7/7")
    assert "8/8" in evidence["hidden_theory_checks"]
    assert "never explicitly committed" in evidence["algorithm_finding"]
    assert "did not run" in evidence["empirical_finding"]
    assert evidence["post_run_shared_mechanism_commit"] == "ecfc2403"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/70"

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1111/j.2517-6161.1954.tb00159.x"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_fieller_ratio_set"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "reference_estimator.py",
    ):
        assert hidden_name not in runtime_visible


def test_randomized_distributional_transform_l0_consumption_is_immutable() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "randomized_distributional_transform_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == (
        "probability_integral_transform_mixed_distributions"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_operator_invalidated_theory_scope_and_"
        "simulation_review_false_accept"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-randomized-distributional-transform-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "f01d4847394414ebea3a22bb2a62e489cea479eb6a7eae5ca486b59e0dcec2c9"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "4fe00920906ffaa8a360cf43a0bd5e09ddaef5a000b6514ed7d52af761efc4bb"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_schema_version"] == 4
    assert evidence["semantic_protocol_version"] == 9
    assert evidence["semantic_activation_record_sha256"] == (
        "e3887c7039929b681041c572867686c2347d4a4ff896d6e5140451cf7daa9c91"
    )
    assert evidence["semantic_calibration_attempts"] == 3
    assert evidence["semantic_calibration_total_model_calls"] == 18
    assert evidence["semantic_calibration_cases"] == 4
    assert evidence["semantic_calibration_cases_correct"] == 4
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 3
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["qualified_semantic_model_calls_before_activation"] == 6
    assert evidence["activation_ledger_commit"] == (
        "b8b79fc2cc416ec3c6e1308c945fb2d80860675c"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["product_code_head"] == (
        "6e9295de6bf84795fa13fe15362a7c4f085d8887"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_eval_complete"] == "1/1"
    assert evidence["hidden_full_task_result"] == "0/1"
    assert evidence["runtime_outer_graph_iterations"] == 11
    assert evidence["runtime_same_owner_workspace_continuations"] == 2
    assert evidence["runtime_tool_calls"] == 17
    assert evidence["enabled_llm_roles"] == 7
    assert evidence["enabled_model"] == "claude-haiku-4-5-20251001"
    assert evidence["enabled_sonnet_calls"] == 0
    assert evidence["enabled_opus_calls"] == 0
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_algorithm_checks"] == "8/8"
    assert evidence["hidden_empirical_checks"] == "7/7"
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_THEORY_SCOPE_CONTRACTION_AND_SIMULATION_REVIEW_FALSE_ACCEPT"
    )
    assert Path(evidence["operator_audit_path"]).exists()
    assert evidence["post_run_shared_mechanism_commit"] == "02ce1ae3"
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/71"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1016/j.spl.2007.02.008"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_randomized_distributional_transform"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "reference_estimator.py",
        "negative_ordinary_pit.py",
        "negative_permissive.py",
    ):
        assert hidden_name not in runtime_visible


def test_fisher_exact_greater_l0_records_one_consumed_operator_invalid_draw() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "fisher_exact_greater_fixed_margins_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == (
        "conditional_exact_contingency_table_inference"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_code_review_"
        "operator_invalidated_theory_code_and_empirical_protocol"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-fisher-exact-greater-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "e1d06b0875682119159f7833787566b1e37bdc03dc05f0fe9110346b71627b12"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "893300d314f343a21bfd8fb5bfe799e5c0ec5477540806f90edbc3076bd7ef1a"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_schema_version"] == 4
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_record_sha256"] == (
        "1266acd5546c8ba9db4d709b6716ccaf29e2f302d811a4c6d9fd8bfd985fb77d"
    )
    assert evidence["semantic_calibration_attempts"] == 3
    assert evidence["semantic_calibration_total_model_calls"] == 12
    assert evidence["semantic_calibration_cases"] == 4
    assert evidence["semantic_calibration_cases_correct"] == 4
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
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
    assert evidence["qualified_semantic_model_calls_before_activation"] == 6
    assert evidence["activation_ledger_commit"] == (
        "f33d6bc333afac8292abc0dfca19767d4c49d59a"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["product_code_head"] == (
        "6eb66dc973bc0a6fa2f67ac26d64df5cc993a8ec"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "generated_code_semantic_review_packet_invalid"
    )
    assert evidence["runtime_research_eval_complete"] == "0/1"
    assert evidence["hidden_full_task_result"] == "0/1"
    assert evidence["runtime_outer_graph_iterations"] == 5
    assert evidence["runtime_same_owner_workspace_continuations"] == 0
    assert evidence["runtime_tool_calls"] == 3
    assert evidence["workspace_model_turns"] == {
        "TheoryDeveloper": 11,
        "independent_theory_referee": 7,
        "AlgorithmEngineer": 10,
        "GeneratedCodeSemanticReviewer": 6,
    }
    assert evidence["enabled_llm_roles"] == 7
    assert evidence["enabled_model"] == "claude-haiku-4-5-20251001"
    assert evidence["enabled_sonnet_calls"] == 0
    assert evidence["enabled_opus_calls"] == 0
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_candidate_status"] == "INCONCLUSIVE"
    assert evidence["hidden_theory_semantic_document_status"] == "PASS"
    assert evidence["hidden_theory_semantic_claims"] == (
        "7 SATISFIED, 1 INCONCLUSIVE"
    )
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_PUBLIC_DOMAIN_CLOSED_ABI_AND_EMPIRICAL_PROTOCOL"
    )
    assert evidence["operator_audit_path"] == (
        "docs/operator_audits/fisher_exact_greater_l0_v1.md"
    )
    assert Path(evidence["operator_audit_path"]).is_file()
    assert evidence["runtime_manifest_sha256"] == (
        "78c31e44adc88ebb3b1d6bbd84b59042b45cdd91a69979eb79e91ed64a31b662"
    )
    assert evidence["runtime_result_sha256"] == (
        "970298a28387be9291cb9e1d5b2e71307331d2885388cf37eb5d83118baaf9a7"
    )
    assert evidence["hidden_gold_evaluation_sha256"] == (
        "b7c64ffc3d3c97d0d59740a0b1c623852ad79d3ff97131ec9d637765d5cf8aec"
    )
    assert evidence["accepted_theory_packet_hash"] == (
        "1da324fd5a0e9b4fd0fe65f40668c4cee88d38ba2049a9902beef82e9569b1cf"
    )
    assert evidence["accepted_theory_document_set_hash"] == (
        "afbf5bffa4879c078cfc9b089c2575b03db090e955054752733610395adb645e"
    )
    assert evidence["committed_estimator_source_hash"] == (
        "2e230efa71e8a4bd21d5ad27da1d3f2bf7fe1d64ebba4f28bbafedefab91edf2"
    )
    assert evidence["post_run_shared_mechanism_commit"] == ""
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/72"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1111/j.2397-2335.1922.tb00768.x"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_fisher_exact_greater"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "reference_estimator.py",
        "negative_lower_tail.py",
        "negative_unconditional_binomial.py",
        "negative_permissive.py",
    ):
        assert hidden_name not in runtime_visible


def test_exponential_maximum_gumbel_l0_is_consumed_and_immutable() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "exponential_maximum_gumbel_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "extreme_value_exponential_maxima"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_critic_lifecycle_"
        "hidden_theory_inconclusive_operator_invalidated_contextual_theory"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-exponential-maximum-gumbel-20260827-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "a4d4d6ffe165c6a47e385058a88b3ea206323675857ce68fcbb9d20c63fc0a00"
    )
    assert evidence["gold_manifest_stable_hash"] == (
        "1c27f187a1c61345dbeb07529fe7160c17831253bc8172fbf11bf5c1e24fd91a"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_schema_version"] == 4
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_activation_record_sha256"] == (
        "c9bd209a6edc9d08cd8e784a4d9d656358b4a50257c4715d01ca1d2209a03f4c"
    )
    assert evidence["semantic_calibration_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 12
    assert evidence["semantic_calibration_cases"] == 4
    assert evidence["semantic_calibration_cases_correct"] == 4
    assert evidence["semantic_candidate_mode_negative_cases"] == 1
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
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
    assert evidence["qualified_semantic_model_calls_before_activation"] == 6
    assert evidence["activation_ledger_commit"] == (
        "63d1d53e586a815848ef16725d49554551253af6"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 12
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["product_code_head"] == (
        "49f6c45b567d7a3ff89b67a6eebb101ef6eb7736"
    )
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "critic_packet_validation_failed"
    )
    assert evidence["runtime_research_eval_complete"] == "0/1"
    assert evidence["hidden_full_task_result"] == "0/1"
    assert evidence["runtime_outer_graph_iterations"] == 15
    assert evidence["critic_workspace_model_turns"] == 25
    assert evidence["enabled_llm_roles"] == 7
    assert evidence["enabled_model"] == "claude-haiku-4-5-20251001"
    assert evidence["enabled_sonnet_calls"] == 0
    assert evidence["enabled_opus_calls"] == 0
    assert evidence["accepted_algorithm_handoff_hash"] == (
        "96707883ada6d428b7e62d9257a32d163fbeb39e21a8afd008ecd585b5e18475"
    )
    assert evidence["committed_estimator_source_hash"] == (
        "4fd67c64a4efc58e15626570460b00918097bf70e61c21f5d86f1f1455c16062"
    )
    assert evidence["accepted_theory_packet_hash"] == (
        "a99cec23c2c812ce5bde15187202ec5b73dc89a0282cc8f1d87e08d3092df7f6"
    )
    assert evidence["accepted_theory_document_set_hash"] == (
        "44c0b81c87531c6874424efd2762e7fa210b2a09c7b58f2a37a9c2bb3a940327"
    )
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_candidate_status"] == (
        "INCONCLUSIVE"
    )
    assert evidence["hidden_theory_semantic_claims"] == (
        "6 SATISFIED, 2 INCONCLUSIVE"
    )
    assert evidence["hidden_algorithm_checks"] == "8/8"
    assert evidence["hidden_algorithm_estimator_invocations"] == 27
    assert evidence["hidden_empirical_checks"] == "10/10"
    assert evidence["hidden_empirical_estimator_invocations"] == 16000
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_CONTEXTUAL_THEORY_AND_RUNTIME_REFEREE_"
        "FALSE_ACCEPTANCE"
    )
    assert evidence["post_run_shared_mechanism_commit"] == (
        "bfae4e135c54b70cadbe6a6fb04234c55b7a8cec"
    )
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/73"

    run_path = Path(evidence["immutable_run_path"])
    assert run_path.is_dir()
    for filename, field in (
        ("research_agent_runtime_manifest.json", "runtime_manifest_sha256"),
        (
            "exponential_maximum_gumbel_known_result_runtime_result.json",
            "runtime_result_sha256",
        ),
        (
            "research_capability_gold_evaluation.json",
            "hidden_gold_evaluation_sha256",
        ),
        ("runtime_completion_summary.json", "runtime_completion_summary_sha256"),
        ("runtime_failure_summary.json", "runtime_failure_summary_sha256"),
        ("runtime_llm_topology.json", "runtime_llm_topology_sha256"),
    ):
        assert hashlib.sha256((run_path / filename).read_bytes()).hexdigest() == (
            evidence[field]
        )

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["source"]["primary_paper"]["doi"] == (
        "10.1017/S0305004100015681"
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_exponential_maximum_gumbel"
    )
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "reference_estimator.py",
        "negative_wrong_center.py",
        "negative_minimum.py",
        "negative_permissive.py",
    ):
        assert hidden_name not in runtime_visible


def test_sandwich_jss_r_l1_is_consumed_and_operator_invalidated() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "sandwich_jss_2004_r_public_replication"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L1"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_and_hidden_automated_pass_"
        "operator_invalidated_report_semantics"
    )
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["product_code_head"] == (
        "9feec25d9f4c819ba4bbd991bd1c8469b9d7f4c8"
    )
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_eval_complete"] == "1/1"
    assert evidence["automated_hidden_full_task_result"] == "1/1"
    assert evidence["product_model_calls"] == 18
    assert evidence["architect_model_calls"] == 2
    assert evidence["architect_full_packet_regenerations"] == 1
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_74_SHARED_MECHANISM_HEAD
    )
    assert evidence["post_run_shared_mechanism_change"].startswith(
        "Future tasks only:"
    )
    assert evidence["hidden_source_execution_checks"] == "12/12"
    assert evidence["hidden_source_semantic_claims"] == "10/10 SATISFIED"
    assert evidence["enabled_model"] == "claude-haiku-4-5-20251001"
    assert evidence["enabled_sonnet_calls"] == 0
    assert evidence["enabled_opus_calls"] == 0
    assert evidence["operator_disposition"] == (
        "OPERATOR_INVALIDATED_REPORT_SEMANTICS_AND_DUAL_REVIEWER_"
        "FALSE_ACCEPTANCE"
    )
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/74"
    assert evidence["formalizer_executed"] is False

    run_path = Path(evidence["immutable_run_path"])
    assert run_path.is_dir()
    for filename, field in (
        ("research_agent_runtime_manifest.json", "runtime_manifest_sha256"),
        (
            "sandwich_jss_2004_r_public_replication_runtime_result.json",
            "runtime_result_sha256",
        ),
        (
            "research_capability_gold_evaluation.json",
            "hidden_gold_evaluation_sha256",
        ),
        ("runtime_completion_summary.json", "runtime_completion_summary_sha256"),
        ("runtime_failure_summary.json", "runtime_failure_summary_sha256"),
        ("runtime_llm_topology.json", "runtime_llm_topology_sha256"),
    ):
        assert hashlib.sha256((run_path / filename).read_bytes()).hexdigest() == (
            evidence[field]
        )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["source"]["doi"] == "10.18637/jss.v011.i10"
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["operator_invalid_tasks"] == CURRENT_OPERATOR_INVALID_TASKS


def test_lehmann_scheffe_l0_is_consumed_once_and_immutable() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "lehmann_scheffe_complete_sufficient_umvu_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "complete_sufficient_umvu_estimation"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_no_hidden_theory_execution"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-lehmann-scheffe-umvu-20260828-v1"
    )
    assert evidence["activation_schema_version"] == 4
    assert evidence["semantic_protocol_version"] == 10
    assert evidence["semantic_calibration_attempts"] == 4
    assert evidence["semantic_calibration_total_model_calls"] == 53
    assert evidence["semantic_final_calibration_cases_correct"] == 4
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["product_loader_preactivation_rejections"] == 1
    assert evidence["mechanical_authority_checks"] == 7
    assert evidence["mechanical_negative_variants_rejected"] == 7
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["activation_ledger_commit"] == (
        "3bd92ff71d4ce8b4900cc75e4701f19df27fbde1"
    )
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["product_code_head"] == (
        "75620bf8ff5f0007e8287ac4d68f8c841f9f5c8f"
    )
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["product_model_calls"] == 67
    assert evidence["initial_architect_planning_model_calls"] == 1
    assert evidence["client_tool_model_turns"] == 66
    assert evidence["theory_developer_model_turns"] == 32
    assert evidence["independent_referee_model_turns"] == 34
    assert evidence["runtime_outer_graph_iterations"] == 6
    assert evidence["runtime_trace_labeled_architect_coordinator_rows"] == 3
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "theory_developer_packet_validation_failed"
    )
    assert evidence["research_eval_complete"] is False
    assert evidence["research_eval_mode_conformant"] is True
    assert evidence["hidden_evaluator_runs"] == 1
    assert evidence["hidden_tasks_evaluated"] == 0
    assert evidence["hidden_theory_execution_attempted"] is False
    assert evidence["theory_document_lines"] == 235
    assert evidence["theory_document_bytes"] == 17403
    assert evidence["independent_referee_cycles"] == 2
    assert evidence["future_shared_mechanism_commit"] == (
        TASK_75_SHARED_MECHANISM_HEAD
    )
    assert "998/998" in evidence["evidence_closeout_verification"]
    assert "No model or hidden-evaluator call" in (
        evidence["evidence_closeout_verification"]
    )
    assert evidence["formalizer_executed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "4/75"
    assert evidence["post_run_score_changed"] is False

    run_path = Path(evidence["immutable_run_path"])
    assert run_path.is_dir()
    for filename, field in (
        ("research_agent_runtime_manifest.json", "runtime_manifest_sha256"),
        (
            "lehmann_scheffe_complete_sufficient_umvu_known_result_runtime_result.json",
            "runtime_result_sha256",
        ),
        (
            "research_capability_gold_evaluation.json",
            "hidden_gold_evaluation_sha256",
        ),
        ("runtime_completion_summary.json", "runtime_completion_summary_sha256"),
        ("runtime_failure_summary.json", "runtime_failure_summary_sha256"),
        ("runtime_observations.jsonl", "runtime_observations_sha256"),
        ("runtime_task_handoffs.jsonl", "runtime_task_handoffs_sha256"),
        ("runtime_progress.jsonl", "runtime_progress_sha256"),
        ("runtime_llm_topology.json", "runtime_llm_topology_sha256"),
        ("runtime_tool_calls.jsonl", "runtime_tool_calls_sha256"),
    ):
        assert hashlib.sha256((run_path / filename).read_bytes()).hexdigest() == (
            evidence[field]
        )

    theory_path = run_path / evidence["theory_document_path"]
    assert hashlib.sha256(theory_path.read_bytes()).hexdigest() == (
        evidence["theory_document_sha256"]
    )
    assert len(theory_path.read_text(encoding="utf-8").splitlines()) == 235
    assert Path(evidence["operator_audit_path"]).is_file()

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["source"]["jstor_stable"] == "25048038"
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "hidden_theory_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7


def test_debiased_lasso_l2_only_product_draw_is_consumed_and_immutable() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "debiased_lasso_known_precision_paper_to_code"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L2"
    assert candidate["family"] == (
        "high_dimensional_debiased_regression_inference"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_hidden_algorithm_and_theory_"
        "failed_empirical_passed_operator_invalidated"
    )
    assert evidence["activation_ledger_commit"] == (
        TASK_77_ACTIVATION_LEDGER_HEAD
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["qualified_semantic_model_calls_before_activation"] == 7
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_consumption"] == "4/76"
    assert evidence["ladder_score_after_consumption"] == "4/77"
    assert evidence["post_run_score_changed"] is False
    assert evidence["runtime_manifest_sha256"] == (
        "23a85c3fab4832dbf6a668b855fc65382554d2681a6428d31d8b39cd224c3cb2"
    )
    assert evidence["hidden_gold_evaluation_sha256"] == (
        "bed81b1f7d18b13dde50f7065386c24697693bc9d6c16c494ee0c8fc73b455a7"
    )
    assert evidence["evaluated_estimator_source_hash"] == (
        "8680b1cf4015d8d3cc35c98903c07f7c6d878b135604934dc410a7e1099bb971"
    )
    boundary = evidence["boundary"]
    for forbidden_action in (
        "rerun",
        "resume",
        "repair",
        "hidden-evaluate again",
        "rescore",
        "resample",
    ):
        assert forbidden_action in boundary

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_debiased_lasso_coordinate"
    )


def test_horvitz_thompson_l0_draw_is_consumed_and_immutable() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "horvitz_thompson_poisson_total_r_known_result"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L0"
    assert candidate["family"] == "finite_population_independent_poisson_sampling"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_hidden_full_task_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l0-horvitz-thompson-poisson-r-20260828-v1"
    )
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["activation_ledger_commit"] == (
        "09eb4bf4244f2f548914442cbf6781ef9766f5b8"
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_final_calibration_cases_correct"] == 6
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
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
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "critic_scientific_inconclusive"
    )
    assert evidence["runtime_research_loop_complete"] == "0/1"
    assert evidence["runtime_mode_conformant"] == "1/1"
    assert evidence["runtime_traces"] == 26
    assert evidence["runtime_outer_graph_iterations"] == 9
    assert evidence["runtime_same_owner_workspace_continuations"] == 17
    assert evidence["runtime_tool_calls"] == 71
    assert evidence["runtime_observations"] == 88
    assert evidence["runtime_task_handoffs"] == 25
    assert "claude-haiku-4-5-20251001" in evidence["runtime_model_policy"]
    assert "zero Sonnet and Opus calls" in evidence["runtime_model_policy"]
    assert evidence["runtime_manifest_sha256"] == (
        "bf532c487a37518896ee255be71a18fa3d718afe34d45e2bbbb9587602302be7"
    )
    assert evidence["runtime_result_sha256"] == (
        "75147633d5ce37cbafa242856c17050cf76174cde8ab2bed236ce464283caf54"
    )
    assert evidence["hidden_gold_evaluation_sha256"] == (
        "21c495275ea40e339ef56a5a2f168515f1c3cb58963bbb9a24e13ef4ba6a3455"
    )
    assert evidence["hidden_theory_result_hash"] == (
        "2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6"
    )
    assert evidence["hidden_theory_semantic_result_hash"] == (
        "eeba4fc3234bf973c81da08ec5a0ea4d814ffaa4c5c5191cda5dff2c4e4d644b"
    )
    assert evidence["hidden_algorithm_result_hash"] == (
        "223a94bb9b66e27197f42615b15616730539e8bb07ef1b2fa7561fb6b6c00edf"
    )
    assert evidence["hidden_empirical_result_hash"] == (
        "fe40d323e8b41acbf8076b7f16c4493650a713b36af4fff761dfde0fd521833a"
    )
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_78_SHARED_MECHANISM_HEAD
    )
    assert "1006/1006" in evidence["post_run_regression_evidence"]
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_consumption"] == "4/77"
    assert evidence["ladder_score_after_consumption"] == "4/78"
    assert "consumed and immutable" in evidence["boundary"]

    operator_audit = Path(evidence["operator_audit"])
    assert operator_audit.exists()
    assert hashlib.sha256(operator_audit.read_bytes()).hexdigest() == (
        evidence["operator_audit_sha256"]
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["research_source_snapshot_hash"] == (
        evidence["source_snapshot_hash"]
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_horvitz_thompson_poisson_total"
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.R",
        "hidden_algorithm_harness.R",
        "hidden_empirical_harness.R",
        "semantic_reference.md",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )


def test_distance_correlation_l2_only_product_draw_is_consumed_and_immutable() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "distance_correlation_chisquare_paper_to_code"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L2"
    assert candidate["family"] == (
        "nonlinear_independence_testing_distance_correlation"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_accepted_hidden_scientific_code_"
        "failed_theory_and_empirical_passed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l2-distance-correlation-chisquare-20260828-v1"
    )
    assert evidence["activation_ledger_commit"] == (
        TASK_79_ACTIVATION_LEDGER_HEAD
    )
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_final_calibration_cases_correct"] == 5
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 7
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["reference_algorithm_contract_checks_passed"] is True
    assert evidence["reference_algorithm_estimator_invocations"] == 18
    assert evidence["reference_algorithm_maximum_relative_error"] == 0.0
    assert evidence["reference_empirical_designs_passed"] == 4
    assert evidence["reference_empirical_replicates_per_design"] == 2000
    assert evidence["reference_empirical_estimator_invocations"] == 8000
    assert evidence["reference_empirical_invocation_failures"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_research_loop_complete"] == "1/1"
    assert evidence["runtime_mode_conformant"] == "1/1"
    assert evidence["hidden_full_task_result"] == "0/1"
    assert evidence["runtime_traces"] == 11
    assert evidence["runtime_outer_graph_iterations"] == 11
    assert evidence["runtime_same_owner_workspace_continuations"] == 0
    assert evidence["runtime_tool_calls"] == 8
    assert evidence["runtime_observations"] == 26
    assert evidence["runtime_task_handoffs"] == 10
    assert evidence["enabled_model"] == "claude-haiku-4-5-20251001"
    assert evidence["enabled_sonnet_calls"] == 0
    assert evidence["enabled_opus_calls"] == 0
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_candidate_status"] == "PASS"
    assert evidence["hidden_theory_semantic_claims"] == "8/8 SATISFIED"
    assert evidence["hidden_algorithm_checks"] == "6/8"
    assert evidence["hidden_algorithm_estimator_invocations"] == 18
    assert evidence["hidden_empirical_checks"] == "9/9"
    assert evidence["hidden_empirical_estimator_invocations"] == 8000
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_79_SHARED_MECHANISM_HEAD
    )
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_consumption"] == "4/78"
    assert evidence["ladder_score_after_consumption"] == "4/79"
    assert evidence["post_run_score_changed"] is False
    assert "consumed and immutable" in evidence["boundary"]

    run_path = Path(evidence["immutable_run_path"])
    run_hashes = {
        "research_agent_runtime_manifest.json": evidence[
            "runtime_manifest_sha256"
        ],
        "distance_correlation_chisquare_paper_to_code_runtime_result.json": evidence[
            "runtime_result_sha256"
        ],
        "research_capability_gold_evaluation.json": evidence[
            "hidden_gold_evaluation_sha256"
        ],
        "runtime_llm_topology.json": evidence["runtime_llm_topology_sha256"],
        "runtime_evidence_ledger.jsonl": evidence[
            "runtime_evidence_ledger_sha256"
        ],
        "runtime_failure_summary.json": evidence[
            "runtime_failure_summary_sha256"
        ],
        "runtime_completion_summary.json": evidence[
            "runtime_completion_summary_sha256"
        ],
        "runtime_progress.jsonl": evidence["runtime_progress_sha256"],
        "runtime_tool_calls.jsonl": evidence["runtime_tool_calls_sha256"],
        "runtime_traces.jsonl": evidence["runtime_traces_sha256"],
        "runtime_task_handoffs.jsonl": evidence[
            "runtime_task_handoffs_sha256"
        ],
        "runtime_observations.jsonl": evidence["runtime_observations_sha256"],
    }
    for filename, expected_sha256 in run_hashes.items():
        assert hashlib.sha256((run_path / filename).read_bytes()).hexdigest() == (
            expected_sha256
        )

    operator_audit = Path(evidence["operator_audit_path"])
    assert operator_audit.is_file()
    assert hashlib.sha256(operator_audit.read_bytes()).hexdigest() == (
        evidence["operator_audit_sha256"]
    )

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["research_source_snapshot_hash"] == (
        evidence["source_snapshot_hash"]
    )
    assert question["estimator_execution_contract"]["estimator_id"] == (
        "est_distance_correlation_chisquare"
    )

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )


def test_pelt_gaussian_mean_l2_only_product_draw_is_consumed_and_immutable() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "pelt_gaussian_mean_paper_to_code"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L2"
    assert candidate["family"] == "offline_gaussian_mean_changepoint_pelt"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_runtime_blocked_hidden_scientific_code_and_"
        "unresolved_gaps_failed_theory_and_empirical_passed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l2-pelt-gaussian-mean-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "ed9bb2eb64c574fb825664c5269443715b129ac3f8d3c31705d7e09bc63d26d0"
    )
    assert candidate["gold_descriptor_hash"] == (
        "894521ac6352ed819aeeeaf8664e555493b00d743ca5db9ecbd6fcae700b8ba9"
    )
    assert evidence["activation_ledger_commit"] == TASK_80_ACTIVATION_LEDGER_HEAD
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_activation_attempts"] == 2
    assert evidence["semantic_calibration_total_model_calls"] == 14
    assert evidence["semantic_final_calibration_model_calls"] == 7
    assert evidence["semantic_final_calibration_cases_correct"] == 5
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 7
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["reference_algorithm_contract_checks_passed"] is True
    assert evidence["reference_algorithm_valid_cases"] == 24
    assert evidence["reference_algorithm_invalid_cases"] == 21
    assert evidence["reference_algorithm_random_bruteforce_cross_checks"] == 3000
    assert evidence["reference_algorithm_regular_ruptures_cross_checks"] == 200
    assert evidence["reference_algorithm_minimum_length_counterexample_detected"] is True
    assert evidence["reference_empirical_designs_passed"] == 3
    assert evidence["reference_empirical_replicates_per_design"] == 1000
    assert evidence["reference_empirical_estimator_invocations"] == 3000
    assert evidence["reference_empirical_invocation_failures"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is True
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_failure_classification"] == (
        "critic_packet_validation_failed"
    )
    assert evidence["runtime_research_loop_complete"] == "0/1"
    assert evidence["runtime_mode_conformant"] == "1/1"
    assert evidence["hidden_theory_mechanical_checks"] == "7/7"
    assert evidence["hidden_theory_semantic_claims"] == "8/8 SATISFIED"
    assert evidence["hidden_algorithm_checks"] == "7/11"
    assert evidence["hidden_algorithm_estimator_invocations"] == 46
    assert evidence["hidden_empirical_checks"] == "9/9"
    assert evidence["hidden_empirical_estimator_invocations"] == 3000
    assert evidence["enabled_model"] == "claude-haiku-4-5-20251001"
    assert evidence["enabled_sonnet_calls"] == 0
    assert evidence["enabled_opus_calls"] == 0
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_consumption"] == "4/79"
    assert evidence["ladder_score_after_consumption"] == "4/80"
    assert evidence["post_run_score_changed"] is False
    assert evidence["future_shared_mechanism_pending"] is False
    assert evidence["post_run_shared_mechanism_commit"] == (
        TASK_80_SHARED_MECHANISM_HEAD
    )
    assert "1013/1013" in evidence["post_run_shared_mechanism_evidence"]
    assert "future tasks only" in evidence["post_run_shared_mechanism_change"].lower()
    assert "consumed and immutable" in evidence["boundary"]

    run_path = Path(evidence["immutable_run_path"])
    assert run_path.is_dir()
    for filename, field in (
        ("research_agent_runtime_manifest.json", "runtime_manifest_sha256"),
        (
            "pelt_gaussian_mean_paper_to_code_runtime_result.json",
            "runtime_result_sha256",
        ),
        (
            "research_capability_gold_evaluation.json",
            "hidden_gold_evaluation_sha256",
        ),
        ("runtime_completion_summary.json", "runtime_completion_summary_sha256"),
        ("runtime_failure_summary.json", "runtime_failure_summary_sha256"),
        ("runtime_llm_topology.json", "runtime_llm_topology_sha256"),
        ("runtime_evidence_ledger.jsonl", "runtime_evidence_ledger_sha256"),
        ("runtime_progress.jsonl", "runtime_progress_sha256"),
        ("runtime_tool_calls.jsonl", "runtime_tool_calls_sha256"),
        ("runtime_traces.jsonl", "runtime_traces_sha256"),
        ("runtime_task_handoffs.jsonl", "runtime_task_handoffs_sha256"),
        ("runtime_observations.jsonl", "runtime_observations_sha256"),
    ):
        assert hashlib.sha256((run_path / filename).read_bytes()).hexdigest() == (
            evidence[field]
        )
    assert Path(evidence["operator_audit_path"]).is_file()

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["research_source_snapshot_hash"] == (
        evidence["source_snapshot_hash"]
    )
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_pelt_gaussian_mean"
    assert [row["name"] for row in contract["request_fields"]] == [
        "signal",
        "penalty",
        "min_segment_length",
    ]
    assert [row["name"] for row in contract["response_fields"]] == [
        "changepoints",
        "objective",
    ]
    exactness = next(
        row["meaning"]
        for row in contract["invariants"]
        if row["clause_id"] == "invariant.exact_pelt_optimality"
    )
    assert "until the witness can begin a feasible following segment" in exactness

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "reference_estimator.py",
        "negative_immediate_pruning.py",
        "hidden_algorithm_harness.py",
        "hidden_empirical_harness.py",
        "semantic_reference.md",
        "semantic_rubric.json",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )


def test_linear_kernel_two_sample_l3_is_blind_frozen_and_consumed_once() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "linear_kernel_two_sample_known_theory_rederivation"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L3"
    assert candidate["family"] == "nonparametric_kernel_two_sample_linear_statistic"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_blocked_hidden_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l3-linear-kernel-two-sample-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "818eeb26868932df51cd6cef58a2dba192fe42546fd4a7f1d8d288c1978f6def"
    )
    assert candidate["gold_descriptor_hash"] == (
        "e417748e2074bb04c23d41cef294b540eddd354c5ec97e2300722078c2455293"
    )
    assert evidence["activation_ledger_commit"] == TASK_81_ACTIVATION_LEDGER_HEAD
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 7
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["target_publication_identity_withheld_from_runtime"] is True
    assert evidence["public_source_discovery_disabled_for_blind_draw"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_activation_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 7
    assert evidence["semantic_final_calibration_cases_correct"] == 5
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 9
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 7
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["reference_algorithm_contract_checks_passed"] is True
    assert evidence["reference_algorithm_valid_cases"] == 24
    assert evidence["reference_algorithm_invalid_cases"] == 28
    assert evidence["reference_empirical_designs_passed"] == 3
    assert evidence["reference_empirical_replicates_per_design"] == 2000
    assert evidence["reference_empirical_estimator_invocations"] == 6000
    assert evidence["reference_empirical_invocation_failures"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is True
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_consumption"] == "4/80"
    assert evidence["ladder_score_after_consumption"] == "4/81"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_research_loop_complete"] is False
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["hidden_theory_combined_passed"] is True
    assert evidence["hidden_algorithm_checks_passed"] == 8
    assert evidence["hidden_algorithm_checks_total"] == 14
    assert evidence["hidden_empirical_checks_passed"] == 10
    assert evidence["hidden_empirical_checks_total"] == 10
    assert evidence["hidden_empirical_authority_passed_runtime_not_accepted"] is True
    assert "sole product draw" in evidence["boundary"]
    assert "Never rerun" in evidence["boundary"]

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["target_publication_identity"] == (
        "evaluator_only_hidden"
    )
    assert question["source"]["public_source_discovery"] == (
        "disabled_for_this_blind_draw"
    )
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_paired_kernel_discrepancy"
    assert [row["name"] for row in contract["request_fields"]] == [
        "x",
        "y",
        "bandwidth",
        "alpha",
    ]
    assert [row["name"] for row in contract["response_fields"]] == [
        "statistic",
        "contrast_variance",
        "standard_error",
        "p_value",
        "reject",
    ]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "primary_paper.pdf",
        "official_code.zip",
        "reference_estimator.py",
        "semantic_reference.md",
        "semantic_rubric.json",
    ):
        assert hidden_name not in runtime_visible
    assert "target_publication_title" not in runtime_visible
    assert "target_publication_authors" not in runtime_visible
    assert "target_publication_venue" not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )


def test_crossfit_orthogonal_contrast_l3_is_blind_frozen_and_consumed_once() -> None:
    ladder = _load_ladder()
    candidate = next(
        row
        for row in ladder["initial_candidate_queue"]
        if row["id"] == "crossfit_orthogonal_contrast_r_known_theory_rederivation"
    )
    evidence = candidate["activation_evidence"]

    assert candidate["level"] == "L3"
    assert candidate["family"] == (
        "causal_binary_treatment_crossfit_orthogonal_contrast"
    )
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_blocked_hidden_failed"
    )
    assert candidate["gold_bundle_id"] == (
        "research-l3-crossfit-orthogonal-contrast-r-20260828-v1"
    )
    assert candidate["gold_manifest_sha256"] == (
        "04837881ed6f7d7e63104fac5bf7649efc2064da82eec7626fe68cac520cde4f"
    )
    assert candidate["gold_descriptor_hash"] == (
        "9e19fc76fd7d03f4c19e37a2163c87786373c35da31fc088383ed8fd81dbf79d"
    )
    assert evidence["activation_ledger_commit"] == TASK_82_ACTIVATION_LEDGER_HEAD
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 7
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["target_publication_identity_withheld_from_runtime"] is True
    assert evidence["public_source_discovery_disabled_for_blind_draw"] is True
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert evidence["semantic_activation_attempts"] == 1
    assert evidence["semantic_calibration_total_model_calls"] == 7
    assert evidence["semantic_final_calibration_cases_correct"] == 5
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == 1
    assert evidence["semantic_reference_claims"] == 10
    assert evidence["semantic_reference_candidate_passed"] is True
    assert evidence["activation_reference_tasks_passed"] == 1
    assert evidence["activation_negative_controls_rejected"] == 4
    assert evidence["activation_semantic_reference_documents_passed"] == 1
    assert (
        evidence[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert evidence["activation_semantic_model_calls"] == 0
    assert evidence["activation_semantic_qualification_model_calls"] == 7
    assert evidence["activation_semantic_qualification_reused"] is True
    assert evidence["reference_algorithm_contract_checks_passed"] is True
    assert evidence["reference_algorithm_valid_cases"] == 20
    assert evidence["reference_algorithm_invalid_cases"] == 43
    assert evidence["reference_algorithm_maximum_length_case_passed"] is True
    assert evidence["reference_empirical_designs_passed"] == 4
    assert evidence["reference_empirical_replicates_per_design"] == 2000
    assert evidence["reference_empirical_estimator_invocations"] == 8000
    assert evidence["reference_empirical_invocation_failures"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["generated_algorithm_executed"] is True
    assert evidence["generated_simulation_executed"] is False
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_consumption"] == "4/81"
    assert evidence["ladder_score_after_consumption"] == "4/82"
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "generated_code_semantic_review_packet_invalid"
    )
    assert evidence["runtime_research_loop_complete"] is False
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_traces"] == 5
    assert evidence["runtime_outer_graph_iterations"] == 5
    assert evidence["runtime_model_calls"] == 38
    assert evidence["hidden_theory_mechanical_checks_passed"] == 7
    assert evidence["hidden_theory_mechanical_checks_total"] == 7
    assert evidence["hidden_theory_semantic_claims_satisfied"] == 9
    assert evidence["hidden_theory_semantic_claims_total"] == 10
    assert evidence["hidden_theory_semantic_candidate_status"] == "INCONCLUSIVE"
    assert evidence["hidden_theory_combined_passed"] is False
    assert evidence["hidden_algorithm_execution_attempted"] is False
    assert evidence["hidden_empirical_execution_attempted"] is False
    assert evidence["independently_accepted_algorithm_handoff_observed"] is False
    assert evidence["future_shared_mechanism_pending"] is False
    assert "sole product draw" in evidence["boundary"]
    assert "Never rerun" in evidence["boundary"]

    run_path = Path(evidence["run_path"])
    run_hashes = {
        "research_agent_runtime_manifest.json": evidence[
            "runtime_manifest_sha256"
        ],
        "crossfit_orthogonal_contrast_r_known_theory_rederivation_runtime_result.json": evidence[
            "runtime_result_sha256"
        ],
        "research_capability_gold_evaluation.json": evidence[
            "hidden_gold_evaluation_sha256"
        ],
        "runtime_llm_topology.json": evidence["runtime_llm_topology_sha256"],
        "runtime_evidence_ledger.jsonl": evidence[
            "runtime_evidence_ledger_sha256"
        ],
        "runtime_failure_summary.json": evidence[
            "runtime_failure_summary_sha256"
        ],
        "runtime_completion_summary.json": evidence[
            "runtime_completion_summary_sha256"
        ],
        "runtime_progress.jsonl": evidence["runtime_progress_sha256"],
        "runtime_tool_calls.jsonl": evidence["runtime_tool_calls_sha256"],
        "runtime_traces.jsonl": evidence["runtime_traces_sha256"],
        "runtime_task_handoffs.jsonl": evidence[
            "runtime_task_handoffs_sha256"
        ],
        "runtime_observations.jsonl": evidence["runtime_observations_sha256"],
    }
    for filename, expected_sha256 in run_hashes.items():
        assert hashlib.sha256((run_path / filename).read_bytes()).hexdigest() == (
            expected_sha256
        )
    assert Path(evidence["operator_audit"]).is_file()

    visible_path = Path(candidate["visible_questions_path"])
    assert hashlib.sha256(visible_path.read_bytes()).hexdigest() == (
        evidence["visible_questions_sha256"]
    )
    question = json.loads(visible_path.read_text(encoding="utf-8"))["questions"][0]
    assert question["id"] == candidate["id"]
    assert question["task_intent"] == candidate["task_intent"]
    assert question["task_intent"]["formal"] == "not_applicable"
    assert question["source"]["target_publication_identity"] == (
        "evaluator_only_hidden"
    )
    assert question["source"]["public_source_discovery"] == (
        "disabled_for_this_blind_draw"
    )
    contract = question["estimator_execution_contract"]
    assert contract["estimator_id"] == "est_crossfit_orthogonal_contrast"
    assert [row["name"] for row in contract["request_fields"]] == [
        "outcomes",
        "assignments",
        "treated_means",
        "control_means",
        "propensities",
        "alpha",
    ]
    assert [row["name"] for row in contract["response_fields"]] == [
        "effect_estimate",
        "score_variance",
        "standard_error",
        "ci_lower",
        "ci_upper",
    ]

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": question}, sort_keys=True
    )
    for hidden_name in (
        "gold_manifest.json",
        "primary_article.xml",
        "official_code.zip",
        "reference_estimator.R",
        "semantic_reference.md",
        "semantic_rubric.json",
    ):
        assert hidden_name not in runtime_visible
    for hidden_identity_field in (
        "target_publication_title",
        "target_publication_authors",
        "target_publication_doi",
        "target_repository_url",
        "target_repository_commit",
    ):
        assert hidden_identity_field not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == CURRENT_SCORED_TASKS
    assert readiness["consumed_scored_tasks"] == CURRENT_CONSUMED_TASKS
    assert readiness["fully_gold_configured_tasks"] == CURRENT_SCORED_TASKS
    assert readiness["fully_gold_passed_tasks"] == 7
    assert readiness["latest_shared_mechanism_head"] == (
        LATEST_SHARED_MECHANISM_HEAD
    )
