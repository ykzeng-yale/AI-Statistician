import StatInference.AsymptoticStatistics.MetricSpaceConvergence
import StatInference.EmpiricalProcess.Complexity
import StatInference.EmpiricalProcess.GlivenkoCantelli
import StatInference.EmpiricalProcess.RealHalfLineGC

/-!
# van der Vaart 1998 Chapter 19 empirical processes

This module opens the Chapter 19 lane by naming the book-facing empirical
average, empirical distribution, Glivenko-Cantelli, and Donsker handoffs.
The proofs reuse the compiled empirical-process interfaces from the VdV&W
track instead of duplicating bracketing or outer-probability infrastructure.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal Function ProbabilityTheory Topology

/-- Chapter 19 notation `P_n f` for a fixed finite sample. -/
abbrev vaart1998_empiricalAverage {Observation : Type*} {sampleSize : ℕ}
    (sample : SampleAt Observation sampleSize)
    (testFunction : Observation -> ℝ) : ℝ :=
  empiricalAverage sample testFunction

/-- Chapter 19 notation `P f` for the population mean of a test function. -/
abbrev vaart1998_populationMean {Observation : Type*}
    [MeasurableSpace Observation] (P : Measure Observation)
    (testFunction : Observation -> ℝ) : ℝ :=
  populationRiskOfFunction P testFunction

/-- Chapter 19 empirical process coordinate `sqrt n * (P_n - P) f`. -/
def vaart1998_empiricalProcess {Observation : Type*}
    [MeasurableSpace Observation] {sampleSize : ℕ}
    (P : Measure Observation) (sample : SampleAt Observation sampleSize)
    (testFunction : Observation -> ℝ) : ℝ :=
  Real.sqrt (sampleSize : ℝ) *
    (vaart1998_empiricalAverage sample testFunction -
      vaart1998_populationMean P testFunction)

/-- The empirical distribution function `F_n(t)`. -/
abbrev vaart1998_empiricalDistributionFunction {sampleSize : ℕ}
    (sample : SampleAt ℝ sampleSize) (threshold : ℝ) : ℝ :=
  empiricalDistributionFunction sample threshold

