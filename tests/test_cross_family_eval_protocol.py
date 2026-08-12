from __future__ import annotations

import copy
from argparse import Namespace
from pathlib import Path

from ai_statistician.cross_family_eval_protocol import (
    advance_confirmatory_evaluation_cohort,
    load_cross_family_eval_protocol,
    resolve_confirmatory_evaluation_cohort,
    resolve_cross_family_eval_panel,
    summarize_candidate_gate_independence,
    validate_cross_family_eval_protocol,
)
from ai_statistician.cli import _cross_family_eval_protocol_selection
from ai_statistician.research_agent_runtime import _runtime_input_context_summary
from ai_statistician.research_lab import load_open_research_questions


PROTOCOL_PATH = Path(
    "benchmarks/autonomous_cross_family_e2e_protocol_20260713.json"
)


def test_frozen_cross_family_protocol_resolves_disjoint_panels() -> None:
    protocol = load_cross_family_eval_protocol(PROTOCOL_PATH)
    questions = load_open_research_questions(Path("examples/research_questions.json"))

    development = resolve_cross_family_eval_panel(
        protocol,
        panel_id="development",
        questions=questions,
    )
    held_out = resolve_cross_family_eval_panel(
        protocol,
        panel_id="held_out",
        questions=questions,
    )

    assert development["question_ids"] == [
        "right_censored_survival_km",
        "sequential_anytime_bernoulli",
    ]
    assert development["task_families"] == ["survival", "sequential"]
    assert held_out["question_ids"] == [
        "high_dimensional_spiked_pca",
        "extreme_tail_quantile_hill",
    ]
    assert held_out["task_families"] == ["high_dimensional", "extremes"]
    assert set(development["task_families"]).isdisjoint(held_out["task_families"])
    assert development["protocol_fingerprint"] == held_out["protocol_fingerprint"]
    assert development["evaluation_claude_model_tier"] == "haiku"
    assert development["evaluation_claude_model"] == (
        "claude-haiku-4-5-20251001"
    )
    assert development["sonnet_opus_live_calls_forbidden"] is True
    assert development["confirmatory_source_outcome_blinding_required"] is True
    assert development["post_outcome_fresh_cohort_required"] is True
    assert development["confirmatory_candidate_seed_blinding_required"] is True


def test_outcome_informed_candidate_uses_a_fresh_evaluator_owned_cohort() -> None:
    protocol = load_cross_family_eval_protocol(PROTOCOL_PATH)
    questions = load_open_research_questions(Path("examples/research_questions.json"))
    selection = resolve_cross_family_eval_panel(
        protocol,
        panel_id="development",
        questions=questions,
    )
    question_id = "right_censored_survival_km"
    context = {"cross_family_evaluation_protocol": selection}

    initial, errors = resolve_confirmatory_evaluation_cohort(
        context,
        question_id=question_id,
        execution_seed=29,
    )
    assert errors == []
    assert initial["cohort_index"] == 0
    assert initial["seed"] == 29
    assert initial["candidate_model_seed_disclosure"] == "WITHHELD"

    context["runtime_confirmatory_evaluation_cohort"] = initial
    outcome = {
        "feedback_id": "confirmatory-outcome:one",
        "question_id": question_id,
        "confirmatory_evaluation_cohort": initial,
        "empirical_outcomes": [{"aggregate_value": 0.1}],
    }
    next_cohort, transition, errors = advance_confirmatory_evaluation_cohort(
        context,
        confirmatory_outcome=outcome,
        question_id=question_id,
    )
    assert errors == []
    assert next_cohort["cohort_index"] == 1
    assert next_cohort["seed"] != initial["seed"]
    assert transition["fresh_seed"] is True
    assert transition["runtime_selected_research_content"] is False

    changed_outcome = copy.deepcopy(outcome)
    changed_outcome["feedback_id"] = "confirmatory-outcome:changed-result"
    changed_outcome["empirical_outcomes"] = [{"aggregate_value": 999.0}]
    changed_cohort, _, errors = advance_confirmatory_evaluation_cohort(
        context,
        confirmatory_outcome=changed_outcome,
        question_id=question_id,
    )
    assert errors == []
    assert changed_cohort["seed"] == next_cohort["seed"]
    assert changed_cohort["cohort_id"] != next_cohort["cohort_id"]

    summary = summarize_candidate_gate_independence(
        [
            {"evidence_type": "simulation", "payload": {
                "confirmatory_evaluation_cohort": initial,
            }},
            {"evidence_type": "simulation", "payload": {
                "confirmatory_evaluation_cohort": initial,
            }},
            {"evidence_type": "confirmatory_evaluation_cohort_transition", "payload": {
                "transition": transition,
            }},
            {"evidence_type": "simulation", "payload": {
                "confirmatory_evaluation_cohort": next_cohort,
            }},
        ],
        architect_context=context,
    )
    assert summary["status"] == "POST_OUTCOME_FRESH_COHORT_VERIFIED"
    assert summary["validation_errors"] == []
    assert summary["n_distinct_executed_cohorts"] == 2


