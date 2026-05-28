import StatInference.Optimization.LowerBounds
import StatInference.Optimization.Reductions

/-!
# Chewi Theorem 4.5 setup

This module starts the strongly-convex lower-bound construction used around
Chewi Theorem 4.5.  The source derives Theorem 4.5 from Lemma 4.2 and the
convex lower bound, but the same regularization layer is also useful as a
concrete strongly-convex chain objective.  We package the regularized chain
objective, its supplied gradient, its strong-convexity/smoothness interfaces,
and the gradient-span support calculation.
-/

namespace StatInference
namespace Optimization

open Set
open scoped InnerProductSpace

/--
Regularized lower-bound chain objective centered at the origin.  The base
chain uses smoothness budget `beta - alpha`; the quadratic regularizer supplies
the `alpha`-strongly-convex part.
-/
noncomputable def strongLowerBoundChainObjective (alpha beta : ℝ) (d : ℕ) :
    EuclideanSpace ℝ (Fin d) -> ℝ :=
  quadraticRegularizedAround
    (lowerBoundChainTextbookObjective (beta - alpha) d) alpha 0

/-- Supplied gradient for `strongLowerBoundChainObjective`. -/
noncomputable def strongLowerBoundChainGradient (alpha beta : ℝ) (d : ℕ) :
    EuclideanSpace ℝ (Fin d) -> EuclideanSpace ℝ (Fin d) :=
  regularizedGradient (lowerBoundChainGradient (beta - alpha) d) alpha 0

theorem strongLowerBoundChainObjective_apply
    (alpha beta : ℝ) (d : ℕ) (x : EuclideanSpace ℝ (Fin d)) :
    strongLowerBoundChainObjective alpha beta d x =
      lowerBoundChainTextbookObjective (beta - alpha) d x +
        (alpha / 2) * ‖x‖ ^ (2 : ℕ) := by
  simp [strongLowerBoundChainObjective, quadraticRegularizedAround]

theorem strongLowerBoundChainGradient_apply
    (alpha beta : ℝ) (d : ℕ) (x : EuclideanSpace ℝ (Fin d)) :
    strongLowerBoundChainGradient alpha beta d x =
      lowerBoundChainGradient (beta - alpha) d x + alpha • x := by
  simp [strongLowerBoundChainGradient, regularizedGradient]

/--
The regularized chain is `alpha`-strongly convex in the supplied first-order
lower-model sense whenever `alpha <= beta`.
-/
theorem strongLowerBoundChainObjective_firstOrderStrongConvexOn
    {alpha beta : ℝ} (halpha_le_beta : alpha ≤ beta) (d : ℕ) :
    FirstOrderStrongConvexOn Set.univ
      (strongLowerBoundChainObjective alpha beta d)
      (strongLowerBoundChainGradient alpha beta d) alpha := by
  have hdiff : 0 ≤ beta - alpha := by
    nlinarith
  simpa [strongLowerBoundChainObjective, strongLowerBoundChainGradient] using
    (quadraticRegularizedAround_firstOrderStrongConvexOn_convex
      (f := lowerBoundChainTextbookObjective (beta - alpha) d)
      (grad := lowerBoundChainGradient (beta - alpha) d)
      (delta := alpha) (x0 := (0 : EuclideanSpace ℝ (Fin d)))
      (lowerBoundChainTextbookObjective_firstOrderConvex hdiff d))

/--
The regularized chain is `beta`-smooth: the base chain is `(beta - alpha)`-
smooth and the regularizer contributes `alpha`.
-/
theorem strongLowerBoundChainObjective_smoothWithGradientOn
    {alpha beta : ℝ} (halpha_le_beta : alpha ≤ beta) (d : ℕ) :
    SmoothWithGradientOn Set.univ
      (strongLowerBoundChainObjective alpha beta d)
      (strongLowerBoundChainGradient alpha beta d) beta := by
  have hdiff : 0 ≤ beta - alpha := by
    nlinarith
  have hreg :
      SmoothWithGradientOn Set.univ
        (strongLowerBoundChainObjective alpha beta d)
        (strongLowerBoundChainGradient alpha beta d) ((beta - alpha) + alpha) := by
    simpa [strongLowerBoundChainObjective, strongLowerBoundChainGradient] using
      (quadraticRegularizedAround_smoothWithGradientOn
        (f := lowerBoundChainTextbookObjective (beta - alpha) d)
        (grad := lowerBoundChainGradient (beta - alpha) d)
        (beta := beta - alpha) (delta := alpha)
        (x0 := (0 : EuclideanSpace ℝ (Fin d)))
        (lowerBoundChainTextbookObjective_smoothWithGradientOn hdiff d))
  convert hreg using 1
  ring

/--
The strongly-convex chain oracle preserves the source support growth:
`x ∈ V_k -> grad f(x) ∈ V_{k+1}`.  The new regularizer term is `alpha • x`,
which already lies in `V_k`.
-/
theorem strongLowerBoundChainGradient_mem_coordinatePrefixSubmodule
    {d k : ℕ} {alpha beta : ℝ} {x : EuclideanSpace ℝ (Fin d)}
    (hx : x ∈ coordinatePrefixSubmodule d k) :
    strongLowerBoundChainGradient alpha beta d x ∈
      coordinatePrefixSubmodule d (k + 1) := by
  rw [strongLowerBoundChainGradient_apply]
  refine Submodule.add_mem _ ?_ ?_
  · exact lowerBoundChainGradient_mem_coordinatePrefixSubmodule hx
  · have hx_smul :
        alpha • x ∈ coordinatePrefixSubmodule d k :=
      Submodule.smul_mem _ alpha hx
    exact coordinatePrefixSubmodule_mono d (Nat.le_succ k) hx_smul

/--
Consequently every gradient-span trajectory for the strongly-convex chain
starting from zero satisfies Chewi's `V_n` containment invariant.
-/
theorem gradientSpanTrajectory_mem_coordinatePrefixSubmodule_of_strongLowerBoundChainGradient
    {d : ℕ} {alpha beta : ℝ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x) :
    ∀ n, x n ∈ coordinatePrefixSubmodule d n :=
  gradientSpanTrajectory_mem_coordinatePrefixSubmodule_of_grad_mem_next
    hx0 hspan (fun _ hxk =>
      strongLowerBoundChainGradient_mem_coordinatePrefixSubmodule hxk)

/--
Source-shaped interface package for the regularized chain used toward Chewi
Theorem 4.5: under `0 < alpha < beta`, it is `alpha`-strongly convex,
`beta`-smooth, and its gradient-span trajectories from the origin stay in
the prefix subspaces.
-/
theorem chewi45_regularized_chain_interface_package
    {alpha beta : ℝ} (_halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (d : ℕ) :
    FirstOrderStrongConvexOn Set.univ
      (strongLowerBoundChainObjective alpha beta d)
      (strongLowerBoundChainGradient alpha beta d) alpha ∧
    SmoothWithGradientOn Set.univ
      (strongLowerBoundChainObjective alpha beta d)
      (strongLowerBoundChainGradient alpha beta d) beta ∧
    ∀ {x : ℕ -> EuclideanSpace ℝ (Fin d)},
      x 0 = 0 ->
      IsGradientSpanTrajectory (strongLowerBoundChainGradient alpha beta d) x ->
      ∀ n, x n ∈ coordinatePrefixSubmodule d n := by
  exact ⟨
    strongLowerBoundChainObjective_firstOrderStrongConvexOn halpha_lt_beta.le d,
    strongLowerBoundChainObjective_smoothWithGradientOn halpha_lt_beta.le d,
    fun {x} hx0 hspan =>
      gradientSpanTrajectory_mem_coordinatePrefixSubmodule_of_strongLowerBoundChainGradient
        (x := x)
        hx0 hspan⟩

/--
The displayed minimizer from the convex lower-bound chain has radius at most
`sqrt d`.  This is the concrete radius estimate fed into the Lemma 4.2
regularization reduction en route to Chewi Theorem 4.5.
-/
theorem lowerBoundChainMinimizer_norm_le_sqrt_dim (d : ℕ) :
    ‖lowerBoundChainMinimizer d‖ ≤ Real.sqrt (d : ℝ) := by
  have hsq := lowerBoundChainMinimizer_norm_sq_le_dim d
  have hdim_nonneg : 0 ≤ (d : ℝ) := by positivity
  have hsqrt_sq : (Real.sqrt (d : ℝ)) ^ (2 : ℕ) = (d : ℝ) :=
    Real.sq_sqrt hdim_nonneg
  have hsq' :
      ‖lowerBoundChainMinimizer d‖ ^ (2 : ℕ) ≤
        (Real.sqrt (d : ℝ)) ^ (2 : ℕ) := by
    simpa [hsqrt_sq] using hsq
  exact (sq_le_sq₀ (norm_nonneg _) (Real.sqrt_nonneg _)).mp hsq'

/--
Lemma 4.2's complexity package instantiated on the concrete convex
lower-bound chain from Chewi Theorem 4.4.
-/
theorem chewi45_lowerBoundChain_regularization_complexity_package
    {beta eps R : ℝ} (hbeta : 0 ≤ beta) (heps : 0 < eps)
    (hR : 0 < R) (heps_le : eps ≤ beta * R ^ (2 : ℕ))
    (d : ℕ) :
    let delta := eps / R ^ (2 : ℕ)
    FirstOrderStrongConvexOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) delta ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) (beta + delta) ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) (2 * beta) ∧
    (beta + delta) / delta ≤ 2 * beta * R ^ (2 : ℕ) / eps := by
  exact lemma42_regularization_complexity_package
    (f := lowerBoundChainTextbookObjective beta d)
    (grad := lowerBoundChainGradient beta d)
    (beta := beta) (eps := eps) (R := R)
    (x0 := (0 : EuclideanSpace ℝ (Fin d)))
    (lowerBoundChainTextbookObjective_firstOrderConvex hbeta d)
    (lowerBoundChainTextbookObjective_smoothWithGradientOn hbeta d)
    heps hR heps_le

/--
Concrete Lemma 4.2 reduction package for Chewi's lower-bound chain: an
`eps / 2`-near minimizer of the regularized chain is an `eps`-near minimizer
of the base convex chain, and the regularized problem carries the expected
strong-convexity, smoothness, and condition-number bounds.
-/
theorem chewi45_lowerBoundChain_regularization_reduction_package
    {beta eps R : ℝ} {d : ℕ}
    {x xDelta : EuclideanSpace ℝ (Fin d)}
    (hbeta : 0 ≤ beta) (heps : 0 < eps) (hR : 0 < R)
    (heps_le : eps ≤ beta * R ^ (2 : ℕ))
    (hR_bound : ‖lowerBoundChainMinimizer d‖ ≤ R)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / R ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) x ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / R ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / R ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / R ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) (lowerBoundChainMinimizer d)) :
    let delta := eps / R ^ (2 : ℕ)
    lowerBoundChainTextbookObjective beta d x -
        lowerBoundChainTextbookObjective beta d (lowerBoundChainMinimizer d) ≤ eps ∧
    ‖xDelta - (0 : EuclideanSpace ℝ (Fin d))‖ ≤ R ∧
    FirstOrderStrongConvexOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) delta ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) (beta + delta) ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) (2 * beta) ∧
    (beta + delta) / delta ≤ 2 * beta * R ^ (2 : ℕ) / eps := by
  exact lemma42_regularization_reduction_package_of_isMinOn
    (f := lowerBoundChainTextbookObjective beta d)
    (grad := lowerBoundChainGradient beta d)
    (beta := beta) (eps := eps) (R := R)
    (x0 := (0 : EuclideanSpace ℝ (Fin d)))
    (x := x) (xDelta := xDelta)
    (xStar := lowerBoundChainMinimizer d)
    (lowerBoundChainTextbookObjective_firstOrderConvex hbeta d)
    (lowerBoundChainTextbookObjective_smoothWithGradientOn hbeta d)
    heps hR heps_le (by simpa using hR_bound) hx_near hDelta_le
    (lowerBoundChainTextbookObjective_isMinOn_lowerBoundChainMinimizer hbeta d)

/--
Source-radius specialization of the concrete Lemma 4.2 reduction package,
using the compiled estimate `‖x_*‖ <= sqrt d` for Chewi's lower-bound chain.
-/
theorem chewi45_lowerBoundChain_regularization_reduction_package_sqrt_dim
    {beta eps : ℝ} {d : ℕ}
    {x xDelta : EuclideanSpace ℝ (Fin d)}
    (hbeta : 0 ≤ beta) (heps : 0 < eps) (hdpos : 0 < d)
    (heps_le :
      eps ≤ beta * (Real.sqrt (d : ℝ)) ^ (2 : ℕ))
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / (Real.sqrt (d : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) x ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / (Real.sqrt (d : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / (Real.sqrt (d : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / (Real.sqrt (d : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) (lowerBoundChainMinimizer d)) :
    let delta := eps / (Real.sqrt (d : ℝ)) ^ (2 : ℕ)
    lowerBoundChainTextbookObjective beta d x -
        lowerBoundChainTextbookObjective beta d (lowerBoundChainMinimizer d) ≤ eps ∧
    ‖xDelta - (0 : EuclideanSpace ℝ (Fin d))‖ ≤ Real.sqrt (d : ℝ) ∧
    FirstOrderStrongConvexOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) delta ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) (beta + delta) ∧
    SmoothWithGradientOn Set.univ
      (quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)))
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) (2 * beta) ∧
    (beta + delta) / delta ≤
      2 * beta * (Real.sqrt (d : ℝ)) ^ (2 : ℕ) / eps := by
  have hdpos_real : 0 < (d : ℝ) := by exact_mod_cast hdpos
  have hR : 0 < Real.sqrt (d : ℝ) := Real.sqrt_pos.2 hdpos_real
  exact chewi45_lowerBoundChain_regularization_reduction_package
    (beta := beta) (eps := eps) (R := Real.sqrt (d : ℝ))
    (d := d) (x := x) (xDelta := xDelta)
    hbeta heps hR heps_le (lowerBoundChainMinimizer_norm_le_sqrt_dim d)
    hx_near hDelta_le

/--
Prefix-subspace version of the convex lower-bound gap.  This removes the
base-chain gradient-span hypothesis when another oracle, such as a regularized
oracle, has already proved `x ∈ V_N`.
-/
theorem lowerBoundChainTextbookObjective_gap_ge_of_mem_coordinatePrefixSubmodule
    {beta : ℝ} (hbeta : 0 ≤ beta) {N d : ℕ} (hNd : N ≤ d)
    {x : EuclideanSpace ℝ (Fin d)}
    (hx : x ∈ coordinatePrefixSubmodule d N) :
    beta / (8 * ((N : ℝ) + 1)) - beta / (8 * ((d : ℝ) + 1)) ≤
      lowerBoundChainTextbookObjective beta d x -
        lowerBoundChainTextbookObjective beta d (lowerBoundChainMinimizer d) := by
  have hprefix :
      -(beta / 8) * (1 - 1 / ((N : ℝ) + 1)) ≤
        lowerBoundChainTextbookObjective beta d x :=
    lowerBoundChainTextbookObjective_ge_prefixMin_of_mem_coordinatePrefixSubmodule
      hbeta hNd hx
  have hNden : ((N : ℝ) + 1) ≠ 0 := by positivity
  have hdden : ((d : ℝ) + 1) ≠ 0 := by positivity
  calc
    beta / (8 * ((N : ℝ) + 1)) - beta / (8 * ((d : ℝ) + 1))
        =
          -(beta / 8) * (1 - 1 / ((N : ℝ) + 1)) -
            (-(beta / 8) * (1 - 1 / ((d : ℝ) + 1))) := by
            field_simp [hNden, hdden]
            ring
    _ ≤ lowerBoundChainTextbookObjective beta d x -
          (-(beta / 8) * (1 - 1 / ((d : ℝ) + 1))) := by
          exact sub_le_sub_right hprefix _
    _ = lowerBoundChainTextbookObjective beta d x -
          lowerBoundChainTextbookObjective beta d (lowerBoundChainMinimizer d) := by
          rw [lowerBoundChainTextbookObjective_lowerBoundChainMinimizer]

/--
The regularized lower-bound chain oracle has the same one-coordinate support
growth as the base chain: `x ∈ V_k -> grad_delta(x) ∈ V_{k+1}`.
-/
theorem regularizedLowerBoundChainGradient_mem_coordinatePrefixSubmodule
    {d k : ℕ} {beta delta : ℝ} {x : EuclideanSpace ℝ (Fin d)}
    (hx : x ∈ coordinatePrefixSubmodule d k) :
    regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d)) x ∈
      coordinatePrefixSubmodule d (k + 1) := by
  rw [regularizedGradient_apply]
  refine Submodule.add_mem _ ?_ ?_
  · exact lowerBoundChainGradient_mem_coordinatePrefixSubmodule hx
  · have hx_sub :
        x - (0 : EuclideanSpace ℝ (Fin d)) ∈ coordinatePrefixSubmodule d k := by
      simpa using hx
    have hx_smul :
        delta • (x - (0 : EuclideanSpace ℝ (Fin d))) ∈
          coordinatePrefixSubmodule d k :=
      Submodule.smul_mem _ delta hx_sub
    exact coordinatePrefixSubmodule_mono d (Nat.le_succ k) hx_smul

/--
Regularized-chain gradient-span trajectories from zero still satisfy the
source support invariant `x_n ∈ V_n`.
-/
theorem gradientSpanTrajectory_mem_coordinatePrefixSubmodule_of_regularizedLowerBoundChainGradient
    {d : ℕ} {beta delta : ℝ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient (lowerBoundChainGradient beta d) delta
        (0 : EuclideanSpace ℝ (Fin d))) x) :
    ∀ n, x n ∈ coordinatePrefixSubmodule d n :=
  gradientSpanTrajectory_mem_coordinatePrefixSubmodule_of_grad_mem_next
    hx0 hspan (fun _ hxk =>
      regularizedLowerBoundChainGradient_mem_coordinatePrefixSubmodule hxk)

