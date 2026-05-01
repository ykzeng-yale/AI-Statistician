import json
from pathlib import Path

from statlean_agent.benchmarks import SEED_BENCHMARKS
from statlean_agent.contracts import ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.training import (
    build_dpo_pairs,
    build_rejected_dpo_attempts,
    build_training_manifest,
    build_verified_sft_examples,
)
from statlean_agent.serialization import read_jsonl
from statlean_agent.verifier import render_task


def test_build_training_manifest_from_seed_tasks() -> None:
    manifest = build_training_manifest(SEED_BENCHMARKS, run_id="test", base_model="lean-prover")
    assert manifest.run_id == "test"
    assert len(manifest.sft_examples) == len(SEED_BENCHMARKS)
    assert len(manifest.grpo_tasks) == len(SEED_BENCHMARKS)
    assert manifest.metadata["task_count"] == str(len(SEED_BENCHMARKS))
    assert manifest.metadata["dpo_pair_count"] == "0"
    assert manifest.metadata["sft_source"] == "benchmark_gold"


def test_build_verified_sft_examples_excludes_placeholder_tasks() -> None:
    attempts = tuple(
        ProofAttempt(task.task_id, "seed-registry", render_task(task.lean_task))
        for task in SEED_BENCHMARKS
    )
    reports = tuple(
        VerificationReport(task.task_id, VerificationStatus.ACCEPTED)
        for task in SEED_BENCHMARKS
    )

    examples = build_verified_sft_examples(SEED_BENCHMARKS, attempts, reports)
    manifest = build_training_manifest(
        SEED_BENCHMARKS,
        attempts,
        reports,
        run_id="verified",
        base_model="lean-prover",
    )

    placeholder_count = sum(1 for task in SEED_BENCHMARKS if task.lean_task.allowed_sorry)
    assert len(examples) == len(SEED_BENCHMARKS) - placeholder_count
    assert len(manifest.sft_examples) == len(examples)
    assert manifest.metadata["sft_source"] == "verified_attempts"
    assert all("sorry" not in example.response for example in examples)


def test_build_rejected_dpo_attempts_preserves_tasks_without_placeholders() -> None:
    attempts = build_rejected_dpo_attempts(SEED_BENCHMARKS)
    placeholder_count = sum(1 for task in SEED_BENCHMARKS if task.lean_task.allowed_sorry)

    assert len(attempts) == len(SEED_BENCHMARKS) - placeholder_count
    assert all("StatInference.__statlean_dpo_missing_premise__" in attempt.lean_code for attempt in attempts)
    assert all("sorry" not in attempt.lean_code for attempt in attempts)


def test_checked_in_training_manifest_uses_verified_sft_examples() -> None:
    manifest = json.loads(Path("artifacts/training/manifest.json").read_text(encoding="utf-8"))
    negative_attempts = read_jsonl(Path("artifacts/training/dpo-negative-attempts.jsonl"))
    negative_reports = read_jsonl(Path("artifacts/training/dpo-negative-reports.jsonl"))
    placeholder_count = sum(1 for task in SEED_BENCHMARKS if task.lean_task.allowed_sorry)

    assert manifest["metadata"]["sft_source"] == "verified_attempts"
    assert manifest["metadata"]["attempt_count"] == str(len(SEED_BENCHMARKS) + len(negative_attempts))
    assert manifest["metadata"]["dpo_pair_count"] == str(len(negative_attempts))
    assert len(manifest["dpo_pairs"]) == int(manifest["metadata"]["dpo_pair_count"])
    assert len(manifest["sft_examples"]) == len(SEED_BENCHMARKS) - placeholder_count
    assert len(manifest["grpo_tasks"]) == len(SEED_BENCHMARKS)
    assert all("sorry" not in example["response"] for example in manifest["sft_examples"])
    assert len(negative_attempts) == len(SEED_BENCHMARKS) - placeholder_count
    assert all("__statlean_dpo_missing_premise__" in attempt["lean_code"] for attempt in negative_attempts)
    assert all(report["status"] == "rejected" for report in negative_reports)
    assert all("Task.lean:" in report["first_error"] for report in negative_reports)


def test_build_dpo_pairs_prefers_accepted_attempt() -> None:
    attempts = (
        ProofAttempt("task", "agent", "theorem ok : True := by trivial"),
        ProofAttempt("task", "agent", "theorem bad : True := by sorry"),
    )
    reports = (
        VerificationReport("task", VerificationStatus.ACCEPTED),
        VerificationReport("task", VerificationStatus.REJECTED, first_error="forbidden token"),
    )
    pairs = build_dpo_pairs(attempts, reports)
    assert len(pairs) == 1
    assert "trivial" in pairs[0].chosen
    assert "sorry" in pairs[0].rejected
