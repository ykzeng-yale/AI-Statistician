import Mathlib.Data.Finset.Basic
import Mathlib.Topology.Basic
import StatInference.Matching.WDSM.ProspectiveNormalizedCountInterfaces
import StatInference.Matching.WDSM.ProspectiveNormalizedCountIndicatorBridge

/-!
# Prospective normalized-count interfaces from indicator sums

This module fills the transfer fields in the prospective normalized-count
interfaces using the checked constant-normalizer indicator-sum identities.
It keeps the ratio-convergence step explicit while removing the manual
rewriting from indicator LLNs to normalized count LLNs.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Build an unscaled prospective normalized-count indicator bridge from
constant-normalizer weighted score-cell indicator sums.
-/
def prospectiveNormalizedCountIndicatorLLNBridgeOfConstantWeight
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (normalizer : Index -> Real)
    (cellLimit : Cell -> Real)
    (totalLimit : Real)
    (nonzeroTotalLimit cellwiseCountRatioConvergence : Prop)
    (normalized_to_ratio :
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit => score index unit = cell)).card : Real))
          l (nhds (cellLimit cell))) ->
      Tendsto
        (fun index =>
          normalizer index * ((sample index).card : Real))
        l (nhds totalLimit) ->
      nonzeroTotalLimit ->
      cellwiseCountRatioConvergence) :
    ProspectiveNormalizedCountIndicatorLLNBridge Cell where
  count_bridge :=
    { cells := cells
      normalized_cell_count_lln :=
        ∀ cell, cell ∈ cells ->
          Tendsto
            (fun index =>
              normalizer index *
                (((sample index).filter
                  (fun unit => score index unit = cell)).card : Real))
            l (nhds (cellLimit cell))
      normalized_sample_size_lln :=
        Tendsto
          (fun index =>
            normalizer index * ((sample index).card : Real))
          l (nhds totalLimit)
      nonzero_total_limit := nonzeroTotalLimit
      cellwise_count_ratio_convergence := cellwiseCountRatioConvergence
      bridge := normalized_to_ratio }
  weighted_cell_indicator_sum_lln :=
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (sample index)
            (fun _unit => normalizer index)
            (scoreCellIndicator (score index) cell))
        l (nhds (cellLimit cell))
  weighted_total_indicator_sum_lln :=
    Tendsto
      (fun index =>
        weightedSampleSum (sample index)
          (fun _unit => normalizer index) (fun _unit => (1 : Real)))
      l (nhds totalLimit)
  cell_indicator_to_normalized_count := by
    intro hindicator cell hcell
    exact
      tendsto_normalized_cell_count_of_tendsto_weightedSampleSum_indicator_constant_weight
        (l := l) sample score normalizer cell (cellLimit cell)
        (hindicator cell hcell)
  total_indicator_to_normalized_size := by
    intro htotal
    exact
      tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
        (l := l) sample normalizer totalLimit htotal

/--
Constant-normalizer indicator-sum LLNs imply the unscaled prospective
cellwise count-ratio conclusion through the supplied normalized-count bridge.
-/
theorem cellwise_count_ratio_convergence_of_indicator_tendsto_constant_weight
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (normalizer : Index -> Real)
    (cellLimit : Cell -> Real)
    (totalLimit : Real)
    (nonzeroTotalLimit cellwiseCountRatioConvergence : Prop)
    (normalized_to_ratio :
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit => score index unit = cell)).card : Real))
          l (nhds (cellLimit cell))) ->
      Tendsto
        (fun index =>
          normalizer index * ((sample index).card : Real))
        l (nhds totalLimit) ->
      nonzeroTotalLimit ->
      cellwiseCountRatioConvergence)
    (hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (sample index)
              (fun _unit => normalizer index)
              (scoreCellIndicator (score index) cell))
          l (nhds (cellLimit cell)))
    (htotal :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index)
            (fun _unit => normalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hnonzero : nonzeroTotalLimit) :
    cellwiseCountRatioConvergence :=
  cellwise_count_ratio_convergence_of_prospective_indicator_sums
    (prospectiveNormalizedCountIndicatorLLNBridgeOfConstantWeight
      (l := l) cells sample score normalizer cellLimit totalLimit
      nonzeroTotalLimit cellwiseCountRatioConvergence normalized_to_ratio)
    hindicator htotal hnonzero