/--
Concrete Theorem 4.5 reduction obstruction: a regularized gradient-span run
which is `eps / 2`-near the regularized minimum by time `N` forces the convex
Theorem 4.4 lower-bound quantity to be at most `eps`.
-/
theorem chewi45_convex_lower_bound_le_eps_of_regularizedGradientSpan_near_min
    {beta eps R : ℝ} (hbeta : 0 ≤ beta) (heps : 0 < eps)
    (hR : 0 < R) (heps_le : eps ≤ beta * R ^ (2 : ℕ))
    {N d : ℕ} (hNd : N ≤ d)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    {xDelta : EuclideanSpace ℝ (Fin d)}
    (hR_bound : ‖lowerBoundChainMinimizer d‖ ≤ R)
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient (lowerBoundChainGradient beta d)
        (eps / R ^ (2 : ℕ)) (0 : EuclideanSpace ℝ (Fin d))) x)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / R ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) (x N) ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / R ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / R ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta d)
        (eps / R ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin d)) (lowerBoundChainMinimizer d)) :
    beta / (8 * ((N : ℝ) + 1)) - beta / (8 * ((d : ℝ) + 1)) ≤ eps := by
  have hx_prefix :
      x N ∈ coordinatePrefixSubmodule d N :=
    gradientSpanTrajectory_mem_coordinatePrefixSubmodule_of_regularizedLowerBoundChainGradient
      (x := x) hx0 hspan N
  have hgap_lower :
      beta / (8 * ((N : ℝ) + 1)) - beta / (8 * ((d : ℝ) + 1)) ≤
        lowerBoundChainTextbookObjective beta d (x N) -
          lowerBoundChainTextbookObjective beta d (lowerBoundChainMinimizer d) :=
    lowerBoundChainTextbookObjective_gap_ge_of_mem_coordinatePrefixSubmodule
      hbeta hNd hx_prefix
  have hreduce :=
    chewi45_lowerBoundChain_regularization_reduction_package
      (beta := beta) (eps := eps) (R := R) (d := d)
      (x := x N) (xDelta := xDelta)
      hbeta heps hR heps_le hR_bound hx_near hDelta_le
  exact hgap_lower.trans hreduce.1

/--
`d = 2N + 1` source specialization of the regularized-chain obstruction,
using the canonical radius bound `R = sqrt d`.
-/
theorem chewi45_two_mul_add_one_lower_bound_le_eps_of_regularizedGradientSpan_near_min
    {beta eps : ℝ} (hbeta : 0 ≤ beta) (heps : 0 < eps) (N : ℕ)
    (heps_le :
      eps ≤ beta * (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    {xDelta : EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient
        (lowerBoundChainGradient beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))) x)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) (x N) ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))
        (lowerBoundChainMinimizer (2 * N + 1))) :
    beta / (16 * ((N : ℝ) + 1)) ≤ eps := by
  have hdpos : 0 < 2 * N + 1 := by omega
  have hdpos_real : 0 < ((2 * N + 1 : ℕ) : ℝ) := by exact_mod_cast hdpos
  have hR : 0 < Real.sqrt ((2 * N + 1 : ℕ) : ℝ) :=
    Real.sqrt_pos.2 hdpos_real
  have hraw :=
    chewi45_convex_lower_bound_le_eps_of_regularizedGradientSpan_near_min
      (beta := beta) (eps := eps)
      (R := Real.sqrt ((2 * N + 1 : ℕ) : ℝ))
      (N := N) (d := 2 * N + 1) (x := x) (xDelta := xDelta)
      hbeta heps hR heps_le (by omega)
      (lowerBoundChainMinimizer_norm_le_sqrt_dim (2 * N + 1))
      hx0 hspan hx_near hDelta_le
  have hleft :
      beta / (8 * ((N : ℝ) + 1)) -
          beta / (8 * (((2 * N + 1 : ℕ) : ℝ) + 1)) =
        beta / (16 * ((N : ℝ) + 1)) := by
    have hden : ((N : ℝ) + 1) ≠ 0 := by positivity
    have hden2 : (((2 * N + 1 : ℕ) : ℝ) + 1) ≠ 0 := by positivity
    field_simp [hden, hden2]
    norm_num [Nat.cast_add, Nat.cast_mul]
    ring
  rwa [hleft] at hraw

/--
Contradiction form of the preceding theorem: under the regularization
reduction hypotheses, accuracy `eps < beta / (16 (N+1))` cannot be reached by
time `N` on the `d = 2N + 1` lower-bound chain.
-/
theorem chewi45_not_regularizedGradientSpan_near_min_of_eps_lt_two_mul_add_one_bound
    {beta eps : ℝ} (hbeta : 0 ≤ beta) (heps : 0 < eps) (N : ℕ)
    (heps_le :
      eps ≤ beta * (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
    (heps_lt : eps < beta / (16 * ((N : ℝ) + 1)))
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    {xDelta : EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient
        (lowerBoundChainGradient beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))) x)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) (x N) ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))
        (lowerBoundChainMinimizer (2 * N + 1))) :
    False := by
  have hle :=
    chewi45_two_mul_add_one_lower_bound_le_eps_of_regularizedGradientSpan_near_min
      (beta := beta) (eps := eps) hbeta heps N heps_le
      hx0 hspan hx_near hDelta_le
  linarith

/--
Iteration-count form of the `d = 2N + 1` obstruction: the lower-bound
inequality `beta / (16 (N + 1)) <= eps` implies
`beta / (16 eps) - 1 <= N`.
-/
theorem chewi45_iteration_count_ge_of_two_mul_add_one_lower_bound
    {beta eps : ℝ} (heps : 0 < eps) (N : ℕ)
    (hle : beta / (16 * ((N : ℝ) + 1)) ≤ eps) :
    beta / (16 * eps) - 1 ≤ (N : ℝ) := by
  have hdenN : 0 < 16 * ((N : ℝ) + 1) := by positivity
  have hmul :
      beta ≤ eps * (16 * ((N : ℝ) + 1)) :=
    (div_le_iff₀ hdenN).mp hle
  have hden_eps : 0 < 16 * eps := by positivity
  have hdiv :
      beta / (16 * eps) ≤ (N : ℝ) + 1 := by
    rw [div_le_iff₀ hden_eps]
    nlinarith
  linarith

/--
Full regularized-chain near-minimizer obstruction in iteration-count form.
If the regularized lower-bound chain is optimized to `eps / 2` accuracy by a
gradient-span trajectory by time `N`, then `N` must satisfy the corresponding
finite lower bound.
-/
theorem chewi45_iteration_count_ge_of_regularizedGradientSpan_near_min
    {beta eps : ℝ} (hbeta : 0 ≤ beta) (heps : 0 < eps) (N : ℕ)
    (heps_le :
      eps ≤ beta * (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    {xDelta : EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient
        (lowerBoundChainGradient beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))) x)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) (x N) ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))
        (lowerBoundChainMinimizer (2 * N + 1))) :
    beta / (16 * eps) - 1 ≤ (N : ℝ) := by
  have hle :=
    chewi45_two_mul_add_one_lower_bound_le_eps_of_regularizedGradientSpan_near_min
      (beta := beta) (eps := eps) hbeta heps N heps_le
      hx0 hspan hx_near hDelta_le
  exact chewi45_iteration_count_ge_of_two_mul_add_one_lower_bound
    heps N hle

/--
Contradiction form of the iteration-count lower bound: a regularized
gradient-span trajectory cannot reach the stated near-minimum condition by
time `N` when `N < beta / (16 eps) - 1`.
-/
theorem chewi45_not_regularizedGradientSpan_near_min_of_iteration_count_lt
    {beta eps : ℝ} (hbeta : 0 ≤ beta) (heps : 0 < eps) (N : ℕ)
    (heps_le :
      eps ≤ beta * (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
    (hN_lt : (N : ℝ) < beta / (16 * eps) - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    {xDelta : EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient
        (lowerBoundChainGradient beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))) x)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) (x N) ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))
        (lowerBoundChainMinimizer (2 * N + 1))) :
    False := by
  have hge :=
    chewi45_iteration_count_ge_of_regularizedGradientSpan_near_min
      (beta := beta) (eps := eps) hbeta heps N heps_le
      hx0 hspan hx_near hDelta_le
  linarith

/--
Generic rate wrapper for the finite Theorem 4.5 obstruction.  Any rate known
to be below the finite lower bound `beta / (16 eps) - 1` is also below the
number of iterations `N`.
-/
theorem chewi45_iteration_count_ge_rate_of_regularizedGradientSpan_near_min
    {beta eps rate : ℝ} (hbeta : 0 ≤ beta) (heps : 0 < eps) (N : ℕ)
    (heps_le :
      eps ≤ beta * (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
    (hrate_le : rate ≤ beta / (16 * eps) - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    {xDelta : EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient
        (lowerBoundChainGradient beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))) x)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) (x N) ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))
        (lowerBoundChainMinimizer (2 * N + 1))) :
    rate ≤ (N : ℝ) := by
  have hfinite :=
    chewi45_iteration_count_ge_of_regularizedGradientSpan_near_min
      (beta := beta) (eps := eps) hbeta heps N heps_le
      hx0 hspan hx_near hDelta_le
  exact hrate_le.trans hfinite

/--
Logarithmic-condition-number-shaped wrapper for Chewi Theorem 4.5.  The
remaining analytic/asymptotic comparison is isolated in `hrate_le`; once that
comparison shows `c * sqrt(kappa) * log(ratio) <= beta / (16 eps) - 1`, the
compiled regularized-chain obstruction gives the source-shaped lower bound on
`N`.
-/
theorem chewi45_iteration_count_ge_sqrtKappa_log_rate_of_regularizedGradientSpan_near_min
    {beta eps c kappa ratio : ℝ}
    (hbeta : 0 ≤ beta) (heps : 0 < eps) (N : ℕ)
    (heps_le :
      eps ≤ beta * (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
    (hrate_le :
      c * Real.sqrt kappa * Real.log ratio ≤ beta / (16 * eps) - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    {xDelta : EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient
        (lowerBoundChainGradient beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))) x)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) (x N) ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))
        (lowerBoundChainMinimizer (2 * N + 1))) :
    c * Real.sqrt kappa * Real.log ratio ≤ (N : ℝ) := by
  exact chewi45_iteration_count_ge_rate_of_regularizedGradientSpan_near_min
    (beta := beta) (eps := eps)
    (rate := c * Real.sqrt kappa * Real.log ratio)
    hbeta heps N heps_le hrate_le hx0 hspan hx_near hDelta_le

/--
Contradiction form of the logarithmic-condition-number-shaped wrapper: a run
cannot satisfy the near-minimum hypotheses by time `N` if `N` is below a
logarithmic rate which has already been compared to the finite obstruction.
-/
theorem chewi45_not_regularizedGradientSpan_near_min_of_sqrtKappa_log_rate_lt
    {beta eps c kappa ratio : ℝ}
    (hbeta : 0 ≤ beta) (heps : 0 < eps) (N : ℕ)
    (heps_le :
      eps ≤ beta * (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
    (hrate_le :
      c * Real.sqrt kappa * Real.log ratio ≤ beta / (16 * eps) - 1)
    (hN_lt : (N : ℝ) < c * Real.sqrt kappa * Real.log ratio)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    {xDelta : EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (regularizedGradient
        (lowerBoundChainGradient beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))) x)
    (hx_near :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) (x N) ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta + eps / 2)
    (hDelta_le :
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1))) xDelta ≤
      quadraticRegularizedAround
        (lowerBoundChainTextbookObjective beta (2 * N + 1))
        (eps / (Real.sqrt ((2 * N + 1 : ℕ) : ℝ)) ^ (2 : ℕ))
        (0 : EuclideanSpace ℝ (Fin (2 * N + 1)))
        (lowerBoundChainMinimizer (2 * N + 1))) :
    False := by
  have hge :=
    chewi45_iteration_count_ge_sqrtKappa_log_rate_of_regularizedGradientSpan_near_min
      (beta := beta) (eps := eps) (c := c) (kappa := kappa)
      (ratio := ratio)
      hbeta heps N heps_le hrate_le hx0 hspan hx_near hDelta_le
  linarith

/--
The geometric factor in the direct strongly-convex lower-bound route from
Exercise 4.2.
-/
noncomputable def chewi45GeometricRatio (kappa : ℝ) : ℝ :=
  (Real.sqrt kappa - 1) / (Real.sqrt kappa + 1)

theorem chewi45GeometricRatio_nonneg {kappa : ℝ} (hkappa : 1 ≤ kappa) :
    0 ≤ chewi45GeometricRatio kappa := by
  have hsqrt_one : 1 ≤ Real.sqrt kappa := by
    rw [← Real.sqrt_one]
    exact Real.sqrt_le_sqrt hkappa
  have hden_pos : 0 < Real.sqrt kappa + 1 := by
    have hsqrt_nonneg : 0 ≤ Real.sqrt kappa := Real.sqrt_nonneg kappa
    linarith
  exact div_nonneg (sub_nonneg.mpr hsqrt_one) hden_pos.le

theorem chewi45GeometricRatio_pos {kappa : ℝ} (hkappa : 1 < kappa) :
    0 < chewi45GeometricRatio kappa := by
  have hsqrt_one : 1 < Real.sqrt kappa := by
    rw [← Real.sqrt_one]
    exact Real.sqrt_lt_sqrt (by norm_num) hkappa
  have hden_pos : 0 < Real.sqrt kappa + 1 := by
    have hsqrt_nonneg : 0 ≤ Real.sqrt kappa := Real.sqrt_nonneg kappa
    linarith
  exact div_pos (sub_pos.mpr hsqrt_one) hden_pos

theorem chewi45GeometricRatio_lt_one (kappa : ℝ) :
    chewi45GeometricRatio kappa < 1 := by
  have hden_pos : 0 < Real.sqrt kappa + 1 := by
    have hsqrt_nonneg : 0 ≤ Real.sqrt kappa := Real.sqrt_nonneg kappa
    linarith
  rw [chewi45GeometricRatio, div_lt_iff₀ hden_pos]
  linarith

theorem chewi45GeometricRatio_le_one (kappa : ℝ) :
    chewi45GeometricRatio kappa ≤ 1 :=
  (chewi45GeometricRatio_lt_one kappa).le

theorem chewi45GeometricRatio_pow_nonneg {kappa : ℝ}
    (hkappa : 1 ≤ kappa) (n : ℕ) :
    0 ≤ (chewi45GeometricRatio kappa) ^ n :=
  pow_nonneg (chewi45GeometricRatio_nonneg hkappa) n

theorem chewi45GeometricRatio_sub_one (kappa : ℝ) :
    chewi45GeometricRatio kappa - 1 =
      -2 / (Real.sqrt kappa + 1) := by
  have hden : Real.sqrt kappa + 1 ≠ 0 := by
    have hsqrt_nonneg : 0 ≤ Real.sqrt kappa := Real.sqrt_nonneg kappa
    linarith
  rw [chewi45GeometricRatio]
  field_simp [hden]
  ring

theorem chewi45GeometricRatio_inv_sub_one {kappa : ℝ}
    (hkappa : 1 < kappa) :
    (chewi45GeometricRatio kappa)⁻¹ - 1 =
      2 / (Real.sqrt kappa - 1) := by
  have hsqrt_one : 1 < Real.sqrt kappa := by
    rw [← Real.sqrt_one]
    exact Real.sqrt_lt_sqrt (by norm_num) hkappa
  have hnum : Real.sqrt kappa - 1 ≠ 0 := by linarith
  have hden : Real.sqrt kappa + 1 ≠ 0 := by
    have hsqrt_nonneg : 0 ≤ Real.sqrt kappa := Real.sqrt_nonneg kappa
    linarith
  rw [chewi45GeometricRatio]
  field_simp [hnum, hden]
  ring

theorem chewi45GeometricRatio_log_le_neg_two_div_sqrt_add_one
    {kappa : ℝ} (hkappa : 1 < kappa) :
    Real.log (chewi45GeometricRatio kappa) ≤
      -2 / (Real.sqrt kappa + 1) := by
  have hq_pos : 0 < chewi45GeometricRatio kappa :=
    chewi45GeometricRatio_pos hkappa
  exact (Real.log_le_sub_one_of_pos hq_pos).trans_eq
    (chewi45GeometricRatio_sub_one kappa)

theorem chewi45GeometricRatio_neg_two_div_sqrt_sub_one_le_log
    {kappa : ℝ} (hkappa : 1 < kappa) :
    -2 / (Real.sqrt kappa - 1) ≤
      Real.log (chewi45GeometricRatio kappa) := by
  let q := chewi45GeometricRatio kappa
  have hq_pos : 0 < q := by
    simpa [q] using chewi45GeometricRatio_pos hkappa
  have hlog_inv_le :
      Real.log q⁻¹ ≤ 2 / (Real.sqrt kappa - 1) := by
    have hinv_pos : 0 < q⁻¹ := inv_pos.mpr hq_pos
    exact (Real.log_le_sub_one_of_pos hinv_pos).trans_eq
      (by simpa [q] using chewi45GeometricRatio_inv_sub_one hkappa)
  have hlog_inv : Real.log q⁻¹ = -Real.log q := by
    rw [Real.log_inv]
  have hneg_le : -Real.log q ≤ 2 / (Real.sqrt kappa - 1) := by
    simpa [hlog_inv] using hlog_inv_le
  have hmain : -2 / (Real.sqrt kappa - 1) ≤ Real.log q := by
    simpa [neg_div] using (neg_le.mp hneg_le)
  simpa [q] using hmain

