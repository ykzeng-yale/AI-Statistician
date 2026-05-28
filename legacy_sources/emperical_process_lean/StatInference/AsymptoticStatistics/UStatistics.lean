import StatInference.AsymptoticStatistics.Projections

/-!
# van der Vaart 1998 Chapter 12 U-statistic interfaces

This module opens the Chapter 12 lane.  The first layer records the
one-sample and two-sample `U`-statistic displays, their Hájek projection
forms, the covariance/variance coefficient displays used in Theorems 12.3 and
12.6, and source-shaped asymptotic-normality and degenerate-kernel handoffs
that reuse the Chapter 11 projection machinery.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal ProbabilityTheory Topology

/--
The normalizing factor `1 / choose n r` in the one-sample `U`-statistic.
-/
def vaart1998_uStatisticChooseNorm (n r : ℕ) : ℝ :=
  (Nat.choose n r : ℝ)⁻¹

/--
The unnormalized one-sample sum over subsets of cardinality `r`.
-/
def vaart1998_oneSampleUStatisticSum
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (kernel : Finset ι -> Ω -> ℝ) (r : ℕ) : Ω -> ℝ :=
  fun ω =>
    ∑ β : Finset ι, if β.card = r then kernel β ω else 0

/--
Chapter 12.1 one-sample `U`-statistic display:
`choose n r^{-1} sum_{|β|=r} h(X_β)`.
-/
def vaart1998_oneSampleUStatistic
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (kernel : Finset ι -> Ω -> ℝ) (r : ℕ) : Ω -> ℝ :=
  fun ω =>
    vaart1998_uStatisticChooseNorm (Fintype.card ι) r *
      vaart1998_oneSampleUStatisticSum kernel r ω

/--
The parameter display `θ = E h(X_1, ..., X_r)` for a chosen reference kernel
representative.
-/
def vaart1998_uStatisticKernelMean
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (kernelAtReference : Ω -> ℝ) : ℝ :=
  ∫ ω, kernelAtReference ω ∂P

/--
The first projection kernel display
`h_1(X_i) = E(h | X_i) - θ`.
-/
def vaart1998_oneSampleFirstProjectionKernel
    {Ω ι : Type*}
    (conditionalKernel : ι -> Ω -> ℝ) (theta : ℝ)
    (i : ι) : Ω -> ℝ :=
  fun ω => conditionalKernel i ω - theta

/--
The one-sample Hájek projection display from Theorem 12.3:
`(r / n) sum_i h_1(X_i)`.
-/
def vaart1998_oneSampleHajekProjection
    {Ω ι : Type*} [Fintype ι]
    (h1 : ι -> Ω -> ℝ) (r : ℕ) : Ω -> ℝ :=
  fun ω =>
    ((r : ℝ) / (Fintype.card ι : ℝ)) *
      ∑ i : ι, h1 i ω

/--
The covariance display `ζ_c` used in the one-sample variance expansion.
-/
def vaart1998_oneSampleZeta
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (left right : Ω -> ℝ) : ℝ :=
  vaart1998_projectionCovariance P left right

/--
The displayed variance of the one-sample Hájek projection:
`r^2 ζ_1 / n`.
-/
def vaart1998_oneSampleProjectionVariance
    (n r : ℕ) (zetaOne : ℝ) : ℝ :=
  ((r : ℝ) ^ 2 / (n : ℝ)) * zetaOne

/--
The coefficient of `ζ_c` in the one-sample variance expansion from the proof
of Theorem 12.3.
-/
def vaart1998_oneSampleVarianceCoefficient
    (n r c : ℕ) : ℝ :=
  (vaart1998_uStatisticChooseNorm n r) ^ 2 *
    (Nat.choose n r : ℝ) *
    (Nat.choose r c : ℝ) *
    (Nat.choose (n - r) (r - c) : ℝ)

/--
The one-sample variance expansion
`choose n r^{-2} sum_c choose n r choose r c choose (n-r) (r-c) ζ_c`.
-/
def vaart1998_oneSampleVarianceExpansion
    (n r : ℕ) (zeta : ℕ -> ℝ) : ℝ :=
  (Finset.range (r + 1)).sum fun c =>
    vaart1998_oneSampleVarianceCoefficient n r c * zeta c

