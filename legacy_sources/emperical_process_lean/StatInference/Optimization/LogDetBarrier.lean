import Mathlib.Analysis.Calculus.Deriv.Polynomial
import Mathlib.Analysis.Calculus.FDeriv.Mul
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.LinearAlgebra.Matrix.Charpoly.Coeff
import Mathlib.Topology.Algebra.Module.FiniteDimension
import StatInference.Optimization.InteriorPoint

/-!
# Chewi Example 13.14(2): PSD log-det barrier surface

This module starts the source-facing Lean surface for the semidefinite
logarithmic barrier from Chewi Example 13.14(2).  The full self-concordance
proof is not duplicated or asserted here; this packet records the PSD/PD cone,
the barrier value `X ↦ -log det X`, and the diagonal restriction bridge to the
already-verified positive-orthant logarithmic barrier.
-/

namespace StatInference
namespace Optimization

open Polynomial
open scoped BigOperators Matrix MatrixOrder Matrix.Norms.Frobenius

/-- The cone of positive-semidefinite square real matrices. -/
def matrixPsdCone (d : ℕ) : Set (Matrix (Fin d) (Fin d) ℝ) :=
  {X | X.PosSemidef}

/-- The positive-definite, strict-interior surface for the PSD cone. -/
def matrixPosDefCone (d : ℕ) : Set (Matrix (Fin d) (Fin d) ℝ) :=
  {X | X.PosDef}

@[simp] theorem mem_matrixPsdCone_iff {d : ℕ}
    {X : Matrix (Fin d) (Fin d) ℝ} :
    X ∈ matrixPsdCone d ↔ X.PosSemidef := by
  rfl

@[simp] theorem mem_matrixPosDefCone_iff {d : ℕ}
    {X : Matrix (Fin d) (Fin d) ℝ} :
    X ∈ matrixPosDefCone d ↔ X.PosDef := by
  rfl

/-- Positive-definite matrices sit in the PSD cone. -/
theorem matrixPosDefCone_subset_matrixPsdCone (d : ℕ) :
    matrixPosDefCone d ⊆ matrixPsdCone d := by
  intro X hX
  exact hX.posSemidef

/--
The real Hermitian, equivalently symmetric, matrices as a linear subspace of
the ambient raw matrix space.  This is a modeling guardrail for the PSD cone:
Chewi's semidefinite cone lives in the symmetric-matrix vector space, while
`Matrix (Fin d) (Fin d) ℝ` contains nonsymmetric perturbations.
-/
def matrixHermitianSubmodule (d : ℕ) :
    Submodule ℝ (Matrix (Fin d) (Fin d) ℝ) where
  carrier := {X | X.IsHermitian}
  zero_mem' := Matrix.isHermitian_zero
  add_mem' hX hY := hX.add hY
  smul_mem' c X hX := hX.smul (by
    change star c = c
    simp)

theorem matrixPsdCone_subset_matrixHermitianSubmodule (d : ℕ) :
    matrixPsdCone d ⊆
      (matrixHermitianSubmodule d : Set (Matrix (Fin d) (Fin d) ℝ)) := by
  intro X hX
  exact hX.1

theorem matrixHermitianSubmodule_ne_top_of_ne
    {d : ℕ} {i j : Fin d} (hij : i ≠ j) :
    matrixHermitianSubmodule d ≠ ⊤ := by
  intro htop
  have hmem :
      Matrix.single i j (1 : ℝ) ∈ matrixHermitianSubmodule d := by
    simp [htop]
  have hsym := Matrix.IsHermitian.apply hmem i j
  have hji : Matrix.single i j (1 : ℝ) j i = 0 := by
    rw [Matrix.single_apply_of_ne]
    rintro ⟨hij_eq, _⟩
    exact hij hij_eq
  have hij_entry : Matrix.single i j (1 : ℝ) i j = 1 := by
    simp
  rw [hji, hij_entry] at hsym
  norm_num at hsym

theorem interior_matrixHermitianSubmodule_eq_empty_of_ne
    {d : ℕ} {i j : Fin d} (hij : i ≠ j) :
    interior (matrixHermitianSubmodule d :
      Set (Matrix (Fin d) (Fin d) ℝ)) = ∅ := by
  by_contra hne
  have hnonempty :
      (interior (matrixHermitianSubmodule d :
        Set (Matrix (Fin d) (Fin d) ℝ))).Nonempty :=
    Set.nonempty_iff_ne_empty.mpr hne
  have htop := Submodule.eq_top_of_nonempty_interior'
    (matrixHermitianSubmodule d) hnonempty
  exact matrixHermitianSubmodule_ne_top_of_ne hij htop

theorem interior_matrixPsdCone_eq_empty_of_ne
    {d : ℕ} {i j : Fin d} (hij : i ≠ j) :
    interior (matrixPsdCone d) = ∅ := by
  apply Set.eq_empty_iff_forall_notMem.mpr
  intro X hX
  have hsub :=
    interior_mono (matrixPsdCone_subset_matrixHermitianSubmodule d) hX
  rw [interior_matrixHermitianSubmodule_eq_empty_of_ne hij] at hsub
  exact hsub

/--
In the full raw `2 x 2` matrix space, the PSD cone has empty interior.  Thus
the textbook identity `int S_+^d = S_{++}^d` must be formalized in the
symmetric/Hermitian matrix subspace, not in the ambient raw matrix type.
-/
theorem interior_matrixPsdCone_eq_empty_fin_two :
    interior (matrixPsdCone 2) = ∅ := by
  exact interior_matrixPsdCone_eq_empty_of_ne
    (d := 2) (i := 0) (j := 1) (by decide)

theorem matrixPosDefCone_not_subset_interior_matrixPsdCone_fin_two :
    ¬ matrixPosDefCone 2 ⊆ interior (matrixPsdCone 2) := by
  intro hsubset
  have hpd : (1 : Matrix (Fin 2) (Fin 2) ℝ) ∈ matrixPosDefCone 2 := by
    exact Matrix.PosDef.one
  have hin : (1 : Matrix (Fin 2) (Fin 2) ℝ) ∈ interior (matrixPsdCone 2) :=
    hsubset hpd
  rw [interior_matrixPsdCone_eq_empty_fin_two] at hin
  exact hin

/--
The source value `X ↦ -log det X` from Chewi Example 13.14(2), represented
through the scalar logarithmic barrier already used in Chapter 13.
-/
noncomputable def matrixNegLogDetBarrier {d : ℕ}
    (X : Matrix (Fin d) (Fin d) ℝ) : ℝ :=
  negLogBarrier X.det

theorem matrixNegLogDetBarrier_eq_neg_log_det {d : ℕ}
    (X : Matrix (Fin d) (Fin d) ℝ) :
    matrixNegLogDetBarrier X = -Real.log X.det := by
  rfl

