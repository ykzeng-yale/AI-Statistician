import Mathlib.Analysis.Matrix.Order
import Mathlib.Analysis.CStarAlgebra.Matrix
import Mathlib.Analysis.CStarAlgebra.ContinuousFunctionalCalculus.Order
import Mathlib.LinearAlgebra.Matrix.Charpoly.Basic
import StatInference.Optimization.Basic

/-!
# Chewi Optimization 2026, Appendix A Matrix Order

This module records source-facing wrappers for the matrix background in
Appendix A of Chewi's optimization notes.  The first layer packages Definition
A.4's Loewner/PSD order display using mathlib's `MatrixOrder` instance.
-/

open Matrix
open Polynomial
open scoped MatrixOrder Matrix.Norms.L2Operator

namespace StatInference
namespace Optimization

variable {n : Type*} [Fintype n]

/--
Chewi Theorem A.1, source-facing spectral theorem wrapper.  A Hermitian real
matrix is unitarily diagonalized by its mathlib eigenvector unitary, with
diagonal entries the real eigenvalues.
-/
theorem chewiA1_spectral_theorem
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) :
    A =
      Unitary.conjStarAlgAut ℝ _ hA.eigenvectorUnitary
        (diagonal (RCLike.ofReal ∘ hA.eigenvalues)) := by
  exact hA.spectral_theorem

/--
Chewi Theorem A.1, eigenvector display.  The source eigenvector basis satisfies
`A u_i = lambda_i u_i`.
-/
theorem chewiA1_mulVec_eigenvectorBasis
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) (i : n) :
    A *ᵥ ⇑(hA.eigenvectorBasis i) =
      (hA.eigenvalues i) • ⇑(hA.eigenvectorBasis i) := by
  exact hA.mulVec_eigenvectorBasis i

/--
Chewi Definition A.2, PSD eigenvalue characterization.
-/
theorem chewiA2_posSemidef_iff_eigenvalues_nonneg
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) :
    A.PosSemidef ↔ ∀ i, 0 ≤ hA.eigenvalues i := by
  simpa [Pi.le_def] using hA.posSemidef_iff_eigenvalues_nonneg

/--
Chewi Definition A.2, PD eigenvalue characterization.
-/
theorem chewiA2_posDef_iff_eigenvalues_pos
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) :
    A.PosDef ↔ ∀ i, 0 < hA.eigenvalues i := by
  exact hA.posDef_iff_eigenvalues_pos

/--
Chewi Lemma A.3, upper eigenvalue bound in Loewner-order form.  For a
Hermitian real matrix, `A <= beta I` is equivalent to every eigenvalue of `A`
being at most `beta`.
-/
theorem chewiA3_le_scalar_one_iff_eigenvalues_le
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {beta : ℝ} :
    A ≤ beta • (1 : Matrix n n ℝ) ↔ ∀ i, hA.eigenvalues i ≤ beta := by
  have hsa : IsSelfAdjoint A := hA.isSelfAdjoint
  rw [show beta • (1 : Matrix n n ℝ) =
      algebraMap ℝ (Matrix n n ℝ) beta by
    simp [Algebra.algebraMap_eq_smul_one]]
  rw [le_algebraMap_iff_spectrum_le (a := A) (r := beta) (ha := hsa)]
  constructor
  · intro h i
    exact h (hA.eigenvalues i)
      (by simp [hA.spectrum_real_eq_range_eigenvalues])
  · intro h x hx
    rw [hA.spectrum_real_eq_range_eigenvalues] at hx
    rcases hx with ⟨i, rfl⟩
    exact h i

/--
Chewi Lemma A.3, lower eigenvalue bound in Loewner-order form.  For a
Hermitian real matrix, `alpha I <= A` is equivalent to every eigenvalue of `A`
being at least `alpha`.
-/
theorem chewiA3_scalar_one_le_iff_le_eigenvalues
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {alpha : ℝ} :
    alpha • (1 : Matrix n n ℝ) ≤ A ↔ ∀ i, alpha ≤ hA.eigenvalues i := by
  have hsa : IsSelfAdjoint A := hA.isSelfAdjoint
  rw [show alpha • (1 : Matrix n n ℝ) =
      algebraMap ℝ (Matrix n n ℝ) alpha by
    simp [Algebra.algebraMap_eq_smul_one]]
  rw [algebraMap_le_iff_le_spectrum (a := A) (r := alpha) (ha := hsa)]
  constructor
  · intro h i
    exact h (hA.eigenvalues i)
      (by simp [hA.spectrum_real_eq_range_eigenvalues])
  · intro h x hx
    rw [hA.spectrum_real_eq_range_eigenvalues] at hx
    rcases hx with ⟨i, rfl⟩
    exact h i

/--
Chewi Lemma A.3, eigenvalue interval in scalar Loewner-order form.
-/
theorem chewiA3_scalar_bounds_iff_eigenvalues_mem_Icc
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {alpha beta : ℝ} :
    (alpha • (1 : Matrix n n ℝ) ≤ A ∧
        A ≤ beta • (1 : Matrix n n ℝ)) ↔
      ∀ i, alpha ≤ hA.eigenvalues i ∧ hA.eigenvalues i ≤ beta := by
  rw [chewiA3_scalar_one_le_iff_le_eigenvalues hA,
    chewiA3_le_scalar_one_iff_eigenvalues_le hA]
  constructor
  · intro h i
    exact ⟨h.1 i, h.2 i⟩
  · intro h
    exact ⟨fun i => (h i).1, fun i => (h i).2⟩

/--
Chewi Definition A.4, Loewner order as a quadratic-form inequality.  Mathlib's
`MatrixOrder` uses `B <= A` to mean `(A - B).PosSemidef`; under the source
hypothesis that `A` and `B` are symmetric/Hermitian, this is equivalent to
`vᵀ B v <= vᵀ A v` for every vector `v`.
-/
theorem chewiA4_loewnerOrder_iff_quadraticForm_le
    {A B : Matrix n n ℝ} (hA : A.IsHermitian) (hB : B.IsHermitian) :
    B ≤ A ↔
      ∀ v : n -> ℝ, dotProduct v (B *ᵥ v) ≤ dotProduct v (A *ᵥ v) := by
  constructor
  · intro hle v
    have hpsd : (A - B).PosSemidef := Matrix.le_iff.mp hle
    have hnonneg :
        0 ≤ star v ⬝ᵥ ((A - B) *ᵥ v) :=
      hpsd.dotProduct_mulVec_nonneg v
    have hdiff :
        star v ⬝ᵥ ((A - B) *ᵥ v) =
          dotProduct v (A *ᵥ v) - dotProduct v (B *ᵥ v) := by
      simp [Matrix.sub_mulVec, dotProduct_sub]
    have hsub_nonneg :
        0 ≤ dotProduct v (A *ᵥ v) - dotProduct v (B *ᵥ v) := by
      rwa [hdiff] at hnonneg
    linarith
  · intro hquad
    rw [Matrix.le_iff]
    refine Matrix.PosSemidef.of_dotProduct_mulVec_nonneg (hA.sub hB) ?_
    intro v
    have hsub_nonneg :
        0 ≤ dotProduct v (A *ᵥ v) - dotProduct v (B *ᵥ v) := by
      exact sub_nonneg.mpr (hquad v)
    have hdiff :
        star v ⬝ᵥ ((A - B) *ᵥ v) =
          dotProduct v (A *ᵥ v) - dotProduct v (B *ᵥ v) := by
      simp [Matrix.sub_mulVec, dotProduct_sub]
    rwa [hdiff]

