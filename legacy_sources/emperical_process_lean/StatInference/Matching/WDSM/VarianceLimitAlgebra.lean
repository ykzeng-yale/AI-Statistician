import Mathlib.MeasureTheory.Function.ConvergenceInMeasure
import StatInference.Matching.WDSM.PATTVarianceAlgebra
import StatInference.Matching.WDSM.ScoreAdjustmentAlgebra
import StatInference.Matching.WDSM.SlutskyAlgebra

/-!
# Variance-target limit algebra for WDSM

The WDSM asymptotic variance proofs eventually need probability arguments
showing that sample analogues of heterogeneity variance, residual variance,
projection reductions, and target-drift terms converge.  This module verifies
the deterministic continuous-mapping layer used after those ingredients are
available.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter

/-- Standard error associated with a scalar variance target. -/
noncomputable def standardError (varianceTarget : Real) : Real :=
  Real.sqrt varianceTarget

/--
Continuous mapping for convergence in measure to a real constant.  This is the
probability-limit analogue of the deterministic continuous-mapping steps below.
-/
theorem tendstoInMeasure_continuousAt_const
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (transform : Real -> Real) (estimate : Index -> Sample -> Real)
    (limit : Real)
    (hestimate :
      TendstoInMeasure sampleLaw estimate l (fun _sample => limit))
    (hcontinuous : ContinuousAt transform limit) :
    TendstoInMeasure sampleLaw
      (fun index sample => transform (estimate index sample)) l
      (fun _sample => transform limit) := by
  rw [tendstoInMeasure_iff_norm] at hestimate ⊢
  intro ε hε
  obtain ⟨δ, hδ_pos, hδ⟩ :=
    Metric.continuousAt_iff.mp hcontinuous ε hε
  have hbase := hestimate δ hδ_pos
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le
    tendsto_const_nhds hbase (fun _index => zero_le) ?_
  intro index
  refine measure_mono ?_
  intro sample hlarge
  have hnot_small : ¬ ‖estimate index sample - limit‖ < δ := by
    intro hsmall
    have hdist_small : dist (estimate index sample) limit < δ := by
      simpa [dist_eq_norm] using hsmall
    have htrans_small :
        dist (transform (estimate index sample)) (transform limit) < ε :=
      hδ hdist_small
    have hnorm_small :
        ‖transform (estimate index sample) - transform limit‖ < ε := by
      simpa [dist_eq_norm] using htrans_small
    exact (not_lt_of_ge hlarge) hnorm_small
  exact le_of_not_gt hnot_small

/--
A constant real-valued sequence of random variables converges in measure to
that same constant.
-/
theorem tendstoInMeasure_const_const
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (constant : Real) :
    TendstoInMeasure sampleLaw (fun _index _sample => constant) l
      (fun _sample => constant) := by
  rw [tendstoInMeasure_iff_norm]
  intro ε hε
  have hfun :
      (fun _index : Index =>
        sampleLaw {sample : Sample | ε ≤ ‖constant - constant‖}) =
        (fun _index : Index => (0 : ENNReal)) := by
    funext index
    have hempty :
        {sample : Sample | ε ≤ ‖constant - constant‖} = ∅ := by
      ext sample
      simp [hε]
    rw [hempty]
    simp
  rw [hfun]
  exact tendsto_const_nhds

/--
If a real-valued estimate converges in measure to a constant, then its
centered error converges in measure to zero.
-/
theorem tendstoInMeasure_sub_const_zero
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (estimate : Index -> Sample -> Real) (limit : Real)
    (hestimate :
      TendstoInMeasure sampleLaw estimate l (fun _sample => limit)) :
    TendstoInMeasure sampleLaw
      (fun index sample => estimate index sample - limit) l
      (fun _sample => (0 : Real)) := by
  simpa using
    tendstoInMeasure_continuousAt_const
      (fun value : Real => value - limit) estimate limit hestimate
      (by fun_prop)

/--
If a centered real-valued error converges in measure to zero, then the
uncentered estimate converges in measure to its constant target.
-/
theorem tendstoInMeasure_of_sub_const_zero
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (estimate : Index -> Sample -> Real) (limit : Real)
    (hcentered :
      TendstoInMeasure sampleLaw
        (fun index sample => estimate index sample - limit) l
        (fun _sample => (0 : Real))) :
    TendstoInMeasure sampleLaw estimate l (fun _sample => limit) := by
  rw [tendstoInMeasure_iff_norm] at hcentered ⊢
  simpa using hcentered

/--
The sum of two real-valued estimates that converge in measure to constants
converges in measure to the sum of the constants.
-/
theorem tendstoInMeasure_add_const
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (first second : Index -> Sample -> Real)
    (firstLimit secondLimit : Real)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => firstLimit))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => secondLimit)) :
    TendstoInMeasure sampleLaw
      (fun index sample => first index sample + second index sample) l
      (fun _sample => firstLimit + secondLimit) := by
  have hfirst_zero :=
    tendstoInMeasure_sub_const_zero
      (sampleLaw := sampleLaw) (l := l) first firstLimit hfirst
  have hsecond_zero :=
    tendstoInMeasure_sub_const_zero
      (sampleLaw := sampleLaw) (l := l) second secondLimit hsecond
  have hsum_zero :=
    tendstoInMeasure_add_zero
      (sampleLaw := sampleLaw) (l := l)
      (fun index sample => first index sample - firstLimit)
      (fun index sample => second index sample - secondLimit)
      hfirst_zero hsecond_zero
  exact tendstoInMeasure_of_sub_const_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => first index sample + second index sample)
    (firstLimit + secondLimit)
    (by
      simpa [sub_eq_add_neg, add_comm, add_left_comm, add_assoc]
        using hsum_zero)

