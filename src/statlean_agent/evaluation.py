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


DEFAULT_PAPER_QUALITY_PROOF_CHAINS = (
    {
        "chain_id": "ipw_hajek_linearization_chain",
        "name": "IPW/Hajek identification plus scaled linearization",
        "source_module": "StatInference.Causal.IPW",
        "benchmark_task_ids": (
            "ipw_identification_certificate_seed",
            "ipw_hajek_scaled_linearization_route_seed",
            "constant_ipw_hajek_route_seed",
            "constant_ipw_hajek_exact_target_seed",
            "paper_quality_ipw_hajek_concrete_chain_seed",
        ),
        "required_declarations": (
            "StatInference.IPWHajekLinearizationRoute.identifies",
            "StatInference.IPWHajekLinearizationRoute.scaledLinearization",
            "StatInference.constantIPWHajekLinearizationRoute",
            "StatInference.paperQualityIPWHajekConcreteEstimatorChain",
        ),
    },
    {
        "chain_id": "aipw_product_rate_chain",
        "name": "AIPW double robustness plus orthogonal product-rate remainder",
        "source_module": "StatInference.Causal.AIPW",
        "benchmark_task_ids": (
            "aipw_double_robust_identification_seed",
            "aipw_product_rate_remainder_seed",
            "aipw_orthogonal_score_seed",
            "aipw_second_order_remainder_seed",
            "trivial_aipw_product_rate_route_seed",
        ),
        "required_declarations": (
            "StatInference.AIPWOrthogonalProductRateRoute.identifies",
            "StatInference.AIPWOrthogonalProductRateRoute.secondOrderRemainderSmall",
            "StatInference.trivialAIPWOrthogonalProductRateRoute",
        ),
    },
    {
        "chain_id": "influence_function_normality_chain",
        "name": "Influence-function asymptotic-linearity and normality route",
        "source_module": "StatInference.Semiparametric.Normality",
        "benchmark_task_ids": (
            "influence_function_normality_route_seed",
            "influence_function_normality_bridge_seed",
            "aipw_influence_function_normality_route_seed",
            "trivial_influence_function_normality_seed",
            "trivial_aipw_influence_function_normality_seed",
        ),
        "required_declarations": (
            "StatInference.InfluenceFunctionNormalityRoute.asymptoticLinear",
            "StatInference.InfluenceFunctionNormalityRoute.asymptoticNormal",
            "StatInference.AIPWInfluenceFunctionNormalityRoute.asymptoticNormal",
        ),
    },
)


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


