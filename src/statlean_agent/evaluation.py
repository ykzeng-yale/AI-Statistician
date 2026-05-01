"""Benchmark evaluation helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from statlean_agent.contracts import EvalReport, ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.rewards import aggregate_reward_breakdowns, scan_policy_tokens, score_attempt


def evaluate_attempts(
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    allowed_placeholders_by_task: Mapping[str, Iterable[str]] | None = None,
) -> EvalReport:
    """Aggregate proof-attempt metrics."""

    if len(attempts) != len(reports):
        raise ValueError("attempts and reports must have the same length")

    allowed_by_task = allowed_placeholders_by_task or {}
    total = len(attempts)
    status_counts = _empty_status_counts()
    diagnostics: list[str] = []
    reward_breakdowns = []

    for attempt, report in zip(attempts, reports, strict=True):
        if attempt.task_id != report.task_id:
            diagnostics.append(
                f"{attempt.task_id}: paired with report for `{report.task_id}`; metrics use the report status"
            )

        status = _normalize_status(report.status, report.task_id, diagnostics)
        allowed_placeholders = tuple(allowed_by_task.get(attempt.task_id, ()))
        observations = scan_policy_tokens(
            attempt.lean_code,
            allowed_placeholders=allowed_placeholders,
        )
        violations = tuple(occurrence for occurrence in observations if not occurrence.allowed)
        diagnostics.extend(f"{attempt.task_id}: {occurrence.diagnostic}" for occurrence in observations)

        effective_status = status
        first_error = report.first_error
        if violations and status is VerificationStatus.ACCEPTED:
            first = violations[0]
            effective_status = VerificationStatus.REJECTED
            first_error = f"forbidden token `{first.token}` at line {first.line}, column {first.column}"
            diagnostics.append(
                f"{attempt.task_id}: accepted report overridden to rejected because policy violations were found"
            )

        status_counts[effective_status.value] += 1
        scoring_report = VerificationReport(
            task_id=report.task_id,
            status=effective_status,
            locally_valid_steps=report.locally_valid_steps,
            closed_goals=report.closed_goals,
            first_error=first_error,
            diagnostics=report.diagnostics,
        )
        reward_breakdowns.append(
            score_attempt(
                attempt,
                scoring_report,
                allowed_placeholders=allowed_placeholders,
            )
        )

    reward_total = aggregate_reward_breakdowns(reward_breakdowns)
    average_reward = reward_total.total / total if total else 0.0
    average_reward_components = {
        key: value / total for key, value in reward_total.components.items()
    } if total else {}
    accepted = status_counts[VerificationStatus.ACCEPTED.value]
    rejected = status_counts[VerificationStatus.REJECTED.value]
    timeout = status_counts[VerificationStatus.TIMEOUT.value]
    error = status_counts[VerificationStatus.ERROR.value]
    pass_rate = accepted / total if total else 0.0

    return EvalReport(
        total_attempts=total,
        accepted=accepted,
        rejected=rejected,
        timeout=timeout,
        error=error,
        average_reward=average_reward,
        pass_rate=pass_rate,
        status_counts=status_counts,
        reward_totals=reward_total.components,
        average_reward_components=average_reward_components,
        diagnostics=tuple(diagnostics),
    )


def _empty_status_counts() -> dict[str, int]:
    return {status.value: 0 for status in VerificationStatus}


def _normalize_status(
    status: VerificationStatus | str,
    task_id: str,
    diagnostics: list[str],
) -> VerificationStatus:
    if isinstance(status, VerificationStatus):
        return status

    normalized = str(status).strip().lower()
    for candidate in VerificationStatus:
        if normalized in {candidate.value, candidate.name.lower()}:
            return candidate

    diagnostics.append(f"{task_id}: unknown verification status `{status}` counted as error")
    return VerificationStatus.ERROR
