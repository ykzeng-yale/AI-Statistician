import StatInference.Matching.WDSM.FiniteCellShareRatioConvergence
import StatInference.Matching.WDSM.ProspectiveScoreCellShareConvergence
import StatInference.Matching.WDSM.ProspectiveNormalizedCountIndicatorBridge

/-!
# Prospective finite count-ratio convergence for WDSM

Prospective sampling arguments usually prove convergence of normalized finite
counts, for example `n⁻¹ * cellCount` and `n⁻¹ * sampleSize`.  This module
turns those normalized-count limits into convergence of the ordinary finite
cell-count ratios used by the prospective WDSM score-share bridges.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Unit Cell : Type*} {l : Filter Index}
  [DecidableEq Cell]

theorem tendsto_ratio_sub_ratio_zero_of_normalized_common_limits
    (normalizerA normalizerB numeratorA denominatorA numeratorB denominatorB :
      Index -> Real)
    (numeratorLimit denominatorLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hnumeratorA :
      Tendsto (fun index => normalizerA index * numeratorA index)
        l (nhds numeratorLimit))
    (hnumeratorB :
      Tendsto (fun index => normalizerB index * numeratorB index)
        l (nhds numeratorLimit))
    (hdenominatorA :
      Tendsto (fun index => normalizerA index * denominatorA index)
        l (nhds denominatorLimit))
    (hdenominatorB :
      Tendsto (fun index => normalizerB index * denominatorB index)
        l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        numeratorA index / denominatorA index -
          numeratorB index / denominatorB index)
      l (nhds 0) := by
  have hnormalized :
      Tendsto
        (fun index =>
          (normalizerA index * numeratorA index) /
              (normalizerA index * denominatorA index) -
            (normalizerB index * numeratorB index) /
              (normalizerB index * denominatorB index))
        l (nhds 0) :=
    tendsto_ratio_sub_ratio_zero_of_common_limits
      (fun index => normalizerA index * numeratorA index)
      (fun index => normalizerA index * denominatorA index)
      (fun index => normalizerB index * numeratorB index)
      (fun index => normalizerB index * denominatorB index)
      numeratorLimit denominatorLimit hnumeratorA hnumeratorB
      hdenominatorA hdenominatorB hdenominatorLimit
  convert hnormalized using 1
  ext index
  rw [mul_div_mul_left _ _ (hnormalizerA index),
    mul_div_mul_left _ _ (hnormalizerB index)]

theorem tendsto_scaled_ratio_sub_ratio_zero_of_normalized_common_limits
    (scale normalizerA normalizerB numeratorA denominatorA numeratorB
      denominatorB : Index -> Real)
    (numeratorLimit denominatorLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hnumeratorB :
      Tendsto (fun index => normalizerB index * numeratorB index)
        l (nhds numeratorLimit))
    (hdenominatorA :
      Tendsto (fun index => normalizerA index * denominatorA index)
        l (nhds denominatorLimit))
    (hdenominatorB :
      Tendsto (fun index => normalizerB index * denominatorB index)
        l (nhds denominatorLimit))
    (hscaledNumerator :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * numeratorA index -
              normalizerB index * numeratorB index))
        l (nhds 0))
    (hscaledDenominator :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * denominatorA index -
              normalizerB index * denominatorB index))
        l (nhds 0))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          (numeratorA index / denominatorA index -
            numeratorB index / denominatorB index))
      l (nhds 0) := by
  have hnormalized :
      Tendsto
        (fun index =>
          scale index *
            ((normalizerA index * numeratorA index) /
                (normalizerA index * denominatorA index) -
              (normalizerB index * numeratorB index) /
                (normalizerB index * denominatorB index)))
        l (nhds 0) :=
    tendsto_scaled_ratio_sub_ratio_zero_of_common_limits
      scale
      (fun index => normalizerA index * numeratorA index)
      (fun index => normalizerA index * denominatorA index)
      (fun index => normalizerB index * numeratorB index)
      (fun index => normalizerB index * denominatorB index)
      numeratorLimit denominatorLimit hnumeratorB hdenominatorA
      hdenominatorB hscaledNumerator hscaledDenominator hdenominatorLimit
  convert hnormalized using 1
  ext index
  rw [mul_div_mul_left _ _ (hnormalizerA index),
    mul_div_mul_left _ _ (hnormalizerB index)]

