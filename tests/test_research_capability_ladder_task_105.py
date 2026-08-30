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
VISIBLE_PATH = Path(
    "benchmarks/research_l3_cusum_brownian_bridge_questions_20260829.json"
)
LEDGER_PATH = Path(
    "docs/evaluation_activations/task105_cusum_brownian_bridge_preactivation.json"
)
GOLD_ROOT = Path(
    "/Users/yukangzengcmac/.codex/evaluator_authority/AI-Statistician/"
    "research-l3-cusum-brownian-bridge-theory-20260829-v1"
)
GOLD_MANIFEST = GOLD_ROOT / "gold_manifest.json"
TASK_ID = "tied_down_cusum_brownian_bridge_known_theory_rederivation"
ACTIVATION_LEDGER = "dc349a4ac3f0e9884574a2f1c006d3dacc73ae00"
RUN_DIR = Path(
    "runs/main_worker_research_l3_cusum_brownian_bridge_theory_20260829_v1_"
    "codex_workspace_exact_haiku"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cusum_task105_is_consumed_after_its_only_product_draw() -> None:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    candidate = next(
        row for row in ladder["initial_candidate_queue"] if row["id"] == TASK_ID
    )
    evidence = candidate["activation_evidence"]
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    visible_payload = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    visible_question = visible_payload["questions"][0]
    loaded_question = load_open_research_questions(VISIBLE_PATH)[0]
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)
    activation = validate_research_gold_benchmark_activation(
        GOLD_MANIFEST,
        visible_questions={TASK_ID: visible_question},
    )

    assert candidate["level"] == "L3"
    assert candidate["family"] == "iid_location_change_functional_cusum"
    assert candidate["status"] == "consumed_scored"
    assert candidate["activation_status"] == (
        "fresh_live_v1_consumed_exact_haiku_runtime_accepted_"
        "hidden_theory_semantic_failed"
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
    assert visible_question["source"]["doi"] == "10.1214/aos/1176342816"
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

    assert _sha256(LEDGER_PATH) == evidence["public_preactivation_ledger_sha256"]
    assert ledger["preactivation_product_model_calls"] == 0
    assert ledger["preactivation_evaluator_model_calls"] == 16
    assert ledger["single_draw_policy"]["product_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert (
        ledger["single_draw_policy"]["automatic_tier_escalation_allowed"] is False
    )
    assert ledger["single_draw_policy"]["resume_or_rerun_allowed"] is False

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
        "453e7146cda57640c62d9630358a7a3c7297718d"
    )
    assert evidence["runtime_product_model_calls"] == 49
    assert evidence["runtime_client_tool_model_turns"] == 49
    assert evidence["runtime_direct_model_calls"] == 0
    assert evidence["runtime_client_tool_executions"] == 58
    assert evidence["runtime_client_tool_errors"] == 6
    assert evidence["runtime_model_calls_by_workspace"] == {
        "TheoryDeveloper": 11,
        "ArchitectMetricSemanticReviewer": 18,
        "CriticEvaluator": 20,
    }
    assert evidence["runtime_status"] == "ACCEPTED"
    assert evidence["runtime_outer_graph_iterations"] == 3
    assert evidence["runtime_same_owner_workspace_continuations"] == 0
    assert evidence["runtime_mode_conformant"] is True
    assert evidence["runtime_research_eval_complete"] is True
    assert evidence["runtime_serious_theory_completed"] is True
    assert evidence["runtime_theory_preexecution_review_accepted"] is True
    assert evidence["runtime_critic_research_acceptance"] is True
    assert evidence["theory_document_sha256"] == (
        "a3ccebb881a51fd10fb30e4ba0a8dbd12b3d9201a72d9a66de57072750c9431b"
    )
    assert evidence["referee_report_sha256"] == (
        "a96f927339934d9b78ae0fd67ccdfcd60c9bfc8e87159b6c83d23c84abe39234"
    )
    assert evidence["sole_hidden_assessment_invocations"] == 1
    assert evidence["hidden_gold_tasks_evaluated"] == 1
    assert evidence["hidden_evaluator_model_calls"] == 2
    assert evidence["hidden_theory_mechanical_checks_passed"] == "7/7"
    assert evidence["hidden_theory_semantic_claims_satisfied"] == 5
    assert evidence["hidden_theory_semantic_claims_violated"] == 2
    assert evidence["hidden_theory_semantic_claims_inconclusive"] == 1
    assert evidence["hidden_theory_semantic_passed"] is False
    assert evidence["runtime_feedback_generated"] is False
    assert evidence["operator_disposition"] == "FAILED"
    assert Path(evidence["operator_audit"]).is_file()
    assert evidence["automatic_tier_escalation_allowed"] is False
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["model_draw_resampling_blocked"] is True
    assert evidence["automated_full_task_passed"] is False
    assert evidence["full_task_passed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/104"
    assert evidence["ladder_score_after_activation"] == (
        "7/105 with one frozen unconsumed task"
    )
    assert evidence["ladder_score_after_consumption"] == "7/105"

    expected_runtime_hashes = {
        "tied_down_cusum_brownian_bridge_known_theory_rederivation_runtime_result.json": (
            "b5728c88984cefd69d46ed12badbfdd6b1d963ca4cf7167d6c7260eb568e42a9"
        ),
        "research_agent_runtime_manifest.json": (
            "f44a4a60fc27c3603732de276ffe949c4b50ff50900db92cd48c0ddd5dbfae9c"
        ),
        "research_capability_gold_evaluation.json": (
            "2b5990882ff49bb2d2995482ef9148d7969f8c376679959310cb3fdd17ac7957"
        ),
        "runtime_completion_summary.json": (
            "5f8d99cfe4de1bceb07b428bc91e22cfb93cfec68d37e1b3fbcb5fe5e2ae6b4c"
        ),
        "runtime_failure_summary.json": (
            "24cb04a35027713ddc327549df51ae6eeb6939955b1649c1b2c05b34e73c0ac6"
        ),
        "runtime_llm_topology.json": (
            "b5b107b4a68b017114f674089fa87b3d41b5de91401d29eaaf01aaf19980ed48"
        ),
        "runtime_progress.jsonl": (
            "186ad1314d79186d53907abfe18bd5cd3e7e2d168d5084254b301916e19f0824"
        ),
    }
    for name, expected_hash in expected_runtime_hashes.items():
        assert _sha256(RUN_DIR / name) == expected_hash

    assessment = json.loads(
        (RUN_DIR / "research_capability_gold_evaluation.json").read_text(
            encoding="utf-8"
        )
    )
    task_assessment = assessment["tasks"][0]
    assert assessment["n_tasks_evaluated"] == 1
    assert assessment["n_tasks_passed"] == 0
    assert assessment["all_active_tasks_passed"] is False
    assert assessment["runtime_feedback_generated"] is False
    assert task_assessment["hidden_theory_execution_passed"] is True
    assert task_assessment["hidden_theory_semantic_candidate_model_calls"] == 2
    assert task_assessment["hidden_theory_semantic_passed"] is False
    assert task_assessment["task_passed"] is False

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
