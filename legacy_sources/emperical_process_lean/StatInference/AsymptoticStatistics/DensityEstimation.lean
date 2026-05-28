import StatInference.AsymptoticStatistics.Bootstrap

/-!
# van der Vaart 1998 Chapter 24 nonparametric density estimation

This module opens the Chapter 24 lane of A. W. van der Vaart,
*Asymptotic Statistics* (1998).  The first source package records the
nonparametric density-estimation problem, the kernel estimator display, the
component-kernel smoothing display, and the mean integrated square error
decomposition.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal Real Topology

/-- Parametric normal plug-in density display used as the foil for kernel
density estimation at the start of Chapter 24.2. -/
def vaart1998_normalPlugInDensityDisplay
    (sampleMean sampleScale x : ℝ) : ℝ :=
  (sampleScale * Real.sqrt (2 * Real.pi))⁻¹ *
    Real.exp (-(1 / 2 : ℝ) * ((x - sampleMean) ^ 2 / sampleScale ^ 2))

/-- Kernel-density estimator display
`hat f(x) = n^{-1} sum_i h^{-1} K((x-X_i)/h)`. -/
def vaart1998_kernelDensityEstimator
    (kernel : ℝ -> ℝ) {n : ℕ} (observation : Fin n -> ℝ)
    (bandwidth x : ℝ) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i : Fin n, bandwidth⁻¹ * kernel ((x - observation i) / bandwidth)

/-- Component "small mountain" contributed by one observation. -/
def vaart1998_kernelDensityComponent
    (kernel : ℝ -> ℝ) (n : ℕ) (observation bandwidth x : ℝ) :
    ℝ :=
  (n : ℝ)⁻¹ *
    (bandwidth⁻¹ * kernel ((x - observation) / bandwidth))

/-- Mean integrated square error decomposition display. -/
def vaart1998_miseDecompositionRHS
    (integratedVariance integratedSquaredBias : ℝ) : ℝ :=
  integratedVariance + integratedSquaredBias

/-- Pointwise squared error of a density estimator. -/
def vaart1998_densityPointwiseSquaredError
    (densityEstimator trueDensity : ℝ -> ℝ) (x : ℝ) : ℝ :=
  (densityEstimator x - trueDensity x) ^ 2

/-- Deterministic scalar `O(rate_n)` wrapper for integrated MISE terms. -/
def vaart1998_deterministicOrderAtRate
    (quantity rate : ℕ -> ℝ) : Prop :=
  ∃ C : ℝ, 0 < C ∧ ∀ᶠ n in atTop, |quantity n| ≤ C * rate n

/-- Deterministic asymptotic equivalence wrapper, used for `a_n ~ b_n`. -/
def vaart1998_asymptoticallyEquivalentRates
    (left right : ℕ -> ℝ) : Prop :=
  Tendsto (fun n : ℕ => left n / right n) atTop (𝓝 1)

/-- Variance-order display `(n h)^{-1}`. -/
def vaart1998_kernelVarianceRateTerm (n : ℕ) (bandwidth : ℝ) : ℝ :=
  ((n : ℝ) * bandwidth)⁻¹

/-- Squared-bias-order display `h^4`. -/
def vaart1998_kernelSquaredBiasRateTerm (bandwidth : ℝ) : ℝ :=
  bandwidth ^ 4

/-- MISE rate envelope `(n h)^{-1} + h^4`. -/
def vaart1998_kernelMISERateEnvelope (n : ℕ) (bandwidth : ℝ) : ℝ :=
  vaart1998_kernelVarianceRateTerm n bandwidth +
    vaart1998_kernelSquaredBiasRateTerm bandwidth

/-- Balance condition `(n h)^{-1} ~ h^4`. -/
def vaart1998_kernelRateBalance (bandwidth : ℕ -> ℝ) : Prop :=
  vaart1998_asymptoticallyEquivalentRates
    (fun n => vaart1998_kernelVarianceRateTerm n (bandwidth n))
    (fun n => vaart1998_kernelSquaredBiasRateTerm (bandwidth n))

/-- Optimal bandwidth display `h ~ n^{-1/5}`. -/
def vaart1998_kernelOptimalBandwidthDisplay (n : ℕ) : ℝ :=
  Real.rpow (n : ℝ) (-(1 / 5 : ℝ))

/-- Optimal MISE display `n^{-4/5}`. -/
def vaart1998_kernelOptimalMISEDisplay (n : ℕ) : ℝ :=
  Real.rpow (n : ℝ) (-(4 / 5 : ℝ))

