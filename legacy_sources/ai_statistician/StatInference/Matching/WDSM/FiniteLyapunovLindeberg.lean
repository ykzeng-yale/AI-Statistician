import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import StatInference.Matching.WDSM.SqueezeAlgebra

/-!
# Finite Lyapunov-to-Lindeberg tail bounds

This module proves the deterministic finite-array inequality behind the
standard Lyapunov-to-Lindeberg step.  It is probability-free: later martingale
CLT work can combine this checked bound with conditional moment statements.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {α : Type*}

/-- Finite quadratic tail sum appearing in a Lindeberg condition. -/
noncomputable def lindebergQuadraticTailSum
    (s : Finset α) (weight value : α -> Real) (epsilon : Real) : Real :=
  ∑ i ∈ s, weight i * if epsilon < |value i| then value i ^ 2 else 0

/-- Finite cubic Lyapunov moment sum. -/
noncomputable def lyapunovCubicMomentSum
    (s : Finset α) (weight value : α -> Real) : Real :=
  ∑ i ∈ s, weight i * |value i| ^ 3

/-- Quadratic tail sums are nonnegative under nonnegative weights. -/
theorem lindebergQuadraticTailSum_nonneg
    (s : Finset α) (weight value : α -> Real) (epsilon : Real)
    (hweight_nonneg : ∀ i, i ∈ s -> 0 ≤ weight i) :
    0 ≤ lindebergQuadraticTailSum s weight value epsilon := by
  unfold lindebergQuadraticTailSum
  exact Finset.sum_nonneg
    (fun i hi => by
      by_cases htail : epsilon < |value i|
      · simp [htail, mul_nonneg (hweight_nonneg i hi)
          (sq_nonneg (value i))]
      · simp [htail])

/--
Pointwise tail inequality: on the event `epsilon < |x|`, the squared term is
bounded by `epsilon^{-1}` times the cubic absolute moment.
-/
theorem sq_le_inv_mul_abs_cube_of_epsilon_lt_abs
    {epsilon x : Real} (hepsilon : 0 < epsilon)
    (htail : epsilon < |x|) :
    x ^ 2 ≤ epsilon⁻¹ * |x| ^ 3 := by
  have hepsilon_le_abs : epsilon ≤ |x| := le_of_lt htail
  have habs_sq_nonneg : 0 ≤ |x| ^ 2 := pow_nonneg (abs_nonneg x) 2
  have hmul :
      epsilon * |x| ^ 2 ≤ |x| * |x| ^ 2 :=
    mul_le_mul_of_nonneg_right hepsilon_le_abs habs_sq_nonneg
  have habs_sq : |x| ^ 2 = x ^ 2 := by
    simp
  have hscaled : epsilon * x ^ 2 ≤ |x| ^ 3 := by
    calc
      epsilon * x ^ 2 = epsilon * |x| ^ 2 := by rw [← habs_sq]
      _ ≤ |x| * |x| ^ 2 := hmul
      _ = |x| ^ 3 := by ring
  calc
    x ^ 2 = epsilon⁻¹ * (epsilon * x ^ 2) := by
      rw [← mul_assoc, inv_mul_cancel₀ (ne_of_gt hepsilon), one_mul]
    _ ≤ epsilon⁻¹ * |x| ^ 3 :=
      mul_le_mul_of_nonneg_left hscaled
        (inv_nonneg.mpr (le_of_lt hepsilon))

/--
Finite Lyapunov-to-Lindeberg bound for nonnegative weights.

The left side is the weighted quadratic tail.  The right side is the cubic
Lyapunov moment multiplied by `epsilon^{-1}`.
-/
theorem lindebergQuadraticTailSum_le_inv_mul_lyapunovCubicMomentSum
    (s : Finset α) (weight value : α -> Real) {epsilon : Real}
    (hepsilon : 0 < epsilon)
    (hweight_nonneg : ∀ i, i ∈ s -> 0 ≤ weight i) :
    lindebergQuadraticTailSum s weight value epsilon ≤
      epsilon⁻¹ * lyapunovCubicMomentSum s weight value := by
  unfold lindebergQuadraticTailSum lyapunovCubicMomentSum
  calc
    (∑ i ∈ s, weight i *
        if epsilon < |value i| then value i ^ 2 else 0) ≤
        ∑ i ∈ s, epsilon⁻¹ * (weight i * |value i| ^ 3) := by
          refine Finset.sum_le_sum ?_
          intro i hi
          by_cases htail : epsilon < |value i|
          · have hpoint :
                value i ^ 2 ≤ epsilon⁻¹ * |value i| ^ 3 :=
              sq_le_inv_mul_abs_cube_of_epsilon_lt_abs hepsilon htail
            calc
              weight i *
                  (if epsilon < |value i| then value i ^ 2 else 0) =
                  weight i * value i ^ 2 := by simp [htail]
              _ ≤ weight i * (epsilon⁻¹ * |value i| ^ 3) :=
                  mul_le_mul_of_nonneg_left hpoint
                    (hweight_nonneg i hi)
              _ = epsilon⁻¹ * (weight i * |value i| ^ 3) := by ring
          · have hright_nonneg :
                0 ≤ epsilon⁻¹ * (weight i * |value i| ^ 3) :=
              mul_nonneg (inv_nonneg.mpr (le_of_lt hepsilon))
                (mul_nonneg (hweight_nonneg i hi)
                  (pow_nonneg (abs_nonneg (value i)) 3))
            calc
              weight i *
                  (if epsilon < |value i| then value i ^ 2 else 0) = 0 := by
                  simp [htail]
              _ ≤ epsilon⁻¹ * (weight i * |value i| ^ 3) :=
                  hright_nonneg
    _ = epsilon⁻¹ * (∑ i ∈ s, weight i * |value i| ^ 3) := by
      rw [Finset.mul_sum]

/--
Convergence-level finite Lyapunov-to-Lindeberg bridge.

If the cubic Lyapunov bound multiplied by `epsilon^{-1}` tends to zero and the
weights are eventually nonnegative, then the quadratic Lindeberg tail tends to
zero.
-/
theorem tendsto_lindebergQuadraticTailSum_zero_of_eventually_nonneg_of_lyapunov
    {Index : Type*} {l : Filter Index}
    (sample : Index -> Finset α)
    (weight value : Index -> α -> Real)
    {epsilon : Real} (hepsilon : 0 < epsilon)
    (hweight_nonneg :
      ∀ᶠ index in l,
        ∀ i, i ∈ sample index -> 0 ≤ weight index i)
    (hlyapunov :
      Tendsto
        (fun index =>
          epsilon⁻¹ *
            lyapunovCubicMomentSum (sample index) (weight index)
              (value index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        lindebergQuadraticTailSum (sample index) (weight index)
          (value index) epsilon)
      l (nhds 0) := by
  exact squeeze_zero'
    (hweight_nonneg.mono
      (fun index hnonneg =>
        lindebergQuadraticTailSum_nonneg (sample index) (weight index)
          (value index) epsilon hnonneg))
    (hweight_nonneg.mono
      (fun index hnonneg =>
        lindebergQuadraticTailSum_le_inv_mul_lyapunovCubicMomentSum
          (sample index) (weight index) (value index) hepsilon hnonneg))
    hlyapunov

end WDSM
end Matching
end StatInference
