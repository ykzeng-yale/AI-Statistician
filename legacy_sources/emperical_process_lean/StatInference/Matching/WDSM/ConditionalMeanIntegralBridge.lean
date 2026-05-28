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

end WDSM
end Matching
end StatInference
