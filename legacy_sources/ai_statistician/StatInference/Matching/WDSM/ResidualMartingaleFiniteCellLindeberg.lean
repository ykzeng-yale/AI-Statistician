import StatInference.Matching.WDSM.FiniteCellResidualThirdMoment
import StatInference.Matching.WDSM.ResidualMartingaleConcreteLindeberg
import Mathlib.Probability.Martingale.Basic

/-!
# Residual martingale CLT input from finite score-cell Lindeberg control

This module composes the finite score-cell coefficient-envelope bridge with
the residual martingale-array interface.  It keeps the martingale CLT theorem
itself explicit, while allowing the Lindeberg premise to be discharged from
finite score-cell measurable coefficient loadings and residual third-moment
control.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory

variable {Index Treated Control TreatedCell ControlCell : Type*}
  {l : Filter Index} [DecidableEq TreatedCell] [DecidableEq ControlCell]

omit [DecidableEq TreatedCell] [DecidableEq ControlCell] in
/--
Residual CLT and variance formula from a martingale-array input whose
Lindeberg field is implied by the concrete two-arm WDSM condition, with that
condition supplied by finite score-cell coefficient loadings.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_lindeberg_bridge
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
    (treatedLoading : Index -> TreatedCell -> Real)
    (controlLoading : Index -> ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hmartingale : input.martingale_difference_array)
    (hqv : input.predictable_quadratic_variation_stabilization)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLoading index (controlScore index control))
    (htreatedLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedLoading index cell| ≤ treatedEnvelope index)
    (hcontrolLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlLoading index cell| ≤ controlEnvelope index)
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
    input.residual_clt ∧ input.residual_variance_formula := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual
      treatedScore controlScore treatedLoading controlLoading
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedCoefficient hcontrolCoefficient htreatedLoadingBound
      hcontrolLoadingBound htreatedEnvelopeBound hcontrolEnvelopeBound
  exact
    residual_clt_and_variance_formula_of_martingale_array_input input
      hexact hregularity hmartingale (hinputLindeberg hlindeberg) hqv

omit [DecidableEq TreatedCell] [DecidableEq ControlCell] in
/--
Input-level finite score-cell loading Lindeberg bridge with the
martingale-difference field supplied by concrete treated/control Mathlib
martingales.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_envelopes_mathlib_martingales_input
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
    (treatedLoading : Index -> TreatedCell -> Real)
    (controlLoading : Index -> ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmartingaleMap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          input.martingale_difference_array)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hqv : input.predictable_quadratic_variation_stabilization)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLoading index (controlScore index control))
    (htreatedLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedLoading index cell| ≤ treatedEnvelope index)
    (hcontrolLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlLoading index cell| ≤ controlEnvelope index)
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
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_lindeberg_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedLoading controlLoading
    treatedEnvelope controlEnvelope input hinputLindeberg hexact hregularity
    (hmartingaleMap htreatedMartingale hcontrolMartingale) hqv
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
    htreatedCoefficient hcontrolCoefficient htreatedLoadingBound
    hcontrolLoadingBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq TreatedCell] [DecidableEq ControlCell] in
/--
Finite score-cell coefficient loadings with envelope-scaled residual
third-moment control close the conditional-Lindeberg field of a residual
martingale-array input.
-/
theorem input_conditional_lindeberg_of_twoArm_scoreCellLoading_envelopes
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
    (treatedLoading : Index -> TreatedCell -> Real)
    (controlLoading : Index -> ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLoading index (controlScore index control))
    (htreatedLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedLoading index cell| ≤ treatedEnvelope index)
    (hcontrolLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlLoading index cell| ≤ controlEnvelope index)
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
    input.conditional_lindeberg := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual
      treatedScore controlScore treatedLoading controlLoading
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedCoefficient hcontrolCoefficient htreatedLoadingBound
      hcontrolLoadingBound htreatedEnvelopeBound hcontrolEnvelopeBound
  exact hinputLindeberg hlindeberg

