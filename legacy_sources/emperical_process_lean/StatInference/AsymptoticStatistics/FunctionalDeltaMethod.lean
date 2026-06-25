import StatInference.AsymptoticStatistics.EmpiricalProcesses
import StatInference.AsymptoticStatistics.RankStatistics

/-!
# van der Vaart 1998 Chapter 20 functional delta method

This module opens the Chapter 20 lane for A. W. van der Vaart,
*Asymptotic Statistics* (1998).  The first layer records the Section 20.1
von Mises calculus displays and connects the rigorous Theorem 20.8
functional-delta-method route to the existing Chapter 3 delta-method spine.

The fully Hadamard-differentiable theorem, chain rule, and first integral
example are represented by source-shaped certificates while the Fréchet
differentiable specializations are already proved from the compiled Chapter 3
`HasFDerivAt` API and mathlib's Fréchet chain rule.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal Real Topology

universe u v w x y

/-- Chapter 20 perturbation path `P + t H`. -/
def vaart1998_chapter20PerturbationPath
    {D : Type*} [Add D] [SMul ℝ D] (base direction : D) (t : ℝ) : D :=
  base + t • direction

/-- Chapter 20 functional increment `phi(T) - phi(theta)`. -/
def vaart1998_chapter20FunctionalIncrement
    {D E : Type*} [Sub E] (phi : D -> E) (T theta : D) : E :=
  phi T - phi theta

/-- The scaled statistic `r_n (T_n - theta)`. -/
def vaart1998_chapter20ScaledDifference
    {D : Type*} [Sub D] [SMul ℝ D] (rate : ℝ) (T theta : D) : D :=
  rate • (T - theta)

/-- The empirical-process display `G_n = sqrt n (P_n - P)` with a generic rate. -/
def vaart1998_chapter20EmpiricalProcess
    {D : Type*} [Sub D] [SMul ℝ D] (rate : ℝ) (empiricalLaw populationLaw : D) :
    D :=
  vaart1998_chapter20ScaledDifference rate empiricalLaw populationLaw

/-- First-order coefficient `1 / sqrt n` in the von Mises expansion. -/
def vaart1998_chapter20FirstOrderCoefficient (sampleSize : ℕ) : ℝ :=
  (Real.sqrt (sampleSize : ℝ))⁻¹

/-- Generic von Mises coefficient `1 / (m! r^m)` for rate `r`. -/
def vaart1998_chapter20VonMisesCoefficient (order : ℕ) (rate : ℝ) : ℝ :=
  ((Nat.factorial order : ℝ) * rate ^ order)⁻¹

/-- A single von Mises term with a supplied derivative display. -/
def vaart1998_chapter20VonMisesTerm
    {D E : Type*} [SMul ℝ E] (derivative : D -> E)
    (coefficient : ℝ) (direction : D) : E :=
  coefficient • derivative direction

/-- The `m`-th rate-normalized von Mises term. -/
def vaart1998_chapter20VonMisesOrderTerm
    {D E : Type*} [SMul ℝ E] (derivative : D -> E)
    (order : ℕ) (rate : ℝ) (direction : D) : E :=
  vaart1998_chapter20VonMisesCoefficient order rate • derivative direction

/-- Influence-function path `(1 - t) P + t delta_x` in an abstract affine model. -/
def vaart1998_chapter20InfluencePath
    {D : Type*} [Add D] [SMul ℝ D] (population pointMass : D) (t : ℝ) : D :=
  (1 - t) • population + t • pointMass

/-- The rescaled maps `g_n(h) = r_n (phi(theta + r_n^{-1} h) - phi(theta))`
used in the proof of Theorem 20.8. -/
def vaart1998_theorem20_8RescaledMap
    {D E : Type*} [Add D] [SMul ℝ D] [Sub E] [SMul ℝ E]
    (phi : D -> E) (theta : D) (rate : ℝ) (h : D) : E :=
  rate • (phi (theta + rate⁻¹ • h) - phi theta)

/-- The corresponding rescaled domain `D_n = {h | theta + r_n^{-1} h in D_phi}`. -/
def vaart1998_theorem20_8RescaledDomain
    {D : Type*} [Add D] [SMul ℝ D] (domain : Set D) (theta : D)
    (rate : ℝ) : Set D :=
  {h | theta + rate⁻¹ • h ∈ domain}

/-- The linearized statistic `phi'_theta (r_n (T_n - theta))`. -/
def vaart1998_theorem20_8LinearizedStatistic
    {D E : Type*} [Sub D] [SMul ℝ D] (derivative : D -> E)
    (rate : ℝ) (T theta : D) : E :=
  derivative (vaart1998_chapter20ScaledDifference rate T theta)

