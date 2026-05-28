import StatInference.Matching.WDSM.ProspectiveNormalizedCountApproximationConvergence

/-!
# Prospective normalized-count stochastic interfaces for WDSM

The deterministic prospective route now reduces approximation negligibility to
normalized finite cell-count limits, normalized sample-size limits, and scaled
normalized-count differences.  This file records those remaining stochastic
claims as explicit named interfaces.  It does not prove an LLN or CLT; later
empirical-process or survey-sampling work should replace these bridge fields by
concrete theorems.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Cell : Type*} [DecidableEq Cell]

/--
Named bridge from prospective normalized count LLNs to ordinary fixed-cell
count-ratio convergence.
-/
structure ProspectiveNormalizedCountLLNBridge
    (Cell : Type*) [DecidableEq Cell] where
  cells : Finset Cell
  normalized_cell_count_lln : Prop
  normalized_sample_size_lln : Prop
  nonzero_total_limit : Prop
  cellwise_count_ratio_convergence : Prop
  bridge :
    normalized_cell_count_lln ->
    normalized_sample_size_lln ->
    nonzero_total_limit ->
    cellwise_count_ratio_convergence

theorem cellwise_count_ratio_convergence_of_prospective_normalized_count_lln
    (b : ProspectiveNormalizedCountLLNBridge Cell)
    (hcell : b.normalized_cell_count_lln)
    (hsize : b.normalized_sample_size_lln)
    (htotal : b.nonzero_total_limit) :
    b.cellwise_count_ratio_convergence :=
  b.bridge hcell hsize htotal

/--
Adapter from indicator-sum LLN statements to the normalized-count LLN interface.
The exact rewriting from normalized counts to constant-normalizer indicator
sums is proved in `ProspectiveNormalizedCountIndicatorBridge`; this adapter
records the remaining transfer functions at the stochastic-interface level.
-/
structure ProspectiveNormalizedCountIndicatorLLNBridge
    (Cell : Type*) [DecidableEq Cell] where
  count_bridge : ProspectiveNormalizedCountLLNBridge Cell
  weighted_cell_indicator_sum_lln : Prop
  weighted_total_indicator_sum_lln : Prop
  cell_indicator_to_normalized_count :
    weighted_cell_indicator_sum_lln ->
      count_bridge.normalized_cell_count_lln
  total_indicator_to_normalized_size :
    weighted_total_indicator_sum_lln ->
      count_bridge.normalized_sample_size_lln

theorem cellwise_count_ratio_convergence_of_prospective_indicator_sums
    (b : ProspectiveNormalizedCountIndicatorLLNBridge Cell)
    (hcell : b.weighted_cell_indicator_sum_lln)
    (hsize : b.weighted_total_indicator_sum_lln)
    (htotal : b.count_bridge.nonzero_total_limit) :
    b.count_bridge.cellwise_count_ratio_convergence :=
  cellwise_count_ratio_convergence_of_prospective_normalized_count_lln
    b.count_bridge
    (b.cell_indicator_to_normalized_count hcell)
    (b.total_indicator_to_normalized_size hsize)
    htotal

/--
Named bridge from prospective normalized count difference CLT/rate inputs to
scaled fixed-cell count-ratio convergence.
-/
structure ProspectiveScaledNormalizedCountBridge
    (Cell : Type*) [DecidableEq Cell] where
  cells : Finset Cell
  reference_normalized_count_lln : Prop
  normalized_sample_size_lln : Prop
  scaled_normalized_cell_count_difference : Prop
  scaled_normalized_sample_size_difference : Prop
  nonzero_total_limit : Prop
  scaled_cellwise_count_ratio_convergence : Prop
  bridge :
    reference_normalized_count_lln ->
    normalized_sample_size_lln ->
    scaled_normalized_cell_count_difference ->
    scaled_normalized_sample_size_difference ->
    nonzero_total_limit ->
    scaled_cellwise_count_ratio_convergence

theorem scaled_cellwise_count_ratio_convergence_of_prospective_normalized_counts
    (b : ProspectiveScaledNormalizedCountBridge Cell)
    (href : b.reference_normalized_count_lln)
    (hsize : b.normalized_sample_size_lln)
    (hcell : b.scaled_normalized_cell_count_difference)
    (htotalScaled : b.scaled_normalized_sample_size_difference)
    (htotal : b.nonzero_total_limit) :
    b.scaled_cellwise_count_ratio_convergence :=
  b.bridge href hsize hcell htotalScaled htotal