/--
Finite-sample source for the Chapter 12.1 one-sample `U`-statistic display.
-/
structure Vaart1998OneSampleUStatisticFiniteSource
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    (P : Measure Ω) where
  /-- Kernel degree `r`. -/
  degree : ℕ
  /-- Kernel evaluated on each unordered subset. -/
  kernel : Finset ι -> Ω -> ℝ
  /-- The displayed `U`-statistic. -/
  statistic : Ω -> ℝ
  /-- Reference kernel representative used for `θ`. -/
  referenceKernel : Ω -> ℝ
  /-- The parameter `θ`. -/
  parameter : ℝ
  /-- Conditional-kernel displays used to form `h_1`. -/
  conditionalKernel : ι -> Ω -> ℝ
  /-- First projection kernels `h_1(X_i)`. -/
  firstProjectionKernel : ι -> Ω -> ℝ
  /-- The Hájek projection `\hat U`. -/
  hajekProjection : Ω -> ℝ
  /-- Covariance coefficients `ζ_c`. -/
  zeta : ℕ -> ℝ
  /-- Variance of the `U`-statistic. -/
  statisticVariance : ℝ
  /-- Variance of the Hájek projection. -/
  projectionVariance : ℝ
  /-- Symmetry assumption on the kernel. -/
  symmetricKernel : Prop
  /-- Square-integrability assumption from Theorem 12.3. -/
  finiteSecondMoment : Prop
  /-- Identification of the finite-sample `U`-statistic display. -/
  statistic_eq :
    statistic =
      vaart1998_oneSampleUStatistic kernel degree
  /-- Identification of `θ = E h`. -/
  parameter_eq :
    parameter = vaart1998_uStatisticKernelMean P referenceKernel
  /-- Identification of `h_1`. -/
  firstProjectionKernel_eq :
    ∀ i,
      firstProjectionKernel i =
        vaart1998_oneSampleFirstProjectionKernel
          conditionalKernel parameter i
  /-- Identification of the Hájek projection display. -/
  hajekProjection_eq :
    hajekProjection =
      vaart1998_oneSampleHajekProjection firstProjectionKernel degree
  /-- The `U`-statistic is unbiased for `θ`. -/
  unbiased :
    vaart1998_projectionExpectation P statistic = parameter
  /-- The proof's variance expansion for `U`. -/
  statisticVariance_eq :
    statisticVariance =
      vaart1998_oneSampleVarianceExpansion
        (Fintype.card ι) degree zeta
  /-- The proof's variance display for `\hat U`. -/
  projectionVariance_eq :
    projectionVariance =
      vaart1998_oneSampleProjectionVariance
        (Fintype.card ι) degree (zeta 1)

/--
The finite-sample one-sample `U`-statistic display.
-/
theorem Vaart1998OneSampleUStatisticFiniteSource.statistic_display
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998OneSampleUStatisticFiniteSource
      (Ω := Ω) (ι := ι) P) :
    S.statistic =
      vaart1998_oneSampleUStatistic S.kernel S.degree :=
  S.statistic_eq

/--
The finite-sample one-sample Hájek projection display.
-/
theorem Vaart1998OneSampleUStatisticFiniteSource.hajekProjection_display
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998OneSampleUStatisticFiniteSource
      (Ω := Ω) (ι := ι) P) :
    S.hajekProjection =
      vaart1998_oneSampleHajekProjection
        S.firstProjectionKernel S.degree :=
  S.hajekProjection_eq

/--
The finite-sample unbiasedness assertion `E U = θ`.
-/
theorem Vaart1998OneSampleUStatisticFiniteSource.unbiased_for_parameter
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998OneSampleUStatisticFiniteSource
      (Ω := Ω) (ι := ι) P) :
    vaart1998_projectionExpectation P S.statistic = S.parameter :=
  S.unbiased

/--
The unnormalized two-sample sum over subsets of cardinalities `r` and `s`.
-/
def vaart1998_twoSampleUStatisticSum
    {Ω ι κ : Type*} [Fintype ι] [DecidableEq ι]
    [Fintype κ] [DecidableEq κ]
    (kernel : Finset ι -> Finset κ -> Ω -> ℝ)
    (r s : ℕ) : Ω -> ℝ :=
  fun ω =>
    ∑ α : Finset ι,
      ∑ β : Finset κ,
        if α.card = r ∧ β.card = s then kernel α β ω else 0

