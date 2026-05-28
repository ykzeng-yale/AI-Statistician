import StatInference.Matching.WDSM.ConditionalExpectationBridge

/-!
# Conditional-mean integral bridge for WDSM identification

Population identification arguments use conditional mean equalities on the
matching score sigma-field to replace one population or arm mean by another.
This module proves the measure-theoretic integral consequences of those
conditional-mean equalities.
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
If two integrable outcomes have the same conditional expectation given the
score sigma-field, then they have the same population integral.
-/
theorem integral_eq_of_condExp_ae_eq
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcomeA outcomeB : Sample -> Real)
    (hcond :
      sampleLaw[outcomeA | scoreSigma] =ᵐ[sampleLaw]
        sampleLaw[outcomeB | scoreSigma]) :
    ∫ sample, outcomeA sample ∂sampleLaw =
      ∫ sample, outcomeB sample ∂sampleLaw := by
  rw [← integral_condExp
    (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw) (f := outcomeA)
    hsub]
  rw [← integral_condExp
    (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw) (f := outcomeB)
    hsub]
  exact integral_congr_ae hcond

/--
If the conditional expectation of an outcome is a supplied score-space version,
then the population integral of the outcome equals the integral of that version.
-/
theorem integral_eq_scoreVersion_of_condExp_ae_eq
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcome sample ∂sampleLaw =
      ∫ sample, scoreVersion sample ∂sampleLaw := by
  rw [← integral_condExp
      (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw) (f := outcome)
      hsub]
  exact integral_congr_ae hcond

