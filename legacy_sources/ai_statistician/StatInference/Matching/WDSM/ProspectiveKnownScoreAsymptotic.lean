import StatInference.Matching.WDSM.ProspectiveDecomposition
import StatInference.Matching.WDSM.AsymptoticInterfaces

/-!
# Prospective known-score asymptotic audit interfaces

This module records the audited boundary between the checked prospective
common-weight finite algebra and the stochastic inputs needed for known-score
asymptotic normality.  The finite side is represented by the prospective
specializations in `ProspectiveDecomposition`; denominator stabilization,
heterogeneity CLT, residual CLT, and radius-rate inputs remain explicit.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Scenario-specific audit bridge for prospective PATE known-score asymptotic
normality.
-/
structure ProspectivePATEKnownScoreAsymptoticBridge where
  exact_decomposition_verified : Prop
  deterministic_discrepancy_bound_verified : Prop
  bias_bridge : AverageRadiusBiasBridge
  known_score_bridge : KnownScoreAsymptoticBridge
  asymptotic_normality : Prop
  exact_decomposition_to_aggregate :
    exact_decomposition_verified ->
      known_score_bridge.aggregate_hajek_decomposition
  deterministic_bound_to_bias_regular :
    deterministic_discrepancy_bound_verified ->
      bias_bridge.lipschitz_score_mean_regular
  bias_to_known_score :
    bias_bridge.matching_discrepancy_negligible ->
      known_score_bridge.matching_discrepancy_negligible
  known_score_to_prospective_pate :
    known_score_bridge.asymptotic_normality -> asymptotic_normality

/--
Known-score asymptotic normality for prospective PATE from checked
common-weight finite algebra and explicit stochastic inputs.
-/
theorem prospective_pate_known_score_asymptotic_normality_of_audited_bridges
    (b : ProspectivePATEKnownScoreAsymptoticBridge)
    (hexact : b.exact_decomposition_verified)
    (hbias_bound : b.deterministic_discrepancy_bound_verified)
    (hfinite : b.bias_bridge.eventual_finite_matching_regular)
    (hradius : b.bias_bridge.weighted_average_radius_rate)
    (hden : b.known_score_bridge.denominator_stabilization)
    (hheterogeneity : b.known_score_bridge.heterogeneity_clt)
    (hresidual : b.known_score_bridge.residual_clt) :
    b.asymptotic_normality := by
  have hlipschitz : b.bias_bridge.lipschitz_score_mean_regular :=
    b.deterministic_bound_to_bias_regular hbias_bound
  have hbias : b.bias_bridge.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_average_radius b.bias_bridge hfinite
      hlipschitz hradius
  have hknown : b.known_score_bridge.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge b.known_score_bridge
      (b.exact_decomposition_to_aggregate hexact)
      hden hheterogeneity hresidual
      (b.bias_to_known_score hbias)
  exact b.known_score_to_prospective_pate hknown

/--
Scenario-specific audit bridge for prospective PATT known-score asymptotic
normality.
-/
structure ProspectivePATTKnownScoreAsymptoticBridge where
  exact_decomposition_verified : Prop
  deterministic_discrepancy_bound_verified : Prop
  bias_bridge : AverageRadiusBiasBridge
  known_score_bridge : KnownScoreAsymptoticBridge
  asymptotic_normality : Prop
  exact_decomposition_to_aggregate :
    exact_decomposition_verified ->
      known_score_bridge.aggregate_hajek_decomposition
  deterministic_bound_to_bias_regular :
    deterministic_discrepancy_bound_verified ->
      bias_bridge.lipschitz_score_mean_regular
  bias_to_known_score :
    bias_bridge.matching_discrepancy_negligible ->
      known_score_bridge.matching_discrepancy_negligible
  known_score_to_prospective_patt :
    known_score_bridge.asymptotic_normality -> asymptotic_normality

/--
Known-score asymptotic normality for prospective PATT from checked one-sided
common-weight finite algebra and explicit stochastic inputs.
-/
theorem prospective_patt_known_score_asymptotic_normality_of_audited_bridges
    (b : ProspectivePATTKnownScoreAsymptoticBridge)
    (hexact : b.exact_decomposition_verified)
    (hbias_bound : b.deterministic_discrepancy_bound_verified)
    (hfinite : b.bias_bridge.eventual_finite_matching_regular)
    (hradius : b.bias_bridge.weighted_average_radius_rate)
    (hden : b.known_score_bridge.denominator_stabilization)
    (hheterogeneity : b.known_score_bridge.heterogeneity_clt)
    (hresidual : b.known_score_bridge.residual_clt) :
    b.asymptotic_normality := by
  have hlipschitz : b.bias_bridge.lipschitz_score_mean_regular :=
    b.deterministic_bound_to_bias_regular hbias_bound
  have hbias : b.bias_bridge.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_average_radius b.bias_bridge hfinite
      hlipschitz hradius
  have hknown : b.known_score_bridge.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge b.known_score_bridge
      (b.exact_decomposition_to_aggregate hexact)
      hden hheterogeneity hresidual
      (b.bias_to_known_score hbias)
  exact b.known_score_to_prospective_patt hknown

/--
Paired known-score asymptotic normality for prospective PATE and PATT from
checked finite algebra and explicit stochastic inputs.
-/
theorem prospective_pate_patt_known_score_asymptotic_normality_of_audited_bridges
    (bpate : ProspectivePATEKnownScoreAsymptoticBridge)
    (bpatt : ProspectivePATTKnownScoreAsymptoticBridge)
    (hpate_exact : bpate.exact_decomposition_verified)
    (hpate_bias_bound : bpate.deterministic_discrepancy_bound_verified)
    (hpate_finite : bpate.bias_bridge.eventual_finite_matching_regular)
    (hpate_radius : bpate.bias_bridge.weighted_average_radius_rate)
    (hpate_den : bpate.known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity : bpate.known_score_bridge.heterogeneity_clt)
    (hpate_residual : bpate.known_score_bridge.residual_clt)
    (hpatt_exact : bpatt.exact_decomposition_verified)
    (hpatt_bias_bound : bpatt.deterministic_discrepancy_bound_verified)
    (hpatt_finite : bpatt.bias_bridge.eventual_finite_matching_regular)
    (hpatt_radius : bpatt.bias_bridge.weighted_average_radius_rate)
    (hpatt_den : bpatt.known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity : bpatt.known_score_bridge.heterogeneity_clt)
    (hpatt_residual : bpatt.known_score_bridge.residual_clt) :
    bpate.asymptotic_normality ∧ bpatt.asymptotic_normality := by
  constructor
  · exact prospective_pate_known_score_asymptotic_normality_of_audited_bridges
      bpate hpate_exact hpate_bias_bound hpate_finite hpate_radius
      hpate_den hpate_heterogeneity hpate_residual
  · exact prospective_patt_known_score_asymptotic_normality_of_audited_bridges
      bpatt hpatt_exact hpatt_bias_bound hpatt_finite hpatt_radius
      hpatt_den hpatt_heterogeneity hpatt_residual

end WDSM
end Matching
end StatInference
