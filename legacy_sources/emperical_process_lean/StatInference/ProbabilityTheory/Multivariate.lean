import StatInference.ProbabilityTheory.Basic
import StatInference.AsymptoticStatistics.MomentEstimators

/-!
# Durrett 2019 multivariate probability-theory wrappers

This module contains Durrett Section 3.10 source-facing wrappers for limit
theorems in finite-dimensional real vector spaces.  Reusable Cramér-Wold
machinery is shared with the existing asymptotic-statistics lane.
-/

namespace StatInference
namespace ProbabilityTheory

open Filter MeasureTheory ProbabilityTheory

open scoped BigOperators BoundedContinuousFunction ENNReal Topology Function ProbabilityTheory

/-! ## Durrett, Section 3.10 -/

/--
Durrett 2019, Theorem 3.10.7, the finite covariance-table quadratic form
appearing in the multivariate normal characteristic function.
-/
noncomputable def durrett2019_theorem_3_10_7_covarianceTableQuadratic
    {Coordinate : Type*} [Fintype Coordinate]
    (theta : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ) : ℝ :=
  ∑ i, ∑ j, theta i * theta j * Gamma i j

/--
Durrett 2019, Theorem 3.10.7, homogeneity of the finite covariance-table
quadratic form.
-/
theorem durrett2019_theorem_3_10_7_covarianceTableQuadratic_smul
    {Coordinate : Type*} [Fintype Coordinate]
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (t : ℝ) :
    durrett2019_theorem_3_10_7_covarianceTableQuadratic
        (fun i => t * theta i) Gamma =
      t ^ 2 *
        durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma := by
  classical
  simp [durrett2019_theorem_3_10_7_covarianceTableQuadratic, Finset.mul_sum,
    pow_two, mul_left_comm, mul_comm]

/--
Durrett 2019, Theorem 3.10.7, complex-valued homogeneity of the finite
covariance-table quadratic form as it appears in characteristic functions.
-/
theorem durrett2019_theorem_3_10_7_covarianceTableQuadratic_smul_complex
    {Coordinate : Type*} [Fintype Coordinate]
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (t : ℝ) :
    (durrett2019_theorem_3_10_7_covarianceTableQuadratic
        (fun i => t * theta i) Gamma : ℂ) =
      (t : ℂ) ^ 2 *
        (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) := by
  rw [durrett2019_theorem_3_10_7_covarianceTableQuadratic_smul
    (Gamma := Gamma) (theta := theta) (t := t)]
  norm_num

/--
Durrett's projection `x ↦ theta · x` as a continuous linear functional on a
finite real coordinate space.
-/
noncomputable def durrett2019_theorem_3_10_7_thetaProjection
    {Coordinate : Type*} [Fintype Coordinate]
    (theta : Coordinate -> ℝ) :
    StrongDual ℝ (Coordinate -> ℝ) :=
  ∑ i,
    theta i •
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
        (Coordinate := Coordinate) i

@[simp]
theorem durrett2019_theorem_3_10_7_thetaProjection_apply
    {Coordinate : Type*} [Fintype Coordinate]
    (theta : Coordinate -> ℝ) (x : Coordinate -> ℝ) :
    durrett2019_theorem_3_10_7_thetaProjection theta x =
      ∑ i, theta i * x i := by
  classical
  simp [durrett2019_theorem_3_10_7_thetaProjection]

/--
Coordinates of an arbitrary finite-dimensional continuous linear functional in
Durrett's dot-product notation.
-/
noncomputable def durrett2019_theorem_3_10_7_dualCoordinates
    {Coordinate : Type*} [Fintype Coordinate]
    (L : StrongDual ℝ (Coordinate -> ℝ)) : Coordinate -> ℝ := by
  classical
  exact fun i => L (fun j => if i = j then (1 : ℝ) else 0)

/--
Every continuous linear functional on a finite real coordinate space is one of
Durrett's theta projections.
-/
theorem durrett2019_theorem_3_10_7_thetaProjection_dualCoordinates
    {Coordinate : Type*} [Fintype Coordinate]
    (L : StrongDual ℝ (Coordinate -> ℝ)) :
    durrett2019_theorem_3_10_7_thetaProjection
        (durrett2019_theorem_3_10_7_dualCoordinates L) = L := by
  classical
  ext x
  have hL :=
    _root_.LinearMap.pi_apply_eq_sum_univ
      (R := ℝ) (M₂ := ℝ) L.toLinearMap x
  rw [durrett2019_theorem_3_10_7_thetaProjection_apply]
  simpa [durrett2019_theorem_3_10_7_dualCoordinates, smul_eq_mul, mul_comm]
    using hL.symm

/--
Centered theta projections imply centered arbitrary continuous linear
projections in finite coordinates.
-/
theorem durrett2019_theorem_3_10_7_allProjectionMean_zero_of_thetaProjectionMean_zero
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    {Q : Measure Ω'} {Z : Ω' -> Coordinate -> ℝ}
    (hZ_theta_mean : ∀ theta : Coordinate -> ℝ,
      (∫ ω, (∑ i, theta i * Z ω i) ∂Q) = 0) :
    ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0 := by
  intro L
  let theta := durrett2019_theorem_3_10_7_dualCoordinates L
  have hL :
      durrett2019_theorem_3_10_7_thetaProjection theta = L :=
    durrett2019_theorem_3_10_7_thetaProjection_dualCoordinates L
  have hfun :
      (fun ω => L (Z ω)) = (fun ω => ∑ i, theta i * Z ω i) := by
    funext ω
    rw [← hL]
    simp
  simpa [hfun] using hZ_theta_mean theta

/--
Coordinatewise centered Gaussian limits give centered theta projections.

This is the literal finite-dimensional mean assumption in Durrett's
Theorem 3.10.7 proof, packaged into the theta-projection source shape consumed
by the compiled Cramér-Wold wrappers.
-/
theorem durrett2019_theorem_3_10_7_thetaProjectionMean_zero_of_coordinateMean_zero
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    {Q : Measure Ω'} {Z : Ω' -> Coordinate -> ℝ}
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0) :
    ∀ theta : Coordinate -> ℝ,
      (∫ ω, (∑ i, theta i * Z ω i) ∂Q) = 0 := by
  classical
  intro theta
  rw [integral_finsetSum]
  · simp [integral_const_mul, hZ_coordinate_mean]
  · intro i _
    exact (hZ_coordinate_integrable i).const_mul (theta i)

/--
For a finite-coordinate random vector, the `covarianceBilinDual` table of the
push-forward law at coordinate evaluations is the ordinary scalar covariance
table of the original coordinates.
-/
theorem durrett2019_theorem_3_10_7_covarianceBilinDual_eval_eq_coordinateCovariance
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    {μ : Measure Ω} [IsFiniteMeasure μ] {Y : Ω -> Coordinate -> ℝ}
    (hY_memLp : MemLp id 2 (μ.map Y))
    (hY_aemeas : AEMeasurable Y μ)
    (i j : Coordinate) :
    _root_.ProbabilityTheory.covarianceBilinDual (μ.map Y)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
          (Coordinate := Coordinate) i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
          (Coordinate := Coordinate) j) =
      _root_.ProbabilityTheory.covariance
        (fun ω => Y ω i) (fun ω => Y ω j) μ := by
  letI : IsFiniteMeasure (μ.map Y) := Measure.isFiniteMeasure_map μ Y
  rw [_root_.ProbabilityTheory.covarianceBilinDual_eq_covariance hY_memLp]
  rw [_root_.ProbabilityTheory.covariance_map_fun]
  · simp [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM_apply]
  · exact Measurable.aestronglyMeasurable (by fun_prop)
  · exact Measurable.aestronglyMeasurable (by fun_prop)
  · exact hY_aemeas

/--
Coordinate covariance identities give the `covarianceBilinDual` coordinate
table required by the compiled multivariate CLT wrappers.
-/
theorem durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    {μ : Measure Ω} [IsFiniteMeasure μ] {Y : Ω -> Coordinate -> ℝ}
    (hY_memLp : MemLp id 2 (μ.map Y))
    (hY_aemeas : AEMeasurable Y μ)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hcov : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Y ω i) (fun ω => Y ω j) μ =
        Gamma i j) :
    ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (μ.map Y)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j := by
  intro i j
  rw [durrett2019_theorem_3_10_7_covarianceBilinDual_eval_eq_coordinateCovariance
    (μ := μ) (Y := Y) hY_memLp hY_aemeas i j]
  exact hcov i j

/--
Centered product identities imply coordinate covariance identities.
-/
theorem durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ] {Y : Ω -> Coordinate -> ℝ}
    (hY_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Y ω coordinate) 2 μ)
    (hY_coordinate_mean : ∀ coordinate, (∫ ω, Y ω coordinate ∂μ) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hY_centered_product : ∀ i j,
      (∫ ω, Y ω i * Y ω j ∂μ) = Gamma i j) :
    ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Y ω i) (fun ω => Y ω j) μ =
        Gamma i j := by
  intro i j
  rw [_root_.ProbabilityTheory.covariance_eq_sub
    (hY_coordinate_memLp i) (hY_coordinate_memLp j)]
  change
    (∫ ω, Y ω i * Y ω j ∂μ) -
        (∫ ω, Y ω i ∂μ) * (∫ ω, Y ω j ∂μ) =
      Gamma i j
  rw [hY_centered_product i j, hY_coordinate_mean i, hY_coordinate_mean j]
  ring

/--
For coordinatewise centered square-integrable variables, scalar covariance
identities are equivalent to centered product identities in the direction
needed by characteristic-function source wrappers.
-/
theorem durrett2019_theorem_3_10_7_centeredProduct_eq_of_coordinateCovariance
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ] {Y : Ω -> Coordinate -> ℝ}
    (hY_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Y ω coordinate) 2 μ)
    (hY_coordinate_mean : ∀ coordinate, (∫ ω, Y ω coordinate ∂μ) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hY_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Y ω i) (fun ω => Y ω j) μ =
        Gamma i j) :
    ∀ i j, (∫ ω, Y ω i * Y ω j ∂μ) = Gamma i j := by
  intro i j
  have hcov := hY_covariance i j
  rw [_root_.ProbabilityTheory.covariance_eq_sub
    (hY_coordinate_memLp i) (hY_coordinate_memLp j)] at hcov
  change
    (∫ ω, Y ω i * Y ω j ∂μ) -
        (∫ ω, Y ω i ∂μ) * (∫ ω, Y ω j ∂μ) =
      Gamma i j at hcov
  rw [hY_coordinate_mean i, hY_coordinate_mean j] at hcov
  simpa using hcov

/--
Durrett 2019, Theorem 3.10.7, coordinate covariance from the source centered
product around a supplied mean vector.

This is the textbook covariance definition
`Gamma_ij = E[(X_i - mu_i) (X_j - mu_j)]`.
-/
theorem durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    {μ : Measure Ω} {Y : Ω -> Coordinate -> ℝ}
    (mean : Coordinate -> ℝ)
    (hY_coordinate_mean : ∀ coordinate, (∫ ω, Y ω coordinate ∂μ) = mean coordinate)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hY_centered_product : ∀ i j,
      (∫ ω, (Y ω i - mean i) * (Y ω j - mean j) ∂μ) = Gamma i j) :
    ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Y ω i) (fun ω => Y ω j) μ =
        Gamma i j := by
  intro i j
  rw [_root_.ProbabilityTheory.covariance, hY_coordinate_mean i,
    hY_coordinate_mean j]
  exact hY_centered_product i j

/--
The coordinate covariance of the canonical infinite-product sample at any
fixed index is the coordinate covariance of the common vector law.
-/
theorem durrett2019_theorem_3_10_7_canonicalSampleCoordinateCovariance_eq_vectorLaw
    {Coordinate : Type*}
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (sampleIndex : ℕ) (i j : Coordinate) :
    _root_.ProbabilityTheory.covariance
        (fun sample : ℕ -> Coordinate -> ℝ => sample sampleIndex i)
        (fun sample : ℕ -> Coordinate -> ℝ => sample sampleIndex j)
        (Measure.infinitePi (fun _ : ℕ => ν)) =
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j)
        ν := by
  have hlaw :
      _root_.ProbabilityTheory.HasLaw
        (fun sample : ℕ -> Coordinate -> ℝ => sample sampleIndex)
        ν (Measure.infinitePi (fun _ : ℕ => ν)) :=
    (measurePreserving_eval_infinitePi (μ := fun _ : ℕ => ν) sampleIndex).hasLaw
  simpa [Function.comp_def] using
    (hlaw.covariance_fun_comp
      (f := fun sampleVector : Coordinate -> ℝ => sampleVector i)
      (g := fun sampleVector : Coordinate -> ℝ => sampleVector j)
      (hcoordinate_meas i).aemeasurable
      (hcoordinate_meas j).aemeasurable)

/--
Durrett 2019, Section 3.10, Gaussian coordinate independence criterion.

For a finite-coordinate Gaussian vector, zero off-diagonal scalar coordinate
covariances imply independence of the coordinate random variables.
-/
theorem durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_coordinateCovariance_zero
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z P)
    (hcov_zero : ∀ i j : Coordinate, i ≠ j ->
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) P = 0) :
    _root_.ProbabilityTheory.iIndepFun (fun i ω => Z ω i) P := by
  let X : Coordinate -> Ω -> ℝ := fun i ω => Z ω i
  have hgauss :
      _root_.ProbabilityTheory.HasGaussianLaw (fun ω => fun i => X i ω) P := by
    simpa [X] using hZ_gaussian
  simpa [X] using
    hgauss.iIndepFun_of_covariance_eq_zero
      (fun i j hij => by
        simpa [X] using hcov_zero i j hij)

/--
Durrett 2019, Section 3.10, Gaussian coordinate independence criterion in
`iff` form.

For a finite-coordinate Gaussian vector, coordinate independence is equivalent
to zero off-diagonal scalar covariance, once coordinate square-integrability is
available for the easy forward implication.
-/
theorem durrett2019_section_3_10_gaussianCoordinate_iIndepFun_iff_coordinateCovariance_zero
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 P) :
    _root_.ProbabilityTheory.iIndepFun (fun i ω => Z ω i) P ↔
      ∀ i j : Coordinate, i ≠ j ->
        _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) P = 0 := by
  constructor
  · intro hindep i j hij
    exact (hindep.indepFun hij).covariance_eq_zero
      (hZ_coordinate_memLp i) (hZ_coordinate_memLp j)
  · exact
      durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_coordinateCovariance_zero
        (P := P) (Z := Z) hZ_gaussian

/--
Durrett 2019, Section 3.10, covariance-table form of the Gaussian coordinate
independence criterion.

If the coordinate covariance table of a finite-coordinate Gaussian vector is
`Gamma` and all off-diagonal entries of `Gamma` vanish, then the coordinates
are independent.
-/
theorem durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_covarianceBilinDualTable
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z P)
    (hZ_memLp : MemLp id 2 (P.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (P.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hGamma_offDiagonal_zero : ∀ i j : Coordinate, i ≠ j -> Gamma i j = 0) :
    _root_.ProbabilityTheory.iIndepFun (fun i ω => Z ω i) P :=
  durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_coordinateCovariance_zero
    (P := P) (Z := Z) hZ_gaussian
    (fun i j hij => by
      calc
        _root_.ProbabilityTheory.covariance
            (fun ω => Z ω i) (fun ω => Z ω j) P =
          _root_.ProbabilityTheory.covarianceBilinDual (P.map Z)
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
              (Coordinate := Coordinate) i)
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
              (Coordinate := Coordinate) j) := by
            rw [durrett2019_theorem_3_10_7_covarianceBilinDual_eval_eq_coordinateCovariance
              (μ := P) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable i j]
        _ = Gamma i j := hZ_table i j
        _ = 0 := hGamma_offDiagonal_zero i j hij)

/--
Durrett 2019, Section 3.10, covariance-table `iff` form of the Gaussian
coordinate independence criterion.

For a finite-coordinate Gaussian vector with supplied covariance table `Gamma`,
the coordinates are independent if and only if the off-diagonal entries of
`Gamma` are zero.
-/
theorem durrett2019_section_3_10_gaussianCoordinate_iIndepFun_iff_covarianceBilinDualTable
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z P)
    (hZ_memLp : MemLp id 2 (P.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 P)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (P.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j) :
    _root_.ProbabilityTheory.iIndepFun (fun i ω => Z ω i) P ↔
      ∀ i j : Coordinate, i ≠ j -> Gamma i j = 0 := by
  constructor
  · intro hindep i j hij
    have hcov_zero :
        _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) P = 0 :=
      (hindep.indepFun hij).covariance_eq_zero
        (hZ_coordinate_memLp i) (hZ_coordinate_memLp j)
    calc
      Gamma i j =
          _root_.ProbabilityTheory.covarianceBilinDual (P.map Z)
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
              (Coordinate := Coordinate) i)
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
              (Coordinate := Coordinate) j) := (hZ_table i j).symm
      _ = _root_.ProbabilityTheory.covariance
            (fun ω => Z ω i) (fun ω => Z ω j) P := by
          rw [durrett2019_theorem_3_10_7_covarianceBilinDual_eval_eq_coordinateCovariance
            (μ := P) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable i j]
      _ = 0 := hcov_zero
  · exact
      durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_covarianceBilinDualTable
        (P := P) (Z := Z) hZ_gaussian hZ_memLp Gamma hZ_table

/--
Durrett 2019, Section 3.10, scalar covariance-table form of the Gaussian
coordinate independence criterion.

If the scalar coordinate covariance table of a finite-coordinate Gaussian
vector is `Gamma` and all off-diagonal entries of `Gamma` vanish, then the
coordinates are independent.
-/
theorem durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_coordinateCovarianceTable
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z P)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) P =
        Gamma i j)
    (hGamma_offDiagonal_zero : ∀ i j : Coordinate, i ≠ j -> Gamma i j = 0) :
    _root_.ProbabilityTheory.iIndepFun (fun i ω => Z ω i) P :=
  durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_coordinateCovariance_zero
    (P := P) (Z := Z) hZ_gaussian
    (fun i j hij => by
      rw [hZ_covariance i j]
      exact hGamma_offDiagonal_zero i j hij)

/--
Durrett 2019, Section 3.10, scalar covariance-table `iff` form of the Gaussian
coordinate independence criterion.

For a finite-coordinate Gaussian vector with supplied scalar covariance table
`Gamma`, the coordinates are independent if and only if the off-diagonal
entries of `Gamma` vanish.
-/
theorem durrett2019_section_3_10_gaussianCoordinate_iIndepFun_iff_coordinateCovarianceTable
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 P)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) P =
        Gamma i j) :
    _root_.ProbabilityTheory.iIndepFun (fun i ω => Z ω i) P ↔
      ∀ i j : Coordinate, i ≠ j -> Gamma i j = 0 := by
  constructor
  · intro hindep i j hij
    have hcov_zero :
        _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) P = 0 :=
      (hindep.indepFun hij).covariance_eq_zero
        (hZ_coordinate_memLp i) (hZ_coordinate_memLp j)
    rw [← hZ_covariance i j]
    exact hcov_zero
  · exact
      durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_coordinateCovarianceTable
        (P := P) (Z := Z) hZ_gaussian Gamma hZ_covariance

/--
Durrett 2019, Section 3.10, centered-product covariance-table form of the
Gaussian coordinate independence criterion.

This packages the textbook covariance definition
`Gamma_ij = E[(Z_i - mean_i) (Z_j - mean_j)]` before applying the compiled
Gaussian independence criterion.
-/
theorem durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_centeredProductSubMean
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z P)
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂P) = mean coordinate)
    (hZ_centered_product : ∀ i j,
      (∫ ω, (Z ω i - mean i) * (Z ω j - mean j) ∂P) = Gamma i j)
    (hGamma_offDiagonal_zero : ∀ i j : Coordinate, i ≠ j -> Gamma i j = 0) :
    _root_.ProbabilityTheory.iIndepFun (fun i ω => Z ω i) P :=
  durrett2019_section_3_10_gaussianCoordinate_iIndepFun_of_coordinateCovarianceTable
    (P := P) (Z := Z) hZ_gaussian Gamma
    (durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
      (μ := P) (Y := Z) mean hZ_coordinate_mean Gamma hZ_centered_product)
    hGamma_offDiagonal_zero

/--
Durrett 2019, Section 3.10, centered-product covariance-table `iff` form of
the Gaussian coordinate independence criterion.

