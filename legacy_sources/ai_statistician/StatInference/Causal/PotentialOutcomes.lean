import StatInference.Estimator.AsymptoticLinear

/-!
# Causal inference seed interfaces
-/

namespace StatInference

structure PotentialOutcomeModel (Unit Outcome Covariate : Type*) where
  y0 : Unit -> Outcome
  y1 : Unit -> Outcome
  x : Unit -> Covariate

structure OverlapAssumption where
  statement : Prop

structure UnconfoundednessAssumption where
  statement : Prop

structure ATEIdentificationBridge where
  overlap : OverlapAssumption
  unconfoundedness : UnconfoundednessAssumption
  identification : Prop
  prove_identification :
    overlap.statement -> unconfoundedness.statement -> identification

theorem ate_identification_of_bridge (b : ATEIdentificationBridge)
    (hoverlap : b.overlap.statement)
    (hunconf : b.unconfoundedness.statement) :
    b.identification :=
  b.prove_identification hoverlap hunconf

end StatInference

