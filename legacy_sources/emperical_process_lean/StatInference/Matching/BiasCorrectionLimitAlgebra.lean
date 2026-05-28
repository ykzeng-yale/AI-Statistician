import StatInference.Matching.WDSM.SlutskyAlgebra

/-!
# Bias-corrected limit algebra for WDSM

The WDSM appendix uses the step
`sqrt n (B_n - \hat B_n) ->p 0` to transfer a centered known-score limit to
the corresponding bias-corrected estimator.  This module records that step as
a real-valued Slutsky theorem.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

omit [MeasurableSpace Sample] in
/--
Exact pointwise identity behind bias-corrected Slutsky transfer.

The scaled bias-corrected error equals the scaled true-bias-centered error
plus the scaled error from estimating the bias term.
-/
theorem scaled_bias_corrected_error_eq_centered_add_bias_error
    (scale : Index -> Real)
    (estimator trueBias estimatedBias : Index -> Sample -> Real)
    (target : Real) (index : Index) (sample : Sample) :
    scale index *
        (estimator index sample - estimatedBias index sample - target) =
      scale index * (estimator index sample - target - trueBias index sample) +
        scale index * (trueBias index sample - estimatedBias index sample) := by
  ring

/--
If the true-bias-centered scaled statistic has a distributional limit and the
scaled bias-estimation error is negligible in probability, then the
bias-corrected scaled statistic has the same distributional limit.
-/
theorem tendstoInDistribution_bias_corrected_of_centered_limit
    (scale : Index -> Real)
    (estimator trueBias estimatedBias : Index -> Sample -> Real)
    (target : Real) (limit : LimitSample -> Real)
    (hcentered :
      TendstoInDistribution
        (fun index sample =>
          scale index * (estimator index sample - target -
            trueBias index sample))
        l limit (fun _index => sampleLaw) limitLaw)
    (hbias_error :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scale index * (trueBias index sample - estimatedBias index sample))
        l (fun _sample => (0 : Real)))
    (hbias_error_meas :
      ∀ index, AEMeasurable
        (fun sample =>
          scale index * (trueBias index sample - estimatedBias index sample))
        sampleLaw) :
    TendstoInDistribution
      (fun index sample =>
        scale index *
          (estimator index sample - estimatedBias index sample - target))
      l limit (fun _index => sampleLaw) limitLaw := by
  have h :=
    tendstoInDistribution_add_negligible_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun index sample =>
        scale index * (estimator index sample - target -
          trueBias index sample))
      (fun index sample =>
        scale index * (trueBias index sample - estimatedBias index sample))
      limit hcentered hbias_error hbias_error_meas
  have hpoint :
      (fun index sample =>
        scale index *
          (estimator index sample - estimatedBias index sample - target)) =
      (fun index sample =>
        scale index * (estimator index sample - target -
          trueBias index sample) +
          scale index *
            (trueBias index sample - estimatedBias index sample)) := by
    funext index sample
    exact scaled_bias_corrected_error_eq_centered_add_bias_error
      scale estimator trueBias estimatedBias target index sample
  simpa [hpoint] using h

/--
Almost-everywhere wrapper for an actual statistic that has already been
rewritten into the scaled bias-corrected form.
-/
theorem tendstoInDistribution_of_ae_eq_bias_corrected_centered_limit
    (statistic : Index -> Sample -> Real)
    (scale : Index -> Real)
    (estimator trueBias estimatedBias : Index -> Sample -> Real)
    (target : Real) (limit : LimitSample -> Real)
    (hstatistic :
      ∀ index,
        statistic index =ᵐ[sampleLaw]
          (fun sample =>
            scale index *
              (estimator index sample - estimatedBias index sample - target)))
    (hcentered :
      TendstoInDistribution
        (fun index sample =>
          scale index * (estimator index sample - target -
            trueBias index sample))
        l limit (fun _index => sampleLaw) limitLaw)
    (hbias_error :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scale index * (trueBias index sample - estimatedBias index sample))
        l (fun _sample => (0 : Real)))
    (hbias_error_meas :
      ∀ index, AEMeasurable
        (fun sample =>
          scale index * (trueBias index sample - estimatedBias index sample))
        sampleLaw) :
    TendstoInDistribution statistic l limit
      (fun _index => sampleLaw) limitLaw := by
  have hcorrected :=
    tendstoInDistribution_bias_corrected_of_centered_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      scale estimator trueBias estimatedBias target limit
      hcentered hbias_error hbias_error_meas
  exact TendstoInDistribution.congr
    (fun index => (hstatistic index).symm)
    (ae_eq_refl limit) hcorrected

end WDSM
end Matching
end StatInference
