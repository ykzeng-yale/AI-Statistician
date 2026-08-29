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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cusum_task105_is_frozen_before_its_only_product_draw() -> None:
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
    assert candidate["status"] == "active_scored"
    assert candidate["activation_status"] == (
        "preactivated_frozen_pre_first_exact_haiku_draw"
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
    assert evidence["first_runtime_model_call_occurred"] is False
    assert evidence["fresh_live_runs"] == 0
    assert evidence["runtime_invocations"] == 0
    assert evidence["activation_ledger_commit"] == ACTIVATION_LEDGER
    assert evidence["activation_push_confirmed_on_work_branch_and_main"] is True
    assert evidence["single_fresh_draw_only"] is True
    assert evidence["planned_runtime_model"] == "claude-haiku-4-5-20251001"
    assert evidence["automatic_tier_escalation_allowed"] is False
    assert evidence["sonnet_product_calls"] == 0
    assert evidence["opus_product_calls"] == 0
    assert evidence["formalization_requirement"] == "not_applicable"
    assert evidence["formalizer_executed"] is False
    assert evidence["trusted_capability_credit"] is False
    assert evidence["ladder_score_before_activation"] == "7/104"
    assert evidence["ladder_score_after_activation"] == (
        "7/105 with one frozen unconsumed task"
    )

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
    assert readiness["scored_tasks_total"] == 105
    assert readiness["unconsumed_scored_tasks"] == 1
    assert readiness["consumed_scored_tasks"] == 104
    assert readiness["fully_gold_configured_tasks"] == 105
    assert readiness["fully_gold_passed_tasks"] == 7