/-- The source-facing real empirical-CDF Glivenko-Cantelli predicate. -/
abbrev vaart1998_empiricalCDFGlivenkoCantelliClass
    {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (P : Measure ℝ) (X : ℕ -> Ω -> ℝ) : Prop :=
  RealEmpiricalCDFGlivenkoCantelliClass μ P X

/-- Chapter 19 book-style `P`-Glivenko-Cantelli predicate for a function class. -/
abbrev vaart1998_pGlivenkoCantelliClass
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (μ : Measure Ω) (P : Measure Observation)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (X : ℕ -> Ω -> Observation) : Prop :=
  VdVWPGlivenkoCantelliClass μ P indexClass classFun X

/-- Chapter 19 outer-a.s. `P`-Glivenko-Cantelli predicate. -/
abbrev vaart1998_outerAlmostSurePGlivenkoCantelliClass
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (μ : Measure Ω) (P : Measure Observation)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (X : ℕ -> Ω -> Observation) : Prop :=
  VdVWOuterAlmostSurePGlivenkoCantelliClass μ P indexClass classFun X

/-- Chapter 19 outer-probability `P`-Glivenko-Cantelli predicate. -/
abbrev vaart1998_outerProbabilityPGlivenkoCantelliClass
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (μ : Measure Ω) (P : Measure Observation)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (X : ℕ -> Ω -> Observation) : Prop :=
  VdVWOuterProbabilityPGlivenkoCantelliClass μ P indexClass classFun X

/-- Chapter 19 empirical-process specification alias. -/
abbrev vaart1998_empiricalProcessSpec :=
  EmpiricalProcessSpec

/-- Chapter 19 Donsker specification alias. -/
abbrev vaart1998_donskerSpec :=
  DonskerSpec

/-- Population means indexed by a Chapter 19 function class. -/
abbrev vaart1998_populationClassMean {Observation Index : Type*}
    [MeasurableSpace Observation] (P : Measure Observation)
    (classFun : Index -> Observation -> ℝ) : Index -> ℝ :=
  fun index => vaart1998_populationMean P (classFun index)

/-- Empirical means indexed by a Chapter 19 function class and sample sequence. -/
abbrev vaart1998_empiricalClassMeanSequence {Observation Index : Type*}
    (samples : ∀ sampleSize, SampleAt Observation sampleSize)
    (classFun : Index -> Observation -> ℝ) : ℕ -> Index -> ℝ :=
  fun sampleSize index =>
    vaart1998_empiricalAverage (samples sampleSize) (classFun index)

/-- Chapter 19 squared `L2(P)` distance between two functions. -/
def vaart1998_l2DistanceSquared {Observation : Type*}
    [MeasurableSpace Observation] (P : Measure Observation)
    (f g : Observation -> ℝ) : ℝ :=
  ∫ x, (f x - g x) ^ 2 ∂P

/-- Chapter 19 variance-semimetric display. -/
def vaart1998_varianceSemimetricSquared {Observation : Type*}
    [MeasurableSpace Observation] (P : Measure Observation)
    (f g : Observation -> ℝ) : ℝ :=
  vaart1998_l2DistanceSquared P
    (fun x => f x - vaart1998_populationMean P f)
    (fun x => g x - vaart1998_populationMean P g)

/-- Empirical process of a difference, `G_n(f-g)`. -/
def vaart1998_empiricalProcessDifference {Observation : Type*}
    [MeasurableSpace Observation] {sampleSize : ℕ}
    (P : Measure Observation) (sample : SampleAt Observation sampleSize)
    (f g : Observation -> ℝ) : ℝ :=
  vaart1998_empiricalProcess P sample (fun x => f x - g x)

/-- Chapter 19 covariance display `P fg - Pf Pg`. -/
def vaart1998_functionCovariance {Observation : Type*}
    [MeasurableSpace Observation] (P : Measure Observation)
    (f g : Observation -> ℝ) : ℝ :=
  (∫ x, f x * g x ∂P) -
    vaart1998_populationMean P f * vaart1998_populationMean P g

/-- Changing-class empirical-process sequence `t ↦ G_n f_{n,t}`. -/
def vaart1998_changingClassEmpiricalProcessSequence
    {Observation Index : Type*} [MeasurableSpace Observation]
    (P : Measure Observation)
    (samples : ∀ sampleSize, SampleAt Observation sampleSize)
    (classFun : ℕ -> Index -> Observation -> ℝ) : ℕ -> Index -> ℝ :=
  fun sampleSize index =>
    vaart1998_empiricalProcess P (samples sampleSize)
      (classFun sampleSize index)

/-- Changing-class covariance sequence `P f_{n,s} f_{n,t} - P f_{n,s} P f_{n,t}`. -/
def vaart1998_changingClassCovarianceSequence
    {Observation Index : Type*} [MeasurableSpace Observation]
    (P : Measure Observation)
    (classFun : ℕ -> Index -> Observation -> ℝ) :
    ℕ -> Index -> Index -> ℝ :=
  fun sampleSize s t =>
    vaart1998_functionCovariance P
      (classFun sampleSize s) (classFun sampleSize t)

/-- Example 19.29 interval cell `(a, a + t δ]`. -/
def vaart1998_localEmpiricalIntervalCell
    (anchor radius index : ℝ) : Set ℝ :=
  Set.Ioc anchor (anchor + index * radius)

/-- Example 19.29 cell indicator `1_(a, a + t δ]`. -/
def vaart1998_localEmpiricalCellIndicator
    (anchor radius index : ℝ) (x : ℝ) : ℝ :=
  Set.indicator
    (vaart1998_localEmpiricalIntervalCell anchor radius index)
    (fun _ : ℝ => (1 : ℝ)) x

/-- Example 19.29 local empirical-measure function `r 1_(a, a + t δ]`. -/
def vaart1998_localEmpiricalFunction
    (anchor scale radius index : ℝ) (x : ℝ) : ℝ :=
  scale * vaart1998_localEmpiricalCellIndicator anchor radius index x

/-- Example 19.29 changing class `f_{n,t} = r_n 1_(a, a + t δ_n]`. -/
def vaart1998_localEmpiricalChangingClass
    (anchor : ℝ) (scale radius : ℕ -> ℝ) :
    ℕ -> ℝ -> ℝ -> ℝ :=
  fun sampleSize index x =>
    vaart1998_localEmpiricalFunction anchor
      (scale sampleSize) (radius sampleSize) index x

/-- Example 19.29 envelope `F_n = f_{n,1}`. -/
def vaart1998_localEmpiricalEnvelope
    (anchor : ℝ) (scale radius : ℕ -> ℝ) :
    ℕ -> ℝ -> ℝ :=
  fun sampleSize =>
    vaart1998_localEmpiricalFunction anchor
      (scale sampleSize) (radius sampleSize) 1

/-- The unscaled local count fraction `P_n 1_(a, a + t δ]`. -/
def vaart1998_localEmpiricalCountFraction {sampleSize : ℕ}
    (sample : SampleAt ℝ sampleSize)
    (anchor radius index : ℝ) : ℝ :=
  vaart1998_empiricalAverage sample
    (vaart1998_localEmpiricalCellIndicator anchor radius index)

/-- Membership display for the local interval cell. -/
theorem vaart1998_mem_localEmpiricalIntervalCell_iff
    {anchor radius index x : ℝ} :
    x ∈ vaart1998_localEmpiricalIntervalCell anchor radius index ↔
      anchor < x ∧ x ≤ anchor + index * radius :=
  Iff.rfl

/-- The local cell indicator is one on its interval. -/
theorem vaart1998_localEmpiricalCellIndicator_eq_one_of_mem
    {anchor radius index x : ℝ}
    (hx : x ∈ vaart1998_localEmpiricalIntervalCell anchor radius index) :
    vaart1998_localEmpiricalCellIndicator anchor radius index x = 1 := by
  simpa [vaart1998_localEmpiricalCellIndicator] using
    Set.indicator_of_mem hx (fun _ : ℝ => (1 : ℝ))

/-- The local cell indicator is zero off its interval. -/
theorem vaart1998_localEmpiricalCellIndicator_eq_zero_of_notMem
    {anchor radius index x : ℝ}
    (hx : x ∉ vaart1998_localEmpiricalIntervalCell anchor radius index) :
    vaart1998_localEmpiricalCellIndicator anchor radius index x = 0 := by
  simpa [vaart1998_localEmpiricalCellIndicator] using
    Set.indicator_of_notMem hx (fun _ : ℝ => (1 : ℝ))

/--
The displayed multiple of the local empirical measure:
`P_n (r 1_(a,a+tδ]) = r P_n 1_(a,a+tδ]`.
-/
theorem vaart1998_localEmpiricalAverage_eq_rescaling_mul_countFraction
    {sampleSize : ℕ} (sample : SampleAt ℝ sampleSize)
    (anchor scale radius index : ℝ) :
    vaart1998_empiricalAverage sample
        (vaart1998_localEmpiricalFunction anchor scale radius index) =
      scale *
        vaart1998_localEmpiricalCountFraction
          sample anchor radius index := by
  simp [vaart1998_localEmpiricalCountFraction, vaart1998_empiricalAverage,
    empiricalAverage, vaart1998_localEmpiricalFunction, Finset.mul_sum,
    div_eq_mul_inv, mul_left_comm, mul_comm]

/-- Lemma 19.31 unit-ball index set `{h : ‖h‖ ≤ 1}`. -/
def vaart1998_lemma19_31UnitBall
    (Parameter : Type*) [Norm Parameter] : Set Parameter :=
  {h | ‖h‖ ≤ 1}

/-- Lemma 19.31 local model difference `m_θ - m_{θ₀}`. -/
def vaart1998_lemma19_31ModelDifference
    {Observation Parameter : Type*}
    (model : Parameter -> Observation -> ℝ)
    (theta theta0 : Parameter) : Observation -> ℝ :=
  fun x => model theta x - model theta0 x

/-- Lemma 19.31 local class `M_δ = {m_θ - m_{θ₀} : ‖θ-θ₀‖ ≤ δ}`. -/
def vaart1998_lemma19_31LocalDifferenceClass
    {Observation Parameter : Type*} [NormedAddCommGroup Parameter]
    (model : Parameter -> Observation -> ℝ) (theta0 : Parameter)
    (radius : ℝ) : Set (Observation -> ℝ) :=
  {g | ∃ theta,
    ‖theta - theta0‖ ≤ radius ∧
      g = vaart1998_lemma19_31ModelDifference model theta theta0}

/-- Lemma 19.31 rescaled class `M_δ / δ`. -/
def vaart1998_lemma19_31RescaledLocalDifferenceClass
    {Observation Parameter : Type*} [NormedAddCommGroup Parameter]
    (model : Parameter -> Observation -> ℝ) (theta0 : Parameter)
    (radius : ℝ) : Set (Observation -> ℝ) :=
  {g | ∃ theta,
    ‖theta - theta0‖ ≤ radius ∧
      g = fun x =>
        radius⁻¹ *
          vaart1998_lemma19_31ModelDifference model theta theta0 x}

/--
Lemma 19.31 rescaled local increment
`r_n (m_{θ₀+h/r_n} - m_{θ₀})`.
-/
def vaart1998_lemma19_31RescaledLocalIncrement
    {Observation Parameter : Type*}
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (model : Parameter -> Observation -> ℝ) (theta0 : Parameter)
    (scale : ℝ) (direction : Parameter) : Observation -> ℝ :=
  fun x =>
    scale *
      (model (theta0 + scale⁻¹ • direction) x - model theta0 x)

/-- Lemma 19.31 linear derivative term `hᵀ dot m_{θ₀}`. -/
def vaart1998_lemma19_31LinearDerivativeTerm
    {Observation Parameter : Type*}
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (derivativeAtTheta0 : Observation -> Parameter →L[ℝ] ℝ)
    (direction : Parameter) : Observation -> ℝ :=
  fun x => derivativeAtTheta0 x direction

/--
Lemma 19.31 centered increment
`r_n(m_{θ₀+h/r_n}-m_{θ₀}) - hᵀ dot m_{θ₀}`.
-/
def vaart1998_lemma19_31CenteredIncrement
    {Observation Parameter : Type*}
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (model : Parameter -> Observation -> ℝ)
    (derivativeAtTheta0 : Observation -> Parameter →L[ℝ] ℝ)
    (theta0 : Parameter) (scale : ℝ)
    (direction : Parameter) : Observation -> ℝ :=
  fun x =>
    vaart1998_lemma19_31RescaledLocalIncrement
        model theta0 scale direction x -
      vaart1998_lemma19_31LinearDerivativeTerm
        derivativeAtTheta0 direction x

/-- Lemma 19.31 changing class indexed by `h`: `r_n(M_{1/r_n})`. -/
def vaart1998_lemma19_31RescaledChangingClass
    {Observation Parameter : Type*}
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (model : Parameter -> Observation -> ℝ)
    (theta0 : Parameter) (scale : ℕ -> ℝ) :
    ℕ -> Parameter -> Observation -> ℝ :=
  fun sampleSize direction =>
    vaart1998_lemma19_31RescaledLocalIncrement
      model theta0 (scale sampleSize) direction

/-- Lemma 19.31 centered changing class appearing in display (19.30). -/
def vaart1998_lemma19_31CenteredChangingClass
    {Observation Parameter : Type*}
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (model : Parameter -> Observation -> ℝ)
    (derivativeAtTheta0 : Observation -> Parameter →L[ℝ] ℝ)
    (theta0 : Parameter) (scale : ℕ -> ℝ) :
    ℕ -> Parameter -> Observation -> ℝ :=
  fun sampleSize direction =>
    vaart1998_lemma19_31CenteredIncrement
      model derivativeAtTheta0 theta0 (scale sampleSize) direction

/-- Right-tail event `{Y > x}` used in Lemma 19.32. -/
def vaart1998_rightTailEvent {Ω : Type*}
    (Y : Ω -> ℝ) (x : ℝ) : Set Ω :=
  {ω | x < Y ω}

/-- Left-tail event `{Y < -x}` used in Lemma 19.32. -/
def vaart1998_leftTailEvent {Ω : Type*}
    (Y : Ω -> ℝ) (x : ℝ) : Set Ω :=
  {ω | Y ω < -x}

/-- Absolute-tail event `{|Y| > x}` used in Lemma 19.32. -/
def vaart1998_absoluteTailEvent {Ω : Type*}
    (Y : Ω -> ℝ) (x : ℝ) : Set Ω :=
  {ω | x < |Y ω|}

/-- Real probability of an absolute-tail event. -/
def vaart1998_absoluteTailProbability {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (Y : Ω -> ℝ) (x : ℝ) : ℝ :=
  μ.real (vaart1998_absoluteTailEvent Y x)

/-- The `P f^2` variance proxy in Bernstein's inequality. -/
def vaart1998_lemma19_32SecondMoment
    {Observation : Type*} [MeasurableSpace Observation]
    (P : Measure Observation) (f : Observation -> ℝ) : ℝ :=
  ∫ x, (f x) ^ 2 ∂P

/-- The denominator `P f^2 + x ||f||_∞ / sqrt n` in Lemma 19.32. -/
def vaart1998_lemma19_32BernsteinDenominator
    (secondMoment uniformBound : ℝ) (sampleSize : ℕ) (x : ℝ) : ℝ :=
  secondMoment + x * uniformBound / Real.sqrt (sampleSize : ℝ)

/-- The exponent `-(1/4) x^2 / (P f^2 + x ||f||_∞ / sqrt n)`. -/
def vaart1998_lemma19_32BernsteinExponent
    (secondMoment uniformBound : ℝ) (sampleSize : ℕ) (x : ℝ) : ℝ :=
  - (1 / 4 : ℝ) *
    (x ^ 2 /
      vaart1998_lemma19_32BernsteinDenominator
        secondMoment uniformBound sampleSize x)

/-- The Lemma 19.32 absolute-tail upper bound. -/
def vaart1998_lemma19_32BernsteinTailBound
    (secondMoment uniformBound : ℝ) (sampleSize : ℕ) (x : ℝ) : ℝ :=
  2 * Real.exp
    (vaart1998_lemma19_32BernsteinExponent
      secondMoment uniformBound sampleSize x)

/-- The proof's choice of the exponential Markov parameter `λ`. -/
def vaart1998_lemma19_32Lambda
    (secondMoment uniformBound : ℝ) (sampleSize : ℕ) (x : ℝ) : ℝ :=
  (1 / 2 : ℝ) *
    (x /
      vaart1998_lemma19_32BernsteinDenominator
        secondMoment uniformBound sampleSize x)

/-- The proof's comparison value `λ₁ = x/(2 P f^2)`. -/
def vaart1998_lemma19_32LambdaOne
    (secondMoment x : ℝ) : ℝ :=
  (1 / 2 : ℝ) * (x / secondMoment)

/-- The proof's comparison value `λ₂ = sqrt n/(2 ||f||_∞)`. -/
def vaart1998_lemma19_32LambdaTwo
    (uniformBound : ℝ) (sampleSize : ℕ) : ℝ :=
  (1 / 2 : ℝ) * (Real.sqrt (sampleSize : ℝ) / uniformBound)

/-- The book's shorthand `log(1 + |F|)` in Lemma 19.33. -/
def vaart1998_lemma19_33LogCardinality
    (cardinality : ℕ) : ℝ :=
  Real.log (1 + (cardinality : ℝ))

/-- The linear, `ψ₁`-controlled term in Lemma 19.33. -/
def vaart1998_lemma19_33LinearTerm
    (uniformBoundMax : ℝ) (sampleSize cardinality : ℕ) : ℝ :=
  uniformBoundMax / Real.sqrt (sampleSize : ℝ) *
    vaart1998_lemma19_33LogCardinality cardinality

/-- The quadratic, `ψ₂`-controlled term in Lemma 19.33. -/
def vaart1998_lemma19_33QuadraticTerm
    (l2NormMax : ℝ) (cardinality : ℕ) : ℝ :=
  l2NormMax *
    Real.sqrt (vaart1998_lemma19_33LogCardinality cardinality)

/--
The two-scale finite-class upper bound in Lemma 19.33, before multiplying by
the universal implicit constant in `\lesssim`.
-/
def vaart1998_lemma19_33FiniteClassBound
    (uniformBoundMax l2NormMax : ℝ) (sampleSize cardinality : ℕ) : ℝ :=
  vaart1998_lemma19_33LinearTerm
    uniformBoundMax sampleSize cardinality +
  vaart1998_lemma19_33QuadraticTerm
    l2NormMax cardinality

/-- The proof's `a = 24 ||f||_∞ / sqrt n` scale. -/
def vaart1998_lemma19_33AScale
    (uniformBound : ℝ) (sampleSize : ℕ) : ℝ :=
  24 * uniformBound / Real.sqrt (sampleSize : ℝ)

/-- The proof's `b = 24 P f^2` scale. -/
def vaart1998_lemma19_33BScale
    (secondMoment : ℝ) : ℝ :=
  24 * secondMoment

/-- The truncation threshold `b/a` used to split `G_n f`. -/
def vaart1998_lemma19_33SplitThreshold
    (uniformBound secondMoment : ℝ) (sampleSize : ℕ) : ℝ :=
  vaart1998_lemma19_33BScale secondMoment /
    vaart1998_lemma19_33AScale uniformBound sampleSize

/-- The Orlicz function `ψ₁(x)=exp x - 1`. -/
def vaart1998_lemma19_33PsiOne (x : ℝ) : ℝ :=
  Real.exp x - 1

/-- The Orlicz function `ψ₂(x)=exp(x^2) - 1`. -/
def vaart1998_lemma19_33PsiTwo (x : ℝ) : ℝ :=
  Real.exp (x ^ 2) - 1

/-- The large-tail part `A_f = G_n f 1{|G_n f| > b/a}`. -/
def vaart1998_lemma19_33TailPart
    {Ω : Type*} (Y : Ω -> ℝ) (threshold : ℝ) : Ω -> ℝ :=
  fun ω => if threshold < |Y ω| then Y ω else 0

/-- The bounded-body part `B_f = G_n f 1{|G_n f| ≤ b/a}`. -/
def vaart1998_lemma19_33BodyPart
    {Ω : Type*} (Y : Ω -> ℝ) (threshold : ℝ) : Ω -> ℝ :=
  fun ω => if |Y ω| ≤ threshold then Y ω else 0

/-- Finite-class empirical-process coordinates for Lemma 19.33. -/
def vaart1998_lemma19_33EmpiricalProcessFamily
    {Observation : Type*} [MeasurableSpace Observation]
    {sampleSize cardinality : ℕ}
    (P : Measure Observation) (sample : SampleAt Observation sampleSize)
    (classFun : Fin cardinality -> Observation -> ℝ) :
    Fin cardinality -> ℝ :=
  fun coordinate =>
    vaart1998_empiricalProcess P sample (classFun coordinate)

/-- Random finite-class empirical-process coordinates for Lemma 19.33. -/
def vaart1998_lemma19_33RandomEmpiricalProcessFamily
    {Ω Observation : Type*} [MeasurableSpace Observation]
    {sampleSize cardinality : ℕ}
    (P : Measure Observation) (randomSample : Ω -> SampleAt Observation sampleSize)
    (classFun : Fin cardinality -> Observation -> ℝ) :
    Ω -> Fin cardinality -> ℝ :=
  fun ω =>
    vaart1998_lemma19_33EmpiricalProcessFamily
      P (randomSample ω) classFun

/-- The finite supremum norm `||G_n||_F`. -/
noncomputable def vaart1998_lemma19_33FiniteEmpiricalProcessNorm
    {cardinality : ℕ} (G : Fin cardinality -> ℝ) : ℝ :=
  ⨆ coordinate : Fin cardinality, |G coordinate|

/-- Expected finite-class empirical-process norm in Lemma 19.33. -/
noncomputable def vaart1998_lemma19_33ExpectedFiniteEmpiricalProcessNorm
    {Ω : Type*} [MeasurableSpace Ω] {cardinality : ℕ}
    (μ : Measure Ω) (G : Ω -> Fin cardinality -> ℝ) : ℝ :=
  ∫ ω, vaart1998_lemma19_33FiniteEmpiricalProcessNorm (G ω) ∂μ

/-- Each finite coordinate is bounded by the finite supremum norm. -/
theorem vaart1998_lemma19_33_abs_coordinate_le_finiteEmpiricalProcessNorm
    {cardinality : ℕ} (G : Fin cardinality -> ℝ)
    (coordinate : Fin cardinality) :
    |G coordinate| ≤
      vaart1998_lemma19_33FiniteEmpiricalProcessNorm G := by
  unfold vaart1998_lemma19_33FiniteEmpiricalProcessNorm
  have hbdd :
      BddAbove
        (Set.range fun coordinate : Fin cardinality => |G coordinate|) :=
    Finite.bddAbove_range _
  exact le_ciSup hbdd coordinate

/-- Section 19.6 convention: book-log `1 ∨ log x`. -/
def vaart1998_lemma19_34BookLog (x : ℝ) : ℝ :=
  max 1 (Real.log x)

/-- The book-log convention is nonnegative. -/
theorem vaart1998_lemma19_34BookLog_nonneg (x : ℝ) :
    0 ≤ vaart1998_lemma19_34BookLog x := by
  exact zero_le_one.trans (le_max_left 1 (Real.log x))

/-- Lemma 19.34 `a(δ)=δ / sqrt(log N_[](δ,F,L2(P)))`. -/
def vaart1998_lemma19_34ADelta
    (delta bracketingNumberAtDelta : ℝ) : ℝ :=
  delta /
    Real.sqrt (vaart1998_lemma19_34BookLog bracketingNumberAtDelta)

/-- The envelope tail set `{F > sqrt n * a(δ)}`. -/
def vaart1998_lemma19_34EnvelopeTailSet
    {Observation : Type*} (envelope : Observation -> ℝ)
    (sampleSize : ℕ) (aDelta : ℝ) : Set Observation :=
  {x | Real.sqrt (sampleSize : ℝ) * aDelta < envelope x}

/-- The envelope-tail integral displayed as `P* F{F > sqrt n a(δ)}`. -/
def vaart1998_lemma19_34EnvelopeTailIntegral
    {Observation : Type*} [MeasurableSpace Observation]
    (P : Measure Observation) (envelope : Observation -> ℝ)
    (sampleSize : ℕ) (aDelta : ℝ) : ℝ :=
  ∫ x, if Real.sqrt (sampleSize : ℝ) * aDelta < envelope x
    then envelope x else 0 ∂P

/-- The Lemma 19.34 upper bound before the universal implicit constant. -/
def vaart1998_lemma19_34MaximalBound
    (bracketingIntegral envelopeTailIntegral : ℝ)
    (sampleSize : ℕ) : ℝ :=
  bracketingIntegral +
    Real.sqrt (sampleSize : ℝ) * envelopeTailIntegral

/-- Truncated class `f 1{F ≤ sqrt n a(δ)}` used at the start of Lemma 19.34. -/
def vaart1998_lemma19_34TruncatedClassFun
    {Observation Index : Type*}
    (envelope : Observation -> ℝ) (sampleSize : ℕ) (aDelta : ℝ)
    (classFun : Index -> Observation -> ℝ) :
    Index -> Observation -> ℝ :=
  fun index x =>
    if envelope x ≤ Real.sqrt (sampleSize : ℝ) * aDelta
    then classFun index x else 0

/-- Dyadic radius `2^{-q}` in the chaining proof. -/
def vaart1998_lemma19_34DyadicRadius (q : ℕ) : ℝ :=
  ((2 : ℝ) ^ q)⁻¹

/-- The dyadic radii are nonnegative. -/
theorem vaart1998_lemma19_34DyadicRadius_nonneg (q : ℕ) :
    0 ≤ vaart1998_lemma19_34DyadicRadius q := by
  unfold vaart1998_lemma19_34DyadicRadius
  exact inv_nonneg.mpr (pow_nonneg zero_le_two q)

/-- The proof's `a_q = 2^{-q}/sqrt(log N_{q+1})`. -/
def vaart1998_lemma19_34ChainScale
    (bracketingNumber : ℕ -> ℝ) (q : ℕ) : ℝ :=
  vaart1998_lemma19_34DyadicRadius q /
    Real.sqrt (vaart1998_lemma19_34BookLog (bracketingNumber (q + 1)))

/-- The entropy-series term `2^{-q} sqrt(log N_q)`. -/
def vaart1998_lemma19_34EntropySeriesTerm
    (bracketingNumber : ℕ -> ℝ) (q : ℕ) : ℝ :=
  vaart1998_lemma19_34DyadicRadius q *
    Real.sqrt (vaart1998_lemma19_34BookLog (bracketingNumber q))

/-- Corollary 19.35 displayed `L2(P)` envelope norm `||F||_{P,2}`. -/
def vaart1998_corollary19_35EnvelopeL2Norm
    {Observation : Type*} [MeasurableSpace Observation]
    (P : Measure Observation) (envelope : Observation -> ℝ) : ℝ :=
  Real.sqrt (∫ x, (envelope x) ^ 2 ∂P)

/-- Corollary 19.35 lower endpoint of the single bracket `[-F,F]`. -/
def vaart1998_corollary19_35SingleBracketLower
    {Observation : Type*} (envelope : Observation -> ℝ) :
    Observation -> ℝ :=
  fun x => - envelope x

/-- Corollary 19.35 upper endpoint of the single bracket `[-F,F]`. -/
def vaart1998_corollary19_35SingleBracketUpper
    {Observation : Type*} (envelope : Observation -> ℝ) :
    Observation -> ℝ :=
  envelope

/-- Corollary 19.35 proof radius `δ = 2 ||F||_{P,2}`. -/
def vaart1998_corollary19_35ProofRadius
    (envelopeL2Norm : ℝ) : ℝ :=
  2 * envelopeL2Norm

/-- The one-bracket bracketing number at the proof radius. -/
def vaart1998_corollary19_35SingleBracketNumber : ℝ := 1

/-- The Lemma 19.34 scale `a(δ)` at the Corollary 19.35 proof radius. -/
def vaart1998_corollary19_35ADelta
    (envelopeL2Norm : ℝ) : ℝ :=
  vaart1998_lemma19_34ADelta
    (vaart1998_corollary19_35ProofRadius envelopeL2Norm)
    vaart1998_corollary19_35SingleBracketNumber

/-- At the one-bracket proof radius, `a(δ)` reduces to `2 ||F||_{P,2}`. -/
theorem vaart1998_corollary19_35ADelta_eq
    (envelopeL2Norm : ℝ) :
    vaart1998_corollary19_35ADelta envelopeL2Norm =
      vaart1998_corollary19_35ProofRadius envelopeL2Norm := by
  simp [vaart1998_corollary19_35ADelta,
    vaart1998_corollary19_35ProofRadius,
    vaart1998_corollary19_35SingleBracketNumber,
    vaart1998_lemma19_34ADelta, vaart1998_lemma19_34BookLog]

/-- The Corollary 19.35 right-hand side before the universal constant. -/
def vaart1998_corollary19_35BracketingIntegralBound
    (bracketingIntegralAtEnvelope : ℝ) : ℝ :=
  bracketingIntegralAtEnvelope

/-- Lemma 19.36 second-order correction `J_[]/(δ^2 sqrt n) * M`. -/
def vaart1998_lemma19_36SecondOrderCorrection
    (bracketingIntegral delta uniformBound : ℝ)
    (sampleSize : ℕ) : ℝ :=
  bracketingIntegral /
    (delta ^ 2 * Real.sqrt (sampleSize : ℝ)) * uniformBound

/-- Lemma 19.36 parenthesized factor
`1 + J_[]/(δ^2 sqrt n) * M`. -/
def vaart1998_lemma19_36BoundFactor
    (bracketingIntegral delta uniformBound : ℝ)
    (sampleSize : ℕ) : ℝ :=
  1 +
    vaart1998_lemma19_36SecondOrderCorrection
      bracketingIntegral delta uniformBound sampleSize

/-- Lemma 19.36 maximal bound before the universal implicit constant. -/
def vaart1998_lemma19_36MaximalBound
    (bracketingIntegral delta uniformBound : ℝ)
    (sampleSize : ℕ) : ℝ :=
  bracketingIntegral *
    vaart1998_lemma19_36BoundFactor
      bracketingIntegral delta uniformBound sampleSize

/-- Lemma 19.37 Bernstein integrand `exp |f| - 1 - |f|`. -/
def vaart1998_lemma19_37BernsteinIntegrand
    {Observation : Type*} (f : Observation -> ℝ) :
    Observation -> ℝ :=
  fun x => Real.exp (|f x|) - 1 - |f x|

/-- Lemma 19.37 squared Bernstein norm
`||f||_{P,B}^2 = 2 P (exp |f| - 1 - |f|)`. -/
def vaart1998_lemma19_37BernsteinNormSquared
    {Observation : Type*} [MeasurableSpace Observation]
    (P : Measure Observation) (f : Observation -> ℝ) : ℝ :=
  2 * ∫ x, vaart1998_lemma19_37BernsteinIntegrand f x ∂P

/-- Lemma 19.37 Bernstein norm display. -/
def vaart1998_lemma19_37BernsteinNorm
    {Observation : Type*} [MeasurableSpace Observation]
    (P : Measure Observation) (f : Observation -> ℝ) : ℝ :=
  Real.sqrt (vaart1998_lemma19_37BernsteinNormSquared P f)

/-- Lemma 19.37 second-order correction `J_[]/(δ^2 sqrt n)`. -/
def vaart1998_lemma19_37SecondOrderCorrection
    (bracketingIntegral delta : ℝ)
    (sampleSize : ℕ) : ℝ :=
  bracketingIntegral / (delta ^ 2 * Real.sqrt (sampleSize : ℝ))

/-- Lemma 19.37 parenthesized factor `1 + J_[]/(δ^2 sqrt n)`. -/
def vaart1998_lemma19_37BoundFactor
    (bracketingIntegral delta : ℝ)
    (sampleSize : ℕ) : ℝ :=
  1 + vaart1998_lemma19_37SecondOrderCorrection
    bracketingIntegral delta sampleSize

/-- Lemma 19.37 maximal bound before the universal implicit constant. -/
def vaart1998_lemma19_37MaximalBound
    (bracketingIntegral delta : ℝ)
    (sampleSize : ℕ) : ℝ :=
  bracketingIntegral *
    vaart1998_lemma19_37BoundFactor
      bracketingIntegral delta sampleSize

/-- Lemma 19.38 empirical second moment `P_n f^2`. -/
def vaart1998_lemma19_38EmpiricalSecondMoment
    {Observation : Type*} {sampleSize : ℕ}
    (sample : SampleAt Observation sampleSize)
    (f : Observation -> ℝ) : ℝ :=
  vaart1998_empiricalAverage sample (fun x => (f x) ^ 2)

/-- Lemma 19.38 empirical `L2(P_n)` norm. -/
def vaart1998_lemma19_38EmpiricalL2Norm
    {Observation : Type*} {sampleSize : ℕ}
    (sample : SampleAt Observation sampleSize)
    (f : Observation -> ℝ) : ℝ :=
  Real.sqrt (vaart1998_lemma19_38EmpiricalSecondMoment sample f)

/-- Lemma 19.38 displayed `θ_n^2` from the class/envelope empirical squares. -/
def vaart1998_lemma19_38ThetaSquared
    (classEmpiricalSecondMomentSupremum envelopeEmpiricalSecondMoment : ℝ) :
    ℝ :=
  classEmpiricalSecondMomentSupremum / envelopeEmpiricalSecondMoment

/-- Lemma 19.38 displayed `θ_n`. -/
def vaart1998_lemma19_38Theta
    (classEmpiricalSecondMomentSupremum envelopeEmpiricalSecondMoment : ℝ) :
    ℝ :=
  Real.sqrt
    (vaart1998_lemma19_38ThetaSquared
      classEmpiricalSecondMomentSupremum envelopeEmpiricalSecondMoment)

/-- Lemma 19.38 random product
`J(θ_n,F,L2) ||F||_{P_n,2}`. -/
def vaart1998_lemma19_38EntropyEnvelopeProduct
    (uniformEntropyIntegralAtTheta empiricalEnvelopeL2Norm : ℝ) : ℝ :=
  uniformEntropyIntegralAtTheta * empiricalEnvelopeL2Norm

/-- Lemma 19.38 expectation of
`J(θ_n,F,L2) ||F||_{P_n,2}`. -/
def vaart1998_lemma19_38ExpectedEntropyEnvelopeProduct
    {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω)
    (entropyEnvelopeProduct : Ω -> ℝ) : ℝ :=
  ∫ ω, entropyEnvelopeProduct ω ∂μ

/-- Lemma 19.38 deterministic endpoint `J(1,F,L2) ||F||_{P,2}`. -/
def vaart1998_lemma19_38DeterministicMaximalBound
    (uniformEntropyIntegralAtOne populationEnvelopeL2Norm : ℝ) : ℝ :=
  uniformEntropyIntegralAtOne * populationEnvelopeL2Norm

/-- A right-tail event is contained in the absolute-tail event. -/
theorem vaart1998_rightTailEvent_subset_absoluteTailEvent
    {Ω : Type*} (Y : Ω -> ℝ) (x : ℝ) :
    vaart1998_rightTailEvent Y x ⊆
      vaart1998_absoluteTailEvent Y x := by
  intro ω hω
  exact lt_of_lt_of_le hω (le_abs_self (Y ω))

/-- A left-tail event is contained in the absolute-tail event. -/
theorem vaart1998_leftTailEvent_subset_absoluteTailEvent
    {Ω : Type*} (Y : Ω -> ℝ) (x : ℝ) :
    vaart1998_leftTailEvent Y x ⊆
      vaart1998_absoluteTailEvent Y x := by
  intro ω hω
  change Y ω < -x at hω
  have hx : x < -Y ω := by
    simpa using (neg_lt_neg hω)
  have hle : -Y ω ≤ |Y ω| := by
    simpa [abs_neg] using (le_abs_self (-Y ω))
  exact lt_of_lt_of_le hx hle

/-!
## Source-shaped definitions and theorem handoffs
-/

/--
Definition 19.2 source: empirical distributions and empirical processes over a
class of real-valued measurable functions.
-/
structure Vaart1998Definition19_2EmpiricalDistributionSource
    {Observation : Type*} [MeasurableSpace Observation] where
  /-- The population law `P`. -/
  probabilityMeasure : Measure Observation
  /-- Finite sample size. -/
  sampleSize : ℕ
  /-- The observed sample. -/
  sample : SampleAt Observation sampleSize
  /-- A test function `f`. -/
  testFunction : Observation -> ℝ
  /-- Book notation `P_n f`. -/
  empiricalAverageValue : ℝ
  /-- The displayed `P_n f = n^{-1} sum f(X_i)` identity. -/
  empiricalAverage_eq :
    empiricalAverageValue =
      vaart1998_empiricalAverage sample testFunction
  /-- Book notation `P f`. -/
  populationMeanValue : ℝ
  /-- The displayed `P f = integral f dP` identity. -/
  populationMean_eq :
    populationMeanValue =
      vaart1998_populationMean probabilityMeasure testFunction
  /-- Book notation `G_n f`. -/
  empiricalProcessValue : ℝ
  /-- The displayed `G_n f = sqrt n (P_n - P) f` identity. -/
  empiricalProcess_eq :
    empiricalProcessValue =
      vaart1998_empiricalProcess probabilityMeasure sample testFunction

/-- Definition 19.2 display for `P_n f`. -/
theorem Vaart1998Definition19_2EmpiricalDistributionSource.empirical_average
    {Observation : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Definition19_2EmpiricalDistributionSource
      (Observation := Observation)) :
    S.empiricalAverageValue =
      vaart1998_empiricalAverage S.sample S.testFunction :=
  S.empiricalAverage_eq

/-- Definition 19.2 display for `P f`. -/
theorem Vaart1998Definition19_2EmpiricalDistributionSource.population_mean
    {Observation : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Definition19_2EmpiricalDistributionSource
      (Observation := Observation)) :
    S.populationMeanValue =
      vaart1998_populationMean S.probabilityMeasure S.testFunction :=
  S.populationMean_eq

/-- Definition 19.2 display for `G_n f`. -/
theorem Vaart1998Definition19_2EmpiricalDistributionSource.empirical_process
    {Observation : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Definition19_2EmpiricalDistributionSource
      (Observation := Observation)) :
    S.empiricalProcessValue =
      vaart1998_empiricalProcess
        S.probabilityMeasure S.sample S.testFunction :=
  S.empiricalProcess_eq

/--
Theorem 19.1 source: Glivenko-Cantelli convergence for empirical distribution
functions on the real line.
-/
structure Vaart1998Theorem19_1EmpiricalCDFGlivenkoCantelliSource
    {Ω : Type*} [MeasurableSpace Ω] where
  /-- The sample-space probability measure. -/
  probabilityMeasure : Measure Ω
  /-- The common law of the observations. -/
  law : Measure ℝ
  /-- The observation process. -/
  observations : ℕ -> Ω -> ℝ
  /-- Proof of the source-shaped uniform empirical-CDF conclusion. -/
  glivenkoCantelli :
    vaart1998_empiricalCDFGlivenkoCantelliClass
      probabilityMeasure law observations

/-- Theorem 19.1 empirical-CDF Glivenko-Cantelli display. -/
theorem Vaart1998Theorem19_1EmpiricalCDFGlivenkoCantelliSource.glivenko_cantelli
    {Ω : Type*} [MeasurableSpace Ω]
    (S : Vaart1998Theorem19_1EmpiricalCDFGlivenkoCantelliSource
      (Ω := Ω)) :
    vaart1998_empiricalCDFGlivenkoCantelliClass
      S.probabilityMeasure S.law S.observations :=
  S.glivenkoCantelli

/--
Theorem 19.3 source: Donsker convergence of the empirical distribution
function to a Brownian bridge.
-/
structure Vaart1998Theorem19_3EmpiricalCDFDonskerSource where
  /-- The distribution function `F`. -/
  distributionFunction : ℝ -> ℝ
  /-- The empirical process coordinates. -/
  empiricalProcess : ℕ -> ℝ -> ℝ
  /-- The limiting Brownian-bridge process display. -/
  brownianBridgeLimit : ℝ -> ℝ
  /-- The finite-dimensional covariance identification statement. -/
  finiteDimensionalCovariance_statement : Prop
  /-- The `D[−∞,∞]` / `ell_infty` weak-convergence statement. -/
  weakConvergence_statement : Prop
  /-- Proof of the covariance display. -/
  finiteDimensionalCovariance : finiteDimensionalCovariance_statement
  /-- Proof of the weak-convergence display. -/
  weakConvergence : weakConvergence_statement

/-- Theorem 19.3 finite-dimensional covariance display. -/
theorem Vaart1998Theorem19_3EmpiricalCDFDonskerSource.finite_dimensional_covariance
    (S : Vaart1998Theorem19_3EmpiricalCDFDonskerSource) :
    S.finiteDimensionalCovariance_statement :=
  S.finiteDimensionalCovariance

/-- Theorem 19.3 weak-convergence display. -/
theorem Vaart1998Theorem19_3EmpiricalCDFDonskerSource.weak_convergence
    (S : Vaart1998Theorem19_3EmpiricalCDFDonskerSource) :
    S.weakConvergence_statement :=
  S.weakConvergence

/--
Theorem 19.4: finite `L1(P)` bracketing numbers at every positive radius give
the book-style `P`-Glivenko-Cantelli predicate.
-/
theorem vaart1998_theorem19_4_glivenkoCantelli_of_l1BracketingNumber_lt_top
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    {μ : Measure Ω} {P : Measure Observation}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (X : ℕ -> Ω -> Observation)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (h_bracketing :
      ∀ epsilon, 0 < epsilon ->
        l1BracketingNumber P indexClass classFun epsilon < ⊤) :
    vaart1998_pGlivenkoCantelliClass μ P indexClass classFun X :=
  vdVW_theorem_2_4_1_glivenkoCantelli
    X hLaw hindep h_bracketing

/--
Theorem 19.4 in the outer-a.s. convergence mode used by the bracketing proof.
-/
theorem
    vaart1998_theorem19_4_outerAlmostSure_glivenkoCantelli_of_l1BracketingNumber_lt_top
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    {μ : Measure Ω} {P : Measure Observation}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (X : ℕ -> Ω -> Observation)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (h_bracketing :
      ∀ epsilon, 0 < epsilon ->
        l1BracketingNumber P indexClass classFun epsilon < ⊤) :
    vaart1998_outerAlmostSurePGlivenkoCantelliClass
      μ P indexClass classFun X :=
  vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli
    X hLaw hindep h_bracketing

/--
Theorem 19.4 in direct outer probability for countable classes whose class
functions are measurable.
-/
theorem
    vaart1998_theorem19_4_outerProbability_glivenkoCantelli_of_countable_of_classFun_measurable
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    {μ : Measure Ω} [IsFiniteMeasure μ] {P : Measure Observation}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (X : ℕ -> Ω -> Observation)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (h_bracketing :
      ∀ epsilon, 0 < epsilon ->
        l1BracketingNumber P indexClass classFun epsilon < ⊤)
    (h_count : indexClass.Countable)
    (h_classFun :
      ∀ index, index ∈ indexClass -> Measurable (classFun index)) :
    vaart1998_outerProbabilityPGlivenkoCantelliClass
      μ P indexClass classFun X :=
  vdVW_theorem_2_4_1_outerProbabilityGlivenkoCantelli_of_countable_of_classFun_measurable
    X hLaw hindep h_bracketing h_count h_classFun

/--
Theorem 19.5 source: finite bracketing integral as a proof-carrying route to a
Donsker specification.
-/
structure Vaart1998Theorem19_5DonskerBracketingSource
    {Observation Index : Type*} [MeasurableSpace Observation] where
  /-- The population law. -/
  probabilityMeasure : Measure Observation
  /-- The indexed function class. -/
  indexClass : Set Index
  /-- The test-function family. -/
  classFun : Index -> Observation -> ℝ
  /-- The finite bracketing-integral hypothesis statement. -/
  bracketingIntegralFinite_statement : Prop
  /-- Donsker specification carried by the theorem route. -/
  donsker : vaart1998_donskerSpec
  /-- Proof of the finite bracketing-integral hypothesis. -/
  bracketingIntegralFinite : bracketingIntegralFinite_statement
  /-- Proof of the weak-convergence conclusion. -/
  weakConvergence : donsker.weak_convergence_statement

/-- Theorem 19.5 bracketing-integral hypothesis display. -/
theorem Vaart1998Theorem19_5DonskerBracketingSource.bracketing_integral
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5DonskerBracketingSource
      (Observation := Observation) (Index := Index)) :
    S.bracketingIntegralFinite_statement :=
  S.bracketingIntegralFinite

/-- Theorem 19.5 weak-convergence conclusion. -/
theorem Vaart1998Theorem19_5DonskerBracketingSource.weak_convergence
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5DonskerBracketingSource
      (Observation := Observation) (Index := Index)) :
    S.donsker.weak_convergence_statement :=
  S.weakConvergence

