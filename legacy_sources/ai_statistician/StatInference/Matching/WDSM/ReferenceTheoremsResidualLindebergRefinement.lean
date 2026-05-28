import StatInference.Matching.WDSM.ReferenceTheorems
import StatInference.Matching.WDSM.ResidualMartingaleFiniteCellLindeberg

/-!
# Residual-Lindeberg refinements for WDSM reference-theorem routes

This module narrows the Chen-Han reference routes that use the explicit
residual martingale-array interface.  Instead of exposing a raw
`residual.conditional_lindeberg` premise, the wrappers below consume the
concrete two-arm WDSM Lindeberg conditions already proved from coefficient
envelopes or finite score-cell loadings.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Treated Control : Type*} {l : Filter Index}

/--
Chen-Han residual martingale reference bridge with the Lindeberg premise
discharged by concrete two-arm coefficient-envelope and third-moment bounds.
-/
theorem residual_clt_and_variance_formula_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridge
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hregular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    residual.residual_clt ∧ residual.residual_variance_formula := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry hregular hcatchment
  exact
    residual_clt_and_variance_formula_of_twoArm_envelope_lindeberg_bridge
      (l := l) treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      treatedEnvelope controlEnvelope residual hinputLindeberg
      (hmoment_transfer hreuse) hresidual_reg hmartingale hquad
      htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
      hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

/--
Known-score Chen-Han martingale reference route with the residual Lindeberg
premise discharged from concrete two-arm envelope bounds.
-/
theorem known_score_asymptotic_normality_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    known.asymptotic_normality := by
  have hresidual :
      residual.residual_clt ∧ residual.residual_variance_formula :=
    residual_clt_and_variance_formula_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridge
      (l := l) treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      treatedEnvelope controlEnvelope geometry residual hinputLindeberg
      hgeometry_regular hcatchment hmoment_transfer hresidual_reg hmartingale
      hquad htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
      hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound
  have hbias : bias.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_chen_han_radius_bridge radius bias
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
  exact known_score_asymptotic_normality_of_bridge known
    hdecomp hden hheterogeneity (hresidual_transfer hresidual.1)
    (hbias_transfer hbias)

/--
Known-score Chen-Han martingale reference route plus Chen-Han limiting variance,
with Lindeberg supplied by concrete two-arm envelope bounds.
-/
theorem known_score_asymptotic_normality_and_limiting_variance_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    known.asymptotic_normality ∧ geometry.limiting_variance_formula := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridges
      (l := l) treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      treatedEnvelope controlEnvelope geometry radius residual bias known
      hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
      hresidual_reg hmartingale hquad hresidual_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden hheterogeneity htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoeffBound hcontrolCoeffBound
      htreatedEnvelopeBound hcontrolEnvelopeBound
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry
      hgeometry_regular hcatchment
  exact ⟨hknown, chen_han_limiting_variance_of_bridge geometry hreuse⟩

/--
Known-score Chen-Han component-variance martingale reference route with the
Lindeberg premise discharged from concrete two-arm envelope bounds.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        variance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : variance.component_orthogonality)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_envelopes
        (l := l) treatedSample controlSample treatedWeight
        treatedCoefficient treatedResidual controlWeight controlCoefficient
        controlResidual treatedEnvelope controlEnvelope
        htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
        hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound)
  exact
    known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
      geometry radius heterogeneity residual bias known variance
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale
      hlindeberg hquad hresidual_transfer hresidual_variance_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden horthogonality

/--
Known-score Chen-Han design-cross-zero martingale reference route with the
Lindeberg premise discharged from concrete two-arm envelope bounds.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_design_cross_zero_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        variance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_envelopes
        (l := l) treatedSample controlSample treatedWeight
        treatedCoefficient treatedResidual controlWeight controlCoefficient
        controlResidual treatedEnvelope controlEnvelope
        htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
        hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound)
  exact
    known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges_design_cross_zero
      geometry radius heterogeneity residual bias known variance
      orthogonality hgeometry_regular hcatchment hmoment_transfer
      hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale
      hlindeberg hquad hresidual_transfer hresidual_variance_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hcross hlimit

