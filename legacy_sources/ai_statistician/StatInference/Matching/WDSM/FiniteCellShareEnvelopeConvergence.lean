import StatInference.Matching.WDSM.FiniteCellMassConvergence
import StatInference.Matching.WDSM.FiniteCellMassEnvelopeBridge
import StatInference.Matching.WDSM.FiniteCellShareConvergence

/-!
# Finite score-cell share convergence from mass envelopes

This module composes the shrinking mass-envelope route with the finite
score-cell share convergence layer.  It is the deterministic adapter needed
when concrete survey LLNs provide eventual absolute cell-mass errors rather
than `Tendsto` statements directly.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index UnitA UnitB Cell : Type*} {l : Filter Index}
  [DecidableEq Cell]

/--
Total weighted-mass convergence follows from fixed partition coverage and
shrinking cellwise mass envelopes.
-/
theorem tendsto_weightedSampleTotal_of_cell_mass_envelope
    (cells : Finset Cell)
    (sample : Index -> Finset UnitA)
    (weight : Index -> UnitA -> Real)
    (score : Index -> UnitA -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hbound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sample index) (weight index)
              (score index) cell - massLimit cell| ≤
            cellScale cell * envelope index)
    (henvelope :
      Tendsto envelope l (nhds 0)) :
    Tendsto
      (fun index => weightedSampleTotal (sample index) (weight index))
      l (nhds (∑ cell ∈ cells, massLimit cell)) :=
  tendsto_weightedSampleTotal_of_cell_mass
    (l := l) cells sample weight score massLimit hcover
    (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sample weight score massLimit cellScale envelope
      hbound henvelope)

/--
Total weighted-mass convergence follows from eventually valid fixed-partition
coverage and shrinking cellwise mass envelopes.
-/
theorem tendsto_weightedSampleTotal_of_eventually_cell_mass_envelope
    (cells : Finset Cell)
    (sample : Index -> Finset UnitA)
    (weight : Index -> UnitA -> Real)
    (score : Index -> UnitA -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hbound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sample index) (weight index)
              (score index) cell - massLimit cell| ≤
            cellScale cell * envelope index)
    (henvelope :
      Tendsto envelope l (nhds 0)) :
    Tendsto
      (fun index => weightedSampleTotal (sample index) (weight index))
      l (nhds (∑ cell ∈ cells, massLimit cell)) := by
  have hsum :
      Tendsto
        (fun index =>
          ∑ cell ∈ cells,
            scoreCellMass (sample index) (weight index)
              (score index) cell)
        l (nhds (∑ cell ∈ cells, massLimit cell)) :=
    tendsto_sum_cell_values cells
      (fun index cell =>
        scoreCellMass (sample index) (weight index)
          (score index) cell)
      massLimit
      (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
        (l := l) cells sample weight score massLimit cellScale envelope
        hbound henvelope)
  have heq :
      (fun index => weightedSampleTotal (sample index) (weight index)) =ᶠ[l]
      (fun index =>
        ∑ cell ∈ cells,
          scoreCellMass (sample index) (weight index)
            (score index) cell) := by
    filter_upwards [hcover] with index hcoverIndex
    exact (sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
      (sample index) cells (weight index) (score index) hcoverIndex).symm
  exact hsum.congr' heq.symm

/--
L1 convergence of fixed finite score-cell shares follows from fixed partition
coverage and shrinking mass envelopes for both samples.
-/
theorem tendsto_l1ScoreCellShareDistance_zero_of_cell_mass_envelopes
    (cells : Finset Cell)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (massLimit cellScaleA cellScaleB : Cell -> Real)
    (envelopeA envelopeB : Index -> Real)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index -> scoreA index unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index -> scoreB index unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) :=
  tendsto_l1ScoreCellShareDistance_zero_of_cell_mass
    (l := l) cells sampleA sampleB weightA weightB scoreA scoreB
    massLimit hcoverA hcoverB
    (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sampleA weightA scoreA massLimit cellScaleA envelopeA
      hboundA henvelopeA)
    (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sampleB weightB scoreB massLimit cellScaleB envelopeB
      hboundB henvelopeB)
    htotalLimit

