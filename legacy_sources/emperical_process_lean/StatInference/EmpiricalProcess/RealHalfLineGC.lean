import StatInference.EmpiricalProcess.GlivenkoCantelli
import StatInference.EmpiricalProcess.EndpointSamples
import StatInference.EmpiricalProcess.RealHalfLine

/-!
# Half-line Glivenko-Cantelli handoffs

This module connects the supplied-grid layer for VdV&W Example 2.4.2 to the
already proved bracketing Glivenko-Cantelli theorem.  The grid construction
from an arbitrary distribution is still a separate task.
-/

namespace StatInference

open MeasureTheory ProbabilityTheory Set Filter

open scoped Function Topology

universe u

/--
The population integral of a closed half-line indicator is the CDF value at
that endpoint.

This is the pointwise bridge between Billingsley's empirical distribution
function notation and the local half-line indicator class.
-/
theorem realHalfLineIndicator_integral_eq_cdf
    (P : Measure ℝ) [IsProbabilityMeasure P] (c : ℝ) :
    (∫ x, realHalfLineIndicator c x ∂P) = ProbabilityTheory.cdf P c := by
  calc
    (∫ x, realHalfLineIndicator c x ∂P) = P.real (Set.Iic c) := by
      simp [realHalfLineIndicator]
    _ = ProbabilityTheory.cdf P c :=
      (ProbabilityTheory.cdf_eq_real P c).symm

/--
The population integral of an open half-line indicator is the left-limit CDF
value at that endpoint.

This is the pointwise bridge for Durrett's `F_n(x-)` display.
-/
theorem realOpenHalfLineIndicator_integral_eq_cdf_leftLim
    (P : Measure ℝ) [IsProbabilityMeasure P] (c : ℝ) :
    (∫ x, realOpenHalfLineIndicator c x ∂P) =
      Function.leftLim (ProbabilityTheory.cdf P) c := by
  have hmeasure :
      ((ProbabilityTheory.cdf P).measure (Set.Iio c)).toReal =
        P.real (Set.Iio c) := by
    rw [measureReal_def, ProbabilityTheory.measure_cdf]
  have hleft_nonneg :
      0 ≤ Function.leftLim (ProbabilityTheory.cdf P) c := by
    have hlt : c - 1 < c := by linarith
    exact
      (ProbabilityTheory.cdf_nonneg P (c - 1)).trans
        ((ProbabilityTheory.monotone_cdf P).le_leftLim hlt)
  calc
    (∫ x, realOpenHalfLineIndicator c x ∂P) = P.real (Set.Iio c) := by
      simp [realOpenHalfLineIndicator]
    _ = ((ProbabilityTheory.cdf P).measure (Set.Iio c)).toReal :=
      hmeasure.symm
    _ = (ENNReal.ofReal
          (Function.leftLim (ProbabilityTheory.cdf P) c - 0)).toReal := by
      exact congrArg ENNReal.toReal
        ((ProbabilityTheory.cdf P).measure_Iio
          (ProbabilityTheory.tendsto_cdf_atBot P) c)
    _ = Function.leftLim (ProbabilityTheory.cdf P) c := by
      simpa using ENNReal.toReal_ofReal hleft_nonneg

/--
The empirical distribution function of a finite real sample.

For a sample `x_0, ..., x_{n-1}`, this is the textbook
`F_n(c) = n^{-1} * #{i : x_i <= c}`, represented through the local empirical
average of the closed-half-line indicator.
-/
noncomputable def empiricalDistributionFunction {n : ℕ}
    (sample : SampleAt ℝ n) (c : ℝ) : ℝ :=
  empiricalAverage sample (realHalfLineIndicator c)

/--
The left empirical distribution function of a finite real sample.

For a sample `x_0, ..., x_{n-1}`, this is Durrett's
`F_n(c-) = n^{-1} * #{i : x_i < c}`, represented through the local empirical
average of the open-half-line indicator.
-/
noncomputable def empiricalLeftDistributionFunction {n : ℕ}
    (sample : SampleAt ℝ n) (c : ℝ) : ℝ :=
  empiricalAverage sample (realOpenHalfLineIndicator c)