/--
Estimated-score Chen-Han martingale reference route with the residual Lindeberg
premise discharged from concrete two-arm envelope bounds.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hadjustment : variance.score_adjustment_algebra)
    (hgodambe_variance : variance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_envelopes
        (l := l) treatedSample controlSample treatedWeight
        treatedCoefficient treatedResidual controlWeight controlCoefficient
        controlResidual treatedEnvelope controlEnvelope
        htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
        hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
      geometry radius residual bias known estimated variance
      hgeometry_regular hcatchment hmoment_transfer hresidual_reg
      hmartingale hlindeberg hquad hresidual_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden hheterogeneity hknown_transfer hfirst hlocal
      hgodambe_normality hknown_variance_transfer hadjustment
      hgodambe_variance

/--
Estimated-score Chen-Han local-experiment martingale reference route with the
residual Lindeberg premise discharged from concrete two-arm envelope bounds.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_envelopes
        (l := l) treatedSample controlSample treatedWeight
        treatedCoefficient treatedResidual controlWeight controlCoefficient
        controlResidual treatedEnvelope controlEnvelope
        htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
        hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges
      geometry radius residual bias known estimated hgeometry_regular
      hcatchment hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
      hresidual_transfer hradius_regular hradius_geometry hradius_transfer
      hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
      hknown_normality_transfer hknown_variance_transfer hfirst hscore
      hfunctional hequicontinuity hadjustment hgodambe

/--
Estimated-score Chen-Han component martingale reference route with the residual
Lindeberg premise discharged from concrete two-arm envelope bounds.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_envelopes
        (l := l) treatedSample controlSample treatedWeight
        treatedCoefficient treatedResidual controlWeight controlCoefficient
        controlResidual treatedEnvelope controlEnvelope
        htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
        hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges
      geometry radius heterogeneity residual bias known knownVariance estimated
      estimatedVariance hgeometry_regular hcatchment hmoment_transfer
      hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden horthogonality hknown_normality_transfer
      hknown_variance_transfer hfirst hlocal hgodambe_normality hadjustment
      hgodambe_variance

/--
Estimated-score Chen-Han component local-experiment martingale reference route
with the residual Lindeberg premise discharged from concrete two-arm envelope
bounds.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_envelopes
        (l := l) treatedSample controlSample treatedWeight
        treatedCoefficient treatedResidual controlWeight controlCoefficient
        controlResidual treatedEnvelope controlEnvelope
        htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
        hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges
      geometry radius heterogeneity residual bias known knownVariance estimated
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden horthogonality hknown_normality_transfer
      hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
      hadjustment hgodambe

/--
Estimated-score Chen-Han component design-cross-zero martingale reference route
with the residual Lindeberg premise discharged from concrete two-arm envelope
bounds.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_envelopes
        (l := l) treatedSample controlSample treatedWeight
        treatedCoefficient treatedResidual controlWeight controlCoefficient
        controlResidual treatedEnvelope controlEnvelope
        htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
        hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_design_cross_zero
      geometry radius heterogeneity residual bias known knownVariance
      orthogonality estimated estimatedVariance hgeometry_regular hcatchment
      hmoment_transfer hheterogeneity_moment hheterogeneity_variance
      hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
      hmartingale hlindeberg hquad hresidual_transfer
      hresidual_variance_transfer hradius_regular hradius_geometry
      hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
      hlimit hknown_normality_transfer hknown_variance_transfer hfirst hlocal
      hgodambe_normality hadjustment hgodambe_variance

/--
Estimated-score Chen-Han component design-cross-zero local-experiment martingale
reference route with the residual Lindeberg premise discharged from concrete
two-arm envelope bounds.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_bridges
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_envelopes
        (l := l) treatedSample controlSample treatedWeight
        treatedCoefficient treatedResidual controlWeight controlCoefficient
        controlResidual treatedEnvelope controlEnvelope
        htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
        hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero
      geometry radius heterogeneity residual bias known knownVariance
      orthogonality estimated hgeometry_regular hcatchment hmoment_transfer
      hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden hcross hlimit hknown_normality_transfer
      hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
      hadjustment hgodambe

variable {TreatedCell ControlCell : Type*}
  [DecidableEq TreatedCell] [DecidableEq ControlCell]

/--
Chen-Han residual martingale reference bridge with Lindeberg supplied by finite
score-cell coefficient loadings and residual third-moment control.
-/
theorem residual_clt_and_variance_formula_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridge
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hregular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    residual.residual_clt ∧ residual.residual_variance_formula := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry hregular hcatchment
  exact
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_bridge
      (l := l) treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual controlWeight
      controlCoefficient controlResidual treatedScore controlScore
      treatedCoefficientLoading controlCoefficientLoading
      treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
      controlMassLimit treatedEnvelope controlEnvelope residual
      hinputLindeberg (hmoment_transfer hreuse) hresidual_reg hmartingale
      hquad htreatedWeightNonneg hcontrolWeightNonneg
      htreatedCoverEventually hcontrolCoverEventually htreatedCover
      hcontrolCover htreatedCoefficient hcontrolCoefficient
      htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
      htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
      htreatedEnvelope hcontrolEnvelope

/--
Known-score Chen-Han martingale reference route with Lindeberg supplied by
finite score-cell coefficient loadings and residual third-moment control.
-/
theorem known_score_asymptotic_normality_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    known.asymptotic_normality := by
  have hresidual :
      residual.residual_clt ∧ residual.residual_variance_formula :=
    residual_clt_and_variance_formula_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridge
      (l := l) treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual controlWeight
      controlCoefficient controlResidual treatedScore controlScore
      treatedCoefficientLoading controlCoefficientLoading
      treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
      controlMassLimit treatedEnvelope controlEnvelope geometry residual
      hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
      hresidual_reg hmartingale hquad htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
      htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
      htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
      htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
      htreatedEnvelope hcontrolEnvelope
  have hbias : bias.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_chen_han_radius_bridge radius bias
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
  exact known_score_asymptotic_normality_of_bridge known
    hdecomp hden hheterogeneity (hresidual_transfer hresidual.1)
    (hbias_transfer hbias)

/--
Known-score Chen-Han martingale reference route plus Chen-Han limiting variance,
with Lindeberg supplied by finite score-cell coefficient loadings.
-/
theorem known_score_asymptotic_normality_and_limiting_variance_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    known.asymptotic_normality ∧ geometry.limiting_variance_formula := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridges
      (l := l) treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual controlWeight
      controlCoefficient controlResidual treatedScore controlScore
      treatedCoefficientLoading controlCoefficientLoading
      treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
      controlMassLimit treatedEnvelope controlEnvelope geometry radius
      residual bias known hinputLindeberg hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hheterogeneity htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
      htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
      htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
      htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
      htreatedEnvelope hcontrolEnvelope
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry
      hgeometry_regular hcatchment
  exact ⟨hknown, chen_han_limiting_variance_of_bridge geometry hreuse⟩

/--
Known-score Chen-Han component-variance martingale reference route with
Lindeberg supplied by finite score-cell coefficient loadings and residual
third-moment control.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        variance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : variance.component_orthogonality)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
        (l := l) treatedCells controlCells treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual controlWeight
        controlCoefficient controlResidual treatedScore controlScore
        treatedCoefficientLoading controlCoefficientLoading
        treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
        controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
        hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
        htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
        htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
        htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
        htreatedEnvelope hcontrolEnvelope)
  exact
    known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
      geometry radius heterogeneity residual bias known variance
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale
      hlindeberg hquad hresidual_transfer hresidual_variance_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden horthogonality

