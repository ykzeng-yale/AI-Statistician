import StatInference

/-!
# Lean benchmark seed tasks
-/

namespace StatInference.Benchmarks

open StatInference

example {ι : Type*} (R Rn : ι -> ℝ) (fhat f : ι) (eps delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : Rn fhat ≤ Rn f + eps) :
    R fhat ≤ R f + 2 * delta + eps :=
  StatInference.oracle_ineq_of_uniform_deviation R Rn fhat f eps delta h_uniform h_erm

example {ι : Type*} (R Rn : ι -> ℝ) (fhat f : ι) (eps delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : Rn fhat ≤ Rn f + eps) :
    R fhat - R f ≤ 2 * delta + eps :=
  StatInference.excess_risk_bound_of_uniform_deviation R Rn fhat f eps delta h_uniform h_erm

end StatInference.Benchmarks
