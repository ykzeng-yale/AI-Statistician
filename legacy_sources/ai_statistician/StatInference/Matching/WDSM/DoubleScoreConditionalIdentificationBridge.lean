import Mathlib.MeasureTheory.Function.ConditionalExpectation.PullOut
import Mathlib.Probability.IdentDistrib
import StatInference.Matching.WDSM.ConditionalExpectationBridge
import StatInference.Matching.WDSM.DiscreteDoubleScoreBalancing
import StatInference.Matching.WDSM.PopulationSelectionDensityDesign
import StatInference.Matching.WDSM.PopulationSurveyIdentificationBridge
import StatInference.Matching.WDSM.ScoreCellConditionalIdentificationBridge

/-!
# Double-score conditional identification bridge

This module specializes the finite score-cell conditional identification layer
to the concrete double-score maps used by the WDSM finite estimator algebra.
It keeps the conditional-mean assumptions explicit, but rewrites their score
versions into the same `pateDoubleScore` and `pattDoubleScore` cell functions
used by the deterministic survey-weighted recovery modules.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory
open scoped BigOperators

variable {Sample PropensityCell TreatedProgCell ControlProgCell : Type*}
variable [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
PATE population identification with conditional means represented by the
PATE double score `(propensity, treated prognostic, control prognostic)`.
-/
theorem populationPATE_eq_scorePATE_of_condExp_pateDoubleScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    repr.populationPATE =
      (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
        (∫ sample, controlValue (controlPrognosticScore sample) ∂sampleLaw) := by
  simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore,
    controlCellValueOnPATEDoubleScore] using
    (populationPATE_eq_scorePATE_of_condExp_scoreCellVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      treatedOutcome controlOutcome
      (treatedCellValueOnPATEDoubleScore treatedValue)
      (controlCellValueOnPATEDoubleScore controlValue)
      hreprT hreprC
      (by
        simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
          htreated)
      (by
        simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
          hcontrol))

/--
Selected-sample Hájek PATE identification with conditional means represented
by the PATE double score.
-/
theorem selectedHajekPATE_eq_scorePATE_of_condExp_pateDoubleScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    repr.selectedHajekPATE =
      (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
        (∫ sample, controlValue (controlPrognosticScore sample) ∂sampleLaw) := by
  simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore,
    controlCellValueOnPATEDoubleScore] using
    (selectedHajekPATE_eq_scorePATE_of_condExp_scoreCellVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr htreatedSampling hcontrolSampling
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      treatedOutcome controlOutcome
      (treatedCellValueOnPATEDoubleScore treatedValue)
      (controlCellValueOnPATEDoubleScore controlValue)
      hreprT hreprC
      (by
        simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
          htreated)
      (by
        simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
          hcontrol))

/--
PATT population identification with numerator and denominator score versions
represented by the PATT double score `(propensity, control prognostic)`.
-/
theorem populationPATT_eq_scorePATT_of_condExp_pattDoubleScoreVersions
    {PATTProgCell : Type*}
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (controlPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample))
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)) :
    repr.populationPATT =
      (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) /
        (∫ sample,
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) :=
  populationPATT_eq_scorePATT_of_condExp_scoreCellVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr (pattDoubleScore propensityScore controlPrognosticScore)
    treatedEffectNumerator treatedMass scoreEffectCellValue
    scoreTreatedMassCellValue hreprNumerator hreprMass hnumerator hmass

/--
Selected-sample Hájek PATT identification with numerator and denominator score
versions represented by the PATT double score.
-/
theorem selectedHajekPATT_eq_scorePATT_of_condExp_pattDoubleScoreVersions
    {PATTProgCell : Type*}
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreatedMass : repr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (controlPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample))
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)) :
    repr.selectedHajekPATT =
      (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) /
        (∫ sample,
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) :=
  selectedHajekPATT_eq_scorePATT_of_condExp_scoreCellVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr hsampling htreatedMass
    (pattDoubleScore propensityScore controlPrognosticScore)
    treatedEffectNumerator treatedMass scoreEffectCellValue
    scoreTreatedMassCellValue hreprNumerator hreprMass hnumerator hmass

/--
Paired population PATE/PATT identification with conditional means represented
by the corresponding WDSM double scores.
-/
theorem populationPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions
    {PATTProgCell : Type*}
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.populationPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.populationPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  constructor
  · exact
      populationPATE_eq_scorePATE_of_condExp_pateDoubleScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr propensityScore
        treatedPrognosticScore controlPrognosticScore treatedOutcome
        controlOutcome treatedValue controlValue hreprT hreprC htreated
        hcontrol
  · exact
      populationPATT_eq_scorePATT_of_condExp_pattDoubleScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr propensityScore
        pattPrognosticScore treatedEffectNumerator treatedMass
        scoreEffectCellValue scoreTreatedMassCellValue hreprNumerator
        hreprMass hnumerator hmass

/--
Paired selected-sample Hájek PATE/PATT identification with conditional means
represented by the corresponding WDSM double scores.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions
    {PATTProgCell : Type*}
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  constructor
  · exact
      selectedHajekPATE_eq_scorePATE_of_condExp_pateDoubleScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr htreatedSampling
        hcontrolSampling propensityScore treatedPrognosticScore
        controlPrognosticScore treatedOutcome controlOutcome treatedValue
        controlValue hreprT hreprC htreated hcontrol
  · exact
      selectedHajekPATT_eq_scorePATT_of_condExp_pattDoubleScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr hpattSampling hpattMass
        propensityScore pattPrognosticScore treatedEffectNumerator
        treatedMass scoreEffectCellValue scoreTreatedMassCellValue
        hreprNumerator hreprMass hnumerator hmass

/--
PATE double-score conditional-mean identities from almost-everywhere equality
to finite PATE double-score versions.
-/
theorem condExp_pateDoubleScoreVersions_of_ae_finiteScoreVersions_finset_abs_sum_bound
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (cells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample) := by
  constructor
  · simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
      (condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub cells
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore)
        (treatedCellValueOnPATEDoubleScore treatedValue) treatedOutcome
        hscore hcover
        (by
          simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
            htreated))
  · simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
      (condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub cells
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore)
        (controlCellValueOnPATEDoubleScore controlValue) controlOutcome
        hscore hcover
        (by
          simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
            hcontrol))

/--
PATT double-score conditional-mean identities from almost-everywhere equality
to finite PATT double-score versions.
-/
theorem condExp_pattDoubleScoreVersions_of_ae_finiteScoreVersions_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (cells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (controlPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore controlPrognosticScore) sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore controlPrognosticScore sample ∈
          (cells : Set (PropensityCell × PATTProgCell)))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)) :
    sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)) ∧
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample) := by
  constructor
  · exact
      condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub cells
        (pattDoubleScore propensityScore controlPrognosticScore)
        scoreEffectCellValue treatedEffectNumerator hscore hcover hnumerator
  · exact
      condExp_ae_eq_scoreCellVersion_of_ae_eq_discreteScore_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub cells
        (pattDoubleScore propensityScore controlPrognosticScore)
        scoreTreatedMassCellValue treatedMass hscore hcover hmass

/--
Paired PATE/PATT double-score conditional-mean identities from
almost-everywhere equality to finite double-score versions.
-/
theorem condExp_doubleScoreVersions_of_ae_finiteScoreVersions_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpateCover :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (pateCells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (hpattCover :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (pattCells : Set (PropensityCell × PATTProgCell)))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  constructor
  · exact
      condExp_pateDoubleScoreVersions_of_ae_finiteScoreVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateCells propensityScore
        treatedPrognosticScore controlPrognosticScore treatedOutcome
        controlOutcome treatedValue controlValue hpateScore hpateCover
        htreated hcontrol
  · exact
      condExp_pattDoubleScoreVersions_of_ae_finiteScoreVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattCells propensityScore
        pattPrognosticScore treatedEffectNumerator treatedMass
        scoreEffectCellValue scoreTreatedMassCellValue hpattScore hpattCover
        hnumerator hmass

/--
Finite deterministic PATE double-score route premise.  This is the local
target that a Yang-Zhang/Antonelli probability route must eventually provide.
-/
abbrev PATEFiniteDoubleScoreRoute
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real) : Prop :=
  AEStronglyMeasurable[scoreSigma]
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore) sampleLaw ∧
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore sample ∈
        (pateCells : Set
          ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
    (treatedOutcome =ᵐ[sampleLaw]
      fun sample => treatedValue (treatedPrognosticScore sample)) ∧
    (controlOutcome =ᵐ[sampleLaw]
      fun sample => controlValue (controlPrognosticScore sample))

/--
Finite deterministic PATT double-score route premise.  This is the local
target that a Yang-Zhang/Antonelli probability route must eventually provide.
-/
abbrev PATTFiniteDoubleScoreRoute
    {PATTProgCell : Type*}
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) : Prop :=
  AEStronglyMeasurable[scoreSigma]
      (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw ∧
    (∀ᵐ sample ∂sampleLaw,
      pattDoubleScore propensityScore pattPrognosticScore sample ∈
        (pattCells : Set (PropensityCell × PATTProgCell))) ∧
    (treatedEffectNumerator =ᵐ[sampleLaw]
      fun sample =>
        scoreEffectCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
    (treatedMass =ᵐ[sampleLaw]
      fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample))

/--
Package finite Yang-Zhang-route score-version hypotheses into the exact
a.e. PATE/PATT double-score premise consumed by the conditional-expectation
adapters.
-/
theorem ae_doubleScoreVersions_of_yangZhang_route_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hroute :
      PATEFiniteDoubleScoreRoute
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) pateCells propensityScore
          treatedPrognosticScore controlPrognosticScore treatedOutcome
          controlOutcome treatedValue controlValue ∧
        PATTFiniteDoubleScoreRoute
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) pattCells propensityScore
          pattPrognosticScore treatedEffectNumerator treatedMass
          scoreEffectCellValue scoreTreatedMassCellValue) :
    AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw ∧
      (∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (pateCells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (pattCells : Set (PropensityCell × PATTProgCell))) ∧
      (treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      (controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      (treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      (treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) := by
  rcases hroute with
    ⟨⟨hpateScore, hpateCover, htreated, hcontrol⟩,
      ⟨hpattScore, hpattCover, hnumerator, hmass⟩⟩
  exact
    ⟨hpateScore, hpateCover, hpattScore, hpattCover, htreated, hcontrol,
      hnumerator, hmass⟩

/--
Build the finite PATE double-score route from component score measurability,
finite component covers, and explicit score-version equalities.
-/
theorem PATEFiniteDoubleScoreRoute_of_componentScoreRoutes_finset_abs_sum_bound
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpropensityCover :
      ∀ᵐ sample ∂sampleLaw,
        propensityScore sample ∈ (propensityCells : Set PropensityCell))
    (htreatedCover :
      ∀ᵐ sample ∂sampleLaw,
        treatedPrognosticScore sample ∈
          (treatedProgCells : Set TreatedProgCell))
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw,
        controlPrognosticScore sample ∈
          (controlProgCells : Set ControlProgCell))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    PATEFiniteDoubleScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw)
      ((propensityCells.product treatedProgCells).product controlProgCells)
      propensityScore treatedPrognosticScore controlPrognosticScore
      treatedOutcome controlOutcome treatedValue controlValue := by
  constructor
  · simpa [pateDoubleScore] using
      ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore)
  · constructor
    · filter_upwards [hpropensityCover, htreatedCover, hcontrolCover] with
        sample hpropensity htreatedCell hcontrolCell
      simp [pateDoubleScore, hpropensity, htreatedCell, hcontrolCell]
    · exact ⟨htreated, hcontrol⟩

/--
Build the finite PATT double-score route from component score measurability,
finite component covers, and explicit numerator/mass score-version equalities.
-/
theorem PATTFiniteDoubleScoreRoute_of_componentScoreRoutes_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    (propensityCells : Finset PropensityCell)
    (pattProgCells : Finset PATTProgCell)
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityCover :
      ∀ᵐ sample ∂sampleLaw,
        propensityScore sample ∈ (propensityCells : Set PropensityCell))
    (hpattCover :
      ∀ᵐ sample ∂sampleLaw,
        pattPrognosticScore sample ∈ (pattProgCells : Set PATTProgCell))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    PATTFiniteDoubleScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) (propensityCells.product pattProgCells)
      propensityScore pattPrognosticScore treatedEffectNumerator treatedMass
      scoreEffectCellValue scoreTreatedMassCellValue := by
  constructor
  · simpa [pattDoubleScore] using hpropensityScore.prodMk hpattScore
  · constructor
    · filter_upwards [hpropensityCover, hpattCover] with
        sample hpropensity hpattCell
      simp [pattDoubleScore, hpropensity, hpattCell]
    · exact ⟨hnumerator, hmass⟩

/--
Paired component-level route adapter for the finite WDSM double scores.
The only remaining paper-level content is in the supplied a.e. score-version
equalities and component score measurability/coverage hypotheses.
-/
theorem finiteDoubleScoreRoutes_of_componentScoreRoutes_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityCover :
      ∀ᵐ sample ∂sampleLaw,
        propensityScore sample ∈ (propensityCells : Set PropensityCell))
    (htreatedCover :
      ∀ᵐ sample ∂sampleLaw,
        treatedPrognosticScore sample ∈
          (treatedProgCells : Set TreatedProgCell))
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw,
        controlPrognosticScore sample ∈
          (controlProgCells : Set ControlProgCell))
    (hpattCover :
      ∀ᵐ sample ∂sampleLaw,
        pattPrognosticScore sample ∈ (pattProgCells : Set PATTProgCell))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    PATEFiniteDoubleScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw)
        ((propensityCells.product treatedProgCells).product controlProgCells)
        propensityScore treatedPrognosticScore controlPrognosticScore
        treatedOutcome controlOutcome treatedValue controlValue ∧
      PATTFiniteDoubleScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) (propensityCells.product pattProgCells)
        propensityScore pattPrognosticScore treatedEffectNumerator treatedMass
        scoreEffectCellValue scoreTreatedMassCellValue := by
  constructor
  · exact
      PATEFiniteDoubleScoreRoute_of_componentScoreRoutes_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) propensityCells treatedProgCells
        controlProgCells propensityScore treatedPrognosticScore
        controlPrognosticScore treatedOutcome controlOutcome treatedValue
        controlValue hpropensityScore htreatedScore hcontrolScore
        hpropensityCover htreatedCover hcontrolCover htreated hcontrol
  · exact
      PATTFiniteDoubleScoreRoute_of_componentScoreRoutes_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) propensityCells pattProgCells
        propensityScore pattPrognosticScore treatedEffectNumerator treatedMass
        scoreEffectCellValue scoreTreatedMassCellValue hpropensityScore
        hpattScore hpropensityCover hpattCover hnumerator hmass

/--
Component-score route adapter into the exact a.e. PATE/PATT double-score
premise consumed by the conditional-expectation bridge.  This discharges the
joint-score measurability and finite double-score coverage parts from
component score routes; the substantive paper-level probability step remains
the supplied a.e. score-version equalities.
-/
theorem ae_doubleScoreVersions_of_componentScoreRoutes_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityCover :
      ∀ᵐ sample ∂sampleLaw,
        propensityScore sample ∈ (propensityCells : Set PropensityCell))
    (htreatedCover :
      ∀ᵐ sample ∂sampleLaw,
        treatedPrognosticScore sample ∈
          (treatedProgCells : Set TreatedProgCell))
    (hcontrolCover :
      ∀ᵐ sample ∂sampleLaw,
        controlPrognosticScore sample ∈
          (controlProgCells : Set ControlProgCell))
    (hpattCover :
      ∀ᵐ sample ∂sampleLaw,
        pattPrognosticScore sample ∈ (pattProgCells : Set PATTProgCell))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw ∧
      (∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (((propensityCells.product treatedProgCells).product
            controlProgCells) : Set
              ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
      (treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      (controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      (treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      (treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) := by
  exact
    ae_doubleScoreVersions_of_yangZhang_route_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw)
      ((propensityCells.product treatedProgCells).product controlProgCells)
      (propensityCells.product pattProgCells) propensityScore
      treatedPrognosticScore controlPrognosticScore pattPrognosticScore
      treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
      (finiteDoubleScoreRoutes_of_componentScoreRoutes_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) propensityCells treatedProgCells
        controlProgCells pattProgCells propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue
        hpropensityScore htreatedScore hcontrolScore hpattScore
        hpropensityCover htreatedCover hcontrolCover hpattCover htreated
        hcontrol hnumerator hmass)

/--
Tower-property adapter for a correct-score route.  If a score version is the
conditional mean at a richer covariate sigma-field and is measurable for the
smaller score sigma-field, then it is also the conditional mean at the score
sigma-field.
-/
theorem condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
    {covariateSigma : MeasurableSpace Sample}
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (outcome scoreVersion : Sample -> Real)
    (hcov :
      sampleLaw[outcome | covariateSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw) :
    sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion := by
  have htower :
      sampleLaw[sampleLaw[outcome | covariateSigma] | scoreSigma] =ᵐ[
          sampleLaw]
        sampleLaw[outcome | scoreSigma] :=
    condExp_condExp_of_le
      (μ := sampleLaw) (m₁ := scoreSigma) (m₂ := covariateSigma)
      (m₀ := mSample) hscoreCov hcovSub
  have hcongr :
      sampleLaw[sampleLaw[outcome | covariateSigma] | scoreSigma] =ᵐ[
          sampleLaw]
        sampleLaw[scoreVersion | scoreSigma] :=
    condExp_congr_ae (m := scoreSigma) (μ := sampleLaw) hcov
  have hscoreIntegrable : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcov
  have hself :
      sampleLaw[scoreVersion | scoreSigma] =ᵐ[sampleLaw] scoreVersion :=
    condExp_of_aestronglyMeasurable'
      (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw)
      (hscoreCov.trans hcovSub) hscoreMeas hscoreIntegrable
  exact htower.symm.trans (hcongr.trans hself)

/--
Primitive residual-zero correct-score route.  If an outcome decomposes into a
conditioning-sigma measurable score version plus a residual whose conditional
mean is zero, then the score version is the conditional mean of the outcome.

This is the local prognostic-score step used below: it does not assume the
desired conditional-mean equality, and it does not strengthen conditional
means into pointwise a.e. equalities.
-/
theorem condExp_scoreVersion_of_residual_correctScoreRoute
    {conditioningSigma : MeasurableSpace Sample}
    (hsub : conditioningSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion residual : Sample -> Real)
    (hscoreMeas :
      AEStronglyMeasurable[conditioningSigma] scoreVersion sampleLaw)
    (hscoreInt : Integrable scoreVersion sampleLaw)
    (hresidualInt : Integrable residual sampleLaw)
    (hdecomp :
      outcome =ᵐ[sampleLaw]
        fun sample => scoreVersion sample + residual sample)
    (hresidualZero :
      sampleLaw[residual | conditioningSigma] =ᵐ[sampleLaw] 0) :
    sampleLaw[outcome | conditioningSigma] =ᵐ[sampleLaw] scoreVersion := by
  have hcongr :
      sampleLaw[outcome | conditioningSigma] =ᵐ[sampleLaw]
        sampleLaw[(fun sample => scoreVersion sample + residual sample) |
          conditioningSigma] :=
    condExp_congr_ae (m := conditioningSigma) (μ := sampleLaw) hdecomp
  have hadd :
      sampleLaw[(fun sample => scoreVersion sample + residual sample) |
          conditioningSigma] =ᵐ[sampleLaw]
        sampleLaw[scoreVersion | conditioningSigma] +
          sampleLaw[residual | conditioningSigma] :=
    condExp_add (μ := sampleLaw) hscoreInt hresidualInt conditioningSigma
  have hself :
      sampleLaw[scoreVersion | conditioningSigma] =ᵐ[sampleLaw]
        scoreVersion :=
    condExp_of_aestronglyMeasurable'
      (m := conditioningSigma) (m₀ := mSample) (μ := sampleLaw)
      hsub hscoreMeas hscoreInt
  refine hcongr.trans (hadd.trans ?_)
  refine (hself.add hresidualZero).trans ?_
  exact Filter.Eventually.of_forall fun sample => by simp

/--
Subtraction-residual version of the primitive correct-score route.  The
residual is defined as `outcome - scoreVersion`, so the decomposition and
residual integrability are proved locally.  The remaining probabilistic input
is exactly the zero conditional mean of that subtraction residual.
-/
theorem condExp_scoreVersion_of_subResidual_zero_correctScoreRoute
    {conditioningSigma : MeasurableSpace Sample}
    (hsub : conditioningSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (hscoreMeas :
      AEStronglyMeasurable[conditioningSigma] scoreVersion sampleLaw)
    (houtcomeInt : Integrable outcome sampleLaw)
    (hscoreInt : Integrable scoreVersion sampleLaw)
    (hresidualZero :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          conditioningSigma] =ᵐ[sampleLaw] 0) :
    sampleLaw[outcome | conditioningSigma] =ᵐ[sampleLaw] scoreVersion :=
  condExp_scoreVersion_of_residual_correctScoreRoute
    (mSample := mSample) (sampleLaw := sampleLaw) hsub outcome scoreVersion
    (fun sample => outcome sample - scoreVersion sample) hscoreMeas hscoreInt
    (houtcomeInt.sub hscoreInt)
    (Filter.Eventually.of_forall fun sample => by ring)
    hresidualZero

/--
Correct-score conditional means imply zero conditional mean for the explicit
subtraction residual.  This is the converse direction needed by paper-style
routes: from `E[Y | primitive] = g(score)` and primitive measurability of
`g(score)`, derive `E[Y - g(score) | primitive] = 0`.
-/
theorem condExp_subResidual_zero_of_condExp_scoreVersion
    {conditioningSigma : MeasurableSpace Sample}
    (hsub : conditioningSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (hcond :
      sampleLaw[outcome | conditioningSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[conditioningSigma] scoreVersion sampleLaw)
    (houtcomeInt : Integrable outcome sampleLaw)
    (hscoreInt : Integrable scoreVersion sampleLaw) :
    sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
        conditioningSigma] =ᵐ[sampleLaw] 0 := by
  have hsubExp :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          conditioningSigma] =ᵐ[sampleLaw]
        sampleLaw[outcome | conditioningSigma] -
          sampleLaw[scoreVersion | conditioningSigma] :=
    condExp_sub (μ := sampleLaw) houtcomeInt hscoreInt conditioningSigma
  have hself :
      sampleLaw[scoreVersion | conditioningSigma] =ᵐ[sampleLaw]
        scoreVersion :=
    condExp_of_aestronglyMeasurable'
      (m := conditioningSigma) (m₀ := mSample) (μ := sampleLaw)
      hsub hscoreMeas hscoreInt
  refine hsubExp.trans ?_
  refine (hcond.sub hself).trans ?_
  exact Filter.Eventually.of_forall fun sample => by simp

/--
Outcome-integrable variant of
`condExp_subResidual_zero_of_condExp_scoreVersion`.  The score-version
integrability premise is derived from the conditional-mean identity itself.
-/
theorem condExp_subResidual_zero_of_condExp_scoreVersion_outcomeIntegrable
    {conditioningSigma : MeasurableSpace Sample}
    (hsub : conditioningSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (hcond :
      sampleLaw[outcome | conditioningSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[conditioningSigma] scoreVersion sampleLaw)
    (houtcomeInt : Integrable outcome sampleLaw) :
    sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
        conditioningSigma] =ᵐ[sampleLaw] 0 :=
  condExp_subResidual_zero_of_condExp_scoreVersion
    (mSample := mSample) (sampleLaw := sampleLaw) hsub outcome scoreVersion
    hcond hscoreMeas houtcomeInt (integrable_condExp.congr hcond)

/--
Conditional-mean transport across an a.e. target replacement.  This is the
local adapter for consistency/selection-transport steps in a paper route: once
an observed target agrees a.e. with a transported target, any primitive
correct-score conditional mean for the transported target is also the
conditional mean of the observed target.
-/
theorem condExp_scoreVersion_of_ae_targetTransport_correctScoreRoute
    {conditioningSigma : MeasurableSpace Sample}
    (outcome transportedTarget scoreVersion : Sample -> Real)
    (htransport : outcome =ᵐ[sampleLaw] transportedTarget)
    (hcond :
      sampleLaw[transportedTarget | conditioningSigma] =ᵐ[sampleLaw]
        scoreVersion) :
    sampleLaw[outcome | conditioningSigma] =ᵐ[sampleLaw] scoreVersion :=
  (condExp_congr_ae (m := conditioningSigma) (μ := sampleLaw)
    htransport).trans hcond

/--
Zero subtraction-residual route after transporting an observed target to a
latent/reference target.  The residual is still the observed residual
`outcome - scoreVersion`; Lean derives its zero conditional mean from a.e.
target transport plus the latent/reference correct-score conditional mean.
-/
theorem condExp_subResidual_zero_of_ae_targetTransport_correctScoreRoute
    {conditioningSigma : MeasurableSpace Sample}
    (hsub : conditioningSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (outcome transportedTarget scoreVersion : Sample -> Real)
    (htransport : outcome =ᵐ[sampleLaw] transportedTarget)
    (hcond :
      sampleLaw[transportedTarget | conditioningSigma] =ᵐ[sampleLaw]
        scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[conditioningSigma] scoreVersion sampleLaw)
    (htargetInt : Integrable transportedTarget sampleLaw) :
    sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
        conditioningSigma] =ᵐ[sampleLaw] 0 :=
  condExp_subResidual_zero_of_condExp_scoreVersion_outcomeIntegrable
    (mSample := mSample) (sampleLaw := sampleLaw) hsub outcome scoreVersion
    (condExp_scoreVersion_of_ae_targetTransport_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) outcome transportedTarget
      scoreVersion htransport hcond)
    hscoreMeas
    (htargetInt.congr htransport.symm)

/--
Integrability transport across an a.e. target replacement.  This lets paper
routes state integrability for latent/reference targets and recover the
observed-target integrability required by downstream Hájek endpoints.
-/
theorem integrable_of_ae_targetTransport
    (outcome transportedTarget : Sample -> Real)
    (htransport : outcome =ᵐ[sampleLaw] transportedTarget)
    (htargetInt : Integrable transportedTarget sampleLaw) :
    Integrable outcome sampleLaw :=
  htargetInt.congr htransport.symm

/--
Integral transport across an a.e. target replacement.
-/
theorem integral_eq_of_ae_targetTransport
    (outcome transportedTarget : Sample -> Real)
    (htransport : outcome =ᵐ[sampleLaw] transportedTarget) :
    (∫ sample, outcome sample ∂sampleLaw) =
      ∫ sample, transportedTarget sample ∂sampleLaw :=
  integral_congr_ae htransport

/--
Nonzero integral transport across an a.e. target replacement.
-/
theorem integral_ne_zero_of_ae_targetTransport
    (outcome transportedTarget : Sample -> Real)
    (htransport : outcome =ᵐ[sampleLaw] transportedTarget)
    (htargetNonzero :
      (∫ sample, transportedTarget sample ∂sampleLaw) ≠ 0) :
    (∫ sample, outcome sample ∂sampleLaw) ≠ 0 := by
  rwa [integral_eq_of_ae_targetTransport
    (mSample := mSample) (sampleLaw := sampleLaw) outcome transportedTarget
    htransport]

/--
Nonnegativity transport across an a.e. target replacement.
-/
theorem ae_nonneg_of_ae_targetTransport
    (outcome transportedTarget : Sample -> Real)
    (htransport : outcome =ᵐ[sampleLaw] transportedTarget)
    (htargetNonneg : 0 ≤ᵐ[sampleLaw] transportedTarget) :
    0 ≤ᵐ[sampleLaw] outcome := by
  filter_upwards [htransport, htargetNonneg] with sample hEq hnonneg
  simpa [hEq] using hnonneg

/--
Paired PATE/PATT primitive correct-score conditional means after transporting
the four observed WDSM targets to latent/reference targets.  This keeps
treatment/survey transport as a.e. target equalities and keeps the
correct-score content as conditional-mean identities for the transported
targets.
-/
theorem primitiveCondExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute
    {PATTProgCell : Type*} {primitiveSigma : MeasurableSpace Sample}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  constructor
  · constructor
    · exact
        condExp_scoreVersion_of_ae_targetTransport_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw) treatedOutcome
          treatedTarget
          (fun sample => treatedValue (treatedPrognosticScore sample))
          htreatedTransport htreatedTargetCond
    · exact
        condExp_scoreVersion_of_ae_targetTransport_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw) controlOutcome
          controlTarget
          (fun sample => controlValue (controlPrognosticScore sample))
          hcontrolTransport hcontrolTargetCond
  · constructor
    · exact
        condExp_scoreVersion_of_ae_targetTransport_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw)
          treatedEffectNumerator effectTarget
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          hnumeratorTransport hnumeratorTargetCond
    · exact
        condExp_scoreVersion_of_ae_targetTransport_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw) treatedMass
          massTarget
          (fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          hmassTransport hmassTargetCond

/--
Primitive latent/reference correct-score identities from stronger a.e. target
score-version equalities.  This is a valid fallback only for references or
paper assumptions that actually state the stronger target-equals-score-version
premises; it does not infer those a.e. equalities from ignorability.
-/
theorem primitiveTargetCondExp_doubleScoreVersions_of_ae_targetScoreVersions_of_le
    {PATTProgCell : Type*} {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace TreatedProgCell] [TopologicalSpace ControlProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology TreatedProgCell] [DiscreteTopology ControlProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (heffectTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  have hpattScorePrimitive :
      AEStronglyMeasurable[primitiveSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw := by
    simpa [pattDoubleScore] using
      (hpropensityScore.mono hscorePrimitive).prodMk
        (hpattComponentScore.mono hscorePrimitive)
  constructor
  · constructor
    · exact
        condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
          (mSample := mSample) (scoreSigma := primitiveSigma)
          (sampleLaw := sampleLaw) hprimitiveSub treatedTarget
          (fun sample => treatedValue (treatedPrognosticScore sample))
          htreatedTargetVersion
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := primitiveSigma)
            (sampleLaw := sampleLaw) treatedPrognosticScore treatedValue
            (htreatedScore.mono hscorePrimitive))
          htreatedTargetInt
    · exact
        condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
          (mSample := mSample) (scoreSigma := primitiveSigma)
          (sampleLaw := sampleLaw) hprimitiveSub controlTarget
          (fun sample => controlValue (controlPrognosticScore sample))
          hcontrolTargetVersion
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := primitiveSigma)
            (sampleLaw := sampleLaw) controlPrognosticScore controlValue
            (hcontrolScore.mono hscorePrimitive))
          hcontrolTargetInt
  · constructor
    · exact
        condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
          (mSample := mSample) (scoreSigma := primitiveSigma)
          (sampleLaw := sampleLaw) hprimitiveSub effectTarget
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          heffectTargetVersion
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := primitiveSigma)
            (sampleLaw := sampleLaw)
            (pattDoubleScore propensityScore pattPrognosticScore)
            scoreEffectCellValue hpattScorePrimitive)
          heffectTargetInt
    · exact
        condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
          (mSample := mSample) (scoreSigma := primitiveSigma)
          (sampleLaw := sampleLaw) hprimitiveSub massTarget
          (fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          hmassTargetVersion
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := primitiveSigma)
            (sampleLaw := sampleLaw)
            (pattDoubleScore propensityScore pattPrognosticScore)
            scoreTreatedMassCellValue hpattScorePrimitive)
          hmassTargetInt

