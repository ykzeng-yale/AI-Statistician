import StatInference.Matching.WDSM.FiniteLyapunovLindeberg
import Mathlib.Tactic.Ring

/-!
# Residual coefficient Lyapunov bounds

This module specializes the finite Lyapunov-to-Lindeberg algebra to residual
arrays of the WDSM form `coefficient * residual`.  It proves the deterministic
envelope step that reduces the cubic Lyapunov condition for weighted residual
contributions to a coefficient envelope times a residual third-moment sum.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Unit : Type*}

/-- Cubic Lyapunov sum for residual contributions `coefficient * residual`. -/
noncomputable def residualCoefficientCubicMomentSum
    (sample : Finset Unit) (weight coefficient residual : Unit -> Real) :
    Real :=
  lyapunovCubicMomentSum sample weight
    (fun unit => coefficient unit * residual unit)

/-- Weighted residual third-moment sum without coefficient powers. -/
noncomputable def residualThirdMomentSum
    (sample : Finset Unit) (weight residual : Unit -> Real) : Real :=
  ∑ unit ∈ sample, weight unit * |residual unit| ^ 3

/-- The residual coefficient cubic sum expands into coefficient and residual powers. -/
theorem residualCoefficientCubicMomentSum_eq_abs_coeff_cube
    (sample : Finset Unit) (weight coefficient residual : Unit -> Real) :
    residualCoefficientCubicMomentSum sample weight coefficient residual =
      ∑ unit ∈ sample,
        weight unit * (|coefficient unit| ^ 3 * |residual unit| ^ 3) := by
  unfold residualCoefficientCubicMomentSum lyapunovCubicMomentSum
  exact Finset.sum_congr rfl
    (fun unit _hunit => by
      rw [abs_mul, mul_pow])

/-- Residual coefficient cubic sums are nonnegative under nonnegative weights. -/
theorem residualCoefficientCubicMomentSum_nonneg
    (sample : Finset Unit) (weight coefficient residual : Unit -> Real)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit) :
    0 ≤ residualCoefficientCubicMomentSum sample weight coefficient residual := by
  unfold residualCoefficientCubicMomentSum lyapunovCubicMomentSum
  exact Finset.sum_nonneg
    (fun unit hunit =>
      mul_nonneg (hweight_nonneg unit hunit)
        (pow_nonneg
          (abs_nonneg (coefficient unit * residual unit)) 3))

/--
If all residual coefficients are bounded by a common envelope, the coefficient
cubic moment is bounded by the envelope cubed times the residual third moment.
-/
theorem residualCoefficientCubicMomentSum_le_envelope_cube_mul_residualThirdMomentSum
    (sample : Finset Unit) (weight coefficient residual : Unit -> Real)
    (envelope : Real)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hcoefficient_bound :
      ∀ unit, unit ∈ sample -> |coefficient unit| ≤ envelope) :
    residualCoefficientCubicMomentSum sample weight coefficient residual ≤
      envelope ^ 3 * residualThirdMomentSum sample weight residual := by
  rw [residualCoefficientCubicMomentSum_eq_abs_coeff_cube]
  unfold residualThirdMomentSum
  calc
    (∑ unit ∈ sample,
        weight unit * (|coefficient unit| ^ 3 * |residual unit| ^ 3)) ≤
        ∑ unit ∈ sample,
          envelope ^ 3 * (weight unit * |residual unit| ^ 3) := by
          refine Finset.sum_le_sum ?_
          intro unit hunit
          have hcoeff_pow :
              |coefficient unit| ^ 3 ≤ envelope ^ 3 :=
            pow_le_pow_left₀ (abs_nonneg (coefficient unit))
              (hcoefficient_bound unit hunit) 3
          have hres_nonneg : 0 ≤ |residual unit| ^ 3 :=
            pow_nonneg (abs_nonneg (residual unit)) 3
          have hcoeff_res :
              |coefficient unit| ^ 3 * |residual unit| ^ 3 ≤
                envelope ^ 3 * |residual unit| ^ 3 :=
            mul_le_mul_of_nonneg_right hcoeff_pow hres_nonneg
          calc
            weight unit *
                (|coefficient unit| ^ 3 * |residual unit| ^ 3) ≤
                weight unit *
                  (envelope ^ 3 * |residual unit| ^ 3) :=
              mul_le_mul_of_nonneg_left hcoeff_res
                (hweight_nonneg unit hunit)
            _ = envelope ^ 3 * (weight unit * |residual unit| ^ 3) := by
              ring
    _ = envelope ^ 3 * (∑ unit ∈ sample,
          weight unit * |residual unit| ^ 3) := by
      rw [Finset.mul_sum]

