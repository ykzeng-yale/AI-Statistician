import StatInference.Matching.WDSM.AggregateDecomposition
import StatInference.Asymptotics.AsymptoticNormal

/-!
# Explicit asymptotic interfaces for WDSM

The WDSM paper's probability-limit and asymptotic-normality claims depend on
substantial external mathematics: nearest-neighbor score-space geometry,
weighted matching-frequency moment limits, martingale-array CLTs, denominator
stabilization, and estimated-score local-experiment expansions.  This module
does not pretend those ingredients are already proved.  It records the exact
bridge interfaces that later Lean work must replace with concrete
mathlib-backed probability statements.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Interface for importing or proving Chen-Han-style score-space geometry and the
weighted WDSM reuse-frequency moment limits derived from it.
-/
structure WeightedGeometryMomentBridge where
  score_space_regularity : Prop
  chen_han_catchment_input : Prop
  exact_weighted_reuse_moment_limits : Prop
  bridge :
    score_space_regularity ->
    chen_han_catchment_input ->
    exact_weighted_reuse_moment_limits

theorem exact_weighted_reuse_moments_of_geometry
    (b : WeightedGeometryMomentBridge)
    (hregular : b.score_space_regularity)
    (hchen_han : b.chen_han_catchment_input) :
    b.exact_weighted_reuse_moment_limits :=
  b.bridge hregular hchen_han

/--
Interface for the residual martingale-array CLT after the exact weighted reuse
moments have been established.
-/
structure ResidualArrayCLTBridge where
  exact_weighted_reuse_moment_limits : Prop
  residual_moment_regularity : Prop
  quadratic_variation_stabilization : Prop
  residual_clt : Prop
  bridge :
    exact_weighted_reuse_moment_limits ->
    residual_moment_regularity ->
    quadratic_variation_stabilization ->
    residual_clt

theorem residual_clt_of_reuse_moments
    (b : ResidualArrayCLTBridge)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hquad : b.quadratic_variation_stabilization) :
    b.residual_clt :=
  b.bridge hmoments hresidual hquad

/--
Residual-array bridge that records both the martingale-array CLT and the
limiting residual variance formula.  This separates the deterministic
quadratic-variation algebra from the remaining probability proof that the
quadratic variation stabilizes to the variance appearing in the CLT.
-/
structure ResidualArrayCLTVarianceBridge where
  exact_weighted_reuse_moment_limits : Prop
  residual_moment_regularity : Prop
  quadratic_variation_stabilization : Prop
  residual_clt : Prop
  residual_variance_formula : Prop
  bridge :
    exact_weighted_reuse_moment_limits ->
    residual_moment_regularity ->
    quadratic_variation_stabilization ->
    residual_clt ∧ residual_variance_formula

theorem residual_clt_and_variance_formula_of_reuse_moments
    (b : ResidualArrayCLTVarianceBridge)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hquad : b.quadratic_variation_stabilization) :
    b.residual_clt ∧ b.residual_variance_formula :=
  b.bridge hmoments hresidual hquad

theorem residual_clt_of_clt_variance_bridge
    (b : ResidualArrayCLTVarianceBridge)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hquad : b.quadratic_variation_stabilization) :
    b.residual_clt :=
  (residual_clt_and_variance_formula_of_reuse_moments b hmoments
    hresidual hquad).1

theorem residual_variance_formula_of_clt_variance_bridge
    (b : ResidualArrayCLTVarianceBridge)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hquad : b.quadratic_variation_stabilization) :
    b.residual_variance_formula :=
  (residual_clt_and_variance_formula_of_reuse_moments b hmoments
    hresidual hquad).2

/--
Heterogeneity bridge that records both the centered treatment-effect CLT and
its variance formula.  The finite square-target algebra is already verified in
`HeterogeneityVarianceAlgebra`; this interface names the remaining probability
step that identifies the limiting centered-effect variance.
-/
structure HeterogeneityCLTVarianceBridge where
  effect_moment_regularity : Prop
  centered_effect_variance_stabilization : Prop
  heterogeneity_clt : Prop
  heterogeneity_variance_formula : Prop
  bridge :
    effect_moment_regularity ->
    centered_effect_variance_stabilization ->
    heterogeneity_clt ∧ heterogeneity_variance_formula

