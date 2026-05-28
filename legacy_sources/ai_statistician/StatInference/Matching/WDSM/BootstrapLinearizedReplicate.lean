import StatInference.Matching.WDSM.BootstrapAlgebra
import StatInference.Matching.WDSM.BootstrapMultinomialDrawBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorPartition
import Mathlib.Tactic.Ring

/-!
# Manuscript-facing linearized bootstrap replicate algebra

This module specializes the generic multiplier bootstrap algebra to the
linearized WDSM replicate forms used in the manuscript.  The theorems are
finite identities: the matching reuse terms are treated as fixed inputs from
the original matching structure, while multiplier weights perturb only the
linearized contributions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Unit Draw Omega Cell Component Index : Type*}

/--
Retrospective PATE linearized contribution.  The `baseWeight` term carries the
heterogeneity contribution, while `reuseResidualWeight` carries the signed
own-plus-reuse residual contribution.
-/
noncomputable def retrospectivePATEBootstrapInfluenceContribution
    (baseWeight reuseResidualWeight heterogeneity residual : Unit -> Real)
    (unit : Unit) : Real :=
  baseWeight unit * heterogeneity unit +
    reuseResidualWeight unit * residual unit

/-- Manuscript-facing retrospective PATE linearized bootstrap numerator. -/
noncomputable def retrospectivePATELinearizedBootstrapNumerator
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) : Real :=
  (∑ unit ∈ sample,
    multiplier unit * baseWeight unit * heterogeneity unit) +
    (∑ unit ∈ sample,
      multiplier unit * reuseResidualWeight unit * residual unit)

/--
The retrospective PATE linearized bootstrap numerator is exactly a replicated
linearized sum of the fixed matching-structure influence contribution.
-/
theorem retrospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) :
    retrospectivePATELinearizedBootstrapNumerator sample multiplier
        baseWeight reuseResidualWeight heterogeneity residual =
      replicatedLinearizedSum sample multiplier
        (retrospectivePATEBootstrapInfluenceContribution baseWeight
          reuseResidualWeight heterogeneity residual) := by
  unfold retrospectivePATELinearizedBootstrapNumerator
    replicatedLinearizedSum
    retrospectivePATEBootstrapInfluenceContribution
  rw [← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl
    (fun unit _hunit => by ring)

/--
The retrospective PATE linearized bootstrap ratio is the generic replicated
linearized ratio applied to the fixed matching-structure influence
contribution and the base survey-weight denominator.
-/
theorem retrospectivePATELinearizedBootstrapRatio_eq_replicatedLinearizedRatio
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual :
      Unit -> Real) :
    retrospectivePATELinearizedBootstrapNumerator sample multiplier
        baseWeight reuseResidualWeight heterogeneity residual /
        replicatedLinearizedSum sample multiplier baseWeight =
      replicatedLinearizedSum sample multiplier
        (retrospectivePATEBootstrapInfluenceContribution baseWeight
          reuseResidualWeight heterogeneity residual) /
        replicatedLinearizedSum sample multiplier baseWeight := by
  rw [retrospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum]

/--
Retrospective PATT linearized contribution.  The treated contribution and the
control reuse contribution are kept separate to preserve PATT's one-sided
structure.
-/
noncomputable def retrospectivePATTBootstrapInfluenceContribution
    (treatedContribution controlReuseContribution : Unit -> Real)
    (unit : Unit) : Real :=
  treatedContribution unit - controlReuseContribution unit

/-- Manuscript-facing retrospective PATT linearized bootstrap numerator. -/
noncomputable def retrospectivePATTLinearizedBootstrapNumerator
    (sample : Finset Unit)
    (multiplier treatedContribution controlReuseContribution : Unit -> Real) :
    Real :=
  (∑ unit ∈ sample, multiplier unit * treatedContribution unit) -
    (∑ unit ∈ sample, multiplier unit * controlReuseContribution unit)

/--
The retrospective PATT linearized bootstrap numerator is exactly a replicated
linearized sum of the fixed one-sided matching-structure influence
contribution.
-/
theorem retrospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum
    (sample : Finset Unit)
    (multiplier treatedContribution controlReuseContribution : Unit -> Real) :
    retrospectivePATTLinearizedBootstrapNumerator sample multiplier
        treatedContribution controlReuseContribution =
      replicatedLinearizedSum sample multiplier
        (retrospectivePATTBootstrapInfluenceContribution treatedContribution
          controlReuseContribution) := by
  unfold retrospectivePATTLinearizedBootstrapNumerator
    replicatedLinearizedSum
    retrospectivePATTBootstrapInfluenceContribution
  rw [← Finset.sum_sub_distrib]
  exact Finset.sum_congr rfl
    (fun unit _hunit => by ring)

/--
The retrospective PATT linearized bootstrap ratio is the generic replicated
linearized ratio applied to the one-sided fixed matching-structure influence
contribution and the treated-side denominator weight.
-/
theorem retrospectivePATTLinearizedBootstrapRatio_eq_replicatedLinearizedRatio
    (sample : Finset Unit)
    (multiplier denominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real) :
    retrospectivePATTLinearizedBootstrapNumerator sample multiplier
        treatedContribution controlReuseContribution /
        replicatedLinearizedSum sample multiplier denominatorWeight =
      replicatedLinearizedSum sample multiplier
        (retrospectivePATTBootstrapInfluenceContribution treatedContribution
          controlReuseContribution) /
        replicatedLinearizedSum sample multiplier denominatorWeight := by
  rw [retrospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum]

