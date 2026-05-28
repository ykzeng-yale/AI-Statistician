import StatInference.EmpiricalProcess.GlivenkoCantelli
import StatInference.EmpiricalProcess.EndpointSamples
import StatInference.EmpiricalProcess.RealHalfLine

/-!
# Half-line Glivenko-Cantelli handoffs

This module connects the supplied-grid layer for VdV&W Example 2.4.2 to the
already proved bracketing Glivenko-Cantelli theorem.  The grid construction
from an arbitrary distribution is still a separate task.
-/

namespace StatInference

open MeasureTheory ProbabilityTheory Set Filter

open scoped Function Topology

universe u

/--
The population integral of a closed half-line indicator is the CDF value at
that endpoint.

This is the pointwise bridge between Billingsley's empirical distribution
function notation and the local half-line indicator class.
-/
theorem realHalfLineIndicator_integral_eq_cdf
    (P : Measure ℝ) [IsProbabilityMeasure P] (c : ℝ) :
    (∫ x, realHalfLineIndicator c x ∂P) = ProbabilityTheory.cdf P c := by
  calc
    (∫ x, realHalfLineIndicator c x ∂P) = P.real (Set.Iic c) := by
      simp [realHalfLineIndicator]
    _ = ProbabilityTheory.cdf P c :=
      (ProbabilityTheory.cdf_eq_real P c).symm

/--
Pointwise empirical-distribution convergence for one closed half-line.

For iid real observations with law `P`, the sample average of
`1{(-∞, c]}` converges almost surely to `F(c)`.
-/
theorem realHalfLine_empiricalAverage_sub_cdf_tendsto_zero_ae_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun n : ℕ =>
          empiricalAverage (samplePath X ω n) (realHalfLineIndicator c) -
            ProbabilityTheory.cdf P c)
        atTop (𝓝 0) := by
  have hInt : Integrable (realHalfLineIndicator c) P :=
    integrable_realHalfLineIndicator P c
  have hIntegral :
      (∫ x, realHalfLineIndicator c x ∂P) = ProbabilityTheory.cdf P c :=
    realHalfLineIndicator_integral_eq_cdf P c
  filter_upwards
    [endpoint_empiricalAverage_sub_population_tendsto_zero_ae_of_iid
      X (realHalfLineIndicator c)
      hInt.aestronglyMeasurable.aemeasurable hInt hLaw hindep]
    with ω hω
  simpa [hIntegral] using hω

/--
Pointwise empirical-distribution convergence in probability for one closed
half-line.

This repackages the fixed-endpoint almost-sure statement through mathlib's
`TendstoInMeasure`, the local common-domain form of convergence in
probability.
-/
theorem realHalfLine_empiricalAverage_sub_cdf_tendstoInMeasure_zero_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    MeasureTheory.TendstoInMeasure μ
      (fun n ω =>
        empiricalAverage (samplePath X ω n) (realHalfLineIndicator c) -
          ProbabilityTheory.cdf P c)
      atTop (fun _ => 0) := by
  letI : IsProbabilityMeasure μ := (hLaw 0).isProbabilityMeasure
  have hIndicator_measurable : Measurable (realHalfLineIndicator c) := by
    simpa [realHalfLineIndicator] using
      (measurable_const.indicator measurableSet_Iic : Measurable (realHalfLineIndicator c))
  have h_aestrongly :
      ∀ n,
        AEStronglyMeasurable
          (fun ω =>
            empiricalAverage (samplePath X ω n) (realHalfLineIndicator c) -
              ProbabilityTheory.cdf P c) μ := by
    intro n
    exact
      ((empiricalAverage_samplePath_aemeasurable_of_hasLaw
        X (realHalfLineIndicator c) n hLaw hIndicator_measurable).sub
          aemeasurable_const).aestronglyMeasurable
  exact
    MeasureTheory.tendstoInMeasure_of_tendsto_ae h_aestrongly
      (realHalfLine_empiricalAverage_sub_cdf_tendsto_zero_ae_of_iid
        X c hLaw hindep)

/--
Fixed-endpoint empirical-distribution convergence in the local VdV&W outer
probability vocabulary.

