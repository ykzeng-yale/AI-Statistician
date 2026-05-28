import StatInference.Matching.WDSM.FiniteCellIndicatorCLTInterfaces
import StatInference.Matching.WDSM.IndicatorSumConvergenceInterfaces

/-!
# From finite score-cell indicator CLTs to WDSM approximation bridges

The deterministic approximation layer already reduces scaled PATE/PATT
approximation negligibility to weighted indicator LLNs plus a scaled
indicator-sum difference CLT.  This module connects that remaining scaled CLT
input to the finite score-cell vector CLT interface.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators Topology

variable {Cell : Type*} [DecidableEq Cell]

/--
Composition bridge from a finite score-cell vector CLT to the scaled PATE
indicator-sum approximation bridge.
-/
structure ScaledPATEFiniteScoreCellCLTApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  vector_clt_bridge : FiniteScoreCellVectorCLTBridge Cell
  indicator_bridge : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge
  vector_clt_to_scaled_indicator_difference :
    vector_clt_bridge.finite_dimensional_score_cell_vector_clt ->
      indicator_bridge.scaled_weighted_indicator_sum_difference_clt

theorem scaled_pate_approximation_negligible_of_finite_score_cell_clt
    (b : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (hsimplex : b.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix : b.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hfinite : b.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.indicator_bridge.envelope_convergence)
    (hlln : b.indicator_bridge.weighted_indicator_sum_lln) :
    b.indicator_bridge.scaled_pate_double_score_approximation_negligible := by
  have hvector :
      b.vector_clt_bridge.finite_dimensional_score_cell_vector_clt :=
    finite_score_cell_vector_clt_of_bridge
      b.vector_clt_bridge hsimplex hlinear hmatrix
  have hscaled :
      b.indicator_bridge.scaled_weighted_indicator_sum_difference_clt :=
    b.vector_clt_to_scaled_indicator_difference hvector
  exact scaled_pate_double_score_approximation_negligible_of_indicator_bridge
    b.indicator_bridge hfinite henvelope hlln hscaled

/--
Composition bridge from an already packaged finite score-cell vector CLT to the
scaled PATE indicator-sum approximation bridge.
-/
theorem scaled_pate_approximation_negligible_of_finite_score_cell_vector_clt
    (b : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (hvector : b.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (hfinite : b.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.indicator_bridge.envelope_convergence)
    (hlln : b.indicator_bridge.weighted_indicator_sum_lln) :
    b.indicator_bridge.scaled_pate_double_score_approximation_negligible := by
  have hscaled :
      b.indicator_bridge.scaled_weighted_indicator_sum_difference_clt :=
    b.vector_clt_to_scaled_indicator_difference hvector
  exact scaled_pate_double_score_approximation_negligible_of_indicator_bridge
    b.indicator_bridge hfinite henvelope hlln hscaled

/--
Build a scaled PATE finite-cell CLT bridge whose vector layer is backed by
Mathlib iid scalar projection CLTs for every loading.
-/
def scaledPATEFiniteScoreCellCLTApproximationBridgeOfIidScalarProjections
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    (P : Measure Ω) (P' : Measure Ω')
    [IsProbabilityMeasure P] [IsProbabilityMeasure P']
    (X : (Cell -> Real) -> ℕ -> Ω -> Real)
    (Y : (Cell -> Real) -> Ω' -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          TendstoInDistribution
            (fun (n : ℕ) (ω : Ω) =>
              (√(n : Real))⁻¹ *
                ((∑ k ∈ Finset.range n, X loading k ω) -
                  (n : Real) * ∫ x, X loading 0 x ∂P))
            atTop (Y loading) (fun _ : ℕ => P) P') ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (indicatorBridge : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge)
    (vectorCLTToScaledIndicatorDifference :
      finiteDimensionalScoreCellVectorCLT ->
        indicatorBridge.scaled_weighted_indicator_sum_difference_clt) :
    ScaledPATEFiniteScoreCellCLTApproximationBridge Cell where
  vector_clt_bridge :=
    finiteScoreCellVectorCLTBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold
  indicator_bridge := indicatorBridge
  vector_clt_to_scaled_indicator_difference :=
    vectorCLTToScaledIndicatorDifference

/--
Scaled PATE approximation negligibility from Mathlib iid scalar projection
CLTs, plus explicit Cramer-Wold and vector-to-scaled transfer maps.
-/
theorem scaled_pate_approximation_negligible_of_iid_scalar_projection_clt
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    (P : Measure Ω) (P' : Measure Ω')
    [IsProbabilityMeasure P] [IsProbabilityMeasure P']
    (X : (Cell -> Real) -> ℕ -> Ω -> Real)
    (Y : (Cell -> Real) -> Ω' -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          TendstoInDistribution
            (fun (n : ℕ) (ω : Ω) =>
              (√(n : Real))⁻¹ *
                ((∑ k ∈ Finset.range n, X loading k ω) -
                  (n : Real) * ∫ x, X loading 0 x ∂P))
            atTop (Y loading) (fun _ : ℕ => P) P') ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (indicatorBridge : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge)
    (vectorCLTToScaledIndicatorDifference :
      finiteDimensionalScoreCellVectorCLT ->
        indicatorBridge.scaled_weighted_indicator_sum_difference_clt)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (hindep : ∀ loading, iIndepFun (X loading) P)
    (hident :
      ∀ loading i, IdentDistrib (X loading i) (X loading 0) P P)
    (hmem : ∀ loading, MemLp (X loading 0) 2 P)
    (hY :
      ∀ loading,
        HasLaw (Y loading)
          (gaussianReal 0
            (scoreCellLoadingReferenceCenteredSecondMoment
              cells referenceShare loading).toNNReal)
          P')
    (hvariance :
      ∀ loading,
        variance (X loading 0) P =
          scoreCellLoadingReferenceCenteredSecondMoment
            cells referenceShare loading)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hlln : indicatorBridge.weighted_indicator_sum_lln) :
    indicatorBridge.scaled_pate_double_score_approximation_negligible :=
  scaled_pate_approximation_negligible_of_finite_score_cell_vector_clt
    (scaledPATEFiniteScoreCellCLTApproximationBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold indicatorBridge vectorCLTToScaledIndicatorDifference)
    (finite_score_cell_vector_clt_of_iid_scalar_projection_bridge
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold hsimplex hmatrix hindep hident hmem hY hvariance)
    hfinite henvelope hlln

/--
Composition bridge from a finite score-cell vector CLT to the scaled PATT
indicator-sum approximation bridge.
-/
structure ScaledPATTFiniteScoreCellCLTApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  vector_clt_bridge : FiniteScoreCellVectorCLTBridge Cell
  indicator_bridge : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge
  vector_clt_to_scaled_indicator_difference :
    vector_clt_bridge.finite_dimensional_score_cell_vector_clt ->
      indicator_bridge.scaled_weighted_indicator_sum_difference_clt

theorem scaled_patt_approximation_negligible_of_finite_score_cell_clt
    (b : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (hsimplex : b.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix : b.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hfinite : b.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.indicator_bridge.envelope_convergence)
    (hlln : b.indicator_bridge.weighted_indicator_sum_lln) :
    b.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  have hvector :
      b.vector_clt_bridge.finite_dimensional_score_cell_vector_clt :=
    finite_score_cell_vector_clt_of_bridge
      b.vector_clt_bridge hsimplex hlinear hmatrix
  have hscaled :
      b.indicator_bridge.scaled_weighted_indicator_sum_difference_clt :=
    b.vector_clt_to_scaled_indicator_difference hvector
  exact scaled_patt_double_score_approximation_negligible_of_indicator_bridge
    b.indicator_bridge hfinite henvelope hlln hscaled

/--
Composition bridge from an already packaged finite score-cell vector CLT to the
scaled PATT indicator-sum approximation bridge.
-/
theorem scaled_patt_approximation_negligible_of_finite_score_cell_vector_clt
    (b : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (hvector : b.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (hfinite : b.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.indicator_bridge.envelope_convergence)
    (hlln : b.indicator_bridge.weighted_indicator_sum_lln) :
    b.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  have hscaled :
      b.indicator_bridge.scaled_weighted_indicator_sum_difference_clt :=
    b.vector_clt_to_scaled_indicator_difference hvector
  exact scaled_patt_double_score_approximation_negligible_of_indicator_bridge
    b.indicator_bridge hfinite henvelope hlln hscaled

/--
Build a scaled PATT finite-cell CLT bridge whose vector layer is backed by
Mathlib iid scalar projection CLTs for every loading.
-/
def scaledPATTFiniteScoreCellCLTApproximationBridgeOfIidScalarProjections
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    (P : Measure Ω) (P' : Measure Ω')
    [IsProbabilityMeasure P] [IsProbabilityMeasure P']
    (X : (Cell -> Real) -> ℕ -> Ω -> Real)
    (Y : (Cell -> Real) -> Ω' -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          TendstoInDistribution
            (fun (n : ℕ) (ω : Ω) =>
              (√(n : Real))⁻¹ *
                ((∑ k ∈ Finset.range n, X loading k ω) -
                  (n : Real) * ∫ x, X loading 0 x ∂P))
            atTop (Y loading) (fun _ : ℕ => P) P') ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (indicatorBridge : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge)
    (vectorCLTToScaledIndicatorDifference :
      finiteDimensionalScoreCellVectorCLT ->
        indicatorBridge.scaled_weighted_indicator_sum_difference_clt) :
    ScaledPATTFiniteScoreCellCLTApproximationBridge Cell where
  vector_clt_bridge :=
    finiteScoreCellVectorCLTBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold
  indicator_bridge := indicatorBridge
  vector_clt_to_scaled_indicator_difference :=
    vectorCLTToScaledIndicatorDifference

/--
Scaled PATT approximation negligibility from Mathlib iid scalar projection
CLTs, plus explicit Cramer-Wold and vector-to-scaled transfer maps.
-/
theorem scaled_patt_approximation_negligible_of_iid_scalar_projection_clt
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    (P : Measure Ω) (P' : Measure Ω')
    [IsProbabilityMeasure P] [IsProbabilityMeasure P']
    (X : (Cell -> Real) -> ℕ -> Ω -> Real)
    (Y : (Cell -> Real) -> Ω' -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          TendstoInDistribution
            (fun (n : ℕ) (ω : Ω) =>
              (√(n : Real))⁻¹ *
                ((∑ k ∈ Finset.range n, X loading k ω) -
                  (n : Real) * ∫ x, X loading 0 x ∂P))
            atTop (Y loading) (fun _ : ℕ => P) P') ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (indicatorBridge : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge)
    (vectorCLTToScaledIndicatorDifference :
      finiteDimensionalScoreCellVectorCLT ->
        indicatorBridge.scaled_weighted_indicator_sum_difference_clt)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (hindep : ∀ loading, iIndepFun (X loading) P)
    (hident :
      ∀ loading i, IdentDistrib (X loading i) (X loading 0) P P)
    (hmem : ∀ loading, MemLp (X loading 0) 2 P)
    (hY :
      ∀ loading,
        HasLaw (Y loading)
          (gaussianReal 0
            (scoreCellLoadingReferenceCenteredSecondMoment
              cells referenceShare loading).toNNReal)
          P')
    (hvariance :
      ∀ loading,
        variance (X loading 0) P =
          scoreCellLoadingReferenceCenteredSecondMoment
            cells referenceShare loading)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hlln : indicatorBridge.weighted_indicator_sum_lln) :
    indicatorBridge.scaled_patt_double_score_approximation_negligible :=
  scaled_patt_approximation_negligible_of_finite_score_cell_vector_clt
    (scaledPATTFiniteScoreCellCLTApproximationBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold indicatorBridge vectorCLTToScaledIndicatorDifference)
    (finite_score_cell_vector_clt_of_iid_scalar_projection_bridge
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold hsimplex hmatrix hindep hident hmem hY hvariance)
    hfinite henvelope hlln

/--
Paired scaled PATE/PATT approximation negligibility from finite score-cell
vector CLTs.
-/
theorem scaled_pate_patt_approximation_negligible_of_finite_score_cell_clt
    (pate : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (patt : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (hpate_simplex : pate.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      pate.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      pate.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_finite : pate.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope : pate.indicator_bridge.envelope_convergence)
    (hpate_lln : pate.indicator_bridge.weighted_indicator_sum_lln)
    (hpatt_simplex : patt.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      patt.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      patt.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_finite : patt.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope : patt.indicator_bridge.envelope_convergence)
    (hpatt_lln : patt.indicator_bridge.weighted_indicator_sum_lln) :
    pate.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      patt.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  constructor
  · exact
      scaled_pate_approximation_negligible_of_finite_score_cell_clt
        pate hpate_simplex hpate_linear hpate_matrix hpate_finite
        hpate_envelope hpate_lln
  · exact
      scaled_patt_approximation_negligible_of_finite_score_cell_clt
        patt hpatt_simplex hpatt_linear hpatt_matrix hpatt_finite
        hpatt_envelope hpatt_lln

/--
Paired scaled PATE/PATT approximation negligibility from already packaged
finite score-cell vector CLTs.
-/
theorem scaled_pate_patt_approximation_negligible_of_finite_score_cell_vector_clt
    (pate : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (patt : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (hpate_vector :
      pate.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (hpate_finite : pate.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope : pate.indicator_bridge.envelope_convergence)
    (hpate_lln : pate.indicator_bridge.weighted_indicator_sum_lln)
    (hpatt_vector :
      patt.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (hpatt_finite : patt.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope : patt.indicator_bridge.envelope_convergence)
    (hpatt_lln : patt.indicator_bridge.weighted_indicator_sum_lln) :
    pate.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      patt.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  constructor
  · exact
      scaled_pate_approximation_negligible_of_finite_score_cell_vector_clt
        pate hpate_vector hpate_finite hpate_envelope hpate_lln
  · exact
      scaled_patt_approximation_negligible_of_finite_score_cell_vector_clt
        patt hpatt_vector hpatt_finite hpatt_envelope hpatt_lln

end WDSM
end Matching
end StatInference
