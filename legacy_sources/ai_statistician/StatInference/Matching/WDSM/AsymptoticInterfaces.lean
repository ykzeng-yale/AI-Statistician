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
Forget the variance-formula part of a residual CLT/variance bridge.
-/
def residualArrayCLTBridgeOfCLTVarianceBridge
    (b : ResidualArrayCLTVarianceBridge) : ResidualArrayCLTBridge where
  exact_weighted_reuse_moment_limits := b.exact_weighted_reuse_moment_limits
  residual_moment_regularity := b.residual_moment_regularity
  quadratic_variation_stabilization := b.quadratic_variation_stabilization
  residual_clt := b.residual_clt
  bridge := by
    intro hmoments hresidual hquad
    exact (b.bridge hmoments hresidual hquad).1

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
Package an explicit martingale-array CLT input as the normality-only residual
CLT bridge once the martingale-difference and conditional Lindeberg conditions
have been supplied.
-/
def residualArrayCLTBridgeOfMartingaleArrayInput
    (b : ResidualMartingaleArrayCLTVarianceInput)
    (hmartingale : b.martingale_difference_array)
    (hlindeberg : b.conditional_lindeberg) :
    ResidualArrayCLTBridge :=
  residualArrayCLTBridgeOfCLTVarianceBridge
    (residualArrayCLTVarianceBridgeOfMartingaleArrayInput b hmartingale
      hlindeberg)

/--
Named interface for the external triangular martingale-array CLT itself.

This is the theorem boundary corresponding to the Billingsley/Hall-Heyde style
probability input used in the WDSM appendix: once the residual array is a
martingale-difference array, the conditional Lindeberg condition holds, and the
predictable quadratic variation stabilizes, the residual CLT and residual
variance formula follow.  The structure is intentionally separate from the
WDSM-specific reuse-moment and residual-regularity inputs, which are used to
prove these three martingale premises rather than to state the abstract CLT.
-/
structure TriangularMartingaleArrayCLTVarianceBridge where
  martingale_difference_array : Prop
  conditional_lindeberg : Prop
  predictable_quadratic_variation_stabilization : Prop
  residual_clt : Prop
  residual_variance_formula : Prop
  bridge :
    martingale_difference_array ->
    conditional_lindeberg ->
    predictable_quadratic_variation_stabilization ->
    residual_clt ∧ residual_variance_formula

theorem residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    (b : TriangularMartingaleArrayCLTVarianceBridge)
    (hmartingale : b.martingale_difference_array)
    (hlindeberg : b.conditional_lindeberg)
    (hqv : b.predictable_quadratic_variation_stabilization) :
    b.residual_clt ∧ b.residual_variance_formula :=
  b.bridge hmartingale hlindeberg hqv

theorem residual_clt_of_triangular_martingale_array_clt_bridge
    (b : TriangularMartingaleArrayCLTVarianceBridge)
    (hmartingale : b.martingale_difference_array)
    (hlindeberg : b.conditional_lindeberg)
    (hqv : b.predictable_quadratic_variation_stabilization) :
    b.residual_clt :=
  (residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    b hmartingale hlindeberg hqv).1

theorem residual_variance_formula_of_triangular_martingale_array_clt_bridge
    (b : TriangularMartingaleArrayCLTVarianceBridge)
    (hmartingale : b.martingale_difference_array)
    (hlindeberg : b.conditional_lindeberg)
    (hqv : b.predictable_quadratic_variation_stabilization) :
    b.residual_variance_formula :=
  (residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    b hmartingale hlindeberg hqv).2

/--
Package an external triangular martingale-array CLT as the WDSM residual input
once exact reuse-moment and residual-regularity propositions have been chosen.
Those two propositions remain explicit WDSM-side obligations, but the imported
CLT bridge itself consumes only the martingale-difference, conditional
Lindeberg, and predictable-QV premises.
-/
def residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (b : TriangularMartingaleArrayCLTVarianceBridge) :
    ResidualMartingaleArrayCLTVarianceInput where
  exact_weighted_reuse_moment_limits := exactWeightedReuseMomentLimits
  residual_moment_regularity := residualMomentRegularity
  martingale_difference_array := b.martingale_difference_array
  conditional_lindeberg := b.conditional_lindeberg
  predictable_quadratic_variation_stabilization :=
    b.predictable_quadratic_variation_stabilization
  residual_clt := b.residual_clt
  residual_variance_formula := b.residual_variance_formula
  martingale_clt_bridge := by
    intro _hmoments _hresidual hmartingale hlindeberg hqv
    exact b.bridge hmartingale hlindeberg hqv

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
Granular bridge for the known-score component-orthogonality input.