/--
Composition interface for unscaled PATE approximation negligibility from
prospective normalized count LLNs.
-/
structure PATEProspectiveNormalizedCountApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  count_bridge : ProspectiveNormalizedCountLLNBridge Cell
  finite_common_weight_conditions : Prop
  envelope_convergence : Prop
  pate_approximation_negligible : Prop
  deterministic_bridge :
    count_bridge.cellwise_count_ratio_convergence ->
    finite_common_weight_conditions ->
    envelope_convergence ->
    pate_approximation_negligible

theorem pate_approximation_negligible_of_prospective_normalized_counts
    (b : PATEProspectiveNormalizedCountApproximationBridge Cell)
    (hcell : b.count_bridge.normalized_cell_count_lln)
    (hsize : b.count_bridge.normalized_sample_size_lln)
    (htotal : b.count_bridge.nonzero_total_limit)
    (hfinite : b.finite_common_weight_conditions)
    (henvelope : b.envelope_convergence) :
    b.pate_approximation_negligible := by
  have hratio :
      b.count_bridge.cellwise_count_ratio_convergence :=
    cellwise_count_ratio_convergence_of_prospective_normalized_count_lln
      b.count_bridge hcell hsize htotal
  exact b.deterministic_bridge hratio hfinite henvelope

/--
Unscaled PATE approximation negligibility from indicator-sum LLNs routed
through the prospective normalized-count interface.
-/
theorem pate_approximation_negligible_of_prospective_indicator_sums
    (b : PATEProspectiveNormalizedCountApproximationBridge Cell)
    (indicator_bridge :
      ProspectiveNormalizedCountIndicatorLLNBridge Cell)
    (hcount :
      indicator_bridge.count_bridge = b.count_bridge)
    (hcell : indicator_bridge.weighted_cell_indicator_sum_lln)
    (hsize : indicator_bridge.weighted_total_indicator_sum_lln)
    (htotal : b.count_bridge.nonzero_total_limit)
    (hfinite : b.finite_common_weight_conditions)
    (henvelope : b.envelope_convergence) :
    b.pate_approximation_negligible := by
  have hratio :
      b.count_bridge.cellwise_count_ratio_convergence := by
    have hratioIndicator :
        indicator_bridge.count_bridge.cellwise_count_ratio_convergence :=
      cellwise_count_ratio_convergence_of_prospective_indicator_sums
        indicator_bridge hcell hsize
        (by simpa [hcount] using htotal)
    simpa [hcount] using hratioIndicator
  exact b.deterministic_bridge hratio hfinite henvelope

/--
Composition interface for scaled PATE approximation negligibility from
prospective normalized count LLN and scaled-difference inputs.
-/
structure ScaledPATEProspectiveNormalizedCountApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  count_bridge : ProspectiveScaledNormalizedCountBridge Cell
  finite_common_weight_conditions : Prop
  envelope_convergence : Prop
  scaled_pate_approximation_negligible : Prop
  deterministic_bridge :
    count_bridge.scaled_cellwise_count_ratio_convergence ->
    finite_common_weight_conditions ->
    envelope_convergence ->
    scaled_pate_approximation_negligible

theorem scaled_pate_approximation_negligible_of_prospective_normalized_counts
    (b : ScaledPATEProspectiveNormalizedCountApproximationBridge Cell)
    (href : b.count_bridge.reference_normalized_count_lln)
    (hsize : b.count_bridge.normalized_sample_size_lln)
    (hcell : b.count_bridge.scaled_normalized_cell_count_difference)
    (htotalScaled :
      b.count_bridge.scaled_normalized_sample_size_difference)
    (htotal : b.count_bridge.nonzero_total_limit)
    (hfinite : b.finite_common_weight_conditions)
    (henvelope : b.envelope_convergence) :
    b.scaled_pate_approximation_negligible := by
  have hratio :
      b.count_bridge.scaled_cellwise_count_ratio_convergence :=
    scaled_cellwise_count_ratio_convergence_of_prospective_normalized_counts
      b.count_bridge href hsize hcell htotalScaled htotal
  exact b.deterministic_bridge hratio hfinite henvelope

