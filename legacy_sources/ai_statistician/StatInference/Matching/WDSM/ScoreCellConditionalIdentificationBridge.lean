import StatInference.Matching.WDSM.ScoreCellScoreVersionBridge
import StatInference.Matching.WDSM.SurveyConditionalIdentificationBridge

/-!
# Score-cell conditional identification bridge

This module specializes the population and selected-sample identification
bridges to score versions that are finite score-cell loadings.  The
conditional-mean assumptions are stated directly as `cellValue (score sample)`,
which is the form used by WDSM finite score construction.  A separate
almost-everywhere route discharges the score-version measurability and
integrability side conditions from finite score-cell coverage.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Sample Cell : Type*}
variable [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
PATE population identification when the treated/control conditional mean
versions are finite score-cell functions.
-/
theorem populationPATE_eq_scorePATE_of_condExp_scoreCellVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample)) :
    repr.populationPATE =
      (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
        (∫ sample, controlCellValue (score sample) ∂sampleLaw) :=
  populationPATE_eq_scorePATE_of_condExp_scoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr treatedOutcome controlOutcome
    (fun sample => treatedCellValue (score sample))
    (fun sample => controlCellValue (score sample))
    hreprT hreprC htreated hcontrol

/--
Selected-sample Hájek PATE identification with finite score-cell conditional
mean versions.
-/
theorem selectedHajekPATE_eq_scorePATE_of_condExp_scoreCellVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample)) :
    repr.selectedHajekPATE =
      (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
        (∫ sample, controlCellValue (score sample) ∂sampleLaw) :=
  selectedHajekPATE_eq_scorePATE_of_condExp_scoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr htreatedSampling hcontrolSampling treatedOutcome controlOutcome
    (fun sample => treatedCellValue (score sample))
    (fun sample => controlCellValue (score sample))
    hreprT hreprC htreated hcontrol

/--
PATT population identification when the numerator and denominator conditional
mean versions are finite score-cell functions.
-/
theorem populationPATT_eq_scorePATT_of_condExp_scoreCellVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (score : Sample -> Cell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue : Cell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    repr.populationPATT =
      (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
        (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) :=
  populationPATT_eq_scorePATT_of_condExp_scoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr treatedEffectNumerator treatedMass
    (fun sample => scoreEffectCellValue (score sample))
    (fun sample => scoreTreatedMassCellValue (score sample))
    hreprNumerator hreprMass hnumerator hmass

/--
Selected-sample Hájek PATT identification with finite score-cell conditional
mean versions.
-/
theorem selectedHajekPATT_eq_scorePATT_of_condExp_scoreCellVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreatedMass : repr.population_treated_mass ≠ 0)
    (score : Sample -> Cell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue : Cell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    repr.selectedHajekPATT =
      (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
        (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) :=
  selectedHajekPATT_eq_scorePATT_of_condExp_scoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr hsampling htreatedMass treatedEffectNumerator treatedMass
    (fun sample => scoreEffectCellValue (score sample))
    (fun sample => scoreTreatedMassCellValue (score sample))
    hreprNumerator hreprMass hnumerator hmass

/--
Paired population PATE/PATT identification when all score versions are finite
score-cell functions.
-/
theorem populationPATE_PATT_eq_scorePATE_PATT_of_condExp_scoreCellVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedCellValue controlCellValue scoreEffectCellValue
      scoreTreatedMassCellValue : Cell -> Real)
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
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample))
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    pateRepr.populationPATE =
        (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
          (∫ sample, controlCellValue (score sample) ∂sampleLaw) ∧
      pattRepr.populationPATT =
        (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
          (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) := by
  constructor
  · exact
      populationPATE_eq_scorePATE_of_condExp_scoreCellVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr score treatedOutcome
        controlOutcome treatedCellValue controlCellValue hreprT hreprC
        htreated hcontrol
  · exact
      populationPATT_eq_scorePATT_of_condExp_scoreCellVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr score treatedEffectNumerator
        treatedMass scoreEffectCellValue scoreTreatedMassCellValue
        hreprNumerator hreprMass hnumerator hmass

/--
Paired selected-sample Hájek PATE/PATT identification when all score versions
are finite score-cell functions.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_scoreCellVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedCellValue controlCellValue scoreEffectCellValue
      scoreTreatedMassCellValue : Cell -> Real)
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
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample))
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
          (∫ sample, controlCellValue (score sample) ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
          (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) := by
  constructor
  · exact
      selectedHajekPATE_eq_scorePATE_of_condExp_scoreCellVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr htreatedSampling
        hcontrolSampling score treatedOutcome controlOutcome treatedCellValue
        controlCellValue hreprT hreprC htreated hcontrol
  · exact
      selectedHajekPATT_eq_scorePATT_of_condExp_scoreCellVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr hpattSampling hpattMass score
        treatedEffectNumerator treatedMass scoreEffectCellValue
        scoreTreatedMassCellValue hreprNumerator hreprMass hnumerator hmass

/--
PATE population identification from almost-everywhere finite score-cell score
versions.  Finite score-cell coverage supplies score-version measurability and
integrability.
-/
theorem populationPATE_eq_scorePATE_of_ae_scoreCellVersions_finset_abs_sum_bound
    [DecidableEq Cell] [TopologicalSpace Cell] [DiscreteTopology Cell]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample)) :
    repr.populationPATE =
      (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
        (∫ sample, controlCellValue (score sample) ∂sampleLaw) :=
  populationPATE_eq_scorePATE_of_ae_scoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr treatedOutcome controlOutcome
    (fun sample => treatedCellValue (score sample))
    (fun sample => controlCellValue (score sample))
    hreprT hreprC htreated hcontrol
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score treatedCellValue hscore)
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score controlCellValue hscore)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score treatedCellValue hscore
      hcover)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score controlCellValue hscore
      hcover)

