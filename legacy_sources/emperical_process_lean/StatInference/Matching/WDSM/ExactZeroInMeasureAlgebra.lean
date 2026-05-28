import Mathlib.MeasureTheory.Function.ConvergenceInDistribution

/-!
# Exact-zero convergence-in-measure algebra for WDSM

The stochastic WDSM asymptotic modules consume negligible remainders as
`TendstoInMeasure ... 0`.  Exact finite algebra often gives a remainder that
is identically zero, or zero almost everywhere under the sample law.  This
module packages those exact-zero facts as convergence-in-measure inputs.
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
variable {l : Filter Index}

/-- A real-valued random sequence that is pointwise zero converges to zero in measure. -/
theorem tendstoInMeasure_zero_of_forall_eq_zero
    (remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, remainder index sample = 0) :
    TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)) := by
  rw [tendstoInMeasure_iff_norm]
  intro ε hε
  have hfun :
      (fun index =>
        sampleLaw {sample | ε ≤ ‖remainder index sample - 0‖}) =
        (fun _index : Index => (0 : ENNReal)) := by
    funext index
    have hempty :
        {sample | ε ≤ ‖remainder index sample - 0‖} =
          (∅ : Set Sample) := by
      ext sample
      simp [hzero index sample, not_le.mpr hε]
    rw [hempty]
    simp
  rw [hfun]
  exact tendsto_const_nhds

/-- A real-valued random sequence that is almost everywhere zero converges to zero in measure. -/
theorem tendstoInMeasure_zero_of_ae_eq_zero
    (remainder : Index -> Sample -> Real)
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real)) :
    TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)) := by
  have hconst :
      TendstoInMeasure sampleLaw (fun _index _sample => (0 : Real)) l
        (fun _sample => (0 : Real)) :=
    tendstoInMeasure_zero_of_forall_eq_zero
      (sampleLaw := sampleLaw) (l := l)
      (fun _index _sample => (0 : Real))
      (fun _index _sample => rfl)
  exact TendstoInMeasure.congr
    (fun index => (hzero index).symm) (ae_eq_refl _) hconst

/--
An almost everywhere zero real-valued random sequence remains negligible in
measure after multiplication by any deterministic scale.
-/
theorem tendstoInMeasure_scaled_zero_of_ae_eq_zero
    (scale : Index -> Real) (remainder : Index -> Sample -> Real)
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real)) :
    TendstoInMeasure sampleLaw
      (fun index sample => scale index * remainder index sample) l
      (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => scale index * remainder index sample)
    (fun index => by
      filter_upwards [hzero index] with sample hsample
      rw [hsample, mul_zero])

/--
An almost everywhere zero real-valued random sequence remains negligible in
measure after multiplication by any sample-dependent scale.
-/
theorem tendstoInMeasure_random_scaled_zero_of_ae_eq_zero
    (scale remainder : Index -> Sample -> Real)
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real)) :
    TendstoInMeasure sampleLaw
      (fun index sample => scale index sample * remainder index sample) l
      (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => scale index sample * remainder index sample)
    (fun index => by
      filter_upwards [hzero index] with sample hsample
      rw [hsample, mul_zero])

/--
An absolute-error-zero real-valued random sequence is negligible in measure.
-/
theorem tendstoInMeasure_zero_of_forall_abs_eq_zero
    (remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, |remainder index sample| = 0) :
    TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l) remainder
    (fun index sample => abs_eq_zero.mp (hzero index sample))