theorem heterogeneity_clt_and_variance_formula_of_bridge
    (b : HeterogeneityCLTVarianceBridge)
    (hmoment : b.effect_moment_regularity)
    (hvariance : b.centered_effect_variance_stabilization) :
    b.heterogeneity_clt ∧ b.heterogeneity_variance_formula :=
  b.bridge hmoment hvariance

theorem heterogeneity_clt_of_clt_variance_bridge
    (b : HeterogeneityCLTVarianceBridge)
    (hmoment : b.effect_moment_regularity)
    (hvariance : b.centered_effect_variance_stabilization) :
    b.heterogeneity_clt :=
  (heterogeneity_clt_and_variance_formula_of_bridge b hmoment hvariance).1

theorem heterogeneity_variance_formula_of_clt_variance_bridge
    (b : HeterogeneityCLTVarianceBridge)
    (hmoment : b.effect_moment_regularity)
    (hvariance : b.centered_effect_variance_stabilization) :
    b.heterogeneity_variance_formula :=
  (heterogeneity_clt_and_variance_formula_of_bridge b hmoment hvariance).2

/--
Known-score variance formula bridge from the two component variance formulas.
The scalar algebra proving oracle variance additivity is in `VarianceAlgebra`;
this interface names the remaining probabilistic orthogonality/additivity
statement that combines heterogeneity and residual variance targets.
-/
structure KnownScoreVarianceFormulaBridge where
  heterogeneity_variance_formula : Prop
  residual_variance_formula : Prop
  component_orthogonality : Prop
  known_score_variance_formula : Prop
  bridge :
    heterogeneity_variance_formula ->
    residual_variance_formula ->
    component_orthogonality ->
    known_score_variance_formula

theorem known_score_variance_formula_of_component_variances
    (b : KnownScoreVarianceFormulaBridge)
    (hheterogeneity : b.heterogeneity_variance_formula)
    (hresidual : b.residual_variance_formula)
    (horthogonality : b.component_orthogonality) :
    b.known_score_variance_formula :=
  b.bridge hheterogeneity hresidual horthogonality

/--
Interface for the nearest-neighbor radius route to negligible matching
discrepancy.  The deterministic Lean theorem in `MatchingBiasRate` reduces
this to finite matching regularity, Lipschitz score-space means, and a scaled
survey-weighted average local radius rate.  The remaining probability work is
the actual nearest-neighbor geometry proof of that average-radius rate.
-/
structure AverageRadiusBiasBridge where
  eventual_finite_matching_regular : Prop
  lipschitz_score_mean_regular : Prop
  weighted_average_radius_rate : Prop
  matching_discrepancy_negligible : Prop
  bridge :
    eventual_finite_matching_regular ->
    lipschitz_score_mean_regular ->
    weighted_average_radius_rate ->
    matching_discrepancy_negligible

theorem matching_discrepancy_negligible_of_average_radius
    (b : AverageRadiusBiasBridge)
    (hfinite : b.eventual_finite_matching_regular)
    (hlipschitz : b.lipschitz_score_mean_regular)
    (hradius : b.weighted_average_radius_rate) :
    b.matching_discrepancy_negligible :=
  b.bridge hfinite hlipschitz hradius

/--
Known-score WDSM asymptotic-normality bridge.

This names the exact ingredients needed after the finite algebra has been
verified: the aggregate decomposition, denominator stabilization,
heterogeneity CLT, residual CLT, negligible matching discrepancy, and a
Slutsky/continuous-mapping step.
-/
structure KnownScoreAsymptoticBridge where
  aggregate_hajek_decomposition : Prop
  denominator_stabilization : Prop
  heterogeneity_clt : Prop
  residual_clt : Prop
  matching_discrepancy_negligible : Prop
  asymptotic_normality : Prop
  bridge :
    aggregate_hajek_decomposition ->
    denominator_stabilization ->
    heterogeneity_clt ->
    residual_clt ->
    matching_discrepancy_negligible ->
    asymptotic_normality

theorem known_score_asymptotic_normality_of_bridge
    (b : KnownScoreAsymptoticBridge)
    (hdecomp : b.aggregate_hajek_decomposition)
    (hden : b.denominator_stabilization)
    (hheterogeneity : b.heterogeneity_clt)
    (hresidual : b.residual_clt)
    (hbias : b.matching_discrepancy_negligible) :
    b.asymptotic_normality :=
  b.bridge hdecomp hden hheterogeneity hresidual hbias

