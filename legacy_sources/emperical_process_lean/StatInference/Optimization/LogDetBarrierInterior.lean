import StatInference.Optimization.AppendixA
import StatInference.Optimization.LogDetBarrier

/-!
# Hermitian-subtype interior for the PSD log-det barrier

This module records the corrected topological surface for Chewi Example
13.14(2).  In the raw matrix space the PSD cone has empty interior; the
source identity is instead modeled in the Hermitian matrix subtype.  The
neighborhood argument uses the L2 operator norm, matching the perturbation
wrappers in `AppendixA`.
-/

namespace StatInference
namespace Optimization

open Filter
open scoped MatrixOrder Matrix.Norms.L2Operator

/--
A Hermitian matrix with a positive scalar Loewner lower bound is an interior
point of the PSD cone inside the Hermitian subtype.
-/
theorem matrixHermitianSubmodule_mem_interior_psd_of_scalar_lower
    {d : ℕ} [DecidableEq (Fin d)]
    {X : matrixHermitianSubmodule d} {α : ℝ} (hα : 0 < α)
    (hlower : α • (1 : Matrix (Fin d) (Fin d) ℝ) ≤
      (X : Matrix (Fin d) (Fin d) ℝ)) :
    X ∈ interior
      {Y : matrixHermitianSubmodule d |
        (Y : Matrix (Fin d) (Fin d) ℝ).PosSemidef} := by
  refine mem_interior.mpr
    ⟨Metric.ball X α, ?_, Metric.isOpen_ball, Metric.mem_ball_self hα⟩
  intro Y hYball
  change (Y : Matrix (Fin d) (Fin d) ℝ).PosSemidef
  have hdist :
      dist (Y : Matrix (Fin d) (Fin d) ℝ)
        (X : Matrix (Fin d) (Fin d) ℝ) < α := by
    simpa [Subtype.dist_eq] using hYball
  have hnorm_le :
      ‖(Y : Matrix (Fin d) (Fin d) ℝ) -
        (X : Matrix (Fin d) (Fin d) ℝ)‖ ≤ α := by
    exact le_of_lt (by simpa [dist_eq_norm] using hdist)
  have hlowerY :
      (α - α) • (1 : Matrix (Fin d) (Fin d) ℝ) ≤
        (Y : Matrix (Fin d) (Fin d) ℝ) :=
    chewiA5_loewner_lower_of_l2_opNorm_sub_le
      (A := (X : Matrix (Fin d) (Fin d) ℝ))
      (B := (Y : Matrix (Fin d) (Fin d) ℝ))
      X.property Y.property (le_of_lt hα) hlower hnorm_le
  have hnonneg :
      (0 : Matrix (Fin d) (Fin d) ℝ) ≤
        (Y : Matrix (Fin d) (Fin d) ℝ) := by
    simpa using hlowerY
  rwa [← Matrix.nonneg_iff_posSemidef]

/--
Positive definite matrices have a positive scalar identity lower bound.  This
is the compact-spectrum bridge needed to feed the Hermitian-subtype interior
ball lemma.
-/
theorem matrixPosDef_exists_pos_scalar_one_le
    {n : Type*} [Fintype n] [DecidableEq n] [Nonempty n]
    {X : Matrix n n ℝ} (hX : X.PosDef) :
    ∃ α : ℝ, 0 < α ∧ α • (1 : Matrix n n ℝ) ≤ X := by
  have hsp : IsStrictlyPositive X := hX.isStrictlyPositive
  obtain ⟨α, hα, hαle⟩ :=
    (CFC.exists_pos_algebraMap_le_iff
      (A := Matrix n n ℝ) (a := X) hsp.isSelfAdjoint).2
      (fun x hx => hsp.spectrum_pos hx)
  refine ⟨α, hα, ?_⟩
  simpa [Algebra.algebraMap_eq_smul_one] using hαle

/--
The positive-definite cone is contained in the interior of the PSD cone after
restricting the ambient space to Hermitian matrices.
-/
theorem matrixHermitianSubmodule_mem_interior_psd_of_posDef
    {d : ℕ} [DecidableEq (Fin d)] [Nonempty (Fin d)]
    {X : matrixHermitianSubmodule d}
    (hX : (X : Matrix (Fin d) (Fin d) ℝ).PosDef) :
    X ∈ interior
      {Y : matrixHermitianSubmodule d |
        (Y : Matrix (Fin d) (Fin d) ℝ).PosSemidef} := by
  obtain ⟨α, hα, hlower⟩ :=
    matrixPosDef_exists_pos_scalar_one_le
      (n := Fin d) (X := (X : Matrix (Fin d) (Fin d) ℝ)) hX
  exact
    matrixHermitianSubmodule_mem_interior_psd_of_scalar_lower
      (d := d) (X := X) hα hlower

