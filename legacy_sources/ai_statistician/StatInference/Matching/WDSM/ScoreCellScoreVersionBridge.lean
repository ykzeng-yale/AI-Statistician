import StatInference.Matching.WDSM.ScoreCellIntegrabilityBridge

/-!
# Score-cell score-version bridge

This module specializes the residual martingale score-cell route to the common
WDSM case where the score-version functions are themselves finite score-cell
loadings.  Under a finite sample law, finite score-cell coverage proves the
score-version integrability and score-field measurability assumptions consumed
by the residual mean-zero and CLT bridge interfaces.
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
A finite score-cell score version is its own conditional expectation with
respect to the score sigma-field.  Finite coverage supplies integrability.
-/
theorem condExp_scoreCellLoading_ae_eq_self_of_discreteScore_finset_abs_sum_bound
    {Cell : Type*} [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (scoreVersionLoading : Cell -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell)) :
    sampleLaw[(fun sample => scoreVersionLoading (score sample)) |
        scoreSigma] =ᵐ[sampleLaw]
      fun sample => scoreVersionLoading (score sample) :=
  condExp_ae_eq_self_of_scoreSigma_aestronglyMeasurable
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub (fun sample => scoreVersionLoading (score sample))
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score scoreVersionLoading hscore)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scoreVersionLoading hscore
      hcover)

/--
Finite score-cell-type variant of the score-version self conditional
expectation identity.
-/
theorem condExp_scoreCellLoading_ae_eq_self_of_discreteScore_fintype_abs_sum_bound
    {Cell : Type*} [Fintype Cell] [DecidableEq Cell]
    [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (score : Sample -> Cell)
    (scoreVersionLoading : Cell -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw) :
    sampleLaw[(fun sample => scoreVersionLoading (score sample)) |
        scoreSigma] =ᵐ[sampleLaw]
      fun sample => scoreVersionLoading (score sample) :=
  condExp_scoreCellLoading_ae_eq_self_of_discreteScore_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub (Finset.univ : Finset Cell) score scoreVersionLoading hscore
    (Filter.Eventually.of_forall (fun sample => by simp))

/--
If an outcome agrees almost everywhere with a finite score-cell score version,
then that score version is its conditional expectation.  This is mainly a
sanity adapter; the general WDSM case still needs the conditional-mean
assumption itself.
-/
theorem condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_finset_abs_sum_bound
    {Cell : Type*} [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (scoreVersionLoading : Cell -> Real)
    (outcome : Sample -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (houtcome :
      outcome =ᵐ[sampleLaw]
        fun sample => scoreVersionLoading (score sample)) :
    sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw]
      fun sample => scoreVersionLoading (score sample) :=
  condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome (fun sample => scoreVersionLoading (score sample)) houtcome
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score scoreVersionLoading hscore)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scoreVersionLoading hscore
      hcover)

/--
Finite score-cell-type variant of the almost-everywhere equality adapter for
conditional score versions.
-/
theorem condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_fintype_abs_sum_bound
    {Cell : Type*} [Fintype Cell] [DecidableEq Cell]
    [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (score : Sample -> Cell)
    (scoreVersionLoading : Cell -> Real)
    (outcome : Sample -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (houtcome :
      outcome =ᵐ[sampleLaw]
        fun sample => scoreVersionLoading (score sample)) :
    sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw]
      fun sample => scoreVersionLoading (score sample) :=
  condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub (Finset.univ : Finset Cell) score scoreVersionLoading outcome
    hscore (Filter.Eventually.of_forall (fun sample => by simp)) houtcome

/--
Two-arm conditional-mean identities from almost-everywhere equality to finite
score-cell score versions.
-/
theorem twoArm_condExp_ae_eq_scoreCellVersions_of_ae_eq_discreteScore_finset_abs_sum_bound
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    [IsFiniteMeasure sampleLaw]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScoreVersionLoading : TreatedCell -> Real)
    (controlScoreVersionLoading : ControlCell -> Real)
    (treatedOutcome controlOutcome : Sample -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedCover :
      ∀ᵐ sample ∂sampleLaw,
        treatedScore sample ∈ (treatedCells : Set TreatedCell))
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw,
        controlScore sample ∈ (controlCells : Set ControlCell))
    (htreatedOutcomeEq :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedScoreVersionLoading (treatedScore sample))
    (hcontrolOutcomeEq :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlScoreVersionLoading (controlScore sample)) :
    sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedScoreVersionLoading (treatedScore sample)) ∧
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        fun sample => controlScoreVersionLoading (controlScore sample) :=
  ⟨condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw) htreatedSub treatedCells treatedScore
      treatedScoreVersionLoading treatedOutcome htreatedScore htreatedCover
      htreatedOutcomeEq,
    condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw) hcontrolSub controlCells controlScore
      controlScoreVersionLoading controlOutcome hcontrolScore hcontrolCover
      hcontrolOutcomeEq⟩