/-- The determinant argument of the PSD log-det barrier is positive on the PD cone. -/
theorem matrixNegLogDetBarrier_det_pos_of_mem_posDefCone {d : ℕ}
    {X : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    0 < X.det :=
  hX.det_pos

/--
First-order determinant expansion along a matrix line at the identity.
This is the analytic Jacobi seed supplied by mathlib's polynomial
`det (1 + tM)` expansion.
-/
theorem matrix_det_one_add_smul_hasDerivAt_zero {d : ℕ}
    (M : Matrix (Fin d) (Fin d) ℝ) :
    HasDerivAt (fun t : ℝ => (1 + t • M).det) (Matrix.trace M) 0 := by
  let p : ℝ[X] := (1 + (X : ℝ[X]) • M.map C).det
  have hp :
      HasDerivAt (fun t : ℝ => p.eval t) (Matrix.trace M) 0 := by
    have hbase := Polynomial.hasDerivAt p (0 : ℝ)
    have hder : p.derivative.eval 0 = Matrix.trace M := by
      simpa [p] using Matrix.derivative_det_one_add_X_smul M
    simpa [hder] using hbase
  have heq : (fun t : ℝ => p.eval t) = fun t : ℝ => (1 + t • M).det := by
    funext t
    simp [p, eval_det, ← Matrix.smul_eq_mul_diagonal]
  simpa [heq] using hp

/--
Directional Jacobi formula for the determinant along the line `X + t U`,
under an invertibility hypothesis on `X`.
-/
theorem matrix_det_line_hasDerivAt_zero_of_isUnit_det {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : IsUnit X.det) :
    HasDerivAt (fun t : ℝ => (X + t • U).det)
      (X.det * Matrix.trace (X⁻¹ * U)) 0 := by
  have hbase := matrix_det_one_add_smul_hasDerivAt_zero (X⁻¹ * U)
  have hscaled :
      HasDerivAt
        (fun t : ℝ => X.det * (1 + t • (X⁻¹ * U)).det)
        (X.det * Matrix.trace (X⁻¹ * U)) 0 :=
    HasDerivAt.const_mul X.det hbase
  have heq :
      (fun t : ℝ => X.det * (1 + t • (X⁻¹ * U)).det) =
        fun t : ℝ => (X + t • U).det := by
    funext t
    calc
      X.det * (1 + t • (X⁻¹ * U)).det
          = (X * (1 + t • (X⁻¹ * U))).det := by
              rw [Matrix.det_mul]
      _ = (X + t • U).det := by
          congr 1
          have hcancel : X * (X⁻¹ * U) = U := by
            rw [← Matrix.mul_assoc, Matrix.mul_nonsing_inv X hX, Matrix.one_mul]
          simp [Matrix.mul_add, hcancel]
  simpa [heq] using hscaled

/-- Directional Jacobi formula for the determinant on the PD cone. -/
theorem matrix_det_line_hasDerivAt_zero_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    HasDerivAt (fun t : ℝ => (X + t • U).det)
      (X.det * Matrix.trace (X⁻¹ * U)) 0 :=
  matrix_det_line_hasDerivAt_zero_of_isUnit_det
    (X := X) (U := U) ((Matrix.isUnit_iff_isUnit_det (A := X)).mp hX.isUnit)

/--
Directional derivative of the source value `-log det` along matrix lines on the
positive-definite cone.
-/
theorem neg_log_det_line_hasDerivAt_zero_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    HasDerivAt (fun t : ℝ => -Real.log ((X + t • U).det))
      (-(Matrix.trace (X⁻¹ * U))) 0 := by
  have hdet := matrix_det_line_hasDerivAt_zero_of_mem_posDefCone (X := X) (U := U) hX
  have hne : (fun t : ℝ => (X + t • U).det) 0 ≠ 0 := by
    simpa using ne_of_gt (matrixNegLogDetBarrier_det_pos_of_mem_posDefCone hX)
  have hlog := hdet.log hne
  have hquot :
      (X.det * Matrix.trace (X⁻¹ * U)) / X.det =
        Matrix.trace (X⁻¹ * U) := by
    field_simp [ne_of_gt (matrixNegLogDetBarrier_det_pos_of_mem_posDefCone hX)]
  have hneg := hlog.neg
  simpa [hquot] using hneg

/--
Diagonal positive-definite matrices are exactly positive-orthant coordinate
vectors.  This is the spectral-reduction surface behind the PSD log-det route.
-/
theorem matrixDiagonal_mem_posDefCone_iff_positiveOrthant {d : ℕ}
    (x : EuclideanSpace ℝ (Fin d)) :
    Matrix.diagonal (fun i : Fin d => x i) ∈ matrixPosDefCone d ↔
      x ∈ positiveOrthant (d := d) := by
  simp [matrixPosDefCone, positiveOrthant]

/-- Positive diagonal coordinates give a positive determinant. -/
theorem matrixDiagonal_det_pos_of_positiveOrthant {d : ℕ}
    {x : EuclideanSpace ℝ (Fin d)} (hx : x ∈ positiveOrthant (d := d)) :
    0 < (Matrix.diagonal fun i : Fin d => x i).det := by
  have hpd :
      Matrix.diagonal (fun i : Fin d => x i) ∈ matrixPosDefCone d :=
    (matrixDiagonal_mem_posDefCone_iff_positiveOrthant x).2 hx
  exact matrixNegLogDetBarrier_det_pos_of_mem_posDefCone hpd

/--
On diagonal positive-definite matrices, the PSD log-det barrier is exactly the
finite positive-orthant logarithmic barrier.  This packages the source
calculation `-log det(diag x) = -∑ i log x_i` for the future full
Example 13.14(2) self-concordance route.
-/
theorem matrixNegLogDetBarrier_diagonal_eq_positiveOrthantNegLogBarrier
    {d : ℕ} {x : EuclideanSpace ℝ (Fin d)}
    (hx : x ∈ positiveOrthant (d := d)) :
    matrixNegLogDetBarrier (Matrix.diagonal fun i : Fin d => x i) =
      positiveOrthantNegLogBarrier x := by
  have hne : ∀ i ∈ (Finset.univ : Finset (Fin d)), x i ≠ 0 := by
    intro i _hi
    exact (hx i).ne'
  calc
    matrixNegLogDetBarrier (Matrix.diagonal fun i : Fin d => x i)
        = -Real.log ((Matrix.diagonal fun i : Fin d => x i).det) := by
          simp [matrixNegLogDetBarrier, negLogBarrier]
    _ = -Real.log (∏ i : Fin d, x i) := by
          rw [Matrix.det_diagonal]
    _ = -∑ i : Fin d, Real.log (x i) := by
          rw [Real.log_prod hne]
    _ = positiveOrthantNegLogBarrier x := by
          simp [positiveOrthantNegLogBarrier, negLogBarrier,
            Finset.sum_neg_distrib]

/-- Supplied gradient oracle for the PSD log-det barrier, `∇(-log det)(X) = -X⁻¹`. -/
noncomputable def matrixLogDetGrad {d : ℕ}
    (X : Matrix (Fin d) (Fin d) ℝ) : Matrix (Fin d) (Fin d) ℝ :=
  -X⁻¹

/-- Supplied Hessian action for the PSD log-det barrier: `U ↦ X⁻¹ U X⁻¹`. -/
noncomputable def matrixLogDetHess {d : ℕ}
    (X : Matrix (Fin d) (Fin d) ℝ) :
    Matrix (Fin d) (Fin d) ℝ →L[ℝ] Matrix (Fin d) (Fin d) ℝ :=
  LinearMap.toContinuousLinearMap
    { toFun := fun U => X⁻¹ * U * X⁻¹
      map_add' := by
        intro U V
        simp [Matrix.mul_add, Matrix.add_mul]
      map_smul' := by
        intro c U
        simp }

/-- Supplied inverse-Hessian action for the PSD log-det barrier: `V ↦ X V X`. -/
noncomputable def matrixLogDetInvHess {d : ℕ}
    (X : Matrix (Fin d) (Fin d) ℝ) :
    Matrix (Fin d) (Fin d) ℝ →L[ℝ] Matrix (Fin d) (Fin d) ℝ :=
  LinearMap.toContinuousLinearMap
    { toFun := fun V => X * V * X
      map_add' := by
        intro U V
        simp [Matrix.mul_add, Matrix.add_mul]
      map_smul' := by
        intro c U
        simp }

/--
Supplied mixed-third oracle for the PSD log-det barrier.  On symmetric tangent
directions this is the usual source expression
`-2 tr(X⁻¹ U X⁻¹ V X⁻¹ V)`.
-/
noncomputable def matrixLogDetThirdMixed {d : ℕ}
    (X U V : Matrix (Fin d) (Fin d) ℝ) : ℝ :=
  -2 * Matrix.trace (X⁻¹ * U * X⁻¹ * V * X⁻¹ * V)

@[simp] theorem matrixLogDetGrad_apply {d : ℕ}
    (X : Matrix (Fin d) (Fin d) ℝ) :
    matrixLogDetGrad X = -X⁻¹ := by
  rfl

@[simp] theorem matrixLogDetHess_apply {d : ℕ}
    (X U : Matrix (Fin d) (Fin d) ℝ) :
    matrixLogDetHess X U = X⁻¹ * U * X⁻¹ := by
  rfl

@[simp] theorem matrixLogDetInvHess_apply {d : ℕ}
    (X V : Matrix (Fin d) (Fin d) ℝ) :
    matrixLogDetInvHess X V = X * V * X := by
  rfl

/-- The real Frobenius trace pairing on matrices, `tr(AᵀB)`. -/
noncomputable def matrixFrobeniusInner
    {m n : Type*} [Fintype m] [Fintype n]
    (A B : Matrix m n ℝ) : ℝ :=
  Matrix.trace (Aᵀ * B)

@[simp] theorem matrixFrobeniusInner_eq_trace_transpose_mul
    {m n : Type*} [Fintype m] [Fintype n]
    (A B : Matrix m n ℝ) :
    matrixFrobeniusInner A B = Matrix.trace (Aᵀ * B) := by
  rfl

/-- The supplied log-det gradient has the expected Frobenius directional pairing. -/
theorem matrixLogDetGrad_frobeniusInner_eq_neg_trace_inv_mul_of_mem_posDefCone
    {d : ℕ} {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixFrobeniusInner (matrixLogDetGrad X) U =
      -Matrix.trace (X⁻¹ * U) := by
  have hXinv : X⁻¹.IsHermitian := hX.isHermitian.inv
  have hXinv_transpose : (X⁻¹)ᵀ = X⁻¹ := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial (X⁻¹)]
    exact hXinv.eq
  simp [matrixFrobeniusInner, matrixLogDetGrad, hXinv_transpose]

/--
First-order bridge from the actual source value `X ↦ -log det X` to the
supplied gradient oracle used by the self-concordance certificate.
-/
theorem matrixNegLogDetBarrier_line_hasDerivAt_zero_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    HasDerivAt (fun t : ℝ => matrixNegLogDetBarrier (X + t • U))
      (matrixFrobeniusInner (matrixLogDetGrad X) U) 0 := by
  have hderiv := neg_log_det_line_hasDerivAt_zero_of_mem_posDefCone
    (X := X) (U := U) hX
  rw [matrixLogDetGrad_frobeniusInner_eq_neg_trace_inv_mul_of_mem_posDefCone hX]
  simpa [matrixNegLogDetBarrier] using hderiv

/--
Directional derivative of matrix inversion along a line through a positive
definite matrix.  This reuses mathlib's Fréchet derivative of `Ring.inverse`;
the matrix nonsingular inverse is rewritten to the ring inverse only at the
API boundary.
-/
theorem matrix_ringInverse_line_hasDerivAt_zero_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    HasDerivAt (fun t : ℝ => Ring.inverse (X + t • U))
      (-(X⁻¹ * U * X⁻¹)) 0 := by
  let A := Matrix (Fin d) (Fin d) ℝ
  have hline :
      HasDerivAt (fun t : ℝ => X + t • U) U 0 := by
    convert (hasDerivAt_const (0 : ℝ) X).add
        ((hasDerivAt_id (0 : ℝ)).smul_const U)
      using 1
    simp
  let xunit : Aˣ := hX.isUnit.unit
  have hxunit : (xunit : A) = X := hX.isUnit.unit_spec
  have hinv :
      HasFDerivAt (fun Y : A => Ring.inverse Y)
        (-(ContinuousLinearMap.mulLeftRight ℝ A X⁻¹ X⁻¹)) X := by
    have hbase := hasFDerivAt_ringInverse (𝕜 := ℝ) (x := xunit)
    simpa [A, hxunit, Matrix.nonsing_inv_eq_ringInverse, Ring.inverse_unit]
      using hbase
  have hcomp := hinv.comp_hasDerivAt_of_eq (x := 0) hline (by simp [A])
  simpa [A, ContinuousLinearMap.mulLeftRight_apply] using hcomp

/--
Second-order source bridge for Chewi's PSD log-det barrier: along every line
through the positive-definite cone, the supplied gradient oracle has derivative
given by the supplied Hessian action.
-/
theorem matrixLogDetGrad_line_hasDerivAt_zero_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    HasDerivAt (fun t : ℝ => matrixLogDetGrad (X + t • U))
      (matrixLogDetHess X U) 0 := by
  have hinv :=
    matrix_ringInverse_line_hasDerivAt_zero_of_mem_posDefCone
      (X := X) (U := U) hX
  have hneg := hinv.neg
  simpa [matrixLogDetGrad, matrixLogDetHess, Matrix.nonsing_inv_eq_ringInverse] using hneg

/--
Product-rule layer for the third derivative bridge.  It differentiates the
matrix product that appears inside the Frobenius quadratic form of the supplied
log-det Hessian.
-/
theorem matrix_ringInverse_quadratic_product_line_hasDerivAt_zero_of_mem_posDefCone {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    HasDerivAt
      (fun t : ℝ =>
        Vᵀ * Ring.inverse (X + t • U) * V * Ring.inverse (X + t • U))
      ((Vᵀ * (-(X⁻¹ * U * X⁻¹)) * V) * X⁻¹ +
        (Vᵀ * X⁻¹ * V) * (-(X⁻¹ * U * X⁻¹))) 0 := by
  have hY :=
    matrix_ringInverse_line_hasDerivAt_zero_of_mem_posDefCone
      (X := X) (U := U) hX
  have hleft :
      HasDerivAt
        (fun t : ℝ => Vᵀ * Ring.inverse (X + t • U) * V)
        (Vᵀ * (-(X⁻¹ * U * X⁻¹)) * V) 0 := by
    exact (hY.const_mul Vᵀ).mul_const V
  simpa [Matrix.nonsing_inv_eq_ringInverse] using hleft.mul hY

/--
Scalar trace version of the product-rule layer for the log-det Hessian
quadratic form.
-/
theorem matrix_trace_ringInverse_quadratic_line_hasDerivAt_zero_of_mem_posDefCone {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    HasDerivAt
      (fun t : ℝ =>
        Matrix.trace
          (Vᵀ * Ring.inverse (X + t • U) * V *
            Ring.inverse (X + t • U)))
      (Matrix.trace
        ((Vᵀ * (-(X⁻¹ * U * X⁻¹)) * V) * X⁻¹ +
          (Vᵀ * X⁻¹ * V) * (-(X⁻¹ * U * X⁻¹)))) 0 := by
  let A := Matrix (Fin d) (Fin d) ℝ
  let trCLM : A →L[ℝ] ℝ :=
    LinearMap.toContinuousLinearMap
      (Matrix.traceLinearMap (n := Fin d) (α := ℝ) (R := ℝ))
  have hprod :=
    matrix_ringInverse_quadratic_product_line_hasDerivAt_zero_of_mem_posDefCone
      (X := X) (U := U) (V := V) hX
  have htrF :
      HasFDerivAt (fun M : A => trCLM M) trCLM
        (Vᵀ * X⁻¹ * V * X⁻¹) := by
    exact trCLM.hasFDerivAt
  have htrace := htrF.comp_hasDerivAt_of_eq (x := 0) hprod (by
    simp [Matrix.nonsing_inv_eq_ringInverse])
  simpa [A, trCLM] using htrace

/--
Trace algebra identifying the derivative of the Hessian quadratic trace with
the supplied mixed-third oracle.  The Hermitian hypothesis is exactly what
turns the Frobenius transpose on `V` into the source expression.
-/
theorem matrix_trace_hess_quadratic_derivative_eq_thirdMixed_of_isHermitian {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hV : V.IsHermitian) :
    Matrix.trace
        ((Vᵀ * (-(X⁻¹ * U * X⁻¹)) * V) * X⁻¹ +
          (Vᵀ * X⁻¹ * V) * (-(X⁻¹ * U * X⁻¹))) =
      matrixLogDetThirdMixed X U V := by
  have hVt : Vᵀ = V := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial V]
    exact hV.eq
  rw [matrixLogDetThirdMixed]
  have hterm1 :
      Matrix.trace (V * (X⁻¹ * (U * (X⁻¹ * (V * X⁻¹))))) =
        Matrix.trace (X⁻¹ * (U * (X⁻¹ * (V * (X⁻¹ * V))))) := by
    calc
      Matrix.trace (V * (X⁻¹ * (U * (X⁻¹ * (V * X⁻¹)))))
          = Matrix.trace (V * (X⁻¹ * U * X⁻¹ * V * X⁻¹)) := by
              simp [Matrix.mul_assoc]
      _ = Matrix.trace ((X⁻¹ * U * X⁻¹ * V * X⁻¹) * V) := by
              rw [Matrix.trace_mul_comm]
      _ = Matrix.trace (X⁻¹ * (U * (X⁻¹ * (V * (X⁻¹ * V))))) := by
              simp [Matrix.mul_assoc]
  have hterm2 :
      Matrix.trace (V * (X⁻¹ * (V * (X⁻¹ * (U * X⁻¹))))) =
        Matrix.trace (X⁻¹ * (U * (X⁻¹ * (V * (X⁻¹ * V))))) := by
    calc
      Matrix.trace (V * (X⁻¹ * (V * (X⁻¹ * (U * X⁻¹)))))
          = Matrix.trace ((V * X⁻¹ * V) * (X⁻¹ * U * X⁻¹)) := by
              simp [Matrix.mul_assoc]
      _ = Matrix.trace ((X⁻¹ * U * X⁻¹) * (V * X⁻¹ * V)) := by
              rw [Matrix.trace_mul_comm]
      _ = Matrix.trace (X⁻¹ * (U * (X⁻¹ * (V * (X⁻¹ * V))))) := by
              simp [Matrix.mul_assoc]
  let T := Matrix.trace (X⁻¹ * (U * (X⁻¹ * (V * (X⁻¹ * V)))))
  have hscalar : -T + -T = -(2 * T) := by
    ring
  simpa [hVt, Matrix.trace_add, Matrix.trace_neg, Matrix.mul_assoc,
    hterm1, hterm2, T] using hscalar

/--
Third-order source bridge for Chewi's PSD log-det barrier: the Hessian
quadratic form has the supplied mixed-third directional derivative along
positive-definite lines.
-/
theorem matrixLogDetHess_quadratic_frobenius_line_hasDerivAt_zero_of_mem_posDefCone
    {d : ℕ} {X U V : Matrix (Fin d) (Fin d) ℝ}
    (hX : X ∈ matrixPosDefCone d) (hV : V.IsHermitian) :
    HasDerivAt
      (fun t : ℝ => matrixFrobeniusInner V (matrixLogDetHess (X + t • U) V))
      (matrixLogDetThirdMixed X U V) 0 := by
  have htrace :=
    matrix_trace_ringInverse_quadratic_line_hasDerivAt_zero_of_mem_posDefCone
      (X := X) (U := U) (V := V) hX
  rw [matrix_trace_hess_quadratic_derivative_eq_thirdMixed_of_isHermitian
    (X := X) (U := U) (V := V) hV] at htrace
  simpa [matrixFrobeniusInner, matrixLogDetHess, Matrix.nonsing_inv_eq_ringInverse,
    Matrix.mul_assoc] using htrace

/-- The Frobenius trace pairing is symmetric over real matrices. -/
theorem matrixFrobeniusInner_comm
    {m n : Type*} [Fintype m] [Fintype n]
    (A B : Matrix m n ℝ) :
    matrixFrobeniusInner A B = matrixFrobeniusInner B A := by
  calc
    matrixFrobeniusInner A B = Matrix.trace ((Aᵀ * B)ᵀ) := by
      rw [matrixFrobeniusInner_eq_trace_transpose_mul, Matrix.trace_transpose]
    _ = matrixFrobeniusInner B A := by
      simp [matrixFrobeniusInner, Matrix.transpose_mul]

/-- The trace-square `tr(Aᵀ A)` is nonnegative for real matrices. -/
theorem matrixTrace_transpose_mul_self_nonneg
    {m n : Type*} [Fintype m] [Fintype n]
    (A : Matrix m n ℝ) :
    0 ≤ Matrix.trace (Aᵀ * A) := by
  rw [← Matrix.conjTranspose_eq_transpose_of_trivial A]
  exact (Matrix.posSemidef_conjTranspose_mul_self A).trace_nonneg

/-- The Frobenius trace pairing is nonnegative on the diagonal. -/
theorem matrixFrobeniusInner_self_nonneg
    {m n : Type*} [Fintype m] [Fintype n]
    (A : Matrix m n ℝ) :
    0 ≤ matrixFrobeniusInner A A := by
  exact matrixTrace_transpose_mul_self_nonneg A

/-- The trace-square `tr(Aᵀ A)` vanishes exactly when the real matrix is zero. -/
theorem matrixTrace_transpose_mul_self_eq_zero_iff
    {m n : Type*} [Fintype m] [Fintype n]
    (A : Matrix m n ℝ) :
    Matrix.trace (Aᵀ * A) = 0 ↔ A = 0 := by
  rw [← Matrix.conjTranspose_eq_transpose_of_trivial A]
  exact Matrix.trace_conjTranspose_mul_self_eq_zero_iff

/-- The Frobenius trace pairing vanishes on the diagonal exactly at zero. -/
theorem matrixFrobeniusInner_self_eq_zero_iff
    {m n : Type*} [Fintype m] [Fintype n]
    (A : Matrix m n ℝ) :
    matrixFrobeniusInner A A = 0 ↔ A = 0 := by
  exact matrixTrace_transpose_mul_self_eq_zero_iff A

/-- The Frobenius trace pairing is the sum of entrywise products. -/
theorem matrixFrobeniusInner_eq_sum_entries
    {m n : Type*} [Fintype m] [Fintype n]
    (A B : Matrix m n ℝ) :
    matrixFrobeniusInner A B = ∑ i, ∑ j, A i j * B i j := by
  rw [matrixFrobeniusInner]
  simp only [Matrix.trace, Matrix.diag_apply, Matrix.mul_apply, Matrix.transpose_apply]
  rw [Finset.sum_comm]

/-- Product-index form of the Frobenius trace pairing. -/
theorem matrixFrobeniusInner_eq_sum_product_entries
    {m n : Type*} [Fintype m] [Fintype n]
    (A B : Matrix m n ℝ) :
    matrixFrobeniusInner A B = ∑ p : m × n, A p.1 p.2 * B p.1 p.2 := by
  rw [matrixFrobeniusInner_eq_sum_entries]
  rw [Fintype.sum_prod_type]

/-- The square-root of the Frobenius self-pairing is mathlib's Frobenius norm. -/
theorem sqrt_matrixFrobeniusInner_self_eq_frobenius_norm
    {m n : Type*} [Fintype m] [Fintype n]
    (A : Matrix m n ℝ) :
    Real.sqrt (matrixFrobeniusInner A A) = ‖A‖ := by
  rw [Matrix.frobenius_norm_def, matrixFrobeniusInner_eq_sum_entries]
  simp [Real.sqrt_eq_rpow, Real.norm_eq_abs, pow_two]

/--
The Frobenius trace pairing as an inner-product-space structure on matrices.
This is deliberately a named non-instance: mathlib keeps matrix norms as
scoped choices, and this bridge lets source-facing matrix barrier theorems use
the generic Chewi self-concordance interfaces without making a global choice.
-/
@[reducible] noncomputable def matrixFrobeniusInnerProductSpace
    {m n : Type*} [Fintype m] [Fintype n] :
    InnerProductSpace ℝ (Matrix m n ℝ) where
  inner A B := matrixFrobeniusInner A B
  norm_sq_eq_re_inner A := by
    have hsqrt := sqrt_matrixFrobeniusInner_self_eq_frobenius_norm A
    have hnonneg := matrixFrobeniusInner_self_nonneg A
    calc
      ‖A‖ ^ (2 : ℕ) =
          (Real.sqrt (matrixFrobeniusInner A A)) ^ (2 : ℕ) := by
            rw [hsqrt]
      _ = matrixFrobeniusInner A A := by
            exact Real.sq_sqrt hnonneg
  conj_inner_symm A B := by
    change matrixFrobeniusInner B A = star (matrixFrobeniusInner A B)
    rw [matrixFrobeniusInner_comm]
    simp
  add_left A B C := by
    change matrixFrobeniusInner (A + B) C =
      matrixFrobeniusInner A C + matrixFrobeniusInner B C
    rw [matrixFrobeniusInner_eq_sum_entries]
    rw [matrixFrobeniusInner_eq_sum_entries]
    rw [matrixFrobeniusInner_eq_sum_entries]
    simp [add_mul, Finset.sum_add_distrib]
  smul_left A B r := by
    change matrixFrobeniusInner (r • A) B =
      star r * matrixFrobeniusInner A B
    rw [matrixFrobeniusInner_eq_sum_entries]
    rw [matrixFrobeniusInner_eq_sum_entries]
    simp [Finset.mul_sum, mul_assoc]

/-- Transposition preserves the square-root Frobenius self-pairing. -/
theorem sqrt_matrixFrobeniusInner_transpose_self_eq
    {m n : Type*} [Fintype m] [Fintype n] (A : Matrix m n ℝ) :
    Real.sqrt (matrixFrobeniusInner Aᵀ Aᵀ) =
      Real.sqrt (matrixFrobeniusInner A A) := by
  rw [sqrt_matrixFrobeniusInner_self_eq_frobenius_norm]
  rw [sqrt_matrixFrobeniusInner_self_eq_frobenius_norm]
  exact Matrix.frobenius_norm_transpose A

/-- Cauchy-Schwarz for the explicit Frobenius trace pairing. -/
theorem abs_matrixFrobeniusInner_le_sqrt_mul_sqrt
    {m n : Type*} [Fintype m] [Fintype n]
    (A B : Matrix m n ℝ) :
    |matrixFrobeniusInner A B| ≤
      Real.sqrt (matrixFrobeniusInner A A) *
        Real.sqrt (matrixFrobeniusInner B B) := by
  have hinner :
      matrixFrobeniusInner A B =
        ∑ p : m × n, A p.1 p.2 * B p.1 p.2 :=
    matrixFrobeniusInner_eq_sum_product_entries A B
  have hA :
      ∑ p : m × n, |A p.1 p.2| ^ (2 : ℕ) = matrixFrobeniusInner A A := by
    rw [matrixFrobeniusInner_eq_sum_product_entries]
    simp [pow_two]
  have hB :
      ∑ p : m × n, |B p.1 p.2| ^ (2 : ℕ) = matrixFrobeniusInner B B := by
    rw [matrixFrobeniusInner_eq_sum_product_entries]
    simp [pow_two]
  calc
    |matrixFrobeniusInner A B|
        = |∑ p : m × n, A p.1 p.2 * B p.1 p.2| := by rw [hinner]
    _ ≤ ∑ p : m × n, |A p.1 p.2 * B p.1 p.2| := by
          simpa using Finset.abs_sum_le_sum_abs
            (fun p : m × n => A p.1 p.2 * B p.1 p.2) Finset.univ
    _ = ∑ p : m × n, |A p.1 p.2| * |B p.1 p.2| := by
          simp [abs_mul]
    _ ≤ Real.sqrt (∑ p : m × n, |A p.1 p.2| ^ (2 : ℕ)) *
          Real.sqrt (∑ p : m × n, |B p.1 p.2| ^ (2 : ℕ)) := by
          simpa using Real.sum_mul_le_sqrt_mul_sqrt Finset.univ
            (fun p : m × n => |A p.1 p.2|) (fun p : m × n => |B p.1 p.2|)
    _ = Real.sqrt (matrixFrobeniusInner A A) *
          Real.sqrt (matrixFrobeniusInner B B) := by
          rw [hA, hB]

/-- Frobenius submultiplicativity in explicit trace-pairing form. -/
theorem sqrt_matrixFrobeniusInner_mul_self_le_sqrt_mul_sqrt
    {l m n : Type*} [Fintype l] [Fintype m] [Fintype n]
    (A : Matrix l m ℝ) (B : Matrix m n ℝ) :
    Real.sqrt (matrixFrobeniusInner (A * B) (A * B)) ≤
      Real.sqrt (matrixFrobeniusInner A A) *
        Real.sqrt (matrixFrobeniusInner B B) := by
  rw [sqrt_matrixFrobeniusInner_self_eq_frobenius_norm]
  rw [sqrt_matrixFrobeniusInner_self_eq_frobenius_norm]
  rw [sqrt_matrixFrobeniusInner_self_eq_frobenius_norm]
  exact Matrix.frobenius_norm_mul A B

/-- Squaring a matrix is bounded by the square of its Frobenius norm. -/
theorem sqrt_matrixFrobeniusInner_mul_self_le_matrixFrobeniusInner_self
    {n : Type*} [Fintype n] (B : Matrix n n ℝ) :
    Real.sqrt (matrixFrobeniusInner (B * B) (B * B)) ≤
      matrixFrobeniusInner B B := by
  have hmul := sqrt_matrixFrobeniusInner_mul_self_le_sqrt_mul_sqrt B B
  have hnonneg : 0 ≤ matrixFrobeniusInner B B :=
    matrixFrobeniusInner_self_nonneg B
  calc
    Real.sqrt (matrixFrobeniusInner (B * B) (B * B))
        ≤ Real.sqrt (matrixFrobeniusInner B B) *
            Real.sqrt (matrixFrobeniusInner B B) := hmul
    _ = matrixFrobeniusInner B B := by
          exact Real.mul_self_sqrt hnonneg

/--
Trace-Cauchy for the source mixed-third shape, valid for arbitrary real square
matrices.  The Hermitian-specialized theorem below is kept for older packets,
but the all-direction version is what connects the PSD log-det oracle to the
generic self-concordance interface.
-/
theorem abs_trace_mul_mul_le_sqrt_frobenius_mul_frobenius_all
    {n : Type*} [Fintype n] (A B : Matrix n n ℝ) :
    |Matrix.trace (A * B * B)| ≤
      Real.sqrt (matrixFrobeniusInner A A) * matrixFrobeniusInner B B := by
  have htrace :
      Matrix.trace (A * B * B) = matrixFrobeniusInner Aᵀ (B * B) := by
    simp [matrixFrobeniusInner, Matrix.mul_assoc]
  rw [htrace]
  have hcs := abs_matrixFrobeniusInner_le_sqrt_mul_sqrt Aᵀ (B * B)
  have htranspose := sqrt_matrixFrobeniusInner_transpose_self_eq A
  have hmul := sqrt_matrixFrobeniusInner_mul_self_le_matrixFrobeniusInner_self B
  calc
    |matrixFrobeniusInner Aᵀ (B * B)|
        ≤ Real.sqrt (matrixFrobeniusInner Aᵀ Aᵀ) *
            Real.sqrt (matrixFrobeniusInner (B * B) (B * B)) := hcs
    _ = Real.sqrt (matrixFrobeniusInner A A) *
            Real.sqrt (matrixFrobeniusInner (B * B) (B * B)) := by
          rw [htranspose]
    _ ≤ Real.sqrt (matrixFrobeniusInner A A) *
          matrixFrobeniusInner B B := by
          exact mul_le_mul_of_nonneg_left hmul (Real.sqrt_nonneg _)

/--
Trace-Cauchy for the source mixed-third shape, with the last factor controlled
by the Frobenius square of `B`.
-/
theorem abs_trace_mul_mul_le_sqrt_frobenius_mul_frobenius
    {n : Type*} [Fintype n]
    {A B : Matrix n n ℝ} (hA : A.IsHermitian) :
    |Matrix.trace (A * B * B)| ≤
      Real.sqrt (matrixFrobeniusInner A A) * matrixFrobeniusInner B B := by
  have hA_transpose : Aᵀ = A := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial A]
    exact hA.eq
  have htrace : Matrix.trace (A * B * B) = matrixFrobeniusInner A (B * B) := by
    simp [matrixFrobeniusInner, hA_transpose, Matrix.mul_assoc]
  rw [htrace]
  have hcs := abs_matrixFrobeniusInner_le_sqrt_mul_sqrt A (B * B)
  have hmul := sqrt_matrixFrobeniusInner_mul_self_le_matrixFrobeniusInner_self B
  exact hcs.trans (mul_le_mul_of_nonneg_left hmul (Real.sqrt_nonneg _))

/-- Cyclically rotate a four-factor matrix trace by one factor to the right. -/
theorem matrixTrace_mul_rotate_right_four
    {n : Type*} [Fintype n]
    (A B C D : Matrix n n ℝ) :
    Matrix.trace (A * B * C * D) = Matrix.trace (D * A * B * C) := by
  rw [show A * B * C * D = (A * B * C) * D by simp [Matrix.mul_assoc]]
  rw [Matrix.trace_mul_comm]
  simp [Matrix.mul_assoc]

/--
Square-root sandwich trace identity for Hermitian directions.  It rewrites the
PSD-weighted trace square as an ordinary Frobenius square.
-/
theorem matrixTrace_sqrt_sandwich_transpose_mul_self_eq_trace_quad
    {n : Type*} [Fintype n] [DecidableEq n]
    {A U : Matrix n n ℝ} (hA : A.PosSemidef) (hU : U.IsHermitian) :
    Matrix.trace (((CFC.sqrt A * U * CFC.sqrt A)ᵀ) *
        (CFC.sqrt A * U * CFC.sqrt A)) =
      Matrix.trace (U * A * U * A) := by
  let S : Matrix n n ℝ := CFC.sqrt A
  have hS_sq : S * S = A := by
    simpa [S, pow_two] using
      (CFC.sq_sqrt A (ha := hA.nonneg))
  have hS_psd : S.PosSemidef :=
    Matrix.nonneg_iff_posSemidef.mp (by simp [S])
  have hS_transpose : Sᵀ = S := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial S]
    exact hS_psd.isHermitian.eq
  have hU_transpose : Uᵀ = U := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial U]
    exact hU.eq
  calc
    Matrix.trace (((CFC.sqrt A * U * CFC.sqrt A)ᵀ) *
        (CFC.sqrt A * U * CFC.sqrt A))
        = Matrix.trace ((S * U * S) * (S * U * S)) := by
          change Matrix.trace (((S * U * S)ᵀ) * (S * U * S)) =
            Matrix.trace ((S * U * S) * (S * U * S))
          simp [Matrix.transpose_mul, hS_transpose, hU_transpose, Matrix.mul_assoc]
    _ = Matrix.trace (S * U * A * U * S) := by
          rw [show (S * U * S) * (S * U * S) = S * U * (S * S) * U * S by
            simp [Matrix.mul_assoc]]
          rw [hS_sq]
    _ = Matrix.trace (A * U * A * U) := by
          rw [show S * U * A * U * S = (S * U * A * U) * S by
            simp [Matrix.mul_assoc]]
          rw [Matrix.trace_mul_comm]
          rw [show S * (S * U * A * U) = (S * S) * U * A * U by
            simp [Matrix.mul_assoc]]
          rw [hS_sq]
    _ = Matrix.trace (U * A * U * A) := by
          rw [matrixTrace_mul_rotate_right_four A U A U]

