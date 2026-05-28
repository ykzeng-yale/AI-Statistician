import StatInference.EmpiricalProcess.BracketingPrimitive
import Mathlib.Data.EReal.Basic
import Mathlib.MeasureTheory.Constructions.BorelSpace.Order
import Mathlib.MeasureTheory.Integral.Bochner.Set
import Mathlib.MeasureTheory.Measure.Real
import Mathlib.MeasureTheory.Measure.TightNormed
import Mathlib.Probability.CDF
import Mathlib.Topology.Instances.EReal.Lemmas
import Mathlib.Topology.Order.Bornology

/-!
# Real half-line brackets

This module starts the local formalization layer for VdV&W Example 2.4.2.
It proves the pointwise and `L1(P)` facts for brackets of indicators of real
half-lines.  The finite grid existence theorem is kept separate.
-/

namespace StatInference

open MeasureTheory Set Filter
open scoped ENNReal Topology

universe u

/-- Indicator of the closed lower half-line `(-∞, c]`, as a real-valued function. -/
noncomputable def realHalfLineIndicator (c : ℝ) : ℝ -> ℝ :=
  Set.indicator (Set.Iic c) (fun _ => (1 : ℝ))

/-- Indicator of the open lower half-line `(-∞, c)`, as a real-valued function. -/
noncomputable def realOpenHalfLineIndicator (c : ℝ) : ℝ -> ℝ :=
  Set.indicator (Set.Iio c) (fun _ => (1 : ℝ))

/--
The VdV&W Example 2.4.2 bracket
`[1{(-∞, a]}, 1{(-∞, b)}]`.
-/
noncomputable def realHalfLineBracket (a b : ℝ) : FunctionBracket ℝ where
  lower := realHalfLineIndicator a
  upper := realOpenHalfLineIndicator b

/--
If `a ≤ c < b`, then `1{(-∞, c]}` lies in the bracket
`[1{(-∞, a]}, 1{(-∞, b)}]`.
-/
theorem realHalfLineBracket_mem_indicator_of_le_lt
    {a b c : ℝ} (hac : a ≤ c) (hcb : c < b) :
    (realHalfLineBracket a b).Mem (realHalfLineIndicator c) := by
  intro x
  constructor
  · by_cases hxa : x ≤ a
    · have hxc : x ≤ c := hxa.trans hac
      simp [realHalfLineBracket, realHalfLineIndicator, hxa, hxc]
    · by_cases hxc : x ≤ c
      · simp [realHalfLineBracket, realHalfLineIndicator, hxa, hxc]
      · simp [realHalfLineBracket, realHalfLineIndicator, hxa, hxc]
  · by_cases hxc : x ≤ c
    · have hxb : x < b := lt_of_le_of_lt hxc hcb
      simp [realHalfLineBracket, realHalfLineIndicator,
        realOpenHalfLineIndicator, hxc, hxb]
    · by_cases hxb : x < b
      · simp [realHalfLineBracket, realHalfLineIndicator,
          realOpenHalfLineIndicator, hxc, hxb]
      · simp [realHalfLineBracket, realHalfLineIndicator,
          realOpenHalfLineIndicator, hxc, hxb]

/-- Closed half-line indicators are integrable under any finite measure. -/
theorem integrable_realHalfLineIndicator
    (μ : Measure ℝ) [IsFiniteMeasure μ] (c : ℝ) :
    Integrable (realHalfLineIndicator c) μ := by
  simpa [realHalfLineIndicator] using
    (integrable_const (1 : ℝ)).indicator measurableSet_Iic

/-- Open half-line indicators are integrable under any finite measure. -/
theorem integrable_realOpenHalfLineIndicator
    (μ : Measure ℝ) [IsFiniteMeasure μ] (c : ℝ) :
    Integrable (realOpenHalfLineIndicator c) μ := by
  simpa [realOpenHalfLineIndicator] using
    (integrable_const (1 : ℝ)).indicator measurableSet_Iio

/--
For `a < b`, the absolute endpoint gap of the Example 2.4.2 bracket is the
indicator of the open cell `(a, b)`.
-/
theorem abs_realHalfLineBracket_endpoint_gap_eq_indicator_Ioo
    {a b : ℝ} (hab : a < b) :
    (fun x =>
      |(realHalfLineBracket a b).upper x -
        (realHalfLineBracket a b).lower x|) =
      Set.indicator (Set.Ioo a b) (fun _ => (1 : ℝ)) := by
  funext x
  by_cases hax : a < x
  · by_cases hxb : x < b
    · simp [realHalfLineBracket, realHalfLineIndicator,
        realOpenHalfLineIndicator, hax, hxb]
    · have hnot_upper : ¬ x < b := hxb
      have hnot_cell : x ∉ Set.Ioo a b := fun hx => hnot_upper hx.2
      simp [realHalfLineBracket, realHalfLineIndicator,
        realOpenHalfLineIndicator, hax, hnot_upper, hnot_cell]
  · have hxa : x ≤ a := le_of_not_gt hax
    have hxb : x < b := lt_of_le_of_lt hxa hab
    have hnot_cell : x ∉ Set.Ioo a b := fun hx => hax hx.1
    simp [realHalfLineBracket, realHalfLineIndicator,
      realOpenHalfLineIndicator, hxa, hxb, hnot_cell]

/--
For `a < b`, the `L1(P)` width of the half-line bracket is the real measure
of the open cell `(a, b)`.
-/
theorem realHalfLineBracket_l1Width_eq_measureReal_Ioo
    (μ : Measure ℝ) {a b : ℝ} (hab : a < b) :
    (realHalfLineBracket a b).l1Width μ = μ.real (Set.Ioo a b) := by
  dsimp [FunctionBracket.l1Width]
  rw [abs_realHalfLineBracket_endpoint_gap_eq_indicator_Ioo hab]
  exact integral_indicator_one measurableSet_Ioo

/--
A supplied finite real grid for half-line brackets.

This is a proof-carrying finite-grid layer for VdV&W Example 2.4.2.  It does
not yet construct the textbook grid from an arbitrary distribution; it records
exactly the data needed to turn such a grid into the primitive local
bracketing-number witness.
-/
structure SuppliedRealHalfLineGrid
    (μ : Measure ℝ) (epsilon : ℝ) (cardinality : ℕ) where
  left : Fin cardinality -> ℝ
  right : Fin cardinality -> ℝ
  bracketOf : ℝ -> Fin cardinality
  left_lt_right : ∀ bracketIndex, left bracketIndex < right bracketIndex
  left_le_index : ∀ c, left (bracketOf c) ≤ c
  index_lt_right : ∀ c, c < right (bracketOf c)
  cell_width_lt :
    ∀ bracketIndex, μ.real (Set.Ioo (left bracketIndex) (right bracketIndex)) < epsilon

namespace SuppliedRealHalfLineGrid

/--
A supplied real half-line grid at a smaller radius is also a supplied grid at
any larger radius.
-/
def of_le_epsilon
    {μ : Measure ℝ} {epsilon smallerEpsilon : ℝ} {cardinality : ℕ}
    (grid : SuppliedRealHalfLineGrid μ smallerEpsilon cardinality)
    (hsmall : smallerEpsilon ≤ epsilon) :
    SuppliedRealHalfLineGrid μ epsilon cardinality where
  left := grid.left
  right := grid.right
  bracketOf := grid.bracketOf
  left_lt_right := grid.left_lt_right
  left_le_index := grid.left_le_index
  index_lt_right := grid.index_lt_right
  cell_width_lt := fun bracketIndex =>
    lt_of_lt_of_le (grid.cell_width_lt bracketIndex) hsmall

/--
Finite real-grid existence is monotone in the requested radius.
-/
theorem exists_of_le_epsilon
    {μ : Measure ℝ} {epsilon smallerEpsilon : ℝ}
    (hsmall : smallerEpsilon ≤ epsilon)
    (gridExists :
      ∃ cardinality, Nonempty
        (SuppliedRealHalfLineGrid μ smallerEpsilon cardinality)) :
    ∃ cardinality, Nonempty (SuppliedRealHalfLineGrid μ epsilon cardinality) := by
  rcases gridExists with ⟨cardinality, gridNonempty⟩
  exact ⟨cardinality, gridNonempty.map fun grid => grid.of_le_epsilon hsmall⟩

/--
A supplied finite real grid yields an explicit-cardinality finite `L1(P)`
bracket cover for the half-line indicator class.
-/
noncomputable def toFiniteL1BracketCoverAtCard
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} {cardinality : ℕ}
    (grid : SuppliedRealHalfLineGrid μ epsilon cardinality) :
    FiniteL1BracketCoverAtCard μ Set.univ realHalfLineIndicator
      epsilon cardinality where
  bracket := fun bracketIndex =>
    realHalfLineBracket (grid.left bracketIndex) (grid.right bracketIndex)
  bracketOf := fun c _ => grid.bracketOf c
  mem_bracket := by
    intro c _hc
    exact
      realHalfLineBracket_mem_indicator_of_le_lt
        (grid.left_le_index c) (grid.index_lt_right c)
  width_lt := by
    intro bracketIndex
    dsimp [IsL1EpsilonBracket, l1BracketWidth]
    rw [realHalfLineBracket_l1Width_eq_measureReal_Ioo μ
      (grid.left_lt_right bracketIndex)]
    exact grid.cell_width_lt bracketIndex
  lower_integrable := by
    intro bracketIndex
    exact integrable_realHalfLineIndicator μ (grid.left bracketIndex)
  upper_integrable := by
    intro bracketIndex
    exact integrable_realOpenHalfLineIndicator μ (grid.right bracketIndex)
  function_integrable := by
    intro c _hc
    exact integrable_realHalfLineIndicator μ c

