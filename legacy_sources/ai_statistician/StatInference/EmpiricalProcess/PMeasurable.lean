import Mathlib.MeasureTheory.Constructions.BorelSpace.Order
import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.MeasureTheory.Group.Arithmetic
import Mathlib.MeasureTheory.Integral.DominatedConvergence
import Mathlib.MeasureTheory.Measure.NullMeasurable
import Mathlib.Probability.HasLawExists
import Mathlib.Probability.ProductMeasure
import Mathlib.Topology.Order.OrderClosed
import Mathlib.GroupTheory.Perm.Fin
import Mathlib.Logic.Equiv.Fintype
import StatInference.EmpiricalProcess.CoveringPrimitive
import StatInference.EmpiricalProcess.OuterProbabilityExpectation

/-!
# `P`-measurable classes

This module records the VdV&W Definition 2.3.3 measurability primitive.

The textbook definition asks that, for every finite sample size `n` and every
weight vector `e : Fin n -> ℝ`, the sample map

`x ↦ ⨆ f ∈ F |∑ i, e i * f (x i)|`

is measurable on the completion of the finite product probability space.  In
mathlib this completion-measurability condition is expressed as
`NullMeasurable` with respect to the product measure.
-/

namespace StatInference

open MeasureTheory Filter ProbabilityTheory
open scoped BigOperators Topology NNReal

universe u v

/-- Finite product measure `P^n` on `n` sample coordinates. -/
noncomputable def vdVWProductMeasure {Observation : Type u}
    [MeasurableSpace Observation] (P : Measure Observation) (n : ℕ) :
    Measure (Fin n -> Observation) :=
  Measure.pi fun _ : Fin n => P

instance instIsProbabilityMeasure_vdVWProductMeasure
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] (n : ℕ) :
    IsProbabilityMeasure (vdVWProductMeasure P n) := by
  unfold vdVWProductMeasure
  infer_instance

/-- Infinite iid product measure `P^∞` on sample sequences. -/
noncomputable def vdVWInfiniteProductMeasure {Observation : Type u}
    [MeasurableSpace Observation] (P : Measure Observation) :
    Measure (ℕ -> Observation) :=
  Measure.infinitePi fun _ : ℕ => P

instance instIsProbabilityMeasure_vdVWInfiniteProductMeasure
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] :
    IsProbabilityMeasure (vdVWInfiniteProductMeasure P) := by
  unfold vdVWInfiniteProductMeasure
  infer_instance

/--
Each coordinate projection of the canonical infinite iid product sample space
has law `P`.
-/
theorem vdVWInfiniteProductMeasure_coordinate_hasLaw
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] (i : ℕ) :
    HasLaw (fun sequence : ℕ -> Observation => sequence i)
      P (vdVWInfiniteProductMeasure P) := by
  simpa [vdVWInfiniteProductMeasure] using
    (measurePreserving_eval_infinitePi
      (fun _ : ℕ => P) i).hasLaw

/--
The coordinate projections of the canonical infinite iid product sample space
are mutually independent.

This is the direct iid bridge needed by finite-class strong-law routes.
-/
theorem vdVWInfiniteProductMeasure_iIndepFun_coordinates
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] :
    iIndepFun (fun i : ℕ => fun sequence : ℕ -> Observation => sequence i)
      (vdVWInfiniteProductMeasure P) := by
  rw [iIndepFun_iff_map_fun_eq_infinitePi_map (by fun_prop)]
  change Measure.map id (vdVWInfiniteProductMeasure P) =
    Measure.infinitePi
      (fun i : ℕ =>
        Measure.map (fun sequence : ℕ -> Observation => sequence i)
          (vdVWInfiniteProductMeasure P))
  rw [Measure.map_id]
  unfold vdVWInfiniteProductMeasure
  congr
  funext i
  exact
    ((measurePreserving_eval_infinitePi
      (fun _ : ℕ => P) i).map_eq).symm

/--
Finite-coordinate permutation of the sample space `Observation^n`.

This is the finite-sample permutation action used by the VdV&W
permutation-symmetric filtration route.
-/
noncomputable def vdVWFinCoordinatePermMeasurableEquiv
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    (perm : Equiv.Perm (Fin n)) :
    (Fin n -> Observation) ≃ᵐ (Fin n -> Observation) :=
  MeasurableEquiv.piCongrLeft (fun _ : Fin n => Observation) perm

/-- Coordinate display for `vdVWFinCoordinatePermMeasurableEquiv`. -/
theorem vdVWFinCoordinatePermMeasurableEquiv_apply_apply
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    (perm : Equiv.Perm (Fin n)) (sample : Fin n -> Observation) (i : Fin n) :
    vdVWFinCoordinatePermMeasurableEquiv perm sample (perm i) = sample i :=
  by
    simpa [vdVWFinCoordinatePermMeasurableEquiv] using
      (MeasurableEquiv.piCongrLeft_apply_apply
        (β := fun _ : Fin n => Observation) perm sample i)

/--
The finite permutation that identifies the sample with coordinate `omitted`
removed with the sample with the last coordinate removed.

It sends the complement of `omitted` to the complement of `Fin.last n` while
preserving the induced `Fin n` order.  This is the deterministic transport
needed for the leave-one-out conditional-symmetry step in VdV&W Lemma 2.4.5.
-/
noncomputable def vdVWLeaveOneOutToLastPerm {n : ℕ}
    (omitted : Fin (n + 1)) : Equiv.Perm (Fin (n + 1)) :=
  omitted.cycleRange.trans (Fin.last n).cycleRange.symm

/-- The leave-one-out transport sends `omitted.succAbove j` to the last-complement coordinate. -/
theorem vdVWLeaveOneOutToLastPerm_apply_succAbove {n : ℕ}
    (omitted : Fin (n + 1)) (j : Fin n) :
    vdVWLeaveOneOutToLastPerm omitted (omitted.succAbove j) =
      (Fin.last n).succAbove j := by
  change (Fin.last n).cycleRange.symm
      (omitted.cycleRange (omitted.succAbove j)) =
    (Fin.last n).succAbove j
  rw [Fin.cycleRange_succAbove, Fin.cycleRange_symm_succ]

/-- Inverse form of `vdVWLeaveOneOutToLastPerm_apply_succAbove`. -/
theorem vdVWLeaveOneOutToLastPerm_symm_apply_last_succAbove {n : ℕ}
    (omitted : Fin (n + 1)) (j : Fin n) :
    (vdVWLeaveOneOutToLastPerm omitted).symm ((Fin.last n).succAbove j) =
      omitted.succAbove j := by
  apply (vdVWLeaveOneOutToLastPerm omitted).injective
  rw [Equiv.apply_symm_apply]
  exact (vdVWLeaveOneOutToLastPerm_apply_succAbove omitted j).symm

/--
Finite-coordinate leave-one-out transport: after applying the canonical
permutation, removing the last coordinate gives the same `n`-sample as removing
the chosen coordinate from the original sample.
-/
theorem removeNth_last_vdVWFinCoordinatePerm_leaveOneOutToLastPerm
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    (omitted : Fin (n + 1)) (sample : Fin (n + 1) -> Observation) :
    (Fin.last n).removeNth
        (vdVWFinCoordinatePermMeasurableEquiv
          (vdVWLeaveOneOutToLastPerm omitted) sample) =
      omitted.removeNth sample := by
  ext j
  have hcoord :=
    vdVWFinCoordinatePermMeasurableEquiv_apply_apply
      (Observation := Observation) (vdVWLeaveOneOutToLastPerm omitted) sample
      ((vdVWLeaveOneOutToLastPerm omitted).symm ((Fin.last n).succAbove j))
  rw [vdVWLeaveOneOutToLastPerm_symm_apply_last_succAbove omitted j] at hcoord
  rw [vdVWLeaveOneOutToLastPerm_apply_succAbove omitted j] at hcoord
  change
    vdVWFinCoordinatePermMeasurableEquiv
        (vdVWLeaveOneOutToLastPerm omitted) sample
        ((Fin.last n).succAbove j) =
      sample (omitted.succAbove j)
  exact hcoord

/--
The iid finite product measure `P^n` is invariant under finite-coordinate
permutations.
-/
theorem vdVWProductMeasure_measurePreserving_finCoordinatePerm
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [SigmaFinite P] {n : ℕ}
    (perm : Equiv.Perm (Fin n)) :
    MeasurePreserving (vdVWFinCoordinatePermMeasurableEquiv perm)
      (vdVWProductMeasure P n) (vdVWProductMeasure P n) := by
  simpa [vdVWProductMeasure, vdVWFinCoordinatePermMeasurableEquiv] using
    (MeasureTheory.measurePreserving_piCongrLeft
      (α := fun _ : Fin n => Observation)
      (μ := fun _ : Fin n => P) perm)

/-- Integral invariance under finite-coordinate permutations of `P^n`. -/
theorem integral_vdVWProductMeasure_comp_finCoordinatePerm
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [SigmaFinite P] {n : ℕ}
    (perm : Equiv.Perm (Fin n))
    (g : (Fin n -> Observation) -> ℝ) :
    (∫ sample : Fin n -> Observation,
        g (vdVWFinCoordinatePermMeasurableEquiv perm sample)
          ∂(vdVWProductMeasure P n)) =
      ∫ sample : Fin n -> Observation, g sample ∂(vdVWProductMeasure P n) :=
  (vdVWProductMeasure_measurePreserving_finCoordinatePerm P perm).integral_comp' g

/-- The first `n` coordinates of an infinite sample sequence. -/
def vdVWFirstNSample {Observation : Type u} (n : ℕ)
    (sequence : ℕ -> Observation) : Fin n -> Observation :=
  fun i => sequence i

/-- The canonical equivalence between `Fin n` and the subtype `Finset.range n`. -/
def vdVWFinRangeEquiv (n : ℕ) : Fin n ≃ ↥(Finset.range n) where
  toFun i := ⟨i, Finset.mem_range.mpr i.isLt⟩
  invFun i := ⟨i, Finset.mem_range.mp i.property⟩
  left_inv i := by
    ext
    rfl
  right_inv i := by
    ext
    rfl

/-- The first-`n` coordinate projection is measurable for product sigma-fields. -/
theorem measurable_vdVWFirstNSample
    {Observation : Type u} [MeasurableSpace Observation] (n : ℕ) :
    Measurable (vdVWFirstNSample (Observation := Observation) n) := by
  rw [measurable_pi_iff]
  intro i
  exact measurable_pi_apply (i : ℕ)

/--
The first `n` coordinates of `P^∞` have law `P^n`.

