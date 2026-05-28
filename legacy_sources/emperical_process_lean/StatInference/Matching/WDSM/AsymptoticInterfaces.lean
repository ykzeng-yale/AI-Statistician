import StatInference.Matching.WDSM.AggregateDecomposition

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
More explicit martingale-array residual CLT input.

This is still a named probability-layer interface, not a local proof of the
martingale CLT.  It splits the previous broad residual CLT bridge into the
ingredients that the WDSM proof has to port or prove: exact reuse-moment
limits, residual moment regularity, a martingale-difference array, conditional
Lindeberg control, and predictable quadratic-variation stabilization.
-/
structure ResidualMartingaleArrayCLTVarianceInput where
  exact_weighted_reuse_moment_limits : Prop
  residual_moment_regularity : Prop
  martingale_difference_array : Prop
  conditional_lindeberg : Prop
  predictable_quadratic_variation_stabilization : Prop
  residual_clt : Prop
  residual_variance_formula : Prop
  martingale_clt_bridge :
    exact_weighted_reuse_moment_limits ->
    residual_moment_regularity ->
    martingale_difference_array ->
    conditional_lindeberg ->
    predictable_quadratic_variation_stabilization ->
    residual_clt ∧ residual_variance_formula

theorem residual_clt_and_variance_formula_of_martingale_array_input
    (b : ResidualMartingaleArrayCLTVarianceInput)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hmartingale : b.martingale_difference_array)
    (hlindeberg : b.conditional_lindeberg)
    (hquad : b.predictable_quadratic_variation_stabilization) :
    b.residual_clt ∧ b.residual_variance_formula :=
  b.martingale_clt_bridge hmoments hresidual hmartingale hlindeberg hquad

theorem residual_clt_of_martingale_array_input
    (b : ResidualMartingaleArrayCLTVarianceInput)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hmartingale : b.martingale_difference_array)
    (hlindeberg : b.conditional_lindeberg)
    (hquad : b.predictable_quadratic_variation_stabilization) :
    b.residual_clt :=
  (residual_clt_and_variance_formula_of_martingale_array_input b hmoments
    hresidual hmartingale hlindeberg hquad).1

theorem residual_variance_formula_of_martingale_array_input
    (b : ResidualMartingaleArrayCLTVarianceInput)
    (hmoments : b.exact_weighted_reuse_moment_limits)
    (hresidual : b.residual_moment_regularity)
    (hmartingale : b.martingale_difference_array)
    (hlindeberg : b.conditional_lindeberg)
    (hquad : b.predictable_quadratic_variation_stabilization) :
    b.residual_variance_formula :=
  (residual_clt_and_variance_formula_of_martingale_array_input b hmoments
    hresidual hmartingale hlindeberg hquad).2

/--
Package an explicit martingale-array CLT input as the existing residual
CLT/variance bridge once the martingale-difference and conditional Lindeberg
conditions have been supplied.
-/
def residualArrayCLTVarianceBridgeOfMartingaleArrayInput
    (b : ResidualMartingaleArrayCLTVarianceInput)
    (hmartingale : b.martingale_difference_array)
    (hlindeberg : b.conditional_lindeberg) :
    ResidualArrayCLTVarianceBridge where
  exact_weighted_reuse_moment_limits := b.exact_weighted_reuse_moment_limits
  residual_moment_regularity := b.residual_moment_regularity
  quadratic_variation_stabilization :=
    b.predictable_quadratic_variation_stabilization
  residual_clt := b.residual_clt
  residual_variance_formula := b.residual_variance_formula
  bridge := by
    intro hmoments hresidual hquad
    exact b.martingale_clt_bridge hmoments hresidual hmartingale
      hlindeberg hquad

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
Known-score composition using the explicit martingale-array residual CLT input.
This theorem exposes the probability obligations for the residual term as
martingale-difference, conditional Lindeberg, and predictable
quadratic-variation hypotheses before feeding them into the existing
known-score asymptotic-normality bridge.
-/
theorem known_score_asymptotic_normality_and_residual_variance_formula_of_geometry_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
    residual_clt_and_variance_formula_of_martingale_array_input residual
      (hmoment_transfer hgeometry_moments) hresidual_reg hmartingale
      hlindeberg hquad
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
More explicit estimated-score local-experiment input.

