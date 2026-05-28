import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.BootstrapOneHotDrawMomentBridge
import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Fintype.Pi
import Mathlib.Data.Fintype.Prod
import Mathlib.Topology.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

/-!
# Uniform finite resampling law

This module gives a concrete finite probability model for the multinomial
bootstrap law used by the WDSM linearized bootstrap.  A bootstrap outcome is a
function from draw slots to sample units; the support is the full finite
function space, with uniform mass.  The one-hot draw indicator records whether
a given draw slot selected a given sample unit.

The proved moments are the elementary equal-probability iid one-hot moments
consumed by `BootstrapOneHotDrawMomentBridge`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Unit Draw Index : Type*}

/-- Full finite support for iid resampling assignments. -/
noncomputable def uniformAssignmentSupport
    (Unit Draw : Type*) [Fintype Unit] [Fintype Draw] [DecidableEq Draw] :
    Finset (Draw -> Unit) :=
  Finset.univ

/-- Uniform mass on finite resampling assignments. -/
noncomputable def uniformAssignmentMass
    (Unit Draw : Type*) [Fintype Unit] [Fintype Draw] [DecidableEq Draw] :
    (Draw -> Unit) -> Real :=
  fun _assignment => 1 / (Fintype.card (Draw -> Unit) : Real)

/-- One-hot indicator for a draw slot selecting a sample unit. -/
def oneHotAssignmentIndicator [DecidableEq Unit]
    (assignment : Draw -> Unit) (draw : Draw) (unit : Unit) : Real :=
  if assignment draw = unit then 1 else 0

/-- One-hot draw indicators are bounded by one in absolute value. -/
theorem abs_oneHotAssignmentIndicator_le_one [DecidableEq Unit]
    (assignment : Draw -> Unit) (draw : Draw) (unit : Unit) :
    |oneHotAssignmentIndicator assignment draw unit| ≤ 1 := by
  unfold oneHotAssignmentIndicator
  split_ifs <;> norm_num

/--
Array-indexed version of the one-hot absolute bound, packaged in the eventual
form consumed by bootstrap draw-count error routes.
-/
theorem eventually_abs_oneHotAssignmentIndicator_le_one
    [DecidableEq Unit] {l : Filter Index}
    (sample : Index -> Finset Unit) (draws : Index -> Finset Draw)
    (assignment : Index -> Draw -> Unit) :
    ∀ᶠ index in l,
      ∀ unit, unit ∈ sample index ->
        ∀ draw, draw ∈ draws index ->
          |oneHotAssignmentIndicator (assignment index) draw unit| ≤ 1 := by
  filter_upwards [] with index unit _hunit draw _hdraw
  exact abs_oneHotAssignmentIndicator_le_one (assignment index) draw unit