/--
The product of two zero-in-probability real-valued remainders is
zero-in-probability.
-/
theorem tendstoInMeasure_mul_zero
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (first second : Index -> Sample -> Real)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => (0 : Real))) :
    TendstoInMeasure sampleLaw
      (fun index sample => first index sample * second index sample) l
      (fun _sample => (0 : Real)) := by
  rw [tendstoInMeasure_iff_norm] at hfirst hsecond ⊢
  intro ε hε
  let δ : Real := Real.sqrt ε
  have hδ_pos : 0 < δ := Real.sqrt_pos.2 hε
  have hfirst_delta := hfirst δ hδ_pos
  have hsecond_delta := hsecond δ hδ_pos
  have hsum :
      Filter.Tendsto
        (fun index =>
          sampleLaw {sample | δ ≤ ‖first index sample - 0‖} +
            sampleLaw {sample | δ ≤ ‖second index sample - 0‖})
        l (nhds (0 + 0 : ENNReal)) :=
    hfirst_delta.add hsecond_delta
  have hsum_zero :
      Filter.Tendsto
        (fun index =>
          sampleLaw {sample | δ ≤ ‖first index sample - 0‖} +
            sampleLaw {sample | δ ≤ ‖second index sample - 0‖})
        l (nhds (0 : ENNReal)) := by
    simpa using hsum
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le
    tendsto_const_nhds hsum_zero (fun _index => zero_le) ?_
  intro index
  calc
    sampleLaw {sample |
        ε ≤ ‖first index sample * second index sample - 0‖}
        ≤ sampleLaw
            ({sample | δ ≤ ‖first index sample - 0‖} ∪
              {sample | δ ≤ ‖second index sample - 0‖}) := by
          refine measure_mono ?_
          intro sample hlarge
          by_contra hnot
          have hnot_or :
              ¬ (sample ∈ {sample |
                    δ ≤ ‖first index sample - 0‖} ∨
                  sample ∈ {sample |
                    δ ≤ ‖second index sample - 0‖}) := by
            simpa [Set.mem_union] using hnot
          have hsmall := not_or.mp hnot_or
          have hfirst_lt : ‖first index sample - 0‖ < δ :=
            not_le.mp hsmall.1
          have hsecond_lt : ‖second index sample - 0‖ < δ :=
            not_le.mp hsmall.2
          have hmul_lt :
              ‖first index sample‖ * ‖second index sample‖ < ε := by
            have hfirst_norm_lt : ‖first index sample‖ < δ := by
              simpa using hfirst_lt
            have hsecond_norm_lt : ‖second index sample‖ < δ := by
              simpa using hsecond_lt
            calc
              ‖first index sample‖ * ‖second index sample‖
                  ≤ ‖first index sample‖ * δ := by
                    exact mul_le_mul_of_nonneg_left
                      (le_of_lt hsecond_norm_lt)
                      (norm_nonneg (first index sample))
              _ < δ * δ := by
                    exact mul_lt_mul_of_pos_right hfirst_norm_lt hδ_pos
              _ = ε := by
                    dsimp [δ]
                    simpa [sq] using Real.sq_sqrt (le_of_lt hε)
          have hprod_lt :
              ‖first index sample * second index sample - 0‖ < ε := by
            simpa [sub_zero, norm_mul] using hmul_lt
          exact (not_lt_of_ge hlarge) hprod_lt
    _ ≤ sampleLaw {sample | δ ≤ ‖first index sample - 0‖} +
          sampleLaw {sample | δ ≤ ‖second index sample - 0‖} :=
        measure_union_le _ _

/--
The product of two real-valued estimates that converge in measure to constants
converges in measure to the product of the constants.
-/
theorem tendstoInMeasure_mul_const
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (first second : Index -> Sample -> Real)
    (firstLimit secondLimit : Real)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => firstLimit))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => secondLimit)) :
    TendstoInMeasure sampleLaw
      (fun index sample => first index sample * second index sample) l
      (fun _sample => firstLimit * secondLimit) := by
  let firstError : Index -> Sample -> Real :=
    fun index sample => first index sample - firstLimit
  let secondError : Index -> Sample -> Real :=
    fun index sample => second index sample - secondLimit
  have hfirst_zero :
      TendstoInMeasure sampleLaw firstError l (fun _sample => (0 : Real)) :=
    tendstoInMeasure_sub_const_zero
      (sampleLaw := sampleLaw) (l := l) first firstLimit hfirst
  have hsecond_zero :
      TendstoInMeasure sampleLaw secondError l (fun _sample => (0 : Real)) :=
    tendstoInMeasure_sub_const_zero
      (sampleLaw := sampleLaw) (l := l) second secondLimit hsecond
  have hproduct_zero :
      TendstoInMeasure sampleLaw
        (fun index sample => firstError index sample * secondError index sample)
        l (fun _sample => (0 : Real)) :=
    tendstoInMeasure_mul_zero
      (sampleLaw := sampleLaw) (l := l)
      firstError secondError hfirst_zero hsecond_zero
  have hfirst_scaled :
      TendstoInMeasure sampleLaw
        (fun index sample => secondLimit * firstError index sample) l
        (fun _sample => (0 : Real)) :=
    tendstoInMeasure_const_mul_zero
      (sampleLaw := sampleLaw) (l := l)
      secondLimit firstError hfirst_zero
  have hsecond_scaled :
      TendstoInMeasure sampleLaw
        (fun index sample => firstLimit * secondError index sample) l
        (fun _sample => (0 : Real)) :=
    tendstoInMeasure_const_mul_zero
      (sampleLaw := sampleLaw) (l := l)
      firstLimit secondError hsecond_zero
  have hpartial_zero :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          firstError index sample * secondError index sample +
            secondLimit * firstError index sample)
        l (fun _sample => (0 : Real)) :=
    tendstoInMeasure_add_zero
      (sampleLaw := sampleLaw) (l := l)
      (fun index sample => firstError index sample * secondError index sample)
      (fun index sample => secondLimit * firstError index sample)
      hproduct_zero hfirst_scaled
  have htotal_zero :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          (firstError index sample * secondError index sample +
              secondLimit * firstError index sample) +
            firstLimit * secondError index sample)
        l (fun _sample => (0 : Real)) :=
    tendstoInMeasure_add_zero
      (sampleLaw := sampleLaw) (l := l)
      (fun index sample =>
        firstError index sample * secondError index sample +
          secondLimit * firstError index sample)
      (fun index sample => firstLimit * secondError index sample)
      hpartial_zero hsecond_scaled
  have hcentered :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          first index sample * second index sample -
            firstLimit * secondLimit)
        l (fun _sample => (0 : Real)) := by
    refine TendstoInMeasure.congr ?_ (ae_eq_refl _) htotal_zero
    intro index
    exact ae_of_all _ (fun sample => by
      change (first index sample - firstLimit) *
              (second index sample - secondLimit) +
            secondLimit * (first index sample - firstLimit) +
              firstLimit * (second index sample - secondLimit) =
            first index sample * second index sample -
              firstLimit * secondLimit
      ring)
  exact tendstoInMeasure_of_sub_const_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => first index sample * second index sample)
    (firstLimit * secondLimit) hcentered