This is a named probability/local-asymptotic interface, not a local proof of
the nonsmooth matching expansion.  It separates the broad
`matching_functional_local_expansion` premise into the score-estimator local
linearity, the matching-functional local derivative/expansion, and stochastic
equicontinuity of the local matching process.
-/
structure EstimatedScoreLocalExperimentInput where
  known_score_asymptotic_normality : Prop
  first_step_asymptotic_linearization : Prop
  score_estimator_local_asymptotic_linearity : Prop
  matching_functional_local_derivative : Prop
  local_stochastic_equicontinuity : Prop
  godambe_variance_identity : Prop
  estimated_score_asymptotic_normality : Prop
  local_experiment_bridge :
    known_score_asymptotic_normality ->
    first_step_asymptotic_linearization ->
    score_estimator_local_asymptotic_linearity ->
    matching_functional_local_derivative ->
    local_stochastic_equicontinuity ->
    godambe_variance_identity ->
    estimated_score_asymptotic_normality

theorem estimated_score_asymptotic_normality_of_local_experiment_input
    (b : EstimatedScoreLocalExperimentInput)
    (hknown : b.known_score_asymptotic_normality)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore :
      b.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.matching_functional_local_derivative)
    (hequicontinuity : b.local_stochastic_equicontinuity)
    (hgodambe : b.godambe_variance_identity) :
    b.estimated_score_asymptotic_normality :=
  b.local_experiment_bridge hknown hfirst hscore hfunctional
    hequicontinuity hgodambe

/--
Package an explicit local-experiment input as the existing estimated-score
asymptotic bridge.  The broad local-expansion premise in the packaged bridge
is the conjunction of score-estimator local linearity, matching-functional
local derivative, and local stochastic equicontinuity.
-/
def estimatedScoreAsymptoticBridgeOfLocalExperimentInput
    (b : EstimatedScoreLocalExperimentInput) :
    EstimatedScoreAsymptoticBridge where
  known_score_asymptotic_normality := b.known_score_asymptotic_normality
  first_step_asymptotic_linearization :=
    b.first_step_asymptotic_linearization
  matching_functional_local_expansion :=
    b.score_estimator_local_asymptotic_linearity ∧
      b.matching_functional_local_derivative ∧
        b.local_stochastic_equicontinuity
  godambe_variance_identity := b.godambe_variance_identity
  estimated_score_asymptotic_normality :=
    b.estimated_score_asymptotic_normality
  bridge := by
    intro hknown hfirst hlocal hgodambe
    exact b.local_experiment_bridge hknown hfirst hlocal.1 hlocal.2.1
      hlocal.2.2 hgodambe

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
Combined estimated-score local-experiment and variance-formula input.

This interface ties the final estimated-score asymptotic normality and
estimated-score variance formula to one local experiment and one Godambe
identity.  It is useful for the paper's final theorem because the normality
statement and variance statement should not silently use unrelated Godambe
premises.
-/
structure EstimatedScoreLocalExperimentVarianceInput where
  known_score_asymptotic_normality : Prop
  known_score_variance_formula : Prop
  first_step_asymptotic_linearization : Prop
  score_estimator_local_asymptotic_linearity : Prop
  matching_functional_local_derivative : Prop
  local_stochastic_equicontinuity : Prop
  score_adjustment_algebra : Prop
  godambe_identity : Prop
  estimated_score_asymptotic_normality : Prop
  estimated_score_variance_formula : Prop
  local_experiment_bridge :
    known_score_asymptotic_normality ->
    first_step_asymptotic_linearization ->
    score_estimator_local_asymptotic_linearity ->
    matching_functional_local_derivative ->
    local_stochastic_equicontinuity ->
    godambe_identity ->
    estimated_score_asymptotic_normality
  variance_formula_bridge :
    known_score_variance_formula ->
    score_adjustment_algebra ->
    godambe_identity ->
    estimated_score_variance_formula

