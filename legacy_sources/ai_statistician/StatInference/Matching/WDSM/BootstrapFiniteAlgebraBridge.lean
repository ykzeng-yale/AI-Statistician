import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.BootstrapLinearizedReplicate
import StatInference.Matching.WDSM.BootstrapVarianceConsistencyBridge
import StatInference.Matching.WDSM.ProspectiveBootstrapVariance

/-!
# Bootstrap finite-algebra bridge

The bootstrap variance-consistency interface separates finite linearized
replicate algebra from multiplier and conditional-variance probability inputs.
This module discharges the finite-algebra field for each WDSM scenario from
the checked replicated-sum and replicated-ratio identities.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit : Type*}

/-- Finite retrospective PATE bootstrap algebra evidence. -/
def retrospectivePATEBootstrapFiniteAlgebraVerified
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) : Prop :=
  retrospectivePATELinearizedBootstrapNumerator sample multiplier baseWeight
      reuseResidualWeight heterogeneity residual =
    replicatedLinearizedSum sample multiplier
      (retrospectivePATEBootstrapInfluenceContribution baseWeight
        reuseResidualWeight heterogeneity residual) ∧
  retrospectivePATELinearizedBootstrapNumerator sample multiplier baseWeight
      reuseResidualWeight heterogeneity residual /
      replicatedLinearizedSum sample multiplier baseWeight =
    replicatedLinearizedSum sample multiplier
      (retrospectivePATEBootstrapInfluenceContribution baseWeight
        reuseResidualWeight heterogeneity residual) /
      replicatedLinearizedSum sample multiplier baseWeight

/-- The finite retrospective PATE bootstrap algebra is checked. -/
theorem retrospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) :
    retrospectivePATEBootstrapFiniteAlgebraVerified sample multiplier
      baseWeight reuseResidualWeight heterogeneity residual :=
  ⟨retrospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum
      sample multiplier baseWeight reuseResidualWeight heterogeneity residual,
    retrospectivePATELinearizedBootstrapRatio_eq_replicatedLinearizedRatio
      sample multiplier baseWeight reuseResidualWeight heterogeneity residual⟩

/--
Retrospective PATE bootstrap variance bridge whose finite-algebra field is the
checked retrospective PATE replicated-sum/ratio evidence.
-/
def retrospectivePATELinearizedBootstrapVarianceBridgeOfFiniteAlgebra
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      retrospectivePATEBootstrapFiniteAlgebraVerified sample multiplier
          baseWeight reuseResidualWeight heterogeneity residual ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent) :
    LinearizedBootstrapVarianceConsistencyBridge where
  linearized_replicate_algebra_verified :=
    retrospectivePATEBootstrapFiniteAlgebraVerified sample multiplier
      baseWeight reuseResidualWeight heterogeneity residual
  multiplier_weight_regular := multiplierWeightRegular
  bootstrap_score_replication_consistent :=
    bootstrapScoreReplicationConsistent
  bootstrap_bias_correction_consistent :=
    bootstrapBiasCorrectionConsistent
  conditional_variance_convergence := conditionalVarianceConvergence
  bootstrap_variance_consistent := bootstrapVarianceConsistent
  bridge := bridge

/--
Retrospective PATE bootstrap variance consistency from checked finite algebra
plus the remaining probability inputs.
-/
theorem retrospective_pate_bootstrap_variance_consistency_of_finite_algebra
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      retrospectivePATEBootstrapFiniteAlgebraVerified sample multiplier
          baseWeight reuseResidualWeight heterogeneity residual ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent)
    (hvariance : conditionalVarianceConvergence) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_linearized_bridge
    (retrospectivePATELinearizedBootstrapVarianceBridgeOfFiniteAlgebra
      sample multiplier baseWeight reuseResidualWeight heterogeneity residual
      multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent bridge)
    (retrospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
      sample multiplier baseWeight reuseResidualWeight heterogeneity residual)
    hmultiplier hscore hbias hvariance

/-- Finite retrospective PATT bootstrap algebra evidence. -/
def retrospectivePATTBootstrapFiniteAlgebraVerified
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real) : Prop :=
  retrospectivePATTLinearizedBootstrapNumerator sample multiplier
      treatedContribution controlReuseContribution =
    replicatedLinearizedSum sample multiplier
      (retrospectivePATTBootstrapInfluenceContribution treatedContribution
        controlReuseContribution) ∧
  retrospectivePATTLinearizedBootstrapNumerator sample multiplier
      treatedContribution controlReuseContribution /
      replicatedLinearizedSum sample multiplier denominatorWeight =
    replicatedLinearizedSum sample multiplier
      (retrospectivePATTBootstrapInfluenceContribution treatedContribution
        controlReuseContribution) /
      replicatedLinearizedSum sample multiplier denominatorWeight