/--
A supplied finite real grid proves finiteness of the primitive local
`L1(P)` bracketing-number witness.
-/
theorem hasFiniteL1BracketingNumber
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} {cardinality : ℕ}
    (grid : SuppliedRealHalfLineGrid μ epsilon cardinality) :
    HasFiniteL1BracketingNumber μ Set.univ realHalfLineIndicator epsilon := by
  exact ⟨cardinality, ⟨grid.toFiniteL1BracketCoverAtCard⟩⟩

/--
A supplied finite real grid makes the numeric primitive bracketing number
finite.
-/
theorem l1BracketingNumber_lt_top
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} {cardinality : ℕ}
    (grid : SuppliedRealHalfLineGrid μ epsilon cardinality) :
    l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ :=
  l1BracketingNumber_lt_top_of_hasFinite grid.hasFiniteL1BracketingNumber

end SuppliedRealHalfLineGrid

/--
Indicator of the extended-endpoint closed lower half-line
`{x : ℝ | (x : EReal) ≤ c}`.
-/
noncomputable def eRealClosedHalfLineIndicator (c : EReal) : ℝ -> ℝ :=
  Set.indicator {x : ℝ | (x : EReal) ≤ c} (fun _ => (1 : ℝ))

/--
Indicator of the extended-endpoint open lower half-line
`{x : ℝ | (x : EReal) < c}`.
-/
noncomputable def eRealOpenHalfLineIndicator (c : EReal) : ℝ -> ℝ :=
  Set.indicator {x : ℝ | (x : EReal) < c} (fun _ => (1 : ℝ))

/--
The extended-endpoint version of the VdV&W Example 2.4.2 bracket
`[1{(-∞, a]}, 1{(-∞, b)}]`.
-/
noncomputable def eRealHalfLineBracket (a b : EReal) : FunctionBracket ℝ where
  lower := eRealClosedHalfLineIndicator a
  upper := eRealOpenHalfLineIndicator b

/-- The open real cell selected by two extended-real endpoints. -/
def eRealOpenCell (a b : EReal) : Set ℝ :=
  {x : ℝ | (x : EReal) ∈ Set.Ioo a b}

