import StatInference.Matching.WDSM.BootstrapVarianceStability
import StatInference.Matching.WDSM.FiniteCellMassConvergence
import StatInference.Matching.WDSM.SqueezeAlgebra

/-!
# Bootstrap error negligibility from deterministic bounds

This module reduces the bootstrap score-replication and bias-correction
negligibility assumptions to absolute-value bounds by deterministic sequences
that converge to zero.  The stochastic work left for the paper is then to
prove those bounds for the concrete matching and score-estimation errors.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index : Type*} {l : Filter Index}

/-- Score-replication error negligibility from a pointwise absolute bound. -/
theorem bootstrapScoreReplicationErrorNegligible_of_abs_le_bound
    (scoreReplicationError scoreErrorBound : Index -> Real)
    (hbound :
      ∀ index, |scoreReplicationError index| ≤ scoreErrorBound index)
    (hbound_tendsto :
      Tendsto scoreErrorBound l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError :=
  tendsto_zero_of_abs_le_bound
    scoreReplicationError scoreErrorBound hbound hbound_tendsto

/--
Score-replication error negligibility from an eventual absolute bound.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_eventually_abs_le_bound
    (scoreReplicationError scoreErrorBound : Index -> Real)
    (hbound :
      ∀ᶠ index in l,
        |scoreReplicationError index| ≤ scoreErrorBound index)
    (hbound_tendsto :
      Tendsto scoreErrorBound l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError :=
  tendsto_zero_of_eventually_abs_le_bound
    scoreReplicationError scoreErrorBound hbound hbound_tendsto

/-- Bias-correction error negligibility from a pointwise absolute bound. -/
theorem bootstrapBiasCorrectionErrorNegligible_of_abs_le_bound
    (biasCorrectionError biasErrorBound : Index -> Real)
    (hbound :
      ∀ index, |biasCorrectionError index| ≤ biasErrorBound index)
    (hbound_tendsto :
      Tendsto biasErrorBound l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError :=
  tendsto_zero_of_abs_le_bound
    biasCorrectionError biasErrorBound hbound hbound_tendsto

/-- Bias-correction error negligibility from an eventual absolute bound. -/
theorem bootstrapBiasCorrectionErrorNegligible_of_eventually_abs_le_bound
    (biasCorrectionError biasErrorBound : Index -> Real)
    (hbound :
      ∀ᶠ index in l,
        |biasCorrectionError index| ≤ biasErrorBound index)
    (hbound_tendsto :
      Tendsto biasErrorBound l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError :=
  tendsto_zero_of_eventually_abs_le_bound
    biasCorrectionError biasErrorBound hbound hbound_tendsto

/--
Paired score-replication negligibility from eventual absolute bounds.
-/
theorem paired_bootstrapScoreReplicationErrorNegligible_of_eventually_abs_le_bound
    (leftScoreReplicationError rightScoreReplicationError
      leftScoreErrorBound rightScoreErrorBound : Index -> Real)
    (hleft_bound :
      ∀ᶠ index in l,
        |leftScoreReplicationError index| ≤ leftScoreErrorBound index)
    (hright_bound :
      ∀ᶠ index in l,
        |rightScoreReplicationError index| ≤ rightScoreErrorBound index)
    (hleft_bound_tendsto :
      Tendsto leftScoreErrorBound l (nhds 0))
    (hright_bound_tendsto :
      Tendsto rightScoreErrorBound l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
        (l := l) leftScoreReplicationError ∧
      bootstrapScoreReplicationErrorNegligible
        (l := l) rightScoreReplicationError :=
  ⟨bootstrapScoreReplicationErrorNegligible_of_eventually_abs_le_bound
      (l := l) leftScoreReplicationError leftScoreErrorBound hleft_bound
      hleft_bound_tendsto,
    bootstrapScoreReplicationErrorNegligible_of_eventually_abs_le_bound
      (l := l) rightScoreReplicationError rightScoreErrorBound hright_bound
      hright_bound_tendsto⟩

/--
Paired bias-correction negligibility from eventual absolute bounds.
-/
theorem paired_bootstrapBiasCorrectionErrorNegligible_of_eventually_abs_le_bound
    (leftBiasCorrectionError rightBiasCorrectionError
      leftBiasErrorBound rightBiasErrorBound : Index -> Real)
    (hleft_bound :
      ∀ᶠ index in l,
        |leftBiasCorrectionError index| ≤ leftBiasErrorBound index)
    (hright_bound :
      ∀ᶠ index in l,
        |rightBiasCorrectionError index| ≤ rightBiasErrorBound index)
    (hleft_bound_tendsto :
      Tendsto leftBiasErrorBound l (nhds 0))
    (hright_bound_tendsto :
      Tendsto rightBiasErrorBound l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
        (l := l) leftBiasCorrectionError ∧
      bootstrapBiasCorrectionErrorNegligible
        (l := l) rightBiasCorrectionError :=
  ⟨bootstrapBiasCorrectionErrorNegligible_of_eventually_abs_le_bound
      (l := l) leftBiasCorrectionError leftBiasErrorBound hleft_bound
      hleft_bound_tendsto,
    bootstrapBiasCorrectionErrorNegligible_of_eventually_abs_le_bound
      (l := l) rightBiasCorrectionError rightBiasErrorBound hright_bound
      hright_bound_tendsto⟩

/--
Actual bootstrap variance consistency from a linearized variance limit and
eventual deterministic bounds on the score-replication and bias-correction
errors.
-/
theorem tendsto_bootstrapVariance_of_eventual_error_bounds
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError scoreErrorBound biasErrorBound : Index -> Real)
    (varianceLimit : Real)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hlinearized :
      Tendsto linearizedVariance l (nhds varianceLimit))
    (hscore_bound :
      ∀ᶠ index in l,
        |scoreReplicationError index| ≤ scoreErrorBound index)
    (hscore_bound_tendsto :
      Tendsto scoreErrorBound l (nhds 0))
    (hbias_bound :
      ∀ᶠ index in l,
        |biasCorrectionError index| ≤ biasErrorBound index)
    (hbias_bound_tendsto :
      Tendsto biasErrorBound l (nhds 0)) :
    Tendsto actualVariance l (nhds varianceLimit) :=
  tendsto_bootstrapVariance_of_eventual_error_decomposition
    (l := l) linearizedVariance actualVariance scoreReplicationError
    biasCorrectionError varianceLimit herror_decomp hlinearized
    (bootstrapScoreReplicationErrorNegligible_of_eventually_abs_le_bound
      (l := l) scoreReplicationError scoreErrorBound hscore_bound
      hscore_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_eventually_abs_le_bound
      (l := l) biasCorrectionError biasErrorBound hbias_bound
      hbias_bound_tendsto)

/--
Bridge-form version of `tendsto_bootstrapVariance_of_eventual_error_bounds`.
-/
theorem actualBootstrapVarianceConsistent_of_eventual_error_bounds
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError scoreErrorBound biasErrorBound : Index -> Real)
    (varianceLimit : Real)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hlinearized :
      linearizedBootstrapVarianceConverges
        (l := l) linearizedVariance varianceLimit)
    (hscore_bound :
      ∀ᶠ index in l,
        |scoreReplicationError index| ≤ scoreErrorBound index)
    (hscore_bound_tendsto :
      Tendsto scoreErrorBound l (nhds 0))
    (hbias_bound :
      ∀ᶠ index in l,
        |biasCorrectionError index| ≤ biasErrorBound index)
    (hbias_bound_tendsto :
      Tendsto biasErrorBound l (nhds 0)) :
    actualBootstrapVarianceConsistent
      (l := l) actualVariance varianceLimit :=
  tendsto_bootstrapVariance_of_eventual_error_bounds
    (l := l) linearizedVariance actualVariance scoreReplicationError
    biasCorrectionError scoreErrorBound biasErrorBound varianceLimit
    herror_decomp hlinearized hscore_bound hscore_bound_tendsto
    hbias_bound hbias_bound_tendsto

/--
Paired actual bootstrap variance consistency from linearized variance limits
and eventual deterministic bounds on score-replication and bias-correction
errors.
-/
theorem paired_actualBootstrapVarianceConsistent_of_eventual_error_bounds
    (leftLinearizedVariance leftActualVariance leftScoreReplicationError
      leftBiasCorrectionError leftScoreErrorBound leftBiasErrorBound :
        Index -> Real)
    (rightLinearizedVariance rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError rightScoreErrorBound rightBiasErrorBound :
        Index -> Real)
    (leftVarianceLimit rightVarianceLimit : Real)
    (hleft_error_decomp :
      (fun index => leftActualVariance index - leftLinearizedVariance index)
        =ᶠ[l]
        (fun index =>
          leftScoreReplicationError index + leftBiasCorrectionError index))
    (hright_error_decomp :
      (fun index => rightActualVariance index - rightLinearizedVariance index)
        =ᶠ[l]
        (fun index =>
          rightScoreReplicationError index + rightBiasCorrectionError index))
    (hleft_linearized :
      linearizedBootstrapVarianceConverges
        (l := l) leftLinearizedVariance leftVarianceLimit)
    (hright_linearized :
      linearizedBootstrapVarianceConverges
        (l := l) rightLinearizedVariance rightVarianceLimit)
    (hleft_score_bound :
      ∀ᶠ index in l,
        |leftScoreReplicationError index| ≤ leftScoreErrorBound index)
    (hright_score_bound :
      ∀ᶠ index in l,
        |rightScoreReplicationError index| ≤ rightScoreErrorBound index)
    (hleft_score_bound_tendsto :
      Tendsto leftScoreErrorBound l (nhds 0))
    (hright_score_bound_tendsto :
      Tendsto rightScoreErrorBound l (nhds 0))
    (hleft_bias_bound :
      ∀ᶠ index in l,
        |leftBiasCorrectionError index| ≤ leftBiasErrorBound index)
    (hright_bias_bound :
      ∀ᶠ index in l,
        |rightBiasCorrectionError index| ≤ rightBiasErrorBound index)
    (hleft_bias_bound_tendsto :
      Tendsto leftBiasErrorBound l (nhds 0))
    (hright_bias_bound_tendsto :
      Tendsto rightBiasErrorBound l (nhds 0)) :
    actualBootstrapVarianceConsistent
        (l := l) leftActualVariance leftVarianceLimit ∧
      actualBootstrapVarianceConsistent
        (l := l) rightActualVariance rightVarianceLimit :=
  ⟨actualBootstrapVarianceConsistent_of_eventual_error_bounds
      (l := l) leftLinearizedVariance leftActualVariance
      leftScoreReplicationError leftBiasCorrectionError leftScoreErrorBound
      leftBiasErrorBound leftVarianceLimit hleft_error_decomp
      hleft_linearized hleft_score_bound hleft_score_bound_tendsto
      hleft_bias_bound hleft_bias_bound_tendsto,
    actualBootstrapVarianceConsistent_of_eventual_error_bounds
      (l := l) rightLinearizedVariance rightActualVariance
      rightScoreReplicationError rightBiasCorrectionError
      rightScoreErrorBound rightBiasErrorBound rightVarianceLimit
      hright_error_decomp hright_linearized hright_score_bound
      hright_score_bound_tendsto hright_bias_bound
      hright_bias_bound_tendsto⟩

/--
Score-replication error negligibility from a finite sum of component errors
whose absolute values are eventually bounded by component bounds that each
converge to zero.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (scoreReplicationError : Index -> Real)
    (scoreComponent scoreComponentBound : Index -> Component -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ components,
          scoreComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ components ->
          |scoreComponent index component| ≤
            scoreComponentBound index component)
    (hcomponent_bound_tendsto :
      ∀ component, component ∈ components ->
        Tendsto (fun index => scoreComponentBound index component)
          l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError := by
  have hsum_bound :
      ∀ᶠ index in l,
        |scoreReplicationError index| ≤
          ∑ component ∈ components, scoreComponentBound index component := by
    filter_upwards [hdecomp, hcomponent_bound] with index hdecomp_index
      hbound_index
    calc
      |scoreReplicationError index| =
          |∑ component ∈ components, scoreComponent index component| := by
            rw [hdecomp_index]
      _ ≤
          ∑ component ∈ components, |scoreComponent index component| :=
            Finset.abs_sum_le_sum_abs _ _
      _ ≤
          ∑ component ∈ components, scoreComponentBound index component :=
            Finset.sum_le_sum
              (fun component hcomponent =>
                hbound_index component hcomponent)
  have hsum_bound_tendsto :
      Tendsto
        (fun index =>
          ∑ component ∈ components, scoreComponentBound index component)
        l (nhds 0) := by
    simpa using
      tendsto_sum_cell_values_zero (l := l) components
        scoreComponentBound hcomponent_bound_tendsto
  exact
    bootstrapScoreReplicationErrorNegligible_of_eventually_abs_le_bound
      (l := l) scoreReplicationError
      (fun index =>
        ∑ component ∈ components, scoreComponentBound index component)
      hsum_bound hsum_bound_tendsto

/--
Bias-correction error negligibility from a finite sum of component errors whose
absolute values are eventually bounded by component bounds that each converge
to zero.
-/
theorem bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (biasCorrectionError : Index -> Real)
    (biasComponent biasComponentBound : Index -> Component -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ components,
          biasComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ components ->
          |biasComponent index component| ≤
            biasComponentBound index component)
    (hcomponent_bound_tendsto :
      ∀ component, component ∈ components ->
        Tendsto (fun index => biasComponentBound index component)
          l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError := by
  have hsum_bound :
      ∀ᶠ index in l,
        |biasCorrectionError index| ≤
          ∑ component ∈ components, biasComponentBound index component := by
    filter_upwards [hdecomp, hcomponent_bound] with index hdecomp_index
      hbound_index
    calc
      |biasCorrectionError index| =
          |∑ component ∈ components, biasComponent index component| := by
            rw [hdecomp_index]
      _ ≤
          ∑ component ∈ components, |biasComponent index component| :=
            Finset.abs_sum_le_sum_abs _ _
      _ ≤
          ∑ component ∈ components, biasComponentBound index component :=
            Finset.sum_le_sum
              (fun component hcomponent =>
                hbound_index component hcomponent)
  have hsum_bound_tendsto :
      Tendsto
        (fun index =>
          ∑ component ∈ components, biasComponentBound index component)
        l (nhds 0) := by
    simpa using
      tendsto_sum_cell_values_zero (l := l) components
        biasComponentBound hcomponent_bound_tendsto
  exact
    bootstrapBiasCorrectionErrorNegligible_of_eventually_abs_le_bound
      (l := l) biasCorrectionError
      (fun index =>
        ∑ component ∈ components, biasComponentBound index component)
      hsum_bound hsum_bound_tendsto

/--
Score-replication negligibility from a finite component decomposition and one
common component envelope.  This is the deterministic endpoint expected after
an empirical-process supremum bound has been proved for every component in the
finite family.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_finite_component_common_bound
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (scoreReplicationError : Index -> Real)
    (scoreComponent : Index -> Component -> Real)
    (scoreComponentBound : Index -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ components,
          scoreComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ components ->
          |scoreComponent index component| ≤ scoreComponentBound index)
    (hcomponent_bound_tendsto :
      Tendsto scoreComponentBound l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError :=
  bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
    (l := l) components scoreReplicationError scoreComponent
    (fun index _component => scoreComponentBound index) hdecomp
    hcomponent_bound
    (fun _component _hcomponent => hcomponent_bound_tendsto)

/--
Bias-correction negligibility from a finite component decomposition and one
common component envelope.  This keeps the algebraic decomposition explicit
while allowing a later empirical-process bound to control all components at
once.
-/
theorem bootstrapBiasCorrectionErrorNegligible_of_finite_component_common_bound
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (biasCorrectionError : Index -> Real)
    (biasComponent : Index -> Component -> Real)
    (biasComponentBound : Index -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ components,
          biasComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ components ->
          |biasComponent index component| ≤ biasComponentBound index)
    (hcomponent_bound_tendsto :
      Tendsto biasComponentBound l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError :=
  bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
    (l := l) components biasCorrectionError biasComponent
    (fun index _component => biasComponentBound index) hdecomp
    hcomponent_bound
    (fun _component _hcomponent => hcomponent_bound_tendsto)

/--
Actual-bootstrap score-replication convergence at `atTop` from a finite
component decomposition and componentwise bounds converging to zero.
-/
theorem tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_bounds
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (scoreReplicationError : ℕ -> Real)
    (scoreComponent scoreComponentBound : ℕ -> Component -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ components,
          scoreComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ components ->
          |scoreComponent index component| ≤
            scoreComponentBound index component)
    (hcomponent_bound_tendsto :
      ∀ component, component ∈ components ->
        Tendsto (fun index => scoreComponentBound index component)
          atTop (nhds 0)) :
    Tendsto scoreReplicationError atTop (nhds 0) :=
  bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
    (l := atTop) components scoreReplicationError scoreComponent
    scoreComponentBound hdecomp hcomponent_bound
    hcomponent_bound_tendsto

/--
Actual-bootstrap bias-correction convergence at `atTop` from a finite component
decomposition and componentwise bounds converging to zero.
-/
theorem tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_bounds
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (biasCorrectionError : ℕ -> Real)
    (biasComponent biasComponentBound : ℕ -> Component -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ components,
          biasComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ components ->
          |biasComponent index component| ≤
            biasComponentBound index component)
    (hcomponent_bound_tendsto :
      ∀ component, component ∈ components ->
        Tendsto (fun index => biasComponentBound index component)
          atTop (nhds 0)) :
    Tendsto biasCorrectionError atTop (nhds 0) :=
  bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
    (l := atTop) components biasCorrectionError biasComponent
    biasComponentBound hdecomp hcomponent_bound hcomponent_bound_tendsto

/--
Actual-bootstrap score-replication convergence at `atTop` from a finite
component decomposition controlled by one common envelope.
-/
theorem tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_common_bound
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (scoreReplicationError : ℕ -> Real)
    (scoreComponent : ℕ -> Component -> Real)
    (scoreComponentBound : ℕ -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ components,
          scoreComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ components ->
          |scoreComponent index component| ≤ scoreComponentBound index)
    (hcomponent_bound_tendsto :
      Tendsto scoreComponentBound atTop (nhds 0)) :
    Tendsto scoreReplicationError atTop (nhds 0) :=
  bootstrapScoreReplicationErrorNegligible_of_finite_component_common_bound
    (l := atTop) components scoreReplicationError scoreComponent
    scoreComponentBound hdecomp hcomponent_bound hcomponent_bound_tendsto

/--
Actual-bootstrap bias-correction convergence at `atTop` from a finite component
decomposition controlled by one common envelope.
-/
theorem tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_common_bound
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (biasCorrectionError : ℕ -> Real)
    (biasComponent : ℕ -> Component -> Real)
    (biasComponentBound : ℕ -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ components,
          biasComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ components ->
          |biasComponent index component| ≤ biasComponentBound index)
    (hcomponent_bound_tendsto :
      Tendsto biasComponentBound atTop (nhds 0)) :
    Tendsto biasCorrectionError atTop (nhds 0) :=
  bootstrapBiasCorrectionErrorNegligible_of_finite_component_common_bound
    (l := atTop) components biasCorrectionError biasComponent
    biasComponentBound hdecomp hcomponent_bound hcomponent_bound_tendsto

/--
Actual-bootstrap score-replication convergence at `atTop` from a finite
score-cell-by-component decomposition and componentwise bounds converging to
zero.
-/
theorem tendsto_actualBootstrapScoreReplicationError_zero_of_finite_score_cell_component_bounds
    {Cell Component : Type*} [DecidableEq Cell] [DecidableEq Component]
    (cells : Finset Cell)
    (components : Finset Component)
    (scoreReplicationError : ℕ -> Real)
    (scoreCellComponent scoreCellComponentBound :
      ℕ -> Cell -> Component -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
          scoreCellComponent index cell component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ components ->
            |scoreCellComponent index cell component| ≤
              scoreCellComponentBound index cell component)
    (hcomponent_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ components ->
          Tendsto (fun index => scoreCellComponentBound index cell component)
            atTop (nhds 0)) :
    Tendsto scoreReplicationError atTop (nhds 0) := by
  have hdecomp_product :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ pair ∈ cells.product components,
          scoreCellComponent index pair.1 pair.2) := by
    filter_upwards [hdecomp] with index hdecomp_index
    calc
      scoreReplicationError index =
          ∑ cell ∈ cells, ∑ component ∈ components,
            scoreCellComponent index cell component := hdecomp_index
      _ = ∑ pair ∈ cells.product components,
            scoreCellComponent index pair.1 pair.2 := by
          rw [← Finset.sum_product']
          rfl
  have hcomponent_bound_product :
      ∀ᶠ index in atTop,
        ∀ pair, pair ∈ cells.product components ->
          |scoreCellComponent index pair.1 pair.2| ≤
            scoreCellComponentBound index pair.1 pair.2 := by
    filter_upwards [hcomponent_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  exact
    tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_bounds
      (components := cells.product components) scoreReplicationError
      (fun index pair => scoreCellComponent index pair.1 pair.2)
      (fun index pair => scoreCellComponentBound index pair.1 pair.2)
      hdecomp_product hcomponent_bound_product
      (fun pair hpair => by
        rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
        exact hcomponent_bound_tendsto pair.1 hcell pair.2 hcomponent)

/--
Actual-bootstrap bias-correction convergence at `atTop` from a finite
score-cell-by-component decomposition and componentwise bounds converging to
zero.
-/
theorem tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_score_cell_component_bounds
    {Cell Component : Type*} [DecidableEq Cell] [DecidableEq Component]
    (cells : Finset Cell)
    (components : Finset Component)
    (biasCorrectionError : ℕ -> Real)
    (biasCellComponent biasCellComponentBound :
      ℕ -> Cell -> Component -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
          biasCellComponent index cell component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ components ->
            |biasCellComponent index cell component| ≤
              biasCellComponentBound index cell component)
    (hcomponent_bound_tendsto :
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ components ->
          Tendsto (fun index => biasCellComponentBound index cell component)
            atTop (nhds 0)) :
    Tendsto biasCorrectionError atTop (nhds 0) := by
  have hdecomp_product :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ pair ∈ cells.product components,
          biasCellComponent index pair.1 pair.2) := by
    filter_upwards [hdecomp] with index hdecomp_index
    calc
      biasCorrectionError index =
          ∑ cell ∈ cells, ∑ component ∈ components,
            biasCellComponent index cell component := hdecomp_index
      _ = ∑ pair ∈ cells.product components,
            biasCellComponent index pair.1 pair.2 := by
          rw [← Finset.sum_product']
          rfl
  have hcomponent_bound_product :
      ∀ᶠ index in atTop,
        ∀ pair, pair ∈ cells.product components ->
          |biasCellComponent index pair.1 pair.2| ≤
            biasCellComponentBound index pair.1 pair.2 := by
    filter_upwards [hcomponent_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  exact
    tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_bounds
      (components := cells.product components) biasCorrectionError
      (fun index pair => biasCellComponent index pair.1 pair.2)
      (fun index pair => biasCellComponentBound index pair.1 pair.2)
      hdecomp_product hcomponent_bound_product
      (fun pair hpair => by
        rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
        exact hcomponent_bound_tendsto pair.1 hcell pair.2 hcomponent)

/--
Paired actual-bootstrap score-replication convergence at `atTop` from finite
component decompositions controlled by common envelopes on each side.
-/
theorem paired_tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_common_bound
    {Component : Type*} [DecidableEq Component]
    (leftComponents rightComponents : Finset Component)
    (leftScoreReplicationError rightScoreReplicationError : ℕ -> Real)
    (leftScoreComponent rightScoreComponent : ℕ -> Component -> Real)
    (leftScoreComponentBound rightScoreComponentBound : ℕ -> Real)
    (hleft_decomp :
      leftScoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ leftComponents,
          leftScoreComponent index component))
    (hright_decomp :
      rightScoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ rightComponents,
          rightScoreComponent index component))
    (hleft_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ leftComponents ->
          |leftScoreComponent index component| ≤
            leftScoreComponentBound index)
    (hright_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ rightComponents ->
          |rightScoreComponent index component| ≤
            rightScoreComponentBound index)
    (hleft_component_bound_tendsto :
      Tendsto leftScoreComponentBound atTop (nhds 0))
    (hright_component_bound_tendsto :
      Tendsto rightScoreComponentBound atTop (nhds 0)) :
    Tendsto leftScoreReplicationError atTop (nhds 0) ∧
      Tendsto rightScoreReplicationError atTop (nhds 0) :=
  ⟨tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_common_bound
      leftComponents leftScoreReplicationError leftScoreComponent
      leftScoreComponentBound hleft_decomp hleft_component_bound
      hleft_component_bound_tendsto,
    tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_common_bound
      rightComponents rightScoreReplicationError rightScoreComponent
      rightScoreComponentBound hright_decomp hright_component_bound
      hright_component_bound_tendsto⟩

/--
Paired actual-bootstrap bias-correction convergence at `atTop` from finite
component decompositions controlled by common envelopes on each side.
-/
theorem paired_tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_common_bound
    {Component : Type*} [DecidableEq Component]
    (leftComponents rightComponents : Finset Component)
    (leftBiasCorrectionError rightBiasCorrectionError : ℕ -> Real)
    (leftBiasComponent rightBiasComponent : ℕ -> Component -> Real)
    (leftBiasComponentBound rightBiasComponentBound : ℕ -> Real)
    (hleft_decomp :
      leftBiasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ leftComponents,
          leftBiasComponent index component))
    (hright_decomp :
      rightBiasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ rightComponents,
          rightBiasComponent index component))
    (hleft_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ leftComponents ->
          |leftBiasComponent index component| ≤
            leftBiasComponentBound index)
    (hright_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ rightComponents ->
          |rightBiasComponent index component| ≤
            rightBiasComponentBound index)
    (hleft_component_bound_tendsto :
      Tendsto leftBiasComponentBound atTop (nhds 0))
    (hright_component_bound_tendsto :
      Tendsto rightBiasComponentBound atTop (nhds 0)) :
    Tendsto leftBiasCorrectionError atTop (nhds 0) ∧
      Tendsto rightBiasCorrectionError atTop (nhds 0) :=
  ⟨tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_common_bound
      leftComponents leftBiasCorrectionError leftBiasComponent
      leftBiasComponentBound hleft_decomp hleft_component_bound
      hleft_component_bound_tendsto,
    tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_common_bound
      rightComponents rightBiasCorrectionError rightBiasComponent
      rightBiasComponentBound hright_decomp hright_component_bound
      hright_component_bound_tendsto⟩

/--
Actual bootstrap variance consistency when the score-replication and
bias-correction errors each decompose into finite component sums with
componentwise bounds converging to zero.
-/
theorem tendsto_bootstrapVariance_of_finite_component_error_bounds
    {ScoreComponent BiasComponent : Type*}
    [DecidableEq ScoreComponent] [DecidableEq BiasComponent]
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (scoreComponent scoreComponentBound : Index -> ScoreComponent -> Real)
    (biasComponent biasComponentBound : Index -> BiasComponent -> Real)
    (varianceLimit : Real)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hlinearized :
      Tendsto linearizedVariance l (nhds varianceLimit))
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreComponents,
          scoreComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreComponents ->
          |scoreComponent index component| ≤
            scoreComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasComponent index component| ≤
            biasComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasComponentBound index component)
          l (nhds 0)) :
    Tendsto actualVariance l (nhds varianceLimit) :=
  tendsto_bootstrapVariance_of_eventual_error_decomposition
    (l := l) linearizedVariance actualVariance scoreReplicationError
    biasCorrectionError varianceLimit herror_decomp hlinearized
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) scoreComponents scoreReplicationError scoreComponent
      scoreComponentBound hscore_decomp hscore_component_bound
      hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) biasComponents biasCorrectionError biasComponent
      biasComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Paired score-replication negligibility from finite component decompositions