This is the bridge from the infinite sequence space used by the VdV&W
permutation-symmetric reverse-submartingale route back to the finite product
estimates used throughout Theorem 2.4.3.
-/
theorem vdVWInfiniteProductMeasure_measurePreserving_firstNSample
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] (n : ℕ) :
    MeasurePreserving (vdVWFirstNSample (Observation := Observation) n)
      (vdVWInfiniteProductMeasure P) (vdVWProductMeasure P n) := by
  refine ⟨measurable_vdVWFirstNSample n, ?_⟩
  let I : Finset ℕ := Finset.range n
  let e : Fin n ≃ ↥I := vdVWFinRangeEquiv n
  let rangeToFin : (↥I -> Observation) -> (Fin n -> Observation) :=
    fun sample i => sample (e i)
  have hrangeToFin_measurable : Measurable rangeToFin := by
    rw [measurable_pi_iff]
    intro i
    exact measurable_pi_apply (e i)
  have hfirst :
      vdVWFirstNSample (Observation := Observation) n =
        rangeToFin ∘ I.restrict := by
    funext sequence i
    rfl
  have hmap_range :
      (Measure.infinitePi fun _ : ℕ => P).map I.restrict =
        Measure.pi fun _ : ↥I => P := by
    simpa [I] using
      (Measure.infinitePi_map_restrict (μ := fun _ : ℕ => P) (I := I))
  have hmap_reindex :
      (Measure.pi fun _ : ↥I => P).map rangeToFin =
        Measure.pi fun _ : Fin n => P := by
    simpa [rangeToFin, e, I] using
      (MeasureTheory.measurePreserving_piCongrLeft
        (α := fun _ : Fin n => Observation)
        (μ := fun _ : Fin n => P) (vdVWFinRangeEquiv n).symm).map_eq
  calc
    (vdVWInfiniteProductMeasure P).map
        (vdVWFirstNSample (Observation := Observation) n)
        = (Measure.infinitePi fun _ : ℕ => P).map (rangeToFin ∘ I.restrict) := by
            simp [vdVWInfiniteProductMeasure, hfirst]
    _ = ((Measure.infinitePi fun _ : ℕ => P).map I.restrict).map rangeToFin := by
          rw [← Measure.map_map hrangeToFin_measurable
            (Finset.measurable_restrict (X := fun _ : ℕ => Observation) I)]
    _ = vdVWProductMeasure P n := by
          rw [hmap_range, hmap_reindex]
          rfl

/-- The first `n` coordinates on `P^∞` have finite-product law `P^n`. -/
theorem vdVWFirstNSample_hasLaw_vdVWProductMeasure
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] (n : ℕ) :
    ProbabilityTheory.HasLaw
      (vdVWFirstNSample (Observation := Observation) n)
      (vdVWProductMeasure P n) (vdVWInfiniteProductMeasure P) :=
  (vdVWInfiniteProductMeasure_measurePreserving_firstNSample P n).hasLaw

/--
Measurable finite-sample events can be lifted from `P^n` to the canonical
infinite iid product space by precomposing with the first-`n` projection.

This is the event-probability counterpart of
`integral_vdVWInfiniteProductMeasure_firstNSample`.  It is intentionally stated
for measurable events; arbitrary outer events still need the one-sided outer
measure inequalities used elsewhere.
-/
theorem vdVWInfiniteProductMeasure_firstNSample_preimage_eq
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] (n : ℕ)
    {event : Set (Fin n -> Observation)} (hevent : MeasurableSet event) :
    (vdVWInfiniteProductMeasure P)
        ((vdVWFirstNSample (Observation := Observation) n) ⁻¹' event) =
      (vdVWProductMeasure P n) event := by
  let hmp := vdVWInfiniteProductMeasure_measurePreserving_firstNSample P n
  calc
    (vdVWInfiniteProductMeasure P)
        ((vdVWFirstNSample (Observation := Observation) n) ⁻¹' event)
        = Measure.map (vdVWFirstNSample (Observation := Observation) n)
            (vdVWInfiniteProductMeasure P) event := by
            rw [Measure.map_apply hmp.measurable hevent]
    _ = (vdVWProductMeasure P n) event := by
            rw [hmp.map_eq]

/--
Real-valued finite-sample tail events have the same probability after lifting
to the infinite iid product space through the first-`n` projection.

This is the common-space recoding form needed for fixed-domain convergence and
uniform-integrability arguments when the statistic is measurable.
-/
theorem vdVWInfiniteProductMeasure_firstNSample_real_tail_eq
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] (n : ℕ)
    {g : (Fin n -> Observation) -> ℝ} (hg : Measurable g)
    (ε c : ℝ) :
    (vdVWInfiniteProductMeasure P)
        {sequence : ℕ -> Observation |
          ε < dist (g (vdVWFirstNSample (Observation := Observation) n sequence)) c} =
      (vdVWProductMeasure P n)
        {sample : Fin n -> Observation | ε < dist (g sample) c} := by
  let event : Set (Fin n -> Observation) :=
    {sample : Fin n -> Observation | ε < dist (g sample) c}
  have hevent : MeasurableSet event := by
    simpa [event, Set.preimage, Set.mem_Ioi] using
      (hg.dist measurable_const) isOpen_Ioi.measurableSet
  simpa [event] using
    vdVWInfiniteProductMeasure_firstNSample_preimage_eq
      (P := P) (n := n) hevent

/--
Measurable finite-product convergence in VdV&W outer probability can be recoded
as common-domain convergence on the canonical infinite iid product space.

This is the convergence-level form of
`vdVWInfiniteProductMeasure_firstNSample_real_tail_eq`.  It is intentionally
restricted to measurable real statistics; arbitrary outer events still use the
one-sided outer-measure transfers.
-/
theorem VdVWConvergesInOuterProbability_firstNSample_real_of_const
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P]
    {g : (n : ℕ) -> (Fin n -> Observation) -> ℝ}
    (hg : ∀ n, Measurable (g n)) {c : ℝ}
    (hfinite :
      VdVWConvergesInOuterProbabilityConst
        (fun n : ℕ => Fin n -> Observation)
        (fun _ : ℕ => inferInstance)
        (fun n : ℕ => vdVWProductMeasure P n)
        g atTop c) :
    VdVWConvergesInOuterProbability (vdVWInfiniteProductMeasure P)
      (fun n sequence =>
        g n (vdVWFirstNSample (Observation := Observation) n sequence))
      atTop (fun _ => c) := by
  intro ε hε
  refine (hfinite ε hε).congr' ?_
  exact Eventually.of_forall fun n => by
    simpa [VdVWOuterProbability] using
      (vdVWInfiniteProductMeasure_firstNSample_real_tail_eq
        (P := P) (n := n) (g := g n) (hg n) ε c).symm

/--
Common-domain convergence of first-sample lifts is equivalent to the original
finite-product VdV&W outer-probability convergence for measurable real
finite-sample statistics.
-/
theorem VdVWConvergesInOuterProbabilityConst_of_firstNSample_real
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P]
    {g : (n : ℕ) -> (Fin n -> Observation) -> ℝ}
    (hg : ∀ n, Measurable (g n)) {c : ℝ}
    (hcommon :
      VdVWConvergesInOuterProbability (vdVWInfiniteProductMeasure P)
        (fun n sequence =>
          g n (vdVWFirstNSample (Observation := Observation) n sequence))
        atTop (fun _ => c)) :
    VdVWConvergesInOuterProbabilityConst
      (fun n : ℕ => Fin n -> Observation)
      (fun _ : ℕ => inferInstance)
      (fun n : ℕ => vdVWProductMeasure P n)
      g atTop c := by
  intro ε hε
  refine (hcommon ε hε).congr' ?_
  exact Eventually.of_forall fun n => by
    simpa [VdVWOuterProbability] using
      (vdVWInfiniteProductMeasure_firstNSample_real_tail_eq
        (P := P) (n := n) (g := g n) (hg n) ε c)

/--
Measurable real finite-sample statistics converge in VdV&W outer probability on
their finite product spaces if and only if their first-sample lifts converge on
the canonical infinite iid product space.
-/
theorem vdVWConvergesInOuterProbability_firstNSample_real_iff_const
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P]
    {g : (n : ℕ) -> (Fin n -> Observation) -> ℝ}
    (hg : ∀ n, Measurable (g n)) {c : ℝ} :
    VdVWConvergesInOuterProbability (vdVWInfiniteProductMeasure P)
        (fun n sequence =>
          g n (vdVWFirstNSample (Observation := Observation) n sequence))
        atTop (fun _ => c) ↔
      VdVWConvergesInOuterProbabilityConst
        (fun n : ℕ => Fin n -> Observation)
        (fun _ : ℕ => inferInstance)
        (fun n : ℕ => vdVWProductMeasure P n)
        g atTop c :=
  ⟨VdVWConvergesInOuterProbabilityConst_of_firstNSample_real P hg,
    VdVWConvergesInOuterProbability_firstNSample_real_of_const P hg⟩

/--
Integrals of finite-sample statistics can be lifted from `P^n` to `P^∞` by
precomposing with the first-`n` projection.
-/
theorem integral_vdVWInfiniteProductMeasure_firstNSample
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] (n : ℕ)
    (g : (Fin n -> Observation) -> ℝ)
    (hg : AEStronglyMeasurable g (vdVWProductMeasure P n)) :
    (∫ sequence : ℕ -> Observation,
        g (vdVWFirstNSample (Observation := Observation) n sequence)
          ∂(vdVWInfiniteProductMeasure P)) =
      ∫ sample : Fin n -> Observation, g sample ∂(vdVWProductMeasure P n) :=
  by
    let hmp := vdVWInfiniteProductMeasure_measurePreserving_firstNSample P n
    have hgmap :
        AEStronglyMeasurable g
          ((vdVWInfiniteProductMeasure P).map
            (vdVWFirstNSample (Observation := Observation) n)) := by
      simpa [hmp.map_eq] using hg
    rw [← hmp.map_eq]
    exact (integral_map (hmp.measurable.aemeasurable) hgmap).symm

/--
Finite-product ordinary means converge to zero when the corresponding
first-sample lifts converge in outer probability on the canonical infinite iid
space and are uniformly integrable there.