/--
Build a scaled prospective normalized-count indicator bridge from
constant-normalizer weighted indicator sums and scaled indicator-sum
differences.
-/
def prospectiveScaledNormalizedCountIndicatorBridgeOfConstantWeight
    (cells : Finset Cell)
    (sample referenceSample : Index -> Finset Unit)
    (score referenceScore : Index -> Unit -> Cell)
    (normalizer referenceNormalizer scale : Index -> Real)
    (referenceLimit differenceLimit : Cell -> Real)
    (totalLimit totalDifferenceLimit : Real)
    (nonzeroTotalLimit scaledCellwiseCountRatioConvergence : Prop)
    (normalized_to_scaled_ratio :
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            referenceNormalizer index *
              (((referenceSample index).filter
                (fun unit => referenceScore index unit = cell)).card :
                Real))
          l (nhds (referenceLimit cell))) ->
      Tendsto
        (fun index =>
          normalizer index * ((sample index).card : Real))
        l (nhds totalLimit) ->
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (normalizer index *
                  (((sample index).filter
                    (fun unit => score index unit = cell)).card : Real) -
                referenceNormalizer index *
                  (((referenceSample index).filter
                    (fun unit => referenceScore index unit = cell)).card :
                    Real)))
          l (nhds (differenceLimit cell))) ->
      Tendsto
        (fun index =>
          scale index *
            (normalizer index * ((sample index).card : Real) -
              referenceNormalizer index *
                ((referenceSample index).card : Real)))
        l (nhds totalDifferenceLimit) ->
      nonzeroTotalLimit ->
      scaledCellwiseCountRatioConvergence) :
    ProspectiveScaledNormalizedCountIndicatorBridge Cell where
  count_bridge :=
    { cells := cells
      reference_normalized_count_lln :=
        ∀ cell, cell ∈ cells ->
          Tendsto
            (fun index =>
              referenceNormalizer index *
                (((referenceSample index).filter
                  (fun unit => referenceScore index unit = cell)).card :
                  Real))
            l (nhds (referenceLimit cell))
      normalized_sample_size_lln :=
        Tendsto
          (fun index =>
            normalizer index * ((sample index).card : Real))
          l (nhds totalLimit)
      scaled_normalized_cell_count_difference :=
        ∀ cell, cell ∈ cells ->
          Tendsto
            (fun index =>
              scale index *
                (normalizer index *
                    (((sample index).filter
                      (fun unit => score index unit = cell)).card : Real) -
                  referenceNormalizer index *
                    (((referenceSample index).filter
                      (fun unit =>
                        referenceScore index unit = cell)).card : Real)))
            l (nhds (differenceLimit cell))
      scaled_normalized_sample_size_difference :=
        Tendsto
          (fun index =>
            scale index *
              (normalizer index * ((sample index).card : Real) -
                referenceNormalizer index *
                  ((referenceSample index).card : Real)))
          l (nhds totalDifferenceLimit)
      nonzero_total_limit := nonzeroTotalLimit
      scaled_cellwise_count_ratio_convergence :=
        scaledCellwiseCountRatioConvergence
      bridge := normalized_to_scaled_ratio }
  weighted_reference_cell_indicator_sum_lln :=
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (referenceSample index)
            (fun _unit => referenceNormalizer index)
            (scoreCellIndicator (referenceScore index) cell))
        l (nhds (referenceLimit cell))
  weighted_total_indicator_sum_lln :=
    Tendsto
      (fun index =>
        weightedSampleSum (sample index)
          (fun _unit => normalizer index) (fun _unit => (1 : Real)))
      l (nhds totalLimit)
  scaled_weighted_cell_indicator_sum_difference :=
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sample index)
                (fun _unit => normalizer index)
                (scoreCellIndicator (score index) cell) -
              weightedSampleSum (referenceSample index)
                (fun _unit => referenceNormalizer index)
                (scoreCellIndicator (referenceScore index) cell)))
        l (nhds (differenceLimit cell))
  scaled_weighted_total_indicator_sum_difference :=
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleSum (sample index)
              (fun _unit => normalizer index) (fun _unit => (1 : Real)) -
            weightedSampleSum (referenceSample index)
              (fun _unit => referenceNormalizer index)
              (fun _unit => (1 : Real))))
      l (nhds totalDifferenceLimit)
  reference_indicator_to_normalized_count := by
    intro href cell hcell
    exact
      tendsto_normalized_cell_count_of_tendsto_weightedSampleSum_indicator_constant_weight
        (l := l) referenceSample referenceScore referenceNormalizer cell
        (referenceLimit cell) (href cell hcell)
  total_indicator_to_normalized_size := by
    intro htotal
    exact
      tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
        (l := l) sample normalizer totalLimit htotal
  scaled_cell_indicator_to_normalized_difference := by
    intro hcell cell hmem
    exact
      tendsto_scaled_normalized_cell_count_difference_of_tendsto_scaled_weightedSampleSum_indicator_difference_constant_weight
        (l := l) scale sample referenceSample score referenceScore
        normalizer referenceNormalizer cell (differenceLimit cell)
        (hcell cell hmem)
  scaled_total_indicator_to_normalized_difference := by
    intro htotal
    exact
      tendsto_scaled_normalized_total_count_difference_of_tendsto_scaled_weightedSampleSum_one_difference_constant_weight
        (l := l) scale sample referenceSample normalizer
        referenceNormalizer totalDifferenceLimit htotal

