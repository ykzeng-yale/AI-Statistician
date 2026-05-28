import StatInference.Matching.WDSM.SlutskyAlgebra

/-!
# Known-score limit algebra for WDSM decompositions

The known-score WDSM proof reduces the scaled estimator to a leading CLT term
plus negligible bias and matching/discretization remainders.  This module
packages the corresponding mathlib-backed Slutsky step for two real-valued
`o_p(1)` remainders.
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

/--
If the leading WDSM statistic has a distributional limit and two real-valued
remainders are negligible in probability, then the leading statistic plus both
remainders has the same distributional limit.
-/
theorem tendstoInDistribution_main_add_two_negligible
    (main firstRemainder secondRemainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw firstRemainder l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw secondRemainder l
        (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (firstRemainder index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (secondRemainder index) sampleLaw) :
    TendstoInDistribution
      (fun index sample =>
        main index sample + firstRemainder index sample +
          secondRemainder index sample)
      l limit (fun _index => sampleLaw) limitLaw := by
  have h :=
    tendstoInDistribution_add_const_mul_add_const_mul_negligible_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (firstScale := (1 : Real)) (secondScale := (1 : Real))
      main firstRemainder secondRemainder limit
      hmain hfirst hsecond hfirst_meas hsecond_meas
  simpa [one_mul, add_assoc] using h

/--
If the actual WDSM statistic is almost everywhere equal to the leading term
plus two negligible remainders, then it has the same distributional limit as
the leading term.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_two_negligible
    (statistic main firstRemainder secondRemainder :
      Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            main index sample + firstRemainder index sample +
              secondRemainder index sample))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw firstRemainder l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw secondRemainder l
        (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (firstRemainder index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (secondRemainder index) sampleLaw) :
    TendstoInDistribution statistic l limit
      (fun _index => sampleLaw) limitLaw := by
  have hsum :=
    tendstoInDistribution_main_add_two_negligible
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main firstRemainder secondRemainder limit
      hmain hfirst hsecond hfirst_meas hsecond_meas
  exact TendstoInDistribution.congr
    (fun index => (hdecomposition index).symm)
    (ae_eq_refl limit) hsum

/--
If the leading WDSM statistic has a distributional limit and three real-valued
remainders are negligible in probability, then the leading statistic plus all
three remainders has the same distributional limit.
-/
theorem tendstoInDistribution_main_add_three_negligible
    (main firstRemainder secondRemainder thirdRemainder :
      Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw firstRemainder l
        (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw secondRemainder l
        (fun _sample => (0 : Real)))
    (hthird :
      TendstoInMeasure sampleLaw thirdRemainder l
        (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (firstRemainder index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (secondRemainder index) sampleLaw)
    (hthird_meas :
      ∀ index, AEMeasurable (thirdRemainder index) sampleLaw) :
    TendstoInDistribution
      (fun index sample =>
        main index sample + firstRemainder index sample +
          secondRemainder index sample + thirdRemainder index sample)
      l limit (fun _index => sampleLaw) limitLaw := by
  have hfirst_second :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          firstRemainder index sample + secondRemainder index sample) l
        (fun _sample => (0 : Real)) :=
    tendstoInMeasure_add_zero
      (sampleLaw := sampleLaw) (l := l)
      firstRemainder secondRemainder hfirst hsecond
  have hfirst_second_meas :
      ∀ index, AEMeasurable
        (fun sample =>
          firstRemainder index sample + secondRemainder index sample)
        sampleLaw := by
    intro index
    exact (hfirst_meas index).add (hsecond_meas index)
  have h :=
    tendstoInDistribution_main_add_two_negligible
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main
      (fun index sample =>
        firstRemainder index sample + secondRemainder index sample)
      thirdRemainder limit
      hmain hfirst_second hthird hfirst_second_meas hthird_meas
  simpa [add_assoc] using h

/--
If the actual WDSM statistic is almost everywhere equal to the leading term
plus three negligible remainders, then it has the same distributional limit as
the leading term.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_three_negligible
    (statistic main firstRemainder secondRemainder thirdRemainder :
      Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            main index sample + firstRemainder index sample +
              secondRemainder index sample + thirdRemainder index sample))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw firstRemainder l
        (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw secondRemainder l
        (fun _sample => (0 : Real)))
    (hthird :
      TendstoInMeasure sampleLaw thirdRemainder l
        (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (firstRemainder index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (secondRemainder index) sampleLaw)
    (hthird_meas :
      ∀ index, AEMeasurable (thirdRemainder index) sampleLaw) :
    TendstoInDistribution statistic l limit
      (fun _index => sampleLaw) limitLaw := by
  have hsum :=
    tendstoInDistribution_main_add_three_negligible
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main firstRemainder secondRemainder thirdRemainder limit
      hmain hfirst hsecond hthird hfirst_meas hsecond_meas hthird_meas
  exact TendstoInDistribution.congr
    (fun index => (hdecomposition index).symm)
    (ae_eq_refl limit) hsum

end WDSM
end Matching
end StatInference
