import StatInference.Matching.WDSM.QuadraticVariation

/-!
# Own-plus-reuse variance algebra for WDSM PATE residuals

For PATE, a matched-arm residual carries its own observed-outcome survey
coefficient plus the exact reuse coefficient.  This file proves the finite
quadratic-variation expansion that precedes the Chen-Han/Palm-process moment
limits in the appendix.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Finite cross variation between own and reuse coefficients. -/
noncomputable def crossVariation (sample : Finset Unit)
    (ownCoefficient reuseCoefficient variance : Unit -> Real) : Real :=
  ∑ unit ∈ sample,
    ownCoefficient unit * reuseCoefficient unit * variance unit

/--
Exact own-plus-reuse quadratic-variation expansion:
`(C + K)^2 sigma^2 = C^2 sigma^2 + 2 C K sigma^2 + K^2 sigma^2`, summed over
the finite matched arm.
-/
theorem quadraticVariation_own_plus_reuse_eq
    (sample : Finset Unit)
    (ownCoefficient reuseCoefficient variance : Unit -> Real) :
    quadraticVariation sample
        (fun unit => ownCoefficient unit + reuseCoefficient unit) variance =
      quadraticVariation sample ownCoefficient variance +
        2 * crossVariation sample ownCoefficient reuseCoefficient variance +
        quadraticVariation sample reuseCoefficient variance := by
  unfold quadraticVariation crossVariation
  calc
    (∑ unit ∈ sample,
        (ownCoefficient unit + reuseCoefficient unit) ^ 2 * variance unit) =
        ∑ unit ∈ sample,
          (ownCoefficient unit ^ 2 * variance unit +
            2 * (ownCoefficient unit * reuseCoefficient unit * variance unit) +
            reuseCoefficient unit ^ 2 * variance unit) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by ring)
    _ =
        (∑ unit ∈ sample, ownCoefficient unit ^ 2 * variance unit) +
          (∑ unit ∈ sample,
            2 * (ownCoefficient unit * reuseCoefficient unit * variance unit)) +
          (∑ unit ∈ sample, reuseCoefficient unit ^ 2 * variance unit) := by
          rw [Finset.sum_add_distrib, Finset.sum_add_distrib]
    _ =
        (∑ unit ∈ sample, ownCoefficient unit ^ 2 * variance unit) +
          2 *
            (∑ unit ∈ sample,
              ownCoefficient unit * reuseCoefficient unit * variance unit) +
          (∑ unit ∈ sample, reuseCoefficient unit ^ 2 * variance unit) := by
          rw [← Finset.mul_sum]

end WDSM
end Matching
end StatInference
