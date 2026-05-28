import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Matching.WDSM.ConditionalOrthogonalityBridge
import Mathlib.Probability.Martingale.Basic
import Mathlib.Probability.Process.Predictable

/-!
# Residual martingale-difference bridge interfaces

The residual martingale CLT input contains a raw
`martingale_difference_array` premise.  The WDSM proof should not leave that
premise anonymous: it should be derived from predictable matching
coefficients, conditional mean-zero residuals, arm/sampling regularity, and
finite-array integrability.  This module names that remaining probability
obligation as a reusable bridge while retaining the already proved
measure-theoretic residual mean-zero lemmas from `ConditionalResidualBridge`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

/--
One-arm martingale-difference bridge for residual matching contributions.

This is a probability-layer interface: later work must prove the bridge from
the relevant filtration and sampling design.  It makes the raw martingale
difference assumption auditable by exposing the expected WDSM components.
-/
structure ResidualMartingaleDifferenceBridge where
  coefficient_predictability : Prop
  residual_conditional_mean_zero : Prop
  sampling_or_filtration_regular : Prop
  finite_array_integrability : Prop
  martingale_difference_array : Prop
  bridge :
    coefficient_predictability ->
    residual_conditional_mean_zero ->
    sampling_or_filtration_regular ->
    finite_array_integrability ->
    martingale_difference_array

/-- Close a one-arm martingale-difference premise from its named components. -/
theorem martingale_difference_array_of_residual_bridge
    (b : ResidualMartingaleDifferenceBridge)
    (hpredictable : b.coefficient_predictability)
    (hzero : b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability) :
    b.martingale_difference_array :=
  b.bridge hpredictable hzero hregular hintegrable

/--
Adapter from a one-arm residual martingale-difference bridge to a concrete
`ResidualMartingaleArrayCLTVarianceInput`.
-/
theorem input_martingale_difference_array_of_residual_bridge
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : ResidualMartingaleDifferenceBridge)
    (hmap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hpredictable : b.coefficient_predictability)
    (hzero : b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability) :
    input.martingale_difference_array :=
  hmap
    (martingale_difference_array_of_residual_bridge b
      hpredictable hzero hregular hintegrable)

/--
Adapter from a one-arm residual martingale-difference bridge to an explicit
triangular martingale-array CLT bridge.
-/
theorem triangular_martingale_difference_array_of_residual_bridge
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : ResidualMartingaleDifferenceBridge)
    (hmap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (hpredictable : b.coefficient_predictability)
    (hzero : b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability) :
    martingaleCLT.martingale_difference_array :=
  hmap
    (martingale_difference_array_of_residual_bridge b
      hpredictable hzero hregular hintegrable)

/--
Residual CLT/variance input closed through a one-arm residual
martingale-difference bridge.
-/
theorem residual_clt_and_variance_formula_of_residual_bridge_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : ResidualMartingaleDifferenceBridge)
    (hmap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hpredictable : b.coefficient_predictability)
    (hzero : b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_residual_bridge input b hmap
      hpredictable hzero hregular hintegrable)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through a one-arm residual
martingale-difference bridge.  This discharges the triangular
martingale-difference field from the named WDSM residual bridge while keeping
the triangular Lindeberg and predictable-QV fields explicit.
-/
theorem residual_clt_and_variance_formula_of_residual_bridge_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : ResidualMartingaleDifferenceBridge)
    (hmap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (hpredictable : b.coefficient_predictability)
    (hzero : b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_residual_bridge
      martingaleCLT b hmap hpredictable hzero hregular hintegrable)
    hlindeberg hquad

/-!
## Mathlib martingale adapters

The WDSM residual CLT interface is intentionally paper-specific, but its
martingale-difference pieces should be discharged from Mathlib martingale
certificates whenever a concrete filtration and array have been built.  The
lemmas below connect that concrete Mathlib layer to the existing named WDSM
bridge without asserting the martingale-array CLT itself.
-/

/--
Close the one-arm coefficient-predictability component from a concrete
Mathlib `StronglyAdapted` certificate for an array process.
-/
theorem coefficient_predictability_component_of_stronglyAdapted_process
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : ResidualMartingaleDifferenceBridge)
    (process : ι -> Ω -> E)
    (hadapted : StronglyAdapted ℱ process)
    (hmap :
      StronglyAdapted ℱ process -> b.coefficient_predictability) :
    b.coefficient_predictability :=
  hmap hadapted

/--
Close the one-arm coefficient-predictability component from a concrete
Mathlib `Martingale`; Mathlib supplies strong adaptedness.
-/
theorem coefficient_predictability_component_of_mathlib_martingale
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : ResidualMartingaleDifferenceBridge)
    (process : ι -> Ω -> E)
    (hmartingale : Martingale process ℱ μ)
    (hmap :
      StronglyAdapted ℱ process -> b.coefficient_predictability) :
    b.coefficient_predictability :=
  hmap hmartingale.stronglyAdapted

/--
Close the one-arm finite-array integrability component from a concrete
Mathlib `Martingale`; Mathlib supplies integrability of every time slice.
-/
theorem finite_array_integrability_component_of_mathlib_martingale
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : ResidualMartingaleDifferenceBridge)
    (process : ι -> Ω -> E)
    (hmartingale : Martingale process ℱ μ)
    (hmap :
      (∀ i, Integrable (process i) μ) ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  hmap fun i => hmartingale.integrable i

/--
Close the one-arm residual conditional-mean-zero component from the Mathlib
martingale identity `μ[process j | ℱ i] =ᵐ[μ] process i`.
-/
theorem residual_conditional_mean_zero_component_of_mathlib_martingale_condExp
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : ResidualMartingaleDifferenceBridge)
    (process : ι -> Ω -> E)
    (hmartingale : Martingale process ℱ μ)
    {i j : ι} (hij : i ≤ j)
    (hmap :
      μ[process j | ℱ i] =ᵐ[μ] process i ->
        b.residual_conditional_mean_zero) :
    b.residual_conditional_mean_zero :=
  hmap (hmartingale.condExp_ae_eq hij)

/--
Adapter from a concrete Mathlib martingale certificate to the paper-specific
WDSM residual martingale-difference array premise.  The remaining `hmap`
premise is the honest place where a concrete WDSM array is identified with
the abstract residual contribution used by the CLT interface.
-/
theorem martingale_difference_array_of_mathlib_martingale
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : ResidualMartingaleDifferenceBridge)
    (process : ι -> Ω -> E)
    (hmartingale : Martingale process ℱ μ)
    (hmap :
      Martingale process ℱ μ -> b.martingale_difference_array) :
    b.martingale_difference_array :=
  hmap hmartingale

/--
Adapter from a concrete Mathlib martingale certificate to the triangular
martingale-difference field.  This is the triangular analogue of
`martingale_difference_array_of_mathlib_martingale`: the only remaining map is
the WDSM-specific identification between the concrete process and the abstract
residual array.
-/
theorem triangular_martingale_difference_array_of_mathlib_martingale
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (process : ι -> Ω -> E)
    (hmartingale : Martingale process ℱ μ)
    (hmap :
      Martingale process ℱ μ ->
        martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  hmap hmartingale

/--
Nat-indexed partial-sum adapter from Mathlib's martingale construction theorem.
This is the concrete residual-array route: prove strong adaptedness,
integrability, and zero conditional expectation of one-step increments, then
map the resulting Mathlib martingale to the WDSM martingale-difference premise.
-/
theorem martingale_difference_array_of_condExp_sub_eq_zero_nat
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : ResidualMartingaleDifferenceBridge)
    (partialSum : ℕ -> Ω -> E)
    (hadapted : StronglyAdapted ℱ partialSum)
    (hintegrable : ∀ i, Integrable (partialSum i) μ)
    (hcondZero :
      ∀ i, μ[partialSum (i + 1) - partialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale partialSum ℱ μ -> b.martingale_difference_array) :
    b.martingale_difference_array :=
  hmap
    (martingale_of_condExp_sub_eq_zero_nat hadapted hintegrable hcondZero)

/--
Increment-array adapter for the Nat-indexed convention
`partialSum n = sum_{k < n} increment k`.  It derives the partial-sum
martingale from increment-level measurability, integrability, and conditional
mean-zero hypotheses, then maps that Mathlib martingale to the WDSM premise.
-/
theorem martingale_difference_array_of_increment_condExp_eq_zero_nat
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : ResidualMartingaleDifferenceBridge)
    (increment : ℕ -> Ω -> E)
    (hincrementMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (increment i))
    (hincrementIntegrable : ∀ i, Integrable (increment i) μ)
    (hincrementCondZero :
      ∀ i, μ[increment i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, increment k ω) ℱ μ ->
        b.martingale_difference_array) :
    b.martingale_difference_array := by
  refine martingale_difference_array_of_condExp_sub_eq_zero_nat b
    (fun n ω => ∑ k ∈ Finset.range n, increment k ω)
    ?hadapted ?hintegrable ?hcondZero hmap
  · intro n
    exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
      (hincrementMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
  · intro n
    exact integrable_finsetSum (Finset.range n) fun k _ =>
      hincrementIntegrable k
  · intro i
    exact
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (hincrementCondZero i)

/--
Predictable-coefficient residual innovations have zero conditional mean.  This
is the Mathlib conditional-expectation pull-out step behind the WDSM residual
martingale representation: once the coefficient is known at time `i`, only the
residual innovation's conditional mean remains.
-/
theorem condExp_predictable_mul_residual_ae_eq_zero_nat
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (coefficient i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient i ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0) :
    ∀ i, μ[(fun ω => coefficient i ω * residual i ω) | ℱ i] =ᵐ[μ] 0 := by
  intro i
  refine
    (condExp_mul_of_stronglyMeasurable_left (m := ℱ i) (μ := μ)
      (hcoefficientMeas i) (hproductIntegrable i)
      (hresidualIntegrable i)).trans ?_
  filter_upwards [hresidualCondZero i] with ω hω
  simp [hω]

/--
One-arm predictable weighted-residual increment adapter.  It derives the
Nat-indexed Mathlib martingale for
`partialSum n = sum_{k < n} coefficient k * residual k` from predictability of
the coefficient, next-step residual measurability, integrability, and residual
conditional mean zero.
-/
theorem martingale_difference_array_of_predictable_weighted_residual_increments_nat
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (coefficient i))
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient i ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient k ω * residual k ω)
          ℱ μ ->
        b.martingale_difference_array) :
    b.martingale_difference_array :=
  martingale_difference_array_of_increment_condExp_eq_zero_nat b
    (fun i ω => coefficient i ω * residual i ω)
    (fun i =>
      ((hcoefficientMeas i).mono (ℱ.mono (Nat.le_succ i))).mul
        (hresidualNextMeas i))
  hproductIntegrable
  (condExp_predictable_mul_residual_ae_eq_zero_nat coefficient residual
    hcoefficientMeas hproductIntegrable hresidualIntegrable
    hresidualCondZero)
  hmap

/--
Concrete Nat-indexed adapter from Mathlib's martingale construction theorem to
an explicit triangular martingale-array CLT bridge.
-/
theorem triangular_martingale_difference_array_of_condExp_sub_eq_zero_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (partialSum : ℕ -> Ω -> E)
    (hadapted : StronglyAdapted ℱ partialSum)
    (hintegrable : ∀ i, Integrable (partialSum i) μ)
    (hcondZero :
      ∀ i, μ[partialSum (i + 1) - partialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale partialSum ℱ μ ->
        martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  hmap
    (martingale_of_condExp_sub_eq_zero_nat hadapted hintegrable hcondZero)

/--
Concrete Nat-indexed increment-array adapter from Mathlib's martingale
construction theorem to an explicit triangular martingale-array CLT bridge.
-/
theorem triangular_martingale_difference_array_of_increment_condExp_eq_zero_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (increment : ℕ -> Ω -> E)
    (hincrementMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (increment i))
    (hincrementIntegrable : ∀ i, Integrable (increment i) μ)
    (hincrementCondZero :
      ∀ i, μ[increment i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, increment k ω) ℱ μ ->
        martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array := by
  refine
    triangular_martingale_difference_array_of_condExp_sub_eq_zero_nat
      martingaleCLT
      (fun n ω => ∑ k ∈ Finset.range n, increment k ω)
      ?hadapted ?hintegrable ?hcondZero hmap
  · intro n
    exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
      (hincrementMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
  · intro n
    exact integrable_finsetSum (Finset.range n) fun k _ =>
      hincrementIntegrable k
  · intro i
    exact
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (hincrementCondZero i)

/--
Adapter from the predictable one-arm residual bridge route to a
`ResidualMartingaleArrayCLTVarianceInput`, keeping the named residual bridge
layer explicit before transferring to the input field.
-/
theorem input_martingale_difference_array_of_predictable_residual_bridge_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : ResidualMartingaleDifferenceBridge)
    (hinputMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (coefficient i))
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient i ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hbridgeMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient k ω * residual k ω)
          ℱ μ ->
        b.martingale_difference_array) :
    input.martingale_difference_array :=
  hinputMap
    (martingale_difference_array_of_predictable_weighted_residual_increments_nat
      b coefficient residual hcoefficientMeas hresidualNextMeas
      hproductIntegrable hresidualIntegrable hresidualCondZero hbridgeMap)

/--
Adapter from the predictable one-arm residual bridge route to an explicit
triangular martingale-array CLT bridge, preserving the named residual bridge
field before the triangular identification map is applied.
-/
theorem triangular_martingale_difference_array_of_predictable_residual_bridge_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : ResidualMartingaleDifferenceBridge)
    (htriangularMap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (coefficient i))
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient i ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hbridgeMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient k ω * residual k ω)
          ℱ μ ->
        b.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  htriangularMap
    (martingale_difference_array_of_predictable_weighted_residual_increments_nat
      b coefficient residual hcoefficientMeas hresidualNextMeas
      hproductIntegrable hresidualIntegrable hresidualCondZero hbridgeMap)

