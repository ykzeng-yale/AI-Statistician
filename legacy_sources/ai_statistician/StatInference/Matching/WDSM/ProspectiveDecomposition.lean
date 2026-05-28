import StatInference.Matching.WDSM.RetrospectivePATEBiasBound
import StatInference.Matching.WDSM.RetrospectivePATTBiasBound

/-!
# Prospective common-weight decomposition and discrepancy bounds

This module records the prospective/common-weight specialization of the
retrospective WDSM decomposition layer.  The statements are deterministic:
prospective sampling changes the survey-weight pattern to a single common
weight, while the finite matching algebra, residual reuse, and Lipschitz
discrepancy bounds are inherited from the retrospective proofs.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit : Type*}

/--
Prospective/common-weight PATE exact decomposition.  This is the checked
finite decomposition used before attaching prospective known-score or
estimated-score probability interfaces.
-/
theorem prospectivePATE_hajek_exact_decomposition
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (commonWeight : Real)
    (mu0 mu1 residual : Unit -> Real) (tau : Real)
    (hden :
      retrospectivePATEDenominator treatedSet controlSet
          (fun _unit : Unit => commonWeight)
          (fun _unit : Unit => commonWeight) ≠ 0)
    (htreatedCoeffSum :
      ∀ control, control ∈ controlSet ->
        (∑ treated ∈ treatedSet,
          treatedCoefficient control treated) = 1)
    (hcontrolCoeffSum :
      ∀ treated, treated ∈ treatedSet ->
        (∑ control ∈ controlSet,
          controlCoefficient treated control) = 1) :
    retrospectivePATEContrastNumerator treatedSet controlSet
        treatedCoefficient controlCoefficient
        (fun _unit : Unit => commonWeight)
        (fun _unit : Unit => commonWeight) mu0 mu1 residual /
        retrospectivePATEDenominator treatedSet controlSet
          (fun _unit : Unit => commonWeight)
          (fun _unit : Unit => commonWeight) -
        tau =
      (retrospectivePATEHeterogeneityNumerator treatedSet controlSet
          (fun _unit : Unit => commonWeight)
          (fun _unit : Unit => commonWeight) mu0 mu1 tau +
          retrospectivePATEDonorResidualNumerator treatedSet controlSet
            treatedCoefficient controlCoefficient
            (fun _unit : Unit => commonWeight)
            (fun _unit : Unit => commonWeight) residual +
          retrospectivePATEDiscrepancyNumerator treatedSet controlSet
            treatedCoefficient controlCoefficient
            (fun _unit : Unit => commonWeight)
            (fun _unit : Unit => commonWeight) mu0 mu1) /
        retrospectivePATEDenominator treatedSet controlSet
          (fun _unit : Unit => commonWeight)
          (fun _unit : Unit => commonWeight) := by
  exact retrospectivePATE_hajek_exact_decomposition_corrected_sign
    treatedSet controlSet treatedCoefficient controlCoefficient
    (fun _unit : Unit => commonWeight)
    (fun _unit : Unit => commonWeight) mu0 mu1 residual tau hden
    htreatedCoeffSum hcontrolCoeffSum

/--
Prospective/common-weight PATE deterministic discrepancy bound.  The only new
assumption relative to the retrospective theorem is nonnegativity of the
single common survey weight.
-/
theorem abs_prospectivePATEDiscrepancy_average_le_lipschitz_radius_average
    (treatedSet controlSet : Finset Unit)
    (treatedCoefficient controlCoefficient : Unit -> Unit -> Real)
    (commonWeight : Real)
    (mu0 mu1 : Unit -> Real)
    (controlScoreDistance treatedScoreDistance : Unit -> Unit -> Real)
    (controlLipschitz treatedLipschitz : Real)
    (controlRadius treatedRadius : Unit -> Real)
    (hden_pos :
      0 <
        retrospectivePATEDenominator treatedSet controlSet
          (fun _unit : Unit => commonWeight)
          (fun _unit : Unit => commonWeight))
    (hcommonWeight_nonneg : 0 ≤ commonWeight)
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
        treatedCoefficient controlCoefficient
        (fun _unit : Unit => commonWeight)
        (fun _unit : Unit => commonWeight) mu0 mu1 /
        retrospectivePATEDenominator treatedSet controlSet
          (fun _unit : Unit => commonWeight)
          (fun _unit : Unit => commonWeight)| ≤
      (weightedSum treatedSet (fun _unit : Unit => commonWeight)
          (fun treated => controlLipschitz * controlRadius treated) +
        weightedSum controlSet (fun _unit : Unit => commonWeight)
          (fun control => treatedLipschitz * treatedRadius control)) /
        retrospectivePATEDenominator treatedSet controlSet
          (fun _unit : Unit => commonWeight)
          (fun _unit : Unit => commonWeight) := by
  exact
    abs_retrospectivePATEDiscrepancy_average_le_lipschitz_radius_average
      treatedSet controlSet treatedCoefficient controlCoefficient
      (fun _unit : Unit => commonWeight)
      (fun _unit : Unit => commonWeight) mu0 mu1 controlScoreDistance
      treatedScoreDistance controlLipschitz treatedLipschitz controlRadius
      treatedRadius hden_pos
      (fun _treated _htreated => hcommonWeight_nonneg)
      (fun _control _hcontrol => hcommonWeight_nonneg)
      hcontrolCoeff_nonneg htreatedCoeff_nonneg hcontrolCoeff_sum
      htreatedCoeff_sum hcontrol_lipschitz htreated_lipschitz
      hcontrol_radius htreated_radius hcontrol_lipschitz_nonneg
      htreated_lipschitz_nonneg