/--
Chapter 12.2 two-sample `U`-statistic display.
-/
def vaart1998_twoSampleUStatistic
    {Ω ι κ : Type*} [Fintype ι] [DecidableEq ι]
    [Fintype κ] [DecidableEq κ]
    (kernel : Finset ι -> Finset κ -> Ω -> ℝ)
    (r s : ℕ) : Ω -> ℝ :=
  fun ω =>
    (vaart1998_uStatisticChooseNorm (Fintype.card ι) r *
        vaart1998_uStatisticChooseNorm (Fintype.card κ) s) *
      vaart1998_twoSampleUStatisticSum kernel r s ω

/--
The first `X`-sample projection kernel display `h_{1,0}`.
-/
def vaart1998_twoSampleFirstProjectionKernelX
    {Ω ι : Type*}
    (conditionalKernelX : ι -> Ω -> ℝ) (theta : ℝ)
    (i : ι) : Ω -> ℝ :=
  fun ω => conditionalKernelX i ω - theta

/--
The first `Y`-sample projection kernel display `h_{0,1}`.
-/
def vaart1998_twoSampleFirstProjectionKernelY
    {Ω κ : Type*}
    (conditionalKernelY : κ -> Ω -> ℝ) (theta : ℝ)
    (j : κ) : Ω -> ℝ :=
  fun ω => conditionalKernelY j ω - theta

/--
The two-sample Hájek projection display from Theorem 12.6:
`(r/m) sum_i h_{1,0}(X_i) + (s/n) sum_j h_{0,1}(Y_j)`.
-/
def vaart1998_twoSampleHajekProjection
    {Ω ι κ : Type*} [Fintype ι] [Fintype κ]
    (h10 : ι -> Ω -> ℝ) (h01 : κ -> Ω -> ℝ)
    (r s : ℕ) : Ω -> ℝ :=
  fun ω =>
    ((r : ℝ) / (Fintype.card ι : ℝ)) *
        ∑ i : ι, h10 i ω
      +
      ((s : ℝ) / (Fintype.card κ : ℝ)) *
        ∑ j : κ, h01 j ω

/--
The displayed variance of the two-sample Hájek projection.
-/
def vaart1998_twoSampleProjectionVariance
    (m n r s : ℕ) (zeta10 zeta01 : ℝ) : ℝ :=
  ((r : ℝ) ^ 2 / (m : ℝ)) * zeta10 +
    ((s : ℝ) ^ 2 / (n : ℝ)) * zeta01

/--
The coefficient of `ζ_{c,d}` in the two-sample variance expansion from
Theorem 12.6.
-/
def vaart1998_twoSampleVarianceCoefficient
    (m n r s c d : ℕ) : ℝ :=
  (vaart1998_uStatisticChooseNorm m r *
      vaart1998_uStatisticChooseNorm n s) ^ 2 *
    (Nat.choose m r : ℝ) *
    (Nat.choose r c : ℝ) *
    (Nat.choose (m - r) (r - c) : ℝ) *
    (Nat.choose n s : ℝ) *
    (Nat.choose s d : ℝ) *
    (Nat.choose (n - s) (s - d) : ℝ)

/--
The two-sample variance expansion over the number of common `X` and `Y`
indices.
-/
def vaart1998_twoSampleVarianceExpansion
    (m n r s : ℕ) (zeta : ℕ -> ℕ -> ℝ) : ℝ :=
  (Finset.range (r + 1)).sum fun c =>
    (Finset.range (s + 1)).sum fun d =>
      vaart1998_twoSampleVarianceCoefficient m n r s c d * zeta c d

