import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Integral.Lebesgue.Markov
import Mathlib.MeasureTheory.Measure.MeasureSpace
import Mathlib.MeasureTheory.Measure.Prod
import Mathlib.MeasureTheory.Measure.Typeclasses.Probability
import Mathlib.MeasureTheory.Constructions.BorelSpace.Real
import Mathlib.MeasureTheory.Order.Lattice

/-!
# VdV&W outer expectation and measurable-cover primitives

This module starts the Chapter 1.2 layer needed for the full textbook-order
empirical-process development.  It formalizes a nonnegative `ℝ≥0∞` version of
outer expectation and the proof-carrying minimal measurable cover interface.

The textbook states these notions for extended-real maps.  The nonnegative
version below is the part directly reusable for probabilities and nonnegative
empirical-process error functionals, while still using mathlib's Lebesgue
integral API as the verification authority.
-/

namespace StatInference

open MeasureTheory

open scoped ENNReal

universe u

/--
A measurable majorant of an arbitrary nonnegative map.

This is the family over which the VdV&W nonnegative outer expectation takes
the infimum: measurable `U` with `T <= U`.
-/
structure VdVWMeasurableMajorant {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (T : Ω -> ℝ≥0∞) where
  toFun : Ω -> ℝ≥0∞
  measurable_toFun : Measurable toFun
  majorizes : ∀ ω, T ω ≤ toFun ω

namespace VdVWMeasurableMajorant

instance {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} :
    CoeFun (VdVWMeasurableMajorant μ T) (fun _ => Ω -> ℝ≥0∞) where
  coe U := U.toFun

end VdVWMeasurableMajorant

/--
VdV&W nonnegative outer expectation.

For nonnegative maps, the ordinary expectation is mathlib's `lintegral`.
The outer expectation is the infimum of the integrals of measurable majorants.
-/
noncomputable def VdVWOuterExpectation {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (T : Ω -> ℝ≥0∞) : ℝ≥0∞ :=
  ⨅ U : VdVWMeasurableMajorant μ T, ∫⁻ ω, U ω ∂μ

/-- The outer expectation is bounded above by every measurable majorant. -/
theorem VdVWOuterExpectation_le_lintegral_majorant
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableMajorant μ T) :
    VdVWOuterExpectation μ T ≤ ∫⁻ ω, U ω ∂μ :=
  iInf_le (fun U : VdVWMeasurableMajorant μ T => ∫⁻ ω, U ω ∂μ) U

/--
For a measurable nonnegative map, VdV&W outer expectation reduces to the
ordinary mathlib Lebesgue integral.
-/
theorem VdVWOuterExpectation_eq_lintegral_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : Measurable T) :
    VdVWOuterExpectation μ T = ∫⁻ ω, T ω ∂μ := by
  refine le_antisymm ?upper ?lower
  · exact
      VdVWOuterExpectation_le_lintegral_majorant
        ({ toFun := T
           measurable_toFun := hT
           majorizes := fun _ => le_rfl } :
          VdVWMeasurableMajorant μ T)
  · dsimp [VdVWOuterExpectation]
    refine le_iInf ?_
    intro U
    exact lintegral_mono U.majorizes

/--
A measurable, integrable, nonnegative real map has finite VdV&W nonnegative
outer expectation after embedding into `ℝ≥0∞`.

This is the local bridge from an ordinary measurable/integrable envelope to the
textbook-style `P^* F < ∞` side condition used in Theorem 2.4.3.
-/
theorem VdVWOuterExpectation_ofReal_lt_top_of_measurable_integrable_nonneg
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {f : Ω -> ℝ} (hf_meas : Measurable f) (hf_int : Integrable f μ)
    (hf_nonneg : ∀ ω, 0 ≤ f ω) :
    VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (f ω)) < ∞ := by
  rw [VdVWOuterExpectation_eq_lintegral_of_measurable hf_meas.ennreal_ofReal]
  rw [← MeasureTheory.ofReal_integral_eq_lintegral_ofReal hf_int
    (ae_of_all μ hf_nonneg)]
  exact ENNReal.ofReal_lt_top

/--
For a measurable integrable real-valued map, the signed difference of the
VdV&W nonnegative outer expectations of its positive and negative parts is
the ordinary Bochner integral.
-/
theorem VdVWOuterExpectation_posPart_sub_negPart_eq_integral_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {f : Ω -> ℝ} (hf_meas : Measurable f) (hf_int : Integrable f μ) :
    ENNReal.toReal (VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (f ω))) -
        ENNReal.toReal (VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (-f ω))) =
      ∫ ω, f ω ∂μ := by
  rw [VdVWOuterExpectation_eq_lintegral_of_measurable hf_meas.ennreal_ofReal,
    VdVWOuterExpectation_eq_lintegral_of_measurable hf_meas.neg.ennreal_ofReal]
  exact (integral_eq_lintegral_pos_part_sub_lintegral_neg_part hf_int).symm

/-- VdV&W nonnegative outer expectation is monotone in the map. -/
theorem VdVWOuterExpectation_mono
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (hST : ∀ ω, S ω ≤ T ω) :
    VdVWOuterExpectation μ S ≤ VdVWOuterExpectation μ T := by
  dsimp [VdVWOuterExpectation]
  refine le_iInf ?_
  intro U
  let US : VdVWMeasurableMajorant μ S :=
    { toFun := U
      measurable_toFun := U.measurable_toFun
      majorizes := fun ω => le_trans (hST ω) (U.majorizes ω) }
  exact iInf_le_of_le US le_rfl

/--
A measurable minorant of an arbitrary nonnegative map.

This is the family over which the VdV&W nonnegative inner expectation takes
the supremum: measurable `L` with `L <= T`.
-/
structure VdVWMeasurableMinorant {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (T : Ω -> ℝ≥0∞) where
  toFun : Ω -> ℝ≥0∞
  measurable_toFun : Measurable toFun
  minorizes : ∀ ω, toFun ω ≤ T ω

namespace VdVWMeasurableMinorant

instance {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} :
    CoeFun (VdVWMeasurableMinorant μ T) (fun _ => Ω -> ℝ≥0∞) where
  coe L := L.toFun

end VdVWMeasurableMinorant

/--
VdV&W nonnegative inner expectation.

For nonnegative maps, this is the supremum of the integrals of measurable
minorants.  This is the nonnegative counterpart of `E_* T`.
-/
noncomputable def VdVWInnerExpectation {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (T : Ω -> ℝ≥0∞) : ℝ≥0∞ :=
  ⨆ L : VdVWMeasurableMinorant μ T, ∫⁻ ω, L ω ∂μ

/-- Every measurable minorant is bounded above by the inner expectation. -/
theorem lintegral_minorant_le_VdVWInnerExpectation
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (L : VdVWMeasurableMinorant μ T) :
    (∫⁻ ω, L ω ∂μ) ≤ VdVWInnerExpectation μ T :=
  le_iSup (fun L : VdVWMeasurableMinorant μ T => ∫⁻ ω, L ω ∂μ) L

/--
For a measurable nonnegative map, VdV&W inner expectation reduces to the
ordinary mathlib Lebesgue integral.
-/
theorem VdVWInnerExpectation_eq_lintegral_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : Measurable T) :
    VdVWInnerExpectation μ T = ∫⁻ ω, T ω ∂μ := by
  refine le_antisymm ?upper ?lower
  · dsimp [VdVWInnerExpectation]
    refine iSup_le ?_
    intro L
    exact lintegral_mono L.minorizes
  · exact
      lintegral_minorant_le_VdVWInnerExpectation
        ({ toFun := T
           measurable_toFun := hT
           minorizes := fun _ => le_rfl } :
          VdVWMeasurableMinorant μ T)

/--
For a measurable nonnegative map, the VdV&W nonnegative outer and inner
expectations coincide.

This is the local Chapter 1 bridge used before the full arbitrary-map
asymptotic-measurability layer: measurable test compositions have zero
outer/inner expectation gap.
-/
theorem VdVWOuterExpectation_eq_innerExpectation_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : Measurable T) :
    VdVWOuterExpectation μ T = VdVWInnerExpectation μ T := by
  rw [VdVWOuterExpectation_eq_lintegral_of_measurable hT,
    VdVWInnerExpectation_eq_lintegral_of_measurable hT]

/--
Measurable real-valued maps embedded as nonnegative `ENNReal.ofReal` maps have
equal VdV&W nonnegative outer and inner expectations.
-/
theorem VdVWOuterExpectation_eq_innerExpectation_of_measurable_ofReal
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {f : Ω -> ℝ} (hf : Measurable f) :
    VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (f ω)) =
      VdVWInnerExpectation μ (fun ω => ENNReal.ofReal (f ω)) :=
  VdVWOuterExpectation_eq_innerExpectation_of_measurable hf.ennreal_ofReal

/--
Composable form: if a map and a nonnegative test are measurable, then the
test-composed arbitrary-map expression has equal VdV&W outer and inner
expectations.
-/
theorem VdVWOuterExpectation_eq_innerExpectation_of_measurable_comp
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {X : Ω -> S} {T : S -> ℝ≥0∞}
    (hX : Measurable X) (hT : Measurable T) :
    VdVWOuterExpectation μ (fun ω => T (X ω)) =
      VdVWInnerExpectation μ (fun ω => T (X ω)) :=
  VdVWOuterExpectation_eq_innerExpectation_of_measurable (hT.comp hX)

/-- VdV&W nonnegative inner expectation is monotone in the map. -/
theorem VdVWInnerExpectation_mono
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (hST : ∀ ω, S ω ≤ T ω) :
    VdVWInnerExpectation μ S ≤ VdVWInnerExpectation μ T := by
  dsimp [VdVWInnerExpectation]
  refine iSup_le ?_
  intro L
  let LT : VdVWMeasurableMinorant μ T :=
    { toFun := L
      measurable_toFun := L.measurable_toFun
      minorizes := fun ω => le_trans (L.minorizes ω) (hST ω) }
  exact le_iSup_of_le LT le_rfl

/--
VdV&W nonnegative inner expectation is bounded above by nonnegative outer
expectation.

Every measurable minorant is pointwise below every measurable majorant, so the
supremum of minorant integrals is below the infimum of majorant integrals.
This is the basic order fact behind the local outer/inner expectation-gap
predicates.
-/
theorem VdVWInnerExpectation_le_outerExpectation
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} :
    VdVWInnerExpectation μ T ≤ VdVWOuterExpectation μ T := by
  dsimp [VdVWInnerExpectation, VdVWOuterExpectation]
  refine iSup_le ?_
  intro L
  refine le_iInf ?_
  intro U
  exact lintegral_mono fun ω => le_trans (L.minorizes ω) (U.majorizes ω)

/--
A proof-carrying nonnegative lower measurable cover, or maximal measurable
minorant.