/--
Adapter from scaled indicator-sum inputs to the scaled prospective
normalized-count interface.
-/
structure ProspectiveScaledNormalizedCountIndicatorBridge
    (Cell : Type*) [DecidableEq Cell] where
  count_bridge : ProspectiveScaledNormalizedCountBridge Cell
  weighted_reference_cell_indicator_sum_lln : Prop
  weighted_total_indicator_sum_lln : Prop
  scaled_weighted_cell_indicator_sum_difference : Prop
  scaled_weighted_total_indicator_sum_difference : Prop
  reference_indicator_to_normalized_count :
    weighted_reference_cell_indicator_sum_lln ->
      count_bridge.reference_normalized_count_lln
  total_indicator_to_normalized_size :
    weighted_total_indicator_sum_lln ->
      count_bridge.normalized_sample_size_lln
  scaled_cell_indicator_to_normalized_difference :
    scaled_weighted_cell_indicator_sum_difference ->
      count_bridge.scaled_normalized_cell_count_difference
  scaled_total_indicator_to_normalized_difference :
    scaled_weighted_total_indicator_sum_difference ->
      count_bridge.scaled_normalized_sample_size_difference

theorem scaled_cellwise_count_ratio_convergence_of_prospective_indicator_sums
    (b : ProspectiveScaledNormalizedCountIndicatorBridge Cell)
    (href : b.weighted_reference_cell_indicator_sum_lln)
    (hsize : b.weighted_total_indicator_sum_lln)
    (hcell : b.scaled_weighted_cell_indicator_sum_difference)
    (htotalScaled : b.scaled_weighted_total_indicator_sum_difference)
    (htotal : b.count_bridge.nonzero_total_limit) :
    b.count_bridge.scaled_cellwise_count_ratio_convergence :=
  scaled_cellwise_count_ratio_convergence_of_prospective_normalized_counts
    b.count_bridge
    (b.reference_indicator_to_normalized_count href)
    (b.total_indicator_to_normalized_size hsize)
    (b.scaled_cell_indicator_to_normalized_difference hcell)
    (b.scaled_total_indicator_to_normalized_difference htotalScaled)
    htotal

/--
Scaled PATE approximation negligibility from scaled indicator-sum inputs routed
through the prospective normalized-count interface.
-/
theorem scaled_pate_approximation_negligible_of_prospective_indicator_sums
    (b : ScaledPATEProspectiveNormalizedCountApproximationBridge Cell)
    (indicator_bridge :
      ProspectiveScaledNormalizedCountIndicatorBridge Cell)
    (hcount :
      indicator_bridge.count_bridge = b.count_bridge)
    (href : indicator_bridge.weighted_reference_cell_indicator_sum_lln)
    (hsize : indicator_bridge.weighted_total_indicator_sum_lln)
    (hcell :
      indicator_bridge.scaled_weighted_cell_indicator_sum_difference)
    (htotalScaled :
      indicator_bridge.scaled_weighted_total_indicator_sum_difference)
    (htotal : b.count_bridge.nonzero_total_limit)
    (hfinite : b.finite_common_weight_conditions)
    (henvelope : b.envelope_convergence) :
    b.scaled_pate_approximation_negligible := by
  have hratio :
      b.count_bridge.scaled_cellwise_count_ratio_convergence := by
    have hratioIndicator :
        indicator_bridge.count_bridge.scaled_cellwise_count_ratio_convergence :=
      scaled_cellwise_count_ratio_convergence_of_prospective_indicator_sums
        indicator_bridge href hsize hcell htotalScaled
        (by simpa [hcount] using htotal)
    simpa [hcount] using hratioIndicator
  exact b.deterministic_bridge hratio hfinite henvelope

/--
PATE ordinary and scaled approximation negligibility from prospective
indicator-sum inputs, packaged as a single interface-level conclusion.
-/
theorem pate_ordinary_and_scaled_approximation_negligible_of_prospective_indicator_sums
    (ordinary : PATEProspectiveNormalizedCountApproximationBridge Cell)
    (scaled : ScaledPATEProspectiveNormalizedCountApproximationBridge Cell)
    (ordinary_indicator_bridge :
      ProspectiveNormalizedCountIndicatorLLNBridge Cell)
    (scaled_indicator_bridge :
      ProspectiveScaledNormalizedCountIndicatorBridge Cell)
    (hordinary_count :
      ordinary_indicator_bridge.count_bridge = ordinary.count_bridge)
    (hscaled_count :
      scaled_indicator_bridge.count_bridge = scaled.count_bridge)
    (hordinary_cell :
      ordinary_indicator_bridge.weighted_cell_indicator_sum_lln)
    (hordinary_size :
      ordinary_indicator_bridge.weighted_total_indicator_sum_lln)
    (hscaled_ref :
      scaled_indicator_bridge.weighted_reference_cell_indicator_sum_lln)
    (hscaled_size :
      scaled_indicator_bridge.weighted_total_indicator_sum_lln)
    (hscaled_cell :
      scaled_indicator_bridge.scaled_weighted_cell_indicator_sum_difference)
    (hscaled_total :
      scaled_indicator_bridge.scaled_weighted_total_indicator_sum_difference)
    (hordinary_total : ordinary.count_bridge.nonzero_total_limit)
    (hscaled_total_limit : scaled.count_bridge.nonzero_total_limit)
    (hordinary_finite : ordinary.finite_common_weight_conditions)
    (hordinary_envelope : ordinary.envelope_convergence)
    (hscaled_finite : scaled.finite_common_weight_conditions)
    (hscaled_envelope : scaled.envelope_convergence) :
    ordinary.pate_approximation_negligible ∧
      scaled.scaled_pate_approximation_negligible := by
  constructor
  · exact
      pate_approximation_negligible_of_prospective_indicator_sums
        ordinary ordinary_indicator_bridge hordinary_count hordinary_cell
        hordinary_size hordinary_total hordinary_finite hordinary_envelope
  · exact
      scaled_pate_approximation_negligible_of_prospective_indicator_sums
        scaled scaled_indicator_bridge hscaled_count hscaled_ref
        hscaled_size hscaled_cell hscaled_total hscaled_total_limit
        hscaled_finite hscaled_envelope

