import Mathlib

/-!
# Squeeze algebra for WDSM rate transfers

After deterministic WDSM bounds reduce a term to a nonnegative radius bound,
the probability layer must prove that the radius converges to zero.  This file
records the real `Tendsto` squeeze steps that turn those bounds into
negligibility conclusions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

/--
If the absolute value of a real-valued term is bounded by a sequence tending to
zero, then the term tends to zero.
-/
theorem tendsto_zero_of_abs_le_bound
    {Index : Type*} {l : Filter Index}
    (value bound : Index -> Real)
    (hbound : ∀ index, |value index| ≤ bound index)
    (hbound_tendsto : Tendsto bound l (nhds 0)) :
    Tendsto value l (nhds 0) := by
  rw [tendsto_zero_iff_abs_tendsto_zero]
  exact squeeze_zero
    (fun index => abs_nonneg (value index))
    hbound hbound_tendsto

/--
Eventual version of `tendsto_zero_of_abs_le_bound`, useful when deterministic
bounds hold only eventually.
-/
theorem tendsto_zero_of_eventually_abs_le_bound
    {Index : Type*} {l : Filter Index}
    (value bound : Index -> Real)
    (hbound : ∀ᶠ index in l, |value index| ≤ bound index)
    (hbound_tendsto : Tendsto bound l (nhds 0)) :
    Tendsto value l (nhds 0) := by
  rw [tendsto_zero_iff_abs_tendsto_zero]
  exact squeeze_zero'
    (Eventually.of_forall (fun index => abs_nonneg (value index)))
    hbound hbound_tendsto

end WDSM
end Matching
end StatInference