/-- Hadamard differentiability tangentially to a subset, in the sequence/filter
form used in the proof of van der Vaart Theorem 20.8. -/
def vaart1998_HadamardDifferentiableAtTangentially
    {D E : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (phi : D -> E) (domain tangentSet : Set D) (theta : D)
    (derivative : D →L[ℝ] E) : Prop :=
  theta ∈ domain ∧
    ∀ {ι : Type} (l : Filter ι) (t : ι -> ℝ) (hpath : ι -> D) (h : D),
      Tendsto t l (𝓝[>] (0 : ℝ)) ->
      Tendsto hpath l (𝓝 h) ->
      h ∈ tangentSet ->
      (∀ᶠ i in l, theta + t i • hpath i ∈ domain) ->
        Tendsto
          (fun i =>
            (t i)⁻¹ • (phi (theta + t i • hpath i) - phi theta) -
              derivative h)
          l (𝓝 0)

/-- Section 20.1 source package for the first-order von Mises calculus. -/
structure Vaart1998Section20_1VonMisesCalculusSource
    {D E : Type*} [Sub D] [Add D] [SMul ℝ D] [Sub E] [Add E] [SMul ℝ E] where
  statisticMap : D -> E
  populationLaw : D
  empiricalLaw : ℕ -> D
  empiricalProcess : ℕ -> D
  rate : ℕ -> ℝ
  firstDerivative : D -> E
  higherDerivative : ℕ -> D -> E
  firstOrderRemainder : ℕ -> E
  vonMisesExpansionRemainder : ℕ -> E
  empiricalProcess_eq : ∀ n,
    empiricalProcess n =
      vaart1998_chapter20EmpiricalProcess (rate n) (empiricalLaw n) populationLaw
  perturbationPath_statement : Prop
  perturbationPath : perturbationPath_statement
  firstOrderExpansion_statement : Prop
  firstOrderExpansion : firstOrderExpansion_statement
  vonMisesExpansion_statement : Prop
  vonMisesExpansion : vonMisesExpansion_statement
  empiricalProcessSubstitution_statement : Prop
  empiricalProcessSubstitution : empiricalProcessSubstitution_statement
  boundedEmpiricalProcessHeuristic_statement : Prop
  boundedEmpiricalProcessHeuristic : boundedEmpiricalProcessHeuristic_statement

namespace Vaart1998Section20_1VonMisesCalculusSource

/-- The source's displayed empirical process. -/
theorem empirical_process_eq
    {D E : Type*} [Sub D] [Add D] [SMul ℝ D] [Sub E] [Add E] [SMul ℝ E]
    (S : Vaart1998Section20_1VonMisesCalculusSource (D := D) (E := E))
    (n : ℕ) :
    S.empiricalProcess n =
      vaart1998_chapter20EmpiricalProcess (S.rate n) (S.empiricalLaw n)
        S.populationLaw :=
  S.empiricalProcess_eq n

/-- The first von Mises term `r_n^{-1} phi'_P(G_n)`. -/
def firstOrderTerm
    {D E : Type*} [Sub D] [Add D] [SMul ℝ D] [Sub E] [Add E] [SMul ℝ E]
    (S : Vaart1998Section20_1VonMisesCalculusSource (D := D) (E := E))
    (n : ℕ) : E :=
  vaart1998_chapter20VonMisesTerm S.firstDerivative (S.rate n)⁻¹
    (S.empiricalProcess n)

/-- The `m`-th formal von Mises term at rate `r_n`. -/
def orderTerm
    {D E : Type*} [Sub D] [Add D] [SMul ℝ D] [Sub E] [Add E] [SMul ℝ E]
    (S : Vaart1998Section20_1VonMisesCalculusSource (D := D) (E := E))
    (order n : ℕ) : E :=
  vaart1998_chapter20VonMisesOrderTerm (S.higherDerivative order)
    order (S.rate n) (S.empiricalProcess n)

theorem first_order_expansion
    {D E : Type*} [Sub D] [Add D] [SMul ℝ D] [Sub E] [Add E] [SMul ℝ E]
    (S : Vaart1998Section20_1VonMisesCalculusSource (D := D) (E := E)) :
    S.firstOrderExpansion_statement :=
  S.firstOrderExpansion

theorem von_mises_expansion
    {D E : Type*} [Sub D] [Add D] [SMul ℝ D] [Sub E] [Add E] [SMul ℝ E]
    (S : Vaart1998Section20_1VonMisesCalculusSource (D := D) (E := E)) :
    S.vonMisesExpansion_statement :=
  S.vonMisesExpansion

end Vaart1998Section20_1VonMisesCalculusSource

/-- Example 20.2 mean influence function display `x - int s dP(s)`. -/
def vaart1998_example20_2MeanInfluence (populationMean observation : ℝ) : ℝ :=
  observation - populationMean

/-- Source package for Example 20.2, the mean functional. -/
structure Vaart1998Example20_2MeanInfluenceSource where
  populationMean : ℝ
  influenceFunction : ℝ -> ℝ
  influenceFunction_eq : ∀ x,
    influenceFunction x = vaart1998_example20_2MeanInfluence populationMean x
  meanFunctional_statement : Prop
  meanFunctional : meanFunctional_statement
  approximationIdentity_statement : Prop
  approximationIdentity : approximationIdentity_statement
  zeroMeanInfluence_statement : Prop
  zeroMeanInfluence : zeroMeanInfluence_statement
  asymptoticNormalityRoute_statement : Prop
  asymptoticNormalityRoute : asymptoticNormalityRoute_statement

namespace Vaart1998Example20_2MeanInfluenceSource

theorem influence_function_eq (S : Vaart1998Example20_2MeanInfluenceSource)
    (x : ℝ) :
    S.influenceFunction x =
      vaart1998_example20_2MeanInfluence S.populationMean x :=
  S.influenceFunction_eq x

theorem approximation_identity (S : Vaart1998Example20_2MeanInfluenceSource) :
    S.approximationIdentity_statement :=
  S.approximationIdentity

end Vaart1998Example20_2MeanInfluenceSource

/-- Source package for the general Hadamard-differentiable Theorem 20.8. -/
structure Vaart1998Theorem20_8FunctionalDeltaMethodSource
    {Ω Ω' D E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E] where
  domain : Set D
  tangentSet : Set D
  phi : D -> E
  theta : D
  derivative : D →L[ℝ] E
  statistic : ℕ -> Ω -> D
  limitProcess : Ω' -> D
  rate : ℕ -> ℝ
  statisticInDomain : ∀ n, ∀ᵐ ω ∂P, statistic n ω ∈ domain
  rate_tendsto : Tendsto rate atTop atTop
  hadamardDifferentiable :
    vaart1998_HadamardDifferentiableAtTangentially phi domain tangentSet theta
      derivative
  scaledStatistic_converges :
    TendstoInDistribution
      (fun n ω => rate n • (statistic n ω - theta)) atTop
      limitProcess (fun _ : ℕ => P) Q
  limitInTangentSet : ∀ᵐ ω ∂Q, limitProcess ω ∈ tangentSet
  transformed_converges :
    TendstoInDistribution
      (fun n ω => rate n • (phi (statistic n ω) - phi theta)) atTop
      (fun ω => derivative (limitProcess ω)) (fun _ : ℕ => P) Q
  linearization_remainder :
    TendstoInMeasure P
      (fun n ω =>
        rate n • (phi (statistic n ω) - phi theta -
          derivative (statistic n ω - theta)))
      atTop 0

namespace Vaart1998Theorem20_8FunctionalDeltaMethodSource

/-- The rescaled proof maps `g_n` used before the extended mapping theorem. -/
def rescaledMap
    {Ω Ω' D E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    (S : @Vaart1998Theorem20_8FunctionalDeltaMethodSource Ω Ω' D E
      _ P _ _ Q _ _ _ _ _ _ _ _ _ _ _ _ _ _)
    (n : ℕ) : D -> E :=
  vaart1998_theorem20_8RescaledMap S.phi S.theta (S.rate n)

theorem functional_delta_method
    {Ω Ω' D E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    (S : @Vaart1998Theorem20_8FunctionalDeltaMethodSource Ω Ω' D E
      _ P _ _ Q _ _ _ _ _ _ _ _ _ _ _ _ _ _) :
    TendstoInDistribution
      (fun n ω => S.rate n • (S.phi (S.statistic n ω) - S.phi S.theta))
      atTop (fun ω => S.derivative (S.limitProcess ω))
      (fun _ : ℕ => P) Q :=
  S.transformed_converges

theorem linearization_remainder_converges
    {Ω Ω' D E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    (S : @Vaart1998Theorem20_8FunctionalDeltaMethodSource Ω Ω' D E
      _ P _ _ Q _ _ _ _ _ _ _ _ _ _ _ _ _ _) :
    TendstoInMeasure P
      (fun n ω =>
        S.rate n • (S.phi (S.statistic n ω) - S.phi S.theta -
          S.derivative (S.statistic n ω - S.theta)))
      atTop (0 : Ω -> E) :=
  S.linearization_remainder

end Vaart1998Theorem20_8FunctionalDeltaMethodSource

/-- Fréchet-differentiable specialization of Theorem 20.8.  This is the part
already discharged by the Chapter 3 delta-method API. -/
structure Vaart1998Theorem20_8FrechetDeltaSource
    {Ω Ω' D E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E] where
  phi : D -> E
  theta : D
  derivative : D →L[ℝ] E
  statistic : ℕ -> Ω -> D
  limitProcess : Ω' -> D
  rate : ℕ -> ℝ
  hasFDerivAt : HasFDerivAt phi derivative theta
  rate_tendsto : Tendsto rate atTop atTop
  scaledStatistic_converges :
    TendstoInDistribution
      (fun n ω => rate n • (statistic n ω - theta)) atTop
      limitProcess (fun _ : ℕ => P) Q
  statistic_aemeasurable : ∀ n, AEMeasurable (statistic n) P
  transformed_aemeasurable : ∀ n, AEMeasurable (fun ω => phi (statistic n ω)) P

namespace Vaart1998Theorem20_8FrechetDeltaSource

/-- Theorem 20.8, Fréchet case: the transformed statistic has the derivative
push-forward weak limit. -/
theorem functional_delta_method
    {Ω Ω' D E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    (S : @Vaart1998Theorem20_8FrechetDeltaSource Ω Ω' D E
      _ P _ _ Q _ _ _ _ _ _ _ _ _ _ _ _ _ _) :
    TendstoInDistribution
      (fun n ω => S.rate n • (S.phi (S.statistic n ω) - S.phi S.theta))
      atTop (fun ω => S.derivative (S.limitProcess ω))
      (fun _ : ℕ => P) Q :=
  vaart1998_theorem_3_1_delta_method_of_hasFDerivAt_distribution_aemeasurable
    (Tn := S.statistic) (T := S.limitProcess) (phi := S.phi)
    (theta := S.theta) (r := S.rate) (L := S.derivative)
    S.hasFDerivAt S.rate_tendsto S.scaledStatistic_converges
    S.statistic_aemeasurable S.transformed_aemeasurable

/-- Theorem 20.8, Fréchet case: the transformed statistic equals the linearized
statistic plus an `o_P(1)` remainder. -/
theorem linearization_remainder
    {Ω Ω' D E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [MeasurableSpace E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    (S : @Vaart1998Theorem20_8FrechetDeltaSource Ω Ω' D E
      _ P _ _ Q _ _ _ _ _ _ _ _ _ _ _ _ _ _) :
    TendstoInMeasure P
      (fun n ω =>
        S.rate n • (S.phi (S.statistic n ω) - S.phi S.theta -
          S.derivative (S.statistic n ω - S.theta)))
      atTop (0 : Ω -> E) := by
  have hsmall :
      ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
        ∀ᶠ n in atTop, ∀ ω,
          ‖S.rate n • (S.statistic n ω - S.theta)‖ < M ->
          ‖S.rate n •
              (S.phi (S.statistic n ω) - S.phi S.theta -
                S.derivative (S.statistic n ω - S.theta))‖ < ε :=
    vaart1998_delta_remainder_small_on_scaled_ball_of_hasFDerivAt
      (Tn := S.statistic) (phi := S.phi) (theta := S.theta)
      (r := S.rate) (L := S.derivative) S.hasFDerivAt S.rate_tendsto
  have hlocal :
      ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
        ∀ᶠ n in atTop,
          {ω |
            ε ≤ ‖S.rate n •
              (S.phi (S.statistic n ω) - S.phi S.theta -
                S.derivative (S.statistic n ω - S.theta))‖} ⊆
          {ω | M ≤ ‖S.rate n • (S.statistic n ω - S.theta)‖} :=
    vaart1998_delta_remainder_local_subset_of_eventually_small_on_scaled_ball
      (Tn := S.statistic) (phi := S.phi) (theta := S.theta)
      (r := S.rate) (L := S.derivative) hsmall
  have hW_tight :
      StochasticBounded P
        (fun n ω => S.rate n • (S.statistic n ω - S.theta)) :=
    vaart1998_stochasticBounded_of_tendstoInDistribution
      S.scaledStatistic_converges
  exact
    vaart1998_tendstoInMeasure_zero_of_eventually_subset_tight
      (P := P)
      (X := fun n ω =>
        S.rate n • (S.phi (S.statistic n ω) - S.phi S.theta -
          S.derivative (S.statistic n ω - S.theta)))
      (W := fun n ω => S.rate n • (S.statistic n ω - S.theta))
      hlocal hW_tight

end Vaart1998Theorem20_8FrechetDeltaSource

/-- Theorem 20.9 derivative composition `psi'_{phi(theta)} ∘ phi'_theta`. -/
def vaart1998_theorem20_9ComposedDerivative
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    (psiDerivative : E →L[ℝ] F) (phiDerivative : D →L[ℝ] E) :
    D →L[ℝ] F :=
  psiDerivative.comp phiDerivative

/-- Image tangent set `phi'_theta(D_0)` in Theorem 20.9. -/
def vaart1998_theorem20_9TangentImage
    {D E : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (phiDerivative : D →L[ℝ] E) (tangentSet : Set D) : Set E :=
  phiDerivative '' tangentSet

/-- Theorem 20.9 composed-map display `psi ∘ phi`. -/
def vaart1998_theorem20_9ComposedMap
    {D E F : Type*} (psi : E -> F) (phi : D -> E) : D -> F :=
  fun x => psi (phi x)

/-- Applying the composed derivative is applying the two derivative maps in
sequence. -/
theorem vaart1998_theorem20_9ComposedDerivative_apply
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    (psiDerivative : E →L[ℝ] F) (phiDerivative : D →L[ℝ] E) (h : D) :
    vaart1998_theorem20_9ComposedDerivative psiDerivative phiDerivative h =
      psiDerivative (phiDerivative h) :=
  rfl

/-- Theorem 20.9, Fréchet-specialized chain rule. -/
theorem vaart1998_theorem20_9_frechet_chain_rule
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    {phi : D -> E} {psi : E -> F} {theta : D}
    {phiDerivative : D →L[ℝ] E} {psiDerivative : E →L[ℝ] F}
    (hphi : HasFDerivAt phi phiDerivative theta)
    (hpsi : HasFDerivAt psi psiDerivative (phi theta)) :
    HasFDerivAt (vaart1998_theorem20_9ComposedMap psi phi)
      (vaart1998_theorem20_9ComposedDerivative psiDerivative phiDerivative)
      theta := by
  change HasFDerivAt (fun x => psi (phi x)) (psiDerivative ∘L phiDerivative) theta
  exact hpsi.comp theta hphi

/-- Source package for the general Hadamard-differentiable Theorem 20.9 chain
rule. -/
structure Vaart1998Theorem20_9ChainRuleSource
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F] where
  phiDomain : Set D
  psiDomain : Set E
  tangentSet : Set D
  phi : D -> E
  psi : E -> F
  theta : D
  phiDerivative : D →L[ℝ] E
  psiDerivative : E →L[ℝ] F
  phi_mapsTo_psiDomain : ∀ x ∈ phiDomain, phi x ∈ psiDomain
  phi_hadamard :
    vaart1998_HadamardDifferentiableAtTangentially phi phiDomain tangentSet
      theta phiDerivative
  psi_hadamard :
    vaart1998_HadamardDifferentiableAtTangentially psi psiDomain
      (vaart1998_theorem20_9TangentImage phiDerivative tangentSet)
      (phi theta) psiDerivative
  proofPath_statement : Prop
  proofPath : proofPath_statement
  chainRule :
    vaart1998_HadamardDifferentiableAtTangentially
      (vaart1998_theorem20_9ComposedMap psi phi) phiDomain tangentSet theta
      (vaart1998_theorem20_9ComposedDerivative psiDerivative phiDerivative)

namespace Vaart1998Theorem20_9ChainRuleSource

/-- The derivative map stated by Theorem 20.9. -/
def composedDerivative
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    (S : @Vaart1998Theorem20_9ChainRuleSource D E F _ _ _ _ _ _) :
    D →L[ℝ] F :=
  vaart1998_theorem20_9ComposedDerivative S.psiDerivative S.phiDerivative

theorem composed_derivative_apply
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    (S : @Vaart1998Theorem20_9ChainRuleSource D E F _ _ _ _ _ _)
    (h : D) :
    S.composedDerivative h = S.psiDerivative (S.phiDerivative h) :=
  rfl

theorem chain_rule
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    (S : @Vaart1998Theorem20_9ChainRuleSource D E F _ _ _ _ _ _) :
    vaart1998_HadamardDifferentiableAtTangentially
      (vaart1998_theorem20_9ComposedMap S.psi S.phi) S.phiDomain
      S.tangentSet S.theta S.composedDerivative :=
  S.chainRule

end Vaart1998Theorem20_9ChainRuleSource

/-- Fréchet-specialized source package for Theorem 20.9. -/
structure Vaart1998Theorem20_9FrechetChainRuleSource
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F] where
  phi : D -> E
  psi : E -> F
  theta : D
  phiDerivative : D →L[ℝ] E
  psiDerivative : E →L[ℝ] F
  phi_hasFDerivAt : HasFDerivAt phi phiDerivative theta
  psi_hasFDerivAt : HasFDerivAt psi psiDerivative (phi theta)

namespace Vaart1998Theorem20_9FrechetChainRuleSource

def composedDerivative
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    (S : @Vaart1998Theorem20_9FrechetChainRuleSource D E F _ _ _ _ _ _) :
    D →L[ℝ] F :=
  vaart1998_theorem20_9ComposedDerivative S.psiDerivative S.phiDerivative

/-- Theorem 20.9, compiled Fréchet chain-rule extractor. -/
theorem chain_rule
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    (S : @Vaart1998Theorem20_9FrechetChainRuleSource D E F _ _ _ _ _ _) :
    HasFDerivAt (vaart1998_theorem20_9ComposedMap S.psi S.phi)
      S.composedDerivative S.theta :=
  vaart1998_theorem20_9_frechet_chain_rule
    S.phi_hasFDerivAt S.psi_hasFDerivAt

theorem composed_derivative_apply
    {D E F : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    (S : @Vaart1998Theorem20_9FrechetChainRuleSource D E F _ _ _ _ _ _)
    (h : D) :
    S.composedDerivative h = S.psiDerivative (S.phiDerivative h) :=
  rfl

end Vaart1998Theorem20_9FrechetChainRuleSource

/-- Lemma 20.10 functional `(F₁, F₂) ↦ ∫ phi(F₁) dF₂`, with the
Stieltjes integral supplied by the surrounding analytic development. -/
def vaart1998_lemma20_10IntegralFunctional
    {Func : Type*} (stieltjesIntegral : Func -> Func -> ℝ)
    (phiCompose : Func -> Func) (F : Func × Func) : ℝ :=
  stieltjesIntegral (phiCompose F.1) F.2

/-- Lemma 20.10 derivative display:
`h₂ phi(F₁)| - ∫ h₂- d phi(F₁) + ∫ phi'(F₁) h₁ dF₂`. -/
def vaart1998_lemma20_10DerivativeDisplay
    {Func : Type*} (boundaryTerm : Func -> Func -> ℝ)
    (stieltjesIntegral : Func -> Func -> ℝ) (leftLimit : Func -> Func)
    (phiCompose : Func -> Func) (phiPrimeTimes : Func -> Func -> Func)
    (F1 F2 h1 h2 : Func) : ℝ :=
  boundaryTerm (phiCompose F1) h2 -
    stieltjesIntegral (leftLimit h2) (phiCompose F1) +
      stieltjesIntegral (phiPrimeTimes F1 h1) F2

/-- The continuous linear derivative map for the first assertion of Lemma
20.10, assembled from the three displayed linear terms. -/
def vaart1998_lemma20_10DerivativeMap
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (boundaryDerivative partialIntegrationDerivative firstCoordinateDerivative :
      Func →L[ℝ] ℝ) :
    Func × Func →L[ℝ] ℝ :=
  boundaryDerivative.comp (ContinuousLinearMap.snd ℝ Func Func) -
    partialIntegrationDerivative.comp (ContinuousLinearMap.snd ℝ Func Func) +
      firstCoordinateDerivative.comp (ContinuousLinearMap.fst ℝ Func Func)

theorem vaart1998_lemma20_10DerivativeMap_apply
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (boundaryDerivative partialIntegrationDerivative firstCoordinateDerivative :
      Func →L[ℝ] ℝ) (h1 h2 : Func) :
    vaart1998_lemma20_10DerivativeMap boundaryDerivative
        partialIntegrationDerivative firstCoordinateDerivative (h1, h2) =
      boundaryDerivative h2 - partialIntegrationDerivative h2 +
        firstCoordinateDerivative h1 := by
  simp [vaart1998_lemma20_10DerivativeMap]

/-- Source package for van der Vaart Lemma 20.10.  It records the analytic
Stieltjes/BV hypotheses and the proof-route estimates, while exposing the
derivative as a compiled continuous linear map on the product function space. -/
structure Vaart1998Lemma20_10IntegralHadamardSource
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func] where
  domain : Set (Func × Func)
  tangentSet : Set (Func × Func)
  boundedVariationDomain : Set Func
  phiCompose : Func -> Func
  phiPrimeTimes : Func -> Func -> Func
  leftLimit : Func -> Func
  stieltjesIntegral : Func -> Func -> ℝ
  boundaryTerm : Func -> Func -> ℝ
  baseF1 : Func
  baseF2 : Func
  pair_mem_domain : (baseF1, baseF2) ∈ domain
  F1_boundedVariation : baseF1 ∈ boundedVariationDomain
  F2_boundedVariation : baseF2 ∈ boundedVariationDomain
  phi_twice_continuouslyDifferentiable_statement : Prop
  phi_twice_continuouslyDifferentiable :
    phi_twice_continuouslyDifferentiable_statement
  firstCoordinateDerivative : Func →L[ℝ] ℝ
  boundaryDerivative : Func →L[ℝ] ℝ
  partialIntegrationDerivative : Func →L[ℝ] ℝ
  firstCoordinateDerivative_eq : ∀ h1,
    firstCoordinateDerivative h1 =
      stieltjesIntegral (phiPrimeTimes baseF1 h1) baseF2
  boundaryDerivative_eq : ∀ h2,
    boundaryDerivative h2 = boundaryTerm (phiCompose baseF1) h2
  partialIntegrationDerivative_eq : ∀ h2,
    partialIntegrationDerivative h2 =
      stieltjesIntegral (leftLimit h2) (phiCompose baseF1)
  decomposition_statement : Prop
  decomposition : decomposition_statement
  taylorRemainderBound_statement : Prop
  taylorRemainderBound : taylorRemainderBound_statement
  partialIntegration_statement : Prop
  partialIntegration : partialIntegration_statement
  gridApproximation_statement : Prop
  gridApproximation : gridApproximation_statement
  derivativeContinuity_statement : Prop
  derivativeContinuity : derivativeContinuity_statement
  hadamardDifferentiable :
    vaart1998_HadamardDifferentiableAtTangentially
      (vaart1998_lemma20_10IntegralFunctional stieltjesIntegral phiCompose)
      domain tangentSet (baseF1, baseF2)
      (vaart1998_lemma20_10DerivativeMap boundaryDerivative
        partialIntegrationDerivative firstCoordinateDerivative)
  indefiniteIntegralHadamard_statement : Prop
  indefiniteIntegralHadamard : indefiniteIntegralHadamard_statement

namespace Vaart1998Lemma20_10IntegralHadamardSource

/-- The integral functional in Lemma 20.10. -/
def functional
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma20_10IntegralHadamardSource Func _ _) :
    Func × Func -> ℝ :=
  vaart1998_lemma20_10IntegralFunctional S.stieltjesIntegral S.phiCompose

/-- The derivative map displayed in Lemma 20.10. -/
def derivative
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma20_10IntegralHadamardSource Func _ _) :
    Func × Func →L[ℝ] ℝ :=
  vaart1998_lemma20_10DerivativeMap S.boundaryDerivative
    S.partialIntegrationDerivative S.firstCoordinateDerivative