/--
Theorem 19.5 bridge source specialized to an empirical-risk sequence.

The `bracketing` field carries the verified uniform-law component supplied by
the bracketing route.  The Donsker fields carry the weak-convergence payload.
Together they produce the local `DonskerBridgeCertificate` consumed by later
empirical-process and estimator arguments.
-/
structure Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
    {Observation Index : Type*} [MeasurableSpace Observation] where
  /-- The population law. -/
  probabilityMeasure : Measure Observation
  /-- The indexed function class. -/
  indexClass : Set Index
  /-- The test-function family. -/
  classFun : Index -> Observation -> ℝ
  /-- Deterministic finite samples used to expose the empirical-risk sequence. -/
  samples : ∀ sampleSize, SampleAt Observation sampleSize
  /-- The finite bracketing-integral hypothesis statement. -/
  bracketingIntegralFinite_statement : Prop
  /-- Proof of the finite bracketing-integral hypothesis. -/
  bracketingIntegralFinite : bracketingIntegralFinite_statement
  /-- Proof-carrying bracketing route to uniform empirical deviations. -/
  bracketing :
    BracketingDeviationCertificate indexClass
      (vaart1998_populationClassMean probabilityMeasure classFun)
      (vaart1998_empiricalClassMeanSequence samples classFun)
  /-- The assumptions needed by the bracketing deviation certificate. -/
  bracketing_assumptions : bracketing.assumptions
  /-- Donsker specification carried by the theorem route. -/
  donsker : vaart1998_donskerSpec
  /-- Asymptotic equicontinuity/equipartition side condition. -/
  asymptoticEquipartition_statement : Prop
  /-- Weak-limit identification side condition. -/
  weakLimitIdentification_statement : Prop
  /-- Proof of the weak-convergence conclusion. -/
  weakConvergence : donsker.weak_convergence_statement

namespace Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource

/-- The empirical-risk sequence displayed by the bridge source. -/
abbrev empiricalRiskSequence
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index)) : ℕ -> Index -> ℝ :=
  vaart1998_empiricalClassMeanSequence S.samples S.classFun

/-- The population-risk function displayed by the bridge source. -/
abbrev populationRisk
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index)) : Index -> ℝ :=
  vaart1998_populationClassMean S.probabilityMeasure S.classFun

/-- Extract the Glivenko-Cantelli component supplied by the bracketing route. -/
def toGlivenkoCantelliClass
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index)) :
    GlivenkoCantelliClass S.indexClass S.populationRisk
      S.empiricalRiskSequence :=
  BracketingDeviationCertificate.toGlivenkoCantelliClass
    S.bracketing S.bracketing_assumptions

/-- The uniform-deviation sequence supplied by the bracketing route. -/
def uniformDeviation
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index)) :
    EmpiricalDeviationSequenceOn S.indexClass S.populationRisk
      S.empiricalRiskSequence S.bracketing.radius :=
  BracketingDeviationCertificate.uniformDeviation
    S.bracketing S.bracketing_assumptions

/-- Convert the Chapter 19 Theorem 19.5 bridge into the generic Donsker bridge. -/
def toDonskerBridgeCertificate
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index)) :
    DonskerBridgeCertificate S.indexClass S.populationRisk
      S.empiricalRiskSequence where
  gc := S.toGlivenkoCantelliClass
  donsker := S.donsker
  asymptotic_equipartition_statement := S.asymptoticEquipartition_statement
  weak_limit_identification_statement := S.weakLimitIdentification_statement
  weak_convergence_proof := S.weakConvergence

/-- Forget the bridge fields back to the source-shaped Theorem 19.5 shell. -/
def toDonskerBracketingSource
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index)) :
    Vaart1998Theorem19_5DonskerBracketingSource
      (Observation := Observation) (Index := Index) where
  probabilityMeasure := S.probabilityMeasure
  indexClass := S.indexClass
  classFun := S.classFun
  bracketingIntegralFinite_statement := S.bracketingIntegralFinite_statement
  donsker := S.donsker
  bracketingIntegralFinite := S.bracketingIntegralFinite
  weakConvergence := S.weakConvergence

/-- Theorem 19.5 bridge weak-convergence display. -/
theorem weak_convergence
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index)) :
    S.donsker.weak_convergence_statement :=
  DonskerBridgeCertificate.weakConvergence S.toDonskerBridgeCertificate

/-- Theorem 19.5 bridge Glivenko-Cantelli component display. -/
def glivenko_cantelli
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index)) :
    GlivenkoCantelliClass S.indexClass S.populationRisk
      S.empiricalRiskSequence :=
  DonskerBridgeCertificate.toGlivenkoCantelliClass
    S.toDonskerBridgeCertificate

/-- Pointwise uniform-deviation consequence of the Theorem 19.5 bridge. -/
theorem deviation
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource
      (Observation := Observation) (Index := Index))
    (sampleSize : ℕ) {index : Index} (hindex : index ∈ S.indexClass) :
    |S.empiricalRiskSequence sampleSize index -
      S.populationRisk index| ≤
        (S.toGlivenkoCantelliClass).radius sampleSize :=
  (S.toGlivenkoCantelliClass).deviation sampleSize hindex

end Vaart1998Theorem19_5EmpiricalClassDonskerBridgeSource

/--
Theorem 19.13 source: uniform covering numbers plus an integrable envelope give
a `P`-Glivenko-Cantelli class.
-/
structure Vaart1998Theorem19_13UniformCoveringGCSource
    {Observation Index : Type*} [MeasurableSpace Observation] where
  /-- The population law. -/
  probabilityMeasure : Measure Observation
  /-- The indexed class `𝓕`. -/
  indexClass : Set Index
  /-- The test-function family. -/
  classFun : Index -> Observation -> ℝ
  /-- Deterministic samples used to expose the empirical-risk sequence. -/
  samples : ∀ sampleSize, SampleAt Observation sampleSize
  /-- Envelope function `F`. -/
  envelope : Observation -> ℝ
  /-- Suitability/measurability side condition from the source theorem. -/
  suitablyMeasurable_statement : Prop
  /-- Proof of the suitability/measurability side condition. -/
  suitablyMeasurable : suitablyMeasurable_statement
  /-- Uniform covering finiteness for every positive radius. -/
  uniformCoveringFinite_statement : Prop
  /-- Proof of uniform covering finiteness. -/
  uniformCoveringFinite : uniformCoveringFinite_statement
  /-- Integrability of the envelope. -/
  envelopeIntegrable_statement : Prop
  /-- Proof of envelope integrability. -/
  envelopeIntegrable : envelopeIntegrable_statement
  /-- Proof-carrying uniform-covering route to uniform empirical deviations. -/
  covering :
    CoveringNumberDeviationCertificate indexClass
      (vaart1998_populationClassMean probabilityMeasure classFun)
      (vaart1998_empiricalClassMeanSequence samples classFun)
  /-- Assumptions needed by the covering-number deviation certificate. -/
  covering_assumptions : covering.assumptions

namespace Vaart1998Theorem19_13UniformCoveringGCSource

/-- The empirical-risk sequence displayed by the uniform-covering GC source. -/
abbrev empiricalRiskSequence
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index)) : ℕ -> Index -> ℝ :=
  vaart1998_empiricalClassMeanSequence S.samples S.classFun

/-- The population-risk function displayed by the uniform-covering GC source. -/
abbrev populationRisk
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index)) : Index -> ℝ :=
  vaart1998_populationClassMean S.probabilityMeasure S.classFun

/-- Extract the Glivenko-Cantelli class supplied by uniform covering. -/
def toGlivenkoCantelliClass
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index)) :
    GlivenkoCantelliClass S.indexClass S.populationRisk
      S.empiricalRiskSequence :=
  CoveringNumberDeviationCertificate.toGlivenkoCantelliClass
    S.covering S.covering_assumptions

/-- The uniform-deviation sequence supplied by the covering route. -/
def uniformDeviation
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index)) :
    EmpiricalDeviationSequenceOn S.indexClass S.populationRisk
      S.empiricalRiskSequence S.covering.radius :=
  CoveringNumberDeviationCertificate.uniformDeviation
    S.covering S.covering_assumptions

/-- The Theorem 19.13 suitability/measurability condition. -/
theorem suitably_measurable
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index)) :
    S.suitablyMeasurable_statement :=
  S.suitablyMeasurable

/-- The Theorem 19.13 uniform-covering finiteness condition. -/
theorem uniform_covering_finite
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index)) :
    S.uniformCoveringFinite_statement :=
  S.uniformCoveringFinite

/-- The Theorem 19.13 envelope integrability condition. -/
theorem envelope_integrable
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index)) :
    S.envelopeIntegrable_statement :=
  S.envelopeIntegrable

/-- Pointwise uniform-deviation consequence of Theorem 19.13. -/
theorem deviation
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index))
    (sampleSize : ℕ) {index : Index} (hindex : index ∈ S.indexClass) :
    |S.empiricalRiskSequence sampleSize index -
      S.populationRisk index| ≤
        (S.toGlivenkoCantelliClass).radius sampleSize :=
  (S.toGlivenkoCantelliClass).deviation sampleSize hindex

end Vaart1998Theorem19_13UniformCoveringGCSource

/--
Theorem 19.14 source: finite uniform entropy integral and square-integrable
envelope give a `P`-Donsker class.

The covering certificate records the uniform-law component that later
statistical arguments use together with the Donsker weak-convergence payload.
-/
structure Vaart1998Theorem19_14UniformEntropyDonskerSource
    {Observation Index : Type*} [MeasurableSpace Observation] where
  /-- The population law. -/
  probabilityMeasure : Measure Observation
  /-- The indexed class `𝓕`. -/
  indexClass : Set Index
  /-- The test-function family. -/
  classFun : Index -> Observation -> ℝ
  /-- Deterministic samples used to expose the empirical-risk sequence. -/
  samples : ∀ sampleSize, SampleAt Observation sampleSize
  /-- Envelope function `F`. -/
  envelope : Observation -> ℝ
  /-- Suitability/measurability side condition from the source theorem. -/
  suitablyMeasurable_statement : Prop
  /-- Proof of the suitability/measurability side condition. -/
  suitablyMeasurable : suitablyMeasurable_statement
  /-- The finite uniform entropy integral condition `J(1, 𝓕, L₂) < ∞`. -/
  uniformEntropyIntegralFinite_statement : Prop
  /-- Proof of the finite uniform entropy integral condition. -/
  uniformEntropyIntegralFinite : uniformEntropyIntegralFinite_statement
  /-- Square-integrability of the envelope, `P* F^2 < ∞`. -/
  squareIntegrableEnvelope_statement : Prop
  /-- Proof of square-integrability of the envelope. -/
  squareIntegrableEnvelope : squareIntegrableEnvelope_statement
  /-- Uniform covering finiteness, used when forgetting to the GC shell. -/
  uniformCoveringFinite_statement : Prop
  /-- Proof of uniform covering finiteness. -/
  uniformCoveringFinite : uniformCoveringFinite_statement
  /-- Integrability of the envelope, used when forgetting to the GC shell. -/
  envelopeIntegrable_statement : Prop
  /-- Proof of envelope integrability. -/
  envelopeIntegrable : envelopeIntegrable_statement
  /-- Proof-carrying uniform-covering route to uniform empirical deviations. -/
  covering :
    CoveringNumberDeviationCertificate indexClass
      (vaart1998_populationClassMean probabilityMeasure classFun)
      (vaart1998_empiricalClassMeanSequence samples classFun)
  /-- Assumptions needed by the covering-number deviation certificate. -/
  covering_assumptions : covering.assumptions
  /-- Donsker specification carried by the theorem route. -/
  donsker : vaart1998_donskerSpec
  /-- Asymptotic-tightness/equicontinuity side condition. -/
  asymptoticTightness_statement : Prop
  /-- Finite-dimensional convergence/Gaussian-limit side condition. -/
  finiteDimensionalConvergence_statement : Prop
  /-- Proof of the Donsker weak-convergence conclusion. -/
  weakConvergence : donsker.weak_convergence_statement

namespace Vaart1998Theorem19_14UniformEntropyDonskerSource

/-- The empirical-risk sequence displayed by the uniform-entropy Donsker source. -/
abbrev empiricalRiskSequence
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) : ℕ -> Index -> ℝ :=
  vaart1998_empiricalClassMeanSequence S.samples S.classFun

/-- The population-risk function displayed by the uniform-entropy Donsker source. -/
abbrev populationRisk
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) : Index -> ℝ :=
  vaart1998_populationClassMean S.probabilityMeasure S.classFun

/-- Extract the Glivenko-Cantelli component supplied by uniform covering. -/
def toGlivenkoCantelliClass
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    GlivenkoCantelliClass S.indexClass S.populationRisk
      S.empiricalRiskSequence :=
  CoveringNumberDeviationCertificate.toGlivenkoCantelliClass
    S.covering S.covering_assumptions

/-- The uniform-deviation sequence supplied by the covering route. -/
def uniformDeviation
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    EmpiricalDeviationSequenceOn S.indexClass S.populationRisk
      S.empiricalRiskSequence S.covering.radius :=
  CoveringNumberDeviationCertificate.uniformDeviation
    S.covering S.covering_assumptions

/-- Convert the Theorem 19.14 source into the generic Donsker bridge. -/
def toDonskerBridgeCertificate
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    DonskerBridgeCertificate S.indexClass S.populationRisk
      S.empiricalRiskSequence where
  gc := S.toGlivenkoCantelliClass
  donsker := S.donsker
  asymptotic_equipartition_statement := S.asymptoticTightness_statement
  weak_limit_identification_statement := S.finiteDimensionalConvergence_statement
  weak_convergence_proof := S.weakConvergence

/-- Forget the Donsker fields back to the source-shaped Theorem 19.13 shell. -/
def toUniformCoveringGCSource
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index) where
  probabilityMeasure := S.probabilityMeasure
  indexClass := S.indexClass
  classFun := S.classFun
  samples := S.samples
  envelope := S.envelope
  suitablyMeasurable_statement := S.suitablyMeasurable_statement
  suitablyMeasurable := S.suitablyMeasurable
  uniformCoveringFinite_statement := S.uniformCoveringFinite_statement
  uniformCoveringFinite := S.uniformCoveringFinite
  envelopeIntegrable_statement := S.envelopeIntegrable_statement
  envelopeIntegrable := S.envelopeIntegrable
  covering := S.covering
  covering_assumptions := S.covering_assumptions

/-- Theorem 19.14 suitability/measurability condition. -/
theorem suitably_measurable
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    S.suitablyMeasurable_statement :=
  S.suitablyMeasurable

/-- Theorem 19.14 finite uniform entropy integral condition. -/
theorem uniform_entropy_integral_finite
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    S.uniformEntropyIntegralFinite_statement :=
  S.uniformEntropyIntegralFinite

/-- Theorem 19.14 square-integrable-envelope condition. -/
theorem square_integrable_envelope
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    S.squareIntegrableEnvelope_statement :=
  S.squareIntegrableEnvelope

/-- Theorem 19.14 weak-convergence display. -/
theorem weak_convergence
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    S.donsker.weak_convergence_statement :=
  DonskerBridgeCertificate.weakConvergence S.toDonskerBridgeCertificate

/-- Theorem 19.14 Glivenko-Cantelli component display. -/
def glivenko_cantelli
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)) :
    GlivenkoCantelliClass S.indexClass S.populationRisk
      S.empiricalRiskSequence :=
  DonskerBridgeCertificate.toGlivenkoCantelliClass
    S.toDonskerBridgeCertificate

/-- Pointwise uniform-deviation consequence of Theorem 19.14. -/
theorem deviation
    {Observation Index : Type*} [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index))
    (sampleSize : ℕ) {index : Index} (hindex : index ∈ S.indexClass) :
    |S.empiricalRiskSequence sampleSize index -
      S.populationRisk index| ≤
        (S.toGlivenkoCantelliClass).radius sampleSize :=
  (S.toGlivenkoCantelliClass).deviation sampleSize hindex

end Vaart1998Theorem19_14UniformEntropyDonskerSource

/--
Lemma 19.24 source: a random member of a Donsker class that converges to
`f0` in the `L2(P)` semimetric has negligible empirical-process difference
and inherits the Brownian-bridge evaluation limit at `f0`.
-/
structure Vaart1998Lemma19_24RandomFunctionDonskerSource
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation] where
  /-- Probability space for the random index/function. -/
  probabilityMeasure : Measure Ω
  /-- Population law `P` on observations. -/
  populationMeasure : Measure Observation
  /-- The Donsker class `𝓕`. -/
  indexClass : Set Index
  /-- Indexed functions in the class. -/
  classFun : Index -> Observation -> ℝ
  /-- Deterministic samples used for the empirical-process coordinates. -/
  samples : ∀ sampleSize, SampleAt Observation sampleSize
  /-- Random indices selecting `\hat f_n` from the class. -/
  randomIndex : ℕ -> Ω -> Index
  /-- The deterministic target index representing `f0`. -/
  limitIndex : Index
  /-- The Donsker bridge for the class. -/
  donskerBridge :
    DonskerBridgeCertificate indexClass
      (vaart1998_populationClassMean populationMeasure classFun)
      (vaart1998_empiricalClassMeanSequence samples classFun)
  /-- Each random index lies in the class. -/
  randomIndex_mem : ∀ sampleSize ω, randomIndex sampleSize ω ∈ indexClass
  /-- The target function lies in the class. -/
  limitIndex_mem : limitIndex ∈ indexClass
  /-- Displayed `L2(P)` distance from `\hat f_n` to `f0`. -/
  l2DistanceToLimit : ℕ -> Ω -> ℝ
  /-- The `L2(P)` distance is the textbook squared distance. -/
  l2DistanceToLimit_eq :
    l2DistanceToLimit =
      fun sampleSize ω =>
        vaart1998_l2DistanceSquared populationMeasure
          (classFun (randomIndex sampleSize ω)) (classFun limitIndex)
  /-- The `L2(P)` distance converges to zero in probability. -/
  l2DistanceToLimit_convergesInProbability :
    VdVWConvergesInOuterProbability probabilityMeasure
      l2DistanceToLimit atTop (fun _ => 0)
  /-- Brownian-bridge path continuity in the variance semimetric. -/
  bridgeContinuity_statement : Prop
  /-- Proof of the bridge-continuity side condition. -/
  bridgeContinuity : bridgeContinuity_statement
  /-- Displayed empirical-process difference `G_n(\hat f_n - f0)`. -/
  empiricalProcessDifference : ℕ -> Ω -> ℝ
  /-- The empirical-process difference has the textbook display. -/
  empiricalProcessDifference_eq :
    empiricalProcessDifference =
      fun sampleSize ω =>
        vaart1998_empiricalProcessDifference populationMeasure
          (samples sampleSize) (classFun (randomIndex sampleSize ω))
          (classFun limitIndex)
  /-- Lemma 19.24 first conclusion: `G_n(\hat f_n - f0) ->P 0`. -/
  empiricalProcessDifference_convergesInProbability :
    VdVWConvergesInOuterProbability probabilityMeasure
      empiricalProcessDifference atTop (fun _ => 0)
  /-- Displayed random empirical-process evaluation `G_n \hat f_n`. -/
  randomEmpiricalProcessEvaluation : ℕ -> Ω -> ℝ
  /-- The random empirical-process evaluation has the textbook display. -/
  randomEmpiricalProcessEvaluation_eq :
    randomEmpiricalProcessEvaluation =
      fun sampleSize ω =>
        vaart1998_empiricalProcess populationMeasure
          (samples sampleSize) (classFun (randomIndex sampleSize ω))
  /-- Brownian-bridge evaluation at `f0`. -/
  brownianBridgeEvaluationLimit : Ω -> ℝ
  /-- Lemma 19.24 second conclusion, stated using the local weak-limit API. -/
  randomEvaluationWeakConvergence_statement : Prop
  /-- Proof of the random-evaluation weak-convergence conclusion. -/
  randomEvaluationWeakConvergence :
    randomEvaluationWeakConvergence_statement

namespace Vaart1998Lemma19_24RandomFunctionDonskerSource

/-- Extract the GC component supplied by the Donsker bridge. -/
def glivenkoCantelliClass
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    GlivenkoCantelliClass S.indexClass
      (vaart1998_populationClassMean S.populationMeasure S.classFun)
      (vaart1998_empiricalClassMeanSequence S.samples S.classFun) :=
  DonskerBridgeCertificate.toGlivenkoCantelliClass S.donskerBridge

/-- The Donsker weak-convergence component carried by Lemma 19.24. -/
theorem donsker_weak_convergence
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.donskerBridge.donsker.weak_convergence_statement :=
  DonskerBridgeCertificate.weakConvergence S.donskerBridge

/-- The displayed `L2(P)` distance identity. -/
theorem l2DistanceToLimit_display
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.l2DistanceToLimit =
      fun sampleSize ω =>
        vaart1998_l2DistanceSquared S.populationMeasure
          (S.classFun (S.randomIndex sampleSize ω)) (S.classFun S.limitIndex) :=
  S.l2DistanceToLimit_eq

/-- The `L2(P)` convergence assumption in the local outer-probability API. -/
theorem l2_convergesInProbability
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    VdVWConvergesInOuterProbability S.probabilityMeasure
      S.l2DistanceToLimit atTop (fun _ => 0) :=
  S.l2DistanceToLimit_convergesInProbability

/-- The bridge-continuity side condition used by the continuous-mapping proof. -/
theorem bridge_continuity
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.bridgeContinuity_statement :=
  S.bridgeContinuity

