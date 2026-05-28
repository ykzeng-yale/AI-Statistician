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

theorem tendstoInDistribution_scaled_zero_of_ae_eq_zero
    (scale : Index -> Real) (remainder : Index -> Sample -> Real)
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real)) :
    TendstoInDistribution
      (fun index sample => scale index * remainder index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw :=
  tendstoInDistribution_random_scaled_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index _sample => scale index) remainder hzero

theorem tendstoInDistribution_random_scaled_zero_of_forall_eq_zero
    (scale remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, remainder index sample = 0) :
    TendstoInDistribution
      (fun index sample => scale index sample * remainder index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_random_scaled_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale remainder
    (fun index => Eventually.of_forall (fun sample => hzero index sample))

theorem tendstoInDistribution_scaled_zero_of_forall_eq_zero
    (scale : Index -> Real) (remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, remainder index sample = 0) :
    TendstoInDistribution
      (fun index sample => scale index * remainder index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw :=
  tendstoInDistribution_scaled_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale remainder
    (fun index => Eventually.of_forall (fun sample => hzero index sample))

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

theorem tendstoInDistribution_random_scaled_zero_of_forall_abs_eq_zero
    (scale remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, |remainder index sample| = 0) :
    TendstoInDistribution
      (fun index sample => scale index sample * remainder index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_random_scaled_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale remainder
    (fun index sample => abs_eq_zero.mp (hzero index sample))

theorem tendstoInDistribution_scaled_zero_of_forall_abs_eq_zero
    (scale : Index -> Real) (remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, |remainder index sample| = 0) :
    TendstoInDistribution
      (fun index sample => scale index * remainder index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_scaled_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale remainder
    (fun index sample => abs_eq_zero.mp (hzero index sample))

/--
Pointwise equality of two real-valued random sequences gives a degenerate
distributional limit for their difference.
-/
theorem tendstoInDistribution_sub_zero_of_forall_eq
    (first second : Index -> Sample -> Real)
    (heq : ∀ index sample, first index sample = second index sample) :
    TendstoInDistribution
      (fun index sample => first index sample - second index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => first index sample - second index sample)
    (fun index sample => by
      change first index sample - second index sample = 0
      rw [heq index sample, sub_self])

/--
Almost everywhere equality of two real-valued random sequences gives a
degenerate distributional limit for their difference.
-/
theorem tendstoInDistribution_sub_zero_of_ae_eq
    (first second : Index -> Sample -> Real)
    (heq : ∀ index, first index =ᵐ[sampleLaw] second index) :
    TendstoInDistribution
      (fun index sample => first index sample - second index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => first index sample - second index sample)
    (fun index => by
      filter_upwards [heq index] with sample hsample
      rw [hsample, sub_self])

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

theorem tendstoInDistribution_random_scaled_sub_zero_of_forall_eq
    (scale first second : Index -> Sample -> Real)
    (heq : ∀ index sample, first index sample = second index sample) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample * (first index sample - second index sample)) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  exact tendstoInDistribution_random_scaled_sub_zero_of_ae_eq
    (sampleLaw := sampleLaw) (l := l) scale first second
    (fun index => Eventually.of_forall (fun sample => heq index sample))

theorem tendstoInDistribution_scaled_sub_zero_of_ae_eq
    (scale : Index -> Real) (first second : Index -> Sample -> Real)
    (heq : ∀ index, first index =ᵐ[sampleLaw] second index) :
    TendstoInDistribution
      (fun index sample =>
        scale index * (first index sample - second index sample)) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw :=
  tendstoInDistribution_random_scaled_sub_zero_of_ae_eq
    (sampleLaw := sampleLaw) (l := l) (fun index _sample => scale index)
    first second heq

theorem tendstoInDistribution_scaled_sub_zero_of_forall_eq
    (scale : Index -> Real) (first second : Index -> Sample -> Real)
    (heq : ∀ index sample, first index sample = second index sample) :
    TendstoInDistribution
      (fun index sample =>
        scale index * (first index sample - second index sample)) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw :=
  tendstoInDistribution_scaled_sub_zero_of_ae_eq
    (sampleLaw := sampleLaw) (l := l) scale first second
    (fun index => Eventually.of_forall (fun sample => heq index sample))

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
Orientation alias for distributional transfer when equality is written as
`main = statistic`.
-/
theorem tendstoInDistribution_of_forall_eq_main
    (statistic main : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index sample, main index sample = statistic index sample)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  exact tendstoInDistribution_of_forall_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main limit
    (fun index sample => (hstat index sample).symm)
    hmain

omit [l.IsCountablyGenerated] in
/--
Pointwise equality transfers a centered, sample-dependently scaled
distributional limit.
-/
theorem tendstoInDistribution_scaled_centered_of_forall_eq
    (scale statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index sample, statistic index sample = main index sample)
    (hmain :
      TendstoInDistribution
        (fun index sample => scale index sample *
          (main index sample - center index sample)) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => scale index sample *
        (statistic index sample - center index sample)) l limit
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_of_forall_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    (fun index sample => scale index sample *
      (statistic index sample - center index sample))
    (fun index sample => scale index sample *
      (main index sample - center index sample))
    limit
    (fun index sample => by
      simpa using
        congrArg
          (fun value => scale index sample * (value - center index sample))
          (hstat index sample))
    hmain

omit [l.IsCountablyGenerated] in
/--
Almost-everywhere equality transfers a centered, sample-dependently scaled
distributional limit.
-/
theorem tendstoInDistribution_scaled_centered_of_ae_eq
    (scale statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index, statistic index =ᵐ[sampleLaw] main index)
    (hmain :
      TendstoInDistribution
        (fun index sample => scale index sample *
          (main index sample - center index sample)) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => scale index sample *
        (statistic index sample - center index sample)) l limit
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    (fun index sample => scale index sample *
      (statistic index sample - center index sample))
    (fun index sample => scale index sample *
      (main index sample - center index sample))
    limit
    (fun index => by
      filter_upwards [hstat index] with sample hsample
      simpa using
        congrArg
          (fun value => scale index sample * (value - center index sample))
          hsample)
    hmain

omit [l.IsCountablyGenerated] in
/--
Pointwise equality transfers a centered, deterministically scaled
distributional limit.
-/
theorem tendstoInDistribution_deterministic_scaled_centered_of_forall_eq
    (scale : Index -> Real)
    (statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index sample, statistic index sample = main index sample)
    (hmain :
      TendstoInDistribution
        (fun index sample => scale index *
          (main index sample - center index sample)) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => scale index *
        (statistic index sample - center index sample)) l limit
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_scaled_centered_of_forall_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    (fun index _sample => scale index) statistic main center limit hstat
    hmain

omit [l.IsCountablyGenerated] in
/--
Almost-everywhere equality transfers a centered, deterministically scaled
distributional limit.
-/
theorem tendstoInDistribution_deterministic_scaled_centered_of_ae_eq
    (scale : Index -> Real)
    (statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index, statistic index =ᵐ[sampleLaw] main index)
    (hmain :
      TendstoInDistribution
        (fun index sample => scale index *
          (main index sample - center index sample)) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => scale index *
        (statistic index sample - center index sample)) l limit
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_scaled_centered_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    (fun index _sample => scale index) statistic main center limit hstat
    hmain

omit [l.IsCountablyGenerated] in
/--
Pointwise equality transfers an unscaled centered distributional limit.
-/
theorem tendstoInDistribution_centered_of_forall_eq
    (statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index sample, statistic index sample = main index sample)
    (hmain :
      TendstoInDistribution
        (fun index sample => main index sample - center index sample) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => statistic index sample - center index sample) l
      limit (fun _index => sampleLaw) limitLaw := by
  simpa using
    tendstoInDistribution_scaled_centered_of_forall_eq
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun _index _sample => (1 : Real)) statistic main center limit hstat
      (by simpa using hmain)

omit [l.IsCountablyGenerated] in
/--
Orientation alias for centered, sample-dependently scaled transfer when the
pointwise equality is written as `main = statistic`.
-/
theorem tendstoInDistribution_scaled_centered_of_forall_eq_main
    (scale statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index sample, main index sample = statistic index sample)
    (hmain :
      TendstoInDistribution
        (fun index sample => scale index sample *
          (main index sample - center index sample)) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => scale index sample *
        (statistic index sample - center index sample)) l limit
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_scaled_centered_of_forall_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scale statistic main center limit
    (fun index sample => (hstat index sample).symm) hmain

omit [l.IsCountablyGenerated] in
/--
Orientation alias for centered, deterministically scaled transfer when the
pointwise equality is written as `main = statistic`.
-/
theorem tendstoInDistribution_deterministic_scaled_centered_of_forall_eq_main
    (scale : Index -> Real)
    (statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index sample, main index sample = statistic index sample)
    (hmain :
      TendstoInDistribution
        (fun index sample => scale index *
          (main index sample - center index sample)) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => scale index *
        (statistic index sample - center index sample)) l limit
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_deterministic_scaled_centered_of_forall_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scale statistic main center limit
    (fun index sample => (hstat index sample).symm) hmain

omit [l.IsCountablyGenerated] in
/--
Orientation alias for unscaled centered transfer when the pointwise equality
is written as `main = statistic`.
-/
theorem tendstoInDistribution_centered_of_forall_eq_main
    (statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index sample, main index sample = statistic index sample)
    (hmain :
      TendstoInDistribution
        (fun index sample => main index sample - center index sample) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => statistic index sample - center index sample) l
      limit (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_centered_of_forall_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main center limit
    (fun index sample => (hstat index sample).symm) hmain

omit [l.IsCountablyGenerated] in
/--
Almost-everywhere equality transfers an unscaled centered distributional limit.
-/
theorem tendstoInDistribution_centered_of_ae_eq
    (statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index, statistic index =ᵐ[sampleLaw] main index)
    (hmain :
      TendstoInDistribution
        (fun index sample => main index sample - center index sample) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => statistic index sample - center index sample) l
      limit (fun _index => sampleLaw) limitLaw := by
  simpa using
    tendstoInDistribution_scaled_centered_of_ae_eq
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun _index _sample => (1 : Real)) statistic main center limit hstat
      (by simpa using hmain)

omit [l.IsCountablyGenerated] in
/--
Orientation alias for centered, sample-dependently scaled transfer when the
a.e. equality is written as `main =ᵐ statistic`.
-/
theorem tendstoInDistribution_scaled_centered_of_ae_eq_main
    (scale statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index, main index =ᵐ[sampleLaw] statistic index)
    (hmain :
      TendstoInDistribution
        (fun index sample => scale index sample *
          (main index sample - center index sample)) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => scale index sample *
        (statistic index sample - center index sample)) l limit
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_scaled_centered_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scale statistic main center limit
    (fun index => (hstat index).symm) hmain

omit [l.IsCountablyGenerated] in
/--
Orientation alias for centered, deterministically scaled transfer when the
a.e. equality is written as `main =ᵐ statistic`.
-/
theorem tendstoInDistribution_deterministic_scaled_centered_of_ae_eq_main
    (scale : Index -> Real)
    (statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index, main index =ᵐ[sampleLaw] statistic index)
    (hmain :
      TendstoInDistribution
        (fun index sample => scale index *
          (main index sample - center index sample)) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => scale index *
        (statistic index sample - center index sample)) l limit
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_deterministic_scaled_centered_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scale statistic main center limit
    (fun index => (hstat index).symm) hmain

omit [l.IsCountablyGenerated] in
/--
Orientation alias for unscaled centered transfer when the a.e. equality is
written as `main =ᵐ statistic`.
-/
theorem tendstoInDistribution_centered_of_ae_eq_main
    (statistic main center : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hstat : ∀ index, main index =ᵐ[sampleLaw] statistic index)
    (hmain :
      TendstoInDistribution
        (fun index sample => main index sample - center index sample) l limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample => statistic index sample - center index sample) l
      limit (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_centered_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main center limit
    (fun index => (hstat index).symm) hmain

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

omit [l.IsCountablyGenerated] in
/--
If a statistic is almost everywhere a main term plus a deterministically
scaled almost-everywhere zero remainder, it has the main term's distributional
limit.
-/
theorem tendstoInDistribution_of_ae_eq_main_add_scaled_ae_zero
    (scale : Index -> Real)
    (statistic main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            main index sample + scale index * remainder index sample))
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw :=
  tendstoInDistribution_of_ae_eq_main_add_random_scaled_ae_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main (fun index _sample => scale index) remainder limit
    hdecomposition hzero hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is pointwise a main term plus a deterministically scaled
pointwise zero remainder, it has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_forall_eq_main_add_scaled_zero
    (scale : Index -> Real)
    (statistic main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index sample,
        statistic index sample =
          main index sample + scale index * remainder index sample)
    (hzero : ∀ index sample, remainder index sample = 0)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw :=
  tendstoInDistribution_of_ae_eq_main_add_scaled_ae_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scale statistic main remainder limit
    (fun index =>
      Eventually.of_forall (fun sample => hdecomposition index sample))
    (fun index =>
      Eventually.of_forall (fun sample => hzero index sample))
    hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is almost everywhere a main term minus a random-scaled
almost-everywhere zero remainder, it has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_ae_eq_main_sub_random_scaled_ae_zero
    (statistic main scale remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            main index sample - scale index sample * remainder index sample))
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
If a statistic is pointwise a main term minus a random-scaled pointwise zero
remainder, it has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_forall_eq_main_sub_random_scaled_zero
    (statistic main scale remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index sample,
        statistic index sample =
          main index sample - scale index sample * remainder index sample)
    (hzero : ∀ index sample, remainder index sample = 0)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw := by
  exact tendstoInDistribution_of_ae_eq_main_sub_random_scaled_ae_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main scale remainder limit
    (fun index =>
      Eventually.of_forall (fun sample => hdecomposition index sample))
    (fun index =>
      Eventually.of_forall (fun sample => hzero index sample))
    hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is almost everywhere a main term minus a deterministically
scaled almost-everywhere zero remainder, it has the main term's distributional
limit.
-/
theorem tendstoInDistribution_of_ae_eq_main_sub_scaled_ae_zero
    (scale : Index -> Real)
    (statistic main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            main index sample - scale index * remainder index sample))
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real))
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw :=
  tendstoInDistribution_of_ae_eq_main_sub_random_scaled_ae_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    statistic main (fun index _sample => scale index) remainder limit
    hdecomposition hzero hmain

omit [l.IsCountablyGenerated] in
/--
If a statistic is pointwise a main term minus a deterministically scaled
pointwise zero remainder, it has the main term's distributional limit.
-/
theorem tendstoInDistribution_of_forall_eq_main_sub_scaled_zero
    (scale : Index -> Real)
    (statistic main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hdecomposition :
      ∀ index sample,
        statistic index sample =
          main index sample - scale index * remainder index sample)
    (hzero : ∀ index sample, remainder index sample = 0)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw)
        limitLaw) :
    TendstoInDistribution statistic l limit (fun _index => sampleLaw)
      limitLaw :=
  tendstoInDistribution_of_ae_eq_main_sub_scaled_ae_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scale statistic main remainder limit
    (fun index =>
      Eventually.of_forall (fun sample => hdecomposition index sample))
    (fun index =>
      Eventually.of_forall (fun sample => hzero index sample))
    hmain

end WDSM
end Matching
end StatInference
