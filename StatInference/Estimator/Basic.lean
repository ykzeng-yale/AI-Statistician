import StatInference.Asymptotics.Basic

/-!
# Estimator interfaces
-/

namespace StatInference

universe u v w

/-- A concrete finite sample of observations, carrying its sample size. -/
structure FiniteSample (Observation : Type u) where
  size : ℕ
  observation : Fin size -> Observation

/-- The type of samples of a fixed size `n`. -/
abbrev SampleAt (Observation : Type u) (n : ℕ) : Type u :=
  Fin n -> Observation

/-- View a bundled finite sample as an element of its fixed-size sample type. -/
def FiniteSample.toSampleAt {Observation : Type u} (sample : FiniteSample Observation) :
    SampleAt Observation sample.size :=
  sample.observation

/-- A family of sample spaces indexed by sample size. -/
structure SampleFamily where
  sample : ℕ -> Type u

/-- The standard fixed-size product sample family `Fin n -> Observation`. -/
def productSampleFamily (Observation : Type u) : SampleFamily.{u} where
  sample := fun n => SampleAt Observation n

/-- A finite-sample estimator from samples to parameters. -/
structure Estimator (Sample Parameter : Type*) where
  estimate : Sample -> Parameter

/-- A sequence of estimators indexed by sample size. -/
structure EstimatorSequence (Sample Parameter : Type*) where
  estimate : ℕ -> Sample -> Parameter

/-- An estimator at a fixed sample size for an indexed sample family. -/
structure EstimatorAt (Sample : ℕ -> Type u) (Parameter : Type v) (n : ℕ) where
  estimate : Sample n -> Parameter

/-- A sample-size-indexed estimator whose domain may depend on `n`. -/
structure IndexedEstimator (Sample : ℕ -> Type u) (Parameter : Type v) where
  estimate : ∀ n, Sample n -> Parameter

/-- Extract the `n`th fixed-size estimator from an indexed estimator. -/
def IndexedEstimator.at {Sample : ℕ -> Type u} {Parameter : Type v}
    (estimator : IndexedEstimator Sample Parameter) (n : ℕ) :
    EstimatorAt Sample Parameter n where
  estimate := estimator.estimate n

/-- A classical estimator sequence is an indexed estimator over a constant sample space. -/
def EstimatorSequence.toIndexedEstimator {Sample : Type u} {Parameter : Type v}
    (estimator : EstimatorSequence Sample Parameter) :
    IndexedEstimator (fun _ => Sample) Parameter where
  estimate n sample := estimator.estimate n sample

/-- A target parameter functional. -/
structure TargetParameter (Model Parameter : Type*) where
  value : Model -> Parameter

/-- Population risk for a candidate decision, predictor, or parameter. -/
structure PopulationRisk (Candidate : Type u) where
  risk : Candidate -> ℝ

/-- Empirical risk over a fixed sample space. -/
structure EmpiricalRisk (Sample : Type u) (Candidate : Type v) where
  risk : Sample -> Candidate -> ℝ

/-- Empirical risk over a sample-size-indexed family of sample spaces. -/
structure IndexedEmpiricalRisk (Sample : ℕ -> Type u) (Candidate : Type v) where
  risk : ∀ n, Sample n -> Candidate -> ℝ

/-- An approximate empirical risk minimizer with deterministic tolerance `tolerance n`. -/
structure ApproximateERM (Sample : ℕ -> Type u) (Candidate : Type v) where
  empirical_risk : IndexedEmpiricalRisk Sample Candidate
  estimator : IndexedEstimator Sample Candidate
  tolerance : ℕ -> ℝ
  is_approx_erm :
    ∀ n (sample : Sample n) (candidate : Candidate),
      empirical_risk.risk n sample (estimator.estimate n sample) ≤
        empirical_risk.risk n sample candidate + tolerance n

/-- A uniform deviation bound comparing empirical and population risks. -/
structure UniformDeviationBound {Sample : ℕ -> Type u} {Candidate : Type v}
    (population_risk : PopulationRisk Candidate)
    (empirical_risk : IndexedEmpiricalRisk Sample Candidate) where
  deviation : ℕ -> ℝ
  bound :
    ∀ n (sample : Sample n) (candidate : Candidate),
      |empirical_risk.risk n sample candidate - population_risk.risk candidate| ≤
        deviation n

/-- A population-risk oracle, represented by a minimizer of the population risk. -/
structure OracleRisk (Candidate : Type u) where
  population_risk : PopulationRisk Candidate
  oracle : Candidate
  is_oracle : ∀ candidate, population_risk.risk oracle ≤ population_risk.risk candidate

/-- Excess risk of `candidate` relative to a comparator. -/
def excessRisk {Candidate : Type u} (population_risk : PopulationRisk Candidate)
    (comparator candidate : Candidate) : ℝ :=
  population_risk.risk candidate - population_risk.risk comparator

/--
Deterministic oracle inequality for an indexed approximate ERM under a uniform
deviation bound, stated relative to an arbitrary comparator.
-/
theorem approximateERM_excess_risk_bound
    {Sample : ℕ -> Type u} {Candidate : Type v}
    (erm : ApproximateERM Sample Candidate)
    (population_risk : PopulationRisk Candidate)
    (deviation : ℕ -> ℝ)
    (h_uniform :
      ∀ n (sample : Sample n) (candidate : Candidate),
        |erm.empirical_risk.risk n sample candidate - population_risk.risk candidate| ≤
          deviation n) :
    ∀ n (sample : Sample n) (comparator : Candidate),
      excessRisk population_risk comparator (erm.estimator.estimate n sample) ≤
        2 * deviation n + erm.tolerance n := by
  intro n sample comparator
  simpa [excessRisk] using
    (excess_risk_bound_of_uniform_deviation
      population_risk.risk
      (erm.empirical_risk.risk n sample)
      (erm.estimator.estimate n sample)
      comparator
      (erm.tolerance n)
      (deviation n)
      (h_uniform n sample)
      (erm.is_approx_erm n sample comparator))

/-- Oracle-risk version of `approximateERM_excess_risk_bound`. -/
theorem approximateERM_oracle_excess_risk_bound
    {Sample : ℕ -> Type u} {Candidate : Type v}
    (erm : ApproximateERM Sample Candidate)
    (oracle_risk : OracleRisk Candidate)
    (deviation : ℕ -> ℝ)
    (h_uniform :
      ∀ n (sample : Sample n) (candidate : Candidate),
        |erm.empirical_risk.risk n sample candidate -
            oracle_risk.population_risk.risk candidate| ≤ deviation n) :
    ∀ n (sample : Sample n),
      excessRisk oracle_risk.population_risk oracle_risk.oracle
          (erm.estimator.estimate n sample) ≤
        2 * deviation n + erm.tolerance n := by
  intro n sample
  exact approximateERM_excess_risk_bound erm oracle_risk.population_risk deviation
    h_uniform n sample oracle_risk.oracle

/-- Oracle inequality packaged from a `UniformDeviationBound`. -/
theorem approximateERM_excess_risk_bound_of_uniformDeviation
    {Sample : ℕ -> Type u} {Candidate : Type v}
    (erm : ApproximateERM Sample Candidate)
    (population_risk : PopulationRisk Candidate)
    (uniform :
      UniformDeviationBound population_risk erm.empirical_risk) :
    ∀ n (sample : Sample n) (comparator : Candidate),
      excessRisk population_risk comparator (erm.estimator.estimate n sample) ≤
        2 * uniform.deviation n + erm.tolerance n :=
  approximateERM_excess_risk_bound erm population_risk uniform.deviation uniform.bound

end StatInference