The lower cover is pointwise below `T` and is almost surely above every
measurable minorant that is below `T` almost surely.
-/
structure VdVWMeasurableLowerCover {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (T : Ω -> ℝ≥0∞) where
  toFun : Ω -> ℝ≥0∞
  measurable_toFun : Measurable toFun
  minorizes : ∀ ω, toFun ω ≤ T ω
  maximal_ae :
    ∀ L : Ω -> ℝ≥0∞,
      Measurable L ->
      (∀ᵐ ω ∂μ, L ω ≤ T ω) ->
      ∀ᵐ ω ∂μ, L ω ≤ toFun ω

namespace VdVWMeasurableLowerCover

instance {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} :
    CoeFun (VdVWMeasurableLowerCover μ T) (fun _ => Ω -> ℝ≥0∞) where
  coe L := L.toFun

/-- A lower measurable cover is in particular a measurable minorant. -/
def toMinorant {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (L : VdVWMeasurableLowerCover μ T) :
    VdVWMeasurableMinorant μ T where
  toFun := L
  measurable_toFun := L.measurable_toFun
  minorizes := L.minorizes

/-- A measurable map is its own lower measurable cover. -/
def ofMeasurable {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    {T : Ω -> ℝ≥0∞} (hT : Measurable T) :
    VdVWMeasurableLowerCover μ T where
  toFun := T
  measurable_toFun := hT
  minorizes := fun _ => le_rfl
  maximal_ae := fun _ _ h_minorizes => h_minorizes

/--
An a.e.-measurable nonnegative map has a VdV&W lower measurable cover.

The measurable modification `hT.mk T` only agrees with `T` almost surely, so
the lower cover is set to `0` on a measurable hull of the disagreement set.
This keeps the cover pointwise below `T` while preserving the usual a.e.
maximality.
-/
noncomputable def ofAEMeasurable {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T μ) :
    VdVWMeasurableLowerCover μ T where
  toFun := by
    classical
    exact fun ω =>
      if ω ∈ toMeasurable μ {ω | T ω ≠ hT.mk T ω} then 0 else hT.mk T ω
  measurable_toFun := by
    classical
    exact
      Measurable.ite (measurableSet_toMeasurable μ {ω | T ω ≠ hT.mk T ω})
        measurable_const hT.measurable_mk
  minorizes := by
    classical
    intro ω
    by_cases hω : ω ∈ toMeasurable μ {ω | T ω ≠ hT.mk T ω}
    · simp [hω]
    · have hnot_bad : ω ∉ {ω | T ω ≠ hT.mk T ω} :=
        fun hbad => hω (subset_toMeasurable μ {ω | T ω ≠ hT.mk T ω} hbad)
      have heq : T ω = hT.mk T ω := by
        by_contra hne
        exact hnot_bad hne
      simp [hω, heq]
  maximal_ae := by
    classical
    intro L hL h_minorizes
    let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
    let hull : Set Ω := toMeasurable μ bad
    have hbad_zero : μ bad = 0 := by
      have h_eq : ∀ᵐ ω ∂μ, T ω = hT.mk T ω := hT.ae_eq_mk
      simpa [bad] using (ae_iff.mp h_eq)
    have hhull_zero : μ hull = 0 := by
      change μ (toMeasurable μ bad) = 0
      rw [measure_toMeasurable bad, hbad_zero]
    have hnot_hull_ae : ∀ᵐ ω ∂μ, ω ∉ hull := by
      apply ae_iff.mpr
      simpa using hhull_zero
    filter_upwards [h_minorizes, hnot_hull_ae] with ω hle hnot_hull
    have hnot_bad : ω ∉ bad :=
      fun hbad => hnot_hull (subset_toMeasurable μ bad hbad)
    have heq : T ω = hT.mk T ω := by
      by_contra hne
      exact hnot_bad hne
    change L ω ≤ (if ω ∈ hull then 0 else hT.mk T ω)
    simp [hnot_hull, ← heq, hle]

end VdVWMeasurableLowerCover

/--
If a nonnegative lower measurable cover is supplied, its integral realizes the
VdV&W inner expectation.
-/
theorem VdVWInnerExpectation_eq_lintegral_lowerCover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (L : VdVWMeasurableLowerCover μ T) :
    VdVWInnerExpectation μ T = ∫⁻ ω, L ω ∂μ := by
  refine le_antisymm ?upper ?lower
  · dsimp [VdVWInnerExpectation]
    refine iSup_le ?_
    intro V
    exact
      lintegral_mono_ae
        (L.maximal_ae V V.measurable_toFun (ae_of_all μ V.minorizes))
  · exact
      lintegral_minorant_le_VdVWInnerExpectation
        (VdVWMeasurableLowerCover.toMinorant L)

/-- The lower-cover theorem specializes to the measurable-map theorem. -/
theorem VdVWInnerExpectation_eq_lintegral_of_lowerCover_ofMeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : Measurable T) :
    VdVWInnerExpectation μ T =
      ∫⁻ ω,
        (VdVWMeasurableLowerCover.ofMeasurable μ hT : Ω -> ℝ≥0∞) ω ∂μ :=
  VdVWInnerExpectation_eq_lintegral_lowerCover
    (VdVWMeasurableLowerCover.ofMeasurable μ hT)

/--
A proof-carrying nonnegative measurable cover, or minimal measurable majorant.

The cover is pointwise above `T` and is almost surely below every measurable
majorant that is above `T` almost surely.  This matches the minimality clause
in VdV&W Lemma 1.2.1 while keeping the existence theorem separate.
-/
structure VdVWMeasurableCover {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (T : Ω -> ℝ≥0∞) where
  toFun : Ω -> ℝ≥0∞
  measurable_toFun : Measurable toFun
  majorizes : ∀ ω, T ω ≤ toFun ω
  minimal_ae :
    ∀ U : Ω -> ℝ≥0∞,
      Measurable U ->
      (∀ᵐ ω ∂μ, T ω ≤ U ω) ->
      ∀ᵐ ω ∂μ, toFun ω ≤ U ω

namespace VdVWMeasurableCover

instance {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} :
    CoeFun (VdVWMeasurableCover μ T) (fun _ => Ω -> ℝ≥0∞) where
  coe U := U.toFun

/-- A measurable cover is in particular a measurable majorant. -/
def toMajorant {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) :
    VdVWMeasurableMajorant μ T where
  toFun := U
  measurable_toFun := U.measurable_toFun
  majorizes := U.majorizes

/-- A measurable map is its own measurable cover. -/
def ofMeasurable {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    {T : Ω -> ℝ≥0∞} (hT : Measurable T) :
    VdVWMeasurableCover μ T where
  toFun := T
  measurable_toFun := hT
  majorizes := fun _ => le_rfl
  minimal_ae := fun _ _ h_majorizes => h_majorizes

/--
An a.e.-measurable nonnegative map has a VdV&W measurable cover.

The measurable modification `hT.mk T` only agrees with `T` almost surely, so
the cover is set to `∞` on a measurable hull of the disagreement set.  This
keeps the cover pointwise above `T` while preserving the usual a.e. minimality.
-/
noncomputable def ofAEMeasurable {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T μ) :
    VdVWMeasurableCover μ T where
  toFun := by
    classical
    exact fun ω =>
      if ω ∈ toMeasurable μ {ω | T ω ≠ hT.mk T ω} then ∞ else hT.mk T ω
  measurable_toFun := by
    classical
    exact
      Measurable.ite (measurableSet_toMeasurable μ {ω | T ω ≠ hT.mk T ω})
        measurable_const hT.measurable_mk
  majorizes := by
    classical
    intro ω
    by_cases hω : ω ∈ toMeasurable μ {ω | T ω ≠ hT.mk T ω}
    · simp [hω]
    · have hnot_bad : ω ∉ {ω | T ω ≠ hT.mk T ω} :=
        fun hbad => hω (subset_toMeasurable μ {ω | T ω ≠ hT.mk T ω} hbad)
      have heq : T ω = hT.mk T ω := by
        by_contra hne
        exact hnot_bad hne
      simp [hω, heq]
  minimal_ae := by
    classical
    intro U hU h_majorizes
    let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
    let hull : Set Ω := toMeasurable μ bad
    have hbad_zero : μ bad = 0 := by
      have h_eq : ∀ᵐ ω ∂μ, T ω = hT.mk T ω := hT.ae_eq_mk
      simpa [bad] using (ae_iff.mp h_eq)
    have hhull_zero : μ hull = 0 := by
      change μ (toMeasurable μ bad) = 0
      rw [measure_toMeasurable bad, hbad_zero]
    have hnot_hull_ae : ∀ᵐ ω ∂μ, ω ∉ hull := by
      apply ae_iff.mpr
      simpa using hhull_zero
    filter_upwards [h_majorizes, hnot_hull_ae] with ω hle hnot_hull
    have hnot_bad : ω ∉ bad :=
      fun hbad => hnot_hull (subset_toMeasurable μ bad hbad)
    have heq : T ω = hT.mk T ω := by
      by_contra hne
      exact hnot_bad hne
    change (if ω ∈ hull then ∞ else hT.mk T ω) ≤ U ω
    simp [hnot_hull, ← heq, hle]

/--
The cover built from an a.e.-measurable representative agrees with the target
almost surely.
-/
theorem ofAEMeasurable_ae_eq {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T μ) :
    (VdVWMeasurableCover.ofAEMeasurable μ hT : Ω -> ℝ≥0∞) =ᵐ[μ] T := by
  classical
  let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
  let hull : Set Ω := toMeasurable μ bad
  have hbad_zero : μ bad = 0 := by
    have h_eq : ∀ᵐ ω ∂μ, T ω = hT.mk T ω := hT.ae_eq_mk
    simpa [bad] using (ae_iff.mp h_eq)
  have hhull_zero : μ hull = 0 := by
    change μ (toMeasurable μ bad) = 0
    rw [measure_toMeasurable bad, hbad_zero]
  have hnot_hull_ae : ∀ᵐ ω ∂μ, ω ∉ hull := by
    apply ae_iff.mpr
    simpa using hhull_zero
  filter_upwards [hnot_hull_ae] with ω hnot_hull
  have hnot_bad : ω ∉ bad :=
    fun hbad => hnot_hull (subset_toMeasurable μ bad hbad)
  have heq : T ω = hT.mk T ω := by
    by_contra hne
    exact hnot_bad hne
  change (if ω ∈ hull then ∞ else hT.mk T ω) = T ω
  simp [hnot_hull, heq]

/--
Dominated-measure minimality of the a.e.-measurable cover built under a
dominating measure.

If `μ << ν`, then a cover built from a `ν`-a.e.-measurable representative is
minimal against every `μ`-a.e. measurable majorant.  This is the core
nonnegative common-cover primitive behind VdV&W Lemma 1.2.4.
-/
theorem ofAEMeasurable_minimal_ae_of_absolutelyContinuous
    {Ω : Type u} [MeasurableSpace Ω] {ν μ : Measure Ω}
    (hμν : μ ≪ ν) {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T ν)
    (U : Ω -> ℝ≥0∞) (_hU : Measurable U)
    (h_majorizes : ∀ᵐ ω ∂μ, T ω ≤ U ω) :
    ∀ᵐ ω ∂μ,
      (VdVWMeasurableCover.ofAEMeasurable ν hT : Ω -> ℝ≥0∞) ω ≤ U ω := by
  filter_upwards [hμν.ae_le (VdVWMeasurableCover.ofAEMeasurable_ae_eq ν hT),
    h_majorizes] with ω hcover_eq hle
  simpa [hcover_eq] using hle

/--
The a.e.-measurable cover built under a dominating measure is a valid
VdV&W measurable cover for every dominated measure.

This is a proof-carrying nonnegative version of the common measurable cover
assertion in VdV&W Lemma 1.2.4.
-/
noncomputable def ofAEMeasurableDominated {Ω : Type u} [MeasurableSpace Ω]
    (ν μ : Measure Ω) (hμν : μ ≪ ν)
    {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T ν) :
    VdVWMeasurableCover μ T where
  toFun := VdVWMeasurableCover.ofAEMeasurable ν hT
  measurable_toFun :=
    (VdVWMeasurableCover.ofAEMeasurable ν hT).measurable_toFun
  majorizes := (VdVWMeasurableCover.ofAEMeasurable ν hT).majorizes
  minimal_ae := by
    intro U hU h_majorizes
    exact
      VdVWMeasurableCover.ofAEMeasurable_minimal_ae_of_absolutelyContinuous
        hμν hT U hU h_majorizes

/--
Family-level common measurable cover for dominated measures.

If every measure in a family is absolutely continuous with respect to `ν` and
`T` is `ν`-a.e.-measurable, then the single cover built under `ν` is
simultaneously minimal for every measure in the family.  This is the
nonnegative a.e.-measurable version of VdV&W Lemma 1.2.4.
-/
theorem exists_common_measurableCover_of_forall_absolutelyContinuous_aemeasurable
    {Ω : Type u} [MeasurableSpace Ω] {ν : Measure Ω}
    {measures : Set (Measure Ω)} {T : Ω -> ℝ≥0∞}
    (hT : AEMeasurable T ν)
    (hdom : ∀ μ ∈ measures, μ ≪ ν) :
    ∃ U : Ω -> ℝ≥0∞,
      Measurable U ∧
        (∀ ω, T ω ≤ U ω) ∧
          ∀ μ ∈ measures, ∀ V : Ω -> ℝ≥0∞,
            Measurable V ->
            (∀ᵐ ω ∂μ, T ω ≤ V ω) ->
              ∀ᵐ ω ∂μ, U ω ≤ V ω := by
  refine ⟨VdVWMeasurableCover.ofAEMeasurable ν hT, ?_, ?_, ?_⟩
  · exact (VdVWMeasurableCover.ofAEMeasurable ν hT).measurable_toFun
  · exact (VdVWMeasurableCover.ofAEMeasurable ν hT).majorizes
  · intro μ hμ V hV h_majorizes
    exact
      VdVWMeasurableCover.ofAEMeasurable_minimal_ae_of_absolutelyContinuous
        (hdom μ hμ) hT V hV h_majorizes

/-- Real-valued null-measurable targets give covers after coercion to `ℝ≥0∞`. -/
noncomputable def ofNullMeasurable_ofReal {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) {f : Ω -> ℝ} (hf : NullMeasurable f μ) :
    VdVWMeasurableCover μ (fun ω => ENNReal.ofReal (f ω)) :=
  VdVWMeasurableCover.ofAEMeasurable μ hf.aemeasurable.ennreal_ofReal

/--
Supremum algebra for nonnegative measurable covers.

This is the nonnegative cover-interface counterpart of the VdV&W Lemma 1.2.2
identity `(S ∨ T)* = S* ∨ T*`.
-/
def sup {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWMeasurableCover μ (fun ω => S ω ⊔ T ω) where
  toFun := fun ω => US ω ⊔ UT ω
  measurable_toFun := US.measurable_toFun.sup UT.measurable_toFun
  majorizes := fun ω => sup_le_sup (US.majorizes ω) (UT.majorizes ω)
  minimal_ae := by
    intro U hU h_majorizes
    have hS : ∀ᵐ ω ∂μ, S ω ≤ U ω :=
      h_majorizes.mono fun _ hω => le_trans le_sup_left hω
    have hT : ∀ᵐ ω ∂μ, T ω ≤ U ω :=
      h_majorizes.mono fun _ hω => le_trans le_sup_right hω
    have hUS : ∀ᵐ ω ∂μ, US ω ≤ U ω :=
      US.minimal_ae U hU hS
    have hUT : ∀ᵐ ω ∂μ, UT ω ≤ U ω :=
      UT.minimal_ae U hU hT
    filter_upwards [hUS, hUT] with ω hUSω hUTω
    exact sup_le hUSω hUTω

/--
Additive majorant algebra for nonnegative measurable covers.

This is the nonnegative cover-interface version of the easy inequality in
VdV&W Lemma 1.2.2(i): `(S + T)* <= S* + T*`.
-/
def addMajorant {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWMeasurableMajorant μ (fun ω => S ω + T ω) where
  toFun := fun ω => US ω + UT ω
  measurable_toFun := US.measurable_toFun.add UT.measurable_toFun
  majorizes := fun ω => add_le_add (US.majorizes ω) (UT.majorizes ω)

/--
Addition by a constant preserves nonnegative measurable covers.

This is a proved equality case for the additive clause in VdV&W
Lemma 1.2.2(i): when one summand is the measurable constant `c`, the cover of
`c + T` is `c + T*`.  The proof splits off the `c = ∞` case and otherwise
uses mathlib's `ℝ≥0∞` subtraction API to test arbitrary measurable majorants
against `V - c`.
-/
def addConstLeft {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (c : ℝ≥0∞) (UT : VdVWMeasurableCover μ T) :
    VdVWMeasurableCover μ (fun ω => c + T ω) where
  toFun := fun ω => c + UT ω
  measurable_toFun := measurable_const.add UT.measurable_toFun
  majorizes := fun ω => add_le_add le_rfl (UT.majorizes ω)
  minimal_ae := by
    intro V hV h_majorizes
    by_cases hc_top : c = ∞
    · filter_upwards [h_majorizes] with ω hω
      simpa [hc_top] using hω
    · let W : Ω -> ℝ≥0∞ := fun ω => V ω - c
      have hW_meas : Measurable W :=
        (ENNReal.continuous_sub_right c).measurable.comp hV
      have hW_majorizes : ∀ᵐ ω ∂μ, T ω ≤ W ω := by
        filter_upwards [h_majorizes] with ω hω
        exact ENNReal.le_sub_of_add_le_left hc_top hω
      have hUT_le_W : ∀ᵐ ω ∂μ, UT ω ≤ W ω :=
        UT.minimal_ae W hW_meas hW_majorizes
      filter_upwards [h_majorizes, hUT_le_W] with ω h_majorizesω hUT_le_Wω
      have hc_le_V : c ≤ V ω := by
        exact le_trans le_self_add h_majorizesω
      exact (ENNReal.le_sub_iff_add_le_left hc_top hc_le_V).mp hUT_le_Wω

/--
Right addition by a constant preserves nonnegative measurable covers.

This is the symmetric constant case of the additive clause in VdV&W
Lemma 1.2.2(i), obtained from `addConstLeft` by commutativity.
-/
def addConstRight {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (UT : VdVWMeasurableCover μ T) (c : ℝ≥0∞) :
    VdVWMeasurableCover μ (fun ω => T ω + c) := by
  simpa [add_comm] using (VdVWMeasurableCover.addConstLeft c UT)

/--
Addition by a finite measurable nonnegative map preserves nonnegative
measurable covers on the left.

This is a guarded nonnegative version of the equality case in VdV&W
Lemma 1.2.2(i): if `S` is measurable and finite pointwise, then the cover of
`S + T` is `S + T*`.  The pointwise finiteness guard keeps `ℝ≥0∞`
subtraction well-defined in the proof.
-/
def addOfMeasurableLeft {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (hS : Measurable S) (hS_ne_top : ∀ ω, S ω ≠ ∞)
    (UT : VdVWMeasurableCover μ T) :
    VdVWMeasurableCover μ (fun ω => S ω + T ω) where
  toFun := fun ω => S ω + UT ω
  measurable_toFun := hS.add UT.measurable_toFun
  majorizes := fun ω => add_le_add le_rfl (UT.majorizes ω)
  minimal_ae := by
    intro V hV h_majorizes
    let W : Ω -> ℝ≥0∞ := fun ω => V ω - S ω
    have hW_meas : Measurable W :=
      measurable_sub.comp (hV.prodMk hS)
    have hW_majorizes : ∀ᵐ ω ∂μ, T ω ≤ W ω := by
      filter_upwards [h_majorizes] with ω hω
      exact ENNReal.le_sub_of_add_le_left (hS_ne_top ω) hω
    have hUT_le_W : ∀ᵐ ω ∂μ, UT ω ≤ W ω :=
      UT.minimal_ae W hW_meas hW_majorizes
    filter_upwards [h_majorizes, hUT_le_W] with ω h_majorizesω hUT_le_Wω
    have hS_le_V : S ω ≤ V ω := by
      exact le_trans le_self_add h_majorizesω
    exact (ENNReal.le_sub_iff_add_le_left (hS_ne_top ω) hS_le_V).mp hUT_le_Wω

/--
Addition by a finite measurable nonnegative map preserves nonnegative
measurable covers on the right.
-/
def addOfMeasurableRight {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (hT : Measurable T) (hT_ne_top : ∀ ω, T ω ≠ ∞) :
    VdVWMeasurableCover μ (fun ω => S ω + T ω) := by
  simpa [add_comm] using
    (VdVWMeasurableCover.addOfMeasurableLeft hT hT_ne_top US)

/--
Infimum majorant algebra for nonnegative measurable covers.

This is the nonnegative cover-interface version of the easy inequality in
VdV&W Lemma 1.2.2(ix): `(S ∧ T)* <= S* ∧ T*`.
-/
def infMajorant {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWMeasurableMajorant μ (fun ω => S ω ⊓ T ω) where
  toFun := fun ω => US ω ⊓ UT ω
  measurable_toFun := US.measurable_toFun.inf UT.measurable_toFun
  majorizes := fun ω => inf_le_inf (US.majorizes ω) (UT.majorizes ω)

/--
Infimum cover algebra when the left map is measurable.

This is the nonnegative counterpart of the equality clause in VdV&W
Lemma 1.2.2(ix): if `S` is measurable, then `(S ∧ T)* = S ∧ T*`.
-/
def infOfMeasurableLeft {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (hS : Measurable S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWMeasurableCover μ (fun ω => S ω ⊓ T ω) where
  toFun := fun ω => S ω ⊓ UT ω
  measurable_toFun := hS.inf UT.measurable_toFun
  majorizes := fun ω => inf_le_inf le_rfl (UT.majorizes ω)
  minimal_ae := by
    intro V hV h_majorizes
    let low : Set Ω := {ω | V ω < S ω}
    let W : Ω -> ℝ≥0∞ := low.piecewise V UT
    have hlow_meas : MeasurableSet low :=
      measurableSet_lt hV hS
    have hW_meas : Measurable W :=
      hV.piecewise hlow_meas UT.measurable_toFun
    have hW_majorizes : ∀ᵐ ω ∂μ, T ω ≤ W ω := by
      filter_upwards [h_majorizes] with ω hV_majorizes
      by_cases hlow : ω ∈ low
      · have hV_lt_S : V ω < S ω := hlow
        have hT_le_V : T ω ≤ V ω := by
          by_contra hnot
          have hV_lt_T : V ω < T ω := lt_of_not_ge hnot
          have hV_lt_inf : V ω < S ω ⊓ T ω :=
            lt_inf_iff.mpr ⟨hV_lt_S, hV_lt_T⟩
          exact not_lt_of_ge hV_majorizes hV_lt_inf
        simpa [W, low, hlow] using hT_le_V
      · have hT_le_UT : T ω ≤ UT ω := UT.majorizes ω
        simpa [W, low, hlow] using hT_le_UT
    have hUT_le_W : ∀ᵐ ω ∂μ, UT ω ≤ W ω :=
      UT.minimal_ae W hW_meas hW_majorizes
    filter_upwards [hUT_le_W] with ω hUT_le_Wω
    by_cases hlow : ω ∈ low
    · have hUT_le_V : UT ω ≤ V ω := by
        simpa [W, low, hlow] using hUT_le_Wω
      exact le_trans inf_le_right hUT_le_V
    · have hS_le_V : S ω ≤ V ω := not_lt.mp hlow
      exact le_trans inf_le_left hS_le_V

/--
Infimum cover algebra when the right map is measurable.

This is the symmetric nonnegative counterpart of the equality clause in
VdV&W Lemma 1.2.2(ix): if `T` is measurable, then `(S ∧ T)* = S* ∧ T`.
-/
def infOfMeasurableRight {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (hT : Measurable T) :
    VdVWMeasurableCover μ (fun ω => S ω ⊓ T ω) := by
  simpa [inf_comm] using (VdVWMeasurableCover.infOfMeasurableLeft hT US)

/--
Multiplicative majorant algebra for nonnegative measurable covers.

This is the nonnegative positive-sign skeleton behind the product clauses in
VdV&W Lemma 1.2.2(iv)-(v): if `S <= S*` and `T <= T*`, then
`S * T <= S* * T*`.
-/
noncomputable def mulMajorant {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWMeasurableMajorant μ (fun ω => S ω * T ω) where
  toFun := fun ω => US ω * UT ω
  measurable_toFun := US.measurable_toFun.mul UT.measurable_toFun
  majorizes := fun ω => mul_le_mul' (US.majorizes ω) (UT.majorizes ω)

/--
First-coordinate product-space cover transfer for measurable targets.

This is the proved measurable-target core of VdV&W Lemma 1.2.5: on a product
space, a minimal measurable cover depending only on the first coordinate
remains minimal after pulling it back by the first projection.
-/
def fstProductOfMeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) (hT : Measurable T) :
    VdVWMeasurableCover (μ.prod ν) (fun z : Ω × S => T z.1) where
  toFun := fun z => U z.1
  measurable_toFun := U.measurable_toFun.comp measurable_fst
  majorizes := fun z => U.majorizes z.1
  minimal_ae := by
    intro V hV h_majorizes
    have h_majorizes_set :
        MeasurableSet {z : Ω × S | T z.1 ≤ V z} :=
      measurableSet_le (hT.comp measurable_fst) hV
    have hxy : ∀ᵐ x ∂μ, ∀ᵐ y ∂ν, T x ≤ V (x, y) :=
      (Measure.ae_prod_iff_ae_ae h_majorizes_set).mp h_majorizes
    have hyx : ∀ᵐ y ∂ν, ∀ᵐ x ∂μ, T x ≤ V (x, y) :=
      (Measure.ae_ae_comm h_majorizes_set).mp hxy
    have hsections : ∀ᵐ y ∂ν, ∀ᵐ x ∂μ, U x ≤ V (x, y) := by
      filter_upwards [hyx] with y hy
      exact
        U.minimal_ae (fun x => V (x, y))
          (hV.comp (measurable_id.prodMk measurable_const)) hy
    have h_cover_set :
        MeasurableSet {z : Ω × S | U z.1 ≤ V z} :=
      measurableSet_le (U.measurable_toFun.comp measurable_fst) hV
    exact
      (Measure.ae_prod_iff_ae_ae h_cover_set).mpr
        ((Measure.ae_ae_comm h_cover_set).mpr hsections)

/--
Second-coordinate product-space cover transfer for measurable targets.

This is the symmetric measurable-target core of VdV&W Lemma 1.2.5 for the
second coordinate projection.
-/
def sndProductOfMeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    {T : S -> ℝ≥0∞} (U : VdVWMeasurableCover ν T) (hT : Measurable T) :
    VdVWMeasurableCover (μ.prod ν) (fun z : Ω × S => T z.2) where
  toFun := fun z => U z.2
  measurable_toFun := U.measurable_toFun.comp measurable_snd
  majorizes := fun z => U.majorizes z.2
  minimal_ae := by
    intro V hV h_majorizes
    have h_majorizes_set :
        MeasurableSet {z : Ω × S | T z.2 ≤ V z} :=
      measurableSet_le (hT.comp measurable_snd) hV
    have hxy : ∀ᵐ x ∂μ, ∀ᵐ y ∂ν, T y ≤ V (x, y) :=
      (Measure.ae_prod_iff_ae_ae h_majorizes_set).mp h_majorizes
    have hsections : ∀ᵐ x ∂μ, ∀ᵐ y ∂ν, U y ≤ V (x, y) := by
      filter_upwards [hxy] with x hx
      exact
        U.minimal_ae (fun y => V (x, y))
          (hV.comp (measurable_const.prodMk measurable_id)) hx
    have h_cover_set :
        MeasurableSet {z : Ω × S | U z.2 ≤ V z} :=
      measurableSet_le (U.measurable_toFun.comp measurable_snd) hV
    exact (Measure.ae_prod_iff_ae_ae h_cover_set).mpr hsections

end VdVWMeasurableCover

/--
A bounded extended-real measurable cover.

This is a proof-carrying primitive for later Chapter 1.2 work with arbitrary
`EReal`-valued maps.  It intentionally records only the reusable cover data:
the target and cover are bounded by the supplied endpoints, the cover is a
measurable pointwise majorant, and it is minimal among measurable a.e.
majorants.  Existence for arbitrary maps is kept separate.
-/
structure VdVWBoundedERealMeasurableCover {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (T : Ω -> EReal) (lower upper : ℝ) where
  toFun : Ω -> EReal
  measurable_toFun : Measurable toFun
  majorizes : ∀ ω, T ω ≤ toFun ω
  lower_le_target : ∀ ω, (lower : EReal) ≤ T ω
  target_le_upper : ∀ ω, T ω ≤ (upper : EReal)
  cover_le_upper : ∀ ω, toFun ω ≤ (upper : EReal)
  minimal_ae :
    ∀ U : Ω -> EReal,
      Measurable U ->
      (∀ᵐ ω ∂μ, T ω ≤ U ω) ->
      ∀ᵐ ω ∂μ, toFun ω ≤ U ω

namespace VdVWBoundedERealMeasurableCover

instance {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> EReal} {lower upper : ℝ} :
    CoeFun (VdVWBoundedERealMeasurableCover μ T lower upper)
      (fun _ => Ω -> EReal) where
  coe U := U.toFun

/-- The measurable cover inherits the recorded lower bound from the target. -/
theorem lower_le_cover {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> EReal} {lower upper : ℝ}
    (U : VdVWBoundedERealMeasurableCover μ T lower upper) (ω : Ω) :
    (lower : EReal) ≤ U ω :=
  le_trans (U.lower_le_target ω) (U.majorizes ω)

/-- A measurable bounded `EReal` map is its own bounded measurable cover. -/
def ofMeasurable {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    {T : Ω -> EReal} {lower upper : ℝ} (hT : Measurable T)
    (hlower : ∀ ω, (lower : EReal) ≤ T ω)
    (hupper : ∀ ω, T ω ≤ (upper : EReal)) :
    VdVWBoundedERealMeasurableCover μ T lower upper where
  toFun := T
  measurable_toFun := hT
  majorizes := fun _ => le_rfl
  lower_le_target := hlower
  target_le_upper := hupper
  cover_le_upper := hupper
  minimal_ae := fun _ _ h_majorizes => h_majorizes

/-- A bounded a.e.-measurable `EReal` map has a bounded measurable cover. -/
noncomputable def ofAEMeasurable {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) {T : Ω -> EReal} {lower upper : ℝ}
    (hT : AEMeasurable T μ) (hlower : ∀ ω, (lower : EReal) ≤ T ω)
    (hupper : ∀ ω, T ω ≤ (upper : EReal)) :
    VdVWBoundedERealMeasurableCover μ T lower upper where
  toFun := by
    classical
    exact fun ω =>
      if ω ∈ toMeasurable μ {ω | T ω ≠ hT.mk T ω} then
        (upper : EReal)
      else
        hT.mk T ω
  measurable_toFun := by
    classical
    exact
      Measurable.ite (measurableSet_toMeasurable μ {ω | T ω ≠ hT.mk T ω})
        measurable_const hT.measurable_mk
  majorizes := by
    classical
    intro ω
    let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
    let hull : Set Ω := toMeasurable μ bad
    by_cases hω : ω ∈ hull
    · change T ω ≤ (if ω ∈ hull then (upper : EReal) else hT.mk T ω)
      simpa [hω] using hupper ω
    · have hnot_bad : ω ∉ bad :=
        fun hbad => hω (subset_toMeasurable μ bad hbad)
      have heq : T ω = hT.mk T ω := by
        by_contra hne
        exact hnot_bad hne
      change T ω ≤ (if ω ∈ hull then (upper : EReal) else hT.mk T ω)
      simp [hω, heq]
  lower_le_target := hlower
  target_le_upper := hupper
  cover_le_upper := by
    classical
    intro ω
    let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
    let hull : Set Ω := toMeasurable μ bad
    by_cases hω : ω ∈ hull
    · change (if ω ∈ hull then (upper : EReal) else hT.mk T ω) ≤ (upper : EReal)
      simp [hω]
    · have hnot_bad : ω ∉ bad :=
        fun hbad => hω (subset_toMeasurable μ bad hbad)
      have heq : T ω = hT.mk T ω := by
        by_contra hne
        exact hnot_bad hne
      change (if ω ∈ hull then (upper : EReal) else hT.mk T ω) ≤ (upper : EReal)
      simpa [hω, ← heq] using hupper ω
  minimal_ae := by
    classical
    intro V _hV h_majorizes
    let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
    let hull : Set Ω := toMeasurable μ bad
    have hbad_zero : μ bad = 0 := by
      have h_eq : ∀ᵐ ω ∂μ, T ω = hT.mk T ω := hT.ae_eq_mk
      simpa [bad] using (ae_iff.mp h_eq)
    have hhull_zero : μ hull = 0 := by
      change μ (toMeasurable μ bad) = 0
      rw [measure_toMeasurable bad, hbad_zero]
    have hnot_hull_ae : ∀ᵐ ω ∂μ, ω ∉ hull := by
      apply ae_iff.mpr
      simpa using hhull_zero
    filter_upwards [h_majorizes, hnot_hull_ae] with ω hle hnot_hull
    have hnot_bad : ω ∉ bad :=
      fun hbad => hnot_hull (subset_toMeasurable μ bad hbad)
    have heq : T ω = hT.mk T ω := by
      by_contra hne
      exact hnot_bad hne
    change (if ω ∈ hull then (upper : EReal) else hT.mk T ω) ≤ V ω
    simpa [hnot_hull, ← heq] using hle

/-- The bounded `EReal` cover built from an a.e.-measurable representative is a.e. equal to the target. -/
theorem ofAEMeasurable_ae_eq {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) {T : Ω -> EReal} {lower upper : ℝ}
    (hT : AEMeasurable T μ) (hlower : ∀ ω, (lower : EReal) ≤ T ω)
    (hupper : ∀ ω, T ω ≤ (upper : EReal)) :
    (VdVWBoundedERealMeasurableCover.ofAEMeasurable μ hT hlower hupper :
        Ω -> EReal) =ᵐ[μ] T := by
  classical
  let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
  let hull : Set Ω := toMeasurable μ bad
  have hbad_zero : μ bad = 0 := by
    have h_eq : ∀ᵐ ω ∂μ, T ω = hT.mk T ω := hT.ae_eq_mk
    simpa [bad] using (ae_iff.mp h_eq)
  have hhull_zero : μ hull = 0 := by
    change μ (toMeasurable μ bad) = 0
    rw [measure_toMeasurable bad, hbad_zero]
  have hnot_hull_ae : ∀ᵐ ω ∂μ, ω ∉ hull := by
    apply ae_iff.mpr
    simpa using hhull_zero
  filter_upwards [hnot_hull_ae] with ω hnot_hull
  have hnot_bad : ω ∉ bad :=
    fun hbad => hnot_hull (subset_toMeasurable μ bad hbad)
  have heq : T ω = hT.mk T ω := by
    by_contra hne
    exact hnot_bad hne
  change (if ω ∈ hull then (upper : EReal) else hT.mk T ω) = T ω
  simp [hnot_hull, heq]

/--
Dominated-measure minimality of the bounded `EReal` cover built under a
dominating measure.
-/
theorem ofAEMeasurable_minimal_ae_of_absolutelyContinuous
    {Ω : Type u} [MeasurableSpace Ω] {ν μ : Measure Ω}
    (hμν : μ ≪ ν) {T : Ω -> EReal} {lower upper : ℝ}
    (hT : AEMeasurable T ν) (hlower : ∀ ω, (lower : EReal) ≤ T ω)
    (hupper : ∀ ω, T ω ≤ (upper : EReal))
    (V : Ω -> EReal) (_hV : Measurable V)
    (h_majorizes : ∀ᵐ ω ∂μ, T ω ≤ V ω) :
    ∀ᵐ ω ∂μ,
      (VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper :
        Ω -> EReal) ω ≤ V ω := by
  filter_upwards
    [hμν.ae_le
      (VdVWBoundedERealMeasurableCover.ofAEMeasurable_ae_eq ν hT hlower hupper),
      h_majorizes] with ω hcover_eq hle
  simpa [hcover_eq] using hle

/--
The bounded `EReal` cover built under a dominating measure is a valid cover for
every dominated measure.
-/
noncomputable def ofAEMeasurableDominated {Ω : Type u} [MeasurableSpace Ω]
    (ν μ : Measure Ω) (hμν : μ ≪ ν)
    {T : Ω -> EReal} {lower upper : ℝ}
    (hT : AEMeasurable T ν) (hlower : ∀ ω, (lower : EReal) ≤ T ω)
    (hupper : ∀ ω, T ω ≤ (upper : EReal)) :
    VdVWBoundedERealMeasurableCover μ T lower upper where
  toFun := VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper
  measurable_toFun :=
    (VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper).measurable_toFun
  majorizes :=
    (VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper).majorizes
  lower_le_target := hlower
  target_le_upper := hupper
  cover_le_upper :=
    (VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper).cover_le_upper
  minimal_ae := by
    intro V hV h_majorizes
    exact
      VdVWBoundedERealMeasurableCover.ofAEMeasurable_minimal_ae_of_absolutelyContinuous
        hμν hT hlower hupper V hV h_majorizes

/--
Family-level common bounded `EReal` measurable cover for measurable maps.

If a bounded extended-real map is measurable, then the map itself is a common
minimal measurable majorant for every measure in any family.  This is the
measurable-map part of the extended-real common-cover statement in VdV&W
Lemma 1.2.4.
-/
theorem exists_common_boundedERealMeasurableCover_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {measures : Set (Measure Ω)}
    {T : Ω -> EReal} {lower upper : ℝ} (hT : Measurable T)
    (hlower : ∀ ω, (lower : EReal) ≤ T ω)
    (hupper : ∀ ω, T ω ≤ (upper : EReal)) :
    ∃ U : Ω -> EReal,
      Measurable U ∧
        (∀ ω, T ω ≤ U ω) ∧
          (∀ ω, (lower : EReal) ≤ T ω) ∧
            (∀ ω, U ω ≤ (upper : EReal)) ∧
              ∀ μ ∈ measures, ∀ V : Ω -> EReal,
                Measurable V ->
                (∀ᵐ ω ∂μ, T ω ≤ V ω) ->
                  ∀ᵐ ω ∂μ, U ω ≤ V ω := by
  refine ⟨T, hT, ?_, hlower, hupper, ?_⟩
  · intro ω
    rfl
  · intro μ _hμ V _hV h_majorizes
    exact h_majorizes

/--
Family-level common bounded `EReal` cover for dominated a.e.-measurable maps.

If every measure in a family is absolutely continuous with respect to `ν` and
the bounded extended-real map is `ν`-a.e.-measurable, then the single cover
built under `ν` is simultaneously minimal for every measure in the family.
This is the dominated a.e.-measurable bounded-extended-real layer of VdV&W
Lemma 1.2.4.
-/
theorem exists_common_boundedERealMeasurableCover_of_forall_absolutelyContinuous_aemeasurable
    {Ω : Type u} [MeasurableSpace Ω] {ν : Measure Ω}
    {measures : Set (Measure Ω)} {T : Ω -> EReal} {lower upper : ℝ}
    (hT : AEMeasurable T ν)
    (hlower : ∀ ω, (lower : EReal) ≤ T ω)
    (hupper : ∀ ω, T ω ≤ (upper : EReal))
    (hdom : ∀ μ ∈ measures, μ ≪ ν) :
    ∃ U : Ω -> EReal,
      Measurable U ∧
        (∀ ω, T ω ≤ U ω) ∧
          (∀ ω, (lower : EReal) ≤ T ω) ∧
            (∀ ω, U ω ≤ (upper : EReal)) ∧
              ∀ μ ∈ measures, ∀ V : Ω -> EReal,
                Measurable V ->
                (∀ᵐ ω ∂μ, T ω ≤ V ω) ->
                  ∀ᵐ ω ∂μ, U ω ≤ V ω := by
  refine
    ⟨VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper,
      ?_, ?_, hlower, ?_, ?_⟩
  · exact
      (VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper).measurable_toFun
  · exact
      (VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper).majorizes
  · exact
      (VdVWBoundedERealMeasurableCover.ofAEMeasurable ν hT hlower hupper).cover_le_upper
  · intro μ hμ V hV h_majorizes
    exact
      VdVWBoundedERealMeasurableCover.ofAEMeasurable_minimal_ae_of_absolutelyContinuous
        (hdom μ hμ) hT hlower hupper V hV h_majorizes

/--
Nonnegative bounded `EReal` covers descend to the existing nonnegative
`ℝ≥0∞` measurable-cover interface.

This is the main bridge primitive: it transfers minimality through the
order-embedding of nonnegative `EReal` values into `ℝ≥0∞`, using mathlib's
`EReal.toENNReal` measurability API.
-/
noncomputable def toNonnegativeCover {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {T : Ω -> EReal} {upper : ℝ}
    (U : VdVWBoundedERealMeasurableCover μ T 0 upper) :
    VdVWMeasurableCover μ (fun ω => (T ω).toENNReal) where
  toFun := fun ω => (U ω).toENNReal
  measurable_toFun := U.measurable_toFun.ereal_toENNReal
  majorizes := fun ω => EReal.toENNReal_le_toENNReal (U.majorizes ω)
  minimal_ae := by
    intro V hV h_majorizes
    have h_majorizes_ereal : ∀ᵐ ω ∂μ, T ω ≤ (V ω : EReal) := by
      filter_upwards [h_majorizes] with ω hω
      have hcoe : ((T ω).toENNReal : EReal) ≤ (V ω : EReal) :=
        EReal.coe_ennreal_le_coe_ennreal_iff.mpr hω
      simpa [EReal.coe_toENNReal (U.lower_le_target ω)] using hcoe
    have hU_le_V : ∀ᵐ ω ∂μ, U ω ≤ (V ω : EReal) :=
      U.minimal_ae (fun ω => (V ω : EReal)) hV.coe_ereal_ennreal h_majorizes_ereal
    filter_upwards [hU_le_V] with ω hω
    have hU_nonneg : (0 : EReal) ≤ U ω :=
      le_trans (U.lower_le_target ω) (U.majorizes ω)
    have hcoe : ((U ω).toENNReal : EReal) ≤ (V ω : EReal) := by
      simpa [EReal.coe_toENNReal hU_nonneg] using hω
    exact EReal.coe_ennreal_le_coe_ennreal_iff.mp hcoe

end VdVWBoundedERealMeasurableCover

/--
If a nonnegative measurable cover is supplied, its integral realizes the
VdV&W outer expectation.

This is the nonnegative counterpart of the equality after Lemma 1.2.1:
`E* T = E T*` for a minimal measurable majorant `T*`.
-/
theorem VdVWOuterExpectation_eq_lintegral_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) :
    VdVWOuterExpectation μ T = ∫⁻ ω, U ω ∂μ := by
  refine le_antisymm ?upper ?lower
  · exact
      VdVWOuterExpectation_le_lintegral_majorant
        (VdVWMeasurableCover.toMajorant U)
  · dsimp [VdVWOuterExpectation]
    refine le_iInf ?_
    intro V
    exact
      lintegral_mono_ae
        (U.minimal_ae V V.measurable_toFun (ae_of_all μ V.majorizes))

/--
First-coordinate product-space outer expectation for measurable targets.

If the second product factor is a probability measure, adjoining it and then
ignoring it does not change the VdV&W nonnegative outer expectation.  This is
the expectation-level measurable-target core of the perfect-coordinate
projection statement in VdV&W Lemma 1.2.5.
-/
theorem VdVWOuterExpectation_prod_fst_eq_of_measurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure ν]
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) (hT : Measurable T) :
    VdVWOuterExpectation (μ.prod ν) (fun z : Ω × S => T z.1) =
      VdVWOuterExpectation μ T := by
  rw [VdVWOuterExpectation_eq_lintegral_cover
      (VdVWMeasurableCover.fstProductOfMeasurable U hT),
    VdVWOuterExpectation_eq_lintegral_cover U]
  change (∫⁻ z : Ω × S, U z.1 ∂μ.prod ν) = ∫⁻ ω, U ω ∂μ
  calc
    ∫⁻ z : Ω × S, U z.1 ∂μ.prod ν =
        ∫⁻ ω, ∫⁻ _s : S, U ω ∂ν ∂μ := by
      exact
        MeasureTheory.lintegral_prod (fun z : Ω × S => U z.1)
          (U.measurable_toFun.comp measurable_fst).aemeasurable
    _ = ∫⁻ ω, U ω ∂μ := by
      simp [lintegral_const]

/--
Second-coordinate product-space outer expectation for measurable targets.

If the first product factor is a probability measure, adjoining it and then
ignoring it does not change the VdV&W nonnegative outer expectation.
-/
theorem VdVWOuterExpectation_prod_snd_eq_of_measurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure μ]
    {T : S -> ℝ≥0∞} (U : VdVWMeasurableCover ν T) (hT : Measurable T) :
    VdVWOuterExpectation (μ.prod ν) (fun z : Ω × S => T z.2) =
      VdVWOuterExpectation ν T := by
  rw [VdVWOuterExpectation_eq_lintegral_cover
      (VdVWMeasurableCover.sndProductOfMeasurable U hT),
    VdVWOuterExpectation_eq_lintegral_cover U]
  change (∫⁻ z : Ω × S, U z.2 ∂μ.prod ν) = ∫⁻ s, U s ∂ν
  calc
    ∫⁻ z : Ω × S, U z.2 ∂μ.prod ν =
        ∫⁻ s, ∫⁻ _ω : Ω, U s ∂μ ∂ν := by
      exact
        MeasureTheory.lintegral_prod_symm (fun z : Ω × S => U z.2)
          (U.measurable_toFun.comp measurable_snd).aemeasurable
    _ = ∫⁻ s, U s ∂ν := by
      simp [lintegral_const]

/--
First-coordinate product-space inner expectation for measurable targets.
-/
theorem VdVWInnerExpectation_prod_fst_eq_of_measurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure ν]
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) (hT : Measurable T) :
    VdVWInnerExpectation (μ.prod ν) (fun z : Ω × S => T z.1) =
      VdVWInnerExpectation μ T := by
  have hprod :
      VdVWOuterExpectation (μ.prod ν) (fun z : Ω × S => T z.1) =
        VdVWInnerExpectation (μ.prod ν) (fun z : Ω × S => T z.1) := by
    simpa only [Function.comp_apply] using
      (VdVWOuterExpectation_eq_innerExpectation_of_measurable
        (hT.comp measurable_fst))
  have hbase :
      VdVWOuterExpectation μ T = VdVWInnerExpectation μ T :=
    VdVWOuterExpectation_eq_innerExpectation_of_measurable hT
  rw [← hprod, ← hbase]
  exact VdVWOuterExpectation_prod_fst_eq_of_measurable U hT

/--
Second-coordinate product-space inner expectation for measurable targets.
-/
theorem VdVWInnerExpectation_prod_snd_eq_of_measurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure μ]
    {T : S -> ℝ≥0∞} (U : VdVWMeasurableCover ν T) (hT : Measurable T) :
    VdVWInnerExpectation (μ.prod ν) (fun z : Ω × S => T z.2) =
      VdVWInnerExpectation ν T := by
  have hprod :
      VdVWOuterExpectation (μ.prod ν) (fun z : Ω × S => T z.2) =
        VdVWInnerExpectation (μ.prod ν) (fun z : Ω × S => T z.2) := by
    simpa only [Function.comp_apply] using
      (VdVWOuterExpectation_eq_innerExpectation_of_measurable
        (hT.comp measurable_snd))
  have hbase :
      VdVWOuterExpectation ν T = VdVWInnerExpectation ν T :=
    VdVWOuterExpectation_eq_innerExpectation_of_measurable hT
  rw [← hprod, ← hbase]
  exact VdVWOuterExpectation_prod_snd_eq_of_measurable U hT

/--
A.e.-measurable nonnegative maps have their VdV&W outer expectation equal to
the ordinary `lintegral`.

This is the null-measurable version of
`VdVWOuterExpectation_eq_lintegral_of_measurable`, using the canonical
measurable cover built from the mathlib a.e.-measurable representative.
-/
theorem VdVWOuterExpectation_eq_lintegral_of_aemeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T μ) :
    VdVWOuterExpectation μ T = ∫⁻ ω, T ω ∂μ := by
  classical
  let U : VdVWMeasurableCover μ T :=
    VdVWMeasurableCover.ofAEMeasurable μ hT
  have hU_ae : U =ᵐ[μ] hT.mk T := by
    let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
    let hull : Set Ω := toMeasurable μ bad
    have hbad_zero : μ bad = 0 := by
      have h_eq : ∀ᵐ ω ∂μ, T ω = hT.mk T ω := hT.ae_eq_mk
      simpa [bad] using (ae_iff.mp h_eq)
    have hhull_zero : μ hull = 0 := by
      change μ (toMeasurable μ bad) = 0
      rw [measure_toMeasurable bad, hbad_zero]
    have hnot_hull_ae : ∀ᵐ ω ∂μ, ω ∉ hull := by
      apply ae_iff.mpr
      simpa using hhull_zero
    filter_upwards [hnot_hull_ae] with ω hnot_hull
    change (if ω ∈ hull then ∞ else hT.mk T ω) = hT.mk T ω
    simp [hnot_hull]
  calc
    VdVWOuterExpectation μ T = ∫⁻ ω, U ω ∂μ :=
      VdVWOuterExpectation_eq_lintegral_cover U
    _ = ∫⁻ ω, hT.mk T ω ∂μ := lintegral_congr_ae hU_ae
    _ = ∫⁻ ω, T ω ∂μ := (lintegral_congr_ae hT.ae_eq_mk).symm

/--
First-coordinate product-space outer expectation for a.e.-measurable targets.

This is the null-measurable/a.e.-measurable analogue of
`VdVWOuterExpectation_prod_fst_eq_of_measurable`.  It gives the
expectation-level product-projection invariance used when the ignored product
coordinate is adjoined to an already null-measurable statistic.
-/
theorem VdVWOuterExpectation_prod_fst_eq_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure ν]
    {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T μ) :
    VdVWOuterExpectation (μ.prod ν) (fun z : Ω × S => T z.1) =
      VdVWOuterExpectation μ T := by
  rw [VdVWOuterExpectation_eq_lintegral_of_aemeasurable hT.comp_fst,
    VdVWOuterExpectation_eq_lintegral_of_aemeasurable hT]
  calc
    ∫⁻ z : Ω × S, T z.1 ∂μ.prod ν =
        ∫⁻ ω, ∫⁻ _s : S, T ω ∂ν ∂μ := by
      exact MeasureTheory.lintegral_prod (fun z : Ω × S => T z.1) hT.comp_fst
    _ = ∫⁻ ω, T ω ∂μ := by
      simp [lintegral_const]

/--
Second-coordinate product-space outer expectation for a.e.-measurable targets.
-/
theorem VdVWOuterExpectation_prod_snd_eq_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure μ]
    {T : S -> ℝ≥0∞} (hT : AEMeasurable T ν) :
    VdVWOuterExpectation (μ.prod ν) (fun z : Ω × S => T z.2) =
      VdVWOuterExpectation ν T := by
  rw [VdVWOuterExpectation_eq_lintegral_of_aemeasurable hT.comp_snd,
    VdVWOuterExpectation_eq_lintegral_of_aemeasurable hT]
  calc
    ∫⁻ z : Ω × S, T z.2 ∂μ.prod ν =
        ∫⁻ s, ∫⁻ _ω : Ω, T s ∂μ ∂ν := by
      exact MeasureTheory.lintegral_prod_symm (fun z : Ω × S => T z.2) hT.comp_snd
    _ = ∫⁻ s, T s ∂ν := by
      simp [lintegral_const]

/--
Product-space Tonelli bridge for VdV&W nonnegative outer expectation.

For an a.e.-measurable nonnegative integrand on a product space, the
product-measure outer expectation agrees with the iterated `lintegral`.  This
is the reusable Chapter 1.2 Fubini/Tonelli wrapper behind later product-space
outer-expectation arguments.
-/
theorem VdVWOuterExpectation_prod_eq_lintegral_lintegral_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite ν]
    {T : Ω × S -> ℝ≥0∞} (hT : AEMeasurable T (μ.prod ν)) :
    VdVWOuterExpectation (μ.prod ν) T =
      ∫⁻ ω, ∫⁻ s, T (ω, s) ∂ν ∂μ := by
  rw [VdVWOuterExpectation_eq_lintegral_of_aemeasurable hT]
  exact MeasureTheory.lintegral_prod T hT

/--
Measurable product-space Tonelli bridge for VdV&W nonnegative outer
expectation.
-/
theorem VdVWOuterExpectation_prod_eq_lintegral_lintegral_of_measurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite ν]
    {T : Ω × S -> ℝ≥0∞} (hT : Measurable T) :
    VdVWOuterExpectation (μ.prod ν) T =
      ∫⁻ ω, ∫⁻ s, T (ω, s) ∂ν ∂μ :=
  VdVWOuterExpectation_prod_eq_lintegral_lintegral_of_aemeasurable
    hT.aemeasurable

/--
Symmetric product-space Tonelli bridge for VdV&W nonnegative outer
expectation.
-/
theorem VdVWOuterExpectation_prod_eq_lintegral_lintegral_symm_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    {T : Ω × S -> ℝ≥0∞} (hT : AEMeasurable T (μ.prod ν)) :
    VdVWOuterExpectation (μ.prod ν) T =
      ∫⁻ s, ∫⁻ ω, T (ω, s) ∂μ ∂ν := by
  rw [VdVWOuterExpectation_eq_lintegral_of_aemeasurable hT]
  exact MeasureTheory.lintegral_prod_symm T hT

/--
Measurable symmetric product-space Tonelli bridge for VdV&W nonnegative outer
expectation.
-/
theorem VdVWOuterExpectation_prod_eq_lintegral_lintegral_symm_of_measurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    {T : Ω × S -> ℝ≥0∞} (hT : Measurable T) :
    VdVWOuterExpectation (μ.prod ν) T =
      ∫⁻ s, ∫⁻ ω, T (ω, s) ∂μ ∂ν :=
  VdVWOuterExpectation_prod_eq_lintegral_lintegral_symm_of_aemeasurable
    hT.aemeasurable

/--
A.e.-measurable nonnegative maps have equal VdV&W outer and inner
expectations.

This extends the measurable-map collapse to null-measurable real statistics
after coercion to `ℝ≥0∞`, using the upper and lower measurable covers built
from the same a.e.-measurable representative.
-/
theorem VdVWOuterExpectation_eq_innerExpectation_of_aemeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T μ) :
    VdVWOuterExpectation μ T = VdVWInnerExpectation μ T := by
  classical
  let U : VdVWMeasurableCover μ T :=
    VdVWMeasurableCover.ofAEMeasurable μ hT
  let L : VdVWMeasurableLowerCover μ T :=
    VdVWMeasurableLowerCover.ofAEMeasurable μ hT
  have hU_ae : U =ᵐ[μ] hT.mk T := by
    let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
    let hull : Set Ω := toMeasurable μ bad
    have hbad_zero : μ bad = 0 := by
      have h_eq : ∀ᵐ ω ∂μ, T ω = hT.mk T ω := hT.ae_eq_mk
      simpa [bad] using (ae_iff.mp h_eq)
    have hhull_zero : μ hull = 0 := by
      change μ (toMeasurable μ bad) = 0
      rw [measure_toMeasurable bad, hbad_zero]
    have hnot_hull_ae : ∀ᵐ ω ∂μ, ω ∉ hull := by
      apply ae_iff.mpr
      simpa using hhull_zero
    filter_upwards [hnot_hull_ae] with ω hnot_hull
    change (if ω ∈ hull then ∞ else hT.mk T ω) = hT.mk T ω
    simp [hnot_hull]
  have hL_ae : L =ᵐ[μ] hT.mk T := by
    let bad : Set Ω := {ω | T ω ≠ hT.mk T ω}
    let hull : Set Ω := toMeasurable μ bad
    have hbad_zero : μ bad = 0 := by
      have h_eq : ∀ᵐ ω ∂μ, T ω = hT.mk T ω := hT.ae_eq_mk
      simpa [bad] using (ae_iff.mp h_eq)
    have hhull_zero : μ hull = 0 := by
      change μ (toMeasurable μ bad) = 0
      rw [measure_toMeasurable bad, hbad_zero]
    have hnot_hull_ae : ∀ᵐ ω ∂μ, ω ∉ hull := by
      apply ae_iff.mpr
      simpa using hhull_zero
    filter_upwards [hnot_hull_ae] with ω hnot_hull
    change (if ω ∈ hull then 0 else hT.mk T ω) = hT.mk T ω
    simp [hnot_hull]
  calc
    VdVWOuterExpectation μ T = ∫⁻ ω, U ω ∂μ :=
      VdVWOuterExpectation_eq_lintegral_cover U
    _ = ∫⁻ ω, hT.mk T ω ∂μ := lintegral_congr_ae hU_ae
    _ = ∫⁻ ω, L ω ∂μ := (lintegral_congr_ae hL_ae).symm
    _ = VdVWInnerExpectation μ T :=
      (VdVWInnerExpectation_eq_lintegral_lowerCover L).symm

/--
First-coordinate product-space inner expectation for a.e.-measurable targets.
-/
theorem VdVWInnerExpectation_prod_fst_eq_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure ν]
    {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T μ) :
    VdVWInnerExpectation (μ.prod ν) (fun z : Ω × S => T z.1) =
      VdVWInnerExpectation μ T := by
  have hprod :
      VdVWOuterExpectation (μ.prod ν) (fun z : Ω × S => T z.1) =
        VdVWInnerExpectation (μ.prod ν) (fun z : Ω × S => T z.1) := by
    simpa only [Function.comp_apply] using
      (VdVWOuterExpectation_eq_innerExpectation_of_aemeasurable hT.comp_fst)
  have hbase :
      VdVWOuterExpectation μ T = VdVWInnerExpectation μ T :=
    VdVWOuterExpectation_eq_innerExpectation_of_aemeasurable hT
  rw [← hprod, ← hbase]
  exact VdVWOuterExpectation_prod_fst_eq_of_aemeasurable hT

/--
Second-coordinate product-space inner expectation for a.e.-measurable targets.
-/
theorem VdVWInnerExpectation_prod_snd_eq_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure μ]
    {T : S -> ℝ≥0∞} (hT : AEMeasurable T ν) :
    VdVWInnerExpectation (μ.prod ν) (fun z : Ω × S => T z.2) =
      VdVWInnerExpectation ν T := by
  have hprod :
      VdVWOuterExpectation (μ.prod ν) (fun z : Ω × S => T z.2) =
        VdVWInnerExpectation (μ.prod ν) (fun z : Ω × S => T z.2) := by
    simpa only [Function.comp_apply] using
      (VdVWOuterExpectation_eq_innerExpectation_of_aemeasurable hT.comp_snd)
  have hbase :
      VdVWOuterExpectation ν T = VdVWInnerExpectation ν T :=
    VdVWOuterExpectation_eq_innerExpectation_of_aemeasurable hT
  rw [← hprod, ← hbase]
  exact VdVWOuterExpectation_prod_snd_eq_of_aemeasurable hT

/--
For an a.e.-measurable integrable real map, the signed positive/negative
VdV&W outer expectation agrees with the ordinary Bochner integral.
-/
theorem VdVWOuterExpectation_posPart_sub_negPart_eq_integral_of_aemeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {f : Ω -> ℝ} (hf_aemeas : AEMeasurable f μ) (hf_int : Integrable f μ) :
    ENNReal.toReal (VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (f ω))) -
        ENNReal.toReal (VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (-f ω))) =
      ∫ ω, f ω ∂μ := by
  rw [VdVWOuterExpectation_eq_lintegral_of_aemeasurable hf_aemeas.ennreal_ofReal,
    VdVWOuterExpectation_eq_lintegral_of_aemeasurable hf_aemeas.neg.ennreal_ofReal]
  exact (integral_eq_lintegral_pos_part_sub_lintegral_neg_part hf_int).symm