/-- Extended-real endpoint open cells are Borel measurable on `ℝ`. -/
theorem measurableSet_eRealOpenCell (a b : EReal) :
    MeasurableSet (eRealOpenCell a b) := by
  change MeasurableSet (((fun x : ℝ => (x : EReal)) ⁻¹' Set.Ioo a b))
  exact continuous_coe_real_ereal.measurable measurableSet_Ioo

/-- Finite extended endpoints recover the ordinary real open interval cell. -/
theorem eRealOpenCell_coe_coe (a b : ℝ) :
    eRealOpenCell (a : EReal) (b : EReal) = Set.Ioo a b := by
  ext x
  simp [eRealOpenCell]

/-- A left endpoint `-∞` and finite right endpoint recover an open lower half-line. -/
theorem eRealOpenCell_bot_coe (b : ℝ) :
    eRealOpenCell ⊥ (b : EReal) = Set.Iio b := by
  ext x
  simp [eRealOpenCell]

/-- A finite left endpoint and right endpoint `∞` recover an open upper half-line. -/
theorem eRealOpenCell_coe_top (a : ℝ) :
    eRealOpenCell (a : EReal) ⊤ = Set.Ioi a := by
  ext x
  simp [eRealOpenCell]

/-- The extended-open cell `(-∞, ∞)` is all of `ℝ`. -/
theorem eRealOpenCell_bot_top :
    eRealOpenCell ⊥ ⊤ = Set.univ := by
  ext x
  simp [eRealOpenCell]

/-- Finite extended endpoints recover the ordinary real open interval measure. -/
theorem measureReal_eRealOpenCell_coe_coe
    (μ : Measure ℝ) (a b : ℝ) :
    μ.real (eRealOpenCell (a : EReal) (b : EReal)) = μ.real (Set.Ioo a b) := by
  rw [eRealOpenCell_coe_coe]

/-- A left endpoint `-∞` and finite right endpoint recover the open lower half-line measure. -/
theorem measureReal_eRealOpenCell_bot_coe
    (μ : Measure ℝ) (b : ℝ) :
    μ.real (eRealOpenCell ⊥ (b : EReal)) = μ.real (Set.Iio b) := by
  rw [eRealOpenCell_bot_coe]

/-- A finite left endpoint and right endpoint `∞` recover the open upper half-line measure. -/
theorem measureReal_eRealOpenCell_coe_top
    (μ : Measure ℝ) (a : ℝ) :
    μ.real (eRealOpenCell (a : EReal) ⊤) = μ.real (Set.Ioi a) := by
  rw [eRealOpenCell_coe_top]

/-- The extended-open cell `(-∞, ∞)` has the measure of the whole line. -/
theorem measureReal_eRealOpenCell_bot_top
    (μ : Measure ℝ) :
    μ.real (eRealOpenCell ⊥ ⊤) = μ.real Set.univ := by
  rw [eRealOpenCell_bot_top]

/--
For a probability measure on the real line, the real mass of an open interval
is the left-limit CDF increment.

This is the CDF/Stieltjes bridge needed for the distribution-dependent
finite-partition step in VdV&W Example 2.4.2.
-/
theorem measureReal_Ioo_eq_cdf_leftLim_sub
    (μ : Measure ℝ) [IsProbabilityMeasure μ] {a b : ℝ} (hab : a < b) :
    μ.real (Set.Ioo a b) =
      Function.leftLim (ProbabilityTheory.cdf μ) b - ProbabilityTheory.cdf μ a := by
  have hmeasure :
      ((ProbabilityTheory.cdf μ).measure (Set.Ioo a b)).toReal =
        μ.real (Set.Ioo a b) := by
    rw [measureReal_def, ProbabilityTheory.measure_cdf]
  calc
    μ.real (Set.Ioo a b)
        = ((ProbabilityTheory.cdf μ).measure (Set.Ioo a b)).toReal :=
          hmeasure.symm
    _ = (ENNReal.ofReal
          (Function.leftLim (ProbabilityTheory.cdf μ) b -
            ProbabilityTheory.cdf μ a)).toReal := by
          rw [StieltjesFunction.measure_Ioo]
    _ = Function.leftLim (ProbabilityTheory.cdf μ) b -
          ProbabilityTheory.cdf μ a :=
          ENNReal.toReal_ofReal
            (sub_nonneg.mpr ((ProbabilityTheory.cdf μ).mono.le_leftLim hab))

/--
An interval CDF left-limit increment bound gives the corresponding real
open-cell measure bound.
-/
theorem measureReal_Ioo_lt_of_cdf_leftLim_sub_lt
    (μ : Measure ℝ) [IsProbabilityMeasure μ] {epsilon a b : ℝ}
    (hab : a < b)
    (hcdf :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ a < epsilon) :
    μ.real (Set.Ioo a b) < epsilon := by
  rw [measureReal_Ioo_eq_cdf_leftLim_sub μ hab]
  exact hcdf

/--
For a non-atomic locally finite real measure, every point has an open
neighborhood of arbitrarily small real measure.

This is the local continuity ingredient for the future finite endpoint-grid
construction in the Durrett/Glivenko-Cantelli route.
-/
theorem exists_realOpenInterval_measureReal_lt_of_noAtoms
    (μ : Measure ℝ) [IsFiniteMeasureOnCompacts μ] [NoAtoms μ]
    {epsilon x : ℝ} (hepsilon : 0 < epsilon) :
    ∃ l r : ℝ, l < x ∧ x < r ∧ μ.real (Set.Ioo l r) < epsilon := by
  have htarget : Set.Iio (ENNReal.ofReal epsilon) ∈ 𝓝 (0 : ℝ≥0∞) := by
    exact Iio_mem_nhds (ENNReal.ofReal_pos.mpr hepsilon)
  have htendsto :
      Tendsto (fun δ : ℝ => μ (Set.Icc (x - δ) (x + δ))) (𝓝[>] (0 : ℝ))
        (𝓝 (0 : ℝ≥0∞)) := by
    simpa [measure_singleton] using tendsto_measure_Icc_nhdsWithin_right' μ x
  have hsmall : ∀ᶠ δ : ℝ in 𝓝[>] (0 : ℝ),
      μ (Set.Icc (x - δ) (x + δ)) < ENNReal.ofReal epsilon :=
    htendsto htarget
  have hpos : ∀ᶠ δ : ℝ in 𝓝[>] (0 : ℝ), δ ∈ Set.Ioi (0 : ℝ) :=
    self_mem_nhdsWithin
  rcases (hsmall.and hpos).exists with ⟨δ, hδsmall, hδpos⟩
  have hδpos' : 0 < δ := hδpos
  refine ⟨x - δ, x + δ, sub_lt_self x hδpos', lt_add_of_pos_right x hδpos', ?_⟩
  have hsubset : Set.Ioo (x - δ) (x + δ) ⊆ Set.Icc (x - δ) (x + δ) :=
    Set.Ioo_subset_Icc_self
  have hIoo_lt : μ (Set.Ioo (x - δ) (x + δ)) < ENNReal.ofReal epsilon :=
    (measure_mono hsubset).trans_lt hδsmall
  exact ENNReal.toReal_lt_of_lt_ofReal hIoo_lt

/--
For a non-atomic locally finite real measure, every compact real interval is
covered by finitely many open intervals of arbitrarily small real measure.

This packages the compactness step needed before a future endpoint-grid
constructor orders the resulting endpoints.
-/
theorem exists_finset_realOpenInterval_cover_Icc_measureReal_lt_of_noAtoms
    (μ : Measure ℝ) [IsFiniteMeasureOnCompacts μ] [NoAtoms μ]
    {epsilon a b : ℝ} (hepsilon : 0 < epsilon) :
    ∃ centers : Finset ℝ, ∃ l r : ℝ -> ℝ,
      (∀ x ∈ centers, x ∈ Set.Icc a b) ∧
      (∀ x ∈ centers,
        l x < x ∧ x < r x ∧ μ.real (Set.Ioo (l x) (r x)) < epsilon) ∧
      Set.Icc a b ⊆ ⋃ x ∈ centers, Set.Ioo (l x) (r x) := by
  classical
  have hlocal : ∀ x : ℝ,
      ∃ l r : ℝ, l < x ∧ x < r ∧ μ.real (Set.Ioo l r) < epsilon := fun x =>
    exists_realOpenInterval_measureReal_lt_of_noAtoms μ (x := x) hepsilon
  choose l r hlr using hlocal
  have hnhds : ∀ x ∈ Set.Icc a b, Set.Ioo (l x) (r x) ∈ 𝓝 x := by
    intro x _hx
    exact isOpen_Ioo.mem_nhds ⟨(hlr x).1, (hlr x).2.1⟩
  rcases isCompact_Icc.elim_nhds_subcover (fun x : ℝ => Set.Ioo (l x) (r x)) hnhds with
    ⟨centers, hcenters, hcover⟩
  refine ⟨centers, l, r, hcenters, ?_, hcover⟩
  intro x _hx
  exact hlr x

/--
A proof-carrying bounded middle CDF partition for the empirical-CDF
half-line class.

This is the local primitive needed before the full quantile/cutpoint
existence proof for VdV&W Example 2.4.2. It records a finite real endpoint
sequence on a bounded interval `[a, b]`, a selector putting every
`c ∈ [a, b)` into an adjacent endpoint cell, and CDF increment bounds for the
open cells. The infinite lower and upper tails are added by later endpoint
grid constructors.
-/
structure SuppliedRealMiddleCDFPartition
    (μ : Measure ℝ) (epsilon a b : ℝ) (middleCells : ℕ) where
  endpoint : Fin (middleCells + 1) -> ℝ
  strictMono : StrictMono endpoint
  left_eq : endpoint 0 = a
  right_eq : endpoint (Fin.last middleCells) = b
  bracketOf : ∀ c : ℝ, a ≤ c -> c < b -> Fin middleCells
  left_le_index :
    ∀ c hleft hright,
      endpoint (Fin.castSucc (bracketOf c hleft hright)) ≤ c
  index_lt_right :
    ∀ c hleft hright,
      c < endpoint (Fin.succ (bracketOf c hleft hright))
  cdf_increment_lt :
    ∀ cell : Fin middleCells,
      Function.leftLim (ProbabilityTheory.cdf μ) (endpoint (Fin.succ cell)) -
        ProbabilityTheory.cdf μ (endpoint (Fin.castSucc cell)) < epsilon

namespace SuppliedRealMiddleCDFPartition

/--
The one-cell middle partition of a bounded interval.

This is the base case for the distribution-dependent middle-CDF partition
constructor: if the entire interval already has CDF left-limit increment below
the requested radius, the endpoint list `[a, b]` is sufficient.
-/
noncomputable def oneCell
    {μ : Measure ℝ} {epsilon a b : ℝ} (hab : a < b)
    (hinc :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ a < epsilon) :
    SuppliedRealMiddleCDFPartition μ epsilon a b 1 where
  endpoint := fun endpointIndex => if endpointIndex = 0 then a else b
  strictMono := by
    intro i j hij
    fin_cases i <;> fin_cases j <;> simp at hij ⊢
    exact hab
  left_eq := by simp
  right_eq := by simp
  bracketOf := fun _ _ _ => 0
  left_le_index := by
    intro c hleft hright
    simp [Fin.castSucc]
    exact hleft
  index_lt_right := by
    intro c hleft hright
    simpa using hright
  cdf_increment_lt := by
    intro cell
    fin_cases cell
    simpa using hinc

/--
The two-cell middle partition obtained by splitting a bounded interval at a
strict interior cutpoint.

This is the first nontrivial finite-partition constructor for the
distribution-dependent middle-CDF grid used in the Glivenko-Cantelli route.
-/
noncomputable def twoCell
    {μ : Measure ℝ} {epsilon a c b : ℝ} (hac : a < c) (hcb : c < b)
    (hleft :
      Function.leftLim (ProbabilityTheory.cdf μ) c -
        ProbabilityTheory.cdf μ a < epsilon)
    (hright :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ c < epsilon) :
    SuppliedRealMiddleCDFPartition μ epsilon a b 2 where
  endpoint := fun endpointIndex =>
    if endpointIndex = 0 then a else if endpointIndex = 1 then c else b
  strictMono := by
    intro i j hij
    fin_cases i <;> fin_cases j <;> simp at hij ⊢
    · exact hac
    · exact hac.trans hcb
    · exact hcb
  left_eq := by simp
  right_eq := by simp
  bracketOf := fun x _ _ => if x < c then 0 else 1
  left_le_index := by
    intro x hleftBound hrightBound
    by_cases hxc : x < c
    · simp [hxc, Fin.castSucc]
      exact hleftBound
    · have hcx : c ≤ x := le_of_not_gt hxc
      simp [hxc, Fin.castSucc]
      exact hcx
  index_lt_right := by
    intro x hleftBound hrightBound
    by_cases hxc : x < c
    · simp [hxc]
    · simp [hxc]
      exact hrightBound
  cdf_increment_lt := by
    intro cell
    fin_cases cell <;> simp [hleft, hright]

/--
Append one small CDF-increment cell to the right of a supplied middle
partition.

This is the induction step for building longer distribution-dependent middle
partitions once a sequence of cutpoints has been chosen.
-/
noncomputable def snocCell
    {μ : Measure ℝ} {epsilon a c b : ℝ} {middleCells : ℕ}
    (partition : SuppliedRealMiddleCDFPartition μ epsilon a c middleCells)
    (hcb : c < b)
    (hinc :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ c < epsilon) :
    SuppliedRealMiddleCDFPartition μ epsilon a b (middleCells + 1) where
  endpoint := Fin.snoc partition.endpoint b
  strictMono := by
    intro i j hij
    cases j using Fin.lastCases with
    | last =>
        have hi_ne : i ≠ Fin.last (middleCells + 1) := Fin.ne_last_of_lt hij
        rcases Fin.eq_castSucc_of_ne_last hi_ne with ⟨i', rfl⟩
        rw [Fin.snoc_castSucc, Fin.snoc_last]
        by_cases hi' : i' = Fin.last middleCells
        · rw [hi', partition.right_eq]
          exact hcb
        · have hi'_lt_last : i' < Fin.last middleCells :=
            Fin.lt_last_iff_ne_last.mpr hi'
          have hp_lt_c : partition.endpoint i' < c := by
            simpa [partition.right_eq] using partition.strictMono hi'_lt_last
          exact hp_lt_c.trans hcb
    | cast j' =>
        have hj_lt_last : j'.castSucc < Fin.last (middleCells + 1) :=
          Fin.castSucc_lt_last j'
        have hi_lt_last : i < Fin.last (middleCells + 1) := lt_trans hij hj_lt_last
        have hi_ne : i ≠ Fin.last (middleCells + 1) := Fin.ne_last_of_lt hi_lt_last
        rcases Fin.eq_castSucc_of_ne_last hi_ne with ⟨i', rfl⟩
        rw [Fin.snoc_castSucc, Fin.snoc_castSucc]
        exact partition.strictMono (Fin.castSucc_lt_castSucc_iff.mp hij)
  left_eq := by
    simpa [Fin.snoc] using partition.left_eq
  right_eq := by
    rw [Fin.snoc_last]
  bracketOf := fun x hleft hright =>
    if hxc : x < c then Fin.castSucc (partition.bracketOf x hleft hxc)
    else Fin.last middleCells
  left_le_index := by
    intro x hleft hright
    by_cases hxc : x < c
    · simp [hxc, Fin.snoc_castSucc]
      exact partition.left_le_index x hleft hxc
    · have hcx : c ≤ x := le_of_not_gt hxc
      simp [hxc, Fin.snoc_castSucc, partition.right_eq]
      exact hcx
  index_lt_right := by
    intro x hleft hright
    by_cases hxc : x < c
    · simp [hxc]
      rw [← Fin.castSucc_succ, Fin.snoc_castSucc]
      exact partition.index_lt_right x hleft hxc
    · simp [hxc, Fin.snoc_last]
      exact hright
  cdf_increment_lt := by
    intro cell
    by_cases hlast : cell = Fin.last middleCells
    · rw [hlast]
      simp [Fin.snoc_castSucc, Fin.snoc_last, partition.right_eq]
      exact hinc
    · rcases Fin.eq_castSucc_of_ne_last hlast with ⟨cell', rfl⟩
      rw [← Fin.castSucc_succ, Fin.snoc_castSucc, Fin.snoc_castSucc]
      exact partition.cdf_increment_lt cell'

/-- Adjacent endpoints in a supplied middle partition are strictly ordered. -/
theorem endpoint_left_lt_right
    {μ : Measure ℝ} {epsilon a b : ℝ} {middleCells : ℕ}
    (partition : SuppliedRealMiddleCDFPartition μ epsilon a b middleCells)
    (cell : Fin middleCells) :
    partition.endpoint (Fin.castSucc cell) < partition.endpoint (Fin.succ cell) :=
  partition.strictMono Fin.castSucc_lt_succ

/--
The CDF increment field of a supplied middle partition gives the real measure
width bound for the corresponding open interval cell.
-/
theorem cell_width_lt
    {μ : Measure ℝ} [IsProbabilityMeasure μ] {epsilon a b : ℝ} {middleCells : ℕ}
    (partition : SuppliedRealMiddleCDFPartition μ epsilon a b middleCells)
    (cell : Fin middleCells) :
    μ.real (Set.Ioo (partition.endpoint (Fin.castSucc cell))
      (partition.endpoint (Fin.succ cell))) < epsilon :=
  measureReal_Ioo_lt_of_cdf_leftLim_sub_lt μ
    (partition.endpoint_left_lt_right cell)
    (partition.cdf_increment_lt cell)

end SuppliedRealMiddleCDFPartition

/--
If the whole bounded interval already has small CDF increment, a one-cell
middle CDF partition exists.
-/
theorem exists_realMiddleCDFPartition_oneCell_of_cdf_leftLim_sub_lt
    {μ : Measure ℝ} {epsilon a b : ℝ} (hab : a < b)
    (hinc :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ a < epsilon) :
    ∃ middleCells, Nonempty
      (SuppliedRealMiddleCDFPartition μ epsilon a b middleCells) :=
  ⟨1, ⟨SuppliedRealMiddleCDFPartition.oneCell hab hinc⟩⟩

/--
If an interior cutpoint splits a bounded interval into two small CDF-increment
pieces, a two-cell middle CDF partition exists.
-/
theorem exists_realMiddleCDFPartition_twoCell_of_cdf_leftLim_sub_lt
    {μ : Measure ℝ} {epsilon a c b : ℝ} (hac : a < c) (hcb : c < b)
    (hleft :
      Function.leftLim (ProbabilityTheory.cdf μ) c -
        ProbabilityTheory.cdf μ a < epsilon)
    (hright :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ c < epsilon) :
    ∃ middleCells, Nonempty
      (SuppliedRealMiddleCDFPartition μ epsilon a b middleCells) :=
  ⟨2, ⟨SuppliedRealMiddleCDFPartition.twoCell hac hcb hleft hright⟩⟩

/--
Appending one small CDF-increment cell to an existing supplied middle partition
gives a larger supplied middle partition.
-/
theorem exists_realMiddleCDFPartition_snocCell_of_partition
    {μ : Measure ℝ} {epsilon a c b : ℝ} {middleCells : ℕ}
    (partition : SuppliedRealMiddleCDFPartition μ epsilon a c middleCells)
    (hcb : c < b)
    (hinc :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ c < epsilon) :
    ∃ nextCells, Nonempty
      (SuppliedRealMiddleCDFPartition μ epsilon a b nextCells) :=
  ⟨middleCells + 1, ⟨SuppliedRealMiddleCDFPartition.snocCell partition hcb hinc⟩⟩

/--
Existence form of the right-append constructor for supplied middle CDF
partitions.
-/
theorem exists_realMiddleCDFPartition_snocCell_of_exists
    {μ : Measure ℝ} {epsilon a c b : ℝ}
    (partitionExists :
      ∃ middleCells, Nonempty
        (SuppliedRealMiddleCDFPartition μ epsilon a c middleCells))
    (hcb : c < b)
    (hinc :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ c < epsilon) :
    ∃ nextCells, Nonempty
      (SuppliedRealMiddleCDFPartition μ epsilon a b nextCells) := by
  rcases partitionExists with ⟨middleCells, partitionNonempty⟩
  exact partitionNonempty.elim fun partition =>
    exists_realMiddleCDFPartition_snocCell_of_partition partition hcb hinc

/--
A finite chain of real cutpoints whose adjacent CDF left-limit increments are
all below the requested radius.

This is the proof target for the future quantile construction in the
Glivenko-Cantelli route: once the source proof has produced such a chain,
`exists_realMiddleCDFPartition_of_cutpoint_chain` turns it into the supplied
middle partition consumed by the endpoint-grid layer.
-/
inductive SuppliedRealMiddleCDFPartitionChain
    (μ : Measure ℝ) (epsilon a : ℝ) : ℝ -> Prop where
  | one {b : ℝ} (hab : a < b)
      (hinc :
        Function.leftLim (ProbabilityTheory.cdf μ) b -
          ProbabilityTheory.cdf μ a < epsilon) :
      SuppliedRealMiddleCDFPartitionChain μ epsilon a b
  | snoc {c b : ℝ}
      (chain : SuppliedRealMiddleCDFPartitionChain μ epsilon a c)
      (hcb : c < b)
      (hinc :
        Function.leftLim (ProbabilityTheory.cdf μ) b -
          ProbabilityTheory.cdf μ c < epsilon) :
      SuppliedRealMiddleCDFPartitionChain μ epsilon a b

/--
A strict finite endpoint grid with small adjacent CDF left-limit increments
produces a cutpoint chain.

This is the endpoint-list handoff for the future quantile construction in
Durrett Theorem 2.4.9: after choosing finitely many real cutpoints, it is
enough to prove strict order and adjacent increment bounds.
-/
theorem SuppliedRealMiddleCDFPartitionChain.of_endpointGrid
    {μ : Measure ℝ} {epsilon : ℝ} {cells : ℕ}
    (endpoint : Fin (cells + 2) -> ℝ)
    (hstrict : StrictMono endpoint)
    (hinc : ∀ cell : Fin (cells + 1),
      Function.leftLim (ProbabilityTheory.cdf μ) (endpoint (Fin.succ cell)) -
        ProbabilityTheory.cdf μ (endpoint (Fin.castSucc cell)) < epsilon) :
    SuppliedRealMiddleCDFPartitionChain μ epsilon (endpoint 0)
      (endpoint (Fin.last (cells + 1))) := by
  induction cells with
  | zero =>
      refine SuppliedRealMiddleCDFPartitionChain.one ?_ ?_
      · simpa using hstrict (show (0 : Fin 2) < Fin.last 1 by decide)
      · simpa using hinc (0 : Fin 1)
  | succ cells ih =>
      let endpoint' : Fin (cells + 2) -> ℝ := fun i => endpoint (Fin.castSucc i)
      have hstrict' : StrictMono endpoint' := by
        intro i j hij
        exact hstrict (Fin.castSucc_lt_castSucc_iff.mpr hij)
      have hinc' : ∀ cell : Fin (cells + 1),
          Function.leftLim (ProbabilityTheory.cdf μ) (endpoint' (Fin.succ cell)) -
            ProbabilityTheory.cdf μ (endpoint' (Fin.castSucc cell)) < epsilon := by
        intro cell
        simpa [endpoint'] using hinc (Fin.castSucc cell)
      have hchain := ih endpoint' hstrict' hinc'
      refine SuppliedRealMiddleCDFPartitionChain.snoc hchain ?_ ?_
      · simpa [endpoint'] using hstrict (Fin.castSucc_lt_last (Fin.last (cells + 1)))
      · simpa [endpoint'] using hinc (Fin.last (cells + 1))

/--
Every finite small-increment cutpoint chain supplies a bounded middle CDF
partition.
-/
theorem exists_realMiddleCDFPartition_of_cutpoint_chain
    {μ : Measure ℝ} {epsilon a b : ℝ}
    (chain : SuppliedRealMiddleCDFPartitionChain μ epsilon a b) :
    ∃ middleCells, Nonempty
      (SuppliedRealMiddleCDFPartition μ epsilon a b middleCells) := by
  induction chain with
  | one hab hinc =>
      exact exists_realMiddleCDFPartition_oneCell_of_cdf_leftLim_sub_lt hab hinc
  | snoc chain hcb hinc ih =>
      exact exists_realMiddleCDFPartition_snocCell_of_exists ih hcb hinc

/--
Finite Borel measures on the real line have finite real cutpoints with
arbitrarily small lower and upper tails.

This is the first distribution-dependent ingredient for the endpoint-grid
construction in VdV&W Example 2.4.2.
-/
theorem exists_real_tails_lt_of_isFiniteMeasure
    (μ : Measure ℝ) [IsFiniteMeasure μ] {epsilon : ℝ} (hepsilon : 0 < epsilon) :
    ∃ a b : ℝ, μ.real (Set.Iio a) < epsilon ∧ μ.real (Set.Ioi b) < epsilon := by
  have hdelta_pos : 0 < ENNReal.ofReal (epsilon / 2) :=
    ENNReal.ofReal_pos.mpr (half_pos hepsilon)
  have hTight : IsTightMeasureSet ({μ} : Set (Measure ℝ)) :=
    isTightMeasureSet_singleton (μ := μ)
  rcases
      (isTightMeasureSet_iff_exists_isCompact_measure_compl_le.mp hTight)
        (ENNReal.ofReal (epsilon / 2)) hdelta_pos with
    ⟨K, hKcompact, hKmeasure⟩
  let a : ℝ := sInf K
  let b : ℝ := sSup K
  refine ⟨a, b, ?_, ?_⟩
  · have hsubset : Set.Iio a ⊆ Kᶜ := by
      intro x hx hxK
      have hxIcc : x ∈ Set.Icc (sInf K) (sSup K) :=
        hKcompact.isBounded.subset_Icc_sInf_sSup hxK
      exact (not_le_of_gt hx) hxIcc.1
    have hle : μ.real (Set.Iio a) ≤ (ENNReal.ofReal (epsilon / 2)).toReal := by
      calc
        μ.real (Set.Iio a) ≤ μ.real Kᶜ := measureReal_mono hsubset
        _ ≤ (ENNReal.ofReal (epsilon / 2)).toReal :=
          ENNReal.toReal_mono ENNReal.ofReal_ne_top (hKmeasure μ rfl)
    rw [ENNReal.toReal_ofReal (by linarith : 0 ≤ epsilon / 2)] at hle
    linarith
  · have hsubset : Set.Ioi b ⊆ Kᶜ := by
      intro x hx hxK
      have hxIcc : x ∈ Set.Icc (sInf K) (sSup K) :=
        hKcompact.isBounded.subset_Icc_sInf_sSup hxK
      exact (not_le_of_gt hx) hxIcc.2
    have hle : μ.real (Set.Ioi b) ≤ (ENNReal.ofReal (epsilon / 2)).toReal := by
      calc
        μ.real (Set.Ioi b) ≤ μ.real Kᶜ := measureReal_mono hsubset
        _ ≤ (ENNReal.ofReal (epsilon / 2)).toReal :=
          ENNReal.toReal_mono ENNReal.ofReal_ne_top (hKmeasure μ rfl)
    rw [ENNReal.toReal_ofReal (by linarith : 0 ≤ epsilon / 2)] at hle
    linarith

/-- Finite extended endpoints recover the ordinary closed half-line indicator. -/
theorem eRealClosedHalfLineIndicator_coe (c : ℝ) :
    eRealClosedHalfLineIndicator (c : EReal) = realHalfLineIndicator c := by
  funext x
  by_cases hx : x ≤ c
  · simp [eRealClosedHalfLineIndicator, realHalfLineIndicator, hx]
  · simp [eRealClosedHalfLineIndicator, realHalfLineIndicator, hx]

/-- Finite extended endpoints recover the ordinary open half-line indicator. -/
theorem eRealOpenHalfLineIndicator_coe (c : ℝ) :
    eRealOpenHalfLineIndicator (c : EReal) = realOpenHalfLineIndicator c := by
  funext x
  by_cases hx : x < c
  · simp [eRealOpenHalfLineIndicator, realOpenHalfLineIndicator, hx]
  · simp [eRealOpenHalfLineIndicator, realOpenHalfLineIndicator, hx]

/-- The closed lower half-line at `-∞` is empty on real observations. -/
theorem eRealClosedHalfLineIndicator_bot :
    eRealClosedHalfLineIndicator ⊥ = fun _ => (0 : ℝ) := by
  funext x
  simp [eRealClosedHalfLineIndicator]

/-- The open lower half-line at `-∞` is empty on real observations. -/
theorem eRealOpenHalfLineIndicator_bot :
    eRealOpenHalfLineIndicator ⊥ = fun _ => (0 : ℝ) := by
  funext x
  simp [eRealOpenHalfLineIndicator]

/-- The closed lower half-line at `∞` is all real observations. -/
theorem eRealClosedHalfLineIndicator_top :
    eRealClosedHalfLineIndicator ⊤ = fun _ => (1 : ℝ) := by
  funext x
  simp [eRealClosedHalfLineIndicator]

/-- The open lower half-line at `∞` is all real observations. -/
theorem eRealOpenHalfLineIndicator_top :
    eRealOpenHalfLineIndicator ⊤ = fun _ => (1 : ℝ) := by
  funext x
  simp [eRealOpenHalfLineIndicator]

/--
For `a < b`, the absolute endpoint gap of the extended-endpoint bracket is
the indicator of the extended-open cell `{x | a < (x : EReal) ∧ (x : EReal) < b}`.
-/
theorem abs_eRealHalfLineBracket_endpoint_gap_eq_indicator_openCell
    {a b : EReal} (hab : a < b) :
    (fun x =>
      |(eRealHalfLineBracket a b).upper x -
        (eRealHalfLineBracket a b).lower x|) =
      Set.indicator (eRealOpenCell a b) (fun _ => (1 : ℝ)) := by
  funext x
  by_cases hax : a < (x : EReal)
  · have hnot_lower : ¬ (x : EReal) ≤ a := not_le.mpr hax
    by_cases hxb : (x : EReal) < b
    · simp [eRealHalfLineBracket, eRealClosedHalfLineIndicator,
        eRealOpenHalfLineIndicator, eRealOpenCell, hnot_lower, hax, hxb]
    · simp [eRealHalfLineBracket, eRealClosedHalfLineIndicator,
        eRealOpenHalfLineIndicator, eRealOpenCell, hnot_lower, hax, hxb]
  · have hxa : (x : EReal) ≤ a := le_of_not_gt hax
    have hxb : (x : EReal) < b := lt_of_le_of_lt hxa hab
    simp [eRealHalfLineBracket, eRealClosedHalfLineIndicator,
      eRealOpenHalfLineIndicator, eRealOpenCell, hxa, hax, hxb]

/--
For `a < b`, the `L1(P)` width of the extended-endpoint half-line bracket is
the real measure of the extended-open cell between the endpoints.
-/
theorem eRealHalfLineBracket_l1Width_eq_measureReal_openCell
    (μ : Measure ℝ) {a b : EReal} (hab : a < b) :
    (eRealHalfLineBracket a b).l1Width μ = μ.real (eRealOpenCell a b) := by
  dsimp [FunctionBracket.l1Width]
  rw [abs_eRealHalfLineBracket_endpoint_gap_eq_indicator_openCell hab]
  exact integral_indicator_one (measurableSet_eRealOpenCell a b)

/-- Extended-endpoint closed half-line indicators are integrable under finite measures. -/
theorem integrable_eRealClosedHalfLineIndicator
    (μ : Measure ℝ) [IsFiniteMeasure μ] (c : EReal) :
    Integrable (eRealClosedHalfLineIndicator c) μ := by
  induction c using EReal.rec with
  | bot =>
      rw [eRealClosedHalfLineIndicator_bot]
      exact integrable_const (0 : ℝ)
  | coe c =>
      rw [eRealClosedHalfLineIndicator_coe]
      exact integrable_realHalfLineIndicator μ c
  | top =>
      rw [eRealClosedHalfLineIndicator_top]
      exact integrable_const (1 : ℝ)

/-- Extended-endpoint open half-line indicators are integrable under finite measures. -/
theorem integrable_eRealOpenHalfLineIndicator
    (μ : Measure ℝ) [IsFiniteMeasure μ] (c : EReal) :
    Integrable (eRealOpenHalfLineIndicator c) μ := by
  induction c using EReal.rec with
  | bot =>
      rw [eRealOpenHalfLineIndicator_bot]
      exact integrable_const (0 : ℝ)
  | coe c =>
      rw [eRealOpenHalfLineIndicator_coe]
      exact integrable_realOpenHalfLineIndicator μ c
  | top =>
      rw [eRealOpenHalfLineIndicator_top]
      exact integrable_const (1 : ℝ)

/--
If `a ≤ c < b` in the extended real line, then the finite real half-line
indicator `1{(-∞, c]}` lies in the extended-endpoint bracket.
-/
theorem eRealHalfLineBracket_mem_realIndicator_of_le_lt
    {a b : EReal} {c : ℝ} (hac : a ≤ (c : EReal)) (hcb : (c : EReal) < b) :
    (eRealHalfLineBracket a b).Mem (realHalfLineIndicator c) := by
  intro x
  constructor
  · by_cases hxa : (x : EReal) ≤ a
    · have hxc : x ≤ c := EReal.coe_le_coe_iff.mp (hxa.trans hac)
      simp [eRealHalfLineBracket, eRealClosedHalfLineIndicator,
        realHalfLineIndicator, hxa, hxc]
    · by_cases hxc : x ≤ c
      · simp [eRealHalfLineBracket, eRealClosedHalfLineIndicator,
          realHalfLineIndicator, hxa, hxc]
      · simp [eRealHalfLineBracket, eRealClosedHalfLineIndicator,
          realHalfLineIndicator, hxa, hxc]
  · by_cases hxc : x ≤ c
    · have hxcE : (x : EReal) ≤ (c : EReal) := EReal.coe_le_coe hxc
      have hxb : (x : EReal) < b := lt_of_le_of_lt hxcE hcb
      simp [eRealHalfLineBracket, eRealOpenHalfLineIndicator,
        realHalfLineIndicator, hxc, hxb]
    · by_cases hxb : (x : EReal) < b
      · simp [eRealHalfLineBracket, eRealOpenHalfLineIndicator,
          realHalfLineIndicator, hxc, hxb]
      · simp [eRealHalfLineBracket, eRealOpenHalfLineIndicator,
          realHalfLineIndicator, hxc, hxb]

/--
A supplied finite extended-real grid for half-line brackets.

The textbook grid in Example 2.4.2 has endpoints `-∞ = t₀` and `tₘ = ∞`.
This proof-carrying structure separates that endpoint issue from the later
problem of constructing such a grid from an arbitrary distribution.
-/
structure SuppliedERealHalfLineGrid
    (μ : Measure ℝ) (epsilon : ℝ) (cardinality : ℕ) where
  left : Fin cardinality -> EReal
  right : Fin cardinality -> EReal
  bracketOf : ℝ -> Fin cardinality
  left_lt_right : ∀ bracketIndex, left bracketIndex < right bracketIndex
  left_le_index : ∀ c : ℝ, left (bracketOf c) ≤ (c : EReal)
  index_lt_right : ∀ c : ℝ, (c : EReal) < right (bracketOf c)
  cell_width_lt :
    ∀ bracketIndex, μ.real (eRealOpenCell (left bracketIndex)
      (right bracketIndex)) < epsilon

/--
A supplied finite extended-real endpoint grid for half-line brackets.

This records the textbook-style adjacent endpoints
`t₀, ..., t_m` and a proof that every real cutoff lies in one adjacent cell.
Constructing such endpoint data from an arbitrary distribution is the next
substantive step for Example 2.4.2.
-/
structure SuppliedERealHalfLineEndpointGrid
    (μ : Measure ℝ) (epsilon : ℝ) (cellCount : ℕ) where
  endpoint : Fin (cellCount + 1) -> EReal
  bracketOf : ℝ -> Fin cellCount
  left_lt_right :
    ∀ cell : Fin cellCount, endpoint (Fin.castSucc cell) < endpoint (Fin.succ cell)
  left_le_index :
    ∀ c : ℝ, endpoint (Fin.castSucc (bracketOf c)) ≤ (c : EReal)
  index_lt_right :
    ∀ c : ℝ, (c : EReal) < endpoint (Fin.succ (bracketOf c))
  cell_width_lt :
    ∀ cell : Fin cellCount, μ.real (eRealOpenCell (endpoint (Fin.castSucc cell))
      (endpoint (Fin.succ cell))) < epsilon

namespace SuppliedERealHalfLineEndpointGrid

/--
A supplied adjacent-endpoint grid yields the more primitive supplied-grid
structure used by the bracketing-number layer.
-/
def toSuppliedERealHalfLineGrid
    {μ : Measure ℝ} {epsilon : ℝ} {cellCount : ℕ}
    (grid : SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) :
    SuppliedERealHalfLineGrid μ epsilon cellCount where
  left := fun cell => grid.endpoint (Fin.castSucc cell)
  right := fun cell => grid.endpoint (Fin.succ cell)
  bracketOf := grid.bracketOf
  left_lt_right := grid.left_lt_right
  left_le_index := grid.left_le_index
  index_lt_right := grid.index_lt_right
  cell_width_lt := grid.cell_width_lt

/--
A supplied adjacent-endpoint grid at a smaller radius is also a supplied
adjacent-endpoint grid at any larger radius.
-/
def of_le_epsilon
    {μ : Measure ℝ} {epsilon smallerEpsilon : ℝ} {cellCount : ℕ}
    (grid : SuppliedERealHalfLineEndpointGrid μ smallerEpsilon cellCount)
    (hsmall : smallerEpsilon ≤ epsilon) :
    SuppliedERealHalfLineEndpointGrid μ epsilon cellCount where
  endpoint := grid.endpoint
  bracketOf := grid.bracketOf
  left_lt_right := grid.left_lt_right
  left_le_index := grid.left_le_index
  index_lt_right := grid.index_lt_right
  cell_width_lt := fun cell =>
    lt_of_lt_of_le (grid.cell_width_lt cell) hsmall

/--
Finite adjacent-endpoint grid existence is monotone in the requested radius.
-/
theorem exists_of_le_epsilon
    {μ : Measure ℝ} {epsilon smallerEpsilon : ℝ}
    (hsmall : smallerEpsilon ≤ epsilon)
    (gridExists :
      ∃ cellCount, Nonempty
        (SuppliedERealHalfLineEndpointGrid μ smallerEpsilon cellCount)) :
    ∃ cellCount, Nonempty
      (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) := by
  rcases gridExists with ⟨cellCount, gridNonempty⟩
  exact ⟨cellCount, gridNonempty.map fun grid => grid.of_le_epsilon hsmall⟩

/--
Lift a strictly increasing finite real endpoint sequence to an extended-real
adjacent-endpoint grid.

This is the compact-core assembly layer for Example 2.4.2; the infinite tails
are handled by adjoining `⊥` and `⊤` in separate constructors.
-/
def ofFiniteRealEndpoints
    {μ : Measure ℝ} {epsilon : ℝ} {cellCount : ℕ}
    (endpoint : Fin (cellCount + 1) -> ℝ)
    (hendpoint_strictMono : StrictMono endpoint)
    (bracketOf : ℝ -> Fin cellCount)
    (left_le_index :
      ∀ c : ℝ, endpoint (Fin.castSucc (bracketOf c)) ≤ c)
    (index_lt_right :
      ∀ c : ℝ, c < endpoint (Fin.succ (bracketOf c)))
    (cell_width_lt :
      ∀ cell : Fin cellCount,
        μ.real (Set.Ioo (endpoint (Fin.castSucc cell))
          (endpoint (Fin.succ cell))) < epsilon) :
    SuppliedERealHalfLineEndpointGrid μ epsilon cellCount where
  endpoint := fun endpointIndex => (endpoint endpointIndex : EReal)
  bracketOf := bracketOf
  left_lt_right := by
    intro cell
    exact EReal.coe_lt_coe_iff.mpr
      (hendpoint_strictMono
        (show Fin.castSucc cell < Fin.succ cell from Fin.castSucc_lt_succ))
  left_le_index := by
    intro c
    exact EReal.coe_le_coe (left_le_index c)
  index_lt_right := by
    intro c
    exact EReal.coe_lt_coe_iff.mpr (index_lt_right c)
  cell_width_lt := by
    intro cell
    simpa [measureReal_eRealOpenCell_coe_coe] using cell_width_lt cell

/--
Adjoin `⊥` and `⊤` around a finite real endpoint sequence.

For `middleCells = m`, this builds the endpoint tuple
`⊥, t₀, ..., t_m, ⊤`, indexed as a tuple of length `m + 3`.
-/
noncomputable def endpointWithRealTails
    {middleCells : ℕ} (endpoint : Fin (middleCells + 1) -> ℝ) :
    Fin (middleCells + 3) -> EReal :=
  Fin.cons (⊥ : EReal)
    (Fin.snoc (fun i : Fin (middleCells + 1) => (endpoint i : EReal)) ⊤)

/--
Adjoin lower and upper tail cells around a supplied bounded middle CDF
partition.

This is the endpoint-grid assembly layer for VdV&W Example 2.4.2: lower tail,
all bounded middle cells, and upper tail become one extended-real adjacent
endpoint grid.
-/
noncomputable def ofMiddleCDFPartitionWithTails
    {μ : Measure ℝ} [IsProbabilityMeasure μ]
    {epsilon a b : ℝ} {middleCells : ℕ}
    (hleftTail : μ.real (Set.Iio a) < epsilon)
    (hrightTail : μ.real (Set.Ioi b) < epsilon)
    (partition : SuppliedRealMiddleCDFPartition μ epsilon a b middleCells) :
    SuppliedERealHalfLineEndpointGrid μ epsilon (middleCells + 2) where
  endpoint := endpointWithRealTails partition.endpoint
  bracketOf := fun c =>
    if hca : c < a then 0
    else if hcb : c < b then
      Fin.succ (Fin.castSucc (partition.bracketOf c (le_of_not_gt hca) hcb))
    else Fin.last (middleCells + 1)
  left_lt_right := by
    intro cell
    refine Fin.cases ?llrZero ?llrRest cell
    · simp [endpointWithRealTails, partition.left_eq]
    · intro rest
      refine Fin.lastCases ?llrLast ?llrMiddle rest
      · rw [endpointWithRealTails]
        rw [Fin.castSucc_succ]
        rw [Fin.cons_succ]
        rw [Fin.snoc_castSucc]
        simp [partition.right_eq]
      · intro middleCell
        dsimp [endpointWithRealTails]
        rw [Fin.cons_succ]
        rw [Fin.cons_succ]
        rw [← Fin.castSucc_succ middleCell]
        rw [Fin.snoc_castSucc]
        rw [Fin.snoc_castSucc]
        exact EReal.coe_lt_coe_iff.mpr
          (partition.endpoint_left_lt_right middleCell)
  left_le_index := by
    intro c
    by_cases hca : c < a
    · simp [hca, endpointWithRealTails]
    · by_cases hcb : c < b
      · dsimp [endpointWithRealTails]
        simp [hca, hcb]
        exact partition.left_le_index c (le_of_not_gt hca) hcb
      · have hbc : b ≤ c := le_of_not_gt hcb
        have hidx : Fin.castSucc (Fin.last (middleCells + 1)) =
            Fin.castSucc (Fin.succ (Fin.last middleCells)) := by
          ext
          simp
        dsimp [endpointWithRealTails]
        simp [hca, hcb]
        rw [hidx]
        rw [Fin.castSucc_succ]
        rw [Fin.cons_succ]
        rw [Fin.snoc_castSucc]
        rw [partition.right_eq]
        exact EReal.coe_le_coe hbc
  index_lt_right := by
    intro c
    by_cases hca : c < a
    · simp [hca, endpointWithRealTails, partition.left_eq]
    · by_cases hcb : c < b
      · dsimp [endpointWithRealTails]
        simp [hca, hcb]
        rw [← Fin.castSucc_succ
          (partition.bracketOf c (le_of_not_gt hca) hcb)]
        rw [Fin.snoc_castSucc]
        exact EReal.coe_lt_coe_iff.mpr
          (partition.index_lt_right c (le_of_not_gt hca) hcb)
      · simp [hca, hcb, endpointWithRealTails]
  cell_width_lt := by
    intro cell
    refine Fin.cases ?cwZero ?cwRest cell
    · simp [endpointWithRealTails, partition.left_eq,
        measureReal_eRealOpenCell_bot_coe, hleftTail]
    · intro rest
      refine Fin.lastCases ?cwLast ?cwMiddle rest
      · rw [endpointWithRealTails]
        rw [Fin.castSucc_succ]
        rw [Fin.cons_succ]
        rw [Fin.snoc_castSucc]
        simpa [partition.right_eq, measureReal_eRealOpenCell_coe_top] using
          hrightTail
      · intro middleCell
        dsimp [endpointWithRealTails]
        rw [Fin.cons_succ]
        rw [Fin.cons_succ]
        rw [← Fin.castSucc_succ middleCell]
        rw [Fin.snoc_castSucc]
        rw [Fin.snoc_castSucc]
        simpa [measureReal_eRealOpenCell_coe_coe] using
          (partition.cell_width_lt middleCell)

/--
Tail bounds plus a supplied bounded middle CDF partition give finite
extended-real adjacent endpoint-grid existence.
-/
theorem exists_endpointGrid_of_realMiddleCDFPartition
    (μ : Measure ℝ) [IsProbabilityMeasure μ] {epsilon a b : ℝ}
    {middleCells : ℕ}
    (hleftTail : μ.real (Set.Iio a) < epsilon)
    (hrightTail : μ.real (Set.Ioi b) < epsilon)
    (partition : SuppliedRealMiddleCDFPartition μ epsilon a b middleCells) :
    ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) :=
  ⟨middleCells + 2,
    ⟨ofMiddleCDFPartitionWithTails hleftTail hrightTail partition⟩⟩

/--
Uniform bounded middle CDF partitions imply full endpoint-grid existence at
every positive radius.

Finite tails are supplied by tightness of finite Borel measures on `ℝ`; the
tail cutpoints are widened to ensure a strictly ordered bounded middle
interval.
-/
theorem exists_forall_of_forall_realMiddleCDFPartition
    (μ : Measure ℝ) [IsProbabilityMeasure μ]
    (middlePartitionExists :
      ∀ {epsilon a b : ℝ}, 0 < epsilon -> a < b ->
        ∃ middleCells, Nonempty
          (SuppliedRealMiddleCDFPartition μ epsilon a b middleCells)) :
    ∀ epsilon, 0 < epsilon ->
      ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) := by
  intro epsilon hepsilon
  rcases exists_real_tails_lt_of_isFiniteMeasure μ hepsilon with
    ⟨a, b, hleftTail, hrightTail⟩
  let lower : ℝ := min a b - 1
  let upper : ℝ := max a b + 1
  have hlower_le_a : lower ≤ a := by
    dsimp [lower]
    have hmin : min a b ≤ a := min_le_left a b
    linarith
  have hb_le_upper : b ≤ upper := by
    dsimp [upper]
    have hmax : b ≤ max a b := le_max_right a b
    linarith
  have hleftTail' : μ.real (Set.Iio lower) < epsilon := by
    have hsubset : Set.Iio lower ⊆ Set.Iio a := by
      intro x hx
      exact lt_of_lt_of_le hx hlower_le_a
    exact lt_of_le_of_lt (measureReal_mono hsubset) hleftTail
  have hrightTail' : μ.real (Set.Ioi upper) < epsilon := by
    have hsubset : Set.Ioi upper ⊆ Set.Ioi b := by
      intro x hx
      exact lt_of_le_of_lt hb_le_upper hx
    exact lt_of_le_of_lt (measureReal_mono hsubset) hrightTail
  have hlower_lt_upper : lower < upper := by
    dsimp [lower, upper]
    have hle : min a b ≤ max a b :=
      le_trans (min_le_left a b) (le_max_left a b)
    linarith
  rcases middlePartitionExists hepsilon hlower_lt_upper with
    ⟨middleCells, partitionNonempty⟩
  exact partitionNonempty.elim fun partition =>
    exists_endpointGrid_of_realMiddleCDFPartition μ hleftTail' hrightTail' partition

/--
The one-cell textbook-style extended endpoint grid `-∞ < ∞`.

This is the endpoint-grid analogue of `SuppliedERealHalfLineGrid.singleCell`;
it is the base case for Example 2.4.2 when the requested radius is larger
than the total mass.
-/
noncomputable def singleCell
    (μ : Measure ℝ) {epsilon : ℝ} (hwidth : μ.real Set.univ < epsilon) :
    SuppliedERealHalfLineEndpointGrid μ epsilon 1 where
  endpoint := fun endpointIndex =>
    if endpointIndex = 0 then (⊥ : EReal) else ⊤
  bracketOf := fun _ => 0
  left_lt_right := by
    intro cell
    fin_cases cell
    simp
  left_le_index := by
    intro _c
    simp
  index_lt_right := by
    intro _c
    simp
  cell_width_lt := by
    intro cell
    fin_cases cell
    simp [eRealOpenCell_bot_top, hwidth]

/--
If the requested radius exceeds the total mass, the one-cell endpoint grid is
a supplied finite adjacent-endpoint grid.
-/
theorem exists_singleCell_of_measureReal_univ_lt
    (μ : Measure ℝ) {epsilon : ℝ} (hwidth : μ.real Set.univ < epsilon) :
    ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) :=
  ⟨1, ⟨singleCell μ hwidth⟩⟩

/--
The three-cell textbook-style endpoint grid
`-∞ < a < b < ∞`.

This packages the simplest nontrivial finite endpoint grid: a lower tail, a
bounded middle cell, and an upper tail.
-/
noncomputable def threeCell
    (μ : Measure ℝ) {epsilon a b : ℝ}
    (hab : a < b)
    (hleft : μ.real (Set.Iio a) < epsilon)
    (hmiddle : μ.real (Set.Ioo a b) < epsilon)
    (hright : μ.real (Set.Ioi b) < epsilon) :
    SuppliedERealHalfLineEndpointGrid μ epsilon 3 where
  endpoint := fun endpointIndex =>
    if endpointIndex = 0 then (⊥ : EReal)
    else if endpointIndex = 1 then (a : EReal)
    else if endpointIndex = 2 then (b : EReal)
    else ⊤
  bracketOf := fun c =>
    if _hca : c < a then 0 else if _hcb : c < b then 1 else 2
  left_lt_right := by
    intro cell
    fin_cases cell <;> simp [hab]
  left_le_index := by
    intro c
    by_cases hca : c < a
    · simp [hca]
    · by_cases hcb : c < b
      · have hac : a ≤ c := le_of_not_gt hca
        simp [hca, hcb, hac]
      · have hbc : b ≤ c := le_of_not_gt hcb
        simp [hca, hcb, hbc]
  index_lt_right := by
    intro c
    by_cases hca : c < a
    · simp [hca]
    · by_cases hcb : c < b
      · simp [hca, hcb]
      · simp [hca, hcb]
  cell_width_lt := by
    intro cell
    fin_cases cell
    · simpa [measureReal_eRealOpenCell_bot_coe] using hleft
    · simpa [measureReal_eRealOpenCell_coe_coe] using hmiddle
    · simpa [measureReal_eRealOpenCell_coe_top] using hright

/--
Three real cutpoints satisfying the lower-tail, middle-cell, and upper-tail
width bounds give a supplied adjacent-endpoint grid.
-/
theorem exists_threeCell
    (μ : Measure ℝ) {epsilon a b : ℝ}
    (hab : a < b)
    (hleft : μ.real (Set.Iio a) < epsilon)
    (hmiddle : μ.real (Set.Ioo a b) < epsilon)
    (hright : μ.real (Set.Ioi b) < epsilon) :
    ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) :=
  ⟨3, ⟨threeCell μ hab hleft hmiddle hright⟩⟩

/--
CDF increment bounds can supply the middle width in the three-cell
endpoint-grid constructor.
-/
theorem exists_threeCell_of_cdf_leftLim_sub_lt
    (μ : Measure ℝ) [IsProbabilityMeasure μ] {epsilon a b : ℝ}
    (hab : a < b)
    (hleft : μ.real (Set.Iio a) < epsilon)
    (hmiddle :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ a < epsilon)
    (hright : μ.real (Set.Ioi b) < epsilon) :
    ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) :=
  exists_threeCell μ hab hleft
    (measureReal_Ioo_lt_of_cdf_leftLim_sub_lt μ hab hmiddle) hright

/--
To prove endpoint-grid existence for every positive radius, it is enough to
construct grids in the nontrivial range below the total mass.  Larger radii
are handled by the one-cell endpoint grid.
-/
theorem exists_forall_of_exists_le_measureReal_univ
    {μ : Measure ℝ}
    (endpointGridExists_le_total :
      ∀ epsilon, 0 < epsilon -> epsilon ≤ μ.real Set.univ ->
        ∃ cellCount, Nonempty
          (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount)) :
    ∀ epsilon, 0 < epsilon ->
      ∃ cellCount, Nonempty
        (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) := by
  intro epsilon hepsilon
  by_cases hwidth : μ.real Set.univ < epsilon
  · exact exists_singleCell_of_measureReal_univ_lt μ hwidth
  · exact endpointGridExists_le_total epsilon hepsilon (le_of_not_gt hwidth)

end SuppliedERealHalfLineEndpointGrid

namespace SuppliedERealHalfLineGrid

/--
A supplied extended-real grid at a smaller radius is also a supplied grid at
any larger radius.
-/
def of_le_epsilon
    {μ : Measure ℝ} {epsilon smallerEpsilon : ℝ} {cardinality : ℕ}
    (grid : SuppliedERealHalfLineGrid μ smallerEpsilon cardinality)
    (hsmall : smallerEpsilon ≤ epsilon) :
    SuppliedERealHalfLineGrid μ epsilon cardinality where
  left := grid.left
  right := grid.right
  bracketOf := grid.bracketOf
  left_lt_right := grid.left_lt_right
  left_le_index := grid.left_le_index
  index_lt_right := grid.index_lt_right
  cell_width_lt := fun bracketIndex =>
    lt_of_lt_of_le (grid.cell_width_lt bracketIndex) hsmall

/--
Finite extended-real grid existence is monotone in the requested radius.
-/
theorem exists_of_le_epsilon
    {μ : Measure ℝ} {epsilon smallerEpsilon : ℝ}
    (hsmall : smallerEpsilon ≤ epsilon)
    (gridExists :
      ∃ cardinality, Nonempty
        (SuppliedERealHalfLineGrid μ smallerEpsilon cardinality)) :
    ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid μ epsilon cardinality) := by
  rcases gridExists with ⟨cardinality, gridNonempty⟩
  exact ⟨cardinality, gridNonempty.map fun grid => grid.of_le_epsilon hsmall⟩

/--
The one-cell extended grid `(-∞, ∞)`.

This is the base case for the distribution-dependent grid construction in
Example 2.4.2: if the total mass is already below the requested radius, one
bracket covers the whole half-line class.
-/
noncomputable def singleCell
    (μ : Measure ℝ) {epsilon : ℝ} (hwidth : μ.real Set.univ < epsilon) :
    SuppliedERealHalfLineGrid μ epsilon 1 where
  left := fun _ => ⊥
  right := fun _ => ⊤
  bracketOf := fun _ => 0
  left_lt_right := by
    intro _bracketIndex
    simp
  left_le_index := by
    intro _c
    simp
  index_lt_right := by
    intro _c
    simp
  cell_width_lt := by
    intro _bracketIndex
    rwa [eRealOpenCell_bot_top]

/--
If the requested radius exceeds the total mass, the one-cell extended grid is
a supplied finite grid.
-/
theorem exists_singleCell_of_measureReal_univ_lt
    (μ : Measure ℝ) {epsilon : ℝ} (hwidth : μ.real Set.univ < epsilon) :
    ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid μ epsilon cardinality) :=
  ⟨1, ⟨singleCell μ hwidth⟩⟩

/--
A supplied extended-real grid yields an explicit-cardinality finite `L1(P)`
bracket cover for the real half-line indicator class.
-/
noncomputable def toFiniteL1BracketCoverAtCard
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} {cardinality : ℕ}
    (grid : SuppliedERealHalfLineGrid μ epsilon cardinality) :
    FiniteL1BracketCoverAtCard μ Set.univ realHalfLineIndicator
      epsilon cardinality where
  bracket := fun bracketIndex =>
    eRealHalfLineBracket (grid.left bracketIndex) (grid.right bracketIndex)
  bracketOf := fun c _ => grid.bracketOf c
  mem_bracket := by
    intro c _hc
    exact
      eRealHalfLineBracket_mem_realIndicator_of_le_lt
        (grid.left_le_index c) (grid.index_lt_right c)
  width_lt := by
    intro bracketIndex
    dsimp [IsL1EpsilonBracket, l1BracketWidth]
    rw [eRealHalfLineBracket_l1Width_eq_measureReal_openCell μ
      (grid.left_lt_right bracketIndex)]
    exact grid.cell_width_lt bracketIndex
  lower_integrable := by
    intro bracketIndex
    exact integrable_eRealClosedHalfLineIndicator μ (grid.left bracketIndex)
  upper_integrable := by
    intro bracketIndex
    exact integrable_eRealOpenHalfLineIndicator μ (grid.right bracketIndex)
  function_integrable := by
    intro c _hc
    exact integrable_realHalfLineIndicator μ c

