"""Benchmark evaluation helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from statlean_agent.contracts import (
    BenchmarkTask,
    EvalReport,
    ProofAttempt,
    RewardBreakdown,
    VerificationReport,
    VerificationStatus,
)
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

        allowed_placeholders = tuple(allowed_by_task.get(attempt.task_id, ()))
        effective_status, reward_breakdown, _, _ = _evaluate_attempt_record(
            attempt,
            report,
            allowed_placeholders=allowed_placeholders,
            diagnostics=diagnostics,
        )
        status_counts[effective_status.value] += 1
        reward_breakdowns.append(reward_breakdown)

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


def summarize_benchmark_attempts(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    allowed_placeholders_by_task: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, object]:
    """Summarize benchmark attempts by split, domain tag, and task type.

    Domain-tag rows count each attempt once per tag, so their totals can exceed
    the global attempt count for multi-domain benchmark tasks.
    """

    if len(attempts) != len(reports):
        raise ValueError("attempts and reports must have the same length")

    task_by_id = _task_index(tasks)
    allowed_by_task = _allowed_placeholders_by_task(tasks)
    if allowed_placeholders_by_task is not None:
        allowed_by_task.update({
            task_id: tuple(tokens)
            for task_id, tokens in allowed_placeholders_by_task.items()
        })
    total = _SummaryBucket()
    by_phase: dict[str, _SummaryBucket] = {}
    by_split: dict[str, _SummaryBucket] = {}
    by_domain: dict[str, _SummaryBucket] = {}
    by_task_type: dict[str, _SummaryBucket] = {}

    for attempt, report in zip(attempts, reports, strict=True):
        task = task_by_id.get(attempt.task_id)
        if task is None:
            raise ValueError(f"unknown benchmark task id: {attempt.task_id}")

        allowed_placeholders = tuple(allowed_by_task.get(attempt.task_id, ()))
        effective_status, reward_breakdown, first_error, violations = _evaluate_attempt_record(
            attempt,
            report,
            allowed_placeholders=allowed_placeholders,
        )
        failure_category = _failure_category(
            effective_status,
            first_error=first_error,
            diagnostics=report.diagnostics,
            violations=violations,
        )

        split = _enum_value(task.split)
        task_type = _enum_value(task.task_type)
        domains = tuple(dict.fromkeys(task.domain_tags)) or ("untagged",)
        phase = _phase_for_task(task)

        total.add(effective_status, reward_breakdown.total, failure_category)
        by_phase.setdefault(phase, _SummaryBucket()).add(
            effective_status,
            reward_breakdown.total,
            failure_category,
        )
        by_split.setdefault(split, _SummaryBucket()).add(
            effective_status,
            reward_breakdown.total,
            failure_category,
        )
        by_task_type.setdefault(task_type, _SummaryBucket()).add(
            effective_status,
            reward_breakdown.total,
            failure_category,
        )
        for domain in domains:
            by_domain.setdefault(domain, _SummaryBucket()).add(
                effective_status,
                reward_breakdown.total,
                failure_category,
            )

    return {
        "total": total.to_row(),
        "by_phase": _rows("phase", by_phase),
        "by_split": _rows("split", by_split),
        "by_domain": _rows("domain", by_domain),
        "by_task_type": _rows("task_type", by_task_type),
    }


@dataclass
class _SummaryBucket:
    attempts: int = 0
    passed: int = 0
    reward_total: float = 0.0
    failure_categories: dict[str, int] = field(default_factory=dict)

    def add(
        self,
        status: VerificationStatus,
        reward: float,
        failure_category: str | None,
    ) -> None:
        self.attempts += 1
        self.reward_total += reward
        if status is VerificationStatus.ACCEPTED:
            self.passed += 1
            return
        if failure_category:
            self.failure_categories[failure_category] = (
                self.failure_categories.get(failure_category, 0) + 1
            )

    def to_row(self) -> dict[str, object]:
        return {
            "attempts": self.attempts,
            "passed": self.passed,
            "failed": self.attempts - self.passed,
            "mean_reward": self.reward_total / self.attempts if self.attempts else 0.0,
            "failure_categories": dict(sorted(self.failure_categories.items())),
        }


def _evaluate_attempt_record(
    attempt: ProofAttempt,
    report: VerificationReport,
    *,
    allowed_placeholders: Iterable[str] = (),
    diagnostics: list[str] | None = None,
) -> tuple[
    VerificationStatus,
    RewardBreakdown,
    str | None,
    tuple[object, ...],
]:
    status = _normalize_status(report.status, report.task_id, diagnostics if diagnostics is not None else [])
    observations = scan_policy_tokens(
        attempt.lean_code,
        allowed_placeholders=allowed_placeholders,
    )
    violations = tuple(occurrence for occurrence in observations if not occurrence.allowed)
    if diagnostics is not None:
        diagnostics.extend(f"{attempt.task_id}: {occurrence.diagnostic}" for occurrence in observations)

    effective_status = status
    first_error = report.first_error
    if violations and status is VerificationStatus.ACCEPTED:
        first = violations[0]
        effective_status = VerificationStatus.REJECTED
        first_error = f"forbidden token `{first.token}` at line {first.line}, column {first.column}"
        if diagnostics is not None:
            diagnostics.append(
                f"{attempt.task_id}: accepted report overridden to rejected because policy violations were found"
            )

    scoring_report = VerificationReport(
        task_id=report.task_id,
        status=effective_status,
        locally_valid_steps=report.locally_valid_steps,
        closed_goals=report.closed_goals,
        first_error=first_error,
        diagnostics=report.diagnostics,
    )
    return (
        effective_status,
        score_attempt(
            attempt,
            scoring_report,
            allowed_placeholders=allowed_placeholders,
        ),
        first_error,
        violations,
    )


def _failure_category(
    status: VerificationStatus,
    *,
    first_error: str | None,
    diagnostics: Iterable[str],
    violations: Iterable[object],
) -> str | None:
    if status is VerificationStatus.ACCEPTED:
        return None
    if status is VerificationStatus.TIMEOUT:
        return "timeout"

    text = " ".join(part for part in (first_error, *diagnostics) if part).lower()
    if "lake executable not found" in text:
        return "missing_lake"
    if "unknown module" in text or "module not found" in text or "invalid import" in text:
        return "import_error"
    if "forbidden token" in text or tuple(violations):
        return "policy_violation"
    if "unknown declaration" in text or "unknown constant" in text or "unknown identifier" in text:
        return "unknown_declaration"
    if "type mismatch" in text or "application type mismatch" in text or "failed to synthesize" in text:
        return "type_mismatch"
    if "unsolved goal" in text:
        return "unsolved_goals"
    if status is VerificationStatus.ERROR:
        return "verifier_error"
    return "rejected"


def _task_index(tasks: tuple[BenchmarkTask, ...]) -> dict[str, BenchmarkTask]:
    task_by_id: dict[str, BenchmarkTask] = {}
    for task in tasks:
        if task.task_id in task_by_id:
            raise ValueError(f"duplicate benchmark task id: {task.task_id}")
        task_by_id[task.task_id] = task
    return task_by_id


def _phase_for_task(task: BenchmarkTask) -> str:
    tags = set(task.domain_tags)
    if tags & {"theorem_hole", "multi_goal"}:
        return "P5"
    if tags & {
        "aipw",
        "ate",
        "causal_bridge",
        "causal_identification",
        "double_robust",
        "hajek_ipw",
        "influence_function",
        "ipw",
        "neyman_orthogonality",
        "orthogonal_score",
        "potential_outcomes",
        "product_rate",
        "second_order_remainder",
        "semiparametric",
    }:
        return "P4"
    if tags & {
        "argmin_consistency",
        "asymptotic_bridge",
        "asymptotic_linearity",
        "asymptotic_normality",
        "asymptotic_scaling",
        "bridge",
        "clt",
        "delta_method",
        "estimator_transformation",
        "m_estimation",
        "slutsky",
        "z_estimation",
    }:
        return "P3"
    if tags & {
        "covering_number",
        "donsker",
        "empirical_average",
        "empirical_process",
        "empirical_risk",
        "finite_class_gc",
        "finite_union",
        "glivenko_cantelli",
        "notation",
        "projection",
        "rademacher_complexity",
        "uniform_deviation",
    }:
        return "P2"
    if tags & {
        "asymptotic_calculus",
        "convergence",
        "erm_consistency",
        "estimator_algebra",
        "estimator_interface",
        "probability_convergence",
        "ratio_estimator",
        "weak_convergence",
    }:
        return "P1"
    return "unmapped"


def _allowed_placeholders_by_task(tasks: tuple[BenchmarkTask, ...]) -> dict[str, tuple[str, ...]]:
    return {task.task_id: ("sorry",) if task.lean_task.allowed_sorry else () for task in tasks}


def _rows(label: str, buckets: Mapping[str, _SummaryBucket]) -> list[dict[str, object]]:
    rows = []
    for key in sorted(buckets):
        rows.append({label: key, **buckets[key].to_row()})
    return rows


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


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
