import StatInference.Matching.WDSM.ScoreCellPredictabilityBridge

/-!
# Score-cell residual mean-zero bridge

This module composes the finite score-cell coefficient representation with the
conditional orthogonality bridge used by residual martingale arguments.  It
turns deterministic scaled score-cell loadings into the score-measurable
coefficients required to prove treated/control weighted centered-residual
mean-zero components.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Sample TreatedCell ControlCell : Type*}
variable [mSample : MeasurableSpace Sample]
variable {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
Two-arm residual conditional mean-zero components from discrete score-cell
scaled coefficient loadings and centered-residual conditional mean identities.
-/
theorem twoArm_residual_conditional_mean_zero_components_of_discreteScore_scaledLoadings
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero) :
    b.treated_residual_conditional_mean_zero ∧
      b.control_residual_conditional_mean_zero := by
  have htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma]
        (fun sample => treatedScale * treatedLoading (treatedScore sample))
        sampleLaw :=
    scaledScoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw) treatedScore treatedScale treatedLoading
      htreatedScore
  have hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma]
        (fun sample => controlScale * controlLoading (controlScore sample))
        sampleLaw :=
    scaledScoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw) controlScore controlScale controlLoading
      hcontrolScore
  exact
    ⟨treated_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw) htreatedSub b
      (fun sample => treatedScale * treatedLoading (treatedScore sample))
      treatedOutcome treatedScoreVersion htreatedCoefficient htreatedOutcome
      htreatedScoreVersion htreatedScoreVersionMeas htreatedWeightedResidual
      htreatedCond htreatedZeroMap,
    control_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw) hcontrolSub b
      (fun sample => controlScale * controlLoading (controlScore sample))
      controlOutcome controlScoreVersion hcontrolCoefficient hcontrolOutcome
      hcontrolScoreVersion hcontrolScoreVersionMeas hcontrolWeightedResidual
      hcontrolCond hcontrolZeroMap⟩

/--
Raw-outcome-integrability variant of the two-arm residual conditional
mean-zero components from discrete score-cell scaled coefficient loadings.
The score-version integrability hypotheses are derived from the conditional
mean identities.
-/
theorem twoArm_residual_conditional_mean_zero_components_of_discreteScore_scaledLoadings_outcomeIntegrable
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero) :
    b.treated_residual_conditional_mean_zero ∧
      b.control_residual_conditional_mean_zero := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    twoArm_residual_conditional_mean_zero_components_of_discreteScore_scaledLoadings
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion htreatedScore
      hcontrolScore htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedWeightedResidual
      hcontrolWeightedResidual htreatedCond hcontrolCond htreatedZeroMap
      hcontrolZeroMap

/--
Combined two-arm coefficient predictability and residual conditional mean-zero
components from discrete score-cell scaled coefficient loadings.
-/
theorem twoArm_predictability_and_residual_mean_zero_components_of_discreteScore_scaledLoadings
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma]
          (fun sample => treatedScale * treatedLoading (treatedScore sample))
          sampleLaw ->
        b.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma]
          (fun sample => controlScale * controlLoading (controlScore sample))
          sampleLaw ->
        b.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero) :
    (b.treated_coefficient_predictability ∧
        b.control_coefficient_predictability) ∧
      b.treated_residual_conditional_mean_zero ∧
        b.control_residual_conditional_mean_zero := by
  exact
    ⟨twoArm_coefficient_predictability_components_of_discreteScore_scaledLoadings
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw) b
      treatedScore controlScore treatedScale controlScale treatedLoading
      controlLoading htreatedScore hcontrolScore htreatedPredictabilityMap
      hcontrolPredictabilityMap,
    twoArm_residual_conditional_mean_zero_components_of_discreteScore_scaledLoadings
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion htreatedScore
      hcontrolScore htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedWeightedResidual
      hcontrolWeightedResidual htreatedCond hcontrolCond htreatedZeroMap
      hcontrolZeroMap⟩

/--
Raw-outcome-integrability variant of the combined two-arm coefficient
predictability and residual mean-zero theorem.
-/
theorem twoArm_predictability_and_residual_mean_zero_components_of_discreteScore_scaledLoadings_outcomeIntegrable
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma]
          (fun sample => treatedScale * treatedLoading (treatedScore sample))
          sampleLaw ->
        b.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma]
          (fun sample => controlScale * controlLoading (controlScore sample))
          sampleLaw ->
        b.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero) :
    (b.treated_coefficient_predictability ∧
        b.control_coefficient_predictability) ∧
      b.treated_residual_conditional_mean_zero ∧
        b.control_residual_conditional_mean_zero := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    twoArm_predictability_and_residual_mean_zero_components_of_discreteScore_scaledLoadings
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion htreatedScore
      hcontrolScore htreatedPredictabilityMap hcontrolPredictabilityMap
      htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedWeightedResidual
      hcontrolWeightedResidual htreatedCond hcontrolCond htreatedZeroMap
      hcontrolZeroMap

end WDSM
end Matching
end StatInference
