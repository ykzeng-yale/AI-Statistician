import StatInference.Optimization.MirrorDescent

/-!
# Chewi Chapter 11 alternating Bregman projections

This module starts the Chapter 11 alternating-projection lane.  The first
packet proves the finite, source-shaped content behind Lemma 11.2: a
Pythagorean Bregman projection certificate gives a one-cycle decrease, which
telescopes over alternating Bregman projections.
-/

namespace StatInference
namespace Optimization

open Finset
open scoped InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Finite real-valued KL display used for the Sinkhorn marginal identities. -/
noncomputable def finiteKL {ι : Type*} [Fintype ι] (p q : ι -> ℝ) : ℝ :=
  ∑ i, p i * Real.log (p i / q i)

/-- A finite KL display vanishes against itself. -/
theorem finiteKL_self {ι : Type*} [Fintype ι] (p : ι -> ℝ) :
    finiteKL p p = 0 := by
  classical
  unfold finiteKL
  refine Finset.sum_eq_zero ?_
  intro i _hi
  by_cases hp : p i = 0
  · simp [hp]
  · simp [hp]

/-- Finite coupling KL display for arrays indexed by `X × Y`. -/
noncomputable def finiteCouplingKL {X Y : Type*} [Fintype X] [Fintype Y]
    (γ η : X -> Y -> ℝ) : ℝ :=
  ∑ x, ∑ y, γ x y * Real.log (γ x y / η x y)

/-- Total mass of a finite coupling array. -/
noncomputable def finiteCouplingMass {X Y : Type*} [Fintype X] [Fintype Y]
    (γ : X -> Y -> ℝ) : ℝ :=
  ∑ x, ∑ y, γ x y

/--
Entropic mirror map on finite couplings, written in the Chewi/Sinkhorn
normalization `sum gamma * log gamma - gamma`.
-/
noncomputable def finiteCouplingEntropy {X Y : Type*} [Fintype X] [Fintype Y]
    (γ : X -> Y -> ℝ) : ℝ :=
  ∑ x, ∑ y, (γ x y * Real.log (γ x y) - γ x y)

/-- The formal gradient of `finiteCouplingEntropy` on the positive orthant. -/
noncomputable def finiteCouplingLogGradient {X Y : Type*}
    (γ : X -> Y -> ℝ) : X -> Y -> ℝ :=
  fun x y => Real.log (γ x y)

/--
Scalar Bregman display for the finite entropic mirror map, written directly on
curried arrays.  A later EuclideanSpace wrapper can transport this to the
generic `bregmanDivergence` interface when needed.
-/
noncomputable def finiteCouplingEntropyBregman {X Y : Type*}
    [Fintype X] [Fintype Y] (γ η : X -> Y -> ℝ) : ℝ :=
  finiteCouplingEntropy γ - finiteCouplingEntropy η -
    ∑ x, ∑ y, Real.log (η x y) * (γ x y - η x y)

/-- Row marginal of a finite coupling array. -/
noncomputable def rowMarginal {X Y : Type*} [Fintype Y]
    (γ : X -> Y -> ℝ) (x : X) : ℝ :=
  ∑ y, γ x y

/-- Column marginal of a finite coupling array. -/
noncomputable def columnMarginal {X Y : Type*} [Fintype X]
    (γ : X -> Y -> ℝ) (y : Y) : ℝ :=
  ∑ x, γ x y

/-- Finite row-marginal constraint set for Sinkhorn row projections. -/
def finiteRowMarginalConstraint {X Y : Type*} [Fintype Y]
    (μ : X -> ℝ) : Set (X -> Y -> ℝ) :=
  {γ | ∀ x, rowMarginal γ x = μ x}

/-- Finite column-marginal constraint set for Sinkhorn column projections. -/
def finiteColumnMarginalConstraint {X Y : Type*} [Fintype X]
    (ν : Y -> ℝ) : Set (X -> Y -> ℝ) :=
  {γ | ∀ y, columnMarginal γ y = ν y}

/-- Summing row marginals recovers the total finite coupling mass. -/
theorem sum_rowMarginal_eq_finiteCouplingMass
    {X Y : Type*} [Fintype X] [Fintype Y] (γ : X -> Y -> ℝ) :
    (∑ x, rowMarginal γ x) = finiteCouplingMass γ := by
  rfl

/-- Summing column marginals recovers the total finite coupling mass. -/
theorem sum_columnMarginal_eq_finiteCouplingMass
    {X Y : Type*} [Fintype X] [Fintype Y] (γ : X -> Y -> ℝ) :
    (∑ y, columnMarginal γ y) = finiteCouplingMass γ := by
  classical
  unfold columnMarginal finiteCouplingMass
  rw [Finset.sum_comm]

/-- Nonnegative finite couplings have nonnegative row marginals. -/
theorem rowMarginal_nonneg_of_nonneg
    {X Y : Type*} [Fintype Y] {γ : X -> Y -> ℝ}
    (hγ_nonneg : ∀ x y, 0 ≤ γ x y) (x : X) :
    0 ≤ rowMarginal γ x := by
  classical
  unfold rowMarginal
  exact Finset.sum_nonneg fun y _hy => hγ_nonneg x y

/-- Positive finite couplings have positive row marginals when `Y` is nonempty. -/
theorem rowMarginal_pos_of_pos
    {X Y : Type*} [Fintype Y] [Nonempty Y] {γ : X -> Y -> ℝ}
    (hγ_pos : ∀ x y, 0 < γ x y) (x : X) :
    0 < rowMarginal γ x := by
  classical
  let y0 : Y := Classical.choice (inferInstance : Nonempty Y)
  unfold rowMarginal
  exact Finset.sum_pos (fun y _hy => hγ_pos x y)
    ⟨y0, Finset.mem_univ y0⟩

/-- Nonnegative finite couplings have nonnegative column marginals. -/
theorem columnMarginal_nonneg_of_nonneg
    {X Y : Type*} [Fintype X] {γ : X -> Y -> ℝ}
    (hγ_nonneg : ∀ x y, 0 ≤ γ x y) (y : Y) :
    0 ≤ columnMarginal γ y := by
  classical
  unfold columnMarginal
  exact Finset.sum_nonneg fun x _hx => hγ_nonneg x y

/-- Positive finite couplings have positive column marginals when `X` is nonempty. -/
theorem columnMarginal_pos_of_pos
    {X Y : Type*} [Fintype X] [Nonempty X] {γ : X -> Y -> ℝ}
    (hγ_pos : ∀ x y, 0 < γ x y) (y : Y) :
    0 < columnMarginal γ y := by
  classical
  let x0 : X := Classical.choice (inferInstance : Nonempty X)
  unfold columnMarginal
  exact Finset.sum_pos (fun x _hx => hγ_pos x y)
    ⟨x0, Finset.mem_univ x0⟩

/--
The row-marginal objective in Chewi Theorem 11.8:
`gamma ↦ KL(rowMarginal gamma || μ)`.
-/
noncomputable def sinkhornRowObjective {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ) : ℝ :=
  finiteKL (rowMarginal γ) μ

/-- The Sinkhorn row objective vanishes when the row marginal is already `μ`. -/
theorem sinkhornRowObjective_eq_zero_of_rowMarginal_eq
    {X Y : Type*} [Fintype X] [Fintype Y]
    {μ : X -> ℝ} {γ : X -> Y -> ℝ}
    (hrow : ∀ x, rowMarginal γ x = μ x) :
    sinkhornRowObjective μ γ = 0 := by
  have hrow_fun : rowMarginal γ = μ := funext hrow
  rw [sinkhornRowObjective, hrow_fun, finiteKL_self]

/-- Row normalization of a finite coupling array toward a target row law `μ`. -/
noncomputable def rowNormalizedCoupling {X Y : Type*} [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ) : X -> Y -> ℝ :=
  fun x y => μ x * γ x y / rowMarginal γ x

/-- Column normalization of a finite coupling array toward a target column law `ν`. -/
noncomputable def columnNormalizedCoupling {X Y : Type*} [Fintype X]
    (ν : Y -> ℝ) (γ : X -> Y -> ℝ) : X -> Y -> ℝ :=
  fun x y => γ x y * ν y / columnMarginal γ y

theorem rowMarginal_rowNormalizedCoupling
    {X Y : Type*} [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ)
    (hrow_ne : ∀ x, rowMarginal γ x ≠ 0) (x : X) :
    rowMarginal (rowNormalizedCoupling μ γ) x = μ x := by
  classical
  unfold rowMarginal rowNormalizedCoupling
  calc
    (∑ y, μ x * γ x y / ∑ y, γ x y)
        = ∑ y, (μ x / (∑ y, γ x y)) * γ x y := by
          refine Finset.sum_congr rfl ?_
          intro y _hy
          ring
    _ = (μ x / (∑ y, γ x y)) * ∑ y, γ x y := by
          exact (Finset.mul_sum (s := Finset.univ)
            (a := μ x / (∑ y, γ x y)) (f := fun y => γ x y)).symm
    _ = μ x := by
          have hsum_ne : (∑ y, γ x y) ≠ 0 := by
            simpa [rowMarginal] using hrow_ne x
          field_simp [hsum_ne]

theorem columnMarginal_columnNormalizedCoupling
    {X Y : Type*} [Fintype X]
    (ν : Y -> ℝ) (γ : X -> Y -> ℝ)
    (hcol_ne : ∀ y, columnMarginal γ y ≠ 0) (y : Y) :
    columnMarginal (columnNormalizedCoupling ν γ) y = ν y := by
  classical
  unfold columnMarginal columnNormalizedCoupling
  calc
    (∑ x, γ x y * ν y / ∑ x, γ x y)
        = ∑ x, (ν y / (∑ x, γ x y)) * γ x y := by
          refine Finset.sum_congr rfl ?_
          intro x _hx
          ring
    _ = (ν y / (∑ x, γ x y)) * ∑ x, γ x y := by
          exact (Finset.mul_sum (s := Finset.univ)
            (a := ν y / (∑ x, γ x y)) (f := fun x => γ x y)).symm
    _ = ν y := by
          have hsum_ne : (∑ x, γ x y) ≠ 0 := by
            simpa [columnMarginal] using hcol_ne y
          field_simp [hsum_ne]

theorem finiteCouplingMass_rowNormalizedCoupling
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ)
    (hrow_ne : ∀ x, rowMarginal γ x ≠ 0) :
    finiteCouplingMass (rowNormalizedCoupling μ γ) = ∑ x, μ x := by
  classical
  unfold finiteCouplingMass
  refine Finset.sum_congr rfl ?_
  intro x _hx
  simpa [rowMarginal] using rowMarginal_rowNormalizedCoupling μ γ hrow_ne x

theorem finiteCouplingMass_columnNormalizedCoupling
    {X Y : Type*} [Fintype X] [Fintype Y]
    (ν : Y -> ℝ) (γ : X -> Y -> ℝ)
    (hcol_ne : ∀ y, columnMarginal γ y ≠ 0) :
    finiteCouplingMass (columnNormalizedCoupling ν γ) = ∑ y, ν y := by
  classical
  unfold finiteCouplingMass
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl ?_
  intro y _hy
  simpa [columnMarginal] using columnMarginal_columnNormalizedCoupling ν γ hcol_ne y

theorem rowNormalizedCoupling_ne_of_ne
    {X Y : Type*} [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ)
    (hμ_ne : ∀ x, μ x ≠ 0)
    (hγ_ne : ∀ x y, γ x y ≠ 0)
    (hrow_ne : ∀ x, rowMarginal γ x ≠ 0) :
    ∀ x y, rowNormalizedCoupling μ γ x y ≠ 0 := by
  intro x y
  unfold rowNormalizedCoupling
  exact div_ne_zero (mul_ne_zero (hμ_ne x) (hγ_ne x y)) (hrow_ne x)

/-- Row normalization preserves positivity under positive target rows and row sums. -/
theorem rowNormalizedCoupling_pos_of_pos
    {X Y : Type*} [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ)
    (hμ_pos : ∀ x, 0 < μ x)
    (hγ_pos : ∀ x y, 0 < γ x y)
    (hrow_pos : ∀ x, 0 < rowMarginal γ x) :
    ∀ x y, 0 < rowNormalizedCoupling μ γ x y := by
  intro x y
  unfold rowNormalizedCoupling
  exact div_pos (mul_pos (hμ_pos x) (hγ_pos x y)) (hrow_pos x)

theorem columnNormalizedCoupling_ne_of_ne
    {X Y : Type*} [Fintype X]
    (ν : Y -> ℝ) (γ : X -> Y -> ℝ)
    (hν_ne : ∀ y, ν y ≠ 0)
    (hγ_ne : ∀ x y, γ x y ≠ 0)
    (hcol_ne : ∀ y, columnMarginal γ y ≠ 0) :
    ∀ x y, columnNormalizedCoupling ν γ x y ≠ 0 := by
  intro x y
  unfold columnNormalizedCoupling
  exact div_ne_zero (mul_ne_zero (hγ_ne x y) (hν_ne y)) (hcol_ne y)

/-- Column normalization preserves positivity under positive target columns and column sums. -/
theorem columnNormalizedCoupling_pos_of_pos
    {X Y : Type*} [Fintype X]
    (ν : Y -> ℝ) (γ : X -> Y -> ℝ)
    (hν_pos : ∀ y, 0 < ν y)
    (hγ_pos : ∀ x y, 0 < γ x y)
    (hcol_pos : ∀ y, 0 < columnMarginal γ y) :
    ∀ x y, 0 < columnNormalizedCoupling ν γ x y := by
  intro x y
  unfold columnNormalizedCoupling
  exact div_pos (mul_pos (hγ_pos x y) (hν_pos y)) (hcol_pos y)