/--
The quotient of two real-valued estimates that converge in measure to
constants converges in measure to the quotient of the constants when the
denominator limit is nonzero.
-/
theorem tendstoInMeasure_div_const
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (numerator denominator : Index -> Sample -> Real)
    (numeratorLimit denominatorLimit : Real)
    (hnumerator :
      TendstoInMeasure sampleLaw numerator l
        (fun _sample => numeratorLimit))
    (hdenominator :
      TendstoInMeasure sampleLaw denominator l
        (fun _sample => denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    TendstoInMeasure sampleLaw
      (fun index sample => numerator index sample / denominator index sample) l
      (fun _sample => numeratorLimit / denominatorLimit) := by
  have hinverse :
      TendstoInMeasure sampleLaw
        (fun index sample => (denominator index sample)⁻¹) l
        (fun _sample => denominatorLimit⁻¹) :=
    tendstoInMeasure_continuousAt_const
      (fun value : Real => value⁻¹) denominator denominatorLimit
      hdenominator (continuousAt_inv₀ hdenominatorLimit)
  simpa [div_eq_mul_inv] using
    tendstoInMeasure_mul_const
      (sampleLaw := sampleLaw) (l := l)
      numerator (fun index sample => (denominator index sample)⁻¹)
    numeratorLimit denominatorLimit⁻¹ hnumerator hinverse

/--
Negating a real-valued estimate that converges in measure to a constant gives
convergence in measure to the negated constant.
-/
theorem tendstoInMeasure_neg_const
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (estimate : Index -> Sample -> Real) (limit : Real)
    (hestimate :
      TendstoInMeasure sampleLaw estimate l (fun _sample => limit)) :
    TendstoInMeasure sampleLaw
      (fun index sample => -estimate index sample) l
      (fun _sample => -limit) := by
  exact tendstoInMeasure_continuousAt_const
    (fun value : Real => -value) estimate limit hestimate (by fun_prop)

/--
The difference of two real-valued estimates that converge in measure to
constants converges in measure to the difference of the constants.
-/
theorem tendstoInMeasure_sub_const
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (first second : Index -> Sample -> Real)
    (firstLimit secondLimit : Real)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => firstLimit))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => secondLimit)) :
    TendstoInMeasure sampleLaw
      (fun index sample => first index sample - second index sample) l
      (fun _sample => firstLimit - secondLimit) := by
  have hneg :
      TendstoInMeasure sampleLaw
        (fun index sample => -second index sample) l
        (fun _sample => -secondLimit) :=
    tendstoInMeasure_neg_const
      (sampleLaw := sampleLaw) (l := l) second secondLimit hsecond
  simpa [sub_eq_add_neg] using
    tendstoInMeasure_add_const
      (sampleLaw := sampleLaw) (l := l)
      first (fun index sample => -second index sample)
      firstLimit (-secondLimit) hfirst hneg

/-- The standard-error target is always nonnegative. -/
theorem standardError_nonneg (varianceTarget : Real) :
    0 ≤ standardError varianceTarget := by
  unfold standardError
  exact Real.sqrt_nonneg varianceTarget

/-- For a nonnegative variance target, the squared standard error recovers the variance. -/
theorem standardError_sq_eq_variance_of_nonneg
    (varianceTarget : Real) (hvariance : 0 ≤ varianceTarget) :
    standardError varianceTarget ^ 2 = varianceTarget := by
  unfold standardError
  exact Real.sq_sqrt hvariance

/-- A consistent scalar variance target gives a consistent standard-error target. -/
theorem tendsto_standardError_of_tendsto_variance
    {Index : Type*} {l : Filter Index}
    (varianceEstimate : Index -> Real) (varianceLimit : Real)
    (hvariance : Tendsto varianceEstimate l (nhds varianceLimit)) :
    Tendsto (fun index => standardError (varianceEstimate index)) l
      (nhds (standardError varianceLimit)) := by
  unfold standardError
  exact hvariance.sqrt

/--
A scalar variance estimate converging to a positive limit is eventually
positive.
-/
theorem eventually_variance_positive_of_tendsto_positive_limit
    {Index : Type*} {l : Filter Index}
    (varianceEstimate : Index -> Real) (varianceLimit : Real)
    (hvariance : Tendsto varianceEstimate l (nhds varianceLimit))
    (hvarianceLimit : 0 < varianceLimit) :
    ∀ᶠ index in l, 0 < varianceEstimate index := by
  exact hvariance.eventually (eventually_gt_nhds hvarianceLimit)

/--
A scalar variance estimate converging to a positive limit has eventually
positive standard-error estimates.
-/
theorem eventually_standardError_positive_of_tendsto_positive_variance_limit
    {Index : Type*} {l : Filter Index}
    (varianceEstimate : Index -> Real) (varianceLimit : Real)
    (hvariance : Tendsto varianceEstimate l (nhds varianceLimit))
    (hvarianceLimit : 0 < varianceLimit) :
    ∀ᶠ index in l, 0 < standardError (varianceEstimate index) := by
  filter_upwards
    [eventually_variance_positive_of_tendsto_positive_limit
      varianceEstimate varianceLimit hvariance hvarianceLimit] with index hpos
  unfold standardError
  exact Real.sqrt_pos.2 hpos

/--
Convergence in probability of a scalar variance target implies convergence in
probability of the corresponding standard-error target.
-/
theorem tendstoInMeasure_standardError_of_tendstoInMeasure_variance
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (varianceEstimate : Index -> Sample -> Real) (varianceLimit : Real)
    (hvariance :
      TendstoInMeasure sampleLaw varianceEstimate l
        (fun _sample => varianceLimit)) :
    TendstoInMeasure sampleLaw
      (fun index sample => standardError (varianceEstimate index sample)) l
      (fun _sample => standardError varianceLimit) := by
  have hcontinuous : ContinuousAt standardError varianceLimit := by
    unfold standardError
    exact Real.continuous_sqrt.continuousAt
  exact tendstoInMeasure_continuousAt_const
    standardError varianceEstimate varianceLimit hvariance hcontinuous

/--
If a standard-error estimate converges to a nonzero limit, its reciprocal
converges to the reciprocal limit.
-/
theorem tendsto_inverse_of_tendsto_standardError_ne_zero
    {Index : Type*} {l : Filter Index}
    (standardErrorEstimate : Index -> Real) (standardErrorLimit : Real)
    (hstandardError :
      Tendsto standardErrorEstimate l (nhds standardErrorLimit))
    (hstandardErrorLimit : standardErrorLimit ≠ 0) :
    Tendsto (fun index => (standardErrorEstimate index)⁻¹) l
      (nhds standardErrorLimit⁻¹) := by
  exact hstandardError.inv₀ hstandardErrorLimit

/--
Convergence in probability of a standard-error estimate to a nonzero limit
implies convergence in probability of the reciprocal estimate.
-/
theorem tendstoInMeasure_inverse_of_tendstoInMeasure_standardError_ne_zero
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (standardErrorEstimate : Index -> Sample -> Real)
    (standardErrorLimit : Real)
    (hstandardError :
      TendstoInMeasure sampleLaw standardErrorEstimate l
        (fun _sample => standardErrorLimit))
    (hstandardErrorLimit : standardErrorLimit ≠ 0) :
    TendstoInMeasure sampleLaw
      (fun index sample => (standardErrorEstimate index sample)⁻¹) l
      (fun _sample => standardErrorLimit⁻¹) := by
  exact tendstoInMeasure_continuousAt_const
    (fun standardErrorEstimate : Real => standardErrorEstimate⁻¹)
    standardErrorEstimate standardErrorLimit hstandardError
    (continuousAt_inv₀ hstandardErrorLimit)