/--
Logarithmic sufficient condition for a half-bound on Chewi's geometric ratio:
if `M * log q <= log (1/2)`, then `q^M <= 1/2`.
-/
theorem chewi45GeometricRatio_pow_le_half_of_nat_mul_log_le
    {kappa : ℝ} (hkappa : 1 < kappa) {M : ℕ}
    (hlog :
      (M : ℝ) * Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ)) :
    (chewi45GeometricRatio kappa) ^ M ≤ (1 / 2 : ℝ) := by
  let q := chewi45GeometricRatio kappa
  have hq_pos : 0 < q := by
    simpa [q] using chewi45GeometricRatio_pos hkappa
  have hhalf_pos : 0 < (1 / 2 : ℝ) := by norm_num
  have hpow_pos : 0 < q ^ M := pow_pos hq_pos M
  have hlogpow :
      Real.log (q ^ M) ≤ Real.log (1 / 2 : ℝ) := by
    rw [Real.log_pow]
    simpa [q] using hlog
  exact (Real.log_le_log_iff hpow_pos hhalf_pos).mp hlogpow

/--
Scalar log bridge for the final Chewi 4.5 rate conversion.  When the log of
the ratio is negative, comparing two doubled exponents reverses the order and
turns the log-chain inequality into `rate <= N`.
-/
theorem chewi45_rate_le_iterations_of_log_chain
    {L rate : ℝ} {N : ℕ} (hL_neg : L < 0)
    (hchain :
      (2 * ((N : ℝ) + 1)) * L ≤ (2 * (rate + 1)) * L) :
    rate ≤ (N : ℝ) := by
  have htwice :
      2 * (rate + 1) ≤ 2 * ((N : ℝ) + 1) := by
    exact (mul_le_mul_right_of_neg hL_neg).mp hchain
  nlinarith

/--
Geometric lower-bound to iteration-count bridge.  If near-minimality forces
`(alpha / 8) * q^(2(N+1)) <= eps`, and the target rate is chosen so that the
same `eps` log-ratio lies below `2(rate+1) log q`, then the negative log of
`0 < q < 1` gives `rate <= N`.
-/
theorem chewi45_iteration_count_ge_rate_of_geometric_eps_lower_bound
    {alpha eps q rate : ℝ} {N : ℕ}
    (halpha_pos : 0 < alpha) (heps_pos : 0 < eps)
    (hq_pos : 0 < q) (hq_lt_one : q < 1)
    (hgeo : (alpha / 8) * q ^ (2 * (N + 1)) ≤ eps)
    (hrate_log :
      Real.log (eps / (alpha / 8)) ≤
        (2 * (rate + 1)) * Real.log q) :
    rate ≤ (N : ℝ) := by
  have ha_pos : 0 < alpha / 8 := by positivity
  have hpow_pos : 0 < q ^ (2 * (N + 1)) := pow_pos hq_pos _
  have heps_div_pos : 0 < eps / (alpha / 8) := div_pos heps_pos ha_pos
  have hpow_le : q ^ (2 * (N + 1)) ≤ eps / (alpha / 8) := by
    rw [le_div_iff₀ ha_pos]
    simpa [mul_comm, mul_left_comm, mul_assoc] using hgeo
  have hlog_le :
      Real.log (q ^ (2 * (N + 1))) ≤
        Real.log (eps / (alpha / 8)) :=
    (Real.log_le_log_iff hpow_pos heps_div_pos).2 hpow_le
  have hleft :
      (2 * ((N : ℝ) + 1)) * Real.log q ≤
        Real.log (eps / (alpha / 8)) := by
    rw [Real.log_pow] at hlog_le
    simpa [Nat.cast_mul, Nat.cast_add, Nat.cast_one,
      mul_comm, mul_left_comm, mul_assoc] using hlog_le
  have hchain :
      (2 * ((N : ℝ) + 1)) * Real.log q ≤
        (2 * (rate + 1)) * Real.log q :=
    hleft.trans hrate_log
  exact chewi45_rate_le_iterations_of_log_chain
    (L := Real.log q) (rate := rate) (N := N)
    (Real.log_neg hq_pos hq_lt_one) hchain

/--
The canonical log-quotient rate discharges the scalar log comparison by
equality.  This keeps the final Theorem 4.5 wrappers from carrying a redundant
`hrate_log` hypothesis.
-/
theorem chewi45_logQuotientRate_log_comparison
    {A L : ℝ} (hL : L ≠ 0) :
    A ≤ (2 * (A / (2 * L) - 1 + 1)) * L := by
  have htwoL : 2 * L ≠ 0 := by
    exact mul_ne_zero two_ne_zero hL
  have hcalc : (2 * (A / (2 * L) - 1 + 1)) * L = A := by
    field_simp [htwoL]
    ring
  exact le_of_eq hcalc.symm

/--
Concrete log-quotient form of the geometric lower-bound bridge.  The bound is
written with the exact quotient that makes
`log(eps/(alpha/8)) = 2(rate+1) log q`.
-/
theorem chewi45_iteration_count_ge_logQuotientRate_of_geometric_eps_lower_bound
    {alpha eps q : ℝ} {N : ℕ}
    (halpha_pos : 0 < alpha) (heps_pos : 0 < eps)
    (hq_pos : 0 < q) (hq_lt_one : q < 1)
    (hgeo : (alpha / 8) * q ^ (2 * (N + 1)) ≤ eps) :
    Real.log (eps / (alpha / 8)) / (2 * Real.log q) - 1 ≤
      (N : ℝ) := by
  have hlog_ne : Real.log q ≠ 0 :=
    (Real.log_neg hq_pos hq_lt_one).ne
  exact chewi45_iteration_count_ge_rate_of_geometric_eps_lower_bound
    (alpha := alpha) (eps := eps) (q := q)
    (rate := Real.log (eps / (alpha / 8)) / (2 * Real.log q) - 1)
    (N := N) halpha_pos heps_pos hq_pos hq_lt_one hgeo
    (chewi45_logQuotientRate_log_comparison
      (A := Real.log (eps / (alpha / 8))) (L := Real.log q) hlog_ne)

/--
For `0 < q < 1`, the source-shaped lower bound on `N` for the half-boundary
rate implies the log half-bound at exponent `2(N+1)`.
-/
theorem chewi45_log_half_bound_of_logQuotient_iteration_lower_bound
    {q : ℝ} {N : ℕ} (hq_pos : 0 < q) (hq_lt_one : q < 1)
    (hN_ge :
      Real.log (1 / 2 : ℝ) / (2 * Real.log q) - 1 ≤ (N : ℝ)) :
    ((2 * (N + 1) : ℕ) : ℝ) * Real.log q ≤
      Real.log (1 / 2 : ℝ) := by
  have hlog_neg : Real.log q < 0 := Real.log_neg hq_pos hq_lt_one
  have htwo_log_neg : 2 * Real.log q < 0 := by nlinarith
  have hdiv_le :
      Real.log (1 / 2 : ℝ) / (2 * Real.log q) ≤ (N : ℝ) + 1 := by
    linarith
  have hmul_le :
      ((N : ℝ) + 1) * (2 * Real.log q) ≤ Real.log (1 / 2 : ℝ) :=
    (div_le_iff_of_neg htwo_log_neg).mp hdiv_le
  have hrewrite :
      ((2 * (N + 1) : ℕ) : ℝ) * Real.log q =
        ((N : ℝ) + 1) * (2 * Real.log q) := by
    norm_num [Nat.cast_mul, Nat.cast_add, Nat.cast_one]
    ring
  exact hrewrite.trans_le hmul_le