/--
Observed-integrability variant of
`primitiveTargetCondExp_doubleScoreVersions_of_ae_targetScoreVersions_of_le`.
It proves the same primitive target conditional-mean identities, but derives
latent/reference target integrability from observed WDSM target integrability
and a.e. observed-to-target transport.
-/
theorem primitiveTargetCondExp_doubleScoreVersions_of_ae_targetScoreVersions_outcomeIntegrable_of_le
    {PATTProgCell : Type*} {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace TreatedProgCell] [TopologicalSpace ControlProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology TreatedProgCell] [DiscreteTopology ControlProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (heffectTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  primitiveTargetCondExp_doubleScoreVersions_of_ae_targetScoreVersions_of_le
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub propensityScore
    treatedPrognosticScore controlPrognosticScore pattPrognosticScore
    treatedTarget controlTarget effectTarget massTarget treatedValue
    controlValue scoreEffectCellValue scoreTreatedMassCellValue
    hpropensityScore htreatedScore hcontrolScore hpattComponentScore
    (htreatedOutcomeInt.congr htreatedTransport)
    (hcontrolOutcomeInt.congr hcontrolTransport)
    (hnumeratorOutcomeInt.congr hnumeratorTransport)
    (hmassOutcomeInt.congr hmassTransport) htreatedTargetVersion
    hcontrolTargetVersion heffectTargetVersion hmassTargetVersion

/--
Score-sigma latent/reference target conditional means from stronger a.e.
target score-version equalities.  This direct variant avoids introducing a
larger primitive sigma-field when a reference already supplies a.e.
latent/reference target score versions.
-/
theorem condExp_targetDoubleScoreVersions_of_component_ae_targetScoreVersions
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (heffectTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedTarget | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | scoreSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[massTarget | scoreSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  have hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw := by
    simpa [pattDoubleScore] using
      hpropensityScore.prodMk hpattComponentScore
  constructor
  · constructor
    · exact
        condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedTarget
          (fun sample => treatedValue (treatedPrognosticScore sample))
          htreatedTargetVersion
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := scoreSigma)
            (sampleLaw := sampleLaw) treatedPrognosticScore treatedValue
            htreatedScore)
          htreatedTargetInt
    · exact
        condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub controlTarget
          (fun sample => controlValue (controlPrognosticScore sample))
          hcontrolTargetVersion
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := scoreSigma)
            (sampleLaw := sampleLaw) controlPrognosticScore controlValue
            hcontrolScore)
          hcontrolTargetInt
  · constructor
    · exact
        condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub effectTarget
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          heffectTargetVersion
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := scoreSigma)
            (sampleLaw := sampleLaw)
            (pattDoubleScore propensityScore pattPrognosticScore)
            scoreEffectCellValue hpattScore)
          heffectTargetInt
    · exact
        condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub massTarget
          (fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          hmassTargetVersion
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := scoreSigma)
            (sampleLaw := sampleLaw)
            (pattDoubleScore propensityScore pattPrognosticScore)
            scoreTreatedMassCellValue hpattScore)
          hmassTargetInt

/--
Observed-integrability variant of
`condExp_targetDoubleScoreVersions_of_component_ae_targetScoreVersions`.
It proves the direct score-sigma target conditional-mean identities from
observed WDSM target integrability, a.e. observed-to-target transport, and
a.e. latent/reference target score versions.
-/
theorem condExp_targetDoubleScoreVersions_of_component_ae_targetScoreVersions_outcomeIntegrable
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (heffectTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedTarget | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | scoreSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[massTarget | scoreSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  condExp_targetDoubleScoreVersions_of_component_ae_targetScoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub propensityScore treatedPrognosticScore
    controlPrognosticScore pattPrognosticScore treatedTarget controlTarget
    effectTarget massTarget treatedValue controlValue scoreEffectCellValue
    scoreTreatedMassCellValue hpropensityScore htreatedScore hcontrolScore
    hpattComponentScore (htreatedOutcomeInt.congr htreatedTransport)
    (hcontrolOutcomeInt.congr hcontrolTransport)
    (hnumeratorOutcomeInt.congr hnumeratorTransport)
    (hmassOutcomeInt.congr hmassTransport) htreatedTargetVersion
    hcontrolTargetVersion heffectTargetVersion hmassTargetVersion

/--
Tower transport for zero residual conditional means.  A residual with zero
conditional mean at a richer primitive sigma-field also has zero conditional
mean at any smaller sigma-field.
-/
theorem condExp_zero_of_condExp_zero_of_le
    {smallSigma primitiveSigma : MeasurableSpace Sample}
    (hsmallPrimitive : smallSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hsmallPrimitive.trans hprimitiveSub))]
    (residual : Sample -> Real)
    (hprimitiveZero :
      sampleLaw[residual | primitiveSigma] =ᵐ[sampleLaw] 0) :
    sampleLaw[residual | smallSigma] =ᵐ[sampleLaw] 0 := by
  have htower :
      sampleLaw[sampleLaw[residual | primitiveSigma] | smallSigma] =ᵐ[
          sampleLaw]
        sampleLaw[residual | smallSigma] :=
    condExp_condExp_of_le
      (μ := sampleLaw) (m₁ := smallSigma) (m₂ := primitiveSigma)
      (m₀ := mSample) hsmallPrimitive hprimitiveSub
  have hcongr :
      sampleLaw[sampleLaw[residual | primitiveSigma] | smallSigma] =ᵐ[
          sampleLaw]
        sampleLaw[(0 : Sample -> Real) | smallSigma] :=
    condExp_congr_ae (m := smallSigma) (μ := sampleLaw) hprimitiveZero
  have hzero :
      sampleLaw[(0 : Sample -> Real) | smallSigma] =ᵐ[sampleLaw] 0 := by
    rw [condExp_zero]
  exact htower.symm.trans (hcongr.trans hzero)

/--
Nonnegativity transfer through a score-version conditional-mean identity.
This is useful for denominator variables such as the PATT treated mass: it
proves nonnegativity of the score version from nonnegativity of the raw
variable, but does not assert the stronger nonzero/positive-mass condition.
-/
theorem scoreVersion_nonneg_of_condExp_scoreVersion_nonneg
    {conditioningSigma : MeasurableSpace Sample}
    (outcome scoreVersion : Sample -> Real)
    (hcond :
      sampleLaw[outcome | conditioningSigma] =ᵐ[sampleLaw] scoreVersion)
    (hnonneg : 0 ≤ᵐ[sampleLaw] outcome) :
    0 ≤ᵐ[sampleLaw] scoreVersion := by
  have hcondNonneg :
      0 ≤ᵐ[sampleLaw] sampleLaw[outcome | conditioningSigma] :=
    condExp_nonneg (μ := sampleLaw) (m := conditioningSigma) hnonneg
  filter_upwards [hcondNonneg, hcond] with sample hsample hEq
  simpa [hEq] using hsample

/--
Finite-sum assembly for conditional score versions.  It lets a covariate-level
score-version identity be proved termwise and then assembled with
`condExp_finsetSum`.
-/
theorem condExp_finsetSum_scoreVersions_of_condExp_scoreVersions
    {ι : Type*} {conditioningSigma : MeasurableSpace Sample}
    (terms : Finset ι)
    (summand scoreSummand : ι -> Sample -> Real)
    (hsummandInt :
      ∀ index, index ∈ terms -> Integrable (summand index) sampleLaw)
    (hcond :
      ∀ index, index ∈ terms ->
        sampleLaw[summand index | conditioningSigma] =ᵐ[sampleLaw]
          scoreSummand index) :
    sampleLaw[(fun sample => terms.sum (fun index => summand index sample)) |
        conditioningSigma] =ᵐ[sampleLaw]
      fun sample => terms.sum (fun index => scoreSummand index sample) := by
  have hsummandFun :
      (fun sample => terms.sum (fun index => summand index sample)) =
        terms.sum (fun index => summand index) := by
    funext sample
    simp
  have hscoreFun :
      (fun sample => terms.sum (fun index => scoreSummand index sample)) =
        terms.sum (fun index => scoreSummand index) := by
    funext sample
    simp
  rw [hsummandFun, hscoreFun]
  exact
    ((condExp_finsetSum (μ := sampleLaw) (s := terms) (f := summand)
      hsummandInt conditioningSigma).trans
      (eventuallyEq_sum fun index hindex => hcond index hindex))

/--
Finite-sum score measurability from termwise score measurability.  This local
version keeps the auxiliary score sigma-field explicit.
-/
theorem aestronglyMeasurable_finsetSum_of_aestronglyMeasurable
    {ι : Type*} [DecidableEq ι]
    (terms : Finset ι) (summand : ι -> Sample -> Real)
    (hsummand :
      ∀ index, index ∈ terms ->
        AEStronglyMeasurable[scoreSigma] (summand index) sampleLaw) :
    AEStronglyMeasurable[scoreSigma]
      (fun sample => terms.sum (fun index => summand index sample))
      sampleLaw := by
  induction terms using Finset.induction_on with
  | empty =>
      simpa using
        (MeasureTheory.aestronglyMeasurable_const
          (μ := sampleLaw) (b := (0 : Real)) :
          AEStronglyMeasurable[scoreSigma]
            (fun _sample : Sample => (0 : Real)) sampleLaw)
  | insert index terms hnotmem ih =>
      simpa [Finset.sum_insert hnotmem] using
        MeasureTheory.AEStronglyMeasurable.add
          (hsummand index (Finset.mem_insert_self index terms))
          (ih fun term hterm =>
            hsummand term (Finset.mem_insert_of_mem hterm))

/--
Pull a score-measurable weight out of a conditional score-version identity.
This is the local algebra needed for survey/treatment weights once their
score-measurability and integrability side conditions have been proved.
-/
theorem condExp_weightedScoreVersion_of_condExp_scoreVersion
    {conditioningSigma : MeasurableSpace Sample}
    (weight outcome scoreVersion : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[conditioningSigma] weight sampleLaw)
    (hweightedInt :
      Integrable (fun sample => weight sample * outcome sample) sampleLaw)
    (houtcomeInt : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | conditioningSigma] =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample => weight sample * outcome sample) |
        conditioningSigma] =ᵐ[sampleLaw]
      fun sample => weight sample * scoreVersion sample := by
  exact
    (condExp_mul_of_aestronglyMeasurable_left
      (μ := sampleLaw) (m := conditioningSigma) hweightMeas hweightedInt
      houtcomeInt).trans
      ((Filter.EventuallyEq.refl (ae sampleLaw) weight).mul hcond)

/--
Weighted covariate correct-score route.  A score-measurable survey/treatment
weight can be pulled out after the covariate-level correct-score identity has
been pushed down to the score sigma-field by the tower property.
-/
theorem condExp_weightedScoreVersion_of_covariate_correctScoreRoute
    {covariateSigma : MeasurableSpace Sample}
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (weight outcome scoreVersion : Sample -> Real)
    (hweightMeas : AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hweightedInt :
      Integrable (fun sample => weight sample * outcome sample) sampleLaw)
    (houtcomeInt : Integrable outcome sampleLaw)
    (hcov :
      sampleLaw[outcome | covariateSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreVersionMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw) :
    sampleLaw[(fun sample => weight sample * outcome sample) | scoreSigma]
        =ᵐ[sampleLaw]
      fun sample => weight sample * scoreVersion sample := by
  exact
    condExp_weightedScoreVersion_of_condExp_scoreVersion
      (mSample := mSample) (sampleLaw := sampleLaw)
      weight outcome scoreVersion hweightMeas hweightedInt houtcomeInt
      (condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub outcome scoreVersion hcov
        hscoreVersionMeas)

/--
Finite-sum covariate-to-score transport.  Termwise covariate conditional-mean
identities can be summed and then pushed down to the score sigma-field by the
tower property, provided the summed score version is assembled from
score-measurable terms.
-/
theorem condExp_finsetSum_scoreVersions_of_covariate_correctScoreRoute
    {ι : Type*} [DecidableEq ι]
    {covariateSigma : MeasurableSpace Sample}
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (terms : Finset ι)
    (summand scoreSummand : ι -> Sample -> Real)
    (hsummandInt :
      ∀ index, index ∈ terms -> Integrable (summand index) sampleLaw)
    (hcov :
      ∀ index, index ∈ terms ->
        sampleLaw[summand index | covariateSigma] =ᵐ[sampleLaw]
          scoreSummand index)
    (hscoreSummand :
      ∀ index, index ∈ terms ->
        AEStronglyMeasurable[scoreSigma] (scoreSummand index) sampleLaw) :
    sampleLaw[(fun sample => terms.sum (fun index => summand index sample)) |
        scoreSigma] =ᵐ[sampleLaw]
      fun sample => terms.sum (fun index => scoreSummand index sample) := by
  have hscoreFun :
      (fun sample => terms.sum (fun index => scoreSummand index sample)) =
        terms.sum (fun index => scoreSummand index) := by
    funext sample
    simp
  have hscoreSum :
      AEStronglyMeasurable[scoreSigma]
        (fun sample => terms.sum (fun index => scoreSummand index sample))
        sampleLaw := by
    exact
      aestronglyMeasurable_finsetSum_of_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) terms scoreSummand hscoreSummand
  exact
    condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovSub
      (fun sample => terms.sum (fun index => summand index sample))
      (fun sample => terms.sum (fun index => scoreSummand index sample))
      (condExp_finsetSum_scoreVersions_of_condExp_scoreVersions
        (mSample := mSample) (sampleLaw := sampleLaw)
        (conditioningSigma := covariateSigma) terms summand scoreSummand
        hsummandInt hcov)
      hscoreSum

/--
Law-transfer adapter for finite score coverage.  If a reference score and the
current WDSM score are identically distributed, then a measurable finite-cover
event transfers from the reference law to the current sample law.
-/
theorem ae_finiteScoreCover_of_identDistrib
    {ReferenceSample CurrentSample Cell : Type*}
    [mReference : MeasurableSpace ReferenceSample]
    [mCurrent : MeasurableSpace CurrentSample]
    [MeasurableSpace Cell]
    {referenceLaw : Measure[mReference] ReferenceSample}
    {currentLaw : Measure[mCurrent] CurrentSample}
    (cells : Finset Cell)
    (referenceScore : ReferenceSample -> Cell)
    (score : CurrentSample -> Cell)
    (hident :
      ProbabilityTheory.IdentDistrib
        (α := ReferenceSample) (β := CurrentSample) (γ := Cell)
        referenceScore score referenceLaw currentLaw)
    (hcellsMeas : MeasurableSet (cells : Set Cell))
    (hrefCover :
      ∀ᵐ reference ∂referenceLaw,
        referenceScore reference ∈ (cells : Set Cell)) :
    ∀ᵐ sample ∂currentLaw, score sample ∈ (cells : Set Cell) :=
  hident.ae_snd hcellsMeas hrefCover

/--
Has-law adapter for finite score coverage.  If the law of a score is supported
on a measurable finite cell set, then the score itself is a.e. covered by that
finite partition.
-/
theorem ae_finiteScoreCover_of_hasLaw
    {CurrentSample Cell : Type*}
    [mCurrent : MeasurableSpace CurrentSample]
    [MeasurableSpace Cell]
    {currentLaw : Measure[mCurrent] CurrentSample}
    {scoreLaw : Measure Cell}
    (cells : Finset Cell)
    (score : CurrentSample -> Cell)
    (hscoreLaw :
      ProbabilityTheory.HasLaw score scoreLaw currentLaw)
    (hcellsMeas : MeasurableSet (cells : Set Cell))
    (hlawCover :
      ∀ᵐ cell ∂scoreLaw, cell ∈ (cells : Set Cell)) :
    ∀ᵐ sample ∂currentLaw, score sample ∈ (cells : Set Cell) :=
  (hscoreLaw.ae_iff (by simpa using hcellsMeas)).2 hlawCover

/--
PATE product-cell finite coverage from component score laws supported on their
finite partitions.
-/
theorem ae_pateDoubleScoreCover_of_component_hasLaw
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) :
    ∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)) := by
  have hpropensityCover :
      ∀ᵐ sample ∂sampleLaw,
        propensityScore sample ∈
          (propensityCells : Set PropensityCell) :=
    ae_finiteScoreCover_of_hasLaw
      (mCurrent := mSample) (currentLaw := sampleLaw)
      propensityCells propensityScore
      hpropensityLaw hpropensityCellsMeas hpropensityCoverLaw
  have htreatedCover :
      ∀ᵐ sample ∂sampleLaw,
        treatedPrognosticScore sample ∈
          (treatedProgCells : Set TreatedProgCell) :=
    ae_finiteScoreCover_of_hasLaw
      (mCurrent := mSample) (currentLaw := sampleLaw)
      treatedProgCells treatedPrognosticScore
      htreatedLaw htreatedCellsMeas htreatedCoverLaw
  have hcontrolCover :
      ∀ᵐ sample ∂sampleLaw,
        controlPrognosticScore sample ∈
          (controlProgCells : Set ControlProgCell) :=
    ae_finiteScoreCover_of_hasLaw
      (mCurrent := mSample) (currentLaw := sampleLaw)
      controlProgCells controlPrognosticScore
      hcontrolLaw hcontrolCellsMeas hcontrolCoverLaw
  filter_upwards [hpropensityCover, htreatedCover, hcontrolCover] with
    sample hpropensity htreated hcontrol
  simp [pateDoubleScore, hpropensity, htreated, hcontrol]

/--
PATT product-cell finite coverage from component score laws supported on their
finite partitions.
-/
theorem ae_pattDoubleScoreCover_of_component_hasLaw
    {PATTProgCell : Type*}
    [MeasurableSpace PropensityCell] [MeasurableSpace PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    (propensityCells : Finset PropensityCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) :
    ∀ᵐ sample ∂sampleLaw,
      pattDoubleScore propensityScore pattPrognosticScore sample ∈
        (propensityCells.product pattProgCells :
          Set (PropensityCell × PATTProgCell)) := by
  have hpropensityCover :
      ∀ᵐ sample ∂sampleLaw,
        propensityScore sample ∈
          (propensityCells : Set PropensityCell) :=
    ae_finiteScoreCover_of_hasLaw
      (currentLaw := sampleLaw) propensityCells propensityScore
      hpropensityLaw hpropensityCellsMeas hpropensityCoverLaw
  have hpattCover :
      ∀ᵐ sample ∂sampleLaw,
        pattPrognosticScore sample ∈
          (pattProgCells : Set PATTProgCell) :=
    ae_finiteScoreCover_of_hasLaw
      (mCurrent := mSample) (currentLaw := sampleLaw)
      pattProgCells pattPrognosticScore
      hpattLaw hpattCellsMeas hpattCoverLaw
  filter_upwards [hpropensityCover, hpattCover] with
    sample hpropensity hpatt
  simp [pattDoubleScore, hpropensity, hpatt]

/--
Primitive component-law route into the finite a.e. PATE/PATT double-score
version premise.  Component `HasLaw` support supplies the finite-cover
obligations; the substantive Yang-Zhang/Antonelli probability content remains
the explicit score-version equalities.
-/
theorem ae_doubleScoreVersions_of_yangZhang_component_hasLaw_route_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw ∧
      (∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (((propensityCells.product treatedProgCells).product
            controlProgCells) : Set
              ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
      (treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      (controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      (treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      (treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) := by
  exact
    ⟨by
      simpa [pateDoubleScore] using
        ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore),
    ae_pateDoubleScoreCover_of_component_hasLaw
      (mSample := mSample) (sampleLaw := sampleLaw)
      propensityCells treatedProgCells controlProgCells propensityScore
      treatedPrognosticScore controlPrognosticScore hpropensityLaw
      htreatedLaw hcontrolLaw hpropensityCellsMeas htreatedCellsMeas
      hcontrolCellsMeas hpropensityCoverLaw htreatedCoverLaw
      hcontrolCoverLaw,
    by
      simpa [pattDoubleScore] using hpropensityScore.prodMk hpattScore,
    ae_pattDoubleScoreCover_of_component_hasLaw
      (mSample := mSample) (sampleLaw := sampleLaw)
      propensityCells pattProgCells propensityScore pattPrognosticScore
      hpropensityLaw hpattLaw hpropensityCellsMeas hpattCellsMeas
      hpropensityCoverLaw hpattCoverLaw,
    htreated, hcontrol, hnumerator, hmass⟩

/--
PATE double-score conditional-mean route from covariate-level correct
prognostic-score identities.  The joint double score includes the treated and
control prognostic components, so score-measurability plus the tower property
pushes the covariate conditional means down to the double-score sigma-field.
-/
theorem condExp_pateDoubleScoreVersions_of_covariate_correctPrognosticRoute
    {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (htreatedCov :
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolCov :
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample) := by
  constructor
  · simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
      (condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub treatedOutcome
        (fun sample =>
          treatedCellValueOnPATEDoubleScore treatedValue
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore sample))
        (by
          simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
            htreatedCov)
        (scoreCellLoading_aestronglyMeasurable_of_discreteScore
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw)
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue) hpateScore))
  · simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
      (condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub controlOutcome
        (fun sample =>
          controlCellValueOnPATEDoubleScore controlValue
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore sample))
        (by
          simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
            hcontrolCov)
        (scoreCellLoading_aestronglyMeasurable_of_discreteScore
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw)
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (controlCellValueOnPATEDoubleScore controlValue) hpateScore))

/--
Weighted PATE treated-outcome conditional-mean identity from the covariate
correct prognostic-score route.  This is the survey-weighted treated-arm
version of the pull-out/tower argument.
-/
theorem condExp_weightedPATEScoreTreatedOutcome_of_covariate_correctPrognosticRoute
    {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hweightedInt :
      Integrable (fun sample => weight sample * treatedOutcome sample)
        sampleLaw)
    (htreatedInt : Integrable treatedOutcome sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (htreatedCov :
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample)) :
    sampleLaw[(fun sample => weight sample * treatedOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
      fun sample => weight sample * treatedValue (treatedPrognosticScore sample) := by
  simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
    (condExp_weightedScoreVersion_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovSub weight treatedOutcome
      (fun sample =>
        treatedCellValueOnPATEDoubleScore treatedValue
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore sample))
      hweightMeas hweightedInt htreatedInt
      (by
        simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
          htreatedCov)
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw)
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore)
        (treatedCellValueOnPATEDoubleScore treatedValue) hpateScore))