/--
An absolute-error-zero random sequence remains negligible in measure after
deterministic scaling.
-/
theorem tendstoInMeasure_scaled_zero_of_forall_abs_eq_zero
    (scale : Index -> Real) (remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, |remainder index sample| = 0) :
    TendstoInMeasure sampleLaw
      (fun index sample => scale index * remainder index sample) l
      (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_scaled_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale remainder
    (fun index =>
      Eventually.of_forall
        (fun sample => abs_eq_zero.mp (hzero index sample)))

/--
An absolute-error-zero random sequence remains negligible in measure after
sample-dependent scaling.
-/
theorem tendstoInMeasure_random_scaled_zero_of_forall_abs_eq_zero
    (scale remainder : Index -> Sample -> Real)
    (hzero : ∀ index sample, |remainder index sample| = 0) :
    TendstoInMeasure sampleLaw
      (fun index sample => scale index sample * remainder index sample) l
      (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_random_scaled_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale remainder
    (fun index =>
      Eventually.of_forall
        (fun sample => abs_eq_zero.mp (hzero index sample)))

/--
Pointwise equality of two real-valued random sequences gives a negligible
difference in measure.
-/
theorem tendstoInMeasure_sub_zero_of_forall_eq
    (first second : Index -> Sample -> Real)
    (heq : ∀ index sample, first index sample = second index sample) :
    TendstoInMeasure sampleLaw
      (fun index sample => first index sample - second index sample) l
      (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => first index sample - second index sample)
    (fun index sample => by
      change first index sample - second index sample = 0
      rw [heq index sample, sub_self])

/--
Almost everywhere equality of two real-valued random sequences gives a
negligible difference in measure.
-/
theorem tendstoInMeasure_sub_zero_of_ae_eq
    (first second : Index -> Sample -> Real)
    (heq : ∀ index, first index =ᵐ[sampleLaw] second index) :
    TendstoInMeasure sampleLaw
      (fun index sample => first index sample - second index sample) l
      (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => first index sample - second index sample)
    (fun index => by
      filter_upwards [heq index] with sample hsample
      rw [hsample, sub_self])

/--
Almost everywhere equality of two real-valued random sequences gives a scaled
negligible difference in measure.
-/
theorem tendstoInMeasure_scaled_sub_zero_of_ae_eq
    (scale : Index -> Real) (first second : Index -> Sample -> Real)
    (heq : ∀ index, first index =ᵐ[sampleLaw] second index) :
    TendstoInMeasure sampleLaw
      (fun index sample =>
        scale index * (first index sample - second index sample)) l
      (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_scaled_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale
    (fun index sample => first index sample - second index sample)
    (fun index => by
      filter_upwards [heq index] with sample hsample
      rw [hsample, sub_self])

/--
Almost everywhere equality of two real-valued random sequences gives a
sample-dependently scaled negligible difference in measure.
-/
theorem tendstoInMeasure_random_scaled_sub_zero_of_ae_eq
    (scale first second : Index -> Sample -> Real)
    (heq : ∀ index, first index =ᵐ[sampleLaw] second index) :
    TendstoInMeasure sampleLaw
      (fun index sample =>
        scale index sample * (first index sample - second index sample)) l
      (fun _sample => (0 : Real)) := by
  exact tendstoInMeasure_random_scaled_zero_of_ae_eq_zero
    (sampleLaw := sampleLaw) (l := l) scale
    (fun index sample => first index sample - second index sample)
    (fun index => by
      filter_upwards [heq index] with sample hsample
      rw [hsample, sub_self])

/--
If two real-valued random sequences are almost everywhere equal at every
index, they have the same convergence-in-measure limit.
-/
theorem tendstoInMeasure_of_ae_eq
    (statistic main : Index -> Sample -> Real) (limit : Sample -> Real)
    (hstat : ∀ index, main index =ᵐ[sampleLaw] statistic index)
    (hmain : TendstoInMeasure sampleLaw main l limit) :
    TendstoInMeasure sampleLaw statistic l limit := by
  exact TendstoInMeasure.congr hstat (ae_eq_refl _) hmain

/--
Pointwise equality of two real-valued random sequences transfers a
convergence-in-measure limit.
-/
theorem tendstoInMeasure_of_forall_eq
    (statistic main : Index -> Sample -> Real) (limit : Sample -> Real)
    (hstat : ∀ index sample, main index sample = statistic index sample)
    (hmain : TendstoInMeasure sampleLaw main l limit) :
    TendstoInMeasure sampleLaw statistic l limit := by
  exact tendstoInMeasure_of_ae_eq
    (sampleLaw := sampleLaw) (l := l) statistic main limit
    (fun index => Eventually.of_forall (fun sample => hstat index sample))
    hmain

/--
If a statistic is almost everywhere a main term plus an almost-everywhere zero
remainder, it has the main term's convergence-in-measure limit.
-/
theorem tendstoInMeasure_of_ae_eq_main_add_ae_zero
    (statistic main remainder : Index -> Sample -> Real)
    (limit : Sample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample => main index sample + remainder index sample))
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real))
    (hmain : TendstoInMeasure sampleLaw main l limit) :
    TendstoInMeasure sampleLaw statistic l limit := by
  have hstat_main :
      ∀ index, main index =ᵐ[sampleLaw] statistic index := by
    intro index
    filter_upwards [hdecomposition index, hzero index] with sample hdecomp hrem
    rw [hdecomp, hrem]
    ring
  exact tendstoInMeasure_of_ae_eq
    (sampleLaw := sampleLaw) (l := l) statistic main limit hstat_main hmain

/--
If a statistic is almost everywhere a main term minus an almost-everywhere zero
remainder, it has the main term's convergence-in-measure limit.
-/
theorem tendstoInMeasure_of_ae_eq_main_sub_ae_zero
    (statistic main remainder : Index -> Sample -> Real)
    (limit : Sample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample => main index sample - remainder index sample))
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real))
    (hmain : TendstoInMeasure sampleLaw main l limit) :
    TendstoInMeasure sampleLaw statistic l limit := by
  have hstat_main :
      ∀ index, main index =ᵐ[sampleLaw] statistic index := by
    intro index
    filter_upwards [hdecomposition index, hzero index] with sample hdecomp hrem
    rw [hdecomp, hrem]
    ring
  exact tendstoInMeasure_of_ae_eq
    (sampleLaw := sampleLaw) (l := l) statistic main limit hstat_main hmain

/--
If a statistic is almost everywhere a main term plus a random-scaled
almost-everywhere zero remainder, it has the main term's convergence-in-measure
limit.
-/
theorem tendstoInMeasure_of_ae_eq_main_add_random_scaled_ae_zero
    (statistic main scale remainder : Index -> Sample -> Real)
    (limit : Sample -> Real)
    (hdecomposition :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            main index sample + scale index sample * remainder index sample))
    (hzero :
      ∀ index, remainder index =ᵐ[sampleLaw] fun _sample => (0 : Real))
    (hmain : TendstoInMeasure sampleLaw main l limit) :
    TendstoInMeasure sampleLaw statistic l limit := by
  have hstat_main :
      ∀ index, main index =ᵐ[sampleLaw] statistic index := by
    intro index
    filter_upwards [hdecomposition index, hzero index] with sample hdecomp hrem
    rw [hdecomp, hrem, mul_zero]
    ring
  exact tendstoInMeasure_of_ae_eq
    (sampleLaw := sampleLaw) (l := l) statistic main limit hstat_main hmain

end WDSM
end Matching
end StatInference