/--
Coefficient-envelope convergence implies the cubic Lyapunov sum for residual
contributions tends to zero.
-/
theorem tendsto_residualCoefficientCubicMomentSum_zero_of_envelope
    {Index : Type*} {l : Filter Index}
    (sample : Index -> Finset Unit)
    (weight coefficient residual : Index -> Unit -> Real)
    (envelope : Index -> Real)
    (hweight_nonneg :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> 0 ≤ weight index unit)
    (hcoefficient_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |coefficient index unit| ≤ envelope index)
    (henvelope_bound :
      Tendsto
        (fun index =>
          envelope index ^ 3 *
            residualThirdMomentSum (sample index) (weight index)
              (residual index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        residualCoefficientCubicMomentSum (sample index) (weight index)
          (coefficient index) (residual index))
      l (nhds 0) := by
  exact squeeze_zero'
    (hweight_nonneg.mono
      (fun index hweight =>
        residualCoefficientCubicMomentSum_nonneg (sample index)
          (weight index) (coefficient index) (residual index) hweight))
    ((hweight_nonneg.and hcoefficient_bound).mono
      (fun index hboth => by
        rcases hboth with ⟨hweight, hcoeff⟩
        exact
          residualCoefficientCubicMomentSum_le_envelope_cube_mul_residualThirdMomentSum
            (sample index) (weight index) (coefficient index)
            (residual index) (envelope index) hweight hcoeff))
    henvelope_bound

/--
Coefficient-envelope convergence plus finite Lyapunov-to-Lindeberg gives the
quadratic residual Lindeberg tail convergence.
-/
theorem tendsto_residual_lindeberg_tail_zero_of_envelope
    {Index : Type*} {l : Filter Index}
    (sample : Index -> Finset Unit)
    (weight coefficient residual : Index -> Unit -> Real)
    (envelope : Index -> Real)
    {epsilon : Real} (hepsilon : 0 < epsilon)
    (hweight_nonneg :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> 0 ≤ weight index unit)
    (hcoefficient_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |coefficient index unit| ≤ envelope index)
    (hscaled_envelope_bound :
      Tendsto
        (fun index =>
          epsilon⁻¹ *
            (envelope index ^ 3 *
              residualThirdMomentSum (sample index) (weight index)
                (residual index)))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        lindebergQuadraticTailSum (sample index) (weight index)
          (fun unit => coefficient index unit * residual index unit)
          epsilon)
      l (nhds 0) := by
  have hlyapunov :
      Tendsto
        (fun index =>
          epsilon⁻¹ *
            residualCoefficientCubicMomentSum (sample index) (weight index)
              (coefficient index) (residual index))
        l (nhds 0) := by
    exact squeeze_zero'
      (hweight_nonneg.mono
        (fun index hweight =>
          mul_nonneg (inv_nonneg.mpr (le_of_lt hepsilon))
            (residualCoefficientCubicMomentSum_nonneg (sample index)
              (weight index) (coefficient index) (residual index) hweight)))
      ((hweight_nonneg.and hcoefficient_bound).mono
        (fun index hboth => by
          rcases hboth with ⟨hweight, hcoeff⟩
          exact mul_le_mul_of_nonneg_left
            (residualCoefficientCubicMomentSum_le_envelope_cube_mul_residualThirdMomentSum
              (sample index) (weight index) (coefficient index)
              (residual index) (envelope index) hweight hcoeff)
            (inv_nonneg.mpr (le_of_lt hepsilon))))
      hscaled_envelope_bound
  exact
    tendsto_lindebergQuadraticTailSum_zero_of_eventually_nonneg_of_lyapunov
      sample weight
      (fun index unit => coefficient index unit * residual index unit)
      hepsilon hweight_nonneg hlyapunov

end WDSM
end Matching
end StatInference
