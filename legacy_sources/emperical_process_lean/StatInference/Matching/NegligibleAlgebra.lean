import Mathlib

/-!
# Negligible-remainder algebra for WDSM asymptotics

The WDSM proofs repeatedly use Slutsky-style steps where an `o_p(1)` remainder
is added to, subtracted from, or compared with a main term.  This module proves
the corresponding deterministic `Tendsto` algebra for real-valued sequences.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

/-- Adding a negligible real remainder preserves the limit. -/
theorem tendsto_add_negligible
    {Index : Type*} {l : Filter Index}
    (main remainder : Index -> Real) (limit : Real)
    (hmain : Tendsto main l (nhds limit))
    (hremainder : Tendsto remainder l (nhds 0)) :
    Tendsto (fun index => main index + remainder index) l (nhds limit) := by
  simpa using hmain.add hremainder

/-- Subtracting a negligible real remainder preserves the limit. -/
theorem tendsto_sub_negligible
    {Index : Type*} {l : Filter Index}
    (main remainder : Index -> Real) (limit : Real)
    (hmain : Tendsto main l (nhds limit))
    (hremainder : Tendsto remainder l (nhds 0)) :
    Tendsto (fun index => main index - remainder index) l (nhds limit) := by
  simpa using hmain.sub hremainder

/-- A negligible correction added to a negligible term is negligible. -/
theorem tendsto_add_zero_of_two_negligible
    {Index : Type*} {l : Filter Index}
    (first second : Index -> Real)
    (hfirst : Tendsto first l (nhds 0))
    (hsecond : Tendsto second l (nhds 0)) :
    Tendsto (fun index => first index + second index) l (nhds 0) := by
  simpa using hfirst.add hsecond

/-- Two real-valued sequences with the same limit have negligible difference. -/
theorem tendsto_sub_zero_of_same_limit
    {Index : Type*} {l : Filter Index}
    (first second : Index -> Real) (limit : Real)
    (hfirst : Tendsto first l (nhds limit))
    (hsecond : Tendsto second l (nhds limit)) :
    Tendsto (fun index => first index - second index) l (nhds 0) := by
  have hdiff := hfirst.sub hsecond
  simpa using hdiff

end WDSM
end Matching
end StatInference