/--
Paired retrospective PATE/PATT linearized bootstrap numerators as generic
replicated linearized sums.
-/
theorem retrospectivePATEPATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual
      treatedContribution controlReuseContribution : Unit -> Real) :
    retrospectivePATELinearizedBootstrapNumerator sample multiplier
        baseWeight reuseResidualWeight heterogeneity residual =
      replicatedLinearizedSum sample multiplier
        (retrospectivePATEBootstrapInfluenceContribution baseWeight
          reuseResidualWeight heterogeneity residual) ∧
    retrospectivePATTLinearizedBootstrapNumerator sample multiplier
        treatedContribution controlReuseContribution =
      replicatedLinearizedSum sample multiplier
        (retrospectivePATTBootstrapInfluenceContribution treatedContribution
          controlReuseContribution) := by
  exact
    ⟨retrospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum
        sample multiplier baseWeight reuseResidualWeight heterogeneity
        residual,
      retrospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum
        sample multiplier treatedContribution controlReuseContribution⟩

/--
Paired retrospective PATE/PATT linearized bootstrap ratios as generic
replicated linearized ratios.
-/
theorem retrospectivePATEPATTLinearizedBootstrapRatio_eq_replicatedLinearizedRatio
    (sample : Finset Unit)
    (multiplier baseWeight reuseResidualWeight heterogeneity residual
      pattDenominatorWeight treatedContribution controlReuseContribution :
      Unit -> Real) :
    retrospectivePATELinearizedBootstrapNumerator sample multiplier
        baseWeight reuseResidualWeight heterogeneity residual /
        replicatedLinearizedSum sample multiplier baseWeight =
      replicatedLinearizedSum sample multiplier
        (retrospectivePATEBootstrapInfluenceContribution baseWeight
          reuseResidualWeight heterogeneity residual) /
        replicatedLinearizedSum sample multiplier baseWeight ∧
    retrospectivePATTLinearizedBootstrapNumerator sample multiplier
        treatedContribution controlReuseContribution /
        replicatedLinearizedSum sample multiplier pattDenominatorWeight =
      replicatedLinearizedSum sample multiplier
        (retrospectivePATTBootstrapInfluenceContribution treatedContribution
          controlReuseContribution) /
        replicatedLinearizedSum sample multiplier pattDenominatorWeight := by
  exact
    ⟨retrospectivePATELinearizedBootstrapRatio_eq_replicatedLinearizedRatio
        sample multiplier baseWeight reuseResidualWeight heterogeneity
        residual,
      retrospectivePATTLinearizedBootstrapRatio_eq_replicatedLinearizedRatio
        sample multiplier pattDenominatorWeight treatedContribution
        controlReuseContribution⟩

/--
Finite component sums of replicated-minus-base linearized sums are exactly
finite component sums of multiplier perturbations.
-/
theorem sum_replicatedLinearizedSum_sub_base_eq_sum_multiplierPerturbation
    (components : Finset Component)
    (sample : Finset Unit)
    (multiplier : Unit -> Real)
    (unitComponent : Unit -> Component -> Real) :
    (∑ component ∈ components,
        (replicatedLinearizedSum sample multiplier
            (fun unit => unitComponent unit component) -
          baseLinearizedSum sample
            (fun unit => unitComponent unit component))) =
      ∑ component ∈ components,
        multiplierPerturbation sample multiplier
          (fun unit => unitComponent unit component) := by
  exact Finset.sum_congr rfl
    (fun component _hcomponent =>
      (multiplierPerturbation_eq_replicated_sub_base sample multiplier
        (fun unit => unitComponent unit component)).symm)

/--
For a multinomial draw-count replicate, the finite component sum of
multiplier perturbations is the centered-count component sum.
-/
theorem sum_multiplierPerturbation_multinomialCount_eq_centered_count_component_sum
    (components : Finset Component)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega)
    (unitComponent : Unit -> Component -> Real) :
    (∑ component ∈ components,
        multiplierPerturbation sample
          (fun unit =>
            multinomialCountFromDrawIndicators draws drawIndicator omega unit)
          (fun unit => unitComponent unit component)) =
      ∑ component ∈ components, ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          unitComponent unit component := by
  simp [multiplierPerturbation]

/--
Replicated-minus-base component sums for a concrete multinomial draw-count
replicate reduce to the centered-count component sum used by the finite-error
bootstrap routes.
-/
theorem sum_replicatedLinearizedSum_sub_base_eq_centered_count_component_sum_of_multinomial_draw_replicate
    (components : Finset Component)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega)
    (unitComponent : Unit -> Component -> Real) :
    (∑ component ∈ components,
        (replicatedLinearizedSum sample
            (fun unit =>
              multinomialCountFromDrawIndicators draws drawIndicator omega unit)
            (fun unit => unitComponent unit component) -
          baseLinearizedSum sample
            (fun unit => unitComponent unit component))) =
      ∑ component ∈ components, ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          unitComponent unit component := by
  rw [sum_replicatedLinearizedSum_sub_base_eq_sum_multiplierPerturbation,
    sum_multiplierPerturbation_multinomialCount_eq_centered_count_component_sum]

