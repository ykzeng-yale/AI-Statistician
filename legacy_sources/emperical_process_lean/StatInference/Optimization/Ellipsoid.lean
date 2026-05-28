import Mathlib.Analysis.Matrix.Order
import StatInference.Optimization.CuttingPlane

/-!
# Chewi Chapter 6 ellipsoid-method layer

This module starts the source-shaped route for Chewi Lemma 6.20.  The exact
matrix update, half-space containment, and determinant/volume calculation are
kept as a step certificate for now; the finite shrink consequence and the link
back to the compiled center-of-gravity rate wrapper are proved here.
-/

namespace StatInference
namespace Optimization

open scoped InnerProductSpace MatrixOrder

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Source ellipsoid set `{z : <z-c, Q (z-c)> <= 1}`. -/
def ellipsoidSet (center : E) (invShape : E -> E) : Set E :=
  {z | inner ℝ (z - center) (invShape (z - center)) ≤ 1}

/-- Cutting half-space from the ellipsoid method display. -/
def ellipsoidCutHalfspace (p x : E) : Set E :=
  {z | inner ℝ p z ≤ inner ℝ p x}

/--
Displayed center update in Lemma 6.20, with `sigmaP` standing for
`Sigma_n p_n` and `quad` for `<p_n, Sigma_n p_n>`.
-/
noncomputable def ellipsoidCenterUpdate
    (d : ℕ) (x sigmaP : E) (quad : ℝ) : E :=
  x - (((d : ℝ) + 1)⁻¹ * (Real.sqrt quad)⁻¹) • sigmaP

/-- The source volume ratio from Chewi Lemma 6.20. -/
noncomputable def ellipsoidVolumeRatio (d : ℕ) : ℝ :=
  Real.sqrt
    ((((d : ℝ) - 1) / ((d : ℝ) + 1)) *
      ((((d : ℝ) ^ (2 : ℕ)) /
        (((d : ℝ) ^ (2 : ℕ)) - 1)) ^ d))

/-- Nonnegativity of the displayed ellipsoid volume ratio. -/
theorem ellipsoidVolumeRatio_nonneg (d : ℕ) :
    0 ≤ ellipsoidVolumeRatio d :=
  Real.sqrt_nonneg _

/--
Cleared scalar core of the central-cut containment in Chewi Lemma 6.20.

After reducing the current ellipsoid to the unit ball and aligning the cut with
the first coordinate, write a point as `(t, y)` with `t <= 0` and
`t^2 + ‖y‖^2 <= 1`.  The next ellipsoid has center shifted by
`-1 / (d + 1)` in the cut direction, squared radius `d^2 / (d + 1)^2` in that
direction, and squared radius `d^2 / (d^2 - 1)` in the orthogonal directions.
This theorem is the denominator-cleared inequality behind that containment.
-/
theorem chewi620_standard_cut_scalar_containment_cleared
    {d : ℕ} {t r2 : ℝ}
    (hd : 1 < d)
    (hr2_nonneg : 0 ≤ r2)
    (hball : t ^ (2 : ℕ) + r2 ≤ 1)
    (hcut : t ≤ 0) :
    (((d : ℝ) + 1) ^ (2 : ℕ)) *
        (t + (((d : ℝ) + 1)⁻¹)) ^ (2 : ℕ) +
      (((d : ℝ) ^ (2 : ℕ)) - 1) * r2 ≤
        (d : ℝ) ^ (2 : ℕ) := by
  have hd_pos_nat : 0 < d := by omega
  have hD_pos : 0 < (d : ℝ) := by exact_mod_cast hd_pos_nat
  have hD1_pos : 0 < (d : ℝ) + 1 := by positivity
  have hD1_ne : (d : ℝ) + 1 ≠ 0 := ne_of_gt hD1_pos
  have hcoef_nonneg : 0 ≤ (d : ℝ) ^ (2 : ℕ) - 1 := by
    have hD_ge_one : 1 ≤ (d : ℝ) := by exact_mod_cast le_of_lt hd
    nlinarith [sq_nonneg ((d : ℝ) - 1)]
  have ht_sq_le_one : t ^ (2 : ℕ) ≤ 1 := by nlinarith
  have ht_ge_neg_one : -1 ≤ t := by
    nlinarith [sq_nonneg (t + 1)]
  have hr2_le : r2 ≤ 1 - t ^ (2 : ℕ) := by nlinarith
  have hbound :
      (((d : ℝ) + 1) ^ (2 : ℕ)) *
          (t + (((d : ℝ) + 1)⁻¹)) ^ (2 : ℕ) +
        (((d : ℝ) ^ (2 : ℕ)) - 1) * r2 ≤
      (((d : ℝ) + 1) ^ (2 : ℕ)) *
          (t + (((d : ℝ) + 1)⁻¹)) ^ (2 : ℕ) +
        (((d : ℝ) ^ (2 : ℕ)) - 1) * (1 - t ^ (2 : ℕ)) := by
    have hmul :
        (((d : ℝ) ^ (2 : ℕ)) - 1) * r2 ≤
          (((d : ℝ) ^ (2 : ℕ)) - 1) * (1 - t ^ (2 : ℕ)) :=
      mul_le_mul_of_nonneg_left hr2_le hcoef_nonneg
    nlinarith
  have hidentity :
      (((d : ℝ) + 1) ^ (2 : ℕ)) *
          (t + (((d : ℝ) + 1)⁻¹)) ^ (2 : ℕ) +
        (((d : ℝ) ^ (2 : ℕ)) - 1) * (1 - t ^ (2 : ℕ)) =
      (d : ℝ) ^ (2 : ℕ) + 2 * (((d : ℝ) + 1) * (t * (t + 1))) := by
    field_simp [hD1_ne]
    ring
  have ht_prod_nonpos : t * (t + 1) ≤ 0 := by nlinarith
  calc
    (((d : ℝ) + 1) ^ (2 : ℕ)) *
        (t + (((d : ℝ) + 1)⁻¹)) ^ (2 : ℕ) +
      (((d : ℝ) ^ (2 : ℕ)) - 1) * r2
        ≤ (((d : ℝ) + 1) ^ (2 : ℕ)) *
            (t + (((d : ℝ) + 1)⁻¹)) ^ (2 : ℕ) +
          (((d : ℝ) ^ (2 : ℕ)) - 1) * (1 - t ^ (2 : ℕ)) := hbound
    _ = (d : ℝ) ^ (2 : ℕ) +
          2 * (((d : ℝ) + 1) * (t * (t + 1))) := hidentity
    _ ≤ (d : ℝ) ^ (2 : ℕ) := by nlinarith

/--
Normalized central-cut containment inequality in the source denominator form.
This is the scalar theorem to reuse when instantiating the half-space part of
`IsEllipsoidStepCertificate` for Chewi's displayed matrix update.
-/
theorem chewi620_standard_cut_scalar_containment
    {d : ℕ} {t r2 : ℝ}
    (hd : 1 < d)
    (hr2_nonneg : 0 ≤ r2)
    (hball : t ^ (2 : ℕ) + r2 ≤ 1)
    (hcut : t ≤ 0) :
    ((((d : ℝ) + 1) ^ (2 : ℕ)) / ((d : ℝ) ^ (2 : ℕ))) *
        (t + (((d : ℝ) + 1)⁻¹)) ^ (2 : ℕ) +
      ((((d : ℝ) ^ (2 : ℕ)) - 1) / ((d : ℝ) ^ (2 : ℕ))) * r2 ≤
        1 := by
  have hd_pos_nat : 0 < d := by omega
  have hD_pos : 0 < (d : ℝ) := by exact_mod_cast hd_pos_nat
  have hD_sq_pos : 0 < (d : ℝ) ^ (2 : ℕ) := sq_pos_of_pos hD_pos
  have hcleared :=
    chewi620_standard_cut_scalar_containment_cleared
      (d := d) (t := t) (r2 := r2) hd hr2_nonneg hball hcut
  rw [div_mul_eq_mul_div, div_mul_eq_mul_div]
  rw [← add_div]
  rwa [div_le_iff₀ hD_sq_pos, one_mul]

/--
Nonnegativity of the source square-root argument in Chewi Lemma 6.20's volume
ratio display.
-/
theorem chewi620_ellipsoidVolumeRatio_source_nonneg
    {d : ℕ} (hd : 1 < d) :
    0 ≤
      (((d : ℝ) - 1) / ((d : ℝ) + 1)) *
        ((((d : ℝ) ^ (2 : ℕ)) /
          (((d : ℝ) ^ (2 : ℕ)) - 1)) ^ d) := by
  have hD_gt_one : 1 < (d : ℝ) := by exact_mod_cast hd
  have hleft_nonneg : 0 ≤ ((d : ℝ) - 1) / ((d : ℝ) + 1) := by
    exact div_nonneg (by linarith) (by positivity)
  have hden_pos : 0 < (d : ℝ) ^ (2 : ℕ) - 1 := by
    nlinarith [sq_pos_of_pos (show 0 < (d : ℝ) - 1 by linarith)]
  have hbase_nonneg :
      0 ≤ ((d : ℝ) ^ (2 : ℕ)) /
        (((d : ℝ) ^ (2 : ℕ)) - 1) :=
    div_nonneg (sq_nonneg (d : ℝ)) hden_pos.le
  exact mul_nonneg hleft_nonneg (pow_nonneg hbase_nonneg d)

/--
Scalar determinant algebra for the normalized standard-cut ellipsoid.

In coordinates where the current ellipsoid is the unit ball and the cut is the
first coordinate half-space, the next ellipsoid has squared axis factor
`d^2 / (d + 1)^2` in the cut direction and
`d^2 / (d^2 - 1)` in each of the remaining `d - 1` directions.  Their product
is exactly Chewi's displayed square-root argument.
-/
theorem chewi620_standardCut_detRatio_eq_source
    {d : ℕ} (hd : 1 < d) :
    (((d : ℝ) ^ (2 : ℕ)) / (((d : ℝ) + 1) ^ (2 : ℕ))) *
        ((((d : ℝ) ^ (2 : ℕ)) /
          (((d : ℝ) ^ (2 : ℕ)) - 1)) ^ (d - 1)) =
      (((d : ℝ) - 1) / ((d : ℝ) + 1)) *
        ((((d : ℝ) ^ (2 : ℕ)) /
          (((d : ℝ) ^ (2 : ℕ)) - 1)) ^ d) := by
  have hD_gt_one : 1 < (d : ℝ) := by exact_mod_cast hd
  have hD1_ne : (d : ℝ) + 1 ≠ 0 := by positivity
  have hDsq_minus_ne : (d : ℝ) ^ (2 : ℕ) - 1 ≠ 0 := by
    nlinarith [sq_pos_of_pos (show 0 < (d : ℝ) - 1 by linarith)]
  let q : ℝ :=
    ((d : ℝ) ^ (2 : ℕ)) /
      (((d : ℝ) ^ (2 : ℕ)) - 1)
  have hpow :
      q ^ d = q ^ (d - 1) * q := by
    calc
      q ^ d = q ^ ((d - 1) + 1) := by
        congr 1
        omega
      _ = q ^ (d - 1) * q := by
        rw [pow_succ]
  have hcoef :
      ((d : ℝ) ^ (2 : ℕ)) / (((d : ℝ) + 1) ^ (2 : ℕ)) =
        (((d : ℝ) - 1) / ((d : ℝ) + 1)) * q := by
    dsimp [q]
    field_simp [hD1_ne, hDsq_minus_ne]
    ring
  change
    (((d : ℝ) ^ (2 : ℕ)) / (((d : ℝ) + 1) ^ (2 : ℕ))) *
        q ^ (d - 1) =
      (((d : ℝ) - 1) / ((d : ℝ) + 1)) * q ^ d
  rw [hpow, hcoef]
  ring

/--
Chewi Lemma 6.20's displayed `ellipsoidVolumeRatio` is the square root of the
standard-cut determinant ratio.
-/
theorem chewi620_ellipsoidVolumeRatio_sq_eq_standardCut_detRatio
    {d : ℕ} (hd : 1 < d) :
    ellipsoidVolumeRatio d ^ (2 : ℕ) =
      (((d : ℝ) ^ (2 : ℕ)) / (((d : ℝ) + 1) ^ (2 : ℕ))) *
        ((((d : ℝ) ^ (2 : ℕ)) /
          (((d : ℝ) ^ (2 : ℕ)) - 1)) ^ (d - 1)) := by
  rw [ellipsoidVolumeRatio]
  rw [Real.sq_sqrt (chewi620_ellipsoidVolumeRatio_source_nonneg hd)]
  exact (chewi620_standardCut_detRatio_eq_source (d := d) hd).symm

/-- Center of the normalized standard central-cut ellipsoid. -/
noncomputable def chewi620StandardCutCenter (d : ℕ) (u : E) : E :=
  -(((d : ℝ) + 1)⁻¹) • u

/--
Inverse-shape operator for the normalized standard central-cut ellipsoid.  The
direction `u` is the cut direction; the theorem below assumes `‖u‖ = 1`.
-/
noncomputable def chewi620StandardCutInvShape (d : ℕ) (u : E) (z : E) : E :=
  (((((d : ℝ) + 1) ^ (2 : ℕ)) / ((d : ℝ) ^ (2 : ℕ))) *
      inner ℝ u z) • u +
    ((((d : ℝ) ^ (2 : ℕ) - 1) / ((d : ℝ) ^ (2 : ℕ))) •
      (z - (inner ℝ u z) • u))

/--
Forward-shape operator for the normalized standard central-cut ellipsoid.  This
is the normalized-coordinate version of Chewi's displayed `Σ_{n+1}` update.
-/
noncomputable def chewi620StandardCutForwardShape
    (d : ℕ) (u : E) (z : E) : E :=
  ((((d : ℝ) ^ (2 : ℕ)) / (((d : ℝ) ^ (2 : ℕ)) - 1)) •
    (z - (((2 : ℝ) / ((d : ℝ) + 1)) * inner ℝ u z) • u))

/--
In normalized coordinates, Chewi's standard-cut forward-shape update is a left
inverse of the normalized next inverse-shape.
-/
theorem chewi620_standardCutForwardShape_left_inverse
    {d : ℕ} (hd : 1 < d) {u x : E} (hu_norm : ‖u‖ = 1) :
    chewi620StandardCutForwardShape d u
      (chewi620StandardCutInvShape d u x) = x := by
  let t : ℝ := inner ℝ u x
  let a : ℝ := (((d : ℝ) + 1) ^ (2 : ℕ)) / ((d : ℝ) ^ (2 : ℕ))
  let b : ℝ := (((d : ℝ) ^ (2 : ℕ) - 1) / ((d : ℝ) ^ (2 : ℕ)))
  let c : ℝ := (2 : ℝ) / ((d : ℝ) + 1)
  let s : ℝ := ((d : ℝ) ^ (2 : ℕ)) / (((d : ℝ) ^ (2 : ℕ)) - 1)
  have hD_pos : 0 < (d : ℝ) := by
    have hd_pos_nat : 0 < d := by omega
    exact_mod_cast hd_pos_nat
  have hD_ne : (d : ℝ) ≠ 0 := ne_of_gt hD_pos
  have hD1_ne : (d : ℝ) + 1 ≠ 0 := by positivity
  have hDsq_ne : (d : ℝ) ^ (2 : ℕ) ≠ 0 := pow_ne_zero _ hD_ne
  have hDsq_minus_ne : (d : ℝ) ^ (2 : ℕ) - 1 ≠ 0 := by
    have hD_gt_one : 1 < (d : ℝ) := by exact_mod_cast hd
    nlinarith [sq_pos_of_pos (show 0 < (d : ℝ) - 1 by linarith)]
  have huu : inner ℝ u u = 1 := by
    rw [real_inner_self_eq_norm_sq, hu_norm]
    norm_num
  have hshape :
      chewi620StandardCutInvShape d u x =
        b • x + ((a - b) * t) • u := by
    dsimp [chewi620StandardCutInvShape, a, b, t]
    module
  have hinner_shape :
      inner ℝ u (chewi620StandardCutInvShape d u x) = a * t := by
    rw [hshape]
    simp [inner_add_right, inner_smul_right, hu_norm, t]
    ring_nf
  have hinner_shape_expanded :
      inner ℝ u (b • x + ((a - b) * t) • u) = a * t := by
    rw [← hshape]
    exact hinner_shape
  have hsb : s * b = 1 := by
    dsimp [s, b]
    field_simp [hDsq_ne, hDsq_minus_ne]
  have hcoef :
      (a - b) * t - c * (a * t) = 0 := by
    have hcoef0 : (a - b) - c * a = 0 := by
      dsimp [a, b, c]
      field_simp [hDsq_ne, hDsq_minus_ne, hD1_ne]
      ring
    calc
      (a - b) * t - c * (a * t) = ((a - b) - c * a) * t := by
        ring
      _ = 0 := by
        rw [hcoef0]
        ring
  calc
    chewi620StandardCutForwardShape d u
        (chewi620StandardCutInvShape d u x)
        = s • (chewi620StandardCutInvShape d u x -
            (c * inner ℝ u (chewi620StandardCutInvShape d u x)) • u) := by
      dsimp [chewi620StandardCutForwardShape, s, c]
    _ = s •
          (b • x + (((a - b) * t) - c * (a * t)) • u) := by
      rw [hshape, hinner_shape_expanded]
      module
    _ = x := by
      rw [hcoef]
      simp
      rw [smul_smul, hsb, one_smul]