/--
Square-root sandwich trace identity for arbitrary real directions.  This is
the raw-matrix version of the Hermitian source formula above, keeping the
transpose that is needed by the Frobenius pairing.
-/
theorem matrixTrace_sqrt_sandwich_transpose_mul_self_eq_trace_transpose_quad
    {n : Type*} [Fintype n] [DecidableEq n]
    {A U : Matrix n n ℝ} (hA : A.PosSemidef) :
    Matrix.trace (((CFC.sqrt A * U * CFC.sqrt A)ᵀ) *
        (CFC.sqrt A * U * CFC.sqrt A)) =
      Matrix.trace (Uᵀ * A * U * A) := by
  let S : Matrix n n ℝ := CFC.sqrt A
  have hS_sq : S * S = A := by
    simpa [S, pow_two] using
      (CFC.sq_sqrt A (ha := hA.nonneg))
  have hS_psd : S.PosSemidef :=
    Matrix.nonneg_iff_posSemidef.mp (by simp [S])
  have hS_transpose : Sᵀ = S := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial S]
    exact hS_psd.isHermitian.eq
  calc
    Matrix.trace (((CFC.sqrt A * U * CFC.sqrt A)ᵀ) *
        (CFC.sqrt A * U * CFC.sqrt A))
        = Matrix.trace ((S * Uᵀ * S) * (S * U * S)) := by
          change Matrix.trace (((S * U * S)ᵀ) * (S * U * S)) =
            Matrix.trace ((S * Uᵀ * S) * (S * U * S))
          simp [Matrix.transpose_mul, hS_transpose, Matrix.mul_assoc]
    _ = Matrix.trace (S * Uᵀ * A * U * S) := by
          rw [show (S * Uᵀ * S) * (S * U * S) =
              S * Uᵀ * (S * S) * U * S by
            simp [Matrix.mul_assoc]]
          rw [hS_sq]
    _ = Matrix.trace (A * Uᵀ * A * U) := by
          rw [show S * Uᵀ * A * U * S =
              (S * Uᵀ * A * U) * S by
            simp [Matrix.mul_assoc]]
          rw [Matrix.trace_mul_comm]
          rw [show S * (S * Uᵀ * A * U) =
              (S * S) * Uᵀ * A * U by
            simp [Matrix.mul_assoc]]
          rw [hS_sq]
    _ = Matrix.trace (Uᵀ * A * U * A) := by
          rw [← matrixTrace_mul_rotate_right_four Uᵀ A U A]