/-- Unfolding lemma for the empirical distribution function. -/
theorem empiricalDistributionFunction_eq_sum_div {n : ℕ}
    (sample : SampleAt ℝ n) (c : ℝ) :
    empiricalDistributionFunction sample c =
      (∑ i : Fin n, realHalfLineIndicator c (sample i)) / (n : ℝ) :=
  rfl

/-- Unfolding lemma for the left empirical distribution function. -/
theorem empiricalLeftDistributionFunction_eq_sum_div {n : ℕ}
    (sample : SampleAt ℝ n) (c : ℝ) :
    empiricalLeftDistributionFunction sample c =
      (∑ i : Fin n, realOpenHalfLineIndicator c (sample i)) / (n : ℝ) :=
  rfl

/-- Empirical distribution functions are nonnegative. -/
theorem empiricalDistributionFunction_nonneg {n : ℕ}
    (sample : SampleAt ℝ n) (c : ℝ) :
    0 ≤ empiricalDistributionFunction sample c := by
  unfold empiricalDistributionFunction empiricalAverage
  exact div_nonneg
    (Finset.sum_nonneg fun i _hi => by
      by_cases h : sample i ≤ c <;> simp [realHalfLineIndicator, h])
    (Nat.cast_nonneg n)

/-- Empirical distribution functions are bounded by one. -/
theorem empiricalDistributionFunction_le_one {n : ℕ}
    (sample : SampleAt ℝ n) (c : ℝ) :
    empiricalDistributionFunction sample c ≤ 1 := by
  unfold empiricalDistributionFunction empiricalAverage
  have hsum :
      (∑ i : Fin n, realHalfLineIndicator c (sample i)) ≤
        ∑ _i : Fin n, (1 : ℝ) := by
    exact Finset.sum_le_sum fun i _hi => by
      by_cases h : sample i ≤ c <;> simp [realHalfLineIndicator, h]
  calc
    (∑ i : Fin n, realHalfLineIndicator c (sample i)) / (n : ℝ)
        ≤ (∑ _i : Fin n, (1 : ℝ)) / (n : ℝ) :=
          div_le_div_of_nonneg_right hsum (Nat.cast_nonneg n)
    _ ≤ 1 := by
      by_cases hn : n = 0
      · subst n
        simp
      · have hcast : (n : ℝ) ≠ 0 := by exact_mod_cast hn
        simp [hcast]

/-- Left empirical distribution functions are nonnegative. -/
theorem empiricalLeftDistributionFunction_nonneg {n : ℕ}
    (sample : SampleAt ℝ n) (c : ℝ) :
    0 ≤ empiricalLeftDistributionFunction sample c := by
  unfold empiricalLeftDistributionFunction empiricalAverage
  exact div_nonneg
    (Finset.sum_nonneg fun i _hi => by
      by_cases h : sample i < c <;> simp [realOpenHalfLineIndicator, h])
    (Nat.cast_nonneg n)

/-- Left empirical distribution functions are bounded by one. -/
theorem empiricalLeftDistributionFunction_le_one {n : ℕ}
    (sample : SampleAt ℝ n) (c : ℝ) :
    empiricalLeftDistributionFunction sample c ≤ 1 := by
  unfold empiricalLeftDistributionFunction empiricalAverage
  have hsum :
      (∑ i : Fin n, realOpenHalfLineIndicator c (sample i)) ≤
        ∑ _i : Fin n, (1 : ℝ) := by
    exact Finset.sum_le_sum fun i _hi => by
      by_cases h : sample i < c <;> simp [realOpenHalfLineIndicator, h]
  calc
    (∑ i : Fin n, realOpenHalfLineIndicator c (sample i)) / (n : ℝ)
        ≤ (∑ _i : Fin n, (1 : ℝ)) / (n : ℝ) :=
          div_le_div_of_nonneg_right hsum (Nat.cast_nonneg n)
    _ ≤ 1 := by
      by_cases hn : n = 0
      · subst n
        simp
      · have hcast : (n : ℝ) ≠ 0 := by exact_mod_cast hn
        simp [hcast]

