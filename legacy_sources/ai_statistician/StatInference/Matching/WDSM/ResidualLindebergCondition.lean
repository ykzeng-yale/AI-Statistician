import StatInference.Matching.WDSM.TwoArmResidualCoefficientLyapunov

/-!
# Residual Lindeberg conditions from coefficient envelopes

The residual CLT interface needs a quantified Lindeberg condition over every
positive threshold.  The lower-level Lyapunov modules prove fixed-threshold
tail convergence.  This module packages those fixed-threshold bounds into
one-arm and two-arm Lindeberg conditions using a single unscaled envelope
third-moment convergence premise.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Treated Control : Type*} {l : Filter Index}

/-- One-arm residual Lindeberg condition for WDSM residual contributions. -/
def residualLindebergCondition
    (sample : Index -> Finset Unit)
    (weight coefficient residual : Index -> Unit -> Real) : Prop :=
  ∀ epsilon : Real, 0 < epsilon ->
    Tendsto
      (fun index =>
        lindebergQuadraticTailSum (sample index) (weight index)
          (fun unit => coefficient index unit * residual index unit)
          epsilon)
      l (nhds 0)

/-- Two-arm residual Lindeberg condition for WDSM residual contributions. -/
def twoArmResidualLindebergCondition
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real) : Prop :=
  ∀ epsilon : Real, 0 < epsilon ->
    Tendsto
      (fun index =>
        twoArmResidualLindebergTailSum (treatedSample index)
          (controlSample index) (treatedWeight index)
          (treatedCoefficient index) (treatedResidual index)
          (controlWeight index) (controlCoefficient index)
          (controlResidual index) epsilon)
      l (nhds 0)

/--
An unscaled coefficient-envelope third-moment bound implies the one-arm
residual Lindeberg condition.
-/
theorem residualLindebergCondition_of_envelope
    (sample : Index -> Finset Unit)
    (weight coefficient residual : Index -> Unit -> Real)
    (envelope : Index -> Real)
    (hweight_nonneg :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> 0 ≤ weight index unit)
    (hcoefficient_bound :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          |coefficient index unit| ≤ envelope index)
    (henvelope_bound :
      Tendsto
        (fun index =>
          envelope index ^ 3 *
            residualThirdMomentSum (sample index) (weight index)
              (residual index))
        l (nhds 0)) :
    residualLindebergCondition (l := l) sample weight coefficient residual := by
  intro epsilon hepsilon
  have hscaled :
      Tendsto
        (fun index =>
          epsilon⁻¹ *
            (envelope index ^ 3 *
              residualThirdMomentSum (sample index) (weight index)
                (residual index)))
        l (nhds 0) := by
    simpa using
      (tendsto_const_nhds.mul henvelope_bound :
        Tendsto
          (fun index =>
            epsilon⁻¹ *
              (envelope index ^ 3 *
                residualThirdMomentSum (sample index) (weight index)
                  (residual index)))
          l (nhds (epsilon⁻¹ * 0)))
  exact
    tendsto_residual_lindeberg_tail_zero_of_envelope
      sample weight coefficient residual envelope hepsilon
      hweight_nonneg hcoefficient_bound hscaled

/--
Unscaled coefficient-envelope third-moment bounds in both arms imply the
two-arm residual Lindeberg condition.
-/
theorem twoArmResidualLindebergCondition_of_envelopes
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    twoArmResidualLindebergCondition (l := l) treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual := by
  intro epsilon hepsilon
  have htreatedScaled :
      Tendsto
        (fun index =>
          epsilon⁻¹ *
            (treatedEnvelope index ^ 3 *
              residualThirdMomentSum (treatedSample index)
                (treatedWeight index) (treatedResidual index)))
        l (nhds 0) := by
    simpa using
      (tendsto_const_nhds.mul htreatedEnvelopeBound :
        Tendsto
          (fun index =>
            epsilon⁻¹ *
              (treatedEnvelope index ^ 3 *
                residualThirdMomentSum (treatedSample index)
                  (treatedWeight index) (treatedResidual index)))
          l (nhds (epsilon⁻¹ * 0)))
  have hcontrolScaled :
      Tendsto
        (fun index =>
          epsilon⁻¹ *
            (controlEnvelope index ^ 3 *
              residualThirdMomentSum (controlSample index)
                (controlWeight index) (controlResidual index)))
        l (nhds 0) := by
    simpa using
      (tendsto_const_nhds.mul hcontrolEnvelopeBound :
        Tendsto
          (fun index =>
            epsilon⁻¹ *
              (controlEnvelope index ^ 3 *
                residualThirdMomentSum (controlSample index)
                  (controlWeight index) (controlResidual index)))
          l (nhds (epsilon⁻¹ * 0)))
  exact
    tendsto_twoArmResidualLindebergTailSum_zero_of_envelopes
      treatedSample controlSample treatedWeight treatedCoefficient
      treatedResidual controlWeight controlCoefficient controlResidual
      treatedEnvelope controlEnvelope hepsilon htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCoeffBound hcontrolCoeffBound
      htreatedScaled hcontrolScaled

end WDSM
end Matching
end StatInference
