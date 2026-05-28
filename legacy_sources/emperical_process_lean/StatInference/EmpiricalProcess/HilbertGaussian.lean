import Mathlib.MeasureTheory.Function.L2Space
import Mathlib.Probability.Distributions.Gaussian.IsGaussianProcess.Basic

/-!
# Hilbert and Gaussian foundation wrappers

This module records Chapter 1 Hilbert-space and Gaussian-process primitives in
project-local names while delegating the mathematical content to pinned mathlib
APIs.
-/

namespace StatInference

open MeasureTheory ProbabilityTheory

/-- A complete inner product space is a Hilbert space. -/
def vdVWHilbertSpace_of_complete_innerProductSpace
    (K H : Type*) [RCLike K] [NormedAddCommGroup H]
    [InnerProductSpace K H] [CompleteSpace H] :
    HilbertSpace K H := by
  exact {}

/-- The `L^2` space over a Hilbert space is a Hilbert space. -/
def vdVWL2_hilbertSpace
    (K : Type*) {alpha E : Type*} [RCLike K] [MeasurableSpace alpha]
    {mu : Measure alpha} [NormedAddCommGroup E] [InnerProductSpace K E]
    [CompleteSpace E] :
    HilbertSpace K (Lp E 2 mu) := by
  exact {}

/-- The `L^2` inner product is the integral of the pointwise inner product. -/
theorem vdVWL2_inner_def
    {K alpha E : Type*} [RCLike K] [MeasurableSpace alpha] {mu : Measure alpha}
    [NormedAddCommGroup E] [InnerProductSpace K E]
    (f g : Lp E 2 mu) :
    inner K f g = integral mu (fun x => inner K (f x) (g x)) := by
  exact MeasureTheory.L2.inner_def f g

/-- The Frechet-Riesz representative of a continuous linear functional on a Hilbert space. -/
noncomputable def vdVWHilbertDualRepresentative
    {K H : Type*} [RCLike K] [NormedAddCommGroup H]
    [InnerProductSpace K H] [CompleteSpace H]
    (L : StrongDual K H) : H :=
  (InnerProductSpace.toDual K H).symm L

/-- The Hilbert dual representative evaluates by the inner product. -/
theorem vdVWHilbertDualRepresentative_apply
    {K H : Type*} [RCLike K] [NormedAddCommGroup H]
    [InnerProductSpace K H] [CompleteSpace H]
    (L : StrongDual K H) (x : H) :
    inner K (vdVWHilbertDualRepresentative L) x = L x := by
  exact InnerProductSpace.toDual_symm_apply

/-- Every continuous linear functional on a Hilbert space is represented by inner product. -/
theorem vdVWHilbertDualRepresentation
    {K H : Type*} [RCLike K] [NormedAddCommGroup H]
    [InnerProductSpace K H] [CompleteSpace H]
    (L : StrongDual K H) :
    exists y : H, forall x : H, L x = inner K y x := by
  refine ⟨vdVWHilbertDualRepresentative L, ?_⟩
  intro x
  symm
  exact vdVWHilbertDualRepresentative_apply L x

/--
Mapping a Gaussian Hilbert-space law by an inner-product coordinate gives the
corresponding real Gaussian law.
-/
theorem vdVWGaussian_inner_map_eq_gaussianReal
    {H : Type*} [NormedAddCommGroup H] [InnerProductSpace ℝ H]
    [MeasurableSpace H] {mu : Measure H} [IsGaussian mu] (h : H) :
    mu.map (fun x : H => inner ℝ h x) =
      gaussianReal (mu[fun x : H => inner ℝ h x])
        (Var[fun x : H => inner ℝ h x; mu]).toNNReal := by
  simpa [InnerProductSpace.toDualMap] using
    (IsGaussian.map_eq_gaussianReal (μ := mu) (InnerProductSpace.toDualMap ℝ H h))

/-- Inner-product coordinates of Hilbert-valued Gaussian random variables are Gaussian. -/
theorem vdVWHasGaussianLaw_inner
    {Omega H : Type*} [MeasurableSpace Omega]
    [NormedAddCommGroup H] [InnerProductSpace ℝ H]
    [MeasurableSpace H] [BorelSpace H]
    {P : Measure Omega} {X : Omega -> H} (hX : HasGaussianLaw X P) (h : H) :
    HasGaussianLaw (fun omega => inner ℝ h (X omega)) P := by
  exact hX.map_fun (InnerProductSpace.toDualMap ℝ H h)

/-- Every coordinate of a Gaussian process has a Gaussian law. -/
theorem vdVWGaussianProcess_eval
    {Omega E T : Type*} [MeasurableSpace Omega]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E]
    {P : Measure Omega} {X : T -> Omega -> E}
    (hX : IsGaussianProcess X P) (t : T) :
    HasGaussianLaw (X t) P := by
  exact hX.hasGaussianLaw_eval t

end StatInference
