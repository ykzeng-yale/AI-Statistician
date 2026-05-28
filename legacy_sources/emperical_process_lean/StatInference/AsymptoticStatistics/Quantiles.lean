import Mathlib.Probability.CDF
import StatInference.AsymptoticStatistics.FunctionalDeltaMethod

/-!
# van der Vaart 1998 Chapter 21 quantiles and order statistics

This module opens the Chapter 21 lane of A. W. van der Vaart,
*Asymptotic Statistics* (1998).  The first layers record the generalized
inverse display, the source clauses of Lemma 21.1, the weak-consistency
equivalence of Lemma 21.2, and the single-quantile Hadamard differentiability
source of Lemma 21.3.

The pointwise CDF convergence mode is the real-line distribution-function
form of Chapter 18 weak convergence.  The package keeps the quantile
transformation and probability-integral transformation proof routes explicit
so later empirical-quantile and order-statistic packets can reuse them without
reopening the generalized-inverse layer.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped Topology BigOperators

universe u

/-- Chapter 21 generalized inverse `F^{-1}(p) = inf {x : F x >= p}`. -/
def vaart1998_quantileFunction (F : ℝ -> ℝ) (p : ℝ) : ℝ :=
  sInf {x : ℝ | p ≤ F x}

/-- The left-limit notation `F_-` used in Lemma 21.1. -/
def vaart1998_cdfLeftLimit (F : ℝ -> ℝ) (x : ℝ) : ℝ :=
  Function.leftLim F x

/-- Composition of two distribution functions, used in Lemma 21.1(vi). -/
def vaart1998_cdfComposition (F G : ℝ -> ℝ) : ℝ -> ℝ :=
  fun x => F (G x)

/-- Quantile transformation `U ↦ F^{-1}(U)`. -/
def vaart1998_quantileTransformation (quantile : ℝ -> ℝ) : ℝ -> ℝ :=
  quantile

/-- Probability integral transformation `X ↦ F(X)`. -/
def vaart1998_probabilityIntegralTransformation (F : ℝ -> ℝ) : ℝ -> ℝ :=
  F

/-- Weak convergence of quantile functions:
pointwise convergence at the continuity points of the limiting quantile. -/
def vaart1998_quantileWeakConvergence
    {Index : Type u} (quantiles : Index -> ℝ -> ℝ) (l : Filter Index)
    (limitQuantile : ℝ -> ℝ) : Prop :=
  ∀ p ∈ Set.Ioo (0 : ℝ) 1, ContinuousAt limitQuantile p ->
    Tendsto (fun n => quantiles n p) l (𝓝 (limitQuantile p))

/-- Weak convergence of real distribution functions:
pointwise convergence at the continuity points of the limiting CDF. -/
def vaart1998_distributionFunctionWeakConvergence
    {Index : Type u} (cdfs : Index -> ℝ -> ℝ) (l : Filter Index)
    (limitCdf : ℝ -> ℝ) : Prop :=
  ∀ x : ℝ, ContinuousAt limitCdf x ->
    Tendsto (fun n => cdfs n x) l (𝓝 (limitCdf x))

theorem vaart1998_quantileFunction_def (F : ℝ -> ℝ) (p : ℝ) :
    vaart1998_quantileFunction F p = sInf {x : ℝ | p ≤ F x} :=
  rfl

theorem vaart1998_cdfLeftLimit_def (F : ℝ -> ℝ) (x : ℝ) :
    vaart1998_cdfLeftLimit F x = Function.leftLim F x :=
  rfl

theorem vaart1998_cdfComposition_apply (F G : ℝ -> ℝ) (x : ℝ) :
    vaart1998_cdfComposition F G x = F (G x) :=
  rfl

/--
Lemma 21.1 source package.  It records the generalized-inverse display and
the six textbook properties:

* `F^{-1}(p) <= x` iff `p <= F(x)`;
* `F(F^{-1}(p)) >= p`, with the range/equality and discontinuity clauses;
* `F_-(F^{-1}(p)) <= p`;
* `F^{-1}(F(x)) <= x`, with the flat-interval failure clause;
* the two idempotence identities;
* `(F ∘ G)^{-1} = G^{-1} ∘ F^{-1}`.
-/
structure Vaart1998Lemma21_1QuantileFunctionSource where
  cdf : ℝ -> ℝ
  quantile : ℝ -> ℝ
  support : Set ℝ
  flatFailureSet : Set ℝ
  compositionOuterCdf : ℝ -> ℝ
  compositionInnerCdf : ℝ -> ℝ
  compositionQuantile : ℝ -> ℝ
  compositionOuterQuantile : ℝ -> ℝ
  compositionInnerQuantile : ℝ -> ℝ
  cdfMonotone : Monotone cdf
  quantile_def : quantile = vaart1998_quantileFunction cdf
  quantileLeftContinuous_statement : Prop
  quantileLeftContinuous : quantileLeftContinuous_statement
  range_eq_support_statement : Prop
  range_eq_support : range_eq_support_statement
  le_iff :
    ∀ {p x : ℝ}, p ∈ Set.Ioo (0 : ℝ) 1 ->
      (quantile p ≤ x ↔ p ≤ cdf x)
  cdf_comp_quantile_ge :
    ∀ {p : ℝ}, p ∈ Set.Ioo (0 : ℝ) 1 -> p ≤ cdf (quantile p)
  cdf_comp_quantile_eq_iff_mem_range :
    ∀ {p : ℝ}, p ∈ Set.Ioo (0 : ℝ) 1 ->
      (cdf (quantile p) = p ↔ p ∈ Set.range cdf)
  cdf_comp_quantile_equality_failure_only_discontinuity :
    ∀ {p : ℝ}, p ∈ Set.Ioo (0 : ℝ) 1 ->
      cdf (quantile p) ≠ p ->
        ¬ ContinuousAt cdf (quantile p)
  leftLimit_comp_quantile_le :
    ∀ {p : ℝ}, p ∈ Set.Ioo (0 : ℝ) 1 ->
      vaart1998_cdfLeftLimit cdf (quantile p) ≤ p
  quantile_comp_cdf_le :
    ∀ x : ℝ, quantile (cdf x) ≤ x
  quantile_comp_cdf_equality_failure_iff_flat :
    ∀ x : ℝ, (quantile (cdf x) ≠ x ↔ x ∈ flatFailureSet)
  quantile_cdf_quantile_id :
    ∀ {p : ℝ}, p ∈ Set.Ioo (0 : ℝ) 1 ->
      quantile (cdf (quantile p)) = quantile p
  cdf_quantile_cdf_id :
    ∀ x : ℝ, cdf (quantile (cdf x)) = cdf x
  compositionQuantile_eq :
    compositionQuantile =
      fun p => compositionInnerQuantile (compositionOuterQuantile p)
  compositionCdf_eq :
    vaart1998_cdfComposition compositionOuterCdf compositionInnerCdf =
      fun x => compositionOuterCdf (compositionInnerCdf x)

namespace Vaart1998Lemma21_1QuantileFunctionSource

theorem quantile_eq_generalized_inverse
    (S : Vaart1998Lemma21_1QuantileFunctionSource) :
    S.quantile = vaart1998_quantileFunction S.cdf :=
  S.quantile_def

theorem quantile_left_continuous
    (S : Vaart1998Lemma21_1QuantileFunctionSource) :
    S.quantileLeftContinuous_statement :=
  S.quantileLeftContinuous

theorem range_eq_support_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource) :
    S.range_eq_support_statement :=
  S.range_eq_support

theorem le_iff_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource)
    {p x : ℝ} (hp : p ∈ Set.Ioo (0 : ℝ) 1) :
    S.quantile p ≤ x ↔ p ≤ S.cdf x :=
  S.le_iff (p := p) (x := x) hp

theorem cdf_comp_quantile_ge_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource)
    {p : ℝ} (hp : p ∈ Set.Ioo (0 : ℝ) 1) :
    p ≤ S.cdf (S.quantile p) :=
  S.cdf_comp_quantile_ge (p := p) hp

theorem cdf_comp_quantile_eq_iff_mem_range_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource)
    {p : ℝ} (hp : p ∈ Set.Ioo (0 : ℝ) 1) :
    S.cdf (S.quantile p) = p ↔ p ∈ Set.range S.cdf :=
  S.cdf_comp_quantile_eq_iff_mem_range (p := p) hp

theorem cdf_comp_quantile_failure_only_discontinuity
    (S : Vaart1998Lemma21_1QuantileFunctionSource)
    {p : ℝ} (hp : p ∈ Set.Ioo (0 : ℝ) 1)
    (hfail : S.cdf (S.quantile p) ≠ p) :
    ¬ ContinuousAt S.cdf (S.quantile p) :=
  S.cdf_comp_quantile_equality_failure_only_discontinuity (p := p) hp hfail

theorem leftLimit_comp_quantile_le_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource)
    {p : ℝ} (hp : p ∈ Set.Ioo (0 : ℝ) 1) :
    vaart1998_cdfLeftLimit S.cdf (S.quantile p) ≤ p :=
  S.leftLimit_comp_quantile_le (p := p) hp

theorem quantile_comp_cdf_le_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource) (x : ℝ) :
    S.quantile (S.cdf x) ≤ x :=
  S.quantile_comp_cdf_le x

theorem quantile_comp_cdf_equality_failure_iff_flat_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource) (x : ℝ) :
    S.quantile (S.cdf x) ≠ x ↔ x ∈ S.flatFailureSet :=
  S.quantile_comp_cdf_equality_failure_iff_flat x

theorem quantile_cdf_quantile_id_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource)
    {p : ℝ} (hp : p ∈ Set.Ioo (0 : ℝ) 1) :
    S.quantile (S.cdf (S.quantile p)) = S.quantile p :=
  S.quantile_cdf_quantile_id (p := p) hp

theorem cdf_quantile_cdf_id_source
    (S : Vaart1998Lemma21_1QuantileFunctionSource) (x : ℝ) :
    S.cdf (S.quantile (S.cdf x)) = S.cdf x :=
  S.cdf_quantile_cdf_id x

theorem composition_quantile_eq
    (S : Vaart1998Lemma21_1QuantileFunctionSource) :
    S.compositionQuantile =
      fun p => S.compositionInnerQuantile (S.compositionOuterQuantile p) :=
  S.compositionQuantile_eq

end Vaart1998Lemma21_1QuantileFunctionSource

/--
Lemma 21.2 source package.  It records the equivalence between weak
convergence of quantile functions and weak convergence of the corresponding
distribution functions.  The package also keeps the law-level Chapter 18 weak
convergence bridge, the quantile transformation, and the probability integral
transformation route explicit.
-/
structure Vaart1998Lemma21_2QuantileWeakConsistencySource
    {Index : Type u} (laws : Index -> ProbabilityMeasure ℝ)
    (indexFilter : Filter Index) (limitLaw : ProbabilityMeasure ℝ) where
  cdfs : Index -> ℝ -> ℝ
  limitCdf : ℝ -> ℝ
  quantiles : Index -> ℝ -> ℝ
  limitQuantile : ℝ -> ℝ
  cdf_eq_mathlib :
    ∀ n x, cdfs n x = ProbabilityTheory.cdf (laws n : Measure ℝ) x
  limitCdf_eq_mathlib :
    ∀ x, limitCdf x = ProbabilityTheory.cdf (limitLaw : Measure ℝ) x
  quantile_eq :
    ∀ n, quantiles n = vaart1998_quantileFunction (cdfs n)
  limitQuantile_eq :
    limitQuantile = vaart1998_quantileFunction limitCdf
  quantileWeakConvergence_iff_distributionFunctionWeakConvergence :
    (vaart1998_quantileWeakConvergence quantiles indexFilter limitQuantile ↔
      vaart1998_distributionFunctionWeakConvergence cdfs indexFilter limitCdf)
  lawWeakConvergence :
    vaart1998_metricWeakConvergenceProbabilityMeasures
      laws indexFilter limitLaw
  lawWeakConvergence_iff_distributionFunctionWeakConvergence_statement : Prop
  lawWeakConvergence_iff_distributionFunctionWeakConvergence :
    lawWeakConvergence_iff_distributionFunctionWeakConvergence_statement
  quantileTransformationLaw_statement : Prop
  quantileTransformationLaw : quantileTransformationLaw_statement
  probabilityIntegralTransformation_statement : Prop
  probabilityIntegralTransformation : probabilityIntegralTransformation_statement
  almostSureQuantileRoute_statement : Prop
  almostSureQuantileRoute : almostSureQuantileRoute_statement
  normalReferenceRoute_statement : Prop
  normalReferenceRoute : normalReferenceRoute_statement

namespace Vaart1998Lemma21_2QuantileWeakConsistencySource

theorem cdf_eq_mathlib_source
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) (n : Index) (x : ℝ) :
    S.cdfs n x = ProbabilityTheory.cdf (laws n : Measure ℝ) x :=
  S.cdf_eq_mathlib n x

theorem limitCdf_eq_mathlib_source
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) (x : ℝ) :
    S.limitCdf x = ProbabilityTheory.cdf (limitLaw : Measure ℝ) x :=
  S.limitCdf_eq_mathlib x

theorem quantile_eq_source
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) (n : Index) :
    S.quantiles n = vaart1998_quantileFunction (S.cdfs n) :=
  S.quantile_eq n

theorem limitQuantile_eq_source
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) :
    S.limitQuantile = vaart1998_quantileFunction S.limitCdf :=
  S.limitQuantile_eq

theorem quantile_weakConvergence_iff_distributionFunction_weakConvergence
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) :
    vaart1998_quantileWeakConvergence S.quantiles indexFilter S.limitQuantile ↔
      vaart1998_distributionFunctionWeakConvergence
        S.cdfs indexFilter S.limitCdf :=
  S.quantileWeakConvergence_iff_distributionFunctionWeakConvergence

theorem law_weakConvergence
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) :
    vaart1998_metricWeakConvergenceProbabilityMeasures
      laws indexFilter limitLaw :=
  S.lawWeakConvergence

theorem law_weakConvergence_route
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) :
    S.lawWeakConvergence_iff_distributionFunctionWeakConvergence_statement :=
  S.lawWeakConvergence_iff_distributionFunctionWeakConvergence

theorem quantile_transformation_law
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) :
    S.quantileTransformationLaw_statement :=
  S.quantileTransformationLaw

theorem probability_integral_transformation
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) :
    S.probabilityIntegralTransformation_statement :=
  S.probabilityIntegralTransformation

theorem almost_sure_quantile_route
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) :
    S.almostSureQuantileRoute_statement :=
  S.almostSureQuantileRoute

theorem normal_reference_route
    {Index : Type u} {laws : Index -> ProbabilityMeasure ℝ}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure ℝ}
    (S : Vaart1998Lemma21_2QuantileWeakConsistencySource
      laws indexFilter limitLaw) :
    S.normalReferenceRoute_statement :=
  S.normalReferenceRoute

end Vaart1998Lemma21_2QuantileWeakConsistencySource

/-- Solution set for the single-quantile functional in Lemma 21.3:
`F(x-) <= p <= F(x)` with `x` restricted to `[a,b]`. -/
def vaart1998_singleQuantileSolutionSet
    (F : ℝ -> ℝ) (p a b : ℝ) : Set ℝ :=
  {x | x ∈ Set.Icc a b ∧ vaart1998_cdfLeftLimit F x ≤ p ∧ p ≤ F x}

/-- Natural domain of the single-quantile selection map in Lemma 21.3. -/
def vaart1998_singleQuantileDomain (p a b : ℝ) : Set (ℝ -> ℝ) :=
  {F | (vaart1998_singleQuantileSolutionSet F p a b).Nonempty}

theorem vaart1998_singleQuantileSolutionSet_mem_iff
    (F : ℝ -> ℝ) (p a b x : ℝ) :
    x ∈ vaart1998_singleQuantileSolutionSet F p a b ↔
      x ∈ Set.Icc a b ∧ vaart1998_cdfLeftLimit F x ≤ p ∧ p ≤ F x :=
  Iff.rfl

theorem vaart1998_singleQuantileDomain_mem_iff
    (F : ℝ -> ℝ) (p a b : ℝ) :
    F ∈ vaart1998_singleQuantileDomain p a b ↔
      (vaart1998_singleQuantileSolutionSet F p a b).Nonempty :=
  Iff.rfl

/-- Perturbation path `F + t h_t` in the pointwise CDF notation of Lemma 21.3. -/
def vaart1998_singleQuantilePerturbation
    (F h : ℝ -> ℝ) (t : ℝ) : ℝ -> ℝ :=
  fun x => F x + t * h x

theorem vaart1998_singleQuantilePerturbation_apply
    (F h : ℝ -> ℝ) (t x : ℝ) :
    vaart1998_singleQuantilePerturbation F h t x = F x + t * h x :=
  rfl

/-- The proof's scaled quantile displacement `(xi_pt - xi_p) / t`. -/
def vaart1998_singleQuantileScaledDisplacement
    (xiPerturbed xi t : ℝ) : ℝ :=
  t⁻¹ * (xiPerturbed - xi)

/-- Lemma 21.3 derivative value `-h(xi_p) / F'(xi_p)`. -/
def vaart1998_singleQuantileDerivativeValue
    (hAtXi FderivAtXi : ℝ) : ℝ :=
  -hAtXi / FderivAtXi

/-- Lemma 21.3 derivative as a continuous linear map, supplied an evaluation
functional `h ↦ h(xi_p)` on the chosen normed function space. -/
def vaart1998_singleQuantileDerivativeMap
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (evalAtXi : Func →L[ℝ] ℝ) (FderivAtXi : ℝ) :
    Func →L[ℝ] ℝ :=
  (-(FderivAtXi)⁻¹) • evalAtXi

theorem vaart1998_singleQuantileDerivativeMap_apply
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (evalAtXi : Func →L[ℝ] ℝ) (FderivAtXi : ℝ) (h : Func) :
    vaart1998_singleQuantileDerivativeMap evalAtXi FderivAtXi h =
      vaart1998_singleQuantileDerivativeValue (evalAtXi h) FderivAtXi := by
  rw [vaart1998_singleQuantileDerivativeMap,
    vaart1998_singleQuantileDerivativeValue]
  simp [div_eq_mul_inv, mul_comm]

/--
Lemma 21.3 source package.  It records the single-quantile selection map
`phi(F)`, the textbook hypotheses `F(xi_p)=p` and `F'(xi_p)>0`, the tangent
condition that directions are continuous at `xi_p`, and the proof route:
perturbed solution inequalities, `epsilon_t=o(t)`, localization
`xi_pt -> xi_p`, convergence of `h_t(xi_pt-epsilon_t)`, the Taylor sandwich,
and the final scaled-displacement limit.  The compiled conclusion is the
Chapter 20 Hadamard differentiability predicate with derivative
`h ↦ -h(xi_p)/F'(xi_p)`.
-/
structure Vaart1998Lemma21_3SingleQuantileHadamardSource
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func] where
  domain : Set Func
  tangentSet : Set Func
  cdfOf : Func -> ℝ -> ℝ
  phi : Func -> ℝ
  baseF : Func
  a : ℝ
  b : ℝ
  p : ℝ
  xi : ℝ
  FderivAtXi : ℝ
  evalAtXi : Func →L[ℝ] ℝ
  interval_nonempty : a < b
  xi_mem_interval : xi ∈ Set.Ioo a b
  base_mem_domain : baseF ∈ domain
  base_cdf_monotone : Monotone (cdfOf baseF)
  base_solution :
    xi ∈ vaart1998_singleQuantileSolutionSet (cdfOf baseF) p a b
  phi_base_eq : phi baseF = xi
  cdf_at_xi : cdfOf baseF xi = p
  cdf_hasDerivAt_xi : HasDerivAt (cdfOf baseF) FderivAtXi xi
  cdf_derivative_pos : 0 < FderivAtXi
  tangent_continuity_at_xi :
    ∀ h ∈ tangentSet, ContinuousAt (cdfOf h) xi
  evalAtXi_eq : ∀ h, evalAtXi h = cdfOf h xi
  perturbed_solution_inequalities_statement : Prop
  perturbed_solution_inequalities :
    perturbed_solution_inequalities_statement
  epsilon_o_rate_statement : Prop
  epsilon_o_rate : epsilon_o_rate_statement
  uniform_bounded_directions_statement : Prop
  uniform_bounded_directions : uniform_bounded_directions_statement
  localization_xi_tendsto_statement : Prop
  localization_xi_tendsto : localization_xi_tendsto_statement
  direction_evaluation_tendsto_statement : Prop
  direction_evaluation_tendsto : direction_evaluation_tendsto_statement
  taylor_sandwich_statement : Prop
  taylor_sandwich : taylor_sandwich_statement
  scaled_quantile_increment_tendsto_statement : Prop
  scaled_quantile_increment_tendsto :
    scaled_quantile_increment_tendsto_statement
  hadamardDifferentiable :
    vaart1998_HadamardDifferentiableAtTangentially
      phi domain tangentSet baseF
      (vaart1998_singleQuantileDerivativeMap evalAtXi FderivAtXi)

namespace Vaart1998Lemma21_3SingleQuantileHadamardSource

/-- The derivative map displayed in Lemma 21.3. -/
def derivative
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    Func →L[ℝ] ℝ :=
  vaart1998_singleQuantileDerivativeMap S.evalAtXi S.FderivAtXi

theorem derivative_apply
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _)
    (h : Func) :
    S.derivative h =
      vaart1998_singleQuantileDerivativeValue
        (S.evalAtXi h) S.FderivAtXi :=
  vaart1998_singleQuantileDerivativeMap_apply S.evalAtXi S.FderivAtXi h

theorem derivative_display
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _)
    (h : Func) :
    S.derivative h = -S.cdfOf h S.xi / S.FderivAtXi := by
  rw [derivative_apply, S.evalAtXi_eq h,
    vaart1998_singleQuantileDerivativeValue]

theorem base_solution_source
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    S.xi ∈
      vaart1998_singleQuantileSolutionSet (S.cdfOf S.baseF) S.p S.a S.b :=
  S.base_solution

theorem base_cdf_at_quantile
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    S.cdfOf S.baseF S.xi = S.p :=
  S.cdf_at_xi

theorem base_derivative_at_quantile
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    HasDerivAt (S.cdfOf S.baseF) S.FderivAtXi S.xi :=
  S.cdf_hasDerivAt_xi

theorem base_derivative_positive
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    0 < S.FderivAtXi :=
  S.cdf_derivative_pos

