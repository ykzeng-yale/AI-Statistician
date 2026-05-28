import StatInference.Optimization.SchurSymmetry

/-!
# Chewi Proposition 13.11(4), inf-projection source surface

This module packages the current inf-projection route for Chewi Proposition
13.11(4).  The lower-level Schur and envelope lemmas live in
`InteriorPoint.lean` and `SchurSymmetry.lean`; the theorem-facing surface here
collects the source conclusions that downstream concrete examples need.
-/

namespace StatInference
namespace Optimization

section InfProjectionSourceSurface

variable {E₁ E₂ : Type*}
variable [NormedAddCommGroup E₁] [InnerProductSpace ℝ E₁]
variable [NormedAddCommGroup E₂] [InnerProductSpace ℝ E₂]
variable [CompleteSpace E₁]
variable [CompleteSpace (WithLp 2 (E₁ × E₂))]

/--
Canonical Schur-Hessian derivative used by the full-Hessian derivative route in
Chewi Proposition 13.11(4).  Naming it keeps theorem-facing surfaces from
repeating the long block-derivative expression.
-/
noncomputable def barrierInfProjectionCanonicalSchurDeriv
    (selector : E₁ -> E₂)
    (hess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂))
    (invHyy : E₁ -> E₂ →L[ℝ] E₂)
    (hessDeriv : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ]
        ((WithLp 2 (E₁ × E₂)) →L[ℝ] WithLp 2 (E₁ × E₂)))
    (dselector : E₁ -> E₁ →L[ℝ] E₂)
    (invHyyDeriv : E₁ -> E₁ →L[ℝ] (E₂ →L[ℝ] E₂)) :
    E₁ -> E₁ →L[ℝ] (E₁ →L[ℝ] E₁) :=
  fun x =>
    barrierInfProjectionSchurHessDeriv
      (barrierInfProjectionBlockXY selector hess)
      (barrierInfProjectionBlockYX selector hess)
      invHyy
      (fun x =>
        barrierInfProjectionBlockXXDeriv
          (hessDeriv (barrierInfProjectionPoint selector x)) (dselector x))
      (fun x =>
        barrierInfProjectionBlockXYDeriv
          (hessDeriv (barrierInfProjectionPoint selector x)) (dselector x))
      (fun x =>
        barrierInfProjectionBlockYXDeriv
          (hessDeriv (barrierInfProjectionPoint selector x)) (dselector x))
      invHyyDeriv x

/--
Source-facing conclusion package for Chewi Proposition 13.11(4).  It records
the three reusable outputs of the inf-projection theorem: the projected
self-concordant barrier, the literal-infimum third-order envelope, and the
projected local-norm sandwich used by downstream Dikin/Newton arguments.
-/
structure Chewi1311InfProjectionSourceSurface
    (s : Set (WithLp 2 (E₁ × E₂))) (f : WithLp 2 (E₁ × E₂) -> ℝ)
    (selector : E₁ -> E₂)
    (hess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂))
    (grad : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂))
    (invHess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂))
    (third : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) -> ℝ)
    (invHyy : E₁ -> E₂ →L[ℝ] E₂)
    (schurDeriv : E₁ -> E₁ →L[ℝ] (E₁ →L[ℝ] E₁)) (M nu : ℝ) : Prop where
  selfConcordantBarrierOn :
    SelfConcordantBarrierOn (barrierInfProjectionSet s)
      (barrierInfProjectionSchurHessFrom selector hess invHyy)
      (barrierInfProjectionGrad selector grad)
      (barrierInfProjectionProjInvHessFromFullInv selector invHess)
      (barrierInfProjectionSchurLiftedThird selector hess invHyy third) M nu
  literalThirdOrderEnvelopeOn :
    BarrierInfProjectionLiteralThirdOrderEnvelopeOn s f selector grad hess
      invHess third invHyy schurDeriv M nu
  projectedLocalNormSandwich :
    ∀ {x y v : E₁},
      M *
          localNorm (barrierInfProjectionSchurHessFrom selector hess invHyy)
            x (y - x) < 1 ->
      Convex ℝ (barrierInfProjectionSet s) ->
      x ∈ barrierInfProjectionSet s ->
      y ∈ barrierInfProjectionSet s ->
        (1 - M *
            localNorm (barrierInfProjectionSchurHessFrom selector hess invHyy)
              x (y - x)) *
            localNorm (barrierInfProjectionSchurHessFrom selector hess invHyy)
              x v ≤
          localNorm (barrierInfProjectionSchurHessFrom selector hess invHyy)
            y v ∧
            localNorm (barrierInfProjectionSchurHessFrom selector hess invHyy)
              y v ≤
              localNorm
                (barrierInfProjectionSchurHessFrom selector hess invHyy) x v /
                (1 - M *
                  localNorm
                    (barrierInfProjectionSchurHessFrom selector hess invHyy)
                      x (y - x))

