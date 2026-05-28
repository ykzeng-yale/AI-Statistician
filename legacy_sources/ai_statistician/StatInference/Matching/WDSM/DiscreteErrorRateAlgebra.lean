import StatInference.Matching.WDSM.DiscreteContrastErrorBounds
import StatInference.Matching.WDSM.ScaledSqueezeAlgebra

/-!
# Rate transfer algebra for finite score-cell approximation errors

The finite error-bound modules reduce score-cell approximation to deterministic
radius inequalities.  This module turns those inequalities into real `Tendsto`
statements: if the radii vanish, the candidate aggregate and contrast errors
vanish; if a scaled radius vanishes, the scaled error vanishes.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} [DecidableEq Cell]
variable {l : Filter Index}

theorem tendsto_candidateCellMeanAggregate_error_zero_of_uniform_error
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight outcome : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (candidateMean : Index -> Cell -> Real) (radius : Index -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index ->
        score index unit ∈ cells index)
    (hmass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (sample index) (weight index) (score index) cell ≠ 0)
    (hshare_nonneg :
      ∀ index cell, cell ∈ cells index ->
        0 ≤ scoreCellShare (sample index) (weight index) (score index) cell)
    (hshare_sum :
      ∀ index,
        (∑ cell ∈ cells index,
          scoreCellShare (sample index) (weight index) (score index) cell) =
            1)
    (herror :
      ∀ index cell, cell ∈ cells index ->
        |candidateMean index cell -
          scoreCellMean (sample index) (weight index) (outcome index)
            (score index) cell| ≤ radius index)
    (hradius : Tendsto radius l (nhds 0)) :
    Tendsto
      (fun index =>
        candidateCellMeanAggregate (sample index) (cells index)
          (weight index) (score index) (candidateMean index) -
        weightedSampleMean (sample index) (weight index) (outcome index))
      l (nhds 0) := by
  exact tendsto_zero_of_abs_le_bound
    (fun index =>
      candidateCellMeanAggregate (sample index) (cells index)
        (weight index) (score index) (candidateMean index) -
      weightedSampleMean (sample index) (weight index) (outcome index))
    radius
    (fun index =>
      abs_candidateCellMeanAggregate_sub_weightedSampleMean_le
        (sample index) (cells index) (weight index) (outcome index)
        (score index) (candidateMean index) (radius index)
        (hcover index) (hmass index) (hshare_nonneg index)
        (hshare_sum index) (herror index))
    hradius

theorem tendsto_candidateCellMeanAggregateContrast_error_zero_of_uniform_error
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight outcomeA outcomeB : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (candidateA candidateB : Index -> Cell -> Real)
    (radiusA radiusB : Index -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index ->
        score index unit ∈ cells index)
    (hmass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (sample index) (weight index) (score index) cell ≠ 0)
    (hshare_nonneg :
      ∀ index cell, cell ∈ cells index ->
        0 ≤ scoreCellShare (sample index) (weight index) (score index) cell)
    (hshare_sum :
      ∀ index,
        (∑ cell ∈ cells index,
          scoreCellShare (sample index) (weight index) (score index) cell) =
            1)
    (herrorA :
      ∀ index cell, cell ∈ cells index ->
        |candidateA index cell -
          scoreCellMean (sample index) (weight index) (outcomeA index)
            (score index) cell| ≤ radiusA index)
    (herrorB :
      ∀ index cell, cell ∈ cells index ->
        |candidateB index cell -
          scoreCellMean (sample index) (weight index) (outcomeB index)
            (score index) cell| ≤ radiusB index)
    (hradiusA : Tendsto radiusA l (nhds 0))
    (hradiusB : Tendsto radiusB l (nhds 0)) :
    Tendsto
      (fun index =>
        candidateCellMeanAggregateContrast (sample index) (cells index)
          (weight index) (score index) (candidateA index) (candidateB index) -
        weightedSampleMeanContrast (sample index) (weight index)
          (outcomeA index) (outcomeB index))
      l (nhds 0) := by
  exact tendsto_zero_of_abs_le_bound
    (fun index =>
      candidateCellMeanAggregateContrast (sample index) (cells index)
        (weight index) (score index) (candidateA index) (candidateB index) -
      weightedSampleMeanContrast (sample index) (weight index)
        (outcomeA index) (outcomeB index))
    (fun index => radiusA index + radiusB index)
    (fun index =>
      abs_candidateCellMeanAggregateContrast_sub_weightedSampleMeanContrast_le
        (sample index) (cells index) (weight index) (outcomeA index)
        (outcomeB index) (score index) (candidateA index)
        (candidateB index) (radiusA index) (radiusB index)
        (hcover index) (hmass index) (hshare_nonneg index)
        (hshare_sum index) (herrorA index) (herrorB index))
    (by
      simpa using hradiusA.add hradiusB)