/--
Pythagoras for the decomposition into a unit direction and its orthogonal
residual.  This is the coordinate-free replacement for writing
`‖z‖² = t² + ‖y‖²` in the normalized Lemma 6.20 proof.
-/
theorem chewi620_norm_sq_eq_inner_sq_add_orthogonal_sq
    {u z : E} (hu_norm : ‖u‖ = 1) :
    ‖z‖ ^ (2 : ℕ) =
      (inner ℝ u z) ^ (2 : ℕ) +
        ‖z - (inner ℝ u z) • u‖ ^ (2 : ℕ) := by
  let t : ℝ := inner ℝ u z
  have hres :
      ‖z - t • u‖ ^ (2 : ℕ) =
        ‖z‖ ^ (2 : ℕ) - t ^ (2 : ℕ) := by
    rw [norm_sub_sq_real, real_inner_smul_right, norm_smul, hu_norm, mul_one,
      Real.norm_eq_abs, sq_abs]
    have hzu : inner ℝ z u = t := by
      dsimp [t]
      rw [real_inner_comm]
    rw [hzu]
    ring
  change
    ‖z‖ ^ (2 : ℕ) =
      t ^ (2 : ℕ) + ‖z - t • u‖ ^ (2 : ℕ)
  nlinarith

/-- Quadratic form of the normalized standard-cut inverse shape. -/
theorem chewi620_standardCutInvShape_quadratic
    {d : ℕ} {u z : E} (hu_norm : ‖u‖ = 1) :
    inner ℝ z (chewi620StandardCutInvShape d u z) =
      ((((d : ℝ) + 1) ^ (2 : ℕ)) / ((d : ℝ) ^ (2 : ℕ))) *
          (inner ℝ u z) ^ (2 : ℕ) +
        ((((d : ℝ) ^ (2 : ℕ) - 1) / ((d : ℝ) ^ (2 : ℕ))) *
          ‖z - (inner ℝ u z) • u‖ ^ (2 : ℕ)) := by
  let t : ℝ := inner ℝ u z
  let q : E := z - t • u
  let a : ℝ := (((d : ℝ) + 1) ^ (2 : ℕ)) / ((d : ℝ) ^ (2 : ℕ))
  let b : ℝ := (((d : ℝ) ^ (2 : ℕ) - 1) / ((d : ℝ) ^ (2 : ℕ)))
  have huu : inner ℝ u u = 1 := by
    rw [real_inner_self_eq_norm_sq, hu_norm]
    norm_num
  have horth_uq : inner ℝ u q = 0 := by
    dsimp [q, t]
    rw [inner_sub_right, real_inner_smul_right, huu]
    ring
  have horth_qu : inner ℝ q u = 0 := by
    simpa [real_inner_comm q u] using horth_uq
  have hz_decomp : z = t • u + q := by
    dsimp [q, t]
    module
  change inner ℝ z (((a * t) • u) + b • q) =
      a * t ^ (2 : ℕ) + b * ‖q‖ ^ (2 : ℕ)
  rw [hz_decomp]
  simp [inner_add_left, inner_add_right, inner_smul_left, inner_smul_right,
    horth_uq, horth_qu, hu_norm]
  ring

/--
Coordinate-free normalized half-space containment for Chewi Lemma 6.20.  This
is the affine-normalized version of the ellipsoid update before inserting a
concrete matrix square-root/change-of-variables for `Σ_n`.
-/
theorem chewi620_standardCut_halfspace_subset
    {d : ℕ} {u : E} (hd : 1 < d) (hu_norm : ‖u‖ = 1) :
    ellipsoidSet (0 : E) (fun z => z) ∩
        ellipsoidCutHalfspace u (0 : E) ⊆
      ellipsoidSet (chewi620StandardCutCenter d u)
        (chewi620StandardCutInvShape d u) := by
  intro z hz
  let t : ℝ := inner ℝ u z
  let r2 : ℝ := ‖z - t • u‖ ^ (2 : ℕ)
  have hz_ball : ‖z‖ ^ (2 : ℕ) ≤ 1 := by
    simpa [ellipsoidSet, real_inner_self_eq_norm_sq] using hz.1
  have hz_cut : t ≤ 0 := by
    simpa [ellipsoidCutHalfspace, t] using hz.2
  have hr2_nonneg : 0 ≤ r2 := sq_nonneg _
  have hpyth :
      ‖z‖ ^ (2 : ℕ) = t ^ (2 : ℕ) + r2 := by
    simpa [t, r2] using
      chewi620_norm_sq_eq_inner_sq_add_orthogonal_sq
        (u := u) (z := z) hu_norm
  have hball : t ^ (2 : ℕ) + r2 ≤ 1 := by
    nlinarith
  have hscalar :
      ((((d : ℝ) + 1) ^ (2 : ℕ)) / ((d : ℝ) ^ (2 : ℕ))) *
          (t + (((d : ℝ) + 1)⁻¹)) ^ (2 : ℕ) +
        ((((d : ℝ) ^ (2 : ℕ)) - 1) / ((d : ℝ) ^ (2 : ℕ))) * r2 ≤
          1 :=
    chewi620_standard_cut_scalar_containment
      (d := d) (t := t) (r2 := r2) hd hr2_nonneg hball hz_cut
  have hcenter_sub :
      z - chewi620StandardCutCenter d u =
        z + (((d : ℝ) + 1)⁻¹) • u := by
    simp [chewi620StandardCutCenter, sub_eq_add_neg]
  have hinner_shift :
      inner ℝ u (z - chewi620StandardCutCenter d u) =
        t + (((d : ℝ) + 1)⁻¹) := by
    rw [hcenter_sub]
    simp [t, inner_add_right, real_inner_smul_right, hu_norm]
  have horth_shift :
      (z - chewi620StandardCutCenter d u) -
          inner ℝ u (z - chewi620StandardCutCenter d u) • u =
        z - t • u := by
    rw [hinner_shift, hcenter_sub]
    module
  have hquad :=
    chewi620_standardCutInvShape_quadratic
      (d := d) (u := u) (z := z - chewi620StandardCutCenter d u) hu_norm
  change
    inner ℝ (z - chewi620StandardCutCenter d u)
        (chewi620StandardCutInvShape d u
          (z - chewi620StandardCutCenter d u)) ≤ 1
  rw [hquad, horth_shift, hinner_shift]
  simpa [r2] using hscalar

/--
Affine transport of the normalized half-space containment in Chewi Lemma 6.20.

The map `toStd` is the still-supplied normalization sending the current
ellipsoid to the unit ball and the current cut to the normalized cut direction
`u`.  This theorem isolates the exact matrix work left for the displayed
`Σ_n` update: prove the three quadratic/cut identities below, then the
containment part of the ellipsoid step follows from
`chewi620_standardCut_halfspace_subset`.
-/
theorem chewi620_affineTransport_halfspace_subset_of_quadratic
    {d : ℕ} {center nextCenter : E} {invShape nextInvShape : E -> E}
    {p u : E} {toStd : E -> E} {scale : ℝ}
    (hd : 1 < d) (hu_norm : ‖u‖ = 1) (hscale_pos : 0 < scale)
    (hcurrent :
      ∀ z,
        inner ℝ (z - center) (invShape (z - center)) =
          ‖toStd (z - center)‖ ^ (2 : ℕ))
    (hcut :
      ∀ z,
        inner ℝ u (toStd (z - center)) =
          scale * (inner ℝ p z - inner ℝ p center))
    (hnext :
      ∀ z,
        inner ℝ (z - nextCenter) (nextInvShape (z - nextCenter)) =
          inner ℝ
            (toStd (z - center) - chewi620StandardCutCenter d u)
            (chewi620StandardCutInvShape d u
              (toStd (z - center) - chewi620StandardCutCenter d u))) :
    ellipsoidSet center invShape ∩ ellipsoidCutHalfspace p center ⊆
      ellipsoidSet nextCenter nextInvShape := by
  intro z hz
  have hz_ball_sq : ‖toStd (z - center)‖ ^ (2 : ℕ) ≤ 1 := by
    have hz_current := hz.1
    change inner ℝ (z - center) (invShape (z - center)) ≤ 1 at hz_current
    rwa [hcurrent z] at hz_current
  have hz_ball :
      toStd (z - center) ∈ ellipsoidSet (0 : E) (fun w => w) := by
    simpa [ellipsoidSet, real_inner_self_eq_norm_sq] using hz_ball_sq
  have hdiff_nonpos : inner ℝ p z - inner ℝ p center ≤ 0 := by
    have hz_cut_original := hz.2
    change inner ℝ p z ≤ inner ℝ p center at hz_cut_original
    exact sub_nonpos.mpr hz_cut_original
  have hz_cut :
      toStd (z - center) ∈ ellipsoidCutHalfspace u (0 : E) := by
    have hscaled_nonpos :
        scale * (inner ℝ p z - inner ℝ p center) ≤ 0 :=
      mul_nonpos_of_nonneg_of_nonpos hscale_pos.le hdiff_nonpos
    change inner ℝ u (toStd (z - center)) ≤ inner ℝ u (0 : E)
    rw [hcut z]
    simpa using hscaled_nonpos
  have hz_std :
      toStd (z - center) ∈
        ellipsoidSet (chewi620StandardCutCenter d u)
          (chewi620StandardCutInvShape d u) :=
    (chewi620_standardCut_halfspace_subset
      (d := d) (u := u) hd hu_norm) ⟨hz_ball, hz_cut⟩
  simpa [ellipsoidSet, hnext z] using hz_std

/--
Source-shaped certificate for one Lemma 6.20 ellipsoid step: the next
ellipsoid contains the half-space cut and has the displayed volume ratio.
-/
def IsEllipsoidStepCertificate
    (center nextCenter : E) (invShape nextInvShape : E -> E)
    (p : E) (vol volNext ratio : ℝ) : Prop :=
  ellipsoidSet center invShape ∩ ellipsoidCutHalfspace p center ⊆
      ellipsoidSet nextCenter nextInvShape ∧
    volNext ≤ ratio * vol

theorem IsEllipsoidStepCertificate.halfspace_subset
    {center nextCenter : E} {invShape nextInvShape : E -> E}
    {p : E} {vol volNext ratio : ℝ}
    (h : IsEllipsoidStepCertificate center nextCenter invShape nextInvShape
      p vol volNext ratio) :
    ellipsoidSet center invShape ∩ ellipsoidCutHalfspace p center ⊆
      ellipsoidSet nextCenter nextInvShape :=
  h.1

theorem IsEllipsoidStepCertificate.volume_le
    {center nextCenter : E} {invShape nextInvShape : E -> E}
    {p : E} {vol volNext ratio : ℝ}
    (h : IsEllipsoidStepCertificate center nextCenter invShape nextInvShape
      p vol volNext ratio) :
    volNext ≤ ratio * vol :=
  h.2

/--
Affine-transport instantiation of the full supplied ellipsoid-step certificate.
The remaining volume hypothesis is exactly the determinant/measure-scaling
part of Chewi Lemma 6.20; the containment part is discharged by
`chewi620_affineTransport_halfspace_subset_of_quadratic`.
-/
theorem chewi620_affineTransport_stepCertificate_of_quadratic
    {d : ℕ} {center nextCenter : E} {invShape nextInvShape : E -> E}
    {p u : E} {toStd : E -> E} {scale vol volNext : ℝ}
    (hd : 1 < d) (hu_norm : ‖u‖ = 1) (hscale_pos : 0 < scale)
    (hcurrent :
      ∀ z,
        inner ℝ (z - center) (invShape (z - center)) =
          ‖toStd (z - center)‖ ^ (2 : ℕ))
    (hcut :
      ∀ z,
        inner ℝ u (toStd (z - center)) =
          scale * (inner ℝ p z - inner ℝ p center))
    (hnext :
      ∀ z,
        inner ℝ (z - nextCenter) (nextInvShape (z - nextCenter)) =
          inner ℝ
            (toStd (z - center) - chewi620StandardCutCenter d u)
            (chewi620StandardCutInvShape d u
              (toStd (z - center) - chewi620StandardCutCenter d u)))
    (hvolume : volNext ≤ ellipsoidVolumeRatio d * vol) :
    IsEllipsoidStepCertificate center nextCenter invShape nextInvShape
      p vol volNext (ellipsoidVolumeRatio d) := by
  exact ⟨
    chewi620_affineTransport_halfspace_subset_of_quadratic
      (d := d) (center := center) (nextCenter := nextCenter)
      (invShape := invShape) (nextInvShape := nextInvShape)
      (p := p) (u := u) (toStd := toStd) (scale := scale)
      hd hu_norm hscale_pos hcurrent hcut hnext,
    hvolume⟩

/--
Raw adjoint identity for the square-root normalization in Chewi Lemma 6.20.

When `T` is the symmetric square-root factor `Σ^{1/2}`, its inverse
`T.symm` is the normalization map `Σ^{-1/2}`.  This proves the source identity
`<Σ^{1/2}p, Σ^{-1/2}(z-center)> = <p,z> - <p,center>` from symmetry and
inverse cancellation alone.
-/
theorem chewi620_rawAdjointIdentity_of_symmetric_inverse
    {T : E ≃ₗ[ℝ] E}
    (hT_symm : T.IsSymmetric)
    (p center z : E) :
    inner ℝ (T p) (T.symm (z - center)) =
      inner ℝ p z - inner ℝ p center := by
  calc
    inner ℝ (T p) (T.symm (z - center)) =
        inner ℝ p (T (T.symm (z - center))) := by
      simpa using hT_symm p (T.symm (z - center))
    _ = inner ℝ p (z - center) := by
      simp
    _ = inner ℝ p z - inner ℝ p center := by
      rw [inner_sub_right]

/--
Current inverse-shape obtained by pulling back the unit-ball quadratic through
the normalization map `T.symm`, intended as `Σ^{-1/2} ∘ Σ^{-1/2}`.
-/
noncomputable def chewi620PullbackIdentityInvShape
    (T : E ≃ₗ[ℝ] E) (y : E) : E :=
  T.symm (T.symm y)

/--
Next inverse-shape obtained by pulling back the normalized standard-cut
inverse-shape through the normalization map `T.symm`.
-/
noncomputable def chewi620PullbackStandardCutInvShape
    (d : ℕ) (u : E) (T : E ≃ₗ[ℝ] E) (y : E) : E :=
  T.symm (chewi620StandardCutInvShape d u (T.symm y))

/-- Quadratic form for the current pullback inverse-shape. -/
theorem chewi620_pullbackIdentityInvShape_quadratic
    {T : E ≃ₗ[ℝ] E} (hT_symm : T.IsSymmetric) (y : E) :
    inner ℝ y (chewi620PullbackIdentityInvShape T y) =
      ‖T.symm y‖ ^ (2 : ℕ) := by
  have hsymm_inv : T.symm.IsSymmetric := hT_symm.toLinearMap_symm
  calc
    inner ℝ y (chewi620PullbackIdentityInvShape T y) =
        inner ℝ (T.symm y) (T.symm y) := by
      exact (hsymm_inv y (T.symm y)).symm
    _ = ‖T.symm y‖ ^ (2 : ℕ) := by
      rw [real_inner_self_eq_norm_sq]

/-- Quadratic form for the next standard-cut pullback inverse-shape. -/
theorem chewi620_pullbackStandardCutInvShape_quadratic
    {d : ℕ} {u : E} {T : E ≃ₗ[ℝ] E}
    (hT_symm : T.IsSymmetric) (y : E) :
    inner ℝ y (chewi620PullbackStandardCutInvShape d u T y) =
      inner ℝ (T.symm y)
        (chewi620StandardCutInvShape d u (T.symm y)) := by
  have hsymm_inv : T.symm.IsSymmetric := hT_symm.toLinearMap_symm
  exact (hsymm_inv y (chewi620StandardCutInvShape d u (T.symm y))).symm

/--
The pulled-back next inverse-shape supplies the `hnext` identity in the affine
transport certificate, once the original-space center is the image of the
normalized standard-cut center.
-/
theorem chewi620_pullbackStandardCutInvShape_hnext
    {d : ℕ} {u center nextCenter z : E} {T : E ≃ₗ[ℝ] E}
    (hT_symm : T.IsSymmetric)
    (hcenter :
      nextCenter - center = T (chewi620StandardCutCenter d u)) :
    inner ℝ (z - nextCenter)
        (chewi620PullbackStandardCutInvShape d u T (z - nextCenter)) =
      inner ℝ
        (T.symm (z - center) - chewi620StandardCutCenter d u)
        (chewi620StandardCutInvShape d u
          (T.symm (z - center) - chewi620StandardCutCenter d u)) := by
  have hstd :
      T.symm (z - nextCenter) =
        T.symm (z - center) - chewi620StandardCutCenter d u := by
    calc
      T.symm (z - nextCenter) =
          T.symm ((z - center) - (nextCenter - center)) := by
        congr 1
        module
      _ = T.symm (z - center) - T.symm (nextCenter - center) := by
        simp
      _ = T.symm (z - center) - chewi620StandardCutCenter d u := by
        rw [hcenter]
        simp
  rw [chewi620_pullbackStandardCutInvShape_quadratic hT_symm]
  rw [hstd]