/-- The finite retrospective PATT bootstrap algebra is checked. -/
theorem retrospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real) :
    retrospectivePATTBootstrapFiniteAlgebraVerified sample multiplier
      denominatorWeight treatedContribution controlReuseContribution :=
  ⟨retrospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum
      sample multiplier treatedContribution controlReuseContribution,
    retrospectivePATTLinearizedBootstrapRatio_eq_replicatedLinearizedRatio
      sample multiplier denominatorWeight treatedContribution
      controlReuseContribution⟩

/--
Retrospective PATT bootstrap variance bridge whose finite-algebra field is the
checked retrospective PATT replicated-sum/ratio evidence.
-/
def retrospectivePATTLinearizedBootstrapVarianceBridgeOfFiniteAlgebra
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      retrospectivePATTBootstrapFiniteAlgebraVerified sample multiplier
          denominatorWeight treatedContribution controlReuseContribution ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent) :
    LinearizedBootstrapVarianceConsistencyBridge where
  linearized_replicate_algebra_verified :=
    retrospectivePATTBootstrapFiniteAlgebraVerified sample multiplier
      denominatorWeight treatedContribution controlReuseContribution
  multiplier_weight_regular := multiplierWeightRegular
  bootstrap_score_replication_consistent :=
    bootstrapScoreReplicationConsistent
  bootstrap_bias_correction_consistent :=
    bootstrapBiasCorrectionConsistent
  conditional_variance_convergence := conditionalVarianceConvergence
  bootstrap_variance_consistent := bootstrapVarianceConsistent
  bridge := bridge

/--
Retrospective PATT bootstrap variance consistency from checked finite algebra
plus the remaining probability inputs.
-/
theorem retrospective_patt_bootstrap_variance_consistency_of_finite_algebra
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      retrospectivePATTBootstrapFiniteAlgebraVerified sample multiplier
          denominatorWeight treatedContribution controlReuseContribution ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent)
    (hvariance : conditionalVarianceConvergence) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_linearized_bridge
    (retrospectivePATTLinearizedBootstrapVarianceBridgeOfFiniteAlgebra
      sample multiplier denominatorWeight treatedContribution
      controlReuseContribution multiplierWeightRegular
      bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
      conditionalVarianceConvergence bootstrapVarianceConsistent bridge)
    (retrospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
      sample multiplier denominatorWeight treatedContribution
      controlReuseContribution)
    hmultiplier hscore hbias hvariance

/-- Finite prospective PATE bootstrap algebra evidence. -/
def prospectivePATEBootstrapFiniteAlgebraVerified
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) : Prop :=
  prospectivePATELinearizedBootstrapNumerator sample multiplier baseWeight
      reuseResidualWeight heterogeneity residual =
    replicatedLinearizedSum sample multiplier
      (prospectivePATEBootstrapInfluenceContribution baseWeight
        reuseResidualWeight heterogeneity residual) ∧
  prospectivePATELinearizedBootstrapNumerator sample multiplier baseWeight
      reuseResidualWeight heterogeneity residual /
      replicatedLinearizedSum sample multiplier baseWeight =
    replicatedLinearizedSum sample multiplier
      (prospectivePATEBootstrapInfluenceContribution baseWeight
        reuseResidualWeight heterogeneity residual) /
      replicatedLinearizedSum sample multiplier baseWeight

/-- The finite prospective PATE bootstrap algebra is checked. -/
theorem prospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) :
    prospectivePATEBootstrapFiniteAlgebraVerified sample multiplier
      baseWeight reuseResidualWeight heterogeneity residual :=
  ⟨prospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum
      sample multiplier baseWeight reuseResidualWeight heterogeneity residual,
    prospectivePATELinearizedBootstrapRatio_eq_replicatedLinearizedRatio
      sample multiplier baseWeight reuseResidualWeight heterogeneity residual⟩

/--
Prospective PATE bootstrap variance bridge whose finite-algebra field is the
checked prospective PATE replicated-sum/ratio evidence.
-/
def prospectivePATELinearizedBootstrapVarianceBridgeOfFiniteAlgebra
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      prospectivePATEBootstrapFiniteAlgebraVerified sample multiplier
          baseWeight reuseResidualWeight heterogeneity residual ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent) :
    LinearizedBootstrapVarianceConsistencyBridge where
  linearized_replicate_algebra_verified :=
    prospectivePATEBootstrapFiniteAlgebraVerified sample multiplier
      baseWeight reuseResidualWeight heterogeneity residual
  multiplier_weight_regular := multiplierWeightRegular
  bootstrap_score_replication_consistent :=
    bootstrapScoreReplicationConsistent
  bootstrap_bias_correction_consistent :=
    bootstrapBiasCorrectionConsistent
  conditional_variance_convergence := conditionalVarianceConvergence
  bootstrap_variance_consistent := bootstrapVarianceConsistent
  bridge := bridge