/--
A single replicated-minus-base linearized sum for a concrete multinomial
draw-count replicate is the centered-count unit sum.
-/
theorem replicatedLinearizedSum_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega)
    (unitContribution : Unit -> Real) :
    replicatedLinearizedSum sample
        (fun unit =>
          multinomialCountFromDrawIndicators draws drawIndicator omega unit)
        unitContribution -
        baseLinearizedSum sample unitContribution =
      ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          unitContribution unit := by
  simpa [multiplierPerturbation] using
    (multiplierPerturbation_eq_replicated_sub_base sample
      (fun unit =>
        multinomialCountFromDrawIndicators draws drawIndicator omega unit)
      unitContribution).symm

/--
Eventual construction bridge from a single replicated-minus-base finite sum
to the centered-count construction consumed by finite bootstrap error
reducers.
-/
theorem eventually_error_eq_centered_count_sum_of_replicated_sub_base
    {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (unitContribution : Index -> Unit -> Real)
    (error : Index -> Real)
    (hconstruct :
      error =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (unitContribution index) -
            baseLinearizedSum (sample index)
              (unitContribution index))) :
    error =ᶠ[l]
      (fun index =>
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            unitContribution index unit) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (unitContribution index) -
          baseLinearizedSum (sample index)
            (unitContribution index) := hindex
    _ =
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            unitContribution index unit :=
          replicatedLinearizedSum_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
            (sample index) (draws index) (drawIndicator index) (omega index)
            (unitContribution index)

/--
Eventual construction bridge from replicated-minus-base finite component sums
to the centered-count construction consumed by the score/bias error reducers.
-/
theorem eventually_error_eq_centered_count_component_sum_of_replicated_sub_base_sum
    {l : Filter Index}
    (components : Finset Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (unitComponent : Index -> Unit -> Component -> Real)
    (error : Index -> Real)
    (hconstruct :
      error =ᶠ[l]
        (fun index =>
          ∑ component ∈ components,
            (replicatedLinearizedSum (sample index)
                (fun unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (drawIndicator index) (omega index) unit)
                (fun unit => unitComponent index unit component) -
              baseLinearizedSum (sample index)
                (fun unit => unitComponent index unit component)))) :
    error =ᶠ[l]
      (fun index =>
        ∑ component ∈ components, ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            unitComponent index unit component) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        ∑ component ∈ components,
          (replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (fun unit => unitComponent index unit component) -
            baseLinearizedSum (sample index)
              (fun unit => unitComponent index unit component)) := hindex
    _ =
        ∑ component ∈ components, ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            unitComponent index unit component :=
          sum_replicatedLinearizedSum_sub_base_eq_centered_count_component_sum_of_multinomial_draw_replicate
            components (sample index) (draws index) (drawIndicator index)
            (omega index) (unitComponent index)

/--
Retrospective PATE manuscript numerator minus its original finite influence
sum is the centered-count sum for a concrete multinomial draw-count
replicate.
-/
theorem retrospectivePATELinearizedBootstrapNumerator_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega)
    (baseWeight reuseResidualWeight heterogeneity residual : Unit -> Real) :
    retrospectivePATELinearizedBootstrapNumerator sample
        (fun unit =>
          multinomialCountFromDrawIndicators draws drawIndicator omega unit)
        baseWeight reuseResidualWeight heterogeneity residual -
        baseLinearizedSum sample
          (retrospectivePATEBootstrapInfluenceContribution baseWeight
            reuseResidualWeight heterogeneity residual) =
      ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          retrospectivePATEBootstrapInfluenceContribution baseWeight
            reuseResidualWeight heterogeneity residual unit := by
  rw [retrospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum]
  simpa [multiplierPerturbation] using
    (multiplierPerturbation_eq_replicated_sub_base sample
      (fun unit =>
        multinomialCountFromDrawIndicators draws drawIndicator omega unit)
      (retrospectivePATEBootstrapInfluenceContribution baseWeight
        reuseResidualWeight heterogeneity residual)).symm

/--
Retrospective PATT manuscript numerator minus its original finite influence
sum is the centered-count sum for a concrete multinomial draw-count
replicate.
-/
theorem retrospectivePATTLinearizedBootstrapNumerator_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega)
    (treatedContribution controlReuseContribution : Unit -> Real) :
    retrospectivePATTLinearizedBootstrapNumerator sample
        (fun unit =>
          multinomialCountFromDrawIndicators draws drawIndicator omega unit)
        treatedContribution controlReuseContribution -
        baseLinearizedSum sample
          (retrospectivePATTBootstrapInfluenceContribution
            treatedContribution controlReuseContribution) =
      ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          retrospectivePATTBootstrapInfluenceContribution
            treatedContribution controlReuseContribution unit := by
  rw [retrospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum]
  simpa [multiplierPerturbation] using
    (multiplierPerturbation_eq_replicated_sub_base sample
      (fun unit =>
        multinomialCountFromDrawIndicators draws drawIndicator omega unit)
      (retrospectivePATTBootstrapInfluenceContribution
        treatedContribution controlReuseContribution)).symm