theorem tangent_continuous_at_quantile
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _)
    {h : Func} (hh : h ∈ S.tangentSet) :
    ContinuousAt (S.cdfOf h) S.xi :=
  S.tangent_continuity_at_xi h hh

theorem perturbed_solution_inequalities_source
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    S.perturbed_solution_inequalities_statement :=
  S.perturbed_solution_inequalities

theorem localization_xi_tendsto_source
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    S.localization_xi_tendsto_statement :=
  S.localization_xi_tendsto

theorem direction_evaluation_tendsto_source
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    S.direction_evaluation_tendsto_statement :=
  S.direction_evaluation_tendsto

theorem taylor_sandwich_source
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    S.taylor_sandwich_statement :=
  S.taylor_sandwich

theorem scaled_quantile_increment_tendsto_source
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    S.scaled_quantile_increment_tendsto_statement :=
  S.scaled_quantile_increment_tendsto

/-- Lemma 21.3: the single-quantile map is Hadamard differentiable with
derivative `h ↦ -h(xi_p)/F'(xi_p)`. -/
theorem hadamard_differentiable
    {Func : Type*} [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    (S : @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.phi S.domain S.tangentSet S.baseF S.derivative := by
  simpa [derivative] using S.hadamardDifferentiable

end Vaart1998Lemma21_3SingleQuantileHadamardSource

/-- Closed quantile-index interval `[p1,p2]` used in Lemma 21.4(i). -/
def vaart1998_quantileFunctionClosedIndexSet (p1 p2 : ℝ) : Set ℝ :=
  Set.Icc p1 p2

/-- Open quantile-index interval `(0,1)` used in Lemma 21.4(ii). -/
def vaart1998_quantileFunctionOpenIndexSet : Set ℝ :=
  Set.Ioo (0 : ℝ) 1

/-- Distribution-function restriction interval `[a,b]` in the Lemma 21.4 domains. -/
def vaart1998_distributionRestrictionInterval (a b : ℝ) : Set ℝ :=
  Set.Icc a b

theorem vaart1998_quantileFunctionClosedIndexSet_mem_iff
    (p1 p2 p : ℝ) :
    p ∈ vaart1998_quantileFunctionClosedIndexSet p1 p2 ↔
      p1 ≤ p ∧ p ≤ p2 :=
  Iff.rfl

theorem vaart1998_quantileFunctionOpenIndexSet_mem_iff
    (p : ℝ) :
    p ∈ vaart1998_quantileFunctionOpenIndexSet ↔
      0 < p ∧ p < 1 :=
  Iff.rfl

theorem vaart1998_distributionRestrictionInterval_mem_iff
    (a b x : ℝ) :
    x ∈ vaart1998_distributionRestrictionInterval a b ↔
      a ≤ x ∧ x ≤ b :=
  Iff.rfl

/-- Lemma 21.4 derivative value at index `p`: `-h(F^{-1}(p))/f(F^{-1}(p))`. -/
def vaart1998_quantileProcessDerivativeValue
    (hAtQuantile densityAtQuantile : ℝ) : ℝ :=
  -hAtQuantile / densityAtQuantile

theorem vaart1998_quantileProcessDerivativeValue_eq
    (hAtQuantile densityAtQuantile : ℝ) :
    vaart1998_quantileProcessDerivativeValue hAtQuantile densityAtQuantile =
      vaart1998_singleQuantileDerivativeValue hAtQuantile densityAtQuantile :=
  rfl

/-- Pointwise display of the Lemma 21.4 derivative process
`h ↦ -(h / f) ∘ F^{-1}`. -/
def vaart1998_quantileProcessDerivativeDisplay
    (h density quantile : ℝ -> ℝ) : ℝ -> ℝ :=
  fun p =>
    vaart1998_quantileProcessDerivativeValue
      (h (quantile p)) (density (quantile p))

theorem vaart1998_quantileProcessDerivativeDisplay_apply
    (h density quantile : ℝ -> ℝ) (p : ℝ) :
    vaart1998_quantileProcessDerivativeDisplay h density quantile p =
      -h (quantile p) / density (quantile p) :=
  rfl

/--
Lemma 21.4 source package.  It records both uniform quantile-function
Hadamard differentiability statements: on a compact subinterval
`[p1,p2] ⊂ (0,1)` for restrictions of distribution functions to `[a,b]`,
and on `(0,1)` when the base distribution has compact support `[a,b]`.

The proof-route fields mirror van der Vaart's text: make Lemma 21.3 uniform in
`p`, use positivity of the density to get strict increase and an ordinary
inverse on a larger quantile neighborhood, localize all perturbed quantiles
there, and in the compact-support case use the positive
`ε_pt = t^2 ∧ (ξ_pt-a)` perturbation plus a uniform Taylor sandwich to obtain
`|ξ_pt-ξ_p| = O(t)` uniformly.
-/
structure Vaart1998Lemma21_4UniformQuantileHadamardSource
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess] where
  domainD1 : Set Func
  domainD2 : Set Func
  tangentSet : Set Func
  cdfOf : Func -> ℝ -> ℝ
  inverseMapD1 : Func -> QuantileProcess
  inverseMapD2 : Func -> QuantileProcess
  processEval : QuantileProcess -> ℝ -> ℝ
  baseF : Func
  a : ℝ
  b : ℝ
  p1 : ℝ
  p2 : ℝ
  epsilon : ℝ
  density : ℝ -> ℝ
  baseQuantile : ℝ -> ℝ
  derivativeD1 : Func →L[ℝ] QuantileProcess
  derivativeD2 : Func →L[ℝ] QuantileProcess
  p1_pos : 0 < p1
  p1_lt_p2 : p1 < p2
  p2_lt_one : p2 < 1
  epsilon_pos : 0 < epsilon
  base_mem_domainD1 : baseF ∈ domainD1
  base_mem_domainD2 : baseF ∈ domainD2
  interval_eq_quantile_neighborhood_statement : Prop
  interval_eq_quantile_neighborhood :
    interval_eq_quantile_neighborhood_statement
  compact_support_statement : Prop
  compact_support : compact_support_statement
  cdf_contDiffOn_interval_statement : Prop
  cdf_contDiffOn_interval : cdf_contDiffOn_interval_statement
  cdf_derivative_density_statement : Prop
  cdf_derivative_density : cdf_derivative_density_statement
  density_positive_on_interval :
    ∀ x ∈ vaart1998_distributionRestrictionInterval a b, 0 < density x
  tangent_continuity_on_interval_statement : Prop
  tangent_continuity_on_interval : tangent_continuity_on_interval_statement
  derivativeD1_eval :
    ∀ h p, p ∈ vaart1998_quantileFunctionClosedIndexSet p1 p2 ->
      processEval (derivativeD1 h) p =
        vaart1998_quantileProcessDerivativeValue
          (cdfOf h (baseQuantile p)) (density (baseQuantile p))
  derivativeD2_eval :
    ∀ h p, p ∈ vaart1998_quantileFunctionOpenIndexSet ->
      processEval (derivativeD2 h) p =
        vaart1998_quantileProcessDerivativeValue
          (cdfOf h (baseQuantile p)) (density (baseQuantile p))
  strictIncreasing_neighborhood_statement : Prop
  strictIncreasing_neighborhood : strictIncreasing_neighborhood_statement
  ordinaryInverse_on_neighborhood_statement : Prop
  ordinaryInverse_on_neighborhood : ordinaryInverse_on_neighborhood_statement
  uniformContinuity_quantile_statement : Prop
  uniformContinuity_quantile : uniformContinuity_quantile_statement
  endpointLocalization_statement : Prop
  endpointLocalization : endpointLocalization_statement
  compactSupport_quantiles_in_support_statement : Prop
  compactSupport_quantiles_in_support :
    compactSupport_quantiles_in_support_statement
  compactSupport_epsilon_positive_statement : Prop
  compactSupport_epsilon_positive : compactSupport_epsilon_positive_statement
  compactSupport_perturbed_solution_inequalities_statement : Prop
  compactSupport_perturbed_solution_inequalities :
    compactSupport_perturbed_solution_inequalities_statement
  compactSupport_uniform_smooth_expansion_statement : Prop
  compactSupport_uniform_smooth_expansion :
    compactSupport_uniform_smooth_expansion_statement
  compactSupport_uniform_sandwich_statement : Prop
  compactSupport_uniform_sandwich : compactSupport_uniform_sandwich_statement
  compactSupport_uniform_bigO_statement : Prop
  compactSupport_uniform_bigO : compactSupport_uniform_bigO_statement
  uniformDifferentiability_finish_statement : Prop
  uniformDifferentiability_finish : uniformDifferentiability_finish_statement
  hadamardDifferentiableD1 :
    vaart1998_HadamardDifferentiableAtTangentially
      inverseMapD1 domainD1 tangentSet baseF derivativeD1
  hadamardDifferentiableD2 :
    vaart1998_HadamardDifferentiableAtTangentially
      inverseMapD2 domainD2 tangentSet baseF derivativeD2

namespace Vaart1998Lemma21_4UniformQuantileHadamardSource

theorem closed_index_bounds
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _)
    {p : ℝ} (hp : p ∈ vaart1998_quantileFunctionClosedIndexSet S.p1 S.p2) :
    S.p1 ≤ p ∧ p ≤ S.p2 :=
  (vaart1998_quantileFunctionClosedIndexSet_mem_iff S.p1 S.p2 p).1 hp

theorem open_index_bounds
    {p : ℝ} (hp : p ∈ vaart1998_quantileFunctionOpenIndexSet) :
    0 < p ∧ p < 1 :=
  (vaart1998_quantileFunctionOpenIndexSet_mem_iff p).1 hp

theorem density_positive
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _)
    {x : ℝ} (hx : x ∈ vaart1998_distributionRestrictionInterval S.a S.b) :
    0 < S.density x :=
  S.density_positive_on_interval x hx

theorem derivativeD1_display
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _)
    (h : Func) {p : ℝ}
    (hp : p ∈ vaart1998_quantileFunctionClosedIndexSet S.p1 S.p2) :
    S.processEval (S.derivativeD1 h) p =
      -S.cdfOf h (S.baseQuantile p) / S.density (S.baseQuantile p) := by
  rw [S.derivativeD1_eval h p hp,
    vaart1998_quantileProcessDerivativeValue]

theorem derivativeD2_display
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _)
    (h : Func) {p : ℝ}
    (hp : p ∈ vaart1998_quantileFunctionOpenIndexSet) :
    S.processEval (S.derivativeD2 h) p =
      -S.cdfOf h (S.baseQuantile p) / S.density (S.baseQuantile p) := by
  rw [S.derivativeD2_eval h p hp,
    vaart1998_quantileProcessDerivativeValue]

theorem strictIncreasing_neighborhood_source
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    S.strictIncreasing_neighborhood_statement :=
  S.strictIncreasing_neighborhood

theorem ordinaryInverse_on_neighborhood_source
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    S.ordinaryInverse_on_neighborhood_statement :=
  S.ordinaryInverse_on_neighborhood

theorem endpointLocalization_source
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    S.endpointLocalization_statement :=
  S.endpointLocalization

theorem compactSupport_epsilon_positive_source
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    S.compactSupport_epsilon_positive_statement :=
  S.compactSupport_epsilon_positive

theorem compactSupport_perturbed_solution_inequalities_source
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    S.compactSupport_perturbed_solution_inequalities_statement :=
  S.compactSupport_perturbed_solution_inequalities

theorem compactSupport_uniform_sandwich_source
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    S.compactSupport_uniform_sandwich_statement :=
  S.compactSupport_uniform_sandwich

theorem compactSupport_uniform_bigO_source
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    S.compactSupport_uniform_bigO_statement :=
  S.compactSupport_uniform_bigO

theorem uniformDifferentiability_finish_source
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    S.uniformDifferentiability_finish_statement :=
  S.uniformDifferentiability_finish

/-- Lemma 21.4(i): uniform Hadamard differentiability of the inverse map on
`ell_infty[p1,p2]`, with derivative `h ↦ -(h/f) ∘ F^{-1}`. -/
theorem hadamard_differentiable_interval
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.inverseMapD1 S.domainD1 S.tangentSet S.baseF S.derivativeD1 :=
  S.hadamardDifferentiableD1

/-- Lemma 21.4(ii): compact-support uniform Hadamard differentiability of the
inverse map on `ell_infty(0,1)`, with derivative `h ↦ -(h/f) ∘ F^{-1}`. -/
theorem hadamard_differentiable_compact_support
    {Func QuantileProcess : Type*}
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    (S :
      @Vaart1998Lemma21_4UniformQuantileHadamardSource
        Func QuantileProcess _ _ _ _) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.inverseMapD2 S.domainD2 S.tangentSet S.baseF S.derivativeD2 :=
  S.hadamardDifferentiableD2

end Vaart1998Lemma21_4UniformQuantileHadamardSource

/-- Indicator of the empirical half-line event `{X_k <= x}` used in Corollary
21.5. -/
def vaart1998_empiricalQuantileIndicator
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ) (k : ℕ) (ω : Ω)
    (x : ℝ) : ℝ :=
  if observations k ω ≤ x then 1 else 0

/-- The coordinate empirical process at a point `x`, in the sum form
`n^{-1/2} sum_k (1{X_k <= x} - F x)`. -/
def vaart1998_empiricalProcessAtQuantile
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ) (cdf : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) (x : ℝ) : ℝ :=
  (√(n : ℝ))⁻¹ *
    ∑ k ∈ Finset.range n,
      (vaart1998_empiricalQuantileIndicator observations k ω x - cdf x)

/-- The scaled empirical-quantile error
`sqrt(n) (F_n^{-1}(p)-F^{-1}(p))`. -/
def vaart1998_empiricalQuantileScaledError
    {Ω : Type*} (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (baseQuantile : ℝ -> ℝ) (p : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  √(n : ℝ) * (empiricalQuantile n ω p - baseQuantile p)

/-- The displayed first-order summand in Corollary 21.5. -/
def vaart1998_empiricalQuantileInfluenceSummand
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ)
    (p xi densityAtXi : ℝ) (k : ℕ) (ω : Ω) : ℝ :=
  (vaart1998_empiricalQuantileIndicator observations k ω xi - p) /
    densityAtXi

/-- Corollary 21.5's linearized empirical-quantile term
`- n^{-1/2} sum_k ((1{X_k <= xi_p}-p) / f(xi_p))`. -/
def vaart1998_empiricalQuantileLinearTerm
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ)
    (p xi densityAtXi : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  - (√(n : ℝ))⁻¹ *
    ∑ k ∈ Finset.range n,
      vaart1998_empiricalQuantileInfluenceSummand
        observations p xi densityAtXi k ω

/-- Corollary 21.5's asymptotic variance `p(1-p)/f(xi_p)^2`. -/
def vaart1998_empiricalQuantileAsymptoticVariance
    (p densityAtXi : ℝ) : ℝ :=
  p * (1 - p) / densityAtXi ^ 2

/-- Brownian-bridge derivative display obtained by applying the quantile
derivative `h ↦ -h(F^{-1}(p))/f(F^{-1}(p))` to the empirical-process limit. -/
def vaart1998_empiricalQuantileBrownianBridgeDerivativeLimit
    (brownianBridge density baseQuantile : ℝ -> ℝ) : ℝ -> ℝ :=
  fun p => -brownianBridge p / density (baseQuantile p)

theorem vaart1998_empiricalQuantileLinearTerm_eq_derivative_at_quantile
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ) (cdf : ℝ -> ℝ)
    (p xi densityAtXi : ℝ) (n : ℕ) (ω : Ω)
    (hcdf : cdf xi = p) :
    vaart1998_empiricalQuantileLinearTerm
        observations p xi densityAtXi n ω =
      -vaart1998_empiricalProcessAtQuantile observations cdf n ω xi /
        densityAtXi := by
  rw [vaart1998_empiricalQuantileLinearTerm,
    vaart1998_empiricalProcessAtQuantile, hcdf]
  simp only [vaart1998_empiricalQuantileInfluenceSummand, div_eq_mul_inv]
  rw [← Finset.sum_mul]
  ring

theorem vaart1998_empiricalQuantileAsymptoticVariance_eq
    (p densityAtXi : ℝ) :
    vaart1998_empiricalQuantileAsymptoticVariance p densityAtXi =
      p * (1 - p) / densityAtXi ^ 2 :=
  rfl

/--
Corollary 21.5 source package.  It records the empirical-quantile expansion,
the scalar asymptotic-normality conclusion, and the quantile-process
convergence conclusion.  The proof route mirrors the textbook: Theorem 19.3
gives empirical-CDF Donsker convergence to an `F`-Brownian bridge; Lemma 21.3
and Theorem 20.8 give the point-quantile delta-method linearization; the
ordinary CLT identifies the displayed variance; Lemma 21.4 gives the process
version on `[p1,p2]` or `(0,1)`.
-/
structure Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess] where
  observations : ℕ -> Ω -> ℝ
  empiricalCdf : ℕ -> Ω -> Func
  empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ
  baseF : Func
  baseCdf : ℝ -> ℝ
  baseQuantile : ℝ -> ℝ
  density : ℝ -> ℝ
  p : ℝ
  xi : ℝ
  densityAtXi : ℝ
  singleScaledError : ℕ -> Ω -> ℝ
  singleLinearTerm : ℕ -> Ω -> ℝ
  gaussianLimit : Ω' -> ℝ
  quantileProcessD1 : ℕ -> Ω -> QuantileProcess
  quantileProcessD2 : ℕ -> Ω -> QuantileProcess
  processLimitD1 : Ω' -> QuantileProcess
  processLimitD2 : Ω' -> QuantileProcess
  theorem19_3 : Vaart1998Theorem19_3EmpiricalCDFDonskerSource
  lemma21_3 :
    @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _
  lemma21_4 :
    @Vaart1998Lemma21_4UniformQuantileHadamardSource
      Func QuantileProcess _ _ _ _
  p_mem_open : p ∈ vaart1998_quantileFunctionOpenIndexSet
  xi_eq_baseQuantile : xi = baseQuantile p
  baseF_eq_lemma21_3 : baseF = lemma21_3.baseF
  baseF_eq_lemma21_4 : baseF = lemma21_4.baseF
  lemma21_3_p_eq : lemma21_3.p = p
  lemma21_3_xi_eq : lemma21_3.xi = xi
  lemma21_3_derivative_eq : lemma21_3.FderivAtXi = densityAtXi
  base_cdf_at_quantile : baseCdf xi = p
  base_derivative_at_quantile : HasDerivAt baseCdf densityAtXi xi
  densityAtXi_eq : densityAtXi = density xi
  densityAtXi_pos : 0 < densityAtXi
  scaledError_eq :
    ∀ n ω, singleScaledError n ω =
      vaart1998_empiricalQuantileScaledError
        empiricalQuantile baseQuantile p n ω
  linearTerm_eq :
    ∀ n ω, singleLinearTerm n ω =
      vaart1998_empiricalQuantileLinearTerm
        observations p xi densityAtXi n ω
  asymptoticVariance : ℝ
  asymptoticVariance_eq :
    asymptoticVariance =
      vaart1998_empiricalQuantileAsymptoticVariance p densityAtXi
  theorem19_3_process_convergence :
    theorem19_3.weakConvergence_statement
  brownianBridge_continuity_at_quantile_statement : Prop
  brownianBridge_continuity_at_quantile :
    brownianBridge_continuity_at_quantile_statement
  functional_delta_method_single_statement : Prop
  functional_delta_method_single : functional_delta_method_single_statement
  single_asymptotic_equivalence_statement : Prop
  single_asymptotic_equivalence : single_asymptotic_equivalence_statement
  single_expansion_statement : Prop
  single_expansion : single_expansion_statement
  single_clt_source_statement : Prop
  single_clt_source : single_clt_source_statement
  single_asymptotic_normal :
    TendstoInDistribution singleScaledError atTop gaussianLimit
      (fun _ : ℕ => P) Q
  process_delta_method_interval_statement : Prop
  process_delta_method_interval : process_delta_method_interval_statement
  process_delta_method_compactSupport_statement : Prop
  process_delta_method_compactSupport :
    process_delta_method_compactSupport_statement
  process_converges_interval :
    TendstoInDistribution quantileProcessD1 atTop processLimitD1
      (fun _ : ℕ => P) Q
  process_converges_compactSupport :
    TendstoInDistribution quantileProcessD2 atTop processLimitD2
      (fun _ : ℕ => P) Q

namespace Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource

theorem theorem19_3_weak_convergence
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.theorem19_3.weakConvergence_statement :=
  S.theorem19_3_process_convergence

theorem lemma21_3_hadamard
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.lemma21_3.phi S.lemma21_3.domain S.lemma21_3.tangentSet
      S.lemma21_3.baseF S.lemma21_3.derivative :=
  Vaart1998Lemma21_3SingleQuantileHadamardSource.hadamard_differentiable
    S.lemma21_3

theorem lemma21_4_hadamard_interval
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.lemma21_4.inverseMapD1 S.lemma21_4.domainD1
      S.lemma21_4.tangentSet S.lemma21_4.baseF S.lemma21_4.derivativeD1 :=
  Vaart1998Lemma21_4UniformQuantileHadamardSource.hadamard_differentiable_interval
    S.lemma21_4

theorem lemma21_4_hadamard_compact_support
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.lemma21_4.inverseMapD2 S.lemma21_4.domainD2
      S.lemma21_4.tangentSet S.lemma21_4.baseF S.lemma21_4.derivativeD2 :=
  Vaart1998Lemma21_4UniformQuantileHadamardSource.hadamard_differentiable_compact_support
    S.lemma21_4

theorem scaled_error_display
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _)
    (n : ℕ) (ω : Ω) :
    S.singleScaledError n ω =
      √(n : ℝ) * (S.empiricalQuantile n ω S.p - S.baseQuantile S.p) :=
  S.scaledError_eq n ω

theorem linear_term_display
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _)
    (n : ℕ) (ω : Ω) :
    S.singleLinearTerm n ω =
      - (√(n : ℝ))⁻¹ *
        ∑ k ∈ Finset.range n,
          (vaart1998_empiricalQuantileIndicator
              S.observations k ω S.xi - S.p) / S.densityAtXi :=
  S.linearTerm_eq n ω

theorem linear_term_derivative_display
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _)
    (n : ℕ) (ω : Ω) :
    S.singleLinearTerm n ω =
      -vaart1998_empiricalProcessAtQuantile
          S.observations S.baseCdf n ω S.xi / S.densityAtXi := by
  rw [S.linearTerm_eq n ω]
  exact
    vaart1998_empiricalQuantileLinearTerm_eq_derivative_at_quantile
      S.observations S.baseCdf S.p S.xi S.densityAtXi n ω
      S.base_cdf_at_quantile

