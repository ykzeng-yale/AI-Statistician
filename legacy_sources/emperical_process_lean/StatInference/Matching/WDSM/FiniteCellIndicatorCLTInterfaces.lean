import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceMatrix

/-!
# Finite score-cell indicator CLT interfaces for WDSM

The preceding modules prove the deterministic covariance targets for finite
score-cell indicator vectors.  This module records the remaining stochastic
CLT layer as explicit bridge assumptions, so later probability work can replace
the interfaces with concrete survey-weighted finite-dimensional CLT proofs.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Cell : Type*} [DecidableEq Cell]

/--
Named bridge for a finite score-cell linear-projection CLT.

The conclusion is indexed by the verified variance target, namely the
reference-share centered second moment of the cell loading.
-/
structure FiniteScoreCellLinearProjectionCLTBridge
    (Cell : Type*) [DecidableEq Cell] where
  cells : Finset Cell
  referenceShare : Cell -> Real
  loading : Cell -> Real
  survey_design_regularity : Prop
  bounded_score_cell_indicators : Prop
  centered_weighted_indicator_array_clt : Prop
  clt_with_variance_target : Real -> Prop
  bridge :
    survey_design_regularity ->
    bounded_score_cell_indicators ->
    centered_weighted_indicator_array_clt ->
    clt_with_variance_target
      (scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading)

theorem finite_score_cell_linear_projection_clt_of_bridge
    (b : FiniteScoreCellLinearProjectionCLTBridge Cell)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hclt : b.centered_weighted_indicator_array_clt) :
    b.clt_with_variance_target
      (scoreCellLoadingReferenceCenteredSecondMoment
        b.cells b.referenceShare b.loading) :=
  b.bridge hdesign hbounded hclt

/--
The linear-projection variance target is the diagonal of the bilinear
covariance-kernel form under simplex reference shares.
-/
theorem finite_score_cell_linear_projection_variance_target_eq_bilinear_kernel
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm
        cells referenceShare loading loading =
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading := by
  rw [scoreCellBilinearCovarianceKernelForm_self_eq_linear]
  rw [scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
    cells referenceShare loading hshare_sum]

/--
Named bridge for one finite score-cell covariance entry in a
finite-dimensional CLT.

The conclusion is indexed by the verified covariance target, namely the
reference-share centered cross moment of two loadings.
-/
structure FiniteScoreCellBilinearCovarianceCLTBridge
    (Cell : Type*) [DecidableEq Cell] where
  cells : Finset Cell
  referenceShare : Cell -> Real
  loadingA : Cell -> Real
  loadingB : Cell -> Real
  survey_design_regularity : Prop
  bounded_score_cell_indicators : Prop
  joint_centered_weighted_indicator_array_clt : Prop
  covariance_entry_with_target : Real -> Prop
  bridge :
    survey_design_regularity ->
    bounded_score_cell_indicators ->
    joint_centered_weighted_indicator_array_clt ->
    covariance_entry_with_target
      (scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB)

theorem finite_score_cell_bilinear_covariance_clt_of_bridge
    (b : FiniteScoreCellBilinearCovarianceCLTBridge Cell)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hclt : b.joint_centered_weighted_indicator_array_clt) :
    b.covariance_entry_with_target
      (scoreCellLoadingReferenceCenteredCrossMoment
        b.cells b.referenceShare b.loadingA b.loadingB) :=
  b.bridge hdesign hbounded hclt

/--
The bilinear covariance target is exactly the covariance-kernel entry induced
by two loadings under simplex reference shares.
-/
theorem finite_score_cell_bilinear_covariance_target_eq_kernel
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB =
      scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB := by
  exact scoreCellBilinearCovarianceKernelForm_eq_centeredCrossMoment
    cells referenceShare loadingA loadingB hshare_sum

/--
Named Cramer-Wold bridge for the full finite score-cell indicator vector CLT.

The deterministic covariance matrix has already been verified by the previous
finite algebra modules; this interface isolates the remaining stochastic
finite-dimensional convergence proof.
-/
structure FiniteScoreCellVectorCLTBridge
    (Cell : Type*) [DecidableEq Cell] where
  cells : Finset Cell
  referenceShare : Cell -> Real
  simplex_reference_shares : Prop
  all_linear_projection_clts_with_verified_variance : Prop
  covariance_matrix_tangent_space_verified : Prop
  finite_dimensional_score_cell_vector_clt : Prop
  bridge :
    simplex_reference_shares ->
    all_linear_projection_clts_with_verified_variance ->
    covariance_matrix_tangent_space_verified ->
    finite_dimensional_score_cell_vector_clt

theorem finite_score_cell_vector_clt_of_bridge
    (b : FiniteScoreCellVectorCLTBridge Cell)
    (hsimplex : b.simplex_reference_shares)
    (hlinear : b.all_linear_projection_clts_with_verified_variance)
    (hmatrix : b.covariance_matrix_tangent_space_verified) :
    b.finite_dimensional_score_cell_vector_clt :=
  b.bridge hsimplex hlinear hmatrix

end WDSM
end Matching
end StatInference