Under the source covariance identities
`Gamma_ij = E[(Z_i - mean_i) (Z_j - mean_j)]`, coordinate independence is
equivalent to the vanishing of the off-diagonal entries of `Gamma`.
-/
theorem durrett2019_section_3_10_gaussianCoordinate_iIndepFun_iff_centeredProductSubMean
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 P)
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂P) = mean coordinate)
    (hZ_centered_product : ∀ i j,
      (∫ ω, (Z ω i - mean i) * (Z ω j - mean j) ∂P) = Gamma i j) :
    _root_.ProbabilityTheory.iIndepFun (fun i ω => Z ω i) P ↔
      ∀ i j : Coordinate, i ≠ j -> Gamma i j = 0 :=
  durrett2019_section_3_10_gaussianCoordinate_iIndepFun_iff_coordinateCovarianceTable
    (P := P) (Z := Z) hZ_gaussian hZ_coordinate_memLp Gamma
    (durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
      (μ := P) (Y := Z) mean hZ_coordinate_mean Gamma hZ_centered_product)

/--
The covariance bilinear form of Durrett's projection is the double sum of the
coordinate covariance table.
-/
theorem durrett2019_theorem_3_10_7_covarianceBilinDual_thetaProjection
    {Coordinate : Type*} [Fintype Coordinate]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    (μ : Measure (Coordinate -> ℝ)) (theta : Coordinate -> ℝ) :
    _root_.ProbabilityTheory.covarianceBilinDual μ
        (durrett2019_theorem_3_10_7_thetaProjection theta)
        (durrett2019_theorem_3_10_7_thetaProjection theta) =
      ∑ i, ∑ j, theta i * theta j *
        _root_.ProbabilityTheory.covarianceBilinDual μ
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) := by
  classical
  simp [durrett2019_theorem_3_10_7_thetaProjection,
    _root_.ProbabilityTheory.covarianceBilinDual_comm, Finset.mul_sum, mul_assoc]

/--
Durrett's projected variance is the covariance-table quadratic form when the
coordinate covariance table is supplied by `covarianceBilinDual`.
-/
theorem durrett2019_theorem_3_10_7_thetaProjection_variance_eq_covarianceTableQuadratic
    {Coordinate : Type*} [Fintype Coordinate]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {μ : Measure (Coordinate -> ℝ)} [IsFiniteMeasure μ]
    (hμ_memLp : MemLp id 2 μ)
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual μ
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    _root_.ProbabilityTheory.variance
        (durrett2019_theorem_3_10_7_thetaProjection theta) μ =
      durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma := by
  rw [← _root_.ProbabilityTheory.covarianceBilinDual_self_eq_variance
    hμ_memLp (durrett2019_theorem_3_10_7_thetaProjection theta)]
  rw [durrett2019_theorem_3_10_7_covarianceBilinDual_thetaProjection]
  simp [durrett2019_theorem_3_10_7_covarianceTableQuadratic, hGamma]

/--
Durrett 2019, Exercise 3.10.8, mean of a finite-coordinate linear
combination.

This packages the textbook expression `c theta^t` for the mean of
`sum_i c_i X_i`.
-/
theorem durrett2019_exercise_3_10_8_thetaProjectionMean_eq_coordinateMeanLinearCombination
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {Q : Measure Ω} {Z : Ω -> Coordinate -> ℝ}
    (mean : Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate) :
    (∫ ω, (∑ i, theta i * Z ω i) ∂Q) =
      ∑ i, theta i * mean i := by
  classical
  rw [integral_finsetSum]
  · simp [integral_const_mul, hZ_coordinate_mean]
  · intro i _
    exact (hZ_coordinate_integrable i).const_mul (theta i)

/--
Durrett 2019, Exercise 3.10.8, forward direction.

A finite-coordinate multivariate Gaussian vector has Gaussian law under every
Durrett linear combination `sum_i c_i X_i`.
-/
theorem durrett2019_exercise_3_10_8_linearCombination_hasGaussianLaw_of_multivariateGaussian
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (theta : Coordinate -> ℝ) :
    _root_.ProbabilityTheory.HasGaussianLaw
      (fun ω => ∑ i, theta i * Z ω i) Q := by
  classical
  have hprojection :
      _root_.ProbabilityTheory.HasGaussianLaw
        (fun ω => durrett2019_theorem_3_10_7_thetaProjection theta (Z ω)) Q :=
    hZ_gaussian.map_fun (durrett2019_theorem_3_10_7_thetaProjection theta)
  exact hprojection.congr (Filter.Eventually.of_forall fun ω => by
    simp [durrett2019_theorem_3_10_7_thetaProjection_apply])

/--
Durrett 2019, Exercise 3.10.8, reverse direction.

If every Durrett finite linear combination has a one-dimensional Gaussian law,
then the finite-coordinate random vector has a multivariate Gaussian law.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_of_linearCombination_hasGaussianLaw
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} {Z : Ω -> Coordinate -> ℝ}
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hlinear : ∀ theta : Coordinate -> ℝ,
      _root_.ProbabilityTheory.HasGaussianLaw
        (fun ω => ∑ i, theta i * Z ω i) Q) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q := by
  classical
  refine ⟨?_⟩
  refine _root_.ProbabilityTheory.isGaussian_of_isGaussian_map
    (μ := Q.map Z) ?_
  intro L
  let theta := durrett2019_theorem_3_10_7_dualCoordinates L
  have hL :
      durrett2019_theorem_3_10_7_thetaProjection theta = L :=
    durrett2019_theorem_3_10_7_thetaProjection_dualCoordinates L
  have hmap :
      (Q.map Z).map L =
        Q.map (fun ω => ∑ i, theta i * Z ω i) := by
    rw [← hL]
    rw [AEMeasurable.map_map_of_aemeasurable
      (by fun_prop : AEMeasurable
        (durrett2019_theorem_3_10_7_thetaProjection theta) (Q.map Z))
      hZ_aemeasurable]
    congr 1
    ext ω
    simp [durrett2019_theorem_3_10_7_thetaProjection_apply]
  rw [hmap]
  exact (hlinear theta).isGaussian_map

/--
Durrett 2019, Exercise 3.10.8, the finite-coordinate `iff` in Lean's
`HasGaussianLaw` language.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_iff_linearCombination_hasGaussianLaw
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_aemeasurable : AEMeasurable Z Q) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q ↔
      ∀ theta : Coordinate -> ℝ,
        _root_.ProbabilityTheory.HasGaussianLaw
          (fun ω => ∑ i, theta i * Z ω i) Q := by
  constructor
  · intro hZ_gaussian theta
    exact
      durrett2019_exercise_3_10_8_linearCombination_hasGaussianLaw_of_multivariateGaussian
        (Q := Q) (Z := Z) hZ_gaussian theta
  · exact
      durrett2019_exercise_3_10_8_multivariateGaussian_of_linearCombination_hasGaussianLaw
        (Q := Q) (Z := Z) hZ_aemeasurable

/--
Durrett 2019, Exercise 3.10.8, source-facing forward law statement.

If the mean vector and covariance table are supplied in Durrett coordinates,
then every linear combination has the corresponding real Gaussian law with mean
`sum_i c_i theta_i` and variance `c Gamma c^t`.
-/
theorem durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_multivariateGaussian
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    Q.map (fun ω => ∑ i, theta i * Z ω i) =
      _root_.ProbabilityTheory.gaussianReal
        (∑ i, theta i * mean i)
        (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
  classical
  let L := durrett2019_theorem_3_10_7_thetaProjection theta
  have hmean_L :
      (∫ x, L x ∂(Q.map Z)) = ∑ i, theta i * mean i := by
    rw [integral_map hZ_gaussian.aemeasurable
      (by fun_prop : AEStronglyMeasurable L (Q.map Z))]
    simpa [L, durrett2019_theorem_3_10_7_thetaProjection_apply] using
      durrett2019_exercise_3_10_8_thetaProjectionMean_eq_coordinateMeanLinearCombination
        (Q := Q) (Z := Z) mean theta hZ_coordinate_integrable
        hZ_coordinate_mean
  have hvar_L :
      _root_.ProbabilityTheory.variance L (Q.map Z) =
        durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma :=
    durrett2019_theorem_3_10_7_thetaProjection_variance_eq_covarianceTableQuadratic
      (μ := Q.map Z) hZ_memLp Gamma theta hGamma
  calc
    Q.map (fun ω => ∑ i, theta i * Z ω i) =
        (Q.map Z).map L := by
      rw [AEMeasurable.map_map_of_aemeasurable
        (by fun_prop : AEMeasurable L (Q.map Z)) hZ_gaussian.aemeasurable]
      congr 1
      ext ω
      simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply]
    _ = _root_.ProbabilityTheory.gaussianReal
        (∫ x, L x ∂(Q.map Z))
        (_root_.ProbabilityTheory.variance L (Q.map Z)).toNNReal := by
      exact hZ_gaussian.isGaussian_map.map_eq_gaussianReal L
    _ = _root_.ProbabilityTheory.gaussianReal
        (∑ i, theta i * mean i)
        (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
      rw [hmean_L, hvar_L]

/--
Durrett 2019, Exercise 3.10.8, centered source-facing forward law statement
from the covariance table of the Gaussian law.

This is the centered form of the textbook linear-combination display:
`theta · Z` has real Gaussian law with mean zero and variance
`theta Gamma theta^t`.
-/
theorem durrett2019_exercise_3_10_8_centeredLinearCombination_law_eq_gaussianReal_of_covarianceBilinDualTable
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    Q.map (fun ω => ∑ i, theta i * Z ω i) =
      _root_.ProbabilityTheory.gaussianReal 0
        (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
  simpa using
    durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_multivariateGaussian
      (Q := Q) (Z := Z)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (mean := fun _ : Coordinate => 0) (Gamma := Gamma) (theta := theta)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hGamma := hGamma)

/--
Durrett 2019, Exercise 3.10.8, source-facing forward law statement from scalar
coordinate covariances.

This removes the `covarianceBilinDual` table from the user-facing hypotheses.
-/
theorem durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_coordinateCovariance
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    Q.map (fun ω => ∑ i, theta i * Z ω i) =
      _root_.ProbabilityTheory.gaussianReal
        (∑ i, theta i * mean i)
        (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal :=
  durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_multivariateGaussian
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (mean := mean) (Gamma := Gamma) (theta := theta)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hGamma := fun i j =>
      (durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
        (μ := Q) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable Gamma
        hZ_covariance i j).symm)

/--
Durrett 2019, Exercise 3.10.8, source-facing forward law statement from the
textbook centered-product covariance definition.

This packages `Gamma_ij = E[(Z_i - mean_i) (Z_j - mean_j)]` into the real
Gaussian law of every finite linear combination.
-/
theorem durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_centeredProductSubMean
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_centered_product : ∀ i j,
      (∫ ω, (Z ω i - mean i) * (Z ω j - mean j) ∂Q) = Gamma i j) :
    Q.map (fun ω => ∑ i, theta i * Z ω i) =
      _root_.ProbabilityTheory.gaussianReal
        (∑ i, theta i * mean i)
        (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal :=
  durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_coordinateCovariance
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (mean := mean) (Gamma := Gamma) (theta := theta)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := Q) (Y := Z) mean hZ_coordinate_mean Gamma hZ_centered_product)

/--
Durrett 2019, Exercise 3.10.8, centered source-facing forward law statement
from scalar coordinate covariances.

If the finite-coordinate Gaussian vector is coordinatewise centered, then every
linear combination has the centered real Gaussian law with variance
`theta Gamma theta^t`.
-/
theorem durrett2019_exercise_3_10_8_centeredLinearCombination_law_eq_gaussianReal_of_coordinateCovariance
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    Q.map (fun ω => ∑ i, theta i * Z ω i) =
      _root_.ProbabilityTheory.gaussianReal 0
        (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
  simpa using
    durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_coordinateCovariance
      (Q := Q) (Z := Z)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (mean := fun _ : Coordinate => 0)
      (Gamma := Gamma) (theta := theta)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hZ_covariance := hZ_covariance)

/--
Durrett 2019, Exercise 3.10.8, centered source-facing forward law statement
from the textbook centered-product covariance definition.
-/
theorem durrett2019_exercise_3_10_8_centeredLinearCombination_law_eq_gaussianReal_of_centeredProduct
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    Q.map (fun ω => ∑ i, theta i * Z ω i) =
      _root_.ProbabilityTheory.gaussianReal 0
        (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal :=
  durrett2019_exercise_3_10_8_centeredLinearCombination_law_eq_gaussianReal_of_coordinateCovariance
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (Gamma := Gamma) (theta := theta)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)

/--
Durrett 2019, Exercise 3.10.8, reverse direction from the source-facing real
Gaussian laws of all linear combinations.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_of_linearCombination_law_eq_gaussianReal
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} {Z : Ω -> Coordinate -> ℝ}
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hlinear_law : ∀ theta : Coordinate -> ℝ,
      Q.map (fun ω => ∑ i, theta i * Z ω i) =
        _root_.ProbabilityTheory.gaussianReal
          (∑ i, theta i * mean i)
          (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q := by
  classical
  exact
    durrett2019_exercise_3_10_8_multivariateGaussian_of_linearCombination_hasGaussianLaw
      (Q := Q) (Z := Z) hZ_aemeasurable
      (fun theta => by
        refine ⟨?_⟩
        rw [hlinear_law theta]
        infer_instance)

/--
Durrett 2019, Exercise 3.10.8, centered reverse direction from the
source-facing real Gaussian laws of all linear combinations.

This is the centered form: if every finite linear combination has centered real
Gaussian law with variance `theta Gamma theta^t`, then the finite-coordinate
random vector has a multivariate Gaussian law.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_of_centeredLinearCombination_law_eq_gaussianReal
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} {Z : Ω -> Coordinate -> ℝ}
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hlinear_law : ∀ theta : Coordinate -> ℝ,
      Q.map (fun ω => ∑ i, theta i * Z ω i) =
        _root_.ProbabilityTheory.gaussianReal 0
          (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q :=
  durrett2019_exercise_3_10_8_multivariateGaussian_of_linearCombination_law_eq_gaussianReal
    (Q := Q) (Z := Z) (mean := fun _ : Coordinate => 0) Gamma
    hZ_aemeasurable
    (fun theta => by
      simpa using hlinear_law theta)

/--
Durrett 2019, Exercise 3.10.8, source-facing finite-coordinate `iff`.

Under supplied mean and covariance coordinates, multivariate Gaussianity is
equivalent to every Durrett linear combination having the corresponding real
Gaussian law.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_iff_linearCombination_law_eq_gaussianReal
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q ↔
      ∀ theta : Coordinate -> ℝ,
        Q.map (fun ω => ∑ i, theta i * Z ω i) =
          _root_.ProbabilityTheory.gaussianReal
            (∑ i, theta i * mean i)
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
  constructor
  · intro hZ_gaussian theta
    exact
      durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_multivariateGaussian
        (Q := Q) (Z := Z) hZ_gaussian hZ_memLp mean Gamma theta
        hZ_coordinate_integrable hZ_coordinate_mean hGamma
  · exact
      durrett2019_exercise_3_10_8_multivariateGaussian_of_linearCombination_law_eq_gaussianReal
        (Q := Q) (Z := Z) mean Gamma hZ_aemeasurable

/--
Durrett 2019, Exercise 3.10.8, centered source-facing finite-coordinate `iff`
from the covariance table of the Gaussian law.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_iff_centeredLinearCombination_law_eq_gaussianReal_of_covarianceBilinDualTable
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q ↔
      ∀ theta : Coordinate -> ℝ,
        Q.map (fun ω => ∑ i, theta i * Z ω i) =
          _root_.ProbabilityTheory.gaussianReal 0
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
  simpa using
    durrett2019_exercise_3_10_8_multivariateGaussian_iff_linearCombination_law_eq_gaussianReal
      (Q := Q) (Z := Z)
      (hZ_aemeasurable := hZ_aemeasurable)
      (hZ_memLp := hZ_memLp)
      (mean := fun _ : Coordinate => 0) (Gamma := Gamma)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hGamma := hGamma)

/--
Durrett 2019, Exercise 3.10.8, source-facing finite-coordinate `iff` from
scalar coordinate covariances.

This removes the `covarianceBilinDual` table from the statement of the
Gaussian linear-combination characterization.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_iff_linearCombination_law_eq_gaussianReal_of_coordinateCovariance
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q ↔
      ∀ theta : Coordinate -> ℝ,
        Q.map (fun ω => ∑ i, theta i * Z ω i) =
          _root_.ProbabilityTheory.gaussianReal
            (∑ i, theta i * mean i)
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
  constructor
  · intro hZ_gaussian theta
    exact
      durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_coordinateCovariance
        (Q := Q) (Z := Z)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (mean := mean) (Gamma := Gamma) (theta := theta)
        (hZ_coordinate_integrable := hZ_coordinate_integrable)
        (hZ_coordinate_mean := hZ_coordinate_mean)
        (hZ_covariance := hZ_covariance)
  · exact
      durrett2019_exercise_3_10_8_multivariateGaussian_of_linearCombination_law_eq_gaussianReal
        (Q := Q) (Z := Z) mean Gamma hZ_aemeasurable

/--
Durrett 2019, Exercise 3.10.8, source-facing finite-coordinate `iff` from the
textbook centered-product covariance definition.

This packages
`Gamma_ij = E[(Z_i - mean_i) (Z_j - mean_j)]` into the finite-dimensional
Gaussian linear-combination characterization.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_iff_linearCombination_law_eq_gaussianReal_of_centeredProductSubMean
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_centered_product : ∀ i j,
      (∫ ω, (Z ω i - mean i) * (Z ω j - mean j) ∂Q) = Gamma i j) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q ↔
      ∀ theta : Coordinate -> ℝ,
        Q.map (fun ω => ∑ i, theta i * Z ω i) =
          _root_.ProbabilityTheory.gaussianReal
            (∑ i, theta i * mean i)
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
  constructor
  · intro hZ_gaussian theta
    exact
      durrett2019_exercise_3_10_8_linearCombination_law_eq_gaussianReal_of_centeredProductSubMean
        (Q := Q) (Z := Z)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_coordinate_memLp := hZ_coordinate_memLp)
        (mean := mean) (Gamma := Gamma) (theta := theta)
        (hZ_coordinate_mean := hZ_coordinate_mean)
        (hZ_centered_product := hZ_centered_product)
  · exact
      durrett2019_exercise_3_10_8_multivariateGaussian_of_linearCombination_law_eq_gaussianReal
        (Q := Q) (Z := Z) mean Gamma hZ_aemeasurable

/--
Durrett 2019, Exercise 3.10.8, centered source-facing finite-coordinate `iff`
from scalar coordinate covariances.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_iff_centeredLinearCombination_law_eq_gaussianReal_of_coordinateCovariance
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q ↔
      ∀ theta : Coordinate -> ℝ,
        Q.map (fun ω => ∑ i, theta i * Z ω i) =
          _root_.ProbabilityTheory.gaussianReal 0
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal := by
  simpa using
    durrett2019_exercise_3_10_8_multivariateGaussian_iff_linearCombination_law_eq_gaussianReal_of_coordinateCovariance
      (Q := Q) (Z := Z)
      (hZ_aemeasurable := hZ_aemeasurable)
      (hZ_memLp := hZ_memLp)
      (mean := fun _ : Coordinate => 0) (Gamma := Gamma)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hZ_covariance := hZ_covariance)

/--
Durrett 2019, Exercise 3.10.8, centered source-facing finite-coordinate `iff`
from centered product identities.
-/
theorem durrett2019_exercise_3_10_8_multivariateGaussian_iff_centeredLinearCombination_law_eq_gaussianReal_of_centeredProduct
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω} [IsProbabilityMeasure Q] {Z : Ω -> Coordinate -> ℝ}
    (hZ_aemeasurable : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    _root_.ProbabilityTheory.HasGaussianLaw Z Q ↔
      ∀ theta : Coordinate -> ℝ,
        Q.map (fun ω => ∑ i, theta i * Z ω i) =
          _root_.ProbabilityTheory.gaussianReal 0
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma).toNNReal :=
  durrett2019_exercise_3_10_8_multivariateGaussian_iff_centeredLinearCombination_law_eq_gaussianReal_of_coordinateCovariance
    (Q := Q) (Z := Z)
    (hZ_aemeasurable := hZ_aemeasurable)
    (hZ_memLp := hZ_memLp)
    (Gamma := Gamma)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, Gaussian projected characteristic-function
display.