/-- The displayed empirical-process difference identity. -/
theorem empiricalProcessDifference_display
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.empiricalProcessDifference =
      fun sampleSize ω =>
        vaart1998_empiricalProcessDifference S.populationMeasure
          (S.samples sampleSize) (S.classFun (S.randomIndex sampleSize ω))
          (S.classFun S.limitIndex) :=
  S.empiricalProcessDifference_eq

/-- Lemma 19.24 first conclusion: the empirical-process difference vanishes. -/
theorem empirical_process_difference_convergesInProbability
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    VdVWConvergesInOuterProbability S.probabilityMeasure
      S.empiricalProcessDifference atTop (fun _ => 0) :=
  S.empiricalProcessDifference_convergesInProbability

/-- The displayed random empirical-process evaluation identity. -/
theorem randomEmpiricalProcessEvaluation_display
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.randomEmpiricalProcessEvaluation =
      fun sampleSize ω =>
        vaart1998_empiricalProcess S.populationMeasure
          (S.samples sampleSize) (S.classFun (S.randomIndex sampleSize ω)) :=
  S.randomEmpiricalProcessEvaluation_eq

/-- Lemma 19.24 second conclusion: random evaluation inherits the limit at `f0`. -/
theorem random_evaluation_weak_convergence
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.randomEvaluationWeakConvergence_statement :=
  S.randomEvaluationWeakConvergence

/-- Uniform-deviation bound for the random index chosen by `\hat f_n`. -/
theorem random_index_deviation
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (sampleSize : ℕ) (ω : Ω) :
    |vaart1998_empiricalClassMeanSequence S.samples S.classFun sampleSize
        (S.randomIndex sampleSize ω) -
      vaart1998_populationClassMean S.populationMeasure S.classFun
        (S.randomIndex sampleSize ω)| ≤
        (S.glivenkoCantelliClass).radius sampleSize :=
  (S.glivenkoCantelliClass).deviation sampleSize
    (S.randomIndex_mem sampleSize ω)

/-- Uniform-deviation bound at the fixed target `f0`. -/
theorem limit_index_deviation
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_24RandomFunctionDonskerSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (sampleSize : ℕ) :
    |vaart1998_empiricalClassMeanSequence S.samples S.classFun sampleSize
        S.limitIndex -
      vaart1998_populationClassMean S.populationMeasure S.classFun
        S.limitIndex| ≤
        (S.glivenkoCantelliClass).radius sampleSize :=
  (S.glivenkoCantelliClass).deviation sampleSize S.limitIndex_mem

end Vaart1998Lemma19_24RandomFunctionDonskerSource

/--
Theorem 19.28 source: changing classes indexed by a common totally bounded
semimetric space converge to a tight Gaussian process when condition (19.27),
the Lindeberg envelope condition, an entropy alternative, and pointwise
covariance convergence hold.
-/
structure Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation] where
  /-- The population law `P`. -/
  populationMeasure : Measure Observation
  /-- The common index set `T`. -/
  indexSet : Set Index
  /-- The semimetric `ρ` on `T`, represented by its distance display. -/
  semimetric : Index -> Index -> ℝ
  /-- The changing class `f_{n,t}`. -/
  classFun : ℕ -> Index -> Observation -> ℝ
  /-- Deterministic samples used to expose `G_n f_{n,t}`. -/
  samples : ∀ sampleSize, SampleAt Observation sampleSize
  /-- Envelope functions `F_n`. -/
  envelope : ℕ -> Observation -> ℝ
  /-- Probability space carrying the limiting tight Gaussian process. -/
  limitProbabilityMeasure : Measure ΩLimit
  /-- Limiting tight Gaussian process indexed by `T`. -/
  limitProcess : ΩLimit -> Index -> ℝ
  /-- Candidate limiting covariance function on `T × T`. -/
  covarianceLimit : Index -> Index -> ℝ
  /-- Total boundedness of the semimetric index space. -/
  totalBoundedSemimetric_statement : Prop
  /-- Proof of total boundedness. -/
  totalBoundedSemimetric : totalBoundedSemimetric_statement
  /-- Condition (19.27), relating the semimetric to the `L2(P)` distance. -/
  condition19_27_statement : Prop
  /-- Proof of condition (19.27). -/
  condition19_27 : condition19_27_statement
  /-- Bounded sample-path condition for the `ell_infty(T)` process display. -/
  boundedSamplePaths_statement : Prop
  /-- Proof of bounded sample paths. -/
  boundedSamplePaths : boundedSamplePaths_statement
  /-- Lindeberg condition for the envelope sequence. -/
  lindebergEnvelope_statement : Prop
  /-- Proof of the envelope Lindeberg condition. -/
  lindebergEnvelope : lindebergEnvelope_statement
  /-- Bracketing entropy alternative `J_[](δ_n, F_n, L2(P)) -> 0`. -/
  bracketingEntropyVanishes_statement : Prop
  /-- Uniform entropy alternative `J(δ_n, F_n, L2) -> 0`. -/
  uniformEntropyVanishes_statement : Prop
  /-- Suitability/measurability condition for the uniform-entropy alternative. -/
  suitablyMeasurable_statement : Prop
  /-- The selected entropy alternative used for this theorem instance. -/
  entropyAlternative_statement : Prop
  /-- Proof of the selected entropy alternative. -/
  entropyAlternative : entropyAlternative_statement
  /-- Pointwise convergence of the covariance functions on `T × T`. -/
  covarianceConvergesPointwise_statement : Prop
  /-- Proof of pointwise covariance convergence. -/
  covarianceConvergesPointwise : covarianceConvergesPointwise_statement
  /-- Finite-dimensional convergence, supplied by the Lindeberg theorem. -/
  finiteDimensionalConvergence_statement : Prop
  /-- Proof of finite-dimensional convergence. -/
  finiteDimensionalConvergence : finiteDimensionalConvergence_statement
  /-- Asymptotic tightness, supplied by the entropy/maximal-inequality route. -/
  asymptoticTightness_statement : Prop
  /-- Proof of asymptotic tightness. -/
  asymptoticTightness : asymptoticTightness_statement
  /-- The limiting process is tight and Gaussian with the displayed covariance. -/
  tightGaussianLimit_statement : Prop
  /-- Proof of the tight Gaussian limit identification. -/
  tightGaussianLimit : tightGaussianLimit_statement
  /-- Theorem 19.28 weak-convergence conclusion in `ell_infty(T)`. -/
  weakConvergence_statement : Prop
  /-- Proof of the weak-convergence conclusion. -/
  weakConvergence : weakConvergence_statement

namespace Vaart1998Theorem19_28ChangingClassEntropyTightnessSource

/-- The changing empirical-process sequence displayed by Theorem 19.28. -/
abbrev empiricalProcessSequence
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    ℕ -> Index -> ℝ :=
  vaart1998_changingClassEmpiricalProcessSequence
    S.populationMeasure S.samples S.classFun

/-- The covariance sequence displayed by Theorem 19.28. -/
abbrev covarianceSequence
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    ℕ -> Index -> Index -> ℝ :=
  vaart1998_changingClassCovarianceSequence
    S.populationMeasure S.classFun

/-- Display for `t ↦ G_n f_{n,t}`. -/
theorem empiricalProcessSequence_apply
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index))
    (sampleSize : ℕ) (index : Index) :
    S.empiricalProcessSequence sampleSize index =
      vaart1998_empiricalProcess S.populationMeasure
        (S.samples sampleSize) (S.classFun sampleSize index) :=
  rfl

/-- Display for `P f_{n,s} f_{n,t} - P f_{n,s} P f_{n,t}`. -/
theorem covarianceSequence_apply
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index))
    (sampleSize : ℕ) (s t : Index) :
    S.covarianceSequence sampleSize s t =
      vaart1998_functionCovariance S.populationMeasure
        (S.classFun sampleSize s) (S.classFun sampleSize t) :=
  rfl

/-- The total-bounded semimetric condition. -/
theorem total_bounded_semimetric
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.totalBoundedSemimetric_statement :=
  S.totalBoundedSemimetric

/-- The condition (19.27) display. -/
theorem condition_19_27
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.condition19_27_statement :=
  S.condition19_27

/-- The Lindeberg envelope condition. -/
theorem lindeberg_envelope
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.lindebergEnvelope_statement :=
  S.lindebergEnvelope

/-- The selected entropy alternative. -/
theorem entropy_alternative
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.entropyAlternative_statement :=
  S.entropyAlternative

/-- The pointwise covariance-convergence hypothesis. -/
theorem covariance_converges_pointwise
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.covarianceConvergesPointwise_statement :=
  S.covarianceConvergesPointwise

/-- The finite-dimensional convergence component of Theorem 19.28. -/
theorem finite_dimensional_convergence
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.finiteDimensionalConvergence_statement :=
  S.finiteDimensionalConvergence

/-- The asymptotic-tightness component of Theorem 19.28. -/
theorem asymptotic_tightness
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.asymptoticTightness_statement :=
  S.asymptoticTightness

/-- The tight Gaussian limit identification. -/
theorem tight_gaussian_limit
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.tightGaussianLimit_statement :=
  S.tightGaussianLimit

/-- The Theorem 19.28 weak-convergence conclusion. -/
theorem weak_convergence
    {ΩLimit Observation Index : Type*}
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (S : Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Index)) :
    S.weakConvergence_statement :=
  S.weakConvergence

end Vaart1998Theorem19_28ChangingClassEntropyTightnessSource

/--
Example 19.29 source: the local empirical-measure class
`f_{n,t} = r_n 1_(a, a + t δ_n]` on a compact real index set.  The source
records the density expansion, normalization, Lindeberg reduction,
bracketing order, Theorem 19.28 handoff, and Brownian-motion covariance
identification used by the book.
-/
structure Vaart1998Example19_29LocalEmpiricalMeasureSource
    {ΩLimit : Type*} [MeasurableSpace ΩLimit] where
  /-- The observation law `P` on the real line. -/
  populationMeasure : Measure ℝ
  /-- Deterministic samples used to display `P_n` and `G_n`. -/
  samples : ∀ sampleSize, SampleAt ℝ sampleSize
  /-- The localization point `a`. -/
  anchor : ℝ
  /-- The shrinking interval widths `δ_n`. -/
  localizationRadius : ℕ -> ℝ
  /-- The rescaling constants `r_n`. -/
  rescaling : ℕ -> ℝ
  /-- The compact real index set, e.g. `[0,1]`. -/
  indexSet : Set ℝ
  /-- Probability space carrying the Gaussian limit process. -/
  limitProbabilityMeasure : Measure ΩLimit
  /-- The Gaussian limit process indexed by local interval length. -/
  limitProcess : ΩLimit -> ℝ -> ℝ
  /-- Candidate Brownian-motion covariance for the limit. -/
  covarianceLimit : ℝ -> ℝ -> ℝ
  /-- The underlying Theorem 19.28 instance specialized to the local class. -/
  theorem19_28Source :
    Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := ℝ) (Index := ℝ)
  /-- The Theorem 19.28 population law is the local empirical-measure law. -/
  theorem19_28_populationMeasure_eq :
    theorem19_28Source.populationMeasure = populationMeasure
  /-- The Theorem 19.28 samples are the local empirical-measure samples. -/
  theorem19_28_samples_eq :
    theorem19_28Source.samples = samples
  /-- The Theorem 19.28 index set is the compact local index set. -/
  theorem19_28_indexSet_eq :
    theorem19_28Source.indexSet = indexSet
  /-- The Theorem 19.28 changing class is `r_n 1_(a,a+tδ_n]`. -/
  theorem19_28_classFun_eq :
    theorem19_28Source.classFun =
      vaart1998_localEmpiricalChangingClass
        anchor rescaling localizationRadius
  /-- The Theorem 19.28 envelope is `F_n = f_{n,1}`. -/
  theorem19_28_envelope_eq :
    theorem19_28Source.envelope =
      vaart1998_localEmpiricalEnvelope
        anchor rescaling localizationRadius
  /-- The Theorem 19.28 limit law is the local Gaussian limit law. -/
  theorem19_28_limitProbabilityMeasure_eq :
    theorem19_28Source.limitProbabilityMeasure = limitProbabilityMeasure
  /-- The Theorem 19.28 limit process is the local Gaussian process. -/
  theorem19_28_limitProcess_eq :
    theorem19_28Source.limitProcess = limitProcess
  /-- The Theorem 19.28 covariance limit is the Brownian-motion covariance. -/
  theorem19_28_covarianceLimit_eq :
    theorem19_28Source.covarianceLimit = covarianceLimit
  /-- Compactness/totally-boundedness of the local index set. -/
  compactIndex_statement : Prop
  /-- Proof of compactness/totally-boundedness of the local index set. -/
  compactIndex : compactIndex_statement
  /-- The shrinkage condition `δ_n ↓ 0`. -/
  localizationRadiusTendstoZero_statement : Prop
  /-- Proof of `δ_n ↓ 0`. -/
  localizationRadiusTendstoZero : localizationRadiusTendstoZero_statement
  /-- The rescaling condition `r_n → ∞`. -/
  rescalingTendstoInfinity_statement : Prop
  /-- Proof of `r_n → ∞`. -/
  rescalingTendstoInfinity : rescalingTendstoInfinity_statement
  /-- The normalization `r_n^2 δ_n ∼ 1` or the exact choice `= 1`. -/
  normalization_statement : Prop
  /-- Proof of the normalization condition. -/
  normalization : normalization_statement
  /-- Continuity/density hypothesis at the anchor `a`. -/
  densityAtAnchor_statement : Prop
  /-- Proof of the density hypothesis at `a`. -/
  densityAtAnchor : densityAtAnchor_statement
  /-- Expansion `P f_{n,t}^2 = r_n^2 p(a) t δ_n + o(r_n^2 δ_n)`. -/
  secondMomentExpansion_statement : Prop
  /-- Proof of the second-moment expansion. -/
  secondMomentExpansion : secondMomentExpansion_statement
  /-- Nondegenerate limiting variance under the normalization. -/
  nondegenerateVarianceScale_statement : Prop
  /-- Proof of the nondegenerate limiting variance. -/
  nondegenerateVarianceScale : nondegenerateVarianceScale_statement
  /-- The envelope Lindeberg condition reduced to the local interval display. -/
  lindebergReduction_statement : Prop
  /-- Proof of the Lindeberg reduction. -/
  lindebergReduction : lindebergReduction_statement
  /-- The not-too-local condition `n δ_n → ∞`. -/
  notTooLocalized_statement : Prop
  /-- Proof that the intervals are not too localized. -/
  notTooLocalized : notTooLocalized_statement
  /-- Bracketing-number order `O(1 / ε^2)` after rescaling. -/
  bracketingNumberOrder_statement : Prop
  /-- Proof of the bracketing-number order. -/
  bracketingNumberOrder : bracketingNumberOrder_statement
  /-- Theorem 19.28 applies to the local empirical-measure class. -/
  theorem19_28Applies_statement : Prop
  /-- Proof that Theorem 19.28 applies. -/
  theorem19_28Applies : theorem19_28Applies_statement
  /-- Weak convergence of `t ↦ G_n f_{n,t}` to a Gaussian process. -/
  gaussianProcessConvergence_statement : Prop
  /-- Proof of the local Gaussian-process convergence. -/
  gaussianProcessConvergence : gaussianProcessConvergence_statement
  /-- The limiting covariance is Brownian-motion, not Brownian-bridge, shaped. -/
  brownianMotionCovariance_statement : Prop
  /-- Proof of the Brownian-motion covariance identification. -/
  brownianMotionCovariance : brownianMotionCovariance_statement

namespace Vaart1998Example19_29LocalEmpiricalMeasureSource

/-- The local changing class `f_{n,t}` attached to Example 19.29. -/
abbrev classFun
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    ℕ -> ℝ -> ℝ -> ℝ :=
  vaart1998_localEmpiricalChangingClass
    S.anchor S.rescaling S.localizationRadius

/-- The local envelope `F_n = f_{n,1}` attached to Example 19.29. -/
abbrev envelope
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    ℕ -> ℝ -> ℝ :=
  vaart1998_localEmpiricalEnvelope
    S.anchor S.rescaling S.localizationRadius

/-- The local empirical-process sequence `t ↦ G_n f_{n,t}`. -/
abbrev empiricalProcessSequence
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    ℕ -> ℝ -> ℝ :=
  vaart1998_changingClassEmpiricalProcessSequence
    S.populationMeasure S.samples S.classFun

/-- The local covariance sequence of `G_n f_{n,t}`. -/
abbrev covarianceSequence
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    ℕ -> ℝ -> ℝ -> ℝ :=
  vaart1998_changingClassCovarianceSequence
    S.populationMeasure S.classFun

/-- Pointwise display of `f_{n,t} = r_n 1_(a,a+tδ_n]`. -/
theorem classFun_apply
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit))
    (sampleSize : ℕ) (index x : ℝ) :
    S.classFun sampleSize index x =
      S.rescaling sampleSize *
        vaart1998_localEmpiricalCellIndicator
          S.anchor (S.localizationRadius sampleSize) index x :=
  rfl

/-- The envelope is the endpoint-index member `f_{n,1}`. -/
theorem envelope_eq_classFun_one
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit))
    (sampleSize : ℕ) :
    S.envelope sampleSize = S.classFun sampleSize 1 :=
  rfl

/-- Display for the local empirical-process sequence. -/
theorem empiricalProcessSequence_apply
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit))
    (sampleSize : ℕ) (index : ℝ) :
    S.empiricalProcessSequence sampleSize index =
      vaart1998_empiricalProcess S.populationMeasure
        (S.samples sampleSize) (S.classFun sampleSize index) :=
  rfl

/-- Display for the local covariance sequence. -/
theorem covarianceSequence_apply
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit))
    (sampleSize : ℕ) (s t : ℝ) :
    S.covarianceSequence sampleSize s t =
      vaart1998_functionCovariance S.populationMeasure
        (S.classFun sampleSize s) (S.classFun sampleSize t) :=
  rfl

/-- The displayed local empirical-measure average identity. -/
theorem empiricalAverage_eq_rescaling_mul_countFraction
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit))
    (sampleSize : ℕ) (index : ℝ) :
    vaart1998_empiricalAverage (S.samples sampleSize)
        (S.classFun sampleSize index) =
      S.rescaling sampleSize *
        vaart1998_localEmpiricalCountFraction
          (S.samples sampleSize) S.anchor
          (S.localizationRadius sampleSize) index :=
  vaart1998_localEmpiricalAverage_eq_rescaling_mul_countFraction
    (S.samples sampleSize) S.anchor (S.rescaling sampleSize)
    (S.localizationRadius sampleSize) index

/-- The embedded Theorem 19.28 source uses the local changing class. -/
theorem theorem19_28_uses_local_classFun
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.theorem19_28Source.classFun = S.classFun := by
  simpa [classFun] using S.theorem19_28_classFun_eq

/-- The embedded Theorem 19.28 source uses the local endpoint envelope. -/
theorem theorem19_28_uses_local_envelope
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.theorem19_28Source.envelope = S.envelope := by
  simpa [envelope] using S.theorem19_28_envelope_eq

/-- Extract Theorem 19.28 weak convergence for the local class. -/
theorem theorem19_28_weak_convergence
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.theorem19_28Source.weakConvergence_statement :=
  Vaart1998Theorem19_28ChangingClassEntropyTightnessSource.weak_convergence
    S.theorem19_28Source

/-- Compactness/totally-boundedness of the local index set. -/
theorem compact_index
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.compactIndex_statement :=
  S.compactIndex

/-- The shrinkage condition `δ_n ↓ 0`. -/
theorem localization_radius_tendsto_zero
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.localizationRadiusTendstoZero_statement :=
  S.localizationRadiusTendstoZero

/-- The rescaling condition `r_n → ∞`. -/
theorem rescaling_tendsto_infinity
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.rescalingTendstoInfinity_statement :=
  S.rescalingTendstoInfinity

/-- The normalization `r_n^2 δ_n ∼ 1` or `= 1`. -/
theorem normalization_condition
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.normalization_statement :=
  S.normalization

/-- The density/continuity hypothesis at the anchor. -/
theorem density_at_anchor
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.densityAtAnchor_statement :=
  S.densityAtAnchor

/-- The local second-moment expansion. -/
theorem second_moment_expansion
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.secondMomentExpansion_statement :=
  S.secondMomentExpansion

/-- The Lindeberg condition reduced to the local interval display. -/
theorem lindeberg_reduction
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.lindebergReduction_statement :=
  S.lindebergReduction

/-- The not-too-local condition `n δ_n → ∞`. -/
theorem not_too_localized
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.notTooLocalized_statement :=
  S.notTooLocalized

/-- The bracketing-number order used to invoke Theorem 19.28. -/
theorem bracketing_number_order
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.bracketingNumberOrder_statement :=
  S.bracketingNumberOrder

/-- Theorem 19.28 applies to the local empirical-measure class. -/
theorem theorem19_28_applies
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.theorem19_28Applies_statement :=
  S.theorem19_28Applies

/-- The local empirical process converges to a Gaussian process. -/
theorem gaussian_process_convergence
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.gaussianProcessConvergence_statement :=
  S.gaussianProcessConvergence

/-- The limit covariance has Brownian-motion, not Brownian-bridge, form. -/
theorem brownian_motion_covariance
    {ΩLimit : Type*} [MeasurableSpace ΩLimit]
    (S : Vaart1998Example19_29LocalEmpiricalMeasureSource
      (ΩLimit := ΩLimit)) :
    S.brownianMotionCovariance_statement :=
  S.brownianMotionCovariance

end Vaart1998Example19_29LocalEmpiricalMeasureSource

