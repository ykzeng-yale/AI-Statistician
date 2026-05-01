"""Benchmark evaluation helpers."""

from __future__ import annotations

from statlean_agent.contracts import EvalReport, ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.rewards import score_attempt


def evaluate_attempts(
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
) -> EvalReport:
    """Aggregate proof-attempt metrics."""

    if len(attempts) != len(reports):
        raise ValueError("attempts and reports must have the same length")

    total = len(attempts)
    accepted = sum(1 for report in reports if report.status is VerificationStatus.ACCEPTED)
    rejected = sum(1 for report in reports if report.status is VerificationStatus.REJECTED)
    timeout = sum(1 for report in reports if report.status is VerificationStatus.TIMEOUT)
    error = sum(1 for report in reports if report.status is VerificationStatus.ERROR)
    rewards = [score_attempt(attempt, report).total for attempt, report in zip(attempts, reports, strict=True)]
    average_reward = sum(rewards) / total if total else 0.0
    pass_rate = accepted / total if total else 0.0

    return EvalReport(
        total_attempts=total,
        accepted=accepted,
        rejected=rejected,
        timeout=timeout,
        error=error,
        average_reward=average_reward,
        pass_rate=pass_rate,
    )