/--
If a variance estimate converges and the limiting standard error is nonzero,
then the inverse standard-error estimate converges.
-/
theorem tendsto_inverseStandardError_of_tendsto_variance
    {Index : Type*} {l : Filter Index}
    (varianceEstimate : Index -> Real) (varianceLimit : Real)
    (hvariance : Tendsto varianceEstimate l (nhds varianceLimit))
    (hstandardErrorLimit : standardError varianceLimit ≠ 0) :
    Tendsto (fun index => (standardError (varianceEstimate index))⁻¹) l
      (nhds (standardError varianceLimit)⁻¹) := by
  exact tendsto_inverse_of_tendsto_standardError_ne_zero
    (fun index => standardError (varianceEstimate index))
    (standardError varianceLimit)
    (tendsto_standardError_of_tendsto_variance varianceEstimate
      varianceLimit hvariance)
    hstandardErrorLimit

/--
If a variance estimate converges to a positive limit, then the inverse
standard-error estimate converges to the reciprocal limiting standard error.
-/
theorem tendsto_inverseStandardError_of_tendsto_variance_pos_limit
    {Index : Type*} {l : Filter Index}
    (varianceEstimate : Index -> Real) (varianceLimit : Real)
    (hvariance : Tendsto varianceEstimate l (nhds varianceLimit))
    (hvarianceLimit : 0 < varianceLimit) :
    Tendsto (fun index => (standardError (varianceEstimate index))⁻¹) l
      (nhds (standardError varianceLimit)⁻¹) := by
  exact tendsto_inverseStandardError_of_tendsto_variance varianceEstimate
    varianceLimit hvariance
    ((show 0 < standardError varianceLimit by
      unfold standardError
      exact Real.sqrt_pos.2 hvarianceLimit).ne')

/--
Convergence in probability of a scalar variance target and a nonzero limiting
standard error imply convergence in probability of the inverse standard-error
target.
-/
theorem tendstoInMeasure_inverseStandardError_of_tendstoInMeasure_variance
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (varianceEstimate : Index -> Sample -> Real) (varianceLimit : Real)
    (hvariance :
      TendstoInMeasure sampleLaw varianceEstimate l
        (fun _sample => varianceLimit))
    (hstandardErrorLimit : standardError varianceLimit ≠ 0) :
    TendstoInMeasure sampleLaw
      (fun index sample => (standardError (varianceEstimate index sample))⁻¹) l
      (fun _sample => (standardError varianceLimit)⁻¹) := by
  have hstandardError :=
    tendstoInMeasure_standardError_of_tendstoInMeasure_variance
      varianceEstimate varianceLimit hvariance
  exact tendstoInMeasure_inverse_of_tendstoInMeasure_standardError_ne_zero
    (fun index sample => standardError (varianceEstimate index sample))
    (standardError varianceLimit) hstandardError hstandardErrorLimit

/--
Convergence in probability of a scalar variance target to a positive limiting
variance implies convergence in probability of the inverse standard-error
target.
-/
theorem tendstoInMeasure_inverseStandardError_of_tendstoInMeasure_variance_pos_limit
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (varianceEstimate : Index -> Sample -> Real) (varianceLimit : Real)
    (hvariance :
      TendstoInMeasure sampleLaw varianceEstimate l
        (fun _sample => varianceLimit))
    (hvarianceLimit : 0 < varianceLimit) :
    TendstoInMeasure sampleLaw
      (fun index sample => (standardError (varianceEstimate index sample))⁻¹) l
      (fun _sample => (standardError varianceLimit)⁻¹) := by
  exact tendstoInMeasure_inverseStandardError_of_tendstoInMeasure_variance
    varianceEstimate varianceLimit hvariance
    ((show 0 < standardError varianceLimit by
      unfold standardError
      exact Real.sqrt_pos.2 hvarianceLimit).ne')

/--
If heterogeneity and residual variance components converge, the oracle
variance target `V_H + V_E` converges.
-/
theorem tendsto_oracleVariance_of_tendsto_components
    {Index : Type*} {l : Filter Index}
    (heterogeneity residual : Index -> Real)
    (heterogeneityLimit residualLimit : Real)
    (hheterogeneity :
      Tendsto heterogeneity l (nhds heterogeneityLimit))
    (hresidual :
      Tendsto residual l (nhds residualLimit)) :
    Tendsto (fun index =>
      oracleVariance (heterogeneity index) (residual index)) l
      (nhds (oracleVariance heterogeneityLimit residualLimit)) := by
  unfold oracleVariance
  exact hheterogeneity.add hresidual

/--
If heterogeneity and residual variance components converge in probability, the
oracle variance target `V_H + V_E` converges in probability.
-/
theorem tendstoInMeasure_oracleVariance_of_tendstoInMeasure_components
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (heterogeneity residual : Index -> Sample -> Real)
    (heterogeneityLimit residualLimit : Real)
    (hheterogeneity :
      TendstoInMeasure sampleLaw heterogeneity l
        (fun _sample => heterogeneityLimit))
    (hresidual :
      TendstoInMeasure sampleLaw residual l
        (fun _sample => residualLimit)) :
    TendstoInMeasure sampleLaw
      (fun index sample =>
        oracleVariance (heterogeneity index sample) (residual index sample)) l
      (fun _sample => oracleVariance heterogeneityLimit residualLimit) := by
  unfold oracleVariance
  exact tendstoInMeasure_add_const
    (sampleLaw := sampleLaw) (l := l)
    heterogeneity residual heterogeneityLimit residualLimit
    hheterogeneity hresidual

/-- Convergence of oracle variance components implies convergence of the oracle standard error. -/
theorem tendsto_oracleStandardError_of_tendsto_components
    {Index : Type*} {l : Filter Index}
    (heterogeneity residual : Index -> Real)
    (heterogeneityLimit residualLimit : Real)
    (hheterogeneity :
      Tendsto heterogeneity l (nhds heterogeneityLimit))
    (hresidual :
      Tendsto residual l (nhds residualLimit)) :
    Tendsto (fun index =>
      standardError
        (oracleVariance (heterogeneity index) (residual index))) l
      (nhds
        (standardError
          (oracleVariance heterogeneityLimit residualLimit))) := by
  exact tendsto_standardError_of_tendsto_variance
    (fun index => oracleVariance (heterogeneity index) (residual index))
    (oracleVariance heterogeneityLimit residualLimit)
    (tendsto_oracleVariance_of_tendsto_components heterogeneity residual
      heterogeneityLimit residualLimit hheterogeneity hresidual)

/--
If oracle variance components converge to a positive oracle variance limit,
then the oracle variance estimates are eventually positive.
-/
theorem eventually_oracleVariance_positive_of_tendsto_components_pos_limit
    {Index : Type*} {l : Filter Index}
    (heterogeneity residual : Index -> Real)
    (heterogeneityLimit residualLimit : Real)
    (hheterogeneity :
      Tendsto heterogeneity l (nhds heterogeneityLimit))
    (hresidual :
      Tendsto residual l (nhds residualLimit))
    (horacleLimit_pos :
      0 < oracleVariance heterogeneityLimit residualLimit) :
    ∀ᶠ index in l,
      0 < oracleVariance (heterogeneity index) (residual index) := by
  exact eventually_variance_positive_of_tendsto_positive_limit
    (fun index => oracleVariance (heterogeneity index) (residual index))
    (oracleVariance heterogeneityLimit residualLimit)
    (tendsto_oracleVariance_of_tendsto_components heterogeneity residual
      heterogeneityLimit residualLimit hheterogeneity hresidual)
    horacleLimit_pos

/--
If oracle variance components converge to a positive oracle variance limit,
then the inverse oracle standard-error estimate converges.
-/
theorem tendsto_inverseOracleStandardError_of_tendsto_components_pos_limit
    {Index : Type*} {l : Filter Index}
    (heterogeneity residual : Index -> Real)
    (heterogeneityLimit residualLimit : Real)
    (hheterogeneity :
      Tendsto heterogeneity l (nhds heterogeneityLimit))
    (hresidual :
      Tendsto residual l (nhds residualLimit))
    (horacleLimit_pos :
      0 < oracleVariance heterogeneityLimit residualLimit) :
    Tendsto (fun index =>
      (standardError
        (oracleVariance (heterogeneity index) (residual index)))⁻¹) l
      (nhds
        (standardError
          (oracleVariance heterogeneityLimit residualLimit))⁻¹) := by
  exact tendsto_inverseStandardError_of_tendsto_variance_pos_limit
    (fun index => oracleVariance (heterogeneity index) (residual index))
    (oracleVariance heterogeneityLimit residualLimit)
    (tendsto_oracleVariance_of_tendsto_components heterogeneity residual
      heterogeneityLimit residualLimit hheterogeneity hresidual)
    horacleLimit_pos

/--
If oracle, projection-reduction, and target-drift terms converge, the
estimated-score variance target converges.
-/
theorem tendsto_estimatedScoreVariance_of_tendsto_components
    {Index : Type*} {l : Filter Index}
    (oracle projectionReduction targetDrift : Index -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle : Tendsto oracle l (nhds oracleLimit))
    (hprojection : Tendsto projectionReduction l (nhds projectionLimit))
    (hdrift : Tendsto targetDrift l (nhds targetDriftLimit)) :
    Tendsto (fun index =>
      estimatedScoreVariance (oracle index) (projectionReduction index)
        (targetDrift index)) l
      (nhds
        (estimatedScoreVariance oracleLimit projectionLimit
          targetDriftLimit)) := by
  unfold estimatedScoreVariance
  exact (horacle.sub hprojection).add hdrift

/--
If oracle, projection-reduction, and target-drift terms converge in
probability, the estimated-score variance target converges in probability.
-/
theorem tendstoInMeasure_estimatedScoreVariance_of_tendstoInMeasure_components
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit)) :
    TendstoInMeasure sampleLaw
      (fun index sample =>
        estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) (targetDrift index sample)) l
      (fun _sample =>
        estimatedScoreVariance oracleLimit projectionLimit
          targetDriftLimit) := by
  have hsub :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          oracle index sample - projectionReduction index sample) l
        (fun _sample => oracleLimit - projectionLimit) :=
    tendstoInMeasure_sub_const
      (sampleLaw := sampleLaw) (l := l)
      oracle projectionReduction oracleLimit projectionLimit
      horacle hprojection
  have hadd :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          (oracle index sample - projectionReduction index sample) +
            targetDrift index sample) l
        (fun _sample =>
          (oracleLimit - projectionLimit) + targetDriftLimit) :=
    tendstoInMeasure_add_const
      (sampleLaw := sampleLaw) (l := l)
      (fun index sample =>
        oracle index sample - projectionReduction index sample)
      targetDrift (oracleLimit - projectionLimit) targetDriftLimit
      hsub hdrift
  simpa [estimatedScoreVariance] using hadd

