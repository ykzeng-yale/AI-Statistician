import StatInference.Matching.WDSM.BootstrapVarianceConsistencyBridge
import StatInference.Matching.WDSM.NegligibleAlgebra
import Mathlib.Tactic.Ring

/-!
# Bootstrap variance stability

This module replaces opaque bootstrap-consistency obligations by reusable
real-valued stability statements.  If the checked linearized bootstrap
variance target converges and the score-replication and bias-correction
errors are negligible, then the corresponding actual bootstrap variance
estimate has the same limit.

The theorem is deterministic `Tendsto` algebra.  Conditional bootstrap
probability regularity and the stochastic proof that the errors are
negligible remain separate inputs.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index : Type*} {l : Filter Index}

/-- Score-replication error negligibility for a scalar bootstrap variance. -/
def bootstrapScoreReplicationErrorNegligible
    (scoreReplicationError : Index -> Real) : Prop :=
  Tendsto scoreReplicationError l (nhds 0)

/-- Bias-correction error negligibility for a scalar bootstrap variance. -/
def bootstrapBiasCorrectionErrorNegligible
    (biasCorrectionError : Index -> Real) : Prop :=
  Tendsto biasCorrectionError l (nhds 0)

/-- Linearized conditional-variance convergence to a scalar target. -/
def linearizedBootstrapVarianceConverges
    (linearizedVariance : Index -> Real) (varianceLimit : Real) : Prop :=
  Tendsto linearizedVariance l (nhds varianceLimit)

/-- Actual bootstrap variance consistency to a scalar target. -/
def actualBootstrapVarianceConsistent
    (actualVariance : Index -> Real) (varianceLimit : Real) : Prop :=
  Tendsto actualVariance l (nhds varianceLimit)

/--
If an actual bootstrap variance is a linearized variance plus one negligible
error, it has the same limit as the linearized variance.
-/
theorem tendsto_bootstrapVariance_of_linearized_and_negligible_error
    (linearizedVariance actualVariance error : Index -> Real)
    (varianceLimit : Real)
    (hdecomp :
      actualVariance =ᶠ[l]
        (fun index => linearizedVariance index + error index))
    (hlinearized :
      Tendsto linearizedVariance l (nhds varianceLimit))
    (herror : Tendsto error l (nhds 0)) :
    Tendsto actualVariance l (nhds varianceLimit) := by
  exact (tendsto_add_negligible linearizedVariance error varianceLimit
    hlinearized herror).congr' hdecomp.symm

/--
If an actual bootstrap variance equals the linearized variance plus
score-replication and bias-correction errors, and both errors are negligible,
it has the same limit as the linearized variance.
-/
theorem tendsto_bootstrapVariance_of_linearized_score_bias_errors
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (varianceLimit : Real)
    (hdecomp :
      actualVariance =ᶠ[l]
        (fun index =>
          linearizedVariance index +
            (scoreReplicationError index + biasCorrectionError index)))
    (hlinearized :
      Tendsto linearizedVariance l (nhds varianceLimit))
    (hscore : bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError)
    (hbias : bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError) :
    Tendsto actualVariance l (nhds varianceLimit) := by
  have hcombined :
      Tendsto
        (fun index =>
          linearizedVariance index +
            (scoreReplicationError index + biasCorrectionError index))
        l (nhds varianceLimit) := by
    simpa using hlinearized.add (hscore.add hbias)
  exact hcombined.congr' hdecomp.symm

/--
Variant using a difference decomposition:
`actual - linearized = score error + bias error` eventually.
-/
theorem tendsto_bootstrapVariance_of_eventual_error_decomposition
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (varianceLimit : Real)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index => scoreReplicationError index + biasCorrectionError index))
    (hlinearized :
      Tendsto linearizedVariance l (nhds varianceLimit))
    (hscore : bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError)
    (hbias : bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError) :
    Tendsto actualVariance l (nhds varianceLimit) := by
  have hdecomp :
      actualVariance =ᶠ[l]
        (fun index =>
          linearizedVariance index +
            (scoreReplicationError index + biasCorrectionError index)) := by
    filter_upwards [herror_decomp] with index hindex
    calc
      actualVariance index =
          linearizedVariance index +
            (actualVariance index - linearizedVariance index) := by
            ring
      _ =
          linearizedVariance index +
            (scoreReplicationError index + biasCorrectionError index) := by
            rw [hindex]
  exact
    tendsto_bootstrapVariance_of_linearized_score_bias_errors
      (l := l) linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError varianceLimit hdecomp hlinearized hscore hbias

