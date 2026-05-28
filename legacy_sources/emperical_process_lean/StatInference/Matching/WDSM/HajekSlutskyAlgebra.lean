import StatInference.Matching.WDSM.KnownScoreLimitAlgebra

/-!
# Hájek Slutsky algebra for WDSM

Hájek-normalized WDSM estimators introduce denominator corrections.  Once the
inverse denominator correction converges to one in probability, multiplication
by that correction should not change the leading distributional limit.  This
module records that mathlib-backed Slutsky step.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

omit [MeasureTheory.IsProbabilityMeasure sampleLaw] [l.IsCountablyGenerated] in
/--
Adding one to a real-valued negligible-in-probability denominator remainder
converges to one in probability.
-/
theorem tendstoInMeasure_one_add_denominator_remainder
    (denominatorRemainder : Index -> Sample -> Real)
    (hdenominator :
      TendstoInMeasure sampleLaw denominatorRemainder l
        (fun _sample => (0 : Real))) :
    TendstoInMeasure sampleLaw
      (fun index sample => 1 + denominatorRemainder index sample) l
      (fun _sample => (1 : Real)) := by
  rw [tendstoInMeasure_iff_norm] at hdenominator ⊢
  intro ε hε
  have hsame :
      (fun index =>
        sampleLaw {sample |
          ε ≤ ‖1 + denominatorRemainder index sample - 1‖}) =
        (fun index =>
          sampleLaw {sample |
            ε ≤ ‖denominatorRemainder index sample - 0‖}) := by
    funext index
    congr 1
    ext sample
    simp only [Set.mem_setOf_eq]
    ring_nf
  rw [hsame]
  exact hdenominator ε hε

/--
Multiplying a leading statistic by a real-valued denominator correction that
converges to one in probability preserves the statistic's distributional
limit.
-/
theorem tendstoInDistribution_mul_denominator_correction_one
    (main denominatorCorrection : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hdenominator :
      TendstoInMeasure sampleLaw denominatorCorrection l
        (fun _sample => (1 : Real)))
    (hdenominator_meas :
      ∀ index, AEMeasurable (denominatorCorrection index) sampleLaw) :
    TendstoInDistribution
      (fun index sample => main index sample *
        denominatorCorrection index sample)
      l limit (fun _index => sampleLaw) limitLaw := by
  have h :=
    hmain.continuous_comp_prodMk_of_tendstoInMeasure_const
      (Y := denominatorCorrection)
      (c := (1 : Real))
      (g := fun pair : Real × Real => pair.1 * pair.2)
      (by fun_prop) hdenominator hdenominator_meas
  simpa [mul_one] using h

/--
Hájek known-score decomposition with denominator correction.