/--
Empirical distribution functions along an observation process are the usual
range-indexed averages of half-line indicators.
-/
theorem empiricalDistributionFunction_samplePath_eq_range_sum
    {Ω : Type u} (X : ℕ -> Ω -> ℝ) (ω : Ω) (n : ℕ) (c : ℝ) :
    empiricalDistributionFunction (samplePath X ω n) c =
      (∑ i ∈ Finset.range n, realHalfLineIndicator c (X i ω)) / (n : ℝ) := by
  simpa [empiricalDistributionFunction] using
    empiricalAverage_samplePath_eq_range_sum X ω n (realHalfLineIndicator c)

/--
Left empirical distribution functions along an observation process are the
usual range-indexed averages of open-half-line indicators.
-/
theorem empiricalLeftDistributionFunction_samplePath_eq_range_sum
    {Ω : Type u} (X : ℕ -> Ω -> ℝ) (ω : Ω) (n : ℕ) (c : ℝ) :
    empiricalLeftDistributionFunction (samplePath X ω n) c =
      (∑ i ∈ Finset.range n, realOpenHalfLineIndicator c (X i ω)) / (n : ℝ) := by
  simpa [empiricalLeftDistributionFunction] using
    empiricalAverage_samplePath_eq_range_sum X ω n (realOpenHalfLineIndicator c)

/--
The population risk of a closed-half-line indicator is the distribution
function value at the endpoint.
-/
theorem populationRisk_realHalfLineIndicator_eq_cdf
    (P : Measure ℝ) [IsProbabilityMeasure P] (c : ℝ) :
    populationRiskOfFunction P (realHalfLineIndicator c) =
      ProbabilityTheory.cdf P c := by
  simpa [populationRiskOfFunction] using realHalfLineIndicator_integral_eq_cdf P c

/--
The population risk of an open-half-line indicator is the left-limit
distribution function value at the endpoint.
-/
theorem populationRisk_realOpenHalfLineIndicator_eq_cdf_leftLim
    (P : Measure ℝ) [IsProbabilityMeasure P] (c : ℝ) :
    populationRiskOfFunction P (realOpenHalfLineIndicator c) =
      Function.leftLim (ProbabilityTheory.cdf P) c := by
  simpa [populationRiskOfFunction] using
    realOpenHalfLineIndicator_integral_eq_cdf_leftLim P c

/--
Source-facing empirical-CDF Glivenko-Cantelli predicate for real observations.

