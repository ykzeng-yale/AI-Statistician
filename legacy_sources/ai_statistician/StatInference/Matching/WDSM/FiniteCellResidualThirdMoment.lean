import StatInference.Matching.WDSM.FiniteCellCoefficientEnvelope
import StatInference.Matching.WDSM.FiniteCellMomentConvergence

/-!
# Finite score-cell residual third-moment convergence

The residual Lindeberg layer needs envelope-scaled residual third moments.
This module proves a finite-cell route to that premise: if `|residual|^3` is
score-cell measurable, the residual third-moment sum is exactly a finite
score-cell loading moment.  Cellwise score-cell mass convergence then supplies
the third-moment limit, and a vanishing coefficient envelope makes the
envelope-scaled third moment negligible.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Treated Control Cell TreatedCell ControlCell : Type*}
  {l : Filter Index} [DecidableEq Cell] [DecidableEq TreatedCell]
  [DecidableEq ControlCell]

/--
If `|residual|^3` is score-cell measurable, the residual third-moment sum is
the corresponding finite score-cell loading moment.
-/
theorem residualThirdMomentSum_eq_weightedScoreCellMoment_of_scoreMeasurable
    (cells : Finset Cell)
    (sample : Finset Unit)
    (weight residual : Unit -> Real)
    (score : Unit -> Cell)
    (loading : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hloading :
      ∀ unit, unit ∈ sample -> loading (score unit) = |residual unit| ^ 3) :
    residualThirdMomentSum sample weight residual =
      weightedScoreCellMoment cells sample weight score loading := by
  calc
    residualThirdMomentSum sample weight residual =
        weightedSampleSum sample weight (fun unit => loading (score unit)) := by
          unfold residualThirdMomentSum weightedSampleSum
          exact Finset.sum_congr rfl
            (fun unit hunit => by
              simpa using
                congrArg (fun value => weight unit * value)
                  (hloading unit hunit).symm)
    _ = weightedScoreCellMoment cells sample weight score loading := by
        unfold weightedScoreCellMoment
        exact
          weightedSampleSum_scoreFunction_eq_sum_cellValue_mul_mass
            sample cells weight score loading hcover

/--
Cellwise score-cell mass convergence gives convergence of residual third
moments when the third absolute moment is score-cell measurable.
-/
theorem tendsto_residualThirdMomentSum_of_cellwiseScoreCellMassLLN
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (residual : Index -> Unit -> Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit) :
    Tendsto
      (fun index =>
        residualThirdMomentSum (sample index) (weight index)
          (residual index))
      l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) := by
  have hmom :
      Tendsto
        (fun index =>
          weightedScoreCellMoment cells (sample index) (weight index)
            (score index) loading)
        l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) :=
    tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN
      cells sample weight score loading massLimit hmass
  convert hmom using 1
  ext index
  exact
    residualThirdMomentSum_eq_weightedScoreCellMoment_of_scoreMeasurable
      cells (sample index) (weight index) (residual index)
      (score index) loading (hcover index) (hloading index)

/--
If the finite score-cell residual third moment converges and the coefficient
envelope cubed vanishes, then the envelope-scaled third moment vanishes.
-/
theorem tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_cellwise
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (residual : Index -> Unit -> Real)
    (envelope : Index -> Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit)
    (henvelope :
      Tendsto (fun index => envelope index ^ 3) l (nhds 0)) :
    Tendsto
      (fun index =>
        envelope index ^ 3 *
          residualThirdMomentSum (sample index) (weight index)
            (residual index))
      l (nhds 0) := by
  have hthird :
      Tendsto
        (fun index =>
          residualThirdMomentSum (sample index) (weight index)
            (residual index))
        l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) :=
    tendsto_residualThirdMomentSum_of_cellwiseScoreCellMassLLN
      cells sample weight score residual loading massLimit hcover hloading
      hmass
  simpa using henvelope.mul hthird

/-- A vanishing coefficient envelope has a vanishing cubic envelope. -/
theorem tendsto_envelope_cube_zero_of_tendsto_envelope_zero
    (envelope : Index -> Real)
    (henvelope : Tendsto envelope l (nhds 0)) :
    Tendsto (fun index => envelope index ^ 3) l (nhds 0) := by
  simpa using henvelope.pow 3

