import Mathlib

/-!
# Exact-zero limit algebra for WDSM remainders

Some WDSM finite-identification steps give exact equality at every sample
index.  This module packages the corresponding asymptotic consequence: an
exactly zero finite error is negligible, and remains negligible after
multiplication by an arbitrary deterministic scale.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

/-- A real sequence that is pointwise zero tends to zero. -/
theorem tendsto_zero_of_eq_zero
    {Index : Type*} {l : Filter Index}
    (value : Index -> Real)
    (hzero : ∀ index, value index = 0) :
    Tendsto value l (nhds 0) := by
  have hvalue : value = fun _index => (0 : Real) := by
    funext index
    exact hzero index
  rw [hvalue]
  exact tendsto_const_nhds

/-- If the absolute value of a real sequence is pointwise zero, the sequence tends to zero. -/
theorem tendsto_zero_of_abs_eq_zero
    {Index : Type*} {l : Filter Index}
    (value : Index -> Real)
    (hzero : ∀ index, |value index| = 0) :
    Tendsto value l (nhds 0) := by
  exact tendsto_zero_of_eq_zero value
    (fun index => abs_eq_zero.mp (hzero index))

/--
An exactly zero real sequence remains negligible after multiplication by any
deterministic scale.
-/
theorem tendsto_scaled_zero_of_eq_zero
    {Index : Type*} {l : Filter Index}
    (scale value : Index -> Real)
    (hzero : ∀ index, value index = 0) :
    Tendsto (fun index => scale index * value index) l (nhds 0) := by
  exact tendsto_zero_of_eq_zero
    (fun index => scale index * value index)
    (fun index => by
      change scale index * value index = 0
      rw [hzero index, mul_zero])

/--
An absolute-error-zero real sequence remains negligible after multiplication by
any deterministic scale.
-/
theorem tendsto_scaled_zero_of_abs_eq_zero
    {Index : Type*} {l : Filter Index}
    (scale value : Index -> Real)
    (hzero : ∀ index, |value index| = 0) :
    Tendsto (fun index => scale index * value index) l (nhds 0) := by
  exact tendsto_scaled_zero_of_eq_zero scale value
    (fun index => abs_eq_zero.mp (hzero index))

/-- Pointwise equality gives a negligible difference. -/
theorem tendsto_sub_zero_of_pointwise_eq
    {Index : Type*} {l : Filter Index}
    (first second : Index -> Real)
    (heq : ∀ index, first index = second index) :
    Tendsto (fun index => first index - second index) l (nhds 0) := by
  exact tendsto_zero_of_eq_zero
    (fun index => first index - second index)
    (fun index => by
      change first index - second index = 0
      rw [heq index, sub_self])

/-- Pointwise equality gives a scaled negligible difference. -/
theorem tendsto_scaled_sub_zero_of_pointwise_eq
    {Index : Type*} {l : Filter Index}
    (scale first second : Index -> Real)
    (heq : ∀ index, first index = second index) :
    Tendsto (fun index => scale index * (first index - second index)) l
      (nhds 0) := by
  exact tendsto_scaled_zero_of_eq_zero scale
    (fun index => first index - second index)
    (fun index => by
      change first index - second index = 0
      rw [heq index, sub_self])

end WDSM
end Matching
end StatInference