This is the local uniform-deviation formulation of Durrett's
`sup_x |F_n(x) - F(x)| -> 0`, using either outer probability or outer almost
sure convergence according to the existing book-style predicate convention.
-/
def RealEmpiricalCDFGlivenkoCantelliClass
    {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (P : Measure ℝ) (X : ℕ -> Ω -> ℝ) : Prop :=
  VdVWOuterProbabilityUniformDeviationTendstoZeroOn μ Set.univ
      (fun c => ProbabilityTheory.cdf P c)
      (fun ω sampleSize c =>
        empiricalDistributionFunction (samplePath X ω sampleSize) c) ∨
    VdVWOuterAlmostSureUniformDeviationTendstoZeroOn μ Set.univ
      (fun c => ProbabilityTheory.cdf P c)
      (fun ω sampleSize c =>
        empiricalDistributionFunction (samplePath X ω sampleSize) c)

/--
Source-facing left empirical-CDF Glivenko-Cantelli predicate for real
observations.

This is the local uniform-deviation formulation of Durrett's
`sup_x |F_n(x-) - F(x-)| -> 0`, expressed through the existing outer
probability / outer almost-sure predicate convention.
-/
def RealEmpiricalLeftCDFGlivenkoCantelliClass
    {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (P : Measure ℝ) (X : ℕ -> Ω -> ℝ) : Prop :=
  VdVWOuterProbabilityUniformDeviationTendstoZeroOn μ Set.univ
      (fun c => Function.leftLim (ProbabilityTheory.cdf P) c)
      (fun ω sampleSize c =>
        empiricalLeftDistributionFunction (samplePath X ω sampleSize) c) ∨
    VdVWOuterAlmostSureUniformDeviationTendstoZeroOn μ Set.univ
      (fun c => Function.leftLim (ProbabilityTheory.cdf P) c)
      (fun ω sampleSize c =>
        empiricalLeftDistributionFunction (samplePath X ω sampleSize) c)

/--
The half-line indicator class predicate is exactly the source-facing empirical
CDF predicate after unfolding `F_n` and `F`.
-/
theorem realEmpiricalCDFGlivenkoCantelliClass_of_realHalfLine
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    {X : ℕ -> Ω -> ℝ}
    (h :
      VdVWPGlivenkoCantelliClass μ P Set.univ realHalfLineIndicator X) :
    RealEmpiricalCDFGlivenkoCantelliClass μ P X := by
  rcases h with h | h
  · left
    simpa [RealEmpiricalCDFGlivenkoCantelliClass,
      VdVWOuterProbabilityPGlivenkoCantelliClass,
      empiricalDistributionFunction, populationRiskOfFunction,
      realHalfLineIndicator_integral_eq_cdf] using h
  · right
    simpa [RealEmpiricalCDFGlivenkoCantelliClass,
      VdVWOuterAlmostSurePGlivenkoCantelliClass,
      empiricalDistributionFunction, populationRiskOfFunction,
      realHalfLineIndicator_integral_eq_cdf] using h

/--
The open-half-line indicator class predicate is exactly the source-facing left
empirical-CDF predicate after unfolding `F_n(·-)` and `F(·-)`.
-/
theorem realEmpiricalLeftCDFGlivenkoCantelliClass_of_realOpenHalfLine
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    {X : ℕ -> Ω -> ℝ}
    (h :
      VdVWPGlivenkoCantelliClass μ P Set.univ realOpenHalfLineIndicator X) :
    RealEmpiricalLeftCDFGlivenkoCantelliClass μ P X := by
  rcases h with h | h
  · left
    simpa [RealEmpiricalLeftCDFGlivenkoCantelliClass,
      VdVWOuterProbabilityPGlivenkoCantelliClass,
      empiricalLeftDistributionFunction, populationRiskOfFunction,
      realOpenHalfLineIndicator_integral_eq_cdf_leftLim] using h
  · right
    simpa [RealEmpiricalLeftCDFGlivenkoCantelliClass,
      VdVWOuterAlmostSurePGlivenkoCantelliClass,
      empiricalLeftDistributionFunction, populationRiskOfFunction,
      realOpenHalfLineIndicator_integral_eq_cdf_leftLim] using h

/--
Exact outer-a.s. open-half-line GC predicates unfold to the left empirical-CDF
uniform-deviation statement.
-/
theorem realEmpiricalLeftCDF_outerAlmostSure_of_realOpenHalfLine
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    {X : ℕ -> Ω -> ℝ}
    (h :
      VdVWOuterAlmostSurePGlivenkoCantelliClass μ P Set.univ
        realOpenHalfLineIndicator X) :
    VdVWOuterAlmostSureUniformDeviationTendstoZeroOn μ Set.univ
      (fun c => Function.leftLim (ProbabilityTheory.cdf P) c)
      (fun ω sampleSize c =>
        empiricalLeftDistributionFunction (samplePath X ω sampleSize) c) := by
  simpa [VdVWOuterAlmostSurePGlivenkoCantelliClass,
    empiricalLeftDistributionFunction, populationRiskOfFunction,
    realOpenHalfLineIndicator_integral_eq_cdf_leftLim] using h

/--
Pointwise empirical-distribution convergence for one closed half-line.

For iid real observations with law `P`, the sample average of
`1{(-∞, c]}` converges almost surely to `F(c)`.
-/
theorem realHalfLine_empiricalAverage_sub_cdf_tendsto_zero_ae_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun n : ℕ =>
          empiricalAverage (samplePath X ω n) (realHalfLineIndicator c) -
            ProbabilityTheory.cdf P c)
        atTop (𝓝 0) := by
  have hInt : Integrable (realHalfLineIndicator c) P :=
    integrable_realHalfLineIndicator P c
  have hIntegral :
      (∫ x, realHalfLineIndicator c x ∂P) = ProbabilityTheory.cdf P c :=
    realHalfLineIndicator_integral_eq_cdf P c
  filter_upwards
    [endpoint_empiricalAverage_sub_population_tendsto_zero_ae_of_iid
      X (realHalfLineIndicator c)
      hInt.aestronglyMeasurable.aemeasurable hInt hLaw hindep]
    with ω hω
  simpa [hIntegral] using hω

/--
Pointwise empirical-distribution convergence in probability for one closed
half-line.

This repackages the fixed-endpoint almost-sure statement through mathlib's
`TendstoInMeasure`, the local common-domain form of convergence in
probability.
-/
theorem realHalfLine_empiricalAverage_sub_cdf_tendstoInMeasure_zero_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    MeasureTheory.TendstoInMeasure μ
      (fun n ω =>
        empiricalAverage (samplePath X ω n) (realHalfLineIndicator c) -
          ProbabilityTheory.cdf P c)
      atTop (fun _ => 0) := by
  letI : IsProbabilityMeasure μ := (hLaw 0).isProbabilityMeasure
  have hIndicator_measurable : Measurable (realHalfLineIndicator c) := by
    simpa [realHalfLineIndicator] using
      (measurable_const.indicator measurableSet_Iic : Measurable (realHalfLineIndicator c))
  have h_aestrongly :
      ∀ n,
        AEStronglyMeasurable
          (fun ω =>
            empiricalAverage (samplePath X ω n) (realHalfLineIndicator c) -
              ProbabilityTheory.cdf P c) μ := by
    intro n
    exact
      ((empiricalAverage_samplePath_aemeasurable_of_hasLaw
        X (realHalfLineIndicator c) n hLaw hIndicator_measurable).sub
          aemeasurable_const).aestronglyMeasurable
  exact
    MeasureTheory.tendstoInMeasure_of_tendsto_ae h_aestrongly
      (realHalfLine_empiricalAverage_sub_cdf_tendsto_zero_ae_of_iid
        X c hLaw hindep)

/--
Fixed-endpoint empirical-distribution convergence in the local VdV&W outer
probability vocabulary.

This is still a pointwise support layer, not the uniform-in-`x`
Glivenko-Cantelli conclusion of Billingsley's Theorem 20.6.
-/
theorem realHalfLine_empiricalAverage_sub_cdf_convergesInOuterProbability_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    VdVWConvergesInOuterProbability μ
      (fun n ω =>
        empiricalAverage (samplePath X ω n) (realHalfLineIndicator c) -
          ProbabilityTheory.cdf P c)
      atTop (fun _ => 0) :=
  vdVWConvergesInOuterProbability_of_tendstoInMeasure
    (realHalfLine_empiricalAverage_sub_cdf_tendstoInMeasure_zero_of_iid
      X c hLaw hindep)

/--
Pointwise left empirical-distribution convergence for one open half-line.

For iid real observations with law `P`, the sample average of
`1{(-∞, c)}` converges almost surely to `F(c-)`.
-/
theorem realOpenHalfLine_empiricalAverage_sub_cdfLeftLim_tendsto_zero_ae_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun n : ℕ =>
          empiricalAverage (samplePath X ω n) (realOpenHalfLineIndicator c) -
            Function.leftLim (ProbabilityTheory.cdf P) c)
        atTop (𝓝 0) := by
  have hInt : Integrable (realOpenHalfLineIndicator c) P :=
    integrable_realOpenHalfLineIndicator P c
  have hIntegral :
      (∫ x, realOpenHalfLineIndicator c x ∂P) =
        Function.leftLim (ProbabilityTheory.cdf P) c :=
    realOpenHalfLineIndicator_integral_eq_cdf_leftLim P c
  filter_upwards
    [endpoint_empiricalAverage_sub_population_tendsto_zero_ae_of_iid
      X (realOpenHalfLineIndicator c)
      hInt.aestronglyMeasurable.aemeasurable hInt hLaw hindep]
    with ω hω
  simpa [hIntegral] using hω

