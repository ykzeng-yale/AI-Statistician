"""Benchmark evaluation helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

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

DEFAULT_REPRODUCIBILITY_ARTIFACTS = (
    "config/statlean_blueprint.json",
    "benchmarks/seeds.jsonl",
    "artifacts/verification/benchmark-seed-reports.jsonl",
    "artifacts/evaluation/benchmark-seed-attempts.jsonl",
    "artifacts/evaluation/benchmark-seed-summary.json",
    "artifacts/evaluation/heldout-baseline.json",
    "artifacts/evaluation/paper-quality-heldout.json",
    "artifacts/evaluation/concrete-estimator-chain.json",
    "artifacts/evaluation/ablation-report.json",
    "artifacts/evaluation/external-baseline-plan.json",
    "artifacts/evaluation/external-baseline-results.json",
    "artifacts/evaluation/empirical-process-targets.json",
    "artifacts/training/manifest.json",
    "artifacts/training/dpo-negative-attempts.jsonl",
    "artifacts/training/dpo-negative-reports.jsonl",
    "artifacts/training/grpo-process-tasks.jsonl",
    "artifacts/curation/theorem-hole-ledger.jsonl",
    "artifacts/curation/lemma-proposals.jsonl",
    "artifacts/curation/theorem-hole-promotion-queue.json",
    "artifacts/curation/lemma-proposal-gates.jsonl",
    "artifacts/curation/lemma-non-vacuity.jsonl",
    "artifacts/curation/lemma-proof-cost.jsonl",
    "docs/paper_draft.md",
)

DEFAULT_EMPIRICAL_PROCESS_EXPANSION_TARGETS = (
    {
        "target_id": "bracketing_gc_interface",
        "interface_family": "bracketing",
        "status": "interface_scoped",
        "lean_module": "StatInference.EmpiricalProcess.Complexity",
        "lean_declarations": (
            "StatInference.BracketingNumberSpec",
            "StatInference.BracketingDeviationCertificate",
            "StatInference.BracketingDeviationCertificate.toGlivenkoCantelliClass",
            "StatInference.BracketingDeviationCertificate.uniformDeviation",
        ),
        "depends_on": (
            "StatInference.EmpiricalDeviationSequenceOn",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_tags": ("empirical_process", "glivenko_cantelli"),
        "next_lemma_candidates": (
            "bracketing_entropy_to_uniform_deviation",
            "finite_bracketing_number_to_gc_class",
        ),
    },
    {
        "target_id": "vc_subgraph_gc_interface",
        "interface_family": "vc_subgraph",
        "status": "interface_scoped",
        "lean_module": "StatInference.EmpiricalProcess.VCSubgraph",
        "lean_declarations": (
            "StatInference.VCSubgraphSpec",
            "StatInference.VCDeviationCertificate",
            "StatInference.VCDeviationCertificate.toGlivenkoCantelliClass",
            "StatInference.VCDeviationCertificate.uniformDeviation",
            "StatInference.VCSubgraphProofObligations",
            "StatInference.VCSubgraphGCRoute",
            "StatInference.VCSubgraphGCRoute.toVCDeviationCertificate",
            "StatInference.VCSubgraphGCRoute.toGlivenkoCantelliClass",
        ),
        "depends_on": (
            "StatInference.EmpiricalDeviationSequenceOn",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_tags": ("empirical_process", "vc_subgraph", "glivenko_cantelli"),
        "next_lemma_candidates": (
            "vc_subgraph_shatter_bound_to_uniform_deviation",
            "vc_subgraph_bounded_envelope_to_gc_class",
        ),
    },
    {
        "target_id": "donsker_bridge_interface",
        "interface_family": "donsker",
        "status": "interface_scoped",
        "lean_module": "StatInference.EmpiricalProcess.Complexity",
        "lean_declarations": (
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerBridgeCertificate.toGlivenkoCantelliClass",
            "StatInference.DonskerBridgeCertificate.weakConvergence",
        ),
        "depends_on": (
            "StatInference.GlivenkoCantelliClass",
            "StatInference.DonskerSpec",
        ),
        "benchmark_tags": ("empirical_process", "donsker"),
        "next_lemma_candidates": (
            "asymptotic_equipartition_to_donsker_bridge",
            "donsker_bridge_to_statistical_inference_clt_route",
        ),
    },
    {
        "target_id": "covering_number_gc_interface",
        "interface_family": "covering_number",
        "status": "implemented_seed_interface",
        "lean_module": "StatInference.EmpiricalProcess.Complexity",
        "lean_declarations": (
            "StatInference.CoveringNumberSpec",
            "StatInference.CoveringNumberDeviationCertificate",
            "StatInference.CoveringNumberDeviationCertificate.toGlivenkoCantelliClass",
        ),
        "depends_on": (
            "StatInference.EmpiricalDeviationSequenceOn",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_tags": ("empirical_process", "covering_number", "glivenko_cantelli"),
        "next_lemma_candidates": (
            "covering_entropy_to_uniform_deviation",
            "covering_certificate_non_vacuity_examples",
        ),
    },
    {
        "target_id": "rademacher_gc_interface",
        "interface_family": "rademacher_complexity",
        "status": "implemented_seed_interface",
        "lean_module": "StatInference.EmpiricalProcess.Complexity",
        "lean_declarations": (
            "StatInference.RademacherComplexitySpec",
            "StatInference.RademacherDeviationCertificate",
            "StatInference.RademacherDeviationCertificate.toGlivenkoCantelliClass",
            "StatInference.RademacherDeviationCertificate.radius_tendsto_zero",
        ),
        "depends_on": (
            "StatInference.EmpiricalDeviationSequenceOn",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_tags": (
            "empirical_process",
            "rademacher_complexity",
            "glivenko_cantelli",
        ),
        "next_lemma_candidates": (
            "symmetrization_to_rademacher_deviation",
            "rademacher_certificate_non_vacuity_examples",
        ),
    },
)

DEFAULT_EXTERNAL_BASELINES = (
    {
        "baseline_id": "seed-registry",
        "display_name": "Checked-in seed registry proof render",
        "runner_type": "local_oracle",
        "status": "ready",
        "requires": (),
        "command_template": (
            "statlean materialize-benchmark-attempts --benchmarks {benchmarks} --output {attempts} "
            "--agent-key seed-registry && statlean verify-attempts --attempts {attempts} "
            "--output {reports} --benchmarks {benchmarks}"
        ),
    },
    {
        "baseline_id": "reprover-byt5",
        "display_name": "LeanDojo/ReProver retrieval-augmented tactic model",
        "runner_type": "external_model",
        "status": "requires_model_setup",
        "requires": ("LeanDojo/ReProver runtime", "model checkpoint", "premise index adapter"),
        "command_template": "external-runner reprover --benchmarks {benchmarks} --split {split} --output {attempts}",
    },
    {
        "baseline_id": "deepseek-prover-v2-7b",
        "display_name": "DeepSeek-Prover-V2 7B whole-proof generator",
        "runner_type": "external_model",
        "status": "requires_model_setup",
        "requires": ("model weights or endpoint", "GPU or hosted inference", "whole-proof adapter"),
        "command_template": "external-runner deepseek-prover-v2 --benchmarks {benchmarks} --split {split} --output {attempts}",
    },
    {
        "baseline_id": "kimina-prover-rl-1.7b",
        "display_name": "Kimina-Prover RL 1.7B whole-proof generator",
        "runner_type": "external_model",
        "status": "requires_model_setup",
        "requires": ("model weights or endpoint", "Kimina Lean Server optional", "whole-proof adapter"),
        "command_template": "external-runner kimina-prover --benchmarks {benchmarks} --split {split} --output {attempts}",
    },
    {
        "baseline_id": "general-llm-codex",
        "display_name": "General coding-agent Lean proof baseline",
        "runner_type": "agentic_llm",
        "status": "requires_harness",
        "requires": ("agent harness", "timeout policy", "attempt capture adapter"),
        "command_template": "external-runner codex --benchmarks {benchmarks} --split {split} --output {attempts}",
    },
)

DEFAULT_REPRODUCIBILITY_COMMANDS = (
    {
        "name": "python_tests",
        "command": "PYTHONPATH=src .venv/bin/python -m pytest",
        "purpose": "Run the complete Python test suite.",
    },
    {
        "name": "smoke",
        "command": "PYTHON=.venv/bin/python bash scripts/smoke.sh",
        "purpose": "Run deterministic benchmark, premise-index, manifest, and blueprint smoke checks.",
    },
    {
        "name": "lean_build",
        "command": "lake build",
        "purpose": "Compile the Lean StatInference library and benchmark modules.",
    },
    {
        "name": "blueprint_status",
        "command": "PYTHONPATH=src .venv/bin/python -m statlean_agent.cli blueprint-status --blueprint config/statlean_blueprint.json",
        "purpose": "Confirm the executable build blueprint status.",
    },
    {
        "name": "forbidden_lean_shortcuts",
        "command": "rg -n \"\\b(sorry|admit|unsafe)\\b|^\\s*axiom\\b\" StatInference -g '*.lean'",
        "purpose": "Fail if promoted Lean sources contain forbidden proof shortcuts.",
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


def build_ablation_report(
    tasks: tuple[BenchmarkTask, ...],
    paper_heldout: Mapping[str, object],
    concrete_chain: Mapping[str, object],
    training_manifest: Mapping[str, object],
    grpo_tasks: tuple[Mapping[str, object], ...],
    dpo_reports: tuple[Mapping[str, object], ...],
    lemma_proposal_gates: tuple[Mapping[str, object], ...],
    lemma_non_vacuity: tuple[Mapping[str, object], ...],
    lemma_proof_cost: tuple[Mapping[str, object], ...],
    lemma_ledger: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    """Build an artifact-backed ablation readiness report.

    This is intentionally a system-evidence ablation scaffold, not a trained
    model performance claim. It records whether each component needed for the
    P8 ablation is present, auditable, and backed by checked-in artifacts.
    """

    baseline_comparison = _mapping(paper_heldout.get("baseline_comparison"))
    mean_premise_recall = _float(baseline_comparison.get("mean_premise_recall"))
    heldout_pass_rate = _float(paper_heldout.get("heldout_pass_rate"))
    concrete_chain_passed = bool(concrete_chain.get("passed"))
    sft_examples = _sequence(training_manifest.get("sft_examples"))
    dpo_pairs = _sequence(training_manifest.get("dpo_pairs"))
    manifest_grpo_tasks = _sequence(training_manifest.get("grpo_tasks"))
    rejected_dpo_reports = sum(1 for report in dpo_reports if report.get("status") == "rejected")
    reward_components = sorted(
        {
            str(component)
            for task in grpo_tasks
            for component in _sequence(task.get("reward_components"))
        }
    )
    static_passed = sum(1 for report in lemma_proposal_gates if bool(report.get("passed")))
    non_vacuity_passed = sum(1 for report in lemma_non_vacuity if bool(report.get("passed")))
    proof_cost_passed = sum(1 for report in lemma_proof_cost if bool(report.get("passed")))
    blocked_placeholder_entries = sum(
        1 for entry in lemma_ledger if entry.get("status") == "blocked_placeholder"
    )
    curation_gate_count = (
        len(lemma_proposal_gates)
        + len(lemma_non_vacuity)
        + len(lemma_proof_cost)
    )
    curation_gate_passed = static_passed + non_vacuity_passed + proof_cost_passed

    components = [
        _ablation_component(
            "retrieval",
            mean_premise_recall,
            (
                f"held-out baseline mean premise recall is {mean_premise_recall:.3f} "
                "from expected-premise usage rows"
            ),
            "without retrieval evidence, expected local-stat lemma recall is not audited",
            mean_premise_recall > 0.0,
        ),
        _ablation_component(
            "sft",
            len(sft_examples),
            f"{len(sft_examples)} verified no-placeholder SFT examples are present in the manifest",
            "without SFT examples, the system has no domain-adaptation trace data",
            len(sft_examples) > 0,
        ),
        _ablation_component(
            "dpo",
            len(dpo_pairs),
            (
                f"{len(dpo_pairs)} chosen/rejected DPO pairs are present; "
                f"{rejected_dpo_reports} rejected attempts are Lean-labeled"
            ),
            "without DPO pairs, the prover lacks Lean-labeled contrast against invalid premises",
            len(dpo_pairs) > 0 and rejected_dpo_reports > 0,
        ),
        _ablation_component(
            "process_reward",
            len(grpo_tasks),
            (
                f"{len(grpo_tasks)} GRPO process-reward tasks expose "
                f"{len(reward_components)} reward components"
            ),
            "without process rewards, training falls back to sparse proof-complete feedback only",
            len(grpo_tasks) > 0 and "proof_complete" in reward_components,
        ),
        _ablation_component(
            "curation",
            curation_gate_passed,
            (
                f"{curation_gate_passed}/{curation_gate_count} proposal, non-vacuity, "
                f"and proof-cost gates pass; {blocked_placeholder_entries} placeholder-ledger "
                "entries remain blocked from library promotion"
            ),
            "without curation, generated lemmas could bypass duplicate, non-vacuity, or reuse checks",
            curation_gate_count > 0 and curation_gate_passed == curation_gate_count,
        ),
    ]
    full_system_ready = (
        heldout_pass_rate == 1.0
        and concrete_chain_passed
        and all(component["ready"] for component in components)
    )

    ablation_rows = [
        {
            "variant": "full_system",
            "status": "ready" if full_system_ready else "blocked",
            "expected_effect": (
                "all current P8 evidence is present and auditable"
                if full_system_ready
                else "one or more evidence components is missing"
            ),
            "removed_component": None,
            "primary_metric": heldout_pass_rate,
        }
    ]
    for component in components:
        ablation_rows.append(
            {
                "variant": f"no_{component['component']}",
                "status": "degraded",
                "expected_effect": component["disabled_effect"],
                "removed_component": component["component"],
                "primary_metric": 0.0,
            }
        )

    return {
        "report_id": "ablation::p8",
        "baseline": str(paper_heldout.get("baseline", "unknown")),
        "benchmark_task_count": len(tasks),
        "heldout_pass_rate": heldout_pass_rate,
        "concrete_chain_passed": concrete_chain_passed,
        "full_system_ready": full_system_ready,
        "components": components,
        "ablation_rows": ablation_rows,
        "evidence_summary": {
            "mean_premise_recall": mean_premise_recall,
            "sft_example_count": len(sft_examples),
            "dpo_pair_count": len(dpo_pairs),
            "dpo_rejected_report_count": rejected_dpo_reports,
            "grpo_process_task_count": len(grpo_tasks),
            "manifest_grpo_task_count": len(manifest_grpo_tasks),
            "process_reward_components": reward_components,
            "curation_gate_count": curation_gate_count,
            "curation_gate_passed": curation_gate_passed,
            "blocked_placeholder_ledger_entries": blocked_placeholder_entries,
        },
        "notes": (
            "P8.M3 report: artifact-backed ablation readiness for retrieval, SFT, "
            "DPO, Lean process reward, and curation. This is an auditable system "
            "component ablation scaffold, not a trained-model performance claim."
        ),
    }


def build_reproducibility_bundle(
    repo_root: Path,
    blueprint_report: Mapping[str, object],
    *,
    artifact_paths: tuple[str, ...] = DEFAULT_REPRODUCIBILITY_ARTIFACTS,
    validation_commands: tuple[Mapping[str, str], ...] = DEFAULT_REPRODUCIBILITY_COMMANDS,
    paper_draft_path: str = "docs/paper_draft.md",
) -> dict[str, object]:
    """Build a paper-facing reproducibility bundle with artifact hashes."""

    root = repo_root.resolve()
    artifact_records = [
        _artifact_record(root, artifact_path)
        for artifact_path in artifact_paths
    ]
    phase = _mapping(blueprint_report.get("current_phase"))
    milestone = _mapping(blueprint_report.get("current_milestone"))
    done_phase_count = int(blueprint_report.get("done_phase_count", 0))
    phase_count = int(blueprint_report.get("phase_count", 0))
    all_phases_done = phase_count > 0 and done_phase_count == phase_count

    return {
        "report_id": "reproducibility::p8",
        "blueprint_id": str(blueprint_report.get("blueprint_id", "")),
        "blueprint_title": str(blueprint_report.get("title", "")),
        "phase_count": phase_count,
        "done_phase_count": done_phase_count,
        "all_phases_done": all_phases_done,
        "current_phase": dict(phase),
        "current_milestone": dict(milestone) if milestone else None,
        "paper_draft_path": paper_draft_path,
        "artifact_count": len(artifact_records),
        "artifacts": artifact_records,
        "validation_commands": [dict(command) for command in validation_commands],
        "reproduction_order": [
            "Install Python development dependencies with pip install -e \".[dev]\".",
            "Run the validation_commands in order from this report.",
            "Compare artifact sha256 values against the artifacts table.",
            "Use docs/paper_draft.md as the paper narrative tied to these artifacts.",
            "Use config/statlean_blueprint.json as the executable progress contract.",
        ],
        "guardrails": [
            "No promoted StatInference theorem may rely on forbidden proof shortcuts.",
            "Training artifacts are preparation data, not evidence of a trained model improvement.",
            "Ablation rows are system-component readiness ablations, not a model-performance claim.",
            "Statistical semantics and new theorem statements still require human review.",
        ],
        "notes": (
            "P8.M4 reproducibility bundle: hash-pinned artifacts, executable "
            "validation commands, paper draft linkage, and explicit guardrails."
        ),
    }


def build_external_baseline_plan(
    tasks: tuple[BenchmarkTask, ...],
    *,
    split: str = "test",
    baseline_specs: tuple[Mapping[str, object], ...] = DEFAULT_EXTERNAL_BASELINES,
    benchmark_path: str = "benchmarks/seeds.jsonl",
    output_dir: str = "artifacts/external_baselines",
) -> dict[str, object]:
    """Build a concrete run plan for post-P8 external prover baselines."""

    split_tasks = tuple(task for task in tasks if _enum_value(task.split) == split)
    if not split_tasks:
        raise ValueError(f"no benchmark tasks found for split `{split}`")

    theorem_hole_tasks = tuple(task for task in tasks if task.lean_task.allowed_sorry)
    domain_tags = sorted({tag for task in split_tasks for tag in task.domain_tags})
    baselines = [
        _external_baseline_row(
            spec,
            split=split,
            benchmark_path=benchmark_path,
            output_dir=output_dir,
            task_count=len(split_tasks),
        )
        for spec in baseline_specs
    ]
    ready_count = sum(1 for baseline in baselines if baseline["status"] == "ready")

    return {
        "report_id": f"external-baseline-plan::{split}",
        "split": split,
        "benchmark_path": benchmark_path,
        "benchmark_task_count": len(tasks),
        "target_task_count": len(split_tasks),
        "target_task_ids": [task.task_id for task in split_tasks],
        "target_domain_tags": domain_tags,
        "theorem_hole_task_count": len(theorem_hole_tasks),
        "theorem_hole_task_ids": [task.task_id for task in theorem_hole_tasks],
        "baseline_count": len(baselines),
        "ready_baseline_count": ready_count,
        "blocked_baseline_count": len(baselines) - ready_count,
        "baselines": baselines,
        "metrics": [
            "pass_at_1",
            "pass_at_8",
            "pass_at_32",
            "valid_tactic_rate",
            "mean_premise_recall",
            "unknown_identifier_rate",
            "timeout_rate",
            "mean_wall_time_seconds",
        ],
        "promotion_gate": (
            "An external baseline row is reportable only after attempts are captured "
            "as ProofAttempt JSONL, verified by the local Lake verifier, and summarized "
            "with the same failure taxonomy as the seed-registry baseline."
        ),
        "notes": (
            "P9.M1 plan: external prover baselines are specified as reproducible run "
            "targets. Only seed-registry is currently ready; model baselines remain "
            "blocked until their adapters and credentials/checkpoints are available."
        ),
    }


def build_external_baseline_results(
    tasks: tuple[BenchmarkTask, ...],
    plan: Mapping[str, object],
    attempts_by_baseline: Mapping[str, tuple[ProofAttempt, ...]],
    reports_by_baseline: Mapping[str, tuple[VerificationReport, ...]],
    *,
    source_by_baseline: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Normalize available external baseline results against the planned split."""

    split = str(plan.get("split", "test"))
    baselines = tuple(_mapping(row) for row in plan.get("baselines", ()))
    source_by_baseline = source_by_baseline or {}
    rows = [
        _external_baseline_result_row(
            tasks,
            baseline,
            split=split,
            attempts=attempts_by_baseline.get(str(baseline.get("baseline_id", ""))),
            reports=reports_by_baseline.get(str(baseline.get("baseline_id", ""))),
            source=source_by_baseline.get(str(baseline.get("baseline_id", "")), "missing"),
        )
        for baseline in baselines
    ]
    ingested_rows = [row for row in rows if row["ingestion_status"] == "ingested"]
    blocked_rows = [row for row in rows if row["ingestion_status"] != "ingested"]
    best = max(
        ingested_rows,
        key=lambda row: (
            float(row["pass_rate"]),
            float(row["mean_premise_recall"]),
            str(row["baseline_id"]),
        ),
        default=None,
    )

    return {
        "report_id": f"external-baseline-results::{split}",
        "plan_report_id": str(plan.get("report_id", "")),
        "split": split,
        "baseline_count": len(rows),
        "ingested_count": len(ingested_rows),
        "blocked_count": len(blocked_rows),
        "best_available_baseline": best["baseline_id"] if best else None,
        "rows": rows,
        "comparison_policy": (
            "Each external baseline must provide ProofAttempt and VerificationReport "
            "JSONL records over the planned split. Results are compared with "
            "compare_baseline_on_split, so policy violations, premise recall, "
            "failure taxonomy, and effective pass rate match the seed-registry "
            "evaluation path."
        ),
        "notes": (
            "P9.M3 ingestion: seed-registry is ingested from checked-in verifier "
            "artifacts when planned external-baseline files are not present; model "
            "baselines remain blocked until adapters produce attempt/report JSONL."
        ),
    }