theorem variance_display
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.asymptoticVariance =
      S.p * (1 - S.p) / S.densityAtXi ^ 2 := by
  rw [S.asymptoticVariance_eq,
    vaart1998_empiricalQuantileAsymptoticVariance]

theorem single_expansion_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.single_expansion_statement :=
  S.single_expansion

theorem single_asymptotic_normality
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution S.singleScaledError atTop S.gaussianLimit
      (fun _ : ℕ => P) Q :=
  S.single_asymptotic_normal

theorem process_convergence_interval
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution S.quantileProcessD1 atTop S.processLimitD1
      (fun _ : ℕ => P) Q :=
  S.process_converges_interval

theorem process_convergence_compact_support
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution S.quantileProcessD2 atTop S.processLimitD2
      (fun _ : ℕ => P) Q :=
  S.process_converges_compactSupport

end Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource

/-- A density is bounded away from zero on a set if it admits a strictly
positive lower bound there.  This is the compact-interval condition used in
Example 21.6 for the normal and Cauchy laws. -/
def vaart1998_densityBoundedAwayFromZeroOn
    (density : ℝ -> ℝ) (s : Set ℝ) : Prop :=
  ∃ ε : ℝ, 0 < ε ∧ ∀ x ∈ s, ε ≤ density x

/-- Quantile-index version of being bounded away from zero on
`F^{-1}([p1,p2])`. -/
def vaart1998_densityBoundedAwayFromZeroOnQuantileInterval
    (density quantile : ℝ -> ℝ) (p1 p2 : ℝ) : Prop :=
  vaart1998_densityBoundedAwayFromZeroOn density
    (quantile '' vaart1998_quantileFunctionClosedIndexSet p1 p2)

theorem vaart1998_densityBoundedAwayFromZeroOn_of_eq_const
    (density : ℝ -> ℝ) (s : Set ℝ) {c : ℝ} (hc : 0 < c)
    (hdensity : ∀ x ∈ s, density x = c) :
    vaart1998_densityBoundedAwayFromZeroOn density s := by
  refine ⟨c, hc, ?_⟩
  intro x hx
  rw [hdensity x hx]

theorem vaart1998_densityBoundedAwayFromZeroOn_of_eq_one
    (density : ℝ -> ℝ) (s : Set ℝ)
    (hdensity : ∀ x ∈ s, density x = 1) :
    vaart1998_densityBoundedAwayFromZeroOn density s :=
  vaart1998_densityBoundedAwayFromZeroOn_of_eq_const density s zero_lt_one
    hdensity

/-- Standard uniform distribution function on `[0,1]`. -/
def vaart1998_standardUniformCdf (x : ℝ) : ℝ :=
  min 1 (max 0 x)

/-- Standard uniform quantile function. -/
def vaart1998_standardUniformQuantile (p : ℝ) : ℝ :=
  p

/-- Standard uniform density, equal to one on its support. -/
def vaart1998_standardUniformDensity (_x : ℝ) : ℝ :=
  1

theorem vaart1998_standardUniformDensity_eq_one (x : ℝ) :
    vaart1998_standardUniformDensity x = 1 :=
  rfl

theorem vaart1998_standardUniformDensity_boundedAwayFromZeroOn
    (s : Set ℝ) :
    vaart1998_densityBoundedAwayFromZeroOn
      vaart1998_standardUniformDensity s :=
  vaart1998_densityBoundedAwayFromZeroOn_of_eq_one
    vaart1998_standardUniformDensity s
    (by intro x hx; rfl)

/-- Standard normal density used in Example 21.6. -/
def vaart1998_standardNormalDensity (x : ℝ) : ℝ :=
  Real.exp (-(x ^ 2) / 2) / Real.sqrt (2 * Real.pi)

theorem vaart1998_standardNormalDensity_pos (x : ℝ) :
    0 < vaart1998_standardNormalDensity x := by
  unfold vaart1998_standardNormalDensity
  positivity

/-- Standard Cauchy density used in Example 21.6. -/
def vaart1998_standardCauchyDensity (x : ℝ) : ℝ :=
  (Real.pi * (1 + x ^ 2))⁻¹

theorem vaart1998_standardCauchyDensity_pos (x : ℝ) :
    0 < vaart1998_standardCauchyDensity x := by
  unfold vaart1998_standardCauchyDensity
  positivity

/-- The signed Brownian-bridge display obtained by applying the quantile
derivative to the uniform law, where `f = 1` and `F^{-1}(p)=p`.  The usual
Example 21.6 statement identifies this signed bridge with a standard Brownian
bridge at the law level. -/
def vaart1998_example21_6UniformDerivativeBridgeLimit
    (brownianBridge : ℝ -> ℝ) : ℝ -> ℝ :=
  fun p => -brownianBridge p

theorem vaart1998_example21_6UniformDerivativeBridgeLimit_eq
    (brownianBridge : ℝ -> ℝ) :
    vaart1998_empiricalQuantileBrownianBridgeDerivativeLimit
        brownianBridge vaart1998_standardUniformDensity
        vaart1998_standardUniformQuantile =
      vaart1998_example21_6UniformDerivativeBridgeLimit brownianBridge := by
  funext p
  simp [vaart1998_empiricalQuantileBrownianBridgeDerivativeLimit,
    vaart1998_standardUniformDensity,
    vaart1998_example21_6UniformDerivativeBridgeLimit]

/-- Smooth-law quantile-process limit display from Corollary 21.5:
`p ↦ -B(p)/f(F^{-1}(p))`. -/
def vaart1998_example21_6SmoothQuantileProcessLimit
    (brownianBridge density quantile : ℝ -> ℝ) : ℝ -> ℝ :=
  vaart1998_empiricalQuantileBrownianBridgeDerivativeLimit
    brownianBridge density quantile

theorem vaart1998_example21_6SmoothQuantileProcessLimit_apply
    (brownianBridge density quantile : ℝ -> ℝ) (p : ℝ) :
    vaart1998_example21_6SmoothQuantileProcessLimit
        brownianBridge density quantile p =
      -brownianBridge p / density (quantile p) :=
  rfl

/--
Example 21.6 source package.  It specializes Corollary 21.5 to the three
textbook examples:

* the uniform distribution, whose density is one on compact support, so the
  empirical quantile process converges in `ell∞(0,1)` to a standard Brownian
  bridge up to the symmetric sign supplied by the quantile derivative;
* the normal and Cauchy distributions, whose continuous positive densities are
  bounded away from zero on each compact quantile interval `[p1,p2]`, giving
  convergence in `ell∞[p1,p2]` for every `0 < p1 < p2 < 1`.
-/
structure Vaart1998Example21_6QuantileProcessExamplesSource
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess] where
  p1 : ℝ
  p2 : ℝ
  p1_pos : 0 < p1
  p1_lt_p2 : p1 < p2
  p2_lt_one : p2 < 1
  uniformCorollary :
    @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  normalCorollary :
    @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  cauchyCorollary :
    @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  uniform_cdf_eq :
    uniformCorollary.baseCdf = vaart1998_standardUniformCdf
  uniform_quantile_eq :
    uniformCorollary.baseQuantile = vaart1998_standardUniformQuantile
  uniform_density_eq :
    uniformCorollary.density = vaart1998_standardUniformDensity
  uniform_derivative_one_on_compact_support_statement : Prop
  uniform_derivative_one_on_compact_support :
    uniform_derivative_one_on_compact_support_statement
  uniform_signedBridge_is_standard_statement : Prop
  uniform_signedBridge_is_standard :
    uniform_signedBridge_is_standard_statement
  normal_density_eq :
    normalCorollary.density = vaart1998_standardNormalDensity
  normal_p1_eq : normalCorollary.lemma21_4.p1 = p1
  normal_p2_eq : normalCorollary.lemma21_4.p2 = p2
  normal_density_continuous_on_compact_interval_statement : Prop
  normal_density_continuous_on_compact_interval :
    normal_density_continuous_on_compact_interval_statement
  normal_density_boundedAway_on_quantile_interval :
    vaart1998_densityBoundedAwayFromZeroOnQuantileInterval
      normalCorollary.density normalCorollary.baseQuantile p1 p2
  cauchy_density_eq :
    cauchyCorollary.density = vaart1998_standardCauchyDensity
  cauchy_p1_eq : cauchyCorollary.lemma21_4.p1 = p1
  cauchy_p2_eq : cauchyCorollary.lemma21_4.p2 = p2
  cauchy_density_continuous_on_compact_interval_statement : Prop
  cauchy_density_continuous_on_compact_interval :
    cauchy_density_continuous_on_compact_interval_statement
  cauchy_density_boundedAway_on_quantile_interval :
    vaart1998_densityBoundedAwayFromZeroOnQuantileInterval
      cauchyCorollary.density cauchyCorollary.baseQuantile p1 p2

namespace Vaart1998Example21_6QuantileProcessExamplesSource

theorem uniform_density_boundedAway_on
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_6QuantileProcessExamplesSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _)
    (s : Set ℝ) :
    vaart1998_densityBoundedAwayFromZeroOn
      S.uniformCorollary.density s := by
  rw [S.uniform_density_eq]
  exact vaart1998_standardUniformDensity_boundedAwayFromZeroOn s

theorem uniform_derivative_one_on_compact_support_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_6QuantileProcessExamplesSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.uniform_derivative_one_on_compact_support_statement :=
  S.uniform_derivative_one_on_compact_support

theorem uniform_signedBridge_is_standard_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_6QuantileProcessExamplesSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.uniform_signedBridge_is_standard_statement :=
  S.uniform_signedBridge_is_standard

theorem uniform_process_convergence
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_6QuantileProcessExamplesSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution
      S.uniformCorollary.quantileProcessD2 atTop
      S.uniformCorollary.processLimitD2 (fun _ : ℕ => P) Q :=
  S.uniformCorollary.process_converges_compactSupport

theorem normal_density_boundedAway_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_6QuantileProcessExamplesSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    vaart1998_densityBoundedAwayFromZeroOnQuantileInterval
      S.normalCorollary.density S.normalCorollary.baseQuantile S.p1 S.p2 :=
  S.normal_density_boundedAway_on_quantile_interval

theorem normal_process_convergence
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_6QuantileProcessExamplesSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution
      S.normalCorollary.quantileProcessD1 atTop
      S.normalCorollary.processLimitD1 (fun _ : ℕ => P) Q :=
  S.normalCorollary.process_converges_interval

theorem cauchy_density_boundedAway_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_6QuantileProcessExamplesSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    vaart1998_densityBoundedAwayFromZeroOnQuantileInterval
      S.cauchyCorollary.density S.cauchyCorollary.baseQuantile S.p1 S.p2 :=
  S.cauchy_density_boundedAway_on_quantile_interval

theorem cauchy_process_convergence
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_6QuantileProcessExamplesSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution
      S.cauchyCorollary.quantileProcessD1 atTop
      S.cauchyCorollary.processLimitD1 (fun _ : ℕ => P) Q :=
  S.cauchyCorollary.process_converges_interval

end Vaart1998Example21_6QuantileProcessExamplesSource

/-- Real-valued index ratio `k_n / n` used in Lemma 21.7. -/
def vaart1998_orderStatisticIndexRatio (kSeq : ℕ -> ℕ) (n : ℕ) : ℝ :=
  (kSeq n : ℝ) / (n : ℝ)

/-- The deterministic remainder in the assumption
`k_n/n = p + c/sqrt(n) + o(1/sqrt(n))`. -/
def vaart1998_orderStatisticIndexExpansionRemainder
    (kSeq : ℕ -> ℕ) (p c : ℝ) (n : ℕ) : ℝ :=
  vaart1998_orderStatisticIndexRatio kSeq n - p - c / √(n : ℝ)

/-- Lemma 21.7's index-rate assumption, written as
`sqrt(n) * (k_n/n - p - c/sqrt(n)) -> 0`. -/
def vaart1998_orderStatisticIndexLocalExpansion
    (kSeq : ℕ -> ℕ) (p c : ℝ) : Prop :=
  Tendsto
    (fun n : ℕ =>
      √(n : ℝ) *
        vaart1998_orderStatisticIndexExpansionRemainder kSeq p c n)
    atTop (𝓝 0)

theorem vaart1998_orderStatisticIndexLocalExpansion_scaled_ratio_eventually_eq
    (kSeq : ℕ -> ℕ) (p c : ℝ) :
    (fun n : ℕ =>
      √(n : ℝ) * (vaart1998_orderStatisticIndexRatio kSeq n - p)) =ᶠ[atTop]
      fun n : ℕ =>
        c + √(n : ℝ) *
          vaart1998_orderStatisticIndexExpansionRemainder kSeq p c n := by
  filter_upwards [eventually_atTop.2 ⟨1, fun n hn => hn⟩] with n hn
  have hn_pos : 0 < n := by omega
  have hsqrt_ne : √(n : ℝ) ≠ 0 := by
    exact ne_of_gt (Real.sqrt_pos.2 (by exact_mod_cast hn_pos))
  unfold vaart1998_orderStatisticIndexExpansionRemainder
  field_simp [hsqrt_ne]
  ring

theorem vaart1998_orderStatisticIndexLocalExpansion_scaled_ratio_tendsto
    (kSeq : ℕ -> ℕ) (p c : ℝ)
    (h : vaart1998_orderStatisticIndexLocalExpansion kSeq p c) :
    Tendsto
      (fun n : ℕ =>
        √(n : ℝ) * (vaart1998_orderStatisticIndexRatio kSeq n - p))
      atTop (𝓝 c) := by
  have hsum :
      Tendsto
        (fun n : ℕ =>
          c + √(n : ℝ) *
            vaart1998_orderStatisticIndexExpansionRemainder kSeq p c n)
        atTop (𝓝 (c + 0)) :=
    tendsto_const_nhds.add h
  have hsum' :
      Tendsto
        (fun n : ℕ =>
          c + √(n : ℝ) *
            vaart1998_orderStatisticIndexExpansionRemainder kSeq p c n)
        atTop (𝓝 c) := by
    simpa using hsum
  exact hsum'.congr'
    (vaart1998_orderStatisticIndexLocalExpansion_scaled_ratio_eventually_eq
      kSeq p c).symm

/-- The Lemma 21.7 scaled gap
`sqrt(n) * (X_{n(k_n)} - F_n^{-1}(p))`. -/
def vaart1998_orderStatisticEmpiricalQuantileGap
    {Ω : Type*} (orderStatistic : ℕ -> Ω -> ℝ)
    (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (p : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  √(n : ℝ) * (orderStatistic n ω - empiricalQuantile n ω p)

/-- Density-scaled version of the Lemma 21.7 gap, used before dividing by
`f(F^{-1}(p))`. -/
def vaart1998_orderStatisticDensityScaledGap
    {Ω : Type*} (orderStatistic : ℕ -> Ω -> ℝ)
    (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (p densityAtXi : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  densityAtXi *
    vaart1998_orderStatisticEmpiricalQuantileGap
      orderStatistic empiricalQuantile p n ω

/-- The proof map `g_n(z) = z(k_n/n)-z(p)` from Lemma 21.7's uniform case. -/
def vaart1998_orderStatisticUniformProofMap
    {QuantileProcess : Type*}
    (processEval : QuantileProcess -> ℝ -> ℝ)
    (kSeq : ℕ -> ℕ) (p : ℝ) (n : ℕ)
    (z : QuantileProcess) : ℝ :=
  processEval z (vaart1998_orderStatisticIndexRatio kSeq n) -
    processEval z p

theorem vaart1998_orderStatisticEmpiricalQuantileGap_apply
    {Ω : Type*} (orderStatistic : ℕ -> Ω -> ℝ)
    (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (p : ℝ) (n : ℕ) (ω : Ω) :
    vaart1998_orderStatisticEmpiricalQuantileGap
        orderStatistic empiricalQuantile p n ω =
      √(n : ℝ) * (orderStatistic n ω - empiricalQuantile n ω p) :=
  rfl

theorem vaart1998_orderStatisticDensityScaledGap_apply
    {Ω : Type*} (orderStatistic : ℕ -> Ω -> ℝ)
    (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (p densityAtXi : ℝ) (n : ℕ) (ω : Ω) :
    vaart1998_orderStatisticDensityScaledGap
        orderStatistic empiricalQuantile p densityAtXi n ω =
      densityAtXi *
        √(n : ℝ) * (orderStatistic n ω - empiricalQuantile n ω p) := by
  simp [vaart1998_orderStatisticDensityScaledGap,
    vaart1998_orderStatisticEmpiricalQuantileGap, mul_assoc]

/--
Lemma 21.7 source package.  It records the order-statistic/empirical-quantile
comparison under the deterministic index condition
`k_n/n = p + c/sqrt(n) + o(1/sqrt(n))`.

The proof route mirrors the textbook: first use Example 21.6's uniform
quantile-process convergence and the extended continuous-mapping theorem on
`g_n(z)=z(k_n/n)-z(p)` to show that the uniform order statistic and the
uniform empirical quantile differ by the index drift; then use the quantile
transformation and a two-term delta-method argument to pass from uniforms to a
general distribution with positive derivative at `F^{-1}(p)`.
-/
structure Vaart1998Lemma21_7OrderStatisticQuantileGapSource
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess] where
  observations : ℕ -> Ω -> ℝ
  uniformObservations : ℕ -> Ω -> ℝ
  kSeq : ℕ -> ℕ
  p : ℝ
  c : ℝ
  xi : ℝ
  densityAtXi : ℝ
  orderStatistic : ℕ -> Ω -> ℝ
  uniformOrderStatistic : ℕ -> Ω -> ℝ
  empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ
  uniformEmpiricalQuantile : ℕ -> Ω -> ℝ -> ℝ
  baseCdf : ℝ -> ℝ
  baseQuantile : ℝ -> ℝ
  density : ℝ -> ℝ
  corollary21_5 :
    @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  example21_6 :
    @Vaart1998Example21_6QuantileProcessExamplesSource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  p_mem_open : p ∈ vaart1998_quantileFunctionOpenIndexSet
  xi_eq_baseQuantile : xi = baseQuantile p
  base_cdf_at_quantile : baseCdf xi = p
  base_derivative_at_quantile : HasDerivAt baseCdf densityAtXi xi
  densityAtXi_eq : densityAtXi = density xi
  densityAtXi_pos : 0 < densityAtXi
  empiricalQuantile_eq :
    empiricalQuantile = corollary21_5.empiricalQuantile
  baseQuantile_eq :
    baseQuantile = corollary21_5.baseQuantile
  density_eq :
    density = corollary21_5.density
  corollary_p_eq : corollary21_5.p = p
  corollary_xi_eq : corollary21_5.xi = xi
  corollary_densityAtXi_eq : corollary21_5.densityAtXi = densityAtXi
  indexLocalExpansion :
    vaart1998_orderStatisticIndexLocalExpansion kSeq p c
  uniformProofMap_continuity_statement : Prop
  uniformProofMap_continuity : uniformProofMap_continuity_statement
  uniform_extended_continuous_mapping_statement : Prop
  uniform_extended_continuous_mapping :
    uniform_extended_continuous_mapping_statement
  uniform_gap_minus_index_drift_oP :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticEmpiricalQuantileGap
          uniformOrderStatistic uniformEmpiricalQuantile p n ω -
        √(n : ℝ) *
          (vaart1998_orderStatisticIndexRatio kSeq n - p))
      atTop 0
  uniform_gap_tendsto :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticEmpiricalQuantileGap
          uniformOrderStatistic uniformEmpiricalQuantile p n ω)
      atTop (fun _ : Ω => c)
  quantileTransformation_orderStatistic_statement : Prop
  quantileTransformation_orderStatistic :
    quantileTransformation_orderStatistic_statement
  twoTerm_delta_method_statement : Prop
  twoTerm_delta_method : twoTerm_delta_method_statement
  density_scaled_gap_minus_index_drift_oP :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticDensityScaledGap
          orderStatistic empiricalQuantile p densityAtXi n ω -
        √(n : ℝ) *
          (vaart1998_orderStatisticIndexRatio kSeq n - p))
      atTop 0
  gap_converges :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticEmpiricalQuantileGap
          orderStatistic empiricalQuantile p n ω)
      atTop (fun _ : Ω => c / densityAtXi)

namespace Vaart1998Lemma21_7OrderStatisticQuantileGapSource

theorem index_scaled_ratio_tendsto
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    Tendsto
      (fun n : ℕ =>
        √(n : ℝ) *
          (vaart1998_orderStatisticIndexRatio S.kSeq n - S.p))
      atTop (𝓝 S.c) :=
  vaart1998_orderStatisticIndexLocalExpansion_scaled_ratio_tendsto
    S.kSeq S.p S.c S.indexLocalExpansion

theorem uniform_process_convergence
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution
      S.example21_6.uniformCorollary.quantileProcessD2 atTop
      S.example21_6.uniformCorollary.processLimitD2
      (fun _ : ℕ => P) Q :=
  S.example21_6.uniform_process_convergence

theorem uniform_mapping_continuity_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.uniformProofMap_continuity_statement :=
  S.uniformProofMap_continuity

theorem uniform_extended_continuous_mapping_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.uniform_extended_continuous_mapping_statement :=
  S.uniform_extended_continuous_mapping

theorem uniform_gap_minus_index_drift
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticEmpiricalQuantileGap
          S.uniformOrderStatistic S.uniformEmpiricalQuantile S.p n ω -
        √(n : ℝ) *
          (vaart1998_orderStatisticIndexRatio S.kSeq n - S.p))
      atTop 0 :=
  S.uniform_gap_minus_index_drift_oP

theorem uniform_gap_converges
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticEmpiricalQuantileGap
          S.uniformOrderStatistic S.uniformEmpiricalQuantile S.p n ω)
      atTop (fun _ : Ω => S.c) :=
  S.uniform_gap_tendsto

theorem quantileTransformation_orderStatistic_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.quantileTransformation_orderStatistic_statement :=
  S.quantileTransformation_orderStatistic

theorem twoTerm_delta_method_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.twoTerm_delta_method_statement :=
  S.twoTerm_delta_method

theorem density_scaled_gap_minus_index_drift
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticDensityScaledGap
          S.orderStatistic S.empiricalQuantile S.p S.densityAtXi n ω -
        √(n : ℝ) *
          (vaart1998_orderStatisticIndexRatio S.kSeq n - S.p))
      atTop 0 :=
  S.density_scaled_gap_minus_index_drift_oP