/-- Bias display before the change of variables. -/
def vaart1998_kernelBiasInitialIntegralDisplay
    (kernel trueDensity : ℝ -> ℝ) (bandwidth x : ℝ) : ℝ :=
  (∫ t : ℝ,
    bandwidth⁻¹ * kernel ((x - t) / bandwidth) * trueDensity t) -
      trueDensity x

/-- Bias display after the change of variables `y=(x-t)/h`. -/
def vaart1998_kernelBiasChangeOfVariablesDisplay
    (kernel trueDensity : ℝ -> ℝ) (bandwidth x : ℝ) : ℝ :=
  ∫ y : ℝ, kernel y * (trueDensity (x - bandwidth * y) -
    trueDensity x)

/-- Kernel second-moment display `∫ y^2 K(y) dy`. -/
def vaart1998_kernelSecondMomentDisplay (kernel : ℝ -> ℝ) : ℝ :=
  ∫ y : ℝ, y ^ 2 * kernel y

/-- Informal Taylor-leading bias term
`(∫ y^2 K(y)dy) * (1/2) h^2 f''(x)`. -/
def vaart1998_kernelBiasTaylorLeadingTermDisplay
    (kernel trueDensitySecondDerivative : ℝ -> ℝ)
    (bandwidth x : ℝ) : ℝ :=
  vaart1998_kernelSecondMomentDisplay kernel *
    ((1 / 2 : ℝ) * bandwidth ^ 2 *
      trueDensitySecondDerivative x)

/-- Kernel first-moment display `∫ y K(y) dy`. -/
def vaart1998_kernelFirstMomentDisplay (kernel : ℝ -> ℝ) : ℝ :=
  ∫ y : ℝ, y * kernel y

/-- Kernel squared-integral display `∫ K(y)^2 dy`. -/
def vaart1998_kernelSquaredIntegralDisplay (kernel : ℝ -> ℝ) : ℝ :=
  ∫ y : ℝ, kernel y ^ 2

/-- Square-integral display for the second derivative of `f`. -/
def vaart1998_densitySecondDerivativeSquareIntegralDisplay
    (trueDensitySecondDerivative : ℝ -> ℝ) : ℝ :=
  ∫ x : ℝ, |trueDensitySecondDerivative x| ^ 2

/-- The displayed Theorem 24.1 MISE upper-bound right-hand side. -/
def vaart1998_kernelMISEBoundRHS
    (constant : ℝ) (n : ℕ) (bandwidth : ℝ) : ℝ :=
  constant * vaart1998_kernelMISERateEnvelope n bandwidth

/-- Theorem 24.1 small-positive-bandwidth bound wrapper. -/
def vaart1998_kernelMISEBoundForSmallBandwidth
    (meanIntegratedSquareErrorAtBandwidth : ℕ -> ℝ -> ℝ)
    (constant : ℝ) : Prop :=
  0 < constant ∧
    ∀ᶠ bandwidth in 𝓝[>] (0 : ℝ),
      ∀ n : ℕ,
        meanIntegratedSquareErrorAtBandwidth n bandwidth ≤
          vaart1998_kernelMISEBoundRHS constant n bandwidth

theorem vaart1998_normalPlugInDensityDisplay_def
    (sampleMean sampleScale x : ℝ) :
    vaart1998_normalPlugInDensityDisplay sampleMean sampleScale x =
      (sampleScale * Real.sqrt (2 * Real.pi))⁻¹ *
        Real.exp (-(1 / 2 : ℝ) * ((x - sampleMean) ^ 2 /
          sampleScale ^ 2)) :=
  rfl

theorem vaart1998_kernelDensityEstimator_def
    (kernel : ℝ -> ℝ) {n : ℕ} (observation : Fin n -> ℝ)
    (bandwidth x : ℝ) :
    vaart1998_kernelDensityEstimator kernel observation bandwidth x =
      (n : ℝ)⁻¹ *
        ∑ i : Fin n,
          bandwidth⁻¹ * kernel ((x - observation i) / bandwidth) :=
  rfl

theorem vaart1998_kernelDensityComponent_def
    (kernel : ℝ -> ℝ) (n : ℕ) (observation bandwidth x : ℝ) :
    vaart1998_kernelDensityComponent kernel n observation bandwidth x =
      (n : ℝ)⁻¹ *
        (bandwidth⁻¹ * kernel ((x - observation) / bandwidth)) :=
  rfl

theorem vaart1998_miseDecompositionRHS_def
    (integratedVariance integratedSquaredBias : ℝ) :
    vaart1998_miseDecompositionRHS integratedVariance
        integratedSquaredBias =
      integratedVariance + integratedSquaredBias :=
  rfl