/--
Prospective PATE bootstrap variance consistency from checked finite algebra
plus the remaining probability inputs.
-/
theorem prospective_pate_bootstrap_variance_consistency_of_finite_algebra
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      prospectivePATEBootstrapFiniteAlgebraVerified sample multiplier
          baseWeight reuseResidualWeight heterogeneity residual ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent)
    (hvariance : conditionalVarianceConvergence) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_linearized_bridge
    (prospectivePATELinearizedBootstrapVarianceBridgeOfFiniteAlgebra
      sample multiplier baseWeight reuseResidualWeight heterogeneity residual
      multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent bridge)
    (prospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
      sample multiplier baseWeight reuseResidualWeight heterogeneity residual)
    hmultiplier hscore hbias hvariance

/-- Finite prospective PATT bootstrap algebra evidence. -/
def prospectivePATTBootstrapFiniteAlgebraVerified
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real) : Prop :=
  prospectivePATTLinearizedBootstrapNumerator sample multiplier
      treatedContribution controlReuseContribution =
    replicatedLinearizedSum sample multiplier
      (prospectivePATTBootstrapInfluenceContribution treatedContribution
        controlReuseContribution) ∧
  prospectivePATTLinearizedBootstrapNumerator sample multiplier
      treatedContribution controlReuseContribution /
      replicatedLinearizedSum sample multiplier denominatorWeight =
    replicatedLinearizedSum sample multiplier
      (prospectivePATTBootstrapInfluenceContribution treatedContribution
        controlReuseContribution) /
      replicatedLinearizedSum sample multiplier denominatorWeight

/-- The finite prospective PATT bootstrap algebra is checked. -/
theorem prospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real) :
    prospectivePATTBootstrapFiniteAlgebraVerified sample multiplier
      denominatorWeight treatedContribution controlReuseContribution :=
  ⟨prospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum
      sample multiplier treatedContribution controlReuseContribution,
    prospectivePATTLinearizedBootstrapRatio_eq_replicatedLinearizedRatio
      sample multiplier denominatorWeight treatedContribution
      controlReuseContribution⟩

/--
Prospective PATT bootstrap variance bridge whose finite-algebra field is the
checked prospective PATT replicated-sum/ratio evidence.
-/
def prospectivePATTLinearizedBootstrapVarianceBridgeOfFiniteAlgebra
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      prospectivePATTBootstrapFiniteAlgebraVerified sample multiplier
          denominatorWeight treatedContribution controlReuseContribution ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent) :
    LinearizedBootstrapVarianceConsistencyBridge where
  linearized_replicate_algebra_verified :=
    prospectivePATTBootstrapFiniteAlgebraVerified sample multiplier
      denominatorWeight treatedContribution controlReuseContribution
  multiplier_weight_regular := multiplierWeightRegular
  bootstrap_score_replication_consistent :=
    bootstrapScoreReplicationConsistent
  bootstrap_bias_correction_consistent :=
    bootstrapBiasCorrectionConsistent
  conditional_variance_convergence := conditionalVarianceConvergence
  bootstrap_variance_consistent := bootstrapVarianceConsistent
  bridge := bridge

/--
Prospective PATT bootstrap variance consistency from checked finite algebra
plus the remaining probability inputs.
-/
theorem prospective_patt_bootstrap_variance_consistency_of_finite_algebra
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real)
    (multiplierWeightRegular bootstrapScoreReplicationConsistent
      bootstrapBiasCorrectionConsistent conditionalVarianceConvergence
      bootstrapVarianceConsistent : Prop)
    (bridge :
      prospectivePATTBootstrapFiniteAlgebraVerified sample multiplier
          denominatorWeight treatedContribution controlReuseContribution ->
        multiplierWeightRegular ->
        bootstrapScoreReplicationConsistent ->
        bootstrapBiasCorrectionConsistent ->
        conditionalVarianceConvergence ->
        bootstrapVarianceConsistent)
    (hmultiplier : multiplierWeightRegular)
    (hscore : bootstrapScoreReplicationConsistent)
    (hbias : bootstrapBiasCorrectionConsistent)
    (hvariance : conditionalVarianceConvergence) :
    bootstrapVarianceConsistent :=
  bootstrap_variance_consistency_of_linearized_bridge
    (prospectivePATTLinearizedBootstrapVarianceBridgeOfFiniteAlgebra
      sample multiplier denominatorWeight treatedContribution
      controlReuseContribution multiplierWeightRegular
      bootstrapScoreReplicationConsistent bootstrapBiasCorrectionConsistent
      conditionalVarianceConvergence bootstrapVarianceConsistent bridge)
    (prospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
      sample multiplier denominatorWeight treatedContribution
      controlReuseContribution)
    hmultiplier hscore hbias hvariance

