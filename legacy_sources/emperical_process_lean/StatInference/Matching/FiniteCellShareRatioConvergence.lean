import StatInference.Matching.WDSM.DiscreteDoubleScoreBalancing
import StatInference.Matching.WDSM.HajekLimitAlgebra

/-!
# Finite score-cell share ratio convergence for WDSM

The fixed finite-cell L1 theorem reduces double-score share convergence to
pointwise convergence of normalized cell shares.  This module reduces that
pointwise statement one step further: a cell share is a Hájek ratio, so it
converges once the corresponding weighted cell mass and total weighted mass
converge to common nonzero denominator limits.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index UnitA UnitB Cell : Type*} {l : Filter Index}

/--
If two ratios have numerators converging to the same limit and denominators
converging to the same nonzero limit, their difference converges to zero.
-/
theorem tendsto_ratio_sub_ratio_zero_of_common_limits
    (numeratorA denominatorA numeratorB denominatorB : Index -> Real)
    (numeratorLimit denominatorLimit : Real)
    (hnumeratorA : Tendsto numeratorA l (nhds numeratorLimit))
    (hnumeratorB : Tendsto numeratorB l (nhds numeratorLimit))
    (hdenominatorA : Tendsto denominatorA l (nhds denominatorLimit))
    (hdenominatorB : Tendsto denominatorB l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        numeratorA index / denominatorA index -
          numeratorB index / denominatorB index)
      l (nhds 0) := by
  have hratioA :
      Tendsto (fun index => numeratorA index / denominatorA index) l
        (nhds (numeratorLimit / denominatorLimit)) :=
    tendsto_ratio_of_tendsto numeratorA denominatorA numeratorLimit
      denominatorLimit hnumeratorA hdenominatorA hdenominatorLimit
  have hratioB :
      Tendsto (fun index => numeratorB index / denominatorB index) l
        (nhds (numeratorLimit / denominatorLimit)) :=
    tendsto_ratio_of_tendsto numeratorB denominatorB numeratorLimit
      denominatorLimit hnumeratorB hdenominatorB hdenominatorLimit
  simpa using hratioA.sub hratioB

/--
Scaled ratio-difference convergence.  If the reference numerator converges,
both denominators converge to the same nonzero limit, and the scaled numerator
and denominator differences vanish, then the scaled ratio difference vanishes.
-/
theorem tendsto_scaled_ratio_sub_ratio_zero_of_common_limits
    (scale numeratorA denominatorA numeratorB denominatorB : Index -> Real)
    (numeratorLimit denominatorLimit : Real)
    (hnumeratorB : Tendsto numeratorB l (nhds numeratorLimit))
    (hdenominatorA : Tendsto denominatorA l (nhds denominatorLimit))
    (hdenominatorB : Tendsto denominatorB l (nhds denominatorLimit))
    (hscaledNumerator :
      Tendsto
        (fun index => scale index * (numeratorA index - numeratorB index))
        l (nhds 0))
    (hscaledDenominator :
      Tendsto
        (fun index =>
          scale index * (denominatorA index - denominatorB index))
        l (nhds 0))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          (numeratorA index / denominatorA index -
            numeratorB index / denominatorB index))
      l (nhds 0) := by
  let numeratorScaled : Index -> Real := fun index =>
    denominatorB index *
        (scale index * (numeratorA index - numeratorB index)) -
      numeratorB index *
        (scale index * (denominatorA index - denominatorB index))
  let denominatorProduct : Index -> Real := fun index =>
    denominatorA index * denominatorB index
  have hnumeratorScaled :
      Tendsto numeratorScaled l (nhds 0) := by
    have hfirst :
        Tendsto
          (fun index =>
            denominatorB index *
              (scale index * (numeratorA index - numeratorB index)))
          l (nhds (denominatorLimit * 0)) :=
      hdenominatorB.mul hscaledNumerator
    have hsecond :
        Tendsto
          (fun index =>
            numeratorB index *
              (scale index * (denominatorA index - denominatorB index)))
          l (nhds (numeratorLimit * 0)) :=
      hnumeratorB.mul hscaledDenominator
    simpa [numeratorScaled] using hfirst.sub hsecond
  have hdenominatorProduct :
      Tendsto denominatorProduct l
        (nhds (denominatorLimit * denominatorLimit)) := by
    simpa [denominatorProduct] using hdenominatorA.mul hdenominatorB
  have hproductLimit : denominatorLimit * denominatorLimit ≠ 0 :=
    mul_ne_zero hdenominatorLimit hdenominatorLimit
  have hratio :
      Tendsto (fun index => numeratorScaled index / denominatorProduct index)
        l (nhds 0) := by
    simpa using
      hnumeratorScaled.div hdenominatorProduct hproductLimit
  have hdenominatorA_ne :
      ∀ᶠ index in l, denominatorA index ≠ 0 :=
    hdenominatorA.eventually_ne hdenominatorLimit
  have hdenominatorB_ne :
      ∀ᶠ index in l, denominatorB index ≠ 0 :=
    hdenominatorB.eventually_ne hdenominatorLimit
  have heq :
      (fun index =>
        scale index *
          (numeratorA index / denominatorA index -
            numeratorB index / denominatorB index)) =ᶠ[l]
        (fun index => numeratorScaled index / denominatorProduct index) := by
    filter_upwards [hdenominatorA_ne, hdenominatorB_ne] with index hA hB
    simp [numeratorScaled, denominatorProduct]
    field_simp [hA, hB]
    ring
  exact hratio.congr' heq.symm