and componentwise bounds converging to zero.
-/
theorem paired_bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
    {Component : Type*} [DecidableEq Component]
    (leftComponents rightComponents : Finset Component)
    (leftScoreReplicationError rightScoreReplicationError : Index -> Real)
    (leftScoreComponent leftScoreComponentBound
      rightScoreComponent rightScoreComponentBound :
        Index -> Component -> Real)
    (hleft_decomp :
      leftScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ leftComponents,
          leftScoreComponent index component))
    (hright_decomp :
      rightScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ rightComponents,
          rightScoreComponent index component))
    (hleft_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftComponents ->
          |leftScoreComponent index component| ≤
            leftScoreComponentBound index component)
    (hright_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightComponents ->
          |rightScoreComponent index component| ≤
            rightScoreComponentBound index component)
    (hleft_component_bound_tendsto :
      ∀ component, component ∈ leftComponents ->
        Tendsto (fun index => leftScoreComponentBound index component)
          l (nhds 0))
    (hright_component_bound_tendsto :
      ∀ component, component ∈ rightComponents ->
        Tendsto (fun index => rightScoreComponentBound index component)
          l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
        (l := l) leftScoreReplicationError ∧
      bootstrapScoreReplicationErrorNegligible
        (l := l) rightScoreReplicationError :=
  ⟨bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) leftComponents leftScoreReplicationError
      leftScoreComponent leftScoreComponentBound hleft_decomp
      hleft_component_bound hleft_component_bound_tendsto,
    bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
      (l := l) rightComponents rightScoreReplicationError
      rightScoreComponent rightScoreComponentBound hright_decomp
      hright_component_bound hright_component_bound_tendsto⟩