For a Gaussian finite-coordinate vector, every continuous linear projection has
the textbook one-dimensional Gaussian characteristic function with its
projected mean and variance.
-/
theorem durrett2019_theorem_3_10_7_gaussianProjectedCharacteristic_display
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (L : StrongDual ℝ (Coordinate -> ℝ)) :
    MeasureTheory.charFunDual (Q.map Z) L =
      Complex.exp
        (((∫ ω, L (Z ω) ∂Q : ℝ) : ℂ) * Complex.I -
          ((_root_.ProbabilityTheory.variance (fun ω => L (Z ω)) Q : ℝ) : ℂ) / 2) := by
  simpa [_root_.ProbabilityTheory.variance] using
    (_root_.ProbabilityTheory.HasGaussianLaw.charFunDual_map_eq_fun
      (X := Z) (P := Q) L hZ_gaussian)

/--
Durrett 2019, Theorem 3.10.7, Gaussian characteristic-function display for the
textbook projection `theta · chi` with a nonzero mean vector.

This expands the projected mean and projected variance into Durrett's finite
coordinate notation.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_display_of_covarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    MeasureTheory.charFunDual (Q.map Z)
        (durrett2019_theorem_3_10_7_thetaProjection theta) =
      Complex.exp
        ((((∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) := by
  have hmean_projection :
      (∫ ω, durrett2019_theorem_3_10_7_thetaProjection theta (Z ω) ∂Q) =
        ∑ i, theta i * mean i := by
    simpa [durrett2019_theorem_3_10_7_thetaProjection_apply] using
      durrett2019_exercise_3_10_8_thetaProjectionMean_eq_coordinateMeanLinearCombination
        (Q := Q) (Z := Z) mean theta hZ_coordinate_integrable
        hZ_coordinate_mean
  have hvar_projection :
      _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (Q.map Z) =
        durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma :=
    durrett2019_theorem_3_10_7_thetaProjection_variance_eq_covarianceTableQuadratic
      (μ := Q.map Z) hZ_memLp Gamma theta hGamma
  have hvar_map :
      _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (Q.map Z) =
        _root_.ProbabilityTheory.variance
          (fun ω => durrett2019_theorem_3_10_7_thetaProjection theta (Z ω)) Q := by
    simpa [Function.comp_def] using
      (_root_.ProbabilityTheory.variance_map
        (X := durrett2019_theorem_3_10_7_thetaProjection theta)
        (Y := Z) (μ := Q) (by fun_prop) hZ_gaussian.aemeasurable)
  rw [durrett2019_theorem_3_10_7_gaussianProjectedCharacteristic_display
    (Q := Q) (Z := Z) hZ_gaussian
    (durrett2019_theorem_3_10_7_thetaProjection theta)]
  rw [hmean_projection, hvar_map.symm.trans hvar_projection]

/--
Durrett 2019, Theorem 3.10.7, Gaussian characteristic-function display for the
textbook projection `theta · chi` from scalar coordinate covariance identities.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_display_of_coordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    MeasureTheory.charFunDual (Q.map Z)
        (durrett2019_theorem_3_10_7_thetaProjection theta) =
      Complex.exp
        ((((∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_display_of_covarianceBilinDualTable
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (mean := mean) (Gamma := Gamma) (theta := theta)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hGamma := fun i j =>
      (durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
        (μ := Q) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable Gamma
        hZ_covariance i j).symm)

/--
Durrett 2019, Theorem 3.10.7, Gaussian characteristic-function display for the
textbook projection `theta · chi` from the centered-product covariance
definition around a supplied mean vector.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_display_of_centeredProductSubMean
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_centered_product : ∀ i j,
      (∫ ω, (Z ω i - mean i) * (Z ω j - mean j) ∂Q) = Gamma i j) :
    MeasureTheory.charFunDual (Q.map Z)
        (durrett2019_theorem_3_10_7_thetaProjection theta) =
      Complex.exp
        ((((∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_display_of_coordinateCovariance
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (mean := mean) (Gamma := Gamma) (theta := theta)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := Q) (Y := Z) mean hZ_coordinate_mean Gamma hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, literal expectation form of the nonzero-mean
Gaussian characteristic-function display.

This rewrites the `charFunDual` display as the textbook integral
`E exp(i theta · chi)`.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_expectation_display_of_covarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    (∫ ω, Complex.exp (((∑ i, theta i * Z ω i : ℝ) : ℂ) * Complex.I) ∂Q) =
      Complex.exp
        ((((∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) := by
  let L := durrett2019_theorem_3_10_7_thetaProjection theta
  have hmap :
      (∫ ω, Complex.exp (((∑ i, theta i * Z ω i : ℝ) : ℂ) * Complex.I) ∂Q) =
        MeasureTheory.charFunDual (Q.map Z) L := by
    rw [MeasureTheory.charFunDual_apply]
    rw [integral_map hZ_gaussian.aemeasurable
      (by fun_prop : AEStronglyMeasurable
        (fun x : Coordinate -> ℝ => Complex.exp (((L x : ℝ) : ℂ) * Complex.I))
        (Q.map Z))]
    simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply]
  rw [hmap]
  exact
    durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_display_of_covarianceBilinDualTable
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp) (mean := mean) (Gamma := Gamma)
      (theta := theta) (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean) (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, literal expectation-form Gaussian
characteristic-function display from scalar coordinate covariance identities.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_expectation_display_of_coordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    (∫ ω, Complex.exp (((∑ i, theta i * Z ω i : ℝ) : ℂ) * Complex.I) ∂Q) =
      Complex.exp
        ((((∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_expectation_display_of_covarianceBilinDualTable
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (mean := mean) (Gamma := Gamma) (theta := theta)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hGamma := fun i j =>
      (durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
        (μ := Q) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable Gamma
        hZ_covariance i j).symm)

/--
Durrett 2019, Theorem 3.10.7, literal expectation-form Gaussian
characteristic-function display from the centered-product covariance
definition around a supplied mean vector.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_expectation_display_of_centeredProductSubMean
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_centered_product : ∀ i j,
      (∫ ω, (Z ω i - mean i) * (Z ω j - mean j) ∂Q) = Gamma i j) :
    (∫ ω, Complex.exp (((∑ i, theta i * Z ω i : ℝ) : ℂ) * Complex.I) ∂Q) =
      Complex.exp
        ((((∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_expectation_display_of_coordinateCovariance
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (mean := mean) (Gamma := Gamma) (theta := theta)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := Q) (Y := Z) mean hZ_coordinate_mean Gamma hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, literal expectation form of the centered
Gaussian characteristic-function display from the covariance table of the
Gaussian limit law.

This is the textbook integral
`E exp(i theta · chi) = exp(-theta Gamma theta^t / 2)` in finite coordinates.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_expectation_display_of_covarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    (∫ ω, Complex.exp (((∑ i, theta i * Z ω i : ℝ) : ℂ) * Complex.I) ∂Q) =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) := by
  simpa using
    durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_expectation_display_of_covarianceBilinDualTable
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp) (mean := fun _ : Coordinate => 0)
      (Gamma := Gamma) (theta := theta)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, literal expectation form of the centered
Gaussian characteristic-function display from scalar coordinate covariance
identities.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_expectation_display_of_coordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    (∫ ω, Complex.exp (((∑ i, theta i * Z ω i : ℝ) : ℂ) * Complex.I) ∂Q) =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_expectation_display_of_covarianceBilinDualTable
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (Gamma := Gamma) (theta := theta)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hGamma := fun i j =>
      (durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
        (μ := Q) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable Gamma
        hZ_covariance i j).symm)

/--
Durrett 2019, Theorem 3.10.7, literal expectation form of the centered
Gaussian characteristic-function display from centered product identities.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_expectation_display_of_centeredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ) (theta : Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    (∫ ω, Complex.exp (((∑ i, theta i * Z ω i : ℝ) : ℂ) * Complex.I) ∂Q) =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_expectation_display_of_coordinateCovariance
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (theta := theta)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian projected
characteristic-function display from a supplied projected-variance
identification.

This is the exact exponential shape used in the proof before expanding the
projected variance into the coordinate covariance table.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianProjectedCharacteristic_display_of_variance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (projectedVariance : StrongDual ℝ (Coordinate -> ℝ) -> ℝ)
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_variance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.variance (fun ω => L (Z ω)) Q =
        projectedVariance L)
    (L : StrongDual ℝ (Coordinate -> ℝ)) :
    MeasureTheory.charFunDual (Q.map Z) L =
      Complex.exp (-((projectedVariance L : ℂ) / 2)) := by
  rw [durrett2019_theorem_3_10_7_gaussianProjectedCharacteristic_display
    (Q := Q) (Z := Z) hZ_gaussian L]
  rw [hZ_mean L, hZ_variance L]
  congr 1
  simp

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian characteristic-function display
after identifying the projected variance with Durrett's finite covariance-table
quadratic form.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianProjectedCharacteristic_display_of_covarianceTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (L : StrongDual ℝ (Coordinate -> ℝ))
    (hZ_mean : (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_variance :
      _root_.ProbabilityTheory.variance (fun ω => L (Z ω)) Q =
        durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma) :
    MeasureTheory.charFunDual (Q.map Z) L =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) := by
  rw [durrett2019_theorem_3_10_7_gaussianProjectedCharacteristic_display
    (Q := Q) (Z := Z) hZ_gaussian L]
  rw [hZ_mean, hZ_variance]
  congr 1
  simp

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian characteristic-function display
for the textbook projection `theta · chi`.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_display_of_covarianceTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_mean :
      (∫ ω, (∑ i, theta i * Z ω i) ∂Q) = 0)
    (hZ_variance :
      _root_.ProbabilityTheory.variance
          (fun ω => ∑ i, theta i * Z ω i) Q =
        durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma) :
    MeasureTheory.charFunDual (Q.map Z)
        (durrett2019_theorem_3_10_7_thetaProjection theta) =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) := by
  exact
    durrett2019_theorem_3_10_7_centeredGaussianProjectedCharacteristic_display_of_covarianceTable
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (Gamma := Gamma) (theta := theta)
      (L := durrett2019_theorem_3_10_7_thetaProjection theta)
      (hZ_mean := by
        simpa using hZ_mean)
      (hZ_variance := by
        simpa using hZ_variance)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian characteristic-function display
from the covariance table of the Gaussian limit law.

This closes the textbook step
`Var(theta · chi) = sum_i sum_j theta_i theta_j Gamma_ij` when `Gamma` is the
coordinate covariance table of the law of `chi`.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_display_of_covarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_mean :
      (∫ ω, (∑ i, theta i * Z ω i) ∂Q) = 0)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    MeasureTheory.charFunDual (Q.map Z)
        (durrett2019_theorem_3_10_7_thetaProjection theta) =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) := by
  have hvar_projection :
      _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (Q.map Z) =
        durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma :=
    durrett2019_theorem_3_10_7_thetaProjection_variance_eq_covarianceTableQuadratic
      (μ := Q.map Z) hZ_memLp Gamma theta hGamma
  have hvar_map :
      _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (Q.map Z) =
        _root_.ProbabilityTheory.variance
          (fun ω => durrett2019_theorem_3_10_7_thetaProjection theta (Z ω)) Q := by
    simpa [Function.comp_def] using
      (_root_.ProbabilityTheory.variance_map
        (X := durrett2019_theorem_3_10_7_thetaProjection theta)
        (Y := Z) (μ := Q) (by fun_prop) hZ_gaussian.aemeasurable)
  exact
    durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_display_of_covarianceTable
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (Gamma := Gamma) (theta := theta)
      (hZ_mean := hZ_mean)
      (hZ_variance := by
        simpa using hvar_map.symm.trans hvar_projection)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian characteristic-function display
from scalar coordinate covariance identities.

This is the textbook covariance-table source form of
`E exp(i theta · chi) = exp(-sum_i sum_j theta_i theta_j Gamma_ij / 2)`.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_display_of_coordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    MeasureTheory.charFunDual (Q.map Z)
        (durrett2019_theorem_3_10_7_thetaProjection theta) =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) := by
  have htable : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j :=
    durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
      (μ := Q) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable Gamma hZ_covariance
  exact
    durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_display_of_covarianceBilinDualTable
      (Q := Q) (Z := Z)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (Gamma := Gamma) (theta := theta)
      (hZ_mean :=
        durrett2019_theorem_3_10_7_thetaProjectionMean_zero_of_coordinateMean_zero
          (Q := Q) (Z := Z) hZ_coordinate_integrable hZ_coordinate_mean theta)
      (hGamma := fun i j => (htable i j).symm)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian characteristic-function display
from centered product identities.

When `chi` is coordinatewise centered, the source identities
`E[chi_i chi_j] = Gamma_ij` imply Durrett's displayed Gaussian characteristic
function.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_display_of_centeredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    MeasureTheory.charFunDual (Q.map Z)
        (durrett2019_theorem_3_10_7_thetaProjection theta) =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_display_of_coordinateCovariance
    (Q := Q) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (theta := theta)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, nonzero-mean Gaussian projected scalar
characteristic-function display at arbitrary frequency from a covariance table
of the Gaussian law.

This is the ordinary one-dimensional `charFun` version of the
`charFunDual` display, keeping Durrett's source mean vector and
`covarianceBilinDual` coordinate table explicit.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_of_covarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        ((((∑ i, (t * theta i) * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)) := by
  let L := durrett2019_theorem_3_10_7_thetaProjection theta
  have hmap :
      Q.map (fun ω => ∑ i, theta i * Z ω i) =
        (Q.map Z).map L := by
    have hfun :
        (fun ω => ∑ i, theta i * Z ω i) =
          (fun ω => L (Z ω)) := by
      funext ω
      simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply]
    have hcomp :
        (Q.map Z).map L = Q.map (fun ω => L (Z ω)) := by
      rw [AEMeasurable.map_map_of_aemeasurable
        L.continuous.measurable.aemeasurable hZ_gaussian.aemeasurable]
      rfl
    rw [hfun, hcomp]
  have hL :
      t • L =
        durrett2019_theorem_3_10_7_thetaProjection
          (fun i => t * theta i) := by
    ext x
    simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply,
      Finset.mul_sum, mul_assoc]
  calc
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t
        = MeasureTheory.charFun
            ((Q.map Z).map L) t := by
          rw [hmap]
    _ = MeasureTheory.charFunDual (Q.map Z) (t • L) := by
          simpa [L] using
            (MeasureTheory.charFun_map_eq_charFunDual_smul
              (μ := Q.map Z) L t)
    _ = MeasureTheory.charFunDual (Q.map Z)
          (durrett2019_theorem_3_10_7_thetaProjection
            (fun i => t * theta i)) := by
          rw [hL]
    _ = Complex.exp
          ((((∑ i, (t * theta i) * mean i : ℝ) : ℂ) * Complex.I) -
            ((durrett2019_theorem_3_10_7_covarianceTableQuadratic
              (fun i => t * theta i) Gamma : ℂ) / 2)) :=
          durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_display_of_covarianceBilinDualTable
            (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
            (hZ_memLp := hZ_memLp)
            (mean := mean) (Gamma := Gamma)
            (theta := fun i => t * theta i)
            (hZ_coordinate_integrable := hZ_coordinate_integrable)
            (hZ_coordinate_mean := hZ_coordinate_mean)
            (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, nonzero-mean Gaussian projected scalar
characteristic-function display from a covariance table, with the textbook
linear phase and `t^2` covariance exponent.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_tsq_of_covarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        ((((t * ∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          (((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)) := by
  calc
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t
        = Complex.exp
          ((((∑ i, (t * theta i) * mean i : ℝ) : ℂ) * Complex.I) -
            ((durrett2019_theorem_3_10_7_covarianceTableQuadratic
              (fun i => t * theta i) Gamma : ℂ) / 2)) :=
          durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_of_covarianceBilinDualTable
            (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
            (hZ_memLp := hZ_memLp)
            (mean := mean) (Gamma := Gamma) (theta := theta) (t := t)
            (hZ_coordinate_integrable := hZ_coordinate_integrable)
            (hZ_coordinate_mean := hZ_coordinate_mean)
            (hGamma := hGamma)
    _ = Complex.exp
          ((((t * ∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
            (((t : ℂ) ^ 2 *
              (durrett2019_theorem_3_10_7_covarianceTableQuadratic
                theta Gamma : ℂ)) / 2)) := by
          rw [durrett2019_theorem_3_10_7_covarianceTableQuadratic_smul_complex
            (Gamma := Gamma) (theta := theta) (t := t)]
          congr 1
          have hmean :
              (∑ i, (t * theta i) * mean i) =
                t * ∑ i, theta i * mean i := by
            simp [Finset.mul_sum, mul_comm, mul_left_comm]
          rw [hmean]

/--
Durrett 2019, Theorem 3.10.7, nonzero-mean Gaussian projected scalar
characteristic-function display at arbitrary frequency.

This rewrites the `charFunDual` display for `theta · chi` into the ordinary
one-dimensional characteristic function of the projected scalar law at `t`,
keeping the source mean vector and covariance table explicit.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_of_coordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        ((((∑ i, (t * theta i) * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)) := by
  let L := durrett2019_theorem_3_10_7_thetaProjection theta
  have hmap :
      Q.map (fun ω => ∑ i, theta i * Z ω i) =
        (Q.map Z).map L := by
    have hfun :
        (fun ω => ∑ i, theta i * Z ω i) =
          (fun ω => L (Z ω)) := by
      funext ω
      simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply]
    have hcomp :
        (Q.map Z).map L = Q.map (fun ω => L (Z ω)) := by
      rw [AEMeasurable.map_map_of_aemeasurable
        L.continuous.measurable.aemeasurable hZ_gaussian.aemeasurable]
      rfl
    rw [hfun, hcomp]
  have hL :
      t • L =
        durrett2019_theorem_3_10_7_thetaProjection
          (fun i => t * theta i) := by
    ext x
    simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply,
      Finset.mul_sum, mul_assoc]
  calc
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t
        = MeasureTheory.charFun
            ((Q.map Z).map L) t := by
          rw [hmap]
    _ = MeasureTheory.charFunDual (Q.map Z) (t • L) := by
          simpa [L] using
            (MeasureTheory.charFun_map_eq_charFunDual_smul
              (μ := Q.map Z) L t)
    _ = MeasureTheory.charFunDual (Q.map Z)
          (durrett2019_theorem_3_10_7_thetaProjection
            (fun i => t * theta i)) := by
          rw [hL]
    _ = Complex.exp
          ((((∑ i, (t * theta i) * mean i : ℝ) : ℂ) * Complex.I) -
            ((durrett2019_theorem_3_10_7_covarianceTableQuadratic
              (fun i => t * theta i) Gamma : ℂ) / 2)) :=
          durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_display_of_coordinateCovariance
            (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
            (hZ_memLp := hZ_memLp)
            (mean := mean) (Gamma := Gamma)
            (theta := fun i => t * theta i)
            (hZ_coordinate_integrable := hZ_coordinate_integrable)
            (hZ_coordinate_mean := hZ_coordinate_mean)
            (hZ_covariance := hZ_covariance)

/--
Durrett 2019, Theorem 3.10.7, nonzero-mean Gaussian projected scalar
characteristic-function display at arbitrary frequency from the textbook
centered-product covariance definition around a supplied mean vector.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_of_centeredProductSubMean
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_centered_product : ∀ i j,
      (∫ ω, (Z ω i - mean i) * (Z ω j - mean j) ∂Q) = Gamma i j) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        ((((∑ i, (t * theta i) * mean i : ℝ) : ℂ) * Complex.I) -
          ((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_of_coordinateCovariance
    (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
    (hZ_memLp := hZ_memLp)
    (mean := mean) (Gamma := Gamma) (theta := theta) (t := t)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := Q) (Y := Z) mean hZ_coordinate_mean Gamma hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, nonzero-mean Gaussian projected scalar
characteristic-function display with the textbook linear phase and `t^2`
quadratic exponent.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_tsq_of_coordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        ((((t * ∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          (((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)) := by
  calc
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t
        = Complex.exp
          ((((∑ i, (t * theta i) * mean i : ℝ) : ℂ) * Complex.I) -
            ((durrett2019_theorem_3_10_7_covarianceTableQuadratic
              (fun i => t * theta i) Gamma : ℂ) / 2)) :=
          durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_of_coordinateCovariance
            (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
            (hZ_memLp := hZ_memLp)
            (mean := mean) (Gamma := Gamma) (theta := theta) (t := t)
            (hZ_coordinate_integrable := hZ_coordinate_integrable)
            (hZ_coordinate_mean := hZ_coordinate_mean)
            (hZ_covariance := hZ_covariance)
    _ = Complex.exp
          ((((t * ∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
            (((t : ℂ) ^ 2 *
              (durrett2019_theorem_3_10_7_covarianceTableQuadratic
                theta Gamma : ℂ)) / 2)) := by
          rw [durrett2019_theorem_3_10_7_covarianceTableQuadratic_smul_complex
            (Gamma := Gamma) (theta := theta) (t := t)]
          congr 1
          have hmean :
              (∑ i, (t * theta i) * mean i) =
                t * ∑ i, theta i * mean i := by
            simp [Finset.mul_sum, mul_comm, mul_left_comm]
          rw [hmean]

/--
Durrett 2019, Theorem 3.10.7, nonzero-mean Gaussian projected scalar
characteristic-function display from the textbook centered-product covariance
definition.

This packages `Gamma_ij = E[(chi_i - mean_i)(chi_j - mean_j)]` into the
ordinary one-dimensional characteristic-function display with the linear phase
and `t^2` covariance exponent.
-/
theorem durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_tsq_of_centeredProductSubMean
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (mean : Coordinate -> ℝ) (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = mean coordinate)
    (hZ_centered_product : ∀ i j,
      (∫ ω, (Z ω i - mean i) * (Z ω j - mean j) ∂Q) = Gamma i j) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        ((((t * ∑ i, theta i * mean i : ℝ) : ℂ) * Complex.I) -
          (((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)) :=
  durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_tsq_of_coordinateCovariance
    (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
    (hZ_memLp := hZ_memLp)
    (mean := mean) (Gamma := Gamma) (theta := theta) (t := t)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := Q) (Y := Z) mean hZ_coordinate_mean Gamma hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian projected scalar
characteristic-function display at arbitrary frequency from a covariance table
of the Gaussian law.

This is the centered specialization of the nonzero-mean covariance-table
ordinary characteristic-function display.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_covarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
          (fun i => t * theta i) Gamma : ℂ) / 2)) := by
  simpa using
    durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_of_covarianceBilinDualTable
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp)
      (mean := fun _ : Coordinate => 0) (Gamma := Gamma)
      (theta := theta) (t := t)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian projected scalar
characteristic-function display from a covariance table, with the textbook
`t^2` covariance exponent.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_tsq_of_covarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        (-(((t : ℂ) ^ 2 *
          (durrett2019_theorem_3_10_7_covarianceTableQuadratic
            theta Gamma : ℂ)) / 2)) := by
  simpa using
    durrett2019_theorem_3_10_7_gaussianThetaCharacteristic_charFun_tsq_of_covarianceBilinDualTable
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp)
      (mean := fun _ : Coordinate => 0) (Gamma := Gamma)
      (theta := theta) (t := t)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian projected scalar
characteristic-function display at arbitrary frequency.

This rewrites the `charFunDual` display for `theta · chi` into the ordinary
one-dimensional characteristic function of the projected scalar law at `t`.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_coordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
          (fun i => t * theta i) Gamma : ℂ) / 2)) := by
  let L := durrett2019_theorem_3_10_7_thetaProjection theta
  have hmap :
      Q.map (fun ω => ∑ i, theta i * Z ω i) =
        (Q.map Z).map L := by
    have hfun :
        (fun ω => ∑ i, theta i * Z ω i) =
          (fun ω => L (Z ω)) := by
      funext ω
      simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply]
    have hcomp :
        (Q.map Z).map L = Q.map (fun ω => L (Z ω)) := by
      rw [AEMeasurable.map_map_of_aemeasurable
        L.continuous.measurable.aemeasurable hZ_gaussian.aemeasurable]
      rfl
    rw [hfun, hcomp]
  have hL :
      t • L =
        durrett2019_theorem_3_10_7_thetaProjection
          (fun i => t * theta i) := by
    ext x
    simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply,
      Finset.mul_sum, mul_assoc]
  calc
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t
        = MeasureTheory.charFun
            ((Q.map Z).map L) t := by
          rw [hmap]
    _ = MeasureTheory.charFunDual (Q.map Z) (t • L) := by
          simpa [L] using
            (MeasureTheory.charFun_map_eq_charFunDual_smul
              (μ := Q.map Z) L t)
    _ = MeasureTheory.charFunDual (Q.map Z)
          (durrett2019_theorem_3_10_7_thetaProjection
            (fun i => t * theta i)) := by
          rw [hL]
    _ = Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)) :=
          durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_display_of_coordinateCovariance
            (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
            (hZ_memLp := hZ_memLp)
            (hZ_coordinate_integrable := hZ_coordinate_integrable)
            (hZ_coordinate_mean := hZ_coordinate_mean)
            (Gamma := Gamma) (theta := fun i => t * theta i)
            (hZ_covariance := hZ_covariance)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian projected scalar
characteristic-function display from centered product identities at arbitrary
frequency.

This is the arbitrary-frequency companion to the existing textbook `t^2`
centered-product wrapper.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_centeredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
          (fun i => t * theta i) Gamma : ℂ) / 2)) :=
  durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_coordinateCovariance
    (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
    (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (theta := theta) (t := t)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian projected scalar
characteristic-function display with the textbook `t^2` quadratic exponent.

This is the same statement as the arbitrary-frequency display above, rewritten
using homogeneity of the finite covariance-table quadratic form.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_tsq_of_coordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        (-(((t : ℂ) ^ 2 *
          (durrett2019_theorem_3_10_7_covarianceTableQuadratic
            theta Gamma : ℂ)) / 2)) := by
  calc
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t
        = Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)) :=
          durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_coordinateCovariance
            (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
            (hZ_memLp := hZ_memLp)
            (hZ_coordinate_integrable := hZ_coordinate_integrable)
            (hZ_coordinate_mean := hZ_coordinate_mean)
            (Gamma := Gamma) (theta := theta) (t := t)
            (hZ_covariance := hZ_covariance)
    _ = Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)) := by
          rw [durrett2019_theorem_3_10_7_covarianceTableQuadratic_smul_complex
            (Gamma := Gamma) (theta := theta) (t := t)]

/--
Durrett 2019, Theorem 3.10.7, centered Gaussian projected scalar
characteristic-function display from centered product identities, with the
textbook `t^2` quadratic exponent.

When `Z` is coordinatewise centered, the source identities
`E[Z_i Z_j] = Gamma_ij` imply the projected Gaussian characteristic-function
display in Durrett's one-dimensional frequency notation.
-/
theorem durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_tsq_of_centeredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (theta : Coordinate -> ℝ) (t : ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
      Complex.exp
        (-(((t : ℂ) ^ 2 *
          (durrett2019_theorem_3_10_7_covarianceTableQuadratic
            theta Gamma : ℂ)) / 2)) :=
  durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_tsq_of_coordinateCovariance
    (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
    (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (theta := theta) (t := t)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, all-projection covariance source handoff from
coordinate covariance tables.

The compiled multivariate CLT wrappers consume an all-dual covariance
identification.  In finite coordinates this follows from the coordinate
covariance table, because every continuous linear functional is a
`thetaProjection`.
-/
theorem durrett2019_theorem_3_10_7_allProjectionCovariance_of_covarianceBilinDualTables
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hX_sample_aemeas :
      AEMeasurable
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0) P)
    (hX_sample_map_memLp :
      MemLp id 2
        (P.map
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)))
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual
          (P.map
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0))
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j) :
    ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P := by
  classical
  intro L
  let theta := durrett2019_theorem_3_10_7_dualCoordinates L
  let sampleVector :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0
  letI : IsProbabilityMeasure (P.map sampleVector) :=
    P.isProbabilityMeasure_map hX_sample_aemeas
  have hL :
      durrett2019_theorem_3_10_7_thetaProjection theta = L :=
    durrett2019_theorem_3_10_7_thetaProjection_dualCoordinates L
  have hZ_projection :
      _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (Q.map Z) =
        durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma :=
    durrett2019_theorem_3_10_7_thetaProjection_variance_eq_covarianceTableQuadratic
      (μ := Q.map Z) hZ_memLp Gamma theta
      (fun i j => (hZ_table i j).symm)
  have hX_projection :
      _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (P.map sampleVector) =
        durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma :=
    durrett2019_theorem_3_10_7_thetaProjection_variance_eq_covarianceTableQuadratic
      (μ := P.map sampleVector) hX_sample_map_memLp Gamma theta
      (fun i j => (hX_table i j).symm)
  have hX_map :
      _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (P.map sampleVector) =
        _root_.ProbabilityTheory.variance
          (fun ω => durrett2019_theorem_3_10_7_thetaProjection theta (sampleVector ω)) P := by
    simpa [Function.comp_def] using
      (_root_.ProbabilityTheory.variance_map
        (X := durrett2019_theorem_3_10_7_thetaProjection theta)
        (Y := sampleVector) (μ := P) (by fun_prop) hX_sample_aemeas)
  calc
    _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (Q.map Z) := by
          rw [← hL]
          exact _root_.ProbabilityTheory.covarianceBilinDual_self_eq_variance
            hZ_memLp (durrett2019_theorem_3_10_7_thetaProjection theta)
    _ = durrett2019_theorem_3_10_7_covarianceTableQuadratic theta Gamma :=
          hZ_projection
    _ = _root_.ProbabilityTheory.variance
          (durrett2019_theorem_3_10_7_thetaProjection theta) (P.map sampleVector) :=
          hX_projection.symm
    _ = _root_.ProbabilityTheory.variance
          (fun ω => durrett2019_theorem_3_10_7_thetaProjection theta (sampleVector ω)) P :=
          hX_map
    _ = _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P := by
          rw [hL]
          rfl

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device, finite-coordinate law form.

For finite real coordinate spaces, weak convergence of every continuous linear
projection implies weak convergence of the vector laws.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_lawTendsto
    {Coordinate : Type*} [Fintype Coordinate]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ)}
    {μ : ProbabilityMeasure (Coordinate -> ℝ)}
    (hproj :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedLawConvergence
        μs μ) :
    Tendsto μs atTop (𝓝 μ) :=
  StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedLawConvergence_lawTendsto
    hproj

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device from projected
characteristic functions.

For finite real coordinate spaces, pointwise convergence of the characteristic
functions of every one-dimensional continuous linear projection implies weak
convergence of the vector laws.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_lawTendsto_of_projected_charFun
    {Coordinate : Type*} [Fintype Coordinate]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ)}
    {μ : ProbabilityMeasure (Coordinate -> ℝ)}
    (hchar : ∀ L : StrongDual ℝ (Coordinate -> ℝ), ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (((μs n).map L.continuous.measurable.aemeasurable :
              ProbabilityMeasure ℝ) : Measure ℝ) t)
        atTop
        (𝓝 (MeasureTheory.charFun
          ((μ.map L.continuous.measurable.aemeasurable :
            ProbabilityMeasure ℝ) : Measure ℝ) t))) :
    Tendsto μs atTop (𝓝 μ) :=
  durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_lawTendsto
    (μs := μs) (μ := μ)
    (fun L => ProbabilityMeasure.tendsto_iff_tendsto_charFun.mpr (hchar L))

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device, law form in the textbook
`theta · x` notation.

For finite real coordinate spaces, weak convergence of every Durrett coordinate
projection `sum_i theta_i x_i` implies weak convergence of the vector laws.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_lawTendsto
    {Coordinate : Type*} [Fintype Coordinate]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ)}
    {μ : ProbabilityMeasure (Coordinate -> ℝ)}
    (htheta : ∀ theta : Coordinate -> ℝ,
      Tendsto (β := ProbabilityMeasure ℝ)
        (fun n => (μs n).map
          (durrett2019_theorem_3_10_7_thetaProjection
            theta).continuous.measurable.aemeasurable)
        atTop
        (𝓝 (μ.map
          (durrett2019_theorem_3_10_7_thetaProjection
            theta).continuous.measurable.aemeasurable))) :
    Tendsto μs atTop (𝓝 μ) :=
  durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_lawTendsto
    (μs := μs) (μ := μ)
    (fun L => by
      let theta := durrett2019_theorem_3_10_7_dualCoordinates L
      have hL :
          durrett2019_theorem_3_10_7_thetaProjection theta = L :=
        durrett2019_theorem_3_10_7_thetaProjection_dualCoordinates L
      simpa [hL] using htheta theta)

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device from projected
characteristic functions in the textbook `theta · x` notation.

For finite real coordinate spaces, pointwise convergence of the characteristic
functions of every scalar projection `sum_i theta_i x_i` implies weak
convergence of the vector laws.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_lawTendsto_of_charFun
    {Coordinate : Type*} [Fintype Coordinate]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ)}
    {μ : ProbabilityMeasure (Coordinate -> ℝ)}
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (((μs n).map
              (durrett2019_theorem_3_10_7_thetaProjection
                theta).continuous.measurable.aemeasurable :
              ProbabilityMeasure ℝ) : Measure ℝ) t)
        atTop
        (𝓝 (MeasureTheory.charFun
          ((μ.map
            (durrett2019_theorem_3_10_7_thetaProjection
              theta).continuous.measurable.aemeasurable :
            ProbabilityMeasure ℝ) : Measure ℝ) t))) :
    Tendsto μs atTop (𝓝 μ) :=
  durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_lawTendsto
    (μs := μs) (μ := μ)
    (fun theta => ProbabilityMeasure.tendsto_iff_tendsto_charFun.mpr (hchar theta))

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device, random-vector convergence
form.

For finite real coordinate spaces, convergence in distribution of every
continuous linear projection implies convergence in distribution of the vector
itself.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_tendstoInDistribution
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n, IsProbabilityMeasure (P n)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : ℕ -> Ω -> Coordinate -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_aemeas : ∀ n, AEMeasurable (X n) (P n))
    (hZ_aemeas : AEMeasurable Z Q)
    (hproj : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      TendstoInDistribution (fun n ω => L (X n ω)) atTop
        (fun ω => L (Z ω)) P Q) :
    TendstoInDistribution X atTop Z P Q := by
  refine
    ({ forall_aemeasurable := hX_aemeas
       aemeasurable_limit := hZ_aemeas
       tendsto := ?_ } :
      TendstoInDistribution X atTop Z P Q)
  let μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ) :=
    fun n => ⟨(P n).map (X n), Measure.isProbabilityMeasure_map (hX_aemeas n)⟩
  let μ : ProbabilityMeasure (Coordinate -> ℝ) :=
    ⟨Q.map Z, Measure.isProbabilityMeasure_map hZ_aemeas⟩
  have hprojected :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedLawConvergence
        μs μ := by
    intro L
    have hseq_eq :
        (fun n => (μs n).map L.continuous.measurable.aemeasurable) =
          (fun n : ℕ =>
            (⟨(P n).map (fun ω => L (X n ω)),
              Measure.isProbabilityMeasure_map ((hproj L).forall_aemeasurable n)⟩ :
              ProbabilityMeasure ℝ)) := by
      funext n
      ext s
      change ((P n).map (X n)).map L s =
        (P n).map (fun ω => L (X n ω)) s
      rw [AEMeasurable.map_map_of_aemeasurable
        L.continuous.measurable.aemeasurable (hX_aemeas n)]
      rfl
    have hlim_eq :
        μ.map L.continuous.measurable.aemeasurable =
          (⟨Q.map (fun ω => L (Z ω)),
            Measure.isProbabilityMeasure_map ((hproj L).aemeasurable_limit)⟩ :
            ProbabilityMeasure ℝ) := by
      ext s
      change (Q.map Z).map L s = Q.map (fun ω => L (Z ω)) s
      rw [AEMeasurable.map_map_of_aemeasurable
        L.continuous.measurable.aemeasurable hZ_aemeas]
      rfl
    simpa [hseq_eq, hlim_eq] using (hproj L).tendsto
  simpa [μs, μ] using
    durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_lawTendsto
      (μs := μs) (μ := μ) hprojected

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device from projected
characteristic functions, random-vector form.

For finite real coordinate spaces, pointwise convergence of the characteristic
functions of every projected random variable implies convergence in
distribution of the random vectors.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_tendstoInDistribution_of_projected_charFun
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n, IsProbabilityMeasure (P n)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : ℕ -> Ω -> Coordinate -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_aemeas : ∀ n, AEMeasurable (X n) (P n))
    (hZ_aemeas : AEMeasurable Z Q)
    (hchar : ∀ L : StrongDual ℝ (Coordinate -> ℝ), ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun ((P n).map (fun ω => L (X n ω))) t)
        atTop
        (𝓝 (MeasureTheory.charFun (Q.map (fun ω => L (Z ω))) t))) :
    TendstoInDistribution X atTop Z P Q := by
  refine
    ({ forall_aemeasurable := hX_aemeas
       aemeasurable_limit := hZ_aemeas
       tendsto := ?_ } :
      TendstoInDistribution X atTop Z P Q)
  let μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ) :=
    fun n => ⟨(P n).map (X n), Measure.isProbabilityMeasure_map (hX_aemeas n)⟩
  let μ : ProbabilityMeasure (Coordinate -> ℝ) :=
    ⟨Q.map Z, Measure.isProbabilityMeasure_map hZ_aemeas⟩
  have hchar_law : ∀ L : StrongDual ℝ (Coordinate -> ℝ), ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (((μs n).map L.continuous.measurable.aemeasurable :
              ProbabilityMeasure ℝ) : Measure ℝ) t)
        atTop
        (𝓝 (MeasureTheory.charFun
          ((μ.map L.continuous.measurable.aemeasurable :
            ProbabilityMeasure ℝ) : Measure ℝ) t)) := by
    intro L t
    have hseq_eq :
        (fun n : ℕ =>
          Measure.map (fun x : Coordinate -> ℝ => L x)
            ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
              Measure (Coordinate -> ℝ))) =
          (fun n : ℕ => (P n).map (fun ω => L (X n ω))) := by
      funext n
      ext s
      change ((P n).map (X n)).map L s =
        (P n).map (fun ω => L (X n ω)) s
      rw [AEMeasurable.map_map_of_aemeasurable
        L.continuous.measurable.aemeasurable (hX_aemeas n)]
      rfl
    have hlim_eq :
        Measure.map (fun x : Coordinate -> ℝ => L x)
          ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
            Measure (Coordinate -> ℝ)) =
          Q.map (fun ω => L (Z ω)) := by
      ext s
      change (Q.map Z).map L s = Q.map (fun ω => L (Z ω)) s
      rw [AEMeasurable.map_map_of_aemeasurable
        L.continuous.measurable.aemeasurable hZ_aemeas]
      rfl
    change Tendsto
      (fun n : ℕ =>
        MeasureTheory.charFun
          (Measure.map (fun x : Coordinate -> ℝ => L x)
            ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
              Measure (Coordinate -> ℝ))) t)
      atTop
      (𝓝 (MeasureTheory.charFun
        (Measure.map (fun x : Coordinate -> ℝ => L x)
          ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
            Measure (Coordinate -> ℝ))) t))
    have hseq_char_eq :
        (fun n : ℕ =>
          MeasureTheory.charFun
            (Measure.map (fun x : Coordinate -> ℝ => L x)
              ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
                Measure (Coordinate -> ℝ))) t) =
          (fun n : ℕ =>
            MeasureTheory.charFun ((P n).map (fun ω => L (X n ω))) t) := by
      funext n
      rw [congrFun hseq_eq n]
    have hlim_char_eq :
        MeasureTheory.charFun
          (Measure.map (fun x : Coordinate -> ℝ => L x)
            ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
              Measure (Coordinate -> ℝ))) t =
          MeasureTheory.charFun (Q.map (fun ω => L (Z ω))) t := by
      rw [hlim_eq]
    rw [hseq_char_eq, hlim_char_eq]
    exact hchar L t
  simpa [μs, μ] using
    durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_lawTendsto_of_projected_charFun
      (μs := μs) (μ := μ) hchar_law

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device from projected
characteristic functions in textbook `theta · X_n` notation.