/-- Paired finite retrospective PATE/PATT bootstrap algebra evidence. -/
def retrospectivePATEPATTBootstrapFiniteAlgebraVerified
    (pateSample : Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Unit -> Real)
    (pattSample : Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Unit -> Real) : Prop :=
  retrospectivePATEBootstrapFiniteAlgebraVerified pateSample pateMultiplier
      pateBaseWeight pateReuseResidualWeight pateHeterogeneity pateResidual ∧
    retrospectivePATTBootstrapFiniteAlgebraVerified pattSample pattMultiplier
      pattDenominatorWeight pattTreatedContribution pattControlReuseContribution

/-- The paired finite retrospective PATE/PATT bootstrap algebra is checked. -/
theorem retrospectivePATEPATTBootstrapFiniteAlgebraVerified_of_replicate_identities
    (pateSample : Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Unit -> Real)
    (pattSample : Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Unit -> Real) :
    retrospectivePATEPATTBootstrapFiniteAlgebraVerified pateSample
      pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution :=
  ⟨retrospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
      pateSample pateMultiplier pateBaseWeight pateReuseResidualWeight
      pateHeterogeneity pateResidual,
    retrospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
      pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution⟩

/-- Paired finite prospective PATE/PATT bootstrap algebra evidence. -/
def prospectivePATEPATTBootstrapFiniteAlgebraVerified
    (pateSample : Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Unit -> Real)
    (pattSample : Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Unit -> Real) : Prop :=
  prospectivePATEBootstrapFiniteAlgebraVerified pateSample pateMultiplier
      pateBaseWeight pateReuseResidualWeight pateHeterogeneity pateResidual ∧
    prospectivePATTBootstrapFiniteAlgebraVerified pattSample pattMultiplier
      pattDenominatorWeight pattTreatedContribution pattControlReuseContribution

/-- The paired finite prospective PATE/PATT bootstrap algebra is checked. -/
theorem prospectivePATEPATTBootstrapFiniteAlgebraVerified_of_replicate_identities
    (pateSample : Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Unit -> Real)
    (pattSample : Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Unit -> Real) :
    prospectivePATEPATTBootstrapFiniteAlgebraVerified pateSample
      pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution :=
  ⟨prospectivePATEBootstrapFiniteAlgebraVerified_of_replicate_identities
      pateSample pateMultiplier pateBaseWeight pateReuseResidualWeight
      pateHeterogeneity pateResidual,
    prospectivePATTBootstrapFiniteAlgebraVerified_of_replicate_identities
      pattSample pattMultiplier pattDenominatorWeight
      pattTreatedContribution pattControlReuseContribution⟩

/--
Paired retrospective PATE/PATT bootstrap variance consistency from checked
finite algebra plus the remaining probability inputs.
-/
theorem retrospective_pate_patt_bootstrap_variance_consistency_of_finite_algebra
    (pateSample : Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Unit -> Real)
    (pattSample : Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Unit -> Real)
    (pateMultiplierWeightRegular pateScoreReplicationConsistent
      pateBiasCorrectionConsistent pateConditionalVarianceConvergence
      pateBootstrapVarianceConsistent : Prop)
    (pattMultiplierWeightRegular pattScoreReplicationConsistent
      pattBiasCorrectionConsistent pattConditionalVarianceConvergence
      pattBootstrapVarianceConsistent : Prop)
    (pateBridge :
      retrospectivePATEBootstrapFiniteAlgebraVerified pateSample
          pateMultiplier pateBaseWeight pateReuseResidualWeight
          pateHeterogeneity pateResidual ->
        pateMultiplierWeightRegular ->
        pateScoreReplicationConsistent ->
        pateBiasCorrectionConsistent ->
        pateConditionalVarianceConvergence ->
        pateBootstrapVarianceConsistent)
    (pattBridge :
      retrospectivePATTBootstrapFiniteAlgebraVerified pattSample
          pattMultiplier pattDenominatorWeight pattTreatedContribution
          pattControlReuseContribution ->
        pattMultiplierWeightRegular ->
        pattScoreReplicationConsistent ->
        pattBiasCorrectionConsistent ->
        pattConditionalVarianceConvergence ->
        pattBootstrapVarianceConsistent)
    (hpateMultiplier : pateMultiplierWeightRegular)
    (hpateScore : pateScoreReplicationConsistent)
    (hpateBias : pateBiasCorrectionConsistent)
    (hpateVariance : pateConditionalVarianceConvergence)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattScoreReplicationConsistent)
    (hpattBias : pattBiasCorrectionConsistent)
    (hpattVariance : pattConditionalVarianceConvergence) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨retrospective_pate_bootstrap_variance_consistency_of_finite_algebra
      pateSample pateMultiplier pateBaseWeight pateReuseResidualWeight
      pateHeterogeneity pateResidual pateMultiplierWeightRegular
      pateScoreReplicationConsistent pateBiasCorrectionConsistent
      pateConditionalVarianceConvergence pateBootstrapVarianceConsistent
      pateBridge hpateMultiplier hpateScore hpateBias hpateVariance,
    retrospective_patt_bootstrap_variance_consistency_of_finite_algebra
      pattSample pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution pattMultiplierWeightRegular
      pattScoreReplicationConsistent pattBiasCorrectionConsistent
      pattConditionalVarianceConvergence pattBootstrapVarianceConsistent
      pattBridge hpattMultiplier hpattScore hpattBias hpattVariance⟩

