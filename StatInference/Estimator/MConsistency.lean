import StatInference.Estimator.MEstimator

/-!
# M-estimator argmin consistency route

This module turns the deterministic M-estimator oracle inequality into an
asymptotic consistency statement: if the empirical-process deviation radius and
the approximate-argmin tolerance vanish, then the sample-path excess risk
against the oracle is eventually below every positive tolerance.
-/

namespace StatInference

open Filter
open scoped Topology

universe u v

/--
Proof-carrying route from approximate M-estimation plus uniform deviation to
argmin consistency along a concrete sample path.
-/
structure MEstimatorArgminConsistencyRoute
    (Sample : ℕ -> Type u) (Parameter : Type v) where
  interface : MEstimatorWithOracle Sample Parameter
  samples : ∀ n, Sample n
  deviation_tendsto_zero :
    Tendsto interface.uniform_deviation.deviation atTop (𝓝 0)
  tolerance_tendsto_zero :
    Tendsto interface.m_estimator.tolerance atTop (𝓝 0)

namespace MEstimatorArgminConsistencyRoute

/-- Excess risk of the M-estimator along the route's sample path. -/
def excessRiskSequence
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (route : MEstimatorArgminConsistencyRoute Sample Parameter) : ℕ -> ℝ :=
  fun n =>
    excessRisk route.interface.populationRisk route.interface.oracle
      (route.interface.m_estimator.estimate n (route.samples n))

/-- Deterministic upper bound from the oracle inequality. -/
def oracleBoundSequence
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (route : MEstimatorArgminConsistencyRoute Sample Parameter) : ℕ -> ℝ :=
  fun n =>
    2 * route.interface.uniform_deviation.deviation n +
      route.interface.m_estimator.tolerance n

/-- Project the route to the existing empirical-process oracle benchmark. -/
def toUniformDeviationOracleBenchmark
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (route : MEstimatorArgminConsistencyRoute Sample Parameter) :
    UniformDeviationOracleBenchmark Parameter :=
  route.interface.toUniformDeviationOracleBenchmark route.samples

/-- The deterministic oracle bound holds along the stored sample path. -/
theorem excessRiskBound
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (route : MEstimatorArgminConsistencyRoute Sample Parameter) :
    ∀ n, route.excessRiskSequence n ≤ route.oracleBoundSequence n := by
  intro n
  simpa [excessRiskSequence, oracleBoundSequence]
    using MEstimatorWithOracle.oracleExcessRiskBound
      route.interface n (route.samples n)

/-- The oracle bound vanishes when both the deviation radius and tolerance vanish. -/
theorem oracleBoundTendstoZero
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (route : MEstimatorArgminConsistencyRoute Sample Parameter) :
    Tendsto route.oracleBoundSequence atTop (𝓝 0) :=
  oracle_bound_tendsto_zero
    route.interface.m_estimator.tolerance
    route.interface.uniform_deviation.deviation
    route.deviation_tendsto_zero
    route.tolerance_tendsto_zero

/--
Argmin consistency conclusion: excess risk is eventually below any positive
tolerance along the stored sample path.
-/
theorem eventually_excessRisk_lt
    {Sample : ℕ -> Type u} {Parameter : Type v}
    (route : MEstimatorArgminConsistencyRoute Sample Parameter) :
    ∀ tolerance > 0,
      ∀ᶠ n in atTop, route.excessRiskSequence n < tolerance := by
  intro tolerance htolerance
  filter_upwards [route.oracleBoundTendstoZero.eventually_lt_const htolerance] with n h_bound
  exact lt_of_le_of_lt (route.excessRiskBound n) h_bound

end MEstimatorArgminConsistencyRoute

end StatInference
