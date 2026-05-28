import StatInference.Matching.WDSM.ResidualLindebergCondition
import StatInference.Matching.WDSM.AsymptoticInterfaces

/-!
# Residual martingale CLT input with concrete two-arm Lindeberg control

This module narrows the residual martingale-array interface by replacing its
abstract `conditional_lindeberg` proposition with the concrete two-arm
residual Lindeberg condition used by WDSM.  The martingale CLT itself remains
an explicit probability bridge, but the Lindeberg premise can now be supplied
by checked coefficient-envelope and residual third-moment bounds.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Treated Control : Type*} {l : Filter Index}

/--
Build a residual martingale-array input whose Lindeberg condition is the
concrete two-arm residual Lindeberg condition.
-/
def residualMartingaleArrayInputOfTwoArmLindebergCondition
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (exactWeightedReuseMomentLimits residualMomentRegularity
      martingaleDifferenceArray predictableQVStabilization
      residualCLT residualVarianceFormula : Prop)
    (martingaleCLTBridge :
      exactWeightedReuseMomentLimits ->
      residualMomentRegularity ->
      martingaleDifferenceArray ->
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      predictableQVStabilization ->
      residualCLT ∧ residualVarianceFormula) :
    ResidualMartingaleArrayCLTVarianceInput where
  exact_weighted_reuse_moment_limits := exactWeightedReuseMomentLimits
  residual_moment_regularity := residualMomentRegularity
  martingale_difference_array := martingaleDifferenceArray
  conditional_lindeberg :=
    twoArmResidualLindebergCondition (l := l) treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual
  predictable_quadratic_variation_stabilization :=
    predictableQVStabilization
  residual_clt := residualCLT
  residual_variance_formula := residualVarianceFormula
  martingale_clt_bridge := martingaleCLTBridge

/--
Build a WDSM residual martingale-array input from an external triangular
martingale-array CLT whose conditional Lindeberg premise is discharged by the
concrete two-arm residual Lindeberg condition.
-/
def residualMartingaleArrayInputOfTwoArmLindebergTriangularMartingaleArrayCLTBridge
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg) :
    ResidualMartingaleArrayCLTVarianceInput where
  exact_weighted_reuse_moment_limits := exactWeightedReuseMomentLimits
  residual_moment_regularity := residualMomentRegularity
  martingale_difference_array := martingaleCLT.martingale_difference_array
  conditional_lindeberg :=
    twoArmResidualLindebergCondition (l := l) treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual
  predictable_quadratic_variation_stabilization :=
    martingaleCLT.predictable_quadratic_variation_stabilization
  residual_clt := martingaleCLT.residual_clt
  residual_variance_formula := martingaleCLT.residual_variance_formula
  martingale_clt_bridge := by
    intro _hexact _hregularity hmartingale hlindeberg hqv
    exact martingaleCLT.bridge hmartingale
      (hlindebergTransfer hlindeberg) hqv

/--
Close a residual CLT/variance conclusion from the explicit triangular
martingale-array CLT bridge once the concrete two-arm Lindeberg condition has
already been proved.
-/
theorem residual_clt_and_variance_formula_of_twoArm_lindeberg_triangular_martingale_array_clt_bridge
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hlindebergTransfer :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      martingaleCLT.conditional_lindeberg)
    (hmartingale : martingaleCLT.martingale_difference_array)
    (hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual)
    (hqv : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT hmartingale (hlindebergTransfer hlindeberg) hqv

/--
Exact reuse moments, residual regularity, martingale difference, predictable
QV stabilization, and checked envelope/third-moment bounds imply the residual
CLT and residual variance formula through a martingale CLT bridge whose
Lindeberg premise is concrete.
-/
theorem residual_clt_and_variance_formula_of_twoArm_envelope_lindeberg_input
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (exactWeightedReuseMomentLimits residualMomentRegularity
      martingaleDifferenceArray predictableQVStabilization
      residualCLT residualVarianceFormula : Prop)
    (martingaleCLTBridge :
      exactWeightedReuseMomentLimits ->
      residualMomentRegularity ->
      martingaleDifferenceArray ->
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
      predictableQVStabilization ->
      residualCLT ∧ residualVarianceFormula)
    (hexact : exactWeightedReuseMomentLimits)
    (hregularity : residualMomentRegularity)
    (hmartingale : martingaleDifferenceArray)
    (hqv : predictableQVStabilization)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
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
    residualCLT ∧ residualVarianceFormula := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_envelopes
      treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoeffBound hcontrolCoeffBound
      htreatedEnvelopeBound hcontrolEnvelopeBound
  exact martingaleCLTBridge hexact hregularity hmartingale hlindeberg hqv

/--
Envelope-based close-out through the explicit triangular martingale-array CLT
bridge.  The checked envelope/third-moment bounds prove the concrete two-arm
Lindeberg premise; the remaining CLT step is exactly the external triangular
martingale-array interface.
-/
theorem residual_clt_and_variance_formula_of_twoArm_envelope_lindeberg_triangular_martingale_array_clt_bridge
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
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
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
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
    twoArmResidualLindebergCondition_of_envelopes
      treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoeffBound hcontrolCoeffBound
      htreatedEnvelopeBound hcontrolEnvelopeBound
  exact
    residual_clt_and_variance_formula_of_twoArm_lindeberg_triangular_martingale_array_clt_bridge
      treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      martingaleCLT hlindebergTransfer hmartingale hlindeberg hqv

/--
Structure-based version of the envelope close-out for a residual martingale
input whose `conditional_lindeberg` field is the concrete two-arm condition.
-/
theorem residual_clt_and_variance_formula_of_twoArm_envelope_lindeberg_bridge
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
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
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
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
    twoArmResidualLindebergCondition_of_envelopes
      treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      treatedEnvelope controlEnvelope htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoeffBound hcontrolCoeffBound
      htreatedEnvelopeBound hcontrolEnvelopeBound
  exact
    residual_clt_and_variance_formula_of_martingale_array_input input
      hexact hregularity hmartingale (hinputLindeberg hlindeberg) hqv

end WDSM
end Matching
end StatInference