/--
Chewi Definition A.4, strict Loewner-order quadratic-form direction.  If
`A - B` is positive definite, every nonzero vector has strictly larger
quadratic form under `A` than under `B`.
-/
theorem chewiA4_quadraticForm_lt_of_posDef_sub
    {A B : Matrix n n ℝ} (hAB : (A - B).PosDef) :
    ∀ v : n -> ℝ, v ≠ 0 ->
      dotProduct v (B *ᵥ v) < dotProduct v (A *ᵥ v) := by
  intro v hv
  have hpos :
      0 < star v ⬝ᵥ ((A - B) *ᵥ v) :=
    hAB.dotProduct_mulVec_pos hv
  have hdiff :
      star v ⬝ᵥ ((A - B) *ᵥ v) =
        dotProduct v (A *ᵥ v) - dotProduct v (B *ᵥ v) := by
    simp [Matrix.sub_mulVec, dotProduct_sub]
  have hsub_pos :
      0 < dotProduct v (A *ᵥ v) - dotProduct v (B *ᵥ v) := by
    rwa [hdiff] at hpos
  linarith

/--
Chewi Lemma A.3, source quadratic-form statement.  A Hermitian real matrix has
all eigenvalues in `[alpha, beta]` iff every quadratic form lies between the
corresponding scalar multiples of `||v||^2`.
-/
theorem chewiA3_eigenvalues_mem_Icc_iff_quadraticForm_between
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {alpha beta : ℝ} :
    (∀ i, alpha ≤ hA.eigenvalues i ∧ hA.eigenvalues i ≤ beta) ↔
      ∀ v : n -> ℝ,
        alpha * dotProduct v v ≤ dotProduct v (A *ᵥ v) ∧
          dotProduct v (A *ᵥ v) ≤ beta * dotProduct v v := by
  rw [← chewiA3_scalar_bounds_iff_eigenvalues_mem_Icc hA]
  have halpha : (alpha • (1 : Matrix n n ℝ)).IsHermitian := by
    exact Matrix.isHermitian_one.smul
      (show IsSelfAdjoint (alpha : ℝ) by
        simp [isSelfAdjoint_iff])
  have hbeta : (beta • (1 : Matrix n n ℝ)).IsHermitian := by
    exact Matrix.isHermitian_one.smul
      (show IsSelfAdjoint (beta : ℝ) by
        simp [isSelfAdjoint_iff])
  constructor
  · intro hsandwich v
    have hlower_raw :=
      (chewiA4_loewnerOrder_iff_quadraticForm_le hA halpha).mp
        hsandwich.1 v
    have hupper_raw :=
      (chewiA4_loewnerOrder_iff_quadraticForm_le hbeta hA).mp
        hsandwich.2 v
    constructor
    · have hscalar :
          dotProduct v ((alpha • (1 : Matrix n n ℝ)) *ᵥ v) =
            alpha * dotProduct v v := by
        simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
          smul_eq_mul]
      simpa [hscalar] using hlower_raw
    · have hscalar :
          dotProduct v ((beta • (1 : Matrix n n ℝ)) *ᵥ v) =
            beta * dotProduct v v := by
        simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
          smul_eq_mul]
      simpa [hscalar] using hupper_raw
  · intro hquad
    constructor
    · rw [chewiA4_loewnerOrder_iff_quadraticForm_le hA halpha]
      intro v
      have hscalar :
          dotProduct v ((alpha • (1 : Matrix n n ℝ)) *ᵥ v) =
            alpha * dotProduct v v := by
        simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
          smul_eq_mul]
      simpa [hscalar] using (hquad v).1
    · rw [chewiA4_loewnerOrder_iff_quadraticForm_le hbeta hA]
      intro v
      have hscalar :
          dotProduct v ((beta • (1 : Matrix n n ℝ)) *ᵥ v) =
            beta * dotProduct v v := by
        simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
          smul_eq_mul]
      simpa [hscalar] using (hquad v).2

variable {m : Type*} [Fintype m]

/--
Chewi Definition A.5 setup: the symmetric matrix `Aᵀ A` associated to a
rectangular real matrix is positive semidefinite.  This is the PSD half of the
operator-norm discussion following Definition A.5.
-/
theorem chewiA5_transpose_mul_self_posSemidef
    (A : Matrix m n ℝ) :
    (Aᵀ * A).PosSemidef := by
  simpa using Matrix.posSemidef_conjTranspose_mul_self A

/--
Chewi Definition A.5 setup: the squared norm of `A v` is the quadratic form of
`Aᵀ A` at `v`.
-/
theorem chewiA5_dotProduct_mulVec_self_eq_transpose_mul_self_quadratic
    (A : Matrix m n ℝ) (v : n -> ℝ) :
    dotProduct (A *ᵥ v) (A *ᵥ v) =
      dotProduct v ((Aᵀ * A) *ᵥ v) := by
  symm
  rw [Matrix.dotProduct_mulVec]
  rw [← Matrix.vecMul_mulVec]
  rw [← Matrix.dotProduct_mulVec]

/--
Chewi Definition A.5, Loewner form of the squared operator-norm bound.  The
matrix inequality `Aᵀ A <= C^2 I` is exactly the coordinate-vector estimate
`||A v||^2 <= C^2 ||v||^2`, written here with mathlib's finite-vector
`dotProduct`.
-/
theorem chewiA5_transpose_mul_self_le_scalar_one_iff_dotProduct_bound
    [DecidableEq n] (A : Matrix m n ℝ) (C : ℝ) :
    (Aᵀ * A) ≤ (C ^ (2 : ℕ)) • (1 : Matrix n n ℝ) ↔
      ∀ v : n -> ℝ,
        dotProduct (A *ᵥ v) (A *ᵥ v) ≤
          C ^ (2 : ℕ) * dotProduct v v := by
  have hright :
      ((C ^ (2 : ℕ)) • (1 : Matrix n n ℝ)).IsHermitian := by
    exact Matrix.isHermitian_one.smul
      (show IsSelfAdjoint (C ^ (2 : ℕ) : ℝ) by
        simp [isSelfAdjoint_iff])
  have hleft : (Aᵀ * A).IsHermitian :=
    (chewiA5_transpose_mul_self_posSemidef A).isHermitian
  rw [chewiA4_loewnerOrder_iff_quadraticForm_le hright hleft]
  constructor
  · intro h v
    have hv := h v
    have hquad :
        dotProduct v ((Aᵀ * A) *ᵥ v) =
          dotProduct (A *ᵥ v) (A *ᵥ v) :=
      (chewiA5_dotProduct_mulVec_self_eq_transpose_mul_self_quadratic A v).symm
    have hscalar :
        dotProduct v (((C ^ (2 : ℕ)) • (1 : Matrix n n ℝ)) *ᵥ v) =
          C ^ (2 : ℕ) * dotProduct v v := by
      simp [Matrix.smul_mulVec]
    simpa [hquad, hscalar] using hv
  · intro h v
    have hv := h v
    have hquad :
        dotProduct (A *ᵥ v) (A *ᵥ v) =
          dotProduct v ((Aᵀ * A) *ᵥ v) :=
      chewiA5_dotProduct_mulVec_self_eq_transpose_mul_self_quadratic A v
    have hscalar :
        C ^ (2 : ℕ) * dotProduct v v =
          dotProduct v (((C ^ (2 : ℕ)) • (1 : Matrix n n ℝ)) *ᵥ v) := by
      simp [Matrix.smul_mulVec]
    simpa [hquad, hscalar] using hv

