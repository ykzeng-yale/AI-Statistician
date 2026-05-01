import StatInference.Estimator.Basic
import StatInference.EmpiricalProcess.Basic

/-!
# Abstract M-estimator interfaces

This file keeps M-estimation as a deterministic interface over the existing
estimator, oracle, and uniform-deviation layer.  It records approximate
empirical minimization as data and proves only projection/bridge lemmas from
that data.
-/

namespace StatInference

universe u v

/--
An abstract sample-size-indexed M-estimator.

The criterion is represented by an indexed empirical risk.  The only
statistical content recorded here is the deterministic approximate-minimizer
property with tolerance `tolerance n`.
-/
structure MEstimator (Sample : ℕ -> Type u) (Parameter : Type v) where
  empirical_risk : IndexedEmpiricalRisk Sample Parameter
  estimator : IndexedEstimator Sample Parameter
  tolerance : ℕ -> ℝ
  is_approximate_minimizer :
    ∀ n (sample : Sample n) (parameter : Parameter),
      empirical_risk.risk n sample (estimator.estimate n sample) ≤
        empirical_risk.risk n sample parameter + tolerance n

namespace MEstimator

/-- The finite-sample proposition asserting approximate empirical minimization. -/
def IsApproximateMinimizerAt {Sample : ℕ -> Type u} {Parameter : Type v}
    (mEstimator : MEstimator Sample Parameter) (n : ℕ)
    (sample : Sample n) : Prop :=
  ∀ parameter : Parameter,
    mEstimator.empirical_risk.risk n sample
        (mEstimator.estimator.estimate n sample) ≤
      mEstimator.empirical_risk.risk n sample parameter +
        mEstimator.tolerance n

/-- View an abstract M-estimator as the existing `ApproximateERM` interface. -/
def toApproximateERM {Sample : ℕ -> Type u} {Parameter : Type v}
    (mEstimator : MEstimator Sample Parameter) :
    ApproximateERM Sample Parameter where
  empirical_risk := mEstimator.empirical_risk
  estimator := mEstimator.estimator
  tolerance := mEstimator.tolerance
  is_approx_erm := mEstimator.is_approximate_minimizer

/-- The estimated parameter at sample size `n`. -/
def estimate {Sample : ℕ -> Type u} {Parameter : Type v}
    (mEstimator : MEstimator Sample Parameter) (n : ℕ)
    (sample : Sample n) : Parameter :=
  mEstimator.estimator.estimate n sample

/-- The empirical criterion at a fixed sample. -/
def empiricalRiskAt {Sample : ℕ -> Type u} {Parameter : Type v}
    (mEstimator : MEstimator Sample Parameter) (n : ℕ)
    (sample : Sample n) : Parameter -> ℝ :=
  mEstimator.empirical_risk.risk n sample

/-- Project the approximate-minimizer proposition at a fixed sample. -/
theorem approximateMinimizerAt {Sample : ℕ -> Type u} {Parameter : Type v}
    (mEstimator : MEstimator Sample Parameter) (n : ℕ)
    (sample : Sample n) :
    mEstimator.IsApproximateMinimizerAt n sample :=
  mEstimator.is_approximate_minimizer n sample

/-- Comparator-specific approximate-minimizer inequality. -/
theorem approximateMinimizer_le {Sample : ℕ -> Type u}
    {Parameter : Type v} (mEstimator : MEstimator Sample Parameter)
    (n : ℕ) (sample : Sample n) (comparator : Parameter) :
    mEstimator.empirical_risk.risk n sample (mEstimator.estimate n sample) ≤
      mEstimator.empirical_risk.risk n sample comparator +
        mEstimator.tolerance n :=
  mEstimator.is_approximate_minimizer n sample comparator

end MEstimator

/--
An M-estimator together with a population risk and a uniform-deviation bound.
This is the deterministic input needed for comparator oracle inequalities.
-/
structure MEstimatorWithUniformDeviation
    (Sample : ℕ -> Type u) (Parameter : Type v) where
  m_estimator : MEstimator Sample Parameter
  population_risk : PopulationRisk Parameter
  uniform_deviation :
    UniformDeviationBound population_risk m_estimator.empirical_risk

namespace MEstimatorWithUniformDeviation

/-- Project the underlying approximate-ERM interface. -/
def toApproximateERM {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithUniformDeviation Sample Parameter) :
    ApproximateERM Sample Parameter :=
  interface.m_estimator.toApproximateERM