theorem vaart1998_densityPointwiseSquaredError_def
    (densityEstimator trueDensity : ℝ -> ℝ) (x : ℝ) :
    vaart1998_densityPointwiseSquaredError densityEstimator trueDensity x =
      (densityEstimator x - trueDensity x) ^ 2 :=
  rfl

theorem vaart1998_deterministicOrderAtRate_def
    (quantity rate : ℕ -> ℝ) :
    vaart1998_deterministicOrderAtRate quantity rate =
      (∃ C : ℝ, 0 < C ∧
        ∀ᶠ n in atTop, |quantity n| ≤ C * rate n) :=
  rfl

theorem vaart1998_asymptoticallyEquivalentRates_def
    (left right : ℕ -> ℝ) :
    vaart1998_asymptoticallyEquivalentRates left right =
      Tendsto (fun n : ℕ => left n / right n) atTop (𝓝 1) :=
  rfl

theorem vaart1998_kernelVarianceRateTerm_def
    (n : ℕ) (bandwidth : ℝ) :
    vaart1998_kernelVarianceRateTerm n bandwidth =
      ((n : ℝ) * bandwidth)⁻¹ :=
  rfl

theorem vaart1998_kernelSquaredBiasRateTerm_def
    (bandwidth : ℝ) :
    vaart1998_kernelSquaredBiasRateTerm bandwidth = bandwidth ^ 4 :=
  rfl

theorem vaart1998_kernelMISERateEnvelope_def
    (n : ℕ) (bandwidth : ℝ) :
    vaart1998_kernelMISERateEnvelope n bandwidth =
      vaart1998_kernelVarianceRateTerm n bandwidth +
        vaart1998_kernelSquaredBiasRateTerm bandwidth :=
  rfl

theorem vaart1998_kernelRateBalance_def (bandwidth : ℕ -> ℝ) :
    vaart1998_kernelRateBalance bandwidth =
      vaart1998_asymptoticallyEquivalentRates
        (fun n => vaart1998_kernelVarianceRateTerm n (bandwidth n))
        (fun n => vaart1998_kernelSquaredBiasRateTerm (bandwidth n)) :=
  rfl

theorem vaart1998_kernelOptimalBandwidthDisplay_def (n : ℕ) :
    vaart1998_kernelOptimalBandwidthDisplay n =
      Real.rpow (n : ℝ) (-(1 / 5 : ℝ)) :=
  rfl

theorem vaart1998_kernelOptimalMISEDisplay_def (n : ℕ) :
    vaart1998_kernelOptimalMISEDisplay n =
      Real.rpow (n : ℝ) (-(4 / 5 : ℝ)) :=
  rfl

theorem vaart1998_kernelBiasInitialIntegralDisplay_def
    (kernel trueDensity : ℝ -> ℝ) (bandwidth x : ℝ) :
    vaart1998_kernelBiasInitialIntegralDisplay
        kernel trueDensity bandwidth x =
      (∫ t : ℝ,
        bandwidth⁻¹ * kernel ((x - t) / bandwidth) *
          trueDensity t) - trueDensity x :=
  rfl

theorem vaart1998_kernelBiasChangeOfVariablesDisplay_def
    (kernel trueDensity : ℝ -> ℝ) (bandwidth x : ℝ) :
    vaart1998_kernelBiasChangeOfVariablesDisplay
        kernel trueDensity bandwidth x =
      ∫ y : ℝ, kernel y * (trueDensity (x - bandwidth * y) -
        trueDensity x) :=
  rfl

theorem vaart1998_kernelSecondMomentDisplay_def
    (kernel : ℝ -> ℝ) :
    vaart1998_kernelSecondMomentDisplay kernel =
      ∫ y : ℝ, y ^ 2 * kernel y :=
  rfl

theorem vaart1998_kernelBiasTaylorLeadingTermDisplay_def
    (kernel trueDensitySecondDerivative : ℝ -> ℝ)
    (bandwidth x : ℝ) :
    vaart1998_kernelBiasTaylorLeadingTermDisplay
        kernel trueDensitySecondDerivative bandwidth x =
      vaart1998_kernelSecondMomentDisplay kernel *
        ((1 / 2 : ℝ) * bandwidth ^ 2 *
          trueDensitySecondDerivative x) :=
  rfl

theorem vaart1998_kernelFirstMomentDisplay_def
    (kernel : ℝ -> ℝ) :
    vaart1998_kernelFirstMomentDisplay kernel =
      ∫ y : ℝ, y * kernel y :=
  rfl

theorem vaart1998_kernelSquaredIntegralDisplay_def
    (kernel : ℝ -> ℝ) :
    vaart1998_kernelSquaredIntegralDisplay kernel =
      ∫ y : ℝ, kernel y ^ 2 :=
  rfl