/--
Finite Sinkhorn row-normalization KL identity, in the algebraic form needed by
Theorem 11.7: if a half-step has row marginal `μ` and pointwise likelihood
ratio `μ x / row x`, then its coupling KL against the previous coupling is
exactly the marginal KL `KL(μ || row)`.
-/
theorem finiteCouplingKL_eq_finiteKL_of_row_ratio
    {X Y : Type*} [Fintype X] [Fintype Y]
    (γ η : X -> Y -> ℝ) (μ row : X -> ℝ)
    (hrow : ∀ x, ∑ y, γ x y = μ x)
    (hratio : ∀ x y, γ x y / η x y = μ x / row x) :
    finiteCouplingKL γ η = finiteKL μ row := by
  classical
  unfold finiteCouplingKL finiteKL
  calc
    (∑ x, ∑ y, γ x y * Real.log (γ x y / η x y))
        = ∑ x, ∑ y, γ x y * Real.log (μ x / row x) := by
          refine Finset.sum_congr rfl ?_
          intro x _hx
          refine Finset.sum_congr rfl ?_
          intro y _hy
          rw [hratio x y]
    _ = ∑ x, (∑ y, γ x y) * Real.log (μ x / row x) := by
          refine Finset.sum_congr rfl ?_
          intro x _hx
          exact (Finset.sum_mul (s := Finset.univ)
            (f := fun y => γ x y) (a := Real.log (μ x / row x))).symm
    _ = ∑ x, μ x * Real.log (μ x / row x) := by
          refine Finset.sum_congr rfl ?_
          intro x _hx
          rw [hrow x]

/--
Finite Sinkhorn column-normalization KL identity, in the algebraic form needed
by Theorem 11.7: if a half-step has column marginal `ν` and pointwise
likelihood ratio `ν y / col y`, then its coupling KL against the previous
coupling is exactly the marginal KL `KL(ν || col)`.
-/
theorem finiteCouplingKL_eq_finiteKL_of_column_ratio
    {X Y : Type*} [Fintype X] [Fintype Y]
    (γ η : X -> Y -> ℝ) (ν col : Y -> ℝ)
    (hcol : ∀ y, ∑ x, γ x y = ν y)
    (hratio : ∀ x y, γ x y / η x y = ν y / col y) :
    finiteCouplingKL γ η = finiteKL ν col := by
  classical
  unfold finiteCouplingKL finiteKL
  calc
    (∑ x, ∑ y, γ x y * Real.log (γ x y / η x y))
        = ∑ x, ∑ y, γ x y * Real.log (ν y / col y) := by
          refine Finset.sum_congr rfl ?_
          intro x _hx
          refine Finset.sum_congr rfl ?_
          intro y _hy
          rw [hratio x y]
    _ = ∑ y, ∑ x, γ x y * Real.log (ν y / col y) := by
          rw [Finset.sum_comm]
    _ = ∑ y, (∑ x, γ x y) * Real.log (ν y / col y) := by
          refine Finset.sum_congr rfl ?_
          intro y _hy
          exact (Finset.sum_mul (s := Finset.univ)
            (f := fun x => γ x y) (a := Real.log (ν y / col y))).symm
    _ = ∑ y, ν y * Real.log (ν y / col y) := by
          refine Finset.sum_congr rfl ?_
          intro y _hy
          rw [hcol y]