This is still a pointwise support layer, not the uniform-in-`x`
Glivenko-Cantelli conclusion of Billingsley's Theorem 20.6.
-/
theorem realHalfLine_empiricalAverage_sub_cdf_convergesInOuterProbability_of_iid
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsProbabilityMeasure P]
    (X : ℕ -> Ω -> ℝ) (c : ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    VdVWConvergesInOuterProbability μ
      (fun n ω =>
        empiricalAverage (samplePath X ω n) (realHalfLineIndicator c) -
          ProbabilityTheory.cdf P c)
      atTop (fun _ => 0) :=
  vdVWConvergesInOuterProbability_of_tendstoInMeasure
    (realHalfLine_empiricalAverage_sub_cdf_tendstoInMeasure_zero_of_iid
      X c hLaw hindep)

/--
Conditional outer-a.s. Glivenko-Cantelli corollary for the real half-line
indicator class.

If finite extended-real half-line grids are supplied at every positive
`L1(P)` radius, then VdV&W Theorem 2.4.1 applies to the class
`{1{(-infty, c]} : c : R}`.
-/
theorem vdVW_realHalfLine_outerAlmostSureGlivenkoCantelli_of_suppliedERealHalfLineGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (gridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid P epsilon cardinality)) :
    VdVWOuterAlmostSurePGlivenkoCantelliClass μ P Set.univ
      realHalfLineIndicator X :=
  vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli
    X hLaw hindep
    (SuppliedERealHalfLineGrid.l1BracketingNumber_lt_top_forall gridExists)

/--
Conditional outer-a.s. Glivenko-Cantelli corollary from supplied adjacent
extended-real endpoint grids.

This is closer to the textbook grid notation in Example 2.4.2 than the
primitive supplied-grid interface.
-/
theorem vdVW_realHalfLine_outerAlmostSureGlivenkoCantelli_of_suppliedERealHalfLineEndpointGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (endpointGridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid P epsilon cellCount)) :
    VdVWOuterAlmostSurePGlivenkoCantelliClass μ P Set.univ
      realHalfLineIndicator X :=
  vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli
    X hLaw hindep
    (SuppliedERealHalfLineEndpointGrid.l1BracketingNumber_lt_top_forall
      endpointGridExists)

/--
Conditional book-style Glivenko-Cantelli corollary for the real half-line
indicator class.

This is the current compiled Example 2.4.2 handoff: once the textbook finite
grid is constructed for every positive radius, the half-line class immediately
inherits the local book-style Glivenko-Cantelli predicate.
-/
theorem vdVW_realHalfLine_glivenkoCantelli_of_suppliedERealHalfLineGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (gridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cardinality, Nonempty (SuppliedERealHalfLineGrid P epsilon cardinality)) :
    VdVWPGlivenkoCantelliClass μ P Set.univ realHalfLineIndicator X :=
  vdVW_theorem_2_4_1_glivenkoCantelli
    X hLaw hindep
    (SuppliedERealHalfLineGrid.l1BracketingNumber_lt_top_forall gridExists)

/--
Conditional book-style Glivenko-Cantelli corollary from supplied adjacent
extended-real endpoint grids.

Once the distribution-dependent endpoint grid from Example 2.4.2 is
constructed at every positive radius, the half-line class inherits the local
book-style Glivenko-Cantelli predicate.
-/
theorem vdVW_realHalfLine_glivenkoCantelli_of_suppliedERealHalfLineEndpointGrids
    {Ω : Type u} [MeasurableSpace Ω]
    {μ : Measure Ω} {P : Measure ℝ} [IsFiniteMeasure P]
    (X : ℕ -> Ω -> ℝ)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (endpointGridExists :
      ∀ epsilon, 0 < epsilon ->
        ∃ cellCount, Nonempty (SuppliedERealHalfLineEndpointGrid P epsilon cellCount)) :
    VdVWPGlivenkoCantelliClass μ P Set.univ realHalfLineIndicator X :=
  vdVW_theorem_2_4_1_glivenkoCantelli
    X hLaw hindep
    (SuppliedERealHalfLineEndpointGrid.l1BracketingNumber_lt_top_forall
      endpointGridExists)

end StatInference