/--
Finite-sample source for the Chapter 12.2 two-sample `U`-statistic display.
-/
structure Vaart1998TwoSampleUStatisticFiniteSource
    {Ω ι κ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι] [Fintype κ] [DecidableEq κ]
    (P : Measure Ω) where
  /-- Kernel degree in the first sample. -/
  degreeX : ℕ
  /-- Kernel degree in the second sample. -/
  degreeY : ℕ
  /-- Kernel evaluated on unordered subsets from both samples. -/
  kernel : Finset ι -> Finset κ -> Ω -> ℝ
  /-- The displayed two-sample `U`-statistic. -/
  statistic : Ω -> ℝ
  /-- Reference kernel representative used for `θ`. -/
  referenceKernel : Ω -> ℝ
  /-- The parameter `θ`. -/
  parameter : ℝ
  /-- Conditional-kernel displays for `h_{1,0}`. -/
  conditionalKernelX : ι -> Ω -> ℝ
  /-- Conditional-kernel displays for `h_{0,1}`. -/
  conditionalKernelY : κ -> Ω -> ℝ
  /-- First projection kernels in the `X` sample. -/
  firstProjectionKernelX : ι -> Ω -> ℝ
  /-- First projection kernels in the `Y` sample. -/
  firstProjectionKernelY : κ -> Ω -> ℝ
  /-- The two-sample Hájek projection. -/
  hajekProjection : Ω -> ℝ
  /-- Covariance coefficients `ζ_{c,d}`. -/
  zeta : ℕ -> ℕ -> ℝ
  /-- Variance of the two-sample `U`-statistic. -/
  statisticVariance : ℝ
  /-- Variance of the two-sample Hájek projection. -/
  projectionVariance : ℝ
  /-- Separate symmetry in the `X` and `Y` arguments. -/
  separatelySymmetricKernel : Prop
  /-- Square-integrability assumption from Theorem 12.6. -/
  finiteSecondMoment : Prop
  /-- Identification of the finite-sample two-sample statistic display. -/
  statistic_eq :
    statistic =
      vaart1998_twoSampleUStatistic kernel degreeX degreeY
  /-- Identification of `θ = E h`. -/
  parameter_eq :
    parameter = vaart1998_uStatisticKernelMean P referenceKernel
  /-- Identification of `h_{1,0}`. -/
  firstProjectionKernelX_eq :
    ∀ i,
      firstProjectionKernelX i =
        vaart1998_twoSampleFirstProjectionKernelX
          conditionalKernelX parameter i
  /-- Identification of `h_{0,1}`. -/
  firstProjectionKernelY_eq :
    ∀ j,
      firstProjectionKernelY j =
        vaart1998_twoSampleFirstProjectionKernelY
          conditionalKernelY parameter j
  /-- Identification of the two-sample Hájek projection display. -/
  hajekProjection_eq :
    hajekProjection =
      vaart1998_twoSampleHajekProjection
        firstProjectionKernelX firstProjectionKernelY degreeX degreeY
  /-- The two-sample `U`-statistic is unbiased for `θ`. -/
  unbiased :
    vaart1998_projectionExpectation P statistic = parameter
  /-- The proof's variance expansion for `U`. -/
  statisticVariance_eq :
    statisticVariance =
      vaart1998_twoSampleVarianceExpansion
        (Fintype.card ι) (Fintype.card κ) degreeX degreeY zeta
  /-- The proof's variance display for `\hat U`. -/
  projectionVariance_eq :
    projectionVariance =
      vaart1998_twoSampleProjectionVariance
        (Fintype.card ι) (Fintype.card κ) degreeX degreeY
        (zeta 1 0) (zeta 0 1)

/--
The finite-sample two-sample `U`-statistic display.
-/
theorem Vaart1998TwoSampleUStatisticFiniteSource.statistic_display
    {Ω ι κ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι] [Fintype κ] [DecidableEq κ]
    {P : Measure Ω}
    (S : Vaart1998TwoSampleUStatisticFiniteSource
      (Ω := Ω) (ι := ι) (κ := κ) P) :
    S.statistic =
      vaart1998_twoSampleUStatistic
        S.kernel S.degreeX S.degreeY :=
  S.statistic_eq

/--
The finite-sample two-sample Hájek projection display.
-/
theorem Vaart1998TwoSampleUStatisticFiniteSource.hajekProjection_display
    {Ω ι κ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι] [Fintype κ] [DecidableEq κ]
    {P : Measure Ω}
    (S : Vaart1998TwoSampleUStatisticFiniteSource
      (Ω := Ω) (ι := ι) (κ := κ) P) :
    S.hajekProjection =
      vaart1998_twoSampleHajekProjection
        S.firstProjectionKernelX S.firstProjectionKernelY
        S.degreeX S.degreeY :=
  S.hajekProjection_eq

/--
The finite-sample two-sample unbiasedness assertion `E U = θ`.
-/
theorem Vaart1998TwoSampleUStatisticFiniteSource.unbiased_for_parameter
    {Ω ι κ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι] [Fintype κ] [DecidableEq κ]
    {P : Measure Ω}
    (S : Vaart1998TwoSampleUStatisticFiniteSource
      (Ω := Ω) (ι := ι) (κ := κ) P) :
    vaart1998_projectionExpectation P S.statistic = S.parameter :=
  S.unbiased