def compare_baseline_on_split(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    baseline: str,
    split: str,
    allowed_placeholders_by_task: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, object]:
    """Build a held-out baseline report from paired attempts and verifier reports."""

    if len(attempts) != len(reports):
        raise ValueError("attempts and reports must have the same length")

    task_by_id = _task_index(tasks)
    split_tasks = tuple(task for task in tasks if _enum_value(task.split) == split)
    if not split_tasks:
        raise ValueError(f"no benchmark tasks found for split `{split}`")

    pairs_by_task: dict[str, tuple[ProofAttempt, VerificationReport]] = {}
    for attempt, report in zip(attempts, reports, strict=True):
        if attempt.agent_key != baseline:
            continue
        if attempt.task_id in pairs_by_task:
            raise ValueError(f"duplicate attempt for baseline `{baseline}` and task `{attempt.task_id}`")
        pairs_by_task[attempt.task_id] = (attempt, report)

    allowed_by_task = _allowed_placeholders_by_task(tasks)
    if allowed_placeholders_by_task is not None:
        allowed_by_task.update({
            task_id: tuple(tokens)
            for task_id, tokens in allowed_placeholders_by_task.items()
        })

    rows: list[dict[str, object]] = []
    status_counts = _empty_status_counts()
    reward_total = 0.0
    premise_recall_total = 0.0
    failure_categories: dict[str, int] = {}

    for task in split_tasks:
        pair = pairs_by_task.get(task.task_id)
        if pair is None:
            raise ValueError(f"missing attempt for baseline `{baseline}` and task `{task.task_id}`")
        attempt, report = pair
        if report.task_id != attempt.task_id:
            raise ValueError(
                f"attempt `{attempt.task_id}` paired with report for `{report.task_id}`"
            )
        if task_by_id.get(attempt.task_id) is None:
            raise ValueError(f"unknown benchmark task id: {attempt.task_id}")

        allowed_placeholders = tuple(allowed_by_task.get(task.task_id, ()))
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
        if failure_category:
            failure_categories[failure_category] = failure_categories.get(failure_category, 0) + 1

        expected_premises = tuple(task.expected_premises)
        premises_used = tuple(attempt.premises_used)
        premise_recall = _premise_recall(expected_premises, premises_used)
        premise_recall_total += premise_recall
        status_counts[effective_status.value] += 1
        reward_total += reward_breakdown.total

        rows.append(
            {
                "task_id": task.task_id,
                "task_type": _enum_value(task.task_type),
                "split": _enum_value(task.split),
                "difficulty": task.difficulty,
                "domain_tags": list(task.domain_tags),
                "agent_key": attempt.agent_key,
                "reported_status": _enum_value(report.status),
                "effective_status": effective_status.value,
                "passed": effective_status is VerificationStatus.ACCEPTED,
                "reward": reward_breakdown.total,
                "reward_components": dict(sorted(reward_breakdown.components.items())),
                "first_error": first_error,
                "failure_category": failure_category,
                "expected_premises": list(expected_premises),
                "premises_used": list(premises_used),
                "premise_recall": premise_recall,
                "allowed_placeholders": list(allowed_placeholders),
            }
        )

    total = len(rows)
    passed = status_counts[VerificationStatus.ACCEPTED.value]
    return {
        "comparison_id": f"{baseline}::{split}",
        "baseline": baseline,
        "split": split,
        "benchmark_task_count": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total if total else 0.0,
        "mean_reward": reward_total / total if total else 0.0,
        "mean_premise_recall": premise_recall_total / total if total else 0.0,
        "status_counts": status_counts,
        "failure_categories": dict(sorted(failure_categories.items())),
        "task_ids": [row["task_id"] for row in rows],
        "rows": rows,
    }


def build_paper_quality_heldout_report(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    baseline: str,
    split: str,
    proof_chains: tuple[Mapping[str, object], ...] = DEFAULT_PAPER_QUALITY_PROOF_CHAINS,
) -> dict[str, object]:
    """Build a paper-facing held-out report with theorem-chain coverage."""

    baseline_report = compare_baseline_on_split(
        tasks,
        attempts,
        reports,
        baseline=baseline,
        split=split,
    )
    chain_reports = [
        _proof_chain_report(chain, tasks, reports)
        for chain in proof_chains
    ]
    chain_count = len(chain_reports)
    chain_passed = sum(1 for report in chain_reports if report["status"] == "passed")
    heldout_domains = tuple(
        sorted({tag for row in baseline_report["rows"] for tag in row["domain_tags"]})
    )

    return {
        "report_id": f"paper-quality::{baseline}::{split}",
        "baseline": baseline,
        "split": split,
        "heldout_task_count": baseline_report["benchmark_task_count"],
        "heldout_pass_rate": baseline_report["pass_rate"],
        "heldout_domains": list(heldout_domains),
        "failure_taxonomy": {
            "failed": baseline_report["failed"],
            "status_counts": baseline_report["status_counts"],
            "failure_categories": baseline_report["failure_categories"],
        },
        "baseline_comparison": baseline_report,
        "non_seed_proof_chains": chain_reports,
        "non_seed_chain_count": chain_count,
        "non_seed_chain_passed": chain_passed,
        "non_seed_chain_pass_rate": chain_passed / chain_count if chain_count else 0.0,
        "notes": (
            "P8.M1 report: held-out baseline rows remain split-based, while "
            "non-seed proof chains audit reusable StatInference theorem routes "
            "that are not themselves benchmark items."
        ),
    }