section EuclideanMatrix

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/--
Matrix-backed inverse-shape operator on Euclidean coordinate space.  This is
the concrete finite-dimensional representation used by Chewi's displayed
`Σ_n^{-1}` and `Σ_{n+1}^{-1}` quadratic forms.
-/
noncomputable def matrixInvShape (A : Matrix ι ι ℝ) :
    EuclideanSpace ℝ ι -> EuclideanSpace ℝ ι :=
  fun z => A.toEuclideanLin z

@[simp]
theorem matrixInvShape_apply (A : Matrix ι ι ℝ) (z : EuclideanSpace ℝ ι) :
    matrixInvShape A z = A.toEuclideanLin z :=
  rfl

/-- Coordinate-vector expression for applying a matrix-backed inverse shape. -/
theorem matrixInvShape_eq_toLp_mulVec
    (A : Matrix ι ι ℝ) (z : EuclideanSpace ℝ ι) :
    matrixInvShape A z =
      (WithLp.toLp 2 (A.mulVec z.ofLp) : EuclideanSpace ℝ ι) := by
  simp [matrixInvShape, Matrix.toEuclideanLin, Matrix.toLpLin_apply]

/--
Coordinate expression for the quadratic form induced by a matrix-backed
inverse shape.  This is the reusable bridge from `ellipsoidSet`'s inner-product
surface to mathlib's `dotProduct`/`mulVec` matrix API.
-/
theorem matrixInvShape_quadratic_eq_dotProduct
    (A : Matrix ι ι ℝ) (z : EuclideanSpace ℝ ι) :
    inner ℝ z (matrixInvShape A z) = z.ofLp ⬝ᵥ A.mulVec z.ofLp := by
  simp [matrixInvShape, EuclideanSpace.inner_eq_star_dotProduct,
    Matrix.toEuclideanLin, Matrix.toLpLin_apply, dotProduct_comm]

/-- Positive-semidefinite matrices give nonnegative ellipsoid quadratic forms. -/
theorem matrixInvShape_quadratic_nonneg_of_posSemidef
    {A : Matrix ι ι ℝ} (hA : A.PosSemidef) (z : EuclideanSpace ℝ ι) :
    0 ≤ inner ℝ z (matrixInvShape A z) := by
  rw [matrixInvShape_quadratic_eq_dotProduct]
  simpa using hA.dotProduct_mulVec_nonneg z.ofLp

/-- Positive-definite matrices give positive quadratic forms away from zero. -/
theorem matrixInvShape_quadratic_pos_of_posDef
    {A : Matrix ι ι ℝ} (hA : A.PosDef)
    {z : EuclideanSpace ℝ ι} (hz : z ≠ 0) :
    0 < inner ℝ z (matrixInvShape A z) := by
  rw [matrixInvShape_quadratic_eq_dotProduct]
  have hz_ofLp : z.ofLp ≠ 0 := by
    intro hz0
    apply hz
    ext i
    exact congrFun hz0 i
  simpa using hA.dotProduct_mulVec_pos hz_ofLp

/--
Composition law for matrix-backed inverse-shape operators.  This is the
Euclidean-space version of `(A * B) z = A (B z)`.
-/
theorem matrixInvShape_mul
    (A B : Matrix ι ι ℝ) (z : EuclideanSpace ℝ ι) :
    matrixInvShape (A * B) z = matrixInvShape A (matrixInvShape B z) := by
  ext i
  simp [matrixInvShape, Matrix.toEuclideanLin, Matrix.toLpLin_apply,
    Matrix.mulVec_mulVec]

/-- The identity matrix-backed inverse shape is the identity map. -/
theorem matrixInvShape_one (z : EuclideanSpace ℝ ι) :
    matrixInvShape (1 : Matrix ι ι ℝ) z = z := by
  ext i
  simp [matrixInvShape, Matrix.toEuclideanLin]

/-- Matrix-backed inverse shapes preserve matrix addition. -/
theorem matrixInvShape_add
    (A B : Matrix ι ι ℝ) (z : EuclideanSpace ℝ ι) :
    matrixInvShape (A + B) z = matrixInvShape A z + matrixInvShape B z := by
  ext i
  simp [matrixInvShape, Matrix.toEuclideanLin, Matrix.toLpLin_apply]

/-- Matrix-backed inverse shapes preserve scalar multiplication of matrices. -/
theorem matrixInvShape_smul
    (c : ℝ) (A : Matrix ι ι ℝ) (z : EuclideanSpace ℝ ι) :
    matrixInvShape (c • A) z = c • matrixInvShape A z := by
  ext i
  simp [matrixInvShape, Matrix.toEuclideanLin, Matrix.toLpLin_apply]

/-- Matrix-backed inverse shapes preserve matrix subtraction. -/
theorem matrixInvShape_sub
    (A B : Matrix ι ι ℝ) (z : EuclideanSpace ℝ ι) :
    matrixInvShape (A - B) z = matrixInvShape A z - matrixInvShape B z := by
  ext i
  simp [matrixInvShape, Matrix.toEuclideanLin, Matrix.toLpLin_apply]

/--
Action of a rank-one matrix-backed inverse shape.  This is the coordinate
engine for expanding Chewi's displayed ellipsoid update
`Σ + c (Σp)(Σp)^T`.
-/
theorem matrixInvShape_vecMulVec
    (a b : ι -> ℝ) (z : EuclideanSpace ℝ ι) :
    matrixInvShape (Matrix.vecMulVec a b) z =
      (b ⬝ᵥ z.ofLp) • (WithLp.toLp 2 a : EuclideanSpace ℝ ι) := by
  ext i
  simp [matrixInvShape, Matrix.toEuclideanLin, Matrix.toLpLin_apply,
    Matrix.vecMulVec_mulVec, mul_comm]

omit [DecidableEq ι] in
/-- Inner product with a coordinate vector as a matrix dot product. -/
theorem inner_toLp_eq_dotProduct
    (a : ι -> ℝ) (z : EuclideanSpace ℝ ι) :
    inner ℝ (WithLp.toLp 2 a : EuclideanSpace ℝ ι) z = a ⬝ᵥ z.ofLp := by
  simp [EuclideanSpace.inner_eq_star_dotProduct, dotProduct_comm]

/--
Self rank-one action in inner-product form.  This is the shape used by the
normalized standard-cut forward map.
-/
theorem matrixInvShape_vecMulVec_self
    (a : ι -> ℝ) (z : EuclideanSpace ℝ ι) :
    matrixInvShape (Matrix.vecMulVec a a) z =
      (inner ℝ (WithLp.toLp 2 a : EuclideanSpace ℝ ι) z) •
        (WithLp.toLp 2 a : EuclideanSpace ℝ ι) := by
  rw [matrixInvShape_vecMulVec, inner_toLp_eq_dotProduct]