/--
L1 convergence of fixed finite score-cell shares follows from eventually valid
fixed partition coverage and shrinking mass envelopes for both samples.
-/
theorem tendsto_l1ScoreCellShareDistance_zero_of_eventually_cell_mass_envelopes
    (cells : Finset Cell)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (massLimit cellScaleA cellScaleB : Cell -> Real)
    (envelopeA envelopeB : Index -> Real)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index -> scoreA index unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index -> scoreB index unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) :=
  tendsto_l1ScoreCellShareDistance_zero_of_cell_mass_total
    (l := l) cells sampleA sampleB weightA weightB scoreA scoreB
    massLimit (∑ cell ∈ cells, massLimit cell)
    (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sampleA weightA scoreA massLimit cellScaleA envelopeA
      hboundA henvelopeA)
    (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sampleB weightB scoreB massLimit cellScaleB envelopeB
      hboundB henvelopeB)
    (tendsto_weightedSampleTotal_of_eventually_cell_mass_envelope
      (l := l) cells sampleA weightA scoreA massLimit cellScaleA envelopeA
      hcoverA hboundA henvelopeA)
    (tendsto_weightedSampleTotal_of_eventually_cell_mass_envelope
      (l := l) cells sampleB weightB scoreB massLimit cellScaleB envelopeB
      hcoverB hboundB henvelopeB)
    htotalLimit

/--
Scaled total-mass differences vanish when fixed-partition coverage holds
eventually and scaled cell-mass differences have a shrinking envelope.
-/
theorem tendsto_scaled_weightedSampleTotal_sub_zero_of_eventually_cell_mass_envelope
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (scaledCellScale : Cell -> Real)
    (scaledEnvelope : Index -> Real)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index -> scoreA index unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index -> scoreB index unit ∈ cells)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleTotal (sampleA index) (weightA index) -
            weightedSampleTotal (sampleB index) (weightB index)))
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index =>
          ∑ cell ∈ cells,
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell))
        l (nhds 0) :=
    tendsto_sum_cell_values_zero cells
      (fun index cell =>
        scale index *
          (scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell -
            scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell))
      (fun cell hcell =>
        tendsto_zero_of_eventually_abs_le_bound
          (fun index =>
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell))
          (fun index => scaledCellScale cell * scaledEnvelope index)
          (hscaledBound cell hcell)
          (by
            simpa using
              ((tendsto_const_nhds :
                Tendsto (fun _index : Index => scaledCellScale cell) l
                  (nhds (scaledCellScale cell))).mul hscaledEnvelope)))
  have heq :
      (fun index =>
        scale index *
          (weightedSampleTotal (sampleA index) (weightA index) -
            weightedSampleTotal (sampleB index) (weightB index))) =ᶠ[l]
      (fun index =>
        ∑ cell ∈ cells,
          scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell)) := by
    filter_upwards [hcoverA, hcoverB] with index hcoverAIndex hcoverBIndex
    have hA :=
      sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
        (sampleA index) cells (weightA index) (scoreA index)
        hcoverAIndex
    have hB :=
      sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
        (sampleB index) cells (weightB index) (scoreB index)
        hcoverBIndex
    calc
      scale index *
          (weightedSampleTotal (sampleA index) (weightA index) -
            weightedSampleTotal (sampleB index) (weightB index))
          =
          scale index *
            ((∑ cell ∈ cells,
                scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell) -
              (∑ cell ∈ cells,
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell)) := by
            rw [← hA, ← hB]
      _ =
          ∑ cell ∈ cells,
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell) := by
            rw [← Finset.sum_sub_distrib, Finset.mul_sum]
  exact hsum.congr' heq.symm

/--
Scaled L1 convergence of fixed finite score-cell shares follows from shrinking
mass envelopes for both samples and a shrinking envelope for the scaled
cell-mass differences.
-/
theorem tendsto_scaled_l1ScoreCellShareDistance_zero_of_cell_mass_envelopes
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (massLimit cellScaleA cellScaleB scaledCellScale : Cell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index -> scoreA index unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index -> scoreB index unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) :=
  tendsto_scaled_l1ScoreCellShareDistance_zero_of_cell_mass
    (l := l) cells scale sampleA sampleB weightA weightB scoreA scoreB
    massLimit hscale_nonneg hcoverA hcoverB
    (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sampleA weightA scoreA massLimit cellScaleA envelopeA
      hboundA henvelopeA)
    (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sampleB weightB scoreB massLimit cellScaleB envelopeB
      hboundB henvelopeB)
    (fun cell hcell =>
      tendsto_zero_of_eventually_abs_le_bound
        (fun index =>
          scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell))
        (fun index => scaledCellScale cell * scaledEnvelope index)
        (hscaledBound cell hcell)
        (by
          simpa using
            ((tendsto_const_nhds :
              Tendsto (fun _index : Index => scaledCellScale cell) l
                (nhds (scaledCellScale cell))).mul hscaledEnvelope)))
    htotalLimit

