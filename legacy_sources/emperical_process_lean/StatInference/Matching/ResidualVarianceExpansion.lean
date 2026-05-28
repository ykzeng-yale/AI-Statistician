import StatInference.Matching.WDSM.OwnPlusReuseVariance
import StatInference.Matching.WDSM.ResidualVarianceAlgebra

/-!
# Own-plus-reuse residual covariance expansion

This module combines the diagonal covariance reduction with the existing
own-plus-reuse quadratic-variation expansion.  It is the finite algebraic
variance identity used before imposing probability limits on reuse counts and
conditional variances.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit : Type*} [DecidableEq Unit]

/--
With zero off-diagonal residual covariances, the covariance form for an
own-plus-reuse coefficient expands into the own variance, the cross term, and
the reuse variance.
-/
theorem linearCovarianceVariation_diagonal_own_plus_reuse_eq
    (sample : Finset Unit)
    (ownCoefficient reuseCoefficient variance : Unit -> Real) :
    linearCovarianceVariation sample
        (fun unit => ownCoefficient unit + reuseCoefficient unit)
        (fun left right => if left = right then variance left else 0) =
      quadraticVariation sample ownCoefficient variance +
        2 * crossVariation sample ownCoefficient reuseCoefficient variance +
        quadraticVariation sample reuseCoefficient variance := by
  rw [linearCovarianceVariation_diagonal_eq_quadraticVariation]
  exact quadraticVariation_own_plus_reuse_eq
    sample ownCoefficient reuseCoefficient variance

end WDSM
end Matching
end StatInference