theorem chewi45_logQuotientRate_le_sqrt_add_one_bound
    {A kappa : ℝ} (hkappa : 1 < kappa) (hA_nonpos : A ≤ 0) :
    A / (2 * Real.log (chewi45GeometricRatio kappa)) - 1 ≤
      -((Real.sqrt kappa + 1) * A) / 4 - 1 := by
  let L := Real.log (chewi45GeometricRatio kappa)
  let S := Real.sqrt kappa + 1
  have hL_neg : L < 0 := by
    exact Real.log_neg (chewi45GeometricRatio_pos hkappa)
      (chewi45GeometricRatio_lt_one kappa)
  have hS_pos : 0 < S := by
    have hsqrt_nonneg : 0 ≤ Real.sqrt kappa := Real.sqrt_nonneg kappa
    linarith [hsqrt_nonneg]
  have hlog_le : L ≤ -2 / S := by
    simpa [L, S] using
      chewi45GeometricRatio_log_le_neg_two_div_sqrt_add_one
        (kappa := kappa) hkappa
  have hden_pos : 0 < 4 / S := by positivity
  have hden_le : 4 / S ≤ -2 * L := by
    have hmul :=
      mul_le_mul_of_nonpos_left hlog_le (by norm_num : (-2 : ℝ) ≤ 0)
    calc
      4 / S = (-2 : ℝ) * (-2 / S) := by
        field_simp [hS_pos.ne']
        norm_num
      _ ≤ -2 * L := by
        simpa [mul_comm, mul_left_comm, mul_assoc] using hmul
  have hquot :
      (-A) / (-2 * L) ≤ (-A) / (4 / S) :=
    div_le_div_of_nonneg_left (neg_nonneg.mpr hA_nonpos) hden_pos hden_le
  have hleft : (-A) / (-2 * L) = A / (2 * L) := by
    have hL_ne : L ≠ 0 := hL_neg.ne
    field_simp [hL_ne]
  have hright : (-A) / (4 / S) = -(S * A) / 4 := by
    have hS_ne : S ≠ 0 := hS_pos.ne'
    field_simp [hS_ne]
  have hmain : A / (2 * L) ≤ -(S * A) / 4 := by
    simpa [hleft, hright] using hquot
  simpa [L, S] using sub_le_sub_right hmain 1

theorem chewi45_sqrt_sub_one_bound_le_logQuotientRate
    {A kappa : ℝ} (hkappa : 1 < kappa) (hA_nonpos : A ≤ 0) :
    -((Real.sqrt kappa - 1) * A) / 4 - 1 ≤
      A / (2 * Real.log (chewi45GeometricRatio kappa)) - 1 := by
  let L := Real.log (chewi45GeometricRatio kappa)
  let S := Real.sqrt kappa - 1
  have hL_neg : L < 0 := by
    exact Real.log_neg (chewi45GeometricRatio_pos hkappa)
      (chewi45GeometricRatio_lt_one kappa)
  have hS_pos : 0 < S := by
    have hsqrt_one : 1 < Real.sqrt kappa := by
      rw [← Real.sqrt_one]
      exact Real.sqrt_lt_sqrt (by norm_num) hkappa
    linarith
  have hlog_lower : -2 / S ≤ L := by
    simpa [L, S] using
      chewi45GeometricRatio_neg_two_div_sqrt_sub_one_le_log
        (kappa := kappa) hkappa
  have hdenL_pos : 0 < -2 * L := by nlinarith
  have hden_le : -2 * L ≤ 4 / S := by
    have hmul :=
      mul_le_mul_of_nonpos_left hlog_lower (by norm_num : (-2 : ℝ) ≤ 0)
    calc
      -2 * L ≤ (-2 : ℝ) * (-2 / S) := by
        simpa [mul_comm, mul_left_comm, mul_assoc] using hmul
      _ = 4 / S := by
        field_simp [hS_pos.ne']
        norm_num
  have hquot :
      (-A) / (4 / S) ≤ (-A) / (-2 * L) :=
    div_le_div_of_nonneg_left (neg_nonneg.mpr hA_nonpos) hdenL_pos hden_le
  have hleft : (-A) / (4 / S) = -(S * A) / 4 := by
    have hS_ne : S ≠ 0 := hS_pos.ne'
    field_simp [hS_ne]
  have hright : (-A) / (-2 * L) = A / (2 * L) := by
    have hL_ne : L ≠ 0 := hL_neg.ne
    field_simp [hL_ne]
  have hmain : -(S * A) / 4 ≤ A / (2 * L) := by
    simpa [hleft, hright] using hquot
  simpa [L, S] using sub_le_sub_right hmain 1

theorem chewi45_two_le_sqrt_of_four_le {kappa : ℝ}
    (hkappa_four : 4 ≤ kappa) :
    (2 : ℝ) ≤ Real.sqrt kappa := by
  have hsq : (2 : ℝ) ^ (2 : ℕ) ≤ kappa := by
    norm_num
    exact hkappa_four
  exact Real.le_sqrt_of_sq_le hsq

theorem chewi45_sqrt_add_one_le_three_halves_sqrt_of_four_le
    {kappa : ℝ} (hkappa_four : 4 ≤ kappa) :
    Real.sqrt kappa + 1 ≤ (3 / 2 : ℝ) * Real.sqrt kappa := by
  have hsqrt_two : (2 : ℝ) ≤ Real.sqrt kappa :=
    chewi45_two_le_sqrt_of_four_le hkappa_four
  nlinarith

theorem chewi45_half_sqrt_le_sqrt_sub_one_of_four_le
    {kappa : ℝ} (hkappa_four : 4 ≤ kappa) :
    Real.sqrt kappa / 2 ≤ Real.sqrt kappa - 1 := by
  have hsqrt_two : (2 : ℝ) ≤ Real.sqrt kappa :=
    chewi45_two_le_sqrt_of_four_le hkappa_four
  nlinarith

theorem chewi45_sqrt_add_one_rate_le_three_halves_sqrt_rate
    {A kappa : ℝ} (hkappa_four : 4 ≤ kappa) (hA_nonpos : A ≤ 0) :
    -((Real.sqrt kappa + 1) * A) / 4 - 1 ≤
      -(((3 / 2 : ℝ) * Real.sqrt kappa) * A) / 4 - 1 := by
  have hle :
      Real.sqrt kappa + 1 ≤ (3 / 2 : ℝ) * Real.sqrt kappa :=
    chewi45_sqrt_add_one_le_three_halves_sqrt_of_four_le hkappa_four
  have hmul :
      ((3 / 2 : ℝ) * Real.sqrt kappa) * A ≤
        (Real.sqrt kappa + 1) * A :=
    mul_le_mul_of_nonpos_right hle hA_nonpos
  nlinarith

theorem chewi45_half_sqrt_rate_le_sqrt_sub_one_rate
    {A kappa : ℝ} (hkappa_four : 4 ≤ kappa) (hA_nonpos : A ≤ 0) :
    -((Real.sqrt kappa / 2) * A) / 4 - 1 ≤
      -((Real.sqrt kappa - 1) * A) / 4 - 1 := by
  have hle :
      Real.sqrt kappa / 2 ≤ Real.sqrt kappa - 1 :=
    chewi45_half_sqrt_le_sqrt_sub_one_of_four_le hkappa_four
  have hmul :
      (Real.sqrt kappa - 1) * A ≤ (Real.sqrt kappa / 2) * A :=
    mul_le_mul_of_nonpos_right hle hA_nonpos
  nlinarith

theorem chewi45_log_half_eq_neg_log_two :
    Real.log (1 / 2 : ℝ) = -Real.log (2 : ℝ) := by
  have hhalf : (1 / 2 : ℝ) = (2 : ℝ)⁻¹ := by norm_num
  rw [hhalf, Real.log_inv]

theorem chewi45_neg_log_eps_div_alpha_eighth_eq_log_alpha_eighth_div_eps
    {alpha eps : ℝ} (halpha_pos : 0 < alpha) (heps_pos : 0 < eps) :
    -Real.log (eps / (alpha / 8)) =
      Real.log ((alpha / 8) / eps) := by
  have ha_pos : 0 < alpha / 8 := by positivity
  have hratio : eps / (alpha / 8) = ((alpha / 8) / eps)⁻¹ := by
    field_simp [halpha_pos.ne', heps_pos.ne', ha_pos.ne']
  rw [hratio, Real.log_inv, neg_neg]

theorem chewi45GeometricRatio_quadratic {kappa : ℝ}
    (hkappa : 1 < kappa) :
    chewi45GeometricRatio kappa ^ (2 : ℕ) -
        (2 + 4 / (kappa - 1)) * chewi45GeometricRatio kappa + 1 = 0 := by
  let s : ℝ := Real.sqrt kappa
  have hkappa_nonneg : 0 ≤ kappa := by linarith
  have hs_sq : s ^ (2 : ℕ) = kappa := by
    simpa [s] using Real.sq_sqrt hkappa_nonneg
  have hden : s + 1 ≠ 0 := by
    have hs_nonneg : 0 ≤ s := by
      simp [s]
    linarith
  have hkden : kappa - 1 ≠ 0 := by linarith
  change ((s - 1) / (s + 1)) ^ (2 : ℕ) -
        (2 + 4 / (kappa - 1)) * ((s - 1) / (s + 1)) + 1 = 0
  field_simp [hden, hkden]
  nlinarith [hs_sq]

theorem chewi45GeometricRatio_recurrence {kappa : ℝ}
    (hkappa : 1 < kappa) :
    (2 + 4 / (kappa - 1)) * chewi45GeometricRatio kappa =
      chewi45GeometricRatio kappa ^ (2 : ℕ) + 1 := by
  have h := chewi45GeometricRatio_quadratic hkappa
  linarith

theorem chewi45GeometricRatio_pow_recurrence {kappa : ℝ}
    (hkappa : 1 < kappa) (n : ℕ) :
    chewi45GeometricRatio kappa ^ (n + 2) -
        (2 + 4 / (kappa - 1)) *
          chewi45GeometricRatio kappa ^ (n + 1) +
        chewi45GeometricRatio kappa ^ n = 0 := by
  let q := chewi45GeometricRatio kappa
  have hquad :
      q ^ (2 : ℕ) - (2 + 4 / (kappa - 1)) * q + 1 = 0 := by
    simpa [q] using chewi45GeometricRatio_quadratic hkappa
  have hmul :
      q ^ n * (q ^ (2 : ℕ) - (2 + 4 / (kappa - 1)) * q + 1) = 0 := by
    rw [hquad, mul_zero]
  change q ^ (n + 2) - (2 + 4 / (kappa - 1)) * q ^ (n + 1) + q ^ n = 0
  rw [pow_add, pow_add, pow_two, pow_one]
  ring_nf at hmul ⊢
  exact hmul

/--
Finite-dimensional geometric vector used as the coordinate model for the
direct Exercise 4.2 hard chain.
-/
noncomputable def strongLowerBoundGeometricCandidate (kappa : ℝ) (d : ℕ) :
    EuclideanSpace ℝ (Fin d) :=
  WithLp.toLp 2 fun i : Fin d =>
    (chewi45GeometricRatio kappa) ^ (i.1 + 1)

theorem strongLowerBoundGeometricCandidate_apply
    (kappa : ℝ) (d : ℕ) (i : Fin d) :
    strongLowerBoundGeometricCandidate kappa d i =
      (chewi45GeometricRatio kappa) ^ (i.1 + 1) := by
  simp [strongLowerBoundGeometricCandidate, PiLp.toLp_apply]

theorem strongLowerBoundChainGradient_geometricCandidate_eq_zero_of_interior
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d : ℕ} {i : Fin d} (hprev : 0 < i.1) (hnext : i.1 + 1 < d) :
    strongLowerBoundChainGradient alpha beta d
      (strongLowerBoundGeometricCandidate kappa d) i = 0 := by
  let q := chewi45GeometricRatio kappa
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hgamma_ne : beta - alpha ≠ 0 := by linarith
  have hkden : kappa - 1 ≠ 0 := by linarith
  have hcoef :
      4 / (kappa - 1) = 4 * alpha / (beta - alpha) := by
    rw [hkappa]
    field_simp [halpha_pos.ne', hgamma_ne]
  have hrec :
      q ^ (i.1 + 2) -
          (2 + 4 * alpha / (beta - alpha)) * q ^ (i.1 + 1) +
        q ^ i.1 = 0 := by
    have h :=
      chewi45GeometricRatio_pow_recurrence (kappa := kappa) hkappa_gt i.1
    simpa [q, hcoef] using h
  have hprev_exp : i.1 - 1 + 1 = i.1 := by omega
  have hnext_exp : i.1 + 1 + 1 = i.1 + 2 := by omega
  rw [strongLowerBoundChainGradient_apply]
  simp [lowerBoundChainGradient, strongLowerBoundGeometricCandidate,
    PiLp.toLp_apply, hprev, hnext, hprev_exp, hnext_exp]
  have hrec_mul :
      (beta - alpha) *
          (2 * q ^ (i.1 + 1) - q ^ i.1 - q ^ (i.1 + 2)) +
        4 * alpha * q ^ (i.1 + 1) = 0 := by
    have hrec' :
        2 * q ^ (i.1 + 1) - q ^ i.1 - q ^ (i.1 + 2) +
            (4 * alpha / (beta - alpha)) * q ^ (i.1 + 1) = 0 := by
      linarith [hrec]
    field_simp [hgamma_ne] at hrec'
    ring_nf at hrec' ⊢
    exact hrec'
  have hmain :
      (beta - alpha) / 4 *
            (2 * q ^ (i.1 + 1) - q ^ i.1 - q ^ (i.1 + 2)) +
          alpha * q ^ (i.1 + 1) =
        0 := by
    field_simp
    linarith [hrec_mul]
  simpa [q, mul_assoc, mul_left_comm, mul_comm] using hmain

theorem strongLowerBoundChainGradient_geometricCandidate_eq_zero_of_first
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d : ℕ} {i : Fin d} (hfirst : i.1 = 0) (hnext : i.1 + 1 < d) :
    strongLowerBoundChainGradient alpha beta d
      (strongLowerBoundGeometricCandidate kappa d) i = 0 := by
  let q := chewi45GeometricRatio kappa
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hgamma_ne : beta - alpha ≠ 0 := by linarith
  have hcoef :
      4 / (kappa - 1) = 4 * alpha / (beta - alpha) := by
    rw [hkappa]
    field_simp [halpha_pos.ne', hgamma_ne]
  have hrec :
      q ^ (0 + 2) -
          (2 + 4 * alpha / (beta - alpha)) * q ^ (0 + 1) +
        q ^ 0 = 0 := by
    have h :=
      chewi45GeometricRatio_pow_recurrence (kappa := kappa) hkappa_gt 0
    simpa [q, hcoef] using h
  have hnext_exp : i.1 + 1 + 1 = 2 := by omega
  have hone_lt_d : 1 < d := by omega
  rw [strongLowerBoundChainGradient_apply]
  simp [lowerBoundChainGradient, strongLowerBoundGeometricCandidate,
    PiLp.toLp_apply, hfirst, hone_lt_d]
  have hrec_mul :
      (beta - alpha) * (2 * q - 1 - q ^ (2 : ℕ)) +
        4 * alpha * q = 0 := by
    have hrec' :
        2 * q - 1 - q ^ (2 : ℕ) +
            (4 * alpha / (beta - alpha)) * q = 0 := by
      norm_num at hrec
      linarith [hrec]
    field_simp [hgamma_ne] at hrec'
    ring_nf at hrec' ⊢
    exact hrec'
  have hmain :
      (beta - alpha) / 4 * (2 * q - 1 - q ^ (2 : ℕ)) +
          alpha * q =
        0 := by
    field_simp
    linarith [hrec_mul]
  simpa [q, mul_assoc, mul_left_comm, mul_comm] using hmain

theorem strongLowerBoundChainGradient_geometricCandidate_eq_zero_of_not_last
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d : ℕ} {i : Fin d} (hnext : i.1 + 1 < d) :
    strongLowerBoundChainGradient alpha beta d
      (strongLowerBoundGeometricCandidate kappa d) i = 0 := by
  by_cases hfirst : i.1 = 0
  · exact strongLowerBoundChainGradient_geometricCandidate_eq_zero_of_first
      halpha_pos halpha_lt_beta hkappa hfirst hnext
  · have hprev : 0 < i.1 := by omega
    exact strongLowerBoundChainGradient_geometricCandidate_eq_zero_of_interior
      halpha_pos halpha_lt_beta hkappa hprev hnext

theorem strongLowerBoundChainGradient_geometricCandidate_eq_terminal_residual
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d : ℕ} {i : Fin d} (hlast : i.1 + 1 = d) :
    strongLowerBoundChainGradient alpha beta d
      (strongLowerBoundGeometricCandidate kappa d) i =
        ((beta - alpha) / 4) *
          (chewi45GeometricRatio kappa) ^ (i.1 + 2) := by
  let q := chewi45GeometricRatio kappa
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hgamma_ne : beta - alpha ≠ 0 := by linarith
  have hcoef :
      4 / (kappa - 1) = 4 * alpha / (beta - alpha) := by
    rw [hkappa]
    field_simp [halpha_pos.ne', hgamma_ne]
  have hrec :
      q ^ (i.1 + 2) -
          (2 + 4 * alpha / (beta - alpha)) * q ^ (i.1 + 1) +
        q ^ i.1 = 0 := by
    have h :=
      chewi45GeometricRatio_pow_recurrence (kappa := kappa) hkappa_gt i.1
    simpa [q, hcoef] using h
  have hrec_mul :
      (beta - alpha) *
          (2 * q ^ (i.1 + 1) - q ^ i.1 - q ^ (i.1 + 2)) +
        4 * alpha * q ^ (i.1 + 1) = 0 := by
    have hrec' :
        2 * q ^ (i.1 + 1) - q ^ i.1 - q ^ (i.1 + 2) +
            (4 * alpha / (beta - alpha)) * q ^ (i.1 + 1) = 0 := by
      linarith [hrec]
    field_simp [hgamma_ne] at hrec'
    ring_nf at hrec' ⊢
    exact hrec'
  rw [strongLowerBoundChainGradient_apply]
  by_cases hfirst : i.1 = 0
  · have hnot_next : ¬i.1 + 1 < d := by omega
    have hone_not_lt : ¬1 < d := by omega
    simp [lowerBoundChainGradient, strongLowerBoundGeometricCandidate,
      PiLp.toLp_apply, hfirst, hone_not_lt]
    have hrec_mul0 :
        (beta - alpha) * (2 * q - 1 - q ^ (2 : ℕ)) + 4 * alpha * q = 0 := by
      simpa [hfirst] using hrec_mul
    have hmain :
        (beta - alpha) / 4 * (2 * q - 1) + alpha * q =
          (beta - alpha) / 4 * q ^ (2 : ℕ) := by
      field_simp
      nlinarith [hrec_mul0]
    simpa [q, hfirst, mul_assoc, mul_left_comm, mul_comm] using hmain
  · have hprev : 0 < i.1 := by omega
    have hnot_next : ¬i.1 + 1 < d := by omega
    have hprev_exp : i.1 - 1 + 1 = i.1 := by omega
    simp [lowerBoundChainGradient, strongLowerBoundGeometricCandidate,
      PiLp.toLp_apply, hprev, hnot_next, hprev_exp]
    have hmain :
        (beta - alpha) / 4 *
              (2 * q ^ (i.1 + 1) - q ^ i.1) +
            alpha * q ^ (i.1 + 1) =
          (beta - alpha) / 4 * q ^ (i.1 + 2) := by
      field_simp
      nlinarith [hrec_mul]
    simpa [q, mul_assoc, mul_left_comm, mul_comm] using hmain

/--
The finite-chain correction denominator for the geometric hard instance is
strictly positive.
-/
theorem chewi45GeometricRatio_finiteDenominator_pos {kappa : ℝ}
    (hkappa : 1 < kappa) (d : ℕ) :
    0 < 1 - (chewi45GeometricRatio kappa) ^ (2 * d + 2) := by
  have hq_nonneg : 0 ≤ chewi45GeometricRatio kappa :=
    chewi45GeometricRatio_nonneg hkappa.le
  have hq_lt_one : chewi45GeometricRatio kappa < 1 :=
    chewi45GeometricRatio_lt_one kappa
  have hexp_ne : 2 * d + 2 ≠ 0 := by omega
  have hpow_lt :
      (chewi45GeometricRatio kappa) ^ (2 * d + 2) < 1 :=
    pow_lt_one₀ hq_nonneg hq_lt_one hexp_ne
  linarith

/-- Nonzero form of `chewi45GeometricRatio_finiteDenominator_pos`. -/
theorem chewi45GeometricRatio_finiteDenominator_ne_zero {kappa : ℝ}
    (hkappa : 1 < kappa) (d : ℕ) :
    1 - (chewi45GeometricRatio kappa) ^ (2 * d + 2) ≠ 0 :=
  (chewi45GeometricRatio_finiteDenominator_pos hkappa d).ne'

/--
Corrected finite-dimensional geometric chain node.  It is the finite-interval
solution of the characteristic recurrence with boundary values `z_0 = 1` and
`z_{d+1} = 0`.
-/
noncomputable def strongLowerBoundFiniteGeometricNode
    (kappa : ℝ) (d j : ℕ) : ℝ :=
  let q := chewi45GeometricRatio kappa
  (q ^ j - q ^ (2 * d + 2 - j)) / (1 - q ^ (2 * d + 2))

/-- The corrected finite geometric node has the left boundary value `1`. -/
theorem strongLowerBoundFiniteGeometricNode_zero {kappa : ℝ}
    (hkappa : 1 < kappa) (d : ℕ) :
    strongLowerBoundFiniteGeometricNode kappa d 0 = 1 := by
  let q := chewi45GeometricRatio kappa
  have hden : 1 - q ^ (2 * d + 2) ≠ 0 := by
    simpa [q] using chewi45GeometricRatio_finiteDenominator_ne_zero hkappa d
  change (q ^ 0 - q ^ (2 * d + 2 - 0)) /
      (1 - q ^ (2 * d + 2)) = 1
  rw [pow_zero, Nat.sub_zero]
  exact div_self hden

/-- The corrected finite geometric node has the right boundary value `0`. -/
theorem strongLowerBoundFiniteGeometricNode_last
    (kappa : ℝ) (d : ℕ) :
    strongLowerBoundFiniteGeometricNode kappa d (d + 1) = 0 := by
  have hsub : 2 * d + 2 - (d + 1) = d + 1 := by omega
  simp [strongLowerBoundFiniteGeometricNode, hsub]

/--
The corrected finite geometric node is nonnegative on the finite interval
`0, ..., d+1`.
-/
theorem strongLowerBoundFiniteGeometricNode_nonneg {kappa : ℝ}
    (hkappa : 1 < kappa) {d j : ℕ} (hj : j ≤ d + 1) :
    0 ≤ strongLowerBoundFiniteGeometricNode kappa d j := by
  let q := chewi45GeometricRatio kappa
  let L := 2 * d + 2
  have hq_pos : 0 < q := by
    simpa [q] using chewi45GeometricRatio_pos hkappa
  have hq_lt_one : q < 1 := by
    simpa [q] using chewi45GeometricRatio_lt_one kappa
  have hD_pos : 0 < 1 - q ^ L := by
    simpa [L, q] using chewi45GeometricRatio_finiteDenominator_pos hkappa d
  have hpow_le : q ^ (L - j) ≤ q ^ j := by
    exact (pow_le_pow_iff_right_of_lt_one₀ hq_pos hq_lt_one).2 (by omega)
  change 0 ≤ (q ^ j - q ^ (L - j)) / (1 - q ^ L)
  exact div_nonneg (sub_nonneg.mpr hpow_le) hD_pos.le

/--
The corrected finite node is bounded above by the pure geometric profile on
the finite interval.  This is the scalar comparison that prevents finite
truncation estimates from accidentally exceeding the infinite-chain profile.
-/
theorem strongLowerBoundFiniteGeometricNode_le_geometric {kappa : ℝ}
    (hkappa : 1 < kappa) {d j : ℕ} (hj : j ≤ d + 1) :
    strongLowerBoundFiniteGeometricNode kappa d j ≤
      (chewi45GeometricRatio kappa) ^ j := by
  let q := chewi45GeometricRatio kappa
  let L := 2 * d + 2
  have hq_pos : 0 < q := by
    simpa [q] using chewi45GeometricRatio_pos hkappa
  have hq_lt_one : q < 1 := by
    simpa [q] using chewi45GeometricRatio_lt_one kappa
  have hD_pos : 0 < 1 - q ^ L := by
    simpa [L, q] using chewi45GeometricRatio_finiteDenominator_pos hkappa d
  have hpow_le : q ^ (j + L) ≤ q ^ (L - j) := by
    exact (pow_le_pow_iff_right_of_lt_one₀ hq_pos hq_lt_one).2 (by omega)
  have hnum_le :
      q ^ j - q ^ (L - j) ≤ q ^ j * (1 - q ^ L) := by
    calc
      q ^ j - q ^ (L - j) ≤ q ^ j - q ^ (j + L) := by
        nlinarith
      _ = q ^ j * (1 - q ^ L) := by
        rw [pow_add]
        ring
  change (q ^ j - q ^ (L - j)) / (1 - q ^ L) ≤ q ^ j
  rw [div_le_iff₀ hD_pos]
  simpa [mul_comm, mul_left_comm, mul_assoc] using hnum_le

/--
Lower comparison between the corrected finite node and the pure geometric
profile, retaining the finite-boundary correction factor.  This is the
finite-dimensional replacement for the exact infinite-chain identity
`z_j = q^j`.
-/
theorem geometric_mul_boundary_le_strongLowerBoundFiniteGeometricNode
    {kappa : ℝ} (hkappa : 1 < kappa) {d j : ℕ} (hj : j ≤ d + 1) :
    (chewi45GeometricRatio kappa) ^ j *
        (1 - (chewi45GeometricRatio kappa) ^ (2 * d + 2 - 2 * j)) ≤
      strongLowerBoundFiniteGeometricNode kappa d j := by
  let q := chewi45GeometricRatio kappa
  let L := 2 * d + 2
  let r := L - 2 * j
  have hq_nonneg : 0 ≤ q := by
    simpa [q] using chewi45GeometricRatio_nonneg hkappa.le
  have hD_pos : 0 < 1 - q ^ L := by
    simpa [L, q] using chewi45GeometricRatio_finiteDenominator_pos hkappa d
  have hD_le_one : 1 - q ^ L ≤ 1 := by
    have hpow_nonneg : 0 ≤ q ^ L := pow_nonneg hq_nonneg L
    linarith
  have hr_le_one : q ^ r ≤ 1 := by
    exact pow_le_one₀ (n := r) hq_nonneg (chewi45GeometricRatio_le_one kappa)
  have hA_nonneg : 0 ≤ q ^ j * (1 - q ^ r) := by
    exact mul_nonneg (pow_nonneg hq_nonneg j) (sub_nonneg.mpr hr_le_one)
  have hsub : L - j = j + r := by omega
  change q ^ j * (1 - q ^ (L - 2 * j)) ≤
    (q ^ j - q ^ (L - j)) / (1 - q ^ L)
  have hr_eq : L - 2 * j = r := by rfl
  rw [hr_eq, hsub, pow_add]
  rw [le_div_iff₀ hD_pos]
  ring_nf
  nlinarith [mul_le_of_le_one_right hA_nonneg hD_le_one]

/--
Finite-dimensional corrected geometric vector for the direct Theorem 4.5 hard
instance.  Coordinate `i` is the corrected node `z_{i+1}`.
-/
noncomputable def strongLowerBoundFiniteGeometricCandidate
    (kappa : ℝ) (d : ℕ) : EuclideanSpace ℝ (Fin d) :=
  WithLp.toLp 2 fun i : Fin d =>
    strongLowerBoundFiniteGeometricNode kappa d (i.1 + 1)

theorem strongLowerBoundFiniteGeometricCandidate_apply
    (kappa : ℝ) (d : ℕ) (i : Fin d) :
    strongLowerBoundFiniteGeometricCandidate kappa d i =
      strongLowerBoundFiniteGeometricNode kappa d (i.1 + 1) := by
  simp [strongLowerBoundFiniteGeometricCandidate, PiLp.toLp_apply]

/-- Coordinates of the corrected finite geometric candidate are nonnegative. -/
theorem strongLowerBoundFiniteGeometricCandidate_nonneg {kappa : ℝ}
    (hkappa : 1 < kappa) {d : ℕ} (i : Fin d) :
    0 ≤ strongLowerBoundFiniteGeometricCandidate kappa d i := by
  rw [strongLowerBoundFiniteGeometricCandidate_apply]
  exact strongLowerBoundFiniteGeometricNode_nonneg hkappa (by omega)

/--
Coordinatewise comparison between the corrected finite geometric candidate
and the pure geometric profile.
-/
theorem strongLowerBoundFiniteGeometricCandidate_le_geometric {kappa : ℝ}
    (hkappa : 1 < kappa) {d : ℕ} (i : Fin d) :
    strongLowerBoundFiniteGeometricCandidate kappa d i ≤
      (chewi45GeometricRatio kappa) ^ (i.1 + 1) := by
  rw [strongLowerBoundFiniteGeometricCandidate_apply]
  exact strongLowerBoundFiniteGeometricNode_le_geometric hkappa (by omega)

/--
Coordinatewise lower comparison against the pure geometric profile with the
finite-boundary correction factor.
-/
theorem geometric_mul_boundary_le_strongLowerBoundFiniteGeometricCandidate
    {kappa : ℝ} (hkappa : 1 < kappa) {d : ℕ} (i : Fin d) :
    (chewi45GeometricRatio kappa) ^ (i.1 + 1) *
        (1 - (chewi45GeometricRatio kappa) ^
          (2 * d + 2 - 2 * (i.1 + 1))) ≤
      strongLowerBoundFiniteGeometricCandidate kappa d i := by
  rw [strongLowerBoundFiniteGeometricCandidate_apply]
  exact geometric_mul_boundary_le_strongLowerBoundFiniteGeometricNode
    hkappa (by omega)

/-- Squared-coordinate version of the finite-to-pure geometric comparison. -/
theorem strongLowerBoundFiniteGeometricCandidate_sq_le_geometric_sq
    {kappa : ℝ} (hkappa : 1 < kappa) {d : ℕ} (i : Fin d) :
    (strongLowerBoundFiniteGeometricCandidate kappa d i) ^ (2 : ℕ) ≤
      ((chewi45GeometricRatio kappa) ^ (i.1 + 1)) ^ (2 : ℕ) := by
  exact (sq_le_sq₀
    (strongLowerBoundFiniteGeometricCandidate_nonneg hkappa i)
    (chewi45GeometricRatio_pow_nonneg hkappa.le (i.1 + 1))).2
      (strongLowerBoundFiniteGeometricCandidate_le_geometric hkappa i)

/-- Squared-coordinate version of the finite-boundary lower comparison. -/
theorem geometric_boundary_sq_le_finiteGeometricCandidate_sq
    {kappa : ℝ} (hkappa : 1 < kappa) {d : ℕ} (i : Fin d) :
    ((chewi45GeometricRatio kappa) ^ (i.1 + 1) *
        (1 - (chewi45GeometricRatio kappa) ^
          (2 * d + 2 - 2 * (i.1 + 1)))) ^ (2 : ℕ) ≤
      (strongLowerBoundFiniteGeometricCandidate kappa d i) ^ (2 : ℕ) := by
  let q := chewi45GeometricRatio kappa
  have hq_nonneg : 0 ≤ q := by
    simpa [q] using chewi45GeometricRatio_nonneg hkappa.le
  have hq_le_one : q ≤ 1 := by
    simpa [q] using chewi45GeometricRatio_le_one kappa
  have hfactor_nonneg :
      0 ≤ q ^ (i.1 + 1) *
        (1 - q ^ (2 * d + 2 - 2 * (i.1 + 1))) := by
    have hpow_le_one :
        q ^ (2 * d + 2 - 2 * (i.1 + 1)) ≤ 1 :=
      pow_le_one₀
        (n := 2 * d + 2 - 2 * (i.1 + 1)) hq_nonneg hq_le_one
    exact mul_nonneg (pow_nonneg hq_nonneg _) (sub_nonneg.mpr hpow_le_one)
  exact (sq_le_sq₀ hfactor_nonneg
    (strongLowerBoundFiniteGeometricCandidate_nonneg hkappa i)).2
      (by
        simpa [q] using
          geometric_mul_boundary_le_strongLowerBoundFiniteGeometricCandidate
            hkappa i)

/--
The corrected finite node satisfies the characteristic second-order recurrence
wherever the three displayed nodes lie in the finite interval.
-/
theorem strongLowerBoundFiniteGeometricNode_recurrence {kappa : ℝ}
    (hkappa : 1 < kappa) (d j : ℕ) (hj : j + 2 ≤ 2 * d + 2) :
    strongLowerBoundFiniteGeometricNode kappa d (j + 2) -
        (2 + 4 / (kappa - 1)) *
          strongLowerBoundFiniteGeometricNode kappa d (j + 1) +
      strongLowerBoundFiniteGeometricNode kappa d j =
        0 := by
  let q := chewi45GeometricRatio kappa
  let D := 1 - q ^ (2 * d + 2)
  let m := 2 * d + 2 - (j + 2)
  have hD : D ≠ 0 := by
    simpa [D, q] using chewi45GeometricRatio_finiteDenominator_ne_zero hkappa d
  have hforward :
      q ^ (j + 2) - (2 + 4 / (kappa - 1)) * q ^ (j + 1) +
        q ^ j = 0 := by
    simpa [q] using chewi45GeometricRatio_pow_recurrence hkappa j
  have hmirror_rec :
      q ^ (m + 2) - (2 + 4 / (kappa - 1)) * q ^ (m + 1) +
        q ^ m = 0 := by
    simpa [q] using chewi45GeometricRatio_pow_recurrence hkappa m
  have hm0 : m + 2 = 2 * d + 2 - j := by omega
  have hm1 : m + 1 = 2 * d + 2 - (j + 1) := by omega
  have hm2 : m = 2 * d + 2 - (j + 2) := by rfl
  rw [hm0, hm1, hm2] at hmirror_rec
  have hmirror :
      q ^ (2 * d + 2 - j) -
          (2 + 4 / (kappa - 1)) *
            q ^ (2 * d + 2 - (j + 1)) +
        q ^ (2 * d + 2 - (j + 2)) =
          0 := by
    simpa [add_assoc] using hmirror_rec
  change
    (q ^ (j + 2) - q ^ (2 * d + 2 - (j + 2))) / D -
        (2 + 4 / (kappa - 1)) *
          ((q ^ (j + 1) - q ^ (2 * d + 2 - (j + 1))) / D) +
      (q ^ j - q ^ (2 * d + 2 - j)) / D =
        0
  field_simp [hD]
  nlinarith [hforward, hmirror]

/--
The corrected finite geometric vector is an exact zero-gradient point for the
regularized finite hard chain.
-/
theorem strongLowerBoundChainGradient_finiteGeometricCandidate_eq_zero
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    (d : ℕ) :
    strongLowerBoundChainGradient alpha beta d
      (strongLowerBoundFiniteGeometricCandidate kappa d) = 0 := by
  ext i
  let z := strongLowerBoundFiniteGeometricNode kappa d
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hgamma_ne : beta - alpha ≠ 0 := by linarith
  have hcoef :
      4 / (kappa - 1) = 4 * alpha / (beta - alpha) := by
    rw [hkappa]
    field_simp [halpha_pos.ne', hgamma_ne]
  have hjbound : i.1 + 2 ≤ 2 * d + 2 := by omega
  have hrec :
      z (i.1 + 2) -
          (2 + 4 * alpha / (beta - alpha)) * z (i.1 + 1) +
        z i.1 =
          0 := by
    have h :=
      strongLowerBoundFiniteGeometricNode_recurrence
        (kappa := kappa) hkappa_gt d i.1 hjbound
    simpa [z, hcoef] using h
  have hrec_mul :
      (beta - alpha) *
          (2 * z (i.1 + 1) - z i.1 - z (i.1 + 2)) +
        4 * alpha * z (i.1 + 1) =
          0 := by
    have hrec' :
        2 * z (i.1 + 1) - z i.1 - z (i.1 + 2) +
            (4 * alpha / (beta - alpha)) * z (i.1 + 1) = 0 := by
      linarith [hrec]
    field_simp [hgamma_ne] at hrec'
    ring_nf at hrec' ⊢
    exact hrec'
  have hmain :
      (beta - alpha) / 4 *
            (2 * z (i.1 + 1) - z i.1 - z (i.1 + 2)) +
          alpha * z (i.1 + 1) =
        0 := by
    field_simp
    linarith [hrec_mul]
  have hnode_zero : z 0 = 1 := by
    simpa [z] using strongLowerBoundFiniteGeometricNode_zero hkappa_gt d
  have hnode_last : z (d + 1) = 0 := by
    simpa [z] using strongLowerBoundFiniteGeometricNode_last kappa d
  rw [strongLowerBoundChainGradient_apply]
  by_cases hprev : 0 < i.1
  · by_cases hnext : i.1 + 1 < d
    · have hprev_exp : i.1 - 1 + 1 = i.1 := by omega
      have hnext_exp : i.1 + 1 + 1 = i.1 + 2 := by omega
      simp [lowerBoundChainGradient, strongLowerBoundFiniteGeometricCandidate,
        PiLp.toLp_apply, hprev, hnext, hprev_exp, hnext_exp]
      simpa [z, mul_assoc, mul_left_comm, mul_comm] using hmain
    · have hprev_exp : i.1 - 1 + 1 = i.1 := by omega
      have hnext_node : z (i.1 + 2) = 0 := by
        have hidx : i.1 + 2 = d + 1 := by omega
        simpa [hidx] using hnode_last
      have hmain' := hmain
      rw [hnext_node] at hmain'
      simp at hmain'
      simp [lowerBoundChainGradient, strongLowerBoundFiniteGeometricCandidate,
        PiLp.toLp_apply, hprev, hnext, hprev_exp]
      simpa [z, mul_assoc, mul_left_comm, mul_comm] using hmain'
  · have hfirst : i.1 = 0 := by omega
    have hprev_node : z i.1 = 1 := by
      simpa [hfirst] using hnode_zero
    by_cases hnext : i.1 + 1 < d
    · have hnext_exp : i.1 + 1 + 1 = i.1 + 2 := by omega
      have hone_lt_d : 1 < d := by omega
      have hmain' := hmain
      rw [hprev_node] at hmain'
      simp [hfirst] at hmain'
      simp [lowerBoundChainGradient, strongLowerBoundFiniteGeometricCandidate,
        PiLp.toLp_apply, hfirst, hone_lt_d]
      simpa [z, mul_assoc, mul_left_comm, mul_comm] using hmain'
    · have hnext_node : z (i.1 + 2) = 0 := by
        have hidx : i.1 + 2 = d + 1 := by omega
        simpa [hidx] using hnode_last
      have hone_not_lt : ¬1 < d := by omega
      have hmain' := hmain
      rw [hprev_node, hnext_node] at hmain'
      simp [hfirst] at hmain'
      simp [lowerBoundChainGradient, strongLowerBoundFiniteGeometricCandidate,
        PiLp.toLp_apply, hfirst, hone_not_lt]
      simpa [z, mul_assoc, mul_left_comm, mul_comm] using hmain'

/-- Squared coordinate tail beyond the source prefix subspace `V_N`. -/
noncomputable def coordinateTailSq (d N : ℕ)
    (z : EuclideanSpace ℝ (Fin d)) : ℝ :=
  Finset.sum (Finset.univ.filter (fun i : Fin d => N ≤ i.1))
    (fun i : Fin d => (z i) ^ (2 : ℕ))

/-- Coordinate-tail energy is nonnegative. -/
theorem coordinateTailSq_nonneg (d N : ℕ)
    (z : EuclideanSpace ℝ (Fin d)) :
    0 ≤ coordinateTailSq d N z := by
  unfold coordinateTailSq
  exact Finset.sum_nonneg fun _ _ => sq_nonneg _

/-- A single tail coordinate is bounded by the full coordinate-tail energy. -/
theorem coordinate_sq_le_coordinateTailSq
    {d N : ℕ} (z : EuclideanSpace ℝ (Fin d)) {i : Fin d}
    (hi : N ≤ i.1) :
    (z i) ^ (2 : ℕ) ≤ coordinateTailSq d N z := by
  unfold coordinateTailSq
  exact Finset.single_le_sum
    (fun _ _ => sq_nonneg _)
    (Finset.mem_filter.mpr ⟨Finset.mem_univ i, hi⟩)

/--
Coordinate-tail energy is antitone in the prefix length: asking for a later
tail can only remove nonnegative coordinate squares.
-/
theorem coordinateTailSq_anti_mono
    {d M N : ℕ} (hMN : M ≤ N) (z : EuclideanSpace ℝ (Fin d)) :
    coordinateTailSq d N z ≤ coordinateTailSq d M z := by
  unfold coordinateTailSq
  exact Finset.sum_le_sum_of_subset_of_nonneg
    (by
      intro i hi
      exact Finset.mem_filter.mpr
        ⟨Finset.mem_univ i, hMN.trans (Finset.mem_filter.mp hi).2⟩)
    (fun _ _ _ => sq_nonneg _)

/-- The zero-prefix tail is the full squared Euclidean norm. -/
theorem coordinateTailSq_zero_eq_norm_sq
    {d : ℕ} (z : EuclideanSpace ℝ (Fin d)) :
    coordinateTailSq d 0 z = ‖z‖ ^ (2 : ℕ) := by
  rw [EuclideanSpace.real_norm_sq_eq]
  unfold coordinateTailSq
  simp

/-- Source-shaped form for the initial point `0` used in lower-bound proofs. -/
theorem norm_zero_sub_sq_eq_coordinateTailSq_zero
    {d : ℕ} (z : EuclideanSpace ℝ (Fin d)) :
    ‖(0 : EuclideanSpace ℝ (Fin d)) - z‖ ^ (2 : ℕ) =
      coordinateTailSq d 0 z := by
  rw [zero_sub, norm_neg, coordinateTailSq_zero_eq_norm_sq]

/--
Tail energy of the corrected finite geometric candidate is bounded above by
the corresponding pure-geometric finite tail.
-/
theorem coordinateTailSq_finiteGeometricCandidate_le_geometric
    {kappa : ℝ} (hkappa : 1 < kappa) (d N : ℕ) :
    coordinateTailSq d N (strongLowerBoundFiniteGeometricCandidate kappa d) ≤
      Finset.sum (Finset.univ.filter (fun i : Fin d => N ≤ i.1))
        (fun i : Fin d =>
          ((chewi45GeometricRatio kappa) ^ (i.1 + 1)) ^ (2 : ℕ)) := by
  unfold coordinateTailSq
  exact Finset.sum_le_sum fun i _ =>
    strongLowerBoundFiniteGeometricCandidate_sq_le_geometric_sq hkappa i

/--
The first undiscovered coordinate contributes to the tail energy whenever it
exists.  This packages the `V_N` tail lower bound in the form used by the
lower-bound obstruction.
-/
theorem finiteGeometricCandidate_coordinate_sq_le_coordinateTailSq
    {kappa : ℝ} (d N : ℕ) (hN : N < d) :
    (strongLowerBoundFiniteGeometricCandidate kappa d ⟨N, hN⟩) ^
        (2 : ℕ) ≤
      coordinateTailSq d N (strongLowerBoundFiniteGeometricCandidate kappa d) :=
  coordinate_sq_le_coordinateTailSq
    (strongLowerBoundFiniteGeometricCandidate kappa d) (i := ⟨N, hN⟩) le_rfl

/--
Concrete one-coordinate lower bound for the corrected finite candidate tail.
It is weak compared with the eventual full-tail comparison, but it is robust
and keeps the finite-boundary correction factor explicit.
-/
theorem geometric_boundary_sq_le_finiteGeometricCandidate_coordinateTailSq
    {kappa : ℝ} (hkappa : 1 < kappa) (d N : ℕ) (hN : N < d) :
    ((chewi45GeometricRatio kappa) ^ (N + 1) *
        (1 - (chewi45GeometricRatio kappa) ^
          (2 * d + 2 - 2 * (N + 1)))) ^ (2 : ℕ) ≤
      coordinateTailSq d N (strongLowerBoundFiniteGeometricCandidate kappa d) := by
  have hcoord :=
    geometric_boundary_sq_le_finiteGeometricCandidate_sq
      (kappa := kappa) hkappa (d := d) ⟨N, hN⟩
  have htail :=
    finiteGeometricCandidate_coordinate_sq_le_coordinateTailSq
      (kappa := kappa) d N hN
  exact hcoord.trans htail

/--
If `x ∈ V_N`, then the squared distance from `x` to any `z` controls the
tail energy of `z` outside `V_N`.
-/
theorem coordinateTailSq_le_sqdist_of_mem_coordinatePrefixSubmodule
    {d N : ℕ} {x z : EuclideanSpace ℝ (Fin d)}
    (hx : x ∈ coordinatePrefixSubmodule d N) :
    coordinateTailSq d N z ≤ ‖x - z‖ ^ (2 : ℕ) := by
  rw [EuclideanSpace.real_norm_sq_eq]
  have htail_eq :
      coordinateTailSq d N z =
        Finset.sum (Finset.univ.filter (fun i : Fin d => N ≤ i.1))
          (fun i : Fin d => ((x - z) i) ^ (2 : ℕ)) := by
    unfold coordinateTailSq
    refine Finset.sum_congr rfl ?_
    intro i hi
    have hNi : N ≤ i.1 := (Finset.mem_filter.mp hi).2
    have hxi : x i = 0 := hx i hNi
    simp [hxi]
  rw [htail_eq]
  exact Finset.sum_le_sum_of_subset_of_nonneg
    (by exact Finset.filter_subset _ _)
    (fun _ _ _ => sq_nonneg _)

/--
Tail-energy gap lower bound for the strongly-convex chain from a supplied
zero-gradient minimizer candidate.
-/
theorem strongLowerBoundChainObjective_gap_ge_tailSq_of_gradient_eq_zero
    {alpha beta : ℝ} (halpha_nonneg : 0 ≤ alpha)
    (halpha_le_beta : alpha ≤ beta) {d N : ℕ}
    {x xStar : EuclideanSpace ℝ (Fin d)}
    (hx_prefix : x ∈ coordinatePrefixSubmodule d N)
    (hgrad_zero : strongLowerBoundChainGradient alpha beta d xStar = 0) :
    (alpha / 2) * coordinateTailSq d N xStar ≤
      strongLowerBoundChainObjective alpha beta d x -
        strongLowerBoundChainObjective alpha beta d xStar := by
  have hfirst :=
    strongLowerBoundChainObjective_firstOrderStrongConvexOn
      (alpha := alpha) (beta := beta) halpha_le_beta d
  have hmodel := hfirst.lower_model
    (by simp : xStar ∈ Set.univ) (by simp : x ∈ Set.univ)
  have htail_le :
      coordinateTailSq d N xStar ≤ ‖x - xStar‖ ^ (2 : ℕ) :=
    coordinateTailSq_le_sqdist_of_mem_coordinatePrefixSubmodule hx_prefix
  have hmul :
      (alpha / 2) * coordinateTailSq d N xStar ≤
        (alpha / 2) * ‖x - xStar‖ ^ (2 : ℕ) := by
    exact mul_le_mul_of_nonneg_left htail_le (by nlinarith)
  simp [hgrad_zero] at hmodel
  nlinarith

/--
Gradient-span version of the tail-energy gap bound.  The prefix membership is
discharged by the compiled support induction for the strongly-convex chain.
-/
theorem strongLowerBoundChainObjective_gap_ge_tailSq_of_gradientSpanTrajectory
    {alpha beta : ℝ} (halpha_nonneg : 0 ≤ alpha)
    (halpha_le_beta : alpha ≤ beta) {d N : ℕ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    {xStar : EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hgrad_zero : strongLowerBoundChainGradient alpha beta d xStar = 0) :
    (alpha / 2) * coordinateTailSq d N xStar ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d xStar := by
  have hx_prefix :
      x N ∈ coordinatePrefixSubmodule d N :=
    gradientSpanTrajectory_mem_coordinatePrefixSubmodule_of_strongLowerBoundChainGradient
      (x := x) hx0 hspan N
  exact strongLowerBoundChainObjective_gap_ge_tailSq_of_gradient_eq_zero
    halpha_nonneg halpha_le_beta hx_prefix hgrad_zero

/--
Direct geometric-tail lower bound for the strongly-convex lower-bound chain.
This is the reusable core of the Exercise 4.2 route: once the minimizer's tail
past `V_N` is bounded below by a geometric multiple of the initial squared
distance, the function-value gap of every gradient-span iterate has the same
geometric obstruction.
-/
theorem strongLowerBoundChainObjective_gap_ge_geometric_tail_of_gradientSpanTrajectory
    {alpha beta q : ℝ} (halpha_nonneg : 0 ≤ alpha)
    (halpha_le_beta : alpha ≤ beta) {d N : ℕ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    {xStar : EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hgrad_zero : strongLowerBoundChainGradient alpha beta d xStar = 0)
    (htail_ge :
      q ^ (2 * N) * ‖x 0 - xStar‖ ^ (2 : ℕ) ≤
        coordinateTailSq d N xStar) :
    (alpha / 2) *
        (q ^ (2 * N) * ‖x 0 - xStar‖ ^ (2 : ℕ)) ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d xStar := by
  have htail :=
    strongLowerBoundChainObjective_gap_ge_tailSq_of_gradientSpanTrajectory
      (alpha := alpha) (beta := beta)
      halpha_nonneg halpha_le_beta (N := N)
      (x := x) (xStar := xStar) hx0 hspan hgrad_zero
  have hcoef_nonneg : 0 ≤ alpha / 2 := by nlinarith
  have hscaled :
      (alpha / 2) *
          (q ^ (2 * N) * ‖x 0 - xStar‖ ^ (2 : ℕ)) ≤
        (alpha / 2) * coordinateTailSq d N xStar :=
    mul_le_mul_of_nonneg_left htail_ge hcoef_nonneg
  exact hscaled.trans htail

/--
Source-shaped specialization of the direct Exercise 4.2 geometric obstruction
using Chewi's displayed factor `(sqrt kappa - 1)/(sqrt kappa + 1)`.
-/
theorem chewi45_gap_ge_geometricRatio_tail_of_gradientSpanTrajectory
    {alpha beta kappa : ℝ} (halpha_nonneg : 0 ≤ alpha)
    (halpha_le_beta : alpha ≤ beta) {d N : ℕ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    {xStar : EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hgrad_zero : strongLowerBoundChainGradient alpha beta d xStar = 0)
    (htail_ge :
      (chewi45GeometricRatio kappa) ^ (2 * N) *
          ‖x 0 - xStar‖ ^ (2 : ℕ) ≤
        coordinateTailSq d N xStar) :
    (alpha / 2) *
        ((chewi45GeometricRatio kappa) ^ (2 * N) *
          ‖x 0 - xStar‖ ^ (2 : ℕ)) ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d xStar := by
  exact strongLowerBoundChainObjective_gap_ge_geometric_tail_of_gradientSpanTrajectory
    (alpha := alpha) (beta := beta)
    (q := chewi45GeometricRatio kappa)
    halpha_nonneg halpha_le_beta (N := N)
    (x := x) (xStar := xStar)
    hx0 hspan hgrad_zero htail_ge

/--
Concrete finite-candidate version of the direct geometric-tail lower bound:
the zero-gradient point is the corrected finite geometric vector, so the only
remaining analytic input is the tail comparison.
-/
theorem chewi45_gap_ge_geometricRatio_tail_of_finiteGeometricCandidate
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N : ℕ} {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (htail_ge :
      (chewi45GeometricRatio kappa) ^ (2 * N) *
          ‖x 0 - strongLowerBoundFiniteGeometricCandidate kappa d‖ ^
            (2 : ℕ) ≤
        coordinateTailSq d N
          (strongLowerBoundFiniteGeometricCandidate kappa d)) :
    (alpha / 2) *
        ((chewi45GeometricRatio kappa) ^ (2 * N) *
          ‖x 0 - strongLowerBoundFiniteGeometricCandidate kappa d‖ ^
            (2 : ℕ)) ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) := by
  have hgrad_zero :=
    strongLowerBoundChainGradient_finiteGeometricCandidate_eq_zero
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_pos halpha_lt_beta hkappa d
  exact chewi45_gap_ge_geometricRatio_tail_of_gradientSpanTrajectory
    (alpha := alpha) (beta := beta) (kappa := kappa)
    halpha_pos.le halpha_lt_beta.le (N := N)
    (x := x) (xStar := strongLowerBoundFiniteGeometricCandidate kappa d)
    hx0 hspan hgrad_zero htail_ge

/--
Same concrete lower bound as
`chewi45_gap_ge_geometricRatio_tail_of_finiteGeometricCandidate`, but with the
remaining tail comparison stated purely in coordinate-tail language.  This is
the form to attack next for finite truncations or infinite-model limits.
-/
theorem chewi45_gap_ge_geometricRatio_tail_of_finiteGeometricCandidate_tailSq
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N : ℕ} {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (htail_ge :
      (chewi45GeometricRatio kappa) ^ (2 * N) *
          coordinateTailSq d 0
            (strongLowerBoundFiniteGeometricCandidate kappa d) ≤
        coordinateTailSq d N
          (strongLowerBoundFiniteGeometricCandidate kappa d)) :
    (alpha / 2) *
        ((chewi45GeometricRatio kappa) ^ (2 * N) *
          ‖x 0 - strongLowerBoundFiniteGeometricCandidate kappa d‖ ^
            (2 : ℕ)) ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) := by
  have hnorm :
      ‖x 0 - strongLowerBoundFiniteGeometricCandidate kappa d‖ ^ (2 : ℕ) =
        coordinateTailSq d 0
          (strongLowerBoundFiniteGeometricCandidate kappa d) := by
    rw [hx0]
    exact norm_zero_sub_sq_eq_coordinateTailSq_zero
      (strongLowerBoundFiniteGeometricCandidate kappa d)
  have htail_ge' :
      (chewi45GeometricRatio kappa) ^ (2 * N) *
          ‖x 0 - strongLowerBoundFiniteGeometricCandidate kappa d‖ ^
            (2 : ℕ) ≤
        coordinateTailSq d N
          (strongLowerBoundFiniteGeometricCandidate kappa d) := by
    simpa [hnorm] using htail_ge
  exact chewi45_gap_ge_geometricRatio_tail_of_finiteGeometricCandidate
    (alpha := alpha) (beta := beta) (kappa := kappa)
    halpha_pos halpha_lt_beta hkappa (N := N)
    (x := x) hx0 hspan htail_ge'

/--
Concrete finite-boundary lower bound obtained from one tail coordinate of the
corrected finite geometric minimizer.  This is weaker than the exact
infinite-chain `q^(2N)` tail identity, but it is a fully discharged finite
obstruction with no supplied tail-comparison hypothesis.
-/
theorem chewi45_gap_ge_geometric_boundary_of_finiteGeometricCandidate
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N : ℕ} (hN : N < d)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x) :
    (alpha / 2) *
        (((chewi45GeometricRatio kappa) ^ (N + 1) *
          (1 - (chewi45GeometricRatio kappa) ^
            (2 * d + 2 - 2 * (N + 1)))) ^ (2 : ℕ)) ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) := by
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hgrad_zero :=
    strongLowerBoundChainGradient_finiteGeometricCandidate_eq_zero
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_pos halpha_lt_beta hkappa d
  have htail :=
    strongLowerBoundChainObjective_gap_ge_tailSq_of_gradientSpanTrajectory
      (alpha := alpha) (beta := beta)
      halpha_pos.le halpha_lt_beta.le (N := N)
      (x := x)
      (xStar := strongLowerBoundFiniteGeometricCandidate kappa d)
      hx0 hspan hgrad_zero
  have hboundary :=
    geometric_boundary_sq_le_finiteGeometricCandidate_coordinateTailSq
      (kappa := kappa) hkappa_gt d N hN
  have hcoef_nonneg : 0 ≤ alpha / 2 := by nlinarith
  have hscaled :
      (alpha / 2) *
          (((chewi45GeometricRatio kappa) ^ (N + 1) *
            (1 - (chewi45GeometricRatio kappa) ^
              (2 * d + 2 - 2 * (N + 1)))) ^ (2 : ℕ)) ≤
        (alpha / 2) *
          coordinateTailSq d N
            (strongLowerBoundFiniteGeometricCandidate kappa d) :=
    mul_le_mul_of_nonneg_left hboundary hcoef_nonneg
  exact hscaled.trans htail

/--
Finite-boundary obstruction with a supplied lower floor for the boundary
factor.  This separates the hard-chain proof from the later dimension/slack
choice: any usable floor for
`1 - q^(2d+2-2(N+1))` immediately yields a concrete gap lower bound.
-/
theorem chewi45_gap_ge_geometric_boundary_floor_of_finiteGeometricCandidate
    {alpha beta kappa c : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    (hc_nonneg : 0 ≤ c) {d N : ℕ} (hN : N < d)
    (hfloor :
      c ≤ 1 - (chewi45GeometricRatio kappa) ^
        (2 * d + 2 - 2 * (N + 1)))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x) :
    (alpha / 2) *
        (((chewi45GeometricRatio kappa) ^ (N + 1) * c) ^ (2 : ℕ)) ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) := by
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hqpow_nonneg :
      0 ≤ (chewi45GeometricRatio kappa) ^ (N + 1) :=
    chewi45GeometricRatio_pow_nonneg hkappa_gt.le (N + 1)
  have hboundary_nonneg :
      0 ≤ 1 - (chewi45GeometricRatio kappa) ^
        (2 * d + 2 - 2 * (N + 1)) :=
    hc_nonneg.trans hfloor
  have hleft_nonneg :
      0 ≤ (chewi45GeometricRatio kappa) ^ (N + 1) * c :=
    mul_nonneg hqpow_nonneg hc_nonneg
  have hright_nonneg :
      0 ≤ (chewi45GeometricRatio kappa) ^ (N + 1) *
        (1 - (chewi45GeometricRatio kappa) ^
          (2 * d + 2 - 2 * (N + 1))) :=
    mul_nonneg hqpow_nonneg hboundary_nonneg
  have hbase :
      (chewi45GeometricRatio kappa) ^ (N + 1) * c ≤
        (chewi45GeometricRatio kappa) ^ (N + 1) *
          (1 - (chewi45GeometricRatio kappa) ^
            (2 * d + 2 - 2 * (N + 1))) :=
    mul_le_mul_of_nonneg_left hfloor hqpow_nonneg
  have hsquare :
      (((chewi45GeometricRatio kappa) ^ (N + 1) * c) ^ (2 : ℕ)) ≤
        (((chewi45GeometricRatio kappa) ^ (N + 1) *
          (1 - (chewi45GeometricRatio kappa) ^
            (2 * d + 2 - 2 * (N + 1)))) ^ (2 : ℕ)) :=
    (sq_le_sq₀ hleft_nonneg hright_nonneg).2 hbase
  have hcoef_nonneg : 0 ≤ alpha / 2 := by nlinarith
  have hscaled :=
    mul_le_mul_of_nonneg_left hsquare hcoef_nonneg
  exact hscaled.trans
    (chewi45_gap_ge_geometric_boundary_of_finiteGeometricCandidate
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_pos halpha_lt_beta hkappa (N := N) hN
      (x := x) hx0 hspan)

