from statlean_agent.contracts import (
    CuratedLemmaCandidate,
    ProofAttempt,
    VerificationReport,
    VerificationStatus,
)
from statlean_agent.curation import curate_candidate
from statlean_agent.rewards import aggregate_reward_breakdowns, find_forbidden_tokens, score_attempt


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
        lean_code="theorem bad : True := by\n  sorry\n  sorry",
        verifier_status=VerificationStatus.REJECTED,
    )
    report = VerificationReport(task_id="task", status=VerificationStatus.REJECTED)
    reward = score_attempt(attempt, report)
    assert reward.total < 0
    assert reward.components["forbidden_sorry"] == -20.0


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


def test_reward_allows_configured_placeholder_without_policy_penalty() -> None:
    attempt = ProofAttempt(
        task_id="draft",
        agent_key="formalizer",
        lean_code="theorem draft : True := by\n  sorry",
        verifier_status=VerificationStatus.ACCEPTED,
    )
    report = VerificationReport(task_id="draft", status=VerificationStatus.ACCEPTED)
    reward = score_attempt(attempt, report, allowed_placeholders=("sorry",))
    assert reward.total == 10.0
    assert "forbidden_sorry" not in reward.components


def test_reward_does_not_allow_admit_placeholder() -> None:
    attempt = ProofAttempt(
        task_id="draft",
        agent_key="formalizer",
        lean_code="theorem draft : True := by\n  admit",
        verifier_status=VerificationStatus.ACCEPTED,
    )
    report = VerificationReport(task_id="draft", status=VerificationStatus.ACCEPTED)
    reward = score_attempt(attempt, report, allowed_placeholders=("admit",))
    assert reward.components["forbidden_admit"] == -10.0


def test_reward_keeps_timeout_penalty_with_policy_violation() -> None:
    attempt = ProofAttempt(
        task_id="timeout",
        agent_key="formalizer",
        lean_code="theorem timeout : True := by\n  sorry",
        verifier_status=VerificationStatus.TIMEOUT,
    )
    report = VerificationReport(task_id="timeout", status=VerificationStatus.TIMEOUT)
    reward = score_attempt(attempt, report)
    assert reward.components["timeout"] == -2.0
    assert reward.components["forbidden_sorry"] == -10.0


def test_policy_scan_ignores_comments_and_strings() -> None:
    source = 'theorem ok : True := by\n  -- sorry in a comment\n  have h := "admit in a string"\n  trivial'
    assert find_forbidden_tokens(source) == ()


def test_aggregate_reward_breakdowns_sums_components() -> None:
    accepted = score_attempt(
        ProofAttempt("ok", "agent", "theorem ok : True := by trivial"),
        VerificationReport("ok", VerificationStatus.ACCEPTED),
    )
    rejected = score_attempt(
        ProofAttempt("bad", "agent", "theorem bad : True := by sorry"),
        VerificationReport("bad", VerificationStatus.REJECTED),
    )

    aggregate = aggregate_reward_breakdowns((accepted, rejected))

    assert aggregate.total == accepted.total + rejected.total
    assert aggregate.components["proof_complete"] == 10.0
    assert aggregate.components["forbidden_sorry"] == -10.0
