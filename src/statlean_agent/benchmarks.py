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
                "(h_delta : Filter.Tendsto delta Filter.atTop (nhds 0)) "
                "(h_eps : Filter.Tendsto eps Filter.atTop (nhds 0)) : "
                "Filter.Tendsto (fun n => 2 * delta n + eps n) Filter.atTop (nhds 0) := by\n"
                "  exact StatInference.oracle_bound_tendsto_zero eps delta h_delta h_eps"
            ),
            tags=("oracle_inequality", "tendsto", "convergence"),
            dependencies=("StatInference.oracle_bound_tendsto_zero",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.oracle_bound_tendsto_zero",),
    ),
    BenchmarkTask(
        task_id="mathlib_probability_to_distribution_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("convergence", "probability_convergence", "weak_convergence"),
        natural_language=(
            "Use the mathlib-backed route from convergence in probability "
            "to convergence in distribution."
        ),
        lean_task=LeanTask(
            task_id="mathlib_probability_to_distribution_seed",
            imports=("StatInference.Asymptotics.Convergence",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {I Omega E : Type*} [MeasurableSpace Omega] [MeasurableSpace E] "
                "[SeminormedAddCommGroup E] [SecondCountableTopology E] [BorelSpace E] "
                "(mu : MeasureTheory.Measure Omega) [MeasureTheory.IsProbabilityMeasure mu] "
                "(X : I -> Omega -> E) (Z : Omega -> E) (l : Filter I) "
                "[l.NeBot] [Filter.IsCountablyGenerated l] "
                "(h : StatInference.MathlibConvergesInProbability mu X l Z) "
                "(hX : forall i, AEMeasurable (X i) mu) : "
                "StatInference.MathlibConvergesInDistribution X l Z (fun _ => mu) mu := by\n"
                "  exact StatInference.mathlib_convergesInDistribution_of_probability h hX"
            ),
            tags=("mathlib_convergence", "convergence_in_probability", "weak_convergence"),
            dependencies=("StatInference.mathlib_convergesInDistribution_of_probability",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.mathlib_convergesInDistribution_of_probability",),
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
        task_id="slutsky_bridge_projection_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("convergence", "slutsky"),
        natural_language="Apply the abstract Slutsky bridge from distributional convergence and a negligible perturbation.",
        lean_task=LeanTask(
            task_id="slutsky_bridge_projection_seed",
            imports=("StatInference.Asymptotics.Convergence",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (b : StatInference.SlutskyBridge) "
                "(hmain : b.main_convergence.statement) "
                "(hsmall : b.perturbation_small.statement) : "
                "b.combined_convergence := by\n"
                "  exact StatInference.convergence_of_slutsky_bridge b hmain hsmall"
            ),
            tags=("slutsky", "convergence", "bridge"),
            dependencies=("StatInference.convergence_of_slutsky_bridge",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.convergence_of_slutsky_bridge",),
    ),
    BenchmarkTask(
        task_id="delta_method_bridge_projection_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S1",
        domain_tags=("convergence", "delta_method"),
        natural_language="Apply the abstract delta-method bridge from linearization, linear-part convergence, and negligible remainder.",
        lean_task=LeanTask(
            task_id="delta_method_bridge_projection_seed",
            imports=("StatInference.Asymptotics.Convergence",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (b : StatInference.DeltaMethodBridge) "
                "(hlin : b.linearization_statement) "
                "(hconv : b.linear_part_convergence.statement) "
                "(hrem : b.remainder_small.statement) : "
                "b.transformed_convergence := by\n"
                "  exact StatInference.convergence_of_delta_method_bridge b hlin hconv hrem"
            ),
            tags=("delta_method", "convergence", "bridge"),
            dependencies=("StatInference.convergence_of_delta_method_bridge",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.convergence_of_delta_method_bridge",),
    ),
    BenchmarkTask(
        task_id="asymptotic_linear_clt_bridge_projection_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S1",
        domain_tags=("asymptotic_normality", "clt", "asymptotic_linearity"),
        natural_language="Apply the central asymptotic-linearity plus CLT bridge.",
        lean_task=LeanTask(
            task_id="asymptotic_linear_clt_bridge_projection_seed",
            imports=("StatInference.Asymptotics.Convergence",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (b : StatInference.AsymptoticLinearCLTBridge) "
                "(hal : b.asymptotic_linear_statement) "
                "(hclt : b.clt.statement) "
                "(hrem : b.negligible_remainder.statement) : "
                "b.asymptotic_normality := by\n"
                "  exact StatInference.asymptotic_normality_of_asymptoticLinear_clt_bridge "
                "b hal hclt hrem"
            ),
            tags=("asymptotic_linearity", "clt", "bridge"),
            dependencies=(
                "StatInference.asymptotic_normality_of_asymptoticLinear_clt_bridge",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.asymptotic_normality_of_asymptoticLinear_clt_bridge",
        ),
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
    BenchmarkTask(
        task_id="erm_sequence_fixed_index_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("erm_consistency", "asymptotic_calculus"),
        natural_language="Specialize the sequence-level ERM excess-risk oracle bound at a fixed sample size.",
        lean_task=LeanTask(
            task_id="erm_sequence_fixed_index_seed",
            imports=("StatInference.Asymptotics.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {I : Type*} (R : I -> Real) (Rn : Nat -> I -> Real) "
                "(fhat : Nat -> I) (f : I) (eps delta : Nat -> Real) (n : Nat) "
                "(h_uniform : forall n g, |Rn n g - R g| <= delta n) "
                "(h_erm : forall n, Rn n (fhat n) <= Rn n f + eps n) : "
                "R (fhat n) - R f <= 2 * delta n + eps n := by\n"
                "  exact StatInference.oracle_excess_sequence_bound "
                "R Rn fhat f eps delta h_uniform h_erm n"
            ),
            tags=("oracle_inequality", "sequence_bound", "fixed_index"),
            dependencies=("StatInference.oracle_excess_sequence_bound",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.oracle_excess_sequence_bound",),
    ),
    BenchmarkTask(
        task_id="erm_zero_deviation_exact_risk_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TEST,
        difficulty="S3",
        domain_tags=("erm_consistency", "asymptotic_calculus"),
        natural_language="Derive exact population-risk optimality when the empirical risk has zero deviation and exact ERM.",
        lean_task=LeanTask(
            task_id="erm_zero_deviation_exact_risk_seed",
            imports=("StatInference.Asymptotics.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {I : Type*} (R Rn : I -> Real) (fhat f : I) "
                "(h_uniform : forall g, |Rn g - R g| <= 0) "
                "(h_erm : Rn fhat <= Rn f) : "
                "R fhat <= R f := by\n"
                "  have h_bound : R fhat <= R f + 2 * (0 : Real) + 0 :=\n"
                "    StatInference.oracle_ineq_of_uniform_deviation "
                "R Rn fhat f 0 0 h_uniform (by simpa using h_erm)\n"
                "  nlinarith"
            ),
            tags=("oracle_inequality", "zero_deviation", "exact_erm"),
            dependencies=("StatInference.oracle_ineq_of_uniform_deviation",),
            expected_patterns=("have", "nlinarith"),
        ),
        expected_premises=("StatInference.oracle_ineq_of_uniform_deviation",),
    ),
    BenchmarkTask(
        task_id="estimator_apply_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("estimator_interface",),
        natural_language="Project the estimate function from a finite-sample estimator interface.",
        lean_task=LeanTask(
            task_id="estimator_apply_seed",
            imports=("StatInference.Estimator.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample Parameter : Type*} "
                "(e : StatInference.Estimator Sample Parameter) (sample : Sample) : "
                "Parameter := by\n"
                "  exact e.estimate sample"
            ),
            tags=("estimator", "projection"),
            dependencies=("StatInference.Estimator.estimate",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.Estimator.estimate",),
    ),
    BenchmarkTask(
        task_id="estimator_sequence_apply_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("estimator_interface",),
        natural_language="Project the indexed estimate function from an estimator-sequence interface.",
        lean_task=LeanTask(
            task_id="estimator_sequence_apply_seed",
            imports=("StatInference.Estimator.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample Parameter : Type*} "
                "(seq : StatInference.EstimatorSequence Sample Parameter) "
                "(n : Nat) (sample : Sample) : "
                "Parameter := by\n"
                "  exact seq.estimate n sample"
            ),
            tags=("estimator_sequence", "projection"),
            dependencies=("StatInference.EstimatorSequence.estimate",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.EstimatorSequence.estimate",),
    ),
    BenchmarkTask(
        task_id="target_parameter_value_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("estimator_interface",),
        natural_language="Evaluate a target-parameter functional at a model.",
        lean_task=LeanTask(
            task_id="target_parameter_value_seed",
            imports=("StatInference.Estimator.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Model Parameter : Type*} "
                "(target : StatInference.TargetParameter Model Parameter) (model : Model) : "
                "Parameter := by\n"
                "  exact target.value model"
            ),
            tags=("target_parameter", "projection"),
            dependencies=("StatInference.TargetParameter.value",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.TargetParameter.value",),
    ),
    BenchmarkTask(
        task_id="influence_expansion_statement_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S1",
        domain_tags=("estimator_interface", "asymptotic_linearity"),
        natural_language="Reuse the proof obligation carried by an influence-expansion interface.",
        lean_task=LeanTask(
            task_id="influence_expansion_statement_seed",
            imports=("StatInference.Estimator.AsymptoticLinear",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Statistic LinearPart Remainder : Type*} "
                "(expansion : StatInference.InfluenceExpansion Statistic LinearPart Remainder) "
                "(h : expansion.expansion_statement) : "
                "expansion.expansion_statement := by\n"
                "  exact h"
            ),
            tags=("influence_expansion", "projection"),
            dependencies=("StatInference.InfluenceExpansion.expansion_statement",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.InfluenceExpansion.expansion_statement",),
    ),
    BenchmarkTask(
        task_id="asymptotic_linear_estimator_statement_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S1",
        domain_tags=("estimator_interface", "asymptotic_linearity"),
        natural_language="Reuse the statement field of an asymptotic-linear estimator interface.",
        lean_task=LeanTask(
            task_id="asymptotic_linear_estimator_statement_seed",
            imports=("StatInference.Estimator.AsymptoticLinear",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {EstimatorObj InfluenceFunction : Type*} "
                "(est : StatInference.AsymptoticLinearEstimator EstimatorObj InfluenceFunction) "
                "(h : est.statement) : "
                "est.statement := by\n"
                "  exact h"
            ),
            tags=("asymptotic_linear_estimator", "projection"),
            dependencies=("StatInference.AsymptoticLinearEstimator.statement",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.AsymptoticLinearEstimator.statement",),
    ),
    BenchmarkTask(
        task_id="m_estimator_approximate_minimizer_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("estimator_interface", "m_estimation", "erm_consistency"),
        natural_language="Project the comparator-specific approximate-minimizer inequality from an M-estimator.",
        lean_task=LeanTask(
            task_id="m_estimator_approximate_minimizer_seed",
            imports=("StatInference.Estimator.MEstimator",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} {Parameter : Type*} "
                "(m : StatInference.MEstimator Sample Parameter) "
                "(n : Nat) (sample : Sample n) (comparator : Parameter) : "
                "m.empirical_risk.risk n sample (m.estimate n sample) <= "
                "m.empirical_risk.risk n sample comparator + m.tolerance n := by\n"
                "  exact StatInference.MEstimator.approximateMinimizer_le "
                "m n sample comparator"
            ),
            tags=("m_estimator", "approximate_minimizer", "projection"),
            dependencies=("StatInference.MEstimator.approximateMinimizer_le",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.MEstimator.approximateMinimizer_le",),
    ),
    BenchmarkTask(
        task_id="m_estimator_oracle_excess_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("estimator_interface", "m_estimation", "erm_consistency"),
        natural_language="Apply the deterministic oracle excess-risk bound for an M-estimator with uniform deviation.",
        lean_task=LeanTask(
            task_id="m_estimator_oracle_excess_seed",
            imports=("StatInference.Estimator.MEstimator",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} {Parameter : Type*} "
                "(interface : StatInference.MEstimatorWithOracle Sample Parameter) "
                "(n : Nat) (sample : Sample n) : "
                "StatInference.excessRisk interface.populationRisk interface.oracle "
                "(interface.m_estimator.estimate n sample) <= "
                "2 * interface.uniform_deviation.deviation n + "
                "interface.m_estimator.tolerance n := by\n"
                "  exact StatInference.MEstimatorWithOracle.oracleExcessRiskBound "
                "interface n sample"
            ),
            tags=("m_estimator", "oracle", "excess_risk"),
            dependencies=("StatInference.MEstimatorWithOracle.oracleExcessRiskBound",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.MEstimatorWithOracle.oracleExcessRiskBound",),
    ),
    BenchmarkTask(
        task_id="z_estimator_to_m_estimator_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("estimator_interface", "z_estimation", "m_estimation"),
        natural_language="Convert a discrepancy-based Z-estimator into the corresponding M-estimator interface.",
        lean_task=LeanTask(
            task_id="z_estimator_to_m_estimator_seed",
            imports=("StatInference.Estimator.ZEstimator",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} {Parameter Moment : Type*} "
                "(z : StatInference.ZEstimator Sample Parameter Moment) : "
                "StatInference.MEstimator Sample Parameter := by\n"
                "  exact z.toMEstimator"
            ),
            tags=("z_estimator", "m_estimator", "conversion"),
            dependencies=("StatInference.ZEstimator.toMEstimator",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.ZEstimator.toMEstimator",),
    ),
    BenchmarkTask(
        task_id="z_estimator_oracle_excess_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("estimator_interface", "z_estimation", "erm_consistency"),
        natural_language="Apply the deterministic oracle excess-residual-risk bound for a Z-estimator.",
        lean_task=LeanTask(
            task_id="z_estimator_oracle_excess_seed",
            imports=("StatInference.Estimator.ZEstimator",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} {Parameter Moment : Type*} "
                "(interface : StatInference.ZEstimatorWithOracle Sample Parameter Moment) "
                "(n : Nat) (sample : Sample n) : "
                "StatInference.excessRisk interface.populationRisk interface.oracle "
                "(interface.z_estimator.estimate n sample) <= "
                "2 * interface.uniform_deviation.deviation n + "
                "interface.z_estimator.tolerance n := by\n"
                "  exact StatInference.ZEstimatorWithOracle.oracleExcessRiskBound "
                "interface n sample"
            ),
            tags=("z_estimator", "oracle", "excess_risk"),
            dependencies=("StatInference.ZEstimatorWithOracle.oracleExcessRiskBound",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.ZEstimatorWithOracle.oracleExcessRiskBound",),
    ),
    BenchmarkTask(
        task_id="empirical_process_measurability_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("empirical_process",),
        natural_language="Reuse the measurability obligation carried by an empirical-process specification.",
        lean_task=LeanTask(
            task_id="empirical_process_measurability_seed",
            imports=("StatInference.EmpiricalProcess.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index Observation Value : Type*} "
                "(spec : StatInference.EmpiricalProcessSpec Index Observation Value) "
                "(h : spec.measurability_statement) : "
                "spec.measurability_statement := by\n"
                "  exact h"
            ),
            tags=("empirical_process", "measurability"),
            dependencies=("StatInference.EmpiricalProcessSpec.measurability_statement",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.EmpiricalProcessSpec.measurability_statement",),
    ),
    BenchmarkTask(
        task_id="empirical_process_complexity_pair_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S1",
        domain_tags=("empirical_process",),
        natural_language="Package empirical-process measurability and complexity obligations together.",
        lean_task=LeanTask(
            task_id="empirical_process_complexity_pair_seed",
            imports=("StatInference.EmpiricalProcess.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index Observation Value : Type*} "
                "(spec : StatInference.EmpiricalProcessSpec Index Observation Value) "
                "(hmeas : spec.measurability_statement) "
                "(hcomplex : spec.complexity_statement) : "
                "spec.measurability_statement /\\ spec.complexity_statement := by\n"
                "  exact And.intro hmeas hcomplex"
            ),
            tags=("empirical_process", "complexity", "measurability"),
            dependencies=(
                "StatInference.EmpiricalProcessSpec.measurability_statement",
                "StatInference.EmpiricalProcessSpec.complexity_statement",
            ),
            expected_patterns=("And.intro",),
        ),
        expected_premises=(
            "StatInference.EmpiricalProcessSpec.measurability_statement",
            "StatInference.EmpiricalProcessSpec.complexity_statement",
        ),
    ),
    BenchmarkTask(
        task_id="glivenko_cantelli_statement_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("empirical_process", "glivenko_cantelli"),
        natural_language="Reuse the uniform-law statement carried by a Glivenko-Cantelli specification.",
        lean_task=LeanTask(
            task_id="glivenko_cantelli_statement_seed",
            imports=("StatInference.EmpiricalProcess.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (gc : StatInference.GlivenkoCantelliSpec) "
                "(h : gc.uniform_law_statement) : "
                "gc.uniform_law_statement := by\n"
                "  exact h"
            ),
            tags=("glivenko_cantelli", "uniform_law"),
            dependencies=("StatInference.GlivenkoCantelliSpec.uniform_law_statement",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.GlivenkoCantelliSpec.uniform_law_statement",),
    ),
    BenchmarkTask(
        task_id="donsker_statement_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TEST,
        difficulty="S1",
        domain_tags=("empirical_process", "donsker"),
        natural_language="Reuse the weak-convergence statement carried by a Donsker specification.",
        lean_task=LeanTask(
            task_id="donsker_statement_seed",
            imports=("StatInference.EmpiricalProcess.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (donsker : StatInference.DonskerSpec) "
                "(h : donsker.weak_convergence_statement) : "
                "donsker.weak_convergence_statement := by\n"
                "  exact h"
            ),
            tags=("donsker", "weak_convergence"),
            dependencies=("StatInference.DonskerSpec.weak_convergence_statement",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.DonskerSpec.weak_convergence_statement",),
    ),
    BenchmarkTask(
        task_id="asymptotic_bridge_verified_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("asymptotic_normality", "asymptotic_bridge"),
        natural_language="Mark the asymptotic-normality bridge conclusion as verified by Lean.",
        lean_task=LeanTask(
            task_id="asymptotic_bridge_verified_seed",
            imports=("StatInference.Asymptotics.AsymptoticNormal",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (b : StatInference.AsymptoticNormalityBridge) "
                "(hal : b.asymptotic_linear) "
                "(hclt : b.clt_for_linear_part) "
                "(hrem : b.negligible_remainder) : "
                "StatInference.VerifiedByLean b.asymptotic_normality := by\n"
                "  exact StatInference.asymptotic_normality_of_bridge b hal hclt hrem"
            ),
            tags=("asymptotic_normality", "bridge", "verified_by_lean"),
            dependencies=("StatInference.asymptotic_normality_of_bridge",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.asymptotic_normality_of_bridge",),
    ),
    BenchmarkTask(
        task_id="potential_outcome_treated_projection_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.TRAIN,
        difficulty="S1",
        domain_tags=("causal_identification", "potential_outcomes"),
        natural_language="Project the treated potential outcome from a potential-outcome model.",
        lean_task=LeanTask(
            task_id="potential_outcome_treated_projection_seed",
            imports=("StatInference.Causal.PotentialOutcomes",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Unit Outcome Covariate : Type*} "
                "(model : StatInference.PotentialOutcomeModel Unit Outcome Covariate) "
                "(unit : Unit) : "
                "Outcome := by\n"
                "  exact model.y1 unit"
            ),
            tags=("potential_outcomes", "projection"),
            dependencies=("StatInference.PotentialOutcomeModel.y1",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.PotentialOutcomeModel.y1",),
    ),
    BenchmarkTask(
        task_id="causal_identification_verified_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("causal_identification", "causal_bridge"),
        natural_language="Mark the ATE identification bridge conclusion as verified by Lean.",
        lean_task=LeanTask(
            task_id="causal_identification_verified_seed",
            imports=("StatInference.Causal.PotentialOutcomes",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (b : StatInference.ATEIdentificationBridge) "
                "(hoverlap : b.overlap.statement) "
                "(hunconf : b.unconfoundedness.statement) : "
                "StatInference.VerifiedByLean b.identification := by\n"
                "  exact StatInference.ate_identification_of_bridge b hoverlap hunconf"
            ),
            tags=("causal_identification", "bridge", "verified_by_lean"),
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
