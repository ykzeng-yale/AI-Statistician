import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Tactic.Ring
import StatInference.Matching.WDSM.BootstrapMultinomialDrawBridge
import StatInference.Matching.WDSM.BootstrapVarianceConsistencyBridge

/-!
# Prospective bootstrap variance audit bridge

This module records the prospective/common-weight counterpart of the WDSM
linearized bootstrap layer.  The finite identities keep the original matching
reuse structure fixed and perturb only linearized contributions with
multiplier weights.  Variance consistency is delegated to the same explicit
bootstrap bridge used by the retrospective route.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators
open Filter

variable {Unit Draw Omega Index : Type*}

/--
Prospective PATE linearized contribution.  The common-weight prospective
scenario uses the same finite influence layout as the retrospective total-PATE
linearization after the denominator and reuse weights have been specialized.
-/
noncomputable def prospectivePATEBootstrapInfluenceContribution
    (baseWeight reuseResidualWeight heterogeneity residual : Unit -> Real)
    (unit : Unit) : Real :=
  baseWeight unit * heterogeneity unit +
    reuseResidualWeight unit * residual unit

/-- Manuscript-facing prospective PATE linearized bootstrap numerator. -/
noncomputable def prospectivePATELinearizedBootstrapNumerator
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) : Real :=
  (∑ unit ∈ sample,
    multiplier unit * baseWeight unit * heterogeneity unit) +
    (∑ unit ∈ sample,
      multiplier unit * reuseResidualWeight unit * residual unit)

/--
The prospective PATE linearized bootstrap numerator is exactly a replicated
linearized sum of the fixed common-weight matching-structure contribution.
-/
theorem prospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) :
    prospectivePATELinearizedBootstrapNumerator sample multiplier
        baseWeight reuseResidualWeight heterogeneity residual =
      replicatedLinearizedSum sample multiplier
        (prospectivePATEBootstrapInfluenceContribution baseWeight
          reuseResidualWeight heterogeneity residual) := by
  unfold prospectivePATELinearizedBootstrapNumerator
    replicatedLinearizedSum
    prospectivePATEBootstrapInfluenceContribution
  rw [← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl
    (fun unit _hunit => by ring)

/--
The prospective PATE linearized bootstrap ratio is the generic replicated
linearized ratio applied to the fixed common-weight influence contribution and
the prospective denominator weight.
-/
theorem prospectivePATELinearizedBootstrapRatio_eq_replicatedLinearizedRatio
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) :
    prospectivePATELinearizedBootstrapNumerator sample multiplier
        baseWeight reuseResidualWeight heterogeneity residual /
        replicatedLinearizedSum sample multiplier baseWeight =
      replicatedLinearizedSum sample multiplier
        (prospectivePATEBootstrapInfluenceContribution baseWeight
          reuseResidualWeight heterogeneity residual) /
        replicatedLinearizedSum sample multiplier baseWeight := by
  rw [prospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum]

/--
Prospective PATT linearized contribution.  The one-sided treated contribution
and control reuse contribution are kept separate.
-/
noncomputable def prospectivePATTBootstrapInfluenceContribution
    (treatedContribution controlReuseContribution : Unit -> Real)
    (unit : Unit) : Real :=
  treatedContribution unit - controlReuseContribution unit

/-- Manuscript-facing prospective PATT linearized bootstrap numerator. -/
noncomputable def prospectivePATTLinearizedBootstrapNumerator
    (sample : Finset Unit)
    (multiplier treatedContribution controlReuseContribution : Unit -> Real) :
    Real :=
  (∑ unit ∈ sample, multiplier unit * treatedContribution unit) -
    (∑ unit ∈ sample, multiplier unit * controlReuseContribution unit)

/--
The prospective PATT linearized bootstrap numerator is exactly a replicated
linearized sum of the fixed one-sided matching-structure contribution.
-/
theorem prospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum
    (sample : Finset Unit)
    (multiplier treatedContribution controlReuseContribution : Unit -> Real) :
    prospectivePATTLinearizedBootstrapNumerator sample multiplier
        treatedContribution controlReuseContribution =
      replicatedLinearizedSum sample multiplier
        (prospectivePATTBootstrapInfluenceContribution treatedContribution
          controlReuseContribution) := by
  unfold prospectivePATTLinearizedBootstrapNumerator
    replicatedLinearizedSum
    prospectivePATTBootstrapInfluenceContribution
  rw [← Finset.sum_sub_distrib]
  exact Finset.sum_congr rfl
    (fun unit _hunit => by ring)