The theorem packages the common-space route exposed by the first-sample event
and integral recoding lemmas: finite-product convergence gives common-domain
convergence after lifting, fixed-domain Vitali/UI gives convergence of the
lifted means, and the integral recoding identifies those means with the
finite-product means.
-/
theorem
    tendsto_integral_vdVWProductMeasure_of_VdVWConvergesInOuterProbabilityConst_firstNSample_unifIntegrable
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P]
    {g : (n : ℕ) -> (Fin n -> Observation) -> ℝ}
    (hg_meas : ∀ n, Measurable (g n))
    (hg_integrable : ∀ n, Integrable (g n) (vdVWProductMeasure P n))
    (hfinite :
      VdVWConvergesInOuterProbabilityConst
        (fun n : ℕ => Fin n -> Observation)
        (fun _ : ℕ => inferInstance)
        (fun n : ℕ => vdVWProductMeasure P n)
        g atTop (0 : ℝ))
    (hg_ui :
      UnifIntegrable
        (fun n sequence =>
          g n (vdVWFirstNSample (Observation := Observation) n sequence))
        1 (vdVWInfiniteProductMeasure P)) :
    Tendsto (fun n : ℕ => ∫ sample, g n sample ∂(vdVWProductMeasure P n))
      atTop (𝓝 0) := by
  have hcommon :
      VdVWConvergesInOuterProbability (vdVWInfiniteProductMeasure P)
        (fun n sequence =>
          g n (vdVWFirstNSample (Observation := Observation) n sequence))
        atTop (fun _ => (0 : ℝ)) :=
    VdVWConvergesInOuterProbability_firstNSample_real_of_const
      (P := P) hg_meas hfinite
  have hg_lift_meas :
      ∀ n,
        AEStronglyMeasurable
          (fun sequence : ℕ -> Observation =>
            g n (vdVWFirstNSample (Observation := Observation) n sequence))
          (vdVWInfiniteProductMeasure P) := by
    intro n
    exact ((hg_meas n).comp (measurable_vdVWFirstNSample n)).aestronglyMeasurable
  have hg_lift_integrable :
      ∀ n,
        Integrable
          (fun sequence : ℕ -> Observation =>
            g n (vdVWFirstNSample (Observation := Observation) n sequence))
          (vdVWInfiniteProductMeasure P) := by
    intro n
    simpa [Function.comp_def] using
      (vdVWInfiniteProductMeasure_measurePreserving_firstNSample P n).integrable_comp_of_integrable
        (hg_integrable n)
  have hcommon_integral :
      Tendsto
        (fun n : ℕ =>
          ∫ sequence : ℕ -> Observation,
            g n (vdVWFirstNSample (Observation := Observation) n sequence)
            ∂(vdVWInfiniteProductMeasure P))
        atTop (𝓝 0) :=
    tendsto_integral_of_VdVWConvergesInOuterProbability_zero_of_unifIntegrable
      hcommon hg_lift_meas hg_lift_integrable hg_ui
  refine hcommon_integral.congr' ?_
  exact Eventually.of_forall fun n =>
    integral_vdVWInfiniteProductMeasure_firstNSample
      (P := P) n (g n) (hg_integrable n).aestronglyMeasurable

/-- Permute the first `n` coordinates of an infinite sample sequence. -/
def vdVWPermuteFirstN {Observation : Type u} {n : ℕ}
    (perm : Equiv.Perm (Fin n)) (sequence : ℕ -> Observation) :
    ℕ -> Observation :=
  fun k => if h : k < n then sequence (perm.symm ⟨k, h⟩) else sequence k

/--
The VdV&W first-`n` permutation-symmetry predicate for functions on infinite
sample sequences.
-/
def VdVWFirstNPermutationSymmetric {Observation : Type u} (n : ℕ)
    (statistic : (ℕ -> Observation) -> ℝ) : Prop :=
  ∀ (perm : Equiv.Perm (Fin n)) (sequence : ℕ -> Observation),
    statistic (vdVWPermuteFirstN perm sequence) = statistic sequence

/-- A permutation of `ℕ` fixes every coordinate from `n` onward. -/
def VdVWNatPermFixesFrom (n : ℕ) (perm : Equiv.Perm ℕ) : Prop :=
  ∀ k, n ≤ k -> perm k = k

/--
Extend a finite-coordinate permutation to a permutation of `ℕ` that fixes all
coordinates outside the first `n`.
-/
noncomputable def vdVWNatPermOfFin {n : ℕ}
    (perm : Equiv.Perm (Fin n)) : Equiv.Perm ℕ :=
  perm.viaFintypeEmbedding Fin.valEmbedding

/-- The finite-to-natural extension agrees with the finite permutation on the first `n` coordinates. -/
theorem vdVWNatPermOfFin_apply_fin {n : ℕ}
    (perm : Equiv.Perm (Fin n)) (i : Fin n) :
    vdVWNatPermOfFin perm (i : ℕ) = (perm i : ℕ) := by
  simpa [vdVWNatPermOfFin] using
    (Equiv.Perm.viaFintypeEmbedding_apply_image
      (e := perm) (f := Fin.valEmbedding) i)

/-- The finite-to-natural extension fixes every coordinate from `n` onward. -/
theorem VdVWNatPermFixesFrom_natPermOfFin {n : ℕ}
    (perm : Equiv.Perm (Fin n)) :
    VdVWNatPermFixesFrom n (vdVWNatPermOfFin perm) := by
  intro k hk
  have hnot : k ∉ Set.range (Fin.valEmbedding : Fin n ↪ ℕ) := by
    rintro ⟨i, hi⟩
    have hk_eq : k = (i : ℕ) := hi.symm
    exact (Nat.not_lt_of_ge hk) (by
      rw [hk_eq]
      exact i.isLt)
  simpa [vdVWNatPermOfFin] using
    (Equiv.Perm.viaFintypeEmbedding_apply_notMem_range
      (e := perm) (f := Fin.valEmbedding) hnot)

/-- Permute an infinite sample sequence by a permutation of coordinate indices. -/
def vdVWPermuteNatSequence {Observation : Type u}
    (perm : Equiv.Perm ℕ) (sequence : ℕ -> Observation) : ℕ -> Observation :=
  fun k => sequence (perm.symm k)

/-- Infinite-coordinate permutation of the sample sequence space. -/
noncomputable def vdVWNatCoordinatePermMeasurableEquiv
    {Observation : Type u} [MeasurableSpace Observation]
    (perm : Equiv.Perm ℕ) :
    (ℕ -> Observation) ≃ᵐ (ℕ -> Observation) :=
  MeasurableEquiv.piCongrLeft (fun _ : ℕ => Observation) perm

/-- Coordinate display for `vdVWNatCoordinatePermMeasurableEquiv`. -/
theorem vdVWNatCoordinatePermMeasurableEquiv_apply_apply
    {Observation : Type u} [MeasurableSpace Observation]
    (perm : Equiv.Perm ℕ) (sequence : ℕ -> Observation) (i : ℕ) :
    vdVWNatCoordinatePermMeasurableEquiv perm sequence (perm i) = sequence i :=
  by
    simpa [vdVWNatCoordinatePermMeasurableEquiv] using
      (MeasurableEquiv.piCongrLeft_apply_apply
        (β := fun _ : ℕ => Observation) perm sequence i)

/-- The measurable-equivalence display agrees with `vdVWPermuteNatSequence`. -/
theorem vdVWNatCoordinatePermMeasurableEquiv_eq_vdVWPermuteNatSequence
    {Observation : Type u} [MeasurableSpace Observation]
    (perm : Equiv.Perm ℕ) :
    (vdVWNatCoordinatePermMeasurableEquiv
      (Observation := Observation) perm : (ℕ -> Observation) -> (ℕ -> Observation)) =
      vdVWPermuteNatSequence perm := by
  funext sequence k
  have hcoord :=
    vdVWNatCoordinatePermMeasurableEquiv_apply_apply
      (Observation := Observation) perm sequence (perm.symm k)
  simpa [vdVWPermuteNatSequence] using hcoord

/-- The iid infinite product measure is invariant under coordinate permutations. -/
theorem vdVWInfiniteProductMeasure_measurePreserving_natCoordinatePerm
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P]
    (perm : Equiv.Perm ℕ) :
    MeasurePreserving (vdVWNatCoordinatePermMeasurableEquiv
      (Observation := Observation) perm)
      (vdVWInfiniteProductMeasure P) (vdVWInfiniteProductMeasure P) := by
  refine ⟨(vdVWNatCoordinatePermMeasurableEquiv
      (Observation := Observation) perm).measurable, ?_⟩
  simpa [vdVWInfiniteProductMeasure, vdVWNatCoordinatePermMeasurableEquiv] using
    (Measure.infinitePi_map_piCongrLeft
      (μ := fun _ : ℕ => P) (X := fun _ : ℕ => Observation) perm)

/-- The iid infinite product measure is invariant under `vdVWPermuteNatSequence`. -/
theorem vdVWInfiniteProductMeasure_measurePreserving_permuteNatSequence
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P]
    (perm : Equiv.Perm ℕ) :
    MeasurePreserving (vdVWPermuteNatSequence
      (Observation := Observation) perm)
      (vdVWInfiniteProductMeasure P) (vdVWInfiniteProductMeasure P) := by
  simpa [vdVWNatCoordinatePermMeasurableEquiv_eq_vdVWPermuteNatSequence
    (Observation := Observation) perm] using
    (vdVWInfiniteProductMeasure_measurePreserving_natCoordinatePerm
      (Observation := Observation) P perm)

/-- A permutation fixing every coordinate from `n` onward maps `{0, ..., n-1}` into itself. -/
theorem VdVWNatPermFixesFrom.image_lt
    {n : ℕ} {perm : Equiv.Perm ℕ}
    (hfix : VdVWNatPermFixesFrom n perm)
    {k : ℕ} (hk : k < n) :
    perm k < n := by
  by_contra hnot
  have hnle : n ≤ perm k := Nat.le_of_not_gt hnot
  have hfixed : perm (perm k) = perm k := hfix (perm k) hnle
  have hperm_eq : perm k = k := perm.injective hfixed
  exact (not_le_of_gt hk) (by simpa [hperm_eq] using hnle)

/-- The inverse of a permutation fixing every coordinate from `n` onward also preserves `{0, ..., n-1}`. -/
theorem VdVWNatPermFixesFrom.symm_image_lt
    {n : ℕ} {perm : Equiv.Perm ℕ}
    (hfix : VdVWNatPermFixesFrom n perm)
    {k : ℕ} (hk : k < n) :
    perm.symm k < n := by
  by_contra hnot
  have hnle : n ≤ perm.symm k := Nat.le_of_not_gt hnot
  have hfixed : perm (perm.symm k) = perm.symm k :=
    hfix (perm.symm k) hnle
  have hperm_eq : k = perm.symm k := by
    simpa using hfixed
  exact (not_le_of_gt hk) (by simpa [← hperm_eq] using hnle)

/-- Restrict a permutation fixing every coordinate from `n` onward to the first `n` coordinates. -/
noncomputable def vdVWNatPermRestrictFin
    {n : ℕ} (perm : Equiv.Perm ℕ)
    (hfix : VdVWNatPermFixesFrom n perm) :
    Equiv.Perm (Fin n) :=
  Equiv.ofBijective
    (fun i : Fin n => ⟨perm i, hfix.image_lt i.2⟩)
    ⟨by
      intro i j hij
      apply Fin.ext
      apply perm.injective
      exact congrArg (fun x : Fin n => (x : ℕ)) hij,
    by
      intro j
      refine ⟨⟨perm.symm j, hfix.symm_image_lt j.2⟩, ?_⟩
      ext
      simp⟩

/-- Restricting the natural extension of a finite permutation recovers the original permutation. -/
theorem vdVWNatPermRestrictFin_natPermOfFin
    {n : ℕ} (perm : Equiv.Perm (Fin n)) :
    vdVWNatPermRestrictFin (vdVWNatPermOfFin perm)
        (VdVWNatPermFixesFrom_natPermOfFin perm) =
      perm := by
  ext i
  exact vdVWNatPermOfFin_apply_fin perm i

/--
The infinite-coordinate form of VdV&W permutation symmetry: a statistic is
invariant under all coordinate permutations that fix every coordinate from
`n` onward.
-/
def VdVWPermutationSymmetricFrom {Observation : Type u} (n : ℕ)
    (statistic : (ℕ -> Observation) -> ℝ) : Prop :=
  ∀ (perm : Equiv.Perm ℕ), VdVWNatPermFixesFrom n perm ->
    ∀ sequence : ℕ -> Observation,
      statistic (vdVWPermuteNatSequence perm sequence) = statistic sequence