/--
Concrete Nat-indexed predictable weighted-residual increment adapter to the
martingale-difference field of an explicit triangular martingale-array CLT
bridge.

The only remaining map identifies the Mathlib partial-sum martingale with the
paper-specific residual array used by the triangular CLT interface.
-/
theorem triangular_martingale_difference_array_of_predictable_weighted_residual_increments_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (coefficient i))
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient i ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient k ω * residual k ω)
          ℱ μ ->
        martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array := by
  refine hmap ?_
  exact
    martingale_of_condExp_sub_eq_zero_nat
      (fun n =>
        Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
          ((hcoefficientMeas k).mono
              (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
            ((hresidualNextMeas k).mono
              (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
      (fun n =>
        integrable_finsetSum (Finset.range n) fun k _ =>
          hproductIntegrable k)
      (fun i =>
        (condExp_congr_ae
          (ae_of_all _ fun ω => by
            simp [Finset.sum_range_succ])).trans
          ((condExp_predictable_mul_residual_ae_eq_zero_nat
              coefficient residual hcoefficientMeas hproductIntegrable
              hresidualIntegrable hresidualCondZero) i))

/--
Discrete predictable processes supply the past-measurability convention used
by residual martingale increments: the coefficient applied to increment `i`
is the predictable process at time `i + 1`, hence it is `ℱ i`-measurable.
-/
theorem coefficient_past_measurable_of_stronglyPredictable_add_one_nat
    {Ω : Type*} {m0 : MeasurableSpace Ω} {ℱ : Filtration ℕ m0}
    (coefficient : ℕ -> Ω -> Real)
    (hcoefficientPredictable :
      IsStronglyPredictable ℱ coefficient) :
    ∀ i, StronglyMeasurable[ℱ i] (coefficient (i + 1)) :=
  fun i => hcoefficientPredictable.measurable_add_one i

/--
One-arm residual martingale-difference field from a genuinely predictable
coefficient process and residual innovations.

This closes the named `ResidualMartingaleDifferenceBridge` field under the
WDSM reveal-order convention: coefficient value `i + 1` is applied to residual
innovation `i`, and Mathlib predictability supplies the required past
measurability.
-/
theorem
    martingale_difference_array_of_stronglyPredictable_weighted_residual_increments_nat
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientPredictable :
      IsStronglyPredictable ℱ coefficient)
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient (i + 1) ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              coefficient (k + 1) ω * residual k ω)
          ℱ μ ->
        b.martingale_difference_array) :
    b.martingale_difference_array :=
  martingale_difference_array_of_predictable_weighted_residual_increments_nat
    b (fun i ω => coefficient (i + 1) ω) residual
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      coefficient hcoefficientPredictable)
    hresidualNextMeas hproductIntegrable hresidualIntegrable
    hresidualCondZero hmap

/--
Adapter from the strongly-predictable one-arm residual bridge route to a
`ResidualMartingaleArrayCLTVarianceInput`, keeping the named residual bridge
layer explicit before transferring to the input field.
-/
theorem input_martingale_difference_array_of_stronglyPredictable_residual_bridge_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : ResidualMartingaleDifferenceBridge)
    (hinputMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientPredictable :
      IsStronglyPredictable ℱ coefficient)
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient (i + 1) ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hbridgeMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              coefficient (k + 1) ω * residual k ω)
          ℱ μ ->
        b.martingale_difference_array) :
    input.martingale_difference_array :=
  hinputMap
    (martingale_difference_array_of_stronglyPredictable_weighted_residual_increments_nat
      b coefficient residual hcoefficientPredictable hresidualNextMeas
      hproductIntegrable hresidualIntegrable hresidualCondZero
      hbridgeMap)

/--
Adapter from the strongly-predictable one-arm residual bridge route to an
explicit triangular martingale-array CLT bridge.
-/
theorem triangular_martingale_difference_array_of_stronglyPredictable_residual_bridge_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : ResidualMartingaleDifferenceBridge)
    (htriangularMap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientPredictable :
      IsStronglyPredictable ℱ coefficient)
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient (i + 1) ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hbridgeMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              coefficient (k + 1) ω * residual k ω)
          ℱ μ ->
        b.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  htriangularMap
    (martingale_difference_array_of_stronglyPredictable_weighted_residual_increments_nat
      b coefficient residual hcoefficientPredictable hresidualNextMeas
      hproductIntegrable hresidualIntegrable hresidualCondZero
      hbridgeMap)

/--
Triangular martingale-difference field from a genuinely predictable
coefficient process and residual innovations.

This is the filtration/index-identification form used by WDSM residual arrays:
the increment at index `i` uses the predictable coefficient at time `i + 1`,
so Mathlib predictability gives the `ℱ i` measurability needed for the
conditional-expectation pull-out step.
-/
theorem
    triangular_martingale_difference_array_of_stronglyPredictable_weighted_residual_increments_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientPredictable :
      IsStronglyPredictable ℱ coefficient)
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient (i + 1) ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              coefficient (k + 1) ω * residual k ω)
          ℱ μ ->
        martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  triangular_martingale_difference_array_of_predictable_weighted_residual_increments_nat
    martingaleCLT (fun i ω => coefficient (i + 1) ω) residual
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      coefficient hcoefficientPredictable)
    hresidualNextMeas hproductIntegrable hresidualIntegrable
    hresidualCondZero hmap

/--
Concrete Nat-indexed adapter from Mathlib's martingale construction theorem to
a `ResidualMartingaleArrayCLTVarianceInput`.
-/
theorem input_martingale_difference_array_of_condExp_sub_eq_zero_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (partialSum : ℕ -> Ω -> E)
    (hadapted : StronglyAdapted ℱ partialSum)
    (hintegrable : ∀ i, Integrable (partialSum i) μ)
    (hcondZero :
      ∀ i, μ[partialSum (i + 1) - partialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale partialSum ℱ μ -> input.martingale_difference_array) :
    input.martingale_difference_array :=
  hmap
    (martingale_of_condExp_sub_eq_zero_nat hadapted hintegrable hcondZero)

/--
Concrete Nat-indexed increment-array adapter from Mathlib's martingale
construction theorem to a `ResidualMartingaleArrayCLTVarianceInput`, using the
convention `partialSum n = sum_{k < n} increment k`.
-/
theorem input_martingale_difference_array_of_increment_condExp_eq_zero_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (increment : ℕ -> Ω -> E)
    (hincrementMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (increment i))
    (hincrementIntegrable : ∀ i, Integrable (increment i) μ)
    (hincrementCondZero :
      ∀ i, μ[increment i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, increment k ω) ℱ μ ->
        input.martingale_difference_array) :
    input.martingale_difference_array := by
  refine input_martingale_difference_array_of_condExp_sub_eq_zero_nat input
    (fun n ω => ∑ k ∈ Finset.range n, increment k ω)
    ?hadapted ?hintegrable ?hcondZero hmap
  · intro n
    exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
      (hincrementMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
  · intro n
    exact integrable_finsetSum (Finset.range n) fun k _ =>
      hincrementIntegrable k
  · intro i
    exact
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (hincrementCondZero i)

/--
Concrete one-arm predictable weighted-residual increment adapter to a
`ResidualMartingaleArrayCLTVarianceInput`.
-/
theorem input_martingale_difference_array_of_predictable_weighted_residual_increments_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (coefficient i))
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient i ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient k ω * residual k ω)
          ℱ μ ->
        input.martingale_difference_array) :
    input.martingale_difference_array :=
  input_martingale_difference_array_of_increment_condExp_eq_zero_nat input
    (fun i ω => coefficient i ω * residual i ω)
    (fun i =>
      ((hcoefficientMeas i).mono (ℱ.mono (Nat.le_succ i))).mul
        (hresidualNextMeas i))
    hproductIntegrable
    (condExp_predictable_mul_residual_ae_eq_zero_nat coefficient residual
      hcoefficientMeas hproductIntegrable hresidualIntegrable
      hresidualCondZero)
    hmap

/--
Concrete one-arm predictable weighted-residual increment adapter to a
`ResidualMartingaleArrayCLTVarianceInput`, with the past-measurability premise
derived from a Mathlib `IsStronglyPredictable` coefficient process under the
WDSM `i + 1` reveal-order convention.
-/
theorem input_martingale_difference_array_of_stronglyPredictable_weighted_residual_increments_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientPredictable : IsStronglyPredictable ℱ coefficient)
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient (i + 1) ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient (k + 1) ω * residual k ω)
          ℱ μ ->
        input.martingale_difference_array) :
    input.martingale_difference_array :=
  input_martingale_difference_array_of_predictable_weighted_residual_increments_nat
    input (fun i ω => coefficient (i + 1) ω) residual
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      coefficient hcoefficientPredictable)
    hresidualNextMeas hproductIntegrable hresidualIntegrable
    hresidualCondZero hmap

/--
Residual CLT/variance input closed through a concrete Mathlib martingale
certificate for the residual array.  This still requires the WDSM-specific
reuse moments, Lindeberg condition, and predictable quadratic-variation
stabilization; it does not assume or manufacture the martingale-array CLT.
-/
theorem residual_clt_and_variance_formula_of_mathlib_martingale_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (process : ι -> Ω -> E)
    (hmartingale : Martingale process ℱ μ)
    (hmap :
      Martingale process ℱ μ -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual (hmap hmartingale) hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through a concrete Mathlib
martingale certificate for the residual array.  This removes the opaque
triangular martingale-difference field when the WDSM residual array has already
been identified with a Mathlib martingale process.
-/
theorem residual_clt_and_variance_formula_of_mathlib_martingale_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (process : ι -> Ω -> E)
    (hmartingale : Martingale process ℱ μ)
    (hmap :
      Martingale process ℱ μ ->
        martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_mathlib_martingale
      martingaleCLT process hmartingale hmap)
    hlindeberg hquad

/--
Residual CLT/variance input closed through Mathlib's Nat-indexed partial-sum
martingale construction.  The actual asymptotic-normality theorem is still the
named WDSM `martingale_clt_bridge`; this lemma only removes the opaque
martingale-difference premise.
-/
theorem residual_clt_and_variance_formula_of_condExp_sub_eq_zero_nat_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (partialSum : ℕ -> Ω -> E)
    (hadapted : StronglyAdapted ℱ partialSum)
    (hintegrable : ∀ i, Integrable (partialSum i) μ)
    (hcondZero :
      ∀ i, μ[partialSum (i + 1) - partialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale partialSum ℱ μ -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_condExp_sub_eq_zero_nat input
      partialSum hadapted hintegrable hcondZero hmap)
    hlindeberg hquad

/--
Residual CLT/variance input closed through a concrete Nat-indexed increment
array.  This turns increment-level conditional mean-zero hypotheses into the
partial-sum Mathlib martingale required by the WDSM residual interface.
-/
theorem residual_clt_and_variance_formula_of_increment_condExp_eq_zero_nat_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (increment : ℕ -> Ω -> E)
    (hincrementMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (increment i))
    (hincrementIntegrable : ∀ i, Integrable (increment i) μ)
    (hincrementCondZero :
      ∀ i, μ[increment i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, increment k ω) ℱ μ ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_increment_condExp_eq_zero_nat input
      increment hincrementMeas hincrementIntegrable hincrementCondZero hmap)
    hlindeberg hquad

/--
Residual CLT/variance input closed through predictable weighted-residual
increments.  This is the paper-style one-arm route where the array increment is
a past-measurable loading times a newly revealed residual innovation.
-/
theorem
    residual_clt_and_variance_formula_of_predictable_weighted_residual_increments_nat_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (coefficient i))
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient i ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient k ω * residual k ω)
          ℱ μ ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_predictable_weighted_residual_increments_nat
      input coefficient residual hcoefficientMeas hresidualNextMeas
      hproductIntegrable hresidualIntegrable hresidualCondZero hmap)
    hlindeberg hquad

/--
Residual CLT/variance input closed through a strongly predictable
weighted-residual increment representation.  This removes the one-arm raw
past-measurability premise from the endpoint while preserving the explicit
Lindeberg and predictable-QV obligations.
-/
theorem
    residual_clt_and_variance_formula_of_stronglyPredictable_weighted_residual_increments_nat_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientPredictable : IsStronglyPredictable ℱ coefficient)
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient (i + 1) ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient (k + 1) ω * residual k ω)
          ℱ μ ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_stronglyPredictable_weighted_residual_increments_nat
      input coefficient residual hcoefficientPredictable hresidualNextMeas
      hproductIntegrable hresidualIntegrable hresidualCondZero hmap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through predictable
weighted-residual increments.  This discharges the triangular
martingale-difference field from past-measurable coefficients and
conditionally mean-zero residual innovations while leaving the triangular
Lindeberg and predictable-QV fields explicit.
-/
theorem
    residual_clt_and_variance_formula_of_predictable_weighted_residual_increments_nat_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (coefficient i))
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient i ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient k ω * residual k ω)
          ℱ μ ->
        martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_predictable_weighted_residual_increments_nat
      martingaleCLT coefficient residual hcoefficientMeas
      hresidualNextMeas hproductIntegrable hresidualIntegrable
      hresidualCondZero hmap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through a strongly predictable