/--
The prospective PATT linearized bootstrap ratio is the generic replicated
linearized ratio applied to the fixed one-sided influence contribution and the
treated-side denominator weight.
-/
theorem prospectivePATTLinearizedBootstrapRatio_eq_replicatedLinearizedRatio
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real) :
    prospectivePATTLinearizedBootstrapNumerator sample multiplier
        treatedContribution controlReuseContribution /
        replicatedLinearizedSum sample multiplier denominatorWeight =
      replicatedLinearizedSum sample multiplier
        (prospectivePATTBootstrapInfluenceContribution treatedContribution
          controlReuseContribution) /
        replicatedLinearizedSum sample multiplier denominatorWeight := by
  rw [prospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum]

/--
Paired prospective PATE/PATT linearized bootstrap numerators as generic
replicated linearized sums.
-/
theorem prospectivePATEPATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual
      treatedContribution controlReuseContribution : Unit -> Real) :
    prospectivePATELinearizedBootstrapNumerator sample multiplier
        baseWeight reuseResidualWeight heterogeneity residual =
      replicatedLinearizedSum sample multiplier
        (prospectivePATEBootstrapInfluenceContribution baseWeight
          reuseResidualWeight heterogeneity residual) ∧
    prospectivePATTLinearizedBootstrapNumerator sample multiplier
        treatedContribution controlReuseContribution =
      replicatedLinearizedSum sample multiplier
        (prospectivePATTBootstrapInfluenceContribution treatedContribution
          controlReuseContribution) := by
  exact
    ⟨prospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum
        sample multiplier baseWeight reuseResidualWeight heterogeneity
        residual,
      prospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum
        sample multiplier treatedContribution controlReuseContribution⟩

/--
Paired prospective PATE/PATT linearized bootstrap ratios as generic replicated
linearized ratios.
-/
theorem prospectivePATEPATTLinearizedBootstrapRatio_eq_replicatedLinearizedRatio
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual
      pattDenominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real) :
    prospectivePATELinearizedBootstrapNumerator sample multiplier
        baseWeight reuseResidualWeight heterogeneity residual /
        replicatedLinearizedSum sample multiplier baseWeight =
      replicatedLinearizedSum sample multiplier
        (prospectivePATEBootstrapInfluenceContribution baseWeight
          reuseResidualWeight heterogeneity residual) /
        replicatedLinearizedSum sample multiplier baseWeight ∧
    prospectivePATTLinearizedBootstrapNumerator sample multiplier
        treatedContribution controlReuseContribution /
        replicatedLinearizedSum sample multiplier pattDenominatorWeight =
      replicatedLinearizedSum sample multiplier
        (prospectivePATTBootstrapInfluenceContribution treatedContribution
          controlReuseContribution) /
        replicatedLinearizedSum sample multiplier pattDenominatorWeight := by
  exact
    ⟨prospectivePATELinearizedBootstrapRatio_eq_replicatedLinearizedRatio
        sample multiplier baseWeight reuseResidualWeight heterogeneity
        residual,
      prospectivePATTLinearizedBootstrapRatio_eq_replicatedLinearizedRatio
        sample multiplier pattDenominatorWeight treatedContribution
        controlReuseContribution⟩

/--
Prospective PATE manuscript numerator minus its original finite influence sum
is the centered-count sum for a concrete multinomial draw-count replicate.
-/
theorem prospectivePATELinearizedBootstrapNumerator_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega)
    (baseWeight reuseResidualWeight heterogeneity residual : Unit -> Real) :
    prospectivePATELinearizedBootstrapNumerator sample
        (fun unit =>
          multinomialCountFromDrawIndicators draws drawIndicator omega unit)
        baseWeight reuseResidualWeight heterogeneity residual -
        baseLinearizedSum sample
          (prospectivePATEBootstrapInfluenceContribution baseWeight
            reuseResidualWeight heterogeneity residual) =
      ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          prospectivePATEBootstrapInfluenceContribution baseWeight
            reuseResidualWeight heterogeneity residual unit := by
  rw [prospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum]
  simpa [multiplierPerturbation] using
    (multiplierPerturbation_eq_replicated_sub_base sample
      (fun unit =>
        multinomialCountFromDrawIndicators draws drawIndicator omega unit)
      (prospectivePATEBootstrapInfluenceContribution baseWeight
        reuseResidualWeight heterogeneity residual)).symm