theorem Chewi1311InfProjectionSourceSurface.infValue_hasGradientAt
    {s : Set (WithLp 2 (E₁ × E₂))}
    {f : WithLp 2 (E₁ × E₂) -> ℝ}
    {selector : E₁ -> E₂}
    {hess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {grad : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂)}
    {invHess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {third : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) -> ℝ}
    {invHyy : E₁ -> E₂ →L[ℝ] E₂}
    {schurDeriv : E₁ -> E₁ →L[ℝ] (E₁ →L[ℝ] E₁)} {M nu : ℝ}
    (hsurf :
      Chewi1311InfProjectionSourceSurface s f selector hess grad invHess
        third invHyy schurDeriv M nu)
    {x : E₁} (hx : x ∈ barrierInfProjectionSet s) :
    HasGradientAt (barrierInfProjectionInfValue (E₂ := E₂) f)
      (barrierInfProjectionGrad selector grad x) x :=
  hsurf.literalThirdOrderEnvelopeOn.infValue_hasGradientAt hx

theorem Chewi1311InfProjectionSourceSurface.grad_hasFDerivAt
    {s : Set (WithLp 2 (E₁ × E₂))}
    {f : WithLp 2 (E₁ × E₂) -> ℝ}
    {selector : E₁ -> E₂}
    {hess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {grad : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂)}
    {invHess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {third : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) -> ℝ}
    {invHyy : E₁ -> E₂ →L[ℝ] E₂}
    {schurDeriv : E₁ -> E₁ →L[ℝ] (E₁ →L[ℝ] E₁)} {M nu : ℝ}
    (hsurf :
      Chewi1311InfProjectionSourceSurface s f selector hess grad invHess
        third invHyy schurDeriv M nu)
    {x : E₁} (hx : x ∈ barrierInfProjectionSet s) :
    HasFDerivAt (barrierInfProjectionGrad selector grad)
      (barrierInfProjectionSchurHessFrom selector hess invHyy x) x :=
  hsurf.literalThirdOrderEnvelopeOn.grad_hasFDerivAt hx

theorem Chewi1311InfProjectionSourceSurface.schurHessDerivativeOn
    {s : Set (WithLp 2 (E₁ × E₂))}
    {f : WithLp 2 (E₁ × E₂) -> ℝ}
    {selector : E₁ -> E₂}
    {hess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {grad : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂)}
    {invHess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {third : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) -> ℝ}
    {invHyy : E₁ -> E₂ →L[ℝ] E₂}
    {schurDeriv : E₁ -> E₁ →L[ℝ] (E₁ →L[ℝ] E₁)} {M nu : ℝ}
    (hsurf :
      Chewi1311InfProjectionSourceSurface s f selector hess grad invHess
        third invHyy schurDeriv M nu) :
    BarrierInfProjectionSchurHessDerivativeOn s selector hess invHyy third
      schurDeriv :=
  hsurf.literalThirdOrderEnvelopeOn.schur_deriv

theorem Chewi1311InfProjectionSourceSurface.hessianSegmentPsi_hasDerivWithinAt_liftedThird
    {s : Set (WithLp 2 (E₁ × E₂))}
    {f : WithLp 2 (E₁ × E₂) -> ℝ}
    {selector : E₁ -> E₂}
    {hess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {grad : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂)}
    {invHess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {third : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) -> ℝ}
    {invHyy : E₁ -> E₂ →L[ℝ] E₂}
    {schurDeriv : E₁ -> E₁ →L[ℝ] (E₁ →L[ℝ] E₁)} {M nu : ℝ}
    (hsurf :
      Chewi1311InfProjectionSourceSurface s f selector hess grad invHess
        third invHyy schurDeriv M nu)
    {x y v : E₁} {t : ℝ} {u : Set ℝ}
    (hz : hessianSegmentPoint x y t ∈ barrierInfProjectionSet s) :
    HasDerivWithinAt
      (hessianSegmentPsi
        (barrierInfProjectionSchurHessFrom selector hess invHyy) x y v)
      (hessianSegmentMixedThirdPsiDeriv
        (barrierInfProjectionSchurLiftedThird selector hess invHyy third)
        x y v t) u t :=
  hsurf.literalThirdOrderEnvelopeOn.schur_deriv
    |>.hessianSegmentPsi_hasDerivWithinAt_liftedThird hz