/--
Symmetry under permutations fixing coordinates from `m` onward implies
symmetry under the smaller group fixing coordinates from `n` onward, when
`n ≤ m`.
-/
theorem VdVWPermutationSymmetricFrom.mono
    {Observation : Type u} {statistic : (ℕ -> Observation) -> ℝ}
    {n m : ℕ} (hnm : n ≤ m)
    (hsymm : VdVWPermutationSymmetricFrom m statistic) :
    VdVWPermutationSymmetricFrom n statistic := by
  intro perm hfix sequence
  exact hsymm perm (fun k hmk => hfix k (hnm.trans hmk)) sequence

/--
Generators for the VdV&W permutation-symmetric sigma-field `Σ_n`: measurable
real functions symmetric under all permutations fixing coordinates from `n`
onward, pulled back along Borel sets.
-/
def VdVWPermutationSymmetricGeneratorSet
    (Observation : Type u) [MeasurableSpace Observation] (n : ℕ) :
    Set (Set (ℕ -> Observation)) :=
  {s | ∃ statistic : (ℕ -> Observation) -> ℝ,
    Measurable statistic ∧
      VdVWPermutationSymmetricFrom n statistic ∧
      ∃ t : Set ℝ, MeasurableSet t ∧ s = statistic ⁻¹' t}

/-- The VdV&W permutation-symmetric sigma-field `Σ_n`. -/
@[reducible]
def vdVWPermutationSymmetricMeasurableSpace
    (Observation : Type u) [MeasurableSpace Observation] (n : ℕ) :
    MeasurableSpace (ℕ -> Observation) :=
  MeasurableSpace.generateFrom
    (VdVWPermutationSymmetricGeneratorSet Observation n)

/-- A generator of `Σ_n` is measurable in `Σ_n`. -/
theorem measurableSet_vdVWPermutationSymmetricMeasurableSpace_of_generator
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    {s : Set (ℕ -> Observation)}
    (hs : s ∈ VdVWPermutationSymmetricGeneratorSet Observation n) :
    MeasurableSet[vdVWPermutationSymmetricMeasurableSpace Observation n] s :=
  MeasurableSpace.measurableSet_generateFrom hs

/--
The VdV&W permutation-symmetric sigma-fields decrease with `n`: if `n ≤ m`,
then every `Σ_m`-measurable set is `Σ_n`-measurable.
-/
theorem vdVWPermutationSymmetricMeasurableSpace_antitone
    {Observation : Type u} [MeasurableSpace Observation]
    {n m : ℕ} (hnm : n ≤ m) :
    vdVWPermutationSymmetricMeasurableSpace Observation m ≤
      vdVWPermutationSymmetricMeasurableSpace Observation n := by
  refine MeasurableSpace.generateFrom_le ?_
  intro s hs
  rcases hs with ⟨statistic, hmeas, hsymm, t, ht, rfl⟩
  exact MeasurableSpace.measurableSet_generateFrom
    ⟨statistic, hmeas, VdVWPermutationSymmetricFrom.mono hnm hsymm, t, ht, rfl⟩

/--
A measurable real statistic symmetric under all permutations fixing
coordinates from `n` onward is measurable with respect to the generated
VdV&W permutation-symmetric sigma-field `Σ_n`.
-/
theorem measurable_vdVWPermutationSymmetricMeasurableSpace_of_symmetric
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    {statistic : (ℕ -> Observation) -> ℝ}
    (hmeas : Measurable statistic)
    (hsymm : VdVWPermutationSymmetricFrom n statistic) :
    Measurable[vdVWPermutationSymmetricMeasurableSpace Observation n] statistic := by
  intro t ht
  exact MeasurableSpace.measurableSet_generateFrom
    ⟨statistic, hmeas, hsymm, t, ht, rfl⟩

/--
Every `Σ_n`-measurable set is invariant under coordinate permutations fixing
the tail from `n` onward.

This is the generated-sigma-field invariant-set primitive needed for the
conditional-expectation symmetry step in VdV&W Lemma 2.4.5.
-/
theorem preimage_vdVWPermuteNatSequence_eq_of_measurableSet_permutationSymmetric
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    (perm : Equiv.Perm ℕ) (hfix : VdVWNatPermFixesFrom n perm)
    {s : Set (ℕ -> Observation)}
    (hs : MeasurableSet[vdVWPermutationSymmetricMeasurableSpace Observation n] s) :
    vdVWPermuteNatSequence perm ⁻¹' s = s := by
  let generator := VdVWPermutationSymmetricGeneratorSet Observation n
  change MeasurableSet[MeasurableSpace.generateFrom generator] s at hs
  refine
    MeasurableSpace.generateFrom_induction generator
      (fun t _ht => vdVWPermuteNatSequence perm ⁻¹' t = t) ?_ ?_ ?_ ?_ s hs
  · intro t ht _hmeas_t
    rcases ht with ⟨statistic, _hmeas_statistic, hsymm, target, _htarget, rfl⟩
    ext sequence
    simp [Set.mem_preimage, hsymm perm hfix sequence]
  · simp
  · intro t _ht hpre
    ext sequence
    simp [hpre]
  · intro sets _hsets hpre
    ext sequence
    simp [hpre]

/--
Coordinate permutations fixing the tail are measurable maps from `Σ_n` to
itself.  This is a direct consequence of the invariant-set theorem above.
-/
theorem measurable_vdVWPermuteNatSequence_permutationSymmetric
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    (perm : Equiv.Perm ℕ) (hfix : VdVWNatPermFixesFrom n perm) :
    Measurable[vdVWPermutationSymmetricMeasurableSpace Observation n,
      vdVWPermutationSymmetricMeasurableSpace Observation n]
      (vdVWPermuteNatSequence (Observation := Observation) perm) := by
  intro s hs
  rw [preimage_vdVWPermuteNatSequence_eq_of_measurableSet_permutationSymmetric
    (Observation := Observation) perm hfix hs]
  exact hs

/--
Set-integral invariance over a `Σ_n`-measurable set under a tail-fixing
coordinate permutation of the iid infinite product space.

This is the integral-side primitive needed to identify conditional
expectations of leave-one-out terms in VdV&W Lemma 2.4.5.
-/
theorem setIntegral_vdVWInfiniteProductMeasure_comp_permuteNatSequence_of_measurableSet_permutationSymmetric
    {Observation : Type u} [MeasurableSpace Observation]
    (P : Measure Observation) [IsProbabilityMeasure P] {n : ℕ}
    (perm : Equiv.Perm ℕ) (hfix : VdVWNatPermFixesFrom n perm)
    {s : Set (ℕ -> Observation)}
    (hs : MeasurableSet[vdVWPermutationSymmetricMeasurableSpace Observation n] s)
    (f : (ℕ -> Observation) -> ℝ) :
    (∫ sequence in s,
        f (vdVWPermuteNatSequence (Observation := Observation) perm sequence)
          ∂(vdVWInfiniteProductMeasure P)) =
      ∫ sequence in s, f sequence ∂(vdVWInfiniteProductMeasure P) := by
  let e := vdVWNatCoordinatePermMeasurableEquiv
    (Observation := Observation) perm
  have hpre : e ⁻¹' s = s := by
    simpa [e, vdVWNatCoordinatePermMeasurableEquiv_eq_vdVWPermuteNatSequence
      (Observation := Observation) perm] using
      preimage_vdVWPermuteNatSequence_eq_of_measurableSet_permutationSymmetric
        (Observation := Observation) perm hfix hs
  have hmp : MeasurePreserving e
      (vdVWInfiniteProductMeasure P) (vdVWInfiniteProductMeasure P) := by
    simpa [e] using
      vdVWInfiniteProductMeasure_measurePreserving_natCoordinatePerm
        (Observation := Observation) P perm
  calc
    (∫ sequence in s,
        f (vdVWPermuteNatSequence (Observation := Observation) perm sequence)
          ∂(vdVWInfiniteProductMeasure P))
        =
      ∫ sequence in s, f (e sequence) ∂(vdVWInfiniteProductMeasure P) := by
          simp [e, vdVWNatCoordinatePermMeasurableEquiv_eq_vdVWPermuteNatSequence
            (Observation := Observation) perm]
    _ = ∫ sequence in e ⁻¹' s, f (e sequence)
        ∂(vdVWInfiniteProductMeasure P) := by
          rw [hpre]
    _ = ∫ sequence in s, f sequence
        ∂(Measure.map e (vdVWInfiniteProductMeasure P)) := by
          exact
            (setIntegral_map_equiv
              (μ := vdVWInfiniteProductMeasure P) e f s).symm
    _ = ∫ sequence in s, f sequence ∂(vdVWInfiniteProductMeasure P) := by
          rw [hmp.map_eq]

/--
Projecting the first `n` coordinates after an infinite permutation fixing the
tail is the finite-coordinate permutation induced by restricting that
permutation to the first `n` coordinates.
-/
theorem vdVWFirstNSample_permuteNatSequence
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    (perm : Equiv.Perm ℕ) (hfix : VdVWNatPermFixesFrom n perm)
    (sequence : ℕ -> Observation) :
    vdVWFirstNSample n (vdVWPermuteNatSequence perm sequence) =
      vdVWFinCoordinatePermMeasurableEquiv
        (vdVWNatPermRestrictFin perm hfix) (vdVWFirstNSample n sequence) := by
  ext i
  let restricted := vdVWNatPermRestrictFin perm hfix
  have hrestricted_symm :
      ((restricted.symm i : Fin n) : ℕ) = perm.symm (i : ℕ) := by
    apply perm.injective
    have happly :
        perm (((restricted.symm i : Fin n) : ℕ)) = (i : ℕ) := by
      change ((restricted (restricted.symm i) : Fin n) : ℕ) = (i : ℕ)
      exact
        congrArg (fun x : Fin n => (x : ℕ))
          (restricted.apply_symm_apply i)
    simpa using happly
  have hcoord :=
    vdVWFinCoordinatePermMeasurableEquiv_apply_apply
      (Observation := Observation) restricted
      (vdVWFirstNSample n sequence)
      (restricted.symm i)
  simpa [vdVWFirstNSample, vdVWPermuteNatSequence, hrestricted_symm] using
    hcoord.symm

/--
Projecting the first `n` coordinates after applying the natural extension of a
finite permutation is exactly the finite-coordinate permutation of the
projected sample.
-/
theorem vdVWFirstNSample_permuteNatSequence_natPermOfFin
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    (perm : Equiv.Perm (Fin n)) (sequence : ℕ -> Observation) :
    vdVWFirstNSample n
        (vdVWPermuteNatSequence
          (Observation := Observation) (vdVWNatPermOfFin perm) sequence) =
      vdVWFinCoordinatePermMeasurableEquiv perm (vdVWFirstNSample n sequence) := by
  rw [vdVWFirstNSample_permuteNatSequence
    (perm := vdVWNatPermOfFin perm)
    (hfix := VdVWNatPermFixesFrom_natPermOfFin perm)]
  rw [vdVWNatPermRestrictFin_natPermOfFin]

/--
Projecting the first `n` coordinates after permuting an infinite sequence is
the finite-coordinate permutation of the first-`n` sample.
-/
theorem vdVWFirstNSample_permuteFirstN
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    (perm : Equiv.Perm (Fin n)) (sequence : ℕ -> Observation) :
    vdVWFirstNSample n (vdVWPermuteFirstN perm sequence) =
      vdVWFinCoordinatePermMeasurableEquiv perm (vdVWFirstNSample n sequence) := by
  funext i
  have hcoord :=
    vdVWFinCoordinatePermMeasurableEquiv_apply_apply
      (Observation := Observation) perm (vdVWFirstNSample n sequence) (perm.symm i)
  simpa [vdVWFirstNSample, vdVWPermuteFirstN] using hcoord.symm

/-- The weighted finite sample sum appearing in VdV&W display `(2.3.2)`. -/
noncomputable def vdVWWeightedSampleSum {Observation : Type u} {Index : Type v}
    (classFun : Index -> Observation -> ℝ) {n : ℕ}
    (weights : Fin n -> ℝ) (index : Index)
    (sample : Fin n -> Observation) : ℝ :=
  ∑ i : Fin n, weights i * classFun index (sample i)

/--
Finite-coordinate permutations preserve weighted sample sums after the
corresponding inverse permutation of the weights.
-/
theorem vdVWWeightedSampleSum_finCoordinatePerm
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    (classFun : Index -> Observation -> ℝ) {n : ℕ}
    (weights : Fin n -> ℝ) (perm : Equiv.Perm (Fin n))
    (index : Index) (sample : Fin n -> Observation) :
    vdVWWeightedSampleSum classFun (fun i : Fin n => weights (perm.symm i))
        index (vdVWFinCoordinatePermMeasurableEquiv perm sample) =
      vdVWWeightedSampleSum classFun weights index sample := by
  let g : Fin n -> ℝ := fun i =>
    weights (perm.symm i) *
      classFun index (vdVWFinCoordinatePermMeasurableEquiv perm sample i)
  calc
    vdVWWeightedSampleSum classFun (fun i : Fin n => weights (perm.symm i))
        index (vdVWFinCoordinatePermMeasurableEquiv perm sample)
        = ∑ i : Fin n, g i := rfl
    _ = ∑ i : Fin n, g (perm i) := by
          simpa using (Equiv.sum_comp perm g).symm
    _ = vdVWWeightedSampleSum classFun weights index sample := by
          simp [g, vdVWWeightedSampleSum,
            vdVWFinCoordinatePermMeasurableEquiv_apply_apply]

/-- Uniform empirical weights make each class-member sample sum permutation-invariant. -/
theorem vdVWWeightedSampleSum_uniform_finCoordinatePerm
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    (classFun : Index -> Observation -> ℝ) {n : ℕ}
    (perm : Equiv.Perm (Fin n)) (index : Index)
    (sample : Fin n -> Observation) :
    vdVWWeightedSampleSum classFun (fun _ : Fin n => (n : ℝ)⁻¹)
        index (vdVWFinCoordinatePermMeasurableEquiv perm sample) =
      vdVWWeightedSampleSum classFun (fun _ : Fin n => (n : ℝ)⁻¹)
        index sample := by
  simpa using
    (vdVWWeightedSampleSum_finCoordinatePerm
      (classFun := classFun) (weights := fun _ : Fin n => (n : ℝ)⁻¹)
      perm index sample)

/--
The supremum over a class in VdV&W display `(2.3.2)`.

For an empty class this follows mathlib's complete-lattice convention for
`⨆ i ∈ ∅, ...`; theorem statements using nonempty classes can add that
hypothesis separately.
-/
noncomputable def vdVWWeightedClassSupremum
    {Observation : Type u} {Index : Type v}
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation) : ℝ :=
  ⨆ index, ⨆ (_ : index ∈ indexClass),
    |vdVWWeightedSampleSum classFun weights index sample|

/-- The VdV&W finite-sample supremum over an empty class is zero. -/
@[simp]
theorem vdVWWeightedClassSupremum_empty
    {Observation : Type u} {Index : Type v}
    (classFun : Index -> Observation -> ℝ)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation) :
    vdVWWeightedClassSupremum (∅ : Set Index) classFun weights sample = 0 := by
  simp [vdVWWeightedClassSupremum]

