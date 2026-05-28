import StatInference.Matching.WDSM.RetrospectivePATEBiasBound
import StatInference.Matching.WDSM.AsymptoticInterfaces

/-!
# Retrospective PATE known-score asymptotic interface

This module records the audited boundary between the checked finite
retrospective PATE algebra and the probability inputs needed for known-score
asymptotic normality.

The finite side is represented by:

* `retrospectivePATE_hajek_exact_decomposition_corrected_sign`;
* `abs_retrospectivePATEDiscrepancy_average_le_lipschitz_radius_average`.

The stochastic side remains explicit: denominator stabilization,
heterogeneity CLT, residual CLT, and weighted average radius rate are named
assumptions supplied through the existing asymptotic bridges.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Scenario-specific audit bridge for retrospective PATE known-score asymptotic
normality.

The two finite-algebra fields are intentionally separate from the stochastic
inputs.  They document that the exact decomposition and deterministic
Lipschitz/radius bias bound have been checked before the proof delegates to
the probability-layer bridge.
-/
structure RetrospectivePATEKnownScoreAsymptoticBridge where
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
  known_score_to_retrospective_pate :
    known_score_bridge.asymptotic_normality -> asymptotic_normality

/--
Known-score asymptotic normality for retrospective PATE from audited finite
algebra and explicit stochastic inputs.
-/
theorem retrospective_pate_known_score_asymptotic_normality_of_audited_bridges
    (b : RetrospectivePATEKnownScoreAsymptoticBridge)
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
  exact b.known_score_to_retrospective_pate hknown

end WDSM
end Matching
end StatInference