/--
Real-valued version of mathlib's Haar image-scaling theorem for a linear map.
This is the measure-theoretic bridge needed to turn a determinant calculation
into Chewi's real-valued volume ratio.
-/
theorem addHaar_image_linearMap_real
    {F : Type*} [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [BorelSpace F] [FiniteDimensional ℝ F]
    (μ : MeasureTheory.Measure F) [μ.IsAddHaarMeasure]
    (L : F →ₗ[ℝ] F) (s : Set F) :
    μ.real (L '' s) = |LinearMap.det L| * μ.real s := by
  change (μ (L '' s)).toReal = |LinearMap.det L| * (μ s).toReal
  rw [MeasureTheory.Measure.addHaar_image_linearMap]
  simp

/--
Real-valued translation invariance for an additive Haar measure.  This is the
affine part needed after the linear determinant scaling has been applied.
-/
theorem addHaar_image_add_left_real
    {F : Type*} [NormedAddCommGroup F]
    [MeasurableSpace F] [BorelSpace F]
    (μ : MeasureTheory.Measure F) [μ.IsAddHaarMeasure]
    (a : F) (s : Set F) :
    μ.real ((fun x => a + x) '' s) = μ.real s := by
  change (μ ((fun x => a + x) '' s)).toReal = (μ s).toReal
  have hset : (fun x => a + x) '' s = (fun x => -a + x) ⁻¹' s := by
    ext y
    constructor
    · rintro ⟨x, hx, rfl⟩
      simpa using hx
    · intro hy
      exact ⟨-a + y, by simpa using hy, by simp⟩
  rw [hset, MeasureTheory.measure_preimage_add]

/-- Determinant of the Euclidean linear map associated to a real matrix. -/
theorem matrix_toEuclideanLin_det (A : Matrix ι ι ℝ) :
    LinearMap.det
        (A.toEuclideanLin :
          EuclideanSpace ℝ ι →ₗ[ℝ] EuclideanSpace ℝ ι) = A.det := by
  simp [Matrix.toEuclideanLin, LinearMap.det_toLpLin]

/--
Real-volume scaling for the image of a set under a matrix-backed inverse-shape
operator on Euclidean coordinate space.
-/
theorem matrixInvShape_image_volume_real
    (A : Matrix ι ι ℝ) (s : Set (EuclideanSpace ℝ ι)) :
    MeasureTheory.volume.real (matrixInvShape A '' s) =
      |A.det| * MeasureTheory.volume.real s := by
  simpa [matrixInvShape, matrix_toEuclideanLin_det] using
    (addHaar_image_linearMap_real
      (μ := MeasureTheory.volume)
      (L :=
        (A.toEuclideanLin :
          EuclideanSpace ℝ ι →ₗ[ℝ] EuclideanSpace ℝ ι))
      (s := s))

/--
Real-volume scaling for the translated image of a set under a matrix-backed
inverse-shape operator.
-/
theorem matrixInvShape_image_add_volume_real
    (A : Matrix ι ι ℝ) (center : EuclideanSpace ℝ ι)
    (s : Set (EuclideanSpace ℝ ι)) :
    MeasureTheory.volume.real
        ((fun x => center + matrixInvShape A x) '' s) =
      |A.det| * MeasureTheory.volume.real s := by
  have himage :
      (fun x => center + matrixInvShape A x) '' s =
        (fun y => center + y) '' (matrixInvShape A '' s) := by
    ext z
    constructor
    · rintro ⟨x, hx, rfl⟩
      exact ⟨matrixInvShape A x, ⟨x, hx, rfl⟩, rfl⟩
    · rintro ⟨y, ⟨x, hx, rfl⟩, rfl⟩
      exact ⟨x, hx, rfl⟩
  rw [himage]
  rw [addHaar_image_add_left_real]
  exact matrixInvShape_image_volume_real A s

/--
Square-root image model for a displayed ellipsoid.  If an invertible matrix
`root` parametrizes the quadratic form in the sense that
`<root y, A⁻¹ root y> = <y, y>`, then the ellipsoid
`{z : <z-c, A⁻¹(z-c)> <= 1}` is exactly the translated image of the closed
unit ball under `root`.
-/
theorem ellipsoidSet_eq_matrix_image_closedBall_of_quadratic
    {A root : Matrix ι ι ℝ} (hroot : IsUnit root.det)
    (center : EuclideanSpace ℝ ι)
    (hquad : ∀ y : EuclideanSpace ℝ ι,
      inner ℝ (matrixInvShape root y)
        (matrixInvShape A⁻¹ (matrixInvShape root y)) = inner ℝ y y) :
    ellipsoidSet center (matrixInvShape A⁻¹) =
      (fun y => center + matrixInvShape root y) ''
        Metric.closedBall (0 : EuclideanSpace ℝ ι) 1 := by
  ext z
  constructor
  · intro hz
    let y : EuclideanSpace ℝ ι := matrixInvShape root⁻¹ (z - center)
    have hy_image : matrixInvShape root y = z - center := by
      change matrixInvShape root (matrixInvShape root⁻¹ (z - center)) = z - center
      rw [← matrixInvShape_mul]
      rw [Matrix.mul_nonsing_inv root hroot]
      simp [matrixInvShape]
    have hquad_y := hquad y
    rw [hy_image] at hquad_y
    have hy_inner_le : inner ℝ y y ≤ 1 := by
      rw [← hquad_y]
      simpa [ellipsoidSet] using hz
    have hy_norm_sq : ‖y‖ ^ (2 : ℕ) ≤ 1 ^ (2 : ℕ) := by
      simpa [real_inner_self_eq_norm_sq] using hy_inner_le
    have hy_norm : ‖y‖ ≤ 1 :=
      (sq_le_sq₀ (norm_nonneg y) zero_le_one).mp hy_norm_sq
    refine ⟨y, ?_, ?_⟩
    · simpa [Metric.mem_closedBall, dist_eq_norm] using hy_norm
    · change center + matrixInvShape root y = z
      rw [hy_image]
      abel
  · rintro ⟨y, hy, rfl⟩
    have hy_norm : ‖y‖ ≤ 1 := by
      simpa [Metric.mem_closedBall, dist_eq_norm] using hy
    have hy_norm_sq : ‖y‖ ^ (2 : ℕ) ≤ 1 ^ (2 : ℕ) :=
      (sq_le_sq₀ (norm_nonneg y) zero_le_one).mpr hy_norm
    have hy_inner_le : inner ℝ y y ≤ 1 := by
      simpa [real_inner_self_eq_norm_sq] using hy_norm_sq
    have hroot_quad_le :
        inner ℝ (matrixInvShape root y)
          (matrixInvShape A⁻¹ (matrixInvShape root y)) ≤ 1 := by
      rw [hquad y]
      exact hy_inner_le
    simpa [ellipsoidSet] using hroot_quad_le

/-- Positive-definite matrices have positive determinant. -/
theorem chewi620_matrixPosDef_det_pos
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    0 < Sigma.det :=
  hSigma.det_pos

/-- Positive-definite matrices have nonzero determinant. -/
theorem chewi620_matrixPosDef_det_ne_zero
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    Sigma.det ≠ 0 :=
  ne_of_gt (chewi620_matrixPosDef_det_pos hSigma)

/--
Determinant-square identity for mathlib's CFC matrix square root.  This is the
local wrapper needed for the Lemma 6.20 square-root volume model.
-/
theorem cfcSqrt_det_sq_of_posSemidef
    {A : Matrix ι ι ℝ} (hA : A.PosSemidef) :
    (CFC.sqrt A).det ^ (2 : ℕ) = A.det := by
  rw [Matrix.PosSemidef.det_sqrt hA]
  simpa using Real.sq_sqrt hA.det_nonneg

/-- Positive-definite matrices have a unit determinant, the key nonsingular-inverse hypothesis. -/
theorem chewi620_matrixPosDef_det_isUnit
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    IsUnit Sigma.det :=
  (Matrix.isUnit_iff_isUnit_det (A := Sigma)).mp hSigma.isUnit

/--
For a positive-definite matrix, the CFC square root conjugates the inverse
quadratic form to the Euclidean unit quadratic form.  This is the spectral
square-root identity needed to instantiate the Lemma 6.20 volume model.
-/
theorem cfcSqrt_quadratic_inv_of_posDef
    {A : Matrix ι ι ℝ} (hA : A.PosDef)
    (y : EuclideanSpace ℝ ι) :
    inner ℝ (matrixInvShape (CFC.sqrt A) y)
      (matrixInvShape A⁻¹ (matrixInvShape (CFC.sqrt A) y)) =
        inner ℝ y y := by
  let S : Matrix ι ι ℝ := CFC.sqrt A
  have hA_psd : A.PosSemidef := hA.posSemidef
  have hS_sq : S * S = A := by
    simpa [S, pow_two] using
      (CFC.sq_sqrt A (ha := hA_psd.nonneg))
  have hS_det_sq : S.det ^ (2 : ℕ) = A.det := by
    simpa [S] using cfcSqrt_det_sq_of_posSemidef hA_psd
  have hS_det_ne : S.det ≠ 0 := by
    intro hzero
    have hA_det_zero : A.det = 0 := by
      rw [← hS_det_sq, hzero]
      norm_num
    exact (chewi620_matrixPosDef_det_ne_zero hA) hA_det_zero
  have hS_unit : IsUnit S.det := isUnit_iff_ne_zero.mpr hS_det_ne
  have hprod :
      S * (A⁻¹ * S) = 1 := by
    have hXS : S * (A⁻¹ * S) * S = S := by
      calc
        S * (A⁻¹ * S) * S = S * (A⁻¹ * (S * S)) := by
          rw [Matrix.mul_assoc, ← Matrix.mul_assoc A⁻¹ S S]
        _ = S * (A⁻¹ * A) := by
          rw [hS_sq]
        _ = S * 1 := by
          rw [Matrix.nonsing_inv_mul A (chewi620_matrixPosDef_det_isUnit hA)]
        _ = S := by
          rw [Matrix.mul_one]
    calc
      S * (A⁻¹ * S) =
          (S * (A⁻¹ * S) * S) * S⁻¹ := by
        exact
          (Matrix.mul_nonsing_inv_cancel_right
            (A := S) (B := S * (A⁻¹ * S)) hS_unit).symm
      _ = S * S⁻¹ := by
        rw [hXS]
      _ = 1 := by
        exact Matrix.mul_nonsing_inv S hS_unit
  have hS_psd : S.PosSemidef :=
    Matrix.nonneg_iff_posSemidef.mp (by simp [S])
  have hS_symm : (S.toEuclideanLin).IsSymmetric :=
    Matrix.isSymmetric_toEuclideanLin_iff.mpr hS_psd.isHermitian
  have happ :
      matrixInvShape S (matrixInvShape A⁻¹ (matrixInvShape S y)) = y := by
    calc
      matrixInvShape S (matrixInvShape A⁻¹ (matrixInvShape S y)) =
          matrixInvShape S (matrixInvShape (A⁻¹ * S) y) := by
        rw [matrixInvShape_mul]
      _ = matrixInvShape (S * (A⁻¹ * S)) y := by
        rw [← matrixInvShape_mul]
      _ = y := by
        rw [hprod, matrixInvShape_one]
  calc
    inner ℝ (matrixInvShape (CFC.sqrt A) y)
        (matrixInvShape A⁻¹ (matrixInvShape (CFC.sqrt A) y)) =
        inner ℝ (matrixInvShape S y)
          (matrixInvShape A⁻¹ (matrixInvShape S y)) := by
      rfl
    _ =
        inner ℝ y
          (matrixInvShape S (matrixInvShape A⁻¹ (matrixInvShape S y))) := by
      simpa [matrixInvShape] using
        hS_symm y (matrixInvShape A⁻¹ (matrixInvShape S y))
    _ = inner ℝ y y := by
      rw [happ]

/--
The CFC square root factors a positive-semidefinite matrix quadratic form.
This is the local Cauchy-Schwarz bridge for Chewi's rank-one ellipsoid update.
-/
theorem cfcSqrt_inner_matrixInvShape_left
    {A : Matrix ι ι ℝ} (hA : A.PosSemidef)
    (x y : EuclideanSpace ℝ ι) :
    inner ℝ (matrixInvShape A x) y =
      inner ℝ (matrixInvShape (CFC.sqrt A) x)
        (matrixInvShape (CFC.sqrt A) y) := by
  let S : Matrix ι ι ℝ := CFC.sqrt A
  have hS_sq : S * S = A := by
    simpa [S, pow_two] using
      (CFC.sq_sqrt A (ha := hA.nonneg))
  have hS_psd : S.PosSemidef :=
    Matrix.nonneg_iff_posSemidef.mp (by simp [S])
  have hS_symm : (S.toEuclideanLin).IsSymmetric :=
    Matrix.isSymmetric_toEuclideanLin_iff.mpr hS_psd.isHermitian
  calc
    inner ℝ (matrixInvShape A x) y =
        inner ℝ (matrixInvShape (S * S) x) y := by
      rw [hS_sq]
    _ = inner ℝ (matrixInvShape S (matrixInvShape S x)) y := by
      rw [matrixInvShape_mul]
    _ =
        inner ℝ (matrixInvShape S x)
          (matrixInvShape S y) := by
      simpa [matrixInvShape] using hS_symm (matrixInvShape S x) y

/--
Cauchy-Schwarz for the positive-definite `Σ`-inner product, in the exact
rank-one form used by the ellipsoid update.
-/
theorem chewi620_matrix_rankOne_cauchy_schwarz
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    (p z : EuclideanSpace ℝ ι) :
    inner ℝ (matrixInvShape Sigma p) z ^ (2 : ℕ) ≤
      inner ℝ p (matrixInvShape Sigma p) *
        inner ℝ z (matrixInvShape Sigma z) := by
  have hpsd : Sigma.PosSemidef := hSigma.posSemidef
  rw [cfcSqrt_inner_matrixInvShape_left hpsd p z]
  have hpp :
      inner ℝ p (matrixInvShape Sigma p) =
        inner ℝ (matrixInvShape (CFC.sqrt Sigma) p)
          (matrixInvShape (CFC.sqrt Sigma) p) := by
    rw [real_inner_comm]
    rw [cfcSqrt_inner_matrixInvShape_left hpsd p p]
  have hzz :
      inner ℝ z (matrixInvShape Sigma z) =
        inner ℝ (matrixInvShape (CFC.sqrt Sigma) z)
          (matrixInvShape (CFC.sqrt Sigma) z) := by
    rw [real_inner_comm]
    rw [cfcSqrt_inner_matrixInvShape_left hpsd z z]
  rw [hpp, hzz]
  simpa [sq] using
    real_inner_mul_inner_self_le
      (matrixInvShape (CFC.sqrt Sigma) p)
      (matrixInvShape (CFC.sqrt Sigma) z)

/-- The nonsingular inverse of a positive-definite matrix is positive definite. -/
theorem chewi620_matrixPosDef_inv
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    Sigma⁻¹.PosDef :=
  hSigma.inv

/-- Right inverse cancellation for a positive-definite matrix. -/
theorem chewi620_matrixPosDef_mul_inv
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    Sigma * Sigma⁻¹ = 1 :=
  Matrix.mul_nonsing_inv Sigma (chewi620_matrixPosDef_det_isUnit hSigma)

/-- Left inverse cancellation for a positive-definite matrix. -/
theorem chewi620_matrixPosDef_inv_mul
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    Sigma⁻¹ * Sigma = 1 :=
  Matrix.nonsing_inv_mul Sigma (chewi620_matrixPosDef_det_isUnit hSigma)

/-- Right cancellation through the nonsingular inverse of a positive-definite matrix. -/
theorem chewi620_matrixPosDef_mul_inv_cancel_right
    {Sigma B : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    B * Sigma * Sigma⁻¹ = B :=
  Matrix.mul_nonsing_inv_cancel_right Sigma B
    (chewi620_matrixPosDef_det_isUnit hSigma)

/-- Left cancellation through the nonsingular inverse of a positive-definite matrix. -/
theorem chewi620_matrixPosDef_inv_mul_cancel_left
    {Sigma B : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    Sigma⁻¹ * (Sigma * B) = B :=
  Matrix.nonsing_inv_mul_cancel_left Sigma B
    (chewi620_matrixPosDef_det_isUnit hSigma)

/-- Determinant product identity for the nonsingular inverse of a positive-definite matrix. -/
theorem chewi620_matrixPosDef_det_inv_mul_det
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    Sigma⁻¹.det * Sigma.det = 1 :=
  Matrix.det_nonsing_inv_mul_det Sigma
    (chewi620_matrixPosDef_det_isUnit hSigma)

/-- The nonsingular inverse of the nonsingular inverse returns a positive-definite matrix. -/
theorem chewi620_matrixPosDef_inv_inv
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef) :
    Sigma⁻¹⁻¹ = Sigma :=
  Matrix.nonsing_inv_nonsing_inv Sigma
    (chewi620_matrixPosDef_det_isUnit hSigma)

/-- Matrix-backed shape cancellation `Σ (Σ⁻¹ z) = z`. -/
theorem matrixInvShape_mul_inv_cancel
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    (z : EuclideanSpace ℝ ι) :
    matrixInvShape Sigma (matrixInvShape Sigma⁻¹ z) = z := by
  rw [← matrixInvShape_mul]
  rw [chewi620_matrixPosDef_mul_inv hSigma]
  simp [matrixInvShape]

/-- Matrix-backed shape cancellation `Σ⁻¹ (Σ z) = z`. -/
theorem matrixInvShape_inv_mul_cancel
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    (z : EuclideanSpace ℝ ι) :
    matrixInvShape Sigma⁻¹ (matrixInvShape Sigma z) = z := by
  rw [← matrixInvShape_mul]
  rw [chewi620_matrixPosDef_inv_mul hSigma]
  simp [matrixInvShape]

/-- Matrix-backed shape cancellation `A (A⁻¹ z) = z` from a determinant unit. -/
theorem matrixInvShape_mul_inv_cancel_of_det_isUnit
    {A : Matrix ι ι ℝ} (hA : IsUnit A.det)
    (z : EuclideanSpace ℝ ι) :
    matrixInvShape A (matrixInvShape A⁻¹ z) = z := by
  rw [← matrixInvShape_mul]
  rw [Matrix.mul_nonsing_inv A hA]
  simp [matrixInvShape]

/-- Matrix-backed shape cancellation `A⁻¹ (A z) = z` from a determinant unit. -/
theorem matrixInvShape_inv_mul_cancel_of_det_isUnit
    {A : Matrix ι ι ℝ} (hA : IsUnit A.det)
    (z : EuclideanSpace ℝ ι) :
    matrixInvShape A⁻¹ (matrixInvShape A z) = z := by
  rw [← matrixInvShape_mul]
  rw [Matrix.nonsing_inv_mul A hA]
  simp [matrixInvShape]

/--
If a candidate inverse-shape operator is a left inverse for `A`, then it is the
matrix-backed nonsingular inverse shape of `A`.
-/
theorem matrixInvShape_eq_inv_of_left_inverse
    {A : Matrix ι ι ℝ} (hA : IsUnit A.det)
    {F : EuclideanSpace ℝ ι -> EuclideanSpace ℝ ι}
    (hleft : ∀ y, matrixInvShape A (F y) = y)
    (y : EuclideanSpace ℝ ι) :
    F y = matrixInvShape A⁻¹ y := by
  calc
    F y = matrixInvShape A⁻¹ (matrixInvShape A (F y)) := by
      exact (matrixInvShape_inv_mul_cancel_of_det_isUnit hA (F y)).symm
    _ = matrixInvShape A⁻¹ y := by
      rw [hleft y]

/--
If a linear equivalence `T` squares to Chewi's forward shape matrix `Σ`, then
the current pullback inverse-shape is the displayed `Σ⁻¹` inverse shape.
-/
theorem chewi620_pullbackIdentityInvShape_eq_matrixInvShape_inv
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    (y : EuclideanSpace ℝ ι) :
    chewi620PullbackIdentityInvShape T y = matrixInvShape Sigma⁻¹ y := by
  let v : EuclideanSpace ℝ ι := chewi620PullbackIdentityInvShape T y
  have hvT : T (T v) = y := by
    simp [v, chewi620PullbackIdentityInvShape]
  have hvSigma : matrixInvShape Sigma v = y := by
    rw [← hT_sq v]
    exact hvT
  calc
    chewi620PullbackIdentityInvShape T y = v := rfl
    _ = matrixInvShape Sigma⁻¹ (matrixInvShape Sigma v) := by
      exact (matrixInvShape_inv_mul_cancel hSigma v).symm
    _ = matrixInvShape Sigma⁻¹ y := by
      rw [hvSigma]

/--
Set-level version of the current-shape pullback identity.  This identifies the
affine-normalized current ellipsoid with Chewi's displayed
`<x-c, Σ⁻¹(x-c)> <= 1` ellipsoid.
-/
theorem chewi620_ellipsoidSet_pullbackIdentity_eq_matrixInvShape_inv
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    (center : EuclideanSpace ℝ ι) :
    ellipsoidSet center (chewi620PullbackIdentityInvShape T) =
      ellipsoidSet center (matrixInvShape Sigma⁻¹) := by
  ext z
  simp [ellipsoidSet,
    chewi620_pullbackIdentityInvShape_eq_matrixInvShape_inv
      (Sigma := Sigma) hSigma hT_sq (z - center)]

/--
Rank-one collapse for Chewi's displayed ellipsoid update:
`(Σp)^T Σ⁻¹ (Σp) = <p, Σp>`.
-/
theorem chewi620_matrix_rankOne_collapse
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    (p : EuclideanSpace ℝ ι) :
    Sigma.mulVec p.ofLp ⬝ᵥ (Sigma⁻¹.mulVec (Sigma.mulVec p.ofLp)) =
      inner ℝ p (matrixInvShape Sigma p) := by
  have hcancel :
      Sigma⁻¹.mulVec (Sigma.mulVec p.ofLp) = p.ofLp := by
    rw [Matrix.mulVec_mulVec]
    rw [chewi620_matrixPosDef_inv_mul hSigma]
    simp
  rw [hcancel, matrixInvShape_quadratic_eq_dotProduct]
  exact dotProduct_comm (Sigma.mulVec p.ofLp) p.ofLp

/--
Rank-one determinant update for Chewi's displayed ellipsoid shape matrix.
This is the matrix determinant lemma specialized to
`Σ - c (Σp)(Σp)^T`, with the scalar collapse
`(Σp)^T Σ⁻¹(Σp) = <p,Σp>` already discharged locally.
-/
theorem chewi620_matrix_rankOne_det_update
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    (c : ℝ) (p : EuclideanSpace ℝ ι) :
    (Sigma -
        c • Matrix.vecMulVec (Sigma.mulVec p.ofLp) (Sigma.mulVec p.ofLp)).det =
      Sigma.det * (1 - c * inner ℝ p (matrixInvShape Sigma p)) := by
  let u : ι -> ℝ := Sigma.mulVec p.ofLp
  have hunit : IsUnit Sigma.det :=
    chewi620_matrixPosDef_det_isUnit hSigma
  have hcollapse :
      u ⬝ᵥ (Sigma⁻¹.mulVec u) =
        inner ℝ p (matrixInvShape Sigma p) := by
    simpa [u] using
      chewi620_matrix_rankOne_collapse (Sigma := Sigma) hSigma p
  calc
    (Sigma -
        c • Matrix.vecMulVec (Sigma.mulVec p.ofLp) (Sigma.mulVec p.ofLp)).det =
        (Sigma +
          Matrix.replicateCol (Fin 1) u *
            Matrix.replicateRow (Fin 1) ((-c) • u)).det := by
      congr 1
      ext i j
      simp [u, Matrix.mul_apply, Matrix.vecMulVec_apply,
        Matrix.replicateCol_apply, Matrix.replicateRow_apply, sub_eq_add_neg]
      ring_nf
    _ =
        Sigma.det *
          (1 +
            Matrix.replicateRow (Fin 1) ((-c) • u) *
              Sigma⁻¹ * Matrix.replicateCol (Fin 1) u).det := by
      exact Matrix.det_add_replicateCol_mul_replicateRow
        (ι := Fin 1) (A := Sigma) hunit u ((-c) • u)
    _ = Sigma.det * (1 - c * inner ℝ p (matrixInvShape Sigma p)) := by
      have hscalar :
          Matrix.vecMul ((-c) • u) Sigma⁻¹ ⬝ᵥ u =
            -c * inner ℝ p (matrixInvShape Sigma p) := by
        calc
          Matrix.vecMul ((-c) • u) Sigma⁻¹ ⬝ᵥ u =
              ((-c) • u) ⬝ᵥ (Sigma⁻¹.mulVec u) := by
            exact (Matrix.dotProduct_mulVec ((-c) • u) Sigma⁻¹ u).symm
          _ = -c * (u ⬝ᵥ (Sigma⁻¹.mulVec u)) := by
            simp [dotProduct, Finset.mul_sum, mul_assoc]
          _ = -c * inner ℝ p (matrixInvShape Sigma p) := by
            rw [hcollapse]
      have hsmall :
          (1 +
            Matrix.replicateRow (Fin 1) ((-c) • u) *
              Sigma⁻¹ * Matrix.replicateCol (Fin 1) u).det =
            1 - c * inner ℝ p (matrixInvShape Sigma p) := by
        rw [Matrix.det_fin_one]
        change
          ((1 +
            Matrix.replicateRow (Fin 1) ((-c) • u) *
              Sigma⁻¹ * Matrix.replicateCol (Fin 1) u :
              Matrix (Fin 1) (Fin 1) ℝ) 0 0) =
            1 - c * inner ℝ p (matrixInvShape Sigma p)
        calc
          ((1 +
              Matrix.replicateRow (Fin 1) ((-c) • u) *
                Sigma⁻¹ * Matrix.replicateCol (Fin 1) u :
                Matrix (Fin 1) (Fin 1) ℝ) 0 0) =
              1 + (Matrix.vecMul ((-c) • u) Sigma⁻¹ ⬝ᵥ u) := by
            simp [Matrix.mul_apply, Matrix.vecMul, dotProduct]
          _ = 1 - c * inner ℝ p (matrixInvShape Sigma p) := by
            rw [hscalar]
            ring
      rw [hsmall]

/--
The unscaled shape-update core in Chewi Lemma 6.20:
`Σ - (2/(d+1)) (Σp)(Σp)^T / <p,Σp>`.
-/
noncomputable def chewi620DisplayedShapeUpdateCore
    (d : ℕ) (Sigma : Matrix ι ι ℝ) (p : EuclideanSpace ℝ ι) :
    Matrix ι ι ℝ :=
  Sigma -
    (((2 : ℝ) / ((d : ℝ) + 1)) /
      inner ℝ p (matrixInvShape Sigma p)) •
      Matrix.vecMulVec (Sigma.mulVec p.ofLp) (Sigma.mulVec p.ofLp)

/--
Determinant of Chewi's unscaled rank-one ellipsoid update core:
`det(Σ - (2/(d+1)) ΣppᵀΣ / <p,Σp>) = det(Σ) * (d-1)/(d+1)`.
-/
theorem chewi620_displayedShapeUpdateCore_det
    {d : ℕ} (hd : 1 < d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    (chewi620DisplayedShapeUpdateCore d Sigma p).det =
      Sigma.det * (((d : ℝ) - 1) / ((d : ℝ) + 1)) := by
  let q : ℝ := inner ℝ p (matrixInvShape Sigma p)
  have hq_pos : 0 < q := by
    exact matrixInvShape_quadratic_pos_of_posDef hSigma hp
  have hq_ne : q ≠ 0 := ne_of_gt hq_pos
  have hd_ne : (d : ℝ) + 1 ≠ 0 := by
    positivity
  rw [chewi620DisplayedShapeUpdateCore]
  rw [chewi620_matrix_rankOne_det_update (Sigma := Sigma) hSigma]
  congr 1
  change 1 - ((2 / ((d : ℝ) + 1)) / q) * q =
    ((d : ℝ) - 1) / ((d : ℝ) + 1)
  field_simp [hq_ne, hd_ne]
  ring

/--
The full displayed forward-shape update in Chewi Lemma 6.20:
`d^2/(d^2-1)` times the rank-one update core.
-/
noncomputable def chewi620DisplayedShapeUpdate
    (d : ℕ) (Sigma : Matrix ι ι ℝ) (p : EuclideanSpace ℝ ι) :
    Matrix ι ι ℝ :=
  ((((d : ℝ) ^ (2 : ℕ)) /
    (((d : ℝ) ^ (2 : ℕ)) - 1)) •
    chewi620DisplayedShapeUpdateCore d Sigma p)

/--
Action of the unscaled displayed update core.  This packages the rank-one
correction in the original Chewi coordinates.
-/
theorem chewi620_displayedShapeUpdateCore_action
    (d : ℕ) (Sigma : Matrix ι ι ℝ)
    (p z : EuclideanSpace ℝ ι) :
    matrixInvShape (chewi620DisplayedShapeUpdateCore d Sigma p) z =
      matrixInvShape Sigma z -
        (((((2 : ℝ) / ((d : ℝ) + 1)) /
            inner ℝ p (matrixInvShape Sigma p)) *
            inner ℝ (matrixInvShape Sigma p) z) •
          matrixInvShape Sigma p) := by
  rw [chewi620DisplayedShapeUpdateCore, matrixInvShape_sub, matrixInvShape_smul,
    matrixInvShape_vecMulVec_self]
  rw [← matrixInvShape_eq_toLp_mulVec Sigma p]
  rw [smul_smul]

/--
Action of Chewi's full displayed forward-shape update.  This is the matrix
side of the remaining Lemma 6.20 transport identity.
-/
theorem chewi620_displayedShapeUpdate_action
    (d : ℕ) (Sigma : Matrix ι ι ℝ)
    (p z : EuclideanSpace ℝ ι) :
    matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p) z =
      ((((d : ℝ) ^ (2 : ℕ)) /
        (((d : ℝ) ^ (2 : ℕ)) - 1)) •
        (matrixInvShape Sigma z -
          (((((2 : ℝ) / ((d : ℝ) + 1)) /
              inner ℝ p (matrixInvShape Sigma p)) *
              inner ℝ (matrixInvShape Sigma p) z) •
            matrixInvShape Sigma p))) := by
  rw [chewi620DisplayedShapeUpdate, matrixInvShape_smul,
    chewi620_displayedShapeUpdateCore_action]

/-- The unscaled displayed shape update is Hermitian. -/
theorem chewi620_displayedShapeUpdateCore_isHermitian
    (d : ℕ) {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    (p : EuclideanSpace ℝ ι) :
    (chewi620DisplayedShapeUpdateCore d Sigma p).IsHermitian := by
  have hvec :
      (Matrix.vecMulVec (Sigma.mulVec p.ofLp) (Sigma.mulVec p.ofLp)).IsHermitian := by
    simpa using
      (Matrix.posSemidef_vecMulVec_self_star
        (Sigma.mulVec p.ofLp)).isHermitian
  have hcoef_self :
      IsSelfAdjoint
        (((2 : ℝ) / ((d : ℝ) + 1)) /
          inner ℝ p (matrixInvShape Sigma p)) := by
    simp [isSelfAdjoint_iff]
  rw [chewi620DisplayedShapeUpdateCore]
  exact hSigma.isHermitian.sub (hvec.smul hcoef_self)

/-- The full displayed shape update is Hermitian. -/
theorem chewi620_displayedShapeUpdate_isHermitian
    (d : ℕ) {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    (p : EuclideanSpace ℝ ι) :
    (chewi620DisplayedShapeUpdate d Sigma p).IsHermitian := by
  have hscale_self :
      IsSelfAdjoint
        (((d : ℝ) ^ (2 : ℕ)) /
          (((d : ℝ) ^ (2 : ℕ)) - 1)) := by
    simp [isSelfAdjoint_iff]
  rw [chewi620DisplayedShapeUpdate]
  exact
    (chewi620_displayedShapeUpdateCore_isHermitian
      (d := d) hSigma p).smul hscale_self

/--
The unscaled rank-one core in Chewi's ellipsoid update remains positive in
every nonzero direction.  The proof is the source Cauchy-Schwarz estimate in
the `Σ`-inner product.
-/
theorem chewi620_displayedShapeUpdateCore_quadratic_pos
    {d : ℕ} (hd : 1 < d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p z : EuclideanSpace ℝ ι} (hp : p ≠ 0) (hz : z ≠ 0) :
    0 <
      inner ℝ z
        (matrixInvShape (chewi620DisplayedShapeUpdateCore d Sigma p) z) := by
  let q : ℝ := inner ℝ p (matrixInvShape Sigma p)
  let r : ℝ := inner ℝ z (matrixInvShape Sigma z)
  let b : ℝ := inner ℝ (matrixInvShape Sigma p) z
  let k : ℝ := (2 : ℝ) / ((d : ℝ) + 1)
  have hq_pos : 0 < q := by
    exact matrixInvShape_quadratic_pos_of_posDef hSigma hp
  have hr_pos : 0 < r := by
    exact matrixInvShape_quadratic_pos_of_posDef hSigma hz
  have hk_pos : 0 < k := by
    have hden_pos : 0 < (d : ℝ) + 1 := by positivity
    exact div_pos (by norm_num) hden_pos
  have hk_lt_one : k < 1 := by
    have hd_real : 1 < (d : ℝ) := by exact_mod_cast hd
    have hden_pos : 0 < (d : ℝ) + 1 := by positivity
    change (2 : ℝ) / ((d : ℝ) + 1) < 1
    rw [div_lt_one hden_pos]
    linarith
  have hq_ne : q ≠ 0 := ne_of_gt hq_pos
  have hcs :
      b ^ (2 : ℕ) ≤ q * r := by
    simpa [q, r, b] using
      chewi620_matrix_rankOne_cauchy_schwarz
        (Sigma := Sigma) hSigma p z
  have hcoef_nonneg : 0 ≤ k / q := div_nonneg hk_pos.le hq_pos.le
  have hcorr_le : (k / q) * b ^ (2 : ℕ) ≤ k * r := by
    calc
      (k / q) * b ^ (2 : ℕ) ≤ (k / q) * (q * r) :=
        mul_le_mul_of_nonneg_left hcs hcoef_nonneg
      _ = k * r := by
        field_simp [hq_ne]
  have hcore_eq :
      inner ℝ z
          (matrixInvShape (chewi620DisplayedShapeUpdateCore d Sigma p) z) =
        r - (k / q) * b ^ (2 : ℕ) := by
    rw [chewi620_displayedShapeUpdateCore_action]
    simp only [inner_sub_right, inner_smul_right]
    have hb_comm : inner ℝ z (matrixInvShape Sigma p) = b := by
      rw [real_inner_comm]
    simp only [q, r, b, k] at hb_comm ⊢
    rw [hb_comm]
    ring
  have hkr_lt : k * r < r := by
    nlinarith [hr_pos, hk_pos, hk_lt_one]
  rw [hcore_eq]
  nlinarith

/-- The full displayed shape update has positive quadratic form. -/
theorem chewi620_displayedShapeUpdate_quadratic_pos
    {d : ℕ} (hd : 1 < d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p z : EuclideanSpace ℝ ι} (hp : p ≠ 0) (hz : z ≠ 0) :
    0 <
      inner ℝ z
        (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p) z) := by
  have hD_pos : 0 < (d : ℝ) := by
    have hd_nat : 0 < d := by omega
    exact_mod_cast hd_nat
  have hden_pos : 0 < ((d : ℝ) ^ (2 : ℕ)) - 1 := by
    have hd_real : 1 < (d : ℝ) := by exact_mod_cast hd
    nlinarith [sq_pos_of_pos (show 0 < (d : ℝ) - 1 by linarith)]
  have hscale_pos :
      0 < ((d : ℝ) ^ (2 : ℕ)) /
        (((d : ℝ) ^ (2 : ℕ)) - 1) :=
    div_pos (sq_pos_of_pos hD_pos) hden_pos
  rw [chewi620DisplayedShapeUpdate, matrixInvShape_smul]
  rw [inner_smul_right]
  exact mul_pos hscale_pos
    (chewi620_displayedShapeUpdateCore_quadratic_pos
      (d := d) hd hSigma hp hz)

/-- Chewi's displayed next forward-shape matrix is positive definite. -/
theorem chewi620_displayedShapeUpdate_posDef
    {d : ℕ} (hd : 1 < d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    (chewi620DisplayedShapeUpdate d Sigma p).PosDef := by
  refine
    Matrix.PosDef.of_dotProduct_mulVec_pos
      (chewi620_displayedShapeUpdate_isHermitian (d := d) hSigma p) ?_
  intro x hx
  let z : EuclideanSpace ℝ ι := WithLp.toLp 2 x
  have hz : z ≠ 0 := by
    intro hz0
    apply hx
    simpa [z] using congrArg (fun y : EuclideanSpace ℝ ι => y.ofLp) hz0
  have hpos :=
    chewi620_displayedShapeUpdate_quadratic_pos
      (d := d) hd hSigma (p := p) (z := z) hp hz
  rw [matrixInvShape_quadratic_eq_dotProduct] at hpos
  simpa [z] using hpos

/--
Determinant of Chewi's fully scaled displayed forward-shape update.  The
cardinality hypothesis identifies the matrix index type with the source
dimension `d`.
-/
theorem chewi620_displayedShapeUpdate_det
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    (chewi620DisplayedShapeUpdate d Sigma p).det =
      ((((d : ℝ) ^ (2 : ℕ)) /
          (((d : ℝ) ^ (2 : ℕ)) - 1)) ^ d) *
        (Sigma.det * (((d : ℝ) - 1) / ((d : ℝ) + 1))) := by
  rw [chewi620DisplayedShapeUpdate, Matrix.det_smul, hcard,
    chewi620_displayedShapeUpdateCore_det (d := d) hd hSigma hp]

/--
Chewi's displayed forward-shape determinant as a ratio against the current
shape determinant, in the source square-volume-ratio form.
-/
theorem chewi620_displayedShapeUpdate_det_div_det
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    (chewi620DisplayedShapeUpdate d Sigma p).det / Sigma.det =
      (((d : ℝ) - 1) / ((d : ℝ) + 1)) *
        ((((d : ℝ) ^ (2 : ℕ)) /
          (((d : ℝ) ^ (2 : ℕ)) - 1)) ^ d) := by
  have hdet :=
    chewi620_displayedShapeUpdate_det
      (d := d) hd hcard hSigma hp
  have hSigma_det_ne : Sigma.det ≠ 0 :=
    chewi620_matrixPosDef_det_ne_zero hSigma
  rw [hdet]
  field_simp [hSigma_det_ne]

/--
The determinant ratio of Chewi's displayed forward-shape update is exactly the
square of the displayed volume ratio.
-/
theorem chewi620_displayedShapeUpdate_det_div_det_eq_ellipsoidVolumeRatio_sq
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    (chewi620DisplayedShapeUpdate d Sigma p).det / Sigma.det =
      ellipsoidVolumeRatio d ^ (2 : ℕ) := by
  rw [chewi620_displayedShapeUpdate_det_div_det (d := d) hd hcard hSigma hp]
  rw [ellipsoidVolumeRatio]
  rw [Real.sq_sqrt (chewi620_ellipsoidVolumeRatio_source_nonneg hd)]

/--
Chewi's displayed forward-shape matrix has positive determinant under the
positive-definite current-shape and nonzero cut-vector hypotheses.
-/
theorem chewi620_displayedShapeUpdate_det_pos
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    0 < (chewi620DisplayedShapeUpdate d Sigma p).det := by
  have hD_gt_one : 1 < (d : ℝ) := by exact_mod_cast hd
  have hD_pos : 0 < (d : ℝ) := by linarith
  have hscale_pos :
      0 < ((d : ℝ) ^ (2 : ℕ)) /
        (((d : ℝ) ^ (2 : ℕ)) - 1) := by
    refine div_pos (sq_pos_of_pos hD_pos) ?_
    nlinarith [sq_pos_of_pos (show 0 < (d : ℝ) - 1 by linarith)]
  have hleft_pos : 0 < ((d : ℝ) - 1) / ((d : ℝ) + 1) := by
    exact div_pos (by linarith) (by positivity)
  rw [chewi620_displayedShapeUpdate_det (d := d) hd hcard hSigma hp]
  exact mul_pos (pow_pos hscale_pos d)
    (mul_pos (chewi620_matrixPosDef_det_pos hSigma) hleft_pos)

/-- Chewi's displayed forward-shape update is nonsingular. -/
theorem chewi620_displayedShapeUpdate_det_ne_zero
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    (chewi620DisplayedShapeUpdate d Sigma p).det ≠ 0 :=
  ne_of_gt (chewi620_displayedShapeUpdate_det_pos (d := d) hd hcard hSigma hp)

/--
Chewi's displayed forward-shape update supplies the determinant unit needed by
mathlib nonsingular-inverse and volume-scaling APIs.
-/
theorem chewi620_displayedShapeUpdate_det_isUnit
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    IsUnit (chewi620DisplayedShapeUpdate d Sigma p).det :=
  isUnit_iff_ne_zero.mpr
    (chewi620_displayedShapeUpdate_det_ne_zero (d := d) hd hcard hSigma hp)

/--
Scalar bridge from a squared-volume determinant bound to the `hvolume`
hypothesis used by the ellipsoid-step certificate.
-/
theorem chewi620_volume_le_of_sq_le_displayedShapeUpdate_det_ratio
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    {vol volNext : ℝ}
    (hvol_nonneg : 0 ≤ vol) (hvolNext_nonneg : 0 ≤ volNext)
    (hsq :
      volNext ^ (2 : ℕ) ≤
        ((chewi620DisplayedShapeUpdate d Sigma p).det / Sigma.det) *
          vol ^ (2 : ℕ)) :
    volNext ≤ ellipsoidVolumeRatio d * vol := by
  have hsq_ratio := hsq
  rw [chewi620_displayedShapeUpdate_det_div_det_eq_ellipsoidVolumeRatio_sq
    (d := d) hd hcard hSigma hp] at hsq_ratio
  have hsq_target :
      volNext ^ (2 : ℕ) ≤ (ellipsoidVolumeRatio d * vol) ^ (2 : ℕ) := by
    simpa [mul_pow] using hsq_ratio
  exact
    (sq_le_sq₀ hvolNext_nonneg
      (mul_nonneg (ellipsoidVolumeRatio_nonneg d) hvol_nonneg)).mp
        hsq_target

/--
Determinant-volume bridge for the final Lemma 6.20 `hvolume` hypothesis.  If
the current and next ellipsoid volumes are modeled as translated images of a
common unit set under matrix square-root factors whose determinant squares are
the displayed forward-shape determinants, then Chewi's source determinant ratio
implies the required volume shrink.
-/
theorem chewi620_hvolume_of_matrix_image_volume_models
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    {currentRoot nextRoot : Matrix ι ι ℝ}
    {center nextCenter : EuclideanSpace ℝ ι}
    {baseSet : Set (EuclideanSpace ℝ ι)}
    {vol volNext : ℝ}
    (hcurrentRoot_det_sq :
      currentRoot.det ^ (2 : ℕ) = Sigma.det)
    (hnextRoot_det_sq :
      nextRoot.det ^ (2 : ℕ) =
        (chewi620DisplayedShapeUpdate d Sigma p).det)
    (hvol :
      vol =
        MeasureTheory.volume.real
          ((fun x => center + matrixInvShape currentRoot x) '' baseSet))
    (hvolNext :
      volNext =
        MeasureTheory.volume.real
          ((fun x => nextCenter + matrixInvShape nextRoot x) '' baseSet)) :
    volNext ≤ ellipsoidVolumeRatio d * vol := by
  let baseVol : ℝ := MeasureTheory.volume.real baseSet
  have hvol_nonneg : 0 ≤ vol := by
    rw [hvol]
    exact MeasureTheory.measureReal_nonneg
  have hvolNext_nonneg : 0 ≤ volNext := by
    rw [hvolNext]
    exact MeasureTheory.measureReal_nonneg
  have hvol_sq :
      vol ^ (2 : ℕ) = Sigma.det * baseVol ^ (2 : ℕ) := by
    rw [hvol, matrixInvShape_image_add_volume_real]
    change (|currentRoot.det| * baseVol) ^ (2 : ℕ) =
      Sigma.det * baseVol ^ (2 : ℕ)
    rw [mul_pow, sq_abs, hcurrentRoot_det_sq]
  have hvolNext_sq :
      volNext ^ (2 : ℕ) =
        (chewi620DisplayedShapeUpdate d Sigma p).det *
          baseVol ^ (2 : ℕ) := by
    rw [hvolNext, matrixInvShape_image_add_volume_real]
    change (|nextRoot.det| * baseVol) ^ (2 : ℕ) =
      (chewi620DisplayedShapeUpdate d Sigma p).det *
        baseVol ^ (2 : ℕ)
    rw [mul_pow, sq_abs, hnextRoot_det_sq]
  have hSigma_det_ne : Sigma.det ≠ 0 :=
    chewi620_matrixPosDef_det_ne_zero hSigma
  have hsq_eq :
      volNext ^ (2 : ℕ) =
        ((chewi620DisplayedShapeUpdate d Sigma p).det / Sigma.det) *
          vol ^ (2 : ℕ) := by
    calc
      volNext ^ (2 : ℕ) =
          (chewi620DisplayedShapeUpdate d Sigma p).det *
            baseVol ^ (2 : ℕ) := hvolNext_sq
      _ =
          ((chewi620DisplayedShapeUpdate d Sigma p).det / Sigma.det) *
            (Sigma.det * baseVol ^ (2 : ℕ)) := by
        field_simp [hSigma_det_ne]
      _ =
          ((chewi620DisplayedShapeUpdate d Sigma p).det / Sigma.det) *
            vol ^ (2 : ℕ) := by
        rw [hvol_sq]
  exact
    chewi620_volume_le_of_sq_le_displayedShapeUpdate_det_ratio
      (d := d) hd hcard hSigma hp hvol_nonneg hvolNext_nonneg
      (le_of_eq hsq_eq)

/--
Once the displayed next-shape update is shown to be a left inverse for the
pulled-back standard-cut inverse-shape, the remaining Chewi Lemma 6.20
next-shape equality follows from nonsingular-inverse uniqueness.
-/
theorem chewi620_pullbackStandardCutInvShape_eq_displayedShapeUpdate_inv_of_left_inverse
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    {u : EuclideanSpace ℝ ι}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hleft :
      ∀ y,
        matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)
          (chewi620PullbackStandardCutInvShape d u T y) = y)
    (y : EuclideanSpace ℝ ι) :
    chewi620PullbackStandardCutInvShape d u T y =
      matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹ y := by
  exact
    matrixInvShape_eq_inv_of_left_inverse
      (A := chewi620DisplayedShapeUpdate d Sigma p)
      (F := fun y =>
        chewi620PullbackStandardCutInvShape d u T y)
      (chewi620_displayedShapeUpdate_det_isUnit
        (d := d) hd hcard hSigma hp)
      hleft y

/--
Set-level form of the displayed next inverse-shape equality, ready to replace
the pullback certificate's `nextInvShape` by Chewi's displayed
`Σ_{n+1}^{-1}` matrix update.
-/
theorem chewi620_ellipsoidSet_pullbackStandardCut_eq_displayedShapeUpdate_inv_of_left_inverse
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    {u : EuclideanSpace ℝ ι}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hleft :
      ∀ y,
        matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)
          (chewi620PullbackStandardCutInvShape d u T y) = y)
    (center : EuclideanSpace ℝ ι) :
    ellipsoidSet center
        (chewi620PullbackStandardCutInvShape d u T) =
      ellipsoidSet center
        (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹) := by
  ext z
  simp [ellipsoidSet,
    chewi620_pullbackStandardCutInvShape_eq_displayedShapeUpdate_inv_of_left_inverse
      (d := d) hd hcard hSigma hp hleft (z - center)]

