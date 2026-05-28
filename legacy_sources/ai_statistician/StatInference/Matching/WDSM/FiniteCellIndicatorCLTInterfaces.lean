import Mathlib.Probability.CentralLimitTheorem
import Mathlib.MeasureTheory.Measure.LevyConvergence
import Mathlib.Analysis.InnerProductSpace.PiL2
import Mathlib.MeasureTheory.Function.SpecialFunctions.Inner
import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceMatrix
import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionLindebergRatio
import StatInference.Matching.WDSM.FiniteCellIndicatorSimplexBounds

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

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators Topology RealInnerProductSpace

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
Concrete iid scalar CLT bridge for one fixed finite score-cell linear
projection.

This is deliberately narrower than the WDSM survey-design CLT: it uses
mathlib's iid real CLT for a scalar sequence `X`, and verifies the variance
target against the finite score-cell centered-second-moment formula.
-/
def finiteScoreCellLinearProjectionCLTBridgeOfIidScalar
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    (P : Measure Ω) (P' : Measure Ω')
    [IsProbabilityMeasure P] [IsProbabilityMeasure P']
    (X : ℕ -> Ω -> Real) (Y : Ω' -> Real) :
    FiniteScoreCellLinearProjectionCLTBridge Cell where
  cells := cells
  referenceShare := referenceShare
  loading := loading
  survey_design_regularity :=
    iIndepFun X P ∧ ∀ i, IdentDistrib (X i) (X 0) P P
  bounded_score_cell_indicators := MemLp (X 0) 2 P
  centered_weighted_indicator_array_clt :=
    HasLaw Y
      (gaussianReal 0
        (scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading).toNNReal)
      P' ∧
      variance (X 0) P =
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading
  clt_with_variance_target := fun _varianceTarget =>
    TendstoInDistribution
      (fun (n : ℕ) (ω : Ω) =>
        (√(n : Real))⁻¹ *
          ((∑ k ∈ Finset.range n, X k ω) -
            (n : Real) * ∫ x, X 0 x ∂P))
      atTop Y (fun _ : ℕ => P) P'
  bridge := by
    intro hdesign hbounded hclt
    rcases hdesign with ⟨hindep, hident⟩
    rcases hclt with ⟨hY, hvariance⟩
    have hYVar :
        HasLaw Y (gaussianReal 0 (variance (X 0) P).toNNReal) P' := by
      simpa [hvariance] using hY
    exact
      tendstoInDistribution_inv_sqrt_mul_sum_sub
        hYVar hbounded hindep hident

/--
The iid scalar bridge discharges the finite score-cell linear-projection CLT
interface when the fixed projection is modeled as an iid real sequence.
-/
theorem finite_score_cell_linear_projection_clt_of_iid_scalar_mathlib
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    (P : Measure Ω) (P' : Measure Ω')
    [IsProbabilityMeasure P] [IsProbabilityMeasure P']
    (X : ℕ -> Ω -> Real) (Y : Ω' -> Real)
    (hindep : iIndepFun X P)
    (hident : ∀ i, IdentDistrib (X i) (X 0) P P)
    (hmem : MemLp (X 0) 2 P)
    (hY :
      HasLaw Y
        (gaussianReal 0
          (scoreCellLoadingReferenceCenteredSecondMoment
            cells referenceShare loading).toNNReal)
        P')
    (hvariance :
      variance (X 0) P =
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading) :
    (finiteScoreCellLinearProjectionCLTBridgeOfIidScalar
      cells referenceShare loading P P' X Y).clt_with_variance_target
        (scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading) :=
  finite_score_cell_linear_projection_clt_of_bridge
    (finiteScoreCellLinearProjectionCLTBridgeOfIidScalar
      cells referenceShare loading P P' X Y)
    ⟨hindep, hident⟩ hmem ⟨hY, hvariance⟩

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

/--
Finite-dimensional Lévy route for a vector CLT.

For a finite-dimensional real inner-product vector target, convergence of the
vector characteristic functions gives convergence in distribution.  This is
the checked Mathlib boundary just below a Cramer-Wold/vector CLT: the remaining
WDSM survey-design work is to prove the characteristic-function convergence for
the centered finite score-cell vector, not to assume vector convergence itself.
-/
theorem finiteDimensional_tendstoInDistribution_of_charFun_convergence
    {E Ω Ω' : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    (sampleLaw : ℕ -> Measure Ω) (limitLaw : Measure Ω')
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (X : ℕ -> Ω -> E) (Z : Ω' -> E)
    (hX : ∀ n, AEMeasurable (X n) (sampleLaw n))
    (hZ : AEMeasurable Z limitLaw)
    (hchar :
      ∀ t : E,
        Tendsto
          (fun n => charFun ((sampleLaw n).map (X n)) t)
          atTop (nhds (charFun (limitLaw.map Z) t))) :
    TendstoInDistribution X atTop Z sampleLaw limitLaw := by
  refine ⟨hX, hZ, ?_⟩
  exact
    ProbabilityMeasure.tendsto_of_tendsto_charFun
      (μ := fun n =>
        ⟨(sampleLaw n).map (X n),
          Measure.isProbabilityMeasure_map (hX n)⟩)
      (μ₀ :=
        ⟨limitLaw.map Z,
          Measure.isProbabilityMeasure_map hZ⟩)
      hchar

/--
Finite-dimensional vector convergence in distribution is equivalent to
pointwise convergence of characteristic functions, once the source and limit
maps are a.e.-measurable.
-/
theorem finiteDimensional_tendstoInDistribution_iff_charFun_convergence
    {E Ω Ω' : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    (sampleLaw : ℕ -> Measure Ω) (limitLaw : Measure Ω')
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (X : ℕ -> Ω -> E) (Z : Ω' -> E)
    (hX : ∀ n, AEMeasurable (X n) (sampleLaw n))
    (hZ : AEMeasurable Z limitLaw) :
    TendstoInDistribution X atTop Z sampleLaw limitLaw ↔
      ∀ t : E,
        Tendsto
          (fun n => charFun ((sampleLaw n).map (X n)) t)
          atTop (nhds (charFun (limitLaw.map Z) t)) := by
  constructor
  · intro h t
    simpa using
      (ProbabilityMeasure.tendsto_iff_tendsto_charFun.mp h.tendsto t)
  · intro hchar
    exact
      finiteDimensional_tendstoInDistribution_of_charFun_convergence
        sampleLaw limitLaw X Z hX hZ hchar

/--
The vector characteristic function at direction `t` is the scalar
characteristic function at frequency `1` of the inner-product projection onto
`t`.
-/
theorem charFun_map_eq_scalar_projection_charFun_one
    {E Ω : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [MeasurableSpace E] [BorelSpace E] [MeasurableSpace Ω]
    (μ : Measure Ω) (X : Ω -> E)
    (hX : AEMeasurable X μ) (t : E) :
    charFun (μ.map X) t =
      charFun (μ.map (fun ω => ⟪X ω, t⟫)) (1 : Real) := by
  rw [charFun_apply, charFun_apply]
  rw [integral_map hX]
  · rw [integral_map]
    · simp
    · exact
        (continuous_id.inner continuous_const).aemeasurable.comp_aemeasurable hX
    · fun_prop
  · fun_prop

/--
Finite-dimensional vector convergence follows from characteristic-function
convergence of every scalar inner-product projection.

This is the checked Cramer-Wold hinge used by the finite-cell CLT lane: the
remaining survey-design work can be stated as scalar projection characteristic
function convergence, rather than as a completed vector CLT.
-/
theorem finiteDimensional_tendstoInDistribution_of_scalar_projection_charFun_convergence
    {E Ω Ω' : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    (sampleLaw : ℕ -> Measure Ω) (limitLaw : Measure Ω')
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (X : ℕ -> Ω -> E) (Z : Ω' -> E)
    (hX : ∀ n, AEMeasurable (X n) (sampleLaw n))
    (hZ : AEMeasurable Z limitLaw)
    (hscalar :
      ∀ t : E,
        Tendsto
          (fun n =>
            charFun ((sampleLaw n).map (fun ω => ⟪X n ω, t⟫)) (1 : Real))
          atTop
          (nhds
            (charFun (limitLaw.map (fun ω => ⟪Z ω, t⟫)) (1 : Real)))) :
    TendstoInDistribution X atTop Z sampleLaw limitLaw :=
  finiteDimensional_tendstoInDistribution_of_charFun_convergence
    sampleLaw limitLaw X Z hX hZ
    (fun t => by
      have hleft :
          (fun n => charFun ((sampleLaw n).map (X n)) t) =
            fun n =>
              charFun ((sampleLaw n).map (fun ω => ⟪X n ω, t⟫))
                (1 : Real) := by
        funext n
        exact charFun_map_eq_scalar_projection_charFun_one
          (sampleLaw n) (X n) (hX n) t
      have hright :
          charFun (limitLaw.map Z) t =
            charFun (limitLaw.map (fun ω => ⟪Z ω, t⟫)) (1 : Real) :=
        charFun_map_eq_scalar_projection_charFun_one limitLaw Z hZ t
      simpa [hleft, hright] using hscalar t)

/--
Finite-dimensional vector convergence follows from convergence in distribution
of every scalar inner-product projection.

This is the Cramer-Wold-style boundary in the language already used by the
scalar CLT interfaces: each direction `t` supplies an ordinary real
`TendstoInDistribution` statement, and Mathlib's real Lévy theorem converts it
to the characteristic-function convergence needed by the vector Lévy route.
-/
theorem finiteDimensional_tendstoInDistribution_of_scalar_projection_tendstoInDistribution
    {E Ω Ω' : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    (sampleLaw : ℕ -> Measure Ω) (limitLaw : Measure Ω')
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (X : ℕ -> Ω -> E) (Z : Ω' -> E)
    (hX : ∀ n, AEMeasurable (X n) (sampleLaw n))
    (hZ : AEMeasurable Z limitLaw)
    (hscalar :
      ∀ t : E,
        TendstoInDistribution
          (fun n sample => ⟪X n sample, t⟫)
          atTop
          (fun sample => ⟪Z sample, t⟫)
          sampleLaw limitLaw) :
    TendstoInDistribution X atTop Z sampleLaw limitLaw :=
  finiteDimensional_tendstoInDistribution_of_scalar_projection_charFun_convergence
    sampleLaw limitLaw X Z hX hZ
    (fun t =>
      (ProbabilityMeasure.tendsto_iff_tendsto_charFun.mp
        (hscalar t).tendsto) (1 : Real))

/--
Finite score-cell vector bridge whose stochastic input is vector
characteristic-function convergence.

The `all_linear_projection_clts_with_verified_variance` field is instantiated
as convergence of the vector characteristic function in every inner-product
direction.  By Mathlib's finite-dimensional Lévy theorem this is enough to
produce the finite-dimensional vector convergence in distribution.  The
survey-design work is therefore reduced to proving the displayed
characteristic-function convergence for the centered finite score-cell vector.
-/
def finiteScoreCellVectorCLTBridgeOfCharFunConvergence
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {E Sample LimitSample : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (vector : ℕ -> Sample -> E) (limitVector : LimitSample -> E)
    (hvector : ∀ n, AEMeasurable (vector n) (sampleLaw n))
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop) :
    FiniteScoreCellVectorCLTBridge Cell where
  cells := cells
  referenceShare := referenceShare
  simplex_reference_shares := simplexReferenceShares
  all_linear_projection_clts_with_verified_variance :=
    ∀ t : E,
      Tendsto
        (fun n => charFun ((sampleLaw n).map (vector n)) t)
        atTop (nhds (charFun (limitLaw.map limitVector) t))
  covariance_matrix_tangent_space_verified :=
    covarianceMatrixTangentSpaceVerified
  finite_dimensional_score_cell_vector_clt :=
    TendstoInDistribution vector atTop limitVector sampleLaw limitLaw
  bridge := by
    intro _hsimplex hchar _hmatrix
    exact
      finiteDimensional_tendstoInDistribution_of_charFun_convergence
        sampleLaw limitLaw vector limitVector hvector hlimitVector hchar

/--
All-direction vector characteristic-function convergence discharges the
finite-dimensional score-cell vector CLT field through the characteristic-
function bridge.
-/
theorem finite_score_cell_vector_clt_of_charFun_convergence_bridge
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {E Sample LimitSample : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (vector : ℕ -> Sample -> E) (limitVector : LimitSample -> E)
    (hvector : ∀ n, AEMeasurable (vector n) (sampleLaw n))
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (hchar :
      ∀ t : E,
        Tendsto
          (fun n => charFun ((sampleLaw n).map (vector n)) t)
          atTop (nhds (charFun (limitLaw.map limitVector) t))) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_bridge
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified)
    hsimplex hchar hmatrix

/--
Scalar inner-product projection characteristic-function convergence also
discharges the finite-dimensional score-cell vector CLT field.  This is the
explicit Cramer-Wold-style handoff from one-dimensional projection evidence to
the vector characteristic-function bridge.
-/
theorem finite_score_cell_vector_clt_of_scalar_projection_charFun_convergence_bridge
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {E Sample LimitSample : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (vector : ℕ -> Sample -> E) (limitVector : LimitSample -> E)
    (hvector : ∀ n, AEMeasurable (vector n) (sampleLaw n))
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (hscalar :
      ∀ t : E,
        Tendsto
          (fun n =>
            charFun ((sampleLaw n).map (fun sample =>
              ⟪vector n sample, t⟫)) (1 : Real))
          atTop
          (nhds
            (charFun (limitLaw.map (fun sample =>
              ⟪limitVector sample, t⟫)) (1 : Real)))) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_charFun_convergence_bridge
    cells referenceShare sampleLaw limitLaw vector limitVector hvector
    hlimitVector simplexReferenceShares covarianceMatrixTangentSpaceVerified
    hsimplex hmatrix
    (fun t => by
      have hleft :
          (fun n => charFun ((sampleLaw n).map (vector n)) t) =
            fun n =>
              charFun ((sampleLaw n).map (fun sample =>
                ⟪vector n sample, t⟫)) (1 : Real) := by
        funext n
        exact charFun_map_eq_scalar_projection_charFun_one
          (sampleLaw n) (vector n) (hvector n) t
      have hright :
          charFun (limitLaw.map limitVector) t =
            charFun (limitLaw.map (fun sample =>
              ⟪limitVector sample, t⟫)) (1 : Real) :=
        charFun_map_eq_scalar_projection_charFun_one
          limitLaw limitVector hlimitVector t
      simpa [hleft, hright] using hscalar t)

/--
Scalar inner-product projection CLTs discharge the finite-dimensional score-cell
vector CLT field.  This packages the Cramer-Wold-style handoff in terms of the
same real `TendstoInDistribution` statements produced by scalar CLT adapters.
-/
theorem finite_score_cell_vector_clt_of_scalar_projection_tendstoInDistribution_bridge
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {E Sample LimitSample : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (vector : ℕ -> Sample -> E) (limitVector : LimitSample -> E)
    (hvector : ∀ n, AEMeasurable (vector n) (sampleLaw n))
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (hscalar :
      ∀ t : E,
        TendstoInDistribution
          (fun n sample => ⟪vector n sample, t⟫)
          atTop
          (fun sample => ⟪limitVector sample, t⟫)
          sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_scalar_projection_charFun_convergence_bridge
    cells referenceShare sampleLaw limitLaw vector limitVector hvector
    hlimitVector simplexReferenceShares covarianceMatrixTangentSpaceVerified
    hsimplex hmatrix
    (fun t =>
      (ProbabilityMeasure.tendsto_iff_tendsto_charFun.mp
        (hscalar t).tendsto) (1 : Real))

/--
Concrete scalar survey-design projection CLT statement for one loading.

This is the finite-cell vector-CLT boundary made explicit: the limit variable
has Gaussian law with the already verified centered-second-moment variance
target, and the centered survey projection converges to that variable in
distribution.
-/
def centeredScoreCellLinearProjectionCLTWithVerifiedVariance
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (loading : Cell -> Real) : Prop :=
  HasLaw (limitProjection loading)
      (gaussianReal 0
        (scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading).toNNReal)
      limitLaw ∧
    TendstoInDistribution
      (fun index sample => centeredProjection loading index sample)
      l (limitProjection loading) sampleLaw limitLaw

omit [DecidableEq Cell] in
/--
A constant-zero real random variable has the degenerate Gaussian law
`gaussianReal 0 0` under any probability law.
-/
theorem hasLaw_const_zero_gaussianReal_zero_var
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P] :
    HasLaw (fun _sample : Ω => (0 : Real)) (gaussianReal 0 0) P := by
  refine ⟨by fun_prop, ?_⟩
  simp [Measure.map_const]

omit [DecidableEq Cell] in
/--
Constant-zero real variables converge in distribution to the constant-zero
limit under arbitrary probability laws.  This avoids treating a degenerate
projection as a stochastic CLT premise.
-/
theorem tendstoInDistribution_const_zero_real
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw] :
    TendstoInDistribution
      (fun _index (_sample : Sample) => (0 : Real))
      l (fun _sample : LimitSample => (0 : Real)) sampleLaw limitLaw := by
  refine ⟨fun _index => by fun_prop, by fun_prop, ?_⟩
  have hsource :
      (fun index =>
        (⟨(sampleLaw index).map
          (fun _sample : Sample => (0 : Real)),
          Measure.isProbabilityMeasure_map
            (by
              fun_prop :
              AEMeasurable (fun _sample : Sample => (0 : Real))
                (sampleLaw index))⟩ : ProbabilityMeasure Real)) =
        (fun _index : Index =>
          (⟨Measure.dirac (0 : Real), inferInstance⟩ :
            ProbabilityMeasure Real)) := by
    funext index
    ext measurableSet
    simp [Measure.map_const]
  have htarget :
      (⟨limitLaw.map (fun _sample : LimitSample => (0 : Real)),
        Measure.isProbabilityMeasure_map
          (by
            fun_prop :
            AEMeasurable (fun _sample : LimitSample => (0 : Real))
              limitLaw)⟩ : ProbabilityMeasure Real) =
        (⟨Measure.dirac (0 : Real), inferInstance⟩ :
          ProbabilityMeasure Real) := by
    ext measurableSet
    simp [Measure.map_const]
  rw [hsource, htarget]
  exact tendsto_const_nhds

omit [DecidableEq Cell] in
/--
Deterministic zero projections discharge the scalar finite-cell projection
CLT bridge.

This covers any degenerate loading whose verified variance target is zero,
provided the finite-sample projection and the proposed limit projection are
pointwise zero.  The theorem removes such directions from the genuine
survey-design scalar CLT burden; it only uses the degenerate Gaussian law and
constant-zero convergence in distribution.
-/
theorem centeredScoreCellLinearProjectionCLTWithVerifiedVariance_of_pointwise_zero
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (hvariance :
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading = 0)
    (hsource_zero :
      ∀ index sample, centeredProjection loading index sample = 0)
    (hlimit_zero :
      ∀ sample, limitProjection loading sample = 0) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection loading := by
  constructor
  · have hlimit_ae :
        limitProjection loading =ᵐ[limitLaw]
          fun _sample : LimitSample => (0 : Real) :=
      ae_of_all _ hlimit_zero
    have hlaw :
        HasLaw (limitProjection loading)
          (gaussianReal 0 0) limitLaw :=
      (hasLaw_const_zero_gaussianReal_zero_var limitLaw).congr hlimit_ae
    simpa [hvariance] using hlaw
  · have hsource_ae :
        ∀ index,
          (fun _sample : Sample => (0 : Real)) =ᵐ[sampleLaw index]
            (fun sample => centeredProjection loading index sample) := by
      intro index
      exact ae_of_all _ fun sample => by
        symm
        exact hsource_zero index sample
    have hlimit_ae :
        (fun _sample : LimitSample => (0 : Real)) =ᵐ[limitLaw]
          limitProjection loading :=
      ae_of_all _ fun sample => by
        symm
        exact hlimit_zero sample
    exact
      (tendstoInDistribution_const_zero_real l sampleLaw limitLaw).congr
        hsource_ae hlimit_ae

omit [DecidableEq Cell] in
/--
The reference-share mean of any finite-cell loading can be written as a sum
over the active cell subtype.
-/
theorem scoreCellLoadingReferenceMean_eq_activeCellSum
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    scoreCellLoadingReferenceMean cells referenceShare loading =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 * loading cellIndex.1 := by
  unfold scoreCellLoadingReferenceMean
  simpa using
    (Finset.sum_attach cells
      (fun cell => referenceShare cell * loading cell)).symm

omit [DecidableEq Cell] in
/--
The verified scalar variance target for any finite-cell loading can be written
entirely on the active cell subtype.
-/
theorem scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare loading =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (loading cellIndex.1 -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * loading other.1) ^ 2 := by
  unfold scoreCellLoadingReferenceCenteredSecondMoment
  rw [scoreCellLoadingReferenceMean_eq_activeCellSum]
  simpa using
    (Finset.sum_attach cells (fun cell =>
      referenceShare cell *
        (loading cell -
          ∑ other : {cell // cell ∈ cells},
            referenceShare other.1 * loading other.1) ^ 2)).symm

omit [DecidableEq Cell] in
/--
Under nonnegative reference shares, the nonnegative real variance parameter
used by `gaussianReal` is exactly the verified finite-cell centered second
moment, not a truncation artifact.
-/
theorem scoreCellGaussianVarianceParameter_toNNReal_eq_centeredSecondMoment_mk
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell) :
    (scoreCellLoadingReferenceCenteredSecondMoment
      cells referenceShare loading).toNNReal =
      ⟨scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading,
        scoreCellLoadingReferenceCenteredSecondMoment_nonneg
          cells referenceShare loading hshare_nonneg⟩ := by
  exact Real.toNNReal_of_nonneg
    (scoreCellLoadingReferenceCenteredSecondMoment_nonneg
      cells referenceShare loading hshare_nonneg)

omit [DecidableEq Cell] in
/--
For a strictly positive verified centered second moment, the Gaussian variance
parameter is the corresponding positive `NNReal`, with no truncation premise.
-/
theorem scoreCellGaussianVarianceParameter_toNNReal_eq_positive_mk
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hvariance_pos :
      0 <
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading) :
    (scoreCellLoadingReferenceCenteredSecondMoment
      cells referenceShare loading).toNNReal =
      ⟨scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading,
        le_of_lt hvariance_pos⟩ := by
  exact Real.toNNReal_of_nonneg (le_of_lt hvariance_pos)

omit [DecidableEq Cell] in
/--
As a real number, the Gaussian variance parameter equals the verified
finite-cell centered second moment under nonnegative reference shares.
-/
theorem scoreCellGaussianVarianceParameter_coe_eq_centeredSecondMoment
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell) :
    ((scoreCellLoadingReferenceCenteredSecondMoment
      cells referenceShare loading).toNNReal : Real) =
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading := by
  exact Real.coe_toNNReal
    (scoreCellLoadingReferenceCenteredSecondMoment
      cells referenceShare loading)
    (scoreCellLoadingReferenceCenteredSecondMoment_nonneg
      cells referenceShare loading hshare_nonneg)

/--
Canonical-limit version of the fixed scalar iid projection CLT.

The limit space is `Real` equipped with the Gaussian law whose variance is the
verified finite-cell centered second moment, and the limit variable is the
identity.  This removes the auxiliary `HasLaw Y ...` premise from the fixed
scalar iid route; it is still only a scalar iid theorem, not the WDSM
survey-design/vector CLT.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_verified_variance_of_iid_scalar_mathlib_canonical_gaussian
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> Real)
    (hindep : iIndepFun X P)
    (hident : ∀ i, IdentDistrib (X i) (X 0) P P)
    (hmem : MemLp (X 0) 2 P)
    (hvariance :
      variance (X 0) P =
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare atTop (fun _ : ℕ => P)
      (gaussianReal 0
        (scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading).toNNReal)
      (fun _loading (n : ℕ) (ω : Ω) =>
        (√(n : Real))⁻¹ *
          ((∑ k ∈ Finset.range n, X k ω) -
            (n : Real) * ∫ x, X 0 x ∂P))
      (fun _loading (z : Real) => z) loading := by
  refine ⟨?_, ?_⟩
  · exact ProbabilityTheory.HasLaw.id
  · exact
      finite_score_cell_linear_projection_clt_of_iid_scalar_mathlib
        cells referenceShare loading P
        (gaussianReal 0
        (scoreCellLoadingReferenceCenteredSecondMoment
            cells referenceShare loading).toNNReal)
        X (fun z : Real => z) hindep hident hmem
        ProbabilityTheory.HasLaw.id hvariance

/--
Canonical-limit fixed scalar iid CLT with a positive `NNReal` Gaussian
variance parameter.

This is the Mathlib iid special case of the positive-variance scalar boundary:
the limit law is `gaussianReal 0 ⟨variance, hvariance_pos.le⟩`, not a
truncated `.toNNReal` presentation.  It remains an iid scalar theorem and does
not cover the WDSM survey-design triangular-array CLT.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_positive_nnreal_variance_of_iid_scalar_mathlib_canonical_gaussian
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> Real)
    (hindep : iIndepFun X P)
    (hident : ∀ i, IdentDistrib (X i) (X 0) P P)
    (hmem : MemLp (X 0) 2 P)
    (hvariance :
      variance (X 0) P =
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading)
    (hvariance_pos :
      0 <
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare atTop (fun _ : ℕ => P)
      (gaussianReal 0
        ⟨scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading, le_of_lt hvariance_pos⟩)
      (fun _loading (n : ℕ) (ω : Ω) =>
        (√(n : Real))⁻¹ *
          ((∑ k ∈ Finset.range n, X k ω) -
            (n : Real) * ∫ x, X 0 x ∂P))
      (fun _loading (z : Real) => z) loading := by
  refine ⟨?_, ?_⟩
  · simpa [
      scoreCellGaussianVarianceParameter_toNNReal_eq_positive_mk
        cells referenceShare loading hvariance_pos]
      using
        (ProbabilityTheory.HasLaw.id :
          HasLaw (fun z : Real => z)
            (gaussianReal 0
              ⟨scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading, le_of_lt hvariance_pos⟩)
            (gaussianReal 0
              ⟨scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading, le_of_lt hvariance_pos⟩))
  · exact
      finite_score_cell_linear_projection_clt_of_iid_scalar_mathlib
        cells referenceShare loading P
        (gaussianReal 0
          ⟨scoreCellLoadingReferenceCenteredSecondMoment
            cells referenceShare loading, le_of_lt hvariance_pos⟩)
        X (fun z : Real => z) hindep hident hmem
        (by
          simpa [hvariance,
            scoreCellGaussianVarianceParameter_toNNReal_eq_positive_mk
              cells referenceShare loading hvariance_pos]
            using
              (ProbabilityTheory.HasLaw.id :
                HasLaw (fun z : Real => z)
                  (gaussianReal 0
                    ⟨scoreCellLoadingReferenceCenteredSecondMoment
                      cells referenceShare loading, le_of_lt hvariance_pos⟩)
                  (gaussianReal 0
                    ⟨scoreCellLoadingReferenceCenteredSecondMoment
                      cells referenceShare loading, le_of_lt hvariance_pos⟩)))
        hvariance

/--
Canonical-limit iid scalar CLT with the variance premise stated as the active
finite-cell centered second moment.

This is the Mathlib iid scalar subroute with the same active variance formula
used by the survey-design boundary.  It still assumes iid scalar observations
and therefore does not prove the WDSM survey-design triangular-array CLT.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_active_variance_of_iid_scalar_mathlib_canonical_gaussian
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> Real)
    (hindep : iIndepFun X P)
    (hident : ∀ i, IdentDistrib (X i) (X 0) P P)
    (hmem : MemLp (X 0) 2 P)
    (hvariance :
      variance (X 0) P =
        ∑ cellIndex : {cell // cell ∈ cells},
          referenceShare cellIndex.1 *
            (loading cellIndex.1 -
              ∑ other : {cell // cell ∈ cells},
                referenceShare other.1 * loading other.1) ^ 2) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare atTop (fun _ : ℕ => P)
      (gaussianReal 0
        ((∑ cellIndex : {cell // cell ∈ cells},
          referenceShare cellIndex.1 *
            (loading cellIndex.1 -
              ∑ other : {cell // cell ∈ cells},
                referenceShare other.1 * loading other.1) ^ 2).toNNReal))
      (fun _loading (n : ℕ) (ω : Ω) =>
        (√(n : Real))⁻¹ *
          ((∑ k ∈ Finset.range n, X k ω) -
            (n : Real) * ∫ x, X 0 x ∂P))
      (fun _loading (z : Real) => z) loading := by
  simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
    using
      centered_scoreCellLinearProjection_clt_with_verified_variance_of_iid_scalar_mathlib_canonical_gaussian
        cells referenceShare loading P X hindep hident hmem
        (by
          simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
            using hvariance)

/--
All-loading scalar finite score-cell CLTs give the vector CLT once every
inner-product direction of the vector is represented by a finite-cell loading.

This is the explicit handoff from
`FiniteScoreCellVectorCLTBridge.all_linear_projection_clts_with_verified_variance`
to a finite-dimensional vector CLT.  The remaining model-specific work is the
representation theorem identifying `⟪vector, t⟫` with the scalar score-cell
projection for `loadingOfDirection t`.
-/
theorem
    finite_score_cell_vector_clt_of_all_linear_projection_clts_and_projection_representation
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {E Sample LimitSample : Type*}
    [NormedAddCommGroup E] [InnerProductSpace Real E]
    [FiniteDimensional Real E] [MeasurableSpace E] [BorelSpace E]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (vector : ℕ -> Sample -> E) (limitVector : LimitSample -> E)
    (hvector : ∀ n, AEMeasurable (vector n) (sampleLaw n))
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (centeredProjection : (Cell -> Real) -> ℕ -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (loadingOfDirection : E -> Cell -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (hlinear :
      ∀ loading : Cell -> Real,
        centeredScoreCellLinearProjectionCLTWithVerifiedVariance
          cells referenceShare atTop sampleLaw limitLaw centeredProjection
          limitProjection loading)
    (hcentered :
      ∀ t n,
        (fun sample => centeredProjection (loadingOfDirection t) n sample)
          =ᵐ[sampleLaw n] fun sample => ⟪vector n sample, t⟫)
    (hlimit :
      ∀ t,
        (fun sample => limitProjection (loadingOfDirection t) sample)
          =ᵐ[limitLaw] fun sample => ⟪limitVector sample, t⟫) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_scalar_projection_tendstoInDistribution_bridge
    cells referenceShare sampleLaw limitLaw vector limitVector hvector
    hlimitVector simplexReferenceShares covarianceMatrixTangentSpaceVerified
    hsimplex hmatrix
    (fun t =>
      TendstoInDistribution.congr (hcentered t) (hlimit t)
        (hlinear (loadingOfDirection t)).2)

/--
Extend a Euclidean direction on the finite subtype of active cells to a
finite-cell loading on the ambient cell type, using zero off the active cell
set.
-/
noncomputable def finiteScoreCellEuclideanDirectionLoading
    (cells : Finset Cell)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) : Cell -> Real :=
  fun cell => if h : cell ∈ cells then direction ⟨cell, h⟩ else 0

/--
Canonical scalar projection of a Euclidean finite-cell vector against an
ambient finite-cell loading.
-/
noncomputable def finiteScoreCellEuclideanProjection
    (cells : Finset Cell)
    {Index Sample : Type*}
    (vector : Index -> Sample -> EuclideanSpace Real {cell // cell ∈ cells})
    (loading : Cell -> Real) : Index -> Sample -> Real :=
  fun index sample =>
    ⟪vector index sample,
      WithLp.toLp 2 (fun cellIndex : {cell // cell ∈ cells} =>
        loading cellIndex.1)⟫

/--
Canonical scalar projection of a Euclidean finite-cell Gaussian limit vector
against an ambient finite-cell loading.
-/
noncomputable def finiteScoreCellEuclideanLimitProjection
    (cells : Finset Cell)
    {LimitSample : Type*}
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (loading : Cell -> Real) : LimitSample -> Real :=
  fun sample =>
    ⟪limitVector sample,
      WithLp.toLp 2 (fun cellIndex : {cell // cell ∈ cells} =>
        loading cellIndex.1)⟫

/--
The ambient loading induced by a Euclidean direction restricts back to that
direction on the finite active-cell subtype.
-/
theorem finiteScoreCellEuclideanDirectionLoading_toLp
    (cells : Finset Cell)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    WithLp.toLp 2 (fun cellIndex : {cell // cell ∈ cells} =>
      finiteScoreCellEuclideanDirectionLoading cells direction cellIndex.1) =
      direction := by
  ext cellIndex
  simp [finiteScoreCellEuclideanDirectionLoading]

/--
The canonical Euclidean finite-cell scalar projection agrees pointwise with
the inner-product projection in the corresponding Euclidean direction.
-/
theorem finiteScoreCellEuclideanProjection_direction_eq_inner
    (cells : Finset Cell)
    {Index Sample : Type*}
    (vector : Index -> Sample -> EuclideanSpace Real {cell // cell ∈ cells})
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (index : Index) (sample : Sample) :
    finiteScoreCellEuclideanProjection cells vector
        (finiteScoreCellEuclideanDirectionLoading cells direction)
        index sample =
      ⟪vector index sample, direction⟫ := by
  simp [finiteScoreCellEuclideanProjection,
    finiteScoreCellEuclideanDirectionLoading_toLp]

/--
The canonical Euclidean finite-cell limit projection agrees pointwise with the
inner-product projection in the corresponding Euclidean direction.
-/
theorem finiteScoreCellEuclideanLimitProjection_direction_eq_inner
    (cells : Finset Cell)
    {LimitSample : Type*}
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (sample : LimitSample) :
    finiteScoreCellEuclideanLimitProjection cells limitVector
        (finiteScoreCellEuclideanDirectionLoading cells direction)
        sample =
      ⟪limitVector sample, direction⟫ := by
  simp [finiteScoreCellEuclideanLimitProjection,
    finiteScoreCellEuclideanDirectionLoading_toLp]

/--
Concrete active-cell vector of centered finite sample score-cell mass
deviations.

Its `cell` coordinate is the weighted cell mass minus the reference share
times total weight.  This is the finite-sample vector whose projections are
the scalar centered score-cell sums used by the CLT interface.
-/
noncomputable def finiteScoreCellCenteredMassVector
    {Unit : Type*} (cells : Finset Cell)
    (sample : Finset Unit) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare : Cell -> Real) :
    EuclideanSpace Real {cell // cell ∈ cells} :=
  WithLp.toLp 2 (fun cellIndex : {cell // cell ∈ cells} =>
    scoreCellMass sample weight score cellIndex.1 -
      referenceShare cellIndex.1 * weightedSampleTotal sample weight)

/--
Scaled active-cell vector of centered finite sample score-cell mass deviations.
-/
noncomputable def finiteScoreCellScaledCenteredMassVector
    {Unit : Type*} (cells : Finset Cell)
    (sample : Finset Unit) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare : Cell -> Real) (normalizer : Real) :
    EuclideanSpace Real {cell // cell ∈ cells} :=
  WithLp.toLp 2 (fun cellIndex : {cell // cell ∈ cells} =>
    normalizer *
      (scoreCellMass sample weight score cellIndex.1 -
        referenceShare cellIndex.1 * weightedSampleTotal sample weight))

/--
The concrete centered mass vector is tangent to the active finite-cell
simplex: its active coordinates sum to zero.
-/
theorem finiteScoreCellCenteredMassVector_sum_eq_zero_of_mapsTo
    {Unit : Type*} (cells : Finset Cell)
    (sample : Finset Unit) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellIndex : {cell // cell ∈ cells},
      finiteScoreCellCenteredMassVector
        cells sample weight score referenceShare cellIndex) = 0 := by
  have hmass :
      (∑ cellIndex : {cell // cell ∈ cells},
        scoreCellMass sample weight score cellIndex.1) =
        weightedSampleTotal sample weight := by
    rw [← Finset.sum_subtype (s := cells)
      (p := fun cell => cell ∈ cells) (h := by intro cell; simp)
      (f := fun cell => scoreCellMass sample weight score cell)]
    exact sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
      sample cells weight score hcover
  have href :
      (∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1) = 1 := by
    rw [← Finset.sum_subtype (s := cells)
      (p := fun cell => cell ∈ cells) (h := by intro cell; simp)
      (f := fun cell => referenceShare cell)]
    exact hshare_sum
  have href_total :
      (∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 * weightedSampleTotal sample weight) =
        weightedSampleTotal sample weight := by
    rw [← Finset.sum_mul, href]
    ring
  simp only [finiteScoreCellCenteredMassVector]
  rw [Finset.sum_sub_distrib, hmass, href_total]
  ring

/--
The scaled concrete centered mass vector remains tangent to the active
finite-cell simplex.
-/
theorem finiteScoreCellScaledCenteredMassVector_sum_eq_zero_of_mapsTo
    {Unit : Type*} (cells : Finset Cell)
    (sample : Finset Unit) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare : Cell -> Real) (normalizer : Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellIndex : {cell // cell ∈ cells},
      finiteScoreCellScaledCenteredMassVector
        cells sample weight score referenceShare normalizer cellIndex) =
      0 := by
  have hcenter :
      (∑ cellIndex : {cell // cell ∈ cells},
        (scoreCellMass sample weight score cellIndex.1 -
          referenceShare cellIndex.1 * weightedSampleTotal sample weight)) =
        0 := by
    simpa [finiteScoreCellCenteredMassVector]
      using
        finiteScoreCellCenteredMassVector_sum_eq_zero_of_mapsTo
          cells sample weight score referenceShare hcover hshare_sum
  simp only [finiteScoreCellScaledCenteredMassVector]
  rw [← Finset.mul_sum, hcenter, mul_zero]

/--
Equivalently, the concrete scaled centered mass vector is orthogonal to the
constant-one active-cell direction.
-/
theorem finiteScoreCellScaledCenteredMassVector_inner_const_one_eq_zero_of_mapsTo
    {Unit : Type*} (cells : Finset Cell)
    (sample : Finset Unit) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare : Cell -> Real) (normalizer : Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    ⟪finiteScoreCellScaledCenteredMassVector
        cells sample weight score referenceShare normalizer,
      WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
        (1 : Real))⟫ = 0 := by
  rw [PiLp.inner_apply]
  simpa [finiteScoreCellScaledCenteredMassVector]
    using
      finiteScoreCellScaledCenteredMassVector_sum_eq_zero_of_mapsTo
        cells sample weight score referenceShare normalizer hcover hshare_sum

/--
Inner products of the concrete centered mass vector are exactly weighted
centered score-cell linear projections.
-/
theorem finiteScoreCellCenteredMassVector_inner_loading_eq_weightedSampleSum
    {Unit : Type*} (cells : Finset Cell)
    (sample : Finset Unit) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) :
    ⟪finiteScoreCellCenteredMassVector cells sample weight score referenceShare,
      WithLp.toLp 2 (fun cellIndex : {cell // cell ∈ cells} =>
        loading cellIndex.1)⟫ =
      weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells score referenceShare
          loading) := by
  unfold finiteScoreCellCenteredMassVector
  rw [EuclideanSpace.inner_toLp_toLp]
  rw [weightedSampleSum_scoreCellLinearCenteredIndicator_eq]
  rw [← Finset.sum_attach cells (fun cell =>
    loading cell *
      (scoreCellMass sample weight score cell -
        referenceShare cell * weightedSampleTotal sample weight))]
  exact Finset.sum_congr rfl (fun cellIndex _ => by simp)

/--
Inner products of the scaled centered mass vector are scaled weighted centered
score-cell linear projections.
-/
theorem finiteScoreCellScaledCenteredMassVector_inner_loading_eq_scaled_weightedSampleSum
    {Unit : Type*} (cells : Finset Cell)
    (sample : Finset Unit) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (normalizer : Real) :
    ⟪finiteScoreCellScaledCenteredMassVector cells sample weight score
        referenceShare normalizer,
      WithLp.toLp 2 (fun cellIndex : {cell // cell ∈ cells} =>
        loading cellIndex.1)⟫ =
      normalizer * weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells score referenceShare
          loading) := by
  unfold finiteScoreCellScaledCenteredMassVector
  rw [EuclideanSpace.inner_toLp_toLp]
  rw [weightedSampleSum_scoreCellLinearCenteredIndicator_eq]
  rw [Finset.mul_sum]
  rw [← Finset.sum_attach cells (fun cell =>
    normalizer *
      (loading cell *
        (scoreCellMass sample weight score cell -
          referenceShare cell * weightedSampleTotal sample weight)))]
  exact Finset.sum_congr rfl (fun cellIndex _ => by simp; ring)

/--
For a Euclidean active-cell direction, the scaled concrete mass-vector
projection is the scaled centered score-cell projection with the corresponding
zero-extended loading.
-/
theorem finiteScoreCellScaledCenteredMassVector_inner_direction_eq_scaled_weightedSampleSum
    {Unit : Type*} (cells : Finset Cell)
    (sample : Finset Unit) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare : Cell -> Real) (normalizer : Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    ⟪finiteScoreCellScaledCenteredMassVector cells sample weight score
        referenceShare normalizer,
      direction⟫ =
      normalizer * weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)) := by
  simpa [finiteScoreCellEuclideanDirectionLoading_toLp]
    using
      finiteScoreCellScaledCenteredMassVector_inner_loading_eq_scaled_weightedSampleSum
        cells sample weight score referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) normalizer

/--
The canonical Euclidean projection of the concrete scaled centered mass-vector
process is the corresponding scaled weighted centered score-cell projection.
-/
theorem finiteScoreCellEuclideanProjection_scaledCenteredMassVector_eq_scaled_weightedSampleSum
    {Index Observation Sample : Type*} (cells : Finset Cell)
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare loading : Cell -> Real)
    (normalizer : Index -> Real) (index : Index) (samplePoint : Sample) :
    finiteScoreCellEuclideanProjection cells
        (fun index _sample =>
          finiteScoreCellScaledCenteredMassVector cells (finiteSample index)
            (weight index) (score index) referenceShare (normalizer index))
        loading index samplePoint =
      normalizer index * weightedSampleSum (finiteSample index) (weight index)
        (scoreCellLinearCenteredIndicator cells (score index) referenceShare
          loading) := by
  unfold finiteScoreCellEuclideanProjection
  exact
    finiteScoreCellScaledCenteredMassVector_inner_loading_eq_scaled_weightedSampleSum
      cells (finiteSample index) (weight index) (score index) referenceShare
      loading (normalizer index)

/--
Direction-specialized form of
`finiteScoreCellEuclideanProjection_scaledCenteredMassVector_eq_scaled_weightedSampleSum`.
-/
theorem
    finiteScoreCellEuclideanProjection_scaledCenteredMassVector_direction_eq_scaled_weightedSampleSum
    {Index Observation Sample : Type*} (cells : Finset Cell)
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare : Cell -> Real)
    (normalizer : Index -> Real) (index : Index) (samplePoint : Sample)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    finiteScoreCellEuclideanProjection cells
        (fun index _sample =>
          finiteScoreCellScaledCenteredMassVector cells (finiteSample index)
            (weight index) (score index) referenceShare (normalizer index))
        (finiteScoreCellEuclideanDirectionLoading cells direction)
        index samplePoint =
      normalizer index * weightedSampleSum (finiteSample index) (weight index)
        (scoreCellLinearCenteredIndicator cells (score index) referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)) := by
  exact
    finiteScoreCellEuclideanProjection_scaledCenteredMassVector_eq_scaled_weightedSampleSum
      cells finiteSample weight score referenceShare
      (finiteScoreCellEuclideanDirectionLoading cells direction) normalizer index
      samplePoint

/--
The reference-share mean of a Euclidean direction-induced loading is the
active-coordinate weighted mean.  This removes the zero-extended ambient
loading from the scalar projection variance target.
-/
theorem scoreCellLoadingReferenceMean_euclideanDirectionLoading
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    scoreCellLoadingReferenceMean cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 * direction cellIndex := by
  unfold scoreCellLoadingReferenceMean
  rw [← Finset.sum_attach cells (fun cell =>
    referenceShare cell *
      finiteScoreCellEuclideanDirectionLoading cells direction cell)]
  simp [finiteScoreCellEuclideanDirectionLoading]

/--
The verified scalar projection variance for a Euclidean direction-induced
loading is the active-coordinate centered second moment.
-/
theorem scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (direction cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * direction other) ^ 2 := by
  unfold scoreCellLoadingReferenceCenteredSecondMoment
  rw [scoreCellLoadingReferenceMean_euclideanDirectionLoading]
  rw [← Finset.sum_attach cells (fun cell =>
    referenceShare cell *
      (finiteScoreCellEuclideanDirectionLoading cells direction cell -
        ∑ other : {cell // cell ∈ cells},
          referenceShare other.1 * direction other) ^ 2)]
  simp [finiteScoreCellEuclideanDirectionLoading]

omit [DecidableEq Cell] in
/--
For a reference-mean-zero active Euclidean direction, the active centered
second moment is the plain active second moment.
-/
theorem finiteScoreCellActiveCenteredSecondMoment_eq_secondMoment_of_referenceMean_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hcentered :
      (∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 * direction cellIndex) = 0) :
    (∑ cellIndex : {cell // cell ∈ cells},
      referenceShare cellIndex.1 *
        (direction cellIndex -
          ∑ other : {cell // cell ∈ cells},
            referenceShare other.1 * direction other) ^ 2) =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 * direction cellIndex ^ 2 := by
  rw [hcentered]
  simp

/--
Reference-share centered version of an active Euclidean direction.

This subtracts the active reference-share mean from every coordinate.  Because
the finite centered mass vector and the Gaussian limit vector are tangent to
the active simplex, this is the canonical representative of the scalar
projection direction.
-/
noncomputable def finiteScoreCellEuclideanReferenceCenteredDirection
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    EuclideanSpace Real {cell // cell ∈ cells} :=
  WithLp.toLp 2 (fun cellIndex : {cell // cell ∈ cells} =>
    direction cellIndex -
      ∑ other : {cell // cell ∈ cells},
        referenceShare other.1 * direction other)

omit [DecidableEq Cell] in
/--
The reference-share centered active direction has zero reference-share mean.
-/
theorem finiteScoreCellEuclideanReferenceCenteredDirection_referenceMean_eq_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellIndex : {cell // cell ∈ cells},
      referenceShare cellIndex.1 *
        finiteScoreCellEuclideanReferenceCenteredDirection
          cells referenceShare direction cellIndex) = 0 := by
  let mean : Real :=
    ∑ other : {cell // cell ∈ cells},
      referenceShare other.1 * direction other
  have href :
      (∑ cellIndex : {cell // cell ∈ cells}, referenceShare cellIndex.1) =
        1 := by
    rw [← Finset.sum_subtype (s := cells)
      (p := fun cell => cell ∈ cells) (h := by intro cell; simp)
      (f := fun cell => referenceShare cell)]
    exact hshare_sum
  calc
    (∑ cellIndex : {cell // cell ∈ cells},
      referenceShare cellIndex.1 *
        finiteScoreCellEuclideanReferenceCenteredDirection
          cells referenceShare direction cellIndex) =
        ∑ cellIndex : {cell // cell ∈ cells},
          (referenceShare cellIndex.1 * direction cellIndex -
            referenceShare cellIndex.1 * mean) := by
          exact Finset.sum_congr rfl (fun cellIndex _hcellIndex => by
            simp [finiteScoreCellEuclideanReferenceCenteredDirection, mean,
              mul_sub])
    _ =
        (∑ cellIndex : {cell // cell ∈ cells},
          referenceShare cellIndex.1 * direction cellIndex) -
        (∑ cellIndex : {cell // cell ∈ cells},
          referenceShare cellIndex.1 * mean) := by
          rw [Finset.sum_sub_distrib]
    _ = mean - (∑ cellIndex : {cell // cell ∈ cells},
          referenceShare cellIndex.1) * mean := by
          rw [Finset.sum_mul]
    _ = 0 := by
          rw [href]
          ring

/--
An active Euclidean direction is nonconstant when two active coordinates
differ.  These are exactly the directions that can carry a nondegenerate
finite-cell projection variance under positive simplex shares.
-/
def finiteScoreCellEuclideanDirectionNonconstant
    (cells : Finset Cell)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) : Prop :=
  ∃ cellA cellB : {cell // cell ∈ cells},
    direction cellA ≠ direction cellB

omit [DecidableEq Cell] in
/--
Reference-centering preserves and reflects nonconstancy of active Euclidean
directions.
-/
theorem finiteScoreCellEuclideanReferenceCenteredDirection_nonconstant_iff
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    finiteScoreCellEuclideanDirectionNonconstant cells
        (finiteScoreCellEuclideanReferenceCenteredDirection
          cells referenceShare direction) ↔
      finiteScoreCellEuclideanDirectionNonconstant cells direction := by
  constructor
  · rintro ⟨cellA, cellB, hneq⟩
    refine ⟨cellA, cellB, ?_⟩
    intro hsame
    exact hneq (by
      simp [finiteScoreCellEuclideanReferenceCenteredDirection, hsame])
  · rintro ⟨cellA, cellB, hneq⟩
    refine ⟨cellA, cellB, ?_⟩
    intro hsame
    have hdiff :
        direction cellA -
            (∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * direction other) =
          direction cellB -
            (∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * direction other) := by
      simpa [finiteScoreCellEuclideanReferenceCenteredDirection]
        using hsame
    exact hneq (by linarith)

/--
The verified active variance of the reference-centered direction is the
original active centered second moment.
-/
theorem
    scoreCellLoadingReferenceCenteredSecondMoment_euclideanReferenceCenteredDirection
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells
          (finiteScoreCellEuclideanReferenceCenteredDirection
            cells referenceShare direction)) =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (direction cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * direction other) ^ 2 := by
  rw [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
  rw [
    finiteScoreCellEuclideanReferenceCenteredDirection_referenceMean_eq_zero
      cells referenceShare direction hshare_sum]
  simp [finiteScoreCellEuclideanReferenceCenteredDirection]

omit [DecidableEq Cell] in
/--
Reference-centering subtracts the active reference-share mean times the
constant-one active direction.
-/
theorem finiteScoreCellEuclideanReferenceCenteredDirection_eq_sub_smul_constOne
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    finiteScoreCellEuclideanReferenceCenteredDirection
        cells referenceShare direction =
      direction -
        (∑ other : {cell // cell ∈ cells},
          referenceShare other.1 * direction other) •
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) := by
  ext cellIndex
  simp [finiteScoreCellEuclideanReferenceCenteredDirection]

omit [DecidableEq Cell] in
/--
On tangent active Euclidean vectors, reference-centering the projection
direction does not change the inner product.
-/
theorem inner_finiteScoreCellEuclideanReferenceCenteredDirection_eq_of_tangent
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction vector : EuclideanSpace Real {cell // cell ∈ cells})
    (hvector_tangent :
      ⟪vector,
        WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
          (1 : Real))⟫ = 0) :
    ⟪vector,
      finiteScoreCellEuclideanReferenceCenteredDirection
        cells referenceShare direction⟫ =
      ⟪vector, direction⟫ := by
  rw [
    finiteScoreCellEuclideanReferenceCenteredDirection_eq_sub_smul_constOne]
  rw [inner_sub_right, inner_smul_right, hvector_tangent]
  ring

/--
For tangent finite-sample vectors, replacing a Euclidean direction by its
reference-centered representative does not change the scalar projection.
-/
theorem
    finiteScoreCellEuclideanProjection_referenceCenteredDirection_eq_of_tangent
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Sample : Type*}
    (vector : Index -> Sample -> EuclideanSpace Real {cell // cell ∈ cells})
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (index : Index) (sample : Sample)
    (hvector_tangent :
      ⟪vector index sample,
        WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
          (1 : Real))⟫ = 0) :
    finiteScoreCellEuclideanProjection cells vector
        (finiteScoreCellEuclideanDirectionLoading cells
          (finiteScoreCellEuclideanReferenceCenteredDirection
            cells referenceShare direction))
        index sample =
      finiteScoreCellEuclideanProjection cells vector
        (finiteScoreCellEuclideanDirectionLoading cells direction)
        index sample := by
  rw [finiteScoreCellEuclideanProjection_direction_eq_inner]
  rw [finiteScoreCellEuclideanProjection_direction_eq_inner]
  exact
    inner_finiteScoreCellEuclideanReferenceCenteredDirection_eq_of_tangent
      cells referenceShare direction (vector index sample) hvector_tangent

/--
For tangent limit vectors, replacing a Euclidean direction by its
reference-centered representative does not change the scalar limit projection.
-/
theorem
    finiteScoreCellEuclideanLimitProjection_referenceCenteredDirection_eq_of_tangent
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {LimitSample : Type*}
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (sample : LimitSample)
    (hlimit_tangent :
      ⟪limitVector sample,
        WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
          (1 : Real))⟫ = 0) :
    finiteScoreCellEuclideanLimitProjection cells limitVector
        (finiteScoreCellEuclideanDirectionLoading cells
          (finiteScoreCellEuclideanReferenceCenteredDirection
            cells referenceShare direction))
        sample =
      finiteScoreCellEuclideanLimitProjection cells limitVector
        (finiteScoreCellEuclideanDirectionLoading cells direction)
        sample := by
  rw [finiteScoreCellEuclideanLimitProjection_direction_eq_inner]
  rw [finiteScoreCellEuclideanLimitProjection_direction_eq_inner]
  exact
    inner_finiteScoreCellEuclideanReferenceCenteredDirection_eq_of_tangent
      cells referenceShare direction (limitVector sample) hlimit_tangent

/--
A constant Euclidean active-cell direction has zero verified centered second
moment under simplex reference shares.
-/
theorem scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirection_eq_zero_of_constant
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hconstant :
      ∀ cellA cellB : {cell // cell ∈ cells},
        direction cellA = direction cellB) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) =
      0 := by
  rw [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
  have href :
      (∑ cellIndex : {cell // cell ∈ cells}, referenceShare cellIndex.1) =
        1 := by
    rw [← Finset.sum_subtype (s := cells)
      (p := fun cell => cell ∈ cells) (h := by intro cell; simp)
      (f := fun cell => referenceShare cell)]
    exact hshare_sum
  apply Finset.sum_eq_zero
  intro cellIndex _hcellIndex
  have hmean :
      (∑ other : {cell // cell ∈ cells},
        referenceShare other.1 * direction other) =
        direction cellIndex := by
    calc
      (∑ other : {cell // cell ∈ cells},
        referenceShare other.1 * direction other) =
          ∑ other : {cell // cell ∈ cells},
            referenceShare other.1 * direction cellIndex := by
            exact Finset.sum_congr rfl (fun other _hother => by
              rw [hconstant other cellIndex])
      _ = (∑ other : {cell // cell ∈ cells},
            referenceShare other.1) * direction cellIndex := by
            rw [Finset.sum_mul]
      _ = direction cellIndex := by
            rw [href]
            ring
  have hdiff :
      direction cellIndex -
        (∑ other : {cell // cell ∈ cells},
          referenceShare other.1 * direction other) =
        0 := by
    rw [hmean]
    ring
  rw [hdiff]
  ring

/--
With strictly positive active reference shares, a zero verified centered second
moment forces the Euclidean direction to be constant on the active finite
cell set.
-/
theorem finiteScoreCellEuclideanDirection_eq_referenceMean_of_centeredSecondMoment_eq_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hvariance :
      scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) = 0) :
    ∀ cellIndex : {cell // cell ∈ cells},
      direction cellIndex =
        ∑ other : {cell // cell ∈ cells},
          referenceShare other.1 * direction other := by
  intro cellIndex
  let mean : Real :=
    ∑ other : {cell // cell ∈ cells},
      referenceShare other.1 * direction other
  have hzero :
      (∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (direction cellIndex - mean) ^ 2) = 0 := by
    simpa [mean,
      scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
      using hvariance
  have hterms :
      ∀ cellIndex : {cell // cell ∈ cells},
        cellIndex ∈ (Finset.univ : Finset {cell // cell ∈ cells}) ->
          referenceShare cellIndex.1 *
            (direction cellIndex - mean) ^ 2 = 0 :=
    (Finset.sum_eq_zero_iff_of_nonneg
      (s := (Finset.univ : Finset {cell // cell ∈ cells}))
      (f := fun cellIndex =>
        referenceShare cellIndex.1 *
          (direction cellIndex - mean) ^ 2)
      (fun cellIndex _hcellIndex =>
        mul_nonneg (le_of_lt (hshare_pos cellIndex.1 cellIndex.2))
          (sq_nonneg (direction cellIndex - mean)))).mp hzero
  have hsquare :
      (direction cellIndex - mean) ^ 2 = 0 := by
    rcases mul_eq_zero.mp (hterms cellIndex (by simp)) with hshare_zero | hsquare
    · exact False.elim ((ne_of_gt (hshare_pos cellIndex.1 cellIndex.2))
        hshare_zero)
    · exact hsquare
  have hdiff : direction cellIndex - mean = 0 :=
    sq_eq_zero_iff.mp hsquare
  linarith

/--
Nonzero verified centered second moment implies a nonconstant active
Euclidean direction.
-/
theorem finiteScoreCellEuclideanDirectionNonconstant_of_centeredSecondMoment_ne_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hvariance :
      scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) ≠ 0) :
    finiteScoreCellEuclideanDirectionNonconstant cells direction := by
  by_contra hnot
  have hconstant :
      ∀ cellA cellB : {cell // cell ∈ cells},
        direction cellA = direction cellB := by
    intro cellA cellB
    by_contra hneq
    exact hnot ⟨cellA, cellB, hneq⟩
  exact hvariance
    (scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirection_eq_zero_of_constant
      cells referenceShare direction hshare_sum hconstant)

/--
With strictly positive active reference shares, every nonconstant Euclidean
direction has nonzero verified centered second moment.
-/
theorem scoreCellLoadingReferenceCenteredSecondMoment_ne_zero_of_euclideanDirectionNonconstant
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hnonconstant :
      finiteScoreCellEuclideanDirectionNonconstant cells direction) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) ≠
      0 := by
  intro hvariance
  rcases hnonconstant with ⟨cellA, cellB, hneq⟩
  have hA :
      direction cellA =
        ∑ other : {cell // cell ∈ cells},
          referenceShare other.1 * direction other :=
    finiteScoreCellEuclideanDirection_eq_referenceMean_of_centeredSecondMoment_eq_zero
      cells referenceShare direction hshare_pos hvariance cellA
  have hB :
      direction cellB =
        ∑ other : {cell // cell ∈ cells},
          referenceShare other.1 * direction other :=
    finiteScoreCellEuclideanDirection_eq_referenceMean_of_centeredSecondMoment_eq_zero
      cells referenceShare direction hshare_pos hvariance cellB
  exact hneq (hA.trans hB.symm)

/--
With strictly positive active reference shares, every nonconstant Euclidean
direction has strictly positive verified centered second moment.
-/
theorem scoreCellLoadingReferenceCenteredSecondMoment_pos_of_euclideanDirectionNonconstant
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hnonconstant :
      finiteScoreCellEuclideanDirectionNonconstant cells direction) :
    0 <
      scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) := by
  have hnonneg :
      0 ≤
        scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction) :=
    scoreCellLoadingReferenceCenteredSecondMoment_nonneg
      cells referenceShare (finiteScoreCellEuclideanDirectionLoading cells direction)
      (fun cell hcell => le_of_lt (hshare_pos cell hcell))
  have hne :
      scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction) ≠
        0 :=
    scoreCellLoadingReferenceCenteredSecondMoment_ne_zero_of_euclideanDirectionNonconstant
      cells referenceShare direction hshare_pos hnonconstant
  exact lt_of_le_of_ne hnonneg (Ne.symm hne)

/--
Active-coordinate form of
`scoreCellLoadingReferenceCenteredSecondMoment_pos_of_euclideanDirectionNonconstant`.
-/
theorem finiteScoreCellActiveCenteredSecondMoment_pos_of_euclideanDirectionNonconstant
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hnonconstant :
      finiteScoreCellEuclideanDirectionNonconstant cells direction) :
    0 <
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (direction cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * direction other) ^ 2 := by
  simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
    using
      scoreCellLoadingReferenceCenteredSecondMoment_pos_of_euclideanDirectionNonconstant
        cells referenceShare direction hshare_pos hnonconstant

/--
A strictly positive active-coordinate centered second moment rules out
constant active Euclidean directions under simplex reference shares.
-/
theorem finiteScoreCellEuclideanDirectionNonconstant_of_activeCenteredSecondMoment_pos
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hactive_pos :
      0 <
        ∑ cellIndex : {cell // cell ∈ cells},
          referenceShare cellIndex.1 *
            (direction cellIndex -
              ∑ other : {cell // cell ∈ cells},
                referenceShare other.1 * direction other) ^ 2) :
    finiteScoreCellEuclideanDirectionNonconstant cells direction := by
  refine
    finiteScoreCellEuclideanDirectionNonconstant_of_centeredSecondMoment_ne_zero
      cells referenceShare direction hshare_sum ?_
  intro hvariance
  have hactive_zero :
      (∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (direction cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * direction other) ^ 2) = 0 := by
    simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
      using hvariance
  exact (ne_of_gt hactive_pos) hactive_zero

/--
Under positive simplex shares, positive active-coordinate centered second
moment is equivalent to nonconstancy of the active Euclidean direction.
-/
theorem finiteScoreCellActiveCenteredSecondMoment_pos_iff_euclideanDirectionNonconstant
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (0 <
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (direction cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * direction other) ^ 2) ↔
      finiteScoreCellEuclideanDirectionNonconstant cells direction := by
  constructor
  · exact
      finiteScoreCellEuclideanDirectionNonconstant_of_activeCenteredSecondMoment_pos
        cells referenceShare direction hshare_sum
  · exact
      finiteScoreCellActiveCenteredSecondMoment_pos_of_euclideanDirectionNonconstant
        cells referenceShare direction hshare_pos

/--
Under strictly positive reference shares, zero verified variance makes the
concrete scaled centered mass-vector projection pointwise zero.
-/
theorem finiteScoreCellEuclideanProjection_scaledCenteredMassVector_eq_zero_of_centeredSecondMoment_eq_zero
    {Index Observation Sample : Type*}
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (normalizer : Index -> Real)
    (index : Index) (samplePoint : Sample)
    (hcover :
      ∀ unit, unit ∈ finiteSample index -> score index unit ∈ cells)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hvariance :
      scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) = 0) :
    finiteScoreCellEuclideanProjection cells
        (fun index _sample =>
          finiteScoreCellScaledCenteredMassVector cells
            (finiteSample index) (weight index) (score index)
            referenceShare (normalizer index))
        (finiteScoreCellEuclideanDirectionLoading cells direction)
        index samplePoint = 0 := by
  let mean : Real :=
    ∑ other : {cell // cell ∈ cells},
      referenceShare other.1 * direction other
  have hconstant :
      ∀ cellIndex : {cell // cell ∈ cells},
        direction cellIndex = mean := by
    intro cellIndex
    simpa [mean] using
      finiteScoreCellEuclideanDirection_eq_referenceMean_of_centeredSecondMoment_eq_zero
        cells referenceShare direction hshare_pos hvariance cellIndex
  rw [finiteScoreCellEuclideanProjection_direction_eq_inner]
  rw [PiLp.inner_apply]
  change
    (∑ cellIndex : {cell // cell ∈ cells},
      direction cellIndex *
        finiteScoreCellScaledCenteredMassVector cells (finiteSample index)
          (weight index) (score index) referenceShare (normalizer index)
          cellIndex) = 0
  calc
    (∑ cellIndex : {cell // cell ∈ cells},
      direction cellIndex *
        finiteScoreCellScaledCenteredMassVector cells (finiteSample index)
          (weight index) (score index) referenceShare (normalizer index)
          cellIndex) =
        ∑ cellIndex : {cell // cell ∈ cells},
          mean *
            finiteScoreCellScaledCenteredMassVector cells (finiteSample index)
              (weight index) (score index) referenceShare (normalizer index)
              cellIndex := by
          exact Finset.sum_congr rfl (fun cellIndex _hcellIndex => by
            rw [hconstant cellIndex])
    _ =
        mean * (∑ cellIndex : {cell // cell ∈ cells},
          finiteScoreCellScaledCenteredMassVector cells (finiteSample index)
              (weight index) (score index) referenceShare (normalizer index)
              cellIndex) := by
          rw [← Finset.mul_sum]
    _ = 0 := by
          rw [
            finiteScoreCellScaledCenteredMassVector_sum_eq_zero_of_mapsTo
              cells (finiteSample index) (weight index) (score index)
              referenceShare (normalizer index) hcover hshare_sum]
          ring

/--
Under strictly positive reference shares, zero verified variance makes a
tangent Euclidean limit-vector projection pointwise zero.
-/
theorem finiteScoreCellEuclideanLimitProjection_eq_zero_of_centeredSecondMoment_eq_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    {LimitSample : Type*}
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (sample : LimitSample)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hvariance :
      scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) = 0)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0) :
    finiteScoreCellEuclideanLimitProjection cells limitVector
        (finiteScoreCellEuclideanDirectionLoading cells direction)
        sample = 0 := by
  let mean : Real :=
    ∑ other : {cell // cell ∈ cells},
      referenceShare other.1 * direction other
  have hconstant :
      ∀ cellIndex : {cell // cell ∈ cells},
        direction cellIndex = mean := by
    intro cellIndex
    simpa [mean] using
      finiteScoreCellEuclideanDirection_eq_referenceMean_of_centeredSecondMoment_eq_zero
        cells referenceShare direction hshare_pos hvariance cellIndex
  have htangent_sum :
      (∑ cellIndex : {cell // cell ∈ cells},
        limitVector sample cellIndex) = 0 := by
    have htangent := hlimit_tangent sample
    rw [PiLp.inner_apply] at htangent
    simpa using htangent
  rw [finiteScoreCellEuclideanLimitProjection_direction_eq_inner]
  rw [PiLp.inner_apply]
  change
    (∑ cellIndex : {cell // cell ∈ cells},
      direction cellIndex * limitVector sample cellIndex) = 0
  calc
    (∑ cellIndex : {cell // cell ∈ cells},
      direction cellIndex * limitVector sample cellIndex) =
        ∑ cellIndex : {cell // cell ∈ cells},
          mean * limitVector sample cellIndex := by
          exact Finset.sum_congr rfl (fun cellIndex _hcellIndex => by
            rw [hconstant cellIndex])
    _ = mean * (∑ cellIndex : {cell // cell ∈ cells},
          limitVector sample cellIndex) := by
          rw [← Finset.mul_sum]
    _ = 0 := by
          rw [htangent_sum]
          ring

/--
The constant-one active Euclidean direction has zero verified centered second
moment under simplex reference shares.
-/
theorem
    scoreCellLoadingReferenceCenteredSecondMoment_euclideanConstOne_eq_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells
          (WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)))) =
      0 := by
  rw [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
  have href :
      (∑ cellIndex : {cell // cell ∈ cells}, referenceShare cellIndex.1) =
        1 := by
    rw [← Finset.sum_subtype (s := cells)
      (p := fun cell => cell ∈ cells) (h := by intro cell; simp)
      (f := fun cell => referenceShare cell)]
    exact hshare_sum
  have hmean :
      (∑ other : {cell // cell ∈ cells},
        referenceShare other.1 *
          (WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) other)) = 1 := by
    simpa using href
  rw [hmean]
  apply Finset.sum_eq_zero
  intro cellIndex _hcellIndex
  simp

/--
The constant-one active Euclidean projection of the concrete scaled centered
mass-vector process is a degenerate scalar CLT, not a remaining stochastic
survey-design premise.

The source projection is pointwise zero from finite score-cell coverage and
simplex shares.  The limit projection is assumed tangent in the same
constant-one direction.  The limit law is then the degenerate Gaussian
`gaussianReal 0 0`, and convergence in distribution follows from the checked
constant-zero law route above.
-/
theorem
    centered_scoreCellLinearProjection_clt_const_one_of_scaledCenteredMassVector
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (normalizer : Index -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hcover :
      ∀ index, ∀ unit, unit ∈ finiteSample index ->
        score index unit ∈ cells)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw
      (finiteScoreCellEuclideanProjection cells
        (fun index _sample =>
          finiteScoreCellScaledCenteredMassVector cells
            (finiteSample index) (weight index) (score index)
            referenceShare (normalizer index)))
      (finiteScoreCellEuclideanLimitProjection cells limitVector)
      (finiteScoreCellEuclideanDirectionLoading cells
        (WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
          (1 : Real)))) := by
  let direction : EuclideanSpace Real {cell // cell ∈ cells} :=
    WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
      (1 : Real))
  let loading : Cell -> Real :=
    finiteScoreCellEuclideanDirectionLoading cells direction
  constructor
  · have hlimit_zero :
        finiteScoreCellEuclideanLimitProjection cells limitVector loading
          =ᵐ[limitLaw] fun _sample : LimitSample => (0 : Real) :=
      ae_of_all _ fun sample => by
        rw [finiteScoreCellEuclideanLimitProjection_direction_eq_inner]
        exact hlimit_tangent sample
    have hlaw :
        HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
          (gaussianReal 0 0) limitLaw :=
      (hasLaw_const_zero_gaussianReal_zero_var limitLaw).congr hlimit_zero
    have hvariance :
        scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
            loading =
          0 := by
      simpa [loading, direction]
        using
          scoreCellLoadingReferenceCenteredSecondMoment_euclideanConstOne_eq_zero
            cells referenceShare hshare_sum
    simpa [loading, direction, hvariance] using hlaw
  · have hsource_zero :
        ∀ index,
          (fun _sample : Sample => (0 : Real)) =ᵐ[sampleLaw index]
            (fun sample =>
              finiteScoreCellEuclideanProjection cells
                (fun index _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample index) (weight index) (score index)
                    referenceShare (normalizer index))
                loading index sample) := by
      intro index
      exact ae_of_all _ fun sample => by
        symm
        change
          finiteScoreCellEuclideanProjection cells
              (fun index _sample =>
                finiteScoreCellScaledCenteredMassVector cells
                  (finiteSample index) (weight index) (score index)
                  referenceShare (normalizer index))
              (finiteScoreCellEuclideanDirectionLoading cells direction)
              index sample =
            0
        rw [finiteScoreCellEuclideanProjection_direction_eq_inner]
        simpa [direction] using
          finiteScoreCellScaledCenteredMassVector_inner_const_one_eq_zero_of_mapsTo
            cells (finiteSample index) (weight index) (score index)
            referenceShare (normalizer index) (hcover index) hshare_sum
    have htarget_zero :
        (fun _sample : LimitSample => (0 : Real)) =ᵐ[limitLaw]
          finiteScoreCellEuclideanLimitProjection cells limitVector loading :=
      ae_of_all _ fun sample => by
        symm
        rw [finiteScoreCellEuclideanLimitProjection_direction_eq_inner]
        exact hlimit_tangent sample
    have hconst :=
      tendstoInDistribution_const_zero_real l sampleLaw limitLaw
    simpa [loading, direction] using
      hconst.congr hsource_zero htarget_zero

/--
The centered cross moment of two Euclidean direction-induced loadings is the
active-coordinate centered cross moment.
-/
theorem scoreCellLoadingReferenceCenteredCrossMoment_euclideanDirectionLoading
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (directionA directionB : EuclideanSpace Real {cell // cell ∈ cells}) :
    scoreCellLoadingReferenceCenteredCrossMoment cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells directionA)
        (finiteScoreCellEuclideanDirectionLoading cells directionB) =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (directionA cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * directionA other) *
          (directionB cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * directionB other) := by
  unfold scoreCellLoadingReferenceCenteredCrossMoment
  rw [scoreCellLoadingReferenceMean_euclideanDirectionLoading]
  rw [scoreCellLoadingReferenceMean_euclideanDirectionLoading]
  rw [← Finset.sum_attach cells (fun cell =>
    referenceShare cell *
      (finiteScoreCellEuclideanDirectionLoading cells directionA cell -
        ∑ other : {cell // cell ∈ cells},
          referenceShare other.1 * directionA other) *
      (finiteScoreCellEuclideanDirectionLoading cells directionB cell -
        ∑ other : {cell // cell ∈ cells},
          referenceShare other.1 * directionB other))]
  simp [finiteScoreCellEuclideanDirectionLoading]

/--
Under simplex reference shares, the covariance-kernel bilinear form for two
Euclidean direction-induced loadings is the active-coordinate centered cross
moment.  This is the matrix-side counterpart of the scalar active variance
target.
-/
theorem
    scoreCellBilinearCovarianceKernelForm_euclideanDirectionLoading_eq_activeCenteredCrossMoment
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (directionA directionB : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells directionA)
        (finiteScoreCellEuclideanDirectionLoading cells directionB) =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (directionA cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * directionA other) *
          (directionB cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * directionB other) := by
  rw [scoreCellBilinearCovarianceKernelForm_eq_centeredCrossMoment
    cells referenceShare
      (finiteScoreCellEuclideanDirectionLoading cells directionA)
      (finiteScoreCellEuclideanDirectionLoading cells directionB) hshare_sum]
  exact scoreCellLoadingReferenceCenteredCrossMoment_euclideanDirectionLoading
    cells referenceShare directionA directionB

/--
Under simplex reference shares, the covariance-kernel quadratic form for a
Euclidean direction-induced loading is the active-coordinate centered second
moment used as the scalar Gaussian variance.
-/
theorem
    scoreCellLinearCovarianceKernelForm_euclideanDirectionLoading_eq_activeVariance
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLinearCovarianceKernelForm cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) =
      ∑ cellIndex : {cell // cell ∈ cells},
        referenceShare cellIndex.1 *
          (direction cellIndex -
            ∑ other : {cell // cell ∈ cells},
              referenceShare other.1 * direction other) ^ 2 := by
  rw [scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
    cells referenceShare (finiteScoreCellEuclideanDirectionLoading cells direction)
    hshare_sum]
  exact scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading
    cells referenceShare direction

/--
The finite centered-indicator projection induced by a Euclidean direction is
the active-coordinate linear combination of centered score-cell indicators.
This is the deterministic projection identity needed by scalar survey-design
CLT proofs.
-/
theorem scoreCellLinearCenteredIndicator_euclideanDirectionLoading
    {Unit : Type*}
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (unit : Unit) :
    scoreCellLinearCenteredIndicator cells score referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction) unit =
      ∑ cellIndex : {cell // cell ∈ cells},
        direction cellIndex *
          centeredScoreCellIndicator score referenceShare cellIndex.1 unit := by
  unfold scoreCellLinearCenteredIndicator
  rw [← Finset.sum_attach cells (fun cell =>
    finiteScoreCellEuclideanDirectionLoading cells direction cell *
      centeredScoreCellIndicator score referenceShare cell unit)]
  simp [finiteScoreCellEuclideanDirectionLoading]

omit [DecidableEq Cell] in
/--
Euclidean finite-cell scalar projections are a.e.-measurable whenever the
underlying Euclidean finite-cell vector is a.e.-measurable.
-/
theorem finiteScoreCellEuclideanProjection_aemeasurable
    (cells : Finset Cell)
    {Index Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Index -> Measure Sample)
    (vector : Index -> Sample -> EuclideanSpace Real {cell // cell ∈ cells})
    (loading : Cell -> Real)
    (hvector : ∀ index, AEMeasurable (vector index) (sampleLaw index)) :
    ∀ index,
      AEMeasurable
        (fun sample => finiteScoreCellEuclideanProjection cells vector loading
          index sample)
        (sampleLaw index) := by
  intro index
  unfold finiteScoreCellEuclideanProjection
  exact (hvector index).inner_const

omit [DecidableEq Cell] in
/--
Euclidean finite-cell scalar limit projections are a.e.-measurable whenever
the underlying Euclidean finite-cell limit vector is a.e.-measurable.
-/
theorem finiteScoreCellEuclideanLimitProjection_aemeasurable
    (cells : Finset Cell)
    {LimitSample : Type*} [MeasurableSpace LimitSample]
    (limitLaw : Measure LimitSample)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (loading : Cell -> Real)
    (hlimitVector : AEMeasurable limitVector limitLaw) :
    AEMeasurable
      (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
      limitLaw := by
  unfold finiteScoreCellEuclideanLimitProjection
  exact hlimitVector.inner_const

/--
Concrete Euclidean finite-cell Cramer-Wold packaging.

For the vector space `EuclideanSpace ℝ {cell // cell ∈ cells}`, scalar CLTs
for the canonical projection attached to every Euclidean direction imply the
finite-dimensional score-cell vector CLT through the checked scalar-projection
Lévy route.  This removes the deterministic representation part of the vector
CLT blocker; the remaining probability theorem is the scalar survey-design
projection CLT itself, for each Euclidean direction/loading.
-/
theorem finite_score_cell_vector_clt_of_euclidean_direction_projection_clts
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (vector : ℕ -> Sample -> EuclideanSpace Real {cell // cell ∈ cells})
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hvector : ∀ n, AEMeasurable (vector n) (sampleLaw n))
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (hprojection :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        centeredScoreCellLinearProjectionCLTWithVerifiedVariance
          cells referenceShare atTop sampleLaw limitLaw
          (finiteScoreCellEuclideanProjection cells vector)
          (finiteScoreCellEuclideanLimitProjection cells limitVector)
          (finiteScoreCellEuclideanDirectionLoading cells direction)) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_scalar_projection_tendstoInDistribution_bridge
    cells referenceShare sampleLaw limitLaw vector limitVector hvector
    hlimitVector simplexReferenceShares covarianceMatrixTangentSpaceVerified
    hsimplex hmatrix
    (fun direction =>
      TendstoInDistribution.congr
        (fun n => Filter.Eventually.of_forall fun sample =>
          finiteScoreCellEuclideanProjection_direction_eq_inner
            cells vector direction n sample)
        (Filter.Eventually.of_forall fun sample =>
          finiteScoreCellEuclideanLimitProjection_direction_eq_inner
            cells limitVector direction sample)
        (hprojection direction).2)

/--
Large-jump tail used as the concrete finite-cell Lindeberg input for one
centered score-cell linear projection.
-/
noncomputable def scoreCellSurveyProjectionLindebergTail
    {Index Observation : Type*}
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare loading : Cell -> Real)
    (scale normalizer : Index -> Real) (epsilon : Real) : Index -> Real :=
  fun index =>
    normalizer index *
      (∑ unit ∈ sample index,
        largeJumpSquare
          (weight index unit *
            scoreCellLinearCenteredIndicator cells (score index)
              referenceShare loading unit)
          (epsilon * scale index))

/--
Concrete deterministic Lindeberg condition for one finite score-cell survey
projection.
-/
def finiteScoreCellSurveyProjectionLindebergCondition
    {Index Observation : Type*} (l : Filter Index)
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare loading : Cell -> Real)
    (scale normalizer : Index -> Real) : Prop :=
  ∀ epsilon : Real, 0 < epsilon ->
    Tendsto
      (scoreCellSurveyProjectionLindebergTail sample cells weight score
        referenceShare loading scale normalizer epsilon)
      l (nhds 0)

/--
The survey-projection Lindeberg tail for a Euclidean direction-induced loading
is the large-jump tail of the active-coordinate centered-indicator projection.
-/
theorem scoreCellSurveyProjectionLindebergTail_euclideanDirectionLoading
    {Index Observation : Type*}
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    (scale normalizer : Index -> Real) (epsilon : Real) (index : Index) :
    scoreCellSurveyProjectionLindebergTail sample cells weight score
        referenceShare (finiteScoreCellEuclideanDirectionLoading cells direction)
        scale normalizer epsilon index =
      normalizer index *
        (∑ unit ∈ sample index,
          largeJumpSquare
            (weight index unit *
              (∑ cellIndex : {cell // cell ∈ cells},
                direction cellIndex *
                  centeredScoreCellIndicator (score index) referenceShare
                    cellIndex.1 unit))
            (epsilon * scale index)) := by
  unfold scoreCellSurveyProjectionLindebergTail
  exact congrArg (fun value => normalizer index * value)
    (Finset.sum_congr rfl
      (fun unit _hunit => by
        rw [scoreCellLinearCenteredIndicator_euclideanDirectionLoading]))

/-- Canonical finite absolute-sum bound for a fixed score-cell loading. -/
noncomputable def finiteScoreCellLoadingAbsSumBound
    (cells : Finset Cell) (loading : Cell -> Real) : Real :=
  ∑ cell ∈ cells, |loading cell|

omit [DecidableEq Cell] in
/-- The canonical finite loading bound is nonnegative. -/
theorem finiteScoreCellLoadingAbsSumBound_nonneg
    (cells : Finset Cell) (loading : Cell -> Real) :
    0 ≤ finiteScoreCellLoadingAbsSumBound cells loading := by
  unfold finiteScoreCellLoadingAbsSumBound
  exact Finset.sum_nonneg (fun cell _hcell => abs_nonneg (loading cell))

omit [DecidableEq Cell] in
/-- Every cell loading is bounded by its canonical finite absolute-sum bound. -/
theorem finiteScoreCellLoadingAbsSumBound_bound
    (cells : Finset Cell) (loading : Cell -> Real) :
    ∀ cell, cell ∈ cells ->
      |loading cell| ≤ finiteScoreCellLoadingAbsSumBound cells loading := by
  intro cell hcell
  unfold finiteScoreCellLoadingAbsSumBound
  exact
    Finset.single_le_sum
      (s := cells) (f := fun other => |loading other|)
      (fun other _hother => abs_nonneg (loading other)) hcell

/--
For an active-cell Euclidean direction, the canonical ambient finite loading
bound is exactly the `ℓ¹` sum of the active coordinates.
-/
theorem finiteScoreCellLoadingAbsSumBound_euclideanDirectionLoading
    (cells : Finset Cell)
    (direction : EuclideanSpace Real {cell // cell ∈ cells}) :
    finiteScoreCellLoadingAbsSumBound cells
        (finiteScoreCellEuclideanDirectionLoading cells direction) =
      ∑ cellIndex : {cell // cell ∈ cells}, |direction cellIndex| := by
  unfold finiteScoreCellLoadingAbsSumBound
  rw [← Finset.sum_attach cells (fun cell =>
    |finiteScoreCellEuclideanDirectionLoading cells direction cell|)]
  simp [finiteScoreCellEuclideanDirectionLoading]

/--
Bounded finite score-cell projections satisfy the concrete survey-projection
Lindeberg condition whenever the comparison scale diverges.
-/
theorem finiteScoreCellSurveyProjectionLindebergCondition_of_tendsto_scale_atTop
    {Index Observation : Type*} {l : Filter Index}
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightBound loadingBound : Real)
    (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    finiteScoreCellSurveyProjectionLindebergCondition
      l sample cells weight score referenceShare loading scale normalizer := by
  intro epsilon hepsilon
  simpa [scoreCellSurveyProjectionLindebergTail] using
    tendsto_normalizer_mul_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_tendsto_scale_atTop
      (l := l) sample cells weight score referenceShare loading weightBound
      loadingBound epsilon scale normalizer hepsilon hscale hloading_nonneg
      hweight hloading hshare

/--
All finite score-cell loadings satisfying a deterministic envelope inherit the
concrete survey-projection Lindeberg condition.
-/
theorem finiteScoreCellSurveyProjectionLindebergCondition_all_loadings_of_tendsto_scale_atTop
    {Index Observation : Type*} {l : Filter Index}
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare : Cell -> Real)
    (weightBound : Real) (loadingBound : (Cell -> Real) -> Real)
    (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : ∀ loading, 0 ≤ loadingBound loading)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ loading cell, cell ∈ cells -> |loading cell| ≤ loadingBound loading)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    ∀ loading : Cell -> Real,
      finiteScoreCellSurveyProjectionLindebergCondition
        l sample cells weight score referenceShare loading scale normalizer := by
  intro loading
  exact
    finiteScoreCellSurveyProjectionLindebergCondition_of_tendsto_scale_atTop
      sample cells weight score referenceShare loading weightBound
      (loadingBound loading) scale normalizer hscale
      (hloading_nonneg loading) hweight (hloading loading) hshare

/--
Simplex reference shares replace the separate absolute-share bound in the
finite-cell survey-projection Lindeberg condition.
-/
theorem finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_tendsto_scale_atTop
    {Index Observation : Type*} {l : Filter Index}
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightBound loadingBound : Real)
    (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    finiteScoreCellSurveyProjectionLindebergCondition
      l sample cells weight score referenceShare loading scale normalizer :=
  finiteScoreCellSurveyProjectionLindebergCondition_of_tendsto_scale_atTop
    sample cells weight score referenceShare loading weightBound loadingBound
    scale normalizer hscale hloading_nonneg hweight hloading
    (fun cell hcell =>
      abs_referenceShare_le_one_of_mem_of_nonneg_sum_one
        cells referenceShare cell hcell hshare_nonneg hshare_sum)

/--
All finite score-cell loadings satisfying deterministic envelopes inherit the
concrete Lindeberg condition from simplex reference shares.
-/
theorem finiteScoreCellSurveyProjectionLindebergCondition_all_loadings_of_simplex_tendsto_scale_atTop
    {Index Observation : Type*} {l : Filter Index}
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare : Cell -> Real)
    (weightBound : Real) (loadingBound : (Cell -> Real) -> Real)
    (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : ∀ loading, 0 ≤ loadingBound loading)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ loading cell, cell ∈ cells -> |loading cell| ≤ loadingBound loading)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    ∀ loading : Cell -> Real,
      finiteScoreCellSurveyProjectionLindebergCondition
        l sample cells weight score referenceShare loading scale normalizer := by
  intro loading
  exact
    finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_tendsto_scale_atTop
      sample cells weight score referenceShare loading weightBound
      (loadingBound loading) scale normalizer hscale
      (hloading_nonneg loading) hweight (hloading loading)
      hshare_nonneg hshare_sum

/--
For fixed finite score cells, the canonical finite absolute-sum bound supplies
the loading envelope in the simplex survey-projection Lindeberg condition.
-/
theorem finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
    {Index Observation : Type*} {l : Filter Index}
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightBound : Real) (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    finiteScoreCellSurveyProjectionLindebergCondition
      l sample cells weight score referenceShare loading scale normalizer :=
  finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_tendsto_scale_atTop
    sample cells weight score referenceShare loading weightBound
    (finiteScoreCellLoadingAbsSumBound cells loading) scale normalizer hscale
    (finiteScoreCellLoadingAbsSumBound_nonneg cells loading) hweight
    (finiteScoreCellLoadingAbsSumBound_bound cells loading)
    hshare_nonneg hshare_sum

/--
Every fixed loading over finite score cells has the canonical finite
absolute-sum envelope needed for the all-loading simplex Lindeberg route.
-/
theorem finiteScoreCellSurveyProjectionLindebergCondition_all_loadings_of_simplex_finite_loading_tendsto_scale_atTop
    {Index Observation : Type*} {l : Filter Index}
    (sample : Index -> Finset Observation) (cells : Finset Cell)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (referenceShare : Cell -> Real)
    (weightBound : Real) (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    ∀ loading : Cell -> Real,
      finiteScoreCellSurveyProjectionLindebergCondition
        l sample cells weight score referenceShare loading scale normalizer := by
  intro loading
  exact
    finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
      sample cells weight score referenceShare loading weightBound scale
      normalizer hscale hweight hshare_nonneg hshare_sum

omit [DecidableEq Cell] in
/--
PATE double-score specialization of the concrete finite-cell survey-projection
Lindeberg condition under simplex reference shares.
-/
theorem finitePATEScoreCellSurveyProjectionLindebergCondition_of_simplex_tendsto_scale_atTop
    {Index Unit PropensityCell TreatedProgCell ControlProgCell : Type*}
    {l : Filter Index}
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    (sample : Index -> Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (weightBound loadingBound : Real)
    (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    finiteScoreCellSurveyProjectionLindebergCondition
      l sample cells weight
      (fun index =>
        pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      referenceShare loading scale normalizer :=
  finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_tendsto_scale_atTop
    sample cells weight
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    referenceShare loading weightBound loadingBound scale normalizer hscale
    hloading_nonneg hweight hloading hshare_nonneg hshare_sum

omit [DecidableEq Cell] in
/--
PATT double-score specialization of the concrete finite-cell survey-projection
Lindeberg condition under simplex reference shares.
-/
theorem finitePATTScoreCellSurveyProjectionLindebergCondition_of_simplex_tendsto_scale_atTop
    {Index Unit PropensityCell PATTProgCell : Type*}
    {l : Filter Index}
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    (sample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (weightBound loadingBound : Real)
    (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    finiteScoreCellSurveyProjectionLindebergCondition
      l sample cells weight
      (fun index =>
        pattDoubleScore (propensityScore index) (controlPrognosticScore index))
      referenceShare loading scale normalizer :=
  finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_tendsto_scale_atTop
    sample cells weight
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    referenceShare loading weightBound loadingBound scale normalizer hscale
    hloading_nonneg hweight hloading hshare_nonneg hshare_sum

omit [DecidableEq Cell] in
/--
PATE double-score Lindeberg condition with the loading envelope supplied by the
canonical finite absolute-sum bound.
-/
theorem
    finitePATEScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
    {Index Unit PropensityCell TreatedProgCell ControlProgCell : Type*}
    {l : Filter Index}
    [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
    [DecidableEq ControlProgCell]
    (sample : Index -> Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (weightBound : Real) (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    finiteScoreCellSurveyProjectionLindebergCondition
      l sample cells weight
      (fun index =>
        pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      referenceShare loading scale normalizer :=
  finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
    sample cells weight
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    referenceShare loading weightBound scale normalizer hscale hweight
    hshare_nonneg hshare_sum

omit [DecidableEq Cell] in
/--
PATT double-score Lindeberg condition with the loading envelope supplied by the
canonical finite absolute-sum bound.
-/
theorem
    finitePATTScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
    {Index Unit PropensityCell PATTProgCell : Type*}
    {l : Filter Index}
    [DecidableEq PropensityCell] [DecidableEq PATTProgCell]
    (sample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (weightBound : Real) (scale normalizer : Index -> Real)
    (hscale : Tendsto scale l atTop)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    finiteScoreCellSurveyProjectionLindebergCondition
      l sample cells weight
      (fun index =>
        pattDoubleScore (propensityScore index) (controlPrognosticScore index))
      referenceShare loading scale normalizer :=
  finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
    sample cells weight
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    referenceShare loading weightBound scale normalizer hscale hweight
    hshare_nonneg hshare_sum

omit [DecidableEq Cell] in
/--
Survey-Lindeberg scalar CLT packaging for one centered score-cell projection.

The probability content is exactly the two inputs `hlimitLaw` and `hclt`:
respectively the Gaussian limit law with the finite-cell variance target and
the centered survey projection convergence.  The theorem only packages them
into the typed scalar projection statement used by the vector bridge.
-/
theorem centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : Prop)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (hlindeberg : surveyLindebergCondition)
    (hlimitLaw :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        HasLaw (limitProjection loading)
          (gaussianReal 0
            (scoreCellLoadingReferenceCenteredSecondMoment
              cells referenceShare loading).toNNReal)
          limitLaw)
    (hclt :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        TendstoInDistribution
          (fun index sample => centeredProjection loading index sample)
          l (limitProjection loading) sampleLaw limitLaw) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection loading := by
  exact ⟨hlimitLaw hdesign hbounded hlindeberg,
    hclt hdesign hbounded hlindeberg⟩

omit [DecidableEq Cell] in
/--
Positive-variance scalar survey-Lindeberg CLT packager.

The Gaussian-law premise is stated with the positive `NNReal` variance
parameter built from the verified finite-cell centered second moment.  The
theorem rewrites that parameter to the `.toNNReal` form used by the existing
scalar CLT bridge, so future probability work does not have to expose a
truncation artifact.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_positive_nnreal_variance_of_survey_lindeberg
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : Prop)
    (hvariance_pos :
      0 <
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (hlindeberg : surveyLindebergCondition)
    (hlimitLaw :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        HasLaw (limitProjection loading)
          (gaussianReal 0
            ⟨scoreCellLoadingReferenceCenteredSecondMoment
              cells referenceShare loading, le_of_lt hvariance_pos⟩)
          limitLaw)
    (hclt :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        TendstoInDistribution
          (fun index sample => centeredProjection loading index sample)
          l (limitProjection loading) sampleLaw limitLaw) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection loading :=
  centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
    cells referenceShare loading l sampleLaw limitLaw centeredProjection
    limitProjection surveyDesignRegularity boundedScoreCellIndicators
    surveyLindebergCondition hdesign hbounded hlindeberg
    (fun hdesign hbounded hlindeberg => by
      simpa [
        scoreCellGaussianVarianceParameter_toNNReal_eq_positive_mk
          cells referenceShare loading hvariance_pos]
        using hlimitLaw hdesign hbounded hlindeberg)
    hclt

/--
Euclidean active-coordinate version of the scalar survey-Lindeberg projection
CLT packager.

Compared with
`centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg`,
the Gaussian law premise is stated with the active-coordinate centered second
moment.  Lean rewrites that expression to the verified WDSM variance target
for the corresponding zero-extended loading.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_active_euclidean_verified_variance_of_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : Prop)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (hlindeberg : surveyLindebergCondition)
    (hlimitLaw :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        HasLaw
          (limitProjection
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          (gaussianReal 0
            ((∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2).toNNReal))
          limitLaw)
    (hclt :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        TendstoInDistribution
          (fun index sample =>
            centeredProjection
              (finiteScoreCellEuclideanDirectionLoading cells direction)
              index sample)
          l
          (limitProjection
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          sampleLaw limitLaw) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection (finiteScoreCellEuclideanDirectionLoading cells direction) :=
  centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
    cells referenceShare (finiteScoreCellEuclideanDirectionLoading cells direction)
    l sampleLaw limitLaw centeredProjection limitProjection
    surveyDesignRegularity boundedScoreCellIndicators surveyLindebergCondition
    hdesign hbounded hlindeberg
    (fun hdesign hbounded hlindeberg => by
      simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
        using hlimitLaw hdesign hbounded hlindeberg)
    hclt

/--
Positive-variance Euclidean active-coordinate version of the scalar
survey-Lindeberg projection CLT packager.

The Gaussian-law premise is stated with the active-coordinate centered second
moment as a positive `NNReal`, so the remaining scalar survey-design CLT does
not have to mention either the ambient zero-extended loading variance or the
`.toNNReal` truncation form.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_active_euclidean_positive_nnreal_variance_of_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (direction : EuclideanSpace Real {cell // cell ∈ cells})
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : Prop)
    (hactive_pos :
      0 <
        ∑ cellIndex : {cell // cell ∈ cells},
          referenceShare cellIndex.1 *
            (direction cellIndex -
              ∑ other : {cell // cell ∈ cells},
                referenceShare other.1 * direction other) ^ 2)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (hlindeberg : surveyLindebergCondition)
    (hlimitLaw :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        HasLaw
          (limitProjection
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hclt :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        TendstoInDistribution
          (fun index sample =>
            centeredProjection
              (finiteScoreCellEuclideanDirectionLoading cells direction)
              index sample)
          l
          (limitProjection
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          sampleLaw limitLaw) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection (finiteScoreCellEuclideanDirectionLoading cells direction) :=
  centered_scoreCellLinearProjection_clt_with_positive_nnreal_variance_of_survey_lindeberg
    cells referenceShare (finiteScoreCellEuclideanDirectionLoading cells direction)
    l sampleLaw limitLaw centeredProjection limitProjection
    surveyDesignRegularity boundedScoreCellIndicators surveyLindebergCondition
    (by
      simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
        using hactive_pos)
    hdesign hbounded hlindeberg
    (fun hdesign hbounded hlindeberg => by
      simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
        using hlimitLaw hdesign hbounded hlindeberg)
    hclt

omit [DecidableEq Cell] in
/--
Active-cell version of the scalar survey-Lindeberg projection CLT packager for
an arbitrary finite-cell loading.

The Gaussian law premise is stated with the finite active-cell sum, and Lean
rewrites it to the verified WDSM variance target used by downstream CLT
bridges.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_active_loading_verified_variance_of_survey_lindeberg
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : Prop)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (hlindeberg : surveyLindebergCondition)
    (hlimitLaw :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        HasLaw (limitProjection loading)
          (gaussianReal 0
            ((∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (loading cellIndex.1 -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * loading other.1) ^ 2).toNNReal))
          limitLaw)
    (hclt :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        TendstoInDistribution
          (fun index sample => centeredProjection loading index sample)
          l (limitProjection loading) sampleLaw limitLaw) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection loading :=
  centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
    cells referenceShare loading l sampleLaw limitLaw centeredProjection
    limitProjection surveyDesignRegularity boundedScoreCellIndicators
    surveyLindebergCondition hdesign hbounded hlindeberg
    (fun hdesign hbounded hlindeberg => by
      simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
        using hlimitLaw hdesign hbounded hlindeberg)
    hclt

omit [DecidableEq Cell] in
/--
Positive-variance active-cell version of the scalar survey-Lindeberg
projection CLT packager.

The Gaussian-law premise is stated with the finite active-cell centered second
moment as a positive `NNReal`.  Lean rewrites that active expression to the
verified WDSM variance target used by the scalar CLT bridge.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_active_loading_positive_nnreal_variance_of_survey_lindeberg
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : Prop)
    (hactive_pos :
      0 <
        ∑ cellIndex : {cell // cell ∈ cells},
          referenceShare cellIndex.1 *
            (loading cellIndex.1 -
              ∑ other : {cell // cell ∈ cells},
                referenceShare other.1 * loading other.1) ^ 2)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (hlindeberg : surveyLindebergCondition)
    (hlimitLaw :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        HasLaw (limitProjection loading)
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (loading cellIndex.1 -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * loading other.1) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hclt :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        surveyLindebergCondition ->
        TendstoInDistribution
          (fun index sample => centeredProjection loading index sample)
          l (limitProjection loading) sampleLaw limitLaw) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection loading :=
  centered_scoreCellLinearProjection_clt_with_positive_nnreal_variance_of_survey_lindeberg
    cells referenceShare loading l sampleLaw limitLaw centeredProjection
    limitProjection surveyDesignRegularity boundedScoreCellIndicators
    surveyLindebergCondition
    (by
      simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
        using hactive_pos)
    hdesign hbounded hlindeberg
    (fun hdesign hbounded hlindeberg => by
      simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
        using hlimitLaw hdesign hbounded hlindeberg)
    hclt

/--
Finite score-cell vector-CLT bridge whose all-linear-projection field is the
typed family of scalar centered survey projection CLTs with verified variance.

This constructor does not prove the survey-design scalar CLT or the
Cramer-Wold/vector theorem.  It fixes the exact interface between them.
-/
def finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT) :
    FiniteScoreCellVectorCLTBridge Cell where
  cells := cells
  referenceShare := referenceShare
  simplex_reference_shares := simplexReferenceShares
  all_linear_projection_clts_with_verified_variance :=
    ∀ loading : Cell -> Real,
      centeredScoreCellLinearProjectionCLTWithVerifiedVariance
        cells referenceShare l sampleLaw limitLaw centeredProjection
        limitProjection loading
  covariance_matrix_tangent_space_verified :=
    covarianceMatrixTangentSpaceVerified
  finite_dimensional_score_cell_vector_clt :=
    finiteDimensionalScoreCellVectorCLT
  bridge := cramerWold

/--
Survey-design scalar projection CLTs discharge the all-linear-projection field
of the finite score-cell vector bridge.
-/
theorem finite_score_cell_all_linear_projection_clts_with_verified_variance_of_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : (Cell -> Real) -> Prop)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlindeberg : ∀ loading, surveyLindebergCondition loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          surveyLindebergCondition loading ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          surveyLindebergCondition loading ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).all_linear_projection_clts_with_verified_variance := by
  intro loading
  exact
    centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
      cells referenceShare loading l sampleLaw limitLaw centeredProjection
      limitProjection (surveyDesignRegularity loading)
      (boundedScoreCellIndicators loading) (surveyLindebergCondition loading)
      (hdesign loading) (hbounded loading) (hlindeberg loading)
      (hlimitLaw loading) (hclt loading)

/--
Survey-design scalar projection CLTs discharge the all-linear-projection field
after removing deterministic zero-variance directions.

For loadings with verified finite-cell variance zero, it uses pointwise-zero
source and limit projections plus the degenerate Gaussian law.  The genuine
survey-design Gaussian-law and scalar-CLT inputs are required only for
nonzero-variance loadings.
-/
theorem
    finite_score_cell_all_linear_projection_clts_with_verified_variance_of_survey_lindeberg_or_pointwise_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : (Cell -> Real) -> Prop)
    (hsource_zero :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading = 0 ->
        ∀ index sample, centeredProjection loading index sample = 0)
    (hlimit_zero :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading = 0 ->
        ∀ sample, limitProjection loading sample = 0)
    (hdesign :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        surveyDesignRegularity loading)
    (hbounded :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        boundedScoreCellIndicators loading)
    (hlindeberg :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        surveyLindebergCondition loading)
    (hlimitLaw :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          surveyLindebergCondition loading ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          surveyLindebergCondition loading ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).all_linear_projection_clts_with_verified_variance := by
  intro loading
  by_cases hvariance :
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading = 0
  · exact
      centeredScoreCellLinearProjectionCLTWithVerifiedVariance_of_pointwise_zero
        cells referenceShare loading l sampleLaw limitLaw centeredProjection
        limitProjection hvariance (hsource_zero loading hvariance)
        (hlimit_zero loading hvariance)
  · exact
      centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
        cells referenceShare loading l sampleLaw limitLaw centeredProjection
        limitProjection (surveyDesignRegularity loading)
        (boundedScoreCellIndicators loading) (surveyLindebergCondition loading)
        (hdesign loading hvariance) (hbounded loading hvariance)
        (hlindeberg loading hvariance)
        (hlimitLaw loading hvariance) (hclt loading hvariance)

/--
Bounded finite-cell large-jump control discharges the Lindeberg part of the
named scalar survey projection CLT boundary for one loading.

This theorem leaves only the genuine scalar probability content as hypotheses:
the Gaussian limit law with the verified finite-cell variance and the centered
projection convergence in distribution.
-/
theorem
    centered_scoreCellLinearProjection_clt_with_verified_variance_of_bounded_finite_tail_survey_lindeberg
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (scale normalizer : Index -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators : Prop)
    (weightBound loadingBound : Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ finiteSample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (hlimitLaw :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        finiteScoreCellSurveyProjectionLindebergCondition
          l finiteSample cells weight score referenceShare loading scale normalizer ->
        HasLaw (limitProjection loading)
          (gaussianReal 0
            (scoreCellLoadingReferenceCenteredSecondMoment
              cells referenceShare loading).toNNReal)
          limitLaw)
    (hclt :
      surveyDesignRegularity ->
        boundedScoreCellIndicators ->
        finiteScoreCellSurveyProjectionLindebergCondition
          l finiteSample cells weight score referenceShare loading scale normalizer ->
        TendstoInDistribution
          (fun index sample => centeredProjection loading index sample)
          l (limitProjection loading) sampleLaw limitLaw) :
    centeredScoreCellLinearProjectionCLTWithVerifiedVariance
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection loading := by
  exact
    centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
      cells referenceShare loading l sampleLaw limitLaw centeredProjection
      limitProjection surveyDesignRegularity boundedScoreCellIndicators
      (finiteScoreCellSurveyProjectionLindebergCondition
        l finiteSample cells weight score referenceShare loading scale normalizer)
      hdesign hbounded
      (finiteScoreCellSurveyProjectionLindebergCondition_of_tendsto_scale_atTop
        finiteSample cells weight score referenceShare loading weightBound
        loadingBound scale normalizer hscale hloading_nonneg hweight
        hloading hshare)
      hlimitLaw hclt

/--
Bounded finite-cell large-jump control discharges the Lindeberg part of the
all-linear survey projection CLT bridge.

The remaining probability obligations are exactly `hlimitLaw` and `hclt` for
each loading, now using the concrete finite-tail Lindeberg condition rather
than an abstract raw stochastic field.
-/
theorem
    finite_score_cell_all_linear_projection_clts_with_verified_variance_of_bounded_finite_tail_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (scale normalizer : Index -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real) (loadingBound : (Cell -> Real) -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : ∀ loading, 0 ≤ loadingBound loading)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ finiteSample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ loading cell, cell ∈ cells -> |loading cell| ≤ loadingBound loading)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).all_linear_projection_clts_with_verified_variance := by
  exact
    finite_score_cell_all_linear_projection_clts_with_verified_variance_of_survey_lindeberg
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      (fun loading =>
        finiteScoreCellSurveyProjectionLindebergCondition
          l finiteSample cells weight score referenceShare loading scale normalizer)
      hdesign hbounded
      (finiteScoreCellSurveyProjectionLindebergCondition_all_loadings_of_tendsto_scale_atTop
        finiteSample cells weight score referenceShare weightBound loadingBound
        scale normalizer hscale hloading_nonneg hweight hloading hshare)
      hlimitLaw hclt

/--
Bounded finite-cell large-jump control plus a Cramer-Wold/vector map gives the
packaged finite-dimensional score-cell vector CLT.

The theorem still leaves the scalar centered projection CLT and Gaussian limit
law as explicit probability inputs for every loading.
-/
theorem finite_score_cell_vector_clt_of_bounded_finite_tail_survey_lindeberg_projection_bridge
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (scale normalizer : Index -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real) (loadingBound : (Cell -> Real) -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : ∀ loading, 0 ≤ loadingBound loading)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ finiteSample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ loading cell, cell ∈ cells -> |loading cell| ≤ loadingBound loading)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_bridge
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold)
    hsimplex
    (finite_score_cell_all_linear_projection_clts_with_verified_variance_of_bounded_finite_tail_survey_lindeberg
      cells referenceShare l sampleLaw limitLaw finiteSample weight score
      centeredProjection limitProjection scale normalizer simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      weightBound loadingBound hscale hloading_nonneg hweight hloading
      hshare hdesign hbounded hlimitLaw hclt)
    hmatrix

/--
Simplex reference shares plus bounded finite-cell large-jump control discharge
the all-linear survey projection field.
-/
theorem
    finite_score_cell_all_linear_projection_clts_with_verified_variance_of_simplex_bounded_finite_tail_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (scale normalizer : Index -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real) (loadingBound : (Cell -> Real) -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : ∀ loading, 0 ≤ loadingBound loading)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ finiteSample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ loading cell, cell ∈ cells -> |loading cell| ≤ loadingBound loading)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).all_linear_projection_clts_with_verified_variance := by
  exact
    finite_score_cell_all_linear_projection_clts_with_verified_variance_of_bounded_finite_tail_survey_lindeberg
      cells referenceShare l sampleLaw limitLaw finiteSample weight score
      centeredProjection limitProjection scale normalizer simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      weightBound loadingBound hscale hloading_nonneg hweight hloading
      (fun cell hcell =>
        abs_referenceShare_le_one_of_mem_of_nonneg_sum_one
          cells referenceShare cell hcell hshare_nonneg hshare_sum)
      hdesign hbounded hlimitLaw hclt

/--
Simplex reference shares plus bounded finite-cell large-jump control and a
Cramer-Wold/vector map give the packaged finite-dimensional score-cell vector
CLT.
-/
theorem
    finite_score_cell_vector_clt_of_simplex_bounded_finite_tail_survey_lindeberg_projection_bridge
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (scale normalizer : Index -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real) (loadingBound : (Cell -> Real) -> Real)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : ∀ loading, 0 ≤ loadingBound loading)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ finiteSample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ loading cell, cell ∈ cells -> |loading cell| ≤ loadingBound loading)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_bridge
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold)
    hsimplex
    (finite_score_cell_all_linear_projection_clts_with_verified_variance_of_simplex_bounded_finite_tail_survey_lindeberg
      cells referenceShare l sampleLaw limitLaw finiteSample weight score
      centeredProjection limitProjection scale normalizer simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      weightBound loadingBound hscale hloading_nonneg hweight hloading
      hshare_nonneg hshare_sum hdesign hbounded hlimitLaw hclt)
    hmatrix

/--
Simplex reference shares and canonical finite absolute-sum loading envelopes
discharge the all-linear survey projection field.
-/
theorem
    finite_score_cell_all_linear_projection_clts_with_verified_variance_of_simplex_finite_loading_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (scale normalizer : Index -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real)
    (hscale : Tendsto scale l atTop)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ finiteSample index -> |weight index unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).all_linear_projection_clts_with_verified_variance := by
  exact
    finite_score_cell_all_linear_projection_clts_with_verified_variance_of_simplex_bounded_finite_tail_survey_lindeberg
      cells referenceShare l sampleLaw limitLaw finiteSample weight score
      centeredProjection limitProjection scale normalizer simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      weightBound (fun loading => finiteScoreCellLoadingAbsSumBound cells loading)
      hscale (fun loading => finiteScoreCellLoadingAbsSumBound_nonneg cells loading)
      hweight
      (fun loading => finiteScoreCellLoadingAbsSumBound_bound cells loading)
      hshare_nonneg hshare_sum hdesign hbounded hlimitLaw hclt

/--
All-linear survey-Lindeberg CLT field with scalar Gaussian laws stated on the
active finite-cell subtype.

This feeds `FiniteScoreCellVectorCLTBridge.all_linear_projection_clts_with_verified_variance`
from scalar CLT inputs whose variance is the active-cell centered second
moment.  The proof reuses the checked finite-loading Lindeberg reducer and
only rewrites the variance target; it does not assume the vector CLT.
-/
theorem
    finite_score_cell_all_linear_projection_clts_with_active_loading_variance_of_simplex_finite_loading_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (scale normalizer : Index -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real)
    (hscale : Tendsto scale l atTop)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ finiteSample index -> |weight index unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              ((∑ cellIndex : {cell // cell ∈ cells},
                referenceShare cellIndex.1 *
                  (loading cellIndex.1 -
                    ∑ other : {cell // cell ∈ cells},
                      referenceShare other.1 * loading other.1) ^ 2).toNNReal))
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).all_linear_projection_clts_with_verified_variance := by
  exact
    finite_score_cell_all_linear_projection_clts_with_verified_variance_of_simplex_finite_loading_survey_lindeberg
      cells referenceShare l sampleLaw limitLaw finiteSample weight score
      centeredProjection limitProjection scale normalizer simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      weightBound hscale hweight hshare_nonneg hshare_sum hdesign hbounded
      (fun loading hdesign hbounded hlindeberg => by
        simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
          using hlimitLaw loading hdesign hbounded hlindeberg)
      hclt

/--
Simplex reference shares, canonical finite loading envelopes, and a
Cramer-Wold/vector map give the packaged finite-dimensional score-cell vector
CLT.
-/
theorem
    finite_score_cell_vector_clt_of_simplex_finite_loading_survey_lindeberg_projection_bridge
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : Index -> Finset Observation)
    (weight : Index -> Observation -> Real)
    (score : Index -> Observation -> Cell)
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (scale normalizer : Index -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real)
    (hscale : Tendsto scale l atTop)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ finiteSample index -> |weight index unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            l finiteSample cells weight score referenceShare loading scale normalizer ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_bridge
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold)
    hsimplex
    (finite_score_cell_all_linear_projection_clts_with_verified_variance_of_simplex_finite_loading_survey_lindeberg
      cells referenceShare l sampleLaw limitLaw finiteSample weight score
      centeredProjection limitProjection scale normalizer simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      weightBound hscale hweight hshare_nonneg hshare_sum hdesign hbounded
      hlimitLaw hclt)
    hmatrix

/--
Euclidean active-cell version of the simplex finite-loading survey-Lindeberg
vector CLT route.

The vector target is the concrete space
`EuclideanSpace ℝ {cell // cell ∈ cells}`.  The deterministic Cramer-Wold
representation and the finite-loading Lindeberg tail are both discharged in
Lean, leaving only the scalar survey-design projection CLT and Gaussian
limit-law inputs for each Euclidean direction.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (vector : ℕ -> Sample -> EuclideanSpace Real {cell // cell ∈ cells})
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hvector : ∀ n, AEMeasurable (vector n) (sampleLaw n))
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale normalizer : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hdesign :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        surveyDesignRegularity
          (finiteScoreCellEuclideanDirectionLoading cells direction))
    (hbounded :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        boundedScoreCellIndicators
          (finiteScoreCellEuclideanDirectionLoading cells direction))
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells vector loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_direction_projection_clts
    cells referenceShare sampleLaw limitLaw vector limitVector hvector hlimitVector
    simplexReferenceShares covarianceMatrixTangentSpaceVerified hsimplex hmatrix
    (fun direction =>
      centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
        cells referenceShare
        (finiteScoreCellEuclideanDirectionLoading cells direction)
        atTop sampleLaw limitLaw
        (finiteScoreCellEuclideanProjection cells vector)
        (finiteScoreCellEuclideanLimitProjection cells limitVector)
        (surveyDesignRegularity
          (finiteScoreCellEuclideanDirectionLoading cells direction))
        (boundedScoreCellIndicators
          (finiteScoreCellEuclideanDirectionLoading cells direction))
        (finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer)
        (hdesign direction) (hbounded direction)
        (finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
          finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightBound scale normalizer hscale hweight hshare_nonneg hshare_sum)
    (hlimitLaw direction) (hclt direction))

/--
Euclidean simplex finite-loading vector CLT route with the degenerate
constant-one active direction discharged internally.

Compared with
`finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg`,
the scalar survey-design CLT and Gaussian-law inputs are required only for
directions different from the constant-one active direction.  The constant-one
projection is handled by the concrete tangent-space proof for the scaled
finite-cell mass vector and the degenerate Gaussian law `gaussianReal 0 0`.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_off_const_one
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hdesign :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        surveyDesignRegularity
          (finiteScoreCellEuclideanDirectionLoading cells direction))
    (hbounded :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        boundedScoreCellIndicators
          (finiteScoreCellEuclideanDirectionLoading cells direction))
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells
                (fun n _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample n) (weight n) (score n)
                    referenceShare (normalizer n))
                loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt := by
  let directionOne : EuclideanSpace Real {cell // cell ∈ cells} :=
    WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
      (1 : Real))
  let vector : ℕ -> Sample -> EuclideanSpace Real {cell // cell ∈ cells} :=
    fun n _sample =>
      finiteScoreCellScaledCenteredMassVector cells
        (finiteSample n) (weight n) (score n) referenceShare
        (normalizer n)
  exact
    finite_score_cell_vector_clt_of_euclidean_direction_projection_clts
      cells referenceShare sampleLaw limitLaw vector limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified hsimplex hmatrix
      (fun direction => by
        by_cases hdirection : direction = directionOne
        · subst direction
          simpa [vector, directionOne]
            using
              centered_scoreCellLinearProjection_clt_const_one_of_scaledCenteredMassVector
                cells referenceShare atTop sampleLaw limitLaw finiteSample weight
                score normalizer limitVector hcover hshare_sum hlimit_tangent
        · exact
            centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
              cells referenceShare
              (finiteScoreCellEuclideanDirectionLoading cells direction)
              atTop sampleLaw limitLaw
              (finiteScoreCellEuclideanProjection cells vector)
              (finiteScoreCellEuclideanLimitProjection cells limitVector)
              (surveyDesignRegularity
                (finiteScoreCellEuclideanDirectionLoading cells direction))
              (boundedScoreCellIndicators
                (finiteScoreCellEuclideanDirectionLoading cells direction))
              (finiteScoreCellSurveyProjectionLindebergCondition
                atTop finiteSample cells weight score referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction)
                scale normalizer)
              (hdesign direction hdirection) (hbounded direction hdirection)
              (finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
                finiteSample cells weight score referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction)
                weightBound scale normalizer hscale hweight hshare_nonneg
                hshare_sum)
              (hlimitLaw direction hdirection) (hclt direction hdirection))

/--
Off-constant-one Euclidean vector CLT route with the nonconstant
`boundedScoreCellIndicators` field replaced by concrete finite projection
second-moment evidence.

The required boundedness input for each nonconstant direction is proved from
an eventual total absolute-weight bound using
`finiteScoreCellWeightedCenteredSecondMomentBound_of_eventually_total_abs_weight_bound`.
The nonconstant scalar Gaussian laws and scalar projection CLTs still remain
as the genuine survey-design probability inputs.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_off_const_one_moment_bound
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity : (Cell -> Real) -> Prop)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hdesign :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        surveyDesignRegularity
          (finiteScoreCellEuclideanDirectionLoading cells direction))
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        surveyDesignRegularity loading ->
          finiteScoreCellWeightedCenteredSecondMomentBound
            atTop finiteSample cells weight score referenceShare loading
            weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        surveyDesignRegularity loading ->
          finiteScoreCellWeightedCenteredSecondMomentBound
            atTop finiteSample cells weight score referenceShare loading
            weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells
                (fun n _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample n) (weight n) (score n)
                    referenceShare (normalizer n))
                loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt := by
  exact
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_off_const_one
      cells referenceShare sampleLaw limitLaw finiteSample weight score normalizer
      limitVector hlimitVector scale simplexReferenceShares
      covarianceMatrixTangentSpaceVerified hsimplex hmatrix
      surveyDesignRegularity
      (fun loading =>
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound)
      weightBound hscale hweight hcover hshare_nonneg hshare_sum
      hlimit_tangent hdesign
      (fun direction _hdirection =>
        finiteScoreCellWeightedCenteredSecondMomentBound_of_eventually_total_abs_weight_bound
          finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound hweightTotal)
      hlimitLaw hclt

/--
Off-constant-one Euclidean vector CLT route with both generic side fields
removed from the nonconstant scalar interface.

Compared with
`finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_off_const_one_moment_bound`,
this theorem instantiates the abstract `surveyDesignRegularity` field by
`True`.  The scalar survey-design inputs therefore receive only concrete
finite-projection second-moment evidence, concrete finite-loading Lindeberg
evidence, and the remaining Gaussian law / scalar projection CLT obligations.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_off_const_one_moment_bound_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        direction ≠
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real)) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells
                (fun n _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample n) (weight n) (score n)
                    referenceShare (normalizer n))
                loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt := by
  exact
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_off_const_one_moment_bound
      cells referenceShare sampleLaw limitLaw finiteSample weight score normalizer
      limitVector hlimitVector scale simplexReferenceShares
      covarianceMatrixTangentSpaceVerified hsimplex hmatrix
      (fun _loading => True) weightBound weightTotalBound hscale hweight
      hweightTotal hcover hshare_nonneg hshare_sum hlimit_tangent
      (fun _direction _hdirection => trivial)
      (fun direction hdirection _hdesign hmoment hlindeberg =>
        hlimitLaw direction hdirection hmoment hlindeberg)
      (fun direction hdirection _hdesign hmoment hlindeberg =>
        hclt direction hdirection hmoment hlindeberg)

/--
Euclidean simplex finite-loading vector CLT route with all verified
zero-variance directions removed from the scalar survey-CLT burden.

The concrete vector is the scaled centered finite score-cell mass vector.
For directions whose verified finite-cell centered second moment is zero, the
theorem uses pointwise-zero source and limit projection evidence together with
the degenerate Gaussian law.  For nonzero-variance directions, it supplies the
checked finite-loading Lindeberg and weighted second-moment evidence, leaving
only the genuine scalar survey-design Gaussian law and CLT as probability
inputs.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_zero_variance_split_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hsource_zero :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction) = 0 ->
        ∀ n (sample : Sample),
          finiteScoreCellEuclideanProjection cells
            (fun n _sample =>
              finiteScoreCellScaledCenteredMassVector cells
                (finiteSample n) (weight n) (score n) referenceShare
                (normalizer n))
            (finiteScoreCellEuclideanDirectionLoading cells direction)
            n sample = 0)
    (hlimit_zero :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction) = 0 ->
        ∀ sample,
          finiteScoreCellEuclideanLimitProjection cells limitVector
            (finiteScoreCellEuclideanDirectionLoading cells direction)
            sample = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction) ≠ 0 ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction) ≠ 0 ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells
                (fun n _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample n) (weight n) (score n)
                    referenceShare (normalizer n))
                loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt := by
  let vector : ℕ -> Sample -> EuclideanSpace Real {cell // cell ∈ cells} :=
    fun n _sample =>
      finiteScoreCellScaledCenteredMassVector cells
        (finiteSample n) (weight n) (score n) referenceShare
        (normalizer n)
  exact
    finite_score_cell_vector_clt_of_euclidean_direction_projection_clts
      cells referenceShare sampleLaw limitLaw vector limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified hsimplex hmatrix
      (fun direction => by
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        by_cases hvariance :
            scoreCellLoadingReferenceCenteredSecondMoment
              cells referenceShare loading = 0
        · exact
            centeredScoreCellLinearProjectionCLTWithVerifiedVariance_of_pointwise_zero
              cells referenceShare loading atTop sampleLaw limitLaw
              (finiteScoreCellEuclideanProjection cells vector)
              (finiteScoreCellEuclideanLimitProjection cells limitVector)
              hvariance
              (by
                intro n sample
                simpa [vector, loading] using
                  hsource_zero direction hvariance n sample)
              (by
                intro sample
                simpa [loading] using
                  hlimit_zero direction hvariance sample)
        · exact
            centered_scoreCellLinearProjection_clt_with_verified_variance_of_survey_lindeberg
              cells referenceShare loading atTop sampleLaw limitLaw
              (finiteScoreCellEuclideanProjection cells vector)
              (finiteScoreCellEuclideanLimitProjection cells limitVector)
              True
              (finiteScoreCellWeightedCenteredSecondMomentBound
                atTop finiteSample cells weight score referenceShare loading
                weightTotalBound)
              (finiteScoreCellSurveyProjectionLindebergCondition
                atTop finiteSample cells weight score referenceShare loading
                scale normalizer)
              trivial
              (finiteScoreCellWeightedCenteredSecondMomentBound_of_eventually_total_abs_weight_bound
                finiteSample cells weight score referenceShare loading
                weightTotalBound hweightTotal)
              (finiteScoreCellSurveyProjectionLindebergCondition_of_simplex_finite_loading_tendsto_scale_atTop
                finiteSample cells weight score referenceShare loading
                weightBound scale normalizer hscale hweight hshare_nonneg
                hshare_sum)
              (fun _hdesign hmoment hlindeberg =>
                hlimitLaw direction hvariance hmoment hlindeberg)
              (fun _hdesign hmoment hlindeberg =>
                hclt direction hvariance hmoment hlindeberg))

/--
Concrete Euclidean scaled-mass-vector CLT route whose zero-variance projection
evidence is derived from positive active reference shares.

Strict positivity of each active reference share turns zero verified centered
second moment into a constant Euclidean direction.  The concrete scaled mass
vector is tangent by finite score-cell coverage and simplex shares, and the
limit vector is assumed tangent.  Therefore all zero-variance projections are
proved pointwise zero internally; only nonzero-variance scalar survey-design
Gaussian laws and projection CLTs remain as stochastic inputs.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_zero_variance_positive_share_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction) ≠ 0 ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction) ≠ 0 ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells
                (fun n _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample n) (weight n) (score n)
                    referenceShare (normalizer n))
                loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_zero_variance_split_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal
    (fun cell hcell => le_of_lt (hshare_pos cell hcell)) hshare_sum
    (fun direction hvariance n sample =>
      finiteScoreCellEuclideanProjection_scaledCenteredMassVector_eq_zero_of_centeredSecondMoment_eq_zero
        cells referenceShare direction finiteSample weight score normalizer
        n sample (hcover n) hshare_sum hshare_pos hvariance)
    (fun direction hvariance sample =>
      finiteScoreCellEuclideanLimitProjection_eq_zero_of_centeredSecondMoment_eq_zero
        cells referenceShare direction limitVector sample hshare_pos hvariance
        hlimit_tangent)
    hlimitLaw hclt

/--
Concrete Euclidean vector CLT route with the remaining scalar survey-design
inputs stated exactly on nonconstant active-cell directions.

Positive active reference shares identify the zero-variance directions with
constant active Euclidean directions.  Therefore the source/limit degenerate
directions are discharged internally, and the probability assumptions are
needed only for directions with two different active coordinates.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_positive_share_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells
                (fun n _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample n) (weight n) (score n)
                    referenceShare (normalizer n))
                loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_zero_variance_positive_share_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hvariance hmoment hlindeberg =>
      hlimitLaw direction
        (finiteScoreCellEuclideanDirectionNonconstant_of_centeredSecondMoment_ne_zero
          cells referenceShare direction hshare_sum hvariance)
        hmoment hlindeberg)
    (fun direction hvariance hmoment hlindeberg =>
      hclt direction
        (finiteScoreCellEuclideanDirectionNonconstant_of_centeredSecondMoment_ne_zero
          cells referenceShare direction hshare_sum hvariance)
        hmoment hlindeberg)

/--
Concrete Euclidean vector CLT route with positive-variance evidence supplied
to the remaining scalar survey-design inputs.

Under positive active reference shares, nonconstant directions have strictly
positive verified variance.  This theorem passes that deterministic positivity
to the scalar Gaussian-law and projection-CLT obligations, so the remaining
probability theorem can be stated on genuinely nondegenerate scalar
projections.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_positive_variance_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        0 <
          scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
            (finiteScoreCellEuclideanDirectionLoading cells direction) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        0 <
          scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
            (finiteScoreCellEuclideanDirectionLoading cells direction) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells
                (fun n _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample n) (weight n) (score n)
                    referenceShare (normalizer n))
                loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_positive_share_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hnonconstant hmoment hlindeberg =>
      hlimitLaw direction
        (scoreCellLoadingReferenceCenteredSecondMoment_pos_of_euclideanDirectionNonconstant
          cells referenceShare direction hshare_pos hnonconstant)
        hmoment hlindeberg)
    (fun direction hnonconstant hmoment hlindeberg =>
      hclt direction
        (scoreCellLoadingReferenceCenteredSecondMoment_pos_of_euclideanDirectionNonconstant
          cells referenceShare direction hshare_pos hnonconstant)
        hmoment hlindeberg)

/--
Positive-variance Euclidean vector CLT route with the scalar Gaussian law
stated using a positive `NNReal` variance parameter.

This removes the final `.toNNReal` truncation from the probability-facing
Gaussian-law premise.  The theorem rewrites that positive parameter back to
the verified finite-cell variance used by the existing scalar projection
interface.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_positive_nnreal_variance_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        (hvariance_pos :
          0 <
            scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
              (finiteScoreCellEuclideanDirectionLoading cells direction)) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare
            (finiteScoreCellEuclideanDirectionLoading cells direction)
            scale normalizer ->
          HasLaw
            (finiteScoreCellEuclideanLimitProjection cells limitVector
              (finiteScoreCellEuclideanDirectionLoading cells direction))
            (gaussianReal 0
              ⟨scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction),
                le_of_lt hvariance_pos⟩)
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        0 <
          scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
            (finiteScoreCellEuclideanDirectionLoading cells direction) ->
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare loading
          weightTotalBound ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells
                (fun n _sample =>
                  finiteScoreCellScaledCenteredMassVector cells
                    (finiteSample n) (weight n) (score n)
                    referenceShare (normalizer n))
                loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_positive_variance_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hvariance_pos hmoment hlindeberg => by
      simpa [
        scoreCellGaussianVarianceParameter_toNNReal_eq_positive_mk
          cells referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          hvariance_pos]
        using hlimitLaw direction hvariance_pos hmoment hlindeberg)
    hclt

/--
Positive-variance Euclidean vector CLT route whose scalar probability inputs
are stated entirely in active coordinates.

Compared with
`finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_positive_nnreal_variance_no_design`,
the nondegenerate scalar Gaussian-law and projection-CLT premises receive the
strict positivity proof for the active finite-cell variance expression itself.
This is the narrowed boundary for the remaining survey-design scalar CLT.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_active_positive_nnreal_variance_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
        finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer ->
        HasLaw
          (finiteScoreCellEuclideanLimitProjection cells limitVector
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
        finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer ->
        TendstoInDistribution
          (fun n sample =>
            finiteScoreCellEuclideanProjection cells
              (fun n _sample =>
                finiteScoreCellScaledCenteredMassVector cells
                  (finiteSample n) (weight n) (score n)
                  referenceShare (normalizer n))
              (finiteScoreCellEuclideanDirectionLoading cells direction) n sample)
          atTop
          (finiteScoreCellEuclideanLimitProjection cells limitVector
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_positive_nnreal_variance_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hvariance_pos hmoment hlindeberg => by
      have hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2 := by
        simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
          using hvariance_pos
      simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
        using hlimitLaw direction hactive_pos hmoment hlindeberg)
    (fun direction hvariance_pos hmoment hlindeberg => by
      have hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2 := by
        simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
          using hvariance_pos
      exact hclt direction hactive_pos hmoment hlindeberg)

/--
Euclidean vector CLT route whose remaining scalar probability inputs are
indexed by nonconstant active directions and receive the checked positive
active-coordinate variance.

This is the same finite-dimensional target as the active positive-variance
route above, but the stochastic theorem to be proved downstream is now stated
on the natural nondegenerate directions: active directions with two unequal
coordinates.  The conversion from positive active variance to nonconstancy is
proved deterministically here.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_active_positive_nnreal_variance_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
        finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer ->
        HasLaw
          (finiteScoreCellEuclideanLimitProjection cells limitVector
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
        finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer ->
        TendstoInDistribution
          (fun n sample =>
            finiteScoreCellEuclideanProjection cells
              (fun n _sample =>
                finiteScoreCellScaledCenteredMassVector cells
                  (finiteSample n) (weight n) (score n)
                  referenceShare (normalizer n))
              (finiteScoreCellEuclideanDirectionLoading cells direction) n sample)
          atTop
          (finiteScoreCellEuclideanLimitProjection cells limitVector
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_active_positive_nnreal_variance_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hactive_pos hmoment hlindeberg =>
      hlimitLaw direction
        (finiteScoreCellEuclideanDirectionNonconstant_of_activeCenteredSecondMoment_pos
          cells referenceShare direction hshare_sum hactive_pos)
        hactive_pos hmoment hlindeberg)
    (fun direction hactive_pos hmoment hlindeberg =>
      hclt direction
        (finiteScoreCellEuclideanDirectionNonconstant_of_activeCenteredSecondMoment_pos
          cells referenceShare direction hshare_sum hactive_pos)
        hactive_pos hmoment hlindeberg)

/--
Concrete weighted-sum version of the nonconstant active positive-variance
Euclidean vector CLT route.

The remaining scalar survey-design CLT is stated for the actual normalized
weighted centered score-cell sum
`normalizer n * weightedSampleSum ...`, rather than for the Euclidean
projection wrapper.  The proof uses the checked pointwise identity between
that weighted sum and the projection of the concrete scaled centered
mass-vector.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_active_positive_nnreal_weighted_sum_clt_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
        finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer ->
        HasLaw
          (finiteScoreCellEuclideanLimitProjection cells limitVector
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
        finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer ->
        TendstoInDistribution
          (fun n _sample =>
            normalizer n * weightedSampleSum (finiteSample n) (weight n)
              (scoreCellLinearCenteredIndicator cells (score n) referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction)))
          atTop
          (finiteScoreCellEuclideanLimitProjection cells limitVector
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_active_positive_nnreal_variance_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent hlimitLaw
    (fun direction hnonconstant hactive_pos hmoment hlindeberg => by
      let loading := finiteScoreCellEuclideanDirectionLoading cells direction
      let weightedProjection : ℕ -> Sample -> Real := fun n _sample =>
        normalizer n * weightedSampleSum (finiteSample n) (weight n)
          (scoreCellLinearCenteredIndicator cells (score n) referenceShare
            loading)
      let euclideanProjection : ℕ -> Sample -> Real := fun n sample =>
        finiteScoreCellEuclideanProjection cells
          (fun n _sample =>
            finiteScoreCellScaledCenteredMassVector cells
              (finiteSample n) (weight n) (score n) referenceShare
              (normalizer n))
          loading n sample
      let limitProjection : LimitSample -> Real :=
        finiteScoreCellEuclideanLimitProjection cells limitVector loading
      have hweighted :
          TendstoInDistribution weightedProjection atTop limitProjection
            sampleLaw limitLaw :=
        hclt direction hnonconstant hactive_pos hmoment hlindeberg
      exact
        MeasureTheory.TendstoInDistribution.congr
          (X := weightedProjection) (Y := euclideanProjection)
          (Z := limitProjection) (T := limitProjection)
          (μ := sampleLaw) (μ' := limitLaw) (l := atTop)
          (fun n =>
            Filter.Eventually.of_forall
              (fun sample => by
                dsimp [weightedProjection, euclideanProjection, loading]
                exact
                  (finiteScoreCellEuclideanProjection_scaledCenteredMassVector_eq_scaled_weightedSampleSum
                    cells finiteSample weight score referenceShare loading
                    normalizer n sample).symm))
          (Filter.Eventually.of_forall fun _sample => rfl)
          hweighted)

/--
Concrete weighted-sum/inner-limit version of the nonconstant active
positive-variance Euclidean vector CLT route.

The scalar probability theorem can now be stated entirely in the paper-level
coordinates: the source is the normalized weighted centered score-cell sum and
the limit variable is the active Euclidean inner product
`⟪limitVector, direction⟫`.  The proof rewrites the limit side through the
checked identity for `finiteScoreCellEuclideanLimitProjection`.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_active_positive_nnreal_weighted_sum_inner_limit_clt_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
        finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer ->
        HasLaw
          (fun sample => ⟪limitVector sample, direction⟫)
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        finiteScoreCellWeightedCenteredSecondMomentBound
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          weightTotalBound ->
        finiteScoreCellSurveyProjectionLindebergCondition
          atTop finiteSample cells weight score referenceShare
          (finiteScoreCellEuclideanDirectionLoading cells direction)
          scale normalizer ->
        TendstoInDistribution
          (fun n _sample =>
            normalizer n * weightedSampleSum (finiteSample n) (weight n)
              (scoreCellLinearCenteredIndicator cells (score n) referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction)))
          atTop (fun sample => ⟪limitVector sample, direction⟫)
          sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_active_positive_nnreal_weighted_sum_clt_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hnonconstant hactive_pos hmoment hlindeberg => by
      exact
        (hlimitLaw direction hnonconstant hactive_pos hmoment hlindeberg).congr
          (Filter.Eventually.of_forall
            (fun sample =>
              finiteScoreCellEuclideanLimitProjection_direction_eq_inner
                cells limitVector direction sample)))
    (fun direction hnonconstant hactive_pos hmoment hlindeberg => by
      let loading := finiteScoreCellEuclideanDirectionLoading cells direction
      let weightedProjection : ℕ -> Sample -> Real := fun n _sample =>
        normalizer n * weightedSampleSum (finiteSample n) (weight n)
          (scoreCellLinearCenteredIndicator cells (score n) referenceShare
            loading)
      let limitInner : LimitSample -> Real := fun sample =>
        ⟪limitVector sample, direction⟫
      let limitProjection : LimitSample -> Real :=
        finiteScoreCellEuclideanLimitProjection cells limitVector loading
      have hweighted :
          TendstoInDistribution weightedProjection atTop limitInner
            sampleLaw limitLaw :=
        hclt direction hnonconstant hactive_pos hmoment hlindeberg
      exact
        MeasureTheory.TendstoInDistribution.congr
          (X := weightedProjection) (Y := weightedProjection)
          (Z := limitInner) (T := limitProjection)
          (μ := sampleLaw) (μ' := limitLaw) (l := atTop)
          (fun _n => Filter.Eventually.of_forall fun _sample => rfl)
          (Filter.Eventually.of_forall
            (fun sample => by
              dsimp [limitInner, limitProjection, loading]
              exact
                (finiteScoreCellEuclideanLimitProjection_direction_eq_inner
                  cells limitVector direction sample).symm))
          hweighted)

/--
Final concrete weighted-sum/inner-limit Euclidean vector CLT route with the
deterministic scalar side conditions removed from the probability-facing
premises.

The theorem still proves and uses the finite weighted second-moment bound and
finite-loading Lindeberg condition internally from the displayed deterministic
inputs.  The remaining probability theorem is only the nondegenerate scalar
Gaussian law and scalar CLT for the actual weighted centered score-cell sum
against the active inner-product Gaussian limit.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_concrete_scalar_clt_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        HasLaw
          (fun sample => ⟪limitVector sample, direction⟫)
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        TendstoInDistribution
          (fun n _sample =>
            normalizer n * weightedSampleSum (finiteSample n) (weight n)
              (scoreCellLinearCenteredIndicator cells (score n) referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction)))
          atTop (fun sample => ⟪limitVector sample, direction⟫)
          sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_nonconstant_active_positive_nnreal_weighted_sum_inner_limit_clt_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hnonconstant hactive_pos _hmoment _hlindeberg =>
      hlimitLaw direction hnonconstant hactive_pos)
    (fun direction hnonconstant hactive_pos _hmoment _hlindeberg =>
      hclt direction hnonconstant hactive_pos)

/--
Concrete vector CLT route whose scalar probability theorem is required only
for reference-mean-zero active directions.

For each Cramer-Wold direction this theorem replaces it by its
reference-centered representative.  The deterministic lemmas above prove that
this preserves nonconstancy and variance and does not change scalar
projections on the tangent finite-sample and limit vectors.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_reference_centered_scalar_clt_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        (hcentered :
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 * direction cellIndex) = 0) ->
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        HasLaw
          (fun sample => ⟪limitVector sample, direction⟫)
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        (hcentered :
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 * direction cellIndex) = 0) ->
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        TendstoInDistribution
          (fun n _sample =>
            normalizer n * weightedSampleSum (finiteSample n) (weight n)
              (scoreCellLinearCenteredIndicator cells (score n) referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction)))
          atTop (fun sample => ⟪limitVector sample, direction⟫)
          sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_concrete_scalar_clt_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hnonconstant hactive_pos => by
      let centeredDirection :=
        finiteScoreCellEuclideanReferenceCenteredDirection
          cells referenceShare direction
      have hcentered_mean :
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 * centeredDirection cellIndex) = 0 := by
        simpa [centeredDirection]
          using
            finiteScoreCellEuclideanReferenceCenteredDirection_referenceMean_eq_zero
              cells referenceShare direction hshare_sum
      have hcentered_nonconstant :
          finiteScoreCellEuclideanDirectionNonconstant
            cells centeredDirection := by
        simpa [centeredDirection] using
          (finiteScoreCellEuclideanReferenceCenteredDirection_nonconstant_iff
            cells referenceShare direction).2 hnonconstant
      have hvariance_eq :
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 *
              (centeredDirection cellIndex -
                ∑ other : {cell // cell ∈ cells},
                  referenceShare other.1 * centeredDirection other) ^ 2) =
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2 := by
        calc
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 *
              (centeredDirection cellIndex -
                ∑ other : {cell // cell ∈ cells},
                  referenceShare other.1 * centeredDirection other) ^ 2) =
              scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells
                  centeredDirection) := by
              rw [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
          _ =
              ∑ cellIndex : {cell // cell ∈ cells},
                referenceShare cellIndex.1 *
                  (direction cellIndex -
                    ∑ other : {cell // cell ∈ cells},
                      referenceShare other.1 * direction other) ^ 2 := by
              simpa [centeredDirection]
                using
                  scoreCellLoadingReferenceCenteredSecondMoment_euclideanReferenceCenteredDirection
                    cells referenceShare direction hshare_sum
      have hcentered_active_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (centeredDirection cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * centeredDirection other) ^ 2 := by
        rw [hvariance_eq]
        exact hactive_pos
      have hcentered_law :
          HasLaw
            (fun sample => ⟪limitVector sample, centeredDirection⟫)
            (gaussianReal 0
              ⟨∑ cellIndex : {cell // cell ∈ cells},
                referenceShare cellIndex.1 *
                  (centeredDirection cellIndex -
                    ∑ other : {cell // cell ∈ cells},
                      referenceShare other.1 * centeredDirection other) ^ 2,
                le_of_lt hcentered_active_pos⟩)
            limitLaw :=
        hlimitLaw centeredDirection hcentered_mean hcentered_nonconstant
          hcentered_active_pos
      have hcentered_law_original_direction :
          HasLaw
            (fun sample => ⟪limitVector sample, direction⟫)
            (gaussianReal 0
              ⟨∑ cellIndex : {cell // cell ∈ cells},
                referenceShare cellIndex.1 *
                  (centeredDirection cellIndex -
                    ∑ other : {cell // cell ∈ cells},
                      referenceShare other.1 * centeredDirection other) ^ 2,
                le_of_lt hcentered_active_pos⟩)
            limitLaw :=
        hcentered_law.congr
          (Filter.Eventually.of_forall
            (fun sample =>
              (inner_finiteScoreCellEuclideanReferenceCenteredDirection_eq_of_tangent
                cells referenceShare direction (limitVector sample)
                (hlimit_tangent sample)).symm))
      have hvariance_nn :
          (⟨∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 *
              (centeredDirection cellIndex -
                ∑ other : {cell // cell ∈ cells},
                  referenceShare other.1 * centeredDirection other) ^ 2,
            le_of_lt hcentered_active_pos⟩ : NNReal) =
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩ :=
        Subtype.ext hvariance_eq
      rw [← hvariance_nn]
      exact hcentered_law_original_direction)
    (fun direction hnonconstant hactive_pos => by
      let centeredDirection :=
        finiteScoreCellEuclideanReferenceCenteredDirection
          cells referenceShare direction
      let originalLoading :=
        finiteScoreCellEuclideanDirectionLoading cells direction
      let centeredLoading :=
        finiteScoreCellEuclideanDirectionLoading cells centeredDirection
      let originalProjection : ℕ -> Sample -> Real := fun n _sample =>
        normalizer n * weightedSampleSum (finiteSample n) (weight n)
          (scoreCellLinearCenteredIndicator cells (score n) referenceShare
            originalLoading)
      let centeredProjection : ℕ -> Sample -> Real := fun n _sample =>
        normalizer n * weightedSampleSum (finiteSample n) (weight n)
          (scoreCellLinearCenteredIndicator cells (score n) referenceShare
            centeredLoading)
      let originalLimit : LimitSample -> Real := fun sample =>
        ⟪limitVector sample, direction⟫
      let centeredLimit : LimitSample -> Real := fun sample =>
        ⟪limitVector sample, centeredDirection⟫
      have hcentered_mean :
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 * centeredDirection cellIndex) = 0 := by
        simpa [centeredDirection]
          using
            finiteScoreCellEuclideanReferenceCenteredDirection_referenceMean_eq_zero
              cells referenceShare direction hshare_sum
      have hcentered_nonconstant :
          finiteScoreCellEuclideanDirectionNonconstant
            cells centeredDirection := by
        simpa [centeredDirection] using
          (finiteScoreCellEuclideanReferenceCenteredDirection_nonconstant_iff
            cells referenceShare direction).2 hnonconstant
      have hvariance_eq :
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 *
              (centeredDirection cellIndex -
                ∑ other : {cell // cell ∈ cells},
                  referenceShare other.1 * centeredDirection other) ^ 2) =
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2 := by
        calc
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 *
              (centeredDirection cellIndex -
                ∑ other : {cell // cell ∈ cells},
                  referenceShare other.1 * centeredDirection other) ^ 2) =
              scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
                centeredLoading := by
              rw [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
          _ =
              ∑ cellIndex : {cell // cell ∈ cells},
                referenceShare cellIndex.1 *
                  (direction cellIndex -
                    ∑ other : {cell // cell ∈ cells},
                      referenceShare other.1 * direction other) ^ 2 := by
              simpa [centeredDirection, centeredLoading]
                using
                  scoreCellLoadingReferenceCenteredSecondMoment_euclideanReferenceCenteredDirection
                    cells referenceShare direction hshare_sum
      have hcentered_active_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (centeredDirection cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * centeredDirection other) ^ 2 := by
        rw [hvariance_eq]
        exact hactive_pos
      have hcentered_clt :
          TendstoInDistribution centeredProjection atTop centeredLimit
            sampleLaw limitLaw :=
        hclt centeredDirection hcentered_mean hcentered_nonconstant
          hcentered_active_pos
      exact
        MeasureTheory.TendstoInDistribution.congr
          (X := centeredProjection) (Y := originalProjection)
          (Z := centeredLimit) (T := originalLimit)
          (μ := sampleLaw) (μ' := limitLaw) (l := atTop)
          (fun n =>
            Filter.Eventually.of_forall
              (fun sample => by
                dsimp [centeredProjection, originalProjection,
                  centeredLoading, originalLoading, centeredDirection]
                calc
                  normalizer n *
                      weightedSampleSum (finiteSample n) (weight n)
                        (scoreCellLinearCenteredIndicator cells (score n)
                          referenceShare
                          (finiteScoreCellEuclideanDirectionLoading cells
                            (finiteScoreCellEuclideanReferenceCenteredDirection
                              cells referenceShare direction))) =
                    finiteScoreCellEuclideanProjection cells
                      (fun n _sample =>
                        finiteScoreCellScaledCenteredMassVector cells
                          (finiteSample n) (weight n) (score n)
                          referenceShare (normalizer n))
                      (finiteScoreCellEuclideanDirectionLoading cells
                        (finiteScoreCellEuclideanReferenceCenteredDirection
                          cells referenceShare direction))
                      n sample := by
                      exact
                        (finiteScoreCellEuclideanProjection_scaledCenteredMassVector_eq_scaled_weightedSampleSum
                          cells finiteSample weight score referenceShare
                          (finiteScoreCellEuclideanDirectionLoading cells
                            (finiteScoreCellEuclideanReferenceCenteredDirection
                              cells referenceShare direction))
                          normalizer n sample).symm
                  _ =
                    finiteScoreCellEuclideanProjection cells
                      (fun n _sample =>
                        finiteScoreCellScaledCenteredMassVector cells
                          (finiteSample n) (weight n) (score n)
                          referenceShare (normalizer n))
                      (finiteScoreCellEuclideanDirectionLoading cells direction)
                      n sample := by
                      exact
                        finiteScoreCellEuclideanProjection_referenceCenteredDirection_eq_of_tangent
                          cells referenceShare
                          (fun n _sample =>
                            finiteScoreCellScaledCenteredMassVector cells
                              (finiteSample n) (weight n) (score n)
                              referenceShare (normalizer n))
                          direction n sample
                          (finiteScoreCellScaledCenteredMassVector_inner_const_one_eq_zero_of_mapsTo
                            cells (finiteSample n) (weight n) (score n)
                            referenceShare (normalizer n) (hcover n)
                            hshare_sum)
                  _ =
                    normalizer n *
                      weightedSampleSum (finiteSample n) (weight n)
                        (scoreCellLinearCenteredIndicator cells (score n)
                          referenceShare
                          (finiteScoreCellEuclideanDirectionLoading cells
                            direction)) := by
                      exact
                        finiteScoreCellEuclideanProjection_scaledCenteredMassVector_eq_scaled_weightedSampleSum
                          cells finiteSample weight score referenceShare
                          (finiteScoreCellEuclideanDirectionLoading cells
                            direction)
                          normalizer n sample))
          (Filter.Eventually.of_forall
            (fun sample => by
              dsimp [centeredLimit, originalLimit, centeredDirection]
              exact
                inner_finiteScoreCellEuclideanReferenceCenteredDirection_eq_of_tangent
                  cells referenceShare direction (limitVector sample)
                  (hlimit_tangent sample)))
          hcentered_clt)

/--
Reference-centered vector CLT route with the scalar Gaussian variance stated
as the plain active second moment.

Since the scalar probability theorem only sees reference-mean-zero directions,
the checked identity
`finiteScoreCellActiveCenteredSecondMoment_eq_secondMoment_of_referenceMean_zero`
removes the repeated centered-mean subtraction from the variance parameter.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_reference_centered_second_moment_scalar_clt_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        (hcentered :
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 * direction cellIndex) = 0) ->
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hsecond_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 * direction cellIndex ^ 2) ->
        HasLaw
          (fun sample => ⟪limitVector sample, direction⟫)
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 * direction cellIndex ^ 2,
              le_of_lt hsecond_pos⟩)
          limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        (hcentered :
          (∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 * direction cellIndex) = 0) ->
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hsecond_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 * direction cellIndex ^ 2) ->
        TendstoInDistribution
          (fun n _sample =>
            normalizer n * weightedSampleSum (finiteSample n) (weight n)
              (scoreCellLinearCenteredIndicator cells (score n) referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction)))
          atTop (fun sample => ⟪limitVector sample, direction⟫)
          sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_reference_centered_scalar_clt_no_design
    cells referenceShare sampleLaw limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent
    (fun direction hcentered hnonconstant hactive_pos => by
      have hvariance_eq :=
        finiteScoreCellActiveCenteredSecondMoment_eq_secondMoment_of_referenceMean_zero
          cells referenceShare direction hcentered
      have hsecond_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 * direction cellIndex ^ 2 := by
        rw [← hvariance_eq]
        exact hactive_pos
      have hsecond_law :
          HasLaw
            (fun sample => ⟪limitVector sample, direction⟫)
            (gaussianReal 0
              ⟨∑ cellIndex : {cell // cell ∈ cells},
                referenceShare cellIndex.1 * direction cellIndex ^ 2,
                le_of_lt hsecond_pos⟩)
            limitLaw :=
        hlimitLaw direction hcentered hnonconstant hsecond_pos
      have hvariance_nn :
          (⟨∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 * direction cellIndex ^ 2,
            le_of_lt hsecond_pos⟩ : NNReal) =
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩ :=
        Subtype.ext hvariance_eq.symm
      rw [← hvariance_nn]
      exact hsecond_law)
    (fun direction hcentered hnonconstant hactive_pos => by
      have hvariance_eq :=
        finiteScoreCellActiveCenteredSecondMoment_eq_secondMoment_of_referenceMean_zero
          cells referenceShare direction hcentered
      have hsecond_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 * direction cellIndex ^ 2 := by
        rw [← hvariance_eq]
        exact hactive_pos
      exact hclt direction hcentered hnonconstant hsecond_pos)

/--
Mathlib iid special case for the concrete weighted-sum scalar CLT boundary.

This theorem does not prove the WDSM survey-design/dependent triangular-array
CLT.  It records the exact smaller case where each concrete weighted centered
score-cell sum is a.e. equal to a normalized iid scalar sum, so Mathlib's
`tendstoInDistribution_inv_sqrt_mul_sum_sub` discharges the scalar CLT
premise of the concrete vector route.
-/
theorem
    finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_iid_weighted_sum_mathlib_no_design
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Ω LimitSample : Type*}
    [MeasurableSpace Ω] [MeasurableSpace LimitSample]
    (P : Measure Ω) (limitLaw : Measure LimitSample)
    [IsProbabilityMeasure P]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (normalizer : ℕ -> Real)
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (weightBound : Real) (weightTotalBound : ℕ -> Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hweightTotal :
      ∀ᶠ n in atTop,
        (∑ unit ∈ finiteSample n, |weight n unit|) ≤
          weightTotalBound n)
    (hcover :
      ∀ n, ∀ unit, unit ∈ finiteSample n -> score n unit ∈ cells)
    (hshare_pos : ∀ cell, cell ∈ cells -> 0 < referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hlimit_tangent :
      ∀ sample,
        ⟪limitVector sample,
          WithLp.toLp 2 (fun _cellIndex : {cell // cell ∈ cells} =>
            (1 : Real))⟫ = 0)
    (X : EuclideanSpace Real {cell // cell ∈ cells} -> ℕ -> Ω -> Real)
    (hindep : ∀ direction, iIndepFun (X direction) P)
    (hident :
      ∀ direction i, IdentDistrib (X direction i) (X direction 0) P P)
    (hmem : ∀ direction, MemLp (X direction 0) 2 P)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        HasLaw
          (fun sample => ⟪limitVector sample, direction⟫)
          (gaussianReal 0
            ⟨∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2,
              le_of_lt hactive_pos⟩)
          limitLaw)
    (hvariance :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        finiteScoreCellEuclideanDirectionNonconstant cells direction ->
        (hactive_pos :
          0 <
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2) ->
        variance (X direction 0) P =
          ∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 *
              (direction cellIndex -
                ∑ other : {cell // cell ∈ cells},
                  referenceShare other.1 * direction other) ^ 2)
    (hweighted_eq_iid :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        ∀ n,
          (fun _ω =>
            normalizer n * weightedSampleSum (finiteSample n) (weight n)
              (scoreCellLinearCenteredIndicator cells (score n) referenceShare
                (finiteScoreCellEuclideanDirectionLoading cells direction))) =ᵐ[P]
          fun ω =>
            (√(n : Real))⁻¹ *
              ((∑ k ∈ Finset.range n, X direction k ω) -
                (n : Real) * ∫ x, X direction 0 x ∂P)) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare (fun _ : ℕ => P) limitLaw
      (fun n _sample =>
        finiteScoreCellScaledCenteredMassVector cells
          (finiteSample n) (weight n) (score n) referenceShare
          (normalizer n))
      limitVector
      (fun n => by fun_prop) hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg_concrete_scalar_clt_no_design
    cells referenceShare (fun _ : ℕ => P) limitLaw finiteSample weight score
    normalizer limitVector hlimitVector scale simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix weightBound
    weightTotalBound hscale hweight hweightTotal hcover hshare_pos
    hshare_sum hlimit_tangent hlimitLaw
    (fun direction hnonconstant hactive_pos => by
      let loading := finiteScoreCellEuclideanDirectionLoading cells direction
      let weightedProjection : ℕ -> Ω -> Real := fun n ω =>
        normalizer n * weightedSampleSum (finiteSample n) (weight n)
          (scoreCellLinearCenteredIndicator cells (score n) referenceShare
            loading)
      let normalized : ℕ -> Ω -> Real := fun n ω =>
        (√(n : Real))⁻¹ *
          ((∑ k ∈ Finset.range n, X direction k ω) -
            (n : Real) * ∫ x, X direction 0 x ∂P)
      let limitInner : LimitSample -> Real := fun sample =>
        ⟪limitVector sample, direction⟫
      have hvariance_pos :
          0 <
            scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
              loading := by
        simpa [loading,
          scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
          using hactive_pos
      have hlimitLaw_toNNReal :
          HasLaw limitInner
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment cells
                referenceShare loading).toNNReal)
            limitLaw := by
        have hactive_toNNReal :
            (∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2).toNNReal =
              ⟨∑ cellIndex : {cell // cell ∈ cells},
                referenceShare cellIndex.1 *
                  (direction cellIndex -
                    ∑ other : {cell // cell ∈ cells},
                      referenceShare other.1 * direction other) ^ 2,
                le_of_lt hactive_pos⟩ :=
          Real.toNNReal_of_nonneg (le_of_lt hactive_pos)
        rw [show
          scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
              loading =
            ∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (direction cellIndex -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * direction other) ^ 2 by
          simpa [loading]
            using
              scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading
                cells referenceShare direction]
        rw [hactive_toNNReal]
        exact hlimitLaw direction hnonconstant hactive_pos
      have hvariance_target :
          variance (X direction 0) P =
            scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
              loading := by
        simpa [loading,
          scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
          using hvariance direction hnonconstant hactive_pos
      have hscalar :
          TendstoInDistribution normalized atTop limitInner
            (fun _ : ℕ => P) limitLaw := by
        exact
          finite_score_cell_linear_projection_clt_of_iid_scalar_mathlib
            cells referenceShare loading P limitLaw (X direction) limitInner
            (hindep direction) (hident direction) (hmem direction)
            hlimitLaw_toNNReal hvariance_target
      exact
        MeasureTheory.TendstoInDistribution.congr
          (X := normalized) (Y := weightedProjection)
          (Z := limitInner) (T := limitInner)
          (μ := fun _ : ℕ => P) (μ' := limitLaw) (l := atTop)
          (fun n => (hweighted_eq_iid direction n).symm)
          (Filter.Eventually.of_forall fun _sample => rfl)
          hscalar)

/--
Euclidean survey-Lindeberg vector CLT route with the scalar Gaussian law stated
using active-coordinate variance.

This is the same vector boundary as
`finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg`,
but its scalar limit-law premise is phrased in the finite Euclidean coordinate
system.  The only stochastic inputs still required are the scalar
survey-design projection CLT and its Gaussian law for each active direction.
-/
theorem finite_score_cell_vector_clt_of_euclidean_active_variance_survey_lindeberg
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Observation Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : ℕ -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ n, IsProbabilityMeasure (sampleLaw n)]
    [IsProbabilityMeasure limitLaw]
    (finiteSample : ℕ -> Finset Observation)
    (weight : ℕ -> Observation -> Real)
    (score : ℕ -> Observation -> Cell)
    (vector : ℕ -> Sample -> EuclideanSpace Real {cell // cell ∈ cells})
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hvector : ∀ n, AEMeasurable (vector n) (sampleLaw n))
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (scale normalizer : ℕ -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity boundedScoreCellIndicators : (Cell -> Real) -> Prop)
    (weightBound : Real)
    (hscale : Tendsto scale atTop atTop)
    (hweight :
      ∀ᶠ n in atTop,
        ∀ unit, unit ∈ finiteSample n -> |weight n unit| ≤ weightBound)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hdesign :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        surveyDesignRegularity
          (finiteScoreCellEuclideanDirectionLoading cells direction))
    (hbounded :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        boundedScoreCellIndicators
          (finiteScoreCellEuclideanDirectionLoading cells direction))
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          HasLaw (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            (gaussianReal 0
              ((∑ cellIndex : {cell // cell ∈ cells},
                referenceShare cellIndex.1 *
                  (direction cellIndex -
                    ∑ other : {cell // cell ∈ cells},
                      referenceShare other.1 * direction other) ^ 2).toNNReal))
            limitLaw)
    (hclt :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        let loading := finiteScoreCellEuclideanDirectionLoading cells direction
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          finiteScoreCellSurveyProjectionLindebergCondition
            atTop finiteSample cells weight score referenceShare loading
            scale normalizer ->
          TendstoInDistribution
            (fun n sample =>
              finiteScoreCellEuclideanProjection cells vector loading n sample)
            atTop (finiteScoreCellEuclideanLimitProjection cells limitVector loading)
            sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare sampleLaw limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_simplex_finite_loading_survey_lindeberg
    cells referenceShare sampleLaw limitLaw finiteSample weight score vector
    limitVector hvector hlimitVector scale normalizer simplexReferenceShares
    covarianceMatrixTangentSpaceVerified hsimplex hmatrix
    surveyDesignRegularity boundedScoreCellIndicators weightBound hscale hweight
    hshare_nonneg hshare_sum hdesign hbounded
    (fun direction hdesign hbounded hlindeberg => by
      simpa [scoreCellLoadingReferenceCenteredSecondMoment_euclideanDirectionLoading]
        using hlimitLaw direction hdesign hbounded hlindeberg)
    hclt

/--
Once the scalar survey projection CLTs and a Cramer-Wold/vector map are
available, the survey-Lindeberg bridge produces the packaged finite-dimensional
score-cell vector CLT.
-/
theorem finite_score_cell_vector_clt_of_survey_lindeberg_projection_bridge
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : (Cell -> Real) -> Prop)
    (hdesign : ∀ loading, surveyDesignRegularity loading)
    (hbounded : ∀ loading, boundedScoreCellIndicators loading)
    (hlindeberg : ∀ loading, surveyLindebergCondition loading)
    (hlimitLaw :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          surveyLindebergCondition loading ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          surveyLindebergCondition loading ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_bridge
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold)
    hsimplex
    (finite_score_cell_all_linear_projection_clts_with_verified_variance_of_survey_lindeberg
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition hdesign hbounded hlindeberg hlimitLaw hclt)
    hmatrix

/--
Vector CLT bridge from survey-design scalar projection CLTs after removing
deterministic zero-variance directions.

This feeds the existing finite score-cell vector bridge with scalar CLT
evidence only for nonzero-variance loadings; zero-variance loadings are
handled by pointwise-zero source and limit projections.
-/
theorem
    finite_score_cell_vector_clt_of_survey_lindeberg_or_pointwise_zero_projection_bridge
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (l : Filter Index)
    (sampleLaw : Index -> Measure Sample) (limitLaw : Measure LimitSample)
    [∀ index, IsProbabilityMeasure (sampleLaw index)]
    [IsProbabilityMeasure limitLaw]
    (centeredProjection : (Cell -> Real) -> Index -> Sample -> Real)
    (limitProjection : (Cell -> Real) -> LimitSample -> Real)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified
      finiteDimensionalScoreCellVectorCLT : Prop)
    (cramerWold :
      simplexReferenceShares ->
        (∀ loading : Cell -> Real,
          centeredScoreCellLinearProjectionCLTWithVerifiedVariance
            cells referenceShare l sampleLaw limitLaw centeredProjection
            limitProjection loading) ->
        covarianceMatrixTangentSpaceVerified ->
        finiteDimensionalScoreCellVectorCLT)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition : (Cell -> Real) -> Prop)
    (hsource_zero :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading = 0 ->
        ∀ index sample, centeredProjection loading index sample = 0)
    (hlimit_zero :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading = 0 ->
        ∀ sample, limitProjection loading sample = 0)
    (hdesign :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        surveyDesignRegularity loading)
    (hbounded :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        boundedScoreCellIndicators loading)
    (hlindeberg :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        surveyLindebergCondition loading)
    (hlimitLaw :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          surveyLindebergCondition loading ->
          HasLaw (limitProjection loading)
            (gaussianReal 0
              (scoreCellLoadingReferenceCenteredSecondMoment
                cells referenceShare loading).toNNReal)
            limitLaw)
    (hclt :
      ∀ loading,
        scoreCellLoadingReferenceCenteredSecondMoment
          cells referenceShare loading ≠ 0 ->
        surveyDesignRegularity loading ->
          boundedScoreCellIndicators loading ->
          surveyLindebergCondition loading ->
          TendstoInDistribution
            (fun index sample => centeredProjection loading index sample)
            l (limitProjection loading) sampleLaw limitLaw) :
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_bridge
    (finiteScoreCellVectorCLTBridgeOfSurveyLindebergProjections
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold)
    hsimplex
    (finite_score_cell_all_linear_projection_clts_with_verified_variance_of_survey_lindeberg_or_pointwise_zero
      cells referenceShare l sampleLaw limitLaw centeredProjection
      limitProjection simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold surveyDesignRegularity boundedScoreCellIndicators
      surveyLindebergCondition hsource_zero hlimit_zero hdesign hbounded
      hlindeberg hlimitLaw hclt)
    hmatrix

/--
Finite score-cell vector-CLT bridge whose linear-projection field is the
concrete family of iid scalar CLTs supplied by mathlib.

This constructor does not prove the Cramer-Wold/vector step.  It isolates that
step in `cramerWold`, while making the all-linear-projection field a concrete
Tendsto-in-distribution statement for every fixed loading.
-/
def finiteScoreCellVectorCLTBridgeOfIidScalarProjections
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
        finiteDimensionalScoreCellVectorCLT) :
    FiniteScoreCellVectorCLTBridge Cell where
  cells := cells
  referenceShare := referenceShare
  simplex_reference_shares := simplexReferenceShares
  all_linear_projection_clts_with_verified_variance :=
    ∀ loading : Cell -> Real,
      TendstoInDistribution
        (fun (n : ℕ) (ω : Ω) =>
          (√(n : Real))⁻¹ *
            ((∑ k ∈ Finset.range n, X loading k ω) -
              (n : Real) * ∫ x, X loading 0 x ∂P))
        atTop (Y loading) (fun _ : ℕ => P) P'
  covariance_matrix_tangent_space_verified :=
    covarianceMatrixTangentSpaceVerified
  finite_dimensional_score_cell_vector_clt :=
    finiteDimensionalScoreCellVectorCLT
  bridge := cramerWold

/--
Mathlib iid scalar CLTs discharge the all-linear-projection field of the iid
scalar-projection vector bridge.
-/
theorem finite_score_cell_all_linear_projection_clts_of_iid_scalar_mathlib
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
            cells referenceShare loading) :
    (finiteScoreCellVectorCLTBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).all_linear_projection_clts_with_verified_variance := by
  intro loading
  exact
    finite_score_cell_linear_projection_clt_of_iid_scalar_mathlib
      cells referenceShare loading P P' (X loading) (Y loading)
      (hindep loading) (hident loading) (hmem loading)
      (hY loading) (hvariance loading)

/--
Mathlib iid scalar CLTs discharge the iid all-linear-projection field when
the Gaussian laws and variance identities are stated using active finite-cell
sums.
-/
theorem finite_score_cell_all_linear_projection_clts_of_iid_scalar_mathlib_active_variance
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
    (hindep : ∀ loading, iIndepFun (X loading) P)
    (hident :
      ∀ loading i, IdentDistrib (X loading i) (X loading 0) P P)
    (hmem : ∀ loading, MemLp (X loading 0) 2 P)
    (hY :
      ∀ loading,
        HasLaw (Y loading)
          (gaussianReal 0
            ((∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (loading cellIndex.1 -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * loading other.1) ^ 2).toNNReal))
          P')
    (hvariance :
      ∀ loading,
        variance (X loading 0) P =
          ∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 *
              (loading cellIndex.1 -
                ∑ other : {cell // cell ∈ cells},
                  referenceShare other.1 * loading other.1) ^ 2) :
    (finiteScoreCellVectorCLTBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).all_linear_projection_clts_with_verified_variance := by
  exact
    finite_score_cell_all_linear_projection_clts_of_iid_scalar_mathlib
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold hindep hident hmem
      (fun loading => by
        simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
          using hY loading)
      (fun loading => by
        simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
          using hvariance loading)

/--
Once a Cramer-Wold/vector map is supplied, the iid scalar-projection bridge
turns mathlib scalar projection CLTs into the packaged vector-CLT field.
-/
theorem finite_score_cell_vector_clt_of_iid_scalar_projection_bridge
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
            cells referenceShare loading) :
    (finiteScoreCellVectorCLTBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_bridge
    (finiteScoreCellVectorCLTBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold)
    hsimplex
    (finite_score_cell_all_linear_projection_clts_of_iid_scalar_mathlib
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold hindep hident hmem hY hvariance)
    hmatrix

/--
Vector CLT from Mathlib iid scalar projections with the scalar Gaussian laws
and variance identities stated as active finite-cell centered second moments.

This is still the iid subroute; the WDSM survey-design/dependent
triangular-array scalar CLT remains a separate probability theorem.
-/
theorem finite_score_cell_vector_clt_of_iid_scalar_projection_bridge_active_variance
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
            ((∑ cellIndex : {cell // cell ∈ cells},
              referenceShare cellIndex.1 *
                (loading cellIndex.1 -
                  ∑ other : {cell // cell ∈ cells},
                    referenceShare other.1 * loading other.1) ^ 2).toNNReal))
          P')
    (hvariance :
      ∀ loading,
        variance (X loading 0) P =
          ∑ cellIndex : {cell // cell ∈ cells},
            referenceShare cellIndex.1 *
              (loading cellIndex.1 -
                ∑ other : {cell // cell ∈ cells},
                  referenceShare other.1 * loading other.1) ^ 2) :
    (finiteScoreCellVectorCLTBridgeOfIidScalarProjections
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold).finite_dimensional_score_cell_vector_clt := by
  exact
    finite_score_cell_vector_clt_of_iid_scalar_projection_bridge
      cells referenceShare P P' X Y simplexReferenceShares
      covarianceMatrixTangentSpaceVerified finiteDimensionalScoreCellVectorCLT
      cramerWold hsimplex hmatrix hindep hident hmem
      (fun loading => by
        simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
          using hY loading)
      (fun loading => by
        simpa [scoreCellLoadingReferenceCenteredSecondMoment_eq_activeCellSum]
          using hvariance loading)

/--
Euclidean active-cell vector CLT from Mathlib scalar iid CLTs in every
Euclidean direction.

This is still an iid scalar-projection route, not the WDSM survey-design CLT.
It uses the checked Euclidean Cramer-Wold representation above, so no abstract
vector map is supplied.  The remaining model-specific inputs are the
directionwise representation of the Euclidean projection as an ordinary
normalized iid scalar sum, the directionwise Gaussian limit law, and the
variance identity with the verified finite-cell centered second moment.
-/
theorem finite_score_cell_vector_clt_of_euclidean_iid_scalar_projection_mathlib
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    {Ω LimitSample : Type*}
    [MeasurableSpace Ω] [MeasurableSpace LimitSample]
    (P : Measure Ω) (limitLaw : Measure LimitSample)
    [IsProbabilityMeasure P] [IsProbabilityMeasure limitLaw]
    (vector : ℕ -> Ω -> EuclideanSpace Real {cell // cell ∈ cells})
    (limitVector : LimitSample -> EuclideanSpace Real {cell // cell ∈ cells})
    (hvector : ∀ n, AEMeasurable (vector n) P)
    (hlimitVector : AEMeasurable limitVector limitLaw)
    (simplexReferenceShares covarianceMatrixTangentSpaceVerified : Prop)
    (hsimplex : simplexReferenceShares)
    (hmatrix : covarianceMatrixTangentSpaceVerified)
    (X : EuclideanSpace Real {cell // cell ∈ cells} -> ℕ -> Ω -> Real)
    (hindep : ∀ direction, iIndepFun (X direction) P)
    (hident : ∀ direction i, IdentDistrib (X direction i) (X direction 0) P P)
    (hmem : ∀ direction, MemLp (X direction 0) 2 P)
    (hlimitLaw :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        HasLaw
          (finiteScoreCellEuclideanLimitProjection cells limitVector
            (finiteScoreCellEuclideanDirectionLoading cells direction))
          (gaussianReal 0
            (scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
              (finiteScoreCellEuclideanDirectionLoading cells direction)).toNNReal)
          limitLaw)
    (hvariance :
      ∀ direction : EuclideanSpace Real {cell // cell ∈ cells},
        variance (X direction 0) P =
          scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
            (finiteScoreCellEuclideanDirectionLoading cells direction))
    (hcentered :
      ∀ direction n,
        (fun ω =>
          finiteScoreCellEuclideanProjection cells vector
            (finiteScoreCellEuclideanDirectionLoading cells direction) n ω) =ᵐ[P]
          fun ω =>
            (√(n : Real))⁻¹ *
              ((∑ k ∈ Finset.range n, X direction k ω) -
                (n : Real) * ∫ x, X direction 0 x ∂P)) :
    (finiteScoreCellVectorCLTBridgeOfCharFunConvergence
      cells referenceShare (fun _ : ℕ => P) limitLaw vector limitVector hvector
      hlimitVector simplexReferenceShares
      covarianceMatrixTangentSpaceVerified).finite_dimensional_score_cell_vector_clt :=
  finite_score_cell_vector_clt_of_euclidean_direction_projection_clts
    cells referenceShare (fun _ : ℕ => P) limitLaw vector limitVector hvector
    hlimitVector simplexReferenceShares covarianceMatrixTangentSpaceVerified
    hsimplex hmatrix
    (fun direction => by
      let loading := finiteScoreCellEuclideanDirectionLoading cells direction
      let normalized : ℕ -> Ω -> Real := fun n ω =>
        (√(n : Real))⁻¹ *
          ((∑ k ∈ Finset.range n, X direction k ω) -
            (n : Real) * ∫ x, X direction 0 x ∂P)
      let projection : ℕ -> Ω -> Real := fun n ω =>
        finiteScoreCellEuclideanProjection cells vector loading n ω
      let limitProjection : LimitSample -> Real :=
        finiteScoreCellEuclideanLimitProjection cells limitVector loading
      have hscalar :
          TendstoInDistribution normalized atTop limitProjection
            (fun _ : ℕ => P) limitLaw := by
        exact
          finite_score_cell_linear_projection_clt_of_iid_scalar_mathlib
            cells referenceShare loading P limitLaw (X direction)
            limitProjection (hindep direction) (hident direction)
            (hmem direction) (hlimitLaw direction) (hvariance direction)
      refine ⟨hlimitLaw direction, ?_⟩
      exact
        MeasureTheory.TendstoInDistribution.congr
          (X := normalized) (Y := projection)
          (Z := limitProjection) (T := limitProjection)
          (μ := fun _ : ℕ => P) (μ' := limitLaw) (l := atTop)
          (fun n => (hcentered direction n).symm)
          (Filter.Eventually.of_forall fun _sample => rfl)
          hscalar)

end WDSM
end Matching
end StatInference