/--
Ordinary and scaled ratio-difference convergence from common normalized
numerator/denominator limits plus scaled normalized numerator/denominator
differences.
-/
theorem tendsto_ratio_sub_ratio_zero_and_scaled_zero_of_normalized_common_limits
    (scale normalizerA normalizerB numeratorA denominatorA numeratorB
      denominatorB : Index -> Real)
    (numeratorLimit denominatorLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hnumeratorA :
      Tendsto (fun index => normalizerA index * numeratorA index)
        l (nhds numeratorLimit))
    (hnumeratorB :
      Tendsto (fun index => normalizerB index * numeratorB index)
        l (nhds numeratorLimit))
    (hdenominatorA :
      Tendsto (fun index => normalizerA index * denominatorA index)
        l (nhds denominatorLimit))
    (hdenominatorB :
      Tendsto (fun index => normalizerB index * denominatorB index)
        l (nhds denominatorLimit))
    (hscaledNumerator :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * numeratorA index -
              normalizerB index * numeratorB index))
        l (nhds 0))
    (hscaledDenominator :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * denominatorA index -
              normalizerB index * denominatorB index))
        l (nhds 0))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
        (fun index =>
          numeratorA index / denominatorA index -
            numeratorB index / denominatorB index)
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (numeratorA index / denominatorA index -
              numeratorB index / denominatorB index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_ratio_sub_ratio_zero_of_normalized_common_limits
        normalizerA normalizerB numeratorA denominatorA numeratorB
        denominatorB numeratorLimit denominatorLimit hnormalizerA
        hnormalizerB hnumeratorA hnumeratorB hdenominatorA hdenominatorB
        hdenominatorLimit
  · exact
      tendsto_scaled_ratio_sub_ratio_zero_of_normalized_common_limits
        scale normalizerA normalizerB numeratorA denominatorA numeratorB
        denominatorB numeratorLimit denominatorLimit hnormalizerA
        hnormalizerB hnumeratorB hdenominatorA hdenominatorB
        hscaledNumerator hscaledDenominator hdenominatorLimit

/--
Unscaled ratio convergence from one reference normalized numerator/denominator
limit and ordinary normalized numerator/denominator difference limits.
-/
theorem tendsto_ratio_sub_ratio_zero_of_normalized_reference_and_difference_limits
    (normalizerA normalizerB numeratorA denominatorA numeratorB denominatorB :
      Index -> Real)
    (numeratorLimit denominatorLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hnumeratorB :
      Tendsto (fun index => normalizerB index * numeratorB index)
        l (nhds numeratorLimit))
    (hdenominatorA :
      Tendsto (fun index => normalizerA index * denominatorA index)
        l (nhds denominatorLimit))
    (hdenominatorB :
      Tendsto (fun index => normalizerB index * denominatorB index)
        l (nhds denominatorLimit))
    (hnumeratorDiff :
      Tendsto
        (fun index =>
          normalizerA index * numeratorA index -
            normalizerB index * numeratorB index)
        l (nhds 0))
    (hdenominatorDiff :
      Tendsto
        (fun index =>
          normalizerA index * denominatorA index -
            normalizerB index * denominatorB index)
        l (nhds 0))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        numeratorA index / denominatorA index -
          numeratorB index / denominatorB index)
      l (nhds 0) := by
  simpa [one_mul] using
    (tendsto_scaled_ratio_sub_ratio_zero_of_normalized_common_limits
      (fun _index => (1 : Real)) normalizerA normalizerB numeratorA
      denominatorA numeratorB denominatorB numeratorLimit denominatorLimit
      hnormalizerA hnormalizerB hnumeratorB hdenominatorA hdenominatorB
      (by simpa [one_mul] using hnumeratorDiff)
      (by simpa [one_mul] using hdenominatorDiff)
      hdenominatorLimit)

theorem tendsto_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cell : Cell) (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellA :
      Tendsto
        (fun index =>
          normalizerA index *
            (((sampleA index).filter
              (fun unit => scoreA index unit = cell)).card : Real))
        l (nhds cellLimit))
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit => scoreB index unit = cell)).card : Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
            (fun unit => scoreA index unit = cell)).card : Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
            (fun unit => scoreB index unit = cell)).card : Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_ratio_sub_ratio_zero_of_normalized_common_limits normalizerA
    normalizerB
    (fun index =>
      (((sampleA index).filter
        (fun unit => scoreA index unit = cell)).card : Real))
    (fun index => ((sampleA index).card : Real))
    (fun index =>
      (((sampleB index).filter
        (fun unit => scoreB index unit = cell)).card : Real))
    (fun index => ((sampleB index).card : Real))
    cellLimit totalLimit hnormalizerA hnormalizerB hcellA hcellB
    htotalA htotalB htotalLimit

theorem tendsto_scaled_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cell : Cell) (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit => scoreB index unit = cell)).card : Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hscaledCell :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index *
                (((sampleA index).filter
                  (fun unit => scoreA index unit = cell)).card : Real) -
              normalizerB index *
                (((sampleB index).filter
                  (fun unit => scoreB index unit = cell)).card : Real)))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * ((sampleA index).card : Real) -
              normalizerB index * ((sampleB index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          ((((sampleA index).filter
              (fun unit => scoreA index unit = cell)).card : Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
              (fun unit => scoreB index unit = cell)).card : Real) /
              ((sampleB index).card : Real)))
      l (nhds 0) :=
  tendsto_scaled_ratio_sub_ratio_zero_of_normalized_common_limits scale
    normalizerA normalizerB
    (fun index =>
      (((sampleA index).filter
        (fun unit => scoreA index unit = cell)).card : Real))
    (fun index => ((sampleA index).card : Real))
    (fun index =>
      (((sampleB index).filter
        (fun unit => scoreB index unit = cell)).card : Real))
    (fun index => ((sampleB index).card : Real))
    cellLimit totalLimit hnormalizerA hnormalizerB hcellB htotalA htotalB
    hscaledCell hscaledTotal htotalLimit