/--
A supplied extended-real grid proves finiteness of the primitive local
`L1(P)` bracketing-number witness.
-/
theorem hasFiniteL1BracketingNumber
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} {cardinality : ℕ}
    (grid : SuppliedERealHalfLineGrid μ epsilon cardinality) :
    HasFiniteL1BracketingNumber μ Set.univ realHalfLineIndicator epsilon := by
  exact ⟨cardinality, ⟨grid.toFiniteL1BracketCoverAtCard⟩⟩

/--
A supplied extended-real grid makes the numeric primitive bracketing number
finite.
-/
theorem l1BracketingNumber_lt_top
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} {cardinality : ℕ}
    (grid : SuppliedERealHalfLineGrid μ epsilon cardinality) :
    l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ :=
  l1BracketingNumber_lt_top_of_hasFinite grid.hasFiniteL1BracketingNumber

end SuppliedERealHalfLineGrid

namespace SuppliedERealHalfLineEndpointGrid

/--
A supplied adjacent-endpoint grid proves finiteness of the primitive local
`L1(P)` bracketing-number witness.
-/
theorem hasFiniteL1BracketingNumber
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} {cellCount : ℕ}
    (grid : SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) :
    HasFiniteL1BracketingNumber μ Set.univ realHalfLineIndicator epsilon :=
  grid.toSuppliedERealHalfLineGrid.hasFiniteL1BracketingNumber