theorem tendsto_candidateCellMeanAggregate_error_zero_of_uniform_error_of_nonneg_weights
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight outcome : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (candidateMean : Index -> Cell -> Real) (radius : Index -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index ->
        score index unit ∈ cells index)
    (hmass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (sample index) (weight index) (score index) cell ≠ 0)
    (htotal_ne :
      ∀ index, weightedSampleTotal (sample index) (weight index) ≠ 0)
    (htotal_nonneg :
      ∀ index, 0 ≤ weightedSampleTotal (sample index) (weight index))
    (hweight_nonneg :
      ∀ index unit, unit ∈ sample index -> 0 ≤ weight index unit)
    (herror :
      ∀ index cell, cell ∈ cells index ->
        |candidateMean index cell -
          scoreCellMean (sample index) (weight index) (outcome index)
            (score index) cell| ≤ radius index)
    (hradius : Tendsto radius l (nhds 0)) :
    Tendsto
      (fun index =>
        candidateCellMeanAggregate (sample index) (cells index)
          (weight index) (score index) (candidateMean index) -
        weightedSampleMean (sample index) (weight index) (outcome index))
      l (nhds 0) := by
  exact tendsto_candidateCellMeanAggregate_error_zero_of_uniform_error
    sample cells weight outcome score candidateMean radius
    hcover hmass
    (fun index cell _ =>
      scoreCellShare_nonneg (sample index) (weight index) (score index)
        cell (htotal_nonneg index)
        (fun unit hunit _ => hweight_nonneg index unit hunit))
    (fun index =>
      sum_scoreCellShare_eq_one_of_mapsTo (sample index) (cells index)
        (weight index) (score index) (hcover index) (htotal_ne index))
    herror hradius

theorem tendsto_candidateCellMeanAggregateContrast_error_zero_of_uniform_error_of_nonneg_weights
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight outcomeA outcomeB : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (candidateA candidateB : Index -> Cell -> Real)
    (radiusA radiusB : Index -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index ->
        score index unit ∈ cells index)
    (hmass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (sample index) (weight index) (score index) cell ≠ 0)
    (htotal_ne :
      ∀ index, weightedSampleTotal (sample index) (weight index) ≠ 0)
    (htotal_nonneg :
      ∀ index, 0 ≤ weightedSampleTotal (sample index) (weight index))
    (hweight_nonneg :
      ∀ index unit, unit ∈ sample index -> 0 ≤ weight index unit)
    (herrorA :
      ∀ index cell, cell ∈ cells index ->
        |candidateA index cell -
          scoreCellMean (sample index) (weight index) (outcomeA index)
            (score index) cell| ≤ radiusA index)
    (herrorB :
      ∀ index cell, cell ∈ cells index ->
        |candidateB index cell -
          scoreCellMean (sample index) (weight index) (outcomeB index)
            (score index) cell| ≤ radiusB index)
    (hradiusA : Tendsto radiusA l (nhds 0))
    (hradiusB : Tendsto radiusB l (nhds 0)) :
    Tendsto
      (fun index =>
        candidateCellMeanAggregateContrast (sample index) (cells index)
          (weight index) (score index) (candidateA index) (candidateB index) -
        weightedSampleMeanContrast (sample index) (weight index)
          (outcomeA index) (outcomeB index))
      l (nhds 0) := by
  exact tendsto_candidateCellMeanAggregateContrast_error_zero_of_uniform_error
    sample cells weight outcomeA outcomeB score candidateA candidateB
    radiusA radiusB hcover hmass
    (fun index cell _ =>
      scoreCellShare_nonneg (sample index) (weight index) (score index)
        cell (htotal_nonneg index)
        (fun unit hunit _ => hweight_nonneg index unit hunit))
    (fun index =>
      sum_scoreCellShare_eq_one_of_mapsTo (sample index) (cells index)
        (weight index) (score index) (hcover index) (htotal_ne index))
    herrorA herrorB hradiusA hradiusB