The population modules prove concrete residual/heterogeneity cross terms equal
zero.  The remaining probabilistic step is the transfer from those exact
population/design cross-zero facts to the asymptotic component-orthogonality
assumption consumed by the known-score variance formula.
-/
structure KnownScoreComponentOrthogonalityBridge
    (variance : KnownScoreVarianceFormulaBridge) where
  population_design_cross_terms_zero : Prop
  limiting_cross_covariance_zero : Prop
  bridge :
    population_design_cross_terms_zero ->
    limiting_cross_covariance_zero ->
    variance.component_orthogonality

theorem component_orthogonality_of_population_design_cross_zero
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero) :
    variance.component_orthogonality :=
  orthogonality.bridge hcross hlimit

/--
Known-score variance formula from component variances plus granular
cross-term-zero inputs.
-/
theorem known_score_variance_formula_of_component_variances_and_design_cross_zero
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
    (hheterogeneity : variance.heterogeneity_variance_formula)
    (hresidual : variance.residual_variance_formula)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero) :
    variance.known_score_variance_formula :=
  known_score_variance_formula_of_component_variances variance hheterogeneity
    hresidual
    (component_orthogonality_of_population_design_cross_zero variance
      orthogonality hcross hlimit)

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
Known-score composition using the explicit martingale-array residual CLT input,
returning only the asymptotic-normality conclusion.  The variance formula is
available from the stronger theorem below, but this theorem keeps normality-only
consumers from carrying an unused residual-variance conclusion.
-/
theorem known_score_asymptotic_normality_of_geometry_residual_and_average_radius_martingale_array
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
    known.asymptotic_normality :=
  known_score_asymptotic_normality_of_geometry_residual_and_average_radius
    geometry
    (residualArrayCLTBridgeOfMartingaleArrayInput residual hmartingale
      hlindeberg)
    bias known hregular hchen_han hmoment_transfer hresidual_reg hquad
    hresidual_transfer hfinite hlipschitz hradius hbias_transfer hdecomp
    hden hheterogeneity

/--
Known-score composition using the named triangular martingale-array CLT bridge
directly.  This is the normality-only downstream adapter for callers that have
already separated the WDSM-side reuse/residual regularity propositions from
the external martingale CLT theorem boundary.
-/
theorem known_score_asymptotic_normality_of_geometry_triangular_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt) :
    known.asymptotic_normality :=
  known_score_asymptotic_normality_of_geometry_residual_and_average_radius_martingale_array
    geometry
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known hregular hchen_han hmoment_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden hheterogeneity

/--
Known-score composition from the stronger residual CLT/variance bridge when
only the asymptotic-normality conclusion is needed.
-/
theorem known_score_asymptotic_normality_of_geometry_residual_variance_and_average_radius
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
    known.asymptotic_normality :=
  known_score_asymptotic_normality_of_geometry_residual_and_average_radius
    geometry (residualArrayCLTBridgeOfCLTVarianceBridge residual) bias known
    hregular hchen_han hmoment_transfer hresidual_reg hquad
    hresidual_transfer hfinite hlipschitz hradius hbias_transfer hdecomp
    hden hheterogeneity

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
Known-score composition carrying the residual variance formula when the
residual probability input is stated as the named triangular martingale-array
CLT bridge.
-/
theorem known_score_asymptotic_normality_and_residual_variance_formula_of_geometry_triangular_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt) :
    known.asymptotic_normality ∧ residualCLT.residual_variance_formula :=
  known_score_asymptotic_normality_and_residual_variance_formula_of_geometry_martingale_array
    geometry
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known hregular hchen_han hmoment_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden hheterogeneity

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
Known-score composition carrying the final variance formula when the
component-orthogonality input is supplied by granular population/design
cross-term-zero premises.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_geometry_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula :=
  known_score_asymptotic_normality_and_variance_formula_of_geometry
    geometry heterogeneity residual bias known variance hregular hchen_han
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hquad hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden
    (component_orthogonality_of_population_design_cross_zero variance
      orthogonality hcross hlimit)