/--
A supplied adjacent-endpoint grid makes the numeric primitive bracketing number
finite.
-/
theorem l1BracketingNumber_lt_top
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} {cellCount : ℕ}
    (grid : SuppliedERealHalfLineEndpointGrid μ epsilon cellCount) :
    l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ :=
  grid.toSuppliedERealHalfLineGrid.l1BracketingNumber_lt_top

/--
If the requested radius exceeds the total mass, the half-line class has finite
primitive `L1(P)` bracketing number via the one-cell endpoint grid.
-/
theorem l1BracketingNumber_lt_top_of_measureReal_univ_lt
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} (hwidth : μ.real Set.univ < epsilon) :
    l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ :=
  (singleCell μ hwidth).l1BracketingNumber_lt_top

/--
Three real cutpoints satisfying the lower-tail, middle-cell, and upper-tail
width bounds give finite primitive `L1(P)` bracketing number.
-/
theorem l1BracketingNumber_lt_top_of_threeCell
    {μ : Measure ℝ} [IsFiniteMeasure μ] {epsilon a b : ℝ}
    (hab : a < b)
    (hleft : μ.real (Set.Iio a) < epsilon)
    (hmiddle : μ.real (Set.Ioo a b) < epsilon)
    (hright : μ.real (Set.Ioi b) < epsilon) :
    l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ :=
  (threeCell μ hab hleft hmiddle hright).l1BracketingNumber_lt_top

