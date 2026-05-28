import StatInference.Matching.WDSM.ScoreCellResidualMeanZeroBridge

/-!
# Score-cell integrability bridge

This module closes the finite-array integrability side condition used by the
residual martingale bridge.  In the finite score-cell route, matching
coefficients are deterministic scales times score-cell loadings.  If those
coefficients are uniformly bounded almost everywhere and the centered residual
is integrable, then the weighted centered residual is integrable.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped BigOperators

variable {Sample TreatedCell ControlCell : Type*}
variable [mSample : MeasurableSpace Sample]
variable {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
An almost-everywhere covered finite score-cell loading bound gives the
almost-everywhere coefficient bound used by the integrability bridge.
-/
theorem scaledScoreCellLoading_ae_bound_of_cell_bound
    {Cell : Type*}
    (cells : Set Cell)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (bound : Real)
    (hcover : ∀ᵐ sample ∂sampleLaw, score sample ∈ cells)
    (hbound : ∀ cell, cell ∈ cells -> ‖scale * loading cell‖ ≤ bound) :
    ∀ᵐ sample ∂sampleLaw,
      ‖scale * loading (score sample)‖ ≤ bound :=
  hcover.mono (fun sample hsample => hbound (score sample) hsample)

/-- Finite absolute-sum bound for scaled score-cell loadings. -/
noncomputable def finiteScoreCellScaledLoadingAbsSumBound
    {Cell : Type*}
    (cells : Finset Cell)
    (scale : Real)
    (loading : Cell -> Real) : Real :=
  ∑ cell ∈ cells, ‖scale * loading cell‖

/--
Every scaled loading on a covered finite cell is bounded by the finite
absolute-sum bound.
-/
theorem finiteScoreCellScaledLoadingAbsSumBound_cell_bound
    {Cell : Type*} [DecidableEq Cell]
    (cells : Finset Cell)
    (scale : Real)
    (loading : Cell -> Real) :
    ∀ cell, cell ∈ cells ->
      ‖scale * loading cell‖ ≤
        finiteScoreCellScaledLoadingAbsSumBound cells scale loading := by
  intro cell hcell
  unfold finiteScoreCellScaledLoadingAbsSumBound
  exact
    Finset.single_le_sum
      (s := cells) (f := fun other => ‖scale * loading other‖)
      (fun other _hother => norm_nonneg (scale * loading other)) hcell

/--
Finite score-cell coverage gives the almost-everywhere bound with the
finite absolute-sum envelope.
-/
theorem scaledScoreCellLoading_ae_bound_of_finset_abs_sum_bound
    {Cell : Type*} [DecidableEq Cell]
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell)) :
    ∀ᵐ sample ∂sampleLaw,
      ‖scale * loading (score sample)‖ ≤
        finiteScoreCellScaledLoadingAbsSumBound cells scale loading :=
  scaledScoreCellLoading_ae_bound_of_cell_bound
    (mSample := mSample) (sampleLaw := sampleLaw) (cells : Set Cell) score
    scale loading (finiteScoreCellScaledLoadingAbsSumBound cells scale loading)
    hcover
    (fun cell hcell =>
      finiteScoreCellScaledLoadingAbsSumBound_cell_bound cells scale loading
        cell (by simpa using hcell))

/--
For a finite score-cell type, coverage by the full cell partition is automatic,
so the finite absolute-sum envelope bounds the scaled loading almost
everywhere.
-/
theorem scaledScoreCellLoading_ae_bound_of_fintype_abs_sum_bound
    {Cell : Type*} [Fintype Cell] [DecidableEq Cell]
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real) :
    ∀ᵐ sample ∂sampleLaw,
      ‖scale * loading (score sample)‖ ≤
        finiteScoreCellScaledLoadingAbsSumBound
          (Finset.univ : Finset Cell) scale loading :=
  scaledScoreCellLoading_ae_bound_of_finset_abs_sum_bound
    (mSample := mSample) (sampleLaw := sampleLaw)
    (Finset.univ : Finset Cell) score scale loading
    (Filter.Eventually.of_forall (fun sample => by simp))

/--
A scaled finite score-cell loading is integrable under a finite sample law.
The finite absolute-sum bound supplies domination.
-/
theorem scaledScoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
    {Cell : Type*} [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell)) :
    Integrable (fun sample => scale * loading (score sample)) sampleLaw := by
  have hmeasScore :
      AEStronglyMeasurable[scoreSigma]
        (fun sample => scale * loading (score sample)) sampleLaw :=
    scaledScoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score scale loading hscore
  have hmeas :
      AEStronglyMeasurable[mSample]
        (fun sample => scale * loading (score sample)) sampleLaw :=
    hmeasScore.mono hsub
  exact
    Integrable.of_bound hmeas
      (finiteScoreCellScaledLoadingAbsSumBound cells scale loading)
      (scaledScoreCellLoading_ae_bound_of_finset_abs_sum_bound
        (mSample := mSample) (sampleLaw := sampleLaw) cells score scale
        loading hcover)