theorem tendsto_scaled_candidateCellMeanAggregateContrast_error_zero_of_uniform_error
    (scale : Index -> Real)
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight outcomeA outcomeB : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (candidateA candidateB : Index -> Cell -> Real)
    (radiusA radiusB : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcover :
      ∀ index unit, unit ∈ sample index ->
        score index unit ∈ cells index)
    (hmass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (sample index) (weight index) (score index) cell ≠ 0)
    (hshare_nonneg :
      ∀ index cell, cell ∈ cells index ->
        0 ≤ scoreCellShare (sample index) (weight index) (score index) cell)
    (hshare_sum :
      ∀ index,
        (∑ cell ∈ cells index,
          scoreCellShare (sample index) (weight index) (score index) cell) =
            1)
    (herrorA :
      ∀ index cell, cell ∈ cells index ->
        |candidateA index cell -
          scoreCellMean (sample index) (weight index) (outcomeA index)
            (score index) cell| ≤ radiusA index)
    (herrorB :
      ∀ index cell, cell ∈ cells index ->
        |candidateB index cell -
          scoreCellMean (sample index) (weight index) (outcomeB index)
            (score index) cell| ≤ radiusB index)
    (hscaled_radius :
      Tendsto (fun index => scale index * (radiusA index + radiusB index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (candidateCellMeanAggregateContrast (sample index) (cells index)
            (weight index) (score index) (candidateA index)
            (candidateB index) -
          weightedSampleMeanContrast (sample index) (weight index)
            (outcomeA index) (outcomeB index)))
      l (nhds 0) := by
  exact tendsto_scaled_zero_of_abs_le_bound
    scale
    (fun index =>
      candidateCellMeanAggregateContrast (sample index) (cells index)
        (weight index) (score index) (candidateA index) (candidateB index) -
      weightedSampleMeanContrast (sample index) (weight index)
        (outcomeA index) (outcomeB index))
    (fun index => radiusA index + radiusB index)
    hscale_nonneg
    (fun index =>
      abs_candidateCellMeanAggregateContrast_sub_weightedSampleMeanContrast_le
        (sample index) (cells index) (weight index) (outcomeA index)
        (outcomeB index) (score index) (candidateA index)
        (candidateB index) (radiusA index) (radiusB index)
        (hcover index) (hmass index) (hshare_nonneg index)
        (hshare_sum index) (herrorA index) (herrorB index))
    hscaled_radius

theorem tendsto_scaled_candidateCellMeanAggregateContrast_error_zero_of_uniform_error_of_nonneg_weights
    (scale : Index -> Real)
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight outcomeA outcomeB : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (candidateA candidateB : Index -> Cell -> Real)
    (radiusA radiusB : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcover :
      ∀ index unit, unit ∈ sample index ->
        score index unit ∈ cells index)
    (hmass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (sample index) (weight index) (score index) cell ≠ 0)
    (htotal_ne :
      ∀ index, weightedSampleTotal (sample index) (weight index) ≠ 0)
    (htotal_nonneg :
      ∀ index, 0 ≤ weightedSampleTotal (sample index) (weight index))
    (hweight_nonneg :
      ∀ index unit, unit ∈ sample index -> 0 ≤ weight index unit)
    (herrorA :
      ∀ index cell, cell ∈ cells index ->
        |candidateA index cell -
          scoreCellMean (sample index) (weight index) (outcomeA index)
            (score index) cell| ≤ radiusA index)
    (herrorB :
      ∀ index cell, cell ∈ cells index ->
        |candidateB index cell -
          scoreCellMean (sample index) (weight index) (outcomeB index)
            (score index) cell| ≤ radiusB index)
    (hscaled_radius :
      Tendsto (fun index => scale index * (radiusA index + radiusB index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (candidateCellMeanAggregateContrast (sample index) (cells index)
            (weight index) (score index) (candidateA index)
            (candidateB index) -
          weightedSampleMeanContrast (sample index) (weight index)
            (outcomeA index) (outcomeB index)))
      l (nhds 0) := by
  exact tendsto_scaled_candidateCellMeanAggregateContrast_error_zero_of_uniform_error
    scale sample cells weight outcomeA outcomeB score candidateA candidateB
    radiusA radiusB hscale_nonneg hcover hmass
    (fun index cell _ =>
      scoreCellShare_nonneg (sample index) (weight index) (score index)
        cell (htotal_nonneg index)
        (fun unit hunit _ => hweight_nonneg index unit hunit))
    (fun index =>
      sum_scoreCellShare_eq_one_of_mapsTo (sample index) (cells index)
        (weight index) (score index) (hcover index) (htotal_ne index))
    herrorA herrorB hscaled_radius

theorem tendsto_candidateCellMeanAggregateContrast_error_zero_of_eventually_uniform_error
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight outcomeA outcomeB : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (candidateA candidateB : Index -> Cell -> Real)
    (radiusA radiusB : Index -> Real)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells index)
    (hmass :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (sample index) (weight index) (score index) cell ≠ 0)
    (hshare_nonneg :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          0 ≤ scoreCellShare (sample index) (weight index) (score index) cell)
    (hshare_sum :
      ∀ᶠ index in l,
        (∑ cell ∈ cells index,
          scoreCellShare (sample index) (weight index) (score index) cell) =
            1)
    (herrorA :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |candidateA index cell -
            scoreCellMean (sample index) (weight index) (outcomeA index)
              (score index) cell| ≤ radiusA index)
    (herrorB :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |candidateB index cell -
            scoreCellMean (sample index) (weight index) (outcomeB index)
              (score index) cell| ≤ radiusB index)
    (hradiusA : Tendsto radiusA l (nhds 0))
    (hradiusB : Tendsto radiusB l (nhds 0)) :
    Tendsto
      (fun index =>
        candidateCellMeanAggregateContrast (sample index) (cells index)
          (weight index) (score index) (candidateA index) (candidateB index) -
        weightedSampleMeanContrast (sample index) (weight index)
          (outcomeA index) (outcomeB index))
      l (nhds 0) := by
  have hbound :
      ∀ᶠ index in l,
        |candidateCellMeanAggregateContrast (sample index) (cells index)
            (weight index) (score index) (candidateA index) (candidateB index) -
          weightedSampleMeanContrast (sample index) (weight index)
            (outcomeA index) (outcomeB index)| ≤
          radiusA index + radiusB index := by
    filter_upwards [hcover, hmass, hshare_nonneg, hshare_sum, herrorA,
      herrorB] with index hcover_index hmass_index hshare_nonneg_index
      hshare_sum_index herrorA_index herrorB_index
    exact
      abs_candidateCellMeanAggregateContrast_sub_weightedSampleMeanContrast_le
        (sample index) (cells index) (weight index) (outcomeA index)
        (outcomeB index) (score index) (candidateA index)
        (candidateB index) (radiusA index) (radiusB index)
        hcover_index hmass_index hshare_nonneg_index hshare_sum_index
        herrorA_index herrorB_index
  exact tendsto_zero_of_eventually_abs_le_bound
    (fun index =>
      candidateCellMeanAggregateContrast (sample index) (cells index)
        (weight index) (score index) (candidateA index) (candidateB index) -
      weightedSampleMeanContrast (sample index) (weight index)
        (outcomeA index) (outcomeB index))
    (fun index => radiusA index + radiusB index)
    hbound
    (by
      simpa using hradiusA.add hradiusB)

theorem tendsto_scaled_candidateCellMeanAggregateContrast_error_zero_of_eventually_uniform_error
    (scale : Index -> Real)
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight outcomeA outcomeB : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (candidateA candidateB : Index -> Cell -> Real)
    (radiusA radiusB : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells index)
    (hmass :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (sample index) (weight index) (score index) cell ≠ 0)
    (hshare_nonneg :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          0 ≤ scoreCellShare (sample index) (weight index) (score index) cell)
    (hshare_sum :
      ∀ᶠ index in l,
        (∑ cell ∈ cells index,
          scoreCellShare (sample index) (weight index) (score index) cell) =
            1)
    (herrorA :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |candidateA index cell -
            scoreCellMean (sample index) (weight index) (outcomeA index)
              (score index) cell| ≤ radiusA index)
    (herrorB :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |candidateB index cell -
            scoreCellMean (sample index) (weight index) (outcomeB index)
              (score index) cell| ≤ radiusB index)
    (hscaled_radius :
      Tendsto (fun index => scale index * (radiusA index + radiusB index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (candidateCellMeanAggregateContrast (sample index) (cells index)
            (weight index) (score index) (candidateA index)
            (candidateB index) -
          weightedSampleMeanContrast (sample index) (weight index)
            (outcomeA index) (outcomeB index)))
      l (nhds 0) := by
  have hbound :
      ∀ᶠ index in l,
        |candidateCellMeanAggregateContrast (sample index) (cells index)
            (weight index) (score index) (candidateA index) (candidateB index) -
          weightedSampleMeanContrast (sample index) (weight index)
            (outcomeA index) (outcomeB index)| ≤
          radiusA index + radiusB index := by
    filter_upwards [hcover, hmass, hshare_nonneg, hshare_sum, herrorA,
      herrorB] with index hcover_index hmass_index hshare_nonneg_index
      hshare_sum_index herrorA_index herrorB_index
    exact
      abs_candidateCellMeanAggregateContrast_sub_weightedSampleMeanContrast_le
        (sample index) (cells index) (weight index) (outcomeA index)
        (outcomeB index) (score index) (candidateA index)
        (candidateB index) (radiusA index) (radiusB index)
        hcover_index hmass_index hshare_nonneg_index hshare_sum_index
        herrorA_index herrorB_index
  exact tendsto_scaled_zero_of_eventually_abs_le_bound
    scale
    (fun index =>
      candidateCellMeanAggregateContrast (sample index) (cells index)
        (weight index) (score index) (candidateA index) (candidateB index) -
      weightedSampleMeanContrast (sample index) (weight index)
        (outcomeA index) (outcomeB index))
    (fun index => radiusA index + radiusB index)
    hscale_nonneg
    hbound
    hscaled_radius

end WDSM
end Matching
end StatInference
