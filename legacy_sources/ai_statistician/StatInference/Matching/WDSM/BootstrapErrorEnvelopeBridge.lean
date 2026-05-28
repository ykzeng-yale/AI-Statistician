import StatInference.Matching.WDSM.BootstrapErrorBoundBridge

/-!
# Bootstrap finite-component error envelopes

`BootstrapErrorBoundBridge` proves negligibility from componentwise bounds whose
individual limits are zero.  In concrete WDSM work those componentwise limits
often come from one common stochastic or deterministic envelope multiplied by
fixed component constants.  This module records that reduction, keeping the
probability input as the single envelope convergence statement.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index : Type*} {l : Filter Index}

/--
Score-replication error negligibility from a finite component decomposition
whose components are eventually bounded by fixed component scales times one
shrinking envelope.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_finite_component_envelope_bounds
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (scoreReplicationError : Index -> Real)
    (scoreComponent : Index -> Component -> Real)
    (componentScale : Component -> Real)
    (envelope : Index -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ components,
          scoreComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ components ->
          |scoreComponent index component| ≤
            componentScale component * envelope index)
    (henvelope_tendsto :
      Tendsto envelope l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError :=
  bootstrapScoreReplicationErrorNegligible_of_finite_component_bounds
    (l := l) components scoreReplicationError scoreComponent
    (fun index component => componentScale component * envelope index)
    hdecomp hcomponent_bound
    (fun component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : Index => componentScale component) l
            (nhds (componentScale component))).mul henvelope_tendsto))

/--
Paired score-replication negligibility from finite component decompositions
controlled by shrinking envelopes.
-/
theorem paired_bootstrapScoreReplicationErrorNegligible_of_finite_component_envelope_bounds
    {LeftComponent RightComponent : Type*}
    [DecidableEq LeftComponent] [DecidableEq RightComponent]
    (leftComponents : Finset LeftComponent)
    (rightComponents : Finset RightComponent)
    (leftScoreReplicationError rightScoreReplicationError : Index -> Real)
    (leftScoreComponent : Index -> LeftComponent -> Real)
    (rightScoreComponent : Index -> RightComponent -> Real)
    (leftComponentScale : LeftComponent -> Real)
    (rightComponentScale : RightComponent -> Real)
    (leftEnvelope rightEnvelope : Index -> Real)
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
            leftComponentScale component * leftEnvelope index)
    (hright_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightComponents ->
          |rightScoreComponent index component| ≤
            rightComponentScale component * rightEnvelope index)
    (hleft_envelope_tendsto :
      Tendsto leftEnvelope l (nhds 0))
    (hright_envelope_tendsto :
      Tendsto rightEnvelope l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
        (l := l) leftScoreReplicationError ∧
      bootstrapScoreReplicationErrorNegligible
        (l := l) rightScoreReplicationError :=
  ⟨bootstrapScoreReplicationErrorNegligible_of_finite_component_envelope_bounds
      (l := l) leftComponents leftScoreReplicationError
      leftScoreComponent leftComponentScale leftEnvelope hleft_decomp
      hleft_component_bound hleft_envelope_tendsto,
    bootstrapScoreReplicationErrorNegligible_of_finite_component_envelope_bounds
      (l := l) rightComponents rightScoreReplicationError
      rightScoreComponent rightComponentScale rightEnvelope hright_decomp
      hright_component_bound hright_envelope_tendsto⟩

/--
Bias-correction error negligibility from a finite component decomposition whose
components are eventually bounded by fixed component scales times one
shrinking envelope.
-/
theorem bootstrapBiasCorrectionErrorNegligible_of_finite_component_envelope_bounds
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (biasCorrectionError : Index -> Real)
    (biasComponent : Index -> Component -> Real)
    (componentScale : Component -> Real)
    (envelope : Index -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ components,
          biasComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ components ->
          |biasComponent index component| ≤
            componentScale component * envelope index)
    (henvelope_tendsto :
      Tendsto envelope l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError :=
  bootstrapBiasCorrectionErrorNegligible_of_finite_component_bounds
    (l := l) components biasCorrectionError biasComponent
    (fun index component => componentScale component * envelope index)
    hdecomp hcomponent_bound
    (fun component _hcomponent => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : Index => componentScale component) l
            (nhds (componentScale component))).mul henvelope_tendsto))

