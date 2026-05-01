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
        task_id="finite_class_oracle_excess_on_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("finite_class_gc", "erm_consistency", "empirical_process"),
        natural_language=(
            "Use a finite/restricted-class uniform-deviation sequence to bound "
            "approximate ERM excess risk against an in-class comparator."
        ),
        lean_task=LeanTask(
            task_id="finite_class_oracle_excess_on_seed",
            imports=("StatInference.EmpiricalProcess.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index : Type*} {indexClass : Set Index} "
                "(R : Index -> Real) (Rn : Nat -> Index -> Real) "
                "(fhat : Nat -> Index) (comparator : Index) "
                "(eps radius : Nat -> Real) "
                "(hfhat : forall n, fhat n ∈ indexClass) "
                "(hcomparator : comparator ∈ indexClass) "
                "(h_uniform : StatInference.EmpiricalDeviationSequenceOn indexClass R Rn radius) "
                "(h_erm : forall n, Rn n (fhat n) <= Rn n comparator + eps n) : "
                "forall n, R (fhat n) - R comparator <= 2 * radius n + eps n := by\n"
                "  exact StatInference.oracle_excess_sequence_bound_on "
                "R Rn fhat comparator eps radius hfhat hcomparator h_uniform h_erm"
            ),
            tags=("finite_class", "restricted_uniform_deviation", "excess_risk"),
            dependencies=("StatInference.oracle_excess_sequence_bound_on",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.oracle_excess_sequence_bound_on",),
    ),
    BenchmarkTask(
        task_id="finite_class_erm_consistency_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S5",
        domain_tags=("finite_class_gc", "erm_consistency", "empirical_process"),
        natural_language=(
            "Apply finite-class uniform convergence plus vanishing approximate "
            "ERM error to get eventual excess-risk consistency."
        ),
        lean_task=LeanTask(
            task_id="finite_class_erm_consistency_seed",
            imports=("StatInference.EmpiricalProcess.Basic",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index : Type*} {indexClass : Set Index} "
                "(R : Index -> Real) (Rn : Nat -> Index -> Real) "
                "(finite_gc : StatInference.FiniteClassUniformConvergence indexClass R Rn) "
                "(fhat : Nat -> Index) (comparator : Index) (eps : Nat -> Real) "
                "(hfhat : forall n, fhat n ∈ indexClass) "
                "(hcomparator : comparator ∈ indexClass) "
                "(h_erm : forall n, Rn n (fhat n) <= Rn n comparator + eps n) "
                "(h_eps : Filter.Tendsto eps Filter.atTop (nhds 0)) : "
                "forall tolerance, tolerance > 0 -> "
                "∀ᶠ n in Filter.atTop, R (fhat n) - R comparator < tolerance := by\n"
                "  exact StatInference.FiniteClassUniformConvergence.eventually_excessRisk_lt_of_approx_erm "
                "finite_gc fhat comparator eps hfhat hcomparator h_erm h_eps"
            ),
            tags=("finite_class", "erm_consistency", "eventual_excess_risk"),
            dependencies=(
                "StatInference.FiniteClassUniformConvergence.eventually_excessRisk_lt_of_approx_erm",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.FiniteClassUniformConvergence.eventually_excessRisk_lt_of_approx_erm",
        ),
    ),
    BenchmarkTask(
        task_id="ratio_error_identity_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("ratio_estimator", "hajek_ipw", "estimator_algebra"),
        natural_language=(
            "Prove the core ratio linearization identity: ratio error is the "
            "centered numerator residual divided by the denominator."
        ),
        lean_task=LeanTask(
            task_id="ratio_error_identity_seed",
            imports=("StatInference.Estimator.Ratio",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (numerator denominator target : Real) "
                "(hden : denominator ≠ 0) : "
                "StatInference.ratioEstimate numerator denominator - target = "
                "StatInference.ratioResidual numerator denominator target / denominator := by\n"
                "  exact StatInference.ratio_sub_target_eq_residual_div "
                "numerator denominator target hden"
            ),
            tags=("ratio_estimator", "linearization", "residual_identity"),
            dependencies=("StatInference.ratio_sub_target_eq_residual_div",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.ratio_sub_target_eq_residual_div",),
    ),
    BenchmarkTask(
        task_id="scaled_hajek_ratio_error_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("ratio_estimator", "hajek_ipw", "asymptotic_scaling"),
        natural_language=(
            "Apply the scaled Hajek/IPW ratio error identity for an arbitrary "
            "deterministic rate sequence."
        ),
        lean_task=LeanTask(
            task_id="scaled_hajek_ratio_error_seed",
            imports=("StatInference.Estimator.Ratio",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (weightedOutcome weightedMass : Nat -> Real) "
                "(target : Real) (rate : Nat -> Real) "
                "(hmass : forall n, weightedMass n ≠ 0) : "
                "forall n, rate n * "
                "(StatInference.hajekRatio weightedOutcome weightedMass n - target) = "
                "rate n * StatInference.hajekResidual "
                "weightedOutcome weightedMass target n / weightedMass n := by\n"
                "  exact StatInference.scaled_hajekRatio_sub_target_eq_residual_div "
                "weightedOutcome weightedMass target rate hmass"
            ),
            tags=("hajek_ipw", "linearization", "scaled_error"),
            dependencies=("StatInference.scaled_hajekRatio_sub_target_eq_residual_div",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.scaled_hajekRatio_sub_target_eq_residual_div",),
    ),
    BenchmarkTask(
        task_id="empirical_average_unfold_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S2",
        domain_tags=("empirical_process", "empirical_average", "notation"),
        natural_language=(
            "Unfold the empirical average notation into a finite sample sum "
            "divided by sample size."
        ),
        lean_task=LeanTask(
            task_id="empirical_average_unfold_seed",
            imports=("StatInference.EmpiricalProcess.Average",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Observation : Type*} {n : Nat} "
                "(sample : StatInference.SampleAt Observation n) "
                "(statistic : Observation -> Real) : "
                "StatInference.empiricalAverage sample statistic = "
                "(Finset.sum Finset.univ (fun i : Fin n => statistic (sample i))) / "
                "(n : Real) := by\n"
                "  exact StatInference.empiricalAverage_eq_sum_div sample statistic"
            ),
            tags=("empirical_average", "finite_sample_sum", "notation"),
            dependencies=("StatInference.empiricalAverage_eq_sum_div",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.empiricalAverage_eq_sum_div",),
    ),
    BenchmarkTask(
        task_id="empirical_risk_sequence_oracle_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("empirical_process", "empirical_risk", "erm_consistency"),
        natural_language=(
            "Use empirical risk generated from a loss and sample sequence as "
            "the empirical-risk input to the deterministic ERM excess bound."
        ),
        lean_task=LeanTask(
            task_id="empirical_risk_sequence_oracle_seed",
            imports=("StatInference.EmpiricalProcess.Average",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Observation Candidate : Type*} "
                "(samples : forall n, StatInference.SampleAt Observation n) "
                "(loss : Candidate -> Observation -> Real) "
                "(populationRisk : Candidate -> Real) "
                "(fhat : Nat -> Candidate) (comparator : Candidate) "
                "(eps radius : Nat -> Real) "
                "(h_uniform : StatInference.EmpiricalDeviationSequence "
                "populationRisk "
                "(StatInference.empiricalRiskSequenceOfSamples samples loss) radius) "
                "(h_erm : forall n, "
                "StatInference.empiricalRiskSequenceOfSamples samples loss n (fhat n) <= "
                "StatInference.empiricalRiskSequenceOfSamples samples loss n comparator + eps n) : "
                "forall n, populationRisk (fhat n) - populationRisk comparator <= "
                "2 * radius n + eps n := by\n"
                "  exact StatInference.empiricalRiskSequence_excess_bound_of_uniform_deviation "
                "samples loss populationRisk fhat comparator eps radius h_uniform h_erm"
            ),
            tags=("empirical_risk", "loss", "oracle_inequality"),
            dependencies=("StatInference.empiricalRiskSequence_excess_bound_of_uniform_deviation",),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.empiricalRiskSequence_excess_bound_of_uniform_deviation",
        ),
    ),
    BenchmarkTask(
        task_id="finite_union_no_failure_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("empirical_process", "finite_union", "uniform_deviation"),
        natural_language=(
            "Convert absence of the finite-union deviation failure event into "
            "a restricted-class uniform-deviation bound."
        ),
        lean_task=LeanTask(
            task_id="finite_union_no_failure_seed",
            imports=("StatInference.EmpiricalProcess.Finite",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index : Type*} {indexClass : Set Index} "
                "(populationRisk empiricalRisk : Index -> Real) (radius : Real) "
                "(hno_failure : ¬ StatInference.DeviationFailureEventOn "
                "indexClass populationRisk empiricalRisk radius) : "
                "StatInference.EmpiricalDeviationBoundOn "
                "indexClass populationRisk empiricalRisk radius := by\n"
                "  exact StatInference.empiricalDeviationBoundOn_of_not_deviationFailureEventOn "
                "hno_failure"
            ),
            tags=("finite_union", "failure_event", "uniform_deviation"),
            dependencies=(
                "StatInference.empiricalDeviationBoundOn_of_not_deviationFailureEventOn",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.empiricalDeviationBoundOn_of_not_deviationFailureEventOn",
        ),
    ),
    BenchmarkTask(
        task_id="finite_union_sequence_excess_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("empirical_process", "finite_union", "erm_consistency"),
        natural_language=(
            "Use a sequence of finite-union no-failure certificates as the "
            "uniform-deviation input to the approximate ERM excess-risk bound."
        ),
        lean_task=LeanTask(
            task_id="finite_union_sequence_excess_seed",
            imports=("StatInference.EmpiricalProcess.Finite",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index : Type*} {indexClass : Set Index} "
                "{populationRisk : Index -> Real} {empiricalRisk : Nat -> Index -> Real} "
                "(certificate : StatInference.FiniteUnionDeviationSequence "
                "indexClass populationRisk empiricalRisk) "
                "(fhat : Nat -> Index) (comparator : Index) (eps : Nat -> Real) "
                "(hfhat : forall n, fhat n ∈ indexClass) "
                "(hcomparator : comparator ∈ indexClass) "
                "(h_erm : forall n, empiricalRisk n (fhat n) <= "
                "empiricalRisk n comparator + eps n) : "
                "forall n, populationRisk (fhat n) - populationRisk comparator <= "
                "2 * certificate.radius n + eps n := by\n"
                "  exact StatInference.FiniteUnionDeviationSequence.excessRiskBound "
                "certificate fhat comparator eps hfhat hcomparator h_erm"
            ),
            tags=("finite_union", "oracle_inequality", "excess_risk"),
            dependencies=("StatInference.FiniteUnionDeviationSequence.excessRiskBound",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.FiniteUnionDeviationSequence.excessRiskBound",),
    ),
    BenchmarkTask(
        task_id="finite_class_gc_projection_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("empirical_process", "glivenko_cantelli", "projection"),
        natural_language=(
            "Project a finite-class uniform-convergence certificate to a "
            "subclass and expose it as a GC class."
        ),
        lean_task=LeanTask(
            task_id="finite_class_gc_projection_seed",
            imports=("StatInference.EmpiricalProcess.Preservation",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index : Type*} {largerClass smallerClass : Set Index} "
                "{populationRisk : Index -> Real} {empiricalRisk : Nat -> Index -> Real} "
                "(finite_gc : StatInference.FiniteClassUniformConvergence "
                "largerClass populationRisk empiricalRisk) "
                "(hsubset : smallerClass ⊆ largerClass) : "
                "StatInference.GlivenkoCantelliClass smallerClass populationRisk empiricalRisk := by\n"
                "  exact StatInference.FiniteClassUniformConvergence.projectToGlivenkoCantelliClass "
                "finite_gc hsubset"
            ),
            tags=("finite_class", "gc_projection", "subclass"),
            dependencies=(
                "StatInference.FiniteClassUniformConvergence.projectToGlivenkoCantelliClass",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.FiniteClassUniformConvergence.projectToGlivenkoCantelliClass",
        ),
    ),
    BenchmarkTask(
        task_id="finite_union_projection_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("empirical_process", "finite_union", "projection"),
        natural_language=(
            "Project a sequence of finite-union no-failure certificates to a "
            "subclass."
        ),
        lean_task=LeanTask(
            task_id="finite_union_projection_seed",
            imports=("StatInference.EmpiricalProcess.Preservation",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index : Type*} {largerClass smallerClass : Set Index} "
                "{populationRisk : Index -> Real} {empiricalRisk : Nat -> Index -> Real} "
                "(certificate : StatInference.FiniteUnionDeviationSequence "
                "largerClass populationRisk empiricalRisk) "
                "(hsubset : smallerClass ⊆ largerClass) : "
                "StatInference.FiniteUnionDeviationSequence "
                "smallerClass populationRisk empiricalRisk := by\n"
                "  exact StatInference.FiniteUnionDeviationSequence.project "
                "certificate hsubset"
            ),
            tags=("finite_union", "subclass", "projection"),
            dependencies=("StatInference.FiniteUnionDeviationSequence.project",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.FiniteUnionDeviationSequence.project",),
    ),
    BenchmarkTask(
        task_id="covering_certificate_gc_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("empirical_process", "covering_number", "glivenko_cantelli"),
        natural_language=(
            "Convert a proof-carrying covering-number deviation certificate "
            "into a GC-class interface."
        ),
        lean_task=LeanTask(
            task_id="covering_certificate_gc_seed",
            imports=("StatInference.EmpiricalProcess.Complexity",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index : Type*} {indexClass : Set Index} "
                "{populationRisk : Index -> Real} {empiricalRisk : Nat -> Index -> Real} "
                "(certificate : StatInference.CoveringNumberDeviationCertificate "
                "indexClass populationRisk empiricalRisk) "
                "(hassumptions : certificate.assumptions) : "
                "StatInference.GlivenkoCantelliClass "
                "indexClass populationRisk empiricalRisk := by\n"
                "  exact StatInference.CoveringNumberDeviationCertificate.toGlivenkoCantelliClass "
                "certificate hassumptions"
            ),
            tags=("covering_number", "gc_certificate", "uniform_deviation"),
            dependencies=(
                "StatInference.CoveringNumberDeviationCertificate.toGlivenkoCantelliClass",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.CoveringNumberDeviationCertificate.toGlivenkoCantelliClass",
        ),
    ),
    BenchmarkTask(
        task_id="rademacher_certificate_gc_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S5",
        domain_tags=("empirical_process", "rademacher_complexity", "glivenko_cantelli"),
        natural_language=(
            "Use a Rademacher-compatible deviation certificate plus vanishing "
            "complexity and slack to build a GC-class interface."
        ),
        lean_task=LeanTask(
            task_id="rademacher_certificate_gc_seed",
            imports=("StatInference.EmpiricalProcess.Complexity",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Index : Type*} {indexClass : Set Index} "
                "{populationRisk : Index -> Real} {empiricalRisk : Nat -> Index -> Real} "
                "(certificate : StatInference.RademacherDeviationCertificate "
                "indexClass populationRisk empiricalRisk) "
                "(hcomplexity : Filter.Tendsto certificate.rademacher.complexity "
                "Filter.atTop (nhds 0)) "
                "(hslack : Filter.Tendsto certificate.slack Filter.atTop (nhds 0)) : "
                "StatInference.GlivenkoCantelliClass "
                "indexClass populationRisk empiricalRisk := by\n"
                "  exact StatInference.RademacherDeviationCertificate.toGlivenkoCantelliClass "
                "certificate hcomplexity hslack"
            ),
            tags=("rademacher_complexity", "gc_certificate", "radius_tendsto_zero"),
            dependencies=(
                "StatInference.RademacherDeviationCertificate.toGlivenkoCantelliClass",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.RademacherDeviationCertificate.toGlivenkoCantelliClass",
        ),
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
        task_id="delta_method_estimator_bridge_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("convergence", "delta_method", "estimator_transformation"),
        natural_language=(
            "Expose an estimator-level delta-method route as the generic "
            "delta-method convergence bridge."
        ),
        lean_task=LeanTask(
            task_id="delta_method_estimator_bridge_seed",
            imports=("StatInference.Estimator.DeltaMethod",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} "
                "{Parameter Transformed LinearPart Remainder : Type*} "
                "(route : StatInference.DeltaMethodEstimatorRoute "
                "Sample Parameter Transformed LinearPart Remainder) : "
                "StatInference.DeltaMethodBridge := by\n"
                "  exact StatInference.DeltaMethodEstimatorRoute.toDeltaMethodBridge "
                "route"
            ),
            tags=("delta_method", "estimator_transformation", "bridge"),
            dependencies=(
                "StatInference.DeltaMethodEstimatorRoute.toDeltaMethodBridge",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.DeltaMethodEstimatorRoute.toDeltaMethodBridge",
        ),
    ),
    BenchmarkTask(
        task_id="delta_method_estimator_convergence_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("convergence", "delta_method", "estimator_transformation"),
        natural_language=(
            "Apply the estimator-level delta method: the estimator-transform "
            "relation, linear-part convergence, and negligible remainder imply "
            "transformed-estimator convergence."
        ),
        lean_task=LeanTask(
            task_id="delta_method_estimator_convergence_seed",
            imports=("StatInference.Estimator.DeltaMethod",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} "
                "{Parameter Transformed LinearPart Remainder : Type*} "
                "(route : StatInference.DeltaMethodEstimatorRoute "
                "Sample Parameter Transformed LinearPart Remainder) "
                "(h_transform : route.estimator_transformation_statement) "
                "(h_linear : route.linear_part_convergence.statement) "
                "(h_remainder : route.remainder_small.statement) : "
                "route.transformed_convergence := by\n"
                "  exact StatInference.DeltaMethodEstimatorRoute.transformedConvergence "
                "route h_transform h_linear h_remainder"
            ),
            tags=("delta_method", "estimator_transformation", "convergence"),
            dependencies=(
                "StatInference.DeltaMethodEstimatorRoute.transformedConvergence",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.DeltaMethodEstimatorRoute.transformedConvergence",
        ),
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
        task_id="indexed_asymptotic_linear_clt_route_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("asymptotic_normality", "clt", "asymptotic_linearity"),
        natural_language=(
            "Apply the explicit indexed estimator route: expansion match, "
            "expansion statement, negligible remainder, and CLT imply "
            "asymptotic normality."
        ),
        lean_task=LeanTask(
            task_id="indexed_asymptotic_linear_clt_route_seed",
            imports=("StatInference.Estimator.Normality",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} "
                "{Parameter InfluenceFunction LinearPart Remainder : Type*} "
                "(route : StatInference.IndexedAsymptoticLinearCLTRoute "
                "Sample Parameter InfluenceFunction LinearPart Remainder) "
                "(h_match : route.estimator.estimator_matches_expansion) "
                "(h_expansion : route.estimator.expansion.expansion_statement) "
                "(h_remainder : route.estimator.remainder_negligible.statement) "
                "(h_clt : route.clt.statement) : "
                "route.asymptotic_normality := by\n"
                "  exact StatInference.IndexedAsymptoticLinearCLTRoute.asymptoticNormal "
                "route h_match h_expansion h_remainder h_clt"
            ),
            tags=("indexed_estimator", "asymptotic_linearity", "clt_route"),
            dependencies=(
                "StatInference.IndexedAsymptoticLinearCLTRoute.asymptoticNormal",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.IndexedAsymptoticLinearCLTRoute.asymptoticNormal",
        ),
    ),
    BenchmarkTask(
        task_id="indexed_asymptotic_linear_clt_bridge_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("asymptotic_normality", "clt", "bridge"),
        natural_language=(
            "Expose an explicit indexed asymptotic-linearity route as the "
            "generic asymptotic-linearity plus CLT bridge."
        ),
        lean_task=LeanTask(
            task_id="indexed_asymptotic_linear_clt_bridge_seed",
            imports=("StatInference.Estimator.Normality",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} "
                "{Parameter InfluenceFunction LinearPart Remainder : Type*} "
                "(route : StatInference.IndexedAsymptoticLinearCLTRoute "
                "Sample Parameter InfluenceFunction LinearPart Remainder) : "
                "StatInference.AsymptoticLinearCLTBridge := by\n"
                "  exact StatInference.IndexedAsymptoticLinearCLTRoute.toAsymptoticLinearCLTBridge "
                "route"
            ),
            tags=("indexed_estimator", "clt_bridge", "normality_route"),
            dependencies=(
                "StatInference.IndexedAsymptoticLinearCLTRoute.toAsymptoticLinearCLTBridge",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.IndexedAsymptoticLinearCLTRoute.toAsymptoticLinearCLTBridge",
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
        task_id="ate_identification_sanity_witness_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("causal_identification", "potential_outcomes", "non_vacuity"),
        natural_language=(
            "Build a concrete one-unit deterministic ATE identification sanity "
            "witness from two real potential outcomes."
        ),
        lean_task=LeanTask(
            task_id="ate_identification_sanity_witness_seed",
            imports=("StatInference.Causal.ATE",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (y0 y1 : Real) : "
                "StatInference.ATEIdentificationSanityExample := by\n"
                "  exact StatInference.ATEIdentificationSanityExample.ofOutcomes y0 y1"
            ),
            tags=("causal_identification", "ate", "non_vacuity"),
            dependencies=("StatInference.ATEIdentificationSanityExample.ofOutcomes",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.ATEIdentificationSanityExample.ofOutcomes",),
    ),
    BenchmarkTask(
        task_id="ate_identification_sanity_verified_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("causal_identification", "potential_outcomes", "ate"),
        natural_language=(
            "Extract the verified ATE identification conclusion from the "
            "deterministic non-vacuity witness."
        ),
        lean_task=LeanTask(
            task_id="ate_identification_sanity_verified_seed",
            imports=("StatInference.Causal.ATE",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (witness : StatInference.ATEIdentificationSanityExample) : "
                "witness.bridge.identification := by\n"
                "  exact StatInference.ATEIdentificationSanityExample.identified witness"
            ),
            tags=("causal_identification", "ate", "verified_by_lean"),
            dependencies=("StatInference.ATEIdentificationSanityExample.identified",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.ATEIdentificationSanityExample.identified",),
    ),
    BenchmarkTask(
        task_id="ipw_identification_certificate_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("causal_identification", "ipw", "verified_by_lean"),
        natural_language=(
            "Extract the IPW identification conclusion from a proof-carrying "
            "certificate of consistency, overlap, unconfoundedness, correct "
            "propensity weights, and finite weight moments."
        ),
        lean_task=LeanTask(
            task_id="ipw_identification_certificate_seed",
            imports=("StatInference.Causal.IPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (certificate : StatInference.VerifiedIPWIdentification) : "
                "certificate.bridge.ipw_identifies_estimand := by\n"
                "  exact StatInference.VerifiedIPWIdentification.identifies certificate"
            ),
            tags=("ipw", "identification", "verified_certificate"),
            dependencies=("StatInference.VerifiedIPWIdentification.identifies",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.VerifiedIPWIdentification.identifies",),
    ),
    BenchmarkTask(
        task_id="ipw_hajek_scaled_linearization_route_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("ipw", "hajek_ipw", "linearization", "asymptotic_scaling"),
        natural_language=(
            "Apply the IPW/Hajek linearization route to obtain the scaled "
            "ratio residual identity needed by asymptotic arguments."
        ),
        lean_task=LeanTask(
            task_id="ipw_hajek_scaled_linearization_route_seed",
            imports=("StatInference.Causal.IPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (route : StatInference.IPWHajekLinearizationRoute) : "
                "forall n, route.rate n * "
                "(route.sequence.estimate n - route.sequence.target) = "
                "route.rate n * route.sequence.residual n / "
                "route.sequence.weightedMass n := by\n"
                "  exact StatInference.IPWHajekLinearizationRoute.scaledLinearization "
                "route"
            ),
            tags=("ipw", "hajek", "scaled_linearization"),
            dependencies=("StatInference.IPWHajekLinearizationRoute.scaledLinearization",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.IPWHajekLinearizationRoute.scaledLinearization",),
    ),
    BenchmarkTask(
        task_id="constant_ipw_hajek_route_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("ipw", "hajek_ipw", "non_vacuity"),
        natural_language=(
            "Construct a concrete constant-mass IPW/Hajek linearization route "
            "as a non-vacuity witness for the API."
        ),
        lean_task=LeanTask(
            task_id="constant_ipw_hajek_route_seed",
            imports=("StatInference.Causal.IPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (target : Real) (rate : Nat -> Real) : "
                "StatInference.IPWHajekLinearizationRoute := by\n"
                "  exact StatInference.constantIPWHajekLinearizationRoute target rate"
            ),
            tags=("ipw", "hajek", "non_vacuity"),
            dependencies=("StatInference.constantIPWHajekLinearizationRoute",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.constantIPWHajekLinearizationRoute",),
    ),
    BenchmarkTask(
        task_id="constant_ipw_hajek_exact_target_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("ipw", "hajek_ipw", "non_vacuity", "ratio_estimator"),
        natural_language=(
            "Show the concrete constant-mass IPW/Hajek sanity sequence "
            "estimates its target exactly."
        ),
        lean_task=LeanTask(
            task_id="constant_ipw_hajek_exact_target_seed",
            imports=("StatInference.Causal.IPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (target : Real) (n : Nat) : "
                "(StatInference.constantIPWHajekSequence target).estimate n = "
                "target := by\n"
                "  exact StatInference.constantIPWHajekSequence_estimate_eq_target "
                "target n"
            ),
            tags=("ipw", "hajek", "exact_target"),
            dependencies=("StatInference.constantIPWHajekSequence_estimate_eq_target",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.constantIPWHajekSequence_estimate_eq_target",),
    ),
    BenchmarkTask(
        task_id="aipw_double_robust_identification_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("aipw", "double_robust", "causal_identification"),
        natural_language=(
            "Extract the AIPW double-robust identification conclusion from a "
            "proof-carrying certificate."
        ),
        lean_task=LeanTask(
            task_id="aipw_double_robust_identification_seed",
            imports=("StatInference.Causal.AIPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example "
                "(certificate : StatInference.VerifiedAIPWDoubleRobustIdentification) : "
                "certificate.bridge.aipw_identifies_estimand := by\n"
                "  exact StatInference.VerifiedAIPWDoubleRobustIdentification.identifies "
                "certificate"
            ),
            tags=("aipw", "double_robust", "identification"),
            dependencies=(
                "StatInference.VerifiedAIPWDoubleRobustIdentification.identifies",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.VerifiedAIPWDoubleRobustIdentification.identifies",
        ),
    ),
    BenchmarkTask(
        task_id="aipw_product_rate_remainder_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("aipw", "product_rate", "second_order_remainder"),
        natural_language=(
            "Use a verified AIPW nuisance product-rate certificate to extract "
            "the small-o second-order remainder."
        ),
        lean_task=LeanTask(
            task_id="aipw_product_rate_remainder_seed",
            imports=("StatInference.Causal.AIPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (certificate : StatInference.VerifiedAIPWNuisanceProductRate) : "
                "certificate.product_rate.product_remainder_small.statement := by\n"
                "  exact StatInference.VerifiedAIPWNuisanceProductRate.remainderSmall "
                "certificate"
            ),
            tags=("aipw", "product_rate", "small_o"),
            dependencies=("StatInference.VerifiedAIPWNuisanceProductRate.remainderSmall",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.VerifiedAIPWNuisanceProductRate.remainderSmall",),
    ),
    BenchmarkTask(
        task_id="aipw_orthogonal_score_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("aipw", "neyman_orthogonality", "orthogonal_score"),
        natural_language=(
            "Expose the AIPW score orthogonality statement from the "
            "orthogonal product-rate route."
        ),
        lean_task=LeanTask(
            task_id="aipw_orthogonal_score_seed",
            imports=("StatInference.Causal.AIPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Observation Propensity Regression ScoreValue Parameter : Type*} "
                "(route : StatInference.AIPWOrthogonalProductRateRoute "
                "Observation Propensity Regression ScoreValue Parameter) : "
                "route.score.orthogonal_score_statement := by\n"
                "  exact StatInference.AIPWOrthogonalProductRateRoute.orthogonalScore "
                "route"
            ),
            tags=("aipw", "orthogonality", "score"),
            dependencies=("StatInference.AIPWOrthogonalProductRateRoute.orthogonalScore",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.AIPWOrthogonalProductRateRoute.orthogonalScore",),
    ),
    BenchmarkTask(
        task_id="aipw_second_order_remainder_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("aipw", "product_rate", "second_order_remainder"),
        natural_language=(
            "Apply the full AIPW orthogonal product-rate route to prove the "
            "second-order remainder statement."
        ),
        lean_task=LeanTask(
            task_id="aipw_second_order_remainder_seed",
            imports=("StatInference.Causal.AIPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Observation Propensity Regression ScoreValue Parameter : Type*} "
                "(route : StatInference.AIPWOrthogonalProductRateRoute "
                "Observation Propensity Regression ScoreValue Parameter) : "
                "route.second_order_remainder.statement := by\n"
                "  exact StatInference.AIPWOrthogonalProductRateRoute."
                "secondOrderRemainderSmall route"
            ),
            tags=("aipw", "orthogonality", "product_rate", "remainder"),
            dependencies=(
                "StatInference.AIPWOrthogonalProductRateRoute.secondOrderRemainderSmall",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.AIPWOrthogonalProductRateRoute.secondOrderRemainderSmall",
        ),
    ),
    BenchmarkTask(
        task_id="trivial_aipw_product_rate_route_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("aipw", "product_rate", "non_vacuity"),
        natural_language=(
            "Use the concrete trivial AIPW product-rate route as a non-vacuity "
            "witness for the orthogonality API."
        ),
        lean_task=LeanTask(
            task_id="trivial_aipw_product_rate_route_seed",
            imports=("StatInference.Causal.AIPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example : "
                "StatInference.trivialAIPWOrthogonalProductRateRoute."
                "second_order_remainder.statement := by\n"
                "  exact StatInference."
                "trivialAIPWOrthogonalProductRateRoute_secondOrderRemainderSmall"
            ),
            tags=("aipw", "non_vacuity", "second_order_remainder"),
            dependencies=(
                "StatInference.trivialAIPWOrthogonalProductRateRoute_secondOrderRemainderSmall",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.trivialAIPWOrthogonalProductRateRoute_secondOrderRemainderSmall",
        ),
    ),
    BenchmarkTask(
        task_id="influence_function_normality_route_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=(
            "semiparametric",
            "influence_function",
            "asymptotic_normality",
        ),
        natural_language=(
            "Apply the generic influence-function normality route: verified "
            "influence function plus CLT and negligible remainder imply "
            "asymptotic normality."
        ),
        lean_task=LeanTask(
            task_id="influence_function_normality_route_seed",
            imports=("StatInference.Semiparametric.Normality",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Model Parameter Observation EstimatorObj : Type*} "
                "(route : StatInference.InfluenceFunctionNormalityRoute "
                "Model Parameter Observation EstimatorObj) "
                "(h_clt : route.clt.statement) "
                "(h_remainder : route.negligible_remainder.statement) : "
                "route.asymptotic_normality := by\n"
                "  exact StatInference.InfluenceFunctionNormalityRoute.asymptoticNormal "
                "route h_clt h_remainder"
            ),
            tags=("influence_function", "asymptotic_normality", "clt"),
            dependencies=("StatInference.InfluenceFunctionNormalityRoute.asymptoticNormal",),
            expected_patterns=("exact",),
        ),
        expected_premises=("StatInference.InfluenceFunctionNormalityRoute.asymptoticNormal",),
    ),
    BenchmarkTask(
        task_id="influence_function_normality_bridge_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=(
            "semiparametric",
            "influence_function",
            "asymptotic_bridge",
        ),
        natural_language=(
            "Expose an influence-function normality route as the generic "
            "asymptotic-linearity plus CLT bridge."
        ),
        lean_task=LeanTask(
            task_id="influence_function_normality_bridge_seed",
            imports=("StatInference.Semiparametric.Normality",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Model Parameter Observation EstimatorObj : Type*} "
                "(route : StatInference.InfluenceFunctionNormalityRoute "
                "Model Parameter Observation EstimatorObj) : "
                "StatInference.AsymptoticLinearCLTBridge := by\n"
                "  exact StatInference.InfluenceFunctionNormalityRoute."
                "toAsymptoticLinearCLTBridge route"
            ),
            tags=("influence_function", "clt_bridge", "asymptotic_normality"),
            dependencies=(
                "StatInference.InfluenceFunctionNormalityRoute.toAsymptoticLinearCLTBridge",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.InfluenceFunctionNormalityRoute.toAsymptoticLinearCLTBridge",
        ),
    ),
    BenchmarkTask(
        task_id="aipw_influence_function_normality_route_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("aipw", "influence_function", "asymptotic_normality"),
        natural_language=(
            "Apply the AIPW influence-function normality route after CLT and "
            "negligible-remainder obligations are supplied."
        ),
        lean_task=LeanTask(
            task_id="aipw_influence_function_normality_route_seed",
            imports=("StatInference.Semiparametric.Normality",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Model Parameter Observation EstimatorObj : Type*} "
                "(route : StatInference.AIPWInfluenceFunctionNormalityRoute "
                "Model Parameter Observation EstimatorObj) "
                "(h_clt : route.clt.statement) "
                "(h_remainder : route.negligible_remainder.statement) : "
                "route.asymptotic_normality := by\n"
                "  exact StatInference.AIPWInfluenceFunctionNormalityRoute."
                "asymptoticNormal route h_clt h_remainder"
            ),
            tags=("aipw", "influence_function", "asymptotic_normality"),
            dependencies=(
                "StatInference.AIPWInfluenceFunctionNormalityRoute.asymptoticNormal",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.AIPWInfluenceFunctionNormalityRoute.asymptoticNormal",
        ),
    ),
    BenchmarkTask(
        task_id="trivial_influence_function_normality_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("semiparametric", "influence_function", "non_vacuity"),
        natural_language=(
            "Use the concrete trivial influence-function route as a "
            "non-vacuity witness for semiparametric normality."
        ),
        lean_task=LeanTask(
            task_id="trivial_influence_function_normality_seed",
            imports=("StatInference.Semiparametric.Normality",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example : "
                "StatInference.trivialInfluenceFunctionNormalityRoute."
                "asymptotic_normality := by\n"
                "  exact StatInference."
                "trivialInfluenceFunctionNormalityRoute_asymptoticNormal"
            ),
            tags=("influence_function", "non_vacuity", "asymptotic_normality"),
            dependencies=(
                "StatInference.trivialInfluenceFunctionNormalityRoute_asymptoticNormal",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.trivialInfluenceFunctionNormalityRoute_asymptoticNormal",
        ),
    ),
    BenchmarkTask(
        task_id="trivial_aipw_influence_function_normality_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("aipw", "influence_function", "non_vacuity"),
        natural_language=(
            "Use the concrete trivial AIPW influence-function normality route "
            "as a non-vacuity witness."
        ),
        lean_task=LeanTask(
            task_id="trivial_aipw_influence_function_normality_seed",
            imports=("StatInference.Semiparametric.Normality",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example : "
                "StatInference.trivialAIPWInfluenceFunctionNormalityRoute."
                "asymptotic_normality := by\n"
                "  exact StatInference."
                "trivialAIPWInfluenceFunctionNormalityRoute_asymptoticNormal"
            ),
            tags=("aipw", "influence_function", "non_vacuity"),
            dependencies=(
                "StatInference.trivialAIPWInfluenceFunctionNormalityRoute_asymptoticNormal",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.trivialAIPWInfluenceFunctionNormalityRoute_asymptoticNormal",
        ),
    ),
    BenchmarkTask(
        task_id="ipw_linearization_theorem_hole_seed",
        task_type=BenchmarkTaskType.SUBGOAL_COMPLETION,
        split=BenchmarkSplit.DEV,
        difficulty="S5",
        domain_tags=("ipw", "hajek_ipw", "theorem_hole", "multi_goal"),
        natural_language=(
            "Complete a two-goal IPW/Hajek theorem hole: prove both causal "
            "identification and the scaled ratio linearization from the same route."
        ),
        proof_state=(
            "Goals after constructor: "
            "1. route.identification.bridge.ipw_identifies_estimand; "
            "2. forall n, route.rate n * (route.sequence.estimate n - "
            "route.sequence.target) = route.rate n * route.sequence.residual n / "
            "route.sequence.weightedMass n."
        ),
        lean_task=LeanTask(
            task_id="ipw_linearization_theorem_hole_seed",
            imports=("StatInference.Causal.IPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example (route : StatInference.IPWHajekLinearizationRoute) : "
                "route.identification.bridge.ipw_identifies_estimand /\\ "
                "(forall n, route.rate n * "
                "(route.sequence.estimate n - route.sequence.target) = "
                "route.rate n * route.sequence.residual n / "
                "route.sequence.weightedMass n) := by\n"
                "  constructor\n"
                "  · sorry\n"
                "  · sorry"
            ),
            allowed_sorry=True,
            tags=("ipw", "theorem_hole", "multi_goal"),
            dependencies=(
                "StatInference.IPWHajekLinearizationRoute.identifies",
                "StatInference.IPWHajekLinearizationRoute.scaledLinearization",
            ),
            expected_patterns=("constructor", "sorry"),
        ),
        expected_premises=(
            "StatInference.IPWHajekLinearizationRoute.identifies",
            "StatInference.IPWHajekLinearizationRoute.scaledLinearization",
        ),
    ),
    BenchmarkTask(
        task_id="aipw_product_rate_theorem_hole_seed",
        task_type=BenchmarkTaskType.SUBGOAL_COMPLETION,
        split=BenchmarkSplit.DEV,
        difficulty="S5",
        domain_tags=("aipw", "product_rate", "theorem_hole", "multi_goal"),
        natural_language=(
            "Complete a two-goal AIPW theorem hole: prove double-robust "
            "identification and the second-order remainder from one route."
        ),
        proof_state=(
            "Goals after constructor: "
            "1. route.identification.bridge.aipw_identifies_estimand; "
            "2. route.second_order_remainder.statement."
        ),
        lean_task=LeanTask(
            task_id="aipw_product_rate_theorem_hole_seed",
            imports=("StatInference.Causal.AIPW",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Observation Propensity Regression ScoreValue Parameter : Type*} "
                "(route : StatInference.AIPWOrthogonalProductRateRoute "
                "Observation Propensity Regression ScoreValue Parameter) : "
                "route.identification.bridge.aipw_identifies_estimand /\\ "
                "route.second_order_remainder.statement := by\n"
                "  constructor\n"
                "  · sorry\n"
                "  · sorry"
            ),
            allowed_sorry=True,
            tags=("aipw", "product_rate", "theorem_hole", "multi_goal"),
            dependencies=(
                "StatInference.AIPWOrthogonalProductRateRoute.identifies",
                "StatInference.AIPWOrthogonalProductRateRoute.secondOrderRemainderSmall",
            ),
            expected_patterns=("constructor", "sorry"),
        ),
        expected_premises=(
            "StatInference.AIPWOrthogonalProductRateRoute.identifies",
            "StatInference.AIPWOrthogonalProductRateRoute.secondOrderRemainderSmall",
        ),
    ),
    BenchmarkTask(
        task_id="if_normality_theorem_hole_seed",
        task_type=BenchmarkTaskType.SUBGOAL_COMPLETION,
        split=BenchmarkSplit.DEV,
        difficulty="S5",
        domain_tags=(
            "semiparametric",
            "influence_function",
            "theorem_hole",
            "multi_goal",
        ),
        natural_language=(
            "Complete a two-goal influence-function theorem hole: prove "
            "asymptotic linearity and asymptotic normality from one route."
        ),
        proof_state=(
            "Goals after constructor: "
            "1. route.influence_bridge.estimator.statement; "
            "2. route.asymptotic_normality."
        ),
        lean_task=LeanTask(
            task_id="if_normality_theorem_hole_seed",
            imports=("StatInference.Semiparametric.Normality",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Model Parameter Observation EstimatorObj : Type*} "
                "(route : StatInference.InfluenceFunctionNormalityRoute "
                "Model Parameter Observation EstimatorObj) "
                "(h_clt : route.clt.statement) "
                "(h_remainder : route.negligible_remainder.statement) : "
                "route.influence_bridge.estimator.statement /\\ "
                "route.asymptotic_normality := by\n"
                "  constructor\n"
                "  · sorry\n"
                "  · sorry"
            ),
            allowed_sorry=True,
            tags=("influence_function", "theorem_hole", "multi_goal"),
            dependencies=(
                "StatInference.InfluenceFunctionNormalityRoute.asymptoticLinear",
                "StatInference.InfluenceFunctionNormalityRoute.asymptoticNormal",
            ),
            expected_patterns=("constructor", "sorry"),
        ),
        expected_premises=(
            "StatInference.InfluenceFunctionNormalityRoute.asymptoticLinear",
            "StatInference.InfluenceFunctionNormalityRoute.asymptoticNormal",
        ),
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
        task_id="m_estimator_argmin_consistency_bound_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("estimator_interface", "m_estimation", "argmin_consistency"),
        natural_language=(
            "Apply the M-estimator argmin consistency route's deterministic "
            "sample-path excess-risk bound."
        ),
        lean_task=LeanTask(
            task_id="m_estimator_argmin_consistency_bound_seed",
            imports=("StatInference.Estimator.MConsistency",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} {Parameter : Type*} "
                "(route : StatInference.MEstimatorArgminConsistencyRoute Sample Parameter) "
                "(n : Nat) : "
                "route.excessRiskSequence n <= route.oracleBoundSequence n := by\n"
                "  exact StatInference.MEstimatorArgminConsistencyRoute.excessRiskBound "
                "route n"
            ),
            tags=("m_estimator", "argmin_consistency", "oracle_bound"),
            dependencies=(
                "StatInference.MEstimatorArgminConsistencyRoute.excessRiskBound",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.MEstimatorArgminConsistencyRoute.excessRiskBound",
        ),
    ),
    BenchmarkTask(
        task_id="m_estimator_argmin_consistency_eventual_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("estimator_interface", "m_estimation", "argmin_consistency"),
        natural_language=(
            "Apply the M-estimator argmin consistency route: vanishing "
            "uniform-deviation radius and approximate-argmin tolerance imply "
            "eventual excess-risk consistency."
        ),
        lean_task=LeanTask(
            task_id="m_estimator_argmin_consistency_eventual_seed",
            imports=("StatInference.Estimator.MConsistency",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} {Parameter : Type*} "
                "(route : StatInference.MEstimatorArgminConsistencyRoute Sample Parameter) : "
                "forall tolerance, tolerance > 0 -> "
                "Filter.Eventually (fun n => route.excessRiskSequence n < tolerance) "
                "Filter.atTop := by\n"
                "  exact StatInference.MEstimatorArgminConsistencyRoute.eventually_excessRisk_lt "
                "route"
            ),
            tags=("m_estimator", "argmin_consistency", "eventual_excess_risk"),
            dependencies=(
                "StatInference.MEstimatorArgminConsistencyRoute.eventually_excessRisk_lt",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.MEstimatorArgminConsistencyRoute.eventually_excessRisk_lt",
        ),
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
        task_id="z_estimator_linearization_bridge_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S3",
        domain_tags=("estimator_interface", "z_estimation", "asymptotic_linearity"),
        natural_language=(
            "Project a proof-carrying Z-estimator differentiability and "
            "linearization bridge to the generic indexed asymptotic-linear "
            "estimator interface."
        ),
        lean_task=LeanTask(
            task_id="z_estimator_linearization_bridge_seed",
            imports=("StatInference.Estimator.ZLinearization",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} "
                "{Parameter Moment InfluenceFunction LinearPart Remainder : Type*} "
                "(bridge : StatInference.ZEstimatorLinearizationBridge "
                "Sample Parameter Moment InfluenceFunction LinearPart Remainder) : "
                "StatInference.IndexedAsymptoticLinearEstimator "
                "Sample Parameter InfluenceFunction LinearPart Remainder := by\n"
                "  exact StatInference.ZEstimatorLinearizationBridge."
                "toIndexedAsymptoticLinearEstimator bridge"
            ),
            tags=("z_estimator", "linearization", "asymptotic_linearity"),
            dependencies=(
                "StatInference.ZEstimatorLinearizationBridge.toIndexedAsymptoticLinearEstimator",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.ZEstimatorLinearizationBridge.toIndexedAsymptoticLinearEstimator",
        ),
    ),
    BenchmarkTask(
        task_id="z_estimator_asymptotic_normal_route_seed",
        task_type=BenchmarkTaskType.FORMAL_ONLY,
        split=BenchmarkSplit.DEV,
        difficulty="S4",
        domain_tags=("estimator_interface", "z_estimation", "asymptotic_normality"),
        natural_language=(
            "Apply the full Z-estimator route: differentiability, estimating "
            "equation, moment linearization, expansion, negligible remainder, "
            "and CLT imply asymptotic normality."
        ),
        lean_task=LeanTask(
            task_id="z_estimator_asymptotic_normal_route_seed",
            imports=("StatInference.Estimator.ZLinearization",),
            namespace="StatInference.Benchmarks",
            statement=(
                "example {Sample : Nat -> Type*} "
                "{Parameter Moment InfluenceFunction LinearPart Remainder : Type*} "
                "(route : StatInference.ZEstimatorAsymptoticNormalRoute "
                "Sample Parameter Moment InfluenceFunction LinearPart Remainder) "
                "(h_differentiability : route.linearization.differentiability_statement) "
                "(h_estimating_equation : route.linearization.estimating_equation_statement) "
                "(h_moment_linearization : route.linearization.moment_linearization_statement) "
                "(h_expansion : route.linearization.expansion.expansion_statement) "
                "(h_remainder : route.linearization.remainder_negligible.statement) "
                "(h_clt : route.clt.statement) : "
                "route.asymptotic_normality := by\n"
                "  exact StatInference.ZEstimatorAsymptoticNormalRoute.asymptoticNormal "
                "route h_differentiability h_estimating_equation "
                "h_moment_linearization h_expansion h_remainder h_clt"
            ),
            tags=("z_estimator", "linearization", "asymptotic_normality"),
            dependencies=(
                "StatInference.ZEstimatorAsymptoticNormalRoute.asymptoticNormal",
            ),
            expected_patterns=("exact",),
        ),
        expected_premises=(
            "StatInference.ZEstimatorAsymptoticNormalRoute.asymptoticNormal",
        ),
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
