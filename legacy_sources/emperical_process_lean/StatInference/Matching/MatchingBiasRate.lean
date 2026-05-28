import StatInference.Matching.WDSM.AggregateLipschitzBiasBound
import StatInference.Matching.WDSM.ScaledSqueezeAlgebra

/-!
# Matching-bias rate transfer for WDSM

This module composes the deterministic aggregate Lipschitz bound with the
scaled squeeze lemma.  It is the real-valued skeleton of the WDSM step:
nearest-neighbor score radii small enough at the chosen scale imply negligible
scaled matching discrepancy.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit : Type*}

/--
If each finite WDSM aggregate discrepancy is bounded by
`lipschitzConstant * uniformRadius index` and the scaled version of that bound
tends to zero, then the scaled aggregate discrepancy tends to zero.
-/
theorem tendsto_scaled_aggregate_meanDiscrepancy_zero_of_uniform_radius
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (donorSet : Index -> Unit -> Finset Unit)
    (coefficient : Index -> Unit -> Unit -> Real)
    (focalWeight mean : Index -> Unit -> Real)
    (scoreDistance : Index -> Unit -> Unit -> Real)
    (scale uniformRadius : Index -> Real)
    (lipschitzConstant : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hden_pos :
      ∀ index, 0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ index, ∀ focal, focal ∈ sample index ->
        0 ≤ focalWeight index focal)
    (hcoeff_nonneg :
      ∀ index, ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          0 ≤ coefficient index focal donor)
    (hsum :
      ∀ index, ∀ focal, focal ∈ sample index ->
        (∑ donor ∈ donorSet index focal,
          coefficient index focal donor) = 1)
    (hlipschitz :
      ∀ index, ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          |mean index focal - mean index donor| ≤
            lipschitzConstant * scoreDistance index focal donor)
    (hradius :
      ∀ index, ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          scoreDistance index focal donor ≤ uniformRadius index)
    (hlipschitz_nonneg : 0 ≤ lipschitzConstant)
    (hscaled_radius_tendsto :
      Tendsto (fun index => scale index *
        (lipschitzConstant * uniformRadius index)) l (nhds 0)) :
    Tendsto
      (fun index => scale index *
        (weightedSum (sample index) (focalWeight index)
          (fun focal =>
            meanDiscrepancy (donorSet index focal) (coefficient index)
              (mean index) focal) /
          weightedDenominator (sample index) (focalWeight index))) l
      (nhds 0) := by
  exact tendsto_scaled_zero_of_abs_le_bound
    scale
    (fun index =>
      weightedSum (sample index) (focalWeight index)
        (fun focal =>
          meanDiscrepancy (donorSet index focal) (coefficient index)
            (mean index) focal) /
        weightedDenominator (sample index) (focalWeight index))
    (fun index => lipschitzConstant * uniformRadius index)
    hscale_nonneg
    (fun index =>
      abs_aggregate_meanDiscrepancy_le_lipschitz_uniform_radius
        (sample index) (donorSet index) (coefficient index)
        (focalWeight index) (mean index) (scoreDistance index)
        lipschitzConstant (uniformRadius index)
        (fun _focal => uniformRadius index)
        (hden_pos index)
        (hfocalWeight_nonneg index)
        (hcoeff_nonneg index)
        (hsum index)
        (hlipschitz index)
        (fun focal hfocal donor hdonor =>
          hradius index focal hfocal donor hdonor)
        (fun _focal _hfocal => le_rfl)
        hlipschitz_nonneg)
    hscaled_radius_tendsto

/--
Average-radius version of the WDSM matching-bias rate transfer.  This is the
deterministic bridge needed when the nearest-neighbor geometry yields a
survey-weighted average radius rate rather than a uniform radius rate.
-/
theorem tendsto_scaled_aggregate_meanDiscrepancy_zero_of_radius_average
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (donorSet : Index -> Unit -> Finset Unit)
    (coefficient : Index -> Unit -> Unit -> Real)
    (focalWeight mean : Index -> Unit -> Real)
    (scoreDistance : Index -> Unit -> Unit -> Real)
    (scale : Index -> Real) (radius : Index -> Unit -> Real)
    (lipschitzConstant : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hden_pos :
      ∀ index, 0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ index, ∀ focal, focal ∈ sample index ->
        0 ≤ focalWeight index focal)
    (hcoeff_nonneg :
      ∀ index, ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          0 ≤ coefficient index focal donor)
    (hsum :
      ∀ index, ∀ focal, focal ∈ sample index ->
        (∑ donor ∈ donorSet index focal,
          coefficient index focal donor) = 1)
    (hlipschitz :
      ∀ index, ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          |mean index focal - mean index donor| ≤
            lipschitzConstant * scoreDistance index focal donor)
    (hradius :
      ∀ index, ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          scoreDistance index focal donor ≤ radius index focal)
    (hlipschitz_nonneg : 0 ≤ lipschitzConstant)
    (hscaled_radius_average_tendsto :
      Tendsto (fun index => scale index *
        (weightedSum (sample index) (focalWeight index)
          (fun focal => lipschitzConstant * radius index focal) /
        weightedDenominator (sample index) (focalWeight index))) l
        (nhds 0)) :
    Tendsto
      (fun index => scale index *
        (weightedSum (sample index) (focalWeight index)
          (fun focal =>
            meanDiscrepancy (donorSet index focal) (coefficient index)
              (mean index) focal) /
          weightedDenominator (sample index) (focalWeight index))) l
      (nhds 0) := by
  exact tendsto_scaled_zero_of_abs_le_bound
    scale
    (fun index =>
      weightedSum (sample index) (focalWeight index)
        (fun focal =>
          meanDiscrepancy (donorSet index focal) (coefficient index)
            (mean index) focal) /
        weightedDenominator (sample index) (focalWeight index))
    (fun index =>
      weightedSum (sample index) (focalWeight index)
        (fun focal => lipschitzConstant * radius index focal) /
      weightedDenominator (sample index) (focalWeight index))
    hscale_nonneg
    (fun index =>
      abs_aggregate_meanDiscrepancy_le_lipschitz_radius_average
        (sample index) (donorSet index) (coefficient index)
        (focalWeight index) (mean index) (scoreDistance index)
        lipschitzConstant (radius index)
        (hden_pos index)
        (hfocalWeight_nonneg index)
        (hcoeff_nonneg index)
        (hsum index)
        (hlipschitz index)
        (hradius index)
        hlipschitz_nonneg)
    hscaled_radius_average_tendsto