theorem tendsto_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_normalized_common_limits
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cell : Cell) (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellA :
      Tendsto
        (fun index =>
          normalizerA index *
            (((sampleA index).filter
              (fun unit => scoreA index unit = cell)).card : Real))
        l (nhds cellLimit))
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit => scoreB index unit = cell)).card : Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hscaledCell :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index *
                (((sampleA index).filter
                  (fun unit => scoreA index unit = cell)).card : Real) -
              normalizerB index *
                (((sampleB index).filter
                  (fun unit => scoreB index unit = cell)).card : Real)))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * ((sampleA index).card : Real) -
              normalizerB index * ((sampleB index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
        (fun index =>
          (((sampleA index).filter
              (fun unit => scoreA index unit = cell)).card : Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
              (fun unit => scoreB index unit = cell)).card : Real) /
              ((sampleB index).card : Real))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            ((((sampleA index).filter
                (fun unit => scoreA index unit = cell)).card : Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                (fun unit => scoreB index unit = cell)).card : Real) /
                ((sampleB index).card : Real)))
        l (nhds 0) :=
  tendsto_ratio_sub_ratio_zero_and_scaled_zero_of_normalized_common_limits
    scale normalizerA normalizerB
    (fun index =>
      (((sampleA index).filter
        (fun unit => scoreA index unit = cell)).card : Real))
    (fun index => ((sampleA index).card : Real))
    (fun index =>
      (((sampleB index).filter
        (fun unit => scoreB index unit = cell)).card : Real))
    (fun index => ((sampleB index).card : Real))
    cellLimit totalLimit hnormalizerA hnormalizerB hcellA hcellB
    htotalA htotalB hscaledCell hscaledTotal htotalLimit

/--
Unscaled finite cell-count ratio convergence from a reference normalized-count
LLN and ordinary normalized cell/total-count difference limits.
-/
theorem tendsto_card_ratio_sub_card_ratio_zero_of_normalized_reference_and_difference_limits
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cell : Cell) (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit => scoreB index unit = cell)).card : Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hcellDiff :
      Tendsto
        (fun index =>
          normalizerA index *
              (((sampleA index).filter
                (fun unit => scoreA index unit = cell)).card : Real) -
            normalizerB index *
              (((sampleB index).filter
                (fun unit => scoreB index unit = cell)).card : Real))
        l (nhds 0))
    (htotalDiff :
      Tendsto
        (fun index =>
          normalizerA index * ((sampleA index).card : Real) -
            normalizerB index * ((sampleB index).card : Real))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
            (fun unit => scoreA index unit = cell)).card : Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
            (fun unit => scoreB index unit = cell)).card : Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_ratio_sub_ratio_zero_of_normalized_reference_and_difference_limits
    normalizerA normalizerB
    (fun index =>
      (((sampleA index).filter
        (fun unit => scoreA index unit = cell)).card : Real))
    (fun index => ((sampleA index).card : Real))
    (fun index =>
      (((sampleB index).filter
        (fun unit => scoreB index unit = cell)).card : Real))
    (fun index => ((sampleB index).card : Real))
    cellLimit totalLimit hnormalizerA hnormalizerB hcellB htotalA htotalB
    hcellDiff htotalDiff htotalLimit

/--
Direct indicator-sum route for ordinary finite cell-count ratio convergence:
one reference weighted score-cell indicator LLN plus ordinary weighted
indicator-sum difference limits imply the unscaled ratio difference vanishes.
-/
theorem tendsto_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cell : Cell) (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (scoreCellIndicator (scoreB index) cell))
        l (nhds cellLimit))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (scoreCellIndicator (scoreA index) cell) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator (scoreB index) cell))
        l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
            (fun unit => scoreA index unit = cell)).card : Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
            (fun unit => scoreB index unit = cell)).card : Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_of_normalized_reference_and_difference_limits
    normalizerA normalizerB sampleA sampleB scoreA scoreB cell cellLimit
    totalLimit hnormalizerA hnormalizerB
    (tendsto_normalized_cell_count_of_tendsto_weightedSampleSum_indicator_constant_weight
      sampleB scoreB normalizerB cell cellLimit hcellBIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      sampleA normalizerA totalLimit htotalAIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      sampleB normalizerB totalLimit htotalBIndicator)
    (tendsto_normalized_cell_count_difference_of_tendsto_weightedSampleSum_indicator_difference_constant_weight
      sampleA sampleB scoreA scoreB normalizerA normalizerB cell 0
      hcellDiffIndicator)
    (tendsto_normalized_total_count_difference_of_tendsto_weightedSampleSum_one_difference_constant_weight
      sampleA sampleB normalizerA normalizerB 0 htotalDiffIndicator)
    htotalLimit