/--
The uniform-weight finite-sample supremum in VdV&W display `(2.3.2)` is
permutation-invariant.
-/
theorem vdVWWeightedClassSupremum_uniform_finCoordinatePerm
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {n : ℕ} (perm : Equiv.Perm (Fin n))
    (sample : Fin n -> Observation) :
    vdVWWeightedClassSupremum indexClass classFun
        (fun _ : Fin n => (n : ℝ)⁻¹)
        (vdVWFinCoordinatePermMeasurableEquiv perm sample) =
      vdVWWeightedClassSupremum indexClass classFun
        (fun _ : Fin n => (n : ℝ)⁻¹) sample := by
  simp [vdVWWeightedClassSupremum,
    vdVWWeightedSampleSum_uniform_finCoordinatePerm]

/--
Leave-one-out transport for the uniform class supremum on the infinite product
space: applying the natural extension of the canonical finite permutation and
then removing the last coordinate is the same as removing `omitted` before the
transport.
-/
theorem vdVWWeightedClassSupremum_leaveOneOut_last_comp_natPermOfFin_eq
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {n : ℕ} (omitted : Fin (n + 1)) (sequence : ℕ -> Observation) :
    vdVWWeightedClassSupremum indexClass classFun
        (fun _ : Fin n => (n : ℝ)⁻¹)
        ((Fin.last n).removeNth
          (vdVWFirstNSample (Observation := Observation) (n + 1)
            (vdVWPermuteNatSequence
              (Observation := Observation)
              (vdVWNatPermOfFin (vdVWLeaveOneOutToLastPerm omitted))
              sequence))) =
      vdVWWeightedClassSupremum indexClass classFun
        (fun _ : Fin n => (n : ℝ)⁻¹)
        (omitted.removeNth
          (vdVWFirstNSample (Observation := Observation) (n + 1) sequence)) := by
  rw [vdVWFirstNSample_permuteNatSequence_natPermOfFin
    (perm := vdVWLeaveOneOutToLastPerm omitted)]
  rw [removeNth_last_vdVWFinCoordinatePerm_leaveOneOutToLastPerm]

/--
The infinite-sequence statistic induced by the uniform finite-sample class
supremum is symmetric in the first `n` arguments, matching the generator shape
of VdV&W Lemma 2.4.5.
-/
theorem vdVWFirstNPermutationSymmetric_uniformClassSupremum
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (n : ℕ) :
    VdVWFirstNPermutationSymmetric n
      (fun sequence : ℕ -> Observation =>
        vdVWWeightedClassSupremum indexClass classFun
          (fun _ : Fin n => (n : ℝ)⁻¹) (vdVWFirstNSample n sequence)) := by
  intro perm sequence
  change
    vdVWWeightedClassSupremum indexClass classFun
        (fun _ : Fin n => (n : ℝ)⁻¹)
        (vdVWFirstNSample n (vdVWPermuteFirstN perm sequence)) =
      vdVWWeightedClassSupremum indexClass classFun
        (fun _ : Fin n => (n : ℝ)⁻¹) (vdVWFirstNSample n sequence)
  rw [vdVWFirstNSample_permuteFirstN]
  exact
    vdVWWeightedClassSupremum_uniform_finCoordinatePerm
      indexClass classFun perm (vdVWFirstNSample n sequence)

/--
The same uniform empirical supremum statistic is symmetric under every
infinite-coordinate permutation fixing the tail from `n` onward.  This is the
form consumed by the generated `Σ_n` permutation-symmetric sigma-field.
-/
theorem VdVWPermutationSymmetricFrom_uniformClassSupremum
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (n : ℕ) :
    VdVWPermutationSymmetricFrom n
      (fun sequence : ℕ -> Observation =>
        vdVWWeightedClassSupremum indexClass classFun
          (fun _ : Fin n => (n : ℝ)⁻¹) (vdVWFirstNSample n sequence)) := by
  intro perm hfix sequence
  change
    vdVWWeightedClassSupremum indexClass classFun
        (fun _ : Fin n => (n : ℝ)⁻¹)
        (vdVWFirstNSample n (vdVWPermuteNatSequence perm sequence)) =
      vdVWWeightedClassSupremum indexClass classFun
        (fun _ : Fin n => (n : ℝ)⁻¹) (vdVWFirstNSample n sequence)
  rw [vdVWFirstNSample_permuteNatSequence perm hfix]
  exact
    vdVWWeightedClassSupremum_uniform_finCoordinatePerm
      indexClass classFun (vdVWNatPermRestrictFin perm hfix)
      (vdVWFirstNSample n sequence)

/--
The value set whose supremum is represented by
`vdVWWeightedClassSupremum`.  This set-level form makes boundedness and
subset arguments explicit, avoiding hidden `ℝ` supremum fallback conventions.
-/
def vdVWWeightedClassValueSet
    {Observation : Type u} {Index : Type v}
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation) : Set ℝ :=
  {value | ∃ index, index ∈ indexClass ∧
    value = |vdVWWeightedSampleSum classFun weights index sample|}

/-- A class member contributes its absolute weighted sum to the value set. -/
theorem abs_vdVWWeightedSampleSum_mem_valueSet
    {Observation : Type u} {Index : Type v}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation) {index : Index}
    (hindex : index ∈ indexClass) :
    |vdVWWeightedSampleSum classFun weights index sample| ∈
      vdVWWeightedClassValueSet indexClass classFun weights sample :=
  ⟨index, hindex, rfl⟩

/-- Value sets are monotone under subclass inclusion. -/
theorem vdVWWeightedClassValueSet_mono
    {Observation : Type u} {Index : Type v}
    {smaller larger : Set Index} {classFun : Index -> Observation -> ℝ}
    (hsubset : smaller ⊆ larger)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation) :
    vdVWWeightedClassValueSet smaller classFun weights sample ⊆
      vdVWWeightedClassValueSet larger classFun weights sample := by
  intro value hvalue
  rcases hvalue with ⟨index, hindex, rfl⟩
  exact abs_vdVWWeightedSampleSum_mem_valueSet weights sample (hsubset hindex)

/--
For a finite class, the value set whose supremum defines
`vdVWWeightedClassSupremum` is bounded above for every fixed sample and weight
vector.
-/
theorem bddAbove_vdVWWeightedClassValueSet_of_finite
    {Observation : Type u} {Index : Type v}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (hindex_finite : indexClass.Finite)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation) :
    BddAbove (vdVWWeightedClassValueSet indexClass classFun weights sample) := by
  let imageValues : Set ℝ :=
    (fun index : Index =>
      |vdVWWeightedSampleSum classFun weights index sample|) '' indexClass
  have himage_finite : imageValues.Finite := hindex_finite.image _
  have hsubset :
      vdVWWeightedClassValueSet indexClass classFun weights sample ⊆
        imageValues := by
    intro value hvalue
    rcases hvalue with ⟨index, hindex, rfl⟩
    exact ⟨index, hindex, rfl⟩
  exact BddAbove.mono hsubset himage_finite.bddAbove

