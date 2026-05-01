from statlean_agent.contracts import ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.evaluation import evaluate_attempts


def test_evaluate_attempts() -> None:
    attempts = (
        ProofAttempt("a", "agent", "theorem ok : True := by trivial"),
        ProofAttempt("b", "agent", "theorem bad : True := by sorry"),
    )
    reports = (
        VerificationReport("a", VerificationStatus.ACCEPTED),
        VerificationReport("b", VerificationStatus.REJECTED),
    )
    report = evaluate_attempts(attempts, reports)
    assert report.total_attempts == 2
    assert report.accepted == 1
    assert report.rejected == 1
    assert report.pass_rate == 0.5
    assert report.status_counts == {"accepted": 1, "rejected": 1, "timeout": 0, "error": 0}
    assert report.reward_totals["proof_complete"] == 10.0
    assert report.reward_totals["forbidden_sorry"] == -10.0


def test_evaluate_attempts_normalizes_statuses_and_aggregates_rewards() -> None:
    attempts = (
        ProofAttempt("a", "agent", "theorem ok : True := by trivial", premises_used=("True.intro",)),
        ProofAttempt("b", "agent", "theorem slow : True := by trivial"),
        ProofAttempt("c", "agent", "theorem broken : True := by trivial"),
    )
    reports = (
        VerificationReport("a", "ACCEPTED", locally_valid_steps=2, closed_goals=1),
        VerificationReport("b", "timeout"),
        VerificationReport("c", "not-a-status"),
    )

    report = evaluate_attempts(attempts, reports)

    assert report.status_counts == {"accepted": 1, "rejected": 0, "timeout": 1, "error": 1}
    assert report.accepted == 1
    assert report.timeout == 1
    assert report.error == 1
    assert report.reward_totals["locally_valid_steps"] == 0.5
    assert report.reward_totals["closed_goals"] == 0.75
    assert report.reward_totals["premises_used"] == 0.1
    assert report.average_reward_components["proof_complete"] == 10.0 / 3
    assert any("unknown verification status" in diagnostic for diagnostic in report.diagnostics)


def test_evaluate_attempts_overrides_accepted_for_forbidden_placeholder() -> None:
    attempts = (
        ProofAttempt("bad", "agent", "theorem bad : True := by\n  sorry"),
    )
    reports = (
        VerificationReport("bad", VerificationStatus.ACCEPTED),
    )

    report = evaluate_attempts(attempts, reports)

    assert report.accepted == 0
    assert report.rejected == 1
    assert report.pass_rate == 0.0
    assert report.reward_totals["forbidden_sorry"] == -10.0
    assert any("overridden to rejected" in diagnostic for diagnostic in report.diagnostics)


def test_evaluate_attempts_allows_configured_placeholder_only() -> None:
    attempts = (
        ProofAttempt("draft", "agent", "theorem draft : True := by\n  sorry"),
        ProofAttempt("bad", "agent", "theorem bad : True := by\n  admit"),
    )
    reports = (
        VerificationReport("draft", VerificationStatus.ACCEPTED),
        VerificationReport("bad", VerificationStatus.ACCEPTED),
    )

    report = evaluate_attempts(
        attempts,
        reports,
        allowed_placeholders_by_task={"draft": ("sorry",), "bad": ("sorry",)},
    )

    assert report.accepted == 1
    assert report.rejected == 1
    assert "forbidden_sorry" not in report.reward_totals
    assert report.reward_totals["forbidden_admit"] == -10.0
    assert any("draft: allowed placeholder `sorry`" in diagnostic for diagnostic in report.diagnostics)
    assert any("bad: forbidden token `admit`" in diagnostic for diagnostic in report.diagnostics)
