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

example {ι : Type*} (R : ι -> ℝ) (Rn : ℕ -> ι -> ℝ) (fhat : ℕ -> ι) (f : ι)
    (eps delta : ℕ -> ℝ)
    (h_uniform : ∀ n g, |Rn n g - R g| ≤ delta n)
    (h_erm : ∀ n, Rn n (fhat n) ≤ Rn n f + eps n) :
    ∀ n, R (fhat n) - R f ≤ 2 * delta n + eps n :=
  StatInference.oracle_excess_sequence_bound R Rn fhat f eps delta h_uniform h_erm

example (eps delta : ℕ -> ℝ)
    (h_delta : Tendsto delta atTop (𝓝 0))
    (h_eps : Tendsto eps atTop (𝓝 0)) :
    Tendsto (fun n => 2 * delta n + eps n) atTop (𝓝 0) :=
  StatInference.oracle_bound_tendsto_zero eps delta h_delta h_eps

end StatInference.Benchmarks