/--
For finite couplings with equal total mass, the scalar Bregman display of the
entropic mirror map is the finite coupling KL display.  This is the algebraic
bridge used to identify Sinkhorn's row/column Bregman movements with marginal
KL terms.
-/
theorem finiteCouplingEntropyBregman_eq_finiteCouplingKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    (γ η : X -> Y -> ℝ)
    (hγ_ne : ∀ x y, γ x y ≠ 0)
    (hη_ne : ∀ x y, η x y ≠ 0)
    (hmass : finiteCouplingMass γ = finiteCouplingMass η) :
    finiteCouplingEntropyBregman γ η = finiteCouplingKL γ η := by
  classical
  have hmass' : (∑ x, ∑ y, γ x y) = ∑ x, ∑ y, η x y := by
    simpa [finiteCouplingMass] using hmass
  unfold finiteCouplingEntropyBregman finiteCouplingEntropy finiteCouplingKL
  simp_rw [Real.log_div (hγ_ne _ _) (hη_ne _ _)]
  simp [Finset.sum_sub_distrib, sub_mul, mul_sub, hmass', mul_comm]

/--
Finite entropic Bregman Pythagorean equality when the log-ratio
`log proj - log base` depends only on rows and `z` has the same row marginal as
`proj`.
-/
theorem finiteCouplingEntropyBregman_add_eq_of_row_log_diff
    {X Y : Type*} [Fintype X] [Fintype Y]
    (z proj base : X -> Y -> ℝ) (rowLog : X -> ℝ)
    (hlog : ∀ x y, Real.log (proj x y) - Real.log (base x y) = rowLog x)
    (hrow : ∀ x, rowMarginal z x = rowMarginal proj x) :
    finiteCouplingEntropyBregman z proj +
        finiteCouplingEntropyBregman proj base =
      finiteCouplingEntropyBregman z base := by
  classical
  have hsum_zero :
      (∑ x, ∑ y,
        (Real.log (proj x y) - Real.log (base x y)) *
          (z x y - proj x y)) = 0 := by
    calc
      (∑ x, ∑ y,
        (Real.log (proj x y) - Real.log (base x y)) *
          (z x y - proj x y))
          = ∑ x, ∑ y, rowLog x * (z x y - proj x y) := by
              refine Finset.sum_congr rfl ?_
              intro x _hx
              refine Finset.sum_congr rfl ?_
              intro y _hy
              rw [hlog x y]
      _ = ∑ x, rowLog x * ∑ y, (z x y - proj x y) := by
              refine Finset.sum_congr rfl ?_
              intro x _hx
              exact (Finset.mul_sum (s := Finset.univ)
                (a := rowLog x) (f := fun y => z x y - proj x y)).symm
      _ = 0 := by
              refine Finset.sum_eq_zero ?_
              intro x _hx
              have hrow_diff : (∑ y, (z x y - proj x y)) = 0 := by
                rw [Finset.sum_sub_distrib]
                simpa [rowMarginal] using sub_eq_zero.mpr (hrow x)
              rw [hrow_diff, mul_zero]
  have halg :
      finiteCouplingEntropyBregman z proj +
          finiteCouplingEntropyBregman proj base =
        finiteCouplingEntropyBregman z base -
          ∑ x, ∑ y,
            (Real.log (proj x y) - Real.log (base x y)) *
              (z x y - proj x y) := by
    unfold finiteCouplingEntropyBregman
    simp [Finset.sum_sub_distrib, sub_mul, mul_sub]
    ring
  rw [halg, hsum_zero, sub_zero]

/--
Finite entropic Bregman Pythagorean equality when the log-ratio
`log proj - log base` depends only on columns and `z` has the same column
marginal as `proj`.
-/
theorem finiteCouplingEntropyBregman_add_eq_of_column_log_diff
    {X Y : Type*} [Fintype X] [Fintype Y]
    (z proj base : X -> Y -> ℝ) (columnLog : Y -> ℝ)
    (hlog : ∀ x y, Real.log (proj x y) - Real.log (base x y) = columnLog y)
    (hcol : ∀ y, columnMarginal z y = columnMarginal proj y) :
    finiteCouplingEntropyBregman z proj +
        finiteCouplingEntropyBregman proj base =
      finiteCouplingEntropyBregman z base := by
  classical
  have hsum_zero :
      (∑ x, ∑ y,
        (Real.log (proj x y) - Real.log (base x y)) *
          (z x y - proj x y)) = 0 := by
    calc
      (∑ x, ∑ y,
        (Real.log (proj x y) - Real.log (base x y)) *
          (z x y - proj x y))
          = ∑ x, ∑ y, columnLog y * (z x y - proj x y) := by
              refine Finset.sum_congr rfl ?_
              intro x _hx
              refine Finset.sum_congr rfl ?_
              intro y _hy
              rw [hlog x y]
      _ = ∑ y, ∑ x, columnLog y * (z x y - proj x y) := by
              rw [Finset.sum_comm]
      _ = ∑ y, columnLog y * ∑ x, (z x y - proj x y) := by
              refine Finset.sum_congr rfl ?_
              intro y _hy
              exact (Finset.mul_sum (s := Finset.univ)
                (a := columnLog y) (f := fun x => z x y - proj x y)).symm
      _ = 0 := by
              refine Finset.sum_eq_zero ?_
              intro y _hy
              have hcol_diff : (∑ x, (z x y - proj x y)) = 0 := by
                rw [Finset.sum_sub_distrib]
                simpa [columnMarginal] using sub_eq_zero.mpr (hcol y)
              rw [hcol_diff, mul_zero]
  have halg :
      finiteCouplingEntropyBregman z proj +
          finiteCouplingEntropyBregman proj base =
        finiteCouplingEntropyBregman z base -
          ∑ x, ∑ y,
            (Real.log (proj x y) - Real.log (base x y)) *
              (z x y - proj x y) := by
    unfold finiteCouplingEntropyBregman
    simp [Finset.sum_sub_distrib, sub_mul, mul_sub]
    ring
  rw [halg, hsum_zero, sub_zero]

/-- Log-ratio form of a positive row-normalization step. -/
theorem rowNormalizedCoupling_log_sub_log_eq
    {X Y : Type*} [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ)
    (hμ_ne : ∀ x, μ x ≠ 0)
    (hγ_ne : ∀ x y, γ x y ≠ 0)
    (hrow_ne : ∀ x, rowMarginal γ x ≠ 0) (x : X) (y : Y) :
    Real.log (rowNormalizedCoupling μ γ x y) - Real.log (γ x y) =
      Real.log (μ x / rowMarginal γ x) := by
  unfold rowNormalizedCoupling
  rw [Real.log_div (mul_ne_zero (hμ_ne x) (hγ_ne x y)) (hrow_ne x),
    Real.log_mul (hμ_ne x) (hγ_ne x y),
    Real.log_div (hμ_ne x) (hrow_ne x)]
  ring

/-- Log-ratio form of a positive column-normalization step. -/
theorem columnNormalizedCoupling_log_sub_log_eq
    {X Y : Type*} [Fintype X]
    (ν : Y -> ℝ) (γ : X -> Y -> ℝ)
    (hν_ne : ∀ y, ν y ≠ 0)
    (hγ_ne : ∀ x y, γ x y ≠ 0)
    (hcol_ne : ∀ y, columnMarginal γ y ≠ 0) (x : X) (y : Y) :
    Real.log (columnNormalizedCoupling ν γ x y) - Real.log (γ x y) =
      Real.log (ν y / columnMarginal γ y) := by
  unfold columnNormalizedCoupling
  rw [Real.log_div (mul_ne_zero (hγ_ne x y) (hν_ne y)) (hcol_ne y),
    Real.log_mul (hγ_ne x y) (hν_ne y),
    Real.log_div (hν_ne y) (hcol_ne y)]
  ring

/-- Pointwise Gibbs inequality in the form used by finite KL sums. -/
theorem finiteKL_term_lower {p q : ℝ} (hp : 0 ≤ p) (hq : 0 < q) :
    p - q ≤ p * Real.log (p / q) := by
  have hratio_nonneg : 0 ≤ p / q := div_nonneg hp hq.le
  have hbasic := Real.self_sub_one_le_mul_log hratio_nonneg
  have hmul := mul_le_mul_of_nonneg_left hbasic hq.le
  have hleft : q * (p / q - 1) = p - q := by
    field_simp [hq.ne']
  have hright : q * ((p / q) * Real.log (p / q)) =
      p * Real.log (p / q) := by
    field_simp [hq.ne']
  simpa [hleft, hright] using hmul

/-- Finite Gibbs inequality for positive reference weights with equal mass. -/
theorem finiteKL_nonneg_of_nonneg_of_pos_of_sum_eq
    {ι : Type*} [Fintype ι] (p q : ι -> ℝ)
    (hp : ∀ i, 0 ≤ p i) (hq : ∀ i, 0 < q i)
    (hsum : (∑ i, p i) = ∑ i, q i) :
    0 ≤ finiteKL p q := by
  classical
  have hsum_terms :
      (∑ i, (p i - q i)) ≤ finiteKL p q := by
    unfold finiteKL
    exact Finset.sum_le_sum fun i _hi => finiteKL_term_lower (hp i) (hq i)
  have hzero : (∑ i, (p i - q i)) = 0 := by
    rw [Finset.sum_sub_distrib, hsum]
    ring
  nlinarith

/-- Pointwise term used in the finite log-sum inequality. -/
theorem finiteKL_logSum_term_le {a b A B : ℝ}
    (ha : 0 < a) (hb : 0 < b) (hA : 0 < A) (hB : 0 < B) :
    a * Real.log (A / B) - a * Real.log (a / b) ≤ A * b / B - a := by
  have hz : 0 < (A / B) / (a / b) := by
    exact div_pos (div_pos hA hB) (div_pos ha hb)
  have hlog := Real.log_le_sub_one_of_pos hz
  have hmul := mul_le_mul_of_nonneg_left hlog ha.le
  have hlog_eq :
      Real.log ((A / B) / (a / b)) =
        Real.log (A / B) - Real.log (a / b) := by
    rw [Real.log_div]
    · exact div_ne_zero hA.ne' hB.ne'
    · exact div_ne_zero ha.ne' hb.ne'
  have hleft :
      a * Real.log ((A / B) / (a / b)) =
        a * Real.log (A / B) - a * Real.log (a / b) := by
    rw [hlog_eq]
    ring
  have hright :
      a * ((A / B) / (a / b) - 1) = A * b / B - a := by
    field_simp [ha.ne', hb.ne', hB.ne']
  simpa [hleft, hright] using hmul

/--
Finite log-sum inequality for one row.  This is the row-level data-processing
step for the finite Sinkhorn KL display.
-/
theorem finiteKL_row_logSum_le
    {Y : Type*} [Fintype Y] (a b : Y -> ℝ)
    (ha : ∀ y, 0 < a y) (hb : ∀ y, 0 < b y)
    (hA : 0 < ∑ y, a y) (hB : 0 < ∑ y, b y) :
    (∑ y, a y) * Real.log ((∑ y, a y) / (∑ y, b y)) ≤
      ∑ y, a y * Real.log (a y / b y) := by
  classical
  let A : ℝ := ∑ y, a y
  let B : ℝ := ∑ y, b y
  have hdiff_le :
      (∑ y, (a y * Real.log (A / B) -
          a y * Real.log (a y / b y))) ≤ 0 := by
    calc
      (∑ y, (a y * Real.log (A / B) -
          a y * Real.log (a y / b y)))
          ≤ ∑ y, (A * b y / B - a y) := by
              exact Finset.sum_le_sum fun y _hy =>
                finiteKL_logSum_term_le (ha y) (hb y) (by simpa [A] using hA)
                  (by simpa [B] using hB)
      _ = 0 := by
              rw [Finset.sum_sub_distrib]
              have hsum_first : (∑ y, A * b y / B) = A := by
                calc
                  (∑ y, A * b y / B) = A / B * ∑ y, b y := by
                      rw [Finset.mul_sum]
                      refine Finset.sum_congr rfl ?_
                      intro y _hy
                      ring
                  _ = A / B * B := by
                      rw [show (∑ y, b y) = B by simp [B]]
                  _ = A := by
                      have hB_ne : B ≠ 0 := by
                        simpa [B] using hB.ne'
                      field_simp [hB_ne]
              have hsum_second : (∑ y, a y) = A := by
                simp [A]
              rw [hsum_first, hsum_second]
              ring
  have hdiff_eq :
      (∑ y, (a y * Real.log (A / B) -
          a y * Real.log (a y / b y))) =
        A * Real.log (A / B) - ∑ y, a y * Real.log (a y / b y) := by
    rw [Finset.sum_sub_distrib]
    have hconst :
        (∑ y, a y * Real.log (A / B)) = A * Real.log (A / B) := by
      simpa [A] using
        (Finset.sum_mul (s := Finset.univ) (f := a) (a := Real.log (A / B))).symm
    rw [hconst]
  have hmain : A * Real.log (A / B) - ∑ y, a y * Real.log (a y / b y) ≤ 0 := by
    simpa [hdiff_eq] using hdiff_le
  have hrewrite :
      A * Real.log (A / B) =
        (∑ y, a y) * Real.log ((∑ y, a y) / (∑ y, b y)) := by
    simp [A, B]
  rw [← hrewrite]
  nlinarith

/--
Finite row-marginal data-processing/log-sum bridge for positive coupling
arrays.
-/
theorem finiteKL_rowMarginal_le_finiteCouplingKL_of_pos
    {X Y : Type*} [Fintype X] [Fintype Y]
    (γ η : X -> Y -> ℝ)
    (hγ_pos : ∀ x y, 0 < γ x y)
    (hη_pos : ∀ x y, 0 < η x y)
    (hrowγ_pos : ∀ x, 0 < rowMarginal γ x)
    (hrowη_pos : ∀ x, 0 < rowMarginal η x) :
    finiteKL (rowMarginal γ) (rowMarginal η) ≤ finiteCouplingKL γ η := by
  classical
  unfold finiteKL finiteCouplingKL
  exact Finset.sum_le_sum fun x _hx =>
    finiteKL_row_logSum_le
      (a := fun y => γ x y) (b := fun y => η x y)
      (hγ_pos x) (hη_pos x)
      (by simpa [rowMarginal] using hrowγ_pos x)
      (by simpa [rowMarginal] using hrowη_pos x)

/--
Row-marginal data-processing bridge with the reference row marginal identified
as the target row law `μ`.
-/
theorem finiteKL_rowMarginal_le_finiteCouplingKL_of_rowMarginal_eq_of_pos
    {X Y : Type*} [Fintype X] [Fintype Y]
    (γ γStar : X -> Y -> ℝ) (μ : X -> ℝ)
    (hγ_pos : ∀ x y, 0 < γ x y)
    (hstar_pos : ∀ x y, 0 < γStar x y)
    (hrowγ_pos : ∀ x, 0 < rowMarginal γ x)
    (hrowStar_pos : ∀ x, 0 < rowMarginal γStar x)
    (hstar_row : ∀ x, rowMarginal γStar x = μ x) :
    finiteKL (rowMarginal γ) μ ≤ finiteCouplingKL γ γStar := by
  have hrow_fun : rowMarginal γStar = μ := funext hstar_row
  rw [← hrow_fun]
  exact finiteKL_rowMarginal_le_finiteCouplingKL_of_pos
    γ γStar hγ_pos hstar_pos hrowγ_pos hrowStar_pos

/--
Sinkhorn row-objective data-processing bridge with the reference row marginal
identified as `μ`.
-/
theorem sinkhornRowObjective_le_finiteCouplingKL_of_rowMarginal_eq_of_pos
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ) (γ γStar : X -> Y -> ℝ)
    (hγ_pos : ∀ x y, 0 < γ x y)
    (hstar_pos : ∀ x y, 0 < γStar x y)
    (hrowγ_pos : ∀ x, 0 < rowMarginal γ x)
    (hrowStar_pos : ∀ x, 0 < rowMarginal γStar x)
    (hstar_row : ∀ x, rowMarginal γStar x = μ x) :
    sinkhornRowObjective μ γ ≤ finiteCouplingKL γ γStar := by
  simpa [sinkhornRowObjective] using
    finiteKL_rowMarginal_le_finiteCouplingKL_of_rowMarginal_eq_of_pos
      γ γStar μ hγ_pos hstar_pos hrowγ_pos hrowStar_pos hstar_row

/--
For a column-normalization step whose previous half-iterate has row marginal
`μ`, the Sinkhorn row objective is bounded by the entropic Bregman movement of
that column-normalization step.
-/
theorem sinkhornRowObjective_columnNormalized_le_entropyBregman
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ) (γHalf : X -> Y -> ℝ)
    (hν_pos : ∀ y, 0 < ν y)
    (hhalf_pos : ∀ x y, 0 < γHalf x y)
    (hhalf_row : ∀ x, rowMarginal γHalf x = μ x)
    (hmass : (∑ y, ν y) = finiteCouplingMass γHalf) :
    sinkhornRowObjective μ (columnNormalizedCoupling ν γHalf) ≤
      finiteCouplingEntropyBregman
        (columnNormalizedCoupling ν γHalf) γHalf := by
  classical
  have hcol_pos : ∀ y, 0 < columnMarginal γHalf y :=
    columnMarginal_pos_of_pos hhalf_pos
  have hnext_pos :
      ∀ x y, 0 < columnNormalizedCoupling ν γHalf x y :=
    columnNormalizedCoupling_pos_of_pos ν γHalf hν_pos hhalf_pos hcol_pos
  have hrow_next_pos :
      ∀ x, 0 < rowMarginal (columnNormalizedCoupling ν γHalf) x :=
    rowMarginal_pos_of_pos hnext_pos
  have hrow_half_pos : ∀ x, 0 < rowMarginal γHalf x :=
    rowMarginal_pos_of_pos hhalf_pos
  have hobj_le_kl :
      sinkhornRowObjective μ (columnNormalizedCoupling ν γHalf) ≤
        finiteCouplingKL (columnNormalizedCoupling ν γHalf) γHalf :=
    sinkhornRowObjective_le_finiteCouplingKL_of_rowMarginal_eq_of_pos
      μ (columnNormalizedCoupling ν γHalf) γHalf hnext_pos hhalf_pos
      hrow_next_pos hrow_half_pos hhalf_row
  have hmass_next :
      finiteCouplingMass (columnNormalizedCoupling ν γHalf) =
        finiteCouplingMass γHalf := by
    rw [finiteCouplingMass_columnNormalizedCoupling ν γHalf
      (fun y => (hcol_pos y).ne'), hmass]
  have hbreg :
      finiteCouplingEntropyBregman
          (columnNormalizedCoupling ν γHalf) γHalf =
        finiteCouplingKL (columnNormalizedCoupling ν γHalf) γHalf :=
    finiteCouplingEntropyBregman_eq_finiteCouplingKL
      (columnNormalizedCoupling ν γHalf) γHalf
      (fun x y => (hnext_pos x y).ne') (fun x y => (hhalf_pos x y).ne')
      hmass_next
  simpa [hbreg] using hobj_le_kl

/--
Column-normalization recurrence bridge for Chewi Theorem 11.8.  Once the
Pythagorean/projection part supplies a decrease by the column-normalization
Bregman movement, the concrete movement dominates the row objective.
-/
theorem chewi118_entropy_one_step_of_columnNormalized_projection_decrease
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    (gammaStar gammaPrev gammaHalf : X -> Y -> ℝ)
    (hν_pos : ∀ y, 0 < ν y)
    (hhalf_pos : ∀ x y, 0 < gammaHalf x y)
    (hhalf_row : ∀ x, rowMarginal gammaHalf x = μ x)
    (hmass : (∑ y, ν y) = finiteCouplingMass gammaHalf)
    (hprojection_decrease :
      finiteCouplingEntropyBregman gammaStar
          (columnNormalizedCoupling ν gammaHalf) +
        finiteCouplingEntropyBregman
          (columnNormalizedCoupling ν gammaHalf) gammaHalf ≤
          finiteCouplingEntropyBregman gammaStar gammaPrev) :
    finiteCouplingEntropyBregman gammaStar
        (columnNormalizedCoupling ν gammaHalf) ≤
      finiteCouplingEntropyBregman gammaStar gammaPrev -
        sinkhornRowObjective μ (columnNormalizedCoupling ν gammaHalf) := by
  have hobj :=
    sinkhornRowObjective_columnNormalized_le_entropyBregman
      μ ν gammaHalf hν_pos hhalf_pos hhalf_row hmass
  nlinarith

/--
Trajectory-indexed version of the column-normalization one-step recurrence for
Chewi Theorem 11.8.
-/
theorem chewi118_entropy_one_step_trajectory_of_columnNormalized_projection_decrease
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    (gamma : ℕ -> X -> Y -> ℝ) (gammaHalf : ℕ -> X -> Y -> ℝ)
    (gammaStar : X -> Y -> ℝ) {N : ℕ}
    (hcolumn_step : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν (gammaHalf n))
    (hν_pos : ∀ y, 0 < ν y)
    (hhalf_pos : ∀ n, n < N -> ∀ x y, 0 < gammaHalf n x y)
    (hhalf_row : ∀ n, n < N -> ∀ x, rowMarginal (gammaHalf n) x = μ x)
    (hmass : ∀ n, n < N -> (∑ y, ν y) = finiteCouplingMass (gammaHalf n))
    (hprojection_decrease : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) +
        finiteCouplingEntropyBregman (gamma (n + 1)) (gammaHalf n) ≤
          finiteCouplingEntropyBregman gammaStar (gamma n)) :
    ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          sinkhornRowObjective μ (gamma (n + 1)) := by
  intro n hn
  have hbase :=
    chewi118_entropy_one_step_of_columnNormalized_projection_decrease
      μ ν gammaStar (gamma n) (gammaHalf n) hν_pos
      (hhalf_pos n hn) (hhalf_row n hn) (hmass n hn)
  have hstep := hcolumn_step n hn
  rw [hstep]
  exact hbase (by simpa [← hstep] using hprojection_decrease n hn)

/--
Finite-array entropic Bregman projection certificate, mirroring the generic
`IsBregmanProjectionStep` API without transporting finite coupling arrays into
a Hilbert-space wrapper.
-/
structure IsFiniteCouplingEntropyProjectionStep
    {X Y : Type*} [Fintype X] [Fintype Y]
    (C : Set (X -> Y -> ℝ)) (base proj : X -> Y -> ℝ) : Prop where
  mem : proj ∈ C
  divergence_nonneg : 0 ≤ finiteCouplingEntropyBregman proj base
  pythagorean : ∀ ⦃z : X -> Y -> ℝ⦄, z ∈ C ->
    finiteCouplingEntropyBregman z proj +
        finiteCouplingEntropyBregman proj base ≤
      finiteCouplingEntropyBregman z base

/--
Two finite entropic Bregman projection steps give the projection-decrease field
needed by the Chewi 11.8 Sinkhorn recurrence.
-/
theorem finiteCouplingEntropyProjection_two_step_decrease
    {X Y : Type*} [Fintype X] [Fintype Y]
    {CRow CCol : Set (X -> Y -> ℝ)}
    {gammaStar gammaPrev gammaHalf gammaNext : X -> Y -> ℝ}
    (hrow : IsFiniteCouplingEntropyProjectionStep CRow gammaPrev gammaHalf)
    (hcol : IsFiniteCouplingEntropyProjectionStep CCol gammaHalf gammaNext)
    (hstar_row : gammaStar ∈ CRow) (hstar_col : gammaStar ∈ CCol) :
    finiteCouplingEntropyBregman gammaStar gammaNext +
        finiteCouplingEntropyBregman gammaNext gammaHalf ≤
      finiteCouplingEntropyBregman gammaStar gammaPrev := by
  have hrow_pyth := hrow.pythagorean hstar_row
  have hcol_pyth := hcol.pythagorean hstar_col
  have hrow_nonneg := hrow.divergence_nonneg
  nlinarith

/--
Finite projection-step version of the Chewi 11.8 one-step recurrence for a
column-normalized Sinkhorn full step.
-/
theorem chewi118_entropy_one_step_of_finiteEntropyProjectionSteps_columnNormalized
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {CRow CCol : Set (X -> Y -> ℝ)}
    (gammaStar gammaPrev gammaHalf : X -> Y -> ℝ)
    (hrow : IsFiniteCouplingEntropyProjectionStep CRow gammaPrev gammaHalf)
    (hcol : IsFiniteCouplingEntropyProjectionStep CCol gammaHalf
      (columnNormalizedCoupling ν gammaHalf))
    (hstar_row : gammaStar ∈ CRow) (hstar_col : gammaStar ∈ CCol)
    (hν_pos : ∀ y, 0 < ν y)
    (hhalf_pos : ∀ x y, 0 < gammaHalf x y)
    (hhalf_row : ∀ x, rowMarginal gammaHalf x = μ x)
    (hmass : (∑ y, ν y) = finiteCouplingMass gammaHalf) :
    finiteCouplingEntropyBregman gammaStar
        (columnNormalizedCoupling ν gammaHalf) ≤
      finiteCouplingEntropyBregman gammaStar gammaPrev -
        sinkhornRowObjective μ (columnNormalizedCoupling ν gammaHalf) := by
  exact
    chewi118_entropy_one_step_of_columnNormalized_projection_decrease
      μ ν gammaStar gammaPrev gammaHalf hν_pos hhalf_pos hhalf_row hmass
      (finiteCouplingEntropyProjection_two_step_decrease
        (hrow := hrow) (hcol := hcol) hstar_row hstar_col)

/--
Trajectory-indexed finite projection-step version of the Chewi 11.8 one-step
recurrence.
-/
theorem chewi118_entropy_one_step_trajectory_of_finiteEntropyProjectionSteps_columnNormalized
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {CRow CCol : Set (X -> Y -> ℝ)}
    (gamma : ℕ -> X -> Y -> ℝ) (gammaHalf : ℕ -> X -> Y -> ℝ)
    (gammaStar : X -> Y -> ℝ) {N : ℕ}
    (hcolumn_step : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν (gammaHalf n))
    (hrow : ∀ n, n < N ->
      IsFiniteCouplingEntropyProjectionStep CRow (gamma n) (gammaHalf n))
    (hcol : ∀ n, n < N ->
      IsFiniteCouplingEntropyProjectionStep CCol (gammaHalf n) (gamma (n + 1)))
    (hstar_row : gammaStar ∈ CRow) (hstar_col : gammaStar ∈ CCol)
    (hν_pos : ∀ y, 0 < ν y)
    (hhalf_pos : ∀ n, n < N -> ∀ x y, 0 < gammaHalf n x y)
    (hhalf_row : ∀ n, n < N -> ∀ x, rowMarginal (gammaHalf n) x = μ x)
    (hmass : ∀ n, n < N -> (∑ y, ν y) = finiteCouplingMass (gammaHalf n)) :
    ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          sinkhornRowObjective μ (gamma (n + 1)) := by
  intro n hn
  have hstep := hcolumn_step n hn
  have hcol' :
      IsFiniteCouplingEntropyProjectionStep CCol (gammaHalf n)
        (columnNormalizedCoupling ν (gammaHalf n)) := by
    simpa [← hstep] using hcol n hn
  rw [hstep]
  exact
    chewi118_entropy_one_step_of_finiteEntropyProjectionSteps_columnNormalized
      μ ν gammaStar (gamma n) (gammaHalf n)
      (hrow n hn) hcol' hstar_row hstar_col hν_pos
      (hhalf_pos n hn) (hhalf_row n hn) (hmass n hn)

/-- Finite Gibbs nonnegativity for the Sinkhorn row objective. -/
theorem sinkhornRowObjective_nonneg_of_nonneg_of_pos_of_mass_eq
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ)
    (hrow_nonneg : ∀ x, 0 ≤ rowMarginal γ x)
    (hμ_pos : ∀ x, 0 < μ x)
    (hmass : finiteCouplingMass γ = ∑ x, μ x) :
    0 ≤ sinkhornRowObjective μ γ := by
  have hsum : (∑ x, rowMarginal γ x) = ∑ x, μ x := by
    rw [sum_rowMarginal_eq_finiteCouplingMass, hmass]
  exact finiteKL_nonneg_of_nonneg_of_pos_of_sum_eq
    (rowMarginal γ) μ hrow_nonneg hμ_pos hsum

/-- Finite Gibbs inequality for positive reference coupling arrays with equal mass. -/
theorem finiteCouplingKL_nonneg_of_nonneg_of_pos_of_mass_eq
    {X Y : Type*} [Fintype X] [Fintype Y]
    (γ η : X -> Y -> ℝ)
    (hγ_nonneg : ∀ x y, 0 ≤ γ x y)
    (hη_pos : ∀ x y, 0 < η x y)
    (hmass : finiteCouplingMass γ = finiteCouplingMass η) :
    0 ≤ finiteCouplingKL γ η := by
  classical
  have hsum_terms :
      (∑ x, ∑ y, (γ x y - η x y)) ≤ finiteCouplingKL γ η := by
    unfold finiteCouplingKL
    exact Finset.sum_le_sum fun x _hx =>
      Finset.sum_le_sum fun y _hy => finiteKL_term_lower (hγ_nonneg x y) (hη_pos x y)
  have hzero : (∑ x, ∑ y, (γ x y - η x y)) = 0 := by
    rw [show (∑ x, ∑ y, (γ x y - η x y)) =
        (∑ x, ∑ y, γ x y) - (∑ x, ∑ y, η x y) by
      simp [Finset.sum_sub_distrib]]
    simpa [finiteCouplingMass] using sub_eq_zero.mpr hmass
  nlinarith

/--
Nonnegativity of the finite entropic Bregman display for positive equal-mass
couplings.
-/
theorem finiteCouplingEntropyBregman_nonneg_of_pos_of_mass_eq
    {X Y : Type*} [Fintype X] [Fintype Y]
    (γ η : X -> Y -> ℝ)
    (hγ_pos : ∀ x y, 0 < γ x y)
    (hη_pos : ∀ x y, 0 < η x y)
    (hmass : finiteCouplingMass γ = finiteCouplingMass η) :
    0 ≤ finiteCouplingEntropyBregman γ η := by
  rw [finiteCouplingEntropyBregman_eq_finiteCouplingKL
    γ η (fun x y => (hγ_pos x y).ne') (fun x y => (hη_pos x y).ne') hmass]
  exact finiteCouplingKL_nonneg_of_nonneg_of_pos_of_mass_eq
    γ η (fun x y => (hγ_pos x y).le) hη_pos hmass

/--
Concrete finite Sinkhorn row normalization is an entropic Bregman projection
onto the row-marginal constraint.
-/
theorem isFiniteCouplingEntropyProjectionStep_rowNormalized
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ) (base : X -> Y -> ℝ)
    (hμ_pos : ∀ x, 0 < μ x)
    (hbase_pos : ∀ x y, 0 < base x y)
    (hrow_pos : ∀ x, 0 < rowMarginal base x)
    (hmass : (∑ x, μ x) = finiteCouplingMass base) :
    IsFiniteCouplingEntropyProjectionStep
      (finiteRowMarginalConstraint μ) base (rowNormalizedCoupling μ base) where
  mem := by
    intro x
    exact rowMarginal_rowNormalizedCoupling μ base (fun x => (hrow_pos x).ne') x
  divergence_nonneg := by
    exact finiteCouplingEntropyBregman_nonneg_of_pos_of_mass_eq
      (rowNormalizedCoupling μ base) base
      (rowNormalizedCoupling_pos_of_pos μ base hμ_pos hbase_pos hrow_pos)
      hbase_pos
      (by
        rw [finiteCouplingMass_rowNormalizedCoupling μ base
          (fun x => (hrow_pos x).ne'), hmass])
  pythagorean := by
    intro z hz
    have hrow :
        ∀ x, rowMarginal z x =
          rowMarginal (rowNormalizedCoupling μ base) x := by
      intro x
      have hz_row : rowMarginal z x = μ x := by
        simpa [finiteRowMarginalConstraint] using hz x
      rw [hz_row,
        rowMarginal_rowNormalizedCoupling μ base (fun x => (hrow_pos x).ne') x]
    exact le_of_eq
      (finiteCouplingEntropyBregman_add_eq_of_row_log_diff
        z (rowNormalizedCoupling μ base) base
        (fun x => Real.log (μ x / rowMarginal base x))
        (fun x y =>
          rowNormalizedCoupling_log_sub_log_eq μ base
            (fun x => (hμ_pos x).ne') (fun x y => (hbase_pos x y).ne')
            (fun x => (hrow_pos x).ne') x y)
        hrow)

/--
Concrete finite Sinkhorn column normalization is an entropic Bregman projection
onto the column-marginal constraint.
-/
theorem isFiniteCouplingEntropyProjectionStep_columnNormalized
    {X Y : Type*} [Fintype X] [Fintype Y]
    (ν : Y -> ℝ) (base : X -> Y -> ℝ)
    (hν_pos : ∀ y, 0 < ν y)
    (hbase_pos : ∀ x y, 0 < base x y)
    (hcol_pos : ∀ y, 0 < columnMarginal base y)
    (hmass : (∑ y, ν y) = finiteCouplingMass base) :
    IsFiniteCouplingEntropyProjectionStep
      (finiteColumnMarginalConstraint ν) base
      (columnNormalizedCoupling ν base) where
  mem := by
    intro y
    exact columnMarginal_columnNormalizedCoupling ν base
      (fun y => (hcol_pos y).ne') y
  divergence_nonneg := by
    exact finiteCouplingEntropyBregman_nonneg_of_pos_of_mass_eq
      (columnNormalizedCoupling ν base) base
      (columnNormalizedCoupling_pos_of_pos ν base hν_pos hbase_pos hcol_pos)
      hbase_pos
      (by
        rw [finiteCouplingMass_columnNormalizedCoupling ν base
          (fun y => (hcol_pos y).ne'), hmass])
  pythagorean := by
    intro z hz
    have hcol :
        ∀ y, columnMarginal z y =
          columnMarginal (columnNormalizedCoupling ν base) y := by
      intro y
      have hz_col : columnMarginal z y = ν y := by
        simpa [finiteColumnMarginalConstraint] using hz y
      rw [hz_col,
        columnMarginal_columnNormalizedCoupling ν base
          (fun y => (hcol_pos y).ne') y]
    exact le_of_eq
      (finiteCouplingEntropyBregman_add_eq_of_column_log_diff
        z (columnNormalizedCoupling ν base) base
        (fun y => Real.log (ν y / columnMarginal base y))
        (fun x y =>
          columnNormalizedCoupling_log_sub_log_eq ν base
            (fun y => (hν_pos y).ne') (fun x y => (hbase_pos x y).ne')
            (fun y => (hcol_pos y).ne') x y)
        hcol)

/--
Concrete one-cycle finite Sinkhorn recurrence: row-normalize toward `μ`, then
column-normalize toward `ν`.
-/
theorem chewi118_entropy_one_step_of_concreteSinkhornNormalizations
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    (gammaStar gammaPrev : X -> Y -> ℝ)
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hprev_pos : ∀ x y, 0 < gammaPrev x y)
    (hprev_mass : (∑ x, μ x) = finiteCouplingMass gammaPrev)
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x) :
    finiteCouplingEntropyBregman gammaStar
        (columnNormalizedCoupling ν (rowNormalizedCoupling μ gammaPrev)) ≤
      finiteCouplingEntropyBregman gammaStar gammaPrev -
        sinkhornRowObjective μ
          (columnNormalizedCoupling ν (rowNormalizedCoupling μ gammaPrev)) := by
  classical
  have hprev_row_pos : ∀ x, 0 < rowMarginal gammaPrev x :=
    rowMarginal_pos_of_pos hprev_pos
  have hhalf_pos :
      ∀ x y, 0 < rowNormalizedCoupling μ gammaPrev x y :=
    rowNormalizedCoupling_pos_of_pos μ gammaPrev hμ_pos hprev_pos hprev_row_pos
  have hhalf_row :
      ∀ x, rowMarginal (rowNormalizedCoupling μ gammaPrev) x = μ x :=
    rowMarginal_rowNormalizedCoupling μ gammaPrev
      (fun x => (hprev_row_pos x).ne')
  have hrow_step :
      IsFiniteCouplingEntropyProjectionStep
        (finiteRowMarginalConstraint μ) gammaPrev
        (rowNormalizedCoupling μ gammaPrev) :=
    isFiniteCouplingEntropyProjectionStep_rowNormalized
      μ gammaPrev hμ_pos hprev_pos hprev_row_pos hprev_mass
  have hhalf_col_pos :
      ∀ y, 0 < columnMarginal (rowNormalizedCoupling μ gammaPrev) y :=
    columnMarginal_pos_of_pos hhalf_pos
  have hhalf_mass :
      (∑ y, ν y) =
        finiteCouplingMass (rowNormalizedCoupling μ gammaPrev) := by
    rw [finiteCouplingMass_rowNormalizedCoupling μ gammaPrev
      (fun x => (hprev_row_pos x).ne')]
    exact htarget_mass
  have hcol_step :
      IsFiniteCouplingEntropyProjectionStep
        (finiteColumnMarginalConstraint ν) (rowNormalizedCoupling μ gammaPrev)
        (columnNormalizedCoupling ν (rowNormalizedCoupling μ gammaPrev)) :=
    isFiniteCouplingEntropyProjectionStep_columnNormalized
      ν (rowNormalizedCoupling μ gammaPrev) hν_pos hhalf_pos hhalf_col_pos
      hhalf_mass
  exact
    chewi118_entropy_one_step_of_finiteEntropyProjectionSteps_columnNormalized
      μ ν gammaStar gammaPrev (rowNormalizedCoupling μ gammaPrev)
      hrow_step hcol_step hstar_row hstar_col hν_pos hhalf_pos hhalf_row
      hhalf_mass

/--
Trajectory form of the concrete finite Sinkhorn one-cycle recurrence.
-/
theorem chewi118_entropy_one_step_trajectory_of_concreteSinkhornNormalizations
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    (gamma : ℕ -> X -> Y -> ℝ) (gammaStar : X -> Y -> ℝ) {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hgamma_pos : ∀ n, n < N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x) :
    ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          sinkhornRowObjective μ (gamma (n + 1)) := by
  intro n hn
  have hbase :=
    chewi118_entropy_one_step_of_concreteSinkhornNormalizations
      μ ν gammaStar (gamma n) hstar_row hstar_col hμ_pos hν_pos
      (hgamma_pos n hn) (hgamma_mass n hn) htarget_mass
  rw [hstep n hn]
  exact hbase

/--
Concrete finite Sinkhorn row-normalization KL identity.  Under nonzero support
and row denominators, normalizing rows toward `μ` makes the coupling KL against
the previous array exactly the row-marginal KL.
-/
theorem finiteCouplingKL_rowNormalizedCoupling_eq_finiteKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ)
    (hrow_ne : ∀ x, rowMarginal γ x ≠ 0)
    (hγ_ne : ∀ x y, γ x y ≠ 0) :
    finiteCouplingKL (rowNormalizedCoupling μ γ) γ =
      finiteKL μ (rowMarginal γ) := by
  classical
  refine finiteCouplingKL_eq_finiteKL_of_row_ratio
    (γ := rowNormalizedCoupling μ γ) (η := γ)
    (μ := μ) (row := rowMarginal γ) ?_ ?_
  · intro x
    exact rowMarginal_rowNormalizedCoupling μ γ hrow_ne x
  · intro x y
    unfold rowNormalizedCoupling
    field_simp [hrow_ne x, hγ_ne x y]

/--
Concrete finite Sinkhorn column-normalization KL identity.  Under nonzero
support and column denominators, normalizing columns toward `ν` makes the
coupling KL against the previous array exactly the column-marginal KL.
-/
theorem finiteCouplingKL_columnNormalizedCoupling_eq_finiteKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    (ν : Y -> ℝ) (γ : X -> Y -> ℝ)
    (hcol_ne : ∀ y, columnMarginal γ y ≠ 0)
    (hγ_ne : ∀ x y, γ x y ≠ 0) :
    finiteCouplingKL (columnNormalizedCoupling ν γ) γ =
      finiteKL ν (columnMarginal γ) := by
  classical
  refine finiteCouplingKL_eq_finiteKL_of_column_ratio
    (γ := columnNormalizedCoupling ν γ) (η := γ)
    (ν := ν) (col := columnMarginal γ) ?_ ?_
  · intro y
    exact columnMarginal_columnNormalizedCoupling ν γ hcol_ne y
  · intro x y
    unfold columnNormalizedCoupling
    field_simp [hcol_ne y, hγ_ne x y]

/--
Row-normalization version of the entropic Bregman/KL identity.  If the target
row law has the same total mass as the current coupling, then the entropic
Bregman movement from the previous coupling to its row normalization is exactly
the row marginal KL.
-/
theorem finiteCouplingEntropyBregman_rowNormalizedCoupling_eq_finiteKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ) (γ : X -> Y -> ℝ)
    (hμ_ne : ∀ x, μ x ≠ 0)
    (hγ_ne : ∀ x y, γ x y ≠ 0)
    (hrow_ne : ∀ x, rowMarginal γ x ≠ 0)
    (hmass : (∑ x, μ x) = finiteCouplingMass γ) :
    finiteCouplingEntropyBregman (rowNormalizedCoupling μ γ) γ =
      finiteKL μ (rowMarginal γ) := by
  calc
    finiteCouplingEntropyBregman (rowNormalizedCoupling μ γ) γ =
        finiteCouplingKL (rowNormalizedCoupling μ γ) γ := by
          exact finiteCouplingEntropyBregman_eq_finiteCouplingKL
            (rowNormalizedCoupling μ γ) γ
            (rowNormalizedCoupling_ne_of_ne μ γ hμ_ne hγ_ne hrow_ne)
            hγ_ne
            (by
              rw [finiteCouplingMass_rowNormalizedCoupling μ γ hrow_ne, hmass])
    _ = finiteKL μ (rowMarginal γ) :=
          finiteCouplingKL_rowNormalizedCoupling_eq_finiteKL μ γ hrow_ne hγ_ne

/--
Column-normalization version of the entropic Bregman/KL identity.  If the
target column law has the same total mass as the current coupling, then the
entropic Bregman movement from the previous coupling to its column
normalization is exactly the column marginal KL.
-/
theorem finiteCouplingEntropyBregman_columnNormalizedCoupling_eq_finiteKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    (ν : Y -> ℝ) (γ : X -> Y -> ℝ)
    (hν_ne : ∀ y, ν y ≠ 0)
    (hγ_ne : ∀ x y, γ x y ≠ 0)
    (hcol_ne : ∀ y, columnMarginal γ y ≠ 0)
    (hmass : (∑ y, ν y) = finiteCouplingMass γ) :
    finiteCouplingEntropyBregman (columnNormalizedCoupling ν γ) γ =
      finiteKL ν (columnMarginal γ) := by
  calc
    finiteCouplingEntropyBregman (columnNormalizedCoupling ν γ) γ =
        finiteCouplingKL (columnNormalizedCoupling ν γ) γ := by
          exact finiteCouplingEntropyBregman_eq_finiteCouplingKL
            (columnNormalizedCoupling ν γ) γ
            (columnNormalizedCoupling_ne_of_ne ν γ hν_ne hγ_ne hcol_ne)
            hγ_ne
            (by
              rw [finiteCouplingMass_columnNormalizedCoupling ν γ hcol_ne, hmass])
    _ = finiteKL ν (columnMarginal γ) :=
          finiteCouplingKL_columnNormalizedCoupling_eq_finiteKL ν γ hcol_ne hγ_ne

/--
Source-shaped Bregman projection certificate.

The `pythagorean` field is Exercise 10.1 in the orientation used in Chewi
Lemma 11.2:
`D_phi(z, base) >= D_phi(z, proj) + D_phi(proj, base)`.
-/
structure IsBregmanProjectionStep
    (C : Set E) (phi : E -> ℝ) (gradPhi : E -> E)
    (base proj : E) : Prop where
  mem : proj ∈ C
  divergence_nonneg : 0 ≤ bregmanDivergence phi gradPhi proj base
  pythagorean : ∀ ⦃z : E⦄, z ∈ C ->
    bregmanDivergence phi gradPhi z proj +
        bregmanDivergence phi gradPhi proj base ≤
      bregmanDivergence phi gradPhi z base

/--
ABP trajectory:
`x_{n+1}` is the Bregman projection of `y_n` onto `C₁`, and `y_{n+1}` is the
Bregman projection of `x_{n+1}` onto `C₂`.
-/
structure IsAlternatingBregmanProjectionTrajectory
    (C₁ C₂ : Set E) (phi : E -> ℝ) (gradPhi : E -> E)
    (x y : ℕ -> E) : Prop where
  x_step : ∀ n, IsBregmanProjectionStep C₁ phi gradPhi (y n) (x (n + 1))
  y_step : ∀ n, IsBregmanProjectionStep C₂ phi gradPhi (x (n + 1)) (y (n + 1))

theorem IsAlternatingBregmanProjectionTrajectory.x_mem_succ
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E}
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (n : ℕ) :
    x (n + 1) ∈ C₁ :=
  (htraj.x_step n).mem

theorem IsAlternatingBregmanProjectionTrajectory.y_mem_succ
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E}
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (n : ℕ) :
    y (n + 1) ∈ C₂ :=
  (htraj.y_step n).mem

/--
First half of the monotonicity chain in Lemma 11.2:
`D_phi(x_*, x_{n+1}) <= D_phi(x_*, y_n)`.
-/
theorem alternatingBregmanProjection_star_x_le_star_y
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} (n : ℕ)
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) :
    bregmanDivergence phi gradPhi xStar (x (n + 1)) ≤
      bregmanDivergence phi gradPhi xStar (y n) := by
  have hpyth := (htraj.x_step n).pythagorean hxStar₁
  have hnonneg := (htraj.x_step n).divergence_nonneg
  nlinarith

/--
Second half of the monotonicity chain in Lemma 11.2:
`D_phi(x_*, y_{n+1}) <= D_phi(x_*, x_{n+1})`.
-/
theorem alternatingBregmanProjection_star_y_succ_le_star_x
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} (n : ℕ)
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₂ : xStar ∈ C₂) :
    bregmanDivergence phi gradPhi xStar (y (n + 1)) ≤
      bregmanDivergence phi gradPhi xStar (x (n + 1)) := by
  have hpyth := (htraj.y_step n).pythagorean hxStar₂
  have hnonneg := (htraj.y_step n).divergence_nonneg
  nlinarith

/-- The two monotonicity halves imply `D_phi(x_*, y_{n+1}) <= D_phi(x_*, y_n)`. -/
theorem alternatingBregmanProjection_star_y_succ_le_star_y
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} (n : ℕ)
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) (hxStar₂ : xStar ∈ C₂) :
    bregmanDivergence phi gradPhi xStar (y (n + 1)) ≤
      bregmanDivergence phi gradPhi xStar (y n) :=
  (alternatingBregmanProjection_star_y_succ_le_star_x n htraj hxStar₂).trans
    (alternatingBregmanProjection_star_x_le_star_y n htraj hxStar₁)

/--
One ABP cycle decrease.  This is the finite one-step inequality that
telescopes in Chewi Lemma 11.2.
-/
theorem alternatingBregmanProjection_cycle_decrease
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} (n : ℕ)
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) (hxStar₂ : xStar ∈ C₂) :
    bregmanDivergence phi gradPhi xStar (y (n + 1)) +
        (bregmanDivergence phi gradPhi (x (n + 1)) (y n) +
          bregmanDivergence phi gradPhi (y (n + 1)) (x (n + 1))) ≤
      bregmanDivergence phi gradPhi xStar (y n) := by
  have hx := (htraj.x_step n).pythagorean hxStar₁
  have hy := (htraj.y_step n).pythagorean hxStar₂
  nlinarith

/--
Finite Lemma 11.2 telescope with the terminal Bregman term retained.
-/
theorem chewi112_finite_sum_with_terminal_le
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} (N : ℕ)
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) (hxStar₂ : xStar ∈ C₂) :
    bregmanDivergence phi gradPhi xStar (y N) +
        (∑ n ∈ Finset.range N,
          (bregmanDivergence phi gradPhi (x (n + 1)) (y n) +
            bregmanDivergence phi gradPhi (y (n + 1)) (x (n + 1)))) ≤
      bregmanDivergence phi gradPhi xStar (y 0) := by
  let D : ℕ -> ℝ := fun n => bregmanDivergence phi gradPhi xStar (y n)
  let gap : ℕ -> ℝ := fun n =>
    bregmanDivergence phi gradPhi (x (n + 1)) (y n) +
      bregmanDivergence phi gradPhi (y (n + 1)) (x (n + 1))
  have hstep : ∀ n, n < N -> gap n ≤ D n - D (n + 1) := by
    intro n _hn
    have hcycle :=
      alternatingBregmanProjection_cycle_decrease
        (C₁ := C₁) (C₂ := C₂) (phi := phi) (gradPhi := gradPhi)
        (x := x) (y := y) (xStar := xStar)
        n htraj hxStar₁ hxStar₂
    dsimp [D, gap] at hcycle ⊢
    nlinarith
  have hsum :
      (∑ n ∈ Finset.range N, gap n) ≤
        ∑ n ∈ Finset.range N, (D n - D (n + 1)) := by
    exact Finset.sum_le_sum fun n hn => hstep n (Finset.mem_range.mp hn)
  have hsum_bound :
      (∑ n ∈ Finset.range N, gap n) ≤ D 0 - D N := by
    calc
      (∑ n ∈ Finset.range N, gap n)
          ≤ ∑ n ∈ Finset.range N, (D n - D (n + 1)) := hsum
      _ = D 0 - D N := by
          simpa using sum_range_sub_succ D N
  dsimp [D, gap] at hsum_bound ⊢
  nlinarith

/--
Finite Lemma 11.2 in the displayed summability orientation, with the terminal
Bregman term discharged separately.
-/
theorem chewi112_finite_sum_le
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} (N : ℕ)
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) (hxStar₂ : xStar ∈ C₂)
    (hterminal_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (y N)) :
    (∑ n ∈ Finset.range N,
      (bregmanDivergence phi gradPhi (x (n + 1)) (y n) +
        bregmanDivergence phi gradPhi (y (n + 1)) (x (n + 1)))) ≤
      bregmanDivergence phi gradPhi xStar (y 0) := by
  have hmain :=
    chewi112_finite_sum_with_terminal_le
      (C₁ := C₁) (C₂ := C₂) (phi := phi) (gradPhi := gradPhi)
      (x := x) (y := y) (xStar := xStar) N htraj hxStar₁ hxStar₂
  nlinarith

/--
Chewi display `(11.1)` in existential finite-minimum form.
-/
theorem chewi113_exists_small_abp_cycle_gap
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} {N : ℕ}
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) (hxStar₂ : xStar ∈ C₂)
    (hterminal_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (y N))
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      bregmanDivergence phi gradPhi (x (n + 1)) (y n) +
          bregmanDivergence phi gradPhi (y (n + 1)) (x (n + 1)) ≤
        bregmanDivergence phi gradPhi xStar (y 0) / (N : ℝ) := by
  let gap : ℕ -> ℝ := fun n =>
    bregmanDivergence phi gradPhi (x (n + 1)) (y n) +
      bregmanDivergence phi gradPhi (y (n + 1)) (x (n + 1))
  have hsum :=
    chewi112_finite_sum_le
      (C₁ := C₁) (C₂ := C₂) (phi := phi) (gradPhi := gradPhi)
      (x := x) (y := y) (xStar := xStar) N
      htraj hxStar₁ hxStar₂ hterminal_nonneg
  have hN_pos_nat : 0 < N := Nat.pos_of_ne_zero hN
  have hN_pos : 0 < (N : ℝ) := by
    exact_mod_cast hN_pos_nat
  have hsum_avg :
      (∑ n ∈ Finset.range N, gap n) ≤
        (N : ℝ) * (bregmanDivergence phi gradPhi xStar (y 0) / (N : ℝ)) := by
    have hmul :
        (N : ℝ) *
            (bregmanDivergence phi gradPhi xStar (y 0) / (N : ℝ)) =
          bregmanDivergence phi gradPhi xStar (y 0) := by
      field_simp [hN_pos.ne']
    simpa [gap, hmul] using hsum
  simpa [gap] using
    exists_le_average_of_sum_le
      (a := gap) (N := N)
      (B := bregmanDivergence phi gradPhi xStar (y 0) / (N : ℝ))
      hN hsum_avg

/--
Chewi Theorem 11.7, supplied-interface Sinkhorn selector.  Lemma 11.2 gives a
cycle with small total KL movement; Pinsker lower bounds for the two Sinkhorn
half-steps then give one row-normalized and one column-normalized iterate with
small marginal error.
-/
theorem chewi117_exists_sinkhorn_marginal_errors_le_of_abp
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} {N : ℕ}
    {rowErr colErr : ℕ -> ℝ} {eps : ℝ}
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) (hxStar₂ : xStar ∈ C₂)
    (hterminal_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (y N))
    (hN : N ≠ 0) (heps_nonneg : 0 ≤ eps)
    (hbudget :
      bregmanDivergence phi gradPhi xStar (y 0) / (N : ℝ) ≤
        eps ^ (2 : ℕ) / 2)
    (hrow_nonneg : ∀ n, 0 ≤ rowErr n)
    (hcol_nonneg : ∀ n, 0 ≤ colErr n)
    (hrow_pinsker : ∀ n,
      rowErr n ^ (2 : ℕ) / 2 ≤
        bregmanDivergence phi gradPhi (x (n + 1)) (y n))
    (hcol_pinsker : ∀ n,
      colErr n ^ (2 : ℕ) / 2 ≤
        bregmanDivergence phi gradPhi (y (n + 1)) (x (n + 1))) :
    ∃ n, n < N ∧ rowErr n ≤ eps ∧ colErr n ≤ eps := by
  obtain ⟨n, hn, hcycle⟩ :=
    chewi113_exists_small_abp_cycle_gap
      (C₁ := C₁) (C₂ := C₂) (phi := phi) (gradPhi := gradPhi)
      (x := x) (y := y) (xStar := xStar) (N := N)
      htraj hxStar₁ hxStar₂ hterminal_nonneg hN
  have hx_nonneg := (htraj.x_step n).divergence_nonneg
  have hy_nonneg := (htraj.y_step n).divergence_nonneg
  have hrow_sq_le : rowErr n ^ (2 : ℕ) ≤ eps ^ (2 : ℕ) := by
    nlinarith [hrow_pinsker n, hy_nonneg, hcycle, hbudget]
  have hcol_sq_le : colErr n ^ (2 : ℕ) ≤ eps ^ (2 : ℕ) := by
    nlinarith [hcol_pinsker n, hx_nonneg, hcycle, hbudget]
  have hrow_le : rowErr n ≤ eps :=
    (sq_le_sq₀ (hrow_nonneg n) heps_nonneg).mp hrow_sq_le
  have hcol_le : colErr n ≤ eps :=
    (sq_le_sq₀ (hcol_nonneg n) heps_nonneg).mp hcol_sq_le
  exact ⟨n, hn, hrow_le, hcol_le⟩