/--
Composition interface for unscaled PATT approximation negligibility from
prospective normalized count LLNs.
-/
structure PATTProspectiveNormalizedCountApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  count_bridge : ProspectiveNormalizedCountLLNBridge Cell
  finite_common_weight_conditions : Prop
  envelope_convergence : Prop
  patt_approximation_negligible : Prop
  deterministic_bridge :
    count_bridge.cellwise_count_ratio_convergence ->
    finite_common_weight_conditions ->
    envelope_convergence ->
    patt_approximation_negligible

theorem patt_approximation_negligible_of_prospective_normalized_counts
    (b : PATTProspectiveNormalizedCountApproximationBridge Cell)
    (hcell : b.count_bridge.normalized_cell_count_lln)
    (hsize : b.count_bridge.normalized_sample_size_lln)
    (htotal : b.count_bridge.nonzero_total_limit)
    (hfinite : b.finite_common_weight_conditions)
    (henvelope : b.envelope_convergence) :
    b.patt_approximation_negligible := by
  have hratio :
      b.count_bridge.cellwise_count_ratio_convergence :=
    cellwise_count_ratio_convergence_of_prospective_normalized_count_lln
      b.count_bridge hcell hsize htotal
  exact b.deterministic_bridge hratio hfinite henvelope

/--
Unscaled PATT approximation negligibility from indicator-sum LLNs routed
through the prospective normalized-count interface.
-/
theorem patt_approximation_negligible_of_prospective_indicator_sums
    (b : PATTProspectiveNormalizedCountApproximationBridge Cell)
    (indicator_bridge :
      ProspectiveNormalizedCountIndicatorLLNBridge Cell)
    (hcount :
      indicator_bridge.count_bridge = b.count_bridge)
    (hcell : indicator_bridge.weighted_cell_indicator_sum_lln)
    (hsize : indicator_bridge.weighted_total_indicator_sum_lln)
    (htotal : b.count_bridge.nonzero_total_limit)
    (hfinite : b.finite_common_weight_conditions)
    (henvelope : b.envelope_convergence) :
    b.patt_approximation_negligible := by
  have hratio :
      b.count_bridge.cellwise_count_ratio_convergence := by
    have hratioIndicator :
        indicator_bridge.count_bridge.cellwise_count_ratio_convergence :=
      cellwise_count_ratio_convergence_of_prospective_indicator_sums
        indicator_bridge hcell hsize
        (by simpa [hcount] using htotal)
    simpa [hcount] using hratioIndicator
  exact b.deterministic_bridge hratio hfinite henvelope

/--
Composition interface for scaled PATT approximation negligibility from
prospective normalized count LLN and scaled-difference inputs.
-/
structure ScaledPATTProspectiveNormalizedCountApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  count_bridge : ProspectiveScaledNormalizedCountBridge Cell
  finite_common_weight_conditions : Prop
  envelope_convergence : Prop
  scaled_patt_approximation_negligible : Prop
  deterministic_bridge :
    count_bridge.scaled_cellwise_count_ratio_convergence ->
    finite_common_weight_conditions ->
    envelope_convergence ->
    scaled_patt_approximation_negligible

