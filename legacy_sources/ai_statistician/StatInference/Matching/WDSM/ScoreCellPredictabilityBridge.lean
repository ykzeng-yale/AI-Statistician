import StatInference.Matching.WDSM.ResidualMartingaleDifferenceBridge

/-!
# Score-cell measurability and predictability bridge

This module closes a small but common WDSM probability-adapter step.  Residual
martingale inputs need coefficient predictability.  The paper's finite-cell
route usually proves coefficients are deterministic scales times score-cell
loadings, so this file turns discrete score-cell measurability into the
`AEStronglyMeasurable` coefficient facts consumed by
`ResidualMartingaleDifferenceBridge`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory

variable {Sample TreatedCell ControlCell : Type*}
variable [mSample : MeasurableSpace Sample]
variable {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
A loading on a discrete score-cell space is score-sigma-field
almost-everywhere strongly measurable after composition with a
score-sigma-field almost-everywhere strongly measurable score.
-/
theorem scoreCellLoading_aestronglyMeasurable_of_discreteScore
    {Cell : Type*} [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (score : Sample -> Cell)
    (loading : Cell -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw) :
    AEStronglyMeasurable[scoreSigma]
      (fun sample => loading (score sample)) sampleLaw :=
  (continuous_of_discreteTopology (f := loading)).comp_aestronglyMeasurable
    hscore

/--
A deterministic scale times a discrete score-cell loading remains
score-sigma-field almost-everywhere strongly measurable.
-/
theorem scaledScoreCellLoading_aestronglyMeasurable_of_discreteScore
    {Cell : Type*} [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw) :
    AEStronglyMeasurable[scoreSigma]
      (fun sample => scale * loading (score sample)) sampleLaw := by
  have hscale :
      AEStronglyMeasurable[scoreSigma] (fun _ : Sample => scale)
        sampleLaw :=
    aestronglyMeasurable_const
  have hloading :
      AEStronglyMeasurable[scoreSigma]
        (fun sample => loading (score sample)) sampleLaw :=
    scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score loading hscore
  exact hscale.mul hloading

/--
Two-arm coefficient predictability from discrete score-cell loading
representations.  The remaining maps express the probability proof that
score-field measurability gives predictability for the chosen array
filtration.
-/
theorem twoArm_coefficient_predictability_components_of_discreteScore_scaledLoadings
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedMap :
      AEStronglyMeasurable[treatedScoreSigma]
          (fun sample => treatedScale * treatedLoading (treatedScore sample))
          sampleLaw ->
        b.treated_coefficient_predictability)
    (hcontrolMap :
      AEStronglyMeasurable[controlScoreSigma]
          (fun sample => controlScale * controlLoading (controlScore sample))
          sampleLaw ->
        b.control_coefficient_predictability) :
    b.treated_coefficient_predictability ∧
      b.control_coefficient_predictability :=
  twoArm_coefficient_predictability_components_of_aestronglyMeasurable
    (mSample := mSample)
    (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma)
    (sampleLaw := sampleLaw)
    b
    (fun sample => treatedScale * treatedLoading (treatedScore sample))
    (fun sample => controlScale * controlLoading (controlScore sample))
    (scaledScoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw)
      treatedScore treatedScale treatedLoading
      htreatedScore)
    (scaledScoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw)
      controlScore controlScale controlLoading
      hcontrolScore)
    htreatedMap hcontrolMap

end WDSM
end Matching
end StatInference