/-- Weighted class suprema are nonnegative, including mathlib's empty-class case. -/
theorem vdVWWeightedClassSupremum_nonneg
    {Observation : Type u} {Index : Type v}
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation) :
    0 ≤ vdVWWeightedClassSupremum indexClass classFun weights sample := by
  unfold vdVWWeightedClassSupremum
  exact Real.iSup_nonneg fun index =>
    Real.iSup_nonneg fun _ : index ∈ indexClass =>
      abs_nonneg (vdVWWeightedSampleSum classFun weights index sample)

/-- Flipping every weight negates each weighted sample sum. -/
theorem vdVWWeightedSampleSum_neg_weights
    {Observation : Type u} {Index : Type v}
    {classFun : Index -> Observation -> ℝ} {n : ℕ}
    (weights : Fin n -> ℝ) (index : Index)
    (sample : Fin n -> Observation) :
    vdVWWeightedSampleSum classFun (fun i : Fin n => -weights i) index sample =
      -vdVWWeightedSampleSum classFun weights index sample := by
  unfold vdVWWeightedSampleSum
  rw [← Finset.sum_neg_distrib]
  exact Finset.sum_congr rfl fun i _hi => by ring

/--
The weighted class supremum is invariant under flipping all weights, since it
takes absolute values of the weighted sums.
-/
theorem vdVWWeightedClassSupremum_neg_weights
    {Observation : Type u} {Index : Type v}
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation) :
    vdVWWeightedClassSupremum indexClass classFun (fun i : Fin n => -weights i)
        sample =
      vdVWWeightedClassSupremum indexClass classFun weights sample := by
  unfold vdVWWeightedClassSupremum
  congr with index
  congr with hindex
  rw [vdVWWeightedSampleSum_neg_weights, abs_neg]

/--
A deterministic finite-cover bound for the weighted supremum in VdV&W display
`(2.3.2)`.

This is the finite-discretization handoff needed for later Chapter 2
covering-number bounds: once every class member is controlled by its finite
cover center, it is enough to bound the finitely many center sums.
-/
theorem vdVWWeightedClassSupremum_le_upper_add_of_finiteMetricCover
    {Observation : Type u} {Index : Type v} [PseudoEMetricSpace Index]
    {indexClass : Set Index} {epsilon : ℝ≥0} {cardinality : ℕ}
    (cover : FiniteMetricCoverAtCard indexClass epsilon cardinality)
    {classFun : Index -> Observation -> ℝ} {n : ℕ}
    (weights : Fin n -> ℝ) (sample : Fin n -> Observation) {upper : ℝ}
    (hupper_nonneg : 0 ≤ upper)
    (hupper :
      ∀ centerIndex : Fin cardinality,
        |vdVWWeightedSampleSum classFun weights (cover.center centerIndex) sample| ≤
          upper)
    (hcontrol :
      ∀ index hindex,
        |vdVWWeightedSampleSum classFun weights index sample -
          vdVWWeightedSampleSum classFun weights
            (cover.center (cover.centerOf index hindex)) sample| ≤
          (epsilon : ℝ)) :
    vdVWWeightedClassSupremum indexClass classFun weights sample ≤
      upper + (epsilon : ℝ) := by
  have htarget_nonneg : 0 ≤ upper + (epsilon : ℝ) :=
    add_nonneg hupper_nonneg (NNReal.coe_nonneg epsilon)
  unfold vdVWWeightedClassSupremum
  apply Real.iSup_le
  · intro index
    apply Real.iSup_le
    · intro hindex
      let centerIndex := cover.centerOf index hindex
      let targetSum := vdVWWeightedSampleSum classFun weights index sample
      let centerSum :=
        vdVWWeightedSampleSum classFun weights (cover.center centerIndex) sample
      have hdecomp : centerSum + (targetSum - centerSum) = targetSum := by ring
      calc
        |targetSum| = |centerSum + (targetSum - centerSum)| :=
          (congrArg abs hdecomp).symm
        _ ≤ |centerSum| + |targetSum - centerSum| :=
          abs_add_le centerSum (targetSum - centerSum)
        _ ≤ upper + (epsilon : ℝ) := add_le_add (hupper centerIndex) (hcontrol index hindex)
    · exact htarget_nonneg
  · exact htarget_nonneg

/--
A bounded weighted value set bounds the corresponding inner supremum range
used by `vdVWWeightedClassSupremum`.
-/
theorem bddAbove_vdVWWeightedClassSupremum_range_of_valueSet
    {Observation : Type u} {Index : Type v}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation)
    (hbdd :
      BddAbove (vdVWWeightedClassValueSet indexClass classFun weights sample)) :
    BddAbove
      (Set.range fun candidate : Index =>
        ⨆ (_ : candidate ∈ indexClass),
          |vdVWWeightedSampleSum classFun weights candidate sample|) := by
  rcases hbdd with ⟨upper, hupper⟩
  refine ⟨max upper 0, ?_⟩
  intro value hvalue
  rcases hvalue with ⟨index, rfl⟩
  apply Real.iSup_le
  · intro hindex
    exact le_trans
      (hupper
        (abs_vdVWWeightedSampleSum_mem_valueSet weights sample hindex))
      (le_max_left upper 0)
  · exact le_max_right upper 0

/--
A class member's absolute weighted sum is bounded by the class supremum once
the associated value set is bounded above.
-/
theorem abs_vdVWWeightedSampleSum_le_vdVWWeightedClassSupremum_of_bddAbove
    {Observation : Type u} {Index : Type v}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {n : ℕ} {weights : Fin n -> ℝ} {sample : Fin n -> Observation}
    (hbdd :
      BddAbove (vdVWWeightedClassValueSet indexClass classFun weights sample))
    {index : Index} (hindex : index ∈ indexClass) :
    |vdVWWeightedSampleSum classFun weights index sample| ≤
      vdVWWeightedClassSupremum indexClass classFun weights sample := by
  unfold vdVWWeightedClassSupremum
  have hbdd_range :
      BddAbove
        (Set.range fun candidate : Index =>
          ⨆ (_ : candidate ∈ indexClass),
            |vdVWWeightedSampleSum classFun weights candidate sample|) :=
    bddAbove_vdVWWeightedClassSupremum_range_of_valueSet weights sample hbdd
  calc
    |vdVWWeightedSampleSum classFun weights index sample|
        = ⨆ (_ : index ∈ indexClass),
            |vdVWWeightedSampleSum classFun weights index sample| := by
          symm
          simp [hindex]
    _ ≤ ⨆ candidate : Index, ⨆ (_ : candidate ∈ indexClass),
          |vdVWWeightedSampleSum classFun weights candidate sample| :=
        le_ciSup hbdd_range index

/--
A pointwise uniform bound on every class member gives boundedness of the
finite weighted value set.
-/
theorem bddAbove_vdVWWeightedClassValueSet_of_uniform_bound
    {Observation : Type u} {Index : Type v}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {n : ℕ} (weights : Fin n -> ℝ) (sample : Fin n -> Observation)
    {bound : ℝ}
    (hbound :
      ∀ index, index ∈ indexClass -> ∀ observation,
        |classFun index observation| ≤ bound) :
    BddAbove (vdVWWeightedClassValueSet indexClass classFun weights sample) := by
  refine ⟨∑ i : Fin n, |weights i| * bound, ?_⟩
  intro value hvalue
  rcases hvalue with ⟨index, hindex, rfl⟩
  calc
    |vdVWWeightedSampleSum classFun weights index sample|
        = |∑ i : Fin n, weights i * classFun index (sample i)| := by
          rfl
    _ ≤ ∑ i : Fin n, |weights i * classFun index (sample i)| := by
          simpa using
            (Finset.abs_sum_le_sum_abs
              (fun i : Fin n => weights i * classFun index (sample i))
              (Finset.univ : Finset (Fin n)))
    _ = ∑ i : Fin n, |weights i| * |classFun index (sample i)| := by
          simp [abs_mul]
    _ ≤ ∑ i : Fin n, |weights i| * bound := by
          exact Finset.sum_le_sum fun i _hi =>
            mul_le_mul_of_nonneg_left
              (hbound index hindex (sample i)) (abs_nonneg (weights i))

/-- Coordinate measurability of all functions in a class. -/
def VdVWClassCoordinateMeasurable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ) : Prop :=
  ∀ index, index ∈ indexClass -> Measurable (classFun index)

/--
VdV&W Definition 2.3.3: a class is `P`-measurable if every weighted finite
supremum display `(2.3.2)` is measurable on the completion of `P^n`.
-/
def VdVWPMeasurableClass
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    (P : Measure Observation) (indexClass : Set Index)
    (classFun : Index -> Observation -> ℝ) : Prop :=
  ∀ (n : ℕ) (weights : Fin n -> ℝ),
    NullMeasurable
      (fun sample : Fin n -> Observation =>
        vdVWWeightedClassSupremum indexClass classFun weights sample)
      (vdVWProductMeasure P n)

/-- Fixed-index weighted sample sums are measurable under coordinate measurability. -/
theorem measurable_vdVWWeightedSampleSum
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {classFun : Index -> Observation -> ℝ} {n : ℕ}
    (weights : Fin n -> ℝ) {index : Index}
    (hmeas : Measurable (classFun index)) :
    Measurable
      (fun sample : Fin n -> Observation =>
        vdVWWeightedSampleSum classFun weights index sample) := by
  unfold vdVWWeightedSampleSum
  exact Finset.measurable_fun_sum Finset.univ fun i _hi =>
    ((hmeas.comp (measurable_pi_apply i)).const_mul (weights i))

/-- Fixed-index absolute weighted sample sums are measurable. -/
theorem measurable_abs_vdVWWeightedSampleSum
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {classFun : Index -> Observation -> ℝ} {n : ℕ}
    (weights : Fin n -> ℝ) {index : Index}
    (hmeas : Measurable (classFun index)) :
    Measurable
      (fun sample : Fin n -> Observation =>
        |vdVWWeightedSampleSum classFun weights index sample|) := by
  exact continuous_abs.measurable.comp
    (measurable_vdVWWeightedSampleSum weights hmeas)

/--
Pointwise convergence of class functions implies convergence of every finite
weighted sample sum.
-/
theorem tendsto_vdVWWeightedSampleSum_of_pointwise
    {Observation : Type u} {Index : Type v}
    {classFun : Index -> Observation -> ℝ} {n : ℕ}
    (weights : Fin n -> ℝ) (sample : Fin n -> Observation)
    {approx : ℕ -> Index} {index : Index}
    (hlim :
      ∀ x : Observation,
        Tendsto (fun m => classFun (approx m) x) atTop
          (𝓝 (classFun index x))) :
    Tendsto
      (fun m => vdVWWeightedSampleSum classFun weights (approx m) sample)
      atTop
      (𝓝 (vdVWWeightedSampleSum classFun weights index sample)) := by
  simpa [vdVWWeightedSampleSum] using
    tendsto_finsetSum Finset.univ fun i _hi =>
      (hlim (sample i)).const_mul (weights i)