/--
Selected-sample Hájek PATE identification from almost-everywhere finite
score-cell score versions.
-/
theorem selectedHajekPATE_eq_scorePATE_of_ae_scoreCellVersions_finset_abs_sum_bound
    [DecidableEq Cell] [TopologicalSpace Cell] [DiscreteTopology Cell]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample)) :
    repr.selectedHajekPATE =
      (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
        (∫ sample, controlCellValue (score sample) ∂sampleLaw) :=
  selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr htreatedSampling hcontrolSampling treatedOutcome controlOutcome
    (fun sample => treatedCellValue (score sample))
    (fun sample => controlCellValue (score sample))
    hreprT hreprC htreated hcontrol
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score treatedCellValue hscore)
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score controlCellValue hscore)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score treatedCellValue hscore
      hcover)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score controlCellValue hscore
      hcover)

/--
PATT population identification from almost-everywhere finite score-cell
versions for the treated-effect numerator and treated-mass denominator.
-/
theorem populationPATT_eq_scorePATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    [DecidableEq Cell] [TopologicalSpace Cell] [DiscreteTopology Cell]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue : Cell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    repr.populationPATT =
      (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
        (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) :=
  populationPATT_eq_scorePATT_of_ae_scoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr treatedEffectNumerator treatedMass
    (fun sample => scoreEffectCellValue (score sample))
    (fun sample => scoreTreatedMassCellValue (score sample))
    hreprNumerator hreprMass hnumerator hmass
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score scoreEffectCellValue hscore)
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score scoreTreatedMassCellValue hscore)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scoreEffectCellValue hscore
      hcover)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scoreTreatedMassCellValue
      hscore hcover)

/--
Selected-sample Hájek PATT identification from almost-everywhere finite
score-cell score versions.
-/
theorem selectedHajekPATT_eq_scorePATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    [DecidableEq Cell] [TopologicalSpace Cell] [DiscreteTopology Cell]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreatedMass : repr.population_treated_mass ≠ 0)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue : Cell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    repr.selectedHajekPATT =
      (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
        (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) :=
  selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub repr hsampling htreatedMass treatedEffectNumerator treatedMass
    (fun sample => scoreEffectCellValue (score sample))
    (fun sample => scoreTreatedMassCellValue (score sample))
    hreprNumerator hreprMass hnumerator hmass
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score scoreEffectCellValue hscore)
    (scoreCellLoading_aestronglyMeasurable_of_discreteScore
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) score scoreTreatedMassCellValue hscore)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scoreEffectCellValue hscore
      hcover)
    (scoreCellLoading_integrable_of_discreteScore_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub cells score scoreTreatedMassCellValue
      hscore hcover)