/-- The cover theorem specializes to the measurable-map theorem. -/
theorem VdVWOuterExpectation_eq_lintegral_of_cover_ofMeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : Measurable T) :
    VdVWOuterExpectation μ T =
      ∫⁻ ω, (VdVWMeasurableCover.ofMeasurable μ hT : Ω -> ℝ≥0∞) ω ∂μ :=
  VdVWOuterExpectation_eq_lintegral_cover
    (VdVWMeasurableCover.ofMeasurable μ hT)

/--
If a real-valued nonnegative target has a measurable cover and is almost
surely bounded by a constant, its VdV&W outer expectation is bounded by that
constant under a probability measure.
-/
theorem VdVWOuterExpectation_le_of_cover_ae_le_const_ofReal
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {f : Ω -> ℝ} {C : ℝ}
    (U : VdVWMeasurableCover μ (fun ω => ENNReal.ofReal (f ω)))
    (hbound : ∀ᵐ ω ∂μ, f ω ≤ C) :
    VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (f ω)) ≤
      ENNReal.ofReal C := by
  rw [VdVWOuterExpectation_eq_lintegral_cover U]
  have hcover_le :
      ∀ᵐ ω ∂μ, U ω ≤ ENNReal.ofReal C :=
    U.minimal_ae (fun _ : Ω => ENNReal.ofReal C) measurable_const
      (hbound.mono fun _ hω => ENNReal.ofReal_le_ofReal hω)
  calc
    ∫⁻ ω, U ω ∂μ ≤ ∫⁻ _ω : Ω, ENNReal.ofReal C ∂μ := by
      exact lintegral_mono_ae hcover_le
    _ = ENNReal.ofReal C := by
      simp [lintegral_const]

