import StatInference.Matching.WDSM.FiniteCellResidualThirdMoment

/-!
# Eventually valid finite-cell residual third-moment bridges

The base finite-cell residual third-moment module assumes score-cell coverage
and residual third-moment score-measurability for every index.  WDSM
asymptotic arguments usually obtain these identities only eventually, after
estimated scores, denominators, and finite partitions are well-defined.  This
module proves the corresponding eventual versions without changing the
lower-level finite algebra.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Treated Control Cell TreatedCell ControlCell : Type*}
  {l : Filter Index} [DecidableEq Cell] [DecidableEq TreatedCell]
  [DecidableEq ControlCell]

/--
Cellwise score-cell mass convergence gives convergence of residual third
moments when score-cell coverage and third-moment score-measurability hold
eventually.
-/
theorem tendsto_residualThirdMomentSum_of_eventually_scoreMeasurable_cellwiseScoreCellMassLLN
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (residual : Index -> Unit -> Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          loading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit) :
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
  have heq :
      (fun index =>
        residualThirdMomentSum (sample index) (weight index)
          (residual index)) =ᶠ[l]
      (fun index =>
        weightedScoreCellMoment cells (sample index) (weight index)
          (score index) loading) := by
    filter_upwards [hcover, hloading] with index hcoverIndex hloadingIndex
    exact
      residualThirdMomentSum_eq_weightedScoreCellMoment_of_scoreMeasurable
        cells (sample index) (weight index) (residual index)
        (score index) loading hcoverIndex hloadingIndex
  exact hmom.congr' heq.symm

/--
If eventual finite-cell residual third-moment measurability holds and the
coefficient envelope cubed vanishes, then the envelope-scaled residual third
moment vanishes.
-/
theorem tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_eventually_cellwise
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (residual : Index -> Unit -> Real)
    (envelope : Index -> Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          loading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit)
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
    tendsto_residualThirdMomentSum_of_eventually_scoreMeasurable_cellwiseScoreCellMassLLN
      cells sample weight score residual loading massLimit hcover hloading
      hmass
  simpa using henvelope.mul hthird

/--
Eventual finite-cell residual third-moment measurability plus a vanishing
coefficient envelope implies a negligible envelope-scaled third moment.
-/
theorem tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_eventually_cellwise_of_tendsto_envelope_zero
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (residual : Index -> Unit -> Real)
    (envelope : Index -> Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          loading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit)
    (henvelope : Tendsto envelope l (nhds 0)) :
    Tendsto
      (fun index =>
        envelope index ^ 3 *
          residualThirdMomentSum (sample index) (weight index)
            (residual index))
      l (nhds 0) :=
  tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_eventually_cellwise
    cells sample weight score residual envelope loading massLimit hcover
    hloading hmass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero envelope henvelope)

/--
One-arm residual Lindeberg condition from eventual finite-cell coverage,
eventual third-moment score-measurability, finite loading envelopes, and a
vanishing coefficient envelope.
-/
theorem residualLindebergCondition_of_eventually_scoreCellLoading_envelope_and_thirdMoment
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
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
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
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          thirdMomentLoading (score index unit) =
            |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit)
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
    tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_eventually_cellwise
      cells sample weight score residual envelope thirdMomentLoading
      massLimit hcover hthirdLoading hmass henvelope
  exact
    residualLindebergCondition_of_scoreCellLoading_envelope
      cells sample weight score coefficient residual coefficientLoading
      envelope hweight_nonneg hcover hcoefficient hcoefficientLoadingBound
      hthird_negligible

/--
One-arm residual Lindeberg condition from eventual finite-cell assumptions,
with envelope convergence stated before cubing.
-/
theorem residualLindebergCondition_of_eventually_scoreCellLoading_envelope_and_thirdMoment_of_tendsto_envelope_zero
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
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
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
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          thirdMomentLoading (score index unit) =
            |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit)
    (henvelope : Tendsto envelope l (nhds 0)) :
    residualLindebergCondition (l := l) sample weight coefficient residual :=
  residualLindebergCondition_of_eventually_scoreCellLoading_envelope_and_thirdMoment
    cells sample weight score coefficient residual coefficientLoading
    thirdMomentLoading massLimit envelope hweight_nonneg hcover
    hcoefficient hcoefficientLoadingBound hthirdLoading hmass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero envelope henvelope)

/--
Two-arm residual Lindeberg condition from eventual finite-cell coverage,
eventual third-moment score-measurability, finite loading envelopes, and
vanishing coefficient envelopes.
-/
theorem twoArmResidualLindebergCondition_of_eventually_scoreCellLoading_envelopes_and_thirdMoments
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
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedThirdMomentLoading (treatedScore index treated) =
            |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
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
    tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_eventually_cellwise
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
    tendsto_envelope_cube_mul_residualThirdMomentSum_zero_of_eventually_cellwise
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
      hcontrolWeightNonneg htreatedCover hcontrolCover htreatedCoefficient
      hcontrolCoefficient htreatedCoefficientLoadingBound
      hcontrolCoefficientLoadingBound htreatedThirdNegligible
      hcontrolThirdNegligible

/--
Two-arm residual Lindeberg condition from eventual finite-cell assumptions,
with envelope convergence stated before cubing.
-/
theorem twoArmResidualLindebergCondition_of_eventually_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
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
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedThirdMomentLoading (treatedScore index treated) =
            |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
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
  twoArmResidualLindebergCondition_of_eventually_scoreCellLoading_envelopes_and_thirdMoments
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedCoefficientLoading
    controlCoefficientLoading treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedEnvelope controlEnvelope
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
    htreatedCoefficient hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero treatedEnvelope
      htreatedEnvelope)
    (tendsto_envelope_cube_zero_of_tendsto_envelope_zero controlEnvelope
      hcontrolEnvelope)

end WDSM
end Matching
end StatInference