/-- Absolute-value version of `tendsto_vdVWWeightedSampleSum_of_pointwise`. -/
theorem tendsto_abs_vdVWWeightedSampleSum_of_pointwise
    {Observation : Type u} {Index : Type v}
    {classFun : Index -> Observation -> ℝ} {n : ℕ}
    (weights : Fin n -> ℝ) (sample : Fin n -> Observation)
    {approx : ℕ -> Index} {index : Index}
    (hlim :
      ∀ x : Observation,
        Tendsto (fun m => classFun (approx m) x) atTop
          (𝓝 (classFun index x))) :
    Tendsto
      (fun m => |vdVWWeightedSampleSum classFun weights (approx m) sample|)
      atTop
      (𝓝 |vdVWWeightedSampleSum classFun weights index sample|) :=
  continuous_abs.tendsto _ |>.comp
    (tendsto_vdVWWeightedSampleSum_of_pointwise weights sample hlim)

/--
The finite weighted term for a pointwise limit lies below the weighted
supremum over the approximating subclass.
-/
theorem abs_vdVWWeightedSampleSum_le_classSupremum_of_pointwise
    {Observation : Type u} {Index : Type v}
    {classFun : Index -> Observation -> ℝ} {n : ℕ}
    (weights : Fin n -> ℝ) (sample : Fin n -> Observation)
    {subclass : Set Index} {approx : ℕ -> Index} {index : Index}
    (hbounded :
      BddAbove
        (Set.range fun candidate : Index =>
          ⨆ (_ : candidate ∈ subclass),
            |vdVWWeightedSampleSum classFun weights candidate sample|))
    (hmem : ∀ m, approx m ∈ subclass)
    (hlim :
      ∀ x : Observation,
        Tendsto (fun m => classFun (approx m) x) atTop
          (𝓝 (classFun index x))) :
    |vdVWWeightedSampleSum classFun weights index sample| ≤
      vdVWWeightedClassSupremum subclass classFun weights sample := by
  apply le_of_tendsto'
    (tendsto_abs_vdVWWeightedSampleSum_of_pointwise weights sample hlim)
  intro m
  unfold vdVWWeightedClassSupremum
  refine le_ciSup_of_le hbounded (approx m) ?_
  simp [ciSup_pos (hmem m)]

/--
Weighted class suprema are monotone under class inclusion once the larger
class has a bounded inner-supremum range.
-/
theorem vdVWWeightedClassSupremum_le_of_subset_of_bddAbove
    {Observation : Type u} {Index : Type v}
    {smaller larger : Set Index} {classFun : Index -> Observation -> ℝ}
    (hsubset : smaller ⊆ larger)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation)
    (hbounded :
      BddAbove
        (Set.range fun candidate : Index =>
          ⨆ (_ : candidate ∈ larger),
            |vdVWWeightedSampleSum classFun weights candidate sample|)) :
    vdVWWeightedClassSupremum smaller classFun weights sample ≤
      vdVWWeightedClassSupremum larger classFun weights sample := by
  have hnonneg :
      0 ≤ vdVWWeightedClassSupremum larger classFun weights sample :=
    vdVWWeightedClassSupremum_nonneg larger classFun weights sample
  unfold vdVWWeightedClassSupremum
  apply Real.iSup_le
  · intro index
    apply Real.iSup_le
    · intro hsmall
      refine le_ciSup_of_le hbounded index ?_
      have hbddInner :
          BddAbove
            (Set.range fun _ : index ∈ larger =>
              |vdVWWeightedSampleSum classFun weights index sample|) := by
        exact ⟨|vdVWWeightedSampleSum classFun weights index sample|, by
          intro value hvalue
          rcases hvalue with ⟨_, rfl⟩
          rfl⟩
      exact le_ciSup_of_le hbddInner (hsubset hsmall) le_rfl
    · exact hnonneg
  · exact hnonneg

/--
A pointwise limit term is below every upper bound for the approximating
subclass value set.
-/
theorem abs_vdVWWeightedSampleSum_le_of_pointwise_of_valueSet_upperBound
    {Observation : Type u} {Index : Type v}
    {classFun : Index -> Observation -> ℝ} {n : ℕ}
    (weights : Fin n -> ℝ) (sample : Fin n -> Observation)
    {subclass : Set Index} {approx : ℕ -> Index} {index : Index}
    {upper : ℝ}
    (hupper :
      ∀ value ∈ vdVWWeightedClassValueSet subclass classFun weights sample,
        value ≤ upper)
    (hmem : ∀ m, approx m ∈ subclass)
    (hlim :
      ∀ x : Observation,
        Tendsto (fun m => classFun (approx m) x) atTop
          (𝓝 (classFun index x))) :
    |vdVWWeightedSampleSum classFun weights index sample| ≤ upper := by
  apply le_of_tendsto'
    (tendsto_abs_vdVWWeightedSampleSum_of_pointwise weights sample hlim)
  intro m
  exact hupper _
    (abs_vdVWWeightedSampleSum_mem_valueSet weights sample (hmem m))

/--
A countable coordinate-measurable class is `P`-measurable.

This is the Lean counterpart of the standard pointwise-measurable/countable
route used to discharge Definition 2.3.3 in concrete empirical-process
applications.
-/
theorem VdVWPMeasurableClass.of_countable_of_measurable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {P : Measure Observation} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (hcount : indexClass.Countable)
    (hmeas : VdVWClassCoordinateMeasurable indexClass classFun) :
    VdVWPMeasurableClass P indexClass classFun := by
  intro n weights
  exact
    (Measurable.biSup indexClass hcount fun index hindex =>
      measurable_abs_vdVWWeightedSampleSum weights (hmeas index hindex)
    ).nullMeasurable

/--
Countable coordinate-measurable classes are `P`-measurable after centering by
their population integrals.
-/
theorem VdVWPMeasurableClass.centered_of_countable_of_coordinate
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {P : Measure Observation} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (hcount : indexClass.Countable)
    (hclass : VdVWClassCoordinateMeasurable indexClass classFun) :
    VdVWPMeasurableClass P indexClass
      (fun index : Index => fun observation : Observation =>
        classFun index observation - ∫ x, classFun index x ∂P) :=
  VdVWPMeasurableClass.of_countable_of_measurable hcount
    (fun index hindex => (hclass index hindex).sub measurable_const)

/--
Proof-carrying form of the separability handoff used after VdV&W
Example 2.3.4.

The subclass is countable and gives the same weighted suprema `(2.3.2)` as
the original class.  The separate pointwise-dense hypothesis of the textbook
can be promoted to this equality in a later exact Example 2.3.4 theorem.
-/
structure VdVWPointwiseSupremumSeparable
    {Observation : Type u} {Index : Type v}
    (indexClass subclass : Set Index)
    (classFun : Index -> Observation -> ℝ) : Prop where
  subset : subclass ⊆ indexClass
  countable : subclass.Countable
  supremum_eq :
    ∀ (n : ℕ) (weights : Fin n -> ℝ)
      (sample : Fin n -> Observation),
      vdVWWeightedClassSupremum indexClass classFun weights sample =
        vdVWWeightedClassSupremum subclass classFun weights sample

/--
Literal pointwise-dense countable-subclass hypothesis from VdV&W
Example 2.3.4.

This is intentionally kept separate from `VdVWPointwiseSupremumSeparable`.
The hard analytic bridge still to promote is that this pointwise convergence
hypothesis preserves every finite weighted supremum `(2.3.2)`.
-/
structure VdVWPointwiseApproximableByCountableSubclass
    {Observation : Type u} {Index : Type v}
    (indexClass subclass : Set Index)
    (classFun : Index -> Observation -> ℝ) : Prop where
  subset : subclass ⊆ indexClass
  countable : subclass.Countable
  approximates :
    ∀ index, index ∈ indexClass ->
      ∃ approx : ℕ -> Index,
        (∀ m, approx m ∈ subclass) ∧
          ∀ x : Observation,
            Tendsto (fun m => classFun (approx m) x) atTop
              (𝓝 (classFun index x))

/--
Dominated-convergence handoff for one pointwise approximating sequence from a
uniformly bounded coordinate-measurable class.