theorem derivative_apply
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma20_10IntegralHadamardSource Func _ _)
    (h1 h2 : Func) :
    S.derivative (h1, h2) =
      S.boundaryDerivative h2 - S.partialIntegrationDerivative h2 +
        S.firstCoordinateDerivative h1 :=
  vaart1998_lemma20_10DerivativeMap_apply S.boundaryDerivative
    S.partialIntegrationDerivative S.firstCoordinateDerivative h1 h2

theorem derivative_display
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma20_10IntegralHadamardSource Func _ _)
    (h1 h2 : Func) :
    S.derivative (h1, h2) =
      vaart1998_lemma20_10DerivativeDisplay S.boundaryTerm
        S.stieltjesIntegral S.leftLimit S.phiCompose S.phiPrimeTimes
        S.baseF1 S.baseF2 h1 h2 := by
  rw [derivative_apply]
  rw [S.boundaryDerivative_eq h2, S.partialIntegrationDerivative_eq h2,
    S.firstCoordinateDerivative_eq h1]
  rfl

/-- Lemma 20.10 first assertion: the integral functional is Hadamard
differentiable with the displayed derivative. -/
theorem hadamard_differentiable
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma20_10IntegralHadamardSource Func _ _) :
    vaart1998_HadamardDifferentiableAtTangentially S.functional S.domain
      S.tangentSet (S.baseF1, S.baseF2) S.derivative := by
  simpa [functional, derivative] using S.hadamardDifferentiable