/--
Scaled L1 convergence of fixed finite score-cell shares follows from
eventually valid fixed partition coverage, eventual scale nonnegativity,
shrinking mass envelopes, and a shrinking envelope for scaled cell-mass
differences.
-/
theorem tendsto_scaled_l1ScoreCellShareDistance_zero_of_eventually_cell_mass_envelopes
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (massLimit cellScaleA cellScaleB scaledCellScale : Cell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index -> scoreA index unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index -> scoreB index unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (weightA index) (weightB index) (scoreA index) (scoreB index))
      l (nhds 0) := by
  have hmassA :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell)
          l (nhds (massLimit cell)) :=
    cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sampleA weightA scoreA massLimit cellScaleA envelopeA
      hboundA henvelopeA
  have hmassB :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell)
          l (nhds (massLimit cell)) :=
    cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sampleB weightB scoreB massLimit cellScaleB envelopeB
      hboundB henvelopeB
  have htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds (∑ cell ∈ cells, massLimit cell)) :=
    tendsto_weightedSampleTotal_of_eventually_cell_mass_envelope
      (l := l) cells sampleA weightA scoreA massLimit cellScaleA envelopeA
      hcoverA hboundA henvelopeA
  have htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds (∑ cell ∈ cells, massLimit cell)) :=
    tendsto_weightedSampleTotal_of_eventually_cell_mass_envelope
      (l := l) cells sampleB weightB scoreB massLimit cellScaleB envelopeB
      hcoverB hboundB henvelopeB
  have hscaledMass :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellMass (sampleA index) (weightA index)
                  (scoreA index) cell -
                scoreCellMass (sampleB index) (weightB index)
                  (scoreB index) cell))
          l (nhds 0) :=
    fun cell hcell =>
      tendsto_zero_of_eventually_abs_le_bound
        (fun index =>
          scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell))
        (fun index => scaledCellScale cell * scaledEnvelope index)
        (hscaledBound cell hcell)
        (by
          simpa using
            ((tendsto_const_nhds :
              Tendsto (fun _index : Index => scaledCellScale cell) l
                (nhds (scaledCellScale cell))).mul hscaledEnvelope))
  have hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleTotal (sampleA index) (weightA index) -
              weightedSampleTotal (sampleB index) (weightB index)))
        l (nhds 0) :=
    tendsto_scaled_weightedSampleTotal_sub_zero_of_eventually_cell_mass_envelope
      (l := l) cells scale sampleA sampleB weightA weightB scoreA scoreB
      scaledCellScale scaledEnvelope hcoverA hcoverB hscaledBound
      hscaledEnvelope
  exact
    tendsto_scaled_l1ScoreCellShareDistance_zero_of_eventually_nonneg_cellwise
      cells scale sampleA sampleB weightA weightB scoreA scoreB
      hscale_nonneg
      (fun cell hcell =>
        tendsto_scaled_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
          scale sampleA sampleB weightA weightB scoreA scoreB cell
          (massLimit cell) (∑ cell ∈ cells, massLimit cell)
          (hmassB cell hcell) htotalA htotalB
          (hscaledMass cell hcell) hscaledTotal htotalLimit)

variable {Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
Fixed finite PATE double-score L1 share convergence follows from shrinking
mass envelopes for both samples.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_envelopes
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit cellScaleA cellScaleB :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (envelopeA envelopeB : Index -> Real)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index))
      l (nhds 0) :=
  tendsto_l1ScoreCellShareDistance_zero_of_cell_mass_envelopes
    (l := l) cells sampleA sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    massLimit cellScaleA cellScaleB envelopeA envelopeB hcoverA hcoverB
    hboundA hboundB henvelopeA henvelopeB htotalLimit