/--
Project a sample path to the empirical-process oracle benchmark interface.
The resulting benchmark is deterministic and uses the provided samples.
-/
def toUniformDeviationOracleBenchmark
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithUniformDeviation Sample Parameter)
    (samples : ∀ n, Sample n) (comparator : Parameter) :
    UniformDeviationOracleBenchmark Parameter where
  populationRisk := interface.population_risk.risk
  empiricalRisk := fun n parameter =>
    interface.m_estimator.empirical_risk.risk n (samples n) parameter
  estimator := fun n =>
    interface.m_estimator.estimator.estimate n (samples n)
  comparator := comparator
  ermError := interface.m_estimator.tolerance
  deviation := interface.uniform_deviation.deviation
  uniform_deviation := fun n parameter =>
    interface.uniform_deviation.bound n (samples n) parameter
  approximateERM := fun n =>
    interface.m_estimator.is_approximate_minimizer n (samples n) comparator

/-- Deterministic excess-risk bound against an arbitrary comparator. -/
theorem excessRiskBound
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithUniformDeviation Sample Parameter) :
    ∀ n (sample : Sample n) (comparator : Parameter),
      excessRisk interface.population_risk comparator
          (interface.m_estimator.estimate n sample) ≤
        2 * interface.uniform_deviation.deviation n +
          interface.m_estimator.tolerance n :=
  approximateERM_excess_risk_bound_of_uniformDeviation
    interface.m_estimator.toApproximateERM
    interface.population_risk
    interface.uniform_deviation

end MEstimatorWithUniformDeviation

/--
An M-estimator equipped with an oracle risk and a uniform-deviation bound.
The oracle field is data; the resulting oracle inequality is a deterministic
projection from the existing `ApproximateERM` theorem.
-/
structure MEstimatorWithOracle
    (Sample : ℕ -> Type u) (Parameter : Type v) where
  m_estimator : MEstimator Sample Parameter
  oracle_risk : OracleRisk Parameter
  uniform_deviation :
    UniformDeviationBound oracle_risk.population_risk
      m_estimator.empirical_risk

namespace MEstimatorWithOracle

/-- Forget the oracle and keep only population risk plus uniform deviation. -/
def toUniformDeviationInterface
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithOracle Sample Parameter) :
    MEstimatorWithUniformDeviation Sample Parameter where
  m_estimator := interface.m_estimator
  population_risk := interface.oracle_risk.population_risk
  uniform_deviation := interface.uniform_deviation

/-- Project the underlying approximate-ERM interface. -/
def toApproximateERM {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithOracle Sample Parameter) :
    ApproximateERM Sample Parameter :=
  interface.m_estimator.toApproximateERM

/-- Project the oracle parameter. -/
def oracle {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithOracle Sample Parameter) : Parameter :=
  interface.oracle_risk.oracle

/-- Project the population risk. -/
def populationRisk {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithOracle Sample Parameter) :
    PopulationRisk Parameter :=
  interface.oracle_risk.population_risk

/-- The oracle is a population-risk minimizer. -/
theorem oracle_minimizes {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithOracle Sample Parameter)
    (parameter : Parameter) :
    interface.populationRisk.risk interface.oracle ≤
      interface.populationRisk.risk parameter :=
  interface.oracle_risk.is_oracle parameter

/--
Project a sample path to the empirical-process oracle benchmark interface,
using the stored oracle as comparator.
-/
def toUniformDeviationOracleBenchmark
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithOracle Sample Parameter)
    (samples : ∀ n, Sample n) :
    UniformDeviationOracleBenchmark Parameter :=
  interface.toUniformDeviationInterface.toUniformDeviationOracleBenchmark
    samples interface.oracle

/-- Deterministic excess-risk bound relative to the stored oracle. -/
theorem oracleExcessRiskBound
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (interface : MEstimatorWithOracle Sample Parameter) :
    ∀ n (sample : Sample n),
      excessRisk interface.populationRisk interface.oracle
          (interface.m_estimator.estimate n sample) ≤
        2 * interface.uniform_deviation.deviation n +
          interface.m_estimator.tolerance n :=
  approximateERM_oracle_excess_risk_bound
    interface.m_estimator.toApproximateERM
    interface.oracle_risk
    interface.uniform_deviation.deviation
    interface.uniform_deviation.bound

end MEstimatorWithOracle

end StatInference