/--
Chewi Proposition 13.11(4), theorem-facing full-Hessian derivative surface.
This combines the already verified sourceFullSqrt barrier theorem, literal
infimum envelope theorem, and projected local-norm sandwich theorem.
-/
theorem chewi1311_infProjection_sourceSurface_of_sourceFullSqrtFirstSecondFullHessianDerivative
    [FiniteDimensional ℝ E₂] [CompleteSpace E₂]
    {s : Set (WithLp 2 (E₁ × E₂))}
    {f : WithLp 2 (E₁ × E₂) -> ℝ}
    {selector : E₁ -> E₂}
    {hess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {grad : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂)}
    {invHess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {third : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) -> ℝ}
    {invHyy : E₁ -> E₂ →L[ℝ] E₂}
    {sqrtFull : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) ≃L[ℝ] WithLp 2 (E₁ × E₂)}
    {sqrtHyy : E₁ -> E₂ ≃L[ℝ] E₂} {M nu : ℝ}
    {hessDeriv : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ]
        ((WithLp 2 (E₁ × E₂)) →L[ℝ] WithLp 2 (E₁ × E₂))}
    {dselector : E₁ -> E₁ →L[ℝ] E₂}
    {invHyyDeriv : E₁ -> E₁ →L[ℝ] (E₂ →L[ℝ] E₂)}
    (hsel : BarrierInfProjectionSelectorStationary s selector grad)
    (hbar : SelfConcordantBarrierOn s hess grad invHess third M nu)
    (hopen : IsOpen (barrierInfProjectionSet s))
    (hyy_hess_eq : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      barrierInfProjectionBlockYY selector hess x =
        (ContinuousLinearMap.adjoint (sqrtHyy x).toContinuousLinearMap).comp
          (sqrtHyy x).toContinuousLinearMap)
    (hyy_inv_eq : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      invHyy x =
        (sqrtHyy x).symm.toContinuousLinearMap.comp
          (ContinuousLinearMap.adjoint
            (sqrtHyy x).symm.toContinuousLinearMap))
    (hfull_hess_eq_source :
      ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
        hess z =
          (ContinuousLinearMap.adjoint (sqrtFull z).toContinuousLinearMap).comp
            (sqrtFull z).toContinuousLinearMap)
    (hfull_inv_eq_source :
      ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
        invHess z =
          (sqrtFull z).symm.toContinuousLinearMap.comp
            (ContinuousLinearMap.adjoint
              (sqrtFull z).symm.toContinuousLinearMap))
    (hfirst : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      FirstOrderStrongConvexOn Set.univ
        (fun y : E₂ => f (WithLp.toLp 2 (x, y)))
        (fun y : E₂ => (grad (WithLp.toLp 2 (x, y))).snd) 0)
    (hfgrad : ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
      HasGradientAt f (grad z) z)
    (hgrad : ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
      HasFDerivAt grad (hess z) z)
    (hhess : ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
      HasFDerivAt hess (hessDeriv z) z)
    (hmixed : ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
      ∀ a v : WithLp 2 (E₁ × E₂),
        inner ℝ v ((hessDeriv z a) v) = third z a v)
    (hselector : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      HasFDerivAt selector (dselector x) x)
    (hinvDeriv : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      HasFDerivAt invHyy (invHyyDeriv x) x) :
    Chewi1311InfProjectionSourceSurface s f selector hess grad invHess third
      invHyy
      (barrierInfProjectionCanonicalSchurDeriv
        selector hess invHyy hessDeriv dselector invHyyDeriv)
      M nu := by
  refine ⟨?_, ?_, ?_⟩
  · exact
      chewi1311_infProjection_selfConcordantBarrierOn_of_sourceFullSqrt
        hsel hbar hyy_hess_eq hyy_inv_eq hfull_hess_eq_source
        hfull_inv_eq_source
  · simpa [barrierInfProjectionCanonicalSchurDeriv] using
      chewi1311_infProjection_literalThirdOrderEnvelopeOn_of_sourceFullSqrtFirstSecondFullHessianDerivative
        (f := f) hsel hbar hopen hyy_hess_eq hyy_inv_eq
        hfull_hess_eq_source hfull_inv_eq_source hfirst hfgrad hgrad
        hhess hmixed hselector hinvDeriv
  · intro x y v hMr_lt hs hx hy
    simpa [barrierInfProjectionCanonicalSchurDeriv] using
      chewi1311_infProjection_literal_projected_localNorm_sandwich_sourceRadius_of_sourceFullSqrtFirstSecondFullHessianDerivative
        (f := f) (x := x) (y := y) (v := v)
        hsel hbar hopen hyy_hess_eq hyy_inv_eq
        hfull_hess_eq_source hfull_inv_eq_source hfirst hfgrad hgrad
        hhess hmixed hselector hinvDeriv hMr_lt hs hx hy