/--
Fixed finite PATE double-score L1 share convergence follows from eventually
valid coverage and shrinking mass envelopes for both samples.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit cellScaleA cellScaleB :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (envelopeA envelopeB : Index -> Real)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index))
      l (nhds 0) :=
  tendsto_l1ScoreCellShareDistance_zero_of_eventually_cell_mass_envelopes
    (l := l) cells sampleA sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    massLimit cellScaleA cellScaleB envelopeA envelopeB hcoverA hcoverB
    hboundA hboundB henvelopeA henvelopeB htotalLimit

/--
Scaled fixed finite PATE double-score L1 share convergence follows from
shrinking mass envelopes and a shrinking envelope for scaled joint-cell mass
differences.
-/
theorem tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_envelopes
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit cellScaleA cellScaleB scaledCellScale :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1PATEDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
      l (nhds 0) :=
  tendsto_scaled_l1ScoreCellShareDistance_zero_of_cell_mass_envelopes
    (l := l) cells scale sampleA sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    massLimit cellScaleA cellScaleB scaledCellScale envelopeA envelopeB
    scaledEnvelope hscale_nonneg hcoverA hcoverB hboundA hboundB
    hscaledBound henvelopeA henvelopeB hscaledEnvelope htotalLimit

/--
Fixed finite PATE double-score L1 share convergence at ordinary and scaled
rates follows from shrinking mass envelopes and a shrinking scaled
joint-cell mass-difference envelope.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_cell_mass_envelopes
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit cellScaleA cellScaleB scaledCellScale :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · apply
      (tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption
  · apply
      (tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption

/--
Scaled fixed finite PATE double-score L1 share convergence follows from
eventually valid coverage, eventual scale nonnegativity, shrinking mass
envelopes, and a shrinking envelope for scaled joint-cell mass differences.
-/
theorem tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit cellScaleA cellScaleB scaledCellScale :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1PATEDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
      l (nhds 0) :=
  tendsto_scaled_l1ScoreCellShareDistance_zero_of_eventually_cell_mass_envelopes
    (l := l) cells scale sampleA sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    massLimit cellScaleA cellScaleB scaledCellScale envelopeA envelopeB
    scaledEnvelope hscale_nonneg hcoverA hcoverB hboundA hboundB
    hscaledBound henvelopeA henvelopeB hscaledEnvelope htotalLimit

/--
Fixed finite PATE double-score L1 share convergence at ordinary and scaled
rates follows from eventually valid coverage, eventual scale nonnegativity,
shrinking mass envelopes, and a shrinking scaled joint-cell mass-difference
envelope.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_eventually_cell_mass_envelopes
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit cellScaleA cellScaleB scaledCellScale :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · apply
      (tendsto_l1PATEDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption
  · apply
      (tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption

/--
Fixed finite PATT double-score L1 share convergence follows from shrinking
mass envelopes for both samples.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_of_cell_mass_envelopes
    (cells : Finset (PropensityCell × PATTProgCell))
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit cellScaleA cellScaleB :
      PropensityCell × PATTProgCell -> Real)
    (envelopeA envelopeB : Index -> Real)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (controlPrognosticScore index))
      l (nhds 0) :=
  tendsto_l1ScoreCellShareDistance_zero_of_cell_mass_envelopes
    (l := l) cells sampleA sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    massLimit cellScaleA cellScaleB envelopeA envelopeB hcoverA hcoverB
    hboundA hboundB henvelopeA henvelopeB htotalLimit

/--
Fixed finite PATT double-score L1 share convergence follows from eventually
valid coverage and shrinking mass envelopes for both samples.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
    (cells : Finset (PropensityCell × PATTProgCell))
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit cellScaleA cellScaleB :
      PropensityCell × PATTProgCell -> Real)
    (envelopeA envelopeB : Index -> Real)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (weightA index) (weightB index) (propensityScore index)
          (controlPrognosticScore index))
      l (nhds 0) :=
  tendsto_l1ScoreCellShareDistance_zero_of_eventually_cell_mass_envelopes
    (l := l) cells sampleA sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    massLimit cellScaleA cellScaleB envelopeA envelopeB hcoverA hcoverB
    hboundA hboundB henvelopeA henvelopeB htotalLimit