/-- A PSD-weighted Hermitian trace square is nonnegative. -/
theorem matrixTrace_quad_nonneg_of_posSemidef_of_isHermitian
    {n : Type*} [Fintype n] [DecidableEq n]
    {A U : Matrix n n ℝ} (hA : A.PosSemidef) (hU : U.IsHermitian) :
    0 ≤ Matrix.trace (U * A * U * A) := by
  rw [← matrixTrace_sqrt_sandwich_transpose_mul_self_eq_trace_quad hA hU]
  exact matrixTrace_transpose_mul_self_nonneg (CFC.sqrt A * U * CFC.sqrt A)

/--
Square-root sandwich trace identity for the mixed-third log-det trace.  This
turns `tr(A U A V A V)` into `tr((sqrt A U sqrt A)(sqrt A V sqrt A)^2)`.
-/
theorem matrixTrace_sqrt_sandwich_mul_square_eq_trace_mixed
    {n : Type*} [Fintype n] [DecidableEq n]
    {A U V : Matrix n n ℝ} (hA : A.PosSemidef) :
    Matrix.trace ((CFC.sqrt A * U * CFC.sqrt A) *
        (CFC.sqrt A * V * CFC.sqrt A) *
        (CFC.sqrt A * V * CFC.sqrt A)) =
      Matrix.trace (A * U * A * V * A * V) := by
  let S : Matrix n n ℝ := CFC.sqrt A
  have hS_sq : S * S = A := by
    simpa [S, pow_two] using
      (CFC.sq_sqrt A (ha := hA.nonneg))
  calc
    Matrix.trace ((CFC.sqrt A * U * CFC.sqrt A) *
        (CFC.sqrt A * V * CFC.sqrt A) *
        (CFC.sqrt A * V * CFC.sqrt A))
        = Matrix.trace ((S * U * S) * (S * V * S) * (S * V * S)) := by
          rfl
    _ = Matrix.trace (S * U * A * V * A * V * S) := by
          rw [show (S * U * S) * (S * V * S) * (S * V * S) =
              S * U * (S * S) * V * (S * S) * V * S by
            simp [Matrix.mul_assoc]]
          rw [hS_sq]
    _ = Matrix.trace (A * U * A * V * A * V) := by
          rw [show S * U * A * V * A * V * S =
              (S * U * A * V * A * V) * S by
            simp [Matrix.mul_assoc]]
          rw [Matrix.trace_mul_comm]
          rw [show S * (S * U * A * V * A * V) =
              (S * S) * U * A * V * A * V by
            simp [Matrix.mul_assoc]]
          rw [hS_sq]