/--
Paired bias-correction negligibility from finite component decompositions
controlled by shrinking envelopes.
-/
theorem paired_bootstrapBiasCorrectionErrorNegligible_of_finite_component_envelope_bounds
    {LeftComponent RightComponent : Type*}
    [DecidableEq LeftComponent] [DecidableEq RightComponent]
    (leftComponents : Finset LeftComponent)
    (rightComponents : Finset RightComponent)
    (leftBiasCorrectionError rightBiasCorrectionError : Index -> Real)
    (leftBiasComponent : Index -> LeftComponent -> Real)
    (rightBiasComponent : Index -> RightComponent -> Real)
    (leftComponentScale : LeftComponent -> Real)
    (rightComponentScale : RightComponent -> Real)
    (leftEnvelope rightEnvelope : Index -> Real)
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
            leftComponentScale component * leftEnvelope index)
    (hright_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightComponents ->
          |rightBiasComponent index component| ≤
            rightComponentScale component * rightEnvelope index)
    (hleft_envelope_tendsto :
      Tendsto leftEnvelope l (nhds 0))
    (hright_envelope_tendsto :
      Tendsto rightEnvelope l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
        (l := l) leftBiasCorrectionError ∧
      bootstrapBiasCorrectionErrorNegligible
        (l := l) rightBiasCorrectionError :=
  ⟨bootstrapBiasCorrectionErrorNegligible_of_finite_component_envelope_bounds
      (l := l) leftComponents leftBiasCorrectionError leftBiasComponent
      leftComponentScale leftEnvelope hleft_decomp hleft_component_bound
      hleft_envelope_tendsto,
    bootstrapBiasCorrectionErrorNegligible_of_finite_component_envelope_bounds
      (l := l) rightComponents rightBiasCorrectionError rightBiasComponent
      rightComponentScale rightEnvelope hright_decomp hright_component_bound
      hright_envelope_tendsto⟩

/--
Actual-bootstrap score-replication convergence at `atTop` from a finite
component decomposition controlled by fixed component scales times one
shrinking envelope.
-/
theorem tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_envelope_bounds
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (scoreReplicationError : ℕ -> Real)
    (scoreComponent : ℕ -> Component -> Real)
    (componentScale : Component -> Real)
    (envelope : ℕ -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ component ∈ components,
          scoreComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ components ->
          |scoreComponent index component| ≤
            componentScale component * envelope index)
    (henvelope_tendsto :
      Tendsto envelope atTop (nhds 0)) :
    Tendsto scoreReplicationError atTop (nhds 0) :=
  bootstrapScoreReplicationErrorNegligible_of_finite_component_envelope_bounds
    (l := atTop) components scoreReplicationError scoreComponent
    componentScale envelope hdecomp hcomponent_bound henvelope_tendsto

/--
Actual-bootstrap bias-correction convergence at `atTop` from a finite component
decomposition controlled by fixed component scales times one shrinking
envelope.
-/
theorem tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_envelope_bounds
    {Component : Type*} [DecidableEq Component]
    (components : Finset Component)
    (biasCorrectionError : ℕ -> Real)
    (biasComponent : ℕ -> Component -> Real)
    (componentScale : Component -> Real)
    (envelope : ℕ -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ component ∈ components,
          biasComponent index component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ components ->
          |biasComponent index component| ≤
            componentScale component * envelope index)
    (henvelope_tendsto :
      Tendsto envelope atTop (nhds 0)) :
    Tendsto biasCorrectionError atTop (nhds 0) :=
  bootstrapBiasCorrectionErrorNegligible_of_finite_component_envelope_bounds
    (l := atTop) components biasCorrectionError biasComponent
    componentScale envelope hdecomp hcomponent_bound henvelope_tendsto

/--
Score-replication error negligibility from a finite score-cell-by-component
decomposition whose components are bounded by fixed cell-component scales times
one shrinking envelope.
-/
theorem bootstrapScoreReplicationErrorNegligible_of_finite_score_cell_component_envelope_bounds
    {Cell Component : Type*} [DecidableEq Cell] [DecidableEq Component]
    (cells : Finset Cell)
    (components : Finset Component)
    (scoreReplicationError : Index -> Real)
    (scoreCellComponent : Index -> Cell -> Component -> Real)
    (componentScale : Cell -> Component -> Real)
    (envelope : Index -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[l]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
          scoreCellComponent index cell component))
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ components ->
            |scoreCellComponent index cell component| ≤
              componentScale cell component * envelope index)
    (henvelope_tendsto :
      Tendsto envelope l (nhds 0)) :
    bootstrapScoreReplicationErrorNegligible
      (l := l) scoreReplicationError := by
  have hdecomp_product :
      scoreReplicationError =ᶠ[l]
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
      ∀ᶠ index in l,
        ∀ pair, pair ∈ cells.product components ->
          |scoreCellComponent index pair.1 pair.2| ≤
            componentScale pair.1 pair.2 * envelope index := by
    filter_upwards [hcomponent_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  exact
    bootstrapScoreReplicationErrorNegligible_of_finite_component_envelope_bounds
      (l := l) (cells.product components) scoreReplicationError
      (fun index pair => scoreCellComponent index pair.1 pair.2)
      (fun pair => componentScale pair.1 pair.2) envelope
      hdecomp_product hcomponent_bound_product henvelope_tendsto

/--
Bias-correction error negligibility from a finite score-cell-by-component
decomposition whose components are bounded by fixed cell-component scales times
one shrinking envelope.
-/
theorem bootstrapBiasCorrectionErrorNegligible_of_finite_score_cell_component_envelope_bounds
    {Cell Component : Type*} [DecidableEq Cell] [DecidableEq Component]
    (cells : Finset Cell)
    (components : Finset Component)
    (biasCorrectionError : Index -> Real)
    (biasCellComponent : Index -> Cell -> Component -> Real)
    (componentScale : Cell -> Component -> Real)
    (envelope : Index -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
          biasCellComponent index cell component))
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ components ->
            |biasCellComponent index cell component| ≤
              componentScale cell component * envelope index)
    (henvelope_tendsto :
      Tendsto envelope l (nhds 0)) :
    bootstrapBiasCorrectionErrorNegligible
      (l := l) biasCorrectionError := by
  have hdecomp_product :
      biasCorrectionError =ᶠ[l]
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
      ∀ᶠ index in l,
        ∀ pair, pair ∈ cells.product components ->
          |biasCellComponent index pair.1 pair.2| ≤
            componentScale pair.1 pair.2 * envelope index := by
    filter_upwards [hcomponent_bound] with index hbound pair hpair
    rcases Finset.mem_product.mp hpair with ⟨hcell, hcomponent⟩
    exact hbound pair.1 hcell pair.2 hcomponent
  exact
    bootstrapBiasCorrectionErrorNegligible_of_finite_component_envelope_bounds
      (l := l) (cells.product components) biasCorrectionError
      (fun index pair => biasCellComponent index pair.1 pair.2)
      (fun pair => componentScale pair.1 pair.2) envelope
      hdecomp_product hcomponent_bound_product henvelope_tendsto