/--
Chewi Theorem 11.7 selector in the source orientation that chooses the
column-correct full Sinkhorn iterate `γⁿ`.  The supplied `hcol_zero` is the
finite marginal identity saying this iterate already has the correct
`Y`-marginal; the row Pinsker lower bound controls the remaining marginal
error.
-/
theorem chewi117_exists_sinkhorn_full_iterate_error_sum_le_of_abp
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} {N : ℕ}
    {rowErr colErr : ℕ -> ℝ} {eps : ℝ}
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) (hxStar₂ : xStar ∈ C₂)
    (hterminal_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (y N))
    (hN : N ≠ 0) (heps_nonneg : 0 ≤ eps)
    (hbudget :
      bregmanDivergence phi gradPhi xStar (y 0) / (N : ℝ) ≤
        eps ^ (2 : ℕ) / 2)
    (hrow_nonneg : ∀ n, 0 ≤ rowErr n)
    (hcol_zero : ∀ n, colErr n = 0)
    (hrow_pinsker : ∀ n,
      rowErr n ^ (2 : ℕ) / 2 ≤
        bregmanDivergence phi gradPhi (x (n + 1)) (y n)) :
    ∃ n, n < N ∧ rowErr n + colErr n ≤ eps := by
  obtain ⟨n, hn, hcycle⟩ :=
    chewi113_exists_small_abp_cycle_gap
      (C₁ := C₁) (C₂ := C₂) (phi := phi) (gradPhi := gradPhi)
      (x := x) (y := y) (xStar := xStar) (N := N)
      htraj hxStar₁ hxStar₂ hterminal_nonneg hN
  have hy_nonneg := (htraj.y_step n).divergence_nonneg
  have hrow_sq_le : rowErr n ^ (2 : ℕ) ≤ eps ^ (2 : ℕ) := by
    nlinarith [hrow_pinsker n, hy_nonneg, hcycle, hbudget]
  have hrow_le : rowErr n ≤ eps :=
    (sq_le_sq₀ (hrow_nonneg n) heps_nonneg).mp hrow_sq_le
  refine ⟨n, hn, ?_⟩
  rw [hcol_zero n]
  nlinarith