/--
Chewi Definition A.5, unit-vector form.  From `Aᵀ A <= C^2 I`, every unit
coordinate vector satisfies `||A v||^2 <= C^2`, written in dot-product form.
-/
theorem chewiA5_unit_dotProduct_mulVec_self_le_of_transpose_mul_self_le_scalar_one
    [DecidableEq n] {A : Matrix m n ℝ} {C : ℝ}
    (hA : (Aᵀ * A) ≤ (C ^ (2 : ℕ)) • (1 : Matrix n n ℝ)) :
    ∀ v : n -> ℝ, dotProduct v v = 1 ->
      dotProduct (A *ᵥ v) (A *ᵥ v) ≤ C ^ (2 : ℕ) := by
  intro v hv
  have hbound :=
    (chewiA5_transpose_mul_self_le_scalar_one_iff_dotProduct_bound A C).mp hA v
  simpa [hv] using hbound

/--
Chewi Definition A.5, operator-norm upper bound from the Loewner bound on
`Aᵀ A`.  Mathlib's `Matrix.Norms.L2Operator` norm is the Euclidean operator
norm, so this is the source implication `Aᵀ A <= C^2 I -> ||A||_op <= C`.
-/
theorem chewiA5_l2_opNorm_le_of_transpose_mul_self_le_scalar_one
    [DecidableEq n] {A : Matrix m n ℝ} {C : ℝ}
    (hC : 0 ≤ C)
    (hA : (Aᵀ * A) ≤ (C ^ (2 : ℕ)) • (1 : Matrix n n ℝ)) :
    ‖A‖ ≤ C := by
  rw [Matrix.l2_opNorm_def]
  let T : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ m :=
    (Matrix.toEuclideanLin (𝕜 := ℝ) (m := m) (n := n)).trans
      LinearMap.toContinuousLinearMap A
  change ‖T‖ ≤ C
  refine T.opNorm_le_bound hC ?_
  intro x
  have hbound :=
    (chewiA5_transpose_mul_self_le_scalar_one_iff_dotProduct_bound A C).mp hA x.ofLp
  have hTx_sq :
      ‖T x‖ ^ (2 : ℕ) = dotProduct (A *ᵥ x.ofLp) (A *ᵥ x.ofLp) := by
    rw [EuclideanSpace.real_norm_sq_eq]
    simp [T, Matrix.toLpLin_apply, dotProduct, pow_two]
  have hx_sq : ‖x‖ ^ (2 : ℕ) = dotProduct x.ofLp x.ofLp := by
    rw [EuclideanSpace.real_norm_sq_eq]
    simp [dotProduct, pow_two]
  have hsq :
      ‖T x‖ ^ (2 : ℕ) ≤ (C * ‖x‖) ^ (2 : ℕ) := by
    calc
      ‖T x‖ ^ (2 : ℕ)
          = dotProduct (A *ᵥ x.ofLp) (A *ᵥ x.ofLp) := hTx_sq
      _ ≤ C ^ (2 : ℕ) * dotProduct x.ofLp x.ofLp := hbound
      _ = (C * ‖x‖) ^ (2 : ℕ) := by
          rw [← hx_sq]
          ring
  exact (sq_le_sq₀ (norm_nonneg _) (mul_nonneg hC (norm_nonneg _))).mp hsq

/--
Chewi Definition A.5, full Loewner/operator-norm bridge for rectangular
matrices.  For `C >= 0`, the Euclidean operator-norm bound `||A||_op <= C` is
equivalent to the Loewner bound `Aᵀ A <= C^2 I`.
-/
theorem chewiA5_transpose_mul_self_le_scalar_one_iff_l2_opNorm_le
    [DecidableEq n] {A : Matrix m n ℝ} {C : ℝ} (hC : 0 ≤ C) :
    (Aᵀ * A) ≤ (C ^ (2 : ℕ)) • (1 : Matrix n n ℝ) ↔ ‖A‖ ≤ C := by
  constructor
  · intro hA
    exact chewiA5_l2_opNorm_le_of_transpose_mul_self_le_scalar_one hC hA
  · intro hnorm
    rw [chewiA5_transpose_mul_self_le_scalar_one_iff_dotProduct_bound A C]
    intro v
    let T : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ m :=
      (Matrix.toEuclideanLin (𝕜 := ℝ) (m := m) (n := n)).trans
        LinearMap.toContinuousLinearMap A
    let x : EuclideanSpace ℝ n := WithLp.toLp 2 v
    have hnorm_T : ‖T‖ ≤ C := by
      simpa [Matrix.l2_opNorm_def, T] using hnorm
    have hpoint : ‖T x‖ ≤ C * ‖x‖ := by
      calc
        ‖T x‖ ≤ ‖T‖ * ‖x‖ := T.le_opNorm x
        _ ≤ C * ‖x‖ := mul_le_mul_of_nonneg_right hnorm_T (norm_nonneg x)
    have hsq :
        ‖T x‖ ^ (2 : ℕ) ≤ (C * ‖x‖) ^ (2 : ℕ) :=
      sq_le_sq₀ (norm_nonneg _) (mul_nonneg hC (norm_nonneg _)) |>.mpr hpoint
    have hTx_sq :
        ‖T x‖ ^ (2 : ℕ) = dotProduct (A *ᵥ v) (A *ᵥ v) := by
      rw [EuclideanSpace.real_norm_sq_eq]
      simp [T, x, Matrix.toLpLin_apply, dotProduct, pow_two]
    have hx_sq : ‖x‖ ^ (2 : ℕ) = dotProduct v v := by
      rw [EuclideanSpace.real_norm_sq_eq]
      simp [x, dotProduct, pow_two]
    calc
      dotProduct (A *ᵥ v) (A *ᵥ v)
          = ‖T x‖ ^ (2 : ℕ) := hTx_sq.symm
      _ ≤ (C * ‖x‖) ^ (2 : ℕ) := hsq
      _ = C ^ (2 : ℕ) * dotProduct v v := by
          rw [← hx_sq]
          ring

/--
Chewi Definition A.5, rectangular eigenvalue display without the redundant
absolute value.  On a nonempty finite domain, the Euclidean operator norm of a
real rectangular matrix is the square root of the largest eigenvalue of
`Aᵀ A`.
-/
theorem chewiA5_l2_opNorm_eq_sqrt_finset_sup_eigenvalues_transpose_mul_self
    [DecidableEq n] [Nonempty n] (A : Matrix m n ℝ) :
    ‖A‖ =
      Real.sqrt
        (Finset.univ.sup' Finset.univ_nonempty
          (fun i =>
            (chewiA5_transpose_mul_self_posSemidef A).isHermitian.eigenvalues i)) := by
  let hGram : (Aᵀ * A).IsHermitian :=
    (chewiA5_transpose_mul_self_posSemidef A).isHermitian
  let M : ℝ :=
    Finset.univ.sup' Finset.univ_nonempty (fun i => hGram.eigenvalues i)
  have hM_nonneg : 0 ≤ M := by
    let i0 : n := Classical.choice ‹Nonempty n›
    have hi0_nonneg :
        0 ≤ hGram.eigenvalues i0 :=
      (chewiA5_transpose_mul_self_posSemidef A).eigenvalues_nonneg i0
    exact hi0_nonneg.trans
      (Finset.le_sup' (s := Finset.univ)
        (f := fun i => hGram.eigenvalues i)
        (by simp : i0 ∈ Finset.univ))
  have hnorm_le : ‖A‖ ≤ Real.sqrt M := by
    have hM_sq : (Real.sqrt M) ^ (2 : ℕ) = M := Real.sq_sqrt hM_nonneg
    refine (chewiA5_transpose_mul_self_le_scalar_one_iff_l2_opNorm_le
      (A := A) (C := Real.sqrt M) (Real.sqrt_nonneg M)).mp ?_
    have hleM : Aᵀ * A ≤ M • (1 : Matrix n n ℝ) := by
      rw [chewiA3_le_scalar_one_iff_eigenvalues_le hGram]
      intro i
      exact Finset.le_sup' (s := Finset.univ)
        (f := fun i => hGram.eigenvalues i)
        (by simp : i ∈ Finset.univ)
    simpa [hM_sq] using hleM
  have hsqrt_le : Real.sqrt M ≤ ‖A‖ := by
    have hle_normsq : M ≤ ‖A‖ ^ (2 : ℕ) := by
      have hbound :
          Aᵀ * A ≤ (‖A‖ ^ (2 : ℕ)) • (1 : Matrix n n ℝ) :=
        (chewiA5_transpose_mul_self_le_scalar_one_iff_l2_opNorm_le
          (A := A) (C := ‖A‖) (norm_nonneg A)).mpr le_rfl
      have heig_bound :
          ∀ i, hGram.eigenvalues i ≤ ‖A‖ ^ (2 : ℕ) :=
        (chewiA3_le_scalar_one_iff_eigenvalues_le hGram).mp hbound
      exact Finset.sup'_le Finset.univ_nonempty
        (fun i => hGram.eigenvalues i)
        (by intro i _hi; exact heig_bound i)
    calc
      Real.sqrt M ≤ Real.sqrt (‖A‖ ^ (2 : ℕ)) :=
        Real.sqrt_le_sqrt hle_normsq
      _ = ‖A‖ := by
        rw [Real.sqrt_sq_eq_abs, abs_of_nonneg (norm_nonneg A)]
  exact le_antisymm hnorm_le hsqrt_le

