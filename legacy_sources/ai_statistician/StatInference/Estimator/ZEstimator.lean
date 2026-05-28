import StatInference.Estimator.MEstimator

/-!
# Abstract Z-estimator interfaces

This file represents Z-estimation through estimating equations and a
real-valued discrepancy applied to their values.  All deterministic oracle
statements are obtained by converting the residual criterion to the
M-estimator layer.
-/

namespace StatInference

universe u v w

/-- Population estimating equation or moment map. -/
structure PopulationMoment (Parameter : Type v) (Moment : Type w) where
  moment : Parameter -> Moment

/-- Sample-size-indexed empirical estimating equation or moment map. -/
structure IndexedEmpiricalMoment
    (Sample : ℕ -> Type u) (Parameter : Type v) (Moment : Type w) where
  moment : ∀ n, Sample n -> Parameter -> Moment

/--
A real-valued discrepancy for moments.  Concrete developments may instantiate
this with a norm, squared norm, maximum coordinate residual, or another
criterion.
-/
structure MomentDiscrepancy (Moment : Type w) where
  value : Moment -> ℝ

namespace PopulationMoment

/-- Convert a population moment plus discrepancy into a population risk. -/
def toPopulationRisk {Parameter : Type v} {Moment : Type w}
    (population_moment : PopulationMoment Parameter Moment)
    (discrepancy : MomentDiscrepancy Moment) :
    PopulationRisk Parameter where
  risk parameter := discrepancy.value (population_moment.moment parameter)

end PopulationMoment

/-- Population Z-root proposition induced by a discrepancy criterion. -/
def IsPopulationZRoot {Parameter : Type v} {Moment : Type w}
    (population_moment : PopulationMoment Parameter Moment)
    (discrepancy : MomentDiscrepancy Moment) (root : Parameter) : Prop :=
  ∀ parameter : Parameter,
    discrepancy.value (population_moment.moment root) ≤
      discrepancy.value (population_moment.moment parameter)

/--
An abstract sample-size-indexed Z-estimator.

The estimator is required to approximately minimize the empirical discrepancy
of the estimating equation.  No algebraic or probabilistic structure on
`Moment` is assumed.
-/
structure ZEstimator
    (Sample : ℕ -> Type u) (Parameter : Type v) (Moment : Type w) where
  empirical_moment : IndexedEmpiricalMoment Sample Parameter Moment
  discrepancy : MomentDiscrepancy Moment
  estimator : IndexedEstimator Sample Parameter
  tolerance : ℕ -> ℝ
  is_approximate_solution :
    ∀ n (sample : Sample n) (parameter : Parameter),
      discrepancy.value
          (empirical_moment.moment n sample (estimator.estimate n sample)) ≤
        discrepancy.value (empirical_moment.moment n sample parameter) +
          tolerance n

namespace ZEstimator

/-- The finite-sample proposition asserting approximate empirical Z-solution. -/
def IsApproximateSolutionAt
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (zEstimator : ZEstimator Sample Parameter Moment) (n : ℕ)
    (sample : Sample n) : Prop :=
  ∀ parameter : Parameter,
    zEstimator.discrepancy.value
        (zEstimator.empirical_moment.moment n sample
          (zEstimator.estimator.estimate n sample)) ≤
      zEstimator.discrepancy.value
          (zEstimator.empirical_moment.moment n sample parameter) +
        zEstimator.tolerance n

/-- The estimated parameter at sample size `n`. -/
def estimate {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (zEstimator : ZEstimator Sample Parameter Moment) (n : ℕ)
    (sample : Sample n) : Parameter :=
  zEstimator.estimator.estimate n sample

/-- Convert the empirical estimating equation to an empirical risk. -/
def toIndexedEmpiricalRisk
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (zEstimator : ZEstimator Sample Parameter Moment) :
    IndexedEmpiricalRisk Sample Parameter where
  risk n sample parameter :=
    zEstimator.discrepancy.value
      (zEstimator.empirical_moment.moment n sample parameter)

/-- Convert a Z-estimator to the M-estimator interface for its residual criterion. -/
def toMEstimator
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (zEstimator : ZEstimator Sample Parameter Moment) :
    MEstimator Sample Parameter where
  empirical_risk := zEstimator.toIndexedEmpiricalRisk
  estimator := zEstimator.estimator
  tolerance := zEstimator.tolerance
  is_approximate_minimizer := zEstimator.is_approximate_solution

/-- Empirical residual criterion at a fixed sample. -/
def empiricalResidualAt
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (zEstimator : ZEstimator Sample Parameter Moment) (n : ℕ)
    (sample : Sample n) : Parameter -> ℝ :=
  zEstimator.toIndexedEmpiricalRisk.risk n sample

/-- Project the approximate-solution proposition at a fixed sample. -/
theorem approximateSolutionAt
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (zEstimator : ZEstimator Sample Parameter Moment) (n : ℕ)
    (sample : Sample n) :
    zEstimator.IsApproximateSolutionAt n sample :=
  zEstimator.is_approximate_solution n sample

/-- Comparator-specific approximate empirical Z-solution inequality. -/
theorem approximateSolution_le
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (zEstimator : ZEstimator Sample Parameter Moment) (n : ℕ)
    (sample : Sample n) (comparator : Parameter) :
    zEstimator.discrepancy.value
        (zEstimator.empirical_moment.moment n sample
          (zEstimator.estimate n sample)) ≤
      zEstimator.discrepancy.value
          (zEstimator.empirical_moment.moment n sample comparator) +
        zEstimator.tolerance n :=
  zEstimator.is_approximate_solution n sample comparator

end ZEstimator

/--
A Z-estimator with population moment and a uniform-deviation bound for the
induced residual risk.
-/
structure ZEstimatorWithUniformDeviation
    (Sample : ℕ -> Type u) (Parameter : Type v) (Moment : Type w) where
  z_estimator : ZEstimator Sample Parameter Moment
  population_moment : PopulationMoment Parameter Moment
  uniform_deviation :
    UniformDeviationBound
      (population_moment.toPopulationRisk z_estimator.discrepancy)
      z_estimator.toIndexedEmpiricalRisk

namespace ZEstimatorWithUniformDeviation

/-- Population residual risk induced by the population moment and discrepancy. -/
def populationRisk
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithUniformDeviation Sample Parameter Moment) :
    PopulationRisk Parameter :=
  interface.population_moment.toPopulationRisk
    interface.z_estimator.discrepancy