/--
Known-score composition carrying both major variance component formulas when
the residual probability input is stated as an explicit martingale-array CLT.
This closes the interface route from Chen-Han-style reuse moments through
martingale-difference, conditional-Lindeberg, and predictable-quadratic-
variation assumptions before the known-score bridge consumes the residual CLT.
-/
theorem known_score_asymptotic_normality_and_component_variance_formulas_of_geometry_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
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
    residual_clt_and_variance_formula_of_martingale_array_input residual
      (hmoment_transfer hgeometry_moments) hresidual_reg hmartingale
      hlindeberg hquad
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
Known-score composition carrying the final known-score variance formula when
the residual CLT/variance input is supplied by the explicit martingale-array
interface.  The theorem keeps the component-orthogonality step separate from
the martingale-array probability obligations.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
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
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
    known_score_asymptotic_normality_and_component_variance_formulas_of_geometry_martingale_array
      geometry heterogeneity residual bias known hregular hchen_han
      hmoment_transfer hheterogeneity_moment hheterogeneity_variance
      hheterogeneity_transfer hresidual_reg hmartingale hlindeberg hquad
      hresidual_transfer hfinite hlipschitz hradius hbias_transfer hdecomp
      hden
  have hvariance : variance.known_score_variance_formula :=
    known_score_variance_formula_of_component_variances variance
      (hheterogeneity_variance_transfer hcomponents.2.1)
      (hresidual_variance_transfer hcomponents.2.2)
      horthogonality
  exact ⟨hcomponents.1, hvariance⟩

/--
Known-score composition carrying the final variance formula from the explicit
martingale-array residual input when component orthogonality is supplied by
granular population/design cross-term-zero premises.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
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
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula :=
  known_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
    geometry heterogeneity residual bias known variance hregular hchen_han
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer
    hresidual_variance_transfer hfinite hlipschitz hradius hbias_transfer
    hdecomp hden
    (component_orthogonality_of_population_design_cross_zero variance
      orthogonality hcross hlimit)

/--
Known-score composition carrying both major variance component formulas when
the residual probability input is the named triangular martingale-array CLT
bridge.  This is the component-variance analogue of the normality-only
triangular bridge adapter.
-/
theorem known_score_asymptotic_normality_and_component_variance_formulas_of_geometry_triangular_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
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
        residualCLT.residual_variance_formula :=
  known_score_asymptotic_normality_and_component_variance_formulas_of_geometry_martingale_array
    geometry heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known hregular hchen_han hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer hresidual_reg hmartingale
    hlindeberg hquad hresidual_transfer hfinite hlipschitz hradius
    hbias_transfer hdecomp hden

/--
Known-score composition carrying the final known-score variance formula when
the residual probability input is the named triangular martingale-array CLT
bridge.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_geometry_triangular_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        variance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
    known.asymptotic_normality ∧ variance.known_score_variance_formula :=
  known_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
    geometry heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known variance hregular hchen_han hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden horthogonality

/--
Known-score final variance formula from the named triangular
martingale-array CLT bridge when component orthogonality is supplied by
granular population/design cross-term-zero premises.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_geometry_triangular_martingale_array_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        variance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
        variance.residual_variance_formula)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula :=
  known_score_asymptotic_normality_and_variance_formula_of_geometry_triangular_martingale_array
    geometry heterogeneity residualCLT bias known variance
    exactWeightedReuseMomentLimits residualMomentRegularity hregular
    hchen_han hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden
    (component_orthogonality_of_population_design_cross_zero variance
      orthogonality hcross hlimit)

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
The remaining local-expansion and Godambe obligations for the older packaged
estimated-score asymptotic bridge, after the known-score and first-step inputs
are supplied separately.
-/
structure EstimatedScoreAsymptoticBridgeCore
    (b : EstimatedScoreAsymptoticBridge) where
  matching_functional_local_expansion :
    b.matching_functional_local_expansion
  godambe_variance_identity : b.godambe_variance_identity

