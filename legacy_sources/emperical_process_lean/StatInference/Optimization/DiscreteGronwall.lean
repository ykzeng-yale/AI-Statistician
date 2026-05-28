import StatInference.Optimization.Basic

/-!
# Discrete Gronwall lemmas

This module starts the Chapter 3 recurrence layer for Chewi's optimization
notes.  Mathlib provides product/Ico discrete Gronwall inequalities in
`Mathlib.Analysis.ODE.DiscreteGronwall`; the main theorem here records the
Chewi Chapter 3 power/range display specialization needed by the gradient
descent route.
-/

namespace StatInference
namespace Optimization

open Finset

/--
Chewi Lemma 3.5, discrete Gronwall, in a finite-sum form with natural powers.

If `u_{n+1} <= A * u_n + B_n` up to time `N - 1` and `A` is nonnegative, then
the `N`-th term is bounded by the unrolled recurrence

`A^N u_0 + sum_{n=0}^{N-1} A^(N-1-n) B_n`.

The textbook assumes `A > 0` and proves this by multiplying by inverse powers
and telescoping; this formulation avoids inverse powers and is the same bound.
-/
theorem discreteGronwall_sum_le {A : ℝ} (hA : 0 ≤ A)
    (u B : ℕ -> ℝ) :
    ∀ N : ℕ,
      (∀ n, n < N -> u (n + 1) ≤ A * u n + B n) ->
        u N ≤ A ^ N * u 0 +
          ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n
  | 0, _ => by
      simp
  | N + 1, hrec => by
      have hrecN : u (N + 1) ≤ A * u N + B N :=
        hrec N (Nat.lt_succ_self N)
      have ih :
          u N ≤ A ^ N * u 0 +
            ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n :=
        discreteGronwall_sum_le hA u B N
          (fun n hn => hrec n (Nat.lt_trans hn (Nat.lt_succ_self N)))
      have hmul :
          A * (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n) =
            ∑ n ∈ Finset.range N, A ^ (N - n) * B n := by
        rw [Finset.mul_sum]
        refine Finset.sum_congr rfl ?_
        intro n hn
        have hnlt : n < N := Finset.mem_range.mp hn
        have hpow : N - n = (N - 1 - n) + 1 := by
          omega
        rw [hpow, pow_succ]
        ring
      have hstep :
          A * u N + B N ≤
            A * (A ^ N * u 0 +
              ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n) + B N := by
        have hmul_le := mul_le_mul_of_nonneg_left ih hA
        nlinarith
      have htarget :
          A * (A ^ N * u 0 +
              ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n) + B N =
            A ^ (N + 1) * u 0 +
              ∑ n ∈ Finset.range (N + 1),
                A ^ ((N + 1) - 1 - n) * B n := by
        rw [mul_add, hmul, Finset.sum_range_succ]
        have hpow0 : A * (A ^ N * u 0) = A ^ (N + 1) * u 0 := by
          rw [pow_succ]
          ring
        have hsum :
            (∑ n ∈ Finset.range N, A ^ (N - n) * B n) =
              ∑ n ∈ Finset.range N,
                A ^ ((N + 1) - 1 - n) * B n := by
          refine Finset.sum_congr rfl ?_
          intro n hn
          have hsub : (N + 1) - 1 - n = N - n := by
            omega
          rw [hsub]
        have hlast : A ^ ((N + 1) - 1 - N) * B N = B N := by
          have hsub : (N + 1) - 1 - N = 0 := by
            omega
          rw [hsub]
          simp
        rw [hpow0, hsum, hlast]
        ring
      exact hrecN.trans (hstep.trans_eq htarget)

/--
Strict-positive version matching the source hypothesis of Chewi Lemma 3.5.
-/
theorem discreteGronwall_sum_le_of_pos {A : ℝ} (hA : 0 < A)
    (u B : ℕ -> ℝ) (N : ℕ)
    (hrec : ∀ n, n < N -> u (n + 1) ≤ A * u n + B n) :
    u N ≤ A ^ N * u 0 +
      ∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n :=
  discreteGronwall_sum_le hA.le u B N hrec

/--
Chewi Lemma 3.5 in the source's one-based display:

`u_N <= A^N u_0 + sum_{n=1}^N A^(N-n) B_{n-1}`.

This is a reindexing wrapper around `discreteGronwall_sum_le`.
-/
theorem discreteGronwall_one_based_sum_le {A : ℝ} (hA : 0 ≤ A)
    (u B : ℕ -> ℝ) (N : ℕ)
    (hrec : ∀ n, n < N -> u (n + 1) ≤ A * u n + B n) :
    u N ≤ A ^ N * u 0 +
      ∑ n ∈ Finset.Ico 1 (N + 1), A ^ (N - n) * B (n - 1) := by
  have hmain := discreteGronwall_sum_le hA u B N hrec
  have hsum :
      (∑ n ∈ Finset.range N, A ^ (N - 1 - n) * B n) =
        ∑ n ∈ Finset.Ico 1 (N + 1), A ^ (N - n) * B (n - 1) := by
    rw [Finset.sum_Ico_eq_sum_range]
    refine Finset.sum_congr ?_ ?_
    · simp
    · intro n hn
      have hsub : N - (1 + n) = N - 1 - n := by
        omega
      rw [hsub]
      simp
  simpa [hsum] using hmain

/--
Strict-positive version matching the stated hypothesis of Chewi Lemma 3.5 and
the source's one-based display.
-/
theorem discreteGronwall_one_based_sum_le_of_pos {A : ℝ} (hA : 0 < A)
    (u B : ℕ -> ℝ) (N : ℕ)
    (hrec : ∀ n, n < N -> u (n + 1) ≤ A * u n + B n) :
    u N ≤ A ^ N * u 0 +
      ∑ n ∈ Finset.Ico 1 (N + 1), A ^ (N - n) * B (n - 1) :=
  discreteGronwall_one_based_sum_le hA.le u B N hrec

end Optimization
end StatInference