/--
Chewi Definition A.5, rectangular absolute-eigenvalue display.  Since `Aᵀ A`
is PSD, the absolute value is redundant, but this theorem matches the source
formula: `||A||_op` is the square root of the largest absolute eigenvalue of
`Aᵀ A`.
-/
theorem chewiA5_l2_opNorm_eq_sqrt_finset_sup_abs_eigenvalues_transpose_mul_self
    [DecidableEq n] [Nonempty n] (A : Matrix m n ℝ) :
    ‖A‖ =
      Real.sqrt
        (Finset.univ.sup' Finset.univ_nonempty
          (fun i =>
            |(chewiA5_transpose_mul_self_posSemidef A).isHermitian.eigenvalues i|)) := by
  let hGram : (Aᵀ * A).IsHermitian :=
    (chewiA5_transpose_mul_self_posSemidef A).isHermitian
  have hsup_abs :
      Finset.univ.sup' Finset.univ_nonempty
          (fun i => |hGram.eigenvalues i|) =
        Finset.univ.sup' Finset.univ_nonempty
          (fun i => hGram.eigenvalues i) := by
    simp [abs_of_nonneg,
      (chewiA5_transpose_mul_self_posSemidef A).eigenvalues_nonneg]
  rw [hsup_abs]
  exact chewiA5_l2_opNorm_eq_sqrt_finset_sup_eigenvalues_transpose_mul_self A

/--
Chewi Definition A.5 setup for the alternate Gram matrix: `A Aᵀ` is
positive semidefinite.
-/
theorem chewiA5_mul_self_transpose_posSemidef
    (A : Matrix m n ℝ) :
    (A * Aᵀ).PosSemidef := by
  simpa using (chewiA5_transpose_mul_self_posSemidef Aᵀ)

/--
Chewi Definition A.5, alternate rectangular eigenvalue display without the
redundant absolute value.  On a nonempty finite codomain, the Euclidean
operator norm is the square root of the largest eigenvalue of `A Aᵀ`.
-/
theorem chewiA5_l2_opNorm_eq_sqrt_finset_sup_eigenvalues_mul_self_transpose
    [DecidableEq m] [DecidableEq n] [Nonempty m] (A : Matrix m n ℝ) :
    ‖A‖ =
      Real.sqrt
        (Finset.univ.sup' Finset.univ_nonempty
          (fun i =>
            (chewiA5_mul_self_transpose_posSemidef A).isHermitian.eigenvalues i)) := by
  have h :=
    chewiA5_l2_opNorm_eq_sqrt_finset_sup_eigenvalues_transpose_mul_self
      (A := Aᵀ)
  have hnorm : ‖Aᵀ‖ = ‖A‖ := by
    simpa using Matrix.l2_opNorm_conjTranspose A
  rw [hnorm] at h
  simpa [chewiA5_mul_self_transpose_posSemidef] using h

/--
Chewi Definition A.5, alternate rectangular absolute-eigenvalue display.  This
matches the source sentence that `||A||_op` is also the square root of the
largest absolute eigenvalue of `A Aᵀ`.
-/
theorem chewiA5_l2_opNorm_eq_sqrt_finset_sup_abs_eigenvalues_mul_self_transpose
    [DecidableEq m] [DecidableEq n] [Nonempty m] (A : Matrix m n ℝ) :
    ‖A‖ =
      Real.sqrt
        (Finset.univ.sup' Finset.univ_nonempty
          (fun i =>
            |(chewiA5_mul_self_transpose_posSemidef A).isHermitian.eigenvalues i|)) := by
  have h :=
    chewiA5_l2_opNorm_eq_sqrt_finset_sup_abs_eigenvalues_transpose_mul_self
      (A := Aᵀ)
  have hnorm : ‖Aᵀ‖ = ‖A‖ := by
    simpa using Matrix.l2_opNorm_conjTranspose A
  rw [hnorm] at h
  simpa [chewiA5_mul_self_transpose_posSemidef] using h

/--
Chewi Definition A.5, rectangular product spectrum padding.  This is the
source-facing characteristic-polynomial form of the statement that `A^T A`
and `A A^T` have the same nonzero eigenvalues, with only zero multiplicities
changed by the rectangular dimensions.
-/
theorem chewiA5_charpoly_padding_transpose_mul_self_mul_self_transpose
    [DecidableEq m] [DecidableEq n] (A : Matrix m n ℝ) :
    X ^ Fintype.card m * (Aᵀ * A).charpoly =
      X ^ Fintype.card n * (A * Aᵀ).charpoly := by
  simpa using Matrix.charpoly_mul_comm' (A := Aᵀ) (B := A)

/--
If the row index type is no larger than the column index type, `A^T A` has
the extra zero eigenvalues.  This is the one-sided padded characteristic
polynomial version of Chewi Definition A.5.
-/
theorem chewiA5_charpoly_transpose_mul_self_eq_X_pow_mul_self_transpose_of_card_le
    [DecidableEq m] [DecidableEq n] (A : Matrix m n ℝ)
    (hcard : Fintype.card m ≤ Fintype.card n) :
    (Aᵀ * A).charpoly =
      X ^ (Fintype.card n - Fintype.card m) * (A * Aᵀ).charpoly := by
  simpa using Matrix.charpoly_mul_comm_of_le (A := Aᵀ) (B := A) hcard

/--
If the column index type is no larger than the row index type, `A A^T` has
the extra zero eigenvalues.  This is the opposite one-sided padded
characteristic-polynomial version of Chewi Definition A.5.
-/
theorem chewiA5_charpoly_mul_self_transpose_eq_X_pow_transpose_mul_self_of_card_le
    [DecidableEq m] [DecidableEq n] (A : Matrix m n ℝ)
    (hcard : Fintype.card n ≤ Fintype.card m) :
    (A * Aᵀ).charpoly =
      X ^ (Fintype.card m - Fintype.card n) * (Aᵀ * A).charpoly := by
  simpa using Matrix.charpoly_mul_comm_of_le (A := A) (B := Aᵀ) hcard

/--
When the rectangular matrix is square up to a cardinal equality of index
types, the two Gram products have exactly the same characteristic polynomial.
-/
theorem chewiA5_charpoly_transpose_mul_self_eq_mul_self_transpose_of_card_eq
    [DecidableEq m] [DecidableEq n] (A : Matrix m n ℝ)
    (hcard : Fintype.card m = Fintype.card n) :
    (Aᵀ * A).charpoly = (A * Aᵀ).charpoly := by
  have hpad :=
    chewiA5_charpoly_padding_transpose_mul_self_mul_self_transpose A
  rw [hcard] at hpad
  exact (isRegular_X_pow (R := ℝ) (Fintype.card n)).left.eq_iff.mp hpad