/--
Paired prospective PATE/PATT bootstrap variance consistency from checked
finite algebra plus the remaining probability inputs.
-/
theorem prospective_pate_patt_bootstrap_variance_consistency_of_finite_algebra
    (pateSample : Finset Unit)
    (pateMultiplier pateBaseWeight pateReuseResidualWeight pateHeterogeneity
      pateResidual : Unit -> Real)
    (pattSample : Finset Unit)
    (pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution : Unit -> Real)
    (pateMultiplierWeightRegular pateScoreReplicationConsistent
      pateBiasCorrectionConsistent pateConditionalVarianceConvergence
      pateBootstrapVarianceConsistent : Prop)
    (pattMultiplierWeightRegular pattScoreReplicationConsistent
      pattBiasCorrectionConsistent pattConditionalVarianceConvergence
      pattBootstrapVarianceConsistent : Prop)
    (pateBridge :
      prospectivePATEBootstrapFiniteAlgebraVerified pateSample
          pateMultiplier pateBaseWeight pateReuseResidualWeight
          pateHeterogeneity pateResidual ->
        pateMultiplierWeightRegular ->
        pateScoreReplicationConsistent ->
        pateBiasCorrectionConsistent ->
        pateConditionalVarianceConvergence ->
        pateBootstrapVarianceConsistent)
    (pattBridge :
      prospectivePATTBootstrapFiniteAlgebraVerified pattSample
          pattMultiplier pattDenominatorWeight pattTreatedContribution
          pattControlReuseContribution ->
        pattMultiplierWeightRegular ->
        pattScoreReplicationConsistent ->
        pattBiasCorrectionConsistent ->
        pattConditionalVarianceConvergence ->
        pattBootstrapVarianceConsistent)
    (hpateMultiplier : pateMultiplierWeightRegular)
    (hpateScore : pateScoreReplicationConsistent)
    (hpateBias : pateBiasCorrectionConsistent)
    (hpateVariance : pateConditionalVarianceConvergence)
    (hpattMultiplier : pattMultiplierWeightRegular)
    (hpattScore : pattScoreReplicationConsistent)
    (hpattBias : pattBiasCorrectionConsistent)
    (hpattVariance : pattConditionalVarianceConvergence) :
    pateBootstrapVarianceConsistent ∧ pattBootstrapVarianceConsistent :=
  ⟨prospective_pate_bootstrap_variance_consistency_of_finite_algebra
      pateSample pateMultiplier pateBaseWeight pateReuseResidualWeight
      pateHeterogeneity pateResidual pateMultiplierWeightRegular
      pateScoreReplicationConsistent pateBiasCorrectionConsistent
      pateConditionalVarianceConvergence pateBootstrapVarianceConsistent
      pateBridge hpateMultiplier hpateScore hpateBias hpateVariance,
    prospective_patt_bootstrap_variance_consistency_of_finite_algebra
      pattSample pattMultiplier pattDenominatorWeight pattTreatedContribution
      pattControlReuseContribution pattMultiplierWeightRegular
      pattScoreReplicationConsistent pattBiasCorrectionConsistent
      pattConditionalVarianceConvergence pattBootstrapVarianceConsistent
      pattBridge hpattMultiplier hpattScore hpattBias hpattVariance⟩

end WDSM
end Matching
end StatInference