weighted-residual increment representation under the WDSM `i + 1`
reveal-order convention.
-/
theorem
    residual_clt_and_variance_formula_of_stronglyPredictable_weighted_residual_increments_nat_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (coefficient residual : ℕ -> Ω -> Real)
    (hcoefficientPredictable : IsStronglyPredictable ℱ coefficient)
    (hresidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (residual i))
    (hproductIntegrable :
      ∀ i, Integrable
        (fun ω => coefficient (i + 1) ω * residual i ω) μ)
    (hresidualIntegrable : ∀ i, Integrable (residual i) μ)
    (hresidualCondZero :
      ∀ i, μ[residual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n, coefficient (k + 1) ω * residual k ω)
          ℱ μ ->
        martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_stronglyPredictable_weighted_residual_increments_nat
      martingaleCLT coefficient residual hcoefficientPredictable
      hresidualNextMeas hproductIntegrable hresidualIntegrable
      hresidualCondZero hmap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through Mathlib's Nat-indexed
partial-sum martingale construction.
-/
theorem residual_clt_and_variance_formula_of_condExp_sub_eq_zero_nat_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (partialSum : ℕ -> Ω -> E)
    (hadapted : StronglyAdapted ℱ partialSum)
    (hintegrable : ∀ i, Integrable (partialSum i) μ)
    (hcondZero :
      ∀ i, μ[partialSum (i + 1) - partialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale partialSum ℱ μ ->
        martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_condExp_sub_eq_zero_nat
      martingaleCLT partialSum hadapted hintegrable hcondZero hmap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through concrete Nat-indexed
increment arrays.
-/
theorem residual_clt_and_variance_formula_of_increment_condExp_eq_zero_nat_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (increment : ℕ -> Ω -> E)
    (hincrementMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (increment i))
    (hincrementIntegrable : ∀ i, Integrable (increment i) μ)
    (hincrementCondZero :
      ∀ i, μ[increment i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, increment k ω) ℱ μ ->
        martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_increment_condExp_eq_zero_nat
      martingaleCLT increment hincrementMeas hincrementIntegrable
      hincrementCondZero hmap)
    hlindeberg hquad

/--
Close the one-arm coefficient predictability component from an
almost-everywhere score-measurability fact.
-/
theorem coefficient_predictability_component_of_aestronglyMeasurable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hmap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        b.coefficient_predictability) :
    b.coefficient_predictability :=
  hmap hcoefficient

/--
Close the one-arm coefficient predictability component from a score-field
strong measurability fact.
-/
theorem coefficient_predictability_component_of_stronglyMeasurable
    {Sample : Type*}
    {scoreSigma : MeasurableSpace Sample}
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient : Sample -> Real)
    (hcoefficient : StronglyMeasurable[scoreSigma] coefficient)
    (hmap :
      StronglyMeasurable[scoreSigma] coefficient ->
        b.coefficient_predictability) :
    b.coefficient_predictability :=
  hmap hcoefficient

/--
Close the one-arm finite-array integrability component from integrability of
the weighted residual contribution.
-/
theorem finite_array_integrability_component_of_integrable_weightedResidual
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {sampleLaw : Measure[mSample] Sample}
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient residual : Sample -> Real)
    (hintegrable :
      Integrable (fun sample => coefficient sample * residual sample)
        sampleLaw)
    (hmap :
      Integrable (fun sample => coefficient sample * residual sample)
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  hmap hintegrable

/--
Close the one-arm residual conditional mean-zero component from a concrete
conditional-expectation residual identity.
-/
theorem residual_conditional_mean_zero_component_of_condExp_ae_eq_scoreVersion
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : ResidualMartingaleDifferenceBridge)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreSelf :
      sampleLaw[scoreVersion | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero) :
    b.residual_conditional_mean_zero :=
  hmap
    (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) outcome scoreVersion houtcome hscore hcond
      hscoreSelf)

/--
Raw-outcome-integrability variant of the one-arm residual conditional
mean-zero component from a concrete conditional-expectation identity.
-/
theorem
    residual_conditional_mean_zero_component_of_condExp_ae_eq_scoreVersion_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : ResidualMartingaleDifferenceBridge)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreSelf :
      sampleLaw[scoreVersion | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero) :
    b.residual_conditional_mean_zero :=
  hmap
    (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) outcome scoreVersion houtcome hcond
      hscoreSelf)

/--
Close the one-arm residual conditional mean-zero component when the score
version is strongly measurable with respect to the score sigma-field.
-/
theorem residual_conditional_mean_zero_component_of_scoreVersion_stronglyMeasurable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (b : ResidualMartingaleDifferenceBridge)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas : StronglyMeasurable[scoreSigma] scoreVersion)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero) :
    b.residual_conditional_mean_zero :=
  hmap
    (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_stronglyMeasurable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub outcome scoreVersion houtcome hscore
      hscoreMeas hcond)

/--
Raw-outcome-integrability variant of the one-arm strongly measurable
score-version residual conditional mean-zero component.
-/
theorem
    residual_conditional_mean_zero_component_of_scoreVersion_stronglyMeasurable_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (b : ResidualMartingaleDifferenceBridge)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas : StronglyMeasurable[scoreSigma] scoreVersion)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero) :
    b.residual_conditional_mean_zero :=
  hmap
    (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_stronglyMeasurable_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub outcome scoreVersion houtcome
      hscoreMeas hcond)

/--
Close the one-arm residual conditional mean-zero component from conditional
orthogonality of a score-measurable coefficient and a centered residual.
-/
theorem residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero) :
    b.residual_conditional_mean_zero :=
  hmap
    (condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub coefficient outcome scoreVersion
      hcoefficient houtcome hscore hscoreMeas hproduct hcond)

/--
Raw-outcome-integrability variant of the one-arm residual conditional
mean-zero component for score-measurable weighted centered residuals.
-/
theorem
    residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero) :
    b.residual_conditional_mean_zero :=
  hmap
    (condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub coefficient outcome scoreVersion
      hcoefficient houtcome hscoreMeas hproduct hcond)