/--
For finite score-cell types, a scaled score-cell loading is integrable under a
finite sample law without a separate coverage proof.
-/
theorem scaledScoreCellLoading_integrable_of_discreteScore_fintype_abs_sum_bound
    {Cell : Type*} [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw) :
    Integrable (fun sample => scale * loading (score sample)) sampleLaw :=
  scaledScoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub (Finset.univ : Finset Cell) score scale loading hscore
    (Filter.Eventually.of_forall (fun sample => by simp))

/--
A finite score-cell loading is integrable under a finite sample law.  This is
the unscaled specialization used for score-version functions.
-/
theorem scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
    {Cell : Type*} [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (loading : Cell -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell)) :
    Integrable (fun sample => loading (score sample)) sampleLaw := by
  simpa using
    (scaledScoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score (1 : Real) loading hscore
      hcover)

/--
For finite score-cell types, an unscaled score-cell loading is integrable under
a finite sample law.
-/
theorem scoreCellLoading_integrable_of_discreteScore_fintype_abs_sum_bound
    {Cell : Type*} [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample)
    (score : Sample -> Cell)
    (loading : Cell -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw) :
    Integrable (fun sample => loading (score sample)) sampleLaw := by
  simpa using
    (scaledScoreCellLoading_integrable_of_discreteScore_fintype_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub score (1 : Real) loading hscore)

/--
Weighted centered residual integrability from a bounded discrete score-cell
scaled loading and integrable outcome/score-version functions.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound
    {Cell : Type*} [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (outcome scoreVersion : Sample -> Real)
    (bound : Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hbound :
      ∀ᵐ sample ∂sampleLaw,
        ‖scale * loading (score sample)‖ ≤ bound)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreVersion : Integrable scoreVersion sampleLaw) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersion sample))
      sampleLaw := by
  have hcoefficientScore :
      AEStronglyMeasurable[scoreSigma]
        (fun sample => scale * loading (score sample)) sampleLaw :=
    scaledScoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score scale loading hscore
  have hcoefficient :
      AEStronglyMeasurable[mSample]
        (fun sample => scale * loading (score sample)) sampleLaw :=
    hcoefficientScore.mono hsub
  have hresidual :
      Integrable (fun sample => outcome sample - scoreVersion sample)
        sampleLaw :=
    houtcome.sub hscoreVersion
  exact hresidual.bdd_mul hcoefficient hbound

/--
Raw-outcome-integrability variant of bounded discrete score-cell weighted
centered-residual integrability.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound_outcomeIntegrable
    {Cell : Type*} [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (outcome scoreVersion : Sample -> Real)
    (bound : Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hbound :
      ∀ᵐ sample ∂sampleLaw,
        ‖scale * loading (score sample)‖ ≤ bound)
    (houtcome : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersion sample))
      sampleLaw := by
  have hscoreVersion : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact
    weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub score scale loading outcome
      scoreVersion bound hscore hbound houtcome hscoreVersion

/--
Close the two-arm finite-array integrability component from bounded discrete
score-cell scaled loadings and integrable centered residuals.
-/
theorem twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_bound
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    (hcontrolSub : controlScoreSigma ≤ mSample)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  twoArm_finite_array_integrability_component_of_integrable_weightedResiduals
    (mSample := mSample) (sampleLaw := sampleLaw) b
    (fun sample => treatedScale * treatedLoading (treatedScore sample))
    (fun sample => treatedOutcome sample - treatedScoreVersion sample)
    (fun sample => controlScale * controlLoading (controlScore sample))
    (fun sample => controlOutcome sample - controlScoreVersion sample)
    (weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw) htreatedSub treatedScore treatedScale
      treatedLoading treatedOutcome treatedScoreVersion treatedBound
      htreatedScore htreatedBound htreatedOutcome htreatedScoreVersion)
    (weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw) hcontrolSub controlScore controlScale
      controlLoading controlOutcome controlScoreVersion controlBound
      hcontrolScore hcontrolBound hcontrolOutcome hcontrolScoreVersion)
    hmap

/--
Raw-outcome-integrability variant of the bounded two-arm finite-array
integrability component.
-/
theorem
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_bound_outcomeIntegrable
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    (hcontrolSub : controlScoreSigma ≤ mSample)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_bound
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion treatedBound
      controlBound htreatedScore hcontrolScore htreatedBound hcontrolBound
      htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion hmap

/--
Weighted centered residual integrability from a bounded loading on the
score-cells that cover the sample almost everywhere.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_cell_bound
    {Cell : Type*} [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    (cells : Set Cell)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (outcome scoreVersion : Sample -> Real)
    (bound : Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover : ∀ᵐ sample ∂sampleLaw, score sample ∈ cells)
    (hbound : ∀ cell, cell ∈ cells -> ‖scale * loading cell‖ ≤ bound)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreVersion : Integrable scoreVersion sampleLaw) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersion sample))
      sampleLaw :=
  weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub score scale loading outcome scoreVersion bound hscore
    (scaledScoreCellLoading_ae_bound_of_cell_bound
      (mSample := mSample) (sampleLaw := sampleLaw) cells score scale loading
      bound hcover hbound)
    houtcome hscoreVersion