/--
The sequence `sqrt n (U_n - θ)`.
-/
def vaart1998_sqrtNCenteredStatistic
    {Ω : Type*} (statistic : ℕ -> Ω -> ℝ) (theta : ℝ) :
    ℕ -> Ω -> ℝ :=
  fun n ω => Real.sqrt (n : ℝ) * (statistic n ω - theta)

/--
The sequence `sqrt n \hat U_n`.
-/
def vaart1998_sqrtNProjection
    {Ω : Type*} (projection : ℕ -> Ω -> ℝ) :
    ℕ -> Ω -> ℝ :=
  fun n ω => Real.sqrt (n : ℝ) * projection n ω

/--
The sequence `sqrt n (U_n - θ - \hat U_n)`.
-/
def vaart1998_sqrtNProjectionResidual
    {Ω : Type*} (statistic projection : ℕ -> Ω -> ℝ)
    (theta : ℝ) : ℕ -> Ω -> ℝ :=
  fun n ω => Real.sqrt (n : ℝ) *
    (statistic n ω - theta - projection n ω)

/--
Theorem 12.3 source: one-sample `U`-statistic asymptotic normality via the
Chapter 11 projection method.
-/
structure Vaart1998Theorem12_3OneSampleProjectionMethodSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Kernel degree `r`. -/
  degree : ℕ
  /-- The `U`-statistics `U_n`. -/
  statistic : ℕ -> Ω -> ℝ
  /-- The parameter `θ`. -/
  parameter : ℝ
  /-- The Hájek projections `\hat U_n`. -/
  hajekProjection : ℕ -> Ω -> ℝ
  /-- Covariance coefficient `ζ_1`. -/
  zetaOne : ℝ
  /-- Asymptotic variance `r^2 ζ_1`. -/
  asymptoticVariance : ℝ
  /-- Displayed `sqrt n (U_n - θ)`. -/
  scaledCenteredStatistic : ℕ -> Ω -> ℝ
  /-- Displayed `sqrt n \hat U_n`. -/
  scaledHajekProjection : ℕ -> Ω -> ℝ
  /-- Displayed `sqrt n (U_n - θ - \hat U_n)`. -/
  scaledProjectionResidual : ℕ -> Ω -> ℝ
  /-- Identification of the scaled statistic display. -/
  scaledCenteredStatistic_eq :
    scaledCenteredStatistic =
      vaart1998_sqrtNCenteredStatistic statistic parameter
  /-- Identification of the scaled projection display. -/
  scaledHajekProjection_eq :
    scaledHajekProjection =
      vaart1998_sqrtNProjection hajekProjection
  /-- Identification of the scaled residual display. -/
  scaledProjectionResidual_eq :
    scaledProjectionResidual =
      vaart1998_sqrtNProjectionResidual
        statistic hajekProjection parameter
  /-- The variance display `r^2 ζ_1`. -/
  asymptoticVariance_eq :
    asymptoticVariance = (degree : ℝ) ^ 2 * zetaOne
  /-- The Chapter 11 projection-method source supplying the `o_P(1)` handoff. -/
  projectionMethodSource :
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource P LimitLaw
  /-- Alignment with the Chapter 11 standardized statistic. -/
  standardizedStatistic_eq :
    projectionMethodSource.standardizedStatistic =
      scaledCenteredStatistic
  /-- Alignment with the Chapter 11 standardized projection. -/
  standardizedProjection_eq :
    projectionMethodSource.standardizedProjection =
      scaledHajekProjection
  /-- Alignment with the Chapter 11 standardized residual. -/
  standardizedDifference_eq :
    projectionMethodSource.standardizedDifference =
      scaledProjectionResidual
  /-- Source predicate saying the limit law is normal with variance `r^2 ζ_1`. -/
  normalLimitWithVariance : ℝ -> Prop
  /-- The normal-limit display from Theorem 12.3. -/
  normalLimit_display :
    normalLimitWithVariance asymptoticVariance

/--
Theorem 12.3 projection residual:
`sqrt n (U_n - θ - \hat U_n) = o_P(1)`.
-/
theorem Vaart1998Theorem12_3OneSampleProjectionMethodSource.projectionResidual_oP
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem12_3OneSampleProjectionMethodSource
      P LimitLaw) :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      S.scaledProjectionResidual := by
  have h :=
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.standardizedDifference_oP
      S.projectionMethodSource
  simpa [S.standardizedDifference_eq] using h