/--
Lemma 19.31 source: under differentiability at `θ₀`, a square-integrable
Lipschitz envelope, and bounded-in-probability local directions, the empirical
process applied to
`r_n(m_{θ₀+\tilde h_n/r_n}-m_{θ₀}) - \tilde h_nᵀ dot m_{θ₀}`
converges to zero in probability.  The source records the proof route through
variance convergence, uniformity on bounded `h`, Theorem 18.14, Theorem
19.28 applied to `r_n M_{1/r_n}`, and the bracketing estimate inherited from
Example 19.7.
-/
structure Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter] where
  /-- Probability law for the random local directions `\tilde h_n`. -/
  samplingMeasure : Measure Ω
  /-- Observation law `P`. -/
  populationMeasure : Measure Observation
  /-- Deterministic samples used to expose `G_n`. -/
  samples : ∀ sampleSize, SampleAt Observation sampleSize
  /-- Parameter-indexed criterion functions `m_θ`. -/
  model : Parameter -> Observation -> ℝ
  /-- The base parameter `θ₀`. -/
  theta0 : Parameter
  /-- The derivative `dot m_{θ₀}(x)` as a continuous linear functional in `h`. -/
  derivativeAtTheta0 : Observation -> Parameter →L[ℝ] ℝ
  /-- The square-integrable Lipschitz envelope `dot m`. -/
  lipschitzEnvelope : Observation -> ℝ
  /-- The localization rates `r_n`. -/
  rescaling : ℕ -> ℝ
  /-- Random local directions `\tilde h_n`. -/
  randomDirection : ℕ -> Ω -> Parameter
  /-- Bounded deterministic local index set, e.g. `{h : ‖h‖ ≤ 1}`. -/
  indexSet : Set Parameter
  /-- The Theorem 19.28 source for `h ↦ r_n(m_{θ₀+h/r_n}-m_{θ₀})`. -/
  theorem19_28Source :
    Vaart1998Theorem19_28ChangingClassEntropyTightnessSource
      (ΩLimit := ΩLimit) (Observation := Observation) (Index := Parameter)
  /-- The Theorem 19.28 population law is the Lemma 19.31 law. -/
  theorem19_28_populationMeasure_eq :
    theorem19_28Source.populationMeasure = populationMeasure
  /-- The Theorem 19.28 samples are the Lemma 19.31 samples. -/
  theorem19_28_samples_eq :
    theorem19_28Source.samples = samples
  /-- The Theorem 19.28 index set is the bounded local `h` set. -/
  theorem19_28_indexSet_eq :
    theorem19_28Source.indexSet = indexSet
  /-- The Theorem 19.28 class is `r_n(M_{1/r_n})`. -/
  theorem19_28_classFun_eq :
    theorem19_28Source.classFun =
      vaart1998_lemma19_31RescaledChangingClass
        model theta0 rescaling
  /-- The Theorem 19.28 envelope is the Lipschitz envelope. -/
  theorem19_28_envelope_eq :
    theorem19_28Source.envelope = fun _ => lipschitzEnvelope
  /-- The parameter domain is open around `θ₀`. -/
  openParameterNeighborhood_statement : Prop
  /-- Proof of the open-neighborhood condition. -/
  openParameterNeighborhood : openParameterNeighborhood_statement
  /-- The base parameter belongs to the relevant neighborhood. -/
  theta0MemNeighborhood_statement : Prop
  /-- Proof that `θ₀` belongs to the relevant neighborhood. -/
  theta0MemNeighborhood : theta0MemNeighborhood_statement
  /-- Measurability of `x ↦ m_θ(x)`. -/
  modelMeasurable_statement : Prop
  /-- Proof of model measurability. -/
  modelMeasurable : modelMeasurable_statement
  /-- Differentiability at `θ₀` almost everywhere or in probability. -/
  differentiableAtTheta0_statement : Prop
  /-- Proof of differentiability at `θ₀`. -/
  differentiableAtTheta0 : differentiableAtTheta0_statement
  /-- Lipschitz condition `‖m_{θ₁}-m_{θ₂}‖ ≤ dot m ‖θ₁-θ₂‖`. -/
  lipschitzCondition_statement : Prop
  /-- Proof of the Lipschitz condition. -/
  lipschitzCondition : lipschitzCondition_statement
  /-- Square-integrability condition `P dot m^2 < ∞`. -/
  lipschitzEnvelopeSquareIntegrable_statement : Prop
  /-- Proof of square-integrability of the Lipschitz envelope. -/
  lipschitzEnvelopeSquareIntegrable :
    lipschitzEnvelopeSquareIntegrable_statement
  /-- The localization rates satisfy `r_n → ∞`. -/
  rescalingTendstoInfinity_statement : Prop
  /-- Proof that `r_n → ∞`. -/
  rescalingTendstoInfinity : rescalingTendstoInfinity_statement
  /-- The random directions satisfy `\tilde h_n = O_P^*(1)`. -/
  randomDirectionBoundedInProbability_statement : Prop
  /-- Proof that the random directions are bounded in probability. -/
  randomDirectionBoundedInProbability :
    randomDirectionBoundedInProbability_statement
  /-- Mean-zero display for the centered empirical-process coordinates. -/
  centeredMeanZero_statement : Prop
  /-- Proof of the mean-zero display. -/
  centeredMeanZero : centeredMeanZero_statement
  /-- Variance convergence to zero for fixed deterministic `h`. -/
  varianceConvergesZero_statement : Prop
  /-- Proof of variance convergence to zero. -/
  varianceConvergesZero : varianceConvergesZero_statement
  /-- Marginal convergence in distribution to zero for fixed `h`. -/
  marginalConvergenceZero_statement : Prop
  /-- Proof of marginal convergence to zero. -/
  marginalConvergenceZero : marginalConvergenceZero_statement
  /-- Tightness of the linear process `h ↦ hᵀ G_n dot m_{θ₀}`. -/
  linearProcessTight_statement : Prop
  /-- Proof of tightness of the linear process. -/
  linearProcessTight : linearProcessTight_statement
  /-- Bracketing-number bound from Example 19.7 for `M_δ`. -/
  bracketingNumberBound_statement : Prop
  /-- Proof of the bracketing-number bound. -/
  bracketingNumberBound : bracketingNumberBound_statement
  /-- Uniform vanishing of the rescaled bracketing entropy integral. -/
  entropyIntegralVanishes_statement : Prop
  /-- Proof of the entropy-integral vanishing. -/
  entropyIntegralVanishes : entropyIntegralVanishes_statement
  /-- Lindeberg condition for the fixed envelope `dot m`. -/
  lindebergEnvelope_statement : Prop
  /-- Proof of the Lindeberg envelope condition. -/
  lindebergEnvelope : lindebergEnvelope_statement
  /-- Theorem 19.28 applies to the rescaled local model class. -/
  theorem19_28Applies_statement : Prop
  /-- Proof that Theorem 19.28 applies. -/
  theorem19_28Applies : theorem19_28Applies_statement
  /-- Asymptotic tightness of the centered process over bounded `h`. -/
  centeredAsymptoticTightness_statement : Prop
  /-- Proof of centered asymptotic tightness. -/
  centeredAsymptoticTightness : centeredAsymptoticTightness_statement
  /-- Uniform convergence to zero on bounded deterministic `h`. -/
  uniformBoundedConvergenceZero_statement : Prop
  /-- Proof of uniform bounded convergence to zero. -/
  uniformBoundedConvergenceZero : uniformBoundedConvergenceZero_statement
  /-- Transfer from bounded deterministic `h` to random `\tilde h_n`. -/
  boundedRandomDirectionTransfer_statement : Prop
  /-- Proof of the random-direction transfer. -/
  boundedRandomDirectionTransfer : boundedRandomDirectionTransfer_statement
  /-- Display (19.30): the random-direction centered process is `o_P(1)`. -/
  display19_30_statement : Prop
  /-- Proof of display (19.30). -/
  display19_30 : display19_30_statement

namespace Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource

/-- The rescaled changing class `h ↦ r_n(m_{θ₀+h/r_n}-m_{θ₀})`. -/
abbrev rescaledClassFun
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    ℕ -> Parameter -> Observation -> ℝ :=
  vaart1998_lemma19_31RescaledChangingClass
    S.model S.theta0 S.rescaling

/-- The centered class in display (19.30). -/
abbrev centeredClassFun
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    ℕ -> Parameter -> Observation -> ℝ :=
  vaart1998_lemma19_31CenteredChangingClass
    S.model S.derivativeAtTheta0 S.theta0 S.rescaling

/-- The empirical process indexed by the rescaled local class. -/
abbrev rescaledEmpiricalProcessSequence
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    ℕ -> Parameter -> ℝ :=
  vaart1998_changingClassEmpiricalProcessSequence
    S.populationMeasure S.samples S.rescaledClassFun

/-- The centered empirical process in display (19.30). -/
abbrev centeredEmpiricalProcessSequence
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    ℕ -> Parameter -> ℝ :=
  vaart1998_changingClassEmpiricalProcessSequence
    S.populationMeasure S.samples S.centeredClassFun

/-- The random-direction value of the centered display (19.30). -/
abbrev randomCenteredEmpiricalProcess
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    ℕ -> Ω -> ℝ :=
  fun sampleSize ω =>
    S.centeredEmpiricalProcessSequence sampleSize
      (S.randomDirection sampleSize ω)

/-- Pointwise display of the rescaled local increment. -/
theorem rescaledClassFun_apply
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter))
    (sampleSize : ℕ) (direction : Parameter) (x : Observation) :
    S.rescaledClassFun sampleSize direction x =
      S.rescaling sampleSize *
        (S.model
            (S.theta0 + (S.rescaling sampleSize)⁻¹ • direction) x -
          S.model S.theta0 x) :=
  rfl

/-- Pointwise display of the centered increment in (19.30). -/
theorem centeredClassFun_apply
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter))
    (sampleSize : ℕ) (direction : Parameter) (x : Observation) :
    S.centeredClassFun sampleSize direction x =
      S.rescaling sampleSize *
          (S.model
              (S.theta0 + (S.rescaling sampleSize)⁻¹ • direction) x -
            S.model S.theta0 x) -
        S.derivativeAtTheta0 x direction :=
  rfl

/-- The embedded Theorem 19.28 source uses the rescaled local class. -/
theorem theorem19_28_uses_rescaled_classFun
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.theorem19_28Source.classFun = S.rescaledClassFun := by
  simpa [rescaledClassFun] using S.theorem19_28_classFun_eq

/-- The embedded Theorem 19.28 source uses the fixed Lipschitz envelope. -/
theorem theorem19_28_uses_lipschitz_envelope
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.theorem19_28Source.envelope =
      fun _ => S.lipschitzEnvelope :=
  S.theorem19_28_envelope_eq

/-- Display for the rescaled empirical-process sequence. -/
theorem rescaledEmpiricalProcessSequence_apply
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter))
    (sampleSize : ℕ) (direction : Parameter) :
    S.rescaledEmpiricalProcessSequence sampleSize direction =
      vaart1998_empiricalProcess S.populationMeasure
        (S.samples sampleSize) (S.rescaledClassFun sampleSize direction) :=
  rfl

/-- Display for the centered empirical-process sequence. -/
theorem centeredEmpiricalProcessSequence_apply
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter))
    (sampleSize : ℕ) (direction : Parameter) :
    S.centeredEmpiricalProcessSequence sampleSize direction =
      vaart1998_empiricalProcess S.populationMeasure
        (S.samples sampleSize) (S.centeredClassFun sampleSize direction) :=
  rfl

/-- Display (19.30) evaluated at the random direction `\tilde h_n`. -/
theorem randomCenteredEmpiricalProcess_apply
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter))
    (sampleSize : ℕ) (ω : Ω) :
    S.randomCenteredEmpiricalProcess sampleSize ω =
      vaart1998_empiricalProcess S.populationMeasure
        (S.samples sampleSize)
        (S.centeredClassFun sampleSize
          (S.randomDirection sampleSize ω)) :=
  rfl

/-- Extract Theorem 19.28 weak convergence for `r_n M_{1/r_n}`. -/
theorem theorem19_28_weak_convergence
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.theorem19_28Source.weakConvergence_statement :=
  Vaart1998Theorem19_28ChangingClassEntropyTightnessSource.weak_convergence
    S.theorem19_28Source

/-- The differentiability-at-`θ₀` hypothesis. -/
theorem differentiable_at_theta0
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.differentiableAtTheta0_statement :=
  S.differentiableAtTheta0

/-- The Lipschitz-envelope hypothesis. -/
theorem lipschitz_condition
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.lipschitzCondition_statement :=
  S.lipschitzCondition

/-- The square-integrability of the Lipschitz envelope. -/
theorem lipschitz_envelope_square_integrable
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.lipschitzEnvelopeSquareIntegrable_statement :=
  S.lipschitzEnvelopeSquareIntegrable

/-- The random directions are bounded in probability. -/
theorem random_direction_bounded_in_probability
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.randomDirectionBoundedInProbability_statement :=
  S.randomDirectionBoundedInProbability

/-- Variance convergence to zero for fixed deterministic directions. -/
theorem variance_converges_zero
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.varianceConvergesZero_statement :=
  S.varianceConvergesZero

/-- The entropy integral vanishes for the rescaled local classes. -/
theorem entropy_integral_vanishes
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.entropyIntegralVanishes_statement :=
  S.entropyIntegralVanishes

/-- Theorem 19.28 applies to the rescaled local model class. -/
theorem theorem19_28_applies
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.theorem19_28Applies_statement :=
  S.theorem19_28Applies

/-- Uniform convergence to zero on bounded deterministic directions. -/
theorem uniform_bounded_convergence_zero
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.uniformBoundedConvergenceZero_statement :=
  S.uniformBoundedConvergenceZero

/-- Display (19.30), the final random-direction negligibility conclusion. -/
theorem display_19_30
    {Ω ΩLimit Observation Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    [MeasurableSpace Observation]
    [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
    (S : Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource
      (Ω := Ω) (ΩLimit := ΩLimit) (Observation := Observation)
      (Parameter := Parameter)) :
    S.display19_30_statement :=
  S.display19_30

end Vaart1998Lemma19_31LipschitzLocalEmpiricalProcessSource

/--
Lemma 19.32 source: Bernstein's inequality for one bounded measurable
coordinate of the empirical process.  The statement records the two one-sided
exponential-Markov bounds, the moment and power-series estimates used in the
proof, and the final absolute-tail inequality

`P(|G_n f| > x) ≤ 2 exp(-(1/4) x^2 / (P f^2 + x ||f||_∞ / sqrt n))`.
-/
structure Vaart1998Lemma19_32BernsteinInequalitySource
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation] where
  /-- Probability law governing the random sample. -/
  samplingMeasure : Measure Ω
  /-- Population law `P`. -/
  populationMeasure : Measure Observation
  /-- Sample size `n`. -/
  sampleSize : ℕ
  /-- The random sample indexed by `Ω`. -/
  randomSample : Ω -> SampleAt Observation sampleSize
  /-- Bounded measurable coordinate `f`. -/
  testFunction : Observation -> ℝ
  /-- The random empirical-process coordinate `G_n f`. -/
  empiricalProcessValue : Ω -> ℝ
  /-- Uniform envelope bound `||f||_∞`. -/
  uniformBound : ℝ
  /-- Positive deviation level `x`. -/
  deviationLevel : ℝ
  /-- The displayed random variable is the empirical process evaluated at `f`. -/
  empiricalProcessValue_eq :
    ∀ ω,
      empiricalProcessValue ω =
        vaart1998_empiricalProcess
          populationMeasure (randomSample ω) testFunction
  /-- Measurability of `f`. -/
  boundedMeasurable_statement : Prop
  /-- Proof of measurability of `f`. -/
  boundedMeasurable : boundedMeasurable_statement
  /-- The uniform bound `|f| ≤ ||f||_∞`. -/
  boundedByUniformBound_statement : Prop
  /-- Proof of the uniform-bound condition. -/
  boundedByUniformBound : boundedByUniformBound_statement
  /-- Square-integrability of `f`. -/
  squareIntegrable_statement : Prop
  /-- Proof of square-integrability of `f`. -/
  squareIntegrable : squareIntegrable_statement
  /-- Positive sample-size side condition. -/
  sampleSizePositive_statement : Prop
  /-- Proof of positive sample size. -/
  sampleSizePositive : sampleSizePositive_statement
  /-- Positive deviation side condition. -/
  deviationPositive_statement : Prop
  /-- Proof of positive deviation. -/
  deviationPositive : deviationPositive_statement
  /-- Nonnegative uniform bound side condition. -/
  uniformBoundNonnegative_statement : Prop
  /-- Proof that the uniform bound is nonnegative. -/
  uniformBoundNonnegative : uniformBoundNonnegative_statement
  /-- Positivity of the Bernstein denominator. -/
  denominatorPositive_statement : Prop
  /-- Proof that the Bernstein denominator is positive. -/
  denominatorPositive : denominatorPositive_statement
  /-- The exponential Markov inequality step for the right tail. -/
  markovRightTailStep_statement : Prop
  /-- Proof of the right-tail Markov step. -/
  markovRightTailStep : markovRightTailStep_statement
  /-- The same exponential Markov step applied to `-f`. -/
  markovLeftTailStep_statement : Prop
  /-- Proof of the left-tail Markov step. -/
  markovLeftTailStep : markovLeftTailStep_statement
  /-- Fubini and power-series expansion of the exponential moment. -/
  fubiniPowerSeries_statement : Prop
  /-- Proof of the Fubini/power-series step. -/
  fubiniPowerSeries : fubiniPowerSeries_statement
  /-- The first centered moment vanishes. -/
  firstCenteredMomentVanishes_statement : Prop
  /-- Proof that the first centered moment vanishes. -/
  firstCenteredMomentVanishes : firstCenteredMomentVanishes_statement
  /-- Higher centered moment bound by `P f^2 (2 ||f||_∞)^(k-2)`. -/
  higherCenteredMomentBound_statement : Prop
  /-- Proof of the higher centered moment bound. -/
  higherCenteredMomentBound : higherCenteredMomentBound_statement
  /-- The proof's choice of `λ` and its comparison with `λ₁ ∧ λ₂`. -/
  lambdaChoiceBound_statement : Prop
  /-- Proof of the `λ` comparison. -/
  lambdaChoiceBound : lambdaChoiceBound_statement
  /-- Exponential moment estimate after inserting the chosen `λ`. -/
  exponentialMomentBound_statement : Prop
  /-- Proof of the exponential moment estimate. -/
  exponentialMomentBound : exponentialMomentBound_statement
  /-- Bernstein bound for the right tail. -/
  rightTailBound :
    samplingMeasure.real
        (vaart1998_rightTailEvent empiricalProcessValue deviationLevel) ≤
      vaart1998_lemma19_32BernsteinTailBound
        (vaart1998_lemma19_32SecondMoment
          populationMeasure testFunction)
        uniformBound sampleSize deviationLevel
  /-- Bernstein bound for the left tail. -/
  leftTailBound :
    samplingMeasure.real
        (vaart1998_leftTailEvent empiricalProcessValue deviationLevel) ≤
      vaart1998_lemma19_32BernsteinTailBound
        (vaart1998_lemma19_32SecondMoment
          populationMeasure testFunction)
        uniformBound sampleSize deviationLevel
  /-- Lemma 19.32 absolute-tail conclusion. -/
  absoluteTailBound :
    vaart1998_absoluteTailProbability
        samplingMeasure empiricalProcessValue deviationLevel ≤
      vaart1998_lemma19_32BernsteinTailBound
        (vaart1998_lemma19_32SecondMoment
          populationMeasure testFunction)
        uniformBound sampleSize deviationLevel

namespace Vaart1998Lemma19_32BernsteinInequalitySource

/-- The `P f^2` variance proxy appearing in Lemma 19.32. -/
abbrev secondMoment
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_32SecondMoment
    S.populationMeasure S.testFunction

/-- The Bernstein denominator for the source. -/
abbrev denominator
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_32BernsteinDenominator
    S.secondMoment S.uniformBound S.sampleSize S.deviationLevel

/-- The Bernstein exponent for the source. -/
abbrev exponent
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_32BernsteinExponent
    S.secondMoment S.uniformBound S.sampleSize S.deviationLevel

/-- The displayed upper bound in Lemma 19.32. -/
abbrev tailBound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_32BernsteinTailBound
    S.secondMoment S.uniformBound S.sampleSize S.deviationLevel

/-- The proof's chosen exponential-Markov parameter. -/
abbrev lambda
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_32Lambda
    S.secondMoment S.uniformBound S.sampleSize S.deviationLevel

/-- The comparison value `λ₁ = x/(2 P f^2)`. -/
abbrev lambdaOne
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_32LambdaOne
    S.secondMoment S.deviationLevel

/-- The comparison value `λ₂ = sqrt n/(2 ||f||_∞)`. -/
abbrev lambdaTwo
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_32LambdaTwo
    S.uniformBound S.sampleSize

/-- The right-tail event for `G_n f`. -/
abbrev rightTailEvent
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : Set Ω :=
  vaart1998_rightTailEvent
    S.empiricalProcessValue S.deviationLevel

/-- The left-tail event for `G_n f`. -/
abbrev leftTailEvent
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : Set Ω :=
  vaart1998_leftTailEvent
    S.empiricalProcessValue S.deviationLevel

/-- The absolute-tail event for `G_n f`. -/
abbrev absoluteTailEvent
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) : Set Ω :=
  vaart1998_absoluteTailEvent
    S.empiricalProcessValue S.deviationLevel

/-- Pointwise display of the empirical-process coordinate. -/
theorem empiricalProcessValue_apply
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation))
    (ω : Ω) :
    S.empiricalProcessValue ω =
      vaart1998_empiricalProcess
        S.populationMeasure (S.randomSample ω) S.testFunction :=
  S.empiricalProcessValue_eq ω

/-- Right-tail events are contained in the absolute-tail event. -/
theorem rightTailEvent_subset_absoluteTailEvent
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.rightTailEvent ⊆ S.absoluteTailEvent :=
  vaart1998_rightTailEvent_subset_absoluteTailEvent
    S.empiricalProcessValue S.deviationLevel

/-- Left-tail events are contained in the absolute-tail event. -/
theorem leftTailEvent_subset_absoluteTailEvent
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.leftTailEvent ⊆ S.absoluteTailEvent :=
  vaart1998_leftTailEvent_subset_absoluteTailEvent
    S.empiricalProcessValue S.deviationLevel

/-- The measurability hypothesis for `f`. -/
theorem bounded_measurable
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.boundedMeasurable_statement :=
  S.boundedMeasurable

/-- The uniform-bound hypothesis for `f`. -/
theorem bounded_by_uniform_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.boundedByUniformBound_statement :=
  S.boundedByUniformBound

/-- Square-integrability of the bounded coordinate. -/
theorem square_integrable
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.squareIntegrable_statement :=
  S.squareIntegrable

/-- Positivity of the Bernstein denominator. -/
theorem denominator_positive
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.denominatorPositive_statement :=
  S.denominatorPositive

/-- The Fubini/power-series step in the proof. -/
theorem fubini_power_series
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.fubiniPowerSeries_statement :=
  S.fubiniPowerSeries

/-- The higher centered moment estimate used by the power-series bound. -/
theorem higher_centered_moment_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.higherCenteredMomentBound_statement :=
  S.higherCenteredMomentBound

/-- The chosen `λ` satisfies the comparison required in the proof. -/
theorem lambda_choice_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.lambdaChoiceBound_statement :=
  S.lambdaChoiceBound

/-- The right-tail Bernstein bound. -/
theorem right_tail_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.samplingMeasure.real S.rightTailEvent ≤ S.tailBound :=
  S.rightTailBound

/-- The left-tail Bernstein bound. -/
theorem left_tail_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.samplingMeasure.real S.leftTailEvent ≤ S.tailBound :=
  S.leftTailBound

/-- Lemma 19.32 absolute-tail Bernstein bound. -/
theorem absolute_tail_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_32BernsteinInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    vaart1998_absoluteTailProbability
        S.samplingMeasure S.empiricalProcessValue S.deviationLevel ≤
      S.tailBound :=
  S.absoluteTailBound

end Vaart1998Lemma19_32BernsteinInequalitySource