/--
Eventual retrospective PATE construction bridge from the manuscript
linearized numerator-minus-base expression to the centered-count construction
used by finite bootstrap error reducers.
-/
theorem eventually_error_eq_retrospectivePATE_centered_count_sum_of_linearized_numerator
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
          retrospectivePATELinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index) -
            baseLinearizedSum (sample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index)))) :
    error =ᶠ[l]
      (fun index =>
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index) unit) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        retrospectivePATELinearizedBootstrapNumerator (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (baseWeight index) (reuseResidualWeight index)
            (heterogeneity index) (residual index) -
          baseLinearizedSum (sample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) := hindex
    _ =
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index) unit :=
          retrospectivePATELinearizedBootstrapNumerator_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
            (sample index) (draws index) (drawIndicator index) (omega index)
            (baseWeight index) (reuseResidualWeight index)
            (heterogeneity index) (residual index)

/--
Eventual retrospective PATE construction bridge from the manuscript
linearized numerator-minus-base expression to the replicated-linearized
minus-base construction consumed by singleton actual-variance endpoints.
-/
theorem eventually_error_eq_retrospectivePATE_replicatedLinearized_sub_base_of_linearized_numerator
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
          retrospectivePATELinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index) -
            baseLinearizedSum (sample index)
              (retrospectivePATEBootstrapInfluenceContribution
                (baseWeight index) (reuseResidualWeight index)
                (heterogeneity index) (residual index)))) :
    error =ᶠ[l]
      (fun index =>
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) -
          baseLinearizedSum (sample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index))) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        retrospectivePATELinearizedBootstrapNumerator (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (baseWeight index) (reuseResidualWeight index)
            (heterogeneity index) (residual index) -
          baseLinearizedSum (sample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) := hindex
    _ =
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) -
          baseLinearizedSum (sample index)
            (retrospectivePATEBootstrapInfluenceContribution
              (baseWeight index) (reuseResidualWeight index)
              (heterogeneity index) (residual index)) := by
          rw [retrospectivePATELinearizedBootstrapNumerator_eq_replicatedLinearizedSum]

/--
Eventual retrospective PATT construction bridge from the manuscript
linearized numerator-minus-base expression to the centered-count construction
used by finite bootstrap error reducers.
-/
theorem eventually_error_eq_retrospectivePATT_centered_count_sum_of_linearized_numerator
    {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (treatedContribution controlReuseContribution : Index -> Unit -> Real)
    (error : Index -> Real)
    (hconstruct :
      error =ᶠ[l]
        (fun index =>
          retrospectivePATTLinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (treatedContribution index) (controlReuseContribution index) -
            baseLinearizedSum (sample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (treatedContribution index)
                (controlReuseContribution index)))) :
    error =ᶠ[l]
      (fun index =>
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index) unit) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        retrospectivePATTLinearizedBootstrapNumerator (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (treatedContribution index) (controlReuseContribution index) -
          baseLinearizedSum (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) := hindex
    _ =
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index) unit :=
          retrospectivePATTLinearizedBootstrapNumerator_sub_base_eq_centered_count_sum_of_multinomial_draw_replicate
            (sample index) (draws index) (drawIndicator index) (omega index)
            (treatedContribution index) (controlReuseContribution index)