variable [DecidableEq Cell]

/--
A single normalized score-cell share converges to the ratio of the limiting
cell mass and total mass.
-/
theorem tendsto_scoreCellShare_of_mass_total
    (sample : Index -> Finset UnitA)
    (weight : Index -> UnitA -> Real)
    (score : Index -> UnitA -> Cell)
    (cell : Cell) (massLimit totalLimit : Real)
    (hmass :
      Tendsto
        (fun index =>
          scoreCellMass (sample index) (weight index) (score index) cell)
        l (nhds massLimit))
    (htotal :
      Tendsto
        (fun index => weightedSampleTotal (sample index) (weight index))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scoreCellShare (sample index) (weight index) (score index) cell)
      l (nhds (massLimit / totalLimit)) := by
  unfold scoreCellShare
  exact tendsto_ratio_of_tendsto
    (fun index =>
      scoreCellMass (sample index) (weight index) (score index) cell)
    (fun index => weightedSampleTotal (sample index) (weight index))
    massLimit totalLimit hmass htotal htotalLimit

/--
Pointwise score-cell share convergence follows from convergence of both
samples' weighted cell masses to the same limit and both weighted totals to
the same nonzero limit.
-/
theorem tendsto_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (cell : Cell) (massLimit totalLimit : Real)
    (hmassA :
      Tendsto
        (fun index =>
          scoreCellMass (sampleA index) (weightA index) (scoreA index) cell)
        l (nhds massLimit))
    (hmassB :
      Tendsto
        (fun index =>
          scoreCellMass (sampleB index) (weightB index) (scoreB index) cell)
        l (nhds massLimit))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scoreCellShare (sampleA index) (weightA index) (scoreA index) cell -
          scoreCellShare (sampleB index) (weightB index) (scoreB index) cell)
      l (nhds 0) := by
  unfold scoreCellShare
  exact tendsto_ratio_sub_ratio_zero_of_common_limits
    (fun index =>
      scoreCellMass (sampleA index) (weightA index) (scoreA index) cell)
    (fun index => weightedSampleTotal (sampleA index) (weightA index))
    (fun index =>
      scoreCellMass (sampleB index) (weightB index) (scoreB index) cell)
    (fun index => weightedSampleTotal (sampleB index) (weightB index))
    massLimit totalLimit hmassA hmassB htotalA htotalB htotalLimit

