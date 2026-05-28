import StatInference.Optimization.GradientDescent

/-!
# Chewi Theorem 3.3 contraction layer

This module proves the algebraic contraction estimate in Chewi Theorem 3.3
from two source-shaped supplied interfaces: strong monotonicity of the gradient
and the Exercise 3.1 co-coercive step inequality.
-/

namespace StatInference
namespace Optimization

open Set
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/--
Chewi Theorem 3.3, squared-distance form, from supplied gradient monotonicity
and the Exercise 3.1 co-coercivity inequality.
-/
theorem gradientStep_sqdist_contract_of_strongMonotone_cocoercive
    {C : Set E} {grad : E -> E} {alpha h : ℝ} {x y : E}
    (hmono : StronglyMonotoneGradientOn C grad alpha)
    (hcoco : GradientStepCocoerciveOn C grad h)
    (hh_nonneg : 0 ≤ h)
    (hx : x ∈ C) (hy : y ∈ C) :
    ‖gradientDescentStep grad h y - gradientDescentStep grad h x‖ ^ (2 : ℕ) ≤
      (1 - alpha * h) * ‖y - x‖ ^ (2 : ℕ) := by
  let d : E := y - x
  let dg : E := grad y - grad x
  have hstep_sub :
      gradientDescentStep grad h y - gradientDescentStep grad h x =
        d - h • dg := by
    simp [d, dg, gradientDescentStep, smul_sub]
    abel
  have hmono' :
      alpha * ‖d‖ ^ (2 : ℕ) ≤ inner ℝ dg d := by
    simpa [d, dg] using hmono.inner_lower hx hy
  have hcoco' :
      h * ‖dg‖ ^ (2 : ℕ) ≤ inner ℝ d dg := by
    simpa [d, dg] using hcoco.inner_lower hx hy
  have hcoco_mul :
      h ^ (2 : ℕ) * ‖dg‖ ^ (2 : ℕ) ≤ h * inner ℝ d dg := by
    have hmul := mul_le_mul_of_nonneg_left hcoco' hh_nonneg
    simpa [pow_two, mul_assoc, mul_left_comm, mul_comm] using hmul
  have hmono_mul :
      alpha * h * ‖d‖ ^ (2 : ℕ) ≤ h * inner ℝ d dg := by
    have hmul := mul_le_mul_of_nonneg_left hmono' hh_nonneg
    simpa [real_inner_comm, mul_assoc, mul_left_comm, mul_comm] using hmul
  rw [hstep_sub, norm_sub_sq_real, real_inner_smul_right, norm_smul,
    Real.norm_eq_abs, abs_of_nonneg hh_nonneg]
  nlinarith

/--
Chewi Theorem 3.3, norm form, obtained from the squared-distance contraction
when the contraction factor is nonnegative.
-/
theorem gradientStep_dist_contract_of_strongMonotone_cocoercive
    {C : Set E} {grad : E -> E} {alpha h : ℝ} {x y : E}
    (hmono : StronglyMonotoneGradientOn C grad alpha)
    (hcoco : GradientStepCocoerciveOn C grad h)
    (hh_nonneg : 0 ≤ h)
    (hfactor_nonneg : 0 ≤ 1 - alpha * h)
    (hx : x ∈ C) (hy : y ∈ C) :
    ‖gradientDescentStep grad h y - gradientDescentStep grad h x‖ ≤
      Real.sqrt (1 - alpha * h) * ‖y - x‖ := by
  have hsquare :=
    gradientStep_sqdist_contract_of_strongMonotone_cocoercive
      hmono hcoco hh_nonneg hx hy
  have hrhs_nonneg :
      0 ≤ Real.sqrt (1 - alpha * h) * ‖y - x‖ :=
    mul_nonneg (Real.sqrt_nonneg _) (norm_nonneg _)
  exact (sq_le_sq₀ (norm_nonneg _) hrhs_nonneg).mp (by
    rw [mul_pow, Real.sq_sqrt hfactor_nonneg]
    exact hsquare)

/--
Chewi Theorem 3.3, squared-distance form, deriving the gradient monotonicity
input from the first-order lower-model form of Proposition 1.6.
-/
theorem gradientStep_sqdist_contract_of_firstOrderStrongConvexOn_cocoercive
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {alpha h : ℝ} {x y : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hcoco : GradientStepCocoerciveOn C grad h)
    (hh_nonneg : 0 ≤ h)
    (hx : x ∈ C) (hy : y ∈ C) :
    ‖gradientDescentStep grad h y - gradientDescentStep grad h x‖ ^ (2 : ℕ) ≤
      (1 - alpha * h) * ‖y - x‖ ^ (2 : ℕ) :=
  gradientStep_sqdist_contract_of_strongMonotone_cocoercive
    hfirst.stronglyMonotoneGradientOn hcoco hh_nonneg hx hy

/--
Chewi Theorem 3.3, norm form, deriving the gradient monotonicity input from
the first-order lower-model form of Proposition 1.6.
-/
theorem gradientStep_dist_contract_of_firstOrderStrongConvexOn_cocoercive
    {C : Set E} {f : E -> ℝ} {grad : E -> E} {alpha h : ℝ} {x y : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hcoco : GradientStepCocoerciveOn C grad h)
    (hh_nonneg : 0 ≤ h)
    (hfactor_nonneg : 0 ≤ 1 - alpha * h)
    (hx : x ∈ C) (hy : y ∈ C) :
    ‖gradientDescentStep grad h y - gradientDescentStep grad h x‖ ≤
      Real.sqrt (1 - alpha * h) * ‖y - x‖ :=
  gradientStep_dist_contract_of_strongMonotone_cocoercive
    hfirst.stronglyMonotoneGradientOn hcoco hh_nonneg
    hfactor_nonneg hx hy

