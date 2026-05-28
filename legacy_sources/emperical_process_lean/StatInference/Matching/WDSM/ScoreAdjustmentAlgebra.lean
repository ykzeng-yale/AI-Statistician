import StatInference.Matching.WDSM.ResidualVarianceAlgebra
import StatInference.Matching.WDSM.VarianceAlgebra

/-!
# Estimated-score adjustment algebra for WDSM

The WDSM appendix writes the estimated-score variance corrections as quadratic
forms such as `gamma^T Sigma gamma`.  This module records the finite algebraic
version of those corrections before any first-step CLT, LAN expansion, or
Godambe identity is proved.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Param : Type*} [DecidableEq Param]

/-- Finite score-adjustment quadratic form `gamma^T Sigma gamma`. -/
noncomputable def scoreQuadraticForm (parameters : Finset Param)
    (loading : Param -> Real) (covariance : Param -> Param -> Real) : Real :=
  ∑ left ∈ parameters, ∑ right ∈ parameters,
    loading left * loading right * covariance left right

omit [DecidableEq Param] in
/-- The score quadratic form is the same finite covariance form used for residual arrays. -/
theorem scoreQuadraticForm_eq_linearCovarianceVariation
    (parameters : Finset Param)
    (loading : Param -> Real) (covariance : Param -> Param -> Real) :
    scoreQuadraticForm parameters loading covariance =
      linearCovarianceVariation parameters loading covariance := by
  rfl

/-- A diagonal score covariance reduces the score quadratic form to a quadratic variation. -/
theorem scoreQuadraticForm_diagonal_eq_quadraticVariation
    (parameters : Finset Param) (loading variance : Param -> Real) :
    scoreQuadraticForm parameters loading
        (fun left right => if left = right then variance left else 0) =
      quadraticVariation parameters loading variance := by
  rw [scoreQuadraticForm_eq_linearCovarianceVariation]
  exact linearCovarianceVariation_diagonal_eq_quadraticVariation
    parameters loading variance

omit [DecidableEq Param] in
/-- Zero first-step loading gives zero score-adjustment quadratic form. -/
theorem scoreQuadraticForm_zero_loading
    (parameters : Finset Param) (covariance : Param -> Param -> Real) :
    scoreQuadraticForm parameters (fun _param => (0 : Real)) covariance = 0 := by
  unfold scoreQuadraticForm
  exact Finset.sum_eq_zero
    (fun left _hleft =>
      Finset.sum_eq_zero
        (fun right _hright => by ring))

/-- Fixed-law estimated-score variance using a score quadratic-form reduction. -/
noncomputable def fixedLawScoreAdjustedVariance
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real) : Real :=
  estimatedScoreVariance oracleVariance
    (scoreQuadraticForm parameters firstStepLoading scoreCovariance) 0

/-- Changing-law estimated-score variance with projection and target-drift quadratic forms. -/
noncomputable def changingLawScoreAdjustedVariance
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real) : Real :=
  estimatedScoreVariance oracleVariance
    (scoreQuadraticForm parameters firstStepLoading scoreCovariance)
    (scoreQuadraticForm parameters targetDriftLoading scoreCovariance)

omit [DecidableEq Param] in
/-- Fixed-law score-adjusted variance has the appendix form `V_or - gamma_1^T Sigma gamma_1`. -/
theorem fixedLawScoreAdjustedVariance_eq
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real) :
    fixedLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading scoreCovariance =
      oracleVariance -
        scoreQuadraticForm parameters firstStepLoading scoreCovariance := by
  unfold fixedLawScoreAdjustedVariance
  rw [fixedLawEstimatedScoreVariance_eq]

omit [DecidableEq Param] in
/--
Changing-law score-adjusted variance is the fixed-law variance plus the
target-drift quadratic form.
-/
theorem changingLawScoreAdjustedVariance_eq_fixed_plus_drift
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real) :
    changingLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading targetDriftLoading scoreCovariance =
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance +
        scoreQuadraticForm parameters targetDriftLoading scoreCovariance := by
  unfold changingLawScoreAdjustedVariance fixedLawScoreAdjustedVariance
  exact changingTargetVariance_eq_fixedLaw_plus_drift
    oracleVariance
    (scoreQuadraticForm parameters firstStepLoading scoreCovariance)
    (scoreQuadraticForm parameters targetDriftLoading scoreCovariance)