omit [DecidableEq TreatedCell] [DecidableEq ControlCell] in
/--
Finite score-cell coefficient loadings with envelope-scaled residual
third-moment control close the conditional-Lindeberg field of an explicit
triangular martingale-array CLT bridge.
-/
theorem triangular_conditional_lindeberg_of_twoArm_scoreCellLoading_envelopes
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
    (treatedLoading : Index -> TreatedCell -> Real)
    (controlLoading : Index -> ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLoading index (controlScore index control))
    (htreatedLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedLoading index cell| ≤ treatedEnvelope index)
    (hcontrolLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlLoading index cell| ≤ controlEnvelope index)
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
    martingaleCLT.conditional_lindeberg := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual
      treatedScore controlScore treatedLoading controlLoading
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedCoefficient hcontrolCoefficient htreatedLoadingBound
      hcontrolLoadingBound htreatedEnvelopeBound hcontrolEnvelopeBound
  exact hlindebergTransfer hlindeberg

omit [DecidableEq TreatedCell] [DecidableEq ControlCell] in
/--
Residual CLT and variance formula from finite score-cell coefficient loadings
and envelope-scaled residual third-moment control, routed directly through an
explicit triangular martingale-array CLT bridge.

This is the triangular counterpart of
`residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_lindeberg_bridge`:
the concrete score-cell envelope lemma supplies the triangular Lindeberg field,
while the martingale-difference and predictable-QV fields remain explicit.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_envelopes_triangular_martingale_array_clt_bridge
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
    (treatedLoading : Index -> TreatedCell -> Real)
    (controlLoading : Index -> ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
    (hmartingale : martingaleCLT.martingale_difference_array)
    (hqv : martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLoading index (controlScore index control))
    (htreatedLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedLoading index cell| ≤ treatedEnvelope index)
    (hcontrolLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlLoading index cell| ≤ controlEnvelope index)
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
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual
      treatedScore controlScore treatedLoading controlLoading
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedCoefficient hcontrolCoefficient htreatedLoadingBound
      hcontrolLoadingBound htreatedEnvelopeBound hcontrolEnvelopeBound
  exact
    residual_clt_and_variance_formula_of_twoArm_lindeberg_triangular_martingale_array_clt_bridge
      treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      martingaleCLT hlindebergTransfer hmartingale hlindeberg hqv

omit [DecidableEq TreatedCell] [DecidableEq ControlCell] in
/--
Triangular finite score-cell loading Lindeberg bridge with the
martingale-difference field supplied by concrete treated/control Mathlib
martingales.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_envelopes_mathlib_martingales_triangular
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
    (treatedLoading : Index -> TreatedCell -> Real)
    (controlLoading : Index -> ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmartingaleMap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
    (hqv : martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLoading index (controlScore index control))
    (htreatedLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedLoading index cell| ≤ treatedEnvelope index)
    (hcontrolLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlLoading index cell| ≤ controlEnvelope index)
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
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_envelopes_triangular_martingale_array_clt_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedLoading controlLoading
    treatedEnvelope controlEnvelope martingaleCLT hlindebergTransfer
    (hmartingaleMap htreatedMartingale hcontrolMartingale) hqv
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
    htreatedCoefficient hcontrolCoefficient htreatedLoadingBound
    hcontrolLoadingBound htreatedEnvelopeBound hcontrolEnvelopeBound

/--
Residual CLT and variance formula from finite score-cell coefficient loadings
and finite score-cell residual third-moment convergence.  This removes the raw
envelope-scaled third-moment premise from the martingale interface boundary.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_bridge
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
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hmartingale : input.martingale_difference_array)
    (hqv : input.predictable_quadratic_variation_stabilization)
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
    (htreatedEnvelope :
      Tendsto (fun index => treatedEnvelope index ^ 3) l (nhds 0))
    (hcontrolEnvelope :
      Tendsto (fun index => controlEnvelope index ^ 3) l (nhds 0)) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual treatedScore
      controlScore treatedCoefficientLoading controlCoefficientLoading
      treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
      controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
      htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
      htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
      htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
      htreatedEnvelope hcontrolEnvelope
  exact
    residual_clt_and_variance_formula_of_martingale_array_input input
      hexact hregularity hmartingale (hinputLindeberg hlindeberg) hqv

/--
Input-level finite score-cell third-moment Lindeberg bridge with the
martingale-difference field supplied by concrete treated/control Mathlib
martingales.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_mathlib_martingales_input
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
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmartingaleMap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          input.martingale_difference_array)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hqv : input.predictable_quadratic_variation_stabilization)
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
    (htreatedEnvelope :
      Tendsto (fun index => treatedEnvelope index ^ 3) l (nhds 0))
    (hcontrolEnvelope :
      Tendsto (fun index => controlEnvelope index ^ 3) l (nhds 0)) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    input hinputLindeberg hexact hregularity
    (hmartingaleMap htreatedMartingale hcontrolMartingale) hqv
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