/--
Weighted PATE control-outcome conditional-mean identity from the covariate
correct prognostic-score route.  This is the survey-weighted control-arm
version of the pull-out/tower argument.
-/
theorem condExp_weightedPATEScoreControlOutcome_of_covariate_correctPrognosticRoute
    {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (controlOutcome : Sample -> Real)
    (controlValue : ControlProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hweightedInt :
      Integrable (fun sample => weight sample * controlOutcome sample)
        sampleLaw)
    (hcontrolInt : Integrable controlOutcome sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hcontrolCov :
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    sampleLaw[(fun sample => weight sample * controlOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
      fun sample => weight sample * controlValue (controlPrognosticScore sample) := by
  simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
    (condExp_weightedScoreVersion_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovSub weight controlOutcome
      (fun sample =>
        controlCellValueOnPATEDoubleScore controlValue
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore sample))
      hweightMeas hweightedInt hcontrolInt
      (by
        simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
          hcontrolCov)
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw)
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore)
        (controlCellValueOnPATEDoubleScore controlValue) hpateScore))

/--
PATT double-score conditional-mean route from covariate-level score-version
identities for the treated-effect numerator and treated-mass denominator.
-/
theorem condExp_pattDoubleScoreVersions_of_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (hnumeratorCov :
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  constructor
  · exact
      condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub treatedEffectNumerator
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        hnumeratorCov
        (scoreCellLoading_aestronglyMeasurable_of_discreteScore
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw)
          (pattDoubleScore propensityScore pattPrognosticScore)
          scoreEffectCellValue hpattScore)
  · exact
      condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub treatedMass
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        hmassCov
        (scoreCellLoading_aestronglyMeasurable_of_discreteScore
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw)
          (pattDoubleScore propensityScore pattPrognosticScore)
          scoreTreatedMassCellValue hpattScore)

/--
Covariate-level PATE/PATT correct-score identities from primitive residual
mean-zero assumptions.  This is the local Yang-Zhang/Antonelli prognostic
route in residual form: each target variable is decomposed into its score
version plus a residual whose covariate conditional mean is zero.
-/
theorem covariate_condExp_doubleScoreVersions_of_residual_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedResidual controlResidual numeratorResidual massResidual :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[covariateSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedResidualInt : Integrable treatedResidual sampleLaw)
    (hcontrolResidualInt : Integrable controlResidual sampleLaw)
    (hnumeratorResidualInt : Integrable numeratorResidual sampleLaw)
    (hmassResidualInt : Integrable massResidual sampleLaw)
    (htreatedDecomp :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          treatedValue (treatedPrognosticScore sample) +
            treatedResidual sample)
    (hcontrolDecomp :
      controlOutcome =ᵐ[sampleLaw]
        fun sample =>
          controlValue (controlPrognosticScore sample) +
            controlResidual sample)
    (hnumeratorDecomp :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) +
            numeratorResidual sample)
    (hmassDecomp :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) +
            massResidual sample)
    (htreatedResidualZero :
      sampleLaw[treatedResidual | covariateSigma] =ᵐ[sampleLaw] 0)
    (hcontrolResidualZero :
      sampleLaw[controlResidual | covariateSigma] =ᵐ[sampleLaw] 0)
    (hnumeratorResidualZero :
      sampleLaw[numeratorResidual | covariateSigma] =ᵐ[sampleLaw] 0)
    (hmassResidualZero :
      sampleLaw[massResidual | covariateSigma] =ᵐ[sampleLaw] 0) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  constructor
  · constructor
    · simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
        (condExp_scoreVersion_of_residual_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw) hcovSub
          treatedOutcome
          (fun sample =>
            treatedCellValueOnPATEDoubleScore treatedValue
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore sample))
          treatedResidual
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := covariateSigma)
            (sampleLaw := sampleLaw)
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            (treatedCellValueOnPATEDoubleScore treatedValue) hpateScore)
          (by
            simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
              htreatedVersionInt)
          htreatedResidualInt
          (by
            simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
              htreatedDecomp)
          htreatedResidualZero)
    · simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
        (condExp_scoreVersion_of_residual_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw) hcovSub
          controlOutcome
          (fun sample =>
            controlCellValueOnPATEDoubleScore controlValue
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore sample))
          controlResidual
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := covariateSigma)
            (sampleLaw := sampleLaw)
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            (controlCellValueOnPATEDoubleScore controlValue) hpateScore)
          (by
            simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
              hcontrolVersionInt)
          hcontrolResidualInt
          (by
            simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
              hcontrolDecomp)
          hcontrolResidualZero)
  · constructor
    · exact
        condExp_scoreVersion_of_residual_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw) hcovSub
          treatedEffectNumerator
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          numeratorResidual
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := covariateSigma)
            (sampleLaw := sampleLaw)
            (pattDoubleScore propensityScore pattPrognosticScore)
            scoreEffectCellValue hpattScore)
          hnumeratorVersionInt hnumeratorResidualInt hnumeratorDecomp
          hnumeratorResidualZero
    · exact
        condExp_scoreVersion_of_residual_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw) hcovSub treatedMass
          (fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          massResidual
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := covariateSigma)
            (sampleLaw := sampleLaw)
            (pattDoubleScore propensityScore pattPrognosticScore)
            scoreTreatedMassCellValue hpattScore)
          hmassVersionInt hmassResidualInt hmassDecomp hmassResidualZero

