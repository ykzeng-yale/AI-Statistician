import StatInference.Matching.WDSM.ResidualMartingaleFiniteCellLindeberg

/-!
# Finite score-cell loading envelopes from cellwise convergence

The residual martingale layer needs a vanishing coefficient envelope.  This
module constructs a deterministic finite-cell envelope from score-cell loading
coefficients:

`sum_{cell in cells} |loading index cell|`.

Every cell loading is bounded by this envelope, and if each fixed cell loading
converges to zero, the finite envelope converges to zero.  This removes one
raw envelope premise from later WDSM coefficient instantiations.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Unit Treated Control Cell TreatedCell ControlCell : Type*}
  {l : Filter Index}

/-- Finite absolute-sum envelope for score-cell loading coefficients. -/
noncomputable def scoreCellLoadingAbsSumEnvelope
    (cells : Finset Cell)
    (loading : Index -> Cell -> Real)
    (index : Index) : Real :=
  ∑ cell ∈ cells, |loading index cell|

/-- Every fixed score-cell loading is bounded by the finite absolute-sum envelope. -/
theorem scoreCellLoadingAbsSumEnvelope_bound
    [DecidableEq Cell]
    (cells : Finset Cell)
    (loading : Index -> Cell -> Real)
    (index : Index) :
    ∀ cell, cell ∈ cells ->
      |loading index cell| ≤
        scoreCellLoadingAbsSumEnvelope cells loading index := by
  intro cell hcell
  unfold scoreCellLoadingAbsSumEnvelope
  exact
    Finset.single_le_sum
      (s := cells) (f := fun other => |loading index other|)
      (fun other _hother => abs_nonneg (loading index other)) hcell

/--
The finite absolute-sum envelope supplies an eventual cell-loading bound without
any stochastic premise.
-/
theorem eventually_scoreCellLoadingAbsSumEnvelope_bound
    [DecidableEq Cell]
    (cells : Finset Cell)
    (loading : Index -> Cell -> Real) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        |loading index cell| ≤
          scoreCellLoadingAbsSumEnvelope cells loading index := by
  exact Filter.Eventually.of_forall
    (fun index =>
      scoreCellLoadingAbsSumEnvelope_bound cells loading index)

/--
If every fixed score-cell loading converges to zero, then the finite
absolute-sum envelope converges to zero.
-/
theorem tendsto_scoreCellLoadingAbsSumEnvelope_zero
    [DecidableEq Cell]
    (cells : Finset Cell)
    (loading : Index -> Cell -> Real)
    (hloading :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell) l (nhds 0)) :
    Tendsto
      (fun index => scoreCellLoadingAbsSumEnvelope cells loading index)
      l (nhds 0) := by
  have hsum :
      Tendsto
        (fun index => ∑ cell ∈ cells, |loading index cell|)
        l (nhds 0) :=
    tendsto_sum_cell_values_zero cells
      (fun index cell => |loading index cell|)
      (fun cell hcell => by
        simpa using (hloading cell hcell).abs)
  simpa [scoreCellLoadingAbsSumEnvelope] using hsum

/--
One-arm residual Lindeberg condition from score-cell coefficient loadings that
converge cellwise to zero, finite-cell residual third-moment convergence, and
score-measurability.
-/
theorem residualLindebergCondition_of_scoreCellLoading_tendsto_zero_and_thirdMoment
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient residual : Index -> Unit -> Real)
    (coefficientLoading : Index -> Cell -> Real)
    (thirdMomentLoading massLimit : Cell -> Real)
    (hweight_nonneg :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> 0 ≤ weight index unit)
    (hcover_eventually :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcoefficient :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          coefficient index unit =
            coefficientLoading index (score index unit))
    (hloading_zero :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => coefficientLoading index cell) l (nhds 0))
    (hthirdLoading :
      ∀ index unit, unit ∈ sample index ->
        thirdMomentLoading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit) :
    residualLindebergCondition (l := l) sample weight coefficient residual :=
  residualLindebergCondition_of_scoreCellLoading_envelope_and_thirdMoment_of_tendsto_envelope_zero
    cells sample weight score coefficient residual coefficientLoading
    thirdMomentLoading massLimit
    (fun index => scoreCellLoadingAbsSumEnvelope cells coefficientLoading index)
    hweight_nonneg hcover_eventually hcover hcoefficient
    (eventually_scoreCellLoadingAbsSumEnvelope_bound cells coefficientLoading)
    hthirdLoading hmass
    (tendsto_scoreCellLoadingAbsSumEnvelope_zero cells coefficientLoading
      hloading_zero)

/--
Two-arm residual Lindeberg condition from score-cell coefficient loadings that
converge cellwise to zero in both arms, finite-cell residual third-moment
convergence, and score-measurability.
-/
theorem twoArmResidualLindebergCondition_of_scoreCellLoading_tendsto_zero_and_thirdMoments
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
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
    (htreatedLoadingZero :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedCoefficientLoading index cell) l (nhds 0))
    (hcontrolLoadingZero :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlCoefficientLoading index cell) l (nhds 0))
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
        controlWeight controlScore controlMassLimit) :
    twoArmResidualLindebergCondition (l := l) treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual :=
  twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit
    (fun index =>
      scoreCellLoadingAbsSumEnvelope treatedCells treatedCoefficientLoading
        index)
    (fun index =>
      scoreCellLoadingAbsSumEnvelope controlCells controlCoefficientLoading
        index)
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient
    (eventually_scoreCellLoadingAbsSumEnvelope_bound treatedCells
      treatedCoefficientLoading)
    (eventually_scoreCellLoadingAbsSumEnvelope_bound controlCells
      controlCoefficientLoading)
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    (tendsto_scoreCellLoadingAbsSumEnvelope_zero treatedCells
      treatedCoefficientLoading htreatedLoadingZero)
    (tendsto_scoreCellLoadingAbsSumEnvelope_zero controlCells
      controlCoefficientLoading hcontrolLoadingZero)

/--
Residual CLT and variance formula from finite score-cell coefficient loadings
that converge cellwise to zero, finite-cell residual third-moment convergence,
and the explicit residual martingale-array probability inputs.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_tendsto_zero_thirdMoment_bridge
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
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
    (htreatedLoadingZero :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedCoefficientLoading index cell) l (nhds 0))
    (hcontrolLoadingZero :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlCoefficientLoading index cell) l (nhds 0))
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
        controlWeight controlScore controlMassLimit) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_thirdMoment_envelope_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit
    (fun index =>
      scoreCellLoadingAbsSumEnvelope treatedCells treatedCoefficientLoading
        index)
    (fun index =>
      scoreCellLoadingAbsSumEnvelope controlCells controlCoefficientLoading
        index)
    input hinputLindeberg hexact hregularity hmartingale hqv
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient
    (eventually_scoreCellLoadingAbsSumEnvelope_bound treatedCells
      treatedCoefficientLoading)
    (eventually_scoreCellLoadingAbsSumEnvelope_bound controlCells
      controlCoefficientLoading)
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    (tendsto_scoreCellLoadingAbsSumEnvelope_zero treatedCells
      treatedCoefficientLoading htreatedLoadingZero)
    (tendsto_scoreCellLoadingAbsSumEnvelope_zero controlCells
      controlCoefficientLoading hcontrolLoadingZero)

end WDSM
end Matching
end StatInference
