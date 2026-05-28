import StatInference.Matching.WDSM.BootstrapLinearizedReplicate

/-!
# Bootstrap variance-consistency audit bridge

This module names the probability layer behind the WDSM linearization-based
bootstrap variance estimator.  The finite replicate algebra is checked in
`BootstrapLinearizedReplicate`; the remaining statements are explicit
regularity inputs rather than hidden assumptions.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Generic variance-consistency bridge for a WDSM linearized bootstrap estimator.

The fields split the proof obligations that the manuscript invokes:
linearized-replicate algebra, multiplier regularity, score-replication
consistency, bootstrap bias-correction consistency, and conditional variance
convergence.
-/
structure LinearizedBootstrapVarianceConsistencyBridge where
  linearized_replicate_algebra_verified : Prop
  multiplier_weight_regular : Prop
  bootstrap_score_replication_consistent : Prop
  bootstrap_bias_correction_consistent : Prop
  conditional_variance_convergence : Prop
  bootstrap_variance_consistent : Prop
  bridge :
    linearized_replicate_algebra_verified ->
    multiplier_weight_regular ->
    bootstrap_score_replication_consistent ->
    bootstrap_bias_correction_consistent ->
    conditional_variance_convergence ->
    bootstrap_variance_consistent

/-- Generic linearized bootstrap variance consistency from explicit inputs. -/
theorem bootstrap_variance_consistency_of_linearized_bridge
    (b : LinearizedBootstrapVarianceConsistencyBridge)
    (halgebra : b.linearized_replicate_algebra_verified)
    (hmultiplier : b.multiplier_weight_regular)
    (hscore : b.bootstrap_score_replication_consistent)
    (hbias : b.bootstrap_bias_correction_consistent)
    (hvariance : b.conditional_variance_convergence) :
    b.bootstrap_variance_consistent :=
  b.bridge halgebra hmultiplier hscore hbias hvariance

/--
Retrospective PATE bootstrap variance audit bridge.  The transfer field records
that the generic bootstrap variance conclusion is the manuscript's PATE
variance-estimator consistency claim.
-/
structure RetrospectivePATEBootstrapVarianceAuditBridge where
  bootstrap_bridge : LinearizedBootstrapVarianceConsistencyBridge
  bootstrap_variance_consistent : Prop
  bootstrap_to_retrospective_pate :
    bootstrap_bridge.bootstrap_variance_consistent ->
      bootstrap_variance_consistent

/-- Retrospective PATE bootstrap variance consistency from the audited bridge. -/
theorem retrospective_pate_bootstrap_variance_consistency_of_linearized_audit
    (b : RetrospectivePATEBootstrapVarianceAuditBridge)
    (halgebra :
      b.bootstrap_bridge.linearized_replicate_algebra_verified)
    (hmultiplier : b.bootstrap_bridge.multiplier_weight_regular)
    (hscore :
      b.bootstrap_bridge.bootstrap_score_replication_consistent)
    (hbias :
      b.bootstrap_bridge.bootstrap_bias_correction_consistent)
    (hvariance : b.bootstrap_bridge.conditional_variance_convergence) :
    b.bootstrap_variance_consistent := by
  exact b.bootstrap_to_retrospective_pate
    (bootstrap_variance_consistency_of_linearized_bridge
      b.bootstrap_bridge halgebra hmultiplier hscore hbias hvariance)

/--
Retrospective PATT bootstrap variance audit bridge.  The transfer field records
that the generic bootstrap variance conclusion is the manuscript's PATT
variance-estimator consistency claim.
-/
structure RetrospectivePATTBootstrapVarianceAuditBridge where
  bootstrap_bridge : LinearizedBootstrapVarianceConsistencyBridge
  bootstrap_variance_consistent : Prop
  bootstrap_to_retrospective_patt :
    bootstrap_bridge.bootstrap_variance_consistent ->
      bootstrap_variance_consistent

/-- Retrospective PATT bootstrap variance consistency from the audited bridge. -/
theorem retrospective_patt_bootstrap_variance_consistency_of_linearized_audit
    (b : RetrospectivePATTBootstrapVarianceAuditBridge)
    (halgebra :
      b.bootstrap_bridge.linearized_replicate_algebra_verified)
    (hmultiplier : b.bootstrap_bridge.multiplier_weight_regular)
    (hscore :
      b.bootstrap_bridge.bootstrap_score_replication_consistent)
    (hbias :
      b.bootstrap_bridge.bootstrap_bias_correction_consistent)
    (hvariance : b.bootstrap_bridge.conditional_variance_convergence) :
    b.bootstrap_variance_consistent := by
  exact b.bootstrap_to_retrospective_patt
    (bootstrap_variance_consistency_of_linearized_bridge
      b.bootstrap_bridge halgebra hmultiplier hscore hbias hvariance)