theorem indefinite_integral_hadamard
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma20_10IntegralHadamardSource Func _ _) :
    S.indefiniteIntegralHadamard_statement :=
  S.indefiniteIntegralHadamard

end Vaart1998Lemma20_10IntegralHadamardSource

/-- Example 20.11 limiting linear functional for the Wilcoxon integral
statistic, with the two scaled Brownian bridges supplied by the empirical
process source layer. -/
def vaart1998_example20_11WilcoxonLimitDisplay
    {ΩLimit Func : Type*} (negativeIntegral firstIntegral : Func -> ℝ)
    (scaledBrownianF scaledBrownianG : ΩLimit -> Func) : ΩLimit -> ℝ :=
  fun ω =>
    - negativeIntegral (scaledBrownianG ω) +
      firstIntegral (scaledBrownianF ω)

/-- Example 20.11 linearized sequence appearing after the strong delta-method
form of Lemma 20.10. -/
def vaart1998_example20_11WilcoxonLinearizedSequence
    {Ω Func : Type*} (negativeIntegral firstIntegral : Func -> ℝ)
    (scaledEmpiricalF scaledEmpiricalG : ℕ -> Ω -> Func) : ℕ -> Ω -> ℝ :=
  fun n ω =>
    - negativeIntegral (scaledEmpiricalG n ω) +
      firstIntegral (scaledEmpiricalF n ω)

