import Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic

/-!
# Conditional-expectation bridge lemmas for WDSM

The finite score-cell modules prove deterministic recovery once candidate
score-cell means agree with true finite cell means.  This module starts the
measure-theoretic lift: a score-sigma-field measurable version is its own
conditional expectation, and an outcome that is almost everywhere equal to such
a version has that version as its conditional expectation.
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
If an outcome is measurable with respect to the score sigma-field, then its
conditional expectation given that score sigma-field is itself.
-/
theorem condExp_eq_self_of_scoreSigma_stronglyMeasurable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome : Sample -> Real)
    (hscoreMeas : StronglyMeasurable[scoreSigma] outcome)
    (hintegrable : Integrable outcome sampleLaw) :
    sampleLaw[outcome | scoreSigma] = outcome := by
  exact condExp_of_stronglyMeasurable hsub hscoreMeas hintegrable

/--
The almost-everywhere measurable version of the previous statement.  This is
the form normally used after replacing an informal conditional-mean claim by an
`AEStronglyMeasurable` representative.
-/
theorem condExp_ae_eq_self_of_scoreSigma_aestronglyMeasurable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome : Sample -> Real)
    (hscoreMeas : AEStronglyMeasurable[scoreSigma] outcome sampleLaw)
    (hintegrable : Integrable outcome sampleLaw) :
    sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] outcome := by
  exact condExp_of_aestronglyMeasurable' hsub hscoreMeas hintegrable

/--
If an outcome agrees almost everywhere with a score-sigma-field measurable
version, then the conditional expectation of the outcome is that score version.
-/
theorem condExp_ae_eq_scoreVersion_of_ae_eq_stronglyMeasurable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[sampleLaw] scoreVersion)
    (hscoreMeas : StronglyMeasurable[scoreSigma] scoreVersion)
    (hintegrable : Integrable scoreVersion sampleLaw) :
    sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion := by
  have hcond :
      sampleLaw[scoreVersion | scoreSigma] = scoreVersion :=
    condExp_of_stronglyMeasurable
      (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw)
      hsub hscoreMeas hintegrable
  exact
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw) houtcome).trans
      (by rw [hcond])

/--
Almost-everywhere version of the score-version bridge.  This is the weakest
form needed when the candidate score-space mean is represented only up to
sample-law null sets.
-/
theorem condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[sampleLaw] scoreVersion)
    (hscoreMeas : AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hintegrable : Integrable scoreVersion sampleLaw) :
    sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion := by
  exact
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw) houtcome).trans
      (condExp_of_aestronglyMeasurable'
        (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw)
        hsub hscoreMeas hintegrable)

end WDSM
end Matching
end StatInference
