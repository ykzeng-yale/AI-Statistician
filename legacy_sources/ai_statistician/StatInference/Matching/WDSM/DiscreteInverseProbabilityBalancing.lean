import StatInference.Matching.WDSM.DiscreteScoreMeasurableBalancing

/-!
# Finite inverse-probability score-cell balancing for WDSM

This module proves a deterministic finite analogue of the propensity-route
balancing step.  If a selected sample has, in each score cell, base weighted
mass equal to a cell probability times the target cell mass, then inverse
cell-probability weighting exactly recovers the target score-cell shares.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Base survey weight divided by a score-cell selection probability. -/
noncomputable def inverseCellProbabilityWeight
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (cellProbability : Cell -> Real) (unit : Unit) : Real :=
  baseWeight unit / cellProbability (score unit)

theorem scoreCellMass_inverseCellProbabilityWeight_eq_of_cellMass_eq
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (cellProbability : Cell -> Real) (cell : Cell)
    (hprob : cellProbability cell ≠ 0)
    (hcellMass :
      scoreCellMass selectedSample baseWeight score cell =
        cellProbability cell *
          scoreCellMass targetSample baseWeight score cell) :
    scoreCellMass selectedSample
        (inverseCellProbabilityWeight baseWeight score cellProbability)
        score cell =
      scoreCellMass targetSample baseWeight score cell := by
  unfold scoreCellMass inverseCellProbabilityWeight
  calc
    (∑ unit ∈ selectedSample with score unit = cell,
        baseWeight unit / cellProbability (score unit)) =
        ∑ unit ∈ selectedSample with score unit = cell,
          baseWeight unit / cellProbability cell := by
          exact Finset.sum_congr rfl
            (fun unit hunit => by
              rw [(Finset.mem_filter.mp hunit).2])
    _ = (∑ unit ∈ selectedSample with score unit = cell,
          baseWeight unit) / cellProbability cell := by
          rw [Finset.sum_div]
    _ = scoreCellMass selectedSample baseWeight score cell /
          cellProbability cell := by
          rfl
    _ = scoreCellMass targetSample baseWeight score cell := by
          rw [hcellMass]
          field_simp [hprob]

theorem weightedSampleTotal_inverseCellProbabilityWeight_eq_of_cellMass_eq
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (cellProbability : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hprob : ∀ cell, cell ∈ cells -> cellProbability cell ≠ 0)
    (hcellMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass selectedSample baseWeight score cell =
          cellProbability cell *
            scoreCellMass targetSample baseWeight score cell) :
    weightedSampleTotal selectedSample
        (inverseCellProbabilityWeight baseWeight score cellProbability) =
      weightedSampleTotal targetSample baseWeight := by
  calc
    weightedSampleTotal selectedSample
        (inverseCellProbabilityWeight baseWeight score cellProbability) =
        ∑ cell ∈ cells,
          scoreCellMass selectedSample
            (inverseCellProbabilityWeight baseWeight score cellProbability)
            score cell := by
          exact (sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
            selectedSample cells
            (inverseCellProbabilityWeight baseWeight score cellProbability)
            score hcoverSelected).symm
    _ = ∑ cell ∈ cells, scoreCellMass targetSample baseWeight score cell := by
        exact Finset.sum_congr rfl
          (fun cell hcell =>
            scoreCellMass_inverseCellProbabilityWeight_eq_of_cellMass_eq
              targetSample selectedSample baseWeight score cellProbability
              cell (hprob cell hcell) (hcellMass cell hcell))
    _ = weightedSampleTotal targetSample baseWeight := by
        exact sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
          targetSample cells baseWeight score hcoverTarget