/-- Example 20.11 statistic `∫ F_m dG_n` expressed through the Lemma 20.10
integral functional. -/
def vaart1998_example20_11WilcoxonIntegralStatistic
    {Ω Func : Type*} (stieltjesIntegral : Func -> Func -> ℝ)
    (phiCompose : Func -> Func) (empiricalF empiricalG : ℕ -> Ω -> Func) :
    ℕ -> Ω -> ℝ :=
  fun n ω =>
    vaart1998_lemma20_10IntegralFunctional stieltjesIntegral phiCompose
      (empiricalF n ω, empiricalG n ω)

/-- Source package for van der Vaart Example 20.11.  It records the
two-sample empirical-CDF Donsker input, the Slutsky sample-share step
`m / (m + n) -> λ`, and the Lemma 20.10 functional-delta-method transfer to
the Wilcoxon integral statistic. -/
structure Vaart1998Example20_11WilcoxonDeltaMethodSource
    (Func : Type*) [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  lemma20_10Source : @Vaart1998Lemma20_10IntegralHadamardSource Func _ _
  donskerFSource : Vaart1998Theorem19_3EmpiricalCDFDonskerSource
  donskerGSource : Vaart1998Theorem19_3EmpiricalCDFDonskerSource
  distributionF : Func
  distributionG : Func
  empiricalF : ℕ -> Ω -> Func
  empiricalG : ℕ -> Ω -> Func
  scaledEmpiricalF : ℕ -> Ω -> Func
  scaledEmpiricalG : ℕ -> Ω -> Func
  brownianBridgeF : ΩLimit -> Func
  brownianBridgeG : ΩLimit -> Func
  scaledBrownianBridgeF : ΩLimit -> Func
  scaledBrownianBridgeG : ΩLimit -> Func
  lambda : ℝ
  lambda_between_zero_and_one : 0 < lambda ∧ lambda < 1
  sampleShare_tendsto_lambda_statement : Prop
  sampleShare_tendsto_lambda : sampleShare_tendsto_lambda_statement
  jointEmpiricalProcessConvergence_statement : Prop
  jointEmpiricalProcessConvergence :
    jointEmpiricalProcessConvergence_statement
  donsker_slutsky_route_statement : Prop
  donsker_slutsky_route : donsker_slutsky_route_statement
  negativeIntegral : Func -> ℝ
  firstIntegral : Func -> ℝ
  wilcoxonIntegralStatistic : ℕ -> Ω -> ℝ
  wilcoxonIntegralLimit : ΩLimit -> ℝ
  linearizedSequence : ℕ -> Ω -> ℝ
  wilcoxonIntegralStatistic_eq :
    wilcoxonIntegralStatistic =
      vaart1998_example20_11WilcoxonIntegralStatistic
        lemma20_10Source.stieltjesIntegral lemma20_10Source.phiCompose
        empiricalF empiricalG
  wilcoxonIntegralLimit_eq :
    wilcoxonIntegralLimit =
      vaart1998_example20_11WilcoxonLimitDisplay
        negativeIntegral firstIntegral scaledBrownianBridgeF
        scaledBrownianBridgeG
  linearizedSequence_eq :
    linearizedSequence =
      vaart1998_example20_11WilcoxonLinearizedSequence
        negativeIntegral firstIntegral scaledEmpiricalF scaledEmpiricalG
  functional_delta_method_route_statement : Prop
  functional_delta_method_route : functional_delta_method_route_statement
  wilcoxonIntegral_converges :
    TendstoInDistribution wilcoxonIntegralStatistic atTop
      wilcoxonIntegralLimit P LimitLaw
  linearizedSequence_converges :
    TendstoInDistribution linearizedSequence atTop
      wilcoxonIntegralLimit P LimitLaw
  limitGaussian_statement : Prop
  limitGaussian : limitGaussian_statement
  realCLTRoute_statement : Prop
  realCLTRoute : realCLTRoute_statement

namespace Vaart1998Example20_11WilcoxonDeltaMethodSource

theorem donsker_F
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    S.donskerFSource.weakConvergence_statement :=
  S.donskerFSource.weak_convergence

theorem donsker_G
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    S.donskerGSource.weakConvergence_statement :=
  S.donskerGSource.weak_convergence

theorem joint_empirical_process_convergence
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    S.jointEmpiricalProcessConvergence_statement :=
  S.jointEmpiricalProcessConvergence

theorem wilcoxon_integral_statistic_eq
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    S.wilcoxonIntegralStatistic =
      vaart1998_example20_11WilcoxonIntegralStatistic
        S.lemma20_10Source.stieltjesIntegral S.lemma20_10Source.phiCompose
        S.empiricalF S.empiricalG :=
  S.wilcoxonIntegralStatistic_eq

theorem wilcoxon_limit_eq
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    S.wilcoxonIntegralLimit =
      vaart1998_example20_11WilcoxonLimitDisplay S.negativeIntegral
        S.firstIntegral S.scaledBrownianBridgeF S.scaledBrownianBridgeG :=
  S.wilcoxonIntegralLimit_eq

theorem linearized_sequence_eq
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    S.linearizedSequence =
      vaart1998_example20_11WilcoxonLinearizedSequence S.negativeIntegral
        S.firstIntegral S.scaledEmpiricalF S.scaledEmpiricalG :=
  S.linearizedSequence_eq

theorem wilcoxon_integral_converges
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    TendstoInDistribution S.wilcoxonIntegralStatistic atTop
      S.wilcoxonIntegralLimit P LimitLaw :=
  S.wilcoxonIntegral_converges

theorem linearized_sequence_converges
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    TendstoInDistribution S.linearizedSequence atTop
      S.wilcoxonIntegralLimit P LimitLaw :=
  S.linearizedSequence_converges

theorem limit_gaussian
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw) :
    S.limitGaussian_statement :=
  S.limitGaussian

