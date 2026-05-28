import Mathlib

/-!
# Hájek limit algebra for WDSM

Many WDSM probability arguments reduce to deterministic continuous-mapping
steps for ratios: a numerator converges, a denominator converges to a nonzero
limit, and therefore the Hájek ratio converges to the corresponding ratio.
This file proves those `Tendsto` algebra steps directly.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

/-- A ratio converges to the ratio of limits when the denominator limit is nonzero. -/
theorem tendsto_ratio_of_tendsto
    {Index : Type*} {l : Filter Index}
    (numerator denominator : Index -> Real) (numeratorLimit denominatorLimit : Real)
    (hnumerator : Tendsto numerator l (nhds numeratorLimit))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index => numerator index / denominator index) l
      (nhds (numeratorLimit / denominatorLimit)) := by
  exact hnumerator.div hdenominator hdenominatorLimit

/-- If the numerator tends to zero and the denominator has a nonzero limit, the ratio tends to zero. -/
theorem tendsto_ratio_zero_of_tendsto_numerator_zero
    {Index : Type*} {l : Filter Index}
    (numerator denominator : Index -> Real) (denominatorLimit : Real)
    (hnumerator : Tendsto numerator l (nhds 0))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index => numerator index / denominator index) l (nhds 0) := by
  simpa using
    tendsto_ratio_of_tendsto numerator denominator 0 denominatorLimit
      hnumerator hdenominator hdenominatorLimit

/--
Centered Hájek-ratio limit: if the numerator tends to `target * denominatorLimit`
and the denominator tends to `denominatorLimit ≠ 0`, then the ratio minus the
target tends to zero.
-/
theorem tendsto_ratio_sub_target_zero
    {Index : Type*} {l : Filter Index}
    (numerator denominator : Index -> Real) (target denominatorLimit : Real)
    (hnumerator : Tendsto numerator l (nhds (target * denominatorLimit)))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index => numerator index / denominator index - target) l
      (nhds 0) := by
  have hratio :
      Tendsto (fun index => numerator index / denominator index) l
        (nhds ((target * denominatorLimit) / denominatorLimit)) :=
    tendsto_ratio_of_tendsto numerator denominator
      (target * denominatorLimit) denominatorLimit
      hnumerator hdenominator hdenominatorLimit
  have hlimit : (target * denominatorLimit) / denominatorLimit - target = 0 := by
    field_simp [hdenominatorLimit]
    ring
  have htarget : Tendsto (fun _index : Index => target) l (nhds target) :=
    tendsto_const_nhds
  simpa [hlimit] using hratio.sub htarget

end WDSM
end Matching
end StatInference