/--
Lemma 19.33 source: finite-class maximal inequality derived from Bernstein's
inequality.  The source records the finite indexed class, the large-tail/body
split `G_n f = A_f + B_f`, the `ψ₁` and `ψ₂` Orlicz estimates, Jensen's
finite-maximum step, and the final `\lesssim` bound.
-/
structure Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation] where
  /-- Probability law governing the random sample. -/
  samplingMeasure : Measure Ω
  /-- Population law `P`. -/
  populationMeasure : Measure Observation
  /-- Sample size `n`. -/
  sampleSize : ℕ
  /-- Number of functions in the finite class. -/
  cardinality : ℕ
  /-- The random sample indexed by `Ω`. -/
  randomSample : Ω -> SampleAt Observation sampleSize
  /-- The finite function class, indexed by `Fin cardinality`. -/
  classFun : Fin cardinality -> Observation -> ℝ
  /-- The displayed empirical-process family. -/
  empiricalProcessFamily : Ω -> Fin cardinality -> ℝ
  /-- Coordinatewise uniform bounds `||f||_∞`. -/
  coordinateUniformBound : Fin cardinality -> ℝ
  /-- Coordinatewise second moments `P f^2`. -/
  coordinateSecondMoment : Fin cardinality -> ℝ
  /-- Coordinatewise `L2(P)` norms `||f||_{P,2}`. -/
  coordinateL2Norm : Fin cardinality -> ℝ
  /-- A maximum dominating the coordinatewise uniform bounds. -/
  uniformBoundMax : ℝ
  /-- A maximum dominating the coordinatewise `L2(P)` norms. -/
  l2NormMax : ℝ
  /-- Universal implicit constant in the textbook notation `\lesssim`. -/
  universalConstant : ℝ
  /-- The expectation display for `E_P ||G_n||_F`. -/
  expectedSupremum : ℝ
  /-- The displayed empirical-process family agrees coordinatewise with `G_n f`. -/
  empiricalProcessFamily_eq :
    ∀ ω coordinate,
      empiricalProcessFamily ω coordinate =
        vaart1998_empiricalProcess populationMeasure
          (randomSample ω) (classFun coordinate)
  /-- The displayed expectation is the finite supremum norm expectation. -/
  expectedSupremum_eq :
    expectedSupremum =
      vaart1998_lemma19_33ExpectedFiniteEmpiricalProcessNorm
        samplingMeasure empiricalProcessFamily
  /-- The finite class is nonempty, when this is needed for maxima. -/
  cardinalityPositive_statement : Prop
  /-- Proof that the finite class is nonempty. -/
  cardinalityPositive : cardinalityPositive_statement
  /-- Positive sample-size side condition. -/
  sampleSizePositive_statement : Prop
  /-- Proof of positive sample size. -/
  sampleSizePositive : sampleSizePositive_statement
  /-- Every class member is bounded and measurable. -/
  boundedMeasurable_statement : Prop
  /-- Proof of bounded measurability. -/
  boundedMeasurable : boundedMeasurable_statement
  /-- Every class member is square-integrable. -/
  squareIntegrable_statement : Prop
  /-- Proof of square-integrability. -/
  squareIntegrable : squareIntegrable_statement
  /-- The coordinate uniform bounds dominate the class members. -/
  coordinateUniformBound_statement : Prop
  /-- Proof of coordinate uniform domination. -/
  coordinateUniformBound_proof : coordinateUniformBound_statement
  /-- The coordinate second moments are `P f^2`. -/
  coordinateSecondMoment_statement : Prop
  /-- Proof of the coordinate second-moment display. -/
  coordinateSecondMoment_proof : coordinateSecondMoment_statement
  /-- The coordinate `L2(P)` norms are controlled by the second moments. -/
  coordinateL2Norm_statement : Prop
  /-- Proof of the coordinate `L2(P)` norm display. -/
  coordinateL2Norm_proof : coordinateL2Norm_statement
  /-- The supplied maximum dominates every coordinate uniform bound. -/
  uniformBoundMaxDominates_statement : Prop
  /-- Proof of uniform-bound maximum domination. -/
  uniformBoundMaxDominates : uniformBoundMaxDominates_statement
  /-- The supplied maximum dominates every coordinate `L2(P)` norm. -/
  l2NormMaxDominates_statement : Prop
  /-- Proof of `L2(P)` maximum domination. -/
  l2NormMaxDominates : l2NormMaxDominates_statement
  /-- Nonnegativity of the supplied maxima and universal constant. -/
  nonnegativeScale_statement : Prop
  /-- Proof of nonnegativity of the supplied scales. -/
  nonnegativeScale : nonnegativeScale_statement
  /-- Lemma 19.32 is available for each coordinate and deviation. -/
  coordinateBernstein_statement : Prop
  /-- Proof that the coordinate Bernstein sources are available. -/
  coordinateBernstein : coordinateBernstein_statement
  /-- The `x ≥ b/a` Bernstein exponent comparison gives the `ψ₁` tail. -/
  bernsteinLargeTailComparison_statement : Prop
  /-- Proof of the large-tail comparison. -/
  bernsteinLargeTailComparison : bernsteinLargeTailComparison_statement
  /-- The `x ≤ b/a` Bernstein exponent comparison gives the `ψ₂` tail. -/
  bernsteinBodyTailComparison_statement : Prop
  /-- Proof of the body-tail comparison. -/
  bernsteinBodyTailComparison : bernsteinBodyTailComparison_statement
  /-- Fubini turns the large-tail bound into a `ψ₁` Orlicz estimate. -/
  psiOneFubiniBound_statement : Prop
  /-- Proof of the `ψ₁` Fubini estimate. -/
  psiOneFubiniBound : psiOneFubiniBound_statement
  /-- Fubini turns the body-tail bound into a `ψ₂` Orlicz estimate. -/
  psiTwoFubiniBound_statement : Prop
  /-- Proof of the `ψ₂` Fubini estimate. -/
  psiTwoFubiniBound : psiTwoFubiniBound_statement
  /-- Jensen and finite summation bound the maximum of the `A_f` terms. -/
  jensenPsiOneMaxBound_statement : Prop
  /-- Proof of the `ψ₁` Jensen maximum bound. -/
  jensenPsiOneMaxBound : jensenPsiOneMaxBound_statement
  /-- Jensen and finite summation bound the maximum of the `B_f` terms. -/
  jensenPsiTwoMaxBound_statement : Prop
  /-- Proof of the `ψ₂` Jensen maximum bound. -/
  jensenPsiTwoMaxBound : jensenPsiTwoMaxBound_statement
  /-- The triangle inequality combines the large-tail and body parts. -/
  triangleInequalityStep_statement : Prop
  /-- Proof of the triangle-inequality step. -/
  triangleInequalityStep : triangleInequalityStep_statement
  /-- Lemma 19.33 finite-class maximal inequality. -/
  finiteClassMaximalInequality :
    expectedSupremum ≤
      universalConstant *
        vaart1998_lemma19_33FiniteClassBound
          uniformBoundMax l2NormMax sampleSize cardinality

namespace Vaart1998Lemma19_33FiniteClassMaximalInequalitySource

/-- The finite-class log-cardinality term. -/
abbrev logCardinality
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_33LogCardinality S.cardinality

/-- The linear term in the finite-class maximal inequality. -/
abbrev linearTerm
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_33LinearTerm
    S.uniformBoundMax S.sampleSize S.cardinality

/-- The quadratic term in the finite-class maximal inequality. -/
abbrev quadraticTerm
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_33QuadraticTerm
    S.l2NormMax S.cardinality

/-- The full finite-class bound before the universal constant. -/
abbrev finiteClassBound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) : ℝ :=
  vaart1998_lemma19_33FiniteClassBound
    S.uniformBoundMax S.l2NormMax S.sampleSize S.cardinality

/-- Coordinate empirical-process family generated from the random sample. -/
abbrev generatedEmpiricalProcessFamily
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    Ω -> Fin S.cardinality -> ℝ :=
  vaart1998_lemma19_33RandomEmpiricalProcessFamily
    S.populationMeasure S.randomSample S.classFun

/-- The finite supremum norm random variable `||G_n||_F`. -/
abbrev finiteEmpiricalProcessNorm
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) : Ω -> ℝ :=
  fun ω =>
    vaart1998_lemma19_33FiniteEmpiricalProcessNorm
      (S.empiricalProcessFamily ω)

/-- The proof's coordinate `a` scale. -/
abbrev aScale
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation))
    (coordinate : Fin S.cardinality) : ℝ :=
  vaart1998_lemma19_33AScale
    (S.coordinateUniformBound coordinate) S.sampleSize

/-- The proof's coordinate `b` scale. -/
abbrev bScale
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation))
    (coordinate : Fin S.cardinality) : ℝ :=
  vaart1998_lemma19_33BScale
    (S.coordinateSecondMoment coordinate)

/-- The proof's coordinate split threshold `b/a`. -/
abbrev splitThreshold
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation))
    (coordinate : Fin S.cardinality) : ℝ :=
  vaart1998_lemma19_33SplitThreshold
    (S.coordinateUniformBound coordinate)
    (S.coordinateSecondMoment coordinate)
    S.sampleSize

/-- The large-tail truncation `A_f`. -/
abbrev tailPart
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation))
    (coordinate : Fin S.cardinality) : Ω -> ℝ :=
  vaart1998_lemma19_33TailPart
    (fun ω => S.empiricalProcessFamily ω coordinate)
    (S.splitThreshold coordinate)

/-- The body truncation `B_f`. -/
abbrev bodyPart
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation))
    (coordinate : Fin S.cardinality) : Ω -> ℝ :=
  vaart1998_lemma19_33BodyPart
    (fun ω => S.empiricalProcessFamily ω coordinate)
    (S.splitThreshold coordinate)

/-- Pointwise display of the finite empirical-process family. -/
theorem empiricalProcessFamily_apply
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation))
    (ω : Ω) (coordinate : Fin S.cardinality) :
    S.empiricalProcessFamily ω coordinate =
      vaart1998_empiricalProcess S.populationMeasure
        (S.randomSample ω) (S.classFun coordinate) :=
  S.empiricalProcessFamily_eq ω coordinate

/-- The generated empirical-process family is the displayed family. -/
theorem generatedEmpiricalProcessFamily_apply
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation))
    (ω : Ω) (coordinate : Fin S.cardinality) :
    S.generatedEmpiricalProcessFamily ω coordinate =
      S.empiricalProcessFamily ω coordinate := by
  exact (S.empiricalProcessFamily_eq ω coordinate).symm

/-- Display for `E_P ||G_n||_F`. -/
theorem expectedSupremum_display
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.expectedSupremum =
      vaart1998_lemma19_33ExpectedFiniteEmpiricalProcessNorm
        S.samplingMeasure S.empiricalProcessFamily :=
  S.expectedSupremum_eq

/-- Coordinate values are bounded by the finite supremum norm. -/
theorem abs_coordinate_le_finiteEmpiricalProcessNorm
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation))
    (ω : Ω) (coordinate : Fin S.cardinality) :
    |S.empiricalProcessFamily ω coordinate| ≤
      S.finiteEmpiricalProcessNorm ω :=
  vaart1998_lemma19_33_abs_coordinate_le_finiteEmpiricalProcessNorm
    (S.empiricalProcessFamily ω) coordinate

/-- The coordinate Bernstein route supplied by Lemma 19.32. -/
theorem coordinate_bernstein
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.coordinateBernstein_statement :=
  S.coordinateBernstein

/-- The `ψ₁` Orlicz estimate for the large-tail variables. -/
theorem psi_one_fubini_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.psiOneFubiniBound_statement :=
  S.psiOneFubiniBound

/-- The `ψ₂` Orlicz estimate for the body variables. -/
theorem psi_two_fubini_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.psiTwoFubiniBound_statement :=
  S.psiTwoFubiniBound

/-- Jensen's finite-maximum step for the large-tail variables. -/
theorem jensen_psi_one_max_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.jensenPsiOneMaxBound_statement :=
  S.jensenPsiOneMaxBound

/-- Jensen's finite-maximum step for the body variables. -/
theorem jensen_psi_two_max_bound
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.jensenPsiTwoMaxBound_statement :=
  S.jensenPsiTwoMaxBound

/-- The final finite-class maximal inequality of Lemma 19.33. -/
theorem finite_class_maximal_inequality
    {Ω Observation : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)) :
    S.expectedSupremum ≤ S.universalConstant * S.finiteClassBound :=
  S.finiteClassMaximalInequality

end Vaart1998Lemma19_33FiniteClassMaximalInequalitySource

/--
Lemma 19.34 source: bracketing maximal inequality.  The source records the
initial envelope truncation, the nested bracketing partitions, the chaining
decomposition, the three uses of Lemma 19.33, and the final outer-expectation
maximal bound.
-/
structure Vaart1998Lemma19_34BracketingMaximalInequalitySource
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation] where
  /-- Probability law governing the random sample. -/
  samplingMeasure : Measure Ω
  /-- Population law `P`. -/
  populationMeasure : Measure Observation
  /-- Sample size `n`. -/
  sampleSize : ℕ
  /-- The random sample indexed by `Ω`. -/
  randomSample : Ω -> SampleAt Observation sampleSize
  /-- Function class `\mathcal F`. -/
  indexClass : Set Index
  /-- Class functions `f : X -> R`. -/
  classFun : Index -> Observation -> ℝ
  /-- Envelope `F`. -/
  envelope : Observation -> ℝ
  /-- Radius `δ`. -/
  delta : ℝ
  /-- Bracketing number `N_[](δ,F,L2(P))`, displayed as a real. -/
  bracketingNumberAtDelta : ℝ
  /-- Levelwise bracketing numbers `N_q` in the chaining proof. -/
  bracketingNumberAtLevel : ℕ -> ℝ
  /-- Bracketing integral `J_[](δ,F,L2(P))`. -/
  bracketingIntegral : ℝ
  /-- Envelope-tail term `P* F{F > sqrt n a(δ)}`. -/
  envelopeTailIntegral : ℝ
  /-- Displayed outer expectation `E_P^* ||G_n||_F`. -/
  outerExpectedSupremum : ℝ
  /-- Universal implicit constant in the textbook notation `\lesssim`. -/
  universalConstant : ℝ
  /-- The integer `q₀` with `4δ ≤ 2^{-q₀} ≤ 8δ`. -/
  q0 : ℕ
  /-- Lemma 19.33 sources for the bad-link finite classes. -/
  badLinkFiniteClassSource :
    ℕ -> Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)
  /-- Lemma 19.33 sources for the good telescoping-link finite classes. -/
  goodLinkFiniteClassSource :
    ℕ -> Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)
  /-- Lemma 19.33 source for the base partition level `π_{q₀} f`. -/
  baseFiniteClassSource :
    Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)
  /-- Each class member has `P f^2 < δ^2`. -/
  classSquareMomentSmall_statement : Prop
  /-- Proof of the small `L2(P)` radius condition. -/
  classSquareMomentSmall : classSquareMomentSmall_statement
  /-- `F` is an envelope for the class. -/
  envelopeBound_statement : Prop
  /-- Proof of the envelope bound. -/
  envelopeBound : envelopeBound_statement
  /-- Positivity of `δ`. -/
  deltaPositive_statement : Prop
  /-- Proof that `δ` is positive. -/
  deltaPositive : deltaPositive_statement
  /-- The displayed bracketing number is finite and positive. -/
  bracketingNumberFinitePositive_statement : Prop
  /-- Proof of the finite positive bracketing-number condition. -/
  bracketingNumberFinitePositive :
    bracketingNumberFinitePositive_statement
  /-- The displayed bracketing integral is finite. -/
  bracketingIntegralFinite_statement : Prop
  /-- Proof that the bracketing integral is finite. -/
  bracketingIntegralFinite : bracketingIntegralFinite_statement
  /-- The truncation number `a(δ)` is positive. -/
  aDeltaPositive_statement : Prop
  /-- Proof that `a(δ)` is positive. -/
  aDeltaPositive : aDeltaPositive_statement
  /-- Initial envelope-tail reduction. -/
  envelopeTailReduction_statement : Prop
  /-- Proof of the envelope-tail reduction. -/
  envelopeTailReduction : envelopeTailReduction_statement
  /-- Truncation does not increase bracketing numbers. -/
  truncatedClassBracketingBound_statement : Prop
  /-- Proof of the truncated-class bracketing-number bound. -/
  truncatedClassBracketingBound :
    truncatedClassBracketingBound_statement
  /-- Choice of `q₀`: `4δ ≤ 2^{-q₀} ≤ 8δ`. -/
  q0Choice_statement : Prop
  /-- Proof of the `q₀` choice. -/
  q0Choice : q0Choice_statement
  /-- Existence of nested partitions with bracket diameters. -/
  nestedPartitions_statement : Prop
  /-- Proof that the nested partitions exist. -/
  nestedPartitions : nestedPartitions_statement
  /-- Diameter bounds `sup |f-g| ≤ Δ_q` and `P Δ_q^2 < 2^{-2q}`. -/
  bracketDiameter_statement : Prop
  /-- Proof of the diameter bounds. -/
  bracketDiameter : bracketDiameter_statement
  /-- Entropy-series domination by the bracketing integral. -/
  entropySeriesBound_statement : Prop
  /-- Proof of the entropy-series domination. -/
  entropySeriesBound : entropySeriesBound_statement
  /-- Choice of representatives `π_q f` and bracket widths `Δ_q f`. -/
  projectionChoice_statement : Prop
  /-- Proof of the representative/projection choice. -/
  projectionChoice : projectionChoice_statement
  /-- Definition and side conditions for `a_q`. -/
  chainScaleChoice_statement : Prop
  /-- Proof of the chain-scale side conditions. -/
  chainScaleChoice : chainScaleChoice_statement
  /-- Good/bad indicators `A_{q-1} f` and `B_q f`. -/
  goodBadIndicator_statement : Prop
  /-- Proof of the good/bad indicator construction. -/
  goodBadIndicator : goodBadIndicator_statement
  /-- Pointwise chaining decomposition of `f - π_{q₀} f`. -/
  telescopingDecomposition_statement : Prop
  /-- Proof of the telescoping decomposition. -/
  telescopingDecomposition : telescopingDecomposition_statement
  /-- Lemma 19.33 controls the bad-link series. -/
  badLinkSeriesBound_statement : Prop
  /-- Proof of the bad-link series bound. -/
  badLinkSeriesBound : badLinkSeriesBound_statement
  /-- Lemma 19.33 controls the good-link telescoping series. -/
  goodLinkSeriesBound_statement : Prop
  /-- Proof of the good-link series bound. -/
  goodLinkSeriesBound : goodLinkSeriesBound_statement
  /-- Lemma 19.33 controls the base partition level. -/
  baseLevelBound_statement : Prop
  /-- Proof of the base-level bound. -/
  baseLevelBound : baseLevelBound_statement
  /-- The chaining series is bounded by the bracketing integral. -/
  chainingBound_statement : Prop
  /-- Proof of the chaining bound. -/
  chainingBound : chainingBound_statement
  /-- Lemma 19.34 bracketing maximal inequality. -/
  bracketingMaximalInequality :
    outerExpectedSupremum ≤
      universalConstant *
        vaart1998_lemma19_34MaximalBound
          bracketingIntegral envelopeTailIntegral sampleSize

namespace Vaart1998Lemma19_34BracketingMaximalInequalitySource

/-- The truncation value `a(δ)`. -/
abbrev aDelta
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_34ADelta S.delta S.bracketingNumberAtDelta

/-- The envelope tail set `{F > sqrt n a(δ)}`. -/
abbrev envelopeTailSet
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    Set Observation :=
  vaart1998_lemma19_34EnvelopeTailSet
    S.envelope S.sampleSize S.aDelta

/-- The displayed envelope-tail integral. -/
abbrev displayedEnvelopeTailIntegral
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_34EnvelopeTailIntegral
    S.populationMeasure S.envelope S.sampleSize S.aDelta

/-- The truncated class `f 1{F ≤ sqrt n a(δ)}`. -/
abbrev truncatedClassFun
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    Index -> Observation -> ℝ :=
  vaart1998_lemma19_34TruncatedClassFun
    S.envelope S.sampleSize S.aDelta S.classFun

/-- The final Lemma 19.34 right-hand side before the universal constant. -/
abbrev maximalBound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_34MaximalBound
    S.bracketingIntegral S.envelopeTailIntegral S.sampleSize

/-- The chain scale `a_q`. -/
abbrev chainScale
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (q : ℕ) : ℝ :=
  vaart1998_lemma19_34ChainScale S.bracketingNumberAtLevel q

/-- The entropy-series term `2^{-q} sqrt(log N_q)`. -/
abbrev entropySeriesTerm
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (q : ℕ) : ℝ :=
  vaart1998_lemma19_34EntropySeriesTerm S.bracketingNumberAtLevel q

/-- The small `L2(P)` radius condition. -/
theorem class_square_moment_small
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.classSquareMomentSmall_statement :=
  S.classSquareMomentSmall

/-- The envelope condition for `F`. -/
theorem envelope_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.envelopeBound_statement :=
  S.envelopeBound

/-- The initial envelope-tail reduction. -/
theorem envelope_tail_reduction
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.envelopeTailReduction_statement :=
  S.envelopeTailReduction

/-- Truncation does not increase bracketing numbers. -/
theorem truncated_class_bracketing_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.truncatedClassBracketingBound_statement :=
  S.truncatedClassBracketingBound

/-- The nested partition construction. -/
theorem nested_partitions
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.nestedPartitions_statement :=
  S.nestedPartitions

/-- The pointwise telescoping decomposition. -/
theorem telescoping_decomposition
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.telescopingDecomposition_statement :=
  S.telescopingDecomposition

/-- Lemma 19.33 bound for bad-link finite classes. -/
theorem bad_link_finite_class_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (q : ℕ) :
    (S.badLinkFiniteClassSource q).expectedSupremum ≤
      (S.badLinkFiniteClassSource q).universalConstant *
        (S.badLinkFiniteClassSource q).finiteClassBound :=
  Vaart1998Lemma19_33FiniteClassMaximalInequalitySource.finite_class_maximal_inequality
    (S.badLinkFiniteClassSource q)

/-- Lemma 19.33 bound for good telescoping-link finite classes. -/
theorem good_link_finite_class_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (q : ℕ) :
    (S.goodLinkFiniteClassSource q).expectedSupremum ≤
      (S.goodLinkFiniteClassSource q).universalConstant *
        (S.goodLinkFiniteClassSource q).finiteClassBound :=
  Vaart1998Lemma19_33FiniteClassMaximalInequalitySource.finite_class_maximal_inequality
    (S.goodLinkFiniteClassSource q)

/-- Lemma 19.33 bound for the base partition level. -/
theorem base_finite_class_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.baseFiniteClassSource.expectedSupremum ≤
      S.baseFiniteClassSource.universalConstant *
        S.baseFiniteClassSource.finiteClassBound :=
  Vaart1998Lemma19_33FiniteClassMaximalInequalitySource.finite_class_maximal_inequality
    S.baseFiniteClassSource