theorem estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (hknown : b.known_score_asymptotic_normality)
    (hknown_variance : b.known_score_variance_formula)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.matching_functional_local_derivative)
    (hequicontinuity : b.local_stochastic_equicontinuity)
    (hadjustment : b.score_adjustment_algebra)
    (hgodambe : b.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  ⟨b.local_experiment_bridge hknown hfirst hscore hfunctional
      hequicontinuity hgodambe,
    b.variance_formula_bridge hknown_variance hadjustment hgodambe⟩

/--
Forget the variance-formula part of a combined estimated-score local experiment.
-/
def estimatedScoreLocalExperimentInputOfVarianceInput
    (b : EstimatedScoreLocalExperimentVarianceInput) :
    EstimatedScoreLocalExperimentInput where
  known_score_asymptotic_normality := b.known_score_asymptotic_normality
  first_step_asymptotic_linearization :=
    b.first_step_asymptotic_linearization
  score_estimator_local_asymptotic_linearity :=
    b.score_estimator_local_asymptotic_linearity
  matching_functional_local_derivative :=
    b.matching_functional_local_derivative
  local_stochastic_equicontinuity := b.local_stochastic_equicontinuity
  godambe_variance_identity := b.godambe_identity
  estimated_score_asymptotic_normality :=
    b.estimated_score_asymptotic_normality
  local_experiment_bridge := b.local_experiment_bridge

/--
Forget the normality part of a combined estimated-score local experiment.
-/
def estimatedScoreVarianceFormulaBridgeOfLocalExperimentVarianceInput
    (b : EstimatedScoreLocalExperimentVarianceInput) :
    EstimatedScoreVarianceFormulaBridge where
  known_score_variance_formula := b.known_score_variance_formula
  score_adjustment_algebra := b.score_adjustment_algebra
  godambe_variance_identity := b.godambe_identity
  estimated_score_variance_formula := b.estimated_score_variance_formula
  bridge := b.variance_formula_bridge

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
Estimated-score composition using the explicit local-experiment input.  This
theorem exposes the estimated-score probability/local-asymptotic obligations as
first-step linearization, score-estimator local linearity,
matching-functional local derivative, local stochastic equicontinuity, and the
Godambe identity.
-/
theorem estimated_score_asymptotic_normality_of_geometry_residual_average_radius_local_experiment
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentInput)
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
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_geometry_residual_and_average_radius
      geometry residual bias known hregular hchen_han hmoment_transfer
      hresidual_reg hquad hresidual_transfer hfinite hlipschitz hradius
      hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_local_experiment_input
    estimated (hknown_transfer hknown) hfirst hscore hfunctional
    hequicontinuity hgodambe

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

/--
Final estimated-score WDSM composition using the explicit combined
local-experiment and variance-formula input.  Compared with
`estimated_score_asymptotic_normality_and_variance_formula_of_geometry`, this
version exposes score-estimator local linearity, matching-functional local
derivative, stochastic equicontinuity, score-adjustment algebra, and one shared
Godambe identity directly.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_local_experiment
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
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
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hknown :=
    known_score_asymptotic_normality_and_variance_formula_of_geometry
      geometry heterogeneity residual bias known knownVariance hregular
      hchen_han hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
      hresidual_variance_transfer hfinite hlipschitz hradius hbias_transfer
      hdecomp hden horthogonality
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated (hknown_normality_transfer hknown.1)
      (hknown_variance_transfer hknown.2) hfirst hscore hfunctional
      hequicontinuity hadjustment hgodambe

end WDSM
end Matching
end StatInference