/--
Raw-outcome-integrability variant of the cell-bound weighted centered-residual
integrability theorem.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_cell_bound_outcomeIntegrable
    {Cell : Type*} [TopologicalSpace Cell] [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    (cells : Set Cell)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (outcome scoreVersion : Sample -> Real)
    (bound : Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover : ∀ᵐ sample ∂sampleLaw, score sample ∈ cells)
    (hbound : ∀ cell, cell ∈ cells -> ‖scale * loading cell‖ ≤ bound)
    (houtcome : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersion sample))
      sampleLaw := by
  have hscoreVersion : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact
    weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_cell_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scale loading outcome
      scoreVersion bound hscore hcover hbound houtcome hscoreVersion

/--
Weighted centered residual integrability from finite score-cell coverage.  The
finite absolute-sum of scaled cell loadings supplies the bound automatically.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_finset_abs_sum_bound
    {Cell : Type*} [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (outcome scoreVersion : Sample -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (houtcome : Integrable outcome sampleLaw)
    (hscoreVersion : Integrable scoreVersion sampleLaw) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersion sample))
      sampleLaw :=
  weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub score scale loading outcome scoreVersion
    (finiteScoreCellScaledLoadingAbsSumBound cells scale loading) hscore
    (scaledScoreCellLoading_ae_bound_of_finset_abs_sum_bound
      (mSample := mSample) (sampleLaw := sampleLaw) cells score scale loading
      hcover)
    houtcome hscoreVersion

/--
Raw-outcome-integrability variant of finite score-cell weighted
centered-residual integrability.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_finset_abs_sum_bound_outcomeIntegrable
    {Cell : Type*} [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (outcome scoreVersion : Sample -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (houtcome : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersion sample))
      sampleLaw := by
  have hscoreVersion : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact
    weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scale loading outcome
      scoreVersion hscore hcover houtcome hscoreVersion

/--
Weighted centered residual integrability for a finite score-cell type.  The
full finite cell partition supplies coverage and the finite absolute-sum bound.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_fintype_abs_sum_bound
    {Cell : Type*} [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (outcome scoreVersion : Sample -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreVersion : Integrable scoreVersion sampleLaw) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersion sample))
      sampleLaw :=
  weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub (Finset.univ : Finset Cell) score scale loading outcome
    scoreVersion hscore (Filter.Eventually.of_forall (fun sample => by simp))
    houtcome hscoreVersion

/--
Raw-outcome-integrability variant for finite score-cell types.
-/
theorem weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_fintype_abs_sum_bound_outcomeIntegrable
    {Cell : Type*} [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell]
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    (score : Sample -> Cell)
    (scale : Real)
    (loading : Cell -> Real)
    (outcome scoreVersion : Sample -> Real)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    Integrable
      (fun sample =>
        (scale * loading (score sample)) *
          (outcome sample - scoreVersion sample))
      sampleLaw := by
  have hscoreVersion : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact
    weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_fintype_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub score scale loading outcome scoreVersion
      hscore houtcome hscoreVersion

/--
Close the two-arm finite-array integrability component from loading bounds on
the treated and control score-cells that cover the sample almost everywhere.
-/
theorem twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_cell_bound
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    (hcontrolSub : controlScoreSigma ≤ mSample)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCells : Set TreatedCell)
    (controlCells : Set ControlCell)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedCover :
      ∀ᵐ sample ∂sampleLaw, treatedScore sample ∈ treatedCells)
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw, controlScore sample ∈ controlCells)
    (htreatedBound :
      ∀ cell, cell ∈ treatedCells ->
        ‖treatedScale * treatedLoading cell‖ ≤ treatedBound)
    (hcontrolBound :
      ∀ cell, cell ∈ controlCells ->
        ‖controlScale * controlLoading cell‖ ≤ controlBound)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_bound
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub b treatedScore controlScore treatedScale
    controlScale treatedLoading controlLoading treatedOutcome
    treatedScoreVersion controlOutcome controlScoreVersion treatedBound
    controlBound htreatedScore hcontrolScore
    (scaledScoreCellLoading_ae_bound_of_cell_bound
      (mSample := mSample) (sampleLaw := sampleLaw) treatedCells treatedScore
      treatedScale treatedLoading treatedBound htreatedCover htreatedBound)
    (scaledScoreCellLoading_ae_bound_of_cell_bound
      (mSample := mSample) (sampleLaw := sampleLaw) controlCells controlScore
      controlScale controlLoading controlBound hcontrolCover hcontrolBound)
    htreatedOutcome hcontrolOutcome htreatedScoreVersion
    hcontrolScoreVersion hmap