/--
Actual-bootstrap score-replication convergence at `atTop` from a finite
score-cell-by-component decomposition controlled by fixed cell-component
scales times one shrinking envelope.
-/
theorem tendsto_actualBootstrapScoreReplicationError_zero_of_finite_score_cell_component_envelope_bounds
    {Cell Component : Type*} [DecidableEq Cell] [DecidableEq Component]
    (cells : Finset Cell)
    (components : Finset Component)
    (scoreReplicationError : ℕ -> Real)
    (scoreCellComponent : ℕ -> Cell -> Component -> Real)
    (componentScale : Cell -> Component -> Real)
    (envelope : ℕ -> Real)
    (hdecomp :
      scoreReplicationError =ᶠ[atTop]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
          scoreCellComponent index cell component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ components ->
            |scoreCellComponent index cell component| ≤
              componentScale cell component * envelope index)
    (henvelope_tendsto :
      Tendsto envelope atTop (nhds 0)) :
    Tendsto scoreReplicationError atTop (nhds 0) :=
  bootstrapScoreReplicationErrorNegligible_of_finite_score_cell_component_envelope_bounds
    (l := atTop) cells components scoreReplicationError scoreCellComponent
    componentScale envelope hdecomp hcomponent_bound henvelope_tendsto

/--
Actual-bootstrap bias-correction convergence at `atTop` from a finite
score-cell-by-component decomposition controlled by fixed cell-component
scales times one shrinking envelope.
-/
theorem tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_score_cell_component_envelope_bounds
    {Cell Component : Type*} [DecidableEq Cell] [DecidableEq Component]
    (cells : Finset Cell)
    (components : Finset Component)
    (biasCorrectionError : ℕ -> Real)
    (biasCellComponent : ℕ -> Cell -> Component -> Real)
    (componentScale : Cell -> Component -> Real)
    (envelope : ℕ -> Real)
    (hdecomp :
      biasCorrectionError =ᶠ[atTop]
        (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
          biasCellComponent index cell component))
    (hcomponent_bound :
      ∀ᶠ index in atTop,
        ∀ cell, cell ∈ cells ->
          ∀ component, component ∈ components ->
            |biasCellComponent index cell component| ≤
              componentScale cell component * envelope index)
    (henvelope_tendsto :
      Tendsto envelope atTop (nhds 0)) :
    Tendsto biasCorrectionError atTop (nhds 0) :=
  bootstrapBiasCorrectionErrorNegligible_of_finite_score_cell_component_envelope_bounds
    (l := atTop) cells components biasCorrectionError biasCellComponent
    componentScale envelope hdecomp hcomponent_bound henvelope_tendsto