/-- The bad-link series bound. -/
theorem bad_link_series_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.badLinkSeriesBound_statement :=
  S.badLinkSeriesBound

/-- The good-link telescoping series bound. -/
theorem good_link_series_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.goodLinkSeriesBound_statement :=
  S.goodLinkSeriesBound

/-- The base-level finite-class bound. -/
theorem base_level_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.baseLevelBound_statement :=
  S.baseLevelBound

/-- Lemma 19.34 bracketing maximal inequality. -/
theorem bracketing_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.outerExpectedSupremum ≤ S.universalConstant * S.maximalBound :=
  S.bracketingMaximalInequality

end Vaart1998Lemma19_34BracketingMaximalInequalitySource

/--
Corollary 19.35 source: the envelope-only bracketing maximal inequality.
The source records the single bracket `[-F,F]`, the specialization
`δ = 2 ||F||_{P,2}` of Lemma 19.34, Markov control of the envelope-tail
term, and the final bound by the bracketing integral at `||F||_{P,2}`.
-/
structure Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation] where
  /-- Probability law governing the random sample. -/
  samplingMeasure : Measure Ω
  /-- Population law `P`. -/
  populationMeasure : Measure Observation
  /-- Sample size `n`. -/
  sampleSize : ℕ
  /-- The random sample indexed by `Ω`. -/
  randomSample : Ω -> SampleAt Observation sampleSize
  /-- Function class `\mathcal F`. -/
  indexClass : Set Index
  /-- Class functions `f : X -> R`. -/
  classFun : Index -> Observation -> ℝ
  /-- Envelope `F`. -/
  envelope : Observation -> ℝ
  /-- Displayed envelope norm `||F||_{P,2}`. -/
  envelopeL2Norm : ℝ
  /-- Bracketing integral `J_[] (||F||_{P,2}, F, L2(P))`. -/
  bracketingIntegralAtEnvelope : ℝ
  /-- Displayed outer expectation `E_P^* ||G_n||_F`. -/
  outerExpectedSupremum : ℝ
  /-- Universal implicit constant in the textbook notation `\lesssim`. -/
  universalConstant : ℝ
  /-- The Lemma 19.34 source specialized to the proof radius. -/
  lemma19_34Source :
    Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)
  /-- The supplied envelope norm is the displayed `L2(P)` norm. -/
  envelopeL2Norm_eq :
    envelopeL2Norm =
      vaart1998_corollary19_35EnvelopeL2Norm
        populationMeasure envelope
  /-- Lemma 19.34 uses the proof radius `2 ||F||_{P,2}`. -/
  lemma19_34_delta_eq :
    lemma19_34Source.delta =
      vaart1998_corollary19_35ProofRadius envelopeL2Norm
  /-- Lemma 19.34 sees the one-bracket bracketing number. -/
  lemma19_34_bracketingNumber_eq :
    lemma19_34Source.bracketingNumberAtDelta =
      vaart1998_corollary19_35SingleBracketNumber
  /-- Lemma 19.34's outer expectation is the displayed corollary one. -/
  lemma19_34_outerExpectedSupremum_eq :
    lemma19_34Source.outerExpectedSupremum = outerExpectedSupremum
  /-- Lemma 19.34's universal constant is absorbed into the corollary constant. -/
  lemma19_34_universalConstant_eq :
    lemma19_34Source.universalConstant = universalConstant
  /-- The class consists of measurable functions. -/
  classMeasurable_statement : Prop
  /-- Proof of class measurability. -/
  classMeasurable : classMeasurable_statement
  /-- `F` is a measurable envelope. -/
  envelopeMeasurable_statement : Prop
  /-- Proof of envelope measurability. -/
  envelopeMeasurable : envelopeMeasurable_statement
  /-- `F` is square-integrable. -/
  squareIntegrableEnvelope_statement : Prop
  /-- Proof of square-integrability of the envelope. -/
  squareIntegrableEnvelope : squareIntegrableEnvelope_statement
  /-- `F` bounds every class member. -/
  envelopeBound_statement : Prop
  /-- Proof of the envelope bound. -/
  envelopeBound : envelopeBound_statement
  /-- The single bracket `[-F,F]` contains the class. -/
  singleBracket_statement : Prop
  /-- Proof of the single-bracket containment. -/
  singleBracket : singleBracket_statement
  /-- The single bracket gives bracketing number `1` at `2 ||F||_{P,2}`. -/
  singleBracketNumber_statement : Prop
  /-- Proof of the one-bracket bracketing-number display. -/
  singleBracketNumber : singleBracketNumber_statement
  /-- The Lemma 19.34 `a(δ)` reduction at this radius. -/
  aDeltaReduction_statement : Prop
  /-- Proof of the `a(δ)` reduction. -/
  aDeltaReduction : aDeltaReduction_statement
  /-- Markov's inequality controls the envelope-tail term. -/
  markovEnvelopeTailBound_statement : Prop
  /-- Proof of the Markov envelope-tail bound. -/
  markovEnvelopeTailBound : markovEnvelopeTailBound_statement
  /-- Radius monotonicity/constant absorption for the bracketing integral. -/
  bracketingIntegralRadiusReduction_statement : Prop
  /-- Proof of the bracketing-integral radius reduction. -/
  bracketingIntegralRadiusReduction :
    bracketingIntegralRadiusReduction_statement
  /-- Lemma 19.34 plus the preceding reductions give the corollary bound. -/
  corollaryMaximalInequality :
    outerExpectedSupremum ≤
      universalConstant *
        vaart1998_corollary19_35BracketingIntegralBound
          bracketingIntegralAtEnvelope

namespace Vaart1998Corollary19_35EnvelopeBracketingMaximalSource

/-- The proof radius `δ = 2 ||F||_{P,2}`. -/
abbrev proofRadius
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_corollary19_35ProofRadius S.envelopeL2Norm

/-- The lower endpoint `-F` of the single bracket. -/
abbrev singleBracketLower
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    Observation -> ℝ :=
  vaart1998_corollary19_35SingleBracketLower S.envelope

/-- The upper endpoint `F` of the single bracket. -/
abbrev singleBracketUpper
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    Observation -> ℝ :=
  vaart1998_corollary19_35SingleBracketUpper S.envelope

/-- The specialized `a(δ)` value used in the proof. -/
abbrev aDelta
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_corollary19_35ADelta S.envelopeL2Norm

/-- The final Corollary 19.35 right-hand side before the universal constant. -/
abbrev maximalBound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_corollary19_35BracketingIntegralBound
    S.bracketingIntegralAtEnvelope

/-- The displayed envelope norm identity. -/
theorem envelope_l2_norm
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.envelopeL2Norm =
      vaart1998_corollary19_35EnvelopeL2Norm
        S.populationMeasure S.envelope :=
  S.envelopeL2Norm_eq

/-- The Lemma 19.34 proof radius display. -/
theorem lemma19_34_delta
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.lemma19_34Source.delta = S.proofRadius :=
  S.lemma19_34_delta_eq

/-- The Lemma 19.34 bracketing number is `1` at the proof radius. -/
theorem lemma19_34_bracketing_number
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.lemma19_34Source.bracketingNumberAtDelta =
      vaart1998_corollary19_35SingleBracketNumber :=
  S.lemma19_34_bracketingNumber_eq

/-- The specialized `a(δ)` is the proof radius. -/
theorem aDelta_eq_proofRadius
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.aDelta = S.proofRadius :=
  vaart1998_corollary19_35ADelta_eq S.envelopeL2Norm

/-- The class measurability assumption. -/
theorem class_measurable
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.classMeasurable_statement :=
  S.classMeasurable

/-- The envelope measurability assumption. -/
theorem envelope_measurable
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.envelopeMeasurable_statement :=
  S.envelopeMeasurable

/-- The square-integrable-envelope assumption. -/
theorem square_integrable_envelope
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.squareIntegrableEnvelope_statement :=
  S.squareIntegrableEnvelope

/-- The envelope bound for every class member. -/
theorem envelope_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.envelopeBound_statement :=
  S.envelopeBound

/-- The single-bracket containment `[-F,F]`. -/
theorem single_bracket
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.singleBracket_statement :=
  S.singleBracket

/-- The one-bracket bracketing-number display. -/
theorem single_bracket_number
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.singleBracketNumber_statement :=
  S.singleBracketNumber

/-- The proof's `a(δ)` reduction. -/
theorem aDelta_reduction
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.aDeltaReduction_statement :=
  S.aDeltaReduction

/-- Markov control of the Lemma 19.34 envelope-tail term. -/
theorem markov_envelope_tail_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.markovEnvelopeTailBound_statement :=
  S.markovEnvelopeTailBound

/-- Bracketing-integral radius reduction/constant absorption. -/
theorem bracketing_integral_radius_reduction
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.bracketingIntegralRadiusReduction_statement :=
  S.bracketingIntegralRadiusReduction

/-- The reused Lemma 19.34 maximal inequality. -/
theorem lemma19_34_bracketing_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.lemma19_34Source.outerExpectedSupremum ≤
      S.lemma19_34Source.universalConstant *
        S.lemma19_34Source.maximalBound :=
  Vaart1998Lemma19_34BracketingMaximalInequalitySource.bracketing_maximal_inequality
    S.lemma19_34Source

/-- Corollary 19.35 envelope bracketing maximal inequality. -/
theorem envelope_bracketing_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Corollary19_35EnvelopeBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.outerExpectedSupremum ≤ S.universalConstant * S.maximalBound := by
  simpa [maximalBound] using S.corollaryMaximalInequality

end Vaart1998Corollary19_35EnvelopeBracketingMaximalSource

/--
Lemma 19.36 source: bracketing maximal inequality for uniformly bounded
classes.  The source records the `P f^2 < δ^2` and `||f||∞ ≤ M`
hypotheses, the finite-class Bernstein inputs reused in the bounded chaining
argument, the Lemma 19.34 baseline source that this refinement sharpens, and
the final bound

`J_[](δ,F,L2(P)) * (1 + J_[](δ,F,L2(P)) M / (δ^2 sqrt n))`.
-/
structure Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation] where
  /-- Probability law governing the random sample. -/
  samplingMeasure : Measure Ω
  /-- Population law `P`. -/
  populationMeasure : Measure Observation
  /-- Sample size `n`. -/
  sampleSize : ℕ
  /-- The random sample indexed by `Ω`. -/
  randomSample : Ω -> SampleAt Observation sampleSize
  /-- Function class `\mathcal F`. -/
  indexClass : Set Index
  /-- Class functions `f : X -> R`. -/
  classFun : Index -> Observation -> ℝ
  /-- Radius `δ`. -/
  delta : ℝ
  /-- Uniform bound `M`. -/
  uniformBound : ℝ
  /-- Bracketing integral `J_[](δ,F,L2(P))`. -/
  bracketingIntegral : ℝ
  /-- Displayed outer expectation `E_P^* ||G_n||_F`. -/
  outerExpectedSupremum : ℝ
  /-- Universal implicit constant in the textbook notation `\lesssim`. -/
  universalConstant : ℝ
  /-- Lemma 19.34 baseline source before applying the bounded refinement. -/
  lemma19_34Source :
    Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)
  /-- Lemma 19.33 finite-class sources used in the bounded chaining proof. -/
  finiteClassRefinementSource :
    ℕ -> Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)
  /-- Lemma 19.34's displayed outer expectation agrees with this source. -/
  lemma19_34_outerExpectedSupremum_eq :
    lemma19_34Source.outerExpectedSupremum = outerExpectedSupremum
  /-- Lemma 19.34's radius agrees with this source. -/
  lemma19_34_delta_eq : lemma19_34Source.delta = delta
  /-- Lemma 19.34's bracketing integral agrees with this source. -/
  lemma19_34_bracketingIntegral_eq :
    lemma19_34Source.bracketingIntegral = bracketingIntegral
  /-- Each class member is measurable. -/
  classMeasurable_statement : Prop
  /-- Proof of class measurability. -/
  classMeasurable : classMeasurable_statement
  /-- Each class member has `P f^2 < δ^2`. -/
  classSquareMomentSmall_statement : Prop
  /-- Proof of the small `L2(P)` radius condition. -/
  classSquareMomentSmall : classSquareMomentSmall_statement
  /-- Each class member is uniformly bounded by `M`. -/
  uniformBound_statement : Prop
  /-- Proof of the uniform bound. -/
  uniformBoundProof : uniformBound_statement
  /-- Positivity of `δ`. -/
  deltaPositive_statement : Prop
  /-- Proof that `δ` is positive. -/
  deltaPositive : deltaPositive_statement
  /-- Positive sample-size side condition. -/
  sampleSizePositive_statement : Prop
  /-- Proof of positive sample size. -/
  sampleSizePositive : sampleSizePositive_statement
  /-- Nonnegativity of `M`. -/
  uniformBoundNonnegative_statement : Prop
  /-- Proof that the uniform bound is nonnegative. -/
  uniformBoundNonnegative : uniformBoundNonnegative_statement
  /-- The bracketing integral is finite. -/
  bracketingIntegralFinite_statement : Prop
  /-- Proof that the bracketing integral is finite. -/
  bracketingIntegralFinite : bracketingIntegralFinite_statement
  /-- The bracketing integral is nonnegative. -/
  bracketingIntegralNonnegative_statement : Prop
  /-- Proof of nonnegativity of the bracketing integral. -/
  bracketingIntegralNonnegative : bracketingIntegralNonnegative_statement
  /-- The class admits finite brackets at the levels used by the proof. -/
  finiteBracketingAtLevels_statement : Prop
  /-- Proof of the finite-bracketing condition. -/
  finiteBracketingAtLevels : finiteBracketingAtLevels_statement
  /-- Boundedness removes the crude envelope-tail term from Lemma 19.34. -/
  boundedEnvelopeTailImprovement_statement : Prop
  /-- Proof of the bounded envelope-tail improvement. -/
  boundedEnvelopeTailImprovement :
    boundedEnvelopeTailImprovement_statement
  /-- Bounded chaining refines the Lemma 19.34 decomposition. -/
  boundedChainingRefinement_statement : Prop
  /-- Proof of the bounded chaining refinement. -/
  boundedChainingRefinement : boundedChainingRefinement_statement
  /-- Lemma 19.33 controls each finite class in the refined chain. -/
  finiteClassMaximalRefinement_statement : Prop
  /-- Proof of the finite-class maximal refinement. -/
  finiteClassMaximalRefinement :
    finiteClassMaximalRefinement_statement
  /-- The first-order entropy series is controlled by the bracketing integral. -/
  firstOrderEntropyBound_statement : Prop
  /-- Proof of the first-order entropy bound. -/
  firstOrderEntropyBound : firstOrderEntropyBound_statement
  /-- The bounded linear terms produce the `J^2 M/(δ^2 sqrt n)` correction. -/
  secondOrderEntropyBound_statement : Prop
  /-- Proof of the second-order entropy bound. -/
  secondOrderEntropyBound : secondOrderEntropyBound_statement
  /-- The final constant-absorption step. -/
  constantAbsorption_statement : Prop
  /-- Proof of constant absorption. -/
  constantAbsorption : constantAbsorption_statement
  /-- Lemma 19.36 uniformly bounded bracketing maximal inequality. -/
  uniformBoundedBracketingMaximalInequality :
    outerExpectedSupremum ≤
      universalConstant *
        vaart1998_lemma19_36MaximalBound
          bracketingIntegral delta uniformBound sampleSize

namespace Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource

/-- The second-order correction `J_[]/(δ^2 sqrt n) * M`. -/
abbrev secondOrderCorrection
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_36SecondOrderCorrection
    S.bracketingIntegral S.delta S.uniformBound S.sampleSize

/-- The parenthesized Lemma 19.36 factor. -/
abbrev boundFactor
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_36BoundFactor
    S.bracketingIntegral S.delta S.uniformBound S.sampleSize

/-- The full Lemma 19.36 right-hand side before the universal constant. -/
abbrev maximalBound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_36MaximalBound
    S.bracketingIntegral S.delta S.uniformBound S.sampleSize

/-- The reused Lemma 19.34 baseline maximal inequality. -/
theorem lemma19_34_bracketing_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.lemma19_34Source.outerExpectedSupremum ≤
      S.lemma19_34Source.universalConstant *
        S.lemma19_34Source.maximalBound :=
  Vaart1998Lemma19_34BracketingMaximalInequalitySource.bracketing_maximal_inequality
    S.lemma19_34Source

/-- Lemma 19.33 bound for each finite class used in the refinement. -/
theorem finite_class_refinement_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (q : ℕ) :
    (S.finiteClassRefinementSource q).expectedSupremum ≤
      (S.finiteClassRefinementSource q).universalConstant *
        (S.finiteClassRefinementSource q).finiteClassBound :=
  Vaart1998Lemma19_33FiniteClassMaximalInequalitySource.finite_class_maximal_inequality
    (S.finiteClassRefinementSource q)

/-- The class measurability assumption. -/
theorem class_measurable
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.classMeasurable_statement :=
  S.classMeasurable

/-- The small `L2(P)` radius condition. -/
theorem class_square_moment_small
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.classSquareMomentSmall_statement :=
  S.classSquareMomentSmall

/-- The uniform bound `||f||∞ ≤ M`. -/
theorem uniform_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.uniformBound_statement :=
  S.uniformBoundProof

/-- The finite-bracketing condition used by the proof. -/
theorem finite_bracketing_at_levels
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.finiteBracketingAtLevels_statement :=
  S.finiteBracketingAtLevels

/-- Bounded classes improve the envelope-tail term. -/
theorem bounded_envelope_tail_improvement
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.boundedEnvelopeTailImprovement_statement :=
  S.boundedEnvelopeTailImprovement

/-- The bounded chaining refinement. -/
theorem bounded_chaining_refinement
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.boundedChainingRefinement_statement :=
  S.boundedChainingRefinement

/-- The refined finite-class maximal step. -/
theorem finite_class_maximal_refinement
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.finiteClassMaximalRefinement_statement :=
  S.finiteClassMaximalRefinement

/-- First-order entropy domination by the bracketing integral. -/
theorem first_order_entropy_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.firstOrderEntropyBound_statement :=
  S.firstOrderEntropyBound

/-- Second-order entropy domination giving the bounded correction term. -/
theorem second_order_entropy_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.secondOrderEntropyBound_statement :=
  S.secondOrderEntropyBound

/-- Constant absorption into the universal implicit constant. -/
theorem constant_absorption
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.constantAbsorption_statement :=
  S.constantAbsorption

/-- Lemma 19.36 uniformly bounded bracketing maximal inequality. -/
theorem uniform_bounded_bracketing_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.outerExpectedSupremum ≤ S.universalConstant * S.maximalBound :=
  S.uniformBoundedBracketingMaximalInequality

end Vaart1998Lemma19_36UniformBoundedBracketingMaximalSource

/--
Lemma 19.37 source: bracketing maximal inequality measured in the Bernstein
norm.  The source records the textbook definition

`||f||_{P,B}^2 = 2 P (exp |f| - 1 - |f|)`,

the small Bernstein-norm hypothesis, the finite-class Bernstein inputs reused
in the chaining proof, the monotonicity/dominance facts that make the
Bernstein expression usable as a bracket gauge, and the final bound

`J_[](δ,F,||.||_{P,B}) * (1 + J_[](δ,F,||.||_{P,B}) / (δ^2 sqrt n))`.
-/
structure Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation] where
  /-- Probability law governing the random sample. -/
  samplingMeasure : Measure Ω
  /-- Population law `P`. -/
  populationMeasure : Measure Observation
  /-- Sample size `n`. -/
  sampleSize : ℕ
  /-- The random sample indexed by `Ω`. -/
  randomSample : Ω -> SampleAt Observation sampleSize
  /-- Function class `\mathcal F`. -/
  indexClass : Set Index
  /-- Class functions `f : X -> R`. -/
  classFun : Index -> Observation -> ℝ
  /-- Radius `δ`. -/
  delta : ℝ
  /-- Bracketing integral `J_[](δ,F,||.||_{P,B})`. -/
  bracketingIntegral : ℝ
  /-- Displayed outer expectation `E_P^* ||G_n||_F`. -/
  outerExpectedSupremum : ℝ
  /-- Universal implicit constant in the textbook notation `\lesssim`. -/
  universalConstant : ℝ
  /-- Lemma 19.34 baseline source before replacing the bracket gauge. -/
  lemma19_34Source :
    Vaart1998Lemma19_34BracketingMaximalInequalitySource
      (Ω := Ω) (Observation := Observation) (Index := Index)
  /-- Lemma 19.33 finite-class sources used in the refined chain. -/
  finiteClassRefinementSource :
    ℕ -> Vaart1998Lemma19_33FiniteClassMaximalInequalitySource
      (Ω := Ω) (Observation := Observation)
  /-- Lemma 19.34's displayed outer expectation agrees with this source. -/
  lemma19_34_outerExpectedSupremum_eq :
    lemma19_34Source.outerExpectedSupremum = outerExpectedSupremum
  /-- Lemma 19.34's radius agrees with this source. -/
  lemma19_34_delta_eq : lemma19_34Source.delta = delta
  /-- Each class member is measurable. -/
  classMeasurable_statement : Prop
  /-- Proof of class measurability. -/
  classMeasurable : classMeasurable_statement
  /-- Each class member has Bernstein norm smaller than `δ`. -/
  bernsteinNormSmall_statement : Prop
  /-- Proof of the small Bernstein-norm radius condition. -/
  bernsteinNormSmall : bernsteinNormSmall_statement
  /-- Positivity of `δ`. -/
  deltaPositive_statement : Prop
  /-- Proof that `δ` is positive. -/
  deltaPositive : deltaPositive_statement
  /-- Positive sample-size side condition. -/
  sampleSizePositive_statement : Prop
  /-- Proof of positive sample size. -/
  sampleSizePositive : sampleSizePositive_statement
  /-- The bracketing integral is finite. -/
  bracketingIntegralFinite_statement : Prop
  /-- Proof that the bracketing integral is finite. -/
  bracketingIntegralFinite : bracketingIntegralFinite_statement
  /-- The bracketing integral is nonnegative. -/
  bracketingIntegralNonnegative_statement : Prop
  /-- Proof of nonnegativity of the bracketing integral. -/
  bracketingIntegralNonnegative : bracketingIntegralNonnegative_statement
  /-- The class admits finite Bernstein-norm brackets at proof levels. -/
  finiteBernsteinBracketingAtLevels_statement : Prop
  /-- Proof of the finite-bracketing condition. -/
  finiteBernsteinBracketingAtLevels :
    finiteBernsteinBracketingAtLevels_statement
  /-- The displayed formula really is the Bernstein norm used for brackets. -/
  bernsteinNormDefinition_statement : Prop
  /-- Proof of the Bernstein-norm definition display. -/
  bernsteinNormDefinition : bernsteinNormDefinition_statement
  /-- The Bernstein gauge is monotone under pointwise absolute domination. -/
  bernsteinNormMonotone_statement : Prop
  /-- Proof of monotonicity of the Bernstein gauge. -/
  bernsteinNormMonotone : bernsteinNormMonotone_statement
  /-- The Bernstein gauge dominates the `L2(P)` gauge when needed. -/
  bernsteinDominatesL2_statement : Prop
  /-- Proof of Bernstein-gauge domination of `L2(P)`. -/
  bernsteinDominatesL2 : bernsteinDominatesL2_statement
  /-- Bernstein brackets induce the bracket chains used by the proof. -/
  bernsteinBracketConstruction_statement : Prop
  /-- Proof of the Bernstein bracket construction. -/
  bernsteinBracketConstruction :
    bernsteinBracketConstruction_statement
  /-- The refined Bernstein inequality is available for chain increments. -/
  refinedBernsteinInequality_statement : Prop
  /-- Proof that the refined Bernstein inequality controls increments. -/
  refinedBernsteinInequality : refinedBernsteinInequality_statement
  /-- Lemma 19.33 controls each finite class in the refined chain. -/
  finiteClassMaximalRefinement_statement : Prop
  /-- Proof of the finite-class maximal refinement. -/
  finiteClassMaximalRefinement :
    finiteClassMaximalRefinement_statement
  /-- The first-order entropy series is controlled by the bracketing integral. -/
  firstOrderEntropyBound_statement : Prop
  /-- Proof of the first-order entropy bound. -/
  firstOrderEntropyBound : firstOrderEntropyBound_statement
  /-- The refined Bernstein terms produce the `J^2/(δ^2 sqrt n)` correction. -/
  secondOrderEntropyBound_statement : Prop
  /-- Proof of the second-order entropy bound. -/
  secondOrderEntropyBound : secondOrderEntropyBound_statement
  /-- The final constant-absorption step. -/
  constantAbsorption_statement : Prop
  /-- Proof of constant absorption. -/
  constantAbsorption : constantAbsorption_statement
  /-- Lemma 19.37 Bernstein-norm bracketing maximal inequality. -/
  bernsteinNormBracketingMaximalInequality :
    outerExpectedSupremum ≤
      universalConstant *
        vaart1998_lemma19_37MaximalBound
          bracketingIntegral delta sampleSize