/--
Chewi Theorem 11.7 selector in the source orientation that chooses the
row-correct half Sinkhorn iterate `γⁿ⁺¹ᐟ²`.  The supplied `hrow_zero` is the
finite marginal identity saying this half-step already has the correct
`X`-marginal; the column Pinsker lower bound controls the remaining marginal
error.
-/
theorem chewi117_exists_sinkhorn_half_iterate_error_sum_le_of_abp
    {C₁ C₂ : Set E} {phi : E -> ℝ} {gradPhi : E -> E}
    {x y : ℕ -> E} {xStar : E} {N : ℕ}
    {rowErr colErr : ℕ -> ℝ} {eps : ℝ}
    (htraj : IsAlternatingBregmanProjectionTrajectory C₁ C₂ phi gradPhi x y)
    (hxStar₁ : xStar ∈ C₁) (hxStar₂ : xStar ∈ C₂)
    (hterminal_nonneg : 0 ≤ bregmanDivergence phi gradPhi xStar (y N))
    (hN : N ≠ 0) (heps_nonneg : 0 ≤ eps)
    (hbudget :
      bregmanDivergence phi gradPhi xStar (y 0) / (N : ℝ) ≤
        eps ^ (2 : ℕ) / 2)
    (hrow_zero : ∀ n, rowErr n = 0)
    (hcol_nonneg : ∀ n, 0 ≤ colErr n)
    (hcol_pinsker : ∀ n,
      colErr n ^ (2 : ℕ) / 2 ≤
        bregmanDivergence phi gradPhi (y (n + 1)) (x (n + 1))) :
    ∃ n, n < N ∧ rowErr n + colErr n ≤ eps := by
  obtain ⟨n, hn, hcycle⟩ :=
    chewi113_exists_small_abp_cycle_gap
      (C₁ := C₁) (C₂ := C₂) (phi := phi) (gradPhi := gradPhi)
      (x := x) (y := y) (xStar := xStar) (N := N)
      htraj hxStar₁ hxStar₂ hterminal_nonneg hN
  have hx_nonneg := (htraj.x_step n).divergence_nonneg
  have hcol_sq_le : colErr n ^ (2 : ℕ) ≤ eps ^ (2 : ℕ) := by
    nlinarith [hcol_pinsker n, hx_nonneg, hcycle, hbudget]
  have hcol_le : colErr n ≤ eps :=
    (sq_le_sq₀ (hcol_nonneg n) heps_nonneg).mp hcol_sq_le
  refine ⟨n, hn, ?_⟩
  rw [hrow_zero n]
  nlinarith

