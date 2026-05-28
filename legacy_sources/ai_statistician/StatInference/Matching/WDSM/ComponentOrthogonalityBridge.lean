import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Matching.WDSM.ConditionalCrossMomentBridge

/-!
# Component orthogonality bridge

Known-score WDSM variance formulas require an orthogonality/additivity input
between the heterogeneity and residual components.  This module connects that
abstract input to a concrete conditional residual cross-moment route: if the
residual cross product has zero conditional expectation given the score field,
then every score-measurable coefficient product has zero unconditional
cross moment.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
Score-field conditional residual cross-moment zero supplies a component
orthogonality proposition through an explicit transfer map.
-/
theorem component_orthogonality_of_condExp_residual_cross_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (leftCoefficient rightCoefficient leftResidual rightResidual :
      Sample -> Real)
    (componentOrthogonality : Prop)
    (hleft :
      AEStronglyMeasurable[scoreSigma] leftCoefficient sampleLaw)
    (hright :
      AEStronglyMeasurable[scoreSigma] rightCoefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (leftCoefficient sample * rightCoefficient sample) *
            (leftResidual sample * rightResidual sample)) sampleLaw)
    (hresidualProduct :
      Integrable (fun sample => leftResidual sample * rightResidual sample)
        sampleLaw)
    (hcrossZero :
      sampleLaw[(fun sample => leftResidual sample * rightResidual sample) |
        scoreSigma] =ᵐ[sampleLaw] 0)
    (htransfer :
      (∫ sample,
          (leftCoefficient sample * rightCoefficient sample) *
            (leftResidual sample * rightResidual sample) ∂sampleLaw) = 0 ->
        componentOrthogonality) :
    componentOrthogonality :=
  htransfer
    (integral_scoreMeasurable_mul_residualProduct_eq_zero_of_condExp_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub leftCoefficient rightCoefficient
      leftResidual rightResidual hleft hright hproduct hresidualProduct
      hcrossZero)

/--
Known-score variance formula from component variance formulas and conditional
residual cross-moment zero.  This is the manuscript-facing bridge from a
concrete score-field orthogonality argument to the abstract
`component_orthogonality` input consumed by the variance interface.
-/
theorem known_score_variance_formula_of_condExp_residual_cross_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (b : KnownScoreVarianceFormulaBridge)
    (leftCoefficient rightCoefficient leftResidual rightResidual :
      Sample -> Real)
    (hheterogeneity : b.heterogeneity_variance_formula)
    (hresidual : b.residual_variance_formula)
    (hleft :
      AEStronglyMeasurable[scoreSigma] leftCoefficient sampleLaw)
    (hright :
      AEStronglyMeasurable[scoreSigma] rightCoefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (leftCoefficient sample * rightCoefficient sample) *
            (leftResidual sample * rightResidual sample)) sampleLaw)
    (hresidualProduct :
      Integrable (fun sample => leftResidual sample * rightResidual sample)
        sampleLaw)
    (hcrossZero :
      sampleLaw[(fun sample => leftResidual sample * rightResidual sample) |
        scoreSigma] =ᵐ[sampleLaw] 0)
    (htransfer :
      (∫ sample,
          (leftCoefficient sample * rightCoefficient sample) *
            (leftResidual sample * rightResidual sample) ∂sampleLaw) = 0 ->
        b.component_orthogonality) :
    b.known_score_variance_formula :=
  known_score_variance_formula_of_component_variances b hheterogeneity
    hresidual
    (component_orthogonality_of_condExp_residual_cross_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub leftCoefficient rightCoefficient
      leftResidual rightResidual b.component_orthogonality hleft hright
      hproduct hresidualProduct hcrossZero htransfer)

end WDSM
end Matching
end StatInference