/--
Composition of the current probability-layer interfaces for known-score WDSM
asymptotic normality.  Geometry supplies reuse-moment limits, those limits feed
the residual CLT bridge, the average-radius route supplies negligible matching
discrepancy, and the final known-score bridge combines these with denominator
and heterogeneity inputs.
-/
theorem known_score_asymptotic_normality_of_geometry_residual_and_average_radius
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt) :
    known.asymptotic_normality := by
  have hgeometry_moments :
      geometry.exact_weighted_reuse_moment_limits :=
    exact_weighted_reuse_moments_of_geometry geometry hregular hchen_han
  have hresidual_clt : residual.residual_clt :=
    residual_clt_of_reuse_moments residual
      (hmoment_transfer hgeometry_moments) hresidual_reg hquad
  have hbias : bias.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_average_radius bias
      hfinite hlipschitz hradius
  exact known_score_asymptotic_normality_of_bridge known
    hdecomp hden hheterogeneity
    (hresidual_transfer hresidual_clt)
    (hbias_transfer hbias)

/--
Known-score composition that carries the residual variance formula along with
the asymptotic-normality conclusion.  This uses the stronger residual
CLT/variance bridge, so the CLT input and the residual variance target stay
linked to the same quadratic-variation stabilization assumption.
-/
theorem known_score_asymptotic_normality_and_residual_variance_formula_of_geometry
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt) :
    known.asymptotic_normality ∧ residual.residual_variance_formula := by
  have hgeometry_moments :
      geometry.exact_weighted_reuse_moment_limits :=
    exact_weighted_reuse_moments_of_geometry geometry hregular hchen_han
  have hresidual_pair :
      residual.residual_clt ∧ residual.residual_variance_formula :=
    residual_clt_and_variance_formula_of_reuse_moments residual
      (hmoment_transfer hgeometry_moments) hresidual_reg hquad
  have hbias : bias.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_average_radius bias
      hfinite hlipschitz hradius
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge known
      hdecomp hden hheterogeneity
      (hresidual_transfer hresidual_pair.1)
      (hbias_transfer hbias)
  exact ⟨hknown, hresidual_pair.2⟩

/--
Known-score composition carrying both major variance component formulas.  The
heterogeneity bridge supplies the centered-effect CLT and variance formula,
the residual bridge supplies the residual CLT and variance formula, and the
known-score bridge consumes their CLT conclusions together with denominator
and bias inputs.
-/
theorem known_score_asymptotic_normality_and_component_variance_formulas_of_geometry
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization) :
    known.asymptotic_normality ∧
      heterogeneity.heterogeneity_variance_formula ∧
        residual.residual_variance_formula := by
  have hgeometry_moments :
      geometry.exact_weighted_reuse_moment_limits :=
    exact_weighted_reuse_moments_of_geometry geometry hregular hchen_han
  have hheterogeneity_pair :
      heterogeneity.heterogeneity_clt ∧
        heterogeneity.heterogeneity_variance_formula :=
    heterogeneity_clt_and_variance_formula_of_bridge heterogeneity
      hheterogeneity_moment hheterogeneity_variance
  have hresidual_pair :
      residual.residual_clt ∧ residual.residual_variance_formula :=
    residual_clt_and_variance_formula_of_reuse_moments residual
      (hmoment_transfer hgeometry_moments) hresidual_reg hquad
  have hbias : bias.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_average_radius bias
      hfinite hlipschitz hradius
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge known
      hdecomp hden
      (hheterogeneity_transfer hheterogeneity_pair.1)
      (hresidual_transfer hresidual_pair.1)
      (hbias_transfer hbias)
  exact ⟨hknown, hheterogeneity_pair.2, hresidual_pair.2⟩

/--
Known-score composition carrying the final known-score variance formula.  It
first obtains asymptotic normality and both component variance formulas, then
passes those component formulas through the known-score variance-formula bridge.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_geometry
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        variance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        variance.residual_variance_formula)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : variance.component_orthogonality) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula := by
  have hcomponents :=
    known_score_asymptotic_normality_and_component_variance_formulas_of_geometry
      geometry heterogeneity residual bias known hregular hchen_han
      hmoment_transfer hheterogeneity_moment hheterogeneity_variance
      hheterogeneity_transfer hresidual_reg hquad hresidual_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden
  have hvariance : variance.known_score_variance_formula :=
    known_score_variance_formula_of_component_variances variance
      (hheterogeneity_variance_transfer hcomponents.2.1)
      (hresidual_variance_transfer hcomponents.2.2)
      horthogonality
  exact ⟨hcomponents.1, hvariance⟩