end Vaart1998Example20_11WilcoxonDeltaMethodSource

/-- Example 20.12 display
`n^{-1} sum_{j=m+1}^N phi(R_{Nj} / N)` for the second sample ranks. -/
def vaart1998_example20_12TwoSampleRankStatisticDisplay
    {Ω κ : Type*} [Fintype κ] (score : ℝ -> ℝ)
    (pooledRank : κ -> Ω -> ℝ) (pooledSampleSize : ℝ) : Ω -> ℝ :=
  fun ω =>
    (Fintype.card κ : ℝ)⁻¹ *
      ∑ j : κ, score (pooledRank j ω / pooledSampleSize)

/-- Source package for Example 20.12.  It connects the pooled empirical
identity `N H_N = m F_m + n G_n`, Example 20.11's joint empirical-process
limit, and Chapter 13's rank asymptotic-equivalence source. -/
structure Vaart1998Example20_12TwoSampleRankStatisticSource
    (Func κ : Type*) [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [Fintype κ] {Ω ΩLimit : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  example20_11Source :
    Vaart1998Example20_11WilcoxonDeltaMethodSource Func P LimitLaw
  rankAsymptoticSource :
    Vaart1998Theorem13_5RankAsymptoticEquivalenceSource P LimitLaw
  score : ℝ -> ℝ
  pooledRank : κ -> Ω -> ℝ
  pooledSampleSize : ℕ -> ℝ
  pooledEmpirical : ℕ -> Ω -> Func
  secondEmpirical : ℕ -> Ω -> Func
  rankStatistic : ℕ -> Ω -> ℝ
  rankLimitStatistic : ΩLimit -> ℝ
  rankStatistic_display_eq :
    rankStatistic =
      fun n =>
        vaart1998_example20_12TwoSampleRankStatisticDisplay score pooledRank
          (pooledSampleSize n)
  pooledEmpiricalIdentity_statement : Prop
  pooledEmpiricalIdentity : pooledEmpiricalIdentity_statement
  empiricalPairConvergence_statement : Prop
  empiricalPairConvergence : empiricalPairConvergence_statement
  deltaMethodRoute_statement : Prop
  deltaMethodRoute : deltaMethodRoute_statement
  rankStatistic_eq_source :
    rankAsymptoticSource.scaledStatistic = rankStatistic
  rankLimit_eq_source :
    rankAsymptoticSource.limitStatistic = rankLimitStatistic
  asymptoticNormality_statement : Prop
  asymptoticNormality : asymptoticNormality_statement

namespace Vaart1998Example20_12TwoSampleRankStatisticSource

theorem rank_statistic_display
    {Func κ : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [Fintype κ] {Ω ΩLimit : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_12TwoSampleRankStatisticSource
      Func κ P LimitLaw) :
    S.rankStatistic =
      fun n =>
        vaart1998_example20_12TwoSampleRankStatisticDisplay S.score
          S.pooledRank (S.pooledSampleSize n) :=
  S.rankStatistic_display_eq

theorem pooled_empirical_identity
    {Func κ : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [Fintype κ] {Ω ΩLimit : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_12TwoSampleRankStatisticSource
      Func κ P LimitLaw) :
    S.pooledEmpiricalIdentity_statement :=
  S.pooledEmpiricalIdentity

theorem empirical_pair_convergence
    {Func κ : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [Fintype κ] {Ω ΩLimit : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_12TwoSampleRankStatisticSource
      Func κ P LimitLaw) :
    S.empiricalPairConvergence_statement :=
  S.empiricalPairConvergence

theorem rank_statistic_converges
    {Func κ : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [Fintype κ] {Ω ΩLimit : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_12TwoSampleRankStatisticSource
      Func κ P LimitLaw) :
    TendstoInDistribution S.rankStatistic atTop S.rankLimitStatistic
      P LimitLaw := by
  have h :=
    Vaart1998Theorem13_5RankAsymptoticEquivalenceSource.statistic_limit
      S.rankAsymptoticSource
  rw [S.rankStatistic_eq_source, S.rankLimit_eq_source] at h
  exact h

theorem asymptotic_normality
    {Func κ : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [Fintype κ] {Ω ΩLimit : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_12TwoSampleRankStatisticSource
      Func κ P LimitLaw) :
    S.asymptoticNormality_statement :=
  S.asymptoticNormality

end Vaart1998Example20_12TwoSampleRankStatisticSource

/-- Lemma 20.14 first decomposition map `F ↦ (F, 1 - F_-)`. -/
def vaart1998_lemma20_14FirstHazardDecomposition
    {Func : Type*} (survivalLeft : Func -> Func) (F : Func) :
    Func × Func :=
  (F, survivalLeft F)

/-- Lemma 20.14 reciprocal step `(F, S) ↦ (F, 1 / S)`. -/
def vaart1998_lemma20_14ReciprocalHazardDecomposition
    {Func : Type*} (reciprocal : Func -> Func) (pair : Func × Func) :
    Func × Func :=
  (pair.1, reciprocal pair.2)

/-- Lemma 20.14 indefinite-integral step
`(F, G) ↦ (t ↦ ∫_[0,t] G dF)`. -/
def vaart1998_lemma20_14IndefiniteIntegralMap
    {Func : Type*} (indefiniteIntegral : Func -> Func -> Func)
    (pair : Func × Func) : Func :=
  indefiniteIntegral pair.2 pair.1

/-- Lemma 20.14 cumulative hazard map
`F ↦ Λ_F = ∫ dF / (1 - F_-)`. -/
def vaart1998_lemma20_14CumulativeHazardMap
    {Func : Type*} (indefiniteIntegral : Func -> Func -> Func)
    (survivalLeft reciprocal : Func -> Func) (F : Func) : Func :=
  indefiniteIntegral (reciprocal (survivalLeft F)) F

theorem vaart1998_lemma20_14CumulativeHazardMap_decomposition
    {Func : Type*} (indefiniteIntegral : Func -> Func -> Func)
    (survivalLeft reciprocal : Func -> Func) (F : Func) :
    vaart1998_lemma20_14IndefiniteIntegralMap indefiniteIntegral
        (vaart1998_lemma20_14ReciprocalHazardDecomposition reciprocal
          (vaart1998_lemma20_14FirstHazardDecomposition survivalLeft F)) =
      vaart1998_lemma20_14CumulativeHazardMap indefiniteIntegral
        survivalLeft reciprocal F :=
  rfl

/-- Lemma 20.14 product-integral inverse map
`Λ ↦ F_Λ`, with the survival product-integral and final `1 - survival`
operation supplied by the surrounding analysis. -/
def vaart1998_lemma20_14ProductIntegralDistributionMap
    {Func : Type*} (productIntegralSurvival oneMinusSurvival : Func -> Func)
    (hazard : Func) : Func :=
  oneMinusSurvival (productIntegralSurvival hazard)

/-- Source package for Lemma 20.14.  It records the domains of monotone cadlag
distribution and cumulative-hazard functions, the decomposition
`F ↦ (F, 1-F_-) ↦ (F, 1/(1-F_-)) ↦ ∫ dF/(1-F_-)`, and the product-integral
inverse map. -/
structure Vaart1998Lemma20_14CumulativeHazardHadamardSource
    (Func : Type*) [NormedAddCommGroup Func] [NormedSpace ℝ Func] where
  distributionDomain : Set Func
  hazardDomain : Set Func
  distributionTangentSet : Set Func
  hazardTangentSet : Set Func
  tau : ℝ
  epsilon : ℝ
  epsilon_pos : 0 < epsilon
  hazardBound : ℝ
  distributionDomain_statement : Prop
  distributionDomain_source : distributionDomain_statement
  hazardDomain_statement : Prop
  hazardDomain_source : hazardDomain_statement
  survivalLeft : Func -> Func
  reciprocal : Func -> Func
  indefiniteIntegral : Func -> Func -> Func
  productIntegralSurvival : Func -> Func
  oneMinusSurvival : Func -> Func
  cumulativeHazardMap : Func -> Func
  distributionFromHazardMap : Func -> Func
  baseDistribution : Func
  baseHazard : Func
  cumulativeHazardDerivative : Func →L[ℝ] Func
  productIntegralDerivative : Func →L[ℝ] Func
  lemma20_10Source : @Vaart1998Lemma20_10IntegralHadamardSource Func _ _
  cumulativeHazardMap_eq :
    cumulativeHazardMap =
      vaart1998_lemma20_14CumulativeHazardMap indefiniteIntegral
        survivalLeft reciprocal
  distributionFromHazardMap_eq :
    distributionFromHazardMap =
      vaart1998_lemma20_14ProductIntegralDistributionMap
        productIntegralSurvival oneMinusSurvival
  productIntegralDisplay20_13_statement : Prop
  productIntegralDisplay20_13 : productIntegralDisplay20_13_statement
  inverseCorrespondence_statement : Prop
  inverseCorrespondence : inverseCorrespondence_statement
  firstDecompositionHadamard_statement : Prop
  firstDecompositionHadamard : firstDecompositionHadamard_statement
  reciprocalHadamard_statement : Prop
  reciprocalHadamard : reciprocalHadamard_statement
  chainRuleRoute_statement : Prop
  chainRuleRoute : chainRuleRoute_statement
  cumulativeHazardHadamard :
    vaart1998_HadamardDifferentiableAtTangentially cumulativeHazardMap
      distributionDomain distributionTangentSet baseDistribution
      cumulativeHazardDerivative
  productIntegralHadamardRoute_statement : Prop
  productIntegralHadamardRoute : productIntegralHadamardRoute_statement
  productIntegralHadamard :
    vaart1998_HadamardDifferentiableAtTangentially distributionFromHazardMap
      hazardDomain hazardTangentSet baseHazard productIntegralDerivative

namespace Vaart1998Lemma20_14CumulativeHazardHadamardSource

theorem cumulative_hazard_map_eq
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : Vaart1998Lemma20_14CumulativeHazardHadamardSource Func) :
    S.cumulativeHazardMap =
      vaart1998_lemma20_14CumulativeHazardMap S.indefiniteIntegral
        S.survivalLeft S.reciprocal :=
  S.cumulativeHazardMap_eq

theorem distribution_from_hazard_map_eq
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : Vaart1998Lemma20_14CumulativeHazardHadamardSource Func) :
    S.distributionFromHazardMap =
      vaart1998_lemma20_14ProductIntegralDistributionMap
        S.productIntegralSurvival S.oneMinusSurvival :=
  S.distributionFromHazardMap_eq

theorem indefinite_integral_hadamard
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : Vaart1998Lemma20_14CumulativeHazardHadamardSource Func) :
    S.lemma20_10Source.indefiniteIntegralHadamard_statement :=
  S.lemma20_10Source.indefinite_integral_hadamard

theorem cumulative_hazard_hadamard
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : Vaart1998Lemma20_14CumulativeHazardHadamardSource Func) :
    vaart1998_HadamardDifferentiableAtTangentially S.cumulativeHazardMap
      S.distributionDomain S.distributionTangentSet S.baseDistribution
      S.cumulativeHazardDerivative :=
  S.cumulativeHazardHadamard

theorem product_integral_hadamard
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : Vaart1998Lemma20_14CumulativeHazardHadamardSource Func) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.distributionFromHazardMap S.hazardDomain S.hazardTangentSet
      S.baseHazard S.productIntegralDerivative :=
  S.productIntegralHadamard

theorem product_integral_display
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : Vaart1998Lemma20_14CumulativeHazardHadamardSource Func) :
    S.productIntegralDisplay20_13_statement :=
  S.productIntegralDisplay20_13

theorem inverse_correspondence
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : Vaart1998Lemma20_14CumulativeHazardHadamardSource Func) :
    S.inverseCorrespondence_statement :=
  S.inverseCorrespondence