theorem scoreCellShare_inverseCellProbabilityWeight_eq_of_cellMass_eq
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (cellProbability : Cell -> Real) (cell : Cell)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hprob : ∀ cell, cell ∈ cells -> cellProbability cell ≠ 0)
    (hcell : cell ∈ cells)
    (hcellMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass selectedSample baseWeight score cell =
          cellProbability cell *
            scoreCellMass targetSample baseWeight score cell) :
    scoreCellShare selectedSample
        (inverseCellProbabilityWeight baseWeight score cellProbability)
        score cell =
      scoreCellShare targetSample baseWeight score cell := by
  unfold scoreCellShare
  rw [scoreCellMass_inverseCellProbabilityWeight_eq_of_cellMass_eq
    targetSample selectedSample baseWeight score cellProbability cell
    (hprob cell hcell) (hcellMass cell hcell)]
  rw [weightedSampleTotal_inverseCellProbabilityWeight_eq_of_cellMass_eq
    targetSample selectedSample cells baseWeight score cellProbability
    hcoverTarget hcoverSelected hprob hcellMass]

theorem weightedSampleMean_eq_inverseCellProbabilityWeightedMean_of_scoreMeasurable
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (targetOutcome selectedOutcome : Unit -> Real)
    (score : Unit -> Cell) (cellProbability : Cell -> Real)
    (cellValue : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight score cell ≠ 0)
    (hprob : ∀ cell, cell ∈ cells -> cellProbability cell ≠ 0)
    (hcellMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass selectedSample baseWeight score cell =
          cellProbability cell *
            scoreCellMass targetSample baseWeight score cell)
    (hscoreMeasTarget :
      ∀ unit, unit ∈ targetSample ->
        targetOutcome unit = cellValue (score unit))
    (hscoreMeasSelected :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcome unit = cellValue (score unit)) :
    weightedSampleMean targetSample baseWeight targetOutcome =
      weightedSampleMean selectedSample
        (inverseCellProbabilityWeight baseWeight score cellProbability)
        selectedOutcome := by
  let inverseWeight :=
    inverseCellProbabilityWeight baseWeight score cellProbability
  have hmassSelected :
      ∀ cell, cell ∈ cells ->
        scoreCellMass selectedSample inverseWeight score cell ≠ 0 := by
    intro cell hcell
    rw [scoreCellMass_inverseCellProbabilityWeight_eq_of_cellMass_eq
      targetSample selectedSample baseWeight score cellProbability cell
      (hprob cell hcell) (hcellMass cell hcell)]
    exact hmassTarget cell hcell
  have hshare :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample baseWeight score cell =
          scoreCellShare selectedSample inverseWeight score cell := by
    intro cell hcell
    exact (scoreCellShare_inverseCellProbabilityWeight_eq_of_cellMass_eq
      targetSample selectedSample cells baseWeight score cellProbability
      cell hcoverTarget hcoverSelected hprob hcell hcellMass).symm
  exact weightedSampleMean_eq_of_scoreCellShare_eq_and_scoreMeasurable
    targetSample selectedSample cells baseWeight inverseWeight
    targetOutcome selectedOutcome score score cellValue
    hcoverTarget hcoverSelected hmassTarget hmassSelected hshare
    hscoreMeasTarget hscoreMeasSelected

/--
Finite inverse-probability PATE score-cell balancing theorem.