/--
Chewi Proposition 13.11(4), theorem-facing surface when the Schur-Hessian
derivative certificate has already been proved separately.
-/
theorem chewi1311_infProjection_sourceSurface_of_sourceFullSqrtFirstSecondSchurHessDerivativeOn
    [FiniteDimensional ℝ E₂] [CompleteSpace E₂]
    {s : Set (WithLp 2 (E₁ × E₂))}
    {f : WithLp 2 (E₁ × E₂) -> ℝ}
    {selector : E₁ -> E₂}
    {hess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {grad : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂)}
    {invHess : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) →L[ℝ] WithLp 2 (E₁ × E₂)}
    {third : WithLp 2 (E₁ × E₂) -> WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) -> ℝ}
    {invHyy : E₁ -> E₂ →L[ℝ] E₂}
    {sqrtFull : WithLp 2 (E₁ × E₂) ->
      WithLp 2 (E₁ × E₂) ≃L[ℝ] WithLp 2 (E₁ × E₂)}
    {sqrtHyy : E₁ -> E₂ ≃L[ℝ] E₂} {M nu : ℝ}
    {dselector : E₁ -> E₁ →L[ℝ] E₂}
    {schurDeriv : E₁ -> E₁ →L[ℝ] (E₁ →L[ℝ] E₁)}
    (hsel : BarrierInfProjectionSelectorStationary s selector grad)
    (hbar : SelfConcordantBarrierOn s hess grad invHess third M nu)
    (hopen : IsOpen (barrierInfProjectionSet s))
    (hyy_hess_eq : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      barrierInfProjectionBlockYY selector hess x =
        (ContinuousLinearMap.adjoint (sqrtHyy x).toContinuousLinearMap).comp
          (sqrtHyy x).toContinuousLinearMap)
    (hyy_inv_eq : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      invHyy x =
        (sqrtHyy x).symm.toContinuousLinearMap.comp
          (ContinuousLinearMap.adjoint
            (sqrtHyy x).symm.toContinuousLinearMap))
    (hfull_hess_eq_source :
      ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
        hess z =
          (ContinuousLinearMap.adjoint (sqrtFull z).toContinuousLinearMap).comp
            (sqrtFull z).toContinuousLinearMap)
    (hfull_inv_eq_source :
      ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
        invHess z =
          (sqrtFull z).symm.toContinuousLinearMap.comp
            (ContinuousLinearMap.adjoint
              (sqrtFull z).symm.toContinuousLinearMap))
    (hfirst : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      FirstOrderStrongConvexOn Set.univ
        (fun y : E₂ => f (WithLp.toLp 2 (x, y)))
        (fun y : E₂ => (grad (WithLp.toLp 2 (x, y))).snd) 0)
    (hfgrad : ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
      HasGradientAt f (grad z) z)
    (hgrad : ∀ ⦃z : WithLp 2 (E₁ × E₂)⦄, z ∈ s ->
      HasFDerivAt grad (hess z) z)
    (hselector : ∀ ⦃x : E₁⦄, x ∈ barrierInfProjectionSet s ->
      HasFDerivAt selector (dselector x) x)
    (hschur :
      BarrierInfProjectionSchurHessDerivativeOn s selector hess invHyy third
        schurDeriv) :
    Chewi1311InfProjectionSourceSurface s f selector hess grad invHess third
      invHyy schurDeriv M nu := by
  refine ⟨?_, ?_, ?_⟩
  · exact
      chewi1311_infProjection_selfConcordantBarrierOn_of_sourceFullSqrt
        hsel hbar hyy_hess_eq hyy_inv_eq hfull_hess_eq_source
        hfull_inv_eq_source
  · exact
      chewi1311_infProjection_literalThirdOrderEnvelopeOn_of_sourceFullSqrtFirstSecondSchurHessDerivativeOn
        (f := f) hsel hbar hopen hyy_hess_eq hyy_inv_eq
        hfull_hess_eq_source hfull_inv_eq_source hfirst hfgrad hgrad
        hselector hschur
  · intro x y v hMr_lt hs hx hy
    exact
      chewi1311_infProjection_literal_projected_localNorm_sandwich_sourceRadius_of_sourceFullSqrtFirstSecondSchurHessDerivativeOn
        (f := f) (x := x) (y := y) (v := v)
        hsel hbar hopen hyy_hess_eq hyy_inv_eq
        hfull_hess_eq_source hfull_inv_eq_source hfirst hfgrad hgrad
        hselector hschur hMr_lt hs hx hy

end InfProjectionSourceSurface

end Optimization
end StatInference