end Vaart1998Lemma20_14CumulativeHazardHadamardSource

/-- Example 20.15 Nelson-Aalen estimator
`Λ_hat_n(t) = ∫_[0,t] (1 - H_{n-})^{-1} d H_{1n}`. -/
def vaart1998_example20_15NelsonAalenEstimator
    {Ω Func : Type*} (indefiniteIntegral : Func -> Func -> Func)
    (atRiskReciprocal subDistributionEmpirical : ℕ -> Ω -> Func) :
    ℕ -> Ω -> Func :=
  fun n ω => indefiniteIntegral (atRiskReciprocal n ω)
    (subDistributionEmpirical n ω)

/-- Example 20.15 Kaplan-Meier/product-limit survival estimator obtained by
applying the product-integral map to the Nelson-Aalen estimator. -/
def vaart1998_example20_15KaplanMeierSurvivalEstimator
    {Ω Func : Type*} (productIntegralSurvival : Func -> Func)
    (nelsonAalenEstimator : ℕ -> Ω -> Func) : ℕ -> Ω -> Func :=
  fun n ω => productIntegralSurvival (nelsonAalenEstimator n ω)

/-- Example 20.15 finite jump-product display for the product-limit estimator.
The inclusion of the condition `X_(i) <= t` is supplied through unit factors in
`oneStepSurvivalFactor`. -/
def vaart1998_example20_15KaplanMeierFiniteProduct
    {Ω EventIndex : Type*} [Fintype EventIndex]
    (oneStepSurvivalFactor : ℕ -> EventIndex -> Ω -> ℝ)
    (eventExponent : ℕ -> EventIndex -> Ω -> ℕ) : ℕ -> Ω -> ℝ :=
  fun n ω =>
    ∏ i : EventIndex,
      (oneStepSurvivalFactor n i ω) ^ eventExponent n i ω