def test_candidate_gate_seed_independence_is_scoped_to_each_question() -> None:
    protocol = load_cross_family_eval_protocol(PROTOCOL_PATH)
    questions = load_open_research_questions(Path("examples/research_questions.json"))
    selection = resolve_cross_family_eval_panel(
        protocol,
        panel_id="development",
        questions=questions,
    )
    context = {"cross_family_evaluation_protocol": selection}
    survival, survival_errors = resolve_confirmatory_evaluation_cohort(
        context,
        question_id="right_censored_survival_km",
        execution_seed=29,
    )
    sequential, sequential_errors = resolve_confirmatory_evaluation_cohort(
        context,
        question_id="sequential_anytime_bernoulli",
        execution_seed=29,
    )

    assert survival_errors == sequential_errors == []
    assert survival["seed"] == sequential["seed"] == 29
    assert survival["cohort_id"] != sequential["cohort_id"]
    summary = summarize_candidate_gate_independence(
        [
            {
                "evidence_type": "simulation",
                "payload": {"confirmatory_evaluation_cohort": survival},
            },
            {
                "evidence_type": "simulation",
                "payload": {"confirmatory_evaluation_cohort": sequential},
            },
        ],
        architect_context=context,
    )

    assert summary["status"] == "NO_POST_OUTCOME_CONTINUATION_OBSERVED"
    assert summary["validation_errors"] == []
    assert summary["n_distinct_executed_cohorts"] == 2


def test_candidate_gate_rejects_seed_reuse_within_one_question() -> None:
    protocol = load_cross_family_eval_protocol(PROTOCOL_PATH)
    questions = load_open_research_questions(Path("examples/research_questions.json"))
    selection = resolve_cross_family_eval_panel(
        protocol,
        panel_id="development",
        questions=questions,
    )
    context = {"cross_family_evaluation_protocol": selection}
    initial, errors = resolve_confirmatory_evaluation_cohort(
        context,
        question_id="right_censored_survival_km",
        execution_seed=29,
    )
    reused = {**initial, "cohort_id": initial["cohort_id"] + ":duplicate"}

    assert errors == []
    summary = summarize_candidate_gate_independence(
        [
            {
                "evidence_type": "simulation",
                "payload": {"confirmatory_evaluation_cohort": initial},
            },
            {
                "evidence_type": "simulation",
                "payload": {"confirmatory_evaluation_cohort": reused},
            },
        ],
        architect_context=context,
    )

    assert summary["status"] == "VIOLATION"
    assert summary["validation_errors"] == [
        "distinct confirmatory cohorts for one question reused one seed"
    ]


def test_cross_family_protocol_rejects_family_overlap() -> None:
    protocol = load_cross_family_eval_protocol(PROTOCOL_PATH)
    bad_protocol = copy.deepcopy(protocol)
    bad_protocol["panels"]["held_out"]["tasks"][0]["task_family"] = "survival"

    errors = validate_cross_family_eval_protocol(bad_protocol)

    assert "development and held_out task families must be disjoint" in errors


