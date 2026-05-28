import StatInference.AsymptoticStatistics.MEstimators
import Mathlib.Probability.Notation

/-!
# van der Vaart 1998 sample mean endpoints

This module keeps concrete sample-mean specializations of the Chapter 5
M-estimator endpoints separate from the large `MEstimators` development.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory _root_.ProbabilityTheory
open scoped BigOperators
open scoped ENNReal
open scoped _root_.ProbabilityTheory
open scoped Topology

/--
The textbook sample-mean estimating map `m_θ(x) = θ - x` on finite-coordinate
observations.
-/
def vaart1998_identityMeanObservationEstimatingMap
    (Idx : Type*) : (Idx -> ℝ) -> (Idx -> ℝ) -> Idx -> ℝ :=
  fun observation theta => theta - observation

/--
Observation-law source package for the finite-coordinate sample-mean route.

It bundles the reusable finite-coordinate vector-law source certificate with
the textbook observation-law mean orientation `E[X] = theta0`.
-/
structure Vaart1998SampleMeanObservationLawSource
    (Idx : Type*) [Fintype Idx] [MeasurableSpace (Idx -> ℝ)]
    (observationLaw : Measure (Idx -> ℝ))
    (theta0 : Idx -> ℝ) where
  /-- Coordinate measurability and coordinate `L²` control of the observation law. -/
  vector_law : Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw
  /-- The observation-law population mean is the target parameter. -/
  law_mean : (∫ observation, observation ∂observationLaw) = theta0