/-- Source package for Example 20.15.  It records the right-censoring
distributional identities, the bivariate empirical-process normality input,
the Nelson-Aalen functional-delta construction, and the Kaplan-Meier
product-integral handoff. -/
structure Vaart1998Example20_15NelsonAalenEstimatorSource
    (Func EventIndex : Type*) [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  lemma20_14Source :
    Vaart1998Lemma20_14CumulativeHazardHadamardSource Func
  failureDistribution : Func
  censoringDistribution : Func
  observationDistribution : Func
  subDistribution : Func
  trueCumulativeHazard : Func
  empiricalObservationDistribution : ℕ -> Ω -> Func
  empiricalSubDistribution : ℕ -> Ω -> Func
  atRiskReciprocal : ℕ -> Ω -> Func
  bivariateEmpiricalDonsker_statement : Prop
  bivariateEmpiricalDonsker : bivariateEmpiricalDonsker_statement
  censoringIdentity_statement : Prop
  censoringIdentity : censoringIdentity_statement
  subDistributionIdentity_statement : Prop
  subDistributionIdentity : subDistributionIdentity_statement
  pairAsymptoticNormality_statement : Prop
  pairAsymptoticNormality : pairAsymptoticNormality_statement
  constructionDecomposition_statement : Prop
  constructionDecomposition : constructionDecomposition_statement
  nelsonAalenEstimator : ℕ -> Ω -> Func
  nelsonAalenLimit : ΩLimit -> Func
  nelsonAalenEstimator_eq :
    nelsonAalenEstimator =
      vaart1998_example20_15NelsonAalenEstimator
        lemma20_14Source.indefiniteIntegral atRiskReciprocal
        empiricalSubDistribution
  nelsonAalenFunctionalDeltaRoute_statement : Prop
  nelsonAalenFunctionalDeltaRoute :
    nelsonAalenFunctionalDeltaRoute_statement
  nelsonAalen_converges :
    TendstoInDistribution nelsonAalenEstimator atTop nelsonAalenLimit
      P LimitLaw
  fixedTimeAsymptoticNormality_statement : Prop
  fixedTimeAsymptoticNormality : fixedTimeAsymptoticNormality_statement
  processAsymptoticNormality_statement : Prop
  processAsymptoticNormality : processAsymptoticNormality_statement
  kaplanMeierSurvivalEstimator : ℕ -> Ω -> Func
  kaplanMeierSurvivalLimit : ΩLimit -> Func
  kaplanMeierSurvivalEstimator_eq :
    kaplanMeierSurvivalEstimator =
      vaart1998_example20_15KaplanMeierSurvivalEstimator
        lemma20_14Source.productIntegralSurvival nelsonAalenEstimator
  oneStepSurvivalFactor : ℕ -> EventIndex -> Ω -> ℝ
  eventExponent : ℕ -> EventIndex -> Ω -> ℕ
  kaplanMeierFiniteProductStatistic : ℕ -> Ω -> ℝ
  kaplanMeierFiniteProduct_eq :
    kaplanMeierFiniteProductStatistic =
      vaart1998_example20_15KaplanMeierFiniteProduct
        oneStepSurvivalFactor eventExponent
  kaplanMeierProductIntegralRoute_statement : Prop
  kaplanMeierProductIntegralRoute :
    kaplanMeierProductIntegralRoute_statement
  kaplanMeier_converges :
    TendstoInDistribution kaplanMeierSurvivalEstimator atTop
      kaplanMeierSurvivalLimit P LimitLaw

namespace Vaart1998Example20_15NelsonAalenEstimatorSource

theorem bivariate_empirical_donsker
    {Func EventIndex : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_15NelsonAalenEstimatorSource
      Func EventIndex P LimitLaw) :
    S.bivariateEmpiricalDonsker_statement :=
  S.bivariateEmpiricalDonsker

theorem nelson_aalen_estimator_eq
    {Func EventIndex : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_15NelsonAalenEstimatorSource
      Func EventIndex P LimitLaw) :
    S.nelsonAalenEstimator =
      vaart1998_example20_15NelsonAalenEstimator
        S.lemma20_14Source.indefiniteIntegral S.atRiskReciprocal
        S.empiricalSubDistribution :=
  S.nelsonAalenEstimator_eq

theorem nelson_aalen_converges
    {Func EventIndex : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_15NelsonAalenEstimatorSource
      Func EventIndex P LimitLaw) :
    TendstoInDistribution S.nelsonAalenEstimator atTop
      S.nelsonAalenLimit P LimitLaw :=
  S.nelsonAalen_converges

theorem kaplan_meier_survival_estimator_eq
    {Func EventIndex : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_15NelsonAalenEstimatorSource
      Func EventIndex P LimitLaw) :
    S.kaplanMeierSurvivalEstimator =
      vaart1998_example20_15KaplanMeierSurvivalEstimator
        S.lemma20_14Source.productIntegralSurvival
        S.nelsonAalenEstimator :=
  S.kaplanMeierSurvivalEstimator_eq

theorem kaplan_meier_finite_product_eq
    {Func EventIndex : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_15NelsonAalenEstimatorSource
      Func EventIndex P LimitLaw) :
    S.kaplanMeierFiniteProductStatistic =
      vaart1998_example20_15KaplanMeierFiniteProduct
        S.oneStepSurvivalFactor S.eventExponent :=
  S.kaplanMeierFiniteProduct_eq

theorem kaplan_meier_converges
    {Func EventIndex : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_15NelsonAalenEstimatorSource
      Func EventIndex P LimitLaw) :
    TendstoInDistribution S.kaplanMeierSurvivalEstimator atTop
      S.kaplanMeierSurvivalLimit P LimitLaw :=
  S.kaplanMeier_converges

theorem fixed_time_asymptotic_normality
    {Func EventIndex : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_15NelsonAalenEstimatorSource
      Func EventIndex P LimitLaw) :
    S.fixedTimeAsymptoticNormality_statement :=
  S.fixedTimeAsymptoticNormality

theorem process_asymptotic_normality
    {Func EventIndex : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [MeasurableSpace Func] [OpensMeasurableSpace Func] [Fintype EventIndex]
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example20_15NelsonAalenEstimatorSource
      Func EventIndex P LimitLaw) :
    S.processAsymptoticNormality_statement :=
  S.processAsymptoticNormality

end Vaart1998Example20_15NelsonAalenEstimatorSource

end AsymptoticStatistics
end StatInference
