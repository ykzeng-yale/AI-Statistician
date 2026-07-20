from __future__ import annotations

import copy
from argparse import Namespace
from pathlib import Path

from ai_statistician.cross_family_eval_protocol import (
    load_cross_family_eval_protocol,
    resolve_cross_family_eval_panel,
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
        "learning_memory_jsonl": [],
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


def test_cross_family_cli_rejects_resume_and_learning_memory() -> None:
    questions = load_open_research_questions(Path("examples/research_questions.json"))

    _, _, errors = _cross_family_eval_protocol_selection(
        _protocol_cli_args(
            resume_runtime_manifest="prior.json",
            learning_memory_jsonl=["prior.jsonl"],
        ),
        questions,
    )

    assert "fresh cross-family protocol runs forbid --resume-runtime-manifest" in errors
    assert "fresh cross-family protocol runs forbid --learning-memory-jsonl" in errors


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