/--
Known-score Chen-Han design-cross-zero martingale reference route with
Lindeberg supplied by finite score-cell coefficient loadings and residual
third-moment control.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_design_cross_zero_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        variance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
        (l := l) treatedCells controlCells treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual controlWeight
        controlCoefficient controlResidual treatedScore controlScore
        treatedCoefficientLoading controlCoefficientLoading
        treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
        controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
        hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
        htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
        htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
        htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
        htreatedEnvelope hcontrolEnvelope)
  exact
    known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges_design_cross_zero
      geometry radius heterogeneity residual bias known variance
      orthogonality hgeometry_regular hcatchment hmoment_transfer
      hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale
      hlindeberg hquad hresidual_transfer hresidual_variance_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hcross hlimit

/--
Estimated-score Chen-Han martingale reference route with Lindeberg supplied by
finite score-cell coefficient loadings and residual third-moment control.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hadjustment : variance.score_adjustment_algebra)
    (hgodambe_variance : variance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
        (l := l) treatedCells controlCells treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual controlWeight
        controlCoefficient controlResidual treatedScore controlScore
        treatedCoefficientLoading controlCoefficientLoading
        treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
        controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
        hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
        htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
        htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
        htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
        htreatedEnvelope hcontrolEnvelope)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
      geometry radius residual bias known estimated variance
      hgeometry_regular hcatchment hmoment_transfer hresidual_reg
      hmartingale hlindeberg hquad hresidual_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden hheterogeneity hknown_transfer hfirst hlocal
      hgodambe_normality hknown_variance_transfer hadjustment
      hgodambe_variance

/--
Estimated-score Chen-Han local-experiment martingale reference route with
Lindeberg supplied by finite score-cell coefficient loadings and residual
third-moment control.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
        (l := l) treatedCells controlCells treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual controlWeight
        controlCoefficient controlResidual treatedScore controlScore
        treatedCoefficientLoading controlCoefficientLoading
        treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
        controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
        hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
        htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
        htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
        htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
        htreatedEnvelope hcontrolEnvelope)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges
      geometry radius residual bias known estimated hgeometry_regular
      hcatchment hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
      hresidual_transfer hradius_regular hradius_geometry hradius_transfer
      hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
      hknown_normality_transfer hknown_variance_transfer hfirst hscore
      hfunctional hequicontinuity hadjustment hgodambe

