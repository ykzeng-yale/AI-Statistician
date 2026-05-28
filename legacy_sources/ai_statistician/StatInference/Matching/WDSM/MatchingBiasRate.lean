import StatInference.Matching.WDSM.AggregateLipschitzBiasBound
import StatInference.Matching.WDSM.ChenHanSamplingCount
import StatInference.Matching.WDSM.ScaledSqueezeAlgebra
import Mathlib.Data.Real.Sqrt

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
Finite weighted Cauchy-Schwarz radius reducer.  If the weighted second moment of
the local radii is bounded by `radiusRate ^ 2`, then the weighted average radius
is bounded by `radiusRate`.
-/
theorem weighted_average_radius_le_second_moment_rate
    (sample : Finset Unit) (weight radius : Unit -> Real)
    (radiusRate : Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hsecond_moment_bound :
      weightedSum sample weight (fun unit => radius unit ^ 2) /
        weightedDenominator sample weight ≤ radiusRate ^ 2)
    (hradiusRate_nonneg : 0 ≤ radiusRate) :
    weightedSum sample weight radius / weightedDenominator sample weight ≤
      radiusRate := by
  let denominator := weightedDenominator sample weight
  let secondMoment := weightedSum sample weight (fun unit => radius unit ^ 2)
  have hden_nonneg : 0 ≤ denominator := hden_pos.le
  have hcs_raw :=
    Real.sum_mul_le_sqrt_mul_sqrt sample
      (fun unit => √(weight unit))
      (fun unit => √(weight unit) * radius unit)
  have hleft_eq :
      (∑ unit ∈ sample, √(weight unit) * (√(weight unit) * radius unit)) =
        weightedSum sample weight radius := by
    unfold weightedSum
    refine Finset.sum_congr rfl ?_
    intro unit hunit
    rw [← mul_assoc, ← pow_two, Real.sq_sqrt (hweight_nonneg unit hunit)]
  have hfirst_eq :
      (∑ unit ∈ sample, (√(weight unit)) ^ 2) = denominator := by
    dsimp [denominator]
    unfold weightedDenominator
    exact Finset.sum_congr rfl
      (fun unit hunit => Real.sq_sqrt (hweight_nonneg unit hunit))
  have hsecond_eq :
      (∑ unit ∈ sample, (√(weight unit) * radius unit) ^ 2) =
        secondMoment := by
    dsimp [secondMoment]
    unfold weightedSum
    refine Finset.sum_congr rfl ?_
    intro unit hunit
    rw [mul_pow, Real.sq_sqrt (hweight_nonneg unit hunit)]
  have hsum_le_sqrt :
      weightedSum sample weight radius ≤ √denominator * √secondMoment := by
    simpa [hleft_eq, hfirst_eq, hsecond_eq] using hcs_raw
  have hsecond_le : secondMoment ≤ denominator * radiusRate ^ 2 := by
    rw [div_le_iff₀' hden_pos] at hsecond_moment_bound
    simpa [denominator, secondMoment] using hsecond_moment_bound
  have hsqrt_second_le : √secondMoment ≤ √(denominator * radiusRate ^ 2) :=
    Real.sqrt_le_sqrt hsecond_le
  have hsqrt_bound :
      √(denominator * radiusRate ^ 2) = √denominator * radiusRate := by
    rw [Real.sqrt_mul hden_nonneg, Real.sqrt_sq hradiusRate_nonneg]
  have hsum_le : weightedSum sample weight radius ≤ denominator * radiusRate := by
    calc
      weightedSum sample weight radius ≤ √denominator * √secondMoment :=
        hsum_le_sqrt
      _ ≤ √denominator * √(denominator * radiusRate ^ 2) := by
        exact mul_le_mul_of_nonneg_left hsqrt_second_le
          (Real.sqrt_nonneg denominator)
      _ = √denominator * (√denominator * radiusRate) := by
        rw [hsqrt_bound]
      _ = denominator * radiusRate := by
        rw [← mul_assoc, ← sq, Real.sq_sqrt hden_nonneg]
  rw [div_le_iff₀' hden_pos]
  simpa [denominator] using hsum_le

/--
If a positive-weight finite sample has nonnegative radii pointwise bounded by a
common `radiusRate`, then that rate is nonnegative.  This discharges the rate
nonnegativity side condition in the pointwise-radius route below.
-/
theorem radiusRate_nonneg_of_positive_weightedDenominator_of_pointwise_radius_bound
    (sample : Finset Unit) (weight radius : Unit -> Real)
    (radiusRate : Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hradius_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ radius unit)
    (hradius_le : ∀ unit, unit ∈ sample -> radius unit ≤ radiusRate) :
    0 ≤ radiusRate := by
  have hexists : ∃ unit ∈ sample, 0 < weight unit := by
    unfold weightedDenominator at hden_pos
    exact (Finset.sum_pos_iff_of_nonneg hweight_nonneg).1 hden_pos
  rcases hexists with ⟨unit, hunit, _hweight_pos⟩
  exact le_trans (hradius_nonneg unit hunit) (hradius_le unit hunit)

/--
Finite deterministic radius-square reducer.  A pointwise radius bound on the
finite sample implies the weighted radius-square average is bounded by
`radiusRate ^ 2`.
-/
theorem weighted_radius_square_average_le_of_pointwise_radius_bound
    (sample : Finset Unit) (weight radius : Unit -> Real)
    (radiusRate : Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hradius_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ radius unit)
    (hradius_le : ∀ unit, unit ∈ sample -> radius unit ≤ radiusRate) :
    weightedSum sample weight (fun unit => radius unit ^ 2) /
      weightedDenominator sample weight ≤ radiusRate ^ 2 := by
  have hradiusRate_nonneg : 0 ≤ radiusRate :=
    radiusRate_nonneg_of_positive_weightedDenominator_of_pointwise_radius_bound
      sample weight radius radiusRate hden_pos hweight_nonneg hradius_nonneg
      hradius_le
  have hsq_le :
      ∀ unit, unit ∈ sample -> radius unit ^ 2 ≤ radiusRate ^ 2 := by
    intro unit hunit
    exact (sq_le_sq₀ (hradius_nonneg unit hunit) hradiusRate_nonneg).2
      (hradius_le unit hunit)
  have hsum_le :
      weightedSum sample weight (fun unit => radius unit ^ 2) ≤
        weightedSum sample weight (fun _unit => radiusRate ^ 2) := by
    unfold weightedSum
    exact Finset.sum_le_sum
      (fun unit hunit =>
        mul_le_mul_of_nonneg_left (hsq_le unit hunit)
          (hweight_nonneg unit hunit))
  calc
    weightedSum sample weight (fun unit => radius unit ^ 2) /
        weightedDenominator sample weight
      ≤ weightedSum sample weight (fun _unit => radiusRate ^ 2) /
          weightedDenominator sample weight := by
            exact div_le_div_of_nonneg_right hsum_le hden_pos.le
    _ = radiusRate ^ 2 := by
          rw [weightedSum_const]
          exact mul_div_cancel_right₀ (radiusRate ^ 2) hden_pos.ne'

/--
Eventual version of
`weighted_radius_square_average_le_of_pointwise_radius_bound`.
-/
theorem eventually_weighted_radius_square_average_le_of_eventually_pointwise_radius_bound
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradius_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤ radiusRate index) :
    ∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2 := by
  filter_upwards [hden_pos, hfocalWeight_nonneg, hradius_nonneg, hradius_le]
    with index hden_pos_index hfocalWeight_nonneg_index hradius_nonneg_index
      hradius_le_index
  exact weighted_radius_square_average_le_of_pointwise_radius_bound
    (sample index) (focalWeight index) (radius index) (radiusRate index)
    hden_pos_index hfocalWeight_nonneg_index hradius_nonneg_index
    hradius_le_index

/--
Eventual rate nonnegativity from the same pointwise-radius package.
-/
theorem eventually_radiusRate_nonneg_of_eventually_pointwise_radius_bound
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradius_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤ radiusRate index) :
    ∀ᶠ index in l, 0 ≤ radiusRate index := by
  filter_upwards [hden_pos, hfocalWeight_nonneg, hradius_nonneg, hradius_le]
    with index hden_pos_index hfocalWeight_nonneg_index hradius_nonneg_index
      hradius_le_index
  exact radiusRate_nonneg_of_positive_weightedDenominator_of_pointwise_radius_bound
    (sample index) (focalWeight index) (radius index) (radiusRate index)
    hden_pos_index hfocalWeight_nonneg_index hradius_nonneg_index
    hradius_le_index