/--
Prospective/common-weight PATT exact decomposition.  This is the one-sided
counterpart needed for the prospective PATT appendix route.
-/
theorem prospectivePATT_hajek_exact_decomposition
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (commonWeight : Real)
    (mu0 mu1 treatedResidual controlResidual : Unit -> Real)
    (tau : Real)
    (hden :
      retrospectivePATTDenominator treatedSet
          (fun _unit : Unit => commonWeight) ≠ 0)
    (hcontrolCoeffSum :
      ∀ treated, treated ∈ treatedSet ->
        (∑ control ∈ controlSet,
          controlCoefficient treated control) = 1) :
    retrospectivePATTContrastNumerator treatedSet controlSet
        controlCoefficient (fun _unit : Unit => commonWeight) mu0 mu1
        treatedResidual controlResidual /
        retrospectivePATTDenominator treatedSet
          (fun _unit : Unit => commonWeight) -
        tau =
      (retrospectivePATTHeterogeneityNumerator treatedSet
          (fun _unit : Unit => commonWeight) mu0 mu1 tau +
          retrospectivePATTDonorResidualNumerator treatedSet controlSet
            controlCoefficient (fun _unit : Unit => commonWeight)
            treatedResidual controlResidual +
          retrospectivePATTDiscrepancyNumerator treatedSet controlSet
            controlCoefficient (fun _unit : Unit => commonWeight) mu0) /
        retrospectivePATTDenominator treatedSet
          (fun _unit : Unit => commonWeight) := by
  exact retrospectivePATT_hajek_exact_decomposition treatedSet controlSet
    controlCoefficient (fun _unit : Unit => commonWeight) mu0 mu1
    treatedResidual controlResidual tau hden hcontrolCoeffSum

/--
Prospective/common-weight PATT deterministic discrepancy bound.
-/
theorem abs_prospectivePATTDiscrepancy_average_le_lipschitz_radius_average
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (commonWeight : Real)
    (mu0 : Unit -> Real)
    (controlScoreDistance : Unit -> Unit -> Real)
    (controlLipschitz : Real)
    (controlRadius : Unit -> Real)
    (hden_pos :
      0 <
        retrospectivePATTDenominator treatedSet
          (fun _unit : Unit => commonWeight))
    (hcommonWeight_nonneg : 0 ≤ commonWeight)
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
        controlCoefficient (fun _unit : Unit => commonWeight) mu0 /
        retrospectivePATTDenominator treatedSet
          (fun _unit : Unit => commonWeight)| ≤
      weightedSum treatedSet (fun _unit : Unit => commonWeight)
        (fun treated => controlLipschitz * controlRadius treated) /
        retrospectivePATTDenominator treatedSet
          (fun _unit : Unit => commonWeight) := by
  exact
    abs_retrospectivePATTDiscrepancy_average_le_lipschitz_radius_average
      treatedSet controlSet controlCoefficient
      (fun _unit : Unit => commonWeight) mu0 controlScoreDistance
      controlLipschitz controlRadius hden_pos
      (fun _treated _htreated => hcommonWeight_nonneg)
      hcontrolCoeff_nonneg hcontrolCoeff_sum hcontrol_lipschitz
      hcontrol_radius hcontrol_lipschitz_nonneg

end WDSM
end Matching
end StatInference