/--
Constant-normalizer indicator-sum inputs imply the scaled prospective
cellwise count-ratio conclusion through the supplied normalized-count bridge.
-/
theorem scaled_cellwise_count_ratio_convergence_of_indicator_tendsto_constant_weight
    (cells : Finset Cell)
    (sample referenceSample : Index -> Finset Unit)
    (score referenceScore : Index -> Unit -> Cell)
    (normalizer referenceNormalizer scale : Index -> Real)
    (referenceLimit differenceLimit : Cell -> Real)
    (totalLimit totalDifferenceLimit : Real)
    (nonzeroTotalLimit scaledCellwiseCountRatioConvergence : Prop)
    (normalized_to_scaled_ratio :
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            referenceNormalizer index *
              (((referenceSample index).filter
                (fun unit => referenceScore index unit = cell)).card :
                Real))
          l (nhds (referenceLimit cell))) ->
      Tendsto
        (fun index =>
          normalizer index * ((sample index).card : Real))
        l (nhds totalLimit) ->
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (normalizer index *
                  (((sample index).filter
                    (fun unit => score index unit = cell)).card : Real) -
                referenceNormalizer index *
                  (((referenceSample index).filter
                    (fun unit => referenceScore index unit = cell)).card :
                    Real)))
          l (nhds (differenceLimit cell))) ->
      Tendsto
        (fun index =>
          scale index *
            (normalizer index * ((sample index).card : Real) -
              referenceNormalizer index *
                ((referenceSample index).card : Real)))
        l (nhds totalDifferenceLimit) ->
      nonzeroTotalLimit ->
      scaledCellwiseCountRatioConvergence)
    (href :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (referenceSample index)
              (fun _unit => referenceNormalizer index)
              (scoreCellIndicator (referenceScore index) cell))
          l (nhds (referenceLimit cell)))
    (htotal :
      Tendsto
        (fun index =>
          weightedSampleSum (sample index)
            (fun _unit => normalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (sample index)
                  (fun _unit => normalizer index)
                  (scoreCellIndicator (score index) cell) -
                weightedSampleSum (referenceSample index)
                  (fun _unit => referenceNormalizer index)
                  (scoreCellIndicator (referenceScore index) cell)))
          l (nhds (differenceLimit cell)))
    (htotalScaled :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sample index)
                (fun _unit => normalizer index) (fun _unit => (1 : Real)) -
              weightedSampleSum (referenceSample index)
                (fun _unit => referenceNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds totalDifferenceLimit))
    (hnonzero : nonzeroTotalLimit) :
    scaledCellwiseCountRatioConvergence :=
  scaled_cellwise_count_ratio_convergence_of_prospective_indicator_sums
    (prospectiveScaledNormalizedCountIndicatorBridgeOfConstantWeight
      (l := l) cells sample referenceSample score referenceScore normalizer
      referenceNormalizer scale referenceLimit differenceLimit totalLimit
      totalDifferenceLimit nonzeroTotalLimit
      scaledCellwiseCountRatioConvergence normalized_to_scaled_ratio)
    href htotal hcell htotalScaled hnonzero

end WDSM
end Matching
end StatInference