/--
Transporting the normalized standard-cut forward-shape cancellation through
`T` gives the displayed-update left-inverse identity for the pulled-back next
inverse-shape.
-/
theorem chewi620_displayedShapeUpdate_left_inverse_of_standardCutForward_transport
    {d : ℕ} (hd : 1 < d)
    {Sigma : Matrix ι ι ℝ} {p u y : EuclideanSpace ℝ ι}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hu_norm : ‖u‖ = 1)
    (htransport :
      ∀ x,
        matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p) (T.symm x) =
          T (chewi620StandardCutForwardShape d u x)) :
    matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)
        (chewi620PullbackStandardCutInvShape d u T y) = y := by
  rw [chewi620PullbackStandardCutInvShape]
  calc
    matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)
        (T.symm (chewi620StandardCutInvShape d u (T.symm y)))
        = T (chewi620StandardCutForwardShape d u
            (chewi620StandardCutInvShape d u (T.symm y))) := by
      exact htransport (chewi620StandardCutInvShape d u (T.symm y))
    _ = T (T.symm y) := by
      rw [chewi620_standardCutForwardShape_left_inverse (d := d) hd hu_norm]
    _ = y := by
      simp

/--
Transport-level displayed next inverse-shape equality: after the matrix update
is identified with the normalized forward-shape update through `T`, the
pullback inverse-shape is Chewi's displayed nonsingular inverse.
-/
theorem chewi620_pullbackStandardCutInvShape_eq_displayedShapeUpdate_inv_of_forwardShape_transport
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    {u y : EuclideanSpace ℝ ι}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hu_norm : ‖u‖ = 1)
    (htransport :
      ∀ x,
        matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p) (T.symm x) =
          T (chewi620StandardCutForwardShape d u x)) :
    chewi620PullbackStandardCutInvShape d u T y =
      matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹ y := by
  exact
    chewi620_pullbackStandardCutInvShape_eq_displayedShapeUpdate_inv_of_left_inverse
      (d := d) hd hcard hSigma hp
      (fun y =>
        chewi620_displayedShapeUpdate_left_inverse_of_standardCutForward_transport
          (d := d) hd (u := u) (T := T) hu_norm htransport (y := y))
      y