/--
Pointwise left empirical-distribution convergence in probability for one open
half-line.
-/
theorem realOpenHalfLine_empiricalAverage_sub_cdfLeftLim_tendstoInMeasure_zero_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    MeasureTheory.TendstoInMeasure μ
      (fun n ω =>
        empiricalAverage (samplePath X ω n) (realOpenHalfLineIndicator c) -
          Function.leftLim (ProbabilityTheory.cdf P) c)
      atTop (fun _ => 0) := by
  letI : IsProbabilityMeasure μ := (hLaw 0).isProbabilityMeasure
  have hIndicator_measurable : Measurable (realOpenHalfLineIndicator c) := by
    simpa [realOpenHalfLineIndicator] using
      (measurable_const.indicator measurableSet_Iio :
        Measurable (realOpenHalfLineIndicator c))
  have h_aestrongly :
      ∀ n,
        AEStronglyMeasurable
          (fun ω =>
            empiricalAverage (samplePath X ω n) (realOpenHalfLineIndicator c) -
              Function.leftLim (ProbabilityTheory.cdf P) c) μ := by
    intro n
    exact
      ((empiricalAverage_samplePath_aemeasurable_of_hasLaw
        X (realOpenHalfLineIndicator c) n hLaw hIndicator_measurable).sub
          aemeasurable_const).aestronglyMeasurable
  exact
    MeasureTheory.tendstoInMeasure_of_tendsto_ae h_aestrongly
      (realOpenHalfLine_empiricalAverage_sub_cdfLeftLim_tendsto_zero_ae_of_iid
        X c hLaw hindep)