/-- Lemma 21.7: the order statistic and empirical quantile differ by
`c / f(F^{-1}(p))` after `sqrt(n)` scaling. -/
theorem gap_converges_in_probability
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticEmpiricalQuantileGap
          S.orderStatistic S.empiricalQuantile S.p n ω)
      atTop (fun _ : Ω => S.c / S.densityAtXi) :=
  S.gap_converges

end Vaart1998Lemma21_7OrderStatisticQuantileGapSource

/-- The confidence interval event
`X_{n(k)} < F^{-1}(p) <= X_{n(l)}` from Example 21.8. -/
def vaart1998_orderStatisticConfidenceIntervalEvent
    {Ω : Type*} (lowerOrderStatistic upperOrderStatistic : ℕ -> Ω -> ℝ)
    (baseQuantile : ℝ -> ℝ) (p : ℝ) (n : ℕ) : Set Ω :=
  {ω | lowerOrderStatistic n ω < baseQuantile p ∧
    baseQuantile p ≤ upperOrderStatistic n ω}

/-- The uniform-order-statistic coverage event
`U_{n(k)} < p <= U_{n(l)}` from Example 21.8. -/
def vaart1998_uniformOrderStatisticCoverageEvent
    {Ω : Type*} (lowerUniformOrderStatistic upperUniformOrderStatistic :
      ℕ -> Ω -> ℝ)
    (p : ℝ) (n : ℕ) : Set Ω :=
  {ω | lowerUniformOrderStatistic n ω < p ∧
    p ≤ upperUniformOrderStatistic n ω}

/-- Large-sample half-width `z_alpha * sqrt(p(1-p)/n)` for the index ratios
in Example 21.8. -/
def vaart1998_quantileConfidenceHalfWidth
    (p zAlpha n : ℝ) : ℝ :=
  zAlpha * Real.sqrt (p * (1 - p) / n)

/-- Lower large-sample index-ratio choice `p - z_alpha sqrt(p(1-p)/n)`. -/
def vaart1998_quantileConfidenceLowerIndexRatio
    (p zAlpha n : ℝ) : ℝ :=
  p - vaart1998_quantileConfidenceHalfWidth p zAlpha n

/-- Upper large-sample index-ratio choice `p + z_alpha sqrt(p(1-p)/n)`. -/
def vaart1998_quantileConfidenceUpperIndexRatio
    (p zAlpha n : ℝ) : ℝ :=
  p + vaart1998_quantileConfidenceHalfWidth p zAlpha n

theorem vaart1998_quantileConfidenceUpperIndexRatio_sub_center
    (p zAlpha n : ℝ) :
    vaart1998_quantileConfidenceUpperIndexRatio p zAlpha n - p =
      vaart1998_quantileConfidenceHalfWidth p zAlpha n := by
  simp [vaart1998_quantileConfidenceUpperIndexRatio]

theorem vaart1998_center_sub_quantileConfidenceLowerIndexRatio
    (p zAlpha n : ℝ) :
    p - vaart1998_quantileConfidenceLowerIndexRatio p zAlpha n =
      vaart1998_quantileConfidenceHalfWidth p zAlpha n := by
  simp [vaart1998_quantileConfidenceLowerIndexRatio]

theorem vaart1998_quantileConfidenceIndexRatio_symmetric
    (p zAlpha n : ℝ) :
    vaart1998_quantileConfidenceUpperIndexRatio p zAlpha n - p =
      p - vaart1998_quantileConfidenceLowerIndexRatio p zAlpha n := by
  simp [vaart1998_quantileConfidenceUpperIndexRatio_sub_center,
    vaart1998_center_sub_quantileConfidenceLowerIndexRatio]

/-- The asymptotically equivalent bridge event
`sqrt(n) * |G_n^{-1}(p) - p| <= z_alpha * sqrt(p(1-p))`. -/
def vaart1998_quantileBridgeAcceptanceEvent
    {Ω : Type*} (uniformEmpiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (p zAlpha : ℝ) (n : ℕ) : Set Ω :=
  {ω | √(n : ℝ) * ‖uniformEmpiricalQuantile n ω p - p‖ ≤
    zAlpha * Real.sqrt (p * (1 - p))}

/--
Example 21.8 source package for distribution-free confidence intervals for
quantiles.  It records the probability-integral transformation, the exact
finite-sample coverage identity
`P_F(X_{n(k)} < F^{-1}(p) <= X_{n(l)})
 = P(U_{n(k)} < p <= U_{n(l)})`, the large-sample index choices
`k/n,l/n = p ± z_alpha sqrt(p(1-p)/n)`, and the handoff to Lemma 21.7 that
turns the uniform-order-statistic event into the bridge event with limiting
coverage `1 - 2 alpha`.
-/
structure Vaart1998Example21_8QuantileConfidenceIntervalSource
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess] where
  p : ℝ
  zAlpha : ℝ
  alpha : ℝ
  lowerIndex : ℕ -> ℕ
  upperIndex : ℕ -> ℕ
  observations : ℕ -> Ω -> ℝ
  uniformObservations : ℕ -> Ω -> ℝ
  lowerOrderStatistic : ℕ -> Ω -> ℝ
  upperOrderStatistic : ℕ -> Ω -> ℝ
  lowerUniformOrderStatistic : ℕ -> Ω -> ℝ
  upperUniformOrderStatistic : ℕ -> Ω -> ℝ
  empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ
  uniformEmpiricalQuantile : ℕ -> Ω -> ℝ -> ℝ
  uniformEmpiricalBridgeQuantile : ℕ -> Ω -> ℝ -> ℝ
  baseCdf : ℝ -> ℝ
  baseQuantile : ℝ -> ℝ
  density : ℝ -> ℝ
  corollary21_5 :
    @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  example21_6 :
    @Vaart1998Example21_6QuantileProcessExamplesSource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  lemma21_7_lower :
    @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  lemma21_7_upper :
    @Vaart1998Lemma21_7OrderStatisticQuantileGapSource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  p_mem_open : p ∈ vaart1998_quantileFunctionOpenIndexSet
  continuous_distribution_statement : Prop
  continuous_distribution : continuous_distribution_statement
  probabilityIntegralTransformation_statement : Prop
  probabilityIntegralTransformation : probabilityIntegralTransformation_statement
  probabilityIntegralUniformSample_statement : Prop
  probabilityIntegralUniformSample : probabilityIntegralUniformSample_statement
  order_statistics_match_preceding_lemma_statement : Prop
  order_statistics_match_preceding_lemma :
    order_statistics_match_preceding_lemma_statement
  quantile_process_sources_match_statement : Prop
  quantile_process_sources_match : quantile_process_sources_match_statement
  lowerIndexRatio_choice :
    ∀ᶠ n in atTop,
      vaart1998_orderStatisticIndexRatio lowerIndex n =
        vaart1998_quantileConfidenceLowerIndexRatio p zAlpha (n : ℝ)
  upperIndexRatio_choice :
    ∀ᶠ n in atTop,
      vaart1998_orderStatisticIndexRatio upperIndex n =
        vaart1998_quantileConfidenceUpperIndexRatio p zAlpha (n : ℝ)
  finite_sample_coverage_eq :
    ∀ n : ℕ,
      P.real
          (vaart1998_orderStatisticConfidenceIntervalEvent
            lowerOrderStatistic upperOrderStatistic baseQuantile p n) =
        P.real
          (vaart1998_uniformOrderStatisticCoverageEvent
            lowerUniformOrderStatistic upperUniformOrderStatistic p n)
  distribution_free_coverage_statement : Prop
  distribution_free_coverage : distribution_free_coverage_statement
  exact_confidence_interval_selection_statement : Prop
  exact_confidence_interval_selection :
    exact_confidence_interval_selection_statement
  precedingLemma_uniform_order_expansion_statement : Prop
  precedingLemma_uniform_order_expansion :
    precedingLemma_uniform_order_expansion_statement
  asymptotic_equivalence_event_statement : Prop
  asymptotic_equivalence_event : asymptotic_equivalence_event_statement
  coverage_probability_limit :
    Tendsto
      (fun n : ℕ =>
        P.real
          (vaart1998_orderStatisticConfidenceIntervalEvent
            lowerOrderStatistic upperOrderStatistic baseQuantile p n))
      atTop (𝓝 (1 - 2 * alpha))
  empiricalQuantile_alternative_needs_density_statement : Prop
  empiricalQuantile_alternative_needs_density :
    empiricalQuantile_alternative_needs_density_statement
  distribution_free_avoids_density_statement : Prop
  distribution_free_avoids_density :
    distribution_free_avoids_density_statement

namespace Vaart1998Example21_8QuantileConfidenceIntervalSource

theorem probability_integral_transform_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.probabilityIntegralTransformation_statement :=
  S.probabilityIntegralTransformation

theorem probability_integral_uniform_sample_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.probabilityIntegralUniformSample_statement :=
  S.probabilityIntegralUniformSample

theorem finite_sample_coverage
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    ∀ n : ℕ,
      P.real
          (vaart1998_orderStatisticConfidenceIntervalEvent
            S.lowerOrderStatistic S.upperOrderStatistic S.baseQuantile S.p n) =
        P.real
          (vaart1998_uniformOrderStatisticCoverageEvent
            S.lowerUniformOrderStatistic S.upperUniformOrderStatistic S.p n) :=
  S.finite_sample_coverage_eq

theorem distribution_free_coverage_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.distribution_free_coverage_statement :=
  S.distribution_free_coverage

theorem exact_confidence_interval_selection_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.exact_confidence_interval_selection_statement :=
  S.exact_confidence_interval_selection

theorem lower_gap_converges_from_preceding_lemma
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticEmpiricalQuantileGap
          S.lemma21_7_lower.orderStatistic S.lemma21_7_lower.empiricalQuantile
          S.lemma21_7_lower.p n ω)
      atTop (fun _ : Ω =>
        S.lemma21_7_lower.c / S.lemma21_7_lower.densityAtXi) :=
  S.lemma21_7_lower.gap_converges_in_probability

theorem upper_gap_converges_from_preceding_lemma
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInMeasure P
      (fun n ω =>
        vaart1998_orderStatisticEmpiricalQuantileGap
          S.lemma21_7_upper.orderStatistic S.lemma21_7_upper.empiricalQuantile
          S.lemma21_7_upper.p n ω)
      atTop (fun _ : Ω =>
        S.lemma21_7_upper.c / S.lemma21_7_upper.densityAtXi) :=
  S.lemma21_7_upper.gap_converges_in_probability

theorem precedingLemma_uniform_order_expansion_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.precedingLemma_uniform_order_expansion_statement :=
  S.precedingLemma_uniform_order_expansion

theorem asymptotic_equivalence_event_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.asymptotic_equivalence_event_statement :=
  S.asymptotic_equivalence_event

theorem coverage_probability_tendsto
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    Tendsto
      (fun n : ℕ =>
        P.real
          (vaart1998_orderStatisticConfidenceIntervalEvent
            S.lowerOrderStatistic S.upperOrderStatistic S.baseQuantile S.p n))
      atTop (𝓝 (1 - 2 * S.alpha)) :=
  S.coverage_probability_limit

theorem empirical_quantile_alternative_needs_density_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.empiricalQuantile_alternative_needs_density_statement :=
  S.empiricalQuantile_alternative_needs_density

theorem distribution_free_avoids_density_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Example21_8QuantileConfidenceIntervalSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.distribution_free_avoids_density_statement :=
  S.distribution_free_avoids_density

end Vaart1998Example21_8QuantileConfidenceIntervalSource

/-- The standardized empirical difference process at a fixed `p`:
`R_n(p) = f(xi_p) sqrt(n) (F_n^{-1}(p)-F^{-1}(p))
  + sqrt(n) (F_n(xi_p)-F(xi_p))`. -/
