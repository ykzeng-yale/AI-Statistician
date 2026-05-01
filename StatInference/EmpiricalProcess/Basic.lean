import StatInference.Asymptotics.Basic

/-!
# Empirical process seed interfaces
-/

namespace StatInference

structure EmpiricalProcessSpec (Index Observation Value : Type*) where
  process : Index -> Observation -> Value
  measurability_statement : Prop
  complexity_statement : Prop

structure GlivenkoCantelliSpec where
  uniform_law_statement : Prop

structure DonskerSpec where
  weak_convergence_statement : Prop

end StatInference