/--
Estimated-score WDSM bridge.

This separates the known-score theorem from the additional non-smooth
first-step expansion and local-experiment/Godambe correction needed when the
matching score is estimated.
-/
structure EstimatedScoreAsymptoticBridge where
  known_score_asymptotic_normality : Prop
  first_step_asymptotic_linearization : Prop
  matching_functional_local_expansion : Prop
  godambe_variance_identity : Prop
  estimated_score_asymptotic_normality : Prop
  bridge :
    known_score_asymptotic_normality ->
    first_step_asymptotic_linearization ->
    matching_functional_local_expansion ->
    godambe_variance_identity ->
    estimated_score_asymptotic_normality

theorem estimated_score_asymptotic_normality_of_bridge
    (b : EstimatedScoreAsymptoticBridge)
    (hknown : b.known_score_asymptotic_normality)
    (hfirst : b.first_step_asymptotic_linearization)
    (hlocal : b.matching_functional_local_expansion)
    (hgodambe : b.godambe_variance_identity) :
    b.estimated_score_asymptotic_normality :=
  b.bridge hknown hfirst hlocal hgodambe

/--
Interface for the estimated-score limiting variance formula.  The deterministic
variance algebra proves the scalar and finite quadratic-form identities; this
bridge records the remaining probability/local-experiment step that connects a
known-score limiting variance formula with the Godambe correction.
-/
structure EstimatedScoreVarianceFormulaBridge where
  known_score_variance_formula : Prop
  score_adjustment_algebra : Prop
  godambe_variance_identity : Prop
  estimated_score_variance_formula : Prop
  bridge :
    known_score_variance_formula ->
    score_adjustment_algebra ->
    godambe_variance_identity ->
    estimated_score_variance_formula

theorem estimated_score_variance_formula_of_bridge
    (b : EstimatedScoreVarianceFormulaBridge)
    (hknown_variance : b.known_score_variance_formula)
    (hadjustment : b.score_adjustment_algebra)
    (hgodambe : b.godambe_variance_identity) :
    b.estimated_score_variance_formula :=
  b.bridge hknown_variance hadjustment hgodambe

/--
Full abstract WDSM estimated-score composition from the currently isolated
probability interfaces.  The known-score limit is obtained from the geometry,
residual CLT, and average-radius bias route, then passed through the
estimated-score local-expansion/Godambe bridge.
-/
theorem estimated_score_asymptotic_normality_of_geometry_residual_average_radius
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_geometry_residual_and_average_radius
      geometry residual bias known hregular hchen_han hmoment_transfer
      hresidual_reg hquad hresidual_transfer hfinite hlipschitz hradius
      hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_bridge estimated
    (hknown_transfer hknown) hfirst hlocal hgodambe

/--
Full abstract WDSM estimated-score composition carrying the estimated-score
variance formula from component variance formulas.  This is the bridge-shaped
statement matching the paper's final estimated-score limit and variance claim,
with all hard probability and local-expansion inputs still explicit.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hadjustment : estimatedVariance.score_adjustment_algebra)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hknown :=
    known_score_asymptotic_normality_and_variance_formula_of_geometry
      geometry heterogeneity residual bias known knownVariance hregular
      hchen_han hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
      hresidual_variance_transfer hfinite hlipschitz hradius hbias_transfer
      hdecomp hden horthogonality
  have hnormal : estimated.estimated_score_asymptotic_normality :=
    estimated_score_asymptotic_normality_of_bridge estimated
      (hknown_normality_transfer hknown.1) hfirst hlocal hgodambe_normality
  have hvariance :
      estimatedVariance.estimated_score_variance_formula :=
    estimated_score_variance_formula_of_bridge estimatedVariance
      (hknown_variance_transfer hknown.2) hadjustment hgodambe_variance
  exact ⟨hnormal, hvariance⟩

end WDSM
end Matching
end StatInference