omit [DecidableEq Param] in
/-- If the target-drift loading is zero, changing-law and fixed-law targets coincide. -/
theorem changingLawScoreAdjustedVariance_eq_fixed_of_zero_drift_loading
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hzero : ∀ param, param ∈ parameters -> targetDriftLoading param = 0) :
    changingLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading targetDriftLoading scoreCovariance =
      fixedLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading scoreCovariance := by
  have hdrift :
      scoreQuadraticForm parameters targetDriftLoading scoreCovariance = 0 := by
    unfold scoreQuadraticForm
    exact Finset.sum_eq_zero
      (fun left hleft =>
        Finset.sum_eq_zero
          (fun right _hright => by
            rw [hzero left hleft]
            ring))
  rw [changingLawScoreAdjustedVariance_eq_fixed_plus_drift]
  rw [hdrift]
  ring

/-- A diagonal score covariance with nonnegative variances gives a nonnegative quadratic form. -/
theorem scoreQuadraticForm_diagonal_nonneg
    (parameters : Finset Param) (loading variance : Param -> Real)
    (hvariance : ∀ param, param ∈ parameters -> 0 ≤ variance param) :
    0 ≤ scoreQuadraticForm parameters loading
      (fun left right => if left = right then variance left else 0) := by
  rw [scoreQuadraticForm_diagonal_eq_quadraticVariation]
  exact quadraticVariation_nonneg parameters loading variance hvariance

omit [DecidableEq Param] in
/-- Zero first-step loading leaves the fixed-law variance equal to the oracle variance. -/
theorem fixedLawScoreAdjustedVariance_eq_oracle_of_zero_loading
    (parameters : Finset Param) (oracleVariance : Real)
    (scoreCovariance : Param -> Param -> Real) :
    fixedLawScoreAdjustedVariance parameters oracleVariance
        (fun _param => (0 : Real)) scoreCovariance =
      oracleVariance := by
  rw [fixedLawScoreAdjustedVariance_eq]
  rw [scoreQuadraticForm_zero_loading]
  ring

/--
Under diagonal nonnegative score covariance, the fixed-law estimated-score
variance does not exceed the oracle variance.
-/
theorem fixedLawScoreAdjustedVariance_le_oracle_of_diagonal_nonneg
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading variance : Param -> Real)
    (hvariance : ∀ param, param ∈ parameters -> 0 ≤ variance param) :
    fixedLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading
        (fun left right => if left = right then variance left else 0) ≤
      oracleVariance := by
  unfold fixedLawScoreAdjustedVariance
  exact fixedLawEstimatedScoreVariance_le_oracle oracleVariance
    (scoreQuadraticForm parameters firstStepLoading
      (fun left right => if left = right then variance left else 0))
    (scoreQuadraticForm_diagonal_nonneg parameters firstStepLoading variance
      hvariance)

omit [DecidableEq Param] in
/--
If the fixed-law projection quadratic form is bounded by the oracle variance,
the fixed-law adjusted variance is nonnegative.
-/
theorem fixedLawScoreAdjustedVariance_nonneg_of_score_le_oracle
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hscore_le_oracle :
      scoreQuadraticForm parameters firstStepLoading scoreCovariance ≤
        oracleVariance) :
    0 ≤ fixedLawScoreAdjustedVariance parameters oracleVariance
      firstStepLoading scoreCovariance := by
  unfold fixedLawScoreAdjustedVariance
  exact fixedLawEstimatedScoreVariance_nonneg_of_projection_le_oracle
    oracleVariance
    (scoreQuadraticForm parameters firstStepLoading scoreCovariance)
    hscore_le_oracle

/--
Under diagonal nonnegative score covariance and a projection bound, the
fixed-law adjusted variance lies between zero and the oracle variance.
-/
theorem fixedLawScoreAdjustedVariance_between_zero_and_oracle_of_diagonal_nonneg
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading variance : Param -> Real)
    (hvariance : ∀ param, param ∈ parameters -> 0 ≤ variance param)
    (hscore_le_oracle :
      scoreQuadraticForm parameters firstStepLoading
          (fun left right => if left = right then variance left else 0) ≤
        oracleVariance) :
    0 ≤ fixedLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading
        (fun left right => if left = right then variance left else 0) ∧
      fixedLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading
        (fun left right => if left = right then variance left else 0) ≤
          oracleVariance := by
  constructor
  · exact fixedLawScoreAdjustedVariance_nonneg_of_score_le_oracle
      parameters oracleVariance firstStepLoading
      (fun left right => if left = right then variance left else 0)
      hscore_le_oracle
  · exact fixedLawScoreAdjustedVariance_le_oracle_of_diagonal_nonneg
      parameters oracleVariance firstStepLoading variance hvariance

