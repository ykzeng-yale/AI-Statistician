import StatInference.Matching.WDSM.FiniteCellIndicatorCLTInterfaces
import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceCenteredCrossMoment

/-!
# Centered-loading targets for finite score-cell CLT interfaces

The CLT interface layer indexes conclusions by centered second moments and
centered cross moments.  Stochastic array proofs often produce the same
quantities as ordinary cross moments of explicitly centered finite loadings, or
as covariance-kernel forms.  This module provides the deterministic rewrite
adapters between those target statements.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

/--
The finite score-cell linear-projection CLT bridge can be read with its
variance target written as an ordinary second cross moment of the centered
loading.
-/
theorem finite_score_cell_linear_projection_clt_with_centered_loading_crossMoment
    (b : FiniteScoreCellLinearProjectionCLTBridge Cell)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hclt : b.centered_weighted_indicator_array_clt) :
    b.clt_with_variance_target
      (scoreCellLoadingReferenceCrossMoment b.cells b.referenceShare
        (fun cell =>
          b.loading cell -
            scoreCellLoadingReferenceMean b.cells b.referenceShare b.loading)
        (fun cell =>
          b.loading cell -
            scoreCellLoadingReferenceMean b.cells b.referenceShare b.loading)) := by
  rw [scoreCellLoadingReferenceCrossMoment_center_self_eq_centeredSecondMoment]
  exact finite_score_cell_linear_projection_clt_of_bridge
    b hdesign hbounded hclt

/--
Under simplex reference shares, the finite score-cell linear-projection CLT
bridge can be read with the quadratic covariance-kernel target.
-/
theorem finite_score_cell_linear_projection_clt_with_linear_kernel
    (b : FiniteScoreCellLinearProjectionCLTBridge Cell)
    (hshare_sum : (∑ cell ∈ b.cells, b.referenceShare cell) = 1)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hclt : b.centered_weighted_indicator_array_clt) :
    b.clt_with_variance_target
      (scoreCellLinearCovarianceKernelForm
        b.cells b.referenceShare b.loading) := by
  rw [scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
    b.cells b.referenceShare b.loading hshare_sum]
  exact finite_score_cell_linear_projection_clt_of_bridge
    b hdesign hbounded hclt

/--
The finite score-cell bilinear CLT bridge can be read with its covariance
entry written as an ordinary cross moment of the two explicitly centered
loadings.
-/
theorem finite_score_cell_bilinear_covariance_clt_with_centered_loading_crossMoment
    (b : FiniteScoreCellBilinearCovarianceCLTBridge Cell)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hclt : b.joint_centered_weighted_indicator_array_clt) :
    b.covariance_entry_with_target
      (scoreCellLoadingReferenceCrossMoment b.cells b.referenceShare
        (fun cell =>
          b.loadingA cell -
            scoreCellLoadingReferenceMean b.cells b.referenceShare b.loadingA)
        (fun cell =>
          b.loadingB cell -
            scoreCellLoadingReferenceMean b.cells b.referenceShare b.loadingB)) := by
  rw [scoreCellLoadingReferenceCrossMoment_center_both_eq_centeredCrossMoment]
  exact finite_score_cell_bilinear_covariance_clt_of_bridge
    b hdesign hbounded hclt

/--
Under simplex reference shares, the finite score-cell bilinear CLT bridge can
be read with only the left loading explicitly centered.
-/
theorem finite_score_cell_bilinear_covariance_clt_with_left_centered_crossMoment
    (b : FiniteScoreCellBilinearCovarianceCLTBridge Cell)
    (hshare_sum : (∑ cell ∈ b.cells, b.referenceShare cell) = 1)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hclt : b.joint_centered_weighted_indicator_array_clt) :
    b.covariance_entry_with_target
      (scoreCellLoadingReferenceCrossMoment b.cells b.referenceShare
        (fun cell =>
          b.loadingA cell -
            scoreCellLoadingReferenceMean b.cells b.referenceShare b.loadingA)
        b.loadingB) := by
  rw [scoreCellLoadingReferenceCrossMoment_center_left_eq_centeredCrossMoment
    b.cells b.referenceShare b.loadingA b.loadingB hshare_sum]
  exact finite_score_cell_bilinear_covariance_clt_of_bridge
    b hdesign hbounded hclt

/--
Under simplex reference shares, the finite score-cell bilinear CLT bridge can
be read with only the right loading explicitly centered.
-/
theorem finite_score_cell_bilinear_covariance_clt_with_right_centered_crossMoment
    (b : FiniteScoreCellBilinearCovarianceCLTBridge Cell)
    (hshare_sum : (∑ cell ∈ b.cells, b.referenceShare cell) = 1)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hclt : b.joint_centered_weighted_indicator_array_clt) :
    b.covariance_entry_with_target
      (scoreCellLoadingReferenceCrossMoment b.cells b.referenceShare
        b.loadingA
        (fun cell =>
          b.loadingB cell -
            scoreCellLoadingReferenceMean b.cells b.referenceShare b.loadingB)) := by
  rw [scoreCellLoadingReferenceCrossMoment_center_right_eq_centeredCrossMoment
    b.cells b.referenceShare b.loadingA b.loadingB hshare_sum]
  exact finite_score_cell_bilinear_covariance_clt_of_bridge
    b hdesign hbounded hclt

/--
Under simplex reference shares, the finite score-cell bilinear CLT bridge can
be read directly with the bilinear covariance-kernel target.
-/
theorem finite_score_cell_bilinear_covariance_clt_with_bilinear_kernel
    (b : FiniteScoreCellBilinearCovarianceCLTBridge Cell)
    (hshare_sum : (∑ cell ∈ b.cells, b.referenceShare cell) = 1)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hclt : b.joint_centered_weighted_indicator_array_clt) :
    b.covariance_entry_with_target
      (scoreCellBilinearCovarianceKernelForm
        b.cells b.referenceShare b.loadingA b.loadingB) := by
  rw [finite_score_cell_bilinear_covariance_target_eq_kernel
    b.cells b.referenceShare b.loadingA b.loadingB hshare_sum]
  exact finite_score_cell_bilinear_covariance_clt_of_bridge
    b hdesign hbounded hclt

end WDSM
end Matching
end StatInference