theorem vaart1998_densitySecondDerivativeSquareIntegralDisplay_def
    (trueDensitySecondDerivative : ℝ -> ℝ) :
    vaart1998_densitySecondDerivativeSquareIntegralDisplay
        trueDensitySecondDerivative =
      ∫ x : ℝ, |trueDensitySecondDerivative x| ^ 2 :=
  rfl

theorem vaart1998_kernelMISEBoundRHS_def
    (constant : ℝ) (n : ℕ) (bandwidth : ℝ) :
    vaart1998_kernelMISEBoundRHS constant n bandwidth =
      constant * vaart1998_kernelMISERateEnvelope n bandwidth :=
  rfl

theorem vaart1998_kernelMISEBoundForSmallBandwidth_def
    (meanIntegratedSquareErrorAtBandwidth : ℕ -> ℝ -> ℝ)
    (constant : ℝ) :
    vaart1998_kernelMISEBoundForSmallBandwidth
        meanIntegratedSquareErrorAtBandwidth constant =
      (0 < constant ∧
        ∀ᶠ bandwidth in 𝓝[>] (0 : ℝ),
          ∀ n : ℕ,
            meanIntegratedSquareErrorAtBandwidth n bandwidth ≤
              vaart1998_kernelMISEBoundRHS constant n bandwidth) :=
  rfl

/--
Source package for van der Vaart 1998, Chapter 24.1-24.2 opening:
nonparametric density estimation, kernel estimators, component smoothing, and
MISE decomposition.
-/
structure Vaart1998Chapter24KernelDensityOpeningSource
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P] where
  /-- The unknown density `f` to be estimated. -/
  trueDensity : ℝ -> ℝ
  /-- Sample observations `X_i`. -/
  observation : (n : ℕ) -> Fin n -> Ω -> ℝ
  /-- Kernel/window `K`. -/
  kernel : ℝ -> ℝ
  /-- Bandwidth `h`. -/
  bandwidth : ℕ -> ℝ
  bandwidthPositive : ∀ n : ℕ, 0 < bandwidth n
  /-- Source statement that `K` is a probability density. -/
  kernelProbabilityDensity_statement : Prop
  kernelProbabilityDensity : kernelProbabilityDensity_statement
  /-- Source statement that `K` has mean zero. -/
  kernelMeanZero_statement : Prop
  kernelMeanZero : kernelMeanZero_statement
  /-- Source statement that `K` has variance one. -/
  kernelVarianceOne_statement : Prop
  kernelVarianceOne : kernelVarianceOne_statement
  /-- Source statement contrasting parametric and nonparametric models. -/
  parametricNonparametricContrast_statement : Prop
  parametricNonparametricContrast :
    parametricNonparametricContrast_statement
  /-- Source statement that Chapter 24 studies density estimation. -/
  densityEstimationProblem_statement : Prop
  densityEstimationProblem : densityEstimationProblem_statement
  /-- Source statement that the empirical distribution is discrete and has no
  density in the sense needed here. -/
  empiricalDistributionNoDensity_statement : Prop
  empiricalDistributionNoDensity : empiricalDistributionNoDensity_statement
  /-- The normal-family plug-in density display. -/
  normalPluginDensity : ℕ -> Ω -> ℝ -> ℝ
  normalPluginDensityDisplay_statement : Prop
  normalPluginDensityDisplay : normalPluginDensityDisplay_statement
  /-- Kernel estimator `hat f`. -/
  kernelEstimator : ℕ -> Ω -> ℝ -> ℝ
  kernelEstimator_eq :
    ∀ n ω x,
      kernelEstimator n ω x =
        vaart1998_kernelDensityEstimator kernel
          (fun i => observation n i ω) (bandwidth n) x
  /-- The component kernel generated by a single observation. -/
  kernelComponent : (n : ℕ) -> Fin n -> Ω -> ℝ -> ℝ
  kernelComponent_eq :
    ∀ n i ω x,
      kernelComponent n i ω x =
        vaart1998_kernelDensityComponent kernel n
          (observation n i ω) (bandwidth n) x
  kernelEstimator_sum_components :
    ∀ n ω x, kernelEstimator n ω x =
      ∑ i : Fin n, kernelComponent n i ω x
  /-- Source statement that every component has area `1/n`. -/
  componentAreaOneOverN_statement : Prop
  componentAreaOneOverN : componentAreaOneOverN_statement
  /-- Source statement that kernel estimators smooth the empirical point
  masses using the kernel and bandwidth. -/
  smoothingInterpretation_statement : Prop
  smoothingInterpretation : smoothingInterpretation_statement
  /-- Mean integrated square error. -/
  meanIntegratedSquareError : ℕ -> ℝ
  integratedVarianceTerm : ℕ -> ℝ
  integratedSquaredBiasTerm : ℕ -> ℝ
  miseDecomposition :
    ∀ n,
      meanIntegratedSquareError n =
        vaart1998_miseDecompositionRHS
          (integratedVarianceTerm n) (integratedSquaredBiasTerm n)
  /-- Source statement that the MISE is integrated pointwise mean-square
  error. -/
  integratedPointwiseMSE_statement : Prop
  integratedPointwiseMSE : integratedPointwiseMSE_statement
  /-- Joint measurability assumption for the random density estimator. -/
  jointMeasurableEstimator_statement : Prop
  jointMeasurableEstimator : jointMeasurableEstimator_statement
  /-- Source statement that small MISE means the estimator is close to the
  target density. -/
  smallMISEImpliesFunctionClose_statement : Prop
  smallMISEImpliesFunctionClose :
    smallMISEImpliesFunctionClose_statement