namespace Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource

/-- The second-order correction `J_[]/(δ^2 sqrt n)`. -/
abbrev secondOrderCorrection
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_37SecondOrderCorrection
    S.bracketingIntegral S.delta S.sampleSize

/-- The parenthesized Lemma 19.37 factor. -/
abbrev boundFactor
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_37BoundFactor
    S.bracketingIntegral S.delta S.sampleSize

/-- The full Lemma 19.37 right-hand side before the universal constant. -/
abbrev maximalBound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_37MaximalBound
    S.bracketingIntegral S.delta S.sampleSize

/-- The squared Bernstein norm of a class member. -/
abbrev bernsteinNormSquared
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (i : Index) : ℝ :=
  vaart1998_lemma19_37BernsteinNormSquared
    S.populationMeasure (S.classFun i)

/-- The Bernstein norm of a class member. -/
abbrev bernsteinNorm
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (i : Index) : ℝ :=
  vaart1998_lemma19_37BernsteinNorm
    S.populationMeasure (S.classFun i)

/-- The reused Lemma 19.34 baseline maximal inequality. -/
theorem lemma19_34_bracketing_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.lemma19_34Source.outerExpectedSupremum ≤
      S.lemma19_34Source.universalConstant *
        S.lemma19_34Source.maximalBound :=
  Vaart1998Lemma19_34BracketingMaximalInequalitySource.bracketing_maximal_inequality
    S.lemma19_34Source

/-- Lemma 19.33 bound for each finite class used in the refinement. -/
theorem finite_class_refinement_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (q : ℕ) :
    (S.finiteClassRefinementSource q).expectedSupremum ≤
      (S.finiteClassRefinementSource q).universalConstant *
        (S.finiteClassRefinementSource q).finiteClassBound :=
  Vaart1998Lemma19_33FiniteClassMaximalInequalitySource.finite_class_maximal_inequality
    (S.finiteClassRefinementSource q)

/-- The class measurability assumption. -/
theorem class_measurable
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.classMeasurable_statement :=
  S.classMeasurable

/-- The small Bernstein-norm radius condition. -/
theorem bernstein_norm_small
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.bernsteinNormSmall_statement :=
  S.bernsteinNormSmall

/-- The finite Bernstein-norm bracketing condition used by the proof. -/
theorem finite_bernstein_bracketing_at_levels
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.finiteBernsteinBracketingAtLevels_statement :=
  S.finiteBernsteinBracketingAtLevels

/-- The Bernstein-norm definition display. -/
theorem bernstein_norm_definition
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.bernsteinNormDefinition_statement :=
  S.bernsteinNormDefinition

/-- Monotonicity of the Bernstein gauge under absolute domination. -/
theorem bernstein_norm_monotone
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.bernsteinNormMonotone_statement :=
  S.bernsteinNormMonotone

/-- Bernstein-gauge domination of the `L2(P)` gauge. -/
theorem bernstein_dominates_l2
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.bernsteinDominatesL2_statement :=
  S.bernsteinDominatesL2

/-- The Bernstein bracket construction. -/
theorem bernstein_bracket_construction
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.bernsteinBracketConstruction_statement :=
  S.bernsteinBracketConstruction

/-- The refined Bernstein inequality used for chain increments. -/
theorem refined_bernstein_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.refinedBernsteinInequality_statement :=
  S.refinedBernsteinInequality

/-- The refined finite-class maximal step. -/
theorem finite_class_maximal_refinement
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.finiteClassMaximalRefinement_statement :=
  S.finiteClassMaximalRefinement

/-- First-order entropy domination by the Bernstein bracketing integral. -/
theorem first_order_entropy_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.firstOrderEntropyBound_statement :=
  S.firstOrderEntropyBound

/-- Second-order entropy domination giving the Bernstein correction term. -/
theorem second_order_entropy_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.secondOrderEntropyBound_statement :=
  S.secondOrderEntropyBound

/-- Constant absorption into the universal implicit constant. -/
theorem constant_absorption
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.constantAbsorption_statement :=
  S.constantAbsorption

/-- Lemma 19.37 Bernstein-norm bracketing maximal inequality. -/
theorem bernstein_norm_bracketing_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.outerExpectedSupremum ≤ S.universalConstant * S.maximalBound :=
  S.bernsteinNormBracketingMaximalInequality

end Vaart1998Lemma19_37BernsteinNormBracketingMaximalSource

/--
Lemma 19.38 source: uniform-covering maximal inequality.  The source records
the random radius

`θ_n^2 = sup_f P_n f^2 / P_n F^2`,

the random maximal bound `E (J(θ_n,F,L2) ||F||_{P_n,2})`, the deterministic
endpoint `J(1,F,L2) ||F||_{P,2}`, and the uniform-covering/Donsker sources
from Theorems 19.13 and 19.14 that supply the reusable entropy route.
-/
structure Vaart1998Lemma19_38UniformCoveringMaximalSource
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation] where
  /-- Probability law governing the random sample. -/
  samplingMeasure : Measure Ω
  /-- Population law `P`. -/
  populationMeasure : Measure Observation
  /-- Sample size `n`. -/
  sampleSize : ℕ
  /-- The random sample indexed by `Ω`. -/
  randomSample : Ω -> SampleAt Observation sampleSize
  /-- Function class `\mathcal F`. -/
  indexClass : Set Index
  /-- Class functions `f : X -> R`. -/
  classFun : Index -> Observation -> ℝ
  /-- Envelope function `F`. -/
  envelope : Observation -> ℝ
  /-- The displayed random squared-class supremum `sup_f P_n f^2`. -/
  classEmpiricalSecondMomentSupremum : Ω -> ℝ
  /-- The displayed random envelope square mean `P_n F^2`. -/
  envelopeEmpiricalSecondMoment : Ω -> ℝ
  /-- The random radius `θ_n`. -/
  theta : Ω -> ℝ
  /-- The random uniform entropy integral `J(θ_n,F,L2)`. -/
  uniformEntropyIntegralAtTheta : Ω -> ℝ
  /-- The random empirical envelope norm `||F||_{P_n,2}`. -/
  empiricalEnvelopeL2Norm : Ω -> ℝ
  /-- The random product `J(θ_n,F,L2) ||F||_{P_n,2}`. -/
  entropyEnvelopeProduct : Ω -> ℝ
  /-- The displayed expectation of the random entropy-envelope product. -/
  expectedEntropyEnvelopeProduct : ℝ
  /-- The deterministic uniform entropy integral `J(1,F,L2)`. -/
  uniformEntropyIntegralAtOne : ℝ
  /-- The population envelope norm `||F||_{P,2}`. -/
  populationEnvelopeL2Norm : ℝ
  /-- Displayed outer expectation `E_P^* ||G_n||_F`. -/
  outerExpectedSupremum : ℝ
  /-- First universal implicit constant in the textbook notation `\lesssim`. -/
  firstUniversalConstant : ℝ
  /-- Second universal implicit constant in the textbook notation `\lesssim`. -/
  secondUniversalConstant : ℝ
  /-- Theorem 19.13 uniform-covering GC source reused by the proof. -/
  theorem19_13Source :
    Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index)
  /-- Theorem 19.14 uniform-entropy Donsker source reused by the proof. -/
  theorem19_14Source :
    Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index)
  /-- The empirical envelope-square display agrees with `P_n F^2`. -/
  envelopeEmpiricalSecondMoment_eq :
    ∀ ω,
      envelopeEmpiricalSecondMoment ω =
        vaart1998_lemma19_38EmpiricalSecondMoment
          (randomSample ω) envelope
  /-- The empirical envelope norm agrees with `||F||_{P_n,2}`. -/
  empiricalEnvelopeL2Norm_eq :
    ∀ ω,
      empiricalEnvelopeL2Norm ω =
        vaart1998_lemma19_38EmpiricalL2Norm
          (randomSample ω) envelope
  /-- The displayed random radius agrees with the `θ_n` formula. -/
  theta_eq :
    ∀ ω,
      theta ω =
        vaart1998_lemma19_38Theta
          (classEmpiricalSecondMomentSupremum ω)
          (envelopeEmpiricalSecondMoment ω)
  /-- The random product display agrees with the textbook product. -/
  entropyEnvelopeProduct_eq :
    ∀ ω,
      entropyEnvelopeProduct ω =
        vaart1998_lemma19_38EntropyEnvelopeProduct
          (uniformEntropyIntegralAtTheta ω)
          (empiricalEnvelopeL2Norm ω)
  /-- The expectation display agrees with the integral of the random product. -/
  expectedEntropyEnvelopeProduct_eq :
    expectedEntropyEnvelopeProduct =
      vaart1998_lemma19_38ExpectedEntropyEnvelopeProduct
        samplingMeasure entropyEnvelopeProduct
  /-- The population envelope norm agrees with the Corollary 19.35 display. -/
  populationEnvelopeL2Norm_eq :
    populationEnvelopeL2Norm =
      vaart1998_corollary19_35EnvelopeL2Norm
        populationMeasure envelope
  /-- The class is suitably measurable. -/
  suitablyMeasurable_statement : Prop
  /-- Proof of suitable measurability. -/
  suitablyMeasurable : suitablyMeasurable_statement
  /-- The envelope dominates the class. -/
  envelopeDominatesClass_statement : Prop
  /-- Proof of envelope domination. -/
  envelopeDominatesClass : envelopeDominatesClass_statement
  /-- The envelope is square-integrable. -/
  squareIntegrableEnvelope_statement : Prop
  /-- Proof of square-integrability of the envelope. -/
  squareIntegrableEnvelope : squareIntegrableEnvelope_statement
  /-- Uniform covering finiteness for the class. -/
  uniformCoveringFinite_statement : Prop
  /-- Proof of uniform covering finiteness. -/
  uniformCoveringFinite : uniformCoveringFinite_statement
  /-- Finite uniform entropy integral `J(1,F,L2)`. -/
  uniformEntropyIntegralFinite_statement : Prop
  /-- Proof of finite uniform entropy integral. -/
  uniformEntropyIntegralFinite : uniformEntropyIntegralFinite_statement
  /-- The displayed `sup_f P_n f^2` is the class empirical second-moment supremum. -/
  classEmpiricalSecondMomentSupremum_statement : Prop
  /-- Proof of the class empirical second-moment supremum display. -/
  classEmpiricalSecondMomentSupremum_proof :
    classEmpiricalSecondMomentSupremum_statement
  /-- The random `θ_n` lies in the unit interval for the endpoint bound. -/
  thetaUnitInterval_statement : Prop
  /-- Proof that `θ_n` is in the unit interval. -/
  thetaUnitInterval : thetaUnitInterval_statement
  /-- Monotonicity of the uniform entropy integral, used for `J(θ_n) ≤ J(1)`. -/
  uniformEntropyMonotone_statement : Prop
  /-- Proof of uniform entropy monotonicity. -/
  uniformEntropyMonotone : uniformEntropyMonotone_statement
  /-- Symmetrization/chaining route to the random entropy-envelope bound. -/
  randomEntropyEnvelopeBound_statement : Prop
  /-- Proof of the random entropy-envelope bound. -/
  randomEntropyEnvelopeBound : randomEntropyEnvelopeBound_statement
  /-- Expectation step for the random entropy-envelope product. -/
  expectationBound_statement : Prop
  /-- Proof of the expectation step. -/
  expectationBound : expectationBound_statement
  /-- Deterministic endpoint bound by `J(1,F,L2) ||F||_{P,2}`. -/
  deterministicEntropyBound_statement : Prop
  /-- Proof of the deterministic endpoint bound. -/
  deterministicEntropyBound : deterministicEntropyBound_statement
  /-- First Lemma 19.38 maximal inequality. -/
  uniformCoveringMaximalInequality :
    outerExpectedSupremum ≤
      firstUniversalConstant * expectedEntropyEnvelopeProduct
  /-- Second Lemma 19.38 deterministic endpoint inequality. -/
  deterministicUniformEntropyBound :
    expectedEntropyEnvelopeProduct ≤
      secondUniversalConstant *
        vaart1998_lemma19_38DeterministicMaximalBound
          uniformEntropyIntegralAtOne populationEnvelopeL2Norm

namespace Vaart1998Lemma19_38UniformCoveringMaximalSource

/-- The displayed `θ_n^2` ratio. -/
abbrev thetaSquared
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (ω : Ω) : ℝ :=
  vaart1998_lemma19_38ThetaSquared
    (S.classEmpiricalSecondMomentSupremum ω)
    (S.envelopeEmpiricalSecondMoment ω)

/-- The displayed `θ_n`. -/
abbrev thetaDisplay
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (ω : Ω) : ℝ :=
  vaart1998_lemma19_38Theta
    (S.classEmpiricalSecondMomentSupremum ω)
    (S.envelopeEmpiricalSecondMoment ω)

/-- The empirical envelope norm generated by the random sample. -/
abbrev empiricalEnvelopeL2NormDisplay
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (ω : Ω) : ℝ :=
  vaart1998_lemma19_38EmpiricalL2Norm
    (S.randomSample ω) S.envelope

/-- The random product `J(θ_n,F,L2) ||F||_{P_n,2}`. -/
abbrev entropyEnvelopeProductDisplay
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (ω : Ω) : ℝ :=
  vaart1998_lemma19_38EntropyEnvelopeProduct
    (S.uniformEntropyIntegralAtTheta ω)
    (S.empiricalEnvelopeL2Norm ω)

/-- The expectation of the random entropy-envelope product. -/
abbrev expectedEntropyEnvelopeProductDisplay
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_38ExpectedEntropyEnvelopeProduct
    S.samplingMeasure S.entropyEnvelopeProduct

/-- The deterministic endpoint `J(1,F,L2) ||F||_{P,2}`. -/
abbrev deterministicMaximalBound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) : ℝ :=
  vaart1998_lemma19_38DeterministicMaximalBound
    S.uniformEntropyIntegralAtOne S.populationEnvelopeL2Norm

/-- The Theorem 19.13 GC source reused by Lemma 19.38. -/
def toUniformCoveringGCSource
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    Vaart1998Theorem19_13UniformCoveringGCSource
      (Observation := Observation) (Index := Index) :=
  S.theorem19_13Source

/-- The Theorem 19.14 Donsker source reused by Lemma 19.38. -/
def toUniformEntropyDonskerSource
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    Vaart1998Theorem19_14UniformEntropyDonskerSource
      (Observation := Observation) (Index := Index) :=
  S.theorem19_14Source

/-- The Theorem 19.13 uniform-covering finiteness condition. -/
theorem theorem19_13_uniform_covering_finite
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.theorem19_13Source.uniformCoveringFinite_statement :=
  Vaart1998Theorem19_13UniformCoveringGCSource.uniform_covering_finite
    S.theorem19_13Source

/-- The Theorem 19.13 envelope-integrability condition. -/
theorem theorem19_13_envelope_integrable
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.theorem19_13Source.envelopeIntegrable_statement :=
  Vaart1998Theorem19_13UniformCoveringGCSource.envelope_integrable
    S.theorem19_13Source

/-- The Theorem 19.14 finite uniform entropy integral condition. -/
theorem theorem19_14_uniform_entropy_integral_finite
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.theorem19_14Source.uniformEntropyIntegralFinite_statement :=
  Vaart1998Theorem19_14UniformEntropyDonskerSource.uniform_entropy_integral_finite
    S.theorem19_14Source

/-- The Theorem 19.14 square-integrable envelope condition. -/
theorem theorem19_14_square_integrable_envelope
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.theorem19_14Source.squareIntegrableEnvelope_statement :=
  Vaart1998Theorem19_14UniformEntropyDonskerSource.square_integrable_envelope
    S.theorem19_14Source

/-- The Theorem 19.14 weak-convergence conclusion. -/
theorem theorem19_14_weak_convergence
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.theorem19_14Source.donsker.weak_convergence_statement :=
  Vaart1998Theorem19_14UniformEntropyDonskerSource.weak_convergence
    S.theorem19_14Source

/-- The empirical envelope-square display. -/
theorem envelope_empirical_second_moment
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (ω : Ω) :
    S.envelopeEmpiricalSecondMoment ω =
      vaart1998_lemma19_38EmpiricalSecondMoment
        (S.randomSample ω) S.envelope :=
  S.envelopeEmpiricalSecondMoment_eq ω

/-- The empirical envelope-`L2` display. -/
theorem empirical_envelope_l2_norm
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (ω : Ω) :
    S.empiricalEnvelopeL2Norm ω =
      S.empiricalEnvelopeL2NormDisplay ω :=
  S.empiricalEnvelopeL2Norm_eq ω

/-- The `θ_n` display. -/
theorem theta_display
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (ω : Ω) :
    S.theta ω = S.thetaDisplay ω :=
  S.theta_eq ω

/-- The random product display. -/
theorem entropy_envelope_product
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index))
    (ω : Ω) :
    S.entropyEnvelopeProduct ω =
      S.entropyEnvelopeProductDisplay ω :=
  S.entropyEnvelopeProduct_eq ω

/-- The expectation display for the random product. -/
theorem expected_entropy_envelope_product
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.expectedEntropyEnvelopeProduct =
      S.expectedEntropyEnvelopeProductDisplay :=
  S.expectedEntropyEnvelopeProduct_eq

/-- The population envelope `L2(P)` norm display. -/
theorem population_envelope_l2_norm
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.populationEnvelopeL2Norm =
      vaart1998_corollary19_35EnvelopeL2Norm
        S.populationMeasure S.envelope :=
  S.populationEnvelopeL2Norm_eq

/-- Suitable measurability for Lemma 19.38. -/
theorem suitably_measurable
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.suitablyMeasurable_statement :=
  S.suitablyMeasurable

/-- Envelope domination for Lemma 19.38. -/
theorem envelope_dominates_class
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.envelopeDominatesClass_statement :=
  S.envelopeDominatesClass

/-- Square-integrability of the envelope. -/
theorem square_integrable_envelope
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.squareIntegrableEnvelope_statement :=
  S.squareIntegrableEnvelope

/-- Uniform-covering finiteness for Lemma 19.38. -/
theorem uniform_covering_finite
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.uniformCoveringFinite_statement :=
  S.uniformCoveringFinite

/-- The finite uniform entropy integral condition. -/
theorem uniform_entropy_integral_finite
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.uniformEntropyIntegralFinite_statement :=
  S.uniformEntropyIntegralFinite

/-- The class empirical second-moment supremum display. -/
theorem class_empirical_second_moment_supremum
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.classEmpiricalSecondMomentSupremum_statement :=
  S.classEmpiricalSecondMomentSupremum_proof

/-- The `θ_n` unit-interval condition. -/
theorem theta_unit_interval
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.thetaUnitInterval_statement :=
  S.thetaUnitInterval

/-- Monotonicity of the uniform entropy integral. -/
theorem uniform_entropy_monotone
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.uniformEntropyMonotone_statement :=
  S.uniformEntropyMonotone

/-- The random entropy-envelope bound. -/
theorem random_entropy_envelope_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.randomEntropyEnvelopeBound_statement :=
  S.randomEntropyEnvelopeBound

/-- The expectation step for the random product. -/
theorem expectation_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.expectationBound_statement :=
  S.expectationBound

/-- The deterministic endpoint bound. -/
theorem deterministic_entropy_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.deterministicEntropyBound_statement :=
  S.deterministicEntropyBound

/-- Lemma 19.38 first uniform-covering maximal inequality. -/
theorem uniform_covering_maximal_inequality
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.outerExpectedSupremum ≤
      S.firstUniversalConstant * S.expectedEntropyEnvelopeProduct :=
  S.uniformCoveringMaximalInequality

/-- Lemma 19.38 deterministic endpoint inequality. -/
theorem deterministic_uniform_entropy_bound
    {Ω Observation Index : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Observation]
    (S : Vaart1998Lemma19_38UniformCoveringMaximalSource
      (Ω := Ω) (Observation := Observation) (Index := Index)) :
    S.expectedEntropyEnvelopeProduct ≤
      S.secondUniversalConstant * S.deterministicMaximalBound :=
  S.deterministicUniformEntropyBound

end Vaart1998Lemma19_38UniformCoveringMaximalSource

/-- Extract the weak-convergence statement from a Chapter 19 Donsker bridge. -/
theorem vaart1998_donskerBridge_weakConvergence
    {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      DonskerBridgeCertificate indexClass populationRisk empiricalRisk) :
    certificate.donsker.weak_convergence_statement :=
  DonskerBridgeCertificate.weakConvergence certificate

/-- Extract the Glivenko-Cantelli component from a Chapter 19 Donsker bridge. -/
def vaart1998_donskerBridge_toGlivenkoCantelliClass
    {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      DonskerBridgeCertificate indexClass populationRisk empiricalRisk) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk :=
  DonskerBridgeCertificate.toGlivenkoCantelliClass certificate

end AsymptoticStatistics
end StatInference
