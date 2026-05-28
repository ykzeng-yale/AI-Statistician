import StatInference.Optimization.LogDetBarrierInterior

/-!
# Source-facing PSD log-det barrier surface

This module bundles the verified pieces of Chewi Example 13.14(2): the actual
barrier value `X ↦ -log det X`, the supplied Frobenius self-concordant-barrier
certificate, the line-derivative bridges identifying the supplied oracles with
the source value, and the corrected Hermitian-subtype interior identity.
-/

namespace StatInference
namespace Optimization

open scoped MatrixOrder Matrix.Norms.Frobenius

/-- Source value formula for Chewi Example 13.14(2). -/
def matrixLogDetBarrierValueFormula (d : ℕ) : Prop :=
  ∀ X : Matrix (Fin d) (Fin d) ℝ,
    matrixNegLogDetBarrier X = -Real.log X.det

/-- Determinant positivity on the positive-definite domain. -/
def matrixLogDetBarrierDetPositiveOnCone (d : ℕ) : Prop :=
  ∀ ⦃X : Matrix (Fin d) (Fin d) ℝ⦄,
    X ∈ matrixPosDefCone d -> 0 < X.det

/-- Frobenius-scoped supplied-oracle self-concordant-barrier certificate. -/
def matrixLogDetFrobeniusSelfConcordantBarrier (d : ℕ) : Prop :=
  letI : InnerProductSpace ℝ (Matrix (Fin d) (Fin d) ℝ) :=
    matrixFrobeniusInnerProductSpace
  SelfConcordantBarrierOn (matrixPosDefCone d)
    matrixLogDetHess matrixLogDetGrad matrixLogDetInvHess
    matrixLogDetThirdMixed 1 (d : ℝ)

/-- Actual-value first line derivative surface. -/
def matrixLogDetValueLineDerivativeSurface (d : ℕ) : Prop :=
  ∀ ⦃X U : Matrix (Fin d) (Fin d) ℝ⦄,
    X ∈ matrixPosDefCone d ->
      HasDerivAt (fun t : ℝ => matrixNegLogDetBarrier (X + t • U))
        (matrixFrobeniusInner (matrixLogDetGrad X) U) 0

/-- Supplied-gradient line derivative surface. -/
def matrixLogDetGradientLineDerivativeSurface (d : ℕ) : Prop :=
  ∀ ⦃X U : Matrix (Fin d) (Fin d) ℝ⦄,
    X ∈ matrixPosDefCone d ->
      HasDerivAt (fun t : ℝ => matrixLogDetGrad (X + t • U))
        (matrixLogDetHess X U) 0

/-- Hessian-quadratic line derivative surface. -/
def matrixLogDetHessianQuadraticLineDerivativeSurface (d : ℕ) : Prop :=
  ∀ ⦃X U V : Matrix (Fin d) (Fin d) ℝ⦄,
    X ∈ matrixPosDefCone d -> V.IsHermitian ->
      HasDerivAt
        (fun t : ℝ =>
          matrixFrobeniusInner V (matrixLogDetHess (X + t • U) V))
        (matrixLogDetThirdMixed X U V) 0

/-- Source value formula for Chewi Example 13.14(2). -/
theorem matrixLogDetBarrierValueFormula_holds {d : ℕ} :
    matrixLogDetBarrierValueFormula d :=
  matrixNegLogDetBarrier_eq_neg_log_det

/-- Determinant positivity on the positive-definite domain. -/
theorem matrixLogDetBarrierDetPositiveOnCone_holds {d : ℕ} :
    matrixLogDetBarrierDetPositiveOnCone d := by
  intro X hX
  exact matrixNegLogDetBarrier_det_pos_of_mem_posDefCone hX

/-- Frobenius-scoped supplied-oracle self-concordant-barrier certificate. -/
theorem matrixLogDetFrobeniusSelfConcordantBarrier_holds {d : ℕ} :
    matrixLogDetFrobeniusSelfConcordantBarrier d :=
  matrixLogDet_selfConcordantBarrierOn

/-- Actual-value first line derivative surface. -/
theorem matrixLogDetValueLineDerivativeSurface_holds {d : ℕ} :
    matrixLogDetValueLineDerivativeSurface d := by
  intro X U hX
  exact matrixNegLogDetBarrier_line_hasDerivAt_zero_of_mem_posDefCone hX

/-- Supplied-gradient line derivative surface. -/
theorem matrixLogDetGradientLineDerivativeSurface_holds {d : ℕ} :
    matrixLogDetGradientLineDerivativeSurface d := by
  intro X U hX
  exact matrixLogDetGrad_line_hasDerivAt_zero_of_mem_posDefCone hX

/-- Hessian-quadratic line derivative surface. -/
theorem matrixLogDetHessianQuadraticLineDerivativeSurface_holds {d : ℕ} :
    matrixLogDetHessianQuadraticLineDerivativeSurface d := by
  intro X U V hX hV
  exact
    matrixLogDetHess_quadratic_frobenius_line_hasDerivAt_zero_of_mem_posDefCone
      hX hV

/--
Source-facing bundle for Chewi Example 13.14(2), the PSD log-det barrier.
The interior field is the L2-operator-topology Hermitian-subtype identity from
`LogDetBarrierInterior`, while the self-concordance field uses the Frobenius
inner-product structure used by the supplied matrix oracles.
-/
structure Chewi1314MatrixLogDetBarrierSourceSurface
    (d : ℕ) [DecidableEq (Fin d)] [Nonempty (Fin d)] : Prop where
  value_eq_neg_log_det : matrixLogDetBarrierValueFormula d
  det_pos_of_mem_posDefCone : matrixLogDetBarrierDetPositiveOnCone d
  hermitian_interior_eq_posDef_l2 :
    matrixHermitianPsdInteriorEqPosDefL2 d
  self_concordant_barrier : matrixLogDetFrobeniusSelfConcordantBarrier d
  value_line_hasDerivAt : matrixLogDetValueLineDerivativeSurface d
  gradient_line_hasDerivAt : matrixLogDetGradientLineDerivativeSurface d
  hessian_quadratic_line_hasDerivAt :
    matrixLogDetHessianQuadraticLineDerivativeSurface d

/--
Chewi Example 13.14(2), source-facing PSD log-det barrier theorem surface.
-/
theorem chewi1314_matrixLogDetBarrier_sourceSurface
    {d : ℕ} [DecidableEq (Fin d)] [Nonempty (Fin d)] :
    Chewi1314MatrixLogDetBarrierSourceSurface d where
  value_eq_neg_log_det := matrixLogDetBarrierValueFormula_holds
  det_pos_of_mem_posDefCone := matrixLogDetBarrierDetPositiveOnCone_holds
  hermitian_interior_eq_posDef_l2 := matrixHermitianPsdInteriorEqPosDefL2_holds
  self_concordant_barrier := matrixLogDetFrobeniusSelfConcordantBarrier_holds
  value_line_hasDerivAt := matrixLogDetValueLineDerivativeSurface_holds
  gradient_line_hasDerivAt := matrixLogDetGradientLineDerivativeSurface_holds
  hessian_quadratic_line_hasDerivAt :=
    matrixLogDetHessianQuadraticLineDerivativeSurface_holds

end Optimization
end StatInference