/--
Estimated-score normality from the older packaged bridge with its local
expansion and Godambe obligations supplied by a compact core.
-/
theorem estimated_score_asymptotic_normality_of_bridge_core
    (b : EstimatedScoreAsymptoticBridge)
    (core : EstimatedScoreAsymptoticBridgeCore b)
    (hknown : b.known_score_asymptotic_normality)
    (hfirst : b.first_step_asymptotic_linearization) :
    b.estimated_score_asymptotic_normality :=
  estimated_score_asymptotic_normality_of_bridge b hknown hfirst
    core.matching_functional_local_expansion
    core.godambe_variance_identity

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
The remaining WDSM-specific local-experiment obligations after first-step and
score-estimator local-linearity evidence have been supplied.
-/
structure EstimatedScoreLocalExperimentCore
    (b : EstimatedScoreLocalExperimentInput) where
  matching_functional_local_derivative :
    b.matching_functional_local_derivative
  local_stochastic_equicontinuity : b.local_stochastic_equicontinuity
  godambe_variance_identity : b.godambe_variance_identity

/--
Estimated-score normality from first-step/score-local inputs plus the compact
WDSM-specific local-experiment core.
-/
theorem estimated_score_asymptotic_normality_of_local_experiment_core
    (b : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore b)
    (hknown : b.known_score_asymptotic_normality)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity) :
    b.estimated_score_asymptotic_normality :=
  estimated_score_asymptotic_normality_of_local_experiment_input b hknown
    hfirst hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_variance_identity

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
Estimated-score asymptotic normality alone from a combined local-experiment
and variance-formula input.
-/
theorem estimated_score_asymptotic_normality_of_local_experiment_variance_input
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (hknown : b.known_score_asymptotic_normality)
    (hknown_variance : b.known_score_variance_formula)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.matching_functional_local_derivative)
    (hequicontinuity : b.local_stochastic_equicontinuity)
    (hadjustment : b.score_adjustment_algebra)
    (hgodambe : b.godambe_identity) :
    b.estimated_score_asymptotic_normality :=
  (estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
    b hknown hknown_variance hfirst hscore hfunctional hequicontinuity
    hadjustment hgodambe).1

/--
Estimated-score variance formula alone from a combined local-experiment and
variance-formula input.
-/
theorem estimated_score_variance_formula_of_local_experiment_variance_input
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (hknown : b.known_score_asymptotic_normality)
    (hknown_variance : b.known_score_variance_formula)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.matching_functional_local_derivative)
    (hequicontinuity : b.local_stochastic_equicontinuity)
    (hadjustment : b.score_adjustment_algebra)
    (hgodambe : b.godambe_identity) :
    b.estimated_score_variance_formula :=
  (estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
    b hknown hknown_variance hfirst hscore hfunctional hequicontinuity
    hadjustment hgodambe).2

/--
The remaining WDSM-specific local-experiment/Godambe obligations for the
combined estimated-score normality and variance-formula input.

This deliberately does not include first-step linearization, score-estimator
local linearity, or finite score-adjustment algebra: those have separate
component/Z-estimator and finite quadratic-form refinement routes.
-/
structure EstimatedScoreLocalExperimentVarianceCore
    (b : EstimatedScoreLocalExperimentVarianceInput) where
  matching_functional_local_derivative :
    b.matching_functional_local_derivative
  local_stochastic_equicontinuity : b.local_stochastic_equicontinuity
  godambe_identity : b.godambe_identity

/--
Estimated-score normality alone from the compact combined local-experiment
core, first-step linearization, and score-estimator local linearity.
-/
theorem estimated_score_asymptotic_normality_of_local_experiment_variance_core
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore b)
    (hknown : b.known_score_asymptotic_normality)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity) :
    b.estimated_score_asymptotic_normality :=
  b.local_experiment_bridge hknown hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Estimated-score variance formula alone from the compact combined
local-experiment core and score-adjustment algebra.
-/
theorem estimated_score_variance_formula_of_local_experiment_variance_core
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore b)
    (hknown_variance : b.known_score_variance_formula)
    (hadjustment : b.score_adjustment_algebra) :
    b.estimated_score_variance_formula :=
  b.variance_formula_bridge hknown_variance hadjustment
    core.godambe_identity

