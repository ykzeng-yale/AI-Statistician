import StatInference.Matching.WDSM.QuadraticVariation

/-!
# Residual variance algebra for WDSM finite arrays

The residual CLT layer uses conditional mean-zero residuals whose cross
covariances vanish after conditioning on the matching structure.  This module
proves the finite algebra that a diagonal covariance kernel reduces the
variance of a linear combination to the quadratic variation.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*} [DecidableEq Unit]

/-- Finite covariance form for a linear residual combination. -/
noncomputable def linearCovarianceVariation (sample : Finset Unit)
    (coefficient : Unit -> Real) (covariance : Unit -> Unit -> Real) : Real :=
  ∑ left ∈ sample, ∑ right ∈ sample,
    coefficient left * coefficient right * covariance left right

/--
When the covariance kernel is diagonal, the linear covariance form equals the
quadratic variation.
-/
theorem linearCovarianceVariation_diagonal_eq_quadraticVariation
    (sample : Finset Unit) (coefficient variance : Unit -> Real) :
    linearCovarianceVariation sample coefficient
        (fun left right => if left = right then variance left else 0) =
      quadraticVariation sample coefficient variance := by
  unfold linearCovarianceVariation quadraticVariation
  exact Finset.sum_congr rfl
    (fun left hleft => by
      have hinner :
          (∑ right ∈ sample,
            coefficient left * coefficient right *
              (if left = right then variance left else 0)) =
            coefficient left ^ 2 * variance left := by
        let summand : Unit -> Real := fun right =>
          coefficient left * coefficient right *
            (if left = right then variance left else 0)
        have hsingle :
            (∑ right ∈ sample, summand right) = summand left := by
          apply Finset.sum_eq_single left
          · intro right _hright hright_ne
            have hleft_ne : left ≠ right := by
              exact fun h => hright_ne h.symm
            simp [summand, hleft_ne]
          · intro hleft_not_mem
            exact False.elim (hleft_not_mem hleft)
        calc
          (∑ right ∈ sample,
            coefficient left * coefficient right *
              (if left = right then variance left else 0)) =
              summand left := by
              simpa [summand] using hsingle
          _ = coefficient left ^ 2 * variance left := by
              dsimp [summand]
              rw [if_pos rfl]
              ring
      exact hinner)

end WDSM
end Matching
end StatInference