/--
Half-boundary finite slack corollary.  If the terminal correction has decayed
below `1/2`, the finite corrected minimizer gives the clean lower bound
`(alpha/8) * q^(2(N+1))`.
-/
theorem chewi45_gap_ge_geometric_half_boundary_of_finiteGeometricCandidate
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N : ℕ} (hN : N < d)
    (hboundary_half :
      (chewi45GeometricRatio kappa) ^
          (2 * d + 2 - 2 * (N + 1)) ≤ (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x) :
    (alpha / 8) * (chewi45GeometricRatio kappa) ^ (2 * (N + 1)) ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) := by
  have hfloor :
      (1 / 2 : ℝ) ≤ 1 - (chewi45GeometricRatio kappa) ^
        (2 * d + 2 - 2 * (N + 1)) := by
    linarith
  have hmain :=
    chewi45_gap_ge_geometric_boundary_floor_of_finiteGeometricCandidate
      (alpha := alpha) (beta := beta) (kappa := kappa) (c := (1 / 2 : ℝ))
      halpha_pos halpha_lt_beta hkappa (by norm_num) (N := N) hN
      hfloor (x := x) hx0 hspan
  have hrewrite :
      (alpha / 2) *
          (((chewi45GeometricRatio kappa) ^ (N + 1) * (1 / 2 : ℝ)) ^
            (2 : ℕ)) =
        (alpha / 8) *
          (chewi45GeometricRatio kappa) ^ (2 * (N + 1)) := by
    calc
      (alpha / 2) *
          (((chewi45GeometricRatio kappa) ^ (N + 1) * (1 / 2 : ℝ)) ^
            (2 : ℕ)) =
          (alpha / 8) *
            ((chewi45GeometricRatio kappa) ^ (N + 1) *
              (chewi45GeometricRatio kappa) ^ (N + 1)) := by
        ring
      _ = (alpha / 8) *
            (chewi45GeometricRatio kappa) ^ ((N + 1) + (N + 1)) := by
        rw [← pow_add]
      _ = (alpha / 8) *
            (chewi45GeometricRatio kappa) ^ (2 * (N + 1)) := by
        have hexp : (N + 1) + (N + 1) = 2 * (N + 1) := by
          omega
        rw [hexp]
  rw [← hrewrite]
  exact hmain