/--
Estimated-score normality and variance formula from first-step/score-local
inputs, finite score-adjustment algebra, and the compact WDSM-specific
local-experiment core.
-/
theorem
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_core
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore b)
    (hknown : b.known_score_asymptotic_normality)
    (hknown_variance : b.known_score_variance_formula)
    (hfirst : b.first_step_asymptotic_linearization)
    (hscore : b.score_estimator_local_asymptotic_linearity)
    (hadjustment : b.score_adjustment_algebra) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  ⟨estimated_score_asymptotic_normality_of_local_experiment_variance_core
      b core hknown hfirst hscore,
    estimated_score_variance_formula_of_local_experiment_variance_core b core
      hknown_variance hadjustment⟩

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
Forget the variance-formula-specific packaging around a compact combined
local-experiment core.
-/
def estimatedScoreLocalExperimentCoreOfVarianceCore
    (b : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore b) :
    EstimatedScoreLocalExperimentCore
      (estimatedScoreLocalExperimentInputOfVarianceInput b) where
  matching_functional_local_derivative :=
    core.matching_functional_local_derivative
  local_stochastic_equicontinuity := core.local_stochastic_equicontinuity
  godambe_variance_identity := core.godambe_identity

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
Package separate local-experiment and variance-formula bridges into one
combined input, with the combined Godambe premise requiring both bridge-specific
Godambe identities.
-/
def estimatedScoreLocalExperimentVarianceInputOfLocalExperimentAndVarianceBridge
    (localInput : EstimatedScoreLocalExperimentInput)
    (variance : EstimatedScoreVarianceFormulaBridge) :
    EstimatedScoreLocalExperimentVarianceInput where
  known_score_asymptotic_normality :=
    localInput.known_score_asymptotic_normality
  known_score_variance_formula := variance.known_score_variance_formula
  first_step_asymptotic_linearization :=
    localInput.first_step_asymptotic_linearization
  score_estimator_local_asymptotic_linearity :=
    localInput.score_estimator_local_asymptotic_linearity
  matching_functional_local_derivative :=
    localInput.matching_functional_local_derivative
  local_stochastic_equicontinuity :=
    localInput.local_stochastic_equicontinuity
  score_adjustment_algebra := variance.score_adjustment_algebra
  godambe_identity :=
    localInput.godambe_variance_identity ∧ variance.godambe_variance_identity
  estimated_score_asymptotic_normality :=
    localInput.estimated_score_asymptotic_normality
  estimated_score_variance_formula :=
    variance.estimated_score_variance_formula
  local_experiment_bridge := by
    intro hknown hfirst hscore hfunctional hequicontinuity hgodambe
    exact localInput.local_experiment_bridge hknown hfirst hscore hfunctional
      hequicontinuity hgodambe.1
  variance_formula_bridge := by
    intro hknown_variance hadjustment hgodambe
    exact variance.bridge hknown_variance hadjustment hgodambe.2

/--
Package a combined local-experiment and variance-formula input as the broad
estimated-score asymptotic bridge.
-/
def estimatedScoreAsymptoticBridgeOfLocalExperimentVarianceInput
    (b : EstimatedScoreLocalExperimentVarianceInput) :
    EstimatedScoreAsymptoticBridge :=
  estimatedScoreAsymptoticBridgeOfLocalExperimentInput
    (estimatedScoreLocalExperimentInputOfVarianceInput b)

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
Estimated-score composition from the stronger residual CLT/variance bridge
when only the estimated-score normality conclusion is needed.
-/
theorem estimated_score_asymptotic_normality_of_geometry_residual_variance_average_radius
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualArrayCLTVarianceBridge)
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
    known_score_asymptotic_normality_of_geometry_residual_variance_and_average_radius
      geometry residual bias known hregular hchen_han hmoment_transfer
      hresidual_reg hquad hresidual_transfer hfinite hlipschitz hradius
      hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_bridge estimated
    (hknown_transfer hknown) hfirst hlocal hgodambe