/--
Residual CLT/variance input from concrete one-arm weighted centered-residual
martingale-difference components.
-/
theorem residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_input
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (harrayMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hpredictabilityMap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        b.coefficient_predictability)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hweightedResidual :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hzeroMap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            coefficient sample * (outcome sample - scoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_residual_bridge_input input b harrayMap
    hmoments hresidualRegularity
    (coefficient_predictability_component_of_aestronglyMeasurable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) b coefficient hcoefficient
      hpredictabilityMap)
    (residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub b coefficient outcome scoreVersion
      hcoefficient houtcome hscore hscoreMeas hweightedResidual hcond
      hzeroMap)
    hregular
    (finite_array_integrability_component_of_integrable_weightedResidual
      (mSample := mSample) (sampleLaw := sampleLaw) b coefficient
      (fun sample => outcome sample - scoreVersion sample) hweightedResidual
      hintegrabilityMap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge from concrete one-arm
score-measurable weighted centered-residual martingale-difference components.
This is the triangular analogue of
`residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_input`.
-/
theorem residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_triangular
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (harrayMap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hpredictabilityMap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        b.coefficient_predictability)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hweightedResidual :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hzeroMap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            coefficient sample * (outcome sample - scoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_residual_bridge_triangular
    martingaleCLT b harrayMap
    (coefficient_predictability_component_of_aestronglyMeasurable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) b coefficient hcoefficient
      hpredictabilityMap)
    (residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub b coefficient outcome scoreVersion
      hcoefficient houtcome hscore hscoreMeas hweightedResidual hcond
      hzeroMap)
    hregular
    (finite_array_integrability_component_of_integrable_weightedResidual
      (mSample := mSample) (sampleLaw := sampleLaw) b coefficient
      (fun sample => outcome sample - scoreVersion sample) hweightedResidual
      hintegrabilityMap)
    hlindeberg hquad

/--
Raw-outcome-integrability variant of the one-arm weighted centered-residual
CLT/variance bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_input_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (harrayMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hpredictabilityMap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        b.coefficient_predictability)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hweightedResidual :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hzeroMap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            coefficient sample * (outcome sample - scoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_residual_bridge_input input b harrayMap
    hmoments hresidualRegularity
    (coefficient_predictability_component_of_aestronglyMeasurable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) b coefficient hcoefficient
      hpredictabilityMap)
    (residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub b coefficient outcome scoreVersion
      hcoefficient houtcome hscoreMeas hweightedResidual hcond hzeroMap)
    hregular
    (finite_array_integrability_component_of_integrable_weightedResidual
      (mSample := mSample) (sampleLaw := sampleLaw) b coefficient
      (fun sample => outcome sample - scoreVersion sample) hweightedResidual
      hintegrabilityMap)
    hlindeberg hquad

/--
Raw-outcome-integrability variant of the one-arm score-measurable weighted
centered-residual triangular CLT/variance bridge.
-/
theorem
    residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_triangular_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : ResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (harrayMap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hpredictabilityMap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        b.coefficient_predictability)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hweightedResidual :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hzeroMap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.residual_conditional_mean_zero)
    (hregular : b.sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            coefficient sample * (outcome sample - scoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_residual_bridge_triangular
    martingaleCLT b harrayMap
    (coefficient_predictability_component_of_aestronglyMeasurable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) b coefficient hcoefficient
      hpredictabilityMap)
    (residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub b coefficient outcome scoreVersion
      hcoefficient houtcome hscoreMeas hweightedResidual hcond hzeroMap)
    hregular
    (finite_array_integrability_component_of_integrable_weightedResidual
      (mSample := mSample) (sampleLaw := sampleLaw) b coefficient
      (fun sample => outcome sample - scoreVersion sample) hweightedResidual
      hintegrabilityMap)
    hlindeberg hquad

/--
One-arm sampling/filtration regularity bridge.

This names the pieces that later WDSM probability work must prove to turn the
score-measurable weighted residual into a martingale-difference array under a
chosen triangular-array filtration.
-/
structure ResidualSamplingFiltrationRegularityBridge where
  array_filtration_defined : Prop
  coefficient_adapted_to_past : Prop
  residual_innovation_measurable : Prop
  sampling_order_regular : Prop
  conditional_design_regular : Prop
  sampling_or_filtration_regular : Prop
  bridge :
    array_filtration_defined ->
    coefficient_adapted_to_past ->
    residual_innovation_measurable ->
    sampling_order_regular ->
    conditional_design_regular ->
    sampling_or_filtration_regular

/-- Close one-arm sampling/filtration regularity from its named pieces. -/
theorem sampling_or_filtration_regular_of_bridge
    (b : ResidualSamplingFiltrationRegularityBridge)
    (hfiltration : b.array_filtration_defined)
    (hadapted : b.coefficient_adapted_to_past)
    (hinnovation : b.residual_innovation_measurable)
    (horder : b.sampling_order_regular)
    (hdesign : b.conditional_design_regular) :
    b.sampling_or_filtration_regular :=
  b.bridge hfiltration hadapted hinnovation horder hdesign

/--
Close the one-arm martingale-difference bridge's sampling/filtration component
from an explicit sampling/filtration regularity bridge.
-/
theorem sampling_or_filtration_regular_component_of_bridge
    (martingaleBridge : ResidualMartingaleDifferenceBridge)
    (regularityBridge : ResidualSamplingFiltrationRegularityBridge)
    (hmap :
      regularityBridge.sampling_or_filtration_regular ->
        martingaleBridge.sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (hadapted : regularityBridge.coefficient_adapted_to_past)
    (hinnovation : regularityBridge.residual_innovation_measurable)
    (horder : regularityBridge.sampling_order_regular)
    (hdesign : regularityBridge.conditional_design_regular) :
    martingaleBridge.sampling_or_filtration_regular :=
  hmap
    (sampling_or_filtration_regular_of_bridge regularityBridge
      hfiltration hadapted hinnovation horder hdesign)

/--
Adapter from one-arm named martingale-difference components plus explicit
sampling/filtration bridge pieces to a concrete martingale-array input.
-/
theorem input_martingale_difference_array_of_residual_sampling_bridge
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : ResidualMartingaleDifferenceBridge)
    (regularityBridge : ResidualSamplingFiltrationRegularityBridge)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hpredictable : martingaleBridge.coefficient_predictability)
    (hzero : martingaleBridge.residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.sampling_or_filtration_regular ->
        martingaleBridge.sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (hadapted : regularityBridge.coefficient_adapted_to_past)
    (hinnovation : regularityBridge.residual_innovation_measurable)
    (horder : regularityBridge.sampling_order_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrable : martingaleBridge.finite_array_integrability) :
    input.martingale_difference_array :=
  input_martingale_difference_array_of_residual_bridge input martingaleBridge
    harrayMap hpredictable hzero
    (sampling_or_filtration_regular_component_of_bridge martingaleBridge
      regularityBridge hregularityMap hfiltration hadapted hinnovation
      horder hdesign)
    hintegrable

/--
Triangular martingale-difference field closed through a one-arm residual
martingale bridge plus an explicit one-arm sampling/filtration regularity
bridge.
-/
theorem triangular_martingale_difference_array_of_residual_sampling_bridge
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (martingaleBridge : ResidualMartingaleDifferenceBridge)
    (regularityBridge : ResidualSamplingFiltrationRegularityBridge)
    (hmap :
      martingaleBridge.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (hpredictable : martingaleBridge.coefficient_predictability)
    (hzero : martingaleBridge.residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.sampling_or_filtration_regular ->
        martingaleBridge.sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (hadapted : regularityBridge.coefficient_adapted_to_past)
    (hinnovation : regularityBridge.residual_innovation_measurable)
    (horder : regularityBridge.sampling_order_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrable : martingaleBridge.finite_array_integrability) :
    martingaleCLT.martingale_difference_array :=
  triangular_martingale_difference_array_of_residual_bridge martingaleCLT
    martingaleBridge hmap hpredictable hzero
    (sampling_or_filtration_regular_component_of_bridge martingaleBridge
      regularityBridge hregularityMap hfiltration hadapted hinnovation
      horder hdesign)
    hintegrable

/--
One-arm weighted centered-residual CLT/variance input closed from explicit
sampling/filtration regularity components.
-/
theorem residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_sampling_bridge_input
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : ResidualMartingaleDifferenceBridge)
    (regularityBridge : ResidualSamplingFiltrationRegularityBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hpredictabilityMap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        martingaleBridge.coefficient_predictability)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hweightedResidual :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hzeroMap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.sampling_or_filtration_regular ->
        martingaleBridge.sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (hadapted : regularityBridge.coefficient_adapted_to_past)
    (hinnovation : regularityBridge.residual_innovation_measurable)
    (horder : regularityBridge.sampling_order_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            coefficient sample * (outcome sample - scoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_input
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub input martingaleBridge coefficient
    outcome scoreVersion harrayMap hmoments hresidualRegularity
    hcoefficient hpredictabilityMap houtcome hscore hscoreMeas
    hweightedResidual hcond hzeroMap
    (sampling_or_filtration_regular_component_of_bridge martingaleBridge
      regularityBridge hregularityMap hfiltration hadapted hinnovation
      horder hdesign)
    hintegrabilityMap hlindeberg hquad

/--
One-arm weighted centered-residual triangular CLT/variance bridge closed from
explicit sampling/filtration regularity components.
-/
theorem residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_sampling_bridge_triangular
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (martingaleBridge : ResidualMartingaleDifferenceBridge)
    (regularityBridge : ResidualSamplingFiltrationRegularityBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hpredictabilityMap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        martingaleBridge.coefficient_predictability)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hweightedResidual :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hzeroMap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.sampling_or_filtration_regular ->
        martingaleBridge.sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (hadapted : regularityBridge.coefficient_adapted_to_past)
    (hinnovation : regularityBridge.residual_innovation_measurable)
    (horder : regularityBridge.sampling_order_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            coefficient sample * (outcome sample - scoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_triangular
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub martingaleCLT martingaleBridge
    coefficient outcome scoreVersion harrayMap hcoefficient
    hpredictabilityMap houtcome hscore hscoreMeas hweightedResidual hcond
    hzeroMap
    (sampling_or_filtration_regular_component_of_bridge martingaleBridge
      regularityBridge hregularityMap hfiltration hadapted hinnovation
      horder hdesign)
    hintegrabilityMap hlindeberg hquad

/--
Raw-outcome-integrability variant of the one-arm weighted centered-residual
sampling/filtration bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_sampling_bridge_input_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : ResidualMartingaleDifferenceBridge)
    (regularityBridge : ResidualSamplingFiltrationRegularityBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hpredictabilityMap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        martingaleBridge.coefficient_predictability)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hweightedResidual :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hzeroMap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.sampling_or_filtration_regular ->
        martingaleBridge.sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (hadapted : regularityBridge.coefficient_adapted_to_past)
    (hinnovation : regularityBridge.residual_innovation_measurable)
    (horder : regularityBridge.sampling_order_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            coefficient sample * (outcome sample - scoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_input_outcomeIntegrable
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub input martingaleBridge coefficient
    outcome scoreVersion harrayMap hmoments hresidualRegularity
    hcoefficient hpredictabilityMap houtcome hscoreMeas hweightedResidual
    hcond hzeroMap
    (sampling_or_filtration_regular_component_of_bridge martingaleBridge
      regularityBridge hregularityMap hfiltration hadapted hinnovation
      horder hdesign)
    hintegrabilityMap hlindeberg hquad

/--
Raw-outcome-integrability variant of the one-arm weighted centered-residual
sampling/filtration triangular CLT/variance bridge.
-/
theorem
    residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_sampling_bridge_triangular_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (martingaleBridge : ResidualMartingaleDifferenceBridge)
    (regularityBridge : ResidualSamplingFiltrationRegularityBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hpredictabilityMap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        martingaleBridge.coefficient_predictability)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hweightedResidual :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hzeroMap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.sampling_or_filtration_regular ->
        martingaleBridge.sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (hadapted : regularityBridge.coefficient_adapted_to_past)
    (hinnovation : regularityBridge.residual_innovation_measurable)
    (horder : regularityBridge.sampling_order_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            coefficient sample * (outcome sample - scoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_scoreMeasurable_weightedCenteredResidual_bridge_triangular_outcomeIntegrable
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub martingaleCLT martingaleBridge
    coefficient outcome scoreVersion harrayMap hcoefficient
    hpredictabilityMap houtcome hscoreMeas hweightedResidual hcond
    hzeroMap
    (sampling_or_filtration_regular_component_of_bridge martingaleBridge
      regularityBridge hregularityMap hfiltration hadapted hinnovation
      horder hdesign)
    hintegrabilityMap hlindeberg hquad

/--
Two-arm martingale-difference bridge for WDSM residual contributions.

The two arms may require separate predictability and conditional mean-zero
arguments; the bridge also records the cross-arm sampling/filtration
regularity needed to combine them into the martingale array used by the
residual CLT.
-/
structure TwoArmResidualMartingaleDifferenceBridge where
  treated_coefficient_predictability : Prop
  control_coefficient_predictability : Prop
  treated_residual_conditional_mean_zero : Prop
  control_residual_conditional_mean_zero : Prop
  arm_sampling_or_filtration_regular : Prop
  finite_array_integrability : Prop
  martingale_difference_array : Prop
  bridge :
    treated_coefficient_predictability ->
    control_coefficient_predictability ->
    treated_residual_conditional_mean_zero ->
    control_residual_conditional_mean_zero ->
    arm_sampling_or_filtration_regular ->
    finite_array_integrability ->
    martingale_difference_array

/-- Close a two-arm martingale-difference premise from its named components. -/
theorem martingale_difference_array_of_twoArm_residual_bridge
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (htreatedPredictable : b.treated_coefficient_predictability)
    (hcontrolPredictable : b.control_coefficient_predictability)
    (htreatedZero : b.treated_residual_conditional_mean_zero)
    (hcontrolZero : b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability) :
    b.martingale_difference_array :=
  b.bridge htreatedPredictable hcontrolPredictable htreatedZero
    hcontrolZero hregular hintegrable

/--
Adapter from a two-arm residual martingale-difference bridge to a concrete
`ResidualMartingaleArrayCLTVarianceInput`.
-/
theorem input_martingale_difference_array_of_twoArm_residual_bridge
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (hmap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (htreatedPredictable : b.treated_coefficient_predictability)
    (hcontrolPredictable : b.control_coefficient_predictability)
    (htreatedZero : b.treated_residual_conditional_mean_zero)
    (hcontrolZero : b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability) :
    input.martingale_difference_array :=
  hmap
    (martingale_difference_array_of_twoArm_residual_bridge b
      htreatedPredictable hcontrolPredictable htreatedZero hcontrolZero
      hregular hintegrable)

/--
Adapter from a two-arm residual martingale-difference bridge to an explicit
triangular martingale-array CLT bridge.
-/
theorem triangular_martingale_difference_array_of_twoArm_residual_bridge
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (hmap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (htreatedPredictable : b.treated_coefficient_predictability)
    (hcontrolPredictable : b.control_coefficient_predictability)
    (htreatedZero : b.treated_residual_conditional_mean_zero)
    (hcontrolZero : b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability) :
    martingaleCLT.martingale_difference_array :=
  hmap
    (martingale_difference_array_of_twoArm_residual_bridge b
      htreatedPredictable hcontrolPredictable htreatedZero hcontrolZero
      hregular hintegrable)

/--
Residual CLT/variance input closed through a two-arm WDSM residual
martingale-difference bridge.
-/
theorem residual_clt_and_variance_formula_of_twoArm_residual_bridge_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (hmap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (htreatedPredictable : b.treated_coefficient_predictability)
    (hcontrolPredictable : b.control_coefficient_predictability)
    (htreatedZero : b.treated_residual_conditional_mean_zero)
    (hcontrolZero : b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_twoArm_residual_bridge input b hmap
      htreatedPredictable hcontrolPredictable htreatedZero hcontrolZero
      hregular hintegrable)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through a two-arm WDSM
residual martingale-difference bridge.  This discharges the triangular
martingale-difference field from the named two-arm residual bridge while
keeping the triangular Lindeberg and predictable-QV fields explicit.
-/
theorem residual_clt_and_variance_formula_of_twoArm_residual_bridge_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (hmap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (htreatedPredictable : b.treated_coefficient_predictability)
    (hcontrolPredictable : b.control_coefficient_predictability)
    (htreatedZero : b.treated_residual_conditional_mean_zero)
    (hcontrolZero : b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrable : b.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_twoArm_residual_bridge
      martingaleCLT b hmap htreatedPredictable hcontrolPredictable
      htreatedZero hcontrolZero hregular hintegrable)
    hlindeberg hquad

/-!
## Two-arm Mathlib martingale adapters

The two-arm WDSM residual bridge is the route used by paired PATE/PATT
residual inputs.  These adapters mirror the one-arm Mathlib bridge above while
keeping the concrete WDSM residual array identification and triangular
martingale-array CLT as explicit obligations.
-/

/--
Close both two-arm coefficient-predictability components from concrete Mathlib
martingale certificates.
-/
theorem twoArm_coefficient_predictability_components_of_mathlib_martingales
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (htreatedMap :
      StronglyAdapted ℱ treatedProcess ->
        b.treated_coefficient_predictability)
    (hcontrolMap :
      StronglyAdapted ℱ controlProcess ->
        b.control_coefficient_predictability) :
    b.treated_coefficient_predictability ∧
      b.control_coefficient_predictability :=
  ⟨htreatedMap htreatedMartingale.stronglyAdapted,
    hcontrolMap hcontrolMartingale.stronglyAdapted⟩

/--
Close the two-arm finite-array integrability component from concrete Mathlib
martingale certificates.
-/
theorem twoArm_finite_array_integrability_component_of_mathlib_martingales
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmap :
      (∀ i, Integrable (treatedProcess i) μ) ->
        (∀ i, Integrable (controlProcess i) μ) ->
          b.finite_array_integrability) :
    b.finite_array_integrability :=
  hmap
    (fun i => htreatedMartingale.integrable i)
    (fun i => hcontrolMartingale.integrable i)

/--
Close the treated-arm residual conditional-mean-zero component from the Mathlib
martingale identity for a concrete treated process.
-/
theorem treated_residual_conditional_mean_zero_component_of_mathlib_martingale_condExp
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    {i j : ι} (hij : i ≤ j)
    (hmap :
      μ[treatedProcess j | ℱ i] =ᵐ[μ] treatedProcess i ->
        b.treated_residual_conditional_mean_zero) :
    b.treated_residual_conditional_mean_zero :=
  hmap (htreatedMartingale.condExp_ae_eq hij)

/--
Close the control-arm residual conditional-mean-zero component from the Mathlib
martingale identity for a concrete control process.
-/
theorem control_residual_conditional_mean_zero_component_of_mathlib_martingale_condExp
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (controlProcess : ι -> Ω -> E)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    {i j : ι} (hij : i ≤ j)
    (hmap :
      μ[controlProcess j | ℱ i] =ᵐ[μ] controlProcess i ->
        b.control_residual_conditional_mean_zero) :
    b.control_residual_conditional_mean_zero :=
  hmap (hcontrolMartingale.condExp_ae_eq hij)

/--
Adapter from concrete treated/control Mathlib martingales to the two-arm WDSM
martingale-difference premise.  The `hmap` premise is the honest WDSM-specific
identification between those processes and the abstract residual contribution.
-/
theorem martingale_difference_array_of_twoArm_mathlib_martingales
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          b.martingale_difference_array) :
    b.martingale_difference_array :=
  hmap htreatedMartingale hcontrolMartingale

/--
Adapter from concrete treated/control Mathlib martingales to a
`ResidualMartingaleArrayCLTVarianceInput` martingale-difference field.
-/
theorem input_martingale_difference_array_of_twoArm_mathlib_martingales
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          input.martingale_difference_array) :
    input.martingale_difference_array :=
  hmap htreatedMartingale hcontrolMartingale

/--
Adapter from concrete treated/control Mathlib martingales to the
martingale-difference field of an explicit triangular martingale-array CLT
bridge.
-/
theorem triangular_martingale_difference_array_of_twoArm_mathlib_martingales
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  hmap htreatedMartingale hcontrolMartingale

/--
Triangular residual CLT/variance bridge closed through concrete
treated/control Mathlib martingale certificates.  The remaining `hmap`
identifies the two Mathlib processes with the paper-specific residual array;
Lindeberg and predictable-QV stay explicit.
-/
theorem residual_clt_and_variance_formula_of_twoArm_mathlib_martingales_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_twoArm_mathlib_martingales
      martingaleCLT treatedProcess controlProcess htreatedMartingale
      hcontrolMartingale hmap)
    hlindeberg hquad

/--
Residual CLT/variance input closed through concrete treated/control Mathlib
martingale certificates.  This is the input-level counterpart of
`residual_clt_and_variance_formula_of_twoArm_mathlib_martingales_triangular`.
-/
theorem residual_clt_and_variance_formula_of_twoArm_mathlib_martingales_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_twoArm_mathlib_martingales
      input treatedProcess controlProcess htreatedMartingale
      hcontrolMartingale hmap)
    hlindeberg hquad

/--
Two-arm increment-array adapter for the Nat-indexed convention
`partialSum n = sum_{k < n} increment k`.  Treated and control increment-level
conditional mean-zero hypotheses give Mathlib martingales, which are then
identified with the paper-specific two-arm residual array premise.
-/
theorem martingale_difference_array_of_twoArm_increment_condExp_eq_zero_nat
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedIncrement controlIncrement : ℕ -> Ω -> E)
    (htreatedMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedIncrement i))
    (hcontrolMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlIncrement i))
    (htreatedIntegrable : ∀ i, Integrable (treatedIncrement i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlIncrement i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedIncrement i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlIncrement i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
          ℱ μ ->
        Martingale (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
          ℱ μ ->
          b.martingale_difference_array) :
    b.martingale_difference_array := by
  refine martingale_difference_array_of_twoArm_mathlib_martingales b
    (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
    (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
    ?htreatedMartingale ?hcontrolMartingale hmap
  · refine martingale_of_condExp_sub_eq_zero_nat ?htreatedAdapted
      ?htreatedSumIntegrable ?htreatedSumCondZero
    · intro n
      exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
        (htreatedMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
    · intro n
      exact integrable_finsetSum (Finset.range n) fun k _ =>
        htreatedIntegrable k
    · intro i
      exact
        (condExp_congr_ae
          (ae_of_all _ fun ω => by
            simp [Finset.sum_range_succ])).trans
          (htreatedCondZero i)
  · refine martingale_of_condExp_sub_eq_zero_nat ?hcontrolAdapted
      ?hcontrolSumIntegrable ?hcontrolSumCondZero
    · intro n
      exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
        (hcontrolMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
    · intro n
      exact integrable_finsetSum (Finset.range n) fun k _ =>
        hcontrolIntegrable k
    · intro i
      exact
        (condExp_congr_ae
          (ae_of_all _ fun ω => by
            simp [Finset.sum_range_succ])).trans
          (hcontrolCondZero i)

/--
Two-arm predictable weighted-residual increment adapter.  This is the
treated/control version of the paper's residual reveal-order argument: each
increment is a past-measurable loading times the residual innovation revealed at
the next step.
-/
theorem
    martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient i ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient i ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient k ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient k ω * controlResidual k ω)
            ℱ μ ->
          b.martingale_difference_array) :
    b.martingale_difference_array :=
  martingale_difference_array_of_twoArm_increment_condExp_eq_zero_nat b
    (fun i ω => treatedCoefficient i ω * treatedResidual i ω)
    (fun i ω => controlCoefficient i ω * controlResidual i ω)
    (fun i =>
      ((htreatedCoefficientMeas i).mono (ℱ.mono (Nat.le_succ i))).mul
        (htreatedResidualNextMeas i))
    (fun i =>
      ((hcontrolCoefficientMeas i).mono (ℱ.mono (Nat.le_succ i))).mul
        (hcontrolResidualNextMeas i))
    htreatedProductIntegrable hcontrolProductIntegrable
    (condExp_predictable_mul_residual_ae_eq_zero_nat treatedCoefficient
      treatedResidual htreatedCoefficientMeas htreatedProductIntegrable
      htreatedResidualIntegrable htreatedResidualCondZero)
    (condExp_predictable_mul_residual_ae_eq_zero_nat controlCoefficient
      controlResidual hcontrolCoefficientMeas hcontrolProductIntegrable
      hcontrolResidualIntegrable hcontrolResidualCondZero)
    hmap

/--
Adapter from the predictable two-arm residual bridge route to a concrete
`ResidualMartingaleArrayCLTVarianceInput`, preserving the named
`TwoArmResidualMartingaleDifferenceBridge` layer before transferring to the
input field.
-/
theorem input_martingale_difference_array_of_twoArm_predictable_residual_bridge_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (hinputMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient i ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient i ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hbridgeMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient k ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient k ω * controlResidual k ω)
            ℱ μ ->
          b.martingale_difference_array) :
    input.martingale_difference_array :=
  hinputMap
    (martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
      b treatedCoefficient treatedResidual controlCoefficient
      controlResidual htreatedCoefficientMeas hcontrolCoefficientMeas
      htreatedResidualNextMeas hcontrolResidualNextMeas
      htreatedProductIntegrable hcontrolProductIntegrable
      htreatedResidualIntegrable hcontrolResidualIntegrable
      htreatedResidualCondZero hcontrolResidualCondZero hbridgeMap)

/--
Adapter from the predictable two-arm residual bridge route to an explicit
triangular martingale-array CLT bridge, preserving the named two-arm bridge
field before the triangular identification map is applied.
-/
theorem triangular_martingale_difference_array_of_twoArm_predictable_residual_bridge_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (htriangularMap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient i ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient i ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hbridgeMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient k ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient k ω * controlResidual k ω)
            ℱ μ ->
          b.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  htriangularMap
    (martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
      b treatedCoefficient treatedResidual controlCoefficient
      controlResidual htreatedCoefficientMeas hcontrolCoefficientMeas
      htreatedResidualNextMeas hcontrolResidualNextMeas
      htreatedProductIntegrable hcontrolProductIntegrable
      htreatedResidualIntegrable hcontrolResidualIntegrable
      htreatedResidualCondZero hcontrolResidualCondZero hbridgeMap)

/--
Two-arm residual martingale-difference field from genuinely predictable
treated/control coefficient processes and residual innovations.

This closes the named `TwoArmResidualMartingaleDifferenceBridge` field under
the WDSM reveal-order convention: coefficient value `i + 1` is applied to
residual innovation `i`, and Mathlib predictability supplies the required
past measurability for each arm.
-/
theorem
    martingale_difference_array_of_twoArm_stronglyPredictable_weighted_residual_increments_nat
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient (i + 1) ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient (i + 1) ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient (k + 1) ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient (k + 1) ω * controlResidual k ω)
            ℱ μ ->
          b.martingale_difference_array) :
    b.martingale_difference_array :=
  martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
    b (fun i ω => treatedCoefficient (i + 1) ω)
    treatedResidual (fun i ω => controlCoefficient (i + 1) ω)
    controlResidual
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      treatedCoefficient htreatedCoefficientPredictable)
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      controlCoefficient hcontrolCoefficientPredictable)
    htreatedResidualNextMeas hcontrolResidualNextMeas
    htreatedProductIntegrable hcontrolProductIntegrable
    htreatedResidualIntegrable hcontrolResidualIntegrable
    htreatedResidualCondZero hcontrolResidualCondZero hmap

/--
Adapter from the strongly-predictable two-arm residual bridge route to a
`ResidualMartingaleArrayCLTVarianceInput`.

This keeps the named `TwoArmResidualMartingaleDifferenceBridge` layer visible:
the Mathlib partial-sum martingales first close the bridge's own
martingale-difference field, then the supplied identification map transfers
that field to the residual CLT input.
-/
theorem
    input_martingale_difference_array_of_twoArm_stronglyPredictable_residual_bridge_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (hinputMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient (i + 1) ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient (i + 1) ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hbridgeMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient (k + 1) ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient (k + 1) ω * controlResidual k ω)
            ℱ μ ->
          b.martingale_difference_array) :
    input.martingale_difference_array :=
  hinputMap
    (martingale_difference_array_of_twoArm_stronglyPredictable_weighted_residual_increments_nat
      b treatedCoefficient treatedResidual controlCoefficient
      controlResidual htreatedCoefficientPredictable
      hcontrolCoefficientPredictable htreatedResidualNextMeas
      hcontrolResidualNextMeas htreatedProductIntegrable
      hcontrolProductIntegrable htreatedResidualIntegrable
      hcontrolResidualIntegrable htreatedResidualCondZero
      hcontrolResidualCondZero hbridgeMap)

/--
Adapter from the strongly-predictable two-arm residual bridge route to an
explicit triangular martingale-array CLT bridge.

This is the triangular counterpart of
`input_martingale_difference_array_of_twoArm_stronglyPredictable_residual_bridge_nat`:
the concrete Mathlib partial-sum martingales close the named two-arm WDSM
martingale bridge first, and a separate identification map transfers that
field to the triangular CLT bridge.
-/
theorem
    triangular_martingale_difference_array_of_twoArm_stronglyPredictable_residual_bridge_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (htriangularMap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient (i + 1) ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient (i + 1) ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hbridgeMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient (k + 1) ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient (k + 1) ω * controlResidual k ω)
            ℱ μ ->
          b.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  htriangularMap
    (martingale_difference_array_of_twoArm_stronglyPredictable_weighted_residual_increments_nat
      b treatedCoefficient treatedResidual controlCoefficient
      controlResidual htreatedCoefficientPredictable
      hcontrolCoefficientPredictable htreatedResidualNextMeas
      hcontrolResidualNextMeas htreatedProductIntegrable
      hcontrolProductIntegrable htreatedResidualIntegrable
      hcontrolResidualIntegrable htreatedResidualCondZero
      hcontrolResidualCondZero hbridgeMap)

/--
Concrete two-arm Nat-indexed predictable weighted-residual increment adapter
to the martingale-difference field of an explicit triangular martingale-array
CLT bridge.

This is the direct triangular-field version of
`input_martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat`:
treated and control predictable weighted residual increments generate Mathlib
partial-sum martingales, and the remaining map identifies those martingales
with the paper-specific residual array used by the triangular CLT interface.
-/
theorem
    triangular_martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient i ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient i ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient k ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient k ω * controlResidual k ω)
            ℱ μ ->
          martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  hmap
    (martingale_of_condExp_sub_eq_zero_nat
      (fun n =>
        Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
          ((htreatedCoefficientMeas k).mono
              (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
            ((htreatedResidualNextMeas k).mono
              (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
      (fun n =>
        integrable_finsetSum (Finset.range n) fun k _ =>
          htreatedProductIntegrable k)
      (fun i =>
        (condExp_congr_ae
          (ae_of_all _ fun ω => by
            simp [Finset.sum_range_succ])).trans
          ((condExp_predictable_mul_residual_ae_eq_zero_nat
              treatedCoefficient treatedResidual htreatedCoefficientMeas
              htreatedProductIntegrable htreatedResidualIntegrable
              htreatedResidualCondZero) i)))
    (martingale_of_condExp_sub_eq_zero_nat
      (fun n =>
        Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
          ((hcontrolCoefficientMeas k).mono
              (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
            ((hcontrolResidualNextMeas k).mono
              (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
      (fun n =>
        integrable_finsetSum (Finset.range n) fun k _ =>
          hcontrolProductIntegrable k)
      (fun i =>
        (condExp_congr_ae
          (ae_of_all _ fun ω => by
            simp [Finset.sum_range_succ])).trans
          ((condExp_predictable_mul_residual_ae_eq_zero_nat
              controlCoefficient controlResidual hcontrolCoefficientMeas
              hcontrolProductIntegrable hcontrolResidualIntegrable
              hcontrolResidualCondZero) i)))

/--
Two-arm triangular martingale-difference field from genuinely predictable
treated/control coefficient processes and residual innovations.

The WDSM reveal-order convention uses coefficient value `i + 1` on residual
innovation `i`; Mathlib predictability supplies the required `ℱ i`
measurability for both arms before the predictable weighted-residual
martingale adapter is applied.
-/
theorem
    triangular_martingale_difference_array_of_twoArm_stronglyPredictable_weighted_residual_increments_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient (i + 1) ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient (i + 1) ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient (k + 1) ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient (k + 1) ω * controlResidual k ω)
            ℱ μ ->
          martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  triangular_martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
    martingaleCLT (fun i ω => treatedCoefficient (i + 1) ω)
    treatedResidual (fun i ω => controlCoefficient (i + 1) ω)
    controlResidual
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      treatedCoefficient htreatedCoefficientPredictable)
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      controlCoefficient hcontrolCoefficientPredictable)
    htreatedResidualNextMeas hcontrolResidualNextMeas
    htreatedProductIntegrable hcontrolProductIntegrable
    htreatedResidualIntegrable hcontrolResidualIntegrable
    htreatedResidualCondZero hcontrolResidualCondZero hmap

/--
Concrete Nat-indexed two-arm adapter from Mathlib's partial-sum martingale
construction theorem to a `ResidualMartingaleArrayCLTVarianceInput`.
-/
theorem input_martingale_difference_array_of_twoArm_condExp_sub_eq_zero_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedPartialSum controlPartialSum : ℕ -> Ω -> E)
    (htreatedAdapted : StronglyAdapted ℱ treatedPartialSum)
    (hcontrolAdapted : StronglyAdapted ℱ controlPartialSum)
    (htreatedIntegrable : ∀ i, Integrable (treatedPartialSum i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlPartialSum i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedPartialSum (i + 1) - treatedPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlPartialSum (i + 1) - controlPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale treatedPartialSum ℱ μ ->
        Martingale controlPartialSum ℱ μ ->
          input.martingale_difference_array) :
    input.martingale_difference_array :=
  hmap
    (martingale_of_condExp_sub_eq_zero_nat htreatedAdapted
      htreatedIntegrable htreatedCondZero)
    (martingale_of_condExp_sub_eq_zero_nat hcontrolAdapted
      hcontrolIntegrable hcontrolCondZero)

/--
Concrete Nat-indexed two-arm increment-array adapter from Mathlib's partial-sum
martingale construction theorem to a `ResidualMartingaleArrayCLTVarianceInput`.
-/
theorem input_martingale_difference_array_of_twoArm_increment_condExp_eq_zero_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedIncrement controlIncrement : ℕ -> Ω -> E)
    (htreatedMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedIncrement i))
    (hcontrolMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlIncrement i))
    (htreatedIntegrable : ∀ i, Integrable (treatedIncrement i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlIncrement i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedIncrement i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlIncrement i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
          ℱ μ ->
        Martingale (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
          ℱ μ ->
          input.martingale_difference_array) :
    input.martingale_difference_array := by
  refine input_martingale_difference_array_of_twoArm_condExp_sub_eq_zero_nat
    input
    (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
    (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
    ?htreatedSumAdapted ?hcontrolSumAdapted ?htreatedSumIntegrable
    ?hcontrolSumIntegrable ?htreatedSumCondZero ?hcontrolSumCondZero hmap
  · intro n
    exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
      (htreatedMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
  · intro n
    exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
      (hcontrolMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
  · intro n
    exact integrable_finsetSum (Finset.range n) fun k _ =>
      htreatedIntegrable k
  · intro n
    exact integrable_finsetSum (Finset.range n) fun k _ =>
      hcontrolIntegrable k
  · intro i
    exact
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (htreatedCondZero i)
  · intro i
    exact
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (hcontrolCondZero i)

/--
Concrete Nat-indexed two-arm adapter from Mathlib's partial-sum martingale
construction theorem to an explicit triangular martingale-array CLT bridge.
-/
theorem triangular_martingale_difference_array_of_twoArm_condExp_sub_eq_zero_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedPartialSum controlPartialSum : ℕ -> Ω -> E)
    (htreatedAdapted : StronglyAdapted ℱ treatedPartialSum)
    (hcontrolAdapted : StronglyAdapted ℱ controlPartialSum)
    (htreatedIntegrable : ∀ i, Integrable (treatedPartialSum i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlPartialSum i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedPartialSum (i + 1) - treatedPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlPartialSum (i + 1) - controlPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale treatedPartialSum ℱ μ ->
        Martingale controlPartialSum ℱ μ ->
          martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array :=
  hmap
    (martingale_of_condExp_sub_eq_zero_nat htreatedAdapted
      htreatedIntegrable htreatedCondZero)
    (martingale_of_condExp_sub_eq_zero_nat hcontrolAdapted
      hcontrolIntegrable hcontrolCondZero)

/--
Concrete Nat-indexed two-arm increment-array adapter from Mathlib's
partial-sum martingale construction theorem to an explicit triangular
martingale-array CLT bridge.
-/
theorem triangular_martingale_difference_array_of_twoArm_increment_condExp_eq_zero_nat
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedIncrement controlIncrement : ℕ -> Ω -> E)
    (htreatedMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedIncrement i))
    (hcontrolMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlIncrement i))
    (htreatedIntegrable : ∀ i, Integrable (treatedIncrement i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlIncrement i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedIncrement i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlIncrement i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
          ℱ μ ->
        Martingale (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
          ℱ μ ->
          martingaleCLT.martingale_difference_array) :
    martingaleCLT.martingale_difference_array := by
  refine
    triangular_martingale_difference_array_of_twoArm_condExp_sub_eq_zero_nat
      martingaleCLT
      (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
      (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
      ?htreatedSumAdapted ?hcontrolSumAdapted ?htreatedSumIntegrable
      ?hcontrolSumIntegrable ?htreatedSumCondZero ?hcontrolSumCondZero hmap
  · intro n
    exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
      (htreatedMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
  · intro n
    exact Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
      (hcontrolMeas k).mono (ℱ.mono (Finset.mem_range.mp hk))
  · intro n
    exact integrable_finsetSum (Finset.range n) fun k _ =>
      htreatedIntegrable k
  · intro n
    exact integrable_finsetSum (Finset.range n) fun k _ =>
      hcontrolIntegrable k
  · intro i
    exact
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (htreatedCondZero i)
  · intro i
    exact
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (hcontrolCondZero i)

/--
Concrete treated/control predictable weighted-residual increment adapter to a
`ResidualMartingaleArrayCLTVarianceInput`.
-/
theorem
    input_martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient i ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient i ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient k ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient k ω * controlResidual k ω)
            ℱ μ ->
          input.martingale_difference_array) :
    input.martingale_difference_array :=
  input_martingale_difference_array_of_twoArm_increment_condExp_eq_zero_nat
    input
    (fun i ω => treatedCoefficient i ω * treatedResidual i ω)
    (fun i ω => controlCoefficient i ω * controlResidual i ω)
    (fun i =>
      ((htreatedCoefficientMeas i).mono (ℱ.mono (Nat.le_succ i))).mul
        (htreatedResidualNextMeas i))
    (fun i =>
      ((hcontrolCoefficientMeas i).mono (ℱ.mono (Nat.le_succ i))).mul
        (hcontrolResidualNextMeas i))
    htreatedProductIntegrable hcontrolProductIntegrable
    (condExp_predictable_mul_residual_ae_eq_zero_nat treatedCoefficient
      treatedResidual htreatedCoefficientMeas htreatedProductIntegrable
      htreatedResidualIntegrable htreatedResidualCondZero)
    (condExp_predictable_mul_residual_ae_eq_zero_nat controlCoefficient
      controlResidual hcontrolCoefficientMeas hcontrolProductIntegrable
      hcontrolResidualIntegrable hcontrolResidualCondZero)
    hmap

/--
Input-level two-arm martingale-difference field from genuinely predictable
treated/control coefficient processes and residual innovations.

This is the `ResidualMartingaleArrayCLTVarianceInput` analogue of the
triangular strongly-predictable reducer: it discharges the input
martingale-difference field from Mathlib `IsStronglyPredictable`
coefficient processes under the WDSM `i + 1` reveal-order convention.
-/
theorem
    input_martingale_difference_array_of_twoArm_stronglyPredictable_weighted_residual_increments_nat
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient (i + 1) ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient (i + 1) ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient (k + 1) ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient (k + 1) ω * controlResidual k ω)
            ℱ μ ->
          input.martingale_difference_array) :
    input.martingale_difference_array :=
  input_martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
    input (fun i ω => treatedCoefficient (i + 1) ω) treatedResidual
    (fun i ω => controlCoefficient (i + 1) ω) controlResidual
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      treatedCoefficient htreatedCoefficientPredictable)
    (coefficient_past_measurable_of_stronglyPredictable_add_one_nat
      controlCoefficient hcontrolCoefficientPredictable)
    htreatedResidualNextMeas hcontrolResidualNextMeas
    htreatedProductIntegrable hcontrolProductIntegrable
    htreatedResidualIntegrable hcontrolResidualIntegrable
    htreatedResidualCondZero hcontrolResidualCondZero hmap

/--
Residual CLT/variance input closed through two Mathlib Nat-indexed partial-sum
martingale constructions.  The residual CLT bridge itself remains the named
WDSM martingale-array theorem obligation.
-/
theorem residual_clt_and_variance_formula_of_twoArm_condExp_sub_eq_zero_nat_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedPartialSum controlPartialSum : ℕ -> Ω -> E)
    (htreatedAdapted : StronglyAdapted ℱ treatedPartialSum)
    (hcontrolAdapted : StronglyAdapted ℱ controlPartialSum)
    (htreatedIntegrable : ∀ i, Integrable (treatedPartialSum i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlPartialSum i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedPartialSum (i + 1) - treatedPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlPartialSum (i + 1) - controlPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale treatedPartialSum ℱ μ ->
        Martingale controlPartialSum ℱ μ ->
          input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_twoArm_condExp_sub_eq_zero_nat input
      treatedPartialSum controlPartialSum htreatedAdapted hcontrolAdapted
      htreatedIntegrable hcontrolIntegrable htreatedCondZero
      hcontrolCondZero hmap)
    hlindeberg hquad

/--
Residual CLT/variance input closed through concrete treated/control increment
arrays.  This discharges the two Mathlib martingales from increment-level
conditional mean-zero hypotheses while leaving the WDSM CLT conditions explicit.
-/
theorem residual_clt_and_variance_formula_of_twoArm_increment_condExp_eq_zero_nat_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedIncrement controlIncrement : ℕ -> Ω -> E)
    (htreatedMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedIncrement i))
    (hcontrolMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlIncrement i))
    (htreatedIntegrable : ∀ i, Integrable (treatedIncrement i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlIncrement i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedIncrement i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlIncrement i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
          ℱ μ ->
        Martingale (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
          ℱ μ ->
          input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_twoArm_increment_condExp_eq_zero_nat
      input treatedIncrement controlIncrement htreatedMeas hcontrolMeas
      htreatedIntegrable hcontrolIntegrable htreatedCondZero
      hcontrolCondZero hmap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through two Mathlib Nat-indexed
partial-sum martingale constructions.
-/
theorem residual_clt_and_variance_formula_of_twoArm_condExp_sub_eq_zero_nat_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedPartialSum controlPartialSum : ℕ -> Ω -> E)
    (htreatedAdapted : StronglyAdapted ℱ treatedPartialSum)
    (hcontrolAdapted : StronglyAdapted ℱ controlPartialSum)
    (htreatedIntegrable : ∀ i, Integrable (treatedPartialSum i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlPartialSum i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedPartialSum (i + 1) - treatedPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlPartialSum (i + 1) - controlPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale treatedPartialSum ℱ μ ->
        Martingale controlPartialSum ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_twoArm_condExp_sub_eq_zero_nat
      martingaleCLT treatedPartialSum controlPartialSum htreatedAdapted
      hcontrolAdapted htreatedIntegrable hcontrolIntegrable
      htreatedCondZero hcontrolCondZero hmap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through concrete treated/control
increment arrays.
-/
theorem residual_clt_and_variance_formula_of_twoArm_increment_condExp_eq_zero_nat_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedIncrement controlIncrement : ℕ -> Ω -> E)
    (htreatedMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedIncrement i))
    (hcontrolMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlIncrement i))
    (htreatedIntegrable : ∀ i, Integrable (treatedIncrement i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlIncrement i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedIncrement i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlIncrement i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
          ℱ μ ->
        Martingale (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
          ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_twoArm_increment_condExp_eq_zero_nat
      martingaleCLT treatedIncrement controlIncrement htreatedMeas
      hcontrolMeas htreatedIntegrable hcontrolIntegrable htreatedCondZero
      hcontrolCondZero hmap)
    hlindeberg hquad

/--
Residual CLT/variance input closed through concrete treated/control predictable
weighted-residual increments, matching the reveal-order martingale
representation used in the WDSM appendix.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_predictable_weighted_residual_increments_nat_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient i ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient i ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient k ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient k ω * controlResidual k ω)
            ℱ μ ->
          input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
      input treatedCoefficient treatedResidual controlCoefficient
      controlResidual htreatedCoefficientMeas hcontrolCoefficientMeas
      htreatedResidualNextMeas hcontrolResidualNextMeas
      htreatedProductIntegrable hcontrolProductIntegrable
      htreatedResidualIntegrable hcontrolResidualIntegrable
      htreatedResidualCondZero hcontrolResidualCondZero hmap)
    hlindeberg hquad

/--
Residual CLT/variance input closed through genuinely predictable treated and
control coefficient processes.  This discharges the martingale-difference
field from Mathlib `IsStronglyPredictable` evidence under the WDSM `i + 1`
reveal-order convention while leaving the Lindeberg and predictable-QV fields
explicit.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_stronglyPredictable_weighted_residual_increments_nat_input
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient (i + 1) ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient (i + 1) ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient (k + 1) ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient (k + 1) ω * controlResidual k ω)
            ℱ μ ->
          input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidual : input.residual_moment_regularity)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_martingale_array_input input
    hmoments hresidual
    (input_martingale_difference_array_of_twoArm_stronglyPredictable_weighted_residual_increments_nat
      input treatedCoefficient treatedResidual controlCoefficient
      controlResidual htreatedCoefficientPredictable
      hcontrolCoefficientPredictable htreatedResidualNextMeas
      hcontrolResidualNextMeas htreatedProductIntegrable
      hcontrolProductIntegrable htreatedResidualIntegrable
      hcontrolResidualIntegrable htreatedResidualCondZero
      hcontrolResidualCondZero hmap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through concrete treated/control
predictable weighted-residual increments.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_predictable_weighted_residual_increments_nat_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient i ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient i ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient k ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient k ω * controlResidual k ω)
            ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_twoArm_predictable_weighted_residual_increments_nat
      martingaleCLT treatedCoefficient treatedResidual controlCoefficient
      controlResidual htreatedCoefficientMeas hcontrolCoefficientMeas
      htreatedResidualNextMeas hcontrolResidualNextMeas
      htreatedProductIntegrable hcontrolProductIntegrable
      htreatedResidualIntegrable hcontrolResidualIntegrable
      htreatedResidualCondZero hcontrolResidualCondZero hmap)
    hlindeberg hquad

/--
Triangular residual CLT/variance bridge closed through genuinely predictable
treated and control coefficient processes under the WDSM `i + 1`
reveal-order convention.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_stronglyPredictable_weighted_residual_increments_nat_triangular
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedCoefficient treatedResidual : ℕ -> Ω -> Real)
    (controlCoefficient controlResidual : ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω => treatedCoefficient (i + 1) ω * treatedResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω => controlCoefficient (i + 1) ω * controlResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlResidual i | ℱ i] =ᵐ[μ] 0)
    (hmap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedCoefficient (k + 1) ω * treatedResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlCoefficient (k + 1) ω * controlResidual k ω)
            ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
    martingaleCLT
    (triangular_martingale_difference_array_of_twoArm_stronglyPredictable_weighted_residual_increments_nat
      martingaleCLT treatedCoefficient treatedResidual controlCoefficient
      controlResidual htreatedCoefficientPredictable
      hcontrolCoefficientPredictable htreatedResidualNextMeas
      hcontrolResidualNextMeas htreatedProductIntegrable
      hcontrolProductIntegrable htreatedResidualIntegrable
      hcontrolResidualIntegrable htreatedResidualCondZero
      hcontrolResidualCondZero hmap)
    hlindeberg hquad

/--
Two-arm sampling/filtration regularity bridge.

This is the armwise version needed by PATE/PATT residual arrays.  It separates
within-arm adaptedness from cross-arm sampling/design regularity so that later
proofs can target the exact missing probability step.
-/
structure TwoArmResidualSamplingFiltrationRegularityBridge where
  array_filtration_defined : Prop
  treated_coefficient_adapted_to_past : Prop
  control_coefficient_adapted_to_past : Prop
  treated_residual_innovation_measurable : Prop
  control_residual_innovation_measurable : Prop
  arm_order_regular : Prop
  cross_arm_sampling_regular : Prop
  conditional_design_regular : Prop
  arm_sampling_or_filtration_regular : Prop
  bridge :
    array_filtration_defined ->
    treated_coefficient_adapted_to_past ->
    control_coefficient_adapted_to_past ->
    treated_residual_innovation_measurable ->
    control_residual_innovation_measurable ->
    arm_order_regular ->
    cross_arm_sampling_regular ->
    conditional_design_regular ->
    arm_sampling_or_filtration_regular

/-- Close two-arm sampling/filtration regularity from its named pieces. -/
theorem arm_sampling_or_filtration_regular_of_bridge
    (b : TwoArmResidualSamplingFiltrationRegularityBridge)
    (hfiltration : b.array_filtration_defined)
    (htreatedAdapted : b.treated_coefficient_adapted_to_past)
    (hcontrolAdapted : b.control_coefficient_adapted_to_past)
    (htreatedInnovation : b.treated_residual_innovation_measurable)
    (hcontrolInnovation : b.control_residual_innovation_measurable)
    (horder : b.arm_order_regular)
    (hcross : b.cross_arm_sampling_regular)
    (hdesign : b.conditional_design_regular) :
    b.arm_sampling_or_filtration_regular :=
  b.bridge hfiltration htreatedAdapted hcontrolAdapted htreatedInnovation
    hcontrolInnovation horder hcross hdesign

/--
Close the two-arm martingale-difference bridge's sampling/filtration component
from an explicit two-arm sampling/filtration regularity bridge.
-/
theorem arm_sampling_or_filtration_regular_component_of_bridge
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (hmap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular) :
    martingaleBridge.arm_sampling_or_filtration_regular :=
  hmap
    (arm_sampling_or_filtration_regular_of_bridge regularityBridge
      hfiltration htreatedAdapted hcontrolAdapted htreatedInnovation
      hcontrolInnovation horder hcross hdesign)

/--
Adapter from two-arm named martingale-difference components plus explicit
sampling/filtration bridge pieces to a concrete martingale-array input.
-/
theorem input_martingale_difference_array_of_twoArm_residual_sampling_bridge
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (htreatedPredictable :
      martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictable :
      martingaleBridge.control_coefficient_predictability)
    (htreatedZero :
      martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZero :
      martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrable : martingaleBridge.finite_array_integrability) :
    input.martingale_difference_array :=
  input_martingale_difference_array_of_twoArm_residual_bridge input
    martingaleBridge harrayMap htreatedPredictable hcontrolPredictable
    htreatedZero hcontrolZero
    (arm_sampling_or_filtration_regular_component_of_bridge martingaleBridge
      regularityBridge hregularityMap hfiltration htreatedAdapted
      hcontrolAdapted htreatedInnovation hcontrolInnovation horder hcross
      hdesign)
    hintegrable

/--
Triangular martingale-difference field closed through a two-arm residual
martingale bridge plus an explicit two-arm sampling/filtration regularity
bridge.
-/
theorem triangular_martingale_difference_array_of_twoArm_residual_sampling_bridge
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (hmap :
      martingaleBridge.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (htreatedPredictable :
      martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictable :
      martingaleBridge.control_coefficient_predictability)
    (htreatedZero :
      martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZero :
      martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrable : martingaleBridge.finite_array_integrability) :
    martingaleCLT.martingale_difference_array :=
  triangular_martingale_difference_array_of_twoArm_residual_bridge
    martingaleCLT martingaleBridge hmap htreatedPredictable
    hcontrolPredictable htreatedZero hcontrolZero
    (arm_sampling_or_filtration_regular_component_of_bridge martingaleBridge
      regularityBridge hregularityMap hfiltration htreatedAdapted
      hcontrolAdapted htreatedInnovation hcontrolInnovation horder hcross
      hdesign)
    hintegrable

/--
Close the treated-arm coefficient predictability component from an
almost-everywhere score-measurability fact.
-/
theorem treated_coefficient_predictability_component_of_aestronglyMeasurable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (coefficient : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hmap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        b.treated_coefficient_predictability) :
    b.treated_coefficient_predictability :=
  hmap hcoefficient

/--
Close the control-arm coefficient predictability component from an
almost-everywhere score-measurability fact.
-/
theorem control_coefficient_predictability_component_of_aestronglyMeasurable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (coefficient : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hmap :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw ->
        b.control_coefficient_predictability) :
    b.control_coefficient_predictability :=
  hmap hcoefficient

/--
Close both two-arm coefficient predictability components from
almost-everywhere score-measurability facts.
-/
theorem twoArm_coefficient_predictability_components_of_aestronglyMeasurable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient controlCoefficient : Sample -> Real)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        b.treated_coefficient_predictability)
    (hcontrolMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        b.control_coefficient_predictability) :
    b.treated_coefficient_predictability ∧
      b.control_coefficient_predictability :=
  ⟨htreatedMap htreatedCoefficient, hcontrolMap hcontrolCoefficient⟩

/--
Close both two-arm coefficient predictability components from score-field
strong measurability facts.
-/
theorem twoArm_coefficient_predictability_components_of_stronglyMeasurable
    {Sample : Type*}
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient controlCoefficient : Sample -> Real)
    (htreatedCoefficient :
      StronglyMeasurable[treatedScoreSigma] treatedCoefficient)
    (hcontrolCoefficient :
      StronglyMeasurable[controlScoreSigma] controlCoefficient)
    (htreatedMap :
      StronglyMeasurable[treatedScoreSigma] treatedCoefficient ->
        b.treated_coefficient_predictability)
    (hcontrolMap :
      StronglyMeasurable[controlScoreSigma] controlCoefficient ->
        b.control_coefficient_predictability) :
    b.treated_coefficient_predictability ∧
      b.control_coefficient_predictability :=
  ⟨htreatedMap htreatedCoefficient, hcontrolMap hcontrolCoefficient⟩

/--
Close the two-arm finite-array integrability component from integrability of
both weighted residual contributions.
-/
theorem twoArm_finite_array_integrability_component_of_integrable_weightedResiduals
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {sampleLaw : Measure[mSample] Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient treatedResidual controlCoefficient controlResidual :
      Sample -> Real)
    (htreatedIntegrable :
      Integrable
        (fun sample => treatedCoefficient sample * treatedResidual sample)
        sampleLaw)
    (hcontrolIntegrable :
      Integrable
        (fun sample => controlCoefficient sample * controlResidual sample)
        sampleLaw)
    (hmap :
      Integrable
          (fun sample => treatedCoefficient sample * treatedResidual sample)
          sampleLaw ->
        Integrable
          (fun sample => controlCoefficient sample * controlResidual sample)
          sampleLaw ->
        b.finite_array_integrability) :
    b.finite_array_integrability :=
  hmap htreatedIntegrable hcontrolIntegrable

/--
Close the treated-arm residual conditional mean-zero component from a concrete
conditional-expectation residual identity.
-/
theorem treated_residual_conditional_mean_zero_component_of_condExp_ae_eq_scoreVersion
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreSelf :
      sampleLaw[scoreVersion | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero) :
    b.treated_residual_conditional_mean_zero :=
  hmap
    (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) outcome scoreVersion houtcome hscore hcond
      hscoreSelf)