For finite real coordinate spaces, pointwise convergence of the characteristic
functions of every scalar projection `sum_i theta_i X_{n,i}` implies
convergence in distribution of the random vectors.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_tendstoInDistribution_of_charFun
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n, IsProbabilityMeasure (P n)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : ℕ -> Ω -> Coordinate -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_aemeas : ∀ n, AEMeasurable (X n) (P n))
    (hZ_aemeas : AEMeasurable Z Q)
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((P n).map (fun ω => ∑ i, theta i * X n ω i)) t)
        atTop
        (𝓝 (MeasureTheory.charFun
          (Q.map (fun ω => ∑ i, theta i * Z ω i)) t))) :
    TendstoInDistribution X atTop Z P Q :=
  durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_tendstoInDistribution_of_projected_charFun
    (P := P) (Q := Q) (X := X) (Z := Z) hX_aemeas hZ_aemeas
    (fun L t => by
      let theta := durrett2019_theorem_3_10_7_dualCoordinates L
      have hL :
          durrett2019_theorem_3_10_7_thetaProjection theta = L :=
        durrett2019_theorem_3_10_7_thetaProjection_dualCoordinates L
      have hseq_eq :
          (fun n : ℕ => (P n).map (fun ω => L (X n ω))) =
            (fun n : ℕ =>
              (P n).map (fun ω => ∑ i, theta i * X n ω i)) := by
        funext n
        have hf :
            (fun ω => L (X n ω)) =
              (fun ω => ∑ i, theta i * X n ω i) := by
          funext ω
          rw [← hL]
          simp [theta, durrett2019_theorem_3_10_7_thetaProjection_apply]
        rw [hf]
      have hlim_eq :
          Q.map (fun ω => L (Z ω)) =
            Q.map (fun ω => ∑ i, theta i * Z ω i) := by
        have hf :
            (fun ω => L (Z ω)) =
              (fun ω => ∑ i, theta i * Z ω i) := by
          funext ω
          rw [← hL]
          simp [theta, durrett2019_theorem_3_10_7_thetaProjection_apply]
        rw [hf]
      change Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun ((P n).map (fun ω => L (X n ω))) t)
        atTop
        (𝓝 (MeasureTheory.charFun (Q.map (fun ω => L (Z ω))) t))
      have hseq_char_eq :
          (fun n : ℕ =>
            MeasureTheory.charFun ((P n).map (fun ω => L (X n ω))) t) =
            (fun n : ℕ =>
              MeasureTheory.charFun
                ((P n).map (fun ω => ∑ i, theta i * X n ω i)) t) := by
        funext n
        rw [congrFun hseq_eq n]
      have hlim_char_eq :
          MeasureTheory.charFun (Q.map (fun ω => L (Z ω))) t =
            MeasureTheory.charFun
              (Q.map (fun ω => ∑ i, theta i * Z ω i)) t := by
        rw [hlim_eq]
      rw [hseq_char_eq, hlim_char_eq]
      exact hchar theta t)

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device in the textbook
`theta · X_n` notation.