/--
CDF increment bounds can supply the middle width in the three-cell primitive
bracketing-number handoff.
-/
theorem l1BracketingNumber_lt_top_of_threeCell_cdf_leftLim_sub_lt
    {μ : Measure ℝ} [IsProbabilityMeasure μ] {epsilon a b : ℝ}
    (hab : a < b)
    (hleft : μ.real (Set.Iio a) < epsilon)
    (hmiddle :
      Function.leftLim (ProbabilityTheory.cdf μ) b -
        ProbabilityTheory.cdf μ a < epsilon)
    (hright : μ.real (Set.Ioi b) < epsilon) :
    l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ :=
  l1BracketingNumber_lt_top_of_threeCell hab hleft
    (measureReal_Ioo_lt_of_cdf_leftLim_sub_lt μ hab hmiddle) hright

/--
Uniform supplied adjacent-endpoint grids yield the primitive bracketing-number
hypothesis needed by VdV&W Theorem 2.4.1.
-/
theorem l1BracketingNumber_lt_top_forall
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    (endpointGridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount)) :
    ∀ epsilon, 0 < epsilon ->
      l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ := by
  intro epsilon hepsilon
  rcases endpointGridExists epsilon hepsilon with ⟨cellCount, gridNonempty⟩
  exact gridNonempty.elim fun grid => grid.l1BracketingNumber_lt_top