/--
Raw-outcome-integrability variant for the treated-arm residual conditional
mean-zero component from a concrete conditional-expectation identity.
-/
theorem
    treated_residual_conditional_mean_zero_component_of_condExp_ae_eq_scoreVersion_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreSelf :
      sampleLaw[scoreVersion | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero) :
    b.treated_residual_conditional_mean_zero :=
  hmap
    (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) outcome scoreVersion houtcome hcond
      hscoreSelf)

/--
Close the control-arm residual conditional mean-zero component from a concrete
conditional-expectation residual identity.
-/
theorem control_residual_conditional_mean_zero_component_of_condExp_ae_eq_scoreVersion
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreSelf :
      sampleLaw[scoreVersion | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero) :
    b.control_residual_conditional_mean_zero :=
  hmap
    (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) outcome scoreVersion houtcome hscore hcond
      hscoreSelf)

/--
Raw-outcome-integrability variant for the control-arm residual conditional
mean-zero component from a concrete conditional-expectation identity.
-/
theorem
    control_residual_conditional_mean_zero_component_of_condExp_ae_eq_scoreVersion_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hscoreSelf :
      sampleLaw[scoreVersion | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero) :
    b.control_residual_conditional_mean_zero :=
  hmap
    (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) outcome scoreVersion houtcome hcond
      hscoreSelf)