/--
Under diagonal nonnegative score covariance, a changing-law target-drift
quadratic form cannot decrease the fixed-law variance.
-/
theorem fixedLawScoreAdjustedVariance_le_changingLaw_of_diagonal_nonneg_drift
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading variance : Param -> Real)
    (hvariance : ∀ param, param ∈ parameters -> 0 ≤ variance param) :
    fixedLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading
        (fun left right => if left = right then variance left else 0) ≤
      changingLawScoreAdjustedVariance parameters oracleVariance
        firstStepLoading targetDriftLoading
        (fun left right => if left = right then variance left else 0) := by
  rw [changingLawScoreAdjustedVariance_eq_fixed_plus_drift]
  exact le_add_of_nonneg_right
    (scoreQuadraticForm_diagonal_nonneg parameters targetDriftLoading variance
      hvariance)

/--
Under diagonal nonnegative score covariance, a bounded fixed-law projection
and nonnegative target-drift quadratic form give a nonnegative changing-law
adjusted variance.
-/
theorem changingLawScoreAdjustedVariance_nonneg_of_diagonal_le_oracle
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading variance : Param -> Real)
    (hvariance : ∀ param, param ∈ parameters -> 0 ≤ variance param)
    (hscore_le_oracle :
      scoreQuadraticForm parameters firstStepLoading
          (fun left right => if left = right then variance left else 0) ≤
        oracleVariance) :
    0 ≤ changingLawScoreAdjustedVariance parameters oracleVariance
      firstStepLoading targetDriftLoading
      (fun left right => if left = right then variance left else 0) := by
  rw [changingLawScoreAdjustedVariance_eq_fixed_plus_drift]
  exact add_nonneg
    (fixedLawScoreAdjustedVariance_nonneg_of_score_le_oracle
      parameters oracleVariance firstStepLoading
      (fun left right => if left = right then variance left else 0)
      hscore_le_oracle)
    (scoreQuadraticForm_diagonal_nonneg parameters targetDriftLoading variance
      hvariance)

omit [DecidableEq Param] in
/--
For a changing-law target, the score-adjusted variance is below the oracle
variance when the target-drift quadratic form is below the first-step
projection quadratic form.
-/
theorem changingLawScoreAdjustedVariance_le_oracle_of_drift_le_projection
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hdrift_le_projection :
      scoreQuadraticForm parameters targetDriftLoading scoreCovariance ≤
        scoreQuadraticForm parameters firstStepLoading scoreCovariance) :
    changingLawScoreAdjustedVariance parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance ≤ oracleVariance := by
  unfold changingLawScoreAdjustedVariance
  exact changingTargetVariance_le_oracle_of_drift_le_projection
    oracleVariance
    (scoreQuadraticForm parameters firstStepLoading scoreCovariance)
    (scoreQuadraticForm parameters targetDriftLoading scoreCovariance)
    hdrift_le_projection

omit [DecidableEq Param] in
/--
For a changing-law target, the oracle variance is below the score-adjusted
variance when the first-step projection quadratic form is below the
target-drift quadratic form.
-/
theorem oracle_le_changingLawScoreAdjustedVariance_of_projection_le_drift
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hprojection_le_drift :
      scoreQuadraticForm parameters firstStepLoading scoreCovariance ≤
        scoreQuadraticForm parameters targetDriftLoading scoreCovariance) :
    oracleVariance ≤ changingLawScoreAdjustedVariance parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance := by
  unfold changingLawScoreAdjustedVariance
  exact oracle_le_changingTargetVariance_of_projection_le_drift
    oracleVariance
    (scoreQuadraticForm parameters firstStepLoading scoreCovariance)
    (scoreQuadraticForm parameters targetDriftLoading scoreCovariance)
    hprojection_le_drift

omit [DecidableEq Param] in
/--
If the projection and target-drift quadratic forms are equal, the changing-law
score-adjusted variance equals the oracle variance.
-/
theorem changingLawScoreAdjustedVariance_eq_oracle_of_equal_quadratic_forms
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hquadratic :
      scoreQuadraticForm parameters firstStepLoading scoreCovariance =
        scoreQuadraticForm parameters targetDriftLoading scoreCovariance) :
    changingLawScoreAdjustedVariance parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance = oracleVariance := by
  unfold changingLawScoreAdjustedVariance
  exact changingTargetVariance_eq_oracle_of_projection_eq_drift
    oracleVariance
    (scoreQuadraticForm parameters firstStepLoading scoreCovariance)
    (scoreQuadraticForm parameters targetDriftLoading scoreCovariance)
    hquadratic

end WDSM
end Matching
end StatInference