/--
Set-level replacement of the pullback next shape by Chewi's displayed
`Σ_{n+1}^{-1}` update from the normalized forward-shape transport identity.
-/
theorem chewi620_ellipsoidSet_pullbackStandardCut_eq_displayedShapeUpdate_inv_of_forwardShape_transport
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    {u : EuclideanSpace ℝ ι}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hu_norm : ‖u‖ = 1)
    (htransport :
      ∀ x,
        matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p) (T.symm x) =
          T (chewi620StandardCutForwardShape d u x))
    (center : EuclideanSpace ℝ ι) :
    ellipsoidSet center (chewi620PullbackStandardCutInvShape d u T) =
      ellipsoidSet center
        (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹) := by
  exact
    chewi620_ellipsoidSet_pullbackStandardCut_eq_displayedShapeUpdate_inv_of_left_inverse
      (d := d) hd hcard hSigma hp
      (fun y =>
        chewi620_displayedShapeUpdate_left_inverse_of_standardCutForward_transport
          (d := d) hd (u := u) (T := T) hu_norm htransport (y := y))
      center

/--
Positive denominator for Chewi's normalized ellipsoid cut direction when the
forward shape matrix is positive definite and the cut vector is nonzero.
-/
theorem chewi620_matrix_cut_sqrt_inv_pos_of_posDef
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    0 < (Real.sqrt (inner ℝ p (matrixInvShape Sigma p)))⁻¹ := by
  exact inv_pos.mpr
    (Real.sqrt_pos.mpr
      (matrixInvShape_quadratic_pos_of_posDef hSigma hp))

/--
The positive scalar used to normalize Chewi's cut direction:
`1 / sqrt(<p, Sigma p>)`.
-/
noncomputable def chewi620MatrixCutScale
    (Sigma : Matrix ι ι ℝ) (p : EuclideanSpace ℝ ι) : ℝ :=
  (Real.sqrt (inner ℝ p (matrixInvShape Sigma p)))⁻¹

/-- The square of the cut-normalization scale is the inverse quadratic form. -/
theorem chewi620_matrixCutScale_mul_self_of_pos
    {Sigma : Matrix ι ι ℝ} {p : EuclideanSpace ℝ ι}
    (hq_pos : 0 < inner ℝ p (matrixInvShape Sigma p)) :
    chewi620MatrixCutScale Sigma p * chewi620MatrixCutScale Sigma p =
      (inner ℝ p (matrixInvShape Sigma p))⁻¹ := by
  let q : ℝ := inner ℝ p (matrixInvShape Sigma p)
  have hq_nonneg : 0 ≤ q := le_of_lt hq_pos
  have hsqrt_sq : Real.sqrt q * Real.sqrt q = q := by
    rw [← sq]
    exact Real.sq_sqrt hq_nonneg
  dsimp [chewi620MatrixCutScale]
  change (Real.sqrt q)⁻¹ * (Real.sqrt q)⁻¹ = q⁻¹
  calc
    (Real.sqrt q)⁻¹ * (Real.sqrt q)⁻¹ =
        (Real.sqrt q * Real.sqrt q)⁻¹ := by
      rw [mul_inv_rev]
    _ = q⁻¹ := by
      rw [hsqrt_sq]

/--
The normalized cut direction obtained from a supplied square-root factor
`sigmaHalfP`, intended to be `Σ_n^{1/2} p_n`.
-/
noncomputable def chewi620MatrixNormalizedCutDirection
    (Sigma : Matrix ι ι ℝ) (p sigmaHalfP : EuclideanSpace ℝ ι) :
    EuclideanSpace ℝ ι :=
  chewi620MatrixCutScale Sigma p • sigmaHalfP

/--
If the supplied square-root factor has squared norm `<p, Sigma p>`, then the
Chewi-normalized cut direction has unit norm.
-/
theorem chewi620_matrixNormalizedCutDirection_norm_of_posDef
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {p sigmaHalfP : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (hsigmaHalfP_norm :
      ‖sigmaHalfP‖ ^ (2 : ℕ) = inner ℝ p (matrixInvShape Sigma p)) :
    ‖chewi620MatrixNormalizedCutDirection Sigma p sigmaHalfP‖ = 1 := by
  have hquad_pos : 0 < inner ℝ p (matrixInvShape Sigma p) :=
    matrixInvShape_quadratic_pos_of_posDef hSigma hp
  have hsqrt_pos : 0 < Real.sqrt (inner ℝ p (matrixInvShape Sigma p)) :=
    Real.sqrt_pos.mpr hquad_pos
  have hscale_pos : 0 < chewi620MatrixCutScale Sigma p :=
    inv_pos.mpr hsqrt_pos
  have hsigmaHalfP_norm_eq_sqrt :
      Real.sqrt (inner ℝ p (matrixInvShape Sigma p)) = ‖sigmaHalfP‖ := by
    exact (Real.sqrt_eq_iff_eq_sq hquad_pos.le
      (norm_nonneg sigmaHalfP)).2 hsigmaHalfP_norm.symm
  rw [chewi620MatrixNormalizedCutDirection, norm_smul, Real.norm_eq_abs,
    abs_of_pos hscale_pos, ← hsigmaHalfP_norm_eq_sqrt]
  exact inv_mul_cancel₀ (ne_of_gt hsqrt_pos)

/--
Cut-normalization identity for Chewi Lemma 6.20.  The remaining matrix
square-root work is exactly the supplied raw identity
`<Σ^{1/2}p, Σ^{-1/2}(z-center)> = <p,z> - <p,center>`; this theorem turns it
into the `hcut` hypothesis required by
`chewi620_affineTransport_stepCertificate_of_quadratic`.
-/
theorem chewi620_matrixNormalizedCutDirection_inner_toStd
    {Sigma : Matrix ι ι ℝ} {p sigmaHalfP center : EuclideanSpace ℝ ι}
    {toStd : EuclideanSpace ℝ ι -> EuclideanSpace ℝ ι}
    (hraw :
      ∀ z,
        inner ℝ sigmaHalfP (toStd (z - center)) =
          inner ℝ p z - inner ℝ p center)
    (z : EuclideanSpace ℝ ι) :
    inner ℝ (chewi620MatrixNormalizedCutDirection Sigma p sigmaHalfP)
        (toStd (z - center)) =
      chewi620MatrixCutScale Sigma p *
        (inner ℝ p z - inner ℝ p center) := by
  rw [chewi620MatrixNormalizedCutDirection, inner_smul_left, hraw]
  simp

/--
Unit-norm wrapper for the normalized cut direction when the supplied vector is
the image of `p` under a square-root factor of the forward shape matrix.
-/
theorem chewi620_matrixSqrt_normalizedCutDirection_norm_of_posDef
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (hT_quadratic :
      ‖T p‖ ^ (2 : ℕ) = inner ℝ p (matrixInvShape Sigma p)) :
    ‖chewi620MatrixNormalizedCutDirection Sigma p (T p)‖ = 1 :=
  chewi620_matrixNormalizedCutDirection_norm_of_posDef
    (Sigma := Sigma) hSigma hp hT_quadratic

/--
The symmetric square-root raw-adjoint identity gives the `hcut` hypothesis
needed by `chewi620_affineTransport_stepCertificate_of_quadratic`.
-/
theorem chewi620_matrixSqrt_normalizedCutDirection_inner_toStd
    {Sigma : Matrix ι ι ℝ}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    (p center z : EuclideanSpace ℝ ι) :
    inner ℝ (chewi620MatrixNormalizedCutDirection Sigma p (T p))
        (T.symm (z - center)) =
      chewi620MatrixCutScale Sigma p *
        (inner ℝ p z - inner ℝ p center) :=
  chewi620_matrixNormalizedCutDirection_inner_toStd
    (Sigma := Sigma) (p := p) (sigmaHalfP := T p) (center := center)
    (toStd := fun y => T.symm y)
    (fun w =>
      chewi620_rawAdjointIdentity_of_symmetric_inverse
        (T := T) hT_symm p center w)
    z

/--
The square-root hypothesis transports the current displayed inverse-shape
action through the normalization map.
-/
theorem chewi620_matrixSqrt_current_action
    {Sigma : Matrix ι ι ℝ}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    (x : EuclideanSpace ℝ ι) :
    matrixInvShape Sigma (T.symm x) = T x := by
  simpa using (hT_sq (T.symm x)).symm

/--
The square-root symmetry transports the rank-one correction inner product from
displayed coordinates to normalized coordinates.
-/
theorem chewi620_matrixSqrt_rank_inner
    {Sigma : Matrix ι ι ℝ}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    (p x : EuclideanSpace ℝ ι) :
    inner ℝ (matrixInvShape Sigma p) (T.symm x) =
      inner ℝ (T p) x := by
  calc
    inner ℝ (matrixInvShape Sigma p) (T.symm x) =
        inner ℝ (T (T p)) (T.symm x) := by
      rw [← hT_sq p]
    _ = inner ℝ (T p) (T (T.symm x)) := by
      simpa using hT_symm (T p) (T.symm x)
    _ = inner ℝ (T p) x := by
      simp

/--
The square-root hypothesis identifies the norm of `T p` with Chewi's displayed
quadratic form `<p, Σ p>`.
-/
theorem chewi620_matrixSqrt_quadratic
    {Sigma : Matrix ι ι ℝ}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    (p : EuclideanSpace ℝ ι) :
    ‖T p‖ ^ (2 : ℕ) = inner ℝ p (matrixInvShape Sigma p) := by
  calc
    ‖T p‖ ^ (2 : ℕ) = inner ℝ (T p) (T p) := by
      rw [real_inner_self_eq_norm_sq]
    _ = inner ℝ p (T (T p)) := by
      exact hT_symm p (T p)
    _ = inner ℝ p (matrixInvShape Sigma p) := by
      rw [hT_sq p]

/--
Concrete displayed-to-normalized forward-shape transport for Chewi Lemma 6.20.
This discharges the matrix identity required by the compiled inverse-shape
transport reductions, assuming `T` is a symmetric square-root factor for the
displayed current shape matrix.
-/
theorem chewi620_displayedShapeUpdate_forwardShape_transport_of_sqrt
    {d : ℕ} {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (x : EuclideanSpace ℝ ι) :
    matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p) (T.symm x) =
      T (chewi620StandardCutForwardShape d
        (chewi620MatrixNormalizedCutDirection Sigma p (T p)) x) := by
  let q : ℝ := inner ℝ p (matrixInvShape Sigma p)
  let scale : ℝ := chewi620MatrixCutScale Sigma p
  let c : ℝ := (2 : ℝ) / ((d : ℝ) + 1)
  have hq_pos : 0 < q := by
    exact matrixInvShape_quadratic_pos_of_posDef hSigma hp
  have hscale_sq :
      scale * scale = q⁻¹ := by
    exact chewi620_matrixCutScale_mul_self_of_pos
      (Sigma := Sigma) (p := p) hq_pos
  have hscalar (r : ℝ) :
      ((((2 : ℝ) / ((d : ℝ) + 1)) /
          inner ℝ p ((Matrix.toEuclideanLin Sigma) p)) * r) =
        (((2 : ℝ) / ((d : ℝ) + 1) *
            (chewi620MatrixCutScale Sigma p * r)) *
          chewi620MatrixCutScale Sigma p) := by
    change (c / q) * r = (c * (scale * r)) * scale
    calc
      (c / q) * r = c * q⁻¹ * r := by rw [div_eq_mul_inv]
      _ = c * (scale * scale) * r := by rw [← hscale_sq]
      _ = (c * (scale * r)) * scale := by ring
  rw [chewi620_displayedShapeUpdate_action]
  rw [chewi620_matrixSqrt_current_action (Sigma := Sigma) (T := T) hT_sq x]
  rw [chewi620_matrixSqrt_rank_inner
    (Sigma := Sigma) (T := T) hT_symm hT_sq p x]
  simp [chewi620StandardCutForwardShape, chewi620MatrixNormalizedCutDirection,
    hT_sq, inner_smul_left, smul_sub, smul_smul]
  rw [hscalar (inner ℝ (T p) x)]

/--
Concrete displayed next inverse-shape equality under the symmetric square-root
hypotheses.  This packages the compiled transport theorem with the nonsingular
inverse reduction, closing the matrix-identification side of Lemma 6.20.
-/
theorem chewi620_pullbackStandardCutInvShape_eq_displayedShapeUpdate_inv_of_sqrt
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {p y : EuclideanSpace ℝ ι} (hp : p ≠ 0) :
    chewi620PullbackStandardCutInvShape d
        (chewi620MatrixNormalizedCutDirection Sigma p (T p)) T y =
      matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹ y := by
  exact
    chewi620_pullbackStandardCutInvShape_eq_displayedShapeUpdate_inv_of_forwardShape_transport
      (d := d) hd hcard hSigma hp
      (u := chewi620MatrixNormalizedCutDirection Sigma p (T p))
      (T := T)
      (chewi620_matrixSqrt_normalizedCutDirection_norm_of_posDef
        (Sigma := Sigma) hSigma hp
        (chewi620_matrixSqrt_quadratic
          (Sigma := Sigma) (T := T) hT_symm hT_sq p))
      (fun x =>
        chewi620_displayedShapeUpdate_forwardShape_transport_of_sqrt
          (d := d) (Sigma := Sigma) hSigma (T := T) hT_symm hT_sq hp x)
      (y := y)

/--
Set-level displayed next inverse-shape replacement under the symmetric
square-root hypotheses.
-/
theorem chewi620_ellipsoidSet_pullbackStandardCut_eq_displayedShapeUpdate_inv_of_sqrt
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (center : EuclideanSpace ℝ ι) :
    ellipsoidSet center
        (chewi620PullbackStandardCutInvShape d
          (chewi620MatrixNormalizedCutDirection Sigma p (T p)) T) =
      ellipsoidSet center
        (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹) := by
  ext z
  simp [ellipsoidSet,
    chewi620_pullbackStandardCutInvShape_eq_displayedShapeUpdate_inv_of_sqrt
      (d := d) hd hcard hSigma (T := T) hT_symm hT_sq hp
      (y := z - center)]

/--
The square-root hypothesis turns Chewi's normalized standard-cut center into
the displayed original-space center update
`x - (d+1)⁻¹ Σp / sqrt(<p, Σp>)`.
-/
theorem chewi620_matrixSqrt_centerUpdate_hcenter
    {d : ℕ} {Sigma : Matrix ι ι ℝ}
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    (center p : EuclideanSpace ℝ ι) :
    ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)) - center =
      T (chewi620StandardCutCenter d
        (chewi620MatrixNormalizedCutDirection Sigma p (T p))) := by
  simp [ellipsoidCenterUpdate, chewi620StandardCutCenter,
    chewi620MatrixNormalizedCutDirection, chewi620MatrixCutScale, hT_sq]
  module