/--
Paired retrospective PATE/PATT bootstrap variance consistency from audited
linearized bootstrap bridges.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_linearized_audit
    (pate : RetrospectivePATEBootstrapVarianceAuditBridge)
    (patt : RetrospectivePATTBootstrapVarianceAuditBridge)
    (hpate_algebra :
      pate.bootstrap_bridge.linearized_replicate_algebra_verified)
    (hpate_multiplier : pate.bootstrap_bridge.multiplier_weight_regular)
    (hpate_score :
      pate.bootstrap_bridge.bootstrap_score_replication_consistent)
    (hpate_bias :
      pate.bootstrap_bridge.bootstrap_bias_correction_consistent)
    (hpate_variance :
      pate.bootstrap_bridge.conditional_variance_convergence)
    (hpatt_algebra :
      patt.bootstrap_bridge.linearized_replicate_algebra_verified)
    (hpatt_multiplier : patt.bootstrap_bridge.multiplier_weight_regular)
    (hpatt_score :
      patt.bootstrap_bridge.bootstrap_score_replication_consistent)
    (hpatt_bias :
      patt.bootstrap_bridge.bootstrap_bias_correction_consistent)
    (hpatt_variance :
      patt.bootstrap_bridge.conditional_variance_convergence) :
    pate.bootstrap_variance_consistent ∧
      patt.bootstrap_variance_consistent := by
  constructor
  · exact retrospective_pate_bootstrap_variance_consistency_of_linearized_audit
      pate hpate_algebra hpate_multiplier hpate_score hpate_bias hpate_variance
  · exact retrospective_patt_bootstrap_variance_consistency_of_linearized_audit
      patt hpatt_algebra hpatt_multiplier hpatt_score hpatt_bias hpatt_variance

/-- Paired retrospective PATE/PATT bootstrap variance audit bridge. -/
structure RetrospectivePATEPATTBootstrapVarianceAuditBridge where
  pate_bridge : RetrospectivePATEBootstrapVarianceAuditBridge
  patt_bridge : RetrospectivePATTBootstrapVarianceAuditBridge

/--
Paired retrospective PATE/PATT bootstrap variance consistency from a single
paired audited linearized bootstrap bridge.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_paired_linearized_audit
    (b : RetrospectivePATEPATTBootstrapVarianceAuditBridge)
    (hpate_algebra :
      b.pate_bridge.bootstrap_bridge.linearized_replicate_algebra_verified)
    (hpate_multiplier :
      b.pate_bridge.bootstrap_bridge.multiplier_weight_regular)
    (hpate_score :
      b.pate_bridge.bootstrap_bridge.bootstrap_score_replication_consistent)
    (hpate_bias :
      b.pate_bridge.bootstrap_bridge.bootstrap_bias_correction_consistent)
    (hpate_variance :
      b.pate_bridge.bootstrap_bridge.conditional_variance_convergence)
    (hpatt_algebra :
      b.patt_bridge.bootstrap_bridge.linearized_replicate_algebra_verified)
    (hpatt_multiplier :
      b.patt_bridge.bootstrap_bridge.multiplier_weight_regular)
    (hpatt_score :
      b.patt_bridge.bootstrap_bridge.bootstrap_score_replication_consistent)
    (hpatt_bias :
      b.patt_bridge.bootstrap_bridge.bootstrap_bias_correction_consistent)
    (hpatt_variance :
      b.patt_bridge.bootstrap_bridge.conditional_variance_convergence) :
    b.pate_bridge.bootstrap_variance_consistent ∧
      b.patt_bridge.bootstrap_variance_consistent :=
  retrospective_pate_patt_bootstrap_variance_consistency_of_linearized_audit
    b.pate_bridge b.patt_bridge hpate_algebra hpate_multiplier hpate_score
    hpate_bias hpate_variance hpatt_algebra hpatt_multiplier hpatt_score
    hpatt_bias hpatt_variance

end WDSM
end Matching
end StatInference