def build_empirical_process_expansion_targets(
    tasks: tuple[BenchmarkTask, ...],
    *,
    target_specs: tuple[Mapping[str, object], ...] = DEFAULT_EMPIRICAL_PROCESS_EXPANSION_TARGETS,
) -> dict[str, object]:
    """Build the P9 empirical-process expansion target map.

    The artifact records scoped Lean interfaces and next theorem targets.  It is
    deliberately not a performance claim: bracketing, VC, and Donsker rows are
    accepted only as proof-carrying interface targets until downstream theorems
    and non-vacuity examples are added.
    """

    task_ids_by_tag = _task_ids_by_tag(tasks)
    rows = [
        _empirical_process_target_row(spec, task_ids_by_tag)
        for spec in target_specs
    ]
    scoped_rows = [
        row for row in rows
        if row["status"] in {"interface_scoped", "implemented_seed_interface"}
    ]
    pending_rows = [row for row in rows if row["status"] == "pending"]

    return {
        "report_id": "empirical-process-targets::p9",
        "target_count": len(rows),
        "scoped_count": len(scoped_rows),
        "pending_count": len(pending_rows),
        "benchmark_task_ids_by_tag": {
            tag: task_ids_by_tag[tag]
            for tag in sorted(task_ids_by_tag)
            if tag in {
                "bracketing_number",
                "covering_number",
                "donsker",
                "empirical_process",
                "glivenko_cantelli",
                "rademacher_complexity",
                "vc_subgraph",
            }
        },
        "targets": rows,
        "acceptance_gates": [
            "Lean module compiles with no sorry/admit/unsafe/axiom in promoted StatInference sources.",
            "Every interface remains proof-carrying: no entropy, VC, or Donsker theorem is asserted without a supplied proof field.",
            "At least one benchmark seed or theorem-hole target cites each active interface family before claiming model-evaluation coverage.",
            "Each promoted empirical-process theorem must include a non-vacuity example or concrete satisfying certificate.",
            "Human statistical review is required before replacing abstract interface fields with primitive theorem statements.",
        ],
        "notes": (
            "P9.M4 scopes the next empirical-process layer around bracketing, "
            "VC-subgraph, and Donsker proof-carrying interfaces, while retaining "
            "the already implemented covering-number and Rademacher seed routes."
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
        "bracketing_number",
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
        "vc_subgraph",
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


def _ablation_component(
    component: str,
    enabled_metric: float | int,
    enabled_evidence: str,
    disabled_effect: str,
    ready: bool,
) -> dict[str, object]:
    return {
        "component": component,
        "ready": ready,
        "enabled_metric": enabled_metric,
        "enabled_evidence": enabled_evidence,
        "disabled_effect": disabled_effect,
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _artifact_record(repo_root: Path, relative_path: str) -> dict[str, object]:
    path = repo_root / relative_path
    if not path.exists():
        raise ValueError(f"missing reproducibility artifact: {relative_path}")
    payload = path.read_bytes()
    text = payload.decode("utf-8")
    return {
        "path": relative_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_count": len(payload),
        "line_count": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
    }


def _task_ids_by_tag(tasks: tuple[BenchmarkTask, ...]) -> dict[str, list[str]]:
    task_ids_by_tag: dict[str, list[str]] = {}
    for task in tasks:
        for tag in task.domain_tags:
            task_ids_by_tag.setdefault(tag, []).append(task.task_id)
    return {tag: sorted(task_ids) for tag, task_ids in task_ids_by_tag.items()}


def _empirical_process_target_row(
    spec: Mapping[str, object],
    task_ids_by_tag: Mapping[str, list[str]],
) -> dict[str, object]:
    benchmark_tags = tuple(str(tag) for tag in _sequence(spec.get("benchmark_tags")))
    interface_family = str(spec["interface_family"])
    family_tags = _empirical_process_family_tags(interface_family)
    motivating_task_ids = sorted({
        task_id
        for tag in benchmark_tags
        for task_id in task_ids_by_tag.get(tag, [])
    })
    family_benchmark_task_ids = sorted({
        task_id
        for tag in family_tags
        for task_id in task_ids_by_tag.get(tag, [])
    })
    return {
        "target_id": str(spec["target_id"]),
        "interface_family": interface_family,
        "status": str(spec["status"]),
        "lean_module": str(spec["lean_module"]),
        "lean_declarations": [
            str(declaration)
            for declaration in _sequence(spec.get("lean_declarations"))
        ],
        "depends_on": [
            str(dependency)
            for dependency in _sequence(spec.get("depends_on"))
        ],
        "benchmark_tags": list(benchmark_tags),
        "motivating_task_ids": motivating_task_ids,
        "family_benchmark_task_ids": family_benchmark_task_ids,
        "next_lemma_candidates": [
            str(candidate)
            for candidate in _sequence(spec.get("next_lemma_candidates"))
        ],
        "gate_status": (
            "ready_for_lemma_targets"
            if family_benchmark_task_ids
            else "needs_benchmark_seed"
        ),
    }


def _empirical_process_family_tags(interface_family: str) -> tuple[str, ...]:
    if interface_family == "bracketing":
        return ("bracketing_number",)
    if interface_family == "vc_subgraph":
        return ("vc_subgraph",)
    return (interface_family,)


def _external_baseline_row(
    spec: Mapping[str, object],
    *,
    split: str,
    benchmark_path: str,
    output_dir: str,
    task_count: int,
) -> dict[str, object]:
    baseline_id = str(spec["baseline_id"])
    attempts_path = f"{output_dir}/{baseline_id}-{split}-attempts.jsonl"
    reports_path = f"{output_dir}/{baseline_id}-{split}-reports.jsonl"
    summary_path = f"{output_dir}/{baseline_id}-{split}-summary.json"
    command_template = str(spec["command_template"])
    return {
        "baseline_id": baseline_id,
        "display_name": str(spec["display_name"]),
        "runner_type": str(spec["runner_type"]),
        "status": str(spec["status"]),
        "requires": [str(requirement) for requirement in _sequence(spec.get("requires"))],
        "target_task_count": task_count,
        "attempts_path": attempts_path,
        "reports_path": reports_path,
        "summary_path": summary_path,
        "command": command_template.format(
            benchmarks=benchmark_path,
            split=split,
            attempts=attempts_path,
            reports=reports_path,
            summary=summary_path,
        ),
    }


def _external_baseline_result_row(
    tasks: tuple[BenchmarkTask, ...],
    baseline: Mapping[str, object],
    *,
    split: str,
    attempts: tuple[ProofAttempt, ...] | None,
    reports: tuple[VerificationReport, ...] | None,
    source: str,
) -> dict[str, object]:
    baseline_id = str(baseline.get("baseline_id", ""))
    base_row = {
        "baseline_id": baseline_id,
        "display_name": str(baseline.get("display_name", "")),
        "runner_type": str(baseline.get("runner_type", "")),
        "planned_status": str(baseline.get("status", "")),
        "source": source,
        "attempts_path": str(baseline.get("attempts_path", "")),
        "reports_path": str(baseline.get("reports_path", "")),
        "summary_path": str(baseline.get("summary_path", "")),
        "target_task_count": int(baseline.get("target_task_count", 0)),
    }
    if attempts is None or reports is None:
        missing = []
        if attempts is None:
            missing.append(str(baseline.get("attempts_path", "")))
        if reports is None:
            missing.append(str(baseline.get("reports_path", "")))
        planned_status = str(baseline.get("status", ""))
        ingestion_status = (
            "blocked_missing_results"
            if planned_status == "ready"
            else "blocked_by_plan_status"
        )
        return {
            **base_row,
            "ingestion_status": ingestion_status,
            "evaluated_task_count": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "mean_reward": 0.0,
            "mean_premise_recall": 0.0,
            "status_counts": _empty_status_counts(),
            "failure_categories": {},
            "blocked_reasons": [
                *(str(requirement) for requirement in _sequence(baseline.get("requires"))),
                *(f"missing result file: {path}" for path in missing if path),
            ],
        }

    try:
        comparison = compare_baseline_on_split(
            tasks,
            attempts,
            reports,
            baseline=baseline_id,
            split=split,
        )
    except ValueError as error:
        return {
            **base_row,
            "ingestion_status": "ingestion_error",
            "evaluated_task_count": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "mean_reward": 0.0,
            "mean_premise_recall": 0.0,
            "status_counts": _empty_status_counts(),
            "failure_categories": {},
            "blocked_reasons": [str(error)],
        }

    return {
        **base_row,
        "ingestion_status": "ingested",
        "evaluated_task_count": int(comparison["benchmark_task_count"]),
        "passed": int(comparison["passed"]),
        "failed": int(comparison["failed"]),
        "pass_rate": float(comparison["pass_rate"]),
        "mean_reward": float(comparison["mean_reward"]),
        "mean_premise_recall": float(comparison["mean_premise_recall"]),
        "status_counts": dict(_mapping(comparison["status_counts"])),
        "failure_categories": dict(_mapping(comparison["failure_categories"])),
        "blocked_reasons": [],
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