/--
Paired actual-bootstrap score-replication convergence at `atTop` from finite
component decompositions controlled by shrinking envelopes.
-/
theorem paired_tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_envelope_bounds
    {LeftComponent RightComponent : Type*}
    [DecidableEq LeftComponent] [DecidableEq RightComponent]
    (leftComponents : Finset LeftComponent)
    (rightComponents : Finset RightComponent)
    (leftScoreReplicationError rightScoreReplicationError : ℕ -> Real)
    (leftScoreComponent : ℕ -> LeftComponent -> Real)
    (rightScoreComponent : ℕ -> RightComponent -> Real)
    (leftComponentScale : LeftComponent -> Real)
    (rightComponentScale : RightComponent -> Real)
    (leftEnvelope rightEnvelope : ℕ -> Real)
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
            leftComponentScale component * leftEnvelope index)
    (hright_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ rightComponents ->
          |rightScoreComponent index component| ≤
            rightComponentScale component * rightEnvelope index)
    (hleft_envelope_tendsto :
      Tendsto leftEnvelope atTop (nhds 0))
    (hright_envelope_tendsto :
      Tendsto rightEnvelope atTop (nhds 0)) :
    Tendsto leftScoreReplicationError atTop (nhds 0) ∧
      Tendsto rightScoreReplicationError atTop (nhds 0) :=
  ⟨tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_envelope_bounds
      leftComponents leftScoreReplicationError leftScoreComponent
      leftComponentScale leftEnvelope hleft_decomp hleft_component_bound
      hleft_envelope_tendsto,
    tendsto_actualBootstrapScoreReplicationError_zero_of_finite_component_envelope_bounds
      rightComponents rightScoreReplicationError rightScoreComponent
      rightComponentScale rightEnvelope hright_decomp hright_component_bound
      hright_envelope_tendsto⟩

/--
Paired actual-bootstrap bias-correction convergence at `atTop` from finite
component decompositions controlled by shrinking envelopes.
-/
theorem paired_tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_envelope_bounds
    {LeftComponent RightComponent : Type*}
    [DecidableEq LeftComponent] [DecidableEq RightComponent]
    (leftComponents : Finset LeftComponent)
    (rightComponents : Finset RightComponent)
    (leftBiasCorrectionError rightBiasCorrectionError : ℕ -> Real)
    (leftBiasComponent : ℕ -> LeftComponent -> Real)
    (rightBiasComponent : ℕ -> RightComponent -> Real)
    (leftComponentScale : LeftComponent -> Real)
    (rightComponentScale : RightComponent -> Real)
    (leftEnvelope rightEnvelope : ℕ -> Real)
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
            leftComponentScale component * leftEnvelope index)
    (hright_component_bound :
      ∀ᶠ index in atTop,
        ∀ component, component ∈ rightComponents ->
          |rightBiasComponent index component| ≤
            rightComponentScale component * rightEnvelope index)
    (hleft_envelope_tendsto :
      Tendsto leftEnvelope atTop (nhds 0))
    (hright_envelope_tendsto :
      Tendsto rightEnvelope atTop (nhds 0)) :
    Tendsto leftBiasCorrectionError atTop (nhds 0) ∧
      Tendsto rightBiasCorrectionError atTop (nhds 0) :=
  ⟨tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_envelope_bounds
      leftComponents leftBiasCorrectionError leftBiasComponent
      leftComponentScale leftEnvelope hleft_decomp hleft_component_bound
      hleft_envelope_tendsto,
    tendsto_actualBootstrapBiasCorrectionError_zero_of_finite_component_envelope_bounds
      rightComponents rightBiasCorrectionError rightBiasComponent
      rightComponentScale rightEnvelope hright_decomp hright_component_bound
      hright_envelope_tendsto⟩

