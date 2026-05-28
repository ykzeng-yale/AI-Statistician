import StatInference.Matching.WDSM.DiscreteCellErrorBounds

/-!
# Finite score-cell contrast approximation error bounds for WDSM

This module lifts the one-mean approximation bounds to two-outcome contrasts.
It proves that if two candidate score-cell mean functions are uniformly close
to the corresponding finite score-cell means, then their candidate contrast is
close to the survey-weighted sample contrast, with the two radii adding.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

theorem abs_sub_contrast_le_add
    (candidateA candidateB trueA trueB radiusA radiusB : Real)
    (hA : |candidateA - trueA| ≤ radiusA)
    (hB : |candidateB - trueB| ≤ radiusB) :
    |(candidateA - candidateB) - (trueA - trueB)| ≤ radiusA + radiusB := by
  calc
    |(candidateA - candidateB) - (trueA - trueB)| =
        |(candidateA - trueA) + -(candidateB - trueB)| := by
          congr 1
          ring
    _ ≤ |candidateA - trueA| + |-(candidateB - trueB)| := by
        exact abs_add_le (candidateA - trueA) (-(candidateB - trueB))
    _ = |candidateA - trueA| + |candidateB - trueB| := by
        rw [abs_neg]
    _ ≤ radiusA + radiusB := by
        exact add_le_add hA hB

theorem abs_candidateCellMeanAggregateContrast_sub_weightedSampleMeanContrast_le
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell)
    (candidateA candidateB : Cell -> Real) (radiusA radiusB : Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells ->
        0 ≤ scoreCellShare sample weight score cell)
    (hshare_sum :
      (∑ cell ∈ cells, scoreCellShare sample weight score cell) = 1)
    (herrorA :
      ∀ cell, cell ∈ cells ->
        |candidateA cell -
          scoreCellMean sample weight outcomeA score cell| ≤ radiusA)
    (herrorB :
      ∀ cell, cell ∈ cells ->
        |candidateB cell -
          scoreCellMean sample weight outcomeB score cell| ≤ radiusB) :
    |candidateCellMeanAggregateContrast sample cells weight score
        candidateA candidateB -
        weightedSampleMeanContrast sample weight outcomeA outcomeB| ≤
      radiusA + radiusB := by
  unfold candidateCellMeanAggregateContrast weightedSampleMeanContrast
  exact abs_sub_contrast_le_add
    (candidateCellMeanAggregate sample cells weight score candidateA)
    (candidateCellMeanAggregate sample cells weight score candidateB)
    (weightedSampleMean sample weight outcomeA)
    (weightedSampleMean sample weight outcomeB)
    radiusA radiusB
    (abs_candidateCellMeanAggregate_sub_weightedSampleMean_le
      sample cells weight outcomeA score candidateA radiusA hcover hmass
      hshare_nonneg hshare_sum herrorA)
    (abs_candidateCellMeanAggregate_sub_weightedSampleMean_le
      sample cells weight outcomeB score candidateB radiusB hcover hmass
      hshare_nonneg hshare_sum herrorB)

theorem abs_candidateCellMeanAggregateContrast_sub_weightedSampleMeanContrast_le_of_nonneg_weights
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell)
    (candidateA candidateB : Cell -> Real) (radiusA radiusB : Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (htotal_ne : weightedSampleTotal sample weight ≠ 0)
    (htotal_nonneg : 0 ≤ weightedSampleTotal sample weight)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (herrorA :
      ∀ cell, cell ∈ cells ->
        |candidateA cell -
          scoreCellMean sample weight outcomeA score cell| ≤ radiusA)
    (herrorB :
      ∀ cell, cell ∈ cells ->
        |candidateB cell -
          scoreCellMean sample weight outcomeB score cell| ≤ radiusB) :
    |candidateCellMeanAggregateContrast sample cells weight score
        candidateA candidateB -
        weightedSampleMeanContrast sample weight outcomeA outcomeB| ≤
      radiusA + radiusB := by
  exact abs_candidateCellMeanAggregateContrast_sub_weightedSampleMeanContrast_le
    sample cells weight outcomeA outcomeB score candidateA candidateB
    radiusA radiusB hcover hmass
    (fun cell _ =>
      scoreCellShare_nonneg sample weight score cell htotal_nonneg
        (fun unit hunit _ => hweight_nonneg unit hunit))
    (sum_scoreCellShare_eq_one_of_mapsTo sample cells weight score
      hcover htotal_ne)
    herrorA herrorB

end WDSM
end Matching
end StatInference