/--
Direct indicator-sum route for scaled finite cell-count ratio convergence:
one reference weighted score-cell indicator LLN plus scaled weighted
indicator-sum difference limits imply the scaled ratio difference vanishes.
-/
theorem tendsto_scaled_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cell : Cell) (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (scoreCellIndicator (scoreB index) cell))
        l (nhds cellLimit))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator (scoreA index) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator (scoreB index) cell)))
        l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          ((((sampleA index).filter
              (fun unit => scoreA index unit = cell)).card : Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
              (fun unit => scoreB index unit = cell)).card : Real) /
              ((sampleB index).card : Real)))
      l (nhds 0) :=
  tendsto_scaled_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    scale normalizerA normalizerB sampleA sampleB scoreA scoreB cell
    cellLimit totalLimit hnormalizerA hnormalizerB
    (tendsto_normalized_cell_count_of_tendsto_weightedSampleSum_indicator_constant_weight
      sampleB scoreB normalizerB cell cellLimit hcellBIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      sampleA normalizerA totalLimit htotalAIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      sampleB normalizerB totalLimit htotalBIndicator)
    (tendsto_scaled_normalized_cell_count_difference_of_tendsto_scaled_weightedSampleSum_indicator_difference_constant_weight
      scale sampleA sampleB scoreA scoreB normalizerA normalizerB cell 0
      hscaledCellDiffIndicator)
    (tendsto_scaled_normalized_total_count_difference_of_tendsto_scaled_weightedSampleSum_one_difference_constant_weight
      scale sampleA sampleB normalizerA normalizerB 0
      hscaledTotalDiffIndicator)
    htotalLimit

/--
Direct L1 score-share convergence from the ordinary weighted-indicator route.
The count normalizers are kept separate from the common survey weights used in
the finite score-share expression.
-/
theorem tendsto_l1ScoreCellShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells : Finset Cell)
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cellLimit : Cell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator (scoreB index) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator (scoreA index) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator (scoreB index) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
          (fun _unit => commonWeightA index)
          (fun _unit => commonWeightB index)
          (scoreA index) (scoreB index))
      l (nhds 0) := by
  exact
    tendsto_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells sampleA sampleB commonWeightA commonWeightB scoreA scoreB
      hweightA hweightB hnonemptyA hnonemptyB
      (by
        intro cell hmem
        exact
          tendsto_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
            normalizerA normalizerB sampleA sampleB scoreA scoreB cell
            (cellLimit cell) totalLimit hnormalizerA hnormalizerB
            (hcellBIndicator cell hmem) htotalAIndicator htotalBIndicator
            (hcellDiffIndicator cell hmem) htotalDiffIndicator htotalLimit)

/--
Direct scaled L1 score-share convergence from the scaled weighted-indicator
route.  The count normalizers are kept separate from the common survey weights
used in the finite score-share expression.
-/
theorem tendsto_scaled_l1ScoreCellShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells : Finset Cell)
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cellLimit : Cell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator (scoreB index) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator (scoreA index) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator (scoreB index) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (scoreA index) (scoreB index))
      l (nhds 0) := by
  exact
    tendsto_scaled_l1ScoreCellShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells scale sampleA sampleB commonWeightA commonWeightB scoreA scoreB
      hscale_nonneg hweightA hweightB hnonemptyA hnonemptyB
      (by
        intro cell hmem
        exact
          tendsto_scaled_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
            scale normalizerA normalizerB sampleA sampleB scoreA scoreB cell
            (cellLimit cell) totalLimit hnormalizerA hnormalizerB
            (hcellBIndicator cell hmem) htotalAIndicator htotalBIndicator
            (hscaledCellDiffIndicator cell hmem) hscaledTotalDiffIndicator
            htotalLimit)