The treated and control selected samples recover the target potential-outcome
means after inverse cell-probability weighting, so their weighted contrast
equals the target finite PATE.
-/
theorem weightedSampleMeanContrast_eq_twoArmInverseProbabilityWeightedMeanContrast
    (targetSample treatedSample controlSample : Finset Unit)
    (cells : Finset Cell)
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome : Unit -> Real)
    (score : Unit -> Cell)
    (treatedProbability controlProbability : Cell -> Real)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverTreated : ∀ unit, unit ∈ treatedSample -> score unit ∈ cells)
    (hcoverControl : ∀ unit, unit ∈ controlSample -> score unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight score cell ≠ 0)
    (htreatedProb :
      ∀ cell, cell ∈ cells -> treatedProbability cell ≠ 0)
    (hcontrolProb :
      ∀ cell, cell ∈ cells -> controlProbability cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass treatedSample baseWeight score cell =
          treatedProbability cell *
            scoreCellMass targetSample baseWeight score cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass controlSample baseWeight score cell =
          controlProbability cell *
            scoreCellMass targetSample baseWeight score cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedCellValue (score unit))
    (hscoreMeasTreated :
      ∀ unit, unit ∈ treatedSample ->
        treatedOutcome unit = treatedCellValue (score unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlCellValue (score unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ controlSample ->
        controlOutcome unit = controlCellValue (score unit)) :
    weightedSampleMeanContrast targetSample baseWeight
        targetOutcomeT targetOutcomeC =
      twoArmWeightedMeanContrast treatedSample controlSample
        (inverseCellProbabilityWeight baseWeight score treatedProbability)
        (inverseCellProbabilityWeight baseWeight score controlProbability)
        treatedOutcome controlOutcome := by
  have htreated :
      weightedSampleMean targetSample baseWeight targetOutcomeT =
        weightedSampleMean treatedSample
          (inverseCellProbabilityWeight baseWeight score treatedProbability)
          treatedOutcome :=
    weightedSampleMean_eq_inverseCellProbabilityWeightedMean_of_scoreMeasurable
      targetSample treatedSample cells baseWeight targetOutcomeT
      treatedOutcome score treatedProbability treatedCellValue
      hcoverTarget hcoverTreated hmassTarget htreatedProb htreatedMass
      hscoreMeasTargetT hscoreMeasTreated
  have hcontrol :
      weightedSampleMean targetSample baseWeight targetOutcomeC =
        weightedSampleMean controlSample
          (inverseCellProbabilityWeight baseWeight score controlProbability)
          controlOutcome :=
    weightedSampleMean_eq_inverseCellProbabilityWeightedMean_of_scoreMeasurable
      targetSample controlSample cells baseWeight targetOutcomeC
      controlOutcome score controlProbability controlCellValue
      hcoverTarget hcoverControl hmassTarget hcontrolProb hcontrolMass
      hscoreMeasTargetC hscoreMeasControl
  unfold weightedSampleMeanContrast twoArmWeightedMeanContrast
  rw [htreated, hcontrol]

/--
Finite inverse-probability PATT score-cell balancing theorem.  The treated
target mean is direct; only the control mean is recovered by inverse
cell-probability weighting.
-/
theorem weightedSampleMeanContrast_eq_pattInverseProbabilityWeightedMeanContrast
    (targetSample controlSample : Finset Unit)
    (cells : Finset Cell)
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome : Unit -> Real)
    (score : Unit -> Cell)
    (controlProbability : Cell -> Real)
    (controlCellValue : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverControl : ∀ unit, unit ∈ controlSample -> score unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight score cell ≠ 0)
    (hcontrolProb :
      ∀ cell, cell ∈ cells -> controlProbability cell ≠ 0)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass controlSample baseWeight score cell =
          controlProbability cell *
            scoreCellMass targetSample baseWeight score cell)
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit = controlCellValue (score unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ controlSample ->
        controlOutcome unit = controlCellValue (score unit)) :
    weightedSampleMeanContrast targetSample baseWeight
        treatedTargetOutcome targetControlOutcome =
      pattWeightedMeanContrast targetSample controlSample baseWeight
        (inverseCellProbabilityWeight baseWeight score controlProbability)
        treatedTargetOutcome controlOutcome := by
  have hcontrol :
      weightedSampleMean targetSample baseWeight targetControlOutcome =
        weightedSampleMean controlSample
          (inverseCellProbabilityWeight baseWeight score controlProbability)
          controlOutcome :=
    weightedSampleMean_eq_inverseCellProbabilityWeightedMean_of_scoreMeasurable
      targetSample controlSample cells baseWeight targetControlOutcome
      controlOutcome score controlProbability controlCellValue
      hcoverTarget hcoverControl hmassTarget hcontrolProb hcontrolMass
      hscoreMeasTargetC hscoreMeasControl
  unfold weightedSampleMeanContrast pattWeightedMeanContrast
  rw [hcontrol]

end WDSM
end Matching
end StatInference