/--
Chewi Theorem 3.3, squared-distance form, using Proposition 1.6 `(1.4) =>
(1.5)` and Exercise 3.1 equation (3.5) with the source step-size condition.
-/
theorem gradientStep_sqdist_contract_of_firstOrderStrongConvexOn_gradientCocoerciveOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x y : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hcoco : GradientCocoerciveOn C grad beta)
    (hbeta_pos : 0 < beta)
    (hh_nonneg : 0 ≤ h)
    (hstep_size : h ≤ 1 / beta)
    (hx : x ∈ C) (hy : y ∈ C) :
    ‖gradientDescentStep grad h y - gradientDescentStep grad h x‖ ^ (2 : ℕ) ≤
      (1 - alpha * h) * ‖y - x‖ ^ (2 : ℕ) :=
  gradientStep_sqdist_contract_of_firstOrderStrongConvexOn_cocoercive
    hfirst (hcoco.stepCocoerciveOn_of_le_inv hbeta_pos hh_nonneg hstep_size)
    hh_nonneg hx hy

/--
Chewi Theorem 3.3, norm form, using Proposition 1.6 `(1.4) => (1.5)` and
Exercise 3.1 equation (3.5) with the source step-size condition.
-/
theorem gradientStep_dist_contract_of_firstOrderStrongConvexOn_gradientCocoerciveOn
    {C : Set E} {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x y : E}
    (hfirst : FirstOrderStrongConvexOn C f grad alpha)
    (hcoco : GradientCocoerciveOn C grad beta)
    (hbeta_pos : 0 < beta)
    (hh_nonneg : 0 ≤ h)
    (hstep_size : h ≤ 1 / beta)
    (hfactor_nonneg : 0 ≤ 1 - alpha * h)
    (hx : x ∈ C) (hy : y ∈ C) :
    ‖gradientDescentStep grad h y - gradientDescentStep grad h x‖ ≤
      Real.sqrt (1 - alpha * h) * ‖y - x‖ :=
  gradientStep_dist_contract_of_firstOrderStrongConvexOn_cocoercive
    hfirst (hcoco.stepCocoerciveOn_of_le_inv hbeta_pos hh_nonneg hstep_size)
    hh_nonneg hfactor_nonneg hx hy

/--
Chewi Theorem 3.3, squared-distance form, with Proposition 1.6 `(1.3) =>
(1.4)` discharged from the actual segment strong-convexity definition on the
whole space.  The co-coercivity input remains the Exercise 3.1 interface.
-/
theorem gradientStep_sqdist_contract_of_strongConvexOn_univ_hasGradientAt_gradientCocoerciveOn
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x y : E}
    (hstrong : StrongConvexOn Set.univ f alpha)
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hcoco : GradientCocoerciveOn Set.univ grad beta)
    (hbeta_pos : 0 < beta)
    (hh_nonneg : 0 ≤ h)
    (hstep_size : h ≤ 1 / beta) :
    ‖gradientDescentStep grad h y - gradientDescentStep grad h x‖ ^ (2 : ℕ) ≤
      (1 - alpha * h) * ‖y - x‖ ^ (2 : ℕ) :=
  gradientStep_sqdist_contract_of_firstOrderStrongConvexOn_gradientCocoerciveOn
    (FirstOrderStrongConvexOn.of_strongConvexOn_univ_hasGradientAt
      hstrong hgrad)
    hcoco hbeta_pos hh_nonneg hstep_size (by simp) (by simp)

/--
Chewi Theorem 3.3, norm form, with Proposition 1.6 `(1.3) => (1.4)`
discharged from the actual segment strong-convexity definition on the whole
space.  The co-coercivity input remains the Exercise 3.1 interface.
-/
theorem gradientStep_dist_contract_of_strongConvexOn_univ_hasGradientAt_gradientCocoerciveOn
    [CompleteSpace E] {f : E -> ℝ} {grad : E -> E}
    {alpha beta h : ℝ} {x y : E}
    (hstrong : StrongConvexOn Set.univ f alpha)
    (hgrad : ∀ z, HasGradientAt f (grad z) z)
    (hcoco : GradientCocoerciveOn Set.univ grad beta)
    (hbeta_pos : 0 < beta)
    (hh_nonneg : 0 ≤ h)
    (hstep_size : h ≤ 1 / beta)
    (hfactor_nonneg : 0 ≤ 1 - alpha * h) :
    ‖gradientDescentStep grad h y - gradientDescentStep grad h x‖ ≤
      Real.sqrt (1 - alpha * h) * ‖y - x‖ :=
  gradientStep_dist_contract_of_firstOrderStrongConvexOn_gradientCocoerciveOn
    (FirstOrderStrongConvexOn.of_strongConvexOn_univ_hasGradientAt
      hstrong hgrad)
    hcoco hbeta_pos hh_nonneg hstep_size hfactor_nonneg
    (by simp) (by simp)

end Optimization
end StatInference
