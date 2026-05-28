import StatInference.Optimization.Theorem131Gradient

/-!
# Chewi Theorem 13.1, Double-Exponential Local Newton Rate

This module turns the local quadratic recurrence in Chewi Theorem 13.1 into
the source-facing double-exponential error decay.  The corrected quantitative
display keeps the scale factor `alpha / gamma` that is forced by the
dimensionless recurrence for `(gamma / alpha) * ||x_n - x_star||`.
-/

namespace StatInference
namespace Optimization

section Scalar

/--
If the scaled Newton error obeys `v_{n+1} <= v_n^2`, then
`v_N <= v_0^(2^N)`.
-/
theorem chewi131_scaled_error_le_initial_pow_two_pow
    {u : ℕ -> ℝ} {c : ℝ}
    (hc_nonneg : 0 ≤ c)
    (hu_nonneg : ∀ k, 0 ≤ u k)
    (hrec : ∀ k, c * u (k + 1) ≤ (c * u k) ^ (2 : ℕ)) :
    ∀ k, c * u k ≤ (c * u 0) ^ ((2 : ℕ) ^ k) := by
  intro k
  induction k with
  | zero =>
      simp
  | succ k ih =>
      have hleft_nonneg : 0 ≤ c * u k :=
        mul_nonneg hc_nonneg (hu_nonneg k)
      have hbase_nonneg : 0 ≤ c * u 0 :=
        mul_nonneg hc_nonneg (hu_nonneg 0)
      have hright_nonneg : 0 ≤ (c * u 0) ^ ((2 : ℕ) ^ k) :=
        pow_nonneg hbase_nonneg _
      have hsquare :
          (c * u k) ^ (2 : ℕ) ≤
            ((c * u 0) ^ ((2 : ℕ) ^ k)) ^ (2 : ℕ) :=
        (sq_le_sq₀ hleft_nonneg hright_nonneg).2 ih
      have hpow :
          ((c * u 0) ^ ((2 : ℕ) ^ k)) ^ (2 : ℕ) =
            (c * u 0) ^ ((2 : ℕ) ^ (k + 1)) := by
        rw [← pow_mul, Nat.pow_succ]
      calc
        c * u (k + 1) ≤ (c * u k) ^ (2 : ℕ) := hrec k
        _ ≤ ((c * u 0) ^ ((2 : ℕ) ^ k)) ^ (2 : ℕ) := hsquare
        _ = (c * u 0) ^ ((2 : ℕ) ^ (k + 1)) := hpow

/--
Exact scaled form of Chewi Theorem 13.1's post-recurrence rate algebra.
The scale factor `alpha / gamma` is necessary when translating back from the
dimensionless error `(gamma / alpha) * u_n`.
-/
theorem chewi131_error_le_alpha_div_gamma_mul_initial_scaled_pow_two_pow
    {u : ℕ -> ℝ} {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hu_nonneg : ∀ k, 0 ≤ u k)
    (hrec : ∀ k,
      u (k + 1) ≤ (gamma / alpha) * u k ^ (2 : ℕ)) :
    ∀ k, u k ≤
      (alpha / gamma) *
        ((gamma / alpha) * u 0) ^ ((2 : ℕ) ^ k) := by
  let c : ℝ := gamma / alpha
  have hc_pos : 0 < c := div_pos hgamma halpha
  have hc_nonneg : 0 ≤ c := le_of_lt hc_pos
  have hscaled_rec : ∀ k, c * u (k + 1) ≤ (c * u k) ^ (2 : ℕ) := by
    intro k
    have hmul :=
      mul_le_mul_of_nonneg_left (hrec k) hc_nonneg
    have hshape :
        c * ((gamma / alpha) * u k ^ (2 : ℕ)) =
          (c * u k) ^ (2 : ℕ) := by
      simp [c, pow_two]
      ring
    simpa [hshape] using hmul
  have hscaled :=
    chewi131_scaled_error_le_initial_pow_two_pow hc_nonneg hu_nonneg
      hscaled_rec
  intro k
  have hscale_nonneg : 0 ≤ alpha / gamma := div_nonneg halpha.le hgamma.le
  have hmul :=
    mul_le_mul_of_nonneg_left (hscaled k) hscale_nonneg
  have hleft : (alpha / gamma) * (c * u k) = u k := by
    simp [c]
    field_simp [halpha.ne', hgamma.ne']
  simpa [hleft, c, mul_assoc] using hmul