/--
For Chewi's ratio `q <= 1`, a half-bound proved at a smaller exponent remains
true at every larger exponent.  This is the monotonicity bridge needed by the
finite-dimensional slack route.
-/
theorem chewi45GeometricRatio_pow_le_half_of_exponent_le
    {kappa : ℝ} (hkappa : 1 ≤ kappa) {m n : ℕ}
    (hmn : m ≤ n)
    (hm_half : (chewi45GeometricRatio kappa) ^ m ≤ (1 / 2 : ℝ)) :
    (chewi45GeometricRatio kappa) ^ n ≤ (1 / 2 : ℝ) := by
  have hq_nonneg : 0 ≤ chewi45GeometricRatio kappa :=
    chewi45GeometricRatio_nonneg hkappa
  have hq_le_one : chewi45GeometricRatio kappa ≤ 1 :=
    chewi45GeometricRatio_le_one kappa
  exact (pow_le_pow_of_le_one hq_nonneg hq_le_one hmn).trans hm_half

/--
Boundary-condition wrapper for the finite slack route: it is enough to prove
`q^M <= 1/2` for any `M` below the available finite-boundary exponent.
-/
theorem chewi45_half_boundary_condition_of_exponent_le
    {kappa : ℝ} (hkappa : 1 ≤ kappa) {d N M : ℕ}
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_half : (chewi45GeometricRatio kappa) ^ M ≤ (1 / 2 : ℝ)) :
    (chewi45GeometricRatio kappa) ^
        (2 * d + 2 - 2 * (N + 1)) ≤ (1 / 2 : ℝ) :=
  chewi45GeometricRatio_pow_le_half_of_exponent_le
    (kappa := kappa) hkappa hM_le hM_half