/--
Eventual retrospective PATT construction bridge from the manuscript
linearized numerator-minus-base expression to the replicated-linearized
minus-base construction consumed by singleton actual-variance endpoints.
-/
theorem eventually_error_eq_retrospectivePATT_replicatedLinearized_sub_base_of_linearized_numerator
    {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (treatedContribution controlReuseContribution : Index -> Unit -> Real)
    (error : Index -> Real)
    (hconstruct :
      error =ᶠ[l]
        (fun index =>
          retrospectivePATTLinearizedBootstrapNumerator (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (treatedContribution index) (controlReuseContribution index) -
            baseLinearizedSum (sample index)
              (retrospectivePATTBootstrapInfluenceContribution
                (treatedContribution index)
                (controlReuseContribution index)))) :
    error =ᶠ[l]
      (fun index =>
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) -
          baseLinearizedSum (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index))) := by
  filter_upwards [hconstruct] with index hindex
  calc
    error index =
        retrospectivePATTLinearizedBootstrapNumerator (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (treatedContribution index) (controlReuseContribution index) -
          baseLinearizedSum (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) := hindex
    _ =
        replicatedLinearizedSum (sample index)
            (fun unit =>
              multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) -
          baseLinearizedSum (sample index)
            (retrospectivePATTBootstrapInfluenceContribution
              (treatedContribution index)
              (controlReuseContribution index)) := by
          rw [retrospectivePATTLinearizedBootstrapNumerator_eq_replicatedLinearizedSum]

/--
Score-cell component induced by the concrete multinomial draw-count replicate.
The centered count `m_i^* - 1` is built from the finite draw indicators, and
the score-cell indicator localizes the unit contribution to one score cell.
-/
noncomputable def multinomialDrawScoreCellErrorComponent
    [DecidableEq Cell]
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega) (score : Unit -> Cell)
    (unitComponent : Unit -> Component -> Real)
    (cell : Cell) (component : Component) : Real :=
  ∑ unit ∈ sample,
    scoreCellIndicator score cell unit *
      ((multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
        unitComponent unit component)

/--
The finite score-cell components induced by the concrete multinomial
draw-count replicate recombine to the unit-level centered-count component sum.
-/
theorem sum_multinomialDrawScoreCellErrorComponent_eq_centered_count_unit_sum
    [DecidableEq Cell]
    (cells : Finset Cell) (components : Finset Component)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega) (score : Unit -> Cell)
    (unitComponent : Unit -> Component -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells) :
    (∑ cell ∈ cells, ∑ component ∈ components,
        multinomialDrawScoreCellErrorComponent sample draws drawIndicator
          omega score unitComponent cell component) =
      ∑ component ∈ components, ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          unitComponent unit component := by
  unfold multinomialDrawScoreCellErrorComponent
  calc
    (∑ cell ∈ cells, ∑ component ∈ components, ∑ unit ∈ sample,
        scoreCellIndicator score cell unit *
          ((multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
            unitComponent unit component)) =
        ∑ component ∈ components, ∑ unit ∈ sample, ∑ cell ∈ cells,
          scoreCellIndicator score cell unit *
            ((multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
              unitComponent unit component) := by
          rw [Finset.sum_comm]
          exact Finset.sum_congr rfl
            (fun component _hcomponent => by rw [Finset.sum_comm])
    _ =
        ∑ component ∈ components, ∑ unit ∈ sample,
          (∑ cell ∈ cells, scoreCellIndicator score cell unit) *
            ((multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
              unitComponent unit component) := by
          exact Finset.sum_congr rfl
            (fun component _hcomponent =>
              Finset.sum_congr rfl
                (fun unit _hunit => by rw [Finset.sum_mul]))
    _ =
        ∑ component ∈ components, ∑ unit ∈ sample,
          1 *
            ((multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
              unitComponent unit component) := by
          exact Finset.sum_congr rfl
            (fun component _hcomponent =>
              Finset.sum_congr rfl
                (fun unit hunit => by
                  rw [sum_scoreCellIndicator_eq_one_of_mem cells score unit
                    (hcover unit hunit)]))
    _ =
        ∑ component ∈ components, ∑ unit ∈ sample,
          (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
            unitComponent unit component := by
          simp

/--
Singleton-component version: a single centered-count influence contribution
recombines from its finite score-cell decomposition.
-/
theorem sum_multinomialDrawScoreCellErrorComponent_singleton_eq_centered_count_unit_sum
    [DecidableEq Cell] [DecidableEq Component]
    (cells : Finset Cell) (component : Component)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega) (score : Unit -> Cell)
    (unitContribution : Unit -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells) :
    (∑ cell ∈ cells, ∑ component' ∈ ({component} : Finset Component),
        multinomialDrawScoreCellErrorComponent sample draws drawIndicator
          omega score (fun unit _component => unitContribution unit)
          cell component') =
      ∑ unit ∈ sample,
        (multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          unitContribution unit := by
  simpa using
    sum_multinomialDrawScoreCellErrorComponent_eq_centered_count_unit_sum
      cells ({component} : Finset Component) sample draws drawIndicator omega
      score (fun unit _component => unitContribution unit) hcover

/--
If the actual score-replication error is constructed as a finite
centered-count sum over unit-level components from the multinomial draw-count
replicate, then it has the finite score-cell component decomposition required
by the finite-error actual-bootstrap routes.
-/
theorem eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_components_of_multinomial_draw_replicate
    [DecidableEq Cell]
    {l : Filter Index}
    (cells : Finset Cell) (components : Finset Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitComponent : Index -> Unit -> Component -> Real)
    (scoreReplicationError : Index -> Real)
    (hconstruct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ components, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              unitComponent index unit component))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells) :
    scoreReplicationError =ᶠ[l]
      (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
        multinomialDrawScoreCellErrorComponent (sample index) (draws index)
          (drawIndicator index) (omega index) (score index)
          (unitComponent index) cell component) := by
  filter_upwards [hconstruct, hcover] with index hconstruct_index hcover_index
  calc
    scoreReplicationError index =
        ∑ component ∈ components, ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            unitComponent index unit component := hconstruct_index
    _ =
        ∑ cell ∈ cells, ∑ component ∈ components,
          multinomialDrawScoreCellErrorComponent (sample index) (draws index)
            (drawIndicator index) (omega index) (score index)
            (unitComponent index) cell component := by
          exact
            (sum_multinomialDrawScoreCellErrorComponent_eq_centered_count_unit_sum
              cells components (sample index) (draws index)
              (drawIndicator index) (omega index) (score index)
              (unitComponent index) hcover_index).symm

/--
Bias-correction analogue of the multinomial draw-count score-cell
decomposition.  It uses the same concrete count-centered replicate
construction but exposes the result under the bias-correction error name.
-/
theorem eventually_actualBootstrapBiasCorrectionError_eq_finite_score_cell_components_of_multinomial_draw_replicate
    [DecidableEq Cell]
    {l : Filter Index}
    (cells : Finset Cell) (components : Finset Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitComponent : Index -> Unit -> Component -> Real)
    (biasCorrectionError : Index -> Real)
    (hconstruct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ components, ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              unitComponent index unit component))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells) :
    biasCorrectionError =ᶠ[l]
      (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
        multinomialDrawScoreCellErrorComponent (sample index) (draws index)
          (drawIndicator index) (omega index) (score index)
          (unitComponent index) cell component) :=
  eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_components_of_multinomial_draw_replicate
    (l := l) cells components sample draws drawIndicator omega score
    unitComponent biasCorrectionError hconstruct hcover

/--
Score-replication decomposition from a single centered-count influence
contribution to a singleton-component finite score-cell decomposition.
-/
theorem eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_singleton_component_of_centered_count_sum
    [DecidableEq Cell] [DecidableEq Component]
    {l : Filter Index}
    (cells : Finset Cell) (component : Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitContribution : Index -> Unit -> Real)
    (scoreReplicationError : Index -> Real)
    (hconstruct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              unitContribution index unit))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells) :
    scoreReplicationError =ᶠ[l]
      (fun index =>
        ∑ cell ∈ cells, ∑ component' ∈ ({component} : Finset Component),
          multinomialDrawScoreCellErrorComponent (sample index) (draws index)
            (drawIndicator index) (omega index) (score index)
            (fun unit _component => unitContribution index unit)
            cell component') := by
  filter_upwards [hconstruct, hcover] with index hconstruct_index hcover_index
  calc
    scoreReplicationError index =
        ∑ unit ∈ sample index,
          (multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            unitContribution index unit := hconstruct_index
    _ =
        ∑ cell ∈ cells, ∑ component' ∈ ({component} : Finset Component),
          multinomialDrawScoreCellErrorComponent (sample index) (draws index)
            (drawIndicator index) (omega index) (score index)
            (fun unit _component => unitContribution index unit)
            cell component' := by
          exact
            (sum_multinomialDrawScoreCellErrorComponent_singleton_eq_centered_count_unit_sum
              cells component (sample index) (draws index)
              (drawIndicator index) (omega index) (score index)
              (unitContribution index) hcover_index).symm

/--
Bias-correction decomposition from a single centered-count influence
contribution to a singleton-component finite score-cell decomposition.
-/
theorem eventually_actualBootstrapBiasCorrectionError_eq_finite_score_cell_singleton_component_of_centered_count_sum
    [DecidableEq Cell] [DecidableEq Component]
    {l : Filter Index}
    (cells : Finset Cell) (component : Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitContribution : Index -> Unit -> Real)
    (biasCorrectionError : Index -> Real)
    (hconstruct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ unit ∈ sample index,
            (multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              unitContribution index unit))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells) :
    biasCorrectionError =ᶠ[l]
      (fun index =>
        ∑ cell ∈ cells, ∑ component' ∈ ({component} : Finset Component),
          multinomialDrawScoreCellErrorComponent (sample index) (draws index)
            (drawIndicator index) (omega index) (score index)
            (fun unit _component => unitContribution index unit)
            cell component') :=
  eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_singleton_component_of_centered_count_sum
    (l := l) cells component sample draws drawIndicator omega score
    unitContribution biasCorrectionError hconstruct hcover

/--
Score-replication decomposition from a single replicated-minus-base
construction to a singleton-component finite score-cell decomposition.
-/
theorem eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_singleton_component_of_replicated_sub_base
    [DecidableEq Cell] [DecidableEq Component]
    {l : Filter Index}
    (cells : Finset Cell) (component : Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitContribution : Index -> Unit -> Real)
    (scoreReplicationError : Index -> Real)
    (hconstruct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (unitContribution index) -
            baseLinearizedSum (sample index)
              (unitContribution index)))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells) :
    scoreReplicationError =ᶠ[l]
      (fun index =>
        ∑ cell ∈ cells, ∑ component' ∈ ({component} : Finset Component),
          multinomialDrawScoreCellErrorComponent (sample index) (draws index)
            (drawIndicator index) (omega index) (score index)
            (fun unit _component => unitContribution index unit)
            cell component') :=
  eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_singleton_component_of_centered_count_sum
    (l := l) cells component sample draws drawIndicator omega score
    unitContribution scoreReplicationError
    (eventually_error_eq_centered_count_sum_of_replicated_sub_base
      (l := l) sample draws drawIndicator omega unitContribution
      scoreReplicationError hconstruct)
    hcover

/--
Bias-correction decomposition from a single replicated-minus-base
construction to a singleton-component finite score-cell decomposition.
-/
theorem eventually_actualBootstrapBiasCorrectionError_eq_finite_score_cell_singleton_component_of_replicated_sub_base
    [DecidableEq Cell] [DecidableEq Component]
    {l : Filter Index}
    (cells : Finset Cell) (component : Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitContribution : Index -> Unit -> Real)
    (biasCorrectionError : Index -> Real)
    (hconstruct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          replicatedLinearizedSum (sample index)
              (fun unit =>
                multinomialCountFromDrawIndicators (draws index)
                  (drawIndicator index) (omega index) unit)
              (unitContribution index) -
            baseLinearizedSum (sample index)
              (unitContribution index)))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells) :
    biasCorrectionError =ᶠ[l]
      (fun index =>
        ∑ cell ∈ cells, ∑ component' ∈ ({component} : Finset Component),
          multinomialDrawScoreCellErrorComponent (sample index) (draws index)
            (drawIndicator index) (omega index) (score index)
            (fun unit _component => unitContribution index unit)
            cell component') :=
  eventually_actualBootstrapBiasCorrectionError_eq_finite_score_cell_singleton_component_of_centered_count_sum
    (l := l) cells component sample draws drawIndicator omega score
    unitContribution biasCorrectionError
    (eventually_error_eq_centered_count_sum_of_replicated_sub_base
      (l := l) sample draws drawIndicator omega unitContribution
      biasCorrectionError hconstruct)
    hcover

/--
Score-replication decomposition from a finite replicated-minus-base
component construction directly to the score-cell components consumed by
finite-error actual-bootstrap routes.
-/
theorem eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_components_of_replicated_sub_base_sum
    [DecidableEq Cell]
    {l : Filter Index}
    (cells : Finset Cell) (components : Finset Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitComponent : Index -> Unit -> Component -> Real)
    (scoreReplicationError : Index -> Real)
    (hconstruct :
      scoreReplicationError =ᶠ[l]
        (fun index =>
          ∑ component ∈ components,
            (replicatedLinearizedSum (sample index)
                (fun unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (drawIndicator index) (omega index) unit)
                (fun unit => unitComponent index unit component) -
              baseLinearizedSum (sample index)
                (fun unit => unitComponent index unit component))))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells) :
    scoreReplicationError =ᶠ[l]
      (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
        multinomialDrawScoreCellErrorComponent (sample index) (draws index)
          (drawIndicator index) (omega index) (score index)
          (unitComponent index) cell component) :=
  eventually_actualBootstrapScoreReplicationError_eq_finite_score_cell_components_of_multinomial_draw_replicate
    (l := l) cells components sample draws drawIndicator omega score
    unitComponent scoreReplicationError
    (eventually_error_eq_centered_count_component_sum_of_replicated_sub_base_sum
      (l := l) components sample draws drawIndicator omega unitComponent
      scoreReplicationError hconstruct)
    hcover