/--
Square-root affine-transport certificate for Chewi Lemma 6.20 with the next
inverse-shape represented as the pullback of the normalized standard-cut
inverse-shape.  This discharges the current-ellipsoid, cut, and next-ellipsoid
quadratic identities; the remaining supplied hypothesis is the determinant/
volume calculation.
-/
theorem chewi620_sqrtAffineTransport_stepCertificate_of_pullback
    {d : ℕ} {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    {center nextCenter p : EuclideanSpace ℝ ι}
    (hd : 1 < d) (hp : p ≠ 0)
    (hT_quadratic :
      ‖T p‖ ^ (2 : ℕ) = inner ℝ p (matrixInvShape Sigma p))
    (hcenter :
      nextCenter - center =
        T (chewi620StandardCutCenter d
          (chewi620MatrixNormalizedCutDirection Sigma p (T p))))
    {vol volNext : ℝ}
    (hvolume : volNext ≤ ellipsoidVolumeRatio d * vol) :
    IsEllipsoidStepCertificate center nextCenter
      (chewi620PullbackIdentityInvShape T)
      (chewi620PullbackStandardCutInvShape d
        (chewi620MatrixNormalizedCutDirection Sigma p (T p)) T)
      p vol volNext (ellipsoidVolumeRatio d) := by
  refine
    chewi620_affineTransport_stepCertificate_of_quadratic
      (d := d) (center := center) (nextCenter := nextCenter)
      (invShape := chewi620PullbackIdentityInvShape T)
      (nextInvShape := chewi620PullbackStandardCutInvShape d
        (chewi620MatrixNormalizedCutDirection Sigma p (T p)) T)
      (p := p)
      (u := chewi620MatrixNormalizedCutDirection Sigma p (T p))
      (toStd := fun y => T.symm y)
      (scale := chewi620MatrixCutScale Sigma p)
      hd
      (chewi620_matrixSqrt_normalizedCutDirection_norm_of_posDef
        (Sigma := Sigma) hSigma hp hT_quadratic)
      (chewi620_matrix_cut_sqrt_inv_pos_of_posDef
        (Sigma := Sigma) hSigma hp)
      ?_ ?_ ?_ hvolume
  · intro z
    exact chewi620_pullbackIdentityInvShape_quadratic
      (T := T) hT_symm (z - center)
  · intro z
    exact chewi620_matrixSqrt_normalizedCutDirection_inner_toStd
      (Sigma := Sigma) (T := T) hT_symm p center z
  · intro z
    exact chewi620_pullbackStandardCutInvShape_hnext
      (d := d)
      (u := chewi620MatrixNormalizedCutDirection Sigma p (T p))
      (center := center) (nextCenter := nextCenter)
      (z := z) (T := T) hT_symm hcenter

/--
Square-root affine-transport certificate with Chewi's displayed center update
inserted.  The remaining supplied hypothesis is now only the determinant/volume
calculation and the matrix identification of the next inverse shape.
-/
theorem chewi620_sqrtAffineTransport_stepCertificate_of_displayedCenter
    {d : ℕ} {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    {center p : EuclideanSpace ℝ ι}
    (hd : 1 < d) (hp : p ≠ 0)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {vol volNext : ℝ}
    (hvolume : volNext ≤ ellipsoidVolumeRatio d * vol) :
    IsEllipsoidStepCertificate center
      (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
      (chewi620PullbackIdentityInvShape T)
      (chewi620PullbackStandardCutInvShape d
        (chewi620MatrixNormalizedCutDirection Sigma p (T p)) T)
      p vol volNext (ellipsoidVolumeRatio d) := by
  refine
    chewi620_sqrtAffineTransport_stepCertificate_of_pullback
      (Sigma := Sigma) hSigma (T := T) hT_symm
      (center := center)
      (nextCenter := ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
      (p := p) hd hp ?_ ?_ hvolume
  · calc
      ‖T p‖ ^ (2 : ℕ) = inner ℝ (T p) (T p) := by
        rw [real_inner_self_eq_norm_sq]
      _ = inner ℝ p (T (T p)) := by
        exact hT_symm p (T p)
      _ = inner ℝ p (matrixInvShape Sigma p) := by
        rw [hT_sq p]
  · exact chewi620_matrixSqrt_centerUpdate_hcenter
      (Sigma := Sigma) (T := T) hT_sq center p

/--
Chewi Lemma 6.20 certificate with the current ellipsoid written in the
source's displayed matrix form `Σ⁻¹` and the center update written in the
source's displayed form.  The next inverse shape is still the pullback of the
standard-cut inverse shape; identifying it with the displayed `Σ_{n+1}^{-1}`
matrix update is the next matrix-algebra blocker.
-/
theorem chewi620_sqrtAffineTransport_stepCertificate_of_displayedCurrentAndCenter
    {d : ℕ} {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    {center p : EuclideanSpace ℝ ι}
    (hd : 1 < d) (hp : p ≠ 0)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {vol volNext : ℝ}
    (hvolume : volNext ≤ ellipsoidVolumeRatio d * vol) :
    IsEllipsoidStepCertificate center
      (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
      (matrixInvShape Sigma⁻¹)
      (chewi620PullbackStandardCutInvShape d
        (chewi620MatrixNormalizedCutDirection Sigma p (T p)) T)
      p vol volNext (ellipsoidVolumeRatio d) := by
  have hcert :=
    chewi620_sqrtAffineTransport_stepCertificate_of_displayedCenter
      (Sigma := Sigma) hSigma (T := T) hT_symm
      (center := center) (p := p) hd hp hT_sq hvolume
  have hset :
      ellipsoidSet center (chewi620PullbackIdentityInvShape T) =
        ellipsoidSet center (matrixInvShape Sigma⁻¹) :=
    chewi620_ellipsoidSet_pullbackIdentity_eq_matrixInvShape_inv
      (Sigma := Sigma) hSigma hT_sq center
  simpa [IsEllipsoidStepCertificate, hset] using hcert

/--
Chewi Lemma 6.20 one-step certificate with both current and next ellipsoids in
the displayed matrix forms `Σ⁻¹` and `Σ_{n+1}^{-1}`.  The only remaining
external input is the real volume inequality `hvolume`.
-/
theorem chewi620_sqrtAffineTransport_stepCertificate_of_displayedMatrices
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    {center p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {vol volNext : ℝ}
    (hvolume : volNext ≤ ellipsoidVolumeRatio d * vol) :
    IsEllipsoidStepCertificate center
      (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
      (matrixInvShape Sigma⁻¹)
      (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹)
      p vol volNext (ellipsoidVolumeRatio d) := by
  have hcert :=
    chewi620_sqrtAffineTransport_stepCertificate_of_displayedCurrentAndCenter
      (Sigma := Sigma) hSigma (T := T) hT_symm
      (center := center) (p := p) hd hp hT_sq hvolume
  have hnext :
      ellipsoidSet
          (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
            (inner ℝ p (matrixInvShape Sigma p)))
          (chewi620PullbackStandardCutInvShape d
            (chewi620MatrixNormalizedCutDirection Sigma p (T p)) T) =
        ellipsoidSet
          (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
            (inner ℝ p (matrixInvShape Sigma p)))
          (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹) :=
    chewi620_ellipsoidSet_pullbackStandardCut_eq_displayedShapeUpdate_inv_of_sqrt
      (d := d) hd hcard hSigma (T := T) hT_symm hT_sq hp
      (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
  exact ⟨by
    intro z hz
    have hz' := hcert.1 hz
    rwa [hnext] at hz',
    hcert.2⟩

/--
Displayed-matrix Lemma 6.20 step certificate whose volume hypothesis is
discharged from translated matrix-image volume models and determinant-square
identities for the current and next square-root factors.
-/
theorem chewi620_displayedMatrices_stepCertificate_of_matrix_image_volume_models
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    {center p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {currentRoot nextRoot : Matrix ι ι ℝ}
    {baseSet : Set (EuclideanSpace ℝ ι)}
    {vol volNext : ℝ}
    (hcurrentRoot_det_sq :
      currentRoot.det ^ (2 : ℕ) = Sigma.det)
    (hnextRoot_det_sq :
      nextRoot.det ^ (2 : ℕ) =
        (chewi620DisplayedShapeUpdate d Sigma p).det)
    (hvol :
      vol =
        MeasureTheory.volume.real
          ((fun x => center + matrixInvShape currentRoot x) '' baseSet))
    (hvolNext :
      volNext =
        MeasureTheory.volume.real
          ((fun x =>
            ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
              (inner ℝ p (matrixInvShape Sigma p)) +
              matrixInvShape nextRoot x) '' baseSet)) :
    IsEllipsoidStepCertificate center
      (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
      (matrixInvShape Sigma⁻¹)
      (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹)
      p vol volNext (ellipsoidVolumeRatio d) := by
  refine
    chewi620_sqrtAffineTransport_stepCertificate_of_displayedMatrices
      (d := d) hd hcard hSigma (T := T) hT_symm
      (center := center) (p := p) hp hT_sq ?_
  exact
    chewi620_hvolume_of_matrix_image_volume_models
      (d := d) hd hcard hSigma hp
      (currentRoot := currentRoot) (nextRoot := nextRoot)
      (center := center)
      (nextCenter :=
        ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
          (inner ℝ p (matrixInvShape Sigma p)))
      (baseSet := baseSet)
      hcurrentRoot_det_sq hnextRoot_det_sq hvol hvolNext

/--
Displayed-matrix Lemma 6.20 step certificate with volumes stated directly as
displayed ellipsoid volumes.  The only remaining square-root inputs are the
quadratic identities showing that `currentRoot` and `nextRoot` parametrize the
current and next ellipsoids, plus their determinant-square identities.  This is
the source-facing bridge from the geometric ellipsoid statement to the compiled
determinant-volume theorem.
-/
theorem chewi620_displayedMatrices_stepCertificate_of_squareRoot_image_models
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    {center p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {currentRoot nextRoot : Matrix ι ι ℝ}
    {vol volNext : ℝ}
    (hcurrentRoot_det_sq :
      currentRoot.det ^ (2 : ℕ) = Sigma.det)
    (hnextRoot_det_sq :
      nextRoot.det ^ (2 : ℕ) =
        (chewi620DisplayedShapeUpdate d Sigma p).det)
    (hcurrentRoot_quad :
      ∀ y : EuclideanSpace ℝ ι,
        inner ℝ (matrixInvShape currentRoot y)
          (matrixInvShape Sigma⁻¹ (matrixInvShape currentRoot y)) =
            inner ℝ y y)
    (hnextRoot_quad :
      ∀ y : EuclideanSpace ℝ ι,
        inner ℝ (matrixInvShape nextRoot y)
          (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹
            (matrixInvShape nextRoot y)) = inner ℝ y y)
    (hvol :
      vol =
        MeasureTheory.volume.real
          (ellipsoidSet center (matrixInvShape Sigma⁻¹)))
    (hvolNext :
      volNext =
        MeasureTheory.volume.real
          (ellipsoidSet
            (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
              (inner ℝ p (matrixInvShape Sigma p)))
            (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹))) :
    IsEllipsoidStepCertificate center
      (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
      (matrixInvShape Sigma⁻¹)
      (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹)
      p vol volNext (ellipsoidVolumeRatio d) := by
  have hcurrentRoot_det_ne : currentRoot.det ≠ 0 := by
    intro hzero
    have hSigma_zero : Sigma.det = 0 := by
      rw [← hcurrentRoot_det_sq, hzero]
      norm_num
    exact (chewi620_matrixPosDef_det_ne_zero hSigma) hSigma_zero
  have hnextRoot_det_ne : nextRoot.det ≠ 0 := by
    intro hzero
    have hnext_zero :
        (chewi620DisplayedShapeUpdate d Sigma p).det = 0 := by
      rw [← hnextRoot_det_sq, hzero]
      norm_num
    exact
      (chewi620_displayedShapeUpdate_det_ne_zero
        (d := d) hd hcard hSigma hp) hnext_zero
  have hcurrentRoot_unit : IsUnit currentRoot.det :=
    isUnit_iff_ne_zero.mpr hcurrentRoot_det_ne
  have hnextRoot_unit : IsUnit nextRoot.det :=
    isUnit_iff_ne_zero.mpr hnextRoot_det_ne
  let unitBall : Set (EuclideanSpace ℝ ι) :=
    Metric.closedBall (0 : EuclideanSpace ℝ ι) 1
  have hvol_image :
      vol =
        MeasureTheory.volume.real
          ((fun x => center + matrixInvShape currentRoot x) '' unitBall) := by
    calc
      vol =
          MeasureTheory.volume.real
            (ellipsoidSet center (matrixInvShape Sigma⁻¹)) := hvol
      _ =
          MeasureTheory.volume.real
            ((fun x => center + matrixInvShape currentRoot x) '' unitBall) := by
        rw [ellipsoidSet_eq_matrix_image_closedBall_of_quadratic
          (A := Sigma) (root := currentRoot) hcurrentRoot_unit
          center hcurrentRoot_quad]
  have hvolNext_image :
      volNext =
        MeasureTheory.volume.real
          ((fun x =>
            ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
              (inner ℝ p (matrixInvShape Sigma p)) +
              matrixInvShape nextRoot x) '' unitBall) := by
    calc
      volNext =
          MeasureTheory.volume.real
            (ellipsoidSet
              (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
                (inner ℝ p (matrixInvShape Sigma p)))
              (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹)) :=
        hvolNext
      _ =
          MeasureTheory.volume.real
            ((fun x =>
              ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
                (inner ℝ p (matrixInvShape Sigma p)) +
                matrixInvShape nextRoot x) '' unitBall) := by
        rw [ellipsoidSet_eq_matrix_image_closedBall_of_quadratic
          (A := chewi620DisplayedShapeUpdate d Sigma p)
          (root := nextRoot) hnextRoot_unit
          (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
            (inner ℝ p (matrixInvShape Sigma p))) hnextRoot_quad]
  exact
    chewi620_displayedMatrices_stepCertificate_of_matrix_image_volume_models
      (d := d) hd hcard hSigma (T := T) hT_symm
      (center := center) (p := p) hp hT_sq
      (currentRoot := currentRoot) (nextRoot := nextRoot)
      (baseSet := unitBall)
      hcurrentRoot_det_sq hnextRoot_det_sq hvol_image hvolNext_image

/--
Displayed-matrix Lemma 6.20 step certificate with the volume model
instantiated by mathlib's CFC square roots.  The only remaining structural
input is positive-definiteness of Chewi's displayed next forward-shape matrix.
-/
theorem chewi620_displayedMatrices_stepCertificate_of_cfcSqrt_posDef
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    {center p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    (hnextPosDef :
      (chewi620DisplayedShapeUpdate d Sigma p).PosDef)
    {vol volNext : ℝ}
    (hvol :
      vol =
        MeasureTheory.volume.real
          (ellipsoidSet center (matrixInvShape Sigma⁻¹)))
    (hvolNext :
      volNext =
        MeasureTheory.volume.real
          (ellipsoidSet
            (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
              (inner ℝ p (matrixInvShape Sigma p)))
            (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹))) :
    IsEllipsoidStepCertificate center
      (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
      (matrixInvShape Sigma⁻¹)
      (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹)
      p vol volNext (ellipsoidVolumeRatio d) := by
  exact
    chewi620_displayedMatrices_stepCertificate_of_squareRoot_image_models
      (d := d) hd hcard hSigma (T := T) hT_symm
      (center := center) (p := p) hp hT_sq
      (currentRoot := CFC.sqrt Sigma)
      (nextRoot := CFC.sqrt (chewi620DisplayedShapeUpdate d Sigma p))
      (cfcSqrt_det_sq_of_posSemidef hSigma.posSemidef)
      (cfcSqrt_det_sq_of_posSemidef hnextPosDef.posSemidef)
      (cfcSqrt_quadratic_inv_of_posDef hSigma)
      (cfcSqrt_quadratic_inv_of_posDef hnextPosDef)
      hvol hvolNext

/--
Displayed-matrix Lemma 6.20 step certificate with CFC square roots and no
separate next-shape positivity hypothesis: the rank-one positivity theorem for
Chewi's displayed update discharges it.
-/
theorem chewi620_displayedMatrices_stepCertificate_of_cfcSqrt
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : Matrix ι ι ℝ} (hSigma : Sigma.PosDef)
    {T : EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : T.IsSymmetric)
    {center p : EuclideanSpace ℝ ι} (hp : p ≠ 0)
    (hT_sq : ∀ y, T (T y) = matrixInvShape Sigma y)
    {vol volNext : ℝ}
    (hvol :
      vol =
        MeasureTheory.volume.real
          (ellipsoidSet center (matrixInvShape Sigma⁻¹)))
    (hvolNext :
      volNext =
        MeasureTheory.volume.real
          (ellipsoidSet
            (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
              (inner ℝ p (matrixInvShape Sigma p)))
            (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹))) :
    IsEllipsoidStepCertificate center
      (ellipsoidCenterUpdate d center (matrixInvShape Sigma p)
        (inner ℝ p (matrixInvShape Sigma p)))
      (matrixInvShape Sigma⁻¹)
      (matrixInvShape (chewi620DisplayedShapeUpdate d Sigma p)⁻¹)
      p vol volNext (ellipsoidVolumeRatio d) := by
  exact
    chewi620_displayedMatrices_stepCertificate_of_cfcSqrt_posDef
      (d := d) hd hcard hSigma (T := T) hT_symm
      (center := center) (p := p) hp hT_sq
      (chewi620_displayedShapeUpdate_posDef
        (d := d) hd hSigma hp)
      hvol hvolNext

end EuclideanMatrix

/-- The localization sets generated by a sequence of ellipsoids. -/
def ellipsoidSets (center : ℕ -> E) (invShape : ℕ -> E -> E) :
    ℕ -> Set E :=
  fun n => ellipsoidSet (center n) (invShape n)

/-- Source-shaped trajectory certificate for Lemma 6.20 ellipsoid updates. -/
def IsEllipsoidCuttingPlaneTrajectory
    (center p : ℕ -> E) (invShape : ℕ -> E -> E)
    (vol : ℕ -> ℝ) (d : ℕ) : Prop :=
  ∀ n, IsEllipsoidStepCertificate
    (center n) (center (n + 1)) (invShape n) (invShape (n + 1))
    (p n) (vol n) (vol (n + 1)) (ellipsoidVolumeRatio d)

theorem IsEllipsoidCuttingPlaneTrajectory.step
    {center p : ℕ -> E} {invShape : ℕ -> E -> E}
    {vol : ℕ -> ℝ} {d n : ℕ}
    (h : IsEllipsoidCuttingPlaneTrajectory center p invShape vol d) :
    IsEllipsoidStepCertificate
      (center n) (center (n + 1)) (invShape n) (invShape (n + 1))
      (p n) (vol n) (vol (n + 1)) (ellipsoidVolumeRatio d) :=
  h n

theorem IsEllipsoidCuttingPlaneTrajectory.hasVolumeShrink
    {center p : ℕ -> E} {invShape : ℕ -> E -> E}
    {vol : ℕ -> ℝ} {d : ℕ}
    (h : IsEllipsoidCuttingPlaneTrajectory center p invShape vol d) :
    HasVolumeShrink vol (ellipsoidVolumeRatio d) := by
  intro n
  exact (h.step (n := n)).volume_le

theorem IsEllipsoidCuttingPlaneTrajectory.halfspace_subset
    {center p : ℕ -> E} {invShape : ℕ -> E -> E}
    {vol : ℕ -> ℝ} {d n : ℕ}
    (h : IsEllipsoidCuttingPlaneTrajectory center p invShape vol d) :
    ellipsoidSets center invShape n ∩ ellipsoidCutHalfspace (p n) (center n) ⊆
      ellipsoidSets center invShape (n + 1) := by
  simpa [ellipsoidSets] using
    (h.step (n := n)).halfspace_subset

section EuclideanMatrixTrajectory

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/--
Chewi Lemma 6.20, sequence form: if the displayed matrix iterates use Chewi's
center and shape updates, then the displayed ellipsoids form an ellipsoid
cutting-plane trajectory.
-/
theorem chewi620_displayedMatrices_trajectory_of_cfcSqrt
    {d : ℕ} (hd : 1 < d) (hcard : Fintype.card ι = d)
    {Sigma : ℕ -> Matrix ι ι ℝ}
    (hSigma : ∀ n, (Sigma n).PosDef)
    {T : ℕ -> EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : ∀ n, (T n).IsSymmetric)
    (hT_sq : ∀ n y, T n (T n y) = matrixInvShape (Sigma n) y)
    {center p : ℕ -> EuclideanSpace ℝ ι}
    (hp : ∀ n, p n ≠ 0)
    (hcenter_succ : ∀ n,
      center (n + 1) =
        ellipsoidCenterUpdate d (center n) (matrixInvShape (Sigma n) (p n))
          (inner ℝ (p n) (matrixInvShape (Sigma n) (p n))))
    (hSigma_succ : ∀ n,
      Sigma (n + 1) = chewi620DisplayedShapeUpdate d (Sigma n) (p n))
    {vol : ℕ -> ℝ}
    (hvol : ∀ n,
      vol n =
        MeasureTheory.volume.real
          (ellipsoidSet (center n) (matrixInvShape (Sigma n)⁻¹))) :
    IsEllipsoidCuttingPlaneTrajectory center p
      (fun n => matrixInvShape (Sigma n)⁻¹) vol d := by
  intro n
  have hvol_next :
      vol (n + 1) =
        MeasureTheory.volume.real
          (ellipsoidSet
            (ellipsoidCenterUpdate d (center n) (matrixInvShape (Sigma n) (p n))
              (inner ℝ (p n) (matrixInvShape (Sigma n) (p n))))
            (matrixInvShape (chewi620DisplayedShapeUpdate d (Sigma n) (p n))⁻¹)) := by
    calc
      vol (n + 1) =
          MeasureTheory.volume.real
            (ellipsoidSet (center (n + 1))
              (matrixInvShape (Sigma (n + 1))⁻¹)) := hvol (n + 1)
      _ =
          MeasureTheory.volume.real
            (ellipsoidSet
              (ellipsoidCenterUpdate d (center n) (matrixInvShape (Sigma n) (p n))
                (inner ℝ (p n) (matrixInvShape (Sigma n) (p n))))
              (matrixInvShape (chewi620DisplayedShapeUpdate d (Sigma n) (p n))⁻¹)) := by
        rw [hcenter_succ n, hSigma_succ n]
  have hstep :=
    chewi620_displayedMatrices_stepCertificate_of_cfcSqrt
      (d := d) hd hcard (hSigma n)
      (T := T n) (hT_symm n)
      (center := center n) (p := p n) (hp n)
      (hT_sq n) (hvol n) hvol_next
  simpa [hcenter_succ n, hSigma_succ n] using hstep

end EuclideanMatrixTrajectory

/-- Finite product consequence of the Lemma 6.20 volume-ratio certificate. -/
theorem ellipsoidTrajectory_volume_ratio_le_pow
    {center p : ℕ -> E} {invShape : ℕ -> E -> E}
    {vol : ℕ -> ℝ} {d N : ℕ}
    (h : IsEllipsoidCuttingPlaneTrajectory center p invShape vol d)
    (hvol0_pos : 0 < vol 0) :
    vol N / vol 0 ≤ ellipsoidVolumeRatio d ^ N :=
  volumeShrink_ratio_le_pow
    (ellipsoidVolumeRatio_nonneg d) hvol0_pos h.hasVolumeShrink

/--
Lemma 6.20 plugged into the source-shaped Theorem 6.19 wrapper: a verified
ellipsoid volume trajectory gives the finite volume ratio, and the supplied
candidate geometry gives the displayed optimization rate with the ellipsoid
volume factor.
-/
theorem chewi620_volume_ratio_and_gap_bound_of_scaled_candidates
    {C : Set E} {center p : ℕ -> E} {invShape : ℕ -> E -> E}
    {vol : ℕ -> ℝ} {f : E -> ℝ} {xStar : E}
    {N d : ℕ} {D L : ℝ}
    (htraj : IsEllipsoidCuttingPlaneTrajectory center p invShape vol d)
    (hvol0_pos : 0 < vol 0)
    (hconv : ConvexOn ℝ C f)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hxStar_mem : xStar ∈ C)
    (hcert :
      IsCuttingPlaneValueCertificate (ellipsoidSets center invShape) f center N)
    (hrate_lt_one :
      centerOfGravityRate (ellipsoidVolumeRatio d) N d < 1)
    (hD_nonneg : 0 ≤ D)
    (hL_nonneg : 0 ≤ L)
    (hcandidates :
      HasScaledOutsideCandidatesAbove C (ellipsoidSets center invShape) xStar N D
        (centerOfGravityRate (ellipsoidVolumeRatio d) N d)) :
    vol N / vol 0 ≤ ellipsoidVolumeRatio d ^ N ∧
      f (center (N - 1)) - f xStar ≤
        D * L * centerOfGravityRate (ellipsoidVolumeRatio d) N d := by
  constructor
  · exact ellipsoidTrajectory_volume_ratio_le_pow htraj hvol0_pos
  · exact
      chewi619_gap_le_display_rate_of_scaled_candidates
        (C := C) (sets := ellipsoidSets center invShape) (f := f)
        (x := center) (xStar := xStar) (N := N) (d := d)
        (D := D) (L := L) (lambda := ellipsoidVolumeRatio d)
        hconv hLip hxStar_mem hcert
        (ellipsoidVolumeRatio_nonneg d) hrate_lt_one
        hD_nonneg hL_nonneg hcandidates

section EuclideanMatrixTrajectory

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/--
Chewi Lemma 6.20 fed directly into the compiled center-of-gravity rate wrapper:
displayed ellipsoid updates give the finite volume-ratio bound and the
source-shaped optimization-rate conclusion.
-/
theorem chewi620_displayedMatrices_volume_ratio_and_gap_bound_of_scaled_candidates
    {C : Set (EuclideanSpace ℝ ι)}
    {center p : ℕ -> EuclideanSpace ℝ ι}
    {Sigma : ℕ -> Matrix ι ι ℝ}
    {vol : ℕ -> ℝ}
    {f : EuclideanSpace ℝ ι -> ℝ} {xStar : EuclideanSpace ℝ ι}
    {N d : ℕ} {D L : ℝ}
    (hd : 1 < d) (hcard : Fintype.card ι = d)
    (hSigma : ∀ n, (Sigma n).PosDef)
    {T : ℕ -> EuclideanSpace ℝ ι ≃ₗ[ℝ] EuclideanSpace ℝ ι}
    (hT_symm : ∀ n, (T n).IsSymmetric)
    (hT_sq : ∀ n y, T n (T n y) = matrixInvShape (Sigma n) y)
    (hp : ∀ n, p n ≠ 0)
    (hcenter_succ : ∀ n,
      center (n + 1) =
        ellipsoidCenterUpdate d (center n) (matrixInvShape (Sigma n) (p n))
          (inner ℝ (p n) (matrixInvShape (Sigma n) (p n))))
    (hSigma_succ : ∀ n,
      Sigma (n + 1) = chewi620DisplayedShapeUpdate d (Sigma n) (p n))
    (hvol : ∀ n,
      vol n =
        MeasureTheory.volume.real
          (ellipsoidSet (center n) (matrixInvShape (Sigma n)⁻¹)))
    (hvol0_pos : 0 < vol 0)
    (hconv : ConvexOn ℝ C f)
    (hLip : LipschitzOnWith (Real.toNNReal L) f C)
    (hxStar_mem : xStar ∈ C)
    (hcert :
      IsCuttingPlaneValueCertificate
        (ellipsoidSets center (fun n => matrixInvShape (Sigma n)⁻¹)) f center N)
    (hrate_lt_one :
      centerOfGravityRate (ellipsoidVolumeRatio d) N d < 1)
    (hD_nonneg : 0 ≤ D)
    (hL_nonneg : 0 ≤ L)
    (hcandidates :
      HasScaledOutsideCandidatesAbove C
        (ellipsoidSets center (fun n => matrixInvShape (Sigma n)⁻¹))
        xStar N D (centerOfGravityRate (ellipsoidVolumeRatio d) N d)) :
    vol N / vol 0 ≤ ellipsoidVolumeRatio d ^ N ∧
      f (center (N - 1)) - f xStar ≤
        D * L * centerOfGravityRate (ellipsoidVolumeRatio d) N d := by
  have htraj :
      IsEllipsoidCuttingPlaneTrajectory center p
        (fun n => matrixInvShape (Sigma n)⁻¹) vol d :=
    chewi620_displayedMatrices_trajectory_of_cfcSqrt
      (d := d) hd hcard hSigma (T := T) hT_symm hT_sq hp
      hcenter_succ hSigma_succ hvol
  exact
    chewi620_volume_ratio_and_gap_bound_of_scaled_candidates
      (C := C) (center := center) (p := p)
      (invShape := fun n => matrixInvShape (Sigma n)⁻¹)
      (vol := vol) (f := f) (xStar := xStar) (N := N) (d := d)
      (D := D) (L := L) htraj hvol0_pos hconv hLip hxStar_mem hcert
      hrate_lt_one hD_nonneg hL_nonneg hcandidates

end EuclideanMatrixTrajectory

end Optimization
end StatInference