/-- Positive-definite matrices supply the determinant unit needed by nonsingular inverse APIs. -/
theorem matrixPosDefCone_det_isUnit {d : ℕ}
    {X : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    IsUnit X.det :=
  (Matrix.isUnit_iff_isUnit_det (A := X)).mp hX.isUnit

/-- The supplied Hessian and inverse-Hessian oracles are right inverses on the PD cone. -/
theorem matrixLogDetHess_invHess_apply_of_mem_posDefCone {d : ℕ}
    {X V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixLogDetHess X (matrixLogDetInvHess X V) = V := by
  have hleft : X⁻¹ * X = 1 :=
    Matrix.nonsing_inv_mul X (matrixPosDefCone_det_isUnit hX)
  have hright : X * X⁻¹ = 1 :=
    Matrix.mul_nonsing_inv X (matrixPosDefCone_det_isUnit hX)
  simp [Matrix.mul_assoc, hright]
  rw [← Matrix.mul_assoc, hleft, Matrix.one_mul]

/-- The supplied inverse-Hessian and Hessian oracles are left inverses on the PD cone. -/
theorem matrixLogDetInvHess_hess_apply_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixLogDetInvHess X (matrixLogDetHess X U) = U := by
  have hleft : X⁻¹ * X = 1 :=
    Matrix.nonsing_inv_mul X (matrixPosDefCone_det_isUnit hX)
  have hright : X * X⁻¹ = 1 :=
    Matrix.mul_nonsing_inv X (matrixPosDefCone_det_isUnit hX)
  simp [Matrix.mul_assoc, hleft]
  rw [← Matrix.mul_assoc, hright, Matrix.one_mul]

/-- Applying the inverse-Hessian oracle to the gradient gives the source step `-X`. -/
theorem matrixLogDetInvHess_grad_eq_neg_self_of_mem_posDefCone {d : ℕ}
    {X : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixLogDetInvHess X (matrixLogDetGrad X) = -X := by
  have hright : X * X⁻¹ = 1 :=
    Matrix.mul_nonsing_inv X (matrixPosDefCone_det_isUnit hX)
  simp [matrixLogDetGrad, hright]

/-- Positive-definite matrices stay positive definite after nonsingular inversion. -/
theorem matrixPosDefCone_inv_mem {d : ℕ}
    {X : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    X⁻¹ ∈ matrixPosDefCone d :=
  hX.inv

/-- The supplied log-det gradient is Hermitian on the PD cone. -/
theorem matrixLogDetGrad_isHermitian_of_mem_posDefCone {d : ℕ}
    {X : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    (matrixLogDetGrad X).IsHermitian := by
  exact hX.isHermitian.inv.neg

/-- The supplied Hessian action preserves Hermitian tangent directions on the PD cone. -/
theorem matrixLogDetHess_apply_isHermitian_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hU : U.IsHermitian) :
    (matrixLogDetHess X U).IsHermitian := by
  have hXinv : X⁻¹.IsHermitian := hX.isHermitian.inv
  have hXinv_transpose : (X⁻¹)ᵀ = X⁻¹ := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial (X⁻¹)]
    exact hXinv.eq
  have hconj : ((X⁻¹)ᴴ * U * X⁻¹).IsHermitian :=
    Matrix.isHermitian_conjTranspose_mul_mul (X⁻¹) hU
  simpa [hXinv_transpose] using hconj

/-- The supplied inverse-Hessian action preserves Hermitian tangent directions on the PD cone. -/
theorem matrixLogDetInvHess_apply_isHermitian_of_mem_posDefCone {d : ℕ}
    {X V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hV : V.IsHermitian) :
    (matrixLogDetInvHess X V).IsHermitian := by
  have hX_transpose : Xᵀ = X := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial X]
    exact hX.isHermitian.eq
  have hconj : (Xᴴ * V * X).IsHermitian :=
    Matrix.isHermitian_conjTranspose_mul_mul X hV
  simpa [hX_transpose] using hconj

/-- The supplied Hessian action preserves PSD matrix directions on the PD cone. -/
theorem matrixLogDetHess_apply_posSemidef_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hU : U.PosSemidef) :
    (matrixLogDetHess X U).PosSemidef := by
  have hXinv : X⁻¹.IsHermitian := hX.isHermitian.inv
  have hXinv_transpose : (X⁻¹)ᵀ = X⁻¹ := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial (X⁻¹)]
    exact hXinv.eq
  have hconj : ((X⁻¹)ᴴ * U * X⁻¹).PosSemidef :=
    hU.conjTranspose_mul_mul_same (X⁻¹)
  simpa [hXinv_transpose] using hconj