/--
Raw-outcome-integrability variant of the cell-bound two-arm finite-array
integrability component.
-/
theorem
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_cell_bound_outcomeIntegrable
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    (hcontrolSub : controlScoreSigma ≤ mSample)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCells : Set TreatedCell)
    (controlCells : Set ControlCell)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedCover :
      ∀ᵐ sample ∂sampleLaw, treatedScore sample ∈ treatedCells)
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw, controlScore sample ∈ controlCells)
    (htreatedBound :
      ∀ cell, cell ∈ treatedCells ->
        ‖treatedScale * treatedLoading cell‖ ≤ treatedBound)
    (hcontrolBound :
      ∀ cell, cell ∈ controlCells ->
        ‖controlScale * controlLoading cell‖ ≤ controlBound)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_cell_bound
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedCells controlCells treatedScore
      controlScore treatedScale controlScale treatedLoading controlLoading
      treatedOutcome treatedScoreVersion controlOutcome controlScoreVersion
      treatedBound controlBound htreatedScore hcontrolScore htreatedCover
      hcontrolCover htreatedBound hcontrolBound htreatedOutcome
      hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion hmap

/--
Close the two-arm finite-array integrability component from finite score-cell
coverage.  The finite absolute-sum bounds are constructed automatically.
-/
theorem twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_finset_abs_sum_bound
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
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
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
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
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_bound
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub b treatedScore controlScore treatedScale
    controlScale treatedLoading controlLoading treatedOutcome
    treatedScoreVersion controlOutcome controlScoreVersion
    (finiteScoreCellScaledLoadingAbsSumBound treatedCells treatedScale
      treatedLoading)
    (finiteScoreCellScaledLoadingAbsSumBound controlCells controlScale
      controlLoading)
    htreatedScore hcontrolScore
    (scaledScoreCellLoading_ae_bound_of_finset_abs_sum_bound
      (mSample := mSample) (sampleLaw := sampleLaw) treatedCells treatedScore
      treatedScale treatedLoading htreatedCover)
    (scaledScoreCellLoading_ae_bound_of_finset_abs_sum_bound
      (mSample := mSample) (sampleLaw := sampleLaw) controlCells controlScore
      controlScale controlLoading hcontrolCover)
    htreatedOutcome hcontrolOutcome htreatedScoreVersion
    hcontrolScoreVersion hmap

/--
Raw-outcome-integrability variant of the finite score-cell two-arm
finite-array integrability component.
-/
theorem
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_finset_abs_sum_bound_outcomeIntegrable
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
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
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
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
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_finset_abs_sum_bound
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedCells controlCells treatedScore
      controlScore treatedScale controlScale treatedLoading controlLoading
      treatedOutcome treatedScoreVersion controlOutcome controlScoreVersion
      htreatedScore hcontrolScore htreatedCover hcontrolCover
      htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion hmap

/--
Close the two-arm finite-array integrability component for finite treated and
control score-cell types.  Full finite partitions supply coverage and finite
absolute-sum bounds.
-/
theorem twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_fintype_abs_sum_bound
    [Fintype TreatedCell] [Fintype ControlCell]
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    (hcontrolSub : controlScoreSigma ≤ mSample)
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
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_finset_abs_sum_bound
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub b (Finset.univ : Finset TreatedCell)
    (Finset.univ : Finset ControlCell) treatedScore controlScore
    treatedScale controlScale treatedLoading controlLoading treatedOutcome
    treatedScoreVersion controlOutcome controlScoreVersion htreatedScore
    hcontrolScore (Filter.Eventually.of_forall (fun sample => by simp))
    (Filter.Eventually.of_forall (fun sample => by simp)) htreatedOutcome
    hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion hmap

