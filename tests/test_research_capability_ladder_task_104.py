from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _visible_question_hash_payload,
    validate_research_gold_benchmark_activation,
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_schema import load_open_research_questions


LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")
VISIBLE_PATH = Path("benchmarks/research_l3_bernoulli_lan_questions_20260829.json")
GOLD_ROOT = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l3-bernoulli-lan-theory-20260829-v1"
)
GOLD_MANIFEST = GOLD_ROOT / "gold_manifest.json"
TASK_ID = "bernoulli_local_alternatives_lan_known_theory_rederivation"
ACTIVATION_LEDGER = "ecce029fbfdd0c5b6fa6e6b49a8b5b9f5e69f0e7"
RUN_DIR = Path(
    "runs/main_worker_research_l3_bernoulli_lan_theory_20260829_v1_"
    "codex_workspace_exact_haiku"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_bernoulli_lan_task104_is_consumed_after_its_only_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)
    activation = validate_research_gold_benchmark_activation(
        GOLD_MANIFEST,
        visible_questions={TASK_ID: visible_question},
    )

    assert candidate["level"] == "L3"
    assert candidate["family"] == "local_asymptotic_binary_experiments"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_theory_reported_"
        "undisclosed_handoff_enum_and_gold_persisted_hydration_failed"
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
    assert loaded_question.id == TASK_ID
    assert loaded_question.task_intent == candidate["task_intent"]
    assert "estimator_execution_contract" not in visible_question
    assert "formal_target_contract" not in visible_question

    assert _sha256(VISIBLE_PATH) == evidence["visible_questions_sha256"]
    assert stable_hash(visible_payload) == evidence["visible_question_full_hash"]
    assert stable_hash(_visible_question_hash_payload(visible_question)) == evidence[
        "runtime_visible_question_hash"
    ]
    assert _sha256(GOLD_MANIFEST) == candidate["gold_manifest_sha256"]
    assert _sha256(GOLD_MANIFEST) == evidence["gold_manifest_file_sha256"]
    assert descriptor["benchmark_manifest_hash"] == candidate[
        "gold_descriptor_hash"
    ]
    assert descriptor["benchmark_manifest_hash"] == evidence[
        "gold_manifest_stable_hash"
    ]
    assert descriptor["active_task_ids"] == [TASK_ID]
    assert descriptor["n_full_task_gold_configured"] == 1

    expected_hidden_hashes = {
        "hidden_theory_harness.py": evidence["hidden_theory_harness_sha256"],
        "semantic_reference.md": evidence["hidden_reference_document_sha256"],
        "semantic_rubric.json": evidence["hidden_semantic_rubric_sha256"],
        "semantic_calibration_cases.json": evidence[
            "hidden_semantic_calibration_cases_sha256"
        ],
        "candidate_mode_near_miss.md": evidence[
            "hidden_candidate_mode_near_miss_sha256"
        ],
        "candidate_mode_negative_cases.json": evidence[
            "hidden_candidate_mode_negative_cases_sha256"
        ],
        "semantic_activation_attempt_1_protocol_v11.json": evidence[
            "semantic_activation_record_sha256"
        ],
        "theory_authority_calibration.json": evidence[
            "mechanical_activation_record_sha256"
        ],
    }
    for name, expected in expected_hidden_hashes.items():
        assert _sha256(GOLD_ROOT / name) == expected

    assert evidence["activation_schema_version"] == 4
    assert evidence["mechanical_authority_checks_correct"] == "7/7"
    assert evidence["mechanical_negative_variants_rejected"] == "7/7"
    assert evidence["semantic_protocol_version"] == 11
    assert evidence["semantic_candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert evidence["semantic_successful_qualification_model_calls"] == 16
    assert evidence["semantic_calibration_cases_correct"] == "6/6"
    assert evidence["semantic_candidate_mode_negative_cases_correct"] == "1/1"
    assert evidence["semantic_reference_claims"] == 8
    assert evidence["semantic_calibration_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert activation["activation_semantic_reference_documents_passed"] == 1
    assert (
        activation[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert activation["activation_semantic_model_calls"] == 0
    assert activation["activation_semantic_qualification_model_calls"] == 16
    assert activation["activation_semantic_qualification_reused"] is True

    assert evidence["hidden_gold_manifest_validated"] is True
    assert evidence["gold_frozen_before_first_runtime_model_call"] is True
    assert evidence["preactivation_product_model_calls"] == 0
    assert evidence["preactivation_evaluator_model_calls"] == 16
    assert evidence["first_runtime_model_call_occurred"] is True
    assert evidence["fresh_live_runs"] == 1
    assert evidence["runtime_invocations"] == 1
    assert evidence["activation_ledger_commit"] == ACTIVATION_LEDGER
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["product_code_head"] == (
        "c3245943a789a75b824a7aa435162809e4e7edbd"
    )
    assert evidence["runtime_product_model_calls"] == 96
    assert evidence["runtime_client_tool_model_turns"] == 96
    assert evidence["runtime_direct_model_calls"] == 0
    assert evidence["runtime_client_tool_executions"] == 95
    assert evidence["runtime_client_tool_errors"] == 15
    assert evidence["runtime_model_calls_by_workspace"] == {
        "TheoryDeveloper": 80,
        "ArchitectMetricSemanticReviewer": 16,
    }
    assert evidence["runtime_status"] == "BLOCKED"
    assert evidence["runtime_terminal_classification"] == (
        "theory_developer_reported_gap"
    )
    assert evidence["runtime_outer_graph_iterations"] == 3
    assert evidence["runtime_same_owner_workspace_continuations"] == 2
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is False
    assert evidence["runtime_serious_theory_completed"] is True
    assert evidence["runtime_theory_preexecution_review_accepted"] is False
    assert evidence["independent_theory_referee_executed"] is True
    assert evidence["independent_theory_referee_verdict"] == "REVISE"
    assert evidence["independent_revised_theory_accepted"] is False
    assert evidence["theory_document_sha256"] == (
        "df3f1aee0ba26108621188705dc7e4d9979a7cea7a8d84e336e688c26db002c2"
    )
    assert evidence["referee_report_sha256"] == (
        "d3e7530356e9c35b55d5617b890c52c0c394927a92e79b053dbd10b6b9768669"
    )
    assert evidence["sole_hidden_assessment_invocations"] == 1
    assert evidence["hidden_gold_tasks_evaluated"] == 0
    assert evidence["hidden_evaluator_model_calls"] == 0
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["operator_disposition"] == "FAILED"
    assert Path(evidence["operator_audit"]).exists()
    assert evidence["post_run_shared_mechanism_commit"] == (
        "36a3dbbe2bfdfb525a82daee25a9f0b92c91c3b7"
    )
    assert evidence["post_run_persisted_path_resolution_commit"] == (
        "9bf3a789adbabc123b1b20d489cecfe74bd9f46a"
    )
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_after_consumption"] == "7/104"

    expected_runtime_hashes = {
        "bernoulli_local_alternatives_lan_known_theory_rederivation_runtime_result.json": (
            "9136f9b613770e162f362fa9a548bf61e520f0d3335b85e2e6c54f461d90afd8"
        ),
        "research_agent_runtime_manifest.json": (
            "f4e5ba1e8af09e28b160cfa558a0f62acf32f0677a5a8f263e3a8ccfcf416fe2"
        ),
        "research_capability_gold_evaluation.json": (
            "52e8fb5eda961a894ba4cc33e63790437f31155711dc48efea09c541bd19f5c0"
        ),
        "runtime_failure_summary.json": (
            "bb755aba66b460f19e2b1da39f580f9677252740adccaa01a388db21666dfd2b"
        ),
        "runtime_llm_topology.json": (
            "b00a05fec1ae65fe2d9fc3341758fbe5afae35c1f6621b8c5aa0a99372c298e8"
        ),
    }
    for name, expected_hash in expected_runtime_hashes.items():
        assert _sha256(RUN_DIR / name) == expected_hash

    runtime_visible = json.dumps(
        {"candidate": candidate, "question": visible_question}, sort_keys=True
    )
    for hidden_name in (
        str(GOLD_MANIFEST),
        "semantic_reference.md",
        "semantic_rubric.json",
        "semantic_calibration_cases.json",
        "candidate_mode_near_miss.md",
        "candidate_mode_negative_cases.json",
    ):
        assert hidden_name not in runtime_visible

    readiness = ladder["current_readiness"]
    assert readiness["scored_tasks_total"] == 109
    assert readiness["unconsumed_scored_tasks"] == 0
    assert readiness["consumed_scored_tasks"] == 109
    assert readiness["fully_gold_configured_tasks"] == 109
    assert readiness["fully_gold_passed_tasks"] == 7