/--
Theorem 12.3: the scaled centered one-sample `U`-statistic inherits the
projection limit law.
-/
theorem Vaart1998Theorem12_3OneSampleProjectionMethodSource.scaledCenteredStatistic_tendstoInDistribution
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem12_3OneSampleProjectionMethodSource
      P LimitLaw) :
    TendstoInDistribution S.scaledCenteredStatistic atTop
      S.projectionMethodSource.limitStatistic P LimitLaw := by
  have h :=
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.statistic_tendstoInDistribution
      S.projectionMethodSource
  simpa [S.standardizedStatistic_eq] using h

/--
Theorem 12.3 normal-limit variance display.
-/
theorem Vaart1998Theorem12_3OneSampleProjectionMethodSource.normalLimit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem12_3OneSampleProjectionMethodSource
      P LimitLaw) :
    S.normalLimitWithVariance S.asymptoticVariance :=
  S.normalLimit_display

/--
Theorem 12.6 source: two-sample `U`-statistic asymptotic normality via the
Chapter 11 projection method.
-/
structure Vaart1998Theorem12_6TwoSampleProjectionMethodSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Kernel degree in the first sample. -/
  degreeX : ℕ
  /-- Kernel degree in the second sample. -/
  degreeY : ℕ
  /-- The two-sample `U`-statistics `U_n`. -/
  statistic : ℕ -> Ω -> ℝ
  /-- The parameter `θ`. -/
  parameter : ℝ
  /-- The two-sample Hájek projections. -/
  hajekProjection : ℕ -> Ω -> ℝ
  /-- Limit of `m / (m+n)`. -/
  lambda : ℝ
  /-- The first-sample covariance coefficient `ζ_{1,0}`. -/
  zeta10 : ℝ
  /-- The second-sample covariance coefficient `ζ_{0,1}`. -/
  zeta01 : ℝ
  /-- Asymptotic variance from Theorem 12.6. -/
  asymptoticVariance : ℝ
  /-- Displayed `sqrt N (U_n - θ)`. -/
  scaledCenteredStatistic : ℕ -> Ω -> ℝ
  /-- Displayed `sqrt N \hat U_n`. -/
  scaledHajekProjection : ℕ -> Ω -> ℝ
  /-- Displayed `sqrt N (U_n - θ - \hat U_n)`. -/
  scaledProjectionResidual : ℕ -> Ω -> ℝ
  /-- The sample-share hypothesis `m/N -> λ`. -/
  sampleShare_tendsto_lambda : Prop
  /-- The side condition `0 < λ < 1`. -/
  lambda_between_zero_and_one : 0 < lambda ∧ lambda < 1
  /-- Identification of the scaled statistic display. -/
  scaledCenteredStatistic_eq :
    scaledCenteredStatistic =
      vaart1998_sqrtNCenteredStatistic statistic parameter
  /-- Identification of the scaled projection display. -/
  scaledHajekProjection_eq :
    scaledHajekProjection =
      vaart1998_sqrtNProjection hajekProjection
  /-- Identification of the scaled residual display. -/
  scaledProjectionResidual_eq :
    scaledProjectionResidual =
      vaart1998_sqrtNProjectionResidual
        statistic hajekProjection parameter
  /-- The variance display
      `r^2 ζ_{1,0}/λ + s^2 ζ_{0,1}/(1-λ)`. -/
  asymptoticVariance_eq :
    asymptoticVariance =
      (degreeX : ℝ) ^ 2 * zeta10 / lambda +
        (degreeY : ℝ) ^ 2 * zeta01 / (1 - lambda)
  /-- The Chapter 11 projection-method source supplying the `o_P(1)` handoff. -/
  projectionMethodSource :
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource P LimitLaw
  /-- Alignment with the Chapter 11 standardized statistic. -/
  standardizedStatistic_eq :
    projectionMethodSource.standardizedStatistic =
      scaledCenteredStatistic
  /-- Alignment with the Chapter 11 standardized projection. -/
  standardizedProjection_eq :
    projectionMethodSource.standardizedProjection =
      scaledHajekProjection
  /-- Alignment with the Chapter 11 standardized residual. -/
  standardizedDifference_eq :
    projectionMethodSource.standardizedDifference =
      scaledProjectionResidual
  /-- Source predicate saying the limit law is normal with the displayed variance. -/
  normalLimitWithVariance : ℝ -> Prop
  /-- The normal-limit display from Theorem 12.6. -/
  normalLimit_display :
    normalLimitWithVariance asymptoticVariance