/--
Fixed-endpoint left empirical-distribution convergence in the local VdV&W
outer probability vocabulary.
-/
theorem realOpenHalfLine_empiricalAverage_sub_cdfLeftLim_convergesInOuterProbability_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    VdVWConvergesInOuterProbability μ
      (fun n ω =>
        empiricalAverage (samplePath X ω n) (realOpenHalfLineIndicator c) -
          Function.leftLim (ProbabilityTheory.cdf P) c)
      atTop (fun _ => 0) :=
  vdVWConvergesInOuterProbability_of_tendstoInMeasure
    (realOpenHalfLine_empiricalAverage_sub_cdfLeftLim_tendstoInMeasure_zero_of_iid
      X c hLaw hindep)

/--
Conditional outer-a.s. Glivenko-Cantelli corollary for the real half-line
indicator class.

If finite extended-real half-line grids are supplied at every positive
`L1(P)` radius, then VdV&W Theorem 2.4.1 applies to the class
`{1{(-infty, c]} : c : R}`.
-/
theorem vdVW_realHalfLine_outerAlmostSureGlivenkoCantelli_of_suppliedERealHalfLineGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (gridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid P epsilon cardinality)) :
    VdVWOuterAlmostSurePGlivenkoCantelliClass μ P Set.univ
      realHalfLineIndicator X :=
  vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli
    X hLaw hindep
    (SuppliedERealHalfLineGrid.l1BracketingNumber_lt_top_forall gridExists)

/--
Conditional outer-a.s. Glivenko-Cantelli corollary for the real open
half-line indicator class.

If finite extended-real open half-line grids are supplied at every positive
`L1(P)` radius, then VdV&W Theorem 2.4.1 applies to the class
`{1{(-infty, c)} : c : R}`.
-/
theorem vdVW_realOpenHalfLine_outerAlmostSureGlivenkoCantelli_of_suppliedERealOpenHalfLineGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (gridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cardinality, Nonempty
          (SuppliedERealOpenHalfLineGrid P epsilon cardinality)) :
    VdVWOuterAlmostSurePGlivenkoCantelliClass μ P Set.univ
      realOpenHalfLineIndicator X :=
  vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli
    X hLaw hindep
    (SuppliedERealOpenHalfLineGrid.l1BracketingNumber_lt_top_forall gridExists)