/--
Close the treated-arm residual conditional mean-zero component from conditional
orthogonality of a score-measurable coefficient and a centered residual.
-/
theorem treated_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero) :
    b.treated_residual_conditional_mean_zero :=
  hmap
    (condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub coefficient outcome scoreVersion
      hcoefficient houtcome hscore hscoreMeas hproduct hcond)

/--
Raw-outcome-integrability variant for the treated-arm score-measurable
weighted centered-residual mean-zero component.
-/
theorem
    treated_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero) :
    b.treated_residual_conditional_mean_zero :=
  hmap
    (condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub coefficient outcome scoreVersion
      hcoefficient houtcome hscoreMeas hproduct hcond)

/--
Close the control-arm residual conditional mean-zero component from conditional
orthogonality of a score-measurable coefficient and a centered residual.
-/
theorem control_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero) :
    b.control_residual_conditional_mean_zero :=
  hmap
    (condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub coefficient outcome scoreVersion
      hcoefficient houtcome hscore hscoreMeas hproduct hcond)

/--
Raw-outcome-integrability variant for the control-arm score-measurable
weighted centered-residual mean-zero component.
-/
theorem
    control_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {scoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample))
        sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion)
    (hmap :
      sampleLaw[(fun sample =>
          coefficient sample * (outcome sample - scoreVersion sample)) |
          scoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero) :
    b.control_residual_conditional_mean_zero :=
  hmap
    (condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub coefficient outcome scoreVersion
      hcoefficient houtcome hscoreMeas hproduct hcond)

/--
Residual CLT/variance input from concrete two-arm weighted centered-residual
martingale-difference components.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_bridge_input
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient treatedOutcome treatedScoreVersion :
      Sample -> Real)
    (controlCoefficient controlOutcome controlScoreVersion :
      Sample -> Real)
    (harrayMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        b.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        b.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScore : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScore : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            treatedCoefficient sample *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            controlCoefficient sample *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have hpredictable :
      b.treated_coefficient_predictability ∧
        b.control_coefficient_predictability :=
    twoArm_coefficient_predictability_components_of_aestronglyMeasurable
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      b treatedCoefficient controlCoefficient htreatedCoefficient
      hcontrolCoefficient htreatedPredictabilityMap
      hcontrolPredictabilityMap
  exact
    residual_clt_and_variance_formula_of_twoArm_residual_bridge_input input b
      harrayMap hmoments hresidualRegularity hpredictable.1 hpredictable.2
      (treated_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
        (mSample := mSample) (scoreSigma := treatedScoreSigma)
        (sampleLaw := sampleLaw) htreatedSub b treatedCoefficient
        treatedOutcome treatedScoreVersion htreatedCoefficient
        htreatedOutcome htreatedScore htreatedScoreMeas
        htreatedWeightedResidual htreatedCond htreatedZeroMap)
      (control_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
        (mSample := mSample) (scoreSigma := controlScoreSigma)
        (sampleLaw := sampleLaw) hcontrolSub b controlCoefficient
        controlOutcome controlScoreVersion hcontrolCoefficient
        hcontrolOutcome hcontrolScore hcontrolScoreMeas
        hcontrolWeightedResidual hcontrolCond hcontrolZeroMap)
      hregular
      (twoArm_finite_array_integrability_component_of_integrable_weightedResiduals
        (mSample := mSample) (sampleLaw := sampleLaw) b treatedCoefficient
        (fun sample => treatedOutcome sample - treatedScoreVersion sample)
        controlCoefficient
        (fun sample => controlOutcome sample - controlScoreVersion sample)
        htreatedWeightedResidual hcontrolWeightedResidual
        hintegrabilityMap)
      hlindeberg hquad

/--
Triangular residual CLT/variance bridge from concrete two-arm weighted
centered-residual martingale-difference components.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_bridge_triangular
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient treatedOutcome treatedScoreVersion :
      Sample -> Real)
    (controlCoefficient controlOutcome controlScoreVersion :
      Sample -> Real)
    (harrayMap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        b.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        b.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScore : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScore : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            treatedCoefficient sample *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            controlCoefficient sample *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula := by
  have hpredictable :
      b.treated_coefficient_predictability ∧
        b.control_coefficient_predictability :=
    twoArm_coefficient_predictability_components_of_aestronglyMeasurable
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      b treatedCoefficient controlCoefficient htreatedCoefficient
      hcontrolCoefficient htreatedPredictabilityMap
      hcontrolPredictabilityMap
  exact
    residual_clt_and_variance_formula_of_twoArm_residual_bridge_triangular
      martingaleCLT b harrayMap hpredictable.1 hpredictable.2
      (treated_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
        (mSample := mSample) (scoreSigma := treatedScoreSigma)
        (sampleLaw := sampleLaw) htreatedSub b treatedCoefficient
        treatedOutcome treatedScoreVersion htreatedCoefficient
        htreatedOutcome htreatedScore htreatedScoreMeas
        htreatedWeightedResidual htreatedCond htreatedZeroMap)
      (control_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual
        (mSample := mSample) (scoreSigma := controlScoreSigma)
        (sampleLaw := sampleLaw) hcontrolSub b controlCoefficient
        controlOutcome controlScoreVersion hcontrolCoefficient
        hcontrolOutcome hcontrolScore hcontrolScoreMeas
        hcontrolWeightedResidual hcontrolCond hcontrolZeroMap)
      hregular
      (twoArm_finite_array_integrability_component_of_integrable_weightedResiduals
        (mSample := mSample) (sampleLaw := sampleLaw) b treatedCoefficient
        (fun sample => treatedOutcome sample - treatedScoreVersion sample)
        controlCoefficient
        (fun sample => controlOutcome sample - controlScoreVersion sample)
        htreatedWeightedResidual hcontrolWeightedResidual
        hintegrabilityMap)
      hlindeberg hquad

/--
Raw-outcome-integrability variant of the two-arm weighted centered-residual
CLT/variance bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_bridge_input_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient treatedOutcome treatedScoreVersion :
      Sample -> Real)
    (controlCoefficient controlOutcome controlScoreVersion :
      Sample -> Real)
    (harrayMap :
      b.martingale_difference_array -> input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        b.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        b.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            treatedCoefficient sample *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            controlCoefficient sample *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have hpredictable :
      b.treated_coefficient_predictability ∧
        b.control_coefficient_predictability :=
    twoArm_coefficient_predictability_components_of_aestronglyMeasurable
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      b treatedCoefficient controlCoefficient htreatedCoefficient
      hcontrolCoefficient htreatedPredictabilityMap
      hcontrolPredictabilityMap
  exact
    residual_clt_and_variance_formula_of_twoArm_residual_bridge_input input b
      harrayMap hmoments hresidualRegularity hpredictable.1 hpredictable.2
      (treated_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
        (mSample := mSample) (scoreSigma := treatedScoreSigma)
        (sampleLaw := sampleLaw) htreatedSub b treatedCoefficient
        treatedOutcome treatedScoreVersion htreatedCoefficient
        htreatedOutcome htreatedScoreMeas htreatedWeightedResidual
        htreatedCond htreatedZeroMap)
      (control_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
        (mSample := mSample) (scoreSigma := controlScoreSigma)
        (sampleLaw := sampleLaw) hcontrolSub b controlCoefficient
        controlOutcome controlScoreVersion hcontrolCoefficient
        hcontrolOutcome hcontrolScoreMeas hcontrolWeightedResidual
        hcontrolCond hcontrolZeroMap)
      hregular
      (twoArm_finite_array_integrability_component_of_integrable_weightedResiduals
        (mSample := mSample) (sampleLaw := sampleLaw) b treatedCoefficient
        (fun sample => treatedOutcome sample - treatedScoreVersion sample)
        controlCoefficient
        (fun sample => controlOutcome sample - controlScoreVersion sample)
        htreatedWeightedResidual hcontrolWeightedResidual
        hintegrabilityMap)
      hlindeberg hquad

/--
Raw-outcome-integrability variant of the two-arm weighted centered-residual
triangular CLT/variance bridge.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_bridge_triangular_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (b : TwoArmResidualMartingaleDifferenceBridge)
    (treatedCoefficient treatedOutcome treatedScoreVersion :
      Sample -> Real)
    (controlCoefficient controlOutcome controlScoreVersion :
      Sample -> Real)
    (harrayMap :
      b.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        b.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        b.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        b.control_residual_conditional_mean_zero)
    (hregular : b.arm_sampling_or_filtration_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            treatedCoefficient sample *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            controlCoefficient sample *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        b.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula := by
  have hpredictable :
      b.treated_coefficient_predictability ∧
        b.control_coefficient_predictability :=
    twoArm_coefficient_predictability_components_of_aestronglyMeasurable
      (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
      (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
      b treatedCoefficient controlCoefficient htreatedCoefficient
      hcontrolCoefficient htreatedPredictabilityMap
      hcontrolPredictabilityMap
  exact
    residual_clt_and_variance_formula_of_twoArm_residual_bridge_triangular
      martingaleCLT b harrayMap hpredictable.1 hpredictable.2
      (treated_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
        (mSample := mSample) (scoreSigma := treatedScoreSigma)
        (sampleLaw := sampleLaw) htreatedSub b treatedCoefficient
        treatedOutcome treatedScoreVersion htreatedCoefficient
        htreatedOutcome htreatedScoreMeas htreatedWeightedResidual
        htreatedCond htreatedZeroMap)
      (control_residual_conditional_mean_zero_component_of_scoreMeasurable_weightedCenteredResidual_outcomeIntegrable
        (mSample := mSample) (scoreSigma := controlScoreSigma)
        (sampleLaw := sampleLaw) hcontrolSub b controlCoefficient
        controlOutcome controlScoreVersion hcontrolCoefficient
        hcontrolOutcome hcontrolScoreMeas hcontrolWeightedResidual
        hcontrolCond hcontrolZeroMap)
      hregular
      (twoArm_finite_array_integrability_component_of_integrable_weightedResiduals
        (mSample := mSample) (sampleLaw := sampleLaw) b treatedCoefficient
        (fun sample => treatedOutcome sample - treatedScoreVersion sample)
        controlCoefficient
        (fun sample => controlOutcome sample - controlScoreVersion sample)
        htreatedWeightedResidual hcontrolWeightedResidual
        hintegrabilityMap)
      hlindeberg hquad

/--
Two-arm weighted centered-residual CLT/variance input closed from explicit
sampling/filtration regularity components.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_sampling_bridge_input
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (treatedCoefficient treatedOutcome treatedScoreVersion :
      Sample -> Real)
    (controlCoefficient controlOutcome controlScoreVersion :
      Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        martingaleBridge.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScore : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScore : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            treatedCoefficient sample *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            controlCoefficient sample *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_bridge_input
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub input martingaleBridge treatedCoefficient
    treatedOutcome treatedScoreVersion controlCoefficient controlOutcome
    controlScoreVersion harrayMap hmoments hresidualRegularity
    htreatedCoefficient hcontrolCoefficient htreatedPredictabilityMap
    hcontrolPredictabilityMap htreatedOutcome hcontrolOutcome htreatedScore
    hcontrolScore htreatedScoreMeas hcontrolScoreMeas
    htreatedWeightedResidual hcontrolWeightedResidual htreatedCond
    hcontrolCond htreatedZeroMap hcontrolZeroMap
    (arm_sampling_or_filtration_regular_component_of_bridge
      martingaleBridge regularityBridge hregularityMap hfiltration
      htreatedAdapted hcontrolAdapted htreatedInnovation hcontrolInnovation
      horder hcross hdesign)
    hintegrabilityMap hlindeberg hquad

/--
Two-arm weighted centered-residual triangular CLT/variance bridge closed from
explicit sampling/filtration regularity components.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_sampling_bridge_triangular
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (treatedCoefficient treatedOutcome treatedScoreVersion :
      Sample -> Real)
    (controlCoefficient controlOutcome controlScoreVersion :
      Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        martingaleBridge.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScore : Integrable treatedScoreVersion sampleLaw)
    (hcontrolScore : Integrable controlScoreVersion sampleLaw)
    (htreatedScoreMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            treatedCoefficient sample *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            controlCoefficient sample *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_bridge_triangular
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub martingaleCLT martingaleBridge
    treatedCoefficient treatedOutcome treatedScoreVersion controlCoefficient
    controlOutcome controlScoreVersion harrayMap htreatedCoefficient
    hcontrolCoefficient htreatedPredictabilityMap hcontrolPredictabilityMap
    htreatedOutcome hcontrolOutcome htreatedScore hcontrolScore
    htreatedScoreMeas hcontrolScoreMeas htreatedWeightedResidual
    hcontrolWeightedResidual htreatedCond hcontrolCond htreatedZeroMap
    hcontrolZeroMap
    (arm_sampling_or_filtration_regular_component_of_bridge
      martingaleBridge regularityBridge hregularityMap hfiltration
      htreatedAdapted hcontrolAdapted htreatedInnovation hcontrolInnovation
      horder hcross hdesign)
    hintegrabilityMap hlindeberg hquad

/--
Raw-outcome-integrability variant of the two-arm weighted centered-residual
sampling/filtration bridge input.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_sampling_bridge_input_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (treatedCoefficient treatedOutcome treatedScoreVersion :
      Sample -> Real)
    (controlCoefficient controlOutcome controlScoreVersion :
      Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (hmoments : input.exact_weighted_reuse_moment_limits)
    (hresidualRegularity : input.residual_moment_regularity)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        martingaleBridge.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            treatedCoefficient sample *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            controlCoefficient sample *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : input.conditional_lindeberg)
    (hquad : input.predictable_quadratic_variation_stabilization) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_bridge_input_outcomeIntegrable
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub input martingaleBridge treatedCoefficient
    treatedOutcome treatedScoreVersion controlCoefficient controlOutcome
    controlScoreVersion harrayMap hmoments hresidualRegularity
    htreatedCoefficient hcontrolCoefficient htreatedPredictabilityMap
    hcontrolPredictabilityMap htreatedOutcome hcontrolOutcome
    htreatedScoreMeas hcontrolScoreMeas htreatedWeightedResidual
    hcontrolWeightedResidual htreatedCond hcontrolCond htreatedZeroMap
    hcontrolZeroMap
    (arm_sampling_or_filtration_regular_component_of_bridge
      martingaleBridge regularityBridge hregularityMap hfiltration
      htreatedAdapted hcontrolAdapted htreatedInnovation hcontrolInnovation
      horder hcross hdesign)
    hintegrabilityMap hlindeberg hquad

/--
Raw-outcome-integrability variant of the two-arm weighted centered-residual
sampling/filtration triangular CLT/variance bridge.
-/
theorem
    residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_sampling_bridge_triangular_outcomeIntegrable
    {Sample : Type*} [mSample : MeasurableSpace Sample]
    {treatedScoreSigma controlScoreSigma : MeasurableSpace Sample}
    {sampleLaw : Measure[mSample] Sample}
    (htreatedSub : treatedScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim htreatedSub)]
    (hcontrolSub : controlScoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hcontrolSub)]
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (treatedCoefficient treatedOutcome treatedScoreVersion :
      Sample -> Real)
    (controlCoefficient controlOutcome controlScoreVersion :
      Sample -> Real)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (htreatedCoefficient :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw)
    (hcontrolCoefficient :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw)
    (htreatedPredictabilityMap :
      AEStronglyMeasurable[treatedScoreSigma] treatedCoefficient sampleLaw ->
        martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictabilityMap :
      AEStronglyMeasurable[controlScoreSigma] controlCoefficient sampleLaw ->
        martingaleBridge.control_coefficient_predictability)
    (htreatedOutcome : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcome : Integrable controlOutcome sampleLaw)
    (htreatedScoreMeas :
      AEStronglyMeasurable[treatedScoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolScoreMeas :
      AEStronglyMeasurable[controlScoreSigma] controlScoreVersion sampleLaw)
    (htreatedWeightedResidual :
      Integrable
        (fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample))
        sampleLaw)
    (hcontrolWeightedResidual :
      Integrable
        (fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample))
        sampleLaw)
    (htreatedCond :
      sampleLaw[treatedOutcome | treatedScoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrolCond :
      sampleLaw[controlOutcome | controlScoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (htreatedZeroMap :
      sampleLaw[(fun sample =>
          treatedCoefficient sample *
            (treatedOutcome sample - treatedScoreVersion sample)) |
          treatedScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZeroMap :
      sampleLaw[(fun sample =>
          controlCoefficient sample *
            (controlOutcome sample - controlScoreVersion sample)) |
          controlScoreSigma] =ᵐ[sampleLaw] 0 ->
        martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrabilityMap :
      Integrable
          (fun sample =>
            treatedCoefficient sample *
              (treatedOutcome sample - treatedScoreVersion sample))
          sampleLaw ->
        Integrable
          (fun sample =>
            controlCoefficient sample *
              (controlOutcome sample - controlScoreVersion sample))
          sampleLaw ->
        martingaleBridge.finite_array_integrability)
    (hlindeberg : martingaleCLT.conditional_lindeberg)
    (hquad : martingaleCLT.predictable_quadratic_variation_stabilization) :
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreMeasurable_weightedCenteredResidual_bridge_triangular_outcomeIntegrable
    (mSample := mSample) (treatedScoreSigma := treatedScoreSigma)
    (controlScoreSigma := controlScoreSigma) (sampleLaw := sampleLaw)
    htreatedSub hcontrolSub martingaleCLT martingaleBridge
    treatedCoefficient treatedOutcome treatedScoreVersion controlCoefficient
    controlOutcome controlScoreVersion harrayMap htreatedCoefficient
    hcontrolCoefficient htreatedPredictabilityMap hcontrolPredictabilityMap
    htreatedOutcome hcontrolOutcome htreatedScoreMeas hcontrolScoreMeas
    htreatedWeightedResidual hcontrolWeightedResidual htreatedCond
    hcontrolCond htreatedZeroMap hcontrolZeroMap
    (arm_sampling_or_filtration_regular_component_of_bridge
      martingaleBridge regularityBridge hregularityMap hfiltration
      htreatedAdapted hcontrolAdapted htreatedInnovation hcontrolInnovation
      horder hcross hdesign)
    hintegrabilityMap hlindeberg hquad

end WDSM
end Matching
end StatInference