/--
Paired population PATE/PATT identification from a.e. finite score-cell
versions with finite-cell integrability supplied by the shared cell cover.
-/
theorem populationPATE_PATT_eq_scorePATE_PATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    [DecidableEq Cell] [TopologicalSpace Cell] [DiscreteTopology Cell]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedCellValue controlCellValue scoreEffectCellValue
      scoreTreatedMassCellValue : Cell -> Real)
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
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    pateRepr.populationPATE =
        (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
          (∫ sample, controlCellValue (score sample) ∂sampleLaw) ∧
      pattRepr.populationPATT =
        (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
          (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) := by
  constructor
  · exact
      populationPATE_eq_scorePATE_of_ae_scoreCellVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr cells score treatedOutcome
        controlOutcome treatedCellValue controlCellValue hreprT hreprC hscore
        hcover htreated hcontrol
  · exact
      populationPATT_eq_scorePATT_of_ae_scoreCellVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr cells score
        treatedEffectNumerator treatedMass scoreEffectCellValue
        scoreTreatedMassCellValue hreprNumerator hreprMass hscore hcover
        hnumerator hmass

/--
Paired selected-sample Hájek PATE/PATT identification from a.e. finite
score-cell versions with finite-cell integrability supplied by the shared cell
cover.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    [DecidableEq Cell] [TopologicalSpace Cell] [DiscreteTopology Cell]
    [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (cells : Finset Cell)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedCellValue controlCellValue scoreEffectCellValue
      scoreTreatedMassCellValue : Cell -> Real)
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
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hcover :
      ∀ᵐ sample ∂sampleLaw, score sample ∈ (cells : Set Cell))
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
          (∫ sample, controlCellValue (score sample) ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
          (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) := by
  constructor
  · exact
      selectedHajekPATE_eq_scorePATE_of_ae_scoreCellVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr htreatedSampling
        hcontrolSampling cells score treatedOutcome controlOutcome
        treatedCellValue controlCellValue hreprT hreprC hscore hcover
        htreated hcontrol
  · exact
      selectedHajekPATT_eq_scorePATT_of_ae_scoreCellVersions_finset_abs_sum_bound
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr hpattSampling hpattMass cells
        score treatedEffectNumerator treatedMass scoreEffectCellValue
        scoreTreatedMassCellValue hreprNumerator hreprMass hscore hcover
        hnumerator hmass

/--
Finite score-cell-type variant of population PATE identification from a.e.
finite score-cell score versions.
-/
theorem populationPATE_eq_scorePATE_of_ae_scoreCellVersions_fintype_abs_sum_bound
    [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell] [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample)) :
    repr.populationPATE =
      (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
        (∫ sample, controlCellValue (score sample) ∂sampleLaw) :=
  populationPATE_eq_scorePATE_of_ae_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub repr (Finset.univ : Finset Cell) score
    treatedOutcome controlOutcome treatedCellValue controlCellValue hreprT
    hreprC hscore (Filter.Eventually.of_forall (fun sample => by simp))
    htreated hcontrol

/--
Finite score-cell-type variant of selected Hájek PATE identification from a.e.
finite score-cell score versions.
-/
theorem selectedHajekPATE_eq_scorePATE_of_ae_scoreCellVersions_fintype_abs_sum_bound
    [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell] [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample)) :
    repr.selectedHajekPATE =
      (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
        (∫ sample, controlCellValue (score sample) ∂sampleLaw) :=
  selectedHajekPATE_eq_scorePATE_of_ae_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub repr htreatedSampling hcontrolSampling
    (Finset.univ : Finset Cell) score treatedOutcome controlOutcome
    treatedCellValue controlCellValue hreprT hreprC hscore
    (Filter.Eventually.of_forall (fun sample => by simp)) htreated hcontrol

/--
Finite score-cell-type variant of population PATT identification from a.e.
finite score-cell score versions.
-/
theorem populationPATT_eq_scorePATT_of_ae_scoreCellVersions_fintype_abs_sum_bound
    [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell] [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (score : Sample -> Cell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue : Cell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    repr.populationPATT =
      (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
        (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) :=
  populationPATT_eq_scorePATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub repr (Finset.univ : Finset Cell) score
    treatedEffectNumerator treatedMass scoreEffectCellValue
    scoreTreatedMassCellValue hreprNumerator hreprMass hscore
    (Filter.Eventually.of_forall (fun sample => by simp)) hnumerator hmass

/--
Finite score-cell-type variant of selected Hájek PATT identification from a.e.
finite score-cell score versions.
-/
theorem selectedHajekPATT_eq_scorePATT_of_ae_scoreCellVersions_fintype_abs_sum_bound
    [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell] [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreatedMass : repr.population_treated_mass ≠ 0)
    (score : Sample -> Cell)
    (treatedEffectNumerator treatedMass : Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue : Cell -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    repr.selectedHajekPATT =
      (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
        (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) :=
  selectedHajekPATT_eq_scorePATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub repr hsampling htreatedMass
    (Finset.univ : Finset Cell) score treatedEffectNumerator treatedMass
    scoreEffectCellValue scoreTreatedMassCellValue hreprNumerator hreprMass
    hscore (Filter.Eventually.of_forall (fun sample => by simp))
    hnumerator hmass

/--
Finite score-cell-type variant of paired population PATE/PATT identification
from a.e. finite score-cell score versions.
-/
theorem populationPATE_PATT_eq_scorePATE_PATT_of_ae_scoreCellVersions_fintype_abs_sum_bound
    [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell] [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedCellValue controlCellValue scoreEffectCellValue
      scoreTreatedMassCellValue : Cell -> Real)
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
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    pateRepr.populationPATE =
        (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
          (∫ sample, controlCellValue (score sample) ∂sampleLaw) ∧
      pattRepr.populationPATT =
        (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
          (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) :=
  populationPATE_PATT_eq_scorePATE_PATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub pateRepr pattRepr
    (Finset.univ : Finset Cell) score treatedOutcome controlOutcome
    treatedEffectNumerator treatedMass treatedCellValue controlCellValue
    scoreEffectCellValue scoreTreatedMassCellValue hreprT hreprC
    hreprNumerator hreprMass hscore
    (Filter.Eventually.of_forall (fun sample => by simp)) htreated hcontrol
    hnumerator hmass

/--
Finite score-cell-type variant of paired selected Hájek PATE/PATT
identification from a.e. finite score-cell score versions.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreCellVersions_fintype_abs_sum_bound
    [Fintype Cell] [DecidableEq Cell] [TopologicalSpace Cell]
    [DiscreteTopology Cell] [IsFiniteMeasure sampleLaw]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (score : Sample -> Cell)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass :
      Sample -> Real)
    (treatedCellValue controlCellValue scoreEffectCellValue
      scoreTreatedMassCellValue : Cell -> Real)
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
    (hscore : AEStronglyMeasurable[scoreSigma] score sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw]
        fun sample => treatedCellValue (score sample))
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw]
        fun sample => controlCellValue (score sample))
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw]
        fun sample => scoreEffectCellValue (score sample))
    (hmass :
      treatedMass =ᵐ[sampleLaw]
        fun sample => scoreTreatedMassCellValue (score sample)) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedCellValue (score sample) ∂sampleLaw) -
          (∫ sample, controlCellValue (score sample) ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectCellValue (score sample) ∂sampleLaw) /
          (∫ sample, scoreTreatedMassCellValue (score sample) ∂sampleLaw) :=
  selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreCellVersions_finset_abs_sum_bound
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
    hcontrolSampling hpattSampling hpattMass (Finset.univ : Finset Cell)
    score treatedOutcome controlOutcome treatedEffectNumerator treatedMass
    treatedCellValue controlCellValue scoreEffectCellValue
    scoreTreatedMassCellValue hreprT hreprC hreprNumerator hreprMass hscore
    (Filter.Eventually.of_forall (fun sample => by simp)) htreated hcontrol
    hnumerator hmass

end WDSM
end Matching
end StatInference