/--
Split a full assignment into the selected value at one draw slot and the
remaining coordinates.
-/
noncomputable def assignmentSplitOneEquiv [DecidableEq Draw]
    (draw : Draw) :
    (Draw -> Unit) ≃
      Unit × ({other : Draw // other ≠ draw} -> Unit) where
  toFun assignment := (assignment draw, fun other => assignment other.1)
  invFun pair := fun d =>
    if h : d = draw then pair.1 else pair.2 ⟨d, h⟩
  left_inv assignment := by
    funext d
    by_cases h : d = draw
    · subst d
      simp
    · simp [h]
  right_inv pair := by
    rcases pair with ⟨chosen, rest⟩
    simp
    funext other
    have hne : (other : Draw) ≠ draw := other.property
    simp [hne]

/--
Assignments with one fixed draw-slot value are equivalent to assignments of
the remaining coordinates.
-/
noncomputable def assignmentFiberOneEquiv [DecidableEq Draw]
    (draw : Draw) (unit : Unit) :
    {assignment : Draw -> Unit // assignment draw = unit} ≃
      ({other : Draw // other ≠ draw} -> Unit) where
  toFun assignment := fun other => assignment.1 other.1
  invFun rest :=
    ⟨fun d => if h : d = draw then unit else rest ⟨d, h⟩, by simp⟩
  left_inv assignment := by
    ext d
    by_cases h : d = draw
    · subst d
      simp [assignment.2]
    · simp [h]
  right_inv rest := by
    funext other
    have hne : (other : Draw) ≠ draw := other.property
    simp [hne]

/--
Split a full assignment into selected values at two distinct draw slots and
the remaining coordinates.
-/
noncomputable def assignmentSplitTwoEquiv [DecidableEq Draw]
    (drawA drawB : Draw) (hne : drawA ≠ drawB) :
    (Draw -> Unit) ≃
      (Unit × Unit) ×
        ({other : Draw // other ≠ drawA ∧ other ≠ drawB} -> Unit) where
  toFun assignment :=
    ((assignment drawA, assignment drawB), fun other => assignment other.1)
  invFun pair := fun d =>
    if hA : d = drawA then pair.1.1
    else if hB : d = drawB then pair.1.2
    else pair.2 ⟨d, hA, hB⟩
  left_inv assignment := by
    funext d
    by_cases hA : d = drawA
    · subst d
      simp
    · by_cases hB : d = drawB
      · subst d
        simp [hA]
      · simp [hA, hB]
  right_inv pair := by
    rcases pair with ⟨⟨chosenA, chosenB⟩, rest⟩
    simp
    constructor
    · intro hBA
      exact False.elim (hne hBA.symm)
    · funext other
      have hA : (other : Draw) ≠ drawA := other.property.1
      have hB : (other : Draw) ≠ drawB := other.property.2
      simp [hA, hB]

/--
Assignments with two fixed distinct draw-slot values are equivalent to
assignments of the remaining coordinates.
-/
noncomputable def assignmentFiberTwoEquiv [DecidableEq Draw]
    (drawA drawB : Draw) (hne : drawA ≠ drawB)
    (left right : Unit) :
    {assignment : Draw -> Unit //
      assignment drawA = left ∧ assignment drawB = right} ≃
      ({other : Draw // other ≠ drawA ∧ other ≠ drawB} -> Unit) where
  toFun assignment := fun other => assignment.1 other.1
  invFun rest :=
    ⟨fun d =>
      if hA : d = drawA then left
      else if hB : d = drawB then right
      else rest ⟨d, hA, hB⟩,
      by
        constructor
        · simp
        · have hBA : drawB ≠ drawA := fun h => hne h.symm
          simp [hBA]⟩
  left_inv assignment := by
    ext d
    by_cases hA : d = drawA
    · subst d
      simp [assignment.2.1]
    · by_cases hB : d = drawB
      · subst d
        simp [hA, assignment.2.2]
      · simp [hA, hB]
  right_inv rest := by
    funext other
    have hA : (other : Draw) ≠ drawA := other.property.1
    have hB : (other : Draw) ≠ drawB := other.property.2
    simp [hA, hB]

/-- The uniform assignment law has total mass one. -/
theorem finiteExpectation_uniformAssignmentMass_const_one
    [Fintype Unit] [Fintype Draw] [DecidableEq Draw] [Nonempty Unit] :
    finiteExpectation
        (uniformAssignmentSupport Unit Draw)
        (uniformAssignmentMass Unit Draw)
        (fun _assignment => (1 : Real)) = 1 := by
  have hcard_ne_nat : Fintype.card (Draw -> Unit) ≠ 0 :=
    Fintype.card_ne_zero
  have hcard_ne : (Fintype.card (Draw -> Unit) : Real) ≠ 0 := by
    exact_mod_cast hcard_ne_nat
  unfold finiteExpectation uniformAssignmentSupport uniformAssignmentMass
  simp [Finset.sum_const, nsmul_eq_mul]

/-- Cardinal identity for one fixed draw-slot fiber. -/
theorem assignment_card_eq_card_unit_mul_fiber_one
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    (draw : Draw) (unit : Unit) :
    Fintype.card (Draw -> Unit) =
      Fintype.card Unit *
        Fintype.card {assignment : Draw -> Unit // assignment draw = unit} := by
  have hsplit :
      Fintype.card (Draw -> Unit) =
        Fintype.card
          (Unit × ({other : Draw // other ≠ draw} -> Unit)) := by
    exact Fintype.card_congr (assignmentSplitOneEquiv (Unit := Unit) draw)
  have hfiber :
      Fintype.card {assignment : Draw -> Unit // assignment draw = unit} =
        Fintype.card ({other : Draw // other ≠ draw} -> Unit) := by
    exact Fintype.card_congr
      (assignmentFiberOneEquiv (Unit := Unit) draw unit)
  rw [hsplit, hfiber]
  simp

/-- Sum of one-hot indicators over all assignments equals the fiber cardinal. -/
theorem sum_oneHotAssignmentIndicator_eq_fiber_card
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    (draw : Draw) (unit : Unit) :
    (∑ assignment : Draw -> Unit,
      oneHotAssignmentIndicator assignment draw unit) =
      (Fintype.card
        {assignment : Draw -> Unit // assignment draw = unit} : Real) := by
  unfold oneHotAssignmentIndicator
  simp [Fintype.card_subtype]

/-- A single draw slot is uniformly distributed over sample units. -/
theorem finiteExpectation_oneHotAssignmentIndicator_eq_inv_card
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit]
    (draw : Draw) (unit : Unit) :
    finiteExpectation
        (uniformAssignmentSupport Unit Draw)
        (uniformAssignmentMass Unit Draw)
        (fun assignment => oneHotAssignmentIndicator assignment draw unit) =
      1 / (Fintype.card Unit : Real) := by
  have htotal_nat :=
    assignment_card_eq_card_unit_mul_fiber_one
      (Unit := Unit) (Draw := Draw) draw unit
  have htotal :
      (Fintype.card (Draw -> Unit) : Real) =
        (Fintype.card Unit : Real) *
          (Fintype.card
            {assignment : Draw -> Unit // assignment draw = unit} : Real) := by
    exact_mod_cast htotal_nat
  have hunit_ne_nat : Fintype.card Unit ≠ 0 := Fintype.card_ne_zero
  have hunit_ne : (Fintype.card Unit : Real) ≠ 0 := by
    exact_mod_cast hunit_ne_nat
  have hfiber_ne_nat :
      Fintype.card
        {assignment : Draw -> Unit // assignment draw = unit} ≠ 0 := by
    have hfiber_nonempty :
        Nonempty {assignment : Draw -> Unit // assignment draw = unit} :=
      ⟨⟨fun _draw => unit, rfl⟩⟩
    exact Fintype.card_ne_zero
  have hfiber_ne :
      (Fintype.card
        {assignment : Draw -> Unit // assignment draw = unit} : Real) ≠ 0 := by
    exact_mod_cast hfiber_ne_nat
  calc
    finiteExpectation
        (uniformAssignmentSupport Unit Draw)
        (uniformAssignmentMass Unit Draw)
        (fun assignment => oneHotAssignmentIndicator assignment draw unit) =
        (1 / (Fintype.card (Draw -> Unit) : Real)) *
          (∑ assignment : Draw -> Unit,
            oneHotAssignmentIndicator assignment draw unit) := by
          unfold finiteExpectation uniformAssignmentSupport uniformAssignmentMass
          rw [← Finset.mul_sum]
    _ =
        (1 / (Fintype.card (Draw -> Unit) : Real)) *
          (Fintype.card
            {assignment : Draw -> Unit // assignment draw = unit} : Real) := by
          rw [sum_oneHotAssignmentIndicator_eq_fiber_card]
    _ = 1 / (Fintype.card Unit : Real) := by
          rw [htotal]
          field_simp [hunit_ne, hfiber_ne]

/-- Same-draw one-hot cross moment under the uniform assignment law. -/
theorem finiteExpectation_oneHotAssignmentIndicator_same_draw_mul_eq
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit]
    (draw : Draw) (left right : Unit) :
    finiteExpectation
        (uniformAssignmentSupport Unit Draw)
        (uniformAssignmentMass Unit Draw)
        (fun assignment =>
          oneHotAssignmentIndicator assignment draw left *
            oneHotAssignmentIndicator assignment draw right) =
      if left = right then 1 / (Fintype.card Unit : Real) else 0 := by
  by_cases h : left = right
  · subst right
    calc
      finiteExpectation
          (uniformAssignmentSupport Unit Draw)
          (uniformAssignmentMass Unit Draw)
          (fun assignment =>
            oneHotAssignmentIndicator assignment draw left *
              oneHotAssignmentIndicator assignment draw left) =
          finiteExpectation
            (uniformAssignmentSupport Unit Draw)
            (uniformAssignmentMass Unit Draw)
            (fun assignment => oneHotAssignmentIndicator assignment draw left) := by
            exact finiteExpectation_congr _ _ _ _
              (fun assignment _hassignment => by
                unfold oneHotAssignmentIndicator
                by_cases hselect : assignment draw = left <;> simp [hselect])
      _ = 1 / (Fintype.card Unit : Real) := by
            exact finiteExpectation_oneHotAssignmentIndicator_eq_inv_card
              (Unit := Unit) (Draw := Draw) draw left
      _ = (if left = left then 1 / (Fintype.card Unit : Real) else 0) := by
            simp
  · calc
      finiteExpectation
          (uniformAssignmentSupport Unit Draw)
          (uniformAssignmentMass Unit Draw)
          (fun assignment =>
            oneHotAssignmentIndicator assignment draw left *
              oneHotAssignmentIndicator assignment draw right) =
          finiteExpectation
            (uniformAssignmentSupport Unit Draw)
            (uniformAssignmentMass Unit Draw)
            (fun _assignment => (0 : Real)) := by
            exact finiteExpectation_congr _ _ _ _
              (fun assignment _hassignment => by
                unfold oneHotAssignmentIndicator
                by_cases hleft : assignment draw = left
                · have hright : assignment draw ≠ right := by
                    intro hright
                    exact h (hleft.symm.trans hright)
                  simp [hleft, h]
                · simp [hleft])
      _ = 0 := by
            unfold finiteExpectation uniformAssignmentSupport uniformAssignmentMass
            simp
      _ = (if left = right then 1 / (Fintype.card Unit : Real) else 0) := by
            simp [h]

/-- Cardinal identity for two fixed distinct draw-slot fibers. -/
theorem assignment_card_eq_card_unit_sq_mul_fiber_two
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    (drawA drawB : Draw) (hne : drawA ≠ drawB)
    (left right : Unit) :
    Fintype.card (Draw -> Unit) =
      Fintype.card Unit * Fintype.card Unit *
        Fintype.card
          {assignment : Draw -> Unit //
            assignment drawA = left ∧ assignment drawB = right} := by
  have hsplit :
      Fintype.card (Draw -> Unit) =
        Fintype.card
          ((Unit × Unit) ×
            ({other : Draw // other ≠ drawA ∧ other ≠ drawB} -> Unit)) := by
    exact Fintype.card_congr
      (assignmentSplitTwoEquiv (Unit := Unit) drawA drawB hne)
  have hfiber :
      Fintype.card
          {assignment : Draw -> Unit //
            assignment drawA = left ∧ assignment drawB = right} =
        Fintype.card
          ({other : Draw // other ≠ drawA ∧ other ≠ drawB} -> Unit) := by
    exact Fintype.card_congr
      (assignmentFiberTwoEquiv (Unit := Unit) drawA drawB hne left right)
  rw [hsplit, hfiber]
  simp [Nat.mul_assoc]

/--
Sum of two distinct-draw one-hot products over all assignments equals the
joint fiber cardinal.
-/
theorem sum_oneHotAssignmentIndicator_distinct_mul_eq_fiber_card
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    (drawA drawB : Draw) (left right : Unit) :
    (∑ assignment : Draw -> Unit,
      oneHotAssignmentIndicator assignment drawA left *
        oneHotAssignmentIndicator assignment drawB right) =
      (Fintype.card
        {assignment : Draw -> Unit //
          assignment drawA = left ∧ assignment drawB = right} : Real) := by
  have hpointwise :
      ∀ assignment : Draw -> Unit,
        oneHotAssignmentIndicator assignment drawA left *
          oneHotAssignmentIndicator assignment drawB right =
        if assignment drawA = left ∧ assignment drawB = right then
          (1 : Real)
        else
          0 := by
    intro assignment
    unfold oneHotAssignmentIndicator
    by_cases hA : assignment drawA = left
    · by_cases hB : assignment drawB = right
      · simp [hA, hB]
      · simp [hA, hB]
    · simp [hA]
  calc
    (∑ assignment : Draw -> Unit,
      oneHotAssignmentIndicator assignment drawA left *
        oneHotAssignmentIndicator assignment drawB right) =
        ∑ assignment : Draw -> Unit,
          if assignment drawA = left ∧ assignment drawB = right then
            (1 : Real)
          else
            0 := by
          exact Finset.sum_congr rfl
            (fun assignment _hassignment => hpointwise assignment)
    _ =
      (Fintype.card
        {assignment : Draw -> Unit //
          assignment drawA = left ∧ assignment drawB = right} : Real) := by
        simp [Fintype.card_subtype]

/-- Distinct draw slots have product one-hot moment `1 / n^2`. -/
theorem finiteExpectation_oneHotAssignmentIndicator_distinct_draw_mul_eq
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit]
    (drawA drawB : Draw) (hne : drawA ≠ drawB)
    (left right : Unit) :
    finiteExpectation
        (uniformAssignmentSupport Unit Draw)
        (uniformAssignmentMass Unit Draw)
        (fun assignment =>
          oneHotAssignmentIndicator assignment drawA left *
            oneHotAssignmentIndicator assignment drawB right) =
      1 / (Fintype.card Unit : Real) ^ 2 := by
  have htotal_nat :=
    assignment_card_eq_card_unit_sq_mul_fiber_two
      (Unit := Unit) (Draw := Draw) drawA drawB hne left right
  have htotal :
      (Fintype.card (Draw -> Unit) : Real) =
        (Fintype.card Unit : Real) * (Fintype.card Unit : Real) *
          (Fintype.card
            {assignment : Draw -> Unit //
              assignment drawA = left ∧ assignment drawB = right} : Real) := by
    exact_mod_cast htotal_nat
  have hunit_ne_nat : Fintype.card Unit ≠ 0 := Fintype.card_ne_zero
  have hunit_ne : (Fintype.card Unit : Real) ≠ 0 := by
    exact_mod_cast hunit_ne_nat
  have hfiber_ne_nat :
      Fintype.card
        {assignment : Draw -> Unit //
          assignment drawA = left ∧ assignment drawB = right} ≠ 0 := by
    let fixedAssignment : Draw -> Unit :=
      fun draw => if draw = drawA then left else right
    have hA : fixedAssignment drawA = left := by
      simp [fixedAssignment]
    have hB : fixedAssignment drawB = right := by
      have hBA : drawB ≠ drawA := fun h => hne h.symm
      simp [fixedAssignment, hBA]
    have hfiber_nonempty :
        Nonempty
          {assignment : Draw -> Unit //
            assignment drawA = left ∧ assignment drawB = right} :=
      ⟨⟨fixedAssignment, hA, hB⟩⟩
    exact Fintype.card_ne_zero
  have hfiber_ne :
      (Fintype.card
        {assignment : Draw -> Unit //
          assignment drawA = left ∧ assignment drawB = right} : Real) ≠ 0 := by
    exact_mod_cast hfiber_ne_nat
  calc
    finiteExpectation
        (uniformAssignmentSupport Unit Draw)
        (uniformAssignmentMass Unit Draw)
        (fun assignment =>
          oneHotAssignmentIndicator assignment drawA left *
            oneHotAssignmentIndicator assignment drawB right) =
        (1 / (Fintype.card (Draw -> Unit) : Real)) *
          (∑ assignment : Draw -> Unit,
            oneHotAssignmentIndicator assignment drawA left *
              oneHotAssignmentIndicator assignment drawB right) := by
          unfold finiteExpectation uniformAssignmentSupport uniformAssignmentMass
          rw [← Finset.mul_sum]
    _ =
        (1 / (Fintype.card (Draw -> Unit) : Real)) *
          (Fintype.card
            {assignment : Draw -> Unit //
              assignment drawA = left ∧ assignment drawB = right} : Real) := by
          rw [sum_oneHotAssignmentIndicator_distinct_mul_eq_fiber_card]
    _ = 1 / (Fintype.card Unit : Real) ^ 2 := by
          rw [htotal]
          field_simp [hunit_ne, hfiber_ne]

/--
Concrete uniform-assignment law supplies the iid one-hot moments used by
`BootstrapOneHotDrawMomentBridge`.
-/
theorem uniformAssignment_oneHot_draw_moments
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit]
    (sampleSize : Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize) :
    (finiteExpectation
        (uniformAssignmentSupport Unit Draw)
        (uniformAssignmentMass Unit Draw)
        (fun _assignment => (1 : Real)) = 1) ∧
      (∀ draw ∈ (Finset.univ : Finset Draw),
        ∀ unit ∈ (Finset.univ : Finset Unit),
          finiteExpectation
            (uniformAssignmentSupport Unit Draw)
            (uniformAssignmentMass Unit Draw)
            (fun assignment =>
              oneHotAssignmentIndicator assignment draw unit) =
            1 / sampleSize) ∧
      (∀ draw ∈ (Finset.univ : Finset Draw),
        ∀ left ∈ (Finset.univ : Finset Unit),
        ∀ right ∈ (Finset.univ : Finset Unit),
          finiteExpectation
            (uniformAssignmentSupport Unit Draw)
            (uniformAssignmentMass Unit Draw)
            (fun assignment =>
              oneHotAssignmentIndicator assignment draw left *
                oneHotAssignmentIndicator assignment draw right) =
            if left = right then 1 / sampleSize else 0) ∧
      (∀ drawA ∈ (Finset.univ : Finset Draw),
        ∀ drawB ∈ (Finset.univ : Finset Draw), drawA ≠ drawB ->
        ∀ left ∈ (Finset.univ : Finset Unit),
        ∀ right ∈ (Finset.univ : Finset Unit),
          finiteExpectation
            (uniformAssignmentSupport Unit Draw)
            (uniformAssignmentMass Unit Draw)
            (fun assignment =>
              oneHotAssignmentIndicator assignment drawA left *
                oneHotAssignmentIndicator assignment drawB right) =
            1 / sampleSize ^ 2) := by
  constructor
  · exact finiteExpectation_uniformAssignmentMass_const_one
      (Unit := Unit) (Draw := Draw)
  constructor
  · intro draw _hdraw unit _hunit
    rw [← hunit_card]
    exact finiteExpectation_oneHotAssignmentIndicator_eq_inv_card
      (Unit := Unit) (Draw := Draw) draw unit
  constructor
  · intro draw _hdraw left _hleft right _hright
    rw [← hunit_card]
    exact finiteExpectation_oneHotAssignmentIndicator_same_draw_mul_eq
      (Unit := Unit) (Draw := Draw) draw left right
  · intro drawA _hdrawA drawB _hdrawB hne left _hleft right _hright
    rw [← hunit_card]
    exact finiteExpectation_oneHotAssignmentIndicator_distinct_draw_mul_eq
      (Unit := Unit) (Draw := Draw) drawA drawB hne left right

/--
Concrete uniform-assignment multinomial raw count moments.  This exposes the
paper-facing bootstrap facts `E[m_i] = 1` and
`E[m_i m_j] = 2 - 1 / n` on the diagonal, `1 - 1 / n` off the diagonal.
-/
theorem uniformAssignment_multinomialCount_raw_count_moments
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit]
    (sampleSize : Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0) :
    (∀ unit ∈ (Finset.univ : Finset Unit),
        finiteExpectation
          (uniformAssignmentSupport Unit Draw)
          (uniformAssignmentMass Unit Draw)
          (fun assignment =>
            multinomialCountFromDrawIndicators
              (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              assignment unit) =
          1) ∧
      (∀ left ∈ (Finset.univ : Finset Unit),
        ∀ right ∈ (Finset.univ : Finset Unit),
        finiteExpectation
          (uniformAssignmentSupport Unit Draw)
          (uniformAssignmentMass Unit Draw)
          (fun assignment =>
            multinomialCountFromDrawIndicators
              (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              assignment left *
            multinomialCountFromDrawIndicators
              (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              assignment right) =
          if left = right then 2 - 1 / sampleSize
          else 1 - 1 / sampleSize) := by
  have hmoments :=
    uniformAssignment_oneHot_draw_moments
      (Unit := Unit) (Draw := Draw) sampleSize hunit_card
  have hdraws_card :
      ((Finset.univ : Finset Draw).card : Real) = sampleSize := by
    simpa using hdraw_card
  have hsums :=
    oneHot_draw_moment_sums_of_iid_equal_probability_moments
      (uniformAssignmentSupport Unit Draw)
      (uniformAssignmentMass Unit Draw)
      (Finset.univ : Finset Unit)
      (Finset.univ : Finset Draw)
      (fun assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      sampleSize hdraws_card hsampleSize_ne
      hmoments.2.1 hmoments.2.2.1 hmoments.2.2.2
  exact
    multinomialCountFromDrawIndicators_raw_count_moments_of_draw_moment_sums
      (uniformAssignmentSupport Unit Draw)
      (uniformAssignmentMass Unit Draw)
      (Finset.univ : Finset Unit)
      (Finset.univ : Finset Draw)
      (fun assignment draw unit =>
        oneHotAssignmentIndicator assignment draw unit)
      sampleSize hsums.1 hsums.2

/--
Uniform-assignment normalized multinomial bootstrap variance target derived
from the concrete raw-count moments `E[m_i]` and `E[m_i m_j]`.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_uniformAssignment_raw_count_moments_base_ratio
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit]
    (contribution weight : Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase :
      baseLinearizedSum (Finset.univ : Finset Unit) contribution =
        target * baseLinearizedSum (Finset.univ : Finset Unit) weight) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment
          (uniformAssignmentSupport Unit Draw)
          (uniformAssignmentMass Unit Draw)
          (Finset.univ : Finset Unit)
          (fun assignment unit =>
            multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              assignment unit)
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget (Finset.univ : Finset Unit)
        contribution weight target denominator normalizer := by
  have hraw :=
    uniformAssignment_multinomialCount_raw_count_moments
      (Unit := Unit) (Draw := Draw) sampleSize hunit_card hdraw_card
      hsampleSize_ne
  exact
    multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_count_moments_of_base_ratio
      (uniformAssignmentSupport Unit Draw)
      (uniformAssignmentMass Unit Draw)
      (Finset.univ : Finset Unit)
      (fun assignment unit =>
        multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
          (fun assignment draw unit =>
            oneHotAssignmentIndicator assignment draw unit)
          assignment unit)
      contribution weight target denominator normalizer sampleSize
      (finiteExpectation_uniformAssignmentMass_const_one
        (Unit := Unit) (Draw := Draw))
      hraw.1 hraw.2 hbase

/--
Uniform-assignment version of the normalized multinomial bootstrap variance
target.  The cardinal equality records the main-paper bootstrap convention:
the number of draw slots equals the number of sample units.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_uniformAssignment_base_ratio
    [Fintype Unit] [Fintype Draw] [DecidableEq Unit] [DecidableEq Draw]
    [Nonempty Unit]
    (contribution weight : Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (hunit_card : (Fintype.card Unit : Real) = sampleSize)
    (hdraw_card : (Fintype.card Draw : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hbase :
      baseLinearizedSum (Finset.univ : Finset Unit) contribution =
        target * baseLinearizedSum (Finset.univ : Finset Unit) weight) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment
          (uniformAssignmentSupport Unit Draw)
          (uniformAssignmentMass Unit Draw)
          (Finset.univ : Finset Unit)
          (fun assignment unit =>
            multinomialCountFromDrawIndicators (Finset.univ : Finset Draw)
              (fun assignment draw unit =>
                oneHotAssignmentIndicator assignment draw unit)
              assignment unit)
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget (Finset.univ : Finset Unit)
        contribution weight target denominator normalizer := by
  exact
    multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_uniformAssignment_raw_count_moments_base_ratio
      (Unit := Unit) (Draw := Draw) contribution weight target denominator
      normalizer sampleSize hunit_card hdraw_card hsampleSize_ne hbase

end WDSM
end Matching
end StatInference