/--
Direct ordinary and scaled L1 score-share convergence from weighted-indicator
reference LLNs, ordinary weighted-indicator differences, and scaled
weighted-indicator differences.
-/
theorem tendsto_l1ScoreCellShareDistance_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells : Finset Cell)
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (scoreA scoreB : Index -> Unit -> Cell)
    (cellLimit : Cell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator (scoreB index) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator (scoreA index) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator (scoreB index) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator (scoreA index) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator (scoreB index) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
        (fun index =>
          l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (scoreA index) (scoreB index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1ScoreCellShareDistance cells (sampleA index) (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (scoreA index) (scoreB index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1ScoreCellShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
        cells normalizerA normalizerB sampleA sampleB commonWeightA
        commonWeightB scoreA scoreB cellLimit totalLimit hnormalizerA
        hnormalizerB hweightA hweightB hnonemptyA hnonemptyB
        hcellBIndicator htotalAIndicator htotalBIndicator
        hcellDiffIndicator htotalDiffIndicator htotalLimit
  · exact
      tendsto_scaled_l1ScoreCellShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
        cells scale normalizerA normalizerB sampleA sampleB commonWeightA
        commonWeightB scoreA scoreB cellLimit totalLimit hscale_nonneg
        hnormalizerA hnormalizerB hweightA hweightB hnonemptyA
        hnonemptyB hcellBIndicator htotalAIndicator htotalBIndicator
        hscaledCellDiffIndicator hscaledTotalDiffIndicator htotalLimit

variable {PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

theorem tendsto_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellA :
      Tendsto
        (fun index =>
          normalizerA index *
            (((sampleA index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    normalizerA normalizerB sampleA sampleB
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellA hcellB
    htotalA htotalB htotalLimit

theorem tendsto_scaled_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hscaledCell :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index *
                (((sampleA index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real) -
              normalizerB index *
                (((sampleB index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real)))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * ((sampleA index).card : Real) -
              normalizerB index * ((sampleB index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          ((((sampleA index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real)))
      l (nhds 0) :=
  tendsto_scaled_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    scale normalizerA normalizerB sampleA sampleB
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellB htotalA
    htotalB hscaledCell hscaledTotal htotalLimit

theorem tendsto_pateDoubleScore_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_normalized_common_limits
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellA :
      Tendsto
        (fun index =>
          normalizerA index *
            (((sampleA index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hscaledCell :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index *
                (((sampleA index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real) -
              normalizerB index *
                (((sampleB index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real)))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * ((sampleA index).card : Real) -
              normalizerB index * ((sampleB index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
        (fun index =>
          (((sampleA index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            ((((sampleA index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real)))
        l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_normalized_common_limits
    scale normalizerA normalizerB sampleA sampleB
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellA hcellB
    htotalA htotalB hscaledCell hscaledTotal htotalLimit

theorem tendsto_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_reference_and_difference_limits
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hcellDiff :
      Tendsto
        (fun index =>
          normalizerA index *
              (((sampleA index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real) -
            normalizerB index *
              (((sampleB index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
        l (nhds 0))
    (htotalDiff :
      Tendsto
        (fun index =>
          normalizerA index * ((sampleA index).card : Real) -
            normalizerB index * ((sampleB index).card : Real))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_of_normalized_reference_and_difference_limits
    normalizerA normalizerB sampleA sampleB
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellB htotalA
    htotalB hcellDiff htotalDiff htotalLimit

theorem tendsto_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds cellLimit))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
        l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    normalizerA normalizerB sampleA sampleB
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellBIndicator
    htotalAIndicator htotalBIndicator hcellDiffIndicator
    htotalDiffIndicator htotalLimit

theorem tendsto_all_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          (((sampleA index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real))
        l (nhds 0) := by
  intro cell hmem
  exact
    tendsto_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
      normalizerA normalizerB sampleA sampleB propensityScore
      treatedPrognosticScore controlPrognosticScore cell (cellLimit cell)
      totalLimit hnormalizerA hnormalizerB (hcellBIndicator cell hmem)
      htotalAIndicator htotalBIndicator (hcellDiffIndicator cell hmem)
      htotalDiffIndicator htotalLimit

/--
Direct PATE double-score L1 share convergence from weighted indicator-sum
reference LLNs and ordinary weighted indicator-sum difference convergence.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (fun _unit => commonWeightA index)
          (fun _unit => commonWeightB index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      l (nhds 0) := by
  exact
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells sampleA sampleB commonWeightA commonWeightB propensityScore
      treatedPrognosticScore controlPrognosticScore hweightA hweightB
      hnonemptyA hnonemptyB
      (tendsto_all_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
        normalizerA normalizerB sampleA sampleB propensityScore
        treatedPrognosticScore controlPrognosticScore cells cellLimit
        totalLimit hnormalizerA hnormalizerB hcellBIndicator
        htotalAIndicator htotalBIndicator hcellDiffIndicator
        htotalDiffIndicator htotalLimit)

/--
Direct scaled PATE double-score cell-ratio convergence from weighted
indicator-sum reference LLNs and scaled weighted indicator-sum differences.
-/
theorem tendsto_scaled_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds cellLimit))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell)))
        l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          ((((sampleA index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real)))
      l (nhds 0) :=
  tendsto_scaled_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    scale normalizerA normalizerB sampleA sampleB
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellBIndicator
    htotalAIndicator htotalBIndicator hscaledCellDiffIndicator
    hscaledTotalDiffIndicator htotalLimit

theorem tendsto_all_scaled_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          scale index *
            ((((sampleA index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real)))
        l (nhds 0) := by
  intro cell hmem
  exact
    tendsto_scaled_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
      scale normalizerA normalizerB sampleA sampleB propensityScore
      treatedPrognosticScore controlPrognosticScore cell (cellLimit cell)
      totalLimit hnormalizerA hnormalizerB (hcellBIndicator cell hmem)
      htotalAIndicator htotalBIndicator
      (hscaledCellDiffIndicator cell hmem) hscaledTotalDiffIndicator
      htotalLimit

theorem tendsto_all_pateDoubleScore_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          (((sampleA index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real))
        l (nhds 0)) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) := by
  constructor
  · exact
      tendsto_all_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
        normalizerA normalizerB sampleA sampleB propensityScore
        treatedPrognosticScore controlPrognosticScore cells cellLimit
        totalLimit hnormalizerA hnormalizerB hcellBIndicator
        htotalAIndicator htotalBIndicator hcellDiffIndicator
        htotalDiffIndicator htotalLimit
  · exact
      tendsto_all_scaled_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
        scale normalizerA normalizerB sampleA sampleB propensityScore
        treatedPrognosticScore controlPrognosticScore cells cellLimit
        totalLimit hnormalizerA hnormalizerB hcellBIndicator
        htotalAIndicator htotalBIndicator hscaledCellDiffIndicator
        hscaledTotalDiffIndicator htotalLimit

theorem tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
      l (nhds 0) := by
  exact
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells scale sampleA sampleB commonWeightA commonWeightB
      propensityScore treatedPrognosticScore controlPrognosticScore
      hscale_nonneg hweightA hweightB hnonemptyA hnonemptyB
      (tendsto_all_scaled_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
        scale normalizerA normalizerB sampleA sampleB propensityScore
        treatedPrognosticScore controlPrognosticScore cells cellLimit
        totalLimit hnormalizerA hnormalizerB hcellBIndicator
        htotalAIndicator htotalBIndicator hscaledCellDiffIndicator
        hscaledTotalDiffIndicator htotalLimit)

/--
Direct ordinary and scaled PATE double-score L1 score-share convergence from
weighted-indicator reference LLNs, ordinary weighted-indicator differences, and
scaled weighted-indicator differences.
-/
theorem tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells (sampleA index)
              (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1PATEDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
        cells normalizerA normalizerB sampleA sampleB commonWeightA
        commonWeightB propensityScore treatedPrognosticScore
        controlPrognosticScore cellLimit totalLimit hnormalizerA
        hnormalizerB hweightA hweightB hnonemptyA hnonemptyB
        hcellBIndicator htotalAIndicator htotalBIndicator
        hcellDiffIndicator htotalDiffIndicator htotalLimit
  · exact
      tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
        cells scale normalizerA normalizerB sampleA sampleB commonWeightA
        commonWeightB propensityScore treatedPrognosticScore
        controlPrognosticScore cellLimit totalLimit hscale_nonneg
        hnormalizerA hnormalizerB hweightA hweightB hnonemptyA
        hnonemptyB hcellBIndicator htotalAIndicator htotalBIndicator
        hscaledCellDiffIndicator hscaledTotalDiffIndicator htotalLimit

theorem tendsto_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellA :
      Tendsto
        (fun index =>
          normalizerA index *
            (((sampleA index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    normalizerA normalizerB sampleA sampleB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellA hcellB
    htotalA htotalB htotalLimit

theorem tendsto_scaled_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hscaledCell :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index *
                (((sampleA index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real) -
              normalizerB index *
                (((sampleB index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real)))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * ((sampleA index).card : Real) -
              normalizerB index * ((sampleB index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          ((((sampleA index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real)))
      l (nhds 0) :=
  tendsto_scaled_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
    scale normalizerA normalizerB sampleA sampleB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellB htotalA
    htotalB hscaledCell hscaledTotal htotalLimit

theorem tendsto_pattDoubleScore_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_normalized_common_limits
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellA :
      Tendsto
        (fun index =>
          normalizerA index *
            (((sampleA index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hscaledCell :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index *
                (((sampleA index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real) -
              normalizerB index *
                (((sampleB index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                  Real)))
        l (nhds 0))
    (hscaledTotal :
      Tendsto
        (fun index =>
          scale index *
            (normalizerA index * ((sampleA index).card : Real) -
              normalizerB index * ((sampleB index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
        (fun index =>
          (((sampleA index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            ((((sampleA index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real)))
        l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_normalized_common_limits
    scale normalizerA normalizerB sampleA sampleB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellA hcellB
    htotalA htotalB hscaledCell hscaledTotal htotalLimit

theorem tendsto_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_reference_and_difference_limits
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellB :
      Tendsto
        (fun index =>
          normalizerB index *
            (((sampleB index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (htotalA :
      Tendsto
        (fun index => normalizerA index * ((sampleA index).card : Real))
        l (nhds totalLimit))
    (htotalB :
      Tendsto
        (fun index => normalizerB index * ((sampleB index).card : Real))
        l (nhds totalLimit))
    (hcellDiff :
      Tendsto
        (fun index =>
          normalizerA index *
              (((sampleA index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real) -
            normalizerB index *
              (((sampleB index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
        l (nhds 0))
    (htotalDiff :
      Tendsto
        (fun index =>
          normalizerA index * ((sampleA index).card : Real) -
            normalizerB index * ((sampleB index).card : Real))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_of_normalized_reference_and_difference_limits
    normalizerA normalizerB sampleA sampleB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellB htotalA
    htotalB hcellDiff htotalDiff htotalLimit

theorem tendsto_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
        l (nhds cellLimit))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
        l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        (((sampleA index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleA index).card : Real) -
          (((sampleB index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
            Real) /
            ((sampleB index).card : Real))
      l (nhds 0) :=
  tendsto_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    normalizerA normalizerB sampleA sampleB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellBIndicator
    htotalAIndicator htotalBIndicator hcellDiffIndicator
    htotalDiffIndicator htotalLimit

theorem tendsto_all_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          (((sampleA index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real))
        l (nhds 0) := by
  intro cell hmem
  exact
    tendsto_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
      normalizerA normalizerB sampleA sampleB propensityScore
      controlPrognosticScore cell (cellLimit cell) totalLimit hnormalizerA
      hnormalizerB (hcellBIndicator cell hmem) htotalAIndicator
      htotalBIndicator (hcellDiffIndicator cell hmem)
      htotalDiffIndicator htotalLimit

/--
Direct PATT double-score L1 share convergence from weighted indicator-sum
reference LLNs and ordinary weighted indicator-sum difference convergence.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells : Finset (PropensityCell × PATTProgCell))
    (normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
          (fun _unit => commonWeightA index)
          (fun _unit => commonWeightB index)
          (propensityScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  exact
    tendsto_l1PATTDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells sampleA sampleB commonWeightA commonWeightB propensityScore
      controlPrognosticScore hweightA hweightB hnonemptyA hnonemptyB
      (tendsto_all_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
        normalizerA normalizerB sampleA sampleB propensityScore
        controlPrognosticScore cells cellLimit totalLimit hnormalizerA
        hnormalizerB hcellBIndicator htotalAIndicator htotalBIndicator
        hcellDiffIndicator htotalDiffIndicator htotalLimit)

/--
Direct scaled PATT double-score cell-ratio convergence from weighted
indicator-sum reference LLNs and scaled weighted indicator-sum differences.
-/
theorem tendsto_scaled_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (cellLimit totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
        l (nhds cellLimit))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell)))
        l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          ((((sampleA index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real)))
      l (nhds 0) :=
  tendsto_scaled_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    scale normalizerA normalizerB sampleA sampleB
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    cell cellLimit totalLimit hnormalizerA hnormalizerB hcellBIndicator
    htotalAIndicator htotalBIndicator hscaledCellDiffIndicator
    hscaledTotalDiffIndicator htotalLimit

theorem tendsto_all_scaled_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          scale index *
            ((((sampleA index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real)))
        l (nhds 0) := by
  intro cell hmem
  exact
    tendsto_scaled_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
      scale normalizerA normalizerB sampleA sampleB propensityScore
      controlPrognosticScore cell (cellLimit cell) totalLimit hnormalizerA
      hnormalizerB (hcellBIndicator cell hmem) htotalAIndicator
      htotalBIndicator (hscaledCellDiffIndicator cell hmem)
      hscaledTotalDiffIndicator htotalLimit

theorem tendsto_all_pattDoubleScore_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          (((sampleA index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real))
        l (nhds 0)) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0)) := by
  constructor
  · exact
      tendsto_all_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
        normalizerA normalizerB sampleA sampleB propensityScore
        controlPrognosticScore cells cellLimit totalLimit hnormalizerA
        hnormalizerB hcellBIndicator htotalAIndicator htotalBIndicator
        hcellDiffIndicator htotalDiffIndicator htotalLimit
  · exact
      tendsto_all_scaled_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
        scale normalizerA normalizerB sampleA sampleB propensityScore
        controlPrognosticScore cells cellLimit totalLimit hnormalizerA
        hnormalizerB hcellBIndicator htotalAIndicator htotalBIndicator
        hscaledCellDiffIndicator hscaledTotalDiffIndicator htotalLimit

theorem tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
      (fun index =>
        scale index *
          l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (controlPrognosticScore index))
      l (nhds 0) := by
  exact
    tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells scale sampleA sampleB commonWeightA commonWeightB propensityScore
      controlPrognosticScore hscale_nonneg hweightA hweightB hnonemptyA
      hnonemptyB
      (tendsto_all_scaled_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_weighted_indicator_reference_and_difference_constant_weight
        scale normalizerA normalizerB sampleA sampleB propensityScore
        controlPrognosticScore cells cellLimit totalLimit hnormalizerA
        hnormalizerB hcellBIndicator htotalAIndicator htotalBIndicator
        hscaledCellDiffIndicator hscaledTotalDiffIndicator htotalLimit)

/--
Direct ordinary and scaled PATT double-score L1 score-share convergence from
weighted-indicator reference LLNs, ordinary weighted-indicator differences, and
scaled weighted-indicator differences.
-/
theorem tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (cells : Finset (PropensityCell × PATTProgCell))
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hcellBIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hscaledCellDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance cells (sampleA index) (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance cells (sampleA index)
              (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_l1PATTDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
        cells normalizerA normalizerB sampleA sampleB commonWeightA
        commonWeightB propensityScore controlPrognosticScore cellLimit
        totalLimit hnormalizerA hnormalizerB hweightA hweightB
        hnonemptyA hnonemptyB hcellBIndicator htotalAIndicator
        htotalBIndicator hcellDiffIndicator htotalDiffIndicator htotalLimit
  · exact
      tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
        cells scale normalizerA normalizerB sampleA sampleB commonWeightA
        commonWeightB propensityScore controlPrognosticScore cellLimit
        totalLimit hscale_nonneg hnormalizerA hnormalizerB hweightA
      hweightB hnonemptyA hnonemptyB hcellBIndicator htotalAIndicator
      htotalBIndicator hscaledCellDiffIndicator
      hscaledTotalDiffIndicator htotalLimit

/--
Paired PATE/PATT all-cell ordinary and scaled double-score card-ratio
convergence from prospective weighted-indicator reference limits and
ordinary/scaled weighted-indicator differences under constant weights.
-/
theorem tendsto_all_pate_pattDoubleScore_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateCellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattCellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hpateCellBIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (pateCellLimit cell)))
    (hpattCellBIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell))
          l (nhds (pattCellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hpateCellDiffIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hpattCellDiffIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hpateScaledCellDiffIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hpattScaledCellDiffIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    ((∀ cell, cell ∈ pateCells ->
      Tendsto
        (fun index =>
          (((sampleA index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleA index).card : Real) -
            (((sampleB index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
              Real) /
              ((sampleB index).card : Real))
        l (nhds 0)) ∧
      (∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              ((((sampleA index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleA index).card : Real) -
                (((sampleB index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((sampleB index).card : Real)))
          l (nhds 0))) ∧
      ((∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            (((sampleA index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleA index).card : Real) -
              (((sampleB index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index) unit = cell)).card :
                Real) /
                ((sampleB index).card : Real))
          l (nhds 0)) ∧
        (∀ cell, cell ∈ pattCells ->
          Tendsto
            (fun index =>
              scale index *
                ((((sampleA index).filter
                      (fun unit =>
                        pattDoubleScore (propensityScore index)
                          (pattPrognosticScore index) unit = cell)).card :
                    Real) /
                    ((sampleA index).card : Real) -
                  (((sampleB index).filter
                      (fun unit =>
                        pattDoubleScore (propensityScore index)
                          (pattPrognosticScore index) unit = cell)).card :
                    Real) /
                    ((sampleB index).card : Real)))
            l (nhds 0))) := by
  constructor
  · exact
      tendsto_all_pateDoubleScore_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
        scale normalizerA normalizerB sampleA sampleB propensityScore
        treatedPrognosticScore controlPrognosticScore pateCells pateCellLimit
        totalLimit hnormalizerA hnormalizerB hpateCellBIndicator
        htotalAIndicator htotalBIndicator hpateCellDiffIndicator
        htotalDiffIndicator hpateScaledCellDiffIndicator
        hscaledTotalDiffIndicator htotalLimit
  · exact
      tendsto_all_pattDoubleScore_card_ratio_sub_card_ratio_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
        scale normalizerA normalizerB sampleA sampleB propensityScore
        pattPrognosticScore pattCells pattCellLimit totalLimit hnormalizerA
        hnormalizerB hpattCellBIndicator htotalAIndicator htotalBIndicator
        hpattCellDiffIndicator htotalDiffIndicator hpattScaledCellDiffIndicator
        hscaledTotalDiffIndicator htotalLimit

/--
Paired PATE/PATT ordinary and scaled double-score L1 score-share convergence
from prospective weighted-indicator reference limits and ordinary/scaled
weighted-indicator differences under constant weights.
-/
theorem tendsto_l1PATE_PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (scale normalizerA normalizerB : Index -> Real)
    (sampleA sampleB : Index -> Finset Unit)
    (commonWeightA commonWeightB : Index -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateCellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattCellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hnormalizerA : ∀ index, normalizerA index ≠ 0)
    (hnormalizerB : ∀ index, normalizerB index ≠ 0)
    (hweightA : ∀ index, commonWeightA index ≠ 0)
    (hweightB : ∀ index, commonWeightB index ≠ 0)
    (hnonemptyA : ∀ index, (sampleA index).Nonempty)
    (hnonemptyB : ∀ index, (sampleB index).Nonempty)
    (hpateCellBIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (pateCellLimit cell)))
    (hpattCellBIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index)) cell))
          l (nhds (pattCellLimit cell)))
    (htotalAIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
            (fun _unit => normalizerA index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalBIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleB index)
            (fun _unit => normalizerB index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hpateCellDiffIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hpattCellDiffIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index)) cell) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (pattPrognosticScore index)) cell))
          l (nhds 0))
    (htotalDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (sampleA index)
              (fun _unit => normalizerA index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (sampleB index)
              (fun _unit => normalizerB index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hpateScaledCellDiffIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hpattScaledCellDiffIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sampleA index)
                  (fun _unit => normalizerA index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index)) cell) -
                weightedSampleSum (sampleB index)
                  (fun _unit => normalizerB index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (pattPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalDiffIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index)
                (fun _unit => normalizerA index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (sampleB index)
                (fun _unit => normalizerB index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0) :
    (Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance pateCells (sampleA index)
            (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance pateCells (sampleA index)
              (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) ∧
      (Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance pattCells (sampleA index)
            (sampleB index)
            (fun _unit => commonWeightA index)
            (fun _unit => commonWeightB index)
            (propensityScore index) (pattPrognosticScore index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance pattCells (sampleA index)
              (sampleB index)
              (fun _unit => commonWeightA index)
              (fun _unit => commonWeightB index)
              (propensityScore index) (pattPrognosticScore index))
        l (nhds 0)) := by
  constructor
  · exact
      tendsto_l1PATEDoubleScoreShareDistance_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
        pateCells scale normalizerA normalizerB sampleA sampleB
        commonWeightA commonWeightB propensityScore treatedPrognosticScore
        controlPrognosticScore pateCellLimit totalLimit hscale_nonneg
        hnormalizerA hnormalizerB hweightA hweightB hnonemptyA hnonemptyB
        hpateCellBIndicator htotalAIndicator htotalBIndicator
        hpateCellDiffIndicator htotalDiffIndicator
        hpateScaledCellDiffIndicator hscaledTotalDiffIndicator htotalLimit
  · exact
      tendsto_l1PATTDoubleScoreShareDistance_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
        pattCells scale normalizerA normalizerB sampleA sampleB
        commonWeightA commonWeightB propensityScore pattPrognosticScore
        pattCellLimit totalLimit hscale_nonneg hnormalizerA hnormalizerB
        hweightA hweightB hnonemptyA hnonemptyB hpattCellBIndicator
        htotalAIndicator htotalBIndicator hpattCellDiffIndicator
        htotalDiffIndicator hpattScaledCellDiffIndicator
        hscaledTotalDiffIndicator htotalLimit

end WDSM
end Matching
end StatInference