theorem scaled_patt_approximation_negligible_of_prospective_normalized_counts
    (b : ScaledPATTProspectiveNormalizedCountApproximationBridge Cell)
    (href : b.count_bridge.reference_normalized_count_lln)
    (hsize : b.count_bridge.normalized_sample_size_lln)
    (hcell : b.count_bridge.scaled_normalized_cell_count_difference)
    (htotalScaled :
      b.count_bridge.scaled_normalized_sample_size_difference)
    (htotal : b.count_bridge.nonzero_total_limit)
    (hfinite : b.finite_common_weight_conditions)
    (henvelope : b.envelope_convergence) :
    b.scaled_patt_approximation_negligible := by
  have hratio :
      b.count_bridge.scaled_cellwise_count_ratio_convergence :=
    scaled_cellwise_count_ratio_convergence_of_prospective_normalized_counts
      b.count_bridge href hsize hcell htotalScaled htotal
  exact b.deterministic_bridge hratio hfinite henvelope

/--
Scaled PATT approximation negligibility from scaled indicator-sum inputs routed
through the prospective normalized-count interface.
-/
theorem scaled_patt_approximation_negligible_of_prospective_indicator_sums
    (b : ScaledPATTProspectiveNormalizedCountApproximationBridge Cell)
    (indicator_bridge :
      ProspectiveScaledNormalizedCountIndicatorBridge Cell)
    (hcount :
      indicator_bridge.count_bridge = b.count_bridge)
    (href : indicator_bridge.weighted_reference_cell_indicator_sum_lln)
    (hsize : indicator_bridge.weighted_total_indicator_sum_lln)
    (hcell :
      indicator_bridge.scaled_weighted_cell_indicator_sum_difference)
    (htotalScaled :
      indicator_bridge.scaled_weighted_total_indicator_sum_difference)
    (htotal : b.count_bridge.nonzero_total_limit)
    (hfinite : b.finite_common_weight_conditions)
    (henvelope : b.envelope_convergence) :
    b.scaled_patt_approximation_negligible := by
  have hratio :
      b.count_bridge.scaled_cellwise_count_ratio_convergence := by
    have hratioIndicator :
        indicator_bridge.count_bridge.scaled_cellwise_count_ratio_convergence :=
      scaled_cellwise_count_ratio_convergence_of_prospective_indicator_sums
        indicator_bridge href hsize hcell htotalScaled
        (by simpa [hcount] using htotal)
    simpa [hcount] using hratioIndicator
  exact b.deterministic_bridge hratio hfinite henvelope

/--
PATT ordinary and scaled approximation negligibility from prospective
indicator-sum inputs, packaged as a single interface-level conclusion.
-/
theorem patt_ordinary_and_scaled_approximation_negligible_of_prospective_indicator_sums
    (ordinary : PATTProspectiveNormalizedCountApproximationBridge Cell)
    (scaled : ScaledPATTProspectiveNormalizedCountApproximationBridge Cell)
    (ordinary_indicator_bridge :
      ProspectiveNormalizedCountIndicatorLLNBridge Cell)
    (scaled_indicator_bridge :
      ProspectiveScaledNormalizedCountIndicatorBridge Cell)
    (hordinary_count :
      ordinary_indicator_bridge.count_bridge = ordinary.count_bridge)
    (hscaled_count :
      scaled_indicator_bridge.count_bridge = scaled.count_bridge)
    (hordinary_cell :
      ordinary_indicator_bridge.weighted_cell_indicator_sum_lln)
    (hordinary_size :
      ordinary_indicator_bridge.weighted_total_indicator_sum_lln)
    (hscaled_ref :
      scaled_indicator_bridge.weighted_reference_cell_indicator_sum_lln)
    (hscaled_size :
      scaled_indicator_bridge.weighted_total_indicator_sum_lln)
    (hscaled_cell :
      scaled_indicator_bridge.scaled_weighted_cell_indicator_sum_difference)
    (hscaled_total :
      scaled_indicator_bridge.scaled_weighted_total_indicator_sum_difference)
    (hordinary_total : ordinary.count_bridge.nonzero_total_limit)
    (hscaled_total_limit : scaled.count_bridge.nonzero_total_limit)
    (hordinary_finite : ordinary.finite_common_weight_conditions)
    (hordinary_envelope : ordinary.envelope_convergence)
    (hscaled_finite : scaled.finite_common_weight_conditions)
    (hscaled_envelope : scaled.envelope_convergence) :
    ordinary.patt_approximation_negligible ∧
      scaled.scaled_patt_approximation_negligible := by
  constructor
  · exact
      patt_approximation_negligible_of_prospective_indicator_sums
        ordinary ordinary_indicator_bridge hordinary_count hordinary_cell
        hordinary_size hordinary_total hordinary_finite hordinary_envelope
  · exact
      scaled_patt_approximation_negligible_of_prospective_indicator_sums
        scaled scaled_indicator_bridge hscaled_count hscaled_ref
        hscaled_size hscaled_cell hscaled_total hscaled_total_limit
        hscaled_finite hscaled_envelope

