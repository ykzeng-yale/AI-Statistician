from statlean_agent.benchmarks import SEED_BENCHMARKS
from statlean_agent.contracts import ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.training import build_dpo_pairs, build_training_manifest


def test_build_training_manifest_from_seed_tasks() -> None:
    manifest = build_training_manifest(SEED_BENCHMARKS, run_id="test", base_model="lean-prover")
    assert manifest.run_id == "test"
    assert len(manifest.sft_examples) == len(SEED_BENCHMARKS)
    assert len(manifest.grpo_tasks) == len(SEED_BENCHMARKS)
    assert manifest.metadata["task_count"] == str(len(SEED_BENCHMARKS))


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