/--
Covariate-level PATE/PATT correct-score identities from residual mean-zero at
a richer primitive sigma-field.  This packages the tower transport from
treatment/covariate/selection information down to the covariate sigma-field
before applying the residual correct-score route.
-/
theorem covariate_condExp_doubleScoreVersions_of_primitiveResidual_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedResidual controlResidual numeratorResidual massResidual :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[covariateSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedResidualInt : Integrable treatedResidual sampleLaw)
    (hcontrolResidualInt : Integrable controlResidual sampleLaw)
    (hnumeratorResidualInt : Integrable numeratorResidual sampleLaw)
    (hmassResidualInt : Integrable massResidual sampleLaw)
    (htreatedDecomp :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          treatedValue (treatedPrognosticScore sample) +
            treatedResidual sample)
    (hcontrolDecomp :
      controlOutcome =ᵐ[sampleLaw]
        fun sample =>
          controlValue (controlPrognosticScore sample) +
            controlResidual sample)
    (hnumeratorDecomp :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) +
            numeratorResidual sample)
    (hmassDecomp :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) +
            massResidual sample)
    (htreatedPrimitiveZero :
      sampleLaw[treatedResidual | primitiveSigma] =ᵐ[sampleLaw] 0)
    (hcontrolPrimitiveZero :
      sampleLaw[controlResidual | primitiveSigma] =ᵐ[sampleLaw] 0)
    (hnumeratorPrimitiveZero :
      sampleLaw[numeratorResidual | primitiveSigma] =ᵐ[sampleLaw] 0)
    (hmassPrimitiveZero :
      sampleLaw[massResidual | primitiveSigma] =ᵐ[sampleLaw] 0) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  exact
    covariate_condExp_doubleScoreVersions_of_residual_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw)
      (hcovPrimitive.trans hprimitiveSub) propensityScore
      treatedPrognosticScore controlPrognosticScore pattPrognosticScore
      treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedResidual controlResidual numeratorResidual massResidual
      treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
      hpateScore hpattScore htreatedVersionInt hcontrolVersionInt
      hnumeratorVersionInt hmassVersionInt htreatedResidualInt
      hcontrolResidualInt hnumeratorResidualInt hmassResidualInt
      htreatedDecomp hcontrolDecomp hnumeratorDecomp hmassDecomp
      (condExp_zero_of_condExp_zero_of_le
        (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
        hprimitiveSub treatedResidual htreatedPrimitiveZero)
      (condExp_zero_of_condExp_zero_of_le
        (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
        hprimitiveSub controlResidual hcontrolPrimitiveZero)
      (condExp_zero_of_condExp_zero_of_le
        (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
        hprimitiveSub numeratorResidual hnumeratorPrimitiveZero)
      (condExp_zero_of_condExp_zero_of_le
        (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
        hprimitiveSub massResidual hmassPrimitiveZero)

/--
Covariate-level PATE/PATT correct-score identities from primitive zero
conditional means of subtraction residuals.  This removes the separate
residual variables and decomposition assumptions from the route: Lean defines
each residual as the raw target minus its score version, proves the algebraic
decomposition, and uses integrability of the raw target and score version.
-/
theorem covariate_condExp_doubleScoreVersions_of_primitiveSubResidual_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[covariateSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedPrimitiveZero :
      sampleLaw[(fun sample =>
        treatedOutcome sample - treatedValue (treatedPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0)
    (hcontrolPrimitiveZero :
      sampleLaw[(fun sample =>
        controlOutcome sample - controlValue (controlPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0)
    (hnumeratorPrimitiveZero :
      sampleLaw[(fun sample =>
        treatedEffectNumerator sample -
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0)
    (hmassPrimitiveZero :
      sampleLaw[(fun sample =>
        treatedMass sample -
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  exact
    covariate_condExp_doubleScoreVersions_of_primitiveResidual_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass
      (fun sample =>
        treatedOutcome sample - treatedValue (treatedPrognosticScore sample))
      (fun sample =>
        controlOutcome sample - controlValue (controlPrognosticScore sample))
      (fun sample =>
        treatedEffectNumerator sample -
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
      (fun sample =>
        treatedMass sample -
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
      treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
      hpateScore hpattScore htreatedVersionInt hcontrolVersionInt
      hnumeratorVersionInt hmassVersionInt
      (htreatedOutcomeInt.sub htreatedVersionInt)
      (hcontrolOutcomeInt.sub hcontrolVersionInt)
      (hnumeratorOutcomeInt.sub hnumeratorVersionInt)
      (hmassOutcomeInt.sub hmassVersionInt)
      (Filter.Eventually.of_forall fun sample => by ring)
      (Filter.Eventually.of_forall fun sample => by ring)
      (Filter.Eventually.of_forall fun sample => by ring)
      (Filter.Eventually.of_forall fun sample => by ring)
      htreatedPrimitiveZero hcontrolPrimitiveZero hnumeratorPrimitiveZero
      hmassPrimitiveZero

/--
Primitive correct-score conditional means imply the four zero conditional means
for the explicit subtraction residuals used by the WDSM double-score route.
This is the local bridge from a paper-style statement
`E[target | primitiveSigma] = score version` to the residual orthogonality
premises consumed by
`covariate_condExp_doubleScoreVersions_of_primitiveSubResidual_correctScoreRoute`.
-/
theorem primitiveSubResidualZeros_of_primitive_correctScoreRoute
    {PATTProgCell : Type*} {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[primitiveSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[primitiveSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    sampleLaw[(fun sample =>
        treatedOutcome sample - treatedValue (treatedPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        controlOutcome sample - controlValue (controlPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        treatedEffectNumerator sample -
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        treatedMass sample -
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 := by
  constructor
  · simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
      condExp_subResidual_zero_of_condExp_scoreVersion
        (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
        treatedOutcome
        (fun sample =>
          treatedCellValueOnPATEDoubleScore treatedValue
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore sample))
        (by
          simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
            htreatedPrimitiveCond)
        (scoreCellLoading_aestronglyMeasurable_of_discreteScore
          (mSample := mSample) (scoreSigma := primitiveSigma)
          (sampleLaw := sampleLaw)
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue) hpateScore)
        htreatedOutcomeInt
        (by
          simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
            htreatedVersionInt)
  · constructor
    · simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
        condExp_subResidual_zero_of_condExp_scoreVersion
          (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
          controlOutcome
          (fun sample =>
            controlCellValueOnPATEDoubleScore controlValue
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore sample))
          (by
            simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
              hcontrolPrimitiveCond)
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := primitiveSigma)
            (sampleLaw := sampleLaw)
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            (controlCellValueOnPATEDoubleScore controlValue) hpateScore)
          hcontrolOutcomeInt
          (by
            simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
              hcontrolVersionInt)
    · constructor
      · exact
          condExp_subResidual_zero_of_condExp_scoreVersion
            (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
            treatedEffectNumerator
            (fun sample =>
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample))
            hnumeratorPrimitiveCond
            (scoreCellLoading_aestronglyMeasurable_of_discreteScore
              (mSample := mSample) (scoreSigma := primitiveSigma)
              (sampleLaw := sampleLaw)
              (pattDoubleScore propensityScore pattPrognosticScore)
              scoreEffectCellValue hpattScore)
            hnumeratorOutcomeInt hnumeratorVersionInt
      · exact
          condExp_subResidual_zero_of_condExp_scoreVersion
            (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
            treatedMass
            (fun sample =>
              scoreTreatedMassCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample))
            hmassPrimitiveCond
            (scoreCellLoading_aestronglyMeasurable_of_discreteScore
              (mSample := mSample) (scoreSigma := primitiveSigma)
              (sampleLaw := sampleLaw)
              (pattDoubleScore propensityScore pattPrognosticScore)
              scoreTreatedMassCellValue hpattScore)
            hmassOutcomeInt hmassVersionInt

/--
Outcome-integrable variant of
`primitiveSubResidualZeros_of_primitive_correctScoreRoute`.  The four
score-version integrability hypotheses are derived from the four primitive
conditional-mean identities.
-/
theorem primitiveSubResidualZeros_of_primitive_correctScoreRoute_outcomeIntegrable
    {PATTProgCell : Type*} {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[primitiveSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[primitiveSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    sampleLaw[(fun sample =>
        treatedOutcome sample - treatedValue (treatedPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        controlOutcome sample - controlValue (controlPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        treatedEffectNumerator sample -
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        treatedMass sample -
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 := by
  exact
    primitiveSubResidualZeros_of_primitive_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hpateScore hpattScore
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt (integrable_condExp.congr htreatedPrimitiveCond)
      (integrable_condExp.congr hcontrolPrimitiveCond)
      (integrable_condExp.congr hnumeratorPrimitiveCond)
      (integrable_condExp.congr hmassPrimitiveCond) htreatedPrimitiveCond
      hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond

/--
Primitive subtraction-residual zeros from the target-transport correct-score
route.  The residuals are still the observed residuals
`observed target - score version`, but the probability inputs are a.e.
transport to latent/reference targets, target integrability, and primitive
conditional means for those transported targets.
-/
theorem primitiveSubResidualZeros_of_ae_targetTransport_correctScoreRoute
    {PATTProgCell : Type*} {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[primitiveSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[primitiveSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    sampleLaw[(fun sample =>
        treatedOutcome sample - treatedValue (treatedPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        controlOutcome sample - controlValue (controlPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        treatedEffectNumerator sample -
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        treatedMass sample -
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 := by
  constructor
  · simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
      condExp_subResidual_zero_of_ae_targetTransport_correctScoreRoute
        (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
        treatedOutcome treatedTarget
        (fun sample =>
          treatedCellValueOnPATEDoubleScore treatedValue
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore sample))
        htreatedTransport
        (by
          simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
            htreatedTargetCond)
        (scoreCellLoading_aestronglyMeasurable_of_discreteScore
          (mSample := mSample) (scoreSigma := primitiveSigma)
          (sampleLaw := sampleLaw)
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue) hpateScore)
        htreatedTargetInt
  · constructor
    · simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
        condExp_subResidual_zero_of_ae_targetTransport_correctScoreRoute
          (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
          controlOutcome controlTarget
          (fun sample =>
            controlCellValueOnPATEDoubleScore controlValue
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore sample))
          hcontrolTransport
          (by
            simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
              hcontrolTargetCond)
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := primitiveSigma)
            (sampleLaw := sampleLaw)
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            (controlCellValueOnPATEDoubleScore controlValue) hpateScore)
          hcontrolTargetInt
    · constructor
      · exact
          condExp_subResidual_zero_of_ae_targetTransport_correctScoreRoute
            (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
            treatedEffectNumerator effectTarget
            (fun sample =>
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample))
            hnumeratorTransport hnumeratorTargetCond
            (scoreCellLoading_aestronglyMeasurable_of_discreteScore
              (mSample := mSample) (scoreSigma := primitiveSigma)
              (sampleLaw := sampleLaw)
              (pattDoubleScore propensityScore pattPrognosticScore)
              scoreEffectCellValue hpattScore)
            heffectTargetInt
      · exact
          condExp_subResidual_zero_of_ae_targetTransport_correctScoreRoute
            (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
            treatedMass massTarget
            (fun sample =>
              scoreTreatedMassCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample))
            hmassTransport hmassTargetCond
            (scoreCellLoading_aestronglyMeasurable_of_discreteScore
              (mSample := mSample) (scoreSigma := primitiveSigma)
              (sampleLaw := sampleLaw)
              (pattDoubleScore propensityScore pattPrognosticScore)
              scoreTreatedMassCellValue hpattScore)
            hmassTargetInt

/--
Covariate-level PATE/PATT correct-score identities from primitive
correct-score conditional means.  This is the direct tower route for
paper-style Yang-Zhang/Antonelli assumptions stated as
`E[target | primitiveSigma] = score version`: the theorem first derives zero
conditional means of explicit subtraction residuals, then transports those
residual facts down to the covariate sigma-field.
-/
theorem covariate_condExp_doubleScoreVersions_of_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[covariateSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  rcases
    primitiveSubResidualZeros_of_primitive_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hprimitiveSub
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue
      (hpateScore.mono hcovPrimitive) (hpattScore.mono hcovPrimitive)
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedVersionInt hcontrolVersionInt
      hnumeratorVersionInt hmassVersionInt htreatedPrimitiveCond
      hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond with
    ⟨htreatedZero, hcontrolZero, hnumeratorZero, hmassZero⟩
  exact
    covariate_condExp_doubleScoreVersions_of_primitiveSubResidual_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue hpateScore
      hpattScore htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedVersionInt hcontrolVersionInt
      hnumeratorVersionInt hmassVersionInt htreatedZero hcontrolZero
      hnumeratorZero hmassZero

/--
Outcome-integrable variant of
`covariate_condExp_doubleScoreVersions_of_primitive_correctScoreRoute`.  The
four score-version integrability side conditions are recovered from the
primitive conditional-mean identities.
-/
theorem covariate_condExp_doubleScoreVersions_of_primitive_correctScoreRoute_outcomeIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[covariateSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  exact
    covariate_condExp_doubleScoreVersions_of_primitive_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue hpateScore
      hpattScore htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt (integrable_condExp.congr htreatedPrimitiveCond)
      (integrable_condExp.congr hcontrolPrimitiveCond)
      (integrable_condExp.congr hnumeratorPrimitiveCond)
      (integrable_condExp.congr hmassPrimitiveCond) htreatedPrimitiveCond
      hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond

/--
Covariate-level PATE/PATT correct-score identities after a paper route first
transports observed WDSM targets to latent/reference targets.  The probability
content remains explicit: four a.e. target-transport identities and four
primitive conditional means for the transported targets.  The proof only uses
conditional-expectation congruence and the tower route above.
-/
theorem covariate_condExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[covariateSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  rcases
    primitiveCondExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw)
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedTarget controlTarget
      effectTarget massTarget treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue htreatedTransport hcontrolTransport
      hnumeratorTransport hmassTransport htreatedTargetCond
      hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
    ⟨⟨htreatedPrimitiveCond, hcontrolPrimitiveCond⟩,
      hnumeratorPrimitiveCond, hmassPrimitiveCond⟩
  exact
    covariate_condExp_doubleScoreVersions_of_primitive_correctScoreRoute_outcomeIntegrable
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue hpateScore
      hpattScore htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedPrimitiveCond hcontrolPrimitiveCond
      hnumeratorPrimitiveCond hmassPrimitiveCond

/--
Target-integrable variant of
`covariate_condExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute`.
Observed-target integrability is derived from the latent/reference target
integrability and the four a.e. transport identities.
-/
theorem covariate_condExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[covariateSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  covariate_condExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute
    (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
    hprimitiveSub propensityScore treatedPrognosticScore
    controlPrognosticScore pattPrognosticScore treatedOutcome controlOutcome
    treatedEffectNumerator treatedMass treatedTarget controlTarget effectTarget
    massTarget treatedValue controlValue scoreEffectCellValue
    scoreTreatedMassCellValue hpateScore hpattScore
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := sampleLaw) treatedOutcome
      treatedTarget htreatedTransport htreatedTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := sampleLaw) controlOutcome
      controlTarget hcontrolTransport hcontrolTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := sampleLaw) treatedEffectNumerator
      effectTarget hnumeratorTransport heffectTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := sampleLaw) treatedMass massTarget
      hmassTransport hmassTargetInt)
    htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
    htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
    hmassTargetCond

/--
Component-score version of
`covariate_condExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute`.
Separate score measurability of the propensity and prognostic components
supplies the joint PATE/PATT double-score measurability needed by the
covariate tower route.
-/
theorem covariate_condExp_doubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[covariateSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[covariateSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[covariateSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[covariateSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  covariate_condExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute
    (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
    hprimitiveSub propensityScore treatedPrognosticScore
    controlPrognosticScore pattPrognosticScore treatedOutcome controlOutcome
    treatedEffectNumerator treatedMass treatedTarget controlTarget effectTarget
    massTarget treatedValue controlValue scoreEffectCellValue
    scoreTreatedMassCellValue
    (by
      simpa [pateDoubleScore] using
        ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore))
    (by
      simpa [pattDoubleScore] using
        hpropensityScore.prodMk hpattComponentScore)
    htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
    hmassOutcomeInt htreatedTransport hcontrolTransport hnumeratorTransport
    hmassTransport htreatedTargetCond hcontrolTargetCond
    hnumeratorTargetCond hmassTargetCond

/--
Component-score target-integrable version of
`covariate_condExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute`.
Separate component score measurability supplies the joint double-score
measurability, while observed-target integrability is recovered from the
latent/reference targets.
-/
theorem covariate_condExp_doubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[covariateSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[covariateSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[covariateSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[covariateSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  covariate_condExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute_targetIntegrable
    (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
    hprimitiveSub propensityScore treatedPrognosticScore
    controlPrognosticScore pattPrognosticScore treatedOutcome controlOutcome
    treatedEffectNumerator treatedMass treatedTarget controlTarget effectTarget
    massTarget treatedValue controlValue scoreEffectCellValue
    scoreTreatedMassCellValue
    (by
      simpa [pateDoubleScore] using
        ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore))
    (by
      simpa [pattDoubleScore] using
        hpropensityScore.prodMk hpattComponentScore)
    htreatedTargetInt hcontrolTargetInt heffectTargetInt hmassTargetInt
    htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
    htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
    hmassTargetCond

/--
PATT treated-mass score version is nonnegative whenever the raw treated-mass
variable is nonnegative and its covariate-level conditional mean is represented
by the PATT score loading.
-/
theorem pattScoreTreatedMass_nonneg_of_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedMass : Sample -> Real)
    (scoreTreatedMassCellValue : PropensityCell × PATTProgCell -> Real)
    (hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassNonneg : 0 ≤ᵐ[sampleLaw] treatedMass) :
    0 ≤ᵐ[sampleLaw]
      fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  scoreVersion_nonneg_of_condExp_scoreVersion_nonneg
    (mSample := mSample) (sampleLaw := sampleLaw) treatedMass
    (fun sample =>
      scoreTreatedMassCellValue
        (pattDoubleScore propensityScore pattPrognosticScore sample))
    hmassCov hmassNonneg

/--
PATT treated-mass score version is nonnegative from a primitive correct-score
conditional-mean identity.  The primitive identity is transported down to the
covariate sigma-field before applying the existing nonnegativity transfer.
-/
theorem pattScoreTreatedMass_nonneg_of_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedMass : Sample -> Real)
    (scoreTreatedMassCellValue : PropensityCell × PATTProgCell -> Real)
    (hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassNonneg : 0 ≤ᵐ[sampleLaw] treatedMass) :
    0 ≤ᵐ[sampleLaw]
      fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  have hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample) :=
    condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
      (mSample := mSample) (scoreSigma := covariateSigma)
      (sampleLaw := sampleLaw) hcovPrimitive hprimitiveSub treatedMass
      (fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample))
      hmassPrimitiveCond
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := covariateSigma)
        (sampleLaw := sampleLaw)
        (pattDoubleScore propensityScore pattPrognosticScore)
        scoreTreatedMassCellValue hpattScore)
  exact
    pattScoreTreatedMass_nonneg_of_covariate_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) propensityScore
      pattPrognosticScore treatedMass scoreTreatedMassCellValue hmassCov
      hmassNonneg

/--
Component-score version of
`pattScoreTreatedMass_nonneg_of_primitive_correctScoreRoute`.  Joint PATT
score measurability is derived from the propensity and PATT prognostic score
components.
-/
theorem pattScoreTreatedMass_nonneg_of_component_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology PATTProgCell]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedMass : Sample -> Real)
    (scoreTreatedMassCellValue : PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[covariateSigma] propensityScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[covariateSigma] pattPrognosticScore sampleLaw)
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassNonneg : 0 ≤ᵐ[sampleLaw] treatedMass) :
    0 ≤ᵐ[sampleLaw]
      fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  pattScoreTreatedMass_nonneg_of_primitive_correctScoreRoute
    (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
    hprimitiveSub propensityScore pattPrognosticScore treatedMass
    scoreTreatedMassCellValue
    (by
      simpa [pattDoubleScore] using
        hpropensityScore.prodMk hpattComponentScore)
    hmassPrimitiveCond hmassNonneg

/--
PATT score-mass nonnegativity directly from a nonnegative latent/reference
mass target and its primitive correct-score conditional mean.  This avoids any
observed treated-mass variable when only score-mass nonnegativity is needed.
-/
theorem pattScoreTreatedMass_nonneg_of_target_correctScoreRoute
    {PATTProgCell : Type*} {primitiveSigma : MeasurableSpace Sample}
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (massTarget : Sample -> Real)
    (scoreTreatedMassCellValue : PropensityCell × PATTProgCell -> Real)
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetNonneg : 0 ≤ᵐ[sampleLaw] massTarget) :
    0 ≤ᵐ[sampleLaw]
      fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  scoreVersion_nonneg_of_condExp_scoreVersion_nonneg
    (mSample := mSample) (sampleLaw := sampleLaw) massTarget
    (fun sample =>
      scoreTreatedMassCellValue
        (pattDoubleScore propensityScore pattPrognosticScore sample))
    hmassTargetCond hmassTargetNonneg

/--
PATT treated-mass score version is nonnegative from a target-transport
correct-score route.  Nonnegativity is stated for the latent/reference mass
target; the a.e. mass transport is retained as part of the route interface but
is not needed for the score-mass nonnegativity conclusion itself.
-/
theorem pattScoreTreatedMass_nonneg_of_ae_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedMass massTarget : Sample -> Real)
    (scoreTreatedMassCellValue : PropensityCell × PATTProgCell -> Real)
    (_hpattScore :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (_hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetNonneg : 0 ≤ᵐ[sampleLaw] massTarget) :
    0 ≤ᵐ[sampleLaw]
      fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  pattScoreTreatedMass_nonneg_of_target_correctScoreRoute
    (mSample := mSample) (sampleLaw := sampleLaw) propensityScore
    pattPrognosticScore massTarget scoreTreatedMassCellValue hmassTargetCond
    hmassTargetNonneg

/--
Component-score version of
`pattScoreTreatedMass_nonneg_of_ae_targetTransport_correctScoreRoute`.
Separate propensity and PATT prognostic score measurability supply the joint
PATT score measurability.
-/
theorem pattScoreTreatedMass_nonneg_of_component_ae_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology PATTProgCell]
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedMass massTarget : Sample -> Real)
    (scoreTreatedMassCellValue : PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[covariateSigma] propensityScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[covariateSigma] pattPrognosticScore sampleLaw)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetNonneg : 0 ≤ᵐ[sampleLaw] massTarget) :
    0 ≤ᵐ[sampleLaw]
      fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  pattScoreTreatedMass_nonneg_of_ae_targetTransport_correctScoreRoute
    (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
    hprimitiveSub propensityScore pattPrognosticScore treatedMass massTarget
    scoreTreatedMassCellValue
    (by
      simpa [pattDoubleScore] using
        hpropensityScore.prodMk hpattComponentScore)
    hmassTransport hmassTargetCond hmassTargetNonneg

/--
Bounded score-measurable weights preserve raw-target integrability.  This is
the local survey-weight side-condition reducer used by the weighted primitive
correct-score route.
-/
theorem integrable_weight_mul_of_bounded_scoreMeasurableWeight
    (hscoreSub : scoreSigma ≤ mSample)
    (weight outcome : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    {weightBound : Real}
    (hweightBound : ∀ᵐ sample ∂sampleLaw, ‖weight sample‖ ≤ weightBound)
    (houtcomeInt : Integrable outcome sampleLaw) :
    Integrable (fun sample => weight sample * outcome sample) sampleLaw :=
  houtcomeInt.bdd_mul (hweightMeas.mono hscoreSub) hweightBound

/--
Weighted PATT treated-effect numerator conditional-mean identity from the
covariate correct-score route.  This is the survey-weighted numerator version
of the pull-out/tower argument.
-/
theorem condExp_weightedPATTScoreEffectNumerator_of_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator : Sample -> Real)
    (scoreEffectCellValue : PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hweightedInt :
      Integrable
        (fun sample => weight sample * treatedEffectNumerator sample)
        sampleLaw)
    (hnumeratorInt : Integrable treatedEffectNumerator sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (hnumeratorCov :
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    sampleLaw[(fun sample =>
        weight sample * treatedEffectNumerator sample) | scoreSigma]
        =ᵐ[sampleLaw]
      fun sample =>
        weight sample *
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  condExp_weightedScoreVersion_of_covariate_correctScoreRoute
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hscoreCov hcovSub weight treatedEffectNumerator
    (fun sample =>
      scoreEffectCellValue
        (pattDoubleScore propensityScore pattPrognosticScore sample))
    hweightMeas hweightedInt hnumeratorInt hnumeratorCov
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw)
      (pattDoubleScore propensityScore pattPrognosticScore)
      scoreEffectCellValue hpattScore)

/--
Weighted PATT treated-mass conditional-mean identity from the covariate
correct-score route.  This is the survey-weighted denominator version of the
pull-out/tower argument.
-/
theorem condExp_weightedPATTScoreTreatedMass_of_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedMass : Sample -> Real)
    (scoreTreatedMassCellValue : PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hweightedInt :
      Integrable (fun sample => weight sample * treatedMass sample)
        sampleLaw)
    (hmassInt : Integrable treatedMass sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    sampleLaw[(fun sample => weight sample * treatedMass sample) |
        scoreSigma] =ᵐ[sampleLaw]
      fun sample =>
        weight sample *
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  condExp_weightedScoreVersion_of_covariate_correctScoreRoute
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hscoreCov hcovSub weight treatedMass
    (fun sample =>
      scoreTreatedMassCellValue
        (pattDoubleScore propensityScore pattPrognosticScore sample))
    hweightMeas hweightedInt hmassInt hmassCov
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw)
      (pattDoubleScore propensityScore pattPrognosticScore)
      scoreTreatedMassCellValue hpattScore)

/--
Paired weighted PATE/PATT conditional-mean route from covariate-level
correct-score identities.  This packages the survey-weighted treated/control
PATE arms and the weighted PATT numerator/mass identities under one route.
-/
theorem condExp_weightedDoubleScoreVersions_of_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (htreatedWeightedInt :
      Integrable (fun sample => weight sample * treatedOutcome sample)
        sampleLaw)
    (hcontrolWeightedInt :
      Integrable (fun sample => weight sample * controlOutcome sample)
        sampleLaw)
    (hnumeratorWeightedInt :
      Integrable
        (fun sample => weight sample * treatedEffectNumerator sample)
        sampleLaw)
    (hmassWeightedInt :
      Integrable (fun sample => weight sample * treatedMass sample)
        sampleLaw)
    (htreatedInt : Integrable treatedOutcome sampleLaw)
    (hcontrolInt : Integrable controlOutcome sampleLaw)
    (hnumeratorInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassInt : Integrable treatedMass sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedCov :
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolCov :
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorCov :
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[(fun sample => weight sample * treatedOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          weight sample * treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * controlOutcome sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample * controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[(fun sample =>
          weight sample * treatedEffectNumerator sample) | scoreSigma]
          =ᵐ[sampleLaw]
        (fun sample =>
          weight sample *
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * treatedMass sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample *
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  constructor
  · constructor
    · exact
        condExp_weightedPATEScoreTreatedOutcome_of_covariate_correctPrognosticRoute
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscoreCov hcovSub weight
          propensityScore treatedPrognosticScore controlPrognosticScore
          treatedOutcome treatedValue hweightMeas htreatedWeightedInt
          htreatedInt hpateScore htreatedCov
    · exact
        condExp_weightedPATEScoreControlOutcome_of_covariate_correctPrognosticRoute
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscoreCov hcovSub weight
          propensityScore treatedPrognosticScore controlPrognosticScore
          controlOutcome controlValue hweightMeas hcontrolWeightedInt
          hcontrolInt hpateScore hcontrolCov
  · constructor
    · exact
        condExp_weightedPATTScoreEffectNumerator_of_covariate_correctScoreRoute
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscoreCov hcovSub weight
          propensityScore pattPrognosticScore treatedEffectNumerator
          scoreEffectCellValue hweightMeas hnumeratorWeightedInt
          hnumeratorInt hpattScore hnumeratorCov
    · exact
        condExp_weightedPATTScoreTreatedMass_of_covariate_correctScoreRoute
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscoreCov hcovSub weight
          propensityScore pattPrognosticScore treatedMass
          scoreTreatedMassCellValue hweightMeas hmassWeightedInt hmassInt
          hpattScore hmassCov

/--
Paired weighted PATE/PATT conditional-mean route from primitive correct-score
identities.  It first derives the covariate-level correct-score identities
from primitive conditional means, then applies the score-measurable weight
pull-out route.
-/
theorem condExp_weightedDoubleScoreVersions_of_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (htreatedWeightedInt :
      Integrable (fun sample => weight sample * treatedOutcome sample)
        sampleLaw)
    (hcontrolWeightedInt :
      Integrable (fun sample => weight sample * controlOutcome sample)
        sampleLaw)
    (hnumeratorWeightedInt :
      Integrable
        (fun sample => weight sample * treatedEffectNumerator sample)
        sampleLaw)
    (hmassWeightedInt :
      Integrable (fun sample => weight sample * treatedMass sample)
        sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[(fun sample => weight sample * treatedOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          weight sample * treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * controlOutcome sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample * controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[(fun sample =>
          weight sample * treatedEffectNumerator sample) | scoreSigma]
          =ᵐ[sampleLaw]
        (fun sample =>
          weight sample *
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * treatedMass sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample *
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  rcases
    covariate_condExp_doubleScoreVersions_of_primitive_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue
      (hpateScore.mono hscoreCov) (hpattScore.mono hscoreCov)
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedVersionInt hcontrolVersionInt
      hnumeratorVersionInt hmassVersionInt htreatedPrimitiveCond
      hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond with
    ⟨hpateCov, hpattCov⟩
  rcases hpateCov with ⟨htreatedCov, hcontrolCov⟩
  rcases hpattCov with ⟨hnumeratorCov, hmassCov⟩
  exact
    condExp_weightedDoubleScoreVersions_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov (hcovPrimitive.trans hprimitiveSub)
      weight propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hweightMeas
      htreatedWeightedInt hcontrolWeightedInt hnumeratorWeightedInt
      hmassWeightedInt htreatedOutcomeInt hcontrolOutcomeInt
      hnumeratorOutcomeInt hmassOutcomeInt hpateScore hpattScore htreatedCov
      hcontrolCov hnumeratorCov hmassCov

/--
Outcome-integrable variant of
`condExp_weightedDoubleScoreVersions_of_primitive_correctScoreRoute`.
Score-version integrability is derived from the primitive conditional-mean
identities, while weighted integrability remains an explicit survey/design
side condition.
-/
theorem condExp_weightedDoubleScoreVersions_of_primitive_correctScoreRoute_outcomeIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (htreatedWeightedInt :
      Integrable (fun sample => weight sample * treatedOutcome sample)
        sampleLaw)
    (hcontrolWeightedInt :
      Integrable (fun sample => weight sample * controlOutcome sample)
        sampleLaw)
    (hnumeratorWeightedInt :
      Integrable
        (fun sample => weight sample * treatedEffectNumerator sample)
        sampleLaw)
    (hmassWeightedInt :
      Integrable (fun sample => weight sample * treatedMass sample)
        sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[(fun sample => weight sample * treatedOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          weight sample * treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * controlOutcome sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample * controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[(fun sample =>
          weight sample * treatedEffectNumerator sample) | scoreSigma]
          =ᵐ[sampleLaw]
        (fun sample =>
          weight sample *
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * treatedMass sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample *
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  condExp_weightedDoubleScoreVersions_of_primitive_correctScoreRoute
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hscoreCov hcovPrimitive hprimitiveSub weight propensityScore
    treatedPrognosticScore controlPrognosticScore pattPrognosticScore
    treatedOutcome controlOutcome treatedEffectNumerator treatedMass
    treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
    hweightMeas htreatedWeightedInt hcontrolWeightedInt
    hnumeratorWeightedInt hmassWeightedInt htreatedOutcomeInt
    hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
    (integrable_condExp.congr htreatedPrimitiveCond)
    (integrable_condExp.congr hcontrolPrimitiveCond)
    (integrable_condExp.congr hnumeratorPrimitiveCond)
    (integrable_condExp.congr hmassPrimitiveCond) hpateScore hpattScore
    htreatedPrimitiveCond hcontrolPrimitiveCond hnumeratorPrimitiveCond
    hmassPrimitiveCond

/--
Component-score version of the paired weighted primitive correct-score route.
The joint PATE/PATT score measurability used by the weight pull-out theorem is
derived from separate propensity and prognostic score measurability.
-/
theorem condExp_weightedDoubleScoreVersions_of_component_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedWeightedInt :
      Integrable (fun sample => weight sample * treatedOutcome sample)
        sampleLaw)
    (hcontrolWeightedInt :
      Integrable (fun sample => weight sample * controlOutcome sample)
        sampleLaw)
    (hnumeratorWeightedInt :
      Integrable
        (fun sample => weight sample * treatedEffectNumerator sample)
        sampleLaw)
    (hmassWeightedInt :
      Integrable (fun sample => weight sample * treatedMass sample)
        sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[(fun sample => weight sample * treatedOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          weight sample * treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * controlOutcome sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample * controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[(fun sample =>
          weight sample * treatedEffectNumerator sample) | scoreSigma]
          =ᵐ[sampleLaw]
        (fun sample =>
          weight sample *
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * treatedMass sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample *
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  exact
    condExp_weightedDoubleScoreVersions_of_primitive_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub weight
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hweightMeas
      htreatedWeightedInt hcontrolWeightedInt hnumeratorWeightedInt
      hmassWeightedInt htreatedOutcomeInt hcontrolOutcomeInt
      hnumeratorOutcomeInt hmassOutcomeInt htreatedVersionInt
      hcontrolVersionInt hnumeratorVersionInt hmassVersionInt
      (by
        simpa [pateDoubleScore] using
          ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore))
      (by
        simpa [pattDoubleScore] using
          hpropensityScore.prodMk hpattComponentScore)
      htreatedPrimitiveCond hcontrolPrimitiveCond hnumeratorPrimitiveCond
      hmassPrimitiveCond

/--
Outcome-integrable component-score version of the paired weighted primitive
correct-score route.  This removes separate score-version integrability from
the weighted route while preserving explicit weighted-integrability and
score-measurable weight side conditions.
-/
theorem condExp_weightedDoubleScoreVersions_of_component_primitive_correctScoreRoute_outcomeIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (weight : Sample -> Real)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedWeightedInt :
      Integrable (fun sample => weight sample * treatedOutcome sample)
        sampleLaw)
    (hcontrolWeightedInt :
      Integrable (fun sample => weight sample * controlOutcome sample)
        sampleLaw)
    (hnumeratorWeightedInt :
      Integrable
        (fun sample => weight sample * treatedEffectNumerator sample)
        sampleLaw)
    (hmassWeightedInt :
      Integrable (fun sample => weight sample * treatedMass sample)
        sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[(fun sample => weight sample * treatedOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          weight sample * treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * controlOutcome sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample * controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[(fun sample =>
          weight sample * treatedEffectNumerator sample) | scoreSigma]
          =ᵐ[sampleLaw]
        (fun sample =>
          weight sample *
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * treatedMass sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample *
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) :=
  condExp_weightedDoubleScoreVersions_of_component_primitive_correctScoreRoute
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hscoreCov hcovPrimitive hprimitiveSub weight propensityScore
    treatedPrognosticScore controlPrognosticScore pattPrognosticScore
    treatedOutcome controlOutcome treatedEffectNumerator treatedMass
    treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
    hweightMeas hpropensityScore htreatedScore hcontrolScore
    hpattComponentScore htreatedWeightedInt hcontrolWeightedInt
    hnumeratorWeightedInt hmassWeightedInt htreatedOutcomeInt
    hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
    (integrable_condExp.congr htreatedPrimitiveCond)
    (integrable_condExp.congr hcontrolPrimitiveCond)
    (integrable_condExp.congr hnumeratorPrimitiveCond)
    (integrable_condExp.congr hmassPrimitiveCond) htreatedPrimitiveCond
    hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond

/--
Bounded-weight variant of
`condExp_weightedDoubleScoreVersions_of_component_primitive_correctScoreRoute_outcomeIntegrable`.
It replaces the four weighted-integrability assumptions by one a.e. bound on
the score-measurable survey/design weight.
-/
theorem condExp_weightedDoubleScoreVersions_of_component_primitive_correctScoreRoute_boundedWeight
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (weight : Sample -> Real)
    {weightBound : Real}
    (hweightBound : ∀ᵐ sample ∂sampleLaw, ‖weight sample‖ ≤ weightBound)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[(fun sample => weight sample * treatedOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          weight sample * treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * controlOutcome sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample * controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[(fun sample =>
          weight sample * treatedEffectNumerator sample) | scoreSigma]
          =ᵐ[sampleLaw]
        (fun sample =>
          weight sample *
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * treatedMass sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample *
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  let hscoreSub := hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)
  exact
    condExp_weightedDoubleScoreVersions_of_component_primitive_correctScoreRoute_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub weight
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hweightMeas
      hpropensityScore htreatedScore hcontrolScore hpattComponentScore
      (integrable_weight_mul_of_bounded_scoreMeasurableWeight
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreSub weight treatedOutcome
        hweightMeas hweightBound htreatedOutcomeInt)
      (integrable_weight_mul_of_bounded_scoreMeasurableWeight
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreSub weight controlOutcome
        hweightMeas hweightBound hcontrolOutcomeInt)
      (integrable_weight_mul_of_bounded_scoreMeasurableWeight
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreSub weight treatedEffectNumerator
        hweightMeas hweightBound hnumeratorOutcomeInt)
      (integrable_weight_mul_of_bounded_scoreMeasurableWeight
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreSub weight treatedMass
        hweightMeas hweightBound hmassOutcomeInt)
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedPrimitiveCond hcontrolPrimitiveCond
      hnumeratorPrimitiveCond hmassPrimitiveCond

/--
Bounded-weight component-score route after a paper proof transports observed
targets to latent/reference targets.  The weighted-integrability and
observed-target integrability side conditions are recovered from bounded
score-measurable weights, target integrability, and a.e. target transport;
the probability content remains the four target-transport identities and the
four latent/reference primitive correct-score conditional means.
-/
theorem condExp_weightedDoubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute_boundedWeight
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (weight : Sample -> Real)
    {weightBound : Real}
    (hweightBound : ∀ᵐ sample ∂sampleLaw, ‖weight sample‖ ≤ weightBound)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma] weight sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[(fun sample => weight sample * treatedOutcome sample) |
        scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          weight sample * treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * controlOutcome sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample * controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[(fun sample =>
          weight sample * treatedEffectNumerator sample) | scoreSigma]
          =ᵐ[sampleLaw]
        (fun sample =>
          weight sample *
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[(fun sample => weight sample * treatedMass sample) |
          scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          weight sample *
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  rcases
    primitiveCondExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw)
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedTarget controlTarget
      effectTarget massTarget treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue htreatedTransport hcontrolTransport
      hnumeratorTransport hmassTransport htreatedTargetCond
      hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
    ⟨⟨htreatedPrimitiveCond, hcontrolPrimitiveCond⟩,
      hnumeratorPrimitiveCond, hmassPrimitiveCond⟩
  exact
    condExp_weightedDoubleScoreVersions_of_component_primitive_correctScoreRoute_boundedWeight
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub weight
      hweightBound propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue
      hweightMeas hpropensityScore htreatedScore hcontrolScore
      hpattComponentScore
      (integrable_of_ae_targetTransport
        (mSample := mSample) (sampleLaw := sampleLaw) treatedOutcome
        treatedTarget htreatedTransport htreatedTargetInt)
      (integrable_of_ae_targetTransport
        (mSample := mSample) (sampleLaw := sampleLaw) controlOutcome
        controlTarget hcontrolTransport hcontrolTargetInt)
      (integrable_of_ae_targetTransport
        (mSample := mSample) (sampleLaw := sampleLaw)
        treatedEffectNumerator effectTarget hnumeratorTransport
        heffectTargetInt)
      (integrable_of_ae_targetTransport
        (mSample := mSample) (sampleLaw := sampleLaw) treatedMass massTarget
        hmassTransport hmassTargetInt)
      htreatedPrimitiveCond hcontrolPrimitiveCond hnumeratorPrimitiveCond
      hmassPrimitiveCond

/--
Paired PATE/PATT double-score conditional-mean route from covariate-level
correct-score identities.
-/
theorem condExp_doubleScoreVersions_of_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedCov :
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolCov :
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorCov :
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  constructor
  · exact
      condExp_pateDoubleScoreVersions_of_covariate_correctPrognosticRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub propensityScore
        treatedPrognosticScore controlPrognosticScore treatedOutcome
        controlOutcome treatedValue controlValue hpateScore htreatedCov
        hcontrolCov
  · exact
      condExp_pattDoubleScoreVersions_of_covariate_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub propensityScore
        pattPrognosticScore treatedEffectNumerator treatedMass
        scoreEffectCellValue scoreTreatedMassCellValue hpattScore
        hnumeratorCov hmassCov

/--
Score-sigma PATE/PATT conditional-mean route from component score
measurability and a target-transport correct-score interface with observed
WDSM target integrability.  This composes the covariate-level observed
integrability target-transport theorem with the tower step to double scores.
-/
theorem condExp_doubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  rcases
    covariate_condExp_doubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedTarget
      controlTarget effectTarget massTarget treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue
      (hpropensityScore.mono hscoreCov) (htreatedScore.mono hscoreCov)
      (hcontrolScore.mono hscoreCov) (hpattComponentScore.mono hscoreCov)
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedTransport hcontrolTransport
      hnumeratorTransport hmassTransport htreatedTargetCond
      hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
    ⟨hpateCov, hpattCov⟩
  rcases hpateCov with ⟨htreatedCov, hcontrolCov⟩
  rcases hpattCov with ⟨hnumeratorCov, hmassCov⟩
  exact
    condExp_doubleScoreVersions_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov
      (hcovPrimitive.trans hprimitiveSub) propensityScore
      treatedPrognosticScore controlPrognosticScore pattPrognosticScore
      treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue
      (by
        simpa [pateDoubleScore] using
          ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore))
      (by
        simpa [pattDoubleScore] using
          hpropensityScore.prodMk hpattComponentScore)
      htreatedCov hcontrolCov hnumeratorCov hmassCov

/--
Score-sigma PATE/PATT conditional-mean route from component score
measurability and a target-transport correct-score interface.  This composes
the covariate-level target-transport theorem with the tower step from
covariates to double scores, so downstream balancing consumers can take
latent/reference target integrability and primitive correct-score identities
directly.
-/
theorem condExp_doubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  rcases
    covariate_condExp_doubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute_targetIntegrable
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedTarget
      controlTarget effectTarget massTarget treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue
      (hpropensityScore.mono hscoreCov) (htreatedScore.mono hscoreCov)
      (hcontrolScore.mono hscoreCov) (hpattComponentScore.mono hscoreCov)
      htreatedTargetInt hcontrolTargetInt heffectTargetInt hmassTargetInt
      htreatedTransport hcontrolTransport hnumeratorTransport
      hmassTransport htreatedTargetCond hcontrolTargetCond
      hnumeratorTargetCond hmassTargetCond with
    ⟨hpateCov, hpattCov⟩
  rcases hpateCov with ⟨htreatedCov, hcontrolCov⟩
  rcases hpattCov with ⟨hnumeratorCov, hmassCov⟩
  exact
    condExp_doubleScoreVersions_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov
      (hcovPrimitive.trans hprimitiveSub) propensityScore
      treatedPrognosticScore controlPrognosticScore pattPrognosticScore
      treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue
      (by
        simpa [pateDoubleScore] using
          ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore))
      (by
        simpa [pattDoubleScore] using
          hpropensityScore.prodMk hpattComponentScore)
      htreatedCov hcontrolCov hnumeratorCov hmassCov

/--
Score-sigma conditional means for latent/reference targets from primitive
target correct-score identities.  This is the target-only upstream adapter for
the target-transport bridge below: no observed-outcome conditional-mean premise
is assumed, and the observed-to-target transports are not needed for this
conditional-mean step.
-/
theorem condExp_targetDoubleScoreVersions_of_component_primitive_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedTarget | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | scoreSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[massTarget | scoreSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  simpa using
    condExp_doubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute_targetIntegrable
      (mSample := mSample) (sampleLaw := sampleLaw) hscoreCov
      hcovPrimitive hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedTarget controlTarget
      effectTarget massTarget treatedTarget controlTarget effectTarget
      massTarget treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue hpropensityScore htreatedScore hcontrolScore
      hpattComponentScore htreatedTargetInt hcontrolTargetInt
      heffectTargetInt hmassTargetInt
      (Filter.EventuallyEq.refl (ae sampleLaw) treatedTarget)
      (Filter.EventuallyEq.refl (ae sampleLaw) controlTarget)
      (Filter.EventuallyEq.refl (ae sampleLaw) effectTarget)
      (Filter.EventuallyEq.refl (ae sampleLaw) massTarget)
      htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
      hmassTargetCond

/--
Direct primitive-to-score target conditional means.  This variant removes the
intermediate covariate sigma-field and target-integrability side conditions:
if the score sigma-field is below the primitive sigma-field, primitive
latent/reference correct-score identities tower directly down to the
score-sigma target identities consumed by the lower target-transport bridge.
-/
theorem condExp_targetDoubleScoreVersions_of_component_primitive_correctScoreRoute_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (sampleLaw[treatedTarget | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | scoreSigma] =ᵐ[sampleLaw]
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
        sampleLaw[massTarget | scoreSigma] =ᵐ[sampleLaw]
          fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) := by
  have hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw := by
    simpa [pattDoubleScore] using
      hpropensityScore.prodMk hpattComponentScore
  constructor
  · constructor
    · exact
        condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
          treatedTarget
          (fun sample => treatedValue (treatedPrognosticScore sample))
          htreatedTargetCond
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := scoreSigma)
            (sampleLaw := sampleLaw) treatedPrognosticScore treatedValue
            htreatedScore)
    · exact
        condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
          controlTarget
          (fun sample => controlValue (controlPrognosticScore sample))
          hcontrolTargetCond
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := scoreSigma)
            (sampleLaw := sampleLaw) controlPrognosticScore controlValue
            hcontrolScore)
  · constructor
    · exact
        condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
          effectTarget
          (fun sample =>
            scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          hnumeratorTargetCond
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := scoreSigma)
            (sampleLaw := sampleLaw)
            (pattDoubleScore propensityScore pattPrognosticScore)
            scoreEffectCellValue hpattScore)
    · exact
        condExp_scoreVersion_of_covariate_condExp_scoreVersion_of_le
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
          massTarget
          (fun sample =>
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample))
          hmassTargetCond
          (scoreCellLoading_aestronglyMeasurable_of_discreteScore
            (mSample := mSample) (scoreSigma := scoreSigma)
            (sampleLaw := sampleLaw)
            (pattDoubleScore propensityScore pattPrognosticScore)
            scoreTreatedMassCellValue hpattScore)

/--
Selected-Hájek PATE/PATT double-score endpoint from transported
latent/reference targets and score-sigma target conditional means.  This is the
direct WDSM consumer of the generic target-transport representation adapter:
observed representation and observed conditional-mean premises are recovered
inside Lean from a.e. target transport.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions_targetTransport_targetRepresentation
    {PATTProgCell : Type*}
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) :=
  selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_scoreVersions_targetTransport_targetRepresentation
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
    treatedOutcome controlOutcome treatedEffectNumerator treatedMass
    treatedTarget controlTarget effectTarget massTarget
    (fun sample => treatedValue (treatedPrognosticScore sample))
    (fun sample => controlValue (controlPrognosticScore sample))
    (fun sample =>
      scoreEffectCellValue
        (pattDoubleScore propensityScore pattPrognosticScore sample))
    (fun sample =>
      scoreTreatedMassCellValue
        (pattDoubleScore propensityScore pattPrognosticScore sample))
    hreprT hreprC hreprNumerator hreprMass hmassTargetNonzero
    htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
    htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
    hmassTargetCond

/--
Selected-Hájek PATE/PATT double-score endpoint from direct a.e.
latent/reference target score versions.  This specializes the generic
survey-layer target-transport theorem to the WDSM component score maps, so the
representation transport and target-integrability bookkeeping are proved once
below the double-score layer.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetScoreVersions_targetTransport_targetRepresentation
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  have hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw := by
    simpa [pattDoubleScore] using
      hpropensityScore.prodMk hpattComponentScore
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_targetTransport_targetRepresentation_targetIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
      hcontrolSampling hpattSampling treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedTarget controlTarget
      effectTarget massTarget
      (fun sample => treatedValue (treatedPrognosticScore sample))
      (fun sample => controlValue (controlPrognosticScore sample))
      (fun sample =>
        scoreEffectCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample))
      (fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample))
      hreprT hreprC hreprNumerator hreprMass hmassTargetNonzero
      htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
      htreatedTargetVersion hcontrolTargetVersion hnumeratorTargetVersion
      hmassTargetVersion
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) treatedPrognosticScore treatedValue
        htreatedScore)
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) controlPrognosticScore controlValue
        hcontrolScore)
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw)
        (pattDoubleScore propensityScore pattPrognosticScore)
        scoreEffectCellValue hpattScore)
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw)
        (pattDoubleScore propensityScore pattPrognosticScore)
        scoreTreatedMassCellValue hpattScore)
      htreatedTargetInt hcontrolTargetInt heffectTargetInt hmassTargetInt

/--
Selected-Hájek PATE/PATT double-score endpoint from direct a.e.
latent/reference target score versions with observed-target integrability.
This variant transfers integrability from the observed WDSM targets to the
transported targets through the same a.e. target-transport identities.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  have hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw := by
    simpa [pattDoubleScore] using
      hpropensityScore.prodMk hpattComponentScore
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
      hcontrolSampling hpattSampling treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedTarget controlTarget
      effectTarget massTarget
      (fun sample => treatedValue (treatedPrognosticScore sample))
      (fun sample => controlValue (controlPrognosticScore sample))
      (fun sample =>
        scoreEffectCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample))
      (fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample))
      hreprT hreprC hreprNumerator hreprMass hmassTargetNonzero
      htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
      htreatedTargetVersion hcontrolTargetVersion hnumeratorTargetVersion
      hmassTargetVersion
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) treatedPrognosticScore treatedValue
        htreatedScore)
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) controlPrognosticScore controlValue
        hcontrolScore)
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw)
        (pattDoubleScore propensityScore pattPrognosticScore)
        scoreEffectCellValue hpattScore)
      (scoreCellLoading_aestronglyMeasurable_of_discreteScore
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw)
        (pattDoubleScore propensityScore pattPrognosticScore)
        scoreTreatedMassCellValue hpattScore)
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt

/--
`SurveyWeightedScoreMeanBridge` packaged from transported latent/reference
targets and score-sigma target conditional means.  This lower bridge removes
observed representation equalities, observed PATT mass nonzero, and observed
conditional-mean premises from the endpoint interface; they are all recovered
from target representation and a.e. target transport in the bridge proof.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_condExp_doubleScoreVersions_targetTransport_targetRepresentation
    {PATTProgCell : Type*}
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | scoreSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | scoreSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨htreatedTransport, hcontrolTransport, hnumeratorTransport,
        hmassTransport, htreatedTargetCond, hcontrolTargetCond,
        hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions_targetTransport_targetRepresentation
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedTarget controlTarget effectTarget massTarget treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hmassTargetNonzero
        htreatedTransport hcontrolTransport hnumeratorTransport
        hmassTransport htreatedTargetCond hcontrolTargetCond
        hnumeratorTargetCond hmassTargetCond
  }

/--
Lower selected-Hájek target-transport bridge from direct score-sigma a.e.
target score-version equalities.  This is the shortest stronger-a.e. route to
the target-transport bridge: no primitive sigma-field or primitive
conditional-mean premises are exposed.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetScoreVersions_targetTransport_targetRepresentation
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlTarget =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      effectTarget =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedTargetInt, hcontrolTargetInt, heffectTargetInt,
        hmassTargetInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetVersion,
        hcontrolTargetVersion, hnumeratorTargetVersion,
        hmassTargetVersion⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetScoreVersions_targetTransport_targetRepresentation
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedTarget controlTarget effectTarget massTarget treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hmassTargetNonzero
        hpropensityScore htreatedScore hcontrolScore hpattComponentScore
        htreatedTargetInt hcontrolTargetInt heffectTargetInt hmassTargetInt
        htreatedTransport hcontrolTransport hnumeratorTransport
        hmassTransport htreatedTargetVersion hcontrolTargetVersion
        hnumeratorTargetVersion hmassTargetVersion
  }

/--
Observed-target-integrability version of
`surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetScoreVersions_targetTransport_targetRepresentation`.
Its balancing field asks for integrability of the observed WDSM targets and
uses a.e. target transport to recover the latent/reference target
integrability needed by the representation-layer route.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
    {PATTProgCell : Type*}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlTarget =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      effectTarget =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedOutcomeInt, hcontrolOutcomeInt, hnumeratorOutcomeInt,
        hmassOutcomeInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetVersion,
        hcontrolTargetVersion, hnumeratorTargetVersion,
        hmassTargetVersion⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedTarget controlTarget effectTarget massTarget treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hmassTargetNonzero
        hpropensityScore htreatedScore hcontrolScore hpattComponentScore
        htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
        hmassOutcomeInt htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetVersion
        hcontrolTargetVersion hnumeratorTargetVersion hmassTargetVersion
  }

/--
Component-law Yang-Zhang/Antonelli finite-cover endpoint from direct
score-sigma target score-version identities.  This is the stronger-a.e. route
without a primitive sigma-field: component `HasLaw` support gives finite
double-score coverage, and target score versions give the score-sigma
conditional means consumed by the target-transport endpoint.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_targetScoreVersions_targetTransport_targetRepresentation
    {PATTProgCell : Type*}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        pateRepr.selectedHajekPATE =
            (∫ sample,
              treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂sampleLaw) ∧
          pattRepr.selectedHajekPATT =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂sampleLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂sampleLaw) := by
  constructor
  · exact
      ae_pateDoubleScoreCover_of_component_hasLaw
        (mSample := mSample) (sampleLaw := sampleLaw)
        propensityCells treatedProgCells controlProgCells propensityScore
        treatedPrognosticScore controlPrognosticScore hpropensityLaw
        htreatedLaw hcontrolLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpropensityCoverLaw htreatedCoverLaw
        hcontrolCoverLaw
  · constructor
    · exact
        ae_pattDoubleScoreCover_of_component_hasLaw
          (mSample := mSample) (sampleLaw := sampleLaw)
          propensityCells pattProgCells propensityScore pattPrognosticScore
          hpropensityLaw hpattLaw hpropensityCellsMeas hpattCellsMeas
          hpropensityCoverLaw hpattCoverLaw
    · exact
        selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetScoreVersions_targetTransport_targetRepresentation
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
          hcontrolSampling hpattSampling propensityScore
          treatedPrognosticScore controlPrognosticScore pattPrognosticScore
          treatedOutcome controlOutcome treatedEffectNumerator treatedMass
          treatedTarget controlTarget effectTarget massTarget treatedValue
          controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
          hreprC hreprNumerator hreprMass hmassTargetNonzero
          hpropensityScore htreatedScore hcontrolScore hpattComponentScore
          htreatedTargetInt hcontrolTargetInt heffectTargetInt
          hmassTargetInt
          htreatedTransport hcontrolTransport hnumeratorTransport
          hmassTransport htreatedTargetVersion hcontrolTargetVersion
          hnumeratorTargetVersion hmassTargetVersion

/--
Component-law Yang-Zhang/Antonelli finite-cover endpoint from direct
score-sigma target score-version identities with observed-target
integrability.  Component `HasLaw` support gives finite double-score coverage;
the selected-Hájek endpoint transfers integrability from the observed WDSM
targets through the a.e. target-transport identities.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
    {PATTProgCell : Type*}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        pateRepr.selectedHajekPATE =
            (∫ sample,
              treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂sampleLaw) ∧
          pattRepr.selectedHajekPATT =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂sampleLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂sampleLaw) := by
  constructor
  · exact
      ae_pateDoubleScoreCover_of_component_hasLaw
        (mSample := mSample) (sampleLaw := sampleLaw)
        propensityCells treatedProgCells controlProgCells propensityScore
        treatedPrognosticScore controlPrognosticScore hpropensityLaw
        htreatedLaw hcontrolLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpropensityCoverLaw htreatedCoverLaw
        hcontrolCoverLaw
  · constructor
    · exact
        ae_pattDoubleScoreCover_of_component_hasLaw
          (mSample := mSample) (sampleLaw := sampleLaw)
          propensityCells pattProgCells propensityScore pattPrognosticScore
          hpropensityLaw hpattLaw hpropensityCellsMeas hpattCellsMeas
          hpropensityCoverLaw hpattCoverLaw
    · exact
        selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
          hcontrolSampling hpattSampling propensityScore
          treatedPrognosticScore controlPrognosticScore pattPrognosticScore
          treatedOutcome controlOutcome treatedEffectNumerator treatedMass
          treatedTarget controlTarget effectTarget massTarget treatedValue
          controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
          hreprC hreprNumerator hreprMass hmassTargetNonzero
          hpropensityScore htreatedScore hcontrolScore hpattComponentScore
          htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
          hmassOutcomeInt
          htreatedTransport hcontrolTransport hnumeratorTransport
          hmassTransport htreatedTargetVersion hcontrolTargetVersion
          hnumeratorTargetVersion hmassTargetVersion

/--
Component-law direct target-score-version route packaged as a
`SurveyWeightedScoreMeanBridge`.  This exposes component finite-support and
target score-version assumptions directly, without primitive-sigma
conditional-mean premises.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_targetScoreVersions_targetTransport_targetRepresentation
    {PATTProgCell : Type*}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlTarget =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      effectTarget =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedTargetInt,
        hcontrolTargetInt, heffectTargetInt, hmassTargetInt,
        htreatedTransport, hcontrolTransport, hnumeratorTransport,
        hmassTransport, htreatedTargetVersion, hcontrolTargetVersion,
        hnumeratorTargetVersion, hmassTargetVersion⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_targetScoreVersions_targetTransport_targetRepresentation
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling propensityCells treatedProgCells
        controlProgCells pattProgCells propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedTarget controlTarget effectTarget massTarget treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
        hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
        htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetVersion
        hcontrolTargetVersion hnumeratorTargetVersion hmassTargetVersion with
      ⟨_hpateCover, _hpattCover, hendpoint⟩
    exact hendpoint
  }

/--
Observed-integrability version of the component-law direct target-score bridge.
It keeps component finite-support assumptions explicit, but asks for
integrability of the observed WDSM targets rather than the transported
latent/reference targets.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
    {PATTProgCell : Type*}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlTarget =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      effectTarget =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedOutcomeInt,
        hcontrolOutcomeInt, hnumeratorOutcomeInt, hmassOutcomeInt,
        htreatedTransport, hcontrolTransport, hnumeratorTransport,
        hmassTransport, htreatedTargetVersion, hcontrolTargetVersion,
        hnumeratorTargetVersion, hmassTargetVersion⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling propensityCells treatedProgCells
        controlProgCells pattProgCells propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedTarget controlTarget effectTarget massTarget treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
        hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
        htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw htreatedOutcomeInt
        hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetVersion
        hcontrolTargetVersion hnumeratorTargetVersion hmassTargetVersion with
      ⟨_hpateCover, _hpattCover, hendpoint⟩
    exact hendpoint
  }

/--
Lower selected-Hájek target-transport bridge from primitive latent/reference
correct-score identities.  This composes the direct primitive-to-score tower
step with the target-transport representation bridge, so the balancing field
contains primitive correct-score identities rather than already-towered
score-sigma target conditional means.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_primitive_targetTransport_targetRepresentation_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedTransport, hcontrolTransport, hnumeratorTransport,
        hmassTransport, htreatedTargetCond, hcontrolTargetCond,
        hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      condExp_targetDoubleScoreVersions_of_component_primitive_correctScoreRoute_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedTarget controlTarget effectTarget
        massTarget treatedValue controlValue scoreEffectCellValue
        scoreTreatedMassCellValue hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
      ⟨⟨htreatedScoreCond, hcontrolScoreCond⟩, hnumeratorScoreCond,
        hmassScoreCond⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions_targetTransport_targetRepresentation
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) (hscorePrimitive.trans hprimitiveSub)
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hmassTargetNonzero htreatedTransport
        hcontrolTransport hnumeratorTransport hmassTransport
        htreatedScoreCond hcontrolScoreCond hnumeratorScoreCond
        hmassScoreCond
  }

/--
Lower selected-Hájek target-transport bridge from stronger a.e. target
score-version equalities.  This removes the four primitive conditional-mean
route assumptions from the component primitive bridge, but only for references
that genuinely supply a.e. latent/reference target score versions.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_primitive_targetScoreVersions_targetTransport_targetRepresentation_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlTarget =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      effectTarget =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedTargetInt, hcontrolTargetInt, heffectTargetInt,
        hmassTargetInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetVersion,
        hcontrolTargetVersion, hnumeratorTargetVersion,
        hmassTargetVersion⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      primitiveTargetCondExp_doubleScoreVersions_of_ae_targetScoreVersions_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedTarget controlTarget effectTarget
        massTarget treatedValue controlValue scoreEffectCellValue
        scoreTreatedMassCellValue hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt
        htreatedTargetVersion hcontrolTargetVersion hnumeratorTargetVersion
        hmassTargetVersion with
      ⟨⟨htreatedTargetCond, hcontrolTargetCond⟩, hnumeratorTargetCond,
        hmassTargetCond⟩
    rcases
      condExp_targetDoubleScoreVersions_of_component_primitive_correctScoreRoute_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedTarget controlTarget effectTarget
        massTarget treatedValue controlValue scoreEffectCellValue
        scoreTreatedMassCellValue hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
      ⟨⟨htreatedScoreCond, hcontrolScoreCond⟩, hnumeratorScoreCond,
        hmassScoreCond⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions_targetTransport_targetRepresentation
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) (hscorePrimitive.trans hprimitiveSub)
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hmassTargetNonzero htreatedTransport
        hcontrolTransport hnumeratorTransport hmassTransport
        htreatedScoreCond hcontrolScoreCond hnumeratorScoreCond
        hmassScoreCond
  }

/--
Observed-integrability version of
`surveyWeightedScoreMeanBridge_of_selectedHajek_component_primitive_targetScoreVersions_targetTransport_targetRepresentation_of_le`.
It keeps the primitive target-score route and target transport explicit, but
derives latent/reference target integrability from observed WDSM target
integrability.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_primitive_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlTarget =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      effectTarget =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedOutcomeInt, hcontrolOutcomeInt, hnumeratorOutcomeInt,
        hmassOutcomeInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetVersion,
        hcontrolTargetVersion, hnumeratorTargetVersion,
        hmassTargetVersion⟩
    exact
      (surveyWeightedScoreMeanBridge_of_selectedHajek_component_primitive_targetScoreVersions_targetTransport_targetRepresentation_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub pateRepr
        pattRepr propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedTarget
        controlTarget effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue).bridge
        ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
          htreatedOutcomeInt.congr htreatedTransport,
          hcontrolOutcomeInt.congr hcontrolTransport,
          hnumeratorOutcomeInt.congr hnumeratorTransport,
          hmassOutcomeInt.congr hmassTransport, htreatedTransport,
          hcontrolTransport, hnumeratorTransport, hmassTransport,
          htreatedTargetVersion, hcontrolTargetVersion,
          hnumeratorTargetVersion, hmassTargetVersion⟩
        hweighted
  }

/--
Component-law Yang-Zhang/Antonelli finite-cover endpoint using the direct
primitive-to-score target route.  Component `HasLaw` support supplies the
finite PATE/PATT double-score cover facts, while the selected-Hájek endpoint
is proved from component score measurability, observed-to-target transport,
primitive latent/reference correct-score identities, and latent/reference
target representation.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_primitive_targetTransport_targetRepresentation_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        pateRepr.selectedHajekPATE =
            (∫ sample,
              treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂sampleLaw) ∧
          pattRepr.selectedHajekPATT =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂sampleLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂sampleLaw) := by
  constructor
  · exact
      ae_pateDoubleScoreCover_of_component_hasLaw
        (mSample := mSample) (sampleLaw := sampleLaw)
        propensityCells treatedProgCells controlProgCells propensityScore
        treatedPrognosticScore controlPrognosticScore hpropensityLaw
        htreatedLaw hcontrolLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpropensityCoverLaw htreatedCoverLaw
        hcontrolCoverLaw
  · constructor
    · exact
        ae_pattDoubleScoreCover_of_component_hasLaw
          (mSample := mSample) (sampleLaw := sampleLaw)
          propensityCells pattProgCells propensityScore pattPrognosticScore
          hpropensityLaw hpattLaw hpropensityCellsMeas hpattCellsMeas
          hpropensityCoverLaw hpattCoverLaw
    · rcases
        condExp_targetDoubleScoreVersions_of_component_primitive_correctScoreRoute_of_le
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
          propensityScore treatedPrognosticScore controlPrognosticScore
          pattPrognosticScore treatedTarget controlTarget effectTarget
          massTarget treatedValue controlValue scoreEffectCellValue
          scoreTreatedMassCellValue hpropensityScore htreatedScore
          hcontrolScore hpattComponentScore htreatedTargetCond
          hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
        ⟨⟨htreatedScoreCond, hcontrolScoreCond⟩, hnumeratorScoreCond,
          hmassScoreCond⟩
      exact
        selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions_targetTransport_targetRepresentation
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) (hscorePrimitive.trans hprimitiveSub)
          pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
          propensityScore treatedPrognosticScore controlPrognosticScore
          pattPrognosticScore treatedOutcome controlOutcome
          treatedEffectNumerator treatedMass treatedTarget controlTarget
          effectTarget massTarget treatedValue controlValue
          scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
          hreprNumerator hreprMass hmassTargetNonzero htreatedTransport
          hcontrolTransport hnumeratorTransport hmassTransport
          htreatedScoreCond hcontrolScoreCond hnumeratorScoreCond
          hmassScoreCond

/--
Component-law Yang-Zhang/Antonelli finite-cover endpoint from stronger a.e.
latent/reference target score versions.  Component `HasLaw` support still
proves the finite PATE/PATT double-score cover facts; the selected-Hájek
endpoint no longer assumes primitive target conditional means, deriving them
from target integrability and a.e. target score-version equalities.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_primitive_targetScoreVersions_targetTransport_targetRepresentation_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        pateRepr.selectedHajekPATE =
            (∫ sample,
              treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂sampleLaw) ∧
          pattRepr.selectedHajekPATT =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂sampleLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂sampleLaw) := by
  rcases
    primitiveTargetCondExp_doubleScoreVersions_of_ae_targetScoreVersions_of_le
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedTarget controlTarget effectTarget massTarget
      treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
      hpropensityScore htreatedScore hcontrolScore hpattComponentScore
      htreatedTargetInt hcontrolTargetInt heffectTargetInt hmassTargetInt
      htreatedTargetVersion hcontrolTargetVersion hnumeratorTargetVersion
      hmassTargetVersion with
    ⟨⟨htreatedTargetCond, hcontrolTargetCond⟩, hnumeratorTargetCond,
      hmassTargetCond⟩
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_primitive_targetTransport_targetRepresentation_of_le
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub pateRepr pattRepr
      htreatedSampling hcontrolSampling hpattSampling propensityCells
      treatedProgCells controlProgCells pattProgCells propensityScore
      treatedPrognosticScore controlPrognosticScore pattPrognosticScore
      treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedTarget controlTarget effectTarget massTarget treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
      hreprC hreprNumerator hreprMass hpropensityScore htreatedScore
      hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
      hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
      hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw htreatedCoverLaw
      hcontrolCoverLaw hpattCoverLaw hmassTargetNonzero htreatedTransport
      hcontrolTransport hnumeratorTransport hmassTransport
      htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
      hmassTargetCond

/--
Observed-integrability version of the component-law primitive target-score
endpoint.  The primitive route still derives target conditional means from
a.e. latent/reference target score versions, but target integrability is
transported from the observed WDSM targets instead of being assumed directly.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_primitive_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetVersion :
      treatedTarget =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetVersion :
      controlTarget =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetVersion :
      effectTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetVersion :
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        pateRepr.selectedHajekPATE =
            (∫ sample,
              treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂sampleLaw) ∧
          pattRepr.selectedHajekPATT =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂sampleLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂sampleLaw) :=
  selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_primitive_targetScoreVersions_targetTransport_targetRepresentation_of_le
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub pateRepr pattRepr
    htreatedSampling hcontrolSampling hpattSampling propensityCells
    treatedProgCells controlProgCells pattProgCells propensityScore
    treatedPrognosticScore controlPrognosticScore pattPrognosticScore
    treatedOutcome controlOutcome treatedEffectNumerator treatedMass
    treatedTarget controlTarget effectTarget massTarget treatedValue
    controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
    hreprNumerator hreprMass hpropensityScore htreatedScore hcontrolScore
    hpattComponentScore hpropensityLaw htreatedLaw hcontrolLaw hpattLaw
    hpropensityCellsMeas htreatedCellsMeas hcontrolCellsMeas hpattCellsMeas
    hpropensityCoverLaw htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw
    (htreatedOutcomeInt.congr htreatedTransport)
    (hcontrolOutcomeInt.congr hcontrolTransport)
    (hnumeratorOutcomeInt.congr hnumeratorTransport)
    (hmassOutcomeInt.congr hmassTransport) hmassTargetNonzero
    htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
    htreatedTargetVersion hcontrolTargetVersion hnumeratorTargetVersion
    hmassTargetVersion

/--
Component-law Yang-Zhang/Antonelli stronger-a.e. target-score-version route
packaged as a `SurveyWeightedScoreMeanBridge`.  Compared with the primitive
target-transport bridge below, the balancing field does not assume primitive
latent/reference conditional means; those are derived from target
integrability and a.e. target score-version equalities.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_primitive_targetScoreVersions_targetTransport_targetRepresentation_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlTarget =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      effectTarget =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedTargetInt,
        hcontrolTargetInt, heffectTargetInt, hmassTargetInt,
        htreatedTransport, hcontrolTransport, hnumeratorTransport,
        hmassTransport, htreatedTargetVersion, hcontrolTargetVersion,
        hnumeratorTargetVersion, hmassTargetVersion⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_primitive_targetScoreVersions_targetTransport_targetRepresentation_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityCells treatedProgCells controlProgCells pattProgCells
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
        hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
        htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetVersion
        hcontrolTargetVersion hnumeratorTargetVersion hmassTargetVersion with
      ⟨_hpateCover, _hpattCover, hendpoint⟩
    exact hendpoint
  }

