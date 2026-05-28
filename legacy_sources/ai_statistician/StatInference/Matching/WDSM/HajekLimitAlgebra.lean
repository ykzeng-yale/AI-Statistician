import Mathlib.Data.Real.Basic
import Mathlib.Topology.Algebra.Field
import Mathlib.Topology.Algebra.Ring.Real
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
# Hájek limit algebra for WDSM

Many WDSM probability arguments reduce to deterministic continuous-mapping
steps for ratios: a numerator converges, a denominator converges to a nonzero
limit, and therefore the Hájek ratio converges to the corresponding ratio.
This file proves those `Tendsto` algebra steps directly.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

/-- A ratio converges to the ratio of limits when the denominator limit is nonzero. -/
theorem tendsto_ratio_of_tendsto
    {Index : Type*} {l : Filter Index}
    (numerator denominator : Index -> Real) (numeratorLimit denominatorLimit : Real)
    (hnumerator : Tendsto numerator l (nhds numeratorLimit))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index => numerator index / denominator index) l
      (nhds (numeratorLimit / denominatorLimit)) := by
  exact hnumerator.div hdenominator hdenominatorLimit

/-- If the numerator tends to zero and the denominator has a nonzero limit, the ratio tends to zero. -/
theorem tendsto_ratio_zero_of_tendsto_numerator_zero
    {Index : Type*} {l : Filter Index}
    (numerator denominator : Index -> Real) (denominatorLimit : Real)
    (hnumerator : Tendsto numerator l (nhds 0))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index => numerator index / denominator index) l (nhds 0) := by
  simpa using
    tendsto_ratio_of_tendsto numerator denominator 0 denominatorLimit
      hnumerator hdenominator hdenominatorLimit

/--
Centered Hájek-ratio limit: if the numerator tends to `target * denominatorLimit`
and the denominator tends to `denominatorLimit ≠ 0`, then the ratio minus the
target tends to zero.
-/
theorem tendsto_ratio_sub_target_zero
    {Index : Type*} {l : Filter Index}
    (numerator denominator : Index -> Real) (target denominatorLimit : Real)
    (hnumerator : Tendsto numerator l (nhds (target * denominatorLimit)))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto (fun index => numerator index / denominator index - target) l
      (nhds 0) := by
  have hratio :
      Tendsto (fun index => numerator index / denominator index) l
        (nhds ((target * denominatorLimit) / denominatorLimit)) :=
    tendsto_ratio_of_tendsto numerator denominator
      (target * denominatorLimit) denominatorLimit
      hnumerator hdenominator hdenominatorLimit
  have hlimit : (target * denominatorLimit) / denominatorLimit - target = 0 := by
    field_simp [hdenominatorLimit]
    ring
  have htarget : Tendsto (fun _index : Index => target) l (nhds target) :=
    tendsto_const_nhds
  simpa [hlimit] using hratio.sub htarget