namespace Vaart1998Chapter24KernelDensityOpeningSource

section

variable {Ω : Type*} [MeasurableSpace Ω]
variable {P : Measure Ω} [IsProbabilityMeasure P]
variable (S : Vaart1998Chapter24KernelDensityOpeningSource P)

theorem bandwidth_positive (n : ℕ) :
    0 < S.bandwidth n :=
  S.bandwidthPositive n

theorem kernel_probability_density_source :
    S.kernelProbabilityDensity_statement :=
  S.kernelProbabilityDensity

theorem kernel_mean_zero_source :
    S.kernelMeanZero_statement :=
  S.kernelMeanZero

theorem kernel_variance_one_source :
    S.kernelVarianceOne_statement :=
  S.kernelVarianceOne

theorem parametric_nonparametric_contrast_source :
    S.parametricNonparametricContrast_statement :=
  S.parametricNonparametricContrast

theorem density_estimation_problem_source :
    S.densityEstimationProblem_statement :=
  S.densityEstimationProblem

theorem empirical_distribution_no_density_source :
    S.empiricalDistributionNoDensity_statement :=
  S.empiricalDistributionNoDensity

theorem normal_plugin_density_display_source :
    S.normalPluginDensityDisplay_statement :=
  S.normalPluginDensityDisplay

theorem kernel_estimator_display (n : ℕ) (ω : Ω) (x : ℝ) :
    S.kernelEstimator n ω x =
      vaart1998_kernelDensityEstimator S.kernel
        (fun i => S.observation n i ω) (S.bandwidth n) x :=
  S.kernelEstimator_eq n ω x

theorem kernel_component_display (n : ℕ) (i : Fin n) (ω : Ω)
    (x : ℝ) :
    S.kernelComponent n i ω x =
      vaart1998_kernelDensityComponent S.kernel n
        (S.observation n i ω) (S.bandwidth n) x :=
  S.kernelComponent_eq n i ω x

theorem kernel_estimator_sum_components (n : ℕ) (ω : Ω) (x : ℝ) :
    S.kernelEstimator n ω x =
      ∑ i : Fin n, S.kernelComponent n i ω x :=
  S.kernelEstimator_sum_components n ω x

theorem component_area_one_over_n_source :
    S.componentAreaOneOverN_statement :=
  S.componentAreaOneOverN

theorem smoothing_interpretation_source :
    S.smoothingInterpretation_statement :=
  S.smoothingInterpretation

theorem mise_decomposition_display (n : ℕ) :
    S.meanIntegratedSquareError n =
      vaart1998_miseDecompositionRHS
        (S.integratedVarianceTerm n) (S.integratedSquaredBiasTerm n) :=
  S.miseDecomposition n

theorem integrated_pointwise_mse_source :
    S.integratedPointwiseMSE_statement :=
  S.integratedPointwiseMSE

theorem joint_measurable_estimator_source :
    S.jointMeasurableEstimator_statement :=
  S.jointMeasurableEstimator

theorem small_mise_implies_function_close_source :
    S.smallMISEImpliesFunctionClose_statement :=
  S.smallMISEImpliesFunctionClose

end

end Vaart1998Chapter24KernelDensityOpeningSource