/--
Convergence of oracle, projection-reduction, and target-drift terms implies
convergence of the estimated-score standard error.
-/
theorem tendsto_estimatedScoreStandardError_of_tendsto_components
    {Index : Type*} {l : Filter Index}
    (oracle projectionReduction targetDrift : Index -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle : Tendsto oracle l (nhds oracleLimit))
    (hprojection : Tendsto projectionReduction l (nhds projectionLimit))
    (hdrift : Tendsto targetDrift l (nhds targetDriftLimit)) :
    Tendsto (fun index =>
      standardError
        (estimatedScoreVariance (oracle index) (projectionReduction index)
          (targetDrift index))) l
      (nhds
        (standardError
          (estimatedScoreVariance oracleLimit projectionLimit
            targetDriftLimit))) := by
  exact tendsto_standardError_of_tendsto_variance
    (fun index =>
      estimatedScoreVariance (oracle index) (projectionReduction index)
        (targetDrift index))
    (estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit)
    (tendsto_estimatedScoreVariance_of_tendsto_components oracle
      projectionReduction targetDrift oracleLimit projectionLimit
      targetDriftLimit horacle hprojection hdrift)

/--
If estimated-score variance components converge to a positive adjusted
variance limit, then the adjusted variance estimates are eventually positive.
-/
theorem eventually_estimatedScoreVariance_positive_of_tendsto_components_pos_limit
    {Index : Type*} {l : Filter Index}
    (oracle projectionReduction targetDrift : Index -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle : Tendsto oracle l (nhds oracleLimit))
    (hprojection : Tendsto projectionReduction l (nhds projectionLimit))
    (hdrift : Tendsto targetDrift l (nhds targetDriftLimit))
    (hadjustedLimit_pos :
      0 < estimatedScoreVariance oracleLimit projectionLimit
        targetDriftLimit) :
    ∀ᶠ index in l,
      0 < estimatedScoreVariance (oracle index) (projectionReduction index)
        (targetDrift index) := by
  exact eventually_variance_positive_of_tendsto_positive_limit
    (fun index =>
      estimatedScoreVariance (oracle index) (projectionReduction index)
        (targetDrift index))
    (estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit)
    (tendsto_estimatedScoreVariance_of_tendsto_components oracle
      projectionReduction targetDrift oracleLimit projectionLimit
      targetDriftLimit horacle hprojection hdrift)
    hadjustedLimit_pos