For finite real coordinate spaces, convergence in distribution of every
Durrett coordinate projection `sum_i theta_i X_{n,i}` implies convergence in
distribution of the vector itself.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_tendstoInDistribution
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n, IsProbabilityMeasure (P n)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : ℕ -> Ω -> Coordinate -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_aemeas : ∀ n, AEMeasurable (X n) (P n))
    (hZ_aemeas : AEMeasurable Z Q)
    (htheta : ∀ theta : Coordinate -> ℝ,
      TendstoInDistribution (fun n ω => ∑ i, theta i * X n ω i) atTop
        (fun ω => ∑ i, theta i * Z ω i) P Q) :
    TendstoInDistribution X atTop Z P Q :=
  durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_tendstoInDistribution
    (P := P) (Q := Q) (X := X) (Z := Z) hX_aemeas hZ_aemeas
    (fun L => by
      let theta := durrett2019_theorem_3_10_7_dualCoordinates L
      have hL :
          durrett2019_theorem_3_10_7_thetaProjection theta = L :=
        durrett2019_theorem_3_10_7_thetaProjection_dualCoordinates L
      refine TendstoInDistribution.congr ?_ ?_ (htheta theta)
      · intro n
        exact Filter.Eventually.of_forall fun ω => by
          rw [← hL]
          simp [theta, durrett2019_theorem_3_10_7_thetaProjection_apply]
      · exact Filter.Eventually.of_forall fun ω => by
          rw [← hL]
          simp [theta, durrett2019_theorem_3_10_7_thetaProjection_apply])

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device in textbook
`theta · X_n` notation for a fixed source probability space.

This is the usual random-variable form: all `X_n` live on the same probability
space `P`.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_tendstoInDistribution_constMeasure
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : ℕ -> Ω -> Coordinate -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_aemeas : ∀ n, AEMeasurable (X n) P)
    (hZ_aemeas : AEMeasurable Z Q)
    (htheta : ∀ theta : Coordinate -> ℝ,
      TendstoInDistribution (fun n ω => ∑ i, theta i * X n ω i) atTop
        (fun ω => ∑ i, theta i * Z ω i) (fun _ : ℕ => P) Q) :
    TendstoInDistribution X atTop Z (fun _ : ℕ => P) Q :=
  durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_tendstoInDistribution
    (P := fun _ : ℕ => P) (Q := Q) (X := X) (Z := Z)
    hX_aemeas hZ_aemeas htheta

/--
Durrett 2019, Theorem 3.10.6, Cramér-Wold device from projected
characteristic functions in textbook `theta · X_n` notation for a fixed source
probability space.

This is the usual random-variable characteristic-function form: all `X_n` live
on the same probability space `P`.
-/
theorem durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_tendstoInDistribution_constMeasure_of_charFun
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : ℕ -> Ω -> Coordinate -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_aemeas : ∀ n, AEMeasurable (X n) P)
    (hZ_aemeas : AEMeasurable Z Q)
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map (fun ω => ∑ i, theta i * X n ω i)) t)
        atTop
        (𝓝 (MeasureTheory.charFun
          (Q.map (fun ω => ∑ i, theta i * Z ω i)) t))) :
    TendstoInDistribution X atTop Z (fun _ : ℕ => P) Q :=
  durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_tendstoInDistribution_of_charFun
    (P := fun _ : ℕ => P) (Q := Q) (X := X) (Z := Z)
    hX_aemeas hZ_aemeas hchar

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from projected
characteristic functions.

This is the characteristic-function version of the Cramér-Wold assembly step:
once every textbook scalar projection of the scaled centered empirical vector
has pointwise characteristic-function convergence to the corresponding
projection of the limit vector, the empirical vector itself converges in
distribution.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (MeasureTheory.charFun
          (Q.map (fun ω => ∑ i, theta i * Z ω i)) t))) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_6_cramerWold_finiteCoordinate_theta_tendstoInDistribution_constMeasure_of_charFun
    (P := P) (Q := Q)
    (X := fun n ω =>
      √(n : ℝ) •
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
    (Z := Z)
    (fun n => by
      simpa [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment]
        using
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_aemeasurable_real
            (P := P) X hX_meas n)
    hZ_aemeas hchar

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected characteristic functions with a centered Gaussian covariance table.

This is the source-shaped characteristic-function endpoint: the projected
empirical characteristic functions converge to Durrett's displayed Gaussian
quadratic exponential, and the centered Gaussian limit has the matching
coordinate covariance table.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCoordinateCovariance
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2))))) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_aemeas := hZ_gaussian.aemeasurable)
    (fun theta t => by
      have hlimit :=
        durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_coordinateCovariance
          (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
          (hZ_memLp := hZ_memLp)
          (hZ_coordinate_integrable := hZ_coordinate_integrable)
          (hZ_coordinate_mean := hZ_coordinate_mean)
          (Gamma := Gamma) (theta := theta) (t := t)
          (hZ_covariance := hZ_covariance)
      simpa [hlimit] using hchar theta t)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected characteristic functions with the textbook `t^2` Gaussian exponent.

This is a source-shaped variant of the centered Gaussian covariance-table
consumer above, with the limit displayed as
`exp(-(t^2 * theta Gamma theta^T) / 2)`.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCoordinateCovariance_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2))))) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCoordinateCovariance
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_gaussian := hZ_gaussian)
    (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_covariance := hZ_covariance)
    (fun theta t => by
      have hquad :=
        durrett2019_theorem_3_10_7_covarianceTableQuadratic_smul_complex
          (Gamma := Gamma) (theta := theta) (t := t)
      simpa [hquad] using hchar theta t)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected characteristic functions with a centered Gaussian covariance-bilinear
coordinate table.

This is the covariance-table source variant of the projected characteristic
function consumer: the Gaussian limit side is supplied by
`covarianceBilinDual` values on coordinate projections.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2))))) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_aemeas := hZ_gaussian.aemeasurable)
    (fun theta t => by
      have hlimit :=
        durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_covarianceBilinDualTable
          (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
          (hZ_memLp := hZ_memLp)
          (Gamma := Gamma) (theta := theta) (t := t)
          (hZ_coordinate_integrable := hZ_coordinate_integrable)
          (hZ_coordinate_mean := hZ_coordinate_mean)
          (hGamma := hGamma)
      simpa [hlimit] using hchar theta t)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected characteristic functions with a centered Gaussian covariance-bilinear
table and the textbook `t^2` Gaussian exponent.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCovarianceBilinDualTable_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2))))) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_gaussian := hZ_gaussian)
    (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)
    (fun theta t => by
      have hquad :=
        durrett2019_theorem_3_10_7_covarianceTableQuadratic_smul_complex
          (Gamma := Gamma) (theta := theta) (t := t)
      simpa [hquad] using hchar theta t)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected characteristic functions and centered product identities for the
Gaussian limit.

This arbitrary-frequency form feeds the centered-product source identities into
the covariance-table characteristic-function consumer before the `t^2`
normalization step.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCenteredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2))))) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCoordinateCovariance
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_gaussian := hZ_gaussian)
    (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    hchar

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected characteristic functions and centered product identities for the
Gaussian limit.

This is the centered-product source variant of the `t^2` characteristic-function
endpoint: the Gaussian covariance table is supplied as
`E[Z_i Z_j] = Gamma_ij`.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCenteredProduct_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hchar : ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2))))) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCoordinateCovariance_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_gaussian := hZ_gaussian)
    (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    hchar

/--
Durrett 2019, Theorem 3.10.7, projected scalar CLTs imply projected
characteristic-function convergence.

This is the bridge from the scalar Cramér-Wold CLT route to the
characteristic-function route: convergence in distribution of every projected
centered empirical average gives pointwise convergence of the corresponding
characteristic functions.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (MeasureTheory.charFun
          (Q.map (fun ω => ∑ i, theta i * Z ω i)) t)) := by
  intro theta t
  let L := durrett2019_theorem_3_10_7_thetaProjection theta
  have hcf :=
    (MeasureTheory.ProbabilityMeasure.tendsto_iff_tendsto_charFun.mp
      (hscalar L).tendsto) t
  have hseq_eq : (fun n : ℕ =>
        MeasureTheory.charFun
          (P.map
            (fun ω =>
              ∑ i, theta i *
                (√(n : ℝ) •
                  (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                      X n ω -
                    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                      P X)) i)) t) =
      (fun n : ℕ =>
        MeasureTheory.charFun
          (P.map
            (fun ω =>
              √(n : ℝ) *
                (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedEmpiricalAverage
                    L X n ω -
                  StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedPopulationMoment
                    L P X))) t) := by
    funext n
    have hfun :
        (fun ω =>
          ∑ i, theta i *
            (√(n : ℝ) •
              (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                  X n ω -
                StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                  P X)) i) =
          (fun ω =>
            √(n : ℝ) *
              (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedEmpiricalAverage
                  L X n ω -
                  StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedPopulationMoment
                  L P X)) := by
      funext ω
      calc
        ∑ i, theta i *
            (√(n : ℝ) •
              (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                  X n ω -
                StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                  P X)) i
            =
          L (√(n : ℝ) •
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                X n ω -
              StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                P X)) := by
              simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply,
                Finset.mul_sum, mul_left_comm]
        _ =
          √(n : ℝ) *
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedEmpiricalAverage
                L X n ω -
              StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedPopulationMoment
                L P X) :=
              StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjected_scaled_centered_empiricalMoment_eq
                L P X n ω
    rw [hfun]
  have hlim_eq :
      MeasureTheory.charFun (Q.map (fun ω => ∑ i, theta i * Z ω i)) t =
        MeasureTheory.charFun (Q.map (fun ω => L (Z ω))) t := by
    have hfun :
        (fun ω => ∑ i, theta i * Z ω i) =
          (fun ω => L (Z ω)) := by
      funext ω
      simp [L, durrett2019_theorem_3_10_7_thetaProjection_apply]
    rw [hfun]
  rw [hseq_eq, hlim_eq]
  exact hcf

/--
Durrett 2019, Theorem 3.10.7, projected scalar CLTs plus a centered Gaussian
covariance-bilinear table imply projected characteristic-function convergence.

This is the covariance-table source variant before rewriting the Gaussian
exponent into the textbook `t^2` display.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  intro theta t
  have hchar :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT
      (P := P) (Q := Q) (X := X) (Z := Z) hscalar theta t
  have hlimit :=
    durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_covarianceBilinDualTable
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp)
      (Gamma := Gamma) (theta := theta) (t := t)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hGamma := hGamma)
  simpa [hlimit] using hchar

/--
Durrett 2019, Theorem 3.10.7, projected scalar CLTs plus a centered Gaussian
covariance-bilinear table imply the textbook `t^2` projected
characteristic-function hypothesis.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  intro theta t
  have hchar :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT
      (P := P) (Q := Q) (X := X) (Z := Z) hscalar theta t
  have hlimit :=
    durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_tsq_of_covarianceBilinDualTable
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp)
      (Gamma := Gamma) (theta := theta) (t := t)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hGamma := hGamma)
  simpa [hlimit] using hchar

/--
Durrett 2019, Theorem 3.10.7, projected scalar CLTs plus centered Gaussian
product identities give the arbitrary-frequency projected
characteristic-function hypothesis.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  intro theta t
  have hchar :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT
      (P := P) (Q := Q) (X := X) (Z := Z) hscalar theta t
  have hlimit :=
    durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_of_centeredProduct
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (theta := theta) (t := t)
      (hZ_centered_product := hZ_centered_product)
  simpa [hlimit] using hchar

/--
Durrett 2019, Theorem 3.10.7, projected scalar CLTs plus centered Gaussian
product identities give the textbook `t^2` projected characteristic-function
hypothesis.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedScalarCLT_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  intro theta t
  have hchar :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT
      (P := P) (Q := Q) (X := X) (Z := Z) hscalar theta t
  have hlimit :=
    durrett2019_theorem_3_10_7_centeredGaussianThetaCharacteristic_charFun_tsq_of_centeredProduct
      (Q := Q) (Z := Z) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (theta := theta) (t := t)
      (hZ_centered_product := hZ_centered_product)
  simpa [hlimit] using hchar

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected scalar CLTs and centered product identities for the Gaussian limit,
via the textbook `t^2` characteristic-function endpoint.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT_centeredGaussianCenteredProduct_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCenteredProduct_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_centered_product := hZ_centered_product)
    (durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedScalarCLT_centeredProduct
      (P := P) (Q := Q) (X := X) (Z := Z)
      hscalar hZ_gaussian hZ_memLp hZ_coordinate_memLp hZ_coordinate_mean
      Gamma hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected scalar CLTs and a centered Gaussian covariance-bilinear coordinate
table, before rewriting the projected characteristic functions into the
textbook `t^2` display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)
    (durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable
      (P := P) (Q := Q) (X := X) (Z := Z)
      hscalar hZ_gaussian hZ_memLp hZ_coordinate_integrable hZ_coordinate_mean
      Gamma hGamma)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected scalar CLTs and a centered Gaussian covariance-bilinear coordinate
table, via the textbook `t^2` characteristic-function endpoint.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCovarianceBilinDualTable_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)
    (durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable
      (P := P) (Q := Q) (X := X) (Z := Z)
      hscalar hZ_gaussian hZ_memLp hZ_coordinate_integrable hZ_coordinate_mean
      Gamma hGamma)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected scalar CLTs and centered product identities for the Gaussian limit,
before rewriting the projected characteristic functions into the textbook
`t^2` display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT_centeredGaussianCenteredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedCharacteristicFunctions_centeredGaussianCenteredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_centered_product := hZ_centered_product)
    (durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT_centeredProduct
      (P := P) (Q := Q) (X := X) (Z := Z)
      hscalar hZ_gaussian hZ_memLp hZ_coordinate_memLp hZ_coordinate_mean
      Gamma hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, projected summand CLTs plus a centered Gaussian
covariance-bilinear table imply projected characteristic-function convergence.

This is the summand-level covariance-table source variant before rewriting the
Gaussian exponent into the textbook `t^2` display.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
      (P := P) (Q := Q) hsummand)
    hZ_gaussian hZ_memLp hZ_coordinate_integrable hZ_coordinate_mean
    Gamma hGamma

/--
Durrett 2019, Theorem 3.10.7, projected summand CLTs plus a centered Gaussian
covariance-bilinear table imply the textbook `t^2` projected
characteristic-function hypothesis.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
      (P := P) (Q := Q) hsummand)
    hZ_gaussian hZ_memLp hZ_coordinate_integrable hZ_coordinate_mean
    Gamma hGamma

/--
Durrett 2019, Theorem 3.10.7, projected summand CLTs plus centered Gaussian
product identities imply projected characteristic-function convergence before
the textbook `t^2` rewrite.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedSummandCLT_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedScalarCLT_centeredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
      (P := P) (Q := Q) hsummand)
    hZ_gaussian hZ_memLp hZ_coordinate_memLp hZ_coordinate_mean Gamma
    hZ_centered_product

/--
Durrett 2019, Theorem 3.10.7, projected summand CLTs imply the textbook `t^2`
projected characteristic-function convergence, with centered product identities
for the Gaussian limit.

This is the summand-level source variant of the V345 bridge.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedSummandCLT_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedScalarCLT_centeredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
      (P := P) (Q := Q) hsummand)
    hZ_gaussian hZ_memLp hZ_coordinate_memLp hZ_coordinate_mean Gamma
    hZ_centered_product

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from projected
summand CLTs and centered product identities for the Gaussian limit, via the
textbook `t^2` characteristic-function endpoint.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCenteredProduct_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT_centeredGaussianCenteredProduct_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hscalar :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
        (P := P) (Q := Q) hsummand)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected summand CLTs and a centered Gaussian covariance-bilinear coordinate
table, before rewriting the projected characteristic functions into the
textbook `t^2` display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hscalar :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
        (P := P) (Q := Q) hsummand)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected summand CLTs and a centered Gaussian covariance-bilinear coordinate
table, via the textbook `t^2` characteristic-function endpoint.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT_centeredGaussianCovarianceBilinDualTable_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hscalar :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
        (P := P) (Q := Q) hsummand)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
projected summand CLTs and centered product identities for the Gaussian limit,
before rewriting the projected characteristic functions into the textbook
`t^2` display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCenteredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT_centeredGaussianCenteredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hscalar :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
        (P := P) (Q := Q) hsummand)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, vector Gaussian source assumptions imply the
projected characteristic-function convergence with a centered Gaussian
covariance-bilinear coordinate table.

This packages the mathlib one-dimensional CLT source hypotheses through the
projected summand CLT and the summand-level covariance-table bridge.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_vectorGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_indep := hX_indep) (hX_ident := hX_ident))
    hZ_gaussian hZ_memLp hZ_coordinate_integrable hZ_coordinate_mean
    Gamma hGamma

/--
Durrett 2019, Theorem 3.10.7, vector Gaussian source assumptions imply the
textbook `t^2` projected characteristic-function convergence with a centered
Gaussian covariance-bilinear coordinate table.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_vectorGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_indep := hX_indep) (hX_ident := hX_ident))
    hZ_gaussian hZ_memLp hZ_coordinate_integrable hZ_coordinate_mean
    Gamma hGamma

/--
Durrett 2019, Theorem 3.10.7, vector Gaussian source assumptions imply
projected characteristic-function convergence with centered product identities
for the Gaussian limit, before the textbook `t^2` rewrite.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_vectorGaussianSource_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedSummandCLT_centeredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_indep := hX_indep) (hX_ident := hX_ident))
    hZ_gaussian hZ_memLp hZ_coordinate_memLp hZ_coordinate_mean Gamma
    hZ_centered_product

/--
Durrett 2019, Theorem 3.10.7, vector Gaussian source assumptions imply the
textbook `t^2` projected characteristic-function convergence.

This packages the mathlib one-dimensional CLT source hypotheses through the
projected summand CLT and then through the V346 characteristic-function bridge.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_vectorGaussianSource_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedSummandCLT_centeredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_indep := hX_indep) (hX_ident := hX_ident))
    hZ_gaussian hZ_memLp hZ_coordinate_memLp hZ_coordinate_mean Gamma
    hZ_centered_product

/--
Durrett 2019, Theorem 3.10.7 normalization algebra for a finite-coordinate
sample on an arbitrary source probability space.

