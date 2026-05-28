import StatInference.Matching.WDSM.ScoreSpaceMean

/-!
# Lipschitz matching-bias bounds for WDSM

The WDSM bias-rate argument uses two ingredients: outcome regressions are
Lipschitz on the matched score space, and nearest-neighbor matches have small
score radius.  This module proves the deterministic step from those two
ingredients to a finite matching-discrepancy bound.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit : Type*}

/--
If the regression mean is `lipschitzConstant`-Lipschitz in the score distance
and all donors in the matched set lie within `radius` of the focal unit, then
the absolute finite mean discrepancy is bounded by
`lipschitzConstant * radius`.
-/
theorem abs_meanDiscrepancy_le_lipschitz_radius
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (mean : Unit -> Real) (scoreDistance : Unit -> Unit -> Real)
    (focal : Unit) (lipschitzConstant radius : Real)
    (hcoeff_nonneg :
      ∀ donor, donor ∈ donorSet -> 0 ≤ coefficient focal donor)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1)
    (hlipschitz :
      ∀ donor, donor ∈ donorSet ->
        |mean focal - mean donor| ≤
          lipschitzConstant * scoreDistance focal donor)
    (hradius :
      ∀ donor, donor ∈ donorSet -> scoreDistance focal donor ≤ radius)
    (hlipschitz_nonneg : 0 ≤ lipschitzConstant) :
    |meanDiscrepancy donorSet coefficient mean focal| ≤
      lipschitzConstant * radius := by
  exact abs_meanDiscrepancy_le_radius donorSet coefficient mean focal
    (lipschitzConstant * radius) hcoeff_nonneg hsum
    (fun donor hdonor =>
      le_trans (hlipschitz donor hdonor)
        (mul_le_mul_of_nonneg_left (hradius donor hdonor)
          hlipschitz_nonneg))

end WDSM
end Matching
end StatInference