/--
Paired PATE/PATT ordinary and scaled approximation negligibility from
prospective indicator-sum inputs.
-/
theorem pate_patt_ordinary_and_scaled_approximation_negligible_of_prospective_indicator_sums
    (pate_ordinary : PATEProspectiveNormalizedCountApproximationBridge Cell)
    (pate_scaled :
      ScaledPATEProspectiveNormalizedCountApproximationBridge Cell)
    (patt_ordinary : PATTProspectiveNormalizedCountApproximationBridge Cell)
    (patt_scaled :
      ScaledPATTProspectiveNormalizedCountApproximationBridge Cell)
    (pate_ordinary_indicator_bridge :
      ProspectiveNormalizedCountIndicatorLLNBridge Cell)
    (pate_scaled_indicator_bridge :
      ProspectiveScaledNormalizedCountIndicatorBridge Cell)
    (patt_ordinary_indicator_bridge :
      ProspectiveNormalizedCountIndicatorLLNBridge Cell)
    (patt_scaled_indicator_bridge :
      ProspectiveScaledNormalizedCountIndicatorBridge Cell)
    (hpate_ordinary_count :
      pate_ordinary_indicator_bridge.count_bridge =
        pate_ordinary.count_bridge)
    (hpate_scaled_count :
      pate_scaled_indicator_bridge.count_bridge =
        pate_scaled.count_bridge)
    (hpatt_ordinary_count :
      patt_ordinary_indicator_bridge.count_bridge =
        patt_ordinary.count_bridge)
    (hpatt_scaled_count :
      patt_scaled_indicator_bridge.count_bridge =
        patt_scaled.count_bridge)
    (hpate_ordinary_cell :
      pate_ordinary_indicator_bridge.weighted_cell_indicator_sum_lln)
    (hpate_ordinary_size :
      pate_ordinary_indicator_bridge.weighted_total_indicator_sum_lln)
    (hpate_scaled_ref :
      pate_scaled_indicator_bridge.weighted_reference_cell_indicator_sum_lln)
    (hpate_scaled_size :
      pate_scaled_indicator_bridge.weighted_total_indicator_sum_lln)
    (hpate_scaled_cell :
      pate_scaled_indicator_bridge.scaled_weighted_cell_indicator_sum_difference)
    (hpate_scaled_total :
      pate_scaled_indicator_bridge.scaled_weighted_total_indicator_sum_difference)
    (hpatt_ordinary_cell :
      patt_ordinary_indicator_bridge.weighted_cell_indicator_sum_lln)
    (hpatt_ordinary_size :
      patt_ordinary_indicator_bridge.weighted_total_indicator_sum_lln)
    (hpatt_scaled_ref :
      patt_scaled_indicator_bridge.weighted_reference_cell_indicator_sum_lln)
    (hpatt_scaled_size :
      patt_scaled_indicator_bridge.weighted_total_indicator_sum_lln)
    (hpatt_scaled_cell :
      patt_scaled_indicator_bridge.scaled_weighted_cell_indicator_sum_difference)
    (hpatt_scaled_total :
      patt_scaled_indicator_bridge.scaled_weighted_total_indicator_sum_difference)
    (hpate_ordinary_total :
      pate_ordinary.count_bridge.nonzero_total_limit)
    (hpate_scaled_total_limit :
      pate_scaled.count_bridge.nonzero_total_limit)
    (hpatt_ordinary_total :
      patt_ordinary.count_bridge.nonzero_total_limit)
    (hpatt_scaled_total_limit :
      patt_scaled.count_bridge.nonzero_total_limit)
    (hpate_ordinary_finite :
      pate_ordinary.finite_common_weight_conditions)
    (hpate_ordinary_envelope : pate_ordinary.envelope_convergence)
    (hpate_scaled_finite : pate_scaled.finite_common_weight_conditions)
    (hpate_scaled_envelope : pate_scaled.envelope_convergence)
    (hpatt_ordinary_finite :
      patt_ordinary.finite_common_weight_conditions)
    (hpatt_ordinary_envelope : patt_ordinary.envelope_convergence)
    (hpatt_scaled_finite : patt_scaled.finite_common_weight_conditions)
    (hpatt_scaled_envelope : patt_scaled.envelope_convergence) :
    pate_ordinary.pate_approximation_negligible ∧
      pate_scaled.scaled_pate_approximation_negligible ∧
      patt_ordinary.patt_approximation_negligible ∧
      patt_scaled.scaled_patt_approximation_negligible := by
  have hpate :
      pate_ordinary.pate_approximation_negligible ∧
        pate_scaled.scaled_pate_approximation_negligible :=
    pate_ordinary_and_scaled_approximation_negligible_of_prospective_indicator_sums
      pate_ordinary pate_scaled pate_ordinary_indicator_bridge
      pate_scaled_indicator_bridge hpate_ordinary_count hpate_scaled_count
      hpate_ordinary_cell hpate_ordinary_size hpate_scaled_ref
      hpate_scaled_size hpate_scaled_cell hpate_scaled_total
      hpate_ordinary_total hpate_scaled_total_limit
      hpate_ordinary_finite hpate_ordinary_envelope hpate_scaled_finite
      hpate_scaled_envelope
  have hpatt :
      patt_ordinary.patt_approximation_negligible ∧
        patt_scaled.scaled_patt_approximation_negligible :=
    patt_ordinary_and_scaled_approximation_negligible_of_prospective_indicator_sums
      patt_ordinary patt_scaled patt_ordinary_indicator_bridge
      patt_scaled_indicator_bridge hpatt_ordinary_count hpatt_scaled_count
      hpatt_ordinary_cell hpatt_ordinary_size hpatt_scaled_ref
      hpatt_scaled_size hpatt_scaled_cell hpatt_scaled_total
      hpatt_ordinary_total hpatt_scaled_total_limit
      hpatt_ordinary_finite hpatt_ordinary_envelope hpatt_scaled_finite
      hpatt_scaled_envelope
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

