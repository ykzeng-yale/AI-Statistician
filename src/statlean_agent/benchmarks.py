"""Benchmark database utilities."""

from __future__ import annotations

from pathlib import Path

from statlean_agent.contracts import BenchmarkSplit, BenchmarkTask, BenchmarkTaskType, LeanTask
from statlean_agent.serialization import dataclass_from_dict, read_jsonl, write_jsonl


SEED_BENCHMARKS: tuple[BenchmarkTask, ...] = (
    BenchmarkTask(
        task_id="erm_oracle_ineq_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("erm_consistency", "asymptotic_calculus"),
        natural_language="Prove the deterministic ERM oracle inequality from a uniform deviation bound.",
        lean_task=LeanTask(
            task_id="erm_oracle_ineq_seed",
            imports=("StatInference.Asymptotics.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {I : Type*} (R Rn : I -> Real) (fhat f : I) "
                "(eps delta : Real) "
                "(h_uniform : forall g, |Rn g - R g| <= delta) "
                "(h_erm : Rn fhat <= Rn f + eps) : "
                "R fhat <= R f + 2 * delta + eps := by\n"
                "  exact StatInference.oracle_ineq_of_uniform_deviation "
                "R Rn fhat f eps delta h_uniform h_erm"
            ),
            tags=("oracle_inequality", "uniform_deviation"),
            dependencies=("StatInference.oracle_ineq_of_uniform_deviation",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.oracle_ineq_of_uniform_deviation",),
    ),
    BenchmarkTask(
        task_id="erm_excess_risk_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("erm_consistency", "asymptotic_calculus"),
        natural_language="Prove the excess-risk form of the deterministic ERM oracle inequality.",
        lean_task=LeanTask(
            task_id="erm_excess_risk_seed",
            imports=("StatInference.Asymptotics.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {I : Type*} (R Rn : I -> Real) (fhat f : I) "
                "(eps delta : Real) "
                "(h_uniform : forall g, |Rn g - R g| <= delta) "
                "(h_erm : Rn fhat <= Rn f + eps) : "
                "R fhat - R f <= 2 * delta + eps := by\n"
                "  exact StatInference.excess_risk_bound_of_uniform_deviation "
                "R Rn fhat f eps delta h_uniform h_erm"
            ),
            tags=("oracle_inequality", "excess_risk"),
            dependencies=("StatInference.excess_risk_bound_of_uniform_deviation",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.excess_risk_bound_of_uniform_deviation",),
    ),
    BenchmarkTask(
        task_id="erm_sequence_excess_bound_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("erm_consistency", "asymptotic_calculus"),
        natural_language="Lift the deterministic ERM excess-risk bound to a sequence of empirical risks.",
        lean_task=LeanTask(
            task_id="erm_sequence_excess_bound_seed",
            imports=("StatInference.Asymptotics.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {I : Type*} (R : I -> Real) (Rn : Nat -> I -> Real) "
                "(fhat : Nat -> I) (f : I) (eps delta : Nat -> Real) "
                "(h_uniform : forall n g, |Rn n g - R g| <= delta n) "
                "(h_erm : forall n, Rn n (fhat n) <= Rn n f + eps n) : "
                "forall n, R (fhat n) - R f <= 2 * delta n + eps n := by\n"
                "  exact StatInference.oracle_excess_sequence_bound "
                "R Rn fhat f eps delta h_uniform h_erm"
            ),
            tags=("oracle_inequality", "sequence_bound", "excess_risk"),
            dependencies=("StatInference.oracle_excess_sequence_bound",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.oracle_excess_sequence_bound",),
    ),
    BenchmarkTask(
        task_id="oracle_bound_tendsto_zero_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("erm_consistency", "asymptotic_calculus", "convergence"),
        natural_language="Show the deterministic ERM oracle bound converges to zero when both components do.",
        lean_task=LeanTask(
            task_id="oracle_bound_tendsto_zero_seed",
            imports=("StatInference.Asymptotics.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (eps delta : Nat -> Real) "
                "(h_delta : Tendsto delta atTop (nhds 0)) "
                "(h_eps : Tendsto eps atTop (nhds 0)) : "
                "Tendsto (fun n => 2 * delta n + eps n) atTop (nhds 0) := by\n"
                "  exact StatInference.oracle_bound_tendsto_zero eps delta h_delta h_eps"
            ),
            tags=("oracle_inequality", "tendsto", "convergence"),
            dependencies=("StatInference.oracle_bound_tendsto_zero",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.oracle_bound_tendsto_zero",),
    ),
    BenchmarkTask(
        task_id="asymptotic_bridge_projection",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("asymptotic_normality",),
        natural_language="Apply the abstract asymptotic-normality bridge once assumptions are supplied.",
        lean_task=LeanTask(
            task_id="asymptotic_bridge_projection",
            imports=("StatInference.Asymptotics.AsymptoticNormal",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (b : StatInference.AsymptoticNormalityBridge) "
                "(hal : b.asymptotic_linear) "
                "(hclt : b.clt_for_linear_part) "
                "(hrem : b.negligible_remainder) : "
                "b.asymptotic_normality := by\n"
                "  exact StatInference.asymptotic_normality_of_bridge b hal hclt hrem"
            ),
            tags=("asymptotic_normality", "bridge"),
            dependencies=("StatInference.asymptotic_normality_of_bridge",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.asymptotic_normality_of_bridge",),
    ),
    BenchmarkTask(
        task_id="causal_identification_bridge_projection",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("causal_identification",),
        natural_language="Apply the abstract ATE identification bridge from overlap and unconfoundedness.",
        lean_task=LeanTask(
            task_id="causal_identification_bridge_projection",
            imports=("StatInference.Causal.PotentialOutcomes",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (b : StatInference.ATEIdentificationBridge) "
                "(hoverlap : b.overlap.statement) "
                "(hunconf : b.unconfoundedness.statement) : "
                "b.identification := by\n"
                "  exact StatInference.ate_identification_of_bridge b hoverlap hunconf"
            ),
            tags=("causal_identification", "bridge"),
            dependencies=("StatInference.ate_identification_of_bridge",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.ate_identification_of_bridge",),
    ),
)


def seed_benchmarks(path: Path) -> None:
    """Write seed benchmark tasks to a JSONL file."""

    write_jsonl(path, list(SEED_BENCHMARKS))


def load_benchmarks(path: Path) -> tuple[BenchmarkTask, ...]:
    """Load benchmark tasks from JSONL."""

    return tuple(dataclass_from_dict(BenchmarkTask, record) for record in read_jsonl(path))


def filter_by_split(tasks: tuple[BenchmarkTask, ...], split: BenchmarkSplit) -> tuple[BenchmarkTask, ...]:
    """Filter benchmark tasks by split."""

    return tuple(task for task in tasks if task.split == split)