/--
Finite-array source-shaped certificate for Chewi Theorem 11.8 after
interpreting Sinkhorn as mirror descent with the entropic mirror map.  This
version avoids an `InnerProductSpace` wrapper around curried finite arrays and
uses `finiteCouplingEntropyBregman` directly.
-/
structure IsChewi118FiniteSinkhornEntropyCertificate
    {X Y : Type*} [Fintype X] [Fintype Y]
    (gamma : ℕ -> X -> Y -> ℝ) (gammaStar : X -> Y -> ℝ)
    (rowMarginalKL : ℕ -> ℝ) (initialCouplingKL : ℝ) (N : ℕ) : Prop where
  terminal_nonneg : 0 ≤ finiteCouplingEntropyBregman gammaStar (gamma N)
  one_step : ∀ n, n < N ->
    finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
      finiteCouplingEntropyBregman gammaStar (gamma n) -
        rowMarginalKL (n + 1)
  monotone_to_last : ∀ n, n < N ->
    rowMarginalKL N ≤ rowMarginalKL (n + 1)
  initial_eq : finiteCouplingEntropyBregman gammaStar (gamma 0) =
    initialCouplingKL

/--
Chewi Theorem 11.8 finite-array endpoint: a zero-error entropic Bregman
recurrence plus monotone marginal KL gaps yields the displayed last-iterate
`KL(gammaStar || gamma^0) / N` bound.
-/
theorem IsChewi118FiniteSinkhornEntropyCertificate.last_rowMarginalKL_le
    {X Y : Type*} [Fintype X] [Fintype Y]
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {rowMarginalKL : ℕ -> ℝ} {initialCouplingKL : ℝ} {N : ℕ}
    (hcert : IsChewi118FiniteSinkhornEntropyCertificate
      gamma gammaStar rowMarginalKL initialCouplingKL N)
    (hN : N ≠ 0) :
    rowMarginalKL N ≤ initialCouplingKL / (N : ℝ) := by
  have hmain :=
    chewi118_last_gap_le_of_recurrence
      (D := fun n => finiteCouplingEntropyBregman gammaStar (gamma n))
      (gap := rowMarginalKL) hN
      hcert.terminal_nonneg hcert.one_step hcert.monotone_to_last
  simpa [hcert.initial_eq] using hmain

/--
Theorem-facing wrapper for the finite-array Sinkhorn entropy certificate.
-/
theorem chewi118_finiteSinkhorn_last_rowMarginalKL_le_of_entropyCertificate
    {X Y : Type*} [Fintype X] [Fintype Y]
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {rowMarginalKL : ℕ -> ℝ} {initialCouplingKL : ℝ} {N : ℕ}
    (hcert : IsChewi118FiniteSinkhornEntropyCertificate
      gamma gammaStar rowMarginalKL initialCouplingKL N)
    (hN : N ≠ 0) :
    rowMarginalKL N ≤ initialCouplingKL / (N : ℝ) :=
  hcert.last_rowMarginalKL_le hN

/--
Build the finite Sinkhorn entropy certificate with the source initial
coupling-KL value, discharging the certificate's `initial_eq` field from the
entropic-Bregman/KL identity.
-/
theorem IsChewi118FiniteSinkhornEntropyCertificate.of_initialCouplingKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {rowMarginalKL : ℕ -> ℝ} {N : ℕ}
    (hterminal_nonneg : 0 ≤ finiteCouplingEntropyBregman gammaStar (gamma N))
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          rowMarginalKL (n + 1))
    (hmono : ∀ n, n < N ->
      rowMarginalKL N ≤ rowMarginalKL (n + 1))
    (hstar_ne : ∀ x y, gammaStar x y ≠ 0)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0)) :
    IsChewi118FiniteSinkhornEntropyCertificate
      gamma gammaStar rowMarginalKL (finiteCouplingKL gammaStar (gamma 0)) N where
  terminal_nonneg := hterminal_nonneg
  one_step := hone_step
  monotone_to_last := hmono
  initial_eq :=
    finiteCouplingEntropyBregman_eq_finiteCouplingKL
      gammaStar (gamma 0) hstar_ne hgamma0_ne hmass0

/--
Chewi Theorem 11.8 finite-array endpoint with the initial divergence identified
as the source coupling KL `KL(gammaStar || gamma^0)`.
-/
theorem chewi118_finiteSinkhorn_last_rowMarginalKL_le_of_entropyRecurrence_initialKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {rowMarginalKL : ℕ -> ℝ} {N : ℕ}
    (hterminal_nonneg : 0 ≤ finiteCouplingEntropyBregman gammaStar (gamma N))
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          rowMarginalKL (n + 1))
    (hmono : ∀ n, n < N ->
      rowMarginalKL N ≤ rowMarginalKL (n + 1))
    (hstar_ne : ∀ x y, gammaStar x y ≠ 0)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0))
    (hN : N ≠ 0) :
    rowMarginalKL N ≤ finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  exact
    (IsChewi118FiniteSinkhornEntropyCertificate.of_initialCouplingKL
      (gamma := gamma) (gammaStar := gammaStar) (rowMarginalKL := rowMarginalKL)
      (N := N) hterminal_nonneg hone_step hmono hstar_ne hgamma0_ne hmass0).last_rowMarginalKL_le hN