/--
Package an eventual pointwise radius bound into the exact second-moment
radius-rate premise consumed by
`averageRadiusBiasBridge_of_eventually_second_moment_radius_rate`.
-/
theorem second_moment_radius_rate_package_of_eventually_pointwise_radius_bound
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (scale radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradius_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤ radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  refine ⟨hradius_nonneg, ?_, ?_, hscaled_radiusRate_tendsto⟩
  · exact
      eventually_weighted_radius_square_average_le_of_eventually_pointwise_radius_bound
        (l := l) sample focalWeight radius radiusRate hden_pos
        hfocalWeight_nonneg hradius_nonneg hradius_le
  · exact
      eventually_radiusRate_nonneg_of_eventually_pointwise_radius_bound
        (l := l) sample focalWeight radius radiusRate hden_pos
        hfocalWeight_nonneg hradius_nonneg hradius_le

/--
Metric nearest-neighbor route into the second-moment radius-rate package.  It
separates the finite deterministic step from the still-open geometric occupancy
claim: every focal unit has a selected neighbor within `radiusRate`.
-/
theorem second_moment_radius_rate_package_of_eventually_metric_neighbor_bound
    {l : Filter Index} {Score : Type*} [PseudoMetricSpace Score]
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (score : Index -> Unit -> Score)
    (neighbor : Index -> Unit -> Unit)
    (scale radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradius_le_neighbor :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤
            dist (score index focal) (score index (neighbor index focal)))
    (hneighbor_dist_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          dist (score index focal) (score index (neighbor index focal)) ≤
            radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  have hradius_le_rate :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤ radiusRate index := by
    filter_upwards [hradius_le_neighbor, hneighbor_dist_le]
      with index hradius_le_neighbor_index hneighbor_dist_le_index
    intro focal hfocal
    exact le_trans (hradius_le_neighbor_index focal hfocal)
      (hneighbor_dist_le_index focal hfocal)
  exact second_moment_radius_rate_package_of_eventually_pointwise_radius_bound
    (l := l) sample focalWeight radius scale radiusRate hden_pos
    hfocalWeight_nonneg hradius_nonneg hradius_le_rate
    hscaled_radiusRate_tendsto

/--
Metric donor-cover route into the second-moment radius-rate package.  This
version does not require a preselected neighbor: an eventual donor within
`radiusRate` for each focal, plus the nearest-neighbor domination property for
`radius`, yields the pointwise radius-rate premise.
-/
theorem second_moment_radius_rate_package_of_eventually_metric_donor_cover_bound
    {l : Filter Index} {Score : Type*} [PseudoMetricSpace Score]
    (sample donorSet : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (score : Index -> Unit -> Score)
    (scale radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradius_le_donor :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∀ donor, donor ∈ donorSet index ->
            radius index focal ≤ dist (score index focal) (score index donor))
    (hdonor_cover :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∃ donor, donor ∈ donorSet index ∧
            dist (score index focal) (score index donor) ≤ radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  have hradius_le_rate :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤ radiusRate index := by
    filter_upwards [hradius_le_donor, hdonor_cover]
      with index hradius_le_donor_index hdonor_cover_index
    intro focal hfocal
    rcases hdonor_cover_index focal hfocal with ⟨donor, hdonor, hdist⟩
    exact le_trans (hradius_le_donor_index focal hfocal donor hdonor) hdist
  exact second_moment_radius_rate_package_of_eventually_pointwise_radius_bound
    (l := l) sample focalWeight radius scale radiusRate hden_pos
    hfocalWeight_nonneg hradius_nonneg hradius_le_rate
    hscaled_radiusRate_tendsto

/--
Finite score-cover occupancy gives the metric donor-cover premise.  A focal
score lies within `coverRadius` of its assigned cover center; every cover cell
has an available donor within `donorRadius` of that center; and the two radii
fit inside `radiusRate`.
-/
theorem eventually_metric_donor_cover_of_eventually_finite_score_cover_occupancy
    {l : Filter Index} {Cell Score : Type*} [PseudoMetricSpace Score]
    (sample donorSet : Index -> Finset Unit)
    (cover : Index -> Finset Cell)
    (score : Index -> Unit -> Score)
    (cellOf : Index -> Unit -> Cell)
    (center : Index -> Cell -> Score)
    (coverRadius donorRadius radiusRate : Index -> Real)
    (hcell_mem :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          cellOf index focal ∈ cover index)
    (hfocal_near_center :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          dist (score index focal) (center index (cellOf index focal)) ≤
            coverRadius index)
    (hcover_cell_donor_available :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover index ->
          ∃ donor, donor ∈ donorSet index ∧
            dist (center index cell) (score index donor) ≤
              donorRadius index)
    (hradius_sum_le :
      ∀ᶠ index in l,
        coverRadius index + donorRadius index ≤ radiusRate index) :
    ∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        ∃ donor, donor ∈ donorSet index ∧
          dist (score index focal) (score index donor) ≤ radiusRate index := by
  filter_upwards [hcell_mem, hfocal_near_center,
    hcover_cell_donor_available, hradius_sum_le] with index hcell_mem_index
      hfocal_near_center_index hcover_cell_donor_available_index
      hradius_sum_le_index
  intro focal hfocal
  rcases hcover_cell_donor_available_index (cellOf index focal)
      (hcell_mem_index focal hfocal) with
    ⟨donor, hdonor, hcenter_donor⟩
  refine ⟨donor, hdonor, ?_⟩
  calc
    dist (score index focal) (score index donor)
        ≤ dist (score index focal) (center index (cellOf index focal)) +
            dist (center index (cellOf index focal)) (score index donor) :=
          dist_triangle _ _ _
    _ ≤ coverRadius index + donorRadius index := by
          exact add_le_add (hfocal_near_center_index focal hfocal)
            hcenter_donor
    _ ≤ radiusRate index := hradius_sum_le_index

/--
Finite score-cover occupancy route into the second-moment radius-rate package.
The probabilistic Chen-Han step can now target the cover-cell donor availability
premise directly.
-/
theorem second_moment_radius_rate_package_of_eventually_finite_score_cover_occupancy
    {l : Filter Index} {Cell Score : Type*} [PseudoMetricSpace Score]
    (sample donorSet : Index -> Finset Unit)
    (cover : Index -> Finset Cell)
    (focalWeight radius : Index -> Unit -> Real)
    (score : Index -> Unit -> Score)
    (cellOf : Index -> Unit -> Cell)
    (center : Index -> Cell -> Score)
    (scale coverRadius donorRadius radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradius_le_donor :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∀ donor, donor ∈ donorSet index ->
            radius index focal ≤ dist (score index focal) (score index donor))
    (hcell_mem :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          cellOf index focal ∈ cover index)
    (hfocal_near_center :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          dist (score index focal) (center index (cellOf index focal)) ≤
            coverRadius index)
    (hcover_cell_donor_available :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover index ->
          ∃ donor, donor ∈ donorSet index ∧
            dist (center index cell) (score index donor) ≤
              donorRadius index)
    (hradius_sum_le :
      ∀ᶠ index in l,
        coverRadius index + donorRadius index ≤ radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  have hdonor_cover :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∃ donor, donor ∈ donorSet index ∧
            dist (score index focal) (score index donor) ≤
              radiusRate index :=
    eventually_metric_donor_cover_of_eventually_finite_score_cover_occupancy
      (l := l) sample donorSet cover score cellOf center coverRadius
      donorRadius radiusRate hcell_mem hfocal_near_center
      hcover_cell_donor_available hradius_sum_le
  exact
    second_moment_radius_rate_package_of_eventually_metric_donor_cover_bound
      (l := l) sample donorSet focalWeight radius score scale radiusRate
      hden_pos hfocalWeight_nonneg hradius_nonneg hradius_le_donor
      hdonor_cover hscaled_radiusRate_tendsto

/--
Positive donor count in every cover ball yields the finite cover-cell donor
availability premise used by
`eventually_metric_donor_cover_of_eventually_finite_score_cover_occupancy`.
-/
theorem eventually_cover_cell_donor_available_of_eventually_cover_cell_count_lower_bound
    {l : Filter Index} {Cell Score : Type*} [PseudoMetricSpace Score]
    (donorSet : Index -> Finset Unit)
    (cover : Index -> Finset Cell)
    (score : Index -> Unit -> Score)
    (center : Index -> Cell -> Score)
    (donorRadius : Index -> Real)
    (minDonors : Index -> Nat)
    (hminDonors_pos : ∀ᶠ index in l, 0 < minDonors index)
    (hcount_lower :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover index ->
          minDonors index ≤
            ((donorSet index).filter
              (fun donor =>
                dist (center index cell) (score index donor) ≤
                  donorRadius index)).card) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cover index ->
        ∃ donor, donor ∈ donorSet index ∧
          dist (center index cell) (score index donor) ≤ donorRadius index := by
  filter_upwards [hminDonors_pos, hcount_lower]
    with index hminDonors_pos_index hcount_lower_index
  intro cell hcell
  have hcount_pos :
      0 < ((donorSet index).filter
        (fun donor =>
          dist (center index cell) (score index donor) ≤
            donorRadius index)).card :=
    lt_of_lt_of_le hminDonors_pos_index (hcount_lower_index cell hcell)
  rcases Finset.card_pos.mp hcount_pos with ⟨donor, hdonor_filter⟩
  exact ⟨donor, (Finset.mem_filter.mp hdonor_filter).1,
    (Finset.mem_filter.mp hdonor_filter).2⟩

/--
Fixed finite-cover normalized donor counts give the eventual raw count lower
bound consumed by the cover-cell donor availability constructor.  This is the
deterministic endpoint of a future binomial-tail or LLN proof for each cover
ball.
-/
theorem eventually_cover_cell_count_lower_bound_of_fixed_cover_normalized_count_tendsto
    {l : Filter Index} {Cell Score : Type*} [PseudoMetricSpace Score]
    (donorSet : Index -> Finset Unit)
    (cover : Finset Cell)
    (score : Index -> Unit -> Score)
    (center : Index -> Cell -> Score)
    (donorRadius sampleSize : Index -> Real)
    (cellMass cellMassLower : Cell -> Real)
    (minDonors : Index -> Nat)
    (hsampleSize_pos : ∀ᶠ index in l, 0 < sampleSize index)
    (hcount_tendsto :
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun index =>
            (((donorSet index).filter
              (fun donor =>
                dist (center index cell) (score index donor) ≤
                  donorRadius index)).card : Real) /
              sampleSize index)
          l (nhds (cellMass cell)))
    (hlower_lt_mass :
      ∀ cell, cell ∈ cover -> cellMassLower cell < cellMass cell)
    (hminDonors_le :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover ->
          (minDonors index : Real) ≤
            cellMassLower cell * sampleSize index) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cover ->
        minDonors index ≤
          ((donorSet index).filter
            (fun donor =>
              dist (center index cell) (score index donor) ≤
                donorRadius index)).card := by
  have hnormalized_lower :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover ->
          cellMassLower cell ≤
            (((donorSet index).filter
              (fun donor =>
                dist (center index cell) (score index donor) ≤
                  donorRadius index)).card : Real) /
              sampleSize index :=
    (Filter.eventually_all_finset cover).mpr
      (fun cell hcell =>
        (hcount_tendsto cell hcell).eventually
          (eventually_ge_nhds (hlower_lt_mass cell hcell)))
  filter_upwards [hsampleSize_pos, hminDonors_le, hnormalized_lower]
    with index hsampleSize_pos_index hminDonors_le_index
      hnormalized_lower_index
  intro cell hcell
  let count : Nat :=
    ((donorSet index).filter
      (fun donor =>
        dist (center index cell) (score index donor) ≤
          donorRadius index)).card
  have hmass_sample_le_count :
      cellMassLower cell * sampleSize index ≤ (count : Real) := by
    have hmul :
        cellMassLower cell * sampleSize index ≤
          ((((donorSet index).filter
            (fun donor =>
              dist (center index cell) (score index donor) ≤
                donorRadius index)).card : Real) /
            sampleSize index) * sampleSize index :=
      mul_le_mul_of_nonneg_right
        (hnormalized_lower_index cell hcell) hsampleSize_pos_index.le
    calc
      cellMassLower cell * sampleSize index
          ≤
            ((((donorSet index).filter
              (fun donor =>
                dist (center index cell) (score index donor) ≤
                  donorRadius index)).card : Real) /
              sampleSize index) * sampleSize index := hmul
      _ = (count : Real) := by
            dsimp [count]
            field_simp [hsampleSize_pos_index.ne']
  have hmin_le_count_real : (minDonors index : Real) ≤ (count : Real) :=
    le_trans (hminDonors_le_index cell hcell) hmass_sample_le_count
  change minDonors index ≤ count
  exact_mod_cast hmin_le_count_real

/--
For a fixed finite cover, positive lower cell masses, sample-size growth, and a
bounded matching count imply the deterministic scaling side condition required
by the normalized-count cover-cell theorem.
-/
theorem eventually_minDonors_le_cellMassLower_mul_sampleSize_of_bounded_minDonors_of_tendsto_atTop
    {l : Filter Index} {Cell : Type*}
    (cover : Finset Cell)
    (sampleSize : Index -> Real)
    (cellMassLower : Cell -> Real)
    (minDonors : Index -> Nat)
    (minDonorsCap : Nat)
    (hsampleSize_tendsto : Tendsto sampleSize l atTop)
    (hlower_pos : ∀ cell, cell ∈ cover -> 0 < cellMassLower cell)
    (hminDonors_le_cap : ∀ᶠ index in l, minDonors index ≤ minDonorsCap) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cover ->
        (minDonors index : Real) ≤
          cellMassLower cell * sampleSize index := by
  have hcap_le_growth :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover ->
          (minDonorsCap : Real) ≤
            cellMassLower cell * sampleSize index :=
    (Filter.eventually_all_finset cover).mpr
      (fun cell hcell => by
        have hsample_large :
            ∀ᶠ index in l,
              (minDonorsCap : Real) / cellMassLower cell ≤
                sampleSize index :=
          hsampleSize_tendsto.eventually (eventually_ge_atTop _)
        filter_upwards [hsample_large] with index hsample_large_index
        have hmul :
            ((minDonorsCap : Real) / cellMassLower cell) *
                cellMassLower cell ≤
              sampleSize index * cellMassLower cell :=
          mul_le_mul_of_nonneg_right hsample_large_index
            (hlower_pos cell hcell).le
        have hcancel :
            ((minDonorsCap : Real) / cellMassLower cell) *
                cellMassLower cell =
              (minDonorsCap : Real) := by
          field_simp [(hlower_pos cell hcell).ne']
        calc
          (minDonorsCap : Real)
              =
                ((minDonorsCap : Real) / cellMassLower cell) *
                  cellMassLower cell := hcancel.symm
          _ ≤ sampleSize index * cellMassLower cell := hmul
          _ = cellMassLower cell * sampleSize index := by rw [mul_comm])
  filter_upwards [hminDonors_le_cap, hcap_le_growth]
    with index hminDonors_le_cap_index hcap_le_growth_index
  intro cell hcell
  have hminDonors_le_cap_real :
      (minDonors index : Real) ≤ (minDonorsCap : Real) := by
    exact_mod_cast hminDonors_le_cap_index
  exact le_trans hminDonors_le_cap_real (hcap_le_growth_index cell hcell)

/--
Cellwise metric-ball indicator-sum convergence gives the eventual raw
cover-ball donor-count lower bound.  This is the direct deterministic consumer
for an iid/binomial LLN over fixed positive-mass cover balls.
-/
theorem eventually_cover_cell_count_lower_bound_of_fixed_cover_metricClosedBallIndicator_weightedSum_tendsto
    {l : Filter Index} {Cell Score : Type*} [PseudoMetricSpace Score]
    (donorSet : Index -> Finset Unit)
    (cover : Finset Cell)
    (score : Index -> Unit -> Score)
    (center : Index -> Cell -> Score)
    (donorRadius sampleSize : Index -> Real)
    (cellMass cellMassLower : Cell -> Real)
    (minDonors : Index -> Nat)
    (hsampleSize_pos : ∀ᶠ index in l, 0 < sampleSize index)
    (hindicator :
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun index =>
            weightedSum (donorSet index)
              (fun _donor => (sampleSize index)⁻¹)
              (fun donor =>
                metricClosedBallIndicator
                  (center index cell) (donorRadius index)
                  (score index donor)))
          l (nhds (cellMass cell)))
    (hlower_lt_mass :
      ∀ cell, cell ∈ cover -> cellMassLower cell < cellMass cell)
    (hminDonors_le :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover ->
          (minDonors index : Real) ≤
            cellMassLower cell * sampleSize index) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cover ->
        minDonors index ≤
          ((donorSet index).filter
            (fun donor =>
              dist (center index cell) (score index donor) ≤
                donorRadius index)).card := by
  have hcount_tendsto :
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun index =>
            (((donorSet index).filter
              (fun donor =>
                dist (center index cell) (score index donor) ≤
                  donorRadius index)).card : Real) /
              sampleSize index)
          l (nhds (cellMass cell)) :=
    fixed_cover_normalized_count_tendsto_of_metricClosedBallIndicator_weightedSum_tendsto
      donorSet cover score center donorRadius sampleSize cellMass hindicator
  exact
    eventually_cover_cell_count_lower_bound_of_fixed_cover_normalized_count_tendsto
      (l := l) donorSet cover score center donorRadius sampleSize
      cellMass cellMassLower minDonors hsampleSize_pos hcount_tendsto
      hlower_lt_mass hminDonors_le

/--
Finite score-cover count lower-bound route into the second-moment radius-rate
package.  This is the deterministic endpoint for a future binomial-tail proof
that every cover ball contains at least `minDonors` sampled donors.
-/
theorem second_moment_radius_rate_package_of_eventually_finite_score_cover_count_lower_bound
    {l : Filter Index} {Cell Score : Type*} [PseudoMetricSpace Score]
    (sample donorSet : Index -> Finset Unit)
    (cover : Index -> Finset Cell)
    (focalWeight radius : Index -> Unit -> Real)
    (score : Index -> Unit -> Score)
    (cellOf : Index -> Unit -> Cell)
    (center : Index -> Cell -> Score)
    (scale coverRadius donorRadius radiusRate : Index -> Real)
    (minDonors : Index -> Nat)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradius_le_donor :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∀ donor, donor ∈ donorSet index ->
            radius index focal ≤ dist (score index focal) (score index donor))
    (hcell_mem :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          cellOf index focal ∈ cover index)
    (hfocal_near_center :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          dist (score index focal) (center index (cellOf index focal)) ≤
            coverRadius index)
    (hminDonors_pos : ∀ᶠ index in l, 0 < minDonors index)
    (hcount_lower :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover index ->
          minDonors index ≤
            ((donorSet index).filter
              (fun donor =>
                dist (center index cell) (score index donor) ≤
                  donorRadius index)).card)
    (hradius_sum_le :
      ∀ᶠ index in l,
        coverRadius index + donorRadius index ≤ radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  have hcover_cell_donor_available :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover index ->
          ∃ donor, donor ∈ donorSet index ∧
            dist (center index cell) (score index donor) ≤
              donorRadius index :=
    eventually_cover_cell_donor_available_of_eventually_cover_cell_count_lower_bound
      (l := l) donorSet cover score center donorRadius minDonors
      hminDonors_pos hcount_lower
  exact
    second_moment_radius_rate_package_of_eventually_finite_score_cover_occupancy
      (l := l) sample donorSet cover focalWeight radius score cellOf center
      scale coverRadius donorRadius radiusRate hden_pos hfocalWeight_nonneg
      hradius_nonneg hradius_le_donor hcell_mem hfocal_near_center
      hcover_cell_donor_available hradius_sum_le
      hscaled_radiusRate_tendsto

/--
Fixed-cover normalized donor-count convergence route into the second-moment
radius-rate package.  The only stochastic input left outside this theorem is
the LLN/binomial-tail proof of normalized counts for each fixed cover ball.
-/
theorem second_moment_radius_rate_package_of_fixed_cover_normalized_count_tendsto
    {l : Filter Index} {Cell Score : Type*} [PseudoMetricSpace Score]
    (sample donorSet : Index -> Finset Unit)
    (cover : Finset Cell)
    (focalWeight radius : Index -> Unit -> Real)
    (score : Index -> Unit -> Score)
    (cellOf : Index -> Unit -> Cell)
    (center : Index -> Cell -> Score)
    (scale coverRadius donorRadius radiusRate sampleSize : Index -> Real)
    (cellMass cellMassLower : Cell -> Real)
    (minDonors : Index -> Nat)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradius_le_donor :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          ∀ donor, donor ∈ donorSet index ->
            radius index focal ≤ dist (score index focal) (score index donor))
    (hcell_mem :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          cellOf index focal ∈ cover)
    (hfocal_near_center :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          dist (score index focal) (center index (cellOf index focal)) ≤
            coverRadius index)
    (hminDonors_pos : ∀ᶠ index in l, 0 < minDonors index)
    (hsampleSize_pos : ∀ᶠ index in l, 0 < sampleSize index)
    (hcount_tendsto :
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun index =>
            (((donorSet index).filter
              (fun donor =>
                dist (center index cell) (score index donor) ≤
                  donorRadius index)).card : Real) /
              sampleSize index)
          l (nhds (cellMass cell)))
    (hlower_lt_mass :
      ∀ cell, cell ∈ cover -> cellMassLower cell < cellMass cell)
    (hminDonors_le :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover ->
          (minDonors index : Real) ≤
            cellMassLower cell * sampleSize index)
    (hradius_sum_le :
      ∀ᶠ index in l,
        coverRadius index + donorRadius index ≤ radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  have hcount_lower :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover ->
          minDonors index ≤
            ((donorSet index).filter
              (fun donor =>
                dist (center index cell) (score index donor) ≤
                  donorRadius index)).card :=
    eventually_cover_cell_count_lower_bound_of_fixed_cover_normalized_count_tendsto
      (l := l) donorSet cover score center donorRadius sampleSize
      cellMass cellMassLower minDonors hsampleSize_pos hcount_tendsto
      hlower_lt_mass hminDonors_le
  exact
    second_moment_radius_rate_package_of_eventually_finite_score_cover_count_lower_bound
      (l := l) sample donorSet (fun _index => cover) focalWeight radius score
      cellOf center scale coverRadius donorRadius radiusRate minDonors
      hden_pos hfocalWeight_nonneg hradius_nonneg hradius_le_donor hcell_mem
      hfocal_near_center hminDonors_pos hcount_lower hradius_sum_le
      hscaled_radiusRate_tendsto

/--
Finite normalization reducer for the weighted radius-square estimate.  If focal
weights are bounded by `weightCap`, the denominator is at least
`denominatorLower`, and the unweighted radius-square sum is small at that
normalization, then the weighted radius-square average is bounded by
`radiusRate ^ 2`.
-/
theorem weighted_radius_square_average_le_of_weight_cap_and_unweighted_square_sum_bound
    (sample : Finset Unit) (weight radius : Unit -> Real)
    (weightCap denominatorLower radiusRate : Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_le : ∀ unit, unit ∈ sample -> weight unit ≤ weightCap)
    (hden_lower : denominatorLower ≤ weightedDenominator sample weight)
    (hraw_bound :
      weightCap * (∑ unit ∈ sample, radius unit ^ 2) ≤
        denominatorLower * radiusRate ^ 2) :
    weightedSum sample weight (fun unit => radius unit ^ 2) /
      weightedDenominator sample weight ≤ radiusRate ^ 2 := by
  have hweighted_le_cap :
      weightedSum sample weight (fun unit => radius unit ^ 2) ≤
        weightCap * (∑ unit ∈ sample, radius unit ^ 2) := by
    unfold weightedSum
    calc
      (∑ unit ∈ sample, weight unit * (radius unit ^ 2))
          ≤ ∑ unit ∈ sample, weightCap * (radius unit ^ 2) := by
            exact Finset.sum_le_sum
              (fun unit hunit =>
                mul_le_mul_of_nonneg_right (hweight_le unit hunit)
                  (sq_nonneg (radius unit)))
      _ = weightCap * (∑ unit ∈ sample, radius unit ^ 2) := by
            rw [Finset.mul_sum]
  have hweighted_le_lower :
      weightedSum sample weight (fun unit => radius unit ^ 2) ≤
        denominatorLower * radiusRate ^ 2 :=
    le_trans hweighted_le_cap hraw_bound
  have hlower_le_den :
      denominatorLower * radiusRate ^ 2 ≤
        weightedDenominator sample weight * radiusRate ^ 2 :=
    mul_le_mul_of_nonneg_right hden_lower (sq_nonneg radiusRate)
  have hweighted_le_den :
      weightedSum sample weight (fun unit => radius unit ^ 2) ≤
        weightedDenominator sample weight * radiusRate ^ 2 :=
    le_trans hweighted_le_lower hlower_le_den
  rw [div_le_iff₀' hden_pos]
  exact hweighted_le_den

/--
Eventual version of the weight-cap/unweighted-square-sum normalization
reducer.
-/
theorem eventually_weighted_radius_square_average_le_of_eventually_weight_cap_and_unweighted_square_sum_bound
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (weightCap denominatorLower radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hweight_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          focalWeight index focal ≤ weightCap index)
    (hden_lower :
      ∀ᶠ index in l,
        denominatorLower index ≤
          weightedDenominator (sample index) (focalWeight index))
    (hraw_bound :
      ∀ᶠ index in l,
        weightCap index * (∑ focal ∈ sample index, radius index focal ^ 2) ≤
          denominatorLower index * radiusRate index ^ 2) :
    ∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2 := by
  filter_upwards [hden_pos, hweight_le, hden_lower, hraw_bound]
    with index hden_pos_index hweight_le_index hden_lower_index hraw_bound_index
  exact
    weighted_radius_square_average_le_of_weight_cap_and_unweighted_square_sum_bound
      (sample index) (focalWeight index) (radius index) (weightCap index)
      (denominatorLower index) (radiusRate index) hden_pos_index
      hweight_le_index hden_lower_index hraw_bound_index

/--
Package weight-cap, denominator-lower-bound, and unweighted radius-square sum
control into the exact second-moment radius-rate premise consumed by
`averageRadiusBiasBridge_of_eventually_second_moment_radius_rate`.
-/
theorem second_moment_radius_rate_package_of_eventually_weight_cap_and_unweighted_square_sum_bound
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (scale weightCap denominatorLower radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hweight_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          focalWeight index focal ≤ weightCap index)
    (hden_lower :
      ∀ᶠ index in l,
        denominatorLower index ≤
          weightedDenominator (sample index) (focalWeight index))
    (hraw_bound :
      ∀ᶠ index in l,
        weightCap index * (∑ focal ∈ sample index, radius index focal ^ 2) ≤
          denominatorLower index * radiusRate index ^ 2)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradiusRate_nonneg : ∀ᶠ index in l, 0 ≤ radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  refine ⟨hradius_nonneg, ?_, hradiusRate_nonneg,
    hscaled_radiusRate_tendsto⟩
  exact
    eventually_weighted_radius_square_average_le_of_eventually_weight_cap_and_unweighted_square_sum_bound
      (l := l) sample focalWeight radius weightCap denominatorLower
      radiusRate hden_pos hweight_le hden_lower hraw_bound

/--
Variant of the weight-cap reducer where the geometry input is a plain
unweighted square-sum upper bound.  The remaining normalization inequality
connects that raw bound to the denominator scale and target `radiusRate`.
-/
theorem weighted_radius_square_average_le_of_weight_cap_and_raw_square_sum_le
    (sample : Finset Unit) (weight radius : Unit -> Real)
    (weightCap rawSquareBound denominatorLower radiusRate : Real)
    (hden_pos : 0 < weightedDenominator sample weight)
    (hweight_le : ∀ unit, unit ∈ sample -> weight unit ≤ weightCap)
    (hweightCap_nonneg : 0 ≤ weightCap)
    (hraw_sum_le :
      (∑ unit ∈ sample, radius unit ^ 2) ≤ rawSquareBound)
    (hden_lower : denominatorLower ≤ weightedDenominator sample weight)
    (hnormalized_raw_bound :
      weightCap * rawSquareBound ≤ denominatorLower * radiusRate ^ 2) :
    weightedSum sample weight (fun unit => radius unit ^ 2) /
      weightedDenominator sample weight ≤ radiusRate ^ 2 := by
  have hraw_bound :
      weightCap * (∑ unit ∈ sample, radius unit ^ 2) ≤
        denominatorLower * radiusRate ^ 2 :=
    le_trans (mul_le_mul_of_nonneg_left hraw_sum_le hweightCap_nonneg)
      hnormalized_raw_bound
  exact
    weighted_radius_square_average_le_of_weight_cap_and_unweighted_square_sum_bound
      sample weight radius weightCap denominatorLower radiusRate hden_pos
      hweight_le hden_lower hraw_bound

/--
Eventual version of
`weighted_radius_square_average_le_of_weight_cap_and_raw_square_sum_le`.
-/
theorem eventually_weighted_radius_square_average_le_of_eventually_weight_cap_and_raw_square_sum_le
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (weightCap rawSquareBound denominatorLower radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hweight_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          focalWeight index focal ≤ weightCap index)
    (hweightCap_nonneg : ∀ᶠ index in l, 0 ≤ weightCap index)
    (hraw_sum_le :
      ∀ᶠ index in l,
        (∑ focal ∈ sample index, radius index focal ^ 2) ≤
          rawSquareBound index)
    (hden_lower :
      ∀ᶠ index in l,
        denominatorLower index ≤
          weightedDenominator (sample index) (focalWeight index))
    (hnormalized_raw_bound :
      ∀ᶠ index in l,
        weightCap index * rawSquareBound index ≤
          denominatorLower index * radiusRate index ^ 2) :
    ∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2 := by
  filter_upwards [hden_pos, hweight_le, hweightCap_nonneg, hraw_sum_le,
    hden_lower, hnormalized_raw_bound] with index hden_pos_index
    hweight_le_index hweightCap_nonneg_index hraw_sum_le_index
    hden_lower_index hnormalized_raw_bound_index
  exact
    weighted_radius_square_average_le_of_weight_cap_and_raw_square_sum_le
      (sample index) (focalWeight index) (radius index) (weightCap index)
      (rawSquareBound index) (denominatorLower index) (radiusRate index)
      hden_pos_index hweight_le_index hweightCap_nonneg_index
      hraw_sum_le_index hden_lower_index hnormalized_raw_bound_index

/--
Package the raw unweighted square-sum route into the exact second-moment
radius-rate premise consumed by
`averageRadiusBiasBridge_of_eventually_second_moment_radius_rate`.
-/
theorem second_moment_radius_rate_package_of_eventually_weight_cap_and_raw_square_sum_le
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (scale weightCap rawSquareBound denominatorLower radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hweight_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          focalWeight index focal ≤ weightCap index)
    (hweightCap_nonneg : ∀ᶠ index in l, 0 ≤ weightCap index)
    (hraw_sum_le :
      ∀ᶠ index in l,
        (∑ focal ∈ sample index, radius index focal ^ 2) ≤
          rawSquareBound index)
    (hden_lower :
      ∀ᶠ index in l,
        denominatorLower index ≤
          weightedDenominator (sample index) (focalWeight index))
    (hnormalized_raw_bound :
      ∀ᶠ index in l,
        weightCap index * rawSquareBound index ≤
          denominatorLower index * radiusRate index ^ 2)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradiusRate_nonneg : ∀ᶠ index in l, 0 ≤ radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  refine ⟨hradius_nonneg, ?_, hradiusRate_nonneg,
    hscaled_radiusRate_tendsto⟩
  exact
    eventually_weighted_radius_square_average_le_of_eventually_weight_cap_and_raw_square_sum_le
      (l := l) sample focalWeight radius weightCap rawSquareBound
      denominatorLower radiusRate hden_pos hweight_le hweightCap_nonneg
      hraw_sum_le hden_lower hnormalized_raw_bound

/--
Raw unweighted square-sum bound from pointwise finite radius control.  This is
the deterministic algebraic endpoint for a future finite covering or
nearest-neighbor radius theorem.
-/
theorem unweighted_radius_square_sum_le_card_mul_of_pointwise_radius_bound
    (sample : Finset Unit) (radius : Unit -> Real) (radiusRate : Real)
    (hradius_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ radius unit)
    (hradiusRate_nonneg : 0 ≤ radiusRate)
    (hradius_le : ∀ unit, unit ∈ sample -> radius unit ≤ radiusRate) :
    (∑ unit ∈ sample, radius unit ^ 2) ≤
      (sample.card : Real) * radiusRate ^ 2 := by
  have hsq_le :
      ∀ unit, unit ∈ sample -> radius unit ^ 2 ≤ radiusRate ^ 2 := by
    intro unit hunit
    exact (sq_le_sq₀ (hradius_nonneg unit hunit) hradiusRate_nonneg).2
      (hradius_le unit hunit)
  calc
    (∑ unit ∈ sample, radius unit ^ 2)
        ≤ ∑ unit ∈ sample, radiusRate ^ 2 := by
          exact Finset.sum_le_sum (fun unit hunit => hsq_le unit hunit)
    _ = (sample.card : Real) * radiusRate ^ 2 := by
          simp [Finset.sum_const, nsmul_eq_mul]

/--
Eventual version of
`unweighted_radius_square_sum_le_card_mul_of_pointwise_radius_bound`.
-/
theorem eventually_unweighted_radius_square_sum_le_card_mul_of_eventually_pointwise_radius_bound
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (radius : Index -> Unit -> Real)
    (radiusRate : Index -> Real)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hradiusRate_nonneg : ∀ᶠ index in l, 0 ≤ radiusRate index)
    (hradius_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤ radiusRate index) :
    ∀ᶠ index in l,
      (∑ focal ∈ sample index, radius index focal ^ 2) ≤
        ((sample index).card : Real) * radiusRate index ^ 2 := by
  filter_upwards [hradius_nonneg, hradiusRate_nonneg, hradius_le]
    with index hradius_nonneg_index hradiusRate_nonneg_index hradius_le_index
  exact
    unweighted_radius_square_sum_le_card_mul_of_pointwise_radius_bound
      (sample index) (radius index) (radiusRate index)
      hradius_nonneg_index hradiusRate_nonneg_index hradius_le_index

/--
Finite catchment-cover radius-square bound.  If every focal unit is assigned to
a cover cell and its radius is bounded by that cell's radius, then the raw
unweighted radius-square sum is bounded by the catchment count weighted sum of
cell-radius squares.
-/
theorem unweighted_radius_square_sum_le_catchment_cover_sum
    {Cell : Type*} [DecidableEq Cell]
    (sample : Finset Unit) (cover : Finset Cell)
    (cellOf : Unit -> Cell) (radius : Unit -> Real)
    (cellRadius : Cell -> Real)
    (hcell_mem : ∀ unit, unit ∈ sample -> cellOf unit ∈ cover)
    (hradius_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ radius unit)
    (hcellRadius_nonneg : ∀ cell, cell ∈ cover -> 0 ≤ cellRadius cell)
    (hradius_le_cell :
      ∀ unit, unit ∈ sample -> radius unit ≤ cellRadius (cellOf unit)) :
    (∑ unit ∈ sample, radius unit ^ 2) ≤
      ∑ cell ∈ cover,
        ((sample.filter (fun unit => cellOf unit = cell)).card : Real) *
          cellRadius cell ^ 2 := by
  have hsq_le :
      ∀ unit, unit ∈ sample ->
        radius unit ^ 2 ≤ cellRadius (cellOf unit) ^ 2 := by
    intro unit hunit
    exact (sq_le_sq₀ (hradius_nonneg unit hunit)
      (hcellRadius_nonneg (cellOf unit) (hcell_mem unit hunit))).2
      (hradius_le_cell unit hunit)
  have hsum_pointwise :
      (∑ unit ∈ sample, radius unit ^ 2) ≤
        ∑ unit ∈ sample, cellRadius (cellOf unit) ^ 2 := by
    exact Finset.sum_le_sum (fun unit hunit => hsq_le unit hunit)
  have hfiber :
      (∑ unit ∈ sample, cellRadius (cellOf unit) ^ 2) =
        ∑ cell ∈ cover, ∑ unit ∈ sample with cellOf unit = cell,
          cellRadius cell ^ 2 := by
    exact (Finset.sum_fiberwise_of_maps_to' hcell_mem
      (fun cell => cellRadius cell ^ 2)).symm
  have hconst :
      (∑ cell ∈ cover, ∑ unit ∈ sample with cellOf unit = cell,
          cellRadius cell ^ 2) =
        ∑ cell ∈ cover,
          ((sample.filter (fun unit => cellOf unit = cell)).card : Real) *
            cellRadius cell ^ 2 := by
    refine Finset.sum_congr rfl ?_
    intro cell _hcell
    simp [Finset.sum_const, nsmul_eq_mul]
  exact le_trans hsum_pointwise (le_of_eq (hfiber.trans hconst))

/--
Eventual finite catchment-cover radius-square bound.
-/
theorem eventually_unweighted_radius_square_sum_le_catchment_cover_sum
    {l : Filter Index} {Cell : Type*} [DecidableEq Cell]
    (sample : Index -> Finset Unit) (cover : Index -> Finset Cell)
    (cellOf : Index -> Unit -> Cell)
    (radius : Index -> Unit -> Real)
    (cellRadius : Index -> Cell -> Real)
    (hcell_mem :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          cellOf index focal ∈ cover index)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hcellRadius_nonneg :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover index ->
          0 ≤ cellRadius index cell)
    (hradius_le_cell :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤ cellRadius index (cellOf index focal)) :
    ∀ᶠ index in l,
      (∑ focal ∈ sample index, radius index focal ^ 2) ≤
        ∑ cell ∈ cover index,
          (((sample index).filter
            (fun focal => cellOf index focal = cell)).card : Real) *
            cellRadius index cell ^ 2 := by
  filter_upwards [hcell_mem, hradius_nonneg, hcellRadius_nonneg,
    hradius_le_cell] with index hcell_mem_index hradius_nonneg_index
      hcellRadius_nonneg_index hradius_le_cell_index
  exact
    unweighted_radius_square_sum_le_catchment_cover_sum
      (sample index) (cover index) (cellOf index) (radius index)
      (cellRadius index) hcell_mem_index hradius_nonneg_index
      hcellRadius_nonneg_index hradius_le_cell_index

/--
Finite catchment-cover route into the second-moment radius-rate package used by
the average-radius bias bridge.  The remaining source-specific input is the
normalization bound on the catchment count weighted cell-radius-square sum.
-/
theorem second_moment_radius_rate_package_of_eventually_catchment_cover_square_sum_bound
    {l : Filter Index} {Cell : Type*} [DecidableEq Cell]
    (sample : Index -> Finset Unit) (cover : Index -> Finset Cell)
    (cellOf : Index -> Unit -> Cell)
    (focalWeight radius : Index -> Unit -> Real)
    (cellRadius : Index -> Cell -> Real)
    (scale weightCap denominatorLower radiusRate : Index -> Real)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hweight_le :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          focalWeight index focal ≤ weightCap index)
    (hweightCap_nonneg : ∀ᶠ index in l, 0 ≤ weightCap index)
    (hcell_mem :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          cellOf index focal ∈ cover index)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hcellRadius_nonneg :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cover index ->
          0 ≤ cellRadius index cell)
    (hradius_le_cell :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          radius index focal ≤ cellRadius index (cellOf index focal))
    (hden_lower :
      ∀ᶠ index in l,
        denominatorLower index ≤
          weightedDenominator (sample index) (focalWeight index))
    (hnormalized_cover_bound :
      ∀ᶠ index in l,
        weightCap index *
          (∑ cell ∈ cover index,
            (((sample index).filter
              (fun focal => cellOf index focal = cell)).card : Real) *
              cellRadius index cell ^ 2) ≤
          denominatorLower index * radiusRate index ^ 2)
    (hradiusRate_nonneg : ∀ᶠ index in l, 0 ≤ radiusRate index)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    (∀ᶠ index in l,
      ∀ focal, focal ∈ sample index ->
        0 ≤ radius index focal) ∧
    (∀ᶠ index in l,
      weightedSum (sample index) (focalWeight index)
        (fun focal => radius index focal ^ 2) /
      weightedDenominator (sample index) (focalWeight index) ≤
        radiusRate index ^ 2) ∧
    (∀ᶠ index in l, 0 ≤ radiusRate index) ∧
    Tendsto (fun index => scale index * radiusRate index) l (nhds 0) := by
  let rawSquareBound : Index -> Real := fun index =>
    ∑ cell ∈ cover index,
      (((sample index).filter
        (fun focal => cellOf index focal = cell)).card : Real) *
        cellRadius index cell ^ 2
  have hraw_sum_le :
      ∀ᶠ index in l,
        (∑ focal ∈ sample index, radius index focal ^ 2) ≤
          rawSquareBound index := by
    simpa [rawSquareBound] using
      eventually_unweighted_radius_square_sum_le_catchment_cover_sum
        (l := l) sample cover cellOf radius cellRadius hcell_mem
        hradius_nonneg hcellRadius_nonneg hradius_le_cell
  have hnormalized_raw_bound :
      ∀ᶠ index in l,
        weightCap index * rawSquareBound index ≤
          denominatorLower index * radiusRate index ^ 2 := by
    simpa [rawSquareBound] using hnormalized_cover_bound
  exact
    second_moment_radius_rate_package_of_eventually_weight_cap_and_raw_square_sum_le
      (l := l) sample focalWeight radius scale weightCap rawSquareBound
      denominatorLower radiusRate hden_pos hweight_le hweightCap_nonneg
      hraw_sum_le hden_lower hnormalized_raw_bound hradius_nonneg
      hradiusRate_nonneg hscaled_radiusRate_tendsto

