import StatInference.Asymptotics.Basic

/-!
# `op` and `Op` roadmap interfaces

The first implementation layer keeps these as explicit records of intended
mathlib-backed statements. The library should later replace each proposition
field with concrete definitions built from `TendstoInMeasure`, tightness, and
normed-space convergence.
-/

namespace StatInference

/-- Prototype record for a small-o-in-probability statement. -/
structure SmallOInProbabilitySpec where
  statement : Prop

/-- Prototype record for a bounded-in-probability statement. -/
structure BoundedInProbabilitySpec where
  statement : Prop

/-- A reusable algebraic interface for a future `op(1) * Op(1) = op(1)` theorem. -/
structure OpAlgebraSpec where
  small : SmallOInProbabilitySpec
  bounded : BoundedInProbabilitySpec
  product_small : Prop
  product_rule : small.statement -> bounded.statement -> product_small

theorem op_mul_Op_rule (s : OpAlgebraSpec)
    (hs : s.small.statement) (hb : s.bounded.statement) :
    s.product_small :=
  s.product_rule hs hb

end StatInference

