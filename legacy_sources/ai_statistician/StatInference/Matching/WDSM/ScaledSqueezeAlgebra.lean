import StatInference.Matching.WDSM.SqueezeAlgebra

/-!
# Scaled squeeze algebra for WDSM rates

WDSM asymptotic bias arguments often multiply a deterministic discrepancy bound
by a nonnegative scale such as `sqrt n`.  This module proves the real
`Tendsto` squeeze step for those scaled bounds.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

/--
If `|value| ≤ bound`, the scale is nonnegative, and the scaled bound tends to
zero, then the scaled value tends to zero.
-/
theorem tendsto_scaled_zero_of_abs_le_bound
    {Index : Type*} {l : Filter Index}
    (scale value bound : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hbound : ∀ index, |value index| ≤ bound index)
    (hscaled_bound_tendsto :
      Tendsto (fun index => scale index * bound index) l (nhds 0)) :
    Tendsto (fun index => scale index * value index) l (nhds 0) := by
  exact tendsto_zero_of_abs_le_bound
    (fun index => scale index * value index)
    (fun index => scale index * bound index)
    (fun index => by
      rw [abs_mul, abs_of_nonneg (hscale_nonneg index)]
      exact mul_le_mul_of_nonneg_left (hbound index) (hscale_nonneg index))
    hscaled_bound_tendsto

/-- Eventual version of `tendsto_scaled_zero_of_abs_le_bound`. -/
theorem tendsto_scaled_zero_of_eventually_abs_le_bound
    {Index : Type*} {l : Filter Index}
    (scale value bound : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hbound : ∀ᶠ index in l, |value index| ≤ bound index)
    (hscaled_bound_tendsto :
      Tendsto (fun index => scale index * bound index) l (nhds 0)) :
    Tendsto (fun index => scale index * value index) l (nhds 0) := by
  exact tendsto_zero_of_eventually_abs_le_bound
    (fun index => scale index * value index)
    (fun index => scale index * bound index)
    ((hscale_nonneg.and hbound).mono
      (fun index hboth => by
        rcases hboth with ⟨hscale, hvalue⟩
        rw [abs_mul, abs_of_nonneg hscale]
        exact mul_le_mul_of_nonneg_left hvalue hscale))
    hscaled_bound_tendsto

end WDSM
end Matching
end StatInference