/--
Actual bootstrap variance convergence when the score-replication and
bias-correction errors have finite component decompositions controlled by
shrinking score and bias envelopes.
-/
theorem tendsto_bootstrapVariance_of_finite_component_envelope_error_bounds
    {ScoreComponent BiasComponent : Type*}
    [DecidableEq ScoreComponent] [DecidableEq BiasComponent]
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (scoreComponent : Index -> ScoreComponent -> Real)
    (biasComponent : Index -> BiasComponent -> Real)
    (scoreComponentScale : ScoreComponent -> Real)
    (biasComponentScale : BiasComponent -> Real)
    (scoreEnvelope biasEnvelope : Index -> Real)
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
            scoreComponentScale component * scoreEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreEnvelope l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasComponent index component| ≤
            biasComponentScale component * biasEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasEnvelope l (nhds 0)) :
    Tendsto actualVariance l (nhds varianceLimit) :=
  tendsto_bootstrapVariance_of_eventual_error_decomposition
    (l := l) linearizedVariance actualVariance scoreReplicationError
    biasCorrectionError varianceLimit herror_decomp hlinearized
    (bootstrapScoreReplicationErrorNegligible_of_finite_component_envelope_bounds
      (l := l) scoreComponents scoreReplicationError scoreComponent
      scoreComponentScale scoreEnvelope hscore_decomp hscore_component_bound
      hscore_envelope_tendsto)
    (bootstrapBiasCorrectionErrorNegligible_of_finite_component_envelope_bounds
      (l := l) biasComponents biasCorrectionError biasComponent
      biasComponentScale biasEnvelope hbias_decomp hbias_component_bound
      hbias_envelope_tendsto)

/--
Bridge-form actual bootstrap variance consistency from finite component error
decompositions controlled by shrinking score and bias envelopes.
-/
theorem actualBootstrapVarianceConsistent_of_finite_component_envelope_error_bounds
    {ScoreComponent BiasComponent : Type*}
    [DecidableEq ScoreComponent] [DecidableEq BiasComponent]
    (scoreComponents : Finset ScoreComponent)
    (biasComponents : Finset BiasComponent)
    (linearizedVariance actualVariance scoreReplicationError
      biasCorrectionError : Index -> Real)
    (scoreComponent : Index -> ScoreComponent -> Real)
    (biasComponent : Index -> BiasComponent -> Real)
    (scoreComponentScale : ScoreComponent -> Real)
    (biasComponentScale : BiasComponent -> Real)
    (scoreEnvelope biasEnvelope : Index -> Real)
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
            scoreComponentScale component * scoreEnvelope index)
    (hscore_envelope_tendsto :
      Tendsto scoreEnvelope l (nhds 0))
    (hbias_decomp :
      biasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ biasComponents,
          biasComponent index component))
    (hbias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ biasComponents ->
          |biasComponent index component| ≤
            biasComponentScale component * biasEnvelope index)
    (hbias_envelope_tendsto :
      Tendsto biasEnvelope l (nhds 0)) :
    actualBootstrapVarianceConsistent
      (l := l) actualVariance varianceLimit :=
  tendsto_bootstrapVariance_of_finite_component_envelope_error_bounds
    (l := l) scoreComponents biasComponents linearizedVariance
    actualVariance scoreReplicationError biasCorrectionError scoreComponent
    biasComponent scoreComponentScale biasComponentScale scoreEnvelope
    biasEnvelope varianceLimit herror_decomp hlinearized hscore_decomp
    hscore_component_bound hscore_envelope_tendsto hbias_decomp
    hbias_component_bound hbias_envelope_tendsto