/--
Paired bias-correction negligibility from finite component decompositions and
componentwise bounds converging to zero.
-/
theorem paired_bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
    {Component : Type*} [DecidableEq Component]
    (leftComponents rightComponents : Finset Component)
    (leftBiasCorrectionError rightBiasCorrectionError : Index -> Real)
    (leftBiasComponent leftBiasComponentBound
      rightBiasComponent rightBiasComponentBound :
        Index -> Component -> Real)
    (hleft_decomp :
      leftBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ leftComponents,
          leftBiasComponent index component))
    (hright_decomp :
      rightBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ rightComponents,
          rightBiasComponent index component))
    (hleft_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftComponents ->
          |leftBiasComponent index component| ≤
            leftBiasComponentBound index component)
    (hright_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightComponents ->
          |rightBiasComponent index component| ≤
            rightBiasComponentBound index component)
    (hleft_component_bound_tendsto :
      ∀ component, component ∈ leftComponents ->
        Tendsto (fun index => leftBiasComponentBound index component)
          l (nhds 0))
    (hright_component_bound_tendsto :
      ∀ component, component ∈ rightComponents ->
        Tendsto (fun index => rightBiasComponentBound index component)
          l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
        (l := l) leftBiasCorrectionError ∧
      bootstrapBiasCorrectionErrorNegligible
        (l := l) rightBiasCorrectionError :=
  ⟨bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) leftComponents leftBiasCorrectionError leftBiasComponent
      leftBiasComponentBound hleft_decomp hleft_component_bound
      hleft_component_bound_tendsto,
    bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
      (l := l) rightComponents rightBiasCorrectionError
      rightBiasComponent rightBiasComponentBound hright_decomp
      hright_component_bound hright_component_bound_tendsto⟩

