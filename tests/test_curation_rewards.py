from statlean_agent.contracts import (
    CuratedLemmaCandidate,
    ProofAttempt,
    VerificationReport,
    VerificationStatus,
)
from statlean_agent.curation import curate_candidate
from statlean_agent.rewards import score_attempt


def test_curator_rejects_sorry() -> None:
    candidate = CuratedLemmaCandidate(
        name="bad",
        statement="theorem bad : True := by",
        proof="sorry",
        motivation_tasks=("task",),
        reuse_count=1,
        semantic_notes="bad example",
    )
    decision = curate_candidate(candidate)
    assert not decision.accepted
    assert any("sorry" in reason for reason in decision.reasons)


def test_reward_penalizes_forbidden_tokens() -> None:
    attempt = ProofAttempt(
        task_id="task",
        agent_key="whole_proof_generator",
        lean_code="theorem bad : True := by sorry",
        verifier_status=VerificationStatus.REJECTED,
    )
    report = VerificationReport(task_id="task", status=VerificationStatus.REJECTED)
    reward = score_attempt(attempt, report)
    assert reward.total < 0
    assert "forbidden_sorry" in reward.components


def test_reward_accepts_verified_progress() -> None:
    attempt = ProofAttempt(
        task_id="task",
        agent_key="tactic_synthesizer",
        lean_code="theorem ok : True := by trivial",
        premises_used=("True.intro",),
        verifier_status=VerificationStatus.ACCEPTED,
    )
    report = VerificationReport(
        task_id="task",
        status=VerificationStatus.ACCEPTED,
        locally_valid_steps=1,
        closed_goals=1,
    )
    reward = score_attempt(attempt, report)
    assert reward.total > 10