def vaart1998_standardizedEmpiricalDifferenceProcess
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ)
    (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (baseCdf baseQuantile : ℝ -> ℝ)
    (p xi densityAtXi : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  densityAtXi *
    vaart1998_empiricalQuantileScaledError
      empiricalQuantile baseQuantile p n ω +
  vaart1998_empiricalProcessAtQuantile observations baseCdf n ω xi

theorem vaart1998_standardizedEmpiricalDifferenceProcess_eq
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ)
    (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (baseCdf baseQuantile : ℝ -> ℝ)
    (p xi densityAtXi : ℝ) (n : ℕ) (ω : Ω) :
    vaart1998_standardizedEmpiricalDifferenceProcess
        observations empiricalQuantile baseCdf baseQuantile
        p xi densityAtXi n ω =
      densityAtXi * √(n : ℝ) *
          (empiricalQuantile n ω p - baseQuantile p) +
        vaart1998_empiricalProcessAtQuantile observations baseCdf n ω xi := by
  simp [vaart1998_standardizedEmpiricalDifferenceProcess,
    vaart1998_empiricalQuantileScaledError, mul_assoc]

/-- The same display as a density-scaled delta-method remainder: since the
Corollary 21.5 linear term is `-G_n(xi_p)/f(xi_p)`, the process `R_n(p)` is
`f(xi_p)` times the difference between the scaled quantile error and its
linear approximation. -/
theorem vaart1998_standardizedEmpiricalDifferenceProcess_eq_density_mul_remainder
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ)
    (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (baseCdf baseQuantile : ℝ -> ℝ)
    (p xi densityAtXi : ℝ) (n : ℕ) (ω : Ω)
    (hdensity : densityAtXi ≠ 0)
    (hcdf : baseCdf xi = p) :
    vaart1998_standardizedEmpiricalDifferenceProcess
        observations empiricalQuantile baseCdf baseQuantile
        p xi densityAtXi n ω =
      densityAtXi *
        (vaart1998_empiricalQuantileScaledError
            empiricalQuantile baseQuantile p n ω -
          vaart1998_empiricalQuantileLinearTerm
            observations p xi densityAtXi n ω) := by
  rw [vaart1998_standardizedEmpiricalDifferenceProcess,
    vaart1998_empiricalQuantileLinearTerm_eq_derivative_at_quantile
      observations baseCdf p xi densityAtXi n ω hcdf]
  field_simp [hdensity]
  ring

/-- The uniform-specialization display emphasized after Example 21.8, where
`f(xi_p)=1` and `xi_p=p`. -/
def vaart1998_uniformStandardizedEmpiricalDifferenceProcess
    {Ω : Type*} (uniformObservations : ℕ -> Ω -> ℝ)
    (uniformEmpiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (p : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  √(n : ℝ) * (uniformEmpiricalQuantile n ω p - p) +
    vaart1998_empiricalProcessAtQuantile
      uniformObservations (fun x : ℝ => x) n ω p

theorem vaart1998_standardizedEmpiricalDifferenceProcess_uniform_eq
    {Ω : Type*} (uniformObservations : ℕ -> Ω -> ℝ)
    (uniformEmpiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (p : ℝ) (n : ℕ) (ω : Ω) :
    vaart1998_standardizedEmpiricalDifferenceProcess
        uniformObservations uniformEmpiricalQuantile
        (fun x : ℝ => x) (fun x : ℝ => x) p p 1 n ω =
      vaart1998_uniformStandardizedEmpiricalDifferenceProcess
        uniformObservations uniformEmpiricalQuantile p n ω := by
  simp [vaart1998_standardizedEmpiricalDifferenceProcess,
    vaart1998_uniformStandardizedEmpiricalDifferenceProcess,
    vaart1998_empiricalQuantileScaledError]

/-- Pointwise Bahadur-Kiefer limsup scaling
`n^(1/4)/(log log n)^(3/4)`. -/
def vaart1998_bahadurKieferPointwiseScale (n : ℕ) : ℝ :=
  (n : ℝ) ^ ((1 : ℝ) / 4) /
    Real.rpow (Real.log (Real.log (n : ℝ))) ((3 : ℝ) / 4)

/-- Pointwise Bahadur-Kiefer fluctuation rate
`n^(-1/4) (log log n)^(3/4)`. -/
def vaart1998_bahadurKieferPointwiseFluctuationRate (n : ℕ) : ℝ :=
  (n : ℝ) ^ (-(1 : ℝ) / 4) *
    Real.rpow (Real.log (Real.log (n : ℝ))) ((3 : ℝ) / 4)

/-- Pointwise Bahadur-Kiefer limsup constant
`[(32/27) p(1-p)]^(1/4)`. -/
def vaart1998_bahadurKieferPointwiseLimsupConstant (p : ℝ) : ℝ :=
  Real.rpow (((32 : ℝ) / 27) * p * (1 - p)) ((1 : ℝ) / 4)

/-- The `n^(1/4) R_n(p)` distributional rescaling. -/
def vaart1998_bahadurKieferPointwiseDistributionRescaling (n : ℕ) : ℝ :=
  (n : ℝ) ^ ((1 : ℝ) / 4)

/-- Supremum norm of a quantile-indexed empirical difference process. -/
def vaart1998_empiricalDifferenceProcessSupNorm
    {Ω : Type*} (differenceProcess : ℕ -> Ω -> ℝ -> ℝ)
    (indexSet : Set ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  sSup ((fun p : ℝ => ‖differenceProcess n ω p‖) '' indexSet)

/-- Supremum-norm Bahadur-Kiefer limsup scaling
`n^(1/4)/((log n)^(1/2)(2 log log n)^(1/4))`. -/
def vaart1998_bahadurKieferSupremumScale (n : ℕ) : ℝ :=
  (n : ℝ) ^ ((1 : ℝ) / 4) /
    (Real.sqrt (Real.log (n : ℝ)) *
      Real.rpow (2 * Real.log (Real.log (n : ℝ))) ((1 : ℝ) / 4))

/-- Supremum-norm Bahadur-Kiefer distributional scaling
`n^(1/4)/(log n)^(1/2)`. -/
def vaart1998_bahadurKieferSupremumDistributionScale (n : ℕ) : ℝ :=
  (n : ℝ) ^ ((1 : ℝ) / 4) / Real.sqrt (Real.log (n : ℝ))

/-- Supremum-norm limsup constant `1/sqrt(2)`. -/
def vaart1998_bahadurKieferSupremumLimsupConstant : ℝ :=
  1 / Real.sqrt 2

/--
Source package for the standardized empirical difference process following
Example 21.8.  It records the display of `R_n(p)`, the Corollary 21.5
convergence `R_n(p) -> 0` in probability, the uniform-law symmetry, and the
Bahadur-Kiefer pointwise and supremum-norm refinements.
-/
structure Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess] where
  observations : ℕ -> Ω -> ℝ
  empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ
  baseCdf : ℝ -> ℝ
  baseQuantile : ℝ -> ℝ
  density : ℝ -> ℝ
  p : ℝ
  xi : ℝ
  densityAtXi : ℝ
  standardizedEmpiricalDifference : ℕ -> Ω -> ℝ
  standardizedEmpiricalDifferenceProcess : ℕ -> Ω -> ℝ -> ℝ
  pointwiseLimitDistribution : Ω' -> ℝ
  supremumLimitDistribution : Ω' -> ℝ
  corollary21_5 :
    @Vaart1998Corollary21_5EmpiricalQuantileAsymptoticNormalitySource
      Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _
  p_mem_open : p ∈ vaart1998_quantileFunctionOpenIndexSet
  xi_eq_baseQuantile : xi = baseQuantile p
  base_cdf_at_quantile : baseCdf xi = p
  densityAtXi_eq : densityAtXi = density xi
  densityAtXi_pos : 0 < densityAtXi
  corollary21_5_reuse_statement : Prop
  corollary21_5_reuse : corollary21_5_reuse_statement
  standardizedEmpiricalDifference_eq :
    ∀ n ω,
      standardizedEmpiricalDifference n ω =
        vaart1998_standardizedEmpiricalDifferenceProcess
          observations empiricalQuantile baseCdf baseQuantile
          p xi densityAtXi n ω
  standardizedEmpiricalDifferenceProcess_at_p :
    ∀ n ω,
      standardizedEmpiricalDifferenceProcess n ω p =
        standardizedEmpiricalDifference n ω
  standardizedEmpiricalDifference_tendsto :
    TendstoInMeasure P standardizedEmpiricalDifference atTop 0
  standardized_name_statement : Prop
  standardized_name : standardized_name_statement
  uniform_symmetry_statement : Prop
  uniform_symmetry : uniform_symmetry_statement
  twice_differentiable_at_quantile_statement : Prop
  twice_differentiable_at_quantile :
    twice_differentiable_at_quantile_statement
  pointwise_limsup_statement : Prop
  pointwise_limsup : pointwise_limsup_statement
  pointwise_distribution_limit :
    TendstoInDistribution
      (fun n ω =>
        vaart1998_bahadurKieferPointwiseDistributionRescaling n *
          standardizedEmpiricalDifference n ω)
      atTop pointwiseLimitDistribution (fun _ : ℕ => P) Q
  pointwise_magnitude_rate_statement : Prop
  pointwise_magnitude_rate : pointwise_magnitude_rate_statement
  supremum_regular_distribution_examples_statement : Prop
  supremum_regular_distribution_examples :
    supremum_regular_distribution_examples_statement
  supremum_limsup_statement : Prop
  supremum_limsup : supremum_limsup_statement
  supremum_distribution_limit :
    TendstoInDistribution
      (fun n ω =>
        vaart1998_bahadurKieferSupremumDistributionScale n *
          vaart1998_empiricalDifferenceProcessSupNorm
            standardizedEmpiricalDifferenceProcess (Set.Icc 0 1) n ω)
      atTop supremumLimitDistribution (fun _ : ℕ => P) Q
  brownian_motion_indexed_unit_interval_statement : Prop
  brownian_motion_indexed_unit_interval :
    brownian_motion_indexed_unit_interval_statement

namespace Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource

theorem display
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _)
    (n : ℕ) (ω : Ω) :
    S.standardizedEmpiricalDifference n ω =
      S.densityAtXi * √(n : ℝ) *
          (S.empiricalQuantile n ω S.p - S.baseQuantile S.p) +
        vaart1998_empiricalProcessAtQuantile
          S.observations S.baseCdf n ω S.xi := by
  rw [S.standardizedEmpiricalDifference_eq n ω]
  exact
    vaart1998_standardizedEmpiricalDifferenceProcess_eq
      S.observations S.empiricalQuantile S.baseCdf S.baseQuantile
      S.p S.xi S.densityAtXi n ω

theorem density_mul_remainder_display
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _)
    (n : ℕ) (ω : Ω) :
    S.standardizedEmpiricalDifference n ω =
      S.densityAtXi *
        (vaart1998_empiricalQuantileScaledError
            S.empiricalQuantile S.baseQuantile S.p n ω -
          vaart1998_empiricalQuantileLinearTerm
            S.observations S.p S.xi S.densityAtXi n ω) := by
  rw [S.standardizedEmpiricalDifference_eq n ω]
  exact
    vaart1998_standardizedEmpiricalDifferenceProcess_eq_density_mul_remainder
      S.observations S.empiricalQuantile S.baseCdf S.baseQuantile
      S.p S.xi S.densityAtXi n ω
      (ne_of_gt S.densityAtXi_pos) S.base_cdf_at_quantile

theorem corollary21_5_reuse_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.corollary21_5_reuse_statement :=
  S.corollary21_5_reuse

theorem tendsto_in_probability
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInMeasure P S.standardizedEmpiricalDifference atTop 0 :=
  S.standardizedEmpiricalDifference_tendsto

theorem standardized_name_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.standardized_name_statement :=
  S.standardized_name

theorem uniform_symmetry_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.uniform_symmetry_statement :=
  S.uniform_symmetry

theorem pointwise_limsup_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.pointwise_limsup_statement :=
  S.pointwise_limsup

theorem pointwise_distribution_convergence
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution
      (fun n ω =>
        vaart1998_bahadurKieferPointwiseDistributionRescaling n *
          S.standardizedEmpiricalDifference n ω)
      atTop S.pointwiseLimitDistribution (fun _ : ℕ => P) Q :=
  S.pointwise_distribution_limit

theorem pointwise_magnitude_rate_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.pointwise_magnitude_rate_statement :=
  S.pointwise_magnitude_rate

theorem supremum_limsup_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.supremum_limsup_statement :=
  S.supremum_limsup

theorem supremum_distribution_convergence
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    TendstoInDistribution
      (fun n ω =>
        vaart1998_bahadurKieferSupremumDistributionScale n *
          vaart1998_empiricalDifferenceProcessSupNorm
            S.standardizedEmpiricalDifferenceProcess (Set.Icc 0 1) n ω)
      atTop S.supremumLimitDistribution (fun _ : ℕ => P) Q :=
  S.supremum_distribution_limit

theorem brownian_motion_indexed_unit_interval_source
    {Ω Ω' Func QuantileProcess : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup QuantileProcess] [NormedSpace ℝ QuantileProcess]
    [MeasurableSpace QuantileProcess]
    [OpensMeasurableSpace QuantileProcess]
    (S :
      @Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource
        Ω Ω' Func QuantileProcess _ P _ _ Q _ _ _ _ _ _ _) :
    S.brownian_motion_indexed_unit_interval_statement :=
  S.brownian_motion_indexed_unit_interval

end Vaart1998Chapter21StandardizedEmpiricalDifferenceProcessSource

/-- The median probability level used in Section 21.3. -/
def vaart1998_medianProbability : ℝ :=
  (1 : ℝ) / 2

/-- The population median, identified with the `1/2`-quantile. -/
def vaart1998_populationMedian (F : ℝ -> ℝ) : ℝ :=
  vaart1998_quantileFunction F vaart1998_medianProbability

/-- The absolute deviation observation `|X_k - center_n|`. -/
def vaart1998_absoluteDeviationObservation
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ)
    (center : ℕ -> Ω -> ℝ) (k n : ℕ) (ω : Ω) : ℝ :=
  ‖observations k ω - center n ω‖

theorem vaart1998_absoluteDeviationObservation_apply
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ)
    (center : ℕ -> Ω -> ℝ) (k n : ℕ) (ω : Ω) :
    vaart1998_absoluteDeviationObservation observations center k n ω =
      ‖observations k ω - center n ω‖ :=
  rfl

/-- The sample median absolute deviation as the median of the absolute
deviation sample. -/
def vaart1998_medianAbsoluteDeviationStatistic
    {Ω : Type*} (deviationMedian : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  deviationMedian n ω

theorem vaart1998_medianAbsoluteDeviationStatistic_apply
    {Ω : Type*} (deviationMedian : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) :
    vaart1998_medianAbsoluteDeviationStatistic deviationMedian n ω =
      deviationMedian n ω :=
  rfl

/-- Distribution function of `|X - theta|`:
`x ↦ F(theta + x) - F_-(theta - x)`. -/
def vaart1998_absoluteDeviationCdf
    (F : ℝ -> ℝ) (theta x : ℝ) : ℝ :=
  F (theta + x) - vaart1998_cdfLeftLimit F (theta - x)

theorem vaart1998_absoluteDeviationCdf_apply
    (F : ℝ -> ℝ) (theta x : ℝ) :
    vaart1998_absoluteDeviationCdf F theta x =
      F (theta + x) - vaart1998_cdfLeftLimit F (theta - x) :=
  rfl

/-- The first map in the MAD proof, `F ↦ (F^{-1}(1/2), F)`. -/
def vaart1998_madPhi1 (F : ℝ -> ℝ) : ℝ × (ℝ -> ℝ) :=
  (vaart1998_populationMedian F, F)

/-- The second map in the MAD proof,
`(theta,F) ↦ (x ↦ F(theta+x)-F_-(theta-x))`. -/
def vaart1998_madPhi2 (thetaAndF : ℝ × (ℝ -> ℝ)) : ℝ -> ℝ :=
  fun x => vaart1998_absoluteDeviationCdf thetaAndF.2 thetaAndF.1 x

/-- The third map in the MAD proof, `G ↦ G^{-1}(1/2)`. -/
def vaart1998_madPhi3 (G : ℝ -> ℝ) : ℝ :=
  vaart1998_quantileFunction G vaart1998_medianProbability

/-- The MAD functional `phi = phi3 ∘ phi2 ∘ phi1`. -/
def vaart1998_madFunctional (F : ℝ -> ℝ) : ℝ :=
  vaart1998_madPhi3 (vaart1998_madPhi2 (vaart1998_madPhi1 F))

theorem vaart1998_madFunctional_apply (F : ℝ -> ℝ) :
    vaart1998_madFunctional F =
      vaart1998_quantileFunction
        (fun x =>
          F (vaart1998_populationMedian F + x) -
            vaart1998_cdfLeftLimit F (vaart1998_populationMedian F - x))
        vaart1998_medianProbability :=
  rfl

/-- The denominator `f(m_F+m_G)+f(m_F-m_G)` in Lemma 21.9. -/
def vaart1998_madDerivativeDenominator
    (density : ℝ -> ℝ) (mF mG : ℝ) : ℝ :=
  density (mF + mG) + density (mF - mG)

/-- The density-asymmetry factor in the first term of Lemma 21.9. -/
def vaart1998_madDerivativeSkewFactor
    (density : ℝ -> ℝ) (mF mG : ℝ) : ℝ :=
  (density (mF + mG) - density (mF - mG)) /
    vaart1998_madDerivativeDenominator density mF mG

/-- Lemma 21.9 derivative display. -/
def vaart1998_madDerivativeValue
    (H density : ℝ -> ℝ) (mF mG : ℝ) : ℝ :=
  H mF / density mF *
      vaart1998_madDerivativeSkewFactor density mF mG -
    (H (mF + mG) - H (mF - mG)) /
      vaart1998_madDerivativeDenominator density mF mG

theorem vaart1998_madDerivativeValue_apply
    (H density : ℝ -> ℝ) (mF mG : ℝ) :
    vaart1998_madDerivativeValue H density mF mG =
      H mF / density mF *
          ((density (mF + mG) - density (mF - mG)) /
            (density (mF + mG) + density (mF - mG))) -
        (H (mF + mG) - H (mF - mG)) /
          (density (mF + mG) + density (mF - mG)) :=
  rfl

/-- The derivative contribution of `phi2` before applying the final quantile
map: shift derivative plus CDF perturbation at the two endpoints. -/
def vaart1998_madPhi2DerivativeValue
    (H density : ℝ -> ℝ) (a mF x : ℝ) : ℝ :=
  a * density (mF + x) + H (mF + x) -
    (a * density (mF - x) + H (mF - x))

theorem vaart1998_madPhi2DerivativeValue_apply
    (H density : ℝ -> ℝ) (a mF x : ℝ) :
    vaart1998_madPhi2DerivativeValue H density a mF x =
      a * density (mF + x) + H (mF + x) -
        (a * density (mF - x) + H (mF - x)) :=
  rfl

/--
Lemma 21.9 source package for the median absolute deviation.  It records the
three-map proof route
`F -> (F^{-1}(1/2),F) -> (x -> F(theta+x)-F_-(theta-x)) -> G^{-1}(1/2)`,
the derivative display, the reuse of Lemma 21.3 for `phi1` and `phi3`, and
the Chapter 20.9 chain-rule handoff.
-/
structure Vaart1998Lemma21_9MedianAbsoluteDeviationSource
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc] where
  observations : ℕ -> Ω -> ℝ
  empiricalCdf : ℕ -> Ω -> Func
  baseF : Func
  cdfOf : Func -> ℝ -> ℝ
  baseCdf : ℝ -> ℝ
  density : ℝ -> ℝ
  sampleMedian : ℕ -> Ω -> ℝ
  empiricalMad : ℕ -> Ω -> ℝ
  madFunctional : Func -> ℝ
  derivative : Func →L[ℝ] ℝ
  brownianBridge : Ω' -> Func
  derivativeLimit : Ω' -> ℝ
  domain : Set Func
  tangentSet : Set Func
  mF : ℝ
  mG : ℝ
  deviationCdf : ℝ -> ℝ
  baseCdf_eq : baseCdf = cdfOf baseF
  deviationCdf_eq :
    deviationCdf = vaart1998_madPhi2 (mF, baseCdf)
  base_median_condition : baseCdf mF = vaart1998_medianProbability
  deviation_median_condition :
    vaart1998_absoluteDeviationCdf baseCdf mF mG =
      vaart1998_medianProbability
  base_derivative_at_mF : HasDerivAt baseCdf (density mF) mF
  density_pos_mF : 0 < density mF
  endpoint_plus_smooth_statement : Prop
  endpoint_plus_smooth : endpoint_plus_smooth_statement
  endpoint_minus_smooth_statement : Prop
  endpoint_minus_smooth : endpoint_minus_smooth_statement
  endpoint_positive_derivative_statement : Prop
  endpoint_positive_derivative : endpoint_positive_derivative_statement
  tangent_continuity_mF :
    ∀ h ∈ tangentSet, ContinuousAt (cdfOf h) mF
  tangent_continuity_endpoints_statement : Prop
  tangent_continuity_endpoints : tangent_continuity_endpoints_statement
  phi1_source :
    @Vaart1998Lemma21_3SingleQuantileHadamardSource Func _ _
  phi2_hadamard_statement : Prop
  phi2_hadamard : phi2_hadamard_statement
  phi3_source :
    @Vaart1998Lemma21_3SingleQuantileHadamardSource DeviationFunc _ _
  chain_rule_statement : Prop
  chain_rule : chain_rule_statement
  tangent_spaces_match_statement : Prop
  tangent_spaces_match : tangent_spaces_match_statement
  derivative_display_statement : Prop
  derivative_display : derivative_display_statement
  madHadamardDifferentiable :
    vaart1998_HadamardDifferentiableAtTangentially
      madFunctional domain tangentSet baseF derivative
  empiricalMad_eq_functional :
    ∀ n ω, empiricalMad n ω = madFunctional (empiricalCdf n ω)
  empiricalCdf_in_domain : ∀ n, ∀ᵐ ω ∂P, empiricalCdf n ω ∈ domain
  brownianBridge_in_tangentSet : ∀ᵐ ω ∂Q, brownianBridge ω ∈ tangentSet
  brownian_bridge_continuity_statement : Prop
  brownian_bridge_continuity : brownian_bridge_continuity_statement
  derivativeLimit_eq :
    ∀ ω, derivativeLimit ω = derivative (brownianBridge ω)
  asymptoticNormality :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) * (empiricalMad n ω - madFunctional baseF))
      atTop derivativeLimit (fun _ : ℕ => P) Q

namespace Vaart1998Lemma21_9MedianAbsoluteDeviationSource

theorem absolute_deviation_cdf_display
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    vaart1998_absoluteDeviationCdf S.baseCdf S.mF S.mG =
      S.baseCdf (S.mF + S.mG) -
        vaart1998_cdfLeftLimit S.baseCdf (S.mF - S.mG) :=
  rfl

theorem median_condition
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.baseCdf S.mF = vaart1998_medianProbability :=
  S.base_median_condition

theorem deviation_median_condition_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    vaart1998_absoluteDeviationCdf S.baseCdf S.mF S.mG =
      vaart1998_medianProbability :=
  S.deviation_median_condition

theorem phi1_hadamard
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.phi1_source.phi S.phi1_source.domain S.phi1_source.tangentSet
      S.phi1_source.baseF S.phi1_source.derivative :=
  Vaart1998Lemma21_3SingleQuantileHadamardSource.hadamard_differentiable
    S.phi1_source

theorem phi2_hadamard_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.phi2_hadamard_statement :=
  S.phi2_hadamard

theorem phi3_hadamard
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.phi3_source.phi S.phi3_source.domain S.phi3_source.tangentSet
      S.phi3_source.baseF S.phi3_source.derivative :=
  Vaart1998Lemma21_3SingleQuantileHadamardSource.hadamard_differentiable
    S.phi3_source

theorem chain_rule_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.chain_rule_statement :=
  S.chain_rule

theorem tangent_spaces_match_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.tangent_spaces_match_statement :=
  S.tangent_spaces_match

theorem derivative_display_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.derivative_display_statement :=
  S.derivative_display

theorem hadamard_differentiable
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.madFunctional S.domain S.tangentSet S.baseF S.derivative :=
  S.madHadamardDifferentiable

theorem empirical_mad_eq_functional
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc))
    (n : ℕ) (ω : Ω) :
    S.empiricalMad n ω = S.madFunctional (S.empiricalCdf n ω) :=
  S.empiricalMad_eq_functional n ω

theorem brownian_bridge_continuity_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.brownian_bridge_continuity_statement :=
  S.brownian_bridge_continuity

theorem derivative_limit_eq
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc))
    (ω : Ω') :
    S.derivativeLimit ω = S.derivative (S.brownianBridge ω) :=
  S.derivativeLimit_eq ω

theorem asymptotic_normality
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) * (S.empiricalMad n ω - S.madFunctional S.baseF))
      atTop S.derivativeLimit (fun _ : ℕ => P) Q :=
  S.asymptoticNormality

end Vaart1998Lemma21_9MedianAbsoluteDeviationSource

/-- The probability level `1/4` used in Examples 21.10-21.11. -/
def vaart1998_oneQuarterProbability : ℝ :=
  (1 : ℝ) / 4

/-- The probability level `3/4` used in Examples 21.10-21.11. -/
def vaart1998_threeQuarterProbability : ℝ :=
  (3 : ℝ) / 4

/-- In the symmetric case the density-asymmetry factor in Lemma 21.9 is zero. -/
theorem vaart1998_madDerivativeSkewFactor_symmetric_zero_median
    (density : ℝ -> ℝ) (mG : ℝ)
    (hsym : density mG = density (-mG)) :
    vaart1998_madDerivativeSkewFactor density 0 mG = 0 := by
  simp [vaart1998_madDerivativeSkewFactor,
    vaart1998_madDerivativeDenominator, hsym]

/-- Lemma 21.9 derivative specialized to a symmetric distribution with
`m_F = 0`. -/
theorem vaart1998_madDerivativeValue_symmetric_zero_median
    (H density : ℝ -> ℝ) (mG : ℝ)
    (hsym : density mG = density (-mG)) :
    vaart1998_madDerivativeValue H density 0 mG =
      - (H mG - H (-mG)) / (2 * density mG) := by
  simp [vaart1998_madDerivativeValue, vaart1998_madDerivativeSkewFactor,
    vaart1998_madDerivativeDenominator, hsym]
  ring

/-- Example 21.10 derivative display for a standard Brownian bridge indexed by
probabilities. -/
def vaart1998_symmetricMadDerivativeLimit
    (standardBrownianBridge : ℝ -> ℝ) (densityAtMad : ℝ) : ℝ :=
  - (standardBrownianBridge vaart1998_threeQuarterProbability -
      standardBrownianBridge vaart1998_oneQuarterProbability) /
    (2 * densityAtMad)

theorem vaart1998_symmetricMadDerivativeLimit_apply
    (standardBrownianBridge : ℝ -> ℝ) (densityAtMad : ℝ) :
    vaart1998_symmetricMadDerivativeLimit standardBrownianBridge
        densityAtMad =
      - (standardBrownianBridge vaart1998_threeQuarterProbability -
          standardBrownianBridge vaart1998_oneQuarterProbability) /
        (2 * densityAtMad) :=
  rfl

/-- Example 21.10 MAD asymptotic variance `(1/16) / f(F^{-1}(3/4))^2`. -/
def vaart1998_symmetricMadAsymptoticVariance (densityAtMad : ℝ) : ℝ :=
  ((1 : ℝ) / 16) / densityAtMad ^ 2

/-- Example 21.11 normal-distribution MAD value
`sigma * Phi^{-1}(3/4)`. -/
def vaart1998_normalMadValue
    (sigma standardNormalQuantile75 : ℝ) : ℝ :=
  sigma * standardNormalQuantile75

/-- Example 21.11 normal MAD asymptotic variance
`(sigma^2/16) / phi(Phi^{-1}(3/4))^2`. -/
def vaart1998_normalMadAsymptoticVariance
    (sigma standardNormalDensityAtQ75 : ℝ) : ℝ :=
  (sigma ^ 2 / 16) / standardNormalDensityAtQ75 ^ 2

/-- The normal standard-deviation estimator based on MAD. -/
def vaart1998_normalStandardDeviationMadEstimator
    (madValue standardNormalQuantile75 : ℝ) : ℝ :=
  madValue / standardNormalQuantile75

/-- The normal variance estimator based on the squared rescaled MAD. -/
def vaart1998_normalVarianceMadEstimator
    (madValue standardNormalQuantile75 : ℝ) : ℝ :=
  (madValue / standardNormalQuantile75) ^ 2

/-- Example 21.11 asymptotic variance of the squared MAD variance estimator. -/
def vaart1998_normalVarianceEstimatorAsymptoticVariance
    (sigma standardNormalDensityAtQ75 standardNormalQuantile75 : ℝ) : ℝ :=
  ((1 : ℝ) / 4) * sigma ^ 4 /
    (standardNormalDensityAtQ75 ^ 2 * standardNormalQuantile75 ^ 2)

/-- The displayed approximate variance constant `5.44`. -/
def vaart1998_normalVarianceEstimatorVarianceConstantApprox : ℝ :=
  (544 : ℝ) / 100

/-- The displayed approximate relative efficiency `37%`. -/
def vaart1998_normalMadVarianceEstimatorRelativeEfficiencyApprox : ℝ :=
  (37 : ℝ) / 100

/--
Source package for Examples 21.10 and 21.11.  It records the symmetric-density
specialization of Lemma 21.9, the Brownian-bridge endpoint display, the
`(1/16)/f(F^{-1}(3/4))^2` variance, and the normal-distribution MAD and
variance-estimator specializations.
-/
structure Vaart1998Examples21_10_21_11MadSource
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc] where
  lemma21_9 :
    @Vaart1998Lemma21_9MedianAbsoluteDeviationSource
      Ω Ω' Func DeviationFunc _ P _ _ Q _ _ _ _ _
  distributionQuantile : ℝ -> ℝ
  density : ℝ -> ℝ
  standardBrownianBridge : Ω' -> ℝ -> ℝ
  mF : ℝ
  mG : ℝ
  densityAtMad : ℝ
  sigma : ℝ
  standardNormalQuantile75 : ℝ
  standardNormalDensityAtQ75 : ℝ
  normalMad : ℝ
  normalMadVariance : ℝ
  normalSdEstimator : ℝ -> ℝ
  normalVarianceEstimator : ℝ -> ℝ
  normalVarianceEstimatorAsymptoticVariance : ℝ
  symmetric_density_about_zero_statement : Prop
  symmetric_density_about_zero : symmetric_density_about_zero_statement
  symmetric_density_at_mad : density mG = density (-mG)
  symmetric_median_zero : mF = 0
  symmetric_mad_eq_three_quarter_quantile :
    mG = distributionQuantile vaart1998_threeQuarterProbability
  densityAtMad_eq : densityAtMad = density mG
  first_derivative_term_vanishes :
    vaart1998_madDerivativeSkewFactor density 0 mG = 0
  brownian_bridge_endpoint_representation_statement : Prop
  brownian_bridge_endpoint_representation :
    brownian_bridge_endpoint_representation_statement
  symmetric_derivative_limit :
    ∀ ω,
      lemma21_9.derivativeLimit ω =
        vaart1998_symmetricMadDerivativeLimit
          (standardBrownianBridge ω) densityAtMad
  symmetric_mad_variance :
    normalMadVariance =
      vaart1998_symmetricMadAsymptoticVariance densityAtMad
  normal_distribution_statement : Prop
  normal_distribution : normal_distribution_statement
  normal_median_zero : mF = 0
  normal_mad_eq :
    normalMad =
      vaart1998_normalMadValue sigma standardNormalQuantile75
  normal_mad_variance_eq :
    normalMadVariance =
      vaart1998_normalMadAsymptoticVariance sigma
        standardNormalDensityAtQ75
  normal_sd_estimator_eq :
    normalSdEstimator =
      fun madValue =>
        vaart1998_normalStandardDeviationMadEstimator madValue
          standardNormalQuantile75
  normal_variance_estimator_eq :
    normalVarianceEstimator =
      fun madValue =>
        vaart1998_normalVarianceMadEstimator madValue
          standardNormalQuantile75
  normal_variance_estimator_asymptotic_variance_eq :
    normalVarianceEstimatorAsymptoticVariance =
      vaart1998_normalVarianceEstimatorAsymptoticVariance sigma
        standardNormalDensityAtQ75 standardNormalQuantile75
  variance_constant_approx_statement : Prop
  variance_constant_approx : variance_constant_approx_statement
  relative_efficiency_approx_statement : Prop
  relative_efficiency_approx : relative_efficiency_approx_statement

namespace Vaart1998Examples21_10_21_11MadSource

theorem lemma21_9_asymptotic_normality
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) *
          (S.lemma21_9.empiricalMad n ω -
            S.lemma21_9.madFunctional S.lemma21_9.baseF))
      atTop S.lemma21_9.derivativeLimit (fun _ : ℕ => P) Q :=
  S.lemma21_9.asymptoticNormality