/--
Bridge-form actual bootstrap variance consistency from finite component error
decompositions and componentwise bounds converging to zero.
-/
theorem actualBootstrapVarianceConsistent_of_finite_component_error_bounds
    {ScoreComponent BiasComponent : Type*}
    [DecidableEq ScoreComponent] [DecidableEq BiasComponent]
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (scoreComponent scoreComponentBound : Index -> ScoreComponent -> Real)
    (biasComponent biasComponentBound : Index -> BiasComponent -> Real)
    (varianceLimit : Real)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hlinearized :
      linearizedBootstrapVarianceConverges
        (l := l) linearizedVariance varianceLimit)
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreComponents,
          scoreComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreComponents ->
          |scoreComponent index component| ≤
            scoreComponentBound index component)
    (hscore_component_bound_tendsto :
      ∀ component, component ∈ scoreComponents ->
        Tendsto (fun index => scoreComponentBound index component)
          l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasComponent index component| ≤
            biasComponentBound index component)
    (hbias_component_bound_tendsto :
      ∀ component, component ∈ biasComponents ->
        Tendsto (fun index => biasComponentBound index component)
          l (nhds 0)) :
    actualBootstrapVarianceConsistent
      (l := l) actualVariance varianceLimit :=
  tendsto_bootstrapVariance_of_finite_component_error_bounds
    (l := l) scoreComponents biasComponents linearizedVariance
    actualVariance scoreReplicationError biasCorrectionError scoreComponent
    scoreComponentBound biasComponent biasComponentBound varianceLimit
    herror_decomp hlinearized hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Actual bootstrap variance consistency from finite component decompositions when
