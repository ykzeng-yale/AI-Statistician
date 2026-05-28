import StatInference.Matching.WDSM.NegligibleAlgebra

/-!
# Bias-centering limit algebra for WDSM

The WDSM asymptotic statements often prove a limit for a bias-centered statistic
and then conclude that the uncentered or bias-corrected statistic has the same
limit when the scaled bias term is negligible.  This file proves the real
`Tendsto` algebra behind that transfer.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

/--
Exact scaled-error identity: raw scaled error equals scaled bias-centered error
plus scaled bias.
-/
theorem scaled_error_eq_bias_centered_add_scaled_bias
    {Index : Type*} (scale estimator bias : Index -> Real) (target : Real)
    (index : Index) :
    scale index * (estimator index - target) =
      scale index * (estimator index - target - bias index) +
        scale index * bias index := by
  ring

/--
If the scaled bias-centered statistic has a limit and the scaled bias is
negligible, then the raw scaled statistic has the same limit.
-/
theorem tendsto_scaled_error_of_bias_centered_limit
    {Index : Type*} {l : Filter Index}
    (scale estimator bias : Index -> Real) (target limit : Real)
    (hcentered :
      Tendsto (fun index =>
        scale index * (estimator index - target - bias index)) l (nhds limit))
    (hbias :
      Tendsto (fun index => scale index * bias index) l (nhds 0)) :
    Tendsto (fun index => scale index * (estimator index - target)) l
      (nhds limit) := by
  have hsum := tendsto_add_negligible
    (fun index => scale index * (estimator index - target - bias index))
    (fun index => scale index * bias index)
    limit hcentered hbias
  convert hsum using 1
  ext index
  exact scaled_error_eq_bias_centered_add_scaled_bias
    scale estimator bias target index

/--
If a bias-corrected estimator is exactly `estimator - bias`, then its scaled
centered error is the scaled bias-centered error of the uncorrected estimator.
-/
theorem scaled_bias_corrected_error_eq_bias_centered
    {Index : Type*} (scale estimator bias biasCorrected : Index -> Real)
    (target : Real)
    (hcorrected : ∀ index, biasCorrected index = estimator index - bias index)
    (index : Index) :
    scale index * (biasCorrected index - target) =
      scale index * (estimator index - target - bias index) := by
  rw [hcorrected index]
  ring

end WDSM
end Matching
end StatInference