/--
Estimated-score composition from the stronger residual CLT/variance bridge and
the explicit local-experiment input when only normality is needed.
-/
theorem estimated_score_asymptotic_normality_of_geometry_residual_variance_average_radius_local_experiment
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualArrayCLTVarianceBridge)
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
    known_score_asymptotic_normality_of_geometry_residual_variance_and_average_radius
      geometry residual bias known hregular hchen_han hmoment_transfer
      hresidual_reg hquad hresidual_transfer hfinite hlipschitz hradius
      hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_local_experiment_input
    estimated (hknown_transfer hknown) hfirst hscore hfunctional
    hequicontinuity hgodambe

/--
Estimated-score composition using the explicit residual martingale-array CLT
input.  This is the normality-only analogue of the variance-carrying
martingale-array route below.
-/
theorem estimated_score_asymptotic_normality_of_geometry_residual_average_radius_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
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
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hknown :=
    known_score_asymptotic_normality_and_residual_variance_formula_of_geometry_martingale_array
      geometry residual bias known hregular hchen_han hmoment_transfer
      hresidual_reg hmartingale hlindeberg hquad hresidual_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_bridge estimated
    (hknown_transfer hknown.1) hfirst hlocal hgodambe

/--
Estimated-score composition using both the explicit residual martingale-array
CLT input and the explicit local-experiment input.
-/
theorem estimated_score_asymptotic_normality_of_geometry_residual_average_radius_martingale_array_local_experiment
    (geometry : WeightedGeometryMomentBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentInput)
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
  have hknown :=
    known_score_asymptotic_normality_and_residual_variance_formula_of_geometry_martingale_array
      geometry residual bias known hregular hchen_han hmoment_transfer
      hresidual_reg hmartingale hlindeberg hquad hresidual_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_local_experiment_input
    estimated (hknown_transfer hknown.1) hfirst hscore hfunctional
    hequicontinuity hgodambe

/--
Estimated-score normality from the named triangular martingale-array CLT bridge.
This is the broad estimated-score bridge version.
-/
theorem estimated_score_asymptotic_normality_of_geometry_residual_average_radius_triangular_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
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
    estimated.estimated_score_asymptotic_normality :=
  estimated_score_asymptotic_normality_of_geometry_residual_average_radius_martingale_array
    geometry
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known estimated hregular hchen_han hmoment_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden hheterogeneity hknown_transfer
    hfirst hlocal hgodambe

/--
Estimated-score normality from the named triangular martingale-array CLT bridge
and the explicit local-experiment input.
-/
theorem estimated_score_asymptotic_normality_of_geometry_residual_average_radius_triangular_martingale_array_local_experiment
    (geometry : WeightedGeometryMomentBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentInput)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
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
    estimated.estimated_score_asymptotic_normality :=
  estimated_score_asymptotic_normality_of_geometry_residual_average_radius_martingale_array_local_experiment
    geometry
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known estimated hregular hchen_han hmoment_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden hheterogeneity hknown_transfer
    hfirst hscore hfunctional hequicontinuity hgodambe

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

/--
Estimated-score WDSM composition carrying the estimated-score variance formula
when the residual CLT/variance input is supplied by the explicit
martingale-array interface.  This is the broad estimated-score bridge version,
so the normality and variance formula may use separately named Godambe inputs.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
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
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
    known_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
      geometry heterogeneity residual bias known knownVariance hregular
      hchen_han hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden horthogonality
  have hnormal : estimated.estimated_score_asymptotic_normality :=
    estimated_score_asymptotic_normality_of_bridge estimated
      (hknown_normality_transfer hknown.1) hfirst hlocal hgodambe_normality
  have hvariance :
      estimatedVariance.estimated_score_variance_formula :=
    estimated_score_variance_formula_of_bridge estimatedVariance
      (hknown_variance_transfer hknown.2) hadjustment hgodambe_variance
  exact ⟨hnormal, hvariance⟩

/--
Final estimated-score WDSM composition using both the explicit residual
martingale-array CLT/variance input and the explicit combined local-experiment
variance input.  This is the most explicit current interface route to the
paper-level estimated-score normality plus variance formula conclusion.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_local_experiment
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
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
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
    known_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
      geometry heterogeneity residual bias known knownVariance hregular
      hchen_han hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden horthogonality
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated (hknown_normality_transfer hknown.1)
      (hknown_variance_transfer hknown.2) hfirst hscore hfunctional
      hequicontinuity hadjustment hgodambe