def build_concrete_estimator_chain_report(
    tasks: tuple[BenchmarkTask, ...],
    reports: tuple[VerificationReport, ...],
    *,
    task_id: str = "paper_quality_ipw_hajek_concrete_chain_seed",
) -> dict[str, object]:
    """Build an auditable report for the concrete estimator proof chain."""

    task_by_id = _task_index(tasks)
    report_by_task = {report.task_id: report for report in reports}
    if task_id not in task_by_id:
        raise ValueError(f"unknown concrete estimator chain task id: {task_id}")

    task = task_by_id[task_id]
    report = report_by_task.get(task_id, VerificationReport(task_id, VerificationStatus.ERROR))
    component_task_ids = (
        "ipw_identification_certificate_seed",
        "ipw_hajek_scaled_linearization_route_seed",
        "constant_ipw_hajek_route_seed",
        "constant_ipw_hajek_exact_target_seed",
    )
    component_reports = [
        _component_report(component_id, task_by_id, report_by_task)
        for component_id in component_task_ids
    ]
    passed_components = sum(1 for component in component_reports if component["status"] == "passed")
    no_placeholder_policy = not task.lean_task.allowed_sorry
    passed = (
        report.status is VerificationStatus.ACCEPTED
        and no_placeholder_policy
        and passed_components == len(component_reports)
    )

    return {
        "report_id": "concrete-estimator-chain::ipw_hajek",
        "chain_id": "ipw_hajek_concrete_estimator_chain",
        "theorem": "StatInference.paperQualityIPWHajekConcreteEstimatorChain",
        "module": "StatInference.Examples.ConcreteEstimatorChain",
        "source_file": "StatInference/Examples/ConcreteEstimatorChain.lean",
        "benchmark_task_id": task_id,
        "verification_status": _enum_value(report.status),
        "passed": passed,
        "no_placeholder_policy": no_placeholder_policy,
        "expected_premises": list(task.expected_premises),
        "proof_components": component_reports,
        "component_count": len(component_reports),
        "component_passed": passed_components,
        "route_declarations": [
            "StatInference.paperQualityIPWHajekRate",
            "StatInference.paperQualityIPWHajekRoute",
            "StatInference.paperQualityIPWHajekConcreteEstimatorChain",
        ],
        "claims_verified": [
            "IPW identification conclusion is available on the concrete route.",
            "The constant Hajek estimator equals the target for every sample size.",
            "The centered numerator residual is zero for every sample size.",
            "The scaled linearization identity holds for every sample size.",
        ],
        "notes": (
            "P8.M2 concrete estimator chain: a single no-sorry Lean theorem "
            "composes the IPW/Hajek route through identification, exact target "
            "recovery, residual control, and scaled linearization."
        ),
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


def _proof_chain_report(
    chain: Mapping[str, object],
    tasks: tuple[BenchmarkTask, ...],
    reports: tuple[VerificationReport, ...],
) -> dict[str, object]:
    task_ids = tuple(str(task_id) for task_id in chain.get("benchmark_task_ids", ()))
    report_by_task = {report.task_id: report for report in reports}
    known_task_ids = {task.task_id for task in tasks}
    accepted_task_ids = tuple(
        task_id
        for task_id in task_ids
        if task_id in known_task_ids
        and report_by_task.get(task_id, VerificationReport(task_id, VerificationStatus.ERROR)).status
        is VerificationStatus.ACCEPTED
    )
    missing_task_ids = tuple(task_id for task_id in task_ids if task_id not in accepted_task_ids)
    pass_rate = len(accepted_task_ids) / len(task_ids) if task_ids else 0.0
    status = "passed" if task_ids and not missing_task_ids else "blocked"
    return {
        "chain_id": str(chain["chain_id"]),
        "name": str(chain["name"]),
        "source_module": str(chain["source_module"]),
        "benchmark_task_ids": list(task_ids),
        "required_declarations": list(chain.get("required_declarations", ())),
        "accepted_task_ids": list(accepted_task_ids),
        "missing_task_ids": list(missing_task_ids),
        "pass_rate": pass_rate,
        "status": status,
    }


def _component_report(
    task_id: str,
    task_by_id: Mapping[str, BenchmarkTask],
    report_by_task: Mapping[str, VerificationReport],
) -> dict[str, object]:
    task = task_by_id.get(task_id)
    report = report_by_task.get(task_id, VerificationReport(task_id, VerificationStatus.ERROR))
    status = "passed" if task is not None and report.status is VerificationStatus.ACCEPTED else "blocked"
    return {
        "task_id": task_id,
        "status": status,
        "verification_status": _enum_value(report.status),
        "expected_premises": list(task.expected_premises) if task is not None else [],
    }


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


def _premise_recall(expected: tuple[str, ...], used: tuple[str, ...]) -> float:
    if not expected:
        return 1.0
    used_set = set(used)
    return sum(1 for premise in expected if premise in used_set) / len(expected)
