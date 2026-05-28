import StatInference.Causal.PotentialOutcomes

/-!
# ATE identification sanity examples

This module adds concrete, inhabited causal objects for the abstract ATE
identification interface.  The examples are intentionally finite and
deterministic: their role is to keep the causal API non-vacuous while later
modules add measure-theoretic identification theorems.
-/

namespace StatInference

/-- A one-unit deterministic potential-outcome case with real outcomes. -/
structure DeterministicATECase where
  y0 : ℝ
  y1 : ℝ

namespace DeterministicATECase

/-- Potential-outcome model for a one-unit deterministic ATE example. -/
def potentialModel (case : DeterministicATECase) :
    PotentialOutcomeModel Unit ℝ Unit where
  y0 := fun _ => case.y0
  y1 := fun _ => case.y1
  x := fun _ => ()

/-- Deterministic ATE value for the one-unit case. -/
def ateValue (case : DeterministicATECase) : ℝ :=
  case.y1 - case.y0

/-- ATE estimand with an explicit definitional statement. -/
def ateEstimand (case : DeterministicATECase) :
    PotentialOutcomeEstimand (PotentialOutcomeModel Unit ℝ Unit) ℝ where
  model := case.potentialModel
  value := case.ateValue
  definition_statement := case.ateValue = case.y1 - case.y0

/-- The deterministic ATE estimand is definitionally the treated-minus-control contrast. -/
theorem ateEstimand_definition (case : DeterministicATECase) :
    case.ateEstimand.definition_statement := by
  rfl

/--
Observed-data model for the one-unit case.  The unit is treated, so the
observed outcome is the treated potential outcome.
-/
def observedModel (case : DeterministicATECase) :
    ObservedPotentialOutcomeModel Unit ℝ Unit where
  potential := case.potentialModel
  treatment := fun _ => true
  observedOutcome := fun _ => case.y1
  consistency :=
    (fun _ : Unit => case.y1) () =
      case.potentialModel.y1 ()

/-- The observed-data consistency statement holds for the deterministic sanity case. -/
theorem observedModel_consistency (case : DeterministicATECase) :
    case.observedModel.consistency := by
  rfl

/-- Consistency assumption instantiated by the deterministic observed-data model. -/
def consistencyAssumption (case : DeterministicATECase) :
    ConsistencyAssumption where
  statement := case.observedModel.consistency

/-- The deterministic one-unit model has a proof-carrying consistency certificate. -/
def verifiedConsistency (case : DeterministicATECase) :
    VerifiedConsistency where
  assumption := case.consistencyAssumption
  proof := case.observedModel_consistency

/--
Overlap is trivially inhabited in this deterministic sanity example.  This is
not a probability theorem; it is a non-vacuity witness for the bridge API.
-/
def overlapAssumption (_case : DeterministicATECase) :
    OverlapAssumption where
  statement := True

/-- Verified overlap certificate for the deterministic sanity example. -/
def verifiedOverlap (case : DeterministicATECase) :
    VerifiedOverlap where
  assumption := case.overlapAssumption
  proof := trivial

/--
Unconfoundedness is trivially inhabited in this deterministic sanity example.
Measure-theoretic exchangeability theorems belong in later modules.
-/
def unconfoundednessAssumption (_case : DeterministicATECase) :
    UnconfoundednessAssumption where
  statement := True

/-- Verified unconfoundedness certificate for the deterministic sanity example. -/
def verifiedUnconfoundedness (case : DeterministicATECase) :
    VerifiedUnconfoundedness where
  assumption := case.unconfoundednessAssumption
  proof := trivial

/-- Observed ATE identification bridge instantiated by the deterministic sanity case. -/
def observedATEBridge (case : DeterministicATECase) :
    ObservedATEIdentificationBridge where
  consistency := case.consistencyAssumption
  overlap := case.overlapAssumption
  unconfoundedness := case.unconfoundednessAssumption
  identification := case.ateEstimand.definition_statement
  bridge := fun _hconsistency _hoverlap _hunconf =>
    case.ateEstimand_definition

/-- The deterministic sanity case proves its observed ATE identification statement. -/
theorem observedATE_identified (case : DeterministicATECase) :
    case.observedATEBridge.identification :=
  observed_ate_identification_of_verified_bridge
    case.observedATEBridge
    case.verifiedConsistency
    case.verifiedOverlap
    case.verifiedUnconfoundedness
    rfl
    rfl
    rfl

end DeterministicATECase

/--
Concrete witness that the observed ATE identification interface is inhabited by
nonempty data, verified assumptions, and a verified identification conclusion.
-/
structure ATEIdentificationSanityExample where
  case : DeterministicATECase
  unit_witness : Unit
  model : ObservedPotentialOutcomeModel Unit ℝ Unit
  estimand : PotentialOutcomeEstimand (PotentialOutcomeModel Unit ℝ Unit) ℝ
  bridge : ObservedATEIdentificationBridge
  consistency : VerifiedConsistency
  overlap : VerifiedOverlap
  unconfoundedness : VerifiedUnconfoundedness
  identification_verified : VerifiedByLean bridge.identification

namespace ATEIdentificationSanityExample

/-- Build a non-vacuous deterministic ATE sanity witness from any two outcomes. -/
def ofOutcomes (y0 y1 : ℝ) : ATEIdentificationSanityExample where
  case := { y0 := y0, y1 := y1 }
  unit_witness := ()
  model := ({ y0 := y0, y1 := y1 } : DeterministicATECase).observedModel
  estimand := ({ y0 := y0, y1 := y1 } : DeterministicATECase).ateEstimand
  bridge := ({ y0 := y0, y1 := y1 } : DeterministicATECase).observedATEBridge
  consistency := ({ y0 := y0, y1 := y1 } : DeterministicATECase).verifiedConsistency
  overlap := ({ y0 := y0, y1 := y1 } : DeterministicATECase).verifiedOverlap
  unconfoundedness :=
    ({ y0 := y0, y1 := y1 } : DeterministicATECase).verifiedUnconfoundedness
  identification_verified :=
    ({ y0 := y0, y1 := y1 } : DeterministicATECase).observedATE_identified

/-- The sanity witness exposes a checked ATE identification conclusion. -/
theorem identified (witness : ATEIdentificationSanityExample) :
    witness.bridge.identification :=
  witness.identification_verified

end ATEIdentificationSanityExample

end StatInference