/--
The Chapter 4 finite-coordinate vector-law source and the law-oriented
population mean identity form the observation-law source package used by the
sample-mean endpoint.
-/
theorem Vaart1998SampleMeanObservationLawSource.of_vectorLawMean
    {Idx : Type*} [Fintype Idx] [MeasurableSpace (Idx -> ℝ)]
    {observationLaw : Measure (Idx -> ℝ)}
    {theta0 : Idx -> ℝ}
    (vectorLaw : Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (law_mean : (∫ observation, observation ∂observationLaw) = theta0) :
    Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0 :=
  { vector_law := vectorLaw
    law_mean := law_mean }

/--
The finite-coordinate vector-law source and the Chapter 4 coordinatewise
population-mean identity form the observation-law source package used by the
sample-mean endpoint.
-/
theorem Vaart1998SampleMeanObservationLawSource.of_vectorLawCoordinateMean
    {Idx : Type*} [Fintype Idx] [MeasurableSpace (Idx -> ℝ)]
    {observationLaw : Measure (Idx -> ℝ)} [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    (vectorLaw : Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw) :
    Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0 := by
  have hCoordinate_integrable : ∀ coordinate : Idx,
      Integrable (fun observation : Idx -> ℝ => observation coordinate)
        observationLaw := fun coordinate =>
    (vectorLaw.coordinate_memLp coordinate).integrable (by norm_num)
  have hCoordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw := by
    intro coordinate
    simpa using congrFun coordinate_mean coordinate
  exact
    { vector_law := vectorLaw
      law_mean :=
        (vaart1998_observationMean_eq_of_coordinateMean
          (observationLaw := observationLaw) (theta0 := theta0)
          hCoordinate_integrable hCoordinate_mean).symm }

/--
Projected Gaussian source package for the finite-coordinate sample-mean route.

The fields match the Gaussian limit package naturally supplied by the
finite-dimensional CLT lane: a Gaussian limit law, centered projected means,
and projected variances matching the observation law.
-/
structure Vaart1998SampleMeanProjectedGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    (Q : Measure Ω') [IsProbabilityMeasure Q]
    (observationLaw : Measure (Idx -> ℝ))
    [IsProbabilityMeasure observationLaw]
    (Z : Ω' -> Idx -> ℝ) where
  /-- The limit random vector has a Gaussian law. -/
  gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q
  /-- All continuous linear projections of the limit are centered. -/
  projected_mean_zero : ∀ L : StrongDual ℝ (Idx -> ℝ),
    (∫ ω, L (Z ω) ∂Q) = 0
  /-- The projected limit variances match the observation law. -/
  projected_variance : ∀ L : StrongDual ℝ (Idx -> ℝ),
    _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
      _root_.ProbabilityTheory.variance L observationLaw

/--
CLT-style Gaussian source package for the finite-coordinate sample-mean route.

This is the law-mean/diagonal-variance boundary naturally supplied by the
finite-dimensional Gaussian limit lane before it is converted to the projected
Gaussian source consumed by the concrete sample-mean endpoint.
-/
structure Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    (Q : Measure Ω') [IsProbabilityMeasure Q]
    (observationLaw : Measure (Idx -> ℝ))
    [IsProbabilityMeasure observationLaw]
    (Z : Ω' -> Idx -> ℝ) where
  /-- The limit random vector has a Gaussian law. -/
  gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q
  /-- The pushed-forward Gaussian limit law is centered. -/
  law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0
  /-- The diagonal projected Gaussian covariance matches the observation law. -/
  projected_variance : ∀ L : StrongDual ℝ (Idx -> ℝ),
    _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
      _root_.ProbabilityTheory.variance L observationLaw

/--
Chapter 4 canonical source package for the finite-coordinate sample-mean
route.

It bundles the observation-law finite-coordinate vector source, the
coordinatewise population-mean identity, and the canonical Gaussian
mean/covariance fields in the exact shape consumed by the current sample-mean
endpoint.
-/
structure Vaart1998SampleMeanChapter4CanonicalSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    (Q : Measure Ω') [IsProbabilityMeasure Q]
    (observationLaw : Measure (Idx -> ℝ))
    [IsProbabilityMeasure observationLaw]
    (theta0 : Idx -> ℝ)
    (Z : Ω' -> Idx -> ℝ) where
  /-- Coordinate measurability and coordinate `L²` control of the observation law. -/
  observation_vector_law :
    Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw
  /-- Coordinatewise population means identify the true sample-mean parameter. -/
  observation_coordinate_mean :
    theta0 =
      fun coordinate : Idx =>
        ∫ observation,
          observation coordinate ∂observationLaw
  /-- The limit random vector has a Gaussian law. -/
  gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q
  /-- The pushed-forward Gaussian limit law is centered in probability notation. -/
  gaussian_map_mean_zero : (Q.map Z)[id] = 0
  /-- The projected Gaussian covariance matches the observation-law variance. -/
  covariance_observationLaw :
    ∀ L : StrongDual ℝ (Idx -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; observationLaw]

/--
Law-centered-product Gaussian source package for the finite-coordinate
sample-mean route.

This is the Chapter 4 notation-shaped centered-product boundary: it bundles
the Gaussian limit law, its probability-notation mean zero, and the law-level
centered-product identities against the observation law.
-/
structure Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    (Q : Measure Ω') [IsProbabilityMeasure Q]
    (observationLaw : Measure (Idx -> ℝ))
    [IsProbabilityMeasure observationLaw]
    (theta0 : Idx -> ℝ)
    (Z : Ω' -> Idx -> ℝ) where
  /-- The limit random vector has a Gaussian law. -/
  gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q
  /-- The pushed-forward Gaussian limit law is centered in probability notation. -/
  gaussian_map_mean_zero : (Q.map Z)[id] = 0
  /-- Law-level centered products match the observation-law centered products. -/
  law_observation_centered_product : ∀ i j : Idx,
    (∫ z, z i * z j ∂(Q.map Z)) =
      ∫ observation,
        (observation i - theta0 i) *
          (observation j - theta0 j) ∂observationLaw

/--
Explicit pushed-forward law mean zero and law-level centered products form the
Chapter 4 notation-shaped Gaussian/product source package.
-/
theorem
    Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource.of_lawMeanLawCenteredProduct
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) :=
  { gaussian := hZ_gaussian
    gaussian_map_mean_zero := by
      simpa using hZ_law_mean_zero
    law_observation_centered_product := hZ_law_observation_centered_product }

/--
Chapter 4 probability-notation mean zero supplies the bundled CLT-style
Gaussian source used by the finite-coordinate sample-mean endpoint.
-/
theorem
    Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource.of_probabilityMeanZero_projectedVariance
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource
      (Q := Q) (observationLaw := observationLaw) (Z := Z) :=
  { gaussian := hZ_gaussian
    law_mean_zero :=
      vaart1998_finiteCoordinateIntegralMapMean_eq_zero_of_map_mean_zero
        (Q := Q) (Z := Z) hZ_mean_zero
    projected_variance := hZ_projected_variance }

/--
The Chapter 4 canonical mean/covariance source fields provide the bundled
Gaussian source used by the finite-coordinate sample-mean endpoint.
-/
theorem
    Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource.of_chapter4CanonicalMeanCovarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource
      (Q := Q) (observationLaw := observationLaw) (Z := Z) :=
  Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource.of_probabilityMeanZero_projectedVariance
    (Q := Q) (observationLaw := observationLaw) (Z := Z)
    hZ_gaussian hZ_mean_zero (by
      intro L
      simpa using hZ_covariance_observationLaw L)

/--
The finite-coordinate CLT/covariance-table source shape supplies the projected
Gaussian source package for the sample-mean endpoint.
-/
theorem Vaart1998SampleMeanProjectedGaussianSource.of_mapMeanZero_projectedVariance
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    [CompleteSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    Vaart1998SampleMeanProjectedGaussianSource
      (Q := Q) (observationLaw := observationLaw) (Z := Z) := by
  haveI : _root_.ProbabilityTheory.IsGaussian (Q.map Z) :=
    hZ_gaussian.isGaussian_map
  have hZ_memLp_law : MemLp id 2 (Q.map Z) :=
    _root_.ProbabilityTheory.IsGaussian.memLp_two_id
  have hZ_memLp_sample : MemLp Z 2 Q := by
    simpa [Function.comp_def] using
      (MeasureTheory.memLp_map_measure_iff
        aestronglyMeasurable_id hZ_gaussian.aemeasurable).1 hZ_memLp_law
  have hZ_integrable : Integrable Z Q :=
    hZ_memLp_sample.integrable (by norm_num)
  have hZ_sample_mean_zero : (∫ ω, Z ω ∂Q) = 0 := by
    have hIntegral :
        (∫ ω, Z ω ∂Q) = ∫ z, z ∂(Q.map Z) := by
      simpa [Function.comp_def] using
        (integral_map hZ_gaussian.aemeasurable
          (f := fun z : Idx -> ℝ => z) aestronglyMeasurable_id).symm
    exact hIntegral.trans hZ_law_mean_zero
  exact
    { gaussian := hZ_gaussian
      projected_mean_zero := by
        intro L
        calc
          (∫ ω, L (Z ω) ∂Q) = L (∫ ω, Z ω ∂Q) :=
            L.integral_comp_comm hZ_integrable
          _ = 0 := by rw [hZ_sample_mean_zero, map_zero]
      projected_variance := hZ_projected_variance }

/--
The bundled CLT-style Gaussian source supplies the projected Gaussian source
consumed by the concrete sample-mean endpoint.
-/
theorem Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource.projectedGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    [CompleteSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {Z : Ω' -> Idx -> ℝ}
    (gaussianSource :
      Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource
        (Q := Q) (observationLaw := observationLaw) (Z := Z)) :
    Vaart1998SampleMeanProjectedGaussianSource
      (Q := Q) (observationLaw := observationLaw) (Z := Z) :=
  Vaart1998SampleMeanProjectedGaussianSource.of_mapMeanZero_projectedVariance
    (Q := Q) (observationLaw := observationLaw) (Z := Z)
    gaussianSource.gaussian gaussianSource.law_mean_zero
    gaussianSource.projected_variance

/--
The vector population mean identity determines coordinate population means for
finite-coordinate observations.
-/
theorem
    vaart1998_coordinateMean_of_observationMean_eq
    {Idx : Type*} [Fintype Idx] [MeasurableSpace (Idx -> ℝ)]
    {observationLaw : Measure (Idx -> ℝ)}
    {theta0 : Idx -> ℝ}
    (hObservation_coordinate_integrable : ∀ coordinate : Idx,
      Integrable (fun observation : Idx -> ℝ => observation coordinate)
        observationLaw)
    (hTheta0_mean : theta0 =
      ∫ observation,
        observation ∂observationLaw) :
    ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw := by
  intro coordinate
  rw [hTheta0_mean, MeasureTheory.eval_integral
    (f := fun observation : Idx -> ℝ => observation)
    hObservation_coordinate_integrable coordinate]

/--
A bundled sample-mean observation source and the Chapter 4 canonical
Gaussian mean/covariance fields form the current Chapter 4 canonical source
certificate consumed by the positive-sample Theorem 5.41 endpoint.
-/
theorem
    Vaart1998SampleMeanChapter4CanonicalSource.of_observationSourceCanonicalGaussian
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) := by
  have hCoordinate_integrable : ∀ coordinate : Idx,
      Integrable (fun observation : Idx -> ℝ => observation coordinate)
        observationLaw := fun coordinate =>
    (observationSource.vector_law.coordinate_memLp coordinate).integrable
      (by norm_num)
  exact
    { observation_vector_law := observationSource.vector_law
      observation_coordinate_mean := by
        funext coordinate
        exact
          vaart1998_coordinateMean_of_observationMean_eq
            (observationLaw := observationLaw) (theta0 := theta0)
            hCoordinate_integrable observationSource.law_mean.symm coordinate
      gaussian := hZ_gaussian
      gaussian_map_mean_zero := hZ_mean_zero
      covariance_observationLaw := hZ_covariance_observationLaw }

/--
The separated finite-coordinate vector-law source and law-oriented population
mean identity provide the Chapter 4 canonical sample-mean source once the
canonical Gaussian mean/covariance fields are available.
-/
theorem
    Vaart1998SampleMeanChapter4CanonicalSource.of_vectorLawMeanCanonicalGaussian
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) :=
  Vaart1998SampleMeanChapter4CanonicalSource.of_observationSourceCanonicalGaussian
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanObservationLawSource.of_vectorLawMean
      (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
      observationVectorLawSource hObservation_law_mean)
    hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw

/--
The separated finite-coordinate vector-law source and Chapter 4 coordinatewise
population-mean identity provide the Chapter 4 canonical sample-mean source
once the canonical Gaussian mean/covariance fields are available.
-/
theorem
    Vaart1998SampleMeanChapter4CanonicalSource.of_vectorLawCoordinateMeanCanonicalGaussian
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) :=
  { observation_vector_law := observationVectorLawSource
    observation_coordinate_mean := hObservation_coordinate_mean
    gaussian := hZ_gaussian
    gaussian_map_mean_zero := hZ_mean_zero
    covariance_observationLaw := hZ_covariance_observationLaw }

/--
The finite-coordinate vector-law source, Chapter 4 coordinatewise
population-mean identity, and bundled sample-mean Gaussian source form the
Chapter 4 canonical sample-mean source.
-/
theorem
    Vaart1998SampleMeanChapter4CanonicalSource.of_vectorLawCoordinateMeanGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (gaussianSource :
      Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource
        (Q := Q) (observationLaw := observationLaw) (Z := Z)) :
    Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) := by
  exact
    { observation_vector_law := observationVectorLawSource
      observation_coordinate_mean := hObservation_coordinate_mean
      gaussian := gaussianSource.gaussian
      gaussian_map_mean_zero := by
        simpa using gaussianSource.law_mean_zero
      covariance_observationLaw := by
        intro L
        simpa using gaussianSource.projected_variance L }

/--
Vector `L²` integrability determines coordinate `L²` integrability for
finite-coordinate observations.
-/
theorem
    vaart1998_coordinateMemLp_of_observationMemLp
    {Idx : Type*} [Fintype Idx] [MeasurableSpace (Idx -> ℝ)]
    {observationLaw : Measure (Idx -> ℝ)}
    (hObservation_memLp :
      MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw) :
    ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw := by
  intro coordinate
  exact hObservation_memLp.eval coordinate

/--
Law-level vector `L²` integrability is the concrete observation vector `L²`
source used by the sample-mean endpoint.
-/
theorem
    vaart1998_observationMemLp_of_observationLawMemLp
    {Idx : Type*} [Fintype Idx] [MeasurableSpace (Idx -> ℝ)]
    {observationLaw : Measure (Idx -> ℝ)}
    (hObservation_law_memLp : MemLp id 2 observationLaw) :
    MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw := by
  simpa [id] using hObservation_law_memLp

/--
The observation-law mean orientation `E[X] = theta0` gives the endpoint's
`theta0 = E[X]` source.
-/
theorem
    vaart1998_theta0_mean_of_observationLaw_mean
    {Idx : Type*} [Fintype Idx] [MeasurableSpace (Idx -> ℝ)]
    {observationLaw : Measure (Idx -> ℝ)}
    {theta0 : Idx -> ℝ}
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0) :
    theta0 =
      ∫ observation,
        observation ∂observationLaw :=
  hObservation_law_mean.symm

/--
Coordinatewise zero means for a finite-coordinate Gaussian limit imply the
projected mean-zero source for every continuous linear functional.
-/
theorem
    vaart1998_z_projected_mean_zero_of_coordinate_mean_zero_of_gaussian
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0) :
    ∀ L : StrongDual ℝ (Idx -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0 := by
  haveI : _root_.ProbabilityTheory.IsGaussian (Q.map Z) :=
    hZ_gaussian.isGaussian_map
  have hZ_memLp_law : MemLp id 2 (Q.map Z) :=
    _root_.ProbabilityTheory.IsGaussian.memLp_two_id
  have hZ_memLp_sample : MemLp Z 2 Q := by
    simpa [Function.comp_def] using
      (MeasureTheory.memLp_map_measure_iff
        aestronglyMeasurable_id hZ_gaussian.aemeasurable).1 hZ_memLp_law
  have hZ_coordinate_integrable : ∀ coordinate : Idx,
      Integrable (fun ω => Z ω coordinate) Q := fun coordinate =>
    (hZ_memLp_sample.eval coordinate).integrable (by norm_num)
  exact
    StatInference.ProbabilityTheory.durrett2019_theorem_3_10_7_allProjectionMean_zero_of_thetaProjectionMean_zero
      (Q := Q) (Z := Z)
      (StatInference.ProbabilityTheory.durrett2019_theorem_3_10_7_thetaProjectionMean_zero_of_coordinateMean_zero
        (Q := Q) (Z := Z) hZ_coordinate_integrable
        hZ_coordinate_mean_zero)

/--
Coordinatewise zero means for a finite-coordinate Gaussian limit imply
probability-notation mean zero for the pushed-forward vector law.

This is the Chapter 4 source-shape bridge from the coordinate displays
`E[Z_i] = 0` to `(Q.map Z)[id] = 0`.
-/
theorem
    vaart1998_z_map_mean_zero_of_coordinate_mean_zero_of_gaussian
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    [CompleteSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0) :
    (Q.map Z)[id] = 0 := by
  haveI : _root_.ProbabilityTheory.IsGaussian (Q.map Z) :=
    hZ_gaussian.isGaussian_map
  have hZ_memLp_law : MemLp id 2 (Q.map Z) :=
    _root_.ProbabilityTheory.IsGaussian.memLp_two_id
  have hZ_coordinate_integrable_law : ∀ coordinate : Idx,
      Integrable (fun z : Idx -> ℝ => z coordinate) (Q.map Z) :=
    fun coordinate =>
      (hZ_memLp_law.eval coordinate).integrable (by norm_num)
  change (∫ z, z ∂(Q.map Z)) = 0
  ext coordinate
  calc
    (∫ z, z ∂(Q.map Z)) coordinate =
        ∫ z, z coordinate ∂(Q.map Z) := by
          rw [MeasureTheory.eval_integral
            (f := fun z : Idx -> ℝ => z)
            hZ_coordinate_integrable_law coordinate]
    _ = ∫ ω, Z ω coordinate ∂Q := by
          simpa [Function.comp_def] using
            (integral_map hZ_gaussian.aemeasurable
              (f := fun z : Idx -> ℝ => z coordinate)
              ((continuous_apply coordinate).measurable.aestronglyMeasurable))
    _ = 0 := hZ_coordinate_mean_zero coordinate

/--
Coordinate covariance equality for a finite-coordinate Gaussian limit and the
observation law gives the projected variance source for every continuous
linear functional.
-/
theorem
    vaart1998_z_observation_projected_variance_of_coordinate_covariance_of_gaussian
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    [CompleteSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_observation_coordinate_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw) :
    ∀ L : StrongDual ℝ (Idx -> ℝ),
      _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        _root_.ProbabilityTheory.variance L observationLaw := by
  haveI : _root_.ProbabilityTheory.IsGaussian (Q.map Z) :=
    hZ_gaussian.isGaussian_map
  have hZ_memLp_law : MemLp id 2 (Q.map Z) :=
    _root_.ProbabilityTheory.IsGaussian.memLp_two_id
  have hObservation_memLp :
      MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw :=
    vaart1998_observationVector_memLp_of_coordinateMemLp
      (observationLaw := observationLaw) hObservation_coordinate_memLp
  have hObservation_law_memLp : MemLp id 2 observationLaw := by
    simpa [id] using hObservation_memLp
  have hZ_law_observation_coordinate_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun z : Idx -> ℝ => z i) (fun z : Idx -> ℝ => z j) (Q.map Z) =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw := by
    intro i j
    calc
      _root_.ProbabilityTheory.covariance
          (fun z : Idx -> ℝ => z i) (fun z : Idx -> ℝ => z j) (Q.map Z) =
        _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q := by
          simpa [Function.comp_def] using
            (_root_.ProbabilityTheory.covariance_map_fun
              (μ := Q) (Z := Z)
              (X := fun z : Idx -> ℝ => z i)
              (Y := fun z : Idx -> ℝ => z j)
              ((continuous_apply i).measurable.aestronglyMeasurable)
              ((continuous_apply j).measurable.aestronglyMeasurable)
              hZ_gaussian.aemeasurable)
      _ =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw := hZ_observation_coordinate_covariance i j
  have hZ_observation_covariance_bilin :
      ∀ L K : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L K =
          _root_.ProbabilityTheory.covarianceBilinDual observationLaw L K :=
    vaart1998_covarianceBilinDual_eq_of_law_coordinate_covariance
      (μ := Q.map Z) (ν := observationLaw)
      hZ_memLp_law hObservation_law_memLp
      hZ_law_observation_coordinate_covariance
  intro L
  exact
    (hZ_observation_covariance_bilin L L).trans
      (_root_.ProbabilityTheory.covarianceBilinDual_self_eq_variance
        hObservation_law_memLp L)

/--
Centered-product identities for a finite-coordinate Gaussian limit and the
centered observation law imply coordinate covariance equality.
-/
theorem
    vaart1998_z_observation_coordinate_covariance_of_centered_products
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_observation_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw := by
  haveI : _root_.ProbabilityTheory.IsGaussian (Q.map Z) :=
    hZ_gaussian.isGaussian_map
  have hZ_memLp_law : MemLp id 2 (Q.map Z) :=
    _root_.ProbabilityTheory.IsGaussian.memLp_two_id
  have hZ_memLp_sample : MemLp Z 2 Q := by
    simpa [Function.comp_def] using
      (MeasureTheory.memLp_map_measure_iff
        aestronglyMeasurable_id hZ_gaussian.aemeasurable).1 hZ_memLp_law
  have hZ_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun ω => Z ω coordinate) 2 Q := fun coordinate =>
    hZ_memLp_sample.eval coordinate
  let Gamma : Idx -> Idx -> ℝ := fun i j =>
    ∫ observation,
      (observation i - theta0 i) *
        (observation j - theta0 j) ∂observationLaw
  have hZ_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j := by
    intro i j
    simpa [Gamma] using hZ_observation_centered_product i j
  have hZ_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q =
        Gamma i j :=
    StatInference.ProbabilityTheory.durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProduct
      hZ_coordinate_memLp hZ_coordinate_mean_zero Gamma hZ_centered_product
  have hObservation_centered_product : ∀ i j : Idx,
      (∫ observation,
        ((fun observation : Idx -> ℝ => observation) observation i - theta0 i) *
          ((fun observation : Idx -> ℝ => observation) observation j - theta0 j)
          ∂observationLaw) =
        Gamma i j := by
    intro i j
    rfl
  have hObservation_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw =
        Gamma i j :=
    StatInference.ProbabilityTheory.durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
      theta0
      (fun coordinate => (hTheta0_coordinate_mean coordinate).symm)
      Gamma hObservation_centered_product
  intro i j
  exact (hZ_covariance i j).trans (hObservation_covariance i j).symm

/--
Mean zero under the pushed-forward Gaussian limit law gives mean zero for the
representative Gaussian limit variable.
-/
theorem
    vaart1998_z_sample_mean_zero_of_law_mean_zero_of_gaussian
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0) :
    (∫ ω, Z ω ∂Q) = 0 := by
  have hIntegral :
      (∫ ω, Z ω ∂Q) = ∫ z, z ∂(Q.map Z) := by
    simpa [Function.comp_def] using
      (integral_map hZ_gaussian.aemeasurable
        (f := fun z : Idx -> ℝ => z) aestronglyMeasurable_id).symm
  calc
    (∫ ω, Z ω ∂Q) = ∫ z, z ∂(Q.map Z) := hIntegral
    _ = 0 := hZ_law_mean_zero

/--
Centered-product identities under the pushed-forward Gaussian limit law give
centered-product identities for the representative Gaussian limit variable.
-/
theorem
    vaart1998_z_centered_product_of_law_centered_product_of_gaussian
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {Z : Ω' -> Idx -> ℝ}
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (Gamma : Idx -> Idx -> ℝ)
    (hZ_law_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) = Gamma i j) :
    ∀ i j : Idx, (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j := by
  intro i j
  have hIntegral :
      (∫ ω, Z ω i * Z ω j ∂Q) =
        ∫ z, z i * z j ∂(Q.map Z) := by
    simpa [Function.comp_def] using
      (integral_map hZ_gaussian.aemeasurable
        (f := fun z : Idx -> ℝ => z i * z j)
        (((continuous_apply i).mul (continuous_apply j)).measurable.aestronglyMeasurable)).symm
  exact hIntegral.trans (hZ_law_centered_product i j)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with the concrete sample-mean estimating map.

This wrapper fixes the estimating map to
`vaart1998_identityMeanObservationEstimatingMap`, so the affine display
`observationEstimatingMap observation theta = theta - observation` is
discharged by definitional equality.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpProjectedMeanVarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_projected_mean_zero : ∀ L : StrongDual ℝ (Idx -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_observation_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationCoordinateMeanMemLpProjectedMeanVarianceSource
      (Q := Q)
      (observationEstimatingMap :=
        vaart1998_identityMeanObservationEstimatingMap Idx)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_coordinate_mean hZ_gaussian
      hZ_projected_mean_zero hZ_observation_projected_variance
      (by
        intro observation theta
        rfl)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with the concrete sample-mean estimating map and coordinate
Gaussian-limit mean sources.

This wrapper replaces the all-dual projected mean-zero source by the
finite-coordinate source `∫ Z_i = 0` for every coordinate.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpCoordinateGaussianMeanVarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_observation_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hZ_projected_mean_zero : ∀ L : StrongDual ℝ (Idx -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0 :=
    vaart1998_z_projected_mean_zero_of_coordinate_mean_zero_of_gaussian
      (Q := Q) (Z := Z) hZ_gaussian hZ_coordinate_mean_zero
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpProjectedMeanVarianceSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_coordinate_mean hZ_gaussian
      hZ_projected_mean_zero hZ_observation_projected_variance

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with coordinate Gaussian mean and covariance sources.

This wrapper replaces the all-dual projected variance source by coordinate
covariance equality between the Gaussian limit and the observation law.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpCoordinateGaussianMeanCovarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_observation_coordinate_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hZ_observation_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw :=
    vaart1998_z_observation_projected_variance_of_coordinate_covariance_of_gaussian
      (Q := Q) (observationLaw := observationLaw) (Z := Z)
      hObservation_coordinate_memLp hZ_gaussian
      hZ_observation_coordinate_covariance
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpCoordinateGaussianMeanVarianceSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_coordinate_mean hZ_gaussian
      hZ_coordinate_mean_zero hZ_observation_projected_variance

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with centered-product covariance sources.

This wrapper replaces the coordinate covariance source by the textbook
centered-product identity
`E[Z_i Z_j] = E[(X_i - theta0_i) (X_j - theta0_j)]`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpCoordinateGaussianMeanCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_observation_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hZ_observation_coordinate_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw :=
    vaart1998_z_observation_coordinate_covariance_of_centered_products
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) hZ_gaussian hTheta0_coordinate_mean
      hZ_coordinate_mean_zero hZ_observation_centered_product
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpCoordinateGaussianMeanCovarianceSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_coordinate_mean hZ_gaussian
      hZ_coordinate_mean_zero hZ_observation_coordinate_covariance

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with a vector Gaussian mean-zero source.

This wrapper replaces coordinatewise Gaussian mean-zero assumptions by the
single vector source `∫ Z = 0`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpGaussianVectorMeanCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (∫ ω, Z ω ∂Q) = 0)
    (hZ_observation_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0 :=
    vaart1998_z_coordinate_mean_zero_of_vector_mean_zero_of_gaussian
      (Q := Q) (Z := Z) hZ_gaussian hZ_mean_zero
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpCoordinateGaussianMeanCenteredProductSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_coordinate_mean hZ_gaussian
      hZ_coordinate_mean_zero hZ_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with a pushed-forward Gaussian law mean-zero source.

This wrapper replaces the representative vector mean source `∫ Z = 0` by the
law-level source `∫ z, z d(Q.map Z) = 0`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpGaussianLawMeanCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_observation_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hZ_mean_zero : (∫ ω, Z ω ∂Q) = 0 :=
    vaart1998_z_sample_mean_zero_of_law_mean_zero_of_gaussian
      (Q := Q) (Z := Z) hZ_gaussian hZ_law_mean_zero
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpGaussianVectorMeanCenteredProductSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_coordinate_mean hZ_gaussian
      hZ_mean_zero hZ_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with pushed-forward Gaussian law mean-zero and centered-product
sources.

This wrapper replaces the representative centered-product source
`E[Z_i Z_j] = E[(X_i - theta0_i) (X_j - theta0_j)]` by the law-level source
`∫ z, z_i z_j d(Q.map Z) = E[(X_i - theta0_i) (X_j - theta0_j)]`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpGaussianLawMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  let Gamma : Idx -> Idx -> ℝ := fun i j =>
    ∫ observation,
      (observation i - theta0 i) *
        (observation j - theta0 j) ∂observationLaw
  have hZ_law_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) = Gamma i j := by
    intro i j
    simpa [Gamma] using hZ_law_observation_centered_product i j
  have hZ_observation_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw := by
    have hZ_centered_product : ∀ i j : Idx,
        (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j :=
      vaart1998_z_centered_product_of_law_centered_product_of_gaussian
        (Q := Q) (Z := Z) hZ_gaussian Gamma hZ_law_centered_product
    intro i j
    simpa [Gamma] using hZ_centered_product i j
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpGaussianLawMeanCenteredProductSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_coordinate_mean hZ_gaussian
      hZ_law_mean_zero hZ_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with a vector population mean source.

This wrapper replaces the coordinate population mean equations by the single
vector identity `theta0 = ∫ observation, observation d(observationLaw)`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapVectorMeanCoordinateMemLpGaussianLawMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw)
    (hTheta0_mean : theta0 =
      ∫ observation,
        observation ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hObservation_coordinate_integrable : ∀ coordinate : Idx,
      Integrable (fun observation : Idx -> ℝ => observation coordinate)
        observationLaw := fun coordinate =>
    (hObservation_coordinate_memLp coordinate).integrable (by norm_num)
  have hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw :=
    vaart1998_coordinateMean_of_observationMean_eq
      (observationLaw := observationLaw) (theta0 := theta0)
      hObservation_coordinate_integrable hTheta0_mean
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapCoordinateMeanMemLpGaussianLawMeanLawCenteredProductSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_coordinate_mean hZ_gaussian
      hZ_law_mean_zero hZ_law_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with vector population mean and vector `L²` observation sources.

This wrapper replaces coordinate observation `MemLp 2` assumptions by the
single vector source `MemLp observation 2`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapVectorMeanVectorMemLpGaussianLawMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_memLp :
      MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw)
    (hTheta0_mean : theta0 =
      ∫ observation,
        observation ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw :=
    vaart1998_coordinateMemLp_of_observationMemLp
      (observationLaw := observationLaw) hObservation_memLp
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapVectorMeanCoordinateMemLpGaussianLawMeanLawCenteredProductSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_coordinate_memLp hTheta0_mean hZ_gaussian
      hZ_law_mean_zero hZ_law_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with observation-law moment sources.

This wrapper replaces the concrete observation vector `MemLp` source by
`MemLp id 2 observationLaw` and accepts the population mean in the law-shaped
orientation `∫ observation, observation = theta0`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanObservationLawMemLpGaussianLawMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_law_memLp : MemLp id 2 observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hObservation_memLp :
      MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw :=
    vaart1998_observationMemLp_of_observationLawMemLp
      (observationLaw := observationLaw) hObservation_law_memLp
  have hTheta0_mean :
      theta0 =
        ∫ observation,
          observation ∂observationLaw :=
    vaart1998_theta0_mean_of_observationLaw_mean
      (observationLaw := observationLaw) (theta0 := theta0)
      hObservation_law_mean
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapVectorMeanVectorMemLpGaussianLawMeanLawCenteredProductSource
      (Q := Q)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_memLp hTheta0_mean hZ_gaussian hZ_law_mean_zero
      hZ_law_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with observation-law moment sources and a covariance-bilinear source.

This wrapper keeps the observation law mean and `L²` hypotheses in their
law-level form, keeps the Gaussian centering hypothesis on the pushed-forward
law, and delegates the covariance identification to the existing
covariance-bilinear route.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanObservationLawMemLpGaussianLawMeanCovarianceBilinSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_law_memLp : MemLp id 2 observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_observation_covariance_bilin :
      ∀ L K : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L K =
          _root_.ProbabilityTheory.covarianceBilinDual observationLaw L K) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hObservation_memLp :
      MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw :=
    vaart1998_observationMemLp_of_observationLawMemLp
      (observationLaw := observationLaw) hObservation_law_memLp
  have hTheta0_mean :
      theta0 =
        ∫ observation,
          observation ∂observationLaw :=
    vaart1998_theta0_mean_of_observationLaw_mean
      (observationLaw := observationLaw) (theta0 := theta0)
      hObservation_law_mean
  have hZ_mean_zero : (∫ ω, Z ω ∂Q) = 0 :=
    vaart1998_z_sample_mean_zero_of_law_mean_zero_of_gaussian
      (Q := Q) (Z := Z) hZ_gaussian hZ_law_mean_zero
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationCovarianceBilinSource
      (Q := Q)
      (observationEstimatingMap :=
        vaart1998_identityMeanObservationEstimatingMap Idx)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_memLp hTheta0_mean hZ_gaussian hZ_mean_zero
      hZ_observation_covariance_bilin
      (by intro observation theta; rfl)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with observation-law moment sources and projected variance sources.

This wrapper keeps the observation law mean and `L²` hypotheses in their
law-level form, keeps the Gaussian centering hypothesis on the pushed-forward
law, and uses the finite-coordinate CLT-style diagonal variance source for the
Gaussian covariance.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanObservationLawMemLpGaussianLawMeanDiagonalVarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_law_memLp : MemLp id 2 observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_observation_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hObservation_memLp :
      MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw :=
    vaart1998_observationMemLp_of_observationLawMemLp
      (observationLaw := observationLaw) hObservation_law_memLp
  have hTheta0_mean :
      theta0 =
        ∫ observation,
          observation ∂observationLaw :=
    vaart1998_theta0_mean_of_observationLaw_mean
      (observationLaw := observationLaw) (theta0 := theta0)
      hObservation_law_mean
  have hZ_mean_zero : (∫ ω, Z ω ∂Q) = 0 :=
    vaart1998_z_sample_mean_zero_of_law_mean_zero_of_gaussian
      (Q := Q) (Z := Z) hZ_gaussian hZ_law_mean_zero
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationDiagonalVarianceSource
      (Q := Q)
      (observationEstimatingMap :=
        vaart1998_identityMeanObservationEstimatingMap Idx)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_memLp hTheta0_mean hZ_gaussian hZ_mean_zero
      hZ_observation_projected_variance
      (by intro observation theta; rfl)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with observation-law moment sources and projected Gaussian sources.

This wrapper keeps the observation law mean and `L²` hypotheses in their
law-level form, fixes the estimating map to the textbook sample-mean map, and
uses projected mean-zero and projected variance sources for the Gaussian
limit.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanObservationLawMemLpProjectedMeanVarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (hObservation_law_memLp : MemLp id 2 observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_projected_mean_zero : ∀ L : StrongDual ℝ (Idx -> ℝ),
      (∫ ω, L (Z ω) ∂Q) = 0)
    (hZ_observation_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hObservation_memLp :
      MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw :=
    vaart1998_observationMemLp_of_observationLawMemLp
      (observationLaw := observationLaw) hObservation_law_memLp
  have hTheta0_mean :
      theta0 =
        ∫ observation,
          observation ∂observationLaw :=
    vaart1998_theta0_mean_of_observationLaw_mean
      (observationLaw := observationLaw) (theta0 := theta0)
      hObservation_law_mean
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationProjectedMeanVarianceSource
      (Q := Q)
      (observationEstimatingMap :=
        vaart1998_identityMeanObservationEstimatingMap Idx)
      (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)
      hObservation_memLp hTheta0_mean hZ_gaussian hZ_projected_mean_zero
      hZ_observation_projected_variance
      (by intro observation theta; rfl)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with source certificates for the observation law and Gaussian limit.

This wrapper packages the current live sample-mean route around two reusable
certificates: the finite-coordinate vector-law source certificate supplies
coordinate measurability and `L²` control of the observation law, while the
projected Gaussian source package supplies the remaining Gaussian limit
fields.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceProjectedGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (gaussianSource :
      Vaart1998SampleMeanProjectedGaussianSource
        (Q := Q) (observationLaw := observationLaw) (Z := Z)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanObservationLawMemLpProjectedMeanVarianceSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z)
      (Vaart1998FiniteCoordinateVectorLawSource.memLp_id
        (ν := observationLaw) observationSource)
      hObservation_law_mean gaussianSource.gaussian
      gaussianSource.projected_mean_zero gaussianSource.projected_variance

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with vector-law observation sources and finite-dimensional
CLT-style Gaussian source fields.

The Gaussian source fields match the covariance-table route used by the
finite-coordinate multivariate CLT: a Gaussian vector limit, pushed-forward law
mean zero, and equality of each projected Gaussian variance with the
observation-law projected variance.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceGaussianLawMeanDiagonalVarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceProjectedGaussianSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationSource hObservation_law_mean
      (Vaart1998SampleMeanProjectedGaussianSource.of_mapMeanZero_projectedVariance
        (Q := Q) (observationLaw := observationLaw) (Z := Z)
        hZ_gaussian hZ_law_mean_zero hZ_projected_variance)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with bundled observation-law source and finite-dimensional
CLT-style Gaussian source fields.

The observation source packages coordinate measurability, coordinate `L²`
control, and the observation-law mean identity for the current concrete
sample-mean route.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianLawMeanDiagonalVarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceGaussianLawMeanDiagonalVarianceSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationSource.vector_law observationSource.law_mean
      hZ_gaussian hZ_law_mean_zero hZ_projected_variance

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with bundled observation-law and CLT-style Gaussian source
certificates.

This wrapper is the smallest current sample-mean boundary: the observation
source packages the finite-coordinate law and target mean, while the Gaussian
source packages the limit Gaussian law, pushed-forward mean zero, and diagonal
projected variance identities.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (gaussianSource :
      Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource
        (Q := Q) (observationLaw := observationLaw) (Z := Z)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceProjectedGaussianSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationSource.vector_law observationSource.law_mean
      (Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource.projectedGaussianSource
        (Q := Q) (observationLaw := observationLaw) (Z := Z) gaussianSource)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with a Chapter 4 probability-notation Gaussian mean source.

This wrapper consumes `(Q.map Z)[id] = 0` directly and packages it into the
bundled sample-mean Gaussian source certificate.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanDiagonalVarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_projected_variance :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          _root_.ProbabilityTheory.variance L observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationSource
      (Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource.of_probabilityMeanZero_projectedVariance
        (Q := Q) (observationLaw := observationLaw) (Z := Z)
        hZ_gaussian hZ_mean_zero hZ_projected_variance)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with Chapter 4 canonical Gaussian mean/covariance source fields.

This wrapper consumes the Gaussian source package used by the finite-coordinate
Chapter 4 canonical covariance-table lane: `HasGaussianLaw Z Q`,
`(Q.map Z)[id] = 0`, and diagonal covariance displayed as `Var[L;
observationLaw]`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanCanonicalCovarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationSource
      (Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource.of_chapter4CanonicalMeanCovarianceSource
        (Q := Q) (observationLaw := observationLaw) (Z := Z)
        hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with Chapter 4-style observation and Gaussian source fields.

This wrapper consumes the finite-coordinate vector-law observation source and
the law-oriented population mean identity separately, then packages them as the
sample-mean observation source before applying the Chapter 4 canonical
Gaussian covariance wrapper.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceGaussianMapMeanCanonicalCovarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanCanonicalCovarianceSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z)
      (Vaart1998SampleMeanObservationLawSource.of_vectorLawMean
        (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
        observationVectorLawSource hObservation_law_mean)
      hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with Chapter 4-style coordinate mean, observation, and Gaussian
source fields.

This wrapper consumes the finite-coordinate vector-law observation source and
the coordinatewise population-mean identity used by the Chapter 4 canonical
moment-estimator lane, packages them as the sample-mean observation source,
and then applies the Chapter 4 canonical Gaussian covariance wrapper.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceGaussianMapMeanCanonicalCovarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanCanonicalCovarianceSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z)
      (Vaart1998SampleMeanObservationLawSource.of_vectorLawCoordinateMean
        (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
        observationVectorLawSource hObservation_coordinate_mean)
      hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint with a bundled Chapter 4 canonical source certificate.

This wrapper is the current narrowest sample-mean boundary: the source
certificate supplies the finite-coordinate observation vector law,
coordinatewise population means, Gaussian limit law, pushed-forward mean zero,
and canonical projected covariance display together.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapChapter4CanonicalSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (source : Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0) (Z := Z)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceGaussianMapMeanCanonicalCovarianceSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z)
      source.observation_vector_law source.observation_coordinate_mean
      source.gaussian source.gaussian_map_mean_zero
      source.covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint routed through the bundled Chapter 4 canonical source constructor.

This keeps older callers that already have the observation-law source package
and Chapter 4 canonical Gaussian mean/covariance fields on the newest bundled
sample-mean route.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceCanonicalGaussianToChapter4Source
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapChapter4CanonicalSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanChapter4CanonicalSource.of_observationSourceCanonicalGaussian
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationSource hZ_gaussian hZ_mean_zero
      hZ_covariance_observationLaw)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint routing separated vector-law and law-mean source fields through the
bundled Chapter 4 canonical source.

This is the direct bridge for callers that have not yet packaged their
observation assumptions as `Vaart1998SampleMeanObservationLawSource`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceCanonicalGaussianToChapter4Source
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceCanonicalGaussianToChapter4Source
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanObservationLawSource.of_vectorLawMean
      (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
      observationVectorLawSource hObservation_law_mean)
    hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint routing Chapter 4 coordinatewise population means through the bundled
Chapter 4 canonical source.

This is the direct bridge for Chapter 4 callers that state the target mean as
coordinatewise population moments.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceCanonicalGaussianToChapter4Source
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapChapter4CanonicalSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanChapter4CanonicalSource.of_vectorLawCoordinateMeanCanonicalGaussian
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationVectorLawSource hObservation_coordinate_mean
      hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint routing Chapter 4 coordinatewise population means and the bundled
sample-mean Gaussian source through the Chapter 4 canonical source.

This is the direct bridge for callers that already packaged the Gaussian law,
mean-zero, and diagonal projected variance fields as
`Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceGaussianSourceToChapter4Source
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (gaussianSource :
      Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource
        (Q := Q) (observationLaw := observationLaw) (Z := Z)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapChapter4CanonicalSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanChapter4CanonicalSource.of_vectorLawCoordinateMeanGaussianSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationVectorLawSource hObservation_coordinate_mean
      gaussianSource)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint routing Chapter 4 canonical Gaussian mean/covariance fields through
the bundled sample-mean Gaussian source.

This keeps callers source-shaped around the Chapter 4 displays
`(Q.map Z)[id] = 0` and
`covarianceBilinDual (Q.map Z) L L = Var[L; observationLaw]`, while the live
sample-mean route consumes the bundled Gaussian certificate internally.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceChapter4CanonicalMeanCovarianceToGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceGaussianSourceToChapter4Source
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z) observationVectorLawSource hObservation_coordinate_mean
    (Vaart1998SampleMeanGaussianLawMeanDiagonalVarianceSource.of_chapter4CanonicalMeanCovarianceSource
      (Q := Q) (observationLaw := observationLaw) (Z := Z)
      hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint routing law-level population means into the Chapter 4 canonical
Gaussian mean/covariance boundary.

This is the bridge for callers that have the finite-coordinate vector-law
source and the law-oriented mean identity `E[X] = theta0`, while the live
sample-mean route wants the coordinatewise Chapter 4 population-mean display.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceChapter4CanonicalMeanCovarianceToGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hCoordinate_integrable : ∀ coordinate : Idx,
      Integrable (fun observation : Idx -> ℝ => observation coordinate)
        observationLaw := fun coordinate =>
    (observationVectorLawSource.coordinate_memLp coordinate).integrable
      (by norm_num)
  have hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw := by
    funext coordinate
    exact
      vaart1998_coordinateMean_of_observationMean_eq
        (observationLaw := observationLaw) (theta0 := theta0)
        hCoordinate_integrable hObservation_law_mean.symm coordinate
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceChapter4CanonicalMeanCovarianceToGaussianSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationVectorLawSource hObservation_coordinate_mean
      hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for bundled observation-law sources and Chapter 4 canonical
Gaussian mean/covariance fields.

This is the smallest bundled observation-source caller for the current
sample-mean route: the observation certificate supplies both vector-law
control and the law-oriented target mean, while the Gaussian fields remain in
the Chapter 4 probability-notation shape.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceChapter4CanonicalMeanCovarianceToGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceChapter4CanonicalMeanCovarianceToGaussianSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z) observationSource.vector_law observationSource.law_mean
    hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for bundled observation-law sources, coordinatewise centered Gaussian
limits, and Chapter 4 canonical covariance fields.

This keeps the Gaussian mean hypothesis in the coordinate source shape
`E[Z_i] = 0` and derives the probability-notation vector mean
`(Q.map Z)[id] = 0` internally before feeding the current bundled
observation-source endpoint.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceCoordinateGaussianMeanChapter4CanonicalCovarianceToGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceChapter4CanonicalMeanCovarianceToGaussianSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z) observationSource hZ_gaussian
    (vaart1998_z_map_mean_zero_of_coordinate_mean_zero_of_gaussian
      (Q := Q) (Z := Z) hZ_gaussian hZ_coordinate_mean_zero)
    hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for Chapter 4 vector-law population-mean sources, coordinatewise
centered Gaussian limits, and Chapter 4 canonical covariance fields.

This is the direct source-shaped caller for Chapter 4 finite-coordinate
sample-mean applications: the finite-coordinate vector-law certificate and
coordinatewise population means are packaged as the bundled observation-law
source internally, while the Gaussian mean remains in coordinate form.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceCoordinateGaussianMeanChapter4CanonicalCovarianceToObservationSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw]) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceCoordinateGaussianMeanChapter4CanonicalCovarianceToGaussianSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanObservationLawSource.of_vectorLawCoordinateMean
      (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
      observationVectorLawSource hObservation_coordinate_mean)
    hZ_gaussian hZ_coordinate_mean_zero hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for Chapter 4 vector-law population-mean sources, coordinatewise
centered Gaussian limits, and coordinate covariance fields.

This replaces the all-dual Chapter 4 canonical covariance display by the
coordinate covariance table naturally produced by finite-dimensional CLT
callers.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceCoordinateGaussianMeanCoordinateCovarianceToChapter4CanonicalCovariance
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_observation_coordinate_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hObservation_coordinate_memLp : ∀ coordinate : Idx,
      MemLp (fun observation : Idx -> ℝ => observation coordinate) 2
        observationLaw :=
    observationVectorLawSource.coordinate_memLp
  have hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw] := by
    intro L
    simpa using
      (vaart1998_z_observation_projected_variance_of_coordinate_covariance_of_gaussian
        (Q := Q) (observationLaw := observationLaw) (Z := Z)
        hObservation_coordinate_memLp hZ_gaussian
        hZ_observation_coordinate_covariance L)
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceCoordinateGaussianMeanChapter4CanonicalCovarianceToObservationSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationVectorLawSource hObservation_coordinate_mean
      hZ_gaussian hZ_coordinate_mean_zero hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for Chapter 4 vector-law population-mean sources, coordinatewise
centered Gaussian limits, and centered-product covariance fields.

This is the textbook covariance boundary: callers may state
`E[Z_i Z_j] = E[(X_i - theta0_i) (X_j - theta0_j)]`, and the coordinate
covariance table is derived internally before feeding the coordinate-covariance
sample-mean endpoint.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceCoordinateGaussianMeanCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0)
    (hZ_observation_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hTheta0_coordinate_mean : ∀ coordinate : Idx,
      theta0 coordinate =
        ∫ observation,
          observation coordinate ∂observationLaw := by
    intro coordinate
    simpa using congrFun hObservation_coordinate_mean coordinate
  have hZ_observation_coordinate_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw :=
    vaart1998_z_observation_coordinate_covariance_of_centered_products
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) hZ_gaussian hTheta0_coordinate_mean
      hZ_coordinate_mean_zero hZ_observation_centered_product
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceCoordinateGaussianMeanCoordinateCovarianceToChapter4CanonicalCovariance
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationVectorLawSource hObservation_coordinate_mean
      hZ_gaussian hZ_coordinate_mean_zero
      hZ_observation_coordinate_covariance

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for Chapter 4 vector-law population-mean sources and law-level
Gaussian mean/centered-product fields.

This keeps the Gaussian source fields under the pushed-forward law `Q.map Z`:
the representative coordinate mean-zero and centered-product displays are
derived internally before feeding the centered-product endpoint.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceGaussianLawMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hZ_mean_zero : (∫ ω, Z ω ∂Q) = 0 :=
    vaart1998_z_sample_mean_zero_of_law_mean_zero_of_gaussian
      (Q := Q) (Z := Z) hZ_gaussian hZ_law_mean_zero
  have hZ_coordinate_mean_zero : ∀ coordinate : Idx,
      (∫ ω, Z ω coordinate ∂Q) = 0 :=
    vaart1998_z_coordinate_mean_zero_of_vector_mean_zero_of_gaussian
      (Q := Q) (Z := Z) hZ_gaussian hZ_mean_zero
  let Gamma : Idx -> Idx -> ℝ := fun i j =>
    ∫ observation,
      (observation i - theta0 i) *
        (observation j - theta0 j) ∂observationLaw
  have hZ_law_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) = Gamma i j := by
    intro i j
    simpa [Gamma] using hZ_law_observation_centered_product i j
  have hZ_observation_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw := by
    have hZ_centered_product : ∀ i j : Idx,
        (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j :=
      vaart1998_z_centered_product_of_law_centered_product_of_gaussian
        (Q := Q) (Z := Z) hZ_gaussian Gamma hZ_law_centered_product
    intro i j
    simpa [Gamma] using hZ_centered_product i j
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceCoordinateGaussianMeanCenteredProductSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationVectorLawSource hObservation_coordinate_mean
      hZ_gaussian hZ_coordinate_mean_zero
      hZ_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for Chapter 4 vector-law population-mean sources, probability-notation
Gaussian map mean zero, and law-level centered-product fields.

This is the Chapter 4 notation-shaped version of the pushed-forward law
endpoint: `(Q.map Z)[id] = 0` is converted internally to the Bochner integral
law mean used by the previous wrapper.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceGaussianMapMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_map_mean_zero : (Q.map Z)[id] = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceGaussianLawMeanLawCenteredProductSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z) observationVectorLawSource hObservation_coordinate_mean
    hZ_gaussian
    (vaart1998_finiteCoordinateIntegralMapMean_eq_zero_of_map_mean_zero
      (Q := Q) (Z := Z) hZ_map_mean_zero)
    hZ_law_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for bundled observation-law sources, probability-notation Gaussian
map mean zero, and law-level centered-product fields.

The bundled observation source supplies the finite-coordinate vector-law
certificate and the law-oriented population mean; this wrapper derives the
coordinatewise Chapter 4 mean display internally before feeding the current
law-centered-product endpoint.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_map_mean_zero : (Q.map Z)[id] = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q := by
  have hCoordinate_integrable : ∀ coordinate : Idx,
      Integrable (fun observation : Idx -> ℝ => observation coordinate)
        observationLaw := fun coordinate =>
    (observationSource.vector_law.coordinate_memLp coordinate).integrable
      (by norm_num)
  have hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw := by
    funext coordinate
    exact
      vaart1998_coordinateMean_of_observationMean_eq
        (observationLaw := observationLaw) (theta0 := theta0)
        hCoordinate_integrable observationSource.law_mean.symm coordinate
  exact
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationCoordinateMeanVectorLawSourceGaussianMapMeanLawCenteredProductSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationSource.vector_law hObservation_coordinate_mean
      hZ_gaussian hZ_map_mean_zero hZ_law_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for separated vector-law and law-oriented population-mean sources,
probability-notation Gaussian map mean zero, and law-level centered products.

This is the unbundled observation-law handoff for callers that already have
the finite-coordinate vector-law certificate and the vector population mean
identity, but have not packaged them as
`Vaart1998SampleMeanObservationLawSource`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceGaussianMapMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_map_mean_zero : (Q.map Z)[id] = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanLawCenteredProductSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanObservationLawSource.of_vectorLawMean
      (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
      observationVectorLawSource hObservation_law_mean)
    hZ_gaussian hZ_map_mean_zero hZ_law_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for bundled observation-law and law-centered-product Gaussian source
certificates.

This is the smallest current source-package boundary for the textbook
finite-coordinate sample mean: observation assumptions and Gaussian/product
assumptions are both bundled before feeding the live map-mean/product route.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanLawCenteredProductGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (gaussianProductSource :
      Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource
        (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
        (Z := Z)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanLawCenteredProductSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z) observationSource gaussianProductSource.gaussian
    gaussianProductSource.gaussian_map_mean_zero
    gaussianProductSource.law_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for separated observation fields and a bundled law-centered-product
Gaussian source certificate.

This is the unbundled observation-law companion to
`...ObservationSourceGaussianMapMeanLawCenteredProductGaussianSource`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceGaussianMapMeanLawCenteredProductGaussianSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (gaussianProductSource :
      Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource
        (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
        (Z := Z)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanLawCenteredProductGaussianSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanObservationLawSource.of_vectorLawMean
      (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
      observationVectorLawSource hObservation_law_mean)
    gaussianProductSource

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for a bundled observation-law source and explicit pushed-forward
law-mean/law-centered-product Gaussian fields.

This wrapper keeps callers on the older explicit Bochner law-mean notation
while internally packaging those Gaussian/product fields as
`Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource`.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianLawMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationSource :
      Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanLawCenteredProductGaussianSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z) observationSource
    (Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource.of_lawMeanLawCenteredProduct
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) hZ_gaussian hZ_law_mean_zero
      hZ_law_observation_centered_product)

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for separated vector-law/law-mean observation fields and explicit
pushed-forward law-mean/law-centered-product Gaussian fields.

This is the fully law-oriented unbundled handoff: both observation assumptions
and Gaussian/product assumptions are packaged internally before feeding the
current bundled-source endpoint.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationLawMeanVectorLawSourceGaussianLawMeanLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hObservation_law_mean :
      (∫ observation,
        observation ∂observationLaw) = theta0)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_law_mean_zero : (∫ z, z ∂(Q.map Z)) = 0)
    (hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianLawMeanLawCenteredProductSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanObservationLawSource.of_vectorLawMean
      (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
      observationVectorLawSource hObservation_law_mean)
    hZ_gaussian hZ_law_mean_zero hZ_law_observation_centered_product

/--
The bundled Chapter 4 canonical sample-mean source supplies the bundled
observation-law source used by the law-centered-product endpoint.
-/
theorem Vaart1998SampleMeanObservationLawSource.of_chapter4CanonicalSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (source : Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z)) :
    Vaart1998SampleMeanObservationLawSource Idx observationLaw theta0 :=
  Vaart1998SampleMeanObservationLawSource.of_vectorLawCoordinateMean
    (Idx := Idx) (observationLaw := observationLaw) (theta0 := theta0)
    source.observation_vector_law source.observation_coordinate_mean

/--
The bundled Chapter 4 canonical sample-mean source supplies the law-level
Gaussian/product package used by the current explicit-law endpoint.

The proof polarizes the Chapter 4 diagonal covariance display, recovers
coordinate covariance equality, converts it to representative Gaussian
centered products, and finally pushes those products to `Q.map Z`.
-/
theorem
    Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource.of_chapter4CanonicalSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    [CompleteSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (source : Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z)) :
    Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) := by
  have hObservation_memLp :
      MemLp (fun observation : Idx -> ℝ => observation) 2 observationLaw :=
    Vaart1998FiniteCoordinateVectorLawSource.memLp_id
      (ν := observationLaw) source.observation_vector_law
  have hObservation_law_memLp : MemLp id 2 observationLaw := by
    simpa [id] using hObservation_memLp
  have hZ_observation_covariance_bilin :
      ∀ L K : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L K =
          _root_.ProbabilityTheory.covarianceBilinDual observationLaw L K :=
    vaart1998_covarianceBilinDual_eq_of_diagonal_variance
      (μ := Q.map Z) (ν := observationLaw) hObservation_law_memLp
      (by
        intro L
        simpa using source.covariance_observationLaw L)
  have hZ_observation_coordinate_covariance : ∀ i j : Idx,
      _root_.ProbabilityTheory.covariance
          (fun ω => Z ω i) (fun ω => Z ω j) Q =
        _root_.ProbabilityTheory.covariance
          (fun observation : Idx -> ℝ => observation i)
          (fun observation : Idx -> ℝ => observation j)
          observationLaw :=
    vaart1998_z_observation_coordinateCovariance_of_covarianceBilinDual
      (observationLaw := observationLaw) (Z := Z)
      hObservation_memLp source.gaussian hZ_observation_covariance_bilin
  have hZ_law_mean_zero :
      (∫ z, z ∂(Q.map Z)) = 0 :=
    vaart1998_finiteCoordinateIntegralMapMean_eq_zero_of_map_mean_zero
      (Q := Q) (Z := Z) source.gaussian_map_mean_zero
  have hZ_mean_zero :
      (∫ ω, Z ω ∂Q) = 0 :=
    vaart1998_z_sample_mean_zero_of_law_mean_zero_of_gaussian
      (Q := Q) (Z := Z) source.gaussian hZ_law_mean_zero
  let Gamma : Idx -> Idx -> ℝ := fun i j =>
    _root_.ProbabilityTheory.covariance
      (fun observation : Idx -> ℝ => observation i)
      (fun observation : Idx -> ℝ => observation j)
      observationLaw
  have hZ_centered_product : ∀ i j : Idx,
      (∫ ω, Z ω i * Z ω j ∂Q) = Gamma i j :=
    vaart1998_z_centeredProduct_of_vectorMeanZero_coordinateCovariance
      (Q := Q) (Z := Z) source.gaussian hZ_mean_zero Gamma
      (by
        intro i j
        simpa [Gamma] using hZ_observation_coordinate_covariance i j)
  have hObservation_coordinate_mean : ∀ coordinate : Idx,
      (∫ observation, observation coordinate ∂observationLaw) =
        theta0 coordinate := by
    intro coordinate
    exact (congrFun source.observation_coordinate_mean coordinate).symm
  have hObservation_covariance_centered_product : ∀ i j : Idx,
      Gamma i j =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw := by
    intro i j
    let GammaCentered : Idx -> Idx -> ℝ := fun i j =>
      ∫ observation,
        (observation i - theta0 i) *
          (observation j - theta0 j) ∂observationLaw
    have hCovariance :
        _root_.ProbabilityTheory.covariance
            (fun observation : Idx -> ℝ => observation i)
            (fun observation : Idx -> ℝ => observation j)
            observationLaw =
          GammaCentered i j :=
      StatInference.ProbabilityTheory.durrett2019_theorem_3_10_7_coordinateCovariance_eq_of_centeredProductSubMean
        theta0 hObservation_coordinate_mean GammaCentered
        (by intro i j; rfl) i j
    simpa [Gamma, GammaCentered] using hCovariance
  have hZ_law_observation_centered_product : ∀ i j : Idx,
      (∫ z, z i * z j ∂(Q.map Z)) =
        ∫ observation,
          (observation i - theta0 i) *
            (observation j - theta0 j) ∂observationLaw := by
    intro i j
    have hIntegral :
        (∫ ω, Z ω i * Z ω j ∂Q) =
          ∫ z, z i * z j ∂(Q.map Z) := by
      simpa [Function.comp_def] using
        (integral_map source.gaussian.aemeasurable
          (f := fun z : Idx -> ℝ => z i * z j)
          (((continuous_apply i).mul
            (continuous_apply j)).measurable.aestronglyMeasurable)).symm
    exact hIntegral.symm.trans
      ((hZ_centered_product i j).trans
        (hObservation_covariance_centered_product i j))
  exact
    Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource.of_lawMeanLawCenteredProduct
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) source.gaussian hZ_law_mean_zero
      hZ_law_observation_centered_product

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint routed from the existing bundled Chapter 4 canonical source through
the current law-centered-product source boundary.

This keeps Chapter 4 callers on the canonical mean/covariance certificate while
making the newest explicit-law Theorem 5.41 endpoint the actual consumer.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapChapter4CanonicalLawCenteredProductSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (source : Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z)) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapObservationSourceGaussianMapMeanLawCenteredProductGaussianSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanObservationLawSource.of_chapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) source)
    (Vaart1998SampleMeanGaussianMapMeanLawCenteredProductSource.of_chapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) source)

/--
Chapter 4 canonical mean/vector-law covariance fields form the bundled
sample-mean canonical source.

This is the source shape produced by the Chapter 4 finite-coordinate moment
lane: a vector-law certificate, the Gaussian map-mean display, and the
diagonal projected covariance display against the common observation law.
-/
theorem
    Vaart1998SampleMeanChapter4CanonicalSource.of_canonicalMeanVectorLawCovarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [MeasurableSpace Ω']
    [MeasurableSpace (Idx -> ℝ)]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)]
    [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw])
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw) :
    Vaart1998SampleMeanChapter4CanonicalSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) :=
  Vaart1998SampleMeanChapter4CanonicalSource.of_vectorLawCoordinateMeanCanonicalGaussian
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z) observationVectorLawSource hObservation_coordinate_mean
    hZ_gaussian hZ_mean_zero hZ_covariance_observationLaw

/--
van der Vaart 1998, Theorem 5.41, positive-sample identity sample-mean
endpoint for the Chapter 4 canonical mean/vector-law covariance source shape.

This composes the existing Chapter 4 finite-coordinate source boundary with
the newest law-centered-product sample-mean endpoint.
-/
theorem
    vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapChapter4CanonicalMeanVectorLawCovarianceSource
    {Ω' Idx : Type*} [Fintype Idx] [DecidableEq Idx]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Idx -> ℝ)]
    [SecondCountableTopology (Idx -> ℝ)] [BorelSpace (Idx -> ℝ)]
    [OpensMeasurableSpace (Idx -> ℝ)] [CompleteSpace (Idx -> ℝ)]
    [MeasurableSub₂ (Idx -> ℝ)] [MeasurableSMul₂ ℝ (Idx -> ℝ)]
    [PseudoMetricSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology (Idx × Idx -> ℝ)]
    [BorelSpace (Idx × Idx -> ℝ)]
    [OpensMeasurableSpace (Idx × Idx -> ℝ)]
    [CompleteSpace (Idx × Idx -> ℝ)]
    [SecondCountableTopology ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [OpensMeasurableSpace ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableAdd₂ ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    [MeasurableConstSMul ℝ
      ((Idx -> ℝ) →L[ℝ] (Idx -> ℝ) →L[ℝ] (Idx -> ℝ))]
    {observationLaw : Measure (Idx -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    {theta0 : Idx -> ℝ}
    {Z : Ω' -> Idx -> ℝ}
    (observationVectorLawSource :
      Vaart1998FiniteCoordinateVectorLawSource Idx observationLaw)
    (hZ_gaussian : _root_.ProbabilityTheory.HasGaussianLaw Z Q)
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covariance_observationLaw :
      ∀ L : StrongDual ℝ (Idx -> ℝ),
        _root_.ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
          Var[L; observationLaw])
    (hObservation_coordinate_mean :
      theta0 =
        fun coordinate : Idx =>
          ∫ observation,
            observation coordinate ∂observationLaw) :
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √((n + 1 : ℕ) : ℝ) •
          (vaart1998PositiveCommonObservationCoreInverseEstimator
              (vaart1998_identityCommonObservationCoreInverse Idx)
              (vaart1998_negativeObservationOffset Idx) n sample -
            theta0))
      atTop
      (fun ω =>
        (-(ContinuousLinearMap.id ℝ (Idx -> ℝ)) :
          (Idx -> ℝ) →L[ℝ] (Idx -> ℝ)) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => observationLaw)) Q :=
  vaart1998_theorem_5_41_positiveSample_identityMeanObservationConcreteEstimatingMapChapter4CanonicalLawCenteredProductSource
    (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
    (Z := Z)
    (Vaart1998SampleMeanChapter4CanonicalSource.of_canonicalMeanVectorLawCovarianceSource
      (Q := Q) (observationLaw := observationLaw) (theta0 := theta0)
      (Z := Z) observationVectorLawSource hZ_gaussian hZ_mean_zero
      hZ_covariance_observationLaw hObservation_coordinate_mean)

end AsymptoticStatistics
end StatInference