/--
Chewi Theorem 11.8 finite-array selected endpoint.  The entropy recurrence
alone selects one iterate among `1, ..., N` with the displayed
`KL(gammaStar || gamma^0) / N` row-marginal KL bound.
-/
theorem chewi118_finiteSinkhorn_exists_rowMarginalKL_le_of_entropyRecurrence_initialKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {rowMarginalKL : ℕ -> ℝ} {N : ℕ}
    (hterminal_nonneg : 0 ≤ finiteCouplingEntropyBregman gammaStar (gamma N))
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          rowMarginalKL (n + 1))
    (hstar_ne : ∀ x y, gammaStar x y ≠ 0)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0))
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      rowMarginalKL (n + 1) ≤
        finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  have hmain :=
    chewi118_exists_gap_le_of_recurrence
      (D := fun n => finiteCouplingEntropyBregman gammaStar (gamma n))
      (gap := rowMarginalKL) hN hterminal_nonneg hone_step
  have hinit :
      finiteCouplingEntropyBregman gammaStar (gamma 0) =
        finiteCouplingKL gammaStar (gamma 0) :=
    finiteCouplingEntropyBregman_eq_finiteCouplingKL
      gammaStar (gamma 0) hstar_ne hgamma0_ne hmass0
  simpa [hinit] using hmain

/--
Build the finite Sinkhorn entropy certificate with the source initial
coupling-KL value, deriving terminal nonnegativity from positivity and equal
mass of the optimal and terminal couplings.
-/
theorem IsChewi118FiniteSinkhornEntropyCertificate.of_initialCouplingKL_and_terminal_pos
    {X Y : Type*} [Fintype X] [Fintype Y]
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {rowMarginalKL : ℕ -> ℝ} {N : ℕ}
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          rowMarginalKL (n + 1))
    (hmono : ∀ n, n < N ->
      rowMarginalKL N ≤ rowMarginalKL (n + 1))
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgammaN_pos : ∀ x y, 0 < gamma N x y)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmassN : finiteCouplingMass gammaStar = finiteCouplingMass (gamma N))
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0)) :
    IsChewi118FiniteSinkhornEntropyCertificate
      gamma gammaStar rowMarginalKL (finiteCouplingKL gammaStar (gamma 0)) N :=
  IsChewi118FiniteSinkhornEntropyCertificate.of_initialCouplingKL
    (gamma := gamma) (gammaStar := gammaStar) (rowMarginalKL := rowMarginalKL)
    (N := N)
    (finiteCouplingEntropyBregman_nonneg_of_pos_of_mass_eq
      gammaStar (gamma N) hstar_pos hgammaN_pos hmassN)
    hone_step hmono (fun x y => (hstar_pos x y).ne') hgamma0_ne hmass0

/--
Chewi Theorem 11.8 finite-array endpoint with terminal Bregman nonnegativity
deduced from positive equal-mass finite couplings.
-/
theorem chewi118_finiteSinkhorn_last_rowMarginalKL_le_of_entropyRecurrence_pos_initialKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {rowMarginalKL : ℕ -> ℝ} {N : ℕ}
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          rowMarginalKL (n + 1))
    (hmono : ∀ n, n < N ->
      rowMarginalKL N ≤ rowMarginalKL (n + 1))
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgammaN_pos : ∀ x y, 0 < gamma N x y)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmassN : finiteCouplingMass gammaStar = finiteCouplingMass (gamma N))
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0))
    (hN : N ≠ 0) :
    rowMarginalKL N ≤ finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  exact
    (IsChewi118FiniteSinkhornEntropyCertificate.of_initialCouplingKL_and_terminal_pos
      (gamma := gamma) (gammaStar := gammaStar) (rowMarginalKL := rowMarginalKL)
      (N := N) hone_step hmono hstar_pos hgammaN_pos hgamma0_ne hmassN hmass0).last_rowMarginalKL_le hN

/--
Chewi Theorem 11.8 finite-array selected endpoint with terminal Bregman
nonnegativity deduced from positive equal-mass finite couplings.
-/
theorem chewi118_finiteSinkhorn_exists_rowMarginalKL_le_of_entropyRecurrence_pos_initialKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {rowMarginalKL : ℕ -> ℝ} {N : ℕ}
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          rowMarginalKL (n + 1))
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgammaN_pos : ∀ x y, 0 < gamma N x y)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmassN : finiteCouplingMass gammaStar = finiteCouplingMass (gamma N))
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0))
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      rowMarginalKL (n + 1) ≤
        finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  exact
    chewi118_finiteSinkhorn_exists_rowMarginalKL_le_of_entropyRecurrence_initialKL
      (gamma := gamma) (gammaStar := gammaStar) (rowMarginalKL := rowMarginalKL)
      (N := N)
      (finiteCouplingEntropyBregman_nonneg_of_pos_of_mass_eq
        gammaStar (gamma N) hstar_pos hgammaN_pos hmassN)
      hone_step (fun x y => (hstar_pos x y).ne') hgamma0_ne hmass0 hN

/--
Chewi Theorem 11.8 finite-array endpoint with the displayed objective
specialized to the terminal row-marginal KL `KL(rowMarginal gamma^N || μ)`.
-/
theorem chewi118_finiteSinkhorn_last_rowMarginal_finiteKL_le_of_entropyRecurrence_pos_initialKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          finiteKL (rowMarginal (gamma (n + 1))) μ)
    (hmono : ∀ n, n < N ->
      finiteKL (rowMarginal (gamma N)) μ ≤
        finiteKL (rowMarginal (gamma (n + 1))) μ)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgammaN_pos : ∀ x y, 0 < gamma N x y)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmassN : finiteCouplingMass gammaStar = finiteCouplingMass (gamma N))
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0))
    (hN : N ≠ 0) :
    finiteKL (rowMarginal (gamma N)) μ ≤
      finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  exact
    chewi118_finiteSinkhorn_last_rowMarginalKL_le_of_entropyRecurrence_pos_initialKL
      (gamma := gamma) (gammaStar := gammaStar)
      (rowMarginalKL := fun n => finiteKL (rowMarginal (gamma n)) μ)
      (N := N) hone_step hmono hstar_pos hgammaN_pos hgamma0_ne hmassN hmass0 hN

/--
Chewi Theorem 11.8 finite-array endpoint stated with the source row-marginal
objective `sinkhornRowObjective μ gamma`.
-/
theorem chewi118_finiteSinkhorn_last_sinkhornRowObjective_le_of_entropyRecurrence_pos_initialKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          sinkhornRowObjective μ (gamma (n + 1)))
    (hmono : ∀ n, n < N ->
      sinkhornRowObjective μ (gamma N) ≤
        sinkhornRowObjective μ (gamma (n + 1)))
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgammaN_pos : ∀ x y, 0 < gamma N x y)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmassN : finiteCouplingMass gammaStar = finiteCouplingMass (gamma N))
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0))
    (hN : N ≠ 0) :
    sinkhornRowObjective μ (gamma N) ≤
      finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  simpa [sinkhornRowObjective] using
    chewi118_finiteSinkhorn_last_rowMarginal_finiteKL_le_of_entropyRecurrence_pos_initialKL
      (μ := μ) (gamma := gamma) (gammaStar := gammaStar) (N := N)
      (by
        intro n hn
        simpa [sinkhornRowObjective] using hone_step n hn)
      (by
        intro n hn
        simpa [sinkhornRowObjective] using hmono n hn)
      hstar_pos hgammaN_pos hgamma0_ne hmassN hmass0 hN

/--
Chewi Theorem 11.8 finite-array selected endpoint stated with the source
row-marginal objective `sinkhornRowObjective μ gamma`.
-/
theorem chewi118_finiteSinkhorn_exists_sinkhornRowObjective_le_of_entropyRecurrence_pos_initialKL
    {X Y : Type*} [Fintype X] [Fintype Y]
    (μ : X -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hone_step : ∀ n, n < N ->
      finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
        finiteCouplingEntropyBregman gammaStar (gamma n) -
          sinkhornRowObjective μ (gamma (n + 1)))
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgammaN_pos : ∀ x y, 0 < gamma N x y)
    (hgamma0_ne : ∀ x y, gamma 0 x y ≠ 0)
    (hmassN : finiteCouplingMass gammaStar = finiteCouplingMass (gamma N))
    (hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0))
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      sinkhornRowObjective μ (gamma (n + 1)) ≤
        finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) :=
  chewi118_finiteSinkhorn_exists_rowMarginalKL_le_of_entropyRecurrence_pos_initialKL
    (gamma := gamma) (gammaStar := gammaStar)
    (rowMarginalKL := fun n => sinkhornRowObjective μ (gamma n))
    (N := N) hone_step hstar_pos hgammaN_pos hgamma0_ne hmassN hmass0 hN

/--
Concrete finite Sinkhorn Theorem 11.8 endpoint for a row-then-column
normalization trajectory.  The actual normalization equation supplies the
zero-error entropy recurrence; the only remaining source-side rate hypothesis
is monotonicity of the displayed row objective along the selected iterates.
-/
theorem chewi118_finiteSinkhorn_last_sinkhornRowObjective_le_of_concreteSinkhornNormalizations
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgamma_pos : ∀ n, n ≤ N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x)
    (hmono : ∀ n, n < N ->
      sinkhornRowObjective μ (gamma N) ≤
        sinkhornRowObjective μ (gamma (n + 1)))
    (hN : N ≠ 0) :
    sinkhornRowObjective μ (gamma N) ≤
      finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  classical
  have hN_pos : 0 < N := Nat.pos_of_ne_zero hN
  have hone_step :
      ∀ n, n < N ->
        finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
          finiteCouplingEntropyBregman gammaStar (gamma n) -
            sinkhornRowObjective μ (gamma (n + 1)) :=
    chewi118_entropy_one_step_trajectory_of_concreteSinkhornNormalizations
      μ ν gamma gammaStar hstep hstar_row hstar_col hμ_pos hν_pos
      (fun n hn => hgamma_pos n (le_of_lt hn)) hgamma_mass htarget_mass
  have hstar_col_eq : ∀ y, columnMarginal gammaStar y = ν y := by
    simpa [finiteColumnMarginalConstraint] using hstar_col
  have hstar_mass :
      finiteCouplingMass gammaStar = ∑ y, ν y := by
    rw [← sum_columnMarginal_eq_finiteCouplingMass gammaStar]
    exact Finset.sum_congr rfl fun y _hy => hstar_col_eq y
  let m : ℕ := N - 1
  have hm_lt : m < N := by
    dsimp [m]
    exact Nat.sub_one_lt hN
  have hm_le : m ≤ N := le_of_lt hm_lt
  have hm_succ : m + 1 = N := by
    dsimp [m]
    omega
  have hm_pos : ∀ x y, 0 < gamma m x y :=
    hgamma_pos m hm_le
  have hm_row_pos : ∀ x, 0 < rowMarginal (gamma m) x :=
    rowMarginal_pos_of_pos hm_pos
  have hhalf_pos :
      ∀ x y, 0 < rowNormalizedCoupling μ (gamma m) x y :=
    rowNormalizedCoupling_pos_of_pos μ (gamma m) hμ_pos hm_pos hm_row_pos
  have hhalf_col_pos :
      ∀ y, 0 < columnMarginal (rowNormalizedCoupling μ (gamma m)) y :=
    columnMarginal_pos_of_pos hhalf_pos
  have hgammaN_col : ∀ y, columnMarginal (gamma N) y = ν y := by
    intro y
    have hstep_m := hstep m hm_lt
    rw [← hm_succ, hstep_m]
    exact columnMarginal_columnNormalizedCoupling ν
      (rowNormalizedCoupling μ (gamma m))
      (fun y => (hhalf_col_pos y).ne') y
  have hgammaN_mass :
      finiteCouplingMass (gamma N) = ∑ y, ν y := by
    rw [← sum_columnMarginal_eq_finiteCouplingMass (gamma N)]
    exact Finset.sum_congr rfl fun y _hy => hgammaN_col y
  have hmassN : finiteCouplingMass gammaStar = finiteCouplingMass (gamma N) := by
    rw [hstar_mass, hgammaN_mass]
  have hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0) := by
    rw [hstar_mass, htarget_mass, hgamma_mass 0 hN_pos]
  exact
    chewi118_finiteSinkhorn_last_sinkhornRowObjective_le_of_entropyRecurrence_pos_initialKL
      (μ := μ) (gamma := gamma) (gammaStar := gammaStar) (N := N)
      hone_step hmono hstar_pos (hgamma_pos N le_rfl)
      (fun x y => (hgamma_pos 0 (Nat.zero_le N) x y).ne') hmassN hmass0 hN

/--
Concrete finite Sinkhorn selected endpoint for a row-then-column
normalization trajectory.  Unlike the last-iterate endpoint, this selected
rate needs no monotonicity assumption on the row objective.
-/
theorem chewi118_finiteSinkhorn_exists_sinkhornRowObjective_le_of_concreteSinkhornNormalizations
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgamma_pos : ∀ n, n ≤ N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x)
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      sinkhornRowObjective μ (gamma (n + 1)) ≤
        finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  classical
  have hN_pos : 0 < N := Nat.pos_of_ne_zero hN
  have hone_step :
      ∀ n, n < N ->
        finiteCouplingEntropyBregman gammaStar (gamma (n + 1)) ≤
          finiteCouplingEntropyBregman gammaStar (gamma n) -
            sinkhornRowObjective μ (gamma (n + 1)) :=
    chewi118_entropy_one_step_trajectory_of_concreteSinkhornNormalizations
      μ ν gamma gammaStar hstep hstar_row hstar_col hμ_pos hν_pos
      (fun n hn => hgamma_pos n (le_of_lt hn)) hgamma_mass htarget_mass
  have hstar_col_eq : ∀ y, columnMarginal gammaStar y = ν y := by
    simpa [finiteColumnMarginalConstraint] using hstar_col
  have hstar_mass :
      finiteCouplingMass gammaStar = ∑ y, ν y := by
    rw [← sum_columnMarginal_eq_finiteCouplingMass gammaStar]
    exact Finset.sum_congr rfl fun y _hy => hstar_col_eq y
  let m : ℕ := N - 1
  have hm_lt : m < N := by
    dsimp [m]
    exact Nat.sub_one_lt hN
  have hm_le : m ≤ N := le_of_lt hm_lt
  have hm_succ : m + 1 = N := by
    dsimp [m]
    omega
  have hm_pos : ∀ x y, 0 < gamma m x y :=
    hgamma_pos m hm_le
  have hm_row_pos : ∀ x, 0 < rowMarginal (gamma m) x :=
    rowMarginal_pos_of_pos hm_pos
  have hhalf_pos :
      ∀ x y, 0 < rowNormalizedCoupling μ (gamma m) x y :=
    rowNormalizedCoupling_pos_of_pos μ (gamma m) hμ_pos hm_pos hm_row_pos
  have hhalf_col_pos :
      ∀ y, 0 < columnMarginal (rowNormalizedCoupling μ (gamma m)) y :=
    columnMarginal_pos_of_pos hhalf_pos
  have hgammaN_col : ∀ y, columnMarginal (gamma N) y = ν y := by
    intro y
    have hstep_m := hstep m hm_lt
    rw [← hm_succ, hstep_m]
    exact columnMarginal_columnNormalizedCoupling ν
      (rowNormalizedCoupling μ (gamma m))
      (fun y => (hhalf_col_pos y).ne') y
  have hgammaN_mass :
      finiteCouplingMass (gamma N) = ∑ y, ν y := by
    rw [← sum_columnMarginal_eq_finiteCouplingMass (gamma N)]
    exact Finset.sum_congr rfl fun y _hy => hgammaN_col y
  have hmassN : finiteCouplingMass gammaStar = finiteCouplingMass (gamma N) := by
    rw [hstar_mass, hgammaN_mass]
  have hmass0 : finiteCouplingMass gammaStar = finiteCouplingMass (gamma 0) := by
    rw [hstar_mass, htarget_mass, hgamma_mass 0 hN_pos]
  exact
    chewi118_finiteSinkhorn_exists_sinkhornRowObjective_le_of_entropyRecurrence_pos_initialKL
      (μ := μ) (gamma := gamma) (gammaStar := gammaStar) (N := N)
      hone_step hstar_pos (hgamma_pos N le_rfl)
      (fun x y => (hgamma_pos 0 (Nat.zero_le N) x y).ne') hmassN hmass0 hN

/--
Scalar monotonicity adapter for Chewi Theorem 11.8: if the displayed
row-objective sequence is antitone, then the terminal objective is below every
earlier selected objective used by the entropy recurrence.
-/
theorem chewi118_last_le_of_antitone
    {a : ℕ -> ℝ} {N : ℕ} (ha : Antitone a) :
    ∀ n, n < N -> a N ≤ a (n + 1) := by
  intro n hn
  exact ha (Nat.succ_le_of_lt hn)

/--
Concrete finite Sinkhorn Theorem 11.8 endpoint with the monotonicity field
supplied as an antitone row-objective sequence.
-/
theorem chewi118_finiteSinkhorn_last_sinkhornRowObjective_le_of_concreteSinkhornNormalizations_antitone
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgamma_pos : ∀ n, n ≤ N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x)
    (hobjective_antitone :
      Antitone fun n => sinkhornRowObjective μ (gamma n))
    (hN : N ≠ 0) :
    sinkhornRowObjective μ (gamma N) ≤
      finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) :=
  chewi118_finiteSinkhorn_last_sinkhornRowObjective_le_of_concreteSinkhornNormalizations
    μ ν hstep hstar_row hstar_col hμ_pos hν_pos hstar_pos hgamma_pos
    hgamma_mass htarget_mass
    (chewi118_last_le_of_antitone hobjective_antitone) hN