/--
For symmetric real matrices, an absolute quadratic-form bound controls the
Euclidean operator norm.  This is the Rayleigh-quotient bridge used in the
symmetric specialization of Chewi Definition A.5.
-/
theorem chewiA5_l2_opNorm_le_of_abs_quadraticForm_bound
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {C : ℝ}
    (hC : 0 ≤ C)
    (hbound : ∀ v : n -> ℝ,
      |dotProduct v (A *ᵥ v)| ≤ C * dotProduct v v) :
    ‖A‖ ≤ C := by
  rw [Matrix.l2_opNorm_def]
  let T : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
    (Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
      LinearMap.toContinuousLinearMap A
  change ‖T‖ ≤ C
  have hsymm : (T : EuclideanSpace ℝ n →ₗ[ℝ] EuclideanSpace ℝ n).IsSymmetric := by
    have hsymm_lin : (Matrix.toEuclideanLin A).IsSymmetric :=
      Matrix.isSymmetric_toEuclideanLin_iff.mpr hA
    simpa [T] using hsymm_lin
  rw [ContinuousLinearMap.norm_eq_iSup_rayleighQuotient T hsymm]
  refine ciSup_le ?_
  intro x
  by_cases hx_zero : ‖x‖ = 0
  · have hx0 : x = 0 := norm_eq_zero.mp hx_zero
    simpa [ContinuousLinearMap.rayleighQuotient, hx0] using hC
  · have hden_pos : 0 < ‖x‖ ^ (2 : ℕ) := by positivity
    have hinner :
        inner ℝ (T x) x = dotProduct x.ofLp (A *ᵥ x.ofLp) := by
      simp [T, Matrix.toLpLin_apply, EuclideanSpace.inner_eq_star_dotProduct]
    have hx_sq : ‖x‖ ^ (2 : ℕ) = dotProduct x.ofLp x.ofLp := by
      rw [EuclideanSpace.real_norm_sq_eq]
      simp [dotProduct, pow_two]
    have hquad :
        |inner ℝ (T x) x| ≤ C * ‖x‖ ^ (2 : ℕ) := by
      simpa [hinner, hx_sq] using hbound x.ofLp
    have hdiv : |inner ℝ (T x) x| / ‖x‖ ^ (2 : ℕ) ≤ C := by
      rw [div_le_iff₀ hden_pos]
      exact hquad
    simpa [ContinuousLinearMap.rayleighQuotient,
      ContinuousLinearMap.reApplyInnerSelf_apply, abs_div] using hdiv

/--
Chewi Definition A.5, symmetric-matrix form.  For a symmetric real matrix and
`C >= 0`, the Euclidean operator-norm bound is equivalent to the Loewner
sandwich `-C I <= A <= C I`.
-/
theorem chewiA5_symmetric_l2_opNorm_le_iff_neg_scalar_one_le_and_le_scalar_one
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {C : ℝ}
    (hC : 0 ≤ C) :
    ‖A‖ ≤ C ↔
      ((-C) • (1 : Matrix n n ℝ) ≤ A ∧
        A ≤ C • (1 : Matrix n n ℝ)) := by
  have hCmat : (C • (1 : Matrix n n ℝ)).IsHermitian := by
    exact Matrix.isHermitian_one.smul
      (show IsSelfAdjoint (C : ℝ) by
        simp [isSelfAdjoint_iff])
  have hnegCmat : ((-C) • (1 : Matrix n n ℝ)).IsHermitian := by
    exact Matrix.isHermitian_one.smul
      (show IsSelfAdjoint (-C : ℝ) by
        simp [isSelfAdjoint_iff])
  constructor
  · intro hnorm
    let T : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
      (Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
        LinearMap.toContinuousLinearMap A
    have hnorm_T : ‖T‖ ≤ C := by
      simpa [Matrix.l2_opNorm_def, T] using hnorm
    have hquad_abs :
        ∀ v : n -> ℝ, |dotProduct v (A *ᵥ v)| ≤ C * dotProduct v v := by
      intro v
      let x : EuclideanSpace ℝ n := WithLp.toLp 2 v
      have hpoint : ‖T x‖ ≤ C * ‖x‖ := by
        calc
          ‖T x‖ ≤ ‖T‖ * ‖x‖ := T.le_opNorm x
          _ ≤ C * ‖x‖ := mul_le_mul_of_nonneg_right hnorm_T (norm_nonneg x)
      have hinner_bound :
          |inner ℝ (T x) x| ≤ C * ‖x‖ ^ (2 : ℕ) := by
        calc
          |inner ℝ (T x) x| ≤ ‖T x‖ * ‖x‖ := abs_real_inner_le_norm (T x) x
          _ ≤ (C * ‖x‖) * ‖x‖ :=
              mul_le_mul_of_nonneg_right hpoint (norm_nonneg x)
          _ = C * ‖x‖ ^ (2 : ℕ) := by ring
      have hinner :
          inner ℝ (T x) x = dotProduct v (A *ᵥ v) := by
        simp [T, x, Matrix.toLpLin_apply, EuclideanSpace.inner_eq_star_dotProduct]
      have hx_sq : ‖x‖ ^ (2 : ℕ) = dotProduct v v := by
        rw [EuclideanSpace.real_norm_sq_eq]
        simp [x, dotProduct, pow_two]
      simpa [hinner, hx_sq] using hinner_bound
    constructor
    · rw [chewiA4_loewnerOrder_iff_quadraticForm_le hA hnegCmat]
      intro v
      have hscalar :
          dotProduct v (((-C) • (1 : Matrix n n ℝ)) *ᵥ v) =
            -(C * dotProduct v v) := by
        calc
          dotProduct v (((-C) • (1 : Matrix n n ℝ)) *ᵥ v)
              = (-C) * dotProduct v v := by
                simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
                  smul_eq_mul]
          _ = -(C * dotProduct v v) := by ring
      have hlow := (abs_le.mp (hquad_abs v)).1
      have hlow' :
          dotProduct v (((-C) • (1 : Matrix n n ℝ)) *ᵥ v) ≤
            dotProduct v (A *ᵥ v) := by
        rw [hscalar]
        exact hlow
      simpa only [neg_smul] using hlow'
    · rw [chewiA4_loewnerOrder_iff_quadraticForm_le hCmat hA]
      intro v
      have hscalar :
          dotProduct v ((C • (1 : Matrix n n ℝ)) *ᵥ v) =
            C * dotProduct v v := by
        simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
          smul_eq_mul]
      have hupper := (abs_le.mp (hquad_abs v)).2
      simpa [hscalar] using hupper
  · intro hsandwich
    refine chewiA5_l2_opNorm_le_of_abs_quadraticForm_bound hA hC ?_
    intro v
    have hupper_raw :=
      (chewiA4_loewnerOrder_iff_quadraticForm_le hCmat hA).mp
        hsandwich.2 v
    have hupper :
        dotProduct v (A *ᵥ v) ≤ C * dotProduct v v := by
      have hscalar :
          dotProduct v ((C • (1 : Matrix n n ℝ)) *ᵥ v) =
            C * dotProduct v v := by
        simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
          smul_eq_mul]
      simpa [hscalar] using hupper_raw
    have hlower_raw :=
      (chewiA4_loewnerOrder_iff_quadraticForm_le hA hnegCmat).mp
        hsandwich.1 v
    have hlower :
        -(C * dotProduct v v) ≤ dotProduct v (A *ᵥ v) := by
      have hscalar :
          dotProduct v (((-C) • (1 : Matrix n n ℝ)) *ᵥ v) =
            -(C * dotProduct v v) := by
        calc
          dotProduct v (((-C) • (1 : Matrix n n ℝ)) *ᵥ v)
              = (-C) * dotProduct v v := by
                simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
                  smul_eq_mul]
          _ = -(C * dotProduct v v) := by ring
      have hlower' :
          dotProduct v (((-C) • (1 : Matrix n n ℝ)) *ᵥ v) ≤
            dotProduct v (A *ᵥ v) := by
        simpa only [neg_smul] using hlower_raw
      rw [← hscalar]
      exact hlower'
    exact abs_le.mpr ⟨hlower, hupper⟩