/--
Estimated-score normality and variance formula from the named triangular
martingale-array CLT bridge.  This is the broad estimated-score bridge version,
so normality and variance may use separately named Godambe inputs.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_triangular_martingale_array
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
    geometry heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known knownVariance estimated estimatedVariance hregular hchen_han
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer
    hresidual_variance_transfer hfinite hlipschitz hradius hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality hadjustment
    hgodambe_variance

/--
Estimated-score normality and variance formula from the named triangular
martingale-array CLT bridge and the explicit local-experiment variance input.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_triangular_martingale_array_local_experiment
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_local_experiment
    geometry heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known knownVariance estimated hregular hchen_han hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden horthogonality
    hknown_normality_transfer hknown_variance_transfer hfirst hscore
    hfunctional hequicontinuity hadjustment hgodambe

/--
Estimated-score WDSM normality and variance formula from the granular
population/design cross-term-zero component-orthogonality route.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
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
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_geometry
    geometry heterogeneity residual bias known knownVariance estimated
    estimatedVariance hregular hchen_han hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hfinite hlipschitz hradius hbias_transfer
    hdecomp hden
    (component_orthogonality_of_population_design_cross_zero knownVariance
      orthogonality hcross hlimit)
    hknown_normality_transfer hknown_variance_transfer hfirst hlocal
    hgodambe_normality hadjustment hgodambe_variance

/--
Estimated-score WDSM normality and variance formula from the granular
population/design cross-term-zero route and the explicit local-experiment
variance input.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_local_experiment_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
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
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_geometry_local_experiment
    geometry heterogeneity residual bias known knownVariance estimated
    hregular hchen_han hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hfinite hlipschitz hradius hbias_transfer
    hdecomp hden
    (component_orthogonality_of_population_design_cross_zero knownVariance
      orthogonality hcross hlimit)
    hknown_normality_transfer hknown_variance_transfer hfirst hscore
    hfunctional hequicontinuity hadjustment hgodambe

/--
Estimated-score WDSM normality and variance formula from the explicit
martingale-array residual input and granular population/design cross-term-zero
orthogonality route.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
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
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
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
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
    geometry heterogeneity residual bias known knownVariance estimated
    estimatedVariance hregular hchen_han hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden
    (component_orthogonality_of_population_design_cross_zero knownVariance
      orthogonality hcross hlimit)
    hknown_normality_transfer hknown_variance_transfer hfirst hlocal
    hgodambe_normality hadjustment hgodambe_variance

/--
Estimated-score WDSM normality and variance formula from the explicit
martingale-array residual input, explicit local-experiment variance input, and
granular population/design cross-term-zero orthogonality route.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_local_experiment_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
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
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
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
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_local_experiment
    geometry heterogeneity residual bias known knownVariance estimated
    hregular hchen_han hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden
    (component_orthogonality_of_population_design_cross_zero knownVariance
      orthogonality hcross hlimit)
    hknown_normality_transfer hknown_variance_transfer hfirst hscore
    hfunctional hequicontinuity hadjustment hgodambe

/--
Estimated-score normality and variance formula from the named triangular
martingale-array CLT bridge and the granular population/design cross-term-zero
orthogonality route.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_triangular_martingale_array_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
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
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_design_cross_zero
    geometry heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known knownVariance orthogonality estimated estimatedVariance
    hregular hchen_han hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
    hradius hbias_transfer hdecomp hden hcross hlimit
    hknown_normality_transfer hknown_variance_transfer hfirst hlocal
    hgodambe_normality hadjustment hgodambe_variance

/--
Estimated-score normality and variance formula from the named triangular
martingale-array CLT bridge, explicit local-experiment variance input, and
granular population/design cross-term-zero orthogonality route.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_geometry_triangular_martingale_array_local_experiment_design_cross_zero
    (geometry : WeightedGeometryMomentBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_space_regularity)
    (hchen_han : geometry.chen_han_catchment_input)
    (hmoment_transfer :
      geometry.exact_weighted_reuse_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hradius : bias.weighted_average_radius_rate)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
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
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_local_experiment_design_cross_zero
    geometry heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known knownVariance orthogonality estimated hregular hchen_han
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer
    hresidual_variance_transfer hfinite hlipschitz hradius hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    hadjustment hgodambe

end WDSM
end Matching
end StatInference