one common score envelope and one common bias envelope control all components.
-/
theorem tendsto_bootstrapVariance_of_finite_component_common_error_bounds
    {ScoreComponent BiasComponent : Type*}
    [DecidableEq ScoreComponent] [DecidableEq BiasComponent]
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (scoreComponent : Index -> ScoreComponent -> Real)
    (biasComponent : Index -> BiasComponent -> Real)
    (scoreComponentBound biasComponentBound : Index -> Real)
    (varianceLimit : Real)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hlinearized :
      Tendsto linearizedVariance l (nhds varianceLimit))
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreComponents,
          scoreComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreComponents ->
          |scoreComponent index component| ≤ scoreComponentBound index)
    (hscore_component_bound_tendsto :
      Tendsto scoreComponentBound l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasComponent index component| ≤ biasComponentBound index)
    (hbias_component_bound_tendsto :
      Tendsto biasComponentBound l (nhds 0)) :
    Tendsto actualVariance l (nhds varianceLimit) :=
  tendsto_bootstrapVariance_of_eventual_error_decomposition
    (l := l) linearizedVariance actualVariance scoreReplicationError
    biasCorrectionError varianceLimit herror_decomp hlinearized
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_common_bound
      (l := l) scoreComponents scoreReplicationError scoreComponent
      scoreComponentBound hscore_decomp hscore_component_bound
      hscore_component_bound_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_common_bound
      (l := l) biasComponents biasCorrectionError biasComponent
      biasComponentBound hbias_decomp hbias_component_bound
      hbias_component_bound_tendsto)