/--
For an integrable nonnegative real-valued target, a supplied VdV&W measurable
cover realizes the ordinary expectation.

This is the expectation-level bridge needed when a theorem first proves an
ordinary integral inequality and only later packages the right-hand side as a
nonnegative VdV&W outer expectation.
-/
theorem VdVWOuterExpectation_eq_ofReal_integral_of_cover_integrable_nonneg
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {f : Ω -> ℝ}
    (U : VdVWMeasurableCover μ (fun ω => ENNReal.ofReal (f ω)))
    (hf_int : Integrable f μ) (hf_nonneg : ∀ᵐ ω ∂μ, 0 ≤ f ω) :
    VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (f ω)) =
      ENNReal.ofReal (∫ ω, f ω ∂μ) := by
  rw [VdVWOuterExpectation_eq_lintegral_cover U]
  have htarget_eq :
      (∫⁻ ω, ENNReal.ofReal (f ω) ∂μ) =
        ENNReal.ofReal (∫ ω, f ω ∂μ) := by
    exact (MeasureTheory.ofReal_integral_eq_lintegral_ofReal hf_int hf_nonneg).symm
  refine le_antisymm ?upper ?lower
  · have hmk_majorizes :
        ∀ᵐ ω ∂μ,
          ENNReal.ofReal (f ω) ≤
            ENNReal.ofReal (hf_int.aestronglyMeasurable.mk f ω) := by
      filter_upwards [hf_int.aestronglyMeasurable.ae_eq_mk] with ω hω
      rw [hω]
    have hU_le_mk :
        ∀ᵐ ω ∂μ,
          U ω ≤ ENNReal.ofReal (hf_int.aestronglyMeasurable.mk f ω) :=
      U.minimal_ae
        (fun ω => ENNReal.ofReal (hf_int.aestronglyMeasurable.mk f ω))
        (hf_int.aestronglyMeasurable.stronglyMeasurable_mk.measurable.ennreal_ofReal)
        hmk_majorizes
    calc
      ∫⁻ ω, U ω ∂μ
          ≤ ∫⁻ ω, ENNReal.ofReal (hf_int.aestronglyMeasurable.mk f ω) ∂μ :=
            lintegral_mono_ae hU_le_mk
      _ = ∫⁻ ω, ENNReal.ofReal (f ω) ∂μ := by
            refine lintegral_congr_ae ?_
            filter_upwards [hf_int.aestronglyMeasurable.ae_eq_mk] with ω hω
            rw [hω]
      _ = ENNReal.ofReal (∫ ω, f ω ∂μ) := htarget_eq
  · calc
      ENNReal.ofReal (∫ ω, f ω ∂μ)
          = ∫⁻ ω, ENNReal.ofReal (f ω) ∂μ := htarget_eq.symm
      _ ≤ ∫⁻ ω, U ω ∂μ := lintegral_mono U.majorizes