/--
Logarithmic version of the finite half-boundary condition.  It is enough to
prove a log inequality at any smaller exponent `M`.
-/
theorem chewi45_half_boundary_condition_of_log_exponent_le
    {kappa : ℝ} (hkappa : 1 < kappa) {d N M : ℕ}
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_log :
      (M : ℝ) * Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ)) :
    (chewi45GeometricRatio kappa) ^
        (2 * d + 2 - 2 * (N + 1)) ≤ (1 / 2 : ℝ) := by
  exact chewi45_half_boundary_condition_of_exponent_le
    (kappa := kappa) hkappa.le hM_le
    (chewi45GeometricRatio_pow_le_half_of_nat_mul_log_le
      (kappa := kappa) hkappa hM_log)

/--
Half-boundary gap bound with the boundary condition supplied at any smaller
exponent `M`.  This is the form intended for the upcoming logarithmic
dimension choice.
-/
theorem chewi45_gap_ge_geometric_half_boundary_of_finiteGeometricCandidate_of_exponent_le
    {alpha beta kappa : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N M : ℕ} (hN : N < d)
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_half : (chewi45GeometricRatio kappa) ^ M ≤ (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x) :
    (alpha / 8) * (chewi45GeometricRatio kappa) ^ (2 * (N + 1)) ≤
      strongLowerBoundChainObjective alpha beta d (x N) -
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) := by
  have hkappa_ge : 1 ≤ kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta |>.le
  have hboundary_half :=
    chewi45_half_boundary_condition_of_exponent_le
      (kappa := kappa) hkappa_ge hM_le hM_half
  exact chewi45_gap_ge_geometric_half_boundary_of_finiteGeometricCandidate
    (alpha := alpha) (beta := beta) (kappa := kappa)
    halpha_pos halpha_lt_beta hkappa (N := N) hN hboundary_half
    (x := x) hx0 hspan

/--
Contradiction form of the direct Exercise 4.2 obstruction: an iterate whose
gap is at most `eps` cannot exist if `eps` lies below the geometric tail lower
bound.
-/
theorem chewi45_not_near_min_of_geometricRatio_tail_lower_bound
    {alpha beta kappa eps : ℝ} (halpha_nonneg : 0 ≤ alpha)
    (halpha_le_beta : alpha ≤ beta) {d N : ℕ}
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    {xStar : EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hgrad_zero : strongLowerBoundChainGradient alpha beta d xStar = 0)
    (htail_ge :
      (chewi45GeometricRatio kappa) ^ (2 * N) *
          ‖x 0 - xStar‖ ^ (2 : ℕ) ≤
        coordinateTailSq d N xStar)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d xStar + eps)
    (heps_lt :
      eps <
        (alpha / 2) *
          ((chewi45GeometricRatio kappa) ^ (2 * N) *
            ‖x 0 - xStar‖ ^ (2 : ℕ))) :
    False := by
  have hgap_ge :=
    chewi45_gap_ge_geometricRatio_tail_of_gradientSpanTrajectory
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_nonneg halpha_le_beta (N := N)
      (x := x) (xStar := xStar)
      hx0 hspan hgrad_zero htail_ge
  have hgap_le :
      strongLowerBoundChainObjective alpha beta d (x N) -
          strongLowerBoundChainObjective alpha beta d xStar ≤ eps := by
    linarith
  linarith

/--
Contradiction form with the concrete corrected finite geometric minimizer.
This removes the supplied zero-gradient hypothesis from the previous wrapper.
-/
theorem chewi45_not_near_min_of_finiteGeometricCandidate_tail_lower_bound
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N : ℕ} {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (htail_ge :
      (chewi45GeometricRatio kappa) ^ (2 * N) *
          ‖x 0 - strongLowerBoundFiniteGeometricCandidate kappa d‖ ^
            (2 : ℕ) ≤
        coordinateTailSq d N
          (strongLowerBoundFiniteGeometricCandidate kappa d))
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps)
    (heps_lt :
      eps <
        (alpha / 2) *
          ((chewi45GeometricRatio kappa) ^ (2 * N) *
            ‖x 0 - strongLowerBoundFiniteGeometricCandidate kappa d‖ ^
              (2 : ℕ))) :
    False := by
  have hgrad_zero :=
    strongLowerBoundChainGradient_finiteGeometricCandidate_eq_zero
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_pos halpha_lt_beta hkappa d
  exact chewi45_not_near_min_of_geometricRatio_tail_lower_bound
    (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
    halpha_pos.le halpha_lt_beta.le (N := N)
    (x := x) (xStar := strongLowerBoundFiniteGeometricCandidate kappa d)
    hx0 hspan hgrad_zero htail_ge hnear heps_lt

/--
Contradiction form of the finite-boundary obstruction.  This is the concrete
finite slack target to use while deciding whether to complete Theorem 4.5 by a
large-dimension comparison or by moving to the true infinite-chain model.
-/
theorem chewi45_not_near_min_of_finiteGeometricCandidate_boundary_lower_bound
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N : ℕ} (hN : N < d)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps)
    (heps_lt :
      eps <
        (alpha / 2) *
          (((chewi45GeometricRatio kappa) ^ (N + 1) *
            (1 - (chewi45GeometricRatio kappa) ^
              (2 * d + 2 - 2 * (N + 1)))) ^ (2 : ℕ))) :
    False := by
  have hgap_ge :=
    chewi45_gap_ge_geometric_boundary_of_finiteGeometricCandidate
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_pos halpha_lt_beta hkappa (N := N) hN
      (x := x) hx0 hspan
  have hgap_le :
      strongLowerBoundChainObjective alpha beta d (x N) -
          strongLowerBoundChainObjective alpha beta d
            (strongLowerBoundFiniteGeometricCandidate kappa d) ≤ eps := by
    linarith
  linarith

/--
Contradiction form of the half-boundary finite slack corollary.
-/
theorem chewi45_not_near_min_of_finiteGeometricCandidate_half_boundary_lower_bound
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N : ℕ} (hN : N < d)
    (hboundary_half :
      (chewi45GeometricRatio kappa) ^
          (2 * d + 2 - 2 * (N + 1)) ≤ (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps)
    (heps_lt :
      eps <
        (alpha / 8) *
          (chewi45GeometricRatio kappa) ^ (2 * (N + 1))) :
    False := by
  have hgap_ge :=
    chewi45_gap_ge_geometric_half_boundary_of_finiteGeometricCandidate
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_pos halpha_lt_beta hkappa (N := N) hN hboundary_half
      (x := x) hx0 hspan
  have hgap_le :
      strongLowerBoundChainObjective alpha beta d (x N) -
          strongLowerBoundChainObjective alpha beta d
            (strongLowerBoundFiniteGeometricCandidate kappa d) ≤ eps := by
    linarith
  linarith

/--
Contradiction form of the half-boundary finite slack corollary, with the
half-bound supplied at any smaller exponent `M`.  This is the final wrapper
needed before proving the logarithmic power estimate.
-/
theorem chewi45_not_near_min_of_finiteGeometricCandidate_half_boundary_lower_bound_of_exponent_le
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N M : ℕ} (hN : N < d)
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_half : (chewi45GeometricRatio kappa) ^ M ≤ (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps)
    (heps_lt :
      eps <
        (alpha / 8) *
          (chewi45GeometricRatio kappa) ^ (2 * (N + 1))) :
    False := by
  have hgap_ge :=
    chewi45_gap_ge_geometric_half_boundary_of_finiteGeometricCandidate_of_exponent_le
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_pos halpha_lt_beta hkappa (N := N) (M := M)
      hN hM_le hM_half (x := x) hx0 hspan
  have hgap_le :
      strongLowerBoundChainObjective alpha beta d (x N) -
          strongLowerBoundChainObjective alpha beta d
            (strongLowerBoundFiniteGeometricCandidate kappa d) ≤ eps := by
    linarith
  linarith

/--
Positive near-minimality form of the finite half-boundary obstruction with a
smaller exponent `M`: any `eps`-near iterate must dominate the geometric
finite-slack lower bound.
-/
theorem chewi45_geometric_half_boundary_lower_bound_le_eps_of_near_min_of_exponent_le
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N M : ℕ} (hN : N < d)
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_half : (chewi45GeometricRatio kappa) ^ M ≤ (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps) :
    (alpha / 8) *
        (chewi45GeometricRatio kappa) ^ (2 * (N + 1)) ≤ eps := by
  have hgap_ge :=
    chewi45_gap_ge_geometric_half_boundary_of_finiteGeometricCandidate_of_exponent_le
      (alpha := alpha) (beta := beta) (kappa := kappa)
      halpha_pos halpha_lt_beta hkappa (N := N) (M := M)
      hN hM_le hM_half (x := x) hx0 hspan
  have hgap_le :
      strongLowerBoundChainObjective alpha beta d (x N) -
          strongLowerBoundChainObjective alpha beta d
            (strongLowerBoundFiniteGeometricCandidate kappa d) ≤ eps := by
    linarith
  exact hgap_ge.trans hgap_le

/--
Logarithmic near-minimality form of the finite half-boundary obstruction.
This is the direct input for the final source-shaped log iteration conversion:
the finite dimension only needs to provide an exponent `M` below the boundary
exponent and a log proof that `q^M <= 1/2`.
-/
theorem chewi45_geometric_half_boundary_lower_bound_le_eps_of_near_min_of_log_exponent_le
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (halpha_lt_beta : alpha < beta) (hkappa : kappa = beta / alpha)
    {d N M : ℕ} (hN : N < d)
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_log :
      (M : ℝ) * Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps) :
    (alpha / 8) *
        (chewi45GeometricRatio kappa) ^ (2 * (N + 1)) ≤ eps := by
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hM_half :
      (chewi45GeometricRatio kappa) ^ M ≤ (1 / 2 : ℝ) :=
    chewi45GeometricRatio_pow_le_half_of_nat_mul_log_le
      (kappa := kappa) hkappa_gt hM_log
  exact
    chewi45_geometric_half_boundary_lower_bound_le_eps_of_near_min_of_exponent_le
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos halpha_lt_beta hkappa (N := N) (M := M)
      hN hM_le hM_half (x := x) hx0 hspan hnear

/--
Source-shaped finite-geometric rate wrapper for Chewi Theorem 4.5.  The
finite construction supplies the half-boundary condition through `M`; the
remaining scalar log comparison then converts the verified geometric
near-minimality lower bound into `rate <= N`.
-/
theorem chewi45_iteration_count_ge_rate_of_finiteGeometricCandidate_log_near_min
    {alpha beta kappa eps rate : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    {d N M : ℕ} (hN : N < d)
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_log :
      (M : ℝ) * Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps)
    (hrate_log :
      Real.log (eps / (alpha / 8)) ≤
        (2 * (rate + 1)) * Real.log (chewi45GeometricRatio kappa)) :
    rate ≤ (N : ℝ) := by
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hgeo :
      (alpha / 8) *
          (chewi45GeometricRatio kappa) ^ (2 * (N + 1)) ≤ eps :=
    chewi45_geometric_half_boundary_lower_bound_le_eps_of_near_min_of_log_exponent_le
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos halpha_lt_beta hkappa (N := N) (M := M)
      hN hM_le hM_log (x := x) hx0 hspan hnear
  exact chewi45_iteration_count_ge_rate_of_geometric_eps_lower_bound
    (alpha := alpha) (eps := eps) (q := chewi45GeometricRatio kappa)
    (rate := rate) (N := N)
    halpha_pos heps_pos
    (chewi45GeometricRatio_pos hkappa_gt)
    (chewi45GeometricRatio_lt_one kappa)
    hgeo hrate_log

/--
Contradiction form of the finite-geometric log-rate wrapper: once the source
dimension and scalar log comparisons are supplied, no `eps`-near gradient-span
iterate can occur before the target rate.
-/
theorem chewi45_not_finiteGeometricCandidate_near_min_of_log_rate_lt
    {alpha beta kappa eps rate : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    {d N M : ℕ} (hN : N < d)
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_log :
      (M : ℝ) * Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ))
    (hN_lt_rate : (N : ℝ) < rate)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps)
    (hrate_log :
      Real.log (eps / (alpha / 8)) ≤
        (2 * (rate + 1)) * Real.log (chewi45GeometricRatio kappa)) :
    False := by
  have hrate_le_N :=
    chewi45_iteration_count_ge_rate_of_finiteGeometricCandidate_log_near_min
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      (rate := rate)
      halpha_pos heps_pos halpha_lt_beta hkappa (N := N) (M := M)
      hN hM_le hM_log (x := x) hx0 hspan hnear hrate_log
  linarith

/--
Canonical log-quotient form of the finite-geometric Theorem 4.5 wrapper.  It
uses the compiled finite obstruction and the scalar quotient identity, so the
only remaining source choices are the finite exponent `M` and its logarithmic
half-boundary proof.
-/
theorem chewi45_iteration_count_ge_logQuotientRate_of_finiteGeometricCandidate_log_near_min
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    {d N M : ℕ} (hN : N < d)
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_log :
      (M : ℝ) * Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps) :
    Real.log (eps / (alpha / 8)) /
          (2 * Real.log (chewi45GeometricRatio kappa)) - 1 ≤
      (N : ℝ) := by
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hgeo :
      (alpha / 8) *
          (chewi45GeometricRatio kappa) ^ (2 * (N + 1)) ≤ eps :=
    chewi45_geometric_half_boundary_lower_bound_le_eps_of_near_min_of_log_exponent_le
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos halpha_lt_beta hkappa (N := N) (M := M)
      hN hM_le hM_log (x := x) hx0 hspan hnear
  exact chewi45_iteration_count_ge_logQuotientRate_of_geometric_eps_lower_bound
    (alpha := alpha) (eps := eps) (q := chewi45GeometricRatio kappa)
    (N := N) halpha_pos heps_pos
    (chewi45GeometricRatio_pos hkappa_gt)
    (chewi45GeometricRatio_lt_one kappa) hgeo

/--
Contradiction form of the canonical log-quotient finite-geometric wrapper.
-/
theorem chewi45_not_finiteGeometricCandidate_near_min_of_logQuotientRate_lt
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    {d N M : ℕ} (hN : N < d)
    (hM_le : M ≤ 2 * d + 2 - 2 * (N + 1))
    (hM_log :
      (M : ℝ) * Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ))
    (hN_lt_rate :
      (N : ℝ) <
        Real.log (eps / (alpha / 8)) /
            (2 * Real.log (chewi45GeometricRatio kappa)) - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin d)}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta d) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta d (x N) ≤
        strongLowerBoundChainObjective alpha beta d
          (strongLowerBoundFiniteGeometricCandidate kappa d) + eps) :
    False := by
  have hrate_le_N :=
    chewi45_iteration_count_ge_logQuotientRate_of_finiteGeometricCandidate_log_near_min
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa (N := N) (M := M)
      hN hM_le hM_log (x := x) hx0 hspan hnear
  linarith

/--
For the standard finite choice `d = 2N + 1`, the available boundary exponent
in the finite geometric correction is exactly `2(N+1)`.
-/
theorem chewi45_two_mul_add_one_boundary_exponent_eq (N : ℕ) :
    2 * (2 * N + 1) + 2 - 2 * (N + 1) = 2 * (N + 1) := by
  omega