/--
Chewi Theorem 13.1, matrix perturbation primitive.  If a symmetric matrix `B`
is within `eps` of a symmetric matrix `A` in Euclidean operator norm, then a
lower Loewner bound on `A` degrades by at most `eps`.
-/
theorem chewiA5_loewner_lower_of_l2_opNorm_sub_le
    [DecidableEq n] {A B : Matrix n n ℝ} (hA : A.IsHermitian)
    (hB : B.IsHermitian) {alpha eps : ℝ} (heps : 0 ≤ eps)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A) (hnorm : ‖B - A‖ ≤ eps) :
    (alpha - eps) • (1 : Matrix n n ℝ) ≤ B := by
  have hD_lower :
      (-eps) • (1 : Matrix n n ℝ) ≤ B - A :=
    ((chewiA5_symmetric_l2_opNorm_le_iff_neg_scalar_one_le_and_le_scalar_one
      (A := B - A) (hB.sub hA) heps).mp hnorm).1
  calc
    (alpha - eps) • (1 : Matrix n n ℝ)
        = alpha • (1 : Matrix n n ℝ) + (-eps) • (1 : Matrix n n ℝ) := by
          rw [sub_eq_add_neg, add_smul]
    _ ≤ A + (B - A) := add_le_add hlower hD_lower
    _ = B := by
      abel

/--
Chewi Theorem 13.1, matrix perturbation primitive.  If a symmetric matrix `B`
is within `eps` of a symmetric matrix `A` in Euclidean operator norm, then an
upper Loewner bound on `A` degrades by at most `eps`.
-/
theorem chewiA5_loewner_upper_of_l2_opNorm_sub_le
    [DecidableEq n] {A B : Matrix n n ℝ} (hA : A.IsHermitian)
    (hB : B.IsHermitian) {beta eps : ℝ} (heps : 0 ≤ eps)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ)) (hnorm : ‖B - A‖ ≤ eps) :
    B ≤ (beta + eps) • (1 : Matrix n n ℝ) := by
  have hD_upper :
      B - A ≤ eps • (1 : Matrix n n ℝ) :=
    ((chewiA5_symmetric_l2_opNorm_le_iff_neg_scalar_one_le_and_le_scalar_one
      (A := B - A) (hB.sub hA) heps).mp hnorm).2
  calc
    B = A + (B - A) := by
      abel
    _ ≤ beta • (1 : Matrix n n ℝ) + eps • (1 : Matrix n n ℝ) :=
      add_le_add hupper hD_upper
    _ = (beta + eps) • (1 : Matrix n n ℝ) := by
      rw [add_smul]

/--
Chewi Theorem 13.1, two-sided perturbation primitive.  A symmetric
operator-norm perturbation widens a scalar Loewner sandwich by `eps`.
-/
theorem chewiA5_loewner_sandwich_of_l2_opNorm_sub_le
    [DecidableEq n] {A B : Matrix n n ℝ} (hA : A.IsHermitian)
    (hB : B.IsHermitian) {alpha beta eps : ℝ} (heps : 0 ≤ eps)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ)) (hnorm : ‖B - A‖ ≤ eps) :
    (alpha - eps) • (1 : Matrix n n ℝ) ≤ B ∧
      B ≤ (beta + eps) • (1 : Matrix n n ℝ) := by
  exact
    ⟨chewiA5_loewner_lower_of_l2_opNorm_sub_le hA hB heps hlower hnorm,
      chewiA5_loewner_upper_of_l2_opNorm_sub_le hA hB heps hupper hnorm⟩

/--
Scalar monotonicity for source-facing Loewner bounds.
-/
theorem chewiA4_scalar_one_le_scalar_one_of_le
    [DecidableEq n] {c d : ℝ} (hcd : c ≤ d) :
    c • (1 : Matrix n n ℝ) ≤ d • (1 : Matrix n n ℝ) := by
  exact smul_le_smul_of_nonneg_right hcd (zero_le_one (α := Matrix n n ℝ))

/--
Chewi Theorem 13.1, Hessian lower-bound perturbation step.  This packages the
display `lambda_min(H) >= lambda_min(Hstar) - eps >= alpha / 2` in Loewner
form, ready for the Newton-method recurrence proof.
-/
theorem chewi131_hessian_lower_half_of_l2_opNorm_sub_le
    [DecidableEq n] {Hstar H : Matrix n n ℝ} (hHstar : Hstar.IsHermitian)
    (hH : H.IsHermitian) {alpha eps : ℝ} (heps : 0 ≤ eps)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hnorm : ‖H - Hstar‖ ≤ eps) (hhalf : eps ≤ alpha / 2) :
    (alpha / 2) • (1 : Matrix n n ℝ) ≤ H := by
  have hlower_degraded :
      (alpha - eps) • (1 : Matrix n n ℝ) ≤ H :=
    chewiA5_loewner_lower_of_l2_opNorm_sub_le hHstar hH heps hlower hnorm
  have hscalar : alpha / 2 ≤ alpha - eps := by
    nlinarith
  exact
    (chewiA4_scalar_one_le_scalar_one_of_le (n := n) hscalar).trans
      hlower_degraded

/--
Chewi Theorem 13.1, Lipschitz-Hessian source display.  If the operator-norm
Hessian error is bounded by `gamma * r` and `gamma * r <= alpha / 2`, the
current Hessian keeps the lower bound `(alpha / 2) I`.
-/
theorem chewi131_hessian_lower_half_of_lipschitz_opNorm
    [DecidableEq n] {Hstar H : Matrix n n ℝ} (hHstar : Hstar.IsHermitian)
    (hH : H.IsHermitian) {alpha gamma r : ℝ} (hgr_nonneg : 0 ≤ gamma * r)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ Hstar)
    (hclose : ‖H - Hstar‖ ≤ gamma * r) (hhalf : gamma * r ≤ alpha / 2) :
    (alpha / 2) • (1 : Matrix n n ℝ) ≤ H := by
  exact
    chewi131_hessian_lower_half_of_l2_opNorm_sub_le hHstar hH hgr_nonneg
      hlower hclose hhalf

/--
A positive scalar Loewner lower bound makes a symmetric matrix positive
definite.
-/
theorem chewiA5_posDef_of_pos_scalar_one_le
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {alpha : ℝ}
    (halpha : 0 < alpha) (hlower : alpha • (1 : Matrix n n ℝ) ≤ A) :
    A.PosDef := by
  rw [hA.posDef_iff_eigenvalues_pos]
  intro i
  exact
    halpha.trans_le
      ((chewiA3_scalar_one_le_iff_le_eigenvalues hA).mp hlower i)