/--
Build the generic bootstrap variance-consistency bridge from concrete
real-valued stability inputs.  The finite-algebra and multiplier-regularity
fields are still supplied as explicit propositions, but the score-replication,
bias-correction, and conditional-variance fields now have concrete
`Tendsto` meanings.
-/
def linearizedBootstrapVarianceConsistencyBridgeOfErrorStability
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (varianceLimit : Real)
    (linearizedReplicateAlgebra multiplierWeightRegular : Prop)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index)) :
    LinearizedBootstrapVarianceConsistencyBridge where
  linearized_replicate_algebra_verified := linearizedReplicateAlgebra
  multiplier_weight_regular := multiplierWeightRegular
  bootstrap_score_replication_consistent :=
    bootstrapScoreReplicationErrorNegligible (l := l) scoreReplicationError
  bootstrap_bias_correction_consistent :=
    bootstrapBiasCorrectionErrorNegligible (l := l) biasCorrectionError
  conditional_variance_convergence :=
    linearizedBootstrapVarianceConverges (l := l) linearizedVariance
      varianceLimit
  bootstrap_variance_consistent :=
    actualBootstrapVarianceConsistent (l := l) actualVariance varianceLimit
  bridge := by
    intro _halgebra _hmultiplier hscore hbias hvariance
    exact
      tendsto_bootstrapVariance_of_eventual_error_decomposition
        (l := l) linearizedVariance actualVariance scoreReplicationError
        biasCorrectionError varianceLimit herror_decomp hvariance hscore hbias

/--
Direct theorem form of the error-stability bridge, useful when a scenario
module already has finite algebra and multiplier regularity evidence.
-/
theorem bootstrap_variance_consistency_of_error_stability_bridge
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (varianceLimit : Real)
    (linearizedReplicateAlgebra multiplierWeightRegular : Prop)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (halgebra : linearizedReplicateAlgebra)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError)
    (hbias : bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError)
    (hlinearized :
      linearizedBootstrapVarianceConverges (l := l) linearizedVariance
        varianceLimit) :
    actualBootstrapVarianceConsistent (l := l) actualVariance varianceLimit :=
  bootstrap_variance_consistency_of_linearized_bridge
    (linearizedBootstrapVarianceConsistencyBridgeOfErrorStability
      (l := l) linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError varianceLimit linearizedReplicateAlgebra
      multiplierWeightRegular herror_decomp)
    halgebra hmultiplier hscore hbias hlinearized

/--
Paired direct theorem form of the bootstrap error-stability bridge.  This is
the shape used by PATE/PATT bootstrap variance audits when both arms have
separate linearized variance targets and negligible score/bias errors.
-/
theorem paired_bootstrap_variance_consistency_of_error_stability_bridge
    (leftLinearizedVariance leftActualVariance leftScoreReplicationError
      leftBiasCorrectionError : Index -> Real)
    (rightLinearizedVariance rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError : Index -> Real)
    (leftVarianceLimit rightVarianceLimit : Real)
    (leftLinearizedReplicateAlgebra leftMultiplierWeightRegular
      rightLinearizedReplicateAlgebra rightMultiplierWeightRegular : Prop)
    (hleft_error_decomp :
      (fun index =>
          leftActualVariance index - leftLinearizedVariance index) =ᶠ[l]
        (fun index =>
          leftScoreReplicationError index + leftBiasCorrectionError index))
    (hright_error_decomp :
      (fun index =>
          rightActualVariance index - rightLinearizedVariance index) =ᶠ[l]
        (fun index =>
          rightScoreReplicationError index + rightBiasCorrectionError index))
    (hleft_algebra : leftLinearizedReplicateAlgebra)
    (hleft_multiplier : leftMultiplierWeightRegular)
    (hleft_score : bootstrapScoreReplicationErrorNegligible
      (l := l) leftScoreReplicationError)
    (hleft_bias : bootstrapBiasCorrectionErrorNegligible
      (l := l) leftBiasCorrectionError)
    (hleft_linearized :
      linearizedBootstrapVarianceConverges (l := l) leftLinearizedVariance
        leftVarianceLimit)
    (hright_algebra : rightLinearizedReplicateAlgebra)
    (hright_multiplier : rightMultiplierWeightRegular)
    (hright_score : bootstrapScoreReplicationErrorNegligible
      (l := l) rightScoreReplicationError)
    (hright_bias : bootstrapBiasCorrectionErrorNegligible
      (l := l) rightBiasCorrectionError)
    (hright_linearized :
      linearizedBootstrapVarianceConverges (l := l) rightLinearizedVariance
        rightVarianceLimit) :
    actualBootstrapVarianceConsistent
        (l := l) leftActualVariance leftVarianceLimit ∧
      actualBootstrapVarianceConsistent
        (l := l) rightActualVariance rightVarianceLimit := by
  constructor
  · exact
      bootstrap_variance_consistency_of_error_stability_bridge
        (l := l) leftLinearizedVariance leftActualVariance
        leftScoreReplicationError leftBiasCorrectionError leftVarianceLimit
        leftLinearizedReplicateAlgebra leftMultiplierWeightRegular
        hleft_error_decomp hleft_algebra hleft_multiplier hleft_score
        hleft_bias hleft_linearized
  · exact
      bootstrap_variance_consistency_of_error_stability_bridge
        (l := l) rightLinearizedVariance rightActualVariance
        rightScoreReplicationError rightBiasCorrectionError rightVarianceLimit
        rightLinearizedReplicateAlgebra rightMultiplierWeightRegular
        hright_error_decomp hright_algebra hright_multiplier hright_score
        hright_bias hright_linearized

end WDSM
end Matching
end StatInference