/-- The supplied Hessian action preserves positive-definite matrix directions on the PD cone. -/
theorem matrixLogDetHess_apply_posDef_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hU : U.PosDef) :
    (matrixLogDetHess X U).PosDef := by
  have hXinv : X⁻¹.IsHermitian := hX.isHermitian.inv
  have hXinv_transpose : (X⁻¹)ᵀ = X⁻¹ := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial (X⁻¹)]
    exact hXinv.eq
  have hXinv_unit : IsUnit X⁻¹ :=
    Matrix.isUnit_nonsing_inv_iff.mpr hX.isUnit
  have hXinv_injective : Function.Injective (X⁻¹).mulVec :=
    Matrix.mulVec_injective_iff_isUnit.mpr hXinv_unit
  have hconj : ((X⁻¹)ᴴ * U * X⁻¹).PosDef :=
    hU.conjTranspose_mul_mul_same hXinv_injective
  simpa [hXinv_transpose] using hconj

/-- The supplied inverse-Hessian action preserves PSD matrix directions on the PD cone. -/
theorem matrixLogDetInvHess_apply_posSemidef_of_mem_posDefCone {d : ℕ}
    {X V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hV : V.PosSemidef) :
    (matrixLogDetInvHess X V).PosSemidef := by
  have hX_transpose : Xᵀ = X := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial X]
    exact hX.isHermitian.eq
  have hconj : (Xᴴ * V * X).PosSemidef :=
    hV.conjTranspose_mul_mul_same X
  simpa [hX_transpose] using hconj

/-- The supplied inverse-Hessian action preserves positive-definite directions on the PD cone. -/
theorem matrixLogDetInvHess_apply_posDef_of_mem_posDefCone {d : ℕ}
    {X V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hV : V.PosDef) :
    (matrixLogDetInvHess X V).PosDef := by
  have hX_transpose : Xᵀ = X := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial X]
    exact hX.isHermitian.eq
  have hX_injective : Function.Injective X.mulVec :=
    Matrix.mulVec_injective_iff_isUnit.mpr hX.isUnit
  have hconj : (Xᴴ * V * X).PosDef :=
    hV.conjTranspose_mul_mul_same hX_injective
  simpa [hX_transpose] using hconj