/--
Conditional exact outer-a.s. left empirical-CDF corollary from supplied
extended-real open half-line grids.
-/
theorem realEmpiricalLeftCDF_outerAlmostSure_of_suppliedERealOpenHalfLineGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (gridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cardinality, Nonempty
          (SuppliedERealOpenHalfLineGrid P epsilon cardinality)) :
    VdVWOuterAlmostSureUniformDeviationTendstoZeroOn μ Set.univ
      (fun c => Function.leftLim (ProbabilityTheory.cdf P) c)
      (fun ω sampleSize c =>
        empiricalLeftDistributionFunction (samplePath X ω sampleSize) c) :=
  realEmpiricalLeftCDF_outerAlmostSure_of_realOpenHalfLine
    (vdVW_realOpenHalfLine_outerAlmostSureGlivenkoCantelli_of_suppliedERealOpenHalfLineGrids
      X hLaw hindep gridExists)

/--
Conditional outer-a.s. Glivenko-Cantelli corollary from supplied adjacent
extended-real endpoint grids.

This is closer to the textbook grid notation in Example 2.4.2 than the
primitive supplied-grid interface.
-/
theorem vdVW_realHalfLine_outerAlmostSureGlivenkoCantelli_of_suppliedERealHalfLineEndpointGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (endpointGridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid P epsilon cellCount)) :
    VdVWOuterAlmostSurePGlivenkoCantelliClass μ P Set.univ
      realHalfLineIndicator X :=
  vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli
    X hLaw hindep
    (SuppliedERealHalfLineEndpointGrid.l1BracketingNumber_lt_top_forall
      endpointGridExists)

/--
Conditional book-style Glivenko-Cantelli corollary for the real half-line
indicator class.

This is the current compiled Example 2.4.2 handoff: once the textbook finite
grid is constructed for every positive radius, the half-line class immediately
inherits the local book-style Glivenko-Cantelli predicate.
-/
theorem vdVW_realHalfLine_glivenkoCantelli_of_suppliedERealHalfLineGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (gridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid P epsilon cardinality)) :
    VdVWPGlivenkoCantelliClass μ P Set.univ realHalfLineIndicator X :=
  vdVW_theorem_2_4_1_glivenkoCantelli
    X hLaw hindep
    (SuppliedERealHalfLineGrid.l1BracketingNumber_lt_top_forall gridExists)

/--
Conditional book-style Glivenko-Cantelli corollary for the real open
half-line indicator class.

This is the open-half-line counterpart of the supplied-grid handoff for
`{1{(-infty, c]} : c : R}`.
-/
theorem vdVW_realOpenHalfLine_glivenkoCantelli_of_suppliedERealOpenHalfLineGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (gridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cardinality, Nonempty
          (SuppliedERealOpenHalfLineGrid P epsilon cardinality)) :
    VdVWPGlivenkoCantelliClass μ P Set.univ realOpenHalfLineIndicator X :=
  vdVW_theorem_2_4_1_glivenkoCantelli
    X hLaw hindep
    (SuppliedERealOpenHalfLineGrid.l1BracketingNumber_lt_top_forall gridExists)

/--
Conditional book-style Glivenko-Cantelli corollary from supplied adjacent
extended-real endpoint grids.

Once the distribution-dependent endpoint grid from Example 2.4.2 is
constructed at every positive radius, the half-line class inherits the local
book-style Glivenko-Cantelli predicate.
-/
theorem vdVW_realHalfLine_glivenkoCantelli_of_suppliedERealHalfLineEndpointGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (endpointGridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid P epsilon cellCount)) :
    VdVWPGlivenkoCantelliClass μ P Set.univ realHalfLineIndicator X :=
  vdVW_theorem_2_4_1_glivenkoCantelli
    X hLaw hindep
    (SuppliedERealHalfLineEndpointGrid.l1BracketingNumber_lt_top_forall
      endpointGridExists)

end StatInference