/--
Scaled fixed finite PATT double-score L1 share convergence follows from
shrinking mass envelopes and a shrinking envelope for scaled joint-cell mass
differences.
-/
theorem tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_cell_mass_envelopes
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit cellScaleA cellScaleB scaledCellScale :
      PropensityCell × PATTProgCell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1PATTDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (controlPrognosticScore index))
      l (nhds 0) :=
  tendsto_scaled_l1ScoreCellShareDistance_zero_of_cell_mass_envelopes
    (l := l) cells scale sampleA sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    massLimit cellScaleA cellScaleB scaledCellScale envelopeA envelopeB
    scaledEnvelope hscale_nonneg hcoverA hcoverB hboundA hboundB
    hscaledBound henvelopeA henvelopeB hscaledEnvelope htotalLimit

/--
Fixed finite PATT double-score L1 share convergence at ordinary and scaled
rates follows from shrinking mass envelopes and a shrinking scaled
joint-cell mass-difference envelope.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_cell_mass_envelopes
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit cellScaleA cellScaleB scaledCellScale :
      PropensityCell × PATTProgCell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance cells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · apply
      (tendsto_l1PATTDoubleScoreShareDistance_zero_of_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption
  · apply
      (tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption

/--
Scaled fixed finite PATT double-score L1 share convergence follows from
eventually valid coverage, eventual scale nonnegativity, shrinking mass
envelopes, and a shrinking envelope for scaled joint-cell mass differences.
-/
theorem tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit cellScaleA cellScaleB scaledCellScale :
      PropensityCell × PATTProgCell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1PATTDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (controlPrognosticScore index))
      l (nhds 0) :=
  tendsto_scaled_l1ScoreCellShareDistance_zero_of_eventually_cell_mass_envelopes
    (l := l) cells scale sampleA sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    massLimit cellScaleA cellScaleB scaledCellScale envelopeA envelopeB
    scaledEnvelope hscale_nonneg hcoverA hcoverB hboundA hboundB
    hscaledBound henvelopeA henvelopeB hscaledEnvelope htotalLimit

/--
Fixed finite PATT double-score L1 share convergence at ordinary and scaled
rates follows from eventually valid coverage, eventual scale nonnegativity,
shrinking mass envelopes, and a shrinking scaled joint-cell mass-difference
envelope.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_eventually_cell_mass_envelopes
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit cellScaleA cellScaleB scaledCellScale :
      PropensityCell × PATTProgCell -> Real)
    (envelopeA envelopeB scaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hboundA :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleA cell * envelopeA index)
    (hboundB :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            cellScaleB cell * envelopeB index)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (henvelopeA :
      Tendsto envelopeA l (nhds 0))
    (henvelopeB :
      Tendsto envelopeB l (nhds 0))
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance cells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance cells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · apply
      (tendsto_l1PATTDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption
  · apply
      (tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption

/--
Paired PATE/PATT ordinary and scaled double-score L1 share convergence from
shrinking finite cell-mass envelopes.
-/
theorem tendsto_l1PATE_PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_cell_mass_envelopes
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateMassLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattMassLimit : PropensityCell × PATTProgCell -> Real)
    (pateCellScaleA pateCellScaleB pateScaledCellScale :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattCellScaleA pattCellScaleB pattScaledCellScale :
      PropensityCell × PATTProgCell -> Real)
    (pateEnvelopeA pateEnvelopeB pateScaledEnvelope : Index -> Real)
    (pattEnvelopeA pattEnvelopeB pattScaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hpateCoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ pateCells)
    (hpattCoverA :
      ∀ index unit, unit ∈ sampleA index ->
        pattDoubleScore (propensityScore index)
          (pattPrognosticScore index) unit ∈ pattCells)
    (hpattCoverB :
      ∀ index unit, unit ∈ sampleB index ->
        pattDoubleScore (propensityScore index)
          (pattPrognosticScore index) unit ∈ pattCells)
    (hpateBoundA :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - pateMassLimit cell| ≤
            pateCellScaleA cell * pateEnvelopeA index)
    (hpateBoundB :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - pateMassLimit cell| ≤
            pateCellScaleB cell * pateEnvelopeB index)
    (hpateScaledBound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            pateScaledCellScale cell * pateScaledEnvelope index)
    (hpattBoundA :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (pattPrognosticScore index)) cell - pattMassLimit cell| ≤
            pattCellScaleA cell * pattEnvelopeA index)
    (hpattBoundB :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (pattPrognosticScore index)) cell - pattMassLimit cell| ≤
            pattCellScaleB cell * pattEnvelopeB index)
    (hpattScaledBound :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell)| ≤
            pattScaledCellScale cell * pattScaledEnvelope index)
    (hpateEnvelopeA :
      Tendsto pateEnvelopeA l (nhds 0))
    (hpateEnvelopeB :
      Tendsto pateEnvelopeB l (nhds 0))
    (hpateScaledEnvelope :
      Tendsto pateScaledEnvelope l (nhds 0))
    (hpattEnvelopeA :
      Tendsto pattEnvelopeA l (nhds 0))
    (hpattEnvelopeB :
      Tendsto pattEnvelopeB l (nhds 0))
    (hpattScaledEnvelope :
      Tendsto pattScaledEnvelope l (nhds 0))
    (hpateTotalLimit :
      (∑ cell ∈ pateCells, pateMassLimit cell) ≠ 0)
    (hpattTotalLimit :
      (∑ cell ∈ pattCells, pattMassLimit cell) ≠ 0) :
    (Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance pateCells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance pateCells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) ∧
      (Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance pattCells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (pattPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance pattCells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (pattPrognosticScore index))
        l (nhds 0)) := by
  constructor
  · apply
      (tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption
  · apply
      (tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption

/--
Paired PATE/PATT ordinary and scaled double-score L1 share convergence from
eventually valid finite cell-mass envelopes.
-/
theorem tendsto_l1PATE_PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_eventually_cell_mass_envelopes
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (scale : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (weightA weightB : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateMassLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattMassLimit : PropensityCell × PATTProgCell -> Real)
    (pateCellScaleA pateCellScaleB pateScaledCellScale :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattCellScaleA pattCellScaleB pattScaledCellScale :
      PropensityCell × PATTProgCell -> Real)
    (pateEnvelopeA pateEnvelopeB pateScaledEnvelope : Index -> Real)
    (pattEnvelopeA pattEnvelopeB pattScaledEnvelope : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hpateCoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ pateCells)
    (hpattCoverA :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleA index ->
          pattDoubleScore (propensityScore index)
            (pattPrognosticScore index) unit ∈ pattCells)
    (hpattCoverB :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sampleB index ->
          pattDoubleScore (propensityScore index)
            (pattPrognosticScore index) unit ∈ pattCells)
    (hpateBoundA :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - pateMassLimit cell| ≤
            pateCellScaleA cell * pateEnvelopeA index)
    (hpateBoundB :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - pateMassLimit cell| ≤
            pateCellScaleB cell * pateEnvelopeB index)
    (hpateScaledBound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            pateScaledCellScale cell * pateScaledEnvelope index)
    (hpattBoundA :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleA index) (weightA index)
              (pattDoubleScore (propensityScore index)
                (pattPrognosticScore index)) cell - pattMassLimit cell| ≤
            pattCellScaleA cell * pattEnvelopeA index)
    (hpattBoundB :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scoreCellMass (sampleB index) (weightB index)
              (pattDoubleScore (propensityScore index)
                (pattPrognosticScore index)) cell - pattMassLimit cell| ≤
            pattCellScaleB cell * pattEnvelopeB index)
    (hpattScaledBound :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell)| ≤
            pattScaledCellScale cell * pattScaledEnvelope index)
    (hpateEnvelopeA :
      Tendsto pateEnvelopeA l (nhds 0))
    (hpateEnvelopeB :
      Tendsto pateEnvelopeB l (nhds 0))
    (hpateScaledEnvelope :
      Tendsto pateScaledEnvelope l (nhds 0))
    (hpattEnvelopeA :
      Tendsto pattEnvelopeA l (nhds 0))
    (hpattEnvelopeB :
      Tendsto pattEnvelopeB l (nhds 0))
    (hpattScaledEnvelope :
      Tendsto pattScaledEnvelope l (nhds 0))
    (hpateTotalLimit :
      (∑ cell ∈ pateCells, pateMassLimit cell) ≠ 0)
    (hpattTotalLimit :
      (∑ cell ∈ pattCells, pattMassLimit cell) ≠ 0) :
    (Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance pateCells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance pateCells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) ∧
      (Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance pattCells (sampleA index)
            (sampleB index) (weightA index) (weightB index)
            (propensityScore index) (pattPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance pattCells (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (propensityScore index) (pattPrognosticScore index))
        l (nhds 0)) := by
  constructor
  · apply
      (tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_eventually_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption
  · apply
      (tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_eventually_cell_mass_envelopes
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption

end WDSM
end Matching
end StatInference