/--
Prospective PATT manuscript numerator minus its original finite influence sum
is the centered-count sum for a concrete multinomial draw-count replicate.
-/
theorem prospectivePATTLinearizedBootstrapNumerator_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega)
    (treatedContribution controlReuseContribution : Unit -> Real) :
    prospectivePATTLinearizedBootstrapNumerator sample
        (fun unit =>
          multinomialCountFromDrawIndicators draws drawIndicator omega unit)
        treatedContribution controlReuseContribution -
        baseLinearizedSum sample
          (prospectivePATTBootstrapInfluenceContribution
            treatedContribution controlReuseContribution) =
      ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          prospectivePATTBootstrapInfluenceContribution
            treatedContribution controlReuseContribution unit := by
  rw [prospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum]
  simpa [multiplierPerturbation] using
    (multiplierPerturbation_eq_replicated_sub_base sample
      (fun unit =>
        multinomialCountFromDrawIndicators draws drawIndicator omega unit)
      (prospectivePATTBootstrapInfluenceContribution
        treatedContribution controlReuseContribution)).symm

/--
Eventual prospective PATE construction bridge from the manuscript linearized
numerator-minus-base expression to the centered-count construction used by
finite bootstrap error reducers.
-/
theorem eventually_error_eq_prospectivePATE_centered_count_sum_of_linearized_numerator
    {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (error : Index -> Real)
    (hconstruct :
      error =ᶠ[l]
        (fun index =>
          prospectivePATELinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index) -
            baseLinearizedSum (sample index)
              (prospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index)))) :
    error =ᶠ[l]
      (fun index =>
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index) unit) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        prospectivePATELinearizedBootstrapNumerator (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (baseWeight index) (reuseResidualWeight index)
            (heterogeneity index) (residual index) -
          baseLinearizedSum (sample index)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) := hindex
    _ =
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index) unit :=
          prospectivePATELinearizedBootstrapNumerator_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
            (sample index) (draws index) (drawIndicator index) (omega index)
            (baseWeight index) (reuseResidualWeight index)
            (heterogeneity index) (residual index)

/--
Eventual prospective PATE construction bridge from the manuscript linearized
numerator-minus-base expression to the replicated-linearized-minus-base
construction used by full-support bootstrap variance endpoints.
-/
theorem eventually_error_eq_prospectivePATE_replicatedLinearized_sub_base_of_linearized_numerator
    {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (baseWeight reuseResidualWeight heterogeneity residual :
      Index -> Unit -> Real)
    (error : Index -> Real)
    (hconstruct :
      error =ᶠ[l]
        (fun index =>
          prospectivePATELinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index) -
            baseLinearizedSum (sample index)
              (prospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index)))) :
    error =ᶠ[l]
      (fun index =>
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) -
          baseLinearizedSum (sample index)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        prospectivePATELinearizedBootstrapNumerator (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (baseWeight index) (reuseResidualWeight index)
            (heterogeneity index) (residual index) -
          baseLinearizedSum (sample index)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) := hindex
    _ =
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) -
          baseLinearizedSum (sample index)
            (prospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) := by
          rw [prospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum]

/--
Eventual prospective PATT construction bridge from the manuscript linearized
numerator-minus-base expression to the centered-count construction used by
finite bootstrap error reducers.
-/
theorem eventually_error_eq_prospectivePATT_centered_count_sum_of_linearized_numerator
    {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (treatedContribution controlReuseContribution : Index -> Unit -> Real)
    (error : Index -> Real)
    (hconstruct :
      error =ᶠ[l]
        (fun index =>
          prospectivePATTLinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (treatedContribution index) (controlReuseContribution index) -
            baseLinearizedSum (sample index)
              (prospectivePATTBootstrapInfluenceContribution
                (treatedContribution index)
                (controlReuseContribution index)))) :
    error =ᶠ[l]
      (fun index =>
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index) unit) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        prospectivePATTLinearizedBootstrapNumerator (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (treatedContribution index) (controlReuseContribution index) -
          baseLinearizedSum (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) := hindex
    _ =
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index) unit :=
          prospectivePATTLinearizedBootstrapNumerator_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
            (sample index) (draws index) (drawIndicator index) (omega index)
            (treatedContribution index) (controlReuseContribution index)

/--
Eventual prospective PATT construction bridge from the manuscript linearized
numerator-minus-base expression to the replicated-linearized-minus-base
construction used by full-support bootstrap variance endpoints.
-/
theorem eventually_error_eq_prospectivePATT_replicatedLinearized_sub_base_of_linearized_numerator
    {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (treatedContribution controlReuseContribution : Index -> Unit -> Real)
    (error : Index -> Real)
    (hconstruct :
      error =ᶠ[l]
        (fun index =>
          prospectivePATTLinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (treatedContribution index) (controlReuseContribution index) -
            baseLinearizedSum (sample index)
              (prospectivePATTBootstrapInfluenceContribution
                (treatedContribution index)
                (controlReuseContribution index)))) :
    error =ᶠ[l]
      (fun index =>
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) -
          baseLinearizedSum (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index))) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        prospectivePATTLinearizedBootstrapNumerator (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (treatedContribution index) (controlReuseContribution index) -
          baseLinearizedSum (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) := hindex
    _ =
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) -
          baseLinearizedSum (sample index)
            (prospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) := by
          rw [prospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum]