/-- Convert to the M-estimator uniform-deviation interface. -/
def toMEstimatorWithUniformDeviation
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithUniformDeviation Sample Parameter Moment) :
    MEstimatorWithUniformDeviation Sample Parameter where
  m_estimator := interface.z_estimator.toMEstimator
  population_risk := interface.populationRisk
  uniform_deviation := interface.uniform_deviation

/-- Deterministic excess-residual-risk bound against an arbitrary comparator. -/
theorem excessRiskBound
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithUniformDeviation Sample Parameter Moment) :
    ∀ n (sample : Sample n) (comparator : Parameter),
      excessRisk interface.populationRisk comparator
          (interface.z_estimator.estimate n sample) ≤
        2 * interface.uniform_deviation.deviation n +
          interface.z_estimator.tolerance n := by
  simpa [toMEstimatorWithUniformDeviation, populationRisk,
    ZEstimator.toMEstimator, ZEstimator.estimate]
    using
      (MEstimatorWithUniformDeviation.excessRiskBound
        interface.toMEstimatorWithUniformDeviation)

end ZEstimatorWithUniformDeviation

/--
A Z-estimator with a population Z-root and a uniform-deviation bound for the
induced residual criterion.
-/
structure ZEstimatorWithOracle
    (Sample : ℕ -> Type u) (Parameter : Type v) (Moment : Type w) where
  z_estimator : ZEstimator Sample Parameter Moment
  population_moment : PopulationMoment Parameter Moment
  oracle : Parameter
  is_oracle :
    IsPopulationZRoot population_moment z_estimator.discrepancy oracle
  uniform_deviation :
    UniformDeviationBound
      (population_moment.toPopulationRisk z_estimator.discrepancy)
      z_estimator.toIndexedEmpiricalRisk

namespace ZEstimatorWithOracle

/-- Population residual risk induced by the population moment and discrepancy. -/
def populationRisk
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithOracle Sample Parameter Moment) :
    PopulationRisk Parameter :=
  interface.population_moment.toPopulationRisk
    interface.z_estimator.discrepancy

/-- Convert the population Z-root to the existing oracle-risk interface. -/
def toOracleRisk
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithOracle Sample Parameter Moment) :
    OracleRisk Parameter where
  population_risk := interface.populationRisk
  oracle := interface.oracle
  is_oracle := interface.is_oracle

/-- Forget the oracle and keep only population risk plus uniform deviation. -/
def toUniformDeviationInterface
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithOracle Sample Parameter Moment) :
    ZEstimatorWithUniformDeviation Sample Parameter Moment where
  z_estimator := interface.z_estimator
  population_moment := interface.population_moment
  uniform_deviation := interface.uniform_deviation

/-- Convert to the M-estimator oracle interface. -/
def toMEstimatorWithOracle
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithOracle Sample Parameter Moment) :
    MEstimatorWithOracle Sample Parameter where
  m_estimator := interface.z_estimator.toMEstimator
  oracle_risk := interface.toOracleRisk
  uniform_deviation := interface.uniform_deviation

/-- The stored oracle minimizes the induced population residual risk. -/
theorem oracle_minimizes
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithOracle Sample Parameter Moment)
    (parameter : Parameter) :
    interface.populationRisk.risk interface.oracle ≤
      interface.populationRisk.risk parameter :=
  interface.is_oracle parameter

/-- Deterministic excess-residual-risk bound relative to the stored oracle. -/
theorem oracleExcessRiskBound
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    (interface : ZEstimatorWithOracle Sample Parameter Moment) :
    ∀ n (sample : Sample n),
      excessRisk interface.populationRisk interface.oracle
          (interface.z_estimator.estimate n sample) ≤
        2 * interface.uniform_deviation.deviation n +
          interface.z_estimator.tolerance n := by
  simpa [toMEstimatorWithOracle, toOracleRisk, populationRisk,
    ZEstimator.toMEstimator, ZEstimator.estimate]
    using
      (MEstimatorWithOracle.oracleExcessRiskBound
        interface.toMEstimatorWithOracle)

end ZEstimatorWithOracle

end StatInference