/-- The supplied log-det Hessian action is self-adjoint for the Frobenius trace pairing. -/
theorem matrixLogDetHess_frobenius_symm_of_mem_posDefCone {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixFrobeniusInner U (matrixLogDetHess X V) =
      matrixFrobeniusInner (matrixLogDetHess X U) V := by
  have hXinv : X⁻¹.IsHermitian := hX.isHermitian.inv
  have hXinv_transpose : (X⁻¹)ᵀ = X⁻¹ := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial (X⁻¹)]
    exact hXinv.eq
  calc
    matrixFrobeniusInner U (matrixLogDetHess X V)
        = Matrix.trace (Uᵀ * X⁻¹ * V * X⁻¹) := by
          simp [matrixFrobeniusInner, Matrix.mul_assoc]
    _ = Matrix.trace (X⁻¹ * Uᵀ * X⁻¹ * V) := by
          rw [matrixTrace_mul_rotate_right_four]
    _ = matrixFrobeniusInner (matrixLogDetHess X U) V := by
          simp [matrixFrobeniusInner, Matrix.transpose_mul, hXinv_transpose,
            Matrix.mul_assoc]

/-- The supplied log-det inverse-Hessian action is self-adjoint for the Frobenius trace pairing. -/
theorem matrixLogDetInvHess_frobenius_symm_of_mem_posDefCone {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixFrobeniusInner U (matrixLogDetInvHess X V) =
      matrixFrobeniusInner (matrixLogDetInvHess X U) V := by
  have hX_transpose : Xᵀ = X := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial X]
    exact hX.isHermitian.eq
  calc
    matrixFrobeniusInner U (matrixLogDetInvHess X V)
        = Matrix.trace (Uᵀ * X * V * X) := by
          simp [matrixFrobeniusInner, Matrix.mul_assoc]
    _ = Matrix.trace (X * Uᵀ * X * V) := by
          rw [matrixTrace_mul_rotate_right_four]
    _ = matrixFrobeniusInner (matrixLogDetInvHess X U) V := by
          simp [matrixFrobeniusInner, Matrix.transpose_mul, hX_transpose,
            Matrix.mul_assoc]

/-- Source trace formula for the Hessian quadratic form. -/
theorem matrixLogDetHess_quadratic_frobenius_eq_trace {d : ℕ}
    (X U : Matrix (Fin d) (Fin d) ℝ) :
    matrixFrobeniusInner U (matrixLogDetHess X U) =
      Matrix.trace (Uᵀ * X⁻¹ * U * X⁻¹) := by
  simp [matrixFrobeniusInner, Matrix.mul_assoc]

/-- Source trace formula for the Hessian quadratic form on Hermitian directions. -/
theorem matrixLogDetHess_quadratic_frobenius_eq_trace_of_isHermitian {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hU : U.IsHermitian) :
    matrixFrobeniusInner U (matrixLogDetHess X U) =
      Matrix.trace (U * X⁻¹ * U * X⁻¹) := by
  have hU_transpose : Uᵀ = U := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial U]
    exact hU.eq
  simp [matrixFrobeniusInner, Matrix.mul_assoc, hU_transpose]

/-- Source trace formula for the inverse-Hessian quadratic form. -/
theorem matrixLogDetInvHess_quadratic_frobenius_eq_trace {d : ℕ}
    (X U : Matrix (Fin d) (Fin d) ℝ) :
    matrixFrobeniusInner U (matrixLogDetInvHess X U) =
      Matrix.trace (Uᵀ * X * U * X) := by
  simp [matrixFrobeniusInner, Matrix.mul_assoc]

/-- Source trace formula for the inverse-Hessian quadratic form on Hermitian directions. -/
theorem matrixLogDetInvHess_quadratic_frobenius_eq_trace_of_isHermitian {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hU : U.IsHermitian) :
    matrixFrobeniusInner U (matrixLogDetInvHess X U) =
      Matrix.trace (U * X * U * X) := by
  have hU_transpose : Uᵀ = U := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial U]
    exact hU.eq
  simp [matrixFrobeniusInner, Matrix.mul_assoc, hU_transpose]

/-- The supplied log-det Hessian quadratic form is nonnegative on Hermitian directions. -/
theorem matrixLogDetHess_quadratic_frobenius_nonneg_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hU : U.IsHermitian) :
    0 ≤ matrixFrobeniusInner U (matrixLogDetHess X U) := by
  rw [matrixLogDetHess_quadratic_frobenius_eq_trace_of_isHermitian hU]
  exact matrixTrace_quad_nonneg_of_posSemidef_of_isHermitian hX.inv.posSemidef hU

/-- The supplied log-det inverse-Hessian quadratic form is nonnegative on Hermitian directions. -/
theorem matrixLogDetInvHess_quadratic_frobenius_nonneg_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hU : U.IsHermitian) :
    0 ≤ matrixFrobeniusInner U (matrixLogDetInvHess X U) := by
  rw [matrixLogDetInvHess_quadratic_frobenius_eq_trace_of_isHermitian hU]
  exact matrixTrace_quad_nonneg_of_posSemidef_of_isHermitian hX.posSemidef hU

