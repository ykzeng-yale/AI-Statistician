import StatInference.Matching.WDSM.RetrospectivePATEDecomposition
import StatInference.Matching.WDSM.AggregateLipschitzBiasBound

/-!
# Retrospective PATE discrepancy bias bound

This module connects the corrected finite discrepancy term from
`RetrospectivePATEDecomposition` to the existing Lipschitz/radius bias
machinery.  It is still deterministic: stochastic rates for the radii are
separate assumptions or later theorems.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
The corrected retrospective PATE discrepancy numerator is the difference of
two weighted aggregate mean-discrepancy sums, one for each matched arm.
-/
theorem retrospectivePATEDiscrepancyNumerator_eq_two_arm_meanDiscrepancy
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight mu0 mu1 : Unit -> Real) :
    retrospectivePATEDiscrepancyNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
        mu1 =
      weightedSum treatedSet treatedWeight
        (fun treated =>
          meanDiscrepancy controlSet controlCoefficient mu0 treated) -
        weightedSum controlSet controlWeight
          (fun control =>
            meanDiscrepancy treatedSet treatedCoefficient mu1 control) := by
  unfold retrospectivePATEDiscrepancyNumerator meanDiscrepancy weightedSum
  simp [mul_neg, Finset.sum_neg_distrib]
  ring

/--
Deterministic total-denominator bias bound for the corrected retrospective
PATE discrepancy term.

