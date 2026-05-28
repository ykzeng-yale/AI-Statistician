import StatInference.Matching.WDSM.ResidualLindebergCondition

/-!
# Finite score-cell coefficient envelopes

WDSM residual CLT arguments require coefficient-envelope bounds.  This module
proves a deterministic finite-cell route to those bounds: if residual
coefficients are score-cell measurable and the finite cell loading is bounded
on the covered partition, then the unit-level coefficients inherit the same
envelope.  It also composes that envelope with the residual Lindeberg bridge.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Treated Control Cell TreatedCell ControlCell : Type*}
  {l : Filter Index}

/--
Finite score-cell measurable coefficients inherit any finite loading envelope
on a covering cell partition.
-/
theorem scoreCellCoefficient_bound_of_loading_bound
    (cells : Finset Cell)
    (sample : Finset Unit)
    (score : Unit -> Cell)
    (coefficient : Unit -> Real)
    (loading : Cell -> Real)
    (envelope : Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hcoefficient :
      ∀ unit, unit ∈ sample -> coefficient unit = loading (score unit))
    (hloading_bound :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ envelope) :
    ∀ unit, unit ∈ sample -> |coefficient unit| ≤ envelope := by
  intro unit hunit
  rw [hcoefficient unit hunit]
  exact hloading_bound (score unit) (hcover unit hunit)

/--
Eventual finite score-cell loading envelopes give eventual unit-level
coefficient envelopes.
-/
theorem eventually_scoreCellCoefficient_bound_of_loading_bound
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (coefficient : Index -> Unit -> Real)
    (loading : Index -> Cell -> Real)
    (envelope : Index -> Real)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcoefficient :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          coefficient index unit = loading index (score index unit))
    (hloading_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells -> |loading index cell| ≤ envelope index) :
    ∀ᶠ index in l,
      ∀ unit, unit ∈ sample index ->
        |coefficient index unit| ≤ envelope index := by
  filter_upwards [hcover, hcoefficient, hloading_bound] with
    index hcover_index hcoefficient_index hloading_index
  exact
    scoreCellCoefficient_bound_of_loading_bound cells (sample index)
      (score index) (coefficient index) (loading index) (envelope index)
      hcover_index hcoefficient_index hloading_index

/--
One-arm residual Lindeberg condition from score-cell-measurable coefficients,
bounded finite cell loadings, and an envelope-scaled residual third-moment
limit.
-/
theorem residualLindebergCondition_of_scoreCellLoading_envelope
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient residual : Index -> Unit -> Real)
    (loading : Index -> Cell -> Real)
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
          coefficient index unit = loading index (score index unit))
    (hloading_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells -> |loading index cell| ≤ envelope index)
    (henvelope_bound :
      Tendsto
        (fun index =>
          envelope index ^ 3 *
            residualThirdMomentSum (sample index) (weight index)
              (residual index))
        l (nhds 0)) :
    residualLindebergCondition (l := l) sample weight coefficient residual := by
  exact
    residualLindebergCondition_of_envelope sample weight coefficient residual
      envelope hweight_nonneg
      (eventually_scoreCellCoefficient_bound_of_loading_bound
        cells sample score coefficient loading envelope hcover hcoefficient
        hloading_bound)
      henvelope_bound

/--
Two-arm residual Lindeberg condition from score-cell-measurable coefficients,
bounded finite cell loadings in both arms, and envelope-scaled residual
third-moment limits.
-/
theorem twoArmResidualLindebergCondition_of_scoreCellLoading_envelopes
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
    twoArmResidualLindebergCondition (l := l) treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual := by
  have htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index :=
    eventually_scoreCellCoefficient_bound_of_loading_bound
      treatedCells treatedSample treatedScore treatedCoefficient
      treatedLoading treatedEnvelope htreatedCover htreatedCoefficient
      htreatedLoadingBound
  have hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index :=
    eventually_scoreCellCoefficient_bound_of_loading_bound
      controlCells controlSample controlScore controlCoefficient
      controlLoading controlEnvelope hcontrolCover hcontrolCoefficient
      hcontrolLoadingBound
  exact
    twoArmResidualLindebergCondition_of_envelopes
      treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoeffBound hcontrolCoeffBound
      htreatedEnvelopeBound hcontrolEnvelopeBound

end WDSM
end Matching
end StatInference