/--
It is enough to build adjacent-endpoint grids in the nontrivial range
`epsilon <= μ.real univ` to get the primitive bracketing-number hypothesis at
every positive radius.
-/
theorem l1BracketingNumber_lt_top_forall_of_exists_le_measureReal_univ
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    (endpointGridExists_le_total :
      ∀ epsilon, 0 < epsilon -> epsilon ≤ μ.real Set.univ ->
        ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount)) :
    ∀ epsilon, 0 < epsilon ->
      l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ :=
  l1BracketingNumber_lt_top_forall
    (exists_forall_of_exists_le_measureReal_univ endpointGridExists_le_total)

/--
Uniform supplied adjacent-endpoint grids yield uniform supplied primitive grids.
-/
theorem exists_suppliedERealHalfLineGrid_of_forall
    {μ : Measure ℝ}
    (endpointGridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount)) :
    ∀ epsilon, 0 < epsilon ->
      ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid μ epsilon cardinality) := by
  intro epsilon hepsilon
  rcases endpointGridExists epsilon hepsilon with ⟨cellCount, gridNonempty⟩
  exact ⟨cellCount, gridNonempty.map fun grid => grid.toSuppliedERealHalfLineGrid⟩

/--
The nontrivial-range adjacent-endpoint grid construction also yields uniform
primitive supplied extended-real grids.
-/
theorem exists_suppliedERealHalfLineGrid_of_exists_le_measureReal_univ
    {μ : Measure ℝ}
    (endpointGridExists_le_total :
      ∀ epsilon, 0 < epsilon -> epsilon ≤ μ.real Set.univ ->
        ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid μ epsilon cellCount)) :
    ∀ epsilon, 0 < epsilon ->
      ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid μ epsilon cardinality) :=
  exists_suppliedERealHalfLineGrid_of_forall
    (exists_forall_of_exists_le_measureReal_univ endpointGridExists_le_total)

end SuppliedERealHalfLineEndpointGrid

namespace SuppliedERealHalfLineGrid

/--
If the requested radius exceeds the total mass, the half-line class has finite
primitive `L1(P)` bracketing number at that radius.
-/
theorem l1BracketingNumber_lt_top_of_measureReal_univ_lt
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    {epsilon : ℝ} (hwidth : μ.real Set.univ < epsilon) :
    l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ :=
  (singleCell μ hwidth).l1BracketingNumber_lt_top

/--
Uniform finite-grid existence at every positive radius yields the primitive
bracketing-number hypothesis needed by VdV&W Theorem 2.4.1.
-/
theorem l1BracketingNumber_lt_top_forall
    {μ : Measure ℝ} [IsFiniteMeasure μ]
    (gridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid μ epsilon cardinality)) :
    ∀ epsilon, 0 < epsilon ->
      l1BracketingNumber μ Set.univ realHalfLineIndicator epsilon < ⊤ := by
  intro epsilon hepsilon
  rcases gridExists epsilon hepsilon with ⟨cardinality, gridNonempty⟩
  exact gridNonempty.elim fun grid => grid.l1BracketingNumber_lt_top

end SuppliedERealHalfLineGrid

end StatInference
