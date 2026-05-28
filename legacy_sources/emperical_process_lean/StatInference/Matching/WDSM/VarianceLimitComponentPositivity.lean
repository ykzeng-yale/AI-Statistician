import StatInference.Matching.WDSM.PATTVarianceAlgebra

/-!
# Componentwise positivity for limiting WDSM variance formulas

This module packages the scalar positivity facts for limiting variance
formulas.  These are the limit-side companions to the eventual sample-side
positivity bridges in `WaldStandardErrorPositivity`.
-/

namespace StatInference
namespace Matching
namespace WDSM

/-! ## Oracle and estimated-score limits -/

/--
A positive heterogeneity limit and nonnegative residual-variance limit make the
oracle limiting variance positive.
-/
theorem oracleVarianceLimit_pos_of_heterogeneity_pos
    (heterogeneityLimit residualLimit : Real)
    (hheterogeneity_pos : 0 < heterogeneityLimit)
    (hresidual_nonneg : 0 ≤ residualLimit) :
    0 < oracleVariance heterogeneityLimit residualLimit := by
  exact oracleVariance_pos_of_heterogeneity_pos_of_residual_nonneg
    heterogeneityLimit residualLimit hheterogeneity_pos hresidual_nonneg

/--
A nonnegative heterogeneity limit and positive residual-variance limit make the
oracle limiting variance positive.
-/
theorem oracleVarianceLimit_pos_of_residual_pos
    (heterogeneityLimit residualLimit : Real)
    (hheterogeneity_nonneg : 0 ≤ heterogeneityLimit)
    (hresidual_pos : 0 < residualLimit) :
    0 < oracleVariance heterogeneityLimit residualLimit := by
  exact oracleVariance_pos_of_residual_pos_of_heterogeneity_nonneg
    heterogeneityLimit residualLimit hheterogeneity_nonneg hresidual_pos

/--
Strict projection slack makes the fixed-law estimated-score limiting variance
positive.
-/
theorem fixedLawEstimatedScoreVarianceLimit_pos_of_projection_lt_oracle
    (oracleLimit projectionLimit : Real)
    (hprojection_lt_oracle : projectionLimit < oracleLimit) :
    0 < estimatedScoreVariance oracleLimit projectionLimit 0 := by
  exact fixedLawEstimatedScoreVariance_pos_of_projection_lt_oracle
    oracleLimit projectionLimit hprojection_lt_oracle

/--
Strict projection slack plus nonnegative moving-target drift makes the
changing-law estimated-score limiting variance positive.
-/
theorem estimatedScoreVarianceLimit_pos_of_projection_lt_oracle_of_drift_nonneg
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (hprojection_lt_oracle : projectionLimit < oracleLimit)
    (hdrift_nonneg : 0 ≤ targetDriftLimit) :
    0 < estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit := by
  exact changingTargetVariance_pos_of_projection_lt_oracle_of_drift_nonneg
    oracleLimit projectionLimit targetDriftLimit hprojection_lt_oracle
    hdrift_nonneg

/--
Weak projection slack plus positive moving-target drift makes the changing-law
estimated-score limiting variance positive.
-/
theorem estimatedScoreVarianceLimit_pos_of_projection_le_oracle_of_drift_pos
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (hprojection_le_oracle : projectionLimit ≤ oracleLimit)
    (hdrift_pos : 0 < targetDriftLimit) :
    0 < estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit := by
  exact changingTargetVariance_pos_of_projection_le_oracle_of_drift_pos
    oracleLimit projectionLimit targetDriftLimit hprojection_le_oracle
    hdrift_pos

/-! ## Two-arm and PATT residual-variance limits -/

/--
Positive treated share and treated residual-variance limits make the two-arm
residual limiting variance positive under nonzero denominator and nonnegative
control-side limits.
-/
theorem twoArmWeightedResidualVarianceLimit_pos_of_treated_pos
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (hdenominator : denominatorLimit ≠ 0)
    (htreatedShare : 0 < treatedShareLimit)
    (hcontrolShare : 0 ≤ controlShareLimit)
    (htreatedVariance : 0 < treatedVarianceLimit)
    (hcontrolVariance : 0 ≤ controlVarianceLimit) :
    0 < twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit := by
  exact twoArmWeightedResidualVariance_pos_of_treated_pos
    denominatorLimit treatedShareLimit controlShareLimit treatedVarianceLimit
    controlVarianceLimit hdenominator htreatedShare hcontrolShare
    htreatedVariance hcontrolVariance

/--
Positive control share and control residual-variance limits make the two-arm
residual limiting variance positive under nonzero denominator and nonnegative
treated-side limits.
-/
theorem twoArmWeightedResidualVarianceLimit_pos_of_control_pos
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (hdenominator : denominatorLimit ≠ 0)
    (htreatedShare : 0 ≤ treatedShareLimit)
    (hcontrolShare : 0 < controlShareLimit)
    (htreatedVariance : 0 ≤ treatedVarianceLimit)
    (hcontrolVariance : 0 < controlVarianceLimit) :
    0 < twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit := by
  exact twoArmWeightedResidualVariance_pos_of_control_pos
    denominatorLimit treatedShareLimit controlShareLimit treatedVarianceLimit
    controlVarianceLimit hdenominator htreatedShare hcontrolShare
    htreatedVariance hcontrolVariance

/--
Positive treated share and treated direct residual-variance limits make the
PATT residual limiting variance positive under nonzero denominator and
nonnegative matched-control-side limits.
-/
theorem pattWeightedResidualVarianceLimit_pos_of_treated_pos
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (hdenominator : denominatorLimit ≠ 0)
    (htreatedShare : 0 < treatedShareLimit)
    (hcontrolShare : 0 ≤ controlShareLimit)
    (htreatedVariance : 0 < treatedDirectVarianceLimit)
    (hcontrolVariance : 0 ≤ matchedControlVarianceLimit) :
    0 < pattWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit
      matchedControlVarianceLimit := by
  exact pattWeightedResidualVariance_pos_of_treated_pos denominatorLimit
    treatedShareLimit controlShareLimit treatedDirectVarianceLimit
    matchedControlVarianceLimit hdenominator htreatedShare hcontrolShare
    htreatedVariance hcontrolVariance

/--
Positive control share and matched-control residual-variance limits make the
PATT residual limiting variance positive under nonzero denominator and
nonnegative treated-side limits.
-/
theorem pattWeightedResidualVarianceLimit_pos_of_control_pos
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (hdenominator : denominatorLimit ≠ 0)
    (htreatedShare : 0 ≤ treatedShareLimit)
    (hcontrolShare : 0 < controlShareLimit)
    (htreatedVariance : 0 ≤ treatedDirectVarianceLimit)
    (hcontrolVariance : 0 < matchedControlVarianceLimit) :
    0 < pattWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit
      matchedControlVarianceLimit := by
  exact pattWeightedResidualVariance_pos_of_control_pos denominatorLimit
    treatedShareLimit controlShareLimit treatedDirectVarianceLimit
    matchedControlVarianceLimit hdenominator htreatedShare hcontrolShare
    htreatedVariance hcontrolVariance

end WDSM
end Matching
end StatInference