/--
PATE ordinary and scaled approximation negligibility from prospective
normalized-count inputs.
-/
theorem pate_ordinary_and_scaled_approximation_negligible_of_prospective_normalized_counts
    (ordinary : PATEProspectiveNormalizedCountApproximationBridge Cell)
    (scaled : ScaledPATEProspectiveNormalizedCountApproximationBridge Cell)
    (hcell : ordinary.count_bridge.normalized_cell_count_lln)
    (hsize : ordinary.count_bridge.normalized_sample_size_lln)
    (htotal : ordinary.count_bridge.nonzero_total_limit)
    (href : scaled.count_bridge.reference_normalized_count_lln)
    (hscaled_size : scaled.count_bridge.normalized_sample_size_lln)
    (hscaled_cell :
      scaled.count_bridge.scaled_normalized_cell_count_difference)
    (hscaled_total :
      scaled.count_bridge.scaled_normalized_sample_size_difference)
    (hscaled_total_limit : scaled.count_bridge.nonzero_total_limit)
    (hfinite : ordinary.finite_common_weight_conditions)
    (henvelope : ordinary.envelope_convergence)
    (hscaled_finite : scaled.finite_common_weight_conditions)
    (hscaled_envelope : scaled.envelope_convergence) :
    ordinary.pate_approximation_negligible ∧
      scaled.scaled_pate_approximation_negligible := by
  constructor
  · exact
      pate_approximation_negligible_of_prospective_normalized_counts
        ordinary hcell hsize htotal hfinite henvelope
  · exact
      scaled_pate_approximation_negligible_of_prospective_normalized_counts
        scaled href hscaled_size hscaled_cell hscaled_total
        hscaled_total_limit hscaled_finite hscaled_envelope

/--
PATT ordinary and scaled approximation negligibility from prospective
normalized-count inputs.
-/
theorem patt_ordinary_and_scaled_approximation_negligible_of_prospective_normalized_counts
    (ordinary : PATTProspectiveNormalizedCountApproximationBridge Cell)
    (scaled : ScaledPATTProspectiveNormalizedCountApproximationBridge Cell)
    (hcell : ordinary.count_bridge.normalized_cell_count_lln)
    (hsize : ordinary.count_bridge.normalized_sample_size_lln)
    (htotal : ordinary.count_bridge.nonzero_total_limit)
    (href : scaled.count_bridge.reference_normalized_count_lln)
    (hscaled_size : scaled.count_bridge.normalized_sample_size_lln)
    (hscaled_cell :
      scaled.count_bridge.scaled_normalized_cell_count_difference)
    (hscaled_total :
      scaled.count_bridge.scaled_normalized_sample_size_difference)
    (hscaled_total_limit : scaled.count_bridge.nonzero_total_limit)
    (hfinite : ordinary.finite_common_weight_conditions)
    (henvelope : ordinary.envelope_convergence)
    (hscaled_finite : scaled.finite_common_weight_conditions)
    (hscaled_envelope : scaled.envelope_convergence) :
    ordinary.patt_approximation_negligible ∧
      scaled.scaled_patt_approximation_negligible := by
  constructor
  · exact
      patt_approximation_negligible_of_prospective_normalized_counts
        ordinary hcell hsize htotal hfinite henvelope
  · exact
      scaled_patt_approximation_negligible_of_prospective_normalized_counts
        scaled href hscaled_size hscaled_cell hscaled_total
        hscaled_total_limit hscaled_finite hscaled_envelope