/--
Eventual-hypothesis version of
`tendsto_scaled_aggregate_meanDiscrepancy_zero_of_radius_average`.  This is
the form used by asymptotic nearest-neighbor arguments when denominator
positivity, coefficient normalization, and radius bounds are only asserted for
all sufficiently large sample sizes.
-/
theorem tendsto_scaled_aggregate_meanDiscrepancy_zero_of_eventually_radius_average
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (donorSet : Index -> Unit -> Finset Unit)
    (coefficient : Index -> Unit -> Unit -> Real)
    (focalWeight mean : Index -> Unit -> Real)
    (scoreDistance : Index -> Unit -> Unit -> Real)
    (scale : Index -> Real) (radius : Index -> Unit -> Real)
    (lipschitzConstant : Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hcoeff_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∀ donor, donor ∈ donorSet index focal ->
            0 ≤ coefficient index focal donor)
    (hsum :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          (∑ donor ∈ donorSet index focal,
            coefficient index focal donor) = 1)
    (hlipschitz :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∀ donor, donor ∈ donorSet index focal ->
            |mean index focal - mean index donor| ≤
              lipschitzConstant * scoreDistance index focal donor)
    (hradius :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∀ donor, donor ∈ donorSet index focal ->
            scoreDistance index focal donor ≤ radius index focal)
    (hlipschitz_nonneg : 0 ≤ lipschitzConstant)
    (hscaled_radius_average_tendsto :
      Tendsto (fun index => scale index *
        (weightedSum (sample index) (focalWeight index)
          (fun focal => lipschitzConstant * radius index focal) /
        weightedDenominator (sample index) (focalWeight index))) l
        (nhds 0)) :
    Tendsto
      (fun index => scale index *
        (weightedSum (sample index) (focalWeight index)
          (fun focal =>
            meanDiscrepancy (donorSet index focal) (coefficient index)
              (mean index) focal) /
          weightedDenominator (sample index) (focalWeight index))) l
      (nhds 0) := by
  have hbound :
      ∀ᶠ index in l,
        |weightedSum (sample index) (focalWeight index)
            (fun focal =>
              meanDiscrepancy (donorSet index focal) (coefficient index)
                (mean index) focal) /
          weightedDenominator (sample index) (focalWeight index)| ≤
          weightedSum (sample index) (focalWeight index)
            (fun focal => lipschitzConstant * radius index focal) /
          weightedDenominator (sample index) (focalWeight index) := by
    filter_upwards [hden_pos, hfocalWeight_nonneg, hcoeff_nonneg, hsum,
      hlipschitz, hradius] with index hden_pos_index
      hfocalWeight_nonneg_index hcoeff_nonneg_index hsum_index
      hlipschitz_index hradius_index
    exact
      abs_aggregate_meanDiscrepancy_le_lipschitz_radius_average
        (sample index) (donorSet index) (coefficient index)
        (focalWeight index) (mean index) (scoreDistance index)
        lipschitzConstant (radius index)
        hden_pos_index
        hfocalWeight_nonneg_index
        hcoeff_nonneg_index
        hsum_index
        hlipschitz_index
        hradius_index
        hlipschitz_nonneg
  exact tendsto_scaled_zero_of_eventually_abs_le_bound
    scale
    (fun index =>
      weightedSum (sample index) (focalWeight index)
        (fun focal =>
          meanDiscrepancy (donorSet index focal) (coefficient index)
            (mean index) focal) /
        weightedDenominator (sample index) (focalWeight index))
    (fun index =>
      weightedSum (sample index) (focalWeight index)
        (fun focal => lipschitzConstant * radius index focal) /
      weightedDenominator (sample index) (focalWeight index))
    hscale_nonneg hbound hscaled_radius_average_tendsto

end WDSM
end Matching
end StatInference