/--
Observed-integrability version of the component-law primitive target-score
`SurveyWeightedScoreMeanBridge`.  It removes the four latent/reference target
integrability fields by deriving them from observed WDSM target integrability
and a.e. target transport before applying the primitive target-score route.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_primitive_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlTarget =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      effectTarget =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      massTarget =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedOutcomeInt,
        hcontrolOutcomeInt, hnumeratorOutcomeInt, hmassOutcomeInt,
        htreatedTransport, hcontrolTransport, hnumeratorTransport,
        hmassTransport, htreatedTargetVersion, hcontrolTargetVersion,
        hnumeratorTargetVersion, hmassTargetVersion⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_primitive_targetScoreVersions_targetTransport_targetRepresentation_outcomeIntegrable_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityCells treatedProgCells controlProgCells pattProgCells
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
        hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
        htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw htreatedOutcomeInt
        hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetVersion
        hcontrolTargetVersion hnumeratorTargetVersion hmassTargetVersion with
      ⟨_hpateCover, _hpattCover, hendpoint⟩
    exact hendpoint
  }

/--
Component-law Yang-Zhang/Antonelli primitive target-transport route packaged
as a `SurveyWeightedScoreMeanBridge`.  Component `HasLaw` finite support stays
in the balancing field for cover evidence, while the selected-Hájek endpoint
uses the direct `scoreSigma ≤ primitiveSigma` primitive-to-score route and
latent/reference target representation.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_primitive_targetTransport_targetRepresentation_of_le
    {PATTProgCell : Type*}
    {primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscorePrimitive : scoreSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hscorePrimitive.trans hprimitiveSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedTransport,
        hcontrolTransport, hnumeratorTransport, hmassTransport,
        htreatedTargetCond, hcontrolTargetCond, hnumeratorTargetCond,
        hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_primitive_targetTransport_targetRepresentation_of_le
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscorePrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityCells treatedProgCells controlProgCells pattProgCells
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
        hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
        htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
      ⟨_hpateCover, _hpattCover, hendpoint⟩
    exact hendpoint
  }

/--
Selected-Hájek PATE/PATT identification from covariate-level correct-score
conditional means.  This is the conditional-expectation route toward the
survey-weighted score-mean bridge; it leaves the paper-level proof of the
covariate conditional-mean identities as the remaining probability interface.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedCov :
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolCov :
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorCov :
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  rcases
    condExp_doubleScoreVersions_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovSub propensityScore
      treatedPrognosticScore controlPrognosticScore pattPrognosticScore
      treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue hpateScore hpattScore htreatedCov
      hcontrolCov hnumeratorCov hmassCov with
    ⟨hpateCond, hpattCond⟩
  rcases hpateCond with ⟨htreatedCond, hcontrolCond⟩
  rcases hpattCond with ⟨hnumeratorCond, hmassCond⟩
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) (hscoreCov.trans hcovSub) pateRepr pattRepr
      htreatedSampling hcontrolSampling hpattSampling hpattMass
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass htreatedCond hcontrolCond hnumeratorCond
      hmassCond

/--
Selected-Hájek PATE/PATT identification from primitive residual-zero
decompositions.  This composes the residual route that proves covariate-level
correct-score identities with the selected-Hájek covariate correct-score
endpoint, so the remaining double-score probability boundary is stated as
primitive residual orthogonality plus decomposition/integrability inputs.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitiveResidual_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedResidual controlResidual numeratorResidual massResidual :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedResidualInt : Integrable treatedResidual sampleLaw)
    (hcontrolResidualInt : Integrable controlResidual sampleLaw)
    (hnumeratorResidualInt : Integrable numeratorResidual sampleLaw)
    (hmassResidualInt : Integrable massResidual sampleLaw)
    (htreatedDecomp :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          treatedValue (treatedPrognosticScore sample) +
            treatedResidual sample)
    (hcontrolDecomp :
      controlOutcome =ᵐ[sampleLaw]
        fun sample =>
          controlValue (controlPrognosticScore sample) +
            controlResidual sample)
    (hnumeratorDecomp :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) +
            numeratorResidual sample)
    (hmassDecomp :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) +
            massResidual sample)
    (htreatedPrimitiveZero :
      sampleLaw[treatedResidual | primitiveSigma] =ᵐ[sampleLaw] 0)
    (hcontrolPrimitiveZero :
      sampleLaw[controlResidual | primitiveSigma] =ᵐ[sampleLaw] 0)
    (hnumeratorPrimitiveZero :
      sampleLaw[numeratorResidual | primitiveSigma] =ᵐ[sampleLaw] 0)
    (hmassPrimitiveZero :
      sampleLaw[massResidual | primitiveSigma] =ᵐ[sampleLaw] 0) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  rcases
    covariate_condExp_doubleScoreVersions_of_primitiveResidual_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedResidual
      controlResidual numeratorResidual massResidual treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue
      (hpateScore.mono hscoreCov) (hpattScore.mono hscoreCov)
      htreatedVersionInt hcontrolVersionInt hnumeratorVersionInt
      hmassVersionInt htreatedResidualInt hcontrolResidualInt
      hnumeratorResidualInt hmassResidualInt htreatedDecomp hcontrolDecomp
      hnumeratorDecomp hmassDecomp htreatedPrimitiveZero
      hcontrolPrimitiveZero hnumeratorPrimitiveZero hmassPrimitiveZero with
    ⟨hpateCov, hpattCov⟩
  rcases hpateCov with ⟨htreatedCov, hcontrolCov⟩
  rcases hpattCov with ⟨hnumeratorCov, hmassCov⟩
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov
      (hcovPrimitive.trans hprimitiveSub) pateRepr pattRepr
      htreatedSampling hcontrolSampling hpattSampling hpattMass
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass hpateScore hpattScore htreatedCov
      hcontrolCov hnumeratorCov hmassCov