/--
Scaled pointwise score-cell share convergence follows from a reference
cell-mass limit, denominator stabilization, and scaled convergence of the
cell-mass and total-mass differences.
-/
theorem tendsto_scaled_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
    (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (cell : Cell) (massLimit totalLimit : Real)
    (hmassB :
      Tendsto
        (fun index =>
          scoreCellMass (sampleB index) (weightB index) (scoreB index) cell)
        l (nhds massLimit))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (hscaledMass :
      Tendsto
        (fun index =>
          scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleTotal (sampleA index) (weightA index) -
              weightedSampleTotal (sampleB index) (weightB index)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          (scoreCellShare (sampleA index) (weightA index)
              (scoreA index) cell -
            scoreCellShare (sampleB index) (weightB index)
              (scoreB index) cell))
      l (nhds 0) := by
  unfold scoreCellShare
  exact tendsto_scaled_ratio_sub_ratio_zero_of_common_limits
    scale
    (fun index =>
      scoreCellMass (sampleA index) (weightA index) (scoreA index) cell)
    (fun index => weightedSampleTotal (sampleA index) (weightA index))
    (fun index =>
      scoreCellMass (sampleB index) (weightB index) (scoreB index) cell)
    (fun index => weightedSampleTotal (sampleB index) (weightB index))
    massLimit totalLimit hmassB htotalA htotalB hscaledMass
    hscaledTotal htotalLimit

variable {PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
PATE double-score pointwise share convergence reduced to convergence of the
corresponding joint double-score cell masses and total masses.
-/
theorem tendsto_pateDoubleScoreShare_sub_zero_of_mass_total
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (propensityScoreA : Index -> UnitA -> PropensityCell)
    (propensityScoreB : Index -> UnitB -> PropensityCell)
    (treatedPrognosticScoreA : Index -> UnitA -> TreatedProgCell)
    (treatedPrognosticScoreB : Index -> UnitB -> TreatedProgCell)
    (controlPrognosticScoreA : Index -> UnitA -> ControlProgCell)
    (controlPrognosticScoreB : Index -> UnitB -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (massLimit totalLimit : Real)
    (hmassA :
      Tendsto
        (fun index =>
          scoreCellMass (sampleA index) (weightA index)
            (pateDoubleScore (propensityScoreA index)
              (treatedPrognosticScoreA index)
              (controlPrognosticScoreA index)) cell)
        l (nhds massLimit))
    (hmassB :
      Tendsto
        (fun index =>
          scoreCellMass (sampleB index) (weightB index)
            (pateDoubleScore (propensityScoreB index)
              (treatedPrognosticScoreB index)
              (controlPrognosticScoreB index)) cell)
        l (nhds massLimit))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scoreCellShare (sampleA index) (weightA index)
            (pateDoubleScore (propensityScoreA index)
              (treatedPrognosticScoreA index)
              (controlPrognosticScoreA index)) cell -
          scoreCellShare (sampleB index) (weightB index)
            (pateDoubleScore (propensityScoreB index)
              (treatedPrognosticScoreB index)
              (controlPrognosticScoreB index)) cell)
      l (nhds 0) := by
  exact tendsto_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
    sampleA sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScoreA index)
        (treatedPrognosticScoreA index) (controlPrognosticScoreA index))
    (fun index =>
      pateDoubleScore (propensityScoreB index)
        (treatedPrognosticScoreB index) (controlPrognosticScoreB index))
    cell massLimit totalLimit hmassA hmassB htotalA htotalB htotalLimit

/--
Scaled PATE double-score pointwise share convergence reduced to scaled
convergence of joint double-score cell-mass and total-mass differences.
-/
theorem tendsto_scaled_pateDoubleScoreShare_sub_zero_of_mass_total
    (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (propensityScoreA : Index -> UnitA -> PropensityCell)
    (propensityScoreB : Index -> UnitB -> PropensityCell)
    (treatedPrognosticScoreA : Index -> UnitA -> TreatedProgCell)
    (treatedPrognosticScoreB : Index -> UnitB -> TreatedProgCell)
    (controlPrognosticScoreA : Index -> UnitA -> ControlProgCell)
    (controlPrognosticScoreB : Index -> UnitB -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (massLimit totalLimit : Real)
    (hmassB :
      Tendsto
        (fun index =>
          scoreCellMass (sampleB index) (weightB index)
            (pateDoubleScore (propensityScoreB index)
              (treatedPrognosticScoreB index)
              (controlPrognosticScoreB index)) cell)
        l (nhds massLimit))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (hscaledMass :
      Tendsto
        (fun index =>
          scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pateDoubleScore (propensityScoreA index)
                  (treatedPrognosticScoreA index)
                  (controlPrognosticScoreA index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pateDoubleScore (propensityScoreB index)
                  (treatedPrognosticScoreB index)
                  (controlPrognosticScoreB index)) cell))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleTotal (sampleA index) (weightA index) -
              weightedSampleTotal (sampleB index) (weightB index)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          (scoreCellShare (sampleA index) (weightA index)
              (pateDoubleScore (propensityScoreA index)
                (treatedPrognosticScoreA index)
                (controlPrognosticScoreA index)) cell -
            scoreCellShare (sampleB index) (weightB index)
              (pateDoubleScore (propensityScoreB index)
                (treatedPrognosticScoreB index)
                (controlPrognosticScoreB index)) cell))
      l (nhds 0) := by
  exact tendsto_scaled_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
    scale sampleA sampleB weightA weightB
    (fun index =>
      pateDoubleScore (propensityScoreA index)
        (treatedPrognosticScoreA index) (controlPrognosticScoreA index))
    (fun index =>
      pateDoubleScore (propensityScoreB index)
        (treatedPrognosticScoreB index) (controlPrognosticScoreB index))
    cell massLimit totalLimit hmassB htotalA htotalB hscaledMass
    hscaledTotal htotalLimit

/--
PATT double-score pointwise share convergence reduced to convergence of the
corresponding joint double-score cell masses and total masses.
-/
theorem tendsto_pattDoubleScoreShare_sub_zero_of_mass_total
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (propensityScoreA : Index -> UnitA -> PropensityCell)
    (propensityScoreB : Index -> UnitB -> PropensityCell)
    (controlPrognosticScoreA : Index -> UnitA -> PATTProgCell)
    (controlPrognosticScoreB : Index -> UnitB -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (massLimit totalLimit : Real)
    (hmassA :
      Tendsto
        (fun index =>
          scoreCellMass (sampleA index) (weightA index)
            (pattDoubleScore (propensityScoreA index)
              (controlPrognosticScoreA index)) cell)
        l (nhds massLimit))
    (hmassB :
      Tendsto
        (fun index =>
          scoreCellMass (sampleB index) (weightB index)
            (pattDoubleScore (propensityScoreB index)
              (controlPrognosticScoreB index)) cell)
        l (nhds massLimit))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scoreCellShare (sampleA index) (weightA index)
            (pattDoubleScore (propensityScoreA index)
              (controlPrognosticScoreA index)) cell -
          scoreCellShare (sampleB index) (weightB index)
            (pattDoubleScore (propensityScoreB index)
              (controlPrognosticScoreB index)) cell)
      l (nhds 0) := by
  exact tendsto_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
    sampleA sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScoreA index)
        (controlPrognosticScoreA index))
    (fun index =>
      pattDoubleScore (propensityScoreB index)
        (controlPrognosticScoreB index))
    cell massLimit totalLimit hmassA hmassB htotalA htotalB htotalLimit