/--
Finite score-cell-type variant of the two-arm conditional-mean identity
adapter from almost-everywhere equality.
-/
theorem twoArm_condExp_ae_eq_scoreCellVersions_of_ae_eq_discreteScore_fintype_abs_sum_bound
    [Fintype TreatedCell] [Fintype ControlCell]
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    [IsFiniteMeasure sampleLaw]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScoreVersionLoading : TreatedCell -> Real)
    (controlScoreVersionLoading : ControlCell -> Real)
    (treatedOutcome controlOutcome : Sample -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedOutcomeEq :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedScoreVersionLoading (treatedScore sample))
    (hcontrolOutcomeEq :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlScoreVersionLoading (controlScore sample)) :
    sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedScoreVersionLoading (treatedScore sample)) ∧
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        fun sample => controlScoreVersionLoading (controlScore sample) :=
  twoArm_condExp_ae_eq_scoreCellVersions_of_ae_eq_discreteScore_finset_abs_sum_bound
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub (Finset.univ : Finset TreatedCell)
    (Finset.univ : Finset ControlCell) treatedScore controlScore
    treatedScoreVersionLoading controlScoreVersionLoading treatedOutcome
    controlOutcome htreatedScore hcontrolScore
    (Filter.Eventually.of_forall (fun sample => by simp))
    (Filter.Eventually.of_forall (fun sample => by simp))
    htreatedOutcomeEq hcontrolOutcomeEq

/--
Weighted centered residual integrability when the coefficient and score
version are finite score-cell loadings on the same discrete score.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_scoreCellVersion_finset_abs_sum_bound
    {Cell : Type*} [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (scale : Real)
    (loading scoreVersionLoading : Cell -> Real)
    (outcome : Sample -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (houtcome : Integrable outcome sampleLaw) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersionLoading (score sample)))
      sampleLaw :=
  weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub cells score scale loading outcome
    (fun sample => scoreVersionLoading (score sample)) hscore hcover
    houtcome
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scoreVersionLoading hscore
      hcover)

/--
Finite score-cell-type variant of the score-cell score-version weighted
centered residual integrability bridge.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_scoreCellVersion_fintype_abs_sum_bound
    {Cell : Type*} [Fintype Cell] [DecidableEq Cell]
    [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    (score : Sample -> Cell)
    (scale : Real)
    (loading scoreVersionLoading : Cell -> Real)
    (outcome : Sample -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (houtcome : Integrable outcome sampleLaw) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersionLoading (score sample)))
      sampleLaw :=
  weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_scoreCellVersion_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub (Finset.univ : Finset Cell) score scale loading
    scoreVersionLoading outcome hscore
    (Filter.Eventually.of_forall (fun sample => by simp)) houtcome

/--
Close the two-arm finite-array integrability component when the coefficient
loadings and score versions are finite score-cell loadings.
-/
theorem twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_scoreCellVersions_finset_abs_sum_bound
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    [IsFiniteMeasure sampleLaw]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    (hcontrolSub : controlScoreSigma ≤ mSample)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedScoreVersionLoading : TreatedCell -> Real)
    (controlScoreVersionLoading : ControlCell -> Real)
    (treatedOutcome controlOutcome : Sample -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedCover :
      ∀ᵐ sample ∂sampleLaw,
        treatedScore sample ∈ (treatedCells : Set TreatedCell))
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw,
        controlScore sample ∈ (controlCells : Set ControlCell))
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample -
                treatedScoreVersionLoading (treatedScore sample)))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample -
                controlScoreVersionLoading (controlScore sample)))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_finset_abs_sum_bound
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub b treatedCells controlCells treatedScore
    controlScore treatedScale controlScale treatedLoading controlLoading
    treatedOutcome (fun sample => treatedScoreVersionLoading (treatedScore sample))
    controlOutcome (fun sample => controlScoreVersionLoading (controlScore sample))
    htreatedScore hcontrolScore htreatedCover hcontrolCover htreatedOutcome
    hcontrolOutcome
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw) htreatedSub treatedCells treatedScore
      treatedScoreVersionLoading htreatedScore htreatedCover)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw) hcontrolSub controlCells controlScore
      controlScoreVersionLoading hcontrolScore hcontrolCover)
    hmap

/--
Finite score-cell-type variant of the two-arm score-version finite-array
integrability bridge.
-/
theorem twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_scoreCellVersions_fintype_abs_sum_bound
    [Fintype TreatedCell] [Fintype ControlCell]
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    [IsFiniteMeasure sampleLaw]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    (hcontrolSub : controlScoreSigma ≤ mSample)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedScoreVersionLoading : TreatedCell -> Real)
    (controlScoreVersionLoading : ControlCell -> Real)
    (treatedOutcome controlOutcome : Sample -> Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample -
                treatedScoreVersionLoading (treatedScore sample)))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample -
                controlScoreVersionLoading (controlScore sample)))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub b (Finset.univ : Finset TreatedCell)
    (Finset.univ : Finset ControlCell) treatedScore controlScore
    treatedScale controlScale treatedLoading controlLoading
    treatedScoreVersionLoading controlScoreVersionLoading treatedOutcome
    controlOutcome htreatedScore hcontrolScore
    (Filter.Eventually.of_forall (fun sample => by simp))
    (Filter.Eventually.of_forall (fun sample => by simp)) htreatedOutcome
    hcontrolOutcome hmap