/--
Deterministic radius-rate reducer for Chen-Han style two-dimensional radius
arguments.  An eventual weighted second-moment radius bound and the scale-rate
condition imply that the scaled weighted average Lipschitz radius tends to zero.
-/
theorem tendsto_scaled_weighted_average_radius_zero_of_second_moment_rate
    {l : Filter Index}
    (sample : Index -> Finset Unit)
    (focalWeight radius : Index -> Unit -> Real)
    (scale radiusRate : Index -> Real)
    (lipschitzConstant : Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hden_pos :
      ∀ᶠ index in l,
        0 < weightedDenominator (sample index) (focalWeight index))
    (hfocalWeight_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ focalWeight index focal)
    (hradius_nonneg :
      ∀ᶠ index in l,
        ∀ focal, focal ∈ sample index ->
          0 ≤ radius index focal)
    (hsecond_moment_bound :
      ∀ᶠ index in l,
        weightedSum (sample index) (focalWeight index)
          (fun focal => radius index focal ^ 2) /
        weightedDenominator (sample index) (focalWeight index) ≤
          radiusRate index ^ 2)
    (hradiusRate_nonneg : ∀ᶠ index in l, 0 ≤ radiusRate index)
    (hlipschitz_nonneg : 0 ≤ lipschitzConstant)
    (hscaled_radiusRate_tendsto :
      Tendsto (fun index => scale index * radiusRate index) l (nhds 0)) :
    Tendsto (fun index => scale index *
      (weightedSum (sample index) (focalWeight index)
        (fun focal => lipschitzConstant * radius index focal) /
      weightedDenominator (sample index) (focalWeight index))) l (nhds 0) := by
  have hscaled_bound_tendsto :
      Tendsto (fun index => scale index *
        (lipschitzConstant * radiusRate index)) l (nhds 0) := by
    have hconst : Tendsto (fun _index : Index => lipschitzConstant) l
        (nhds lipschitzConstant) := tendsto_const_nhds
    have hprod := hconst.mul hscaled_radiusRate_tendsto
    simpa [mul_assoc, mul_left_comm, mul_comm] using hprod
  have hbound :
      ∀ᶠ index in l,
        |weightedSum (sample index) (focalWeight index)
            (fun focal => lipschitzConstant * radius index focal) /
          weightedDenominator (sample index) (focalWeight index)| ≤
          lipschitzConstant * radiusRate index := by
    filter_upwards [hden_pos, hfocalWeight_nonneg, hradius_nonneg,
      hsecond_moment_bound, hradiusRate_nonneg] with index hden_pos_index
      hfocalWeight_nonneg_index hradius_nonneg_index hsecond_index
      hradiusRate_nonneg_index
    have havg_radius_le :
        weightedSum (sample index) (focalWeight index) (radius index) /
          weightedDenominator (sample index) (focalWeight index) ≤
            radiusRate index :=
      weighted_average_radius_le_second_moment_rate
        (sample index) (focalWeight index) (radius index) (radiusRate index)
        hden_pos_index hfocalWeight_nonneg_index hsecond_index
        hradiusRate_nonneg_index
    have hscaled_average_eq :
        weightedSum (sample index) (focalWeight index)
            (fun focal => lipschitzConstant * radius index focal) /
          weightedDenominator (sample index) (focalWeight index) =
        lipschitzConstant *
          (weightedSum (sample index) (focalWeight index) (radius index) /
            weightedDenominator (sample index) (focalWeight index)) := by
      rw [weightedSum_smul_const]
      ring
    have hvalue_nonneg :
        0 ≤ weightedSum (sample index) (focalWeight index)
            (fun focal => lipschitzConstant * radius index focal) /
          weightedDenominator (sample index) (focalWeight index) := by
      exact div_nonneg
        (weightedSum_nonneg (sample index) (focalWeight index)
          (fun focal => lipschitzConstant * radius index focal)
          hfocalWeight_nonneg_index
          (fun focal hfocal => mul_nonneg hlipschitz_nonneg
            (hradius_nonneg_index focal hfocal)))
        hden_pos_index.le
    rw [abs_of_nonneg hvalue_nonneg, hscaled_average_eq]
    exact mul_le_mul_of_nonneg_left havg_radius_le hlipschitz_nonneg
  exact tendsto_scaled_zero_of_eventually_abs_le_bound
    scale
    (fun index =>
      weightedSum (sample index) (focalWeight index)
        (fun focal => lipschitzConstant * radius index focal) /
      weightedDenominator (sample index) (focalWeight index))
    (fun index => lipschitzConstant * radiusRate index)
    hscale_nonneg hbound hscaled_bound_tendsto

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