/--
If the scaled Newton error obeys `v_{n+1} <= v_n^2` and starts below `1/2`,
then `v_N <= (1/2)^(2^N)`.
-/
theorem chewi131_scaled_error_le_half_pow_two_pow
    {u : ℕ -> ℝ} {c : ℝ}
    (hc_nonneg : 0 ≤ c)
    (hu_nonneg : ∀ k, 0 ≤ u k)
    (hrec : ∀ k, c * u (k + 1) ≤ (c * u k) ^ (2 : ℕ))
    (hinit : c * u 0 ≤ (1 / 2 : ℝ)) :
    ∀ k, c * u k ≤ (1 / 2 : ℝ) ^ ((2 : ℕ) ^ k) := by
  intro k
  induction k with
  | zero =>
      simpa using hinit
  | succ k ih =>
      have hleft_nonneg : 0 ≤ c * u k :=
        mul_nonneg hc_nonneg (hu_nonneg k)
      have hright_nonneg :
          0 ≤ (1 / 2 : ℝ) ^ ((2 : ℕ) ^ k) :=
        pow_nonneg (by norm_num : (0 : ℝ) ≤ 1 / 2) _
      have hsquare :
          (c * u k) ^ (2 : ℕ) ≤
            ((1 / 2 : ℝ) ^ ((2 : ℕ) ^ k)) ^ (2 : ℕ) :=
        (sq_le_sq₀ hleft_nonneg hright_nonneg).2 ih
      have hpow :
          ((1 / 2 : ℝ) ^ ((2 : ℕ) ^ k)) ^ (2 : ℕ) =
            (1 / 2 : ℝ) ^ ((2 : ℕ) ^ (k + 1)) := by
        rw [← pow_mul, Nat.pow_succ]
      calc
        c * u (k + 1) ≤ (c * u k) ^ (2 : ℕ) := hrec k
        _ ≤ ((1 / 2 : ℝ) ^ ((2 : ℕ) ^ k)) ^ (2 : ℕ) := hsquare
        _ = (1 / 2 : ℝ) ^ ((2 : ℕ) ^ (k + 1)) := hpow

/--
Chewi Theorem 13.1 scalar rate algebra.  From the local quadratic recurrence
`u_{n+1} <= (gamma / alpha) * u_n^2` and the local-radius hypothesis, the
unscaled error satisfies the corrected source display
`u_N <= (alpha / gamma) * (1/2)^(2^N)`.
-/
theorem chewi131_error_le_alpha_div_gamma_mul_half_pow_two_pow
    {u : ℕ -> ℝ} {alpha gamma : ℝ}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hu_nonneg : ∀ k, 0 ≤ u k)
    (hrec : ∀ k,
      u (k + 1) ≤ (gamma / alpha) * u k ^ (2 : ℕ))
    (hinit : u 0 ≤ alpha / (2 * gamma)) :
    ∀ k, u k ≤
      (alpha / gamma) * (1 / 2 : ℝ) ^ ((2 : ℕ) ^ k) := by
  let c : ℝ := gamma / alpha
  have hc_pos : 0 < c := div_pos hgamma halpha
  have hc_nonneg : 0 ≤ c := le_of_lt hc_pos
  have hscaled_rec : ∀ k, c * u (k + 1) ≤ (c * u k) ^ (2 : ℕ) := by
    intro k
    have hmul :=
      mul_le_mul_of_nonneg_left (hrec k) hc_nonneg
    have hshape :
        c * ((gamma / alpha) * u k ^ (2 : ℕ)) =
          (c * u k) ^ (2 : ℕ) := by
      simp [c, pow_two]
      ring
    simpa [hshape] using hmul
  have hscaled_init : c * u 0 ≤ (1 / 2 : ℝ) := by
    have hmul :=
      mul_le_mul_of_nonneg_left hinit hc_nonneg
    have hshape : c * (alpha / (2 * gamma)) = (1 / 2 : ℝ) := by
      simp [c]
      field_simp [halpha.ne', hgamma.ne']
    simpa [hshape] using hmul
  have hscaled :=
    chewi131_scaled_error_le_half_pow_two_pow hc_nonneg hu_nonneg
      hscaled_rec hscaled_init
  intro k
  have hscale_nonneg : 0 ≤ alpha / gamma := div_nonneg halpha.le hgamma.le
  have hmul :=
    mul_le_mul_of_nonneg_left (hscaled k) hscale_nonneg
  have hleft : (alpha / gamma) * (c * u k) = u k := by
    simp [c]
    field_simp [halpha.ne', hgamma.ne']
  simpa [hleft, mul_assoc] using hmul

