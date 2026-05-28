import StatInference.Matching.WDSM.ExactZeroInMeasureAlgebra
import StatInference.Matching.WDSM.SlutskyAlgebra

/-!
# Exact-zero convergence-in-distribution algebra for WDSM

After exact finite algebra has reduced a stochastic remainder to zero almost
everywhere, the asymptotic-normality proof often needs a degenerate weak-limit
input.  This module packages exact-zero and random-scaled exact-zero
remainders as convergence in distribution to the zero random variable.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample : Type*}
variable [MeasurableSpace Sample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable {LimitSample : Type*} [MeasurableSpace LimitSample]
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/--
A real-valued random sequence that is almost everywhere zero converges in
distribution to the zero random variable.
-/
theorem tendstoInDistribution_zero_of_ae_eq_zero
    (remainder : Index -> Sample -> Real)
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real)) :
    TendstoInDistribution remainder l (fun _sample => (0 : Real))
      (fun _index => sampleLaw) sampleLaw := by
  have hmeasure :=
    tendstoInMeasure_zero_of_ae_eq_zero
      (sampleLaw := sampleLaw) (l := l) remainder hzero
  have hmeas : ∀ index, AEMeasurable (remainder index) sampleLaw := by
    intro index
    exact AEMeasurable.congr aemeasurable_const (hzero index).symm
  exact tendstoInDistribution_zero_of_tendstoInMeasure_zero
    (sampleLaw := sampleLaw) (l := l) remainder hmeasure hmeas

/--
A real-valued random sequence that is pointwise zero converges in distribution
to the zero random variable.
-/
theorem tendstoInDistribution_zero_of_forall_eq_zero
    (remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, remainder index sample = 0) :
    TendstoInDistribution remainder l (fun _sample => (0 : Real))
      (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l) remainder
    (fun index =>
      Eventually.of_forall (fun sample => hzero index sample))

/--
An almost everywhere zero real-valued random sequence remains degenerate in
distribution after multiplication by any sample-dependent scale.
-/
theorem tendstoInDistribution_random_scaled_zero_of_ae_eq_zero
    (scale remainder : Index -> Sample -> Real)
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real)) :
    TendstoInDistribution
      (fun index sample => scale index sample * remainder index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => scale index sample * remainder index sample)
    (fun index => by
      filter_upwards [hzero index] with sample hsample
      rw [hsample, mul_zero])

/--
An absolute-error-zero real-valued random sequence converges in distribution
to the zero random variable.
-/
theorem tendstoInDistribution_zero_of_forall_abs_eq_zero
    (remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, |remainder index sample| = 0) :
    TendstoInDistribution remainder l (fun _sample => (0 : Real))
      (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l) remainder
    (fun index sample => abs_eq_zero.mp (hzero index sample))

/--
Almost everywhere equality of two real-valued random sequences gives a
sample-dependently scaled degenerate distributional difference.
-/
theorem tendstoInDistribution_random_scaled_sub_zero_of_ae_eq
    (scale first second : Index -> Sample -> Real)
    (heq : ∀ index, first index =ᵐ[sampleLaw] second index) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample * (first index sample - second index sample)) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_random_scaled_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale
    (fun index sample => first index sample - second index sample)
    (fun index => by
      filter_upwards [heq index] with sample hsample
      rw [hsample, sub_self])

omit [l.IsCountablyGenerated] in
/--
If two real-valued statistics are almost everywhere equal at every index, they
have the same distributional limit.
-/
theorem tendstoInDistribution_of_ae_eq
    (statistic main : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index, statistic index =ᵐ[sampleLaw] main index)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  exact TendstoInDistribution.congr
    (fun index => (hstat index).symm) (ae_eq_refl limit) hmain

omit [l.IsCountablyGenerated] in
/--
Pointwise equality of two real-valued statistics transfers a distributional
limit.
-/
theorem tendstoInDistribution_of_forall_eq
    (statistic main : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index sample, statistic index sample = main index sample)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  exact tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main limit
    (fun index => Eventually.of_forall (fun sample => hstat index sample))
    hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is almost everywhere a main term plus an almost-everywhere zero
remainder, it has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_ae_zero
    (statistic main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample => main index sample + remainder index sample))
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  have hstat_main :
      ∀ index, statistic index =ᵐ[sampleLaw] main index := by
    intro index
    filter_upwards [hdecomposition index, hzero index] with sample hdecomp hrem
    rw [hdecomp, hrem]
    ring
  exact tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main limit hstat_main hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is pointwise a main term plus a pointwise zero remainder, it has
the main term's distributional limit.
-/
theorem tendstoInDistribution_of_forall_eq_main_add_zero
    (statistic main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index sample,
        statistic index sample = main index sample + remainder index sample)
    (hzero : ∀ index sample, remainder index sample = 0)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  exact tendstoInDistribution_of_ae_eq_main_add_ae_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main remainder limit
    (fun index =>
      Eventually.of_forall (fun sample => hdecomposition index sample))
    (fun index =>
      Eventually.of_forall (fun sample => hzero index sample))
    hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is almost everywhere a main term minus an almost-everywhere zero
remainder, it has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_ae_eq_main_sub_ae_zero
    (statistic main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample => main index sample - remainder index sample))
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  have hstat_main :
      ∀ index, statistic index =ᵐ[sampleLaw] main index := by
    intro index
    filter_upwards [hdecomposition index, hzero index] with sample hdecomp hrem
    rw [hdecomp, hrem]
    ring
  exact tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main limit hstat_main hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is pointwise a main term minus a pointwise zero remainder, it
has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_forall_eq_main_sub_zero
    (statistic main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index sample,
        statistic index sample = main index sample - remainder index sample)
    (hzero : ∀ index sample, remainder index sample = 0)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  exact tendstoInDistribution_of_ae_eq_main_sub_ae_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main remainder limit
    (fun index =>
      Eventually.of_forall (fun sample => hdecomposition index sample))
    (fun index =>
      Eventually.of_forall (fun sample => hzero index sample))
    hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is almost everywhere a main term plus a random-scaled
almost-everywhere zero remainder, it has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_random_scaled_ae_zero
    (statistic main scale remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            main index sample + scale index sample * remainder index sample))
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  have hstat_main :
      ∀ index, statistic index =ᵐ[sampleLaw] main index := by
    intro index
    filter_upwards [hdecomposition index, hzero index] with sample hdecomp hrem
    rw [hdecomp, hrem, mul_zero]
    ring
  exact tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main limit hstat_main hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is pointwise a main term plus a random-scaled pointwise zero
remainder, it has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_forall_eq_main_add_random_scaled_zero
    (statistic main scale remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index sample,
        statistic index sample =
          main index sample + scale index sample * remainder index sample)
    (hzero : ∀ index sample, remainder index sample = 0)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  exact tendstoInDistribution_of_ae_eq_main_add_random_scaled_ae_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main scale remainder limit
    (fun index =>
      Eventually.of_forall (fun sample => hdecomposition index sample))
    (fun index =>
      Eventually.of_forall (fun sample => hzero index sample))
    hmain

end WDSM
end Matching
end StatInference