/--
The supremum cover realizes the nonnegative outer expectation of a pointwise
supremum.
-/
theorem VdVWOuterExpectation_eq_lintegral_sup_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWOuterExpectation μ (fun ω => S ω ⊔ T ω) =
      ∫⁻ ω, US ω ⊔ UT ω ∂μ :=
  VdVWOuterExpectation_eq_lintegral_cover
    (VdVWMeasurableCover.sup US UT)

/--
The additive cover majorant bounds the nonnegative outer expectation of a
pointwise sum.
-/
theorem VdVWOuterExpectation_le_lintegral_add_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWOuterExpectation μ (fun ω => S ω + T ω) ≤
      ∫⁻ ω, US ω + UT ω ∂μ :=
  VdVWOuterExpectation_le_lintegral_majorant
    (VdVWMeasurableCover.addMajorant US UT)

/--
The constant-left addition cover realizes the nonnegative outer expectation
of `c + T`.
-/
theorem VdVWOuterExpectation_eq_lintegral_const_add_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (c : ℝ≥0∞) (UT : VdVWMeasurableCover μ T) :
    VdVWOuterExpectation μ (fun ω => c + T ω) =
      ∫⁻ ω, c + UT ω ∂μ :=
  VdVWOuterExpectation_eq_lintegral_cover
    (VdVWMeasurableCover.addConstLeft c UT)