/--
Finite score-cell coefficient loadings and residual third-moment control close
the conditional-Lindeberg field of a residual martingale-array input.  This is
the input-level counterpart of the triangular bridge reducer below.
-/
theorem input_conditional_lindeberg_of_twoArm_scoreCellLoading_thirdMoment
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
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
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
    (htreatedEnvelope :
      Tendsto (fun index => treatedEnvelope index ^ 3) l (nhds 0))
    (hcontrolEnvelope :
      Tendsto (fun index => controlEnvelope index ^ 3) l (nhds 0)) :
    input.conditional_lindeberg := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual treatedScore
      controlScore treatedCoefficientLoading controlCoefficientLoading
      treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
      controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
      htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
      htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
      htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
      htreatedEnvelope hcontrolEnvelope
  exact hinputLindeberg hlindeberg

/--
Envelope convergence stated as `envelope -> 0` closes the residual
martingale-array input's conditional-Lindeberg field by first deriving the
cube-envelope convergence used by the finite score-cell third-moment reducer.
-/
theorem input_conditional_lindeberg_of_twoArm_scoreCellLoading_thirdMoment_envelope
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
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
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
    input.conditional_lindeberg :=
  input_conditional_lindeberg_of_twoArm_scoreCellLoading_thirdMoment
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    input hinputLindeberg htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero treatedEnvelope
      htreatedEnvelope)
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero controlEnvelope
      hcontrolEnvelope)

/--
Finite score-cell coefficient loadings and residual third-moment control close
the conditional-Lindeberg field of an explicit triangular martingale-array CLT
bridge.  This exposes the field-level reducer used by the CLT endpoint below.
-/
theorem triangular_conditional_lindeberg_of_twoArm_scoreCellLoading_thirdMoment
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
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
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
    (htreatedEnvelope :
      Tendsto (fun index => treatedEnvelope index ^ 3) l (nhds 0))
    (hcontrolEnvelope :
      Tendsto (fun index => controlEnvelope index ^ 3) l (nhds 0)) :
    martingaleCLT.conditional_lindeberg := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual treatedScore
      controlScore treatedCoefficientLoading controlCoefficientLoading
      treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
      controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
      htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
      htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
      htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
      htreatedEnvelope hcontrolEnvelope
  exact hlindebergTransfer hlindeberg

/--
Envelope convergence stated as `envelope -> 0` closes the triangular
conditional-Lindeberg field after translating it to the cube-envelope
condition used by the finite score-cell third-moment reducer.
-/
theorem triangular_conditional_lindeberg_of_twoArm_scoreCellLoading_thirdMoment_envelope
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
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
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
    martingaleCLT.conditional_lindeberg :=
  triangular_conditional_lindeberg_of_twoArm_scoreCellLoading_thirdMoment
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    martingaleCLT hlindebergTransfer htreatedWeightNonneg
    hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
    htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero treatedEnvelope
      htreatedEnvelope)
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero controlEnvelope
      hcontrolEnvelope)