/--
For a nonnegative symmetric matrix, an upper scalar Loewner bound is enough to
bound the Euclidean operator norm.
-/
theorem chewiA5_symmetric_l2_opNorm_le_of_nonneg_le_scalar_one
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {C : ℝ}
    (hC : 0 ≤ C) (hnonneg : 0 ≤ A)
    (hupper : A ≤ C • (1 : Matrix n n ℝ)) :
    ‖A‖ ≤ C := by
  have hlower : (-C) • (1 : Matrix n n ℝ) ≤ A := by
    have hneg_le_zero : -C ≤ 0 := neg_nonpos.mpr hC
    have hneg_scalar_le_zero :
        (-C) • (1 : Matrix n n ℝ) ≤
          (0 : ℝ) • (1 : Matrix n n ℝ) :=
      chewiA4_scalar_one_le_scalar_one_of_le (n := n) hneg_le_zero
    have hzero_le : (0 : ℝ) • (1 : Matrix n n ℝ) ≤ A := by
      simpa using hnonneg
    exact hneg_scalar_le_zero.trans hzero_le
  exact
    (chewiA5_symmetric_l2_opNorm_le_iff_neg_scalar_one_le_and_le_scalar_one
      hA hC).mpr
      ⟨hlower, hupper⟩

/--
Spectral step-map contraction for a symmetric matrix with source Loewner
bounds.  If `α I ≤ A ≤ β I` and the step size satisfies both `α h ≤ 1` and
`β h ≤ 1`, then the Euclidean operator norm of `I - h A` is at most
`1 - α h`.
-/
theorem chewiA5_l2_opNorm_one_sub_smul_le_one_sub_mul_of_loewner_bounds
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian)
    {alpha beta h : ℝ}
    (hh_nonneg : 0 ≤ h)
    (halpha_step : alpha * h ≤ 1)
    (hbeta_step : beta * h ≤ 1)
    (hlower : alpha • (1 : Matrix n n ℝ) ≤ A)
    (hupper : A ≤ beta • (1 : Matrix n n ℝ)) :
    ‖(1 : Matrix n n ℝ) - h • A‖ ≤ 1 - alpha * h := by
  let B : Matrix n n ℝ := (1 : Matrix n n ℝ) - h • A
  have hB : B.IsHermitian := by
    dsimp [B]
    exact Matrix.isHermitian_one.sub
      (hA.smul (show IsSelfAdjoint (h : ℝ) by simp [isSelfAdjoint_iff]))
  have hC : 0 ≤ 1 - alpha * h := by
    nlinarith
  have h_hA_le_one : h • A ≤ (1 : Matrix n n ℝ) := by
    calc
      h • A ≤ h • (beta • (1 : Matrix n n ℝ)) :=
        smul_le_smul_of_nonneg_left hupper hh_nonneg
      _ = (h * beta) • (1 : Matrix n n ℝ) := by
        simp [smul_smul]
      _ ≤ (1 : ℝ) • (1 : Matrix n n ℝ) :=
        chewiA4_scalar_one_le_scalar_one_of_le (n := n) (by nlinarith)
      _ = (1 : Matrix n n ℝ) := by simp
  have hnonneg : 0 ≤ B := by
    dsimp [B]
    exact sub_nonneg.mpr h_hA_le_one
  have h_alpha_le_hA : (alpha * h) • (1 : Matrix n n ℝ) ≤ h • A := by
    calc
      (alpha * h) • (1 : Matrix n n ℝ) =
          h • (alpha • (1 : Matrix n n ℝ)) := by
        simp [smul_smul, mul_comm]
      _ ≤ h • A := smul_le_smul_of_nonneg_left hlower hh_nonneg
  have hupperB : B ≤ (1 - alpha * h) • (1 : Matrix n n ℝ) := by
    dsimp [B]
    calc
      (1 : Matrix n n ℝ) - h • A
          ≤ (1 : Matrix n n ℝ) - (alpha * h) • (1 : Matrix n n ℝ) := by
            exact sub_le_sub_left h_alpha_le_hA (1 : Matrix n n ℝ)
      _ = (1 - alpha * h) • (1 : Matrix n n ℝ) := by
            rw [sub_eq_add_neg]
            rw [show 1 - alpha * h = 1 + -(alpha * h) by ring]
            rw [add_smul]
            simp
  exact
    chewiA5_symmetric_l2_opNorm_le_of_nonneg_le_scalar_one
      hB hC hnonneg hupperB

section ContinuousLinearMap

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/--
A reusable coercivity-to-inverse-norm bridge.  If `T` has a left inverse `S`
and `T` is bounded below in quadratic form by `c > 0`, then the operator norm
of `S` is at most `c^{-1}`.
-/
theorem continuousLinearMap_opNorm_right_inverse_le_of_inner_lower
    {T S : E →L[ℝ] E} {c : ℝ} (hc : 0 < c)
    (hlower : ∀ x : E, c * ‖x‖ ^ (2 : ℕ) ≤ inner ℝ (T x) x)
    (hleft : ∀ x : E, T (S x) = x) :
    ‖S‖ ≤ c⁻¹ := by
  refine S.opNorm_le_bound (le_of_lt (inv_pos.mpr hc)) ?_
  intro x
  by_cases hy : S x = 0
  · have hnonneg : 0 ≤ c⁻¹ * ‖x‖ :=
      mul_nonneg (inv_nonneg.mpr (le_of_lt hc)) (norm_nonneg x)
    simpa [hy] using hnonneg
  · have hypos : 0 < ‖S x‖ := norm_pos_iff.mpr hy
    have hquad : c * ‖S x‖ ^ (2 : ℕ) ≤ inner ℝ x (S x) := by
      simpa [hleft x] using hlower (S x)
    have hinner_le : inner ℝ x (S x) ≤ ‖x‖ * ‖S x‖ :=
      (le_abs_self _).trans (abs_real_inner_le_norm x (S x))
    have hmain : c * ‖S x‖ ^ (2 : ℕ) ≤ ‖x‖ * ‖S x‖ :=
      hquad.trans hinner_le
    have hmul : c * ‖S x‖ ≤ ‖x‖ := by
      nlinarith [hypos]
    have hdiv : ‖S x‖ ≤ ‖x‖ / c :=
      (le_div_iff₀ hc).mpr (by simpa [mul_comm] using hmul)
    simpa [div_eq_mul_inv, mul_comm] using hdiv

end ContinuousLinearMap

/--
Chewi Theorem 13.1, supplied inverse-Loewner gate for the reciprocal
operator-norm bound.
-/
theorem chewi131_inverse_l2_opNorm_le_two_div_alpha_of_inverse_loewner_upper
    [DecidableEq n] {H : Matrix n n ℝ} (hH : H.IsHermitian) {alpha : ℝ}
    (halpha : 0 < alpha) (hinv_nonneg : 0 ≤ H⁻¹)
    (hinv_upper : H⁻¹ ≤ (2 / alpha) • (1 : Matrix n n ℝ)) :
    ‖H⁻¹‖ ≤ 2 / alpha := by
  have hC : 0 ≤ 2 / alpha := by
    positivity
  exact
    chewiA5_symmetric_l2_opNorm_le_of_nonneg_le_scalar_one hH.inv hC
      hinv_nonneg hinv_upper

/--
Chewi Theorem 13.1, inverse-operator-norm bound with the positive-definiteness
part discharged from the half-radius Hessian lower estimate.  The remaining
supplied gate is the standard inverse Loewner upper bound.
-/
theorem chewi131_inverse_l2_opNorm_le_two_div_alpha_of_hessian_lower_half_and_inverse_loewner_upper
    [DecidableEq n] {H : Matrix n n ℝ} (hH : H.IsHermitian) {alpha : ℝ}
    (halpha : 0 < alpha)
    (hlower : (alpha / 2) • (1 : Matrix n n ℝ) ≤ H)
    (hinv_upper : H⁻¹ ≤ (2 / alpha) • (1 : Matrix n n ℝ)) :
    ‖H⁻¹‖ ≤ 2 / alpha := by
  have hhalf_pos : 0 < alpha / 2 := by
    positivity
  have hH_posDef : H.PosDef :=
    chewiA5_posDef_of_pos_scalar_one_le hH hhalf_pos hlower
  exact
    chewi131_inverse_l2_opNorm_le_two_div_alpha_of_inverse_loewner_upper
      hH halpha hH_posDef.inv.posSemidef.nonneg hinv_upper