/--
If estimated-score variance components converge to a positive adjusted
variance limit, then the inverse adjusted standard-error estimate converges.
-/
theorem tendsto_inverseEstimatedScoreStandardError_of_tendsto_components_pos_limit
    {Index : Type*} {l : Filter Index}
    (oracle projectionReduction targetDrift : Index -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle : Tendsto oracle l (nhds oracleLimit))
    (hprojection : Tendsto projectionReduction l (nhds projectionLimit))
    (hdrift : Tendsto targetDrift l (nhds targetDriftLimit))
    (hadjustedLimit_pos :
      0 < estimatedScoreVariance oracleLimit projectionLimit
        targetDriftLimit) :
    Tendsto (fun index =>
      (standardError
        (estimatedScoreVariance (oracle index) (projectionReduction index)
          (targetDrift index)))⁻¹) l
      (nhds
        (standardError
          (estimatedScoreVariance oracleLimit projectionLimit
            targetDriftLimit))⁻¹) := by
  exact tendsto_inverseStandardError_of_tendsto_variance_pos_limit
    (fun index =>
      estimatedScoreVariance (oracle index) (projectionReduction index)
        (targetDrift index))
    (estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit)
    (tendsto_estimatedScoreVariance_of_tendsto_components oracle
      projectionReduction targetDrift oracleLimit projectionLimit
      targetDriftLimit horacle hprojection hdrift)
    hadjustedLimit_pos

/--
Fixed-law estimated-score variance convergence is the zero-drift specialization
of the generic estimated-score variance limit.
-/
theorem tendsto_fixedLawEstimatedScoreVariance_of_tendsto_components
    {Index : Type*} {l : Filter Index}
    (oracle projectionReduction : Index -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle : Tendsto oracle l (nhds oracleLimit))
    (hprojection : Tendsto projectionReduction l (nhds projectionLimit)) :
    Tendsto (fun index =>
      estimatedScoreVariance (oracle index) (projectionReduction index) 0) l
      (nhds (estimatedScoreVariance oracleLimit projectionLimit 0)) := by
  exact tendsto_estimatedScoreVariance_of_tendsto_components
    oracle projectionReduction (fun _index => (0 : Real))
    oracleLimit projectionLimit 0 horacle hprojection tendsto_const_nhds

/--
Fixed-law estimated-score variance convergence in probability is the zero-drift
specialization of the generic estimated-score variance convergence in
probability.
-/
theorem tendstoInMeasure_fixedLawEstimatedScoreVariance_of_tendstoInMeasure_components
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (oracle projectionReduction : Index -> Sample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit)) :
    TendstoInMeasure sampleLaw
      (fun index sample =>
        estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) 0) l
      (fun _sample => estimatedScoreVariance oracleLimit projectionLimit 0) := by
  exact tendstoInMeasure_estimatedScoreVariance_of_tendstoInMeasure_components
    (sampleLaw := sampleLaw) (l := l)
    oracle projectionReduction (fun _index _sample => (0 : Real))
    oracleLimit projectionLimit 0 horacle hprojection
    (tendstoInMeasure_const_const (sampleLaw := sampleLaw) (l := l) (0 : Real))

/--
If fixed-law estimated-score components converge to a positive adjusted
variance limit, then the inverse fixed-law adjusted standard-error estimate
converges.
-/
theorem tendsto_inverseFixedLawEstimatedScoreStandardError_of_tendsto_components_pos_limit
    {Index : Type*} {l : Filter Index}
    (oracle projectionReduction : Index -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle : Tendsto oracle l (nhds oracleLimit))
    (hprojection : Tendsto projectionReduction l (nhds projectionLimit))
    (hadjustedLimit_pos :
      0 < estimatedScoreVariance oracleLimit projectionLimit 0) :
    Tendsto (fun index =>
      (standardError
        (estimatedScoreVariance (oracle index) (projectionReduction index)
          0))⁻¹) l
      (nhds
        (standardError
          (estimatedScoreVariance oracleLimit projectionLimit 0))⁻¹) := by
  exact tendsto_inverseEstimatedScoreStandardError_of_tendsto_components_pos_limit
    oracle projectionReduction (fun _index => (0 : Real))
    oracleLimit projectionLimit 0 horacle hprojection tendsto_const_nhds
    hadjustedLimit_pos

/--
Consistent scalar arm-share, arm-variance, and denominator estimates give a
consistent two-arm residual variance target, provided the denominator limit is
nonzero.
-/
theorem tendsto_twoArmWeightedResidualVariance_of_tendsto
    {Index : Type*} {l : Filter Index}
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (hdenominator :
      Tendsto denominator l (nhds denominatorLimit))
    (htreatedShare :
      Tendsto treatedShare l (nhds treatedShareLimit))
    (hcontrolShare :
      Tendsto controlShare l (nhds controlShareLimit))
    (htreatedVariance :
      Tendsto treatedArmVariance l (nhds treatedVarianceLimit))
    (hcontrolVariance :
      Tendsto controlArmVariance l (nhds controlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index =>
      twoArmWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedArmVariance index) (controlArmVariance index)) l
      (nhds
        (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
          controlShareLimit treatedVarianceLimit controlVarianceLimit)) := by
  unfold twoArmWeightedResidualVariance
  exact
    ((htreatedShare.mul htreatedVariance).add
        (hcontrolShare.mul hcontrolVariance)).div
      (hdenominator.pow 2) (pow_ne_zero 2 hdenominatorLimit)

/--
Componentwise convergence in probability of the scalar arm shares, arm
variance proxies, and denominator gives convergence in probability of the
assembled two-arm residual variance target.
-/
theorem tendstoInMeasure_twoArmWeightedResidualVariance_of_tendstoInMeasure
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (hdenominator :
      TendstoInMeasure sampleLaw denominator l
        (fun _sample => denominatorLimit))
    (htreatedShare :
      TendstoInMeasure sampleLaw treatedShare l
        (fun _sample => treatedShareLimit))
    (hcontrolShare :
      TendstoInMeasure sampleLaw controlShare l
        (fun _sample => controlShareLimit))
    (htreatedVariance :
      TendstoInMeasure sampleLaw treatedArmVariance l
        (fun _sample => treatedVarianceLimit))
    (hcontrolVariance :
      TendstoInMeasure sampleLaw controlArmVariance l
        (fun _sample => controlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    TendstoInMeasure sampleLaw
      (fun index sample =>
        twoArmWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedArmVariance index sample) (controlArmVariance index sample))
      l
      (fun _sample =>
        twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
          controlShareLimit treatedVarianceLimit controlVarianceLimit) := by
  have htreatedProduct :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          treatedShare index sample * treatedArmVariance index sample) l
        (fun _sample => treatedShareLimit * treatedVarianceLimit) :=
    tendstoInMeasure_mul_const
      (sampleLaw := sampleLaw) (l := l)
      treatedShare treatedArmVariance treatedShareLimit treatedVarianceLimit
      htreatedShare htreatedVariance
  have hcontrolProduct :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          controlShare index sample * controlArmVariance index sample) l
        (fun _sample => controlShareLimit * controlVarianceLimit) :=
    tendstoInMeasure_mul_const
      (sampleLaw := sampleLaw) (l := l)
      controlShare controlArmVariance controlShareLimit controlVarianceLimit
      hcontrolShare hcontrolVariance
  have hnumerator :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          treatedShare index sample * treatedArmVariance index sample +
            controlShare index sample * controlArmVariance index sample) l
        (fun _sample =>
          treatedShareLimit * treatedVarianceLimit +
            controlShareLimit * controlVarianceLimit) :=
    tendstoInMeasure_add_const
      (sampleLaw := sampleLaw) (l := l)
      (fun index sample =>
        treatedShare index sample * treatedArmVariance index sample)
      (fun index sample =>
        controlShare index sample * controlArmVariance index sample)
      (treatedShareLimit * treatedVarianceLimit)
      (controlShareLimit * controlVarianceLimit)
      htreatedProduct hcontrolProduct
  have hdenominatorSq :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          denominator index sample * denominator index sample) l
        (fun _sample => denominatorLimit * denominatorLimit) :=
    tendstoInMeasure_mul_const
      (sampleLaw := sampleLaw) (l := l)
      denominator denominator denominatorLimit denominatorLimit
      hdenominator hdenominator
  have hratio :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          (treatedShare index sample * treatedArmVariance index sample +
              controlShare index sample * controlArmVariance index sample) /
            (denominator index sample * denominator index sample))
        l
        (fun _sample =>
          (treatedShareLimit * treatedVarianceLimit +
              controlShareLimit * controlVarianceLimit) /
            (denominatorLimit * denominatorLimit)) :=
    tendstoInMeasure_div_const
      (sampleLaw := sampleLaw) (l := l)
      (fun index sample =>
        treatedShare index sample * treatedArmVariance index sample +
          controlShare index sample * controlArmVariance index sample)
      (fun index sample =>
        denominator index sample * denominator index sample)
      (treatedShareLimit * treatedVarianceLimit +
        controlShareLimit * controlVarianceLimit)
      (denominatorLimit * denominatorLimit)
      hnumerator hdenominatorSq
      (mul_ne_zero hdenominatorLimit hdenominatorLimit)
  simpa [twoArmWeightedResidualVariance, pow_two] using hratio