If the actual statistic is almost everywhere equal to the two-remainder
known-score decomposition multiplied by a denominator correction, the leading
term has a distributional limit, the two remainders are `o_p(1)`, and the
denominator correction converges to one in probability, then the actual
statistic has the leading term's distributional limit.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_two_negligible_mul_denominator
    (statistic main firstRemainder secondRemainder denominatorCorrection :
      Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            (main index sample + firstRemainder index sample +
                secondRemainder index sample) *
              denominatorCorrection index sample))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw firstRemainder l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw secondRemainder l
        (fun _sample => (0 : Real)))
    (hdenominator :
      TendstoInMeasure sampleLaw denominatorCorrection l
        (fun _sample => (1 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (firstRemainder index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (secondRemainder index) sampleLaw)
    (hdenominator_meas :
      ∀ index, AEMeasurable (denominatorCorrection index) sampleLaw) :
    TendstoInDistribution statistic l limit
      (fun _index => sampleLaw) limitLaw := by
  have hsum :=
    tendstoInDistribution_main_add_two_negligible
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main firstRemainder secondRemainder limit
      hmain hfirst hsecond hfirst_meas hsecond_meas
  have hmul :=
    tendstoInDistribution_mul_denominator_correction_one
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun index sample =>
        main index sample + firstRemainder index sample +
          secondRemainder index sample)
      denominatorCorrection limit hsum hdenominator hdenominator_meas
  exact TendstoInDistribution.congr
    (fun index => (hdecomposition index).symm)
    (ae_eq_refl limit) hmul

/--
Hájek known-score decomposition where the denominator correction is written as
`1 + denominatorRemainder` and the denominator remainder is `o_p(1)`.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_two_negligible_mul_one_add_denominator
    (statistic main firstRemainder secondRemainder denominatorRemainder :
      Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            (main index sample + firstRemainder index sample +
                secondRemainder index sample) *
              (1 + denominatorRemainder index sample)))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw firstRemainder l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw secondRemainder l
        (fun _sample => (0 : Real)))
    (hdenominator :
      TendstoInMeasure sampleLaw denominatorRemainder l
        (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (firstRemainder index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (secondRemainder index) sampleLaw)
    (hdenominator_meas :
      ∀ index, AEMeasurable (denominatorRemainder index) sampleLaw) :
    TendstoInDistribution statistic l limit
      (fun _index => sampleLaw) limitLaw := by
  have hcorrection :=
    tendstoInMeasure_one_add_denominator_remainder
      (sampleLaw := sampleLaw) (l := l) denominatorRemainder hdenominator
  have hcorrection_meas :
      ∀ index, AEMeasurable
        (fun sample => 1 + denominatorRemainder index sample) sampleLaw := by
    intro index
    exact aemeasurable_const.add (hdenominator_meas index)
  exact tendstoInDistribution_of_ae_eq_main_add_two_negligible_mul_denominator
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main firstRemainder secondRemainder
    (fun index sample => 1 + denominatorRemainder index sample)
    limit hdecomposition hmain hfirst hsecond hcorrection
    hfirst_meas hsecond_meas hcorrection_meas

/--
Hájek known-score decomposition with three negligible remainders and a
denominator correction.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_three_negligible_mul_denominator
    (statistic main firstRemainder secondRemainder thirdRemainder
      denominatorCorrection : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            (main index sample + firstRemainder index sample +
                secondRemainder index sample + thirdRemainder index sample) *
              denominatorCorrection index sample))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw firstRemainder l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw secondRemainder l
        (fun _sample => (0 : Real)))
    (hthird :
      TendstoInMeasure sampleLaw thirdRemainder l
        (fun _sample => (0 : Real)))
    (hdenominator :
      TendstoInMeasure sampleLaw denominatorCorrection l
        (fun _sample => (1 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (firstRemainder index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (secondRemainder index) sampleLaw)
    (hthird_meas :
      ∀ index, AEMeasurable (thirdRemainder index) sampleLaw)
    (hdenominator_meas :
      ∀ index, AEMeasurable (denominatorCorrection index) sampleLaw) :
    TendstoInDistribution statistic l limit
      (fun _index => sampleLaw) limitLaw := by
  have hsum :=
    tendstoInDistribution_main_add_three_negligible
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main firstRemainder secondRemainder thirdRemainder limit
      hmain hfirst hsecond hthird hfirst_meas hsecond_meas hthird_meas
  have hmul :=
    tendstoInDistribution_mul_denominator_correction_one
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun index sample =>
        main index sample + firstRemainder index sample +
          secondRemainder index sample + thirdRemainder index sample)
      denominatorCorrection limit hsum hdenominator hdenominator_meas
  exact TendstoInDistribution.congr
    (fun index => (hdecomposition index).symm)
    (ae_eq_refl limit) hmul

/--
Hájek known-score decomposition with three negligible remainders where the
denominator correction is written as `1 + denominatorRemainder`.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_three_negligible_mul_one_add_denominator
    (statistic main firstRemainder secondRemainder thirdRemainder
      denominatorRemainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            (main index sample + firstRemainder index sample +
                secondRemainder index sample + thirdRemainder index sample) *
              (1 + denominatorRemainder index sample)))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw firstRemainder l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw secondRemainder l
        (fun _sample => (0 : Real)))
    (hthird :
      TendstoInMeasure sampleLaw thirdRemainder l
        (fun _sample => (0 : Real)))
    (hdenominator :
      TendstoInMeasure sampleLaw denominatorRemainder l
        (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (firstRemainder index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (secondRemainder index) sampleLaw)
    (hthird_meas :
      ∀ index, AEMeasurable (thirdRemainder index) sampleLaw)
    (hdenominator_meas :
      ∀ index, AEMeasurable (denominatorRemainder index) sampleLaw) :
    TendstoInDistribution statistic l limit
      (fun _index => sampleLaw) limitLaw := by
  have hcorrection :=
    tendstoInMeasure_one_add_denominator_remainder
      (sampleLaw := sampleLaw) (l := l) denominatorRemainder hdenominator
  have hcorrection_meas :
      ∀ index, AEMeasurable
        (fun sample => 1 + denominatorRemainder index sample) sampleLaw := by
    intro index
    exact aemeasurable_const.add (hdenominator_meas index)
  exact tendstoInDistribution_of_ae_eq_main_add_three_negligible_mul_denominator
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main firstRemainder secondRemainder thirdRemainder
    (fun index sample => 1 + denominatorRemainder index sample)
    limit hdecomposition hmain hfirst hsecond hthird hcorrection
    hfirst_meas hsecond_meas hthird_meas hcorrection_meas

end WDSM
end Matching
end StatInference