The reusable empirical-moment normalization is exactly the textbook
`(S_n - n * mu) / sqrt n` coordinate display whenever the first summand has
mean vector `mu`.
-/
theorem durrett2019_theorem_3_10_7_finiteCoordinate_explicitMean_normalization_eq_sum
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} (X : Coordinate -> ℕ -> Ω -> ℝ) (mu : Coordinate -> ℝ)
    (hX_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (n : ℕ) (ω : Ω) :
    √(n : ℝ) •
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
            X n ω -
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X) =
      fun coordinate : Coordinate =>
        (√(n : ℝ))⁻¹ *
          ((∑ i ∈ Finset.range n, X coordinate i ω) -
            (n : ℝ) * mu coordinate) := by
  ext coordinate
  by_cases hn : n = 0
  · subst n
    simp [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment,
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment,
      hX_mean]
  · have hnpos_nat : 0 < n := Nat.pos_of_ne_zero hn
    have hnpos : 0 < (n : ℝ) := Nat.cast_pos.mpr hnpos_nat
    have hsqrt_pos : 0 < √(n : ℝ) := Real.sqrt_pos_of_pos hnpos
    have hsqrt_ne : √(n : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
    have hn_ne : (n : ℝ) ≠ 0 := ne_of_gt hnpos
    have hsqrt_sq : (√(n : ℝ)) ^ 2 = (n : ℝ) :=
      Real.sq_sqrt hnpos.le
    simp [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment,
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment,
      Pi.sub_apply, smul_eq_mul, div_eq_inv_mul, hX_mean]
    field_simp [hsqrt_ne, hn_ne]
    rw [hsqrt_sq]

/--
Durrett 2019, Theorem 3.10.7, vector Gaussian source assumptions imply the
literal normalized-sum projected characteristic-function display before the
textbook `t^2` rewrite.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_vectorGaussianSource_centeredProduct_explicitMean_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {mu : Coordinate -> ℝ}
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    ((∑ i ∈ Finset.range n, X coordinate i ω) -
                      (n : ℝ) * mu coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  intro theta t
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_vectorGaussianSource_centeredProduct
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)
      (hX_indep := hX_indep) (hX_ident := hX_ident)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  have hfun :
      (fun ω : Ω =>
        ∑ i, theta i *
          (√(n : ℝ) •
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                X n ω -
              StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                P X)) i) =
      (fun ω : Ω =>
        ∑ coordinate, theta coordinate *
          ((√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, X coordinate i ω) -
              (n : ℝ) * mu coordinate))) := by
    funext ω
    have hnorm :=
      durrett2019_theorem_3_10_7_finiteCoordinate_explicitMean_normalization_eq_sum
        (P := P) X mu hX_coordinate_mean n ω
    have hsum :=
      congrArg (fun v : Coordinate -> ℝ => ∑ coordinate, theta coordinate * v coordinate)
        hnorm
    simpa [Pi.smul_apply, Pi.sub_apply, smul_eq_mul] using hsum
  rw [hfun]

/--
Durrett 2019, Theorem 3.10.7, vector Gaussian source assumptions imply the
literal normalized-sum projected characteristic-function display in the
textbook `t^2` exponent form.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_vectorGaussianSource_centeredProduct_explicitMean_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {mu : Coordinate -> ℝ}
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    ((∑ i ∈ Finset.range n, X coordinate i ω) -
                      (n : ℝ) * mu coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  intro theta t
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_vectorGaussianSource_centeredProduct
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)
      (hX_indep := hX_indep) (hX_ident := hX_ident)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  have hfun :
      (fun ω : Ω =>
        ∑ i, theta i *
          (√(n : ℝ) •
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                X n ω -
              StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                P X)) i) =
      (fun ω : Ω =>
        ∑ coordinate, theta coordinate *
          ((√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, X coordinate i ω) -
              (n : ℝ) * mu coordinate))) := by
    funext ω
    have hnorm :=
      durrett2019_theorem_3_10_7_finiteCoordinate_explicitMean_normalization_eq_sum
        (P := P) X mu hX_coordinate_mean n ω
    have hsum :=
      congrArg (fun v : Coordinate -> ℝ => ∑ coordinate, theta coordinate * v coordinate)
        hnorm
    simpa [Pi.smul_apply, Pi.sub_apply, smul_eq_mul] using hsum
  rw [hfun]

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from vector
Gaussian source assumptions and a centered Gaussian covariance-bilinear
coordinate table, before rewriting the projected characteristic functions into
the textbook `t^2` display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hsummand :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_indep := hX_indep) (hX_ident := hX_ident))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from vector
Gaussian source assumptions and a centered Gaussian covariance-bilinear
coordinate table, via the textbook `t^2` characteristic-function endpoint.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianSource_centeredGaussianCovarianceBilinDualTable_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hsummand :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_indep := hX_indep) (hX_ident := hX_ident))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from vector
Gaussian source assumptions and centered product identities for the Gaussian
limit, before rewriting the projected characteristic functions into the
textbook `t^2` display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianSource_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCenteredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hsummand :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_indep := hX_indep) (hX_ident := hX_ident))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from vector
Gaussian source assumptions, via the textbook `t^2` characteristic-function
endpoint and centered product identities for the Gaussian limit.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianSource_centeredProduct_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCenteredProduct_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hsummand :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_indep := hX_indep) (hX_ident := hX_ident))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, common-vector-law source assumptions imply the
projected characteristic-function convergence with a centered Gaussian
covariance-bilinear coordinate table.

The common finite-coordinate vector law and the infinite product law discharge
the i.i.d. sample-vector hypotheses used by the projected summand CLT, then
the summand-level covariance-table bridge supplies the Gaussian exponent.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_commonVectorLawGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_vector_law := hX_vector_law)
      (hX_sequence_law := hX_sequence_law))
    hZ_gaussian hZ_memLp hZ_coordinate_integrable hZ_coordinate_mean
    Gamma hGamma

/--
Durrett 2019, Theorem 3.10.7, common-vector-law source assumptions imply the
textbook `t^2` projected characteristic-function convergence with a centered
Gaussian covariance-bilinear coordinate table.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_commonVectorLawGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_vector_law := hX_vector_law)
      (hX_sequence_law := hX_sequence_law))
    hZ_gaussian hZ_memLp hZ_coordinate_integrable hZ_coordinate_mean
    Gamma hGamma

/--
Durrett 2019, Theorem 3.10.7, common-vector-law source assumptions imply
projected characteristic-function convergence with centered product identities
for the Gaussian limit, before the textbook `t^2` rewrite.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_commonVectorLawGaussianSource_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_projectedSummandCLT_centeredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_vector_law := hX_vector_law)
      (hX_sequence_law := hX_sequence_law))
    hZ_gaussian hZ_memLp hZ_coordinate_memLp hZ_coordinate_mean Gamma
    hZ_centered_product

/--
Durrett 2019, Theorem 3.10.7, common-vector-law source assumptions imply the
textbook `t^2` projected characteristic-function convergence.

The common finite-coordinate vector law and the infinite product law discharge
the i.i.d. sample-vector hypotheses used by the projected summand CLT, then
the V346 characteristic-function bridge supplies Durrett's displayed endpoint.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_commonVectorLawGaussianSource_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        X n ω -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        P X)) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_projectedSummandCLT_centeredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_vector_law := hX_vector_law)
      (hX_sequence_law := hX_sequence_law))
    hZ_gaussian hZ_memLp hZ_coordinate_memLp hZ_coordinate_mean Gamma
    hZ_centered_product

/--
Durrett 2019, Theorem 3.10.7, common-vector-law source assumptions imply the
literal normalized-sum projected characteristic-function display before the
textbook `t^2` rewrite.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_commonVectorLawGaussianSource_centeredProduct_explicitMean_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)} {mu : Coordinate -> ℝ}
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    ((∑ i ∈ Finset.range n, X coordinate i ω) -
                      (n : ℝ) * mu coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  intro theta t
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_commonVectorLawGaussianSource_centeredProduct
      (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)
      (hX_vector_law := hX_vector_law) (hX_sequence_law := hX_sequence_law)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  have hfun :
      (fun ω : Ω =>
        ∑ i, theta i *
          (√(n : ℝ) •
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                X n ω -
              StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                P X)) i) =
      (fun ω : Ω =>
        ∑ coordinate, theta coordinate *
          ((√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, X coordinate i ω) -
              (n : ℝ) * mu coordinate))) := by
    funext ω
    have hnorm :=
      durrett2019_theorem_3_10_7_finiteCoordinate_explicitMean_normalization_eq_sum
        (P := P) X mu hX_coordinate_mean n ω
    have hsum :=
      congrArg (fun v : Coordinate -> ℝ => ∑ coordinate, theta coordinate * v coordinate)
        hnorm
    simpa [Pi.smul_apply, Pi.sub_apply, smul_eq_mul] using hsum
  rw [hfun]

/--
Durrett 2019, Theorem 3.10.7, common-vector-law source assumptions imply the
literal normalized-sum projected characteristic-function display in the
textbook `t^2` exponent form.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_commonVectorLawGaussianSource_centeredProduct_explicitMean_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)} {mu : Coordinate -> ℝ}
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            (P.map
              (fun ω =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    ((∑ i ∈ Finset.range n, X coordinate i ω) -
                      (n : ℝ) * mu coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  intro theta t
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_commonVectorLawGaussianSource_centeredProduct
      (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)
      (hX_vector_law := hX_vector_law) (hX_sequence_law := hX_sequence_law)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  have hfun :
      (fun ω : Ω =>
        ∑ i, theta i *
          (√(n : ℝ) •
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                X n ω -
              StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                P X)) i) =
      (fun ω : Ω =>
        ∑ coordinate, theta coordinate *
          ((√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, X coordinate i ω) -
              (n : ℝ) * mu coordinate))) := by
    funext ω
    have hnorm :=
      durrett2019_theorem_3_10_7_finiteCoordinate_explicitMean_normalization_eq_sum
        (P := P) X mu hX_coordinate_mean n ω
    have hsum :=
      congrArg (fun v : Coordinate -> ℝ => ∑ coordinate, theta coordinate * v coordinate)
        hnorm
    simpa [Pi.smul_apply, Pi.sub_apply, smul_eq_mul] using hsum
  rw [hfun]

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from a common
vector law and a centered Gaussian covariance-bilinear coordinate table, before
rewriting the projected characteristic functions into the textbook `t^2`
display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hsummand :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_vector_law := hX_vector_law)
        (hX_sequence_law := hX_sequence_law))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from a common
vector law and a centered Gaussian covariance-bilinear coordinate table, via
the textbook `t^2` characteristic-function endpoint.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource_centeredGaussianCovarianceBilinDualTable_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j))
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCovarianceBilinDualTable_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hsummand :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_vector_law := hX_vector_law)
        (hX_sequence_law := hX_sequence_law))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hGamma := hGamma)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from a common
vector law and centered product identities for the Gaussian limit, before
rewriting the projected characteristic functions into the textbook `t^2`
display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource_centeredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCenteredProduct
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hsummand :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_vector_law := hX_vector_law)
        (hX_sequence_law := hX_sequence_law))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from a common
vector law, via the textbook `t^2` characteristic-function endpoint and
centered product identities for the Gaussian limit.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource_centeredProduct_tsq
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT_centeredGaussianCenteredProduct_tsq
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas)
    (hsummand :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_vector_law := hX_vector_law)
        (hX_sequence_law := hX_sequence_law))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample source assumptions imply
projected characteristic-function convergence with a centered Gaussian
covariance-bilinear coordinate table.

The sample space is the infinite product `ℕ -> Coordinate -> ℝ`; local
product-law support supplies the common-vector-law hypotheses consumed by the
V360 covariance-table characteristic-function route.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample
            L (fun coordinate i sample => sample i coordinate) 0)
          (Measure.infinitePi (fun _ : ℕ => ν)))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        (fun coordinate i sample => sample i coordinate) n sample -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        (Measure.infinitePi (fun _ : ℕ => ν))
                        (fun coordinate i sample => sample i coordinate))) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_commonVectorLawGaussianSource_centeredGaussianCovarianceBilinDualTable
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X)
      (Z := Z) (ν := ν)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance := by simpa [X] using hZ_covariance)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hGamma := hGamma)
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample source assumptions imply
the textbook `t^2` projected characteristic-function convergence with a
centered Gaussian covariance-bilinear coordinate table.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample
            L (fun coordinate i sample => sample i coordinate) 0)
          (Measure.infinitePi (fun _ : ℕ => ν)))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        (fun coordinate i sample => sample i coordinate) n sample -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        (Measure.infinitePi (fun _ : ℕ => ν))
                        (fun coordinate i sample => sample i coordinate))) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_commonVectorLawGaussianSource_centeredGaussianCovarianceBilinDualTable
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X)
      (Z := Z) (ν := ν)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance := by simpa [X] using hZ_covariance)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hGamma := hGamma)
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample source assumptions imply
projected characteristic-function convergence with centered product identities
for the Gaussian limit, before the textbook `t^2` rewrite.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianSource_centeredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample
            L (fun coordinate i sample => sample i coordinate) 0)
          (Measure.infinitePi (fun _ : ℕ => ν)))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        (fun coordinate i sample => sample i coordinate) n sample -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        (Measure.infinitePi (fun _ : ℕ => ν))
                        (fun coordinate i sample => sample i coordinate))) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_commonVectorLawGaussianSource_centeredProduct
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X)
      (Z := Z) (ν := ν)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance := by simpa [X] using hZ_covariance)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample source assumptions imply
the textbook `t^2` projected characteristic-function convergence.

The sample space is the infinite product `ℕ -> Coordinate -> ℝ`; local
product-law support supplies the common-vector-law hypotheses consumed by the
V348 characteristic-function route.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianSource_centeredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample
            L (fun coordinate i sample => sample i coordinate) 0)
          (Measure.infinitePi (fun _ : ℕ => ν)))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        (fun coordinate i sample => sample i coordinate) n sample -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        (Measure.infinitePi (fun _ : ℕ => ν))
                        (fun coordinate i sample => sample i coordinate))) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_commonVectorLawGaussianSource_centeredProduct
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X)
      (Z := Z) (ν := ν)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance := by simpa [X] using hZ_covariance)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample finite-coordinate CLT
with a centered Gaussian covariance-bilinear coordinate table, before rewriting
the projected characteristic functions into the textbook `t^2` display.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianSource_centeredGaussianCovarianceBilinDualTable
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample
            L (fun coordinate i sample => sample i coordinate) 0)
          (Measure.infinitePi (fun _ : ℕ => ν)))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
              (Measure.infinitePi (fun _ : ℕ => ν))
              (fun coordinate i sample => sample i coordinate)))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource_centeredGaussianCovarianceBilinDualTable
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X)
      (Z := Z) (ν := ν)
      (hX_meas := by simpa [X] using hcanonicalCoordinateSource.2)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance := by simpa [X] using hZ_covariance)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hGamma := hGamma)
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample finite-coordinate CLT
with a centered Gaussian covariance-bilinear coordinate table, via the textbook
`t^2` characteristic-function endpoint.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianSource_centeredGaussianCovarianceBilinDualTable_tsq
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample
            L (fun coordinate i sample => sample i coordinate) 0)
          (Measure.infinitePi (fun _ : ℕ => ν)))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hGamma : ∀ i j,
      Gamma i j =
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
              (Measure.infinitePi (fun _ : ℕ => ν))
              (fun coordinate i sample => sample i coordinate)))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource_centeredGaussianCovarianceBilinDualTable_tsq
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X)
      (Z := Z) (ν := ν)
      (hX_meas := by simpa [X] using hcanonicalCoordinateSource.2)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance := by simpa [X] using hZ_covariance)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hGamma := hGamma)
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample finite-coordinate CLT
with centered product identities for the Gaussian limit, before the textbook
`t^2` rewrite.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianSource_centeredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample
            L (fun coordinate i sample => sample i coordinate) 0)
          (Measure.infinitePi (fun _ : ℕ => ν)))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
              (Measure.infinitePi (fun _ : ℕ => ν))
              (fun coordinate i sample => sample i coordinate)))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource_centeredProduct
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X)
      (Z := Z) (ν := ν)
      (hX_meas := by simpa [X] using hcanonicalCoordinateSource.2)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance := by simpa [X] using hZ_covariance)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample finite-coordinate CLT
via the textbook `t^2` characteristic-function endpoint.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianSource_centeredProduct_tsq
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample
            L (fun coordinate i sample => sample i coordinate) 0)
          (Measure.infinitePi (fun _ : ℕ => ν)))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
              (Measure.infinitePi (fun _ : ℕ => ν))
              (fun coordinate i sample => sample i coordinate)))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource_centeredProduct_tsq
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X)
      (Z := Z) (ν := ν)
      (hX_meas := by simpa [X] using hcanonicalCoordinateSource.2)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance := by simpa [X] using hZ_covariance)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hZ_centered_product := hZ_centered_product)
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample coordinate covariance
source assumptions imply projected characteristic-function convergence before
the textbook `t^2` rewrite.

This is the scalar covariance-table source form feeding the V361 canonical
product route: coordinate covariance identities on the Gaussian limit and the
canonical first summand produce the covariance-bilinear table hypotheses.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        (fun coordinate i sample => sample i coordinate) n sample -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        (Measure.infinitePi (fun _ : ℕ => ν))
                        (fun coordinate i sample => sample i coordinate))) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  let sampleVector :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hsample_memLp : MemLp sampleVector 2 (Measure.infinitePi (fun _ : ℕ => ν)) := by
    simpa [X, sampleVector] using
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_memLp_of_coordinate_memLp
        (P := Measure.infinitePi (fun _ : ℕ => ν)) (X := X) 0
        (by simpa [X] using hcanonicalCoordinateSource.1)
  have hsample_aemeas : AEMeasurable sampleVector (Measure.infinitePi (fun _ : ℕ => ν)) :=
    hsample_memLp.aemeasurable
  have hsample_map_memLp :
      MemLp id 2 ((Measure.infinitePi (fun _ : ℕ => ν)).map sampleVector) := by
    simpa [sampleVector] using
      (MeasureTheory.memLp_map_measure_iff aestronglyMeasurable_id hsample_aemeas).2
        hsample_memLp
  have hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0 :=
    durrett2019_theorem_3_10_7_allProjectionMean_zero_of_thetaProjectionMean_zero
      (Q := Q) (Z := Z)
      (durrett2019_theorem_3_10_7_thetaProjectionMean_zero_of_coordinateMean_zero
        (Q := Q) (Z := Z)
        (fun coordinate => (hZ_coordinate_memLp coordinate).integrable (by simp))
        hZ_coordinate_mean)
  have hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j :=
    durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
      (μ := Q) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable Gamma hZ_covariance
  have hX_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual
          ((Measure.infinitePi (fun _ : ℕ => ν)).map sampleVector)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j :=
    durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
      (μ := Measure.infinitePi (fun _ : ℕ => ν)) (Y := sampleVector)
      hsample_map_memLp hsample_aemeas Gamma
      (fun i j => by
        exact
          (durrett2019_theorem_3_10_7_canonicalSampleCoordinateCovariance_eq_vectorLaw
            (ν := ν) hcoordinate_meas 0 i j).trans (hν_covariance i j))
  exact
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianSource_centeredGaussianCovarianceBilinDualTable
      (ν := ν) (Q := Q) (Z := Z)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance :=
        durrett2019_theorem_3_10_7_allProjectionCovariance_of_covarianceBilinDualTables
          (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X) (Z := Z)
          (hZ_memLp := hZ_memLp)
          (hX_sample_aemeas := by simpa [X, sampleVector] using hsample_aemeas)
          (hX_sample_map_memLp := by simpa [X, sampleVector] using hsample_map_memLp)
          (Gamma := Gamma) (hZ_table := hZ_table)
          (hX_table := by simpa [X, sampleVector] using hX_table))
      (hZ_coordinate_integrable := fun coordinate =>
        (hZ_coordinate_memLp coordinate).integrable (by simp))
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma) (hGamma := fun i j => (hZ_table i j).symm)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample coordinate covariance
source assumptions imply the textbook `t^2` projected characteristic-function
convergence.