/--
Estimated-score Chen-Han component martingale reference route with Lindeberg
supplied by finite score-cell coefficient loadings and residual third-moment
control.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
        (l := l) treatedCells controlCells treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual controlWeight
        controlCoefficient controlResidual treatedScore controlScore
        treatedCoefficientLoading controlCoefficientLoading
        treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
        controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
        hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
        htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
        htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
        htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
        htreatedEnvelope hcontrolEnvelope)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges
      geometry radius heterogeneity residual bias known knownVariance estimated
      estimatedVariance hgeometry_regular hcatchment hmoment_transfer
      hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden horthogonality hknown_normality_transfer
      hknown_variance_transfer hfirst hlocal hgodambe_normality hadjustment
      hgodambe_variance

/--
Estimated-score Chen-Han component local-experiment martingale reference route
with Lindeberg supplied by finite score-cell coefficient loadings and residual
third-moment control.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
        (l := l) treatedCells controlCells treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual controlWeight
        controlCoefficient controlResidual treatedScore controlScore
        treatedCoefficientLoading controlCoefficientLoading
        treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
        controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
        hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
        htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
        htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
        htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
        htreatedEnvelope hcontrolEnvelope)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges
      geometry radius heterogeneity residual bias known knownVariance estimated
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden horthogonality hknown_normality_transfer
      hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
      hadjustment hgodambe

/--
Estimated-score Chen-Han component design-cross-zero martingale reference route
with Lindeberg supplied by finite score-cell coefficient loadings and residual
third-moment control.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
        (l := l) treatedCells controlCells treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual controlWeight
        controlCoefficient controlResidual treatedScore controlScore
        treatedCoefficientLoading controlCoefficientLoading
        treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
        controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
        hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
        htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
        htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
        htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
        htreatedEnvelope hcontrolEnvelope)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_design_cross_zero
      geometry radius heterogeneity residual bias known knownVariance
      orthogonality estimated estimatedVariance hgeometry_regular hcatchment
      hmoment_transfer hheterogeneity_moment hheterogeneity_variance
      hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
      hmartingale hlindeberg hquad hresidual_transfer
      hresidual_variance_transfer hradius_regular hradius_geometry
      hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
      hlimit hknown_normality_transfer hknown_variance_transfer hfirst hlocal
      hgodambe_normality hadjustment hgodambe_variance

/--
Estimated-score Chen-Han component design-cross-zero local-experiment martingale
reference route with Lindeberg supplied by finite score-cell coefficient
loadings and residual third-moment control.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_bridges
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hlindeberg : residual.conditional_lindeberg :=
    hinputLindeberg
      (twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
        (l := l) treatedCells controlCells treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual controlWeight
        controlCoefficient controlResidual treatedScore controlScore
        treatedCoefficientLoading controlCoefficientLoading
        treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
        controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
        hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
        htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
        htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
        htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
        htreatedEnvelope hcontrolEnvelope)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero
      geometry radius heterogeneity residual bias known knownVariance
      orthogonality estimated hgeometry_regular hcatchment hmoment_transfer
      hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hradius_regular
      hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
      hdecomp hden hcross hlimit hknown_normality_transfer
      hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
      hadjustment hgodambe

/--
Estimated-score Chen-Han local-experiment martingale reference route with the
residual Lindeberg premise discharged from concrete two-arm envelope bounds
and the local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius residual bias known
    estimated hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hresidual_reg hmartingale hquad hresidual_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

/--
Estimated-score Chen-Han local-experiment martingale reference route with
Lindeberg supplied by finite score-cell coefficient loadings and residual
third-moment control, and with the local-experiment/Godambe obligations
packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius residual
    bias known estimated hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

/--
Estimated-score Chen-Han component local-experiment martingale reference route
with the residual Lindeberg premise discharged from concrete two-arm envelope
bounds and the local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance estimated hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hquad hresidual_transfer hresidual_variance_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

/--
Estimated-score Chen-Han component local-experiment martingale reference route
with Lindeberg supplied by finite score-cell coefficient loadings and residual
third-moment control, and with the local-experiment/Godambe obligations
packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance estimated hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

/--
Estimated-score Chen-Han component design-cross-zero local-experiment
martingale reference route with the residual Lindeberg premise discharged from
concrete two-arm envelope bounds and the local-experiment/Godambe obligations
packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_bridges_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance orthogonality estimated hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

/--
Estimated-score Chen-Han component design-cross-zero local-experiment
martingale reference route with Lindeberg supplied by finite score-cell
coefficient loadings and residual third-moment control, and with the
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_bridges_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
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
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance orthogonality estimated
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

end WDSM
end Matching
end StatInference
