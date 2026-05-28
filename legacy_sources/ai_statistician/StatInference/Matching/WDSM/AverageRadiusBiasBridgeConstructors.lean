import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Matching.WDSM.MatchingBiasRate

/-!
# Constructors for the average-radius bias bridge

The Chen-Han nearest-neighbor radius input should feed the WDSM bias route
through a weighted average local-radius rate.  This module packages the
checked deterministic `MatchingBiasRate` theorem into the abstract
`AverageRadiusBiasBridge` used by the known-score asymptotic interface.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit : Type*} {l : Filter Index}

/--
Construct the `AverageRadiusBiasBridge` from eventual finite matching
regularity, a Lipschitz score-mean condition, and the scaled weighted
average-radius rate.
-/
noncomputable def averageRadiusBiasBridge_of_eventually_radius_average
    (sample : Index -> Finset Unit)
    (donorSet : Index -> Unit -> Finset Unit)
    (coefficient : Index -> Unit -> Unit -> Real)
    (focalWeight mean : Index -> Unit -> Real)
    (scoreDistance : Index -> Unit -> Unit -> Real)
    (scale : Index -> Real) (radius : Index -> Unit -> Real)
    (lipschitzConstant : Real) :
    AverageRadiusBiasBridge where
  eventual_finite_matching_regular :=
    (∀ᶠ index in l, 0 ≤ scale index) ∧
    (∀ᶠ index in l,
      0 < weightedDenominator (sample index) (focalWeight index)) ∧
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ focalWeight index focal) ∧
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          0 ≤ coefficient index focal donor) ∧
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        (∑ donor ∈ donorSet index focal,
          coefficient index focal donor) = 1) ∧
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          scoreDistance index focal donor ≤ radius index focal)
  lipschitz_score_mean_regular :=
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          |mean index focal - mean index donor| ≤
            lipschitzConstant * scoreDistance index focal donor) ∧
    0 ≤ lipschitzConstant
  weighted_average_radius_rate :=
    Tendsto
      (fun index => scale index *
        (weightedSum (sample index) (focalWeight index)
          (fun focal => lipschitzConstant * radius index focal) /
        weightedDenominator (sample index) (focalWeight index)))
      l (nhds 0)
  matching_discrepancy_negligible :=
    Tendsto
      (fun index => scale index *
        (weightedSum (sample index) (focalWeight index)
          (fun focal =>
            meanDiscrepancy (donorSet index focal) (coefficient index)
              (mean index) focal) /
          weightedDenominator (sample index) (focalWeight index)))
      l (nhds 0)
  bridge := by
    intro hfinite hlipschitz hradius_rate
    rcases hfinite with
      ⟨hscale_nonneg, hden_pos, hfocalWeight_nonneg, hcoeff_nonneg,
        hsum, hradius⟩
    rcases hlipschitz with
      ⟨hlipschitz_bound, hlipschitz_nonneg⟩
    exact
      tendsto_scaled_aggregate_meanDiscrepancy_zero_of_eventually_radius_average
        (l := l) sample donorSet coefficient focalWeight mean
        scoreDistance scale radius lipschitzConstant hscale_nonneg
        hden_pos hfocalWeight_nonneg hcoeff_nonneg hsum hlipschitz_bound
        hradius hlipschitz_nonneg hradius_rate

/--
Construct the `AverageRadiusBiasBridge` from a second-moment radius-rate
package.  The finite matching regularity and Lipschitz score-mean fields are
the same as in `averageRadiusBiasBridge_of_eventually_radius_average`; only the
radius-rate premise is narrowed to the deterministic second-moment package.
-/
noncomputable def averageRadiusBiasBridge_of_eventually_second_moment_radius_rate
    (sample : Index -> Finset Unit)
    (donorSet : Index -> Unit -> Finset Unit)
    (coefficient : Index -> Unit -> Unit -> Real)
    (focalWeight mean : Index -> Unit -> Real)
    (scoreDistance : Index -> Unit -> Unit -> Real)
    (scale : Index -> Real) (radius : Index -> Unit -> Real)
    (radiusRate : Index -> Real) (lipschitzConstant : Real) :
    AverageRadiusBiasBridge where
  eventual_finite_matching_regular :=
    (∀ᶠ index in l, 0 ≤ scale index) ∧
    (∀ᶠ index in l,
      0 < weightedDenominator (sample index) (focalWeight index)) ∧
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ focalWeight index focal) ∧
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          0 ≤ coefficient index focal donor) ∧
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        (∑ donor ∈ donorSet index focal,
          coefficient index focal donor) = 1) ∧
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          scoreDistance index focal donor ≤ radius index focal)
  lipschitz_score_mean_regular :=
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        ∀ donor, donor ∈ donorSet index focal ->
          |mean index focal - mean index donor| ≤
            lipschitzConstant * scoreDistance index focal donor) ∧
    0 ≤ lipschitzConstant
  weighted_average_radius_rate :=
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0)
  matching_discrepancy_negligible :=
    Tendsto
      (fun index => scale index *
        (weightedSum (sample index) (focalWeight index)
          (fun focal =>
            meanDiscrepancy (donorSet index focal) (coefficient index)
              (mean index) focal) /
          weightedDenominator (sample index) (focalWeight index)))
      l (nhds 0)
  bridge := by
    intro hfinite hlipschitz hsecond_moment_rate
    have hfinite_for_base := hfinite
    have hlipschitz_for_base := hlipschitz
    rcases hfinite with
      ⟨hscale_nonneg, hden_pos, hfocalWeight_nonneg, hcoeff_nonneg,
        hsum, hradius⟩
    rcases hlipschitz with
      ⟨hlipschitz_bound, hlipschitz_nonneg⟩
    rcases hsecond_moment_rate with
      ⟨hradius_nonneg, hsecond_moment_bound, hradiusRate_nonneg,
        hscaled_radiusRate_tendsto⟩
    let base :=
      averageRadiusBiasBridge_of_eventually_radius_average
        (l := l) sample donorSet coefficient focalWeight mean scoreDistance
        scale radius lipschitzConstant
    have hradius_rate : base.weighted_average_radius_rate :=
      tendsto_scaled_weighted_average_radius_zero_of_second_moment_rate
        (l := l) sample focalWeight radius scale radiusRate lipschitzConstant
        hscale_nonneg hden_pos hfocalWeight_nonneg hradius_nonneg
        hsecond_moment_bound hradiusRate_nonneg hlipschitz_nonneg
        hscaled_radiusRate_tendsto
    exact matching_discrepancy_negligible_of_average_radius base
      hfinite_for_base hlipschitz_for_base hradius_rate

end WDSM
end Matching
end StatInference