/--
Raw-outcome-integrability variant for finite treated/control score-cell types.
-/
theorem
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_fintype_abs_sum_bound_outcomeIntegrable
    [Fintype TreatedCell] [Fintype ControlCell]
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    (hcontrolSub : controlScoreSigma ≤ mSample)
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
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (hmap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_fintype_abs_sum_bound
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion htreatedScore
      hcontrolScore htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion hmap

/--
Close two-arm coefficient predictability, weighted residual conditional
mean-zero, and finite-array integrability from one bounded discrete score-cell
loading representation.
-/
theorem twoArm_predictability_residual_mean_zero_and_integrability_components_of_discreteScore_scaledLoadings_bound
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
    (treatedBound controlBound : Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
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
        b.control_residual_conditional_mean_zero)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    ((b.treated_coefficient_predictability ∧
        b.control_coefficient_predictability) ∧
      (b.treated_residual_conditional_mean_zero ∧
        b.control_residual_conditional_mean_zero)) ∧
      b.finite_array_integrability := by
  have htreatedWeighted :
      Integrable
        (fun sample =>
          (treatedScale * treatedLoading (treatedScore sample)) *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw :=
    weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound
      (mSample := mSample) (scoreSigma := treatedScoreSigma)
      (sampleLaw := sampleLaw) htreatedSub treatedScore treatedScale
      treatedLoading treatedOutcome treatedScoreVersion treatedBound
      htreatedScore htreatedBound htreatedOutcome htreatedScoreVersion
  have hcontrolWeighted :
      Integrable
        (fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw :=
    weightedCenteredResidual_integrable_of_discreteScore_scaledLoading_bound
      (mSample := mSample) (scoreSigma := controlScoreSigma)
      (sampleLaw := sampleLaw) hcontrolSub controlScore controlScale
      controlLoading controlOutcome controlScoreVersion controlBound
      hcontrolScore hcontrolBound hcontrolOutcome hcontrolScoreVersion
  have hpredictableZero :
      (b.treated_coefficient_predictability ∧
          b.control_coefficient_predictability) ∧
        b.treated_residual_conditional_mean_zero ∧
          b.control_residual_conditional_mean_zero :=
    twoArm_predictability_and_residual_mean_zero_components_of_discreteScore_scaledLoadings
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion htreatedScore
      hcontrolScore htreatedPredictabilityMap hcontrolPredictabilityMap
      htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedWeighted hcontrolWeighted
      htreatedCond hcontrolCond htreatedZeroMap hcontrolZeroMap
  have hintegrable :
      b.finite_array_integrability :=
    twoArm_finite_array_integrability_component_of_discreteScore_scaledLoadings_bound
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion treatedBound
      controlBound htreatedScore hcontrolScore htreatedBound hcontrolBound
      htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion hintegrabilityMap
  exact ⟨⟨hpredictableZero.1, hpredictableZero.2⟩, hintegrable⟩

/--
Raw-outcome-integrability variant of the bounded two-arm predictability,
residual mean-zero, and finite-array integrability package.
-/
theorem
    twoArm_predictability_residual_mean_zero_and_integrability_components_of_discreteScore_scaledLoadings_bound_outcomeIntegrable
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
    (treatedBound controlBound : Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
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
        b.control_residual_conditional_mean_zero)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    ((b.treated_coefficient_predictability ∧
        b.control_coefficient_predictability) ∧
      (b.treated_residual_conditional_mean_zero ∧
        b.control_residual_conditional_mean_zero)) ∧
      b.finite_array_integrability := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    twoArm_predictability_residual_mean_zero_and_integrability_components_of_discreteScore_scaledLoadings_bound
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion treatedBound
      controlBound htreatedScore hcontrolScore htreatedBound hcontrolBound
      htreatedPredictabilityMap hcontrolPredictabilityMap htreatedOutcome
      hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion
      htreatedScoreVersionMeas hcontrolScoreVersionMeas htreatedCond
      hcontrolCond htreatedZeroMap hcontrolZeroMap hintegrabilityMap

/--
Close the two-arm martingale-difference component from bounded discrete
score-cell coefficient loadings, centered-residual conditional mean identities,
and an explicit sampling/filtration regularity proof.
-/
theorem martingale_difference_array_of_discreteScore_scaledLoadings_bound
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
    (treatedBound controlBound : Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
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
        b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.martingale_difference_array := by
  have hcomponents :
      ((b.treated_coefficient_predictability ∧
          b.control_coefficient_predictability) ∧
        (b.treated_residual_conditional_mean_zero ∧
          b.control_residual_conditional_mean_zero)) ∧
        b.finite_array_integrability :=
    twoArm_predictability_residual_mean_zero_and_integrability_components_of_discreteScore_scaledLoadings_bound
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion treatedBound
      controlBound htreatedScore hcontrolScore htreatedBound hcontrolBound
      htreatedPredictabilityMap hcontrolPredictabilityMap htreatedOutcome
      hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion
      htreatedScoreVersionMeas hcontrolScoreVersionMeas htreatedCond
      hcontrolCond htreatedZeroMap hcontrolZeroMap hintegrabilityMap
  obtain ⟨⟨hpredictable, hzero⟩, hintegrable⟩ := hcomponents
  exact
    martingale_difference_array_of_twoArm_residual_bridge b
      hpredictable.1 hpredictable.2 hzero.1 hzero.2 hregular
      hintegrable

/--
Raw-outcome-integrability variant of the bounded score-cell
martingale-difference array wrapper.
-/
theorem martingale_difference_array_of_discreteScore_scaledLoadings_bound_outcomeIntegrable
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
    (treatedBound controlBound : Real)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
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
        b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability) :
    b.martingale_difference_array := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    martingale_difference_array_of_discreteScore_scaledLoadings_bound
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion treatedBound
      controlBound htreatedScore hcontrolScore htreatedBound hcontrolBound
      htreatedPredictabilityMap hcontrolPredictabilityMap htreatedOutcome
      hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion
      htreatedScoreVersionMeas hcontrolScoreVersionMeas htreatedCond
      hcontrolCond htreatedZeroMap hcontrolZeroMap hregular
      hintegrabilityMap

/--
Residual CLT/variance input from bounded discrete score-cell coefficient
loadings, centered-residual conditional mean identities, and an explicit
sampling/filtration regularity proof.

This theorem keeps the generic martingale CLT, conditional Lindeberg, reuse
moment limits, residual regularity, and predictable-QV stabilization as the
explicit probability inputs.
-/
theorem residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_bound_bridge_input
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
    (harrayMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
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
        b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidualRegularity
    (harrayMap
      (martingale_difference_array_of_discreteScore_scaledLoadings_bound
        (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
        (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
        htreatedSub hcontrolSub b treatedScore controlScore treatedScale
        controlScale treatedLoading controlLoading treatedOutcome
        treatedScoreVersion controlOutcome controlScoreVersion treatedBound
        controlBound htreatedScore hcontrolScore htreatedBound hcontrolBound
        htreatedPredictabilityMap hcontrolPredictabilityMap htreatedOutcome
        hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion
        htreatedScoreVersionMeas hcontrolScoreVersionMeas htreatedCond
        hcontrolCond htreatedZeroMap hcontrolZeroMap hregular
        hintegrabilityMap))
    hlindeberg hquad

/--
Raw-outcome-integrability variant of the bounded score-cell residual
CLT/variance bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_bound_bridge_input_outcomeIntegrable
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
    (harrayMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
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
        b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            (treatedScale * treatedLoading (treatedScore sample)) *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_bound_bridge_input
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub input b treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion treatedBound
      controlBound harrayMap hmoments hresidualRegularity htreatedScore
      hcontrolScore htreatedBound hcontrolBound htreatedPredictabilityMap
      hcontrolPredictabilityMap htreatedOutcome hcontrolOutcome
      htreatedScoreVersion hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedCond hcontrolCond htreatedZeroMap
      hcontrolZeroMap hregular hintegrabilityMap hlindeberg hquad

/--
Residual CLT/variance input from bounded discrete score-cell coefficient
loadings and explicit sampling/filtration regularity components.

This is the most expanded score-cell entry point: all martingale-difference
components except the external martingale CLT are reduced to named WDSM
probability obligations.
-/
theorem residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_bound_sampling_bridge_input
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
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
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
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
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
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
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
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
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_bound_bridge_input
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub input martingaleBridge treatedScore controlScore
    treatedScale controlScale treatedLoading controlLoading treatedOutcome
    treatedScoreVersion controlOutcome controlScoreVersion treatedBound
    controlBound harrayMap hmoments hresidualRegularity htreatedScore
    hcontrolScore htreatedBound hcontrolBound htreatedPredictabilityMap
    hcontrolPredictabilityMap htreatedOutcome hcontrolOutcome
    htreatedScoreVersion hcontrolScoreVersion htreatedScoreVersionMeas
    hcontrolScoreVersionMeas htreatedCond hcontrolCond htreatedZeroMap
    hcontrolZeroMap
    (arm_sampling_or_filtration_regular_component_of_bridge
      martingaleBridge regularityBridge hregularityMap hfiltration
      htreatedAdapted hcontrolAdapted htreatedInnovation hcontrolInnovation
      horder hcross hdesign)
    hintegrabilityMap hlindeberg hquad

/--
Raw-outcome-integrability variant of the bounded score-cell residual
CLT/variance sampling bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_bound_sampling_bridge_input_outcomeIntegrable
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
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
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedScore :
      AEStronglyMeasurable[treatedScoreSigma] treatedScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[controlScoreSigma] controlScore sampleLaw)
    (htreatedBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖treatedScale * treatedLoading (treatedScore sample)‖ ≤
          treatedBound)
    (hcontrolBound :
      ∀ᵐ sample ∂sampleLaw,
        ‖controlScale * controlLoading (controlScore sample)‖ ≤
          controlBound)
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
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
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
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
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
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_bound_sampling_bridge_input
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub input martingaleBridge regularityBridge
      treatedScore controlScore treatedScale controlScale treatedLoading
      controlLoading treatedOutcome treatedScoreVersion controlOutcome
      controlScoreVersion treatedBound controlBound harrayMap hmoments
      hresidualRegularity htreatedScore hcontrolScore htreatedBound
      hcontrolBound htreatedPredictabilityMap hcontrolPredictabilityMap
      htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedCond hcontrolCond htreatedZeroMap
      hcontrolZeroMap hregularityMap hfiltration htreatedAdapted
      hcontrolAdapted htreatedInnovation hcontrolInnovation horder hcross
      hdesign hintegrabilityMap hlindeberg hquad

/--
Residual CLT/variance input from score-cell coverage, cellwise bounded
discrete score-cell loadings, and explicit sampling/filtration regularity
components.

This variant discharges the measure-level bounded-loading premises from
almost-everywhere cell coverage and cellwise loading bounds before invoking
the bounded-loading score-cell bridge.
-/
theorem residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_cell_bound_sampling_bridge_input
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (treatedCells : Set TreatedCell)
    (controlCells : Set ControlCell)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
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
      ∀ᵐ sample ∂sampleLaw, treatedScore sample ∈ treatedCells)
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw, controlScore sample ∈ controlCells)
    (htreatedCellBound :
      ∀ cell, cell ∈ treatedCells ->
        ‖treatedScale * treatedLoading cell‖ ≤ treatedBound)
    (hcontrolCellBound :
      ∀ cell, cell ∈ controlCells ->
        ‖controlScale * controlLoading cell‖ ≤ controlBound)
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
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
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
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
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
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_bound_sampling_bridge_input
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub input martingaleBridge regularityBridge
    treatedScore controlScore treatedScale controlScale treatedLoading
    controlLoading treatedOutcome treatedScoreVersion controlOutcome
    controlScoreVersion treatedBound controlBound harrayMap hmoments
    hresidualRegularity htreatedScore hcontrolScore
    (scaledScoreCellLoading_ae_bound_of_cell_bound
      (mSample := mSample) (sampleLaw := sampleLaw) treatedCells treatedScore
      treatedScale treatedLoading treatedBound htreatedCover
      htreatedCellBound)
    (scaledScoreCellLoading_ae_bound_of_cell_bound
      (mSample := mSample) (sampleLaw := sampleLaw) controlCells controlScore
      controlScale controlLoading controlBound hcontrolCover
      hcontrolCellBound)
    htreatedPredictabilityMap hcontrolPredictabilityMap htreatedOutcome
    hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion
    htreatedScoreVersionMeas hcontrolScoreVersionMeas htreatedCond
    hcontrolCond htreatedZeroMap hcontrolZeroMap hregularityMap
    hfiltration htreatedAdapted hcontrolAdapted htreatedInnovation
    hcontrolInnovation horder hcross hdesign hintegrabilityMap hlindeberg
    hquad

/--
Raw-outcome-integrability variant of the cell-bound score-cell residual
CLT/variance sampling bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_cell_bound_sampling_bridge_input_outcomeIntegrable
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (treatedCells : Set TreatedCell)
    (controlCells : Set ControlCell)
    (treatedScore : Sample -> TreatedCell)
    (controlScore : Sample -> ControlCell)
    (treatedScale controlScale : Real)
    (treatedLoading : TreatedCell -> Real)
    (controlLoading : ControlCell -> Real)
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
    (treatedBound controlBound : Real)
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
      ∀ᵐ sample ∂sampleLaw, treatedScore sample ∈ treatedCells)
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw, controlScore sample ∈ controlCells)
    (htreatedCellBound :
      ∀ cell, cell ∈ treatedCells ->
        ‖treatedScale * treatedLoading cell‖ ≤ treatedBound)
    (hcontrolCellBound :
      ∀ cell, cell ∈ controlCells ->
        ‖controlScale * controlLoading cell‖ ≤ controlBound)
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
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
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
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
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
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_cell_bound_sampling_bridge_input
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub input martingaleBridge regularityBridge
      treatedCells controlCells treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion treatedBound
      controlBound harrayMap hmoments hresidualRegularity htreatedScore
      hcontrolScore htreatedCover hcontrolCover htreatedCellBound
      hcontrolCellBound htreatedPredictabilityMap hcontrolPredictabilityMap
      htreatedOutcome hcontrolOutcome htreatedScoreVersion
      hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedCond hcontrolCond htreatedZeroMap
      hcontrolZeroMap hregularityMap hfiltration htreatedAdapted
      hcontrolAdapted htreatedInnovation hcontrolInnovation horder hcross
      hdesign hintegrabilityMap hlindeberg hquad

/--
Residual CLT/variance input from finite score-cell coverage and explicit
sampling/filtration regularity components.  The finite absolute-sum envelopes
of the treated/control scaled cell loadings supply the bounded-loading
premises automatically.
-/
theorem residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_finset_abs_sum_bound_sampling_bridge_input
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
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
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
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
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
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
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
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
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_cell_bound_sampling_bridge_input
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub input martingaleBridge regularityBridge
    (treatedCells : Set TreatedCell) (controlCells : Set ControlCell)
    treatedScore controlScore treatedScale controlScale treatedLoading
    controlLoading treatedOutcome treatedScoreVersion controlOutcome
    controlScoreVersion
    (finiteScoreCellScaledLoadingAbsSumBound treatedCells treatedScale
      treatedLoading)
    (finiteScoreCellScaledLoadingAbsSumBound controlCells controlScale
      controlLoading)
    harrayMap hmoments hresidualRegularity htreatedScore hcontrolScore
    htreatedCover hcontrolCover
    (fun cell hcell =>
      finiteScoreCellScaledLoadingAbsSumBound_cell_bound treatedCells
        treatedScale treatedLoading cell (by simpa using hcell))
    (fun cell hcell =>
      finiteScoreCellScaledLoadingAbsSumBound_cell_bound controlCells
        controlScale controlLoading cell (by simpa using hcell))
    htreatedPredictabilityMap hcontrolPredictabilityMap htreatedOutcome
    hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion
    htreatedScoreVersionMeas hcontrolScoreVersionMeas htreatedCond
    hcontrolCond htreatedZeroMap hcontrolZeroMap hregularityMap
    hfiltration htreatedAdapted hcontrolAdapted htreatedInnovation
    hcontrolInnovation horder hcross hdesign hintegrabilityMap hlindeberg
    hquad

/--
Raw-outcome-integrability variant of the finite score-cell residual
CLT/variance sampling bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_finset_abs_sum_bound_sampling_bridge_input_outcomeIntegrable
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
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
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
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
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
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
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
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
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_finset_abs_sum_bound_sampling_bridge_input
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub input martingaleBridge regularityBridge
      treatedCells controlCells treatedScore controlScore treatedScale
      controlScale treatedLoading controlLoading treatedOutcome
      treatedScoreVersion controlOutcome controlScoreVersion harrayMap
      hmoments hresidualRegularity htreatedScore hcontrolScore
      htreatedCover hcontrolCover htreatedPredictabilityMap
      hcontrolPredictabilityMap htreatedOutcome hcontrolOutcome
      htreatedScoreVersion hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedCond hcontrolCond htreatedZeroMap
      hcontrolZeroMap hregularityMap hfiltration htreatedAdapted
      hcontrolAdapted htreatedInnovation hcontrolInnovation horder hcross
      hdesign hintegrabilityMap hlindeberg hquad

/--
Residual CLT/variance input for finite treated and control score-cell types.
Full finite partitions supply coverage, and finite absolute-sum envelopes
supply bounded-loading premises automatically.
-/
theorem residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_fintype_abs_sum_bound_sampling_bridge_input
    [Fintype TreatedCell] [Fintype ControlCell]
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
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
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
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
    (htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
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
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
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
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_finset_abs_sum_bound_sampling_bridge_input
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub input martingaleBridge regularityBridge
    (Finset.univ : Finset TreatedCell) (Finset.univ : Finset ControlCell)
    treatedScore controlScore treatedScale controlScale treatedLoading
    controlLoading treatedOutcome treatedScoreVersion controlOutcome
    controlScoreVersion harrayMap hmoments hresidualRegularity htreatedScore
    hcontrolScore (Filter.Eventually.of_forall (fun sample => by simp))
    (Filter.Eventually.of_forall (fun sample => by simp))
    htreatedPredictabilityMap hcontrolPredictabilityMap htreatedOutcome
    hcontrolOutcome htreatedScoreVersion hcontrolScoreVersion
    htreatedScoreVersionMeas hcontrolScoreVersionMeas htreatedCond
    hcontrolCond htreatedZeroMap hcontrolZeroMap hregularityMap
    hfiltration htreatedAdapted hcontrolAdapted htreatedInnovation
    hcontrolInnovation horder hcross hdesign hintegrabilityMap hlindeberg
    hquad

/--
Raw-outcome-integrability variant of the finite-type score-cell residual
CLT/variance sampling bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_fintype_abs_sum_bound_sampling_bridge_input_outcomeIntegrable
    [Fintype TreatedCell] [Fintype ControlCell]
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    [TopologicalSpace TreatedCell] [DiscreteTopology TreatedCell]
    [TopologicalSpace ControlCell] [DiscreteTopology ControlCell]
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
    (treatedOutcome treatedScoreVersion : Sample -> Real)
    (controlOutcome controlScoreVersion : Sample -> Real)
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
    (htreatedScoreVersionMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreVersionMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
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
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          (controlScale * controlLoading (controlScore sample)) *
            (controlOutcome sample - controlScoreVersion sample)) |
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
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            (controlScale * controlLoading (controlScore sample)) *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have htreatedScoreVersion : Integrable treatedScoreVersion sampleLaw :=
    integrable_condExp.congr htreatedCond
  have hcontrolScoreVersion : Integrable controlScoreVersion sampleLaw :=
    integrable_condExp.congr hcontrolCond
  exact
    residual_clt_and_variance_formula_of_discreteScore_scaledLoadings_fintype_abs_sum_bound_sampling_bridge_input
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      htreatedSub hcontrolSub input martingaleBridge regularityBridge
      treatedScore controlScore treatedScale controlScale treatedLoading
      controlLoading treatedOutcome treatedScoreVersion controlOutcome
      controlScoreVersion harrayMap hmoments hresidualRegularity
      htreatedScore hcontrolScore htreatedPredictabilityMap
      hcontrolPredictabilityMap htreatedOutcome hcontrolOutcome
      htreatedScoreVersion hcontrolScoreVersion htreatedScoreVersionMeas
      hcontrolScoreVersionMeas htreatedCond hcontrolCond htreatedZeroMap
      hcontrolZeroMap hregularityMap hfiltration htreatedAdapted
      hcontrolAdapted htreatedInnovation hcontrolInnovation horder hcross
      hdesign hintegrabilityMap hlindeberg hquad

end WDSM
end Matching
end StatInference