/--
Concrete finite Sinkhorn Theorem 11.8 endpoint with the monotonicity field
supplied by adjacent nonincrease of the displayed row objective.
-/
theorem chewi118_finiteSinkhorn_last_sinkhornRowObjective_le_of_concreteSinkhornNormalizations_succ_le
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgamma_pos : ∀ n, n ≤ N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x)
    (hobjective_succ_le : ∀ n,
      sinkhornRowObjective μ (gamma (n + 1)) ≤
        sinkhornRowObjective μ (gamma n))
    (hN : N ≠ 0) :
    sinkhornRowObjective μ (gamma N) ≤
      finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) :=
  chewi118_finiteSinkhorn_last_sinkhornRowObjective_le_of_concreteSinkhornNormalizations_antitone
    μ ν hstep hstar_row hstar_col hμ_pos hν_pos hstar_pos hgamma_pos
    hgamma_mass htarget_mass
    (antitone_nat_of_succ_le hobjective_succ_le) hN

/--
Concrete finite Sinkhorn Theorem 11.8 endpoint in the literal displayed KL
form `KL(rowMarginal gamma^N || mu) <= KL(gammaStar || gamma^0) / N`.
-/
theorem chewi118_finiteSinkhorn_last_rowMarginal_finiteKL_le_of_concreteSinkhornNormalizations
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgamma_pos : ∀ n, n ≤ N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x)
    (hmono : ∀ n, n < N ->
      finiteKL (rowMarginal (gamma N)) μ ≤
        finiteKL (rowMarginal (gamma (n + 1))) μ)
    (hN : N ≠ 0) :
    finiteKL (rowMarginal (gamma N)) μ ≤
      finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  simpa [sinkhornRowObjective] using
    chewi118_finiteSinkhorn_last_sinkhornRowObjective_le_of_concreteSinkhornNormalizations
      μ ν hstep hstar_row hstar_col hμ_pos hν_pos hstar_pos hgamma_pos
      hgamma_mass htarget_mass
      (by
        intro n hn
        simpa [sinkhornRowObjective] using hmono n hn)
      hN

/--
Concrete finite Sinkhorn selected endpoint in literal row-marginal KL form.
This version needs no monotonicity of the displayed KL objective.
-/
theorem chewi118_finiteSinkhorn_exists_rowMarginal_finiteKL_le_of_concreteSinkhornNormalizations
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgamma_pos : ∀ n, n ≤ N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x)
    (hN : N ≠ 0) :
    ∃ n, n < N ∧
      finiteKL (rowMarginal (gamma (n + 1))) μ ≤
        finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  rcases
    chewi118_finiteSinkhorn_exists_sinkhornRowObjective_le_of_concreteSinkhornNormalizations
      μ ν hstep hstar_row hstar_col hμ_pos hν_pos hstar_pos hgamma_pos
      hgamma_mass htarget_mass hN with
    ⟨n, hn, hle⟩
  exact ⟨n, hn, by simpa [sinkhornRowObjective] using hle⟩

/--
Concrete finite Sinkhorn last-iterate KL endpoint with monotonicity supplied as
an antitone literal row-marginal KL sequence.
-/
theorem chewi118_finiteSinkhorn_last_rowMarginal_finiteKL_le_of_concreteSinkhornNormalizations_antitone
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgamma_pos : ∀ n, n ≤ N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x)
    (hobjective_antitone :
      Antitone fun n => finiteKL (rowMarginal (gamma n)) μ)
    (hN : N ≠ 0) :
    finiteKL (rowMarginal (gamma N)) μ ≤
      finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) := by
  exact
    chewi118_finiteSinkhorn_last_rowMarginal_finiteKL_le_of_concreteSinkhornNormalizations
      μ ν hstep hstar_row hstar_col hμ_pos hν_pos hstar_pos hgamma_pos
      hgamma_mass htarget_mass
      (chewi118_last_le_of_antitone hobjective_antitone) hN

/--
Concrete finite Sinkhorn last-iterate KL endpoint with monotonicity supplied by
adjacent nonincrease of the literal row-marginal KL sequence.
-/
theorem chewi118_finiteSinkhorn_last_rowMarginal_finiteKL_le_of_concreteSinkhornNormalizations_succ_le
    {X Y : Type*} [Fintype X] [Fintype Y] [Nonempty X] [Nonempty Y]
    (μ : X -> ℝ) (ν : Y -> ℝ)
    {gamma : ℕ -> X -> Y -> ℝ} {gammaStar : X -> Y -> ℝ}
    {N : ℕ}
    (hstep : ∀ n, n < N ->
      gamma (n + 1) = columnNormalizedCoupling ν
        (rowNormalizedCoupling μ (gamma n)))
    (hstar_row : gammaStar ∈ finiteRowMarginalConstraint μ)
    (hstar_col : gammaStar ∈ finiteColumnMarginalConstraint ν)
    (hμ_pos : ∀ x, 0 < μ x)
    (hν_pos : ∀ y, 0 < ν y)
    (hstar_pos : ∀ x y, 0 < gammaStar x y)
    (hgamma_pos : ∀ n, n ≤ N -> ∀ x y, 0 < gamma n x y)
    (hgamma_mass : ∀ n, n < N -> (∑ x, μ x) = finiteCouplingMass (gamma n))
    (htarget_mass : (∑ y, ν y) = ∑ x, μ x)
    (hobjective_succ_le : ∀ n,
      finiteKL (rowMarginal (gamma (n + 1))) μ ≤
        finiteKL (rowMarginal (gamma n)) μ)
    (hN : N ≠ 0) :
    finiteKL (rowMarginal (gamma N)) μ ≤
      finiteCouplingKL gammaStar (gamma 0) / (N : ℝ) :=
  chewi118_finiteSinkhorn_last_rowMarginal_finiteKL_le_of_concreteSinkhornNormalizations_antitone
    μ ν hstep hstar_row hstar_col hμ_pos hν_pos hstar_pos hgamma_pos
    hgamma_mass htarget_mass
    (antitone_nat_of_succ_le hobjective_succ_le) hN

/--
Source-shaped certificate for Chewi Theorem 11.8 after interpreting Sinkhorn
as mirror descent.  The concrete finite Sinkhorn/KL work is isolated in these
fields: the zero-error Bregman recurrence, monotonicity of the marginal KL
gaps, nonnegativity of the terminal divergence, and identification of the
initial Bregman divergence with `KL(gammaStar || gamma^0)`.
-/
structure IsChewi118SinkhornMirrorDescentCertificate
    (phi : E -> ℝ) (gradPhi : E -> E) (gamma : ℕ -> E) (gammaStar : E)
    (rowMarginalKL : ℕ -> ℝ) (initialCouplingKL : ℝ) (N : ℕ) : Prop where
  terminal_nonneg : 0 ≤ bregmanDivergence phi gradPhi gammaStar (gamma N)
  one_step : ∀ n, n < N ->
    bregmanDivergence phi gradPhi gammaStar (gamma (n + 1)) ≤
      bregmanDivergence phi gradPhi gammaStar (gamma n) -
        rowMarginalKL (n + 1)
  monotone_to_last : ∀ n, n < N ->
    rowMarginalKL N ≤ rowMarginalKL (n + 1)
  initial_eq : bregmanDivergence phi gradPhi gammaStar (gamma 0) =
    initialCouplingKL

/--
Chewi Theorem 11.8, supplied-interface Sinkhorn/mirror-descent form:
once the finite row-normalization identities supply the certificate, the last
`X`-marginal KL obeys the displayed `KL(gammaStar || gamma^0) / N` rate.
-/
theorem IsChewi118SinkhornMirrorDescentCertificate.last_rowMarginalKL_le
    {phi : E -> ℝ} {gradPhi : E -> E} {gamma : ℕ -> E} {gammaStar : E}
    {rowMarginalKL : ℕ -> ℝ} {initialCouplingKL : ℝ} {N : ℕ}
    (hcert : IsChewi118SinkhornMirrorDescentCertificate
      phi gradPhi gamma gammaStar rowMarginalKL initialCouplingKL N)
    (hN : N ≠ 0) :
    rowMarginalKL N ≤ initialCouplingKL / (N : ℝ) := by
  have hmain :=
    chewi118_last_gap_le_of_recurrence
      (D := fun n => bregmanDivergence phi gradPhi gammaStar (gamma n))
      (gap := rowMarginalKL) hN
      hcert.terminal_nonneg hcert.one_step hcert.monotone_to_last
  simpa [hcert.initial_eq] using hmain

/--
Chewi Theorem 11.8, theorem-facing wrapper.  This is the source-shaped endpoint
to instantiate for Sinkhorn after the finite KL row/column normalization
identities are proved.
-/
theorem chewi118_sinkhorn_last_rowMarginalKL_le_of_mirrorDescent
    {phi : E -> ℝ} {gradPhi : E -> E} {gamma : ℕ -> E} {gammaStar : E}
    {rowMarginalKL : ℕ -> ℝ} {initialCouplingKL : ℝ} {N : ℕ}
    (hcert : IsChewi118SinkhornMirrorDescentCertificate
      phi gradPhi gamma gammaStar rowMarginalKL initialCouplingKL N)
    (hN : N ≠ 0) :
    rowMarginalKL N ≤ initialCouplingKL / (N : ℝ) :=
  hcert.last_rowMarginalKL_le hN

end Optimization
end StatInference