theorem first_derivative_term_vanishes_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    vaart1998_madDerivativeSkewFactor S.density 0 S.mG = 0 :=
  S.first_derivative_term_vanishes

theorem derivative_value_reduction
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc))
    (H : ℝ -> ℝ) :
    vaart1998_madDerivativeValue H S.density 0 S.mG =
      - (H S.mG - H (-S.mG)) / (2 * S.density S.mG) :=
  vaart1998_madDerivativeValue_symmetric_zero_median H S.density S.mG
    S.symmetric_density_at_mad

theorem symmetric_derivative_limit_display
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc))
    (ω : Ω') :
    S.lemma21_9.derivativeLimit ω =
      vaart1998_symmetricMadDerivativeLimit
        (S.standardBrownianBridge ω) S.densityAtMad :=
  S.symmetric_derivative_limit ω

theorem symmetric_mad_variance_display
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.normalMadVariance =
      vaart1998_symmetricMadAsymptoticVariance S.densityAtMad :=
  S.symmetric_mad_variance

theorem normal_mad_display
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.normalMad =
      vaart1998_normalMadValue S.sigma S.standardNormalQuantile75 :=
  S.normal_mad_eq

theorem normal_mad_variance_display
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.normalMadVariance =
      vaart1998_normalMadAsymptoticVariance S.sigma
        S.standardNormalDensityAtQ75 :=
  S.normal_mad_variance_eq

theorem normal_sd_estimator_display
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.normalSdEstimator =
      fun madValue =>
        vaart1998_normalStandardDeviationMadEstimator madValue
          S.standardNormalQuantile75 :=
  S.normal_sd_estimator_eq

theorem normal_variance_estimator_display
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.normalVarianceEstimator =
      fun madValue =>
        vaart1998_normalVarianceMadEstimator madValue
          S.standardNormalQuantile75 :=
  S.normal_variance_estimator_eq

theorem normal_variance_estimator_asymptotic_variance_display
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.normalVarianceEstimatorAsymptoticVariance =
      vaart1998_normalVarianceEstimatorAsymptoticVariance S.sigma
        S.standardNormalDensityAtQ75 S.standardNormalQuantile75 :=
  S.normal_variance_estimator_asymptotic_variance_eq

theorem variance_constant_approx_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.variance_constant_approx_statement :=
  S.variance_constant_approx

theorem relative_efficiency_approx_source
    {Ω Ω' Func DeviationFunc : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup Func] [NormedSpace ℝ Func]
    [NormedAddCommGroup DeviationFunc] [NormedSpace ℝ DeviationFunc]
    (S : Vaart1998Examples21_10_21_11MadSource
      (P := P) (Q := Q) (Func := Func) (DeviationFunc := DeviationFunc)) :
    S.relative_efficiency_approx_statement :=
  S.relative_efficiency_approx

end Vaart1998Examples21_10_21_11MadSource

/-- Survival function notation `\bar F(t)=1-F(t)` from Section 21.4. -/
def vaart1998_survivalFunction (F : ℝ -> ℝ) (t : ℝ) : ℝ :=
  1 - F t

theorem vaart1998_survivalFunction_apply (F : ℝ -> ℝ) (t : ℝ) :
    vaart1998_survivalFunction F t = 1 - F t :=
  rfl

/-- Number of observations among the first `n` exceeding a threshold. -/
def vaart1998_exceedanceCount
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ)
    (threshold : ℝ) (n : ℕ) (ω : Ω) : ℕ :=
  ((Finset.range n).filter
    (fun i => threshold < observations i ω)).card

/-- Source display for the binomial tail in the general-order-statistic
reduction: `P(bin(n,p) <= m)`. -/
def vaart1998_binomialLeProbabilityDisplay
    (binomialLeProbability : ℕ -> ℝ -> ℕ -> ℝ)
    (n : ℕ) (p : ℝ) (m : ℕ) : ℝ :=
  binomialLeProbability n p m

/-- The event `{X_{n(n)} <= x_n}` for a supplied maximum statistic. -/
def vaart1998_maximumLeEvent
    {Ω : Type*} (sampleMaximum : ℕ -> Ω -> ℝ)
    (threshold : ℕ -> ℝ) (n : ℕ) : Set Ω :=
  {ω | sampleMaximum n ω ≤ threshold n}

/-- The source display `P(X_(n(k_n)) <= x_n) =
P(bin(n,p_n) <= n-k_n)`. -/
def vaart1998_orderStatisticBinomialDisplay
    (binomialLeProbability : ℕ -> ℝ -> ℕ -> ℝ)
    (n k : ℕ) (p : ℝ) : ℝ :=
  vaart1998_binomialLeProbabilityDisplay
    binomialLeProbability n p (n - k)

/-- The maximum CDF display `F(x_n)^n`. -/
def vaart1998_maximumCdfPowerDisplay
    (F : ℝ -> ℝ) (threshold : ℕ -> ℝ) (n : ℕ) : ℝ :=
  F (threshold n) ^ n

/-- The equivalent maximum CDF display
`(1 - n \bar F(x_n)/n)^n`. -/
def vaart1998_maximumCdfSurvivalDisplay
    (survival : ℝ -> ℝ) (threshold : ℕ -> ℝ) (n : ℕ) : ℝ :=
  (1 - (n : ℝ) * survival (threshold n) / (n : ℝ)) ^ n

theorem vaart1998_maximumCdfPower_eq_survivalDisplay
    (F survival : ℝ -> ℝ) (threshold : ℕ -> ℝ) (n : ℕ)
    (hn : (n : ℝ) ≠ 0)
    (hF : F (threshold n) = 1 - survival (threshold n)) :
    vaart1998_maximumCdfPowerDisplay F threshold n =
      vaart1998_maximumCdfSurvivalDisplay survival threshold n := by
  rw [vaart1998_maximumCdfPowerDisplay,
    vaart1998_maximumCdfSurvivalDisplay, hF]
  congr 1
  field_simp [hn]

/--
Source package for the opening of Section 21.4 and Lemma 21.12.  It records
the survival function notation, the order-statistic-to-binomial reduction, the
maximum CDF display `F(x_n)^n = (1 - n \bar F(x_n)/n)^n`, and the limiting
equivalence between `P(X_{n(n)} <= x_n) -> exp(-tau)` and
`n \bar F(x_n) -> tau`.
-/
structure Vaart1998Lemma21_12MaximumSource
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] where
  observations : ℕ -> Ω -> ℝ
  sampleMaximum : ℕ -> Ω -> ℝ
  cdf : ℝ -> ℝ
  survival : ℝ -> ℝ
  threshold : ℕ -> ℝ
  orderIndex : ℕ -> ℕ
  exceedanceProbability : ℕ -> ℝ
  maximumProbability : ℕ -> ℝ
  binomialLeProbability : ℕ -> ℝ -> ℕ -> ℝ
  tau : ℝ
  tau_nonnegative : 0 ≤ tau
  survival_eq : ∀ x, survival x = vaart1998_survivalFunction cdf x
  exceedanceProbability_eq :
    ∀ n, exceedanceProbability n = survival (threshold n)
  order_statistic_binomial_display_statement : Prop
  order_statistic_binomial_display :
    order_statistic_binomial_display_statement
  order_statistic_binomial_probability :
    ∀ n,
      vaart1998_orderStatisticBinomialDisplay
        binomialLeProbability n (orderIndex n) (exceedanceProbability n) =
        binomialLeProbability n (exceedanceProbability n) (n - orderIndex n)
  maximumProbability_event :
    ∀ n,
      maximumProbability n =
        P.real (vaart1998_maximumLeEvent sampleMaximum threshold n)
  maximumProbability_power :
    ∀ n,
      maximumProbability n =
        vaart1998_maximumCdfPowerDisplay cdf threshold n
  maximum_cdf_independence_source_statement : Prop
  maximum_cdf_independence_source :
    maximum_cdf_independence_source_statement
  normalizedSurvival : ℕ -> ℝ
  normalizedSurvival_eq :
    ∀ n, normalizedSurvival n = (n : ℝ) * survival (threshold n)
  normalizedSurvival_tendsto :
    Tendsto normalizedSurvival atTop (𝓝 tau)
  maximumProbability_tendsto_exp :
    Tendsto maximumProbability atTop (𝓝 (Real.exp (-tau)))
  lemma21_12_iff :
    Tendsto maximumProbability atTop (𝓝 (Real.exp (-tau))) ↔
      Tendsto normalizedSurvival atTop (𝓝 tau)
  infinite_tau_source_statement : Prop
  infinite_tau_source : infinite_tau_source_statement
  interesting_limits_statement : Prop
  interesting_limits : interesting_limits_statement

namespace Vaart1998Lemma21_12MaximumSource

theorem survival_display
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) (x : ℝ) :
    S.survival x = 1 - S.cdf x := by
  rw [S.survival_eq x, vaart1998_survivalFunction]

theorem exceedance_probability_display
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) (n : ℕ) :
    S.exceedanceProbability n = S.survival (S.threshold n) :=
  S.exceedanceProbability_eq n

theorem order_statistic_binomial_display_source
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) :
    S.order_statistic_binomial_display_statement :=
  S.order_statistic_binomial_display

theorem order_statistic_binomial_probability_display
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) (n : ℕ) :
    vaart1998_orderStatisticBinomialDisplay
        S.binomialLeProbability n (S.orderIndex n)
        (S.exceedanceProbability n) =
      S.binomialLeProbability n (S.exceedanceProbability n)
        (n - S.orderIndex n) :=
  S.order_statistic_binomial_probability n

theorem maximum_probability_event_display
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) (n : ℕ) :
    S.maximumProbability n =
      P.real (vaart1998_maximumLeEvent S.sampleMaximum S.threshold n) :=
  S.maximumProbability_event n

theorem maximum_probability_power_display
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) (n : ℕ) :
    S.maximumProbability n =
      vaart1998_maximumCdfPowerDisplay S.cdf S.threshold n :=
  S.maximumProbability_power n

theorem maximum_probability_survival_display
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) {n : ℕ}
    (hn : (n : ℝ) ≠ 0) :
    S.maximumProbability n =
      vaart1998_maximumCdfSurvivalDisplay S.survival S.threshold n := by
  rw [S.maximumProbability_power n]
  refine vaart1998_maximumCdfPower_eq_survivalDisplay
    S.cdf S.survival S.threshold n hn ?_
  have hs := S.survival_display (S.threshold n)
  linarith

theorem normalized_survival_display
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) (n : ℕ) :
    S.normalizedSurvival n =
      (n : ℝ) * S.survival (S.threshold n) :=
  S.normalizedSurvival_eq n

theorem normalized_survival_converges
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) :
    Tendsto S.normalizedSurvival atTop (𝓝 S.tau) :=
  S.normalizedSurvival_tendsto

theorem maximum_probability_converges_exp
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) :
    Tendsto S.maximumProbability atTop (𝓝 (Real.exp (-S.tau))) :=
  S.maximumProbability_tendsto_exp

theorem lemma21_12_equivalence
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) :
    Tendsto S.maximumProbability atTop (𝓝 (Real.exp (-S.tau))) ↔
      Tendsto S.normalizedSurvival atTop (𝓝 S.tau) :=
  S.lemma21_12_iff

theorem infinite_tau_source_clause
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) :
    S.infinite_tau_source_statement :=
  S.infinite_tau_source

theorem interesting_limits_source
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (S : Vaart1998Lemma21_12MaximumSource (P := P)) :
    S.interesting_limits_statement :=
  S.interesting_limits

end Vaart1998Lemma21_12MaximumSource

/-- Extremal type (i), the Gumbel CDF `exp(-exp(-x))`. -/
def vaart1998_extremeValueTypeI (x : ℝ) : ℝ :=
  Real.exp (-Real.exp (-x))

/-- Extremal type (ii), the Fréchet-form CDF on `[0,infinity)`. -/
def vaart1998_extremeValueTypeII (alpha x : ℝ) : ℝ :=
  Real.exp (-(1 / Real.rpow x alpha))

/-- Extremal type (iii), the reversed-Weibull-form CDF on `(-infinity,0]`. -/
def vaart1998_extremeValueTypeIII (alpha x : ℝ) : ℝ :=
  Real.exp (-(Real.rpow (-x) alpha))

def vaart1998_extremeValueTypeISupport : Set ℝ :=
  Set.univ

def vaart1998_extremeValueTypeIISupport : Set ℝ :=
  Set.Ici (0 : ℝ)

def vaart1998_extremeValueTypeIIISupport : Set ℝ :=
  Set.Iic (0 : ℝ)

/-- Location-scale family generated by a CDF. -/
def vaart1998_locationScaleFamily
    (G : ℝ -> ℝ) (location scale : ℝ) : ℝ -> ℝ :=
  fun x => G ((x - location) / scale)

/-- General normalized maximum `b_n^{-1}(X_{n(n)}-a_n)`. -/
def vaart1998_normalizedMaximum
    {Ω : Type*} (sampleMaximum : ℕ -> Ω -> ℝ)
    (center scale : ℕ -> ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (scale n)⁻¹ * (sampleMaximum n ω - center n)

theorem vaart1998_extremeValueTypeI_apply (x : ℝ) :
    vaart1998_extremeValueTypeI x = Real.exp (-Real.exp (-x)) :=
  rfl

theorem vaart1998_extremeValueTypeII_apply (alpha x : ℝ) :
    vaart1998_extremeValueTypeII alpha x =
      Real.exp (-(1 / Real.rpow x alpha)) :=
  rfl

theorem vaart1998_extremeValueTypeIII_apply (alpha x : ℝ) :
    vaart1998_extremeValueTypeIII alpha x =
      Real.exp (-(Real.rpow (-x) alpha)) :=
  rfl

theorem vaart1998_locationScaleFamily_apply
    (G : ℝ -> ℝ) (location scale x : ℝ) :
    vaart1998_locationScaleFamily G location scale x =
      G ((x - location) / scale) :=
  rfl

/-- Uniform finite-endpoint survival display `(1-t)^alpha`. -/
def vaart1998_uniformEndpointSurvival (alpha t : ℝ) : ℝ :=
  Real.rpow (1 - t) alpha

/-- Uniform finite-endpoint threshold `1 + n^{-1/alpha} x`. -/
def vaart1998_uniformEndpointThreshold
    (alpha x : ℝ) (n : ℕ) : ℝ :=
  1 + Real.rpow (n : ℝ) (-(1 / alpha)) * x

/-- Uniform finite-endpoint normalized maximum
`n^{1/alpha}(X_{n(n)}-1)`. -/
def vaart1998_uniformEndpointNormalizedMaximum
    {Ω : Type*} (sampleMaximum : ℕ -> Ω -> ℝ)
    (alpha : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  Real.rpow (n : ℝ) (1 / alpha) * (sampleMaximum n ω - 1)

/-- Pareto survival display `(mu/t)^alpha`. -/
def vaart1998_paretoSurvival (mu alpha t : ℝ) : ℝ :=
  Real.rpow (mu / t) alpha

/-- Pareto threshold `n^{1/alpha} mu x`. -/
def vaart1998_paretoThreshold
    (mu alpha x : ℝ) (n : ℕ) : ℝ :=
  Real.rpow (n : ℝ) (1 / alpha) * mu * x

/-- Pareto normalized maximum `n^{-1/alpha} X_{n(n)} / mu`. -/
def vaart1998_paretoNormalizedMaximum
    {Ω : Type*} (sampleMaximum : ℕ -> Ω -> ℝ)
    (mu alpha : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  Real.rpow (n : ℝ) (-(1 / alpha)) * sampleMaximum n ω / mu

/-- Normal maximum centering constant from Example 21.16. -/
def vaart1998_normalMaximumCenter (n : ℕ) : ℝ :=
  Real.sqrt (2 * Real.log (n : ℝ)) -
    (1 / 2) *
      ((Real.log (Real.log (n : ℝ)) + Real.log (4 * Real.pi)) /
        Real.sqrt (2 * Real.log (n : ℝ)))

/-- Normal maximum scale `1/sqrt(2 log n)`. -/
def vaart1998_normalMaximumScale (n : ℕ) : ℝ :=
  1 / Real.sqrt (2 * Real.log (n : ℝ))

/-- Normal maximum normalization
`sqrt(2 log n) (X_{n(n)} - a_n)`. -/
def vaart1998_normalMaximumNormalized
    {Ω : Type*} (sampleMaximum : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  Real.sqrt (2 * Real.log (n : ℝ)) *
    (sampleMaximum n ω - vaart1998_normalMaximumCenter n)

theorem vaart1998_uniformEndpointThreshold_apply
    (alpha x : ℝ) (n : ℕ) :
    vaart1998_uniformEndpointThreshold alpha x n =
      1 + Real.rpow (n : ℝ) (-(1 / alpha)) * x :=
  rfl

theorem vaart1998_paretoThreshold_apply
    (mu alpha x : ℝ) (n : ℕ) :
    vaart1998_paretoThreshold mu alpha x n =
      Real.rpow (n : ℝ) (1 / alpha) * mu * x :=
  rfl

theorem vaart1998_normalMaximumCenter_apply (n : ℕ) :
    vaart1998_normalMaximumCenter n =
      Real.sqrt (2 * Real.log (n : ℝ)) -
        (1 / 2) *
          ((Real.log (Real.log (n : ℝ)) + Real.log (4 * Real.pi)) /
            Real.sqrt (2 * Real.log (n : ℝ))) :=
  rfl

theorem vaart1998_normalMaximumScale_apply (n : ℕ) :
    vaart1998_normalMaximumScale n =
      1 / Real.sqrt (2 * Real.log (n : ℝ)) :=
  rfl

/--
Source package for Theorem 21.13 and Examples 21.14-21.16.  It records the
three extremal distribution types, the location-scale conclusion, and the
uniform, Pareto, and normal normalizations derived from Lemma 21.12.
-/
structure Vaart1998Theorem21_13ExtremalTypesSource
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] where
  lemma21_12 : @Vaart1998Lemma21_12MaximumSource Ω _ P _
  sampleMaximum : ℕ -> Ω -> ℝ
  center : ℕ -> ℝ
  scale : ℕ -> ℝ
  normalizedMaximum : ℕ -> Ω -> ℝ
  limitStatistic : Ω' -> ℝ
  limitCdf : ℝ -> ℝ
  baseExtremalCdf : ℝ -> ℝ
  location : ℝ
  scaleLocationFamily : ℝ
  scaleLocationFamily_pos : 0 < scaleLocationFamily
  theorem21_13_hypothesis_statement : Prop
  theorem21_13_hypothesis : theorem21_13_hypothesis_statement
  normalizedMaximum_eq :
    ∀ n ω,
      normalizedMaximum n ω =
        vaart1998_normalizedMaximum sampleMaximum center scale n ω
  normalizedMaximum_converges :
    TendstoInDistribution normalizedMaximum atTop limitStatistic
      (fun _ : ℕ => P) Q
  limit_cdf_nondegenerate_statement : Prop
  limit_cdf_nondegenerate : limit_cdf_nondegenerate_statement
  base_extremal_type_statement : Prop
  base_extremal_type : base_extremal_type_statement
  limitCdf_locationScale :
    limitCdf =
      vaart1998_locationScaleFamily baseExtremalCdf location
        scaleLocationFamily
  typeI_display :
    vaart1998_extremeValueTypeISupport = Set.univ ∧
      ∀ x, vaart1998_extremeValueTypeI x = Real.exp (-Real.exp (-x))
  typeII_display :
    ∀ alpha, 0 < alpha ->
      vaart1998_extremeValueTypeIISupport = Set.Ici (0 : ℝ) ∧
        ∀ x, vaart1998_extremeValueTypeII alpha x =
          Real.exp (-(1 / Real.rpow x alpha))
  typeIII_display :
    ∀ alpha, 0 < alpha ->
      vaart1998_extremeValueTypeIIISupport = Set.Iic (0 : ℝ) ∧
        ∀ x, vaart1998_extremeValueTypeIII alpha x =
          Real.exp (-(Real.rpow (-x) alpha))

/-- Source package for Examples 21.14-21.16. -/
structure Vaart1998Examples21_14_21_16ExtremeValueSource
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] where
  theorem21_13 :
    @Vaart1998Theorem21_13ExtremalTypesSource Ω Ω' _ P _ _ Q _
  uniformMaximum : ℕ -> Ω -> ℝ
  paretoMaximum : ℕ -> Ω -> ℝ
  normalMaximum : ℕ -> Ω -> ℝ
  uniformLimit : Ω' -> ℝ
  paretoLimit : Ω' -> ℝ
  normalLimit : Ω' -> ℝ
  uniformAlpha : ℝ
  uniformAlpha_pos : 0 < uniformAlpha
  paretoMu : ℝ
  paretoMu_pos : 0 < paretoMu
  paretoAlpha : ℝ
  paretoAlpha_pos : 0 < paretoAlpha
  normalSurvival : ℝ -> ℝ
  normalDensity : ℝ -> ℝ
  uniform_survival_display :
    ∀ t, vaart1998_uniformEndpointSurvival uniformAlpha t =
      Real.rpow (1 - t) uniformAlpha
  uniform_tail_limit :
    ∀ x, x ≤ 0 ->
      Tendsto
        (fun n : ℕ =>
          (n : ℝ) *
            vaart1998_uniformEndpointSurvival uniformAlpha
              (vaart1998_uniformEndpointThreshold uniformAlpha x n))
        atTop (𝓝 (Real.rpow (-x) uniformAlpha))
  uniform_maximum_converges :
    TendstoInDistribution
      (fun n ω =>
        vaart1998_uniformEndpointNormalizedMaximum
          uniformMaximum uniformAlpha n ω)
      atTop uniformLimit (fun _ : ℕ => P) Q
  uniform_alpha_one_negative_exponential_statement : Prop
  uniform_alpha_one_negative_exponential :
    uniform_alpha_one_negative_exponential_statement
  pareto_survival_display :
    ∀ t, vaart1998_paretoSurvival paretoMu paretoAlpha t =
      Real.rpow (paretoMu / t) paretoAlpha
  pareto_tail_limit :
    ∀ x, 0 < x ->
      Tendsto
        (fun n : ℕ =>
          (n : ℝ) *
            vaart1998_paretoSurvival paretoMu paretoAlpha
              (vaart1998_paretoThreshold paretoMu paretoAlpha x n))
        atTop (𝓝 (1 / Real.rpow x paretoAlpha))
  pareto_maximum_converges :
    TendstoInDistribution
      (fun n ω =>
        vaart1998_paretoNormalizedMaximum
          paretoMaximum paretoMu paretoAlpha n ω)
      atTop paretoLimit (fun _ : ℕ => P) Q
  normal_center_scale_display :
    ∀ n,
      vaart1998_normalMaximumCenter n =
          Real.sqrt (2 * Real.log (n : ℝ)) -
            (1 / 2) *
              ((Real.log (Real.log (n : ℝ)) + Real.log (4 * Real.pi)) /
                Real.sqrt (2 * Real.log (n : ℝ))) ∧
        vaart1998_normalMaximumScale n =
          1 / Real.sqrt (2 * Real.log (n : ℝ))
  mills_ratio_statement : Prop
  mills_ratio : mills_ratio_statement
  normal_tail_limit :
    ∀ x,
      Tendsto
        (fun n : ℕ =>
          (n : ℝ) * normalSurvival
            (vaart1998_normalMaximumCenter n +
              vaart1998_normalMaximumScale n * x))
        atTop (𝓝 (Real.exp (-x)))
  normal_maximum_converges :
    TendstoInDistribution
      (fun n ω => vaart1998_normalMaximumNormalized normalMaximum n ω)
      atTop normalLimit (fun _ : ℕ => P) Q

namespace Vaart1998Theorem21_13ExtremalTypesSource

theorem normalized_maximum_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_13ExtremalTypesSource (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.normalizedMaximum n ω =
      vaart1998_normalizedMaximum S.sampleMaximum S.center S.scale n ω :=
  S.normalizedMaximum_eq n ω

theorem normalized_maximum_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_13ExtremalTypesSource (P := P) (Q := Q)) :
    TendstoInDistribution S.normalizedMaximum atTop S.limitStatistic
      (fun _ : ℕ => P) Q :=
  S.normalizedMaximum_converges

theorem location_scale_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_13ExtremalTypesSource (P := P) (Q := Q)) :
    S.limitCdf =
      vaart1998_locationScaleFamily S.baseExtremalCdf S.location
        S.scaleLocationFamily :=
  S.limitCdf_locationScale

theorem typeI_display_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_13ExtremalTypesSource (P := P) (Q := Q)) :
    vaart1998_extremeValueTypeISupport = Set.univ ∧
      ∀ x, vaart1998_extremeValueTypeI x = Real.exp (-Real.exp (-x)) :=
  S.typeI_display