/--
If an outcome is a.e. equal to another outcome whose conditional expectation is
a supplied score-space version, then the original outcome has the same integral
as that score version.
-/
theorem integral_eq_of_ae_eq_condExp_ae_eq_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome outcome' scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[sampleLaw] outcome')
    (hcond :
      sampleLaw[outcome' | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcome sample ∂sampleLaw =
      ∫ sample, scoreVersion sample ∂sampleLaw := by
  rw [integral_congr_ae houtcome]
  exact integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome' scoreVersion hcond

/--
Conditional-mean score-version equality makes the integrated residual
`outcome - scoreVersion` vanish.
-/
theorem integral_sub_scoreVersion_eq_zero_of_condExp_ae_eq
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (hscoreIntegrable : Integrable scoreVersion sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcome sample - scoreVersion sample ∂sampleLaw = 0 := by
  rw [integral_sub houtcomeIntegrable hscoreIntegrable]
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome scoreVersion hcond]
  ring

/--
Raw-outcome-integrability variant of
`integral_sub_scoreVersion_eq_zero_of_condExp_ae_eq`.
-/
theorem integral_sub_scoreVersion_eq_zero_of_condExp_ae_eq_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcome sample - scoreVersion sample ∂sampleLaw = 0 := by
  have hscoreIntegrable : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact integral_sub_scoreVersion_eq_zero_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome scoreVersion houtcomeIntegrable hscoreIntegrable hcond

/--
Conditional-mean score-version equality also makes the reverse integrated
residual `scoreVersion - outcome` vanish.
-/
theorem integral_scoreVersion_sub_eq_zero_of_condExp_ae_eq
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (hscoreIntegrable : Integrable scoreVersion sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, scoreVersion sample - outcome sample ∂sampleLaw = 0 := by
  rw [integral_sub hscoreIntegrable houtcomeIntegrable]
  rw [← integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome scoreVersion hcond]
  ring

/--
Raw-outcome-integrability variant of
`integral_scoreVersion_sub_eq_zero_of_condExp_ae_eq`.
-/
theorem integral_scoreVersion_sub_eq_zero_of_condExp_ae_eq_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, scoreVersion sample - outcome sample ∂sampleLaw = 0 := by
  have hscoreIntegrable : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact integral_scoreVersion_sub_eq_zero_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome scoreVersion houtcomeIntegrable hscoreIntegrable hcond

/--
If two outcomes share the same score-space conditional-mean version, then their
population integrals are equal.
-/
theorem integral_eq_of_common_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcomeA outcomeB scoreVersion : Sample -> Real)
    (hcondA :
      sampleLaw[outcomeA | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hcondB :
      sampleLaw[outcomeB | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcomeA sample ∂sampleLaw =
      ∫ sample, outcomeB sample ∂sampleLaw := by
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcomeA scoreVersion hcondA]
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcomeB scoreVersion hcondB]

/--
If an outcome agrees a.e. with a score-measurable version, then its population
integral equals the integral of that score version.
-/
theorem integral_eq_scoreVersion_of_ae_eq_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[sampleLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hscoreIntegrable : Integrable scoreVersion sampleLaw) :
    ∫ sample, outcome sample ∂sampleLaw =
      ∫ sample, scoreVersion sample ∂sampleLaw := by
  exact
    integral_eq_scoreVersion_of_condExp_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      hsub outcome scoreVersion
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
        hsub outcome scoreVersion houtcome hscoreMeas hscoreIntegrable)

/--
Raw-outcome-integrability variant of
`integral_eq_scoreVersion_of_ae_eq_scoreVersion`.
-/
theorem integral_eq_scoreVersion_of_ae_eq_scoreVersion_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[sampleLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (houtcomeIntegrable : Integrable outcome sampleLaw) :
    ∫ sample, outcome sample ∂sampleLaw =
      ∫ sample, scoreVersion sample ∂sampleLaw := by
  exact integral_eq_scoreVersion_of_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome scoreVersion houtcome hscoreMeas
    (houtcomeIntegrable.congr houtcome)

/--
If an outcome agrees a.e. with a score-measurable version, then the integrated
residual against that version vanishes.
-/
theorem integral_sub_scoreVersion_eq_zero_of_ae_eq_scoreVersion
    (outcome scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (hscoreIntegrable : Integrable scoreVersion sampleLaw)
    (houtcome : outcome =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcome sample - scoreVersion sample ∂sampleLaw = 0 := by
  rw [integral_sub houtcomeIntegrable hscoreIntegrable]
  rw [integral_congr_ae houtcome]
  ring

/--
If an outcome agrees a.e. with a score-measurable version, then the reverse
integrated residual against that version vanishes.
-/
theorem integral_scoreVersion_sub_eq_zero_of_ae_eq_scoreVersion
    (outcome scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (hscoreIntegrable : Integrable scoreVersion sampleLaw)
    (houtcome : outcome =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, scoreVersion sample - outcome sample ∂sampleLaw = 0 := by
  rw [integral_sub hscoreIntegrable houtcomeIntegrable]
  rw [integral_congr_ae houtcome]
  ring

/--
Raw-outcome-integrability variant of the a.e. residual-zero theorem.
-/
theorem integral_sub_scoreVersion_eq_zero_of_ae_eq_scoreVersion_outcomeIntegrable
    (outcome scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (houtcome : outcome =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcome sample - scoreVersion sample ∂sampleLaw = 0 := by
  exact integral_sub_scoreVersion_eq_zero_of_ae_eq_scoreVersion
    (mSample := mSample) (sampleLaw := sampleLaw) outcome scoreVersion
    houtcomeIntegrable (houtcomeIntegrable.congr houtcome) houtcome

/--
Raw-outcome-integrability variant of the reverse a.e. residual-zero theorem.
-/
theorem integral_scoreVersion_sub_eq_zero_of_ae_eq_scoreVersion_outcomeIntegrable
    (outcome scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (houtcome : outcome =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, scoreVersion sample - outcome sample ∂sampleLaw = 0 := by
  exact integral_scoreVersion_sub_eq_zero_of_ae_eq_scoreVersion
    (mSample := mSample) (sampleLaw := sampleLaw) outcome scoreVersion
    houtcomeIntegrable (houtcomeIntegrable.congr houtcome) houtcome

/--
If an outcome is a.e. equal to another outcome whose conditional expectation is
a supplied score-space version, then the integrated residual against the score
version vanishes.
-/
theorem integral_sub_scoreVersion_eq_zero_of_ae_eq_condExp_ae_eq_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome outcome' scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (hscoreIntegrable : Integrable scoreVersion sampleLaw)
    (houtcome : outcome =ᵐ[sampleLaw] outcome')
    (hcond :
      sampleLaw[outcome' | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcome sample - scoreVersion sample ∂sampleLaw = 0 := by
  rw [integral_sub houtcomeIntegrable hscoreIntegrable]
  rw [integral_eq_of_ae_eq_condExp_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome outcome' scoreVersion houtcome hcond]
  ring

/--
Raw-outcome-integrability variant of the residual-zero theorem with an a.e.
outcome replacement before the conditional-mean score-version equality.
-/
theorem
    integral_sub_scoreVersion_eq_zero_of_ae_eq_condExp_ae_eq_scoreVersion_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome outcome' scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (houtcome : outcome =ᵐ[sampleLaw] outcome')
    (hcond :
      sampleLaw[outcome' | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, outcome sample - scoreVersion sample ∂sampleLaw = 0 := by
  have hscoreIntegrable : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact integral_sub_scoreVersion_eq_zero_of_ae_eq_condExp_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome outcome' scoreVersion houtcomeIntegrable hscoreIntegrable
    houtcome hcond

/--
If an outcome is a.e. equal to another outcome whose conditional expectation is
a supplied score-space version, then the reverse integrated residual against
the score version vanishes.
-/
theorem integral_scoreVersion_sub_eq_zero_of_ae_eq_condExp_ae_eq_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome outcome' scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (hscoreIntegrable : Integrable scoreVersion sampleLaw)
    (houtcome : outcome =ᵐ[sampleLaw] outcome')
    (hcond :
      sampleLaw[outcome' | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, scoreVersion sample - outcome sample ∂sampleLaw = 0 := by
  rw [integral_sub hscoreIntegrable houtcomeIntegrable]
  rw [integral_eq_of_ae_eq_condExp_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome outcome' scoreVersion houtcome hcond]
  ring

/--
Raw-outcome-integrability variant of the reverse residual-zero theorem with an
a.e. outcome replacement before the conditional-mean score-version equality.
-/
theorem
    integral_scoreVersion_sub_eq_zero_of_ae_eq_condExp_ae_eq_scoreVersion_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome outcome' scoreVersion : Sample -> Real)
    (houtcomeIntegrable : Integrable outcome sampleLaw)
    (houtcome : outcome =ᵐ[sampleLaw] outcome')
    (hcond :
      sampleLaw[outcome' | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample, scoreVersion sample - outcome sample ∂sampleLaw = 0 := by
  have hscoreIntegrable : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact integral_scoreVersion_sub_eq_zero_of_ae_eq_condExp_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub outcome outcome' scoreVersion houtcomeIntegrable hscoreIntegrable
    houtcome hcond

end WDSM
end Matching
end StatInference