The treated-focal side is controlled by the control-outcome regression
Lipschitz constant and control matched-set radii.  The control-focal side is
controlled by the treated-outcome regression Lipschitz constant and treated
matched-set radii.
-/
theorem abs_retrospectivePATEDiscrepancy_average_le_lipschitz_radius_average
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight controlWeight mu0 mu1 : Unit -> Real)
    (controlScoreDistance treatedScoreDistance : Unit -> Unit -> Real)
    (controlLipschitz treatedLipschitz : Real)
    (controlRadius treatedRadius : Unit -> Real)
    (hden_pos :
      0 <
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight)
    (htreatedWeight_nonneg :
      ∀ treated, treated ∈ treatedSet -> 0 ≤ treatedWeight treated)
    (hcontrolWeight_nonneg :
      ∀ control, control ∈ controlSet -> 0 ≤ controlWeight control)
    (hcontrolCoeff_nonneg :
      ∀ treated, treated ∈ treatedSet ->
        ∀ control, control ∈ controlSet ->
          0 ≤ controlCoefficient treated control)
    (htreatedCoeff_nonneg :
      ∀ control, control ∈ controlSet ->
        ∀ treated, treated ∈ treatedSet ->
          0 ≤ treatedCoefficient control treated)
    (hcontrolCoeff_sum :
      ∀ treated, treated ∈ treatedSet ->
        (∑ control ∈ controlSet,
          controlCoefficient treated control) = 1)
    (htreatedCoeff_sum :
      ∀ control, control ∈ controlSet ->
        (∑ treated ∈ treatedSet,
          treatedCoefficient control treated) = 1)
    (hcontrol_lipschitz :
      ∀ treated, treated ∈ treatedSet ->
        ∀ control, control ∈ controlSet ->
          |mu0 treated - mu0 control| ≤
            controlLipschitz * controlScoreDistance treated control)
    (htreated_lipschitz :
      ∀ control, control ∈ controlSet ->
        ∀ treated, treated ∈ treatedSet ->
          |mu1 control - mu1 treated| ≤
            treatedLipschitz * treatedScoreDistance control treated)
    (hcontrol_radius :
      ∀ treated, treated ∈ treatedSet ->
        ∀ control, control ∈ controlSet ->
          controlScoreDistance treated control ≤ controlRadius treated)
    (htreated_radius :
      ∀ control, control ∈ controlSet ->
        ∀ treated, treated ∈ treatedSet ->
          treatedScoreDistance control treated ≤ treatedRadius control)
    (hcontrol_lipschitz_nonneg : 0 ≤ controlLipschitz)
    (htreated_lipschitz_nonneg : 0 ≤ treatedLipschitz) :
    |retrospectivePATEDiscrepancyNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
        mu1 /
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight| ≤
      (weightedSum treatedSet treatedWeight
          (fun treated => controlLipschitz * controlRadius treated) +
        weightedSum controlSet controlWeight
          (fun control => treatedLipschitz * treatedRadius control)) /
        retrospectivePATEDenominator treatedSet controlSet treatedWeight
          controlWeight := by
  let treatedDiscrepancy : Real :=
    weightedSum treatedSet treatedWeight
      (fun treated =>
        meanDiscrepancy controlSet controlCoefficient mu0 treated)
  let controlDiscrepancy : Real :=
    weightedSum controlSet controlWeight
      (fun control =>
        meanDiscrepancy treatedSet treatedCoefficient mu1 control)
  let treatedBound : Real :=
    weightedSum treatedSet treatedWeight
      (fun treated => controlLipschitz * controlRadius treated)
  let controlBound : Real :=
    weightedSum controlSet controlWeight
      (fun control => treatedLipschitz * treatedRadius control)
  have hdisc :
      retrospectivePATEDiscrepancyNumerator treatedSet controlSet
          treatedCoefficient controlCoefficient treatedWeight controlWeight mu0
          mu1 = treatedDiscrepancy - controlDiscrepancy := by
    unfold treatedDiscrepancy controlDiscrepancy
    exact retrospectivePATEDiscrepancyNumerator_eq_two_arm_meanDiscrepancy
      treatedSet controlSet treatedCoefficient controlCoefficient
      treatedWeight controlWeight mu0 mu1
  have htreatedBound :
      |treatedDiscrepancy| ≤ treatedBound := by
    unfold treatedDiscrepancy treatedBound
    exact abs_weightedSum_le_weightedSum_bound treatedSet treatedWeight
      (fun treated =>
        meanDiscrepancy controlSet controlCoefficient mu0 treated)
      (fun treated => controlLipschitz * controlRadius treated)
      htreatedWeight_nonneg
      (fun treated htreated =>
        abs_meanDiscrepancy_le_lipschitz_radius controlSet
          controlCoefficient mu0 controlScoreDistance treated
          controlLipschitz (controlRadius treated)
          (hcontrolCoeff_nonneg treated htreated)
          (hcontrolCoeff_sum treated htreated)
          (hcontrol_lipschitz treated htreated)
          (hcontrol_radius treated htreated)
          hcontrol_lipschitz_nonneg)
  have hcontrolBound :
      |controlDiscrepancy| ≤ controlBound := by
    unfold controlDiscrepancy controlBound
    exact abs_weightedSum_le_weightedSum_bound controlSet controlWeight
      (fun control =>
        meanDiscrepancy treatedSet treatedCoefficient mu1 control)
      (fun control => treatedLipschitz * treatedRadius control)
      hcontrolWeight_nonneg
      (fun control hcontrol =>
        abs_meanDiscrepancy_le_lipschitz_radius treatedSet
          treatedCoefficient mu1 treatedScoreDistance control
          treatedLipschitz (treatedRadius control)
          (htreatedCoeff_nonneg control hcontrol)
          (htreatedCoeff_sum control hcontrol)
          (htreated_lipschitz control hcontrol)
          (htreated_radius control hcontrol)
          htreated_lipschitz_nonneg)
  have hdiff :
      |treatedDiscrepancy - controlDiscrepancy| ≤
        treatedBound + controlBound := by
    calc
      |treatedDiscrepancy - controlDiscrepancy| =
          |treatedDiscrepancy + -controlDiscrepancy| := by ring_nf
      _ ≤ |treatedDiscrepancy| + |-controlDiscrepancy| := by
        exact abs_add_le treatedDiscrepancy (-controlDiscrepancy)
      _ = |treatedDiscrepancy| + |controlDiscrepancy| := by
        rw [abs_neg]
      _ ≤ treatedBound + controlBound :=
        add_le_add htreatedBound hcontrolBound
  rw [hdisc]
  rw [abs_div, abs_of_nonneg hden_pos.le]
  exact div_le_div_of_nonneg_right hdiff hden_pos.le

end WDSM
end Matching
end StatInference