/--
Source package for the Chapter 24 variance/bias order paragraph following the
kernel-density MISE decomposition.
-/
structure Vaart1998Chapter24KernelDensityRateSource
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P] where
  /-- The already-verified opening kernel-density source package. -/
  opening : Vaart1998Chapter24KernelDensityOpeningSource P
  /-- Display envelope `(n h)^{-1} + h^4`. -/
  rateEnvelope : ℕ -> ℝ
  rateEnvelope_eq :
    ∀ n,
      rateEnvelope n =
        vaart1998_kernelMISERateEnvelope n (opening.bandwidth n)
  /-- Source statement that small MISE requires both the integrated variance
  and integrated squared-bias terms to be small. -/
  bothTermsSmallNeeded_statement : Prop
  bothTermsSmallNeeded : bothTermsSmallNeeded_statement
  /-- Integrated variance term has order `(n h)^{-1}`. -/
  integratedVarianceOrder :
    vaart1998_deterministicOrderAtRate
      opening.integratedVarianceTerm
      (fun n => vaart1998_kernelVarianceRateTerm n
        (opening.bandwidth n))
  /-- Integrated squared-bias term has order `h^4`. -/
  integratedSquaredBiasOrder :
    vaart1998_deterministicOrderAtRate
      opening.integratedSquaredBiasTerm
      (fun n => vaart1998_kernelSquaredBiasRateTerm
        (opening.bandwidth n))
  /-- Source balance `(n h)^{-1} ~ h^4`. -/
  varianceBiasRateBalance :
    vaart1998_kernelRateBalance opening.bandwidth
  /-- Source optimal bandwidth display `h ~ n^{-1/5}`. -/
  bandwidthOptimalRate :
    vaart1998_asymptoticallyEquivalentRates opening.bandwidth
      vaart1998_kernelOptimalBandwidthDisplay
  /-- Source optimal MISE order `n^{-4/5}`. -/
  meanIntegratedSquareErrorOrderOptimal :
    vaart1998_deterministicOrderAtRate
      opening.meanIntegratedSquareError
      vaart1998_kernelOptimalMISEDisplay
  /-- Bias display before the change of variables. -/
  biasInitialIntegral : ℕ -> ℝ -> ℝ
  biasInitialIntegral_eq :
    ∀ n x,
      biasInitialIntegral n x =
        vaart1998_kernelBiasInitialIntegralDisplay
          opening.kernel opening.trueDensity (opening.bandwidth n) x
  /-- Bias display after the change of variables. -/
  biasChangeOfVariables : ℕ -> ℝ -> ℝ
  biasChangeOfVariables_eq :
    ∀ n x,
      biasChangeOfVariables n x =
        vaart1998_kernelBiasChangeOfVariablesDisplay
          opening.kernel opening.trueDensity (opening.bandwidth n) x
  /-- Source statement justifying the change of variables in the displayed
  bias identity. -/
  biasChangeOfVariables_statement : Prop
  biasChangeOfVariables_source : biasChangeOfVariables_statement
  /-- A supplied second derivative of the unknown density for the Taylor
  display. -/
  trueDensitySecondDerivative : ℝ -> ℝ
  /-- The informal leading Taylor bias term. -/
  biasTaylorLeadingTerm : ℕ -> ℝ -> ℝ
  biasTaylorLeadingTerm_eq :
    ∀ n x,
      biasTaylorLeadingTerm n x =
        vaart1998_kernelBiasTaylorLeadingTermDisplay
          opening.kernel trueDensitySecondDerivative
          (opening.bandwidth n) x
  /-- Source statement using `∫ y K(y) dy = 0` to remove the first-order Taylor
  term. -/
  firstMomentCancellation_statement : Prop
  firstMomentCancellation : firstMomentCancellation_statement
  /-- Source statement that the Taylor display yields squared-bias order
  `h^4`. -/
  squaredBiasTaylorOrder_statement : Prop
  squaredBiasTaylorOrder : squaredBiasTaylorOrder_statement
  /-- Source statement that the variance term is handled similarly. -/
  varianceTermSimilarTaylor_statement : Prop
  varianceTermSimilarTaylor : varianceTermSimilarTaylor_statement

namespace Vaart1998Chapter24KernelDensityRateSource

section

variable {Ω : Type*} [MeasurableSpace Ω]
variable {P : Measure Ω} [IsProbabilityMeasure P]
variable (S : Vaart1998Chapter24KernelDensityRateSource P)

def opening_source :
    Vaart1998Chapter24KernelDensityOpeningSource P :=
  S.opening

theorem rate_envelope_display (n : ℕ) :
    S.rateEnvelope n =
      vaart1998_kernelMISERateEnvelope n (S.opening.bandwidth n) :=
  S.rateEnvelope_eq n

theorem both_terms_small_needed_source :
    S.bothTermsSmallNeeded_statement :=
  S.bothTermsSmallNeeded

theorem integrated_variance_order :
    vaart1998_deterministicOrderAtRate
      S.opening.integratedVarianceTerm
      (fun n => vaart1998_kernelVarianceRateTerm n
        (S.opening.bandwidth n)) :=
  S.integratedVarianceOrder