/--
Canonical quotient-rate wrapper for the standard source dimension
`d = 2N + 1`.  This discharges the finite side conditions `N < d` and
`M <= 2*d+2-2*(N+1)` by taking `M = 2(N+1)`.
-/
theorem chewi45_iteration_count_ge_logQuotientRate_two_mul_add_one
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha) {N : ℕ}
    (hM_log :
      ((2 * (N + 1) : ℕ) : ℝ) *
          Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    Real.log (eps / (alpha / 8)) /
          (2 * Real.log (chewi45GeometricRatio kappa)) - 1 ≤
      (N : ℝ) := by
  exact
    chewi45_iteration_count_ge_logQuotientRate_of_finiteGeometricCandidate_log_near_min
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa
      (d := 2 * N + 1) (N := N) (M := 2 * (N + 1))
      (by omega) (by omega) hM_log (x := x) hx0 hspan hnear

/--
Contradiction form of the standard `d = 2N + 1` quotient-rate wrapper.
-/
theorem chewi45_not_finiteGeometricCandidate_near_min_of_logQuotientRate_lt_two_mul_add_one
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha) {N : ℕ}
    (hM_log :
      ((2 * (N + 1) : ℕ) : ℝ) *
          Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ))
    (hN_lt_rate :
      (N : ℝ) <
        Real.log (eps / (alpha / 8)) /
            (2 * Real.log (chewi45GeometricRatio kappa)) - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    False := by
  have hrate_le_N :=
    chewi45_iteration_count_ge_logQuotientRate_two_mul_add_one
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa (N := N)
      hM_log (x := x) hx0 hspan hnear
  linarith

/--
Fully source-shaped two-rate contradiction for the standard `d = 2N+1`
finite-geometric route.  The first rate comparison supplies the logarithmic
half-boundary condition; the second says the observed iteration count is below
the canonical `eps` quotient rate.
-/
theorem chewi45_not_finiteGeometricCandidate_near_min_of_two_logQuotient_rates
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha) {N : ℕ}
    (hhalf_rate_le_N :
      Real.log (1 / 2 : ℝ) /
            (2 * Real.log (chewi45GeometricRatio kappa)) - 1 ≤
        (N : ℝ))
    (hN_lt_eps_rate :
      (N : ℝ) <
        Real.log (eps / (alpha / 8)) /
            (2 * Real.log (chewi45GeometricRatio kappa)) - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    False := by
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hM_log :
      ((2 * (N + 1) : ℕ) : ℝ) *
          Real.log (chewi45GeometricRatio kappa) ≤
        Real.log (1 / 2 : ℝ) :=
    chewi45_log_half_bound_of_logQuotient_iteration_lower_bound
      (q := chewi45GeometricRatio kappa) (N := N)
      (chewi45GeometricRatio_pos hkappa_gt)
      (chewi45GeometricRatio_lt_one kappa)
      hhalf_rate_le_N
  exact
    chewi45_not_finiteGeometricCandidate_near_min_of_logQuotientRate_lt_two_mul_add_one
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa (N := N)
      hM_log hN_lt_eps_rate (x := x) hx0 hspan hnear

/--
Condition-number-shaped contradiction for the standard finite direct route.
The two scalar comparisons use Chewi's ratio bounds
`log q <= -2/(sqrt(kappa)+1)` and
`-2/(sqrt(kappa)-1) <= log q`.
-/
theorem chewi45_not_finiteGeometricCandidate_near_min_of_conditionNumber_rates
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    (heps_le : eps ≤ alpha / 8) {N : ℕ}
    (hhalf_condition_le_N :
      -((Real.sqrt kappa + 1) * Real.log (1 / 2 : ℝ)) / 4 - 1 ≤
        (N : ℝ))
    (hN_lt_eps_condition :
      (N : ℝ) <
        -((Real.sqrt kappa - 1) * Real.log (eps / (alpha / 8))) / 4 - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    False := by
  have hkappa_gt : 1 < kappa := by
    rw [hkappa]
    exact (one_lt_div halpha_pos).2 halpha_lt_beta
  have hhalf_nonpos : Real.log (1 / 2 : ℝ) ≤ 0 := by
    exact Real.log_nonpos (by norm_num : 0 ≤ (1 / 2 : ℝ))
      (by norm_num : (1 / 2 : ℝ) ≤ 1)
  have hhalf_rate_le_condition :
      Real.log (1 / 2 : ℝ) /
            (2 * Real.log (chewi45GeometricRatio kappa)) - 1 ≤
        -((Real.sqrt kappa + 1) * Real.log (1 / 2 : ℝ)) / 4 - 1 :=
    chewi45_logQuotientRate_le_sqrt_add_one_bound
      (A := Real.log (1 / 2 : ℝ)) (kappa := kappa)
      hkappa_gt hhalf_nonpos
  have hhalf_rate_le_N :
      Real.log (1 / 2 : ℝ) /
            (2 * Real.log (chewi45GeometricRatio kappa)) - 1 ≤
        (N : ℝ) :=
    hhalf_rate_le_condition.trans hhalf_condition_le_N
  have ha_pos : 0 < alpha / 8 := by positivity
  have heps_ratio_nonneg : 0 ≤ eps / (alpha / 8) := by positivity
  have heps_ratio_le_one : eps / (alpha / 8) ≤ 1 := by
    rw [div_le_iff₀ ha_pos]
    simpa using heps_le
  have heps_log_nonpos :
      Real.log (eps / (alpha / 8)) ≤ 0 :=
    Real.log_nonpos heps_ratio_nonneg heps_ratio_le_one
  have heps_condition_le_rate :
      -((Real.sqrt kappa - 1) *
            Real.log (eps / (alpha / 8))) / 4 - 1 ≤
        Real.log (eps / (alpha / 8)) /
            (2 * Real.log (chewi45GeometricRatio kappa)) - 1 :=
    chewi45_sqrt_sub_one_bound_le_logQuotientRate
      (A := Real.log (eps / (alpha / 8))) (kappa := kappa)
      hkappa_gt heps_log_nonpos
  have hN_lt_eps_rate :
      (N : ℝ) <
        Real.log (eps / (alpha / 8)) /
            (2 * Real.log (chewi45GeometricRatio kappa)) - 1 :=
    hN_lt_eps_condition.trans_le heps_condition_le_rate
  exact
    chewi45_not_finiteGeometricCandidate_near_min_of_two_logQuotient_rates
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa (N := N)
      hhalf_rate_le_N hN_lt_eps_rate (x := x) hx0 hspan hnear

/--
Textbook-shaped constant cleanup of the finite direct route.  Under
`kappa >= 4`, the two condition-number gates can be expressed with pure
`sqrt(kappa)` factors: `3/2 * sqrt(kappa)` for the finite half-boundary gate
and `sqrt(kappa)/2` for the `eps` gate.
-/
theorem chewi45_not_finiteGeometricCandidate_near_min_of_sqrtKappa_rates
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    (hkappa_four : 4 ≤ kappa) (heps_le : eps ≤ alpha / 8) {N : ℕ}
    (hhalf_sqrt_le_N :
      -(((3 / 2 : ℝ) * Real.sqrt kappa) *
            Real.log (1 / 2 : ℝ)) / 4 - 1 ≤
        (N : ℝ))
    (hN_lt_eps_sqrt :
      (N : ℝ) <
        -((Real.sqrt kappa / 2) *
            Real.log (eps / (alpha / 8))) / 4 - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    False := by
  have hhalf_nonpos : Real.log (1 / 2 : ℝ) ≤ 0 := by
    exact Real.log_nonpos (by norm_num : 0 ≤ (1 / 2 : ℝ))
      (by norm_num : (1 / 2 : ℝ) ≤ 1)
  have hhalf_condition_le_sqrt :
      -((Real.sqrt kappa + 1) * Real.log (1 / 2 : ℝ)) / 4 - 1 ≤
        -(((3 / 2 : ℝ) * Real.sqrt kappa) *
            Real.log (1 / 2 : ℝ)) / 4 - 1 :=
    chewi45_sqrt_add_one_rate_le_three_halves_sqrt_rate
      (A := Real.log (1 / 2 : ℝ)) (kappa := kappa)
      hkappa_four hhalf_nonpos
  have hhalf_condition_le_N :
      -((Real.sqrt kappa + 1) * Real.log (1 / 2 : ℝ)) / 4 - 1 ≤
        (N : ℝ) :=
    hhalf_condition_le_sqrt.trans hhalf_sqrt_le_N
  have ha_pos : 0 < alpha / 8 := by positivity
  have heps_ratio_nonneg : 0 ≤ eps / (alpha / 8) := by positivity
  have heps_ratio_le_one : eps / (alpha / 8) ≤ 1 := by
    rw [div_le_iff₀ ha_pos]
    simpa using heps_le
  have heps_log_nonpos :
      Real.log (eps / (alpha / 8)) ≤ 0 :=
    Real.log_nonpos heps_ratio_nonneg heps_ratio_le_one
  have heps_sqrt_le_condition :
      -((Real.sqrt kappa / 2) *
          Real.log (eps / (alpha / 8))) / 4 - 1 ≤
        -((Real.sqrt kappa - 1) *
          Real.log (eps / (alpha / 8))) / 4 - 1 :=
    chewi45_half_sqrt_rate_le_sqrt_sub_one_rate
      (A := Real.log (eps / (alpha / 8))) (kappa := kappa)
      hkappa_four heps_log_nonpos
  have hN_lt_eps_condition :
      (N : ℝ) <
        -((Real.sqrt kappa - 1) *
          Real.log (eps / (alpha / 8))) / 4 - 1 :=
    hN_lt_eps_sqrt.trans_le heps_sqrt_le_condition
  exact
    chewi45_not_finiteGeometricCandidate_near_min_of_conditionNumber_rates
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa heps_le (N := N)
      hhalf_condition_le_N hN_lt_eps_condition
      (x := x) hx0 hspan hnear

/--
Positive-log presentation of the `sqrt(kappa)` finite direct route.  This is
the same obstruction as `chewi45_not_finiteGeometricCandidate_near_min_of_sqrtKappa_rates`,
but with the rates written as `log 2` and `log ((alpha/8)/eps)`, matching the
source theorem's positive logarithm convention.
-/
theorem chewi45_not_finiteGeometricCandidate_near_min_of_sqrtKappa_positiveLog_rates
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    (hkappa_four : 4 ≤ kappa) (heps_le : eps ≤ alpha / 8) {N : ℕ}
    (hhalf_sqrt_le_N :
      (((3 / 2 : ℝ) * Real.sqrt kappa) *
            Real.log (2 : ℝ)) / 4 - 1 ≤
        (N : ℝ))
    (hN_lt_eps_sqrt :
      (N : ℝ) <
        ((Real.sqrt kappa / 2) *
            Real.log ((alpha / 8) / eps)) / 4 - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    False := by
  have hhalf_old :
      -(((3 / 2 : ℝ) * Real.sqrt kappa) *
            Real.log (1 / 2 : ℝ)) / 4 - 1 ≤
        (N : ℝ) := by
    rw [chewi45_log_half_eq_neg_log_two]
    ring_nf at hhalf_sqrt_le_N ⊢
    exact hhalf_sqrt_le_N
  have hlog_eps :
      Real.log (eps / (alpha / 8)) =
        -Real.log ((alpha / 8) / eps) := by
    have hneg :=
      chewi45_neg_log_eps_div_alpha_eighth_eq_log_alpha_eighth_div_eps
        halpha_pos heps_pos
    rw [← hneg, neg_neg]
  have heps_old :
      (N : ℝ) <
        -((Real.sqrt kappa / 2) *
            Real.log (eps / (alpha / 8))) / 4 - 1 := by
    rw [hlog_eps]
    ring_nf at hN_lt_eps_sqrt ⊢
    exact hN_lt_eps_sqrt
  exact
    chewi45_not_finiteGeometricCandidate_near_min_of_sqrtKappa_rates
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa hkappa_four heps_le
      (N := N) hhalf_old heps_old (x := x) hx0 hspan hnear

/--
Scalar nonemptiness comparison for the source-positive-log window in the
direct finite Theorem 4.5 route.  If the accuracy logarithm dominates the
fixed half-boundary logarithm, then the half-boundary gate is no larger than
the accuracy gate.
-/
theorem chewi45_source_positiveLog_half_gate_le_eps_gate
    {alpha eps kappa : ℝ}
    (hlog_large :
      3 * Real.log (2 : ℝ) ≤ Real.log ((alpha / 8) / eps)) :
    (3 * Real.sqrt kappa * Real.log (2 : ℝ)) / 8 - 1 ≤
      (Real.sqrt kappa * Real.log ((alpha / 8) / eps)) / 8 - 1 := by
  have hsqrt_nonneg : 0 ≤ Real.sqrt kappa := Real.sqrt_nonneg kappa
  have hmul :
      Real.sqrt kappa * (3 * Real.log (2 : ℝ)) ≤
        Real.sqrt kappa * Real.log ((alpha / 8) / eps) :=
    mul_le_mul_of_nonneg_left hlog_large hsqrt_nonneg
  nlinarith

/--
Strict version of `chewi45_source_positiveLog_half_gate_le_eps_gate`, useful
when choosing a natural iteration count inside the source-positive-log window.
-/
theorem chewi45_source_positiveLog_half_gate_lt_eps_gate_of_kappa_pos
    {alpha eps kappa : ℝ} (hkappa_pos : 0 < kappa)
    (hlog_large :
      3 * Real.log (2 : ℝ) < Real.log ((alpha / 8) / eps)) :
    (3 * Real.sqrt kappa * Real.log (2 : ℝ)) / 8 - 1 <
      (Real.sqrt kappa * Real.log ((alpha / 8) / eps)) / 8 - 1 := by
  have hsqrt_pos : 0 < Real.sqrt kappa := Real.sqrt_pos.2 hkappa_pos
  have hmul :
      Real.sqrt kappa * (3 * Real.log (2 : ℝ)) <
        Real.sqrt kappa * Real.log ((alpha / 8) / eps) :=
    mul_lt_mul_of_pos_left hlog_large hsqrt_pos
  nlinarith

/--
Strict source-positive-log window comparison in the standard Theorem 4.5
condition-number regime `4 <= kappa`.
-/
theorem chewi45_source_positiveLog_half_gate_lt_eps_gate_of_four_le
    {alpha eps kappa : ℝ} (hkappa_four : 4 ≤ kappa)
    (hlog_large :
      3 * Real.log (2 : ℝ) < Real.log ((alpha / 8) / eps)) :
    (3 * Real.sqrt kappa * Real.log (2 : ℝ)) / 8 - 1 <
      (Real.sqrt kappa * Real.log ((alpha / 8) / eps)) / 8 - 1 := by
  exact chewi45_source_positiveLog_half_gate_lt_eps_gate_of_kappa_pos
    (by nlinarith) hlog_large

/--
Source-constant presentation of the direct finite Theorem 4.5 obstruction.
This is the positive-log wrapper with the scalar coefficients multiplied out:
the lower dimension-adequacy gate is `3 * sqrt(kappa) * log 2 / 8`, while
the target accuracy gate is `sqrt(kappa) * log ((alpha/8)/eps) / 8`.
-/
theorem chewi45_not_finiteGeometricCandidate_near_min_of_source_positiveLog_window
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    (hkappa_four : 4 ≤ kappa) (heps_le : eps ≤ alpha / 8) {N : ℕ}
    (hhalf_sqrt_le_N :
      (3 * Real.sqrt kappa * Real.log (2 : ℝ)) / 8 - 1 ≤
        (N : ℝ))
    (hN_lt_eps_sqrt :
      (N : ℝ) <
        (Real.sqrt kappa * Real.log ((alpha / 8) / eps)) / 8 - 1)
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    False := by
  have hhalf_old :
      (((3 / 2 : ℝ) * Real.sqrt kappa) *
            Real.log (2 : ℝ)) / 4 - 1 ≤
        (N : ℝ) := by
    ring_nf at hhalf_sqrt_le_N ⊢
    exact hhalf_sqrt_le_N
  have heps_old :
      (N : ℝ) <
        ((Real.sqrt kappa / 2) *
            Real.log ((alpha / 8) / eps)) / 4 - 1 := by
    ring_nf at hN_lt_eps_sqrt ⊢
    exact hN_lt_eps_sqrt
  exact
    chewi45_not_finiteGeometricCandidate_near_min_of_sqrtKappa_positiveLog_rates
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa hkappa_four heps_le
      (N := N) hhalf_old heps_old (x := x) hx0 hspan hnear

/--
Lower-bound form of the source-positive-log finite Theorem 4.5 obstruction.
For a near-minimizing gradient-span run satisfying the finite dimension gate,
the source accuracy rate itself must be no larger than the iteration count.
-/
theorem chewi45_source_positiveLog_rate_le_of_finiteGeometricCandidate_near_min
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    (hkappa_four : 4 ≤ kappa) (heps_le : eps ≤ alpha / 8) {N : ℕ}
    (hhalf_sqrt_le_N :
      (3 * Real.sqrt kappa * Real.log (2 : ℝ)) / 8 - 1 ≤
        (N : ℝ))
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    (Real.sqrt kappa * Real.log ((alpha / 8) / eps)) / 8 - 1 ≤
      (N : ℝ) := by
  by_contra hnot
  have hN_lt_eps_sqrt :
      (N : ℝ) <
        (Real.sqrt kappa * Real.log ((alpha / 8) / eps)) / 8 - 1 :=
    not_le.mp hnot
  exact
    chewi45_not_finiteGeometricCandidate_near_min_of_source_positiveLog_window
      (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
      halpha_pos heps_pos halpha_lt_beta hkappa hkappa_four heps_le
      (N := N) hhalf_sqrt_le_N hN_lt_eps_sqrt
      (x := x) hx0 hspan hnear

/--
Burn-in-or-rate form of the source-positive-log finite Theorem 4.5 lower
bound.  A near-minimizing gradient-span run is either still below the finite
dimension-adequacy gate, or else it has already run at least the source
accuracy rate.
-/
theorem chewi45_source_positiveLog_burnin_or_rate_le_of_finiteGeometricCandidate_near_min
    {alpha beta kappa eps : ℝ} (halpha_pos : 0 < alpha)
    (heps_pos : 0 < eps) (halpha_lt_beta : alpha < beta)
    (hkappa : kappa = beta / alpha)
    (hkappa_four : 4 ≤ kappa) (heps_le : eps ≤ alpha / 8) {N : ℕ}
    {x : ℕ -> EuclideanSpace ℝ (Fin (2 * N + 1))}
    (hx0 : x 0 = 0)
    (hspan : IsGradientSpanTrajectory
      (strongLowerBoundChainGradient alpha beta (2 * N + 1)) x)
    (hnear :
      strongLowerBoundChainObjective alpha beta (2 * N + 1) (x N) ≤
        strongLowerBoundChainObjective alpha beta (2 * N + 1)
          (strongLowerBoundFiniteGeometricCandidate kappa (2 * N + 1)) +
            eps) :
    (N : ℝ) <
        (3 * Real.sqrt kappa * Real.log (2 : ℝ)) / 8 - 1 ∨
      (Real.sqrt kappa * Real.log ((alpha / 8) / eps)) / 8 - 1 ≤
        (N : ℝ) := by
  rcases lt_or_ge (N : ℝ)
      ((3 * Real.sqrt kappa * Real.log (2 : ℝ)) / 8 - 1) with
    hburnin | hhalf_sqrt_le_N
  · exact Or.inl hburnin
  · exact Or.inr
      (chewi45_source_positiveLog_rate_le_of_finiteGeometricCandidate_near_min
        (alpha := alpha) (beta := beta) (kappa := kappa) (eps := eps)
        halpha_pos heps_pos halpha_lt_beta hkappa hkappa_four heps_le
        (N := N) hhalf_sqrt_le_N (x := x) hx0 hspan hnear)

end Optimization
end StatInference