/--
The constant-right addition cover realizes the nonnegative outer expectation
of `T + c`.
-/
theorem VdVWOuterExpectation_eq_lintegral_add_const_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (UT : VdVWMeasurableCover μ T) (c : ℝ≥0∞) :
    VdVWOuterExpectation μ (fun ω => T ω + c) =
      ∫⁻ ω, UT ω + c ∂μ := by
  simpa [add_comm] using
    (VdVWOuterExpectation_eq_lintegral_const_add_cover c UT)

/--
The finite-measurable-left addition cover realizes the nonnegative outer
expectation of `S + T`.
-/
theorem VdVWOuterExpectation_eq_lintegral_add_cover_of_left_measurable_finite
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (hS : Measurable S) (hS_ne_top : ∀ ω, S ω ≠ ∞)
    (UT : VdVWMeasurableCover μ T) :
    VdVWOuterExpectation μ (fun ω => S ω + T ω) =
      ∫⁻ ω, S ω + UT ω ∂μ :=
  VdVWOuterExpectation_eq_lintegral_cover
    (VdVWMeasurableCover.addOfMeasurableLeft hS hS_ne_top UT)

/--
The finite-measurable-right addition cover realizes the nonnegative outer
expectation of `S + T`.
-/
theorem VdVWOuterExpectation_eq_lintegral_add_cover_of_right_measurable_finite
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (hT : Measurable T) (hT_ne_top : ∀ ω, T ω ≠ ∞) :
    VdVWOuterExpectation μ (fun ω => S ω + T ω) =
      ∫⁻ ω, US ω + T ω ∂μ := by
  simpa [add_comm] using
    (VdVWOuterExpectation_eq_lintegral_add_cover_of_left_measurable_finite
      hT hT_ne_top US)

/--
The infimum cover majorant bounds the nonnegative outer expectation of a
pointwise infimum.
-/
theorem VdVWOuterExpectation_le_lintegral_inf_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWOuterExpectation μ (fun ω => S ω ⊓ T ω) ≤
      ∫⁻ ω, US ω ⊓ UT ω ∂μ :=
  VdVWOuterExpectation_le_lintegral_majorant
    (VdVWMeasurableCover.infMajorant US UT)

/--
If the left map is measurable, the pointwise infimum with the cover of the
right map realizes the nonnegative outer expectation.
-/
theorem VdVWOuterExpectation_eq_lintegral_inf_cover_of_left_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (hS : Measurable S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWOuterExpectation μ (fun ω => S ω ⊓ T ω) =
      ∫⁻ ω, S ω ⊓ UT ω ∂μ :=
  VdVWOuterExpectation_eq_lintegral_cover
    (VdVWMeasurableCover.infOfMeasurableLeft hS UT)

/--
If the right map is measurable, the pointwise infimum with the cover of the
left map realizes the nonnegative outer expectation.
-/
theorem VdVWOuterExpectation_eq_lintegral_inf_cover_of_right_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (hT : Measurable T) :
    VdVWOuterExpectation μ (fun ω => S ω ⊓ T ω) =
      ∫⁻ ω, US ω ⊓ T ω ∂μ := by
  simpa [inf_comm] using
    (VdVWOuterExpectation_eq_lintegral_inf_cover_of_left_measurable hT US)

/--
The product cover majorant bounds the nonnegative outer expectation of a
pointwise product.
-/
theorem VdVWOuterExpectation_le_lintegral_mul_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {S T : Ω -> ℝ≥0∞} (US : VdVWMeasurableCover μ S)
    (UT : VdVWMeasurableCover μ T) :
    VdVWOuterExpectation μ (fun ω => S ω * T ω) ≤
      ∫⁻ ω, US ω * UT ω ∂μ :=
  VdVWOuterExpectation_le_lintegral_majorant
    (VdVWMeasurableCover.mulMajorant US UT)

/-- Nonnegative indicator of an arbitrary event. -/
noncomputable def VdVWEventIndicator {Ω : Type u} (event : Set Ω) : Ω -> ℝ≥0∞ :=
  event.indicator fun _ => 1

/-- Event indicators are monotone under set inclusion. -/
theorem VdVWEventIndicator_mono
    {Ω : Type u} {event₁ event₂ : Set Ω} (hsubset : event₁ ⊆ event₂) :
    VdVWEventIndicator event₁ ≤ VdVWEventIndicator event₂ := by
  intro ω
  by_cases hω₁ : ω ∈ event₁
  · have hω₂ : ω ∈ event₂ := hsubset hω₁
    simp [VdVWEventIndicator, hω₁, hω₂]
  · by_cases hω₂ : ω ∈ event₂
    · simp [VdVWEventIndicator, hω₁, hω₂]
    · simp [VdVWEventIndicator, hω₁, hω₂]

/-- Outer expectations of event indicators are monotone under set inclusion. -/
theorem VdVWOuterExpectation_eventIndicator_mono
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {event₁ event₂ : Set Ω} (hsubset : event₁ ⊆ event₂) :
    VdVWOuterExpectation μ (VdVWEventIndicator event₁) ≤
      VdVWOuterExpectation μ (VdVWEventIndicator event₂) :=
  VdVWOuterExpectation_mono (VdVWEventIndicator_mono hsubset)

/-- Inner expectations of event indicators are monotone under set inclusion. -/
theorem VdVWInnerExpectation_eventIndicator_mono
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {event₁ event₂ : Set Ω} (hsubset : event₁ ⊆ event₂) :
    VdVWInnerExpectation μ (VdVWEventIndicator event₁) ≤
      VdVWInnerExpectation μ (VdVWEventIndicator event₂) :=
  VdVWInnerExpectation_mono (VdVWEventIndicator_mono hsubset)

namespace VdVWMeasurableCover

/--
Threshold-indicator cover algebra for nonnegative measurable covers.

This is the nonnegative counterpart of VdV&W Lemma 1.2.2(vi):
`(1_{T > c})* = 1_{T* > c}`.  The threshold event uses `c < T` because
the maps here take values in `ℝ≥0∞`.
-/
noncomputable def thresholdIndicatorCover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) (c : ℝ≥0∞) :
    VdVWMeasurableCover μ (VdVWEventIndicator {ω | c < T ω}) where
  toFun := VdVWEventIndicator {ω | c < U ω}
  measurable_toFun :=
    measurable_const.indicator (measurableSet_lt measurable_const U.measurable_toFun)
  majorizes := by
    intro ω
    by_cases hT : c < T ω
    · have hU : c < U ω := lt_of_lt_of_le hT (U.majorizes ω)
      simp [VdVWEventIndicator, hT, hU]
    · simp [VdVWEventIndicator, hT]
  minimal_ae := by
    classical
    intro V hV h_majorizes
    let low : Set Ω := {ω | V ω < 1}
    let W : Ω -> ℝ≥0∞ := low.piecewise (fun ω => U ω ⊓ c) (fun ω => U ω)
    have hlow_meas : MeasurableSet low :=
      measurableSet_lt hV measurable_const
    have hW_meas : Measurable W := by
      exact (U.measurable_toFun.inf measurable_const).piecewise hlow_meas U.measurable_toFun
    have hW_majorizes : ∀ᵐ ω ∂μ, T ω ≤ W ω := by
      filter_upwards [h_majorizes] with ω hV_majorizes
      by_cases hlow : ω ∈ low
      · have hnot_threshold : ¬ c < T ω := by
          intro hthreshold
          have hone_le : (1 : ℝ≥0∞) ≤ V ω := by
            simpa [VdVWEventIndicator, hthreshold] using hV_majorizes
          exact not_lt_of_ge hone_le hlow
        have hT_le_c : T ω ≤ c := not_lt.mp hnot_threshold
        have hT_le_U : T ω ≤ U ω := U.majorizes ω
        have hT_le_inf : T ω ≤ U ω ⊓ c := le_inf hT_le_U hT_le_c
        simpa [W, low, hlow] using hT_le_inf
      · have hT_le_U : T ω ≤ U ω := U.majorizes ω
        simpa [W, low, hlow] using hT_le_U
    have hU_le_W : ∀ᵐ ω ∂μ, U ω ≤ W ω :=
      U.minimal_ae W hW_meas hW_majorizes
    filter_upwards [hU_le_W] with ω hU_le_Wω
    by_cases hthreshold : c < U ω
    · have hnot_low : ω ∉ low := by
        intro hlow
        have hU_le_inf : U ω ≤ U ω ⊓ c := by
          simpa [W, low, hlow] using hU_le_Wω
        have hU_le_c : U ω ≤ c := le_trans hU_le_inf inf_le_right
        exact not_lt_of_ge hU_le_c hthreshold
      have hone_le : (1 : ℝ≥0∞) ≤ V ω := not_lt.mp hnot_low
      simpa [VdVWEventIndicator, hthreshold] using hone_le
    · simp [VdVWEventIndicator, hthreshold]

end VdVWMeasurableCover

/--
The threshold-indicator cover realizes the nonnegative outer expectation of a
threshold event.
-/
theorem VdVWOuterExpectation_eq_lintegral_thresholdIndicatorCover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) (c : ℝ≥0∞) :
    VdVWOuterExpectation μ (VdVWEventIndicator {ω | c < T ω}) =
      ∫⁻ ω,
        (VdVWMeasurableCover.thresholdIndicatorCover U c : Ω -> ℝ≥0∞) ω ∂μ :=
  VdVWOuterExpectation_eq_lintegral_cover
    (VdVWMeasurableCover.thresholdIndicatorCover U c)

/--
Nonnegative VdV&W Lemma 1.2.2(vi) probability form:
the outer probability of `{T > c}` is the measure of `{T* > c}`.
-/
theorem VdVWOuterExpectation_thresholdIndicator_eq_measure_cover_threshold
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) (c : ℝ≥0∞) :
    VdVWOuterExpectation μ (VdVWEventIndicator {ω | c < T ω}) =
      μ {ω | c < U ω} := by
  rw [VdVWOuterExpectation_eq_lintegral_thresholdIndicatorCover U c]
  change
    (∫⁻ ω, ({ω | c < U ω}.indicator (fun _ => (1 : ℝ≥0∞)) ω) ∂μ) =
      μ {ω | c < U ω}
  simpa [Pi.one_apply] using
    lintegral_indicator_one (measurableSet_lt measurable_const U.measurable_toFun)

/--
Tail-product outer-expectation bound from a measurable cover.

This is the nonnegative Chapter 1.2 cover-majorant bridge behind later
envelope-tail terms such as `P^* F{F > M}` in Theorem 2.4.3.
-/
theorem VdVWOuterExpectation_tailProduct_le_lintegral_tail_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T) (c : ℝ≥0∞) :
    VdVWOuterExpectation μ
        (fun ω => T ω * VdVWEventIndicator {ω | c < T ω} ω) ≤
      ∫⁻ ω, U ω *
        (VdVWMeasurableCover.thresholdIndicatorCover U c : Ω -> ℝ≥0∞) ω ∂μ :=
  VdVWOuterExpectation_le_lintegral_majorant
    (VdVWMeasurableCover.mulMajorant U
      (VdVWMeasurableCover.thresholdIndicatorCover U c))

/--
A measurable cover of an arbitrary event.