theorem integrated_squared_bias_order :
    vaart1998_deterministicOrderAtRate
      S.opening.integratedSquaredBiasTerm
      (fun n => vaart1998_kernelSquaredBiasRateTerm
        (S.opening.bandwidth n)) :=
  S.integratedSquaredBiasOrder

theorem variance_bias_rate_balance :
    vaart1998_kernelRateBalance S.opening.bandwidth :=
  S.varianceBiasRateBalance

theorem bandwidth_optimal_rate :
    vaart1998_asymptoticallyEquivalentRates S.opening.bandwidth
      vaart1998_kernelOptimalBandwidthDisplay :=
  S.bandwidthOptimalRate

theorem mean_integrated_square_error_order_optimal :
    vaart1998_deterministicOrderAtRate
      S.opening.meanIntegratedSquareError
      vaart1998_kernelOptimalMISEDisplay :=
  S.meanIntegratedSquareErrorOrderOptimal

theorem bias_initial_integral_display (n : ℕ) (x : ℝ) :
    S.biasInitialIntegral n x =
      vaart1998_kernelBiasInitialIntegralDisplay
        S.opening.kernel S.opening.trueDensity
        (S.opening.bandwidth n) x :=
  S.biasInitialIntegral_eq n x

theorem bias_change_of_variables_display (n : ℕ) (x : ℝ) :
    S.biasChangeOfVariables n x =
      vaart1998_kernelBiasChangeOfVariablesDisplay
        S.opening.kernel S.opening.trueDensity
        (S.opening.bandwidth n) x :=
  S.biasChangeOfVariables_eq n x

theorem bias_change_of_variables_source :
    S.biasChangeOfVariables_statement :=
  S.biasChangeOfVariables_source

theorem kernel_mean_zero_for_taylor_source :
    S.opening.kernelMeanZero_statement :=
  S.opening.kernelMeanZero

theorem bias_taylor_leading_term_display (n : ℕ) (x : ℝ) :
    S.biasTaylorLeadingTerm n x =
      vaart1998_kernelBiasTaylorLeadingTermDisplay
        S.opening.kernel S.trueDensitySecondDerivative
        (S.opening.bandwidth n) x :=
  S.biasTaylorLeadingTerm_eq n x

theorem first_moment_cancellation_source :
    S.firstMomentCancellation_statement :=
  S.firstMomentCancellation

theorem squared_bias_taylor_order_source :
    S.squaredBiasTaylorOrder_statement :=
  S.squaredBiasTaylorOrder

theorem variance_term_similar_taylor_source :
    S.varianceTermSimilarTaylor_statement :=
  S.varianceTermSimilarTaylor

end

end Vaart1998Chapter24KernelDensityRateSource

/--
Source package for van der Vaart 1998, Theorem 24.1: the precise MISE upper
bound for kernel density estimators and the optimal-bandwidth consequence.
-/
structure Vaart1998Chapter24Theorem24_1MISEBoundSource
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P] where
  /-- The preceding Chapter 24 variance/bias rate source. -/
  rateSource : Vaart1998Chapter24KernelDensityRateSource P
  /-- MISE as a two-argument display depending on sample size and a bandwidth
  value. -/
  meanIntegratedSquareErrorAtBandwidth : ℕ -> ℝ -> ℝ
  meanIntegratedSquareErrorAtSourceBandwidth :
    ∀ n,
      meanIntegratedSquareErrorAtBandwidth n
        (rateSource.opening.bandwidth n) =
          rateSource.opening.meanIntegratedSquareError n
  /-- Source assumption: `f` is twice continuously differentiable. -/
  densityTwiceContinuouslyDifferentiable_statement : Prop
  densityTwiceContinuouslyDifferentiable :
    densityTwiceContinuouslyDifferentiable_statement
  /-- Source assumption: `∫ |f''(x)|^2 dx < ∞`. -/
  densitySecondDerivativeSquareIntegrable_statement : Prop
  densitySecondDerivativeSquareIntegrable :
    densitySecondDerivativeSquareIntegrable_statement
  densitySecondDerivativeSquareIntegral : ℝ
  densitySecondDerivativeSquareIntegral_eq :
    densitySecondDerivativeSquareIntegral =
      vaart1998_densitySecondDerivativeSquareIntegralDisplay
        rateSource.trueDensitySecondDerivative
  /-- Source assumption `∫ y K(y) dy = 0`. -/
  kernelFirstMomentZero :
    vaart1998_kernelFirstMomentDisplay rateSource.opening.kernel = 0
  /-- Source assumption: `∫ y^2 K(y) dy` is finite. -/
  kernelSecondMomentFinite_statement : Prop
  kernelSecondMomentFinite : kernelSecondMomentFinite_statement
  kernelSecondMoment : ℝ
  kernelSecondMomentDisplay_eq :
    kernelSecondMoment =
      vaart1998_kernelSecondMomentDisplay rateSource.opening.kernel
  /-- Source assumption: `∫ K^2(y) dy` is finite. -/
  kernelSquaredIntegralFinite_statement : Prop
  kernelSquaredIntegralFinite : kernelSquaredIntegralFinite_statement
  kernelSquaredIntegral : ℝ
  kernelSquaredIntegral_eq :
    kernelSquaredIntegral =
      vaart1998_kernelSquaredIntegralDisplay rateSource.opening.kernel
  /-- The constant `C_f` in Theorem 24.1. -/
  theoremConstant : ℝ
  theoremConstantPositive : 0 < theoremConstant
  /-- The displayed bound for sufficiently small positive bandwidth. -/
  theorem24_1MISEBound :
    vaart1998_kernelMISEBoundForSmallBandwidth
      meanIntegratedSquareErrorAtBandwidth theoremConstant
  /-- Consequence for source bandwidths `h_n ~ n^{-1/5}`:
  `MISE_f(hat f_n)=O(n^{-4/5})`. -/
  optimalBandwidthMISEOrder :
    vaart1998_deterministicOrderAtRate
      rateSource.opening.meanIntegratedSquareError
      vaart1998_kernelOptimalMISEDisplay

