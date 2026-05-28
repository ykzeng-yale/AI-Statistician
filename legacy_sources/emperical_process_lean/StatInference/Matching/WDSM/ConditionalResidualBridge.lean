import StatInference.Matching.WDSM.ConditionalExpectationBridge

/-!
# Conditional mean-zero residual bridge for WDSM

Residual CLT arguments require residuals with zero conditional mean given the
matching score sigma-field.  This module proves the measure-theoretic algebra:
if a score-space version is the conditional expectation of an outcome, then the
outcome minus that version has zero conditional expectation.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped MeasureTheory

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
If `scoreVersion` is both the conditional expectation of `outcome` and its own
conditional expectation, then the residual `outcome - scoreVersion` has zero
conditional expectation.
-/
theorem condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreSelf :
      sampleLaw[scoreVersion | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample => outcome sample - scoreVersion sample) | scoreSigma] =ᵐ[
      sampleLaw] 0 := by
  refine (condExp_sub (μ := sampleLaw) houtcome hscore scoreSigma).trans ?_
  refine (hcond.sub hscoreSelf).trans ?_
  exact Eventually.of_forall (fun sample => sub_self (scoreVersion sample))

/--
Score-measurable version of the residual mean-zero bridge.  Once an external
identification argument supplies that the conditional expectation of the outcome
equals the score-version, score-measurability discharges the self-conditional
expectation side.
-/
theorem condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_stronglyMeasurable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas : StronglyMeasurable[scoreSigma] scoreVersion)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample => outcome sample - scoreVersion sample) | scoreSigma] =ᵐ[
      sampleLaw] 0 := by
  exact
    condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      outcome scoreVersion houtcome hscore hcond
      (by
        rw [condExp_of_stronglyMeasurable
          (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw)
          hsub hscoreMeas hscore])

/--
Almost-everywhere measurable version of the residual mean-zero bridge, matching
the common form of score-space regressions in probability arguments.
-/
theorem condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_aestronglyMeasurable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas : AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample => outcome sample - scoreVersion sample) | scoreSigma] =ᵐ[
      sampleLaw] 0 :=
  condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    outcome scoreVersion houtcome hscore hcond
    (condExp_of_aestronglyMeasurable'
      (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw)
      hsub hscoreMeas hscore)

end WDSM
end Matching
end StatInference