This is the analytic ingredient needed to center separability statements:
pointwise convergence of uniformly bounded measurable coordinates also
converges after taking population integrals.
-/
theorem VdVWPointwiseApproximableByCountableSubclass.tendsto_integral_of_uniform_bound
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {P : Measure Observation} [IsFiniteMeasure P]
    {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    (hmeas : VdVWClassCoordinateMeasurable indexClass classFun)
    {bound : ℝ}
    (hbound :
      ∀ index, index ∈ indexClass -> ∀ observation,
        |classFun index observation| ≤ bound)
    {index : Index}
    {approx : ℕ -> Index}
    (hmem : ∀ m, approx m ∈ subclass)
    (hlim :
      ∀ observation : Observation,
        Tendsto (fun m => classFun (approx m) observation) atTop
          (𝓝 (classFun index observation))) :
    Tendsto (fun m => ∫ x, classFun (approx m) x ∂P) atTop
      (𝓝 (∫ x, classFun index x ∂P)) := by
  let boundFun : Observation -> ℝ := fun _ => max bound 0
  refine
    MeasureTheory.tendsto_integral_of_dominated_convergence
      (μ := P) (F := fun m x => classFun (approx m) x)
      (f := fun x => classFun index x) boundFun ?_ ?_ ?_ ?_
  · intro m
    exact (hmeas (approx m) (happrox.subset (hmem m))).aestronglyMeasurable
  · exact integrable_const (max bound 0)
  · intro m
    exact Filter.Eventually.of_forall fun x => by
      have hle : |classFun (approx m) x| ≤ bound :=
        hbound (approx m) (happrox.subset (hmem m)) x
      exact (by simpa [Real.norm_eq_abs, boundFun] using
        (hle.trans (le_max_left bound 0)))
  · exact Filter.Eventually.of_forall hlim

/--
Uniformly bounded pointwise approximability survives centering by population
integrals.

The proof uses the dominated-convergence handoff above to pass the pointwise
approximating sequence through `f ↦ ∫ f dP`.  This is the centered
separability primitive needed before turning bounded separability into
centered `P`-measurability.
-/
theorem VdVWPointwiseApproximableByCountableSubclass.centered_of_uniform_bound
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {P : Measure Observation} [IsFiniteMeasure P]
    {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    (hmeas : VdVWClassCoordinateMeasurable indexClass classFun)
    {bound : ℝ}
    (hbound :
      ∀ index, index ∈ indexClass -> ∀ observation,
        |classFun index observation| ≤ bound) :
    VdVWPointwiseApproximableByCountableSubclass indexClass subclass
      (fun index : Index => fun observation : Observation =>
        classFun index observation - ∫ x, classFun index x ∂P) where
  subset := happrox.subset
  countable := happrox.countable
  approximates := by
    intro index hindex
    rcases happrox.approximates index hindex with ⟨approx, hmem, hlim⟩
    refine ⟨approx, hmem, ?_⟩
    intro observation
    have hintegral :
        Tendsto (fun m => ∫ x, classFun (approx m) x ∂P) atTop
          (𝓝 (∫ x, classFun index x ∂P)) :=
      happrox.tendsto_integral_of_uniform_bound
        hmeas hbound hmem hlim
    exact (hlim observation).sub hintegral

/--
Pointwise approximability transfers boundedness of the weighted value set from
the countable subclass to the original class.
-/
theorem bddAbove_vdVWWeightedClassValueSet_of_pointwiseApproximable
    {Observation : Type u} {Index : Type v}
    {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation)
    (hbdd :
      BddAbove (vdVWWeightedClassValueSet subclass classFun weights sample)) :
    BddAbove (vdVWWeightedClassValueSet indexClass classFun weights sample) := by
  rcases hbdd with ⟨upper, hupper⟩
  refine ⟨upper, ?_⟩
  intro value hvalue
  rcases hvalue with ⟨index, hindex, rfl⟩
  rcases happrox.approximates index hindex with ⟨approx, hmem, hlim⟩
  exact
    abs_vdVWWeightedSampleSum_le_of_pointwise_of_valueSet_upperBound
      weights sample hupper hmem hlim

/--
Pointwise approximability gives the reverse supremum inequality whenever the
approximating subclass has a bounded inner-supremum range.
-/
theorem vdVWWeightedClassSupremum_le_of_pointwiseApproximable_of_bddAbove
    {Observation : Type u} {Index : Type v}
    {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation)
    (hbounded :
      BddAbove
        (Set.range fun candidate : Index =>
          ⨆ (_ : candidate ∈ subclass),
            |vdVWWeightedSampleSum classFun weights candidate sample|)) :
    vdVWWeightedClassSupremum indexClass classFun weights sample ≤
      vdVWWeightedClassSupremum subclass classFun weights sample := by
  have hnonneg :
      0 ≤ vdVWWeightedClassSupremum subclass classFun weights sample :=
    vdVWWeightedClassSupremum_nonneg subclass classFun weights sample
  unfold vdVWWeightedClassSupremum
  apply Real.iSup_le
  · intro index
    apply Real.iSup_le
    · intro hindex
      rcases happrox.approximates index hindex with ⟨approx, hmem, hlim⟩
      exact
        abs_vdVWWeightedSampleSum_le_classSupremum_of_pointwise
          weights sample hbounded hmem hlim
    · exact hnonneg
  · exact hnonneg

/--
Bounded pointwise approximability identifies one finite weighted supremum over
the original class with the supremum over the countable subclass.
-/
theorem vdVWWeightedClassSupremum_eq_of_pointwiseApproximable_of_bddAbove
    {Observation : Type u} {Index : Type v}
    {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    {n : ℕ} (weights : Fin n -> ℝ)
    (sample : Fin n -> Observation)
    (hbdd :
      BddAbove (vdVWWeightedClassValueSet subclass classFun weights sample)) :
    vdVWWeightedClassSupremum indexClass classFun weights sample =
      vdVWWeightedClassSupremum subclass classFun weights sample := by
  apply le_antisymm
  · have hboundedSubclass :
        BddAbove
          (Set.range fun candidate : Index =>
            ⨆ (_ : candidate ∈ subclass),
              |vdVWWeightedSampleSum classFun weights candidate sample|) :=
      bddAbove_vdVWWeightedClassSupremum_range_of_valueSet
        weights sample hbdd
    exact
      vdVWWeightedClassSupremum_le_of_pointwiseApproximable_of_bddAbove
        happrox weights sample hboundedSubclass
  · have hbddIndex :
        BddAbove
          (vdVWWeightedClassValueSet indexClass classFun weights sample) :=
      bddAbove_vdVWWeightedClassValueSet_of_pointwiseApproximable
        happrox weights sample hbdd
    have hboundedIndex :
        BddAbove
          (Set.range fun candidate : Index =>
            ⨆ (_ : candidate ∈ indexClass),
              |vdVWWeightedSampleSum classFun weights candidate sample|) :=
      bddAbove_vdVWWeightedClassSupremum_range_of_valueSet
        weights sample hbddIndex
    exact
      vdVWWeightedClassSupremum_le_of_subset_of_bddAbove
        happrox.subset weights sample hboundedIndex

/--
Bounded pointwise approximability is a proof-carrying route from the literal
Example 2.3.4 pointwise approximation hypothesis to equality of all finite
weighted suprema `(2.3.2)`.

The extra boundedness hypothesis is explicit because the current Lean
realization uses real-valued conditional suprema.
-/
theorem VdVWPointwiseApproximableByCountableSubclass.to_pointwiseSupremumSeparable_of_bddAbove
    {Observation : Type u} {Index : Type v}
    {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    (hbdd :
      ∀ (n : ℕ) (weights : Fin n -> ℝ)
        (sample : Fin n -> Observation),
        BddAbove (vdVWWeightedClassValueSet subclass classFun weights sample)) :
    VdVWPointwiseSupremumSeparable indexClass subclass classFun where
  subset := happrox.subset
  countable := happrox.countable
  supremum_eq := by
    intro n weights sample
    exact
      vdVWWeightedClassSupremum_eq_of_pointwiseApproximable_of_bddAbove
        happrox weights sample (hbdd n weights sample)

/--
If the weighted supremum over a class is realized by a countable measurable
subclass, then the original class is `P`-measurable.

This is the formal handoff behind the sentence after Example 2.3.4: once the
supremum over `F` equals the supremum over `G`, measurability follows from the
countable subclass.
-/
theorem VdVWPMeasurableClass.of_pointwiseSupremumSeparable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {P : Measure Observation} {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (hsep : VdVWPointwiseSupremumSeparable indexClass subclass classFun)
    (hmeas : VdVWClassCoordinateMeasurable subclass classFun) :
    VdVWPMeasurableClass P indexClass classFun := by
  intro n weights
  have hsub :
      NullMeasurable
        (fun sample : Fin n -> Observation =>
          vdVWWeightedClassSupremum subclass classFun weights sample)
        (vdVWProductMeasure P n) :=
    VdVWPMeasurableClass.of_countable_of_measurable
      hsep.countable hmeas n weights
  have hfun :
      (fun sample : Fin n -> Observation =>
        vdVWWeightedClassSupremum indexClass classFun weights sample) =
      (fun sample : Fin n -> Observation =>
        vdVWWeightedClassSupremum subclass classFun weights sample) :=
    funext fun sample => hsep.supremum_eq n weights sample
  simpa [hfun] using hsub

/--
Bounded pointwise approximability by a countable measurable subclass gives
`P`-measurability of the original class.

This is the direct theorem-facing handoff from the literal VdV&W
Example 2.3.4-style separability hypothesis to Definition 2.3.3.  The bounded
value-set assumption is kept explicit because the current real-valued supremum
formalization requires bounded conditional suprema.
-/
theorem VdVWPMeasurableClass.of_pointwiseApproximableByCountableSubclass_of_bddAbove
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {P : Measure Observation} {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    (hbdd :
      ∀ (n : ℕ) (weights : Fin n -> ℝ)
        (sample : Fin n -> Observation),
        BddAbove (vdVWWeightedClassValueSet subclass classFun weights sample))
    (hmeas : VdVWClassCoordinateMeasurable subclass classFun) :
    VdVWPMeasurableClass P indexClass classFun :=
  VdVWPMeasurableClass.of_pointwiseSupremumSeparable
    (happrox.to_pointwiseSupremumSeparable_of_bddAbove hbdd) hmeas

/--
Uniformly bounded pointwise approximability by a countable measurable subclass
gives `P`-measurability of the original class.

This discharges the bounded value-set side condition in
`VdVWPMeasurableClass.of_pointwiseApproximableByCountableSubclass_of_bddAbove`
from a global absolute bound on the approximating subclass.  It is the bounded
separable-class route to VdV&W Definition 2.3.3.
-/
theorem VdVWPMeasurableClass.of_pointwiseApproximableByCountableSubclass_of_uniform_bound
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {P : Measure Observation} {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    {bound : ℝ}
    (hbound :
      ∀ index, index ∈ subclass -> ∀ observation,
        |classFun index observation| ≤ bound)
    (hmeas : VdVWClassCoordinateMeasurable subclass classFun) :
    VdVWPMeasurableClass P indexClass classFun :=
    VdVWPMeasurableClass.of_pointwiseApproximableByCountableSubclass_of_bddAbove
    happrox
    (fun _n weights sample =>
      bddAbove_vdVWWeightedClassValueSet_of_uniform_bound
        (indexClass := subclass) (classFun := classFun) weights sample hbound)
    hmeas

/--
Uniformly bounded pointwise approximability by a countable measurable subclass
also gives `P`-measurability after centering by population integrals.

This is the centered version of
`VdVWPMeasurableClass.of_pointwiseApproximableByCountableSubclass_of_uniform_bound`.
The proof uses dominated convergence to show that the pointwise approximating
sequences remain approximating after subtracting their integrals, and the
finite-measure constant bound controls the centered subclass.
-/
theorem VdVWPMeasurableClass.centered_of_pointwiseApproximableByCountableSubclass_of_uniform_bound
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {P : Measure Observation} [IsFiniteMeasure P]
    {indexClass subclass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    (happrox :
      VdVWPointwiseApproximableByCountableSubclass
        indexClass subclass classFun)
    (hmeas : VdVWClassCoordinateMeasurable indexClass classFun)
    {bound : ℝ}
    (hbound :
      ∀ index, index ∈ indexClass -> ∀ observation,
        |classFun index observation| ≤ bound) :
    VdVWPMeasurableClass P indexClass
      (fun index : Index => fun observation : Observation =>
        classFun index observation - ∫ x, classFun index x ∂P) := by
  refine
    VdVWPMeasurableClass.of_pointwiseApproximableByCountableSubclass_of_uniform_bound
      (P := P)
      (classFun := fun index : Index => fun observation : Observation =>
        classFun index observation - ∫ x, classFun index x ∂P)
      (happrox.centered_of_uniform_bound hmeas hbound)
      (bound := max bound 0 + max bound 0 * P.real Set.univ) ?_ ?_
  · intro index hindex observation
    have hpoint :
        |classFun index observation| ≤ max bound 0 :=
      (hbound index (happrox.subset hindex) observation).trans
        (le_max_left bound 0)
    have hintegral :
        |∫ x, classFun index x ∂P| ≤ max bound 0 * P.real Set.univ := by
      simpa [Real.norm_eq_abs] using
        (norm_integral_le_of_norm_le_const
          (μ := P) (f := fun x : Observation => classFun index x)
          (C := max bound 0)
          (Filter.Eventually.of_forall fun x => by
            have hx :
                |classFun index x| ≤ max bound 0 :=
              (hbound index (happrox.subset hindex) x).trans
                (le_max_left bound 0)
            simpa [Real.norm_eq_abs] using hx))
    calc
      |classFun index observation - ∫ x, classFun index x ∂P|
          ≤ |classFun index observation| + |∫ x, classFun index x ∂P| := by
            simpa [sub_eq_add_neg, abs_neg] using
              (abs_add_le (classFun index observation)
                (-(∫ x, classFun index x ∂P)))
      _ ≤ max bound 0 + max bound 0 * P.real Set.univ :=
            add_le_add hpoint hintegral
  · intro index hindex
    exact (hmeas index (happrox.subset hindex)).sub measurable_const

end StatInference