theorem typeII_display_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_13ExtremalTypesSource (P := P) (Q := Q))
    {alpha : ℝ} (halpha : 0 < alpha) :
    vaart1998_extremeValueTypeIISupport = Set.Ici (0 : ℝ) ∧
      ∀ x, vaart1998_extremeValueTypeII alpha x =
        Real.exp (-(1 / Real.rpow x alpha)) :=
  S.typeII_display alpha halpha

theorem typeIII_display_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_13ExtremalTypesSource (P := P) (Q := Q))
    {alpha : ℝ} (halpha : 0 < alpha) :
    vaart1998_extremeValueTypeIIISupport = Set.Iic (0 : ℝ) ∧
      ∀ x, vaart1998_extremeValueTypeIII alpha x =
        Real.exp (-(Real.rpow (-x) alpha)) :=
  S.typeIII_display alpha halpha

end Vaart1998Theorem21_13ExtremalTypesSource

namespace Vaart1998Examples21_14_21_16ExtremeValueSource

theorem theorem21_13_location_scale
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q)) :
    S.theorem21_13.limitCdf =
      vaart1998_locationScaleFamily S.theorem21_13.baseExtremalCdf
        S.theorem21_13.location S.theorem21_13.scaleLocationFamily :=
  S.theorem21_13.limitCdf_locationScale

theorem uniform_tail_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q))
    {x : ℝ} (hx : x ≤ 0) :
    Tendsto
      (fun n : ℕ =>
        (n : ℝ) *
          vaart1998_uniformEndpointSurvival S.uniformAlpha
            (vaart1998_uniformEndpointThreshold S.uniformAlpha x n))
      atTop (𝓝 (Real.rpow (-x) S.uniformAlpha)) :=
  S.uniform_tail_limit x hx

theorem uniform_maximum_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q)) :
    TendstoInDistribution
      (fun n ω =>
        vaart1998_uniformEndpointNormalizedMaximum
          S.uniformMaximum S.uniformAlpha n ω)
      atTop S.uniformLimit (fun _ : ℕ => P) Q :=
  S.uniform_maximum_converges

theorem pareto_tail_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q))
    {x : ℝ} (hx : 0 < x) :
    Tendsto
      (fun n : ℕ =>
        (n : ℝ) *
          vaart1998_paretoSurvival S.paretoMu S.paretoAlpha
            (vaart1998_paretoThreshold S.paretoMu S.paretoAlpha x n))
      atTop (𝓝 (1 / Real.rpow x S.paretoAlpha)) :=
  S.pareto_tail_limit x hx

theorem pareto_maximum_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q)) :
    TendstoInDistribution
      (fun n ω =>
        vaart1998_paretoNormalizedMaximum
          S.paretoMaximum S.paretoMu S.paretoAlpha n ω)
      atTop S.paretoLimit (fun _ : ℕ => P) Q :=
  S.pareto_maximum_converges

theorem normal_center_scale_display_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q))
    (n : ℕ) :
    vaart1998_normalMaximumCenter n =
        Real.sqrt (2 * Real.log (n : ℝ)) -
          (1 / 2) *
            ((Real.log (Real.log (n : ℝ)) + Real.log (4 * Real.pi)) /
              Real.sqrt (2 * Real.log (n : ℝ))) ∧
      vaart1998_normalMaximumScale n =
        1 / Real.sqrt (2 * Real.log (n : ℝ)) :=
  S.normal_center_scale_display n

theorem normal_tail_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q))
    (x : ℝ) :
    Tendsto
      (fun n : ℕ =>
        (n : ℝ) * S.normalSurvival
          (vaart1998_normalMaximumCenter n +
            vaart1998_normalMaximumScale n * x))
      atTop (𝓝 (Real.exp (-x))) :=
  S.normal_tail_limit x

theorem normal_maximum_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q)) :
    TendstoInDistribution
      (fun n ω => vaart1998_normalMaximumNormalized S.normalMaximum n ω)
      atTop S.normalLimit (fun _ : ℕ => P) Q :=
  S.normal_maximum_converges

theorem mills_ratio_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Examples21_14_21_16ExtremeValueSource (P := P) (Q := Q)) :
    S.mills_ratio_statement :=
  S.mills_ratio

end Vaart1998Examples21_14_21_16ExtremeValueSource

/-- The right endpoint display `tau_F = sup {t : F t < 1}`. -/
def vaart1998_distributionRightEndpoint (F : ℝ -> ℝ) : ℝ :=
  sSup {t : ℝ | F t < 1}

/-- Endpoint quantile sequence `u_n = F^{-1}(1 - 1/n)`. -/
def vaart1998_endpointQuantileSequence
    (quantile : ℝ -> ℝ) (n : ℕ) : ℝ :=
  quantile (1 - (n : ℝ)⁻¹)

/-- Type (i) endpoint tail ratio from Theorem 21.17. -/
def vaart1998_endpointTailRatioTypeI
    (survival endpointScale : ℝ -> ℝ) (t x : ℝ) : ℝ :=
  survival (t + endpointScale t * x) / survival t

/-- Type (ii) endpoint tail ratio from Theorem 21.17. -/
def vaart1998_endpointTailRatioTypeII
    (survival : ℝ -> ℝ) (t x : ℝ) : ℝ :=
  survival (t * x) / survival t

/-- Type (iii) finite-endpoint tail ratio from Theorem 21.17. -/
def vaart1998_endpointTailRatioTypeIII
    (survival : ℝ -> ℝ) (rightEndpoint t x : ℝ) : ℝ :=
  survival (rightEndpoint - (rightEndpoint - t) * x) / survival t

/-- Type (i) domain-of-attraction condition. -/
def vaart1998_domainAttractionTypeICondition
    (survival endpointScale : ℝ -> ℝ) (endpointFilter : Filter ℝ) : Prop :=
  (∀ t : ℝ, 0 < endpointScale t) ∧
    ∀ x : ℝ,
      Tendsto
        (fun t : ℝ =>
          vaart1998_endpointTailRatioTypeI survival endpointScale t x)
        endpointFilter (𝓝 (Real.exp (-x)))

/-- Type (ii) domain-of-attraction condition. -/
def vaart1998_domainAttractionTypeIICondition
    (survival : ℝ -> ℝ) (alpha : ℝ) : Prop :=
  ∀ x : ℝ, 0 < x ->
    Tendsto
      (fun t : ℝ => vaart1998_endpointTailRatioTypeII survival t x)
      atTop (𝓝 (1 / Real.rpow x alpha))

/-- Type (iii) domain-of-attraction condition. -/
def vaart1998_domainAttractionTypeIIICondition
    (survival : ℝ -> ℝ) (rightEndpoint alpha : ℝ) : Prop :=
  ∀ x : ℝ, 0 < x ->
    Tendsto
      (fun t : ℝ =>
        vaart1998_endpointTailRatioTypeIII survival rightEndpoint t x)
      (𝓝[<] rightEndpoint) (𝓝 (Real.rpow x alpha))

theorem vaart1998_distributionRightEndpoint_apply (F : ℝ -> ℝ) :
    vaart1998_distributionRightEndpoint F = sSup {t : ℝ | F t < 1} :=
  rfl

theorem vaart1998_endpointQuantileSequence_apply
    (quantile : ℝ -> ℝ) (n : ℕ) :
    vaart1998_endpointQuantileSequence quantile n =
      quantile (1 - (n : ℝ)⁻¹) :=
  rfl

theorem vaart1998_endpointTailRatioTypeI_apply
    (survival endpointScale : ℝ -> ℝ) (t x : ℝ) :
    vaart1998_endpointTailRatioTypeI survival endpointScale t x =
      survival (t + endpointScale t * x) / survival t :=
  rfl

theorem vaart1998_endpointTailRatioTypeII_apply
    (survival : ℝ -> ℝ) (t x : ℝ) :
    vaart1998_endpointTailRatioTypeII survival t x =
      survival (t * x) / survival t :=
  rfl

theorem vaart1998_endpointTailRatioTypeIII_apply
    (survival : ℝ -> ℝ) (rightEndpoint t x : ℝ) :
    vaart1998_endpointTailRatioTypeIII survival rightEndpoint t x =
      survival (rightEndpoint - (rightEndpoint - t) * x) / survival t :=
  rfl

/--
Source package for Theorem 21.17.  It records the three tail-ratio
domain-of-attraction criteria, the endpoint quantile constants
`u_n = F^{-1}(1 - 1/n)`, the constants proposed in the theorem for the three
cases, and the proof-route clauses through Lemma 21.12.
-/
structure Vaart1998Theorem21_17DomainAttractionSource
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] where
  theorem21_13 :
    @Vaart1998Theorem21_13ExtremalTypesSource Ω Ω' _ P _ _ Q _
  lemma21_12 : @Vaart1998Lemma21_12MaximumSource Ω _ P _
  cdf : ℝ -> ℝ
  survival : ℝ -> ℝ
  quantile : ℝ -> ℝ
  rightEndpoint : ℝ
  endpointFilter : Filter ℝ
  endpointScale : ℝ -> ℝ
  alpha : ℝ
  alpha_pos : 0 < alpha
  sampleMaximum : ℕ -> Ω -> ℝ
  center : ℕ -> ℝ
  scale : ℕ -> ℝ
  normalizedMaximum : ℕ -> Ω -> ℝ
  limitStatistic : Ω' -> ℝ
  endpointQuantile : ℕ -> ℝ
  survival_eq : survival = vaart1998_survivalFunction cdf
  rightEndpoint_eq : rightEndpoint = vaart1998_distributionRightEndpoint cdf
  endpointQuantile_eq :
    ∀ n, endpointQuantile n =
      vaart1998_endpointQuantileSequence quantile n
  normalizedMaximum_eq :
    ∀ n ω,
      normalizedMaximum n ω =
        vaart1998_normalizedMaximum sampleMaximum center scale n ω
  normalizedMaximum_converges :
    TendstoInDistribution normalizedMaximum atTop limitStatistic
      (fun _ : ℕ => P) Q
  exists_normalization_iff_domain_condition_statement : Prop
  exists_normalization_iff_domain_condition :
    exists_normalization_iff_domain_condition_statement
  typeI_condition :
    vaart1998_domainAttractionTypeICondition survival endpointScale
      endpointFilter
  typeII_infinite_endpoint_statement : Prop
  typeII_infinite_endpoint : typeII_infinite_endpoint_statement
  typeII_condition :
    vaart1998_domainAttractionTypeIICondition survival alpha
  typeIII_finite_endpoint_statement : Prop
  typeIII_finite_endpoint : typeIII_finite_endpoint_statement
  typeIII_condition :
    vaart1998_domainAttractionTypeIIICondition survival rightEndpoint alpha
  typeI_constants :
    ∀ n, center n = endpointQuantile n ∧
      scale n = endpointScale (endpointQuantile n)
  typeII_constants :
    ∀ n, center n = 0 ∧ scale n = endpointQuantile n
  typeIII_constants :
    ∀ n, center n = rightEndpoint ∧
      scale n = rightEndpoint - endpointQuantile n
  normalized_survival_endpointQuantile_tendsto_one :
    Tendsto
      (fun n : ℕ => (n : ℝ) * survival (endpointQuantile n))
      atTop (𝓝 1)
  jump_small_statement : Prop
  jump_small : jump_small_statement
  typeI_lemma21_12_tail_limit :
    ∀ x : ℝ,
      Tendsto
        (fun n : ℕ =>
          (n : ℝ) *
            survival
              (endpointQuantile n +
                endpointScale (endpointQuantile n) * x))
        atTop (𝓝 (Real.exp (-x)))
  typeII_lemma21_12_tail_limit :
    ∀ x : ℝ, 0 < x ->
      Tendsto
        (fun n : ℕ =>
          (n : ℝ) * survival (endpointQuantile n * x))
        atTop (𝓝 (1 / Real.rpow x alpha))
  typeIII_lemma21_12_tail_limit :
    ∀ x : ℝ, 0 < x ->
      Tendsto
        (fun n : ℕ =>
          (n : ℝ) *
            survival
              (rightEndpoint - (rightEndpoint - endpointQuantile n) * x))
        atTop (𝓝 (Real.rpow x alpha))

namespace Vaart1998Theorem21_17DomainAttractionSource

theorem survival_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q)) :
    S.survival = vaart1998_survivalFunction S.cdf :=
  S.survival_eq

theorem right_endpoint_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q)) :
    S.rightEndpoint = vaart1998_distributionRightEndpoint S.cdf :=
  S.rightEndpoint_eq

theorem endpoint_quantile_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    (n : ℕ) :
    S.endpointQuantile n =
      vaart1998_endpointQuantileSequence S.quantile n :=
  S.endpointQuantile_eq n

theorem normalized_maximum_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.normalizedMaximum n ω =
      vaart1998_normalizedMaximum S.sampleMaximum S.center S.scale n ω :=
  S.normalizedMaximum_eq n ω

theorem normalized_maximum_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q)) :
    TendstoInDistribution S.normalizedMaximum atTop S.limitStatistic
      (fun _ : ℕ => P) Q :=
  S.normalizedMaximum_converges

theorem normalization_iff_domain_condition_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q)) :
    S.exists_normalization_iff_domain_condition_statement :=
  S.exists_normalization_iff_domain_condition

theorem typeI_endpointScale_pos
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    (t : ℝ) :
    0 < S.endpointScale t :=
  S.typeI_condition.1 t

theorem typeI_tail_ratio_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    (x : ℝ) :
    Tendsto
      (fun t : ℝ =>
        vaart1998_endpointTailRatioTypeI S.survival S.endpointScale t x)
      S.endpointFilter (𝓝 (Real.exp (-x))) :=
  S.typeI_condition.2 x

theorem typeII_infinite_endpoint_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q)) :
    S.typeII_infinite_endpoint_statement :=
  S.typeII_infinite_endpoint

theorem typeII_tail_ratio_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    {x : ℝ} (hx : 0 < x) :
    Tendsto
      (fun t : ℝ => vaart1998_endpointTailRatioTypeII S.survival t x)
      atTop (𝓝 (1 / Real.rpow x S.alpha)) :=
  S.typeII_condition x hx

theorem typeIII_finite_endpoint_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q)) :
    S.typeIII_finite_endpoint_statement :=
  S.typeIII_finite_endpoint

theorem typeIII_tail_ratio_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    {x : ℝ} (hx : 0 < x) :
    Tendsto
      (fun t : ℝ =>
        vaart1998_endpointTailRatioTypeIII S.survival S.rightEndpoint t x)
      (𝓝[<] S.rightEndpoint) (𝓝 (Real.rpow x S.alpha)) :=
  S.typeIII_condition x hx

theorem typeI_constants_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    (n : ℕ) :
    S.center n = S.endpointQuantile n ∧
      S.scale n = S.endpointScale (S.endpointQuantile n) :=
  S.typeI_constants n

theorem typeII_constants_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    (n : ℕ) :
    S.center n = 0 ∧ S.scale n = S.endpointQuantile n :=
  S.typeII_constants n

theorem typeIII_constants_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    (n : ℕ) :
    S.center n = S.rightEndpoint ∧
      S.scale n = S.rightEndpoint - S.endpointQuantile n :=
  S.typeIII_constants n

theorem normalized_survival_endpointQuantile_tendsto_one_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q)) :
    Tendsto
      (fun n : ℕ => (n : ℝ) * S.survival (S.endpointQuantile n))
      atTop (𝓝 1) :=
  S.normalized_survival_endpointQuantile_tendsto_one

theorem jump_small_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q)) :
    S.jump_small_statement :=
  S.jump_small

theorem typeI_lemma21_12_tail_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    (x : ℝ) :
    Tendsto
      (fun n : ℕ =>
        (n : ℝ) *
          S.survival
            (S.endpointQuantile n +
              S.endpointScale (S.endpointQuantile n) * x))
      atTop (𝓝 (Real.exp (-x))) :=
  S.typeI_lemma21_12_tail_limit x

theorem typeII_lemma21_12_tail_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    {x : ℝ} (hx : 0 < x) :
    Tendsto
      (fun n : ℕ =>
        (n : ℝ) * S.survival (S.endpointQuantile n * x))
      atTop (𝓝 (1 / Real.rpow x S.alpha)) :=
  S.typeII_lemma21_12_tail_limit x hx

theorem typeIII_lemma21_12_tail_limit_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_17DomainAttractionSource (P := P) (Q := Q))
    {x : ℝ} (hx : 0 < x) :
    Tendsto
      (fun n : ℕ =>
        (n : ℝ) *
          S.survival
            (S.rightEndpoint - (S.rightEndpoint - S.endpointQuantile n) * x))
      atTop (𝓝 (Real.rpow x S.alpha)) :=
  S.typeIII_lemma21_12_tail_limit x hx

end Vaart1998Theorem21_17DomainAttractionSource

/-- Threshold `a_n + b_n x` used in the proof of Theorem 21.18. -/
def vaart1998_extremeOrderThreshold
    (center scale : ℕ -> ℝ) (n : ℕ) (x : ℝ) : ℝ :=
  center n + scale n * x

/-- Tail probability `p_n = \bar F(a_n + b_n x)`. -/
def vaart1998_extremeOrderTailProbability
    (survival : ℝ -> ℝ) (center scale : ℕ -> ℝ)
    (n : ℕ) (x : ℝ) : ℝ :=
  survival (vaart1998_extremeOrderThreshold center scale n x)

/-- Normalized `(k+1)`-th largest order statistic
`b_n^{-1}(X_{n(n-k)}-a_n)`. -/
def vaart1998_normalizedExtremeOrderStatistic
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (center scale : ℕ -> ℝ) (n k : ℕ) (ω : Ω) : ℝ :=
  (scale n)⁻¹ * (orderStatistic n (n - k) ω - center n)

/-- Poisson CDF display `exp(-lambda) * sum_{i=0}^k lambda^i / i!`. -/
def vaart1998_poissonLeProbabilityDisplay (lambda : ℝ) (k : ℕ) : ℝ :=
  Real.exp (-lambda) *
    ∑ i ∈ Finset.range (k + 1),
      lambda ^ i / (Nat.factorial i : ℝ)

/-- The Theorem 21.18 limiting CDF
`H(x)=G(x) sum_{i=0}^k (-log G(x))^i / i!`. -/
def vaart1998_extremeOrderLimitCdf
    (G : ℝ -> ℝ) (k : ℕ) (x : ℝ) : ℝ :=
  G x *
    ∑ i ∈ Finset.range (k + 1),
      (-Real.log (G x)) ^ i / (Nat.factorial i : ℝ)

theorem vaart1998_extremeOrderThreshold_apply
    (center scale : ℕ -> ℝ) (n : ℕ) (x : ℝ) :
    vaart1998_extremeOrderThreshold center scale n x =
      center n + scale n * x :=
  rfl

theorem vaart1998_extremeOrderTailProbability_apply
    (survival : ℝ -> ℝ) (center scale : ℕ -> ℝ)
    (n : ℕ) (x : ℝ) :
    vaart1998_extremeOrderTailProbability survival center scale n x =
      survival (center n + scale n * x) :=
  rfl

theorem vaart1998_normalizedExtremeOrderStatistic_apply
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (center scale : ℕ -> ℝ) (n k : ℕ) (ω : Ω) :
    vaart1998_normalizedExtremeOrderStatistic orderStatistic center scale
        n k ω =
      (scale n)⁻¹ * (orderStatistic n (n - k) ω - center n) :=
  rfl

theorem vaart1998_poissonLeProbabilityDisplay_apply
    (lambda : ℝ) (k : ℕ) :
    vaart1998_poissonLeProbabilityDisplay lambda k =
      Real.exp (-lambda) *
        ∑ i ∈ Finset.range (k + 1),
          lambda ^ i / (Nat.factorial i : ℝ) :=
  rfl

theorem vaart1998_extremeOrderLimitCdf_apply
    (G : ℝ -> ℝ) (k : ℕ) (x : ℝ) :
    vaart1998_extremeOrderLimitCdf G k x =
      G x *
        ∑ i ∈ Finset.range (k + 1),
          (-Real.log (G x)) ^ i / (Nat.factorial i : ℝ) :=
  rfl