/--
Selected-Hájek PATE/PATT identification from primitive zero conditional means
of subtraction residuals.  This is the residual route with residuals fixed to
`raw target - score version`, so callers provide raw-target integrability and
the primitive zero conditional-mean facts for those differences.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitiveSubResidual_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedPrimitiveZero :
      sampleLaw[(fun sample =>
        treatedOutcome sample - treatedValue (treatedPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0)
    (hcontrolPrimitiveZero :
      sampleLaw[(fun sample =>
        controlOutcome sample - controlValue (controlPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0)
    (hnumeratorPrimitiveZero :
      sampleLaw[(fun sample =>
        treatedEffectNumerator sample -
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0)
    (hmassPrimitiveZero :
      sampleLaw[(fun sample =>
        treatedMass sample -
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  rcases
    covariate_condExp_doubleScoreVersions_of_primitiveSubResidual_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue
      (hpateScore.mono hscoreCov) (hpattScore.mono hscoreCov)
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedVersionInt hcontrolVersionInt
      hnumeratorVersionInt hmassVersionInt htreatedPrimitiveZero
      hcontrolPrimitiveZero hnumeratorPrimitiveZero hmassPrimitiveZero with
    ⟨hpateCov, hpattCov⟩
  rcases hpateCov with ⟨htreatedCov, hcontrolCov⟩
  rcases hpattCov with ⟨hnumeratorCov, hmassCov⟩
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov
      (hcovPrimitive.trans hprimitiveSub) pateRepr pattRepr
      htreatedSampling hcontrolSampling hpattSampling hpattMass
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass hpateScore hpattScore htreatedCov
      hcontrolCov hnumeratorCov hmassCov

/--
Selected-Hájek PATE/PATT identification from primitive correct-score
conditional means.  This composes the checked route from primitive
conditional-mean identities to covariate-level identities with the existing
selected-Hájek covariate correct-score endpoint.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  rcases
    covariate_condExp_doubleScoreVersions_of_primitive_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue
      (hpateScore.mono hscoreCov) (hpattScore.mono hscoreCov)
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedVersionInt hcontrolVersionInt
      hnumeratorVersionInt hmassVersionInt htreatedPrimitiveCond
      hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond with
    ⟨hpateCov, hpattCov⟩
  rcases hpateCov with ⟨htreatedCov, hcontrolCov⟩
  rcases hpattCov with ⟨hnumeratorCov, hmassCov⟩
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov
      (hcovPrimitive.trans hprimitiveSub) pateRepr pattRepr
      htreatedSampling hcontrolSampling hpattSampling hpattMass
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass hpateScore hpattScore htreatedCov
      hcontrolCov hnumeratorCov hmassCov

/--
Outcome-integrable variant of
`selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitive_correctScoreRoute`.
The score-version integrability assumptions are recovered from the primitive
conditional-mean identities.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitive_correctScoreRoute_outcomeIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) :=
  selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitive_correctScoreRoute
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
    pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
    hpattMass propensityScore treatedPrognosticScore controlPrognosticScore
    pattPrognosticScore treatedOutcome controlOutcome treatedEffectNumerator
    treatedMass treatedValue controlValue scoreEffectCellValue
    scoreTreatedMassCellValue hreprT hreprC hreprNumerator hreprMass
    hpateScore hpattScore htreatedOutcomeInt hcontrolOutcomeInt
    hnumeratorOutcomeInt hmassOutcomeInt
    (integrable_condExp.congr htreatedPrimitiveCond)
    (integrable_condExp.congr hcontrolPrimitiveCond)
    (integrable_condExp.congr hnumeratorPrimitiveCond)
    (integrable_condExp.congr hmassPrimitiveCond) htreatedPrimitiveCond
    hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond

/--
`SurveyWeightedScoreMeanBridge` packaged from primitive residual-zero
decompositions.  Downstream WDSM endpoints can consume the selected-Hájek
score-space identification bridge directly with residual orthogonality inputs,
without restating the intermediate covariate correct-score conditional means.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_primitiveResidual_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedResidual controlResidual numeratorResidual massResidual :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw ∧
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw ∧
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw ∧
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw ∧
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw ∧
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw ∧
      Integrable treatedResidual sampleLaw ∧
      Integrable controlResidual sampleLaw ∧
      Integrable numeratorResidual sampleLaw ∧
      Integrable massResidual sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw]
        (fun sample =>
          treatedValue (treatedPrognosticScore sample) +
            treatedResidual sample) ∧
      controlOutcome =ᵐ[sampleLaw]
        (fun sample =>
          controlValue (controlPrognosticScore sample) +
            controlResidual sample) ∧
      treatedEffectNumerator =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) +
            numeratorResidual sample) ∧
      treatedMass =ᵐ[sampleLaw]
        (fun sample =>
          scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample) +
            massResidual sample) ∧
      sampleLaw[treatedResidual | primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[controlResidual | primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[numeratorResidual | primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[massResidual | primitiveSigma] =ᵐ[sampleLaw] 0
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpateScore, hpattScore, htreatedVersionInt, hcontrolVersionInt,
        hnumeratorVersionInt, hmassVersionInt, htreatedResidualInt,
        hcontrolResidualInt, hnumeratorResidualInt, hmassResidualInt,
        htreatedDecomp, hcontrolDecomp, hnumeratorDecomp, hmassDecomp,
        htreatedPrimitiveZero, hcontrolPrimitiveZero, hnumeratorPrimitiveZero,
        hmassPrimitiveZero⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitiveResidual_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        hpattMass propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedResidual
        controlResidual numeratorResidual massResidual treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hpateScore hpattScore
        htreatedVersionInt hcontrolVersionInt hnumeratorVersionInt
        hmassVersionInt htreatedResidualInt hcontrolResidualInt
        hnumeratorResidualInt hmassResidualInt htreatedDecomp hcontrolDecomp
        hnumeratorDecomp hmassDecomp htreatedPrimitiveZero
        hcontrolPrimitiveZero hnumeratorPrimitiveZero hmassPrimitiveZero
  }

/--
`SurveyWeightedScoreMeanBridge` packaged from primitive zero conditional means
of subtraction residuals.  This is the same selected-Hájek bridge as the
residual route above, but the residuals are fixed to `raw target - score
version`, so the bridge boundary is closer to the paper's correct-score
conditional-mean calculations.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_primitiveSubResidual_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw ∧
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw ∧
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw ∧
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw ∧
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw ∧
      sampleLaw[(fun sample =>
        treatedOutcome sample - treatedValue (treatedPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        controlOutcome sample - controlValue (controlPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        treatedEffectNumerator sample -
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0 ∧
      sampleLaw[(fun sample =>
        treatedMass sample -
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) |
          primitiveSigma] =ᵐ[sampleLaw] 0
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpateScore, hpattScore, htreatedOutcomeInt, hcontrolOutcomeInt,
        hnumeratorOutcomeInt, hmassOutcomeInt, htreatedVersionInt,
        hcontrolVersionInt, hnumeratorVersionInt, hmassVersionInt,
        htreatedPrimitiveZero, hcontrolPrimitiveZero, hnumeratorPrimitiveZero,
        hmassPrimitiveZero⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitiveSubResidual_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        hpattMass propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hpateScore hpattScore
        htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
        hmassOutcomeInt htreatedVersionInt hcontrolVersionInt
        hnumeratorVersionInt hmassVersionInt htreatedPrimitiveZero
        hcontrolPrimitiveZero hnumeratorPrimitiveZero hmassPrimitiveZero
  }

/--
`SurveyWeightedScoreMeanBridge` packaged from primitive correct-score
conditional-mean identities.  This is the bridge-level route closest to the
paper statement when the Yang-Zhang/Antonelli argument supplies conditional
means at a richer primitive sigma-field.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw ∧
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw ∧
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw ∧
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw ∧
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw ∧
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpateScore, hpattScore, htreatedOutcomeInt, hcontrolOutcomeInt,
        hnumeratorOutcomeInt, hmassOutcomeInt, htreatedVersionInt,
        hcontrolVersionInt, hnumeratorVersionInt, hmassVersionInt,
        htreatedPrimitiveCond, hcontrolPrimitiveCond, hnumeratorPrimitiveCond,
        hmassPrimitiveCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitive_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        hpattMass propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hpateScore hpattScore
        htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
        hmassOutcomeInt htreatedVersionInt hcontrolVersionInt
        hnumeratorVersionInt hmassVersionInt htreatedPrimitiveCond
        hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond
  }

/--
Component-score version of the primitive correct-score selected-Hájek route.
It derives the joint PATE/PATT double-score measurability premises from the
component propensity and prognostic scores, while keeping the primitive
conditional-mean identities as the paper-level probability input.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedVersionInt :
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw)
    (hcontrolVersionInt :
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw)
    (hnumeratorVersionInt :
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (hmassVersionInt :
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw)
    (htreatedPrimitiveCond :
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitive_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
      pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
      hpattMass propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass
      (by
        simpa [pateDoubleScore] using
          ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore))
      (by
        simpa [pattDoubleScore] using
          hpropensityScore.prodMk hpattComponentScore)
      htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
      hmassOutcomeInt htreatedVersionInt hcontrolVersionInt
      hnumeratorVersionInt hmassVersionInt htreatedPrimitiveCond
      hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond

/--
Component-score selected-Hájek PATE/PATT identification when a paper route
first transports observed WDSM targets to latent/reference targets and proves
primitive correct-score conditional means for those transported targets.  This
is the selected-Hájek analogue of the raw selection-density target-transport
route, and it keeps the target-transport identities explicit.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  rcases
    primitiveCondExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute
      (mSample := mSample) (sampleLaw := sampleLaw)
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedTarget controlTarget
      effectTarget massTarget treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue htreatedTransport hcontrolTransport
      hnumeratorTransport hmassTransport htreatedTargetCond
      hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
    ⟨⟨htreatedPrimitiveCond, hcontrolPrimitiveCond⟩,
      hnumeratorPrimitiveCond, hmassPrimitiveCond⟩
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_primitive_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
      pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
      hpattMass propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass hpropensityScore htreatedScore
      hcontrolScore hpattComponentScore htreatedOutcomeInt
      hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
      (integrable_condExp.congr htreatedPrimitiveCond)
      (integrable_condExp.congr hcontrolPrimitiveCond)
      (integrable_condExp.congr hnumeratorPrimitiveCond)
      (integrable_condExp.congr hmassPrimitiveCond)
      htreatedPrimitiveCond hcontrolPrimitiveCond hnumeratorPrimitiveCond
      hmassPrimitiveCond

/--
Target-integrable selected-Hájek version of
`selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute`.
The four observed-target integrability side conditions are derived from
integrability of the transported latent/reference targets and the four a.e.
target-transport identities.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) :=
  selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
    pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
    hpattMass propensityScore treatedPrognosticScore controlPrognosticScore
    pattPrognosticScore treatedOutcome controlOutcome treatedEffectNumerator
    treatedMass treatedTarget controlTarget effectTarget massTarget
    treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
    hreprT hreprC hreprNumerator hreprMass hpropensityScore htreatedScore
    hcontrolScore hpattComponentScore
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := sampleLaw) treatedOutcome
      treatedTarget htreatedTransport htreatedTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := sampleLaw) controlOutcome
      controlTarget hcontrolTransport hcontrolTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := sampleLaw) treatedEffectNumerator
      effectTarget hnumeratorTransport heffectTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := sampleLaw) treatedMass
      massTarget hmassTransport hmassTargetInt)
    htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
    htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond hmassTargetCond

/--
Target-integrable selected-Hájek target-transport route with a latent/reference
PATT mass nonzero premise.  The nonzero population treated mass in the
`PATTRepresentation` is recovered from the representation equality and the
a.e. mass-target transport.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  have hpattMass : pattRepr.population_treated_mass ≠ 0 := by
    intro hpattMassZero
    apply hmassTargetNonzero
    calc
      (∫ sample, massTarget sample ∂sampleLaw)
          = ∫ sample, treatedMass sample ∂sampleLaw :=
        (integral_eq_of_ae_targetTransport
          (mSample := mSample) (sampleLaw := sampleLaw) treatedMass
          massTarget hmassTransport).symm
      _ = pattRepr.population_treated_mass := hreprMass.symm
      _ = 0 := hpattMassZero
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
      pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
      hpattMass propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedTarget
      controlTarget effectTarget massTarget treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass hpropensityScore htreatedScore hcontrolScore
      hpattComponentScore htreatedTargetInt hcontrolTargetInt
      heffectTargetInt hmassTargetInt htreatedTransport hcontrolTransport
      hnumeratorTransport hmassTransport htreatedTargetCond
      hcontrolTargetCond hnumeratorTargetCond hmassTargetCond

/--
Target-representation variant of
`selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass`.
The PATE/PATT representation equalities are stated against the transported
latent/reference targets; observed-target representation equalities are
recovered by a.e. integral transport.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
      pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedTarget controlTarget
      effectTarget massTarget treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue
      (by
        calc
          pateRepr.treated.population_target =
              ∫ sample, treatedTarget sample ∂sampleLaw := hreprT
          _ = ∫ sample, treatedOutcome sample ∂sampleLaw :=
              (integral_eq_of_ae_targetTransport
                (mSample := mSample) (sampleLaw := sampleLaw)
                treatedOutcome treatedTarget htreatedTransport).symm)
      (by
        calc
          pateRepr.control.population_target =
              ∫ sample, controlTarget sample ∂sampleLaw := hreprC
          _ = ∫ sample, controlOutcome sample ∂sampleLaw :=
              (integral_eq_of_ae_targetTransport
                (mSample := mSample) (sampleLaw := sampleLaw)
                controlOutcome controlTarget hcontrolTransport).symm)
      (by
        calc
          pattRepr.population_treated_effect_numerator =
              ∫ sample, effectTarget sample ∂sampleLaw := hreprNumerator
          _ = ∫ sample, treatedEffectNumerator sample ∂sampleLaw :=
              (integral_eq_of_ae_targetTransport
                (mSample := mSample) (sampleLaw := sampleLaw)
                treatedEffectNumerator effectTarget hnumeratorTransport).symm)
      (by
        calc
          pattRepr.population_treated_mass =
              ∫ sample, massTarget sample ∂sampleLaw := hreprMass
          _ = ∫ sample, treatedMass sample ∂sampleLaw :=
              (integral_eq_of_ae_targetTransport
                (mSample := mSample) (sampleLaw := sampleLaw) treatedMass
                massTarget hmassTransport).symm)
      hpropensityScore htreatedScore hcontrolScore hpattComponentScore
      htreatedTargetInt hcontrolTargetInt heffectTargetInt hmassTargetInt
      hmassTargetNonzero htreatedTransport hcontrolTransport
      hnumeratorTransport hmassTransport htreatedTargetCond
      hcontrolTargetCond hnumeratorTargetCond hmassTargetCond

/--
Observed-integrability target-representation variant of
`selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation`.
The PATE/PATT representation and denominator nonzero premises remain stated
on latent/reference targets, while target integrability is transported from
the observed WDSM targets.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_outcomeIntegrable_targetMass_targetRepresentation
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt : Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) :=
  selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
    pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
    propensityScore treatedPrognosticScore controlPrognosticScore
    pattPrognosticScore treatedOutcome controlOutcome treatedEffectNumerator
    treatedMass treatedTarget controlTarget effectTarget massTarget
    treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
    hreprT hreprC hreprNumerator hreprMass hpropensityScore htreatedScore
    hcontrolScore hpattComponentScore
    (htreatedOutcomeInt.congr htreatedTransport)
    (hcontrolOutcomeInt.congr hcontrolTransport)
    (hnumeratorOutcomeInt.congr hnumeratorTransport)
    (hmassOutcomeInt.congr hmassTransport) hmassTargetNonzero
    htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
    htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
    hmassTargetCond

/--
Component-score primitive correct-score route packaged as a
`SurveyWeightedScoreMeanBridge`.  The balancing input is stated in terms of
component score measurability and primitive conditional-mean identities.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      Integrable (fun sample => treatedValue (treatedPrognosticScore sample))
        sampleLaw ∧
      Integrable (fun sample => controlValue (controlPrognosticScore sample))
        sampleLaw ∧
      Integrable
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw ∧
      Integrable
        (fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
        sampleLaw ∧
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedOutcomeInt, hcontrolOutcomeInt, hnumeratorOutcomeInt,
        hmassOutcomeInt, htreatedVersionInt, hcontrolVersionInt,
        hnumeratorVersionInt, hmassVersionInt, htreatedPrimitiveCond,
        hcontrolPrimitiveCond, hnumeratorPrimitiveCond, hmassPrimitiveCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_primitive_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        hpattMass propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedOutcomeInt
        hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
        htreatedVersionInt hcontrolVersionInt hnumeratorVersionInt
        hmassVersionInt htreatedPrimitiveCond hcontrolPrimitiveCond
        hnumeratorPrimitiveCond hmassPrimitiveCond
  }

/--
Outcome-integrable component primitive correct-score route packaged as a
`SurveyWeightedScoreMeanBridge`.  Compared with
`surveyWeightedScoreMeanBridge_of_selectedHajek_component_primitive_correctScoreRoute`,
the balancing field no longer asks separately for score-version integrability;
those facts are derived from the primitive conditional-mean identities.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_primitive_correctScoreRoute_outcomeIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      sampleLaw[treatedOutcome | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[treatedMass | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedOutcomeInt, hcontrolOutcomeInt, hnumeratorOutcomeInt,
        hmassOutcomeInt, htreatedPrimitiveCond, hcontrolPrimitiveCond,
        hnumeratorPrimitiveCond, hmassPrimitiveCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_primitive_correctScoreRoute_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        hpattMass propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue hreprT
        hreprC hreprNumerator hreprMass
        (by
          simpa [pateDoubleScore] using
            ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore))
        (by
          simpa [pattDoubleScore] using
            hpropensityScore.prodMk hpattComponentScore)
        htreatedOutcomeInt hcontrolOutcomeInt hnumeratorOutcomeInt
        hmassOutcomeInt htreatedPrimitiveCond hcontrolPrimitiveCond
        hnumeratorPrimitiveCond hmassPrimitiveCond
  }

/--
Component-score target-transport correct-score route packaged as a
`SurveyWeightedScoreMeanBridge`.  The balancing field exposes the paper
probability boundary as a.e. transport from observed WDSM targets to
latent/reference targets, plus primitive conditional means for those
transported targets.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedOutcomeInt, hcontrolOutcomeInt, hnumeratorOutcomeInt,
        hmassOutcomeInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetCond,
        hcontrolTargetCond, hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        hpattMass propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedTarget
        controlTarget effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedOutcomeInt
        hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
        htreatedTransport hcontrolTransport hnumeratorTransport
        hmassTransport htreatedTargetCond hcontrolTargetCond
        hnumeratorTargetCond hmassTargetCond
  }

/--
Target-integrable component-score target-transport route packaged as a
`SurveyWeightedScoreMeanBridge`.  Compared with
`surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetTransport_correctScoreRoute`,
the balancing field asks for integrability of the transported latent/reference
targets; observed-target integrability is recovered from the a.e. transport
identities.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedTargetInt, hcontrolTargetInt, heffectTargetInt,
        hmassTargetInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetCond,
        hcontrolTargetCond, hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        hpattMass propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedTarget
        controlTarget effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt htreatedTransport
        hcontrolTransport hnumeratorTransport hmassTransport
        htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
        hmassTargetCond
  }

/--
Target-integrable selected-Hájek bridge with the PATT denominator nonzero
condition stated on the latent/reference mass target.  This removes the
observed-population treated-mass nonzero assumption from the bridge
representation field.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedTargetInt, hcontrolTargetInt, heffectTargetInt,
        hmassTargetInt, hmassTargetNonzero, htreatedTransport,
        hcontrolTransport, hnumeratorTransport, hmassTransport,
        htreatedTargetCond, hcontrolTargetCond, hnumeratorTargetCond,
        hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hreprT, hreprC,
        hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond
  }

/--
Target-representation selected-Hájek bridge for the component target-transport
route.  The representation field is stated against latent/reference target
integrals, while the bridge recovers the observed integral representation by
a.e. integral transport.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedTargetInt, hcontrolTargetInt, heffectTargetInt,
        hmassTargetInt, hmassTargetNonzero, htreatedTransport,
        hcontrolTransport, hnumeratorTransport, hmassTransport,
        htreatedTargetCond, hcontrolTargetCond, hnumeratorTargetCond,
        hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hreprT, hreprC,
        hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond
  }

/--
Observed-integrability selected-Hájek target-representation bridge for the
component target-transport route.  The representation and denominator nonzero
fields remain stated on latent/reference targets, while the balancing field
uses observed WDSM target integrability.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_targetTransport_correctScoreRoute_outcomeIntegrable_targetMass_targetRepresentation
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedOutcomeInt, hcontrolOutcomeInt, hnumeratorOutcomeInt,
        hmassOutcomeInt, hmassTargetNonzero, htreatedTransport,
        hcontrolTransport, hnumeratorTransport, hmassTransport,
        htreatedTargetCond, hcontrolTargetCond, hnumeratorTargetCond,
        hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hreprT, hreprC,
        hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_outcomeIntegrable_targetMass_targetRepresentation
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedOutcomeInt
        hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond
  }

/--
Raw selected-law survey-weighted PATE/PATT double-score identification from
packaged population selection-density designs and primitive component
correct-score conditional means.  The three design records discharge the
selected-law inverse-selection integral recovery assumptions; the remaining
probability boundary is the four primitive conditional means under the
population law.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_primitive_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore populationLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore populationLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore populationLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome populationLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome populationLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator populationLaw)
    (hmassOutcomeInt : Integrable treatedMass populationLaw)
    (htreatedPrimitiveCond :
      populationLaw[treatedOutcome | primitiveSigma] =ᵐ[populationLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolPrimitiveCond :
      populationLaw[controlOutcome | primitiveSigma] =ᵐ[populationLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorPrimitiveCond :
      populationLaw[treatedEffectNumerator | primitiveSigma]
          =ᵐ[populationLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassPrimitiveCond :
      populationLaw[treatedMass | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw treatedDesign) sample : Real) *
          treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real)
          ∂selectedLaw) -
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw controlDesign) sample : Real) *
          controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real)
          ∂selectedLaw) =
        (∫ sample, treatedValue (treatedPrognosticScore sample)
          ∂populationLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂populationLaw) ∧
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw pattDesign) sample : Real) *
          treatedEffectNumerator sample ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedMass sample
          ∂selectedLaw) =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂populationLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂populationLaw) := by
  have hpateScoreCov :
      AEStronglyMeasurable[covariateSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) populationLaw := by
    simpa [pateDoubleScore] using
      (((hpropensityScore.mono hscoreCov).prodMk
        (htreatedScore.mono hscoreCov)).prodMk
          (hcontrolScore.mono hscoreCov))
  have hpattScoreCov :
      AEStronglyMeasurable[covariateSigma]
        (pattDoubleScore propensityScore pattPrognosticScore)
        populationLaw := by
    simpa [pattDoubleScore] using
      (hpropensityScore.mono hscoreCov).prodMk
        (hpattComponentScore.mono hscoreCov)
  rcases
    covariate_condExp_doubleScoreVersions_of_primitive_correctScoreRoute_outcomeIntegrable
      (mSample := mSample) (sampleLaw := populationLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue
      hpateScoreCov hpattScoreCov htreatedOutcomeInt hcontrolOutcomeInt
      hnumeratorOutcomeInt hmassOutcomeInt htreatedPrimitiveCond
      hcontrolPrimitiveCond hnumeratorPrimitiveCond hmassPrimitiveCond with
    ⟨⟨htreatedCov, hcontrolCov⟩, hnumeratorCov, hmassCov⟩
  have hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) populationLaw := by
    simpa [pateDoubleScore] using
      ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore)
  have hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore)
        populationLaw := by
    simpa [pattDoubleScore] using
      hpropensityScore.prodMk hpattComponentScore
  rcases
    condExp_doubleScoreVersions_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hscoreCov
      (hcovPrimitive.trans hprimitiveSub) propensityScore
      treatedPrognosticScore controlPrognosticScore pattPrognosticScore
      treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue hpateScore hpattScore htreatedCov
      hcontrolCov hnumeratorCov hmassCov with
    ⟨⟨htreatedCond, hcontrolCond⟩, hnumeratorCond, hmassCond⟩
  have htreatedTarget :
      (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real) *
            treatedOutcome sample
          ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          @PopulationSelectionDensityDesign.samplingMass Sample mSample
            selectedLaw populationLaw treatedDesign := by
    simpa using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw treatedDesign treatedOutcome)
  have htreatedOne :
      (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real)
          ∂selectedLaw) =
        1 / @PopulationSelectionDensityDesign.samplingMass Sample mSample
          selectedLaw populationLaw treatedDesign := by
    simpa using
      (@PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        Sample mSample selectedLaw populationLaw treatedDesign hpopulationOne)
  have hcontrolTarget :
      (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real) *
            controlOutcome sample
          ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          @PopulationSelectionDensityDesign.samplingMass Sample mSample
            selectedLaw populationLaw controlDesign := by
    simpa using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw controlDesign controlOutcome)
  have hcontrolOne :
      (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real)
          ∂selectedLaw) =
        1 / @PopulationSelectionDensityDesign.samplingMass Sample mSample
          selectedLaw populationLaw controlDesign := by
    simpa using
      (@PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        Sample mSample selectedLaw populationLaw controlDesign hpopulationOne)
  have hnumeratorRecovery :
      (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedEffectNumerator sample ∂selectedLaw) =
        (∫ sample, treatedEffectNumerator sample ∂populationLaw) /
          @PopulationSelectionDensityDesign.samplingMass Sample mSample
            selectedLaw populationLaw pattDesign := by
    simpa using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw pattDesign
        treatedEffectNumerator)
  have hmassRecovery :
      (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedMass sample
          ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) /
          @PopulationSelectionDensityDesign.samplingMass Sample mSample
            selectedLaw populationLaw pattDesign := by
    simpa using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw pattDesign treatedMass)
  exact
    selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub))
      (fun sample =>
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw treatedDesign) sample : Real))
      (fun sample =>
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw controlDesign) sample : Real))
      (fun sample =>
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw pattDesign) sample : Real))
      treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      (fun sample => treatedValue (treatedPrognosticScore sample))
      (fun sample => controlValue (controlPrognosticScore sample))
      (fun sample =>
        scoreEffectCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample))
      (fun sample =>
        scoreTreatedMassCellValue
          (pattDoubleScore propensityScore pattPrognosticScore sample))
      (@PopulationSelectionDensityDesign.samplingMass Sample mSample
        selectedLaw populationLaw treatedDesign)
      (@PopulationSelectionDensityDesign.samplingMass Sample mSample
        selectedLaw populationLaw controlDesign)
      (@PopulationSelectionDensityDesign.samplingMass Sample mSample
        selectedLaw populationLaw pattDesign)
      htreatedTarget htreatedOne hcontrolTarget
      hcontrolOne hnumeratorRecovery hmassRecovery
      (ne_of_gt
        (@PopulationSelectionDensityDesign.sampling_pos Sample mSample
          selectedLaw populationLaw treatedDesign))
      (ne_of_gt
        (@PopulationSelectionDensityDesign.sampling_pos Sample mSample
          selectedLaw populationLaw controlDesign))
      (ne_of_gt
        (@PopulationSelectionDensityDesign.sampling_pos Sample mSample
          selectedLaw populationLaw pattDesign))
      hpopulationMass htreatedCond
      hcontrolCond hnumeratorCond hmassCond