/--
If two Hájek ratios have the same numerator and denominator limits, their
difference tends to zero.
-/
theorem tendsto_ratio_sub_ratio_zero_of_tendsto_common_limits
    {Index : Type*} {l : Filter Index}
    (numeratorA denominatorA numeratorB denominatorB : Index -> Real)
    (numeratorLimit denominatorLimit : Real)
    (hnumeratorA : Tendsto numeratorA l (nhds numeratorLimit))
    (hdenominatorA : Tendsto denominatorA l (nhds denominatorLimit))
    (hnumeratorB : Tendsto numeratorB l (nhds numeratorLimit))
    (hdenominatorB : Tendsto denominatorB l (nhds denominatorLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        numeratorA index / denominatorA index -
          numeratorB index / denominatorB index)
      l (nhds 0) := by
  have hratioA :
      Tendsto (fun index => numeratorA index / denominatorA index) l
        (nhds (numeratorLimit / denominatorLimit)) :=
    tendsto_ratio_of_tendsto numeratorA denominatorA numeratorLimit
      denominatorLimit hnumeratorA hdenominatorA hdenominatorLimit
  have hratioB :
      Tendsto (fun index => numeratorB index / denominatorB index) l
        (nhds (numeratorLimit / denominatorLimit)) :=
    tendsto_ratio_of_tendsto numeratorB denominatorB numeratorLimit
      denominatorLimit hnumeratorB hdenominatorB hdenominatorLimit
  have hzero :
      numeratorLimit / denominatorLimit -
          numeratorLimit / denominatorLimit = 0 := by
    ring
  simpa [hzero] using hratioA.sub hratioB

/--
Two denominator-stabilized Hájek ratios converge jointly to their PATE-style
contrast target.
-/
theorem tendsto_ratio_contrast_of_tendsto
    {Index : Type*} {l : Filter Index}
    (treatedNumerator treatedDenominator controlNumerator controlDenominator :
      Index -> Real)
    (treatedTarget controlTarget treatedDenominatorLimit
      controlDenominatorLimit : Real)
    (htreatedNumerator :
      Tendsto treatedNumerator l
        (nhds (treatedTarget * treatedDenominatorLimit)))
    (htreatedDenominator :
      Tendsto treatedDenominator l (nhds treatedDenominatorLimit))
    (hcontrolNumerator :
      Tendsto controlNumerator l
        (nhds (controlTarget * controlDenominatorLimit)))
    (hcontrolDenominator :
      Tendsto controlDenominator l (nhds controlDenominatorLimit))
    (htreatedDenominatorLimit : treatedDenominatorLimit ≠ 0)
    (hcontrolDenominatorLimit : controlDenominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        treatedNumerator index / treatedDenominator index -
          controlNumerator index / controlDenominator index)
      l (nhds (treatedTarget - controlTarget)) := by
  have htreated :
      Tendsto
        (fun index => treatedNumerator index / treatedDenominator index)
        l (nhds treatedTarget) := by
    have hratio :=
      tendsto_ratio_of_tendsto treatedNumerator treatedDenominator
        (treatedTarget * treatedDenominatorLimit) treatedDenominatorLimit
        htreatedNumerator htreatedDenominator htreatedDenominatorLimit
    have hlimit :
        (treatedTarget * treatedDenominatorLimit) /
            treatedDenominatorLimit = treatedTarget := by
      field_simp [htreatedDenominatorLimit]
    simpa [hlimit] using hratio
  have hcontrol :
      Tendsto
        (fun index => controlNumerator index / controlDenominator index)
        l (nhds controlTarget) := by
    have hratio :=
      tendsto_ratio_of_tendsto controlNumerator controlDenominator
        (controlTarget * controlDenominatorLimit) controlDenominatorLimit
        hcontrolNumerator hcontrolDenominator hcontrolDenominatorLimit
    have hlimit :
        (controlTarget * controlDenominatorLimit) /
            controlDenominatorLimit = controlTarget := by
      field_simp [hcontrolDenominatorLimit]
    simpa [hlimit] using hratio
  exact htreated.sub hcontrol

/--
Centered PATE-style Hájek contrast limit: the treated/control ratio contrast
minus its target converges to zero.
-/
theorem tendsto_ratio_contrast_sub_target_zero
    {Index : Type*} {l : Filter Index}
    (treatedNumerator treatedDenominator controlNumerator controlDenominator :
      Index -> Real)
    (treatedTarget controlTarget treatedDenominatorLimit
      controlDenominatorLimit : Real)
    (htreatedNumerator :
      Tendsto treatedNumerator l
        (nhds (treatedTarget * treatedDenominatorLimit)))
    (htreatedDenominator :
      Tendsto treatedDenominator l (nhds treatedDenominatorLimit))
    (hcontrolNumerator :
      Tendsto controlNumerator l
        (nhds (controlTarget * controlDenominatorLimit)))
    (hcontrolDenominator :
      Tendsto controlDenominator l (nhds controlDenominatorLimit))
    (htreatedDenominatorLimit : treatedDenominatorLimit ≠ 0)
    (hcontrolDenominatorLimit : controlDenominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        treatedNumerator index / treatedDenominator index -
          controlNumerator index / controlDenominator index -
            (treatedTarget - controlTarget))
      l (nhds 0) := by
  have hcontrast :=
    tendsto_ratio_contrast_of_tendsto treatedNumerator treatedDenominator
      controlNumerator controlDenominator treatedTarget controlTarget
      treatedDenominatorLimit controlDenominatorLimit htreatedNumerator
      htreatedDenominator hcontrolNumerator hcontrolDenominator
      htreatedDenominatorLimit hcontrolDenominatorLimit
  have htarget :
      Tendsto (fun _index : Index => treatedTarget - controlTarget) l
        (nhds (treatedTarget - controlTarget)) :=
    tendsto_const_nhds
  have hzero :
      (treatedTarget - controlTarget) -
          (treatedTarget - controlTarget) = 0 := by
    ring
  simpa [hzero] using hcontrast.sub htarget

end WDSM
end Matching
end StatInference
