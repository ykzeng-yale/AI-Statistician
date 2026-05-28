import StatInference.Matching.WDSM.ScoreAdjustmentAlgebra
import StatInference.Matching.WDSM.AsymptoticInterfaces

/-!
# Refinements for estimated-score local-experiment variance inputs

This module narrows one part of `EstimatedScoreLocalExperimentVarianceInput`.
The original interface keeps `score_adjustment_algebra` as an abstract `Prop`.
The lemmas here let downstream proofs provide concrete finite score-adjustment
algebra from `ScoreAdjustmentAlgebra` and a small interpretation bridge into
that abstract field, instead of passing the abstract premise directly.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Param : Type*} [DecidableEq Param]

omit [DecidableEq Param] in
/--
Derive an abstract score-adjustment premise from the fixed-law finite
score-adjustment identity proved in `ScoreAdjustmentAlgebra`.
-/
theorem score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
    (score_adjustment_algebra : Prop)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        score_adjustment_algebra) :
    score_adjustment_algebra :=
  hinterpret
    (fixedLawScoreAdjustedVariance_eq parameters oracleVariance
      firstStepLoading scoreCovariance)

omit [DecidableEq Param] in
/--
Derive an abstract score-adjustment premise from the changing-law finite
score-adjustment identity proved in `ScoreAdjustmentAlgebra`.
-/
theorem score_adjustment_algebra_of_changingLaw_score_adjustment_identity
    (score_adjustment_algebra : Prop)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        score_adjustment_algebra) :
    score_adjustment_algebra :=
  hinterpret
    (changingLawScoreAdjustedVariance_eq_fixed_plus_drift parameters
      oracleVariance firstStepLoading targetDriftLoading scoreCovariance)

omit [DecidableEq Param] in
/--
Estimated-score normality and variance formula where the score-adjustment
premise is discharged by the fixed-law finite score-adjustment identity.
-/
theorem
    estimated_score_asymptotic_normality_and_variance_formula_of_fixedLaw_score_adjustment_identity
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.score_adjustment_algebra)
    (hknown : b.known_score_asymptotic_normality)
    (hknown_variance : b.known_score_variance_formula)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.matching_functional_local_derivative)
    (hequicontinuity : b.local_stochastic_equicontinuity)
    (hgodambe : b.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      b hknown hknown_variance hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.score_adjustment_algebra parameters oracleVariance firstStepLoading
        scoreCovariance hinterpret)
      hgodambe

omit [DecidableEq Param] in
/--
Estimated-score normality and variance formula where the score-adjustment
premise is discharged by the changing-law finite score-adjustment identity.
-/
theorem
    estimated_score_asymptotic_normality_and_variance_formula_of_changingLaw_score_adjustment_identity
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.score_adjustment_algebra)
    (hknown : b.known_score_asymptotic_normality)
    (hknown_variance : b.known_score_variance_formula)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.matching_functional_local_derivative)
    (hequicontinuity : b.local_stochastic_equicontinuity)
    (hgodambe : b.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      b hknown hknown_variance hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.score_adjustment_algebra parameters oracleVariance firstStepLoading
        targetDriftLoading scoreCovariance hinterpret)
      hgodambe

omit [DecidableEq Param] in
/--
Estimated-score normality and variance formula from the fixed-law finite
score-adjustment identity plus the compact WDSM-specific local-experiment core.
-/
theorem
    estimated_score_asymptotic_normality_and_variance_formula_of_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore b)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.score_adjustment_algebra)
    (hknown : b.known_score_asymptotic_normality)
    (hknown_variance : b.known_score_variance_formula)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_core
      b core hknown hknown_variance hfirst hscore
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.score_adjustment_algebra parameters oracleVariance firstStepLoading
        scoreCovariance hinterpret)

omit [DecidableEq Param] in
/--
Estimated-score normality and variance formula from the changing-law finite
score-adjustment identity plus the compact WDSM-specific local-experiment core.
-/
theorem
    estimated_score_asymptotic_normality_and_variance_formula_of_changingLaw_score_adjustment_identity_and_local_experiment_core
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore b)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.score_adjustment_algebra)
    (hknown : b.known_score_asymptotic_normality)
    (hknown_variance : b.known_score_variance_formula)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_core
      b core hknown hknown_variance hfirst hscore
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.score_adjustment_algebra parameters oracleVariance firstStepLoading
        targetDriftLoading scoreCovariance hinterpret)

end WDSM
end Matching
end StatInference