/--
Residual CLT and variance formula from finite score-cell coefficient loadings
and finite score-cell residual third-moment convergence, routed directly
through an explicit triangular martingale-array CLT bridge.  This discharges
the bridge's conditional-Lindeberg field from finite-cell WDSM data, leaving
only the martingale-difference and predictable-QV bridge fields open.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_triangular_martingale_array_clt_bridge
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
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
    (hmartingale : martingaleCLT.martingale_difference_array)
    (hqv : martingaleCLT.predictable_quadratic_variation_stabilization)
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
    (htreatedEnvelope :
      Tendsto (fun index => treatedEnvelope index ^ 3) l (nhds 0))
    (hcontrolEnvelope :
      Tendsto (fun index => controlEnvelope index ^ 3) l (nhds 0)) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual treatedScore
      controlScore treatedCoefficientLoading controlCoefficientLoading
      treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
      controlMassLimit treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
      htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
      htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
      htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
      htreatedEnvelope hcontrolEnvelope
  exact
    residual_clt_and_variance_formula_of_twoArm_lindeberg_triangular_martingale_array_clt_bridge
      treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      martingaleCLT hlindebergTransfer hmartingale hlindeberg hqv

/--
Triangular finite score-cell third-moment Lindeberg bridge with the
martingale-difference field supplied by concrete treated/control Mathlib
martingales.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_mathlib_martingales_triangular
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
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmartingaleMap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
    (hqv : martingaleCLT.predictable_quadratic_variation_stabilization)
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
    (htreatedEnvelope :
      Tendsto (fun index => treatedEnvelope index ^ 3) l (nhds 0))
    (hcontrolEnvelope :
      Tendsto (fun index => controlEnvelope index ^ 3) l (nhds 0)) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_triangular_martingale_array_clt_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    martingaleCLT hlindebergTransfer
    (hmartingaleMap htreatedMartingale hcontrolMartingale) hqv
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

/--
Residual CLT and variance formula from finite score-cell coefficient loadings
and finite score-cell residual third-moment convergence, with vanishing
coefficient envelopes stated directly as `envelope -> 0`.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_bridge
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
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hmartingale : input.martingale_difference_array)
    (hqv : input.predictable_quadratic_variation_stabilization)
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
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    input hinputLindeberg hexact hregularity hmartingale hqv
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero treatedEnvelope
      htreatedEnvelope)
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero controlEnvelope
      hcontrolEnvelope)

/--
Input-level finite score-cell third-moment bridge with paper-style envelope
convergence and the martingale-difference field supplied by concrete
treated/control Mathlib martingales.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_mathlib_martingales_input
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
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmartingaleMap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          input.martingale_difference_array)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hqv : input.predictable_quadratic_variation_stabilization)
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
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    input hinputLindeberg hexact hregularity
    (hmartingaleMap htreatedMartingale hcontrolMartingale) hqv
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

/--
Triangular residual CLT and variance formula from finite score-cell
coefficient loadings and finite score-cell residual third-moment convergence,
with vanishing coefficient envelopes stated directly as `envelope -> 0`.

This is the triangular counterpart of
`residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_bridge`:
it derives the cube-envelope condition and then closes the triangular
conditional-Lindeberg field.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_triangular_martingale_array_clt_bridge
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
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
    (hmartingale : martingaleCLT.martingale_difference_array)
    (hqv : martingaleCLT.predictable_quadratic_variation_stabilization)
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
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_triangular_martingale_array_clt_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    martingaleCLT hlindebergTransfer hmartingale hqv htreatedWeightNonneg
    hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
    htreatedCover hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero treatedEnvelope
      htreatedEnvelope)
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero controlEnvelope
      hcontrolEnvelope)

/--
Triangular finite score-cell third-moment bridge with paper-style envelope
convergence and the martingale-difference field supplied by concrete
treated/control Mathlib martingales.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_mathlib_martingales_triangular
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
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmartingaleMap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
    (hqv : martingaleCLT.predictable_quadratic_variation_stabilization)
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
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_triangular_martingale_array_clt_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    martingaleCLT hlindebergTransfer
    (hmartingaleMap htreatedMartingale hcontrolMartingale) hqv
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

end WDSM
end Matching
end StatInference