This is the scalar covariance-table source form feeding the V349 all-dual
canonical product route: coordinatewise zero means turn covariance identities
into centered products on the Gaussian side, while the canonical vector law
supplies the first-summand covariance table.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        (fun coordinate i sample => sample i coordinate) n sample -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        (Measure.infinitePi (fun _ : ℕ => ν))
                        (fun coordinate i sample => sample i coordinate))) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  let sampleVector :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hsample_memLp : MemLp sampleVector 2 (Measure.infinitePi (fun _ : ℕ => ν)) := by
    simpa [X, sampleVector] using
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_memLp_of_coordinate_memLp
        (P := Measure.infinitePi (fun _ : ℕ => ν)) (X := X) 0
        (by simpa [X] using hcanonicalCoordinateSource.1)
  have hsample_aemeas : AEMeasurable sampleVector (Measure.infinitePi (fun _ : ℕ => ν)) :=
    hsample_memLp.aemeasurable
  have hsample_map_memLp :
      MemLp id 2 ((Measure.infinitePi (fun _ : ℕ => ν)).map sampleVector) := by
    simpa [sampleVector] using
      (MeasureTheory.memLp_map_measure_iff aestronglyMeasurable_id hsample_aemeas).2
        hsample_memLp
  have hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0 :=
    durrett2019_theorem_3_10_7_allProjectionMean_zero_of_thetaProjectionMean_zero
      (Q := Q) (Z := Z)
      (durrett2019_theorem_3_10_7_thetaProjectionMean_zero_of_coordinateMean_zero
        (Q := Q) (Z := Z)
        (fun coordinate => (hZ_coordinate_memLp coordinate).integrable (by simp))
        hZ_coordinate_mean)
  have hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j :=
    durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
      (μ := Q) (Y := Z) hZ_memLp hZ_gaussian.aemeasurable Gamma hZ_covariance
  have hX_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual
          ((Measure.infinitePi (fun _ : ℕ => ν)).map sampleVector)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j :=
    durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
      (μ := Measure.infinitePi (fun _ : ℕ => ν)) (Y := sampleVector)
      hsample_map_memLp hsample_aemeas Gamma
      (fun i j => by
        exact
          (durrett2019_theorem_3_10_7_canonicalSampleCoordinateCovariance_eq_vectorLaw
            (ν := ν) hcoordinate_meas 0 i j).trans (hν_covariance i j))
  exact
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianSource_centeredProduct
      (ν := ν) (Q := Q) (Z := Z)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance :=
        durrett2019_theorem_3_10_7_allProjectionCovariance_of_covarianceBilinDualTables
          (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X) (Z := Z)
          (hZ_memLp := hZ_memLp)
          (hX_sample_aemeas := by simpa [X, sampleVector] using hsample_aemeas)
          (hX_sample_map_memLp := by simpa [X, sampleVector] using hsample_map_memLp)
          (Gamma := Gamma) (hZ_table := hZ_table)
          (hX_table := by simpa [X, sampleVector] using hX_table))
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_centered_product :=
        durrett2019_theorem_3_10_7_centeredProduct_eq_of_coordinateCovariance
          (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
          hZ_covariance)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample centered-product source
assumptions imply projected characteristic-function convergence before the
textbook `t^2` rewrite.

This is the centered textbook source display for the canonical i.i.d. product
sample, routed through the coordinate-covariance characteristic wrapper.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCenteredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector, sampleVector i * sampleVector j ∂ν) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        (fun coordinate i sample => sample i coordinate) n sample -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        (Measure.infinitePi (fun _ : ℕ => ν))
                        (fun coordinate i sample => sample i coordinate))) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
    (ν := ν) (Q := Q) (Z := Z)
    (hcoordinate_meas := hcoordinate_meas)
    (hν_coordinate_memLp := hν_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    (hν_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := ν) (Y := fun sampleVector coordinate => sampleVector coordinate)
        hν_coordinate_memLp hν_coordinate_mean Gamma hν_centered_product)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample centered-product source
assumptions imply the textbook `t^2` projected characteristic-function
convergence.

This is the centered textbook source display for the canonical i.i.d. product
sample, now routed through the V350 coordinate-covariance characteristic
wrapper.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCenteredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector, sampleVector i * sampleVector j ∂ν) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ i, theta i *
                  (√(n : ℝ) •
                    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                        (fun coordinate i sample => sample i coordinate) n sample -
                      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
                        (Measure.infinitePi (fun _ : ℕ => ν))
                        (fun coordinate i sample => sample i coordinate))) i)) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
    (ν := ν) (Q := Q) (Z := Z)
    (hcoordinate_meas := hcoordinate_meas)
    (hν_coordinate_memLp := hν_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    (hν_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := ν) (Y := fun sampleVector coordinate => sampleVector coordinate)
        hν_coordinate_memLp hν_coordinate_mean Gamma hν_centered_product)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from projected
scalar CLTs.

This is the Cramér-Wold assembly step in Durrett's proof: once every continuous
linear projection of the scaled centered vector has the scalar CLT, the vector
itself converges in distribution.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hscalar :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT
        (P := P) (Q := Q) X Z) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q := by
  let B :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_finiteDimensional
      (P := P) (Q := Q) X Z hX_meas hZ_aemeas hscalar
  exact B.cramerWold_vector_clt B.projected_clt

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from projected
summand CLTs.

This packages the preceding wrapper with the finite-average algebra that
rewrites the projected empirical vector into the one-dimensional CLT summand
form.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hsummand :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT
        (P := P) (Q := Q) X Z) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedScalarCLT
    (P := P) (Q := Q) hX_meas hZ_aemeas
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
      (P := P) (Q := Q) hsummand)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from vector
source fields and a Gaussian covariance identification.

The hypotheses are the formal Cramér-Wold source shape: finite second moments
for each coordinate, i.i.d. finite-coordinate sample vectors, a centered
Gaussian vector limit, and equality of every projected limit variance with the
corresponding projected summand variance.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianSource
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT
    (P := P) (Q := Q) hX_meas hZ_aemeas
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_indep := hX_indep) (hX_ident := hX_ident))

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from
coordinate covariance tables.

This is the source-facing covariance-table form of Durrett's proof.  The
coordinate covariance tables for the Gaussian limit and the first summand
discharge the all-projection covariance hypothesis used by the compiled
Cramér-Wold CLT wrapper.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateCovarianceTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual
          (P.map
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0))
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q := by
  let sampleVector :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0
  have hX_vector_memLp : MemLp sampleVector 2 P := by
    simpa [sampleVector] using
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_memLp_of_coordinate_memLp
        (P := P) (X := X) 0 hX_coordinate_memLp
  have hX_sample_aemeas : AEMeasurable sampleVector P :=
    hX_vector_memLp.aemeasurable
  have hX_sample_map_memLp : MemLp id 2 (P.map sampleVector) := by
    simpa [sampleVector] using
      (MeasureTheory.memLp_map_measure_iff aestronglyMeasurable_id hX_sample_aemeas).2
        hX_vector_memLp
  exact
    durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_meas := hX_meas) (hZ_aemeas := hZ_aemeas)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean)
      (hZ_covariance :=
        durrett2019_theorem_3_10_7_allProjectionCovariance_of_covarianceBilinDualTables
          (P := P) (Q := Q) (X := X) (Z := Z)
          (hZ_memLp := hZ_memLp)
          (hX_sample_aemeas := by simpa [sampleVector] using hX_sample_aemeas)
          (hX_sample_map_memLp := by simpa [sampleVector] using hX_sample_map_memLp)
          (Gamma := Gamma) (hZ_table := hZ_table) (hX_table := hX_table))
      (hX_indep := hX_indep) (hX_ident := hX_ident)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from centered
theta means and coordinate covariance tables.

This packages both finite-coordinate source handoffs: centered theta
projections imply the all-dual centered Gaussian mean hypothesis, and coordinate
covariance tables imply the all-dual covariance hypothesis.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianThetaMeanCoordinateCovarianceTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_theta_mean : ∀ theta : Coordinate -> ℝ,
      (∫ ω, (∑ i, theta i * Z ω i) ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual
          (P.map
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0))
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateCovarianceTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_aemeas := hZ_aemeas)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean :=
      durrett2019_theorem_3_10_7_allProjectionMean_zero_of_thetaProjectionMean_zero
        (Q := Q) (Z := Z) hZ_theta_mean)
    (Gamma := Gamma) (hZ_table := hZ_table) (hX_table := hX_table)
    (hX_indep := hX_indep) (hX_ident := hX_ident)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from literal
coordinate centering and coordinate covariance tables.

This is the coordinate-source endpoint for the mean side of Durrett's
finite-dimensional CLT proof: coordinatewise zero Gaussian means are converted
to centered theta projections, while the covariance tables are consumed by the
compiled all-dual handoff.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCovarianceTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual
          (P.map
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0))
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianThetaMeanCoordinateCovarianceTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_aemeas := hZ_aemeas)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_theta_mean :=
      durrett2019_theorem_3_10_7_thetaProjectionMean_zero_of_coordinateMean_zero
        (Q := Q) (Z := Z) hZ_coordinate_integrable hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_table := hZ_table) (hX_table := hX_table)
    (hX_indep := hX_indep) (hX_ident := hX_ident)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from literal
coordinate centering and scalar coordinate covariance identities.

This is the source endpoint immediately before Durrett's covariance table
notation: scalar coordinate covariance assumptions are converted into the
`covarianceBilinDual` coordinate tables consumed by the compiled vector CLT.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCoordinateCovariance
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hX_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => X i 0 ω) (fun ω => X j 0 ω) P =
        Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q := by
  let sampleVector :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0
  have hX_vector_memLp : MemLp sampleVector 2 P := by
    simpa [sampleVector] using
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_memLp_of_coordinate_memLp
        (P := P) (X := X) 0 hX_coordinate_memLp
  have hX_sample_aemeas : AEMeasurable sampleVector P :=
    hX_vector_memLp.aemeasurable
  have hX_sample_map_memLp : MemLp id 2 (P.map sampleVector) := by
    simpa [sampleVector] using
      (MeasureTheory.memLp_map_measure_iff aestronglyMeasurable_id hX_sample_aemeas).2
        hX_vector_memLp
  exact
    durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCovarianceTable
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_meas := hX_meas) (hZ_aemeas := hZ_aemeas)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_table :=
        durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
          (μ := Q) (Y := Z) hZ_memLp hZ_aemeas Gamma hZ_covariance)
      (hX_table :=
        durrett2019_theorem_3_10_7_covarianceBilinDualTable_of_coordinateCovariance
          (μ := P) (Y := sampleVector) hX_sample_map_memLp hX_sample_aemeas Gamma
          (fun i j => by
            simpa [sampleVector,
              StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector]
              using hX_covariance i j))
      (hX_indep := hX_indep) (hX_ident := hX_ident)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from centered
coordinate product identities.

When the Gaussian limit and the first summand are coordinatewise centered,
Durrett's product displays `E[Z_i Z_j] = Gamma_{ij}` and
`E[X_i X_j] = Gamma_{ij}` are converted into scalar covariance identities and
then into the compiled covariance-table CLT wrapper.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCenteredProduct
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_centered_product : ∀ i j,
      (∫ ω, X i 0 ω * X j 0 ω ∂P) = Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCoordinateCovariance
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_aemeas := hZ_aemeas)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    (hX_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := P) (Y := fun ω coordinate => X coordinate 0 ω)
        hX_coordinate_memLp hX_coordinate_mean Gamma
        (fun i j => hX_centered_product i j))
    (hX_indep := hX_indep) (hX_ident := hX_ident)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT from an i.i.d.
common vector law.

This version packages the independence and identical-distribution assumptions
through the common finite-coordinate vector law and the infinite product law of
the sample-vector sequence.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianSource
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSample L X 0) P)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_projectedSummandCLT
    (P := P) (Q := Q) hX_meas hZ_aemeas
    (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
      (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_vector_law := hX_vector_law)
      (hX_sequence_law := hX_sequence_law))

/--
Durrett 2019, Theorem 3.10.7, common-vector-law finite-coordinate CLT from
literal coordinate centering and coordinate covariance tables.

This combines the coordinate-source endpoint with the existing local
common-vector-law support for the i.i.d. sample-vector hypotheses.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianCoordinateMeanCovarianceTable
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_table : ∀ i j,
      _root_.ProbabilityTheory.covarianceBilinDual
          (P.map
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0))
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) i)
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEvalCLM
            (Coordinate := Coordinate) j) =
        Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCovarianceTable
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_aemeas := hZ_aemeas)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma) (hZ_table := hZ_table) (hX_table := hX_table)
    (hX_indep :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_iIndepFun_of_hasLaw_infinitePi
        (P := P) (X := X) (ν := fun _ : ℕ => ν) hX_vector_law hX_sequence_law)
    (hX_ident :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_identDistrib_of_common_hasLaw
        (P := P) (X := X) (ν := ν) hX_vector_law)

/--
Durrett 2019, Theorem 3.10.7, common-vector-law finite-coordinate CLT from
literal coordinate centering and scalar coordinate covariance identities.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianCoordinateMeanCoordinateCovariance
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hX_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => X i 0 ω) (fun ω => X j 0 ω) P =
        Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCoordinateCovariance
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_meas := hX_meas) (hZ_aemeas := hZ_aemeas)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance := hZ_covariance) (hX_covariance := hX_covariance)
    (hX_indep :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_iIndepFun_of_hasLaw_infinitePi
        (P := P) (X := X) (ν := fun _ : ℕ => ν) hX_vector_law hX_sequence_law)
    (hX_ident :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_identDistrib_of_common_hasLaw
        (P := P) (X := X) (ν := ν) hX_vector_law)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT in the literal
normalized-sum display from scalar coordinate covariance assumptions.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {mu : Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hX_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => X i 0 ω) (fun ω => X j 0 ω) P =
        Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, X coordinate i ω) -
              (n : ℝ) * mu coordinate))
      atTop Z (fun _ => P) Q := by
  refine TendstoInDistribution.congr ?_ Filter.EventuallyEq.rfl
    (durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCoordinateCovariance
      (P := P) (Q := Q) (X := X) (Z := Z)
      (hX_meas := hX_meas) (hZ_aemeas := hZ_aemeas)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hX_covariance := hX_covariance)
      (hX_indep := hX_indep) (hX_ident := hX_ident))
  intro n
  exact Filter.Eventually.of_forall fun ω =>
    durrett2019_theorem_3_10_7_finiteCoordinate_explicitMean_normalization_eq_sum
      (P := P) X mu hX_coordinate_mean n ω

/--
Durrett 2019, Theorem 3.10.7, common-vector-law finite-coordinate CLT in the
literal normalized-sum display from scalar coordinate covariance assumptions.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)} {mu : Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hX_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => X i 0 ω) (fun ω => X j 0 ω) P =
        Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, X coordinate i ω) -
              (n : ℝ) * mu coordinate))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    (P := P) (Q := Q) (X := X) (Z := Z) (mu := mu)
    (hX_meas := hX_meas)
    (hX_coordinate_mean := hX_coordinate_mean)
    (hZ_aemeas := hZ_aemeas)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := hZ_coordinate_integrable)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance := hZ_covariance)
    (hX_covariance := hX_covariance)
    (hX_indep :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_iIndepFun_of_hasLaw_infinitePi
        (P := P) (X := X) (ν := fun _ : ℕ => ν) hX_vector_law hX_sequence_law)
    (hX_ident :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_identDistrib_of_common_hasLaw
        (P := P) (X := X) (ν := ν) hX_vector_law)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT in the literal
normalized-sum display from Durrett's centered-product covariance definition.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCenteredProduct_explicitMean_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {mu : Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_centered_product : ∀ i j,
      (∫ ω, (X i 0 ω - mu i) * (X j 0 ω - mu j) ∂P) =
        Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, X coordinate i ω) -
              (n : ℝ) * mu coordinate))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    (P := P) (Q := Q) (X := X) (Z := Z) (mu := mu)
    (hX_meas := hX_meas)
    (hX_coordinate_mean := hX_coordinate_mean)
    (hZ_aemeas := hZ_aemeas)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    (hX_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := P) (Y := fun ω coordinate => X coordinate 0 ω)
        mu hX_coordinate_mean Gamma hX_centered_product)
    (hX_indep := hX_indep) (hX_ident := hX_ident)

/--
Durrett 2019, Theorem 3.10.7, common-vector-law finite-coordinate CLT in the
literal normalized-sum display from Durrett's centered-product covariance
definition.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianCenteredProduct_explicitMean_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)} {mu : Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = mu coordinate)
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_centered_product : ∀ i j,
      (∫ ω, (X i 0 ω - mu i) * (X j 0 ω - mu j) ∂P) =
        Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, X coordinate i ω) -
              (n : ℝ) * mu coordinate))
      atTop Z (fun _ => P) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCenteredProduct_explicitMean_sum
    (P := P) (Q := Q) (X := X) (Z := Z) (mu := mu)
    (hX_meas := hX_meas)
    (hX_coordinate_mean := hX_coordinate_mean)
    (hZ_aemeas := hZ_aemeas)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_centered_product := hZ_centered_product)
    (hX_centered_product := hX_centered_product)
    (hX_indep :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_iIndepFun_of_hasLaw_infinitePi
        (P := P) (X := X) (ν := fun _ : ℕ => ν) hX_vector_law hX_sequence_law)
    (hX_ident :=
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector_identDistrib_of_common_hasLaw
        (P := P) (X := X) (ν := ν) hX_vector_law)

/--
Durrett 2019, Theorem 3.10.7, finite-coordinate multivariate CLT in the literal
centered normalized-sum display from centered product identities.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCenteredProduct_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_centered_product : ∀ i j,
      (∫ ω, X i 0 ω * X j 0 ω ∂P) = Gamma i j)
    (hX_indep :
      _root_.ProbabilityTheory.iIndepFun
        (fun i => StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        P)
    (hX_ident : ∀ i : ℕ,
      _root_.ProbabilityTheory.IdentDistrib
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X 0)
        P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            (∑ i ∈ Finset.range n, X coordinate i ω))
      atTop Z (fun _ => P) Q := by
  refine TendstoInDistribution.congr ?_ Filter.EventuallyEq.rfl
    (durrett2019_theorem_3_10_7_multivariateCLT_of_vectorGaussianCenteredProduct_explicitMean_sum
      (P := P) (Q := Q) (X := X) (Z := Z) (mu := fun _ : Coordinate => 0)
      (hX_meas := hX_meas)
      (hX_coordinate_mean := hX_coordinate_mean)
      (hZ_aemeas := hZ_aemeas)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_centered_product := hZ_centered_product)
      (hX_centered_product := fun i j => by
        simpa using hX_centered_product i j)
      (hX_indep := hX_indep) (hX_ident := hX_ident))
  intro n
  exact Filter.Eventually.of_forall fun ω => by
    ext coordinate
    simp

/--
Durrett 2019, Theorem 3.10.7, common-vector-law finite-coordinate CLT in the
literal centered normalized-sum display from centered product identities.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianCenteredProduct_sum
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hX_coordinate_mean : ∀ coordinate, (∫ ω, X coordinate 0 ω ∂P) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hX_centered_product : ∀ i j,
      (∫ ω, X i 0 ω * X j 0 ω ∂P) = Gamma i j)
    (hX_vector_law : ∀ i : ℕ,
      _root_.ProbabilityTheory.HasLaw
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i)
        ν P)
    (hX_sequence_law :
      _root_.ProbabilityTheory.HasLaw
        (fun ω i =>
          StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            (∑ i ∈ Finset.range n, X coordinate i ω))
      atTop Z (fun _ => P) Q := by
  refine TendstoInDistribution.congr ?_ Filter.EventuallyEq.rfl
    (durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianCenteredProduct_explicitMean_sum
      (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
      (mu := fun _ : Coordinate => 0)
      (hX_meas := hX_meas)
      (hX_coordinate_mean := hX_coordinate_mean)
      (hZ_aemeas := hZ_aemeas)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_centered_product := hZ_centered_product)
      (hX_centered_product := fun i j => by
        simpa using hX_centered_product i j)
      (hX_vector_law := hX_vector_law)
      (hX_sequence_law := hX_sequence_law))
  intro n
  exact Filter.Eventually.of_forall fun ω => by
    ext coordinate
    simp

/--
Durrett 2019, Theorem 3.10.7, canonical i.i.d. product-sample endpoint from
literal coordinate centering and scalar coordinate covariance identities.

The sample space is the infinite product `ℕ -> Coordinate -> ℝ` with common
vector law `ν`; local product-law support supplies the common-vector-law
hypotheses consumed by the compiled finite-coordinate CLT wrapper.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
              (Measure.infinitePi (fun _ : ℕ => ν))
              (fun coordinate i sample => sample i coordinate)))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have hcanonicalCoordinateSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    durrett2019_theorem_3_10_7_multivariateCLT_of_commonVectorLawGaussianCoordinateMeanCoordinateCovariance
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) (X := X) (Z := Z)
      (ν := ν)
      (hX_meas := by simpa [X] using hcanonicalCoordinateSource.2)
      (hZ_aemeas := hZ_aemeas)
      (hX_coordinate_memLp := by simpa [X] using hcanonicalCoordinateSource.1)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hX_covariance := fun i j => by
        exact
          (durrett2019_theorem_3_10_7_canonicalSampleCoordinateCovariance_eq_vectorLaw
            (ν := ν) hcoordinate_meas 0 i j).trans (hν_covariance i j))
      (hX_vector_law := by simpa [X] using hcanonicalVectorSource.1)
      (hX_sequence_law := by simpa [X] using hcanonicalVectorSource.2)