/--
Residual CLT/variance input from finite score-cell coefficient loadings and
finite score-cell score-version loadings.  This discharges the score-version
integrability and score-field measurability premises of the sampling bridge.
-/
theorem residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_scoreCellVersions_finset_abs_sum_bound_sampling_bridge_input
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    [IsFiniteMeasure sampleLaw]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedScoreVersionLoading : TreatedCell -> Real)
    (controlScoreVersionLoading : ControlCell -> Real)
    (treatedOutcome controlOutcome : Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedCover :
      ∀ᵐ sample ∂sampleLaw,
        treatedScore sample ∈ (treatedCells : Set TreatedCell))
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw,
        controlScore sample ∈ (controlCells : Set ControlCell))
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma]
          (fun sample => treatedScale * treatedLoading (treatedScore sample))
          sampleLaw ->
        martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma]
          (fun sample => controlScale * controlLoading (controlScore sample))
          sampleLaw ->
        martingaleBridge.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedScoreVersionLoading (treatedScore sample))
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        fun sample => controlScoreVersionLoading (controlScore sample))
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample -
              treatedScoreVersionLoading (treatedScore sample))) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample -
              controlScoreVersionLoading (controlScore sample))) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample -
                treatedScoreVersionLoading (treatedScore sample)))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample -
                controlScoreVersionLoading (controlScore sample)))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_finset_abs_sum_bound_sampling_bridge_input
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub input martingaleBridge regularityBridge
    treatedCells controlCells treatedScore controlScore treatedScale
    controlScale treatedLoading controlLoading treatedOutcome
    (fun sample => treatedScoreVersionLoading (treatedScore sample))
    controlOutcome
    (fun sample => controlScoreVersionLoading (controlScore sample))
    harrayMap hmoments hresidualRegularity htreatedScore hcontrolScore
    htreatedCover hcontrolCover htreatedPredictabilityMap
    hcontrolPredictabilityMap htreatedOutcome hcontrolOutcome
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw) htreatedSub treatedCells treatedScore
      treatedScoreVersionLoading htreatedScore htreatedCover)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw) hcontrolSub controlCells controlScore
      controlScoreVersionLoading hcontrolScore hcontrolCover)
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw) treatedScore treatedScoreVersionLoading
      htreatedScore)
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw) controlScore controlScoreVersionLoading
      hcontrolScore)
    htreatedCond hcontrolCond htreatedZeroMap hcontrolZeroMap
    hregularityMap hfiltration htreatedAdapted hcontrolAdapted
    htreatedInnovation hcontrolInnovation horder hcross hdesign
    hintegrabilityMap hlindeberg hquad

/--
Finite score-cell-type variant of the residual CLT/variance score-version
sampling bridge.
-/
theorem residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_scoreCellVersions_fintype_abs_sum_bound_sampling_bridge_input
    [Fintype TreatedCell] [Fintype ControlCell]
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    [IsFiniteMeasure sampleLaw]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedScoreVersionLoading : TreatedCell -> Real)
    (controlScoreVersionLoading : ControlCell -> Real)
    (treatedOutcome controlOutcome : Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma]
          (fun sample => treatedScale * treatedLoading (treatedScore sample))
          sampleLaw ->
        martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma]
          (fun sample => controlScale * controlLoading (controlScore sample))
          sampleLaw ->
        martingaleBridge.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedScoreVersionLoading (treatedScore sample))
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        fun sample => controlScoreVersionLoading (controlScore sample))
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample -
              treatedScoreVersionLoading (treatedScore sample))) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample -
              controlScoreVersionLoading (controlScore sample))) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample -
                treatedScoreVersionLoading (treatedScore sample)))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample -
                controlScoreVersionLoading (controlScore sample)))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_scoreCellVersions_finset_abs_sum_bound_sampling_bridge_input
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub input martingaleBridge regularityBridge
    (Finset.univ : Finset TreatedCell) (Finset.univ : Finset ControlCell)
    treatedScore controlScore treatedScale controlScale treatedLoading
    controlLoading treatedScoreVersionLoading controlScoreVersionLoading
    treatedOutcome controlOutcome harrayMap hmoments hresidualRegularity
    htreatedScore hcontrolScore
    (Filter.Eventually.of_forall (fun sample => by simp))
    (Filter.Eventually.of_forall (fun sample => by simp))
    htreatedPredictabilityMap hcontrolPredictabilityMap htreatedOutcome
    hcontrolOutcome htreatedCond hcontrolCond htreatedZeroMap
    hcontrolZeroMap hregularityMap hfiltration htreatedAdapted
    hcontrolAdapted htreatedInnovation hcontrolInnovation horder hcross
    hdesign hintegrabilityMap hlindeberg hquad

end WDSM
end Matching
end StatInference