/--
Bias-correction decomposition from a finite replicated-minus-base component
construction directly to the score-cell components consumed by finite-error
actual-bootstrap routes.
-/
theorem eventually_actualBootstrapBiasCorrectionError_eq_finite_score_cell_components_of_replicated_sub_base_sum
    [DecidableEq Cell]
    {l : Filter Index}
    (cells : Finset Cell) (components : Finset Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitComponent : Index -> Unit -> Component -> Real)
    (biasCorrectionError : Index -> Real)
    (hconstruct :
      biasCorrectionError =ᶠ[l]
        (fun index =>
          ∑ component ∈ components,
            (replicatedLinearizedSum (sample index)
                (fun unit =>
                  multinomialCountFromDrawIndicators (draws index)
                    (drawIndicator index) (omega index) unit)
                (fun unit => unitComponent index unit component) -
              baseLinearizedSum (sample index)
                (fun unit => unitComponent index unit component))))
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells) :
    biasCorrectionError =ᶠ[l]
      (fun index => ∑ cell ∈ cells, ∑ component ∈ components,
        multinomialDrawScoreCellErrorComponent (sample index) (draws index)
          (drawIndicator index) (omega index) (score index)
          (unitComponent index) cell component) :=
  eventually_actualBootstrapBiasCorrectionError_eq_finite_score_cell_components_of_multinomial_draw_replicate
    (l := l) cells components sample draws drawIndicator omega score
    unitComponent biasCorrectionError
    (eventually_error_eq_centered_count_component_sum_of_replicated_sub_base_sum
      (l := l) components sample draws drawIndicator omega unitComponent
      biasCorrectionError hconstruct)
    hcover