/--
Theorem 12.6 projection residual:
`sqrt N (U_n - θ - \hat U_n) = o_P(1)`.
-/
theorem Vaart1998Theorem12_6TwoSampleProjectionMethodSource.projectionResidual_oP
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem12_6TwoSampleProjectionMethodSource
      P LimitLaw) :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      S.scaledProjectionResidual := by
  have h :=
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.standardizedDifference_oP
      S.projectionMethodSource
  simpa [S.standardizedDifference_eq] using h

/--
Theorem 12.6: the scaled centered two-sample `U`-statistic inherits the
projection limit law.
-/
theorem Vaart1998Theorem12_6TwoSampleProjectionMethodSource.scaledCenteredStatistic_tendstoInDistribution
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem12_6TwoSampleProjectionMethodSource
      P LimitLaw) :
    TendstoInDistribution S.scaledCenteredStatistic atTop
      S.projectionMethodSource.limitStatistic P LimitLaw := by
  have h :=
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.statistic_tendstoInDistribution
      S.projectionMethodSource
  simpa [S.standardizedStatistic_eq] using h

/--
Theorem 12.6 normal-limit variance display.
-/
theorem Vaart1998Theorem12_6TwoSampleProjectionMethodSource.normalLimit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem12_6TwoSampleProjectionMethodSource
      P LimitLaw) :
    S.normalLimitWithVariance S.asymptoticVariance :=
  S.normalLimit_display

/--
Strong degeneracy of a kernel of order `A`: every strict lower conditioning
has conditional expectation zero.
-/
def vaart1998_stronglyDegenerateKernel
    {Ω ι : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (conditionalKernel : Finset ι -> Ω -> ℝ)
    (A : Finset ι) : Prop :=
  ∀ B, B ⊆ A -> B.card < A.card ->
    conditionalKernel B =ᵐ[P] 0

/--
The covariance-order degeneracy condition
`ζ_1 = ... = ζ_{c-1} = 0 < ζ_c`.
-/
def vaart1998_degenerateCovarianceOrder
    (zeta : ℕ -> ℝ) (c : ℕ) : Prop :=
  (∀ k, 1 ≤ k -> k < c -> zeta k = 0) ∧ 0 < zeta c

/--
The generic degenerate scaling display `a_n (U_n - θ)`.
-/
def vaart1998_degenerateScaledCenteredStatistic
    {Ω : Type*} (scale : ℕ -> ℝ)
    (statistic : ℕ -> Ω -> ℝ) (theta : ℝ) :
    ℕ -> Ω -> ℝ :=
  fun n ω => scale n * (statistic n ω - theta)

/--
Section 12.3 source: the Hoeffding decomposition of a `U`-statistic produces
lower-order `U`-statistics with strongly degenerate kernels.
-/
structure Vaart1998DegenerateUStatisticHoeffdingSource
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    (P : Measure Ω) (statistic : Ω -> ℝ) where
  /-- The Chapter 11 symmetric Hoeffding bridge. -/
  hoeffdingBridge :
    Vaart1998SymmetricHoeffdingUStatisticBridgeSource
      (Ω := Ω) (ι := ι) statistic
  /-- The active Hoeffding order `c`. -/
  order : ℕ
  /-- A representative active set of variables of size `c`. -/
  activeSet : Finset ι
  /-- Cardinality of the active set. -/
  activeSet_card : activeSet.card = order
  /-- Conditional-kernel displays for strict lower subsets. -/
  conditionalKernel : Finset ι -> Ω -> ℝ
  /-- Identification with the Chapter 11 order kernel. -/
  conditionalKernel_eq_orderTerm :
    conditionalKernel =
      hoeffdingBridge.orderTerm order
  /-- Strong degeneracy of the order-`c` kernel. -/
  stronglyDegenerate :
    vaart1998_stronglyDegenerateKernel P
      conditionalKernel activeSet
  /-- Orthogonality to every statistic depending on fewer than `c` variables. -/
  uncorrelatedWithLowerOrder : Prop
  /-- The orthogonality assertion from Section 12.3. -/
  uncorrelatedWithLowerOrder_proof :
    uncorrelatedWithLowerOrder

/--
The Chapter 12 order term is a `U`-statistic, inherited from the Chapter 11
Hoeffding bridge.
-/
theorem Vaart1998DegenerateUStatisticHoeffdingSource.order_uStatistic
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω} {statistic : Ω -> ℝ}
    (S : Vaart1998DegenerateUStatisticHoeffdingSource
      (Ω := Ω) (ι := ι) P statistic) :
    S.hoeffdingBridge.uStatisticOfOrder
      S.order (S.hoeffdingBridge.orderStatistic S.order) :=
  S.hoeffdingBridge.orderStatistic_uStatistic S.order