/--
Paired PATE/PATT ordinary and scaled approximation negligibility from
prospective normalized-count inputs.
-/
theorem pate_patt_ordinary_and_scaled_approximation_negligible_of_prospective_normalized_counts
    (pate_ordinary : PATEProspectiveNormalizedCountApproximationBridge Cell)
    (pate_scaled :
      ScaledPATEProspectiveNormalizedCountApproximationBridge Cell)
    (patt_ordinary : PATTProspectiveNormalizedCountApproximationBridge Cell)
    (patt_scaled :
      ScaledPATTProspectiveNormalizedCountApproximationBridge Cell)
    (hpate_cell : pate_ordinary.count_bridge.normalized_cell_count_lln)
    (hpate_size : pate_ordinary.count_bridge.normalized_sample_size_lln)
    (hpate_total : pate_ordinary.count_bridge.nonzero_total_limit)
    (hpate_ref : pate_scaled.count_bridge.reference_normalized_count_lln)
    (hpate_scaled_size :
      pate_scaled.count_bridge.normalized_sample_size_lln)
    (hpate_scaled_cell :
      pate_scaled.count_bridge.scaled_normalized_cell_count_difference)
    (hpate_scaled_total :
      pate_scaled.count_bridge.scaled_normalized_sample_size_difference)
    (hpate_scaled_total_limit :
      pate_scaled.count_bridge.nonzero_total_limit)
    (hpatt_cell : patt_ordinary.count_bridge.normalized_cell_count_lln)
    (hpatt_size : patt_ordinary.count_bridge.normalized_sample_size_lln)
    (hpatt_total : patt_ordinary.count_bridge.nonzero_total_limit)
    (hpatt_ref : patt_scaled.count_bridge.reference_normalized_count_lln)
    (hpatt_scaled_size :
      patt_scaled.count_bridge.normalized_sample_size_lln)
    (hpatt_scaled_cell :
      patt_scaled.count_bridge.scaled_normalized_cell_count_difference)
    (hpatt_scaled_total :
      patt_scaled.count_bridge.scaled_normalized_sample_size_difference)
    (hpatt_scaled_total_limit :
      patt_scaled.count_bridge.nonzero_total_limit)
    (hpate_finite : pate_ordinary.finite_common_weight_conditions)
    (hpate_envelope : pate_ordinary.envelope_convergence)
    (hpate_scaled_finite : pate_scaled.finite_common_weight_conditions)
    (hpate_scaled_envelope : pate_scaled.envelope_convergence)
    (hpatt_finite : patt_ordinary.finite_common_weight_conditions)
    (hpatt_envelope : patt_ordinary.envelope_convergence)
    (hpatt_scaled_finite : patt_scaled.finite_common_weight_conditions)
    (hpatt_scaled_envelope : patt_scaled.envelope_convergence) :
    pate_ordinary.pate_approximation_negligible ∧
      pate_scaled.scaled_pate_approximation_negligible ∧
      patt_ordinary.patt_approximation_negligible ∧
      patt_scaled.scaled_patt_approximation_negligible := by
  have hpate :
      pate_ordinary.pate_approximation_negligible ∧
        pate_scaled.scaled_pate_approximation_negligible :=
    pate_ordinary_and_scaled_approximation_negligible_of_prospective_normalized_counts
      pate_ordinary pate_scaled hpate_cell hpate_size hpate_total hpate_ref
      hpate_scaled_size hpate_scaled_cell hpate_scaled_total
      hpate_scaled_total_limit hpate_finite hpate_envelope
      hpate_scaled_finite hpate_scaled_envelope
  have hpatt :
      patt_ordinary.patt_approximation_negligible ∧
        patt_scaled.scaled_patt_approximation_negligible :=
    patt_ordinary_and_scaled_approximation_negligible_of_prospective_normalized_counts
      patt_ordinary patt_scaled hpatt_cell hpatt_size hpatt_total hpatt_ref
      hpatt_scaled_size hpatt_scaled_cell hpatt_scaled_total
      hpatt_scaled_total_limit hpatt_finite hpatt_envelope
      hpatt_scaled_finite hpatt_scaled_envelope
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

end WDSM
end Matching
end StatInference