/--
A cell-local multinomial draw component is bounded by the corresponding
score-cell indicator weighted sum of unit-level centered-count bounds.
-/
theorem abs_multinomialDrawScoreCellErrorComponent_le_indicator_unit_bounds
    [DecidableEq Cell]
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega) (score : Unit -> Cell)
    (unitComponent unitComponentBound : Unit -> Component -> Real)
    (cell : Cell) (component : Component)
    (hunit_bound :
      ∀ unit, unit ∈ sample ->
        |(multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
          unitComponent unit component| ≤
          unitComponentBound unit component) :
    |multinomialDrawScoreCellErrorComponent sample draws drawIndicator omega
        score unitComponent cell component| ≤
      ∑ unit ∈ sample,
        scoreCellIndicator score cell unit *
          unitComponentBound unit component := by
  unfold multinomialDrawScoreCellErrorComponent
  calc
    |∑ unit ∈ sample,
        scoreCellIndicator score cell unit *
          ((multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
            unitComponent unit component)| ≤
        ∑ unit ∈ sample,
          |scoreCellIndicator score cell unit *
            ((multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
              unitComponent unit component)| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ =
        ∑ unit ∈ sample,
          scoreCellIndicator score cell unit *
            |(multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1) *
              unitComponent unit component| := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by
              rw [abs_mul,
                abs_of_nonneg (scoreCellIndicator_nonneg score cell unit)])
    _ ≤
        ∑ unit ∈ sample,
          scoreCellIndicator score cell unit *
            unitComponentBound unit component := by
          exact Finset.sum_le_sum
            (fun unit hunit =>
              mul_le_mul_of_nonneg_left (hunit_bound unit hunit)
                (scoreCellIndicator_nonneg score cell unit))

/--
Eventual version of the unit-bound reduction for all finite score cells and
components.
-/
theorem eventually_abs_multinomialDrawScoreCellErrorComponent_le_indicator_unit_bounds
    [DecidableEq Cell]
    {l : Filter Index}
    (cells : Finset Cell) (components : Finset Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega) (score : Index -> Unit -> Cell)
    (unitComponent unitComponentBound :
      Index -> Unit -> Component -> Real)
    (hunit_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ components ->
            |(multinomialCountFromDrawIndicators (draws index)
                (drawIndicator index) (omega index) unit - 1) *
              unitComponent index unit component| ≤
              unitComponentBound index unit component) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        ∀ component, component ∈ components ->
          |multinomialDrawScoreCellErrorComponent (sample index)
              (draws index) (drawIndicator index) (omega index)
              (score index) (unitComponent index) cell component| ≤
            ∑ unit ∈ sample index,
              scoreCellIndicator (score index) cell unit *
                unitComponentBound index unit component := by
  filter_upwards [hunit_bound] with index hbound cell _hcell component
    hcomponent
  exact
    abs_multinomialDrawScoreCellErrorComponent_le_indicator_unit_bounds
      (sample index) (draws index) (drawIndicator index) (omega index)
      (score index) (unitComponent index) (unitComponentBound index)
      cell component
      (fun unit hunit => hbound unit hunit component hcomponent)

/--
Unit-level centered-count products are bounded by a count envelope times a
component envelope.
-/
theorem eventually_abs_centered_multinomial_count_mul_unitComponent_le_count_mul_component_envelope
    {l : Filter Index}
    (components : Finset Component)
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (unitComponent : Index -> Unit -> Component -> Real)
    (countEnvelope : Index -> Real)
    (componentEnvelope : Index -> Component -> Real)
    (hcount_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1| ≤
            countEnvelope index)
    (hcomponent_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ component, component ∈ components ->
            |unitComponent index unit component| ≤
              componentEnvelope index component) :
    ∀ᶠ index in l,
      ∀ unit, unit ∈ sample index ->
        ∀ component, component ∈ components ->
          |(multinomialCountFromDrawIndicators (draws index)
              (drawIndicator index) (omega index) unit - 1) *
            unitComponent index unit component| ≤
            countEnvelope index * componentEnvelope index component := by
  filter_upwards [hcount_bound, hcomponent_bound] with index hcount hcomponent
    unit hunit component hcomponent_mem
  have hcount_nonneg : 0 ≤ countEnvelope index :=
    le_trans (abs_nonneg _) (hcount unit hunit)
  have hcomponent_abs_nonneg :
      0 ≤ |unitComponent index unit component| := abs_nonneg _
  calc
    |(multinomialCountFromDrawIndicators (draws index)
        (drawIndicator index) (omega index) unit - 1) *
        unitComponent index unit component| =
        |multinomialCountFromDrawIndicators (draws index)
            (drawIndicator index) (omega index) unit - 1| *
          |unitComponent index unit component| := by
          rw [abs_mul]
    _ ≤ countEnvelope index * componentEnvelope index component := by
          exact
            mul_le_mul (hcount unit hunit)
              (hcomponent unit hunit component hcomponent_mem)
              hcomponent_abs_nonneg hcount_nonneg

/--
The centered multinomial draw count is bounded by the number of draw slots
plus one when each one-hot draw indicator is bounded by one in absolute value.
-/
theorem abs_multinomialCountFromDrawIndicators_sub_one_le_draw_card_add_one
    (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (omega : Omega) (unit : Unit)
    (hdraw_bound :
      ∀ draw, draw ∈ draws ->
        |drawIndicator omega draw unit| ≤ 1) :
    |multinomialCountFromDrawIndicators draws drawIndicator omega unit - 1| ≤
      (draws.card : Real) + 1 := by
  unfold multinomialCountFromDrawIndicators
  calc
    |(∑ draw ∈ draws, drawIndicator omega draw unit) - 1| ≤
        |∑ draw ∈ draws, drawIndicator omega draw unit| + |(1 : Real)| := by
          simpa [sub_eq_add_neg] using
            abs_add_le (∑ draw ∈ draws, drawIndicator omega draw unit)
              (-(1 : Real))
    _ ≤
        (∑ draw ∈ draws, |drawIndicator omega draw unit|) + 1 := by
          simpa using
            add_le_add_right
              (Finset.abs_sum_le_sum_abs
                (fun draw => drawIndicator omega draw unit) draws)
              (1 : Real)
    _ ≤ (∑ _draw ∈ draws, (1 : Real)) + 1 := by
          simpa [add_comm, add_left_comm, add_assoc] using
            add_le_add_right
              (Finset.sum_le_sum (fun draw hdraw => hdraw_bound draw hdraw))
              (1 : Real)
    _ = (draws.card : Real) + 1 := by
          simp [Finset.sum_const, nsmul_eq_mul]

/--
Eventual finite-draw version of
`abs_multinomialCountFromDrawIndicators_sub_one_le_draw_card_add_one`.
-/
theorem eventually_abs_multinomialCountFromDrawIndicators_sub_one_le_draw_card_add_one
    {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (drawIndicator : Index -> Omega -> Draw -> Unit -> Real)
    (omega : Index -> Omega)
    (hdraw_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          ∀ draw, draw ∈ draws index ->
            |drawIndicator index (omega index) draw unit| ≤ 1) :
    ∀ᶠ index in l,
      ∀ unit, unit ∈ sample index ->
        |multinomialCountFromDrawIndicators (draws index)
            (drawIndicator index) (omega index) unit - 1| ≤
          ((draws index).card : Real) + 1 := by
  filter_upwards [hdraw_bound] with index hbound unit hunit
  exact
    abs_multinomialCountFromDrawIndicators_sub_one_le_draw_card_add_one
      (draws index) (drawIndicator index) (omega index) unit
      (fun draw hdraw => hbound unit hunit draw hdraw)

end WDSM
end Matching
end StatInference