/--
Durrett 2019, Theorem 3.10.7, canonical i.i.d. product-sample endpoint with an
explicit mean vector.

This is the textbook source display with the deterministic mean vector `mu`:
the scaled empirical vector is centered by `mu`, not by the abstract population
moment field used internally by the reusable Cramér-Wold wrapper.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ} {mu : Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = mu coordinate)
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample -
            mu))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  have hpopulation :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
          (Measure.infinitePi (fun _ : ℕ => ν))
          (fun coordinate i sample => sample i coordinate) =
        mu := by
    rw [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_populationMoment_eq_integral
      (ν := ν) hcoordinate_meas]
    ext coordinate
    exact hν_coordinate_mean coordinate
  simpa [hpopulation] using
    durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
      (ν := ν) (Q := Q) (Z := Z)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hZ_aemeas := hZ_aemeas)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hν_covariance := hν_covariance)

/--
Durrett 2019, Theorem 3.10.7 normalization algebra for the canonical product
sample.

The reusable empirical-moment normalization is exactly the textbook
`(S_n - n * mu) / sqrt n` coordinate display.
-/
theorem durrett2019_theorem_3_10_7_canonicalProduct_explicitMean_normalization_eq_sum
    {Coordinate : Type*} [Fintype Coordinate] (mu : Coordinate -> ℝ)
    (n : ℕ) (sample : ℕ -> Coordinate -> ℝ) :
    √(n : ℝ) •
        (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
            (fun coordinate i sample => sample i coordinate) n sample -
          mu) =
      fun coordinate : Coordinate =>
        (√(n : ℝ))⁻¹ *
          ((∑ i ∈ Finset.range n, sample i coordinate) -
            (n : ℝ) * mu coordinate) := by
  ext coordinate
  by_cases hn : n = 0
  · subst n
    simp [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment]
  · have hnpos_nat : 0 < n := Nat.pos_of_ne_zero hn
    have hnpos : 0 < (n : ℝ) := Nat.cast_pos.mpr hnpos_nat
    have hsqrt_pos : 0 < √(n : ℝ) := Real.sqrt_pos_of_pos hnpos
    have hsqrt_ne : √(n : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
    have hn_ne : (n : ℝ) ≠ 0 := ne_of_gt hnpos
    have hsqrt_sq : (√(n : ℝ)) ^ 2 = (n : ℝ) :=
      Real.sq_sqrt hnpos.le
    simp [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment,
      Pi.sub_apply, smul_eq_mul, div_eq_inv_mul]
    field_simp [hsqrt_ne, hn_ne]
    rw [hsqrt_sq]

/--
Durrett 2019, Theorem 3.10.7, canonical i.i.d. product-sample endpoint in the
literal normalized-sum display.

This is the source form `((S_n - n * mu) / sqrt n) => chi`, written
coordinatewise for a finite coordinate type.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ} {mu : Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = mu coordinate)
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, sample i coordinate) -
              (n : ℝ) * mu coordinate))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  refine TendstoInDistribution.congr ?_ Filter.EventuallyEq.rfl
    (durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean
      (ν := ν) (Q := Q) (Z := Z) (mu := mu)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hν_coordinate_mean := hν_coordinate_mean)
      (hZ_aemeas := hZ_aemeas)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hν_covariance := hν_covariance))
  intro n
  exact Filter.Eventually.of_forall fun sample =>
    durrett2019_theorem_3_10_7_canonicalProduct_explicitMean_normalization_eq_sum
      (Coordinate := Coordinate) mu n sample

/--
Durrett 2019, Theorem 3.10.7, canonical i.i.d. product-sample endpoint in the
literal centered normalized-sum display from coordinate covariance assumptions.

This is the zero-mean source form `S_n / sqrt n => chi`, written coordinatewise
for a finite coordinate type.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_integrable : ∀ coordinate, Integrable (fun ω => Z ω coordinate) Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            (∑ i ∈ Finset.range n, sample i coordinate))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  refine TendstoInDistribution.congr ?_ Filter.EventuallyEq.rfl
    (durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
      (ν := ν) (Q := Q) (Z := Z) (mu := fun _ : Coordinate => 0)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hν_coordinate_mean := hν_coordinate_mean)
      (hZ_aemeas := hZ_aemeas)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_integrable := hZ_coordinate_integrable)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hν_covariance := hν_covariance))
  intro n
  exact Filter.Eventually.of_forall fun sample => by
    ext coordinate
    simp

/--
Durrett 2019, Theorem 3.10.7, canonical i.i.d. product-sample endpoint from the
textbook nonzero-mean covariance definition.

This combines the literal normalized-sum display with Durrett's source
assumption `Gamma_ij = E[(X_i - mu_i) (X_j - mu_j)]`.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCenteredProduct_explicitMean_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ} {mu : Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = mu coordinate)
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector,
        (sampleVector i - mu i) * (sampleVector j - mu j) ∂ν) =
        Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, sample i coordinate) -
              (n : ℝ) * mu coordinate))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    (ν := ν) (Q := Q) (Z := Z) (mu := mu)
    (hcoordinate_meas := hcoordinate_meas)
    (hν_coordinate_memLp := hν_coordinate_memLp)
    (hν_coordinate_mean := hν_coordinate_mean)
    (hZ_aemeas := hZ_aemeas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    (hν_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := ν) (Y := fun sampleVector coordinate => sampleVector coordinate)
        mu hν_coordinate_mean Gamma hν_centered_product)

/--
Durrett 2019, Theorem 3.10.7, canonical i.i.d. product-sample endpoint from
centered coordinate product identities under the Gaussian limit and common
vector law.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCenteredProduct
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector, sampleVector i * sampleVector j ∂ν) = Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample -
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
              (Measure.infinitePi (fun _ : ℕ => ν))
              (fun coordinate i sample => sample i coordinate)))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q :=
  durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
    (ν := ν) (Q := Q) (Z := Z)
    (hcoordinate_meas := hcoordinate_meas)
    (hν_coordinate_memLp := hν_coordinate_memLp)
    (hZ_aemeas := hZ_aemeas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_integrable := fun coordinate =>
      (hZ_coordinate_memLp coordinate).integrable (by simp))
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    (hν_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := ν) (Y := fun sampleVector coordinate => sampleVector coordinate)
        hν_coordinate_memLp hν_coordinate_mean Gamma hν_centered_product)

/--
Durrett 2019, Theorem 3.10.7, canonical i.i.d. product-sample endpoint in the
literal centered normalized-sum display.

This is the centered source form `S_n / sqrt n => chi`, written
coordinatewise for a finite coordinate type.
-/
theorem durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCenteredProduct_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector, sampleVector i * sampleVector j ∂ν) = Gamma i j) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        fun coordinate : Coordinate =>
          (√(n : ℝ))⁻¹ *
            (∑ i ∈ Finset.range n, sample i coordinate))
      atTop Z (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q := by
  refine TendstoInDistribution.congr ?_ Filter.EventuallyEq.rfl
    (durrett2019_theorem_3_10_7_multivariateCLT_of_canonicalProductGaussianCenteredProduct_explicitMean_sum
      (ν := ν) (Q := Q) (Z := Z) (mu := fun _ : Coordinate => 0)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hν_coordinate_mean := hν_coordinate_mean)
      (hZ_aemeas := hZ_aemeas)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_centered_product := hZ_centered_product)
      (hν_centered_product := fun i j => by
        simpa using hν_centered_product i j))
  intro n
  exact Filter.Eventually.of_forall fun sample => by
    ext coordinate
    simp

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample centered-product source
assumptions imply the literal centered normalized-sum characteristic-function
display before the textbook `t^2` rewrite.

This is the characteristic-function version of the textbook centered display
`S_n / sqrt n`, with the Gaussian exponent left in arbitrary-frequency form.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCenteredProduct_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector, sampleVector i * sampleVector j ∂ν) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    (∑ i ∈ Finset.range n, sample i coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  intro theta t
  have hpopulation :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
          (Measure.infinitePi (fun _ : ℕ => ν))
          (fun coordinate i sample => sample i coordinate) =
        (fun _ : Coordinate => 0) := by
    rw [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_populationMoment_eq_integral
      (ν := ν) hcoordinate_meas]
    ext coordinate
    exact hν_coordinate_mean coordinate
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCenteredProduct
      (ν := ν) (Q := Q) (Z := Z)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hν_coordinate_mean := hν_coordinate_mean)
      (Gamma := Gamma)
      (hZ_centered_product := hZ_centered_product)
      (hν_centered_product := hν_centered_product)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  have hfun :
      (fun sample : ℕ -> Coordinate -> ℝ =>
        ∑ coordinate, theta coordinate *
          (√(n : ℝ) *
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i path => path i coordinate) n sample coordinate)) =
      (fun sample : ℕ -> Coordinate -> ℝ =>
        ∑ coordinate, theta coordinate *
          ((√(n : ℝ))⁻¹ *
            (∑ i ∈ Finset.range n, sample i coordinate))) := by
    funext sample
    have hnorm :=
      durrett2019_theorem_3_10_7_canonicalProduct_explicitMean_normalization_eq_sum
        (Coordinate := Coordinate) (fun _ : Coordinate => 0) n sample
    have hsum :=
      congrArg (fun v : Coordinate -> ℝ => ∑ coordinate, theta coordinate * v coordinate)
        hnorm
    simpa [Pi.sub_apply, smul_eq_mul] using hsum
  simp [hpopulation, hfun]

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample centered-product source
assumptions imply the literal centered normalized-sum characteristic-function
display.

This is the characteristic-function version of the textbook centered display
`S_n / sqrt n`, obtained by rewriting the reusable empirical-moment
normalization into the coordinatewise finite sum.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCenteredProduct_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector, sampleVector i * sampleVector j ∂ν) = Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    (∑ i ∈ Finset.range n, sample i coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  intro theta t
  have hpopulation :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
          (Measure.infinitePi (fun _ : ℕ => ν))
          (fun coordinate i sample => sample i coordinate) =
        (fun _ : Coordinate => 0) := by
    rw [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_populationMoment_eq_integral
      (ν := ν) hcoordinate_meas]
    ext coordinate
    exact hν_coordinate_mean coordinate
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCenteredProduct
      (ν := ν) (Q := Q) (Z := Z)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (hν_coordinate_mean := hν_coordinate_mean)
      (Gamma := Gamma)
      (hZ_centered_product := hZ_centered_product)
      (hν_centered_product := hν_centered_product)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  have hfun :
      (fun sample : ℕ -> Coordinate -> ℝ =>
        ∑ coordinate, theta coordinate *
          (√(n : ℝ) *
            StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i path => path i coordinate) n sample coordinate)) =
      (fun sample : ℕ -> Coordinate -> ℝ =>
        ∑ coordinate, theta coordinate *
          ((√(n : ℝ))⁻¹ *
            (∑ i ∈ Finset.range n, sample i coordinate))) := by
    funext sample
    have hnorm :=
      durrett2019_theorem_3_10_7_canonicalProduct_explicitMean_normalization_eq_sum
        (Coordinate := Coordinate) (fun _ : Coordinate => 0) n sample
    have hsum :=
      congrArg (fun v : Coordinate -> ℝ => ∑ coordinate, theta coordinate * v coordinate)
        hnorm
    simpa [Pi.sub_apply, smul_eq_mul] using hsum
  simp [hpopulation, hfun]

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample coordinate covariance
source assumptions imply the literal nonzero-mean normalized-sum
characteristic-function display before the textbook `t^2` rewrite.

This packages Durrett's displayed `(S_n - n * mu) / sqrt n` normalization at
arbitrary frequency, using the canonical product normalization algebra.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ} {mu : Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = mu coordinate)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    ((∑ i ∈ Finset.range n, sample i coordinate) -
                      (n : ℝ) * mu coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  intro theta t
  have hpopulation :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
          (Measure.infinitePi (fun _ : ℕ => ν))
          (fun coordinate i sample => sample i coordinate) =
        mu := by
    rw [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_populationMoment_eq_integral
      (ν := ν) hcoordinate_meas]
    ext coordinate
    exact hν_coordinate_mean coordinate
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
      (ν := ν) (Q := Q) (Z := Z)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hν_covariance := hν_covariance)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  have hfun :
      (fun sample : ℕ -> Coordinate -> ℝ =>
        ∑ coordinate, theta coordinate *
          (√(n : ℝ) *
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i path => path i coordinate) n sample coordinate -
              mu coordinate))) =
      (fun sample : ℕ -> Coordinate -> ℝ =>
        ∑ coordinate, theta coordinate *
          ((√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, sample i coordinate) -
              (n : ℝ) * mu coordinate))) := by
    funext sample
    have hnorm :=
      durrett2019_theorem_3_10_7_canonicalProduct_explicitMean_normalization_eq_sum
        (Coordinate := Coordinate) mu n sample
    have hsum :=
      congrArg (fun v : Coordinate -> ℝ => ∑ coordinate, theta coordinate * v coordinate)
        hnorm
    simpa [Pi.sub_apply, smul_eq_mul] using hsum
  simp [hpopulation, hfun]

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample coordinate covariance
source assumptions imply the literal centered normalized-sum
characteristic-function display before the textbook `t^2` rewrite.

This is the coordinate-covariance companion to the centered-product source
display, with the Gaussian exponent left in arbitrary-frequency form.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    (∑ i ∈ Finset.range n, sample i coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) := by
  intro theta t
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
      (ν := ν) (Q := Q) (Z := Z) (mu := fun _ : Coordinate => 0)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hν_coordinate_mean := hν_coordinate_mean)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hν_covariance := hν_covariance)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  simp

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample coordinate covariance
source assumptions imply the literal nonzero-mean normalized-sum
characteristic-function display.

This packages Durrett's displayed `(S_n - n * mu) / sqrt n` normalization at
the characteristic-function level, using the canonical product normalization
algebra to rewrite the reusable empirical-moment centering.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ} {mu : Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = mu coordinate)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    ((∑ i ∈ Finset.range n, sample i coordinate) -
                      (n : ℝ) * mu coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  intro theta t
  have hpopulation :
      StatInference.AsymptoticStatistics.vaart1998_finiteCoordinatePopulationMoment
          (Measure.infinitePi (fun _ : ℕ => ν))
          (fun coordinate i sample => sample i coordinate) =
        mu := by
    rw [StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateCanonicalSample_populationMoment_eq_integral
      (ν := ν) hcoordinate_meas]
    ext coordinate
    exact hν_coordinate_mean coordinate
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance
      (ν := ν) (Q := Q) (Z := Z)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hν_covariance := hν_covariance)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  have hfun :
      (fun sample : ℕ -> Coordinate -> ℝ =>
        ∑ coordinate, theta coordinate *
          (√(n : ℝ) *
            (StatInference.AsymptoticStatistics.vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i path => path i coordinate) n sample coordinate -
              mu coordinate))) =
      (fun sample : ℕ -> Coordinate -> ℝ =>
        ∑ coordinate, theta coordinate *
          ((√(n : ℝ))⁻¹ *
            ((∑ i ∈ Finset.range n, sample i coordinate) -
              (n : ℝ) * mu coordinate))) := by
    funext sample
    have hnorm :=
      durrett2019_theorem_3_10_7_canonicalProduct_explicitMean_normalization_eq_sum
        (Coordinate := Coordinate) mu n sample
    have hsum :=
      congrArg (fun v : Coordinate -> ℝ => ∑ coordinate, theta coordinate * v coordinate)
        hnorm
    simpa [Pi.sub_apply, smul_eq_mul] using hsum
  simp [hpopulation, hfun]

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample coordinate covariance
source assumptions imply the literal centered normalized-sum
characteristic-function display in the textbook `t^2` exponent form.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = 0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j)
    (hν_covariance : ∀ i j,
      _root_.ProbabilityTheory.covariance
        (fun sampleVector : Coordinate -> ℝ => sampleVector i)
        (fun sampleVector : Coordinate -> ℝ => sampleVector j) ν =
        Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    (∑ i ∈ Finset.range n, sample i coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) := by
  intro theta t
  have hbase :=
    durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
      (ν := ν) (Q := Q) (Z := Z) (mu := fun _ : Coordinate => 0)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (hν_coordinate_mean := hν_coordinate_mean)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_coordinate_memLp := hZ_coordinate_memLp)
      (hZ_coordinate_mean := hZ_coordinate_mean)
      (Gamma := Gamma)
      (hZ_covariance := hZ_covariance)
      (hν_covariance := hν_covariance)
      theta t
  refine Tendsto.congr' (Filter.Eventually.of_forall fun n => ?_) hbase
  simp

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample centered-product
covariance-definition assumptions imply the literal nonzero-mean normalized-sum
characteristic-function display before the textbook `t^2` rewrite.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCenteredProduct_explicitMean_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ} {mu : Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = mu coordinate)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector,
        (sampleVector i - mu i) * (sampleVector j - mu j) ∂ν) =
        Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    ((∑ i ∈ Finset.range n, sample i coordinate) -
                      (n : ℝ) * mu coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-((durrett2019_theorem_3_10_7_covarianceTableQuadratic
            (fun i => t * theta i) Gamma : ℂ) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    (ν := ν) (Q := Q) (Z := Z) (mu := mu)
    (hcoordinate_meas := hcoordinate_meas)
    (hν_coordinate_memLp := hν_coordinate_memLp)
    (hν_coordinate_mean := hν_coordinate_mean)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    (hν_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := ν) (Y := fun sampleVector coordinate => sampleVector coordinate)
        mu hν_coordinate_mean Gamma hν_centered_product)

/--
Durrett 2019, Theorem 3.10.7, canonical product-sample centered-product
covariance-definition assumptions imply the literal nonzero-mean normalized-sum
characteristic-function display.

This is the characteristic-function companion to the source theorem using
Durrett's covariance definition
`Gamma_ij = E[(X_i - mu_i) (X_j - mu_j)]`.
-/
theorem durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCenteredProduct_explicitMean_sum
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Coordinate -> ℝ} {mu : Coordinate -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (hν_coordinate_mean : ∀ coordinate,
      (∫ sampleVector, sampleVector coordinate ∂ν) = mu coordinate)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_coordinate_memLp : ∀ coordinate, MemLp (fun ω => Z ω coordinate) 2 Q)
    (hZ_coordinate_mean : ∀ coordinate, (∫ ω, Z ω coordinate ∂Q) = 0)
    (Gamma : Coordinate -> Coordinate -> ℝ)
    (hZ_centered_product : ∀ i j,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j)
    (hν_centered_product : ∀ i j,
      (∫ sampleVector,
        (sampleVector i - mu i) * (sampleVector j - mu j) ∂ν) =
        Gamma i j) :
    ∀ theta : Coordinate -> ℝ, ∀ t : ℝ,
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFun
            ((Measure.infinitePi (fun _ : ℕ => ν)).map
              (fun sample =>
                ∑ coordinate, theta coordinate *
                  ((√(n : ℝ))⁻¹ *
                    ((∑ i ∈ Finset.range n, sample i coordinate) -
                      (n : ℝ) * mu coordinate)))) t)
        atTop
        (𝓝 (Complex.exp
          (-(((t : ℂ) ^ 2 *
            (durrett2019_theorem_3_10_7_covarianceTableQuadratic
              theta Gamma : ℂ)) / 2)))) :=
  durrett2019_theorem_3_10_7_projectedCharacteristicFunctions_tsq_of_canonicalProductGaussianCoordinateMeanCoordinateCovariance_explicitMean_sum
    (ν := ν) (Q := Q) (Z := Z) (mu := mu)
    (hcoordinate_meas := hcoordinate_meas)
    (hν_coordinate_memLp := hν_coordinate_memLp)
    (hν_coordinate_mean := hν_coordinate_mean)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_coordinate_memLp := hZ_coordinate_memLp)
    (hZ_coordinate_mean := hZ_coordinate_mean)
    (Gamma := Gamma)
    (hZ_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
        (μ := Q) (Y := Z) hZ_coordinate_memLp hZ_coordinate_mean Gamma
        hZ_centered_product)
    (hν_covariance :=
      durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        (μ := ν) (Y := fun sampleVector coordinate => sampleVector coordinate)
        mu hν_coordinate_mean Gamma hν_centered_product)

end ProbabilityTheory
end StatInference