/--
Chewi Theorem 13.1, inverse-operator-norm bound from the half-radius Hessian
lower estimate.  This discharges the previously supplied inverse-Loewner gate
by applying coercivity to the Euclidean linear map induced by `H`.
-/
theorem chewi131_inverse_l2_opNorm_le_two_div_alpha_of_hessian_lower_half
    [DecidableEq n] {H : Matrix n n ℝ} (hH : H.IsHermitian) {alpha : ℝ}
    (halpha : 0 < alpha)
    (hlower : (alpha / 2) • (1 : Matrix n n ℝ) ≤ H) :
    ‖H⁻¹‖ ≤ 2 / alpha := by
  rw [Matrix.l2_opNorm_def]
  let T : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
    (Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
      LinearMap.toContinuousLinearMap H
  let S : EuclideanSpace ℝ n →L[ℝ] EuclideanSpace ℝ n :=
    (Matrix.toEuclideanLin (𝕜 := ℝ) (m := n) (n := n)).trans
      LinearMap.toContinuousLinearMap H⁻¹
  change ‖S‖ ≤ 2 / alpha
  have hhalf_pos : 0 < alpha / 2 := by
    positivity
  have hH_posDef : H.PosDef :=
    chewiA5_posDef_of_pos_scalar_one_le hH hhalf_pos hlower
  have hscalarHerm :
      ((alpha / 2) • (1 : Matrix n n ℝ)).IsHermitian := by
    exact Matrix.isHermitian_one.smul
      (show IsSelfAdjoint (alpha / 2 : ℝ) by
        simp [isSelfAdjoint_iff])
  have hcoercive :
      ∀ x : EuclideanSpace ℝ n,
        (alpha / 2) * ‖x‖ ^ (2 : ℕ) ≤ inner ℝ (T x) x := by
    intro x
    have hquad :=
      (chewiA4_loewnerOrder_iff_quadraticForm_le hH hscalarHerm).mp
        hlower x.ofLp
    have hscalar :
        dotProduct x.ofLp (((alpha / 2) • (1 : Matrix n n ℝ)) *ᵥ x.ofLp) =
          (alpha / 2) * dotProduct x.ofLp x.ofLp := by
      simp only [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul,
        smul_eq_mul]
    have hx_sq : ‖x‖ ^ (2 : ℕ) = dotProduct x.ofLp x.ofLp := by
      rw [EuclideanSpace.real_norm_sq_eq]
      simp [dotProduct, pow_two]
    have hinner :
        inner ℝ (T x) x = dotProduct x.ofLp (H *ᵥ x.ofLp) := by
      simp [T, Matrix.toLpLin_apply, EuclideanSpace.inner_eq_star_dotProduct]
    simpa [hscalar, hx_sq, hinner] using hquad
  have hleft : ∀ x : EuclideanSpace ℝ n, T (S x) = x := by
    intro x
    have hdet : IsUnit H.det :=
      (Matrix.isUnit_iff_isUnit_det H).mp hH_posDef.isUnit
    have hmul : H * H⁻¹ = 1 := Matrix.mul_nonsing_inv H hdet
    simp [T, S, Matrix.toLpLin_apply, Matrix.mulVec_mulVec, hmul]
  have hbound :
      ‖S‖ ≤ (alpha / 2)⁻¹ :=
    continuousLinearMap_opNorm_right_inverse_le_of_inner_lower hhalf_pos
      hcoercive hleft
  have hinv : (alpha / 2)⁻¹ = 2 / alpha := by
    field_simp [halpha.ne']
  simpa [hinv] using hbound

/--
Chewi Theorem 13.1, inverse Loewner upper bound from the half-radius Hessian
lower estimate.  This is the exact gate previously left supplied.
-/
theorem chewi131_inverse_loewner_upper_of_hessian_lower_half
    [DecidableEq n] {H : Matrix n n ℝ} (hH : H.IsHermitian) {alpha : ℝ}
    (halpha : 0 < alpha)
    (hlower : (alpha / 2) • (1 : Matrix n n ℝ) ≤ H) :
    H⁻¹ ≤ (2 / alpha) • (1 : Matrix n n ℝ) := by
  have hC : 0 ≤ 2 / alpha := by
    positivity
  have hnorm :
      ‖H⁻¹‖ ≤ 2 / alpha :=
    chewi131_inverse_l2_opNorm_le_two_div_alpha_of_hessian_lower_half hH
      halpha hlower
  exact
    ((chewiA5_symmetric_l2_opNorm_le_iff_neg_scalar_one_le_and_le_scalar_one
      hH.inv hC).mp hnorm).2

/--
Chewi Definition A.5, symmetric eigenvalue form.  For a symmetric real matrix,
`||A||_op <= C` is equivalent to the source statement that all eigenvalues of
`A` have absolute value at most `C`.
-/
theorem chewiA5_symmetric_l2_opNorm_le_iff_abs_eigenvalues_le
    [DecidableEq n] {A : Matrix n n ℝ} (hA : A.IsHermitian) {C : ℝ}
    (hC : 0 ≤ C) :
    ‖A‖ ≤ C ↔ ∀ i, |hA.eigenvalues i| ≤ C := by
  rw [chewiA5_symmetric_l2_opNorm_le_iff_neg_scalar_one_le_and_le_scalar_one hA hC]
  rw [chewiA3_scalar_bounds_iff_eigenvalues_mem_Icc hA]
  constructor
  · intro h i
    exact abs_le.mpr ⟨(h i).1, (h i).2⟩
  · intro h i
    exact abs_le.mp (h i)

/--
Chewi Definition A.5, symmetric max-eigenvalue display.  On a nonempty finite
index type, the Euclidean operator norm of a symmetric real matrix is the
finite maximum of the absolute values of its eigenvalues.
-/
theorem chewiA5_symmetric_l2_opNorm_eq_finset_sup_abs_eigenvalues
    [DecidableEq n] [Nonempty n] {A : Matrix n n ℝ} (hA : A.IsHermitian) :
    ‖A‖ =
      Finset.univ.sup' Finset.univ_nonempty (fun i => |hA.eigenvalues i|) := by
  let M : ℝ :=
    Finset.univ.sup' Finset.univ_nonempty (fun i => |hA.eigenvalues i|)
  have hM_nonneg : 0 ≤ M := by
    let i0 : n := Classical.choice ‹Nonempty n›
    exact (abs_nonneg (hA.eigenvalues i0)).trans
      (Finset.le_sup' (s := Finset.univ)
        (f := fun i => |hA.eigenvalues i|)
        (by simp : i0 ∈ Finset.univ))
  have hnorm_le_M : ‖A‖ ≤ M := by
    rw [chewiA5_symmetric_l2_opNorm_le_iff_abs_eigenvalues_le hA hM_nonneg]
    intro i
    exact Finset.le_sup' (s := Finset.univ)
      (f := fun i => |hA.eigenvalues i|)
      (by simp : i ∈ Finset.univ)
  have hM_le_norm : M ≤ ‖A‖ := by
    have hbounds :
        ∀ i, |hA.eigenvalues i| ≤ ‖A‖ :=
      (chewiA5_symmetric_l2_opNorm_le_iff_abs_eigenvalues_le
        hA (norm_nonneg A)).mp le_rfl
    exact Finset.sup'_le Finset.univ_nonempty
      (fun i => |hA.eigenvalues i|) (by intro i _hi; exact hbounds i)
  exact le_antisymm hnorm_le_M hM_le_norm

end Optimization
end StatInference