/--
Every interior point of the PSD cone in the Hermitian subtype is positive
definite.  The proof turns an interior ball into a positive scalar Loewner
lower bound by testing the point `X - eta I` inside the ball.
-/
theorem matrixHermitianSubmodule_posDef_of_mem_interior_psd
    {d : ℕ} [DecidableEq (Fin d)]
    {X : matrixHermitianSubmodule d}
    (hX : X ∈ interior
      {Y : matrixHermitianSubmodule d |
        (Y : Matrix (Fin d) (Fin d) ℝ).PosSemidef}) :
    (X : Matrix (Fin d) (Fin d) ℝ).PosDef := by
  have hnhds :
      {Y : matrixHermitianSubmodule d |
        (Y : Matrix (Fin d) (Fin d) ℝ).PosSemidef} ∈ nhds X :=
    mem_interior_iff_mem_nhds.mp hX
  rcases Metric.mem_nhds_iff.mp hnhds with ⟨ε, hε_pos, hball⟩
  let I : Matrix (Fin d) (Fin d) ℝ := 1
  let η : ℝ := ε / (2 * (‖I‖ + 1))
  have hden_pos : 0 < 2 * (‖I‖ + 1) := by
    positivity
  have hη_pos : 0 < η := by
    positivity
  have hη_nonneg : 0 ≤ η := le_of_lt hη_pos
  let Y : matrixHermitianSubmodule d :=
    ⟨(X : Matrix (Fin d) (Fin d) ℝ) - η • I, by
      have hηI : (η • I : Matrix (Fin d) (Fin d) ℝ).IsHermitian :=
        Matrix.isHermitian_one.smul (by
          change star η = η
          simp)
      exact X.property.sub hηI⟩
  have hη_norm_lt :
      ‖η • I‖ < ε := by
    have hnormI_nonneg : 0 ≤ ‖I‖ := norm_nonneg I
    have hη_mul_norm_le : η * ‖I‖ ≤ η * (‖I‖ + 1) := by
      exact mul_le_mul_of_nonneg_left (by linarith) hη_nonneg
    have hη_mul_eq : η * (‖I‖ + 1) = ε / 2 := by
      dsimp [η]
      field_simp [hden_pos.ne']
    calc
      ‖η • I‖ = η * ‖I‖ := by
        rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg hη_nonneg]
      _ ≤ η * (‖I‖ + 1) := hη_mul_norm_le
      _ = ε / 2 := hη_mul_eq
      _ < ε := by linarith
  have hYball : Y ∈ Metric.ball X ε := by
    rw [Metric.mem_ball]
    have hdist :
        dist (Y : Matrix (Fin d) (Fin d) ℝ)
          (X : Matrix (Fin d) (Fin d) ℝ) < ε := by
      rw [dist_eq_norm]
      change ‖((X : Matrix (Fin d) (Fin d) ℝ) - η • I) -
        (X : Matrix (Fin d) (Fin d) ℝ)‖ < ε
      have hdiff :
          ((X : Matrix (Fin d) (Fin d) ℝ) - η • I) -
            (X : Matrix (Fin d) (Fin d) ℝ) = -(η • I) := by
        abel
      rw [hdiff]
      simpa [norm_neg] using hη_norm_lt
    simpa [Subtype.dist_eq] using hdist
  have hYpsd : (Y : Matrix (Fin d) (Fin d) ℝ).PosSemidef :=
    hball hYball
  have hlower :
      η • (1 : Matrix (Fin d) (Fin d) ℝ) ≤
        (X : Matrix (Fin d) (Fin d) ℝ) := by
    rw [Matrix.le_iff]
    simpa [I] using hYpsd
  exact chewiA5_posDef_of_pos_scalar_one_le X.property hη_pos hlower

/--
Chewi's identity `int S_+^d = S_{++}^d`, formalized in the Hermitian matrix
subtype rather than the raw matrix space.
-/
theorem interior_matrixHermitianSubmodule_psd_eq_posDef
    {d : ℕ} [DecidableEq (Fin d)] [Nonempty (Fin d)] :
    interior
      {Y : matrixHermitianSubmodule d |
        (Y : Matrix (Fin d) (Fin d) ℝ).PosSemidef} =
      {Y : matrixHermitianSubmodule d |
        (Y : Matrix (Fin d) (Fin d) ℝ).PosDef} := by
  ext X
  constructor
  · intro hX
    exact matrixHermitianSubmodule_posDef_of_mem_interior_psd hX
  · intro hX
    exact matrixHermitianSubmodule_mem_interior_psd_of_posDef hX

/--
Named L2-operator-topology proposition for Chewi's Hermitian-subtype identity
`int S_+^d = S_{++}^d`.  Keeping this as a named proposition lets source
bundles combine it with Frobenius-scoped self-concordance certificates without
mixing scoped matrix norm instances in one theorem type.
-/
def matrixHermitianPsdInteriorEqPosDefL2
    (d : ℕ) [DecidableEq (Fin d)] [Nonempty (Fin d)] : Prop :=
    interior
      {Y : matrixHermitianSubmodule d |
        (Y : Matrix (Fin d) (Fin d) ℝ).PosSemidef} =
      {Y : matrixHermitianSubmodule d |
        (Y : Matrix (Fin d) (Fin d) ℝ).PosDef}

/--
Named proposition wrapper for the L2-operator-topology PSD interior identity.
-/
theorem matrixHermitianPsdInteriorEqPosDefL2_holds
    {d : ℕ} [DecidableEq (Fin d)] [Nonempty (Fin d)] :
    matrixHermitianPsdInteriorEqPosDefL2 d :=
  interior_matrixHermitianSubmodule_psd_eq_posDef

end Optimization
end StatInference