This is the event-level counterpart of `VdVWMeasurableCover`: a measurable
superset with the same outer measure as the original event.
-/
structure VdVWMeasurableSetCover {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (event : Set Ω) where
  toSet : Set Ω
  measurable_toSet : MeasurableSet toSet
  subset_event : event ⊆ toSet
  measure_eq : μ toSet = μ event

namespace VdVWMeasurableSetCover

instance {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {event : Set Ω} :
    CoeSort (VdVWMeasurableSetCover μ event) (Set Ω) where
  coe cover := cover.toSet

/--
Mathlib's `toMeasurable` supplies an event-level measurable cover.

This is the local VdV&W wrapper around mathlib's `measurableSet_toMeasurable`,
`subset_toMeasurable`, and `measure_toMeasurable`.
-/
noncomputable def ofToMeasurable {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (event : Set Ω) :
    VdVWMeasurableSetCover μ event where
  toSet := toMeasurable μ event
  measurable_toSet := measurableSet_toMeasurable μ event
  subset_event := subset_toMeasurable μ event
  measure_eq := measure_toMeasurable event

/--
Existence clause for VdV&W Lemma 1.2.3(ii): every event has a measurable
superset with the same outer measure.
-/
theorem exists_measurableSet_superset_measure_eq {Ω : Type u}
    [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    ∃ coverSet : Set Ω,
      MeasurableSet coverSet ∧ event ⊆ coverSet ∧ μ coverSet = μ event := by
  exact
    ⟨toMeasurable μ event, measurableSet_toMeasurable μ event,
      subset_toMeasurable μ event, measure_toMeasurable event⟩

/-- The indicator of a measurable event cover is a measurable majorant. -/
noncomputable def indicatorMajorant {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {event : Set Ω}
    (cover : VdVWMeasurableSetCover μ event) :
    VdVWMeasurableMajorant μ (VdVWEventIndicator event) where
  toFun := cover.toSet.indicator fun _ => 1
  measurable_toFun := measurable_const.indicator cover.measurable_toSet
  majorizes := by
    intro ω
    by_cases hω : ω ∈ event
    · simp [VdVWEventIndicator, hω, cover.subset_event hω]
    · simp [VdVWEventIndicator, hω]

/--
An arbitrary measurable set cover of an event induces the measurable cover of
the event indicator.

This is the nonnegative indicator version of the VdV&W Lemma 1.2.3(ii) clause:
if `B*` is measurable, contains `B`, and has measure `P* B`, then
`1_{B*}` is the measurable cover of `1_B`.
-/
noncomputable def toEventIndicatorCover {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} [IsFiniteMeasure μ] {event : Set Ω}
    (cover : VdVWMeasurableSetCover μ event) :
    VdVWMeasurableCover μ (VdVWEventIndicator event) where
  toFun := VdVWEventIndicator cover.toSet
  measurable_toFun := measurable_const.indicator cover.measurable_toSet
  majorizes := by
    intro ω
    by_cases hω : ω ∈ event
    · simp [VdVWEventIndicator, hω, cover.subset_event hω]
    · simp [VdVWEventIndicator, hω]
  minimal_ae := by
    intro U hU h_majorizes
    let low : Set Ω := {ω | U ω < 1}
    have hlow_meas : MeasurableSet low := measurableSet_lt hU measurable_const
    have h_event_low_zero : μ (event ∩ low) = 0 := by
      have hbad_zero :
          μ {ω | ¬ VdVWEventIndicator event ω ≤ U ω} = 0 :=
        ae_iff.mp h_majorizes
      refine measure_mono_null ?_ hbad_zero
      intro ω hω
      change ¬ VdVWEventIndicator event ω ≤ U ω
      simpa [VdVWEventIndicator, hω.1, low] using not_le.mpr hω.2
    have h_cover_low_zero : μ (cover.toSet ∩ low) = 0 := by
      have h_inter_eq :
          μ (event ∩ low) = μ (cover.toSet ∩ low) :=
        Measure.measure_inter_eq_of_measure_eq hlow_meas cover.measure_eq.symm
          cover.subset_event (measure_ne_top μ event)
      exact h_inter_eq.symm.trans h_event_low_zero
    refine ae_iff.mpr ?_
    refine measure_mono_null ?_ h_cover_low_zero
    intro ω hω
    by_cases hmem : ω ∈ cover.toSet
    · refine ⟨hmem, ?_⟩
      have hnot_one : ¬ (1 : ℝ≥0∞) ≤ U ω := by
        simpa [VdVWEventIndicator, hmem] using hω
      exact lt_of_not_ge hnot_one
    · exfalso
      have hle : VdVWEventIndicator cover.toSet ω ≤ U ω := by
        simp [VdVWEventIndicator, hmem]
      exact hω hle

/--
An arbitrary measurable set cover of the complement induces the lower
measurable cover of the event indicator.

This is the event-cover form of the identity
`(1_B)_* = 1 - 1_{Bᶜ*}` used in VdV&W Lemma 1.2.3.
-/
noncomputable def complToEventIndicatorLowerCover {Ω : Type u}
    [MeasurableSpace Ω] {μ : Measure Ω} [IsFiniteMeasure μ] {event : Set Ω}
    (coverCompl : VdVWMeasurableSetCover μ eventᶜ) :
    VdVWMeasurableLowerCover μ (VdVWEventIndicator event) where
  toFun := VdVWEventIndicator coverCompl.toSetᶜ
  measurable_toFun := measurable_const.indicator coverCompl.measurable_toSet.compl
  minorizes := by
    intro ω
    by_cases hω : ω ∈ coverCompl.toSetᶜ
    · have h_event : ω ∈ event := by
        by_contra h_not_event
        exact hω (coverCompl.subset_event h_not_event)
      simp [VdVWEventIndicator, hω, h_event]
    · simp [VdVWEventIndicator, hω]
  maximal_ae := by
    intro L hL h_minorizes
    let positive : Set Ω := {ω | 0 < L ω}
    have hpositive_meas : MeasurableSet positive :=
      measurableSet_lt measurable_const hL
    have hbad_zero :
        μ {ω | ¬ L ω ≤ VdVWEventIndicator event ω} = 0 :=
      ae_iff.mp h_minorizes
    have h_event_compl_positive_zero : μ (eventᶜ ∩ positive) = 0 := by
      refine measure_mono_null ?_ hbad_zero
      intro ω hω
      change ¬ L ω ≤ VdVWEventIndicator event ω
      have hnot_event : ω ∉ event := hω.1
      have hpos : 0 < L ω := hω.2
      simpa [VdVWEventIndicator, hnot_event] using not_le.mpr hpos
    have h_cover_positive_zero : μ (coverCompl.toSet ∩ positive) = 0 := by
      have h_inter_eq :
          μ (eventᶜ ∩ positive) = μ (coverCompl.toSet ∩ positive) :=
        Measure.measure_inter_eq_of_measure_eq hpositive_meas
          coverCompl.measure_eq.symm coverCompl.subset_event
          (measure_ne_top μ eventᶜ)
      exact h_inter_eq.symm.trans h_event_compl_positive_zero
    have h_not_cover_positive : ∀ᵐ ω ∂μ, ω ∉ coverCompl.toSet ∩ positive := by
      refine ae_iff.mpr ?_
      simpa using h_cover_positive_zero
    filter_upwards [h_minorizes, h_not_cover_positive] with ω hL_minorizes hω_not_cover_positive
    by_cases hcover : ω ∈ coverCompl.toSet
    · have hnot_positive : ¬ 0 < L ω := by
        intro hpositive
        exact hω_not_cover_positive ⟨hcover, hpositive⟩
      have hL_zero : L ω ≤ 0 := not_lt.mp hnot_positive
      simpa [VdVWEventIndicator, hcover] using hL_zero
    · have h_event : ω ∈ event := by
        by_contra h_not_event
        exact hcover (coverCompl.subset_event h_not_event)
      have hL_one : L ω ≤ 1 := by
        simpa [VdVWEventIndicator, h_event] using hL_minorizes
      simpa [VdVWEventIndicator, hcover] using hL_one

end VdVWMeasurableSetCover

/--
VdV&W Lemma 1.2.3(i), nonnegative indicator form: outer probability is a
special case of nonnegative outer expectation.

Mathlib measures already evaluate arbitrary events by outer measure, so the
right-hand side is `μ event`.
-/
theorem VdVWOuterExpectation_eventIndicator_eq_measure
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    VdVWOuterExpectation μ (VdVWEventIndicator event) = μ event := by
  refine le_antisymm ?upper ?lower
  · let cover := VdVWMeasurableSetCover.ofToMeasurable μ event
    refine
      (VdVWOuterExpectation_le_lintegral_majorant
        (VdVWMeasurableSetCover.indicatorMajorant cover)).trans_eq ?_
    dsimp [VdVWMeasurableSetCover.indicatorMajorant, cover]
    change
      ∫⁻ ω, (toMeasurable μ event).indicator (1 : Ω -> ℝ≥0∞) ω ∂μ =
        μ event
    rw [lintegral_indicator_one (measurableSet_toMeasurable μ event),
      measure_toMeasurable]
  · dsimp [VdVWOuterExpectation]
    refine le_iInf ?_
    intro U
    exact
      meas_le_lintegral₀ U.measurable_toFun.aemeasurable
        (fun ω hω => by
          have h_majorizes := U.majorizes ω
          simpa [VdVWEventIndicator, hω] using h_majorizes)

/--
VdV&W inner probability of an arbitrary event.

For probability measures this is the textbook formula
`1 - P* (eventᶜ)`.  The definition uses `μ univ` rather than `1` so the same
primitive also applies to finite measures.
-/
noncomputable def VdVWInnerProbability {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (event : Set Ω) : ℝ≥0∞ :=
  μ Set.univ - μ eventᶜ

/--
Complement identity behind VdV&W Lemma 1.2.3(i): inner probability plus the
outer measure of the complement is the total mass.
-/
theorem VdVWInnerProbability_add_outerMeasure_compl
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    VdVWInnerProbability μ event + μ eventᶜ = μ Set.univ := by
  rw [VdVWInnerProbability]
  exact tsub_add_cancel_of_le (measure_mono (Set.subset_univ eventᶜ))

/-- Probability-space specialization of the complement identity. -/
theorem VdVWInnerProbability_add_outerMeasure_compl_eq_one
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ]
    (event : Set Ω) :
    VdVWInnerProbability μ event + μ eventᶜ = 1 := by
  simpa using VdVWInnerProbability_add_outerMeasure_compl μ event

/--
On null-measurable events, VdV&W inner probability agrees with the ordinary
mathlib measure.
-/
theorem VdVWInnerProbability_eq_measure_of_nullMeasurable
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    {event : Set Ω} (hevent : NullMeasurableSet event μ) :
    VdVWInnerProbability μ event = μ event := by
  rw [VdVWInnerProbability]
  exact
    (ENNReal.eq_sub_of_add_eq (measure_ne_top μ eventᶜ)
      (measure_add_measure_compl₀ hevent)).symm

/-- Measurable-event specialization of the inner-probability identity. -/
theorem VdVWInnerProbability_eq_measure_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    {event : Set Ω} (hevent : MeasurableSet event) :
    VdVWInnerProbability μ event = μ event :=
  VdVWInnerProbability_eq_measure_of_nullMeasurable μ hevent.nullMeasurableSet

/--
Event-level lower measurable indicator.

For an event `B`, this is the concrete nonnegative version of `(1_B)_*`:
the indicator of the complement of a measurable cover of `Bᶜ`.
-/
noncomputable def VdVWEventLowerIndicator {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (event : Set Ω) : Ω -> ℝ≥0∞ :=
  VdVWEventIndicator (toMeasurable μ eventᶜ)ᶜ

/-- The event-level lower indicator is measurable. -/
theorem measurable_vdVWEventLowerIndicator
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    Measurable (VdVWEventLowerIndicator μ event) :=
  measurable_const.indicator (measurableSet_toMeasurable μ eventᶜ).compl

/-- The event-level lower indicator is pointwise below the raw event indicator. -/
theorem VdVWEventLowerIndicator_le_eventIndicator
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    VdVWEventLowerIndicator μ event ≤ VdVWEventIndicator event := by
  intro ω
  by_cases hω : ω ∈ (toMeasurable μ eventᶜ)ᶜ
  · have h_event : ω ∈ event := by
      by_contra h_not_event
      exact hω (subset_toMeasurable μ eventᶜ h_not_event)
    simp [VdVWEventLowerIndicator, VdVWEventIndicator, hω, h_event]
  · simp [VdVWEventLowerIndicator, VdVWEventIndicator, hω]

/--
Integral of the event-level lower indicator realizes the inner probability in
the finite-measure setting.
-/
theorem lintegral_vdVWEventLowerIndicator_eq_innerProbability
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    (∫⁻ ω, VdVWEventLowerIndicator μ event ω ∂μ) =
      VdVWInnerProbability μ event := by
  rw [VdVWEventLowerIndicator, VdVWEventIndicator]
  change
    (∫⁻ ω,
      ((toMeasurable μ eventᶜ)ᶜ.indicator (1 : Ω -> ℝ≥0∞)) ω ∂μ) =
      VdVWInnerProbability μ event
  rw [lintegral_indicator_one (measurableSet_toMeasurable μ eventᶜ).compl]
  rw [VdVWInnerProbability,
    measure_compl (measurableSet_toMeasurable μ eventᶜ)
      (measure_ne_top μ (toMeasurable μ eventᶜ)),
    measure_toMeasurable]

/-- The event-level lower indicator is a measurable minorant of the event indicator. -/
noncomputable def VdVWMeasurableMinorant.eventLowerIndicator
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    VdVWMeasurableMinorant μ (VdVWEventIndicator event) where
  toFun := VdVWEventLowerIndicator μ event
  measurable_toFun := measurable_vdVWEventLowerIndicator μ event
  minorizes := VdVWEventLowerIndicator_le_eventIndicator μ event

/--
The event inner probability is bounded by the nonnegative inner expectation of
the event indicator.
-/
theorem VdVWInnerProbability_le_innerExpectation_eventIndicator
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    VdVWInnerProbability μ event ≤
      VdVWInnerExpectation μ (VdVWEventIndicator event) := by
  rw [← lintegral_vdVWEventLowerIndicator_eq_innerProbability μ event]
  exact
    lintegral_minorant_le_VdVWInnerExpectation
      (VdVWMeasurableMinorant.eventLowerIndicator μ event)

/--
For finite measures, the event-level lower indicator is the lower measurable
cover of the raw event indicator.

The proof uses mathlib's `toMeasurable` hull and
`measure_toMeasurable_inter`: if a measurable minorant is positive on the
measurable hull of `eventᶜ`, then it is positive on `eventᶜ` up to a null set,
contradicting the minorant hypothesis.
-/
noncomputable def VdVWMeasurableLowerCover.eventIndicatorOfToMeasurableCompl
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    VdVWMeasurableLowerCover μ (VdVWEventIndicator event) where
  toFun := VdVWEventLowerIndicator μ event
  measurable_toFun := measurable_vdVWEventLowerIndicator μ event
  minorizes := VdVWEventLowerIndicator_le_eventIndicator μ event
  maximal_ae := by
    intro L hL h_minorizes
    let coverCompl : Set Ω := toMeasurable μ eventᶜ
    let positive : Set Ω := {ω | 0 < L ω}
    have hpositive_meas : MeasurableSet positive :=
      measurableSet_lt measurable_const hL
    have hbad_zero :
        μ {ω | ¬ L ω ≤ VdVWEventIndicator event ω} = 0 :=
      ae_iff.mp h_minorizes
    have h_event_compl_positive_zero : μ (eventᶜ ∩ positive) = 0 := by
      refine measure_mono_null ?_ hbad_zero
      intro ω hω
      change ¬ L ω ≤ VdVWEventIndicator event ω
      have hnot_event : ω ∉ event := hω.1
      have hpos : 0 < L ω := hω.2
      simpa [VdVWEventIndicator, hnot_event] using not_le.mpr hpos
    have h_cover_positive_zero : μ (coverCompl ∩ positive) = 0 := by
      change μ (toMeasurable μ eventᶜ ∩ positive) = 0
      rw [Measure.measure_toMeasurable_inter hpositive_meas (measure_ne_top μ eventᶜ)]
      exact h_event_compl_positive_zero
    have h_not_cover_positive : ∀ᵐ ω ∂μ, ω ∉ coverCompl ∩ positive := by
      refine ae_iff.mpr ?_
      simpa [coverCompl] using h_cover_positive_zero
    filter_upwards [h_minorizes, h_not_cover_positive] with ω hL_minorizes hω_not_cover_positive
    by_cases hcover : ω ∈ coverCompl
    · have hnot_positive : ¬ 0 < L ω := by
        intro hpositive
        exact hω_not_cover_positive ⟨hcover, hpositive⟩
      have hL_zero : L ω ≤ 0 := not_lt.mp hnot_positive
      simpa [VdVWEventLowerIndicator, VdVWEventIndicator, coverCompl, hcover]
        using hL_zero
    · have hnot_event_compl : ω ∉ eventᶜ := by
        intro hω_event_compl
        exact hcover (subset_toMeasurable μ eventᶜ hω_event_compl)
      have h_event : ω ∈ event := by
        simpa using hnot_event_compl
      have hL_one : L ω ≤ 1 := by
        simpa [VdVWEventIndicator, h_event] using hL_minorizes
      simpa [VdVWEventLowerIndicator, VdVWEventIndicator, coverCompl, hcover]
        using hL_one

/--
VdV&W Lemma 1.2.3(iii), nonnegative indicator form: the inner expectation of
an arbitrary event indicator is the inner probability of the event.
-/
theorem VdVWInnerExpectation_eventIndicator_eq_innerProbability
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    VdVWInnerExpectation μ (VdVWEventIndicator event) =
      VdVWInnerProbability μ event := by
  rw [VdVWInnerExpectation_eq_lintegral_lowerCover
    (VdVWMeasurableLowerCover.eventIndicatorOfToMeasurableCompl μ event)]
  exact lintegral_vdVWEventLowerIndicator_eq_innerProbability μ event

/--
Any measurable set cover of the complement realizes the inner expectation of
the event indicator through its complement.
-/
theorem VdVWInnerExpectation_eq_lintegral_eventIndicator_complSetCover
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    {event : Set Ω} (coverCompl : VdVWMeasurableSetCover μ eventᶜ) :
    VdVWInnerExpectation μ (VdVWEventIndicator event) =
      ∫⁻ ω, VdVWEventIndicator coverCompl.toSetᶜ ω ∂μ :=
  VdVWInnerExpectation_eq_lintegral_lowerCover
    (VdVWMeasurableSetCover.complToEventIndicatorLowerCover coverCompl)

/--
The complement of any measurable set cover of `Bᶜ` integrates to the inner
probability of `B`.
-/
theorem lintegral_eventIndicator_complSetCover_eq_innerProbability
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    {event : Set Ω} (coverCompl : VdVWMeasurableSetCover μ eventᶜ) :
    (∫⁻ ω, VdVWEventIndicator coverCompl.toSetᶜ ω ∂μ) =
      VdVWInnerProbability μ event := by
  rw [← VdVWInnerExpectation_eq_lintegral_eventIndicator_complSetCover μ coverCompl]
  exact VdVWInnerExpectation_eventIndicator_eq_innerProbability μ event

/--
Expectation-level complement identity behind VdV&W Lemma 1.2.3(iii).

The nonnegative outer expectation of `1_B` plus the nonnegative inner
expectation of `1_{Bᶜ}` is the total mass.
-/
theorem VdVWOuterExpectation_eventIndicator_add_innerExpectation_compl
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    VdVWOuterExpectation μ (VdVWEventIndicator event) +
      VdVWInnerExpectation μ (VdVWEventIndicator eventᶜ) =
        μ Set.univ := by
  rw [VdVWOuterExpectation_eventIndicator_eq_measure,
    VdVWInnerExpectation_eventIndicator_eq_innerProbability]
  simpa [add_comm] using VdVWInnerProbability_add_outerMeasure_compl μ eventᶜ

/--
Probability-space specialization of the expectation-level complement identity.
-/
theorem VdVWOuterExpectation_eventIndicator_add_innerExpectation_compl_eq_one
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ]
    (event : Set Ω) :
    VdVWOuterExpectation μ (VdVWEventIndicator event) +
      VdVWInnerExpectation μ (VdVWEventIndicator eventᶜ) = 1 := by
  simpa using
    VdVWOuterExpectation_eventIndicator_add_innerExpectation_compl μ event

/--
Symmetric expectation-level complement identity behind VdV&W Lemma 1.2.3(iii).

The nonnegative inner expectation of `1_B` plus the nonnegative outer
expectation of `1_{Bᶜ}` is the total mass.
-/
theorem VdVWInnerExpectation_eventIndicator_add_outerExpectation_compl
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    VdVWInnerExpectation μ (VdVWEventIndicator event) +
      VdVWOuterExpectation μ (VdVWEventIndicator eventᶜ) =
        μ Set.univ := by
  rw [VdVWInnerExpectation_eventIndicator_eq_innerProbability,
    VdVWOuterExpectation_eventIndicator_eq_measure]
  exact VdVWInnerProbability_add_outerMeasure_compl μ event

/--
Probability-space specialization of the symmetric expectation-level
complement identity.
-/
theorem VdVWInnerExpectation_eventIndicator_add_outerExpectation_compl_eq_one
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ]
    (event : Set Ω) :
    VdVWInnerExpectation μ (VdVWEventIndicator event) +
      VdVWOuterExpectation μ (VdVWEventIndicator eventᶜ) = 1 := by
  simpa using
    VdVWInnerExpectation_eventIndicator_add_outerExpectation_compl μ event

/--
Event-indicator complement identity for VdV&W Lemma 1.2.3(iii):
the upper indicator of `B` plus the lower indicator of `Bᶜ` is `1`.
-/
theorem VdVWEventIndicator_cover_add_lower_compl
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    (fun ω =>
      VdVWEventIndicator (toMeasurable μ event) ω +
        VdVWEventLowerIndicator μ eventᶜ ω) =
      fun _ => (1 : ℝ≥0∞) := by
  funext ω
  by_cases hω : ω ∈ toMeasurable μ event
  · simp [VdVWEventLowerIndicator, VdVWEventIndicator, hω]
  · simp [VdVWEventLowerIndicator, VdVWEventIndicator, hω]

/--
Pointwise event-indicator complement identity for an arbitrary measurable set
cover.

This is the set-cover version of the VdV&W Lemma 1.2.3(iii) identity
`(1_B)^* + (1_{Ω \\ B})_* = 1`.
-/
theorem VdVWEventIndicator_setCover_add_compl
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} {event : Set Ω}
    (cover : VdVWMeasurableSetCover μ event) :
    (fun ω =>
      VdVWEventIndicator cover.toSet ω +
        VdVWEventIndicator cover.toSetᶜ ω) =
      fun _ => (1 : ℝ≥0∞) := by
  funext ω
  by_cases hω : ω ∈ cover.toSet
  · simp [VdVWEventIndicator, hω]
  · simp [VdVWEventIndicator, hω]

/--
For a finite measure, the measurable hull of an event is a measurable cover of
the event indicator.

This is the nonnegative indicator version of the measurable-set-cover part of
VdV&W Lemma 1.2.3.  The finite-measure assumption is natural for the textbook
probability-space setting and lets mathlib's `Measure.measure_toMeasurable_inter`
transfer measurable subevent tests from the hull back to the original event.
-/
noncomputable def VdVWMeasurableCover.eventIndicatorOfToMeasurable
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    VdVWMeasurableCover μ (VdVWEventIndicator event) where
  toFun := VdVWEventIndicator (toMeasurable μ event)
  measurable_toFun :=
    measurable_const.indicator (measurableSet_toMeasurable μ event)
  majorizes := by
    intro ω
    by_cases hω : ω ∈ event
    · simp [VdVWEventIndicator, hω, subset_toMeasurable μ event hω]
    · simp [VdVWEventIndicator, hω]
  minimal_ae := by
    intro U hU h_majorizes
    let low : Set Ω := {ω | U ω < 1}
    have hlow_meas : MeasurableSet low := measurableSet_lt hU measurable_const
    have h_event_low_zero : μ (event ∩ low) = 0 := by
      have hbad_zero :
          μ {ω | ¬ VdVWEventIndicator event ω ≤ U ω} = 0 :=
        ae_iff.mp h_majorizes
      refine measure_mono_null ?_ hbad_zero
      intro ω hω
      change ¬ VdVWEventIndicator event ω ≤ U ω
      simpa [VdVWEventIndicator, hω.1, low] using not_le.mpr hω.2
    have h_hull_low_zero : μ (toMeasurable μ event ∩ low) = 0 := by
      rw [Measure.measure_toMeasurable_inter hlow_meas (measure_ne_top μ event),
        h_event_low_zero]
    refine ae_iff.mpr ?_
    refine measure_mono_null ?_ h_hull_low_zero
    intro ω hω
    by_cases hmem : ω ∈ toMeasurable μ event
    · refine ⟨hmem, ?_⟩
      have hnot_one : ¬ (1 : ℝ≥0∞) ≤ U ω := by
        simpa [VdVWEventIndicator, hmem] using hω
      exact lt_of_not_ge hnot_one
    · exfalso
      have hle : VdVWEventIndicator (toMeasurable μ event) ω ≤ U ω := by
        simp [VdVWEventIndicator, hmem]
      exact hω hle

/--
The finite-measure event-indicator measurable cover realizes the already
proved outer-expectation value.
-/
theorem VdVWOuterExpectation_eq_lintegral_eventIndicatorCover
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    VdVWOuterExpectation μ (VdVWEventIndicator event) =
      ∫⁻ ω,
        (VdVWMeasurableCover.eventIndicatorOfToMeasurable μ event : Ω -> ℝ≥0∞)
          ω ∂μ :=
  VdVWOuterExpectation_eq_lintegral_cover
    (VdVWMeasurableCover.eventIndicatorOfToMeasurable μ event)

/--
The event-indicator measurable cover induced by any measurable set cover
realizes the outer expectation.
-/
theorem VdVWOuterExpectation_eq_lintegral_eventIndicator_setCover
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    {event : Set Ω} (cover : VdVWMeasurableSetCover μ event) :
    VdVWOuterExpectation μ (VdVWEventIndicator event) =
      ∫⁻ ω, VdVWEventIndicator cover.toSet ω ∂μ :=
  VdVWOuterExpectation_eq_lintegral_cover
    (VdVWMeasurableSetCover.toEventIndicatorCover cover)

/--
The indicator of any measurable set cover integrates to the outer measure of
the original event.

This is the direct integral form of the VdV&W Lemma 1.2.3(ii) equality
`E 1_{B*} = P(B*) = P*(B)`.
-/
theorem lintegral_eventIndicator_setCover_eq_measure
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    {event : Set Ω} (cover : VdVWMeasurableSetCover μ event) :
    (∫⁻ ω, VdVWEventIndicator cover.toSet ω ∂μ) = μ event := by
  change
    (∫⁻ ω, cover.toSet.indicator (fun _ => (1 : ℝ≥0∞)) ω ∂μ) =
      μ event
  rw [← cover.measure_eq]
  simpa [Pi.one_apply] using lintegral_indicator_one cover.measurable_toSet

/--
The `toMeasurable` hull gives the direct integral realization of the outer
measure of an event.

This is the concrete hull version of the VdV&W Lemma 1.2.3(ii) equality
`E 1_{B*} = P*(B)`.
-/
theorem lintegral_eventIndicator_toMeasurable_eq_measure
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    (∫⁻ ω, VdVWEventIndicator (toMeasurable μ event) ω ∂μ) = μ event := by
  calc
    (∫⁻ ω, VdVWEventIndicator (toMeasurable μ event) ω ∂μ) =
        μ (toMeasurable μ event) := by
      change
        (∫⁻ ω,
          (toMeasurable μ event).indicator (fun _ => (1 : ℝ≥0∞)) ω ∂μ) =
          μ (toMeasurable μ event)
      simpa only [Pi.one_apply] using
        lintegral_indicator_one (measurableSet_toMeasurable μ event)
    _ = μ event := measure_toMeasurable event

/--
The complement of the `toMeasurable` hull of `eventᶜ` has measure equal to
the inner probability of `event`.

This is the event-set version of the VdV&W Lemma 1.2.3(iii) identity
`P_* B = P((Bᶜ)*ᶜ)`.
-/
theorem measure_compl_toMeasurable_compl_eq_innerProbability
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    (event : Set Ω) :
    μ (toMeasurable μ eventᶜ)ᶜ = VdVWInnerProbability μ event := by
  rw [VdVWInnerProbability,
    measure_compl (measurableSet_toMeasurable μ eventᶜ)
      (measure_ne_top μ (toMeasurable μ eventᶜ)),
    measure_toMeasurable]

/--
The complement of any measurable cover of `eventᶜ` has measure equal to the
inner probability of `event`.

This is the arbitrary-set-cover version of the VdV&W Lemma 1.2.3(iii)
identity `P_* B = P((Bᶜ)*ᶜ)`.
-/
theorem measure_compl_setCover_eq_innerProbability
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) [IsFiniteMeasure μ]
    {event : Set Ω} (coverCompl : VdVWMeasurableSetCover μ eventᶜ) :
    μ coverCompl.toSetᶜ = VdVWInnerProbability μ event := by
  calc
    μ coverCompl.toSetᶜ =
        ∫⁻ ω, VdVWEventIndicator coverCompl.toSetᶜ ω ∂μ := by
      change
        μ coverCompl.toSetᶜ =
          ∫⁻ ω,
            coverCompl.toSetᶜ.indicator (fun _ => (1 : ℝ≥0∞)) ω ∂μ
      simpa [Pi.one_apply] using
        (lintegral_indicator_one coverCompl.measurable_toSet.compl).symm
    _ = VdVWInnerProbability μ event :=
      lintegral_eventIndicator_complSetCover_eq_innerProbability μ coverCompl

end StatInference