namespace Vaart1998Chapter24Theorem24_1MISEBoundSource

section

variable {Ω : Type*} [MeasurableSpace Ω]
variable {P : Measure Ω} [IsProbabilityMeasure P]
variable (S : Vaart1998Chapter24Theorem24_1MISEBoundSource P)

def rate_source :
    Vaart1998Chapter24KernelDensityRateSource P :=
  S.rateSource

theorem mise_at_source_bandwidth (n : ℕ) :
    S.meanIntegratedSquareErrorAtBandwidth n
        (S.rateSource.opening.bandwidth n) =
      S.rateSource.opening.meanIntegratedSquareError n :=
  S.meanIntegratedSquareErrorAtSourceBandwidth n

theorem density_twice_continuously_differentiable_source :
    S.densityTwiceContinuouslyDifferentiable_statement :=
  S.densityTwiceContinuouslyDifferentiable

theorem density_second_derivative_square_integrable_source :
    S.densitySecondDerivativeSquareIntegrable_statement :=
  S.densitySecondDerivativeSquareIntegrable

theorem density_second_derivative_square_integral_display :
    S.densitySecondDerivativeSquareIntegral =
      vaart1998_densitySecondDerivativeSquareIntegralDisplay
        S.rateSource.trueDensitySecondDerivative :=
  S.densitySecondDerivativeSquareIntegral_eq

theorem kernel_first_moment_zero :
    vaart1998_kernelFirstMomentDisplay S.rateSource.opening.kernel = 0 :=
  S.kernelFirstMomentZero

theorem kernel_second_moment_finite_source :
    S.kernelSecondMomentFinite_statement :=
  S.kernelSecondMomentFinite

theorem kernel_second_moment_display :
    S.kernelSecondMoment =
      vaart1998_kernelSecondMomentDisplay S.rateSource.opening.kernel :=
  S.kernelSecondMomentDisplay_eq

theorem kernel_squared_integral_finite_source :
    S.kernelSquaredIntegralFinite_statement :=
  S.kernelSquaredIntegralFinite

theorem kernel_squared_integral_display :
    S.kernelSquaredIntegral =
      vaart1998_kernelSquaredIntegralDisplay
        S.rateSource.opening.kernel :=
  S.kernelSquaredIntegral_eq

theorem theorem_constant_positive :
    0 < S.theoremConstant :=
  S.theoremConstantPositive

theorem theorem24_1_mise_bound :
    vaart1998_kernelMISEBoundForSmallBandwidth
      S.meanIntegratedSquareErrorAtBandwidth S.theoremConstant :=
  S.theorem24_1MISEBound

theorem optimal_bandwidth_mise_order :
    vaart1998_deterministicOrderAtRate
      S.rateSource.opening.meanIntegratedSquareError
      vaart1998_kernelOptimalMISEDisplay :=
  S.optimalBandwidthMISEOrder

theorem optimal_bandwidth_mise_order_from_rate_source :
    vaart1998_deterministicOrderAtRate
      S.rateSource.opening.meanIntegratedSquareError
      vaart1998_kernelOptimalMISEDisplay :=
  S.rateSource.meanIntegratedSquareErrorOrderOptimal

end

end Vaart1998Chapter24Theorem24_1MISEBoundSource

end AsymptoticStatistics
end StatInference
