import StatInference.Asymptotics.Basic
import StatInference.Asymptotics.Op

/-!
# Convergence bridge interfaces

This module records the reusable convergence routes used in asymptotic
statistics.  The propositions stay explicit so concrete developments can later
replace them with mathlib-backed convergence-in-measure, weak-convergence, CLT,
Slutsky, and delta-method statements without changing downstream estimator
interfaces.
-/

namespace StatInference

open Filter
open scoped Topology

/-- Prototype record for convergence in probability. -/
structure ConvergenceInProbabilitySpec where
  statement : Prop

/-- Prototype record for convergence in distribution / weak convergence. -/
structure ConvergenceInDistributionSpec where
  statement : Prop

/-- Prototype record for tightness of a sequence of random elements. -/
structure TightnessSpec where
  statement : Prop

/-- Prototype central-limit-theorem statement. -/
structure CentralLimitTheoremSpec where
  statement : Prop

/--
Slutsky-style bridge: a main term converges in distribution, a perturbation is
small in probability, and the combined statistic has the same limit.
-/
structure SlutskyBridge where
  main_convergence : ConvergenceInDistributionSpec
  perturbation_small : SmallOInProbabilitySpec
  combined_convergence : Prop
  bridge :
    main_convergence.statement ->
    perturbation_small.statement ->
    combined_convergence

/-- Apply a Slutsky-style bridge. -/
theorem convergence_of_slutsky_bridge (bridge : SlutskyBridge)
    (hmain : bridge.main_convergence.statement)
    (hsmall : bridge.perturbation_small.statement) :
    bridge.combined_convergence :=
  bridge.bridge hmain hsmall

/--
Continuous-mapping bridge: convergence of the input plus continuity of the map
implies convergence of the mapped statistic.
-/
structure ContinuousMappingBridge where
  input_convergence : ConvergenceInDistributionSpec
  continuity_statement : Prop
  mapped_convergence : Prop
  bridge :
    input_convergence.statement ->
    continuity_statement ->
    mapped_convergence

/-- Apply a continuous-mapping bridge. -/
theorem convergence_of_continuous_mapping_bridge
    (bridge : ContinuousMappingBridge)
    (hconv : bridge.input_convergence.statement)
    (hcontinuous : bridge.continuity_statement) :
    bridge.mapped_convergence :=
  bridge.bridge hconv hcontinuous

/--
Delta-method bridge: a first-order linearization, convergence of the linear
part, and negligible remainder imply convergence of the transformed statistic.
-/
structure DeltaMethodBridge where
  linearization_statement : Prop
  linear_part_convergence : ConvergenceInDistributionSpec
  remainder_small : SmallOInProbabilitySpec
  transformed_convergence : Prop
  bridge :
    linearization_statement ->
    linear_part_convergence.statement ->
    remainder_small.statement ->
    transformed_convergence

/-- Apply a delta-method bridge. -/
theorem convergence_of_delta_method_bridge (bridge : DeltaMethodBridge)
    (hlinearization : bridge.linearization_statement)
    (hlinear : bridge.linear_part_convergence.statement)
    (hremainder : bridge.remainder_small.statement) :
    bridge.transformed_convergence :=
  bridge.bridge hlinearization hlinear hremainder

/--
CLT-to-asymptotic-normality bridge for estimators with an asymptotic linear
expansion.  This is the central theorem-family interface for statistical
inference modules.
-/
structure AsymptoticLinearCLTBridge where
  asymptotic_linear_statement : Prop
  clt : CentralLimitTheoremSpec
  negligible_remainder : SmallOInProbabilitySpec
  asymptotic_normality : Prop
  bridge :
    asymptotic_linear_statement ->
    clt.statement ->
    negligible_remainder.statement ->
    asymptotic_normality

/-- Apply the asymptotic-linearity plus CLT bridge. -/
theorem asymptotic_normality_of_asymptoticLinear_clt_bridge
    (bridge : AsymptoticLinearCLTBridge)
    (hal : bridge.asymptotic_linear_statement)
    (hclt : bridge.clt.statement)
    (hrem : bridge.negligible_remainder.statement) :
    bridge.asymptotic_normality :=
  bridge.bridge hal hclt hrem

/-- Package a proved proposition as a convergence-in-probability specification. -/
def convergenceInProbabilityOfStatement (p : Prop) :
    ConvergenceInProbabilitySpec where
  statement := p

/-- Package a proved proposition as a convergence-in-distribution specification. -/
def convergenceInDistributionOfStatement (p : Prop) :
    ConvergenceInDistributionSpec where
  statement := p

/-- Package a proved proposition as a CLT specification. -/
def centralLimitTheoremOfStatement (p : Prop) :
    CentralLimitTheoremSpec where
  statement := p

end StatInference
