import StatInference.EmpiricalProcess.Complexity
import StatInference.Estimator.Normality

/-!
# Donsker-to-CLT handoff routes

This module connects the empirical-process Donsker interface to the estimator
CLT interfaces used downstream for asymptotic normality.  It does not assert a
primitive Donsker theorem.  A concrete development must still provide the
weak-convergence certificate and the map from that weak convergence statement
to the estimator's CLT statement.
-/

namespace StatInference

universe u v w x y

/--
Proof-carrying handoff from a Donsker bridge certificate to the CLT statement
needed by an indexed asymptotic-linear estimator route.
-/
structure DonskerAsymptoticNormalityRoute {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ)
    (Sample : ℕ -> Type u) (Parameter : Type v)
    (InfluenceFunction : Type w) (LinearPart : Type x) (Remainder : Type y) where
  donsker_bridge : DonskerBridgeCertificate indexClass populationRisk empiricalRisk
  estimator_route :
    IndexedAsymptoticLinearCLTRoute Sample Parameter InfluenceFunction
      LinearPart Remainder
  weak_convergence_to_estimator_clt :
    donsker_bridge.donsker.weak_convergence_statement ->
      estimator_route.clt.statement

namespace DonskerAsymptoticNormalityRoute

/-- Extract the GC component that is carried alongside the Donsker certificate. -/
def toGlivenkoCantelliClass {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    {Sample : ℕ -> Type u} {Parameter : Type v}
    {InfluenceFunction : Type w} {LinearPart : Type x} {Remainder : Type y}
    (route :
      DonskerAsymptoticNormalityRoute indexClass populationRisk empiricalRisk
        Sample Parameter InfluenceFunction LinearPart Remainder) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk :=
  route.donsker_bridge.toGlivenkoCantelliClass

/-- Convert the certified Donsker weak convergence into the estimator CLT input. -/
theorem estimatorCLT {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    {Sample : ℕ -> Type u} {Parameter : Type v}
    {InfluenceFunction : Type w} {LinearPart : Type x} {Remainder : Type y}
    (route :
      DonskerAsymptoticNormalityRoute indexClass populationRisk empiricalRisk
        Sample Parameter InfluenceFunction LinearPart Remainder) :
    route.estimator_route.clt.statement :=
  route.weak_convergence_to_estimator_clt
    (DonskerBridgeCertificate.weakConvergence route.donsker_bridge)

/--
Apply the Donsker-to-CLT handoff and the estimator normality route in one step.
-/
theorem asymptoticNormal {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    {Sample : ℕ -> Type u} {Parameter : Type v}
    {InfluenceFunction : Type w} {LinearPart : Type x} {Remainder : Type y}
    (route :
      DonskerAsymptoticNormalityRoute indexClass populationRisk empiricalRisk
        Sample Parameter InfluenceFunction LinearPart Remainder)
    (h_match : route.estimator_route.estimator.estimator_matches_expansion)
    (h_expansion :
      route.estimator_route.estimator.expansion.expansion_statement)
    (h_remainder :
      route.estimator_route.estimator.remainder_negligible.statement) :
    route.estimator_route.asymptotic_normality :=
  route.estimator_route.asymptoticNormal
    h_match h_expansion h_remainder route.estimatorCLT

/-- Expose the estimator side of the Donsker route as the generic CLT bridge. -/
def toAsymptoticLinearCLTBridge {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    {Sample : ℕ -> Type u} {Parameter : Type v}
    {InfluenceFunction : Type w} {LinearPart : Type x} {Remainder : Type y}
    (route :
      DonskerAsymptoticNormalityRoute indexClass populationRisk empiricalRisk
        Sample Parameter InfluenceFunction LinearPart Remainder) :
    AsymptoticLinearCLTBridge :=
  route.estimator_route.toAsymptoticLinearCLTBridge

end DonskerAsymptoticNormalityRoute

/-- Concrete one-point Donsker bridge witness for interface non-vacuity. -/
def trivialDonskerBridgeCertificate :
    DonskerBridgeCertificate (Set.univ : Set Unit)
      (fun _ : Unit => (0 : ℝ)) (fun _ (_ : Unit) => (0 : ℝ)) where
  gc := {
    radius := fun _ => 0
    uniform_deviation := by
      intro _sampleSize _index _hindex
      simp
    radius_tendsto_zero := by
      simp
  }
  donsker := { weak_convergence_statement := True }
  asymptotic_equipartition_statement := True
  weak_limit_identification_statement := True
  weak_convergence_proof := True.intro

/--
A concrete indexed estimator route whose propositions are all `True`.  This is
only a non-vacuity witness for the route API, not a statistical theorem.
-/
def trivialDonskerIndexedCLTRoute :
    IndexedAsymptoticLinearCLTRoute
      (fun _ : ℕ => Unit) Unit Unit Unit Unit where
  estimator := {
    estimator := { estimate := fun _ _ => Unit.unit }
    target := Unit.unit
    influence_function := Unit.unit
    expansion := {
      statistic := fun _ _ => Unit.unit
      linear_part := fun _ _ => Unit.unit
      remainder := fun _ _ => Unit.unit
      expansion_statement := True
    }
    estimator_matches_expansion := True
    remainder_negligible := { statement := True }
    asymptotic_linear_statement := True
    certify_asymptotic_linear := by
      intro _hmatch _hexpansion _hremainder
      trivial
  }
  clt := { statement := True }
  asymptotic_normality := True
  normality_bridge := by
    intro _hal _hclt _hremainder
    trivial

/-- Concrete Donsker-to-asymptotic-normality route witness. -/
def trivialDonskerAsymptoticNormalityRoute :
    DonskerAsymptoticNormalityRoute (Set.univ : Set Unit)
      (fun _ : Unit => (0 : ℝ)) (fun _ (_ : Unit) => (0 : ℝ))
      (fun _ : ℕ => Unit) Unit Unit Unit Unit where
  donsker_bridge := trivialDonskerBridgeCertificate
  estimator_route := trivialDonskerIndexedCLTRoute
  weak_convergence_to_estimator_clt := by
    intro _hweak
    trivial

/-- Concrete non-vacuity witness for the Donsker-to-normality handoff. -/
theorem trivialDonskerAsymptoticNormality :
    (trivialDonskerAsymptoticNormalityRoute :
      DonskerAsymptoticNormalityRoute (Set.univ : Set Unit)
        (fun _ : Unit => (0 : ℝ)) (fun _ (_ : Unit) => (0 : ℝ))
        (fun _ : ℕ => Unit) Unit Unit Unit Unit).estimator_route.asymptotic_normality :=
  by
    change True
    trivial

end StatInference