/--
Bridge-form actual bootstrap variance consistency from finite component
decompositions controlled by one common score envelope and one common bias
envelope.
-/
theorem actualBootstrapVarianceConsistent_of_finite_component_common_error_bounds
    {ScoreComponent BiasComponent : Type*}
    [DecidableEq ScoreComponent] [DecidableEq BiasComponent]
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (scoreComponent : Index -> ScoreComponent -> Real)
    (biasComponent : Index -> BiasComponent -> Real)
    (scoreComponentBound biasComponentBound : Index -> Real)
    (varianceLimit : Real)
    (herror_decomp :
      (fun index => actualVariance index - linearizedVariance index) =ᶠ[l]
        (fun index =>
          scoreReplicationError index + biasCorrectionError index))
    (hlinearized :
      linearizedBootstrapVarianceConverges
        (l := l) linearizedVariance varianceLimit)
    (hscore_decomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ scoreComponents,
          scoreComponent index component))
    (hscore_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ scoreComponents ->
          |scoreComponent index component| ≤ scoreComponentBound index)
    (hscore_component_bound_tendsto :
      Tendsto scoreComponentBound l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasComponent index component| ≤ biasComponentBound index)
    (hbias_component_bound_tendsto :
      Tendsto biasComponentBound l (nhds 0)) :
    actualBootstrapVarianceConsistent
      (l := l) actualVariance varianceLimit :=
  tendsto_bootstrapVariance_of_finite_component_common_error_bounds
    (l := l) scoreComponents biasComponents linearizedVariance
    actualVariance scoreReplicationError biasCorrectionError scoreComponent
    biasComponent scoreComponentBound biasComponentBound varianceLimit
    herror_decomp hlinearized hscore_decomp hscore_component_bound
    hscore_component_bound_tendsto hbias_decomp hbias_component_bound
    hbias_component_bound_tendsto