/--
Paired bridge-form actual bootstrap variance consistency from finite component
score/bias error decompositions controlled by shrinking envelopes.
-/
theorem paired_actualBootstrapVarianceConsistent_of_finite_component_envelope_error_bounds
    {LeftScoreComponent LeftBiasComponent RightScoreComponent
      RightBiasComponent : Type*}
    [DecidableEq LeftScoreComponent] [DecidableEq LeftBiasComponent]
    [DecidableEq RightScoreComponent] [DecidableEq RightBiasComponent]
    (leftScoreComponents : Finset LeftScoreComponent)
    (leftBiasComponents : Finset LeftBiasComponent)
    (rightScoreComponents : Finset RightScoreComponent)
    (rightBiasComponents : Finset RightBiasComponent)
    (leftLinearizedVariance leftActualVariance leftScoreReplicationError
      leftBiasCorrectionError : Index -> Real)
    (rightLinearizedVariance rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError : Index -> Real)
    (leftScoreComponent : Index -> LeftScoreComponent -> Real)
    (leftBiasComponent : Index -> LeftBiasComponent -> Real)
    (rightScoreComponent : Index -> RightScoreComponent -> Real)
    (rightBiasComponent : Index -> RightBiasComponent -> Real)
    (leftScoreComponentScale : LeftScoreComponent -> Real)
    (leftBiasComponentScale : LeftBiasComponent -> Real)
    (rightScoreComponentScale : RightScoreComponent -> Real)
    (rightBiasComponentScale : RightBiasComponent -> Real)
    (leftScoreEnvelope leftBiasEnvelope rightScoreEnvelope rightBiasEnvelope :
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
    (hleft_score_decomp :
      leftScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ leftScoreComponents,
          leftScoreComponent index component))
    (hleft_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftScoreComponents ->
          |leftScoreComponent index component| ≤
            leftScoreComponentScale component * leftScoreEnvelope index)
    (hleft_score_envelope_tendsto :
      Tendsto leftScoreEnvelope l (nhds 0))
    (hleft_bias_decomp :
      leftBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ leftBiasComponents,
          leftBiasComponent index component))
    (hleft_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ leftBiasComponents ->
          |leftBiasComponent index component| ≤
            leftBiasComponentScale component * leftBiasEnvelope index)
    (hleft_bias_envelope_tendsto :
      Tendsto leftBiasEnvelope l (nhds 0))
    (hright_score_decomp :
      rightScoreReplicationError =ᶠ[l]
        (fun index => ∑ component ∈ rightScoreComponents,
          rightScoreComponent index component))
    (hright_score_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightScoreComponents ->
          |rightScoreComponent index component| ≤
            rightScoreComponentScale component * rightScoreEnvelope index)
    (hright_score_envelope_tendsto :
      Tendsto rightScoreEnvelope l (nhds 0))
    (hright_bias_decomp :
      rightBiasCorrectionError =ᶠ[l]
        (fun index => ∑ component ∈ rightBiasComponents,
          rightBiasComponent index component))
    (hright_bias_component_bound :
      ∀ᶠ index in l,
        ∀ component, component ∈ rightBiasComponents ->
          |rightBiasComponent index component| ≤
            rightBiasComponentScale component * rightBiasEnvelope index)
    (hright_bias_envelope_tendsto :
      Tendsto rightBiasEnvelope l (nhds 0)) :
    actualBootstrapVarianceConsistent
        (l := l) leftActualVariance leftVarianceLimit ∧
      actualBootstrapVarianceConsistent
        (l := l) rightActualVariance rightVarianceLimit :=
  ⟨actualBootstrapVarianceConsistent_of_finite_component_envelope_error_bounds
      (l := l) leftScoreComponents leftBiasComponents
      leftLinearizedVariance leftActualVariance leftScoreReplicationError
      leftBiasCorrectionError leftScoreComponent leftBiasComponent
      leftScoreComponentScale leftBiasComponentScale leftScoreEnvelope
      leftBiasEnvelope leftVarianceLimit hleft_error_decomp
      hleft_linearized hleft_score_decomp hleft_score_component_bound
      hleft_score_envelope_tendsto hleft_bias_decomp
      hleft_bias_component_bound hleft_bias_envelope_tendsto,
    actualBootstrapVarianceConsistent_of_finite_component_envelope_error_bounds
      (l := l) rightScoreComponents rightBiasComponents
      rightLinearizedVariance rightActualVariance rightScoreReplicationError
      rightBiasCorrectionError rightScoreComponent rightBiasComponent
      rightScoreComponentScale rightBiasComponentScale rightScoreEnvelope
      rightBiasEnvelope rightVarianceLimit hright_error_decomp
      hright_linearized hright_score_decomp hright_score_component_bound
      hright_score_envelope_tendsto hright_bias_decomp
      hright_bias_component_bound hright_bias_envelope_tendsto⟩

end WDSM
end Matching
end StatInference
