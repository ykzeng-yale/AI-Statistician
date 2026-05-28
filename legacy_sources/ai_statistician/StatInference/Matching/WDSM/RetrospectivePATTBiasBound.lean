import StatInference.Matching.WDSM.RetrospectivePATTDecomposition
import StatInference.Matching.WDSM.AggregateLipschitzBiasBound

/-!
# Retrospective PATT discrepancy bias bound

This module connects the finite one-sided retrospective PATT discrepancy term
to the existing Lipschitz/radius matching-bias machinery.  It is deterministic;
stochastic rates for the PATT control-score radii are later assumptions or
theorems.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit : Type*}

/--
The retrospective PATT discrepancy numerator is exactly the treated-side
survey-weighted aggregate mean discrepancy for the control outcome regression.
-/
theorem retrospectivePATTDiscrepancyNumerator_eq_meanDiscrepancy
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight mu0 : Unit -> Real) :
    retrospectivePATTDiscrepancyNumerator treatedSet controlSet
        controlCoefficient treatedWeight mu0 =
      weightedSum treatedSet treatedWeight
        (fun treated =>
          meanDiscrepancy controlSet controlCoefficient mu0 treated) := by
  rfl

/--
Deterministic treated-denominator bias bound for the retrospective PATT
matching-discrepancy term.
-/
theorem abs_retrospectivePATTDiscrepancy_average_le_lipschitz_radius_average
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight mu0 : Unit -> Real)
    (controlScoreDistance : Unit -> Unit -> Real)
    (controlLipschitz : Real)
    (controlRadius : Unit -> Real)
    (hden_pos : 0 < retrospectivePATTDenominator treatedSet treatedWeight)
    (htreatedWeight_nonneg :
      ∀ treated, treated ∈ treatedSet -> 0 ≤ treatedWeight treated)
    (hcontrolCoeff_nonneg :
      ∀ treated, treated ∈ treatedSet ->
        ∀ control, control ∈ controlSet ->
          0 ≤ controlCoefficient treated control)
    (hcontrolCoeff_sum :
      ∀ treated, treated ∈ treatedSet ->
        (∑ control ∈ controlSet,
          controlCoefficient treated control) = 1)
    (hcontrol_lipschitz :
      ∀ treated, treated ∈ treatedSet ->
        ∀ control, control ∈ controlSet ->
          |mu0 treated - mu0 control| ≤
            controlLipschitz * controlScoreDistance treated control)
    (hcontrol_radius :
      ∀ treated, treated ∈ treatedSet ->
        ∀ control, control ∈ controlSet ->
          controlScoreDistance treated control ≤ controlRadius treated)
    (hcontrol_lipschitz_nonneg : 0 ≤ controlLipschitz) :
    |retrospectivePATTDiscrepancyNumerator treatedSet controlSet
        controlCoefficient treatedWeight mu0 /
        retrospectivePATTDenominator treatedSet treatedWeight| ≤
      weightedSum treatedSet treatedWeight
        (fun treated => controlLipschitz * controlRadius treated) /
        retrospectivePATTDenominator treatedSet treatedWeight := by
  rw [retrospectivePATTDiscrepancyNumerator_eq_meanDiscrepancy]
  unfold retrospectivePATTDenominator
  exact
    abs_aggregate_meanDiscrepancy_le_lipschitz_radius_average
      treatedSet (fun _treated => controlSet) controlCoefficient
      treatedWeight mu0 controlScoreDistance controlLipschitz controlRadius
      hden_pos htreatedWeight_nonneg hcontrolCoeff_nonneg
      hcontrolCoeff_sum hcontrol_lipschitz hcontrol_radius
      hcontrol_lipschitz_nonneg

end WDSM
end Matching
end StatInference