def test_cross_family_protocol_requires_generated_code_semantic_review() -> None:
    protocol = load_cross_family_eval_protocol(PROTOCOL_PATH)
    bad_protocol = copy.deepcopy(protocol)
    bad_protocol["run_contract"][
        "generated_code_semantic_review_required"
    ] = False

    errors = validate_cross_family_eval_protocol(bad_protocol)

    assert (
        "run_contract.generated_code_semantic_review_required must be true"
        in errors
    )


def test_cross_family_protocol_rejects_question_family_drift() -> None:
    protocol = load_cross_family_eval_protocol(PROTOCOL_PATH)
    bad_protocol = copy.deepcopy(protocol)
    bad_protocol["panels"]["development"]["tasks"][0]["task_family"] = (
        "experimental_design"
    )
    questions = load_open_research_questions(Path("examples/research_questions.json"))

    try:
        resolve_cross_family_eval_panel(
            bad_protocol,
            panel_id="development",
            questions=questions,
        )
    except ValueError as exc:
        assert "task-family mismatches" in str(exc)
    else:
        raise AssertionError("question/task-family drift must fail closed")


def _protocol_cli_args(**overrides: object) -> Namespace:
    values: dict[str, object] = {
        "cross_family_eval_protocol": str(PROTOCOL_PATH),
        "cross_family_eval_panel": "development",
        "capability_eval": True,
        "capability_eval_preset": "full-live",
        "resume_runtime_manifest": "",
        "context_json": "",
        "capability_gap_routing_jsonl": [],
        "question_task_family": [],
        "question_id": [],
        "question_file": "examples/research_questions.json",
        "max_questions": 0,
    }
    values.update(overrides)
    return Namespace(**values)


def test_cross_family_cli_selects_the_complete_frozen_panel() -> None:
    questions = load_open_research_questions(Path("examples/research_questions.json"))

    question_ids, selection, errors = _cross_family_eval_protocol_selection(
        _protocol_cli_args(),
        questions,
    )

    assert errors == []
    assert question_ids == [
        "right_censored_survival_km",
        "sequential_anytime_bernoulli",
    ]
    assert selection["minimum_distinct_task_families"] == 2
    assert selection["protocol_path"] == str(PROTOCOL_PATH)
    assert selection["evaluation_claude_model_tier"] == "haiku"
    assert selection["evaluation_claude_model"] == "claude-haiku-4-5-20251001"
    assert selection["sonnet_opus_live_calls_forbidden"] is True


def test_cross_family_cli_rejects_single_question_override() -> None:
    questions = load_open_research_questions(Path("examples/research_questions.json"))

    _, _, errors = _cross_family_eval_protocol_selection(
        _protocol_cli_args(question_id=["right_censored_survival_km"]),
        questions,
    )

    assert any("must exactly match the frozen protocol panel" in error for error in errors)


def test_cross_family_cli_rejects_resume() -> None:
    questions = load_open_research_questions(Path("examples/research_questions.json"))

    _, _, errors = _cross_family_eval_protocol_selection(
        _protocol_cli_args(
            resume_runtime_manifest="prior.json",
        ),
        questions,
    )

    assert "fresh cross-family protocol runs forbid --resume-runtime-manifest" in errors


def test_runtime_manifest_summary_preserves_frozen_protocol_lineage() -> None:
    questions = load_open_research_questions(Path("examples/research_questions.json"))
    _, selection, errors = _cross_family_eval_protocol_selection(
        _protocol_cli_args(),
        questions,
    )
    assert errors == []

    summary = _runtime_input_context_summary(
        {"cross_family_evaluation_protocol": selection}
    )

    assert summary["runtime_cross_family_evaluation_protocol_supplied"] is True
    assert summary["runtime_cross_family_evaluation_protocol"] == selection