/--
Prospective PATE bootstrap variance audit bridge.  The transfer field records
that the generic bootstrap variance conclusion is the manuscript's prospective
PATE variance-estimator consistency claim.
-/
structure ProspectivePATEBootstrapVarianceAuditBridge where
  bootstrap_bridge : LinearizedBootstrapVarianceConsistencyBridge
  bootstrap_variance_consistent : Prop
  bootstrap_to_prospective_pate :
    bootstrap_bridge.bootstrap_variance_consistent ->
      bootstrap_variance_consistent

/-- Prospective PATE bootstrap variance consistency from the audited bridge. -/
theorem prospective_pate_bootstrap_variance_consistency_of_linearized_audit
    (b : ProspectivePATEBootstrapVarianceAuditBridge)
    (halgebra :
      b.bootstrap_bridge.linearized_replicate_algebra_verified)
    (hmultiplier : b.bootstrap_bridge.multiplier_weight_regular)
    (hscore :
      b.bootstrap_bridge.bootstrap_score_replication_consistent)
    (hbias :
      b.bootstrap_bridge.bootstrap_bias_correction_consistent)
    (hvariance : b.bootstrap_bridge.conditional_variance_convergence) :
    b.bootstrap_variance_consistent := by
  exact b.bootstrap_to_prospective_pate
    (bootstrap_variance_consistency_of_linearized_bridge
      b.bootstrap_bridge halgebra hmultiplier hscore hbias hvariance)

/--
Prospective PATT bootstrap variance audit bridge.  The transfer field records
that the generic bootstrap variance conclusion is the manuscript's prospective
PATT variance-estimator consistency claim.
-/
structure ProspectivePATTBootstrapVarianceAuditBridge where
  bootstrap_bridge : LinearizedBootstrapVarianceConsistencyBridge
  bootstrap_variance_consistent : Prop
  bootstrap_to_prospective_patt :
    bootstrap_bridge.bootstrap_variance_consistent ->
      bootstrap_variance_consistent

/-- Prospective PATT bootstrap variance consistency from the audited bridge. -/
theorem prospective_patt_bootstrap_variance_consistency_of_linearized_audit
    (b : ProspectivePATTBootstrapVarianceAuditBridge)
    (halgebra :
      b.bootstrap_bridge.linearized_replicate_algebra_verified)
    (hmultiplier : b.bootstrap_bridge.multiplier_weight_regular)
    (hscore :
      b.bootstrap_bridge.bootstrap_score_replication_consistent)
    (hbias :
      b.bootstrap_bridge.bootstrap_bias_correction_consistent)
    (hvariance : b.bootstrap_bridge.conditional_variance_convergence) :
    b.bootstrap_variance_consistent := by
  exact b.bootstrap_to_prospective_patt
    (bootstrap_variance_consistency_of_linearized_bridge
      b.bootstrap_bridge halgebra hmultiplier hscore hbias hvariance)

/--
Paired prospective PATE/PATT bootstrap variance consistency from audited
linearized bootstrap bridges.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_linearized_audit
    (pate : ProspectivePATEBootstrapVarianceAuditBridge)
    (patt : ProspectivePATTBootstrapVarianceAuditBridge)
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
  · exact prospective_pate_bootstrap_variance_consistency_of_linearized_audit
      pate hpate_algebra hpate_multiplier hpate_score hpate_bias hpate_variance
  · exact prospective_patt_bootstrap_variance_consistency_of_linearized_audit
      patt hpatt_algebra hpatt_multiplier hpatt_score hpatt_bias hpatt_variance

/-- Paired prospective PATE/PATT bootstrap variance audit bridge. -/
structure ProspectivePATEPATTBootstrapVarianceAuditBridge where
  pate_bridge : ProspectivePATEBootstrapVarianceAuditBridge
  patt_bridge : ProspectivePATTBootstrapVarianceAuditBridge

/--
Paired prospective PATE/PATT bootstrap variance consistency from a single
paired audited linearized bootstrap bridge.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_paired_linearized_audit
    (b : ProspectivePATEPATTBootstrapVarianceAuditBridge)
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
  prospective_pate_patt_bootstrap_variance_consistency_of_linearized_audit
    b.pate_bridge b.patt_bridge hpate_algebra hpate_multiplier hpate_score
    hpate_bias hpate_variance hpatt_algebra hpatt_multiplier hpatt_score
    hpatt_bias hpatt_variance

end WDSM
end Matching
end StatInference