/--
Paired bridge-form actual bootstrap variance consistency from finite component
score-replication and bias-correction error bounds.
-/
theorem paired_actualBootstrapVarianceConsistent_of_finite_component_error_bounds
    {LeftScoreComponent RightScoreComponent LeftBiasComponent
      RightBiasComponent : Type*}
    [DecidableEq LeftScoreComponent] [DecidableEq RightScoreComponent]
    [DecidableEq LeftBiasComponent] [DecidableEq RightBiasComponent]
    (leftScoreComponents : Finset LeftScoreComponent)
    (rightScoreComponents : Finset RightScoreComponent)
    (leftBiasComponents : Finset LeftBiasComponent)
    (rightBiasComponents : Finset RightBiasComponent)
    (leftLinearizedVariance leftActualVariance leftScoreReplicationError
      leftBiasCorrectionError : Index -> Real)
    (rightLinearizedVariance rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError : Index -> Real)
    (leftScoreComponent leftScoreComponentBound :
      Index -> LeftScoreComponent -> Real)
    (rightScoreComponent rightScoreComponentBound :
      Index -> RightScoreComponent -> Real)
    (leftBiasComponent leftBiasComponentBound :
      Index -> LeftBiasComponent -> Real)
    (rightBiasComponent rightBiasComponentBound :
      Index -> RightBiasComponent -> Real)
    (leftVarianceLimit rightVarianceLimit : Real)
    (hleft_error_decomp :
      (fun index => leftActualVariance index - leftLinearizedVariance index)
        =ᶠ[l]
        (fun index =>
          leftScoreReplicationError index + leftBiasCorrectionError index))
    (hright_error_decomp :
      (fun index => rightActualVariance index - rightLinearizedVariance index)
        =ᶠ[l]
        (fun index =>
          rightScoreReplicationError index + rightBiasCorrectionError index))
    (hleft_linearized :
      linearizedBootstrapVarianceConverges
        (l := l) leftLinearizedVariance leftVarianceLimit)
    (hright_linearized :
      linearizedBootstrapVarianceConverges
        (l := l) rightLinearizedVariance rightVarianceLimit)
    (hleft_score_decomp :
      leftScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ leftScoreComponents,
          leftScoreComponent index component))
    (hright_score_decomp :
      rightScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ rightScoreComponents,
          rightScoreComponent index component))
    (hleft_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftScoreComponents ->
          |leftScoreComponent index component| ≤
            leftScoreComponentBound index component)
    (hright_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightScoreComponents ->
          |rightScoreComponent index component| ≤
            rightScoreComponentBound index component)
    (hleft_score_component_bound_tendsto :
      ∀ component, component ∈ leftScoreComponents ->
        Tendsto (fun index => leftScoreComponentBound index component)
          l (nhds 0))
    (hright_score_component_bound_tendsto :
      ∀ component, component ∈ rightScoreComponents ->
        Tendsto (fun index => rightScoreComponentBound index component)
          l (nhds 0))
    (hleft_bias_decomp :
      leftBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ leftBiasComponents,
          leftBiasComponent index component))
    (hright_bias_decomp :
      rightBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ rightBiasComponents,
          rightBiasComponent index component))
    (hleft_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftBiasComponents ->
          |leftBiasComponent index component| ≤
            leftBiasComponentBound index component)
    (hright_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightBiasComponents ->
          |rightBiasComponent index component| ≤
            rightBiasComponentBound index component)
    (hleft_bias_component_bound_tendsto :
      ∀ component, component ∈ leftBiasComponents ->
        Tendsto (fun index => leftBiasComponentBound index component)
          l (nhds 0))
    (hright_bias_component_bound_tendsto :
      ∀ component, component ∈ rightBiasComponents ->
        Tendsto (fun index => rightBiasComponentBound index component)
          l (nhds 0)) :
    actualBootstrapVarianceConsistent
        (l := l) leftActualVariance leftVarianceLimit ∧
      actualBootstrapVarianceConsistent
        (l := l) rightActualVariance rightVarianceLimit :=
  ⟨actualBootstrapVarianceConsistent_of_finite_component_error_bounds
      (l := l) leftScoreComponents leftBiasComponents
      leftLinearizedVariance leftActualVariance leftScoreReplicationError
      leftBiasCorrectionError leftScoreComponent leftScoreComponentBound
      leftBiasComponent leftBiasComponentBound leftVarianceLimit
      hleft_error_decomp hleft_linearized hleft_score_decomp
      hleft_score_component_bound hleft_score_component_bound_tendsto
      hleft_bias_decomp hleft_bias_component_bound
      hleft_bias_component_bound_tendsto,
    actualBootstrapVarianceConsistent_of_finite_component_error_bounds
      (l := l) rightScoreComponents rightBiasComponents
      rightLinearizedVariance rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError rightScoreComponent rightScoreComponentBound
      rightBiasComponent rightBiasComponentBound rightVarianceLimit
      hright_error_decomp hright_linearized hright_score_decomp
      hright_score_component_bound hright_score_component_bound_tendsto
      hright_bias_decomp hright_bias_component_bound
      hright_bias_component_bound_tendsto⟩

end WDSM
end Matching
end StatInference
