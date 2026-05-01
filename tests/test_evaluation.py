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