/--
Stopping-certificate form of the corrected Chewi Theorem 13.1 rate.
-/
theorem chewi131_error_le_eps_of_alpha_div_gamma_mul_half_pow_two_pow_le
    {u : ℕ -> ℝ} {alpha gamma eps : ℝ} {N : ℕ}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hu_nonneg : ∀ k, 0 ≤ u k)
    (hrec : ∀ k,
      u (k + 1) ≤ (gamma / alpha) * u k ^ (2 : ℕ))
    (hinit : u 0 ≤ alpha / (2 * gamma))
    (hbudget :
      (alpha / gamma) * (1 / 2 : ℝ) ^ ((2 : ℕ) ^ N) ≤ eps) :
    u N ≤ eps :=
  (chewi131_error_le_alpha_div_gamma_mul_half_pow_two_pow
    halpha hgamma hu_nonneg hrec hinit N).trans hbudget

end Scalar

section Normed

variable {E : Type*} [NormedAddCommGroup E]

/--
Exact normed form of Chewi Theorem 13.1's double-exponential rate, before the
local-radius simplification `((gamma / alpha) * ||x_0-x_*||) <= 1/2`.
-/
theorem chewi131_local_quadratic_error_rate_exact_of_recurrence
    {alpha gamma : ℝ}
    {x : ℕ -> E} {xStar : E}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hrec : ∀ k,
      ‖x (k + 1) - xStar‖ ≤
        (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ)) :
    ∀ N, ‖x N - xStar‖ ≤
      (alpha / gamma) *
        ((gamma / alpha) * ‖x 0 - xStar‖) ^ ((2 : ℕ) ^ N) := by
  exact
    chewi131_error_le_alpha_div_gamma_mul_initial_scaled_pow_two_pow
      (u := fun k => ‖x k - xStar‖) halpha hgamma
      (fun k => norm_nonneg (x k - xStar)) hrec

/--
Chewi Theorem 13.1 double-exponential local Newton error rate for any normed
sequence satisfying the already-formalized local quadratic recurrence.
-/
theorem chewi131_local_quadratic_error_rate_of_recurrence
    {alpha gamma : ℝ}
    {x : ℕ -> E} {xStar : E}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hrec : ∀ k,
      ‖x (k + 1) - xStar‖ ≤
        (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ))
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ N, ‖x N - xStar‖ ≤
      (alpha / gamma) * (1 / 2 : ℝ) ^ ((2 : ℕ) ^ N) := by
  exact
    chewi131_error_le_alpha_div_gamma_mul_half_pow_two_pow
      (u := fun k => ‖x k - xStar‖) halpha hgamma
      (fun k => norm_nonneg (x k - xStar)) hrec hinit

/--
Chewi Theorem 13.1 rate wrapper consuming the already-formalized display
`(13.1)` as a paired quadratic/half-contraction recurrence.
-/
theorem chewi131_local_quadratic_error_rate_of_recurrence_pair
    {alpha gamma : ℝ}
    {x : ℕ -> E} {xStar : E}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hrec : ∀ k,
      ‖x (k + 1) - xStar‖ ≤
          (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ) ∧
        ‖x (k + 1) - xStar‖ ≤ (1 / 2) * ‖x k - xStar‖)
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma)) :
    ∀ N, ‖x N - xStar‖ ≤
      (alpha / gamma) * (1 / 2 : ℝ) ^ ((2 : ℕ) ^ N) :=
  chewi131_local_quadratic_error_rate_of_recurrence
    halpha hgamma (fun k => (hrec k).1) hinit

/--
Stopping-certificate form for the normed Chewi Theorem 13.1 rate.
-/
theorem chewi131_local_quadratic_error_le_eps_of_rate_budget
    {alpha gamma eps : ℝ} {N : ℕ}
    {x : ℕ -> E} {xStar : E}
    (halpha : 0 < alpha) (hgamma : 0 < gamma)
    (hrec : ∀ k,
      ‖x (k + 1) - xStar‖ ≤
        (gamma / alpha) * ‖x k - xStar‖ ^ (2 : ℕ))
    (hinit : ‖x 0 - xStar‖ ≤ alpha / (2 * gamma))
    (hbudget :
      (alpha / gamma) * (1 / 2 : ℝ) ^ ((2 : ℕ) ^ N) ≤ eps) :
    ‖x N - xStar‖ ≤ eps :=
  (chewi131_local_quadratic_error_rate_of_recurrence
    (E := E) halpha hgamma hrec hinit N).trans hbudget

end Normed

end Optimization
end StatInference