/-- Source square-root sandwich trace formula for the Hessian quadratic form, all directions. -/
theorem matrixLogDetHess_quadratic_frobenius_eq_sqrt_sandwich_all {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixFrobeniusInner U (matrixLogDetHess X U) =
      matrixFrobeniusInner
        (CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹)
        (CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹) := by
  rw [matrixLogDetHess_quadratic_frobenius_eq_trace]
  rw [matrixFrobeniusInner_eq_trace_transpose_mul]
  rw [matrixTrace_sqrt_sandwich_transpose_mul_self_eq_trace_transpose_quad
    hX.inv.posSemidef]

/-- Source square-root sandwich trace formula for the inverse-Hessian quadratic form, all directions. -/
theorem matrixLogDetInvHess_quadratic_frobenius_eq_sqrt_sandwich_all {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixFrobeniusInner U (matrixLogDetInvHess X U) =
      matrixFrobeniusInner
        (CFC.sqrt X * U * CFC.sqrt X)
        (CFC.sqrt X * U * CFC.sqrt X) := by
  rw [matrixLogDetInvHess_quadratic_frobenius_eq_trace]
  rw [matrixFrobeniusInner_eq_trace_transpose_mul]
  rw [matrixTrace_sqrt_sandwich_transpose_mul_self_eq_trace_transpose_quad
    hX.posSemidef]

/-- The supplied log-det Hessian quadratic form is nonnegative on all real directions. -/
theorem matrixLogDetHess_quadratic_frobenius_nonneg_all_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    0 ≤ matrixFrobeniusInner U (matrixLogDetHess X U) := by
  rw [matrixLogDetHess_quadratic_frobenius_eq_sqrt_sandwich_all hX]
  exact matrixFrobeniusInner_self_nonneg _

/-- The supplied log-det inverse-Hessian quadratic form is nonnegative on all real directions. -/
theorem matrixLogDetInvHess_quadratic_frobenius_nonneg_all_of_mem_posDefCone {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    0 ≤ matrixFrobeniusInner U (matrixLogDetInvHess X U) := by
  rw [matrixLogDetInvHess_quadratic_frobenius_eq_sqrt_sandwich_all hX]
  exact matrixFrobeniusInner_self_nonneg _

/-- Source square-root sandwich trace formula for the Hessian quadratic form. -/
theorem matrixLogDetHess_quadratic_frobenius_eq_sqrt_sandwich {d : ℕ}
    {X U : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hU : U.IsHermitian) :
    matrixFrobeniusInner U (matrixLogDetHess X U) =
      matrixFrobeniusInner
        (CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹)
        (CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹) := by
  rw [matrixLogDetHess_quadratic_frobenius_eq_trace_of_isHermitian hU]
  rw [matrixFrobeniusInner_eq_trace_transpose_mul]
  rw [matrixTrace_sqrt_sandwich_transpose_mul_self_eq_trace_quad hX.inv.posSemidef hU]

/-- Source square-root sandwich trace formula for the log-det mixed-third oracle. -/
theorem matrixLogDetThirdMixed_eq_sqrt_sandwich_trace {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixLogDetThirdMixed X U V =
      -2 * Matrix.trace ((CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹) *
        (CFC.sqrt X⁻¹ * V * CFC.sqrt X⁻¹) *
        (CFC.sqrt X⁻¹ * V * CFC.sqrt X⁻¹)) := by
  rw [matrixLogDetThirdMixed]
  rw [matrixTrace_sqrt_sandwich_mul_square_eq_trace_mixed hX.inv.posSemidef]

/-- Absolute-value form of the square-root sandwich mixed-third trace formula. -/
theorem abs_matrixLogDetThirdMixed_eq_two_abs_sqrt_sandwich_trace {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    |matrixLogDetThirdMixed X U V| =
      2 * |Matrix.trace ((CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹) *
        (CFC.sqrt X⁻¹ * V * CFC.sqrt X⁻¹) *
        (CFC.sqrt X⁻¹ * V * CFC.sqrt X⁻¹))| := by
  rw [matrixLogDetThirdMixed_eq_sqrt_sandwich_trace hX]
  simp [abs_mul]

/--
Reduction of the log-det mixed-third bound to the remaining square-root
sandwich trace-Cauchy inequality.
-/
theorem matrixLogDetThirdMixed_abs_le_of_sqrt_sandwich_trace_bound {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hU : U.IsHermitian) (hV : V.IsHermitian)
    (htrace :
      |Matrix.trace ((CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹) *
        (CFC.sqrt X⁻¹ * V * CFC.sqrt X⁻¹) *
        (CFC.sqrt X⁻¹ * V * CFC.sqrt X⁻¹))| ≤
        Real.sqrt (matrixFrobeniusInner
          (CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹)
          (CFC.sqrt X⁻¹ * U * CFC.sqrt X⁻¹)) *
          matrixFrobeniusInner
            (CFC.sqrt X⁻¹ * V * CFC.sqrt X⁻¹)
            (CFC.sqrt X⁻¹ * V * CFC.sqrt X⁻¹)) :
    |matrixLogDetThirdMixed X U V| ≤
      2 * Real.sqrt (matrixFrobeniusInner U (matrixLogDetHess X U)) *
        matrixFrobeniusInner V (matrixLogDetHess X V) := by
  rw [abs_matrixLogDetThirdMixed_eq_two_abs_sqrt_sandwich_trace hX]
  rw [matrixLogDetHess_quadratic_frobenius_eq_sqrt_sandwich hX hU]
  rw [matrixLogDetHess_quadratic_frobenius_eq_sqrt_sandwich hX hV]
  nlinarith

/-- Chewi Example 13.14(2), supplied log-det mixed-third self-concordance bound. -/
theorem matrixLogDetThirdMixed_abs_le_of_mem_posDefCone {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d)
    (hU : U.IsHermitian) (hV : V.IsHermitian) :
    |matrixLogDetThirdMixed X U V| ≤
      2 * Real.sqrt (matrixFrobeniusInner U (matrixLogDetHess X U)) *
        matrixFrobeniusInner V (matrixLogDetHess X V) := by
  refine matrixLogDetThirdMixed_abs_le_of_sqrt_sandwich_trace_bound hX hU hV ?_
  let S : Matrix (Fin d) (Fin d) ℝ := CFC.sqrt X⁻¹
  have hS_psd : S.PosSemidef := by
    exact Matrix.nonneg_iff_posSemidef.mp (by simp [S])
  have hS_transpose : Sᵀ = S := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial S]
    exact hS_psd.isHermitian.eq
  have hBu : (S * U * S).IsHermitian := by
    have hconj : (Sᴴ * U * S).IsHermitian :=
      Matrix.isHermitian_conjTranspose_mul_mul S hU
    simpa [hS_transpose] using hconj
  simpa [S] using
    (abs_trace_mul_mul_le_sqrt_frobenius_mul_frobenius
      (A := S * U * S) (B := S * V * S) hBu)

/--
Chewi Example 13.14(2), supplied log-det mixed-third bound on all raw matrix
directions under the Frobenius pairing.
-/
theorem matrixLogDetThirdMixed_abs_le_of_mem_posDefCone_all {d : ℕ}
    {X U V : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    |matrixLogDetThirdMixed X U V| ≤
      2 * Real.sqrt (matrixFrobeniusInner U (matrixLogDetHess X U)) *
        matrixFrobeniusInner V (matrixLogDetHess X V) := by
  rw [abs_matrixLogDetThirdMixed_eq_two_abs_sqrt_sandwich_trace hX]
  rw [matrixLogDetHess_quadratic_frobenius_eq_sqrt_sandwich_all hX]
  rw [matrixLogDetHess_quadratic_frobenius_eq_sqrt_sandwich_all hX]
  let S : Matrix (Fin d) (Fin d) ℝ := CFC.sqrt X⁻¹
  have htrace :=
    abs_trace_mul_mul_le_sqrt_frobenius_mul_frobenius_all
      (A := S * U * S) (B := S * V * S)
  simpa [S, mul_assoc] using
    (show 2 * |Matrix.trace ((S * U * S) * (S * V * S) * (S * V * S))| ≤
        2 * (Real.sqrt (matrixFrobeniusInner (S * U * S) (S * U * S)) *
          matrixFrobeniusInner (S * V * S) (S * V * S)) by
      nlinarith)

/--
The source squared dual local norm of the PSD log-det gradient, expressed with
the Frobenius trace pairing, is the matrix dimension:
`tr((∇F(X))ᵀ H_X^{-1}∇F(X)) = d`.
-/
theorem matrixLogDetGrad_invHess_grad_frobenius_eq_card {d : ℕ}
    {X : Matrix (Fin d) (Fin d) ℝ} (hX : X ∈ matrixPosDefCone d) :
    matrixFrobeniusInner (matrixLogDetGrad X)
      (matrixLogDetInvHess X (matrixLogDetGrad X)) = (d : ℝ) := by
  have hXinv : X⁻¹.IsHermitian := hX.isHermitian.inv
  have hXinv_transpose : (X⁻¹)ᵀ = X⁻¹ := by
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial (X⁻¹)]
    exact hXinv.eq
  have hleft : X⁻¹ * X = 1 :=
    Matrix.nonsing_inv_mul X (matrixPosDefCone_det_isUnit hX)
  calc
    matrixFrobeniusInner (matrixLogDetGrad X)
        (matrixLogDetInvHess X (matrixLogDetGrad X))
        = Matrix.trace ((matrixLogDetGrad X)ᵀ *
            matrixLogDetInvHess X (matrixLogDetGrad X)) := by
          rfl
    _ = Matrix.trace ((-X⁻¹)ᵀ * (-X)) := by
          rw [matrixLogDetInvHess_grad_eq_neg_self_of_mem_posDefCone hX]
          rfl
    _ = Matrix.trace (X⁻¹ * X) := by
          simp [Matrix.transpose_neg, hXinv_transpose]
    _ = Matrix.trace (1 : Matrix (Fin d) (Fin d) ℝ) := by
          rw [hleft]
    _ = (d : ℝ) := by
          simp [Matrix.trace_one]

/--
Chewi Example 13.14(2), supplied-oracle mixed-third self-concordance of the
PSD log-det barrier under the named Frobenius matrix inner product.
-/
theorem matrixLogDet_mixedThirdSelfConcordantOn {d : ℕ} :
    letI : InnerProductSpace ℝ (Matrix (Fin d) (Fin d) ℝ) :=
      matrixFrobeniusInnerProductSpace
    MixedThirdSelfConcordantOn (matrixPosDefCone d)
      matrixLogDetHess matrixLogDetThirdMixed 1 := by
  letI : InnerProductSpace ℝ (Matrix (Fin d) (Fin d) ℝ) :=
    matrixFrobeniusInnerProductSpace
  refine ⟨by norm_num, ?_, ?_⟩
  · intro X hX U
    exact matrixLogDetHess_quadratic_frobenius_nonneg_all_of_mem_posDefCone hX
  · intro X hX U V
    have hbound :=
      matrixLogDetThirdMixed_abs_le_of_mem_posDefCone_all
        (X := X) (U := U) (V := V) hX
    have hV_nonneg :
        0 ≤ matrixFrobeniusInner V (matrixLogDetHess X V) :=
      matrixLogDetHess_quadratic_frobenius_nonneg_all_of_mem_posDefCone hX
    have hlocalV_sq :
        (localNorm matrixLogDetHess X V) ^ (2 : ℕ) =
          matrixFrobeniusInner V (matrixLogDetHess X V) := by
      simpa [localNorm] using Real.sq_sqrt hV_nonneg
    rw [hlocalV_sq]
    simpa [localNorm, one_mul, mul_assoc] using hbound

/--
Chewi Example 13.14(2), supplied-oracle self-concordant barrier certificate
for the PSD log-det barrier under the named Frobenius matrix inner product.
The remaining source gap for a literal textbook theorem is the analytic
identification of the supplied oracles with derivatives of `X ↦ -log det X`
and the interior of the PSD cone.
-/
theorem matrixLogDet_selfConcordantBarrierOn {d : ℕ} :
    letI : InnerProductSpace ℝ (Matrix (Fin d) (Fin d) ℝ) :=
      matrixFrobeniusInnerProductSpace
    SelfConcordantBarrierOn (matrixPosDefCone d)
      matrixLogDetHess matrixLogDetGrad matrixLogDetInvHess matrixLogDetThirdMixed
      1 (d : ℝ) := by
  letI : InnerProductSpace ℝ (Matrix (Fin d) (Fin d) ℝ) :=
    matrixFrobeniusInnerProductSpace
  refine
    { parameter_nonneg := ?_
      self_concordant := ?_
      invHess_nonneg := ?_
      gradient_bound := ?_ }
  · exact_mod_cast Nat.zero_le d
  · exact matrixLogDet_mixedThirdSelfConcordantOn
  · intro X hX V
    exact matrixLogDetInvHess_quadratic_frobenius_nonneg_all_of_mem_posDefCone hX
  · intro X hX
    change Real.sqrt (matrixFrobeniusInner (matrixLogDetGrad X)
        (matrixLogDetInvHess X (matrixLogDetGrad X))) ≤ Real.sqrt (d : ℝ)
    rw [matrixLogDetGrad_invHess_grad_frobenius_eq_card hX]

end Optimization
end StatInference