/--
Consistent scalar two-arm residual variance targets give consistent two-arm
residual standard-error targets.
-/
theorem tendsto_twoArmResidualStandardError_of_tendsto
    {Index : Type*} {l : Filter Index}
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (hdenominator :
      Tendsto denominator l (nhds denominatorLimit))
    (htreatedShare :
      Tendsto treatedShare l (nhds treatedShareLimit))
    (hcontrolShare :
      Tendsto controlShare l (nhds controlShareLimit))
    (htreatedVariance :
      Tendsto treatedArmVariance l (nhds treatedVarianceLimit))
    (hcontrolVariance :
      Tendsto controlArmVariance l (nhds controlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index =>
      standardError
        (twoArmWeightedResidualVariance (denominator index)
          (treatedShare index) (controlShare index)
          (treatedArmVariance index) (controlArmVariance index))) l
      (nhds
        (standardError
          (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
            controlShareLimit treatedVarianceLimit controlVarianceLimit))) := by
  exact tendsto_standardError_of_tendsto_variance
    (fun index =>
      twoArmWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedArmVariance index) (controlArmVariance index))
    (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit)
    (tendsto_twoArmWeightedResidualVariance_of_tendsto denominator
      treatedShare controlShare treatedArmVariance controlArmVariance
      denominatorLimit treatedShareLimit controlShareLimit treatedVarianceLimit
      controlVarianceLimit hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit)

/--
Consistent scalar two-arm residual variance targets with a positive limiting
variance are eventually positive.
-/
theorem eventually_twoArmWeightedResidualVariance_positive_of_tendsto_pos_limit
    {Index : Type*} {l : Filter Index}
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (hdenominator :
      Tendsto denominator l (nhds denominatorLimit))
    (htreatedShare :
      Tendsto treatedShare l (nhds treatedShareLimit))
    (hcontrolShare :
      Tendsto controlShare l (nhds controlShareLimit))
    (htreatedVariance :
      Tendsto treatedArmVariance l (nhds treatedVarianceLimit))
    (hcontrolVariance :
      Tendsto controlArmVariance l (nhds controlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0)
    (hvarianceLimit_pos :
      0 < twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedVarianceLimit controlVarianceLimit) :
    ∀ᶠ index in l,
      0 < twoArmWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedArmVariance index) (controlArmVariance index) := by
  exact eventually_variance_positive_of_tendsto_positive_limit
    (fun index =>
      twoArmWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedArmVariance index) (controlArmVariance index))
    (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit)
    (tendsto_twoArmWeightedResidualVariance_of_tendsto denominator
      treatedShare controlShare treatedArmVariance controlArmVariance
      denominatorLimit treatedShareLimit controlShareLimit treatedVarianceLimit
      controlVarianceLimit hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit)
    hvarianceLimit_pos

/--
Consistent scalar two-arm residual variance targets with a positive limiting
variance give convergent inverse residual standard-error estimates.
-/
theorem tendsto_inverseTwoArmResidualStandardError_of_tendsto_pos_limit
    {Index : Type*} {l : Filter Index}
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (hdenominator :
      Tendsto denominator l (nhds denominatorLimit))
    (htreatedShare :
      Tendsto treatedShare l (nhds treatedShareLimit))
    (hcontrolShare :
      Tendsto controlShare l (nhds controlShareLimit))
    (htreatedVariance :
      Tendsto treatedArmVariance l (nhds treatedVarianceLimit))
    (hcontrolVariance :
      Tendsto controlArmVariance l (nhds controlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0)
    (hvarianceLimit_pos :
      0 < twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedVarianceLimit controlVarianceLimit) :
    Tendsto (fun index =>
      (standardError
        (twoArmWeightedResidualVariance (denominator index)
          (treatedShare index) (controlShare index)
          (treatedArmVariance index) (controlArmVariance index)))⁻¹) l
      (nhds
        (standardError
          (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
            controlShareLimit treatedVarianceLimit controlVarianceLimit))⁻¹) := by
  exact tendsto_inverseStandardError_of_tendsto_variance_pos_limit
    (fun index =>
      twoArmWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedArmVariance index) (controlArmVariance index))
    (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit)
    (tendsto_twoArmWeightedResidualVariance_of_tendsto denominator
      treatedShare controlShare treatedArmVariance controlArmVariance
      denominatorLimit treatedShareLimit controlShareLimit treatedVarianceLimit
      controlVarianceLimit hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit)
    hvarianceLimit_pos

/--
The PATT scalar residual variance limit is the same continuous-mapping result
with treated direct and matched-control variance components.
-/
theorem tendsto_pattWeightedResidualVariance_of_tendsto
    {Index : Type*} {l : Filter Index}
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (hdenominator :
      Tendsto denominator l (nhds denominatorLimit))
    (htreatedShare :
      Tendsto treatedShare l (nhds treatedShareLimit))
    (hcontrolShare :
      Tendsto controlShare l (nhds controlShareLimit))
    (htreatedVariance :
      Tendsto treatedDirectVariance l (nhds treatedDirectVarianceLimit))
    (hcontrolVariance :
      Tendsto matchedControlVariance l (nhds matchedControlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index =>
      pattWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedDirectVariance index) (matchedControlVariance index)) l
      (nhds
        (pattWeightedResidualVariance denominatorLimit treatedShareLimit
          controlShareLimit treatedDirectVarianceLimit
          matchedControlVarianceLimit)) := by
  rw [pattWeightedResidualVariance_eq_twoArmWeightedResidualVariance]
  exact tendsto_twoArmWeightedResidualVariance_of_tendsto
    denominator treatedShare controlShare treatedDirectVariance
    matchedControlVariance denominatorLimit treatedShareLimit
    controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
    hdenominator htreatedShare hcontrolShare htreatedVariance
    hcontrolVariance hdenominatorLimit