/--
Source package for Theorem 21.18.  It records that if the normalized maximum
converges to `G`, then the `(k+1)`-th largest normalized order statistic
converges with the same centering/scaling and limiting distribution function
`H(x)=G(x) sum_{i=0}^k (-log G(x))^i/i!`.  The proof-route fields expose the
tail probability `p_n`, the order-statistic-to-binomial reduction, and the
binomial-to-Poisson approximation.
-/
structure Vaart1998Theorem21_18ExtremeOrderSource
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] where
  theorem21_17 :
    @Vaart1998Theorem21_17DomainAttractionSource Ω Ω' _ P _ _ Q _
  lemma21_12 : @Vaart1998Lemma21_12MaximumSource Ω _ P _
  k : ℕ
  cdf : ℝ -> ℝ
  survival : ℝ -> ℝ
  center : ℕ -> ℝ
  scale : ℕ -> ℝ
  sampleMaximum : ℕ -> Ω -> ℝ
  orderStatistic : ℕ -> ℕ -> Ω -> ℝ
  maximumNormalized : ℕ -> Ω -> ℝ
  extremeOrderNormalized : ℕ -> Ω -> ℝ
  maximumLimitStatistic : Ω' -> ℝ
  extremeOrderLimitStatistic : Ω' -> ℝ
  maximumLimitCdf : ℝ -> ℝ
  extremeOrderLimitCdf : ℝ -> ℝ
  tailProbability : ℕ -> ℝ -> ℝ
  orderStatisticProbability : ℕ -> ℝ -> ℝ
  binomialLeProbability : ℕ -> ℝ -> ℕ -> ℝ
  maximumNormalized_eq :
    ∀ n ω,
      maximumNormalized n ω =
        vaart1998_normalizedMaximum sampleMaximum center scale n ω
  maximum_converges :
    TendstoInDistribution maximumNormalized atTop maximumLimitStatistic
      (fun _ : ℕ => P) Q
  extremeOrderNormalized_eq :
    ∀ n ω,
      extremeOrderNormalized n ω =
        vaart1998_normalizedExtremeOrderStatistic orderStatistic center scale
          n k ω
  extremeOrder_converges :
    TendstoInDistribution extremeOrderNormalized atTop
      extremeOrderLimitStatistic (fun _ : ℕ => P) Q
  same_centering_scaling_statement : Prop
  same_centering_scaling : same_centering_scaling_statement
  limit_cdf_display :
    extremeOrderLimitCdf = vaart1998_extremeOrderLimitCdf maximumLimitCdf k
  tailProbability_eq :
    ∀ n x,
      tailProbability n x =
        vaart1998_extremeOrderTailProbability survival center scale n x
  tailProbability_tendsto_neg_log :
    ∀ x, ContinuousAt maximumLimitCdf x ->
      Tendsto
        (fun n : ℕ => (n : ℝ) * tailProbability n x)
        atTop (𝓝 (-Real.log (maximumLimitCdf x)))
  orderStatisticProbability_eq :
    ∀ n x,
      orderStatisticProbability n x =
        vaart1998_binomialLeProbabilityDisplay binomialLeProbability n
          (tailProbability n x) k
  binomial_poisson_approx :
    ∀ x, ContinuousAt maximumLimitCdf x ->
      Tendsto
        (fun n : ℕ =>
          binomialLeProbability n (tailProbability n x) k)
        atTop
        (𝓝 (vaart1998_poissonLeProbabilityDisplay
          (-Real.log (maximumLimitCdf x)) k))
  poisson_limit_eq_extreme_order_cdf_statement : Prop
  poisson_limit_eq_extreme_order_cdf :
    poisson_limit_eq_extreme_order_cdf_statement
  joint_extremes_omitted_statement : Prop
  joint_extremes_omitted : joint_extremes_omitted_statement

namespace Vaart1998Theorem21_18ExtremeOrderSource

theorem maximum_normalized_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.maximumNormalized n ω =
      vaart1998_normalizedMaximum S.sampleMaximum S.center S.scale n ω :=
  S.maximumNormalized_eq n ω

theorem maximum_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q)) :
    TendstoInDistribution S.maximumNormalized atTop S.maximumLimitStatistic
      (fun _ : ℕ => P) Q :=
  S.maximum_converges

theorem extreme_order_normalized_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.extremeOrderNormalized n ω =
      vaart1998_normalizedExtremeOrderStatistic S.orderStatistic S.center
        S.scale n S.k ω :=
  S.extremeOrderNormalized_eq n ω

theorem extreme_order_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q)) :
    TendstoInDistribution S.extremeOrderNormalized atTop
      S.extremeOrderLimitStatistic (fun _ : ℕ => P) Q :=
  S.extremeOrder_converges

theorem same_centering_scaling_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q)) :
    S.same_centering_scaling_statement :=
  S.same_centering_scaling

theorem limit_cdf_display_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q)) :
    S.extremeOrderLimitCdf =
      vaart1998_extremeOrderLimitCdf S.maximumLimitCdf S.k :=
  S.limit_cdf_display

theorem tail_probability_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q))
    (n : ℕ) (x : ℝ) :
    S.tailProbability n x =
      S.survival (S.center n + S.scale n * x) :=
  S.tailProbability_eq n x

theorem tail_probability_tendsto_neg_log_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q))
    {x : ℝ} (hx : ContinuousAt S.maximumLimitCdf x) :
    Tendsto
      (fun n : ℕ => (n : ℝ) * S.tailProbability n x)
      atTop (𝓝 (-Real.log (S.maximumLimitCdf x))) :=
  S.tailProbability_tendsto_neg_log x hx

theorem order_statistic_probability_binomial_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q))
    (n : ℕ) (x : ℝ) :
    S.orderStatisticProbability n x =
      S.binomialLeProbability n (S.tailProbability n x) S.k :=
  S.orderStatisticProbability_eq n x

theorem binomial_poisson_approx_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q))
    {x : ℝ} (hx : ContinuousAt S.maximumLimitCdf x) :
    Tendsto
      (fun n : ℕ =>
        S.binomialLeProbability n (S.tailProbability n x) S.k)
      atTop
      (𝓝 (vaart1998_poissonLeProbabilityDisplay
        (-Real.log (S.maximumLimitCdf x)) S.k)) :=
  S.binomial_poisson_approx x hx

theorem poisson_limit_eq_extreme_order_cdf_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q)) :
    S.poisson_limit_eq_extreme_order_cdf_statement :=
  S.poisson_limit_eq_extreme_order_cdf

theorem joint_extremes_omitted_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Theorem21_18ExtremeOrderSource (P := P) (Q := Q)) :
    S.joint_extremes_omitted_statement :=
  S.joint_extremes_omitted

end Vaart1998Theorem21_18ExtremeOrderSource

/-- Lemma 21.19 empirical-sum coordinate
`n^{-1/2} sum_{i=1}^n g(X_i)`.  The finite range is zero-based, so the
display uses `Finset.range n`. -/
def vaart1998_normalizedEmpiricalGSum
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ) (g : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  (√(n : ℝ))⁻¹ *
    ∑ i ∈ Finset.range n, g (observations i ω)

/-- Lemma 21.19 trimmed sum
`n^{-1/2} sum_{i=1}^{n-1} g(X_{n(i)})`, with order statistics indexed
one-based inside the abstract `orderStatistic` argument. -/
def vaart1998_trimmedExtremeGSum
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ) (g : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  (√(n : ℝ))⁻¹ *
    ∑ i ∈ Finset.range (n - 1), g (orderStatistic n (i + 1) ω)

/-- The negligible deleted-maximum contribution
`n^{-1/2} |g(X_{n(n)})|`. -/
def vaart1998_maximumGContribution
    {Ω : Type*} (sampleMaximum : ℕ -> Ω -> ℝ) (g : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  (√(n : ℝ))⁻¹ * |g (sampleMaximum n ω)|

/-- Pairing operation used for `(G_n g,V_n)` and `(U_n,V_n)`. -/
def vaart1998_extremePair
    {Ω : Type*} (first second : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ × ℝ :=
  (first n ω, second n ω)

/-- Conditional CDF notation `F_n(u | V_n = v)`. -/
def vaart1998_conditionalCdfGivenExtreme
    (conditionalCdf : ℕ -> ℝ -> ℝ -> ℝ)
    (n : ℕ) (u v : ℝ) : ℝ :=
  conditionalCdf n u v

/-- Product CDF display for independent real limits:
`(u,v) ↦ Phi(u) G(v)`. -/
def vaart1998_independentProductCdf
    (normalCdf extremeCdf : ℝ -> ℝ) : ℝ -> ℝ -> ℝ :=
  fun u v => normalCdf u * extremeCdf v

/-- The Cauchy-Schwarz tail bound appearing in Lemma 21.19:
`sqrt((int_{(x,infty)} g^2 dF) * \bar F(x)) / F(x)`. -/
def vaart1998_conditionalMeanTailBound
    (tailSecondMoment survival cdf : ℝ -> ℝ) (x : ℝ) : ℝ :=
  Real.sqrt (tailSecondMoment x * survival x) / cdf x

theorem vaart1998_normalizedEmpiricalGSum_apply
    {Ω : Type*} (observations : ℕ -> Ω -> ℝ) (g : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) :
    vaart1998_normalizedEmpiricalGSum observations g n ω =
      (√(n : ℝ))⁻¹ *
        ∑ i ∈ Finset.range n, g (observations i ω) :=
  rfl

theorem vaart1998_trimmedExtremeGSum_apply
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ) (g : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) :
    vaart1998_trimmedExtremeGSum orderStatistic g n ω =
      (√(n : ℝ))⁻¹ *
        ∑ i ∈ Finset.range (n - 1),
          g (orderStatistic n (i + 1) ω) :=
  rfl

theorem vaart1998_maximumGContribution_apply
    {Ω : Type*} (sampleMaximum : ℕ -> Ω -> ℝ) (g : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) :
    vaart1998_maximumGContribution sampleMaximum g n ω =
      (√(n : ℝ))⁻¹ * |g (sampleMaximum n ω)| :=
  rfl

theorem vaart1998_extremePair_apply
    {Ω : Type*} (first second : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) :
    vaart1998_extremePair first second n ω =
      (first n ω, second n ω) :=
  rfl

theorem vaart1998_conditionalCdfGivenExtreme_apply
    (conditionalCdf : ℕ -> ℝ -> ℝ -> ℝ)
    (n : ℕ) (u v : ℝ) :
    vaart1998_conditionalCdfGivenExtreme conditionalCdf n u v =
      conditionalCdf n u v :=
  rfl

theorem vaart1998_independentProductCdf_apply
    (normalCdf extremeCdf : ℝ -> ℝ) (u v : ℝ) :
    vaart1998_independentProductCdf normalCdf extremeCdf u v =
      normalCdf u * extremeCdf v :=
  rfl

theorem vaart1998_conditionalMeanTailBound_apply
    (tailSecondMoment survival cdf : ℝ -> ℝ) (x : ℝ) :
    vaart1998_conditionalMeanTailBound tailSecondMoment survival cdf x =
      Real.sqrt (tailSecondMoment x * survival x) / cdf x :=
  rfl

/--
Source package for Lemma 21.19.  It records the asymptotic independence of the
centered empirical sum `n^{-1/2} sum_i g(X_i)` and the normalized maximum
`b_n^{-1}(X_{n(n)}-a_n)` under the book hypotheses `Fg=0`, `Fg^2=1`, and a
nondegenerate maximum limit.  The proof-route fields expose the deletion of
the maximum summand, the conditional-CDF reduction, the tail mean bound from
Lemma 21.12, and the Lindeberg-Feller conditional CLT step.
-/
structure Vaart1998Lemma21_19AsymptoticIndependenceSource
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q] where
  theorem21_18 :
    @Vaart1998Theorem21_18ExtremeOrderSource Ω Ω' _ P _ _ Q _
  lemma21_12 : @Vaart1998Lemma21_12MaximumSource Ω _ P _
  cdf : ℝ -> ℝ
  survival : ℝ -> ℝ
  center : ℕ -> ℝ
  scale : ℕ -> ℝ
  observations : ℕ -> Ω -> ℝ
  orderStatistic : ℕ -> ℕ -> Ω -> ℝ
  sampleMaximum : ℕ -> Ω -> ℝ
  g : ℝ -> ℝ
  maximumNormalized : ℕ -> Ω -> ℝ
  empiricalGProcess : ℕ -> Ω -> ℝ
  trimmedGProcess : ℕ -> Ω -> ℝ
  maximumContribution : ℕ -> Ω -> ℝ
  jointEmpiricalExtreme : ℕ -> Ω -> ℝ × ℝ
  jointTrimmedExtreme : ℕ -> Ω -> ℝ × ℝ
  gaussianLimit : Ω' -> ℝ
  extremeLimit : Ω' -> ℝ
  jointLimit : Ω' -> ℝ × ℝ
  normalCdf : ℝ -> ℝ
  extremeLimitCdf : ℝ -> ℝ
  jointLimitCdf : ℝ -> ℝ -> ℝ
  conditionalCdf : ℕ -> ℝ -> ℝ -> ℝ
  conditionalAbsMean : ℕ -> ℝ -> ℝ
  conditionalSecondMoment : ℕ -> ℝ -> ℝ
  conditionalLindebergRemainder : ℕ -> ℝ -> ℝ -> ℝ
  tailSecondMoment : ℝ -> ℝ
  g_measurable : Measurable g
  observations_iid_statement : Prop
  observations_iid : observations_iid_statement
  population_mean_zero_statement : Prop
  population_mean_zero : population_mean_zero_statement
  population_second_moment_one_statement : Prop
  population_second_moment_one : population_second_moment_one_statement
  maximum_limit_nondegenerate_statement : Prop
  maximum_limit_nondegenerate : maximum_limit_nondegenerate_statement
  maximumNormalized_eq :
    ∀ n ω,
      maximumNormalized n ω =
        vaart1998_normalizedMaximum sampleMaximum center scale n ω
  empiricalGProcess_eq :
    ∀ n ω,
      empiricalGProcess n ω =
        vaart1998_normalizedEmpiricalGSum observations g n ω
  trimmedGProcess_eq :
    ∀ n ω,
      trimmedGProcess n ω =
        vaart1998_trimmedExtremeGSum orderStatistic g n ω
  maximumContribution_eq :
    ∀ n ω,
      maximumContribution n ω =
        vaart1998_maximumGContribution sampleMaximum g n ω
  jointEmpiricalExtreme_eq :
    ∀ n ω,
      jointEmpiricalExtreme n ω =
        vaart1998_extremePair empiricalGProcess maximumNormalized n ω
  jointTrimmedExtreme_eq :
    ∀ n ω,
      jointTrimmedExtreme n ω =
        vaart1998_extremePair trimmedGProcess maximumNormalized n ω
  jointLimit_eq :
    ∀ ω, jointLimit ω = (gaussianLimit ω, extremeLimit ω)
  jointLimitCdf_eq :
    jointLimitCdf = vaart1998_independentProductCdf normalCdf extremeLimitCdf
  maximum_converges :
    TendstoInDistribution maximumNormalized atTop extremeLimit
      (fun _ : ℕ => P) Q
  empiricalGProcess_converges :
    TendstoInDistribution empiricalGProcess atTop gaussianLimit
      (fun _ : ℕ => P) Q
  limit_independence :
    _root_.ProbabilityTheory.IndepFun gaussianLimit extremeLimit Q
  trimmed_joint_converges :
    TendstoInDistribution jointTrimmedExtreme atTop jointLimit
      (fun _ : ℕ => P) Q
  joint_converges :
    TendstoInDistribution jointEmpiricalExtreme atTop jointLimit
      (fun _ : ℕ => P) Q
  max_g_contribution_negligible_statement : Prop
  max_g_contribution_negligible : max_g_contribution_negligible_statement
  pair_distance_negligible_statement : Prop
  pair_distance_negligible : pair_distance_negligible_statement
  conditionalCdf_display :
    ∀ n u v,
      vaart1998_conditionalCdfGivenExtreme conditionalCdf n u v =
        conditionalCdf n u v
  conditional_cdf_converges_to_normal_statement : Prop
  conditional_cdf_converges_to_normal :
    conditional_cdf_converges_to_normal_statement
  dominated_convergence_joint_cdf_statement : Prop
  dominated_convergence_joint_cdf : dominated_convergence_joint_cdf_statement
  conditional_distribution_iid_source_statement : Prop
  conditional_distribution_iid_source :
    conditional_distribution_iid_source_statement
  conditionalAbsMean_bound :
    ∀ n v,
      conditionalAbsMean n v ≤
        vaart1998_conditionalMeanTailBound tailSecondMoment survival cdf
          (vaart1998_extremeOrderThreshold center scale n v)
  tail_bound_from_lemma21_12_statement : Prop
  tail_bound_from_lemma21_12 : tail_bound_from_lemma21_12_statement
  sqrt_n_conditional_mean_tendsto_zero_statement : Prop
  sqrt_n_conditional_mean_tendsto_zero :
    sqrt_n_conditional_mean_tendsto_zero_statement
  conditionalSecondMoment_tendsto_one_statement : Prop
  conditionalSecondMoment_tendsto_one :
    conditionalSecondMoment_tendsto_one_statement
  conditional_lindeberg_statement : Prop
  conditional_lindeberg : conditional_lindeberg_statement
  empirical_process_extreme_independence_statement : Prop
  empirical_process_extreme_independence :
    empirical_process_extreme_independence_statement
  delta_method_central_order_statistic_source_statement : Prop
  delta_method_central_order_statistic_source :
    delta_method_central_order_statistic_source_statement

namespace Vaart1998Lemma21_19AsymptoticIndependenceSource

theorem maximum_normalized_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.maximumNormalized n ω =
      vaart1998_normalizedMaximum S.sampleMaximum S.center S.scale n ω :=
  S.maximumNormalized_eq n ω

theorem empirical_g_process_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.empiricalGProcess n ω =
      vaart1998_normalizedEmpiricalGSum S.observations S.g n ω :=
  S.empiricalGProcess_eq n ω

theorem trimmed_g_process_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.trimmedGProcess n ω =
      vaart1998_trimmedExtremeGSum S.orderStatistic S.g n ω :=
  S.trimmedGProcess_eq n ω

theorem maximum_contribution_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.maximumContribution n ω =
      vaart1998_maximumGContribution S.sampleMaximum S.g n ω :=
  S.maximumContribution_eq n ω

theorem joint_empirical_extreme_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.jointEmpiricalExtreme n ω =
      vaart1998_extremePair S.empiricalGProcess S.maximumNormalized n ω :=
  S.jointEmpiricalExtreme_eq n ω

theorem joint_trimmed_extreme_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (n : ℕ) (ω : Ω) :
    S.jointTrimmedExtreme n ω =
      vaart1998_extremePair S.trimmedGProcess S.maximumNormalized n ω :=
  S.jointTrimmedExtreme_eq n ω

theorem joint_limit_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (ω : Ω') :
    S.jointLimit ω = (S.gaussianLimit ω, S.extremeLimit ω) :=
  S.jointLimit_eq ω

theorem joint_limit_cdf_product_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.jointLimitCdf =
      vaart1998_independentProductCdf S.normalCdf S.extremeLimitCdf :=
  S.jointLimitCdf_eq

theorem maximum_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    TendstoInDistribution S.maximumNormalized atTop S.extremeLimit
      (fun _ : ℕ => P) Q :=
  S.maximum_converges

theorem empirical_g_process_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    TendstoInDistribution S.empiricalGProcess atTop S.gaussianLimit
      (fun _ : ℕ => P) Q :=
  S.empiricalGProcess_converges

theorem limit_independence_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    _root_.ProbabilityTheory.IndepFun S.gaussianLimit S.extremeLimit Q :=
  S.limit_independence

theorem trimmed_joint_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    TendstoInDistribution S.jointTrimmedExtreme atTop S.jointLimit
      (fun _ : ℕ => P) Q :=
  S.trimmed_joint_converges

theorem joint_convergence
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    TendstoInDistribution S.jointEmpiricalExtreme atTop S.jointLimit
      (fun _ : ℕ => P) Q :=
  S.joint_converges

theorem max_g_contribution_negligible_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.max_g_contribution_negligible_statement :=
  S.max_g_contribution_negligible

theorem pair_distance_negligible_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.pair_distance_negligible_statement :=
  S.pair_distance_negligible

theorem conditional_cdf_display
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (n : ℕ) (u v : ℝ) :
    vaart1998_conditionalCdfGivenExtreme S.conditionalCdf n u v =
      S.conditionalCdf n u v :=
  S.conditionalCdf_display n u v

theorem conditional_cdf_converges_to_normal_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.conditional_cdf_converges_to_normal_statement :=
  S.conditional_cdf_converges_to_normal

theorem dominated_convergence_joint_cdf_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.dominated_convergence_joint_cdf_statement :=
  S.dominated_convergence_joint_cdf

theorem conditional_distribution_iid_clause
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.conditional_distribution_iid_source_statement :=
  S.conditional_distribution_iid_source

theorem conditional_abs_mean_bound
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q))
    (n : ℕ) (v : ℝ) :
    S.conditionalAbsMean n v ≤
      vaart1998_conditionalMeanTailBound S.tailSecondMoment S.survival S.cdf
        (vaart1998_extremeOrderThreshold S.center S.scale n v) :=
  S.conditionalAbsMean_bound n v

theorem tail_bound_from_lemma21_12_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.tail_bound_from_lemma21_12_statement :=
  S.tail_bound_from_lemma21_12

theorem sqrt_n_conditional_mean_tendsto_zero_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.sqrt_n_conditional_mean_tendsto_zero_statement :=
  S.sqrt_n_conditional_mean_tendsto_zero

theorem conditional_second_moment_tendsto_one_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.conditionalSecondMoment_tendsto_one_statement :=
  S.conditionalSecondMoment_tendsto_one

theorem conditional_lindeberg_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.conditional_lindeberg_statement :=
  S.conditional_lindeberg

theorem empirical_process_extreme_independence_source
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.empirical_process_extreme_independence_statement :=
  S.empirical_process_extreme_independence

theorem delta_method_central_order_statistic_clause
    {Ω Ω' : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [MeasurableSpace Ω'] {Q : Measure Ω'}
    [IsProbabilityMeasure Q]
    (S : Vaart1998Lemma21_19AsymptoticIndependenceSource
      (P := P) (Q := Q)) :
    S.delta_method_central_order_statistic_source_statement :=
  S.delta_method_central_order_statistic_source

end Vaart1998Lemma21_19AsymptoticIndependenceSource

end AsymptoticStatistics
end StatInference