/--
Raw selected-law survey-weighted PATE/PATT identification when the
Yang-Zhang/Antonelli route first transports observed WDSM targets to latent
or reference targets and proves correct-score conditional means for those
transported targets.  This avoids strengthening the route to a.e.
outcome-equals-score-version; only a.e. target transport plus conditional mean
identities for the transported targets are used.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore populationLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore populationLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore populationLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome populationLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome populationLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator populationLaw)
    (hmassOutcomeInt : Integrable treatedMass populationLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[populationLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[populationLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[populationLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[populationLaw] massTarget)
    (htreatedTargetCond :
      populationLaw[treatedTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      populationLaw[controlTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      populationLaw[effectTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      populationLaw[massTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw treatedDesign) sample : Real) *
          treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real)
          ∂selectedLaw) -
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw controlDesign) sample : Real) *
          controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real)
          ∂selectedLaw) =
        (∫ sample, treatedValue (treatedPrognosticScore sample)
          ∂populationLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂populationLaw) ∧
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw pattDesign) sample : Real) *
          treatedEffectNumerator sample ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedMass sample
          ∂selectedLaw) =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂populationLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂populationLaw) := by
  rcases
    primitiveCondExp_doubleScoreVersions_of_ae_targetTransport_correctScoreRoute
      (mSample := mSample) (sampleLaw := populationLaw)
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedTarget controlTarget
      effectTarget massTarget treatedValue controlValue scoreEffectCellValue
      scoreTreatedMassCellValue htreatedTransport hcontrolTransport
      hnumeratorTransport hmassTransport htreatedTargetCond
      hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
    ⟨⟨htreatedPrimitiveCond, hcontrolPrimitiveCond⟩,
      hnumeratorPrimitiveCond, hmassPrimitiveCond⟩
  exact
    selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_primitive_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hscoreCov hcovPrimitive hprimitiveSub treatedDesign controlDesign
      pattDesign propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedValue
      controlValue scoreEffectCellValue scoreTreatedMassCellValue
      hpopulationOne hpopulationMass hpropensityScore htreatedScore
      hcontrolScore hpattComponentScore htreatedOutcomeInt
      hcontrolOutcomeInt hnumeratorOutcomeInt hmassOutcomeInt
      htreatedPrimitiveCond hcontrolPrimitiveCond hnumeratorPrimitiveCond
      hmassPrimitiveCond

/--
Target-integrable raw selection-density version of
`selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute`.
The observed-target integrability hypotheses are recovered from integrability
of the transported latent/reference targets under the population law.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore populationLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore populationLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore populationLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw)
    (htreatedTargetInt : Integrable treatedTarget populationLaw)
    (hcontrolTargetInt : Integrable controlTarget populationLaw)
    (heffectTargetInt : Integrable effectTarget populationLaw)
    (hmassTargetInt : Integrable massTarget populationLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[populationLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[populationLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[populationLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[populationLaw] massTarget)
    (htreatedTargetCond :
      populationLaw[treatedTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      populationLaw[controlTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      populationLaw[effectTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      populationLaw[massTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw treatedDesign) sample : Real) *
          treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real)
          ∂selectedLaw) -
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw controlDesign) sample : Real) *
          controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real)
          ∂selectedLaw) =
        (∫ sample, treatedValue (treatedPrognosticScore sample)
          ∂populationLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂populationLaw) ∧
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw pattDesign) sample : Real) *
          treatedEffectNumerator sample ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedMass sample
          ∂selectedLaw) =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂populationLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂populationLaw) :=
  selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw) hscoreCov
    hcovPrimitive hprimitiveSub treatedDesign controlDesign pattDesign
    propensityScore treatedPrognosticScore controlPrognosticScore
    pattPrognosticScore treatedOutcome controlOutcome treatedEffectNumerator
    treatedMass treatedTarget controlTarget effectTarget massTarget
    treatedValue controlValue scoreEffectCellValue scoreTreatedMassCellValue
    hpopulationOne hpopulationMass hpropensityScore htreatedScore
    hcontrolScore hpattComponentScore
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := populationLaw) treatedOutcome
      treatedTarget htreatedTransport htreatedTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := populationLaw) controlOutcome
      controlTarget hcontrolTransport hcontrolTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := populationLaw)
      treatedEffectNumerator effectTarget hnumeratorTransport
      heffectTargetInt)
    (integrable_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := populationLaw) treatedMass
      massTarget hmassTransport hmassTargetInt)
    htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
    htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond hmassTargetCond

/--
Raw selection-density target-transport endpoint with latent/reference target
integrability and latent/reference PATT mass nonzero.  This is the theorem
level version of the target-mass bridge below.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (htargetMassNonzero :
      (∫ sample, massTarget sample ∂populationLaw) ≠ 0)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore populationLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore populationLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore populationLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw)
    (htreatedTargetInt : Integrable treatedTarget populationLaw)
    (hcontrolTargetInt : Integrable controlTarget populationLaw)
    (heffectTargetInt : Integrable effectTarget populationLaw)
    (hmassTargetInt : Integrable massTarget populationLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[populationLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[populationLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[populationLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[populationLaw] massTarget)
    (htreatedTargetCond :
      populationLaw[treatedTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      populationLaw[controlTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      populationLaw[effectTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      populationLaw[massTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw treatedDesign) sample : Real) *
          treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real)
          ∂selectedLaw) -
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw controlDesign) sample : Real) *
          controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real)
          ∂selectedLaw) =
        (∫ sample, treatedValue (treatedPrognosticScore sample)
          ∂populationLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂populationLaw) ∧
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw pattDesign) sample : Real) *
          treatedEffectNumerator sample ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedMass sample
          ∂selectedLaw) =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂populationLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂populationLaw) :=
  selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute_targetIntegrable
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hscoreCov hcovPrimitive hprimitiveSub treatedDesign controlDesign
    pattDesign propensityScore treatedPrognosticScore
    controlPrognosticScore pattPrognosticScore treatedOutcome controlOutcome
    treatedEffectNumerator treatedMass treatedTarget controlTarget effectTarget
    massTarget treatedValue controlValue scoreEffectCellValue
    scoreTreatedMassCellValue hpopulationOne
    (integral_ne_zero_of_ae_targetTransport
      (mSample := mSample) (sampleLaw := populationLaw) treatedMass
      massTarget hmassTransport htargetMassNonzero)
    hpropensityScore htreatedScore hcontrolScore hpattComponentScore
    htreatedTargetInt hcontrolTargetInt heffectTargetInt hmassTargetInt
    htreatedTransport hcontrolTransport hnumeratorTransport hmassTransport
    htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond hmassTargetCond

/--
Raw selection-density Yang-Zhang/Antonelli component-law target-transport
route.  Component score laws supported on finite partitions supply the finite
PATE/PATT double-score cover facts, while the selection-density design records
and target-transport correct-score route supply the raw survey-weighted
PATE/PATT score-space endpoint.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable_targetMass
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (htargetMassNonzero :
      (∫ sample, massTarget sample ∂populationLaw) ≠ 0)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore populationLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore populationLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore populationLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw populationLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        populationLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        populationLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw
        populationLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreatedTargetInt : Integrable treatedTarget populationLaw)
    (hcontrolTargetInt : Integrable controlTarget populationLaw)
    (heffectTargetInt : Integrable effectTarget populationLaw)
    (hmassTargetInt : Integrable massTarget populationLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[populationLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[populationLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[populationLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[populationLaw] massTarget)
    (htreatedTargetCond :
      populationLaw[treatedTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      populationLaw[controlTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      populationLaw[effectTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      populationLaw[massTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂populationLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂populationLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        (∫ sample,
            ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
              selectedLaw populationLaw treatedDesign) sample : Real) *
              treatedOutcome sample
            ∂selectedLaw) /
            (∫ sample,
              ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
                selectedLaw populationLaw treatedDesign) sample : Real)
              ∂selectedLaw) -
          (∫ sample,
            ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
              selectedLaw populationLaw controlDesign) sample : Real) *
              controlOutcome sample
            ∂selectedLaw) /
            (∫ sample,
              ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
                selectedLaw populationLaw controlDesign) sample : Real)
              ∂selectedLaw) =
            (∫ sample, treatedValue (treatedPrognosticScore sample)
              ∂populationLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂populationLaw) ∧
          (∫ sample,
            ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
              selectedLaw populationLaw pattDesign) sample : Real) *
              treatedEffectNumerator sample ∂selectedLaw) /
            (∫ sample,
              ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
                selectedLaw populationLaw pattDesign) sample : Real) *
                treatedMass sample
              ∂selectedLaw) =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂populationLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂populationLaw) := by
  constructor
  · exact
      ae_pateDoubleScoreCover_of_component_hasLaw
        (mSample := mSample) (sampleLaw := populationLaw)
        propensityCells treatedProgCells controlProgCells propensityScore
        treatedPrognosticScore controlPrognosticScore hpropensityLaw
        htreatedLaw hcontrolLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpropensityCoverLaw htreatedCoverLaw
        hcontrolCoverLaw
  · constructor
    · exact
        ae_pattDoubleScoreCover_of_component_hasLaw
          (mSample := mSample) (sampleLaw := populationLaw)
          propensityCells pattProgCells propensityScore pattPrognosticScore
          hpropensityLaw hpattLaw hpropensityCellsMeas hpattCellsMeas
          hpropensityCoverLaw hpattCoverLaw
    · exact
        selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass
          (mSample := mSample) (scoreSigma := scoreSigma)
          (selectedLaw := selectedLaw) (populationLaw := populationLaw)
          hscoreCov hcovPrimitive hprimitiveSub treatedDesign
          controlDesign pattDesign propensityScore treatedPrognosticScore
          controlPrognosticScore pattPrognosticScore treatedOutcome
          controlOutcome treatedEffectNumerator treatedMass treatedTarget
          controlTarget effectTarget massTarget treatedValue controlValue
          scoreEffectCellValue scoreTreatedMassCellValue hpopulationOne
          htargetMassNonzero hpropensityScore htreatedScore hcontrolScore
          hpattComponentScore htreatedTargetInt hcontrolTargetInt
          heffectTargetInt hmassTargetInt htreatedTransport
          hcontrolTransport hnumeratorTransport hmassTransport
          htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
          hmassTargetCond

/--
Raw selection-density target-transport route packaged as a
`SurveyWeightedScoreMeanBridge`.  The representation field is reduced to the
two population-level side conditions needed by the raw Hájek ratios because
the `PopulationSelectionDensityDesign` records already provide the
inverse-selection integral recovery.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectionDensityDesign_component_targetTransport_correctScoreRoute
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore populationLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore
        populationLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore
        populationLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw ∧
      Integrable treatedOutcome populationLaw ∧
      Integrable controlOutcome populationLaw ∧
      Integrable treatedEffectNumerator populationLaw ∧
      Integrable treatedMass populationLaw ∧
      treatedOutcome =ᵐ[populationLaw] treatedTarget ∧
      controlOutcome =ᵐ[populationLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[populationLaw] effectTarget ∧
      treatedMass =ᵐ[populationLaw] massTarget ∧
      populationLaw[treatedTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      populationLaw[controlTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      populationLaw[effectTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      populationLaw[massTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    (∫ _sample, (1 : Real) ∂populationLaw) = 1 ∧
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0
  score_space_identification :=
    (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw treatedDesign) sample : Real) *
          treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real)
          ∂selectedLaw) -
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw controlDesign) sample : Real) *
          controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real)
          ∂selectedLaw) =
        (∫ sample, treatedValue (treatedPrognosticScore sample)
          ∂populationLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂populationLaw) ∧
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw pattDesign) sample : Real) *
          treatedEffectNumerator sample ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedMass sample
          ∂selectedLaw) =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂populationLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂populationLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedOutcomeInt, hcontrolOutcomeInt, hnumeratorOutcomeInt,
        hmassOutcomeInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetCond,
        hcontrolTargetCond, hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with ⟨hpopulationOne, hpopulationMass⟩
    exact
      selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hscoreCov hcovPrimitive hprimitiveSub treatedDesign controlDesign
        pattDesign propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedTarget
        controlTarget effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hpopulationOne
        hpopulationMass hpropensityScore htreatedScore hcontrolScore
        hpattComponentScore htreatedOutcomeInt hcontrolOutcomeInt
        hnumeratorOutcomeInt hmassOutcomeInt htreatedTransport
        hcontrolTransport hnumeratorTransport hmassTransport
        htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
        hmassTargetCond
  }

/--
Target-integrable raw selection-density route packaged as a
`SurveyWeightedScoreMeanBridge`.  The balancing field states integrability of
the latent/reference targets; the bridge recovers observed-target integrability
from the target-transport equalities before applying the raw selection-density
endpoint.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectionDensityDesign_component_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore populationLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore
        populationLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore
        populationLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw ∧
      Integrable treatedTarget populationLaw ∧
      Integrable controlTarget populationLaw ∧
      Integrable effectTarget populationLaw ∧
      Integrable massTarget populationLaw ∧
      treatedOutcome =ᵐ[populationLaw] treatedTarget ∧
      controlOutcome =ᵐ[populationLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[populationLaw] effectTarget ∧
      treatedMass =ᵐ[populationLaw] massTarget ∧
      populationLaw[treatedTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      populationLaw[controlTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      populationLaw[effectTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      populationLaw[massTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    (∫ _sample, (1 : Real) ∂populationLaw) = 1 ∧
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0
  score_space_identification :=
    (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw treatedDesign) sample : Real) *
          treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real)
          ∂selectedLaw) -
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw controlDesign) sample : Real) *
          controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real)
          ∂selectedLaw) =
        (∫ sample, treatedValue (treatedPrognosticScore sample)
          ∂populationLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂populationLaw) ∧
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw pattDesign) sample : Real) *
          treatedEffectNumerator sample ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedMass sample
          ∂selectedLaw) =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂populationLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂populationLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedTargetInt, hcontrolTargetInt, heffectTargetInt,
        hmassTargetInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetCond,
        hcontrolTargetCond, hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with ⟨hpopulationOne, hpopulationMass⟩
    exact
      selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute_targetIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hscoreCov hcovPrimitive hprimitiveSub treatedDesign controlDesign
        pattDesign propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedTarget
        controlTarget effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hpopulationOne
        hpopulationMass hpropensityScore htreatedScore hcontrolScore
        hpattComponentScore htreatedTargetInt hcontrolTargetInt
        heffectTargetInt hmassTargetInt htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond
  }

/--
Target-integrable raw selection-density bridge with a latent/reference PATT
mass nonzero premise.  The observed-population PATT denominator nonzero side
condition is recovered by a.e. integral transport from `massTarget`.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectionDensityDesign_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore populationLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore
        populationLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore
        populationLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw ∧
      Integrable treatedTarget populationLaw ∧
      Integrable controlTarget populationLaw ∧
      Integrable effectTarget populationLaw ∧
      Integrable massTarget populationLaw ∧
      treatedOutcome =ᵐ[populationLaw] treatedTarget ∧
      controlOutcome =ᵐ[populationLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[populationLaw] effectTarget ∧
      treatedMass =ᵐ[populationLaw] massTarget ∧
      populationLaw[treatedTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      populationLaw[controlTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      populationLaw[effectTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      populationLaw[massTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    (∫ _sample, (1 : Real) ∂populationLaw) = 1 ∧
      (∫ sample, massTarget sample ∂populationLaw) ≠ 0
  score_space_identification :=
    (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw treatedDesign) sample : Real) *
          treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw treatedDesign) sample : Real)
          ∂selectedLaw) -
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw controlDesign) sample : Real) *
          controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw controlDesign) sample : Real)
          ∂selectedLaw) =
        (∫ sample, treatedValue (treatedPrognosticScore sample)
          ∂populationLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂populationLaw) ∧
      (∫ sample,
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw pattDesign) sample : Real) *
          treatedEffectNumerator sample ∂selectedLaw) /
        (∫ sample,
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw pattDesign) sample : Real) *
            treatedMass sample
          ∂selectedLaw) =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂populationLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂populationLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedTargetInt, hcontrolTargetInt, heffectTargetInt,
        hmassTargetInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetCond,
        hcontrolTargetCond, hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with ⟨hpopulationOne, htargetMassNonzero⟩
    exact
      selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hscoreCov hcovPrimitive hprimitiveSub treatedDesign controlDesign
        pattDesign propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedTarget
        controlTarget effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hpopulationOne
        htargetMassNonzero hpropensityScore htreatedScore hcontrolScore
        hpattComponentScore htreatedTargetInt hcontrolTargetInt
        heffectTargetInt hmassTargetInt htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond
  }

/--
Raw selection-density Yang-Zhang/Antonelli component-law target-transport
route packaged as a `SurveyWeightedScoreMeanBridge`.  Its balancing field
exposes component `HasLaw` finite support, component score measurability,
latent/reference target integrability, a.e. target transport, and primitive
latent/reference correct-score identities.  The bridge conclusion includes
the finite PATE/PATT double-score cover facts and the raw survey-weighted
score-space endpoint.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectionDensityDesign_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable_targetMass
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    {selectedLaw populationLaw : Measure[mSample] Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (populationLaw.trim hprimitiveSub)]
    [SigmaFinite (populationLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (populationLaw.trim
        (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore populationLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore
        populationLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore
        populationLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore populationLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw populationLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        populationLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        populationLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw
        populationLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      Integrable treatedTarget populationLaw ∧
      Integrable controlTarget populationLaw ∧
      Integrable effectTarget populationLaw ∧
      Integrable massTarget populationLaw ∧
      treatedOutcome =ᵐ[populationLaw] treatedTarget ∧
      controlOutcome =ᵐ[populationLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[populationLaw] effectTarget ∧
      treatedMass =ᵐ[populationLaw] massTarget ∧
      populationLaw[treatedTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      populationLaw[controlTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      populationLaw[effectTarget | primitiveSigma] =ᵐ[populationLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      populationLaw[massTarget | primitiveSigma] =ᵐ[populationLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    (∫ _sample, (1 : Real) ∂populationLaw) = 1 ∧
      (∫ sample, massTarget sample ∂populationLaw) ≠ 0
  score_space_identification :=
    (∀ᵐ sample ∂populationLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂populationLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        (∫ sample,
            ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
              selectedLaw populationLaw treatedDesign) sample : Real) *
              treatedOutcome sample
            ∂selectedLaw) /
            (∫ sample,
              ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
                selectedLaw populationLaw treatedDesign) sample : Real)
              ∂selectedLaw) -
          (∫ sample,
            ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
              selectedLaw populationLaw controlDesign) sample : Real) *
              controlOutcome sample
            ∂selectedLaw) /
            (∫ sample,
              ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
                selectedLaw populationLaw controlDesign) sample : Real)
              ∂selectedLaw) =
            (∫ sample, treatedValue (treatedPrognosticScore sample)
              ∂populationLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂populationLaw) ∧
          (∫ sample,
            ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
              selectedLaw populationLaw pattDesign) sample : Real) *
              treatedEffectNumerator sample ∂selectedLaw) /
            (∫ sample,
              ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
                selectedLaw populationLaw pattDesign) sample : Real) *
                treatedMass sample
              ∂selectedLaw) =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂populationLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂populationLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedTargetInt,
        hcontrolTargetInt, heffectTargetInt, hmassTargetInt,
        htreatedTransport, hcontrolTransport, hnumeratorTransport,
        hmassTransport, htreatedTargetCond, hcontrolTargetCond,
        hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with ⟨hpopulationOne, htargetMassNonzero⟩
    exact
      selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_selectionDensityDesign_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable_targetMass
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hscoreCov hcovPrimitive hprimitiveSub treatedDesign controlDesign
        pattDesign propensityCells treatedProgCells controlProgCells
        pattProgCells propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedTarget
        controlTarget effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hpopulationOne
        htargetMassNonzero hpropensityScore htreatedScore hcontrolScore
        hpattComponentScore hpropensityLaw htreatedLaw hcontrolLaw
        hpattLaw hpropensityCellsMeas htreatedCellsMeas hcontrolCellsMeas
        hpattCellsMeas hpropensityCoverLaw htreatedCoverLaw
        hcontrolCoverLaw hpattCoverLaw htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt
        htreatedTransport hcontrolTransport hnumeratorTransport
        hmassTransport htreatedTargetCond hcontrolTargetCond
        hnumeratorTargetCond hmassTargetCond
  }

/--
Component-score version of the covariate correct-score selected-Hájek route.
It derives the two joint double-score measurability premises from the
propensity and prognostic-score components, leaving only the covariate-level
conditional-mean identities as the paper-level probability interface.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (htreatedCov :
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolCov :
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorCov :
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov hcovSub pateRepr pattRepr
      htreatedSampling hcontrolSampling hpattSampling hpattMass
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass
      (by
        simpa [pateDoubleScore] using
          ((hpropensityScore.prodMk htreatedScore).prodMk hcontrolScore))
      (by
        simpa [pattDoubleScore] using
          hpropensityScore.prodMk hpattComponentScore)
      htreatedCov hcontrolCov hnumeratorCov hmassCov

/--
Concrete selected-Hájek PATE/PATT double-score identification packaged as a
`SurveyWeightedScoreMeanBridge` from covariate-level correct-score conditional
means.  Compared with the finite a.e. route below, this bridge exposes the
probability boundary as covariate conditional-mean identities and uses the
tower property to reach the double-score sigma-field.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw ∧
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw ∧
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpateScore, hpattScore, htreatedCov, hcontrolCov, hnumeratorCov,
        hmassCov⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_covariate_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub pateRepr pattRepr
        htreatedSampling hcontrolSampling hpattSampling hpattMass
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpateScore hpattScore htreatedCov
        hcontrolCov hnumeratorCov hmassCov
  }

/--
Component-score version of
`surveyWeightedScoreMeanBridge_of_selectedHajek_covariate_correctScoreRoute`.
The balancing input is now stated in terms of component score measurability plus
covariate-level correct-score conditional means; the joint double-score
measurability obligations are proved inside the bridge.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_component_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        htreatedCov, hcontrolCov, hnumeratorCov, hmassCov⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_covariate_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub pateRepr pattRepr
        htreatedSampling hcontrolSampling hpattSampling hpattMass
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore htreatedCov hcontrolCov
        hnumeratorCov hmassCov
  }

/--
Primitive Yang-Zhang/Antonelli-style component route with finite partition
support.  Component score laws supported on finite partitions provide the
PATE/PATT double-score finite-cover premises, while covariate-level
correct-score conditional means and selected-Hájek representation inputs
provide the score-space identification endpoint.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreatedCov :
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolCov :
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorCov :
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassCov :
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        pateRepr.selectedHajekPATE =
            (∫ sample,
              treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂sampleLaw) ∧
          pattRepr.selectedHajekPATT =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂sampleLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂sampleLaw) := by
  constructor
  · exact
      ae_pateDoubleScoreCover_of_component_hasLaw
        (mSample := mSample) (sampleLaw := sampleLaw)
        propensityCells treatedProgCells controlProgCells propensityScore
        treatedPrognosticScore controlPrognosticScore hpropensityLaw
        htreatedLaw hcontrolLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpropensityCoverLaw htreatedCoverLaw
        hcontrolCoverLaw
  · constructor
    · exact
        ae_pattDoubleScoreCover_of_component_hasLaw
          (mSample := mSample) (sampleLaw := sampleLaw)
          propensityCells pattProgCells propensityScore pattPrognosticScore
          hpropensityLaw hpattLaw hpropensityCellsMeas hpattCellsMeas
          hpropensityCoverLaw hpattCoverLaw
    · exact
        selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_covariate_correctScoreRoute
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscoreCov hcovSub pateRepr pattRepr
          htreatedSampling hcontrolSampling hpattSampling hpattMass
          propensityScore treatedPrognosticScore controlPrognosticScore
          pattPrognosticScore treatedOutcome controlOutcome
          treatedEffectNumerator treatedMass treatedValue controlValue
          scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
          hreprNumerator hreprMass hpropensityScore htreatedScore
          hcontrolScore hpattComponentScore htreatedCov hcontrolCov
          hnumeratorCov hmassCov

/--
Component-law Yang-Zhang/Antonelli target-transport route with finite
partition support.  Component score laws supported on finite partitions give
the PATE/PATT double-score finite-cover premises, while a.e. target transport
and latent/reference primitive correct-score identities supply the
covariate-level conditional means through the checked tower route.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        pateRepr.selectedHajekPATE =
            (∫ sample,
              treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂sampleLaw) ∧
          pattRepr.selectedHajekPATT =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂sampleLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂sampleLaw) := by
  rcases
    covariate_condExp_doubleScoreVersions_of_component_ae_targetTransport_correctScoreRoute_targetIntegrable
      (mSample := mSample) (sampleLaw := sampleLaw) hcovPrimitive
      hprimitiveSub propensityScore treatedPrognosticScore
      controlPrognosticScore pattPrognosticScore treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedTarget
      controlTarget effectTarget massTarget treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue
      (hpropensityScore.mono hscoreCov) (htreatedScore.mono hscoreCov)
      (hcontrolScore.mono hscoreCov) (hpattComponentScore.mono hscoreCov)
      htreatedTargetInt hcontrolTargetInt heffectTargetInt hmassTargetInt
      htreatedTransport hcontrolTransport hnumeratorTransport
      hmassTransport htreatedTargetCond hcontrolTargetCond
      hnumeratorTargetCond hmassTargetCond with
    ⟨hpateCov, hpattCov⟩
  rcases hpateCov with ⟨htreatedCov, hcontrolCov⟩
  rcases hpattCov with ⟨hnumeratorCov, hmassCov⟩
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_covariate_correctScoreRoute
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hscoreCov
      (hcovPrimitive.trans hprimitiveSub) pateRepr pattRepr
      htreatedSampling hcontrolSampling hpattSampling hpattMass
      propensityCells treatedProgCells controlProgCells pattProgCells
      propensityScore treatedPrognosticScore controlPrognosticScore
      pattPrognosticScore treatedOutcome controlOutcome
      treatedEffectNumerator treatedMass treatedValue controlValue
      scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
      hreprNumerator hreprMass hpropensityScore htreatedScore
      hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
      hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
      hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
      htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw htreatedCov
      hcontrolCov hnumeratorCov hmassCov