/--
Componentwise convergence in probability of the scalar PATT shares, residual
variance proxies, and denominator gives convergence in probability of the
assembled one-sided PATT residual variance target.
-/
theorem tendstoInMeasure_pattWeightedResidualVariance_of_tendstoInMeasure
    {Index Sample : Type*} [MeasurableSpace Sample]
    {sampleLaw : Measure Sample} {l : Filter Index}
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (hdenominator :
      TendstoInMeasure sampleLaw denominator l
        (fun _sample => denominatorLimit))
    (htreatedShare :
      TendstoInMeasure sampleLaw treatedShare l
        (fun _sample => treatedShareLimit))
    (hcontrolShare :
      TendstoInMeasure sampleLaw controlShare l
        (fun _sample => controlShareLimit))
    (htreatedVariance :
      TendstoInMeasure sampleLaw treatedDirectVariance l
        (fun _sample => treatedDirectVarianceLimit))
    (hcontrolVariance :
      TendstoInMeasure sampleLaw matchedControlVariance l
        (fun _sample => matchedControlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    TendstoInMeasure sampleLaw
      (fun index sample =>
        pattWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedDirectVariance index sample)
          (matchedControlVariance index sample))
      l
      (fun _sample =>
        pattWeightedResidualVariance denominatorLimit treatedShareLimit
          controlShareLimit treatedDirectVarianceLimit
          matchedControlVarianceLimit) := by
  simpa [pattWeightedResidualVariance_eq_twoArmWeightedResidualVariance] using
    tendstoInMeasure_twoArmWeightedResidualVariance_of_tendstoInMeasure
      (sampleLaw := sampleLaw) (l := l)
      denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit

/--
Consistent scalar PATT residual variance targets give consistent PATT residual
standard-error targets.
-/
theorem tendsto_pattResidualStandardError_of_tendsto
    {Index : Type*} {l : Filter Index}
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (hdenominator :
      Tendsto denominator l (nhds denominatorLimit))
    (htreatedShare :
      Tendsto treatedShare l (nhds treatedShareLimit))
    (hcontrolShare :
      Tendsto controlShare l (nhds controlShareLimit))
    (htreatedVariance :
      Tendsto treatedDirectVariance l (nhds treatedDirectVarianceLimit))
    (hcontrolVariance :
      Tendsto matchedControlVariance l (nhds matchedControlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index =>
      standardError
        (pattWeightedResidualVariance (denominator index)
          (treatedShare index) (controlShare index)
          (treatedDirectVariance index) (matchedControlVariance index))) l
      (nhds
        (standardError
          (pattWeightedResidualVariance denominatorLimit treatedShareLimit
            controlShareLimit treatedDirectVarianceLimit
            matchedControlVarianceLimit))) := by
  exact tendsto_standardError_of_tendsto_variance
    (fun index =>
      pattWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedDirectVariance index) (matchedControlVariance index))
    (pattWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    (tendsto_pattWeightedResidualVariance_of_tendsto denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance
      denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit hdenominator
      htreatedShare hcontrolShare htreatedVariance hcontrolVariance
      hdenominatorLimit)

/--
Consistent scalar PATT residual variance targets with a positive limiting
variance are eventually positive.
-/
theorem eventually_pattWeightedResidualVariance_positive_of_tendsto_pos_limit
    {Index : Type*} {l : Filter Index}
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (hdenominator :
      Tendsto denominator l (nhds denominatorLimit))
    (htreatedShare :
      Tendsto treatedShare l (nhds treatedShareLimit))
    (hcontrolShare :
      Tendsto controlShare l (nhds controlShareLimit))
    (htreatedVariance :
      Tendsto treatedDirectVariance l (nhds treatedDirectVarianceLimit))
    (hcontrolVariance :
      Tendsto matchedControlVariance l (nhds matchedControlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0)
    (hvarianceLimit_pos :
      0 < pattWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedDirectVarianceLimit
        matchedControlVarianceLimit) :
    ∀ᶠ index in l,
      0 < pattWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedDirectVariance index) (matchedControlVariance index) := by
  exact eventually_variance_positive_of_tendsto_positive_limit
    (fun index =>
      pattWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedDirectVariance index) (matchedControlVariance index))
    (pattWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    (tendsto_pattWeightedResidualVariance_of_tendsto denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance
      denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit hdenominator
      htreatedShare hcontrolShare htreatedVariance hcontrolVariance
      hdenominatorLimit)
    hvarianceLimit_pos

/--
Consistent scalar PATT residual variance targets with a positive limiting
variance give convergent inverse residual standard-error estimates.
-/
theorem tendsto_inversePATTResidualStandardError_of_tendsto_pos_limit
    {Index : Type*} {l : Filter Index}
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (hdenominator :
      Tendsto denominator l (nhds denominatorLimit))
    (htreatedShare :
      Tendsto treatedShare l (nhds treatedShareLimit))
    (hcontrolShare :
      Tendsto controlShare l (nhds controlShareLimit))
    (htreatedVariance :
      Tendsto treatedDirectVariance l (nhds treatedDirectVarianceLimit))
    (hcontrolVariance :
      Tendsto matchedControlVariance l (nhds matchedControlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0)
    (hvarianceLimit_pos :
      0 < pattWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedDirectVarianceLimit
        matchedControlVarianceLimit) :
    Tendsto (fun index =>
      (standardError
        (pattWeightedResidualVariance (denominator index)
          (treatedShare index) (controlShare index)
          (treatedDirectVariance index) (matchedControlVariance index)))⁻¹) l
      (nhds
        (standardError
          (pattWeightedResidualVariance denominatorLimit treatedShareLimit
            controlShareLimit treatedDirectVarianceLimit
            matchedControlVarianceLimit))⁻¹) := by
  exact tendsto_inverseStandardError_of_tendsto_variance_pos_limit
    (fun index =>
      pattWeightedResidualVariance (denominator index)
        (treatedShare index) (controlShare index)
        (treatedDirectVariance index) (matchedControlVariance index))
    (pattWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    (tendsto_pattWeightedResidualVariance_of_tendsto denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance
      denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit hdenominator
      htreatedShare hcontrolShare htreatedVariance hcontrolVariance
      hdenominatorLimit)
    hvarianceLimit_pos

end WDSM
end Matching
end StatInference
