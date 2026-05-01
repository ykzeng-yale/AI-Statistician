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