/--
If the finite score-cell residual third moment converges and the coefficient
envelope itself vanishes, then the envelope-scaled third moment vanishes.
-/
theorem tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_cellwise_of_tendsto_envelope_zero
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (residual : Index -> Unit -> Real)
    (envelope : Index -> Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit)
    (henvelope : Tendsto envelope l (nhds 0)) :
    Tendsto
      (fun index =>
        envelope index ^ 3 *
          residualThirdMomentSum (sample index) (weight index)
            (residual index))
      l (nhds 0) :=
  tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_cellwise
    cells sample weight score residual envelope loading massLimit hcover
    hloading hmass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero envelope henvelope)

/--
One-arm Lindeberg condition from finite score-cell loading envelopes, finite
score-cell residual third-moment convergence, and a vanishing coefficient
envelope.
-/
theorem residualLindebergCondition_of_scoreCellLoading_envelope_and_thirdMoment
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient residual : Index -> Unit -> Real)
    (coefficientLoading : Index -> Cell -> Real)
    (thirdMomentLoading massLimit : Cell -> Real)
    (envelope : Index -> Real)
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
    (hcoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          |coefficientLoading index cell| ≤ envelope index)
    (hthirdLoading :
      ∀ index unit, unit ∈ sample index ->
        thirdMomentLoading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit)
    (henvelope :
      Tendsto (fun index => envelope index ^ 3) l (nhds 0)) :
    residualLindebergCondition (l := l) sample weight coefficient residual := by
  have hthird_negligible :
      Tendsto
        (fun index =>
          envelope index ^ 3 *
            residualThirdMomentSum (sample index) (weight index)
              (residual index))
        l (nhds 0) :=
    tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_cellwise
      cells sample weight score residual envelope thirdMomentLoading
      massLimit hcover hthirdLoading hmass henvelope
  exact
    residualLindebergCondition_of_scoreCellLoading_envelope
      cells sample weight score coefficient residual coefficientLoading
      envelope hweight_nonneg hcover_eventually hcoefficient
      hcoefficientLoadingBound hthird_negligible

/--
One-arm Lindeberg condition from finite score-cell loading envelopes, finite
score-cell residual third-moment convergence, and a vanishing coefficient
envelope stated without cubing the convergence premise.
-/
theorem residualLindebergCondition_of_scoreCellLoading_envelope_and_thirdMoment_of_tendsto_envelope_zero
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient residual : Index -> Unit -> Real)
    (coefficientLoading : Index -> Cell -> Real)
    (thirdMomentLoading massLimit : Cell -> Real)
    (envelope : Index -> Real)
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
    (hcoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          |coefficientLoading index cell| ≤ envelope index)
    (hthirdLoading :
      ∀ index unit, unit ∈ sample index ->
        thirdMomentLoading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit)
    (henvelope : Tendsto envelope l (nhds 0)) :
    residualLindebergCondition (l := l) sample weight coefficient residual :=
  residualLindebergCondition_of_scoreCellLoading_envelope_and_thirdMoment
    cells sample weight score coefficient residual coefficientLoading
    thirdMomentLoading massLimit envelope hweight_nonneg hcover_eventually
    hcover hcoefficient hcoefficientLoadingBound hthirdLoading hmass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero envelope henvelope)

/--
Two-arm Lindeberg condition from finite score-cell loading envelopes, finite
score-cell residual third-moment convergence in both arms, and vanishing
coefficient envelopes.
-/
theorem twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments
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
    twoArmResidualLindebergCondition (l := l) treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual := by
  have htreatedThirdNegligible :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0) :=
    tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_cellwise
      treatedCells treatedSample treatedWeight treatedScore treatedResidual
      treatedEnvelope treatedThirdMomentLoading treatedMassLimit
      htreatedCover htreatedThirdLoading htreatedMass htreatedEnvelope
  have hcontrolThirdNegligible :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0) :=
    tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_cellwise
      controlCells controlSample controlWeight controlScore controlResidual
      controlEnvelope controlThirdMomentLoading controlMassLimit
      hcontrolCover hcontrolThirdLoading hcontrolMass hcontrolEnvelope
  exact
    twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual treatedScore
      controlScore treatedCoefficientLoading controlCoefficientLoading
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoverEventually hcontrolCoverEventually
      htreatedCoefficient hcontrolCoefficient
      htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
      htreatedThirdNegligible hcontrolThirdNegligible

/--
Two-arm Lindeberg condition from finite score-cell loading envelopes, finite
score-cell residual third-moment convergence in both arms, and vanishing
coefficient envelopes stated without cubing the convergence premises.
-/
theorem twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
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
    twoArmResidualLindebergCondition (l := l) treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual :=
  twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes_and_thirdMoments
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero treatedEnvelope
      htreatedEnvelope)
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero controlEnvelope
      hcontrolEnvelope)

end WDSM
end Matching
end StatInference