/--
Component-law Yang-Zhang/Antonelli selected-Hájek target-transport route with
latent/reference target representation.  This strengthens the previous
component-law target-transport route by moving the PATE/PATT representation
equalities and PATT mass nonzero condition to the latent/reference targets;
observed representation facts are recovered downstream by a.e. integral
transport.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hpropensityScore :
      AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw)
    (htreatedScore :
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw)
    (hcontrolScore :
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw)
    (hpattComponentScore :
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw)
    (hpropensityLaw :
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw)
    (htreatedLaw :
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw)
    (hcontrolLaw :
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw)
    (hpattLaw :
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw)
    (hpropensityCellsMeas :
      MeasurableSet (propensityCells : Set PropensityCell))
    (htreatedCellsMeas :
      MeasurableSet (treatedProgCells : Set TreatedProgCell))
    (hcontrolCellsMeas :
      MeasurableSet (controlProgCells : Set ControlProgCell))
    (hpattCellsMeas :
      MeasurableSet (pattProgCells : Set PATTProgCell))
    (hpropensityCoverLaw :
      ∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell))
    (htreatedCoverLaw :
      ∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell))
    (hcontrolCoverLaw :
      ∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell))
    (hpattCoverLaw :
      ∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell))
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTargetCond :
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrolTargetCond :
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumeratorTargetCond :
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmassTargetCond :
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    (∀ᵐ sample ∂sampleLaw,
      pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
        (((propensityCells.product treatedProgCells).product
          controlProgCells) : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell))) ∧
      (∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (propensityCells.product pattProgCells :
            Set (PropensityCell × PATTProgCell))) ∧
        pateRepr.selectedHajekPATE =
            (∫ sample,
              treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
              (∫ sample, controlValue (controlPrognosticScore sample)
                ∂sampleLaw) ∧
          pattRepr.selectedHajekPATT =
            (∫ sample,
              scoreEffectCellValue
                (pattDoubleScore propensityScore pattPrognosticScore sample)
              ∂sampleLaw) /
              (∫ sample,
                scoreTreatedMassCellValue
                  (pattDoubleScore propensityScore pattPrognosticScore sample)
                ∂sampleLaw) := by
  constructor
  · exact
      ae_pateDoubleScoreCover_of_component_hasLaw
        (mSample := mSample) (sampleLaw := sampleLaw)
        propensityCells treatedProgCells controlProgCells propensityScore
        treatedPrognosticScore controlPrognosticScore hpropensityLaw
        htreatedLaw hcontrolLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpropensityCoverLaw htreatedCoverLaw
        hcontrolCoverLaw
  · constructor
    · exact
        ae_pattDoubleScoreCover_of_component_hasLaw
          (mSample := mSample) (sampleLaw := sampleLaw)
          propensityCells pattProgCells propensityScore pattPrognosticScore
          hpropensityLaw hpattLaw hpropensityCellsMeas hpattCellsMeas
          hpropensityCoverLaw hpattCoverLaw
    · exact
        selectedHajekPATE_PATT_eq_scorePATE_PATT_of_component_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
          pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
          propensityScore treatedPrognosticScore controlPrognosticScore
          pattPrognosticScore treatedOutcome controlOutcome
          treatedEffectNumerator treatedMass treatedTarget controlTarget
          effectTarget massTarget treatedValue controlValue
          scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
          hreprNumerator hreprMass hpropensityScore htreatedScore
          hcontrolScore hpattComponentScore htreatedTargetInt
          hcontrolTargetInt heffectTargetInt hmassTargetInt
          hmassTargetNonzero htreatedTransport hcontrolTransport
          hnumeratorTransport hmassTransport htreatedTargetCond
          hcontrolTargetCond hnumeratorTargetCond hmassTargetCond

/--
Component-law Yang-Zhang/Antonelli covariate-correct route packaged as a
`SurveyWeightedScoreMeanBridge`.  This is the conditional-mean analogue of the
finite-a.e. component-law bridge below: component `HasLaw` support supplies
finite score coverage, while covariate correct-score identities supply the
selected-Hájek score-space endpoint through the tower-property route.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_covariate_correctScoreRoute
    {PATTProgCell : Type*} {covariateSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovSub : covariateSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcovSub)]
    [SigmaFinite (sampleLaw.trim (hscoreCov.trans hcovSub))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      sampleLaw[treatedOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlOutcome | covariateSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[treatedEffectNumerator | covariateSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[treatedMass | covariateSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedCov, hcontrolCov,
        hnumeratorCov, hmassCov⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_covariate_correctScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovSub pateRepr pattRepr
        htreatedSampling hcontrolSampling hpattSampling hpattMass
        propensityCells treatedProgCells controlProgCells pattProgCells
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
        hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
        htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw htreatedCov
        hcontrolCov hnumeratorCov hmassCov with
      ⟨_hpateCover, _hpattCover, hendpoint⟩
    exact hendpoint
  }

/--
Component-law Yang-Zhang/Antonelli target-transport route packaged as a
`SurveyWeightedScoreMeanBridge`.  Compared with the covariate-correct bridge,
the balancing field no longer assumes the four covariate conditional means
directly; it derives them from latent/reference target integrability, a.e.
target transport, and primitive latent/reference correct-score identities.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedTargetInt,
        hcontrolTargetInt, heffectTargetInt, hmassTargetInt,
        htreatedTransport, hcontrolTransport, hnumeratorTransport,
        hmassTransport, htreatedTargetCond, hcontrolTargetCond,
        hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        hpattMass propensityCells treatedProgCells controlProgCells
        pattProgCells propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedTarget
        controlTarget effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
        hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
        htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt htreatedTransport
        hcontrolTransport hnumeratorTransport hmassTransport
        htreatedTargetCond hcontrolTargetCond hnumeratorTargetCond
        hmassTargetCond with
      ⟨_hpateCover, _hpattCover, hendpoint⟩
    exact hendpoint
  }

/--
Component-law Yang-Zhang/Antonelli selected-Hájek target-transport route
packaged with latent/reference target representation.  The representation
field is stated on the latent/reference targets and the balancing field
contains the latent/reference PATT mass nonzero condition; observed
representation equalities are recovered inside the bridge by a.e. integral
transport through the target-representation endpoint.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation
    {PATTProgCell : Type*}
    {covariateSigma primitiveSigma : MeasurableSpace Sample}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    (hscoreCov : scoreSigma ≤ covariateSigma)
    (hcovPrimitive : covariateSigma ≤ primitiveSigma)
    (hprimitiveSub : primitiveSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hprimitiveSub)]
    [SigmaFinite (sampleLaw.trim (hcovPrimitive.trans hprimitiveSub))]
    [SigmaFinite
      (sampleLaw.trim (hscoreCov.trans (hcovPrimitive.trans hprimitiveSub)))]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedTarget controlTarget effectTarget massTarget : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      sampleLaw[treatedTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      sampleLaw[controlTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      sampleLaw[effectTarget | primitiveSigma] =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      sampleLaw[massTarget | primitiveSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreatedTargetInt,
        hcontrolTargetInt, heffectTargetInt, hmassTargetInt,
        hmassTargetNonzero, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTargetCond,
        hcontrolTargetCond, hnumeratorTargetCond, hmassTargetCond⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hreprT, hreprC,
        hreprNumerator, hreprMass⟩
    rcases
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_yangZhang_component_hasLaw_targetTransport_correctScoreRoute_targetIntegrable_targetMass_targetRepresentation
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hscoreCov hcovPrimitive hprimitiveSub
        pateRepr pattRepr htreatedSampling hcontrolSampling hpattSampling
        propensityCells treatedProgCells controlProgCells pattProgCells
        propensityScore treatedPrognosticScore controlPrognosticScore
        pattPrognosticScore treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedValue controlValue
        scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
        hreprNumerator hreprMass hpropensityScore htreatedScore
        hcontrolScore hpattComponentScore hpropensityLaw htreatedLaw
        hcontrolLaw hpattLaw hpropensityCellsMeas htreatedCellsMeas
        hcontrolCellsMeas hpattCellsMeas hpropensityCoverLaw
        htreatedCoverLaw hcontrolCoverLaw hpattCoverLaw htreatedTargetInt
        hcontrolTargetInt heffectTargetInt hmassTargetInt
        hmassTargetNonzero htreatedTransport hcontrolTransport
        hnumeratorTransport hmassTransport htreatedTargetCond
        hcontrolTargetCond hnumeratorTargetCond hmassTargetCond with
      ⟨_hpateCover, _hpattCover, hendpoint⟩
    exact hendpoint
  }

/--
Concrete selected-Hájek PATE/PATT double-score identification packaged as the
abstract survey-weighted score-mean bridge.

The bridge's balancing field is the finite Yang-Zhang-route score-version
input that feeds the conditional-expectation adapters above.  Its representation
field is the selected-Hájek nonzero-mass and population-representation input.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_ae_doubleScoreVersions_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    PATEFiniteDoubleScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) pateCells propensityScore
        treatedPrognosticScore controlPrognosticScore treatedOutcome
        controlOutcome treatedValue controlValue ∧
      PATTFiniteDoubleScoreRoute
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) pattCells propensityScore
        pattPrognosticScore treatedEffectNumerator treatedMass
        scoreEffectCellValue scoreTreatedMassCellValue
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases
      ae_doubleScoreVersions_of_yangZhang_route_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) pateCells pattCells propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedValue controlValue scoreEffectCellValue
        scoreTreatedMassCellValue hbalance with
      ⟨hpateScore, hpateCover, hpattScore, hpattCover, htreated, hcontrol,
        hnumerator, hmass⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      condExp_doubleScoreVersions_of_ae_finiteScoreVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateCells pattCells propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedValue controlValue scoreEffectCellValue
        scoreTreatedMassCellValue hpateScore hpateCover hpattScore hpattCover
        htreated hcontrol hnumerator hmass with
      ⟨hpateCond, hpattCond⟩
    rcases hpateCond with ⟨htreatedCond, hcontrolCond⟩
    rcases hpattCond with ⟨hnumeratorCond, hmassCond⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling hpattMass propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedValue controlValue scoreEffectCellValue
        scoreTreatedMassCellValue hreprT hreprC hreprNumerator hreprMass
        htreatedCond hcontrolCond hnumeratorCond hmassCond
  }

/--
Component-law Yang-Zhang/Antonelli finite-route bridge.  This is the
`SurveyWeightedScoreMeanBridge` version of
`ae_doubleScoreVersions_of_yangZhang_component_hasLaw_route_finset_abs_sum_bound`:
component score measurability, component `HasLaw` support on finite
partitions, and explicit finite score-version equalities are packaged directly
into the selected-Hájek score-space endpoint.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_yangZhang_component_hasLaw_route_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [MeasurableSpace PropensityCell] [MeasurableSpace TreatedProgCell]
    [MeasurableSpace ControlProgCell] [MeasurableSpace PATTProgCell]
    [TopologicalSpace PropensityCell] [TopologicalSpace TreatedProgCell]
    [TopologicalSpace ControlProgCell] [TopologicalSpace PATTProgCell]
    [DiscreteTopology PropensityCell] [DiscreteTopology TreatedProgCell]
    [DiscreteTopology ControlProgCell] [DiscreteTopology PATTProgCell]
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityCells : Finset PropensityCell)
    (treatedProgCells : Finset TreatedProgCell)
    (controlProgCells : Finset ControlProgCell)
    (pattProgCells : Finset PATTProgCell)
    {propensityLaw : Measure PropensityCell}
    {treatedProgLaw : Measure TreatedProgCell}
    {controlProgLaw : Measure ControlProgCell}
    {pattProgLaw : Measure PATTProgCell}
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    AEStronglyMeasurable[scoreSigma] propensityScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] treatedPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlPrognosticScore sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] pattPrognosticScore sampleLaw ∧
      ProbabilityTheory.HasLaw propensityScore propensityLaw sampleLaw ∧
      ProbabilityTheory.HasLaw treatedPrognosticScore treatedProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw controlPrognosticScore controlProgLaw
        sampleLaw ∧
      ProbabilityTheory.HasLaw pattPrognosticScore pattProgLaw sampleLaw ∧
      MeasurableSet (propensityCells : Set PropensityCell) ∧
      MeasurableSet (treatedProgCells : Set TreatedProgCell) ∧
      MeasurableSet (controlProgCells : Set ControlProgCell) ∧
      MeasurableSet (pattProgCells : Set PATTProgCell) ∧
      (∀ᵐ cell ∂propensityLaw,
        cell ∈ (propensityCells : Set PropensityCell)) ∧
      (∀ᵐ cell ∂treatedProgLaw,
        cell ∈ (treatedProgCells : Set TreatedProgCell)) ∧
      (∀ᵐ cell ∂controlProgLaw,
        cell ∈ (controlProgCells : Set ControlProgCell)) ∧
      (∀ᵐ cell ∂pattProgLaw,
        cell ∈ (pattProgCells : Set PATTProgCell)) ∧
      treatedOutcome =ᵐ[sampleLaw]
        (fun sample => treatedValue (treatedPrognosticScore sample)) ∧
      controlOutcome =ᵐ[sampleLaw]
        (fun sample => controlValue (controlPrognosticScore sample)) ∧
      treatedEffectNumerator =ᵐ[sampleLaw]
        (fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) ∧
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      pattRepr.population_treated_mass ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨hpropensityScore, htreatedScore, hcontrolScore, hpattComponentScore,
        hpropensityLaw, htreatedLaw, hcontrolLaw, hpattLaw,
        hpropensityCellsMeas, htreatedCellsMeas, hcontrolCellsMeas,
        hpattCellsMeas, hpropensityCoverLaw, htreatedCoverLaw,
        hcontrolCoverLaw, hpattCoverLaw, htreated, hcontrol, hnumerator,
        hmass⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling, hpattMass,
        hreprT, hreprC, hreprNumerator, hreprMass⟩
    rcases
      ae_doubleScoreVersions_of_yangZhang_component_hasLaw_route_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) propensityCells treatedProgCells
        controlProgCells pattProgCells propensityScore treatedPrognosticScore
        controlPrognosticScore pattPrognosticScore treatedOutcome
        controlOutcome treatedEffectNumerator treatedMass treatedValue
        controlValue scoreEffectCellValue scoreTreatedMassCellValue
        hpropensityScore htreatedScore hcontrolScore hpattComponentScore
        hpropensityLaw htreatedLaw hcontrolLaw hpattLaw
        hpropensityCellsMeas htreatedCellsMeas hcontrolCellsMeas
        hpattCellsMeas hpropensityCoverLaw htreatedCoverLaw
        hcontrolCoverLaw hpattCoverLaw htreated hcontrol hnumerator hmass with
      ⟨hpateScore, hpateCover, hpattScore, hpattCover, htreatedScoreVersion,
        hcontrolScoreVersion, hnumeratorScoreVersion, hmassScoreVersion⟩
    rcases
      condExp_doubleScoreVersions_of_ae_finiteScoreVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub
        ((propensityCells.product treatedProgCells).product controlProgCells)
        (propensityCells.product pattProgCells) propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedValue controlValue scoreEffectCellValue
        scoreTreatedMassCellValue hpateScore hpateCover hpattScore hpattCover
        htreatedScoreVersion hcontrolScoreVersion hnumeratorScoreVersion
        hmassScoreVersion with
      ⟨hpateCond, hpattCond⟩
    rcases hpateCond with ⟨htreatedCond, hcontrolCond⟩
    rcases hpattCond with ⟨hnumeratorCond, hmassCond⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_doubleScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling hpattMass propensityScore
        treatedPrognosticScore controlPrognosticScore pattPrognosticScore
        treatedOutcome controlOutcome treatedEffectNumerator treatedMass
        treatedValue controlValue scoreEffectCellValue
        scoreTreatedMassCellValue hreprT hreprC hreprNumerator hreprMass
        htreatedCond hcontrolCond hnumeratorCond hmassCond
  }

/--
PATE population identification from almost-everywhere PATE double-score
versions.  The finite double-score coverage assumption supplies the
score-version side conditions.
-/
theorem populationPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_finset_abs_sum_bound
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (cells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    repr.populationPATE =
      (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
        (∫ sample, controlValue (controlPrognosticScore sample) ∂sampleLaw) := by
  simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore,
    controlCellValueOnPATEDoubleScore] using
    (populationPATE_eq_scorePATE_of_ae_scoreCellVersions_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr cells
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      treatedOutcome controlOutcome
      (treatedCellValueOnPATEDoubleScore treatedValue)
      (controlCellValueOnPATEDoubleScore controlValue)
      hreprT hreprC hscore hcover
      (by
        simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
          htreated)
      (by
        simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
          hcontrol))

/--
PATT population identification from almost-everywhere PATT double-score
versions.
-/
theorem populationPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (cells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (controlPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore controlPrognosticScore) sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore controlPrognosticScore sample ∈
          (cells : Set (PropensityCell × PATTProgCell)))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)) :
    repr.populationPATT =
      (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) /
        (∫ sample,
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) :=
  populationPATT_eq_scorePATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr cells (pattDoubleScore propensityScore controlPrognosticScore)
    treatedEffectNumerator treatedMass scoreEffectCellValue
    scoreTreatedMassCellValue hreprNumerator hreprMass hscore hcover
    hnumerator hmass

/--
Paired population PATE/PATT identification from a.e. WDSM double-score
versions with separate finite covers for the PATE and PATT double scores.
-/
theorem populationPATE_PATT_eq_scorePATE_PATT_of_ae_doubleScoreVersions_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpateCover :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (pateCells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (hpattCover :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (pattCells : Set (PropensityCell × PATTProgCell)))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.populationPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.populationPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  constructor
  · exact
      populationPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pateCells propensityScore
        treatedPrognosticScore controlPrognosticScore treatedOutcome
        controlOutcome treatedValue controlValue hreprT hreprC hpateScore
        hpateCover htreated hcontrol
  · exact
      populationPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr pattCells propensityScore
        pattPrognosticScore treatedEffectNumerator treatedMass
        scoreEffectCellValue scoreTreatedMassCellValue hreprNumerator
        hreprMass hpattScore hpattCover hnumerator hmass

/--
Selected-sample Hájek PATE identification from almost-everywhere PATE
double-score versions.  The finite double-score coverage assumption supplies
the score-version side conditions.
-/
theorem selectedHajekPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_finset_abs_sum_bound
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (cells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    repr.selectedHajekPATE =
      (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
        (∫ sample, controlValue (controlPrognosticScore sample) ∂sampleLaw) := by
  simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore,
    controlCellValueOnPATEDoubleScore] using
    (selectedHajekPATE_eq_scorePATE_of_ae_scoreCellVersions_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr htreatedSampling hcontrolSampling
      cells
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      treatedOutcome controlOutcome
      (treatedCellValueOnPATEDoubleScore treatedValue)
      (controlCellValueOnPATEDoubleScore controlValue)
      hreprT hreprC hscore hcover
      (by
        simpa [pateDoubleScore, treatedCellValueOnPATEDoubleScore] using
          htreated)
      (by
        simpa [pateDoubleScore, controlCellValueOnPATEDoubleScore] using
          hcontrol))

/--
Selected-sample Hájek PATT identification from almost-everywhere PATT
double-score versions.
-/
theorem selectedHajekPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreatedMass : repr.population_treated_mass ≠ 0)
    (cells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (controlPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore controlPrognosticScore) sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore controlPrognosticScore sample ∈
          (cells : Set (PropensityCell × PATTProgCell)))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)) :
    repr.selectedHajekPATT =
      (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) /
        (∫ sample,
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) :=
  selectedHajekPATT_eq_scorePATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr hsampling htreatedMass cells
    (pattDoubleScore propensityScore controlPrognosticScore)
    treatedEffectNumerator treatedMass scoreEffectCellValue
    scoreTreatedMassCellValue hreprNumerator hreprMass hscore hcover
    hnumerator hmass

/--
Paired selected-sample Hájek PATE/PATT identification from a.e. WDSM
double-score versions with separate finite covers for the PATE and PATT double
scores.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_doubleScoreVersions_finset_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpateCover :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore sample ∈
          (pateCells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (hpattCover :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore propensityScore pattPrognosticScore sample ∈
          (pattCells : Set (PropensityCell × PATTProgCell)))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) := by
  constructor
  · exact
      selectedHajekPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr htreatedSampling
        hcontrolSampling pateCells propensityScore treatedPrognosticScore
        controlPrognosticScore treatedOutcome controlOutcome treatedValue
        controlValue hreprT hreprC hpateScore hpateCover htreated hcontrol
  · exact
      selectedHajekPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr hpattSampling hpattMass
        pattCells propensityScore pattPrognosticScore treatedEffectNumerator
        treatedMass scoreEffectCellValue scoreTreatedMassCellValue
        hreprNumerator hreprMass hpattScore hpattCover hnumerator hmass

/--
Finite-type PATE double-score population identification from a.e. score
versions.
-/
theorem populationPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_fintype_abs_sum_bound
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    repr.populationPATE =
      (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
        (∫ sample, controlValue (controlPrognosticScore sample) ∂sampleLaw) :=
  populationPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub repr
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedOutcome controlOutcome treatedValue controlValue hreprT hreprC
    hscore (Filter.Eventually.of_forall (fun sample => by simp))
    htreated hcontrol

/--
Finite-type PATT double-score population identification from a.e. score
versions.
-/
theorem populationPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_fintype_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    [Fintype (PropensityCell × PATTProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (controlPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore controlPrognosticScore) sampleLaw)
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)) :
    repr.populationPATT =
      (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) /
        (∫ sample,
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) :=
  populationPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub repr
    (Finset.univ : Finset (PropensityCell × PATTProgCell))
    propensityScore controlPrognosticScore treatedEffectNumerator
    treatedMass scoreEffectCellValue scoreTreatedMassCellValue
    hreprNumerator hreprMass hscore
    (Filter.Eventually.of_forall (fun sample => by simp)) hnumerator hmass

/--
Finite-type paired population PATE/PATT double-score identification from a.e.
score versions.
-/
theorem populationPATE_PATT_eq_scorePATE_PATT_of_ae_doubleScoreVersions_fintype_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [Fintype (PropensityCell × PATTProgCell)]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.populationPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.populationPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) :=
  populationPATE_PATT_eq_scorePATE_PATT_of_ae_doubleScoreVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub pateRepr pattRepr
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (Finset.univ : Finset (PropensityCell × PATTProgCell))
    propensityScore treatedPrognosticScore controlPrognosticScore
    pattPrognosticScore treatedOutcome controlOutcome treatedEffectNumerator
    treatedMass treatedValue controlValue scoreEffectCellValue
    scoreTreatedMassCellValue hreprT hreprC hreprNumerator hreprMass
    hpateScore (Filter.Eventually.of_forall (fun sample => by simp))
    hpattScore (Filter.Eventually.of_forall (fun sample => by simp))
    htreated hcontrol hnumerator hmass

/--
Finite-type selected Hájek PATE double-score identification from a.e. score
versions.
-/
theorem selectedHajekPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_fintype_abs_sum_bound
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample)) :
    repr.selectedHajekPATE =
      (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
        (∫ sample, controlValue (controlPrognosticScore sample) ∂sampleLaw) :=
  selectedHajekPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub repr htreatedSampling hcontrolSampling
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedOutcome controlOutcome treatedValue controlValue hreprT hreprC
    hscore (Filter.Eventually.of_forall (fun sample => by simp))
    htreated hcontrol

/--
Finite-type selected Hájek PATT double-score identification from a.e. score
versions.
-/
theorem selectedHajekPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_fintype_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    [Fintype (PropensityCell × PATTProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreatedMass : repr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (controlPrognosticScore : Sample -> PATTProgCell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hscore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore controlPrognosticScore) sampleLaw)
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)) :
    repr.selectedHajekPATT =
      (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) /
        (∫ sample,
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore controlPrognosticScore sample)
          ∂sampleLaw) :=
  selectedHajekPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub repr hsampling htreatedMass
    (Finset.univ : Finset (PropensityCell × PATTProgCell))
    propensityScore controlPrognosticScore treatedEffectNumerator
    treatedMass scoreEffectCellValue scoreTreatedMassCellValue
    hreprNumerator hreprMass hscore
    (Filter.Eventually.of_forall (fun sample => by simp)) hnumerator hmass

/--
Finite-type paired selected Hájek PATE/PATT double-score identification from
a.e. score versions.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_doubleScoreVersions_fintype_abs_sum_bound
    {PATTProgCell : Type*}
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [Fintype (PropensityCell × PATTProgCell)]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (propensityScore : Sample -> PropensityCell)
    (treatedPrognosticScore : Sample -> TreatedProgCell)
    (controlPrognosticScore : Sample -> ControlProgCell)
    (pattPrognosticScore : Sample -> PATTProgCell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hpateScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) sampleLaw)
    (hpattScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore propensityScore pattPrognosticScore) sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedValue (treatedPrognosticScore sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlValue (controlPrognosticScore sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedValue (treatedPrognosticScore sample) ∂sampleLaw) -
          (∫ sample, controlValue (controlPrognosticScore sample)
            ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
          scoreEffectCellValue
            (pattDoubleScore propensityScore pattPrognosticScore sample)
          ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore propensityScore pattPrognosticScore sample)
            ∂sampleLaw) :=
  selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_doubleScoreVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
    hcontrolSampling hpattSampling hpattMass
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (Finset.univ : Finset (PropensityCell × PATTProgCell))
    propensityScore treatedPrognosticScore controlPrognosticScore
    pattPrognosticScore treatedOutcome controlOutcome treatedEffectNumerator
    treatedMass treatedValue controlValue scoreEffectCellValue
    scoreTreatedMassCellValue hreprT hreprC hreprNumerator hreprMass
    hpateScore (Filter.Eventually.of_forall (fun sample => by simp))
    hpattScore (Filter.Eventually.of_forall (fun sample => by simp))
    htreated hcontrol hnumerator hmass

end WDSM
end Matching
end StatInference
