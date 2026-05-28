import StatInference.Matching.WDSM.ResidualCoefficientLyapunov

/-!
# Two-arm residual coefficient Lyapunov bounds

This module combines the one-arm residual coefficient Lyapunov/Lindeberg
control into the two-arm residual array shape used by prospective PATE and
one-sided PATT residual CLT audits.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Treated Control : Type*}

/-- Two-arm quadratic Lindeberg tail for residual contributions. -/
noncomputable def twoArmResidualLindebergTailSum
    (treatedSample : Finset Treated) (controlSample : Finset Control)
    (treatedWeight treatedCoefficient treatedResidual : Treated -> Real)
    (controlWeight controlCoefficient controlResidual : Control -> Real)
    (epsilon : Real) : Real :=
  lindebergQuadraticTailSum treatedSample treatedWeight
      (fun treated => treatedCoefficient treated * treatedResidual treated)
      epsilon +
    lindebergQuadraticTailSum controlSample controlWeight
      (fun control => controlCoefficient control * controlResidual control)
      epsilon

/--
Component Lindeberg-tail convergence gives two-arm residual Lindeberg-tail
convergence.
-/
theorem tendsto_twoArmResidualLindebergTailSum_zero_of_components
    {Index : Type*} {l : Filter Index}
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    {epsilon : Real}
    (htreated :
      Tendsto
        (fun index =>
          lindebergQuadraticTailSum (treatedSample index)
            (treatedWeight index)
            (fun treated =>
              treatedCoefficient index treated *
                treatedResidual index treated)
            epsilon)
        l (nhds 0))
    (hcontrol :
      Tendsto
        (fun index =>
          lindebergQuadraticTailSum (controlSample index)
            (controlWeight index)
            (fun control =>
              controlCoefficient index control *
                controlResidual index control)
            epsilon)
        l (nhds 0)) :
    Tendsto
      (fun index =>
        twoArmResidualLindebergTailSum (treatedSample index)
          (controlSample index) (treatedWeight index)
          (treatedCoefficient index) (treatedResidual index)
          (controlWeight index) (controlCoefficient index)
          (controlResidual index) epsilon)
      l (nhds 0) := by
  unfold twoArmResidualLindebergTailSum
  simpa using htreated.add hcontrol

/--
Two-arm residual Lindeberg tails vanish when each arm has nonnegative weights,
an eventual coefficient envelope, and an envelope-scaled residual third moment
converging to zero.
-/
theorem tendsto_twoArmResidualLindebergTailSum_zero_of_envelopes
    {Index : Type*} {l : Filter Index}
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    {epsilon : Real} (hepsilon : 0 < epsilon)
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
          epsilon⁻¹ *
            (treatedEnvelope index ^ 3 *
              residualThirdMomentSum (treatedSample index)
                (treatedWeight index) (treatedResidual index)))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          epsilon⁻¹ *
            (controlEnvelope index ^ 3 *
              residualThirdMomentSum (controlSample index)
                (controlWeight index) (controlResidual index)))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        twoArmResidualLindebergTailSum (treatedSample index)
          (controlSample index) (treatedWeight index)
          (treatedCoefficient index) (treatedResidual index)
          (controlWeight index) (controlCoefficient index)
          (controlResidual index) epsilon)
      l (nhds 0) := by
  have htreated :
      Tendsto
        (fun index =>
          lindebergQuadraticTailSum (treatedSample index)
            (treatedWeight index)
            (fun treated =>
              treatedCoefficient index treated *
                treatedResidual index treated)
            epsilon)
        l (nhds 0) :=
    tendsto_residual_lindeberg_tail_zero_of_envelope
      treatedSample treatedWeight treatedCoefficient treatedResidual
      treatedEnvelope hepsilon htreatedWeightNonneg htreatedCoeffBound
      htreatedEnvelopeBound
  have hcontrol :
      Tendsto
        (fun index =>
          lindebergQuadraticTailSum (controlSample index)
            (controlWeight index)
            (fun control =>
              controlCoefficient index control *
                controlResidual index control)
            epsilon)
        l (nhds 0) :=
    tendsto_residual_lindeberg_tail_zero_of_envelope
      controlSample controlWeight controlCoefficient controlResidual
      controlEnvelope hepsilon hcontrolWeightNonneg hcontrolCoeffBound
      hcontrolEnvelopeBound
  exact tendsto_twoArmResidualLindebergTailSum_zero_of_components
    treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    htreated hcontrol

end WDSM
end Matching
end StatInference