/--
The Section 12.3 strong-degeneracy handoff for the active kernel.
-/
theorem Vaart1998DegenerateUStatisticHoeffdingSource.strong_degenerate
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω} {statistic : Ω -> ℝ}
    (S : Vaart1998DegenerateUStatisticHoeffdingSource
      (Ω := Ω) (ι := ι) P statistic) :
    vaart1998_stronglyDegenerateKernel P
      S.conditionalKernel S.activeSet :=
  S.stronglyDegenerate

/--
The Section 12.3 orthogonality-to-lower-order-statistics handoff.
-/
theorem Vaart1998DegenerateUStatisticHoeffdingSource.uncorrelated_lower_order
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω} {statistic : Ω -> ℝ}
    (S : Vaart1998DegenerateUStatisticHoeffdingSource
      (Ω := Ω) (ι := ι) P statistic) :
    S.uncorrelatedWithLowerOrder :=
  S.uncorrelatedWithLowerOrder_proof

/--
Theorem 12.10 source: a degenerate `U`-statistic has a Gaussian-chaos limit
with variance `c! E h_c^2`.
-/
structure Vaart1998Theorem12_10DegenerateUStatisticLimitSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Degenerate order `c`. -/
  order : ℕ
  /-- The degenerate `U`-statistics `U_{n,c}`. -/
  statistic : ℕ -> Ω -> ℝ
  /-- Scaling, typically `n^{c/2}`. -/
  scale : ℕ -> ℝ
  /-- Scaled statistic display. -/
  scaledStatistic : ℕ -> Ω -> ℝ
  /-- Limit Gaussian-chaos statistic. -/
  gaussianChaosLimit : ΩLimit -> ℝ
  /-- Second moment `E h_c^2`. -/
  kernelSecondMoment : ℝ
  /-- Limit variance. -/
  limitVariance : ℝ
  /-- Identification of the scaling display. -/
  scaledStatistic_eq :
    scaledStatistic =
      vaart1998_degenerateScaledCenteredStatistic
        scale statistic 0
  /-- The theorem's weak convergence conclusion. -/
  scaledStatistic_tendstoInDistribution :
    TendstoInDistribution scaledStatistic atTop
      gaussianChaosLimit P LimitLaw
  /-- Variance display `c! E h_c^2`. -/
  limitVariance_eq :
    limitVariance =
      (Nat.factorial order : ℝ) * kernelSecondMoment
  /-- Source predicate for the Gaussian-chaos expansion. -/
  gaussianChaosExpansion : (ΩLimit -> ℝ) -> Prop
  /-- The displayed Hermite/product-basis Gaussian-chaos expansion. -/
  gaussianChaosExpansion_proof :
    gaussianChaosExpansion gaussianChaosLimit

/--
Theorem 12.10 weak convergence to the Gaussian-chaos limit.
-/
theorem Vaart1998Theorem12_10DegenerateUStatisticLimitSource.tendstoInDistribution
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem12_10DegenerateUStatisticLimitSource
      P LimitLaw) :
    TendstoInDistribution S.scaledStatistic atTop
      S.gaussianChaosLimit P LimitLaw :=
  S.scaledStatistic_tendstoInDistribution

/--
Theorem 12.10 variance display.
-/
theorem Vaart1998Theorem12_10DegenerateUStatisticLimitSource.variance_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem12_10DegenerateUStatisticLimitSource
      P LimitLaw) :
    S.limitVariance =
      (Nat.factorial S.order : ℝ) * S.kernelSecondMoment :=
  S.limitVariance_eq

end AsymptoticStatistics
end StatInference