/--
Scaled PATT double-score pointwise share convergence reduced to scaled
convergence of joint double-score cell-mass and total-mass differences.
-/
theorem tendsto_scaled_pattDoubleScoreShare_sub_zero_of_mass_total
    (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (propensityScoreA : Index -> UnitA -> PropensityCell)
    (propensityScoreB : Index -> UnitB -> PropensityCell)
    (controlPrognosticScoreA : Index -> UnitA -> PATTProgCell)
    (controlPrognosticScoreB : Index -> UnitB -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (massLimit totalLimit : Real)
    (hmassB :
      Tendsto
        (fun index =>
          scoreCellMass (sampleB index) (weightB index)
            (pattDoubleScore (propensityScoreB index)
              (controlPrognosticScoreB index)) cell)
        l (nhds massLimit))
    (htotalA :
      Tendsto
        (fun index => weightedSampleTotal (sampleA index) (weightA index))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => weightedSampleTotal (sampleB index) (weightB index))
        l (nhds totalLimit))
    (hscaledMass :
      Tendsto
        (fun index =>
          scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (pattDoubleScore (propensityScoreA index)
                  (controlPrognosticScoreA index)) cell -
              scoreCellMass (sampleB index) (weightB index)
                (pattDoubleScore (propensityScoreB index)
                  (controlPrognosticScoreB index)) cell))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleTotal (sampleA index) (weightA index) -
              weightedSampleTotal (sampleB index) (weightB index)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          (scoreCellShare (sampleA index) (weightA index)
              (pattDoubleScore (propensityScoreA index)
                (controlPrognosticScoreA index)) cell -
            scoreCellShare (sampleB index) (weightB index)
              (pattDoubleScore (propensityScoreB index)
                (controlPrognosticScoreB index)) cell))
      l (nhds 0) := by
  exact tendsto_scaled_scoreCellShare_sub_scoreCellShare_zero_of_mass_total
    scale sampleA sampleB weightA weightB
    (fun index =>
      pattDoubleScore (propensityScoreA index)
        (controlPrognosticScoreA index))
    (fun index =>
      pattDoubleScore (propensityScoreB index)
        (controlPrognosticScoreB index))
    cell massLimit totalLimit hmassB htotalA htotalB hscaledMass
    hscaledTotal htotalLimit

end WDSM
end Matching
end StatInference
